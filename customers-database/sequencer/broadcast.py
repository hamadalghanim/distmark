"""
customers_broadcast.py — Broadcast shim for the customers service

Same design as broadcast.py but wired to customers_pb2 and customers_engine.
Every write (CreateAccount, Login, Logout, AddItemToCart, etc.) goes through
atomic broadcast so all 5 customer nodes stay consistent.

Read-only methods (GetCart, GetBuyer, GetBuyerPurchases) are NOT broadcast —
they query local state directly like any normal gRPC handler.
"""

import struct
import logging
import threading
import datetime

from sequencer.member import Member

logger = logging.getLogger(__name__)

OP_CREATE_ACCOUNT = 0x01
OP_LOGIN = 0x02
OP_LOGOUT = 0x03
OP_ADD_ITEM_TO_CART = 0x04
OP_REMOVE_ITEM_FROM_CART = 0x05
OP_CLEAR_CART = 0x06
OP_SAVE_CART = 0x07
OP_MAKE_PURCHASE = 0x08

_OP = struct.Struct("!B")


class BroadcastShim:
    def __init__(self):
        self.member: Member = None
        self._handlers: dict = {}
        self._submitted: set = set()
        self._submitted_lock = threading.Lock()

    def register(self, opcode, proto_class, handler_fn):
        self._handlers[opcode] = (proto_class, handler_fn)

    def broadcast(self, opcode: int, proto_request):
        """Submit to broadcast, block until ordering slot, run handler, return response."""
        payload = _OP.pack(opcode) + proto_request.SerializeToString()
        event, rid = self.member.submit(payload)

        with self._submitted_lock:
            self._submitted.add(rid)

        event.wait()

        return self._run_handler(opcode, proto_request.SerializeToString())

    def deliver(self, global_seq, rid, payload):
        """Deliver callback — skip submitter (already handled), run handler on others."""
        with self._submitted_lock:
            is_mine = rid in self._submitted
            if is_mine:
                self._submitted.discard(rid)

        if is_mine:
            logger.debug(
                "deliver global_seq=%d rid=%s: skipped (submitter)", global_seq, rid
            )
            return

        opcode = _OP.unpack_from(payload, 0)[0]
        body = payload[1:]
        self._run_handler(opcode, body)

    def _run_handler(self, opcode, body: bytes):
        entry = self._handlers.get(opcode)
        if entry is None:
            logger.error("unknown opcode %#x", opcode)
            return None
        proto_class, handler_fn = entry
        try:
            req = proto_class()
            req.ParseFromString(body)
            return handler_fn(req)
        except Exception:
            logger.exception("handler for opcode %#x raised", opcode)
            return None


class BroadcastMixin:
    """Mixin for CustomerAPI. Requires self._shim set by setup_member()."""

    _shim: BroadcastShim

    def _broadcast(self, opcode, proto_request):
        return self._shim.broadcast(opcode, proto_request)


def setup_member(member_id, n, peer_addrs, api) -> Member:
    from proto import customers_pb2
    from db import Buyer, BuyerSession, Cart, CartItem, ItemsBought
    from sqlalchemy.orm import Session
    from utils import customers_engine, getAndValidateSession

    shim = BroadcastShim()

    def _get_or_create_cart(session: BuyerSession, s: Session) -> Cart:
        cart = (
            s.query(Cart)
            .filter_by(buyer_id=session.buyer_id, buyer_session_id=session.id)
            .first()
        )
        if cart is None:
            cart = Cart(buyer_id=session.buyer_id, buyer_session_id=session.id)
            s.add(cart)
            s.commit()
        return cart

    # ── Write handlers ────────────────────────────────────────────────────────

    def _create_account(req):
        with Session(customers_engine) as s:
            try:
                obj = Buyer(
                    name=req.username, username=req.username, password=req.password
                )
                s.add(obj)
                s.commit()
                return customers_pb2.CreateAccountResponse(
                    success=True,
                    message=f"Buyer created with ID: {obj.id}",
                    buyer_id=obj.id,
                )
            except Exception as e:
                s.rollback()
                return customers_pb2.CreateAccountResponse(
                    success=False, message=f"Database error: {e}"
                )

    def _login(req):
        with Session(customers_engine) as s:
            try:
                buyer = s.query(Buyer).filter_by(username=req.username).first()
            except Exception as e:
                return customers_pb2.LoginResponse(
                    success=False, message=f"Database error: {e}"
                )
            if buyer is None:
                return customers_pb2.LoginResponse(
                    success=False, message="Buyer not found"
                )
            if buyer.password != req.password:
                return customers_pb2.LoginResponse(
                    success=False, message="Invalid username or password"
                )
            try:
                sess = BuyerSession(
                    buyer_id=buyer.id,
                    last_activity=datetime.datetime.now(datetime.timezone.utc),
                )
                sess.cart = Cart(buyer_id=buyer.id)
                s.add(sess)
                s.commit()
                return customers_pb2.LoginResponse(success=True, session_id=sess.id)
            except Exception as e:
                s.rollback()
                return customers_pb2.LoginResponse(
                    success=False, message=f"Database error: {e}"
                )

    def _logout(req):
        with Session(customers_engine) as s:
            result = getAndValidateSession(req.session_id, s)
            if result.error:
                return customers_pb2.BasicResponse(
                    success=False, message="Session not found or expired"
                )
            try:
                s.delete(result.session)
                s.commit()
                return customers_pb2.BasicResponse(
                    success=True, message="Logout successful"
                )
            except Exception as e:
                s.rollback()
                return customers_pb2.BasicResponse(
                    success=False, message=f"Database error: {e}"
                )

    def _add_item_to_cart(req):
        with Session(customers_engine) as s:
            result = getAndValidateSession(req.session_id, s)
            if result.error:
                return customers_pb2.BasicResponse(
                    success=False, message="Session not found or expired"
                )
            try:
                cart = _get_or_create_cart(result.session, s)
                cart_item = (
                    s.query(CartItem)
                    .filter_by(cart_id=cart.id, item_id=req.item_id)
                    .first()
                )
                if cart_item:
                    cart_item.quantity += req.quantity
                else:
                    s.add(
                        CartItem(
                            cart_id=cart.id, item_id=req.item_id, quantity=req.quantity
                        )
                    )
                s.commit()
                return customers_pb2.BasicResponse(
                    success=True, message="Item added to cart successfully"
                )
            except Exception as e:
                s.rollback()
                return customers_pb2.BasicResponse(
                    success=False, message=f"Database error: {e}"
                )

    def _remove_item_from_cart(req):
        with Session(customers_engine) as s:
            result = getAndValidateSession(req.session_id, s)
            if result.error:
                return customers_pb2.BasicResponse(
                    success=False, message="Session not found or expired"
                )
            try:
                cart = _get_or_create_cart(result.session, s)
                cart_item = (
                    s.query(CartItem)
                    .filter_by(cart_id=cart.id, item_id=req.item_id)
                    .first()
                )
                if cart_item:
                    s.delete(cart_item)
                    s.commit()
                    return customers_pb2.BasicResponse(
                        success=True, message="Item removed from cart successfully"
                    )
                return customers_pb2.BasicResponse(
                    success=False, message="Item not found in cart"
                )
            except Exception as e:
                s.rollback()
                return customers_pb2.BasicResponse(
                    success=False, message=f"Database error: {e}"
                )

    def _clear_cart(req):
        with Session(customers_engine) as s:
            result = getAndValidateSession(req.session_id, s)
            if result.error:
                return customers_pb2.BasicResponse(
                    success=False, message="Session not found or expired"
                )
            try:
                cart = _get_or_create_cart(result.session, s)
                saved = (
                    s.query(Cart)
                    .filter_by(buyer_id=result.session.buyer_id, saved=True)
                    .first()
                )
                s.query(CartItem).filter_by(cart_id=cart.id).delete()
                if saved:
                    s.query(CartItem).filter_by(cart_id=saved.id).delete()
                s.commit()
                return customers_pb2.BasicResponse(
                    success=True, message="Cart cleared successfully"
                )
            except Exception as e:
                s.rollback()
                return customers_pb2.BasicResponse(
                    success=False, message=f"Database error: {e}"
                )

    def _save_cart(req):
        with Session(customers_engine) as s:
            result = getAndValidateSession(req.session_id, s)
            if result.error:
                return customers_pb2.BasicResponse(
                    success=False, message="Session not found or expired"
                )
            current_cart = result.session.cart
            if current_cart is None:
                return customers_pb2.BasicResponse(
                    success=False, message="No cart to save"
                )
            current_items = s.query(CartItem).filter_by(cart_id=current_cart.id).all()
            saved = (
                s.query(Cart)
                .filter_by(buyer_id=result.session.buyer_id, saved=True)
                .first()
            )
            if saved is None:
                saved = Cart(
                    buyer_id=result.session.buyer_id, buyer_session_id=None, saved=True
                )
                s.add(saved)
                s.flush()
            else:
                s.query(CartItem).filter_by(cart_id=saved.id).delete()
            for item in current_items:
                s.add(
                    CartItem(
                        cart_id=saved.id, item_id=item.item_id, quantity=item.quantity
                    )
                )
            try:
                s.commit()
                return customers_pb2.BasicResponse(
                    success=True, message="Cart saved successfully"
                )
            except Exception as e:
                s.rollback()
                return customers_pb2.BasicResponse(
                    success=False, message=f"Database error: {e}"
                )

    def _make_purchase(req):
        with Session(customers_engine) as s:
            result = getAndValidateSession(req.session_id, s)
            if result.error:
                return customers_pb2.MakePurchaseResponse(
                    success=False, message="Session not found or expired"
                )
            saved = (
                s.query(Cart)
                .filter_by(buyer_id=result.session.buyer_id, saved=True)
                .first()
            )
            try:
                cart_items = s.query(CartItem).filter_by(cart_id=saved.id).all()
                for ci in cart_items:
                    s.add(
                        ItemsBought(
                            buyer_id=result.session.buyer_id,
                            item_id=ci.item_id,
                            quantity=ci.quantity,
                        )
                    )
                s.commit()
                return customers_pb2.MakePurchaseResponse(success=True)
            except Exception as e:
                s.rollback()
                return customers_pb2.MakePurchaseResponse(
                    success=False, message=f"Purchase failed: {e}"
                )

    shim.register(
        OP_CREATE_ACCOUNT, customers_pb2.CreateAccountRequest, _create_account
    )
    shim.register(OP_LOGIN, customers_pb2.LoginRequest, _login)
    shim.register(OP_LOGOUT, customers_pb2.LogoutRequest, _logout)
    shim.register(
        OP_ADD_ITEM_TO_CART, customers_pb2.AddItemToCartRequest, _add_item_to_cart
    )
    shim.register(
        OP_REMOVE_ITEM_FROM_CART,
        customers_pb2.RemoveItemFromCartRequest,
        _remove_item_from_cart,
    )
    shim.register(OP_CLEAR_CART, customers_pb2.ClearCartRequest, _clear_cart)
    shim.register(OP_SAVE_CART, customers_pb2.SaveCartRequest, _save_cart)
    shim.register(OP_MAKE_PURCHASE, customers_pb2.MakePurchaseRequest, _make_purchase)

    member = Member(
        member_id=member_id,
        n=n,
        peers=peer_addrs,
        deliver_callback=shim.deliver,
    )
    shim.member = member
    api._shim = shim
    member.start()
    return member

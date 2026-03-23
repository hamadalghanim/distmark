"""
customers_broadcast.py — Broadcast shim for the customers service

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


def setup_member(member_id, n, peer_addrs, api) -> Member:
    from proto import customers_pb2
    from db import Buyer, BuyerSession, Cart, CartItem, ItemsBought
    from sqlalchemy.orm import Session
    from utils import customers_engine, getAndValidateSession

    # ── Helpers ───────────────────────────────────────────────────────────────

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
                for ci in s.query(CartItem).filter_by(cart_id=saved.id).all():
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


    # dispatch table each operation calls a function,
    _handlers = {
        OP_CREATE_ACCOUNT: (customers_pb2.CreateAccountRequest, _create_account),
        OP_LOGIN: (customers_pb2.LoginRequest, _login),
        OP_LOGOUT: (customers_pb2.LogoutRequest, _logout),
        OP_ADD_ITEM_TO_CART: (customers_pb2.AddItemToCartRequest, _add_item_to_cart),
        OP_REMOVE_ITEM_FROM_CART: (
            customers_pb2.RemoveItemFromCartRequest,
            _remove_item_from_cart,
        ),
        OP_CLEAR_CART: (customers_pb2.ClearCartRequest, _clear_cart),
        OP_SAVE_CART: (customers_pb2.SaveCartRequest, _save_cart),
        OP_MAKE_PURCHASE: (customers_pb2.MakePurchaseRequest, _make_purchase),
    }

    def _run(opcode, body):
        proto_class, fn = _handlers[opcode]
        req = proto_class()
        req.ParseFromString(body)
        return fn(req)


    _pending: dict = {}
    _pending_lock = threading.Lock()

    def broadcast(opcode, proto_request):
        payload = _OP.pack(opcode) + proto_request.SerializeToString()
        event, rid = member.submit(payload)
        with _pending_lock:
            _pending[rid] = event
        event.wait()
        return _run(opcode, proto_request.SerializeToString())

    def deliver(global_seq, rid, payload):
        with _pending_lock:
            is_mine = _pending.pop(rid, None) is not None
        if not is_mine:
            _run(_OP.unpack_from(payload)[0], payload[1:])

    # ── Wire it up ────────────────────────────────────────────────────────────

    member = Member(member_id, n, peer_addrs, deliver_callback=deliver)
    api._broadcast = broadcast
    member.start()
    return member

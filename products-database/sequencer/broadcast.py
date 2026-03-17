"""
broadcast.py

Design:
  - Every write goes through _broadcast(opcode, proto_request).
  - _broadcast submits to Member and blocks on event.wait().
  - event fires as soon as the global ordering slot is reached (before DB write).
  - The gRPC thread (the one that called _broadcast) then does the DB write
    and returns the response. This means the response is produced by the
    thread that received the RPC — correct, fast, no cross-thread result passing.
  - The Member's deliver_callback runs on the deliver thread for every request
    on every replica. On the submitting replica it is a no-op (DB already done).
    On non-submitting replicas it does the DB write to keep them in sync.
"""

import struct
import logging
import threading
from sequencer.member import Member

logger = logging.getLogger(__name__)

OP_CREATE_ACCOUNT = 0x10
OP_LOGIN = 0x11
OP_LOGOUT = 0x12
OP_REGISTER_ITEM = 0x13
OP_CHANGE_PRICE = 0x14
OP_UPDATE_UNITS = 0x15
OP_PROVIDE_FEEDBACK = 0x16
OP_MAKE_PURCHASE = 0x17

_OP = struct.Struct("!B")


class BroadcastShim:
    """
    Created once per process by setup_member().
    Holds the Member, the opcode->handler map, and the set of rids
    that this node submitted (so deliver_callback knows to skip them).
    """

    def __init__(self):
        self.member: Member = None
        self._handlers: dict = {}  # opcode -> (proto_class, handler_fn)
        self._submitted = (
            set()
        )  # rids submitted by THIS node (deliver_callback skips these)
        self._submitted_lock = threading.Lock()

    def register(self, opcode, proto_class, handler_fn):
        self._handlers[opcode] = (proto_class, handler_fn)

    def broadcast(self, opcode: int, proto_request):
        """
        Submit to broadcast group, wait for ordering slot, do DB write,
        return the response. Called from the gRPC thread.
        """
        payload = _OP.pack(opcode) + proto_request.SerializeToString()
        event, rid = self.member.submit(payload)

        with self._submitted_lock:
            self._submitted.add(rid)

        event.wait()  # unblocks as soon as global slot reached (before any DB write)

        return self._run_handler(opcode, proto_request.SerializeToString())

    def deliver(self, global_seq, rid, payload):
        """
        Called by Member's deliver_callback for every delivered request.
        Skip if this node submitted it (gRPC thread already handles the DB write).
        Otherwise deserialise and run the handler.
        """
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
        logger.debug("deliver global_seq=%d rid=%s opcode=%#x", global_seq, rid, opcode)
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
    """Mixin for SellerAPI. Requires self._shim set by setup_member()."""

    _shim: BroadcastShim

    def _broadcast(self, opcode, proto_request):
        return self._shim.broadcast(opcode, proto_request)


def setup_member(member_id, n, peer_addrs, api) -> Member:
    from proto import products_pb2
    from db import Session as TblSession, Seller, Category, Item
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import IntegrityError
    from utils import products_engine, getAndValidateSession
    import datetime

    shim = BroadcastShim()

    def _create_account(req):
        with Session(products_engine) as s:
            try:
                obj = Seller(
                    name=req.name, username=req.username, password=req.password
                )
                s.add(obj)
                s.commit()
                return products_pb2.CreateAccountResponse(
                    success=True, seller_id=obj.id
                )
            except IntegrityError:
                s.rollback()
                return products_pb2.CreateAccountResponse(
                    success=False, message="Account already exists"
                )
            except Exception as e:
                s.rollback()
                return products_pb2.CreateAccountResponse(
                    success=False, message=f"Database error: {e}"
                )

    def _login(req):
        with Session(products_engine) as s:
            seller = s.query(Seller).filter_by(username=req.username).first()
            if seller is None:
                return products_pb2.LoginResponse(
                    success=False, message="Seller not found"
                )
            if seller.password != req.password:
                return products_pb2.LoginResponse(
                    success=False, message="Invalid username or password"
                )
            try:
                sess = TblSession(
                    seller_id=seller.id,
                    last_activity=datetime.datetime.now(datetime.timezone.utc),
                )
                s.add(sess)
                s.commit()
                return products_pb2.LoginResponse(success=True, session_id=sess.id)
            except Exception as e:
                s.rollback()
                return products_pb2.LoginResponse(
                    success=False, message=f"Database error: {e}"
                )

    def _logout(req):
        with Session(products_engine) as s:
            result = getAndValidateSession(req.session_id, s)
            if result.error:
                return products_pb2.LogoutResponse(success=False, message=result.error)
            try:
                s.delete(result.session)
                s.commit()
                return products_pb2.LogoutResponse(success=True)
            except Exception as e:
                s.rollback()
                return products_pb2.LogoutResponse(
                    success=False, message=f"Database error: {e}"
                )

    def _register_item(req):
        with Session(products_engine) as s:
            result = getAndValidateSession(req.session_id, s)
            if result.error:
                return products_pb2.RegisterItemResponse(
                    success=False, message=result.error
                )
            try:
                item = Item(
                    name=req.item_name,
                    category_id=req.category_id,
                    keywords=req.keywords,
                    condition=req.condition,
                    sale_price=req.price,
                    quantity=req.quantity,
                    seller_id=result.session.seller_id,
                )
                s.add(item)
                s.commit()
                return products_pb2.RegisterItemResponse(success=True, item_id=item.id)
            except Exception as e:
                s.rollback()
                return products_pb2.RegisterItemResponse(
                    success=False, message=f"Database error: {e}"
                )

    def _change_price(req):
        with Session(products_engine) as s:
            result = getAndValidateSession(req.session_id, s)
            if result.error:
                return products_pb2.ChangeItemPriceResponse(
                    success=False, message=result.error
                )
            item = (
                s.query(Item)
                .filter_by(id=req.item_id, seller_id=result.session.seller_id)
                .first()
            )
            if item is None:
                return products_pb2.ChangeItemPriceResponse(
                    success=False, message="Item not found"
                )
            try:
                item.sale_price = float(req.new_price)
                s.add(item)
                s.commit()
                return products_pb2.ChangeItemPriceResponse(
                    success=True, current_price=item.sale_price
                )
            except Exception as e:
                s.rollback()
                return products_pb2.ChangeItemPriceResponse(
                    success=False, message=f"Database error: {e}"
                )

    def _update_units(req):
        with Session(products_engine) as s:
            result = getAndValidateSession(req.session_id, s)
            if result.error:
                return products_pb2.UpdateUnitsResponse(
                    success=False, message=result.error
                )
            item = (
                s.query(Item)
                .filter_by(id=req.item_id, seller_id=result.session.seller_id)
                .first()
            )
            if item is None:
                return products_pb2.UpdateUnitsResponse(
                    success=False, message="Item not found"
                )
            try:
                item.quantity = int(req.new_quantity)
                s.commit()
                return products_pb2.UpdateUnitsResponse(
                    success=True, current_quantity=item.quantity
                )
            except Exception as e:
                s.rollback()
                return products_pb2.UpdateUnitsResponse(
                    success=False, message=f"Database error: {e}"
                )

    def _provide_feedback(req):
        with Session(products_engine) as s:
            item = s.query(Item).filter_by(id=req.item_id).first()
            if item is None:
                return products_pb2.ProvideFeedbackResponse(
                    success=False, message="Item not found"
                )
            item.feedback += req.feedback
            item.seller.feedback += req.feedback
            try:
                s.add(item)
                s.commit()
                return products_pb2.ProvideFeedbackResponse(success=True)
            except Exception as e:
                s.rollback()
                return products_pb2.ProvideFeedbackResponse(
                    success=False, message=f"Database error: {e}"
                )

    def _make_purchase(req):
        with Session(products_engine) as s:
            try:
                for item_qty in req.items:
                    item = s.query(Item).filter_by(id=item_qty.item_id).first()
                    if item is None:
                        s.rollback()
                        return products_pb2.MakePurchaseResponse(
                            success=False, message=f"Item {item_qty.item_id} not found"
                        )
                    if item.quantity < item_qty.quantity:
                        s.rollback()
                        return products_pb2.MakePurchaseResponse(
                            success=False,
                            message=f"Insufficient quantity for {item.name}",
                        )
                    item.quantity -= item_qty.quantity
                    item.seller.items_sold += item_qty.quantity
                s.commit()
                return products_pb2.MakePurchaseResponse(
                    success=True, message="Purchase successful"
                )
            except Exception as e:
                s.rollback()
                return products_pb2.MakePurchaseResponse(
                    success=False, message=f"Database error: {e}"
                )

    shim.register(OP_CREATE_ACCOUNT, products_pb2.CreateAccountRequest, _create_account)
    shim.register(OP_LOGIN, products_pb2.LoginRequest, _login)
    shim.register(OP_LOGOUT, products_pb2.LogoutRequest, _logout)
    shim.register(OP_REGISTER_ITEM, products_pb2.RegisterItemRequest, _register_item)
    shim.register(OP_CHANGE_PRICE, products_pb2.ChangeItemPriceRequest, _change_price)
    shim.register(OP_UPDATE_UNITS, products_pb2.UpdateUnitsRequest, _update_units)
    shim.register(
        OP_PROVIDE_FEEDBACK, products_pb2.ProvideFeedbackRequest, _provide_feedback
    )
    shim.register(OP_MAKE_PURCHASE, products_pb2.MakePurchaseRequest, _make_purchase)

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

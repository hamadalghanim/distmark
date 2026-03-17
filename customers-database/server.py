"""
customers_server.py — CustomerAPI gRPC server with atomic broadcast replication

Write handlers go through self._broadcast() — atomic broadcast ensures all
5 customer nodes execute writes in the same global order.

Read-only handlers (GetCart, GetBuyer, GetBuyerPurchases) query local DB directly.

Environment variables:
  MEMBER_ID    integer 0-based index of this replica
  N_MEMBERS    total number of replicas
  PEER_ADDRS   comma-separated host:port UDP addresses for all replicas in ID order
               e.g. "customers-node0:6100,customers-node1:6101,...,customers-node4:6104"
"""

import os
import logging
from concurrent import futures

import grpc
from proto import customers_pb2
from proto import customers_pb2_grpc

from db import BaseCustomers, Buyer, BuyerSession, Cart, CartItem, ItemsBought
from sqlalchemy.orm import Session
from utils import customers_engine, getAndValidateSession

from sequencer.broadcast import (
    BroadcastMixin,
    setup_member,
    OP_CREATE_ACCOUNT,
    OP_LOGIN,
    OP_LOGOUT,
    OP_ADD_ITEM_TO_CART,
    OP_REMOVE_ITEM_FROM_CART,
    OP_CLEAR_CART,
    OP_SAVE_CART,
    OP_MAKE_PURCHASE,
)


def _load_config():
    member_id = int(os.environ["MEMBER_ID"])
    n = int(os.environ["N_MEMBERS"])
    peers = []
    for p in os.environ["PEER_ADDRS"].split(","):
        host, port = p.strip().rsplit(":", 1)
        peers.append((host, int(port)))
    assert len(peers) == n
    return member_id, n, peers


class CustomerAPI(BroadcastMixin, customers_pb2_grpc.CustomersServiceServicer):
    # ── Writes — go through broadcast ────────────────────────────────────────

    def CreateAccount(self, request, context):
        return self._broadcast(OP_CREATE_ACCOUNT, request)

    def Login(self, request, context):
        return self._broadcast(OP_LOGIN, request)

    def Logout(self, request, context):
        return self._broadcast(OP_LOGOUT, request)

    def AddItemToCart(self, request, context):
        return self._broadcast(OP_ADD_ITEM_TO_CART, request)

    def RemoveItemFromCart(self, request, context):
        return self._broadcast(OP_REMOVE_ITEM_FROM_CART, request)

    def ClearCart(self, request, context):
        return self._broadcast(OP_CLEAR_CART, request)

    def SaveCart(self, request, context):
        return self._broadcast(OP_SAVE_CART, request)

    def MakePurchase(self, request, context):
        return self._broadcast(OP_MAKE_PURCHASE, request)

    # ── Reads — direct local DB query ────────────────────────────────────────

    def GetBuyer(self, request, context):
        with Session(customers_engine) as s:
            result = getAndValidateSession(request.session_id, s)
            if result.error:
                return customers_pb2.GetBuyerResponse(
                    success=False, message="Session not found or expired"
                )
            return customers_pb2.GetBuyerResponse(
                success=True,
                buyer_id=result.session.buyer_id,
                name=result.session.buyer.name,
            )

    def GetCart(self, request, context):
        with Session(customers_engine) as s:
            result = getAndValidateSession(request.session_id, s)
            if result.error:
                return customers_pb2.GetCartResponse(
                    success=False, message="Session not found or expired"
                )
            session = result.session
            try:
                cart = (
                    s.query(Cart)
                    .filter_by(buyer_id=session.buyer_id, buyer_session_id=session.id)
                    .first()
                )
                current_items = (
                    s.query(CartItem).filter_by(cart_id=cart.id).all() if cart else []
                )
                saved = (
                    s.query(Cart)
                    .filter_by(buyer_id=session.buyer_id, saved=True)
                    .first()
                )
                saved_items = (
                    s.query(CartItem).filter_by(cart_id=saved.id).all() if saved else []
                )
                return customers_pb2.GetCartResponse(
                    success=True,
                    message="Cart retrieved",
                    session_cart=[
                        customers_pb2.CartItem(item_id=i.item_id, quantity=i.quantity)
                        for i in current_items
                    ],
                    saved_cart=[
                        customers_pb2.CartItem(item_id=i.item_id, quantity=i.quantity)
                        for i in saved_items
                    ],
                )
            except Exception as e:
                return customers_pb2.GetCartResponse(
                    success=False, message=f"Database error: {e}"
                )

    def GetBuyerPurchases(self, request, context):
        with Session(customers_engine) as s:
            result = getAndValidateSession(request.session_id, s)
            if result.error:
                return customers_pb2.GetBuyerPurchasesResponse(
                    success=False, message="Session not found or expired"
                )
            try:
                items = (
                    s.query(ItemsBought)
                    .filter_by(buyer_id=result.session.buyer_id)
                    .all()
                )
                return customers_pb2.GetBuyerPurchasesResponse(
                    success=True,
                    message="Purchases retrieved",
                    purchases=[
                        customers_pb2.PurchaseItem(
                            item_id=i.item_id, quantity=i.quantity
                        )
                        for i in items
                    ],
                )
            except Exception as e:
                return customers_pb2.GetBuyerPurchasesResponse(
                    success=False, message=f"Database Error: {e}"
                )


def serve():
    member_id, n, peer_addrs = _load_config()
    BaseCustomers.metadata.create_all(customers_engine)

    api = CustomerAPI()
    member = setup_member(member_id, n, peer_addrs, api)

    grpc_port = "5000"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    customers_pb2_grpc.add_CustomersServiceServicer_to_server(api, server)
    server.add_insecure_port("[::]:" + grpc_port)
    server.start()
    print(
        f"Customer replica {member_id}/{n} gRPC :{grpc_port}  UDP {peer_addrs[member_id]}"
    )
    try:
        server.wait_for_termination()
    finally:
        member.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()

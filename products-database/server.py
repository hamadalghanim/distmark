import os
import logging
from concurrent import futures

import grpc
from proto import products_pb2
from proto import products_pb2_grpc

from db import BaseProducts, Category, Item, Seller
from sqlalchemy.orm import Session
from utils import products_engine, getAndValidateSession
from sequencer.broadcast import (
    BroadcastMixin,
    setup_member,
    OP_CREATE_ACCOUNT,
    OP_LOGIN,
    OP_LOGOUT,
    OP_REGISTER_ITEM,
    OP_CHANGE_PRICE,
    OP_UPDATE_UNITS,
    OP_PROVIDE_FEEDBACK,
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


class SellerAPI(BroadcastMixin, products_pb2_grpc.SellerService):
    def CreateAccount(self, request, context):
        return self._broadcast(OP_CREATE_ACCOUNT, request)

    def Login(self, request, context):
        return self._broadcast(OP_LOGIN, request)

    def Logout(self, request, context):
        return self._broadcast(OP_LOGOUT, request)

    def RegisterItemForSale(self, request, context):
        return self._broadcast(OP_REGISTER_ITEM, request)

    def ChangeItemPrice(self, request, context):
        return self._broadcast(OP_CHANGE_PRICE, request)

    def UpdateUnitsForSale(self, request, context):
        return self._broadcast(OP_UPDATE_UNITS, request)

    def ProvideFeedback(self, request, context):
        return self._broadcast(OP_PROVIDE_FEEDBACK, request)

    def MakePurchase(self, request, context):
        return self._broadcast(OP_MAKE_PURCHASE, request)

    # ── Reads ─────────────────────────────────────────────────────────────────

    def GetSellerRating(self, request, context):
        with Session(products_engine) as s:
            result = getAndValidateSession(request.session_id, s)
            if result.error:
                return products_pb2.RatingResponse(success=False, message=result.error)
            return products_pb2.RatingResponse(
                success=True, feedback=result.session.seller.feedback
            )

    def GetSellerRatingById(self, request, context):
        with Session(products_engine) as s:
            seller = s.query(Seller).filter_by(id=request.seller_id).first()
            if seller is None:
                return products_pb2.RatingResponse(
                    success=False, message="Seller not found"
                )
            return products_pb2.RatingResponse(feedback=seller.feedback, success=True)

    def DisplayItemsForSale(self, request, context):
        with Session(products_engine) as s:
            result = getAndValidateSession(request.session_id, s)
            if result.error:
                return products_pb2.ItemListResponse(
                    success=False, message=result.error
                )
            items = s.query(Item).filter_by(seller_id=result.session.seller_id).all()
            return products_pb2.ItemListResponse(
                success=True,
                items=[
                    products_pb2.Item(
                        id=i.id,
                        name=i.name,
                        quantity=i.quantity,
                        sale_price=i.sale_price,
                        category_id=i.category_id,
                        condition=i.condition.name,
                        keywords=i.keywords,
                    )
                    for i in items
                ],
            )

    def GetItem(self, request, context):
        with Session(products_engine) as s:
            item = s.query(Item).filter_by(id=request.item_id).first()
            if item is None:
                return products_pb2.GetItemResponse(
                    success=False, message="Item not found"
                )
            return products_pb2.GetItemResponse(
                success=True,
                item=products_pb2.Item(
                    id=item.id,
                    name=item.name,
                    category_id=item.category_id,
                    keywords=item.keywords,
                    condition=item.condition.name,
                    sale_price=item.sale_price,
                    quantity=item.quantity,
                    seller_id=item.seller_id,
                ),
            )

    def SearchItemsForSale(self, request, context):
        with Session(products_engine) as s:
            query = s.query(Item)
            if request.category_id != 0:
                query = query.filter_by(category_id=request.category_id)
            for kw in request.keywords:
                query = query.filter(Item.keywords.ilike(f"%{kw.strip()}%"))
            items = query.all()
            return products_pb2.ItemListResponse(
                success=True,
                items=[
                    products_pb2.Item(
                        id=i.id,
                        name=i.name,
                        category_id=i.category_id,
                        keywords=i.keywords,
                        condition=i.condition.name,
                        sale_price=i.sale_price,
                        quantity=i.quantity,
                        seller_id=i.seller_id,
                    )
                    for i in items
                ],
            )

    def GetCategoriesClient(self, request, context):
        with Session(products_engine) as s:
            cats = s.query(Category).all()
            return products_pb2.CategoryListResponse(
                success=True,
                categories=[products_pb2.Category(id=c.id, name=c.name) for c in cats],
            )

    def GetCategories(self, request, context):
        with Session(products_engine) as s:
            result = getAndValidateSession(request.session_id, s)
            if result.error:
                return products_pb2.CategoryListResponse(
                    success=False, message=result.error
                )
            cats = s.query(Category).all()
            return products_pb2.CategoryListResponse(
                success=True,
                categories=[products_pb2.Category(id=c.id, name=c.name) for c in cats],
            )


def seed(engine):
    with Session(engine) as s:
        if s.query(Category).count() == 0:
            s.add_all(
                [
                    Category(name="Electronics"),
                    Category(name="Art"),
                    Category(name="Home"),
                ]
            )
            s.commit()


def serve():
    member_id, n, peer_addrs = _load_config()
    BaseProducts.metadata.create_all(products_engine)
    seed(products_engine)

    api = SellerAPI()
    member = setup_member(member_id, n, peer_addrs, api)

    grpc_port = "5000"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    products_pb2_grpc.add_SellerServiceServicer_to_server(api, server)
    server.add_insecure_port("[::]:" + grpc_port)
    server.start()
    print(f"Replica {member_id + 1}/{n} gRPC :{grpc_port}  UDP {peer_addrs[member_id]}")
    try:
        server.wait_for_termination()
    finally:
        member.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()

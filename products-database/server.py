"""
server.py — Products/Seller gRPC server with Raft replication

IDs for new rows (seller_id, session_id, item_id) are generated HERE, before
the Raft call, so that every replica inserts the same value.  This avoids the
per-node postgres auto-increment divergence problem.
"""

import os
import secrets
import logging
from concurrent import futures
from sqlalchemy import text

import grpc
from proto import products_pb2
from proto import products_pb2_grpc

from db import BaseProducts, Category, Item, Seller
from sqlalchemy.orm import Session
from utils import products_engine, getAndValidateSession
from products_raft import RaftMixin, setup_raft


def _new_id() -> int:
    """Generate a random positive 31-bit integer safe for use as a postgres int PK."""
    return secrets.randbelow(2**31 - 1) + 1


def _load_config():
    member_id = int(os.environ["MEMBER_ID"])
    raft_addrs = [p.strip() for p in os.environ["RAFT_ADDRS"].split(",")]
    return member_id, raft_addrs


class SellerAPI(RaftMixin, products_pb2_grpc.SellerServiceServicer):
    # ── Writes — replicated via Raft ─────────────────────────────────────────

    def CreateAccount(self, request, context):
        return self._raft.create_account(
            _new_id(),
            request.name,
            request.username,
            request.password,
            sync=True,
        )

    def Login(self, request, context):
        return self._raft.login(
            _new_id(),
            request.username,
            request.password,
            sync=True,
        )

    def Logout(self, request, context):
        return self._raft.logout(request.session_id, sync=True)

    def RegisterItemForSale(self, request, context):
        return self._raft.register_item(
            _new_id(),
            request.session_id,
            request.item_name,
            request.category_id,
            request.keywords,
            request.condition,
            request.price,
            request.quantity,
            sync=True,
        )

    def ChangeItemPrice(self, request, context):
        return self._raft.change_price(
            request.session_id,
            request.item_id,
            request.new_price,
            sync=True,
        )

    def UpdateUnitsForSale(self, request, context):
        return self._raft.update_units(
            request.session_id,
            request.item_id,
            request.new_quantity,
            sync=True,
        )

    def ProvideFeedback(self, request, context):
        return self._raft.provide_feedback(
            request.item_id,
            request.feedback,
            sync=True,
        )

    def MakePurchase(self, request, context):
        items = [(i.item_id, i.quantity) for i in request.items]
        return self._raft.make_purchase(items, sync=True)

    # ── Reads — local DB query ────────────────────────────────────────────────

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

            rows = (
                s.query(Item)
                .filter(Item.seller_id == result.session.seller_id)
                .with_entities(
                    Item.id,
                    Item.name,
                    Item.quantity,
                    Item.sale_price,
                    Item.category_id,
                    Item.condition,
                    Item.keywords,
                )
                .all()
            )

            return products_pb2.ItemListResponse(
                success=True,
                items=[
                    products_pb2.Item(
                        id=r.id,
                        name=r.name,
                        quantity=r.quantity,
                        sale_price=r.sale_price,
                        category_id=r.category_id,
                        condition=r.condition.name,
                        keywords=r.keywords,
                    )
                    for r in rows
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
            query = s.query(Item).filter(Item.quantity > 0)

            if request.category_id != 0:
                query = query.filter(Item.category_id == request.category_id)

            for kw in request.keywords:
                kw = kw.strip()
                if kw:
                    query = query.filter(Item.keywords.ilike(f"%{kw}%"))

            rows = (
                query.with_entities(
                    Item.id,
                    Item.name,
                    Item.category_id,
                    Item.keywords,
                    Item.condition,
                    Item.sale_price,
                    Item.quantity,
                    Item.seller_id,
                )
                .limit(50)
                .all()
            )

            return products_pb2.ItemListResponse(
                success=True,
                items=[
                    products_pb2.Item(
                        id=r.id,
                        name=r.name,
                        category_id=r.category_id,
                        keywords=r.keywords,
                        condition=r.condition.name,
                        sale_price=r.sale_price,
                        quantity=r.quantity,
                        seller_id=r.seller_id,
                    )
                    for r in rows
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
    BaseProducts.metadata.create_all(engine)

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
    member_id, raft_addrs = _load_config()
    seed(products_engine)

    api = SellerAPI()
    raft = setup_raft(member_id, raft_addrs, api)

    grpc_port = "5000"

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=4), options=[("grpc.so_reuseport", 0)]
    )
    products_pb2_grpc.add_SellerServiceServicer_to_server(api, server)
    server.add_insecure_port("[::]:" + grpc_port)
    server.start()
    print(
        f"Products node {member_id}/{len(raft_addrs)} gRPC :{grpc_port}  Raft {raft_addrs[member_id]}"
    )
    try:
        server.wait_for_termination()
    finally:
        raft.destroy()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()

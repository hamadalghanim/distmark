from concurrent import futures
import logging

import grpc
from proto import products_pb2
from proto import products_pb2_grpc

import datetime
from db import BaseProducts, Seller, Category, Item
from db import Session as TblSession

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from utils import products_engine, getAndValidateSession


class SellerAPI(products_pb2_grpc.SellerService):
    def CreateAccount(self, request: products_pb2.CreateAccountRequest, context):
        with Session(products_engine) as products_session:
            try:
                obj = Seller(
                    name=request.name,
                    username=request.username,
                    password=request.password,
                )
                products_session.add(obj)
                products_session.commit()
            except IntegrityError:
                products_session.rollback()
                return products_pb2.CreateAccountResponse(
                    success=False, message="Error: Account already exists"
                )
            except Exception as e:
                products_session.rollback()
                return products_pb2.CreateAccountResponse(
                    success=False, message=f"Database error: {e}"
                )

            return products_pb2.CreateAccountResponse(success=True, seller_id=obj.id)

    def Login(self, request: products_pb2.LoginRequest, context):
        with Session(products_engine) as products_session:
            try:
                seller = (
                    products_session.query(Seller)
                    .filter_by(username=request.username)
                    .first()
                )
            except Exception as e:
                return products_pb2.LoginResponse(
                    success=False, message=f"Database error: {e}"
                )

            if seller is None:
                return products_pb2.LoginResponse(
                    success=False, message="Seller not found"
                )

            if seller.password != request.password:
                return products_pb2.LoginResponse(
                    success=False, message="Invalid username or password"
                )
            try:
                _session = TblSession(
                    seller_id=seller.id,
                    last_activity=datetime.datetime.now(datetime.timezone.utc),
                )
                products_session.add(_session)
                products_session.commit()
            except Exception as e:
                products_session.rollback()
                return products_pb2.LoginResponse(
                    success=False, message=f"Database error: {e}"
                )

            return products_pb2.LoginResponse(success=True, session_id=_session.id)

    def Logout(self, request: products_pb2.LogoutRequest, context):
        with Session(products_engine) as products_session:
            session_id = request.session_id
            result = getAndValidateSession(session_id, products_session)
            if result.error:
                return products_pb2.LogoutResponse(success=False, message=result.error)
            else:
                session = result.session
            try:
                products_session.delete(session)
                products_session.commit()
            except Exception as e:
                products_session.rollback()
                return products_pb2.LogoutResponse(
                    success=False, message=f"Database error: {e}"
                )

            return products_pb2.LogoutResponse(success=True)

    def GetSellerRating(self, request: products_pb2.GetSellerRatingRequest, context):
        with Session(products_engine) as products_session:
            result = getAndValidateSession(request.session_id, products_session)
            if result.error:
                return products_pb2.RatingResponse(success=False, message=result.error)
            else:
                session = result.session

            return products_pb2.RatingResponse(
                success=True, feedback=session.seller.feedback
            )

    def RegisterItemForSale(self, request: products_pb2.RegisterItemRequest, context):
        with Session(products_engine) as products_session:
            result = getAndValidateSession(request.session_id, products_session)
            if result.error:
                return products_pb2.RegisterItemResponse(
                    success=False, message=result.error
                )
            else:
                session = result.session
            try:
                item = Item(
                    name=request.item_name,
                    category_id=request.category_id,
                    keywords=request.keywords,
                    condition=request.condition,
                    sale_price=request.price,
                    quantity=request.quantity,
                    seller_id=session.seller_id,
                )
                products_session.add(item)
                products_session.commit()
            except Exception as e:
                products_session.rollback()
                return products_pb2.RegisterItemResponse(
                    success=False, message=f"Database Error: {e}"
                )

            return products_pb2.RegisterItemResponse(success=True, item_id=item.id)

    def ChangeItemPrice(self, request: products_pb2.ChangeItemPriceRequest, context):
        with Session(products_engine) as products_session:
            # Structure "command name", "session_id","item_id" "new_price"
            result = getAndValidateSession(request.session_id, products_session)
            if result.error:
                return products_pb2.ChangeItemPriceResponse(
                    success=False, message=result.error
                )
            else:
                session = result.session

            try:
                item = (
                    products_session.query(Item)
                    .filter_by(id=request.item_id, seller_id=session.seller_id)
                    .first()
                )
            except Exception as e:
                return products_pb2.ChangeItemPriceResponse(
                    success=False, message=f"Database error: {e}"
                )
            if item is None:
                return products_pb2.ChangeItemPriceResponse(
                    success=False, message="Item not found"
                )
            try:
                item.sale_price = float(request.new_price)
                products_session.add(item)
                products_session.commit()
            except Exception as e:
                products_session.rollback()
                return products_pb2.ChangeItemPriceResponse(
                    success=False, message=f"Database error: {e}"
                )
                return
            return products_pb2.ChangeItemPriceResponse(
                success=True, current_price=item.sale_price
            )

    def UpdateUnitsForSale(self, request: products_pb2.UpdateUnitsRequest, context):
        with Session(products_engine) as products_session:
            result = getAndValidateSession(request.session_id, products_session)
            if result.error:
                return products_pb2.UpdateUnitsResponse(
                    success=False,
                    message=result.error,
                )

            session = result.session

            try:
                item = (
                    products_session.query(Item)
                    .filter_by(id=request.item_id, seller_id=session.seller_id)
                    .first()
                )
            except Exception as e:
                return products_pb2.UpdateUnitsResponse(
                    success=False,
                    message=f"Database error: {e}",
                )

            if item is None:
                return products_pb2.UpdateUnitsResponse(
                    success=False,
                    message="Item not found",
                )

            try:
                item.quantity = int(request.new_quantity)
                products_session.commit()
            except Exception as e:
                products_session.rollback()
                return products_pb2.UpdateUnitsResponse(
                    success=False,
                    message=f"Database error: {e}",
                )

            return products_pb2.UpdateUnitsResponse(
                success=True,
                current_quantity=item.quantity,
            )

    def DisplayItemsForSale(self, request: products_pb2.DisplayItemsRequest, context):
        with Session(products_engine) as products_session:
            result = getAndValidateSession(request.session_id, products_session)
            if result.error:
                return products_pb2.ItemListResponse(
                    success=False,
                    message=result.error,
                )
            session = result.session
            try:
                items = (
                    products_session.query(Item)
                    .filter_by(seller_id=session.seller_id)
                    .all()
                )
            except Exception as e:
                return products_pb2.ItemListResponse(
                    success=False,
                    message=f"Database error: {e}",
                )

            if not items:
                return products_pb2.ItemListResponse(
                    success=True,
                    items=[],
                )
            proto_items = [
                products_pb2.Item(
                    id=item.id,
                    name=item.name,
                    quantity=item.quantity,
                    sale_price=item.sale_price,
                    category_id=item.category_id,
                    condition=item.condition.name,
                    keywords=item.keywords,
                )
                for item in items
            ]

            return products_pb2.ItemListResponse(
                success=True,
                items=proto_items,
            )

    def GetCategories(self, request: products_pb2.GetCategoriesRequest, context):
        with Session(products_engine) as products_session:
            # TODO: figure out where to do activity check
            # result = getAndValidateSession(request.session_id, products_session)
            # if result.error:
            #     return products_pb2.CategoryListResponse(
            #         success=False,
            #         message=result.error,
            #     )

            try:
                categories = products_session.query(Category).all()
            except Exception as e:
                return products_pb2.CategoryListResponse(
                    success=False,
                    message=f"Database error: {e}",
                )

            proto_categories = [
                products_pb2.Category(
                    id=category.id,
                    name=category.name,
                )
                for category in categories
            ]

            return products_pb2.CategoryListResponse(
                success=True,
                categories=proto_categories,
            )

    def GetItem(self, request: products_pb2.GetItemRequest, context):
        with Session(products_engine) as products_session:
            try:
                item = (
                    products_session.query(Item).filter_by(id=request.item_id).first()
                )
            except Exception as e:
                return products_pb2.GetItemResponse(
                    success=False, message=f"Database error: {e}"
                )

            item = products_pb2.Item(
                id=item.id,
                name=item.name,
                category_id=item.category_id,
                keywords=item.keywords,
                condition=item.condition.name,
                sale_price=item.sale_price,
                quantity=item.quantity,
                seller_id=item.seller_id,
            )
            return products_pb2.GetItemResponse(item=item, success=True)

    def SearchItemsForSale(self, request: products_pb2.SearchItemsRequest, context):
        with Session(products_engine) as products_session:
            try:
                query = products_session.query(Item)
                if request.category_id != 0:  # assuming 0 means all categories
                    query = query.filter_by(category_id=request.category_id)
                if len(request.keywords):
                    for keyword in request.keywords:
                        query = query.filter(
                            Item.keywords.ilike(f"%{keyword.strip()}%")
                        )
                items = query.all()
            except Exception as e:
                return products_pb2.ItemListResponse(
                    success=False, message=f"Database Error: {e}"
                )

            result = [
                products_pb2.Item(
                    id=item.id,
                    name=item.name,
                    category_id=item.category_id,
                    keywords=item.keywords,
                    condition=item.condition.name,
                    sale_price=item.sale_price,
                    quantity=item.quantity,
                    seller_id=item.seller_id,
                )
                for item in items
            ]
            return products_pb2.ItemListResponse(success=True, items=result)

    def ProvideFeedback(self, request: products_pb2.ProvideFeedbackRequest, context):
        with Session(products_engine) as products_session:
            # TODO: for later assignments check item if purchased by buyer through ItemsBought table
            item = products_session.query(Item).filter_by(id=request.item_id).first()
            if item is None:
                return products_pb2.ProvideFeedbackResponse(
                    success=False, message="Item not found"
                )
            feedback = request.feedback
            item.feedback += feedback
            item.seller.feedback += feedback
            try:
                products_session.add(item)
                products_session.commit()
            except Exception as e:
                products_session.rollback()
                return products_pb2.ProvideFeedbackResponse(
                    success=False, message=f"Database error: {e}"
                )
            return products_pb2.ProvideFeedbackResponse(success=True)

    def GetSellerRatingById(
        self, request: products_pb2.GetSellerRatingByIdRequest, context
    ):
        with Session(products_engine) as products_session:
            try:
                seller = (
                    products_session.query(Seller)
                    .filter_by(id=request.seller_id)
                    .first()
                )
            except Exception as e:
                return products_pb2.RatingResponse(
                    success=False, message=f"Database error: {e}"
                )

            if seller is None:
                return products_pb2.RatingResponse(
                    success=False, message="Seller not found"
                )
            return products_pb2.RatingResponse(feedback=seller.feedback, success=True)


def seed(products_engine):
    print("Seeding categories...")
    with Session(products_engine) as products_session:
        try:
            count = products_session.query(Category).count()
            if count == 0:
                print("Seeding categories...")
                categories = [
                    Category(name="Electronics"),
                    Category(name="Art"),
                    Category(name="Home"),
                ]
                products_session.add_all(categories)
                products_session.commit()
                print("Categories seeded successfully")
        except Exception as e:
            products_session.rollback()
            print(f"Error seeding database: {e}")


def serve():
    BaseProducts.metadata.create_all(products_engine)
    seed(products_engine)
    port = "5000"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    products_pb2_grpc.add_SellerServiceServicer_to_server(SellerAPI(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    serve()

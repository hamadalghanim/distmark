from concurrent import futures
import datetime
import grpc
import logging
from db import Buyer, BuyerSession, Cart, CartItem, ItemsBought, Item
from sqlalchemy.orm import Session

# Import generated proto files (after running protoc)
import customers_pb2
import customers_pb2_grpc

from utils import customers_engine, getAndValidateSession


class CustomerAPI(customers_pb2_grpc.CustomersServiceServicer):
    def _get_or_create_cart(session: BuyerSession, customers_session: Session) -> Cart:
        cart = (
            customers_session.query(Cart)
            .filter_by(buyer_id=session.buyer_id, buyer_session_id=session.id)
            .first()
        )
        if cart is None:
            cart = Cart(buyer_id=session.buyer_id, buyer_session_id=session.id)
            customers_session.add(cart)
            customers_session.commit()
        return cart

    def CreateAccount(
        self, request: customers_pb2.CreateAccountRequest, context
    ) -> customers_pb2.CreateAccountResponse:

        with Session(customers_engine) as customers_session:
            try:
                obj = Buyer(
                    name=request.username,
                    username=request.username,
                    password=request.password,
                )
                customers_session.add(obj)
                customers_session.commit()
                return customers_pb2.CreateAccountResponse(
                    success=True,
                    message=f"Buyer created with ID: {obj.id}",
                    buyer_id=obj.id,
                )
            except Exception as e:
                customers_session.rollback()
                return customers_pb2.CreateAccountResponse(
                    success=False, message=f"Database error: {e}"
                )

    def Login(
        self, request: customers_pb2.LoginRequest, context
    ) -> customers_pb2.LoginResponse:
        with Session(customers_engine) as customers_session:
            try:
                buyer = (
                    customers_session.query(Buyer)
                    .filter_by(username=request.username)
                    .first()
                )
            except Exception as e:
                return customers_pb2.LoginResponse(
                    success=False,
                    message=f"Database error: {e}",
                )

            if buyer is None:
                return customers_pb2.LoginResponse(
                    success=False,
                    message="Buyer not found",
                )

            if buyer.password != request.password:
                return customers_pb2.LoginResponse(
                    success=False,
                    message="Invalid username or password",
                )

            try:
                _session = BuyerSession(
                    buyer_id=buyer.id,
                    last_activity=datetime.datetime.now(datetime.timezone.utc),
                )
                _session.cart = Cart(buyer_id=buyer.id)
                customers_session.add(_session)
                customers_session.commit()
                return customers_pb2.LoginResponse(
                    success=True, message="Login successful", session_id=_session.id
                )
            except Exception as e:
                customers_session.rollback()
                return customers_pb2.LoginResponse(
                    success=False,
                    message=f"Database error: {e}",
                )

    def GetBuyer(
        self, request: customers_pb2.GetBuyerRequest, context
    ) -> customers_pb2.BasicResponse:
        with Session(customers_engine) as customers_session:
            result = getAndValidateSession(request.session_id, customers_session)
            if result.error:
                return customers_pb2.GetBuyerResponse(
                    success=False, message="Session not found or expired"
                )
            session = result.session
        return customers_pb2.GetBuyerResponse(success=True, buyer_id=session.buyer_id)

    def Logout(
        self, request: customers_pb2.LogoutRequest, context
    ) -> customers_pb2.BasicResponse:
        with Session(customers_engine) as customers_session:
            result = getAndValidateSession(request.session_id, customers_session)
            if result.error:
                return customers_pb2.BasicResponse(
                    success=False, message="Session not found or expired"
                )
            session = result.session

            try:
                customers_session.delete(session)
                customers_session.commit()
                return customers_pb2.BasicResponse(
                    success=True, message="Logout successful"
                )
            except Exception as e:
                customers_session.rollback()
                return customers_pb2.BasicResponse(
                    success=False, message=f"Database error: {e}"
                )

    def AddItemToCart(
        self, request: customers_pb2.AddItemToCartRequest, context
    ) -> customers_pb2.BasicResponse:
        with Session(customers_engine) as customers_session:
            result = getAndValidateSession(request.session_id, customers_session)
            if result.error:
                return customers_pb2.BasicResponse(
                    success=False, message="Session not found or expired"
                )
            session = result.session

            try:
                cart = self._get_or_create_cart(session, customers_session)
                cart_item = (
                    customers_session.query(CartItem)
                    .filter_by(cart_id=cart.id, item_id=request.item_id)
                    .first()
                )
                if cart_item:
                    cart_item.quantity += request.quantity
                else:
                    cart_item = CartItem(
                        cart_id=cart.id,
                        item_id=request.item_id,
                        quantity=request.quantity,
                    )
                    customers_session.add(cart_item)
                customers_session.commit()
                return customers_pb2.BasicResponse(
                    success=True, message="Item added to cart successfully"
                )
            except Exception as e:
                customers_session.rollback()
                return customers_pb2.BasicResponse(
                    success=False, message=f"Database error: {e}"
                )

    def RemoveItemFromCart(
        self, request: customers_pb2.RemoveItemFromCartRequest, context
    ) -> customers_pb2.BasicResponse:
        with Session(customers_engine) as customers_session:
            result = getAndValidateSession(request.session_id, customers_session)
            if result.error:
                return customers_pb2.BasicResponse(
                    success=False, message="Session not found or expired"
                )
            session = result.session

            try:
                cart = self._get_or_create_cart(session, customers_session)
                cart_item = (
                    customers_session.query(CartItem)
                    .filter_by(cart_id=cart.id, item_id=request.item_id)
                    .first()
                )
                if cart_item:
                    customers_session.delete(cart_item)
                    customers_session.commit()
                    return customers_pb2.BasicResponse(
                        success=True, message="Item removed from cart successfully"
                    )
                else:
                    return customers_pb2.BasicResponse(
                        success=False, message="Item not found in cart"
                    )
            except Exception as e:
                customers_session.rollback()
                return customers_pb2.BasicResponse(
                    success=False, message=f"Database error: {e}"
                )

    def ClearCart(
        self, request: customers_pb2.ClearCartRequest, context
    ) -> customers_pb2.BasicResponse:
        with Session(customers_engine) as customers_session:
            result = getAndValidateSession(request.session_id, customers_session)
            if result.error:
                return customers_pb2.BasicResponse(
                    success=False, message="Session not found or expired"
                )
            session = result.session

            try:
                cart = self._get_or_create_cart(session, customers_session)
                active_cart = (
                    customers_session.query(Cart)
                    .filter_by(buyer_id=session.buyer_id, saved=True)
                    .first()
                )
                customers_session.query(CartItem).filter_by(cart_id=cart.id).delete()
                if active_cart is not None:
                    customers_session.query(CartItem).filter_by(
                        cart_id=active_cart.id
                    ).delete()
                customers_session.commit()
                return customers_pb2.BasicResponse(
                    success=True, message="Cart cleared successfully"
                )
            except Exception as e:
                customers_session.rollback()
                return customers_pb2.BasicResponse(
                    success=False, message=f"Database error: {e}"
                )

    def SaveCart(
        self, request: customers_pb2.SaveCartRequest, context
    ) -> customers_pb2.BasicResponse:
        with Session(customers_engine) as customers_session:
            result = getAndValidateSession(request.session_id, customers_session)
            if result.error:
                return customers_pb2.BasicResponse(
                    success=False, message="Session not found or expired"
                )
            session = result.session
            current_cart = session.cart

            if current_cart is None:
                return customers_pb2.BasicResponse(
                    success=False, message="No cart to save"
                )

            current_cart_items = (
                customers_session.query(CartItem)
                .filter_by(cart_id=current_cart.id)
                .all()
            )

            saved_cart = (
                customers_session.query(Cart)
                .filter_by(buyer_id=session.buyer_id, saved=True)
                .first()
            )

            if saved_cart is None:
                saved_cart = Cart(
                    buyer_id=session.buyer_id,
                    buyer_session_id=None,
                    saved=True,
                )
                customers_session.add(saved_cart)
                customers_session.flush()
            else:
                customers_session.query(CartItem).filter_by(
                    cart_id=saved_cart.id
                ).delete()

            for item in current_cart_items:
                saved_item = CartItem(
                    cart_id=saved_cart.id, item_id=item.item_id, quantity=item.quantity
                )
                customers_session.add(saved_item)

            try:
                customers_session.commit()
                return customers_pb2.BasicResponse(
                    success=True, message="Cart saved successfully"
                )
            except Exception as e:
                customers_session.rollback()
                return customers_pb2.BasicResponse(
                    success=False, message=f"Database error: {e}"
                )

    def GetCart(
        self, request: customers_pb2.GetCartRequest, context
    ) -> customers_pb2.GetCartResponse:
        with Session(customers_engine) as customers_session:
            result = getAndValidateSession(request.session_id, customers_session)
            if result.error:
                return customers_pb2.GetCartResponse(
                    success=False,
                    message="Session not found or expired",
                )

            session = result.session

            try:
                current_cart = self._get_or_create_cart(session, customers_session)
                current_cart_items = (
                    customers_session.query(CartItem)
                    .filter_by(cart_id=current_cart.id)
                    .all()
                )

                saved_cart = (
                    customers_session.query(Cart)
                    .filter_by(buyer_id=session.buyer_id, saved=True)
                    .first()
                )

                saved_cart_items = []
                if saved_cart:
                    saved_cart_items = (
                        customers_session.query(CartItem)
                        .filter_by(cart_id=saved_cart.id)
                        .all()
                    )

                # Convert to protobuf format
                current_items_proto = [
                    customers_pb2.CartItem(item_id=item.id, quantity=item.quantity)
                    for item in current_cart_items
                ]

                saved_items_proto = [
                    customers_pb2.CartItem(item_id=item.id, quantity=item.quantity)
                    for item in saved_cart_items
                ]

                return customers_pb2.GetCartResponse(
                    success=True,
                    message="Cart retrieved",
                    session_cart=current_items_proto,
                    saved_cart=saved_items_proto,
                )

            except Exception as e:
                customers_session.rollback()
                return customers_pb2.GetCartResponse(
                    success=False, message=f"Database error: {e}"
                )

    def GetBuyerPurchases(
        self, request: customers_pb2.GetBuyerPurchasesRequest, context
    ) -> customers_pb2.GetBuyerPurchasesResponse:
        with Session(customers_engine) as customers_session:
            result = getAndValidateSession(request.session_id, customers_session)
            if result.error:
                return customers_pb2.GetBuyerPurchasesResponse(
                    success=False,
                    message="Session not found or expired",
                )
            session = result.session
            if session is None:
                return

            try:
                items_bought: list[ItemsBought] = (
                    customers_session.query(ItemsBought)
                    .filter_by(buyer_id=session.buyer_id)
                    .all()
                )
            except Exception as e:
                return customers_pb2.GetBuyerPurchasesResponse(
                    success=False,
                    message=f"Database Error: {e}",
                )

            purchases = [
                customers_pb2.PurchaseItem(item_id=item.item_id, quantity=item.quantity)
                for item in items_bought
            ]

            return customers_pb2.GetBuyerPurchasesResponse(
                success=True, message="Purchases retrieved", purchases=purchases
            )


def serve() -> None:
    """Start the gRPC server."""
    port = "5000"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    customers_pb2_grpc.add_CustomersServiceServicer_to_server(CustomerAPI(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig()
    serve()

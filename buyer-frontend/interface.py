import grpc
from proto import customers_pb2
from proto import customers_pb2_grpc
from proto import products_pb2
from proto import products_pb2_grpc
from zeep import Client
import os

# gRPC setup
CUSTOMERS_GRPC_HOST = os.getenv("CUSTOMERS_DB_RPC_HOST", "customers-db-rpc")
CUSTOMERS_GRPC_PORT = os.getenv("CUSTOMERS_DB_RPC_PORT", "5000")
CUSTOMERS_GRPC_ADDRESS = f"{CUSTOMERS_GRPC_HOST}:{CUSTOMERS_GRPC_PORT}"

PRODUCTS_GRPC_HOST = os.getenv("PRODUCTS_DB_RPC_HOST", "products-db-rpc")
PRODUCTS_GRPC_PORT = os.getenv("PRODUCTS_DB_RPC_PORT", "5000")
PRODUCTS_GRPC_ADDRESS = f"{PRODUCTS_GRPC_HOST}:{PRODUCTS_GRPC_PORT}"

_customers_channel = grpc.insecure_channel(CUSTOMERS_GRPC_ADDRESS)
_customers_stub = customers_pb2_grpc.CustomersServiceStub(_customers_channel)

_products_channel = grpc.insecure_channel(PRODUCTS_GRPC_ADDRESS)
_products_stub = products_pb2_grpc.SellerServiceStub(_products_channel)

# soap setup
WSDL_PAYMENT_HOST = os.getenv("WSDL_PAYMENT_HOST", "payments-api")
WSDL_PAYMENT_PORT = os.getenv("WSDL_PAYMENT_PORT", "5000")
PAYMENT_ADDRESS = f"http://{WSDL_PAYMENT_HOST}:{WSDL_PAYMENT_PORT}/?wsdl"


def _item_to_dict(item):
    """Helper to convert a gRPC item object to a dictionary."""
    return {
        "id": item.id,
        "name": item.name,
        "category_id": item.category_id,
        "keywords": item.keywords,
        "condition": item.condition,
        "sale_price": item.sale_price,
        "quantity": item.quantity,
        "seller_id": item.seller_id,
    }


def createAccount(data):
    # Data comes from request.json
    name = data.get("name")
    username = data.get("username")
    password = data.get("password")

    try:
        request = customers_pb2.CreateAccountRequest(
            name=name, username=username, password=password
        )
        response = _customers_stub.CreateAccount(request)

        if response.success:
            return {"result": "success", "buyer_id": response.buyer_id}
        else:
            return {"result": "error", "message": response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def login(data):
    username = data.get("username")
    password = data.get("password")

    try:
        request = customers_pb2.LoginRequest(username=username, password=password)
        response = _customers_stub.Login(request)

        if response.success:
            return {"result": "success", "session_id": response.session_id}
        else:
            return {"result": "error", "message": response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def logout(data):
    try:
        session_id = int(data.get("session_id"))
    except (TypeError, ValueError):
        return {"result": "error", "message": "Invalid session_id"}

    try:
        request = customers_pb2.LogoutRequest(session_id=session_id)
        response = _customers_stub.Logout(request)

        if response.success:
            return {"result": "success", "message": "Logout successful"}
        else:
            return {"result": "error", "message": response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def getItem(data):
    try:
        session_id = int(data.get("session_id"))
        item_id = int(data.get("item_id"))
    except (TypeError, ValueError):
        return {"result": "error", "message": "Invalid number format"}

    try:
        # Verify buyer session first
        buyer_request = customers_pb2.GetBuyerRequest(session_id=session_id)
        buyer_response = _customers_stub.GetBuyer(buyer_request)

        if not buyer_response.success:
            return {"result": "error", "message": buyer_response.message}

        # Get item from products service
        item_request = products_pb2.GetItemRequest(item_id=item_id)
        item_response = _products_stub.GetItem(item_request)

        if item_response.success:
            item = _item_to_dict(item_response.item)
            return {"result": "success", "item": item}
        else:
            return {"result": "error", "message": item_response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def getCategories(data):
    try:
        session_id = int(data.get("session_id"))
    except (TypeError, ValueError):
        return {"result": "error", "message": "Invalid session_id"}

    try:
        # Verify buyer session first
        buyer_request = customers_pb2.GetBuyerRequest(session_id=session_id)
        buyer_response = _customers_stub.GetBuyer(buyer_request)

        if not buyer_response.success:
            return {"result": "error", "message": buyer_response.message}

        # Get categories from products service
        get_categories_request = products_pb2.GetCategoriesClientRequest()
        categories_response = _products_stub.GetCategoriesClient(get_categories_request)

        if categories_response.success:
            if not categories_response.categories:
                return {"result": "success", "categories": []}

            categories_list = [
                {"id": cat.id, "name": cat.name}
                for cat in categories_response.categories
            ]
            return {"result": "success", "categories": categories_list}
        else:
            return {"result": "error", "message": categories_response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def searchItemsForSale(data):
    try:
        session_id = int(data.get("session_id"))
        category_id = int(data.get("category"))
    except (TypeError, ValueError):
        return {"result": "error", "message": "Invalid number format"}

    keywords = data.get("keywords", "")
    keywords_list = keywords.split(",") if keywords else []

    try:
        # Verify buyer session first
        buyer_request = customers_pb2.GetBuyerRequest(session_id=session_id)
        buyer_response = _customers_stub.GetBuyer(buyer_request)

        if not buyer_response.success:
            return {"result": "error", "message": buyer_response.message}

        # Search items from products service
        search_request = products_pb2.SearchItemsRequest(
            category_id=category_id, keywords=keywords_list
        )
        search_response = _products_stub.SearchItemsForSale(search_request)

        if search_response.success:
            if not search_response.items:
                return {"result": "success", "message": "No items found", "items": []}

            items_list = [_item_to_dict(item) for item in search_response.items]
            return {"result": "success", "items": items_list}
        else:
            return {"result": "error", "message": search_response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def saveCart(data):
    try:
        session_id = int(data.get("session_id"))
    except (TypeError, ValueError):
        return {"result": "error", "message": "Invalid session_id"}

    try:
        request = customers_pb2.SaveCartRequest(session_id=session_id)
        response = _customers_stub.SaveCart(request)

        if response.success:
            return {"result": "success", "message": "Cart saved successfully"}
        else:
            return {"result": "error", "message": response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def addItemToCart(data):
    try:
        session_id = int(data.get("session_id"))
        item_id = int(data.get("item_id"))
        quantity = int(data.get("quantity"))
    except (TypeError, ValueError):
        return {"result": "error", "message": "Invalid number format"}

    try:
        request = customers_pb2.AddItemToCartRequest(
            session_id=session_id, item_id=item_id, quantity=quantity
        )
        response = _customers_stub.AddItemToCart(request)

        if response.success:
            return {"result": "success", "message": "Item added to cart successfully"}
        else:
            return {"result": "error", "message": response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def removeItemFromCart(data):
    try:
        session_id = int(data.get("session_id"))
        item_id = int(data.get("item_id"))
    except (TypeError, ValueError):
        return {"result": "error", "message": "Invalid number format"}

    try:
        request = customers_pb2.RemoveItemFromCartRequest(
            session_id=session_id, item_id=item_id
        )
        response = _customers_stub.RemoveItemFromCart(request)

        if response.success:
            return {
                "result": "success",
                "message": "Item removed from cart successfully",
            }
        else:
            return {"result": "error", "message": response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def clearCart(data):
    try:
        session_id = int(data.get("session_id"))
    except (TypeError, ValueError):
        return {"result": "error", "message": "Invalid session_id"}

    try:
        request = customers_pb2.ClearCartRequest(session_id=session_id)
        response = _customers_stub.ClearCart(request)

        if response.success:
            return {"result": "success", "message": "Cart cleared successfully"}
        else:
            return {"result": "error", "message": response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def getCart(data):
    try:
        session_id = int(data.get("session_id"))
    except (TypeError, ValueError):
        return {"result": "error", "message": "Invalid session_id"}

    try:
        request = customers_pb2.GetCartRequest(session_id=session_id)
        response = _customers_stub.GetCart(request)

        if response.success:
            session_cart = []
            saved_cart = []

            if response.session_cart:
                session_cart = [
                    {"item_id": item.item_id, "quantity": item.quantity}
                    for item in response.session_cart
                ]

            if response.saved_cart:
                saved_cart = [
                    {"item_id": item.item_id, "quantity": item.quantity}
                    for item in response.saved_cart
                ]

            return {
                "result": "success",
                "session_cart": session_cart,
                "saved_cart": saved_cart,
            }
        else:
            return {"result": "error", "message": response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def provideFeedback(data):
    try:
        session_id = int(data.get("session_id"))
        item_id = int(data.get("item_id"))
        feedback = int(data.get("feedback"))
    except (TypeError, ValueError):
        return {"result": "error", "message": "Invalid number format"}

    try:
        # Verify buyer session first
        buyer_request = customers_pb2.GetBuyerRequest(session_id=session_id)
        buyer_response = _customers_stub.GetBuyer(buyer_request)

        if not buyer_response.success:
            return {"result": "error", "message": buyer_response.message}

        get_purchases_request = customers_pb2.GetBuyerPurchasesRequest(
            session_id=session_id
        )
        get_purchases_response = _customers_stub.GetBuyerPurchases(
            get_purchases_request
        )
        if not get_purchases_response.success:
            return {"result": "error", "message": get_purchases_response.message}

        ids = [item.item_id for item in get_purchases_response.purchases]
        if item_id not in ids:
            return {
                "result": "error",
                "message": "You never bought that item you cant rate it",
            }

        # Provide feedback via products service
        feedback_request = products_pb2.ProvideFeedbackRequest(
            item_id=item_id, feedback=feedback
        )
        feedback_response = _products_stub.ProvideFeedback(feedback_request)

        if feedback_response.success:
            return {"result": "success", "message": "Feedback recorded successfully"}
        else:
            return {"result": "error", "message": feedback_response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def getSellerRating(data):
    try:
        session_id = int(data.get("session_id"))
        seller_id = int(data.get("seller_id"))
    except (TypeError, ValueError):
        return {"result": "error", "message": "Invalid number format"}

    try:
        # Verify buyer session first
        buyer_request = customers_pb2.GetBuyerRequest(session_id=session_id)
        buyer_response = _customers_stub.GetBuyer(buyer_request)

        if not buyer_response.success:
            return {"result": "error", "message": buyer_response.message}

        # Get seller rating via products service
        rating_request = products_pb2.GetSellerRatingByIdRequest(seller_id=seller_id)
        rating_response = _products_stub.GetSellerRatingById(rating_request)

        if rating_response.success:
            return {"result": "success", "feedback": rating_response.feedback}
        else:
            return {"result": "error", "message": rating_response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def getBuyerPurchases(data):
    try:
        session_id = int(data.get("session_id"))
    except (TypeError, ValueError):
        return {"result": "error", "message": "Invalid session_id"}

    try:
        request = customers_pb2.GetBuyerPurchasesRequest(session_id=session_id)
        response = _customers_stub.GetBuyerPurchases(request)

        if response.success:
            if not response.purchases:
                return {
                    "result": "success",
                    "message": "No purchases found",
                    "purchases": [],
                }

            purchases_list = [
                {"item_id": item.item_id, "quantity": item.quantity}
                for item in response.purchases
            ]
            return {"result": "success", "purchases": purchases_list}
        else:
            return {"result": "error", "message": response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def makePurchase(data):
    try:
        session_id = int(data.get("session_id"))
        card_number = data.get("card_number")
        expiration_date = data.get("expiration_date")
        security_code = data.get("security_code")
    except (TypeError, ValueError):
        return {"result": "error", "message": "Invalid session_id"}

    try:
        # Get cart and buyer info
        cart_request = customers_pb2.GetCartRequest(session_id=session_id)
        cart_response = _customers_stub.GetCart(cart_request)

        buyer_request = customers_pb2.GetBuyerRequest(session_id=session_id)
        buyer_response = _customers_stub.GetBuyer(buyer_request)

        if not cart_response.success:
            return {"result": "error", "message": cart_response.message}

        if not buyer_response.success:
            return {"result": "error", "message": buyer_response.message}

        if not cart_response.saved_cart:
            return {
                "result": "error",
                "message": "Remote Cart is empty, nothing to purchase",
            }

        # Prepare items for reservation
        items_to_buy = [
            products_pb2.ItemQuantity(
                item_id=cart_item.item_id, quantity=cart_item.quantity
            )
            for cart_item in cart_response.saved_cart
        ]

        amount = 0
        # Get amounts and multiply with quantity
        for cart_item in cart_response.saved_cart:
            item_request = products_pb2.GetItemRequest(item_id=cart_item.item_id)
            item_response = _products_stub.GetItem(item_request)

            if item_response.success:
                amount += item_response.item.sale_price * cart_item.quantity
            else:
                return {
                    "result": "error",
                    "message": item_response.message,
                }

        # Call payment service
        name = buyer_response.name
        payment_result = call_payment_service(
            name=name,
            card_number=card_number,
            expiration_date=expiration_date,
            security_code=security_code,
            amount=amount,
        )
        if payment_result == "Yes":
            # Payment successful - deduct items permanently from the seller
            seller_purchase_request = products_pb2.MakePurchaseRequest(
                items=items_to_buy
            )
            seller_purchase_response = _products_stub.MakePurchase(
                seller_purchase_request
            )

            if not seller_purchase_response.success:
                # This shouldn't happen since we reserved, but handle it
                return {"result": "error", "message": seller_purchase_response.message}

            # Record purchase in customer database
            purchase_request = customers_pb2.MakePurchaseRequest(session_id=session_id)
            purchase_response = _customers_stub.MakePurchase(purchase_request)
            if not purchase_response.success:
                return {"result": "error", "message": purchase_response.message}

            clear_cart_request = customers_pb2.ClearCartRequest(session_id=session_id)
            clear_cart_response = _customers_stub.ClearCart(clear_cart_request)

            if not clear_cart_response.success:
                pass  # we kinda dont care because the user can see the cart and clear it if he doesn't

            return {"result": "success", "message": "Purchase completed successfully"}
        else:
            return {"result": "error", "message": "Payment declined"}

    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def call_payment_service(name, card_number, expiration_date, security_code, amount):
    # Create a SOAP client
    client = Client(PAYMENT_ADDRESS)

    # Call the pay service
    result = client.service.pay(
        name=name,
        card_number=card_number,
        expiration_date=expiration_date,
        security_code=security_code,
        amount=amount,
    )

    return result

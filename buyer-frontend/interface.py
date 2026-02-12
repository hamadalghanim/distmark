from typing import List
import socket
import grpc
from proto import customers_pb2
from proto import customers_pb2_grpc
from proto import products_pb2
from proto import products_pb2_grpc
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


def createAccount(cmd: List[str], conn: socket.socket) -> None:
    # Structure "command name", "name", "username", "password"
    name = cmd[1]
    username = cmd[2]
    password = cmd[3]

    try:
        request = customers_pb2.CreateAccountRequest(
            name=name, username=username, password=password
        )
        response = _customers_stub.CreateAccount(request)

        if response.success:
            conn.send(bytes(f"Buyer created with ID: {response.buyer_id}", "utf-8"))
        else:
            conn.send(bytes(response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))


def login(cmd: List[str], conn: socket.socket):
    # Structure "command name", "username", "password"
    username = cmd[1]
    password = cmd[2]

    try:
        request = customers_pb2.LoginRequest(username=username, password=password)
        response = _customers_stub.Login(request)

        if response.success:
            conn.send(
                bytes(f"Login successful. Session ID: {response.session_id}", "utf-8")
            )
        else:
            conn.send(bytes(response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))


def logout(cmd: List[str], conn: socket.socket):
    # Structure "command name", "session_id"
    session_id = int(cmd[1])

    try:
        request = customers_pb2.LogoutRequest(session_id=session_id)
        response = _customers_stub.Logout(request)

        if response.success:
            conn.send(bytes("Logout successful", "utf-8"))
        else:
            conn.send(bytes(response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))


def getItem(cmd: List[str], conn: socket.socket):
    # Structure "command name", "session_id", "item_id"
    session_id = int(cmd[1])
    item_id = int(cmd[2])

    try:
        # Verify buyer session first
        buyer_request = customers_pb2.GetBuyerRequest(session_id=session_id)
        buyer_response = _customers_stub.GetBuyer(buyer_request)

        if not buyer_response.success:
            conn.send(bytes(buyer_response.message, "utf-8"))
            return

        # Get item from products service
        item_request = products_pb2.GetItemRequest(item_id=item_id)
        item_response = _products_stub.GetItem(item_request)

        if item_response.success:
            item = item_response.item
            item_str = f"Item(id={item.id}, name='{item.name}', category_id={item.category_id}, keywords='{item.keywords}', condition='{item.condition}', sale_price={item.sale_price}, quantity={item.quantity}, seller_id={item.seller_id})"
            conn.send(bytes(item_str, "utf-8"))
        else:
            conn.send(bytes(item_response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))


def getCategories(cmd: List[str], conn: socket.socket):
    # Structure "command name", "session_id"
    session_id = int(cmd[1])

    try:
        # Verify buyer session first
        buyer_request = customers_pb2.GetBuyerRequest(session_id=session_id)
        buyer_response = _customers_stub.GetBuyer(buyer_request)

        if not buyer_response.success:
            conn.send(bytes(buyer_response.message, "utf-8"))
            return

        # Get categories from products service
        get_categories_request = products_pb2.GetCategoriesClientRequest()
        categories_response = _products_stub.GetCategoriesClient(get_categories_request)

        if categories_response.success:
            if not categories_response.categories:
                conn.send(bytes("No categories found", "utf-8"))
            else:
                categories_str = "\n".join(
                    [
                        f"Category(id={cat.id}, name='{cat.name}')"
                        for cat in categories_response.categories
                    ]
                )
                conn.send(bytes(categories_str, "utf-8"))
        else:
            conn.send(bytes(categories_response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))


def searchItemsForSale(cmd: List[str], conn: socket.socket):
    # Structure "command name", "session_id", "category_id", "keywords"
    session_id = int(cmd[1])
    category_id = int(cmd[2])
    keywords = cmd[3].split(",") if cmd[3] else []

    try:
        # Verify buyer session first
        buyer_request = customers_pb2.GetBuyerRequest(session_id=session_id)
        buyer_response = _customers_stub.GetBuyer(buyer_request)

        if not buyer_response.success:
            conn.send(bytes(buyer_response.message, "utf-8"))
            return

        # Search items from products service
        search_request = products_pb2.SearchItemsRequest(
            category_id=category_id, keywords=keywords
        )
        search_response = _products_stub.SearchItemsForSale(search_request)

        if search_response.success:
            if not search_response.items:
                conn.send(bytes("No items found", "utf-8"))
            else:
                items_str = "\n".join(
                    [
                        f"Item(id={item.id}, name='{item.name}', category_id={item.category_id}, keywords='{item.keywords}', condition='{item.condition}', sale_price={item.sale_price}, quantity={item.quantity}, seller_id={item.seller_id})"
                        for item in search_response.items
                    ]
                )
                conn.send(bytes(items_str, "utf-8"))
        else:
            conn.send(bytes(search_response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))


def saveCart(cmd: List[str], conn: socket.socket):
    # Structure "command name", "session_id"
    session_id = int(cmd[1])

    try:
        request = customers_pb2.SaveCartRequest(session_id=session_id)
        response = _customers_stub.SaveCart(request)

        if response.success:
            conn.send(bytes("Cart saved successfully", "utf-8"))
        else:
            conn.send(bytes(response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))


def addItemToCart(cmd: List[str], conn: socket.socket):
    # Structure "command name", "session_id", "item_id", "quantity"
    session_id = int(cmd[1])
    item_id = int(cmd[2])
    quantity = int(cmd[3])

    try:
        request = customers_pb2.AddItemToCartRequest(
            session_id=session_id, item_id=item_id, quantity=quantity
        )
        response = _customers_stub.AddItemToCart(request)

        if response.success:
            conn.send(bytes("Item added to cart successfully", "utf-8"))
        else:
            conn.send(bytes(response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))


def removeItemFromCart(cmd: List[str], conn: socket.socket):
    # Structure "command name", "session_id", "item_id"
    session_id = int(cmd[1])
    item_id = int(cmd[2])

    try:
        request = customers_pb2.RemoveItemFromCartRequest(
            session_id=session_id, item_id=item_id
        )
        response = _customers_stub.RemoveItemFromCart(request)

        if response.success:
            conn.send(bytes("Item removed from cart successfully", "utf-8"))
        else:
            conn.send(bytes(response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))


def clearCart(cmd: List[str], conn: socket.socket):
    # Structure "command name", "session_id"
    session_id = int(cmd[1])

    try:
        request = customers_pb2.ClearCartRequest(session_id=session_id)
        response = _customers_stub.ClearCart(request)

        if response.success:
            conn.send(bytes("Cart cleared successfully", "utf-8"))
        else:
            conn.send(bytes(response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))


def getCart(cmd: List[str], conn: socket.socket):
    # Structure "command name", "session_id"
    session_id = int(cmd[1])

    try:
        request = customers_pb2.GetCartRequest(session_id=session_id)
        response = _customers_stub.GetCart(request)

        if response.success:
            response_lines = []

            response_lines.append("Session Cart")
            if not response.session_cart:
                response_lines.append("Cart is empty")
            else:
                for item in response.session_cart:
                    response_lines.append(
                        f"Item ID: {item.item_id}, Quantity: {item.quantity}"
                    )

            if response.saved_cart:
                response_lines.append("Saved Cart")
                for item in response.saved_cart:
                    response_lines.append(
                        f"Item ID: {item.item_id}, Quantity: {item.quantity}"
                    )

            conn.send(bytes("\n".join(response_lines), "utf-8"))
        else:
            conn.send(bytes(response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))


def provideFeedback(cmd: List[str], conn: socket.socket):
    # Structure "command name", "session_id", "item_id", "feedback"
    session_id = int(cmd[1])
    item_id = int(cmd[2])
    feedback = int(cmd[3])

    try:
        # Verify buyer session first
        buyer_request = customers_pb2.GetBuyerRequest(session_id=session_id)
        buyer_response = _customers_stub.GetBuyer(buyer_request)

        if not buyer_response.success:
            conn.send(bytes(buyer_response.message, "utf-8"))
            return

        # Provide feedback via products service
        feedback_request = products_pb2.ProvideFeedbackRequest(
            item_id=item_id, feedback=feedback
        )
        feedback_response = _products_stub.ProvideFeedback(feedback_request)

        if feedback_response.success:
            conn.send(bytes("Feedback recorded successfully", "utf-8"))
        else:
            conn.send(bytes(feedback_response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))


def getSellerRating(cmd: List[str], conn: socket.socket):
    # Structure "command name", "session_id", "seller_id"
    session_id = int(cmd[1])
    seller_id = int(cmd[2])

    try:
        # Verify buyer session first
        buyer_request = customers_pb2.GetBuyerRequest(session_id=session_id)
        buyer_response = _customers_stub.GetBuyer(buyer_request)

        if not buyer_response.success:
            conn.send(bytes(buyer_response.message, "utf-8"))
            return

        # Get seller rating via products service
        rating_request = products_pb2.GetSellerRatingByIdRequest(seller_id=seller_id)
        rating_response = _products_stub.GetSellerRatingById(rating_request)

        if rating_response.success:
            conn.send(bytes(f"Seller Rating: {rating_response.feedback}", "utf-8"))
        else:
            conn.send(bytes(rating_response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))


def getBuyerPurchases(cmd: List[str], conn: socket.socket):
    # Structure "command name", "session_id"
    session_id = int(cmd[1])

    try:
        request = customers_pb2.GetBuyerPurchasesRequest(session_id=session_id)
        response = _customers_stub.GetBuyerPurchases(request)

        if response.success:
            if not response.purchases:
                conn.send(bytes("No purchases found", "utf-8"))
            else:
                response_lines = [
                    f"Item ID: {item.item_id}, Quantity: {item.quantity}"
                    for item in response.purchases
                ]
                conn.send(bytes("\n".join(response_lines), "utf-8"))
        else:
            conn.send(bytes(response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))


def makePurchase(cmd: List[str], conn: socket.socket):
    # Structure "command name", "session_id"
    session_id = int(cmd[1])

    try:
        # For now, just check if cart has items
        cart_request = customers_pb2.GetCartRequest(session_id=session_id)
        cart_response = _customers_stub.GetCart(cart_request)

        if not cart_response.success:
            conn.send(bytes(cart_response.message, "utf-8"))
            return

        if not cart_response.session_cart:
            conn.send(bytes("Remote Cart is empty, nothing to purchase", "utf-8"))
            return

        conn.send(bytes("Not Implemented Yet\n", "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))

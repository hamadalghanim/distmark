import os
import grpc
from typing import List
import socket

# Import the generated protobuf classes
from proto import products_pb2
from proto import products_pb2_grpc

GRPC_HOST = os.getenv("PRODUCTS_DB_RPC_HOST", "products-db-rpc")
GRPC_PORT = os.getenv("PRODUCTS_DB_RPC_PORT", "5000")
GRPC_ADDRESS = f"{GRPC_HOST}:{GRPC_PORT}"

_channel = grpc.insecure_channel(GRPC_ADDRESS)
_stub = products_pb2_grpc.SellerServiceStub(_channel)


def createAccount(cmd: List[str], conn: socket.socket) -> None:
    # Structure "command name", "name", "username", "password"
    name = cmd[1]
    username = cmd[2]
    password = cmd[3]

    try:
        request = products_pb2.CreateAccountRequest(
            name=name, username=username, password=password
        )
        response = _stub.CreateAccount(request)
        if response.success:
            conn.send(bytes(f"Seller created with ID: {response.seller_id}", "utf-8"))
        else:
            conn.send(bytes(response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))


def login(cmd: List[str], conn: socket.socket):
    # Structure "command name", "username", "password"
    username = cmd[1]
    password = cmd[2]

    try:
        request = products_pb2.LoginRequest(username=username, password=password)
        response = _stub.Login(request)
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
        request = products_pb2.LogoutRequest(session_id=session_id)
        response = _stub.Logout(request)
        if response.success:
            conn.send(bytes("Logout successful", "utf-8"))
        else:
            conn.send(bytes(response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))


def getSellerRating(cmd: List[str], conn: socket.socket):
    # Structure "command name", "session_id"
    session_id = int(cmd[1])

    try:
        request = products_pb2.GetSellerRatingRequest(session_id=session_id)
        response = _stub.GetSellerRating(request)

        if response.success:
            conn.send(bytes(f"Your current feedback = {response.feedback}", "utf-8"))
        else:
            conn.send(bytes(response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))


def registerItemForSale(cmd: List[str], conn: socket.socket):
    # Structure "command name", "session_id","item name","category_id", "Keywords", "condition", "price", "qty"
    session_id = int(cmd[1])

    try:
        request = products_pb2.RegisterItemRequest(
            session_id=session_id,
            item_name=cmd[2],
            category_id=int(cmd[3]),
            keywords=cmd[4],
            condition=cmd[5].upper().strip(),
            price=float(cmd[6]),
            quantity=int(cmd[7]),
        )
        response = _stub.RegisterItemForSale(request)
        if response.success:
            conn.send(bytes(f"Item registered with ID: {response.item_id}", "utf-8"))
        else:
            conn.send(bytes(response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))
    except Exception as e:
        conn.send(bytes(f"Error: {e}", "utf-8"))


def changeItemPrice(cmd: List[str], conn: socket.socket):
    # Structure "command name", "session_id","item_id" "new_price"
    session_id = int(cmd[1])
    item_id = int(cmd[2])
    new_price = float(cmd[3])

    try:
        request = products_pb2.ChangeItemPriceRequest(
            session_id=session_id, item_id=item_id, new_price=new_price
        )
        response = _stub.ChangeItemPrice(request)
        if response.success:
            conn.send(
                bytes(f"Item price updated to: {response.current_price}", "utf-8")
            )
        else:
            conn.send(bytes(response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))


def updateUnitsForSale(cmd: List[str], conn: socket.socket):
    # Structure "command name", "session_id","item_id" "new_qty"
    session_id = int(cmd[1])
    item_id = int(cmd[2])
    new_qty = int(cmd[3])

    try:
        request = products_pb2.UpdateUnitsRequest(
            session_id=session_id, item_id=item_id, new_quantity=new_qty
        )
        response = _stub.UpdateUnitsForSale(request)
        if response.success:
            conn.send(
                bytes(f"Item quantity updated to: {response.current_quantity}", "utf-8")
            )
        else:
            conn.send(bytes(response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))


def displayItemsForSale(cmd: List[str], conn: socket.socket):
    # Structure "command name", "session_id"
    session_id = int(cmd[1])

    try:
        request = products_pb2.DisplayItemsRequest(session_id=session_id)
        response = _stub.DisplayItemsForSale(request)

        if response.success:
            if response.items:
                items_str = "\n".join(
                    [
                        f"Item(id={item.id}, name='{item.name}', category_id={item.category_id}, "
                        f"keywords='{item.keywords}', condition='{item.condition}', "
                        f"sale_price={item.sale_price}, quantity={item.quantity}, seller_id={item.seller_id})"
                        for item in response.items
                    ]
                )
                conn.send(bytes(items_str, "utf-8"))
            else:
                conn.send(bytes("No items found", "utf-8"))
        else:
            conn.send(bytes(response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))


def getCategories(cmd: List[str], conn: socket.socket):
    session_id = int(cmd[1])

    try:
        request = products_pb2.GetCategoriesRequest(session_id=session_id)
        response = _stub.GetCategories(request)

        if response.success:
            if not response.categories or len(response.categories) == 0:
                categories_str = "no categories"
            else:
                categories_str = "\n".join(
                    [
                        f"Category(id={cat.id}, name='{cat.name}')"
                        for cat in response.categories
                    ]
                )
            conn.send(bytes(categories_str, "utf-8"))
        else:
            conn.send(bytes(response.message, "utf-8"))
    except grpc.RpcError as e:
        conn.send(bytes(f"RPC error: {e.details()}", "utf-8"))

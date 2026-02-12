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
        request = products_pb2.CreateAccountRequest(
            name=name, username=username, password=password
        )
        response = _stub.CreateAccount(request)

        if response.success:
            return {"result": "success", "seller_id": response.seller_id}
        else:
            return {"result": "error", "message": response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def login(data):
    username = data.get("username")
    password = data.get("password")

    try:
        request = products_pb2.LoginRequest(username=username, password=password)
        response = _stub.Login(request)

        if response.success:
            return {"result": "success", "session_id": response.session_id}
        else:
            return {"result": "error", "message": response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def logout(data):
    # Parse session_id safely
    try:
        session_id = int(data.get("session_id"))
    except (TypeError, ValueError):
        return {"result": "error", "message": "Invalid session_id"}

    try:
        request = products_pb2.LogoutRequest(session_id=session_id)
        response = _stub.Logout(request)

        if response.success:
            return {"result": "success", "message": "Logout successful"}
        else:
            return {"result": "error", "message": response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def getSellerRating(data):
    try:
        session_id = int(data.get("session_id"))
    except (TypeError, ValueError):
        return {"result": "error", "message": "Invalid session_id"}

    try:
        request = products_pb2.GetSellerRatingRequest(session_id=session_id)
        response = _stub.GetSellerRating(request)

        if response.success:
            return {"result": "success", "feedback": response.feedback}
        else:
            return {"result": "error", "message": response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def registerItemForSale(data):
    try:
        session_id = int(data.get("session_id"))
        category_id = int(data.get("category"))
        price = float(data.get("price"))
        quantity = int(data.get("qty"))
    except (TypeError, ValueError):
        return {
            "result": "error",
            "message": "Invalid number format for ID, Price, or Qty",
        }

    try:
        request = products_pb2.RegisterItemRequest(
            session_id=session_id,
            item_name=data.get("name"),
            category_id=category_id,
            keywords=data.get("keywords", ""),  # Optional, default to empty
            condition=data.get("condition", "New").upper().strip(),  # Default to New
            price=price,
            quantity=quantity,
        )
        response = _stub.RegisterItemForSale(request)

        if response.success:
            return {"result": "success", "item_id": response.item_id}
        else:
            return {"result": "error", "message": response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}
    except Exception as e:
        return {"result": "error", "message": f"Error: {str(e)}"}


def changeItemPrice(data):
    try:
        session_id = int(data.get("session_id"))
        item_id = int(data.get("item_id"))
        new_price = float(data.get("new_price"))
    except (TypeError, ValueError):
        return {"result": "error", "message": "Invalid number format"}

    try:
        request = products_pb2.ChangeItemPriceRequest(
            session_id=session_id, item_id=item_id, new_price=new_price
        )
        response = _stub.ChangeItemPrice(request)

        if response.success:
            return {"result": "success", "current_price": response.current_price}
        else:
            return {"result": "error", "message": response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def updateUnitsForSale(data):
    try:
        session_id = int(data.get("session_id"))
        item_id = int(data.get("item_id"))
        new_qty = int(data.get("new_qty"))
    except (TypeError, ValueError):
        return {"result": "error", "message": "Invalid number format"}

    try:
        request = products_pb2.UpdateUnitsRequest(
            session_id=session_id, item_id=item_id, new_quantity=new_qty
        )
        response = _stub.UpdateUnitsForSale(request)

        if response.success:
            return {"result": "success", "current_quantity": response.current_quantity}
        else:
            return {"result": "error", "message": response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def displayItemsForSale(data):
    try:
        session_id = int(data.get("session_id"))
    except (TypeError, ValueError):
        return {"result": "error", "message": "Invalid session_id"}

    try:
        request = products_pb2.DisplayItemsRequest(session_id=session_id)
        response = _stub.DisplayItemsForSale(request)

        if response.success:
            if not response.items:
                return {"result": "success", "message": "No items found", "items": []}

            # Convert protobuf items to list of dicts
            items_list = [_item_to_dict(item) for item in response.items]
            return {"result": "success", "items": items_list}
        else:
            return {"result": "error", "message": response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}


def getCategories(data):
    try:
        session_id = int(data.get("session_id"))
    except (TypeError, ValueError):
        return {"result": "error", "message": "Invalid session_id"}

    try:
        request = products_pb2.GetCategoriesRequest(session_id=session_id)
        response = _stub.GetCategories(request)

        if response.success:
            if not response.categories:
                return {"result": "success", "categories": []}

            categories_list = [
                {"id": cat.id, "name": cat.name} for cat in response.categories
            ]
            return {"result": "success", "categories": categories_list}
        else:
            return {"result": "error", "message": response.message}
    except grpc.RpcError as e:
        return {"result": "error", "message": f"RPC error: {e.details()}"}

#!/usr/bin/python
from flask import Flask, request
import interface

app = Flask(__name__)


@app.route("/account/register", methods=["POST"])
def create_account():
    data = request.json
    return interface.createAccount(data)


@app.route("/account/login", methods=["POST"])
def login():
    data = request.json
    return interface.login(data)


@app.route("/account/logout", methods=["POST"])
def logout():
    data = request.json
    return interface.logout(data)


@app.route("/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    # Convert query parameters (e.g., ?session_id=x) to a dictionary
    data = request.args.to_dict()
    data["item_id"] = item_id
    return interface.getItem(data)


@app.route("/categories", methods=["GET"])
def get_categories():
    data = request.args.to_dict()
    return interface.getCategories(data)


@app.route("/items/search", methods=["GET"])
def search_items():
    data = request.args.to_dict()
    return interface.searchItemsForSale(data)


@app.route("/cart/save", methods=["POST"])
def save_cart():
    data = request.json
    return interface.saveCart(data)


@app.route("/cart", methods=["GET"])
def get_cart():
    data = request.args.to_dict()
    return interface.getCart(data)


@app.route("/cart/items", methods=["POST"])
def add_item_to_cart():
    data = request.json
    return interface.addItemToCart(data)


@app.route("/cart/items/<int:item_id>", methods=["DELETE"])
def remove_item_from_cart(item_id):
    data = request.json or {}
    data["item_id"] = item_id
    return interface.removeItemFromCart(data)


@app.route("/cart/clear", methods=["POST"])
def clear_cart():
    data = request.json
    return interface.clearCart(data)


@app.route("/feedback", methods=["POST"])
def provide_feedback():
    data = request.json
    return interface.provideFeedback(data)


@app.route("/seller/<int:seller_id>/rating", methods=["GET"])
def get_seller_rating(seller_id):
    data = request.args.to_dict()
    data["seller_id"] = seller_id
    return interface.getSellerRating(data)


@app.route("/purchases", methods=["GET"])
def get_buyer_purchases():
    data = request.args.to_dict()
    return interface.getBuyerPurchases(data)


@app.route("/purchase", methods=["POST"])
def make_purchase():
    data = request.json
    return interface.makePurchase(data)


if __name__ == "__main__":
    print("Customer Frontend REST API listening on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=True)

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


@app.route("/seller/rating", methods=["GET"])
def get_seller_rating():
    # Convert query parameters (e.g., ?session_id=x) to a dictionary
    data = request.args.to_dict()
    return interface.getSellerRating(data)


@app.route("/items", methods=["POST"])
def register_item():
    data = request.json
    return interface.registerItemForSale(data)


@app.route("/items/price", methods=["PUT"])
def change_item_price():
    data = request.json
    return interface.changeItemPrice(data)


@app.route("/items/quantity", methods=["PUT"])
def update_units():
    data = request.json
    return interface.updateUnitsForSale(data)


@app.route("/items", methods=["GET"])
def display_items():
    data = request.args.to_dict()
    return interface.displayItemsForSale(data)


@app.route("/categories", methods=["GET"])
def get_categories():
    data = request.args.to_dict()
    return interface.getCategories(data)


if __name__ == "__main__":
    print("Seller Frontend REST API listening on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=True)

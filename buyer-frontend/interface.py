import datetime
from config import customers_engine, products_engine
from db import Buyer, Category, Item, ItemsBought, Seller
from db import BuyerSession, Cart, CartItem
from typing import List
import socket
from sqlalchemy.orm import Session


def createAccount(
    cmd: List[str],
    conn: socket.socket,
) -> None:
    # Structure "command name", "name", "username", "password" MAYBE put this in class

    with Session(customers_engine) as customers_session:
        name = cmd[1]
        username = cmd[2]
        password = cmd[3]
        try:
            obj = Buyer(name=name, username=username, password=password)
            customers_session.add(obj)
            customers_session.commit()
        except Exception as e:
            customers_session.rollback()
            conn.send(bytes(f"Database error: {e}", "utf-8"))
            return

        conn.send(bytes(f"Buyer created with ID: {obj.id}", "utf-8"))


def login(
    cmd: List[str],
    conn: socket.socket,
):
    # Structure "command name", "username", "password" MAYBE put this in class
    with Session(customers_engine) as customers_session:
        username = cmd[1]
        password = cmd[2]
        try:
            buyer = customers_session.query(Buyer).filter_by(username=username).first()
        except Exception as e:
            conn.send(bytes(f"Database error: {e}", "utf-8"))
            return

        if buyer is None:
            conn.send(bytes("Buyer not found", "utf-8"))
            return

        if buyer.password != password:
            conn.send(bytes("Invalid username or password", "utf-8"))
            return
        try:
            sess = BuyerSession(
                buyer_id=buyer.id,
                last_activity=datetime.datetime.now(datetime.timezone.utc),
            )
            customers_session.add(sess)
            customers_session.commit()
        except Exception as e:
            customers_session.rollback()
            conn.send(bytes(f"Database error: {e}", "utf-8"))
            return

        conn.send(bytes(f"Login successful. Session ID: {sess.id}", "utf-8"))


def logout(
    cmd: List[str],
    conn: socket.socket,
):
    with Session(customers_engine) as customers_session:
        # Structure "command name", "session_id" MAYBE put this in class
        session_id = cmd[1]
        session = get_and_validate_session(session_id, conn, customers_session)
        if session is None:
            return
        try:
            customers_session.delete(session)
            customers_session.commit()
        except Exception as e:
            customers_session.rollback()
            conn.send(bytes(f"Database error: {e}", "utf-8"))
            return

        conn.send(bytes("Logout successful", "utf-8"))


def getItem(
    cmd: List[str],
    conn: socket.socket,
):
    with Session(customers_engine) as customers_session:
        with Session(products_engine) as products_session:
            # Structure "command name", "session_id", "item_id"
            session_id = cmd[1]
            session = get_and_validate_session(session_id, conn, customers_session)
            item_id = cmd[2]
            if session is None:
                return
            try:
                items = products_session.query(Item).filter_by(id=item_id).all()
            except Exception as e:
                conn.send(bytes(f"Database error: {e}", "utf-8"))
                return
            if not items:
                conn.send(bytes("No items found", "utf-8"))
                return
            conn.send(bytes("\n".join([item.__repr__() for item in items]), "utf-8"))


def getCategories(
    cmd: List[str],
    conn: socket.socket,
):
    with Session(customers_engine) as customers_session:
        with Session(products_engine) as products_session:
            session_id = cmd[1]
            session = get_and_validate_session(session_id, conn, customers_session)
            if session is None:
                return
            categories = products_session.query(Category).all()
            conn.send(
                bytes("\n".join([item.__repr__() for item in categories]), "utf-8")
            )


def get_and_validate_session(
    session_id: str, conn: socket.socket, customers_session: Session
):
    try:
        session = (
            customers_session.query(BuyerSession).filter_by(id=int(session_id)).first()
        )
    except Exception as e:
        conn.send(bytes(f"Database error: {e}", "utf-8"))
        return

    if session is None:
        conn.send(bytes("Session not found", "utf-8"))
        return

    if is_older_than_5_minutes(session.last_activity):
        conn.send(bytes("Session no longer valid", "utf-8"))
        return
    # update last activity
    try:
        session.last_activity = datetime.datetime.now(datetime.timezone.utc)
        customers_session.add(session)
        customers_session.commit()
    except Exception as e:
        customers_session.rollback()
        conn.send(bytes(f"Database error: {e}", "utf-8"))
        return

    return session


def searchItemsForSale(
    cmd: List[str],
    conn: socket.socket,
):
    with Session(customers_engine) as customers_session:
        with Session(products_engine) as products_session:
            # Structure "command name", "session_id", "category_id", "keywords"
            session_id = cmd[1]
            session = get_and_validate_session(session_id, conn, customers_session)
            category_id = cmd[2]
            keywords = cmd[3].split(",")  # assuming keywords are comma-separated
            if session is None:
                return
            try:
                query = products_session.query(Item)
                if category_id != "0":  # assuming 0 means all categories
                    query = query.filter_by(category_id=int(category_id))
                if keywords:
                    for keyword in keywords:
                        query = query.filter(
                            Item.keywords.ilike(f"%{keyword.strip()}%")
                        )
                items = query.all()
            except Exception as e:
                conn.send(bytes(f"Database error: {e}", "utf-8"))
                return
            if not items:
                conn.send(bytes("No items found", "utf-8"))
                return
            conn.send(bytes("\n".join([item.__repr__() for item in items]), "utf-8"))


def saveCart(
    cmd: List[str],
    conn: socket.socket,
):
    with Session(customers_engine) as customers_session:
        with Session(products_engine) as products_session:
            # Structure "command name", "session_id", "item_id:quantity,item_id:quantity,..."
            session_id = cmd[1]
            session = get_and_validate_session(session_id, conn, customers_session)
            items_str = cmd[2]
            if session is None:
                return

            # Add new items to cart
            response_lines = []
            try:
                cart = get_or_create_cart(session.buyer_id, customers_session)
                # Clear existing cart items
                customers_session.query(CartItem).filter_by(cart_id=cart.id).delete()
                items = items_str.split(",")
                for item_entry in items:
                    item_id, quantity = map(int, item_entry.split(":"))
                    # validate item exists in products database with the correct id and quantity
                    product_item = (
                        products_session.query(Item).filter_by(id=item_id).first()
                    )
                    if product_item is None:
                        response_lines.append(
                            f"Item ID {item_id} not found in products database (skipped)"
                        )
                        continue
                    if product_item.quantity < quantity:
                        response_lines.append(
                            f"Not enough quantity for Item ID {item_id} available {product_item.quantity} asked for {quantity} (skipped)"
                        )
                        continue
                    cart_item = CartItem(
                        cart_id=cart.id, item_id=item_id, quantity=quantity
                    )
                    customers_session.add(cart_item)
                customers_session.commit()
            except Exception as e:
                customers_session.rollback()
                conn.send(bytes(f"Database error: {e}", "utf-8"))
                return
            if response_lines:
                response_lines.insert(0, "Some items were not added to the cart:")
            response_lines.append("Cart saved successfully")
            conn.send(bytes("\n".join(response_lines), "utf-8"))


def getCart(
    cmd: List[str],
    conn: socket.socket,
):
    with Session(customers_engine) as customers_session:
        # Structure "command name", "session_id"
        session_id = cmd[1]
        session = get_and_validate_session(session_id, conn, customers_session)
        if session is None:
            return

        try:
            cart = get_or_create_cart(session.buyer_id, customers_session)
            cart_items = (
                customers_session.query(CartItem).filter_by(cart_id=cart.id).all()
            )
        except Exception as e:
            customers_session.rollback()
            conn.send(bytes(f"Database error: {e}", "utf-8"))
            return

        if not cart_items:
            conn.send(bytes("Remote Cart is empty", "utf-8"))
            return

        response_lines = [
            f"Item ID: {item.item_id}, Quantity: {item.quantity}" for item in cart_items
        ]
        conn.send(bytes("\n".join(response_lines), "utf-8"))


def is_older_than_5_minutes(event_time):
    # Get the current time, ensuring it is timezone-aware (UTC is a good default)
    current_time = datetime.datetime.now(datetime.timezone.utc)

    # If event_time is naive (no tzinfo), assume UTC to make it timezone-aware
    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=datetime.timezone.utc)

    # Define the 5-minute threshold
    time_threshold = datetime.timedelta(minutes=5)

    # Calculate the difference
    time_difference = current_time - event_time

    # Check if the difference is greater than the threshold
    return time_difference > time_threshold


def get_or_create_cart(buyer_id: int, customers_session: Session) -> Cart:
    cart = customers_session.query(Cart).filter_by(buyer_id=buyer_id).first()
    if cart is None:
        cart = Cart(buyer_id=buyer_id)
        customers_session.add(cart)
        customers_session.commit()
    return cart


def provideFeedback(
    cmd: List[str],
    conn: socket.socket,
):
    with Session(customers_engine) as customers_session:
        with Session(products_engine) as products_session:
            # Structure "command name", "session_id", "item_id", "feedback" (thumbs up or down)
            session_id = cmd[1]
            session = get_and_validate_session(session_id, conn, customers_session)
            if session is None:
                return
            # TODO: for later assignments check item if purchased by buyer through ItemsBought table
            item = products_session.query(Item).filter_by(id=int(cmd[2])).first()
            if item is None:
                conn.send(bytes("Item not found", "utf-8"))
                return
            feedback = int(cmd[3])  # +1 for thumbs up, -1 for thumbs down
            item.feedback += feedback
            item.seller.feedback += feedback
            try:
                products_session.add(item)
                products_session.commit()
            except Exception as e:
                products_session.rollback()
                conn.send(bytes(f"Database error: {e}", "utf-8"))
                return
            conn.send(bytes("Feedback recorded successfully", "utf-8"))


def getSellerRating(
    cmd: List[str],
    conn: socket.socket,
):
    with Session(customers_engine) as customers_session:
        with Session(products_engine) as products_session:
            # Structure "command name", "session_id", "seller_id"
            session_id = cmd[1]
            session = get_and_validate_session(session_id, conn, customers_session)
            if session is None:
                return

            try:
                seller = (
                    products_session.query(Seller).filter_by(id=int(cmd[2])).first()
                )
            except Exception as e:
                conn.send(bytes(f"Database error: {e}", "utf-8"))
                return

            if seller is None:
                conn.send(bytes("Seller not found", "utf-8"))
                return
            conn.send(bytes(f"Seller Rating: {seller.feedback}", "utf-8"))


def getBuyerPurchases(
    cmd: List[str],
    conn: socket.socket,
):
    with Session(customers_engine) as customers_session:
        # Structure "command name", "session_id"
        session_id = cmd[1]
        session = get_and_validate_session(session_id, conn, customers_session)
        if session is None:
            return

        try:
            items_bought = (
                customers_session.query(ItemsBought)
                .filter_by(buyer_id=session.buyer_id)
                .all()
            )
        except Exception as e:
            conn.send(bytes(f"Database error: {e}", "utf-8"))
            return

        if not items_bought:
            conn.send(bytes("No purchases found", "utf-8"))
            return

        response_lines = [
            f"Item ID: {item.item_id}, Quantity: {item.quantity}"
            for item in items_bought
        ]
        conn.send(bytes("\n".join(response_lines), "utf-8"))


def makePurchase(
    cmd: List[str],
    conn: socket.socket,
):
    with Session(customers_engine) as customers_session:
        # Structure "command name", "session_id"
        session_id = cmd[1]
        session = get_and_validate_session(session_id, conn, customers_session)
        if session is None:
            return
        try:
            cart = get_or_create_cart(session.buyer_id, customers_session)
            cart_items = (
                customers_session.query(CartItem).filter_by(cart_id=cart.id).all()
            )
        except Exception as e:
            customers_session.rollback()
            conn.send(bytes(f"Database error: {e}", "utf-8"))
            return

        if not cart_items:
            conn.send(bytes("Remote Cart is empty, nothing to purchase", "utf-8"))
            return
        conn.send(bytes("Not Implemented Yet\n", "utf-8"))

import datetime
from db import Buyer, Category, Item
from db import BuyerSession
from typing import List
import socket
from sqlalchemy.orm import Session


def createAccount(
    cmd: List[str],
    conn: socket.socket,
    products_session: Session,
    customers_session: Session,
) -> None:
    # Structure "command name", "name", "username", "password" MAYBE put this in class
    name = cmd[1]
    username = cmd[2]
    password = cmd[3]
    try:
        obj = Buyer(name=name, username=username, password=password)
        customers_session.add(obj)
        customers_session.commit()
    except Exception as e:
        conn.send(bytes(f"Database error: {e}", "utf-8"))
        return

    conn.send(bytes(f"Buyer created with ID: {obj.id}", "utf-8"))


def login(
    cmd: List[str],
    conn: socket.socket,
    products_session: Session,
    customers_session: Session,
):
    # Structure "command name", "username", "password" MAYBE put this in class
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
        conn.send(bytes(f"Database error: {e}", "utf-8"))
        return

    conn.send(bytes(f"Login successful. Session ID: {sess.id}", "utf-8"))

    pass


def logout(
    cmd: List[str],
    conn: socket.socket,
    products_session: Session,
    customers_session: Session,
):
    # Structure "command name", "session_id" MAYBE put this in class
    session_id = cmd[1]
    session = get_and_validate_session(session_id, conn, customers_session)
    if session is None:
        return
    try:
        customers_session.delete(session)
        customers_session.commit()
    except Exception as e:
        conn.send(bytes(f"Database error: {e}", "utf-8"))
        return

    conn.send(bytes("Logout successful", "utf-8"))


def getItem(
    cmd: List[str],
    conn: socket.socket,
    products_session: Session,
    customers_session: Session,
):
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
    products_session: Session,
    customers_session: Session,
):
    session_id = cmd[1]
    session = get_and_validate_session(session_id, conn, customers_session)
    if session is None:
        return
    categories = products_session.query(Category).all()
    conn.send(bytes("\n".join([item.__repr__() for item in categories]), "utf-8"))


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
        print("updated last activity for session")
    except Exception as e:
        conn.send(bytes(f"Database error: {e}", "utf-8"))
        return

    return session


def searchItemsForSale(
    cmd: List[str],
    conn: socket.socket,
    products_session: Session,
    customers_session: Session,
):
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
                query = query.filter(Item.keywords.ilike(f"%{keyword.strip()}%"))
        items = query.all()
    except Exception as e:
        conn.send(bytes(f"Database error: {e}", "utf-8"))
        return
    if not items:
        conn.send(bytes("No items found", "utf-8"))
        return
    conn.send(bytes("\n".join([item.__repr__() for item in items]), "utf-8"))


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

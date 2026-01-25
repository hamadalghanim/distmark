import datetime
from db import Seller
from db import Session as TblSession
from typing import List
import socket
from sqlalchemy.orm import Session


def createAccount(
    cmd: List[str], conn: socket.socket, products_session: Session
) -> None:
    # Structure "command name", "name", "username", "password" MAYBE put this in class
    name = cmd[1]
    username = cmd[2]
    password = cmd[3]
    try:
        obj = Seller(name=name, username=username, password=password)
        products_session.add(obj)
        products_session.commit()
    except Exception as e:
        conn.send(bytes(f"Database error: {e}", "utf-8"))
        return

    conn.send(bytes(f"Seller created with ID: {obj.id}", "utf-8"))


def login(cmd: List[str], conn: socket.socket, products_session: Session):
    # Structure "command name", "username", "password" MAYBE put this in class
    username = cmd[1]
    password = cmd[2]
    try:
        seller = products_session.query(Seller).filter_by(username=username).first()
    except Exception as e:
        conn.send(bytes(f"Database error: {e}", "utf-8"))
        return

    if seller is None:
        conn.send(bytes("Seller not found", "utf-8"))
        return

    if seller.password != password:
        conn.send(bytes("Invalid username or password", "utf-8"))
        return
    try:
        sess = TblSession(seller_id=seller.id)
        products_session.add(sess)
        products_session.commit()
    except Exception as e:
        conn.send(bytes(f"Database error: {e}", "utf-8"))
        return

    conn.send(bytes(f"Login successful. Session ID: {sess.id}", "utf-8"))

    pass


def logout(cmd: List[str], conn: socket.socket, products_session: Session):
    # Structure "command name", "session_id" MAYBE put this in class
    session_id = cmd[1]
    session = get_and_validate_session(session_id, conn, products_session)
    if session is None:
        return
    try:
        products_session.delete(session)
        products_session.commit()
    except Exception as e:
        conn.send(bytes(f"Database error: {e}", "utf-8"))
        return

    conn.send(bytes("Logout successful", "utf-8"))


def getSellerRating(cmd: List[str], conn: socket.socket, products_session: Session):
    # Structure "command name", "session_id" MAYBE put this in class
    session_id = cmd[1]
    session = get_and_validate_session(session_id, conn, products_session)
    if session is None:
        return
    conn.send(bytes(f"Your current feedback = {session.seller.feedback}", "utf-8"))


def registerItemForSale(cmd: List[str], conn: socket.socket, products_session: Session):
    pass


def changeItemPrice(cmd: List[str], conn: socket.socket, products_session: Session):
    pass


def updateUnitsForSale(cmd: List[str], conn: socket.socket, products_session: Session):
    pass


def displayItemsForSale(cmd: List[str], conn: socket.socket, products_session: Session):
    pass


def get_and_validate_session(
    session_id: str, conn: socket.socket, products_session: Session
):
    try:
        session = (
            products_session.query(TblSession).filter_by(id=int(session_id)).first()
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
        products_session.add(session)
        products_session.commit()
        print("updated last activity for session")
    except Exception as e:
        conn.send(bytes(f"Database error: {e}", "utf-8"))
        return

    return session


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

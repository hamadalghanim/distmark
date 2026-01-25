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
    pass


def getSellerRating(cmd: List[str], conn: socket.socket, products_session: Session):
    pass


def registerItemForSale(cmd: List[str], conn: socket.socket, products_session: Session):
    pass


def changeItemPrice(cmd: List[str], conn: socket.socket, products_session: Session):
    pass


def updateUnitsForSale(cmd: List[str], conn: socket.socket, products_session: Session):
    pass


def displayItemsForSale(cmd: List[str], conn: socket.socket, products_session: Session):
    pass

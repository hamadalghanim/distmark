from db import Seller
from typing import List
import socket
from sqlalchemy.orm import Session


def createAccount(
    cmd: List[str], conn: socket.socket, products_session: Session
) -> None:
    # Structure "command name" "name", "username", "password" MAYBE put this in class
    name = cmd[1]
    username = cmd[2]
    password = cmd[3]
    obj = Seller(name=name, username=username, password=password)
    products_session.add(obj)
    products_session.commit()
    conn.send(bytes(f"Seller created with ID: {obj.id}", "utf-8"))


def login(cmd: List[str], conn: socket.socket, products_session: Session):
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

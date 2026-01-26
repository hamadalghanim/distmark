#!/usr/bin/python
import socket
from config import products_engine
from sqlalchemy.orm import Session
import interface

PORT = 5000
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(("0.0.0.0", PORT))
sock.listen(1)
products_session = Session(products_engine)


def process_command(cmd, conn):
    lines = cmd.strip().split("\n")
    commands = [line.strip() for line in lines if line.strip()]

    if not commands:
        conn.send(bytes("ERROR: Empty command", "utf-8"))
        return

    mappings = {
        "createaccount": interface.createAccount,
        "login": interface.login,
        "logout": interface.logout,
        "getsellerrating": interface.getSellerRating,
        "registeritemforsale": interface.registerItemForSale,
        "changeitemprice": interface.changeItemPrice,
        "updateunitsforsale": interface.updateUnitsForSale,
        "displayitemsforsale": interface.displayItemsForSale,
        "getcategories": interface.getCategories
    }
    command_name = commands[0].lower()

    if command_name not in mappings:
        conn.send(bytes(f"ERROR: Unknown command '{command_name}'", "utf-8"))
        return
    mappings[command_name](commands, conn, products_session)


print(f"Seller Frontend Server listening on port {PORT}...")
while True:
    conn, addr = sock.accept()
    print(f"Connection from {addr} has been established!")

    while True:  # Keep reading commands
        info = conn.recv(65536)
        if not info:  # Connection closed by client
            break

        cmd = info.decode("utf-8").strip()
        print(f"Received data: {cmd}")

        if cmd == "quit":
            break
        elif cmd.lower() == "help":
            help_text = (
                "Available commands:\n"
                "CreateAccount - SETS UP USERNAME+PASSWORD, RETURNS SELLER_ID\n"
                "Login - LOGIN WITH USERNAME+PASSWORD (starts session)\n"
                "Logout - ENDS ACTIVE SELLER SESSION\n"
                "GetSellerRating - RETURNS FEEDBACK FOR CURRENT SELLER\n"
                "RegisterItemForSale - REGISTER ITEM WITH ATTRIBUTES AND QUANTITY, RETURNS ITEM_ID\n"
                "ChangeItemPrice - UPDATE ITEM PRICE BY ITEM_ID\n"
                "UpdateUnitsForSale - REMOVE QUANTITY FROM ITEM_ID\n"
                "DisplayItemsForSale - DISPLAY ITEMS ON SALE BY CURRENT SELLER\n"
            )
            conn.send(bytes(help_text, "utf-8"))
        else:
            process_command(cmd, conn)
            # conn.send(bytes("Unknown command\n", "utf-8"))

    conn.close()
    print(f"Connection from {addr} closed")

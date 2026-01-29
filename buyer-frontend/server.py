#!/usr/bin/python
import socket
import threading
import interface

PORT = 5000
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(("0.0.0.0", PORT))
sock.listen(1)


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
        "getitem": interface.getItem,
        "getcategories": interface.getCategories,
        "searchitemsforsale": interface.searchItemsForSale,
        "savecart": interface.saveCart,
        "getcart": interface.getCart,
        "providefeedback": interface.provideFeedback,
        "getsellerrating": interface.getSellerRating,
        "getbuyerpurchases": interface.getBuyerPurchases,
        "makepurchase": interface.makePurchase,
    }
    command_name = commands[0].lower()

    if command_name not in mappings:
        conn.send(bytes(f"ERROR: Unknown command '{command_name}'", "utf-8"))
        return
    mappings[command_name](commands, conn)


print(f"Customer Frontend Server listening on port {PORT}...")


def handle_client(conn, addr):
    try:
        while True:  # Keep reading commands
            info = conn.recv(65536)
            if not info:  # Connection closed by client
                break
            cmd = info.decode("utf-8").strip()
            process_command(cmd, conn)
    except Exception as e:
        print(f"Error handling {addr}: {e}")
    finally:
        conn.close()
        print(f"Connection from {addr} closed")


while True:
    conn, addr = sock.accept()
    t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
    t.start()

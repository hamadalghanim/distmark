#!/usr/bin/python
import socket
from config import customer_db, products_db

PORT = 5000
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('0.0.0.0', PORT))
sock.listen(1)

print(f"Seller Frontend Server listening on port {PORT}...")
while True:
    conn, addr = sock.accept()
    print(f"Connection from {addr} has been established!")
    
    while True:  # Keep reading commands
        info = conn.recv(65536)
        if not info:  # Connection closed by client
            break
            
        cmd = info.decode('utf-8').strip()
        print(f"Received data: {cmd}")
        
        if cmd == "quit":
            break
        elif cmd.lower() == "help":
            help_text = (
                "Available commands:\n"
                "PING - Check server status\n"
                "GET_CUSTOMERS - Retrieve all customers\n"
                "GET_PRODUCTS - Retrieve all products\n"
                "QUIT - Close the connection\n"
            )
            conn.send(bytes(help_text, "utf-8"))
        elif cmd.lower() == "ping":
            conn.send(bytes("pong\n", "utf-8"))
        elif cmd == "GET_CUSTOMERS":
            results = customer_db.run_query("SELECT * FROM customers;")
            response = "\n".join([str(row) for row in results])
            conn.send(bytes(response + "\n", "utf-8"))
        elif cmd == "GET_PRODUCTS":
            results = products_db.run_query("SELECT * FROM products;")
            response = "\n".join([str(row) for row in results])
            conn.send(bytes(response + "\n", "utf-8"))
        else:
            conn.send(bytes("Unknown command\n", "utf-8"))
    
    conn.close()
    print(f"Connection from {addr} closed")
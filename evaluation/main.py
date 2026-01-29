import socket
import threading
import time
import random

number_of_clients_per_scenario = [1, 10, 100]
# number_of_clients_per_scenario = [1]

create_account = f"CreateAccount\njeff\nusername__id__\npassword\n"
login = f"Login\nusername__id__\npassword\n"
logout = f"Logout\n__session__\n"


def perform_random_buyer_cmd(sock, session_id):
    cmds = [
        f"GetItem\n{session_id}\n2\n",
        f"GetCategories\n{session_id}\n",
        f"SearchItemsForSale\n{session_id}\n0\ntech\n",
        f"ProvideFeedback\n{session_id}\n2\n1\n",
        f"GetSellerRating\n{session_id}\n1\n",
        f"ClearCart\n{session_id}\n",
        f"AddItemToCart\n{session_id}\n1\n1\n",
        f"RemoveItemFromCart\n{session_id}\n1\n",
        f"SaveCart\n{session_id}\n"
    ]
    cmd = random.choice(cmds)
    sock.send(bytes(cmd, encoding="utf-8"))
    sock.recv(1024)


def perform_random_seller_cmd(sock, session_id, item_id):
    cmds = [
        f"GetCategories\n{session_id}\n",
        f"GetSellerRating\n{session_id}\n",
        f"RegisterItemForSale\n{session_id}\nplunger\n1\nbath\nnew\n3.99\n20\n",
        f"DisplayItemsForSale\n{session_id}\n"
        f"ChangeItemPrice\n{session_id}\n{item_id}\n4.99\n",
        f"UpdateUnitsForSale\n{session_id}\n{item_id}\n900\n",
    ]
    cmd = random.choice(cmds)
    sock.send(bytes(cmd, encoding="utf-8"))
    sock.recv(1024)


def run_seller_client(id):
    id = str(id)

    create = create_account.replace("__id__", id)
    log = login.replace("__id__", id)
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        tcp_socket.connect(("localhost", 8000))
        tcp_socket.send(bytes(create, encoding="utf-8"))
        tcp_socket.recv(1024)
        tcp_socket.send(bytes(log, encoding="utf-8"))
        response = tcp_socket.recv(1024).decode("utf-8")

        if "Session ID:" in response:
            session_id = response.split("Session ID: ")[1].strip()
            # print(f"Logged in! Session ID for seller {id}: {session_id}")
            tcp_socket.send(
                bytes(
                    f"RegisterItemForSale\n{session_id}\nplunger1\n1\nbath\nnew\n3.99\n20\n",
                    encoding="utf-8",
                )
            )
            out = logout.replace("__session__", session_id)
            response = tcp_socket.recv(1024).decode("utf-8")
            item_id = response.split("Item registered with ID: ")[1].strip()

            for _ in range(996):
                perform_random_seller_cmd(tcp_socket, session_id, item_id)
            tcp_socket.send(bytes(out, encoding="utf-8"))
        else:
            print(response)

            print("Login failed or response format unexpected.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        tcp_socket.close()
    # maybe start an account then login then add items, get rating, get items listed
    # Seller client logic to perform 1000 operations


def run_buyer_client(id):
    id = str(id)
    create = create_account.replace("__id__", id)
    log = login.replace("__id__", id)

    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        tcp_socket.connect(("localhost", 8001))
        tcp_socket.send(bytes(create, encoding="utf-8"))
        tcp_socket.recv(1024)
        tcp_socket.send(bytes(log, encoding="utf-8"))
        response = tcp_socket.recv(1024).decode("utf-8")
        if "Session ID:" in response:
            session_id = response.split("Session ID: ")[1].strip()
            # print(f"Logged in! Session ID for buyer {id}: {session_id}")
            out = logout.replace("__session__", session_id)

            # 4. Perform 997 random operations
            for _ in range(997):
                perform_random_buyer_cmd(tcp_socket, session_id)
            tcp_socket.send(bytes(out, encoding="utf-8"))
        else:
            print(response)
            print("Login failed or response format unexpected.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        tcp_socket.close()


def main():
    for scenario in range(len(number_of_clients_per_scenario)):
        print(f"Starting Scenario {scenario}...")
        clients = number_of_clients_per_scenario[scenario]
        seller_threads = []
        buyer_threads = []
        start_time = time.time()
        for i in range(clients):
            seller_thread = threading.Thread(
                target=run_seller_client, args=((scenario + 1) * i,)
            )
            buyer_thread = threading.Thread(
                target=run_buyer_client, args=((scenario + 1) * i,)
            )
            seller_threads.append(seller_thread)
            buyer_threads.append(buyer_thread)
            seller_thread.start()
            buyer_thread.start()
        for st in seller_threads:
            st.join()
        for bt in buyer_threads:
            bt.join()
        end_time = time.time()
        total_time = end_time - start_time
        total_operations = clients * 1000 * 2  # 1000 operations per
        avg_response_time = total_time / total_operations
        throughput = total_operations / total_time
        print(f"Total time taken: {total_time:.2f} seconds")
        print(f"Average response time: {avg_response_time:.4f} seconds")
        print(f"Server throughput: {throughput:.2f} operations/second")

        print(f"Scenario {scenario} completed.\n")


if __name__ == "__main__":
    main()

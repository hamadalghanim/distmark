import socket
import threading
from time import time

number_of_clients_per_scenario = [1, 10, 100]


def main():
    for scenario in range(3):
        print(f"Starting Scenario {scenario}...")
        clients = number_of_clients_per_scenario[scenario]
        seller_threads = []
        buyer_threads = []
        start_time = time.time()
        for i in range(clients):
            seller_thread = threading.Thread(target=run_seller_client)
            buyer_thread = threading.Thread(target=run_buyer_client)
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


def run_seller_client():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect(("localhost", 8000))
    # maybe start an account then login then add items, get rating, get items listed
    # Seller client logic to perform 1000 operations


def run_buyer_client():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect(("localhost", 8001))
    # register, login then do 998 operations randomly?

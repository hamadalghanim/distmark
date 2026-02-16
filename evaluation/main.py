import requests
import threading
import time
import random

number_of_clients_per_scenario = [1, 10, 100]
# number_of_clients_per_scenario = [1]

BUYER_BASE_URL = "http://localhost:8001"
SELLER_BASE_URL = "http://localhost:8000"


def select_client_counts():
    print("\nNumber of clients per scenario")
    print("1. Default ([1, 10, 100])")
    print("2. Custom")

    choice = input("Select option (1 or 2): ").strip()

    if choice == "2":
        counts_input = input(
            "Enter comma-separated client counts (e.g., 1,5,20,50): "
        ).strip()
        try:
            counts = [int(x.strip()) for x in counts_input.split(",")]
            return counts
        except ValueError:
            print("Invalid input, using default")
            return [1, 10, 100]
    else:
        return [1, 10, 100]


def select_environment(service_name, local_url, gcp_url):
    print(f"\n{service_name}")
    print(f"1. Local ({local_url})")
    print(f"2. GCP ({gcp_url})")
    print("3. Custom")

    choice = input("Select environment (1, 2, or 3): ").strip()

    if choice == "1":
        return local_url
    elif choice == "2":
        return gcp_url
    elif choice == "3":
        return input("Enter custom server URL: ").strip()
    else:
        print("Invalid choice, defaulting to local")
        return local_url


BUYER_BASE_URL = select_environment(
    "Buyer Frontend Client", "http://localhost:8001", "http://34.72.178.240:80"
)

# Select Seller Frontend
SELLER_BASE_URL = select_environment(
    "Seller Frontend Client", "http://localhost:8000", "http://34.70.9.107:80"
)


def perform_random_buyer_cmd(session_id):
    cmds = [
        lambda: requests.get(
            f"{BUYER_BASE_URL}/items/2", params={"session_id": session_id}
        ),
        lambda: requests.get(
            f"{BUYER_BASE_URL}/categories", params={"session_id": session_id}
        ),
        lambda: requests.get(
            f"{BUYER_BASE_URL}/items/search",
            params={"session_id": session_id, "category_id": "0", "keywords": "tech"},
        ),
        lambda: requests.post(
            f"{BUYER_BASE_URL}/feedback",
            json={"session_id": session_id, "item_id": "2", "feedback": "1"},
        ),
        lambda: requests.get(
            f"{BUYER_BASE_URL}/seller/1/rating", params={"session_id": session_id}
        ),
        lambda: requests.post(
            f"{BUYER_BASE_URL}/cart/clear", json={"session_id": session_id}
        ),
        lambda: requests.post(
            f"{BUYER_BASE_URL}/cart/items",
            json={"session_id": session_id, "item_id": "1", "quantity": "1"},
        ),
        lambda: requests.delete(
            f"{BUYER_BASE_URL}/cart/items/1", json={"session_id": session_id}
        ),
        lambda: requests.post(
            f"{BUYER_BASE_URL}/cart/save", json={"session_id": session_id}
        ),
        lambda: requests.get(
            f"{BUYER_BASE_URL}/cart", params={"session_id": session_id}
        ),
        lambda: requests.post(
            f"{BUYER_BASE_URL}/purchase",
            json={
                "session_id": session_id,
                "card_number": "1234567890123456",
                "expiration_date": "12/25",
                "security_code": "123",
            },
        ),
        lambda: requests.get(
            f"{BUYER_BASE_URL}/purchases", params={"session_id": session_id}
        ),
    ]

    try:
        cmd = random.choice(cmds)
        cmd()
    except Exception as e:
        print(f"error? {e}")


def perform_random_seller_cmd(session_id, item_id):
    cmds = [
        lambda: requests.get(
            f"{SELLER_BASE_URL}/categories", params={"session_id": session_id}
        ),
        lambda: requests.get(
            f"{SELLER_BASE_URL}/seller/rating", params={"session_id": session_id}
        ),
        lambda: requests.post(
            f"{SELLER_BASE_URL}/items",
            json={
                "session_id": session_id,
                "name": "plunger",
                "category": "1",
                "keywords": "bath",
                "condition": "new",
                "price": "3.99",
                "qty": "20",
            },
        ),
        lambda: requests.get(
            f"{SELLER_BASE_URL}/items", params={"session_id": session_id}
        ),
        lambda: requests.put(
            f"{SELLER_BASE_URL}/items/price",
            json={
                "session_id": session_id,
                "item_id": str(item_id),
                "new_price": "4.99",
            },
        ),
        lambda: requests.put(
            f"{SELLER_BASE_URL}/items/quantity",
            json={"session_id": session_id, "item_id": str(item_id), "new_qty": "900"},
        ),
    ]

    try:
        cmd = random.choice(cmds)
        cmd()
    except Exception as e:
        print(f"error? {e}")


def run_seller_client(id):
    id = str(id)

    try:
        requests.post(
            f"{SELLER_BASE_URL}/account/register",
            json={"name": "jeff", "username": f"username{id}", "password": "password"},
        )

        login_response = requests.post(
            f"{SELLER_BASE_URL}/account/login",
            json={"username": f"username{id}", "password": "password"},
        )

        if login_response.status_code == 200:
            login_data = login_response.json()
            session_id = login_data.get("session_id")

            if session_id:
                # 3. Register initial item
                register_item_response = requests.post(
                    f"{SELLER_BASE_URL}/items",
                    json={
                        "session_id": session_id,
                        "name": "plunger1",
                        "category": "1",
                        "keywords": "bath",
                        "condition": "new",
                        "price": "3.99",
                        "qty": "20",
                    },
                )

                item_id = None
                if register_item_response.status_code == 200:
                    item_data = register_item_response.json()
                    item_id = item_data.get("item_id", 1)

                # perform 996 random operations (1 create + 1 register + 1login + 996 random + 1 logout = 1000)
                for _ in range(996):
                    perform_random_seller_cmd(session_id, item_id if item_id else 1)

                requests.post(
                    f"{SELLER_BASE_URL}/account/logout", json={"session_id": session_id}
                )
            else:
                print(f"Seller {id}: Login failed - no session ID")
        else:
            print(
                f"Seller {id}: Login request failed with status {login_response.status_code}"
            )

    except Exception as e:
        print(f"Seller {id} error: {e}")


def run_buyer_client(id):
    id = str(id)

    try:
        requests.post(
            f"{BUYER_BASE_URL}/account/register",
            json={"name": "jeff", "username": f"username{id}", "password": "password"},
        )

        login_response = requests.post(
            f"{BUYER_BASE_URL}/account/login",
            json={"username": f"username{id}", "password": "password"},
        )

        if login_response.status_code == 200:
            login_data = login_response.json()
            session_id = login_data.get("session_id")

            if session_id:
                # perform 997 random operations (1 create + 1 login + 997 random + 1 logout = 1000)
                for _ in range(997):
                    perform_random_buyer_cmd(session_id)

                requests.post(
                    f"{BUYER_BASE_URL}/account/logout", json={"session_id": session_id}
                )
            else:
                print(f"Buyer {id}: Login failed - no session ID")
        else:
            print(
                f"Buyer {id}: Login request failed with status {login_response.status_code}"
            )

    except Exception as e:
        print(f"Buyer {id} error: {e}")


def main():

    number_of_clients_per_scenario = select_client_counts()
    print("\nConfiguration:")
    print(f"Buyer:  {BUYER_BASE_URL}")
    print(f"Seller: {SELLER_BASE_URL}")

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
        total_operations = clients * 1000 * 2  # 1000 operations per client
        avg_response_time = total_time / total_operations
        throughput = total_operations / total_time

        print(f"Total time taken: {total_time:.2f} seconds")
        print(f"Average response time: {avg_response_time:.4f} seconds")
        print(f"Server throughput: {throughput:.2f} operations/second")
        print(f"Scenario {scenario} completed.\n")


if __name__ == "__main__":
    main()

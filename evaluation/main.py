import requests
import threading
import time
import random
from collections import defaultdict
from dataclasses import dataclass
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BUYER_BASE_URL = "http://localhost:8001"
SELLER_BASE_URL = "http://localhost:8000"


@dataclass
class EndpointStats:
    count: int = 0
    total_ms: float = 0.0
    errors: int = 0

    def record(self, ms: float):
        self.count += 1
        self.total_ms += ms

    def record_error(self):
        self.errors += 1

    @property
    def avg_ms(self):
        return self.total_ms / self.count if self.count else 0.0

    @property
    def throughput(self):
        return self.count / (self.total_ms / 1000) if self.total_ms else 0.0


# Global stats: { endpoint_key -> EndpointStats }
_stats_lock = threading.Lock()
_canceled = False
_endpoint_stats: dict[str, EndpointStats] = defaultdict(EndpointStats)

# Per-client stats: { client_id -> EndpointStats (aggregate) }
_client_stats: dict[str, EndpointStats] = defaultdict(EndpointStats)


def _record(endpoint_key: str, client_id: str, ms: float, error: bool = False):
    with _stats_lock:
        if error:
            _endpoint_stats[endpoint_key].record_error()
            _client_stats[client_id].record_error()
        else:
            _endpoint_stats[endpoint_key].record(ms)
            _client_stats[client_id].record(ms)


def _timed(endpoint_key: str, client_id: str, fn):
    t0 = time.monotonic()
    try:
        fn()
        ms = (time.monotonic() - t0) * 1000
        _record(endpoint_key, client_id, ms)
    except Exception as e:
        ms = (time.monotonic() - t0) * 1000
        _record(endpoint_key, client_id, ms, error=True)
        print(f"[{client_id}] {endpoint_key} error: {e}")


thread_local = threading.local()


def get_session():
    if not hasattr(thread_local, "session"):
        s = requests.Session()
        retry = Retry(total=1, backoff_factor=0.05)
        adapter = HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=retry)
        s.mount("http://", adapter)
        s.mount("https://", adapter)
        thread_local.session = s
    return thread_local.session


def perform_random_buyer_cmd(session_id: str, client_id: str):
    session = get_session()
    cmds = [
        (
            "GET /items/{id}",
            lambda: session.get(
                f"{BUYER_BASE_URL}/items/2",
                params={"session_id": session_id},
                timeout=3,
            ),
        ),
        (
            "GET /categories",
            lambda: session.get(
                f"{BUYER_BASE_URL}/categories",
                params={"session_id": session_id},
                timeout=3,
            ),
        ),
        (
            "GET /items/search",
            lambda: session.get(
                f"{BUYER_BASE_URL}/items/search",
                params={
                    "session_id": session_id,
                    "category_id": "0",
                    "keywords": "tech",
                },
                timeout=3,
            ),
        ),
        (
            "POST /feedback",
            lambda: session.post(
                f"{BUYER_BASE_URL}/feedback",
                json={"session_id": session_id, "item_id": "2", "feedback": "1"},
                timeout=3,
            ),
        ),
        (
            "GET /seller/{id}/rating",
            lambda: session.get(
                f"{BUYER_BASE_URL}/seller/1/rating",
                params={"session_id": session_id},
                timeout=3,
            ),
        ),
        (
            "POST /cart/clear",
            lambda: session.post(
                f"{BUYER_BASE_URL}/cart/clear",
                json={"session_id": session_id},
                timeout=3,
            ),
        ),
        (
            "POST /cart/items",
            lambda: session.post(
                f"{BUYER_BASE_URL}/cart/items",
                json={"session_id": session_id, "item_id": "1", "quantity": "1"},
                timeout=3,
            ),
        ),
        (
            "DELETE /cart/items/{id}",
            lambda: session.delete(
                f"{BUYER_BASE_URL}/cart/items/1",
                json={"session_id": session_id},
                timeout=3,
            ),
        ),
        (
            "POST /cart/save",
            lambda: session.post(
                f"{BUYER_BASE_URL}/cart/save",
                json={"session_id": session_id},
                timeout=3,
            ),
        ),
        (
            "GET /cart",
            lambda: session.get(
                f"{BUYER_BASE_URL}/cart", params={"session_id": session_id}, timeout=3
            ),
        ),
        (
            "POST /purchase",
            lambda: session.post(
                f"{BUYER_BASE_URL}/purchase",
                json={
                    "session_id": session_id,
                    "card_number": "1234567890123456",
                    "expiration_date": "12/25",
                    "security_code": "123",
                },
                timeout=3,
            ),
        ),
        (
            "GET /purchases",
            lambda: session.get(
                f"{BUYER_BASE_URL}/purchases",
                params={"session_id": session_id},
                timeout=3,
            ),
        ),
    ]
    key, fn = random.choice(cmds)
    _timed(f"buyer  {key}", client_id, fn)


# seller


def perform_random_seller_cmd(session_id: str, item_id, client_id: str):
    session = get_session()
    cmds = [
        (
            "GET /categories",
            lambda: session.get(
                f"{SELLER_BASE_URL}/categories",
                params={"session_id": session_id},
                timeout=3,
            ),
        ),
        (
            "GET /seller/rating",
            lambda: session.get(
                f"{SELLER_BASE_URL}/seller/rating",
                params={"session_id": session_id},
                timeout=3,
            ),
        ),
        (
            "POST /items",
            lambda: session.post(
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
                timeout=3,
            ),
        ),
        (
            "GET /items",
            lambda: session.get(
                f"{SELLER_BASE_URL}/items",
                params={"session_id": session_id},
                timeout=3,
            ),
        ),
        (
            "PUT /items/price",
            lambda: session.put(
                f"{SELLER_BASE_URL}/items/price",
                json={
                    "session_id": session_id,
                    "item_id": str(item_id),
                    "new_price": "4.99",
                },
                timeout=3,
            ),
        ),
        (
            "PUT /items/quantity",
            lambda: session.put(
                f"{SELLER_BASE_URL}/items/quantity",
                json={
                    "session_id": session_id,
                    "item_id": str(item_id),
                    "new_qty": "900",
                },
                timeout=3,
            ),
        ),
    ]
    key, fn = random.choice(cmds)
    _timed(f"seller {key}", client_id, fn)


# client


def run_seller_client(id: int, scenario: int):
    session = get_session()
    unique_id = f"s{scenario}_u{id}"
    client_id = f"seller/{unique_id}"

    try:
        _timed(
            "seller POST /account/register",
            client_id,
            lambda: session.post(
                f"{SELLER_BASE_URL}/account/register",
                json={"name": "jeff", "username": unique_id, "password": "password"},
                timeout=3,
            ),
        )

        login_response = None

        def do_login():
            nonlocal login_response
            login_response = session.post(
                f"{SELLER_BASE_URL}/account/login",
                json={"username": unique_id, "password": "password"},
                timeout=3,
            )

        _timed("seller POST /account/login", client_id, do_login)

        if login_response and login_response.status_code == 200:
            session_id = login_response.json().get("session_id")
            if not session_id:
                print(f"[{client_id}] Login failed - no session ID")
                return

            item_id = None
            register_response = None

            def do_register():
                nonlocal register_response
                register_response = session.post(
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
                    timeout=3,
                )

            _timed("seller POST /items", client_id, do_register)

            if register_response and register_response.status_code == 200:
                item_id = register_response.json().get("item_id", 1)

            for i in range(996):
                if _canceled:
                    break
                if (i + 4) % 100 == 0:
                    print(f"  Seller {id} {i + 4}/1000")
                perform_random_seller_cmd(session_id, item_id or 1, client_id)

            _timed(
                "seller POST /account/logout",
                client_id,
                lambda: session.post(
                    f"{SELLER_BASE_URL}/account/logout",
                    json={"session_id": session_id},
                    timeout=3,
                ),
            )
        else:
            status = login_response.status_code if login_response else "N/A"
            print(f"[{client_id}] Login failed with status {status}")

    except Exception as e:
        print(f"[{client_id}] Fatal error: {e}")


def run_buyer_client(id: int, scenario: int):
    session = get_session()
    unique_id = f"s{scenario}_u{id}"
    client_id = f"buyer/{unique_id}"

    try:
        _timed(
            "buyer  POST /account/register",
            client_id,
            lambda: session.post(
                f"{BUYER_BASE_URL}/account/register",
                json={"name": "jeff", "username": unique_id, "password": "password"},
                timeout=3,
            ),
        )

        login_response = None

        def do_login():
            nonlocal login_response
            login_response = session.post(
                f"{BUYER_BASE_URL}/account/login",
                json={"username": unique_id, "password": "password"},
                timeout=3,
            )

        _timed("buyer  POST /account/login", client_id, do_login)

        if login_response and login_response.status_code == 200:
            session_id = login_response.json().get("session_id")
            if not session_id:
                print(f"[{client_id}] Login failed - no session ID")
                return

            for i in range(997):
                if _canceled:
                    break
                if (i + 3) % 100 == 0:
                    print(f"  Buyer  {id} {i + 3}/1000")
                perform_random_buyer_cmd(session_id, client_id)

            _timed(
                "buyer  POST /account/logout",
                client_id,
                lambda: session.post(
                    f"{BUYER_BASE_URL}/account/logout",
                    json={"session_id": session_id},
                    timeout=3,
                ),
            )
        else:
            status = login_response.status_code if login_response else "N/A"
            print(f"[{client_id}] Login failed with status {status}")

    except Exception as e:
        print(f"[{client_id}] Fatal error: {e}")


def print_scenario_report(
    scenario: int,
    clients: int,
    elapsed: float,
    endpoint_snapshot: dict,
    client_snapshot: dict,
    file=None,  # pass an open file handle, or None for stdout
):
    def p(*args, **kwargs):
        print(*args, **kwargs, file=file)

    total_ops = sum(s.count for s in endpoint_snapshot.values())
    total_errors = sum(s.errors for s in endpoint_snapshot.values())
    throughput = total_ops / elapsed if elapsed else 0

    p(f"\n{'═' * 70}")
    p(f"  SCENARIO {scenario}  —  {clients} buyer(s) + {clients} seller(s)")
    p(f"{'═' * 70}")
    p(f"  Elapsed:    {elapsed:.2f}s")
    p(f"  Total ops:  {total_ops}  ({total_errors} errors)")
    p(f"  Throughput: {throughput:.1f} ops/sec")

    p(f"\n  {'ENDPOINT':<40} {'CALLS':>7} {'AVG ms':>9} {'ERR':>6}")
    p(f"  {'-' * 40} {'-' * 7} {'-' * 9} {'-' * 6}")
    for key in sorted(endpoint_snapshot):
        s = endpoint_snapshot[key]
        p(f"  {key:<40} {s.count:>7} {s.avg_ms:>9.1f} {s.errors:>6}")

    if client_snapshot:
        sorted_clients = sorted(
            client_snapshot.items(), key=lambda x: x[1].avg_ms, reverse=True
        )
        p("\n  TOP 5 SLOWEST CLIENTS (avg ms)")
        p(f"  {'CLIENT':<35} {'CALLS':>7} {'AVG ms':>9} {'ERR':>6}")
        p(f"  {'-' * 35} {'-' * 7} {'-' * 9} {'-' * 6}")
        for cid, s in sorted_clients[:5]:
            p(f"  {cid:<35} {s.count:>7} {s.avg_ms:>9.1f} {s.errors:>6}")

    p()


def select_environment(service_name, local_url, gcp_url):
    print(f"\n{service_name}")
    print(f"1. Local ({local_url})")
    print(f"2. GCP ({gcp_url})")
    print("3. Custom")
    choice = input("Select environment (1, 2, or 3): ").strip()
    if choice == "2":
        return gcp_url
    elif choice == "3":
        return input("Enter custom server URL: ").strip()
    return local_url


def main():
    global BUYER_BASE_URL, SELLER_BASE_URL
    BUYER_BASE_URL = select_environment(
        "Buyer Frontend", "http://localhost:8001", "http://34.106.251.143:80"
    )
    SELLER_BASE_URL = select_environment(
        "Seller Frontend", "http://localhost:8000", "http://34.106.116.74:80"
    )
    counts = [1, 10, 100]

    print(f"\nBuyer:  {BUYER_BASE_URL}")
    print(f"Seller: {SELLER_BASE_URL}")

    for scenario, clients in enumerate(counts):
        # Reset stats for this scenario
        with _stats_lock:
            _endpoint_stats.clear()
            _client_stats.clear()

        print(f"\nStarting Scenario {scenario} ({clients} client(s) each side)...")
        threads = []
        start = time.monotonic()

        for i in range(clients):
            threads.append(
                threading.Thread(target=run_seller_client, args=(i, scenario))
            )
            threads.append(
                threading.Thread(target=run_buyer_client, args=(i, scenario))
            )

        for t in threads:
            t.start()
        try:
            while any(t.is_alive() for t in threads):
                time.sleep(1)
        except KeyboardInterrupt:
            print("Interrupted, waiting for threads to finish...")
            global _canceled
            _canceled = True
        for t in threads:
            t.join()

        elapsed = time.monotonic() - start

        with _stats_lock:
            endpoint_snapshot = {
                k: EndpointStats(v.count, v.total_ms, v.errors)
                for k, v in _endpoint_stats.items()
            }
            client_snapshot = {
                k: EndpointStats(v.count, v.total_ms, v.errors)
                for k, v in _client_stats.items()
            }
        with open("report_one_seller_leader_down.txt", "a") as f:
            print_scenario_report(
                scenario, clients, elapsed, endpoint_snapshot, client_snapshot, file=f
            )
        _canceled = False  # reset for next scenario


if __name__ == "__main__":
    main()

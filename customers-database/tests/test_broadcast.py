"""
tests/test_customers_broadcast.py — Integration tests for customers atomic broadcast

Verifies that writes submitted to different customer nodes are reflected
consistently on all nodes.
"""

import os
import time
import threading
import uuid

import grpc
import pytest

from proto import customers_pb2
from proto import customers_pb2_grpc


# ── Config ────────────────────────────────────────────────────────────────────

NODE_ADDRS = [
    os.environ.get("REPLICA0_ADDR", "localhost:5000"),
    os.environ.get("REPLICA1_ADDR", "localhost:5001"),
    os.environ.get("REPLICA2_ADDR", "localhost:5002"),
    os.environ.get("REPLICA3_ADDR", "localhost:5003"),
    os.environ.get("REPLICA4_ADDR", "localhost:5004"),
]

PROPAGATION_WAIT = 1.0


def _make_stub(addr):
    return customers_pb2_grpc.CustomersServiceStub(grpc.insecure_channel(addr))


def uid():
    return uuid.uuid4().hex[:8]


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def nodes():
    return {i: _make_stub(addr) for i, addr in enumerate(NODE_ADDRS)}


@pytest.fixture()
def registered_buyer(nodes):
    """Create a buyer via node 0 and return context dict."""
    username, password = f"buyer_{uid()}", "pass123"

    resp = nodes[0].CreateAccount(
        customers_pb2.CreateAccountRequest(
            username=username,
            password=password,
        )
    )
    assert resp.success, f"CreateAccount failed: {resp.message}"

    login = nodes[0].Login(
        customers_pb2.LoginRequest(username=username, password=password)
    )
    assert login.success, f"Login failed: {login.message}"

    time.sleep(PROPAGATION_WAIT)
    return {
        "buyer_id": resp.buyer_id,
        "session_id": login.session_id,
        "username": username,
        "password": password,
        "nodes": nodes,
    }


# ── TestAccountConsistency ────────────────────────────────────────────────────


class TestAccountConsistency:
    def test_create_account_visible_on_all_nodes(self, nodes):
        """Account created on node 0 must be loginable on all 5 nodes."""
        username, password = f"buyer_{uid()}", "secret"
        resp = nodes[0].CreateAccount(
            customers_pb2.CreateAccountRequest(
                username=username,
                password=password,
            )
        )
        assert resp.success, resp.message
        time.sleep(PROPAGATION_WAIT)

        for nid, stub in nodes.items():
            login = stub.Login(
                customers_pb2.LoginRequest(username=username, password=password)
            )
            assert login.success, f"Login failed on node {nid}: {login.message}"

    def test_account_created_on_node2_visible_on_all(self, nodes):
        """Account created on node 2 must propagate to all nodes."""
        username, password = f"buyer_{uid()}", "pass"
        resp = nodes[2].CreateAccount(
            customers_pb2.CreateAccountRequest(
                username=username,
                password=password,
            )
        )
        assert resp.success, resp.message
        time.sleep(PROPAGATION_WAIT)

        for nid, stub in nodes.items():
            login = stub.Login(
                customers_pb2.LoginRequest(username=username, password=password)
            )
            assert login.success, f"Login failed on node {nid}: {login.message}"

    def test_duplicate_account_rejected_on_all_nodes(self, nodes):
        """Creating the same username twice must fail on every node."""
        username, password = f"buyer_{uid()}", "pass"
        nodes[0].CreateAccount(
            customers_pb2.CreateAccountRequest(username=username, password=password)
        )
        time.sleep(PROPAGATION_WAIT)

        for nid, stub in nodes.items():
            r2 = stub.CreateAccount(
                customers_pb2.CreateAccountRequest(username=username, password=password)
            )
            assert not r2.success, f"Duplicate account succeeded on node {nid}"

    def test_logout_reflected_on_all_nodes(self, registered_buyer):
        """Session logged out on node 0 must be invalid on all nodes."""
        b = registered_buyer

        login = b["nodes"][0].Login(
            customers_pb2.LoginRequest(
                username=b["username"],
                password=b["password"],
            )
        )
        assert login.success
        session_id = login.session_id
        time.sleep(PROPAGATION_WAIT)

        # Verify valid everywhere first.
        for nid, stub in b["nodes"].items():
            resp = stub.GetBuyer(customers_pb2.GetBuyerRequest(session_id=session_id))
            assert resp.success, f"Session not valid on node {nid} before logout"

        logout = b["nodes"][0].Logout(
            customers_pb2.LogoutRequest(session_id=session_id)
        )
        assert logout.success
        time.sleep(PROPAGATION_WAIT)

        for nid, stub in b["nodes"].items():
            resp = stub.GetBuyer(customers_pb2.GetBuyerRequest(session_id=session_id))
            assert not resp.success, f"Stale session still valid on node {nid}"


# ── TestCartConsistency ───────────────────────────────────────────────────────


class TestCartConsistency:
    def test_add_item_visible_on_all_nodes(self, registered_buyer):
        """Item added to cart on node 1 must appear on all nodes."""
        b, session_id = registered_buyer, registered_buyer["session_id"]
        item_id = 42  # arbitrary — cart just stores the ID

        resp = b["nodes"][1].AddItemToCart(
            customers_pb2.AddItemToCartRequest(
                session_id=session_id,
                item_id=item_id,
                quantity=3,
            )
        )
        assert resp.success, f"AddItemToCart failed: {resp.message}"
        time.sleep(PROPAGATION_WAIT)

        for nid, stub in b["nodes"].items():
            cart = stub.GetCart(customers_pb2.GetCartRequest(session_id=session_id))
            assert cart.success
            ids = [i.item_id for i in cart.session_cart]
            assert item_id in ids, f"Item not in cart on node {nid}"

    def test_remove_item_reflected_on_all_nodes(self, registered_buyer):
        """Item removed from cart must disappear on all nodes."""
        b, session_id = registered_buyer, registered_buyer["session_id"]
        item_id = 99

        b["nodes"][0].AddItemToCart(
            customers_pb2.AddItemToCartRequest(
                session_id=session_id,
                item_id=item_id,
                quantity=1,
            )
        )
        time.sleep(PROPAGATION_WAIT)

        b["nodes"][2].RemoveItemFromCart(
            customers_pb2.RemoveItemFromCartRequest(
                session_id=session_id,
                item_id=item_id,
            )
        )
        time.sleep(PROPAGATION_WAIT)

        for nid, stub in b["nodes"].items():
            cart = stub.GetCart(customers_pb2.GetCartRequest(session_id=session_id))
            ids = [i.item_id for i in cart.session_cart]
            assert item_id not in ids, f"Removed item still in cart on node {nid}"

    def test_clear_cart_reflected_on_all_nodes(self, registered_buyer):
        """Clearing cart on node 3 must empty it on all nodes."""
        b, session_id = registered_buyer, registered_buyer["session_id"]

        for item_id in [1, 2, 3]:
            b["nodes"][0].AddItemToCart(
                customers_pb2.AddItemToCartRequest(
                    session_id=session_id,
                    item_id=item_id,
                    quantity=1,
                )
            )
        time.sleep(PROPAGATION_WAIT)

        b["nodes"][3].ClearCart(customers_pb2.ClearCartRequest(session_id=session_id))
        time.sleep(PROPAGATION_WAIT)

        for nid, stub in b["nodes"].items():
            cart = stub.GetCart(customers_pb2.GetCartRequest(session_id=session_id))
            assert cart.success
            assert len(cart.session_cart) == 0, f"Cart not empty on node {nid}"

    def test_save_cart_reflected_on_all_nodes(self, registered_buyer):
        """Saved cart on node 0 must appear in saved_cart on all nodes."""
        b, session_id = registered_buyer, registered_buyer["session_id"]
        item_id = 77

        b["nodes"][0].AddItemToCart(
            customers_pb2.AddItemToCartRequest(
                session_id=session_id,
                item_id=item_id,
                quantity=2,
            )
        )
        time.sleep(PROPAGATION_WAIT)

        b["nodes"][0].SaveCart(customers_pb2.SaveCartRequest(session_id=session_id))
        time.sleep(PROPAGATION_WAIT)

        for nid, stub in b["nodes"].items():
            cart = stub.GetCart(customers_pb2.GetCartRequest(session_id=session_id))
            assert cart.success
            saved_ids = [i.item_id for i in cart.saved_cart]
            assert item_id in saved_ids, f"Saved cart missing item on node {nid}"


# ── TestPurchaseConsistency ───────────────────────────────────────────────────


class TestPurchaseConsistency:
    def test_purchase_recorded_on_all_nodes(self, registered_buyer):
        """Purchase made on node 4 must appear in GetBuyerPurchases on all nodes."""
        b, session_id = registered_buyer, registered_buyer["session_id"]
        item_id = 55

        b["nodes"][0].AddItemToCart(
            customers_pb2.AddItemToCartRequest(
                session_id=session_id,
                item_id=item_id,
                quantity=2,
            )
        )
        time.sleep(PROPAGATION_WAIT / 2)
        b["nodes"][0].SaveCart(customers_pb2.SaveCartRequest(session_id=session_id))
        time.sleep(PROPAGATION_WAIT)

        resp = b["nodes"][4].MakePurchase(
            customers_pb2.MakePurchaseRequest(session_id=session_id)
        )
        assert resp.success, f"MakePurchase failed: {resp.message}"
        time.sleep(PROPAGATION_WAIT)

        for nid, stub in b["nodes"].items():
            purchases = stub.GetBuyerPurchases(
                customers_pb2.GetBuyerPurchasesRequest(session_id=session_id)
            )
            assert purchases.success
            ids = [p.item_id for p in purchases.purchases]
            assert item_id in ids, f"Purchase not recorded on node {nid}"


# ── TestConcurrentWrites ──────────────────────────────────────────────────────


class TestConcurrentWrites:
    def test_concurrent_cart_adds_consistent(self, registered_buyer):
        """
        Two nodes simultaneously add different items to the same cart.
        All nodes must end up with both items.
        """
        b, session_id = registered_buyer, registered_buyer["session_id"]
        item_a, item_b = 101, 102
        errors = []

        def add(stub, item_id):
            resp = stub.AddItemToCart(
                customers_pb2.AddItemToCartRequest(
                    session_id=session_id,
                    item_id=item_id,
                    quantity=1,
                )
            )
            if not resp.success:
                errors.append(resp.message)

        t0 = threading.Thread(target=add, args=(b["nodes"][0], item_a))
        t1 = threading.Thread(target=add, args=(b["nodes"][1], item_b))
        t0.start()
        t1.start()
        t0.join()
        t1.join()

        assert not errors, f"Cart errors: {errors}"
        time.sleep(PROPAGATION_WAIT * 2)

        for nid, stub in b["nodes"].items():
            cart = stub.GetCart(customers_pb2.GetCartRequest(session_id=session_id))
            ids = [i.item_id for i in cart.session_cart]
            assert item_a in ids, f"Item A missing on node {nid}"
            assert item_b in ids, f"Item B missing on node {nid}"

    def test_concurrent_accounts_all_created(self, nodes):
        """
        Five accounts created simultaneously across all 5 nodes.
        Every account must be loginable on every node afterwards.
        """
        credentials = [(f"buyer_{uid()}", "pass") for _ in range(5)]
        errors = []

        def create(stub, username, password):
            resp = stub.CreateAccount(
                customers_pb2.CreateAccountRequest(
                    username=username,
                    password=password,
                )
            )
            if not resp.success:
                errors.append(f"{username}: {resp.message}")

        threads = [
            threading.Thread(target=create, args=(nodes[i], creds[0], creds[1]))
            for i, creds in enumerate(credentials)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"CreateAccount errors: {errors}"
        time.sleep(PROPAGATION_WAIT * 2)

        for username, password in credentials:
            for nid, stub in nodes.items():
                login = stub.Login(
                    customers_pb2.LoginRequest(username=username, password=password)
                )
                assert login.success, f"{username} not loginable on node {nid}"

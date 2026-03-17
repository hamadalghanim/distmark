"""
tests/test_raft.py — Integration tests for the Raft-replicated products service

Key differences from the sequencer tests:
  - Raft elects a single leader; writes to followers are retried by the test
    using _write() which tries all nodes until one succeeds (the leader).
  - After a write succeeds, all nodes apply it from the committed log —
    reads on any node should reflect the write after PROPAGATION_WAIT.
  - PROPAGATION_WAIT is longer than the sequencer tests to allow for
    initial leader election on startup.
"""

import os
import time
import threading
import uuid

import grpc
import pytest
from grpc import RpcError, StatusCode

from proto import products_pb2
from proto import products_pb2_grpc


# ── Config ────────────────────────────────────────────────────────────────────

NODE_ADDRS = [
    os.environ.get("PRODUCTS_NODE0_ADDR", "localhost:5000"),
    os.environ.get("PRODUCTS_NODE1_ADDR", "localhost:5001"),
    os.environ.get("PRODUCTS_NODE2_ADDR", "localhost:5002"),
    os.environ.get("PRODUCTS_NODE3_ADDR", "localhost:5003"),
    os.environ.get("PRODUCTS_NODE4_ADDR", "localhost:5004"),
]

# Raft leader election + log commit + DB write propagation
PROPAGATION_WAIT = 2.0
# How long to wait for initial leader election before running any tests
ELECTION_WAIT = 5.0


def _make_stub(addr):
    return products_pb2_grpc.SellerServiceStub(grpc.insecure_channel(addr))


def uid():
    return uuid.uuid4().hex[:8]


def _write(nodes: dict, fn, *args, retries=10, delay=0.5):
    """
    Try fn(stub, *args) on each node until one succeeds (the leader).
    Returns (node_id, response).  Raises AssertionError if all fail.
    """
    last_err = None
    for attempt in range(retries):
        for nid, stub in nodes.items():
            try:
                resp = fn(stub, *args)
                # PySyncObj returns None on followers for sync=True calls
                # that hit NotLeaderException — treat as transient, keep trying
                if resp is None:
                    continue
                return nid, resp
            except RpcError as e:
                last_err = e
                continue
        time.sleep(delay)
    raise AssertionError(
        f"No leader responded after {retries} attempts. Last error: {last_err}"
    )


def _register_item(
    stub,
    session_id,
    category_id,
    *,
    name=None,
    price=9.99,
    quantity=10,
    keywords="test widget",
):
    return stub.RegisterItemForSale(
        products_pb2.RegisterItemRequest(
            session_id=session_id,
            item_name=name or f"item_{uid()}",
            category_id=category_id,
            keywords=keywords,
            condition="NEW",
            price=price,
            quantity=quantity,
        )
    )


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def nodes():
    stubs = {i: _make_stub(addr) for i, addr in enumerate(NODE_ADDRS)}
    # Wait for Raft to elect a leader before running any tests
    time.sleep(ELECTION_WAIT)
    return stubs


@pytest.fixture()
def registered_seller(nodes):
    username, password = f"seller_{uid()}", "pass123"

    _, resp = _write(
        nodes,
        lambda stub: stub.CreateAccount(
            products_pb2.CreateAccountRequest(
                name="Test Seller",
                username=username,
                password=password,
            )
        ),
    )
    assert resp.success, f"CreateAccount failed: {resp.message}"

    _, login = _write(
        nodes,
        lambda stub: stub.Login(
            products_pb2.LoginRequest(username=username, password=password)
        ),
    )
    assert login.success, f"Login failed: {login.message}"

    time.sleep(PROPAGATION_WAIT)
    return {
        "seller_id": resp.seller_id,
        "session_id": login.session_id,
        "username": username,
        "password": password,
        "nodes": nodes,
    }


@pytest.fixture()
def registered_item(registered_seller):
    s = registered_seller
    _, cat = _write(
        s["nodes"],
        lambda stub: stub.GetCategoriesClient(
            products_pb2.GetCategoriesClientRequest()
        ),
    )
    assert cat.success and cat.categories
    category_id = cat.categories[0].id

    _, resp = _write(
        s["nodes"], lambda stub: _register_item(stub, s["session_id"], category_id)
    )
    assert resp.success, f"RegisterItemForSale failed: {resp.message}"
    time.sleep(PROPAGATION_WAIT)
    return {**s, "item_id": resp.item_id, "category_id": category_id}


# ── TestAccountConsistency ────────────────────────────────────────────────────


class TestAccountConsistency:
    def test_create_account_visible_on_all_nodes(self, nodes):
        """Account written via leader must be readable on all 5 nodes."""
        username, password = f"seller_{uid()}", "secret"

        _, resp = _write(
            nodes,
            lambda stub: stub.CreateAccount(
                products_pb2.CreateAccountRequest(
                    name="Alice",
                    username=username,
                    password=password,
                )
            ),
        )
        assert resp.success, resp.message
        time.sleep(PROPAGATION_WAIT)

        for nid, stub in nodes.items():
            login = stub.Login(
                products_pb2.LoginRequest(username=username, password=password)
            )
            assert login.success, f"Login failed on node {nid}: {login.message}"

    def test_duplicate_account_rejected(self, nodes):
        """Second CreateAccount for same username must fail on every node."""
        username, password = f"seller_{uid()}", "pass"

        _write(
            nodes,
            lambda stub: stub.CreateAccount(
                products_pb2.CreateAccountRequest(
                    name="Bob", username=username, password=password
                )
            ),
        )
        time.sleep(PROPAGATION_WAIT)

        for nid, stub in nodes.items():
            r2 = stub.CreateAccount(
                products_pb2.CreateAccountRequest(
                    name="Bob2",
                    username=username,
                    password=password,
                )
            )
            # Either fails immediately (follower with stale read) or after commit
            if r2 is not None:
                assert not r2.success, f"Duplicate succeeded on node {nid}"

    def test_login_session_valid_on_all_nodes(self, registered_seller):
        """Session created via leader must be accepted by every node for reads."""
        s = registered_seller
        session_id = s["session_id"]

        for nid, stub in s["nodes"].items():
            resp = stub.DisplayItemsForSale(
                products_pb2.DisplayItemsRequest(session_id=session_id)
            )
            assert resp.success, f"Session not valid on node {nid}: {resp.message}"

    def test_logout_reflected_on_all_nodes(self, registered_seller):
        """Logout committed via Raft must invalidate session on every node."""
        s = registered_seller

        _, login = _write(
            s["nodes"],
            lambda stub: stub.Login(
                products_pb2.LoginRequest(
                    username=s["username"],
                    password=s["password"],
                )
            ),
        )
        assert login.success
        session_id = login.session_id
        time.sleep(PROPAGATION_WAIT)

        # Valid everywhere before logout
        for nid, stub in s["nodes"].items():
            resp = stub.DisplayItemsForSale(
                products_pb2.DisplayItemsRequest(session_id=session_id)
            )
            assert resp.success, f"Session not valid on node {nid} before logout"

        _write(
            s["nodes"],
            lambda stub: stub.Logout(products_pb2.LogoutRequest(session_id=session_id)),
        )
        time.sleep(PROPAGATION_WAIT)

        for nid, stub in s["nodes"].items():
            resp = stub.DisplayItemsForSale(
                products_pb2.DisplayItemsRequest(session_id=session_id)
            )
            assert not resp.success, f"Stale session still valid on node {nid}"


# ── TestItemConsistency ───────────────────────────────────────────────────────


class TestItemConsistency:
    def test_register_item_visible_on_all_nodes(self, registered_item):
        """Item committed via Raft must be retrievable on all nodes."""
        item_id = registered_item["item_id"]
        for nid, stub in registered_item["nodes"].items():
            resp = stub.GetItem(products_pb2.GetItemRequest(item_id=item_id))
            assert resp.success, f"GetItem failed on node {nid}: {resp.message}"
            assert resp.item.id == item_id

    def test_price_change_reflected_on_all_nodes(self, registered_item):
        """Price change committed via Raft must appear on every node."""
        s, item_id = registered_item, registered_item["item_id"]
        new_price = 42.00

        _, resp = _write(
            s["nodes"],
            lambda stub: stub.ChangeItemPrice(
                products_pb2.ChangeItemPriceRequest(
                    session_id=s["session_id"],
                    item_id=item_id,
                    new_price=new_price,
                )
            ),
        )
        assert resp.success, f"ChangeItemPrice failed: {resp.message}"
        time.sleep(PROPAGATION_WAIT)

        for nid, stub in s["nodes"].items():
            r = stub.GetItem(products_pb2.GetItemRequest(item_id=item_id))
            assert r.success
            assert abs(r.item.sale_price - new_price) < 0.01, (
                f"Price mismatch on node {nid}: expected {new_price}, got {r.item.sale_price}"
            )

    def test_quantity_update_reflected_on_all_nodes(self, registered_item):
        """UpdateUnitsForSale committed via Raft must appear on every node."""
        s, item_id = registered_item, registered_item["item_id"]

        _, resp = _write(
            s["nodes"],
            lambda stub: stub.UpdateUnitsForSale(
                products_pb2.UpdateUnitsRequest(
                    session_id=s["session_id"],
                    item_id=item_id,
                    new_quantity=99,
                )
            ),
        )
        assert resp.success, f"UpdateUnitsForSale failed: {resp.message}"
        time.sleep(PROPAGATION_WAIT)

        for nid, stub in s["nodes"].items():
            r = stub.GetItem(products_pb2.GetItemRequest(item_id=item_id))
            assert r.item.quantity == 99, (
                f"Quantity mismatch on node {nid}: expected 99, got {r.item.quantity}"
            )

    def test_search_cross_node(self, registered_item):
        """Item registered via leader must appear in search on all nodes."""
        s, category_id = registered_item, registered_item["category_id"]

        for nid, stub in s["nodes"].items():
            search = stub.SearchItemsForSale(
                products_pb2.SearchItemsRequest(
                    category_id=category_id,
                    keywords=["widget"],
                )
            )
            assert search.success
            assert registered_item["item_id"] in [i.id for i in search.items], (
                f"Item not found in search on node {nid}"
            )

    def test_sequential_price_changes_ordering(self, registered_item):
        """Three sequential writes must be applied in order; last value wins."""
        s, item_id = registered_item, registered_item["item_id"]

        for price in [10.00, 20.00, 30.00]:
            _, resp = _write(
                s["nodes"],
                lambda stub, p=price: stub.ChangeItemPrice(
                    products_pb2.ChangeItemPriceRequest(
                        session_id=s["session_id"],
                        item_id=item_id,
                        new_price=p,
                    )
                ),
            )
            assert resp.success

        time.sleep(PROPAGATION_WAIT)

        for nid, stub in s["nodes"].items():
            r = stub.GetItem(products_pb2.GetItemRequest(item_id=item_id))
            assert abs(r.item.sale_price - 30.00) < 0.01, (
                f"Final price wrong on node {nid}: got {r.item.sale_price}"
            )


# ── TestPurchaseConsistency ───────────────────────────────────────────────────


class TestPurchaseConsistency:
    def test_purchase_reduces_inventory_on_all_nodes(self, registered_item):
        """Purchase committed via Raft must reduce quantity on every node."""
        s, item_id = registered_item, registered_item["item_id"]

        _, resp = _write(
            s["nodes"],
            lambda stub: stub.MakePurchase(
                products_pb2.MakePurchaseRequest(
                    items=[products_pb2.ItemQuantity(item_id=item_id, quantity=3)],
                )
            ),
        )
        assert resp.success, f"MakePurchase failed: {resp.message}"
        time.sleep(PROPAGATION_WAIT)

        for nid, stub in s["nodes"].items():
            r = stub.GetItem(products_pb2.GetItemRequest(item_id=item_id))
            assert r.item.quantity == 7, (
                f"Wrong quantity on node {nid}: expected 7, got {r.item.quantity}"
            )

    def test_insufficient_stock_rejected(self, registered_item):
        """Purchasing more than available stock must fail."""
        s, item_id = registered_item, registered_item["item_id"]

        _, resp = _write(
            s["nodes"],
            lambda stub: stub.MakePurchase(
                products_pb2.MakePurchaseRequest(
                    items=[products_pb2.ItemQuantity(item_id=item_id, quantity=999)],
                )
            ),
        )
        assert not resp.success

    def test_concurrent_purchases_no_oversell(self, registered_item):
        """
        Two clients race to buy all 10 units via different nodes.
        Raft serialises them — exactly one must succeed; quantity ends at 0.
        """
        s, item_id = registered_item, registered_item["item_id"]
        results = []
        lock = threading.Lock()

        def buy(stub):
            try:
                resp = stub.MakePurchase(
                    products_pb2.MakePurchaseRequest(
                        items=[products_pb2.ItemQuantity(item_id=item_id, quantity=10)],
                    )
                )
                with lock:
                    results.append(resp.success if resp else False)
            except RpcError:
                with lock:
                    results.append(False)

        # Send to two different nodes simultaneously
        t0 = threading.Thread(target=buy, args=(s["nodes"][0],))
        t1 = threading.Thread(target=buy, args=(s["nodes"][1],))
        t0.start()
        t1.start()
        t0.join()
        t1.join()

        assert results.count(True) == 1, f"Expected exactly 1 success, got: {results}"
        time.sleep(PROPAGATION_WAIT)

        for nid, stub in s["nodes"].items():
            r = stub.GetItem(products_pb2.GetItemRequest(item_id=item_id))
            assert r.item.quantity == 0, (
                f"Quantity not zero on node {nid}: {r.item.quantity}"
            )


# ── TestConcurrentWrites ──────────────────────────────────────────────────────


class TestConcurrentWrites:
    def test_concurrent_item_registrations_consistent(self, registered_seller):
        """
        4 items submitted concurrently to different nodes.
        Raft must serialise them — all nodes end up with the same count.
        """
        s, nodes = registered_seller, registered_seller["nodes"]

        _, cat = _write(
            nodes,
            lambda stub: stub.GetCategoriesClient(
                products_pb2.GetCategoriesClientRequest()
            ),
        )
        category_id = cat.categories[0].id
        errors = []
        n_items = 4

        def submit(stub, count):
            for _ in range(count):
                try:
                    resp = stub.RegisterItemForSale(
                        products_pb2.RegisterItemRequest(
                            session_id=s["session_id"],
                            item_name=f"concurrent_{uid()}",
                            category_id=category_id,
                            keywords="concurrent",
                            condition="NEW",
                            price=1.00,
                            quantity=1,
                        )
                    )
                    if resp and not resp.success:
                        errors.append(resp.message)
                except RpcError as e:
                    errors.append(str(e))

        threads = [
            threading.Thread(target=submit, args=(nodes[i % len(nodes)], n_items // 4))
            for i in range(4)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Write errors: {errors}"
        time.sleep(PROPAGATION_WAIT * 2)

        counts = []
        for nid, stub in nodes.items():
            resp = stub.DisplayItemsForSale(
                products_pb2.DisplayItemsRequest(session_id=s["session_id"])
            )
            assert resp.success, f"DisplayItemsForSale failed on node {nid}"
            counts.append(len(resp.items))

        assert len(set(counts)) == 1, f"Item counts differ: {dict(enumerate(counts))}"
        assert counts[0] >= n_items, (
            f"Expected at least {n_items} items, got {counts[0]}"
        )

    def test_writes_from_all_five_nodes_consistent(self, registered_seller):
        """
        One item submitted from each of the 5 nodes concurrently.
        All nodes must converge on the same total.
        """
        s, nodes = registered_seller, registered_seller["nodes"]

        _, cat = _write(
            nodes,
            lambda stub: stub.GetCategoriesClient(
                products_pb2.GetCategoriesClientRequest()
            ),
        )
        category_id = cat.categories[0].id
        errors = []

        def submit_one(stub):
            try:
                resp = stub.RegisterItemForSale(
                    products_pb2.RegisterItemRequest(
                        session_id=s["session_id"],
                        item_name=f"five_{uid()}",
                        category_id=category_id,
                        keywords="five",
                        condition="NEW",
                        price=5.00,
                        quantity=1,
                    )
                )
                if resp and not resp.success:
                    errors.append(resp.message)
            except RpcError as e:
                errors.append(str(e))

        threads = [
            threading.Thread(target=submit_one, args=(nodes[i],)) for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Write errors: {errors}"
        time.sleep(PROPAGATION_WAIT * 2)

        counts = []
        for nid, stub in nodes.items():
            resp = stub.DisplayItemsForSale(
                products_pb2.DisplayItemsRequest(session_id=s["session_id"])
            )
            assert resp.success
            counts.append(len(resp.items))

        assert len(set(counts)) == 1, f"Item counts differ: {dict(enumerate(counts))}"
        assert counts[0] >= 5, f"Expected at least 5 items, got {counts[0]}"

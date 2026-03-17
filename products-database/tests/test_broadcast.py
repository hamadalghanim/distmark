"""
tests/test_broadcast.py — Integration tests for the atomic broadcast protocol
"""

import os
import time
import threading
import uuid

import grpc
import pytest

from proto import products_pb2
from proto import products_pb2_grpc


# ── Config ────────────────────────────────────────────────────────────────────

REPLICA_ADDRS = [
    os.environ.get("REPLICA0_ADDR", "localhost:5000"),
    os.environ.get("REPLICA1_ADDR", "localhost:5001"),
    os.environ.get("REPLICA2_ADDR", "localhost:5002"),
]

PROPAGATION_WAIT = 1.0  # seconds — time for a write to reach all replicas


def _make_stub(addr):
    return products_pb2_grpc.SellerServiceStub(grpc.insecure_channel(addr))


def uid():
    return uuid.uuid4().hex[:8]


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
    resp = stub.RegisterItemForSale(
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
    return resp


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def stubs():
    return {i: _make_stub(addr) for i, addr in enumerate(REPLICA_ADDRS)}


@pytest.fixture()
def registered_seller(stubs):
    username = f"seller_{uid()}"
    password = "pass123"

    resp = stubs[0].CreateAccount(
        products_pb2.CreateAccountRequest(
            name="Test Seller",
            username=username,
            password=password,
        )
    )
    assert resp.success, f"CreateAccount failed: {resp.message}"

    login = stubs[0].Login(
        products_pb2.LoginRequest(username=username, password=password)
    )
    assert login.success, f"Login failed: {login.message}"

    time.sleep(PROPAGATION_WAIT)
    return {
        "seller_id": resp.seller_id,
        "session_id": login.session_id,
        "username": username,
        "password": password,
        "stubs": stubs,
    }


@pytest.fixture()
def registered_item(registered_seller):
    s = registered_seller
    cat = s["stubs"][0].GetCategoriesClient(products_pb2.GetCategoriesClientRequest())
    assert cat.success and cat.categories
    category_id = cat.categories[0].id

    resp = _register_item(s["stubs"][0], s["session_id"], category_id)
    assert resp.success, f"RegisterItemForSale failed: {resp.message}"
    time.sleep(PROPAGATION_WAIT)
    return {**s, "item_id": resp.item_id, "category_id": category_id}


# ── TestAccountConsistency ────────────────────────────────────────────────────


class TestAccountConsistency:
    def test_create_account_visible_on_all_replicas(self, stubs):
        """Account created on replica 0 must be loginable on all three."""
        username, password = f"seller_{uid()}", "secret"
        resp = stubs[0].CreateAccount(
            products_pb2.CreateAccountRequest(
                name="Alice",
                username=username,
                password=password,
            )
        )
        assert resp.success, resp.message
        time.sleep(PROPAGATION_WAIT)

        for rid, stub in stubs.items():
            login = stub.Login(
                products_pb2.LoginRequest(username=username, password=password)
            )
            assert login.success, f"Login failed on replica {rid}: {login.message}"

    def test_duplicate_account_rejected_on_all_replicas(self, stubs):
        """Creating the same username twice must fail on every replica."""
        username, password = f"seller_{uid()}", "pass"
        stubs[0].CreateAccount(
            products_pb2.CreateAccountRequest(
                name="Bob",
                username=username,
                password=password,
            )
        )
        time.sleep(PROPAGATION_WAIT)

        for rid, stub in stubs.items():
            r2 = stub.CreateAccount(
                products_pb2.CreateAccountRequest(
                    name="Bob2",
                    username=username,
                    password=password,
                )
            )
            assert not r2.success, f"Duplicate account succeeded on replica {rid}"

    def test_account_created_on_replica1_visible_on_others(self, stubs):
        """Account created on replica 1 (not 0) must propagate to all."""
        username, password = f"seller_{uid()}", "pass"
        resp = stubs[1].CreateAccount(
            products_pb2.CreateAccountRequest(
                name="Carol",
                username=username,
                password=password,
            )
        )
        assert resp.success, resp.message
        time.sleep(PROPAGATION_WAIT)

        for rid, stub in stubs.items():
            login = stub.Login(
                products_pb2.LoginRequest(username=username, password=password)
            )
            assert login.success, f"Login failed on replica {rid}: {login.message}"

    def test_logout_reflected_on_all_replicas(self, registered_seller):
        """Session logged out on replica 0 must be invalid on all replicas."""
        s = registered_seller

        # Create a fresh login on replica 0 — broadcast ensures session exists everywhere.
        login = s["stubs"][0].Login(
            products_pb2.LoginRequest(
                username=s["username"],
                password=s["password"],
            )
        )
        assert login.success
        session_id = login.session_id
        time.sleep(PROPAGATION_WAIT)

        # Verify session is valid on all replicas before logging out.
        for rid, stub in s["stubs"].items():
            resp = stub.DisplayItemsForSale(
                products_pb2.DisplayItemsRequest(session_id=session_id)
            )
            assert resp.success, f"Session not valid on replica {rid} before logout"

        # Log out via replica 0.
        logout = s["stubs"][0].Logout(products_pb2.LogoutRequest(session_id=session_id))
        assert logout.success
        time.sleep(PROPAGATION_WAIT)

        # Session must now be invalid on all replicas.
        for rid, stub in s["stubs"].items():
            resp = stub.DisplayItemsForSale(
                products_pb2.DisplayItemsRequest(session_id=session_id)
            )
            assert not resp.success, f"Stale session still valid on replica {rid}"


# ── TestItemConsistency ───────────────────────────────────────────────────────


class TestItemConsistency:
    def test_register_item_visible_on_all_replicas(self, registered_item):
        """Item registered on replica 0 must be retrievable via GetItem on all."""
        item_id = registered_item["item_id"]
        for rid, stub in registered_item["stubs"].items():
            resp = stub.GetItem(products_pb2.GetItemRequest(item_id=item_id))
            assert resp.success, f"GetItem failed on replica {rid}: {resp.message}"
            assert resp.item.id == item_id

    def test_price_change_reflected_everywhere(self, registered_item):
        """Price change submitted to replica 2 must appear on replicas 0 and 1."""
        stubs, item_id, session_id = (
            registered_item["stubs"],
            registered_item["item_id"],
            registered_item["session_id"],
        )
        new_price = 42.00

        resp = stubs[2].ChangeItemPrice(
            products_pb2.ChangeItemPriceRequest(
                session_id=session_id,
                item_id=item_id,
                new_price=new_price,
            )
        )
        assert resp.success, f"ChangeItemPrice failed: {resp.message}"
        time.sleep(PROPAGATION_WAIT)

        for rid in [0, 1]:
            item_resp = stubs[rid].GetItem(products_pb2.GetItemRequest(item_id=item_id))
            assert item_resp.success
            assert abs(item_resp.item.sale_price - new_price) < 0.01, (
                f"Price mismatch on replica {rid}: expected {new_price}, got {item_resp.item.sale_price}"
            )

    def test_quantity_update_reflected_everywhere(self, registered_item):
        """UpdateUnitsForSale submitted to replica 1 must appear on all replicas."""
        stubs, item_id, session_id = (
            registered_item["stubs"],
            registered_item["item_id"],
            registered_item["session_id"],
        )

        resp = stubs[1].UpdateUnitsForSale(
            products_pb2.UpdateUnitsRequest(
                session_id=session_id,
                item_id=item_id,
                new_quantity=99,
            )
        )
        assert resp.success, f"UpdateUnitsForSale failed: {resp.message}"
        time.sleep(PROPAGATION_WAIT)

        for rid, stub in stubs.items():
            item_resp = stub.GetItem(products_pb2.GetItemRequest(item_id=item_id))
            assert item_resp.success
            assert item_resp.item.quantity == 99, (
                f"Quantity mismatch on replica {rid}: expected 99, got {item_resp.item.quantity}"
            )

    def test_register_and_search_cross_replica(self, registered_item):
        """Search on replicas 1 and 2 must find an item registered on replica 0."""
        stubs, category_id = registered_item["stubs"], registered_item["category_id"]

        for rid in [1, 2]:
            search = stubs[rid].SearchItemsForSale(
                products_pb2.SearchItemsRequest(
                    category_id=category_id,
                    keywords=["widget"],
                )
            )
            assert search.success
            assert registered_item["item_id"] in [i.id for i in search.items], (
                f"Item not found in search on replica {rid}"
            )

    def test_multiple_price_changes_ordering(self, registered_item):
        """Three sequential price changes must land in order on all replicas."""
        stubs, item_id, session_id = (
            registered_item["stubs"],
            registered_item["item_id"],
            registered_item["session_id"],
        )

        for price in [10.00, 20.00, 30.00]:
            resp = stubs[0].ChangeItemPrice(
                products_pb2.ChangeItemPriceRequest(
                    session_id=session_id,
                    item_id=item_id,
                    new_price=price,
                )
            )
            assert resp.success

        time.sleep(PROPAGATION_WAIT)

        # The last price (30.00) must be what everyone sees.
        for rid, stub in stubs.items():
            item_resp = stub.GetItem(products_pb2.GetItemRequest(item_id=item_id))
            assert item_resp.success
            assert abs(item_resp.item.sale_price - 30.00) < 0.01, (
                f"Final price wrong on replica {rid}: got {item_resp.item.sale_price}"
            )


# ── TestPurchaseConsistency ───────────────────────────────────────────────────


class TestPurchaseConsistency:
    def test_make_purchase_inventory_consistent(self, registered_item):
        """Purchase 3 units via replica 1; all replicas must show quantity = 7."""
        stubs, item_id = registered_item["stubs"], registered_item["item_id"]

        purchase = stubs[1].MakePurchase(
            products_pb2.MakePurchaseRequest(
                items=[products_pb2.ItemQuantity(item_id=item_id, quantity=3)],
            )
        )
        assert purchase.success, f"MakePurchase failed: {purchase.message}"
        time.sleep(PROPAGATION_WAIT)

        for rid, stub in stubs.items():
            resp = stub.GetItem(products_pb2.GetItemRequest(item_id=item_id))
            assert resp.success
            assert resp.item.quantity == 7, (
                f"Wrong quantity on replica {rid}: expected 7, got {resp.item.quantity}"
            )

    def test_insufficient_stock_rejected(self, registered_item):
        """Purchasing more than available must fail."""
        stubs, item_id = registered_item["stubs"], registered_item["item_id"]
        purchase = stubs[0].MakePurchase(
            products_pb2.MakePurchaseRequest(
                items=[products_pb2.ItemQuantity(item_id=item_id, quantity=999)],
            )
        )
        assert not purchase.success

    def test_concurrent_purchases_no_oversell(self, registered_item):
        """
        Two replicas simultaneously attempt to buy all 10 units.
        Exactly one should succeed; quantity must be 0, not negative.
        """
        stubs, item_id = registered_item["stubs"], registered_item["item_id"]
        results = []

        def buy(stub):
            resp = stub.MakePurchase(
                products_pb2.MakePurchaseRequest(
                    items=[products_pb2.ItemQuantity(item_id=item_id, quantity=10)],
                )
            )
            results.append(resp.success)

        t0 = threading.Thread(target=buy, args=(stubs[0],))
        t1 = threading.Thread(target=buy, args=(stubs[1],))
        t0.start()
        t1.start()
        t0.join()
        t1.join()

        assert results.count(True) == 1, f"Expected exactly 1 success, got: {results}"
        time.sleep(PROPAGATION_WAIT)

        for rid, stub in stubs.items():
            resp = stub.GetItem(products_pb2.GetItemRequest(item_id=item_id))
            assert resp.item.quantity == 0, (
                f"Quantity not zero after purchase on replica {rid}: {resp.item.quantity}"
            )


# ── TestConcurrentWrites ──────────────────────────────────────────────────────


class TestConcurrentWrites:
    def test_concurrent_writes_consistent_on_all_replicas(self, registered_seller):
        """
        Submit writes to replica 0 and replica 1 simultaneously.
        All replicas must end up with the same number of items.
        """
        s, stubs = registered_seller, registered_seller["stubs"]
        cat = stubs[0].GetCategoriesClient(products_pb2.GetCategoriesClientRequest())
        assert cat.success and cat.categories
        category_id = cat.categories[0].id

        errors = []
        n_items = 4

        def submit_items(stub, count):
            for _ in range(count):
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
                if not resp.success:
                    errors.append(resp.message)

        t0 = threading.Thread(target=submit_items, args=(stubs[0], n_items // 2))
        t1 = threading.Thread(target=submit_items, args=(stubs[1], n_items // 2))
        t0.start()
        t1.start()
        t0.join()
        t1.join()

        assert not errors, f"Write errors: {errors}"
        time.sleep(PROPAGATION_WAIT * 2)

        counts = []
        for rid, stub in stubs.items():
            resp = stub.DisplayItemsForSale(
                products_pb2.DisplayItemsRequest(session_id=s["session_id"])
            )
            assert resp.success, f"DisplayItemsForSale failed on replica {rid}"
            counts.append(len(resp.items))

        assert len(set(counts)) == 1, f"Item counts differ: {dict(enumerate(counts))}"
        assert counts[0] >= n_items, (
            f"Expected at least {n_items} items, got {counts[0]}"
        )

    def test_writes_to_all_three_replicas_consistent(self, registered_seller):
        """
        Submit one item to each of the three replicas concurrently.
        All replicas must converge on the same total count.
        """
        s, stubs = registered_seller, registered_seller["stubs"]
        cat = stubs[0].GetCategoriesClient(products_pb2.GetCategoriesClientRequest())
        category_id = cat.categories[0].id

        errors = []

        def submit_one(stub):
            resp = stub.RegisterItemForSale(
                products_pb2.RegisterItemRequest(
                    session_id=s["session_id"],
                    item_name=f"triple_{uid()}",
                    category_id=category_id,
                    keywords="triple",
                    condition="NEW",
                    price=5.00,
                    quantity=1,
                )
            )
            if not resp.success:
                errors.append(resp.message)

        threads = [
            threading.Thread(target=submit_one, args=(stubs[i],)) for i in range(3)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Write errors: {errors}"
        time.sleep(PROPAGATION_WAIT * 2)

        counts = []
        for rid, stub in stubs.items():
            resp = stub.DisplayItemsForSale(
                products_pb2.DisplayItemsRequest(session_id=s["session_id"])
            )
            assert resp.success
            counts.append(len(resp.items))

        assert len(set(counts)) == 1, f"Item counts differ: {dict(enumerate(counts))}"
        assert counts[0] >= 3, f"Expected at least 3 items, got {counts[0]}"

"""
tests/test_broadcast.py — Integration tests for the atomic broadcast protocol

Each test connects to replicas via gRPC (using addresses from env vars) and
verifies that writes submitted to different replicas are reflected consistently
on all replicas, demonstrating correct global ordering.

Test structure
──────────────
  Fixtures:
    stubs       — dict of {0: stub, 1: stub, 2: stub} (one per replica)
    unique_user — factory for unique usernames to avoid cross-test collisions

  Tests:
    test_create_account_visible_on_all_replicas
        Submit CreateAccount to replica 0; verify the seller appears on all 3.

    test_concurrent_writes_consistent_ordering
        Submit writes to replica 0 and replica 1 simultaneously; verify the
        final item list is the same length on all replicas.

    test_register_and_search_cross_replica
        Register an item on replica 0; search for it on replica 1 and 2.

    test_make_purchase_inventory_consistent
        Register an item with quantity 10 on replica 0; purchase 3 units via
        replica 1; verify remaining quantity is 7 on all replicas.

    test_price_change_reflected_everywhere
        Change an item's price on replica 2; verify the updated price is
        returned by GetItem on replica 0 and 1.
"""

import os
import time
import threading
import uuid

import grpc
import pytest

from proto import products_pb2
from proto import products_pb2_grpc


# ── Helpers ───────────────────────────────────────────────────────────────────

REPLICA_ADDRS = [
    os.environ.get("REPLICA0_ADDR", "localhost:5000"),
    os.environ.get("REPLICA1_ADDR", "localhost:5001"),
    os.environ.get("REPLICA2_ADDR", "localhost:5002"),
]

# How long to wait for a write to propagate to all replicas after it returns.
# Atomic broadcast guarantees ordering but network latency is real.
PROPAGATION_WAIT = 1.0  # seconds


def _make_stub(addr: str) -> products_pb2_grpc.SellerServiceStub:
    channel = grpc.insecure_channel(addr)
    return products_pb2_grpc.SellerServiceStub(channel)


def uid() -> str:
    """Return a short unique string safe for use in usernames."""
    return uuid.uuid4().hex[:8]


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def stubs() -> dict[int, products_pb2_grpc.SellerServiceStub]:
    return {i: _make_stub(addr) for i, addr in enumerate(REPLICA_ADDRS)}


@pytest.fixture()
def registered_seller(stubs):
    """
    Create a fresh seller account via replica 0 and return
    (seller_id, session_id, username, password, stubs).
    """
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
        products_pb2.LoginRequest(
            username=username,
            password=password,
        )
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
    """
    Register a single item via replica 0 and return the seller context
    plus item_id.
    """
    s = registered_seller
    cat = s["stubs"][0].GetCategoriesClient(products_pb2.GetCategoriesClientRequest())
    assert cat.success and cat.categories
    category_id = cat.categories[0].id

    resp = s["stubs"][0].RegisterItemForSale(
        products_pb2.RegisterItemRequest(
            session_id=s["session_id"],
            item_name=f"item_{uid()}",
            category_id=category_id,
            keywords="test widget",
            condition="NEW",
            price=9.99,
            quantity=10,
        )
    )
    assert resp.success, f"RegisterItemForSale failed: {resp.message}"
    time.sleep(PROPAGATION_WAIT)
    return {**s, "item_id": resp.item_id, "category_id": category_id}


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestAccountConsistency:
    def test_create_account_visible_on_all_replicas(self, stubs):
        """
        A seller created on replica 0 must be loginable on all three replicas.
        """
        username = f"seller_{uid()}"
        password = "secret"

        resp = stubs[0].CreateAccount(
            products_pb2.CreateAccountRequest(
                name="Alice",
                username=username,
                password=password,
            )
        )
        assert resp.success, resp.message

        time.sleep(PROPAGATION_WAIT)

        for replica_id, stub in stubs.items():
            login = stub.Login(
                products_pb2.LoginRequest(
                    username=username,
                    password=password,
                )
            )
            assert login.success, (
                f"Login failed on replica {replica_id} after create on replica 0: "
                f"{login.message}"
            )

    def test_duplicate_account_rejected_consistently(self, stubs):
        """
        Creating the same username twice must fail on all replicas.
        """
        username = f"seller_{uid()}"
        password = "pass"

        r1 = stubs[0].CreateAccount(
            products_pb2.CreateAccountRequest(
                name="Bob",
                username=username,
                password=password,
            )
        )
        assert r1.success

        time.sleep(PROPAGATION_WAIT)

        # Try to create the same account on each replica — all must fail.
        for replica_id, stub in stubs.items():
            r2 = stub.CreateAccount(
                products_pb2.CreateAccountRequest(
                    name="Bob2",
                    username=username,
                    password=password,
                )
            )
            assert not r2.success, (
                f"Duplicate CreateAccount succeeded on replica {replica_id}"
            )


class TestItemConsistency:
    def test_register_item_visible_on_all_replicas(self, registered_item):
        """
        An item registered on replica 0 must be retrievable via GetItem on all.
        """
        item_id = registered_item["item_id"]
        stubs = registered_item["stubs"]

        for replica_id, stub in stubs.items():
            resp = stub.GetItem(products_pb2.GetItemRequest(item_id=item_id))
            assert resp.success, (
                f"GetItem failed on replica {replica_id}: {resp.message}"
            )
            assert resp.item.id == item_id

    def test_price_change_reflected_everywhere(self, registered_item):
        """
        A price change submitted to replica 2 must appear on replicas 0 and 1.
        """
        stubs = registered_item["stubs"]
        item_id = registered_item["item_id"]
        new_price = 42.00

        resp = stubs[2].ChangeItemPrice(
            products_pb2.ChangeItemPriceRequest(
                session_id=registered_item["session_id"],
                item_id=item_id,
                new_price=new_price,
            )
        )
        assert resp.success, f"ChangeItemPrice failed: {resp.message}"

        time.sleep(PROPAGATION_WAIT)

        for replica_id in [0, 1]:
            item_resp = stubs[replica_id].GetItem(
                products_pb2.GetItemRequest(item_id=item_id)
            )
            assert item_resp.success
            assert abs(item_resp.item.sale_price - new_price) < 0.01, (
                f"Price mismatch on replica {replica_id}: "
                f"expected {new_price}, got {item_resp.item.sale_price}"
            )

    def test_register_and_search_cross_replica(self, registered_item):
        """
        Search on replicas 1 and 2 must find an item registered on replica 0.
        """
        stubs = registered_item["stubs"]
        category_id = registered_item["category_id"]

        for replica_id in [1, 2]:
            search = stubs[replica_id].SearchItemsForSale(
                products_pb2.SearchItemsRequest(
                    category_id=category_id,
                    keywords=["widget"],
                )
            )
            assert search.success
            found_ids = [i.id for i in search.items]
            assert registered_item["item_id"] in found_ids, (
                f"Item not found in search on replica {replica_id}"
            )


class TestPurchaseConsistency:
    def test_make_purchase_inventory_consistent(self, registered_item):
        """
        Purchase 3 units via replica 1; all replicas must show quantity = 7.
        """
        stubs = registered_item["stubs"]
        item_id = registered_item["item_id"]

        purchase = stubs[1].MakePurchase(
            products_pb2.MakePurchaseRequest(
                items=[products_pb2.ItemQuantity(item_id=item_id, quantity=3)],
            )
        )
        assert purchase.success, f"MakePurchase failed: {purchase.message}"

        time.sleep(PROPAGATION_WAIT)

        for replica_id, stub in stubs.items():
            resp = stub.GetItem(products_pb2.GetItemRequest(item_id=item_id))
            assert resp.success
            assert resp.item.quantity == 7, (
                f"Wrong quantity on replica {replica_id}: "
                f"expected 7, got {resp.item.quantity}"
            )

    def test_insufficient_stock_rejected(self, registered_item):
        """
        Purchasing more than available quantity must fail.
        """
        stubs = registered_item["stubs"]
        item_id = registered_item["item_id"]

        purchase = stubs[0].MakePurchase(
            products_pb2.MakePurchaseRequest(
                items=[products_pb2.ItemQuantity(item_id=item_id, quantity=999)],
            )
        )
        assert not purchase.success


class TestConcurrentWrites:
    def test_concurrent_writes_consistent_on_all_replicas(self, registered_seller):
        """
        Submit writes to replica 0 and replica 1 simultaneously.
        All replicas must end up with the same number of items for this seller.
        """
        s = registered_seller
        stubs = s["stubs"]

        cat = stubs[0].GetCategoriesClient(products_pb2.GetCategoriesClientRequest())
        assert cat.success and cat.categories
        category_id = cat.categories[0].id

        errors = []
        n_items = 4  # 2 submitted per replica

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

        # Give the broadcast time to propagate and deliver everywhere.
        time.sleep(PROPAGATION_WAIT * 2)

        counts = []
        for replica_id, stub in stubs.items():
            resp = stub.DisplayItemsForSale(
                products_pb2.DisplayItemsRequest(
                    session_id=s["session_id"],
                )
            )
            assert resp.success, f"DisplayItemsForSale failed on replica {replica_id}"
            counts.append(len(resp.items))

        assert len(set(counts)) == 1, (
            f"Item counts differ across replicas: {dict(enumerate(counts))}"
        )
        assert counts[0] >= n_items, (
            f"Expected at least {n_items} items, got {counts[0]}"
        )

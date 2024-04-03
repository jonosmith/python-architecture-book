from datetime import date, timedelta

import pytest

from src.allocation.adapters import repository
from src.allocation.domain import model
from src.allocation.service_layer import services, unit_of_work

today = date.today()
tomorrow = date.today() + timedelta(days=1.0)
later = date.today() + timedelta(days=10.0)


class FakeRepository(repository.AbstractProductRepository):
    def __init__(self, products: list[model.Product]):
        self._products = set(products)

    def add(self, product: model.Product) -> None:
        self._products.add(product)

    def delete(self, product: model.Product) -> None:
        self._products.remove(product)

    def get(self, sku: str) -> model.Product | None:
        try:
            return next(p for p in self._products if p.sku == sku)
        except StopIteration:
            return None

    def list(self) -> list[model.Product]:
        return list(self._products)


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def __enter__(self):
        # Testing fake - no op required
        pass

    def commit(self):
        self.committed = True

    def rollback(self):
        # Testing fake - no op required
        pass


def test_add_batch_for_new_product():
    uow = FakeUnitOfWork()

    services.add_batch("b1", "CRUNCHY-ARMCHAIR", qty=100, eta=None, uow=uow)

    assert uow.products.get("CRUNCHY-ARMCHAIR") is not None
    assert uow.committed


def test_add_batch_for_existing_product():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "GARISH-RUG", 100, None, uow)
    services.add_batch("b2", "GARISH-RUG", 99, None, uow)
    retrieved_product = uow.products.get("GARISH-RUG")
    retrieved_product_batches: list[model.Batch] = retrieved_product.batches if retrieved_product else []
    assert "b2" in [b.reference for b in retrieved_product_batches]


def test_allocate_returns_allocation():
    uow = FakeUnitOfWork()
    services.add_batch("batch1", "COMPLICATED-LAMP", 100, None, uow)
    result = services.allocate("o1", "COMPLICATED-LAMP", 10, uow)
    assert result == "batch1"


def test_remove_batch():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "CRUNCHY-ARMCHAIR", qty=100, eta=None, uow=uow)
    retrieved_product = uow.products.get("CRUNCHY-ARMCHAIR")
    retrieved_product_batches: list[model.Batch] = retrieved_product.batches if retrieved_product else []

    retrieved_batch = next(b for b in retrieved_product_batches if b.reference == "b1")
    assert retrieved_batch is not None

    services.delete_batch(ref="b1", sku="CRUNCHY-ARMCHAIR", uow=uow)

    retrieved_product = uow.products.get("CRUNCHY-ARMCHAIR")
    assert retrieved_product.batches == []


def test_allocate_errors_for_invalid_sku():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "AREALSKU", qty=100, eta=None, uow=uow)

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, uow)


def test_allocate_commits():
    uow = FakeUnitOfWork()

    services.add_batch("b1", sku="OMINOUS-MIRROR", qty=100, eta=None, uow=uow)
    services.allocate("o1", sku="OMINOUS-MIRROR", qty=10, uow=uow)

    assert uow.committed


# Service layer version of test_allocate.py:test_prefers_current_stock_batches_to_shipments()
def test_prefers_current_stock_batches_to_shipments():
    uow = FakeUnitOfWork()

    services.add_batch("in-stock-batch", sku="RETRO-CLOCK", qty=100, eta=None, uow=uow)
    services.add_batch("shipment-batch", sku="RETRO-CLOCK", qty=100, eta=tomorrow, uow=uow)

    services.allocate("oref", "RETRO-CLOCK", qty=10, uow=uow)

    retrieved_product = uow.products.get("RETRO-CLOCK")
    retrieved_product_batches: list[model.Batch] = retrieved_product.batches if retrieved_product else []

    in_stock_batch = next(b for b in retrieved_product_batches if b.reference == "in-stock-batch")
    shipment_batch = next(b for b in retrieved_product_batches if b.reference == "shipment-batch")
    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100

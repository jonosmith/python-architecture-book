from datetime import date, timedelta

import pytest

from src.allocation.adapters import repository
from src.allocation.service_layer import services, unit_of_work

today = date.today()
tomorrow = date.today() + timedelta(days=1.0)
later = date.today() + timedelta(days=10.0)


class FakeRepository(repository.AbstractRepository):
    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def delete(self, batch):
        self._batches.remove(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.batches = FakeRepository([])
        self.committed = False

    def __enter__(self):
        # Testing fake - no op required
        pass

    def commit(self):
        self.committed = True

    def rollback(self):
        # Testing fake - no op required
        pass


def test_allocate_returns_allocation():
    uow = FakeUnitOfWork()
    services.add_batch("batch1", "COMPLICATED-LAMP", qty=100, eta=None, uow=uow)

    result = services.allocate("o1", "COMPLICATED-LAMP", 10, uow)

    assert result == "batch1"


def test_allocate_errors_for_invalid_sku():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "AREALSKU", qty=100, eta=None, uow=uow)

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, uow)


def test_commits():
    uow = FakeUnitOfWork()
    services.add_batch("b1", sku="OMINOUS-MIRROR", qty=100, eta=None, uow=uow)

    services.allocate("o1", "OMINOUS-MIRROR", qty=10, uow=uow)

    assert uow.committed is True


# Service layer version of test_allocate.py:test_prefers_current_stock_batches_to_shipments()
def test_prefers_current_stock_batches_to_shipments():
    uow = FakeUnitOfWork()

    services.add_batch("in-stock-batch", sku="RETRO-CLOCK", qty=100, eta=None, uow=uow)
    services.add_batch("shipment-batch", sku="RETRO-CLOCK", qty=100, eta=tomorrow, uow=uow)

    services.allocate("oref", "RETRO-CLOCK", qty=10, uow=uow)

    assert uow.batches.get("in-stock-batch").available_quantity == 90
    assert uow.batches.get("shipment-batch").available_quantity == 100


def test_add_batch():
    uow = FakeUnitOfWork()

    services.add_batch("b1", "CRUNCHY-ARMCHAIR", qty=100, eta=None, uow=uow)

    assert uow.batches.get("b1") is not None
    assert uow.committed


def test_remove_batch():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "CRUNCHY-ARMCHAIR", qty=100, eta=None, uow=uow)
    assert uow.batches.get("b1") is not None

    services.delete_batch("b1", uow=uow)

    with pytest.raises(StopIteration):
        uow.batches.get("b1")

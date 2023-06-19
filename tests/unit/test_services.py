from datetime import date, timedelta

import pytest

from src.allocation.adapters import repository
from src.allocation.service_layer import services

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


def test_allocate_returns_allocation():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("batch1", "COMPLICATED-LAMP", 100, None, repo, session)

    result = services.allocate("o1", "COMPLICATED-LAMP", 10, repo, session)
    assert result == "batch1"


def test_allocate_errors_for_invalid_sku():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "AREALSKU", 100, None, repo, session)

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, repo, FakeSession())


def test_commits():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", sku="OMINOUS-MIRROR", qty=100, eta=None, repo=repo, session=session)

    services.allocate("o1", "OMINOUS-MIRROR", 10, repo, session)

    assert session.committed is True


# Service layer version of test_allocate.py:test_prefers_current_stock_batches_to_shipments()
def test_prefers_current_stock_batches_to_shipments():
    repo, session = FakeRepository([]), FakeSession()

    services.add_batch("in-stock-batch", sku="RETRO-CLOCK", qty=100, eta=None, repo=repo, session=session)
    services.add_batch("shipment-batch", sku="RETRO-CLOCK", qty=100, eta=tomorrow, repo=repo, session=session)

    services.allocate("oref", "RETRO-CLOCK", qty=10, repo=repo, session=session)

    assert repo.get("in-stock-batch").available_quantity == 90
    assert repo.get("shipment-batch").available_quantity == 100


def test_add_batch():
    repo, session = FakeRepository([]), FakeSession()

    services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, repo, session)

    assert repo.get("b1") is not None
    assert session.committed


def test_remove_batch():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "CRUNCHY-ARMCHAIR", qty=100, eta=None, repo=repo, session=session)
    assert repo.get("b1") is not None

    services.delete_batch("b1", repo, session)

    with pytest.raises(StopIteration):
        repo.get("b1")

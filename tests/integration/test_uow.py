import datetime

import pytest
from sqlalchemy.orm import Session

from src.allocation.domain import model
from src.allocation.service_layer import unit_of_work


# Helpers

def insert_batch(session: Session, ref: str, sku: str, qty: int, eta: datetime.datetime | None):
    session.execute(
        "INSERT INTO products (sku) VALUES (:sku)",
        dict(sku=sku)
    )
    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
        " VALUES (:ref, :sku, :qty, :eta)",
        dict(ref=ref, sku=sku, qty=qty, eta=eta)
    )


def get_allocated_batch_ref(session: Session, orderid: str, sku: str) -> str:
    [[orderline_id]] = session.execute(
        "SELECT id from order_lines WHERE orderid=:orderid AND sku=:sku",
        dict(orderid=orderid, sku=sku)
    )
    [[batchref]] = session.execute(
        "SELECT b.reference FROM allocations JOIN batches b on allocations.batch_id = b.id"
        " WHERE orderline_id=:orderline_id",
        dict(orderline_id=orderline_id)
    )
    return batchref


# Tests

def test_uow_can_retrieve_a_batch_and_allocate_to_it(session_factory):
    session = session_factory()
    insert_batch(session, "batch1", "HIPSTER-WORKBENCH", 100, None)
    session.commit()

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        retrieved_product = uow.products.get(sku="HIPSTER-WORKBENCH")
        assert retrieved_product is not None

        line = model.OrderLine("o1", "HIPSTER-WORKBENCH", 10)
        retrieved_product.allocate(line)
        uow.commit()

    batchref = get_allocated_batch_ref(session, "o1", "HIPSTER-WORKBENCH")
    assert batchref == "batch1"


def test_rolls_back_uncommitted_work_by_default(session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    with uow:
        insert_batch(session=uow.session, ref="batch1", sku="MEDIUM-PLINTH", qty=100, eta=None)

    new_session = session_factory()
    rows = list(new_session.execute("SELECT * FROM batches"))
    assert rows == []


def test_rolls_back_on_error(session_factory):
    class MyException(Exception):
        pass

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with pytest.raises(MyException):
        with uow:
            insert_batch(uow.session, ref="batch1", sku="LARGE-FORK", qty=100, eta=None)
            raise MyException()

    new_session = session_factory()
    rows = list(new_session.execute("SELECT * FROM batches"))
    assert rows == []

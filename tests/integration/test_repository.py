from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.allocation.adapters import repository
from src.allocation.domain import model


def insert_order_line(session: Session) -> int:
    session.execute(
        "INSERT INTO order_lines (orderid, sku, qty) VALUES "
        '("order1", "GENERIC-SOFA", 12)'
    )

    [[orderline_id]] = session.execute(
        "SELECT id from order_lines WHERE orderid=:orderid AND sku=:sku",
        dict(orderid="order1", sku="GENERIC-SOFA")
    )

    return orderline_id


def insert_product(session: Session):
    session.execute(
        'INSERT INTO products (sku) VALUES ("GENERIC-SOFA")'
    )


def insert_batch(session: Session, ref: str) -> int:
    tomorrow = date.today() + timedelta(days=1.0)

    [[batch_id]] = session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta) VALUES (:reference, :sku, :qty, :eta) RETURNING id",
        dict(reference=ref, sku="GENERIC-SOFA", qty=100, eta=tomorrow)
    )

    return batch_id


def insert_allocation(session: Session, orderline_id, batch_id) -> None:
    session.execute(
        "INSERT INTO allocations (orderline_id, batch_id) VALUES(:orderline_id, :batch_id)",
        dict(batch_id=batch_id, orderline_id=orderline_id)
    )


def test_repository_can_save_a_product(session: Session):
    batch = model.Batch("batch1", "RUSTY-SOAPDISH", 100, eta=None)
    product = model.Product(sku="RUSTY-SOAPDISH", batches=[batch])

    repo = repository.SqlAlchemyRepository(session)
    repo.add(product)
    session.commit()

    rows = list(session.execute(text("SELECT reference, sku, _purchased_quantity, eta FROM batches")))
    assert rows == [("batch1", "RUSTY-SOAPDISH", 100, None)]


def test_repository_can_retrieve_a_product_with_batches_and_allocations(session: Session):
    orderline_id = insert_order_line(session)
    batch1_id = insert_batch(session, "batch1")
    insert_product(session)
    insert_batch(session, "batch2")
    insert_allocation(session, orderline_id, batch1_id)
    repo = repository.SqlAlchemyRepository(session)

    retrieved_product = repo.get("GENERIC-SOFA")

    expected_product = model.Product("GENERIC-SOFA", [
        model.Batch("batch1", "GENERIC-SOFA", 100, eta=None)
    ])
    expected_product.allocate(model.OrderLine(orderid="order1", sku="GENERIC-SOFA", qty=12))

    assert retrieved_product == expected_product
    assert retrieved_product.batches[0]._purchased_quantity == expected_product.batches[0]._purchased_quantity
    assert retrieved_product.batches[0]._allocations == {
        model.OrderLine("order1", "GENERIC-SOFA", 12)
    }

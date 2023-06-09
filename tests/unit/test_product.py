from datetime import date, timedelta

import pytest

from src.allocation.domain.model import Batch, OrderLine, OutOfStock, Product

today = date.today()
tomorrow = date.today() + timedelta(days=1.0)
later = date.today() + timedelta(days=10.0)


def test_prefers_warehouse_batches_to_shipments():
    in_stock_batch = Batch("in-stock-batch", "RETRO-CLOCK", qty=100, eta=None)
    shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", qty=100, eta=tomorrow)
    product = Product(sku="RETRO-CLOCK", batches=[in_stock_batch, shipment_batch])
    line = OrderLine("oref", "RETRO-CLOCK", 10)

    product.allocate(line)

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_prefers_earlier_batches():
    earliest = Batch("speedy-batch", "MINIMALIST-SPOON", qty=100, eta=today)
    medium = Batch("normal-batch", "MINIMALIST-SPOON", qty=100, eta=tomorrow)
    latest = Batch("slow-batch", "MINIMALIST-SPOON", qty=100, eta=later)
    product = Product(sku="MINIMALIST-SPOON", batches=[earliest, medium, latest])
    line = OrderLine("order1", "MINIMALIST-SPOON", 10)

    product.allocate(line)

    assert earliest.available_quantity == 90
    assert medium.available_quantity == 100
    assert latest.available_quantity == 100


def test_returns_allocated_batch_ref():
    in_stock_batch = Batch("in-stock-batch-ref", "HIGHBROW-POSTER", 100, eta=None)
    shipment_batch = Batch("shipment-batch-ref", "HIGHBROW-POSTER", 100, eta=tomorrow)
    product = Product(sku="HIGHBROW-POSTER", batches=[in_stock_batch, shipment_batch])
    line = OrderLine("oref", "HIGHBROW-POSTER", 10)

    allocation = product.allocate(line)

    assert allocation == in_stock_batch.reference


def test_raises_out_of_stock_exception_if_cannot_allocate():
    batch = Batch("batch1", "SMALL-FORK", 10, eta=today)
    product = Product(sku="SMALL-FORK", batches=[batch])

    product.allocate(OrderLine("order1", "SMALL-FORK", 10))

    with pytest.raises(OutOfStock, match="SMALL-FORK"):
        product.allocate(OrderLine("order2", "SMALL-FORK", 1))

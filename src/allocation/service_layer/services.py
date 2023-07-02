from datetime import date
from typing import Optional

from src.allocation.domain import model
from src.allocation.service_layer import unit_of_work


class InvalidSku(Exception):
    pass


class BatchNotFound(Exception):
    pass


def is_valid_sku(sku: str, batches: list[model.Batch]):
    return sku in {b.sku for b in batches}


def add_batch(ref: str, sku: str, qty: int, eta: Optional[date], uow: unit_of_work.AbstractUnitOfWork) -> None:
    with uow:
        product = uow.products.get(sku=sku)
        if product is None:
            product = model.Product(sku, batches=[])
            uow.products.add(product)

        product.batches.append(model.Batch(ref=ref, sku=sku, qty=qty, eta=eta))

        uow.commit()


def delete_batch(ref: str, sku: str, uow: unit_of_work.AbstractUnitOfWork) -> None:
    """
    :raises InvalidSku
    :raises BatchNotFound
    """

    with uow:
        product = uow.products.get(sku=sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {sku}")

        try:
            next(b for b in product.batches if b.reference == ref)
        except StopIteration:
            raise BatchNotFound(f"Batch {ref} not found")

        product.batches = [b for b in product.batches if b.reference is not ref]

        uow.commit()


def allocate(orderid: str, sku: str, qty: int, uow: unit_of_work.AbstractUnitOfWork) -> str:
    """
    :raises InvalidSku
    """

    line = model.OrderLine(orderid, sku, qty)
    with uow:
        product = uow.products.get(sku=line.sku)

        if product is None:
            raise InvalidSku(f"Invalid sku {sku}")

        batchref = product.allocate(line)
        uow.commit()

    return batchref

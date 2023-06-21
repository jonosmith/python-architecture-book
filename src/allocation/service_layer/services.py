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
        uow.batches.add(model.Batch(ref, sku, qty, eta))
        uow.commit()


def delete_batch(ref: str, uow: unit_of_work.AbstractUnitOfWork) -> None:
    with uow:
        batch = uow.batches.get(ref)

        if not batch:
            raise BatchNotFound(f"Batch {ref} not found")

        uow.batches.delete(batch)

        uow.commit()


def allocate(orderid: str, sku: str, qty: int, uow: unit_of_work.AbstractUnitOfWork) -> str:
    with uow:
        batches = uow.batches.list()

        if not is_valid_sku(sku, batches):
            raise InvalidSku(f"Invalid sku {sku}")

        batchref = model.allocate(model.OrderLine(orderid, sku, qty), batches)
        uow.commit()

        return batchref

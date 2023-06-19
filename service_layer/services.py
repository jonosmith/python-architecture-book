from datetime import date
from typing import Optional

from adapters.repository import AbstractRepository
from domain import model


class InvalidSku(Exception):
    pass


class BatchNotFound(Exception):
    pass


def is_valid_sku(sku: str, batches: list[model.Batch]):
    return sku in {b.sku for b in batches}


def add_batch(ref: str, sku: str, qty: int, eta: Optional[date], repo: AbstractRepository, session) -> None:
    repo.add(model.Batch(ref, sku, qty, eta))
    session.commit()


def delete_batch(ref: str, repo: AbstractRepository, session) -> None:
    batch = repo.get(ref)

    if not batch:
        raise BatchNotFound(f"Batch {ref} not found")

    repo.delete(batch)

    session.commit()


def allocate(orderid: str, sku: str, qty: int, repo: AbstractRepository, session) -> str:
    batches = repo.list()

    if not is_valid_sku(sku, batches):
        raise InvalidSku(f"Invalid sku {sku}")

    batchref = model.allocate(model.OrderLine(orderid, sku, qty), batches)
    session.commit()

    return batchref

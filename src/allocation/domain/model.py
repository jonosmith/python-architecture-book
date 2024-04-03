from dataclasses import dataclass
from datetime import date
from typing import Optional, Set, Self, Any


class OutOfStock(Exception):
    pass


@dataclass(unsafe_hash=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int


class Batch:
    def __init__(self, ref: str, sku: str, qty: int, eta: Optional[date]):
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations: Set[OrderLine] = set()

    def __eq__(self, other: Any):
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    def __lt__(self, other: Self) -> bool:
        if self.eta is None:
            return True
        if other.eta is None:
            return False

        return self.eta < other.eta

    def __hash__(self):
        return hash(self.reference)

    @property
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        is_same_sku = self.sku == line.sku
        has_enough_quantity = self.available_quantity >= line.qty
        return is_same_sku and has_enough_quantity

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine):
        if line in self._allocations:
            self._allocations.remove(line)


class Product:
    """
    Aggregate root
    """

    def __init__(self, sku: str, batches: list[Batch]):
        self.sku = sku
        self.batches = batches

    def __eq__(self, other: Any):
        if not isinstance(other, Product):
            return False
        return other.sku == self.sku

    def __hash__(self):
        return hash(self.sku)

    def allocate(self, line: OrderLine) -> str:
        try:
            batch = next(
                b for b in sorted(self.batches) if b.can_allocate(line)
            )
            batch.allocate(line)
            return batch.reference
        except StopIteration:
            raise OutOfStock(f"Out of stock for sku {line.sku}")

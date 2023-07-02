import abc

from sqlalchemy.orm import Session

from src.allocation.domain import model


class AbstractProductRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, product: model.Product) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, product: model.Product) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, sku: str) -> model.Product | None:
        raise NotImplementedError

    @abc.abstractmethod
    def list(self) -> list[model.Product]:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractProductRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, product: model.Product):
        self.session.add(product)

    def delete(self, product: model.Product):
        self.session.delete(product)

    def get(self, sku: str) -> model.Product | None:
        return self.session.query(model.Product).filter_by(sku=sku).first()

    def list(self) -> list[model.Product]:
        return self.session.query(model.Product).all()

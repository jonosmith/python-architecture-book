import abc

from sqlalchemy.orm import Session

from allocations import model


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch: model.Batch):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference: str) -> model.Batch:
        raise NotImplementedError

    @abc.abstractmethod
    def list(self) -> list[model.Batch]:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, batch: model.Batch):
        self.session.add(batch)

    def get(self, reference: str) -> model.Batch:
        return self.session.query(model.Batch).filter_by(reference=reference).one()

    def list(self) -> list[model.Batch]:
        return self.session.query(model.Batch).all()


class FakeRepository(AbstractRepository):

    def __init__(self, batches: list[model.Batch] | set[model.Batch]):
        self._batches = set(batches)

    def add(self, batch: model.Batch):
        self._batches.add(batch)

    def get(self, reference: str) -> model.Batch:
        return next(b for b in self._batches if b.reference == reference)

    def list(self) -> list[model.Batch]:
        return list(self._batches)

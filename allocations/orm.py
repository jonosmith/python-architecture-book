import logging

from sqlalchemy import MetaData, Column, Table, Integer, String, Date, ForeignKey
from sqlalchemy.ext.instrumentation import InstrumentationManager
from sqlalchemy.orm import mapper, relationship

from allocations import model
from allocations.model import OrderLine

logger = logging.getLogger(__name__)

metadata = MetaData()

orderline_table = Table(
    "order_lines",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("sku", String(255)),
    Column("qty", Integer, nullable=False),
    Column("orderid", String(255)),
)

batch_table = Table(
    "batches",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("reference", String(255)),
    Column("sku", String(255)),
    Column("_purchased_quantity", Integer),
    Column("eta", Date)
)

allocations_table = Table(
    "allocations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("orderline_id", ForeignKey("order_lines.id")),
    Column("batch_id", ForeignKey("batches.id"))
)


def start_mappers():
    logger.info("Starting mappers")

    lines_mapper = mapper(model.OrderLine, orderline_table)
    batches_mapper = mapper(
        model.Batch,
        batch_table,
        properties={
            "_allocations": relationship(
                lines_mapper,
                secondary=allocations_table,
                collection_class=set
            ),
        }
    )


DEL_ATTR = object()


class FrozenDataclassInstrumentationManager(InstrumentationManager):
    def install_member(self, class_, key, implementation):
        self.originals.setdefault(key, class_.__dict__.get(key, DEL_ATTR))
        setattr(class_, key, implementation)

    def uninstall_member(self, class_, key):
        original = self.originals.pop(key, None)
        if original is not DEL_ATTR:
            setattr(class_, key, original)
        else:
            delattr(class_, key)

    def unregister(self, class_, manager):
        del self.originals
        delattr(class_, "_sa_class_manager")

    def manager_getter(self, class_):
        def get(cls):
            return cls.__dict__["_sa_class_manager"]

        return get

    def manage(self, class_, manager):
        self.originals = {}
        setattr(class_, "_sa_class_manager", manager)

    def get_instance_dict(self, class_, instance):
        return instance.__dict__

    def install_state(self, class_, instance, state):
        instance.__dict__["state"] = state

    def remove_state(self, class_, instance, state):
        del instance.__dict__["state"]

    def state_getter(self, class_):
        def find(instance):
            return instance.__dict__["state"]

        return find


# Extremely dirty hack to allow SQLAlchemy to work with frozen dataclasses
OrderLine.__sa_instrumentation_manager__ = FrozenDataclassInstrumentationManager  # type: ignore

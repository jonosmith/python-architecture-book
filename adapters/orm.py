import logging

from sqlalchemy import MetaData, Column, Table, Integer, String, Date, ForeignKey
from sqlalchemy.orm import mapper, relationship

from domain import model

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

from datetime import datetime
from http import HTTPStatus

from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.allocation import config
from src.allocation.adapters import orm
from src.allocation.domain import model
from src.allocation.service_layer import services, unit_of_work

orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = Flask(__name__)


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    if not request.json:
        return jsonify({"message": "Invalid format"}), HTTPStatus.BAD_REQUEST

    orderid = request.json["orderid"]
    sku = request.json["sku"]
    qty = request.json["qty"]

    try:
        batchref = services.allocate(
            orderid=orderid,
            sku=sku,
            qty=qty,
            uow=unit_of_work.SqlAlchemyUnitOfWork()
        )
    except (model.OutOfStock, services.InvalidSku) as e:
        return jsonify({"message": str(e)}), HTTPStatus.BAD_REQUEST

    return jsonify({"batchref": batchref}), HTTPStatus.CREATED


@app.route("/add_batch", methods=["POST"])
def add_batch():
    if not request.json:
        return jsonify({"message": "Invalid format"}), HTTPStatus.BAD_REQUEST

    ref = request.json["ref"]
    sku = request.json["sku"]
    qty = request.json["qty"]
    eta = None
    input_eta = request.json["eta"]
    if input_eta is not None:
        eta = datetime.fromisoformat(input_eta).date()

    services.add_batch(
        ref=ref,
        sku=sku,
        qty=qty,
        eta=eta,
        uow=unit_of_work.SqlAlchemyUnitOfWork()
    )

    return 'OK', HTTPStatus.CREATED


@app.route("/products/<sku>/batches/<ref>", methods=["DELETE"])
def delete_batch(sku: str, ref: str):
    try:
        services.delete_batch(
            ref=ref,
            sku=sku,
            uow=unit_of_work.SqlAlchemyUnitOfWork()
        )
    except services.BatchNotFound:
        return jsonify({"message": f"Batch {ref} not found"}), HTTPStatus.BAD_REQUEST

    return 'OK', HTTPStatus.OK

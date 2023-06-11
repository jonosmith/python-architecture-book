from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
from adapters import orm, repository
from domain import model
from service_layer import services

orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = Flask(__name__)


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)

    if not request.json:
        return jsonify({"message": "Invalid format"}), 400

    orderid = request.json["orderid"]
    sku = request.json["sku"]
    qty = request.json["qty"]

    try:
        batchref = services.allocate(orderid=orderid, sku=sku, qty=qty, repo=repo, session=session)
    except (model.OutOfStock, services.InvalidSku) as e:
        return jsonify({"message": str(e)}), 400

    return jsonify({"batchref": batchref}), 201

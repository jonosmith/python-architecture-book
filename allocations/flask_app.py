from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from allocations import config, orm, repository, model, services

orm.start_mappers()
print(config.get_postgres_uri())
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = Flask(__name__)


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)

    if not request.json:
        return jsonify({"message": "Invalid format"}), 400

    line = model.OrderLine(
        request.json["orderid"],
        request.json["sku"],
        request.json["qty"]
    )

    try:
        batchref = services.allocate(line, repo, session)
    except (model.OutOfStock, services.InvalidSku) as e:
        return jsonify({"message": str(e)}), 400

    return jsonify({"batchref": batchref}), 201

from http import HTTPStatus

import pytest
import requests

from src.allocation import config
from tests.random_refs import random_sku, random_batchref, random_orderid


def api_add_batch(ref: str, sku: str, qty: int, eta: str | None):
    url = config.get_api_url()
    r = requests.post(
        f"{url}/add_batch",
        json={"ref": ref, "sku": sku, "qty": qty, "eta": eta}
    )
    assert r.status_code == HTTPStatus.CREATED


def api_delete_batch(ref: str, sku: str):
    url = config.get_api_url()
    r = requests.delete(f"{url}/products/{sku}/batches/{ref}")
    assert r.status_code == HTTPStatus.OK


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_happy_path_returns_201_and_allocated_batch():
    # Arrange
    sku, other_sku = random_sku(), random_sku("other")
    earlybatch = random_batchref(1)
    laterbatch = random_batchref(2)
    otherbatch = random_batchref(3)

    api_add_batch(ref=earlybatch, sku=sku, qty=100, eta='2011-01-01')
    api_add_batch(ref=laterbatch, sku=sku, qty=100, eta="2011-01-02")
    api_add_batch(ref=otherbatch, sku=other_sku, qty=100, eta=None)

    data = {"orderid": random_orderid(), "sku": sku, "qty": 3}
    url = config.get_api_url()

    # Act
    r = requests.post(f"{url}/allocate", json=data)

    # Cleanup
    api_delete_batch(earlybatch, sku)
    api_delete_batch(laterbatch, sku)
    api_delete_batch(otherbatch, other_sku)

    # Assert
    assert r.status_code == HTTPStatus.CREATED
    assert r.json()['batchref'] == earlybatch


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_unhappy_path_returns_400_and_error_message():
    unknown_sku, orderid = random_sku(), random_orderid()
    data = {"orderid": orderid, "sku": unknown_sku, "qty": 20}
    url = config.get_api_url()

    r = requests.post(f"{url}/allocate", json=data)

    assert r.status_code == HTTPStatus.BAD_REQUEST
    assert r.json()["message"] == f"Invalid sku {unknown_sku}"

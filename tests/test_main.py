from __future__ import annotations

import importlib
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient


def create_test_client(tmp_path) -> TestClient:
    db_path = tmp_path / "app.db"

    import os

    os.environ["DATABASE_PATH"] = str(db_path)
    os.environ["API_RATE_LIMIT_PER_MINUTE"] = "2"
    os.environ["DEFAULT_API_KEYS"] = "test-key:Test User,rate-key:Rate User"

    import app.config as config
    import app.database as database_module
    import app.security as security_module
    import app.main as main_module

    importlib.reload(config)
    importlib.reload(database_module)
    importlib.reload(security_module)
    importlib.reload(main_module)

    return TestClient(main_module.app)


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    test_client = create_test_client(tmp_path)
    with test_client as client_instance:
        yield client_instance


def test_inspect_valid_id(client: TestClient) -> None:
    response = client.post(
        "/v1/national-ids/inspect",
        json={"national_id": "30101012100013"},
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is True
    assert payload["details"]["birth_date"] == "2001-01-01"
    assert payload["details"]["governorate_code"] == "21"
    assert payload["details"]["gender"] == "male"


def test_inspect_invalid_id(client: TestClient) -> None:
    response = client.post(
        "/v1/national-ids/inspect",
        json={"national_id": "10101012100013"},
        headers={"X-API-Key": "test-key"},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"].startswith("Unsupported century digit")


def test_missing_api_key_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/v1/national-ids/inspect",
        json={"national_id": "30101012100013"},
    )

    assert response.status_code == 401


def test_rate_limit_is_enforced(client: TestClient) -> None:
    headers = {"X-API-Key": "rate-key"}
    body = {"national_id": "30101012100013"}

    first = client.post("/v1/national-ids/inspect", json=body, headers=headers)
    second = client.post("/v1/national-ids/inspect", json=body, headers=headers)
    third = client.post("/v1/national-ids/inspect", json=body, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429


def test_usage_endpoint_reports_total_requests(client: TestClient) -> None:
    headers = {"X-API-Key": "test-key"}
    body = {"national_id": "30101012100013"}

    client.post("/v1/national-ids/inspect", json=body, headers=headers)
    client.post("/v1/national-ids/inspect", json=body, headers=headers)

    usage = client.get("/v1/usage", headers=headers)

    assert usage.status_code == 200
    payload = usage.json()
    assert payload["total_requests"] == 2
    assert payload["api_key"] == "test-key"

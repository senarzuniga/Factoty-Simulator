import pytest
from fastapi.testclient import TestClient
from dcfs.api.server import app

client = TestClient(app)


def test_get_factory_status():
    response = client.get("/factory/status")
    assert response.status_code == 200
    assert "factory_running" in response.json()


def test_get_factory_machines():
    response = client.get("/factory/machines")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_factory_events():
    response = client.get("/factory/events")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_factory_requests():
    response = client.get("/factory/requests")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_post_start_factory():
    response = client.post("/factory/start")
    assert response.status_code == 200
    assert response.json().get("running") is True


def test_post_stop_factory():
    response = client.post("/factory/stop")
    assert response.status_code == 200
    assert response.json().get("running") is False

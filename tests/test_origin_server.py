"""
Unit tests for Origin Server endpoints using FastAPI TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from backend.origin_server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_origin_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "up"
    assert data["server"] == "origin"
    assert data["port"] == 8000


def test_origin_list_files_endpoint(client):
    response = client.get("/list")
    assert response.status_code == 200
    data = response.json()
    assert data["origin"] == "up"
    assert data["file_count"] >= 1
    assert isinstance(data["files"], list)
    paths = [f["path"] for f in data["files"]]
    assert any("index.html" in p for p in paths)


def test_origin_logs_endpoint(client):
    # Make a request first to ensure log exists
    client.get("/health")
    response = client.get("/logs")
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert isinstance(data["logs"], list)


def test_origin_serve_existing_file(client):
    response = client.get("/files/index.html")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_origin_serve_missing_file_returns_404(client):
    response = client.get("/files/non_existent_file_9999.xyz")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data

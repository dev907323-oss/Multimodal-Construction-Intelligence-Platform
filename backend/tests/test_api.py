import pytest
from fastapi.testclient import TestClient

from app.main import app
import app.database as database


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    with TestClient(app) as test_client:
        yield test_client


def test_health_reports_demo_mode(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["ai_enabled"] is False


def test_analysis_is_created_and_saved(client):
    response = client.post(
        "/api/analyze",
        data={"module": "safety", "prompt": "Inspect access routes", "project_name": "Test Project"},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["provider"] == "demo"
    assert result["module"] == "safety"
    assert result["findings"]

    history = client.get("/api/analyses")
    assert history.status_code == 200
    assert history.json()["count"] == 1
    assert history.json()["items"][0]["id"] == result["id"]


def test_unknown_analysis_module_is_rejected(client):
    response = client.post("/api/analyze", data={"module": "not-a-module"})
    assert response.status_code == 422


def test_valuation_uses_user_supplied_area_and_rate_in_demo_mode(client):
    response = client.post(
        "/api/analyze",
        data={
            "module": "valuation",
            "area_sqft": "1800",
            "market_rate_sqft": "5500",
            "project_name": "Test Home",
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert "₹9,900,000" in result["summary"]
    assert "₹9,108,000" in result["summary"]
    assert "₹10,692,000" in result["summary"]

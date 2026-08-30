import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "Online"

def test_cameras_list():
    res = client.get("/api/cameras")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 4

def test_tracking_live():
    res = client.get("/api/tracking/live")
    assert res.status_code == 200
    data = res.json()
    assert "cameras" in data

def test_system_health():
    res = client.get("/api/system/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "Healthy"
    assert "cpu_usage_percent" in data

def test_analytics_overview():
    res = client.get("/api/analytics/overview")
    assert res.status_code == 200

def test_events_list():
    res = client.get("/api/events")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

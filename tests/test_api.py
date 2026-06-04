import pytest
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_predict_range():
    payload = {
        "temperature_c": 20.0,
        "speed_kmh": 80.0,
        "payload_kg": 0.0,
        "hvac_kw": 1.0,
        "battery_age_cycles": 100,
        "soc_pct": 80.0,
        "terrain_grade_pct": 0.0,
        "wind_speed_kmh": 0.0,
        "battery_capacity_kwh": 75.0,
        "model_name": "random_forest"
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "primary" in data
    assert "all_models" in data
    assert data["primary"]["model_used"] == "random_forest"

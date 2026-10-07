import pytest
from fastapi.testclient import TestClient
from hems_api import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_scenarios_expose_bundled_data():
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert "doba_szczyt_wieczorny" in names


def test_optimize_returns_full_horizon_and_beats_thermostat():
    response = client.post("/api/optimize", json={"scenario": "doba_zmienna_cena"})
    assert response.status_code == 200
    body = response.json()
    assert len(body["rows"]) == body["hours"] == 24
    assert body["optimal"]["cost_pln"] < body["thermostat"]["cost_pln"]
    assert body["saving_pln"] > 0
    assert body["optimal"]["hours_below_t_min"] == 0


def test_optimize_honours_overrides():
    response = client.post(
        "/api/optimize",
        json={"scenario": "doba_zmienna_cena", "overrides": {"6": 1, "7": 1}},
    )
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert [rows[6]["optimal_state"], rows[7]["optimal_state"]] == [1, 1]


def test_optimize_accepts_model_params():
    response = client.post(
        "/api/optimize",
        json={"scenario": "doba_mroz", "model_params": {"heater_power_kw": 3.0}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["optimal"]["energy_kwh"] == pytest.approx(3.0 * body["optimal"]["heating_hours"])


def test_unknown_scenario_is_404():
    assert client.post("/api/optimize", json={"scenario": "nie_ma"}).status_code == 404


def test_inverted_comfort_band_is_422():
    response = client.post("/api/optimize", json={"t_min": 23.0, "t_max": 21.0})
    assert response.status_code == 422

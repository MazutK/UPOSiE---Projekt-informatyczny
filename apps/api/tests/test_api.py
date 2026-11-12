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
    assert "doba_live" in names


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


def test_compare_endpoint_returns_methods():
    response = client.post(
        "/api/compare",
        json={"scenario": "doba_szczyt_wieczorny", "t_min": 21.0, "t_max": 22.5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["scenario"] == "doba_szczyt_wieczorny"
    assert len(data["methods"]) == 4
    methods = [m["method"] for m in data["methods"]]
    assert "dp" in methods
    assert "termostat" in methods
    assert "zachlanna" in methods
    assert "progowo" in methods


def test_sensitivity_endpoint():
    response = client.post(
        "/api/sensitivity",
        json={
            "scenario": "doba_zmienna_cena",
            "parameter": "t_min",
            "values": [20.5, 21.0, 21.5],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["parameter"] == "t_min"
    assert len(data["rows"]) == 3
    assert data["rows"][0]["value"] == 20.5


def _fake_weather(date_str, timeout):
    _fake_weather.date = date_str
    return dict.fromkeys(range(24), 5.0), dict.fromkeys(range(24), 0.0)


def _pse_down(date_str, timeout):
    raise OSError("PSE niedostępne")


def test_live_defaults_to_today_and_does_not_mix_days_when_pse_down(monkeypatch, tmp_path):
    from datetime import date

    from hems_api import service

    monkeypatch.setenv("HEMS_LIVE_DIR", str(tmp_path))
    monkeypatch.setattr(service, "fetch_open_meteo_day", _fake_weather)
    monkeypatch.setattr(service, "fetch_pse_day", _pse_down)

    response = client.get("/api/live")
    assert response.status_code == 200
    data = response.json()
    today = date.today().isoformat()
    assert data["date"] == today
    assert _fake_weather.date == today
    # P-01: bez doby mieszanej — cała próbka offline, a nie pogoda z dziś + ceny z próbki
    assert data["source"] == "offline_sample"
    assert "2026-10-13" in data["message"]
    first_row = (tmp_path / "doba_live.csv").read_text(encoding="utf-8").splitlines()[1]
    assert not first_row.endswith(",5.00,0.0")


def test_live_endpoint(monkeypatch, tmp_path):
    from hems_api import service

    monkeypatch.setattr(service, "BUNDLED_DATA_DIR", tmp_path)
    response = client.get("/api/live?date=2026-10-13")
    assert response.status_code == 200
    data = response.json()
    assert data["scenario_name"] == "doba_live"
    assert data["hours"] == 24

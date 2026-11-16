"""Lab 6: doba live — P-01 (bez mieszania dni), Z-08 (metadane), Z-09 (zapis poza repo)."""

import json

from fastapi.testclient import TestClient
from heating_optimizer.datasets import BUNDLED_DATA_DIR
from hems_api import app, service

client = TestClient(app)


def _weather(date_str, timeout):
    return dict.fromkeys(range(24), 4.0), dict.fromkeys(range(24), 0.0)


def _prices(date_str, timeout):
    return dict.fromkeys(range(24), 0.5)


def _down(date_str, timeout):
    raise OSError("brak sieci")


def _incomplete_weather(date_str, timeout):
    raise ValueError("Oczekiwano dokładnie 24 unikalnych godzin")


def test_live_api_writes_day_and_meta_outside_repo(monkeypatch, tmp_path):
    monkeypatch.setenv("HEMS_LIVE_DIR", str(tmp_path))
    monkeypatch.setattr(service, "fetch_open_meteo_day", _weather)
    monkeypatch.setattr(service, "fetch_pse_day", _prices)
    bundled_before = (BUNDLED_DATA_DIR / "doba_live.csv").read_bytes()

    response = client.get("/api/live?date=2026-11-05")

    assert response.status_code == 200
    assert response.json()["source"] == "live_api"
    meta = json.loads((tmp_path / "doba_live.meta.json").read_text(encoding="utf-8"))
    assert meta["data_date"] == "2026-11-05"
    assert meta["requested_date"] == "2026-11-05"
    assert meta["source"] == "live_api"
    assert meta["fetched_at"]
    assert (tmp_path / "doba_live.csv").read_text(encoding="utf-8").splitlines()[1] == "0,0.5000,4.00,0.0"
    assert (BUNDLED_DATA_DIR / "doba_live.csv").read_bytes() == bundled_before  # git status bez zmian
    assert not list(tmp_path.glob("*.tmp"))

    scenarios = {s["name"]: s for s in client.get("/api/scenarios").json()}
    assert "doba 2026-11-05 (live_api)" in scenarios["doba_live"]["description"]

    plan = client.post("/api/optimize", json={"scenario": "doba_live"})
    assert plan.status_code == 200
    assert plan.json()["rows"][0]["outside_temp_c"] == 4.0


def test_incomplete_weather_falls_back_to_whole_sample(monkeypatch, tmp_path):
    monkeypatch.setenv("HEMS_LIVE_DIR", str(tmp_path))
    monkeypatch.setattr(service, "fetch_open_meteo_day", _incomplete_weather)
    monkeypatch.setattr(service, "fetch_pse_day", _prices)

    data = client.get("/api/live?date=2026-11-05").json()

    assert data["source"] == "offline_sample"
    assert "NIE dotyczy wybranej daty" in data["message"]
    meta = json.loads((tmp_path / "doba_live.meta.json").read_text(encoding="utf-8"))
    assert meta["data_date"] == "2026-10-13"
    assert meta["requested_date"] == "2026-11-05"


def test_no_network_no_samples_keeps_previous_day_without_claiming_new_date(monkeypatch, tmp_path):
    live = tmp_path / "live"
    monkeypatch.setenv("HEMS_LIVE_DIR", str(live))
    monkeypatch.setattr(service, "fetch_open_meteo_day", _weather)
    monkeypatch.setattr(service, "fetch_pse_day", _prices)
    assert client.get("/api/live?date=2026-11-01").status_code == 200

    monkeypatch.setattr(service, "RAW_DIR", tmp_path / "brak_probek")
    monkeypatch.setattr(service, "fetch_open_meteo_day", _down)
    data = client.get("/api/live?date=2026-11-07").json()

    assert data["source"] == "cached_bundled"
    assert "2026-11-01" in data["message"]
    assert "2026-11-07" not in data["message"].split("Zostaje")[1]


def test_previous_day_without_meta_has_unknown_date(monkeypatch, tmp_path):
    monkeypatch.setenv("HEMS_LIVE_DIR", str(tmp_path / "pusty"))
    monkeypatch.setattr(service, "RAW_DIR", tmp_path / "brak_probek")
    monkeypatch.setattr(service, "fetch_open_meteo_day", _down)

    data = client.get("/api/live?date=2026-11-07").json()

    assert data["source"] == "cached_bundled"
    assert "nieznanej dacie" in data["message"]

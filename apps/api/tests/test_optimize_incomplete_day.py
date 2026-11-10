"""Z-01: niepełna doba w scenariuszu → HTTP 422, a nie plan na krótszą dobę."""

from fastapi.testclient import TestClient
from heating_optimizer.datasets import DATA_DIR_ENV
from hems_api import app

client = TestClient(app)
HEADER = "hour,price_pln_kwh,outside_temp_c,solar_radiation_wm2\n"


def test_scenario_without_one_hour_is_422(tmp_path, monkeypatch):
    rows = "".join(f"{h},0.5,1.0,0.0\n" for h in range(24) if h != 17)
    (tmp_path / "doba_dziura.csv").write_text(HEADER + rows, encoding="utf-8")
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path))

    response = client.post("/api/optimize", json={"scenario": "doba_dziura"})

    assert response.status_code == 422
    body = response.json()
    assert "brakujące godziny [17]" in body["detail"]
    assert "rows" not in body and "optimal" not in body


def test_valid_scenario_still_returns_plan():
    response = client.post("/api/optimize", json={"scenario": "doba_mroz"})
    assert response.status_code == 200
    assert response.json()["hours"] == 24

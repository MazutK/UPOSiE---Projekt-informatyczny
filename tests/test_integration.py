"""Lab 7: testy integracyjne głównego przepływu UC-01 (Oskar Wysocki).

Przypadki TC-08…TC-11 z docs/tests.md, sekcja 2. Test uruchamia prawdziwy interfejs
(`python -m heating_optimizer` w osobnym procesie i `POST /api/optimize`) i sprawdza
zawartość wyniku, a nie tylko to, czy plik powstał. Koszt i godziny poniżej T_min liczone są
od nowa z pliku wyniku, niezależnie od silnika.

Oczekiwania: docs/architecture.md (UC-01, kryterium odbioru), docs/experiment.md p. 6-7
(5,3469 zł / 0 h i 11,1525 zł / 4 h), docs/implementation.md p. 2 (tabela błędów).
"""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DAY_CSV = ROOT / "data" / "processed" / "doba-live.csv"
INVALID_CSV = ROOT / "data" / "test" / "doba-invalid.csv"
T_MIN = 21.0
HEATER_KW = 1.5
OUTPUT_COLUMNS = [
    "hour",
    "price_pln_kwh",
    "outside_temp_c",
    "solar_radiation_wm2",
    "optimal_state",
    "optimal_temp_c",
    "thermostat_state",
    "thermostat_temp_c",
]


def run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    src = str(ROOT / "packages" / "core" / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, "-m", "heating_optimizer", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )


def read_rows(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == OUTPUT_COLUMNS
        return list(reader)


def cost_from_rows(rows: list[dict[str, str]], state_column: str) -> float:
    return sum(int(r[state_column]) * HEATER_KW * float(r["price_pln_kwh"]) for r in rows)


def hours_below_from_rows(rows: list[dict[str, str]], temp_column: str) -> int:
    return sum(1 for r in rows if float(r[temp_column]) < T_MIN)


# --- TC-08 (R1, R3, R4, R6): pełny przepływ CLI na dobie z Lab 3 ------------------------


def test_tc08_cli_main_flow_writes_plan_matching_lab4(tmp_path):
    out = tmp_path / "wyniki" / "plan-2026-10-13.csv"

    result = run_cli("--data", str(DAY_CSV), "--out", str(out), cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    rows = read_rows(out)
    assert [int(r["hour"]) for r in rows] == list(range(24))
    assert {r["optimal_state"] for r in rows} <= {"0", "1"}

    # Wartości z experiment.md p. 7, przeliczone z pliku wyniku.
    assert cost_from_rows(rows, "optimal_state") == pytest.approx(5.3469, abs=0.0005)
    assert cost_from_rows(rows, "thermostat_state") == pytest.approx(11.1525, abs=0.0005)
    assert hours_below_from_rows(rows, "optimal_temp_c") == 0
    assert hours_below_from_rows(rows, "thermostat_temp_c") == 4

    # Ceny i pogoda w wyniku = plik wejściowy (te same dane dla obu wariantów).
    with open(DAY_CSV, encoding="utf-8", newline="") as f:
        source = list(csv.DictReader(f))
    for got, src in zip(rows, source, strict=True):
        assert float(got["price_pln_kwh"]) == pytest.approx(float(src["price_pln_kwh"]))
        assert float(got["outside_temp_c"]) == pytest.approx(float(src["outside_temp_c"]))

    # Podsumowanie na ekranie (README, sekcja Lab 6).
    assert "Oszczędność: 5.81 zł (52.1%)" in result.stdout


# --- TC-09 (R4, R6): API daje ten sam wynik co CLI --------------------------------------


def test_tc09_api_optimize_matches_cli_for_live_day(tmp_path, monkeypatch):
    monkeypatch.setenv("HEMS_LIVE_DIR", str(tmp_path / "live"))  # bez data-local/ użytkownika
    from fastapi.testclient import TestClient
    from hems_api import app

    response = TestClient(app).post(
        "/api/optimize",
        json={"scenario": "doba_live", "t_min": 21.0, "t_max": 22.5, "t_start": 21.8},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["rows"]) == 24
    assert body["optimal"]["cost_pln"] == pytest.approx(5.3469, abs=0.0005)
    assert body["thermostat"]["cost_pln"] == pytest.approx(11.1525, abs=0.0005)
    assert body["optimal"]["hours_below_t_min"] == 0
    assert body["thermostat"]["hours_below_t_min"] == 4
    assert body["saving_pln"] == pytest.approx(5.8056, abs=0.001)


# --- TC-10: błędna doba przez CLI -------------------------------------------------------


def test_tc10_cli_rejects_incomplete_day_without_output(tmp_path):
    out = tmp_path / "bad.csv"

    result = run_cli("--data", str(INVALID_CSV), "--out", str(out), cwd=tmp_path)

    assert result.returncode == 1
    assert "niepełna doba" in result.stderr
    assert "brakujące godziny" in result.stderr
    assert not out.exists()


# --- TC-11: niepoprawna wartość parametru (NaN / inf) -----------------------------------


@pytest.mark.parametrize("option", [("--t-min", "nan"), ("--t-max", "inf"), ("--t-start", "nan")])
def test_tc11_cli_rejects_non_finite_band_without_plan(tmp_path, option):
    """UC-01: przy błędnym wejściu obliczenie przerwane, bez planu i bez kosztu 0 zł."""
    out = tmp_path / "plan.csv"

    result = run_cli("--data", str(DAY_CSV), "--out", str(out), *option, cwd=tmp_path)

    assert result.returncode != 0
    assert "Koszt energii" not in result.stdout
    assert not out.exists()

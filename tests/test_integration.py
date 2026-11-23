"""Lab 7: test integracyjny głównego przepływu (UC-01) przez CLI.

Uruchomienie z katalogu repozytorium:
    python -m pytest tests/test_integration.py -v

Test woła prawdziwe polecenie z README (`python -m heating_optimizer --data ... --out ...`)
w osobnym procesie, na KOPII próbki w katalogu tymczasowym (data/ nie jest ruszane).
Sprawdza treść wyniku, jednostki i komunikaty, nie tylko to, że plik powstał.

Oczekiwane wartości i ich podstawa:
- 5,35 zł / 11,15 zł / 52,1 %, 0 h vs 4 h poniżej T_min — docs/experiment.md (Lab 4, sekcja 6),
  liczone ręcznie w sekcji 7 (DP: 1,5 · 3,5646 = 5,3469 zł; termostat: 1,5 · 7,4350 = 11,1525 zł).
- Kontrole danych — scripts/check_data.py (Lab 3); ceny w zł/kWh — docs/data-dictionary.md.
- MD5 próbki 729ecf79… — docs/experiment.md, sekcja 2.
- Komunikaty błędów — README, sekcja „Realizacja MVP (Lab 6)”.
"""

from __future__ import annotations

import csv
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "processed" / "doba-live.csv"
INVALID = ROOT / "data" / "test" / "doba-invalid.csv"
SAMPLE_MD5 = "729ecf79df5d39a3ef5e9c64d8be77fe"  # wersja z Lab 3/Lab 4 (końce linii LF)
HEATER_KW = 1.5  # parametry.json: HEMS_HEATER_POWER_KW
T_MIN = 21.0
OUT_COLUMNS = [
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
    env["PYTHONIOENCODING"] = "utf-8"  # polskie znaki w komunikatach także na Windows
    env.pop("HEMS_DATA_DIR", None)  # model budynku zawsze z pakietu
    return subprocess.run(
        [sys.executable, "-m", "heating_optimizer", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )


def md5_lf(path: Path) -> str:
    return hashlib.md5(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


@pytest.fixture
def sample_copy(tmp_path: Path) -> Path:
    copy = tmp_path / "doba-live.csv"
    shutil.copyfile(SAMPLE, copy)
    return copy


# --- T-INT-01: kontrole jakości danych z Lab 3 na próbce użytej do oceny ---------------------


def run_lab3_check(path: Path) -> subprocess.CompletedProcess[str]:
    """Prawdziwy skrypt kontroli z Lab 3 (scripts/check_data.py), bez zmian."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_data.py"), str(path)],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )


def test_int_01_sample_passes_lab3_quality_checks(sample_copy: Path):
    # wersja próbki = ta z Lab 3/Lab 4
    assert md5_lf(SAMPLE) == SAMPLE_MD5, "próbka różni się od wersji z Lab 3/Lab 4"

    result = run_lab3_check(sample_copy)
    assert result.returncode == 0, result.stdout + result.stderr
    for line in ("Rekordy: 24", "Braki: 0", "Duplikaty hour: 0", "Kontrola OK"):
        assert line in result.stdout

    # jednostka ceny: zł/kWh, nie zł/MWh (RCE / 1000 w Lab 3) — tego check_data.py nie sprawdza
    with sample_copy.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == OUT_COLUMNS[:4]
        prices = [float(r["price_pln_kwh"]) for r in reader]
    assert all(0 < p < 5 for p in prices), prices


def test_int_01b_lab3_check_rejects_incomplete_day(tmp_path: Path):
    # kontrola z Lab 3 naprawdę coś łapie: na niepełnej dobie musi się nie udać
    bad = tmp_path / "doba-invalid.csv"
    shutil.copyfile(INVALID, bad)
    result = run_lab3_check(bad)
    assert result.returncode != 0
    assert "Kontrola niezaliczona" in result.stderr
    assert "rekordy: 2 != 24" in result.stderr


# --- T-INT-02: główny przepływ — poprawne wejście -------------------------------------------


def test_int_02_main_flow_content_units_and_messages(sample_copy: Path, tmp_path: Path):
    out = tmp_path / "wyniki" / "plan.csv"  # katalog nie istnieje — CLI ma go utworzyć
    result = run_cli("--data", str(sample_copy), "--out", str(out), cwd=tmp_path)

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    # komunikaty i jednostki w podsumowaniu
    assert "Dane: doba-live.csv (24 h)" in result.stdout
    assert "Komfort: 21.0-22.5 °C, start: 21.8 °C" in result.stdout
    summary = {line.split("  ")[0].strip(): line.split() for line in result.stdout.splitlines()}
    assert summary["Koszt energii [zł]"][-2:] == ["5.35", "11.15"]
    assert summary["Energia [kWh]"][-2:] == ["9.0", "15.0"]
    assert summary["Godziny poniżej T_min"][-2:] == ["0", "4"]
    assert "Oszczędność: 5.81 zł (52.1%)" in result.stdout
    assert f"Zapisano: {out}" in result.stdout

    # treść pliku wyniku, nie tylko jego istnienie
    with out.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == OUT_COLUMNS
        rows = list(reader)
    with sample_copy.open(encoding="utf-8", newline="") as f:
        source = list(csv.DictReader(f))

    assert [int(r["hour"]) for r in rows] == list(range(24))
    for got, src in zip(rows, source, strict=True):
        for column in OUT_COLUMNS[1:4]:  # wejście przepisane bez zmiany jednostek
            assert float(got[column]) == pytest.approx(float(src[column]))
        assert got["optimal_state"] in {"0", "1"} and got["thermostat_state"] in {"0", "1"}
        assert float(got["optimal_temp_c"]) >= T_MIN  # optymalizator trzyma komfort

    cost_dp = sum(int(r["optimal_state"]) * float(r["price_pln_kwh"]) * HEATER_KW for r in rows)
    cost_term = sum(
        int(r["thermostat_state"]) * float(r["price_pln_kwh"]) * HEATER_KW for r in rows
    )
    assert cost_dp == pytest.approx(5.3469, abs=1e-4)
    assert cost_term == pytest.approx(11.1525, abs=1e-4)
    assert sum(float(r["thermostat_temp_c"]) < T_MIN for r in rows) == 4
    assert md5_lf(sample_copy) == SAMPLE_MD5  # wejście nietknięte


# --- T-INT-03: błędne wejście — niepełna doba -------------------------------------------------


def test_int_03_incomplete_day_gives_message_and_no_file(tmp_path: Path):
    bad = tmp_path / "doba-invalid.csv"
    shutil.copyfile(INVALID, bad)
    out = tmp_path / "plan.csv"
    result = run_cli("--data", str(bad), "--out", str(out), cwd=tmp_path)

    assert result.returncode == 1
    assert "niepełna doba" in result.stderr
    assert "brakujące godziny [2," in result.stderr
    assert not out.exists()


# --- T-INT-04: istniejący wynik nie jest nadpisywany -----------------------------------------


def test_int_04_existing_output_is_not_overwritten(sample_copy: Path, tmp_path: Path):
    out = tmp_path / "plan.csv"
    out.write_text("stary wynik\n", encoding="utf-8")
    result = run_cli("--data", str(sample_copy), "--out", str(out), cwd=tmp_path)

    assert result.returncode == 1
    assert "już istnieje" in result.stderr
    assert out.read_text(encoding="utf-8") == "stary wynik\n"


# --- T-INT-05: pasmo komfortu musi być liczbą skończoną (Issue: CLI przyjmuje NaN) ----------


@pytest.mark.parametrize(
    "args",
    [
        ("--t-min", "nan"),
        ("--t-max", "inf"),
        ("--t-start", "nan"),
        ("--t-min=-inf",),  # z „=”, inaczej argparse bierze -inf za nazwę opcji
    ],
)
def test_int_05_non_finite_comfort_band_is_rejected(sample_copy: Path, tmp_path: Path, args):
    out = tmp_path / "plan.csv"
    result = run_cli("--data", str(sample_copy), "--out", str(out), *args, cwd=tmp_path)

    # wymaganie R3: bez poprawnego pasma nie ma planu — błąd zamiast „0 zł, 0 h poniżej T_min”
    assert result.returncode != 0
    assert "skończoną liczbą" in result.stderr
    assert "Koszt energii" not in result.stdout
    assert not out.exists()

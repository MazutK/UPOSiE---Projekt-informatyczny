from pathlib import Path

import pytest
from heating_optimizer.data_sources import (
    build_hourly_inputs,
    format_as_csv_string,
    load_live_sample,
    load_open_meteo_file,
    load_pse_file,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = REPO_ROOT / "data" / "raw"
PSE_SAMPLE = RAW_DIR / "pse-rce-sample.json"
WEATHER_SAMPLE = RAW_DIR / "open-meteo-sample.json"


def test_pse_sample_parsing():
    prices = load_pse_file(PSE_SAMPLE)
    assert len(prices) == 24
    assert all(0 <= h < 24 for h in prices)
    assert all(p > 0 for p in prices.values())
    # Pierwsza godzina w próbce
    assert isinstance(prices[0], float)


def test_weather_sample_parsing():
    temps, rads = load_open_meteo_file(WEATHER_SAMPLE)
    assert len(temps) == 24
    assert len(rads) == 24
    assert all(r >= 0 for r in rads.values())


def test_build_hourly_inputs_from_fixtures():
    inputs = load_live_sample(PSE_SAMPLE, WEATHER_SAMPLE)
    assert inputs.hours == 24
    assert len(inputs.prices) == 24
    assert len(inputs.outside_temperatures) == 24
    assert len(inputs.solar_radiation) == 24


def test_validation_missing_hours():
    prices = dict.fromkeys(range(23), 0.5)  # brakuje godziny 23
    temps = dict.fromkeys(range(24), 5.0)
    rads = dict.fromkeys(range(24), 0.0)

    with pytest.raises(ValueError, match="Brakujące godziny"):
        build_hourly_inputs(prices, temps, rads)


def test_validation_negative_radiation():
    prices = dict.fromkeys(range(24), 0.5)
    temps = dict.fromkeys(range(24), 5.0)
    rads = dict.fromkeys(range(24), 0.0)
    rads[12] = -5.0

    with pytest.raises(ValueError, match="nieprawidłowe"):
        build_hourly_inputs(prices, temps, rads)


def test_format_as_csv_string():
    inputs = load_live_sample(PSE_SAMPLE, WEATHER_SAMPLE)
    csv_text = format_as_csv_string(inputs)
    lines = csv_text.strip().split("\n")
    assert lines[0] == "hour,price_pln_kwh,outside_temp_c,solar_radiation_wm2"
    assert len(lines) == 25


def test_save_as_csv_is_atomic(tmp_path, monkeypatch):
    """Z-09: przerwany zapis zostawia poprzedni plik, a nie niepełny nowy."""
    import os

    import pytest
    from heating_optimizer import HourlyInputs
    from heating_optimizer.data_sources import save_as_csv

    day = HourlyInputs.of([0.5] * 24, [1.0] * 24, [0.0] * 24)
    target = tmp_path / "doba_live.csv"
    target.write_text("poprzednia doba", encoding="utf-8")

    def broken_replace(src, dst):
        raise OSError("dysk pełny")

    monkeypatch.setattr(os, "replace", broken_replace)
    with pytest.raises(OSError):
        save_as_csv(day, target)
    assert target.read_text(encoding="utf-8") == "poprzednia doba"
    assert not list(tmp_path.glob("*.tmp"))

"""Z-01: kontrola doby przy wczytaniu CSV (Lab 6)."""

import pytest
from heating_optimizer import HourlyInputs
from heating_optimizer.datasets import BUNDLED_DATA_DIR

HEADER = "hour,price_pln_kwh,outside_temp_c,solar_radiation_wm2\n"


def write_day(tmp_path, hours, row="0.5,1.0,0.0"):
    path = tmp_path / "doba.csv"
    path.write_text(HEADER + "".join(f"{h},{row}\n" for h in hours), encoding="utf-8")
    return path


def test_full_day_is_accepted():
    inputs = HourlyInputs.from_csv(BUNDLED_DATA_DIR / "doba_mroz.csv", expected_hours=24)
    assert inputs.hours == 24


def test_missing_hour_is_rejected(tmp_path):
    path = write_day(tmp_path, [h for h in range(24) if h != 17])
    with pytest.raises(ValueError, match=r"brakujące godziny \[17\]"):
        HourlyInputs.from_csv(path, expected_hours=24)


def test_gap_is_rejected_without_expected_length(tmp_path):
    # Przypadek z przeglądu Lab 5 (§8.1): godziny 0 i 5 dawały plan na 2 h.
    path = write_day(tmp_path, [0, 5])
    with pytest.raises(ValueError, match="niepełna doba"):
        HourlyInputs.from_csv(path)


def test_duplicate_hour_is_rejected(tmp_path):
    path = write_day(tmp_path, [*range(24), 3])
    with pytest.raises(ValueError, match="więcej niż raz"):
        HourlyInputs.from_csv(path, expected_hours=24)


def test_text_instead_of_number_is_rejected(tmp_path):
    path = write_day(tmp_path, range(24), row="brak,1.0,0.0")
    with pytest.raises(ValueError, match="niepoprawną liczbę"):
        HourlyInputs.from_csv(path, expected_hours=24)


def test_nan_and_negative_radiation_are_rejected(tmp_path):
    path = write_day(tmp_path, range(24), row="nan,1.0,0.0")
    with pytest.raises(ValueError, match="nieskończoną"):
        HourlyInputs.from_csv(path, expected_hours=24)
    path = write_day(tmp_path, range(24), row="0.5,1.0,-3")
    with pytest.raises(ValueError, match="ujemne"):
        HourlyInputs.from_csv(path, expected_hours=24)


def test_empty_file_is_rejected(tmp_path):
    path = write_day(tmp_path, [])
    with pytest.raises(ValueError):
        HourlyInputs.from_csv(path, expected_hours=24)

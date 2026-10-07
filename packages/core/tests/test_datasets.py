import pytest
from heating_optimizer import available, default_model, load_inputs, resolve
from heating_optimizer.datasets import BUNDLED_DATA_DIR, DATA_DIR_ENV


def test_bundled_scenarios_are_discoverable():
    names = {scenario.name for scenario in available()}
    assert names == {
        "doba_mroz",
        "doba_slonecznie",
        "doba_szczyt_wieczorny",
        "doba_zmienna_cena",
    }
    assert all(scenario.hours == 24 for scenario in available())


def test_resolve_accepts_name_and_path():
    assert resolve("doba_mroz") == BUNDLED_DATA_DIR / "doba_mroz.csv"
    assert resolve(str(BUNDLED_DATA_DIR / "doba_mroz.csv")) == BUNDLED_DATA_DIR / "doba_mroz.csv"


def test_resolve_reports_unknown_scenario():
    with pytest.raises(FileNotFoundError, match="doba_zmienna_cena"):
        resolve("nie_ma_takiej_doby")


def test_load_inputs_matches_model_horizon():
    assert load_inputs("doba_slonecznie").hours == 24


def test_user_data_dir_takes_precedence(tmp_path, monkeypatch):
    custom = tmp_path / "wlasne"
    custom.mkdir()
    (custom / "doba_testowa.csv").write_text(
        "hour,price_pln_kwh,outside_temp_c,solar_radiation_wm2\n0,0.5,0.0,0.0\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(DATA_DIR_ENV, str(custom))

    assert "doba_testowa" in {scenario.name for scenario in available()}
    assert load_inputs("doba_testowa").hours == 1
    assert default_model().delay == 2  # parametry.json nadal z pakietu

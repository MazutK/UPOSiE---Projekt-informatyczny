import json

import pytest
from heating_optimizer import HourlyInputs, ThermalModel, simulate_temperatures

MODEL = ThermalModel(alpha=0.005, beta=0.25, gamma=0.0005, constant=-0.05, delay=2)
COLD = HourlyInputs.of([1.0] * 24, [0.0] * 24, [0.0] * 24)


def test_without_heating_temperature_falls():
    temps = simulate_temperatures(MODEL, [0] * 24, COLD, 21.0)
    assert len(temps) == 24
    assert temps[-1] < 21.0


def test_heating_raises_temperature():
    cold = simulate_temperatures(MODEL, [0] * 24, COLD, 21.0)
    warm = simulate_temperatures(MODEL, [1] * 24, COLD, 21.0)
    assert warm[-1] > cold[-1]


def test_delay_postpones_heating_effect():
    on = simulate_temperatures(MODEL, [1] * 24, COLD, 21.0)
    off = simulate_temperatures(MODEL, [0] * 24, COLD, 21.0)
    assert on[0] == off[0]
    assert on[1] == off[1]
    assert on[2] > off[2]


def test_heating_history_seeds_the_delay_window():
    without = simulate_temperatures(MODEL, [0] * 24, COLD, 21.0)
    with_history = simulate_temperatures(MODEL, [0] * 24, COLD, 21.0, heating_history=[1, 1])
    assert with_history[0] > without[0]


def test_solar_gain_increases_temperature():
    sunny = HourlyInputs.of([1.0] * 24, [0.0] * 24, [300.0] * 24)
    assert (
        simulate_temperatures(MODEL, [0] * 24, sunny, 21.0)[-1]
        > simulate_temperatures(MODEL, [0] * 24, COLD, 21.0)[-1]
    )


def test_model_from_json(tmp_path):
    path = tmp_path / "params.json"
    path.write_text(
        json.dumps({"ALPHA": 0.01, "BETA": 0.3, "DELAY": 1, "HEMS_HEATER_POWER_KW": 2.0}),
        encoding="utf-8",
    )
    model = ThermalModel.from_json(path)
    assert model == ThermalModel(
        alpha=0.01, beta=0.3, gamma=0.0, constant=0.0, delay=1, heater_power_kw=2.0
    )


def test_model_validation():
    with pytest.raises(ValueError):
        ThermalModel(alpha=0.01, beta=0.3, delay=-1)
    with pytest.raises(ValueError):
        ThermalModel(alpha=0.01, beta=0.3, heater_power_kw=0.0)


def test_inputs_require_equal_lengths():
    with pytest.raises(ValueError):
        HourlyInputs.of([1.0] * 24, [0.0] * 23, [0.0] * 24)
    with pytest.raises(ValueError):
        HourlyInputs.of([], [], [])


def test_inputs_window():
    inputs = HourlyInputs.of(range(48), [0.0] * 48, [0.0] * 48)
    window = inputs.window(10, 24)
    assert window.hours == 24
    assert window.prices[0] == 10.0
    with pytest.raises(ValueError):
        inputs.window(30, 24)


def test_inputs_from_csv_sorts_by_hour(tmp_path):
    path = tmp_path / "day.csv"
    path.write_text(
        "hour,price_pln_kwh,outside_temp_c,solar_radiation_wm2\n1,0.7,2.0,10\n0,0.5,1.0,0\n",
        encoding="utf-8",
    )
    inputs = HourlyInputs.from_csv(path)
    assert inputs.prices == (0.5, 0.7)
    assert inputs.outside_temperatures == (1.0, 2.0)


def test_inputs_from_csv_reports_missing_columns(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("hour,price\n0,0.5\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing columns"):
        HourlyInputs.from_csv(path)

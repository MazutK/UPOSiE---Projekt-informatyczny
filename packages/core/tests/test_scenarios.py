import pytest
from heating_optimizer import (
    ComfortBand,
    HourlyInputs,
    cli,
    default_model,
    find_optimal_schedule,
    simulate_thermostat,
)
from heating_optimizer.datasets import BUNDLED_DATA_DIR as DATA

MODEL = default_model()
T_MIN, T_MAX = 21.0, 22.5


def run(name, t_start=21.8, overrides=None):
    inputs = HourlyInputs.from_csv(DATA / name)
    optimal = find_optimal_schedule(
        MODEL, inputs, ComfortBand(T_MIN, T_MAX), t_start, overrides=overrides
    )
    thermostat = simulate_thermostat(MODEL, inputs, T_MIN, T_MAX, t_start)
    return inputs, optimal, thermostat


@pytest.mark.parametrize(
    "name", ["doba_zmienna_cena.csv", "doba_szczyt_wieczorny.csv", "doba_slonecznie.csv"]
)
def test_cheaper_than_thermostat_and_comfortable(name):
    _, optimal, thermostat = run(name)
    assert optimal.cost < thermostat.cost
    assert optimal.hours_below(T_MIN) == 0


def test_evening_peak_is_avoided():
    _, optimal, thermostat = run("doba_szczyt_wieczorny.csv")
    assert sum(optimal.schedule[17:22]) < sum(thermostat.schedule[17:22])


def test_cold_snap_deficit_not_worse_than_thermostat():
    _, optimal, thermostat = run("doba_mroz.csv", t_start=21.5)
    assert optimal.deficit(T_MIN) <= thermostat.deficit(T_MIN) + 1e-9


def test_cold_start_returns_to_comfort():
    _, optimal, thermostat = run("doba_zmienna_cena.csv", t_start=19.5)
    assert optimal.temperatures[-1] >= T_MIN
    assert optimal.deficit(T_MIN) <= thermostat.deficit(T_MIN) + 1e-9


def test_flat_price_saves_less_than_variable_price():
    inputs, optimal, thermostat = run("doba_zmienna_cena.csv")
    flat_price = sum(inputs.prices) / inputs.hours
    flat = HourlyInputs.of(
        [flat_price] * inputs.hours, inputs.outside_temperatures, inputs.solar_radiation
    )
    flat_optimal = find_optimal_schedule(MODEL, flat, ComfortBand(T_MIN, T_MAX), 21.8)
    flat_thermostat = simulate_thermostat(MODEL, flat, T_MIN, T_MAX, 21.8)
    variable_pct = (thermostat.cost - optimal.cost) / thermostat.cost
    flat_pct = (flat_thermostat.cost - flat_optimal.cost) / flat_thermostat.cost
    assert flat_pct < variable_pct


def test_user_overrides_are_executed():
    _, optimal, _ = run("doba_zmienna_cena.csv", overrides={6: 1, 7: 1, 8: 1, 9: 0})
    assert [optimal.schedule[h] for h in (6, 7, 8, 9)] == [1, 1, 1, 0]


def test_cli_runs_and_writes_csv(tmp_path, capsys):
    out = tmp_path / "wyniki.csv"
    assert (
        cli.main(["--data", str(DATA / "doba_mroz.csv"), "--t-start", "21.5", "--out", str(out)])
        == 0
    )
    assert "Oszczędność" in capsys.readouterr().out
    assert len(out.read_text(encoding="utf-8").strip().splitlines()) == 25


def test_cli_reports_missing_file(tmp_path, capsys):
    assert cli.main(["--data", str(tmp_path / "brak.csv")]) == 1
    assert "Błąd" in capsys.readouterr().err


def test_cli_lists_bundled_scenarios(capsys):
    assert cli.main(["--list"]) == 0
    assert "doba_szczyt_wieczorny" in capsys.readouterr().out

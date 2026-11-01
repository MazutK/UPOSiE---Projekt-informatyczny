import math

from heating_optimizer import HourlyInputs, default_model
from heating_optimizer.datasets import BUNDLED_DATA_DIR
from heating_optimizer.sensitivity import (
    export_sensitivity_csv,
    run_sensitivity_analysis,
)

MODEL = default_model()
INPUTS = HourlyInputs.from_csv(BUNDLED_DATA_DIR / "doba_zmienna_cena.csv")


def test_sensitivity_three_points_returns_three_rows():
    grid = [20.5, 21.0, 21.5]
    result = run_sensitivity_analysis(
        MODEL, INPUTS, parameter="t_min", values=grid, scenario_name="doba_zmienna_cena"
    )

    assert result.parameter == "t_min"
    assert len(result.rows) == 3

    # Sprawdzenie kolejności rosnącej
    values = [r.value for r in result.rows]
    assert values == [20.5, 21.0, 21.5]

    # Sprawdzenie skończoności liczb
    for r in result.rows:
        assert math.isfinite(r.dp_cost_pln)
        assert math.isfinite(r.thermostat_cost_pln)
        assert math.isfinite(r.saving_pln)
        assert r.dp_cost_pln > 0


def test_sensitivity_overshoot_grid():
    grid = [0.0, 0.5, 1.0]
    result = run_sensitivity_analysis(MODEL, INPUTS, parameter="max_overshoot", values=grid)
    assert len(result.rows) == 3
    # Większy dopuszczalny overshoot pozwala akumulować tańsze ciepło -> koszt DP nie powinien rosnąć
    assert result.rows[-1].dp_cost_pln <= result.rows[0].dp_cost_pln + 1e-4


def test_export_sensitivity_csv():
    grid = [20.5, 21.0]
    result = run_sensitivity_analysis(MODEL, INPUTS, parameter="t_min", values=grid)
    csv_str = export_sensitivity_csv(result)
    lines = csv_str.strip().split("\n")
    assert lines[0].startswith("parametr_t_min,")
    assert len(lines) == 3

from heating_optimizer import (
    ComfortBand,
    HourlyInputs,
    default_model,
)
from heating_optimizer.baselines import (
    compare_all_methods,
    simulate_fixed_threshold,
    simulate_greedy,
)
from heating_optimizer.datasets import BUNDLED_DATA_DIR

MODEL = default_model()
COMFORT = ComfortBand(t_min=21.0, t_max=22.5)


def test_greedy_and_fixed_threshold_return_valid_plans():
    inputs = HourlyInputs.from_csv(BUNDLED_DATA_DIR / "doba_szczyt_wieczorny.csv")
    greedy = simulate_greedy(MODEL, inputs, COMFORT, t_start=21.8)
    fixed = simulate_fixed_threshold(MODEL, inputs, COMFORT, t_start=21.8)

    assert greedy.hours == 24
    assert fixed.hours == 24
    assert len(greedy.temperatures) == 24
    assert len(fixed.temperatures) == 24
    assert greedy.cost > 0
    assert fixed.cost > 0


def test_evening_peak_dp_is_cheapest():
    inputs = HourlyInputs.from_csv(BUNDLED_DATA_DIR / "doba_szczyt_wieczorny.csv")
    results = compare_all_methods(MODEL, inputs, COMFORT, t_start=21.8)

    metrics_map = {m.method: m for m in results}
    dp = metrics_map["dp"]
    thermostat = metrics_map["termostat"]
    metrics_map["zachlanna"]

    # DP musi być tańszy niż termostat
    assert dp.cost_pln < thermostat.cost_pln
    # DP osiąga zerowy deficyt poniżej T_min
    assert dp.hours_below_t_min == 0
    # Oszczędność DP jest dodatnia
    assert dp.saving_pln > 0
    assert dp.saving_pct > 0


def test_compare_all_methods_returns_all_four_variants():
    inputs = HourlyInputs.from_csv(BUNDLED_DATA_DIR / "doba_zmienna_cena.csv")
    results = compare_all_methods(MODEL, inputs, COMFORT, t_start=21.8)
    assert len(results) == 4
    methods = [m.method for m in results]
    assert methods == ["dp", "termostat", "zachlanna", "progowo"]

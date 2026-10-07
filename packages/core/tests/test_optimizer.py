import pytest
from heating_optimizer import (
    ComfortBand,
    HourlyInputs,
    ThermalModel,
    evaluate_schedule,
    find_optimal_schedule,
    simulate_temperatures,
    simulate_thermostat,
)

MODEL = ThermalModel(alpha=0.005, beta=0.25, gamma=0.0005, constant=-0.05, delay=2)
COLD = HourlyInputs.of([1.0] * 24, [0.0] * 24, [0.0] * 24)
MILD_FLAT = HourlyInputs.of([1.0] * 24, [5.0] * 24, [0.0] * 24)


def mild(prices):
    return HourlyInputs.of(prices, [5.0] * len(prices), [0.0] * len(prices))


def test_dp_respects_overrides():
    overrides = {5: 1, 6: 1, 12: 0}
    plan = find_optimal_schedule(MODEL, COLD, ComfortBand(21.0, 23.0), 22.0, overrides=overrides)
    for hour, expected in overrides.items():
        assert plan.schedule[hour] == expected


def test_override_wins_over_comfort():
    plan = find_optimal_schedule(
        MODEL, COLD, ComfortBand(21.0, 23.0), 18.0, overrides=dict.fromkeys(range(24), 0)
    )
    assert plan.heating_hours == 0


def test_invalid_override_is_rejected():
    with pytest.raises(ValueError):
        find_optimal_schedule(MODEL, COLD, ComfortBand(21.0, 23.0), 22.0, overrides={24: 1})
    with pytest.raises(ValueError):
        find_optimal_schedule(MODEL, COLD, ComfortBand(21.0, 23.0), 22.0, overrides={3: 2})


def test_dp_prefers_cheap_hours():
    inputs = HourlyInputs.of([0.1] * 6 + [10.0] * 18, [0.0] * 24, [0.0] * 24)
    plan = find_optimal_schedule(MODEL, inputs, ComfortBand(21.0, 24.0), 21.5)
    assert sum(plan.schedule[:6]) > 0


def test_t_min_is_kept_when_feasible():
    inputs = mild([0.1] * 6 + [50.0] * 18)
    plan = find_optimal_schedule(MODEL, inputs, ComfortBand(21.0, 22.0), 22.5)
    assert min(plan.temperatures) >= 21.0 - 1e-6


def test_unavoidable_deficit_is_minimized():
    plan = find_optimal_schedule(MODEL, MILD_FLAT, ComfortBand(21.0, 22.0), 18.0)
    always_on = simulate_temperatures(MODEL, [1] * 24, MILD_FLAT, 18.0)
    assert min(plan.temperatures) >= min(always_on) - 1e-6


def test_overshoot_allowance_enables_heat_storage():
    inputs = mild([0.1] * 6 + [3.0] * 18)
    no_buffer = find_optimal_schedule(
        MODEL, inputs, ComfortBand(21.0, 21.5, max_overshoot=0.0), 21.3
    )
    with_buffer = find_optimal_schedule(
        MODEL, inputs, ComfortBand(21.0, 21.5, max_overshoot=1.0), 21.3
    )
    assert with_buffer.cost < no_buffer.cost
    assert max(with_buffer.temperatures) > 21.5
    assert max(with_buffer.temperatures) <= 21.5 + 1.0 + 0.3


def test_plan_matches_replayed_simulation():
    inputs = mild([0.3, 0.2, 0.2, 0.4] * 6)
    plan = find_optimal_schedule(
        MODEL, inputs, ComfortBand(21.0, 22.5), 21.4, heating_history=[1, 0]
    )
    replay = evaluate_schedule(MODEL, plan.schedule, inputs, 21.4, heating_history=[1, 0])
    assert replay.temperatures == plan.temperatures
    assert replay.cost == pytest.approx(plan.cost)


@pytest.mark.parametrize("hours", [1, 6, 24, 48])
def test_any_horizon_length(hours):
    inputs = HourlyInputs.of(
        [0.5 + 0.1 * (h % 7) for h in range(hours)], [2.0] * hours, [0.0] * hours
    )
    plan = find_optimal_schedule(MODEL, inputs, ComfortBand(21.0, 22.5), 21.5)
    assert plan.hours == hours
    assert len(plan.temperatures) == hours
    assert plan.temperatures == simulate_temperatures(MODEL, plan.schedule, inputs, 21.5)


def test_48h_plan_keeps_comfort_on_second_day():
    prices = [
        0.6,
        0.5,
        0.5,
        0.5,
        0.6,
        0.8,
        1.1,
        1.2,
        1.0,
        0.9,
        0.8,
        0.8,
        0.8,
        0.9,
        1.0,
        1.2,
        1.4,
        1.5,
        1.4,
        1.2,
        1.0,
        0.8,
        0.7,
        0.6,
    ] * 2
    inputs = HourlyInputs.of(prices, [1.0] * 48, [0.0] * 48)
    plan = find_optimal_schedule(MODEL, inputs, ComfortBand(21.0, 22.5), 21.8)
    assert plan.hours_below(21.0) == 0


def test_zero_delay_heating_acts_immediately():
    model = ThermalModel(alpha=0.005, beta=0.25, constant=-0.05, delay=0)
    plan = find_optimal_schedule(model, COLD, ComfortBand(21.0, 22.5), 21.0)
    assert plan.hours_below(21.0) == 0
    assert plan.temperatures == simulate_temperatures(model, plan.schedule, COLD, 21.0)


def test_comfort_band_validation():
    with pytest.raises(ValueError):
        ComfortBand(23.0, 21.0)
    with pytest.raises(ValueError):
        ComfortBand(21.0, 22.0, max_overshoot=-1.0)


def test_thermostat_cost_is_sum_of_hours():
    plan = simulate_thermostat(MODEL, COLD, 21.0, 22.5, 20.0)
    assert plan.schedule[0] == 1
    assert plan.cost == pytest.approx(sum(plan.cost_by_hour))


def test_thermostat_cost_scales_with_heater_power():
    weak = ThermalModel(alpha=0.005, beta=0.25, constant=-0.05, heater_power_kw=1.0)
    strong = ThermalModel(alpha=0.005, beta=0.25, constant=-0.05, heater_power_kw=3.0)
    cost_weak = simulate_thermostat(weak, COLD, 21.0, 22.5, 20.0).cost
    cost_strong = simulate_thermostat(strong, COLD, 21.0, 22.5, 20.0).cost
    assert cost_strong == pytest.approx(cost_weak * 3.0)


def test_thermostat_initial_state_is_kept_inside_band():
    on = simulate_thermostat(MODEL, MILD_FLAT, 21.0, 22.5, 21.5, initial_state=1)
    off = simulate_thermostat(MODEL, MILD_FLAT, 21.0, 22.5, 21.5, initial_state=0)
    assert on.schedule[0] == 1
    assert off.schedule[0] == 0

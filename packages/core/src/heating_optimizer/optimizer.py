from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .inputs import HourlyInputs
from .model import ThermalModel
from .plan import Plan, hourly_costs

STATE_TEMP_RESOLUTION = 0.05
DEFAULT_MAX_OVERSHOOT_C = 1.0
DEFAULT_OVERHEAT_PENALTY_PLN = 1000.0


@dataclass(frozen=True)
class ComfortBand:
    t_min: float
    t_max: float
    max_overshoot: float = DEFAULT_MAX_OVERSHOOT_C
    overheat_penalty: float = DEFAULT_OVERHEAT_PENALTY_PLN

    def __post_init__(self) -> None:
        if self.t_min > self.t_max:
            raise ValueError("t_min must not be greater than t_max")
        if self.max_overshoot < 0:
            raise ValueError("max_overshoot must not be negative")


@dataclass
class _Node:
    cost: tuple[float, float]
    previous: tuple[float, tuple[int, ...]] | None
    action: int | None
    temperature: float


def _state_key(temperature: float) -> float:
    return round(temperature / STATE_TEMP_RESOLUTION) * STATE_TEMP_RESOLUTION


def _validate_overrides(overrides: Mapping[int, int] | None, hours: int) -> dict[int, int]:
    if not overrides:
        return {}
    for hour, state in overrides.items():
        if not 0 <= hour < hours:
            raise ValueError(f"override hour {hour} is outside 0..{hours - 1}")
        if state not in (0, 1):
            raise ValueError(f"override state for hour {hour} must be 0 or 1")
    return dict(overrides)


def find_optimal_schedule(
    model: ThermalModel,
    inputs: HourlyInputs,
    comfort: ComfortBand,
    t_start: float,
    heating_history: Sequence[int] | None = None,
    overrides: Mapping[int, int] | None = None,
) -> Plan:
    hours = inputs.hours
    forced = _validate_overrides(overrides, hours)
    ceiling = comfort.t_max + comfort.max_overshoot
    start_history = model.initial_history(heating_history)

    layer: dict[tuple[float, tuple[int, ...]], _Node] = {
        (_state_key(t_start), start_history): _Node((0.0, 0.0), None, None, float(t_start))
    }
    layers = [layer]

    for hour in range(hours):
        price = inputs.prices[hour]
        outside = inputs.outside_temperatures[hour]
        radiation = inputs.solar_radiation[hour]
        choices = (forced[hour],) if hour in forced else (0, 1)
        next_layer: dict[tuple[float, tuple[int, ...]], _Node] = {}

        for key, node in layer.items():
            _, history = key
            for decision in choices:
                effective, next_history = model.advance(history, decision)
                temperature = model.next_temperature(
                    node.temperature, effective, outside, radiation
                )

                discomfort = max(0.0, comfort.t_min - temperature) ** 2
                money = price * model.heater_power_kw if decision == 1 else 0.0
                excess = temperature - ceiling
                if excess > 0:
                    money += comfort.overheat_penalty * excess**2

                cost = (node.cost[0] + discomfort, node.cost[1] + money)
                next_key = (_state_key(temperature), next_history)
                existing = next_layer.get(next_key)
                if existing is None or cost < existing.cost:
                    next_layer[next_key] = _Node(cost, key, decision, temperature)

        layer = next_layer
        layers.append(layer)

    key = min(layer, key=lambda k: layer[k].cost)
    schedule = [0] * hours
    temperatures = [0.0] * hours
    for hour in reversed(range(hours)):
        node = layers[hour + 1][key]
        schedule[hour] = node.action
        temperatures[hour] = node.temperature
        key = node.previous

    return Plan(
        schedule=tuple(schedule),
        temperatures=tuple(temperatures),
        cost_by_hour=hourly_costs(schedule, inputs.prices, model.heater_power_kw),
        heater_power_kw=model.heater_power_kw,
    )

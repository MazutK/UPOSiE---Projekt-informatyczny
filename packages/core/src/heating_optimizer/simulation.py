from __future__ import annotations

from collections.abc import Sequence

from .inputs import HourlyInputs
from .model import ThermalModel
from .plan import Plan, hourly_costs


def simulate_temperatures(
    model: ThermalModel,
    schedule: Sequence[int],
    inputs: HourlyInputs,
    t_start: float,
    heating_history: Sequence[int] | None = None,
) -> tuple[float, ...]:
    if len(schedule) > inputs.hours:
        raise ValueError("schedule is longer than the inputs")
    history = model.initial_history(heating_history)
    temperature = t_start
    temperatures: list[float] = []
    for hour, decision in enumerate(schedule):
        effective, history = model.advance(history, int(decision))
        temperature = model.next_temperature(
            temperature,
            effective,
            inputs.outside_temperatures[hour],
            inputs.solar_radiation[hour],
        )
        temperatures.append(temperature)
    return tuple(temperatures)


def evaluate_schedule(
    model: ThermalModel,
    schedule: Sequence[int],
    inputs: HourlyInputs,
    t_start: float,
    heating_history: Sequence[int] | None = None,
) -> Plan:
    temperatures = simulate_temperatures(model, schedule, inputs, t_start, heating_history)
    return Plan(
        schedule=tuple(int(s) for s in schedule),
        temperatures=temperatures,
        cost_by_hour=hourly_costs(schedule, inputs.prices, model.heater_power_kw),
        heater_power_kw=model.heater_power_kw,
    )


def thermostat_decision(temperature: float, t_min: float, t_max: float, previous: int) -> int:
    if temperature <= t_min:
        return 1
    if temperature >= t_max:
        return 0
    return previous


def simulate_thermostat(
    model: ThermalModel,
    inputs: HourlyInputs,
    t_min: float,
    t_max: float,
    t_start: float,
    heating_history: Sequence[int] | None = None,
    initial_state: int = 0,
) -> Plan:
    history = model.initial_history(heating_history)
    temperature = t_start
    previous = initial_state
    schedule: list[int] = []
    temperatures: list[float] = []
    for hour in range(inputs.hours):
        decision = thermostat_decision(temperature, t_min, t_max, previous)
        effective, history = model.advance(history, decision)
        temperature = model.next_temperature(
            temperature,
            effective,
            inputs.outside_temperatures[hour],
            inputs.solar_radiation[hour],
        )
        schedule.append(decision)
        temperatures.append(temperature)
        previous = decision
    return Plan(
        schedule=tuple(schedule),
        temperatures=tuple(temperatures),
        cost_by_hour=hourly_costs(schedule, inputs.prices, model.heater_power_kw),
        heater_power_kw=model.heater_power_kw,
    )

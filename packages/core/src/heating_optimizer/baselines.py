from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .inputs import HourlyInputs
from .model import ThermalModel
from .optimizer import ComfortBand, find_optimal_schedule
from .plan import Plan, hourly_costs
from .simulation import simulate_thermostat


@dataclass(frozen=True)
class MethodMetric:
    method: str
    label: str
    description: str
    cost_pln: float
    energy_kwh: float
    heating_hours: int
    hours_below_t_min: int
    deficit_kh: float
    mean_temp_c: float
    min_temp_c: float
    max_temp_c: float
    saving_pln: float
    saving_pct: float


def simulate_greedy(
    model: ThermalModel,
    inputs: HourlyInputs,
    comfort: ComfortBand,
    t_start: float,
    heating_history: Sequence[int] | None = None,
    threshold_offset: float = 0.5,
) -> Plan:
    """Reguła zachłanna: grzeje gdy cena jest poniżej mediany dobowej i temperatura zbliża się do T_min."""
    sorted_prices = sorted(inputs.prices)
    median_price = sorted_prices[len(sorted_prices) // 2]

    history = model.initial_history(heating_history)
    temperature = t_start
    schedule: list[int] = []
    temperatures: list[float] = []

    for hour in range(inputs.hours):
        price = inputs.prices[hour]
        # Reguła decyzyjna:
        if temperature <= comfort.t_min:
            decision = 1
        elif temperature >= comfort.t_max:
            decision = 0
        elif price < median_price and temperature <= comfort.t_min + threshold_offset:
            decision = 1
        else:
            decision = 0

        effective, history = model.advance(history, decision)
        temperature = model.next_temperature(
            temperature,
            effective,
            inputs.outside_temperatures[hour],
            inputs.solar_radiation[hour],
        )
        schedule.append(decision)
        temperatures.append(temperature)

    return Plan(
        schedule=tuple(schedule),
        temperatures=tuple(temperatures),
        cost_by_hour=hourly_costs(schedule, inputs.prices, model.heater_power_kw),
        heater_power_kw=model.heater_power_kw,
    )


def simulate_fixed_threshold(
    model: ThermalModel,
    inputs: HourlyInputs,
    comfort: ComfortBand,
    t_start: float,
    heating_history: Sequence[int] | None = None,
) -> Plan:
    """Utrzymuj T_min bez histerezy (grzej gdy T <= T_min, wyłącz gdy T > T_min)."""
    history = model.initial_history(heating_history)
    temperature = t_start
    schedule: list[int] = []
    temperatures: list[float] = []

    for hour in range(inputs.hours):
        decision = 1 if temperature <= comfort.t_min else 0
        effective, history = model.advance(history, decision)
        temperature = model.next_temperature(
            temperature,
            effective,
            inputs.outside_temperatures[hour],
            inputs.solar_radiation[hour],
        )
        schedule.append(decision)
        temperatures.append(temperature)

    return Plan(
        schedule=tuple(schedule),
        temperatures=tuple(temperatures),
        cost_by_hour=hourly_costs(schedule, inputs.prices, model.heater_power_kw),
        heater_power_kw=model.heater_power_kw,
    )


def compare_all_methods(
    model: ThermalModel,
    inputs: HourlyInputs,
    comfort: ComfortBand,
    t_start: float,
    overrides: dict[int, int] | None = None,
) -> list[MethodMetric]:
    """Porównuje 4 warianty sterowania: DP, Termostat, Regułę zachłanną oraz Stały próg."""
    dp_plan = find_optimal_schedule(model, inputs, comfort, t_start=t_start, overrides=overrides)
    thermostat_plan = simulate_thermostat(model, inputs, comfort.t_min, comfort.t_max, t_start)
    greedy_plan = simulate_greedy(model, inputs, comfort, t_start)
    fixed_plan = simulate_fixed_threshold(model, inputs, comfort, t_start)

    baseline_cost = thermostat_plan.cost

    plans = [
        (
            "dp",
            "Programowanie dynamiczne (DP)",
            "Globalnie optymalny 24-godzinny plan grzania z priorytetem komfortu",
            dp_plan,
        ),
        (
            "termostat",
            "Termostat z histerezą (baza)",
            "Klasyczny termostat ignorujący zmienne ceny energii (RBC)",
            thermostat_plan,
        ),
        (
            "zachlanna",
            "Reguła zachłanna (tani prąd)",
            "Dogrzewa gdy cena < mediana doby i T <= T_min + 0.5 °C",
            greedy_plan,
        ),
        (
            "progowo",
            "Stały próg T_min",
            "Włącza grzanie gdy T <= T_min, bez histerezy górnej",
            fixed_plan,
        ),
    ]

    metrics: list[MethodMetric] = []
    for code, label, desc, plan in plans:
        saving = baseline_cost - plan.cost
        saving_pct = round(100 * saving / baseline_cost, 2) if baseline_cost > 0 else 0.0
        metrics.append(
            MethodMetric(
                method=code,
                label=label,
                description=desc,
                cost_pln=round(plan.cost, 4),
                energy_kwh=round(plan.energy_kwh, 2),
                heating_hours=plan.heating_hours,
                hours_below_t_min=plan.hours_below(comfort.t_min),
                deficit_kh=round(plan.deficit(comfort.t_min), 3),
                mean_temp_c=round(plan.mean_temperature, 2),
                min_temp_c=round(min(plan.temperatures), 2),
                max_temp_c=round(max(plan.temperatures), 2),
                saving_pln=round(saving, 4),
                saving_pct=saving_pct,
            )
        )

    return metrics

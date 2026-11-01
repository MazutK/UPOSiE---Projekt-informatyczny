from __future__ import annotations

import io
from collections.abc import Sequence
from dataclasses import dataclass

from .inputs import HourlyInputs
from .model import ThermalModel
from .optimizer import ComfortBand, find_optimal_schedule
from .simulation import simulate_thermostat


@dataclass(frozen=True)
class SensitivityRow:
    value: float
    dp_cost_pln: float
    thermostat_cost_pln: float
    saving_pln: float
    saving_pct: float
    dp_heating_hours: int
    thermostat_heating_hours: int
    dp_hours_below_t_min: int
    thermostat_hours_below_t_min: int
    dp_mean_temp_c: float


@dataclass(frozen=True)
class SensitivityResult:
    parameter: str
    scenario: str
    rows: list[SensitivityRow]


DEFAULT_T_MIN_GRID = (20.0, 20.5, 21.0, 21.5, 22.0)
DEFAULT_OVERSHOOT_GRID = (0.0, 0.5, 1.0, 1.5, 2.0)


def run_sensitivity_analysis(
    model: ThermalModel,
    inputs: HourlyInputs,
    parameter: str = "t_min",
    values: Sequence[float] | None = None,
    scenario_name: str = "doba",
    t_min: float = 21.0,
    t_max: float = 22.5,
    t_start: float = 21.8,
    max_overshoot: float = 1.0,
    overrides: dict[int, int] | None = None,
) -> SensitivityResult:
    """Przeprowadza analizę wrażliwości dla siatki wartości zadanego parametru."""
    if parameter not in ("t_min", "max_overshoot"):
        raise ValueError(
            f"Nieobsługiwany parametr wrażliwości: '{parameter}'. Wybierz 't_min' lub 'max_overshoot'."
        )

    if values is None or len(values) == 0:
        values = DEFAULT_T_MIN_GRID if parameter == "t_min" else DEFAULT_OVERSHOOT_GRID

    sorted_values = sorted(set(values))
    rows: list[SensitivityRow] = []

    for val in sorted_values:
        if parameter == "t_min":
            current_t_min = float(val)
            current_t_max = max(current_t_min + 0.5, t_max)
            current_overshoot = max_overshoot
        else:
            current_t_min = t_min
            current_t_max = t_max
            current_overshoot = float(val)

        comfort = ComfortBand(
            t_min=current_t_min,
            t_max=current_t_max,
            max_overshoot=current_overshoot,
        )

        dp = find_optimal_schedule(model, inputs, comfort, t_start=t_start, overrides=overrides)
        thermostat = simulate_thermostat(model, inputs, current_t_min, current_t_max, t_start)

        saving = thermostat.cost - dp.cost
        saving_pct = round(100.0 * saving / thermostat.cost, 2) if thermostat.cost > 0 else 0.0

        rows.append(
            SensitivityRow(
                value=round(val, 2),
                dp_cost_pln=round(dp.cost, 4),
                thermostat_cost_pln=round(thermostat.cost, 4),
                saving_pln=round(saving, 4),
                saving_pct=saving_pct,
                dp_heating_hours=dp.heating_hours,
                thermostat_heating_hours=thermostat.heating_hours,
                dp_hours_below_t_min=dp.hours_below(current_t_min),
                thermostat_hours_below_t_min=thermostat.hours_below(current_t_min),
                dp_mean_temp_c=round(dp.mean_temperature, 2),
            )
        )

    return SensitivityResult(parameter=parameter, scenario=scenario_name, rows=rows)


def export_sensitivity_csv(result: SensitivityResult) -> str:
    """Eksportuje wyniki analizy wrażliwości do łańcucha CSV."""
    buf = io.StringIO()
    buf.write(
        f"parametr_{result.parameter},dp_koszt_pln,termostat_koszt_pln,oszczednosc_pln,oszczednosc_proc,dp_godziny_grzania,termostat_godziny_grzania,dp_ponizej_tmin,termostat_ponizej_tmin,dp_srednia_temp_c\n"
    )
    for r in result.rows:
        buf.write(
            f"{r.value},{r.dp_cost_pln:.4f},{r.thermostat_cost_pln:.4f},{r.saving_pln:.4f},{r.saving_pct:.2f},{r.dp_heating_hours},{r.thermostat_heating_hours},{r.dp_hours_below_t_min},{r.thermostat_hours_below_t_min},{r.dp_mean_temp_c:.2f}\n"
        )
    return buf.getvalue()

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    schedule: tuple[int, ...]
    temperatures: tuple[float, ...]
    cost_by_hour: tuple[float, ...]
    heater_power_kw: float

    @property
    def hours(self) -> int:
        return len(self.schedule)

    @property
    def cost(self) -> float:
        return sum(self.cost_by_hour)

    @property
    def heating_hours(self) -> int:
        return sum(self.schedule)

    @property
    def energy_kwh(self) -> float:
        return self.heating_hours * self.heater_power_kw

    @property
    def mean_temperature(self) -> float:
        return sum(self.temperatures) / len(self.temperatures)

    def hours_below(self, t_min: float) -> int:
        return sum(1 for t in self.temperatures if t < t_min - 1e-9)

    def deficit(self, t_min: float) -> float:
        return sum(max(0.0, t_min - t) for t in self.temperatures)


def hourly_costs(
    schedule: Sequence[int], prices: Sequence[float], heater_power_kw: float
) -> tuple[float, ...]:
    return tuple(
        prices[hour] * heater_power_kw if state == 1 else 0.0 for hour, state in enumerate(schedule)
    )

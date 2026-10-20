from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ThermalModel:
    alpha: float
    beta: float
    gamma: float = 0.0
    constant: float = 0.0
    delay: int = 2
    heater_power_kw: float = 1.5

    def __post_init__(self) -> None:
        if self.delay < 0:
            raise ValueError("delay must not be negative")
        if self.heater_power_kw <= 0:
            raise ValueError("heater_power_kw must be positive")

    @classmethod
    def from_dict(cls, params: Mapping[str, float]) -> ThermalModel:
        return cls(
            alpha=float(params["ALPHA"]),
            beta=float(params["BETA"]),
            gamma=float(params.get("GAMMA", 0.0)),
            constant=float(params.get("CONSTANT", 0.0)),
            delay=int(params.get("DELAY", 2)),
            heater_power_kw=float(params.get("HEMS_HEATER_POWER_KW", 1.5)),
        )

    @classmethod
    def from_json(cls, path: str | Path) -> ThermalModel:
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def next_temperature(
        self,
        temperature: float,
        effective_heating: int,
        outside_temperature: float,
        solar_radiation: float,
    ) -> float:
        value = (
            temperature
            - self.alpha * (temperature - outside_temperature)
            + self.beta * effective_heating
            + self.gamma * solar_radiation
            + self.constant
        )
        return round(value, 2)

    def initial_history(self, heating_history: Sequence[int] | None = None) -> tuple[int, ...]:
        if heating_history is not None and len(heating_history) == self.delay:
            return tuple(int(state) for state in heating_history)
        return (0,) * self.delay

    def advance(self, history: tuple[int, ...], decision: int) -> tuple[int, tuple[int, ...]]:
        if self.delay == 0:
            return decision, ()
        return history[0], history[1:] + (decision,)

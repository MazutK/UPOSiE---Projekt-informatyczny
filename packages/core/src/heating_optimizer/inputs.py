from __future__ import annotations

import csv
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

CSV_COLUMNS = ("hour", "price_pln_kwh", "outside_temp_c", "solar_radiation_wm2")


@dataclass(frozen=True)
class HourlyInputs:
    prices: tuple[float, ...]
    outside_temperatures: tuple[float, ...]
    solar_radiation: tuple[float, ...]

    def __post_init__(self) -> None:
        lengths = {len(self.prices), len(self.outside_temperatures), len(self.solar_radiation)}
        if len(lengths) != 1:
            raise ValueError(
                "prices, outside_temperatures and solar_radiation must have the same length"
            )
        if not self.prices:
            raise ValueError("inputs must cover at least one hour")

    @classmethod
    def of(
        cls,
        prices: Sequence[float],
        outside_temperatures: Sequence[float],
        solar_radiation: Sequence[float],
    ) -> HourlyInputs:
        return cls(
            tuple(float(v) for v in prices),
            tuple(float(v) for v in outside_temperatures),
            tuple(float(v) for v in solar_radiation),
        )

    @classmethod
    def from_csv(cls, path: str | Path) -> HourlyInputs:
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            missing = set(CSV_COLUMNS) - set(reader.fieldnames or ())
            if missing:
                raise ValueError(f"{path}: missing columns {sorted(missing)}")
            rows = sorted(reader, key=lambda row: int(row["hour"]))
        return cls.of(
            [row["price_pln_kwh"] for row in rows],
            [row["outside_temp_c"] for row in rows],
            [row["solar_radiation_wm2"] for row in rows],
        )

    @property
    def hours(self) -> int:
        return len(self.prices)

    def window(self, start: int, length: int) -> HourlyInputs:
        if start < 0 or length < 1 or start + length > self.hours:
            raise ValueError(f"window {start}..{start + length} is outside 0..{self.hours}")
        end = start + length
        return HourlyInputs(
            self.prices[start:end],
            self.outside_temperatures[start:end],
            self.solar_radiation[start:end],
        )

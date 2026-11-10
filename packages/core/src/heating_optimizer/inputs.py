from __future__ import annotations

import csv
import math
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
    def from_csv(cls, path: str | Path, expected_hours: int | None = None) -> HourlyInputs:
        """Wczytuje dobę z CSV i sprawdza ją przed obliczeniem.

        Godziny muszą być kolejne od 0 (bez luk i duplikatów), a wartości skończone,
        nasłonecznienie >= 0. Gdy podano ``expected_hours``, plik musi mieć dokładnie
        tyle godzin. Każda niezgodność to ``ValueError`` z opisem — nie plan na krótszą dobę.
        """
        with open(path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            missing = set(CSV_COLUMNS) - set(reader.fieldnames or ())
            if missing:
                raise ValueError(f"{path}: missing columns {sorted(missing)}")
            raw_rows = list(reader)

        name = Path(path).name
        parsed: dict[int, tuple[float, float, float]] = {}
        for line, row in enumerate(raw_rows, start=2):
            try:
                hour = int(row["hour"])
                values = tuple(float(row[column]) for column in CSV_COLUMNS[1:])
            except (TypeError, ValueError):
                raise ValueError(f"{name}: wiersz {line} ma niepoprawną liczbę") from None
            if not all(math.isfinite(v) for v in values):
                raise ValueError(f"{name}: godzina {hour} ma wartość pustą lub nieskończoną")
            if values[2] < 0:
                raise ValueError(f"{name}: godzina {hour} ma ujemne nasłonecznienie")
            if hour in parsed:
                raise ValueError(f"{name}: godzina {hour} występuje więcej niż raz")
            parsed[hour] = (values[0], values[1], values[2])

        hours = sorted(parsed)
        expected = list(range(expected_hours if expected_hours is not None else len(hours)))
        if hours != expected:
            missing_hours = sorted(set(expected) - set(hours))
            extra_hours = sorted(set(hours) - set(expected))
            details = []
            if missing_hours:
                details.append(f"brakujące godziny {missing_hours}")
            if extra_hours:
                details.append(f"nadmiarowe godziny {extra_hours}")
            if not details:
                details.append("brak wierszy")
            raise ValueError(f"{name}: niepełna doba — " + ", ".join(details))

        return cls.of(
            [parsed[h][0] for h in hours],
            [parsed[h][1] for h in hours],
            [parsed[h][2] for h in hours],
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

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .inputs import HourlyInputs
from .model import ThermalModel

BUNDLED_DATA_DIR = Path(__file__).resolve().parent / "data"
PARAMS_FILE = "parametry.json"
DATA_DIR_ENV = "HEMS_DATA_DIR"

DESCRIPTIONS = {
    "doba_zmienna_cena": "łagodna zima, typowy przebieg cen",
    "doba_szczyt_wieczorny": "ostry szczyt cenowy 17-21",
    "doba_mroz": "mróz do -10 °C",
    "doba_slonecznie": "bezchmurny dzień zimowy",
}


@dataclass(frozen=True)
class Scenario:
    name: str
    path: Path
    description: str
    hours: int


def search_dirs() -> tuple[Path, ...]:
    extra = os.environ.get(DATA_DIR_ENV)
    if extra:
        return (Path(extra).expanduser().resolve(), BUNDLED_DATA_DIR)
    return (BUNDLED_DATA_DIR,)


def _count_hours(path: Path) -> int:
    with open(path, encoding="utf-8", newline="") as f:
        return max(0, sum(1 for _ in f) - 1)


def available() -> tuple[Scenario, ...]:
    found: dict[str, Scenario] = {}
    for directory in reversed(search_dirs()):
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.csv")):
            found[path.stem] = Scenario(
                name=path.stem,
                path=path,
                description=DESCRIPTIONS.get(path.stem, "dane własne"),
                hours=_count_hours(path),
            )
    return tuple(found[name] for name in sorted(found))


def resolve(name: str) -> Path:
    candidate = Path(name)
    if candidate.suffix == ".csv" and candidate.is_file():
        return candidate.resolve()
    stem = candidate.stem or name
    if "/" in name or "\\" in name:
        raise FileNotFoundError(f"nie znaleziono pliku {name}")
    for directory in search_dirs():
        path = directory / f"{stem}.csv"
        if path.is_file():
            return path
    known = ", ".join(s.name for s in available())
    raise FileNotFoundError(f"nieznany scenariusz '{name}'; dostępne: {known}")


def load_inputs(name: str) -> HourlyInputs:
    return HourlyInputs.from_csv(resolve(name))


def default_model() -> ThermalModel:
    for directory in search_dirs():
        path = directory / PARAMS_FILE
        if path.is_file():
            return ThermalModel.from_json(path)
    raise FileNotFoundError(f"nie znaleziono {PARAMS_FILE}")

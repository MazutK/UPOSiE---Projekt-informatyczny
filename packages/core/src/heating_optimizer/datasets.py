from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from .inputs import HourlyInputs
from .model import ThermalModel

BUNDLED_DATA_DIR = Path(__file__).resolve().parent / "data"
PARAMS_FILE = "parametry.json"
DATA_DIR_ENV = "HEMS_DATA_DIR"
LIVE_DIR_ENV = "HEMS_LIVE_DIR"
LIVE_SCENARIO = "doba_live"
LIVE_META_SUFFIX = ".meta.json"

DESCRIPTIONS = {
    "doba_zmienna_cena": "łagodna zima, typowy przebieg cen",
    "doba_szczyt_wieczorny": "ostry szczyt cenowy 17-21",
    "doba_mroz": "mróz do -10 °C",
    "doba_slonecznie": "bezchmurny dzień zimowy",
    "doba_live": "doba rzeczywista z PSE i Open-Meteo",
}


@dataclass(frozen=True)
class Scenario:
    name: str
    path: Path
    description: str
    hours: int


def live_data_dir() -> Path:
    """Katalog doby live (Z-09): poza śledzonymi plikami pakietu.

    Domyślnie `data-local/` w katalogu repozytorium (jest w .gitignore);
    w kontenerze ustawiane przez zmienną HEMS_LIVE_DIR.
    """
    configured = os.environ.get(LIVE_DIR_ENV)
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[4] / "data-local"


def search_dirs() -> tuple[Path, ...]:
    dirs: list[Path] = []
    extra = os.environ.get(DATA_DIR_ENV)
    if extra:
        dirs.append(Path(extra).expanduser().resolve())
    dirs.append(live_data_dir())
    dirs.append(BUNDLED_DATA_DIR)
    return tuple(dirs)


def read_live_meta(csv_path: Path) -> dict[str, str] | None:
    """Metadane doby live (Z-08): data doby, źródło, czas pobrania. None, gdy brak."""
    meta_path = csv_path.with_name(csv_path.stem + LIVE_META_SUFFIX)
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return meta if isinstance(meta, dict) else None


def _describe(path: Path) -> str:
    description = DESCRIPTIONS.get(path.stem, "dane własne")
    if path.stem == LIVE_SCENARIO:
        meta = read_live_meta(path)
        if meta and meta.get("data_date"):
            description += f" — doba {meta['data_date']} ({meta.get('source', '?')})"
        else:
            description += " — data doby nieznana"
    return description


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
                description=_describe(path),
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

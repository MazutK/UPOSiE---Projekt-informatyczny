"""Lab 6, ocena usprawnienia: ile razy analiza wrażliwości symuluje termostat i ile to trwa.

Uruchomienie (z katalogu repozytorium):
    python scripts/measure_sensitivity.py

Liczy wywołania simulate_thermostat i find_optimal_schedule w run_sensitivity_analysis
(logging na stderr) oraz medianę czasu z 7 powtórzeń dla obu parametrów na tej samej dobie
(data/processed/doba-live.csv, domyślne siatki). Wypisuje skrót wyników, żeby porównać
wiersze przed i po zmianie (muszą być identyczne).
"""

from __future__ import annotations

import hashlib
import logging
import statistics
import sys
import time
from pathlib import Path

try:
    import heating_optimizer  # noqa: F401
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "core" / "src"))

from heating_optimizer import HourlyInputs, default_model
from heating_optimizer import sensitivity as module

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("measure_sensitivity")

DATA = Path(__file__).resolve().parents[1] / "data" / "processed" / "doba-live.csv"
REPEATS = 7


def counted(name: str, function, counter: dict[str, int]):
    def wrapper(*args, **kwargs):
        counter[name] += 1
        return function(*args, **kwargs)

    return wrapper


def main() -> None:
    inputs = HourlyInputs.from_csv(DATA)
    model = default_model()
    original = {
        "simulate_thermostat": module.simulate_thermostat,
        "find_optimal_schedule": module.find_optimal_schedule,
    }
    for parameter in ("t_min", "max_overshoot"):
        counter = dict.fromkeys(original, 0)
        for name, function in original.items():
            setattr(module, name, counted(name, function, counter))
        try:
            result = module.run_sensitivity_analysis(model, inputs, parameter=parameter)
        finally:
            for name, function in original.items():
                setattr(module, name, function)

        times = []
        for _ in range(REPEATS):
            start = time.perf_counter()
            module.run_sensitivity_analysis(model, inputs, parameter=parameter)
            times.append(time.perf_counter() - start)

        digest = hashlib.md5(repr(result.rows).encode()).hexdigest()[:12]
        logger.info(
            "%s: %d wartości, termostat %d×, DP %d×, mediana %.1f ms (n=%d), wynik %s",
            parameter,
            len(result.rows),
            counter["simulate_thermostat"],
            counter["find_optimal_schedule"],
            1000 * statistics.median(times),
            REPEATS,
            digest,
        )


if __name__ == "__main__":
    main()

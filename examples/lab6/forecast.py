"""Lab 6 — przykład z instrukcji: CLI prognozy średnią ruchomą (tylko biblioteka standardowa).

Uruchomienie (z katalogu repozytorium):
    python examples/lab6/forecast.py examples/lab6/history.json examples/lab6/results/run-01.json --window 3

Oczekiwane: "Prognoza: 14.00 zgloszenia/dzien". Ponowne uruchomienie z tą samą ścieżką
wyniku kończy się błędem (zapis tylko do nowego pliku).
To ćwiczenie demonstracyjne, odseparowane od kodu projektu (packages/, apps/, scripts/).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

UNIT = "zgloszenia/dzien"


def forecast(history: list[float], window: int) -> float:
    """Średnia z ostatnich `window` obserwacji."""
    if isinstance(window, bool) or not isinstance(window, int) or window < 1:
        raise ValueError("okno musi być dodatnią liczbą całkowitą")
    if not isinstance(history, list):
        raise ValueError("historia musi być listą liczb")
    if len(history) < window:
        raise ValueError(f"za krótka historia: {len(history)} obserwacji, okno {window}")
    for value in history:
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValueError(f"wartość {value!r} nie jest liczbą")
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"wartość {value!r} musi być skończona i nieujemna")
    return sum(history[-window:]) / window


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prognoza średnią ruchomą")
    parser.add_argument("input", type=Path, help="plik JSON z listą obserwacji")
    parser.add_argument("output", type=Path, help="nowy plik JSON z wynikiem")
    parser.add_argument("--window", type=int, default=3)
    args = parser.parse_args(argv)
    try:
        if args.output.resolve() == args.input.resolve():
            raise ValueError("wynik nie może nadpisać pliku wejściowego")
        if args.output.exists():
            raise ValueError(f"plik {args.output} już istnieje — podaj nową nazwę")
        with args.input.open(encoding="utf-8-sig") as stream:
            history = json.load(stream)
        value = forecast(history, args.window)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        result = {"forecast": value, "unit": UNIT, "method": "moving_average", "window": args.window}
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
    except (OSError, ValueError) as error:
        print(f"Błąd: {error}", file=sys.stderr)
        return 1
    print(f"Prognoza: {value:.2f} {UNIT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

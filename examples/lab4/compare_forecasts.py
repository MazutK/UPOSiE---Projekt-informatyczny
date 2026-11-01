import argparse
import csv
import math
from datetime import date
from pathlib import Path
from statistics import mean

parser = argparse.ArgumentParser()
parser.add_argument("input", type=Path)
parser.add_argument("output", type=Path, help="katalog wyników")
parser.add_argument("--window", type=int, default=3)
parser.add_argument("--start", type=int, default=8, help="liczba dni początkowej historii")
args = parser.parse_args()

with args.input.open(encoding="utf-8-sig", newline="") as stream:
    rows = list(csv.DictReader(stream))
dates = [date.fromisoformat(row["data"]) for row in rows]
values = [float(row["zgloszenia"]) for row in rows]

if not 1 <= args.window <= args.start < len(rows):
    parser.error("Wymagane: 1 <= window <= start < liczba obserwacji")
if any((b - a).days != 1 for a, b in zip(dates, dates[1:])):
    parser.error("Daty muszą być kolejnymi dniami, bez powtórzeń")
if not all(math.isfinite(v) and v >= 0 and v.is_integer() for v in values):
    parser.error("Liczby zgłoszeń muszą być nieujemnymi liczbami całkowitymi")

observations = []
for i in range(args.start, len(rows)):
    baseline = values[i - 1]
    method = mean(values[i - args.window:i])
    observations.append({
        "data": dates[i].isoformat(),
        "rzeczywiste": values[i],
        "bazowy": baseline,
        "srednia": method,
        "blad_bazowy": abs(values[i] - baseline),
        "blad_srednia": abs(values[i] - method),
    })

comparison = []
for variant, column, window in [
    ("ostatnia_wartosc", "blad_bazowy", 1),
    ("srednia_ruchoma", "blad_srednia", args.window),
]:
    comparison.append({
        "wariant": variant,
        "okno": window,
        "start": args.start,
        "n": len(observations),
        "mae": mean(row[column] for row in observations),
        "jednostka": "zgloszenia",
    })

args.output.mkdir(parents=True, exist_ok=True)
for name, records in [("observations.csv", observations), ("comparison.csv", comparison)]:
    destination = args.output / name
    if destination.resolve() == args.input.resolve():
        parser.error("Wynik nie może nadpisać pliku wejściowego")
    with destination.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

for result in comparison:
    print(f"{result['wariant']}: MAE={result['mae']:.3f}, n={result['n']}")

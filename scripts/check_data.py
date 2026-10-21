import argparse
from pathlib import Path
import pandas as pd
EXPECTED = ("hour", "price_pln_kwh", "outside_temp_c", "solar_radiation_wm2")
def check(path: Path) -> None:
    frame = pd.read_csv(path)
    errors: list[str] = []
    if tuple(frame.columns) != EXPECTED:
        errors.append(f"kolumny: {list(frame.columns)} != {list(EXPECTED)}")
    if len(frame) != 24:
        errors.append(f"rekordy: {len(frame)} != 24")
    if frame["hour"].duplicated().any() or set(frame["hour"]) != set(range(24)):
        errors.append("hour musi byc unikalne i pokrywac 0..23")
    if frame[list(EXPECTED)].isna().any().any():
        errors.append("braki w kolumnach wynikowych")
    if frame["solar_radiation_wm2"].lt(0).any():
        errors.append("ujemne naslonecznienie")
    if not frame["outside_temp_c"].between(-40, 45).all():
        errors.append("temperatura poza -40..45 C")
    print(f"Plik: {path}")
    print(f"Rekordy: {len(frame)}")
    print(f"Braki: {int(frame.isna().sum().sum())}")
    print(f"Duplikaty hour: {int(frame['hour'].duplicated().sum())}")
    if errors:
        raise SystemExit("Kontrola niezaliczona:\n- " + "\n- ".join(errors))
    print("Kontrola OK")
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    check(parser.parse_args().input)
if __name__ == "__main__":
    main()
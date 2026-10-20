import argparse
import json
from pathlib import Path

import pandas as pd


def load_pse(path: Path) -> pd.DataFrame:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["value"] if isinstance(payload, dict) else payload
    frame = pd.DataFrame(rows)
    time_col = "dtime" if "dtime" in frame.columns else "udtczas"
    # PSE podaje koniec kwadransa (00:15 ... 24:00), cofamy na jego poczatek,
    # zeby kwadranse 00:00-01:00 trafily do godziny 0.
    frame["ts"] = pd.to_datetime(frame[time_col]) - pd.Timedelta(minutes=15)
    frame["price_mwh"] = pd.to_numeric(frame["rce_pln"], errors="raise")
    return frame[["ts", "price_mwh"]]


def load_weather(path: Path) -> pd.DataFrame:
    payload = json.loads(path.read_text(encoding="utf-8"))
    hourly = payload["hourly"]
    frame = pd.DataFrame(
        {
            "ts": pd.to_datetime(hourly["time"]),
            "outside_temp_c": hourly["temperature_2m"],
            "solar_radiation_wm2": hourly["shortwave_radiation"],
        }
    )
    frame["outside_temp_c"] = pd.to_numeric(frame["outside_temp_c"], errors="raise")
    frame["solar_radiation_wm2"] = pd.to_numeric(frame["solar_radiation_wm2"], errors="raise")
    return frame


def prepare(prices: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    hourly_price = (
        prices.assign(hour_ts=prices["ts"].dt.floor("h"))
        .groupby("hour_ts", as_index=False)["price_mwh"]
        .mean()
    )
    hourly_price["price_pln_kwh"] = hourly_price["price_mwh"] / 1000.0

    weather = weather.assign(hour_ts=weather["ts"].dt.floor("h"))
    merged = hourly_price.merge(weather, on="hour_ts", how="inner")
    merged = merged.sort_values("hour_ts")
    merged["hour"] = merged["hour_ts"].dt.hour

    clean = merged.dropna(
        subset=["hour", "price_pln_kwh", "outside_temp_c", "solar_radiation_wm2"]
    ).copy()
    if clean["solar_radiation_wm2"].lt(0).any():
        raise ValueError("naslonecznienie nie moze byc ujemne")
    return clean[["hour", "price_pln_kwh", "outside_temp_c", "solar_radiation_wm2"]]


def main() -> None:
    parser = argparse.ArgumentParser(description="Składa dobę RCE + pogodę do CSV silnika.")
    parser.add_argument("pse", type=Path, help="surowy JSON PSE")
    parser.add_argument("weather", type=Path, help="surowy JSON Open-Meteo")
    parser.add_argument("output", type=Path, help="docelowy CSV")
    args = parser.parse_args()

    raw_prices = load_pse(args.pse)
    raw_weather = load_weather(args.weather)
    clean = prepare(raw_prices, raw_weather)

    if clean["hour"].nunique() != 24 or len(clean) != 24:
        raise SystemExit(f"Oczekiwano 24 godzin, otrzymano {len(clean)}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(args.output, index=False, float_format="%.4f")

    print(f"PSE kwadranse: {len(raw_prices)}")
    print(f"Open-Meteo godziny: {len(raw_weather)}")
    print(f"Wynik: {len(clean)} -> {args.output}")


if __name__ == "__main__":
    main()

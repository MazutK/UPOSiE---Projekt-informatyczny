# Przetwarzanie danych
## Dobór narzędzi
- Źródło i format danych: publiczne API (JSON) — PSE RCE i Open-Meteo Archive
- Narzędzie główne: Python + pandas (`scripts/prepare_data.py`)
- Dlaczego pasuje do tego źródła i zadania: dwa JSON-y trzeba złączyć, przeliczyć jednostki i zapisać CSV w formacie silnika; skrypt da się odpalić ponownie
- Narzędzie pomocnicze: Postman (kolekcja w `api/`) — sprawdzenie statusu i pól przed zapisem próbki
- Wynik zapisany w repozytorium: `data/raw/*.json`, `data/processed/doba-live.csv`, `scripts/prepare_data.py`, `scripts/check_data.py`
## Kroki
| Krok | Operacja | Powód | Wpływ na dane |
|---|---|---|---|
| 1 | Średnia RCE z 15 min do 1 h | Silnik liczy krok 1 h, API PSE podaje kwadranse | ok. 96 wierszy cen → 24 |
| 2 | `rce_pln / 1000` | Źródło jest w zł/MWh, silnik w zł/kWh | wartości ~1000× mniejsze |
| 3 | Inner join z pogodą po godzinie | komplet wejścia: cena + T_zew + słońce | przy pełnej dobie zostaje 24 |
| 4 | `dropna` na kolumnach wynikowych | brak godziny nie może wejść do DP jako ciche 0 | ubytek tylko gdy źródło nie dosłało godziny |

Ujemnej ceny RCE nie usuwamy — na rynku bywa ujemna. Ujemne nasłonecznienie jest błędem i przerywa skrypt.
## Kontrola jakości
| Kontrola | Wynik | Działanie lub ograniczenie |
|---|---|---|
| Liczba rekordów | surowe: ~96 RCE + 24 pogoda → 24 po skrypcie | inna liczba = stop |
| Brakujące wartości | w wyniku niedozwolone | wiersz bez ceny albo pogody odrzucony |
| Duplikaty | `hour` 0..23 unikalne | `scripts/check_data.py` |
| Zakresy i jednostki | zł/kWh, °C, W/m²; T w −40..45 | słońce < 0 = błąd |
| Powtarzalność | ponowne odpalenie skryptu na tych samych raw daje ten sam CSV | raw nie edytujemy ręcznie |
## Ograniczenia
- Próbka to jedna doba i jedna lokalizacja (Warszawa), nie reprezentuje całego roku ani innego budynku.
- Model cieplny jest z jednego budynku referencyjnego — pogoda z Warszawy jest przybliżeniem.
- Nie da się jeszcze potwierdzić, jak błąd prognozy pogody psuje oszczędność DP vs termostat: do tego potrzeba wielu dób (poza Lab 3).
- Wbudowane `doba_*.csv` w `packages/core` zostają jako demo offline.
## Powtarzalność
Usunąć `data/processed/doba-live.csv` i ponownie:
`python scripts/prepare_data.py data/raw/pse-rce-sample.json data/raw/open-meteo-sample.json data/processed/doba-live.csv`
Struktura ma wrócić: 24 wiersze, 4 kolumny.

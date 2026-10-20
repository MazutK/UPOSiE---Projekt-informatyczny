# Słownik danych
Jedna obserwacja po przetworzeniu = jedna godzina doby dla budynku referencyjnego.
Źródła surowe: Open-Meteo Archive i PSE RCE. Znaczenie pól potwierdzone w dokumentacji źródeł, nie zgadywane z nazwy.
## Pola po przetworzeniu (`data/processed/`)
| Pole | Znaczenie | Typ | Jednostka | Przykładowa wartość | Czy może być puste? |
|---|---|---|---|---|---|
| hour | Godzina doby, 0 = 00:00–01:00 czasu Europe/Warsaw | INTEGER | brak | 17 | nie |
| price_pln_kwh | Średnia RCE z czterech kwadransów, przeliczona z PLN/MWh | REAL | zł/kWh | 0.4123 | nie |
| outside_temp_c | Temperatura powietrza na 2 m | REAL | °C | 8.4 | nie |
| solar_radiation_wm2 | Promieniowanie krótkofalowe | REAL | W/m² | 120.0 | nie |
## Pola surowe — Open-Meteo
| Pole | Znaczenie | Typ | Jednostka | Przykładowa wartość | Czy może być puste? |
|---|---|---|---|---|---|
| hourly.time | Znacznik czasu godziny | TEXT | ISO8601 | 2026-10-13T00:00 | nie |
| hourly.temperature_2m | Temperatura powietrza na 2 m | REAL | °C | 8.4 | tak |
| hourly.shortwave_radiation | Promieniowanie krótkofalowe | REAL | W/m² | 0.0 | tak |
## Pola surowe — PSE RCE
| Pole | Znaczenie | Typ | Jednostka | Przykładowa wartość | Czy może być puste? |
|---|---|---|---|---|---|
| rce_pln | Rynkowa cena energii w kwadransie | REAL | zł/MWh | 412.34 | nie |
| dtime | Czas końca okresu RCE | TEXT | data-czas | 2026-10-13 00:15:00 | nie |
| period | Przedział kwadransa | TEXT | brak | 00:00 - 00:15 | nie |
| business_date | Doba handlowa | DATE | dzień | 2026-10-13 | nie |
Uwagi:
- Silnik aplikacji oczekuje dokładnie czterech kolumn z pierwszej tabeli. Tego formatu nie zmieniamy.
- RCE może być ujemna — to nie jest błąd importu.
- `rce_pln` jest za MWh; w pliku przetworzonym dzielimy przez 1000.
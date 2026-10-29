# Lab 4 — porównanie metod: termostat vs plan DP

Kolejność edycji tego pliku: Osoba 1 → 2 → 3 → 4 → 5 → 6.
Każda osoba przed edycją robi `git pull` i podmienia **tylko swój** blok `_(uzupełnia …)_`.

## 1. Pytanie i wymaganie

**Pytanie:** Czy plan grzania z programowania dynamicznego (DP) daje niższy koszt energii
na jednej rzeczywistej dobie niż zwykły termostat, bez pogorszenia komfortu?

**Wymagania z `docs/problem.md`:** R4 (porównanie z klasycznym termostatem),
R2 (uwzględnienie cen), R6 (koszt w zł), R3 (pasmo komfortu).

**Decyzja, którą wspiera wynik:** czy warto proponować użytkownikowi plan DP zamiast
termostatu przy taryfie dynamicznej.

**Ścieżka z instrukcji:** symulacja / analiza kosztów procesu — oba warianty uruchomione
na tych samych danych wejściowych i tym samym modelu budynku. Brak losowania.

## 2. Dane

| Element | Ustalenie |
|---|---|
| Plik | `data/processed/doba-live.csv` (wynik Lab 3, bez zmian) |
| Jak powstał | `python scripts/prepare_data.py data/raw/pse-rce-sample.json data/raw/open-meteo-sample.json data/processed/doba-live.csv` |
| Wersja | commit, w którym dodano plik; MD5 `729ecf79df5d39a3ef5e9c64d8be77fe` |
| Zakres | doba 2026-10-13, Warszawa, ceny RCE PSE + pogoda Open-Meteo (archiwum) |
| Liczba obserwacji | 24 |
| Jednostka obserwacji | jedna godzina doby dla budynku referencyjnego |
| Kontrola Lab 3 | `python scripts/check_data.py data/processed/doba-live.csv` → `Kontrola OK` |
| Model budynku | `packages/core/src/heating_optimizer/data/parametry.json` (α, β, γ, c, opóźnienie 2 h, grzałka 1,5 kW) |

## 3. Warunki porównania (ustalone przed uruchomieniem)

| Element | Ustalenie |
|---|---|
| Pytanie i wymaganie | jak w p. 1 (R4, R2, R6, R3) |
| Dane | `data/processed/doba-live.csv`, 24 h, 2026-10-13 |
| Wariant bazowy | termostat z histerezą: grzej gdy T ≤ T_min, wyłącz gdy T ≥ T_max, ceny ignoruje (`simulate_thermostat`) |
| Metoda | DP: najtańszy ciąg 24 decyzji 0/1, najpierw kara za zimno, potem koszt (`find_optimal_schedule`) |
| Parametry | T_min = 21,0 °C, T_max = 22,5 °C, T_start = 21,8 °C, max_overshoot = 1,0 °C, krok 1 h |
| Stan początkowy | T = 21,8 °C, grzałka wyłączona, historia opóźnienia = [0, 0] |
| Miara główna | koszt energii za dobę [zł] — mniej = lepiej |
| Miara komfortu | liczba godzin poniżej T_min [h] — mniej = lepiej |
| Kryterium praktyczne | DP oszczędza ≥ 5 % kosztu termostatu **i** nie ma więcej godzin poniżej T_min (próg 5 % to założenie zespołu) |
| Warunki oceny | te same 24 godziny, te same ceny, pogoda, model i pasmo dla obu wariantów |
| Próba wrażliwości | T_min 21,0 → 21,5 °C (reszta bez zmian), wynik w `results/lab4/sensitivity/` |
| Odtworzenie | polecenia w `README.md`, sekcja Lab 4; brak losowania, ziarno niepotrzebne |

## 4. Źródła i uzasadnienie metody

_(uzupełnia Osoba 2)_

## 5. Implementacja wariantów

_(uzupełnia Osoba 3)_

## 6. Wyniki i próba wrażliwości

_(uzupełnia Osoba 4)_

## 7. Kontrola obliczeń

_(uzupełnia Osoba 5)_

## 8. Wnioski i ograniczenia

_(uzupełnia Osoba 6)_

## 9. Odtworzenie i użycie agenta AI

_(uzupełnia Osoba 6)_

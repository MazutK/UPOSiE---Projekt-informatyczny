# Lab 7: testowanie i ocena rezultatów

Podział sekcji: 1–2 Karol Brzozowski, 3 i 6 Sebastian Król, 4–5 i 7 Sebastian Rączka
(link do PR z przeglądem kodu w 4: Kacper Mazur), wyniki testu integracyjnego w 2: Oskar Wysocki.
Każda osoba przed edycją robi `git pull` i uzupełnia **tylko swoją** sekcję.

## 1. Zakres, wersja kodu i danych

_Karol Brzozowski._

**Co sprawdzamy:** główny przepływ UC-01 (`docs/architecture.md`): dla doby (ceny + pogoda)
i pasma komfortu silnik wyznacza najtańszy plan grzania na 24 h (DP) i porównuje go z termostatem.
Testy logiki obejmują pakiet `packages/core` (`heating_optimizer`): model cieplny, regułę termostatu,
optymalizator DP, wczytanie i walidację doby, obliczenie kosztu i godzin poniżej `T_min`.

**Poza zakresem testów logiki:** API (`apps/api`), GUI (`apps/web`), pobieranie danych z PSE
i Open-Meteo (zewnętrzne API sprawdzane osobno, żeby zmiana danych dostawcy nie wyglądała na błąd
algorytmu), Docker. Główny przepływ przez interfejs: test integracyjny (Oskar Wysocki).

| Element | Wersja |
|---|---|
| Kod (sprawdzana implementacja) | `main` @ `12c1a95` (Merge PR #6 `feature/lab6-integracja`, 2026-11-17) |
| Próbka danych | `data/processed/doba-live.csv`, doba 2026-10-13, 24 h, MD5 `729ecf79df5d39a3ef5e9c64d8be77fe` (ta sama co w Lab 4) |
| Dane błędne | `data/test/doba-invalid.csv` (2 godziny); pozostałe błędne pliki tworzone przez testy w katalogu tymczasowym (`tmp_path`) |
| Model budynku | `packages/core/src/heating_optimizer/data/parametry.json`, MD5 `7dc67881aed5465dc26a86047990f3f6` |
| Pasmo | `T_min` 21,0 °C, `T_max` 22,5 °C, `T_start` 21,8 °C, `max_overshoot` 1,0 °C (jak `docs/experiment.md` p. 3) |
| Wymagania | R1–R6 z `docs/problem.md`, kryterium odbioru UC-01 z `docs/architecture.md` |

Testy nie zapisują nic do `data/raw/` ani `data/processed/`; błędne doby powstają jako kopie w `tmp_path`.

**Uruchomienie** (z katalogu repozytorium, w `.venv`):

```bash
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests/test_logic.py -v     # testy logiki Lab 7
python -m pytest                            # wszystkie testy (tests/, packages/core/tests, apps/api/tests)
```

Katalog `tests/` dopisano do `testpaths` w `pyproject.toml`.

## 2. Plan przypadków i dziennik uruchomień

_Plan i testy logiki: Karol Brzozowski. Wyniki testu integracyjnego: Oskar Wysocki._

### 2.1. Plan przypadków (oczekiwania zapisane przed uruchomieniem)

Oczekiwany wynik pochodzi ze specyfikacji, ręcznego rachunku albo wyniku referencyjnego z Lab 4,
nie z bieżącego działania kodu. Oczekiwań nie zmienia się po to, żeby test przeszedł.

| ID | Wymaganie | Rodzaj | Wejście | Oczekiwany wynik | Podstawa oczekiwania | Test |
|---|---|---|---|---|---|---|
| TC-01 | R1, R3, R6 | poprawne | `doba-live.csv`, pasmo z p. 1, metoda DP | 24 decyzje 0/1; grzanie w godz. 0–1 i 10–13; 9,0 kWh; koszt 5,3469 zł (±0,0005); 0 h poniżej `T_min` | `experiment.md` p. 6 i p. 7: Σ cen 0,6373 + 0,6345 + 0,5809 + 0,5753 + 0,5321 + 0,6045 = 3,5646 zł/kWh · 1,5 = 5,3469 zł; kryterium odbioru UC-01 (1) | `test_tc01_dp_plan_for_real_day_matches_lab4` |
| TC-02 | R4, R6 | poprawne | jak TC-01, termostat | grzanie 7–16; koszt 11,1525 zł; 4 h poniżej `T_min`; oszczędność DP 5,8056 zł = 52,06 % | `experiment.md` p. 7: Σ cen 7..16 = 7,4350 zł/kWh · 1,5 = 11,1525 zł; 11,1525 − 5,3469 = 5,8056; 5,8056 / 11,1525 = 52,06 % | `test_tc02_thermostat_baseline_and_saving_match_lab4` |
| TC-03 | R3 | poprawne (ręczny rachunek) | jeden krok modelu: T = 21,8, T_zew = 6,7, G = 0; u = 0 i u = 1; ciąg decyzji 1, 0, 0 | 21,67 °C bez grzania, 21,94 °C z grzaniem; grzałka włączona w godz. 0 działa dopiero w godz. 2 | `PROJEKT.md`: T[t+1] = T − α(T − T_zew) + β·u[t−d] + γ·G + c; `parametry.json`: 21,8 − 0,0053218 · 15,1 − 0,0520086 = 21,6676 → 21,67; + 0,26944 = 21,9370 → 21,94; DELAY = 2 | `test_tc03_one_model_step_matches_hand_calculation`, `test_tc03_heating_acts_after_two_hour_delay` |
| TC-04 | R3 | graniczne | termostat przy T = 21,0 / 22,5 / 21,01 / 22,49; plan z T = 21,0 i 20,99; pasmo 22,0–22,0 i 22,6–22,5 | T = `T_min` → grzej; T = `T_max` → wyłącz; wewnątrz pasma → poprzedni stan; godzina z T = `T_min` nie liczy się jako „poniżej”, 20,99 °C tak (deficyt 0,01 K·h); `T_min` = `T_max` przyjęte; `T_min` > `T_max` → błąd | `experiment.md` p. 3 i p. 5 (T ≤ T_min → 1, T ≥ T_max → 0); p. 7, K5 (godziny < T_min); UC-01: warunek `T_min ≤ T_max`, kryterium odbioru (2) | `test_tc04_thermostat_rule_at_band_edges` (4 warianty), `test_tc04_temperature_exactly_t_min_is_not_counted_below`, `test_tc04_band_with_t_min_equal_t_max_is_accepted_and_inverted_band_rejected` |
| TC-05 | R2, R3 | poprawne (zmiana danych) | `doba-live.csv` z ceną 5 zł/kWh w godz. 10–13 | plan DP inny niż dla doby bazowej; brak grzania w 10–13; nadal 0 h poniżej `T_min` | `problem.md` R2: „zmiana cen powoduje zmianę harmonogramu”; tanie godziny nocne (0,50–0,70 zł/kWh) pozwalają utrzymać pasmo bez drogich godzin | `test_tc05_expensive_hours_change_the_schedule` |
| TC-06 | R1 | błędne | kopia `doba-live.csv` bez godziny 17; `data/test/doba-invalid.csv` (2 godziny) | `ValueError` z „brakujące godziny [17]” / „niepełna doba”; brak planu na 23 h | UC-01: komunikat „Brakujące godziny …: [17]”, kryterium odbioru (3); `implementation.md` p. 2 (tabela błędów) | `test_tc06_day_without_one_hour_is_rejected`, `test_tc06_invalid_test_day_is_rejected` |
| TC-07 | R1, R6 | puste | plik z samym nagłówkiem; puste listy cen i pogody | `ValueError`; żadnego planu z kosztem 0 zł | UC-01, „Brak danych / błąd”: obliczenie przerwane, „bez planu i bez kosztu 0 zł” | `test_tc07_file_with_header_only_is_rejected`, `test_tc07_empty_inputs_are_rejected` |
| TC-08 | R1, R4, R6 | integracyjne | _(uzupełnia Oskar Wysocki: główny przepływ CLI/API)_ | | | `tests/test_integration.py` |

Pokrycie rodzajów: poprawne (TC-01, 02, 03, 05), graniczne (TC-04), błędne (TC-06), puste (TC-07).
R5 (dane pogodowe z udokumentowanego źródła) nie jest sprawdzane testami logiki, bo dotyczy pobierania
z Open-Meteo (status w sekcji 5).

### 2.2. Dziennik uruchomień

Po poprawce dopisujemy nowy wiersz, starych nie usuwamy. Czas: **zestaw** = cały plik / polecenie,
**przypadek** = jeden test.

| Data | Commit | Środowisko | ID testu | Wynik | Czas | Dowód |
|---|---|---|---|---|---|---|
| 2026-11-23 | `12c1a95` + `tests/test_logic.py` (przed commitem) | Linux, Python 3.13.18, pytest 9.2.0 | TC-01…TC-07 (`tests/test_logic.py`, 15 testów z parametryzacją) | PASS | 0,06 s (zestaw) | `python -m pytest tests/test_logic.py -v` → `15 passed` |
| 2026-11-23 | jw. | jw. | całość (`python -m pytest`) | PASS | 0,93 s (zestaw) | `119 passed, 1 warning` (104 dotychczasowe + 15 nowych) |
| 2026-11-23 | jw. + kontrolowana zmiana (lokalnie, cofnięta) | jw. | TC-04 | FAIL (oczekiwany) | 0,04 s (zestaw) | w `simulation.py` zmieniono `temperature <= t_min` na `<` → `FAILED test_tc04_thermostat_rule_at_band_edges[21.0-0-1]`, `1 failed, 14 passed`; zmianę cofnięto (`git checkout`), ponownie `15 passed` |
| _(uzupełnia Oskar Wysocki)_ | | | TC-08 | | | |

## 3. Pomiar niefunkcjonalny

_(uzupełnia Sebastian Król)_

## 4. Ocena danych, wyników i kodu

_(uzupełnia Sebastian Rączka; link do PR z przeglądem kodu: Kacper Mazur)_

## 5. Statusy wymagań

_(uzupełnia Sebastian Rączka)_

## 6. Sprawdzenie dokumentacji

_(uzupełnia Sebastian Król)_

## 7. Znane błędy i ograniczenia

_(uzupełnia Sebastian Rączka)_

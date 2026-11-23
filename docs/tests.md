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
| TC-08 | R1, R4, R6 | integracyjne (poprawne) | `python -m heating_optimizer --data <kopia doba-live.csv> --out <tmp>/wyniki/plan.csv` — osobny proces, katalog tymczasowy | kod 0; podsumowanie: koszt 5.35 / 11.15 zł, energia 9.0 / 15.0 kWh, 0 / 4 h poniżej `T_min`, „Oszczędność: 5.81 zł (52.1%)”; plik wyniku: 8 kolumn, 24 h 0..23, wejście przepisane bez zmiany jednostek (zł/kWh, °C, W/m²), stany 0/1, T optymalizatora ≥ 21,0 °C; koszt przeliczony z pliku 5,3469 / 11,1525 zł; plik wejściowy nietknięty (MD5) | `experiment.md` p. 6–7 (jak TC-01, TC-02); README „Realizacja MVP (Lab 6)”; `data-dictionary.md` (jednostki) | `test_int_02_main_flow_content_units_and_messages` |
| TC-09 | — (jakość danych, Lab 3) | dane | kopia `doba-live.csv`; kopia `data/test/doba-invalid.csv` | `scripts/check_data.py` (bez zmian): „Kontrola OK”, Rekordy: 24, Braki: 0, Duplikaty hour: 0; MD5 `729ecf79…`; ceny 0–5 zł/kWh (nie zł/MWh); dla doby z 2 h: kod ≠ 0, „Kontrola niezaliczona”, „rekordy: 2 != 24” | `processing.md` (kontrole Lab 3), `data-dictionary.md`, p. 1 (MD5 próbki) | `test_int_01_sample_passes_lab3_quality_checks`, `test_int_01b_lab3_check_rejects_incomplete_day` |
| TC-10 | R1 | integracyjne (błędne) | CLI z kopią `doba-invalid.csv`; CLI z istniejącym plikiem `--out` | kod 1; „niepełna doba — brakujące godziny [2, …]” i brak pliku wyniku; „już istnieje” i plik bez zmian | UC-01, kryterium odbioru (3); README (Lab 6): błędy CLI | `test_int_03_incomplete_day_gives_message_and_no_file`, `test_int_04_existing_output_is_not_overwritten` |
| TC-11 | R3 | graniczne | CLI z `--t-min nan`, `--t-max inf`, `--t-start nan`, `--t-min=-inf` | błąd argumentu „…skończoną liczbą”, kod ≠ 0, brak planu i pliku wyniku | R3 (bez poprawnego pasma nie ma planu); spójność z API (Z-03: NaN → 422) | `test_int_05_non_finite_comfort_band_is_rejected` (4 warianty) |

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
| 2026-11-23 | `c02b614` | Windows, Python 3.13.3, pytest 9.2.0 | TC-08…TC-10 (`tests/test_integration.py`, 5 przypadków) | PASS | 8,06 s (zestaw) | `python -m pytest tests/test_integration.py -v` → `4 failed, 5 passed` |
| 2026-11-23 | `c02b614` | jw. | TC-11 (4 warianty) | **FAIL** | jw. | `--t-min nan` → kod 0, „Koszt energii 0.00 / 0.00 zł”, „Godziny poniżej T_min 0”, temperatura spada do 19,68 °C; zgłoszone w Issue #13 |
| 2026-11-23 | `7b1a752` (poprawka `cli.py`, fixes #13) | jw. | TC-08…TC-11 (9 przypadków) | PASS | 6,87 s (zestaw) | `python -m pytest tests/test_integration.py -v` → `9 passed` |
| 2026-11-23 | `7b1a752` | jw. | całość (`python -m pytest`, jeszcze bez `tests/` w `testpaths`) | PASS | 1,83 s (zestaw) | `104 passed, 1 warning` |
| 2026-11-23 | `2eca744` (po scaleniu `main` z PR #7) | jw. | całość (`python -m pytest`, z `tests/`) | PASS | 9,28 s (zestaw) | `128 passed, 1 warning in 9.28s` |

## 3. Pomiar niefunkcjonalny

_Sebastian Król._

**Właściwość:** czas pełnej analizy UC-01: wczytanie i walidacja doby z CSV, plan DP i symulacja
termostatu (te same funkcje co CLI i `POST /api/optimize`; bez sieci i bez HTTP).

**Kryterium (ustalone przed pomiarem):** mediana ≤ **1 s** dla jednej doby (24 h).
Uzasadnienie: w GUI plan przelicza się sam po każdej zmianie suwaka `T_min`/`T_max`/`T_start`
i wymuszeń (zachowanie GUI; w `docs/user-guide.md` jeszcze nieopisane, Issue #18). Użytkownik porównuje warianty, więc odpowiedź musi być
praktycznie natychmiastowa; 1 s to założenie zespołu (typowa granica, przy której opóźnienie
zaczyna przerywać pracę). Zakres projektu to jedna doba (`problem.md`), więc kryterium dotyczy 24 h.
Dziesięciokrotnie większa próbka (240 h) to ćwiczenie z instrukcji: pokazuje, jak czas rośnie z horyzontem.

**Warunki:**

| Element | Ustalenie |
|---|---|
| Polecenie | `python scripts/measure_lab7.py data/processed/doba-live.csv results/lab7` |
| Dane | `doba-live.csv` (24 h, MD5 `729ecf79…`); 10x = ta sama doba powtórzona 10 razy (240 h, plik tymczasowy) |
| Parametry | `T_min` 21,0, `T_max` 22,5, `T_start` 21,8, model z `parametry.json` |
| Metoda | 1 uruchomienie rozgrzewające (nieliczone), 5 powtórzeń, `time.perf_counter`; walidacja wejścia włączona |
| Kod | commit `5775572` (zmiany Lab 7 nie dotyczą silnika poza walidacją parametrów CLI) |
| Sprzęt (pomiar 1) | Linux 6.18 x86_64, Intel Xeon @ 2,30 GHz, 2 rdzenie, Python 3.13.18 (środowisko wirtualne, nie komputer zespołu); kod `5775572` |
| Sprzęt (pomiar 2) | komputer Sebastiana Króla: AMD Ryzen 7 5800X (8 rdzeni / 16 wątków, 3,8 GHz), 32 GB RAM, Windows 11 Pro 10.0.26200, Python 3.14.5 w nowym `.venv`; świeży klon `main` @ `b639c98`; zwykłe programy w tle (bez zamykania aplikacji) |

**Wyniki** (pomiar 1: `results/lab7/timing.csv` - każde powtórzenie, `results/lab7/timing-summary.csv` - podsumowanie;
pomiar 2: `results/lab7/komputer-seba/timing.csv` i `timing-summary.csv`):

| Środowisko | Przypadek | Godzin | Mediana | Min | Max | Kryterium ≤ 1 s | Kontrola poprawności |
|---|---|---|---|---|---|---|---|
| 1 (VM) | doba | 24 | **0,0033 s** | 0,0032 s | 0,0037 s | **spełnione** (ok. 300× zapasu) | koszt DP 5,3469 zł, termostat 11,1525 zł (= Lab 4) |
| 1 (VM) | 10x | 240 | 1,2446 s | 1,2013 s | 1,3021 s | nie dotyczy (poza zakresem; byłoby niespełnione) | koszt DP 71,1720 zł, termostat 100,1329 zł |
| 2 (komputer Seby) | doba | 24 | **0,0046 s** | 0,0045 s | 0,0049 s | **spełnione** (ok. 200× zapasu) | koszt DP 5,3469 zł, termostat 11,1525 zł (= Lab 4) |
| 2 (komputer Seby) | 10x | 240 | 1,4416 s | 1,2702 s | 1,5763 s | nie dotyczy (poza zakresem; byłoby niespełnione) | koszt DP 71,1720 zł, termostat 100,1329 zł |

**Wniosek:** dla zakresu projektu (jedna doba) czas jest pomijalny wobec kryterium. Czas rośnie
szybciej niż liniowo: 10 razy dłuższy horyzont daje ok. 380 razy dłuższy czas, bo z każdą godziną
przybywa stanów DP (temperatura × historia grzałki). Plan na kilka dni w GUI wymagałby zmian
w `optimizer.py` (np. ograniczenia liczby stanów) - zapisane w sekcji 7.
Pomiar 2 na komputerze użytkownika potwierdza wynik: doba 0,0046 s (kryterium spełnione), 240 h ok. 310× dłużej.
Na komputerze Seby czas doby jest nieco dłuższy niż w VM mimo szybszego procesora - inny system i wersja Pythona
(Windows, 3.14 vs Linux, 3.13) oraz programy w tle; różnica ok. 1 ms nie ma znaczenia wobec kryterium 1 s.
Koszty w obu środowiskach są identyczne, więc mierzono ten sam przebieg obliczeń.

**Ograniczenia pomiaru:** nie obejmuje HTTP ani rysowania wykresów w przeglądarce; po 5 powtórzeń
w każdym środowisku; pomiar 2 bez zamykania innych programów (warunki zwykłej pracy, większy rozrzut max).
Polecenie pomiaru 2: `python scripts/measure_lab7.py data/processed/doba-live.csv <nowy katalog>` w świeżym klonie.

## 4. Ocena danych, wyników i kodu

_Sebastian Rączka. Przegląd kodu w PR: Kacper Mazur._

### 4.1. Dane

| Kontrola | Wynik | Dowód |
|---|---|---|
| Próbka oceny = próbka z Lab 4 | tak, MD5 `729ecf79df5d39a3ef5e9c64d8be77fe` w `doba-live.csv` i w `results/lab4/comparison.csv` (`dane_md5`) | sekcja 1, `comparison.csv` |
| Kontrole Lab 3 (`check_data.py`) | `Kontrola OK`: 24 rekordy, 0 braków, 0 duplikatów `hour` | sekcja 2 (Oskar), krok w `check.yml` |
| Kontrola obliczeń Lab 4 (`check_lab4.py`) | `Kontrola OK (K1-K7)` dla `results/lab4` i `results/lab4/sensitivity` | krok w `check.yml` |

Ograniczenie danych: jedna doba archiwalna (13.10.2026, Warszawa) z cenami RCE i pogodą znanymi z góry.
Zero naruszeń kontroli nie dowodzi, że próbka jest reprezentatywna dla innych dni i budynków.

### 4.2. Wyniki po integracji vs eksperyment Lab 4

**Miary** (te same co w Lab 4, `experiment.md` p. 3): koszt [zł] i godziny poniżej `T_min` [h], do tego
energia, godziny grzania, deficyt [K·h], temperatury średnia/min/max, oszczędność [zł, %]. Dla każdej
godziny: MAE temperatury i liczba różnych decyzji względem `observations.csv` z Lab 4.

**Sposób:** `python scripts/compare_lab7.py results/lab7`. Dla przypadku bazowego (`T_min` 21,0) i próby
wrażliwości (`T_min` 21,5) skrypt wykonuje pełną operację przez interfejs projektu
(`python -m heating_optimizer … --out`), liczy miary od nowa z pliku wyniku, dopasowuje godziny po
kolumnie `hour` (nie po pozycji) i porównuje z `results/lab4/…/comparison.csv`.

**Uzgodniona tolerancja (przed uruchomieniem):** koszt i oszczędność ±0,01 zł, oszczędność % ±0,1 p.p.,
temperatury i deficyt ±0,01 °C, liczby godzin i energia: dokładnie. Lab 4 był deterministyczny
(brak losowania), więc każda większa różnica oznaczałaby zmianę zachowania po integracji.

| Przypadek | Wariant | Koszt Lab 4 → Lab 7 | Godziny < T_min | MAE temp. | Różne decyzje | Zgodne miary |
|---|---|---|---|---|---|---|
| bazowy (`T_min` 21,0) | termostat | 11,1525 → 11,1525 zł | 4 → 4 | 0,0000 °C | 0/24 | 10/10 |
| bazowy | DP | 5,3469 → 5,3469 zł | 0 → 0 | 0,0000 °C | 0/24 | 10/10 |
| wrażliwość (`T_min` 21,5) | termostat | 11,3871 → 11,3871 zł | 5 → 5 | 0,0000 °C | 0/24 | 10/10 |
| wrażliwość | DP | 7,2809 → 7,2809 zł | 0 → 0 | 0,0000 °C | 0/24 | 10/10 |

Wynik: **40/40 miar zgodnych**, oszczędność 5,81 zł (52,06 %) i 4,11 zł (36,06 %) jak w Lab 4.
Pliki: `results/lab7/quality.csv` (każda miara), `results/lab7/quality-hourly.csv` (MAE, decyzje).
Po integracji nie ma pogorszenia, więc kryterium praktyczne z Lab 4 (≥ 5 % oszczędności i nie zimniej)
pozostaje spełnione.

**Czy porównanie wykrywa różnicę** (kontrolowana zmiana, nie zapisana w repo): po zmianie `T_start` na
21,9 w kopii skryptu wynik to 30/40 zgodnych, MAE temperatury 0,10–0,13 °C, 1 różna decyzja DP,
kod wyjścia ≠ 0 dla niezgodności.

**Poprawne obliczenie ≠ użyteczny wynik:** zgodność z Lab 4 potwierdza, że integracja nie zmieniła
obliczeń. Nie potwierdza, że w prawdziwym domu oszczędność wyniesie 52 %: plan zakłada idealną
prognozę cen i pogody oraz budynek referencyjny (`experiment.md` p. 4, odrzucone SMPC).

### 4.3. Kod

| Kontrola | Wynik |
|---|---|
| `python -m pytest` | `128 passed, 1 warning` (104 dotychczasowe + 15 logiki + 9 integracyjnych TC-08..TC-11) |
| `ruff check .` | 4 ostrzeżenia, wszystkie sprzed Lab 7 (`check_data.py`, `check_lab4.py`, `examples/lab4`); pliki Lab 7 bez uwag |
| Przegląd zmienionego fragmentu (`cli.py`, `finite_float`; podział funkcji, nazwy, wyjątki, zgodność z UC-01) | _(Kacper Mazur: link do komentarza w PR `feature/lab7-test-integracyjny`)_ |

## 5. Statusy wymagań

_Sebastian Rączka._ Wymagania z `docs/problem.md` + kryterium czasu z sekcji 3. Wymagań niespełnionych
lub niesprawdzonych nie usuwamy - zostają jako jawne zadania.

| ID | Wymaganie | Wynik | Dowód | Status |
|---|---|---|---|---|
| R1 | Plan ogrzewania dla kolejnych 24 h | 24 decyzje 0/1 z temperaturą w CLI, pliku CSV i API; niepełna lub pusta doba → błąd, nie plan | TC-01, TC-06, TC-07, TC-08, TC-09, TC-10 | **spełnione** |
| R2 | Uwzględnianie cen energii | droższe godziny 10–13 → inny plan bez grzania w 10–13; DP grzeje w tanich godzinach | TC-05, TC-01 | **spełnione** |
| R3 | Temperatura w paśmie komfortu | DP: 0 h poniżej `T_min` dla `T_min` 21,0 i 21,5; reguły na granicach pasma; NaN/inf w paśmie → błąd | TC-01, TC-03, TC-04, TC-08, TC-11, sekcja 4.2 | **spełnione** na próbce (jedna doba, model referencyjny) |
| R4 | Porównanie z klasycznym termostatem | oba warianty na tych samych danych, wyniki zgodne z Lab 4 (40/40) | TC-02, TC-08, TC-09, sekcja 4.2 | **spełnione** |
| R5 | Publiczne dane pogodowe z udokumentowanego źródła | testy sprawdzają tylko parsowanie zapisanych próbek Open-Meteo (`test_data_sources.py`); pobieranie na żywo sprawdzone ręcznie w Lab 6, nie w Lab 7 (bez testów cudzych API) | `implementation.md` p. 2 | **niesprawdzone** w Lab 7 |
| R6 | Prognozowany koszt w zł | koszt obu wariantów w zł w CLI i API, przeliczony ręcznie i z pliku wyniku; wyświetlanie w GUI sprawdzane tylko ręcznie (Lab 6) | TC-01, TC-02, TC-08, TC-09 | **spełnione** (CLI, API); GUI: ręcznie |
| N1 | Czas analizy doby ≤ 1 s | mediana 0,0033 s (24 h); 240 h: 1,24 s (poza zakresem) | sekcja 3 | **spełnione** |
| U1 | Oszczędność w prawdziwym domu (użyteczność decyzji) | brak reprezentatywnej próbki: jeden dzień, idealna prognoza, budynek referencyjny | sekcja 4.2 | **niesprawdzone** |

## 6. Sprawdzenie dokumentacji

_Sebastian Król (nie jest autorem README ani `docs/user-guide.md`; autor: Kacper Mazur)._

Zasada: wykonać instrukcję **samodzielnie, bez ustnych podpowiedzi autora**, w nowym katalogu
(`git clone` do pustego folderu, nowe `.venv`). Każdy brak zapisać w tabeli i w Issue.

| Krok z dokumentacji | Gdzie | Wynik (OK / brak / błąd) | Uwagi |
|---|---|---|---|
| Utworzenie `.venv` i instalacja `requirements.txt` + `requirements-dev.txt` | README („Testy i CI (Lab 7)”), `user-guide.md` p. 1 | **OK** | `python -m venv .venv`, aktywacja, `python -m pip install -r requirements.txt -r requirements-dev.txt` bez błędów. **Brak** w README „Uruchomienie bez Dockera”: inne, niepełne polecenia (Issue #18, p. 1–2) |
| `python -m pytest -v`: same `passed` | README („Testy i CI (Lab 7)”), `user-guide.md` p. 6 | **OK** | 128 passed, 1 warning (`StarletteDeprecationWarning` przy fastapi 0.165), 5,14 s |
| Przypadek poprawny: `python -m heating_optimizer --data data/processed/doba-live.csv --out wyniki/plan.csv`; wynik 5,35 zł / 11,15 zł / 52,1 % | `user-guide.md` p. 2.1 i 4 | **OK** | wynik identyczny z przykładem w p. 4; `wyniki/plan.csv`: 25 linii (nagłówek + 24 h), katalog `wyniki/` utworzony sam |
| Odczyt wyniku: czy z p. 4 wiadomo, co znaczą „Godziny poniżej T_min” i kolumny CSV | `user-guide.md` p. 4 | **OK** | opis wierszy podsumowania i kolumn wystarcza; nagłówek pliku zgodny z listą kolumn w p. 4 |
| Przypadek błędny: `--data data/test/doba-invalid.csv`; komunikat zgodny z tabelą z p. 5 | `user-guide.md` p. 5 | **OK** | `Błąd: doba-invalid.csv: niepełna doba — brakujące godziny [2, 3, …, 23]`, kod 1, brak pliku `wyniki/bad.csv`. Dodatkowo ponowny `--out wyniki/plan.csv`: `Błąd: plik wyniki\plan.csv już istnieje — podaj nową nazwę`, kod 1 (zgodnie z p. 5) |
| GUI: `npm install`, `npm run api`, `npm run dev`, zmiana `T_min` przelicza plan | `user-guide.md` p. 2.2 | **NOT RUN** | na komputerze sprawdzającym nie ma Node.js (`npm` nieznane) - wymaganie Node 20+ jest w p. 1, więc to nie brak dokumentacji. **Brak:** `user-guide.md` nie opisuje obsługi GUI (Issue #18, p. 3) |

Data sprawdzenia: 2026-11-23 · commit: `b639c98` (świeży `git clone`, nowe `.venv`) · system / Python: Windows 11 Pro 10.0.26200, Python 3.14.5, git 2.56.0

Sprawdzał Sebastian Król, bez podpowiedzi autora (Kacper Mazur): polecenia wykonane dokładnie w brzmieniu z dokumentacji,
przebieg zapisany do logu (wyniki wyżej). Odwołania do punktów `user-guide.md` w tabeli poprawione do obecnej numeracji (1–6).

**Znalezione braki** (zgłoszone w [Issue #18](https://github.com/MazutK/UPOSiE---Projekt-informatyczny/issues/18)):

1. README, „Uruchomienie bez Dockera”: `pip install -r requirements-dev.txt` bez `requirements.txt` (brak `pandas`
   dla `scripts/check_data.py` i testu `test_int_01`); `.venv\Scripts\activate` nie działa w PowerShell;
   `npm run api` i `npm run dev` w jednym bloku, choć pierwsze blokuje terminal, i bez informacji, że terminal z API
   potrzebuje aktywnego `.venv`.
2. README ma cztery różne bloki instalacji (bez Dockera, Lab 4, Lab 6, Lab 7) - nie wiadomo, który jest aktualny.
3. `docs/user-guide.md` nie opisuje obsługi GUI (panel ustawień, wymuszenia, dane publiczne, eksport, wykresy),
   choć GUI to główny interfejs z README.
4. Drobne: wersje zależności bez górnych ograniczeń (ostrzeżenie przy świeżej instalacji); na Windows ścieżki
   w komunikatach z `\`, w dokumentacji z `/`.

Przypadek poprawny i błędny z `user-guide.md` działają zgodnie z opisem; braki dotyczą instrukcji, nie programu.

## 7. Znane błędy i ograniczenia

_Sebastian Rączka._

| # | Problem | Wpływ | Obejście / stan |
|---|---|---|---|
| B1 | CLI przyjmowało `nan`/`inf` w `--t-min`, `--t-max`, `--t-start`: „plan” za 0 zł z kodem 0 | użytkownik dostaje bezsensowny wynik bez ostrzeżenia | **poprawione** w `feature/lab7-test-integracyjny` (Issue Oskara, TC-11) |
| B2 | CLI przyjmuje liczby skończone spoza zakresu API (5–30 °C), np. `--t-min 40 --t-max 45` → plan z 24 h poniżej `T_min`, kod 0 | wynik formalnie policzony, praktycznie bez sensu | **otwarte**: dodać w `cli.py` te same zakresy co `schemas.py`; do tego czasu korzystać z GUI albo podawać 5–30 °C |
| B3 | Czas DP rośnie szybciej niż liniowo z horyzontem (24 h: 0,003 s, 240 h: 1,24 s) | plan wielodniowy w GUI byłby odczuwalnie wolny | **otwarte**, poza zakresem (jedna doba); ewentualnie ograniczenie liczby stanów w `optimizer.py` |
| B4 | Z-10 częściowo: nazwa eksportu bez daty doby live (odpowiedź `/api/optimize` jej nie zawiera) | trudniej rozpoznać plik planu | **otwarte** (z `implementation.md` p. 4): dodać `data_date` do kontraktu |
| B5 | `docs/diagrams/granice.png` nieaktualny względem `granice.drawio` | dokumentacja architektury pokazuje stary obraz | **otwarte**: wyeksportować PNG z draw.io |
| B6 | Termostat nie stosuje wymuszeń godzin | porównanie przy wymuszeniach nie jest symetryczne | **otwarte**, informacja w GUI (Z-05) |
| B7 | Docker bez `data/raw/`: przy braku sieci `/api/live` nie ma próbki offline | brak świeżej doby bez internetu | **otwarte**, zachowanie bezpieczne (zostaje poprzednia doba) |

**Ograniczenia oceny:** jedna doba archiwalna i jeden model budynku; plan przy idealnej prognozie;
pomiar czasu w środowisku wirtualnym; GUI i zewnętrzne API (PSE, Open-Meteo) sprawdzane tylko ręcznie.
Przejście testów nie oznacza pełnej użyteczności w warunkach rzeczywistych (U1).

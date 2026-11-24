# Raport końcowy: Optymalizator ogrzewania elektrycznego przy zmiennych cenach energii

_Lab 8. Redakcja raportu: Karol Brzozowski. Przegląd: Oskar Wysocki (uwagi w PR)._

| Element | Wartość |
|---|---|
| Prezentowana wersja | `v1.0.0` — tag zakłada Kacper Mazur na końcu prac; commit taga: _(uzupełnić po `git rev-parse "v1.0.0^{commit}"`)_ |
| Stan, na którym sprawdzono liczby z raportu | `main` @ `791545e` (Merge PR #20), 2026-11-24 |
| Próbka danych | `data/processed/doba-live.csv`, doba 2026-10-13, Warszawa, 24 h, MD5 `729ecf79df5d39a3ef5e9c64d8be77fe` |
| Model budynku | `packages/core/src/heating_optimizer/data/parametry.json` (jeden budynek referencyjny, grzałka 1,5 kW, opóźnienie 2 h) |
| Repozytorium | <https://github.com/MazutK/UPOSiE---Projekt-informatyczny> |

Sprawdzenie przed oddaniem raportu (2026-11-24, `791545e`, świeży `git clone`, nowe `.venv`,
Linux, Python 3.10.12): `python -m pytest` → `128 passed, 1 warning`; CLI na `doba-live.csv` →
5,35 zł / 11,15 zł, „Oszczędność: 5.81 zł (52.1%)”, kod 0; CLI na `data/test/doba-invalid.csv` →
„niepełna doba — brakujące godziny [2, 3, …, 23]”, kod 1; `scripts/check_lab4.py` dla
`results/lab4` i `results/lab4/sensitivity` → `Kontrola OK (K1-K7)`; MD5 próbki zgodny.

## 1. Problem i użytkownik

**Użytkownik:** właściciel lub najemca domu/mieszkania z ogrzewaniem elektrycznym i taryfą dynamiczną.
**Wspierana decyzja:** w których godzinach najbliższej doby włączyć grzanie, żeby utrzymać temperaturę
w paśmie komfortu przy możliwie najniższym koszcie energii.

Zwykły termostat reaguje tylko na temperaturę w pomieszczeniu, więc może grzać w najdroższych godzinach.
Użytkownik nie ma narzędzia, które powie mu, kiedy grzać, ile to będzie kosztować i ile zyskuje
względem termostatu.

**Zakres:** plan na 24 h z krokiem 1 h, godzinowe ceny energii, pogoda, porównanie z termostatem,
koszt i komfort. **Poza zakresem:** sterowanie urządzeniem na żywo, wiele budynków, automatyka domowa,
prognozowanie cen.

Sprawdzane wymagania: R1–R6 z [`problem.md`](./problem.md), kryterium czasu N1 i pytanie o użyteczność U1
z [`tests.md`](./tests.md#5-statusy-wymagań). Statusy — rozdział 5.

Dowód: [`problem.md`](./problem.md).

## 2. Zakres wykonany

Główny przepływ **UC-01** ([`architecture.md` §2](./architecture.md#2-przypadek-użycia-uc-01)): dla doby
(ceny + pogoda) i pasma komfortu silnik wyznacza najtańszy plan grzania na 24 h i porównuje go z termostatem.

**Działa (sprawdzone na `791545e`):**

| Element | Gdzie | Dowód działania |
|---|---|---|
| Silnik: model cieplny, termostat, plan DP, walidacja doby | `packages/core/src/heating_optimizer/` | testy TC-01…TC-07 ([`tests.md` §2](./tests.md#2-plan-przypadków-i-dziennik-uruchomień)) |
| CLI: plan do pliku CSV, ochrona przed nadpisaniem, odrzucenie niepełnej doby i NaN/inf | `cli.py`, `python -m heating_optimizer` | TC-08, TC-10, TC-11; ręcznie w tym raporcie |
| API: `POST /api/optimize`, `/api/compare`, `/api/sensitivity`, `GET /api/live` | `apps/api` | `apps/api/tests`, kontrakt w [`architecture.md` §3](./architecture.md#3-kontrakt-interfejsu-post-apioptimize) |
| GUI: panel ustawień, wykresy, tabela godzinowa, porównanie 4 metod, wrażliwość, wymuszenia godzin, dane live, eksport CSV | `apps/web` | sprawdzone ręcznie w Lab 6 ([`implementation.md` §2](./implementation.md#2-uruchomienie-głównego-przepływu)); brak testów automatycznych GUI |
| Dane publiczne PSE + Open-Meteo z zapisem do `data-local/` i metadanymi daty | `data_sources/`, `datasets.py` | Z-08, Z-09, P-01 w [`implementation.md` §3](./implementation.md#3-wynik-integracji-i-podział-prac) |
| Uruchomienie w Dockerze | `docker-compose.yml` | [`README.md`](../README.md#uruchomienie) |
| CI (GitHub Actions) | `.github/workflows/check.yml` | [`README.md`](../README.md#testy-i-ci-lab-7) |

**Nie zrealizowano lub zrealizowano częściowo** (z [`implementation.md` §4](./implementation.md#4-znane-ograniczenia-i-otwarte-zadania)
i [`tests.md` §7](./tests.md#7-znane-błędy-i-ograniczenia)):

- B2 — CLI przyjmuje skończone wartości pasma spoza zakresu API (np. `--t-min 40`) i zwraca bezsensowny plan z kodem 0. **Otwarte.**
- B4 / Z-10 częściowo — nazwa eksportu planu nie zawiera daty doby live (brak `data_date` w odpowiedzi `/api/optimize`). **Otwarte.**
- B5 — `docs/diagrams/granice.png` nieaktualny względem `granice.drawio`. **Otwarte.**
- B6 — termostat w porównaniu nie stosuje wymuszeń godzin (GUI tylko o tym informuje, Z-05). **Otwarte.**
- B7 — w obrazie Dockera nie ma `data/raw/`, więc bez sieci `/api/live` nie ma próbki offline (zostaje poprzednia doba). **Otwarte.**
- Lista scenariuszy w GUI ładowana raz — nowa data doby live widoczna po odświeżeniu strony.
- Brak sterowania urządzeniem na żywo i brak historii obliczeń z GUI — poza zakresem (ADR-001).

**Otwarte Issues** (stan 2026-11-24): [#18](https://github.com/MazutK/UPOSiE---Projekt-informatyczny/issues/18)
— braki w README i w opisie GUI w `user-guide.md`; poprawka w PR #21 (Kacper Mazur), jeszcze niescalona.
Błędy B2–B7 nie mają osobnych Issues — są opisane w `tests.md` §7.

Dowód: [`implementation.md`](./implementation.md), [`tests.md` §7](./tests.md#7-znane-błędy-i-ograniczenia), Issues w repozytorium.

## 3. Dane

| Element | Ustalenie |
|---|---|
| Źródła | ceny RCE: PSE, `https://api.raporty.pse.pl/api/rce-pln`; pogoda: Open-Meteo Archive, `https://archive-api.open-meteo.com/v1/archive` (dla doby live także `api.open-meteo.com/v1/forecast`) |
| Zakres próbki | jedna doba 2026-10-13, Warszawa (52,2297 N, 21,0122 E), strefa `Europe/Warsaw` |
| Jednostka obserwacji | jedna godzina doby dla budynku referencyjnego |
| Pola po przetworzeniu | `hour` (0–23), `price_pln_kwh` [zł/kWh], `outside_temp_c` [°C], `solar_radiation_wm2` [W/m²] |
| Przetwarzanie | średnia RCE z czterech kwadransów → 1 h; zł/MWh ÷ 1000 → zł/kWh; inner join z pogodą po godzinie; `dropna` (brak godziny nie może wejść do DP jako 0) |
| Kontrola jakości | `scripts/check_data.py`: 24 rekordy, 0 braków, 0 duplikatów `hour`, zakresy jednostek → `Kontrola OK` |
| Odtworzenie | `python scripts/prepare_data.py data/raw/pse-rce-sample.json data/raw/open-meteo-sample.json data/processed/doba-live.csv` |
| Plan awaryjny | wbudowane doby CSV w `packages/core/src/heating_optimizer/data/` (5 scenariuszy + `doba_live.csv`) |
| Dane osobowe | brak |

**Ważne ograniczenia danych:**

- jedna doba i jedna lokalizacja — próbka nie reprezentuje sezonu grzewczego ani innego klimatu;
- dane archiwalne, więc ceny i pogoda są „znane z góry” (idealna prognoza);
- brak danych o innych budynkach — model cieplny ma jeden zestaw parametrów;
- RCE może być ujemna (to nie błąd importu); ujemne nasłonecznienie przerywa przetwarzanie;
- API PSE bywa wrażliwe na brak nagłówka `User-Agent`.

Dowód: [`data.md`](./data.md), [`data-dictionary.md`](./data-dictionary.md), [`processing.md`](./processing.md).

## 4. Metoda i architektura

**Wariant bazowy:** termostat z histerezą — grzej, gdy T ≤ `T_min`, wyłącz, gdy T ≥ `T_max`, cen nie bierze pod uwagę
(`simulate_thermostat`).

**Metoda:** programowanie dynamiczne (DP) na horyzoncie 24 etapów z decyzją 0/1 w każdej godzinie
(`find_optimal_schedule`). Koszt porównywany leksykograficznie: najpierw kara za spadek poniżej `T_min`,
potem koszt w zł. Stan = temperatura (siatka 0,05 °C) + historia grzałki, bo grzanie działa z opóźnieniem 2 h
(rozszerzenie stanu jak u Bertsekasa, rozdz. 1.4). Model budynku: T[t+1] = T − α(T − T_zew) + β·u[t−d] + γ·G + c.

**Odrzucona alternatywa:** stochastyczne MPC w ruchomym horyzoncie (Oldewurtel i in., 2012) — wymaga modelu błędu
prognozy i solvera; na danych archiwalnych nie ma niepewności do modelowania. Skutek: wynik DP to oszczędność przy
idealnej prognozie.

**Warunki porównania** (ustalone przed uruchomieniem, [`experiment.md` §3](./experiment.md#3-warunki-porównania-ustalone-przed-uruchomieniem)):
te same 24 h, ceny, pogoda, model i pasmo dla obu wariantów; `T_min` 21,0 °C, `T_max` 22,5 °C, `T_start` 21,8 °C,
`max_overshoot` 1,0 °C; kryterium praktyczne: DP oszczędza ≥ 5 % **i** nie ma więcej godzin poniżej `T_min`
(próg 5 % to założenie zespołu); próba wrażliwości: `T_min` 21,5 °C.

**Architektura** ([`architecture.md`](./architecture.md)): jeden silnik w Pythonie (`packages/core`) wołany przez dwa
interfejsy — CLI i API FastAPI (`apps/api`), z którego korzysta GUI w React (`apps/web`). Granice systemu:
[`architecture.md` §1](./architecture.md#1-granice-systemu), diagram `docs/diagrams/granice.drawio`;
przepływ danych i diagram sekwencji UC-01: §5–§6.

**Kluczowa decyzja techniczna — [ADR-001](./decisions/001-storage.md):** dane wejściowe i wyniki w plikach CSV/JSON
w repozytorium zamiast bazy SQLite. Powód: kilka plików po kilkadziesiąt wierszy, czytelny diff i MD5 jako wersja danych,
cały kod Lab 3–4 pracuje na CSV. Koszt: kontrolę poprawności, ochronę przed nadpisaniem (Z-06, Z-07) i zapis atomowy
(Z-09) trzeba było napisać samemu. Warunki powrotu do decyzji są w ADR (historia uruchomień w GUI, wiele budynków
lub użytkowników, równoległe zapisy).

Dowód: [`experiment.md`](./experiment.md), [`architecture.md`](./architecture.md), [`decisions/001-storage.md`](./decisions/001-storage.md).

## 5. Wyniki i ocena

### 5.1. Porównanie metod (Lab 4, potwierdzone po integracji w Lab 7)

Doba 2026-10-13, 24 h, dane MD5 `729ecf79…`, model `parametry.json`, `T_max` 22,5 °C, `T_start` 21,8 °C, `max_overshoot` 1,0 °C.

| Wariant | `T_min` [°C] | Koszt [zł] | Energia [kWh] | Godziny grzania | Godziny < `T_min` | Min T [°C] | Oszczędność vs termostat |
|---|---|---|---|---|---|---|---|
| termostat | 21,0 | 11,1525 | 15,0 | 10 (7–16) | 4 | 20,65 | — |
| DP | 21,0 | 5,3469 | 9,0 | 6 (0–1, 10–13) | 0 | 21,02 | 5,8056 zł (52,06 %) |
| termostat | 21,5 | 11,3871 | 15,0 | 10 | 5 | 21,15 | — |
| DP | 21,5 | 7,2809 | 12,0 | 8 | 0 | 21,53 | 4,1063 zł (36,06 %) |

Pliki: [`results/lab4/comparison.csv`](../results/lab4/comparison.csv),
[`results/lab4/sensitivity/comparison.csv`](../results/lab4/sensitivity/comparison.csv), godzinowo:
[`results/lab4/observations.csv`](../results/lab4/observations.csv). Kryterium praktyczne spełnione w obu przypadkach
(`kryterium_spelnione = true`). Niezależna kontrola `scripts/check_lab4.py` (bez importu silnika) → `Kontrola OK (K1-K7)`;
ręczne przeliczenie sum w [`experiment.md` §7](./experiment.md#7-kontrola-obliczeń).

Po integracji (Lab 7) ten sam przepływ przez CLI dał **40/40 miar zgodnych** z Lab 4 w uzgodnionej tolerancji
(koszt ±0,01 zł, temperatury ±0,01 °C, liczby godzin dokładnie), MAE temperatury 0,0000 °C, 0/24 różnych decyzji:
[`results/lab7/quality.csv`](../results/lab7/quality.csv), [`results/lab7/quality-hourly.csv`](../results/lab7/quality-hourly.csv).

### 5.2. Testy

| Zestaw | Commit | Wynik |
|---|---|---|
| `python -m pytest` (wszystkie: `tests/`, `packages/core/tests`, `apps/api/tests`) | `791545e` (sprawdzenie do raportu, Linux, Python 3.10.12) | `128 passed, 1 warning` |
| jw. | `2eca744` (Lab 7, dziennik w `tests.md` §2.2) | `128 passed, 1 warning` |
| Testy logiki TC-01…TC-07 + kontrolowana zmiana `<=` → `<` w `simulation.py` | Lab 7 | test TC-04 wykrył zmianę (`1 failed`), po cofnięciu `15 passed` |
| Test integracyjny TC-08…TC-11 | `7b1a752` | `9 passed` po poprawce Issue #13 (NaN w paśmie CLI) |

Plan przypadków z oczekiwaniami zapisanymi przed uruchomieniem i pełny dziennik: [`tests.md` §2](./tests.md#2-plan-przypadków-i-dziennik-uruchomień).

### 5.3. Miara niefunkcjonalna

Czas pełnej analizy UC-01 (wczytanie i walidacja doby, DP, termostat; bez HTTP i GUI), 5 powtórzeń po rozgrzaniu,
kryterium ustalone przed pomiarem: mediana ≤ 1 s dla 24 h.

| Środowisko | Godzin | Mediana | Kryterium |
|---|---|---|---|
| VM Linux, Python 3.13.18, commit `5775572` | 24 | 0,0033 s | spełnione |
| komputer zespołu (Windows 11, Ryzen 7 5800X, Python 3.14.5), commit `b639c98` | 24 | 0,0046 s | spełnione |
| VM / komputer zespołu | 240 | 1,2446 s / 1,4416 s | poza zakresem projektu |

Pliki: [`results/lab7/timing-summary.csv`](../results/lab7/timing-summary.csv),
[`results/lab7/komputer-seba/timing-summary.csv`](../results/lab7/komputer-seba/timing-summary.csv).

### 5.4. Statusy wymagań

| ID | Wymaganie | Status | Dowód |
|---|---|---|---|
| R1 | Plan ogrzewania na kolejne 24 h | **spełnione** | TC-01, TC-06…TC-10 |
| R2 | Uwzględnienie cen energii | **spełnione** | TC-05 (droższe godziny 10–13 → inny plan), TC-01 |
| R3 | Temperatura w paśmie komfortu | **spełnione** na próbce (jedna doba, model referencyjny) | TC-01, TC-03, TC-04, TC-08, TC-11, §5.1 |
| R4 | Porównanie z klasycznym termostatem | **spełnione** | TC-02, TC-08, §5.1 (40/40) |
| R5 | Publiczne dane pogodowe z udokumentowanego źródła | **niesprawdzone** (w Lab 7 bez testów cudzych API; pobranie sprawdzone ręcznie tylko w Lab 6) | [`implementation.md` §2](./implementation.md#2-uruchomienie-głównego-przepływu) |
| R6 | Prognozowany koszt w zł | **spełnione** dla CLI i API; w GUI sprawdzone tylko ręcznie | TC-01, TC-02, TC-08 |
| N1 | Czas analizy doby ≤ 1 s | **spełnione** | §5.3 |
| U1 | Oszczędność w prawdziwym domu | **niesprawdzone** | brak reprezentatywnej próbki |

Źródło statusów: [`tests.md` §5](./tests.md#5-statusy-wymagań). Opisanie ograniczenia nie zmienia statusu R5 ani U1.

### 5.5. Trzy najważniejsze stwierdzenia

| # | Stwierdzenie | Co je potwierdza | Czego nie można wywnioskować |
|---|---|---|---|
| 1 | Na dobie 2026-10-13 plan DP kosztuje **5,35 zł zamiast 11,15 zł** termostatu (−5,81 zł, −52,06 %) przy **0 h** poniżej `T_min` (termostat: 4 h). Parametry: 24 h, `T_min` 21,0, `T_max` 22,5, `T_start` 21,8 °C, dane MD5 `729ecf79…`. | [`results/lab4/comparison.csv`](../results/lab4/comparison.csv); `check_lab4.py` K1–K7; TC-01, TC-02; [`results/lab7/quality.csv`](../results/lab7/quality.csv) (40/40) | rocznej ani miesięcznej oszczędności (jedna doba, jedna lokalizacja); wyniku dla innych budynków (jeden model); wyniku na prawdziwej prognozie — 52 % to raczej górna granica; że cała różnica wynika z cen — termostat przez opóźnienie 2 h jest też słabszy komfortowo |
| 2 | Wniosek o wyborze DP **nie zmienia się** przy `T_min` 21,5 °C: oszczędność 4,11 zł (36,06 %), DP nadal 0 h poniżej `T_min`, termostat 5 h. Cieplejsze pasmo kosztuje DP +1,93 zł/dobę. | [`results/lab4/sensitivity/comparison.csv`](../results/lab4/sensitivity/comparison.csv); `check_lab4.py`; `quality.csv` | odporności na zmianę innych parametrów (sprawdzono jeden parametr i jedną wartość); zachowania przy płaskiej taryfie lub mrozie na danych rzeczywistych (scenariusze w `packages/core/.../data/` są syntetyczne) |
| 3 | Analiza jednej doby trwa **ok. 0,003–0,005 s** (mediana, 5 powtórzeń), czyli ok. 200–300 razy poniżej kryterium 1 s. | [`results/lab7/timing-summary.csv`](../results/lab7/timing-summary.csv), [`results/lab7/komputer-seba/timing-summary.csv`](../results/lab7/komputer-seba/timing-summary.csv); [`tests.md` §3](./tests.md#3-pomiar-niefunkcjonalny) | czasu odpowiedzi w GUI (pomiar bez HTTP i rysowania); że planowanie kilku dni będzie równie szybkie — dla 240 h czas rośnie do 1,24–1,44 s (szybciej niż liniowo) |

## 6. Użycie i odtworzenie

**Prezentowana wersja:** tag `v1.0.0`. Kolejne poprawki — nowy tag (`v1.0.1`), taga nie przesuwamy.
Wynik odtworzenia ze świeżego klonu zapisuje Kacper Mazur w Issue „Odbiór v1.0.0” albo w opisie GitHub Release.

Odtworzenie dokładnie prezentowanej wersji:

```bash
git clone --branch v1.0.0 --single-branch https://github.com/MazutK/UPOSiE---Projekt-informatyczny.git projekt-odbior
cd projekt-odbior
git rev-parse HEAD
```

Dalej wyłącznie według [`README.md`](../README.md#instalacja) (instalacja, `python -m pytest`) i
[`user-guide.md`](./user-guide.md):

- przypadek poprawny: `python -m heating_optimizer --data data/processed/doba-live.csv --out wyniki/plan.csv`
  → 5,35 zł / 11,15 zł, „Oszczędność: 5.81 zł (52.1%)”, plik z 24 godzinami;
- przypadek błędny: `python -m heating_optimizer --data data/test/doba-invalid.csv --out wyniki/bad.csv`
  → „niepełna doba — brakujące godziny [2, …, 23]”, kod 1, brak pliku;
- GUI: `docker compose up --build` → <http://localhost:8080> (albo `npm run api` + `npm run dev` → <http://localhost:5173>).

Scenariusz demo i wariant awaryjny: [`presentation.md`](./presentation.md); slajdy: [`../presentation/slides.pdf`](../presentation/slides.pdf).

Dowód: [`README.md`](../README.md), [`user-guide.md`](./user-guide.md), tag `v1.0.0`.

## 7. Ograniczenia i kierunki rozwoju

**Czego wynik nie potwierdza:**

- oszczędności w prawdziwym domu (U1 niesprawdzone) — symulacja na jednym modelu budynku, nie pomiar;
- oszczędności w sezonie — oceniono jedną dobę z jednej lokalizacji;
- działania na prognozach — dane archiwalne oznaczają idealną prognozę cen i pogody;
- że DP wygrywa z dobrze ustawionym termostatem — wariant bazowy z histerezą spada poniżej `T_min` przez opóźnienie 2 h;
  uczciwszy wariant bazowy (np. wcześniejszy próg włączenia) może dać mniejszą różnicę;
- poprawności pobierania danych z PSE i Open-Meteo na żywo (R5 niesprawdzone w Lab 7);
- działania GUI — sprawdzane tylko ręcznie.

**Uzasadniony kolejny krok** (w tej kolejności):

1. **Wiele dób:** uruchomić `scripts/compare_methods.py` na całym sezonie grzewczym z PSE i Open-Meteo, raportować
   rozkład oszczędności, a nie jedną liczbę. To bezpośrednio odpowiada na ograniczenia stwierdzeń 1 i 2.
2. **Prognoza zamiast archiwum:** liczyć plan na prognozie pogody z dnia poprzedniego i oceniać na danych rzeczywistych —
   mierzy, ile z 52 % zostaje przy prawdziwej niepewności.
3. **Mocniejszy wariant bazowy:** dołączyć do raportu porównania reguły z `baselines.py` (zachłanna, stały próg) i termostat
   z wcześniejszym progiem.
4. Zamknąć otwarte błędy B2 (zakresy pasma w CLI jak w `schemas.py`), B4 (`data_date` w odpowiedzi API) i B7 (próbka offline w Dockerze).
5. Plan wielodniowy dopiero po ograniczeniu liczby stanów w `optimizer.py` (B3) — obecnie poza zakresem.

Sterowanie urządzeniem na żywo i wiele budynków pozostają poza zakresem; ADR-001 opisuje, kiedy wtedy wrócić do bazy danych.

## 8. Wkład zespołu i źródła

### 8.1. Wkład zespołu

Wkład opisany rezultatami. Commity i PR na `main`; numery PR według GitHuba.

| Osoba | Rezultaty | Dowód (PR / commit / plik) |
|---|---|---|
| **Karol Brzozowski** | skrypt przygotowania doby z PSE i Open-Meteo (Lab 3); skrypt porównania termostat vs DP (Lab 4); szkielet architektury i kontrakt `POST /api/optimize` (Lab 5); w GUI: domyślna data i pogoda z Open-Meteo przy awarii PSE, siatka wymuszeń 24 h; **Z-03** NaN → 422, **Z-04** zakresy `model_params` (Lab 6); plan TC-01…TC-07 i testy logiki (Lab 7); ten raport (Lab 8) | `c254263`, `a5560b6` (`scripts/prepare_data.py`); `5c40df6` (`scripts/compare_methods.py`); `dffc053`, `2853758` (`architecture.md` §3); `4c1351c`, `ff2a2a4`; PR #2 (`1332a69`, `01d4f35`); PR #7 (`f95f2c8`, `tests/test_logic.py`); `docs/report.md` |
| **Kacper Mazur** | surowa próbka PSE i kolekcja żądań `api/` (Lab 3); źródła i uzasadnienie metody (Lab 4); granice systemu i UC-01 (Lab 5); **Z-01** kontrola 24 godzin w CSV, **Z-02** GUI bez starego planu po błędzie, ochrona `--out` w CLI (Lab 6); CI i `user-guide.md` (Lab 7); README i tag `v1.0.0` (Lab 8) | `5119150`; `1993061`; `a92cec9`; PR #3 (`edac7ee`, `e36b51d`, `816a335`, `56ff9c7`); PR #15 (`9f4bdf2`, `.github/workflows/check.yml`); PR #21 (otwarty) |
| **Sebastian Król** | opis przetwarzania (Lab 3); niezależna kontrola obliczeń `check_lab4.py` (Lab 4); przegląd architektury (Lab 5); integracja MVP, **Z-10**, `implementation.md` (Lab 6); pomiar czasu UC-01 i sprawdzenie dokumentacji ze świeżego klonu (Lab 7); obserwator próby prezentacji (Lab 8) | `853db90`; `3820dd5`; `ee1670b`; PR #6 (`42d65c7`, `01cfc0f`); `fdf988b`, PR #19 (`8947c51`, `results/lab7/`); `presentation.md` §5 |
| **Sebastian Rączka** | początkowy monorepo (silnik, API, GUI, Docker), surowa próbka Open-Meteo, podział obowiązków w `PROJEKT.md`; rozszerzenia GUI: dane publiczne, porównanie metod, wrażliwość, wymuszenia, eksport; wyniki porównania i próba wrażliwości (Lab 4); diagram sekwencji i przepływ danych (Lab 5); **Z-05**, **P-02**, ocena usprawnienia `sensitivity.py` (Lab 6); ocena jakości po integracji, statusy wymagań, znane błędy (Lab 7); slajdy i scenariusz demo (Lab 8) | `6344c1c`, `b879817`; `bbc41a4` (`results/lab4/`); `b47f4e6`; PR #5 (`dd8ad5a`, `b93dffd`, `487344f`); PR #17 (`5007ca0`, `results/lab7/quality.csv`); PR #20 (`91363ef`); jako `ai3izu`: `af0168d`, `c9e48b7`, `1ba34ca` |
| **Oskar Wysocki** | słownik danych (Lab 3); próbka doby i warunki porównania (Lab 4); ADR-001 i lista elementów istniejących/planowanych (Lab 5); **Z-08**, **Z-09**, **P-01** — doba live z metadanymi, zapis atomowy poza repo (Lab 6); test integracyjny UC-01 i poprawka NaN w CLI, Issue #13 (Lab 7); instrukcja użytkownika i sprawdzenie demo (Lab 8) | `63841fe`; `36bf9e7`; `200d8b4` (`decisions/001-storage.md`); PR #1 (`fbc5b4f`, `4c396aa`); PR #14, #16 (`c02b614`, `7b1a752`, `aef2ac7`) |
| **Patryk Uchman** | kontrola jakości przetworzonej doby `check_data.py` (Lab 3); instrukcja uruchomienia, odtworzenie i wnioski (Lab 4); model danych i podpowiedź w analizie wrażliwości (Lab 5); **Z-06** MD5 danych w wyniku, **Z-07** brak cichego nadpisania (Lab 6); `tests.md` — statusy i tabela stwierdzeń (Lab 8) | `24d8ecc`; `b144760`; `1df40f9`, `2b654a8`; PR #4 (`0ab31b5`, `dc2d17e`) |

### 8.2. Źródła literaturowe

- D. P. Bertsekas, *Dynamic Programming and Optimal Control*, t. I, wyd. 4, Athena Scientific, 2017, rozdz. 1;
  ISBN 978-1-886529-43-4; <https://www.mit.edu/~dimitrib/dpbook.html> — sformułowanie problemu DP, rozszerzenie stanu przy opóźnieniu.
- F. Oldewurtel i in., *Use of model predictive control and weather forecasts for energy efficient building climate control*,
  Energy and Buildings 45 (2012) 15–27, DOI: 10.1016/j.enbuild.2011.09.022 — porównanie z regułą (RBC), horyzont 24 h z krokiem 1 h,
  odrzucona alternatywa SMPC.

Szczegóły wykorzystania: [`experiment.md` §4](./experiment.md#4-źródła-i-uzasadnienie-metody).

### 8.3. Źródła danych

| Źródło | Właściciel | Adres | Licencja / warunki | Data dostępu |
|---|---|---|---|---|
| Rynkowa cena energii RCE | Polskie Sieci Elektroenergetyczne S.A. | <https://api.raporty.pse.pl/api/rce-pln> | dane publiczne, bez klucza; **warunków licencji nie potwierdziliśmy w dokumencie PSE** — do sprawdzenia | próbka: doba 2026-10-13 (`data/raw/pse-rce-sample.json`); dane live pobierane w GUI |
| Pogoda (temperatura 2 m, promieniowanie krótkofalowe) | Open-Meteo | <https://archive-api.open-meteo.com/v1/archive>, <https://api.open-meteo.com/v1/forecast> | dane API na licencji CC BY 4.0 (<https://open-meteo.com/en/licence>), darmowe API do użytku niekomercyjnego (<https://open-meteo.com/en/terms>); wymagane przypisanie źródła | próbka: doba 2026-10-13 (`data/raw/open-meteo-sample.json`); licencję sprawdzono 2026-11-24 |

Uwaga: licencja CC BY 4.0 wymaga podania źródła tam, gdzie dane są wyświetlane — w GUI nie ma jeszcze napisu
„Weather data by Open-Meteo.com” (do dodania).

### 8.4. Biblioteki i kod zewnętrzny

| Biblioteka | Zastosowanie | Licencja |
|---|---|---|
| pandas | przetwarzanie danych (Lab 3) | BSD-3-Clause |
| FastAPI, Pydantic | API i walidacja żądań | MIT |
| Uvicorn | serwer API | BSD-3-Clause |
| pytest, httpx | testy | MIT, BSD-3-Clause |
| Ruff | lint | MIT |
| React, Recharts | GUI i wykresy | MIT |
| Vite, ESLint | budowanie i lint GUI | MIT |
| TypeScript | typowanie GUI | Apache-2.0 |

Wersje: `requirements.txt`, `requirements-dev.txt`, `apps/web/package.json` (wersje bez górnych ograniczeń —
uwaga z [`tests.md` §6](./tests.md#6-sprawdzenie-dokumentacji)). Przykłady z instrukcji laboratoriów są w `examples/lab4/`
i `examples/lab6/`, oddzielnie od kodu projektu. **Repozytorium nie ma pliku licencji projektu** (`LICENSE`).

### 8.5. Wsparcie AI

| Kto | Narzędzie | Zakres pomocy | Jak sprawdzono wynik |
|---|---|---|---|
| zespół, Lab 4 | Claude (Anthropic) | szkic `scripts/compare_methods.py`, `scripts/check_lab4.py` i `experiment.md` | ręczne przeliczenie godzin 0 i 9 oraz sum kosztów; niezależny skrypt kontroli bez importu silnika; test na celowo błędnej kopii wyników ([`experiment.md` §9](./experiment.md#9-odtworzenie-i-użycie-agenta-ai)) |
| Karol Brzozowski, Lab 8 | Claude (Anthropic) | zebranie treści z dokumentów Lab 1–7 w szkic tego raportu | każda liczba porównana z plikiem wyniku (`comparison.csv`, `quality.csv`, `timing-summary.csv`); ponownie uruchomione `pytest`, CLI (przypadek poprawny i błędny) i `check_lab4.py` na `791545e`; licencja Open-Meteo sprawdzona na stronie źródła; linki sprawdzone w podglądzie GitHuba |
| _pozostałe osoby_ | _do uzupełnienia w przeglądzie PR: narzędzie, zakres, sposób sprawdzenia_ | | |

Odpowiedź czatu nie była traktowana jako dowód — dowodem są pliki wyników, testy i dokumentacja źródeł.

---

## Do zamknięcia przed tagiem `v1.0.0`

_Sekcja robocza — usunąć, gdy wszystkie punkty są zamknięte._

- [ ] Usunąć `docs/Karta_projektu.docx` i odwołania do niej w `docs/PROJEKT.md` (Oskar).
- [ ] `docs/DEMO.md`: zdanie o „30–50 %” zastąpić wynikiem z warunkami i linkiem do `results/lab4/comparison.csv`; lista
  „Zespół projektowy” w `DEMO.md` nie zgadza się z §8.1 (Oskar).
- [ ] Scalić PR #21 (README, opis GUI w `user-guide.md`, Issue #18) (Kacper).
- [ ] `docs/presentation.md`: wersja `v1.0.0` jest tam opisana jako commit `95b358d`, a `main` jest już na `791545e` —
  wpisać commit taga; czasy 0,005 s / 1,65 s nie zgadzają się z `results/lab7/` (0,0033–0,0046 s / 1,24–1,44 s);
  plan B mówi o próbce offline z `data/raw/` w Dockerze, a obraz jej nie ma (B7) (Seba Rączka).
- [ ] `docs/tests.md`: uzupełnić wiersz dziennika dla commita taga (Patryk).
- [ ] Wpisać commit taga w nagłówku tego raportu (Karol, po tagu).

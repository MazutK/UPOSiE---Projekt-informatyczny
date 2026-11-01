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

| Źródło: autor lub instytucja, tytuł, rok i link/DOI | Metoda lub wniosek przydatny w projekcie | Założenie albo ograniczenie | Co wykorzystano? |
|---|---|---|---|
| D. P. Bertsekas, *Dynamic Programming and Optimal Control*, t. I, wyd. 4, Athena Scientific, 2017, rozdz. 1 (1.2 „The Basic Problem”, 1.3 „The Dynamic Programming Algorithm”, 1.4 „State Augmentation and Other Reformulations”); ISBN 978-1-886529-43-4; https://www.mit.edu/~dimitrib/dpbook.html | Problem decyzyjny w N etapach z kosztem sumowanym po etapach; zasada optymalności (końcówka planu optymalnego jest optymalna dla podproblemu startującego z tego samego stanu), więc optimum to ciąg prostych minimalizacji etap po etapie; rozszerzenie stanu, gdy decyzja działa z opóźnieniem | Skończony horyzont, koszt addytywny w czasie, znany model przejścia stanu; nakład obliczeń rośnie z liczbą stanów | Sformułowanie `find_optimal_schedule`: 24 etapy (godziny), decyzja 0/1, koszt = kara za zimno + zł; stan = temperatura + historia grzałki (opóźnienie 2 h obsłużone rozszerzeniem stanu jak w p. 1.4) |
| F. Oldewurtel, A. Parisio, C. N. Jones, D. Gyalistras, M. Gwerder, V. Stauch, B. Lehmann, M. Morari, *Use of model predictive control and weather forecasts for energy efficient building climate control*, Energy and Buildings 45 (2012) 15–27, DOI: 10.1016/j.enbuild.2011.09.022 | Sterowanie predykcyjne z prognozą pogody (MPC, także stochastyczne SMPC) zużywa wyraźnie mniej energii niż sterowanie regułowe (RBC, obecna praktyka); horyzont 24 h z krokiem 1 h wystarczał, by większość badanych przypadków była w granicy 5 % od teoretycznego optimum | Badanie symulacyjne (rok 2007, model RC budynku); celem jest zużycie nieodnawialnej energii pierwotnej, nie koszt przy cenach dynamicznych (zmienne wagi kosztu są dopuszczone, ale wyników dla cen dynamicznych brak); niepewność prognozy modelowana jawnie | Uzasadnienie porównania z regułą (termostat = odpowiednik RBC, wymaganie R4), horyzontu 24 h z krokiem 1 h oraz oceny dwiema miarami: koszt i naruszenia pasma komfortu |

**Uzasadnienie wyboru metody.** Problem ma strukturę „problemu podstawowego” z rozdz. 1 Bertsekasa:
24 etapy, dwie decyzje na etap, koszt sumowany po godzinach, stan zależny od poprzedniej decyzji.
Ceny RCE i pogoda dla 2026-10-13 są danymi archiwalnymi, więc w porównaniu nie ma zakłóceń losowych
i DP daje plan optymalny dla przyjętego modelu budynku (z dokładnością do siatki 0,05 °C, na której
silnik łączy stany). Silnik liczy warstwy stanów od pierwszej godziny i odtwarza plan od końca —
dla problemu deterministycznego daje to ten sam wynik co rekurencja wsteczna z p. 1.3.
Koszt porównywany jest leksykograficznie: najpierw kara za zimno, potem zł (zgodnie z p. 3).
Wariant bazowy — termostat z histerezą — odpowiada sterowaniu regułowemu (RBC), z którym
Oldewurtel i in. porównują MPC.

**Odrzucona alternatywa: stochastyczne MPC (SMPC) w ruchomym horyzoncie**, jak u Oldewurtela i in.
Wymaga modelu błędu prognozy (pogody, a u nas także cen) i solvera optymalizacji stożkowej, a w tym
porównaniu dane są znane z góry, więc nie ma niepewności do modelowania. Skutek: wynik DP jest
oszczędnością przy idealnej prognozie — w działaniu na prognozach będzie niższy (do p. 8).

### Demonstracja z instrukcji (`examples/lab4/`)

Przed adaptacją uruchomiono przykład prognozy zgłoszeń z instrukcji Lab 4 (dane syntetyczne,
12 dni, historia początkowa 8 dni, ocena dni 9–12, bez losowania):

```
python examples/lab4/compare_forecasts.py examples/lab4/data/popyt.csv examples/lab4/results/okno3 --window 3
python examples/lab4/compare_forecasts.py examples/lab4/data/popyt.csv examples/lab4/results/okno5 --window 5
```

| Okno | Dni oceny | MAE — ostatnia wartość | MAE — średnia ruchoma | Spadek MAE ≥ 0,5? |
|---|---|---|---|---|
| 3 | 4 | 1,5 | 1,0 | tak |
| 5 | 4 | 1,5 | 1,5 | nie |

Ręczna kontrola (9 października): wariant bazowy = 15, średnia z 6–8 października (14, 13, 15) = 14,
rzeczywista wartość = 14, więc błędy 1 i 0 — zgodnie z `results/okno3/observations.csv`.
Wyniki zgadzają się z instrukcją. Średnia nie może zawierać prognozowanego dnia, bo w chwili
prognozy jego wartość nie jest znana (wyciek informacji). Zmiana okna z 3 na 5 dni usuwa przewagę
metody — ranking zależy od parametru, dlatego w naszym porównaniu zaplanowano próbę wrażliwości (p. 3).

## 5. Implementacja wariantów

Skrypt: `scripts/compare_methods.py` (tylko biblioteka standardowa + istniejący pakiet `packages/core`).
Silnika nie zmieniano — skrypt woła gotowe funkcje:

| Wariant | Funkcja silnika | Reguła |
|---|---|---|
| bazowy `termostat` | `simulate_thermostat(model, inputs, t_min, t_max, t_start)` | T ≤ T_min → 1, T ≥ T_max → 0, inaczej poprzedni stan; ceny ignorowane |
| metoda `dp` | `find_optimal_schedule(model, inputs, ComfortBand(...), t_start)` | najtańszy plan 0/1 na 24 h, najpierw kara za zimno, potem zł |

Co robi skrypt:
1. sprawdza wejście: 4 kolumny, 24 unikalne godziny 0..23, brak pustych / nieskończonych wartości;
2. liczy oba plany na **tych samych** danych, modelu i paśmie;
3. zapisuje `observations.csv` (1 wiersz = 1 godzina: cena, pogoda, decyzja, temperatura i koszt obu wariantów);
4. zapisuje `comparison.csv` (1 wiersz = 1 wariant: koszt, kWh, godziny grzania, godziny poniżej T_min,
   deficyt °C·h, średnia/min/max T, oszczędność zł i %, czy spełnione kryterium);
5. nie pozwala nadpisać pliku wejściowego.

Parametry z linii poleceń: `--t-min`, `--t-max`, `--t-start`, `--max-overshoot`, `--min-saving-pct`
(domyślne = wartości z p. 3). Brak losowania.

## 6. Wyniki i próba wrażliwości

_(uzupełnia Osoba 4)_

## 7. Kontrola obliczeń

_(uzupełnia Osoba 5)_

## 8. Wnioski i ograniczenia

_(uzupełnia Osoba 6)_

## 9. Odtworzenie i użycie agenta AI

_(uzupełnia Osoba 6)_

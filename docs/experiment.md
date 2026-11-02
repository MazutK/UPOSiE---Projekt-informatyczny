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

Pliki: `results/lab4/observations.csv`, `results/lab4/comparison.csv`,
`results/lab4/sensitivity/observations.csv`, `results/lab4/sensitivity/comparison.csv`.

| Wariant i parametry | Dane lub scenariusz | Liczba przypadków | Miara, jednostka i wynik | Koszt lub ograniczenie |
|---|---|---|---|---|
| Bazowy: termostat, T_min 21,0, T_max 22,5, start 21,8 | `doba-live.csv`, 2026-10-13 | 24 h | 11,15 zł; 15,0 kWh; 4 h poniżej T_min (min 20,65 °C) | grzeje 7:00–16:00, w tym drogie 7–9 |
| Metoda: DP, te same parametry, max_overshoot 1,0 | `doba-live.csv`, 2026-10-13 | 24 h | 5,35 zł; 9,0 kWh; 0 h poniżej T_min (min 21,02 °C) | grzeje 0–1 i 10–13 (tanie godziny) |
| Próba wrażliwości: T_min 21,5 (reszta bez zmian) | `doba-live.csv`, 2026-10-13 | 24 h | termostat 11,39 zł / 5 h poniżej; DP 7,28 zł / 0 h poniżej | DP droższy o 1,93 zł względem T_min 21,0 |

Różnica podstawowa: DP − termostat = **−5,81 zł (−52,1 %)**, godziny poniżej T_min 0 vs 4.
Kryterium praktyczne (≥ 5 % i nie zimniej): **spełnione** (`kryterium_spelnione = true`).

Wrażliwość: przy T_min 21,5 oszczędność spada do −4,11 zł (−36,1 %), DP nadal 0 h poniżej T_min,
termostat 5 h. **Wniosek o wyborze metody się nie zmienia.** Cieplejsze pasmo kosztuje DP
+1,93 zł/dobę (+36 %).

Parametru wrażliwości nie dobierano po obejrzeniu wyników — T_min 21,5 zapisano w p. 3 przed uruchomieniem.
Brak losowania, więc brak rozrzutu między powtórzeniami; dwa uruchomienia dają identyczne pliki.

## 7. Kontrola obliczeń

Skrypt: `scripts/check_lab4.py` (tylko biblioteka standardowa). **Nie importuje silnika ani pandas** —
przelicza wszystko od nowa z `observations.csv` i `comparison.csv`, więc nie powtarza ewentualnego
błędu z `scripts/compare_methods.py`. Moc grzałki czyta z `parametry.json` (1,5 kW).

| Kontrola | Co sprawdza |
|---|---|
| K1 | struktura: kolumny obu plików, godziny 0..23 kolejno i bez powtórzeń, warianty `termostat` + `dp`, `n_godzin` = 24, te same parametry i dane |
| K2 | decyzje u ∈ {0, 1}; `godziny_grzania` = Σu; `energia_kwh` = Σu · 1,5 kWh |
| K3 | koszt każdej godziny = u · 1,5 kW · 1 h · cena [zł/kWh] (tolerancja 0,0001 zł) |
| K4 | suma 24 kosztów godzinowych = `koszt_pln` w `comparison.csv` (tolerancja 0,002 zł) |
| K5 | z kolumny temperatur: godziny < T_min, deficyt °C·h, średnia / min / max T |
| K6 | oszczędność zł i % względem termostatu, `kryterium_spelnione` (≥ 5 % **i** nie więcej godzin < T_min) |
| K7 | cena i pogoda w `observations.csv` zgodne z plikiem z kolumny `dane` (`data/processed/doba-live.csv`) |

### Uruchomienie na wynikach Osoby 4

```
python scripts/check_lab4.py results/lab4              → Kontrola OK (K1-K7)
python scripts/check_lab4.py results/lab4/sensitivity  → Kontrola OK (K1-K7)
```

### Ręczne przeliczenie (kalkulator)

Koszt godziny = u · 1,5 kWh · cena.

| Co | Obliczenie ręczne | W pliku | Zgodne? |
|---|---|---|---|
| Godz. 0, DP (u = 1) | 1 · 1,5 · 0,6373 = 0,95595 zł | `dp_koszt_pln` = 0,9559 | tak (różnica 0,00005 = zaokrąglenie zapisu do 4 miejsc) |
| Godz. 9, termostat (u = 1, T = 20,83 °C < T_min, grzałka włączona od godz. 7) | 1 · 1,5 · 0,8085 = 1,21275 zł | `termostat_koszt_pln` = 1,2127 | tak (jw.) |
| Suma, termostat (grzeje 7–16, 10 h) | Σ cen = 1,1177 + 1,0366 + 0,8085 + 0,5809 + 0,5753 + 0,5321 + 0,6045 + 0,6356 + 0,6959 + 0,8479 = 7,4350 zł/kWh; · 1,5 = **11,1525 zł** | `koszt_pln` = 11,1525 | tak |
| Suma, DP (grzeje 0–1 i 10–13, 6 h) | Σ cen = 0,6373 + 0,6345 + 0,5809 + 0,5753 + 0,5321 + 0,6045 = 3,5646 zł/kWh; · 1,5 = **5,3469 zł** | `koszt_pln` = 5,3469 | tak |
| Oszczędność | 11,1525 − 5,3469 = 5,8056 zł; 5,8056 / 11,1525 = **52,06 %** | 5,8056 / 52,06 | tak |

Suma zaokrąglonych kosztów godzinowych termostatu daje 11,1524 zł (o 0,0001 mniej niż `koszt_pln`,
liczony z pełnej precyzji) — dlatego K4 ma tolerancję 0,002 zł, a K3 0,0001 zł.

### Test na błędnej kopii

`results/lab4/*.csv` skopiowano do katalogu poza repozytorium (`~/lab4-zla-kopia/`)
i w `observations.csv` zmieniono `dp_koszt_pln` w godzinie 0 z 0,9559 na 0,5:

```
python scripts/check_lab4.py ~/lab4-zla-kopia
Kontrola niezaliczona (K3, K4):
- K3: dp, godz. 0: 1 * 1.5 * 0.6373 = 0.9559 zl, w pliku 0.5
- K4: dp: suma godzin 4.8910 zl != koszt_pln 5.3469
```

Padły dokładnie K3 (zły koszt godziny) i K4 (suma godzin ≠ koszt doby), kod wyjścia 1.
Pozostałe kontrole przeszły, bo zmiana nie dotyka decyzji, temperatur, `comparison.csv` ani danych wejściowych.
Skrypt wykrywa więc ręczną edycję wyniku. Pliki w `results/lab4/` nie były zmieniane.

**Wniosek:** liczby w p. 6 są spójne z plikami godzinowymi i z danymi Lab 3; niezależne przeliczenie
potwierdza koszt 11,15 zł (termostat) vs 5,35 zł (DP) i oszczędność 52,1 %.

## 8. Wnioski i ograniczenia


**Który wariant jest lepszy i o ile?** DP: 5,35 zł zamiast 11,15 zł na dobę 2026-10-13,
czyli −5,81 zł (−52,1 %), przy 0 h poniżej T_min (termostat: 4 h). Kryterium praktyczne
(≥ 5 % i nie zimniej) jest spełnione.

**Czy poprawa uzasadnia koszt i złożoność?** Tak w tej próbie: DP nie wymaga nowych danych
(te same ceny i pogoda co termostat) ani nowego sprzętu, a liczy się w ułamku sekundy.
Dodatkowy koszt to potrzeba cen na kolejną dobę — RCE jest publikowane dzień wcześniej.

**Czy próba wrażliwości zmieniła wniosek?** Nie. Przy T_min 21,5 °C DP nadal tańszy (−36,1 %)
i nadal 0 h poniżej T_min.

**Czego nie można wnioskować z tej próby:**
- rocznej ani miesięcznej oszczędności — to jedna doba z jednej lokalizacji;
- skuteczności dla innych budynków — model to jeden budynek referencyjny;
- wyniku przy prawdziwej prognozie — dane archiwalne = idealna prognoza cen i pogody,
  więc 52 % to raczej górna granica (por. Oldewurtel i in., 2012);
- że cała oszczędność wynika z „patrzenia na ceny” — termostat przez opóźnienie 2 h
  spada poniżej T_min, więc jest też słabszy komfortowo; uczciwszy wariant bazowy
  (np. termostat z wcześniejszym progiem włączenia) może dać mniejszą różnicę.

**Czego brakuje do sprawdzenia:** wielu dób (np. cały sezon grzewczy z PSE i Open-Meteo),
prognozy pogody zamiast archiwum, trzeciej reguły z `baselines.py` (Osoba 4 w `PROJEKT.md`)
oraz siatki wrażliwości z `sensitivity.py` (Osoba 5).

Obserwowana różnica dotyczy tej doby i tego modelu — to wynik symulacji, nie pomiar w domu.

## 9. Odtworzenie i użycie agenta AI


**Odtworzenie** (osoba inna niż autor skryptu i wyników):

| Element | Wynik                                                   |
|---|---------------------------------------------------------|
| Kto i kiedy | pu-ctrl, 02.11.2026                                     |
| Środowisko | Windows, Python 3.14, `.venv`                           |
| Kroki | świeży `git clone`, polecenia z `README.md` → sekcja Lab 4 |
| Porównanie | `git status --short results/` → brak zmian = pliki identyczne |
| `check_lab4.py` | [Kontrola OK (K1–K7)]                                   |
| Wynik | zgodny                                                  |

**Agent AI:** użyto agenta (Claude) do przygotowania szkicu `scripts/compare_methods.py`,
`scripts/check_lab4.py` i tego dokumentu. Agent dostał: plik `doba-live.csv`, słownik
danych z Lab 3 i warunki z p. 3. Sprawdzenie: ręczne przeliczenie godzin 0 i 9 oraz sumy
kosztów (p. 7), niezależny skrypt kontroli bez importu silnika, test na celowo błędnej kopii.
Parametrów nie zmieniano po obejrzeniu wyników.


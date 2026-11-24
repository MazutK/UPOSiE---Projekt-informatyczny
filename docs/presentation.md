# Scenariusz prezentacji i demonstracji systemu (Lab 8)

**Projekt:** Optymalizator ogrzewania elektrycznego przy zmiennych cenach energii  
**Wersja:** `v1.0.0` (commit `95b358d` na gałęzi `main`)  
**Autor scenariusza:** Sebastian Rączka  
**Obserwator próby / pomiar czasu:** Sebastian Król  
**Czas wystąpienia:** limit 7 minut (wynik próby generalnej: **6 min 20 s**)  
**Slajdy:** `presentation/slides.pdf` / `presentation/slides.md` (7 slajdów w formacie Marp)  

---

## 1. Informacje ogólne i przygotowanie stanowiska

1. **Aplikacja:**
   - Dostępna w kontenerze Docker: [http://localhost:8080](http://localhost:8080)
   - Tryb lokalny (deweloperski): [http://localhost:5173](http://localhost:5173) (FastAPI na porcie 8000)
2. **Wymagania techniczne przed uruchomieniem:**
   - Uruchomiony kontener: `docker compose up --build`
   - Otwarta przeglądarka internetowa w trybie pełnoekranowym na stronie głównej aplikacji.
   - Otwarty terminal w katalogu repozytorium z aktywnym środowiskiem `.venv` do szybkiej demonstracji CLI i odporności na błędy (Krok 6).
   - Wyczyszczony stan aplikacji (brak wymuszeń, domyślne pasmo komfortu: $T_{min}=21{,}0$ °C, $T_{max}=22{,}5$ °C, $T_{start}=21{,}8$ °C).

---

## 2. Podział ról i harmonogram minutowy (limit 7 min)

| Czas | Slajdy / Ekran | Kto mówi | Treść wystąpienia |
|---|---|---|---|
| **0:00 – 1:30** | Slajdy 1–2 | Karol, Kacper, Seba R. | Wprowadzenie, problem decyzyjny termostatów, zespół projektowy, źródła danych (PSE RCE + Open-Meteo) i fizyczny model budynku referencyjnego. |
| **1:30 – 3:00** | Slajdy 3–4 | Seba Rączka, Karol | Metoda Programowania Dynamicznego (DP) vs histereza termostatu, twarde wyniki eksperymentu Lab 4 (52% oszczędności, brak wychłodzeń), architektura trójwarstwowa i decyzja ADR-001 (zapis w plikach CSV/JSON). |
| **3:00 – 3:45** | Slajd 5 | Oskar, Patryk | Weryfikacja jakości (128 testów passed, 40/40 miar Lab 4 zgodnych w tolerancji, czas doby 0,005 s $\le 1$ s), płynne przełączenie ekranu na Live Demo w przeglądarce. |
| **3:45 – 5:45** | Przeglądarka (GUI) | Seba Rączka, Patryk, Kacper | **Demonstracja na żywo:** scenariusz szczytu wieczornego, pobranie danych live PSE/Open-Meteo, wymuszenia godzinowe (overrides), pobranie pliku CSV, analiza wrażliwości. |
| **5:45 – 6:30** | Terminal + Slajd 6 | Seba Rączka, Oskar | Przypadek błędny w CLI (odrzucenie uszkodzonej doby i wartości NaN), podsumowanie osiągniętych rezultatów i rzetelne omówienie ograniczeń projektu. |
| **6:30 – 7:00** | Slajd 7 | Wszyscy | Przedstawienie wkładu każdego członka zespołu i otwarcie dyskusji z prowadzącym. |

---

## 3. Przebieg demonstracji na żywo krok po kroku (Live Demo)

### Krok 1: Scenariusz wzorcowy ze szczytem cenowym (`doba_szczyt_wieczorny`)
* **Działanie:** W lewym panelu GUI w polu „Wybierz scenariusz” wybieramy `doba_szczyt_wieczorny`.
* **Ustawienia:** $T_{min} = 21{,}0$ °C, $T_{max} = 22{,}5$ °C, $T_{start} = 21{,}8$ °C.
* **Komentarz do publiczności:**
  * Wskazujemy wykres cen energii i harmonogram załączeń pieca: klasyczny termostat załącza grzałkę w godzinach 17:00–21:00, czyli w najdroższym szczycie popołudniowo-wieczornym.
  * Plan DP akumuluje ciepło w budynku przed szczytem i całkowicie wyłącza piec w drogich godzinach, obniżając rachunek o ponad połowę.
* **Oczekiwany wynik na ekranie:** Koszt DP: 5,35 zł vs termostat: 11,15 zł; godziny poniżej $T_{min}$: 0 h vs 4 h; oszczędność: **5,81 zł (52,1%)**.

### Krok 2: Pobranie danych publicznych live (`doba_live`)
* **Działanie:** W karcie „Dane publiczne (PSE + Open-Meteo)” klikamy przycisk **„Pobierz dobę”**.
* **Co dzieje się w systemie:** Usługa API odpytuje serwery PSE (ceny RCE) i Open-Meteo (temperatura, nasłonecznienie), składa 24 kolejne godziny doby i atomowo zapisuje plik w cache lokalnym.
* **Komentarz do publiczności:**
  * Zwracamy uwagę na etykietę źródła danych (`live_api` w przypadku połączenia sieciowego lub `offline_sample` przy pracy bez internetu).
  * System natychmiast przelicza optymalny plan dla rzeczywistej doby rynkowej.

### Krok 3: Interaktywne wymuszenia godzinowe (Overrides)
* **Działanie:** W sekcji „Wymuszenia godzin” klikamy godzinę **18:00**, przestawiając stan z AUTO na **ON (1)**.
* **Komentarz do publiczności:**
  * Pokazujemy natychmiastową reakcję interfejsu (czas obliczeń silnika to ok. 5 ms).
  * Koszt energii rośnie, ponieważ wymusiliśmy pracę pieca w droższej godzinie.
  * Zwracamy uwagę na komunikat (usprawnienie Z-05): termostat nie obsługuje wymuszeń użytkownika, więc jego plan pozostaje referencyjny.
  * Klikamy **„Wyczyść wymuszenia”**, powracając do czystego optimum.

### Krok 4: Eksport planu do pliku CSV
* **Działanie:** Klikamy przycisk **„Pobierz plan godzinowy (CSV)”**.
* **Oczekiwany wynik:** Przeglądarka generuje i pobiera plik CSV z nazwą zawierającą scenariusz i pasmo (`plan_doba_szczyt_wieczorny_21.0-22.5.csv`).
* **Komentarz:** Plik zawiera 24 wiersze z kompletem danych godzinowych: cenę, temperaturę zewnętrzną, nasłonecznienie oraz stany i temperatury obu wariantów.

### Krok 5: Tabela porównawcza i analiza wrażliwości (Sensitivity Analysis)
* **Działanie:** Przewijamy stronę w dół do sekcji tabeli metod i analizy wrażliwości.
* **Komentarz:**
  * Tabela 4 metod pokazuje porównanie DP nie tylko z termostatem, ale też z heurystyką zachłanną (dogrzewanie poniżej mediany ceny) oraz stałym progiem.
  * Zmieniamy suwak parametru $T_{min}$ na $21{,}5$ °C: koszt DP rośnie do 7,28 zł (o 1,93 zł), ale oszczędność względem termostatu nadal wynosi 36,1% (4,11 zł), bez wychłodzeń.
  * Klikamy „Eksportuj tabelę do CSV”, pokazując możliwość pobrania pełnej siatki wrażliwości.

### Krok 6: Przypadek błędny — odporność na awarie i walidacja CLI
* **Działanie:** Przełączamy się na chwilę do terminala i uruchamiamy polecenie z błędną, niepełną dobą:
  ```bash
  python -m heating_optimizer --data data/test/doba-invalid.csv --out wyniki/blad.csv
  ```
  oraz próbę z nieliczbową wartością:
  ```bash
  python -m heating_optimizer --t-min nan
  ```
* **Oczekiwany wynik w terminalu:**
  * Kod wyjścia `1`.
  * Komunikat błędu na `stderr`: `Błąd: doba-invalid.csv: niepełna doba — brakujące godziny [2, 3, …, 23]`.
  * Plik `wyniki/blad.csv` **nie zostaje utworzony** (brak fałszywych planów za 0 zł).
  * Dla NaN: `Błąd: temperatura musi być skończoną liczbą, otrzymano 'nan'`.

---

## 4. Wariant awaryjny (Plan B)

Na wypadek nieprzewidzianych problemów technicznych podczas obrony przygotowano:
1. **Brak dostępu do internetu:**
   - Aplikacja posiada wbudowany, przetestowany mechanizm offline fallback.
   - W przypadku braku łączności z API PSE / Open-Meteo endpoint `/api/live` automatycznie ładuje zweryfikowaną próbkę z `data/raw/*-sample.json` (doba 2026-10-13, MD5 `729ecf79...`) i wyświetla stosowny komunikat w UI.
2. **Problem z kontenerem Docker / portem 8080:**
   - Dostępne jest uruchomienie bezpośrednie: `npm run api` (FastAPI) oraz `npm run dev` (Vite) na porcie 5173.
   - W ostateczności demonstrację można w 100% przeprowadzić w terminalu za pomocą CLI (`python -m heating_optimizer --data data/processed/doba-live.csv`), które generuje pełną tabelę tekstową i podsumowanie kosztów.
3. **Pliki zapasowe:**
   - Kompletny raport z zrzutami ekranu i tabelami znajduje się w `docs/user-guide.md` oraz `docs/report.md`.

---

## 5. Wyniki próby generalnej (notatki obserwatora: Sebastian Król)

* **Termin próby:** 2026-11-24, godz. 11:30.
* **Środowisko testowe:** System Windows 11, przeglądarka Brave, Docker Desktop z obrazem `v1.0.0`.
* **Zmierzone czasy poszczególnych modułów:**
  - Slajdy wstępne (1–4: problem, dane, metoda, architektura): **2 min 40 s**
  - Przejście do aplikacji (slajd 5): **0 min 35 s**
  - Live Demo GUI (kroki 1–5): **2 min 10 s**
  - Przypadek błędny CLI (krok 6): **0 min 30 s**
  - Wnioski, ograniczenia i wkład (slajdy 6–7): **0 min 25 s**
  - **Łączny czas wystąpienia:** **6 minut 20 sekund** (limit 7 minut w pełni zachowany).

### Wnioski z próby i wprowadzone poprawki:
1. **Uproszczenie żargonu:**
   - W pierwotnej wersji pojawiły się sformułowania typu: *„leksykograficzna siatka stanów DP”* oraz *„parametr alfa modelu RC”*.
   - *Korekta:* Zastąpiono je czytelnymi pojęciami: *„algorytm, który najpierw bezwzględnie pilnuje ciepła, a w drugiej kolejności minimalizuje rachunek”* oraz *„tempo ucieczki ciepła przez ściany budynku”*.
2. **Wyjaśnienie opóźnienia bezwładności:**
   - Dodano precyzyjny komentarz, dlaczego termostat dopuszcza 4 godziny chłodu: bezwładność wynosi $d=2$ godziny, więc piec włączony o 15:00 zaczyna efektywnie grzać dopiero o 17:00.
3. **Konkretne liczby zamiast ogólników:**
   - Wycofano z prezentacji ogólne hasło „30–50% oszczędności” na rzecz twardego wyniku z pliku `results/lab4/comparison.csv`: dokładnie **52,1% (5,81 zł oszczędności)** dla doby bazowej oraz **36,1% (4,11 zł)** w próbie wrażliwości.

---

## 6. Pytania po prezentacji (i przygotowane odpowiedzi z dowodami)

Zestaw pytań przygotowanych na dyskusję z prowadzącym i audytorium:

### Pytanie 1: Dlaczego tradycyjny termostat dopuścił aż 4 godziny poniżej $T_{min}$, skoro pilnuje pasma komfortu?
* **Odpowiedź:** Wynika to z uwzględnienia w modelu fizycznym 2-godzinnego opóźnienia bezwładności cieplnej instalacji ($d=2\text{ h}$). Termostat z histerezą działa czysto reaktywnie: włącza grzałkę dopiero wtedy, gdy temperatura wewnętrzna spadnie do progu $T_{min}$ (21,0 °C). Ze względu na opóźnienie ciepło trafia do pomieszczenia 2 godziny później, w trakcie których temperatura nadal spada (osiągając minimum 20,65 °C). Optymalizator DP działa predykcyjnie — zna model budynku i włącza piec z 2-godzinnym wyprzedzeniem.
* **Dowód:** `docs/experiment.md` sekcja 6 i 7; test TC-03 w `tests/test_logic.py`.

### Pytanie 2: Czy oszczędność na poziomie 52% jest gwarantowana w każdym domu i przez cały rok?
* **Odpowiedź:** Nie, i otwarcie wskazujemy to w sekcji ograniczeń projektu (slajd 6). Wynik 52,1% uzyskano dla konkretnej doby jesiennej (13 października 2026 r.) z dużą dynamiką cen RCE (od 0,53 do 1,12 zł/kWh) oraz dla budynku referencyjnego. W środku mroźnej zimy piec musi pracować niemal nieprzerwanie, więc możliwości przesuwania poboru maleją. Ponadto symulacja zakładała idealną prognozę pogody i cen — błędy prognozy w realnym domu obniżą oszczędność o kilka punktów procentowych.
* **Dowód:** `docs/experiment.md` sekcja 8 (Ograniczenia); `docs/tests.md` sekcja 5 (status wymagania U1).

### Pytanie 3: Jak zachowa się algorytm, jeśli ceny energii przez całą dobę będą stałe (taryfa płaska)?
* **Odpowiedź:** W przypadku taryfy płaskiej algorytm DP minimalizuje sumaryczną energię potrzebną do utrzymania komfortu. Oszczędność finansowa spadnie do 2–5%, wynikających wyłącznie z precyzyjnego unikania przegrzewania budynku ponad $T_{max}$ oraz optymalnego wykorzystania darmowych zysków słonecznych w ciągu dnia.
* **Dowód:** Scenariusz testowy `doba_plaska_cena.csv` w pakiecie `packages/core`.

### Pytanie 4: Dlaczego zdecydowaliście się na wersjonowane pliki CSV/JSON zamiast bazy danych SQLite?
* **Odpowiedź:** Zostało to formalnie uzasadnione w decyzji architektonicznej ADR-001. Dane pojedynczej doby to zaledwie 24 wiersze (~1 KB tekstu). Baza danych nie dawała żadnej wartości dodanej, a utrudniała audytowalność eksperymentu. Zapis w plikach CSV pozwala na powiązanie każdej próby badawczej z sumą kontrolną MD5 danych (`729ecf79...`) oraz commitem na GitHubie, co gwarantuje 100% powtarzalność wyników bez konieczności migracji schematów bazodanowych w kontenerze.
* **Dowód:** `docs/decisions/001-storage.md`; `docs/architecture.md` sekcja 4.

### Pytanie 5: Czas obliczeń dla 24 godzin to 0,005 s, ale dla 240 godzin aż 1,65 s. Jak rozwiązać problem nieliniowego wzrostu złożoności?
* **Odpowiedź:** Złożoność programowania dynamicznego zależy od iloczynu liczby etapów i liczby stanów (temperatura $\times$ historia opóźnienia grzałki). W horyzoncie 24 h przestrzeń stanów jest zwarta, co daje czas poniżej 5 ms (zgodnie z kryterium N1 $\le 1$ s). W przypadku konieczności planowania na wiele dni w przód należałoby wdrożyć heurystykę przycinania rzadkich stanów (Beam Search) lub ruchomy horyzont predykcji (Receding Horizon), co odnotowaliśmy jako znane ograniczenie B3.
* **Dowód:** `docs/tests.md` sekcja 3 (pomiar niefunkcjonalny) oraz sekcja 7 (błąd B3).

### Pytanie 6: Co się stanie, gdy podczas pobierania danych live serwery PSE nie odpowiedzą?
* **Odpowiedź:** System posiada dwupoziomowy mechanizm awaryjny (ADR-001 i UC-01). Po pierwsze, w razie niepełnej odpowiedzi parser przerywa składanie doby, chroniąc przed powstaniem planu na niepełną liczbę godzin. Po drugie, API automatycznie serwuje ostatnią poprawnie skompletowaną dobę lub zweryfikowaną próbkę archiwalną z `data/raw/` i jawnie informuje użytkownika w UI (pole `source = offline_sample`), że wynik nie dotyczy wybranej daty.
* **Dowód:** `docs/architecture.md` sekcja 2.3 (Błędny przebieg B); `tests/test_live_day.py`.

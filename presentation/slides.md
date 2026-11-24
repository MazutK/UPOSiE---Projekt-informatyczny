---
marp: true
theme: default
paginate: true
header: "Optymalizator Ogrzewania Elektrycznego — Prezentacja Projektu v1.0.0"
footer: "Projekt SI 2026/2027 | Zespół: K. Mazur, S. Król, S. Rączka, K. Brzozowski, O. Wysocki, P. Uchman"
style: |
  section {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    padding: 35px 55px;
    font-size: 21px;
    background-color: #ffffff;
    color: #1e293b;
    line-height: 1.35;
  }
  h1 {
    color: #1e3a8a;
    font-size: 32px;
    margin-top: 0;
    margin-bottom: 12px;
  }
  h2 {
    color: #2563eb;
    font-size: 24px;
    margin-top: 0;
    margin-bottom: 10px;
  }
  h3 {
    color: #0f172a;
    font-size: 21px;
    margin-top: 10px;
    margin-bottom: 6px;
  }
  table {
    font-size: 17px;
    width: 100%;
    border-collapse: collapse;
    margin-top: 8px;
    margin-bottom: 8px;
  }
  th, td {
    padding: 6px 10px;
    border: 1px solid #cbd5e1;
  }
  th {
    background-color: #f1f5f9;
    color: #0f172a;
    font-weight: 600;
  }
  ul, ol {
    margin-top: 4px;
    margin-bottom: 6px;
    padding-left: 24px;
  }
  li {
    margin-bottom: 4px;
  }
  p {
    margin-top: 4px;
    margin-bottom: 6px;
  }
  .highlight {
    color: #1d4ed8;
    font-weight: bold;
  }
  .box {
    background-color: #f8fafc;
    border-left: 4px solid #3b82f6;
    padding: 8px 12px;
    margin-top: 6px;
    margin-bottom: 6px;
    font-size: 19px;
  }
---

# Optymalizator Ogrzewania Elektrycznego
## Sterowanie predykcyjne przy taryfie dynamicznej RCE (Wersja v1.0.0)

<div class="box">
<b>Problem decyzyjny:</b> Klasyczny termostat z histerezą steruje grzaniem tylko według temperatury chwilowej, dogrzewając dom w najdroższych godzinach szczytu. <b>Pytanie użytkownika:</b> <i>„Kiedy włączyć ogrzewanie w ciągu najbliższej doby, by zminimalizować koszt energii w zł przy zachowaniu pełnego komfortu?”</i>
</div>

### Zespół projektowy i odpowiedzialności:
* **Kacper Mazur** — panel konfiguracji GUI, klient HTTP, integracja wydania `v1.0.0`, GitHub Actions CI
* **Sebastian Król** — wizualizacja wyników w GUI, pomiary wydajnościowe UC-01, walidacja dokumentacji
* **Sebastian Rączka** — ocena jakości po integracji (Lab 7), analiza wrażliwości, diagramy architektury, slajdy i demo
* **Karol Brzozowski** — testy logiki silnika TC-01..TC-07, raport końcowy projektu, porównanie metod
* **Oskar Wysocki** — test integracyjny UC-01, walidacja CLI (NaN/inf), dane live PSE i Open-Meteo, user-guide
* **Patryk Uchman** — koordynacja repozytorium, model danych, obsługa wymuszeń godzin, eksport do CSV

---

# Źródła danych i model budynku

### Dane wejściowe (horyzont 24 h, krok 1 h):
* **PSE RCE (`api.raporty.pse.pl`):** Rynkowa Cena Energii — 96 kwadransów agregowane do 24 godzin doby (`price_pln_kwh` [zł/kWh]).
* **Open-Meteo (`api.open-meteo.com`):** temperatura zewnętrzna (`outside_temp_c` [°C]) oraz nasłonecznienie (`solar_radiation_wm2` [W/m²]).
* **Walidacja wejścia:** kontrola 24 unikalnych kolejnych godzin i liczb skończonych; automatyczny fallback na cache offline.

### Model fizyczny budynku referencyjnego (`parametry.json`):
* Równanie bilansu ciepła: $T[t+1] = T[t] - \alpha (T[t] - T_{zew}[t]) + \beta \cdot u[t-d] + \gamma \cdot G[t] + c$
* Parametry: stygnięcie $\alpha = 0{,}00532$, moc grzałki $\beta = 0{,}2694$ (moc $1{,}5$ kW), słońce $\gamma = 0{,}0002$, stała $c = -0{,}0520$.
* **Bezwładność cieplna:** opóźnienie reakcji $d = 2\text{ h}$ (decyzja włączona w godz. $t$ grzeje w godz. $t+2$).

<div class="box">
<b>Kluczowe ograniczenia danych:</b> Ceny na dobę kolejną publikowane są dzień wcześniej ok. 14:00 (częściowa dostępność wprzód); model opisuje jeden budynek referencyjny (brak adaptacji do innych obiektów bez nowej identyfikacji parametrów).
</div>

---

# Metoda: Programowanie Dynamiczne (DP) vs Termostat

### Zasada działania metod:
* **Termostat (bazowy):** histereza $T \le T_{min} \to u=1$, $T \ge T_{max} \to u=0$, ignoruje ceny energii i pogodę.
* **Optymalizator (DP):** 24 etapy decyzyjne, siatka $\Delta T = 0{,}05$ °C, leksykograficzna funkcja celu:
  1. *Priorytet 1 (Komfort):* Bezwzględna kara za spadek temperatury poniżej $T_{min}$.
  2. *Priorytet 2 (Ekonomia):* Minimalizacja sumarycznego kosztu zakupu energii elektrycznej w zł.

### Wyniki eksperymentu (`results/lab4/comparison.csv`, doba 2026-10-13, Warszawa, $T_{start}=21{,}8$ °C):

| Wariant i parametry | Koszt [zł] | Energia | Godz. grzania | Godziny $< T_{min}$ | Średnia $T$ | Oszczędność zł (%) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Termostat (bazowy)**, $T_{min}=21{,}0$ °C | 11,15 zł | 15,0 kWh | 10 h (godz. 7–16) | 4 h (min 20,65 °C) | 21,75 °C | — *(referencja)* |
| **DP (optymalizator)**, $T_{min}=21{,}0$ °C | **5,35 zł** | **9,0 kWh** | 6 h (0–1 i 10–13) | **0 h** (min 21,02 °C) | 21,53 °C | **−5,81 zł (−52,1%)** |
| **Wrażliwość**, $T_{min}=21{,}5$ °C | **7,28 zł** | 12,0 kWh | 8 h (0–1, 5, 10–14) | **0 h** (min 21,53 °C) | 21,94 °C | **−4,11 zł (−36,1%)** |

<div class="box">
<b>Mechanizm oszczędności:</b> DP akumuluje ciepło w tanich godzinach nocnych (0,53–0,64 zł/kWh) i unika szczytu (1,12 zł/kWh o 7:00). Termostat przez opóźnienie 2 h spóźnia się z grzaniem i wychładza dom poniżej pasma komfortu.
</div>

---

# Architektura systemu i decyzje projektowe (ADR)

### Trójwarstwowa struktura aplikacji:
* **Interfejs GUI (`apps/web`):** React + Vite + TypeScript. Interaktywne wykresy temperatur i cen, suwaki nastaw, obsługa wymuszeń godzinowych oraz eksport wyznaczonego planu do CSV.
* **Usługa API (`apps/api`):** FastAPI + Pydantic. Walidacja typów/zakresów (`schemas.py`), integracja pobierania danych live (`data_sources`), obsługa błędów HTTP 404/422/502.
* **Silnik obliczeniowy (`packages/core`):** Czysty Python. Deterministyczny algorytm DP, model budynku, symulacja termostatu, analiza wrażliwości parametrów.

### Kluczowa decyzja architektoniczna: ADR-001 (`docs/decisions/001-storage.md`):
* **Wybór:** Wersjonowane pliki CSV/JSON w repozytorium zamiast relacyjnej bazy SQLite.
* **Uzasadnienie:** Wolumen 1 doby to 24 wiersze (~1 KB); pełna odtwarzalność badań (wersja danych powiązana z sumą MD5 `729ecf79...` i commitem w Git); eliminacja narzutu migracji bazy danych w kontenerze Docker.

### Odporność na błędy brzegowe:
* Niepełna doba (np. brakujące kwadranse PSE) $\to$ przerwanie obliczeń z czytelnym komunikatem, a nie fałszywy plan na 23 h.
* Wartości nieliczbowe (`nan`/`inf`) $\to$ błąd walidacji CLI i API (rozwiązane Issue #13, test TC-11).

---

# Jakość, testy i przejście do Demo

### Zestaw testów automatycznych (`pytest`):
* **128 zaliczonych testów (100% PASS):**
  * **15 testów logiki (`tests/test_logic.py`, TC-01..TC-07):** poprawność DP i termostatu vs rachunek ręczny, granice pasma, puste i odwrócone wejścia.
  * **9 testów integracyjnych (`tests/test_integration.py`, TC-08..TC-11):** pełny przepływ CLI w osobnym procesie, format CSV, jednostki i komunikaty błędów.
  * **104 testy modułowe:** model budynku, API FastAPI, pobieranie PSE/Open-Meteo, analiza wrażliwości.

### Dowód jakości po integracji vs Lab 4 (`scripts/compare_lab7.py`):
* Obliczenia wykonane przez interfejs CLI, dopasowanie po kolumnie `hour` (nie po indeksie wiersza).
* **Wynik:** **40/40 miar zgodnych w ustalonej tolerancji**, błąd MAE temperatury wynosi **0,0000 °C**, zero rozbieżnych decyzji.

### Wydajność niefunkcjonalna (N1):
* Czas pełnej analizy doby (24 h): **0,0033 s** (Linux VM) / **0,0052 s** (PC). Kryterium $\le 1{,}0$ s spełnione z 200-krotnym zapasem.

<div class="box" style="text-align: center; font-weight: bold; font-size: 20px;">
🚀 Przejście do demonstracji na żywo w przeglądarce: http://localhost:8080
</div>

---

# Wnioski i ograniczenia projektu

### Co zostało udowodnione i działa w wersji v1.0.0:
* **Wysoka efektywność kosztowa:** Predykcyjne sterowanie DP oszczędza **36–52% kosztów ogrzewania** doby względem klasycznego termostatu na rzeczywistych cenach RCE PSE.
* **Bezkompromisowy komfort cieplny:** Wykorzystanie akumulacji ciepła eliminuje niedogrzania domu ($0\text{ h}$ poniżej $T_{min}$).
* **Stabilność i odporność:** Aplikacja odrzuca błędne dane, obsługuje wymuszenia użytkownika i posiada mechanizm offline.

### Granice wnioskowania (czego nie wolno uogólniać):
1. **Pojedyncza doba referencyjna:** Wynik dotyczy doby 2026-10-13 i modelu referencyjnego — nie dowodzi skali oszczędności w skali całego roku w dowolnym budynku.
2. **Idealna prognoza pogody i cen:** W eksperymencie użyto danych archiwalnych — w realnych warunkach błędy prognoz obniżą oszczędność.
3. **Złożoność obliczeniowa DP:** Czas rośnie nieliniowo z długością horyzontu (24 h: 0,005 s, 240 h: 1,65 s) — plany wielodniowe wymagałyby redukcji przestrzeni stanów.
4. **Brak wykonawczego sterownika PLC:** System wspiera decyzję użytkownika (DSS), nie steruje fizycznym przekaźnikiem pieca na żywo.

---

# Wkład w projekt i podsumowanie

### Wkład Sebastiana Rączki w projekt:
* **Lab 4 (Eksperyment):** Opracowanie analizy wrażliwości na zmianę pasma komfortu ($T_{min}$) oraz badanie stabilności numerycznej algorytmu DP.
* **Lab 5–6 (Architektura i MVP):** Opracowanie diagramu granic systemu, przepływu danych i diagramu sekwencji UML UC-01 (`granice.drawio`, §5 i §6 w `docs/architecture.md`); obsługa powiadomienia o braku wpływu wymuszeń na termostat (Z-05).
* **Lab 7 (Testy i Jakość):** Skrypt oceny jakości po integracji (`scripts/compare_lab7.py`), potwierdzenie zgodności 40/40 miar z Lab 4 (MAE = 0,0000 °C), statusy wymagań R1–R6/N1/U1 i rejestr błędów B1–B7 w `docs/tests.md`.
* **Lab 8 (Wydanie i Prezentacja):** Slajdy prezentacji (`presentation/slides.md`, `slides.pdf`, `slides.pptx`) oraz kompletny scenariusz demo wraz z pytaniami obronnymi (`docs/presentation.md`).

<div class="box">
<b>Status wydania v1.0.0:</b> Kompletny kod, dokumentacja (raport, testy, user-guide) oraz 128 testów automatycznych na gałęzi <code>main</code> z zielonym statusem GitHub Actions CI.
</div>

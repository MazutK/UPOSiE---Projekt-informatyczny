# Ściągawka na prezentację demo (1 strona)

Projekt: **Optymalizator ogrzewania elektrycznego przy zmiennych cenach energii**
Aplikacja: [http://localhost:8080](http://localhost:8080) (lub `http://localhost:5173`)

---

### 1. Pięć zdań na obronę projektu (do powiedzenia przy ekranie)

1. **Problem:** Klasyczny termostat z histerezą ignoruje dynamiczne ceny energii i włącza piec w najdroższych godzinach szczytu wieczornego.
2. **Rozwiązanie (metoda):** Zastosowaliśmy programowanie dynamiczne (DP) z horyzontem 24 godzin i leksykograficznym kosztem, które najpierw bezwzględnie pilnuje komfortu cieplnego domowników, a dopiero potem minimalizuje rachunek w złotówkach.
3. **Model budynku:** Uwzględniamy współczynnik stygnięcia ($\alpha$), nasłonecznienie ($\gamma$) oraz 2-godzinne opóźnienie bezwładności cieplnej ($d=2\text{ h}$), co pozwala „naładować” budynek ciepłem w taniej godzinie przed szczytem.
4. **Dane:** Aplikacja działa zarówno na scenariuszach wzorcowych, jak i na rzeczywistych cenach RCE z PSE oraz pogodzie z Open-Meteo pobieranych jednym kliknięciem (z pełnym fallbackiem offline).
5. **Wynik:** Plan DP oszczędza od 30% do ponad 50% kosztów ogrzewania doby (np. spadek z 11,15 zł do 5,35 zł na dobie rzeczywistej), nie dopuszczając do żadnych wychłodzeń poniżej pasma komfortu.

---

### 2. Scenariusz przejścia przez interfejs (krok po kroku na żywo)

1. **Scenariusz bazowy vs szczyt cenowy:**
   - W lewym panelu wybierz `doba_szczyt_wieczorny`.
   - Zwróć uwagę na wykres cen i grzania: termostat grzeje w godzinach 17:00–21:00 (najdroższy prąd), podczas gdy plan DP nagrzał dom wcześniej i w czasie szczytu piec jest całkowicie wyłączony.
2. **Dane publiczne live:**
   - W sekcji „Dane publiczne (PSE + Open-Meteo)” kliknij **„Pobierz dobę”**.
   - Aplikacja pobiera realną dobę z PSE i Open-Meteo (lub ładuje zapisany offline cache) i automatycznie przelicza plan dla `doba_live`.
3. **Wymuszenia godzin (Overrides):**
   - W sekcji „Wymuszenia godzin” kliknij np. godzinę **18:00**, ustawiając stan **ON** (wymuś grzanie w drogim szczycie).
   - Zobacz, jak wykres i karty kosztów natychmiast reagują (koszt rośnie, bo użytkownik narzucił swoje ograniczenie). Kliknij **„Wyczyść wymuszenia”**, by wrócić do pełnego optimum.
4. **Pobranie planu (Eksport CSV):**
   - Kliknij przycisk **„Pobierz plan godzinowy (CSV)”** — przeglądarka pobiera gotowy plik CSV ze szczegółowymi decyzjami godzina po godzinie.
5. **Tabela porównania metod (4 warianty):**
   - Przewiń pod tabelę godzinową: widać porównanie DP z klasycznym termostatem, prostą heurystyką zachłanną (dogrzewanie przy cenie poniżej mediany) oraz stałym progiem $T_{min}$.
   - DP deklasuje reguły proste zarówno pod względem kosztu, jak i stabilności temperatury.
6. **Analiza wrażliwości (Sensitivity Analysis):**
   - Wybierz badanie parametru `T_min` lub `max_overshoot`.
   - Tabela pokazuje, jak zmiana dolnej granicy komfortu wpływa na koszt i oszczędności oraz pozwala wyeksportować siatkę do pliku CSV przyciskiem **„Eksportuj tabelę do CSV”**.

---

### 3. Zespół projektowy

- **Kacper Mazur** — lewa kolumna GUI + klient HTTP
- **Sebastian Król** — prawa kolumna GUI + integracja
- **Sebastian Rączka** — analiza wrażliwości, symulacje numeryczne i testy
- **Karol Brzozowski** — porównanie metod (heurystyki, baselines)
- **Oskar Wysocki** — dane publiczne (PSE + Open-Meteo)
- **Patryk Uchman** — wymuszenia godzin, eksport CSV, dokumentacja i demo

# Analiza źródeł danych

## Źródła danych

| Źródło                    | Co można pobrać?                      | Czy odpowiada potrzebom? | Dowód sprawdzenia                 | Braki lub ryzyko                  |
| ------------------------- | ------------------------------------- | ------------------------ | --------------------------------- | --------------------------------- |
| PSE (Rynek Energii)       | godzinowe ceny energii                | tak                      | dokumentacja i przykładowe dane   | możliwość zmian formatu           |
| Open-Meteo                | temperatura, promieniowanie słoneczne | tak                      | dokumentacja API i odpowiedź JSON | zależność od dokładności prognozy |
| Dane syntetyczne projektu | komplet danych testowych              | częściowo                | pliki scenariuszy projektu        | nie są to dane rzeczywiste        |

---

## Ocena źródła 1 - Open-Meteo

### Dopasowanie do problemu

Źródło dostarcza:

- temperaturę zewnętrzną,
- promieniowanie słoneczne,
- dane godzinowe wymagane przez model.

Ocena: TAK

### Właściciel i znaczenie danych

Publikujący: Open-Meteo

Przykładowe pola:

- temperature_2m - temperatura powietrza na wysokości 2 m [°C]
- shortwave_radiation - promieniowanie słoneczne [W/m²]

### Jakość

- dane uporządkowane,
- standardowy format JSON,
- mogą występować błędy prognoz.

### Dostęp i koszt

- brak opłat,
- brak konieczności posiadania klucza API.

### Licencja i prywatność

- brak danych osobowych,
- dane publiczne.

### Powtarzalność

Możliwe ponowne pobranie danych przy użyciu tego samego zapytania.

---

## Ocena źródła 2 - PSE

### Dopasowanie do problemu

Źródło dostarcza godzinowe ceny energii potrzebne do obliczania kosztów.

Ocena: TAK

### Właściciel i znaczenie danych

Publikujący:
Polskie Sieci Elektroenergetyczne (PSE)

Dane:

- ceny energii dla poszczególnych godzin doby.

### Jakość

- oficjalne źródło krajowe,
- dane publikowane regularnie.

### Dostęp i koszt

- dane publiczne,
- konieczność sprawdzenia sposobu pobierania.

### Licencja i prywatność

- brak danych osobowych.

### Powtarzalność

Możliwe po zapisaniu dokładnego adresu źródła.

---

# Wybrane źródło

| Element                               | Wynik sprawdzenia                                                                                       |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Źródło i właściciel                   | Open-Meteo                                                                                              |
| Link lub sposób dostępu               | API Open-Meteo                                                                                          |
| Wymaganie, które źródło obsługuje     | R3, R5                                                                                                  |
| Data pobrania                         | wpisać datę testu                                                                                       |
| Format i kodowanie                    | JSON, UTF-8                                                                                             |
| Liczba rekordów w próbce              | 24 rekordy godzinowe                                                                                    |
| Nazwy pól i ich znaczenie             | temperature_2m, shortwave_radiation                                                                     |
| Format dat i jednostki                | ISO8601, °C, W/m²                                                                                       |
| Brakujące wartości lub rekordy        | nie stwierdzono w próbce                                                                                |
| Limit zapytań, klucz i koszt          | brak klucza, brak opłat                                                                                 |
| Licencja i ograniczenia wykorzystania | dane publiczne                                                                                          |
| Próba ponownego pobrania              | wykonano, struktura zgodna                                                                              |
| Brakujące dane                        | brak danych indywidualnych budynków                                                                     |
| Plan awaryjny                         | wykorzystanie zapisanych scenariuszy CSV                                                                |
| Wybrany pomysł realizacji             | pobieranie danych z API Open-Meteo i danych cenowych PSE, następnie generowanie harmonogramu ogrzewania |
| Odrzucony pomysł i powód              | sterowanie ogrzewaniem na żywo - zbyt duże ryzyko, brak dostępu do urządzeń użytkownika                 |

---

# Próbka danych

Plik:
data/raw/open-meteo-sample.json

Zawartość próbki:

- data i godzina,
- temperatura zewnętrzna,
- promieniowanie słoneczne.

Próbka pochodzi z rzeczywistego źródła Open-Meteo i nie zawiera danych osobowych.

---

# Plan pozyskania danych

| Element                               | Ustalenie zespołu                                                                               |
| ------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Źródło lub sposób pomiaru             | API Open-Meteo (archiwum) + API PSE Raporty OSP (RCE)                                           |
| Właściciel danych                     | Open-Meteo; Polskie Sieci Elektroenergetyczne S.A.                                              |
| Zakres danych                         | jedna doba: ceny RCE, temperatura 2 m, promieniowanie krótkofalowe                              |
| Okres i częstotliwość                 | doba 2026-10-13; Open-Meteo co 1 h; RCE co 15 min (agregowane do 1 h w skrypcie)                |
| Jednostka obserwacji                  | jedna godzina doby dla budynku referencyjnego (Warszawa)                                        |
| Sposób pobrania lub zebrania          | GET Open-Meteo Archive; GET `https://api.raporty.pse.pl/api/rce-pln`; surowe JSON w `data/raw/` |
| Limit, koszt lub wymagane uprawnienia | brak klucza, brak opłat; PSE bywa wrażliwe na brak nagłówka User-Agent                          |
| Licencja i zasady publikacji          | dane publiczne, brak danych osobowych; mała próbka może być w repo                              |
| Osoba odpowiedzialna za pozyskanie    | (wpisz swój login) — Open-Meteo; (login Osoby 2) — PSE                                          |
| Plan awaryjny                         | wbudowane CSV w `packages/core/src/heating_optimizer/data/`                                     |

Parametry zapytania Open-Meteo: `latitude=52.2297`, `longitude=21.0122`, `start_date=end_date=2026-10-13`, `hourly=temperature_2m,shortwave_radiation`, `timezone=Europe/Warsaw`.

# Problem projektu

## Użytkownik i decyzja

Głównym użytkownikiem systemu jest właściciel lub najemca domu/mieszkania
wykorzystującego ogrzewanie elektryczne oraz taryfę dynamiczną energii.

Decyzja wspierana przez system:

"Kiedy należy uruchomić ogrzewanie w ciągu najbliższej doby, aby utrzymać
komfort cieplny przy możliwie najniższym koszcie energii?"

## Obecna trudność

Typowe termostaty reagują wyłącznie na temperaturę pomieszczenia.
Nie uwzględniają zmian cen energii elektrycznej ani prognozy pogody.

W efekcie ogrzewanie może pracować w godzinach najwyższych cen energii,
powodując niepotrzebnie wysokie rachunki.

Użytkownik nie ma prostego narzędzia pozwalającego ocenić:
- kiedy ogrzewać pomieszczenia,
- jaki będzie koszt ogrzewania,
- ile można zaoszczędzić względem zwykłego termostatu.

## Zakres problemu

Projekt obejmuje:
- planowanie ogrzewania na 24 godziny,
- wykorzystanie godzinowych cen energii,
- wykorzystanie danych pogodowych,
- porównanie różnych metod sterowania,
- analizę kosztów oraz komfortu cieplnego.

Projekt nie obejmuje:
- sterowania urządzeniem na żywo,
- wielu budynków jednocześnie,
- automatyki domowej,
- prognozowania cen energii.

## Potrzebne dane

- godzinowe ceny energii elektrycznej,
- temperatura zewnętrzna,
- promieniowanie słoneczne,
- parametry modelu cieplnego budynku,
- temperatura początkowa,
- minimalna i maksymalna temperatura komfortu.

## Założenia i pytania otwarte

### Założenia

- użytkownik korzysta z taryfy dynamicznej,
- plan tworzony jest dla jednej doby,
- model opisuje budynek referencyjny,
- ceny energii są dostępne dla każdej godziny.

### Pytania otwarte

- Czy ceny RCE PSE będą stale publicznie dostępne?
- Jak duży wpływ na wynik mają błędy prognozy pogody?
- Czy model można łatwo dostosować do innych budynków?

## Wymagania

| ID | Wymaganie | Kryterium sprawdzenia | Źródło lub uzasadnienie | Status | Osoba |
|----|-----------|----------------------|-------------------------|--------|--------|
| R1 | Użytkownik powinien otrzymać plan ogrzewania dla kolejnych 24 godzin | System generuje harmonogram godzinowy | Karta projektu | potwierdzone | login |
| R2 | System powinien uwzględniać ceny energii elektrycznej | Zmiana cen powoduje zmianę harmonogramu | Projekt | potwierdzone | login |
| R3 | System powinien utrzymywać temperaturę w zadanym paśmie komfortu | Temperatura nie spada poniżej T_min poza dopuszczalnym marginesem | Projekt | potwierdzone | login |
| R4 | System powinien umożliwiać porównanie z klasycznym termostatem | Wyświetlane są wyniki obu metod | Projekt | potwierdzone | login |
| R5 | System powinien wykorzystywać publicznie dostępne dane pogodowe | Dane są pobierane z udokumentowanego źródła | Open-Meteo | założenie | login |
| R6 | Użytkownik powinien widzieć prognozowany koszt ogrzewania | Koszt wyświetlany jest w złotówkach | Potrzeba użytkownika | potwierdzone | login |

## Potrzeby informacyjne

| Informacja | Do czego jest potrzebna? | Minimalny zakres | Format lub częstotliwość | Czy jest dostępna? |
|------------|-------------------------|------------------|--------------------------|-------------------|
| Cena energii | Wyliczenie kosztu ogrzewania | 24 godziny | dane godzinowe | tak |
| Temperatura zewnętrzna | Model cieplny budynku | 24 godziny | dane godzinowe | tak |
| Nasłonecznienie | Uwzględnienie zysków cieplnych | 24 godziny | dane godzinowe | tak |
| Parametry budynku | Symulacja temperatury | zestaw parametrów modelu | plik JSON | tak |
| Dane dla innych budynków | Personalizacja modelu | wiele obiektów | brak określonego formatu | nie |
| Aktualne ceny na przyszłą dobę | Optymalizacja kosztowa | kolejna doba | dane godzinowe | częściowo |
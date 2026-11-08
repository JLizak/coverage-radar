# Notatka o danych

Źródło: SEC Form 13F Data Sets, raporty złożone od 3 I 2023 do 31 VIII 2026. Kolumny opisuje `docs/data_dictionary.md`, a decyzje `docs/decisions.md`.

## Pozycje

Kwartały od 2022-12-31 do 2026-06-30, jeden wiersz na filer + kwartał + papier.

| | Punkt w czasie | Końcowa |
|---|---|---|
| Wiersze po filtrach, przed korektą | 28 869 909 | 29 797 037 |
| Raporty usunięte jako `mixed` (filer × kwartał) | 134 | 121 |
| Wiersze usunięte z tego powodu | 45 233 | 44 249 |
| **Wiersze w pliku** | **28 824 676** | **29 752 788** |
| Filerzy | 10 464 | 10 500 |
| Suma wartości po korekcie | 794,6 bln USD | 815,4 bln USD |

## Korekta jednostek

| `unit_status` | Raporty (punkt w czasie) | Wiersze | Wartość po korekcie |
|---|---|---|---|
| `dollars` | 103 736 | 26 004 221 | 744,54 bln USD |
| `thousands` | 8 043 | 2 792 887 | 50,04 bln USD |
| `unchecked` | 276 | 26 506 | 0,03 bln USD |
| `too_few_rows` | 387 | 1 062 | poniżej 0,01 bln USD |

Po korekcie, dla papierów z co najmniej 20 posiadaczami, 2 148 z 27,95 mln wierszy pozostaje około 1000 razy za nisko. Około 5 300 jest około 1000 razy za wysoko. Tych drugich reguła nie obejmuje.

## Liczba filerów

Liczba filerów rośnie skokowo w Q4, a poza tym prawie płasko. Powtarza się to co roku, więc najpewniej wynika z reguł 13F, nie z błędu grupowania. Tej przyczyny nie potwierdziliśmy w źródłach.

## Panel

Jeden wiersz na filer + kwartał, bez 21 wykluczonych filerów. Plik: `data/processed/panel.parquet`, budowany przez `python -m radar.dataset`.

| | |
| --- | --- |
| Wiersze | 112 140 |
| Filerzy | 10 443 |
| Wiersze z etykietą | 101 252 (bez ostatniego kwartału i filerów bez raportu w t+1) |
| Wiersze bez przepływu w t (`new_money_t` puste) | 11 768 (pierwszy raport filera albo przerwa) |

| Kwartał t | Filerzy | Posiadacze JPM | Pozytywy | % wszystkich | % posiadaczy | % prospektów |
| --- | --- | --- | --- | --- | --- | --- |
| 2022-12-31 | 6 687 | 1 364 | 395 | 6,1 | 25,5 | 1,10 |
| 2023-06-30 | 6 708 | 1 541 | 393 | 5,9 | 23,4 | 0,74 |
| 2023-12-31 | 7 014 | 1 724 | 475 | 6,9 | 25,3 | 0,91 |
| 2024-06-30 | 7 126 | 1 893 | 511 | 7,3 | 25,1 | 0,85 |
| 2024-12-31 | 7 755 | 2 189 | 669 | 8,8 | 28,9 | 0,90 |
| 2025-06-30 | 7 878 | 2 347 | 642 | 8,3 | 26,0 | 0,81 |
| 2025-12-31 | 8 400 | 2 620 | 715 | 8,7 | 25,9 | 0,83 |
| 2026-03-31 | 8 579 | 2 733 | 682 | 8,1 | 24,1 | 0,68 |
| 2026-06-30 | 8 683 | 2 832 | brak etykiety | | | |

Co drugi kwartał dla czytelności. Odsetek pozytywów rośnie z około 6% do 8–9%, razem z liczbą posiadaczy ETF-ów JPMorgan.

Do sprawdzenia: Morgan Stanley ma największe przepływy w panelu (+5,9, +6,9 i −12,0 mld USD w kolejnych kwartałach od 2023-09-30). Takie wahania u jednego filera mogą wynikać ze zmiany sposobu raportowania, a nie z decyzji inwestycyjnych.

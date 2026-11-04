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

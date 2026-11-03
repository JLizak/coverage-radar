# Słownik danych: SEC Form 13F

Źródło: `FORM13F_readme.htm` i `FORM13F_metadata.json` z paczek SEC oraz kontrole na 15 ZIP-ach
w `data/raw/` (raporty złożone od 3 I 2023 do 31 VIII 2026).

## W skrócie

Form 13F to kwartalny raport, w którym duzi zarządzający aktywami ujawniają swoje pozycje.
Jeden raport to jeden `ACCESSION_NUMBER`, a jego treść jest rozbita na tabele:

| Tabela | Jak o niej myśleć | Jeden wiersz to | Wiersze | Parquet |
|---|---|---|---|---|
| `submission` | koperta: kto, kiedy, za jaki okres | raport | 153 519 | tak |
| `coverpage` | strona tytułowa: czy to poprawka, nazwa i adres | raport | 153 519 | tak |
| `summarypage` | podsumowanie: deklarowana liczba i suma pozycji | raport | 127 775 | tak |
| `infotable` | właściwa treść: pozycje w portfelu | pozycja | 47 980 718 | tak |
| `othermanager` | inni zarządzający zgłaszający za tego filera | zarządzający | nie liczono | nie |
| `othermanager2` | inni zarządzający objęci tym raportem | zarządzający | nie liczono | nie |
| `signature` | podpis: osoba, stanowisko, telefon | raport | nie liczono | nie |

```text
submission 1 ── 1 coverpage
submission 1 ── 0..1 summarypage
submission 1 ── 0..n infotable
```

Wszystko łączysz po `ACCESSION_NUMBER`. `CIK` i `PERIODOFREPORT` są tylko w `submission`,
więc `infotable` bez złączenia nie wie, czyja i z którego kwartału jest pozycja.

## Typy raportów

| `SUBMISSIONTYPE` | Znaczenie | Liczba | Ma pozycje? |
|---|---|---|---|
| `13F-HR` | raport o pozycjach, pierwotny | 120 698 | tak |
| `13F-HR/A` | poprawka raportu o pozycjach | 5 279 | tak |
| `13F-NT` | zawiadomienie: pozycje zgłasza ktoś inny | 27 301 | nie |
| `13F-NT/A` | poprawka zawiadomienia | 241 | nie |

## submission

| Kolumna | Typ | Znaczenie | Uwagi |
|---|---|---|---|
| `ACCESSION_NUMBER` | tekst | identyfikator raportu nadany przez SEC | klucz, zawsze 20 znaków |
| `FILING_DATE` | data | dzień złożenia raportu | podstawa punktu w czasie |
| `SUBMISSIONTYPE` | tekst | typ raportu, zob. wyżej | |
| `CIK` | tekst | identyfikator filera w SEC | **format niespójny**, zob. pułapki |
| `PERIODOFREPORT` | data | koniec kwartału, którego dotyczy raport | od 2001, ale kompletne dopiero od 2022-12-31 |
| `source_file` | tekst | ZIP, z którego pochodzi wiersz | dodane w `load.py`, nie grupuj po tym |

## coverpage

| Kolumna | Typ | Znaczenie | Braki | Uwagi |
|---|---|---|---|---|
| `ACCESSION_NUMBER` | tekst | identyfikator raportu | 0% | klucz |
| `REPORTCALENDARORQUARTER` | data | kwartał raportu | 0% | zawsze równe `PERIODOFREPORT` |
| `ISAMENDMENT` | tekst | czy poprawka: `Y`, `N` | 46,6% | nie polegaj na tym, użyj `SUBMISSIONTYPE` |
| `AMENDMENTNO` | tekst | numer poprawki | 96,4% | rzutuj na liczbę przed sortowaniem |
| `AMENDMENTTYPE` | tekst | `RESTATEMENT` lub `NEW HOLDINGS` | 96,4% | zob. poprawki |
| `REPORTTYPE` | tekst | `13F HOLDINGS REPORT`, `13F NOTICE`, `13F COMBINATION REPORT` | 0% | zob. pułapki |
| `FILINGMANAGER_NAME` | tekst | nazwa filera | 0% | ten sam CIK może mieć do 4 nazw |
| `FILINGMANAGER_STREET1`, `_STREET2` | tekst | adres | 0,03%, 44,5% | |
| `FILINGMANAGER_CITY` | tekst | miasto | 0,03% | |
| `FILINGMANAGER_STATEORCOUNTRY` | tekst | kod stanu lub kraju | 0,03% | |
| `FILINGMANAGER_ZIPCODE` | tekst | kod pocztowy | 0,03% | |
| `FORM13FFILENUMBER` | tekst | numer akt Form 13F | 0% | |
| `CRDNUMBER` | tekst | numer CRD | 56,0% | |
| `SECFILENUMBER` | tekst | numer akt SEC | 58,6% | |
| `CONFDENIEDEXPIRED` | tekst | czy poufność odrzucono lub wygasła | 98,7% | |
| `DATEDENIEDEXPIRED` | tekst | kiedy poufność odrzucono lub wygasła | 99,7% | data zapisana jako tekst |
| `DATEREPORTED` | tekst | kiedy pozycje zgłoszono z wnioskiem o poufność | 99,7% | data zapisana jako tekst |
| `REASONFORNONCONFIDENTIALITY` | tekst | powód braku poufności | 99,7% | |
| `PROVIDEINFOFORINSTRUCTION5` | tekst | czy filer dodaje informacje z instrukcji 5 | 0% | |
| `ADDITIONALINFORMATION` | tekst | wolny tekst filera | 96,0% | |
| `source_file` | tekst | ZIP źródłowy | 0% | dodane w `load.py` |

## summarypage

Deklaracja filera, a nie wynik liczony przez SEC, więc służy do kontroli `infotable`.

| Kolumna | Typ | Znaczenie | Uwagi |
|---|---|---|---|
| `ACCESSION_NUMBER` | tekst | identyfikator raportu | klucz |
| `OTHERINCLUDEDMANAGERSCOUNT` | tekst | liczba innych zarządzających objętych raportem | rzutuj na liczbę |
| `TABLEENTRYTOTAL` | liczba | deklarowana liczba pozycji | niezgodna z `infotable` w 2 658 ze 125 976 raportów |
| `TABLEVALUETOTAL` | liczba | deklarowana suma wartości | |
| `ISCONFIDENTIALOMITTED` | tekst | czy pominięto pozycje poufne | 32,2% braków |
| `source_file` | tekst | ZIP źródłowy | dodane w `load.py` |

## infotable

| Kolumna | Typ | Znaczenie | Braki | Uwagi |
|---|---|---|---|---|
| `ACCESSION_NUMBER` | tekst | raport, do którego należy wiersz | 0% | klucz razem z `INFOTABLE_SK` |
| `INFOTABLE_SK` | tekst | numer wiersza nadany przez SEC | 0% | bez znaczenia analitycznego |
| `NAMEOFISSUER` | tekst | nazwa emitenta | 0% | wolny tekst, nie używaj jako klucza |
| `TITLEOFCLASS` | tekst | klasa papieru | 0% | wolny tekst: `COM`, `Stock`, `Common Stock` |
| `CUSIP` | tekst | identyfikator papieru | 0% | **brudny**, zob. pułapki |
| `FIGI` | tekst | identyfikator FIGI | 90,4% | zawiera też śmieci, np. `XXXXXXXXXXXX` |
| `VALUE` | liczba | wartość rynkowa w dolarach | 0% | 450 563 wierszy ma 0 |
| `SSHPRNAMT` | liczba | liczba akcji lub kwota nominalna | 0% | znaczenie zależy od `SSHPRNAMTTYPE` |
| `SSHPRNAMTTYPE` | tekst | `SH` to akcje, `PRN` to kwota nominalna | 0% | `PRN`: 399 730 wierszy |
| `PUTCALL` | tekst | `Put`, `Call` lub puste | 96,0% | wypełnione oznacza opcję, nie akcje |
| `INVESTMENTDISCRETION` | tekst | kto decyduje: `SOLE`, `DFND`, `OTR` | 0% | |
| `OTHERMANAGER` | tekst | numery innych zarządzających dzielących decyzje | 53,6% | format niespójny |
| `VOTING_AUTH_SOLE` | tekst | akcje z wyłącznym prawem głosu | 0% | rzutuj na liczbę |
| `VOTING_AUTH_SHARED` | tekst | akcje ze wspólnym prawem głosu | 0% | rzutuj na liczbę |
| `VOTING_AUTH_NONE` | tekst | akcje bez prawa głosu | 0% | rzutuj na liczbę |
| `source_file` | tekst | ZIP źródłowy | 0% | dodane w `load.py` |

## Poprawki

| `AMENDMENTTYPE` | Co robi | Przykład |
|---|---|---|
| `RESTATEMENT` | zastępuje cały poprzedni raport | oryginał + restatement = tylko restatement |
| `NEW HOLDINGS` | dopisuje pozycje do poprzedniego raportu | oryginał + new holdings = oba |

## Pułapki

- **`CIK` ma różny format.** 238 wierszy nie ma 10 znaków (np. `872786`), a 11 filerów występuje
  w dwóch zapisach. Przed grupowaniem użyj `lpad(CIK, 10, '0')`.
- **Stare okresy są niepełne.** `PERIODOFREPORT` sięga 2001, ale raporty są złożone od 2023, więc
  dla starszych kwartałów są głównie same późne poprawki. Filtruj `PERIODOFREPORT >= '2022-12-31'`.
- **`CUSIP` jest brudny.** Zawsze ma 9 znaków, ale 130 639 wierszy ma małe litery, a 2 259 to
  `000000000`. Przed złączeniami użyj `upper(CUSIP)`.
- **Jedna spółka to kilka wierszy.** Filer może mieć kilka wierszy dla tego samego `CUSIP`, np. przy
  różnych `INVESTMENTDISCRETION` lub `OTHERMANAGER`. Agreguj przed liczeniem cech.
- **Opcje i obligacje są razem z akcjami.** Do analizy akcji filtruj `PUTCALL IS NULL` i
  `SSHPRNAMTTYPE = 'SH'`.
- **Raport może być częściowy.** `13F COMBINATION REPORT` (5 670 raportów) oznacza, że część pozycji
  zgłasza inny filer. Sam portfel takiego filera może więc być niepełny.
- **Puste `ISAMENDMENT`.** Dotyczy też wielu oryginałów, a pole bywa sprzeczne z `SUBMISSIONTYPE`.
- **`summarypage` nie jest dla wszystkich.** Większość `13F-NT` jej nie ma, a 1 `13F-HR` też nie.
- **Typy w Parquecie.** Daty i kwoty skonwertowano tylko dla kolumn z `CONVERSIONS` w
  `src/radar/load.py`. Reszta to tekst, żeby `CIK` i `CUSIP` nie straciły zer.

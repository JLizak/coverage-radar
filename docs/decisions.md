# Decyzje

## Korekta jednostek w `VALUE`

**Problem.** Od 3 I 2023 SEC wymaga `VALUE` w dolarach, ale część filerów nadal podaje tysiące. Około 9,6% wierszy ma cenę domniemaną około 1000 razy niższą od ceny rynkowej.

**Decyzja.** Oceniamy cały raport (filer × kwartał), bo tam leży błąd: około 99% zaniżonych wierszy jest w raportach zaniżonych niemal w całości.

| Stan raportu   | Warunek                                                          | Co robimy          |
| -------------- | ---------------------------------------------------------------- | ------------------ |
| `thousands`    | co najmniej 90% wierszy za nisko, co najmniej 5 wierszy do oceny | `VALUE` razy 1000  |
| `mixed`        | 10–90% wierszy za nisko, co najmniej 5 wierszy do oceny          | raport usunięty    |
| `too_few_rows` | co najmniej 10% wierszy za nisko, mniej niż 5 wierszy do oceny   | bez zmian, z flagą |
| `dollars`      | poniżej 10% wierszy za nisko                                     | bez zmian          |
| `unchecked`    | brak papierów z co najmniej 20 posiadaczami                      | bez zmian, z flagą |

„Za nisko” oznacza stosunek do mediany ceny papieru między 0,0005 a 0,002. Odniesieniem są tylko papiery z co najmniej 20 posiadaczami, bo mediana rzadkiego papieru sama bywa zaniżona.

**Dlaczego korekta, a nie usunięcie.** Dotyczy to około 2,8 mln wierszy i dużych filerów, a po korekcie 96,3% wierszy mieści się w ±10% od ceny rynkowej. Usunięcie zabrałoby około 50 bln USD portfeli.

**Dlaczego raporty mieszane odpadają.** Żaden jeden mnożnik ich nie naprawi, a to tylko 134 raporty w wersji punkt w czasie.

**Czego nie używamy.** `TABLEVALUETOTAL` nie wykrywa tego błędu: filerzy w tysiącach podają też sumę w tysiącach.

**Konsekwencja.** Etykieta liczy zmianę akcji, więc błąd jej nie dotyka. Cechy oparte na wartości używają `value_corrected`.

Dowody: `notebooks/01_unit_errors.ipynb`. Kod: `src/radar/sql/unit_corrections.sql`.

## Identyfikacja splitów

**Problem.** Niektóre papiery przechodzą z kwartału na kwartał przez splity, co znacząco zwiększa lub zmniejsza liczbę posiadanych papierów przez filera bez wpływu na ich wartość. W rezultacie wygląda to jak kupno lub sprzedaż, a etykieta liczy właśnie zmianę liczby akcji.

**Decyzja.** Splity są wyłapywane poprzez porównanie liczby akcji z poprzednim kwartałem (`shr_ratio`), porównanie wartości z poprzednim kwartałem (`val_ratio`) oraz porównanie tych stosunków ze sobą (`sv`). Każdy stosunek to mediana po wszystkich filerach, którzy mają papier w obu kwartałach.

| Warunek                                     | Próg                           | Dlaczego                                                                                                                                                             |
| ------------------------------------------- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Posiadacze z oboma kwartałami (`filers_ct`) | co najmniej 10                 | Mediana z kilku filerów to ich własny handel. Między 10–19 a 20–49 filerami odsetek okrągłych stosunków jest taki sam (12%), więc 20 niczego nie poprawia.           |
| Zmiana liczby akcji (`shr_ratio`)           | powyżej 1,4 albo poniżej 1/1,4 | Najmniejszy częsty split to 3:2 (1,5). Zwykły handel daje medianę przy 1: 93 448 z 95 721 par mieści się w 0,9–1,1.                                                  |
| Akcje względem wartości (`sv`)              | powyżej 1,3                    | Przy kupowaniu akcje i wartość rosną podobnie (`sv` 0,4–1,3). Przy splicie wartość zmienia się tylko o ruch kursu. Dla spadków liczone odwrotnie.                    |
| Okrągłość                                   | do 2% od wielokrotności 0,5    | Splity to proporcje małych liczb całkowitych (1,5, 2, 3, 10). Tolerancja jest względna, bo mediana odbiega od proporcji przez handel części filerów (NVIDIA 10,005). |

**Wynik.** Wykrytych zostało 214 splitów, w tym 8 odwrotnych. Faktor splitu to proporcja zaokrąglona do wielokrotności 0,5 (NVIDIA: 10, a nie mediana 10,005).

**Ograniczenia.**

- Split 3:2 przy wzroście kursu o ponad około 15% w kwartale ma `sv` poniżej 1,3 i zostaje potraktowany jak kupno. Z danych 13F nie da się tego odróżnić od dokupienia 50%.
- Splity papierów z mniej niż 10 posiadaczami nie są wykrywane.
- Przy dużych faktorach tolerancja 2% przepuszcza nietypowe proporcje (np. 16,5 i 21). To kilka przypadków do ręcznego sprawdzenia.

Dowody: `notebooks/02_splits.ipynb`. Kod: `src/radar/sql/splits.sql`.

## Rodzina domowa i próg pozytywu

**Problem.** Projekt symuluje zespół sprzedaży, który ma „swoje” fundusze. Trzeba wybrać markę ETF, dla której pytanie „kto dołoży pieniądze w następnym kwartale” jest dla modelu sensowne: nie może dokładać prawie każdy, ale pozytywów musi być dość, żeby było się czego uczyć.

**Decyzja.** Rodziną domową są ETF-y JPMorgan (prefiksy CUSIP `46641Q` i `46654Q`). Pozytyw to filer, który w kwartale t+1 dołożył do rodziny ponad **1 mln USD** nowych pieniędzy, liczonych jako zmiana liczby akcji po splitach razy cena z t+1. Sam wzrost kursu się nie liczy.

| Marka | Posiadacze | % wszystkich filerów z pozytywem | Ocena |
| --- | --- | --- | --- |
| iShares, Vanguard, SPDR | 4 900–5 500 | 18–27% | dokłada prawie każdy duży filer, model uczyłby się tylko wielkości |
| Invesco | 4 365 | 13,0% | na granicy |
| **JPMorgan** | 2 363 | **8,6%** | wybrana |
| Schwab, Dimensional | 1 900–3 200 | 8,1–8,2% | podobne liczby, ale słabiej pasują (niżej) |

Średnie z 6 przejść kwartalnych (2024-12-31 → 2026-03-31), na około 7 800 filerach obecnych w obu kwartałach.

**Dlaczego JPMorgan.** To tradycyjny, aktywny zarządzający z linią ETF (m.in. JEPI, JPST), czyli ten sam typ firmy co UBS Asset Management. Schwab jest powiązany z własną platformą brokerską, co miesza sygnał. Dimensional to firma czysto funduszowa.

**Dlaczego 1 mln USD.**

| Próg | % wszystkich | % posiadaczy | % prospektów |
| --- | --- | --- | --- |
| 100 tys. USD | 16,0 | 47,9 | 2,19 |
| 500 tys. USD | 11,2 | 34,3 | 1,17 |
| **1 mln USD** | **8,6** | **26,8** | **0,82** |
| 5 mln USD | 3,5 | 11,0 | 0,33 |

Przy 100 tys. USD pozytywem jest prawie połowa posiadaczy, co w dużej części jest zwykłym rebalansowaniem. Przy 5 mln USD zostaje około 18 pozytywów wśród prospektów na kwartał, za mało, żeby model nauczył się czegokolwiek o nowych klientach. 1 mln USD to kwota, przy której zespół sprzedaży faktycznie dzwoni.

**Jak znaleziono prefiksy.** Nazwa emitenta to wolny tekst, więc posłużyła tylko do znalezienia prefiksów (pierwsze 6 znaków CUSIP to trust). Prefiksy `46641Q` i `46654Q` zawierają wyłącznie „J P MORGAN EXCHANGE TRADED F”. Pozostałe papiery z „JPMorgan” w nazwie to akcje i obligacje banku, fundusze inwestycyjne (nie ETF-y) albo ETF-y innych marek na indeksach JPM.

**Ograniczenia.**

- Próg wybrano na wszystkich 6 przejściach, a nie tylko na treningowych. To decyzja z grubsza, z tabeli o kilku wartościach, a nie strojenie pod test.
- Rozkład jest nierówny: wśród posiadaczy pozytywem jest 26,8%, a wśród prospektów 0,82%. Wyniki modelu raportujemy osobno dla obu grup.

Dowody: `notebooks/03_house_family.ipynb`. Konfiguracja: `config/house.yaml`, `config/target.yaml`.

## Wykluczenia

**Problem.** Część filerów rusza ETF-ami JPMorgan z powodów innych niż decyzja klienta: zarządza nimi, obsługuje handel nimi albo ma błędy w raportach. Gdyby zostali w panelu, model uczyłby się przewidywać szum.

**Decyzja.** Wykluczamy 21 filerów w całości (nie trenujemy i nie oceniamy na nich). Lista z CIK i powodem jest w `config/exclusions.yaml`.

| Powód | Kto | Dlaczego |
| --- | --- | --- |
| `house` | JPMorgan Chase | trzyma własne ETF-y jako zarządzający (kapitał startowy, obsługa jednostek, private bank); zespół sprzedaży nie dzwoni do własnej firmy |
| `market_maker` | m.in. Jane Street, Susquehanna, Citadel, Flow Traders, Old Mission, IMC, Virtu, Optiver, dealerzy BNP, SG i CIBC (18 filerów) | trzymają ETF-y jako zapas do handlu; obrót 0,3–1,1 pozycji na kwartał przy medianie 0,13 |
| `data_error` | Legacy Financial Group, Quattro Financial Advisors | Legacy w dwóch kwartałach raportuje ponad 400 mld USD przy portfelu około 0,5 mld (w tym 56 mld w ETF-ach JPMorgan); Quattro ma błędną liczbę akcji (2 mln USD pozycji, 200 mln „obrotu” na kwartał) |

Obrót to średnio przehandlowane w kwartale podzielone przez średnio trzymane. Kandydatów szukano na dwa sposoby: najwięksi pod względem obrotu w USD oraz znane nazwy animatorów rynku i dealerów.

**Dlaczego duzi dystrybutorzy zostają.** Morgan Stanley, LPL, Bank of America, Raymond James czy UBS sumują w 13F pozycje tysięcy doradców i ich klientów. To najważniejsze cele prawdziwej sprzedaży ETF, a ich obrót (0,08–0,2) jest typowy dla inwestorów, nie dla pośredników.

**Skutek.** Wykluczenia zabierają 47 z 4 053 pozytywów (1,2%), ale 12,0 z 88,6 mld USD nowych pieniędzy (13,5%), głównie przez JPMorgan i Legacy. Pozostałe 4 006 pozytywów to 76,6 mld USD.

**Ograniczenia.**

- Lista animatorów rynku powstała z nazw i obrotu, więc mniejsi, nieznani pośrednicy mogą zostać w danych.
- Legacy to objaw szerszego problemu: raporty z wartościami zawyżonymi około 1000 razy (około 5 300 wierszy). Korekta jednostek łapie tylko zaniżone. Wykluczenie usuwa najgorszy przypadek, ale nie naprawia przyczyny.

Dowody: `notebooks/04_exclusions.ipynb`. Konfiguracja: `config/exclusions.yaml`.

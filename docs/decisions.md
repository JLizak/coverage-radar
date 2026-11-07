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

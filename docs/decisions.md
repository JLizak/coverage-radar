# Decyzje

## Korekta jednostek w `VALUE`

**Problem.** Od 3 I 2023 SEC wymaga `VALUE` w dolarach, ale część filerów nadal podaje tysiące. Około 9,6% wierszy ma cenę domniemaną około 1000 razy niższą od ceny rynkowej.

**Decyzja.** Oceniamy cały raport (filer × kwartał), bo tam leży błąd: około 99% zaniżonych wierszy jest w raportach zaniżonych niemal w całości.

| Stan raportu | Warunek | Co robimy |
|---|---|---|
| `thousands` | co najmniej 90% wierszy za nisko, co najmniej 5 wierszy do oceny | `VALUE` razy 1000 |
| `mixed` | 10–90% wierszy za nisko, co najmniej 5 wierszy do oceny | raport usunięty |
| `too_few_rows` | co najmniej 10% wierszy za nisko, mniej niż 5 wierszy do oceny | bez zmian, z flagą |
| `dollars` | poniżej 10% wierszy za nisko | bez zmian |
| `unchecked` | brak papierów z co najmniej 20 posiadaczami | bez zmian, z flagą |

„Za nisko” oznacza stosunek do mediany ceny papieru między 0,0005 a 0,002. Odniesieniem są tylko papiery z co najmniej 20 posiadaczami, bo mediana rzadkiego papieru sama bywa zaniżona.

**Dlaczego korekta, a nie usunięcie.** Dotyczy to około 2,8 mln wierszy i dużych filerów, a po korekcie 96,3% wierszy mieści się w ±10% od ceny rynkowej. Usunięcie zabrałoby około 50 bln USD portfeli.

**Dlaczego raporty mieszane odpadają.** Żaden jeden mnożnik ich nie naprawi, a to tylko 134 raporty w wersji punkt w czasie.

**Czego nie używamy.** `TABLEVALUETOTAL` nie wykrywa tego błędu: filerzy w tysiącach podają też sumę w tysiącach.

**Konsekwencja.** Etykieta liczy zmianę akcji, więc błąd jej nie dotyka. Cechy oparte na wartości używają `value_corrected`.

Dowody: `notebooks/01_unit_errors.ipynb`. Kod: `src/radar/sql/unit_corrections.sql`.

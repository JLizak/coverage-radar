-- Nowe pieniądze w rodzinie domowej w kwartale t, względem t-1, dla filerów z raportem w obu.
-- Zmiana liczby akcji po splitach razy mediana ceny z t, więc sam ruch kursu daje 0.
-- Papier tylko w jednym z kwartałów ma w drugim 0 akcji (pierwszy zakup, sprzedaż całości).

WITH reports AS (
    SELECT DISTINCT CIK, PERIODOFREPORT FROM read_parquet($path)
),
pairs AS (
    SELECT cur.CIK, prev.PERIODOFREPORT AS prev_period, cur.PERIODOFREPORT
    FROM reports cur
    JOIN reports prev
      ON prev.CIK = cur.CIK
     AND cur.PERIODOFREPORT = last_day(prev.PERIODOFREPORT + INTERVAL 3 MONTH)
),
family AS (
    SELECT CIK, PERIODOFREPORT, CUSIP, shares, value_corrected
    FROM read_parquet($path)
    WHERE list_contains($prefixes, left(CUSIP, 6))
),
prices AS (
    SELECT CUSIP, PERIODOFREPORT, median(value_corrected * 1.0 / shares) AS price
    FROM family
    WHERE shares > 0 AND value_corrected > 0
    GROUP BY CUSIP, PERIODOFREPORT
),
before AS (
    SELECT p.CIK, p.PERIODOFREPORT, f.CUSIP, f.shares
    FROM pairs p
    JOIN family f ON f.CIK = p.CIK AND f.PERIODOFREPORT = p.prev_period
),
after AS (
    SELECT p.CIK, p.PERIODOFREPORT, f.CUSIP, f.shares
    FROM pairs p
    JOIN family f ON f.CIK = p.CIK AND f.PERIODOFREPORT = p.PERIODOFREPORT
),
changes AS (
    SELECT
        coalesce(a.CIK, b.CIK) AS CIK,
        coalesce(a.PERIODOFREPORT, b.PERIODOFREPORT) AS PERIODOFREPORT,
        coalesce(a.CUSIP, b.CUSIP) AS CUSIP,
        coalesce(b.shares, 0) AS shares_before,
        coalesce(a.shares, 0) AS shares_after
    FROM after a
    FULL JOIN before b
      ON a.CIK = b.CIK AND a.PERIODOFREPORT = b.PERIODOFREPORT AND a.CUSIP = b.CUSIP
)
SELECT
    p.CIK,
    p.PERIODOFREPORT,
    coalesce(
        sum((c.shares_after - c.shares_before * coalesce(s.split_factor, 1)) * pr.price),
        0
    ) AS new_money
FROM pairs p
LEFT JOIN changes c
  ON c.CIK = p.CIK AND c.PERIODOFREPORT = p.PERIODOFREPORT
LEFT JOIN prices pr
  ON pr.CUSIP = c.CUSIP AND pr.PERIODOFREPORT = c.PERIODOFREPORT
LEFT JOIN read_parquet($splits_path) s
  ON s.CUSIP = c.CUSIP AND s.PERIODOFREPORT = c.PERIODOFREPORT
GROUP BY p.CIK, p.PERIODOFREPORT

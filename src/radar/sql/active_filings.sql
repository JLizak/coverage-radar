-- Raporty, które tworzą aktualny stan portfela dla każdej pary filer + kwartał.
-- $days: ile dni po końcu kwartału raport mógł zostać złożony; NULL oznacza wersję końcową.

WITH reports AS (
    SELECT
        s.ACCESSION_NUMBER,
        lpad(s.CIK, 10, '0') AS CIK,
        s.PERIODOFREPORT,
        s.FILING_DATE,
        c.AMENDMENTNO,
        c.AMENDMENTTYPE,
        c.REPORTTYPE
    FROM submission s
    JOIN coverpage c ON s.ACCESSION_NUMBER = c.ACCESSION_NUMBER
    WHERE s.SUBMISSIONTYPE IN ('13F-HR', '13F-HR/A')
      AND s.PERIODOFREPORT >= '2022-12-31'
      -- Poprawka bez typu: nie wiadomo, czy zastępuje, czy dopisuje.
      AND NOT (s.SUBMISSIONTYPE = '13F-HR/A' AND c.AMENDMENTTYPE IS NULL)
      AND ($days IS NULL OR s.FILING_DATE <= s.PERIODOFREPORT + $days * INTERVAL 1 DAY)
),

-- Numer raportu w parze, od najstarszego.
numbered AS (
    SELECT
        *,
        row_number() OVER (
            PARTITION BY CIK, PERIODOFREPORT
            ORDER BY FILING_DATE, coalesce(try_cast(AMENDMENTNO AS INT), 0), ACCESSION_NUMBER
        ) AS rn
    FROM reports
),

-- Baza to ostatni raport, który nie jest NEW HOLDINGS. Oryginały mają pusty typ, stąd coalesce.
with_base AS (
    SELECT
        *,
        max(rn) FILTER (WHERE coalesce(AMENDMENTTYPE, '') <> 'NEW HOLDINGS') OVER (
            PARTITION BY CIK, PERIODOFREPORT
        ) AS base_rn
    FROM numbered
)

-- Zostają baza i wszystko po niej. Para bez bazy ma base_rn = NULL i odpada.
SELECT ACCESSION_NUMBER, CIK, PERIODOFREPORT, FILING_DATE, AMENDMENTTYPE, REPORTTYPE
FROM with_base
WHERE rn >= base_rn
ORDER BY CIK, PERIODOFREPORT, rn

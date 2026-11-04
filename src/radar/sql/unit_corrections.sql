-- Część filerów nadal podaje VALUE w tysiącach, mimo zmiany SEC z 3 I 2023.
-- Błąd dotyczy prawie zawsze całego raportu, więc oceniamy raport, nie pojedynczy wiersz.
-- Uzasadnienie progów: docs/decisions.md. Dowody: notebooks/01_unit_errors.ipynb.
-- "raw" podstawia panel.py, patrz positions().

WITH reference AS (
    -- Tylko papiery z wieloma posiadaczami: mediana rzadkiego papieru sama bywa zaniżona.
    SELECT CUSIP, PERIODOFREPORT, median(value_usd * 1.0 / shares) AS price
    FROM raw
    WHERE shares > 0 AND value_usd > 0
    GROUP BY CUSIP, PERIODOFREPORT
    HAVING count(*) >= 20
),

reports AS (
    SELECT
        r.CIK,
        r.PERIODOFREPORT,
        count(*) AS checked_rows,
        avg((r.value_usd * 1.0 / r.shares / x.price BETWEEN 0.0005 AND 0.002)::INT) AS low_share
    FROM raw r
    JOIN reference x ON r.CUSIP = x.CUSIP AND r.PERIODOFREPORT = x.PERIODOFREPORT
    WHERE r.shares > 0 AND r.value_usd > 0
    GROUP BY r.CIK, r.PERIODOFREPORT
),

labelled AS (
    SELECT
        CIK,
        PERIODOFREPORT,
        CASE
            WHEN low_share < 0.1 THEN 'dollars'
            WHEN checked_rows < 5 THEN 'too_few_rows'
            WHEN low_share >= 0.9 THEN 'thousands'
            ELSE 'mixed'
        END AS status
    FROM reports
)

SELECT
    r.CIK,
    r.PERIODOFREPORT,
    r.CUSIP,
    r.value_usd,
    r.shares,
    r.is_combination,
    CASE WHEN l.status = 'thousands' THEN r.value_usd * 1000 ELSE r.value_usd END AS value_corrected,
    coalesce(l.status, 'unchecked') AS unit_status
FROM raw r
LEFT JOIN labelled l ON r.CIK = l.CIK AND r.PERIODOFREPORT = l.PERIODOFREPORT
-- Raporty mieszane są nie do naprawienia jednym mnożnikiem, więc odpadają.
WHERE coalesce(l.status, '') <> 'mixed'

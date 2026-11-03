-- Stan portfela: jeden wiersz na filer + kwartał + papier.
-- Tylko akcje: opcje (PUTCALL) i kwoty nominalne (PRN) nie mówią, ile akcji filer naprawdę ma.
-- Sumowanie łączy kilka wierszy tego samego papieru i dolicza NEW HOLDINGS do bazy.
-- "active" podstawia panel.py, patrz positions().

SELECT
    a.CIK,
    a.PERIODOFREPORT,
    upper(i.CUSIP) AS CUSIP,
    sum(i.VALUE)::BIGINT AS value_usd,
    sum(i.SSHPRNAMT)::BIGINT AS shares,
    -- Część pozycji takiego filera zgłasza ktoś inny, więc portfel może być niepełny.
    bool_or(a.REPORTTYPE = '13F COMBINATION REPORT') AS is_combination
FROM active a
JOIN infotable i ON a.ACCESSION_NUMBER = i.ACCESSION_NUMBER
WHERE i.PUTCALL IS NULL
  AND i.SSHPRNAMTTYPE = 'SH'
  AND i.CUSIP <> '000000000'
GROUP BY a.CIK, a.PERIODOFREPORT, upper(i.CUSIP)

-- Panel: filer × kwartał. Cechy z wersji punkt w czasie, etykieta z wersji końcowej.
-- label = NULL, gdy filer nie ma raportu w t+1 (albo t to ostatni kwartał): etykieta nieznana.

SELECT
    h.CIK,
    h.PERIODOFREPORT,
    h.n_positions,
    h.portfolio_value,
    h.house_value,
    h.has_house,
    fp.new_money AS new_money_t,
    ff.new_money AS new_money_next,
    CASE WHEN ff.new_money IS NULL THEN NULL ELSE ff.new_money > $min_new_money END AS label
FROM holdings h
LEFT JOIN flows_pit fp
  ON fp.CIK = h.CIK AND fp.PERIODOFREPORT = h.PERIODOFREPORT
LEFT JOIN flows_final ff
  ON ff.CIK = h.CIK AND ff.PERIODOFREPORT = last_day(h.PERIODOFREPORT + INTERVAL 3 MONTH)
WHERE NOT list_contains($excluded, h.CIK)

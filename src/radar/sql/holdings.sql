-- Stan filera na koniec kwartału: cały portfel i część w rodzinie domowej.
-- Każdy filer z raportem ma wiersz, także prospekt bez rodziny domowej (jpm_value = 0).

SELECT
    CIK,
    PERIODOFREPORT,
    count(*) AS n_positions,
    sum(value_corrected) AS portfolio_value,
    coalesce(sum(value_corrected) FILTER (WHERE list_contains($prefixes, left(CUSIP, 6))), 0) AS house_value,
    bool_or(list_contains($prefixes, left(CUSIP, 6))) AS has_house
FROM read_parquet($path)
GROUP BY CIK, PERIODOFREPORT

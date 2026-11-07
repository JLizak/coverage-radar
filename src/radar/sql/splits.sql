WITH changes AS (
    SELECT
        CIK, PERIODOFREPORT, CUSIP, shares, value_corrected,
        lag(shares) OVER (PARTITION BY CIK, CUSIP ORDER BY PERIODOFREPORT) AS prev_shares,
        lag(value_corrected) OVER (PARTITION BY CIK, CUSIP ORDER BY PERIODOFREPORT) AS prev_value,
        lag(PERIODOFREPORT) OVER (PARTITION BY CIK, CUSIP ORDER BY PERIODOFREPORT) AS prev_period
    FROM read_parquet($path)
),
ratios AS (
    SELECT
        PERIODOFREPORT,
        CUSIP,
        median(shares * 1.0 / prev_shares) AS shr_ratio,
        median(value_corrected * 1.0 / prev_value) AS val_ratio,
        count(*) AS filers_ct
    FROM changes
    WHERE prev_shares > 0
      AND prev_value > 0
      AND PERIODOFREPORT = last_day(prev_period + INTERVAL 3 MONTH)
    GROUP BY PERIODOFREPORT, CUSIP
),
candidates AS (
    SELECT
        *,
        greatest(shr_ratio, 1 / shr_ratio) AS unified_shr,
        CASE WHEN shr_ratio >= 1
            THEN shr_ratio / val_ratio
            ELSE val_ratio / shr_ratio
        END AS sv
    FROM ratios
    WHERE val_ratio > 0
)
SELECT
    CUSIP,
    PERIODOFREPORT,
    CASE WHEN shr_ratio >= 1
        THEN round(unified_shr * 2) / 2
        ELSE 2 / round(unified_shr * 2)
    END AS split_factor,
    shr_ratio,
    val_ratio,
    filers_ct
FROM candidates
WHERE filers_ct >= 10
  AND unified_shr > 1.4
  AND sv > 1.3
  AND abs(unified_shr * 2 - round(unified_shr * 2)) / unified_shr < 0.02

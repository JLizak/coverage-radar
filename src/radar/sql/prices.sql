
SELECT
    CUSIP,
    PERIODOFREPORT,
    median(value_corrected * 1.0 / shares) AS price,
    count(*) AS holders
FROM read_parquet($path)
WHERE shares > 0
  AND value_corrected > 0
GROUP BY CUSIP, PERIODOFREPORT

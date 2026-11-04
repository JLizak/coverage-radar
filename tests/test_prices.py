import duckdb as db

from radar.prices import implied_prices

CUSIP = "123456789"
PERIOD = "2024-03-31"


def prices_from(tmp_path, rows: list[tuple]) -> list[tuple]:
    """Wiersz: (CUSIP, okres, wartość, akcje)."""
    con = db.connect()
    con.execute("""
        CREATE TABLE p (CUSIP VARCHAR, PERIODOFREPORT DATE, value_corrected BIGINT, shares BIGINT)
    """)
    con.executemany("INSERT INTO p VALUES (?, ?, ?, ?)", rows)
    path = tmp_path / "positions.parquet"
    con.execute(f"COPY p TO '{path}' (FORMAT parquet)")
    return implied_prices(con, path).fetchall()


def test_price_is_value_over_shares(tmp_path):
    result = prices_from(tmp_path, [(CUSIP, PERIOD, 5000, 100)])
    assert [(row[2], row[3]) for row in result] == [(50.0, 1)]


def test_median_ignores_one_filer_reporting_in_thousands(tmp_path):
    rows = [
        (CUSIP, PERIOD, 5000, 100),
        (CUSIP, PERIOD, 5100, 100),
        (CUSIP, PERIOD, 5, 100),
    ]
    result = prices_from(tmp_path, rows)
    assert [(row[2], row[3]) for row in result] == [(50.0, 3)]


def test_rows_with_zero_do_not_count(tmp_path):
    rows = [
        (CUSIP, PERIOD, 5000, 100),
        (CUSIP, PERIOD, 0, 100),
        (CUSIP, PERIOD, 5000, 0),
    ]
    result = prices_from(tmp_path, rows)
    assert [(row[2], row[3]) for row in result] == [(50.0, 1)]


def test_quarters_are_separate(tmp_path):
    rows = [(CUSIP, PERIOD, 5000, 100), (CUSIP, "2024-06-30", 6000, 100)]
    result = sorted(row[2] for row in prices_from(tmp_path, rows))
    assert result == [50.0, 60.0]

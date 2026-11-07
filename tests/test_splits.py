import duckdb as db

from radar.splits import splits

CUSIP = "123456789"
Q1, Q2, Q3 = "2024-03-31", "2024-06-30", "2024-09-30"


def splits_from(tmp_path, rows: list[tuple]) -> list[tuple]:
    """Wiersz: (CIK, okres, CUSIP, akcje, wartość). Zwraca (CUSIP, okres, faktor)."""
    con = db.connect()
    con.execute("""
        CREATE TABLE p (
            CIK VARCHAR, PERIODOFREPORT DATE, CUSIP VARCHAR, shares BIGINT, value_corrected BIGINT
        )
    """)
    con.executemany("INSERT INTO p VALUES (?, ?, ?, ?, ?)", rows)
    path = tmp_path / "positions.parquet"
    con.execute(f"COPY p TO '{path}' (FORMAT parquet)")
    return [(row[0], str(row[1]), row[2]) for row in splits(con, path).fetchall()]


def holders(n: int, period: str, shares: int, value: int) -> list[tuple]:
    return [(f"CIK{i}", period, CUSIP, shares, value) for i in range(n)]


def test_two_for_one_split(tmp_path):
    rows = holders(10, Q1, 100, 5000) + holders(10, Q2, 200, 5100)
    assert splits_from(tmp_path, rows) == [(CUSIP, Q2, 2.0)]


def test_factor_is_rounded_when_some_holders_trade(tmp_path):
    rows = holders(10, Q1, 100, 5000) + holders(10, Q2, 1000, 5000)
    rows[-1] = ("CIK9", Q2, CUSIP, 1300, 6500)
    assert splits_from(tmp_path, rows) == [(CUSIP, Q2, 10.0)]


def test_reverse_split(tmp_path):
    rows = holders(10, Q1, 1000, 5000) + holders(10, Q2, 100, 4900)
    assert splits_from(tmp_path, rows) == [(CUSIP, Q2, 0.1)]


def test_three_for_two_split(tmp_path):
    rows = holders(10, Q1, 100, 5000) + holders(10, Q2, 150, 5000)
    assert splits_from(tmp_path, rows) == [(CUSIP, Q2, 1.5)]


def test_buying_is_not_a_split(tmp_path):
    rows = holders(10, Q1, 100, 5000) + holders(10, Q2, 200, 10000)
    assert splits_from(tmp_path, rows) == []


def test_too_few_holders(tmp_path):
    rows = holders(9, Q1, 100, 5000) + holders(9, Q2, 200, 5000)
    assert splits_from(tmp_path, rows) == []


def test_non_round_ratio_is_not_a_split(tmp_path):
    rows = holders(10, Q1, 100, 5000) + holders(10, Q2, 170, 5000)
    assert splits_from(tmp_path, rows) == []


def test_gap_between_quarters_is_ignored(tmp_path):
    rows = holders(10, Q1, 100, 5000) + holders(10, Q3, 200, 5000)
    assert splits_from(tmp_path, rows) == []


def test_split_is_found_per_security(tmp_path):
    other = "987654321"
    rows = holders(10, Q1, 100, 5000) + holders(10, Q2, 200, 5000)
    rows += [(f"CIK{i}", Q1, other, 100, 5000) for i in range(10)]
    rows += [(f"CIK{i}", Q2, other, 100, 5000) for i in range(10)]
    assert splits_from(tmp_path, rows) == [(CUSIP, Q2, 2.0)]

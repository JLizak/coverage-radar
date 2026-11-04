import duckdb as db
import pytest

from radar.panel import active_filings, build_positions, positions

PERIOD = "2024-03-31"


def make_con(rows: list[tuple]) -> db.DuckDBPyConnection:
    """Wiersz: (accession, data złożenia, typ raportu, CIK, okres, numer poprawki, typ poprawki)."""
    con = db.connect()
    con.execute("""
        CREATE TABLE submission (
            ACCESSION_NUMBER VARCHAR, FILING_DATE DATE, SUBMISSIONTYPE VARCHAR,
            CIK VARCHAR, PERIODOFREPORT DATE
        )
    """)
    con.execute("""
        CREATE TABLE coverpage (
            ACCESSION_NUMBER VARCHAR, AMENDMENTNO VARCHAR, AMENDMENTTYPE VARCHAR,
            REPORTTYPE VARCHAR DEFAULT '13F HOLDINGS REPORT'
        )
    """)
    con.execute("""
        CREATE TABLE infotable (
            ACCESSION_NUMBER VARCHAR, CUSIP VARCHAR, VALUE BIGINT, SSHPRNAMT BIGINT,
            SSHPRNAMTTYPE VARCHAR, PUTCALL VARCHAR
        )
    """)
    for accession, filed, kind, cik, period, number, amendment in rows:
        con.execute(
            "INSERT INTO submission VALUES (?, ?, ?, ?, ?)", [accession, filed, kind, cik, period]
        )
        con.execute(
            "INSERT INTO coverpage (ACCESSION_NUMBER, AMENDMENTNO, AMENDMENTTYPE) VALUES (?, ?, ?)",
            [accession, number, amendment],
        )
    return con


def accessions(rows: list[tuple], days: int | None = None) -> list[str]:
    return [row[0] for row in active_filings(make_con(rows), days).fetchall()]


ORIGINAL = ("orig", "2024-05-10", "13F-HR", "0000000001", PERIOD, None, None)
ADDED_BEFORE = ("add1", "2024-05-12", "13F-HR/A", "0000000001", PERIOD, "1", "NEW HOLDINGS")
RESTATED = ("rest", "2024-08-01", "13F-HR/A", "0000000001", PERIOD, "2", "RESTATEMENT")
ADDED_AFTER = ("add2", "2024-09-01", "13F-HR/A", "0000000001", PERIOD, "3", "NEW HOLDINGS")


def test_original_alone_stays():
    assert accessions([ORIGINAL]) == ["orig"]


def test_new_holdings_adds_to_original():
    assert accessions([ORIGINAL, ADDED_BEFORE]) == ["orig", "add1"]


def test_restatement_replaces_everything_before_it():
    assert accessions([ORIGINAL, ADDED_BEFORE, RESTATED, ADDED_AFTER]) == ["rest", "add2"]


def test_point_in_time_ignores_later_amendments():
    rows = [ORIGINAL, ADDED_BEFORE, RESTATED, ADDED_AFTER]
    assert accessions(rows, days=50) == ["orig", "add1"]


def test_amendment_number_sorts_as_number_on_the_same_day():
    day = "2024-08-01"
    rows = [
        ORIGINAL,
        ("r10", day, "13F-HR/A", "0000000001", PERIOD, "10", "RESTATEMENT"),
        ("r2", day, "13F-HR/A", "0000000001", PERIOD, "2", "RESTATEMENT"),
    ]
    assert accessions(rows) == ["r10"]


def test_cik_written_differently_is_one_filer():
    rows = [
        ("short", "2024-05-10", "13F-HR", "1", PERIOD, None, None),
        ("rest", "2024-08-01", "13F-HR/A", "0000000001", PERIOD, "1", "RESTATEMENT"),
    ]
    assert accessions(rows) == ["rest"]


@pytest.mark.parametrize(
    "row",
    [
        ("notice", "2024-05-10", "13F-NT", "0000000001", PERIOD, None, None),
        ("no_type", "2024-05-10", "13F-HR/A", "0000000001", PERIOD, "1", None),
        ("old", "2023-05-10", "13F-HR", "0000000001", "2022-09-30", None, None),
        ("no_base", "2024-05-10", "13F-HR/A", "0000000001", PERIOD, "1", "NEW HOLDINGS"),
    ],
)
def test_reports_that_drop_out(row):
    assert accessions([row]) == []


def test_filers_and_quarters_are_separate():
    other_filer = ("other", "2024-05-10", "13F-HR", "0000000002", PERIOD, None, None)
    other_quarter = ("next", "2024-08-10", "13F-HR", "0000000001", "2024-06-30", None, None)
    result = accessions([ORIGINAL, RESTATED, other_filer, other_quarter])
    assert sorted(result) == ["next", "other", "rest"]


CUSIP = "123456789"


def add_lines(con: db.DuckDBPyConnection, lines: list[tuple]) -> None:
    """Wiersz: (accession, CUSIP, wartość, akcje, typ, put/call)."""
    con.executemany("INSERT INTO infotable VALUES (?, ?, ?, ?, ?, ?)", lines)


def holdings(con: db.DuckDBPyConnection, days: int | None = None) -> dict:
    return {(row[0], row[2]): (row[3], row[4]) for row in positions(con, days).fetchall()}


def test_lines_of_one_security_are_summed():
    con = make_con([ORIGINAL])
    add_lines(
        con,
        [
            ("orig", CUSIP, 3000, 60, "SH", None),
            ("orig", CUSIP, 2000, 40, "SH", None),
        ],
    )
    assert holdings(con) == {("0000000001", CUSIP): (5000, 100)}


def test_lowercase_cusip_is_the_same_security():
    con = make_con([ORIGINAL])
    add_lines(
        con,
        [
            ("orig", "abc123456", 1000, 10, "SH", None),
            ("orig", "ABC123456", 2000, 20, "SH", None),
        ],
    )
    assert holdings(con) == {("0000000001", "ABC123456"): (3000, 30)}


@pytest.mark.parametrize(
    "line",
    [
        ("orig", CUSIP, 9000, 90, "SH", "Put"),
        ("orig", CUSIP, 9000, 90, "SH", "Call"),
        ("orig", CUSIP, 9000, 90, "PRN", None),
        ("orig", "000000000", 9000, 90, "SH", None),
    ],
)
def test_lines_that_are_not_counted(line):
    con = make_con([ORIGINAL])
    add_lines(con, [("orig", CUSIP, 1000, 10, "SH", None), line])
    assert holdings(con) == {("0000000001", CUSIP): (1000, 10)}


def test_new_holdings_add_to_the_base():
    con = make_con([ORIGINAL, ADDED_BEFORE])
    add_lines(
        con,
        [
            ("orig", CUSIP, 1000, 10, "SH", None),
            ("add1", CUSIP, 500, 5, "SH", None),
        ],
    )
    assert holdings(con) == {("0000000001", CUSIP): (1500, 15)}


def test_restatement_replaces_positions():
    con = make_con([ORIGINAL, RESTATED])
    add_lines(
        con,
        [
            ("orig", CUSIP, 1000, 10, "SH", None),
            ("orig", "AAA111111", 7000, 70, "SH", None),
            ("rest", CUSIP, 2000, 20, "SH", None),
        ],
    )
    assert holdings(con) == {("0000000001", CUSIP): (2000, 20)}


def test_each_call_uses_its_own_version():
    con = make_con([ORIGINAL, RESTATED])
    add_lines(
        con,
        [
            ("orig", CUSIP, 1000, 10, "SH", None),
            ("rest", CUSIP, 2000, 20, "SH", None),
        ],
    )
    point_in_time = positions(con, 50)
    final = positions(con, None)
    assert point_in_time.fetchall()[0][4] == 10
    assert final.fetchall()[0][4] == 20


def test_combination_report_is_flagged():
    con = make_con([ORIGINAL])
    add_lines(con, [("orig", CUSIP, 1000, 10, "SH", None)])
    assert positions(con, None).fetchall()[0][5] is False
    con.execute("UPDATE coverpage SET REPORTTYPE = '13F COMBINATION REPORT'")
    assert positions(con, None).fetchall()[0][5] is True


def test_build_writes_both_versions(tmp_path):
    con = make_con([ORIGINAL, RESTATED])
    add_lines(
        con,
        [
            ("orig", CUSIP, 1000, 10, "SH", None),
            ("rest", CUSIP, 2000, 20, "SH", None),
        ],
    )
    build_positions(con, tmp_path)
    read = "SELECT shares FROM '{}'"
    assert con.sql(read.format(tmp_path / "positions_pit.parquet")).fetchall() == [(10,)]
    assert con.sql(read.format(tmp_path / "positions_final.parquet")).fetchall() == [(20,)]
    assert list(tmp_path.glob("*.tmp")) == []


UNIT_CUSIPS = [f"CUSIP{number:04d}" for number in range(6)]


def con_with_market(target_lines: list[tuple]) -> db.DuckDBPyConnection:
    """20 filerów w dolarach ustala cenę 50 USD, a badany filer ma raport "orig"."""
    others = [
        (f"f{number}", "2024-05-10", "13F-HR", f"{number + 100:010d}", PERIOD, None, None)
        for number in range(20)
    ]
    con = make_con([ORIGINAL, *others])
    lines = [(row[0], cusip, 5000, 100, "SH", None) for row in others for cusip in UNIT_CUSIPS]
    add_lines(con, lines + target_lines)
    return con


def target_rows(con: db.DuckDBPyConnection) -> list[tuple]:
    query = """
        SELECT value_usd, value_corrected, unit_status FROM result
        WHERE CIK = '0000000001' ORDER BY CUSIP
    """
    result = positions(con, None)
    return result.query("result", query).fetchall()


def lines_in_thousands(count: int) -> list[tuple]:
    return [("orig", cusip, 5, 100, "SH", None) for cusip in UNIT_CUSIPS[:count]]


def lines_in_dollars(count: int, start: int = 0) -> list[tuple]:
    cusips = UNIT_CUSIPS[start : start + count]
    return [("orig", cusip, 5000, 100, "SH", None) for cusip in cusips]


def test_report_in_thousands_is_multiplied():
    con = con_with_market(lines_in_thousands(5))
    assert target_rows(con) == [(5, 5000, "thousands")] * 5


def test_report_in_dollars_is_left_alone():
    con = con_with_market(lines_in_dollars(5))
    assert target_rows(con) == [(5000, 5000, "dollars")] * 5


def test_mixed_report_is_dropped():
    con = con_with_market(lines_in_thousands(3) + lines_in_dollars(3, start=3))
    assert target_rows(con) == []


def test_small_report_is_flagged_but_not_corrected():
    con = con_with_market(lines_in_thousands(2))
    assert target_rows(con) == [(5, 5, "too_few_rows")] * 2


def test_report_without_widely_held_securities_stays_unchecked():
    con = con_with_market([("orig", "RARE00000", 5, 100, "SH", None)])
    assert target_rows(con) == [(5, 5, "unchecked")]

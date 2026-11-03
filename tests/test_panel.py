import duckdb as db
import pytest

from radar.panel import active_filings

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
            ACCESSION_NUMBER VARCHAR, AMENDMENTNO VARCHAR, AMENDMENTTYPE VARCHAR
        )
    """)
    for accession, filed, kind, cik, period, number, amendment in rows:
        con.execute(
            "INSERT INTO submission VALUES (?, ?, ?, ?, ?)", [accession, filed, kind, cik, period]
        )
        con.execute("INSERT INTO coverpage VALUES (?, ?, ?)", [accession, number, amendment])
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

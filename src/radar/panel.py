from pathlib import Path

import duckdb as db

DATA_DIR = "data/processed"
SQL_DIR = Path(__file__).parent / "sql"
TABLES = ["submission", "coverpage", "infotable", "summarypage"]


def connect(data_dir: str = DATA_DIR) -> db.DuckDBPyConnection:
    """Baza w pamięci z widokami na Parquety. Ścieżka do danych jest tylko tutaj."""
    con = db.connect()
    for table in TABLES:
        con.execute(f"CREATE VIEW {table} AS SELECT * FROM '{data_dir}/{table}/*.parquet'")
    return con


def active_filings(
    con: db.DuckDBPyConnection, days_after_period: int | None = 50
) -> db.DuckDBPyRelation:
    """Raporty tworzące stan portfela.

    days_after_period=50 daje wersję punkt w czasie (cechy i trening),
    a None wersję końcową (tylko etykiety testowe).
    """
    query = (SQL_DIR / "active_filings.sql").read_text()
    return con.sql(query, params={"days": days_after_period})

from pathlib import Path

import duckdb as db

DATA_DIR = "data/processed"
SQL_DIR = Path(__file__).parent / "sql"
TABLES = ["submission", "coverpage", "infotable", "summarypage"]

# Koniec kwartału + 45 dni na złożenie raportu + mały margines.
POINT_IN_TIME_DAYS = 50

# Nazwa pliku wynikowego -> days_after_period. None to wersja końcowa, tylko na etykiety testowe.
POSITION_VERSIONS = {"positions_pit": POINT_IN_TIME_DAYS, "positions_final": None}


def connect(data_dir: str = DATA_DIR) -> db.DuckDBPyConnection:
    """Baza w pamięci z widokami na Parquety. Ścieżka do danych jest tylko tutaj."""
    con = db.connect()
    for table in TABLES:
        con.execute(f"CREATE VIEW {table} AS SELECT * FROM '{data_dir}/{table}/*.parquet'")
    return con


def read_sql(name: str) -> str:
    return (SQL_DIR / f"{name}.sql").read_text()


def active_filings(
    con: db.DuckDBPyConnection, days_after_period: int | None = POINT_IN_TIME_DAYS
) -> db.DuckDBPyRelation:
    """Raporty tworzące stan portfela.

    days_after_period=50 daje wersję punkt w czasie (cechy i trening),
    a None wersję końcową (tylko etykiety testowe).
    """
    return con.sql(read_sql("active_filings"), params={"days": days_after_period})


def positions(
    con: db.DuckDBPyConnection, days_after_period: int | None = POINT_IN_TIME_DAYS
) -> db.DuckDBPyRelation:
    """Stan portfela: filer + kwartał + papier, z korektą jednostek.

    Parametr działa jak w active_filings.
    """
    # Składamy zapytania jako CTE, żeby jedno wywołanie nie zależało od stanu po drugim.
    query = f"""
        WITH active AS (
        {read_sql("active_filings")}
        ),
        raw AS (
        {read_sql("positions")}
        )
        SELECT * FROM (
        {read_sql("unit_corrections")}
        )
    """
    return con.sql(query, params={"days": days_after_period})


def build_positions(con: db.DuckDBPyConnection, output_dir: Path = Path(DATA_DIR)) -> None:
    """Zapisuje obie wersje pozycji do Parqueta. Plik pojawia się dopiero po pełnym zapisie."""
    for name, days in POSITION_VERSIONS.items():
        parquet_path = output_dir / f"{name}.parquet"
        tmp_path = parquet_path.with_suffix(".tmp")
        positions(con, days).write_parquet(str(tmp_path))
        tmp_path.replace(parquet_path)
        rows = con.sql(f"SELECT count(*) FROM '{parquet_path}'").fetchall()[0][0]
        print(f"{parquet_path}: {rows} wierszy")


if __name__ == "__main__":
    build_positions(connect())

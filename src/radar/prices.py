from pathlib import Path

import duckdb as db

SQL_DIR = Path(__file__).parent / "sql"


def implied_prices(con: db.DuckDBPyConnection, positions_path: Path) -> db.DuckDBPyRelation:
    """Cena każdego papieru w każdym kwartale, policzona z pliku pozycji."""
    query = (SQL_DIR / "prices.sql").read_text()
    return con.sql(query, params={"path": str(positions_path)})

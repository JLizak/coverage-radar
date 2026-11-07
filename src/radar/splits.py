from pathlib import Path

import duckdb as db

SQL_DIR = Path(__file__).parent / "sql"


def splits(con: db.DuckDBPyConnection, positions_path: Path) -> db.DuckDBPyRelation:
    """Splits for every quarter"""
    query = (SQL_DIR / "splits.sql").read_text()
    return con.sql(query, params={"path": str(positions_path)})


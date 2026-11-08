import tempfile
from pathlib import Path

import duckdb as db
import yaml

from radar.splits import splits

DATA_DIR = Path("data/processed")
CONFIG_DIR = Path("config")
SQL_DIR = Path(__file__).parent / "sql"


def read_sql(name: str) -> str:
    return (SQL_DIR / f"{name}.sql").read_text()


def read_config(config_dir: Path = CONFIG_DIR) -> dict:
    """Prefiksy rodziny domowej, wykluczeni filerzy i próg etykiety."""
    house = yaml.safe_load((config_dir / "house.yaml").read_text())
    exclusions = yaml.safe_load((config_dir / "exclusions.yaml").read_text())
    target = yaml.safe_load((config_dir / "target.yaml").read_text())
    return {
        "prefixes": house["cusip_prefixes"],
        "excluded": [e["cik"] for e in exclusions["exclusions"]],
        "min_new_money": target["min_new_money_usd"],
    }


def holdings(
    con: db.DuckDBPyConnection, positions_path: Path, prefixes: list[str]
) -> db.DuckDBPyRelation:
    """Stan każdego filera w każdym kwartale: portfel i rodzina domowa."""
    return con.sql(read_sql("holdings"), params={"path": str(positions_path), "prefixes": prefixes})


def house_splits(
    con: db.DuckDBPyConnection, positions_path: Path, prefixes: list[str], output_path: Path
) -> None:
    """Splity papierów rodziny domowej.

    Liczone na pozycjach samej rodziny, bo split zależy tylko od posiadaczy danego papieru,
    a cały plik nie mieści się w pamięci.
    """
    with tempfile.TemporaryDirectory() as tmp:
        family_path = Path(tmp) / "family.parquet"
        con.sql(
            "SELECT * FROM read_parquet($path) WHERE list_contains($prefixes, left(CUSIP, 6))",
            params={"path": str(positions_path), "prefixes": prefixes},
        ).write_parquet(str(family_path))
        splits(con, family_path).write_parquet(str(output_path))


def flows(
    con: db.DuckDBPyConnection, positions_path: Path, prefixes: list[str], splits_path: Path
) -> db.DuckDBPyRelation:
    """Nowe pieniądze w rodzinie domowej w kwartale t względem t-1."""
    params = {"path": str(positions_path), "prefixes": prefixes, "splits_path": str(splits_path)}
    return con.sql(read_sql("flows"), params=params)


def panel(
    con: db.DuckDBPyConnection, pit_path: Path, final_path: Path, config: dict, work_dir: Path
) -> db.DuckDBPyRelation:
    """Filer × kwartał: cechy z wersji punkt w czasie, etykieta z wersji końcowej."""
    prefixes = config["prefixes"]
    for name, path in {"pit": pit_path, "final": final_path}.items():
        splits_path = work_dir / f"house_splits_{name}.parquet"
        house_splits(con, path, prefixes, splits_path)
        flows(con, path, prefixes, splits_path).to_view(f"flows_{name}_rel")
        con.execute(f"CREATE OR REPLACE TABLE flows_{name} AS SELECT * FROM flows_{name}_rel")
    holdings(con, pit_path, prefixes).to_view("holdings_rel")
    con.execute("CREATE OR REPLACE TABLE holdings AS SELECT * FROM holdings_rel")
    params = {"min_new_money": config["min_new_money"], "excluded": config["excluded"]}
    return con.sql(read_sql("panel"), params=params)


def build_panel(data_dir: Path = DATA_DIR, config_dir: Path = CONFIG_DIR) -> None:
    """Zapisuje panel do Parqueta. Plik pojawia się dopiero po pełnym zapisie."""
    con = db.connect()
    con.execute("SET preserve_insertion_order = false")
    output_path = data_dir / "panel.parquet"
    tmp_path = output_path.with_suffix(".tmp")
    with tempfile.TemporaryDirectory() as work_dir:
        panel(
            con,
            data_dir / "positions_pit.parquet",
            data_dir / "positions_final.parquet",
            read_config(config_dir),
            Path(work_dir),
        ).write_parquet(str(tmp_path))
    tmp_path.replace(output_path)
    rows = con.sql(f"SELECT count(*) FROM '{output_path}'").fetchall()[0][0]
    print(f"{output_path}: {rows} wierszy")


if __name__ == "__main__":
    build_panel()

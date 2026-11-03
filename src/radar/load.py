import shutil
import tempfile
from pathlib import Path
from zipfile import ZipFile

import duckdb as db

TABLES = ["SUBMISSION.tsv", "COVERPAGE.tsv", "INFOTABLE.tsv", "SUMMARYPAGE.tsv"]

RAW_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/processed")

DATE_FORMAT = "%d-%b-%Y"  # np. 31-MAR-2026
CONVERSIONS = {
    "SUBMISSION": {
        "FILING_DATE": f"strptime(FILING_DATE, '{DATE_FORMAT}')::DATE",
        "PERIODOFREPORT": f"strptime(PERIODOFREPORT, '{DATE_FORMAT}')::DATE",
    },
    "COVERPAGE": {
        "REPORTCALENDARORQUARTER": f"strptime(REPORTCALENDARORQUARTER, '{DATE_FORMAT}')::DATE",
    },
    "INFOTABLE": {
        "VALUE": "VALUE::BIGINT",
        "SSHPRNAMT": "SSHPRNAMT::BIGINT",
    },
    "SUMMARYPAGE": {
        "TABLEENTRYTOTAL": "TABLEENTRYTOTAL::BIGINT",
        "TABLEVALUETOTAL": "TABLEVALUETOTAL::BIGINT",
    },
}


def find_tables(archive: ZipFile) -> dict[str, str]:
    found = {}
    for path_in_zip in archive.namelist():
        file_name = Path(path_in_zip).name
        if file_name in TABLES:
            found[file_name] = path_in_zip

    missing = set(TABLES) - set(found)
    if missing:
        raise ValueError(f"{archive.filename}: brak tabel {sorted(missing)}")

    return found


def extract_one_zip(zip_path: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)

    with ZipFile(zip_path) as archive:
        for file_name, path_in_zip in find_tables(archive).items():
            with archive.open(path_in_zip) as source, open(target_dir / file_name, "wb") as target:
                shutil.copyfileobj(source, target)


def extract_zips(source: Path, target_root: Path) -> None:
    for zip_path in sorted(source.glob("*.zip")):
        extract_one_zip(zip_path, target_root / zip_path.stem)


def parquet_path_for(zip_path: Path, table: str, output_dir: Path) -> Path:
    """Np. data/processed/infotable/2023q2_form13f.parquet"""
    return output_dir / table.lower() / f"{zip_path.stem}.parquet"


def tsv_to_parquet(tsv_path: Path, parquet_path: Path, source_file: str) -> None:
    table = tsv_path.stem
    replaced = ", ".join(f"{expr} AS {col}" for col, expr in CONVERSIONS[table].items())

    parquet_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = parquet_path.with_suffix(".tmp")
    db.sql(f"""
        COPY (
            SELECT * REPLACE ({replaced}), '{source_file}' AS source_file
            FROM read_csv('{tsv_path}', delim='\t', header=true, all_varchar=true)
        ) TO '{tmp_path}' (FORMAT parquet)
    """)
    tmp_path.replace(parquet_path)


def create_parquet(zip_path: Path, output_dir: Path) -> None:
    """Zamienia 4 tabele z jednego ZIP-a na Parquet. Gotowe pliki pomija."""
    tables = [Path(table).stem for table in TABLES]
    if all(parquet_path_for(zip_path, table, output_dir).exists() for table in tables):
        return

    # Katalog tymczasowy kasuje się sam, więc na dysku są naraz TSV-y tylko z jednego ZIP-a.
    with tempfile.TemporaryDirectory() as tmp_dir:
        extract_one_zip(zip_path, Path(tmp_dir))
        for table in tables:
            tsv_to_parquet(
                Path(tmp_dir) / f"{table}.tsv",
                parquet_path_for(zip_path, table, output_dir),
                zip_path.stem,
            )


def create_all_parquet(source: Path = RAW_DIR, output_dir: Path = OUTPUT_DIR) -> None:
    for zip_path in sorted(source.glob("*.zip")):
        print(zip_path.name)
        create_parquet(zip_path, output_dir)


if __name__ == "__main__":
    create_all_parquet()

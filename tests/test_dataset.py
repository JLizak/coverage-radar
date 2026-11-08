import duckdb as db
import pytest

from radar.dataset import panel

HOUSE = "46641Q332"
OTHER = "037833100"
Q1, Q2, Q3 = "2024-03-31", "2024-06-30", "2024-09-30"
CONFIG = {"prefixes": ["46641Q"], "excluded": ["EXCLUDED"], "min_new_money": 1_000_000}


def write_positions(con, path, rows: list[tuple]) -> None:
    """Wiersz: (CIK, okres, CUSIP, akcje, wartość)."""
    con.execute("""
        CREATE OR REPLACE TABLE p (
            CIK VARCHAR, PERIODOFREPORT DATE, CUSIP VARCHAR, shares BIGINT, value_corrected BIGINT
        )
    """)
    con.executemany("INSERT INTO p VALUES (?, ?, ?, ?, ?)", rows)
    con.execute(f"COPY p TO '{path}' (FORMAT parquet)")


def panel_from(tmp_path, pit: list[tuple], final: list[tuple] | None = None) -> dict:
    """Zwraca {(CIK, okres): wiersz panelu jako słownik}. Bez final obie wersje są takie same."""
    con = db.connect()
    pit_path, final_path = tmp_path / "pit.parquet", tmp_path / "final.parquet"
    write_positions(con, pit_path, pit)
    write_positions(con, final_path, final if final is not None else pit)
    rel = panel(con, pit_path, final_path, CONFIG, tmp_path)
    rows = [dict(zip(rel.columns, row, strict=True)) for row in rel.fetchall()]
    return {(row["CIK"], str(row["PERIODOFREPORT"])): row for row in rows}


def test_price_increase_is_not_new_money(tmp_path):
    rows = [("A", Q1, HOUSE, 100_000, 5_000_000), ("A", Q2, HOUSE, 100_000, 6_000_000)]
    row = panel_from(tmp_path, rows)[("A", Q1)]
    assert row["new_money_next"] == 0
    assert row["label"] is False


def test_purchase_above_threshold_is_positive(tmp_path):
    rows = [("A", Q1, HOUSE, 100_000, 5_000_000), ("A", Q2, HOUSE, 150_000, 7_500_000)]
    row = panel_from(tmp_path, rows)[("A", Q1)]
    assert row["new_money_next"] == pytest.approx(2_500_000)
    assert row["label"] is True


def test_purchase_below_threshold_is_negative(tmp_path):
    rows = [("A", Q1, HOUSE, 100_000, 5_000_000), ("A", Q2, HOUSE, 110_000, 5_500_000)]
    assert panel_from(tmp_path, rows)[("A", Q1)]["label"] is False


def test_split_is_not_new_money(tmp_path):
    holders = [f"H{i}" for i in range(10)]
    rows = [(h, Q1, HOUSE, 100_000, 5_000_000) for h in holders]
    rows += [(h, Q2, HOUSE, 200_000, 5_000_000) for h in holders]
    row = panel_from(tmp_path, rows)[("H0", Q1)]
    assert row["new_money_next"] == pytest.approx(0)
    assert row["label"] is False


def test_prospect_first_purchase(tmp_path):
    rows = [
        ("A", Q1, OTHER, 1_000, 200_000_000),
        ("A", Q2, OTHER, 1_000, 200_000_000),
        ("A", Q2, HOUSE, 40_000, 2_000_000),
    ]
    row = panel_from(tmp_path, rows)[("A", Q1)]
    assert row["has_house"] is False
    assert row["house_value"] == 0
    assert row["new_money_next"] == pytest.approx(2_000_000)
    assert row["label"] is True


def test_selling_everything_is_negative_money(tmp_path):
    rows = [
        ("A", Q1, HOUSE, 100_000, 5_000_000),
        ("A", Q2, OTHER, 1_000, 200_000),
        ("B", Q2, HOUSE, 10, 500),
    ]
    row = panel_from(tmp_path, rows)[("A", Q1)]
    assert row["new_money_next"] == pytest.approx(-5_000_000)
    assert row["label"] is False


def test_other_securities_do_not_count(tmp_path):
    rows = [("A", Q1, OTHER, 1_000, 200_000), ("A", Q2, OTHER, 100_000, 20_000_000)]
    row = panel_from(tmp_path, rows)[("A", Q1)]
    assert row["portfolio_value"] == 200_000
    assert row["new_money_next"] == 0


def test_no_report_next_quarter_gives_unknown_label(tmp_path):
    rows = [("A", Q1, HOUSE, 100_000, 5_000_000), ("A", Q3, HOUSE, 900_000, 45_000_000)]
    result = panel_from(tmp_path, rows)
    assert result[("A", Q1)]["label"] is None
    assert result[("A", Q3)]["label"] is None


def test_label_uses_final_version(tmp_path):
    pit = [("A", Q1, HOUSE, 100_000, 5_000_000)]
    final = pit + [("A", Q2, HOUSE, 150_000, 7_500_000)]
    row = panel_from(tmp_path, pit, final)[("A", Q1)]
    assert row["label"] is True


def test_features_use_point_in_time_version(tmp_path):
    pit = [("A", Q1, HOUSE, 100_000, 5_000_000), ("A", Q2, HOUSE, 100_000, 5_000_000)]
    final = [("A", Q1, HOUSE, 100_000, 5_000_000), ("A", Q2, HOUSE, 300_000, 15_000_000)]
    row = panel_from(tmp_path, pit, final)[("A", Q2)]
    assert row["house_value"] == 5_000_000
    assert row["new_money_t"] == 0


def test_feature_is_last_quarter_flow(tmp_path):
    rows = [
        ("A", Q1, HOUSE, 100_000, 5_000_000),
        ("A", Q2, HOUSE, 150_000, 7_500_000),
        ("A", Q3, HOUSE, 150_000, 7_500_000),
    ]
    result = panel_from(tmp_path, rows)
    assert result[("A", Q1)]["new_money_t"] is None
    assert result[("A", Q2)]["new_money_t"] == pytest.approx(2_500_000)
    assert result[("A", Q2)]["label"] is False


def test_excluded_filer_is_dropped(tmp_path):
    rows = [("EXCLUDED", Q1, HOUSE, 100_000, 5_000_000), ("A", Q1, HOUSE, 1, 50)]
    assert {cik for cik, _ in panel_from(tmp_path, rows)} == {"A"}

from datetime import UTC, datetime

from hidro_mg_lakehouse.bronze.control import CONTROL_COLUMNS, add_control_columns, row_hash


def test_row_hash_ignores_key_order():
    assert row_hash({"a": 1, "b": "x"}) == row_hash({"b": "x", "a": 1})


def test_row_hash_changes_with_content():
    assert row_hash({"a": 1}) != row_hash({"a": 2})


def test_add_control_columns_follows_adr_0003():
    loaded_at = datetime(2026, 11, 18, 12, 0, tzinfo=UTC)
    rows = add_control_columns(
        [{"a": 1}, {"a": 2}], "ibge", "/Volumes/x/f.json", batch_id="b1", loaded_at=loaded_at
    )

    assert [name for name, _ in CONTROL_COLUMNS] == [k for k in rows[0] if k.startswith("_")]
    assert rows[0]["_source"] == "ibge"
    assert rows[0]["_source_file"] == "/Volumes/x/f.json"
    assert {r["_batch_id"] for r in rows} == {"b1"}
    assert rows[1]["_loaded_at"] == loaded_at
    assert rows[0]["_row_hash"] == row_hash({"a": 1})


def test_add_control_columns_generates_one_batch_id():
    rows = add_control_columns([{"a": 1}, {"a": 2}], "ibge", "f.json")
    assert rows[0]["_batch_id"] == rows[1]["_batch_id"]

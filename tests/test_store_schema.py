from __future__ import annotations

from royale_analytics.store import Store


EXPECTED_TABLES = {
    "battles",
    "battle_sides",
    "battle_cards",
    "profile_snapshots",
    "fetch_log",
}


def _table_names(store: Store) -> set[str]:
    rows = store.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    return {r[0] for r in rows}


def test_init_schema_creates_all_five_tables():
    store = Store(":memory:")
    store.init_schema()
    assert EXPECTED_TABLES <= _table_names(store)


def test_init_schema_is_idempotent():
    store = Store(":memory:")
    store.init_schema()
    # Calling twice must not raise (IF NOT EXISTS).
    store.init_schema()
    assert EXPECTED_TABLES <= _table_names(store)


def test_battles_has_unique_constraint(tmp_path):
    db = tmp_path / "sub" / "royale.sqlite"
    store = Store(str(db))
    store.init_schema()
    # Inserting the same (player_tag, battle_time, opponent_tag) twice with
    # INSERT (not OR IGNORE) must violate the UNIQUE constraint.
    import sqlite3

    store.conn.execute(
        "INSERT INTO battles (player_tag, opponent_tag, battle_time) "
        "VALUES (?, ?, ?)",
        ("ME", "OPP", "2026-05-02T02:19:10+00:00"),
    )
    try:
        store.conn.execute(
            "INSERT INTO battles (player_tag, opponent_tag, battle_time) "
            "VALUES (?, ?, ?)",
            ("ME", "OPP", "2026-05-02T02:19:10+00:00"),
        )
        raised = False
    except sqlite3.IntegrityError:
        raised = True
    assert raised


def test_init_creates_parent_dirs(tmp_path):
    db = tmp_path / "nested" / "deeper" / "royale.sqlite"
    store = Store(str(db))
    store.init_schema()
    assert db.parent.is_dir()
    assert db.exists()

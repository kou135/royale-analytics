from __future__ import annotations

import os
import sqlite3


_SCHEMA = """
CREATE TABLE IF NOT EXISTS battles (
    id                   INTEGER PRIMARY KEY,
    player_tag           TEXT,
    opponent_tag         TEXT,
    battle_time          TEXT,
    type                 TEXT,
    game_mode_id         INTEGER,
    game_mode_name       TEXT,
    arena_name           TEXT,
    is_ladder_tournament INTEGER,
    league_number        INTEGER,
    deck_selection       TEXT,
    result               TEXT,
    raw_json             TEXT,
    UNIQUE(player_tag, battle_time, opponent_tag)
);

CREATE INDEX IF NOT EXISTS idx_battles_battle_time ON battles(battle_time);

CREATE TABLE IF NOT EXISTS battle_sides (
    id                 INTEGER PRIMARY KEY,
    battle_id          INTEGER,
    side               TEXT,
    tag                TEXT,
    name               TEXT,
    crowns             INTEGER,
    starting_trophies  INTEGER,
    trophy_change      INTEGER,
    king_tower_hp      INTEGER,
    princess_towers_hp TEXT,
    elixir_leaked      REAL,
    global_rank        INTEGER,
    clan_tag           TEXT,
    deck_key           TEXT,
    FOREIGN KEY (battle_id) REFERENCES battles(id)
);

CREATE TABLE IF NOT EXISTS battle_cards (
    id              INTEGER PRIMARY KEY,
    battle_id       INTEGER,
    side            TEXT,
    card_id         INTEGER,
    card_name       TEXT,
    level           INTEGER,
    max_level       INTEGER,
    evolution_level INTEGER,
    star_level      INTEGER,
    rarity          TEXT,
    elixir_cost     INTEGER,
    FOREIGN KEY (battle_id) REFERENCES battles(id)
);

CREATE TABLE IF NOT EXISTS profile_snapshots (
    id            INTEGER PRIMARY KEY,
    player_tag    TEXT,
    fetched_at    TEXT,
    trophies      INTEGER,
    best_trophies INTEGER,
    raw_json      TEXT
);

CREATE TABLE IF NOT EXISTS fetch_log (
    id            INTEGER PRIMARY KEY,
    player_tag    TEXT,
    fetched_at    TEXT,
    new_battles   INTEGER,
    gap_suspected INTEGER
);
"""


class Store:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self.conn = sqlite3.connect(db_path)

    def init_schema(self) -> None:
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

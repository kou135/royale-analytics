from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone

from royale_analytics.battletime import to_utc_iso
from royale_analytics.decks import compute_deck_key
from royale_analytics.errors import BattleTimeParseError


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


def _to_card_dict(api_card: dict) -> dict:
    """Convert an API camelCase card to the contract's snake_case card dict."""
    return {
        "name": api_card["name"],
        "id": api_card["id"],
        "level": api_card["level"],
        "max_level": api_card["maxLevel"],
        "elixir_cost": api_card["elixirCost"],
        "rarity": api_card.get("rarity", ""),
        "evolution_level": api_card.get("evolutionLevel"),
    }


def _derive_result(team_crowns: int, opponent_crowns: int) -> str:
    if team_crowns > opponent_crowns:
        return "win"
    if team_crowns < opponent_crowns:
        return "loss"
    return "draw"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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

    def upsert_battles(self, player_tag: str, battlelog: list[dict]) -> int:
        inserted = 0
        for raw in battlelog:
            team = raw["team"][0]
            opponent = raw["opponent"][0]
            opponent_tag = opponent["tag"]
            try:
                battle_time = to_utc_iso(raw["battleTime"])
            except BattleTimeParseError:
                continue
            game_mode = raw.get("gameMode") or {}
            arena = raw.get("arena") or {}
            cur = self.conn.execute(
                "INSERT OR IGNORE INTO battles ("
                "player_tag, opponent_tag, battle_time, type, "
                "game_mode_id, game_mode_name, arena_name, "
                "is_ladder_tournament, league_number, deck_selection, "
                "result, raw_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    player_tag,
                    opponent_tag,
                    battle_time,
                    raw.get("type"),
                    game_mode.get("id"),
                    game_mode.get("name"),
                    arena.get("name"),
                    1 if raw.get("isLadderTournament") else 0,
                    raw.get("leagueNumber"),
                    raw.get("deckSelection"),
                    _derive_result(team["crowns"], opponent["crowns"]),
                    json.dumps(raw),
                ),
            )
            if cur.rowcount == 0:
                # Already present (UNIQUE collision) -> skip side/card writes.
                continue
            inserted += 1
            battle_id = cur.lastrowid
            self._insert_side(battle_id, "team", team)
            self._insert_side(battle_id, "opponent", opponent)
        self.conn.commit()
        return inserted

    def _insert_side(self, battle_id: int, side: str, raw_side: dict) -> None:
        cards = [_to_card_dict(c) for c in raw_side.get("cards", [])]
        deck_key = compute_deck_key(cards)
        self.conn.execute(
            "INSERT INTO battle_sides ("
            "battle_id, side, tag, name, crowns, starting_trophies, "
            "trophy_change, king_tower_hp, princess_towers_hp, "
            "elixir_leaked, global_rank, clan_tag, deck_key) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                battle_id,
                side,
                raw_side.get("tag"),
                raw_side.get("name"),
                raw_side.get("crowns"),
                raw_side.get("startingTrophies"),
                raw_side.get("trophyChange"),
                raw_side.get("kingTowerHitPoints"),
                None,
                raw_side.get("elixirLeaked"),
                raw_side.get("globalRank"),
                (raw_side.get("clan") or {}).get("tag"),
                deck_key,
            ),
        )
        for card in cards:
            self.conn.execute(
                "INSERT INTO battle_cards ("
                "battle_id, side, card_id, card_name, level, max_level, "
                "evolution_level, star_level, rarity, elixir_cost) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    battle_id,
                    side,
                    card["id"],
                    card["name"],
                    card["level"],
                    card["max_level"],
                    card["evolution_level"],
                    None,
                    card["rarity"],
                    card["elixir_cost"],
                ),
            )

    def save_profile_snapshot(self, player_tag: str, profile: dict) -> None:
        self.conn.execute(
            "INSERT INTO profile_snapshots ("
            "player_tag, fetched_at, trophies, best_trophies, raw_json) "
            "VALUES (?,?,?,?,?)",
            (
                player_tag,
                _utcnow_iso(),
                profile.get("trophies"),
                profile.get("bestTrophies"),
                json.dumps(profile),
            ),
        )
        self.conn.commit()

    def record_fetch(
        self, player_tag: str, new_battles: int, gap_suspected: bool
    ) -> None:
        self.conn.execute(
            "INSERT INTO fetch_log ("
            "player_tag, fetched_at, new_battles, gap_suspected) "
            "VALUES (?,?,?,?)",
            (
                player_tag,
                _utcnow_iso(),
                new_battles,
                1 if gap_suspected else 0,
            ),
        )
        self.conn.commit()

    def load_battles(self, player_tag: str) -> list[dict]:
        battle_rows = self.conn.execute(
            "SELECT id, battle_time, game_mode_name, is_ladder_tournament, "
            "league_number, result FROM battles WHERE player_tag = ? "
            "ORDER BY battle_time",
            (player_tag,),
        ).fetchall()
        views: list[dict] = []
        for (
            battle_id,
            battle_time,
            game_mode_name,
            is_ladder_tournament,
            league_number,
            result,
        ) in battle_rows:
            views.append(
                {
                    "battle_time": battle_time,
                    "game_mode_name": game_mode_name,
                    "is_ladder_tournament": bool(is_ladder_tournament),
                    "league_number": league_number,
                    "result": result,
                    "team": self._load_side(battle_id, "team"),
                    "opponent": self._load_side(battle_id, "opponent"),
                }
            )
        return views

    def _load_side(self, battle_id: int, side: str) -> dict:
        side_row = self.conn.execute(
            "SELECT tag, name, crowns, trophy_change, elixir_leaked, deck_key "
            "FROM battle_sides WHERE battle_id = ? AND side = ?",
            (battle_id, side),
        ).fetchone()
        tag, name, crowns, trophy_change, elixir_leaked, deck_key = side_row
        card_rows = self.conn.execute(
            "SELECT card_name, card_id, level, max_level, elixir_cost, "
            "rarity, evolution_level FROM battle_cards "
            "WHERE battle_id = ? AND side = ? ORDER BY id",
            (battle_id, side),
        ).fetchall()
        cards = [
            {
                "name": r[0],
                "id": r[1],
                "level": r[2],
                "max_level": r[3],
                "elixir_cost": r[4],
                "rarity": r[5],
                "evolution_level": r[6],
            }
            for r in card_rows
        ]
        return {
            "tag": tag,
            "name": name,
            "crowns": crowns,
            "trophy_change": trophy_change,
            "elixir_leaked": elixir_leaked,
            "deck_key": deck_key,
            "cards": cards,
        }

    def get_latest_profile(self, player_tag: str) -> dict | None:
        row = self.conn.execute(
            "SELECT raw_json FROM profile_snapshots WHERE player_tag = ? "
            "ORDER BY id DESC LIMIT 1",
            (player_tag,),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

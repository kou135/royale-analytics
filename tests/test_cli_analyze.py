from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

import royale_analytics.cli as cli_module
from royale_analytics.cli import cli
from royale_analytics.config import Config
from royale_analytics.reference import load_reference
from royale_analytics.store import Store
from tests.factories import HOG_DECK, GOLEM_DECK, make_profile, make_raw_battle


def _seed_store(tmp_path) -> Config:
    config = Config(
        token="tok-123",
        base_url="https://proxy.royaleapi.dev/v1",
        player_tag="2PP",
        db_path=str(tmp_path / "royale.sqlite"),
    )
    store = Store(config.db_path)
    store.init_schema()
    battlelog = [
        make_raw_battle(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                        team_crowns=2, opp_crowns=1,
                        battle_time="20260502T021910.000Z"),
        make_raw_battle(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                        team_crowns=0, opp_crowns=3,
                        battle_time="20260502T022500.000Z"),
    ]
    store.upsert_battles(config.player_tag, battlelog)
    store.save_profile_snapshot(
        config.player_tag, make_profile({"Hog Rider": (11, 14)})
    )
    return config


def test_analyze_outputs_markdown(tmp_path, monkeypatch):
    config = _seed_store(tmp_path)
    monkeypatch.setattr(cli_module, "load_config", lambda: config)
    monkeypatch.setattr(cli_module, "load_reference", load_reference)

    runner = CliRunner()
    result = runner.invoke(cli, ["analyze"])

    assert result.exit_code == 0, result.output
    assert "あなたのデッキ" in result.output


def test_analyze_json_out_writes_valid_json(tmp_path, monkeypatch):
    config = _seed_store(tmp_path)
    monkeypatch.setattr(cli_module, "load_config", lambda: config)
    monkeypatch.setattr(cli_module, "load_reference", load_reference)

    out_path = tmp_path / "brief.json"
    runner = CliRunner()
    result = runner.invoke(cli, ["analyze", "--json-out", str(out_path)])

    assert result.exit_code == 0, result.output
    assert "あなたのデッキ" in result.output
    assert out_path.exists()
    with open(out_path, encoding="utf-8") as fh:
        data = json.load(fh)
    assert isinstance(data, dict)
    assert data["sample_size"] == 2

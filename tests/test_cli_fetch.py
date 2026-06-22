from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

import royale_analytics.cli as cli_module
from royale_analytics.cli import cli
from royale_analytics.config import Config
from royale_analytics.store import Store
from tests.factories import HOG_DECK, GOLEM_DECK, make_profile, make_raw_battle


def _config(tmp_path) -> Config:
    return Config(
        token="tok-123",
        base_url="https://proxy.royaleapi.dev/v1",
        player_tag="2PP",
        db_path=str(tmp_path / "royale.sqlite"),
    )


class FakeApiClient:
    def __init__(self, token, base_url, *, battlelog, profile, chests=None,
                 chests_error=None):
        self.token = token
        self.base_url = base_url
        self._battlelog = battlelog
        self._profile = profile
        self._chests = chests if chests is not None else {"items": []}
        self._chests_error = chests_error

    def get_player(self, tag):
        return self._profile

    def get_battlelog(self, tag):
        return self._battlelog

    def get_upcoming_chests(self, tag):
        if self._chests_error is not None:
            raise self._chests_error
        return self._chests


def test_fetch_reports_new_battle_count(tmp_path, monkeypatch):
    config = _config(tmp_path)
    battlelog = [
        make_raw_battle(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                        team_crowns=2, opp_crowns=1,
                        battle_time="20260502T021910.000Z"),
        make_raw_battle(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                        team_crowns=0, opp_crowns=3,
                        battle_time="20260502T022500.000Z"),
    ]
    profile = make_profile({"Hog Rider": (11, 14)})

    def fake_factory(token, base_url):
        return FakeApiClient(token, base_url, battlelog=battlelog,
                             profile=profile)

    monkeypatch.setattr(cli_module, "load_config", lambda: config)
    monkeypatch.setattr(cli_module, "ApiClient", fake_factory)

    runner = CliRunner()
    result = runner.invoke(cli, ["fetch"])

    assert result.exit_code == 0, result.output
    assert "2 件の新規対戦を取得" in result.output
    # 2 < 25 → ギャップ警告は出さない
    assert "ギャップ" not in result.output
    # battles actually persisted
    assert len(Store(config.db_path).load_battles(config.player_tag)) == 2


def test_fetch_gap_note_and_tolerates_chests_failure(tmp_path, monkeypatch):
    config = _config(tmp_path)
    battlelog = [
        make_raw_battle(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                        team_crowns=2, opp_crowns=1,
                        battle_time=f"20260502T0219{i:02d}.000Z",
                        opponent_tag=f"#OPP{i}")
        for i in range(25)
    ]
    profile = make_profile({"Hog Rider": (11, 14)})

    def fake_factory(token, base_url):
        return FakeApiClient(
            token, base_url, battlelog=battlelog, profile=profile,
            chests_error=RuntimeError("chests boom"),
        )

    monkeypatch.setattr(cli_module, "load_config", lambda: config)
    monkeypatch.setattr(cli_module, "ApiClient", fake_factory)

    runner = CliRunner()
    result = runner.invoke(cli, ["fetch"])

    assert result.exit_code == 0, result.output
    assert "25 件の新規対戦を取得" in result.output
    assert "ギャップ警告" in result.output  # 25 >= 25
    assert "upcomingchests の取得に失敗" in result.output  # tolerated, not fatal


def test_fetch_reports_empty_battlelog(monkeypatch, tmp_path):
    config = _config(tmp_path)
    profile = make_profile({"Hog Rider": (11, 14)})

    def fake_factory(token, base_url):
        return FakeApiClient(token, base_url, battlelog=[], profile=profile)

    monkeypatch.setattr(cli_module, "load_config", lambda: config)
    monkeypatch.setattr(cli_module, "ApiClient", fake_factory)

    runner = CliRunner()
    result = runner.invoke(cli, ["fetch"])

    assert result.exit_code == 0, result.output
    assert "まだ対戦がありません" in result.output

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

import royale_analytics.cli as cli_module
from royale_analytics.cli import cli
from royale_analytics.config import Config
from royale_analytics.errors import AccessDeniedError, ConfigError
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
    def __init__(self, token, base_url, *, battlelog, profile, get_player_error=None):
        self.token = token
        self.base_url = base_url
        self._battlelog = battlelog
        self._profile = profile
        self._get_player_error = get_player_error

    def get_player(self, tag):
        if self._get_player_error is not None:
            raise self._get_player_error
        return self._profile

    def get_battlelog(self, tag):
        return self._battlelog


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


def test_fetch_gap_note(tmp_path, monkeypatch):
    """25件のbattlelogでギャップ警告が出ること。chestsコールは行わない。"""
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
        return FakeApiClient(token, base_url, battlelog=battlelog, profile=profile)

    monkeypatch.setattr(cli_module, "load_config", lambda: config)
    monkeypatch.setattr(cli_module, "ApiClient", fake_factory)

    runner = CliRunner()
    result = runner.invoke(cli, ["fetch"])

    assert result.exit_code == 0, result.output
    assert "25 件の新規対戦を取得" in result.output
    assert "ギャップ警告" in result.output  # 25 >= 25
    # fetch no longer calls chests — no chest-related output
    assert "upcomingchests" not in result.output


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


def test_fetch_access_denied_shows_guidance(monkeypatch, tmp_path):
    """403 AccessDeniedError: CLI exits non-zero and guidance (IP) is shown."""
    config = _config(tmp_path)
    error = AccessDeniedError(
        "Access denied.",
        status=403,
        guidance="whitelist 45.79.218.79 on developer.clashroyale.com",
    )

    def fake_factory(token, base_url):
        return FakeApiClient(
            token, base_url, battlelog=[], profile={}, get_player_error=error
        )

    monkeypatch.setattr(cli_module, "load_config", lambda: config)
    monkeypatch.setattr(cli_module, "ApiClient", fake_factory)

    runner = CliRunner()
    result = runner.invoke(cli, ["fetch"], catch_exceptions=False)

    assert result.exit_code != 0
    # guidance string must appear in output (CliRunner mixes stderr into output)
    assert "45.79.218.79" in result.output


def test_fetch_config_error_exits_nonzero(monkeypatch):
    """Missing token ConfigError: CLI exits non-zero with a helpful message."""
    monkeypatch.setattr(
        cli_module,
        "load_config",
        lambda: (_ for _ in ()).throw(
            ConfigError("CLASH_ROYALE_API_TOKEN が設定されていません。")
        ),
    )

    runner = CliRunner()
    result = runner.invoke(cli, ["fetch"], catch_exceptions=False)

    assert result.exit_code != 0
    assert "CLASH_ROYALE_API_TOKEN" in result.output

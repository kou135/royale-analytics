from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

import royale_analytics.cli as cli_module
from royale_analytics.cli import cli
from royale_analytics.config import Config


def test_init_prints_tag_and_whitelist_and_creates_db(tmp_path, monkeypatch):
    db_path = tmp_path / "royale.sqlite"
    fake_config = Config(
        token="tok-123",
        base_url="https://proxy.royaleapi.dev/v1",
        player_tag="2PP",
        db_path=str(db_path),
    )
    monkeypatch.setattr(cli_module, "load_config", lambda: fake_config)

    runner = CliRunner()
    result = runner.invoke(cli, ["init"])

    assert result.exit_code == 0, result.output
    assert "2PP" in result.output
    assert str(db_path) in result.output
    assert "45.79.218.79" in result.output
    assert "https://proxy.royaleapi.dev/v1" in result.output
    assert db_path.exists()

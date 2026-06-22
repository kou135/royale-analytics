from __future__ import annotations

import pytest

from royale_analytics.config import Config, load_config
from royale_analytics.errors import ConfigError


def test_load_config_minimal_uses_defaults_and_normalizes_tag():
    cfg = load_config({"CLASH_ROYALE_API_TOKEN": "t", "CR_PLAYER_TAG": "#C0G"})
    assert cfg == Config(
        token="t",
        base_url="https://proxy.royaleapi.dev/v1",
        player_tag="C0G",
        db_path="data/royale.sqlite",
    )


def test_load_config_normalizes_o_in_player_tag():
    cfg = load_config({"CLASH_ROYALE_API_TOKEN": "t", "CR_PLAYER_TAG": "#OPR"})
    assert cfg.player_tag == "0PR"


def test_load_config_respects_cr_api_base_override():
    cfg = load_config(
        {
            "CLASH_ROYALE_API_TOKEN": "t",
            "CR_PLAYER_TAG": "#C0G",
            "CR_API_BASE": "https://api.clashroyale.com/v1",
        }
    )
    assert cfg.base_url == "https://api.clashroyale.com/v1"


def test_load_config_respects_ra_db_path_override():
    cfg = load_config(
        {
            "CLASH_ROYALE_API_TOKEN": "t",
            "CR_PLAYER_TAG": "#C0G",
            "RA_DB_PATH": "/tmp/custom.sqlite",
        }
    )
    assert cfg.db_path == "/tmp/custom.sqlite"


def test_config_is_frozen():
    cfg = load_config({"CLASH_ROYALE_API_TOKEN": "t", "CR_PLAYER_TAG": "#C0G"})
    with pytest.raises(Exception):
        cfg.token = "other"  # type: ignore[misc]


def test_load_config_missing_token_raises():
    with pytest.raises(ConfigError):
        load_config({"CR_PLAYER_TAG": "#C0G"})


def test_load_config_missing_player_tag_raises():
    with pytest.raises(ConfigError):
        load_config({"CLASH_ROYALE_API_TOKEN": "t"})

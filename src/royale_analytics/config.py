from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

from royale_analytics.errors import ConfigError
from royale_analytics.tags import normalize_tag

DEFAULT_BASE_URL = "https://proxy.royaleapi.dev/v1"
DEFAULT_DB_PATH = "data/royale.sqlite"


@dataclass(frozen=True)
class Config:
    token: str
    base_url: str
    player_tag: str  # normalized (no '#')
    db_path: str


def load_config(env: Mapping[str, str] | None = None) -> Config:
    """Build a Config from a mapping of environment variables.

    When env is None, load_dotenv() is called and os.environ is used. Tests
    always pass env explicitly and never touch the real environment or .env.

    Reads CLASH_ROYALE_API_TOKEN and CR_PLAYER_TAG (both required), and the
    optional overrides CR_API_BASE (default https://proxy.royaleapi.dev/v1)
    and RA_DB_PATH (default data/royale.sqlite). Missing token or player tag
    raises ConfigError.
    """
    if env is None:
        from dotenv import load_dotenv

        load_dotenv()
        env = os.environ

    token = env.get("CLASH_ROYALE_API_TOKEN")
    if not token:
        raise ConfigError(
            "CLASH_ROYALE_API_TOKEN is not set. Create a token at "
            "developer.clashroyale.com and put it in your environment or .env."
        )

    raw_tag = env.get("CR_PLAYER_TAG")
    if not raw_tag:
        raise ConfigError(
            "CR_PLAYER_TAG is not set. Set it to your player tag (e.g. #C0G20PR2)."
        )

    base_url = env.get("CR_API_BASE", DEFAULT_BASE_URL)
    db_path = env.get("RA_DB_PATH", DEFAULT_DB_PATH)

    return Config(
        token=token,
        base_url=base_url,
        player_tag=normalize_tag(raw_tag),
        db_path=db_path,
    )

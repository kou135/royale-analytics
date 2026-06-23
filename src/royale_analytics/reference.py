from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Reference:
    card_roles: dict
    archetype_rules: dict
    archetype_profiles: dict
    template_decks: list


def _read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_reference(ref_dir: str | Path | None = None) -> Reference:
    if ref_dir is None:
        base = Path(__file__).resolve().parent / "reference"
    else:
        base = Path(ref_dir)

    card_roles = _read_json(base / "card_roles.json")
    archetype_rules = _read_json(base / "archetype_rules.json")
    archetype_profiles = _read_json(base / "archetype_profiles.json")
    template_decks_doc = _read_json(base / "template_decks.json")

    return Reference(
        card_roles=card_roles,
        archetype_rules=archetype_rules,
        archetype_profiles=archetype_profiles,
        template_decks=template_decks_doc["decks"],
    )

# tests/factories.py
from __future__ import annotations
from royale_analytics.decks import compute_deck_key


def make_card(name, id, elixir_cost, *, level=11, max_level=14,
              rarity="common", evolution_level=None):
    return {"name": name, "id": id, "level": level, "max_level": max_level,
            "elixir_cost": elixir_cost, "rarity": rarity,
            "evolution_level": evolution_level}


HOG_DECK = [
    make_card("Hog Rider", 1, 4, rarity="rare"),
    make_card("Ice Spirit", 2, 1),
    make_card("Ice Golem", 3, 2, rarity="rare"),
    make_card("Skeletons", 4, 1),
    make_card("Musketeer", 5, 4, rarity="rare"),
    make_card("Fireball", 6, 4, rarity="rare"),
    make_card("The Log", 7, 2, rarity="legendary"),
    make_card("Cannon", 8, 3),
]

GOLEM_DECK = [
    make_card("Golem", 11, 8, rarity="epic"),
    make_card("Baby Dragon", 12, 4, rarity="epic"),
    make_card("Mega Minion", 13, 3, rarity="rare"),
    make_card("Lightning", 14, 6, rarity="epic"),
    make_card("Tornado", 15, 3, rarity="epic"),
    make_card("Lumberjack", 16, 4, rarity="legendary"),
    make_card("Barbarian Barrel", 17, 2, rarity="epic"),
    make_card("Night Witch", 18, 4, rarity="epic"),
]


def make_battle_view(*, team_cards, opp_cards, team_crowns, opp_crowns,
                     battle_time="2026-05-02T02:19:10+00:00", result=None,
                     mode_fields=None, team_elixir_leaked=None,
                     opp_elixir_leaked=None, trophy_change=None):
    if result is None:
        result = ("win" if team_crowns > opp_crowns
                  else "loss" if team_crowns < opp_crowns else "draw")
    mf = {"game_mode_name": "Ladder", "is_ladder_tournament": False,
          "league_number": None}
    if mode_fields:
        mf.update(mode_fields)

    def side(tag, name, cards, crowns, leaked):
        return {"tag": tag, "name": name, "crowns": crowns,
                "trophy_change": trophy_change, "elixir_leaked": leaked,
                "deck_key": compute_deck_key(cards), "cards": cards}

    return {
        "battle_time": battle_time, "result": result, **mf,
        "team": side("#ME", "Me", team_cards, team_crowns, team_elixir_leaked),
        "opponent": side("#OPP", "Opp", opp_cards, opp_crowns, opp_elixir_leaked),
    }


def make_raw_battle(*, battle_time="20260502T021910.000Z", team_cards, opp_cards,
                    team_crowns, opp_crowns, opponent_tag="#OPP", player_tag="#ME",
                    game_mode_name="Ladder", is_ladder_tournament=False,
                    league_number=0, trophy_change=-30,
                    team_elixir_leaked=3.0, opp_elixir_leaked=2.0):
    """公式 API の battlelog 1要素を模す（camelCase）。store はこれを snake_case に変換する。"""
    def api_card(c):
        d = {"name": c["name"], "id": c["id"], "level": c["level"],
             "maxLevel": c["max_level"], "elixirCost": c["elixir_cost"],
             "rarity": c["rarity"]}
        if c["evolution_level"] is not None:
            d["evolutionLevel"] = c["evolution_level"]
        return d

    def side(tag, name, cards, crowns, leaked):
        return {"tag": tag, "name": name, "crowns": crowns,
                "startingTrophies": 6000, "trophyChange": trophy_change,
                "elixirLeaked": leaked, "cards": [api_card(c) for c in cards]}

    return {
        "type": "PvP", "battleTime": battle_time,
        "isLadderTournament": is_ladder_tournament,
        "arena": {"id": 1, "name": "Arena"},
        "gameMode": {"id": 72000006, "name": game_mode_name},
        "deckSelection": "collection", "leagueNumber": league_number,
        "team": [side(player_tag, "Me", team_cards, team_crowns, team_elixir_leaked)],
        "opponent": [side(opponent_tag, "Opp", opp_cards, opp_crowns, opp_elixir_leaked)],
    }


def make_profile(card_levels):
    """card_levels: {name: (level, max_level)} → API プロフィール風 dict。"""
    return {"tag": "#ME", "name": "Me", "trophies": 6000, "bestTrophies": 6500,
            "cards": [{"name": n, "level": lv, "maxLevel": mx}
                      for n, (lv, mx) in card_levels.items()]}

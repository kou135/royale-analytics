# Royale Analytics MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** OSS のクラッシュロワイヤル AI 分析ツール（Claude Code skill）の MVP を、決定論的 Python コア＋セッション Claude 分析という構成で実装する。

**Architecture:** 案A。Python パッケージ `royale_analytics` が公式 API（RoyaleAPI proxy 経由）からデータを取得し SQLite に蓄積、決定論的に特徴量を算出して「分析ブリーフ（Markdown＋JSON）」を出力する。`.claude/skills/royale-analyzer/SKILL.md` が Claude Code セッションに「CLI 実行 → ブリーフ読込 → 局所解回避ルーブリックで定性分析」を指示する。

**Tech Stack:** Python 3.11+ / httpx（HTTP）/ click（CLI）/ python-dotenv（.env）/ pytest（テスト）/ SQLite（標準 `sqlite3`）。

設計書: `docs/superpowers/specs/2026-06-22-royale-analytics-mvp-design.md`

---

## Global Constraints

これらは全タスクの暗黙の要件。値は逐語。

- **Python**: 3.11 以上（`list[dict]` / `X | None` 構文を使用）。
- **依存**: 実行時 `httpx`, `click`, `python-dotenv`。開発時 `pytest`。これ以外を勝手に増やさない。
- **API base URL 既定**: `https://proxy.royaleapi.dev/v1`（環境変数 `CR_API_BASE` で上書き可）。
- **proxy ホワイトリスト IP**: `45.79.218.79`（README / `init` ガイドに明記）。
- **DB パス既定**: `data/royale.sqlite`（環境変数 `RA_DB_PATH` で上書き可）。
- **環境変数名**: `CLASH_ROYALE_API_TOKEN`, `CR_PLAYER_TAG`, `CR_API_BASE`, `RA_DB_PATH`。
- **タグ有効文字**: `0289CGJLPQRUVY`（`O` は存在しない→`0` に変換）。リクエスト時 `#`→`%23`。
- **battleTime 形式**: `%Y%m%dT%H%M%S.%fZ`（例 `20260502T021910.000Z`）。保存は UTC ISO。
- **必須免責文（逐語）**: `This material is unofficial and is not endorsed by Supercell. For more information see Supercell's Fan Content Policy: www.supercell.com/fan-content-policy.`
- **命名（商標回避）**: パッケージ `royale_analytics` / CLI `ra` / skill `royale-analyzer`。"Clash" を製品名に含めない。
- **課金機能を実装しない**（OSS 無料）。
- **ライセンス**: MIT。
- **秘密情報**: トークンは env のみ。`.env` と `data/` は `.gitignore`。トークンをコミットしない。
- **nullable 前提**: `elixir_leaked` / `king_tower_hp` / `global_rank` / `evolution_level` 等は欠落し得る。
- **立ち回り・elixirLeaked 由来の示唆は「推測（実測ではない）」と必ず明示**（ブリーフ／skill 双方）。

---

## Commit & Semantic Phase Strategy

ユーザー要望に従い、**コミットは意味的な段階（フェーズ）で分ける**。原則は「1タスク＝1コミット＝テストが通る最小の意味的増分」。フェーズは関連タスクの束。各コミットは Conventional Commits 形式。

| フェーズ | 意味的単位 | タスク | コミット種別 |
|---|---|---|---|
| Phase 0 | プロジェクト土台 | T1 scaffolding（pyproject/gitignore/env.example/README/errors/factories） | `chore:` |
| Phase 1 | 基礎ユーティリティ | T2 tags / T3 battletime / T4 decks / T5 config | `feat:` ×4 |
| Phase 2 | API クライアント | T6 client core / T7 endpoints | `feat:` ×2 |
| Phase 3 | 蓄積（SQLite） | T8 schema+init / T9 write path / T10 read path | `feat:` ×3 |
| Phase 4 | リファレンス＆分類 | T11 reference / T12 classify_deck / T13 match_deck | `feat:` ×3 |
| Phase 5 | 特徴量 | T14 matchups / T15 loss+elixir / T16 deficits+frequent / T17 build_features | `feat:` ×4 |
| Phase 6 | 分析ブリーフ | T18 render_json / T19 render_markdown | `feat:` ×2 |
| Phase 7 | CLI | T20 init / T21 fetch / T22 analyze | `feat:` ×3 |
| Phase 8 | skill | T23 SKILL.md | `docs:` ×1 |

各タスクの最終ステップは、そのタスク専用ファイルだけを `git add` して上記種別でコミットする。各コミットメッセージは本計画のタスク見出しの英語スコープに対応させる。

---

## File Structure

各ファイルは単一責務。

| ファイル | 責務 |
|---|---|
| `pyproject.toml` | パッケージ定義・依存・CLI エントリポイント `ra` |
| `.gitignore` | `.env` / `data/` / `__pycache__` 等を除外 |
| `.env.example` | 環境変数サンプル |
| `README.md` | プロジェクト説明・セットアップ・免責文 |
| `src/royale_analytics/__init__.py` | パッケージ宣言・`__version__` |
| `src/royale_analytics/errors.py` | 例外階層（全モジュール共通） |
| `src/royale_analytics/tags.py` | プレイヤータグ正規化・エンコード |
| `src/royale_analytics/battletime.py` | `battleTime` パース・UTC ISO 変換 |
| `src/royale_analytics/decks.py` | `compute_deck_key` / `average_elixir`（reference 不要の純関数） |
| `src/royale_analytics/config.py` | 環境変数読込（`Config` / `load_config`） |
| `src/royale_analytics/api_client.py` | httpx 薄クライアント・エラーマッピング・429 バックオフ |
| `src/royale_analytics/store.py` | SQLite スキーマ・冪等 upsert・battle view 復元 |
| `src/royale_analytics/reference.py` | リファレンス JSON 読込（`Reference` / `load_reference`） |
| `src/royale_analytics/classify.py` | `classify_deck` / `match_deck` |
| `src/royale_analytics/features.py` | 蓄積→特徴量（matchups/loss/elixir/deficit/frequent/build） |
| `src/royale_analytics/brief.py` | `render_json` / `render_markdown` |
| `src/royale_analytics/cli.py` | click グループ `cli` と `init`/`fetch`/`analyze` |
| `src/royale_analytics/reference/card_roles.json` | カード→役割/特性タグ |
| `src/royale_analytics/reference/archetype_rules.json` | アーキタイプ判定の閾値・カード群 |
| `src/royale_analytics/reference/archetype_profiles.json` | アーキタイプ単位の強み/弱み/勝ち筋 |
| `src/royale_analytics/reference/template_decks.json` | 厳選定番デッキ |
| `.claude/skills/royale-analyzer/SKILL.md` | オーケストレーション＋局所解回避ルーブリック |
| `tests/factories.py` | 共有フィクスチャ（カード/デッキ/battlelog/battle view ヘルパー） |
| `tests/test_*.py` | 各モジュールの単体テスト |

---

## Module Interface Contract

**全タスクはこの契約のシグネチャ・型・名前を厳密に守ること。** 後続タスクは先行タスクの定義のみを前提に書かれている。

### 共通データ形状

**card dict**（battle_cards 1枚・全モジュール共通）:
```python
{"name": str, "id": int, "level": int, "max_level": int,
 "elixir_cost": int, "rarity": str, "evolution_level": int | None}
```

**battle view dict**（`Store.load_battles` が返す1試合・`features` の入力）:
```python
{
  "battle_time": str,            # UTC ISO 例 "2026-05-02T02:19:10+00:00"
  "game_mode_name": str | None,
  "is_ladder_tournament": bool,
  "league_number": int | None,
  "result": str,                 # "win" | "loss" | "draw"（owner=team 視点）
  "team": {
    "tag": str, "name": str, "crowns": int,
    "trophy_change": int | None, "elixir_leaked": float | None,
    "deck_key": str, "cards": list[card dict],  # 8枚
  },
  "opponent": { ...team と同形状... },
}
```

### errors.py（Phase 0 で全定義）
```python
class RoyaleAnalyticsError(Exception): ...
class InvalidTagError(RoyaleAnalyticsError, ValueError): ...
class BattleTimeParseError(RoyaleAnalyticsError, ValueError): ...
class ConfigError(RoyaleAnalyticsError): ...
class ApiError(RoyaleAnalyticsError):
    def __init__(self, message: str, *, status: int | None = None, guidance: str = "") -> None: ...
    # 属性: .status, .guidance
class AccessDeniedError(ApiError): ...   # 403
class NotFoundError(ApiError): ...       # 404
class ThrottledError(ApiError): ...      # 429（リトライ後も）
class MaintenanceError(ApiError): ...    # 503
class ApiServerError(ApiError): ...      # 5xx
```

### tags.py
```python
VALID_TAG_CHARS: str = "0289CGJLPQRUVY"
def normalize_tag(raw: str) -> str: ...   # '#'除去, 大文字化, O→0, 文字種検証。不正は InvalidTagError
def encode_tag(raw: str) -> str: ...      # normalize 後に "%23" + tag を返す
```

### battletime.py
```python
def parse_battle_time(s: str) -> datetime: ...   # tz-aware UTC。失敗は BattleTimeParseError
def to_utc_iso(s: str) -> str: ...               # parse して .isoformat() を返す
```

### decks.py
```python
def compute_deck_key(cards: list[dict]) -> str: ...  # card["id"] を昇順 unique で ","連結
def average_elixir(cards: list[dict]) -> float: ...  # mean(card["elixir_cost"]) を小数1桁に round
```

### config.py
```python
@dataclass(frozen=True)
class Config:
    token: str
    base_url: str
    player_tag: str   # normalize 済（'#'なし）
    db_path: str
def load_config(env: Mapping[str, str] | None = None) -> Config: ...
# env=None のとき load_dotenv() 後に os.environ を使用。
# 既定: base_url="https://proxy.royaleapi.dev/v1", db_path="data/royale.sqlite"
# token / player_tag 欠落は ConfigError。
```

### api_client.py
```python
class ApiClient:
    def __init__(self, token: str, base_url: str, *,
                 client: "httpx.Client | None" = None,
                 max_retries: int = 2,
                 sleep: "Callable[[float], None]" = time.sleep) -> None: ...
    def get_player(self, tag: str) -> dict: ...
    def get_battlelog(self, tag: str) -> list[dict]: ...
    def get_upcoming_chests(self, tag: str) -> dict: ...
    def get_cards(self) -> dict: ...
    # 内部 _get(self, path: str) -> Any:
    #   - ヘッダ Authorization: Bearer <token>
    #   - 403→AccessDeniedError / 404→NotFoundError / 503→MaintenanceError / 5xx→ApiServerError
    #   - 429: ヘッダ x-ratelimit-retry-after(µs)→秒に変換し sleep、max_retries まで再試行、超えたら ThrottledError
    #   - 各例外に実行可能な .guidance を設定
    # tag を取るメソッドは encode_tag で %23 エンコードしてからパスに使う
```

### reference.py
```python
@dataclass
class Reference:
    card_roles: dict       # {"version":..., "cards": {name: {"role":str,"tags":[str]}}}
    archetype_rules: dict
    archetype_profiles: dict
    template_decks: list   # [{name,archetype,cards,avg_elixir,win_condition,strengths,weaknesses,counters}]
def load_reference(ref_dir: "str | Path | None" = None) -> Reference: ...
# ref_dir=None のとき パッケージ同梱 reference/ を読む（importlib.resources / __file__ 基準）
```

### classify.py
```python
@dataclass
class DeckClassification:
    archetype: str             # "cycle"|"beatdown"|"siege"|"bridge_spam"|"control"
    avg_elixir: float
    role_counts: dict          # {"wincon":int,"support":int,"defense":int,"cycle":int,"spell":int}
    weakness_tags: list[str]
    card_names: list[str]
@dataclass
class DeckMatch:
    name: str | None
    confidence: str            # "exact"|"variant"|"unknown"
    overlap: int               # 最大カード名一致数
    archetype: str | None
def classify_deck(cards: list[dict], reference: Reference) -> DeckClassification: ...
def match_deck(cards: list[dict], reference: Reference, *, variant_threshold: int = 6) -> DeckMatch: ...
```

**classify_deck のアーキタイプ判定ロジック（archetype_rules.json を参照）:**
1. siege_cards のいずれかを含む → `siege`
2. else tank_cards を含み avg_elixir ≥ beatdown_min_avg_elixir → `beatdown`
3. else bridge_spam_cards を 2枚以上含む → `bridge_spam`
4. else avg_elixir ≤ cycle_max_avg_elixir → `cycle`
5. else → `control`

**weakness_tags 判定（card_roles の tags / role を集計）:**
- `air-targeting` タグを持つカードが ≤1 → `"weak-to-air"`
- `splash` タグが 0 → `"weak-to-swarm"`
- role が `spell` のカードが 0 → `"spell-light"`
- role が `wincon` が 0 → `"no-win-condition"`、==1 → `"single-win-condition"`
- tag `building` が 0 → `"no-building-defense"`

**match_deck:** 各 template の cards(名前集合) と観測 deck の名前集合の積集合サイズ＝overlap。最大 overlap の template を採用。overlap==8→`exact`、≥variant_threshold→`variant`、それ未満→`unknown`（name/archetype は None）。

### features.py
```python
@dataclass
class MatchupRow:
    opponent_archetype: str
    mode: str                  # "ladder"|"ranked"|"other"
    wins: int
    losses: int
    draws: int
@dataclass
class LevelDeficit:
    card_name: str
    level: int
    max_level: int
    deficit: int
@dataclass
class OpponentDeck:
    deck_key: str
    archetype: str
    count: int
    wins: int                  # owner 視点
    losses: int
    sample_names: list[str]    # 代表カード名（最大8）
@dataclass
class Features:
    my_deck: DeckClassification | None
    my_deck_match: DeckMatch | None
    matchups: list[MatchupRow]
    loss_patterns: dict        # {"total_losses":int,"three_crown_losses":int,"close_losses":int}
    level_deficits: list[LevelDeficit]
    elixir_leaked: dict        # {"my_avg":float|None,"opp_avg":float|None,"delta":float|None,"sample":int}
    frequent_opponent_decks: list[OpponentDeck]
    sample_size: int
    gap_warning: bool
    modes_present: list[str]

def mode_of(battle: dict) -> str: ...
def current_deck(battles: list[dict]) -> list[dict] | None: ...   # 最新 battle_time の team.cards
def derive_matchups(battles: list[dict], reference: Reference) -> list[MatchupRow]: ...
def detect_loss_patterns(battles: list[dict]) -> dict: ...
def elixir_leaked_summary(battles: list[dict]) -> dict: ...
def detect_level_deficits(profile: dict | None, my_deck_cards: list[dict] | None) -> list[LevelDeficit]: ...
def frequent_opponent_decks(battles: list[dict], reference: Reference, *, top: int = 5) -> list[OpponentDeck]: ...
def build_features(battles: list[dict], profile: dict | None, reference: Reference) -> Features: ...
```

- `mode_of`: `is_ladder_tournament` が真、または `game_mode_name` に "Tournament"/"Challenge"/"Friendly" を含む → `"other"`。else `league_number` が int かつ ≥1 → `"ranked"`。else → `"ladder"`。
- `detect_loss_patterns`: loss の中で `team.crowns==0 and opponent.crowns==3` を three_crown_losses、`abs(team.crowns - opponent.crowns)==1` を close_losses。
- `elixir_leaked_summary`: team/opponent の `elixir_leaked` が非 None の試合のみ平均。delta = my_avg - opp_avg（両方ある時）。sample=採用試合数。
- `detect_level_deficits`: profile["cards"]（API プロフィールの所持カード, 各 {"name","level","maxLevel"}）から、my_deck_cards の各カード名の deficit = maxLevel - level（>0 のみ）。profile か my_deck_cards が None なら空配列。
- `frequent_opponent_decks`: opponent.deck_key で集計、count 降順 top 件。archetype は classify_deck(opponent.cards) の archetype。

### brief.py
```python
def render_json(features: Features) -> dict: ...     # JSON 直列化可能（dataclasses.asdict ベース）
def render_markdown(features: Features) -> str: ...   # 人間向け俯瞰＋「実測/推測」注記＋標本/ギャップ警告
```

### cli.py
```python
import click
@click.group()
def cli() -> None: ...
@cli.command()
def init() -> None: ...      # config 検証・タグ正規化表示・DB init・セットアップガイド（45.79.218.79）
@cli.command()
def fetch() -> None: ...     # profile+battlelog(+chests) 取得→store→fetch_log→件数/ギャップ報告
@cli.command()
@click.option("--json-out", type=click.Path(), default=None)
def analyze(json_out: str | None) -> None: ...  # load_battles+profile→build_features→render_* 出力
```
pyproject: `[project.scripts]` に `ra = "royale_analytics.cli:cli"`。

---

## Seed Reference Data

初期版の同梱 JSON。**テストはこの内容に依存するため、Phase 4 の T11 はこの内容を逐語で作成すること。** カード網羅は MVP の代表サブセット（2.6 Hog と Golem Beatdown を完全に含む）。シーズン毎に拡充するメンテ対象。

### card_roles.json
```json
{
  "version": "2026-06",
  "cards": {
    "Hog Rider":        {"role": "wincon",  "tags": ["building-target", "ground"]},
    "Ice Spirit":       {"role": "cycle",   "tags": ["air-targeting", "splash", "cheap"]},
    "Ice Golem":        {"role": "cycle",   "tags": ["ground", "mini-tank", "building-target"]},
    "Skeletons":        {"role": "cycle",   "tags": ["ground", "swarm", "cheap"]},
    "Musketeer":        {"role": "support", "tags": ["air-targeting", "ranged"]},
    "Fireball":         {"role": "spell",   "tags": ["air-targeting", "splash", "medium-spell"]},
    "The Log":          {"role": "spell",   "tags": ["ground", "splash", "small-spell"]},
    "Cannon":           {"role": "defense", "tags": ["building", "ground"]},
    "Golem":            {"role": "wincon",  "tags": ["ground", "tank", "building-target"]},
    "Baby Dragon":      {"role": "support", "tags": ["air", "air-targeting", "splash"]},
    "Mega Minion":      {"role": "support", "tags": ["air", "air-targeting"]},
    "Lightning":        {"role": "spell",   "tags": ["air-targeting", "splash", "big-spell"]},
    "Tornado":          {"role": "spell",   "tags": ["air-targeting", "utility"]},
    "Lumberjack":       {"role": "support", "tags": ["ground", "rage"]},
    "Barbarian Barrel": {"role": "spell",   "tags": ["ground", "splash", "small-spell"]},
    "Night Witch":      {"role": "support", "tags": ["ground", "spawner"]},
    "X-Bow":            {"role": "wincon",  "tags": ["building", "siege", "ground"]},
    "Tesla":            {"role": "defense", "tags": ["building", "air-targeting"]},
    "Archers":          {"role": "support", "tags": ["air-targeting", "ranged"]},
    "Knight":           {"role": "defense", "tags": ["ground", "mini-tank"]}
  }
}
```

### archetype_rules.json
```json
{
  "version": "2026-06",
  "tank_cards": ["Golem", "Lava Hound", "Giant", "Electro Giant", "Goblin Giant"],
  "siege_cards": ["X-Bow", "Mortar"],
  "bridge_spam_cards": ["Battle Ram", "Bandit", "Ram Rider", "Royal Ghost"],
  "cycle_max_avg_elixir": 3.0,
  "beatdown_min_avg_elixir": 3.8
}
```

### archetype_profiles.json
```json
{
  "version": "2026-06",
  "archetypes": {
    "beatdown": {
      "win_condition": "高HPタンクの裏に火力を積み、ダブルエリで一撃必殺の大型プッシュを作る",
      "strengths": ["止めにくい大型プッシュ", "ダブルエリで支配的"],
      "weaknesses": ["スロースタート", "重い committ を逆サイドで punish される", "Inferno/スウォームに弱い", "高速サイクルに先行される"]
    },
    "control": {
      "win_condition": "効率的な防衛でポジティブトレードを重ね、カウンタープッシュで chip する",
      "strengths": ["エリ効率", "テンポ管理", "適応力"],
      "weaknesses": ["直接火力が低い/遅い", "精密なタイミングが要る", "単発の overwhelming プッシュと序盤の圧に弱い", "時間切れになりやすい"]
    },
    "cycle": {
      "win_condition": "安価札で素早く回し、相手の対策より速く win condition を再投下して chip し続ける",
      "strengths": ["速度", "継続的な圧", "エリ経済"],
      "weaknesses": ["1枚の火力が低い", "ネガティブトレードに弱い", "重スプラッシュと忍耐の防衛に弱い"]
    },
    "siege": {
      "win_condition": "X-Bow/Mortar で自陣から相手タワーを攻撃し、防衛を強要して削る",
      "strengths": ["継続 chip", "多目的な建物", "反応を強要"],
      "weaknesses": ["読まれやすい", "建物の位置取りミスが致命的", "近接ブリッジ圧と高速ラッシュに弱い"]
    },
    "bridge_spam": {
      "win_condition": "ブリッジへ高速・高火力ユニットを送り、相手の overcommit を punish する",
      "strengths": ["速い不意の圧", "反応を強要"],
      "weaknesses": ["準備された防衛に止められる", "綺麗に捌かれると不利"]
    }
  }
}
```

### template_decks.json
```json
{
  "version": "2026-06",
  "decks": [
    {
      "name": "Hog 2.6 Cycle",
      "archetype": "cycle",
      "cards": ["Hog Rider", "Ice Spirit", "Ice Golem", "Skeletons", "Musketeer", "Fireball", "The Log", "Cannon"],
      "avg_elixir": 2.6,
      "win_condition": "Hog で継続的にタワーを削り、相手の Hog 対策より速くサイクルして押し切る",
      "strengths": ["高速サイクル", "ポジティブトレードしやすい", "防衛が固い"],
      "weaknesses": ["1枚あたりの火力が低い", "重いスプラッシュに弱い", "逆転の決定力が乏しい"],
      "counters": "Hog を止める建物 / 重スプラッシュ＋忍耐の防衛で削り切らせない"
    },
    {
      "name": "Golem Beatdown",
      "archetype": "beatdown",
      "cards": ["Golem", "Baby Dragon", "Mega Minion", "Lightning", "Tornado", "Lumberjack", "Barbarian Barrel", "Night Witch"],
      "avg_elixir": 4.3,
      "win_condition": "Golem を盾に支援を積み上げ、ダブルエリで巨大プッシュを通す",
      "strengths": ["圧倒的な後半火力", "ダブルエリで支配的"],
      "weaknesses": ["スロースタート", "逆サイド punish に弱い", "防衛建物が無い"],
      "counters": "序盤に逆サイドを攻めて committ を罰する / Inferno でタンクを溶かす"
    },
    {
      "name": "X-Bow 2.9",
      "archetype": "siege",
      "cards": ["X-Bow", "Tesla", "Archers", "Knight", "Ice Spirit", "Skeletons", "Fireball", "The Log"],
      "avg_elixir": 2.9,
      "win_condition": "X-Bow を自陣に置き、防衛を強要しながらタワーを削る",
      "strengths": ["継続 chip", "防衛が堅い"],
      "weaknesses": ["読まれやすい", "高速ラッシュとブリッジ圧に弱い"],
      "counters": "X-Bow をタンクで受けつつ逆サイドへ高速ラッシュ"
    }
  ]
}
```

---

## Test Factories（`tests/factories.py` — Phase 0 / T1 で作成、全テストが import）

テストのフィクスチャ一貫性のため、この内容を逐語で作成する。後続の全テストはここから import する。

```python
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
```

**store のフィールドマッピング（重要）:** 公式 API は camelCase（`maxLevel`/`elixirCost`/`evolutionLevel`/`trophyChange`/`elixirLeaked`/`leagueNumber`/`isLadderTournament`/`gameMode.name`）。`store.upsert_battles` と `load_battles` はこれを契約の snake_case（`max_level`/`elixir_cost`/`evolution_level`/`trophy_change`/`elixir_leaked`/`league_number`/`is_ladder_tournament`/`game_mode_name`）へ変換する。

---

## Tasks

### Task 1: Project scaffolding (Phase 0, commit type: chore)

Create the project skeleton and shared test infrastructure. Establishes the `src` layout, dependencies, the CLI entry point `ra`, the full exception hierarchy, and the shared `tests/factories.py` that every later test imports.

**Ordering note (read first):** `tests/factories.py` imports `from royale_analytics.decks import compute_deck_key`, but `decks.py` does not exist until Task 4. Therefore importing `tests.factories` will raise `ImportError` until Task 4 is done. To keep this task's smoke test green, **`tests/test_scaffold.py` must NOT import `tests.factories`** — it imports only `royale_analytics`. The factories file is still created verbatim in this task (later tasks depend on it), it is simply not exercised yet.

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `README.md`
- Create: `src/royale_analytics/__init__.py`
- Create: `src/royale_analytics/errors.py`
- Create: `tests/__init__.py`
- Create: `tests/factories.py`
- Test: `tests/test_scaffold.py`

**Interfaces:**
- Consumes: nothing (first task).
- Produces:
  - `royale_analytics.__version__: str` = `"0.1.0"`
  - `RoyaleAnalyticsError(Exception)`
  - `InvalidTagError(RoyaleAnalyticsError, ValueError)`
  - `BattleTimeParseError(RoyaleAnalyticsError, ValueError)`
  - `ConfigError(RoyaleAnalyticsError)`
  - `ApiError(RoyaleAnalyticsError)` with `__init__(self, message: str, *, status: int | None = None, guidance: str = "") -> None`, attributes `.status`, `.guidance`
  - `AccessDeniedError(ApiError)` (403)
  - `NotFoundError(ApiError)` (404)
  - `ThrottledError(ApiError)` (429)
  - `MaintenanceError(ApiError)` (503)
  - `ApiServerError(ApiError)` (5xx)
  - CLI entry point declared: `ra = "royale_analytics.cli:cli"` (the `cli.py` module is authored in Phase 7; the script entry just names it).

---

- [ ] **Step 1: Create `pyproject.toml`** with the full content below (src layout, setuptools backend, deps, dev extra, the `ra` script, and pytest config that puts the repo root on `pythonpath` so both `royale_analytics` and `tests.factories` import cleanly).

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "royale-analytics"
version = "0.1.0"
description = "OSS AI analytics tool for Clash Royale battle history (unofficial; not endorsed by Supercell)."
readme = "README.md"
requires-python = ">=3.11"
license = { text = "MIT" }
authors = [{ name = "royale-analytics contributors" }]
dependencies = [
    "httpx",
    "click",
    "python-dotenv",
]

[project.optional-dependencies]
dev = ["pytest"]

[project.scripts]
ra = "royale_analytics.cli:cli"

[tool.setuptools]
package-dir = { "" = "src" }

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
royale_analytics = ["reference/*.json"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 2: Create `.gitignore`** with the full content below.

```gitignore
.env
data/
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
build/
dist/
```

- [ ] **Step 3: Create `.env.example`** with the full content below (commented sample env vars; defaults match Global Constraints).

```dotenv
# Clash Royale API token (JWT from https://developer.clashroyale.com).
# Create the key with the RoyaleAPI proxy IP whitelisted: 45.79.218.79
CLASH_ROYALE_API_TOKEN=

# Your player tag. The leading '#' is optional; it is stripped automatically.
# Valid characters: 0289CGJLPQRUVY ('O' is auto-converted to '0').
CR_PLAYER_TAG=

# API base URL. Default routes through the RoyaleAPI proxy (recommended for dynamic IPs).
CR_API_BASE=https://proxy.royaleapi.dev/v1

# SQLite database path (gitignored).
RA_DB_PATH=data/royale.sqlite
```

- [ ] **Step 4: Create `README.md`** with the full content below. Note the Supercell disclaimer is reproduced verbatim from Global Constraints, and the proxy whitelist IP `45.79.218.79` is documented.

```markdown
# Royale Analytics

OSS の Clash Royale 対戦履歴 AI 分析ツール（Claude Code skill）。決定論的な Python コアが公式 API（RoyaleAPI proxy 経由）からデータを取得・蓄積・集計し、構造化した「分析ブリーフ（Markdown ＋ JSON）」を出力します。Claude Code のセッションがそのブリーフを読み、局所解に陥らない多様な次アクションを提案します。

- パッケージ: `royale_analytics`
- CLI: `ra`
- skill: `royale-analyzer`

## セットアップ

1. **API トークンを発行**: <https://developer.clashroyale.com> で無料のトークンを作成します。
2. **IP をホワイトリスト登録**: 動的 IP 環境では、トークン作成時に固定 IP `45.79.218.79`（RoyaleAPI proxy）を許可 IP として登録します。
3. **proxy 経由でリクエスト**: ベース URL を `https://proxy.royaleapi.dev/v1` にします（同じ Bearer トークンをそのまま使用）。これが既定値です。
4. **環境変数を設定**: `.env.example` を `.env` にコピーし、`CLASH_ROYALE_API_TOKEN` と `CR_PLAYER_TAG` を埋めます。

   ```sh
   cp .env.example .env
   ```

5. **インストール**:

   ```sh
   pip install -e .
   ```

## 使い方

```sh
ra init       # 設定検証・タグ正規化表示・DB 初期化・セットアップガイド
ra fetch      # プロフィール＋battlelog 取得 → 重複排除 → SQLite 追記
ra analyze    # 蓄積から特徴量算出 → 分析ブリーフ（Markdown ＋ JSON）を出力
```

## 免責

This material is unofficial and is not endorsed by Supercell. For more information see Supercell's Fan Content Policy: www.supercell.com/fan-content-policy.

## ライセンス

MIT License.
```

- [ ] **Step 5: Create `src/royale_analytics/__init__.py`** with the full content below.

```python
__version__ = "0.1.0"
```

- [ ] **Step 6: Create `src/royale_analytics/errors.py`** with the full exception hierarchy below (matches the contract exactly: `ApiError.__init__` stores `.status` and `.guidance`; all HTTP subclasses derive from `ApiError`).

```python
"""Exception hierarchy shared by all royale_analytics modules."""

from __future__ import annotations


class RoyaleAnalyticsError(Exception):
    """Base class for all royale_analytics errors."""


class InvalidTagError(RoyaleAnalyticsError, ValueError):
    """Raised when a player tag fails normalization/validation."""


class BattleTimeParseError(RoyaleAnalyticsError, ValueError):
    """Raised when a battleTime string cannot be parsed."""


class ConfigError(RoyaleAnalyticsError):
    """Raised when required configuration is missing or invalid."""


class ApiError(RoyaleAnalyticsError):
    """Base class for HTTP/API errors.

    Carries the HTTP ``status`` (when known) and actionable ``guidance``.
    """

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        guidance: str = "",
    ) -> None:
        super().__init__(message)
        self.status = status
        self.guidance = guidance


class AccessDeniedError(ApiError):
    """HTTP 403: invalid token or IP not whitelisted."""


class NotFoundError(ApiError):
    """HTTP 404: player tag not found."""


class ThrottledError(ApiError):
    """HTTP 429: rate limited (even after retries)."""


class MaintenanceError(ApiError):
    """HTTP 503: Supercell maintenance."""


class ApiServerError(ApiError):
    """HTTP 5xx: upstream server error."""
```

- [ ] **Step 7: Create `tests/__init__.py`** as an empty file (so `tests.factories` is an importable module).

```python
```

- [ ] **Step 8: Create `tests/factories.py`** with EXACTLY the content from the plan's "Test Factories" section (verbatim copy). Later tasks import `make_card`, `HOG_DECK`, `GOLEM_DECK`, `make_battle_view`, `make_raw_battle`, `make_profile` from here. It imports `compute_deck_key`, which is added in Task 4 — that is expected, and this task does not import this module.

```python
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
```

- [ ] **Step 9: Install the package (editable) so imports resolve.** Run:

```sh
pip install -e .
```

Expected: a successful build/install of `royale-analytics 0.1.0` (ending with a "Successfully installed royale-analytics-0.1.0" line). The `cli.py` module referenced by the `ra` script does not exist yet — that is fine; `pip install -e .` only records the entry point and does not import it. Invoking the `ra` command itself would fail until Phase 7, so do not run `ra` in this task.

- [ ] **Step 10: Write the failing smoke test `tests/test_scaffold.py`** with the full content below. It imports ONLY `royale_analytics` (NOT `tests.factories`), per the ordering note.

```python
from royale_analytics import __version__
from royale_analytics.errors import (
    AccessDeniedError,
    ApiError,
    RoyaleAnalyticsError,
)


def test_version_is_pinned():
    assert __version__ == "0.1.0"


def test_api_error_carries_status_and_guidance():
    err = ApiError("x", status=403, guidance="g")
    assert err.status == 403
    assert err.guidance == "g"
    assert str(err) == "x"


def test_api_error_defaults():
    err = ApiError("boom")
    assert err.status is None
    assert err.guidance == ""


def test_access_denied_is_api_error_and_base_error():
    assert issubclass(AccessDeniedError, ApiError)
    assert issubclass(AccessDeniedError, RoyaleAnalyticsError)
```

- [ ] **Step 11: Run the smoke test and expect it to FAIL first if run before Step 6/5 exist.** Since all files are created above, run it now to confirm PASS. If you authored Step 10 before Steps 5–6, the expected FAIL reason would be `ModuleNotFoundError: No module named 'royale_analytics'` (or `ImportError: cannot import name '__version__'`). Run:

```sh
pytest tests/test_scaffold.py -v
```

Expected (after Steps 5, 6, 9): all 4 tests PASS — `test_version_is_pinned`, `test_api_error_carries_status_and_guidance`, `test_api_error_defaults`, `test_access_denied_is_api_error_and_base_error` show `PASSED`.

- [ ] **Step 12: Commit this task's files only (Conventional Commit type `chore`).** Run:

```sh
git add pyproject.toml .gitignore .env.example README.md \
  src/royale_analytics/__init__.py src/royale_analytics/errors.py \
  tests/__init__.py tests/factories.py tests/test_scaffold.py
git commit -m "chore: scaffold project, package skeleton, errors, and test factories"
```

### Task 2: tags.py — normalize_tag / encode_tag

**Files:**
- Create: `src/royale_analytics/tags.py`
- Test: `tests/test_tags.py`
- Consumes (existing from Phase 0): `src/royale_analytics/errors.py` (`InvalidTagError`)

**Interfaces:**
- Consumes: `from royale_analytics.errors import InvalidTagError`
- Produces:
  - `VALID_TAG_CHARS: str = "0289CGJLPQRUVY"`
  - `def normalize_tag(raw: str) -> str` — strip `#`, uppercase, map `O`→`0`, validate against `VALID_TAG_CHARS`; raises `InvalidTagError` on empty or invalid char
  - `def encode_tag(raw: str) -> str` — `normalize_tag` then return `"%23" + tag`

Steps:

- [ ] **Step 1: Write failing test** — Create `tests/test_tags.py`:

```python
from __future__ import annotations

import pytest

from royale_analytics.errors import InvalidTagError
from royale_analytics.tags import VALID_TAG_CHARS, encode_tag, normalize_tag


def test_valid_tag_chars_constant():
    assert VALID_TAG_CHARS == "0289CGJLPQRUVY"


def test_normalize_strips_hash():
    assert normalize_tag("#C0G20PR2") == "C0G20PR2"


def test_normalize_uppercases_input():
    assert normalize_tag("#c0g20pr2") == "C0G20PR2"


def test_normalize_maps_o_to_zero():
    assert normalize_tag("#OPR") == "0PR"


def test_normalize_maps_lowercase_o_to_zero():
    assert normalize_tag("#opr") == "0PR"


def test_normalize_rejects_invalid_char_b():
    with pytest.raises(InvalidTagError):
        normalize_tag("#B0G")


def test_normalize_rejects_invalid_char_i():
    with pytest.raises(InvalidTagError):
        normalize_tag("#I0G")


def test_normalize_rejects_empty():
    with pytest.raises(InvalidTagError):
        normalize_tag("")


def test_normalize_rejects_hash_only():
    with pytest.raises(InvalidTagError):
        normalize_tag("#")


def test_encode_tag_adds_percent_23_and_normalizes():
    assert encode_tag("#c0g") == "%23C0G"
```

- [ ] **Step 2: Run it & expect FAIL** — Run:

```
pytest tests/test_tags.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'royale_analytics.tags'` (the module does not exist yet).

- [ ] **Step 3: Minimal implementation** — Create `src/royale_analytics/tags.py`:

```python
from __future__ import annotations

from royale_analytics.errors import InvalidTagError

VALID_TAG_CHARS: str = "0289CGJLPQRUVY"


def normalize_tag(raw: str) -> str:
    """Normalize a player tag: strip '#', uppercase, map 'O'->'0', validate.

    Raises InvalidTagError if the tag is empty or contains a character that is
    not in VALID_TAG_CHARS (after O->0 substitution).
    """
    tag = raw.strip().lstrip("#").upper().replace("O", "0")
    if not tag:
        raise InvalidTagError(f"Empty tag after normalization: {raw!r}")
    for ch in tag:
        if ch not in VALID_TAG_CHARS:
            raise InvalidTagError(
                f"Invalid character {ch!r} in tag {raw!r}; "
                f"valid characters are {VALID_TAG_CHARS}"
            )
    return tag


def encode_tag(raw: str) -> str:
    """Return the URL-safe tag for an API path: '%23' + normalized tag."""
    return "%23" + normalize_tag(raw)
```

- [ ] **Step 4: Run & expect PASS** — Run:

```
pytest tests/test_tags.py -v
```

Expected: PASS (all 10 tests green).

- [ ] **Step 5: Commit** — Stage only this task's files and commit:

```
git add src/royale_analytics/tags.py tests/test_tags.py
git commit -m "feat: tags normalize and encode"
```

### Task 3: battletime.py — parse_battle_time / to_utc_iso

**Files:**
- Create: `src/royale_analytics/battletime.py`
- Test: `tests/test_battletime.py`
- Consumes (existing from Phase 0): `src/royale_analytics/errors.py` (`BattleTimeParseError`)

**Interfaces:**
- Consumes: `from royale_analytics.errors import BattleTimeParseError`
- Produces:
  - `def parse_battle_time(s: str) -> datetime` — parse `%Y%m%dT%H%M%S.%fZ`, return tz-aware UTC `datetime`; raises `BattleTimeParseError` on failure
  - `def to_utc_iso(s: str) -> str` — `parse_battle_time(s).isoformat()`

Steps:

- [ ] **Step 1: Write failing test** — Create `tests/test_battletime.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from royale_analytics.battletime import parse_battle_time, to_utc_iso
from royale_analytics.errors import BattleTimeParseError


def test_parse_battle_time_returns_tz_aware_utc_datetime():
    result = parse_battle_time("20260502T021910.000Z")
    assert result == datetime(2026, 5, 2, 2, 19, 10, tzinfo=timezone.utc)


def test_parse_battle_time_is_tz_aware():
    result = parse_battle_time("20260502T021910.000Z")
    assert result.tzinfo is not None
    assert result.utcoffset() == timezone.utc.utcoffset(None)


def test_to_utc_iso_roundtrip():
    assert to_utc_iso("20260502T021910.000Z") == "2026-05-02T02:19:10+00:00"


def test_parse_battle_time_bad_input_raises():
    with pytest.raises(BattleTimeParseError):
        parse_battle_time("not-a-time")


def test_to_utc_iso_bad_input_raises():
    with pytest.raises(BattleTimeParseError):
        to_utc_iso("not-a-time")
```

- [ ] **Step 2: Run it & expect FAIL** — Run:

```
pytest tests/test_battletime.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'royale_analytics.battletime'` (the module does not exist yet).

- [ ] **Step 3: Minimal implementation** — Create `src/royale_analytics/battletime.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone

from royale_analytics.errors import BattleTimeParseError

_BATTLE_TIME_FORMAT = "%Y%m%dT%H%M%S.%fZ"


def parse_battle_time(s: str) -> datetime:
    """Parse the API battleTime string (e.g. '20260502T021910.000Z').

    Returns a timezone-aware datetime in UTC. Raises BattleTimeParseError on
    any value that does not match the '%Y%m%dT%H%M%S.%fZ' format.
    """
    try:
        naive = datetime.strptime(s, _BATTLE_TIME_FORMAT)
    except (ValueError, TypeError) as exc:
        raise BattleTimeParseError(
            f"Could not parse battleTime {s!r} "
            f"(expected format {_BATTLE_TIME_FORMAT})"
        ) from exc
    return naive.replace(tzinfo=timezone.utc)


def to_utc_iso(s: str) -> str:
    """Parse a battleTime string and return its UTC ISO-8601 representation."""
    return parse_battle_time(s).isoformat()
```

- [ ] **Step 4: Run & expect PASS** — Run:

```
pytest tests/test_battletime.py -v
```

Expected: PASS (all 5 tests green). Note `to_utc_iso("20260502T021910.000Z")` yields `"2026-05-02T02:19:10+00:00"` because the microseconds are `000000` and `isoformat()` omits them.

- [ ] **Step 5: Commit** — Stage only this task's files and commit:

```
git add src/royale_analytics/battletime.py tests/test_battletime.py
git commit -m "feat: battletime parse and utc iso"
```

### Task 4: decks.py — compute_deck_key / average_elixir

This task makes `tests/factories.py` importable for the first time, since `factories.py` does `from royale_analytics.decks import compute_deck_key`. Tests in this task import `HOG_DECK` and `GOLEM_DECK` from `tests.factories`.

**Files:**
- Create: `src/royale_analytics/decks.py`
- Test: `tests/test_decks.py`
- Consumes (existing from Phase 0): `tests/factories.py` (helpers `HOG_DECK`, `GOLEM_DECK`, `make_card`)

**Interfaces:**
- Consumes: `from tests.factories import HOG_DECK, GOLEM_DECK, make_card`
- Produces:
  - `def compute_deck_key(cards: list[dict]) -> str` — `card["id"]` ascending, unique, `,`-joined
  - `def average_elixir(cards: list[dict]) -> float` — `mean(card["elixir_cost"])` rounded to 1 decimal

Steps:

- [ ] **Step 1: Write failing test** — Create `tests/test_decks.py`:

```python
from __future__ import annotations

import random

from royale_analytics.decks import average_elixir, compute_deck_key
from tests.factories import GOLEM_DECK, HOG_DECK, make_card


def test_compute_deck_key_hog_deck():
    assert compute_deck_key(HOG_DECK) == "1,2,3,4,5,6,7,8"


def test_compute_deck_key_is_order_independent():
    shuffled = list(HOG_DECK)
    random.Random(1234).shuffle(shuffled)
    assert compute_deck_key(shuffled) == compute_deck_key(HOG_DECK)


def test_compute_deck_key_deduplicates_ids():
    cards = [make_card("A", 5, 3), make_card("B", 5, 2), make_card("C", 1, 4)]
    assert compute_deck_key(cards) == "1,5"


def test_average_elixir_hog_deck():
    assert average_elixir(HOG_DECK) == 2.6


def test_average_elixir_golem_deck():
    assert average_elixir(GOLEM_DECK) == 4.3
```

- [ ] **Step 2: Run it & expect FAIL** — Run:

```
pytest tests/test_decks.py -v
```

Expected: FAIL during collection with `ModuleNotFoundError: No module named 'royale_analytics.decks'` — raised while importing `tests/factories.py` (which itself imports `compute_deck_key`). This is the first time `tests.factories` is exercised.

- [ ] **Step 3: Minimal implementation** — Create `src/royale_analytics/decks.py`:

```python
from __future__ import annotations


def compute_deck_key(cards: list[dict]) -> str:
    """Return a stable group key for a deck: card ids ascending, unique, comma-joined.

    Order-independent (sorted) and de-duplicated so the same 8 cards always
    yield the same key regardless of the order they appear in the battlelog.
    """
    ids = sorted({card["id"] for card in cards})
    return ",".join(str(i) for i in ids)


def average_elixir(cards: list[dict]) -> float:
    """Return the mean elixir cost of the cards, rounded to one decimal place."""
    if not cards:
        return 0.0
    total = sum(card["elixir_cost"] for card in cards)
    return round(total / len(cards), 1)
```

- [ ] **Step 4: Run & expect PASS** — Run:

```
pytest tests/test_decks.py -v
```

Expected: PASS (all 5 tests green). HOG_DECK elixir = (4+1+2+1+4+4+2+3)/8 = 21/8 = 2.625 → 2.6; GOLEM_DECK = (8+4+3+6+3+4+2+4)/8 = 34/8 = 4.25 → 4.2... verify: 34/8 = 4.25, `round(4.25, 1)` in Python = 4.2 due to banker's rounding. The contract requires 4.3.

  Because `round(4.25, 1) == 4.2` (IEEE-754 / banker's rounding), the plain `round` would FAIL `test_average_elixir_golem_deck`. Fix the implementation to use decimal half-up rounding. Re-edit `src/royale_analytics/decks.py` to:

```python
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal


def compute_deck_key(cards: list[dict]) -> str:
    """Return a stable group key for a deck: card ids ascending, unique, comma-joined.

    Order-independent (sorted) and de-duplicated so the same 8 cards always
    yield the same key regardless of the order they appear in the battlelog.
    """
    ids = sorted({card["id"] for card in cards})
    return ",".join(str(i) for i in ids)


def average_elixir(cards: list[dict]) -> float:
    """Return the mean elixir cost of the cards, rounded to one decimal place.

    Uses half-up rounding (not banker's rounding) so 4.25 -> 4.3, matching the
    template_decks reference values.
    """
    if not cards:
        return 0.0
    mean = Decimal(sum(card["elixir_cost"] for card in cards)) / Decimal(len(cards))
    return float(mean.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
```

- [ ] **Step 5: Re-run & expect PASS** — Run:

```
pytest tests/test_decks.py -v
```

Expected: PASS (all 5 tests green). Now `average_elixir(GOLEM_DECK) == 4.3` and `average_elixir(HOG_DECK) == 2.6`.

- [ ] **Step 6: Commit** — Stage only this task's files and commit:

```
git add src/royale_analytics/decks.py tests/test_decks.py
git commit -m "feat: decks deck_key and average_elixir"
```

### Task 5: config.py — Config dataclass + load_config(env)

**Files:**
- Create: `src/royale_analytics/config.py`
- Test: `tests/test_config.py`
- Consumes (existing from Phase 0): `src/royale_analytics/errors.py` (`ConfigError`); `src/royale_analytics/tags.py` (`normalize_tag`, from Task 2)

**Interfaces:**
- Consumes: `from royale_analytics.errors import ConfigError`; `from royale_analytics.tags import normalize_tag`
- Produces:
  - `@dataclass(frozen=True) class Config` with fields `token: str`, `base_url: str`, `player_tag: str` (normalized, no `#`), `db_path: str`
  - `def load_config(env: Mapping[str, str] | None = None) -> Config` — defaults `base_url="https://proxy.royaleapi.dev/v1"`, `db_path="data/royale.sqlite"`; reads `CLASH_ROYALE_API_TOKEN`, `CR_PLAYER_TAG`, `CR_API_BASE`, `RA_DB_PATH`; missing token or player_tag raises `ConfigError`; when `env=None`, calls `load_dotenv()` then uses `os.environ`.

Steps:

- [ ] **Step 1: Write failing test** — Create `tests/test_config.py` (env is always passed explicitly; never rely on real environment or `.env`):

```python
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
```

- [ ] **Step 2: Run it & expect FAIL** — Run:

```
pytest tests/test_config.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'royale_analytics.config'` (the module does not exist yet).

- [ ] **Step 3: Minimal implementation** — Create `src/royale_analytics/config.py`:

```python
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
```

- [ ] **Step 4: Run & expect PASS** — Run:

```
pytest tests/test_config.py -v
```

Expected: PASS (all 7 tests green).

- [ ] **Step 5: Commit** — Stage only this task's files and commit:

```
git add src/royale_analytics/config.py tests/test_config.py
git commit -m "feat: config dataclass and load_config"
```

### Task 6: api_client.py — ApiClient core (_get, auth, error mapping, 429 retry).

**Files:**
- Create: `src/royale_analytics/api_client.py`
- Test: `tests/test_api_client_core.py`

**Interfaces:**
- Consumes:
  - `from royale_analytics.errors import ApiError, AccessDeniedError, NotFoundError, ThrottledError, MaintenanceError, ApiServerError` (Phase 0 / T1) — `ApiError.__init__(message: str, *, status: int | None = None, guidance: str = "")` with attributes `.status`, `.guidance`.
  - `httpx` (runtime dep), `time` (stdlib).
- Produces:
  - `class ApiClient` with `def __init__(self, token: str, base_url: str, *, client: "httpx.Client | None" = None, max_retries: int = 2, sleep: "Callable[[float], None]" = time.sleep) -> None`
  - internal `def _get(self, path: str) -> Any` — adds header `Authorization: Bearer <token>`; maps `403→AccessDeniedError`, `404→NotFoundError`, `503→MaintenanceError`, `500..599→ApiServerError`, other non-2xx → `ApiError`; sets `.status` and an actionable `.guidance`; on `429` reads header `x-ratelimit-retry-after` (microseconds), converts to seconds, calls `self.sleep(seconds)`, retries up to `max_retries`, then raises `ThrottledError`.

---

- [ ] **Step 1: Write the failing test file for the core (`_get`) behaviors.**

This test uses `httpx.MockTransport` so no network is touched. Each test builds a `httpx.Client` with a handler and injects it via the `client=` parameter. The 429 test injects a fake sleep that captures its arguments.

Create `tests/test_api_client_core.py`:

```python
from __future__ import annotations

import httpx
import pytest

from royale_analytics.api_client import ApiClient
from royale_analytics.errors import (
    AccessDeniedError,
    ApiServerError,
    MaintenanceError,
    NotFoundError,
    ThrottledError,
)

BASE_URL = "https://proxy.royaleapi.dev/v1"


def make_client(handler, *, max_retries=2, sleep=None):
    """Build an ApiClient backed by an httpx.MockTransport handler (no network)."""
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(base_url=BASE_URL, transport=transport)
    kwargs = {"client": http_client, "max_retries": max_retries}
    if sleep is not None:
        kwargs["sleep"] = sleep
    return ApiClient("tok-123", BASE_URL, **kwargs)


def test_get_returns_parsed_json_and_sends_bearer_header():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers.get("Authorization")
        return httpx.Response(200, json={"tag": "#ME", "name": "Me"})

    client = make_client(handler)
    body = client._get("/players/%23ME")

    assert body == {"tag": "#ME", "name": "Me"}
    assert seen["authorization"] == "Bearer tok-123"


def test_403_raises_access_denied_with_status_and_guidance():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"reason": "accessDenied"})

    client = make_client(handler)
    with pytest.raises(AccessDeniedError) as exc:
        client._get("/players/%23ME")

    assert exc.value.status == 403
    assert exc.value.guidance != ""
    assert "45.79.218.79" in exc.value.guidance


def test_404_raises_not_found_with_status_and_guidance():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"reason": "notFound"})

    client = make_client(handler)
    with pytest.raises(NotFoundError) as exc:
        client._get("/players/%23ME")

    assert exc.value.status == 404
    assert exc.value.guidance != ""
    assert "tag" in exc.value.guidance.lower()


def test_503_raises_maintenance_with_status_and_guidance():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"reason": "inMaintenance"})

    client = make_client(handler)
    with pytest.raises(MaintenanceError) as exc:
        client._get("/players/%23ME")

    assert exc.value.status == 503
    assert exc.value.guidance != ""
    assert "maintenance" in exc.value.guidance.lower()


def test_500_raises_api_server_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"reason": "serverError"})

    client = make_client(handler)
    with pytest.raises(ApiServerError) as exc:
        client._get("/cards")

    assert exc.value.status == 500


def test_one_429_then_200_succeeds_and_sleep_called_with_converted_seconds():
    slept = []
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            # 1_500_000 microseconds -> 1.5 seconds
            return httpx.Response(
                429,
                headers={"x-ratelimit-retry-after": "1500000"},
                json={"reason": "throttled"},
            )
        return httpx.Response(200, json={"ok": True})

    client = make_client(handler, max_retries=2, sleep=lambda s: slept.append(s))
    body = client._get("/cards")

    assert body == {"ok": True}
    assert slept == [1.5]
    assert calls["n"] == 2


def test_persistent_429_raises_throttled():
    slept = []

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            headers={"x-ratelimit-retry-after": "500000"},
            json={"reason": "throttled"},
        )

    client = make_client(handler, max_retries=2, sleep=lambda s: slept.append(s))
    with pytest.raises(ThrottledError) as exc:
        client._get("/cards")

    assert exc.value.status == 429
    assert exc.value.guidance != ""
    # 500_000 microseconds -> 0.5 seconds, slept once per retry (max_retries=2)
    assert slept == [0.5, 0.5]
```

- [ ] **Step 2: Run the test and expect FAIL (module does not exist yet).**

```
pytest tests/test_api_client_core.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'royale_analytics.api_client'` (the file has not been created), so all collected tests error out at import time.

- [ ] **Step 3: Implement the minimal `ApiClient` core in `src/royale_analytics/api_client.py`.**

Full file:

```python
from __future__ import annotations

import time
from typing import Any, Callable

import httpx

from royale_analytics.errors import (
    AccessDeniedError,
    ApiError,
    ApiServerError,
    MaintenanceError,
    NotFoundError,
    ThrottledError,
)
from royale_analytics.tags import encode_tag

_ACCESS_DENIED_GUIDANCE = (
    "Access denied (403). Your token is invalid or the request IP is not "
    "whitelisted. When using the RoyaleAPI proxy, whitelist the IP "
    "45.79.218.79 on developer.clashroyale.com; for a direct connection, "
    "re-issue the key with your current IP."
)
_NOT_FOUND_GUIDANCE = (
    "Not found (404). Check the player tag (the letter 'O' must be the digit "
    "'0', and the '#' is not part of the tag)."
)
_MAINTENANCE_GUIDANCE = (
    "Service in maintenance (503). Supercell is performing maintenance; "
    "retry later."
)
_THROTTLED_GUIDANCE = (
    "Throttled (429). The rate limit was exceeded and retries were exhausted; "
    "wait and try again."
)
_SERVER_ERROR_GUIDANCE = (
    "Server error from the API. This is usually transient; retry later."
)


class ApiClient:
    def __init__(
        self,
        token: str,
        base_url: str,
        *,
        client: "httpx.Client | None" = None,
        max_retries: int = 2,
        sleep: "Callable[[float], None]" = time.sleep,
    ) -> None:
        self.token = token
        self.base_url = base_url
        self.client = client if client is not None else httpx.Client(base_url=base_url)
        self.max_retries = max_retries
        self.sleep = sleep

    def _get(self, path: str) -> Any:
        headers = {"Authorization": f"Bearer {self.token}"}
        attempts = 0
        while True:
            response = self.client.get(path, headers=headers)
            status = response.status_code

            if 200 <= status < 300:
                return response.json()

            if status == 429:
                retry_after_us = response.headers.get("x-ratelimit-retry-after")
                seconds = float(retry_after_us) / 1_000_000 if retry_after_us else 0.0
                if attempts < self.max_retries:
                    attempts += 1
                    self.sleep(seconds)
                    continue
                raise ThrottledError(
                    "Throttled after retries.",
                    status=429,
                    guidance=_THROTTLED_GUIDANCE,
                )

            if status == 403:
                raise AccessDeniedError(
                    "Access denied.", status=403, guidance=_ACCESS_DENIED_GUIDANCE
                )
            if status == 404:
                raise NotFoundError(
                    "Not found.", status=404, guidance=_NOT_FOUND_GUIDANCE
                )
            if status == 503:
                raise MaintenanceError(
                    "In maintenance.", status=503, guidance=_MAINTENANCE_GUIDANCE
                )
            if 500 <= status < 600:
                raise ApiServerError(
                    f"Server error ({status}).",
                    status=status,
                    guidance=_SERVER_ERROR_GUIDANCE,
                )
            raise ApiError(
                f"Unexpected API response ({status}).",
                status=status,
                guidance="Unexpected response from the API.",
            )
```

Note: the `encode_tag` import is included now because the endpoint methods in Task 7 live in this same file and depend on it; it is also harmless to the core. The endpoint methods (`get_player` etc.) are added in Task 7.

- [ ] **Step 4: Run the test and expect PASS.**

```
pytest tests/test_api_client_core.py -v
```

Expected: PASS — 7 tests pass. `test_get_returns_parsed_json_and_sends_bearer_header` confirms the Bearer header and parsed JSON; the 403/404/503/500 tests confirm the correct exception type, `.status`, and non-empty actionable `.guidance`; `test_one_429_then_200_succeeds_and_sleep_called_with_converted_seconds` confirms `self.sleep` was called with `1.5` (1_500_000 µs → s) and the retry then succeeded; `test_persistent_429_raises_throttled` confirms `ThrottledError` after exhausting `max_retries`.

- [ ] **Step 5: Commit (this task's files only).**

```
git add src/royale_analytics/api_client.py tests/test_api_client_core.py
git commit -m "feat: add ApiClient core with auth, error mapping, and 429 retry"
```

### Task 7: api_client.py — endpoint methods (get_player/get_battlelog/get_upcoming_chests/get_cards).

**Files:**
- Modify: `src/royale_analytics/api_client.py`
- Test: `tests/test_api_client_endpoints.py`

**Interfaces:**
- Consumes:
  - `ApiClient._get(self, path: str) -> Any` (Task 6).
  - `from royale_analytics.tags import encode_tag` (Phase 1 / T2) — `encode_tag(raw)` returns `"%23" + normalized_tag`.
  - `httpx`.
- Produces (on `ApiClient`):
  - `def get_player(self, tag: str) -> dict` → `_get("/players/" + encode_tag(tag))`
  - `def get_battlelog(self, tag: str) -> list[dict]` → `_get("/players/" + encode_tag(tag) + "/battlelog")`
  - `def get_upcoming_chests(self, tag: str) -> dict` → `_get("/players/" + encode_tag(tag) + "/upcomingchests")`
  - `def get_cards(self) -> dict` → `_get("/cards")`

---

- [ ] **Step 1: Write the failing test file for the endpoint methods.**

These tests use a captured-request handler so the request `path` can be asserted equal to the expected `%23`-encoded path, and confirm the parsed body shape (battlelog → list, others → dict). For tag `"#ABC"`, `encode_tag` yields `"%23ABC"`.

Create `tests/test_api_client_endpoints.py`:

```python
from __future__ import annotations

import httpx

from royale_analytics.api_client import ApiClient

BASE_URL = "https://proxy.royaleapi.dev/v1"


def make_client_capturing(captured, response):
    """Build an ApiClient whose MockTransport records the request and returns `response`."""

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        return response

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(base_url=BASE_URL, transport=transport)
    return ApiClient("tok-123", BASE_URL, client=http_client)


def test_get_player_uses_encoded_path_and_returns_dict():
    captured = {}
    client = make_client_capturing(
        captured, httpx.Response(200, json={"tag": "#ABC", "name": "Me"})
    )
    body = client.get_player("#ABC")

    assert captured["path"] == "/v1/players/%23ABC"
    assert body == {"tag": "#ABC", "name": "Me"}


def test_get_battlelog_uses_encoded_path_and_returns_list():
    captured = {}
    client = make_client_capturing(
        captured, httpx.Response(200, json=[{"type": "PvP"}, {"type": "PvP"}])
    )
    body = client.get_battlelog("#ABC")

    assert captured["path"] == "/v1/players/%23ABC/battlelog"
    assert isinstance(body, list)
    assert body == [{"type": "PvP"}, {"type": "PvP"}]


def test_get_upcoming_chests_uses_encoded_path_and_returns_dict():
    captured = {}
    client = make_client_capturing(
        captured, httpx.Response(200, json={"items": [{"name": "Silver Chest"}]})
    )
    body = client.get_upcoming_chests("#ABC")

    assert captured["path"] == "/v1/players/%23ABC/upcomingchests"
    assert body == {"items": [{"name": "Silver Chest"}]}


def test_get_cards_uses_cards_path_and_returns_dict():
    captured = {}
    client = make_client_capturing(
        captured, httpx.Response(200, json={"items": [{"name": "Hog Rider"}]})
    )
    body = client.get_cards()

    assert captured["path"] == "/v1/cards"
    assert body == {"items": [{"name": "Hog Rider"}]}


def test_get_player_normalizes_o_to_zero_in_path():
    captured = {}
    client = make_client_capturing(
        captured, httpx.Response(200, json={"tag": "#0AB"})
    )
    # 'O' normalizes to '0' via encode_tag; '#' is stripped then re-added as %23.
    client.get_player("#OAB")

    assert captured["path"] == "/v1/players/%230AB"
```

Note on `request.url.path`: httpx prepends the client `base_url` path component (`/v1`), so the asserted paths include the `/v1` prefix. The `%23` encoding is preserved by httpx because `encode_tag` already produced a percent-encoded literal in the path segment.

- [ ] **Step 2: Run the test and expect FAIL (methods not defined yet).**

```
pytest tests/test_api_client_endpoints.py -v
```

Expected: FAIL — `AttributeError: 'ApiClient' object has no attribute 'get_player'` (and likewise for `get_battlelog`, `get_upcoming_chests`, `get_cards`), since Task 6 only implemented `__init__` and `_get`.

- [ ] **Step 3: Add the four endpoint methods to `src/royale_analytics/api_client.py`.**

Append these methods to the `ApiClient` class (immediately after `_get`). The `encode_tag` import is already present from Task 6:

```python
    def get_player(self, tag: str) -> dict:
        return self._get("/players/" + encode_tag(tag))

    def get_battlelog(self, tag: str) -> list[dict]:
        return self._get("/players/" + encode_tag(tag) + "/battlelog")

    def get_upcoming_chests(self, tag: str) -> dict:
        return self._get("/players/" + encode_tag(tag) + "/upcomingchests")

    def get_cards(self) -> dict:
        return self._get("/cards")
```

For clarity, the resulting full `src/royale_analytics/api_client.py` is:

```python
from __future__ import annotations

import time
from typing import Any, Callable

import httpx

from royale_analytics.errors import (
    AccessDeniedError,
    ApiError,
    ApiServerError,
    MaintenanceError,
    NotFoundError,
    ThrottledError,
)
from royale_analytics.tags import encode_tag

_ACCESS_DENIED_GUIDANCE = (
    "Access denied (403). Your token is invalid or the request IP is not "
    "whitelisted. When using the RoyaleAPI proxy, whitelist the IP "
    "45.79.218.79 on developer.clashroyale.com; for a direct connection, "
    "re-issue the key with your current IP."
)
_NOT_FOUND_GUIDANCE = (
    "Not found (404). Check the player tag (the letter 'O' must be the digit "
    "'0', and the '#' is not part of the tag)."
)
_MAINTENANCE_GUIDANCE = (
    "Service in maintenance (503). Supercell is performing maintenance; "
    "retry later."
)
_THROTTLED_GUIDANCE = (
    "Throttled (429). The rate limit was exceeded and retries were exhausted; "
    "wait and try again."
)
_SERVER_ERROR_GUIDANCE = (
    "Server error from the API. This is usually transient; retry later."
)


class ApiClient:
    def __init__(
        self,
        token: str,
        base_url: str,
        *,
        client: "httpx.Client | None" = None,
        max_retries: int = 2,
        sleep: "Callable[[float], None]" = time.sleep,
    ) -> None:
        self.token = token
        self.base_url = base_url
        self.client = client if client is not None else httpx.Client(base_url=base_url)
        self.max_retries = max_retries
        self.sleep = sleep

    def _get(self, path: str) -> Any:
        headers = {"Authorization": f"Bearer {self.token}"}
        attempts = 0
        while True:
            response = self.client.get(path, headers=headers)
            status = response.status_code

            if 200 <= status < 300:
                return response.json()

            if status == 429:
                retry_after_us = response.headers.get("x-ratelimit-retry-after")
                seconds = float(retry_after_us) / 1_000_000 if retry_after_us else 0.0
                if attempts < self.max_retries:
                    attempts += 1
                    self.sleep(seconds)
                    continue
                raise ThrottledError(
                    "Throttled after retries.",
                    status=429,
                    guidance=_THROTTLED_GUIDANCE,
                )

            if status == 403:
                raise AccessDeniedError(
                    "Access denied.", status=403, guidance=_ACCESS_DENIED_GUIDANCE
                )
            if status == 404:
                raise NotFoundError(
                    "Not found.", status=404, guidance=_NOT_FOUND_GUIDANCE
                )
            if status == 503:
                raise MaintenanceError(
                    "In maintenance.", status=503, guidance=_MAINTENANCE_GUIDANCE
                )
            if 500 <= status < 600:
                raise ApiServerError(
                    f"Server error ({status}).",
                    status=status,
                    guidance=_SERVER_ERROR_GUIDANCE,
                )
            raise ApiError(
                f"Unexpected API response ({status}).",
                status=status,
                guidance="Unexpected response from the API.",
            )

    def get_player(self, tag: str) -> dict:
        return self._get("/players/" + encode_tag(tag))

    def get_battlelog(self, tag: str) -> list[dict]:
        return self._get("/players/" + encode_tag(tag) + "/battlelog")

    def get_upcoming_chests(self, tag: str) -> dict:
        return self._get("/players/" + encode_tag(tag) + "/upcomingchests")

    def get_cards(self) -> dict:
        return self._get("/cards")
```

- [ ] **Step 4: Run the endpoint tests (and the core tests for regression) and expect PASS.**

```
pytest tests/test_api_client_endpoints.py tests/test_api_client_core.py -v
```

Expected: PASS — all endpoint tests confirm the request path equals the exact `%23`-encoded path (`/v1/players/%23ABC`, `/v1/players/%23ABC/battlelog`, `/v1/players/%23ABC/upcomingchests`, `/v1/cards`), that `get_battlelog` returns a `list` and the others a `dict`, and that `encode_tag` normalization (`O→0`) is reflected in the path (`/v1/players/%230AB`). The Task 6 core tests still pass (no regression).

- [ ] **Step 5: Commit (this task's files only).**

```
git add src/royale_analytics/api_client.py tests/test_api_client_endpoints.py
git commit -m "feat: add ApiClient endpoint methods for player, battlelog, chests, and cards"
```

### Task 8: store.py — schema & init

**Files:**
- Create: `src/royale_analytics/store.py`
- Test: `tests/test_store_schema.py`

**Interfaces:**
- Consumes: nothing (first store task; uses stdlib `sqlite3`, `os`).
- Produces:
  ```python
  class Store:
      def __init__(self, db_path: str) -> None: ...   # makedirs(parent, exist_ok=True); self.conn = sqlite3.connect(db_path)
      def init_schema(self) -> None: ...              # CREATE TABLE IF NOT EXISTS for battles/battle_sides/battle_cards/profile_snapshots/fetch_log
      def close(self) -> None: ...
  ```
  Tables per spec Data Model. `battles` carries `UNIQUE(player_tag, battle_time, opponent_tag)`.

- [ ] **Step 1: Write the failing test.**
  Create `tests/test_store_schema.py`:
  ```python
  from __future__ import annotations

  from royale_analytics.store import Store


  EXPECTED_TABLES = {
      "battles",
      "battle_sides",
      "battle_cards",
      "profile_snapshots",
      "fetch_log",
  }


  def _table_names(store: Store) -> set[str]:
      rows = store.conn.execute(
          "SELECT name FROM sqlite_master WHERE type='table'"
      ).fetchall()
      return {r[0] for r in rows}


  def test_init_schema_creates_all_five_tables():
      store = Store(":memory:")
      store.init_schema()
      assert EXPECTED_TABLES <= _table_names(store)


  def test_init_schema_is_idempotent():
      store = Store(":memory:")
      store.init_schema()
      # Calling twice must not raise (IF NOT EXISTS).
      store.init_schema()
      assert EXPECTED_TABLES <= _table_names(store)


  def test_battles_has_unique_constraint(tmp_path):
      db = tmp_path / "sub" / "royale.sqlite"
      store = Store(str(db))
      store.init_schema()
      # Inserting the same (player_tag, battle_time, opponent_tag) twice with
      # INSERT (not OR IGNORE) must violate the UNIQUE constraint.
      import sqlite3

      store.conn.execute(
          "INSERT INTO battles (player_tag, opponent_tag, battle_time) "
          "VALUES (?, ?, ?)",
          ("ME", "OPP", "2026-05-02T02:19:10+00:00"),
      )
      try:
          store.conn.execute(
              "INSERT INTO battles (player_tag, opponent_tag, battle_time) "
              "VALUES (?, ?, ?)",
              ("ME", "OPP", "2026-05-02T02:19:10+00:00"),
          )
          raised = False
      except sqlite3.IntegrityError:
          raised = True
      assert raised


  def test_init_creates_parent_dirs(tmp_path):
      db = tmp_path / "nested" / "deeper" / "royale.sqlite"
      store = Store(str(db))
      store.init_schema()
      assert db.parent.is_dir()
      assert db.exists()
  ```

- [ ] **Step 2: Run it & expect FAIL.**
  ```
  pytest tests/test_store_schema.py -v
  ```
  Expected: FAIL with `ModuleNotFoundError: No module named 'royale_analytics.store'` (the module does not exist yet).

- [ ] **Step 3: Minimal implementation.**
  Create `src/royale_analytics/store.py`:
  ```python
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
  ```

- [ ] **Step 4: Run & expect PASS.**
  ```
  pytest tests/test_store_schema.py -v
  ```
  Expected: PASS (5 tests: all-five-tables, idempotent, unique-constraint, two parent-dir/memory cases). `:memory:` has no parent so `os.path.dirname(":memory:")` is `""` and `makedirs` is skipped.

- [ ] **Step 5: Commit.**
  ```
  git add src/royale_analytics/store.py tests/test_store_schema.py
  git commit -m "feat: store schema and init"
  ```

### Task 9: store.py — write path

**Files:**
- Modify: `src/royale_analytics/store.py`
- Test: `tests/test_store_write.py`

**Interfaces:**
- Consumes:
  - `royale_analytics.battletime.to_utc_iso(s: str) -> str` (Task 3).
  - `royale_analytics.decks.compute_deck_key(cards: list[dict]) -> str` (Task 4).
  - `Store.__init__` / `Store.init_schema` (Task 8).
  - `tests.factories.make_raw_battle`, `make_profile`, `HOG_DECK`, `GOLEM_DECK`.
- Produces:
  ```python
  class Store:
      def upsert_battles(self, player_tag: str, battlelog: list[dict]) -> int: ...
      def save_profile_snapshot(self, player_tag: str, profile: dict) -> None: ...
      def record_fetch(self, player_tag: str, new_battles: int, gap_suspected: bool) -> None: ...
  ```
  `upsert_battles` returns the count of **newly inserted** battles. Card field mapping camelCase→snake_case: `maxLevel→max_level`, `elixirCost→elixir_cost`, `evolutionLevel→evolution_level` (default `None`).

- [ ] **Step 1: Write the failing test (insert + idempotency + result derivation).**
  Create `tests/test_store_write.py`:
  ```python
  from __future__ import annotations

  import json

  from royale_analytics.store import Store
  from tests.factories import GOLEM_DECK, HOG_DECK, make_profile, make_raw_battle


  def _new_store() -> Store:
      store = Store(":memory:")
      store.init_schema()
      return store


  def test_upsert_two_distinct_battles_returns_two():
      store = _new_store()
      battlelog = [
          make_raw_battle(
              battle_time="20260502T021910.000Z",
              team_cards=HOG_DECK,
              opp_cards=GOLEM_DECK,
              team_crowns=2,
              opp_crowns=1,
          ),
          make_raw_battle(
              battle_time="20260502T031910.000Z",
              team_cards=HOG_DECK,
              opp_cards=GOLEM_DECK,
              team_crowns=0,
              opp_crowns=2,
              opponent_tag="#OPP2",
          ),
      ]
      assert store.upsert_battles("#ME", battlelog) == 2


  def test_upsert_is_idempotent():
      store = _new_store()
      battlelog = [
          make_raw_battle(
              team_cards=HOG_DECK,
              opp_cards=GOLEM_DECK,
              team_crowns=2,
              opp_crowns=1,
          ),
      ]
      assert store.upsert_battles("#ME", battlelog) == 1
      # Re-inserting the same list adds nothing.
      assert store.upsert_battles("#ME", battlelog) == 0
  ```

- [ ] **Step 2: Run it & expect FAIL.**
  ```
  pytest tests/test_store_write.py -v
  ```
  Expected: FAIL with `AttributeError: 'Store' object has no attribute 'upsert_battles'`.

- [ ] **Step 3: Implement upsert_battles (and helpers).**
  Edit `src/royale_analytics/store.py` — add imports at top and the methods on `Store`.

  Replace the import block at the top:
  ```python
  from __future__ import annotations

  import json
  import os
  import sqlite3
  from datetime import datetime, timezone

  from royale_analytics.battletime import to_utc_iso
  from royale_analytics.decks import compute_deck_key
  from royale_analytics.errors import BattleTimeParseError
  ```

  Add a module-level helper before the `Store` class (after `_SCHEMA`):
  ```python
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
  ```

  Add these methods to the `Store` class (after `close`):
  ```python
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
  ```

- [ ] **Step 4: Run & expect PASS (insert + idempotency).**
  ```
  pytest tests/test_store_write.py -v
  ```
  Expected: PASS for `test_upsert_two_distinct_battles_returns_two` and `test_upsert_is_idempotent`.

- [ ] **Step 5: Add tests for result derivation, card mapping, profile, fetch_log.**
  Append to `tests/test_store_write.py`:
  ```python
  def test_loss_result_for_zero_vs_two_crowns():
      store = _new_store()
      store.upsert_battles(
          "#ME",
          [
              make_raw_battle(
                  team_cards=HOG_DECK,
                  opp_cards=GOLEM_DECK,
                  team_crowns=0,
                  opp_crowns=2,
              )
          ],
      )
      row = store.conn.execute("SELECT result FROM battles").fetchone()
      assert row[0] == "loss"


  def test_battle_cards_has_sixteen_snake_case_rows():
      store = _new_store()
      store.upsert_battles(
          "#ME",
          [
              make_raw_battle(
                  team_cards=HOG_DECK,
                  opp_cards=GOLEM_DECK,
                  team_crowns=2,
                  opp_crowns=1,
              )
          ],
      )
      rows = store.conn.execute(
          "SELECT card_name, max_level, elixir_cost, evolution_level "
          "FROM battle_cards"
      ).fetchall()
      assert len(rows) == 16  # 8 cards x 2 sides
      # snake_case fields are populated (elixir_cost present, not null).
      for card_name, max_level, elixir_cost, _evo in rows:
          assert isinstance(card_name, str) and card_name
          assert max_level is not None
          assert elixir_cost is not None
      # Hog Rider costs 4 elixir per the HOG_DECK factory.
      hog = store.conn.execute(
          "SELECT elixir_cost FROM battle_cards WHERE card_name='Hog Rider'"
      ).fetchone()
      assert hog[0] == 4


  def test_save_profile_snapshot_writes_row():
      store = _new_store()
      profile = make_profile({"Hog Rider": (11, 14)})
      store.save_profile_snapshot("#ME", profile)
      count = store.conn.execute(
          "SELECT COUNT(*) FROM profile_snapshots WHERE player_tag='#ME'"
      ).fetchone()[0]
      assert count == 1


  def test_record_fetch_stores_gap_as_int():
      store = _new_store()
      store.record_fetch("#ME", new_battles=3, gap_suspected=True)
      store.record_fetch("#ME", new_battles=0, gap_suspected=False)
      rows = store.conn.execute(
          "SELECT new_battles, gap_suspected FROM fetch_log ORDER BY id"
      ).fetchall()
      assert rows[0] == (3, 1)
      assert rows[1] == (0, 0)
  ```

- [ ] **Step 6: Run & expect PASS (all write-path behaviors).**
  ```
  pytest tests/test_store_write.py -v
  ```
  Expected: PASS for all 6 tests. Note `gap_suspected` is stored as `1`/`0` (the `1 if gap_suspected else 0` mapping), and `elixir_cost` for Hog Rider is `4`.

- [ ] **Step 7: Write the failing test for skip-on-unparseable-battleTime.**
  Append to `tests/test_store_write.py`:
  ```python
  def test_upsert_skips_unparseable_battletime(tmp_path):
      from royale_analytics.store import Store
      from tests.factories import make_raw_battle, HOG_DECK, GOLEM_DECK
      s = Store(str(tmp_path / "db.sqlite"))
      s.init_schema()
      good = make_raw_battle(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                             team_crowns=1, opp_crowns=0, opponent_tag="#A")
      bad = make_raw_battle(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                            team_crowns=0, opp_crowns=1, opponent_tag="#B")
      bad["battleTime"] = "not-a-time"
      assert s.upsert_battles("#ME", [good, bad]) == 1
  ```

- [ ] **Step 8: Run it.**
  ```
  pytest tests/test_store.py::test_upsert_skips_unparseable_battletime -v
  ```
  Expected: PASS (the bad battle is skipped, the good one is stored).

- [ ] **Step 9: Commit.**
  ```
  git add src/royale_analytics/store.py tests/test_store_write.py
  git commit -m "feat: store write path with idempotent upsert"
  ```

### Task 10: store.py — read path

**Files:**
- Modify: `src/royale_analytics/store.py`
- Test: `tests/test_store_read.py`

**Interfaces:**
- Consumes:
  - `Store.upsert_battles` / `save_profile_snapshot` (Task 9).
  - `tests.factories.make_raw_battle`, `make_profile`, `make_battle_view`, `HOG_DECK`, `GOLEM_DECK`.
- Produces:
  ```python
  class Store:
      def load_battles(self, player_tag: str) -> list[dict]: ...      # battle view dicts, ordered by battle_time
      def get_latest_profile(self, player_tag: str) -> dict | None: ...  # parsed raw_json of newest snapshot, or None
  ```
  Each battle view dict matches the contract's battle view shape: top-level `battle_time`, `game_mode_name`, `is_ladder_tournament` (bool), `league_number`, `result`; and `team`/`opponent` each with snake_case `cards`, `crowns`, `trophy_change`, `elixir_leaked`, `deck_key`, plus `tag`/`name`.

- [ ] **Step 1: Write the failing test.**
  Create `tests/test_store_read.py`:
  ```python
  from __future__ import annotations

  from royale_analytics.store import Store
  from tests.factories import (
      GOLEM_DECK,
      HOG_DECK,
      make_battle_view,
      make_profile,
      make_raw_battle,
  )


  def _new_store() -> Store:
      store = Store(":memory:")
      store.init_schema()
      return store


  def test_load_battles_returns_view_shaped_dicts():
      store = _new_store()
      store.upsert_battles(
          "#ME",
          [
              make_raw_battle(
                  battle_time="20260502T021910.000Z",
                  team_cards=HOG_DECK,
                  opp_cards=GOLEM_DECK,
                  team_crowns=2,
                  opp_crowns=1,
              ),
              make_raw_battle(
                  battle_time="20260502T031910.000Z",
                  team_cards=HOG_DECK,
                  opp_cards=GOLEM_DECK,
                  team_crowns=0,
                  opp_crowns=2,
                  opponent_tag="#OPP2",
              ),
          ],
      )
      battles = store.load_battles("#ME")
      assert len(battles) == 2

      first = battles[0]
      # Top-level shape matches make_battle_view-style dict.
      reference = make_battle_view(
          team_cards=HOG_DECK,
          opp_cards=GOLEM_DECK,
          team_crowns=2,
          opp_crowns=1,
      )
      assert set(reference.keys()) <= set(first.keys())
      assert set(reference["team"].keys()) <= set(first["team"].keys())

      # snake_case card fields are reconstructed.
      assert first["team"]["cards"][0]["elixir_cost"] is not None
      assert "max_level" in first["team"]["cards"][0]
      # is_ladder_tournament is a real bool (not 0/1 int).
      assert isinstance(first["is_ladder_tournament"], bool)
      # result reflects crowns (first battle is a win for team).
      assert first["result"] == "win"
      # opponent deck_key is present.
      assert first["opponent"]["deck_key"]
      assert first["team"]["crowns"] == 2
      assert first["opponent"]["crowns"] == 1


  def test_load_battles_ordered_by_battle_time():
      store = _new_store()
      store.upsert_battles(
          "#ME",
          [
              make_raw_battle(
                  battle_time="20260502T031910.000Z",
                  team_cards=HOG_DECK,
                  opp_cards=GOLEM_DECK,
                  team_crowns=0,
                  opp_crowns=2,
                  opponent_tag="#OPP2",
              ),
              make_raw_battle(
                  battle_time="20260502T021910.000Z",
                  team_cards=HOG_DECK,
                  opp_cards=GOLEM_DECK,
                  team_crowns=2,
                  opp_crowns=1,
              ),
          ],
      )
      battles = store.load_battles("#ME")
      times = [b["battle_time"] for b in battles]
      assert times == sorted(times)
  ```

- [ ] **Step 2: Run it & expect FAIL.**
  ```
  pytest tests/test_store_read.py -v
  ```
  Expected: FAIL with `AttributeError: 'Store' object has no attribute 'load_battles'`.

- [ ] **Step 3: Implement load_battles.**
  Add these methods to the `Store` class in `src/royale_analytics/store.py` (after `record_fetch`):
  ```python
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
  ```

- [ ] **Step 4: Run & expect PASS (load_battles).**
  ```
  pytest tests/test_store_read.py -v
  ```
  Expected: PASS for `test_load_battles_returns_view_shaped_dicts` and `test_load_battles_ordered_by_battle_time`. `is_ladder_tournament` is a `bool` (via `bool(...)`), cards carry snake_case `elixir_cost`/`max_level`, and `result == "win"`.

- [ ] **Step 5: Add get_latest_profile tests.**
  Append to `tests/test_store_read.py`:
  ```python
  def test_get_latest_profile_returns_none_when_empty():
      store = _new_store()
      assert store.get_latest_profile("#ME") is None


  def test_get_latest_profile_returns_most_recent():
      store = _new_store()
      first = make_profile({"Hog Rider": (10, 14)})
      first["trophies"] = 5900
      second = make_profile({"Hog Rider": (11, 14)})
      second["trophies"] = 6100
      store.save_profile_snapshot("#ME", first)
      store.save_profile_snapshot("#ME", second)
      latest = store.get_latest_profile("#ME")
      assert latest is not None
      # Most recently saved snapshot wins (highest id / fetched_at).
      assert latest["trophies"] == 6100
      assert latest["cards"][0]["level"] == 11
  ```

- [ ] **Step 6: Implement get_latest_profile.**
  Add this method to the `Store` class (after `_load_side`):
  ```python
      def get_latest_profile(self, player_tag: str) -> dict | None:
          row = self.conn.execute(
              "SELECT raw_json FROM profile_snapshots WHERE player_tag = ? "
              "ORDER BY id DESC LIMIT 1",
              (player_tag,),
          ).fetchone()
          if row is None:
              return None
          return json.loads(row[0])
  ```

- [ ] **Step 7: Run & expect PASS (full read path).**
  ```
  pytest tests/test_store_read.py -v
  ```
  Expected: PASS for all 4 tests. `get_latest_profile` returns `None` on an empty table and the newest snapshot (`trophies == 6100`, `cards[0].level == 11`) otherwise. Ordering by `id DESC` reflects insertion recency even if `fetched_at` ties at second precision.

- [ ] **Step 8: Run the whole store suite & commit.**
  ```
  pytest tests/test_store_schema.py tests/test_store_write.py tests/test_store_read.py -v
  ```
  Expected: PASS (all store tests green).
  ```
  git add src/royale_analytics/store.py tests/test_store_read.py
  git commit -m "feat: store read path reconstructing battle views"
  ```

### Task 11: reference data + loader

Create the four reference JSON files (verbatim from the plan's Seed Reference Data) and implement `reference.py` with the `Reference` dataclass and `load_reference()`.

**Files:**
- Create: `src/royale_analytics/reference/card_roles.json`
- Create: `src/royale_analytics/reference/archetype_rules.json`
- Create: `src/royale_analytics/reference/archetype_profiles.json`
- Create: `src/royale_analytics/reference/template_decks.json`
- Create: `src/royale_analytics/reference.py`
- Test: `tests/test_reference.py`

**Interfaces:**
- Consumes: (nothing — first module of Phase 4; only stdlib `json`, `dataclasses`, `pathlib`)
- Produces:
  ```python
  @dataclass
  class Reference:
      card_roles: dict       # {"version":..., "cards": {name: {"role":str,"tags":[str]}}}
      archetype_rules: dict
      archetype_profiles: dict
      template_decks: list   # [{name,archetype,cards,avg_elixir,win_condition,strengths,weaknesses,counters}]
  def load_reference(ref_dir: str | Path | None = None) -> Reference: ...
  ```

Steps:

- [ ] **Step 1: Create the four reference JSON files verbatim from the plan.**

  `src/royale_analytics/reference/card_roles.json`:
  ```json
  {
    "version": "2026-06",
    "cards": {
      "Hog Rider":        {"role": "wincon",  "tags": ["building-target", "ground"]},
      "Ice Spirit":       {"role": "cycle",   "tags": ["air-targeting", "splash", "cheap"]},
      "Ice Golem":        {"role": "cycle",   "tags": ["ground", "mini-tank", "building-target"]},
      "Skeletons":        {"role": "cycle",   "tags": ["ground", "swarm", "cheap"]},
      "Musketeer":        {"role": "support", "tags": ["air-targeting", "ranged"]},
      "Fireball":         {"role": "spell",   "tags": ["air-targeting", "splash", "medium-spell"]},
      "The Log":          {"role": "spell",   "tags": ["ground", "splash", "small-spell"]},
      "Cannon":           {"role": "defense", "tags": ["building", "ground"]},
      "Golem":            {"role": "wincon",  "tags": ["ground", "tank", "building-target"]},
      "Baby Dragon":      {"role": "support", "tags": ["air", "air-targeting", "splash"]},
      "Mega Minion":      {"role": "support", "tags": ["air", "air-targeting"]},
      "Lightning":        {"role": "spell",   "tags": ["air-targeting", "splash", "big-spell"]},
      "Tornado":          {"role": "spell",   "tags": ["air-targeting", "utility"]},
      "Lumberjack":       {"role": "support", "tags": ["ground", "rage"]},
      "Barbarian Barrel": {"role": "spell",   "tags": ["ground", "splash", "small-spell"]},
      "Night Witch":      {"role": "support", "tags": ["ground", "spawner"]},
      "X-Bow":            {"role": "wincon",  "tags": ["building", "siege", "ground"]},
      "Tesla":            {"role": "defense", "tags": ["building", "air-targeting"]},
      "Archers":          {"role": "support", "tags": ["air-targeting", "ranged"]},
      "Knight":           {"role": "defense", "tags": ["ground", "mini-tank"]}
    }
  }
  ```

  `src/royale_analytics/reference/archetype_rules.json`:
  ```json
  {
    "version": "2026-06",
    "tank_cards": ["Golem", "Lava Hound", "Giant", "Electro Giant", "Goblin Giant"],
    "siege_cards": ["X-Bow", "Mortar"],
    "bridge_spam_cards": ["Battle Ram", "Bandit", "Ram Rider", "Royal Ghost"],
    "cycle_max_avg_elixir": 3.0,
    "beatdown_min_avg_elixir": 3.8
  }
  ```

  `src/royale_analytics/reference/archetype_profiles.json`:
  ```json
  {
    "version": "2026-06",
    "archetypes": {
      "beatdown": {
        "win_condition": "高HPタンクの裏に火力を積み、ダブルエリで一撃必殺の大型プッシュを作る",
        "strengths": ["止めにくい大型プッシュ", "ダブルエリで支配的"],
        "weaknesses": ["スロースタート", "重い committ を逆サイドで punish される", "Inferno/スウォームに弱い", "高速サイクルに先行される"]
      },
      "control": {
        "win_condition": "効率的な防衛でポジティブトレードを重ね、カウンタープッシュで chip する",
        "strengths": ["エリ効率", "テンポ管理", "適応力"],
        "weaknesses": ["直接火力が低い/遅い", "精密なタイミングが要る", "単発の overwhelming プッシュと序盤の圧に弱い", "時間切れになりやすい"]
      },
      "cycle": {
        "win_condition": "安価札で素早く回し、相手の対策より速く win condition を再投下して chip し続ける",
        "strengths": ["速度", "継続的な圧", "エリ経済"],
        "weaknesses": ["1枚の火力が低い", "ネガティブトレードに弱い", "重スプラッシュと忍耐の防衛に弱い"]
      },
      "siege": {
        "win_condition": "X-Bow/Mortar で自陣から相手タワーを攻撃し、防衛を強要して削る",
        "strengths": ["継続 chip", "多目的な建物", "反応を強要"],
        "weaknesses": ["読まれやすい", "建物の位置取りミスが致命的", "近接ブリッジ圧と高速ラッシュに弱い"]
      },
      "bridge_spam": {
        "win_condition": "ブリッジへ高速・高火力ユニットを送り、相手の overcommit を punish する",
        "strengths": ["速い不意の圧", "反応を強要"],
        "weaknesses": ["準備された防衛に止められる", "綺麗に捌かれると不利"]
      }
    }
  }
  ```

  `src/royale_analytics/reference/template_decks.json`:
  ```json
  {
    "version": "2026-06",
    "decks": [
      {
        "name": "Hog 2.6 Cycle",
        "archetype": "cycle",
        "cards": ["Hog Rider", "Ice Spirit", "Ice Golem", "Skeletons", "Musketeer", "Fireball", "The Log", "Cannon"],
        "avg_elixir": 2.6,
        "win_condition": "Hog で継続的にタワーを削り、相手の Hog 対策より速くサイクルして押し切る",
        "strengths": ["高速サイクル", "ポジティブトレードしやすい", "防衛が固い"],
        "weaknesses": ["1枚あたりの火力が低い", "重いスプラッシュに弱い", "逆転の決定力が乏しい"],
        "counters": "Hog を止める建物 / 重スプラッシュ＋忍耐の防衛で削り切らせない"
      },
      {
        "name": "Golem Beatdown",
        "archetype": "beatdown",
        "cards": ["Golem", "Baby Dragon", "Mega Minion", "Lightning", "Tornado", "Lumberjack", "Barbarian Barrel", "Night Witch"],
        "avg_elixir": 4.3,
        "win_condition": "Golem を盾に支援を積み上げ、ダブルエリで巨大プッシュを通す",
        "strengths": ["圧倒的な後半火力", "ダブルエリで支配的"],
        "weaknesses": ["スロースタート", "逆サイド punish に弱い", "防衛建物が無い"],
        "counters": "序盤に逆サイドを攻めて committ を罰する / Inferno でタンクを溶かす"
      },
      {
        "name": "X-Bow 2.9",
        "archetype": "siege",
        "cards": ["X-Bow", "Tesla", "Archers", "Knight", "Ice Spirit", "Skeletons", "Fireball", "The Log"],
        "avg_elixir": 2.9,
        "win_condition": "X-Bow を自陣に置き、防衛を強要しながらタワーを削る",
        "strengths": ["継続 chip", "防衛が堅い"],
        "weaknesses": ["読まれやすい", "高速ラッシュとブリッジ圧に弱い"],
        "counters": "X-Bow をタンクで受けつつ逆サイドへ高速ラッシュ"
      }
    ]
  }
  ```

- [ ] **Step 2: Write the failing test for `load_reference`.**

  Create `tests/test_reference.py`:
  ```python
  from __future__ import annotations

  from royale_analytics.reference import Reference, load_reference


  def test_load_reference_returns_reference():
      ref = load_reference()
      assert isinstance(ref, Reference)


  def test_card_roles_hog_rider_is_wincon():
      ref = load_reference()
      assert ref.card_roles["cards"]["Hog Rider"]["role"] == "wincon"


  def test_archetype_rules_siege_cards():
      ref = load_reference()
      assert ref.archetype_rules["siege_cards"] == ["X-Bow", "Mortar"]


  def test_template_decks_has_at_least_three_with_hog_cycle():
      ref = load_reference()
      assert len(ref.template_decks) >= 3
      names = [d["name"] for d in ref.template_decks]
      assert "Hog 2.6 Cycle" in names
  ```

- [ ] **Step 3: Run the test and expect FAIL.**

  ```
  pytest tests/test_reference.py -v
  ```
  Expected: FAIL with `ModuleNotFoundError: No module named 'royale_analytics.reference'` (the `reference.py` module does not exist yet — note the `reference/` directory has no `__init__.py`, so importing `royale_analytics.reference` resolves to `reference.py` once created).

- [ ] **Step 4: Implement `reference.py`.**

  Create `src/royale_analytics/reference.py`:
  ```python
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
  ```

- [ ] **Step 5: Run the test and expect PASS.**

  ```
  pytest tests/test_reference.py -v
  ```
  Expected: PASS (4 passed). `Reference` instance returned, `card_roles["cards"]["Hog Rider"]["role"] == "wincon"`, `archetype_rules["siege_cards"] == ["X-Bow", "Mortar"]`, 3 template decks including `"Hog 2.6 Cycle"`.

- [ ] **Step 6: Commit (this task's files only).**

  ```
  git add src/royale_analytics/reference/card_roles.json src/royale_analytics/reference/archetype_rules.json src/royale_analytics/reference/archetype_profiles.json src/royale_analytics/reference/template_decks.json src/royale_analytics/reference.py tests/test_reference.py
  git commit -m "feat: add reference data files and load_reference loader"
  ```

### Task 12: classify.py — classify_deck

Implement `classify_deck` per the contract's archetype logic and weakness-tag rules, with `role_counts`, `avg_elixir` (via `decks.average_elixir`), and `card_names`.

**Files:**
- Create: `src/royale_analytics/classify.py`
- Modify: (none)
- Test: `tests/test_classify_deck.py`

**Interfaces:**
- Consumes:
  ```python
  from royale_analytics.decks import average_elixir   # (cards: list[dict]) -> float
  from royale_analytics.reference import Reference     # .card_roles, .archetype_rules
  ```
- Produces:
  ```python
  @dataclass
  class DeckClassification:
      archetype: str             # "cycle"|"beatdown"|"siege"|"bridge_spam"|"control"
      avg_elixir: float
      role_counts: dict          # {"wincon":int,"support":int,"defense":int,"cycle":int,"spell":int}
      weakness_tags: list[str]
      card_names: list[str]
  def classify_deck(cards: list[dict], reference: Reference) -> DeckClassification: ...
  ```

Steps:

- [ ] **Step 1: Write the failing test for archetype + avg_elixir + role_counts (HOG_DECK).**

  Create `tests/test_classify_deck.py`:
  ```python
  from __future__ import annotations

  from royale_analytics.classify import DeckClassification, classify_deck
  from royale_analytics.reference import load_reference
  from tests.factories import GOLEM_DECK, HOG_DECK


  def test_hog_deck_is_cycle():
      ref = load_reference()
      result = classify_deck(HOG_DECK, ref)
      assert isinstance(result, DeckClassification)
      assert result.archetype == "cycle"
      assert result.avg_elixir == 2.6


  def test_hog_deck_role_counts_one_wincon():
      ref = load_reference()
      result = classify_deck(HOG_DECK, ref)
      assert result.role_counts["wincon"] == 1
  ```

- [ ] **Step 2: Run the test and expect FAIL.**

  ```
  pytest tests/test_classify_deck.py -v
  ```
  Expected: FAIL with `ModuleNotFoundError: No module named 'royale_analytics.classify'`.

- [ ] **Step 3: Implement `classify_deck` (and `DeckClassification`) in `classify.py`.**

  Create `src/royale_analytics/classify.py`:
  ```python
  from __future__ import annotations

  from dataclasses import dataclass

  from royale_analytics.decks import average_elixir
  from royale_analytics.reference import Reference

  _ROLE_KEYS = ("wincon", "support", "defense", "cycle", "spell")


  @dataclass
  class DeckClassification:
      archetype: str
      avg_elixir: float
      role_counts: dict
      weakness_tags: list[str]
      card_names: list[str]


  def _card_roles(cards: list[dict], reference: Reference) -> list[str]:
      roles_table = reference.card_roles["cards"]
      out = []
      for c in cards:
          entry = roles_table.get(c["name"])
          out.append(entry["role"] if entry else "")
      return out


  def _card_tags(cards: list[dict], reference: Reference) -> list[list[str]]:
      roles_table = reference.card_roles["cards"]
      out = []
      for c in cards:
          entry = roles_table.get(c["name"])
          out.append(list(entry["tags"]) if entry else [])
      return out


  def _archetype(cards: list[dict], avg: float, reference: Reference) -> str:
      rules = reference.archetype_rules
      names = {c["name"] for c in cards}

      if names & set(rules["siege_cards"]):
          return "siege"
      if (names & set(rules["tank_cards"])) and avg >= rules["beatdown_min_avg_elixir"]:
          return "beatdown"
      if len(names & set(rules["bridge_spam_cards"])) >= 2:
          return "bridge_spam"
      if avg <= rules["cycle_max_avg_elixir"]:
          return "cycle"
      return "control"


  def _role_counts(roles: list[str]) -> dict:
      counts = {key: 0 for key in _ROLE_KEYS}
      for role in roles:
          if role in counts:
              counts[role] += 1
      return counts


  def _weakness_tags(roles: list[str], tags: list[list[str]]) -> list[str]:
      flat_tags = [t for card_tags in tags for t in card_tags]
      air_targeting = sum(1 for card_tags in tags if "air-targeting" in card_tags)
      splash = sum(1 for t in flat_tags if t == "splash")
      building = sum(1 for t in flat_tags if t == "building")
      spell_count = sum(1 for role in roles if role == "spell")
      wincon_count = sum(1 for role in roles if role == "wincon")

      out: list[str] = []
      if air_targeting <= 1:
          out.append("weak-to-air")
      if splash == 0:
          out.append("weak-to-swarm")
      if spell_count == 0:
          out.append("spell-light")
      if wincon_count == 0:
          out.append("no-win-condition")
      elif wincon_count == 1:
          out.append("single-win-condition")
      if building == 0:
          out.append("no-building-defense")
      return out


  def classify_deck(cards: list[dict], reference: Reference) -> DeckClassification:
      avg = average_elixir(cards)
      roles = _card_roles(cards, reference)
      tags = _card_tags(cards, reference)
      return DeckClassification(
          archetype=_archetype(cards, avg, reference),
          avg_elixir=avg,
          role_counts=_role_counts(roles),
          weakness_tags=_weakness_tags(roles, tags),
          card_names=[c["name"] for c in cards],
      )
  ```

- [ ] **Step 4: Run the test and expect PASS.**

  ```
  pytest tests/test_classify_deck.py -v
  ```
  Expected: PASS (2 passed). HOG_DECK avg_elixir = mean(4,1,2,1,4,4,2,3)=2.625 → round 1dp = 2.6; no siege/tank/bridge_spam cards and 2.6 ≤ 3.0 → `cycle`; one `wincon` (Hog Rider).

- [ ] **Step 5: Add tests for weakness_tags (HOG_DECK air rule + GOLEM_DECK building rule).**

  Append to `tests/test_classify_deck.py`:
  ```python
  def test_hog_deck_weakness_tags():
      ref = load_reference()
      result = classify_deck(HOG_DECK, ref)
      # Hog deck has 3 air-targeting cards (Ice Spirit, Musketeer, Fireball)
      assert "weak-to-air" not in result.weakness_tags
      assert "single-win-condition" in result.weakness_tags


  def test_golem_deck_is_beatdown_no_building_defense():
      ref = load_reference()
      result = classify_deck(GOLEM_DECK, ref)
      assert result.archetype == "beatdown"
      assert "no-building-defense" in result.weakness_tags
  ```

- [ ] **Step 6: Run the new tests and expect PASS.**

  ```
  pytest tests/test_classify_deck.py -v
  ```
  Expected: PASS (4 passed). HOG_DECK air-targeting count = 3 (Ice Spirit, Musketeer, Fireball) > 1 → no `weak-to-air`; exactly one wincon → `single-win-condition`. GOLEM_DECK: contains Golem (tank) and avg = mean(8,4,3,6,3,4,2,4)=4.25 ≥ 3.8 → `beatdown`; no card carries the `building` tag → `no-building-defense`.

- [ ] **Step 7: Commit (this task's files only).**

  ```
  git add src/royale_analytics/classify.py tests/test_classify_deck.py
  git commit -m "feat: add classify_deck with archetype and weakness-tag logic"
  ```

### Task 13: classify.py — match_deck

Implement fuzzy `match_deck` by card-name set overlap against `template_decks`: `overlap==8 → "exact"`, `>= variant_threshold → "variant"`, else `"unknown"` (name/archetype None).

**Files:**
- Create: (none)
- Modify: `src/royale_analytics/classify.py`
- Test: `tests/test_match_deck.py`

**Interfaces:**
- Consumes:
  ```python
  from royale_analytics.reference import Reference   # .template_decks
  ```
- Produces:
  ```python
  @dataclass
  class DeckMatch:
      name: str | None
      confidence: str            # "exact"|"variant"|"unknown"
      overlap: int               # 最大カード名一致数
      archetype: str | None
  def match_deck(cards: list[dict], reference: Reference, *, variant_threshold: int = 6) -> DeckMatch: ...
  ```

Steps:

- [ ] **Step 1: Write the failing test for exact + variant + unknown.**

  Create `tests/test_match_deck.py`:
  ```python
  from __future__ import annotations

  from royale_analytics.classify import DeckMatch, match_deck
  from royale_analytics.reference import load_reference
  from tests.factories import HOG_DECK, make_card


  def test_exact_match_hog():
      ref = load_reference()
      result = match_deck(HOG_DECK, ref)
      assert isinstance(result, DeckMatch)
      assert result.confidence == "exact"
      assert result.name == "Hog 2.6 Cycle"
      assert result.overlap == 8
      assert result.archetype == "cycle"


  def test_variant_match_hog_six_of_eight():
      ref = load_reference()
      # Replace two HOG_DECK cards (Cannon, Skeletons) with off-deck cards.
      variant = [
          c for c in HOG_DECK if c["name"] not in ("Cannon", "Skeletons")
      ] + [
          make_card("Archers", 8, 3, rarity="common"),
          make_card("Knight", 4, 3, rarity="common"),
      ]
      result = match_deck(variant, ref)
      assert result.confidence == "variant"
      assert result.name == "Hog 2.6 Cycle"
      assert result.overlap == 6
      assert result.archetype == "cycle"


  def test_unknown_match_unrelated_cards():
      ref = load_reference()
      unrelated = [
          make_card("Goblin Barrel", 101, 3),
          make_card("Princess", 102, 3),
          make_card("Goblin Gang", 103, 3),
          make_card("Inferno Tower", 104, 5),
          make_card("Rocket", 105, 6),
          make_card("Bats", 106, 2),
          make_card("Tesla Trooper", 107, 4),
          make_card("Dart Goblin", 108, 3),
      ]
      result = match_deck(unrelated, ref)
      assert result.confidence == "unknown"
      assert result.name is None
      assert result.archetype is None
  ```

- [ ] **Step 2: Run the test and expect FAIL.**

  ```
  pytest tests/test_match_deck.py -v
  ```
  Expected: FAIL with `ImportError: cannot import name 'DeckMatch' from 'royale_analytics.classify'` (`DeckMatch` and `match_deck` are not defined yet).

- [ ] **Step 3: Add `DeckMatch` and `match_deck` to `classify.py`.**

  Add the import is already present (`Reference`). Append the dataclass after `DeckClassification` and the function at the end of `src/royale_analytics/classify.py`:

  Add this dataclass immediately after the `DeckClassification` dataclass:
  ```python
  @dataclass
  class DeckMatch:
      name: str | None
      confidence: str
      overlap: int
      archetype: str | None
  ```

  Append this function at the end of the file:
  ```python
  def match_deck(
      cards: list[dict], reference: Reference, *, variant_threshold: int = 6
  ) -> DeckMatch:
      observed = {c["name"] for c in cards}

      best_template: dict | None = None
      best_overlap = -1
      for template in reference.template_decks:
          overlap = len(observed & set(template["cards"]))
          if overlap > best_overlap:
              best_overlap = overlap
              best_template = template

      if best_template is None:
          return DeckMatch(name=None, confidence="unknown", overlap=0, archetype=None)

      if best_overlap == 8:
          confidence = "exact"
      elif best_overlap >= variant_threshold:
          confidence = "variant"
      else:
          confidence = "unknown"

      if confidence == "unknown":
          return DeckMatch(
              name=None, confidence="unknown", overlap=best_overlap, archetype=None
          )

      return DeckMatch(
          name=best_template["name"],
          confidence=confidence,
          overlap=best_overlap,
          archetype=best_template["archetype"],
      )
  ```

- [ ] **Step 4: Run the test and expect PASS.**

  ```
  pytest tests/test_match_deck.py -v
  ```
  Expected: PASS (3 passed). HOG_DECK overlaps the "Hog 2.6 Cycle" template on all 8 names → `exact`. The variant (Cannon/Skeletons swapped for Archers/Knight, which are not in the Hog template) overlaps 6/8 → `variant`, name `"Hog 2.6 Cycle"`, overlap 6. The unrelated 8 cards overlap 0 with every template → below `variant_threshold` → `unknown`, name/archetype `None`.

- [ ] **Step 5: Run the full classify test suite to confirm no regression.**

  ```
  pytest tests/test_classify_deck.py tests/test_match_deck.py -v
  ```
  Expected: PASS (7 passed total — 4 from Task 12, 3 from Task 13).

- [ ] **Step 6: Commit (this task's files only).**

  ```
  git add src/royale_analytics/classify.py tests/test_match_deck.py
  git commit -m "feat: add match_deck fuzzy template matching"
  ```

### Task 14: features.py — mode_of, current_deck, derive_matchups

**Files:**
- Create: `src/royale_analytics/features.py`
- Test: `tests/test_features.py`

**Interfaces:**
- Consumes: `classify_deck(cards: list[dict], reference: Reference) -> DeckClassification` (from `classify.py`), `load_reference(ref_dir=None) -> Reference` (from `reference.py`), `make_battle_view`, `make_card`, `HOG_DECK`, `GOLEM_DECK` (from `tests.factories`)
- Produces:
  - `@dataclass MatchupRow(opponent_archetype: str, mode: str, wins: int, losses: int, draws: int)`
  - `def mode_of(battle: dict) -> str` returns `"ladder" | "ranked" | "other"`
  - `def current_deck(battles: list[dict]) -> list[dict] | None`
  - `def derive_matchups(battles: list[dict], reference: Reference) -> list[MatchupRow]`

- [ ] **Step 1: Write failing test for `mode_of`**

Create `tests/test_features.py`:
```python
from __future__ import annotations

from royale_analytics.features import (
    MatchupRow,
    current_deck,
    derive_matchups,
    mode_of,
)
from royale_analytics.reference import load_reference
from tests.factories import GOLEM_DECK, HOG_DECK, make_battle_view


def test_mode_of_ladder():
    battle = make_battle_view(
        team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
        team_crowns=1, opp_crowns=0,
        mode_fields={"game_mode_name": "Ladder",
                     "is_ladder_tournament": False, "league_number": None},
    )
    assert mode_of(battle) == "ladder"


def test_mode_of_ranked_by_league_number():
    battle = make_battle_view(
        team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
        team_crowns=1, opp_crowns=0,
        mode_fields={"game_mode_name": "Ranked",
                     "is_ladder_tournament": False, "league_number": 5},
    )
    assert mode_of(battle) == "ranked"


def test_mode_of_other_when_ladder_tournament():
    battle = make_battle_view(
        team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
        team_crowns=1, opp_crowns=0,
        mode_fields={"game_mode_name": "Some Challenge",
                     "is_ladder_tournament": True, "league_number": None},
    )
    assert mode_of(battle) == "other"
```

- [ ] **Step 2: Run the test, expect FAIL**

```
pytest tests/test_features.py::test_mode_of_ladder tests/test_features.py::test_mode_of_ranked_by_league_number tests/test_features.py::test_mode_of_other_when_ladder_tournament -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'royale_analytics.features'` (the module does not exist yet).

- [ ] **Step 3: Minimal implementation of `features.py` (dataclasses + `mode_of` + `current_deck` + `derive_matchups`)**

Create `src/royale_analytics/features.py`:
```python
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .battletime import parse_battle_time
from .classify import DeckClassification, classify_deck
from .reference import Reference

_OTHER_MODE_TOKENS = ("Tournament", "Challenge", "Friendly")


@dataclass
class MatchupRow:
    opponent_archetype: str
    mode: str
    wins: int
    losses: int
    draws: int


def mode_of(battle: dict) -> str:
    game_mode_name = battle.get("game_mode_name") or ""
    if battle.get("is_ladder_tournament") or any(
        token in game_mode_name for token in _OTHER_MODE_TOKENS
    ):
        return "other"
    league_number = battle.get("league_number")
    if isinstance(league_number, int) and league_number >= 1:
        return "ranked"
    return "ladder"


def current_deck(battles: list[dict]) -> list[dict] | None:
    if not battles:
        return None
    latest = max(battles, key=lambda b: parse_battle_time(b["battle_time"]))
    return latest["team"]["cards"]


def derive_matchups(battles: list[dict], reference: Reference) -> list[MatchupRow]:
    tallies: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"wins": 0, "losses": 0, "draws": 0}
    )
    for battle in battles:
        opp_classification: DeckClassification = classify_deck(
            battle["opponent"]["cards"], reference
        )
        key = (opp_classification.archetype, mode_of(battle))
        result = battle["result"]
        if result == "win":
            tallies[key]["wins"] += 1
        elif result == "loss":
            tallies[key]["losses"] += 1
        else:
            tallies[key]["draws"] += 1
    rows = [
        MatchupRow(
            opponent_archetype=archetype,
            mode=mode,
            wins=counts["wins"],
            losses=counts["losses"],
            draws=counts["draws"],
        )
        for (archetype, mode), counts in tallies.items()
    ]
    rows.sort(key=lambda r: (r.opponent_archetype, r.mode))
    return rows
```

Note: `parse_battle_time` consumes the UTC ISO string that `make_battle_view` produces (e.g. `"2026-05-02T02:19:10+00:00"`); `datetime.fromisoformat` handles that form, so `parse_battle_time` must accept it.

- [ ] **Step 4: Run the `mode_of` tests, expect PASS**

```
pytest tests/test_features.py::test_mode_of_ladder tests/test_features.py::test_mode_of_ranked_by_league_number tests/test_features.py::test_mode_of_other_when_ladder_tournament -v
```
Expected: 3 passed.

- [ ] **Step 5: Write failing test for `current_deck` on empty list**

Append to `tests/test_features.py`:
```python
def test_current_deck_empty_returns_none():
    assert current_deck([]) is None


def test_current_deck_returns_most_recent_team_cards():
    older = make_battle_view(
        team_cards=GOLEM_DECK, opp_cards=HOG_DECK,
        team_crowns=0, opp_crowns=3,
        battle_time="2026-05-01T00:00:00+00:00",
    )
    newer = make_battle_view(
        team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
        team_crowns=3, opp_crowns=0,
        battle_time="2026-05-02T00:00:00+00:00",
    )
    deck = current_deck([older, newer])
    assert deck == HOG_DECK
```

- [ ] **Step 6: Run the `current_deck` tests, expect PASS**

```
pytest tests/test_features.py::test_current_deck_empty_returns_none tests/test_features.py::test_current_deck_returns_most_recent_team_cards -v
```
Expected: 2 passed (the implementation from Step 3 already covers these).

- [ ] **Step 7: Write failing test for `derive_matchups`**

Append to `tests/test_features.py`:
```python
def test_derive_matchups_groups_by_opponent_archetype_and_mode():
    ref = load_reference()
    battles = [
        # loss vs Golem/beatdown opponent (ladder)
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=0, opp_crowns=3,
            battle_time="2026-05-01T00:00:00+00:00",
        ),
        # loss vs Golem/beatdown opponent (ladder)
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=1, opp_crowns=2,
            battle_time="2026-05-01T01:00:00+00:00",
        ),
        # win vs Hog/cycle opponent (ladder)
        make_battle_view(
            team_cards=GOLEM_DECK, opp_cards=HOG_DECK,
            team_crowns=3, opp_crowns=0,
            battle_time="2026-05-01T02:00:00+00:00",
        ),
    ]
    rows = derive_matchups(battles, ref)

    beatdown = next(
        r for r in rows
        if r.opponent_archetype == "beatdown" and r.mode == "ladder"
    )
    assert beatdown.losses == 2
    assert beatdown.wins == 0
    assert beatdown.draws == 0

    cycle = next(
        r for r in rows
        if r.opponent_archetype == "cycle" and r.mode == "ladder"
    )
    assert cycle.wins == 1
    assert cycle.losses == 0
    assert cycle.draws == 0
```

- [ ] **Step 8: Run the `derive_matchups` test, expect PASS**

```
pytest tests/test_features.py::test_derive_matchups_groups_by_opponent_archetype_and_mode -v
```
Expected: 1 passed. The GOLEM_DECK classifies as `beatdown` (contains tank `Golem`, avg elixir 4.3 ≥ 3.8) and HOG_DECK as `cycle` (avg elixir 2.6 ≤ 3.0, no tank/siege), per the seed reference data.

- [ ] **Step 9: Run the full test file, then commit**

```
pytest tests/test_features.py -v
```
Expected: all tests in the file pass.

```
git add src/royale_analytics/features.py tests/test_features.py
git commit -m "feat: matchups (mode_of, current_deck, derive_matchups)"
```

### Task 15: features.py — detect_loss_patterns, elixir_leaked_summary

**Files:**
- Modify: `src/royale_analytics/features.py`
- Test: `tests/test_features.py`

**Interfaces:**
- Consumes: `make_battle_view`, `HOG_DECK`, `GOLEM_DECK` (from `tests.factories`)
- Produces:
  - `def detect_loss_patterns(battles: list[dict]) -> dict` returning `{"total_losses": int, "three_crown_losses": int, "close_losses": int}`
  - `def elixir_leaked_summary(battles: list[dict]) -> dict` returning `{"my_avg": float | None, "opp_avg": float | None, "delta": float | None, "sample": int}`

- [ ] **Step 1: Write failing test for `detect_loss_patterns`**

Append to `tests/test_features.py`:
```python
from royale_analytics.features import (  # noqa: E402
    detect_loss_patterns,
    elixir_leaked_summary,
)


def test_detect_loss_patterns_counts_three_crown_and_close():
    battles = [
        # three-crown loss (0-3): also counts? abs diff == 3, so NOT close
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=0, opp_crowns=3,
        ),
        # close loss (1-2): abs diff == 1
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=1, opp_crowns=2,
        ),
        # a win (not a loss)
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=3, opp_crowns=0,
        ),
    ]
    patterns = detect_loss_patterns(battles)
    assert patterns == {
        "total_losses": 2,
        "three_crown_losses": 1,
        "close_losses": 1,
    }
```

- [ ] **Step 2: Run the test, expect FAIL**

```
pytest tests/test_features.py::test_detect_loss_patterns_counts_three_crown_and_close -v
```
Expected: FAIL with `ImportError: cannot import name 'detect_loss_patterns' from 'royale_analytics.features'` (function not yet defined).

- [ ] **Step 3: Implement `detect_loss_patterns`**

Append to `src/royale_analytics/features.py`:
```python
def detect_loss_patterns(battles: list[dict]) -> dict:
    total_losses = 0
    three_crown_losses = 0
    close_losses = 0
    for battle in battles:
        if battle["result"] != "loss":
            continue
        total_losses += 1
        team_crowns = battle["team"]["crowns"]
        opp_crowns = battle["opponent"]["crowns"]
        if team_crowns == 0 and opp_crowns == 3:
            three_crown_losses += 1
        if abs(team_crowns - opp_crowns) == 1:
            close_losses += 1
    return {
        "total_losses": total_losses,
        "three_crown_losses": three_crown_losses,
        "close_losses": close_losses,
    }
```

- [ ] **Step 4: Run the `detect_loss_patterns` test, expect PASS**

```
pytest tests/test_features.py::test_detect_loss_patterns_counts_three_crown_and_close -v
```
Expected: 1 passed.

- [ ] **Step 5: Write failing test for `elixir_leaked_summary`**

Append to `tests/test_features.py`:
```python
def test_elixir_leaked_summary_averages_only_complete_battles():
    battles = [
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=1, opp_crowns=0,
            team_elixir_leaked=3.0, opp_elixir_leaked=2.0,
        ),
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=0, opp_crowns=1,
            team_elixir_leaked=5.0, opp_elixir_leaked=4.0,
        ),
        # excluded: team leaked is None
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=1, opp_crowns=1,
            team_elixir_leaked=None, opp_elixir_leaked=4.0,
        ),
        # excluded: opp leaked is None
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=1, opp_crowns=1,
            team_elixir_leaked=4.0, opp_elixir_leaked=None,
        ),
    ]
    summary = elixir_leaked_summary(battles)
    assert summary == {
        "my_avg": 4.0,
        "opp_avg": 3.0,
        "delta": 1.0,
        "sample": 2,
    }


def test_elixir_leaked_summary_no_complete_battles():
    battles = [
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=1, opp_crowns=0,
            team_elixir_leaked=None, opp_elixir_leaked=None,
        ),
    ]
    summary = elixir_leaked_summary(battles)
    assert summary == {
        "my_avg": None,
        "opp_avg": None,
        "delta": None,
        "sample": 0,
    }
```

- [ ] **Step 6: Run the `elixir_leaked_summary` test, expect FAIL**

```
pytest tests/test_features.py::test_elixir_leaked_summary_averages_only_complete_battles tests/test_features.py::test_elixir_leaked_summary_no_complete_battles -v
```
Expected: FAIL with `ImportError: cannot import name 'elixir_leaked_summary' from 'royale_analytics.features'`.

- [ ] **Step 7: Implement `elixir_leaked_summary`**

Append to `src/royale_analytics/features.py`:
```python
def elixir_leaked_summary(battles: list[dict]) -> dict:
    my_values: list[float] = []
    opp_values: list[float] = []
    for battle in battles:
        team_leaked = battle["team"]["elixir_leaked"]
        opp_leaked = battle["opponent"]["elixir_leaked"]
        if team_leaked is None or opp_leaked is None:
            continue
        my_values.append(team_leaked)
        opp_values.append(opp_leaked)
    sample = len(my_values)
    if sample == 0:
        return {"my_avg": None, "opp_avg": None, "delta": None, "sample": 0}
    my_avg = round(sum(my_values) / sample, 2)
    opp_avg = round(sum(opp_values) / sample, 2)
    delta = round(my_avg - opp_avg, 2)
    return {
        "my_avg": my_avg,
        "opp_avg": opp_avg,
        "delta": delta,
        "sample": sample,
    }
```

- [ ] **Step 8: Run the `elixir_leaked_summary` tests, expect PASS**

```
pytest tests/test_features.py::test_elixir_leaked_summary_averages_only_complete_battles tests/test_features.py::test_elixir_leaked_summary_no_complete_battles -v
```
Expected: 2 passed.

- [ ] **Step 9: Run the full test file, then commit**

```
pytest tests/test_features.py -v
```
Expected: all tests pass.

```
git add src/royale_analytics/features.py tests/test_features.py
git commit -m "feat: loss patterns and elixir leaked summary"
```

### Task 16: features.py — detect_level_deficits, frequent_opponent_decks

**Files:**
- Modify: `src/royale_analytics/features.py`
- Test: `tests/test_features.py`

**Interfaces:**
- Consumes: `classify_deck(cards, reference) -> DeckClassification` (from `classify.py`), `load_reference` (from `reference.py`), `make_profile`, `make_battle_view`, `HOG_DECK`, `GOLEM_DECK` (from `tests.factories`)
- Produces:
  - `@dataclass LevelDeficit(card_name: str, level: int, max_level: int, deficit: int)`
  - `@dataclass OpponentDeck(deck_key: str, archetype: str, count: int, wins: int, losses: int, sample_names: list[str])`
  - `def detect_level_deficits(profile: dict | None, my_deck_cards: list[dict] | None) -> list[LevelDeficit]`
  - `def frequent_opponent_decks(battles: list[dict], reference: Reference, *, top: int = 5) -> list[OpponentDeck]`

- [ ] **Step 1: Write failing test for `detect_level_deficits`**

Append to `tests/test_features.py`:
```python
from royale_analytics.features import (  # noqa: E402
    LevelDeficit,
    OpponentDeck,
    detect_level_deficits,
    frequent_opponent_decks,
)
from tests.factories import make_profile  # noqa: E402


def test_detect_level_deficits_for_under_leveled_card_in_deck():
    profile = make_profile({"Hog Rider": (11, 14), "Cannon": (14, 14)})
    deficits = detect_level_deficits(profile, HOG_DECK)
    assert isinstance(deficits, list)
    hog = next(d for d in deficits if d.card_name == "Hog Rider")
    assert hog == LevelDeficit(
        card_name="Hog Rider", level=11, max_level=14, deficit=3
    )
    # Cannon is maxed (14/14): no deficit row
    assert all(d.card_name != "Cannon" for d in deficits)


def test_detect_level_deficits_none_inputs_return_empty():
    assert detect_level_deficits(None, HOG_DECK) == []
    assert detect_level_deficits(make_profile({"Hog Rider": (11, 14)}), None) == []
    assert detect_level_deficits(None, None) == []
```

- [ ] **Step 2: Run the test, expect FAIL**

```
pytest tests/test_features.py::test_detect_level_deficits_for_under_leveled_card_in_deck tests/test_features.py::test_detect_level_deficits_none_inputs_return_empty -v
```
Expected: FAIL with `ImportError: cannot import name 'detect_level_deficits' from 'royale_analytics.features'`.

- [ ] **Step 3: Implement `LevelDeficit`, `OpponentDeck`, and `detect_level_deficits`**

Append to `src/royale_analytics/features.py` (place the two dataclasses near `MatchupRow` conceptually; appended at end is fine since module-level order does not affect runtime):
```python
@dataclass
class LevelDeficit:
    card_name: str
    level: int
    max_level: int
    deficit: int


@dataclass
class OpponentDeck:
    deck_key: str
    archetype: str
    count: int
    wins: int
    losses: int
    sample_names: list[str]


def detect_level_deficits(
    profile: dict | None, my_deck_cards: list[dict] | None
) -> list[LevelDeficit]:
    if profile is None or my_deck_cards is None:
        return []
    levels_by_name = {
        card["name"]: card for card in profile.get("cards", [])
    }
    deficits: list[LevelDeficit] = []
    for card in my_deck_cards:
        name = card["name"]
        profile_card = levels_by_name.get(name)
        if profile_card is None:
            continue
        level = profile_card["level"]
        max_level = profile_card["maxLevel"]
        deficit = max_level - level
        if deficit > 0:
            deficits.append(
                LevelDeficit(
                    card_name=name,
                    level=level,
                    max_level=max_level,
                    deficit=deficit,
                )
            )
    return deficits
```

- [ ] **Step 4: Run the `detect_level_deficits` tests, expect PASS**

```
pytest tests/test_features.py::test_detect_level_deficits_for_under_leveled_card_in_deck tests/test_features.py::test_detect_level_deficits_none_inputs_return_empty -v
```
Expected: 2 passed. (`make_profile` builds `cards` entries with `name`/`level`/`maxLevel` keys, which the implementation reads directly.)

- [ ] **Step 5: Write failing test for `frequent_opponent_decks`**

Append to `tests/test_features.py`:
```python
def test_frequent_opponent_decks_counts_and_classifies():
    ref = load_reference()
    battles = [
        # vs same Golem deck (loss)
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=0, opp_crowns=3,
            battle_time="2026-05-01T00:00:00+00:00",
        ),
        # vs same Golem deck (win)
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=2, opp_crowns=1,
            battle_time="2026-05-01T01:00:00+00:00",
        ),
        # vs a Hog deck (win)
        make_battle_view(
            team_cards=GOLEM_DECK, opp_cards=HOG_DECK,
            team_crowns=3, opp_crowns=0,
            battle_time="2026-05-01T02:00:00+00:00",
        ),
    ]
    decks = frequent_opponent_decks(battles, ref, top=5)
    assert isinstance(decks[0], OpponentDeck)
    first = decks[0]
    assert first.count == 2
    assert first.archetype == "beatdown"
    assert first.wins == 1
    assert first.losses == 1
    assert "Golem" in first.sample_names
```

- [ ] **Step 6: Run the `frequent_opponent_decks` test, expect FAIL**

```
pytest tests/test_features.py::test_frequent_opponent_decks_counts_and_classifies -v
```
Expected: FAIL with `ImportError: cannot import name 'frequent_opponent_decks' from 'royale_analytics.features'`.

- [ ] **Step 7: Implement `frequent_opponent_decks`**

Append to `src/royale_analytics/features.py`:
```python
def frequent_opponent_decks(
    battles: list[dict], reference: Reference, *, top: int = 5
) -> list[OpponentDeck]:
    groups: dict[str, dict] = {}
    order: list[str] = []
    for battle in battles:
        opponent = battle["opponent"]
        deck_key = opponent["deck_key"]
        if deck_key not in groups:
            groups[deck_key] = {
                "deck_key": deck_key,
                "cards": opponent["cards"],
                "count": 0,
                "wins": 0,
                "losses": 0,
            }
            order.append(deck_key)
        group = groups[deck_key]
        group["count"] += 1
        result = battle["result"]
        if result == "win":
            group["wins"] += 1
        elif result == "loss":
            group["losses"] += 1
    ranked = sorted(
        order,
        key=lambda key: (-groups[key]["count"], order.index(key)),
    )
    decks: list[OpponentDeck] = []
    for key in ranked[:top]:
        group = groups[key]
        classification = classify_deck(group["cards"], reference)
        sample_names = [card["name"] for card in group["cards"]][:8]
        decks.append(
            OpponentDeck(
                deck_key=group["deck_key"],
                archetype=classification.archetype,
                count=group["count"],
                wins=group["wins"],
                losses=group["losses"],
                sample_names=sample_names,
            )
        )
    return decks
```

- [ ] **Step 8: Run the `frequent_opponent_decks` test, expect PASS**

```
pytest tests/test_features.py::test_frequent_opponent_decks_counts_and_classifies -v
```
Expected: 1 passed. The two GOLEM_DECK battles share one `deck_key` (same card ids) → `count == 2`, classified `beatdown`; one win + one loss.

- [ ] **Step 9: Run the full test file, then commit**

```
pytest tests/test_features.py -v
```
Expected: all tests pass.

```
git add src/royale_analytics/features.py tests/test_features.py
git commit -m "feat: level deficits and frequent opponent decks"
```

### Task 17: features.py — build_features

**Files:**
- Modify: `src/royale_analytics/features.py`
- Test: `tests/test_features.py`

**Interfaces:**
- Consumes: `classify_deck(cards, reference) -> DeckClassification` and `match_deck(cards, reference, *, variant_threshold=6) -> DeckMatch` (from `classify.py`), `load_reference` (from `reference.py`), plus the Task 14-16 helpers `mode_of`, `current_deck`, `derive_matchups`, `detect_loss_patterns`, `elixir_leaked_summary`, `detect_level_deficits`, `frequent_opponent_decks`; `make_profile`, `make_battle_view`, `HOG_DECK`, `GOLEM_DECK` (from `tests.factories`)
- Produces:
  - `@dataclass Features(my_deck: DeckClassification | None, my_deck_match: DeckMatch | None, matchups: list[MatchupRow], loss_patterns: dict, level_deficits: list[LevelDeficit], elixir_leaked: dict, frequent_opponent_decks: list[OpponentDeck], sample_size: int, gap_warning: bool, modes_present: list[str])`
  - `def build_features(battles: list[dict], profile: dict | None, reference: Reference) -> Features`

- [ ] **Step 1: Write failing test for `build_features` on empty input**

Append to `tests/test_features.py`:
```python
from royale_analytics.features import Features, build_features  # noqa: E402


def test_build_features_empty_battles():
    ref = load_reference()
    features = build_features([], None, ref)
    assert isinstance(features, Features)
    assert features.my_deck is None
    assert features.my_deck_match is None
    assert features.matchups == []
    assert features.level_deficits == []
    assert features.frequent_opponent_decks == []
    assert features.sample_size == 0
    assert features.gap_warning is False
    assert features.modes_present == []
    assert features.loss_patterns == {
        "total_losses": 0,
        "three_crown_losses": 0,
        "close_losses": 0,
    }
    assert features.elixir_leaked == {
        "my_avg": None,
        "opp_avg": None,
        "delta": None,
        "sample": 0,
    }
```

- [ ] **Step 2: Run the test, expect FAIL**

```
pytest tests/test_features.py::test_build_features_empty_battles -v
```
Expected: FAIL with `ImportError: cannot import name 'Features' from 'royale_analytics.features'`.

- [ ] **Step 3: Implement `Features` dataclass and `build_features`**

Add the import of `match_deck` and `DeckMatch` to the existing `classify` import line at the top of `src/royale_analytics/features.py`. Change:
```python
from .classify import DeckClassification, classify_deck
```
to:
```python
from .classify import DeckClassification, DeckMatch, classify_deck, match_deck
```

Then append to `src/royale_analytics/features.py`:
```python
@dataclass
class Features:
    my_deck: DeckClassification | None
    my_deck_match: DeckMatch | None
    matchups: list[MatchupRow]
    loss_patterns: dict
    level_deficits: list[LevelDeficit]
    elixir_leaked: dict
    frequent_opponent_decks: list[OpponentDeck]
    sample_size: int
    gap_warning: bool
    modes_present: list[str]


def build_features(
    battles: list[dict], profile: dict | None, reference: Reference
) -> Features:
    deck_cards = current_deck(battles)
    my_deck = classify_deck(deck_cards, reference) if deck_cards else None
    my_deck_match = match_deck(deck_cards, reference) if deck_cards else None
    sample_size = len(battles)
    modes_present = sorted({mode_of(battle) for battle in battles})
    return Features(
        my_deck=my_deck,
        my_deck_match=my_deck_match,
        matchups=derive_matchups(battles, reference),
        loss_patterns=detect_loss_patterns(battles),
        level_deficits=detect_level_deficits(profile, deck_cards),
        elixir_leaked=elixir_leaked_summary(battles),
        frequent_opponent_decks=frequent_opponent_decks(battles, reference),
        sample_size=sample_size,
        gap_warning=sample_size >= 25,
        modes_present=modes_present,
    )
```

- [ ] **Step 4: Run the empty-input test, expect PASS**

```
pytest tests/test_features.py::test_build_features_empty_battles -v
```
Expected: 1 passed.

- [ ] **Step 5: Write failing test for `build_features` on populated input**

Append to `tests/test_features.py`:
```python
def test_build_features_populated():
    ref = load_reference()
    profile = make_profile({"Hog Rider": (11, 14), "Cannon": (14, 14)})
    battles = [
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=0, opp_crowns=3,
            battle_time="2026-05-01T00:00:00+00:00",
            mode_fields={"game_mode_name": "Ladder",
                         "is_ladder_tournament": False, "league_number": None},
        ),
        make_battle_view(
            team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
            team_crowns=2, opp_crowns=1,
            battle_time="2026-05-02T00:00:00+00:00",
            mode_fields={"game_mode_name": "Ranked",
                         "is_ladder_tournament": False, "league_number": 5},
        ),
    ]
    features = build_features(battles, profile, ref)
    # current_deck is the most-recent battle's team (HOG_DECK) -> cycle
    assert features.my_deck is not None
    assert features.my_deck.archetype == "cycle"
    assert features.sample_size == 2
    assert features.modes_present == ["ladder", "ranked"]
    # level deficit from profile against the current (Hog) deck
    assert any(d.card_name == "Hog Rider" for d in features.level_deficits)
```

- [ ] **Step 6: Run the populated test, expect PASS**

```
pytest tests/test_features.py::test_build_features_populated -v
```
Expected: 1 passed. `current_deck` returns the most-recent battle's `team.cards` (HOG_DECK, battle_time `2026-05-02`), which classifies as `cycle`; `modes_present` is the sorted set `["ladder", "ranked"]`.

- [ ] **Step 7: Run the full test file, then commit**

```
pytest tests/test_features.py -v
```
Expected: all tests in the file pass.

```
git add src/royale_analytics/features.py tests/test_features.py
git commit -m "feat: compose build_features"
```

### Task 18: brief.py — `render_json(features) -> dict`

**Files:**
- Create: `src/royale_analytics/brief.py`
- Test: `tests/test_brief_json.py`

**Interfaces:**
- Consumes:
  - `royale_analytics.features.build_features(battles: list[dict], profile: dict | None, reference: Reference) -> Features`
  - `royale_analytics.features.Features` (dataclass with fields `my_deck`, `my_deck_match`, `matchups`, `loss_patterns`, `level_deficits`, `elixir_leaked`, `frequent_opponent_decks`, `sample_size`, `gap_warning`, `modes_present`)
  - `royale_analytics.reference.load_reference(ref_dir=None) -> Reference`
  - Test factories: `make_battle_view`, `HOG_DECK`, `GOLEM_DECK`
- Produces:
  - `royale_analytics.brief.render_json(features: Features) -> dict` — JSON-serializable dict produced via `dataclasses.asdict(features)`. Nested dataclasses (`DeckClassification`, `DeckMatch`, `MatchupRow`, `LevelDeficit`, `OpponentDeck`) convert recursively; `None` values for `my_deck`/`my_deck_match` stay `None`. Guarantee: `json.dumps(render_json(f))` never raises.

Steps:

- [ ] **Step 1: Write failing test for `render_json`.**
  Create `tests/test_brief_json.py`:

```python
from __future__ import annotations

import json

from royale_analytics.brief import render_json
from royale_analytics.features import build_features
from royale_analytics.reference import load_reference
from tests.factories import HOG_DECK, GOLEM_DECK, make_battle_view


def _battles():
    return [
        make_battle_view(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                         team_crowns=2, opp_crowns=1),
        make_battle_view(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                         team_crowns=0, opp_crowns=3),
        make_battle_view(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                         team_crowns=1, opp_crowns=2),
    ]


def test_render_json_returns_dict_with_top_level_keys():
    ref = load_reference()
    features = build_features(_battles(), None, ref)
    out = render_json(features)
    assert isinstance(out, dict)
    for key in ("my_deck", "matchups", "sample_size"):
        assert key in out


def test_render_json_my_deck_is_dict_with_archetype():
    ref = load_reference()
    features = build_features(_battles(), None, ref)
    out = render_json(features)
    assert isinstance(out["my_deck"], dict)
    assert "archetype" in out["my_deck"]


def test_render_json_matchups_is_list_of_dicts():
    ref = load_reference()
    features = build_features(_battles(), None, ref)
    out = render_json(features)
    assert isinstance(out["matchups"], list)
    for row in out["matchups"]:
        assert isinstance(row, dict)
        assert "opponent_archetype" in row


def test_render_json_is_json_serializable():
    ref = load_reference()
    features = build_features(_battles(), None, ref)
    out = render_json(features)
    # Must not raise.
    dumped = json.dumps(out)
    assert isinstance(dumped, str)
```

- [ ] **Step 2: Run the test & expect FAIL.**
  Command: `pytest tests/test_brief_json.py -v`
  Expected: FAIL — collection/import error `ModuleNotFoundError: No module named 'royale_analytics.brief'` (the module does not exist yet).

- [ ] **Step 3: Minimal implementation of `render_json`.**
  Create `src/royale_analytics/brief.py`:

```python
from __future__ import annotations

import dataclasses

from .features import Features


def render_json(features: Features) -> dict:
    """Convert Features into a JSON-serializable dict.

    Uses dataclasses.asdict, which recursively converts nested dataclasses
    (DeckClassification, DeckMatch, MatchupRow, LevelDeficit, OpponentDeck)
    into plain dicts. None values (e.g. my_deck on an empty history) are
    preserved. The resulting structure contains only dicts, lists, str, int,
    float, bool, and None, so json.dumps(render_json(f)) never raises.
    """
    return dataclasses.asdict(features)
```

- [ ] **Step 4: Run the test & expect PASS.**
  Command: `pytest tests/test_brief_json.py -v`
  Expected: PASS — all four tests pass (`test_render_json_returns_dict_with_top_level_keys`, `test_render_json_my_deck_is_dict_with_archetype`, `test_render_json_matchups_is_list_of_dicts`, `test_render_json_is_json_serializable`).

- [ ] **Step 5: Commit (this task's files only).**
  Commands:
  ```
  git add src/royale_analytics/brief.py tests/test_brief_json.py
  git commit -m "feat: add brief.render_json for JSON-serializable analysis brief"
  ```

### Task 19: brief.py — `render_markdown(features) -> str`

**Files:**
- Modify: `src/royale_analytics/brief.py`
- Test: `tests/test_brief_markdown.py`

**Interfaces:**
- Consumes:
  - `royale_analytics.features.Features` and its nested dataclasses (`DeckClassification.archetype`/`.avg_elixir`/`.weakness_tags`, `DeckMatch.name`/`.confidence`, `MatchupRow.opponent_archetype`/`.mode`/`.wins`/`.losses`/`.draws`, `LevelDeficit.card_name`/`.level`/`.max_level`/`.deficit`, `OpponentDeck.deck_key`/`.archetype`/`.count`/`.wins`/`.losses`/`.sample_names`)
  - `Features.loss_patterns` dict keys `total_losses`/`three_crown_losses`/`close_losses`; `Features.elixir_leaked` dict keys `my_avg`/`opp_avg`/`delta`/`sample`; `Features.sample_size`/`gap_warning`/`modes_present`
  - `royale_analytics.features.build_features`, `royale_analytics.reference.load_reference`
  - Test factories: `make_battle_view`, `HOG_DECK`, `GOLEM_DECK`
- Produces:
  - `royale_analytics.brief.render_markdown(features: Features) -> str` — Japanese human-readable brief. Sections (逐語 headings): `あなたのデッキ`, `相性表`, `負け方パターン`, `レベル差`, `elixirLeaked`, `頻出相手デッキ`. elixirLeaked is labelled `推測`/`参考` (NEVER `実測` for derived play). Footer note states 立ち回り and elixirLeaked are `推測` not `実測`. Emits the substring `標本が少` when `sample_size < 10`, and a gap warning when `gap_warning` is true. Empty Features renders without error and notes `試合がない`/`データがない`.

Steps:

- [ ] **Step 1: Write failing test for the main `render_markdown` behaviors.**
  Create `tests/test_brief_markdown.py`:

```python
from __future__ import annotations

from royale_analytics.brief import render_markdown
from royale_analytics.features import build_features
from royale_analytics.reference import load_reference
from tests.factories import HOG_DECK, GOLEM_DECK, make_battle_view


def _battles(n):
    out = []
    for i in range(n):
        team_crowns, opp_crowns = (2, 1) if i % 2 == 0 else (0, 3)
        out.append(make_battle_view(team_cards=HOG_DECK, opp_cards=GOLEM_DECK,
                                    team_crowns=team_crowns, opp_crowns=opp_crowns))
    return out


def test_render_markdown_contains_core_sections_and_archetype():
    ref = load_reference()
    features = build_features(_battles(12), None, ref)
    md = render_markdown(features)
    assert isinstance(md, str)
    assert "あなたのデッキ" in md
    assert "相性表" in md
    assert "負け方パターン" in md
    assert "レベル差" in md
    assert "elixirLeaked" in md
    assert "頻出相手デッキ" in md
    # my_deck archetype must appear (HOG_DECK classifies as "cycle").
    assert features.my_deck is not None
    assert features.my_deck.archetype in md


def test_render_markdown_marks_guess_not_measured():
    ref = load_reference()
    features = build_features(_battles(12), None, ref)
    md = render_markdown(features)
    assert "推測" in md
    # elixirLeaked / 立ち回り must NOT be presented as 実測.
    assert "elixirLeaked（実測）" not in md
    assert "立ち回り（実測）" not in md


def test_render_markdown_small_sample_warning():
    ref = load_reference()
    features = build_features(_battles(3), None, ref)  # sample_size < 10
    md = render_markdown(features)
    assert features.sample_size < 10
    assert "標本が少" in md
```

- [ ] **Step 2: Run the test & expect FAIL.**
  Command: `pytest tests/test_brief_markdown.py -v`
  Expected: FAIL — `AttributeError: module 'royale_analytics.brief' has no attribute 'render_markdown'` (function not defined yet).

- [ ] **Step 3: Implement `render_markdown` in `brief.py`.**
  Edit `src/royale_analytics/brief.py` to add the `render_markdown` function and its helpers (full file shown):

```python
from __future__ import annotations

import dataclasses

from .features import Features


def render_json(features: Features) -> dict:
    """Convert Features into a JSON-serializable dict.

    Uses dataclasses.asdict, which recursively converts nested dataclasses
    (DeckClassification, DeckMatch, MatchupRow, LevelDeficit, OpponentDeck)
    into plain dicts. None values (e.g. my_deck on an empty history) are
    preserved. The resulting structure contains only dicts, lists, str, int,
    float, bool, and None, so json.dumps(render_json(f)) never raises.
    """
    return dataclasses.asdict(features)


def _fmt_opt(value: object) -> str:
    """Render an optional number/None for display."""
    if value is None:
        return "不明"
    return str(value)


def _render_my_deck(features: Features) -> list[str]:
    lines: list[str] = ["## あなたのデッキ", ""]
    deck = features.my_deck
    if deck is None:
        lines.append("デッキを判定できる試合がないため、デッキ情報はありません。")
        lines.append("")
        return lines
    lines.append(f"- アーキタイプ: {deck.archetype}")
    lines.append(f"- 平均エリクサー: {deck.avg_elixir}")
    match = features.my_deck_match
    if match is not None and match.name is not None:
        lines.append(f"- テンプレ照合: {match.name}（{match.confidence}）")
    else:
        confidence = match.confidence if match is not None else "unknown"
        lines.append(f"- テンプレ照合: 該当なし（{confidence}）")
    if deck.weakness_tags:
        lines.append(f"- 弱点タグ: {', '.join(deck.weakness_tags)}")
    else:
        lines.append("- 弱点タグ: なし")
    lines.append("")
    return lines


def _render_matchups(features: Features) -> list[str]:
    lines: list[str] = ["## 相性表", ""]
    if not features.matchups:
        lines.append("相性を集計できる試合がありません。")
        lines.append("")
        return lines
    lines.append("| 相手アーキタイプ | モード | 勝 | 負 | 分 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for row in features.matchups:
        lines.append(
            f"| {row.opponent_archetype} | {row.mode} | "
            f"{row.wins} | {row.losses} | {row.draws} |"
        )
    lines.append("")
    return lines


def _render_loss_patterns(features: Features) -> list[str]:
    lines: list[str] = ["## 負け方パターン", ""]
    lp = features.loss_patterns
    total = lp.get("total_losses", 0)
    three = lp.get("three_crown_losses", 0)
    close = lp.get("close_losses", 0)
    lines.append(f"- 総負け数: {total}")
    lines.append(f"- 3クラウン負け: {three}")
    lines.append(f"- 接戦負け（1クラウン差）: {close}")
    lines.append("")
    return lines


def _render_level_deficits(features: Features) -> list[str]:
    lines: list[str] = ["## レベル差", ""]
    if not features.level_deficits:
        lines.append("レベル差のあるカードはありません（または所持データなし）。")
        lines.append("")
        return lines
    lines.append("| カード | レベル | 最大 | 差 |")
    lines.append("| --- | --- | --- | --- |")
    for d in features.level_deficits:
        lines.append(f"| {d.card_name} | {d.level} | {d.max_level} | {d.deficit} |")
    lines.append("")
    return lines


def _render_elixir_leaked(features: Features) -> list[str]:
    lines: list[str] = ["## elixirLeaked（推測・参考）", ""]
    el = features.elixir_leaked
    my_avg = el.get("my_avg")
    opp_avg = el.get("opp_avg")
    delta = el.get("delta")
    sample = el.get("sample", 0)
    lines.append("※ elixirLeaked は唯一の機械的指標ですが、立ち回りの良し悪しを直接")
    lines.append("測ったものではなく、あくまで推測・参考値です（実測ではありません）。")
    lines.append(f"- 自分の平均: {_fmt_opt(my_avg)}")
    lines.append(f"- 相手の平均: {_fmt_opt(opp_avg)}")
    lines.append(f"- 差（自分 - 相手）: {_fmt_opt(delta)}")
    lines.append(f"- 対象試合数: {sample}")
    lines.append("")
    return lines


def _render_frequent_opponents(features: Features) -> list[str]:
    lines: list[str] = ["## 頻出相手デッキ", ""]
    if not features.frequent_opponent_decks:
        lines.append("頻出相手デッキを集計できる試合がありません。")
        lines.append("")
        return lines
    for od in features.frequent_opponent_decks:
        names = "、".join(od.sample_names) if od.sample_names else od.deck_key
        lines.append(
            f"- [{od.archetype}] {od.count}回 "
            f"(勝 {od.wins} / 負 {od.losses}): {names}"
        )
    lines.append("")
    return lines


def _render_footer(features: Features) -> list[str]:
    lines: list[str] = ["## メモ・注記", ""]
    lines.append(f"- 標本サイズ: {features.sample_size} 試合")
    if features.modes_present:
        lines.append(f"- 含まれるモード: {', '.join(features.modes_present)}")
    if features.sample_size == 0:
        lines.append("- まだ試合がないため、分析できるデータがありません。"
                     "`ra fetch` で対戦履歴を蓄積してください。")
    elif features.sample_size < 10:
        lines.append("- 標本が少ないため、結果は断定ではなく仮説として扱ってください。")
    if features.gap_warning:
        lines.append("- 取りこぼし（ギャップ）の疑いがあります。"
                     "battlelog は直近約25戦しか返さないため、"
                     "こまめな `ra fetch` を推奨します。")
    lines.append("- 立ち回り・elixirLeaked 由来の示唆はすべて「推測」であり、"
                 "試合中の実測ではありません。")
    lines.append("")
    return lines


def render_markdown(features: Features) -> str:
    """Render a Japanese human-readable analysis brief.

    Always includes the sections あなたのデッキ / 相性表 / 負け方パターン /
    レベル差 / elixirLeaked / 頻出相手デッキ plus a footer. elixirLeaked and
    立ち回り are explicitly labelled 推測 (NOT 実測). Emits a small-sample
    warning ("標本が少") when sample_size < 10, an empty-data note ("試合がない"
    / "データがない") when there are no battles, and a gap warning when
    gap_warning is set.
    """
    lines: list[str] = ["# 分析ブリーフ", ""]
    lines += _render_my_deck(features)
    lines += _render_matchups(features)
    lines += _render_loss_patterns(features)
    lines += _render_level_deficits(features)
    lines += _render_elixir_leaked(features)
    lines += _render_frequent_opponents(features)
    lines += _render_footer(features)
    return "\n".join(lines)
```

- [ ] **Step 4: Run the test & expect PASS.**
  Command: `pytest tests/test_brief_markdown.py -v`
  Expected: PASS — `test_render_markdown_contains_core_sections_and_archetype`, `test_render_markdown_marks_guess_not_measured`, `test_render_markdown_small_sample_warning` all pass.

- [ ] **Step 5: Write failing test for the empty-Features behavior.**
  Append to `tests/test_brief_markdown.py`:

```python
def test_render_markdown_empty_features_renders_with_no_data_note():
    ref = load_reference()
    features = build_features([], None, ref)
    md = render_markdown(features)  # must not raise
    assert isinstance(md, str)
    assert features.sample_size == 0
    assert features.my_deck is None
    # Core sections still present.
    assert "あなたのデッキ" in md
    # Notes that there is no data / no battles.
    assert ("データがない" in md) or ("試合がない" in md)
```

- [ ] **Step 6: Run the empty-Features test & expect PASS.**
  Command: `pytest tests/test_brief_markdown.py::test_render_markdown_empty_features_renders_with_no_data_note -v`
  Expected: PASS — the footer's `sample_size == 0` branch emits "まだ試合がないため、分析できるデータがありません。", which contains the substrings `試合がない` and `データがない` (both satisfy the assertion), and `_render_my_deck` handles `my_deck is None` without raising.

- [ ] **Step 7: Run the full brief test suite & expect PASS.**
  Command: `pytest tests/test_brief_json.py tests/test_brief_markdown.py -v`
  Expected: PASS — all Task 18 and Task 19 tests pass together.

- [ ] **Step 8: Commit (this task's files only).**
  Commands:
  ```
  git add src/royale_analytics/brief.py tests/test_brief_markdown.py
  git commit -m "feat: add brief.render_markdown Japanese analysis brief with guess labelling and sample/gap warnings"
  ```

### Task 20: cli.py — group + `init` command

**Files:**
- Create: `src/royale_analytics/cli.py`
- Test: `tests/test_cli_init.py`

**Interfaces:**
- Consumes:
  - `from royale_analytics.config import Config, load_config` — `Config(token: str, base_url: str, player_tag: str, db_path: str)` (frozen dataclass); `load_config(env: Mapping[str, str] | None = None) -> Config`
  - `from royale_analytics.store import Store` — `Store(db_path: str)`; `Store.init_schema() -> None`
  - `from royale_analytics.tags import normalize_tag` — `normalize_tag(raw: str) -> str`
- Produces:
  - `from royale_analytics.cli import cli` — `cli` is a `click.Group`
  - `init` command registered on `cli` as `cli.command()`; signature `def init() -> None`. Exits 0; prints normalized player tag, the db path, the whitelist IP `45.79.218.79`, and the proxy base URL.

- [ ] **Step 1: Write the failing test for `init`.**

Create `tests/test_cli_init.py`:

```python
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
```

- [ ] **Step 2: Run it and expect FAIL.**

```
pytest tests/test_cli_init.py::test_init_prints_tag_and_whitelist_and_creates_db -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'royale_analytics.cli'` (the module does not exist yet).

- [ ] **Step 3: Create `src/royale_analytics/cli.py` with the group and `init`.**

Create `src/royale_analytics/cli.py`:

```python
from __future__ import annotations

import click

from royale_analytics.config import load_config
from royale_analytics.store import Store

WHITELIST_IP = "45.79.218.79"


@click.group()
def cli() -> None:
    """Royale Analytics — クラッシュロワイヤルのAI分析ツール（非公式）。"""


@cli.command()
def init() -> None:
    """設定を検証し、DB を初期化し、初回セットアップ手順を表示する。"""
    config = load_config()

    click.echo("Royale Analytics の初期化を行います。")
    click.echo(f"プレイヤータグ（正規化済み）: {config.player_tag}")
    click.echo(f"API base URL: {config.base_url}")
    click.echo(f"DB パス: {config.db_path}")

    store = Store(config.db_path)
    store.init_schema()
    click.echo("SQLite スキーマを初期化しました。")

    click.echo("")
    click.echo("セットアップ手順:")
    click.echo("  1. developer.clashroyale.com で API トークンを無料発行する。")
    click.echo(
        "  2. トークン作成時に固定 IP "
        f"{WHITELIST_IP} をホワイトリストへ登録する"
        "（RoyaleAPI proxy 用）。"
    )
    click.echo(
        f"  3. リクエスト先を proxy base URL {config.base_url} にする"
        "（同じ Bearer トークンをそのまま使用）。"
    )
    click.echo(
        "  4. .env に CLASH_ROYALE_API_TOKEN と CR_PLAYER_TAG を設定する。"
    )
    click.echo("")
    click.echo(
        "This material is unofficial and is not endorsed by Supercell. "
        "For more information see Supercell's Fan Content Policy: "
        "www.supercell.com/fan-content-policy."
    )
```

- [ ] **Step 4: Run the test and expect PASS.**

```
pytest tests/test_cli_init.py::test_init_prints_tag_and_whitelist_and_creates_db -v
```

Expected: PASS. The monkeypatched `load_config` returns a `Config` pointing at the tmp db; `init` echoes the tag `2PP`, the db path, `45.79.218.79`, and the proxy base URL, then `Store(db_path).init_schema()` creates the sqlite file so `db_path.exists()` is true.

- [ ] **Step 5: Commit (only this task's files).**

```
git add src/royale_analytics/cli.py tests/test_cli_init.py
git commit -m "feat: add cli group and init command"
```

### Task 21: cli.py — `fetch` command

**Files:**
- Modify: `src/royale_analytics/cli.py`
- Test: `tests/test_cli_fetch.py`

**Interfaces:**
- Consumes:
  - `from royale_analytics.config import load_config` — `load_config() -> Config`
  - `from royale_analytics.api_client import ApiClient` — `ApiClient(token: str, base_url: str)`; `get_player(tag: str) -> dict`; `get_battlelog(tag: str) -> list[dict]`; `get_upcoming_chests(tag: str) -> dict`
  - `from royale_analytics.store import Store` — `Store(db_path: str)`; `init_schema() -> None`; `upsert_battles(player_tag: str, battlelog: list[dict]) -> int`; `save_profile_snapshot(player_tag: str, profile: dict) -> None`; `record_fetch(player_tag: str, new_battles: int, gap_suspected: bool) -> None`
- Produces:
  - `fetch` command registered on `cli` (`cli.command()`); signature `def fetch() -> None`. Exits 0; prints the new-battle count as `N 件の新規対戦を取得` and a gap note when `gap_suspected` is true. `gap_suspected = len(battlelog) >= 25`. Failure of `get_upcoming_chests` is tolerated (caught, fetch still succeeds).

- [ ] **Step 1: Write the failing test for `fetch` (basic count report).**

Create `tests/test_cli_fetch.py`:

```python
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
```

- [ ] **Step 2: Run it and expect FAIL.**

```
pytest tests/test_cli_fetch.py::test_fetch_reports_new_battle_count -v
```

Expected: FAIL with `click`'s "No such command 'fetch'." (the `fetch` command is not registered yet; `result.exit_code` is non-zero).

- [ ] **Step 3: Add the `fetch` command to `src/royale_analytics/cli.py`.**

First update the imports block at the top of `src/royale_analytics/cli.py`:

```python
from __future__ import annotations

import click

from royale_analytics.api_client import ApiClient
from royale_analytics.config import load_config
from royale_analytics.store import Store

WHITELIST_IP = "45.79.218.79"
GAP_BATTLELOG_THRESHOLD = 25
```

Then append the `fetch` command after `init`:

```python
@cli.command()
def fetch() -> None:
    """プロフィール＋battlelog（＋upcomingchests）を取得し SQLite に追記する。"""
    config = load_config()

    client = ApiClient(config.token, config.base_url)
    store = Store(config.db_path)
    store.init_schema()

    profile = client.get_player(config.player_tag)
    battlelog = client.get_battlelog(config.player_tag)

    try:
        client.get_upcoming_chests(config.player_tag)
    except Exception as exc:  # noqa: BLE001 - chests は任意。失敗しても続行
        click.echo(f"upcomingchests の取得に失敗しました（続行します）: {exc}")

    if not battlelog:
        click.echo(
            "まだ対戦がありません（battlelog が空です）。"
            "プレイしてから再実行してください。"
        )

    new_battles = store.upsert_battles(config.player_tag, battlelog)
    store.save_profile_snapshot(config.player_tag, profile)

    gap_suspected = len(battlelog) >= GAP_BATTLELOG_THRESHOLD
    store.record_fetch(
        config.player_tag, new_battles, gap_suspected=gap_suspected
    )

    click.echo(f"{new_battles} 件の新規対戦を取得")
    if gap_suspected:
        click.echo(
            "ギャップ警告: battlelog が満杯（25件）でした。"
            "前回取得からの取りこぼしの可能性があります。"
        )
```

- [ ] **Step 4: Run the test and expect PASS.**

```
pytest tests/test_cli_fetch.py::test_fetch_reports_new_battle_count -v
```

Expected: PASS. The monkeypatched `ApiClient` factory returns a `FakeApiClient` serving 2 raw battles + a profile; `upsert_battles` persists both, `fetch` prints `2 件の新規対戦を取得`, no gap note (2 < 25), and `load_battles` confirms 2 rows.

- [ ] **Step 5: Write a second failing test — gap note + tolerated chests failure.**

Add to `tests/test_cli_fetch.py`:

```python
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
```

- [ ] **Step 6: Run the new test and expect PASS (no impl change needed).**

```
pytest tests/test_cli_fetch.py -v
```

Expected: both tests PASS. `len(battlelog) == 25 >= 25` triggers the gap note; the `RuntimeError` from `get_upcoming_chests` is caught and reported without aborting, so `exit_code == 0` and the count is still printed.

- [ ] **Step 7: Write the failing test for empty-battlelog handling.**

Add to `tests/test_cli_fetch.py`:

```python
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
```

- [ ] **Step 8: Run the test and expect PASS (no impl change needed).**

```
pytest tests/test_cli_fetch.py::test_fetch_reports_empty_battlelog -v
```

Expected: PASS. The fake `ApiClient` returns `[]` for the battlelog; `fetch` echoes the graceful note, still calls `record_fetch`, and exits 0.

- [ ] **Step 9: Commit (only this task's files).**

```
git add src/royale_analytics/cli.py tests/test_cli_fetch.py
git commit -m "feat: add fetch command"
```

### Task 22: cli.py — `analyze` command

**Files:**
- Modify: `src/royale_analytics/cli.py`
- Test: `tests/test_cli_analyze.py`

**Interfaces:**
- Consumes:
  - `from royale_analytics.config import load_config` — `load_config() -> Config`
  - `from royale_analytics.store import Store` — `Store(db_path: str)`; `load_battles(player_tag: str) -> list[dict]` (battle view dicts); `get_latest_profile(player_tag: str) -> dict | None`
  - `from royale_analytics.reference import load_reference` — `load_reference(ref_dir=None) -> Reference`
  - `from royale_analytics.features import build_features` — `build_features(battles: list[dict], profile: dict | None, reference: Reference) -> Features`
  - `from royale_analytics.brief import render_markdown, render_json` — `render_markdown(features: Features) -> str`; `render_json(features: Features) -> dict`
- Produces:
  - `analyze` command registered on `cli`; `@click.option("--json-out", type=click.Path(), default=None)`; signature `def analyze(json_out: str | None) -> None`. Exits 0; echoes `render_markdown(features)` (contains `あなたのデッキ`); when `--json-out` given, writes `json.dumps(render_json(features))` to that path (valid for `json.load`).

- [ ] **Step 1: Write the failing test for `analyze` (markdown output).**

Create `tests/test_cli_analyze.py`:

```python
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
```

- [ ] **Step 2: Run it and expect FAIL.**

```
pytest tests/test_cli_analyze.py::test_analyze_outputs_markdown -v
```

Expected: FAIL with `click`'s "No such command 'analyze'." (the `analyze` command is not registered yet; non-zero exit code).

- [ ] **Step 3: Add the `analyze` command to `src/royale_analytics/cli.py`.**

First update the imports/constants block at the top of `src/royale_analytics/cli.py`:

```python
from __future__ import annotations

import json

import click

from royale_analytics.api_client import ApiClient
from royale_analytics.brief import render_json, render_markdown
from royale_analytics.config import load_config
from royale_analytics.features import build_features
from royale_analytics.reference import load_reference
from royale_analytics.store import Store

WHITELIST_IP = "45.79.218.79"
GAP_BATTLELOG_THRESHOLD = 25
```

Then append the `analyze` command after `fetch`:

```python
@cli.command()
@click.option("--json-out", type=click.Path(), default=None)
def analyze(json_out: str | None) -> None:
    """蓄積から特徴量を算出し、分析ブリーフ（Markdown＋任意でJSON）を出力する。"""
    config = load_config()

    store = Store(config.db_path)
    reference = load_reference()

    battles = store.load_battles(config.player_tag)
    profile = store.get_latest_profile(config.player_tag)

    features = build_features(battles, profile, reference)

    click.echo(render_markdown(features))

    if json_out is not None:
        with open(json_out, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(render_json(features), ensure_ascii=False))
        click.echo(f"JSON ブリーフを書き出しました: {json_out}")
```

- [ ] **Step 4: Run the markdown test and expect PASS.**

```
pytest tests/test_cli_analyze.py::test_analyze_outputs_markdown -v
```

Expected: PASS. The seeded store provides two battle views + a profile; `build_features` + `render_markdown` produce a brief whose "あなたのデッキ" section header appears in `result.output`, exit 0.

- [ ] **Step 5: Write a second failing test — `--json-out` writes valid JSON.**

Add to `tests/test_cli_analyze.py`:

```python
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
```

- [ ] **Step 6: Run the JSON test and expect PASS (no impl change needed).**

```
pytest tests/test_cli_analyze.py -v
```

Expected: both tests PASS. `--json-out` writes `json.dumps(render_json(features))` to `brief.json`; `json.load` parses it into a dict and `sample_size == 2` (two seeded battles). Markdown is still echoed.

- [ ] **Step 7: Commit (only this task's files).**

```
git add src/royale_analytics/cli.py tests/test_cli_analyze.py
git commit -m "feat: add analyze command"
```

### Task 23: SKILL.md for royale-analyzer (Phase 8, commit type: docs)

**Files:**
- Create: `.claude/skills/royale-analyzer/SKILL.md`
- Test: `tests/test_skill_md.py`

**Interfaces:**
- Consumes: CLI commands `ra init` / `ra fetch` / `ra analyze` (from `royale_analytics.cli:cli`, Tasks 20–22); the analysis brief produced by `render_markdown` / `render_json` (`royale_analytics.brief`, Tasks 18–19). No Python symbols are imported by SKILL.md itself; the file is documentation/orchestration.
- Produces: `.claude/skills/royale-analyzer/SKILL.md` — a Claude Code skill manifest with YAML frontmatter (`name: royale-analyzer`, `description: ...`), an orchestration section (`ra init` on first run → `ra fetch` → `ra analyze` → read the emitted brief), the verbatim 8-point 局所解回避ルーブリック, the explicit 推測 (not 実測) labelling rule, a Japanese final-report instruction, and the verbatim Supercell disclaimer.

Steps:

- [ ] **Step 1: Write `tests/test_skill_md.py`.**
  Create `tests/test_skill_md.py` with EXACTLY this content:

```python
from __future__ import annotations

from pathlib import Path

SKILL_PATH = (
    Path(__file__).resolve().parent.parent
    / ".claude" / "skills" / "royale-analyzer" / "SKILL.md"
)


def test_skill_md_exists():
    assert SKILL_PATH.is_file(), f"SKILL.md not found at {SKILL_PATH}"


def test_skill_md_contains_required_substrings():
    text = SKILL_PATH.read_text(encoding="utf-8")
    for needle in [
        "royale-analyzer",
        "ra fetch",
        "ra analyze",
        "局所解",
        "推測",
        "not endorsed by Supercell",
    ]:
        assert needle in text, f"missing substring: {needle!r}"
```

- [ ] **Step 2: Run it, expect FAIL.**
  Run:
  ```
  pytest tests/test_skill_md.py -v
  ```
  Expected: FAIL. `.claude/skills/royale-analyzer/SKILL.md` does not exist yet, so `test_skill_md_exists` fails the `is_file()` assert and `test_skill_md_contains_required_substrings` errors with `FileNotFoundError` on `read_text`.

- [ ] **Step 3: Create the SKILL.md (full content).**
  Create `.claude/skills/royale-analyzer/SKILL.md` with EXACTLY this content:

```markdown
---
name: royale-analyzer
description: クラッシュロワイヤルの自分の対戦履歴を取得・蓄積・集計し、局所解に陥らない多様な次アクションを根拠付きで提案する OSS 分析スキル。ユーザーが「クラロワを分析して」「対戦データを見て」「デッキの弱点を知りたい」等と求めたとき、決定論的 Python コア（CLI `ra`）でブリーフを生成し、局所解回避ルーブリックに従って日本語レポートを作成する。
---

# Royale Analyzer

あなた（Claude）は、ローカルの決定論的 Python コア（CLI: `ra`）が出力した「分析ブリーフ」を読み、**局所解に陥らない**定性分析と提案を日本語で生成する。算術や集計はやり直さない。Python が固めた「事実」を解釈・発想することに集中する。

## 役割分担

- **Python コア（`ra` コマンド）= 再現可能な事実**: 取得・蓄積・特徴量算出・ブリーフ出力。
- **あなた（Claude セッション）= 解釈・発想**: ブリーフを読み、ルーブリックに従って複数仮説を広げ、日本語レポートにする。

## オーケストレーション手順

必ず次の順序で CLI を実行し、最後に出力されたブリーフを読んでから分析する。

1. **初回のみ `ra init`**: 設定（トークン・タグ）を検証し、DB を初期化する。403 が出た場合は、proxy 利用時に固定 IP `45.79.218.79` を developer.clashroyale.com のキーにホワイトリスト登録するようユーザーへ案内する。`ra init` が成功している既存環境では再実行不要。
2. **`ra fetch`**: プロフィール＋ battlelog（＋ upcomingchests）を取得し、重複排除して SQLite に追記する。出力の「新規取得数」と「ギャップ警告（取りこぼし疑い）」を確認する。
3. **`ra analyze`**: 蓄積から特徴量を算出し、分析ブリーフを出力する。人間向け Markdown（俯瞰サマリ）と LLM 向け JSON（事実データ＋メタ情報）が出る。必要なら `ra analyze --json-out <path>` で JSON をファイルに保存する。
4. **ブリーフを読む**: `ra analyze` が出力したブリーフ（Markdown と JSON）を必ず読む。標本サイズ・ギャップ警告・ラダー/ランク区別・「実測/推測」フラグを把握してから分析を始める。

ブリーフに含まれる事実: あなたのデッキ（8枚・役割内訳・平均エリ・アーキタイプ・弱点タグ・テンプレ照合）、相性表（自分 vs 相手アーキタイプ別の勝敗、ラダー/ランク分離）、負け方パターン（3クラウン負け・接戦負け）、レベル差、elixirLeaked 統計、標本サイズとギャップ警告。

## 局所解回避ルーブリック

以下はあなたが必ず従う分析作法であり、本ツールの中核価値である。8点すべてを毎回適用する。

1. **単一の処方箋を出さない。** 各弱点に対し最低3つの異なる方向性の仮説・対策を、根拠とトレードオフ付きで並べる。
2. **デッキ変更に偏らせない。** 対策を「デッキ構成」「カードレベル」「立ち回り(推測)」「メンタル/標本」の複数カテゴリに意図的に分散させる。
3. **確証バイアスを排す。** 結論前に「この負けはレベル差/相性/運のどれでも説明できるか」を自問し、複数原因を併記する。
4. **証拠と強さを明示。** 各主張に「何戦中何戦か」を添える。標本が小さい時は断定せず「仮説」と明言。
5. **ラダーとランクを分離。** ラダーの負け越しはレベル不足の交絡かもしれない点を常に考慮。ランク/チャレンジは技量寄りと扱う。
6. **推測と実測を区別。** 立ち回り・elixirLeaked 由来の話は「推測であり試合中の実測ではない」と毎回明示。
7. **無課金現実的・進行連動。** 助言は実カードレベルと upcomingchests を踏まえ、実行可能な手順に落とす。
8. **プレイヤーの語彙で語る。** ポジティブトレード/カウンタープッシュ/out-cycle/プッシュの捌き等、実用語で説明。

## 推測と実測の区別（必須）

立ち回りに関する示唆と `elixirLeaked`（エリ漏れ）由来の示唆は、**必ず「推測」とラベル付けする**。公式 API には試合中のフレーム単位テレメトリが存在せず、立ち回りを「実測」することは**不可能**である。`elixirLeaked` は唯一の機械的なスキル指標だが、これも因果ではなく傾向のヒントに過ぎないため「推測」として扱う。crowns 由来の勝敗・相性表・レベル差など Python が集計した数値は「実測（事実）」として扱ってよい。レポート内で両者を取り違えてはならない。

## 最終アウトプット（日本語レポート）

ブリーフを読み終えたら、ユーザーに日本語で次の形式のレポートを提示する。各主張に「実測/推測」を明記し、証拠（何戦中何戦か）を添える。例:

```
# クラロワ分析レポート（標本: 過去 N 戦 / ラダー A 戦・ランク B 戦）

## あなたのデッキ
- アーキタイプ: cycle（Hog 2.6 Cycle と exact 一致）／平均エリ 2.6（実測）
- 弱点タグ: weak-to-swarm, single-win-condition（実測: リファレンス照合）

## 苦手な相性（実測）
- vs beatdown: 2勝6敗（ラダー）。理論上は out-cycle 可能だが実績は負け越し。
- vs siege: 1勝3敗（ランク）。標本が小さく仮説段階。

## 負け方パターン（実測）
- 3クラウン負け 3戦／12敗。大型プッシュを止め切れていない可能性。

## 弱点ごとの複数仮説（局所解回避）
### 弱点: beatdown に負け越し
- [デッキ構成] Cannon → Tesla 等で対空・タンク受けを強化（トレードオフ: 防衛偏重で攻め手が減る）。
- [カードレベル] Musketeer がレベル差 -2（実測）。Inferno 役の火力不足の交絡かもしれない。
- [立ち回り(推測)] 逆サイド committ を punish できていない可能性（※推測。試合中の実測ではない）。
- [メンタル/標本] 8戦と小さく、運/マッチング偏りの可能性も否定できない。

## 次アクション（無課金現実的・進行連動）
- upcomingchests を踏まえ、Musketeer のレベル上げを優先（実行可能な手順）。
```

ルーブリックの全8点を満たし、単一の処方箋に収束させないこと。最後にユーザーと深掘りの対話を続ける。

## 免責

This material is unofficial and is not endorsed by Supercell. For more information see Supercell's Fan Content Policy: www.supercell.com/fan-content-policy.
```

- [ ] **Step 4: Run the test, expect PASS.**
  With both `.claude/skills/royale-analyzer/SKILL.md` (Step 3) and `tests/test_skill_md.py` (Step 1) in place, run:
  ```
  pytest tests/test_skill_md.py -v
  ```
  Expected: PASS — `test_skill_md_exists` and `test_skill_md_contains_required_substrings` both pass. The file exists and contains every required substring: `royale-analyzer` (frontmatter name + title), `ra fetch`, `ra analyze` (orchestration), `局所解` (rubric heading), `推測` (推測/実測 rule), and `not endorsed by Supercell` (verbatim disclaimer).

- [ ] **Step 5: Commit (docs).**
  Stage ONLY this task's files and commit with the Conventional Commit type `docs` from the phase table:
  ```
  git add .claude/skills/royale-analyzer/SKILL.md tests/test_skill_md.py
  git commit -m "docs: add royale-analyzer SKILL.md with orchestration and local-optimum-avoidance rubric"
  ```

---

## Known Limitations / Deliberate Omissions (MVP)

- **試合内タイムライン依存のパターンは決定論的特徴量にしない。** 「ダブルエリ逆転負け」などは API に時系列が無いため計測不能。`matchups` と `weakness_tags` を材料に、SKILL.md の局所解回避ルーブリックが「推測」として扱う。
- **細かい弱点クラスタは定性的に導く。** 「対空デッキ相手に負けが集中」等は専用の決定論クラスタを作らず、`derive_matchups`（相手アーキタイプ別勝敗）＋ `classify_deck` の `weakness_tags` を材料に Claude が導く。
- **match_deck のタイは反復順依存。** template_decks を順に走査し strict `>` で最大 overlap を採用するため、Hog/X-Bow のように共有カードが多いデッキ同士のタイは反復順に依存する。`match_deck` 実装にこの旨のコメントを残すこと。
- **reference ローダは editable install 前提。** 同梱 `reference/` を `__file__` 基準で読むため、MVP は `pip install -e .` 前提。非 editable/zip install では package-data 解決の追加対応が将来必要。
- **get_cards は MVP 未使用。** 契約には含むが分析フローでは呼ばない（将来「未所持カード」分析用の予約 API）。

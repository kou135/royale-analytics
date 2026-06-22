# Royale Analytics — MVP 設計書

- 日付: 2026-06-22
- ステータス: 設計承認済み（実装計画の作成へ移行予定）
- スコープ: MVP（Claude Code skill 経由で使う、クラッシュロワイヤルのAI分析ツール）

---

## 1. 概要

クラッシュロワイヤル（Supercell）のプレイヤーが、自分の過去対戦データをもとに「苦手な相性・苦手なデッキ・立ち回りの傾向」を把握し、**局所解に陥らない多様な次アクション**を得るための OSS 分析ツール。

MVP は Claude Code の **skill** として動作する。決定論的な Python コアが Clash Royale 公式 API からデータを取得・蓄積・集計し、構造化した「分析ブリーフ」を出力する。Claude Code のセッションがそのブリーフを読み、明文化したルーブリックに従って定性分析と提案を生成する。

### 価値の中核
有料競合（ClashCoachAI 等）が「単一の処方箋」を出しがちなのに対し、本ツールは **複数仮説を根拠付きで広げる**こと、**OSS・無料・推論が透明**であること、**理論（テンプレ知識）と実績（自分の履歴）の突き合わせ**で差別化する。

### ゴール
- 自分の対戦履歴を蓄積し、相性別の勝敗・負け方パターン・デッキの弱点を可視化する。
- 弱点ごとに、デッキ構成・カードレベル・立ち回り（推測）・標本/運という**複数カテゴリにまたがる仮説**を、各々の根拠とトレードオフ付きで提示する。
- 無課金で現実的、かつ進行（upcomingchests）と連動した助言を出す。

### 非ゴール（MVP では扱わない）
- フレーム単位の立ち回り実測（API に試合中テレメトリが無いため**不可能**。立ち回りは推測のみ）。
- 外部メタサイトのライブ取得/スクレイピング（ToS リスク・RoyaleAPI の dev API 廃止のため）。
- 課金機能（Supercell Fan Content Policy に抵触。OSS 無料で進める）。
- 複数ユーザー同時利用を前提とした基盤（将来 UI 化時に対応）。

---

## 2. 確定した意思決定

| 項目 | 決定 | 理由 |
|---|---|---|
| 収益化方針 | OSS・無料で進める | Fan Content Policy が課金を原則禁止。差別化は透明性・無料・OSS に寄せる |
| 言語 | Python 中心 | データ分析エコシステムが豊富。将来 UI 化時もコア再利用可 |
| 分析スコープ | スタンダード | 相性集計＋負け方パターン＋デッキ評価＋無課金レベル助言＋多様な次アクション |
| 履歴の蓄積 | 実行時取得＋ SQLite 追記 | battlelog は直近約25戦しか返さない。蓄積必須。セットアップ不要を優先 |
| 立ち回り | 推測で割り切る（推測と明示） | 試合中テレメトリ不在。唯一の機械的指標は `elixirLeaked` のみ |
| アーキテクチャ | 案A: 決定論 Python ＋ セッション Claude | 再現性と将来 UI 化の両立。プロンプト改善が速い |
| DB | SQLite（`store.py` に隔離） | 単一ユーザー・ローカル・小規模。将来 PostgreSQL 移行可能に |
| テンプレ知識ベース | ハイブリッド | アーキタイプ単位の普遍知識＋厳選定番デッキ＋履歴からのデータ駆動認識 |

---

## 3. 調査で判明した制約（設計の前提）

公式 API（`https://api.clashroyale.com/v1`）に関する重要事実:

- **認証**: `Authorization: Bearer <JWT>`。トークンは developer.clashroyale.com で無料発行、失効まで永続。
- **IP ホワイトリスト問題**: トークンは作成時に登録した IP に固定。動的 IP では 403 になる。回避策＝ **RoyaleAPI proxy**: 鍵作成時に固定 IP `45.79.218.79` を登録し、リクエスト先を `https://proxy.royaleapi.dev`（`/v1/...` はそのまま、同じ Bearer トークン）にする。
- **プレイヤータグ**: `#` は `%23` に URL エンコード。有効文字は `0289CGJLPQRUVY`（`O` は無い→`0` に変換）。
- **battlelog の保持制約**: 直近**約25戦のみ**。ページング・履歴・期間指定エンドポイントは存在しない。古い試合は消える。第三者の深い履歴アーカイブも無い → **ローカル蓄積が必須**。
- **battlelog のデータ**: カードごとに `elixirCost`・`rarity`・`level`・`evolutionLevel`・`id` がインライン → 1回の呼び出しで平均エリ・レア構成・レベル差まで算出可能（`/cards` 結合不要）。勝敗フラグは無く `crowns` 比較で導出。`elixirLeaked` が唯一の機械的スキル指標。
- **`battleTime` 形式**: 非標準の `yyyyMMddTHHmmss.SSSZ`（例 `20260502T021910.000Z`）。専用パーサが必要（`%Y%m%dT%H%M%S.%fZ`）。
- **レート制限**: 秒間クォータ（具体値は非公開）。`x-ratelimit-*` ヘッダを実行時に読む。超過は 429。単一プレイヤー分析では実質非問題。
- **法的**: Fan Content Policy は課金を原則禁止（例外: 広告・寄付・人的コーチング）。商標を製品名/ドメインに使わない。必須免責文の表示が必要。

---

## 4. アーキテクチャ（案A）

2層構成。

1. **Python コア（決定論エンジン）**: パッケージ＋ CLI。「取得 → 蓄積 → 特徴量算出 → 分析ブリーフ出力」までを担う。再現可能な「事実」だけを扱う。
2. **Skill 層（SKILL.md）**: Claude Code セッションに「CLI 実行 → ブリーフ読込 → 局所解回避ルーブリックで定性分析 → 日本語レポート生成」を指示する。「判断・発想」を担う。

**分担**: Python = 再現可能な事実、Claude = 解釈・発想。Claude は多数試合の算術をやり直さず中核価値に集中する。

### 命名（商標回避）
- Python パッケージ: `royale_analytics`
- CLI コマンド: `ra`
- skill ID: `royale-analyzer`

いずれも "Clash" / "Clash Royale" の商標を製品名に含めない。

---

## 5. リポジトリ構成

```
royale-analytics/
  README.md                      # Supercell免責文・セットアップ手順
  pyproject.toml                 # パッケージ + CLIエントリ (依存: httpx, click)
  .env.example                   # トークン等のサンプル
  .gitignore                     # .env, data/ を除外
  src/royale_analytics/
    config.py        # env読込(トークン/base URL/タグ/DBパス)
    tags.py          # タグ正規化(#除去, 大文字化, O→0, 文字種検証, %23化)
    battletime.py    # 独自フォーマット(%Y%m%dT%H%M%S.%fZ)のパース→UTC
    api_client.py    # httpx薄クライアント + エラー対応 + レート制御
    store.py         # SQLiteスキーマ + 重複排除upsert
    classify.py      # 8枚→役割/平均エリ/アーキタイプ/弱点タグ + match_deck()
    features.py      # 蓄積から集計(相性表/負け方/レベル差/elixirLeaked)
    brief.py         # 特徴量→分析ブリーフ(人間用Markdown + LLM用JSON)
    cli.py           # サブコマンド配線
    reference/
      card_roles.json        # カード→役割/特性タグ(自前調査データ, 日付管理)
      archetype_profiles.json# アーキタイプ単位の強み/弱み/勝ち筋(普遍・低メンテ)
      archetype_rules.json   # デッキ→アーキタイプ/弱点タグ判定ルール
      template_decks.json    # 厳選定番デッキ10〜15(名前付き, version/updated)
  .claude/skills/royale-analyzer/
    SKILL.md         # オーケストレーション + 局所解回避ルーブリック
  tests/
    fixtures/        # 実battlelogの匿名化サンプル
    test_*.py
  data/              # gitignore; SQLite実体
```

- skill は `.claude/skills/` に置きプロジェクトで自動認識。グローバル利用は `~/.claude/skills/` へコピーする手順を README に記載。
- Python パッケージは `pip install -e .` で導入し、SKILL.md からは `ra ...`（または `python -m royale_analytics ...`）で呼ぶ。

---

## 6. コンポーネント（モジュール責務）

各モジュールは単一責務・明確なインターフェース・単体テスト可能。

- **`config.py`**: env からトークン（`CLASH_ROYALE_API_TOKEN`）、base URL（`CR_API_BASE`、既定 `https://proxy.royaleapi.dev/v1`）、プレイヤータグ（`CR_PLAYER_TAG`）、DB パス（`RA_DB_PATH`、既定 `data/royale.sqlite`）を読む。
- **`tags.py`**: タグ正規化（`#` 除去、大文字化、`O`→`0`、文字種 `0289CGJLPQRUVY` 検証、リクエスト用に `%23` 化）。不正タグはリクエスト前にローカルで弾く。
- **`battletime.py`**: 独自 `battleTime` のパース/整形（`%Y%m%dT%H%M%S.%fZ`）、UTC ISO で保存。
- **`api_client.py`**: httpx 薄クライアント。`get_player` / `get_battlelog` / `get_upcoming_chests` / `get_cards`。認証ヘッダ付与、エラーを型付き例外にマップ（403/404/429/503）、`x-ratelimit-*` 読取、429 時バックオフ再試行。
- **`store.py`**: SQLite スキーマと冪等 upsert（重複排除）。DB アクセスをここに閉じ込め、将来の PostgreSQL 移行を局所化。
- **`classify.py`**: デッキ8枚 → 役割内訳・平均エリ・アーキタイプ（マクロ＋サブラベル）・弱点タグ。`match_deck()` で観測デッキを `template_decks` に曖昧マッチ（カード重複度の閾値、例 6/8 一致＝亜種）し `exact/variant/unknown` を返す。
- **`features.py`**: 蓄積から集計。crowns から勝敗導出、相性表（自分 vs 相手アーキタイプ、ラダー/ランク分離）、3クラウン負け等の負け方パターン、弱点クラスタ（例: 対空デッキ相手に負け集中）、レベル差検出、`elixirLeaked` 統計、標本サイズ・ギャップ警告。
- **`brief.py`**: 特徴量を分析ブリーフ（人間用 Markdown ＋ LLM 用 JSON）に整形。「実測/推測」フラグ・標本/ギャップ注記を含める。
- **`cli.py`**: サブコマンド配線（click）。

### CLI サブコマンド
- `ra init`: トークン検証・タグ正規化・DB 初期化。初回ガイド（鍵発行と `45.79.218.79` ホワイトリスト）。
- `ra fetch`: プロフィール＋ battlelog（＋ upcomingchests）取得 → 重複排除 → SQLite 追記。新規取得数とギャップ有無を報告。
- `ra analyze`: 蓄積から特徴量算出 → 分析ブリーフ（Markdown ＋ JSON）を出力。

---

## 7. データモデル（SQLite）

重複排除キー: **`(player_tag, battle_time, opponent_tag)`**（battle_time はミリ秒精度）。生 JSON も保存して将来のスキーマ変化に備える。

```
battles                          -- 1試合1行（重複排除済み）
  id              INTEGER PK
  player_tag      TEXT           -- 所有者
  opponent_tag    TEXT
  battle_time     TEXT  (UTC ISO, INDEX)
  type            TEXT           -- PvP / friendly ...
  game_mode_id    INTEGER
  game_mode_name  TEXT
  arena_name      TEXT
  is_ladder_tournament INTEGER   -- 0/1
  league_number   INTEGER        -- ランク判定の手がかり
  deck_selection  TEXT
  result          TEXT           -- win/loss/draw（crowns比較で導出）
  raw_json        TEXT           -- 試合まるごと（前方互換）
  UNIQUE(player_tag, battle_time, opponent_tag)

battle_sides                     -- 1試合2行（team / opponent）
  id              INTEGER PK
  battle_id       INTEGER FK
  side            TEXT           -- 'team' / 'opponent'
  tag             TEXT
  name            TEXT
  crowns          INTEGER
  starting_trophies INTEGER
  trophy_change   INTEGER        -- ラダー判定/レベル交絡の手がかり
  king_tower_hp   INTEGER  NULL
  princess_towers_hp TEXT  NULL  -- JSON配列
  elixir_leaked   REAL     NULL  -- 唯一の機械的指標（nullable）
  global_rank     INTEGER  NULL
  clan_tag        TEXT     NULL
  deck_key        TEXT           -- card_id8個をソート連結（相性集計のグループキー）

battle_cards                     -- 1試合16行（8枚×2サイド）
  id              INTEGER PK
  battle_id       INTEGER FK
  side            TEXT
  card_id         INTEGER
  card_name       TEXT
  level           INTEGER
  max_level       INTEGER        -- 上限16まで許容
  evolution_level INTEGER  NULL
  star_level      INTEGER  NULL
  rarity          TEXT
  elixir_cost     INTEGER        -- battlelogにインラインで入る

profile_snapshots                -- fetchごとのプロフィール（レベル/トロフィー推移）
  id              INTEGER PK
  player_tag      TEXT
  fetched_at      TEXT  (UTC ISO)
  trophies        INTEGER
  best_trophies   INTEGER
  raw_json        TEXT           -- 全カードコレクションのレベル等

fetch_log                        -- 取得のたびに記録（鮮度/ギャップ警告用）
  id              INTEGER PK
  player_tag      TEXT
  fetched_at      TEXT  (UTC ISO)
  new_battles     INTEGER        -- 今回新規追加できた件数
  gap_suspected   INTEGER        -- 取りこぼし疑いフラグ（25件満杯で取得など）
```

設計上の判断:
- アーキタイプ判定は DB に保存せず `analyze` 時に算出（リファレンス更新後も過去試合を再解釈できる）。グループ化用の `deck_key` だけ保存。
- `result` は crowns 比較で導出して保存（勝敗フラグは API に無い）。引き分けもあり得る。
- nullable 前提（`elixir_leaked` / `king_tower_hp` / `global_rank` / `evolution_level` 等はモード次第で欠落）。
- 投入は `INSERT OR IGNORE`（再実行しても二重登録しない＝冪等）。

---

## 8. リファレンスデータ（ハイブリッド）

カードの「役割」やデッキの強み/弱みは API が返さないため自前で持ち、日付管理する。

- **`card_roles.json`**: カード → 役割（wincon/support/defense/cycle/spell/building）と特性タグ（air-targeting/swarm/splash/building/reset/tank/ground-only 等）。`version` 付き。
- **`archetype_profiles.json`**: アーキタイプ単位の強み/弱み/勝ち筋（普遍的・低メンテ）。土台となる知識。
- **`archetype_rules.json`**: デッキ → アーキタイプ判定ルール（例: タンク有＋平均エリ高→beatdown、X-Bow/Mortar→siege、WinCon＋平均エリ<3.0→cycle）と弱点タグ導出ルール（例: 対空可能0〜1枚→weak-to-air、スプラッシュ0→weak-to-swarm、呪文なし→spell-light、WinConが1枚のみ→single-win-condition）。
- **`template_decks.json`**: 厳選定番デッキ10〜15個。各デッキに name / archetype / cards(8) / avg_elixir / win_condition / strengths / weaknesses / counters。`version` / `updated` 付き、シーズン毎に手動更新。

`template_decks.json` のスキーマ例:
```json
{
  "version": "2026-06",
  "decks": [
    {
      "name": "Hog 2.6 Cycle",
      "archetype": "cycle",
      "cards": ["Hog Rider","Ice Spirit","Ice Golem","Skeletons",
                "Musketeer","Fireball","The Log","Cannon"],
      "avg_elixir": 2.6,
      "win_condition": "Hogで継続的にタワーを削り、相手のHog対策より速くサイクルして押し切る",
      "strengths": ["高速サイクル","ポジティブトレードしやすい","防衛が固い"],
      "weaknesses": ["1枚あたりの火力が低い","重いスプラッシュに弱い","逆転の決定力が乏しい"],
      "counters": "Hogを止める建物/重スプラッシュ＋忍耐の防衛で削り切らせない"
    }
  ]
}
```

**データ駆動認識**: `analyze` 時に蓄積履歴の `deck_key` を頻度集計し、よく当たる相手デッキを「実データテンプレ」として自動抽出する。これがメタ陳腐化に強く、個人最適でもある。`match_deck()` は観測8枚を `template_decks` に曖昧マッチし、一致しなければデータ駆動テンプレ → アーキタイプ単位の順にフォールバックする。

分析では常に「**理論（テンプレ/アーキタイプ知識）× 実績（自分の履歴勝率）**」を併記し、**両者の食い違いを最重要シグナル**として扱う（例: 理論上有利だが実績は負け越し → レベル不足 or 立ち回りの問題の可能性）。

---

## 9. データフロー

```
ユーザー: 「クラロワを分析して」/ /royale-analyze
      │
      ▼
[SKILL.md がClaudeに指示]
  1. ra fetch  ── プロフィール＋battlelog取得 → 重複排除 → SQLite追記
      │         （新規N戦取得 / 取りこぼしギャップ有無を報告）
  2. ra analyze ── 蓄積を集計 → 分析ブリーフ出力
      │            ・人間用Markdown（俯瞰サマリ）
      │            ・LLM用JSON（事実データ＋メタ情報）
      ▼
[Claudeセッションがブリーフを読む]
  3. 局所解回避ルーブリックを適用して定性分析
      ▼
  4. 日本語レポートをユーザーに提示 ＋ 深掘りの対話
```

`1`〜`2` の「事実」は決定論的 Python が固める。`3`〜`4` のみが Claude の仕事。

分析ブリーフ（Python が出す事実）に含めるもの:
- あなたのデッキ: カード8枚・役割内訳・平均エリ・アーキタイプ・弱点タグ・テンプレ照合結果
- 相性表: 自分 vs 相手アーキタイプ別の勝敗（ラダー/ランク分離）
- 負け方パターン: 3クラウン負け・接戦負け・ダブルエリ逆転負け等の集計
- 弱点の証拠: 「対空デッキ相手に負けが集中」等のクラスタ
- レベル差: 自デッキ各カードのレベル vs 最大レベル
- elixirLeaked 統計: 自分の平均・相手との差・推移（※唯一の機械的指標）
- メタ情報: 標本サイズ、ギャップ警告、ラダー/ランク区別、「実測/推測」フラグ

---

## 10. 局所解回避ルーブリック（SKILL.md に明文化）

Claude が必ず従う分析作法。本ツールの中核価値。

1. **単一の処方箋を出さない。** 各弱点に対し最低3つの異なる方向性の仮説・対策を、根拠とトレードオフ付きで並べる。
2. **デッキ変更に偏らせない。** 対策を「デッキ構成」「カードレベル」「立ち回り(推測)」「メンタル/標本」の複数カテゴリに意図的に分散させる。
3. **確証バイアスを排す。** 結論前に「この負けはレベル差/相性/運のどれでも説明できるか」を自問し、複数原因を併記する。
4. **証拠と強さを明示。** 各主張に「何戦中何戦か」を添える。標本が小さい時は断定せず「仮説」と明言。
5. **ラダーとランクを分離。** ラダーの負け越しはレベル不足の交絡かもしれない点を常に考慮。ランク/チャレンジは技量寄りと扱う。
6. **推測と実測を区別。** 立ち回り・elixirLeaked 由来の話は「推測であり試合中の実測ではない」と毎回明示。
7. **無課金現実的・進行連動。** 助言は実カードレベルと upcomingchests を踏まえ、実行可能な手順に落とす。
8. **プレイヤーの語彙で語る。** ポジティブトレード/カウンタープッシュ/out-cycle/プッシュの捌き等、実用語で説明。

---

## 11. エラー処理

`api_client` で型付き例外 → 実行可能なメッセージに変換:

- **403 accessDenied** → 「トークン無効 or IP未許可。proxy 利用時は `45.79.218.79` をホワイトリスト登録、直接接続時は自分の IP で鍵を再発行」
- **404 notFound** → 「プレイヤータグを確認（`O` は `0`、`#` は不要）」※リクエスト前にローカル検証で無駄打ち回避
- **429 throttled** → `x-ratelimit-retry-after`（µs）でバックオフ → 自動再試行
- **503 inMaintenance** → 「Supercell メンテ中。後で再試行」
- **ネットワーク/タイムアウト** → 指数バックオフ再試行
- **battleTime パース失敗** → その試合だけ警告ログを残しスキップ（全体は落とさない）
- **空の battlelog/新規アカウント** → 「まだ試合がありません」を丁寧に表示
- **スキーマ揺れ耐性** → 任意フィールドは null 許容、生 JSON 保存で後追い可能

---

## 12. テスト

pytest、ネットワーク無し（クライアントはモック）。

- `tags` 正規化（O→0・文字種拒否・%23化）
- `battletime` パーサ（独自フォーマット往復・UTC）
- `store` 重複排除（再投入で冪等・複合キー）
- `classify` / `match_deck`（既知デッキ → 期待アーキタイプ/役割/平均エリ/弱点タグ・曖昧マッチ閾値）
- `features` 集計（crowns から勝敗導出・相性表・レベル差）を fixture 対戦群で
- `api_client` エラーマッピング（403/404/429/503 のモック応答）
- fixture は実 battlelog の匿名化キャプチャ（実装時にライブ取得・第14章参照）

---

## 13. コンプライアンス（コードに最初から内蔵）

- README・出力に **Supercell 必須免責文**を表示: "This material is unofficial and is not endorsed by Supercell. For more information see Supercell's Fan Content Policy: www.supercell.com/fan-content-policy."
- 非商標の製品名を採用（`royale-analytics` / `ra` / `royale-analyzer`）。
- カード画像は API の `iconUrls` を使用（公式アートを再ホストしない）。
- 課金しない（OSS 無料）。将来の収益化は広告/寄付のみ検討。
- ライセンス: MIT 想定（実装着手時に確定）。

---

## 14. 実装着手前に確認/検証すべき事項

1. **ライブの battlelog スキーマ**を実取得し、それからデータモデルを確定（古いラッパーは `elixirCost` 等を欠く）。
2. proxy IP `45.79.218.79` が現行か（過去1度変更あり）・公開 proxy が独自レート制限を足すか。
3. battlelog の実際の返却件数（「約25」は観測上限）。
4. 現行 `maxLevel`（15 or 16）。
5. `template_decks.json` 初期版の現環境デッキ選定（要・現メタ確認）。
6. API 利用規約(ToS) の逐語確認（再配布・帰属）※将来の配布前まで。

---

## 15. 将来ロードマップ（MVP 後）

- **UI 化（Web）**: 決定論 Python コアを再利用。分析部をセッション Claude → 同梱の LLM API 呼び出しに差し替え（案C へ自然進化）。
- **DB 移行**: 複数ユーザー同時利用が必要になれば `store.py` 差し替えで PostgreSQL へ。
- **常時収集**: cron/launchd による定期ポーリングで取りこぼし削減（オプション）。
- **収益化**: 課金は不可。広告/寄付のみ検討。
- **テンプレ KB の自動化**: 蓄積した相手デッキから流行デッキを半自動抽出し、curated KB を補強。
- **分析の拡張**: 外部メタ照合（取得手段の整理後）、時系列トレンド、複数デッキ運用比較（Ambitious スコープ）。

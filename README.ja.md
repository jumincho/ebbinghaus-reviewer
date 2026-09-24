<div align="center">

🇺🇸 [English](README.md) | 🇨🇳 [简体中文](README.zh-CN.md) | 🇭🇰 [繁體中文](README.zh-HK.md) | 🇯🇵 **日本語** | 🇰🇷 [한국어](README.ko.md)

<img src="src/ebbinghaus_reviewer/web/static/icon.svg" width="64" height="64" alt="">

# Ebbinghaus Reviewer

**学んだことを忘却曲線に沿って復習できる、間隔反復のコマンドラインツールとローカル Web アプリです。**

[![CI](https://github.com/jumincho/ebbinghaus-reviewer/actions/workflows/ci.yml/badge.svg)](https://github.com/jumincho/ebbinghaus-reviewer/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%E2%80%933.14-3776AB?logo=python&logoColor=white)
![Typed](https://img.shields.io/badge/typing-mypy%20strict-2A6DB2)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

<img src="docs/screenshots/today.png" width="49%" alt="今日（Today）ページ：統計と復習期限が来た項目">
<img src="docs/screenshots/review.png" width="49%" alt="4 つの評価ボタンを備えた、ダークモードの復習（Review）ページ">

</div>

## 概要

何かを学んだら、すぐに記録しましょう。Ebbinghaus Reviewer は、ちょうど忘れかけた頃にその内容を復習として再び出題します。最初は **10 分**後、続いて **1 日**後、**1 週間**後、**1 か月**後です。また、毎日どの項目が復習期限を迎えるかを知らせてくれます。復習のたびに「もう一度」（*again*）、「難しい」（*hard*）、「正解」（*good*）、「簡単」（*easy*）のいずれかで評価すると、それに合わせてスケジュールが調整されます。

## 機能

- **2 種類のスケジューリング戦略。** 固定の *Ebbinghaus ラダー*（10 分 → 1 日 → 1 週間 → 1 か月、その後は習得済み）と適応型の *SM-2* のどちらかを、項目ごとに選べます。
- **ターミナルでのワークフロー。** `add`、`due`、対話式の `review`、`agenda`、`stats`、`show`、`edit`、`restart` などのコマンドがあり、結果は読みやすい表で表示されます。
- **ローカル Web アプリ。** ダッシュボード、思い出そうとするまでメモを隠しておく復習画面、復習履歴と忘却曲線のグラフを表示する項目ページ、そして予定表を備えています。JavaScript なしでも動作し、ダークモードにも対応しています。
- **復習ログ。** 復習のたびに、その評価と、期限より早かったか遅かったかが記録されます。連続復習日数と 30 日間の想起率は、この記録をもとに算出されます。
- **ローカルファースト。** データはユーザーデータディレクトリにある 1 つの SQLite ファイルだけです。バックアップや別のマシンへの移行に使える、バージョン付きの JSON エクスポート／インポートも備えています。
- **長期的な保守を見据えた設計。** スケジューリングのルールは純粋関数で、プロパティベーステストで検証されています。スキーマはマイグレーションでバージョン管理され、型は mypy の strict モードをパスし、CI は Python 3.10–3.14 をカバーしています。

## クイックスタート

```bash
pip install "ebbinghaus-reviewer[web] @ git+https://github.com/jumincho/ebbinghaus-reviewer"

ebbinghaus demo      # 任意：お試し用のサンプルコレクションを読み込む
ebbinghaus due       # 今、何を復習すべき？
ebbinghaus review    # 復習する
ebbinghaus serve     # Web アプリ（http://127.0.0.1:8000）
```

コマンドラインだけを使う場合は、`[web]` を省いてください。`demo` コマンドは空のコレクションでのみ実行できます。別のファイルで試すには `--db demo.sqlite3` を指定してください。

## コマンドライン

サンプルコレクションでのセッション例：

```text
$ ebbinghaus add "Pythagorean theorem" --notes "a² + b² = c²" --subject Math
Added #9 Pythagorean theorem - first review in 10 min.

$ ebbinghaus due
Due now (3)
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ ID ┃ Item                                       ┃ Schedule   ┃ Next review ┃ Recall* ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━┩
│  2 │ Krebs cycle: the eight intermediates in    │ ladder 3/4 │ 1 day ago   │     89% │
│    │ order  Biology                             │            │             │         │
│  3 │ Binary heap: cost of push and pop          │ SM-2 rep 2 │ 2 h ago     │     90% │
│    │ Algorithms                                 │            │             │         │
│  7 │ Korean spelling: 되 vs 돼  Korean          │ ladder 2/4 │ 50 min ago  │     90% │
└────┴────────────────────────────────────────────┴────────────┴─────────────┴─────────┘
*estimated probability of recall right now

$ ebbinghaus review --limit 1
1 to review. Grades: [a]gain  [h]ard  [g]ood  [e]asy; [s]kip, [q]uit.
╭──────────────────────────────────── #2 · Biology ────────────────────────────────────╮
│ Krebs cycle: the eight intermediates in order                                        │
╰───────────────────── 1/1 · ladder · step 3 of 4 · due 1 day ago ─────────────────────╯
Recall it, then press Enter to see your notes:
╭─────────────────────────────────────── Notes ────────────────────────────────────────╮
│ Citrate, isocitrate, alpha-ketoglutarate, succinyl-CoA, succinate, fumarate, malate, │
│ oxaloacetate.                                                                        │
╰──────────────────────────────────────────────────────────────────────────────────────╯
Grade: g
good - next review in 1 month (Fri 23 Oct 16:49).
Reviewed 1 item.

$ ebbinghaus agenda --days 7
Today 2026-09-23
  overdue  #3 Binary heap: cost of push and pop Algorithms
  overdue  #7 Korean spelling: 되 vs 돼 Korean
    16:54  #8 French: 'être' in the passé simple French
    16:59  #9 Pythagorean theorem Math
Friday 2026-09-25
    16:49  #5 Treaty of Westphalia History
...
```

| コマンド | 説明 |
| --- | --- |
| `ebbinghaus add TITLE [-n NOTES] [-s SUBJECT] [--strategy ladder\|sm2] [--studied WHEN]` | 学んだ内容を記録します（`--studied "2h ago"` で過去の学習をさかのぼって記録できます）。 |
| `ebbinghaus due [-s SUBJECT] [--limit N]` | 期限が来ている項目を、期限を大きく過ぎたものから順に一覧表示します。 |
| `ebbinghaus review [ID] [-s SUBJECT] [--limit N]` | 期限が来た項目を 1 つずつ復習し、それぞれを a / h / g / e で評価します。 |
| `ebbinghaus grade ID {again,hard,good,easy}` | 対話式のプロンプトを使わずに復習結果を記録します。 |
| `ebbinghaus list [-s SUBJECT] [--active]` | すべての項目とそのスケジュールを表示します。 |
| `ebbinghaus show ID` | 1 つの項目を、すべての復習履歴とともに表示します。 |
| `ebbinghaus agenda [--days N]` | 今後の復習予定を日ごとに表示します。 |
| `ebbinghaus stats` | 合計数、期限が来た項目数、連続復習日数、30 日間の想起率を表示します。 |
| `ebbinghaus edit ID [--title] [--notes] [--subject \| --clear-subject]` | 項目のテキストを変更します。スケジュールはそのまま保持されます。 |
| `ebbinghaus restart ID [--strategy ...]` | 項目のスケジュールを最初からやり直します。必要に応じて戦略も切り替えられます。 |
| `ebbinghaus delete ID [-y]` | 項目とその履歴を削除します。 |
| `ebbinghaus export [-o FILE]` / `ebbinghaus import FILE` | コレクションを JSON でバックアップ・復元します。 |
| `ebbinghaus demo` | 空のデータベースにサンプルコレクションを読み込みます。 |
| `ebbinghaus serve [--host] [--port]` | Web アプリを起動します（`web` extra が必要です）。 |

すべてのコマンドで `--help` を使えます。コレクションは、プラットフォームごとのユーザーデータディレクトリ（たとえば Linux では `~/.local/share/ebbinghaus-reviewer/`）に保存されます。複数のコレクションを使い分けるには、`--db` または環境変数 `EBBINGHAUS_DB` で別のファイルを指定してください。

## Web アプリ

`ebbinghaus serve` は、コマンドラインと同じ SQLite ファイルを使うローカル Web アプリを起動します。そのため、ターミナルで記録し、ブラウザーで復習するといった使い方ができます。ページは、統計・期限が来た項目・クイック追加をまとめた**今日**（*Today*）、カードを 1 枚ずつ表示し、開くまでメモを隠しておく**復習**（*Review*）、科目で絞り込める**項目一覧**（*Items*）、スケジュール・履歴・編集・やり直しを扱う**項目ページ**、そして**予定表**（*Agenda*）です。

<p align="center">
  <img src="docs/screenshots/item.png" width="80%" alt="スケジュール情報と忘却曲線のグラフを表示した項目ページ">
</p>

このアプリは自分のマシンで使うためのものです。`127.0.0.1` で待ち受け、アカウント機能もないため、信頼できないネットワークには公開しないでください。

## スケジューリングの仕組み

```text
ladder:  studied ─10 min─▶ ✓ ─1 day─▶ ✓ ─1 week─▶ ✓ ─1 month─▶ ✓ ─▶ mastered
```

| 評価 | ラダー | SM-2 |
| --- | --- | --- |
| もう一度（*again*） | 最初の段に戻る | 1 日の間隔からやり直し、容易度係数（ease factor）は維持 |
| 難しい（*hard*） | 現在の段を繰り返す | 合格扱い、容易度係数 −0.14 |
| 正解（*good*） | 1 段上がる | 合格扱い、容易度係数は変わらない |
| 簡単（*easy*） | 2 段上がる | 合格扱い、容易度係数 +0.10 |

SM-2 の間隔は 1 日、6 日と進み、その後は前回の間隔 × 容易度係数を切り上げた値になります。想起確率の推定では、項目の期限ちょうどに 90% に達する指数関数的な忘却曲線を仮定しています。[`docs/algorithm.md`](docs/algorithm.md) には完全なルール、計算例、参考文献が記載されており、[`docs/architecture.md`](docs/architecture.md) ではレイヤー構成、データモデル、時刻の扱いを説明しています。

## プロジェクト構成

```text
ebbinghaus-reviewer/
├── src/ebbinghaus_reviewer/
│   ├── scheduling.py     # 評価、ラダーと SM-2 の各戦略（純粋関数）
│   ├── retention.py      # 忘却曲線の推定
│   ├── models.py         # Item, Review, Stats, AgendaDay
│   ├── storage.py        # スキーママイグレーション付きの SQLite リポジトリ
│   ├── service.py        # Reviewer：CLI と Web で共有するユースケース
│   ├── transfer.py       # バージョン付き JSON エクスポート／インポート
│   ├── presentation.py   # 共通の表示ラベル
│   ├── cli.py            # `ebbinghaus` コマンド
│   ├── demo.py           # サンプルコレクション
│   └── web/              # FastAPI アプリ、Jinja2 テンプレート、CSS
├── tests/                # pytest + Hypothesis、レイヤーごとに 1 モジュール
├── docs/                 # アルゴリズム、アーキテクチャ、スクリーンショット、発表スライド
└── pyproject.toml
```

## 開発

```bash
git clone https://github.com/jumincho/ebbinghaus-reviewer
cd ebbinghaus-reviewer
python -m pip install -e ".[web]" --group dev   # pip >= 25.1 が必要（依存関係グループ）

pytest --cov        # テスト
ruff check .        # リント
ruff format .       # フォーマット
mypy                # 厳格な型チェック
```

## ライセンス

[MIT](LICENSE) © 2021 jumincho

<div align="center">

🇺🇸 **English** | 🇨🇳 [简体中文](README.zh-CN.md) | 🇭🇰 [繁體中文](README.zh-HK.md) | 🇯🇵 [日本語](README.ja.md) | 🇰🇷 [한국어](README.ko.md)

<img src="src/ebbinghaus_reviewer/web/static/icon.svg" width="64" height="64" alt="">

# Ebbinghaus Reviewer

**Review what you study along the forgetting curve: a spaced-repetition command line and local web app.**

[![CI](https://github.com/jumincho/ebbinghaus-reviewer/actions/workflows/ci.yml/badge.svg)](https://github.com/jumincho/ebbinghaus-reviewer/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%E2%80%933.14-3776AB?logo=python&logoColor=white)
![Typed](https://img.shields.io/badge/typing-mypy%20strict-2A6DB2)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

<img src="docs/screenshots/today.png" width="49%" alt="Today page: statistics and items due for review">
<img src="docs/screenshots/review.png" width="49%" alt="Review page in dark mode with the four grade buttons">

</div>

## Overview

Right after you study something, log it. Ebbinghaus Reviewer brings it back for
review just as you are about to forget it, first after **10 minutes**, then
**1 day**, **1 week** and **1 month**, and tells you what is due each day. Grade
every review *again*, *hard*, *good* or *easy*, and the schedule adapts.

## Features

- **Two scheduling strategies.** The fixed *Ebbinghaus ladder* (10 min → 1 day →
  1 week → 1 month, then mastered) or adaptive *SM-2*, per item.
- **Terminal workflow.** Use `add`, `due`, an interactive `review`, `agenda`,
  `stats`, `show`, `edit`, `restart` and more, with readable tables.
- **Local web app.** A dashboard, a review screen that hides your notes until
  you have tried to recall, item pages with review history and a
  forgetting-curve chart, and an agenda. It works without JavaScript and in
  dark mode.
- **Review log.** Every review is recorded with its grade and whether it was
  early or late, which drives streaks and the 30-day recall rate.
- **Local-first.** Your data is one SQLite file in your user data directory,
  with versioned JSON export/import for backups or moving machines.
- **Engineered to last.** The scheduling rules are pure and property-tested.
  The schema is versioned with migrations, types pass strict mypy, and CI
  covers Python 3.10–3.14.

## Quickstart

```bash
pip install "ebbinghaus-reviewer[web] @ git+https://github.com/jumincho/ebbinghaus-reviewer"

ebbinghaus demo      # optional: load a sample collection to explore
ebbinghaus due       # what should I review now?
ebbinghaus review    # review it
ebbinghaus serve     # the web app at http://127.0.0.1:8000
```

Leave out `[web]` if you only want the command line. The `demo` command only
runs on an empty collection; pass `--db demo.sqlite3` to try it in a separate
file.

## Command line

A session on the sample collection:

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

| Command | What it does |
| --- | --- |
| `ebbinghaus add TITLE [-n NOTES] [-s SUBJECT] [--strategy ladder\|sm2] [--studied WHEN]` | Log something you studied (`--studied "2h ago"` to backfill). |
| `ebbinghaus due [-s SUBJECT] [--limit N]` | List what is due now, most overdue first. |
| `ebbinghaus review [ID] [-s SUBJECT] [--limit N]` | Review due items one by one, grading each with a / h / g / e. |
| `ebbinghaus grade ID {again,hard,good,easy}` | Record a review without the interactive prompt. |
| `ebbinghaus list [-s SUBJECT] [--active]` | All items and their schedules. |
| `ebbinghaus show ID` | One item with its full review history. |
| `ebbinghaus agenda [--days N]` | Upcoming reviews day by day. |
| `ebbinghaus stats` | Totals, due counts, streak and 30-day recall rate. |
| `ebbinghaus edit ID [--title] [--notes] [--subject \| --clear-subject]` | Change an item's text; its schedule is kept. |
| `ebbinghaus restart ID [--strategy ...]` | Start an item's schedule over, optionally switching strategy. |
| `ebbinghaus delete ID [-y]` | Delete an item and its history. |
| `ebbinghaus export [-o FILE]` / `ebbinghaus import FILE` | Back up or restore the collection as JSON. |
| `ebbinghaus demo` | Load the sample collection into an empty database. |
| `ebbinghaus serve [--host] [--port]` | Run the web app (needs the `web` extra). |

Every command has `--help`. The collection lives in your platform's user data
directory (for example `~/.local/share/ebbinghaus-reviewer/` on Linux); point
`--db` or the `EBBINGHAUS_DB` environment variable at another file to use
several collections.

## Web app

`ebbinghaus serve` starts a local web app over the same SQLite file as the
command line, so you can log in the terminal and review in the browser. Pages:
**Today** (statistics, due items, quick add), **Review** (one card at a time,
notes hidden until you open them), **Items** (filter by subject), an **item
page** (schedule, history, edit and restart) and the **Agenda**.

<p align="center">
  <img src="docs/screenshots/item.png" width="80%" alt="Item page with schedule facts and the forgetting-curve chart">
</p>

The app is meant for your own machine. It listens on `127.0.0.1` and has no
accounts, so don't expose it to a network you don't trust.

## How scheduling works

```text
ladder:  studied ─10 min─▶ ✓ ─1 day─▶ ✓ ─1 week─▶ ✓ ─1 month─▶ ✓ ─▶ mastered
```

| Grade | Ladder | SM-2 |
| --- | --- | --- |
| again | back to the first rung | restart at a 1-day interval, ease factor kept |
| hard | repeat the current rung | pass; ease factor −0.14 |
| good | climb one rung | pass; ease factor unchanged |
| easy | climb two rungs | pass; ease factor +0.10 |

SM-2 intervals go 1 day, 6 days, then the previous interval × the ease factor,
rounded up. The recall estimate assumes an exponential forgetting curve that
reaches 90% exactly when an item is due. [`docs/algorithm.md`](docs/algorithm.md)
has the full rules, a worked example and references, and
[`docs/architecture.md`](docs/architecture.md) describes the layers, data model
and time handling.

## Project structure

```text
ebbinghaus-reviewer/
├── src/ebbinghaus_reviewer/
│   ├── scheduling.py     # grades, ladder and SM-2 strategies (pure)
│   ├── retention.py      # forgetting-curve estimate
│   ├── models.py         # Item, Review, Stats, AgendaDay
│   ├── storage.py        # SQLite repository with schema migrations
│   ├── service.py        # Reviewer: the use cases shared by CLI and web
│   ├── transfer.py       # versioned JSON export / import
│   ├── presentation.py   # shared display labels
│   ├── cli.py            # the `ebbinghaus` command
│   ├── demo.py           # sample collection
│   └── web/              # FastAPI app, Jinja2 templates, CSS
├── tests/                # pytest + Hypothesis, one module per layer
├── docs/                 # algorithm, architecture, screenshots, presentation slides
└── pyproject.toml
```

## Development

```bash
git clone https://github.com/jumincho/ebbinghaus-reviewer
cd ebbinghaus-reviewer
python -m pip install -e ".[web]" --group dev   # pip >= 25.1 (dependency groups)

pytest --cov        # tests
ruff check .        # lint
ruff format .       # format
mypy                # strict type check
```

## License

[MIT](LICENSE) © 2021 jumincho

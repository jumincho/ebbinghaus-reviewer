<div align="center">

# ebbinghaus-reviewer

**A spaced-repetition study reviewer grounded in the Ebbinghaus forgetting curve.**
Cross-platform Python CLI + local web UI, sharing one SQLite store.

[![CI](https://github.com/jumincho/ebbinghaus-reviewer/actions/workflows/ci.yml/badge.svg)](https://github.com/jumincho/ebbinghaus-reviewer/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![Code style: ruff](https://img.shields.io/badge/style-ruff-261230)](https://docs.astral.sh/ruff/)
[![Types: mypy](https://img.shields.io/badge/types-mypy_strict-2A6DB2)](https://mypy.readthedocs.io/)

</div>

---

Add a study item, recall it on demand, and the app schedules the next review at
a curve-aligned interval — closer if you struggled, farther if you nailed it.
Storage is a single SQLite file on your machine; the same data is reachable
from both the CLI and the local web UI.

## Quick start

```bash
# Install
pip install -e .

# Add a card
ebbinghaus add "What does the Ebbinghaus forgetting curve describe?" \
  -b "Exponential decay of memory retention over time without review." \
  -t psych -t memory

# See what's due now
ebbinghaus today

# Review interactively (one card or all due)
ebbinghaus review 1

# Open the web UI on http://127.0.0.1:8000
ebbinghaus serve
```

That's the whole tour. The same `db.sqlite` is shared between the CLI and the
web UI, so you can capture cards on the command line and review them in the
browser, or vice versa.

## CLI in 10 seconds

```
$ ebbinghaus today
                                Due now (2)
┏━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ # ┃ Front                                    ┃ Tags          ┃ Was due  ┃
┡━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ 1 │ What does the Ebbinghaus curve describe? │ psych, memory │ just now │
│ 2 │ Who introduced SM-2?                     │ algo          │ just now │
└───┴──────────────────────────────────────────┴───────────────┴──────────┘

$ ebbinghaus review 1
─── Card #1 ───
What does the Ebbinghaus curve describe?
tags: psych, memory

Press Enter to reveal answer:
> Exponential decay of memory retention over time without review.

Quality:  0 blackout  1 wrong/hard  2 wrong/easy  3 ok/hard  4 ok/hesitant  5 perfect
How well did you recall? [0/1/2/3/4/5]: 5

Saved. Next review: 2026-05-28 11:27 (in 1d, EF=2.60)
```

## Commands

| Command | Purpose |
| --- | --- |
| `ebbinghaus add <front> [-b BACK] [-t TAG]...` | Add a study card, due immediately. |
| `ebbinghaus list [-t TAG]` | List all cards, optionally filtered by tag. |
| `ebbinghaus today` | Show cards currently due for review. |
| `ebbinghaus review [<id>]` | Review one card by id, or step through everything due. |
| `ebbinghaus delete <id> --yes` | Delete a card and its review history. |
| `ebbinghaus stats` | Summary: total cards, total reviews, due count, db path. |
| `ebbinghaus serve [--host HOST] [--port PORT]` | Launch the local web UI. |
| `ebbinghaus --db PATH ...` | Override the database location for any command. |

The database location defaults to `~/.ebbinghaus/db.sqlite` and can also be
controlled via the `EBBINGHAUS_DB_PATH` environment variable.

## Web UI

```bash
ebbinghaus serve
# Serving at http://127.0.0.1:8000 · db=~/.ebbinghaus/db.sqlite
```

The server is FastAPI + Jinja2 + HTMX (no JS toolchain, no build step). It
exposes the same operations as the CLI, plus a deck dashboard, a card creator
form, an interactive review flow with six-button quality grading, and a stats
page — all rendered with Tailwind for a clean look.

| Route | What it does |
| --- | --- |
| `GET /` | Today's due cards. |
| `GET /cards` | All cards (filterable by `?tag=`). |
| `GET /cards/new` | Add-card form. |
| `POST /cards` | Create a card. |
| `GET /cards/{id}/review` | Render the review page. |
| `POST /cards/{id}/review` | Submit a quality grade and advance the schedule. |
| `POST /cards/{id}/delete` | Delete a card. |
| `GET /stats` | Dashboard counts. |
| `GET /healthz` | Liveness probe (`{"status":"ok"}`). |

## How the scheduling works

The algorithm is **SM-2** (Wozniak, 1985), the standard operationalization of
Ebbinghaus's forgetting curve. Each card carries three pieces of state:

- `repetition` — count of consecutive successful recalls (resets on failure)
- `ease_factor` — per-card difficulty, ≥ 1.3 (lower = harder)
- `interval_days` — days until the next review

On each review the user grades recall on a 0–5 quality scale. The next
interval is computed deterministically:

```
quality < 3 (failed recall):
    repetition := 0
    interval   := 1 day

quality ≥ 3 (passed):
    repetition := repetition + 1
    interval   := 1 if repetition == 1
                  6 if repetition == 2
                  round(prev_interval * ease_factor) otherwise

# Always — ease factor drifts with quality:
ease_factor := max(1.3, ease_factor + (0.1 - (5-q) * (0.08 + (5-q)*0.02)))
```

Failed reviews still drag the ease factor down, so a card you keep getting
wrong becomes intrinsically harder and gets shorter intervals over time. See
[`docs/algorithm.md`](docs/algorithm.md) for derivation and numerical examples.

## Project layout

```
ebbinghaus-reviewer/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/ebbinghaus_reviewer/
│   ├── __init__.py
│   ├── algorithm.py            # Pure SM-2 (no I/O)
│   ├── models.py               # Card, Review dataclasses
│   ├── storage.py              # SQLite repository
│   ├── scheduler.py            # algorithm + storage = workflow
│   ├── cli.py                  # Click + Rich CLI
│   └── web/
│       ├── server.py           # FastAPI app factory
│       └── templates/          # Jinja2 + HTMX + Tailwind (CDN)
├── tests/                      # pytest suite, 63 tests, ~91% coverage
├── docs/
│   ├── algorithm.md            # SM-2 derivation + worked examples
│   ├── architecture.md         # How the pieces fit
│   └── presentation.pdf        # Original 2021 project deck (historical)
├── archive/                    # Original 2021 WPF artifacts (not used by the app)
└── .github/workflows/ci.yml    # 3 OS × 2 Python + lint + types
```

## Development

```bash
# Install with dev extras
pip install -e ".[dev]"

# Run the full test suite (63 tests)
pytest

# Coverage
pytest --cov --cov-report=term-missing

# Lint + types
ruff check src tests
mypy src

# Run the web UI with auto-reload
ebbinghaus serve --reload
```

CI runs the test suite on Ubuntu, macOS, and Windows against Python 3.11 and
3.12, plus a CLI smoke test, lint, and strict mypy.

## A note on the archive

This repository was originally a Windows WPF C# app from 2021 whose source
code was never committed. Only the compiled `.exe` (missing its commercial
Syncfusion DLL dependencies, so unrunnable) and `BAML`/MSBuild artifacts
survived. Those originals are preserved in [`archive/`](archive/) for
historical record. The current Python implementation is a clean-room rewrite
of the original *intent*, not a port of its code.

## License

[MIT](./LICENSE)

<div align="center">

# 🧠 Ebbinghaus Reviewer

**Spaced-repetition study tool along the Ebbinghaus forgetting curve (SM-2), with a CLI and web UI**

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
[![CI](https://github.com/jumincho/ebbinghaus-reviewer/actions/workflows/ci.yml/badge.svg)](https://github.com/jumincho/ebbinghaus-reviewer/actions/workflows/ci.yml)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-72%20passing-brightgreen)
![Algorithm](https://img.shields.io/badge/algorithm-SM--2-512BD4)
![Year](https://img.shields.io/badge/since-2021-blue)

</div>

---

## Overview

**Ebbinghaus Reviewer** is a spaced-repetition study tool that helps you review
material along the **Ebbinghaus forgetting curve**. You capture study items
(cards); the **SM-2 algorithm** computes when each is next due, you grade your
recall from 0–5, and the schedule adapts automatically.

This repository is a **clean-room Python reimplementation of the same idea** as
a 2021 Windows WPF/C# app built for a Jeonbuk National University (JBNU)
project. The original WPF source is preserved for honest provenance under
[`archive/`](./archive) (see [Archive](#archive-the-original-2021-wpf-app) below).

## How spaced repetition / SM-2 works

Hermann Ebbinghaus showed that memory fades quickly after learning, but
reviewing at well-chosen moments flattens the *forgetting curve* and moves
material into long-term memory.

**SM-2** (SuperMemo, Woźniak 1990) turns that into an algorithm. Each card keeps
three numbers — `repetitions`, an `ease factor`, and the `interval` in days — and
on every review:

- **Successful recall (quality ≥ 3):** increment repetitions and grow the
  interval: `1 day → 6 days → round(previous interval × EF)`.
- **Failed recall (quality < 3):** reset repetitions and the interval so the
  card is due again tomorrow (the ease factor is preserved).

The ease factor is floored at 1.3. A full explanation with a worked numeric
example is in [`docs/algorithm.md`](./docs/algorithm.md).

## Quickstart

```bash
# install (editable)
pip install -e .

# add a card
ebbinghaus add "What is the Ebbinghaus forgetting curve?" --back "Memory decay over time"

# see what's due today
ebbinghaus today

# review (recall, then grade yourself 0–5)
ebbinghaus review

# stats
ebbinghaus stats
```

Commands:

| Command | Description |
| --- | --- |
| `ebbinghaus add FRONT [--back ...]` | Add a study card |
| `ebbinghaus list` | List all cards and their schedule |
| `ebbinghaus today` | Items due today (or overdue) |
| `ebbinghaus review [--id N]` | Interactive review + grading |
| `ebbinghaus stats` | Collection statistics |
| `ebbinghaus delete ID` | Delete a card |

Every command has detailed `--help`. The database path can be set with `--db`
or the `EBBINGHAUS_DB` environment variable (default:
`~/.local/share/ebbinghaus-reviewer/reviews.db`).

## Demo

```text
$ ebbinghaus add "SM-2 ease-factor floor?" --back "1.3"
Added item #1: SM-2 ease-factor floor? (due 2026-05-29)

$ ebbinghaus today
                             Due today (2)
┏━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━┳━━━━━━┳━━━━━━━━━━┓
┃ ID ┃ Front              ┃ Back   ┃    Due     ┃ Reps ┃   EF ┃ Interval ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━╇━━━━━━╇━━━━━━━━━━┩
│  1 │ SM-2 ease-factor   │ 1.3    │ 2026-05-29 │    0 │ 2.50 │       0d │
│    │ floor?             │        │            │      │      │          │
│  2 │ Interval after 2nd │ 6 days │ 2026-05-29 │    0 │ 2.50 │       0d │
│    │ success?           │        │            │      │      │          │
└────┴────────────────────┴────────┴────────────┴──────┴──────┴──────────┘

$ ebbinghaus stats
           Statistics
┌─────────────────────────┬──────┐
│ Total items             │    2 │
│ Due today               │    2 │
│ Learning (<2 reps)      │    2 │
│ Mature (>=21d interval) │    0 │
│ Average ease factor     │ 2.50 │
└─────────────────────────┴──────┘
```

## Web UI (optional)

A lightweight FastAPI + Jinja2 server shares the **same SQLite file** as the CLI.

```bash
pip install -e ".[web]"
uvicorn ebbinghaus_reviewer.web:create_app --factory --reload
# visit http://127.0.0.1:8000 — dashboard / cards / review / health (/healthz)
```

The web layer is import-lazy, so the core code and tests run without FastAPI.

## Project layout

```
ebbinghaus-reviewer/
├── src/ebbinghaus_reviewer/
│   ├── algorithm.py     # pure SM-2 (no I/O)
│   ├── storage.py       # SQLite repository (injectable path)
│   ├── scheduler.py     # ties algorithm + storage (use cases)
│   ├── cli.py           # click + rich CLI
│   └── web/             # FastAPI + Jinja2 (optional)
├── tests/               # pytest (algorithm/storage/scheduler/cli/web)
├── docs/
│   ├── algorithm.md     # SM-2 explained, with a worked example
│   └── architecture.md  # layering / data model
├── archive/             # original 2021 WPF/C# source (honest provenance)
├── pyproject.toml
├── README.md
└── LICENSE
```

See [`docs/architecture.md`](./docs/architecture.md) for the layering and data model.

## Development

```bash
pip install -e ".[dev,web]"
pytest          # 72 tests
ruff check .    # lint
mypy src        # type check
```

## Archive: the original 2021 WPF app

[`archive/`](./archive) preserves the source of the original **Windows WPF / C#**
desktop app this project grew from. That app is Windows-only and depends on a
commercial Syncfusion WPF license, so it cannot be built or run in this
environment; the non-runnable binary outputs were deleted and only the source
was kept. See [`archive/README.md`](./archive/README.md) for details.

- Demo video (original WPF app): <https://www.youtube.com/watch?v=J2nf1r5jZrI>
- Slides: [`archive/docs/presentation.pdf`](./archive/docs/presentation.pdf)

## License

[MIT License](./LICENSE)

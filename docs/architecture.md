# Architecture

Ebbinghaus Reviewer is layered so that the scheduling *logic* is pure and the
*delivery mechanisms* (CLI, web) are thin shells around it. Dependencies point
inward: outer layers know about inner ones, never the reverse.

```
            +-----------+        +-----------+
            |    cli    |        |    web    |   delivery (click+rich / FastAPI)
            +-----+-----+        +-----+-----+
                  |                    |
                  +---------+----------+
                            v
                     +-------------+
                     |  scheduler  |              use cases
                     +------+------+
                            |
                +-----------+-----------+
                v                       v
          +-----------+           +-----------+
          | algorithm |           |  storage  |   pure SM-2 / SQLite repo
          +-----------+           +-----------+
```

## Layers

| Module | Responsibility | Depends on |
| --- | --- | --- |
| [`algorithm.py`](../src/ebbinghaus_reviewer/algorithm.py) | Pure SM-2. Given a state and a grade, returns the next state. No I/O, no clock. | — |
| [`storage.py`](../src/ebbinghaus_reviewer/storage.py) | A SQLite repository of `StudyItem` rows. The database path is injectable; there are no module-level globals. | `algorithm` (for defaults / `ReviewState`) |
| [`scheduler.py`](../src/ebbinghaus_reviewer/scheduler.py) | Use-case layer. Wires the algorithm to storage: add an item, list due items, record a graded review (compute the next state, set the next due date), compute stats. | `algorithm`, `storage` |
| [`cli.py`](../src/ebbinghaus_reviewer/cli.py) | A `click` command group rendered with `rich`. One command per use case. | `scheduler`, `storage` |
| [`web/`](../src/ebbinghaus_reviewer/web/) | Optional FastAPI + Jinja2 server over the **same** SQLite file. FastAPI is imported lazily so the core package never requires it. | `scheduler`, `storage` |

Because the CLI and the web app both go through `Scheduler` over the same
SQLite database, you can add a card on the command line and review it in the
browser (and vice versa).

## Data model

A single table, `items`, defined in `storage.py`:

| Column | Type | Notes |
| --- | --- | --- |
| `id` | INTEGER PK | autoincrement |
| `front` | TEXT | the prompt / subject (required) |
| `back` | TEXT | the answer / note (may be empty) |
| `repetitions` | INTEGER | consecutive successful recalls |
| `ease_factor` | REAL | SM-2 ease factor (>= 1.3) |
| `interval` | INTEGER | days from the last review to `due_date` |
| `due_date` | TEXT (ISO date) | when the card is next due |
| `created_at` | TEXT (ISO datetime) | when it was added |
| `last_reviewed` | TEXT (ISO datetime) | last grade time, or NULL |

Dates/times are stored as ISO-8601 strings for portability and round-tripped
through `date`/`datetime` in the repository layer.

## Database location

The CLI and web UI resolve the database path via
`ebbinghaus_reviewer.default_db_path()`:

1. `$EBBINGHAUS_DB` if set, else
2. `$XDG_DATA_HOME/ebbinghaus-reviewer/reviews.db` if `XDG_DATA_HOME` is set, else
3. `~/.local/share/ebbinghaus-reviewer/reviews.db`.

Tests use a private in-memory database (`Storage(":memory:")`) or a `tmp_path`
file, so they never touch your real data.

## Testing strategy

- The pure `algorithm` is tested directly against the SM-2 specification.
- `storage` is tested with round-trips on an in-memory and a file database.
- `scheduler` is tested with deterministic clocks (the `when=` parameter) so
  due-date arithmetic is reproducible.
- `cli` is exercised through click's `CliRunner`; `web` through FastAPI's
  `TestClient` (auto-skipped when the optional web stack is absent).

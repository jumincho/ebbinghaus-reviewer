# Architecture

The codebase is organized as a layered cake. Pure logic lives at the bottom;
I/O and UI live above it, and depend only on layers below them.

```
┌─────────────────────────────────────────┐
│   CLI (cli.py)        Web (web/)        │  ← UI / I/O entry points
├─────────────────────────────────────────┤
│   Scheduler (scheduler.py)              │  ← workflow: algorithm + storage
├─────────────────────────────────────────┤
│   Algorithm (algorithm.py)              │  ← pure functions, no I/O
│   Storage (storage.py)    Models        │  ← SQLite + dataclasses
└─────────────────────────────────────────┘
```

## Modules

| Module | Responsibility | Dependencies |
| --- | --- | --- |
| `algorithm.py` | SM-2 update rules. Pure functions of (state, quality) → state. | stdlib only |
| `models.py` | `Card`, `Review` dataclasses. | stdlib only |
| `storage.py` | SQLite-backed CRUD. Owns one connection per `Storage` instance, autocommit, with explicit `BEGIN`/`COMMIT` for multi-statement work. | stdlib, `models` |
| `scheduler.py` | Combines `algorithm` + `storage` into a single transactional review workflow. | `algorithm`, `models`, `storage` |
| `cli.py` | Click-based CLI with Rich rendering. | `click`, `rich`, `scheduler`, `storage` |
| `web/server.py` | FastAPI app + Jinja2 templates + HTMX. | `fastapi`, `jinja2`, `scheduler`, `storage` |

## Design choices

### One SQLite, two front-ends
Both `cli.py` and `web/server.py` go through the same `Storage` and
`Scheduler`. There is no API layer between them — the CLI and the web server
are alternative *views* over the same domain, so they share business logic
rather than re-implementing it across an HTTP boundary.

### Storage is single-connection
A `Storage` object owns one SQLite connection. `check_same_thread=False`
lets FastAPI's thread-pool dispatch sync handlers without confusing SQLite,
which serializes its own writes. For a single-user study tool that's enough;
adding connection pooling would be premature.

### Algorithm is pure
`algorithm.py` deliberately knows nothing about cards, databases, or time.
It takes a `ScheduleState` and a `ReviewQuality` and returns a new state.
This is the part most worth testing exhaustively (and is where ~17 of the
test cases live).

### Time is injected
Every scheduling operation accepts an explicit `now: datetime | None`. In
production it defaults to `datetime.utcnow()`; in tests it's set to a fixed
constant. The algorithm never calls `datetime.utcnow()` itself, which is
why the test suite can deterministically walk a card through a 5-step
trajectory without `freezegun` or other clock-mocking tricks.

### Templates use server-rendered HTMX, not SPA
The web UI is plain HTML + Tailwind + HTMX. No node, no bundler, no build
step — the whole UI ships as a handful of `.html` files inside the Python
package. Tailwind is loaded via CDN for development simplicity; for
production deploys you would prebuild a Tailwind CSS file instead.

### Migrations
Schema lives in a single `SCHEMA_SQL` string in `storage.py`, executed with
`CREATE TABLE IF NOT EXISTS`. The schema is small and frozen for v0.1.x; a
future schema change should introduce a `_migrations` table and forward
migrations rather than relying on `IF NOT EXISTS`.

## Data model

```
cards
├── id                  INTEGER PK
├── front               TEXT
├── back                TEXT
├── tags                TEXT (comma-joined)
├── created_at          TEXT (ISO 8601)
├── repetition          INTEGER       ┐ flattened schedule state,
├── ease_factor         REAL          │ kept on the card row so the
├── interval_days       INTEGER       │ "what's due now" query is a
└── next_review_at      TEXT (ISO)    ┘ single indexed lookup

reviews
├── id                       INTEGER PK
├── card_id                  INTEGER FK → cards.id (ON DELETE CASCADE)
├── reviewed_at              TEXT (ISO)
├── quality                  INTEGER (0-5)
├── interval_days_before     INTEGER       ┐ snapshot of pre/post state,
├── interval_days_after      INTEGER       │ for plotting curves or
└── ease_factor_after        REAL          ┘ debugging the algorithm

indexes
├── cards(next_review_at)        for due-card lookup
├── reviews(card_id)             for per-card history
└── reviews(reviewed_at)         for activity history
```

Tags are stored as a comma-joined string on the card row rather than in a
normalized `tags` table. For a single-user app with O(100) cards this is
plenty; if you wanted faceted queries or tag autocompletion you'd want a
proper many-to-many.

## Testing strategy

| Layer | What we verify |
| --- | --- |
| `algorithm` | All branches of SM-2: initial state, first/second/third pass, failure reset, EF floor, EF drift, late review. 17 tests. |
| `storage` | CRUD round-trips, tag filtering edge cases, cascade delete, count queries, env-var path override. 15 tests. |
| `scheduler` | End-to-end card lifecycle: add → review → persisted state matches algorithm output. 6 tests. |
| `cli` | Each Click subcommand against an isolated tmpdir-backed DB. 13 tests. |
| `web` | Each FastAPI route against an injected in-tmpdir `Storage` via `TestClient`. 12 tests. |

Total: 63 tests, ~91% line coverage. The uncovered portions are the
`serve` command (which exec's uvicorn) and a few defensive branches.

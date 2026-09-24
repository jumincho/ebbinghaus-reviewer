# How reviews are scheduled

Ebbinghaus Reviewer gives every item a **schedule**: when it is due next and
how far apart reviews currently are. After each review you grade how well you
remembered, and the item's strategy decides the next due time.

The rules live in [`scheduling.py`](../src/ebbinghaus_reviewer/scheduling.py).
They are pure functions of *(schedule, grade, review time)* - no clock, no
database - so every rule below is pinned by a unit test in
[`tests/test_scheduling.py`](../tests/test_scheduling.py).

## The forgetting curve

Hermann Ebbinghaus (*Über das Gedächtnis*, 1885) measured how quickly learned
material is lost: retention drops steeply within the first hour and day and
then levels off. Reviewing just before something is forgotten restores it and
makes the next decline slower, so the gaps between reviews can keep growing.
Both strategies turn that observation into expanding review intervals.

## Grades

Every review is graded with one of four buttons:

| Grade | Meaning | Ladder | SM-2 quality |
| --- | --- | --- | --- |
| **again** | forgot it | back to the first rung | 1 (fail) |
| **hard** | recalled with serious difficulty | repeat the current rung | 3 |
| **good** | recalled after some thought | climb one rung | 4 |
| **easy** | recalled instantly | climb two rungs | 5 |

## Strategy 1: the Ebbinghaus ladder (default)

The ladder spaces reviews **10 minutes, 1 day, 1 week and 1 month** apart.
Each rung is the gap between two consecutive reviews:

```
studied ──10 min──▶ review ──1 day──▶ review ──1 week──▶ review ──1 month──▶ review ──▶ mastered
```

Gaps are measured from the moment you actually review, not from the original
study time, so a late review never leaves the next one already overdue.
Climbing past the top rung marks the item **mastered**: it drops out of the
queue until you restart it (`ebbinghaus restart ID`).

## Strategy 2: SM-2 (adaptive)

SM-2 is SuperMemo's classic algorithm (P. A. Woźniak, *Optimization of
learning*, 1990). Each item carries a repetition count `n`, an **ease factor**
`EF` (starting at 2.5) and the current interval `I` in days. With `q` the
SM-2 quality of the grade (table above):

1. **Failed review** (`q < 3`, i.e. *again*): `n = 0`, `I = 1` day, `EF`
   unchanged - "start repetitions from the beginning without changing the
   E-Factor".
2. **Passed review**: `n = n + 1`, then
   `I = 1` day for `n = 1`, `I = 6` days for `n = 2`, and
   `I = ceil(I_previous × EF)` days afterwards - "if interval is a fraction,
   round it up to the nearest integer". The multiplication uses the ease
   factor from *before* this review.
3. The ease factor is updated with
   `EF' = EF + (0.1 − (5 − q) × (0.08 + (5 − q) × 0.02))` and floored at 1.3.
   In practice: *easy* adds 0.10, *good* keeps it, *hard* subtracts 0.14.

Two small, documented choices:

* Logging a new SM-2 item counts as its first presentation, so the first
  review is due one day later.
* Intervals are capped at 100 years. Without a cap, a long streak of *easy*
  grades grows them exponentially until dates overflow (property-based tests
  found exactly that).

SM-2's optional step 7 - re-drilling every item graded below 4 within the same
session - is not implemented; *hard* counts as a pass.

### Worked example

A new item studied on day 0 (`n = 0`, `EF = 2.5`, first review due on day 1),
reviewed exactly when due each time:

| Review | Grade (q) | n | Interval | EF after |
| --- | --- | --- | --- | --- |
| 1 | easy (5) | 1 | 1 day | 2.60 |
| 2 | easy (5) | 2 | 6 days | 2.70 |
| 3 | good (4) | 3 | ceil(6 × 2.70) = ceil(16.2) = **17 days** | 2.70 |
| 4 | hard (3) | 4 | ceil(17 × 2.70) = ceil(45.9) = **46 days** | 2.56 |
| 5 | again (1) | 0 | 1 day | 2.56 (unchanged) |
| 6 | good (4) | 1 | 1 day | 2.56 |

This exact sequence is asserted by `TestSM2.test_worked_example`.

## Estimated recall

Item pages and tables show an **estimated probability of recall** and draw the
forgetting curve since the last review. The model is deliberately simple: an
exponential curve `R(t) = e^(−t/S)` whose stability `S` is chosen so that
recall has fallen to 90% exactly when the item is due, i.e.

```
R(t) = 0.9 ^ (t / interval)
```

It visualises "how far along the curve" an item is - it is an assumption about
a well-calibrated schedule, not a measurement, and it never influences
scheduling ([`retention.py`](../src/ebbinghaus_reviewer/retention.py)).

## The plumbob

Like the plumbob above a Sim's head in *The Sims*, every item carries a
diamond whose colour and face show how it is doing
([`plumbob.py`](../src/ebbinghaus_reviewer/plumbob.py)):

| Plumbob | State | When |
| --- | --- | --- |
| green, happy | **fresh** | not due yet, or mastered |
| yellow, neutral | **due** | due, with an estimated recall of 80% or more |
| red, worried | **fading** | due, with an estimated recall below 80% |

With the curve above, recall is 90% when an item becomes due and 80% after
about 2.1 intervals, so an item turns red roughly one interval after it became
due: about 11 minutes late on the first rung of the ladder, 8 days late on the
1-week rung. The Today page and `ebbinghaus stats` show the plumbob of the
whole collection: the worst state among the items due. Like the recall
estimate, the plumbob never influences scheduling.

## References

- H. Ebbinghaus, *Über das Gedächtnis: Untersuchungen zur experimentellen
  Psychologie*, 1885 (English: *Memory: A Contribution to Experimental
  Psychology*, 1913).
- P. A. Woźniak, *Optimization of learning*, master's thesis, University of
  Technology in Poznań, 1990 - SM-2 description:
  <https://www.supermemo.com/en/archives1990-2015/english/ol/sm2>

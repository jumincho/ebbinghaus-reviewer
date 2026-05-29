# The SM-2 algorithm

Ebbinghaus Reviewer schedules reviews with **SM-2**, the spaced-repetition
algorithm introduced by Piotr Woźniak for SuperMemo (1987, published 1990). SM-2
operationalises Hermann Ebbinghaus's *forgetting curve*: memory of a freshly
learned item decays quickly, but each successful recall flattens the curve, so
the item can be reviewed less and less often.

Implementation: [`src/ebbinghaus_reviewer/algorithm.py`](../src/ebbinghaus_reviewer/algorithm.py).
It is pure (no I/O, no clock), so it is trivially testable.

## State per item

| Field | Meaning | Initial value |
| --- | --- | --- |
| `repetitions` | consecutive successful recalls | `0` |
| `ease_factor` (EF) | how "easy" the item is; scales the interval | `2.5` |
| `interval` | days until the next review | `0` |

## A graded review

Each review is graded with a **quality** `q` from 0 to 5:

| q | meaning |
| --- | --- |
| 5 | perfect recall |
| 4 | correct after some hesitation |
| 3 | correct, but with serious difficulty |
| 2 | wrong; the answer was easy to recall once shown |
| 1 | wrong; the answer felt familiar |
| 0 | total blackout |

The update follows the canonical SM-2 order of operations:

1. **Failed recall (`q < 3`)** — reset `repetitions` to `0` and `interval` to
   `1` day. The ease factor is left **unchanged** (SM-2 step 6).
2. **Successful recall (`q >= 3`)** — increment `repetitions`, then choose the
   interval from the previous one using the ease factor *before* it is updated:

   * 1st success -> `interval = 1`
   * 2nd success -> `interval = 6`
   * 3rd+ success -> `interval = round(previous_interval * EF)`
3. **Then** update the ease factor with the SM-2 formula:

   ```
   EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
   ```

   `EF'` is floored at **1.3** — an item never becomes "harder" than that.

A handy consequence of the formula: `q = 4` leaves EF unchanged, `q = 5` raises
it by `0.1`, and `q <= 3` lowers it.

## Worked example

Start with a brand-new card: `repetitions = 0`, `EF = 2.5`, `interval = 0`.

| Review | q | repetitions | interval (days) | EF after |
| --- | --- | --- | --- | --- |
| 1 | 5 | 1 | `1` | `2.5 + 0.1 = 2.6` |
| 2 | 5 | 2 | `6` | `2.6 + 0.1 = 2.7` |
| 3 | 4 | 3 | `round(6 * 2.7) = 16` | `2.7 + 0.0 = 2.7` |
| 4 | 3 | 4 | `round(16 * 2.7) = 43` | `2.7 - 0.14 = 2.56` |
| 5 | 1 | 0 (reset) | `1` | `2.56` (unchanged) |

Notice in review 3 the interval uses `EF = 2.7` (the value *before* that
review's update), giving `round(6 * 2.7) = 16`. After the failed review 5 the
card is due again the next day, but its ease factor is preserved, so it climbs
back up faster than a truly new card.

## References

- P. A. Woźniak, *Optimization of learning*, 1990 —
  <https://www.supermemo.com/en/archives1990-2015/english/ol/sm2>
- H. Ebbinghaus, *Über das Gedächtnis* (Memory: A Contribution to Experimental
  Psychology), 1885.

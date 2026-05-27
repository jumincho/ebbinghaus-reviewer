# The Algorithm

`ebbinghaus-reviewer` schedules reviews with the **SM-2 algorithm** (Wozniak,
1985), the canonical modern operationalization of Hermann Ebbinghaus's
forgetting curve.

## Why not Ebbinghaus's original 1885 intervals?

Ebbinghaus showed that retention decays exponentially after learning unless
the material is revisited. His original data suggested fixed intervals on the
order of 20 minutes → 1 hour → 9 hours → 1 day → 2 days → 6 days → 31 days.

The trouble is that those intervals assume **all material is equally
difficult**. In practice a vocab pair you find obvious shouldn't get the same
schedule as a formula you keep mixing up. SM-2 keeps Ebbinghaus's
"exponential stretching" intuition but lets each card carry its own
difficulty.

## State per card

| Field | Initial | Meaning |
| --- | --- | --- |
| `repetition` | 0 | Consecutive successful recalls (resets on failure). |
| `ease_factor` | 2.5 | Per-card multiplier, floored at 1.3 (lower = harder). |
| `interval_days` | 0 | Days until next review. |
| `next_review_at` | now | Absolute timestamp of next review. |

## Quality scale

When the user grades recall, they pick 0-5:

| q | Label | Pass? |
| --- | --- | --- |
| 0 | Blackout | No |
| 1 | Wrong, hard to remember | No |
| 2 | Wrong, easy in hindsight | No |
| 3 | Right, with serious effort | Yes |
| 4 | Right, with hesitation | Yes |
| 5 | Perfect recall | Yes |

The threshold for "pass" is `q >= 3`.

## Interval update

```python
if quality < 3:                       # failed recall
    repetition = 0
    interval   = 1                    # try again tomorrow
else:                                 # passed recall
    repetition += 1
    if repetition == 1:
        interval = 1
    elif repetition == 2:
        interval = 6
    else:
        interval = round(prev_interval * ease_factor)
```

The interval stretches geometrically by the ease factor on each successful
pass after the second.

## Ease-factor update

The ease factor is updated *every* review (pass or fail):

```
ease_factor := max(1.3, ease_factor + 0.1 - (5-q) * (0.08 + (5-q) * 0.02))
```

Worked deltas:

| q | delta | meaning |
| --- | --- | --- |
| 5 | +0.10 | Perfect → card gets easier |
| 4 |  0.00 | Hesitant → unchanged |
| 3 | −0.14 | Hard → slightly harder |
| 2 | −0.32 | Wrong → significantly harder |
| 1 | −0.54 | Wrong/hard → much harder |
| 0 | −0.80 | Blackout → much harder |

A failed card is double-penalized: its repetition count resets *and* its
ease factor drops, so future intervals for that card start short *and* grow
slowly.

## Worked example

Starting state: `repetition=0`, `ef=2.5`, `interval=0`.

| Step | Quality | After: rep | ef | interval | next |
| --- | --- | --- | --- | --- | --- |
| 1 | 5 (perfect) | 1 | 2.60 | 1 | +1d |
| 2 | 5 (perfect) | 2 | 2.70 | 6 | +6d |
| 3 | 5 (perfect) | 3 | 2.80 | round(6·2.80)=17 | +17d |
| 4 | 3 (hard pass) | 4 | 2.66 | round(17·2.66)=45 | +45d |
| 5 | 1 (failed) | 0 | 2.12 | 1 | +1d |
| 6 | 5 (perfect) | 1 | 2.22 | 1 | +1d |
| 7 | 5 (perfect) | 2 | 2.32 | 6 | +6d |
| 8 | 5 (perfect) | 3 | 2.42 | round(6·2.42)=15 | +15d |

Note step 5: a failure resets `repetition` to 0 and sets `interval` back to
1 day, but the lower ease factor (2.12) means the post-recovery growth in
step 8 is gentler (15d) than the original step 3 (17d) — the card has been
permanently flagged as harder than it first appeared.

## Boundary behavior

- The ease factor never drops below **1.3** (so even a chronically-failed
  card still has an exponential, just very slow, stretch).
- Failing review N resets to interval=1d regardless of how far the card had
  grown — the schedule restarts from scratch but with a lowered ease.
- Reviewing late (after `next_review_at`) doesn't change the algorithm: the
  next interval is added on top of the review's actual timestamp, not the
  scheduled one.

## References

- P. A. Wozniak, *"SuperMemo 2 algorithm description"*, 1985.
  <https://super-memo.com/english/ol/sm2.htm>
- H. Ebbinghaus, *Über das Gedächtnis*, 1885.

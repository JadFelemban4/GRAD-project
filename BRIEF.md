# BRIEF.md — the project in one page

Read this first if you have five minutes. `CLAUDE.md` is the long version.

---

## The claim

Not "a predictive controller for engines." That is commercially solved and
academically crowded. The claim is a **criterion for when preview information is
worth acquiring at all**, governed by one dimensionless ratio:

> **H / τ** — the preview horizon divided by the time constant of the component
> being protected.

- **τ ≫ H** — you are seeing thirty seconds into a problem that takes ten
  minutes to develop. Preview buys nothing.
- **τ ≪ H** — the system reacts faster than you can anticipate. Preview is
  redundant.
- **τ ≈ H** — the useful region, and nobody has mapped it.

## The falsifiable version

Preview value should collapse onto a single curve when plotted against H/τ,
**regardless of which plant produced the point**. Two plants: a turbocharged
petrol engine and a battery pack. If the two do not overlap, the criterion is
wrong or incomplete — and reporting that is still a result.

## The one hard constraint

**The project never writes to the vehicle's ECU.** Read-only OBD-II logging
only. No flashing, no CAN transmission, no tuning. If a task seems to require
writing to the car, it is the wrong task. Say so rather than finding a way.

---

## The single strongest fact

Disabling preview collapses the predictive policy onto the reactive one **to the
decimal**:

```
predictive protection          437.6 damage
reactive protection            548.6 damage
predictive, preview disabled   548.6 damage    <-- identical
```

Identical fuel, identical damage, identical peak temperatures. The size of the
effect has changed four times, across two engines, two scenarios and two
protection triggers. **The identity has held every single time.**

That is what makes it load-bearing: whatever gap exists is attributable to
preview information and to nothing else. It is the sentence to defend in the
viva.

---

## Where the project stands

| Phase | Status |
|---|---|
| A · setup | done |
| B · match the simulator to the car | **passed** — 1.4 % load residual with k derived (2.8 % fitted), 22 pooled points. Read mistake 12 before quoting it |
| C · get an agent to learn | **next.** `train.py` exists, nothing trained yet |
| D · baselines and the ablation | not started. **This is the floor of the project** |
| E · battery plant | not started. `battery.py` does not exist |
| F · the H/τ sweep | preliminary, from hand-written policies |
| G · writing | not started |

**A passing project is Phase D**: validated simulator + agent beating two
baselines + an ablation isolating preview. Everything after D raises the
ceiling. Nothing after D protects the floor.

---

## The numbers, and the command that prints each one

Do not quote a number that a script does not print.

| Number | Command |
|---|---|
| 829.2 · 548.6 · 437.6 · 548.6 | `python check_premise.py` |
| 8 of 11 inside band | `python validate.py` |
| 4 of 4 checks pass | `python test_reward.py` |
| 168.1 min, 8 drives, 22 points | `python build_dataset.py "logs/raw/*.csv"` |
| 1.4 % load residual, PASS, k derived | `python compare_log.py data/master_points.csv` |
| all 22 figures match | `python verify_docs.py` |
| 16.5 → 18.0 → 26.0 pts | `python generality_test.py` |

Preview advantage: reactive cuts damage 33.8 %, predictive 47.2 % —
**13.4 points**, measured against a **1123 K** turbine protection limit.

**Always report the threshold with the preview figure.** A preview advantage
quoted without the limit it was measured against is not a result.

---

## The tone that earns marks

Almost every number here came out of running something. Two calibrations have
been corrected against measurement, one hypothesis has been refuted and
reported, and the validation table states what it does *not* cover.

An examiner trusts a student who reports against themselves, and punishes a
validation table that implies coverage it lacks.

---

## Where to go next

| You want | Read |
|---|---|
| what to do right now | [handoff.md](handoff.md) |
| current state and today's run log | [CHECKPOINT.md](CHECKPOINT.md) |
| what the words mean | [Context.md](Context.md) |
| how the code fits together | [ARCHITECTURE.md](ARCHITECTURE.md) |
| what is in the data files | [DATA-MODEL.md](DATA-MODEL.md) |
| the mistakes already made | [CLAUDE.md](CLAUDE.md) |
| the evidence for Chapter 3 | [validation_table.md](validation_table.md) |

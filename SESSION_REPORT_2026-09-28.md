# Session report — 21 to 28 September 2026

**Audience:** the team. It assumes you know the project. In the order it
happened, including the things that were wrong on the first attempt.

**Branch:** `JMF-2340550`, not pushed. `git log 7f6c7f1..HEAD` is this session.
`JMF-2340550-sep17` is still not merged.

---

## Headline

| | |
|---|---|
| **The retrain is ready.** | New road every training episode, dt = 1.0, output to `runs/terrain_dt1/`. Scoring untouched. Not yet run. |
| **The new roads found a gearbox defect.** | Grades near 9 % at 130 km/h could not be driven by any policy. Fixed: the box kicks down when the engine falls short. |
| **The car-fitted spark map was never in use.** | The model's knock limit sat below it at every steady point. Offset refitted: part-load bias +3.16° → −0.08°. |
| **Preview's −0.4 is entirely the knock term.** | On turbine and oil damage alone, predictive and current-grade tie. |
| **The knock test could not see knock.** | One reading of each ignition angle every ~8 s. Untested, not refuted. |
| **The oil node cannot be calibrated from these logs.** | Light-load drives and drive10 pull opposite ways. |
| **A phone-readable results page exists.** | `results/page/index.html`, published as a private claude.ai artifact. |

---

## 1 · Phase D on the loaded scenario (21 September)

All ten existing agents were scored on the locked 130 km/h climb with
`evaluate.py`'s twenty frozen episodes, run through a parallel driver that calls
`evaluate.run_episode` unchanged (spot-checked against the serial protocol to
1e-6). Re-run on 27 September after the fixes below:

| | |
|---|---|
| trained agents' damage cut | 45.1–70.5 % (sighted), 46.0–70.1 % (blinded) |
| best hand-written (current-grade) | 34.4 % |
| **training over current-grade** | **+25.9 points** |
| sighted minus blinded, paired by seed | −1.0 / −0.3 / +0.4 / −2.3 / +0.9 |
| mean, 95 % CI | −0.5, −2.0 to +1.1 — indistinguishable from zero |

**Not Phase D's answer.** Those agents trained at 110 km/h (nothing binds), at
dt = 0.2 s while scoring runs at 1.0 s, and on one road. What it does settle:
hand-written policies gave the preview question the wrong sign (AUDIT.md C3).

**Found on the way: `train.py` never passed `dt`.** Every agent learned at 0.2 s
and was scored at 1.0 s; since AUDIT.md M16 scales the slew limit by dt, every
actuator moved five times further per step at scoring than in training.

## 2 · The simulator against the car (21–27 September)

`model_vs_data.py` lays the simulator beside the logs in eleven places, each
stating what its residual can see (mistake 12).

| comparison | status | result |
|---|---|---|
| load, relative air filling | limited | 1.44 % over 26 points; blind to the breathing model; 48.0 % on the wrong engine |
| manifold pressure under boost | agrees | +1.9 % against the car's boost channel |
| enrichment | off | worst cell 0.076 lean (4500–7000 rpm, 4–8 s) |
| part-load spark | agrees, after the fix | bias −0.08°, RMS 2.51° |
| oil and coolant, drive10 | agrees | −4.4 K and −4.0 K median |
| oil on hard pulls | off | model 140 °C, car 107 °C |
| knock | untested | r = −0.12, on one reading per ~8 s |
| gearbox ratios | agrees | 86.7 % of samples within 4 % of a published ratio |
| compressor ceiling | limited | fitted to these data; top rests on 4–5 readings |
| operating region | not covered | 1.8 % of samples reach the climb's load |
| published bands | limited | 8 of 11 |

Three of these had been documented differently, and each was traced before
anything was changed:

<!-- RETIRED-OK -->
- **Enrichment.** CLAUDE.md said every cell was within 0.027. That table was on
  the row-count dwell axis AUDIT.md H3 retired; the README's copy also carried
  pre-drive10 counts and superseded correlations, shielded from the checker by
  a section-wide `RETIRED-OK`. Corrected in all three places and guarded in
  `verify_docs.RETIRED`. The dwell constants were not refitted: too few
  independent readings.
- **Spark.** See section 4.
- **Oil.** First described as "the oil node is too light". Wrong: see section 5.

## 3 · Training roads, and the gearbox defect they found (27 September)

On one fixed climb the road ahead never changes, so preview has nothing to
report. `engine_env.make_terrain` and `TerrainTrainingEnv` draw a new road each
episode: the locked climb (15 %), a single climb of 4–14 % (30 %), rolling hills
of −3 to +10 % (25 %), a double climb (20 %), flat (10 %). Grade changes ramp
over 4–12 s. Speed and ambient stay at the locked values. Descents stop at −3 %:
measured, the baseline follows torque to −4 %, and at −5 % the request turns
negative (no fuel-cut model) and the neutral reward falls to −8 per step.

**The first 40 roads failed.** Neutral rewards reached −0.26 and tracking error
0.106 against a 0.05 band. Cause: in 8th at 130 km/h (2107 rpm) the model's
engine sustains 333 Nm, but the shift rule only handed back a gear above 375 Nm.
Grades of about 7.5–9.5 % were undrivable by any policy. The boost ceiling is
fitted to flat-road logs where the car was never asked for low-rpm boost, so the
model is short there. **Fix:** `Vehicle.DELIVERABLE_TORQUE`, measured through
the env's own load loop, and the box kicks down when a request exceeds it. After:
worst neutral +0.004, worst tracking 0.015. `test_reward.py` now checks a 9.3 %
regression road and every road family (8 of 8); `check_roads.py` drives 40.

Effect on the locked climb: it runs in 7th either way. The 0–130 km/h launch
had the same one-step shortfall, so the premise moved by a hair
(959.8 → 959.4).

## 4 · The spark map (27 September)

The map was fitted on 7 September with its IAT compensation reading the
pre-throttle sensor; mistake 13 switched the compensation to the modelled charge
temperature and the offset was never refitted. Worse, at 26.18 the fitted line
sat a median 9.6° **above** the model's knock limit at all 26 steady points, so
the unvalidated knock model set part-load spark everywhere.

`SPARK_A` 26.18 → 13.33, **offset only**. The full three-constant refit fitted
better (RMS 2.29°) but its steeper slope undercut the knock limit in boost —
−10.8° where the car runs 0°, and 3.8° at the locked climb. That is mistake 6,
so it was rejected. With the old slopes the climb stays knock-limited.

Effect: baseline 959.4 → 951.9 (flat cruise 0.8° less advanced, less knock
damage); preview against current-grade stays −0.4. The app's `pull01` pin moved
608.0 → 609.2 °C (fallback spark), reason written beside it.

## 5 · The three comparisons that don't agree, re-read (28 September)

**Knock: untested, not refuted.** `7475b5d7` was logged with 26 channels. Its
14 318 rows hold only 404 target and 410 actual ignition readings in 55 minutes;
a third of the pairs in a row are more than a second apart. A knock retard lasts
a second or two. Filtering to steady gear does not help — speed and rpm were
read seconds apart too. Drive C logs 6 channels.

**The knock term decides preview's −0.4.** It is 6.4 % of the baseline's damage
and 11–12 % of the protecting policies'. On turbine and oil damage alone,
predictive and current-grade tie: 555.7 against 555.8.

**Oil: the logs cannot calibrate it.** Replaying the pulls with one assumption
changed at a time: halving the fuel-to-oil heat share takes the peak from 140 to
116 °C; doubling the oil's capacity only to 125 °C; pinning the block to the
measured coolant to 134 °C. So the assumed 5 % share drives it. But fitting both
oil parameters on the three light-load drives fixes the pulls (134 → 102 °C, car
107) and breaks drive10 (116 → 102 °C, car 117). Nothing in `thermal.py` was
changed.

**Elevation.** The scored climb rises 2 340 m, but the engine breathes sea-level
air: `p_baro` is fixed and the plant never reads it. A standard atmosphere gives
about 76 kPa at that height. The scenario is sustained load at sea level.

## 6 · What was built

- `model_vs_data.py` — the eleven comparisons plus the knock-sampling and
  oil-identification probes; `results/model_vs_data.json`.
- `make_figures.py` — figures 1–19 in `results/figures/`.
- `make_page.py` + `results/page/template.html` — the phone page; every result
  in its prose is a token filled from the data.
- `check_roads.py` — the training-road gate; `results/training_roads.json`.
- `logs/DRIVE_PLAN.md` — drives A (climb), B (roll-ons), C (knock).

## 7 · Commits

| commit | what |
|---|---|
| `a50d22c` | results from 21 September: Phase D on the loaded scenario, the car comparisons |
| `c6e9e03` | training roads, the gearbox kickdown, `train.py` dt = 1.0 |
| `0d8e6ca` | the spark offset refit |
| `e27564e` | everything re-measured on the corrected simulator; the drive plan |
| `480711b` | page rounding fix |
| this one | the 28 September re-reading, and every handoff document updated |

One unpushed commit (`0d8e6ca`) was amended after a command chain committed while
`verify_docs.py` was failing, so that its message's "38 of 38" would be true.
The failure was a false positive from a comment of ours.

## 8 · Next

1. Decide the order: drives A and B first, or retrain now and again after.
2. Retrain: ten runs, ~3 h, `check_roads.py` first.
3. Score with `evaluate.py`: paired by seed, three rows, damage two ways.
4. Merge `sep17` before reporting.

`presentation/` was not touched: it is marked out of date and needs a rewrite.

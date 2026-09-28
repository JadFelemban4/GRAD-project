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
| **Oil and coolant are now scored against the car.** | `validate.py` rows 8–11 use bands from our own drives: 7 of 11, and 1 of 4 of the car rows. The car's oil takes 70–100 s to respond; the model's takes 14. |
| **GCC spec and fuel checked.** | No uprated GCC cooling found in any source; 50 % stronger cooling moves the turbine 0.5 K. 95 or 98 RON moves only the knock term. |
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
| oil and coolant, drive10 | off | −6.1 K and −4.7 K median, fed the car's measured fuel (section 6) |
| oil on hard pulls | off | model 140 °C, car 107 °C |
| knock | untested | r = −0.12, on one reading per ~8 s |
| gearbox ratios | agrees | 86.7 % of samples within 4 % of a published ratio |
| compressor ceiling | limited | fitted to these data; top rests on 4–5 readings |
| operating region | not covered | 1.8 % of samples reach the climb's load |
| validation table | limited | 7 of 11: 6 of 7 against literature, 1 of 4 against our car (section 6) |

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
116 °C; doubling the oil's capacity only to 124 °C; pinning the block to the
measured coolant to 134 °C. So the assumed 5 % share drives it. But fitting both
oil parameters on the three light-load drives fixes the pulls (134 → 104 °C, car
107) and breaks drive10 (116 → 102 °C, car 117). Nothing in `thermal.py` was
changed. *(Figures from the measured-fuel replay of section 6; the first pass,
on modelled fuel, read 125 and 102 for the second and fourth.)*

**Elevation.** The scored climb rises 2 340 m, but the engine breathes sea-level
air: `p_baro` is fixed and the plant never reads it. A standard atmosphere gives
about 76 kPa at that height. The scenario is sustained load at sea level.

## 6 · The validation table scores oil and coolant against the car (28 September)

`validate.py` compared eleven model outputs against "published bands". Rows 1–7
are things no channel on this car can see, so literature is the only yardstick.
**Rows 8–11 were oil and coolant, which the car logs** — and three of their four
bands had no source (REFERENCES.md section 3). They now use bands computed from
our own drives, each rule fixed before the model was scored against it:

| row | quantity | model | band, from our car | |
|---|---|---|---|---|
| 8 | oil, drive10's hottest 10 min | 96.4 °C | 103–111 | outside |
| 9 | oil apparent time constant | 14.0 s | 70–100 (4 drives) | outside |
| 10 | coolant, synthetic climb | 94.5 °C | 83.5–95.6 | inside |
| 11 | coolant, drive10 free-running | 88.4 °C | 91.8–94 | outside |

**7 of 11**: 6 of 7 against literature, 1 of 4 against the car. It read eight of
eleven against the old bands; stricter bands that are the car's own should move
it that way. `verify_docs.py` was changed to expect 7 and to count the car rows,
with that reason written beside it.

How it was built: **`car_thermal.py`** is now the one replay both `validate.py`
and `model_vs_data.py` use. `thermal.py` runs free-running over a drive on a 1 s
grid, seeded at the first real reading (AUDIT.md M8 zeros skipped), fed the fuel
the car actually burned — air mass over (14.7 × λ), two measured channels — so
the car's fuel cut on overrun is in it and no combustion model is. The old replay
fed modelled fuel, which misses the cut; the switch moved drive10 from −4.4 / −4.0 K
to −6.1 / −4.7 K and that comparison from *agrees* to *off*. The page and
`model_vs_data.py` say so.

**The time constant is the most useful thing it found.** One fitting method,
checked first by recovering the model's analytic 14 s on every drive, gives the
car's oil **70–100 s** on four of five drives (the steady cruise, `3aca2ec1`,
does not excite it enough to say). The model's oil τ is c_oil / (ua_block_oil +
ua_oil_amb) = 12 000 / 860 = 14 s, so the car implies **c_oil ≈ 60 000–86 000 J/K**
— four to seven times the assumed 12 000. The independent two-parameter fit of
section 5 lands on 48 000. Two routes, one direction. **`thermal.py` was not
changed:** it moves the locked scenario's oil damage, so it is a decision for
before the retrain, with drive A behind it. The old literature band for this row,
20–400 s, contained the car's value: the band was right and the model was not.

**Also caught on the way:** REFERENCES.md placed our best BSFC between
Heywood's 270 and Conway's 233 g/kWh using the figure from before the cycle model
was converged (AUDIT.md H1). `validate.py` has printed 239.9 since. Fixed, and the
old figure is now in `verify_docs.RETIRED`.

## 7 · The GCC specification and the fuel (28 September)

Our car is GCC-spec. Toyota Saudi Arabia's spec page confirms the 382 hp engine
(the 285 kW B58B30O1 `plant.py` runs; the page is the 2026 model year). **No
admissible source was found for any GCC-specific radiator, fan or oil cooler** —
only forum posts. Do not write that it has uprated cooling. On the model, 50 %
stronger radiator and fan moves the climb's turbine peak 884.0 → 883.5 °C: the
housing trades heat with exhaust and air, not coolant. And the fitted
parameters (`ua_block_oil`, the 88 °C regulation point, spark, enrichment)
already came from this car's logs.

The owner's manual (team's report): 95 RON minimum, 98 recommended. The model
runs 95. At 98 the baseline's damage falls 951.9 → 931.5, all of it in the knock
term (61.3 → 41.2); the turbine peak stays 884 °C and preview over current-grade
on thermal damage stays +0.00. **Whichever the car was filled with while logging
is the one to use**, and changing it means refitting the knock-limited spark,
re-running `validate.py` and `check_map.py` — before the retrain. Details in
REFERENCES.md section 2c.

## 8 · What was built

- `model_vs_data.py` — the eleven comparisons plus the knock-sampling and
  oil-identification probes; `results/model_vs_data.json`.
- `make_figures.py` — figures 1–19 in `results/figures/`.
- `make_page.py` + `results/page/template.html` — the phone page; every result
  in its prose is a token filled from the data.
- `check_roads.py` — the training-road gate; `results/training_roads.json`.
- `logs/DRIVE_PLAN.md` — drives A (climb), B (roll-ons), C (knock).
- `car_thermal.py` — the shared oil and coolant replay, measured fuel, and the
  time-constant identification behind `validate.py` rows 8–11.

## 9 · Commits

| commit | what |
|---|---|
| `a50d22c` | results from 21 September: Phase D on the loaded scenario, the car comparisons |
| `c6e9e03` | training roads, the gearbox kickdown, `train.py` dt = 1.0 |
| `0d8e6ca` | the spark offset refit |
| `e27564e` | everything re-measured on the corrected simulator; the drive plan |
| `480711b` | page rounding fix |
| `13363ea` | the 28 September re-reading, and every handoff document updated |
| next | `validate.py` rows 8–11 onto car data (`car_thermal.py`), REFERENCES 2c (GCC, fuel), the page and figures |

One unpushed commit (`0d8e6ca`) was amended after a command chain committed while
`verify_docs.py` was failing, so that its message's "38 of 38" would be true.
The failure was a false positive from a comment of ours.

## 10 · Next

0. **Tell us which fuel the car was filled with while it was logged**, and the
   manual's page for 95 / 98. It decides whether the octane changes before the
   retrain.
1. Decide the order: drives A and B first, or retrain now and again after. The
   oil time constant (section 6) is a new reason for drive A first: it is the
   drive that could settle `c_oil`.
2. Retrain: ten runs, ~3 h, `check_roads.py` first.
3. Score with `evaluate.py`: paired by seed, three rows, damage two ways.
4. Merge `sep17` before reporting.

`presentation/` was not touched: it is marked out of date and needs a rewrite.

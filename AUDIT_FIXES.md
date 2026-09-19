# AUDIT_FIXES.md — what was fixed from `AUDIT.md`, and what every number did

**Started 16 September 2026.** `AUDIT.md` is the review: 3 CRITICAL, 8 HIGH,
16 MEDIUM, 14 LOW. This file is the response to it — one row per finding, what
changed, and **what moved as a result**. It is the place to look when a number
in another document disagrees with a script.

> **The headline first, because it reverses a claim this project has made for
> weeks.** With C1, C2 and C3 fixed, the standard scenario **no longer binds the
> protection trigger at all**, and a policy with **no preview** — one that acts
> on the grade the car is on right now — **beats the predictive policy by 2.2
> points**. The premise figures 829.2 / 548.6 / 437.6 and the 13.4-point preview
> advantage are **VOID**. See C1/C2/C3 below.

---

## What the scripts print now

| script | before the audit fixes | after |
|---|---|---|
| `check_premise.py` | baseline 829.2 · reactive 548.6 · predictive 437.6 | **baseline 256.5 at 801 °C — constraint does not bind** |
| `test_reward.py` | 4 of 4, neutral −0.00438 | **4 of 4, neutral −0.00888** (quote the ±0.05 band, not the digits — M13) |
| `generality_test.py` | H2 table 16.5 → 18.0 → 26.0 pts | **the baseline never exceeds the limit — H1 and H2 are not measurable on this scenario** |
| `build_dataset.py` | 22 operating points | **23**, and stable across 8 orderings (was 20–23) |
| `compare_log.py` | 1.4 % derived | **1.3 % derived, 1.1 % fitted** over 26 points |
| `compare_log.py --map-from-log` | empty table, exit 0 | **110.4 % residual** — it reproduces mistake 2 again |
| `verify_docs.py` | 33 of 33, 256 mentions, 22 files | **33 of 33, 274 mentions, 23 files** (now scans `presentation/index.html`) |
| `python -m app.test_replay` | 46 of 46 | **49 of 49** (three new regressions) |
| `app` replay, `7475b5d7` | peak 884.9 °C, 13 thermal | **peak 890.6 °C, 15 thermal** |
| `app` replay, `pull01` | peak 593.7 °C, 0 thermal | **peak 608.0 °C, 1 thermal** |
| `validate.py` EGT cruise max | 777.3 °C | **787.7 °C** — further outside, honestly |
| `plant.DTHETA_DEG` | 0.5° (unstudied) | **0.25°**, with the study in the docstring |
| `import generality_test` | ~9 minutes (ran at import) | **0.19 s** |

---

## CRITICAL

### C1 — the baseline had its cooling switched off. FIXED.
`check_premise.py` and `generality_test.py` each defined their own neutral as
all five actions at zero. Actions 3 and 4 are absolute duties, so zero means
**fan OFF and pump at its 0.3 floor**, and the pump term was −1.857, outside the
declared action space. Both now import `engine_env.neutral_action()`, and the
protecting policies floor fan and pump at the neutral values — a policy that
cools *less* than the baseline is not protecting.

**Moved:** premise baseline 829.2 → 674.1 with C1 alone (then 256.5 once C2
landed too).

### C2 — the baseline ECU was scheduled on a load the engine was not at. FIXED.
`ecu.step()` was fed `_map_for(...)`, an open-loop feed-forward **guess**: 224 kPa
on the standard climb where the tracking loop actually settles at 175 kPa. The
ECU commanded knock-limited spark for a phantom load and ran the enrichment
dwell timer above `ENR_LOAD` while the engine sat below it. It is now scheduled
on the pressure the baseline loop produced on the **previous step**, which is
what a real ECU has.

**Moved:** the turbine peak falls from 873 °C to **801 °C**, below the 850 °C
trigger. **The constraint stops binding**, the reactive policy never acts, and
its row becomes the baseline row. The "879 °C turbine" the documents quoted was
this scheduling error, not the engine.

### C3 — the comparison was depth, not timing; and the ablation was an identity. FIXED.
`p_reactive` saturated at k = 0.36 while `p_predictive` held k ≥ 0.55, so the two
differed in **how hard they protected** as well as when. Both now use one
`_protect(k)`. A third baseline was added — **`p_grade_now`**, which acts on the
current road gradient with no preview at all, the comparator the audit asked for.

The "548.6 = 548.6 to the decimal" ablation is **not evidence and never was**:
with `use_preview=False` the preview term is literally zero, so `p_predictive`
returns `p_reactive`'s vector every step. Measured: `blinded − reactive =
+0.000000`. `check_premise.py` now says so in its own output.

**Result:** preview over current-grade is **−2.2 points**. Preview is currently
*worse* than knowing the grade you are on.

---

## HIGH

| id | status | what changed |
|---|---|---|
| **H1** discretisation not converged at `dtheta = 0.5°` | **FIXED** | convergence study run; `plant.DTHETA_DEG` **0.5 → 0.25**, and `validate.test_convergence()` now fails if halving the step moves a headline more than its quoted precision |
| **H2** checker cannot see simulation-derived figures | **FIXED** | `validate.rows()` exposes the validation rows as data and `verify_docs.check_simulation()` asserts them. The auditor's own drift test now FAILS as it should — "8 of 11" changed in README is caught. `presentation/index.html` is tracked too |
| **H3** dwell computed at an assumed 4.6 Hz | **FIXED** | dwell now summed from timestamps. corr(λ,dwell) **−0.47 → −0.41**; "seconds above 207 kPa" **178 → 184** |
| **H4** "n samples" are forward-filled rows | **FIXED** | `build_dataset.fresh_readings()` counts genuine polls; `verify_docs` prints the effective n and standard error beside every correlation. The 1055 rows above 180 kPa hold **~39 independent air-mass and 74 lambda readings** — SE **±0.17** |
| **H5** knock integral says the car detonates continuously | **MEASURED, NOT FIXABLE HERE** | the model's KI and the car's own retard correlate at **−0.149** over 13 592 paired samples. Documented as a limitation in CLAUDE.md; settling it needs a deliberate drive |
| **H6** `train.py` cannot resume | **FIXED** | loads the newest `ckpt_*_steps.zip`, passes `reset_num_timesteps=False` and the remaining budget |
| **H7** de-duplication is order-dependent | **FIXED** | windows sorted before merging: **23 points, identical in 8 orderings**. `max_gap` now carries the worst case, exposing the true **0.481 s** the average hid; 9 points that pool more than one drive are labelled `n_sources` instead of silently taking the first drive's name |
| **H8** app's modelled lambda can never enrich | **FIXED** | fallbacks run through `BaselineECU.step`; λ reaches 0.81 after a sustained pull |

### H1 — the convergence study, and what it moved

Measured against a 0.0625° reference. The integration is explicit Euler, so the
error is first order and halves with the step, which is exactly what it does:

| `dtheta` | torque error | EGT error | knock-integral error | cost |
|---|---|---|---|---|
| 1.0° | −1.0 to −3.9 % | −30 to −44 K | −4.0 to −4.5 % | 2 ms |
| **0.5°** *(was shipped)* | −0.5 to −1.8 % | **−14 to −21 K** | −1.9 to −2.5 % | 5 ms |
| **0.25°** *(shipped now)* | −0.2 to −0.8 % | −6 to −9 K | −0.8 to −1.1 % | 9 ms |
| 0.125° | −0.1 to −0.3 % | −2 to −3 K | −0.3 to −0.4 % | 19 ms |

0.25° halves the error for double the cost. **It is not converged either**, and
that is why the table is published: the residual is about **7 K of EGT and
0.25 % of torque**, and no figure should be quoted finer than that.

**What moved.** Every EGT rises ~8 K, so the cruise-band EGT maximum goes
777.3 → **787.7 °C** — *further outside its band*, which is the honest
direction. `validate.py` stays 8 of 11. The premise baseline moves 256.5 →
**294.2** and its peak turbine 801 → **812 °C**, still below the 850 °C trigger,
so **no conclusion changes**. The app's turbine estimates rise with the EGT:
`pull01` 601.4 → **608.0 °C**, `7475b5d7` 884.9 → **890.6 °C**, with no alert
count moving.

### H2 — what closing it actually took
Three attempts, and the first two *passed while the drift was injected*:

1. patterns too tight — "8 of 11" is written bold, plain and in table cells;
2. **`check_simulation()` was called AFTER `report_documents()`**, so its
   findings were computed and then thrown away. Found only by re-running the
   auditor's drift test and watching it pass;
3. patterns too loose — turbine τ collided with the oil, coolant and IAT-sensor
   constants, displacement with mistake 1's historical 1998 cc.

Settled on: scan **"N of 11"** in prose (unambiguous), and assert turbine τ and
displacement as **values only**. A value assertion catches the model moving; a
prose scan for those two would mostly catch the documents being right.

---

## MEDIUM — app findings all fixed

| id | status | what changed |
|---|---|---|
| **M1** env clamps at 200+trim, documents say `boost_ceiling_kpa` | **FIXED** | the flow-dependent ceiling is now actually applied in `_track_torque` |
| **M2** two sources of truth for the same physics | **FIXED** | one `damage_rate()` in `engine_env`; backpressure unified at 1.15 (was 1.12 in the env); app fallbacks routed through `BaselineECU.step` |
| **M7** nothing imports `app.server` | **FIXED** | test imports it and checks its three routes and its served limits; `scipy` dropped from requirements (imported nowhere) |
| **M8** placeholder zeros read as measurements | **FIXED** | physical range guards + leading-zero masking. `3f64372e` no longer seeds the block at 273 K |
| **M9** one baro miss retires the mismatch detector | **FIXED** | `_last_poll` advances only on success; a boost miss counts only if barometric is itself retired |
| **M10** thermal warning projects linearly | **FIXED** | projects the node's own first-order curve; **no time-to-threshold is quoted when the steady state is below the limit** |
| **M11** block node free-runs though coolant is measured | **FIXED** | block pinned to the sensor every sample; the drift it would have had is published as `block_residual_k` |
| **M12** generality_test: wrong damage fn, τ, runs at import | **FIXED** | τ from the episode's own exhaust flow; `main()` guard; "grew 0.7x" now says SHRANK |
| **M13** neutral quoted as a requirement | **FIXED** | documents quote the ±0.05 band; the random policy is seeded so its "for information" line stops moving |
| **M14** `--map-from-log` scored zero rows and exited 0 | **FIXED** | the missing alias is added, so it reproduces mistake 2 properly (**110.4 %** against 1.3 %), and it now exits non-zero when it scores nothing |
| **M3** "steady" windows are steady in speed and rpm only | **FIXED** | every point carries `load_ptp`, and `compare_log.py` prints it: **median load spread 0.52, max 1.25, and only 2 of 23 points hold within 25 %**. Recorded rather than filtered — filtering at 0.25 costs 23 points → 11 and narrows the span to 37–75 kPa, which trades away more coverage than the mislabelling costs |
| **M4** the `stable` flag does not implement its criterion | **FIXED (and the finding is bigger)** | `stable_rate` computes the rate between genuine READINGS alongside the gradient flag. They agree almost exactly — **93.9 % vs 92.7 %** — so the gradient artefact is real but is NOT what makes the flag unselective. The thresholds are: 40 g/s/s and 0.6 bar/s admit nearly everything a road drive does. "74 013 quasi-steady samples" means "warm rows not mid-transient", a much weaker claim |
| **M5** the envelope exists in two disagreeing versions, no script produces it | **FIXED** | new `fit_envelope.py` regenerates it from the shipped data with the method stated, and prints **independent readings beside every bin** |
| **M6** published figures no shipped script prints | **PARTLY** | the envelope now has one (`fit_envelope.py`). The thermal-fit RMSE table, the spark fit, the knock-limit fit and the retard filter still have none |
| **M16** per-step terms scale with `dt` | **FIXED** | `SLEW` and the smoothness penalty are per SECOND now. The environment runs at dt 1.0 / 2.0 / 0.2, so the reachable actuator movement per second differed **fivefold** between the hand-written policies and the agent meant to beat them |
| M15 | **OPEN** | a document sweep; `verify_docs` now catches most of what it named |

---

## LOW — app findings fixed

`L1` one damage function and one pair of protection constants · `L2` every
thermal condition evaluated, returns a list (the oil branch used to be skipped
whenever the turbine branch was in cooldown) · `L3` payload rebound instead of
`clear()`+`update()` · `L4` a blank `State` instead of the last one with `ok`
flipped · `L5` live mode polls only what something reads · `L6` the mismatch
window really is 30 s and the sweep table is re-captioned · `L7` the "novel"
alert names the right evidence band · `L11` absolute path removed from
`presentation/*.py`, and `index.html` is now scanned.

`L13` the pressure-ratio filter no longer silently drops a ratio above its
ceiling — it reports one · `L14` the baseline's charge temperature is computed
from its **own** block node, so the baseline-relative reference no longer moves
with the agent's cooling.

`L9` the 0.98 in `press_ratio` is now a named `INLET_DEPRESSION` constant with
its assumption stated · `L10` the coolant row is relabelled "regulation
response (NOT a free time constant)" · `L12` `check_map.lam_for` documents why
it still schedules by load and why no published cell changes.

**Open:** L8 only (compressor inlet temperature defined differently across
drives — `Intake air temperature` where present, `Ambient temperature`
elsewhere, 8–12 K apart, worth ~1.5–2 % on corrected flow).

### M5 — the envelope's top rests on four readings

`fit_envelope.py` reproduces the table and adds the column that matters:

| flow kg/s | PR p95 | rows | independent readings |
|---|---|---|---|
| 0.015 | 1.159 | 24 060 | 1120 |
| 0.195 | 2.440 | 124 | 13 |
| 0.285 | **2.515** | 53 | **4** |
| 0.315 | 2.473 | 47 | 5 |

**"PR 2.52" — the ceiling `plant.boost_ceiling_kpa` is built on, which every
boost claim inherits — is four measurements.** The envelope is densely
determined where it does not matter and barely determined where it does. Also
settles the 0.303-vs-0.314 discrepancy: same quantity, two filters; the highest
`stable` corrected flow is **0.314 kg/s**.

### H4 — what the row counts actually rest on

| population | rows | independent readings | inflation |
|---|---|---|---|
| above 180 kPa | 1150 | 74 lambda, 39 air mass | 15–30× |
| whole warm set | 46 707 | 1288 lambda | 36× |
| "517 pinned at the MAF ceiling" | 517 | **14 excursions** | 37× |

**Consequence, and it corrects this project's own reasoning.** A correlation on
~39 independent readings has a standard error near **±0.17**. So −0.56 and −0.49
are real (3 σ), but mistake 4's claim that **+0.23 "points the WRONG WAY"** is
1.4 σ — indistinguishable from zero. CLAUDE.md now says manifold pressure
carries *no detectable signal*, which still rejects a load table but is not
evidence that load points the other way.

### M3 — "steady" was steady in two channels out of five

Load, air mass, throttle and spark were never tested. Measured: the median
window's load swings **52 % of its own mean**, the worst **125 %**, and only
**2 of 23** points hold within 25 %. The residual survives that only because it
is linear in the MAF channel and cancels the rest (mistake 12) — which is a
reason to distrust the *label*, not the number. `compare_log.py` prints this
above the residual now, so the phrase "steady operating points" cannot be quoted
without the qualifier.

---

## Both experiments now agree, and they agree on something awkward

`check_premise.py` and `generality_test.py` were fixed independently and land in
the same place: **with the baseline ECU scheduled correctly, the standard
scenario produces no constraint violation at all.** The premise table's reactive
row becomes the baseline row; the H1 table is empty because there is no damage
to re-score under any cost curvature.

**That is a finding about the SCENARIO, not about preview.** The fix is to
re-choose it so the trigger is reached for a physical reason — a real grade, a
published towing cycle, a measured ambient — and never by turning a knob until
the gap looks good. Doing the latter would be mistake 12 happening to Phase D,
and it is the single most important thing to get right next.

---

## Why `pull01`'s peak turbine moved 593.7 → 601.4 °C

Traced before the expectation was touched. The modelled fallbacks now run
through `BaselineECU.step`, which applies the **IAT compensation** that
`base_spark` alone omits: −3.3° of spark at that drive's charge temperature,
worth **+18 °C of EGT** at the hardest sample (5832 rpm, 204 kPa). Enrichment
pulls the other way — −111 °C at full dwell — but `pull01`'s pulls are short, so
the retard dominates. The old figure was not "cooler"; it was modelling less of
the ECU.

`7475b5d7`'s peak is **unchanged at 884.9 °C**, which is the check that the
physics did not move: that drive reports spark and lambda, so the fallback path
never runs on it.

---

## The rule this whole exercise demonstrates

**The app's own suite reported 46 of 46 while all six of its defects were live.**
A suite pins the behaviour it was written to pin. That is mistake 11 one level
further down, and it is the reason every fix above ships with a regression test
that would have failed before it.

---

## 18 September — the tenth drive, and the bug it exposed

`drive10-20260918_233912.csv`: **119.5 minutes, 10 channels**, the longest single
drive the project has. It took the dataset from 175.5 to **295.0 minutes**, a
68 % increase in one file.

### It found a bug before it found anything else

**It contributed ZERO operating points on arrival** — 119 minutes, nothing. The
cause is **mistake 8, still half-unfixed for a fortnight.**

`steady_points()` sized its window as `WINDOW_S x average_rate` ROWS, then
rejected the window if its real wall-clock span came out wrong. The check added
after mistake 8 caught the symptom; the SIZING was never fixed. `drive10` logs
at **two rates** — 0.150 s for ~15 000 rows and 0.240 s for ~16 000 — so its
average of 5.06 Hz fits neither half. The window came out 304 rows, which at the
slow half's 0.239 s median spans **72.7 s**, i.e. **0.7 s outside** the 48–72 s
band. Every window failed, by less than a second, on a drive with **no logger
gaps at all**.

Windows are now sized in TIME (`_window_end` walks to `t[i] + WINDOW_S`), so a
window is 60 s by construction at any rate, and the span check goes back to
being a net for logger gaps rather than the thing doing the rejecting.

**It recovered points on EVERY drive, not just the new one:**

| drive | points before | after |
|---|---|---|
| 3aca2ec1 | 17 | **21** |
| 7475b5d7 | 26 | **30** |
| cb67b01f | 3 | **5** |
| **drive10** | **0** | **7** |
| total | 23 | **26** |

### What the drive bought

| | before | after |
|---|---|---|
| dataset | 175.5 min, 9 drives | **295.0 min, 10 drives**, 7 carrying samples |
| operating points | 23 | **26**, span 30–**75** kPa |
| load residual | 1.4 % derived / 1.1 % fitted | **unchanged at 1.4 / 1.1** over 26 points |
| quasi-steady samples | 43 853 | **74 013** |
| hottest oil measured | 107 °C | **117 °C** |
| charge-temp model vs boost channel | +3.0 % | **+1.9 %** |
| corr(lambda, MAP) | +0.23 | **+0.11** |

**The oil finding is the most valuable.** The band is 115–140 °C and our own car
had only ever reached 107, so the band was unverifiable and `validate.py`'s miss
uninterpretable. `drive10` reaches 117 °C (1320 rows above 110, 60 above 115), so
the band's lower end is now inside our own measurement and the model's 110.2 °C
is confirmed **~7 K too cool** rather than merely disagreeing with an unsourced
number.

**The charge-temperature model got better on more data**, +3.0 % → **+1.9 %**
against the car's own boost channel, over 762 model samples and 1097 logged
readings. A model that improves when the dataset grows was not fitted to it.

**corr(lambda, MAP) fell from +0.23 to +0.11**, which retires the last of
mistake 4's over-claim: AUDIT.md H4 had already shown +0.23 was 1.4 sigma and
not evidence of a "wrong way round" effect; at +0.11 it is under one. The
docstring in `engine_env.base_lambda` that made that argument is corrected.
Dwell STRENGTHENED, −0.41 → **−0.44**, which is the variable the model uses.

### What it could NOT buy, and why — two missing channels

| wanted | channel needed | present? |
|---|---|---|
| the compressor envelope | `Ambient pressure` | **NO** — `corr_flow` and `press_ratio` are NaN for all 36 277 samples, so the drive adds **nothing** to the envelope. Its top bins still rest on 4–5 readings |
| the knock question (H5) | `Target ignition angle from torque intervention` | **NO** — it has `Actual ignition angle` only, and the retard is the difference of the two |

**Ask for those two channels on the next drive.** They are the difference
between 119 minutes that moved six figures and 119 minutes that would also have
settled the biggest open question in the audit.


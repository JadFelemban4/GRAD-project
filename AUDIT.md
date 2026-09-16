# AUDIT.md — full technical review of `engine-supervisor`, branch `JMF-2340550`

Reviewed 15 September 2026. Branch confirmed before anything else:

```
$ git rev-parse --abbrev-ref HEAD
JMF-2340550
```

Merge-base with `main` is `e819cd7`; the branch carries ten commits over it
(`361a785` … `df7b7c3`), touching 46 files: the app, `pull01`, the charge-temperature
correction, `REFERENCES.md`, the reworked `verify_docs.py`, and the regenerated
`data/`. Working tree was clean apart from the untracked `presentation/plan.html`.

Nothing in the repository was modified by this review. All probes were run from
temporary scripts under `scratch/`, which are deleted at the end. Every number
below that is not quoted from a document was produced by a command shown next to it.

Findings are ordered so that silent numerical corruption comes first, as asked.

---

## What this project actually does

Based on the implementation, not the prose:

1. `plant.py` is a single-zone, crank-angle-resolved cycle model (Wiebe burn,
   Woschni heat loss, Chen–Flynn friction, Douaud–Eyzat knock integral) integrated
   with explicit Euler in crank angle at `dtheta = 0.5°`. Its inputs are speed,
   manifold pressure, charge temperature, coolant temperature, spark, lambda and
   backpressure; its outputs are torque, fuel flow, EGT, a knock integral, and the
   air mass it assumed. `map_from_airflow()` inverts the same speed-density relation.
2. `thermal.py` is a three-node lumped network (block, oil, turbine housing)
   stepped with explicit Euler at whatever `dt` the caller passes.
3. `engine_env.py` wraps both in a Gymnasium environment. Each step it runs a
   `BaselineECU` (fitted spark map, dwell-scheduled enrichment, knock feedback,
   fan schedule) through a three-iteration PI manifold-pressure loop to hit a
   torque demand from a simple vehicle model, then runs the agent's trimmed
   spark/lambda/boost through a second copy of the same loop, and integrates two
   independent thermal networks. Reward is baseline-relative. Damage is
   `exp((T_turb − 1123)/45) + 0.4·exp((T_oil − 408)/12) + 40·max(0, KI − 0.85)²`,
   integrated per step.
4. `check_premise.py` rolls four hand-written policies over a 720 s grade climb at
   `dt = 1 s` and prints the damage column that the whole README rests on.
   `generality_test.py` does the same with `dt = 2 s` over a `c_turb` sweep and
   re-scores the traces with a *different* damage function.
5. `build_dataset.py` turns the raw BimmerLink CSVs into a manifest, 22 de-duplicated
   60 s steady points, and 46 707 per-sample rows with manifold pressure inverted
   from air mass at a *modelled* charge temperature. `compare_log.py` scores the
   22 points; `verify_docs.py` recomputes dataset-derived figures and greps the
   documents for them and for retired values.
6. `app/` replays a log (or reads an ELM327) through the same `plant.predict`,
   `map_from_airflow`, `charge_temperature` and `ThermalNetwork`, seeds three thermal
   copies to bound the warm start, and raises thermal / mismatch / novel alerts.
   It serves three fixed static pages on localhost and appends alerts to one JSONL file.
7. `train.py` (SAC) has never been executed past its import guard; nothing has been trained.

**Where documented behaviour differs from actual behaviour** (each is expanded as a
finding below):

- CLAUDE.md mistake 10 says the broken neutral vector "is fixed in `neutral_action()`
  itself". `check_premise.py:11` and `generality_test.py:26` still carry their own
  copy of the broken formula and never call `neutral_action()`. The published
  baseline row is a policy with the fan off and the coolant pump at 30 %.
- README §3 says `plant.boost_ceiling_kpa` "now bounds" manifold pressure and that
  `MAP_CEIL_KPA` is the measured 250 kPa. The environment never calls
  `boost_ceiling_kpa`, and its inner loop clamps at `200 + boost_trim` kPa, not 250.
- `verify_docs.py` is described as the thing that "would have caught" a drift. It
  asserts no simulation-derived figure at all: not 829.2 / 548.6 / 437.6, not the
  13.4-point gap, not 48.0 s, not 8 of 11, not the 1.4 % residual, not the H2 table.
- The enrichment correlation −0.47 and the 0.87 / 0.79 cells are computed with
  every drive assumed to log at 4.6 Hz. The drives log at 4.34–6.63 Hz.
- `predict()` (used by `compare_log.py` and the app) models backpressure as
  1.15 × MAP; the environment and `check_map.py` use 1.12 × MAP.
- `estimator.py` says its damage rate is "the SAME model check_premise.py scores
  with". It omits the knock term.
- `validate.py` still prints "there is no compressor flow ceiling"; CHECKPOINT
  already lists this as open.
- `train.py`'s docstring still says 50 000 steps ≈ 1.5 h; every other document says 4.6 h.

---

## Are the headline numbers trustworthy

**Short answer: they reproduce exactly, and they are wrong as labelled.** Two
independent runs of `check_premise.py` print `829.2 · 548.6 · 437.6 · 548.6`, the
damage column is identical for seeds 0, 1 and 7, and regenerating `data/` from
`logs/raw/` gives byte-identical CSVs. Reproducibility is not the problem. What
each number means is. Five things, each established by running code:

**1. The "baseline ECU" row is a policy with the cooling switched off.**
`check_premise.py:11` and `generality_test.py:26` carry their own `NEUTRAL`
written with the pre-mistake-10 formula. Rescaled it is `[0, 0, 0, fan 0.0,
pump 0.3]`, and its pump component is −1.857, outside the `Box(−1, 1)` action
space. CLAUDE.md says mistake 10 was "fixed in `neutral_action()` itself";
neither experiment script calls it. In the same rollout, the environment's own
BaselineECU path (`episode_summary["damage_base"]`) scores 718.7, and the
correct `neutral_action()` vector scores 674.1.

```
$ python scratch/exp_premise.py base          (full float precision)
  neutral      damage=829.2470237731148 damage_base=718.6512753968736
  reactive     damage=548.6498477371352 damage_base=685.0381497694273
  predictive   damage=437.60139887686574 damage_base=679.0240479142518
  blinded      damage=548.6498477371352 damage_base=685.0381497694273
$ python scratch/exp_neutral.py               (agent path vs baseline path, neutral policy)
 t   Tturb_a Tturb_b  Toil_a Toil_b  Tblk_a Tblk_b    fan  pump
 700   879.4   876.6   128.1  108.2   115.5   94.1   0.00  0.30
```

The "peak oil 128 °C" and the 115 °C coolant in the baseline row are the pump at
30 % for twelve minutes in 42 °C air. The reactive and predictive policies set the
pump to 1.0 and the fan to `k` the moment they act, so part of their "damage
reduction" is turning the cooling back on. With `neutral_action()` as the idle
vector (`scratch/exp_neutral_fix.py`): baseline 674.1, reactive 531.7,
predictive 437.3, cuts of 21.1 % and 35.1 %, edge 14.0 points. The H2 table
inherits the same vector: its rows reproduce exactly with the shipped `NEUTRAL`
(16.5 / 18.0 / 26.0) and read 21.8 / 24.1 / 34.8 with the correct one
(`scratch/exp_h2.py`).

**2. The baseline ECU is scheduled on a manifold pressure the engine is not at.**
`engine_env.py:512` evaluates the ECU's spark map and enrichment timer at
`_map_for(torque_req, rpm, 0.0)` = `40 + 0.62·torque`, an open-loop guess. The
engine actually runs at whatever the PI loop in `_track_torque` settled on. On
the standard climb the guess is 224 kPa and the actual is 175 kPa, so the ECU
commands the knock-limited spark for 224 kPa (−0.8°, then −6° after IAT
compensation) where its own map gives +4.7° at 175 kPa:

```
$ python scratch/exp_premise.py trace
  t= 500 rpm= 2465 Treq= 297 actualMAP= 174.8 ffMAP= 224.2 spark_cmd= -6.1
         base_spark(ff)= -0.8 base_spark(actual)= 4.7  dwell=320.0 EGT= 1041 Tturb= 878
```

Scheduling the ECU on the tracked pressure instead (`scratch/exp_ecu_map.py`, a
one-line monkeypatch, everything else as shipped) changes the experiment
qualitatively:

```
== ECU scheduled on TRACKED (actual) MAP ==
  baseline (shipped NEUTRAL)   damage=  295.5  peak turb= 806 C  median spark in climb= +2.7
  reactive                     damage=  295.5  peak turb= 806 C
  predictive                   damage=  232.4  peak turb= 781 C
  blinded                      damage=  295.5  peak turb= 806 C
  reactive cut 0.0 %  predictive cut 21.4 %  edge 21.4 pts
```

The turbine peaks at 806 °C, never reaches the 850 °C trigger, and the reactive
policy never acts. The sentence in CLAUDE.md that justifies the scenario, "12 %
at 110 km/h … loads the real engine, and the constraint binds", is true only
because the baseline runs about ten degrees more retarded than its own
calibration. With both corrections applied (`scratch/exp_both.py`) the standard
scenario gives neutral = reactive = 255.0 at an 801 °C peak; a 16 % grade at
120 km/h (459 Nm) is needed before the trigger is reached at all (neutral
1185.1, reactive 973.1, predictive 803.8, edge 14.3 points).

**3. The 548.6 = 548.6 identity is algebraic, not evidential.**
`use_preview=False` does exactly one thing: `_preview()` returns zeros
(`engine_env.py:426`). `p_predictive` is `p_reactive` plus a term
`0.55·clip(ahead/0.08)` with `ahead` taken from `_preview()`; with `ahead = 0`
the two functions return the same vector on every step, so the trajectories are
bit-identical by construction. It holds at every `dt` tested (2.0, 1.0, 0.5,
0.2) because it cannot fail. It becomes a real test only for a trained agent,
whose blinded policy is a different network. "The identity has held every single
time" is therefore not the load-bearing fact the documents make of it.

**4. The gap is protection depth, not anticipation.** `p_predictive` applies at
least `k = 0.55` from 30 s before the grade and for the whole climb, while
`p_reactive` reaches only `k = clip(over/25) ≈ 0.36` at its 859 °C peak. A policy
that uses only the current grade (which is in the observation even with preview
off) and the same `k` formula lands on the predictive number:

```
$ python scratch/exp_premise.py depth
  grade_now (no preview, same k floor)       damage=437.7   (predictive: 437.6)
  reactive_deep (trigger + 0.55 floor)       damage=484.5
```

Of the 13.4 points, the part attributable to seeing 30 s ahead is about 0.1
point; the rest is "protect harder whenever the road is climbing". The README's
sentence "whatever gap exists is attributable to preview information and nothing
else" is not supported by this experiment. The same holds after both corrections
(`exp_both.py`: grade_now 225.3 vs predictive 230.9 at 12 %; 807.6 vs 803.8 at 16 %).

**5. The numbers are not converged in the cycle model's integration step.**
`plant.run_cycle` uses explicit Euler in crank angle at `dtheta = 0.5°` by
default and no caller passes anything else. Halving it moves EGT by 10–19 °C at
every operating point tested and moves the headline by more than the effect
being claimed is precise to:

```
$ python scratch/exp_dtheta.py
dtheta=0.5:  baseline=829.2 reactive=548.6 predictive=437.6 | edge 13.4 pts
dtheta=0.25: baseline=887.1 reactive=567.7 predictive=474.0 | edge 10.6 pts
```

The environment time step, by contrast, barely matters for these hand-written
policies (`scratch/exp_premise.py dt`, 720 s scenario):

```
  dt=2.0  baseline= 833.4 reactive= 550.0 predictive= 439.4 | edge 13.3 pts
  dt=1.0  baseline= 829.2 reactive= 548.6 predictive= 437.6 | edge 13.4 pts
  dt=0.5  baseline= 826.6 reactive= 547.7 predictive= 436.4 | edge 13.5 pts
  dt=0.2  baseline= 825.3 reactive= 547.1 predictive= 435.8 | edge 13.5 pts
```

**What would have to be true for the published figures to stand:** that a
baseline with its fan off and pump at 30 % is the intended reference; that a
production ECU schedules spark on an open-loop torque-to-MAP guess 50 kPa above
the real manifold pressure; that a policy which protects harder throughout the
climb is "preview"; and that first-order crank-angle integration at 0.5° is
converged. None of those is true, and the first two are contradicted by the
project's own code (`neutral_action()`, `damage_base`).

**What survives:** the sign of the effect (a policy that acts on upcoming grade
does reduce this damage function), the reproducibility of every script, and the
dataset-side figures: 175.5 min, 9 drives, 22 points at 30–74 kPa, 517 pinned
rows, 43 853 stable rows, PR 2.52, and the 1.4 % derived load residual, which I
re-derived independently of `compare_log.py` at 1.3738 %. All of those regenerate
exactly from `logs/raw/`. What the row counts mean is a separate finding (H4).

**Wall time, measured** (Windows 11, Python 3.13, one core; the last four rows ran
alongside other jobs, so treat them as upper bounds):

| script | README / docs say | measured |
|---|---|---|
| `plant.py` | ~30 s | 0.3 s |
| `validate.py` | ~4 min | 7.1 s |
| `check_premise.py` | ~90 s | 111 s |
| `verify_docs.py` | ~20 s | 2.2 s |
| `test_reward.py` | "about two minutes" | 269 s |
| `check_map.py` | — | 22 s |
| `compare_log.py` | — | 0.5 s |
| `app/test_replay.py` | "about a minute" | 79 s |
| `generality_test.py` | — | 544 s |

Every script exited 0 and printed the figures the documents quote
(`validate.py` 8 of 11 with τ 48.0 s; `verify_docs.py` "All 33 checks pass (241
figure mentions)"; `test_reward.py` 4 of 4, neutral −0.00438, starver −0.28044;
`check_map.py` 6 unreachable cells and 0 `knk`; `compare_log.py` 1.4 % derived,
1.1 % fitted; `app/test_replay.py` 36 of 36; `generality_test.py` H2
16.5 / 18.0 / 26.0).

---

## CRITICAL

### C1. The experiment scripts still use the pre-mistake-10 neutral vector — Confirmed bug
1. `check_premise.py:11`; `generality_test.py:26`; `presentation/dump_traces.py` imports `check_premise.p_neutral`.
2. `NEUTRAL = (2.0 * (0.0 - ACT_LO) / (ACT_HI - ACT_LO) - 1.0)` maps all five actions to "zero", which for the two absolute duties means fan 0.0 and pump 0.3 (the floor), and yields −1.857 for the pump, outside the declared action space. `engine_env.neutral_action()` was corrected for exactly this (CLAUDE.md mistake 10); these two files never call it.
3. Every preview figure in the repository is measured against a baseline with its cooling disabled: 829.2 / 548.6 / 437.6, the 33.8 % / 47.2 % / 13.4-point line in README, CLAUDE.md, CHECKPOINT.md, handoff.md, DOCUMENT_STATUS.md, `presentation/index.html` (24 mentions of 829.2), `presentation/data.js`, and the H2 table 16.5 / 18.0 / 26.0. The reactive and predictive policies restore the pump to 1.0 when they act, so part of their measured "protection" is cooling that the baseline row had switched off. The "peak oil 128 °C" in the baseline row is the pump at 30 %.
4. Evidence: section "Are the headline numbers trustworthy", item 1. `python scratch/exp_neutral.py` prints the rescaled vector `[0. 0. 0. 0. 0.3]` and the per-step traces; `python scratch/exp_neutral_fix.py` gives baseline 674.1 with `neutral_action()`; `python scratch/exp_h2.py` gives 21.8 / 24.1 / 34.8 for H2.
5. Fix: delete both local `NEUTRAL` definitions and import `neutral_action` from `engine_env`; make the protection policies return `neutral_action()` when idle and never command the fan below the neutral value. Then regenerate every document and `presentation/data.js`. `verify_docs.py` should grep for the old formula so it cannot return (it has returned once already).

### C2. The baseline ECU is scheduled on an open-loop MAP guess, not the pressure the engine runs at — Confirmed bug
1. `engine_env.py:512` (`self.ecu.step(self.rpm, self._map_for(self.torque_req, self.rpm, 0.0), …)`), with `_map_for` at `:393-396` and the actual pressure computed at `:515-517`.
2. The spark map, the IAT compensation base, and the enrichment dwell timer are evaluated at `40 + 0.62·torque_req`, which on the standard climb is 224 kPa against an actual 175 kPa. The ECU therefore commands the knock-limited spark for a load it is not at (−0.8° instead of +4.7°, −6.1° after IAT compensation), and the dwell timer runs above `ENR_LOAD` = 180 kPa while the engine sits at 175.
3. This is what makes the constraint bind. With the ECU scheduled on the tracked pressure the turbine peaks at 806 °C, below the 850 °C trigger; the reactive policy never acts; the four-row comparison collapses to "protect vs do nothing". The scenario justification in CLAUDE.md ("12 % at 110 km/h … the constraint binds") and README ("the turbine reaches 879 °C") rest on a ten-degree scheduling error, not on the engine. At a higher rpm the same defect would enrich on a phantom load.
4. Evidence: section "Are the headline numbers trustworthy", item 2; `python scratch/exp_premise.py trace` and `python scratch/exp_ecu_map.py` (outputs reproduced there).
5. Fix: feed `ecu.step()` the manifold pressure from the previous step's baseline tracking state (or run the tracking loop first and the ECU second, as a real ECU does: load measured, then spark and lambda looked up). Then re-choose the evaluation scenario so that the trigger is reached for a physical reason, re-run `test_reward.py`, and re-derive the premise table at a converged `dtheta` (H1).

### C3. The 13.4-point "preview advantage" is protection depth, and the ablation identity is guaranteed by construction — Confirmed bug (in the inference the code supports, not in a line of code)
1. `check_premise.py:83-92` (`p_predictive`), `:74-80` (`p_reactive`), `engine_env.py:422-427` (`_preview`); README.md:30-35, 350-358; handoff.md:62-64, 310-322.
2. `p_predictive` holds `k ≥ 0.55` from 30 s before the grade and throughout the climb; `p_reactive` never exceeds `k ≈ 0.36`. The two policies differ in how hard they protect, not only in when. With `use_preview=False` the preview term is literally zero, so the predictive function returns the reactive function's vector on every step; the "548.6 = 548.6 to the decimal" identity cannot fail and has no evidential weight.
3. The thesis claim "whatever gap exists is attributable to preview information and to nothing else" is contradicted by a policy with no preview that keys on the current grade and lands within 0.1 point of predictive (437.7 vs 437.6). The identity will only become a test once a trained blinded agent exists.
4. Evidence: `python scratch/exp_premise.py depth`; the `blinded` row equals `reactive` bit-for-bit at every `dt` in `scratch/exp_premise.py dt`.
5. Fix: make the reactive comparator apply the same protection depth (same `k` floor) so that timing is the only difference; report the current-grade policy as a third baseline; and stop presenting the algebraic identity as a result. Phase D's trained blinded agent is the real ablation.

## HIGH

### H1. The cycle model is not converged in crank-angle step and every downstream figure inherits it — Confirmed bug
1. `plant.py:159` (`dtheta: float = 0.5`), `:198-256` (explicit Euler); no caller passes another value except `presentation/dump_sweeps.py:41`, which passes 0.5.
2. Torque, EGT and the knock integral all move monotonically as `dtheta` is refined and are not converged at 0.5°: EGT changes by 10–19 °C between 0.5° and 0.1° at every point tested, torque by 0.5–1.6 %, KI by 2 %.
3. The premise edge moves from 13.4 to 10.6 points at 0.25°; `validate.py`'s EGT rows move by ~15 °C (the "777.3 outside" row would be further outside, the 714.5 row closer to the edge); the knock-limited spark row can move by a degree; the app's turbine estimate inherits the EGT offset. None of this is stated anywhere.
4. Evidence:
```
$ python scratch/exp_plant.py     (excerpt)
  cruise 2500/60/sp30   dtheta=0.5  T=120.09 KI=0.676 EGT=731.7 | dtheta=0.1  T=122.03 KI=0.688 EGT=750.4
  boost 3000/200/sp12   dtheta=0.5  T=474.32 KI=1.026 EGT=865.7 | dtheta=0.1  T=477.24 KI=1.047 EGT=880.8
  climb 2465/150/sp8    dtheta=0.5  T=309.33 KI=0.860 EGT=935.6 | dtheta=0.1  T=310.80 KI=0.880 EGT=948.5
$ python scratch/exp_dtheta.py
dtheta=0.25: baseline=887.1 reactive=567.7 predictive=474.0 | edge 10.6 pts
```
5. Fix: pick `dtheta` by a convergence study (0.1° or a second-order scheme), state the discretisation error next to every published figure, and add a regression that the headline moves by less than the claimed precision when `dtheta` is halved.

### H2. `verify_docs.py` cannot see any simulation-derived figure, so the checker is green while the headline drifts — Confirmed bug
1. `verify_docs.py:461-670` (`main`), `:255-268` (`figure`), `:477-486` (dataset-size patterns).
2. Every `figure()` call is a dataset statistic recomputed from `data/*.csv`. Nothing asserts 829.2 / 548.6 / 437.6, the 13.4-point gap, 8 of 11, τ = 48.0 s, the 1.4 % / 1.1 % residuals, k_fit 0.837, the H2 table, the 3×3 lambda cells, the envelope bins, or 587 / 887 / 226 / 279.5 / 232.7 as written in documents (587 and 887 are `chk` against constants, not scanned). Two pattern gaps let live false sentences through today: README.md:273 "175.5 minutes of the real car, pooled across eight drives" and `engine_env.py:116` "the full 175.5 minutes over eight drives" (175.5 min is nine drives). CLAUDE.md:156 and `logs/CHANNEL_SET_FINAL.md:27` still say the inversion "gives 1.3 %", a figure no script prints; nothing guards it.
3. The project's stated defence against mistake 11 does not cover the numbers the thesis rests on.
4. Evidence: an empirical drift test on a scratch copy of the tracked documents:
```
baseline                              -> All 33 checks pass
README: 548.6→561.2, 437.6→402.9, 13.4→19.1 points  -> All 33 checks pass
validation_table: τ 48.0→61.0 s, "8 of 11"→"10 of 11"  -> All 33 checks pass
README: residual 1.4 %→2.9 %                          -> All 33 checks pass
README: 517 samples→512 (control, dataset-derived)    -> exit 1, WRONG README.md:258
```
The tolerances in use (`tol`/`dtol` 0.002–1.0, correlations ±0.02, the boosted gap ±0.4 on 3.0) are adequate for rounding; coverage, not tolerance, is the defect.
5. Fix: factor the residual, the premise rollout, `validate.py`'s rows and the H2 table into importable functions and `figure()` them (the premise rollout takes ~2 min; cache it or gate it behind a flag); use `WORDNUM` in the minutes patterns; add a pattern for the residual.

### H3. The enrichment correlations and table were computed with every drive assumed to log at 4.6 Hz — Confirmed bug
1. `verify_docs.py:286` (`d["dwell"] = run / 4.6`), `:563` (`len(hh) / 4.6`); the drives log at 4.34–6.63 Hz (`data/manifest.csv` `rate_hz`), and the same file uses per-drive rates at `:601`.
2. Dwell in seconds is overstated by 44 % on the 6.6 Hz drives and understated on 7475b5d7. The published corr(λ, dwell) = −0.47 is −0.435 with per-drive rates and −0.413 on wall-clock time, outside its own ±0.02 tolerance; the 4500–7000 rpm row of the table reads 0.97 / 0.83 / 0.79 instead of 0.98 / 0.87 / 0.79; `ENR_DWELL_LO/HI` (2 s / 9 s) were fitted to a mis-scaled axis. `verify_docs.py` asserts the artefact, so the checker enforces the wrong number. "178 s above 207 kPa" happens to survive.
3. `base_lambda()` is the enrichment model the agent trains against and the thesis's "enrichment is thermal, not load-based" argument leans on the −0.47 figure.
4. Evidence: `python scratch/exp_dataset.py`:
```
  mode=fixed    n=1055 corr(lam,dwell)=-0.466  cells={..., (4500, 7000): [0.98, 0.87, 0.79, 465]}
  mode=perdrive n=1055 corr(lam,dwell)=-0.435  cells={..., (4500, 7000): [0.97, 0.83, 0.79, 465]}
  mode=wall     n=1055 corr(lam,dwell)=-0.413
```
5. Fix: accumulate dwell from the timestamps; re-derive the constants and the table; sweep the documents.

### H4. Every "n samples" figure is a count of forward-filled rows, roughly twenty times the number of readings — Confirmed bug (structure); Highly likely (statistical consequence)
1. `build_dataset.py:374-394` (row emission), `verify_docs.py:552-581` (counts and correlations), `engine_env.py:162-192` (the table), README.md:288-307.
2. The BimmerLink export polls one channel per row and forward-fills the rest: only 2–5 % of rows carry a fresh value for any given channel. The 1055 rows above 180 kPa contain 65 fresh lambda readings and 39 fresh MAF readings; "517 samples pinned at 1020 kg/h" is on the order of twenty independent readings; the n = 168 cell is a handful. Correlations quoted to two decimals on ~50 independent readings have standard errors near 0.14, so the "+0.23, the wrong sign" argument for dropping manifold pressure is not supported at that sample size (the reviewer's decimation across poll phases put the MAP correlation between −0.01 and +0.34).
3. CLAUDE.md mistake 4's rule "check how many samples support a fit" is currently answered with row counts.
4. Evidence: `python scratch/verify_agents1.py`:
```
  3aca2ec1 changed-per-row: air_gps=0.042 lam=0.032 rpm=0.052 press_ratio=0.057
  7475b5d7 changed-per-row: air_gps=0.033 lam=0.024 rpm=0.039 press_ratio=0.044
  rows above 180 kPa=1055 fresh lambda updates=65 fresh MAF updates=39
```
5. Fix: report independent readings beside every row count; compute the correlations on decimated data with a spread; state the poll structure in Chapter 3.

### H5. The plant's knock integral says the real car detonates continuously at its own calibration — Highly likely bug (in the knock model or its inputs)
1. `plant.py:248-256` (Douaud–Eyzat integral), `engine_env.py:537-539` (knock damage term), `app/estimator.py:350` (measured spark and lambda into `predict`).
2. Replaying 7475b5d7 through the app, which feeds the car's measured spark and lambda into `predict()`, gives KI up to 3.67 and KI > 0.85 on 369 samples, while the car's own knock-retard channel on that drive reads median 0° (CLAUDE.md, knock retard section). The omitted knock damage term on that drive integrates to 7468 against the app's reported 179.6. Either the knock model is far too pessimistic under boost, or the modelled charge temperature / inverted MAP under boost are off, or the spark channel is not the final angle. Any of the three undermines validate.py row 4 (11°, already unsourced), `BaselineECU.knock_limited_spark`, and the 40·max(0, KI−0.85)² term in the damage function.
3. The premise numbers do not currently exercise the knock term (KI stays at 0.3–0.4 because the baseline is over-retarded, C2). Fix C2 and it will.
4. Evidence: `python scratch/verify_agents1.py`:
```
  app thermal damage_total=179.6  omitted knock-term integral=7468.3  KI max=3.67  samples KI>0.85: 369
```
5. Fix: compare the model's KI at the car's measured operating points against the measured retard channel as a validation row; until it agrees, do not quote a knock-limited spark or a knock damage term as calibrated.

### H6. `train.py` cannot resume from a checkpoint, contrary to its docstring — Highly likely bug (not run: stable-baselines3 is not installed)
1. `train.py:94-103`, `:106`, `:109-110`.
2. The periodic `CheckpointCallback(save_freq=10_000, name_prefix="ckpt")` writes `ckpt_<n>_steps.zip`; the resume path looks only for `checkpoint.zip`, which is written once, after `learn()` returns. A laptop closed at hour 3 of a 4.6-hour run has nothing the script will load. On the one path where `checkpoint.zip` exists (a completed run), `learn(total_timesteps=a.steps)` starts the step count from zero and trains a second full run.
3. Phase D is the project's floor and needs ten overnight runs; the docstring promises "a closed laptop costs you minutes rather than the whole run".
4. Evidence: by reading; the save/load names differ in the source. Not executed because the import guard exits.
5. Fix: load the newest `ckpt_*_steps.zip` and pass `reset_num_timesteps=False` and the remaining step budget to `learn()`.

### H7. De-duplication is order-dependent and averages bookkeeping fields, so "22 distinct operating points" is a property of file order — Confirmed bug
1. `build_dataset.py:305-322` (`dedupe`), `:335` (`sorted(glob.glob(...))`), `verify_docs.py:494-497`.
2. Greedy first-match clustering with a chained running mean: feeding the same 59 windows in reverse yields 23 points; five shuffles yield 20, 21, 22, 22, 23. A new log whose name sorts before `3aca2ec1` re-seeds every cluster. `dedupe` also averages `t_start`, `t_span`, `max_gap`, `gear` and `brake`, and keeps only the first window's `source`: 8 of 14 merged clusters pool windows from two or three drives under one label, so the per-drive residual table in validation_table.md:153-154 attributes windows to the wrong drives, and the "no point straddles a logger gap ≤ 0.45 s" check runs on an averaged column whose true member maximum is 0.481 s (validation_table.md:219 and build_dataset.py:236 state 0.45).
3. The derived residual is robust (1.3736–1.3738 % across orderings); the point count, the fitted residual (1.16 % reversed) and the per-drive table are not.
4. Evidence: `python scratch/verify_agents2.py`:
```
windows after filters: 59 ; true max_gap over member windows: 0.481 s ; t_span range 49.0-68.7 s
dedupe in glob order: 22 points; averaged max_gap max 0.453
dedupe reversed: 23 points ; shuffled: 22, 22, 20, 21, 23
```
5. Fix: cluster on a fixed (rpm, load) grid or sort windows before merging; average only measurement channels; carry `max(max_gap)`, `min/max(t_span)` and the list of sources.

### H8. The app's modelled-lambda fallback can never enrich — Confirmed bug (reading), magnitude agent-measured
1. `app/estimator.py:344-348`.
2. `self.ecu.base_lambda(s.rpm, map_kpa)` omits `dwell_s`, so the v4 model's dwell term is zero and λ = 1.00 always; the estimator never accumulates `hot_dwell` the way `BaselineECU.step` does. This is the path for any log without a lambda column (pull01, per the test output's `modelled: [..., 'lambda', ...]`), for any live car without PID 0x44, and after that PID is retired mid-drive.
3. Under a sustained pull the modelled EGT runs 80–110 K hot (reviewer measurement: 5500 rpm at 2.3 bar absolute, λ 1.00 → 1040 °C vs λ 0.81 → 928 °C), which feeds the driver-facing thermal alerts.
4. Evidence: source reading; the reviewer's `predict()` comparison at dwell 0 and 9 s.
5. Fix: track dwell above `ENR_LOAD` in the estimator (or call `ecu.step`) and add a test that the fallback reaches 0.81 after 9 s at 5500 rpm.

## MEDIUM

### M1. The environment's manifold-pressure ceiling is 200 + trim kPa, not the documented 250, and `boost_ceiling_kpa` is never called by it — Confirmed bug (doc vs code)
1. `engine_env.py:411` (`MAP_CEIL_KPA + boost_trim`), `:418` (`min(self.MAP_CEIL_KPA, 200.0 + boost_trim)`), `:391`; README.md:189-191; `grep boost_ceiling_kpa` shows only `check_map.py` uses it.
2. README says `plant.boost_ceiling_kpa` "now bounds" MAP in the model and that `MAP_CEIL_KPA` is the measured 250 kPa; the inner loop clamps at 200 + trim (160–215 kPa) and the flow-dependent ceiling is not applied. Not binding on the standard scenario (175 kPa), so no current number moves; any heavier scenario, or a trained agent with +15 trim, hits an undocumented 215 kPa wall.
3. Fix: apply `boost_ceiling_kpa(mdot_air)` in `_track_torque` or change the documents.

### M2. Two sources of truth for the same physics — Confirmed
1. Backpressure: `plant.py:324/338` 1.15 × MAP (used by `predict`, `compare_log`, the app) vs `engine_env.py:381` and `check_map.py:64,114` 1.12 × MAP. Measured: EGT −6 °C, torque +1 Nm at the climb point.
2. Damage: `engine_env.py:538` uses literal 1123 / 408 (the comment says `TURB_PROTECT_K` "is the same number"); `app/estimator.py:388-389` re-types the formula without the knock term while its docstring says "the SAME model check_premise.py scores with"; `app/alerts.py:173` re-types 408.
3. Exhaust flow: `engine_env.py:519,533` and `app/estimator.py:362` use fuel × 15; `validate.py:150` uses fuel × (1 + 14.7 λ); `plant.py:283` computes the real value and nobody reads it. At λ = 0.81 the gas-side UA is 16 % high.
4. Fan: `app/estimator.py:376` one-step at 373 K vs `BaselineECU.step` three-step 367 / 372 K. Modelled spark: `app/estimator.py:342` uses `base_spark` alone, without the IAT compensation and knock retard the ECU applies.
5. Fix: one importable `damage()`, one backpressure constant, one exhaust-flow expression; route the app's fallbacks through `BaselineECU.step`.

### M3. "Steady" windows are steady in speed and rpm only — Confirmed
1. `build_dataset.py:274-278`.
2. Load, air mass, throttle and spark are not tested; among the singleton points, load swings up to 25.5 % and air mass by 60 % of its mean inside a "steady" window (7475b5d7, t = 2657 s: air ptp 17.8 g/s on a mean of 29.9, spark ptp 19.5°); the reviewer found windows with 47 % load swing and 65 kPa of MAP swing among all 59. The residual is not flattered (a strict ptp-load < 10 % subset gives 1.09 % on 11 points) because the comparison is linear in MAF and cancels the rest (mistake 12); the label "22 steady operating points" and the spark/lambda means attached to them are overstated.
3. Evidence: `python scratch/exp_misc.py` section C.
4. Fix: add a peak-to-peak criterion on load or air mass and report the surviving count.

### M4. The `stable` flag does not implement its documented criterion on a forward-filled export — Confirmed (flag); consequence limited
1. `build_dataset.py:216-220`, docstring `:34-38`.
2. `np.gradient` over a staircase is zero except on the two rows beside each update, so the flag rejects only those rows: 93.9 % of warm rows are "quasi-steady" (43 853 of 46 707; 2 337 rejected by the gradient). The mis-pairing the docstring worries about is smaller than it fears in the top bins, because MAF and boost are polled 0.2 s apart in the round-robin (median and p90 skew 0.2 s on the two boosted drives). So "43 853 quasi-steady samples" is a count of rows, not a steadiness selection; the reviewer's alternative envelope (PR max 2.415 with an update-aware filter) I could not reproduce and do not assert.
3. Fix: compute the rate between successive readings of each channel; say what the flag does in the docstring.

### M5. The compressor-envelope table exists in two versions that disagree with each other and with a recompute, and no script produces it — Confirmed (inconsistency)
1. `plant.py:380-386` (RMS 0.129) vs `validation_table.md:315-321` (RMS 0.135; different top bins 0.280 → 2.515, 0.301 → 2.333 vs 0.289 → 2.515, 0.303 → 2.395).
2. Recomputed with the stated method (stable, 0.03 kg/s bins, p95, n ≥ 15): 0.021 → 1.159, 0.070 → 1.582, 0.197 → 2.440 (documents 0.194 → 2.219), 0.250 → 2.342, 0.307 → 2.473; RMS 0.130. The fit constants A, B are not regenerated by any shipped script. `verify_docs.py` asserts only the 2.52 maximum. The measured top of range is quoted as both 0.303 (CLAUDE.md, README, validation_table §E) and 0.314 kg/s (validation_table §D); the stable maximum is 0.314.
3. Evidence: `python scratch/exp_envelope.py`.
4. Fix: ship the fit script; have `verify_docs.py` assert the bins and the RMS.

### M6. Published figures no shipped script prints — Maintainability issue (reproducibility)
1. validation_table.md:258-275 (thermal calibration RMSE table and the 800 W/K sweep), CLAUDE.md:655-662 (radiator fit R² = 0.157), CLAUDE.md:643-648 and REFERENCES.md:211 (knock retard p99 9.8° over 10 896 filtered samples), engine_env.py:54-57 and README.md:331 (spark fit residual 1.66° vs 8.43°), engine_env.py:86-89 (knock-limit fit 0.95°), `validation_table.md:87` (+11.0 K / +6.8 K oil after filter).
2. None has a generating script in the repository, which the project's own rule forbids. My attempt at the knock-retard figure with a plausible steady-gear filter gives p99 21.75° over 16–17 k rows, so the published 9.8° depends on an unspecified filter that removed a third of the rows.
3. Evidence: `grep` list in this review; `python scratch/exp_knock.py`.
4. Fix: commit the calibration scripts (thermal time-series driver, spark fit, knock-limit fit, envelope fit, retard filter) and have `verify_docs.py` run or import them.

### M7. The app server cannot be imported in this environment, and nothing tests that it can — Confirmed bug (environment)
1. `requirements.txt` (`fastapi>=0.110`); installed `fastapi 0.65.1` with `pydantic 2.12.5`; `app/server.py:49`.
2. `python -c "import app.server"` fails with `ImportError: cannot import name 'Undefined' from 'pydantic.fields'`. `app/test_replay.py` never imports the server, so "36 of 36 pass" (CHECKPOINT.md:563) says nothing about the product running. `scipy` and `Flask` are listed or installed and imported nowhere; `obd` is listed as an active requirement but is live-only and not installed.
3. Fix: upgrade fastapi; import `app.server` in the test suite; drop scipy and Flask from requirements.

### M8. Placeholder zeros in the exports are parsed as measurements — Confirmed
1. `app/reader.py:213-227` (`_f`), `build_dataset.py:135-146` (`col`).
2. BimmerLink writes `0` for a channel until its first poll; the first rows of every log show `Coolant temperature 0`, `Ambient temperature 0`, `Ambient pressure 0`. In replay, 3f64372e and fb988991 reach the estimator's `rpm ≥ 400 & air > 0` gate while coolant is still 0, so `_seed` sets the block and oil to 273 K and the block needs minutes to recover; a placeholder spark of 0° at idle moves the seed EGT by ~46 K (reviewer measurement). In `build_dataset.py` the warm filter removes these rows from the samples, but `manifest.max_map_kpa` and the derived columns see them.
3. Evidence: raw-file heads in this review (`3f64372e`: first six rows of coolant, ambient, pressure all `0`).
4. Fix: mask each column's leading run of zeros to None in the reader; add physical guards (coolant below −40 °C is not a reading).

### M9. One transient miss on barometric pressure retires the mismatch detector for the session — Confirmed by reading
1. `app/reader.py:458-461` (`_last_poll` set before `_query`, never cleared on a miss), `:492-507` (`_derive_boost` notes a boost miss whenever `p_amb_psi` is None).
2. Barometric carries `min_period_s = 30`, so after one NO DATA it is not re-asked for 30 s, while `boost_psi` collects a miss every cycle and is retired after `MAX_MISSES = 5` (7–15 s live). The fake adapter in `test_replay.py` never fails a single PID once, so the test cannot see it.
3. Fix: advance `_last_poll` only on success; count a boost miss only when barometric itself is retired; add a one-shot-miss case to the fake.

### M10. The thermal warning projects linearly what a first-order node cannot reach — Highly likely bug (reviewer-measured)
1. `app/alerts.py:293-294, 308-315`.
2. `projected = T + rate·30 s`; the housing's τ is 27–51 s depending on exhaust flow, so a 30 s continuation at constant inputs reaches 61–75 % of the linear projection. On 7475b5d7 five of the ten warns sit within 5 K of the limit by linear projection and 20–110 K short of it by the model's own dynamics (e.g. 578 °C at 9.1 K/s projects 852 °C; the model peaks at 743–785 °C). The driver-facing "threshold in about N s" is a quantitative claim the model contradicts.
3. Fix: project with a throwaway copy of the network, or with `_steady_turb_k` and τ.

### M11. The block node free-runs although coolant is measured every sample — Highly likely (reviewer-measured 14 K drift)
1. `app/estimator.py:270-272` (only `_seed` uses `ect_k`), `:375-378`; `app/reader.py:114-115` calls coolant "the thermal network's measured node".
2. The radiator group is unidentifiable (thermal.py:89-103), so the free-running block is the least-trusted node while its truth arrives each sample; on 7475b5d7 it drifts 14 K from the sensor and the oil node inherits it. With `DEFAULT_V_KMH = 0` a log without vehicle speed loses all ram-air cooling.
3. Fix: pin `t_block` to measured coolant on every update when present and integrate only oil and turbine; log the residual as a self-check.

### M12. `generality_test.py` scores with a different damage function, mislabels τ, and runs at import — Potential risk
1. `generality_test.py:77-89` (`damage`: scale 25, per-sample sum), `engine_env.py:538` (scale 45, integrated); `:130` (`UA = 0.9·112.5 + 18`); `:93` onward (module-level execution).
2. The H1/H2 percentages are not the premise damage model and cannot be compared to it. The τ labels assume 112.5 g/s exhaust; the climb produces ~103 g/s, so τ is 54.0 s not 50.3 and H/τ 0.56 not 0.60 (`scratch/exp_misc.py` D). `import generality_test` runs nine minutes of rollouts. The H1 summary line prints "preview edge grew 0.7x" for a shrink from 36.8 to 26.0 points.
3. Fix: import the env's damage function; compute τ from the episode's own exhaust flow; guard with `if __name__ == "__main__"`.

### M13. `test_reward.py`'s neutral figure is one preference draw, quoted as a requirement — Potential risk (documentation)
1. `test_reward.py:57-58, 81-82`; `engine_env.py:457-481`; handoff.md:75, 146 ("neutral must score −0.00438").
2. `reset(seed=…)` re-creates the RNG, so the reset seed governs and the constructor seed is used only when `reset()` gets none; `check_premise.py` (0/0) and `test_reward.py` (0/1) therefore draw different `w`. The damage column does not depend on `w` (identical for seeds 0, 1, 7), so the two scripts are comparable on damage; the reward is not, and "−0.00438" is the value for `w = [0.578, 0.023, 0.399]`: reset seeds 2 and 3 give −0.00407 and −0.00273. The `action_space.sample()` line is unseeded (labelled "for information"; it moved between my runs: −0.08782, −0.08293).
3. Fix: quote the neutral check as "|r| < 0.05 for the seed used" and seed the action space.

### M14. `compare_log.py --map-from-log` scores zero rows and exits 0 — Confirmed (already listed as open in CHECKPOINT.md:360-365)
1. `compare_log.py:41-50` (no alias for the pressure channel under the short schema), `:118-123`.
2. The mode that "exists only to reproduce the failure for the thesis" prints an empty table and `too few points` on the canonical dataset; fail-open, the shape of mistake 9.
3. Evidence: captured run in this review.
4. Fix: add the alias and exit non-zero on zero scored rows.

### M15. Stale or exempt document figures the checker cannot see — Confirmed
1. `DOCUMENT_STATUS.md:21` names the superseded residual over 17 points as "what replaced" the older figures (current: 1.4 % over 22) and `:50` writes a check count into prose; the file is in `RETIRED_EXEMPT`. CLAUDE.md:156 and `logs/CHANNEL_SET_FINAL.md:27` say "1.3 %". README.md:23-26 timing estimates are wrong by 10–30× (table above). `train.py:17-18` says 1.5 h. `validate.py:224-227` prints that there is no compressor flow ceiling.
2. Fix: sweep and add patterns.

### M16. Per-step terms in the environment scale with `dt` — Potential risk (design)
1. `engine_env.py:342` (`SLEW` per step), `:499`, `:552` (`smooth` per step), `:413-418` (three PI iterations per step regardless of `dt`), `:240` (knock retard per second, correct).
2. The same environment runs at `dt` = 1.0 (premise), 2.0 (generality) and 0.2 (training). The hand-written premise numbers move only 0.5 % over that range (table above), but the smoothness penalty per second and the reachable action slew per second change fivefold between the premise scripts and `train.py`, so a trained agent's reward landscape is not the one the hand-written policies were scored on.
3. Fix: express slew and smoothness per second; fix `dt` project-wide.

## LOW

### L1. Duplicated protection constants — Maintainability
`engine_env.py:538` literal 1123.0 / 408.0 beside `TURB_PROTECT_K` at `:338`; `app/alerts.py:173` `OIL_PROTECT_K = 408.0`; `app/estimator.py:388-389`. Fix: one `damage()` and one pair of constants.

### L2. `_thermal` returns after the turbine branch even when `_fire` is in cooldown — Confirmed by reading (low impact)
`app/alerts.py:303-315` return `self._fire(...)`, which is `None` in cooldown, so the oil branch at `:316-324` is skipped whenever the turbine is at or projected to the limit. The oil limit (135 °C) is in any case unreachable with `ua_block_oil = 800` (network settles at 110 °C; hottest logged oil 107 °C). Fix: evaluate every condition and return a list.

### L3. `_latest.clear()` then `update()` from the reader thread while the event loop serialises the same dict — Potential risk
`app/server.py:88-90`, read at `:159, :171, :225`. A frame can serialise as `{}`; the reviewer reproduced it standalone (server itself will not import here, M7). Fix: build the payload and rebind the reference.

### L4. The dashboard keeps painting stale fields when `ok` is false — Potential risk
`app/estimator.py:294-299` returns the previous `State` mutated to `ok=False`; `app/static/index.html:211-238` paints every field regardless. `driver.html:121-127` handles it. Fix: return a fresh `State` or blank the panels.

### L5. Live mode polls channels nobody consumes, and one more than the budget note admits — Maintainability
`app/server.py:266` (`LiveReader(port=a.port)` → `optional=True`) polls `OIL_TEMP` and `INTAKE_TEMP` every cycle; `oil_c` and `iat_pre_c` are read by no consumer. `_derive_boost` (`reader.py:495`) queries `INTAKE_PRESSURE` every cycle, a seventh per-cycle round trip that the docstring at `:343-347` says does not exist. `Stream.buf` (`:518-529`) is filled and never read. Fix: default `optional=False`, give slow channels a period, use `oil_c` to anchor the oil node.

### L6. Mismatch window is 30 s in code and 20 s in its docstring and margin analysis — Maintainability
`app/alerts.py:180` vs `:333` and the commit message's "worst 20 s median … 13.6 %". Fix: re-run the sweep at the shipped window.

### L7. The "novel" alert labels the boost-checked region as extrapolation — Potential risk
`app/alerts.py:212, 401-415`: 30–74 kPa is the load-residual range, which tests nothing about the inversion (mistake 12); above 200 kPa is where the inversion was checked against the boost channel. Fix: reword, or gate on what the app actually has less evidence for.

### L8. Compressor inlet temperature is defined differently across drives — Potential risk
`build_dataset.py:189-190` uses `Intake air temperature` where present and `Ambient temperature` elsewhere; the two differ by 8–12 K while running, ~1.5–2 % on corrected flow, so the envelope's x-axis is inconsistent between drives; `check_map.py:49` evaluates the ceiling at the 298 K default. Fix: one definition; pass the inlet temperature.

### L9. `press_ratio` divides by 0.98 × ambient while documented as "(ambient + boost) / ambient" — Maintainability
`build_dataset.py:33` vs `:191-193`; PR min over stable rows is exactly 1/0.98. Self-consistent with `boost_ceiling_kpa`'s 99.3 kPa default, but the 2 % inlet depression is an undocumented assumption inside "PR 2.52 = 250 kPa". Fix: document it.

### L10. Two `validate.py` rows do not measure what their labels say — Maintainability
"Coolant apparent time constant 9.5 s" (`validate.py:183-187`) is the time to cover 63 % of a 4.5 K change from a warm start with the stand-in thermostat regulating, against a 1–600 s band; row 4 (knock-limited spark) has no source (REFERENCES.md §3). Both count toward "8 of 11". Fix: relabel or drop.

### L11. `presentation/` is outside every check and hard-codes an absolute path — Maintainability
`presentation/index.html` carries 24 × 829.2, 70 × 548.6, 16 × 437.6, 13.4 points and −0.47 (all affected by C1/H3); `verify_docs.py` scans only `.md` and `.py`. `presentation/dump_sweeps.py:4` and `dump_traces.py:69` insert `C:\Users\endof\OneDrive\Documents\engine-supervisor` into `sys.path`. Fix: derive the path from `__file__`; scan `presentation/*.html`.

### L12. `check_map.py` schedules lambda by load — Maintainability (CHECKPOINT open item)
`check_map.py:76-77`; mistake 4 says load is the wrong variable. No cell changes today.

### L13. `verify_docs.py` filters pressure ratio to 0.8–3.0 before taking the maximum — Potential risk
`verify_docs.py:543-544`: a future PR above 3.0 would be silently dropped from "highest pressure ratio observed". No row exceeds 3.0 today.

### L14. The baseline reference depends on the agent's actions through the charge temperature — Potential risk
`engine_env.py:509` computes `iat_k` from the agent's block temperature and passes it to both the baseline and the agent evaluation (`:512-517, :529-531`), so the "baseline-relative" reward has a reference that moves with the agent's fan and pump. With the cooling-disabled neutral (C1) the difference is 1.5 K; with a trained agent it is unbounded. Fix: compute the baseline's charge temperature from `thermal_base`.

## NITPICK

- `generality_test.py:119-120` prints "preview edge grew 0.7x" for a 36.8 → 26.0 shrink.
- `check_premise.py:49` accepts a `w` argument that `__main__` never passes.
- `plant.py:290` recomputes `mfb` over the whole crank array after the loop already evaluated it; `build_dataset.py:184-185` inverts 46 707 samples in a Python loop. Performance only.
- `extract_steady.py` lacks the span and gap checks `build_dataset.py` added and is documented as superseded; it still ships beside the routine that says to run it.
- `DOCUMENT_STATUS.md:50` writes a check count into prose, which CHECKPOINT.md:427-429 says never to do.
- `logs/CHANNEL_SET_FINAL.md:83` says the after-filter oil channel runs +12.5 K hotter; validation_table.md:87 says +11.0 K median / +6.8 K above 100 °C, from a different drive. Neither is scripted.

---

## Confidence ledger

| label | count |
|---|---|
| Confirmed bug | 20 (C1, C2, C3, H1, H2, H3, H4, H7, H8, M1, M2, M3, M4, M5, M7, M8, M9, M14, M15, L2) |
| Highly likely bug | 4 (H5, H6, M10, M11; plus the statistical half of H4) |
| Potential risk | 9 (M12, M13, M16, L3, L4, L7, L8, L13, L14) |
| Maintainability issue | 8 (M6, L1, L5, L6, L9, L10, L11, L12; plus the nitpicks) |
| Style preference | 0 |

Every figure in C1–C3, H1–H4, H7, M3–M5, M13 and the "trustworthy" section was
produced by a command I ran in this session; the outputs are quoted. Findings
marked "reviewer-measured" (the magnitudes in H8, M10, M11, and the placeholder
EGT shift in M8) come from the two independent reviewers I dispatched; I
verified their mechanisms by reading the code and, where cheap, by re-running
(H4's fresh-reading counts, M4's skew, M8's raw-file heads, H7's dedupe orderings,
the knock term in H5), but I did not re-run their EGT deltas, the 14 K block
drift, or the ten-warn projection table.

**Could not run or verify, and why:**

- `train.py` past its import guard: stable-baselines3 is not installed and installing it would change the environment. H6 is from reading the source.
- `app/server.py` and the three routes: the installed fastapi cannot import (M7). Route and path handling were reviewed by reading only (three literal page names, no user-controlled path reaches `open()`, `--review` is CLI-only, host is 127.0.0.1).
- Live OBD mode and the python-obd PID scalings for `TIMING_ADVANCE`, `COMMANDED_EQUIV_RATIO`, `INTAKE_TEMP`: no adapter, library not installed. The MAF g/s→kg/h and kPa→psi conversions were checked in the fake-adapter test.
- The knock-retard p99 9.8° (M6): the filter that produced it is unspecified; my plausible filter gives 21.75°.
- The thermal calibration table, the 800 W/K sweep, the R² = 0.157 radiator fit, the spark and knock-limit fit residuals, the envelope fit constants: no script exists to regenerate them (M6).
- A converged `dtheta` for the premise numbers: I ran 0.25° (H1); 0.1° would take roughly five times the 111 s per rollout and was not run.
- The third independent reviewer (simulation core) was terminated by a session rate limit before reporting. Its scope is covered by my own probes (`scratch/exp_premise.py`, `exp_neutral*.py`, `exp_ecu_map.py`, `exp_both.py`, `exp_dtheta.py`, `exp_plant.py`, `exp_h2.py`, `exp_misc.py`), but it is not an independent second reading.
- The reviewer's alternative compressor envelope (PR max 2.415 with an update-aware `stable` flag): not reproduced; the skew measurement in M4 argues against its mechanism, so it is not asserted.
- Whether the real ECU schedules on measured load rather than an open-loop torque map (C2): assumed from how production ECUs work and from the fact that the repository's own calibration data is measured load; the conclusion that the trigger is not reached at 12 % / 110 km/h holds for the model as written either way.

---

## Top 3 fixes

1. **Replace the local `NEUTRAL` in `check_premise.py` and `generality_test.py` with `engine_env.neutral_action()` (C1).** One line each, and every preview figure in the repository, the presentation and the Novelty Statement changes. Nothing else can be quoted until this is done, and it is the cheapest fix with the largest effect on what the thesis currently claims.
2. **Schedule `BaselineECU` on the manifold pressure the engine is actually at (C2), then re-choose the evaluation scenario and re-run `test_reward.py`, at a `dtheta` shown to be converged (H1).** This decides whether the constraint binds for a physical reason, and with it whether Phase D has an experiment. Doing it after step 1 keeps the two effects separable, which the project's own "change one thing" rule requires.
3. **Make `verify_docs.py` assert the simulation-derived figures and use per-drive sample rates (H2, H3).** Until the premise table, the validation rows, the residual and the H2 table are recomputed and compared as the documents state them, the corrected numbers from steps 1 and 2 will drift back the way 55 figures did in September. Fix the 4.6 Hz divisor in the same change so the checker stops enforcing an artefact.

After those three: H4 (report independent readings), H5 (validate the knock integral against the retard channel), H6 (`train.py` resume) before any overnight run, and H7 (deterministic de-duplication) before the next drive arrives.

---

## Appendix: the probe scripts behind the evidence

All probes lived under `scratch/` and were deleted after the run, as instructed.
Each was a short, read-only Python script importing the repository's own modules;
what each did is stated so the evidence can be rebuilt:

- `exp_premise.py` — `check_premise.py`'s four rollouts at full float precision with `damage_base` printed; the same at `dt` 2.0 / 1.0 / 0.5 / 0.2; seeds 0 / 1 / 7; a per-step trace of feed-forward vs tracked MAP and the ECU's spark at each; and two no-preview policies (`grade_now`, `reactive_deep`).
- `exp_neutral.py` — the neutral policy with agent-path and baseline-path thermal states side by side.
- `exp_neutral_fix.py` — the four policies with `engine_env.neutral_action()` as the idle vector, two protection variants.
- `exp_ecu_map.py` — a one-line monkeypatch making `_map_for` return the previous step's tracked baseline MAP, everything else as shipped.
- `exp_both.py` — both corrections together, at 12 % / 110 km/h and 16 % / 120 km/h.
- `exp_dtheta.py` — `engine_env.run_cycle` bound to `dtheta` 0.25 via `functools.partial`.
- `exp_h2.py` — `generality_test.py`'s H2 sweep with the shipped and the corrected neutral.
- `exp_plant.py` — `run_cycle` at five `dtheta` values and three operating points; backpressure 1.12 vs 1.15; inversion round trip; ceiling at 298 vs 315 K.
- `exp_dataset.py` — dwell with a fixed 4.6 Hz, per-drive rates and wall-clock time; the 22-point residual re-derived without `compare_log.py`.
- `exp_misc.py` — seed semantics; load steadiness inside the singleton windows; in-episode turbine τ; thermal step-size check; the `tol`/`dtol` values in `verify_docs.py`.
- `exp_envelope.py`, `exp_knock.py` — recompute of the compressor bins and of the knock-retard percentile.
- `verify_agents1.py`, `verify_agents2.py` — checks of the reviewers' claims: forward-fill fractions, `stable` counts, fresh readings above 180 kPa, MAF/boost skew, the knock term on 7475b5d7, raw-file placeholder rows, regenerated windows and dedupe orderings.
- `timed.py` — every project script with wall-clock timing and captured output.
- The `verify_docs.py` drift test ran on a scratch copy of the tracked documents and `data/` outside the repository; the repository's own copies were never edited.

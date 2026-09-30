# conflict-test_reward -- `test_reward.py` (1 hunk)

Label: conflict-test_reward. Merge under review: `JMF-2340550-merge` in
`C:/Users/admin/Documents/graduation project/To main` (Jad = HEAD =
`JMF-2340550-sep17` @ 086c519; Ghassan = `origin/JMF-2340550` @ 74de99a; base f6b46e9).
Nothing in MERGE or in GRAD-project was modified. All runs were made in copies under
`scratchpad/work/conflict-test_reward/`.

## Verdict

TAKE BOTH. The single hunk is two independent additions at the same spot: Jad's Phase D2
gate (`D2_ROADS`, `_d2_job`, `main_random_road`, commit 8e91276) and Ghassan's training-road
roller (`road_roll`, commit c6e9e03). Neither calls the other and every name either side
needs is present in the merged tree. But the silently merged docstring and several figures
are now false, and -- more important -- on the merged plant (Ghassan's physics) the fixed-road
starver check passes on the 0-20 s launch alone (97 % of its penalty), so Ghassan's
training-road starver check is the only one left that holds a sustained torque shortfall.
It must be kept. Proposed final file: `scratchpad/work/conflict-test_reward/test_reward.PROPOSED.py`.

## What was read

- MERGE/test_reward.py, 358 lines, in full (markers at 132 / 221 / 222 / 244).
- JAD/test_reward.py (285 lines), GHASSAN/test_reward.py (231), BASE/test_reward.py (160), each in full.
- Commits touching the file: Jad 8e91276 (22 Sep, D2 gate) and 5ef1aa2 (17 Sep merge; its
  test_reward.py is byte-identical to base -- `git diff f6b46e9 5ef1aa2 -- test_reward.py` is empty);
  Ghassan c6e9e03 (27 Sep, training roads + gearbox checks) and cbb8d09 (29 Sep, one line:
  `Vehicle.DELIVERABLE_TORQUE` -> `Vehicle().DELIVERABLE_TORQUE`, now a derived property).
  Full messages read, plus 0d8e6ca, e27564e (Ghassan) and 27e720c and the mistake-17 commit
  (Jad) for the starver-margin history (-2.16 -> -0.10434 -> -0.90349).
- For the physics: GHASSAN/engine_env.py in full; JAD/engine_env.py via `diff -u` against base
  (docstrings, one comment block, `v_kmh` default -- no reward change); MERGE/engine_env.py
  conflict region (docstring only, lines 1009-1085); plant.py `boost_ceiling_kpa` on both sides;
  MERGE/thermal.py conflict hunk (98-211); JAD/random_road.py in full; JAD/full_run.py in full;
  GHASSAN/check_roads.py (first 80 lines); GHASSAN/derived.py; data/derived_params.json
  (boost_ceiling, deliverable_torque); JAD/AUDIT2.md Part 6.
- Orchestrator logs `runs/{jad,ghassan}_{test_reward,check_premise}.log`.
- NOT read in full: train.py (grep only), evaluate.py, verify_docs.py (grep only),
  check_random_road.py.

## The hunk (MERGE lines 132-244)

| | content |
|---|---|
| base (221-222) | nothing -- neither block existed |
| Jad (133-220), 8e91276 | `D2_ROADS` = (120,12 %), (300,12 %), (120,16 %), (300,16 %), (300,13.73 %); `D2_DURATION` 480; `_d2_job` (neutral / starve / random / preview on `random_road.climb` at dt 0.2); `main_random_road` (Pool, per-road PASS/FAIL with the same four rules). Comment: "13.73 %, NOT 14.0 % ... (+6.9 K)". |
| Ghassan (223-243), c6e9e03 | `road_roll(job)`: one road at dt 1.0 -- the 9.3 % "band" road on `make_grade_climb(dt=1.0)` or a `TerrainTrainingEnv` family -- returning mean reward and p95 tracking error. |

Relation: take-both. The conflict exists only because both inserted after
`obs_differs_without_preview`. AUDIT2.md Part 6 (merge simulated against Ghassan's 7f6c7f1,
19 Sep) had test_reward.py merging clean; it conflicts now because of c6e9e03.

Silently merged around it (all compatible): Ghassan's imports (`TerrainTrainingEnv`, `Vehicle`,
`measure_deliverable_torque`, `TRACK_TOL`) and `BAND_GRADE`; Jad's `roll(..., cycle=None)` and
`obs_differs_without_preview(..., cycle_fn=None, start_s=180.0)` (behaviour-identical at defaults:
n_steps = int(min(295, 190)/0.2) = 950 either way); Jad's `--road/--jobs` args and early exit;
Ghassan's pool and four extra checks in `main()`.

Verified running (merged candidate = MERGE with test_reward "both", engine_env and thermal hunks
resolved to Ghassan's side): `import test_reward, random_road` succeeds -- random_road's import-time
assertion that `climb(180, 12 %) == make_grade_climb()` holds on the merged plant;
`_d2_job(('neutral',300,0.12,30))` -> -0.00417; `road_roll(('flat',11,'neutral',40))` ->
(-0.00233, p95 0.0171). AST comparison (docstrings stripped): merged engine_env.py, thermal.py,
plant.py, derived.py and data/derived_params.json are code-identical to Ghassan's; random_road.py
to Jad's. So the merged default run prints Ghassan's numbers for the shared checks (neutral
-0.00028, starver -0.13265, |d obs| 1.44, random +0.00436) -- by code identity and determinism;
my instrumented rollouts reproduce every one of the four branch figures exactly.

Stale in the hunk (Jad's block): "13.73 %" is no longer the notch; "+6.9 K" is the old plant's
margin (not re-measured on the merged plant: UNVERIFIED). "14.0 % (+12.7 K)" is labelled design
history and can stay. Ghassan's block has no figures.

## Measurements (all in copies; python 3.12 from the task, PYTHONIOENCODING=utf-8)

Probe = `probe_reward.py`: test_reward's own rollout (make_grade_climb(300), env seed 0,
reset seed 1, dt 0.2, same action functions), instrumented per step. Weights for this episode:
w = [0.578 tracking, 0.0229 fuel, 0.3991 life] on both plants.

Reproduction check: jad_starver -0.90349, ghassan_starver -0.13265, jad_random -0.04744,
ghassan_random +0.00436 -- identical to the orchestrator's logs.

### Starver (boost trim at -40 kPa), locked climb, 300 s

| | Jad plant | merged (= Ghassan) plant |
|---|---|---|
| launch 0-20 s: reward/step, sum | -1.181, -118.1 | -1.933, -193.3 |
| launch mean tracking error | 0.098 | 0.153 |
| flat 20-180 s: reward/step | +0.0024 | -0.0010 |
| climb 180-300 s: reward/step, sum | -2.067, -1238.1 | -0.00795, -4.76 |
| climb: requested / delivered torque | 340.2 / 273.2 Nm | 335.5 / 335.2 Nm |
| climb: mean error, share of steps beyond TRACK_TOL | 0.197, 100 % | 0.0047, 0.7 % |
| climb: MAP needed (baseline) / starver ceiling | 178.6 / 148.3 kPa | 175.3 / 176.5 kPa |
| climb: baseline's boost ceiling | 198.9 kPa (formula, at charge temp 330 K) | 216.7 kPa (derived envelope, at ambient 315 K) |
| climb: turbine, starver vs baseline | -50.7 K mean (790.5 vs 847.5 C peak) | -4.1 K mean (848.0 vs 848.9 C) |
| share of the episode penalty from the launch | 8.7 % | 97.2 % |
| mean reward | -0.90349 | -0.13265 |

Static boost ceilings (each tree's `plant.boost_ceiling_kpa`, 315 K): at 100 g/s 189.7 (Jad) vs
207.8 (merged); 110 g/s 194.9 vs 214.5; at 60 g/s 163.9 vs 147.3 (merged LOWER at low flow --
why its launch penalty is bigger).

### Starver elsewhere on the merged plant

| road | starver | neutral | where the penalty is |
|---|---|---|---|
| D2 (120 s, 12 %), 480 s, dt 0.2 | -0.08067 | (~0; not run) | launch -193.31; climb +0.00039/step (error 0.0016) |
| D2 (120 s, 16 %), 480 s, dt 0.2 | -0.07744 | +0.00001 | launch -193.31; climb +0.00469/step, ABOVE neutral's +0.00034 |
| rolling training road, seed 11, 600 s, dt 1.0 | -2.32655 | -0.00030 (Ghassan log) | launch 1.4 %; 80.1 % of post-launch steps beyond TRACK_TOL, mean error 0.239 |
| "hard starver" (spark -8 deg AND boost -40), locked climb | -0.68008 | | climb error 0.115 on every step, turbine +33.5 K (retard heats) |

On Jad's plant the D2 table (8e91276) read -1.54083 (120 s, 12 %) and -0.02549 (120 s, 16 %).
On the merged plant both pass the "starver < neutral - 0.02" rule with a wider margin (~0.06), but
on the launch only. The 16 % climb gain at identical MAP (e.g. +0.025/step at t = 168 s) is the
thermal deficit the launch shortfall left behind.

### Shift-rule band road (Ghassan's 9.3 % check), dt 1.0, 300 s

| plant, shift rule | grade | p95 error | neutral mean | check |
|---|---|---|---|---|
| merged, as shipped (deliverable-torque table) | 9.3 % | 0.0021 | -0.00079 | PASS |
| merged, as shipped | 9.6 % | 0.0022 | -0.00081 | PASS |
| merged, OLD flat 375 Nm rule (monkeypatched) | 9.3 % | 0.0064 | -0.0129 | PASS |
| merged, OLD rule | 9.6 % | 0.0091 | -0.0192 | PASS |
| merged, OLD rule | 9.84 % (steepest grade the old rule keeps 8th on) | 0.0257 | -0.0316 | PASS |
| Jad plant as it is (flat rule) | 9.3 % | 0.0926 | -0.644 | FAIL (8th kept, 99.6 % of climb steps beyond TOL) |

Static (merged plant): 8th at 130 km/h turns 2107 rpm, is asked 360.5 Nm at 9.3 %, table
sustains 348.1 Nm; kickdowns 8->7 at 8.82-8.83 %, 7->6 at 13.96-13.97 %. Jad plant: 8->7 at
9.62-9.63 %, 7->6 at 13.72-13.73 %.

### Random policy (slew-limited uniform actions, seeded)

Applied action settles near the middle of each range on both plants: mean [-1.96 deg spark,
-0.046 lambda (lambda 0.954), -13.1 kPa boost, fan 0.48, pump 0.67].

| climb 180-300 s | Jad plant | merged plant | merged, exhaust = fuel x 15 |
|---|---|---|---|
| turbine vs baseline (mean) | +6.28 K | -3.70 K | +7.39 K |
| r_life (unweighted) | -0.108 | +0.0586 | -0.0755 |
| fuel vs baseline | +8.1 % | +8.4 % | +8.4 % |
| tracking term/step | -0.0102 | -0.0004 | -0.0004 |
| climb reward/step | -0.0572 | +0.0190 | -0.0345 |
| episode mean | -0.04744 | +0.00436 | -0.01707 |

## Physics: why the starver margin collapsed (-0.90349 -> -0.13265)

The starver is not a torque limit; it is a 40 kPa cut to the boost ceiling (`_track_torque`:
`ceil = min(MAP_CEIL_KPA, boost_ceiling_kpa(...) + boost_trim)`). It refuses torque only where the
road needs more than ceiling - 40 kPa. On Jad's plant the climb needs 178.6 kPa against a
198.9 kPa ceiling (20 kPa headroom): the cut leaves 148 kPa, a 20 % shortfall on every climb step,
the hinge fires, -2.07/step. On the merged plant the ceiling is the measured envelope with drive B's
low-rpm roll-ons, evaluated at the compressor inlet (ambient) -- 216.7 kPa -- and the climb needs
175.3 kPa (lower drag with rho 1.12): 41.4 kPa of headroom, more than the action bound of 40. The
starver delivers 335.2 of 335.5 Nm on the climb and is punished only in the launch, where the derived
envelope is LOWER than the old formula (147 vs 164 kPa at 60 g/s).

This is mistake 17's sentence verbatim: "an engine that meets its demand easily makes refusing to
work a smaller crime -- the number to watch first if a trained agent turns lazy." The reward did not
get softer (TRACK_TOL 0.05, TRACK_HINGE 25, TRACK_W_MIN 0.45 unchanged on both sides; where torque
IS refused the hinge bites harder on the merged plant, -1.93/step in the launch). What changed is the
probe's reach. It also means mistake 5's hack -- refusing torque to save the turbine -- is less
reachable on the locked climb: the one damage-reducing lever (boost cut) cannot bite, and the other
torque-cutting lever (spark retard) heats the turbine (+33.5 K, r -1.29/step). The residual,
untested by both branches, is the 5 % driveability allowance where the tracking cost is linear.

What the merged file must contain: BOTH starver checks. On the merged plant the fixed-road check
and every D2 road measured pass on the launch; the rolling training-road starver (1.4 % launch
share, 80 % of steps beyond TRACK_TOL) is the only check with a sustained shortfall. Dropping
Ghassan's side would leave the reward gate with a launch-only hack test. Print the launch share
beside the fixed-road figure (done in the proposed file).

## Physics: why random scores above neutral on the merged plant (+0.00436)

The random walk holds about lambda 0.95 and 2 deg of retard, burning ~8 % more fuel than the baseline
on the climb on both plants. On the merged plant that cools the turbine 3.7 K; on Jad's it heats it
6.3 K. One variable settles it: on the merged plant with only the exhaust mass flow reverted to
fuel x 15, random falls to -0.01707 and runs 7.39 K HOTTER. With fuel x 15 the modelled exhaust flow
rises one-for-one with fuel, so enrichment (more fuel, same air) inflates the gas-side heat input
ua_gas_turb * mdot_exh * (EGT - T_turb) and hides its cooling; with air + fuel (mass conservation)
the flow rises only ~3 %, the EGT drop wins. Ghassan's definition is the physically correct one.

Then the preference draw: this episode weights fuel at 0.0229, so +8.4 % fuel costs 0.0019/step
while the damage gain pays 0.0234/step. Random is NOT a tracking hack (mean tracking error 0.0008,
no shortfall) -- mistake 5's hack was a torque refusal scoring above neutral. The file's note
("not automatically a bug ... protection is cheap to earn by accident") is right for the merged
plant; it should say it holds on one preference draw with a very light fuel weight, and "before
Phase D scores anything" is out of date. The rest of the gap to Jad's -0.04744 is tracking on Jad's
plant (resp -0.02406 vs -0.00121 mean, mostly launch shortfall: -28.9 of -36.1) and unisolated
differences.

## Semantic problems after the merge (beyond the hunk)

1. HIGH -- fixed-road and D2 starver checks are launch-borne on the merged plant (above).
2. MEDIUM -- "baseline delivers torque on a 9.3 % grade ... (was 0.09 before)" can no longer fail
   on the merged plant: the old rule passes there and up to 9.84 %. "The gearbox fix is guarded here
   by a road sitting in that band" (MERGE:53-54) is stale. The drift check (0.01 %) is the real guard.
   On Jad's plant the same road fails (p95 0.0926) -- the defect is live on Jad's branch but never
   met by Phase D/D2/C4 roads (12-16 % run in 7th/6th).
3. MEDIUM -- D2 notch moved to 13.96-13.97 %; `D2_ROADS`' fifth road (13.73 %) is a 7th-gear road
   on the merged plant; "+6.9 K" is the old plant's. Docstring line 25 "16 % asks the most torque" is
   wrong on both plants (16 % asks 345.5 / 341.6 Nm in 6th; just under the notch asks ~375 Nm in 7th):
   it asks the most road power.
4. MEDIUM -- docstring: "The default invocation (no --road) is unchanged" (MERGE:32) false; "the same
   four checks" (10-11) -- default now eight; "about two minutes" (8) stale on both sides
   (orchestrator: 367 s Jad, 370 s Ghassan, machine shared).
5. MEDIUM -- dependency: the merged gate only runs if thermal.py's hunk takes Ghassan's CODE
   (MERGE thermal.py:294 `p.ua_oil_ram` in the auto-merged `step()`; the field exists only in
   Ghassan's side of the hunk, :209). Jad's side there -> AttributeError on the first env step.
   engine_env.py's conflict is docstring-only; its code is Ghassan's.
6. LOW -- BAND_GRADE comment (65-67) "366 Nm ... sustains 333" is the 27-Sep plant: merged 360.5 /
   348.1 Nm.
7. LOW -- STOP advice (343-353) only addresses the starver ("raise w[0]"); failures of the four new
   checks need different fixes (derive_params.py; a plant/scenario defect per mistake 17). Also
   "every number in Phase D" / "before Phase C" are out of date.
8. LOW -- dt: the four original checks run at dt 0.2 while Ghassan's train.py trains at 1.0 and
   evaluate.py scores at 1.0 (AUDIT2 H2-14 asked for a dt check). The D2 gate is dt 0.2 (right for the
   closed D2). Ghassan's docstring "train.py now trains ... at dt = 1.0" holds only if the train.py
   resolution keeps his defaults.
9. LOW -- cross-file claims about this script's output that the merge moves: MERGE engine_env.py:1392
   "neutral still scores -0.00038" (merged: -0.00028); README.md:489 "passes all four checks";
   handoff.md:328, :338 "4 of 4"; CLAUDE.md:687, :696 "4 of 4" (vs :711 "8 of 8"); Jad's README.md:426
   "starver -0.90349"; presentation/index.html (Jad) "4 of 4". Dated records (Jad CHECKPOINT.md:995,
   :1026; results/PREREGISTRATION_D2.md:356 and its limit 10 "thin starver margin at 16 %"; Ghassan
   CHECKPOINT.md:846; SESSION_REPORT_2026-09-19.md:421) are history and stay, but limit 10 does not
   describe the merged plant (margin ~0.057, launch-borne).
10. INFO -- nobody imports test_reward (grep of both trees); full_run.py runs it as a script, timeout
    3600 s, unaffected.

## Recommended resolution

Take both blocks (Jad's D2 section, then Ghassan's `road_roll`, two blank lines between), and fix the
silently merged text. Full proposed file: `scratchpad/work/conflict-test_reward/test_reward.PROPOSED.py`
(parses; only non-ASCII character is the original em dash). Changes against the "both" resolution:

- usage lines: timing as measured (367-370 s, machine shared, not re-timed idle); "the four ORIGINAL
  checks" for `--road random`.
- D2 docstring: "16 % asks the most road power (not the most engine torque ...)"; "13.73 % is the notch
  on the plant D2 was gated and trained on"; replace "The default invocation (no --road) is unchanged"
  with: default runs Phase D's four checks AND the four training-road checks; `--road random` runs the
  four original checks per D2 road.
- Ghassan's paragraph: keep; add the two findings (band road no longer separates the rules; which
  starver check exercises the hinge).
- BAND_GRADE comment: date the 366/333 figures to the 27-Sep plant; give 360.5/348.1 for the merged one.
- `D2_ROADS` comment: "THE NOTCH MOVED WITH THE MERGE" -- 13.96-13.97 %; keep the tuple as gated
  (D2 is closed); re-run check_random_road.py's notch sweep before gating any NEW training.
- `roll(..., log=None)`: optional per-step (t, reward, tracking error); rollout unchanged.
- `main()`: log the starver; print "(NN % of it from the 0-20 s launch)" in the starver detail; drop
  "(was 0.09 before)"; add a FOR-INFORMATION line with the starver's mean error after 180 s and, when
  it is under TRACK_TOL, say the check passed on the launch and that the training-road starver check
  must not be dropped.
- random note: explain the slew-limited middle-of-range action and the light fuel weight; "before an
  experiment scores anything".
- STOP block: per-check advice (drift -> derive_params.py; band/training roads -> plant or scenario
  defect, check_roads.py; starver -> the existing weight advice).
- Optional, team decision: add ("locked", 11, "neutral"/"starver", 720.0) at dt 1.0 to the pooled roads
  so the locked climb is also gated at the step evaluate.py and the new train.py use.

Code sketch of the one functional change:

```python
def roll(action_fn, duration, seed=1, cycle=None, log=None):
    ...
        t = env.k * env.dt
        obs, r, term, trunc, info = env.step(action_fn(env, obs))
        rs.append(r)
        if log is not None:
            log.append((t, float(r), abs(info["torque_req"] - info["torque"])
                        / max(info["torque_req"], 40.0)))
```

## Scripts and outputs

`scratchpad/work/conflict-test_reward/`: probe_reward.py, band_probe.py, road_probe.py,
static_demand.py, static_notch.py, static_band.py, codecmp.py, resolve.py, summ.py; results in `out/`
(`*_starver.json`, `*_random.json`, `ghassan_random_exh15.json`, `merged_d2_120_1{2,6}_*.json`,
`merged_hardstarver.json`, `band_*.log`, `merged_rolling_starver.log`, `merged_proposed_default.log`).

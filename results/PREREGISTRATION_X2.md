# PREREGISTRATION — X2, the preview ablation in wider air, 5 seeds a side, 1200 episodes each

**Written 11 October 2026 on `GRA-2340394`, BEFORE any X2 agent trained.** Like
the preregistrations of Phase D, D2, C4 and X1 before it, this file exists so
that every rule the result will be read by is fixed before there is a result.

> **Status at writing: complete except sections 11 (run log) and 12 (outcome),
> which are filled in as the experiment runs and after it, and marked so.**

---

## 0. Who decided what, and what is still open

- **Ordered by Ghassan, 11 October 2026**, as two items of his list: *"Change to
  6 agents: 3 blinded, 3 sighted, 1200ep"* and *"Widen the training range from
  0°C to 45°C and kPa from sea level to ..."*. Asked the same day, he chose:
  the pressure floor **80 kPa** (about 1 950 m), with 76 kPa kept out of training;
  **5 seeds a side instead of 3**, after being shown that three pairs can never
  pass the sign test (section 5b); **1200 episodes per agent**, not in total; and
  **nothing else changes** from X1.
- **Jad's column of the decision sheet is still empty**, as it was for X1.
  Section 9 lists what X2 adopts provisionally.
- **The plant is X1's, on purpose** (section 3): the open question of whether the
  thermal fit should be sub-stepped (mistake 25, Q10) waits for the next plant
  change, so that X1 and X2 share one plant and one certificate.
- **Drive C (knock) has not been driven.** The knock model is untested (limit 3).

## 1. The questions

| | question | how it is answered |
|---|---|---|
| **P** (primary) | Does an agent that can see the road ahead protect the turbine better than an identically trained agent that cannot? | the ablation on the locked climb, section 5a — **with five pairs, only a unanimous result can leave INCONCLUSIVE** |
| C | Had the agents stopped changing by 1200 episodes? | the convergence rule, section 5c |
| D | How far apart are the seeds after 1200 episodes? | the sd of the paired differences, and the seed count it implies, section 5b |
| S | Do the trained agents beat `current-grade`? | section 5d — **a different claim, never evidence for P** (`AUDIT.md` C3) |
| T | Do they still protect in conditions they never trained in? | the transfer battery, section 5e |
| L | On the car's own drives, do they do no harm? | the logged-drive check, section 5f |

## 2. Why this experiment, and what it is NOT

X1 (`results/PREREGISTRATION_X1.md`, result 9 October) read SMALLER THAN THE MEI
at 50 000 steps, on a spread three times the one it had planned for (sd 24.78
points against 7.84), with six sighted agents and no blinded one protecting
little on the scored climb, every agent spending fuel on the car's own drives
where nothing needed protecting (1 of 46 passed the logged check), and no agent
passing the probe outright. Two of the explanations left open are what X2
changes: **training too short** (50 000 steps, about 55 episodes), and **air
too narrow** (25–45 °C at sea level only; the agents had never met cool air,
where nothing needs protecting, or thin air).

**X2 changes four things at once against X1, and so it is NOT a one-variable
comparison with X1:** the seed count (23 → 5 a side), the training length (55 →
1200 episodes), the ambient range (25–45 → 0–45 °C) and pressure (101.3 →
80–101.3 kPa). Anything said about X2 against X1 is descriptive and attributes
nothing to any single change. Jad's rule of 23 September ("one at a time") is
broken here by the order in section 0, and this sentence records it.

**What five pairs can and cannot do.** The smallest p the one-sided sign test
returns on five pairs is 1/32 = 0.031, so PREVIEW HELPS, SMALLER THAN THE MEI and
PREVIEW COSTS DAMAGE each need all five pairs on one side, and INCONCLUSIVE is
the likely reading unless 1200 episodes pull the seeds together. X2 is therefore
also a measurement: of convergence (C), and of the spread after 1200 episodes
(D), which sizes the next test.

## 3. The plant, pinned — X1's

| fingerprint (live, `fingerprint.plant_fingerprint()`, 11 October) | |
|---|---|
| `plant_sha` | `3c48890dd15bc116` (X1's) |
| `derived_sha` | `326c0835548975e2` (X1's) |
| `episodes_sha` (the twenty frozen episodes) | `05a598a574268b20` |
| schema | 2 |

No hashed plant file changes for X2. Everything new lives in `wide_air.py` and in
`train.py`, `train_all.py`, `check_roads.py` and `test_reward.py`, none of which
is a plant file. The locked climb, the reward, the spark cap at 0, the ramps, the
sub-stepping and the twenty frozen episodes are X1's.

### 3a. The training design: `wide_air.WideAirTrainingEnv`

X1's extremes roads (decision 12), with per episode, from the same road stream:

| | X1 | X2 |
|---|---|---|
| ambient | 25–45 °C | **0–45 °C** |
| pressure | 101.3 kPa | **80–101.3 kPa**, drawn independently of the ambient |
| the compressor inlet | 99.3 kPa | **p × 99.3 / 101.3**: the flow ceiling and the hard pressure cap fall with altitude (the conditions test's model), for both cars |
| the gearbox's kickdown table | sea level | **follows the pressure** (below) |
| the least torque a road asks for | 15 Nm | **X1's rule at the episode's air** (below) |
| families, speeds, hills, housing capacity | as decision 12 | unchanged |

Two of those rows were not in the order; the gates found them before any agent
trained, and each is X1's own rule carried into the new air rather than a new
choice:

- **The torque floor follows the ambient** (found by `check_roads.py`). The model
  has no fuel cut; with the throttle shut the engine makes 12.0 Nm at 42 °C, and
  X1 asked no road for less than 15 Nm, 1.25 times that. In colder air it makes
  more: 15.5 Nm at 25 °C, 20.6 at 0 °C. With 15 Nm kept, five of forty roads, all
  at 0–7 °C, failed: on descents the baseline was asked 15 Nm and made 17–19. The
  floor is now 1.25 times the closed-throttle torque at the episode's ambient,
  and never under 15 Nm (`wide_air.torque_floor_nm`).
- **The gearbox knows the air** (found by `test_reward.py`'s new corners). The box
  kicks down when a gear is asked for more than the engine can deliver, read from
  a table measured at sea level. At 80 kPa the engine delivers 252.8 Nm at
  2000 rpm against 316.3 at sea level, and with the sea-level table the box held a
  gear it could no longer pull: on the 12 % climb at 45 °C and 80 kPa the baseline
  fell short on 80 of 899 steps (neutral −0.139 a step). The table is now scaled
  per engine speed by what the engine delivers at the episode's pressure, measured
  with `measure_deliverable_torque`'s own loop at 80, 85, 90 and 95 kPa
  (`wide_air.ThinAirVehicle`). Afterwards: neutral −0.0022, p95 error 0.003.

At 101.3 kPa and a 15 Nm floor the design reduces to the plant exactly;
`test_wide_air.py` checks it to the bit, and that every other environment in a
process that imports `wide_air` is untouched (16 tests; with each of three
guards removed in turn — the inlet set while stepping, the builders' drag, the
sea-level inlet — its test failed).

### 3b. The gates, as they stood when this file was written

| gate | result |
|---|---|
| `test_wide_air.py` | **16 tests OK**: sea level equals the plant step for step; other environments see the plant's ceiling; thin air lowers both ceilings and the steps use it; the floor and the gearbox as above |
| `check_roads.py --road wideair` | **PASS**, 40 roads (seeds 100–139): worst neutral −0.0054, worst p95 tracking 0.013 against the 0.05 band. **The baseline passes 850 °C on 2 of 40** (X1's roads: 10 of 40) — limit 7 (`results/training_roads_wideair.json`) |
| `test_reward.py` | **12 of 12 pass**: X1's ten, unchanged (neutral −0.00027 on the climb; worst extremes road −0.00355), and two new on the wideair roads: neutral on every family in cold thin air (0 °C, 80 kPa) and hot thin air (45 °C, 80 kPa), ten roads, worst −0.00283, worst p95 error 0.009; the starver punished in hot thin air (−1.437 against −0.00283) |
| the blind arm | preview inputs (observation 14–17) non-zero on 0 of 899 steps of a wideair road for the blinded arm, on 899 of 899 for the sighted arm on the same road |
| the yardstick, decision 13 | the plant and the climb are X1's: `current-grade` short of 95 % of the requested torque on 1 of 719 demand steps (X1's 3b) |
| `analyse_x2.py` | dry run on X1's seeds 0–4: INCONCLUSIVE, sd 26.82 points, power 0.066 against the MEI at that spread |
| `check_x2_convergence.py --selftest` | PASSES: the practice set regenerates, and no episode seed is shared with a frozen test set |

## 4. The design

| | |
|---|---|
| arms | **sighted**, and **blinded** (`--no-preview`: the four preview inputs are zero) |
| seeds | **0 … 4 per arm — 10 runs**, paired by seed |
| budget | **1 080 000 steps per run**, dt 1.0 s, 900 s episodes: **1200 training episodes** (X1: 50 000 steps, about 55) |
| learner | SAC exactly as X1 (learning rate 3e-4, batch 256, the rest stable-baselines3's defaults), one process per run, CPU, one thread. The replay buffer follows `train.py`'s rule, sized to the run and capped at stable-baselines3's default: **1 000 000 transitions**, 93 % of the run (X1's held all of its 50 000) |
| training roads | **`wide_air.WideAirTrainingEnv`** (`train.py --road wideair`), section 3a |
| held out of training | **50 °C**, **76 kPa** and hills of **18–22 %** (section 5e) |
| command | `python train_all.py --road wideair --seeds 0-4 --steps 1080000 --jobs 10 --keep-buffer --out runs/wideair_dt1` (gitignored) |
| time | **about 50 hours**: ten runs side by side measured 6.0 steps a second each on this laptop (11 October, X1's roads); a reset adds 0.7 s (the floor's measurement), the first thin-air episode about 110 s (the gearbox's) |
| crash rule | **a run that stops is resumed from its last checkpoint WITH its replay buffer** (`--keep-buffer`): re-running the same command resumes every unfinished run. A machine restart counts as a crash. A resumed run is close to an unbroken one, not equal to it (the road and weight streams restart, the policy's sampling noise is not saved); every resume is in the run's `config.json` and in section 11. Restarting from step 0 (X1's rule) would cost up to 50 hours |
| recorded | every training step, `step_record.py`'s fields, in each run's `train_record.npz`; checkpoints every 10 000 steps; gitignored, backed up outside the repository after the run (decision 11) |

## 5. The tests — fixed now

### 5a. P, the primary test: `analyse_x2.py`

X1's rule, imported (`analyse_x1.report`, whose tests come from
`analyse_phase_d`), on X2's five pairs:

- **Scored on `evaluate.EPISODES`**, the twenty frozen episodes of the locked
  climb (12 %, 130 km/h, 42 °C, 101.3 kPa, 720 s, ramped over 8 s at 180 s).
- **Per agent:** cut = 100 × (1 − median damage / the baseline ECU's median
  damage). **Per seed:** d = cut(sighted) − cut(blinded), in points.
- **Minimum effect of interest: 5.43 points** (decision 5, as X1).
- **The cells, X1's order:** PREVIEW COSTS DAMAGE if the one-sided sign test of
  d < 0 has p < 0.05; otherwise PREVIEW HELPS if that of d > 0 does; otherwise
  SMALLER THAN THE MEI if that of MEI − d > 0 does; otherwise INCONCLUSIVE. The
  exact permutation test beside every sign test; the sign test primary.
- **Both ways until drive C:** total damage (primary) and thermal-only.

### 5b. D, power and the spread — declared now

| | |
|---|---|
| the smallest one-sided sign p on 5 pairs | **0.031**: every cell but INCONCLUSIVE needs **5 of 5** |
| power against the MEI at X1's spread (sd 24.78) | **0.07** |
| at the spread of 29 September (sd 7.84) | 0.25 |
| the spread at which 5 pairs reach 80 % | an sd of about **3 points** |

**No prediction about the spread is made.** Longer training could pull the seeds
together or not; D2 predicted a spread and was wrong, and X1's tripled. X2
reports the sd of the paired differences and, from it, the seed count with 80 %
power against the MEI (`analyse_x2.py` prints it): that number, not X2's cell, is
what sizes the next preregistered test.

### 5c. C, convergence: `check_x2_convergence.py`

C4's rule (`PREREGISTRATION_C4.md` 5b, set by the team on 23 September), at X2's
budget and in X2's units:

- **Measured:** every agent at **720 000** and **900 000** steps and its final
  model at **1 080 000** (2/3, 5/6 and all of training), on the same ten
  **practice episodes**: the locked climb under ten preference-weight draws made
  once from `numpy.default_rng(20261011)` the way `reset()` draws them, episode
  seeds 4000–4009, which no frozen test set uses (`--selftest` checks both).
  Deterministic policy, weights pinned.
- **Settled:** the agent's practice cut moves by no more than **2.715 points**
  (half the MEI) across the three points. **Pair settled:** the seed's d moves by
  no more than 2.715 points across them.
- **Converged:** at least **4 of 5** agents in **each** arm settled, **and** at
  least **4 of 5** pairs settled — one dissenter each, as C4's 7 of 8.
- The verdict labels the result (section 6). It does not choose a checkpoint,
  extend a run or drop one.

### 5d. S, supervision, and the worst episode

Printed by `analyse_x2.py` (X1's code), never as evidence for P: each agent's
cut against `current-grade`'s (47.0 % on this plant), the count per arm that
beats it, and the agents whose worst frozen episode does more damage than the
baseline ECU on the same episode.

### 5e. T, transfer: `conditions_test.py --set runs/wideair_dt1`

X1's battery unchanged, so X1 and X2 read side by side: 25, 35, 42 and 50 °C at
101.3 kPa, and 90, 82 and 76 kPa at 42 °C, each on its hill, frozen episodes 1,
5, 9, 13 and 17, against each condition's own baseline ECU and `current-grade`.
The hills are fixed before training: `results/conditions_wideair_dt1/
conditions_grades.json` is X1's file, copied byte for byte, because the hills
depend only on the plant (the baseline ECU climbs them) and that file carries
this plant's fingerprint (`plant_sha` 3c48890dd15bc116, `derived_sha`
326c0835548975e2), fixed before X1 trained. A recomputation on this tree
(`--hills-only`) reproduced its first four hills exactly (8.25, 21.75, 12.00 and
7.50 %) before it was stopped at a 30-minute limit; it is re-run during training
and compared in section 11.

| condition | in X2's training? |
|---|---|
| 25 °C on its 21.75 % hill | **held out: steeper than 18 %** |
| 35, 42 °C | in range (controls) |
| 50 °C | **held out: hotter than 45 °C** |
| 90, 82 kPa | in range (controls) |
| 76 kPa | **held out: thinner than 80 kPa** |

Five episodes a condition carry no test: descriptive. **The battery's altitude is
milder than X2's training in one more way** (limit 6): its gearbox kicks down on
the sea-level table, where in X1's run the baseline fell short on at most 4, 8
and 15 of 719 steps at 90, 82 and 76 kPa.

### 5f. L, the logged-drive check: `logged_check.py --set runs/wideair_dt1`

X1's check unchanged (`PREREGISTRATION_X1.md` 5e): the six drives fixed before
X1 trained, replayed flat at their own speed and median ambient, at two
weightings; an agent passes when it delivers the torque (T) and burns at most 1 %
more fuel than the baseline ECU (F) on every drive at both. X1: 1 of 46 passed.

### 5g. Safeguard 2's probe: `sanity_probe.py runs/wideair_dt1`

X1's probe unchanged: the housing input raised 50 K on every 10th climb step of
each agent's own frozen episodes; a violation is a leaner lambda trim by more
than 0.005 or a higher boost trim by more than 1 kPa. Reported per agent.

## 6. What each outcome may be called — declared now

Every sentence carries the budget and, from 5c, whether the agents had settled.

| cell | the sentence |
|---|---|
| PREVIEW HELPS | "All five agents trained in wide air with the preview channel took less damage on the locked climb than their blind twins (sign p 0.031); the mean effect is … points against an MEI of 5.43, at 1200 episodes per agent." |
| SMALLER THAN THE MEI | "Preview's effect on the locked climb is below the MEI (5.43 points of cut) in all five pairs of agents trained in wide air for 1200 episodes." Never "preview does not help" |
| INCONCLUSIVE | "INCONCLUSIVE on five pairs: the paired differences have an sd of … points, at which a test needs … seeds for 80 % power against the MEI." |
| PREVIEW COSTS DAMAGE | "All five sighted agents took more damage than their blind twins" — a finding about this learner at this budget, never evidence that preview is worthless |

If the agents had NOT settled (5c), every sentence adds: "The agents were still
changing at 1200 episodes." The thermal-only reading is printed beside the total
one under the same rule; if the two differ, both are reported and the total stays
primary. The scored climb is one H/τ point (about 0.64); X2 draws no curve.

## 7. Everything reported; the stopping rule

- All 10 runs are reported, including any that fail to learn. No run is dropped,
  no seed is added after any X2 result is seen, no run is extended past
  1 080 000 steps. More seeds or more steps is another experiment.
- Median, interquartile range and worst episode for every agent; `current-grade`
  beside both arms.
- X2 is reported beside Phase D, D2, C4, the twenty of 29 September and X1, one
  line each, never pooled.

## 8. Known limits — declared now

1. **Four changes at once against X1** (section 2). X2 against X1 is descriptive.
2. **Five pairs** (5b): only a unanimous result reaches a cell, and at X1's
   spread that happens rarely; X2's reading is mainly C and D.
3. **The knock model is untested against this car** (drive C). The spark cap
   stays at 0; the knock term stays in the reward; hence the thermal-only reading.
4. **Cold air is extrapolation.** The car's logs cover 19–45 °C of ambient; below
   19 °C the derived thermal constants run outside the air they were fitted in.
5. **Altitude is milder than real**, as in the conditions test: no hotter
   compressor outlet at the higher pressure ratio, no fall in exhaust
   backpressure, and ambient and pressure drawn independently, so the corners
   include hot, thin air no road has.
6. **The transfer battery's altitude is not X2's training altitude**: its gearbox
   kicks down on the sea-level table (5e).
7. **Most of X2's training needs no protection.** The baseline passes 850 °C on 2
   of 40 sampled roads (X1's: 10 of 40): cool and thin air keep the turbine
   cooler. Each agent still meets roughly four times as many hot episodes as an X1
   agent did (about 5 % of 1200 against 25 % of 55), but they are a smaller share
   of what it learns from — which is also what X1's logged check said it lacked.
8. **The scored climb's constant 130 km/h is never drawn in training** (X1's limit 7).
9. **The logged check replays flat at sea level** and cannot show protection.
10. **The agents train across τ**: speed moves the exhaust flow, and the housing
    capacity is drawn. An H/τ statement built on X2 has to say so.
11. **A resumed run is close to an unbroken one, not equal** (section 4).
12. **The thermal fit is not sub-stepped** (mistake 25, Q10); kept as X1's so the
    two share a plant.
13. **This is the sixth preregistered look at the preview question** (Phase D,
    D2, C4, 29 September, X1, X2). Every p is unadjusted; the thesis reports them
    together, one line each.
14. **The decision sheet is half answered** (section 9).

## 9. The decisions X2 rests on, adopted provisionally

As for X1 (`PREREGISTRATION_X1.md` section 9): Ghassan's column taken as filled
by his orders, Jad's empty. Decisions 5, 8, 9, 10, 11 and 13 at X1's adopted
options, each re-scored from the records without retraining if Jad answers
differently. **Decision 12 is widened by Ghassan's order of 11 October**
(section 0): train in 0–45 °C and 80–101.3 kPa, hold out 50 °C, 76 kPa and
18–22 %; a different answer to it is a new experiment.

## 10. How to run it

```bash
# before: the gates of section 3b, on this tree
python test_wide_air.py; python test_reward.py; python check_roads.py --road wideair
python check_x2_convergence.py --selftest
# the held-out hills, fixed before training: X1's file (same plant fingerprint), section 5e
cp results/conditions_extremes_dt1/conditions_grades.json results/conditions_wideair_dt1/

# 1. the 10 runs (about 50 hours); after a crash, the same command resumes them
python train_all.py --road wideair --seeds 0-4 --steps 1080000 --jobs 10 --keep-buffer --out runs/wideair_dt1

# 2. score them: the raw rows, then every step recorded and checked against them
python run_results.py phase_d --agents=runs/wideair_dt1
python record_agents.py runs/wideair_dt1

# 3. the preregistered test, then everything else section 5 names
python analyse_x2.py                                  # -> results/X2_RESULT.txt
python check_x2_convergence.py                        # -> results/x2_convergence.txt
python conditions_test.py --set runs/wideair_dt1 --resume-all
python logged_check.py --set runs/wideair_dt1
python sanity_probe.py runs/wideair_dt1
```

## 11. Run log — filled in as it runs

- **11 October 2026, before the launch.** Committed locally on `GRA-2340394`:
  `315e040` (X1's scored results, the 9 October audit, the results page;
  pushed to GitHub at Ghassan's request) and then this file with X2's code as
  `06f4686`; the working tree clean. The transfer hills recomputed with
  `--hills-only` matched X1's first four exactly and were stopped at a 30-minute
  limit; X1's file was copied instead (section 5e).
- **05:10.** The 10 runs launched in a hidden process, so no window can close
  them: `python train_all.py --road wideair --seeds 0-4 --steps 1080000 --jobs 10
  --keep-buffer --out runs/wideair_dt1`, launcher output in
  `runs/wideair_dt1/LAUNCH.txt`. Every run's `meta.json`: `git_head` 06f4686,
  `git_dirty` false, `plant_sha` 3c48890dd15bc116, `derived_sha`
  326c0835548975e2, `train_road` wideair, 1 080 000 steps, resume allowed; every
  `config.json`: `keep_buffer` true, a buffer of 1 000 000.
- **05:13.** `x2_score.py` started in a hidden process: it waits for the 10 runs,
  then scores them in the order of section 10 (`results/x2_score/SCORE_LOG.txt`).
  The hills recompute restarted beside the training on 4 workers, into a set of
  its own (`runs/wideair_dt1_hillcheck`), so the copy is never overwritten.
- <!-- RETIRED-OK: 241.2, -0.52 -- the two false positives this entry explains, not the retired figures -->
  **05:15.** Found while committing, not part of X2: `verify_docs.py` read 72 of
  73 on `315e040`, because two result tables first tracked there (X1's
  `X1_RESULT.txt` and `phase_d_extremes_dt1.txt`) hold a 241.2 (a damage median)
  and a −0.52 (a paired difference) that two bare-number retired patterns
  matched. Scoped out of that scan like the agent reports beside them; 73 of 73;
  `drift_test.py` running before that fix is committed. No rule of this file
  changed.
- **06:30 (about).** `drift_test.py` restarted once (this run log's own entry
  had quoted the two figures without a marker; marked, 73 of 73), then
  **16 of 16 drifts CAUGHT**, each on its own anchor. The scoped exemption, the
  document sweep for X2 and this log committed next, locally.

- **12 October.** The hills recompute beside the training finished: identical
  to the copy in every one of the seven conditions — grade, peak and the whole
  peak-against-grade curve (`results/conditions_wideair_dt1_hillcheck/`).
- **13 October, 08:41.** All 10 runs finished: 3067–3090 minutes each (about
  51 hours, 5.8 steps a second), 1201 complete episodes each (an episode is 899
  steps), none crashed, none resumed — the crash rule never applied.
  `x2_score.py` took over.
- **09:15–10:35.** Step 1 (`run_results.py phase_d`) exit 0 after 34 min; step 2
  (`record_agents.py`) exit 0 after 33 min; step 3 (`analyse_x2.py`) exit 0,
  `results/X2_RESULT.txt`; step 4 (`check_x2_convergence.py`) exit 0 after
  47 min, `results/x2_convergence.txt`; step 5 (`sanity_probe.py`) exit 0.
- **10:36.** Step 6 (`conditions_test.py --resume-all`) STOPPED by its own
  harness check: its five check episodes name agents by seed, and two of them
  (sighted seed 6, blinded seed 9) are seeds X2 does not have. Fixed: an agent
  the set lacks is replaced by the same arm at seed s mod the set's seed count
  (here sighted seed 1 and blinded seed 4); the 29 September and X1 checks are
  unchanged, every seed they name exists. No rule of this file changed.
- **11:36.** Step 7 (`logged_check.py`) exit 0 after 60 min.
- **13:27.** Step 6 re-run on the fixed harness; its reading is appended to
  section 12 when it ends. *(Corrected 13 October: this entry said 13:40,
  written from memory; the re-run's log file was created at 13:27.)*
- **14:31.** Step 6 exit 0 after 64 minutes. Its harness check passed before and
  after the battery: 5 of 5 frozen episodes on the locked climb equal their
  committed scores. `results/conditions_wideair_dt1/conditions_test.json`,
  `results/figures/conditions_test_wideair_dt1.png`; the reading is in 12b.

## 12. Outcome — added after the result, never above this line

Added 13 October 2026, from `results/X2_RESULT.txt` (`python analyse_x2.py`) and
`results/x2_convergence.txt`. Nothing above this line changed after the result,
except the run log of section 11, which is appended in time order.

### 12a. The preregistered reading (P)

| seed | sighted cut | blinded cut | d (points) |
|---|---|---|---|
| 0 | 71.67 | 72.01 | −0.34 |
| 1 | 39.26 | 70.56 | −31.31 |
| 2 | 35.36 | 47.64 | −12.28 |
| 3 | 71.27 | 46.01 | +25.25 |
| 4 | 48.44 | 51.78 | −3.34 |

1 of 5 positive, mean −4.40 points, sd 20.51. Preview helps: sign p 0.9688;
smaller than the MEI: 4 of 5 below 5.43, sign p 0.1875 (permutation 0.1875);
preview costs damage: 4 of 5 negative, sign p 0.1875. **CELL: INCONCLUSIVE**,
the same on thermal-only damage (mean −4.40, sd 20.56).

**The sentence that may be said (section 6):** *"INCONCLUSIVE on five pairs: the
paired differences have an sd of 20.51 points, at which a test needs 143 seeds
for 80 % power against the MEI. The agents were still changing at 1200
episodes."* Never "preview does not help".

### 12b. Everything else section 5 names

- **C, convergence: NOT-CONVERGED.** Settled: sighted 0 of 5, blinded 1 of 5
  (4 each needed); pairs 0 of 5 (4 needed). Between 720 000 and 1 080 000 steps
  the agents' practice cuts moved by 0.3 to 33.6 points against a band of 2.715,
  and the pairs' d by 12.2 to 39.2. At this budget, on these roads, the agents
  had not stopped changing.
- **D, the spread: an sd of 20.51 points** across the five pairs (X1: 24.78;
  the twenty of 29 September: 7.84). About 22 times X1's training, on wider
  air did not pull the seeds together. At this spread a sign test needs **143
  seeds** a side for 80 % power against the MEI; five pairs have 0.081.
- **S, supervision:** 7 of 10 agents beat `current-grade` (46.98 %) on the
  median: sighted median margin +1.45 points (−11.62 to +24.69), blinded +4.80
  (−0.97 to +25.03). **4 of 10** do more damage than the baseline ECU on at least
  one frozen episode: sighted seeds 2 and 4 on one each, blinded seed 1 on five,
  blinded seed 3 on four. Post hoc, not a test: sighted seeds 1 and 2 cut 39.3 %
  and 35.4 %, under `current-grade`, while no blinded agent is under 46.0 % —
  X1's pattern (six sighted agents under 40 %, no blinded one) again.
- **Safeguard 2's probe: no agent passes.** A 50 K hotter housing gets less
  protection on 22.3–72.9 % of probed climb states for the sighted agents
  (median 32.5 %) and 55.5–93.1 % for the blinded (median 64.9 %); X1's medians
  were 49 % and 62 %.
- **L, the logged-drive check: 0 of 10 pass** (X1: 1 of 46). With life weighted
  most (episode 4), 59 of 60 agent runs burn more than 1 % over the baseline ECU
  (median +6.92 %, worst +20.12 %; X1: 252 of 276, median +4.33 %, worst
  +21.40 %); with life weighted least (episode 15), 21 of 60 (median +0.39 %).
  And unlike X1's agents, five of X2's fall short of the torque on some drive
  (blinded seeds 0 and 4, sighted seeds 1, 3 and 4).
- **T, transfer (descriptive: five episodes a condition).** Held out: at 50 °C
  **8 of 10** agents beat that condition's `current-grade` (X1: 26 of 46), at
  76 kPa **6 of 10** (X1, which trained at 101.3 kPa only: 25 of 46), at 25 °C on
  the 21.75 % hill **5 of 10** (X1: 30 of 46). In range: 9 of 10 at 35 °C, 7 of 10
  at 42 °C, 10 of 10 at 82 kPa, 4 of 10 at 90 kPa. One agent does more damage than
  its condition's baseline ECU, sighted seed 2 at 25 °C (X1: 0–3 a condition).
  Only at 25 and 35 °C does `current-grade` deliver its torque (elsewhere it falls
  under 95 % of the request on 16–297 of 719 steps); the agents fall short on a
  median of 1–6 steps, except at 76 kPa: a median of 48, and sighted seed 4 on
  frozen episode 5 on 525, so the agents' cuts there are partly torque refused.
  Sighted minus blinded per condition (mean of the five pairs, 95 % interval):
  −12.4 [−47.1, +22.4] at 25 °C to +17.5 [−16.3, +51.2] at 50 °C; only 90 kPa's
  interval excludes zero (+15.2 [+5.0, +25.3]), one of seven, not a test.
  `results/conditions_wideair_dt1/conditions_test.json`.
- **What the agents did, measured after the result:** `results/X2_AGENTS.md`
  (`python x2_agents.py`). Description, never a test; nothing above changes.

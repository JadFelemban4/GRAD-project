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

## 12. Outcome — added after the result, never above this line

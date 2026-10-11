# PREREGISTRATION — X1, the preview ablation on the extremes design, 23 seeds a side

**Written 8 October 2026 on `GRA-2340394`, BEFORE any X1 agent trained.** Like
`PREREGISTRATION.md`, `_D2.md` and `_C4.md` before it, this file exists so that
every rule the result will be read by is fixed before there is a result. A
hypothesis declared after the numbers are in is a description.

> **Status at writing: complete except sections 11 (run log) and 12 (outcome),
> which are filled in as the experiment runs and after it, and marked so.**

---

## 0. Who decided what, and what is still open

- **Ordered by Ghassan, 8 October 2026:** "do it, add more seeds and retrain".
  "It" is decision 12 of `results/VALIDATION_DECISIONS.md` as he and Claude
  worded it on 7 October: *train on the extremes the car never reached, so the
  agent knows them; check the trained agent on the states we have logs for, so
  we know it trained correctly*.
- **The five steps Jad and Ghassan agreed on 30 September before any training**
  (`CLAUDE.md`, the merge box): steps 1–4 are done in code and measured
  (section 3); step 5 is this file.
- **Jad's column of the decision sheet is empty.** `CLAUDE.md`'s box of 7–8
  October says nothing is retrained until the thirteen decisions are answered.
  Ghassan's order overrides that for this experiment, and this is the place it
  says so. Section 9 lists the decisions X1 rests on, each adopted at its
  recommended option, and what an answer from Jad that differs would cost: a
  decision that only changes SCORING is re-applied from the per-step records
  without retraining; decision 12 itself is the training, so a different answer
  to it is a new experiment.
- **Drive C (knock) has not been driven.** The knock model is untested (limit 2).

## 1. The questions

| | question | how it is answered |
|---|---|---|
| **P** (primary) | Does an agent that can see the road ahead protect the turbine better than an identically trained agent that cannot? | the ablation on the locked climb, section 5a |
| S | Do the trained agents beat `current-grade`, the no-preview hand-written comparator? | section 5c — **a different claim, never evidence for P** (`AUDIT.md` C3) |
| T | Do they still protect in conditions they never trained in? | the transfer battery, section 5d |
| L | On the states the car has logs for, do they do no harm? | the logged-drive check, section 5e |

## 2. Why this experiment, and what it is NOT

The twenty agents of 29 September trained at one ambient (42 °C), one constant
speed (130 km/h), on hills to 14 %, with spark advance allowed, on a plant whose
thermal network was stiff at dt 1 and whose grade changes were single steps. The
merge review and the conditions test of 7 October found four things wrong with
that: the agents push spark to the +4° bound the untested knock model grants;
the step-grade knock spike is the size of the MEI; the network never learned
what ambient, pressure or a changing speed mean; and ten pairs have power 0.26.

**X1 changes all of that at once, and so it is NOT a one-variable comparison
with 29 September.** It is a new experiment, preregistered on its own: the
plant (sub-stepped, ramped), the action (spark capped at 0), the training
distribution (decision 12) and the seed count all differ. Anything said about
X1 against the twenty of 29 September is descriptive, and attributes nothing to
any single change. Jad's rule of 23 September ("one at a time, so that we can
tell") is broken here on purpose, by the order in section 0; this sentence is
where that is recorded.

## 3. The plant, pinned

| fingerprint (live, `fingerprint.plant_fingerprint()`) | |
|---|---|
| `plant_sha` (code of plant.py, thermal.py, engine_env.py, derived.py; docstrings and comments stripped) | `3c48890dd15bc116` |
| `derived_sha` (data/derived_params.json, FATAL since 8 October) | `326c0835548975e2` |
| `episodes_sha` (evaluate.EPISODES, the twenty frozen episodes) | `05a598a574268b20` |
| schema | 2 |

Every run writes this block into its `meta.json` before its first step, and
`evaluate.py` refuses a model whose fatal fields differ.

### 3a. The four agreed changes, each measured

| step of 30 Sep | what | where |
|---|---|---|
| 1 | the thermal network sub-stepped: explicit Euler at most 0.1 s per sub-step (`thermal.DT_SUB_MAX`) | `thermal.py` |
| 2 | the fingerprint covers `data/derived_params.json` (fatal `derived_sha`, schema 2) and `derived.py` | `fingerprint.py` |
| 3 | the spark trim capped at 0 (`engine_env.SPARK_TRIM_MAX`): the agent may retard, never advance. The command is still recorded beside what was applied | `engine_env.py` |
| 4 | every grade change ramped over 8 s (`engine_env.GRADE_RAMP_S`): the locked climb, the D2 climb (`random_road.climb`, its import guard still passes) and `test_reward.py`'s band road. The training roads already ramped over 4–12 s | `engine_env.py`, `random_road.py`, `test_reward.py` |

**What steps 1 and 4 did to the locked climb, one at a time**
(`check_premise.py`'s policies; the first row reproduces the merged plant's
published figures exactly):

| plant | baseline damage | peak | current-grade cuts | preview over current-grade |
|---|---|---|---|---|
| merged, 30 September | 920.1 | 883.0 °C | 43.4 % | −0.32 points |
| + sub-stepping only | 917.6 | 883.0 °C | 43.4 % | −0.32 |
| + ramp only | 850.4 | 883.0 °C | 47.0 % | −0.01 |
| **both: the plant X1 trains on** | **848.1** | **883.0 °C** | **47.0 %** | **−0.01** |

The ramp removes the one-step knock spike, and with it all of the hand-written
preview deficit, as the merge review predicted. The sub-stepping moves the
baseline 2.5 units and `validate.py` row 8 (oil) from 97.0 to 97.1 °C; the
validation table still reads 8 of 11.

### 3b. The gates, as they stood when this file was written

| gate | result |
|---|---|
| `test_reward.py` | **10 of 10 pass.** Neutral −0.00027 on the climb; on the 9.3 % band road p95 error 0.002; neutral on every terrain road (worst −0.00063); starver punished on a terrain road (−2.327 vs −0.00046). New: neutral on every extremes road, ten roads, two seeds of each family, worst −0.00355, worst p95 error 0.016; starver punished on an extremes road (−0.761 vs −0.00113) |
| `check_roads.py --road extremes` | **PASS**, 40 roads (seeds 100–139): worst neutral −0.0043, worst p95 tracking 0.018 against the 0.05 band; the baseline passes 850 °C on 10 of 40 (`results/training_roads_extremes.json`) |
| `validate.py` | 8 of 11: 6 of 7 literature, 2 of 4 our car |
| the blind arm (section 4) | preview inputs (observation 14–17) zero on 899 of 899 steps of an extremes road; non-zero on 783 of 899 for the sighted arm on the same road |
| the yardstick, decision 13 | on the locked climb `current-grade` falls under 95 % of the requested torque on **1 of 719** demand steps (the baseline ECU on 0). It does not need a shortfall column |
| `python -m app.test_replay --full` | **59 of 59**, after two pins moved with the sub-stepping and were attributed by switching it off (`7475b5d7` peak 873.1 → 872.7 °C, `pull01` 604.8 → 604.2 °C; no alert count moved) |
| `verify_docs.py` | **73 of 73**, after the documents were swept to this plant's premise (the merged plant's kept as marked records) |
| `drift_test.py` | the two rows this change re-anchored, 6 and 13: **CAUGHT**. The full sixteen run beside the training (section 11) |

## 4. The design

| | |
|---|---|
| arms | **sighted**, and **blinded** (`--no-preview`: the four preview inputs are zero) |
| seeds | **0 … 22 per arm — 46 runs**, paired by seed |
| budget | **50 000 steps per run**, dt 1.0 s, 900 s episodes: about 55 training episodes |
| learner | SAC as `train.py` sets it (learning rate 3e-4, replay buffer 50 000, the rest stable-baselines3's defaults), one process per run, CPU, one thread; every setting is written into each run's `config.json` |
| training roads | **`engine_env.ExtremesTrainingEnv`** (`train.py --road extremes`), a new road every episode from a stream seeded by `--seed`: the terrain families (locked 0.15, single 0.30, rolling 0.25, double 0.20, flat 0.10), and per episode an ambient drawn on **25–45 °C**, a speed target redrawn every **60–180 s** on **60–150 km/h** (reached at no more than 0.8 m/s² when speeding up; slowing down is a coast no faster than the road allows), hills to **18 %**, and the turbine housing's heat capacity scaled by a log-uniform draw on **×0.75–1.333** of the assumed 6000 J/K |
| what no road asks | less than **15 Nm** of the engine (`EXTREME_T_FLOOR_NM`): this model has no fuel cut, so a request below what it makes with the throttle shut (8–12 Nm) cannot be met by any policy. Slowdowns coast; a descent held at speed is no steeper than that allows. Measured on the first drafts: without it the neutral policy scored −112 to −693 an episode |
| held out of training | **50 °C** and hills of **18–22 %** (section 5d); pressure (the plant does not read it) |
| command | `python train_all.py --road extremes --seeds 0-22 --no-resume --jobs 23` → `runs/extremes_dt1/` (gitignored) |
| crash rule | **a crashed run is re-run from step 0, never resumed** (`--no-resume`): re-running the same command moves the dead directory aside to `<tag>.crashed<N>`, kept, and trains that seed again. A machine restart counts as a crash. A resume restores no replay buffer, so it is not the same agent |
| recorded | every training step, 47 fields (`step_record.py`: action and what was applied, observation, reward and its terms, road, gear, engine, heat, the parallel baseline car, the running totals, the episode's ambient and housing capacity), in each run's `train_record.npz`, gitignored and backed up outside the repository (decision 11) |

**Why 23.** At the spread the twenty agents of 29 September measured (sd of the
paired differences 7.84 points), the exact one-sided sign test reaches 80 %
power against the MEI at 23 pairs (0.822); at 20 pairs it has 0.640, at 24
0.786 (the test's discreteness). Section 5b.

## 5. The tests — fixed now

### 5a. P, the primary test: `analyse_x1.py`

- **Scored on `evaluate.EPISODES`**, the twenty frozen episodes of the locked
  climb (12 %, 130 km/h, 42 °C, 720 s, dt 1.0, now ramped over 8 s at 180 s).
  The twenty episodes do not change.
- **Per agent:** cut = 100 × (1 − median damage / the baseline ECU's median
  damage), over the twenty episodes (`record_agents.summarise`).
- **Per seed:** d = cut(sighted) − cut(blinded), in points.
- **Minimum effect of interest: 5.43 points.** The 50 damage units the team set
  on 22 September were 5.43 % of the baseline's damage on the merged plant;
  decision 5 restates the MEI as that share so it survives a plant change.
- **The three cells, D2's rule:** PREVIEW HELPS if the exact one-sided sign test
  of d > 0 has p < 0.05; otherwise SMALLER THAN THE MEI if the sign test of
  MEI − d > 0 has p < 0.05; otherwise INCONCLUSIVE. **And C4's rule:** if the
  one-sided sign test of d < 0 has p < 0.05, the reading is PREVIEW COSTS
  DAMAGE, whatever the cell.
- The exact paired permutation test is printed beside every sign test as the
  sensitivity reading. If they disagree both are reported; the sign test is
  primary; neither is chosen after the fact. Both tests are imported from
  `analyse_phase_d.py`.
- **Both ways, as agreed on 30 September until drive C:** the rule is applied to
  total damage (primary) and to thermal-only damage (no knock term), and both
  are reported.
- `analyse_x1.py` was written before training and dry-run on the twenty of
  29 September: it reproduces their published reading (6 of 10 positive, mean
  +1.17, sd 7.84, sign p 0.3770, INCONCLUSIVE; +24.45 and +22.00 points over
  `current-grade`).

### 5b. Power — declared now, from the spread of 29 September

| | |
|---|---|
| sd of the paired differences, 29 September (ten pairs) | 7.84 points |
| sign test at 23 pairs | needs **16 of 23** to agree |
| power against the MEI at 23 pairs, at that spread | **0.822** |
| the effect with 80 % power at 23 pairs | **5.26 points** |
| power at 23 pairs if the spread is 1.25×, 1.5×, 2× | 0.659, 0.527, 0.358 |

**This file makes no prediction about the spread.** Wider training conditions
could spread the seeds (decision 12 warned of it) or settle them; D2 predicted a
spread and was wrong. `power_analysis.delta_for_power` returned 64.63 at 23
pairs until 8 October, where a direct scan gives 5.26: its binomial tail
underflowed for success probabilities near 1. Fixed, and `power_analysis.py`'s
own output is byte-identical after the fix.

### 5c. S, supervision, and the worst episode

Printed by `analyse_x1.py`, never as evidence for P: each agent's median cut
against `current-grade`'s (47.0 % on this plant), the count per arm that beats
it, the median margin; and, from the decision sheet's input to decision 7, the
agents whose WORST frozen episode does more damage than the baseline ECU on the
same episode — the measure that caught blinded seed 6 of 29 September.

### 5d. T, transfer: `conditions_test.py --set runs/extremes_dt1`

The conditions test of 7 October on the X1 agents: seven conditions (25, 35, 42
and 50 °C at 101.3 kPa; 90, 82 and 76 kPa at 42 °C), each on the speed profile
that changes every one to two minutes, each on its own hill — the gentlest grade
at which the baseline ECU peaks at the locked climb's 883 °C. **The hills were
calibrated on this plant before training** (`--hills-only`,
`results/conditions_extremes_dt1/conditions_grades.json`, stamped with the
plant and derived hashes):

| condition | hill | baseline peak | in X1's training? |
|---|---|---|---|
| 42 °C, 101.3 kPa | 8.25 % | 882.7 °C | in range (control) |
| 25 °C | **21.75 %** | 882.8 °C | **held out: steeper than 18 %** |
| 35 °C | 12.00 % | 883.0 °C | in range (control) |
| 50 °C | 7.50 % | 882.6 °C | **held out: hotter than 45 °C** |
| 90 kPa | 8.75 % | 885.4 °C | pressure: untrained |
| 82 kPa, about Taif | 12.00 % | 886.6 °C | pressure: untrained |
| 76 kPa, the climb's top | 12.25 % | 888.1 °C | pressure: untrained |

Every hill is the one the plant of 29 September gave: the sub-stepping and the
ramp moved no grade on the coarse-then-fine search.

Frozen episodes 1, 5, 9, 13 and 17. For each condition and agent: damage against
that condition's baseline, the margin over that condition's `current-grade`,
torque shortfall steps, and what the actuators did on the climb. **Held out:
50 °C, and the 25 °C condition's hill wherever it is steeper than 18 %.** In
range, as controls: 35 and 42 °C. Pressure: untrained, reported as such. Five
episodes per condition carry no test: the transfer reading is descriptive — how
many agents of each arm beat their condition's `current-grade`, held out against
in range. The harness check (five episodes must equal their committed scores)
runs first.

### 5e. L, the logged-drive check: `logged_check.py --set runs/extremes_dt1`

<!-- RETIRED-OK: 269.8, 6 -- the logged check's subset of the manifest, not the manifest's own total -->
Fixed before training in `results/logged_cycles.json` (`python logged_check.py
--build`): **six drives, 269.8 minutes** — every manifest drive that logs
vehicle speed and ambient and runs five minutes or more, except the census log
`fb988991` (mistake 8): `3aca2ec1`, `670063b2`, `683640a0`, `7475b5d7`,
`cb67b01f`, `drive10`. Each replayed FLAT through the simulator at its own speed
(each reading where it first appears, linear on a 1 s grid, 3 s mean) and its
own median ambient (26.5–42.0 °C), at two weightings: frozen episode 4 (life
weighted most, 0.493) and 15 (least, 0.029). The speed traces are hashed; the
script refuses to run if a trace differs.

An agent passes when, on every drive at both weightings:

- **T**: on the steps that ask more than 40 Nm, it falls more than 5 % short on
  at most 1 % of the steps on which the baseline ECU in the same run does not;
- **F**: it burns at most 1 % more fuel than the baseline ECU over the drive.

Reported: the count of each arm that passes, the worst fuel and the worst
shortfall per agent, and what each agent does where nothing needed protecting
(median applied actuators while the baseline's housing is under 750 °C).
**What it can say:** no harm on states the simulator is validated on. **What it
cannot:** that the agent protects correctly — a flat replay never loads the
engine as the car's own climbs did, so no drive is expected to reach the
trigger.

### 5f. Safeguard 2's probe: `sanity_probe.py runs/extremes_dt1`

A hotter housing must never get less protection. On every 10th climb step of
each agent's own frozen episodes, the housing input is raised by 50 K and the
policy asked again; a VIOLATION is a leaner lambda trim by more than 0.005 or a
higher boost trim by more than 1 kPa. Reported per agent, not a gate. (Dry run
on two agents of 29 September: 28 % and 37 % of states violate — their policies
are not monotone in housing temperature; X1's will be read beside them.)

## 6. What each outcome may be called — declared now

| cell | the sentence |
|---|---|
| PREVIEW HELPS | "Agents trained on the extremes design with the preview channel took less damage on the locked climb than their blind twins, by the sign test across 23 seeds (p = …); the effect is … points against an MEI of 5.43." Its size against the MEI is what says whether preview is WORTH acquiring at this operating point |
| SMALLER THAN THE MEI | "Preview's effect on the locked climb is below the MEI (5.43 points of cut) for agents trained on the extremes design at 50 000 steps." Never "preview does not help" |
| INCONCLUSIVE | "INCONCLUSIVE: the experiment rules out neither an effect of the MEI nor none." With the effect that has 80 % power at X1's own spread printed beside it |
| PREVIEW COSTS DAMAGE | "The sighted agents took significantly more damage than their blind twins" — reported as a finding about this learner at this budget, never as evidence that preview is worthless and never turned into a two-sided win |

The thermal-only reading is printed beside the total one under the same rule;
if the two cells differ, both are reported and the total stays primary. In no
cell is the result written as "preview does not help". The scored climb is one
H/τ point (30 s over a τ of about 47 s on the climb, 0.64); X1 draws no curve,
and the agents trained across τ (section 8, limit 6).

## 7. Everything reported; the stopping rule

- All 46 runs are reported, including any that fail to learn. No run is dropped
  for a poor curve, no seed is added after any X1 result is seen, no run is
  extended past 50 000 steps. More seeds or more steps is another experiment
  with its own preregistration.
- Median, interquartile range and worst episode for every agent; `current-grade`
  beside both arms.
- X1 is reported beside Phase D, D2, C4 and the twenty of 29 September, one line
  each, never pooled with any of them.

## 8. Known limits — declared now

1. **Many changes at once** against 29 September (section 2). X1 against the
   earlier sets is descriptive.
2. **The knock model is untested against this car** (drive C). The cap removes
   the advance the agents of 29 September exploited; retard is still open to
   them, and the knock term is still in the reward. Hence the thermal-only
   reading.
3. **Safeguard 1 is only partly implemented.** The housing's heat capacity is
   drawn per episode; the knock threshold and the damage scale are not. Drawing
   them would change the reward per episode, not the plant; with advance capped
   the knock exploit of 29 September is closed by the cap instead, and the
   damage constants' alternatives (decisions 8–9) are scored from the records.
4. **Pressure is not in training** — the plant does not read it. The conditions
   test's thin-air rows test a dimension the agents never saw.
5. **The logged check replays flat** and cannot show protection (5e). Its drives
   include speeds the training never drew (up to 227 km/h).
6. **The agents train across τ.** Speed moves the exhaust flow and so τ, and the
   housing capacity is drawn too; the scored climb holds one τ. An H/τ statement
   built on X1 has to say so.
7. **The scored climb's constant 130 km/h is never drawn in training**: every
   training episode's speed target changes. The locked family keeps the climb's
   shape, not its speed profile.
8. **No road asks less than 15 Nm, and no road brakes** (section 4): a limit of
   the plant, which has no fuel cut and no engine braking.
9. **50 000 steps is the C1 budget**; convergence is not tested. A null from
   undertrained agents is not a null from trained ones (Phase D's limit 6).
10. **The decision sheet is half answered** (section 9).
11. **Severity is not realistic, by design**: the hottest real climb logged
    (drive10) is 86 K cooler than the scored one.
12. **This is the fifth preregistered look at the preview question** (Phase D,
    D2, C4, 29 September, X1), on different plants and designs. Every p here is
    unadjusted; the thesis reports them together, one line each.

## 9. The decisions X1 rests on, adopted provisionally

Ghassan's column is taken as filled by his order of 8 October at the
recommended option; Jad's is empty.

| # | adopted | if Jad answers differently |
|---|---|---|
| 5 | relative damage; the MEI as 5.43 points of cut | re-scored from the committed summaries; no retraining |
| 8 | the turbine scale stays 45 K; 20.3 K (creep rupture) a pre-declared sensitivity row | re-scored from the per-step records |
| 9 | the knee stays 850 °C; 804 and 907 °C sensitivity rows; the no-knock column | re-scored from the per-step records; a moved knee also moves the hand-written trigger, so the comparator is re-run too (cheap) |
| 10 | the oil scale stays 12 K | re-scored |
| 11 | records out of git, backed up outside the repository | — |
| 12 | **train on the extremes, check on logged states, hold out 50 °C and 18–22 %** | **a new experiment**: this one is the training |
| 13 | `current-grade`'s shortfall is a gate: measured above, 1 of 719 steps | — |
| 1–4, 6, 7 | the validation plan's labels and standards | independent of the training |

## 10. How to run it

```bash
# before: the gates of section 3b, on this tree
python test_reward.py; python check_roads.py --road extremes
python conditions_test.py --set runs/extremes_dt1 --hills-only    # the held-out hills (done)
python logged_check.py --build                                    # the logged drives (done)

# 1. the 46 runs (about 9 hours on the 20-thread team laptop)
python train_all.py --road extremes --seeds 0-22 --no-resume --jobs 23

# 2. score them: the raw rows, then every step recorded and checked against them
python run_results.py phase_d --agents=runs/extremes_dt1
python record_agents.py runs/extremes_dt1

# 3. the preregistered test, then everything else section 5 names
python analyse_x1.py                                  # -> results/X1_RESULT.txt
python conditions_test.py --set runs/extremes_dt1 --resume-all
python logged_check.py --set runs/extremes_dt1
python sanity_probe.py runs/extremes_dt1
```

## 11. Run log — filled in as it runs

- **8 October 2026, 15:15.** This file committed as `75ca65f` (local, on
  `GRA-2340394`; working tree clean), then the 46 runs launched in their own
  window: `python train_all.py --road extremes --seeds 0-22 --no-resume
  --jobs 23`, launcher output in `runs/extremes_dt1/LAUNCH.txt`. The first
  wave is seeds 0–10 of both arms and sighted seed 11; the rest start as runs
  finish. Every run's `meta.json`: `git_head` 75ca65f, `git_dirty` false,
  `plant_sha` 3c48890dd15bc116, `derived_sha` 326c0835548975e2,
  `resume_allowed` false.
- **15:17.** The full `drift_test.py` started beside the training (it runs
  `verify_docs.py` on sixteen copies of the tree; the working tree is never
  touched).
- **15:49.** `x1_score.py` started in its own window: it waits for the 46 runs,
  then scores them in the order of section 10 (`results/x1_score/SCORE_LOG.txt`).
- **16:19.** The drift test restarted. Its first rows were "caught" for a reason
  that had nothing to do with the drift: `verify_docs.py` failed on every copy,
  on two of this file's own figures (the logged check's drive count and
  minutes, which the dataset pattern read as the manifest's) and on a comment in
  `logged_check.py` (its housing threshold next to the word for the ECU car,
  which the premise pattern read as a damage figure). Marked and reworded;
  `verify_docs.py` 73 of 73 again. No rule of this file changed.
- **17:35.** `drift_test.py`: **16 of 16 drifts CAUGHT**, each on its own
  anchor (rows 6 and 13 on the figures re-anchored on 8 October). The training
  is at about 25 000 steps a run, no run has crashed, and every run writes its
  per-step record at each 10 000-step checkpoint.
- **19:09–19:22.** The first wave finished: 23 of 23 runs exited cleanly after
  233–246 minutes each (about 3.5 steps a second each, 23 sharing the 20-thread
  laptop); none crashed. The second wave, blinded seed 11 and seeds 12–22 of both
  arms, started as each finished.
- **23:01.** All 46 runs finished, none crashed: `train_all.py` reports "all done in
  465 min; every run finished" (`runs/extremes_dt1/LAUNCH.txt`). No run was re-run
  or resumed, so the crash rule never applied. `x1_score.py` takes over.
- **9 October, 01:04.** Step 1 (`run_results.py phase_d`) exit 0 after 120 min.
- **03:01.** Step 2 (`record_agents.py`) exit 0 after 117 min: all 1 000 recorded
  episodes equal step 1's unrecorded scores. Step 3 (`analyse_x1.py`) exit 0:
  `results/X1_RESULT.txt`. Step 4 (`sanity_probe.py`) exit 0.
- **03:03.** Step 5 (`conditions_test.py --resume-all`) STOPPED by its own harness
  check: 5 locked-climb episodes did not equal their committed scores. Cause, found
  and fixed the same night: the test's worker processes re-import the module and
  were never told the agent set (`--set`, added on 8 October), so each loaded the
  29 September agent of the same name from `runs/terrain_dt1`. The pool now passes
  the set to every worker; the harness check then passed, 5 of 5 identical. The
  hills fixed before training are unaffected (they ran the baseline ECU only). No
  rule changed; the step is re-run after step 6.
- **03:03.** Step 6 (`logged_check.py`) started.
- **07:22.** Step 6 exit 0 after 259 min. Step 5 re-run from the start
  (`--resume-all`; the harness check first, 5 of 5 identical).
- **10:54.** Step 5 scored all seven conditions (250 episodes each, every step
  recorded). The merge wrote `results/conditions_extremes_dt1/conditions_test.json`,
  then the report stopped on a lookup: it read the harness result from the hills
  file, where a set whose hills were fixed before training keeps it beside them
  (`harness_check.json`). The report now reads it there; `--report-only` printed
  the table and drew the figure. Nothing was re-run and no row changed.

## 12. Outcome — added after the result, never above this line

Added 9 October 2026, from `results/X1_RESULT.txt` (`python analyse_x1.py`).
Nothing above this line changed after the result, except the run log of
section 11, which is appended in time order.

### 12a. The preregistered reading (P)

```
TOTAL DAMAGE (primary)   positive 10 of 23   mean -10.35   sd 24.78 points
  preview helps:         sign p 0.7976   permutation p 0.9710
  smaller than the MEI:  sign p 0.0173 (17 of 23 below 5.43)   permutation p 0.0027
  preview costs damage:  sign p 0.3388 (13 of 23 negative)
  CELL: SMALLER THAN THE MEI
THERMAL-ONLY             the same cell: 17 of 23 below, sign p 0.0173, mean -10.43
```

**The sentence of section 6, verbatim:** *"Preview's effect on the locked climb
is below the MEI (5.43 points of cut) for agents trained on the extremes design
at 50 000 steps."* The sign and permutation tests agree. The other direction,
preview costing damage, is not significant by the sign test (13 of 23). Never
"preview does not help".

**What the reading rests on, stated beside it.** The spread is 24.78 points,
three times the 7.84 of 29 September (section 5b made no prediction). At it,
X1 had power 0.20 against the MEI and 80 % power only for an effect of 16.6
points; "smaller than the MEI" is still reached because the paired differences
sit mostly below it, many of them far below. And much of that comes from one
arm: **six sighted agents cut less than 40 % on the scored climb (seeds 4, 13,
16, 17, 21, 22: 0.6–36.3 %); no blinded agent does** (the lowest, seed 1,
44.4 %). That asymmetry is a POST-HOC observation, not a preregistered test.
What those six do there is measured (the page's table, from the per-step
records): five of them enrich at most about half as deeply on the climb as their
blinded twins (median lambda trim −0.019 to −0.067 against −0.094 to −0.147);
seed 4 enriches as deeply as its twin but retards spark 4.3° and adds 7.4 kPa of
boost; three retard spark by 2.2–4.3°. On their own last ten TRAINING roads the
same six cut 25.6–47.4 % against the parallel baseline car, inside the
11.2–59.3 % of the other forty (`record_extracts.py --x1`). So they learned to
protect, and did not carry it to the scored climb. Why is not measured. The scored climb's
constant 130 km/h is never drawn in X1's training (limit 7).

### 12b. Everything else section 5 names

- **S, supervision:** 39 of 46 agents beat `current-grade` (46.98 %) on the
  median: 17 of 23 sighted, 22 of 23 blinded; median margins +16.80 and +18.91
  points. **19 of 46 do more damage than the baseline ECU on at least one frozen
  episode** (13 sighted, 6 blinded).
- **The yardstick (decision 13):** `current-grade` short of 95 % of the request
  on 1 of 719 steps, as measured before training.
- **Safeguard 2's probe:** no agent passes it outright. The share of probed climb
  states where a 50 K hotter housing got less protection runs from 1.1 % to
  98.5 %; median 49.2 % for the sighted, 61.8 % for the blinded agents. Most
  agents' median response to the hotter housing is small in both levers, so this
  reads as policies that barely respond to the housing input in a consistent
  direction (`results/agents/extremes_dt1/sanity_probe.json`).
- **The sensitivity rows of decisions 8 and 9** (`damage_constants.py --set
  extremes_dt1`): under every one, 38 or 39 of 46 agents beat current-grade and
  the ablation's mean is −9.9 to −13.0 points. Its 95 % interval spans zero in
  seven of nine rows; the two with the creep-rupture scale (20.3 K) exclude zero,
  on the side of preview costing damage. Descriptive, like every row there.
- **L, the logged drives (`results/logged_check_extremes_dt1.json`): 1 of 46
  agents passes** (sighted seed 18): 1 of 23 sighted, 0 of 23 blinded.
  `current-grade` passes everything (on a flat replay it never acts). The agents
  deliver their torque (T fails on 14 of 552 runs); they fail on FUEL. With life
  weighted most (frozen episode 4), 252 of 276 runs burn more than 1 % over the
  baseline ECU (median +4.33 %, worst +21.40 %); with it weighted least (episode
  15), 156 of 276 (median +1.29 %). Of that extra fuel, 67.0 % is burned while
  the parallel ECU car's housing is under 500 °C and 95.4 % under 650 °C
  (`record_extracts.py --x1` -> `logged_fuel_bands.json`): protection where
  nothing needed it, on the drives where the simulator is validated. On 236 of
  552 runs the agent's housing also peaked more than 5 K above the ECU car's.
  By the preregistered criteria, **X1's agents do harm on the car's own
  driving**: the fuel cost of protecting at the wrong temperature.
- **T, transfer** (`python conditions_test.py --set runs/extremes_dt1
  --report-only`; `results/conditions_extremes_dt1/conditions_test.json`). As
  section 5d fixed it, descriptive: how many agents of each arm beat their
  condition's `current-grade`, held out against in range.

  | condition | hill | for X1 | sighted | blinded | of 46 | worse than its ECU |
  |---|---|---|---|---|---|---|
  | 42 °C, 101.3 kPa | 8.25 % | in range (control) | 15 of 23 | 14 of 23 | 29 | 2 |
  | 35 °C | 12.00 % | in range (control) | 20 of 23 | 22 of 23 | 42 | 0 |
  | **25 °C** | **21.75 %** | **held out** | 17 of 23 | 13 of 23 | **30** | 3 |
  | **50 °C** | **7.50 %** | **held out** | 14 of 23 | 12 of 23 | **26** | 1 |
  | 90 kPa | 8.75 % | pressure: untrained | 13 of 23 | 12 of 23 | 25 | 1 |
  | 82 kPa | 12.00 % | pressure: untrained | 15 of 23 | 17 of 23 | 32 | 3 |
  | 76 kPa | 12.25 % | pressure: untrained | 11 of 23 | 14 of 23 | 25 | 2 |

  Held out, 26 and 30 of 46 beat the comparator; in range, 29 and 42. Two things
  limit the comparison, both read off the same run. `current-grade` misses the
  requested torque by more than 5 % on more than 1 % of the 719 steps (the logged
  check's T criterion) in five conditions — 42 °C 115 steps, 50 °C 115, 90 kPa
  297, 82 kPa 16, 76 kPa 222 — so there its cut is partly torque refused, not
  protection; only 25 °C (held out) and 35 °C (in range) have a comparator that
  delivers, and there the counts are 30 and 42. And at 82 and 76 kPa the agents
  miss their torque at least as often as it does (median 20 and 228 steps). The
  agents doing more
  damage than their condition's baseline ECU are mostly the same few: blinded
  seed 2 and sighted seed 17 in four conditions each, sighted seed 21 in two.
  The sighted-minus-blinded mean's 95 % interval spans zero in all seven
  conditions. Beside it, not part of this test: the twenty agents of
  29 September on the same hills (`results/conditions_test.json`, 7 October, the
  plant before the agreed fixes, spark advance allowed): 6 of 20 at 25 °C,
  19 of 20 at 50 °C, 19 of 20 at 42 °C, 20 of 20 at 35 °C.

# Session report — 7–8 October 2026: every step recorded, the damage constants, the decisions, the page

Branch `GRA-2340394`, on top of `2864592` (the validation plan). Sections 1–7
were committed with X1's preregistration as `75ca65f` (local, not pushed), on
Ghassan's word; section 8 is X1. Written for Ghassan and Jad.

Ghassan asked for four things:

1. *"Every constant in the formula is a design choice, not a property of the
   car." Look for every constant, and if we can calculate it, do it.*
2. *Make sure the validation decisions are chosen. If decisions are to be made,
   write them for me and Jad.*
3. *Make sure that everything from the environment to the actions of the agents
   is recorded for monitoring and understanding.*
4. *Update the artifact.*

---

## 1. Recording (part 3)

### 1.1 One definition of a step

`step_record.py` defines what a recorded step holds, and every script that runs
episodes now uses it: `evaluate.py` (and through it `record_agents.py` and
`knock_margin.py`), `conditions_test.py` and `train.py`. **41 fields** a step:

| group | fields |
|---|---|
| the agent | `action` (what the network asked, [-1, 1]), `applied` (what the actuators did after slew and bounds, physical units), `obs` (the 23 inputs, before the step), `reward` and `r_fuel`, `r_life`, `r_resp`, the constraint costs |
| the road | `grade`, `v_kmh`, `gear` (from engine and road speed; exact between 800 and 6500 rpm, where `Vehicle.demand` clips) |
| the engine | `rpm`, `map_kpa`, `tps`, `iat_c`, `torque_req`, `torque`, `spark`, `lam`, `ki`, `egt_c`, `mdot_fuel`, `mdot_exh` |
| the heat | `t_turb`, `t_oil`, `t_block`, `thermostat` |
| the baseline car beside it | `t_turb_base`, `t_oil_base`, `t_block_base`, `thermostat_base`, `map_kpa_base`, `knock_retard_base`, `hot_dwell_base` |
| the ledger | `damage_rate`, and the running totals `damage_cum`, `damage_base_cum`, `fuel_cum`, `fuel_base_cum` |

Everything is read after `env.step()` returns, so a recorded episode is the
episode without a record. Each producer checks that before writing.

### 1.2 Where each record is, and how it was checked

| episodes | record | check |
|---|---|---|
| training (`train.py`, from the next run on) | 44 fields a step in `train_record.npz`: the 41, plus `step`, `episode` and the episode's preference `weights`. A `_StepState` wrapper adds the environment's state to each step's info dict before the vector env resets | seed 0, 600 steps, CPU, against the `train.py` of `2864592`: **largest weight difference 0.0**; the 18 fields both keep agree exactly, or to the float16 the old record stored them at |
| the twenty runs of 29 September | they kept 18 fields and **no road**. `training_roads.py` regenerated the road, the preference weights and the applied actuators under every step: the road and weights come from seeded streams the agent cannot move, the actuators from the recorded actions through the slew limit | 20 of 20 runs, 1 000 000 steps: every family equals `curve.csv`; the torque request agrees to 0.125 Nm (the old float16 rounding); the reward rebuilt from weights, terms and actuators agrees to 1.85e-06 (`results/train_roads_check.json`) |
| the twenty frozen episodes (`record_agents.py --records-only`) | `eval_record.npz`, 41 fields | each episode must equal its committed `eval_summary.json` before anything is written; nothing tracked is rewritten |
| the knock margin (`knock_margin.py --records-only`) | `results/records/knock_margin/terrain_dt1/<agent>.npz` | each episode must equal `knock_margin.json` first |
| the conditions test (`conditions_test.py`) | `results/records/conditions/<k>_<condition>/<policy>.npz`, with a `.json` naming the condition, the hill and the speed profile | the merge compares every re-run row with the committed `results/conditions_test.json` |

The re-runs (conditions test, then the frozen episodes, then the knock margin)
ran in one chain on the team laptop; its log is `results/records/chain.log`
(gitignored). The result of each check is in section 6.

`show_record.py` draws or tabulates one episode of any of these records: road,
gear, engine, each actuator asked and applied, the heat against the baseline car,
the damage and the reward terms. On an old training record it reads the
regenerated roads beside it.

**What the records showed on the first look** (each line reproduces with the
command beside it):

- **Why `blind_seed6` does about twice the baseline's damage at 25 °C.**
  `python show_record.py results/records/conditions/1_25_C/blind_seed6.npz --episode 3 --table 30`
  (and `--list` for the peak). Once the 21.75 % climb starts it holds spark
  trim at its −8° limit to the end (in the air it trained in it advances to
  +4°) and runs the mixture slightly lean. To deliver the torque asked for with
  that retard the engine breathes more and burns later: in the rows from 240 s
  its manifold pressure is 149–178 kPa against the baseline's 135–168, and its
  housing runs 48–61 K above the baseline's, peaking at 930.4 °C. Its knock
  integral sits at 0.41–0.47 in those rows, so there is no knock reason for
  the retard: it is the network's answer to inputs it never saw.
- **The coolant zig-zag is the coolant pump at full duty.**
  `python show_record.py "results/records/conditions/1_25_C/*.npz" --zigzag`.
  The step-to-step swing of the coolant node, reversing on nearly every step,
  is the stiffness agreed for fixing on 30 September. It appears whenever the
  pump runs near 1.0, whatever the fan does: at 25 °C the baseline ECU (pump
  1.0) swings 2.18 K a step (95th percentile 4.77 K), blinded seed 4 (fan 0,
  pump 1.0) 2.66 K, blinded seed 1 (fan 1.0, pump 0.30) almost nothing. On the
  locked climb the baseline swings 1.68 K. The coolant is input 6 of the agent's
  23, and the charge temperature computed from it is input 9, so the agents
  see the artefact. Sub-stepping (agreed step 1) removes it.
- On the flat before the climb, several agents' lambda trim and fan duty
  alternate step to step (a chatter band on the plots). Noted, not analysed.
- The one-second knock spike at the grade step is visible in the ledger of
  every policy, the baseline's included.

## 2. The damage constants (part 1)

`damage_constants.py`, written up in `results/DAMAGE_CONSTANTS.md`. Sources were
opened on the day and are listed there and in `REFERENCES.md` section 7.

| constant | outcome |
|---|---|
| turbine scale 45 K | **calculable once a mechanism is named**: creep rupture, Larson–Miller with C = 20, gives **20.3 K** (19.5–21.2 K over 10³–10⁵ h). 45 K is oxidation-like (Q = 233 kJ/mol); no opened source gives Q for the housing's steel, whose grade BMW does not publish (ST1505 §5.2.1: "one single cast steel part"). Thermo-mechanical fatigue, which housings are designed against, is per cycle, not per second |
| turbine knee 850 °C | **bracketed**: the node sits 0.142 of the way from gas to ambient at the climb's steady state, so 900 °C gas → 778 °C, Conway's 930 °C → 804 °C, 1050 °C → 907 °C; the knee itself is 984 °C of gas |
| oil scale 12 K | the 10 °C doubling rule gives 14.4 K; the rule is not universal |
| oil weight 0.4, knee 408 K | one number (123.9 °C at weight 1); a valuation |
| knock knee 0.85 | drive C |
| knock weight 40, square | a valuation |

Re-scored on the twenty frozen episodes of all 24 policies: **every agent beats
current-grade under every calculated value; the ablation stays inconclusive**,
except with the knee at 907 °C (+6.33 [+0.35, +12.30]), where the knock term
grows to a fifth to a third of the damage. Without the knock term at that knee:
−1.43 [−6.87, +4.01]. It is the one-second knock spike at the grade step, post
hoc, on the untested knock model.

**Mistake 23, found doing this:** REFERENCES.md and CLAUDE.md said the knee is
"80 K more conservative" than Conway's 930 °C pre-turbine limit. That set a
housing temperature against a gas temperature. Like for like the knee is 984 °C
of gas, 54 K hotter. Corrected in both, and logged as mistake 23.

`damage_robustness.py` was refactored to share its loader and scorer
(`load_records`, `score`); its JSON and figure are byte-identical after.

## 2b. Three corrections to what was written before

- **Mistake 23** (above): the knee against Conway's gas limit.
- **Mistake 24: blinded seed 6 is not trading life for fuel.** CLAUDE.md, the
  agents' README and the results page said the reward lets it trade life for
  fuel on the five frozen episodes that weight life least. On those episodes it
  burns 6.3–9.9 % more fuel than the baseline, its return is negative (at most
  −45, against at least +32 on its other fifteen), and its climb spark trim is
  −3.2 to −6.4° against +2.6 to +3.9° on the others. It fails on both counts.
  Corrected in CLAUDE.md, in `record_agents.py` (the README's generator, which
  now prints each bad episode's fuel and return), in `make_page.py` (the page
  sentence, with a check that stops the build if it stops being true) and in
  `results/conditions_fixed12/README.md`.
- **`VALIDATION_PLAN.md` §11, point 6** said "every agent keeps its spark trim
  between +3 and +4° in every condition". That was read off the group medians
  (+2.6 to +4.0°). Agent by agent, 45 of 140 agent-condition cells sit under +3°
  and 12 retard; at 25 °C the two deepest, blinded seed 6 (−6.86°) and sighted
  seed 2 (−5.63°), are the two that do about twice the baseline's damage.
  `conditions_test.py` now keeps each agent's spark in its summary and prints
  the count, so the sentence has a run behind it. Mistake 22's shape: a claim
  about every member read off a median.

## 3. The decisions (part 2)

`results/VALIDATION_DECISIONS.md`: **thirteen open decisions**, a column each for
Ghassan and Jad, each with a recommended option and why.

- 1–7: the validation plan's, unchanged since Jad's review.
- 8–10: the damage constants. Recommended: keep the published values for the
  next training (one change at a time; the agreed steps already change it) and
  pre-declare the calculated ones as sensitivity rows, which cost seconds from
  the records.
- 11: keep the per-step records out of git and back them up outside the
  repository after every run.
- 12–13: where the next agents train and are checked, and the yardstick.
  Decision 12 first said to keep the trained air; Ghassan pointed out that we
  had agreed the opposite on 7 October (train on the extremes the car never
  reached, so the agent knows them; check the trained agent on the states we
  have logs for, so we know it trained correctly). It now says that, with a
  held-out transfer test. Decision 13: make current-grade's torque shortfall a
  gate in the preregistration.

`results/VALIDATION_PLAN.md` section 10 now points at the sheet. A copy for
sending is on the Desktop.

## 4. The page (part 4)

The four page commits of 30 September (`f35a5df`, `194d75f`, `a3656ac`,
`3f127a7`) were on the local `JMF-2340550` only. Their changes are applied to
this branch's working tree, **not committed**; built here, the page's data
equals the published v9 except the commit stamp and the date. Added: the
findings of 7–8 October in the summary, and a Validation section (the thirteen
decisions, what is recorded, the agents in other air, the damage constants),
every number a token from a results file. Checked at desktop width and at a true
390 px (an iframe: headless Edge will not lay out narrower than 510 px). The
header says `2864592 + uncommitted changes` until it is committed.

**Version 11, the same day, after Ghassan pointed out that only a section had
been added and the rest of the page still showed the old data.** Every section
now carries the current data:

- **Summary tiles:** the agents beat current-grade under all 16 damage formulas
  tried; the ablation's interval spans zero under 14 of them (the 2 exceptions
  weigh the untested knock term more); the sweep is unquotable because the
  thermal step alone moves a cut by 0.22 points at 2 s; the car scorecard is 4 of
  12 with spark under boost added. `make_page.py` checks each of these sentences
  against the data and stops the build if one stops being true.
- **Phase D:** the frozen episodes under the nine rulers (`damage_robustness.py`);
  blinded seed 6 on its worst and best frozen episode, step by step, beside the
  baseline; the step-by-step chart gains manifold pressure, knock, coolant and
  the running damage and fuel from the new records.
- **Simulation vs car:** spark under boost as a twelfth comparison (untested),
  with the 31 readings drawn against the model's baseline.
- **Validation:** the uncertainty budget (the thermal step's convergence at 1 s
  and 2 s; what one resolution step of each input moves) and a viewer of the
  recorded conditions-test episodes, condition by condition.
- **Caveats and footer:** the agreed steps before the next training, the agents'
  single climate, the thermal step as measured (and the pump-driven coolant
  swing), where the records live, and every new command.

**Version 12: current-grade as the comparing line everywhere.** Ghassan pointed
out that the Phase D charts still measured from the baseline ECU, though the
comparing line had been moved to current-grade on 7 October. Every comparison
chart now measures from current-grade:

- every policy: the reference line is current-grade's median, and each label
  is the margin over it in points;
- the ablation, paired by seed: each bar is the cut over current-grade, which
  sits at zero;
- the knock margin: the margin over current-grade, as trained and with spark
  advance forbidden;
- damage against fuel: both axes from current-grade, so it sits at the origin.
  Measured that way, 16 of 20 agents cut more damage AND burn less fuel than
  current-grade, which burns +5.9 % against the baseline;
- what the agents do on the climb: current-grade's setting is the reference
  line. Against it, every agent advances spark and cools less, 7 run richer,
  12 trim boost further;
- blinded seed 6's worst episode: current-grade is the reference (2527 damage
  units against its 521; +3.4 % fuel against it).

The cut itself stays against the baseline, as `evaluate.py` defines it, and
the baseline stays on each chart as a faint line, because the reward is paid
against it. Each new sentence is checked by `make_page.py` against the data.

**Version 13: the environment the agents trained in, drawn** (Ghassan: "a graph
showing the environment trained on and its details: speed, hills, how steep").
From the roads regenerated under every training step (`training_roads.py`),
extracted to `results/agents/terrain_dt1/training_env.json` by
`record_extracts.py`. The sighted and blinded agent of each seed drove the same
56 roads with the same weights (checked), so ten road sequences cover all twenty.

- The roads, per seed: every one of the 56 episodes as a row, coloured by grade,
  with its kind; an environment card: 130 km/h held after a 20 s run-up, 42 °C,
  101.3 kPa, 1 s steps, 900 s episodes, five kinds of road, grades −3 to +14 %.
- How steep: 52 % of training time on 4 % or more, 19 % at 12 % or steeper, 20 %
  downhill, nothing steeper than 14 %; the conditions test's hills marked beside
  it, the 25 °C one (21.75 %) beyond anything in training.
- Which gears: 98 % of training in 7th and 8th, 1.0 % in 5th, the gear the 25 °C
  hill ran in.
- Which weights: 124 of the 560 training episodes (22 %) weighted life at 0.089 or
  less, the range of blinded seed 6's bad frozen episodes; 13 of its own 56.

**That last count corrected mistake 24 the same day.** It had said blinded seed
6 fails on "the inputs it saw least"; it met such weights in 13 of its 56 training
episodes, so the retard is learned behaviour, not inexperience. Corrected in
CLAUDE.md, the decision sheet and the page.

A float32 detail found on the way: the locked climb's 12 % is stored as
0.11999999, so a threshold of exactly 12 % missed it (7 % instead of 19 % of the
time); the extract compares with a 1e-4 allowance.

The records are gitignored, so the page draws small committed extracts written
by the new `record_extracts.py`: `results/conditions_traces.json` (489 kB) and
`results/agents/terrain_dt1/bad_episode_trace.json` (47 kB); `episode_trace.json`
grew to 256 kB with the new series. The page is 1.2 MB. In a headless browser
every one of its 36 charts draws and the console is clean; checked at desktop
width and at 390 px.

## 5. Verification

| check | result |
|---|---|
| `verify_docs.py`, with the new documents included | All 73 checks pass (853 figure mentions) |
| `python -m app.test_replay` | 49 of 49 |
| `python -m app.test_simulation` | 16 of 16 |
| `python -m unittest app.test_agents` | 135 tests OK, 14 skipped as before (re-run after the chain; a first run during it tripped the suite's own guard against files changing on disk, which the chain and the page edits were doing) |
| the re-run episodes against their committed scores | all identical (section 6) |

## 6. The chain's checks

One chain on the team laptop, 00:11 to 03:59 on 8 October (`results/records/chain.log`):

| step | check | result |
|---|---|---|
| `conditions_test.py --resume-all` | every re-run row against the committed `results/conditions_test.json` | **840 of 840 identical**; the merge added only the per-agent spark keys, every earlier summary value unchanged, the figure byte-identical |
| `record_agents.py runs/terrain_dt1 --records-only` | every episode against its committed `eval_summary.json` before writing | **24 policies × 20 episodes equal**; `eval_record.npz` rewritten with 41 fields (61 min) |
| `knock_margin.py runs/terrain_dt1 --records-only` | every episode against `knock_margin.json` before writing | **20 agents × 20 episodes equal**; 20 records written |

Afterwards `record_agents.py runs/terrain_dt1 --report-only` rebuilt the agents'
README from the records: only the corrected blinded-seed-6 sentence and the
index's timestamp changed.

The records now take **188 MB**: training 53 MB and its regenerated roads 18 MB,
the frozen episodes 28 MB, the knock margin 26 MB, the conditions test 63 MB;
plus 70 MB of training-record copies that `record_agents.py` keeps beside each
agent. All of it is gitignored and exists on this laptop only (decision 11).

## 7. Not done, and why

- *(Superseded by section 8: committed as `75ca65f` with X1's
  preregistration, and the next training is running.)* Nothing was committed
  or pushed until X1: the request did not ask for it.
- The training recorder was new; X1 is the first training run with it.
- The chatter seen on the flat in one record is noted, not analysed.

## 8. X1: the agreed fixes, the extremes design, 23 seeds a side

Ghassan, 8 October: *"do it, add more seeds and retrain and update artifact"* —
decision 12 as worded on 7 October (train on the extremes the car never
reached; check on the states the logs hold). Jad's column of the decision sheet
is empty; `results/PREREGISTRATION_X1.md` section 9 says which recommended
options X1 adopts and what a different answer costs.

### 8.1 The four plant steps of 30 September, one at a time

On the locked climb, `check_premise.py`'s policies (the first row reproduces
the merged plant's published figures exactly):

| plant | baseline | current-grade cuts | preview over it |
|---|---|---|---|
| merged, 30 September | 920.1 at 883.0 °C | 43.4 % | −0.32 points |
| + thermal sub-stepping (`thermal.DT_SUB_MAX` 0.1 s) | 917.6 | 43.4 % | −0.32 |
| + every grade change ramped over 8 s | 850.4 | 47.0 % | −0.01 |
| **both** | **848.1 at 883.0 °C** | **47.0 %** | **−0.01** |

The ramp removed the one-step knock spike and with it all of the hand-written
preview deficit, as the merge review predicted. The spark trim is capped at 0
(the command still recorded beside what was applied), and the fingerprint is
schema 2 (`derived_sha` fatal, `derived.py` hashed, the code hash on text with
docstrings and comments stripped). `validate.py`: 8 of 11 (row 8, oil, 97.0 →
97.1 °C). The app's pins moved 873.1 → 872.7 °C and 604.8 → 604.2 °C; switching
the sub-stepping off brings them back exactly.

### 8.2 The extremes roads, and two defects found building them

`engine_env.ExtremesTrainingEnv`: the terrain families, plus per episode an
ambient on 25–45 °C, a speed target redrawn every 60–180 s on 60–150 km/h,
hills to 18 %, and the housing's heat capacity ×0.75–1.333. The first draft
failed its own smoke test:

- **Slowdowns asked for negative torque.** The model has no fuel cut and no
  engine braking, and a speed profile slowing at 0.8 m/s² asked the engine for
  less than nothing; the neutral policy, which IS the baseline, scored −112 to
  −693 an episode. Slowing down is now a coast no faster than the road allows.
- **A descent at moderate speed asked for less than the engine makes shut.**
  Measured: 12.0 Nm at 1200 rpm, 9.9 at 2100, 7.8 at 2700 with the throttle
  shut. A −1.7 % descent at 79 km/h asked 7.6 Nm of an engine making 10.7, and
  the tracking hinge fired on 127 steps (−47.5). Every road now asks at least
  15 Nm (`EXTREME_T_FLOOR_NM`), and the floor carries the acceleration term —
  without it, it put a 3.5 % hill under every launch from rest.

Then: `check_roads.py --road extremes` PASS on 40 roads (worst neutral −0.0043,
worst p95 tracking 0.018, 10 roads bind); `test_reward.py` 10 of 10 with two new
checks on these roads.

### 8.3 Fixed before training

| what | where | value |
|---|---|---|
| the held-out hills | `results/conditions_extremes_dt1/conditions_grades.json` | 42 °C 8.25 %, **25 °C 21.75 %**, 35 °C 12.00 %, **50 °C 7.50 %**, 90 / 82 / 76 kPa 8.75 / 12.00 / 12.25 % — every grade as on 29 September |
| the logged-drive check | `results/logged_cycles.json`, `logged_check.py` | six drives, 269.8 min, flat, at frozen episodes 4 and 15's weightings; pass = T (torque) and F (fuel ≤ +1 %) on all |
| the statistic | `analyse_x1.py` | the MEI rule at 5.43 points, both ways; dry run on the twenty of 29 September reproduces INCONCLUSIVE |
| the sanity probe | `sanity_probe.py` | a 50 K hotter housing must not get less protection; dry run on two agents of 29 September: 28 % and 37 % of climb states violate |
| the yardstick (decision 13) | measured | `current-grade` short of 95 % on 1 of 719 steps of the scored climb |
| the seeds | `power_analysis.py` | 23 a side: sign-test power 0.822 at the 29 September spread (20 give 0.640) |

On the way, `power_analysis.delta_for_power` was found returning 64.63 points at
23 seeds where a scan gives 5.26: its binomial tail underflowed near p = 1.
Fixed; the script's own printed output is byte-identical.

### 8.4 The documents, the commit, the launch

The stale premise figures (920.1, −0.3) were swept: live claims to 848.1 /
47.0 % / −0.0, records of the merged plant marked with the figures they keep.
`verify_docs.py` 73 of 73; its two expectations that moved (premise baseline,
app pins) carry the measured reason; `drift_test.py` rows 6 and 13
re-anchored and CAUGHT. Committed as `75ca65f`, then the 46 runs launched at
15:15 (`runs/extremes_dt1/LAUNCH.txt`), and the full drift test beside them.
Results, and the page, follow in this section when they exist.

### 8.5 Training, scoring, and the result

- **Training:** 46 runs, 15:16–23:01 on 8 October (465 min), two waves of 23; none
  crashed, none resumed. Every run's `meta.json` carries `plant_sha` 3c48890dd15bc116
  and the clean commit `75ca65f`.
- **Scoring** (`x1_score.py`, unattended): the twenty frozen episodes for 50 policies
  (120 min), then recorded again and found identical, all 1 000 (117 min).
- **The preregistered reading: SMALLER THAN THE MEI**, total and thermal-only alike:
  17 of 23 pairs below 5.43 points (sign p 0.0173; permutation p 0.0027); preview helps
  in 10 of 23 (p 0.80); costs damage in 13 of 23 (p 0.34, not significant). Mean
  −10.35 points, sd 24.78 (29 September: 7.84).
- **Post hoc, and the reason the reading must be read with care:** six sighted agents
  cut under 40 % on the scored climb, no blinded one does. They protected on their own
  training roads (25.6–47.4 %, inside the other forty's 11.2–59.3 %); on the climb five
  enrich at most half as deeply as their twins and three retard spark 2.2–4.3°.
- **Supervision:** 39 of 46 beat current-grade; 19 of 46 do more damage than the
  baseline ECU on at least one frozen episode.
- **Probe:** no agent passes outright (1.1–98.5 % of probed states violate).
- **Logged drives: 1 of 46 pass.** Torque is delivered (14 of 552 runs fail T); fuel is
  not: life weighted most, 252 of 276 runs over +1 % (median +4.33 %, worst +21.40 %);
  67 % of the extra fuel is burned with the ECU car's housing under 500 °C.
- **Sensitivity rows:** 38–39 of 46 beat current-grade under every formula; the
  ablation mean −9.9 to −13.0 points.
- **A bug, caught by its own guard:** the transfer test's workers loaded the 29 September
  agents (the `--set` of 8 October never reached them). Its harness check stopped it
  before any condition was scored; fixed, 5 of 5 identical, re-run after the logged check
  (07:22–10:54, all seven conditions). Its report then stopped once more, on reading the
  harness result from the grades file where a set trained after its hills keeps it
  beside them (`harness_check.json`); fixed, nothing re-run.
- **Transfer (T), descriptive, five episodes a condition:** held out, 30 of 46 agents
  beat that condition's current-grade at 25 °C on the 21.75 % hill (17 sighted, 13
  blinded) and 26 of 46 at 50 °C (14, 12); in range, 29 of 46 at 42 °C and 42 of 46 at
  35 °C; under untrained air pressure 25–32 of 46. 0–3 agents per condition do more
  damage than its baseline ECU (blinded seed 2 and sighted seed 17 in four conditions
  each, sighted seed 21 in two). Current-grade misses its torque on more than 1 % of the
  steps in five conditions (16–297 of 719), so only 25 and 35 °C compare against a
  comparator that delivers: held out 30, in range 42. The twenty of 29 September on the
  same hills (7 October, the plant before the fixes, spark advance allowed): 6 of 20 at
  25 °C, 19 of 20 at 50 °C. The figure's spark panel was drawn for the +4° trim and
  showed nothing for a set whose trim is capped at 0; it now draws each agent's own
  median trim, which shows who retards (8–18 of 46 per condition).
- Also on the way: the H/τ sweep and the timestep study re-ran on the sub-stepped plant
  (preview 0.0 at every binding τ; the step error at 2 s is gone); `record_agents.py`
  no longer counts the spark cap as slew limiting, and reads whether a cap was in force
  from the record itself.

### 8.6 The audit of 9 October: everything the simulation touches

Asked for after X1 was scored: go through every file that affects or is affected
by the simulation, the training and the agents, and say what needs editing or
regenerating. What was checked, and how:

- **The plant.** The live fingerprint equals all 46 X1 agents' `meta.json` on
  every fatal key, and on the plant files' full text: nothing has moved since
  they trained. Rebuilding the dataset from the eleven logs reproduced
  `derived_sha` exactly (only the file's timestamp changed, and was restored).
- **The generated files.** Every results file stamped with a plant is on the
  live one. X1's extracts (`record_extracts.py --x1`) re-ran byte for byte; the
  older plant's files that the page shows (`traces_130kmh.json`,
  `sweep_speed_grade.json`) are labelled there as the merged plant's record.
- **One pass of `full_run.py`**, updated first: it now also runs
  `premise_split.py`, `check_roads.py --road extremes`, `app.test_simulation`,
  `model_vs_data.py`, `analyse_phase_d.py` and `analyse_x1.py`, and its refusal
  uses agents this machine has. **Every block exit 0**, and the refusal exit 1
  as it should (`FULL_RUN.txt`, about 87 minutes): the dataset rebuilt to the
  same `derived_sha`; `validate.py` 8 of 11; `test_reward.py` 10 of 10; the
  premise and its split byte for byte; `check_roads.py --road extremes` PASS and
  byte for byte; the app suites 59 of 59 and 16 of 16; `verify_docs.py` 73 of 73;
  `drift_test.py` 16 of 16; `check_random_road.py` PASS on this plant for the
  first time (0 of 121, weakest 13.97 % at +11.9 K; it was last run on
  sep17's); the three analyses as published.

Found and fixed (in the working tree, not committed):

- **The fit that derives the thermal constants was never sub-stepped**
  (CLAUDE.md mistake 25). `calibrate_thermal.simulate` steps its own nodes once
  per 1 s sample, so the re-derivation of 8 October returned the same constants
  without touching the new integrator, and the claim that every caller shared
  it was repeated in `thermal.py`, the WBS and the validation plan. Measured,
  not shipped (`substep_fit_check.py`): the oil constants move under 2 %, the
  coolant constants a lot (radiator scale +61 %, block-to-ambient −42 %), the
  locked climb's baseline 848.1 → 845.6 and current-grade's cut +0.01 points.
  Shipping it changes `derived_sha`, so it waits for the next plant change. The
  false claims are corrected.
- **The ramp broke six tests of `app.test_agents`**, which nobody had run, and
  the app labelled the scored climb "181 s at 1.5 %". `app/agent_trace.py` now
  starts a climb on the last level step and reads a fixed road's full grade;
  the road's rise pins moved with their reason (2755 → 2733 m, 1917 → 1894,
  3247 → 3220). 135 tests OK, 14 skipped without `runs_c4/`.
- **X1's run directory was not closed**: `train.py --road extremes` without
  `--out` would have trained into it. `runs/extremes_dt1` is CLOSED now, as
  `terrain_dt1` was after its result; `train_all.py`'s examples name a new one.
- **Regenerated on today's plant:** `FULL_RUN.txt` (30 Sep); `validation_table.md`
  (row 8 97.0 → 97.1 °C, the only value that moved); `results/model_vs_data.json`
  (7 Oct: row 8's split is now 2.9 K coolant and 9.0 K oil node of an 11.9 K miss,
  where the merged plant gave 4.6 and 7.3), its figures 8–18 and the page.
- **Two missing regression tests**, named by the WBS: `test_plant_guards.py`
  (a 1 s step equals ten 0.1 s steps; the coolant settles at 2 s; one changed
  derived constant moves `derived_sha` and the file's timestamp does not).
- **Stale text:** `CLAUDE.md` (the phase table, the numbers list, the file list,
  the live list's status, and a convention: after a plant change, run all three
  app suites), the validation plan's §9 step 2, `results/README.md` (an X1 and a
  29 September section), the page's validation numbers (now labelled as the
  merged plant's stored traces).

Not changed, because each needs a decision or an owner:

- **Ship the sub-stepped fit** now (a retrain) or with the next plant change.
- **Back up X1's runs and records**: 1.7 GB of runs and 457 MB of per-step
  records exist only on this laptop (decision 11 recommends a sha-checked copy
  outside the repository after every run).
- **The app's verdict row for X1**: `app/agent_catalog.py` quotes verdicts for
  Phase D, D2 and C4 only, so X1 shows "none" (Jad's code).
- **`validation_numbers.json`** re-scores the merged plant's stored traces;
  recompute it on today's plant with the labels (WBS 3.12–3.15).
- **The presentation deck (23 September) and the PDFs** (`DOCUMENT_STATUS.md`,
  last checked 8 September), and the thesis figures 1–3 and 23, which show the
  merged plant's premise.

### 8.7 The results page: every abbreviation, with its equation

Asked for by Ghassan on 9 October. The page (`results/page/`, published as
version 20 of the same artifact) ends with a new section, "Every abbreviation
on this page": 77 entries in six groups (the claim and the experiments, damage
and scoring, the engine and the car, statistics, validation, units, drives and
files), each with what it stands for, the equation the code uses and the file
it lives in. The abbreviations were taken from the rendered page's own text,
not from memory.

The section has to type its equations, which makes it prose about code, the
kind that drifts. So `make_page.glossary()` checks it at every build: each
constant is read from the live module, each formula (damage, both tests, the
power calculation, corrected flow, the MEI) is evaluated against the function
that owns it, and each line the section quotes is looked for in its file. A
changed constant, a changed formula and a missing line were each shown to stop
the build. Its worked numbers are tokens: tau 47.2 s and H/tau 0.64 at the
climb's exhaust flow, the MEI as 100 x 50 / the merged baseline, current-grade's
cut on today's plant.

Found on the way and fixed: the Phase D section called the scored climb "a
900 s motorway climb". `evaluate.py` scores 720 s (`DURATION = 720.0`); 900 s
is the training episode and the speed-by-grade sweep. It now says 720 s.
`verify_docs.py`: 73 of 73.

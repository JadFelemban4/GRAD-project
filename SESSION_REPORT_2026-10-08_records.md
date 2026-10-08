# Session report — 7–8 October 2026: every step recorded, the damage constants, the decisions, the page

Branch `GRA-2340394`, on top of `2864592` (the validation plan). **Nothing in
this report is committed or pushed yet.** Written for Ghassan and Jad.

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

- Nothing is committed or pushed: the request did not ask for it. The page is
  built from the working tree and says so.
- The training recorder is new; no agent has been trained with it beyond the
  600-step check. The next training is gated on the five agreed steps and the
  thirteen decisions.
- The chatter seen on the flat in one record is noted, not analysed.

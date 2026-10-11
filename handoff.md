# handoff.md — pick this up and keep going

**What this file is for.** This is the entry point, and only that: what to run
first, what to do next, what not to touch. It is deliberately the shortest of the
three. `CLAUDE.md` is the permanent handoff and the mistake log — the rules, the
traps, and every mistake already made; read it before you change
anything. `CHECKPOINT.md` is a dated snapshot of what was verified and when, and
it is meant to go out of date. This file holds no history and makes no argument,
so it should never become a third source of truth. **Where any of the three
disagree, the scripts win: run the command and read what it prints.**

`REFERENCES.md` sits beside those three and answers a different question: where
every number we did **not** measure comes from. Read it before calling any band
in `validate.py` "published": four of the seven literature bands still have no
source, and rows 8–11 are not published bands at all — they come from our car.

You are taking over a project that works. Everything in the repository
regenerates, and `verify_docs.py` re-checks the published figures against the
shipped data every time it runs. What was missing was Phase D, and it has now
run.

> **Where the project stands, 30 September 2026: the two branches are merged.**
> Ghassan's physics, Jad's method — the first box of `CLAUDE.md`, and `conflict.md`.
>
> Four trained ablations, none decisive: Phase D and D2 INCONCLUSIVE; C4 smaller
> than the minimum effect of interest by the sign test only, the agents not
> converged; Ghassan's ten-pair retrain INCONCLUSIVE under the same rule. Write
> *preview does not separate from seed noise at these budgets*, never *preview
> does not help*. **Separately**, trained agents beat `current-grade` on the
> median in every set — but that margin rests on spark advance that only the
> untested knock model allows; with advance forbidden it disappears.
>
> **Before any new training**, do the five agreed steps in `CLAUDE.md`'s first
> box: sub-step the thermal network, extend the fingerprint to
> `data/derived_params.json`, cap the spark trim, ramp the grade changes, and
> write the new preregistration. Then drive C.
>
> `python analyse_phase_d.py`, `analyse_phase_d2.py` and `analyse_c4.py` print the
> sep17 results from the committed files (their agents re-run only from the tag
> `sep17-before-merge`); `results/agents/terrain_dt1/README.md` holds Ghassan's.

**There is now a second deliverable, `app/`, and it is NOT the missing piece.**
It runs this same physics beside the car in real time and estimates turbine
temperature, which the vehicle has no sensor for. It works, it is tested, and it
is the first thing anyone will ask to see. It does not test the claim; Phase D
and D2 do. If you have an hour, spend it on those, not on the app.

**Where the numbers stand today.** 321.7 minutes over eleven drives, eight
carrying samples, **26 distinct operating points spanning 30–75 kPa**. The load
residual is **1.4 % with the DIN constant derived** (k = 0.831, zero free
parameters) and **1.1 % with it fitted** (k = 0.839, one). Note the direction:
dropping the fitted parameter makes the residual **rise**, 1.1 → 1.4 %. Say that
out loud rather than quoting only the derived figure — and read mistake 12 in
`CLAUDE.md` before quoting either, because the residual cancels the breathing
model and therefore cannot validate it.

---

> ## 29 September 2026 — THE RETRAIN RAN
>
> Twenty agents, seeds 0–9 sighted and blinded, 130 km/h on varied roads, on the
> derived plant. **All twenty beat every hand-written policy; sighted minus
> blinded is +1.2 points (95 % CI −4.4 to +6.8, n = 10) — no measurable preview
> value.** Every agent advances spark to just under the untested knock model's
> knee, and with that advance forbidden (`knock_margin.py`) their median cut
> falls to ~41.6 %, below current-grade's 43.4 %: **most of their margin rests on
> the knock model, so drive C (knock) is now the most valuable drive.** Blinded
> seed 6 does more damage than the baseline on the five episodes that weight
> component life least. The fuel is settled (95 RON). Every action is recorded
> (`results/agents/`; the per-step records stay on the training machine,
> gitignored); `results/agents/terrain_dt1/README.md` has every table.
> `SESSION_REPORT_2026-09-29.md` is the full account. Committed 29 September.

<!-- RETIRED-OK: section 829.2, 548.6, 437.6 -->

```bash
python verify_docs.py      # every check must pass before you quote anything
python test_reward.py      # 8 of 8, four of them on the training roads
python check_roads.py      # PASS: the baseline can drive every training road
python check_premise.py    # the hand-written policies on the locked climb
```

A few minutes — five full rollouts. It prints the protection trigger, then one
row per policy, then a warning you must read.

**THE FOUR NUMBERS THIS FILE USED TO TELL YOU TO EXPECT ARE VOID.** They were
829.2 / 548.6 / 437.6 / 548.6, and the 15 September audit found three reasons
not to trust them — the baseline had its cooling switched off, the baseline ECU
was scheduled on a load the engine was not at, and the reactive comparator
protected less hard rather than merely later. See the box in
[README.md](README.md), and `AUDIT.md` findings C1, C2 and C3.

What it prints on the plant of 8 October (the locked scenario, 12 % at
130 km/h in 42 °C air, the climb ramped over 8 s, on the ZF 8HP51 gearbox; the
physics derived from the logs; the thermal network sub-stepped):

```
protection trigger: 1123 K (850 C) = the knee of the turbine damage term

policy                             fuel g    damage  peak turb C  peak oil C
----------------------------------------------------------------------------
baseline ECU (true neutral)          4544     848.1          883          94
reactive protection                  4683     559.7          860          94
current-grade protection             4810     449.6          853          94
predictive protection                4815     449.7          853          94
predictive, preview disabled         4683     559.7          860          94
----------------------------------------------------------------------------
  reactive protection            cuts damage  34.0 %
  current-grade protection       cuts damage  47.0 %
  predictive protection          cuts damage  47.0 %

  preview over reactive      +13.0 points
  preview over current grade  -0.0 points   <- THE HONEST ONE
```

**Read the warning underneath it.** The baseline peaks at 883 °C against the
850 °C trigger, so **the constraint binds**, and every protecting policy acts.
"Predictive, preview disabled" equals "reactive" **by construction**, not as a
finding (`AUDIT.md` C3). These are hand-written policies. Preview and
current-grade tie: the 8 s ramp of 8 October removed the one second of knock at
the grade step that was all of the merged plant's deficit.

<!-- RETIRED-OK: 920.1, 625.7, 520.5, 523.5, 4573, 32.0, 43.4, 43.1, 11.1, -0.3 -- the merged plant of 30 September -->
*(On the merged plant, 30 September to 8 October, it printed baseline 920.1 at
883 °C, reactive 625.7, current-grade 520.5 and predictive 523.5 (cuts 32.0,
43.4, 43.1 %), and preview −0.3 against current-grade: that knock spike. The
ramp is 70 of the 72 units the baseline moved; the sub-stepping 2.5.)*

<!-- RETIRED-OK: 959.8, 884, 679.0, 633.2, 637.4, 29.3, 34.0, 33.6, 4.3 -->
*(On `JMF-2340550-sep17`'s plant, before the merge, the same script printed
baseline 959.8 at 884 °C, current-grade cutting 34.0 % and preview −0.4 against
it. The equal peak is two of the merged plant's corrections cancelling: +5.5 K
from the exhaust flow, −6.2 K from the air density.)*

The row worth looking at is **current-grade protection**: no preview at all,
only the gradient the car is on right now, and hand-written preview **gains
nothing over it** (−0.0 points).

<!-- RETIRED-OK: 256.5, 801, 294.2, 812, 2.2, 1.8, 110 -->
*(This block held 256.5 / 801 °C / 2.2 points until 17 September — the figures
from before the H1 crank-angle correction took `plant.DTHETA_DEG` to 0.25°;
`AUDIT_FIXES.md` H1 records the move. It then held baseline 294.2 at 812 °C
until 22 September — the six-speed run at 110 km/h, from before the scenario
moved to 12 % at 130 km/h — in which the constraint did not bind and
current-grade beat predictive by 1.8 points. Both times the code moved and
this file did not.)*

**How the scenario compares with the car's own driving, measured over every
drive** — on 17–19 September, with the app's physics of that day (exhaust
= fuel × 15). On today's physics `7475b5d7` peaks at 872.7 °C (the pinned
figure in `app/test_replay.py`; 873.1 °C on the merged plant before the thermal
network was sub-stepped on 8 October) <!-- RETIRED-OK: 873.1 -- the merged plant's pin -->;
the other rows were not re-measured. Replay them through `app/` and read the peak estimated turbine housing
— a MODEL OUTPUT, not a reading — against the 850 °C trigger:

```
7475b5d7   55.1 min   890.6 C   +40.8   36 s above
670063b2    7.3 min   780.3 C   -69.5    0
cb67b01f   21.6 min   728.0 C  -121.9    0
3aca2ec1   41.7 min   676.1 C  -173.7    0
683640a0   24.0 min   664.1 C  -185.7    0
pull01      7.4 min   608.0 C  -241.8    0
fb988991   14.7 min   607.9 C  -242.0    0
3f64372e    0.7 min   340.1 C  -509.8    0
f51686d7        -- no estimate
drive10   119.4 min   797.6 C   -52.4    0      <- TAIF, a real mountain climb
                                        ----
total     292.0 min                      36 s  =  0.206 %
```

<!-- RETIRED-OK: 812, 38, 78 -->
**One drive of ten reaches the limit, for 36 seconds in 292.0 minutes.** When
this was first measured, on 17 September, the synthetic climb peaked at 812 °C
and missed by 38 K, so the car's own driving was 78 K hotter than the scenario
written to stress it — and the conclusion was that the scenario was wrong, not
the trigger. The scenario was re-chosen and the trigger did not move: the
locked climb now peaks at 884 °C and binds.

**And the mountain drive does NOT bind, which is the 19 September addition.**
`drive10` is Jeddah to Taif and back — two hours, ambient falling 31.5 to
20.5 °C and recovering, driver reaching 167 km/h. It peaks at **797.6 °C with
zero seconds above the trigger**. The hottest moment is a brief acceleration at
137 km/h and 5792 rpm, not the climb and not the top speed: the housing's ~50 s
time constant ignores bursts, and the 160 km/h stretch lasted five seconds.
**Road power, not altitude** — the locked scenario holds 88.7 kW for twelve
minutes, the Taif climb asks about half that.

Reproduce it: replay each log through `app.estimator.Estimator` and count
samples with `t_turb_c` above `engine_env.TURB_PROTECT_K - 273.15`.

> The old "548.6 against 548.6" identity was never evidence. With
> `use_preview=False` the preview term is literally zero, so the predictive
> policy returns the reactive policy's vector on every step — the identity
> could not have failed. The real ablation needs a TRAINED blinded agent, and
> that is Phase D — which has now run, and returned a null (the box at the top
> of this file).

---

## What each script should print today

Run any of these before quoting anything out of it. If a number here does not
reproduce, the number here is stale and the script is right.

| command | what it prints today |
|---|---|
| `python analyse_phase_d.py` | Phase D, on sep17's plant: 5 of 8 seeds positive, mean +4.8, sign p 0.3633, permutation p 0.4922 — NOT SIGNIFICANT. The agent's margin over `current-grade` is a DIFFERENT claim, and it rests on spark advance |
| `python analyse_phase_d2.py` / `python analyse_c4.py` | D2 INCONCLUSIVE (4 of 8, sign p 0.6367); C4 SMALLER THAN THE MEI by the sign test only (p 0.0352), permutation disagreeing, not converged. From the committed result files |
| `python check_premise.py` | baseline **848.1** at **883 °C**; reactive 559.7 (cuts 34.0 %), current-grade 449.6 (47.0 %), predictive 449.7 (47.0 %); preview over current-grade **−0.0**. Writes `results/premise.json`. Hand-written — read AUDIT.md C1 and C3 first |
| `python test_reward.py` | **10 of 10** pass. Neutral scores inside ±0.05 on the locked climb, on every training-road family and on the extremes roads of X1; refusing torque is punished on both kinds of road; the gearbox's torque table still matches the plant. A random policy scores just below neutral (informational) |
| `python check_roads.py --road extremes` | **PASS** over 40 of X1's training roads; 10 push the baseline past 850 °C; worst neutral reward −0.0043, worst p95 tracking error 0.018 |
| `python analyse_x1.py` | X1's preregistered test (`results/PREREGISTRATION_X1.md`): **SMALLER THAN THE MEI**, 17 of 23 pairs below 5.43 points (sign p 0.0173, permutation p 0.0027), the same without the knock term; 39 of 46 agents beat current-grade. Writes `results/X1_RESULT.txt` and `.json`; `--set terrain_dt1` is its dry run on the twenty of 29 September |
| `python logged_check.py --set runs/extremes_dt1` | X1's check on the car's own drives, replayed flat (six drives, two weightings): **1 of 46** agents pass. The torque is delivered; the fuel is not — with life weighted most, 252 of 276 runs burn more than 1 % over the baseline ECU. About 4 h; writes `results/logged_check_extremes_dt1.json` |
| `python conditions_test.py --set runs/extremes_dt1 --report-only` | X1's transfer battery, descriptive (five episodes a condition): held out, **30 of 46** beat that condition's current-grade at 25 °C on a 21.75 % hill and **26 of 46** at 50 °C; in range, 29 (42 °C) and 42 (35 °C). Re-scoring all seven conditions (`--resume-all`) takes about 3.5 h |
| `python check_roads.py` | **PASS** over 40 roads; 14 push the baseline past 850 °C; worst neutral reward about −0.002, worst p95 tracking error 0.016 against a 0.05 band. The terrain roads of the 29 September agents, as checked on 28 September on the plant they trained on; `results/training_roads.json` is kept as that record (the page draws it), so it was not re-run on X1's plant — X1's own roads are the `--road extremes` row |
| `python validate.py` | **8 of 11** inside their band — 6 of 7 against literature, **2 of 4 against our own car** (rows 8–11, oil and coolant); displacement 2997.5 cc; turbine τ **48.0 s** |
| `python compare_log.py data/master_points.csv` | fitted k 0.839 → **1.1 %**; derived k 0.831 → **1.4 %**, PASS. Mistake 12: it cannot see the breathing model |
| `python derive_params.py` | re-derives every constant the logs set into `data/derived_params.json`, in about a minute; `build_dataset.py` runs it |
| `python calibrate_thermal.py` | the thermal fit with leave-one-drive-out scores, `results/thermal_calibration.json` (~3 min) |
| `python run_results.py` | regenerates `results/traces_130kmh.json`, `sweep_speed_grade.json` and the Phase D files (~15 min) |
| `python compare_calibration.py` | the 28 Sep before/after comparisons, `results/calibration_comparison.json`, for figures 20–25 |
| `python check_map.py` | spark falls with load in every row and rises with speed in every column; **6 cells above the compressor ceiling**, 0 with no knock-free spark |
| `python build_dataset.py "logs/raw/*.csv"` | 321.7 min, 11 drives, 26 operating points — then it runs `derive_params.py` |
| `python model_vs_data.py` | eleven comparisons of the simulator against the car, each beside the figure the documents quote; ~10 min |
| `python verify_docs.py` | recomputes the published figures and scans every tracked document. **Do not memorise its count** — it moves each time a figure is added |
| `python -m app.test_replay` | **49 of 49**. Add `--full` for **59 of 59**: 14278 of 14340 samples estimated, peak estimated turbine **872.7 °C**, **14 thermal · 0 mismatch · 19 novel**. Both drives' pins moved on 28 Sep (exhaust = air + fuel; the derived enrichment dwell) and again on 8 Oct (the thermal sub-stepping, 0.4–0.6 K); the change behind each is written beside it |
| `python make_figures.py` / `python make_page.py` | the thesis figures in `results/figures/`, and the phone page `results/page/index.html` |

`validate.py` being 8 of 11 is expected, not a failure. Against literature the one miss
is the cruise-band EGT maximum. Against the car, rows 10 and 11 (coolant) pass since the
thermal network was derived from the logs; rows 8 and 9 (oil) still miss — the model's oil
runs cool of the car's over drive10's sustained high-rpm stretch (97.0 °C against
103–111) and its time constant is 60 s against the car's 70–100. Drive A is the data.
`validation_table.md` section A says how each band is built, section C what the
derivation changed.

---

## The path to a passing project

**Phase D is the bar**: validated simulator + agent beating two baselines + an
ablation isolating preview. Everything after D raises the ceiling. Nothing after
D protects the floor.

> **This route was followed on 21–22 September, and Phase D is done** — with
> eight seeds per arm rather than the five below, preregistered before any
> agent trained. The steps are kept as the record of how it was run, not as
> instructions, and some sentences in them describe the state before that run
> (step 1's "nothing in that file past the imports has ever been executed",
> for one). **Do not add seeds to Phase D:** more seeds, having seen the
> result, is a second experiment with its own preregistration
> (`results/PREREGISTRATION.md` section 7).

### Step 1 — install the trainer · 2 minutes
### Step 1 — decide the order: drives first, or retrain first

`logs/DRIVE_PLAN.md` lists three drives. A (a long climb) and B (roll-ons in a
held gear) would change the plant; C (knock) would not. Retraining after a plant
change is three more hours. Both orders are defensible — say which you chose.

### Step 2 — check the gates · a few minutes

```bash
python test_reward.py     # 8 of 8
python check_roads.py     # PASS
```

A training curve computed against a broken reward is worse than no curve,
because it looks like progress. The reward has carried a live hack twice
(mistake 5), and the training roads found a gearbox defect that no single-road
check could have (27 September).

Until that install happens, `train.py` raises `SystemExit` in its import block
with the instruction above, so **nothing in that file past the imports has ever
been executed.** Step 1 is also the first time anybody finds out.

### Step 2 — one training run, to prove it runs · 45 minutes

> **Agree the seed assignment first**, or you end up with three copies of
> seed 0.
### Step 3 — the runs that ARE Phase D · DONE 29 September (twenty, 234 min)

```bash
python train_all.py                          # seeds 0-9, sighted and blinded
python record_agents.py runs/terrain_dt1     # score, record, document
```

**About 45 minutes per seed. Re-measured 17 September**, by timing 2000 SAC
steps with gradient updates already running:
*(What this step said before it ran, kept for the commands:)*

```
OMP_NUM_THREADS=1   19.19 steps/s   ->  50k = 0.72 h
OMP_NUM_THREADS=6   18.14 steps/s   ->  50k = 0.77 h
```

*(This section said **4.6 hours on one CPU core** until 17 September, and told
you to plan an overnight. Wrong by 6.4×. Two things were wrong with it: the
"one CPU core" qualifier is meaningless — **one thread is marginally faster
than six**, because the policy network is tiny — and **SAC's gradient updates
are nearly free**, about 2 %, not the 6.5× slowdown claimed. The environment
alone runs 19.5 steps/s and the full loop 19.2. Each env step runs six engine
cycles at ~9 ms against ~1 ms for a gradient step, so the combustion model is
the whole cost, and `plant.DTHETA_DEG` is what sets it.)*

Checkpoints land every 10 000 steps, and re-running the same seed resumes from
its checkpoint -- at the SAME `--steps` only, and not for C4, whose runs are
started with `--no-resume` and re-run a crash from scratch
(`results/PREREGISTRATION_C4.md` section 6). A different `--steps` is refused:
see `train.py`, "A RESUME IS NOT A LONGER RUN".

**Expect a poor result.** It running at all is the point of this step.

`train.py` options: `--steps` · `--seed` · `--no-preview` · `--duration` · `--lr`
· `--out` (default `runs`).

### Step 3 — check the gate before believing any curve · 1 minute
> **Ask the owner before starting this.** It occupies the machine for the
> afternoon, and every run must use a different seed.

```bash
python train.py --steps 50000 --seed 0 ... --seed 4               # sighted
python train.py --steps 50000 --seed 0 ... --seed 4 --no-preview  # blinded
```

All four checks must pass, and neutral must score **inside ±0.05** — that is the criterion the check applies. The exact figure depends on the reset seed (the command table above quotes one draw, −0.00038, from `FULL_RUN.txt`), so do not treat one value as a requirement. A training curve
computed against a broken reward is worse than no curve, because it looks like
progress. The reward has carried a live hack twice (mistake 5), and the second
time it came back only because the plant changed underneath it.
Measured: **13.7 steps/s for one run alone**, about an hour each; ten sharing a
20-core machine took 173 min on 19 September — run them together, capped with
`OMP_NUM_THREADS=1`. Every episode is a new road; the output goes to
`runs/terrain_dt1/`, deliberately not `runs/`, where `train.py` would resume the
110 km/h agents. 50 000 steps is 55 episodes. **The training curve cannot show
learning** — returns vary with the road and the preference weights. Score it.

### Step 4 — score with the frozen protocol, and nothing else

```bash
python evaluate.py runs/terrain_dt1/sighted_seed0 runs/terrain_dt1/blind_seed0
```

Ten runs total, **about 45 minutes each — 7.5 hours altogether**. That is one
evening on one machine, or under an hour if the five of you take one seed each.
Agree who takes which seed before anyone starts.

*(This said "about 4.6 hours each … one overnight each, twice" until
17 September. See step 2: the rate was wrong by 6.4×, so Phase D is an evening,
not two weeks. **Nothing about the work changed — only the estimate.**)*
Twenty frozen episodes, median and IQR, **paired by seed** across all five.
Report three rows — sighted, blinded, and current-grade — and report damage two
ways, total and turbine plus oil, until the knock model is tested.

> **The twenty episodes never change.** Changing the test set after seeing
> results is the one mistake this project cannot recover from.

**Do not start Phase E or F until D produces a table.**

---

## What you must not do

| Never | Why |
|---|---|
| **Write to the vehicle's ECU** | Read-only OBD-II logging only. If a task seems to require it, it is the wrong task — say so rather than finding a way |
| Edit `data/` or `validation_table.md` by hand | Regenerate them |
| Edit `logs/raw/` | Those are measurements |
| Quote a number no script prints | Run `verify_docs.py` first |
| Change the locked scenario or the twenty episodes | `make_grade_climb` and `evaluate.EPISODES`. Training roads may vary; scoring may not |
| Point `train.py` at `runs/` | It resumes any checkpoint there — the 110 km/h agents |
| Feed `map_raw` into the model | It is a pre-throttle sensor. Use `plant.map_from_airflow()` |
| Feed the raw intake-air-temperature channel in as charge temperature | `Intake air temperature before throttle valve` is a **compressor outlet**. Use `plant.charge_temperature()` |
| Rely on a default plant geometry | Pass `geo=GEO` explicitly. This cost three weeks once |
| Call a validation band "published" without checking `REFERENCES.md` | Most have no source |
| Cite the 88 °C thermostat to BMW | The B58 has a heat-management valve; 88 °C is our own stand-in, identified from the logs |
| Quote the knock model as calibrated — or as refuted | The only test so far could not see knock (28 September) |
| Describe the scenario as a mountain | It is sustained load in sea-level air; altitude is not modelled |
| **Add a write path to `app/`, in any form** | The read-only rule is structural. `app/test_replay.py` asserts no write path exists |
| **Write raw samples to disk from `app/`** | Only what the model marks is persisted. A test asserts it |
| Lower an `app/` threshold to quiet a demo | A threshold changes for a measurement, and the measurement goes in the docstring. Mistake 14 |
| **Unzip a release archive over the tree** | Diff first, take only what is new. Mistake 16 |

| **Add a write path to `app/`, in any form** | The read-only rule is structural, not stylistic. A future version may SUGGEST an ECU parameter as text on a screen; applying it is a different product and must never share a code path. `app/test_replay.py` asserts that no write path exists |
| **Write raw samples to disk from `app/`** | The stream is memory → websocket → gone. Only what the model *marks* is persisted, to `app/review_log.jsonl`. A test asserts a whole replay creates exactly one file |
| Add a seventh live channel without justifying it | The adapter polls one channel per round trip, so every addition costs every other channel ~14 % of its rate. Put the reason in the channel's `why` field |
| Lower an `app/` threshold to quiet a demo | A threshold changes for a measurement, and the measurement goes in the docstring. See mistake 14 |
| **Unzip a release archive over the tree** | The v19 archive was older than the branch for everything except `app/` and would have reverted a fortnight of work. Diff first, take only what is new. Mistake 16 |

On that charge-temperature row, the car settles it. Over 762 boosted model
samples against 1097 logged readings of the vehicle's own boost channel (the
counts `verify_docs.py` asserts on the current dataset), the shipped
`charge_temperature()` sits **+1.9 %** from the car; the raw sensor, when it
was used, put the inversion **+23.7 %** high. An `ambient + 8 K` knob scored
+0.7 % when the correction was made on 10 September, on the smaller dataset of
the time, and was rejected for being tuned to the target.

One constant to watch while reading older prose: **`ENR_LOAD` is 180 kPa, not
200.** The enrichment gate is written in manifold pressure and manifold pressure
changed definition when the charge temperature was corrected; 180 on the current
scale selects exactly the samples that 200 selected on the old one, and
every enrichment figure reproduces without a refit.
On the charge-temperature row, the car settles it: 762 boosted model samples
against 1097 logged readings of the car's own boost channel put the shipped
`charge_temperature()` at **+1.9 %** of the car, where the raw sensor inverts
about 25 % high.

---

## Habits that keep this project defensible

1. **Change one thing, re-run, write down what happened.** Two changes at once
   and you no longer know which one did it.
2. **After changing `plant.py` or `thermal.py`** — re-run `validate.py` and update
   `validation_table.md` **in the same commit**.
3. **After changing the reward, the env, the plant, the gearbox or the roads** —
   re-run `test_reward.py` and `check_roads.py`, and paste the output into the
   commit message.
4. **Report numbers with their condition attached.** "1.4 % load residual over
   26 points, 30–75 kPa" — not "the model is accurate."
5. **Report the protection threshold with every preview figure.**
6. **Before calling a residual a validation, perturb the thing it supposedly
   validates and check the number moves** (mistake 12).
7. **Count readings, not rows.** The logger polls one channel per row; a row
   count can be 25 times the measurement count (AUDIT.md H4). The knock test
   failed exactly this way.
8. **Never promote a citation from memory.** Open the source and write down the
   page. `REFERENCES.md` is where that record lives.
9. **When a figure changes, grep the tree for the OLD value yourself and read
   every hit** — including inside sections marked `RETIRED-OK`, which the
   checker skips.

---

## When a new drive CSV arrives

The drives worth making are in `logs/DRIVE_PLAN.md` — A (climb), B (roll-ons),
C (knock) — each with its channel set and how to drive it.

```bash
cp <new>.csv logs/raw/<descriptive-name>.csv
python new_drive.py logs/raw/<descriptive-name>.csv   # what did it buy?
python build_dataset.py "logs/raw/*.csv"              # rebuilds all three data files
python compare_log.py data/master_points.csv          # re-scores the load
python model_vs_data.py                               # re-scores everything else
```

Then check: did anything get filtered out (a drive without `Coolant temperature`
contributes nothing); did the operating-point count rise; did any window fail
for span or a logger gap; does the load residual stay near 1.4 %. If the drive
changes a calibration, check how many **independent readings** support it and
that the variable you fitted against actually correlates. For lambda that is
engine speed (−0.47), air mass (−0.41) and dwell (−0.44); manifold pressure
carries no detectable signal (+0.11).

> **Census once with everything, then record the small set for real drives.**
> Fewer channels, faster refresh: 7 channels read each every 1.45 s, 26 every
> 7.5 s.

---

## The open problem, if you want the harder work

**Phase F's H2b threshold rule does not survive the correct engine.** It sets the
constraint at the 80th percentile of the unprotected trace, which assumes the
temperature spends a minority of the episode near its peak. The standard scenario
is a sustained climb — nine of twelve minutes at the top — so p80 lands on the
peak and the top three rows saturate at 100 % for both policies.

`check_premise.py` hit the same wall and solved it by anchoring to the **damage
model** instead — 1123 K, the knee of `exp((t_turb − 1123)/45)`. That is a
statement about the component rather than about one episode, and it transfers
between scenarios. `generality_test.py` now imports the same constant,
`engine_env.TURB_PROTECT_K`, so the two experiments cannot report different
protection limits.

**Replacing H2b's percentile rule with something that transfers is real,
publishable work.** Until then there is no usable H/τ table: the fixed-limit
H2 table is void too (`AUDIT.md` C1 and M12). Re-run `generality_test.py`,
read what it prints, and quote the threshold with every figure taken from it.
And do not use H/τ to rescue Phase D's null: that reading was drafted and
refuted (`results/PREREGISTRATION.md` limit 8).

---

## Where everything is

| You need | File |
|---|---|
| the rules, the traps, the mistakes already made, the improvement plan | [CLAUDE.md](CLAUDE.md) |
| **the project's result**, and the rules Phase D was run under | `python analyse_phase_d.py` and [results/PREREGISTRATION.md](results/PREREGISTRATION.md) |
| what was verified, and on what date | [CHECKPOINT.md](CHECKPOINT.md) |
| the last session in full | [SESSION_REPORT_2026-09-28_evening.md](SESSION_REPORT_2026-09-28_evening.md); the morning's is [SESSION_REPORT_2026-09-28.md](SESSION_REPORT_2026-09-28.md) |
| the prompt to continue in a new session | [NEXT_CHAT_PROMPT.md](NEXT_CHAT_PROMPT.md) |
| **where every number we did not measure comes from** | [REFERENCES.md](REFERENCES.md) |
| the drives still worth making, and how | [logs/DRIVE_PLAN.md](logs/DRIVE_PLAN.md) |
| results, figures, and the phone page | [results/](results/) — `results/page/index.html` |
| the project in prose, for a reader outside the team | [README.md](README.md) |
| Chapter 3's evidence | [validation_table.md](validation_table.md) |
| which team PDFs still carry void numbers | [DOCUMENT_STATUS.md](DOCUMENT_STATUS.md) |
| what the car can and cannot measure, all 656 channels | [logs/CHANNEL_CENSUS.md](logs/CHANNEL_CENSUS.md) |
| the live app, and why it estimates what it estimates | [app/estimator.py](app/estimator.py) — read its docstring first |

---

## The one thing to carry into the viva

**We built an ablation that could fail and ran it four times; it has not
separated.** Phase D and D2 are INCONCLUSIVE, C4 is smaller than the minimum
effect by the sign test only, and Ghassan's retrain is INCONCLUSIVE: preview does
not separate from seed noise at these budgets. Separately, and never as evidence
for preview, the trained agents beat `current-grade` — by a margin that rests on
spark advance the untested knock model allows. Carry the limits with both.

**The claim is a criterion, not a controller:** preview is worth acquiring only
where the horizon H and the protected part's time constant τ are comparable.

<!-- RETIRED-OK: section 13.4 -- the superseded viva claim, kept so it is recognisable -->
**The evidence for it is a TRAINED ablation, and nothing else.** A sighted agent
and a blinded one, trained identically, scored on twenty frozen episodes, paired
by seed, beside a comparator that reads only the grade the car is on now.

*What this section used to say, kept so it is recognisable:* the size of the
preview effect has changed four times, across two engines, two scenarios and
two protection triggers — 30 points on a guessed baseline, 4 after that
baseline was recalibrated against real data, 13.4 on the corrected engine at
the 1123 K limit. The first two were real measurements of different systems.
*(The 13.4 is void — `AUDIT.md` C1: it was measured against a baseline with
its cooling switched off; and the identity it leaned on could not fail, C3.)*

**The number is not the result. The ablation is.** The section used to close
with this sentence, which is the refuted claim:

> *"Preview-disabled has landed on reactive to the decimal, every single time.
> Whatever the gap is, it is attributable to preview information and to
> nothing else. That is the sentence to defend."*

> **REFUTED TWICE — do not defend this.** The identity cannot fail: with
> `use_preview=False` the preview vector is zeros, so `p_predictive` returns
> `p_reactive`'s action on every step and the two rows are one rollout
> (`AUDIT.md` C3). And the real ablation ran on 21–22 September — eight trained
> blinded agents against eight trained sighted ones, preregistered — and
> **preview is not significant**: 5 of 8 positive, mean +4.8, p = 0.3633.
>
> The defensible sentence is: *we built an ablation that could fail, ran it
> eight times, and it did not separate.* `python analyse_phase_d.py`.
The hand-written policies cannot carry this. Their "preview disabled equals
reactive, to the decimal" was an identity built into the code (AUDIT.md C3), and
their −0.4 against current-grade turned out to be the untested knock term. On
the existing (not yet valid) agents, training beat every hand-written policy by
about 26 points while sighted and blinded were indistinguishable.

**If the retrain shows no preview advantage on this scenario, that is the
result**: a statement about H/τ at this operating point, reported as one. Pair it
with a validation table that says what it does not cover, and defend that.

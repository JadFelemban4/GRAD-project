# handoff.md — pick this up and keep going

**What this file is for.** This is the entry point, and only that: what to run
first, what to do next, what not to touch. It is deliberately the shortest of the
three. `CLAUDE.md` is the permanent handoff and the mistake log — the rules, the
traps, and everything already gone wrong; read it before you change anything.
`CHECKPOINT.md` is a dated snapshot of what was verified and when, and it is
meant to go out of date. This file holds no history and makes no argument, so it
should never become a third source of truth. **Where any of the three disagree,
the scripts win: run the command and read what it prints.**

`REFERENCES.md` sits beside those three and answers a different question: where
every number we did **not** measure comes from. Read it before calling any band
in `validate.py` "published" — most of the eleven still have no source.

*(Rewritten 28 September 2026. The version before it told a newcomer to expect
figures that had been void since 16 September, behind a section-wide exemption
the checker could not see past, and ended by recommending an argument AUDIT.md
C3 had already withdrawn.)*

---

> ## ⚠️ READ THIS BEFORE ANYTHING ELSE — 28 September 2026
>
> **The Phase D retrain is ready and has not been run.** Everything it needs is
> committed: the locked scenario (12 % at 130 km/h, 42 °C, which binds), a new
> road every training episode, and a 1.0 s step that matches the scoring.
>
> **Decide one thing first: calibrate before or after the retrain.** Two drives
> in `logs/DRIVE_PLAN.md` (A and B) would change the plant — the oil node, the
> boost ceiling at low rpm. A plant change after the retrain means retraining
> again. It is about three hours of machine time either way.
>
> **Three things the latest pass found** (CLAUDE.md, current-state box):
> - the knock comparison could not have seen knock — it rests on one reading
>   of each ignition angle every ~8 s. Untested, not refuted;
> - preview's −0.4 against current-grade is entirely the knock term; on
>   turbine and oil damage alone the two tie;
> - the logs we have cannot calibrate the oil node — the drives disagree.
>
> **The ten agents in `runs/` are a record, not a result.** They trained at
> 110 km/h (nothing binds), at dt = 0.2 s, on one road.
>
> **Merge `origin/JMF-2340550-sep17`** before reporting Phase D. The code it
> needs is already here; the merge is documents and history.

## Do this first

```bash
python verify_docs.py      # every check must pass before you quote anything
python test_reward.py      # 8 of 8, four of them on the training roads
python check_roads.py      # PASS: the baseline can drive every training road
python check_premise.py    # the hand-written policies on the locked climb
```

## What each script should print today

Run any of these before quoting anything out of it. If a number here does not
reproduce, the number here is stale and the script is right.

| command | what it prints today |
|---|---|
| `python check_premise.py` | baseline **951.9** at **884 °C**; reactive 671.1 (cuts 29.5 %), current-grade 624.5 (34.4 %), predictive 628.4 (34.0 %); preview over current-grade **−0.4**. Hand-written — read AUDIT.md C1 and C3 first |
| `python test_reward.py` | **8 of 8** pass. Neutral scores inside ±0.05 on the locked climb and on every training-road family; the gearbox's torque table still matches the plant |
| `python check_roads.py` | **PASS** over 40 roads; 11 push the baseline past 850 °C; worst neutral reward about +0.004, worst p95 tracking error 0.015 against a 0.05 band |
| `python validate.py` | **8 of 11** quantities inside the published band; displacement 2997.5 cc; turbine τ **48.0 s** |
| `python compare_log.py data/master_points.csv` | fitted k 0.837 → **1.1 %**; derived k 0.831 → **1.4 %**, PASS. Mistake 12: it cannot see the breathing model |
| `python check_map.py` | spark falls with load in every row and rises with speed in every column; **6 cells above the compressor ceiling**, 0 with no knock-free spark |
| `python build_dataset.py "logs/raw/*.csv"` | 295.0 min, 10 drives, 26 operating points |
| `python model_vs_data.py` | eleven comparisons of the simulator against the car, each beside the figure the documents quote; ~10 min |
| `python verify_docs.py` | recomputes the published figures and scans every tracked document. **Do not memorise its count** — it moves each time a figure is added |
| `python -m app.test_replay` | **49 of 49**. Add `--full` for **59 of 59**: 14278 of 14340 samples estimated, peak estimated turbine **890.6 °C**, **15 thermal · 0 mismatch · 19 novel** |
| `python make_figures.py` / `python make_page.py` | the thesis figures in `results/figures/`, and the phone page `results/page/index.html` |

`validate.py` being 8 of 11 is expected, not a failure: the three outside are the
cruise-band EGT maximum and the two oil figures. The hottest oil in the logs is
**117 °C on drive10**, inside the published 115–140 °C band, so the oil miss is
now a measured one: the model runs a few kelvin cool on sustained load.

---

## The path to a passing project

**Phase D is the bar**: validated simulator + agent beating two baselines + an
ablation isolating preview. Everything after D raises the ceiling. Nothing after
D protects the floor.

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

### Step 3 — the ten runs that ARE Phase D · about three hours

> **Ask the owner before starting this.** It occupies the machine for the
> afternoon, and every run must use a different seed.

```bash
python train.py --steps 50000 --seed 0 ... --seed 4               # sighted
python train.py --steps 50000 --seed 0 ... --seed 4 --no-preview  # blinded
```

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
is a sustained climb, so p80 lands on the peak and the top rows saturate.
`check_premise.py` anchors instead to the damage model's knee, 1123 K, and
`generality_test.py` imports the same constant. **Replacing H2b's percentile rule
with something that transfers is real, publishable work.**

---

## Where everything is

| You need | File |
|---|---|
| the rules, the traps, the mistakes already made, the improvement plan | [CLAUDE.md](CLAUDE.md) |
| what was verified, and on what date | [CHECKPOINT.md](CHECKPOINT.md) |
| the last session in full | [SESSION_REPORT_2026-09-28.md](SESSION_REPORT_2026-09-28.md) |
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

**The claim is a criterion, not a controller:** preview is worth acquiring only
where the horizon H and the protected part's time constant τ are comparable.

**The evidence for it is a TRAINED ablation, and nothing else.** A sighted agent
and a blinded one, trained identically, scored on twenty frozen episodes, paired
by seed, beside a comparator that reads only the grade the car is on now.

The hand-written policies cannot carry this. Their "preview disabled equals
reactive, to the decimal" was an identity built into the code (AUDIT.md C3), and
their −0.4 against current-grade turned out to be the untested knock term. On
the existing (not yet valid) agents, training beat every hand-written policy by
about 26 points while sighted and blinded were indistinguishable.

**If the retrain shows no preview advantage on this scenario, that is the
result**: a statement about H/τ at this operating point, reported as one. Pair it
with a validation table that says what it does not cover, and defend that.

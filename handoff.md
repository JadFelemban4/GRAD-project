# handoff.md — pick this up and keep going

**What this file is for.** This is the entry point, and only that: what to run
first, what to do next, what not to touch. It is deliberately the shortest of the
three. `CLAUDE.md` is the permanent handoff and the mistake log — the rules, the
traps, and the thirteen things already gone wrong; read it before you change
anything. `CHECKPOINT.md` is a dated snapshot of what was verified and when, and
it is meant to go out of date. This file holds no history and makes no argument,
so it should never become a third source of truth. **Where any of the three
disagree, the scripts win: run the command and read what it prints.**

You are taking over a project that works. Everything in the repository
regenerates, every published figure was re-verified against the shipped data on
**11 September 2026**, and nothing is secretly broken. What is missing is not
correctness — it is Phase D.

**Where the numbers stand today.** 168.1 minutes over eight drives, six of them
carrying samples, **22 distinct operating points spanning 30–74 kPa**. The load
residual is **1.4 % with the DIN constant derived** (k = 0.829, zero free
parameters) and **1.1 % with it fitted** (k = 0.837, one). Note the direction:
dropping the fitted parameter makes the residual **rise**, 1.1 → 1.4 %. Say that
out loud rather than quoting only the derived figure — and read mistake 12 in
`CLAUDE.md` before quoting either, because the residual cancels the breathing
model and therefore cannot validate it.

---

## Do this first, before anything else

```bash
python check_premise.py
```

A few minutes — four full rollouts. It prints the protection trigger, then one
row per policy.
The damage column is the one that matters:

```
protection trigger: 1123 K (850 C) = the knee of the turbine damage term

policy                             fuel g    damage  peak turb C  peak oil C
----------------------------------------------------------------------------
baseline ECU (neutral trims)         4091     829.2          879         128
reactive protection                  4175     548.6          859         123
predictive protection                4314     437.6          852         109
predictive, preview disabled         4175     548.6          859         123
----------------------------------------------------------------------------
```

Against the baseline's 829.2, reactive cuts damage **33.8 %** and predictive
**47.2 %** — a preview edge of **13.4 points**, at the 1123 K limit. The script
does not print those percentages; they come from the damage column.

If those four damage figures appear, the environment works and you can trust
everything else in the repo. If they do not, stop and find out why before
writing any code.

> The last pair is the point. **548.6 against 548.6** — disabling preview
> collapses the predictive policy onto the reactive one exactly.

---

## What each script should print today

Run any of these before quoting anything out of it. If a number here does not
reproduce, the number here is stale and the script is right.

| command | what it prints today |
|---|---|
| `python check_premise.py` | damage 829.2 · 548.6 · 437.6 · 548.6 — rows 2 and 4 identical; trigger 1123 K |
| `python test_reward.py` | 4 of 4 checks pass; neutral scores **−0.00438** |
| `python validate.py` | **8 of 11** quantities inside the published band; displacement 2997.5 cc; turbine τ **48.0 s** |
| `python compare_log.py data/master_points.csv` | fitted k 0.837 → **1.1 %**; derived k 0.829 → **1.4 %**, PASS; a 20 °C reference would give 0.890, which the fit excludes |
| `python check_map.py` | spark falls with load in every row and rises with speed in every column; **6 cells `--`** (above the compressor ceiling), **0 `knk`** |
| `python build_dataset.py "logs/raw/*.csv"` | 168.1 min, 8 drives, 22 operating points |
| `python verify_docs.py` | recomputes the published figures, scans every tracked document for retired ones, and prints its own total. Every check must pass. **Do not memorise the count** — it moves each time a figure is added |

`validate.py` being 8 of 11 is expected, not a failure: the three outside are the
cruise-band EGT maximum and the two oil figures, and `validation_table.md` says
why. Everything the model says about hot oil is extrapolation: **107 °C** is the
hottest oil anywhere in the logs (`7475b5d7`), and the published band starts
above it.

---

## The path to a passing project

**Phase D is the bar**: validated simulator + agent beating two baselines + an
ablation isolating preview. Everything after D raises the ceiling. Nothing after
D protects the floor.

### Step 1 — install the trainer · 2 minutes

```bash
pip install "stable-baselines3[extra]"
```

Then uncomment the two lines under "Phase C onward" in `requirements.txt` so the
rest of the team installs the same thing.

Until that install happens, `train.py` raises `SystemExit` in its import block
with the instruction above, so **nothing in that file past the imports has ever
been executed.** Step 1 is also the first time anybody finds out.

### Step 2 — one training run, to prove it runs · 4.6 hours

> **Ask the owner before starting this.** It occupies a machine for a night, and
> the seed assignment has to be agreed first or you end up with three copies of
> seed 0.

```bash
python train.py --steps 50000 --seed 0
```

**About 4.6 hours on one CPU core, per seed. Measured, not guessed:** the
environment runs at 19.5 steps/s alone, and 3.0 steps/s once SAC's gradient
updates are included. The "1.5 hours" figure came from a formula optimistic by
3.6× — and `train.py`'s own docstring still carries it. Believe 4.6 hours.

**Plan an overnight, not an evening.** Checkpoints land every 10 000 steps, and
re-running the same seed resumes from its checkpoint.

**Expect a poor result.** It running at all is the point of this step.

`train.py` options: `--steps` · `--seed` · `--no-preview` · `--duration` · `--lr`
· `--out` (default `runs`).

### Step 3 — check the gate before believing any curve · 1 minute

```bash
python test_reward.py
```

All four checks must pass, and neutral must score **−0.00438**. A training curve
computed against a broken reward is worse than no curve, because it looks like
progress. The reward has carried a live hack twice (mistake 5), and the second
time it came back only because the plant changed underneath it.

### Step 4 — the ten runs that ARE Phase D · five overnights, twice

Five seeds, **one per team member**, run overnight:

```bash
python train.py --steps 50000 --seed 0      # ... through --seed 4
python train.py --steps 50000 --seed 0 --no-preview   # ... through --seed 4
```

Ten runs total, **about 4.6 hours each**. Split across five people, that is one
overnight each, twice. Agree who takes which seed before anyone starts, and get
the owner's go-ahead before committing five machines to it.

### Step 5 — the evaluation protocol · fix it once, never touch it

Three baselines. **One fixed evaluation protocol of 20 episodes.** Report median
and interquartile range over five seeds.

> **Once the 20 episodes are fixed they never change.** Changing the test set
> after seeing results is the one mistake this project cannot recover from.
> Write the 20 episode seeds into a file, commit it, and treat it as read-only.

**Do not start Phase E or F until D produces a table.**

---

## What you must not do

| Never | Why |
|---|---|
| **Write to the vehicle's ECU** | Read-only OBD-II logging only. If a task seems to require it, it is the wrong task — say so rather than finding a way |
| Edit `data/` or `validation_table.md` by hand | Regenerate them |
| Edit `logs/raw/` | Those are measurements |
| Quote a number no script prints | Run `verify_docs.py` first |
| Feed `map_raw` into the model | It is a pre-throttle sensor. Use `plant.map_from_airflow()` |
| Feed the raw intake-air-temperature channel in as charge temperature | `Intake air temperature before throttle valve` is a **compressor outlet** — the B58 carries its cooler inside the manifold. Use `plant.charge_temperature()` |
| Rely on a default plant geometry | Pass `geo=GEO` explicitly. This cost three weeks once |
| Change the test set after seeing results | Unrecoverable |

On that charge-temperature row, the car settles it. Over 587 boosted model
samples against 887 logged readings of the vehicle's own boost channel (median
**226 kPa**): the raw sensor inverts to 279.5 kPa, **+23.7 %**; the shipped
`charge_temperature()` gives 232.7 kPa, **+3.0 %**. An `ambient + 8 K` knob
scores 227.5 kPa, +0.7 %, and was rejected for being tuned to the target.

One constant to watch while reading older prose: **`ENR_LOAD` is 180 kPa, not
200.** The enrichment gate is written in manifold pressure and manifold pressure
changed definition when the charge temperature was corrected; 180 on the current
scale selects exactly the 1055 samples that 200 selected on the old one, and
every enrichment figure reproduces without a refit.

---

## Habits that keep this project defensible

1. **Change one thing, re-run, write down what happened.** Two changes at once
   and you no longer know which one did it.
2. **After changing `plant.py` or `thermal.py`** — re-run `validate.py` and update
   `validation_table.md` **in the same commit**.
3. **After changing the reward, the env, the plant, OR the scenario** — re-run
   `test_reward.py` and paste the output into the commit message. A reward is
   only safe relative to the dynamics it scores.
4. **Report numbers with their condition attached.** "1.4 % load residual over 22
   points, 30–74 kPa" — not "the model is accurate."
5. **Report the protection threshold with every preview figure.** A preview
   advantage quoted without the limit it was measured against is not a result.
6. **Before calling a residual a validation, perturb the thing it supposedly
   validates and check the number moves.** It takes one run, and the load
   residual failed that test (mistake 12).

---

## When a new drive CSV arrives

This is the most likely reason someone opens this repo.

```bash
cp <new>.csv logs/raw/
python build_dataset.py "logs/raw/*.csv"      # rebuilds all three data files
python compare_log.py data/master_points.csv  # re-scores the model
```

Then check, in order — each of these prints:

1. Did the sanity floor or the fuel-cut filter drop anything?
2. Did the operating-point count go up from 22? Zero new points means the drive
   was not steady enough — a driving problem, not a code one.
3. Did any window get rejected for span or a logger gap? A drive that loses every
   window that way was logged with too many channels selected.
4. Which compressor flow bins are still empty? Only 0.33–0.36 kg/s remains, and
   the MAF channel saturates at 1020.0 kg/h before it — 517 pinned samples across
   five drives — so no drive can fill it with this sensor.
5. Does the load residual stay near 1.4 % derived / 1.1 % fitted? A jump means
   the drive covers a region the model has not seen — information, not failure.

If the drive changes a calibration, **check how many samples support it and check
that the variable you fitted against actually correlates.** The enrichment map
has been wrong three times, most recently in its variable: λ correlates with
engine speed (−0.56), air mass flow (−0.49) and dwell above the gate (−0.47),
and only **+0.23** with manifold pressure — weak, and pointing the wrong way for
a load table.

> **Census once with everything, then record the small set for real drives.**
> Twenty channels log cleanly at 4.6 Hz with no dropouts. 655 channels drops 23 %
> of the drive.

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
publishable work.** Until then, use the fixed-limit H2 table, and quote the
threshold with every figure taken from it.

---

## Where everything is

| You need | File |
|---|---|
| the rules, the traps, **the thirteen mistakes already made** | [CLAUDE.md](CLAUDE.md) |
| what was verified, and on what date | [CHECKPOINT.md](CHECKPOINT.md) |
| the project in prose, for a reader outside the team | [README.md](README.md) |
| Chapter 3's evidence | [validation_table.md](validation_table.md) |
| which team PDFs still carry void numbers | [DOCUMENT_STATUS.md](DOCUMENT_STATUS.md) |
| what the car can and cannot measure, all 656 channels | [logs/CHANNEL_CENSUS.md](logs/CHANNEL_CENSUS.md) |
| what is recorded on a real drive, and why | [logs/CHANNEL_SET_FINAL.md](logs/CHANNEL_SET_FINAL.md) |

There is no `BRIEF.md`, `Context.md`, `ARCHITECTURE.md` or `DATA-MODEL.md` in
this repository. If you find one of those linked anywhere, the link is dead —
what it promised is in `CLAUDE.md` or `README.md`.

---

## The one thing to carry into the viva

The size of the preview effect has changed four times, across two engines, two
scenarios and two protection triggers — 30 points on a guessed baseline, 4 after
that baseline was recalibrated against real data, 13.4 on the corrected engine at
the 1123 K limit. Every one of those was a real measurement of a different
system.

**The number is not the result. The ablation is.**

Preview-disabled has landed on reactive **to the decimal, every single time**.
Whatever the gap is, it is attributable to preview information and to nothing
else. That is the sentence to defend.

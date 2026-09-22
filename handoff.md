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
in `validate.py` "published" — seven of the eleven still have no source.

You are taking over a project that works. Everything in the repository
regenerates, and `verify_docs.py` re-checks the published figures against the
shipped data every time it runs. What was missing was Phase D, and it has now
run.

> **Where the project stands, 22 September 2026: Phase D has run, and it is a
> NULL.** Sixteen SAC agents, eight seeds per arm, sighted against blinded,
> preregistered in `results/PREREGISTRATION.md` before any of them trained:
>
> ```
> positive (preview helped) : 5 of 8     mean difference : +4.8 damage units
> exact one-sided sign test   p = 0.3633
> exact paired permutation    p = 0.4922   alpha 0.05 -> NOT SIGNIFICANT
> ```
>
> **Separately**, the trained agent beats `current-grade` by **+29 to +34
> points** on five of eight seeds and is positive on seven of eight. Learned
> supervision works; preview specifically is what cannot be shown. Two claims,
> never one (`AUDIT.md` C3).
>
> Say three limits with the null, every time. **The budget:** these are C1
> agents, 50 000 steps, 11 training episodes — write *with agents trained to
> the C1 budget, preview does not separate from seed noise*, never *preview
> does not help*. **The blinded arm was not blind:** one fixed road plus a
> thermal clock, so a blind agent could memorise when the hill comes
> (`PREREGISTRATION.md` limit 7). **The power:** at Phase D's spread, eight
> seeds have power 0.10 against the minimum effect of interest, 50 damage
> units. And do not rescue the null with H/τ (limit 8).
>
> **In flight: Phase D2** — the same ablation on a randomised climb, so the
> blind arm is truly blind, preregistered in `results/PREREGISTRATION_D2.md`
> before any D2 agent trained. **No D2 result exists yet; do not predict one.**
>
> `python analyse_phase_d.py`. The full account is `CHECKPOINT.md`,
> 21–22 September.

**There is now a second deliverable, `app/`, and it is NOT the missing piece.**
It runs this same physics beside the car in real time and estimates turbine
temperature, which the vehicle has no sensor for. It works, it is tested, and it
is the first thing anyone will ask to see. It does not test the claim; Phase D
and D2 do. If you have an hour, spend it on those, not on the app.

**Where the numbers stand today.** 295.0 minutes over ten drives, seven
carrying samples, **26 distinct operating points spanning 30–75 kPa**. The load
residual is **1.4 % with the DIN constant derived** (k = 0.831, zero free
parameters) and **1.1 % with it fitted** (k = 0.839, one). Note the direction:
dropping the fitted parameter makes the residual **rise**, 1.1 → 1.4 %. Say that
out loud rather than quoting only the derived figure — and read mistake 12 in
`CLAUDE.md` before quoting either, because the residual cancels the breathing
model and therefore cannot validate it.

---

## Do this first, before anything else

<!-- RETIRED-OK: section 829.2, 548.6, 437.6 -->

```bash
python check_premise.py
```

A few minutes — five full rollouts. It prints the protection trigger, then one
row per policy, then a warning you must read.

**THE FOUR NUMBERS THIS FILE USED TO TELL YOU TO EXPECT ARE VOID.** They were
829.2 / 548.6 / 437.6 / 548.6, and the 15 September audit found three reasons
not to trust them — the baseline had its cooling switched off, the baseline ECU
was scheduled on a load the engine was not at, and the reactive comparator
protected less hard rather than merely later. See the box in
[README.md](README.md), and `AUDIT.md` findings C1, C2 and C3.

What it prints today (`FULL_RUN.txt`, 21 September; the locked scenario, 12 %
at 130 km/h in 42 °C air, on the ZF 8HP51 gearbox):

```
protection trigger: 1123 K (850 C) = the knee of the turbine damage term

policy                             fuel g    damage  peak turb C  peak oil C
----------------------------------------------------------------------------
baseline ECU (true neutral)          4664     959.8          884         110
reactive protection                  4843     679.0          862         111
current-grade protection             4936     633.2          861         112
predictive protection                4941     637.4          861         112
predictive, preview disabled         4843     679.0          862         111
----------------------------------------------------------------------------
  reactive protection            cuts damage  29.3 %
  current-grade protection       cuts damage  34.0 %
  predictive protection          cuts damage  33.6 %

  preview over reactive       +4.3 points
  preview over current grade  -0.4 points   <- THE HONEST ONE
```

**Read the warning underneath it.** The baseline peaks at 884 °C against the
850 °C trigger, so **the constraint binds, by about 34 K**, and every
protecting policy acts. "Predictive, preview disabled" equals "reactive" **by
construction**, not as a finding (`AUDIT.md` C3). And these are hand-written
policies: they say the environment rewards anticipation, not how much a
trained agent would gain. That is Phase D, in the box at the top of this file.

The row worth looking at is **current-grade protection**: no preview at all,
only the gradient the car is on right now, and hand-written preview **loses to
it by 0.4 points**.

<!-- RETIRED-OK: 256.5, 801, 294.2, 812, 2.2, 1.8, 110 -->
*(This block held 256.5 / 801 °C / 2.2 points until 17 September — the figures
from before the H1 crank-angle correction took `plant.DTHETA_DEG` to 0.25°;
`AUDIT_FIXES.md` H1 records the move. It then held baseline 294.2 at 812 °C
until 22 September — the six-speed run at 110 km/h, from before the scenario
moved to 12 % at 130 km/h — in which the constraint did not bind and
current-grade beat predictive by 1.8 points. Both times the code moved and
this file did not.)*

**How the scenario compares with the car's own driving, measured over every
drive.** Replay them through `app/` and read the peak estimated turbine housing
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
| `python analyse_phase_d.py` | **the project's result, a NULL.** 5 of 8 seeds positive, mean +4.8 damage units, exact one-sided sign test p = 0.3633, permutation p = 0.4922 — not significant. Also the agent's +29 to +34 points over `current-grade` on five of eight seeds, which is a DIFFERENT claim |
| `python check_premise.py` | **the constraint BINDS on the locked scenario** — baseline 959.8 at 884 °C against the 1123 K (850 °C) trigger; preview over current grade **−0.4 points**, the honest comparator. Hand-written policies, not the result. Read the warning it prints. AUDIT.md C1/C2/C3 |
| `python test_reward.py` | 4 of 4 checks pass; neutral scores **inside ±0.05** (−0.00038 in `FULL_RUN.txt`, 21 September). The exact value is one preference draw and moves with the reset seed — AUDIT.md M13 |
| `python validate.py` | **8 of 11** quantities inside the published band; displacement 2997.5 cc; turbine τ **48.0 s** |
| `python compare_log.py data/master_points.csv` | fitted k 0.839 → **1.1 %**; derived k 0.831 → **1.4 %**, PASS; a 20 °C reference would give 0.891, which the fit excludes |
| `python check_map.py` | spark falls with load in every row and rises with speed in every column; **6 cells `--`** (above the compressor ceiling), **0 `knk`** |
| `python build_dataset.py "logs/raw/*.csv"` | 295.0 min, 10 drives, 26 operating points |
| `python verify_docs.py` | recomputes the published figures, scans every tracked document for retired ones, and prints its own total. Every check must pass. **Do not memorise the count** — it moves each time a figure is added |
| `python -m app.test_replay` | **49 of 49**, and 59 of 59 with `--full` (was 36/46 before the audit fixes added three regressions). Replays `7475b5d7`: peak estimated turbine **890.6 °C**. That peak rose from 884.9 with the H1 crank-angle correction, not with any app change |
| `python -m app.server --replay logs/raw/7475b5d7-20260908_142743.csv --speed 8` | serves `http://localhost:8000` — dashboard, `/driver`, `/review`. **No car needed** |

`validate.py` being 8 of 11 is expected, not a failure: the three outside are the
cruise-band EGT maximum and the two oil figures, and `validation_table.md` says
why. **117 °C** is the hottest oil anywhere in the logs (`drive10`, the Taif
climb), which puts the lower end of the published 115–140 °C band inside our
own measurement: the model's 110.2 °C on the sustained climb is a real,
measured miss, not a disagreement with an unsourced number. Above 117 °C is
still extrapolation.

**And read what "published band" means before you defend one.** A citation pass
on 14 September opened the sources row by row. Two of the eleven bands are now
sourced to a page, one is partial, one is measured from our own logs, and
**seven have no source at all** — including the knock-limited spark, which a
deliberate search failed to support. `REFERENCES.md` section 3 gives the status
of each row and `validation_table.md` carries a `source` column pointing at it.
In the thesis, call an unsourced row an engineering-judgement band and say so.

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

```bash
pip install "stable-baselines3[extra]"
```

Then uncomment the two lines under "Phase C onward" in `requirements.txt` so the
rest of the team installs the same thing.

Until that install happens, `train.py` raises `SystemExit` in its import block
with the instruction above, so **nothing in that file past the imports has ever
been executed.** Step 1 is also the first time anybody finds out.

### Step 2 — one training run, to prove it runs · 45 minutes

> **Agree the seed assignment first**, or you end up with three copies of
> seed 0.

```bash
python train.py --steps 50000 --seed 0
```

**About 45 minutes per seed. Re-measured 17 September**, by timing 2000 SAC
steps with gradient updates already running:

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
its checkpoint.

**Expect a poor result.** It running at all is the point of this step.

`train.py` options: `--steps` · `--seed` · `--no-preview` · `--duration` · `--lr`
· `--out` (default `runs`).

### Step 3 — check the gate before believing any curve · 1 minute

```bash
python test_reward.py
```

All four checks must pass, and neutral must score **inside ±0.05** — that is the criterion the check applies. The exact figure depends on the reset seed (the command table above quotes one draw, −0.00038, from `FULL_RUN.txt`), so do not treat one value as a requirement. A training curve
computed against a broken reward is worse than no curve, because it looks like
progress. The reward has carried a live hack twice (mistake 5), and the second
time it came back only because the plant changed underneath it.

### Step 4 — the ten runs that ARE Phase D · five overnights, twice

Five seeds, **one per team member**, run overnight:

```bash
python train.py --steps 50000 --seed 0      # ... through --seed 4
python train.py --steps 50000 --seed 0 --no-preview   # ... through --seed 4
```

Ten runs total, **about 45 minutes each — 7.5 hours altogether**. That is one
evening on one machine, or under an hour if the five of you take one seed each.
Agree who takes which seed before anyone starts.

*(This said "about 4.6 hours each … one overnight each, twice" until
17 September. See step 2: the rate was wrong by 6.4×, so Phase D is an evening,
not two weeks. **Nothing about the work changed — only the estimate.**)*

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
| Call a validation band "published" without checking `REFERENCES.md` | Seven of the eleven have no source. Quoting one as published is the kind of claim an examiner can dismantle in a sentence |
| Cite the 88 °C thermostat to BMW | The B58 has no thermostat. It is a heat-management valve, and 88 °C is our own stand-in, identified from the logs |

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

---

## Habits that keep this project defensible

1. **Change one thing, re-run, write down what happened.** Two changes at once
   and you no longer know which one did it.
2. **After changing `plant.py` or `thermal.py`** — re-run `validate.py` and update
   `validation_table.md` **in the same commit**.
3. **After changing the reward, the env, the plant, OR the scenario** — re-run
   `test_reward.py` and paste the output into the commit message. A reward is
   only safe relative to the dynamics it scores.
4. **Report numbers with their condition attached.** "1.4 % load residual over 26
   points, 30–75 kPa" — not "the model is accurate."
5. **Report the protection threshold with every preview figure.** A preview
   advantage quoted without the limit it was measured against is not a result.
6. **Before calling a residual a validation, perturb the thing it supposedly
   validates and check the number moves.** It takes one run, and the load
   residual failed that test (mistake 12).
7. **Never promote a citation from memory — yours or a model's.** Open the
   source, write down the page, and if you looked and failed, record that
   instead. A fabricated citation is worse than a missing one because no
   script can catch it. `REFERENCES.md` is where that record lives.
8. **When a figure changes, grep the tree for the OLD value yourself and read
   every hit.** A green `verify_docs.py` proves only that the patterns which
   exist found nothing. Three sweeps in a row have left figures behind
   (mistake 11); the third time, five of them.

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
2. Did the operating-point count go up from 26? Zero new points means the drive
   was not steady enough — a driving problem, not a code one.
3. Did any window get rejected for span or a logger gap? A drive that loses every
   window that way was logged with too many channels selected.
4. Which compressor flow bins are still empty? Only 0.33–0.36 kg/s remains, and
   the MAF channel saturates at 1020.0 kg/h before it — 547 samples pinned there,
   on six separate drives — so no drive can fill it with this sensor.
5. Does the load residual stay near 1.4 % derived / 1.1 % fitted? A jump means
   the drive covers a region the model has not seen — information, not failure.

If the drive changes a calibration, **check how many samples support it and check
that the variable you fitted against actually correlates.** The enrichment map
has been wrong three times, most recently in its variable: λ correlates with
engine speed (−0.47), air mass flow (−0.41) and dwell above the gate (−0.44),
and only **+0.11** with manifold pressure — indistinguishable from zero, since
those rows hold only about 67 independent readings and the standard error is
about 0.12. Manifold pressure carries no detectable signal, which is enough to
reject a load table; it is not evidence that load points the other way.

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
publishable work.** Until then there is no usable H/τ table: the fixed-limit
H2 table is void too (`AUDIT.md` C1 and M12). Re-run `generality_test.py`,
read what it prints, and quote the threshold with every figure taken from it.
And do not use H/τ to rescue Phase D's null: that reading was drafted and
refuted (`results/PREREGISTRATION.md` limit 8).

---

## Where everything is

| You need | File |
|---|---|
| the rules, the traps, **the mistakes already made** | [CLAUDE.md](CLAUDE.md) |
| **the project's result**, and the rules Phase D was run under | `python analyse_phase_d.py` and [results/PREREGISTRATION.md](results/PREREGISTRATION.md) |
| what was verified, and on what date | [CHECKPOINT.md](CHECKPOINT.md) |
| **where every number we did not measure comes from**, and which bands are actually sourced | [REFERENCES.md](REFERENCES.md) |
| the live supervisor that runs beside the car | [app/](app/) — described in [CLAUDE.md](CLAUDE.md) |
| the project in prose, for a reader outside the team | [README.md](README.md) |
| Chapter 3's evidence | [validation_table.md](validation_table.md) |
| which team PDFs still carry void numbers | [DOCUMENT_STATUS.md](DOCUMENT_STATUS.md) |
| what the car can and cannot measure, all 656 channels | [logs/CHANNEL_CENSUS.md](logs/CHANNEL_CENSUS.md) |
| what is recorded on a real drive, and why | [logs/CHANNEL_SET_FINAL.md](logs/CHANNEL_SET_FINAL.md) |
| which numbers are measured, assumed or unsourced | [REFERENCES.md](REFERENCES.md) |
| **the live app, and why it estimates what it estimates** | [app/estimator.py](app/estimator.py) — read its docstring first |
| the app's channel budget, and why the set is six | [app/reader.py](app/reader.py) |
| the three alert types and every threshold's measurement | [app/alerts.py](app/alerts.py) |

There is no `BRIEF.md`, `Context.md`, `ARCHITECTURE.md` or `DATA-MODEL.md` in
this repository. If you find one of those linked anywhere, the link is dead —
what it promised is in `CLAUDE.md` or `README.md`.

---

## The one thing to carry into the viva

**We built an ablation that could fail, ran it eight times, and it did not
separate.** With agents trained to the C1 budget, preview does not separate
from seed noise: 5 of 8 seeds positive, mean +4.8, sign test p = 0.3633,
permutation p = 0.4922. Separately, and never as evidence for preview, the
trained agent beats `current-grade` by +29 to +34 points on five of eight
seeds: learned supervision works. Carry the limits with it, declared before
the numbers — the C1 budget, the blinded arm that was not blind, the power.
`python analyse_phase_d.py`.

<!-- RETIRED-OK: section 13.4 -- the superseded viva claim, kept so it is recognisable -->

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

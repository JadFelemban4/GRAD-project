# handoff.md — pick this up and keep going

You are taking over a project that works. Everything in the repository
regenerates, every published figure was verified on **9 September 2026**, and
nothing is secretly broken. What is missing is not correctness — it is Phase D.

---

## Do this first, before anything else

```bash
python check_premise.py
```

**~90 seconds.** You should see exactly:

```
baseline 829.2 · reactive 548.6 · predictive 437.6 · preview-disabled 548.6
```

If those four numbers appear, the environment works and you can trust everything
else in the repo. If they do not, stop and find out why before writing any code.

> The last pair is the point. **548.6 against 548.6** — disabling preview
> collapses the predictive policy onto the reactive one exactly.

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

This also confirms the one unverified encoding patch in `train.py` — that script
currently exits before reaching its print statements.

### Step 2 — one training run, to prove it runs · 4.6 hours

```bash
python train.py --steps 50000 --seed 0
```

**About 4.6 hours on one CPU core. Measured, not guessed:** the environment runs
at 19.5 steps/s alone, and 3.0 steps/s once SAC's gradient updates are included.
The old "1.5 hours" estimate came from a formula optimistic by 3.6×.

**Plan an overnight, not an evening.** Checkpoints land every 10 000 steps.

**Expect a poor result.** It running at all is the point of this step.

`train.py` options: `--steps` · `--seed` · `--no-preview` · `--duration` · `--lr`
· `--out` (default `runs`).

### Step 3 — check the gate before believing any curve · 1 minute

```bash
python test_reward.py
```

All four checks must pass. A training curve computed against a broken reward is
worse than no curve, because it looks like progress.

### Step 4 — the ten runs that ARE Phase D · five overnights, parallel

Five seeds, **one per team member**, run overnight:

```bash
python train.py --steps 50000 --seed 0      # ... through --seed 4
python train.py --steps 50000 --seed 0 --no-preview   # ... through --seed 4
```

Ten runs total. Split across five people, that is one overnight each, twice.

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
| Rely on a default plant geometry | Pass `geo=GEO` explicitly. This cost three weeks once |
| Change the test set after seeing results | Unrecoverable |

---

## Habits that keep this project defensible

1. **Change one thing, re-run, write down what happened.** Two changes at once
   and you no longer know which one did it.
2. **After changing `plant.py` or `thermal.py`** — re-run `validate.py` and update
   `validation_table.md` **in the same commit**.
3. **After changing the reward, the env, the plant, OR the scenario** — re-run
   `test_reward.py` and paste the output into the commit message. A reward is
   only safe relative to the dynamics it scores.
4. **Report numbers with their condition attached.** "2.8 % load residual over 22
   points, 31–82 kPa" — not "the model is accurate."
5. **Report the protection threshold with every preview figure.** A preview
   advantage quoted without the limit it was measured against is not a result.

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
2. Did the operating-point count go up? Zero new points means the drive was not
   steady enough — a driving problem, not a code one.
3. Did any window get rejected for span or a logger gap? A drive that loses every
   window that way was logged with too many channels selected.
4. Which compressor flow bins are still empty?
5. Does the load residual stay near 2.8 %? A jump means the drive covers a region
   the model has not seen — information, not failure.

If the drive changes a calibration, **check how many samples support it and check
that the variable you fitted against actually correlates.**

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
between scenarios.

**Replacing H2b's percentile rule with something that transfers is real,
publishable work.** Until then, use the fixed-limit H2 table.

---

## Where everything is

| You need | File |
|---|---|
| the claim, in one page | [BRIEF.md](BRIEF.md) |
| current state + today's run log | [CHECKPOINT.md](CHECKPOINT.md) |
| vocabulary and the car's quirks | [Context.md](Context.md) |
| how the code fits together | [ARCHITECTURE.md](ARCHITECTURE.md) |
| the data files and their columns | [DATA-MODEL.md](DATA-MODEL.md) |
| **the eight mistakes already made** | [CLAUDE.md](CLAUDE.md) |
| Chapter 3's evidence | [validation_table.md](validation_table.md) |
| which team PDFs are stale | [DOCUMENT_STATUS.md](DOCUMENT_STATUS.md) |
| what the car can and cannot measure | [logs/CHANNEL_CENSUS.md](logs/CHANNEL_CENSUS.md) |

---

## The one thing to carry into the viva

The size of the preview effect has changed four times — 30 points, 4 points,
13.4 points — across two engines, two scenarios and two protection triggers.
Every one of those was a real measurement of a different system.

**The number is not the result. The ablation is.**

Preview-disabled has landed on reactive **to the decimal, every single time**.
Whatever the gap is, it is attributable to preview information and to nothing
else. That is the sentence to defend.

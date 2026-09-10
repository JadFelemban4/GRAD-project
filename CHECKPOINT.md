# CHECKPOINT.md — state as of 9 September 2026

A snapshot: what is proven, what was run today, what is open. Regenerate the
numbers rather than trusting this file if it is more than a week old.

---

## Phase status

| Phase | Status |
|---|---|
| A · setup | done |
| B · match the simulator to the car | **passed** — 2.8 % load residual, 22 pooled points, 168.1 min |
| C · get an agent to learn | **next.** `train.py` exists and runs; nothing trained yet |
| D · baselines and the ablation | not started. **This is the floor of the project** |
| E · battery plant | not started. `battery.py` does not exist |
| F · the H/τ sweep | preliminary only, from hand-written policies |
| G · writing | not started |

**Phase D is the passing bar.** Validated simulator + agent beating two baselines
+ an ablation isolating preview. Do not start E or F until D produces a table.

---

## Full verification run — 9 September 2026

Every script in the repo was executed end to end. **All seven passed.**

| # | Script | Result |
|---|---|---|
| 1 | `plant.py` | ✅ four sweeps; torque 431–514 Nm across the boosted sweep |
| 2 | `validate.py` | ✅ **8 of 11** inside band; τ_turb 48.0 s; 2997.5 cc |
| 3 | `check_premise.py` | ✅ **829.2 · 548.6 · 437.6 · 548.6** |
| 4 | `verify_docs.py` | ✅ **all 22 figures match** |
| 5 | `test_reward.py` | ✅ **4 of 4** |
| 6 | `build_dataset.py` | ✅ 168.1 min, 8 drives, 22 points |
| 7 | `compare_log.py` | ✅ **2.8 % load residual, PASS** |
| 8 | `generality_test.py` | ✅ H2 table reproduced: 16.5 / 18.0 / 26.0 pts |

Nothing in the repository is stale. Every published figure regenerates.

### The premise check, in full

Protection trigger **1123 K (850 °C)** — the knee of the turbine damage term.

| policy | fuel g | damage | peak turb °C | peak oil °C |
|---|---|---|---|---|
| baseline ECU (neutral trims) | 4091 | **829.2** | 879 | 128 |
| reactive protection | 4175 | **548.6** | 859 | 123 |
| predictive protection | 4314 | **437.6** | 852 | 109 |
| predictive, **preview disabled** | 4175 | **548.6** | 859 | 123 |

**The ablation held again.** Preview-disabled lands on reactive across *all four*
reported quantities, not just damage. Reactive cuts damage 33.9 %, predictive
47.2 % — **13.4 points**.

The cost is legible and worth quoting: predictive burns **139 g more fuel than
reactive** (+3.3 %) and **223 g more than baseline** (+5.5 %) to buy that damage
reduction, and it drops peak oil by **19 °C** where reactive manages 5 °C.

### The validation table

| Quantity | Model | Published | Status |
|---|---|---|---|
| Displacement | 2997.5 cc | 2990–3000 | inside |
| MFB50 at MBT | 8.5° | 8–10 | inside |
| Best BSFC (λ1, knock-feasible) | 241.2 | 235–260 | inside |
| Knock-limited spark (3000 / 200 kPa) | 11.0° | 8–14 | inside |
| EGT cruise band, min | 714.5 °C | 600–750 | inside |
| EGT cruise band, max | 777.3 °C | 600–750 | **outside** |
| Turbine housing τ | 48.0 s | 40–120 | inside |
| Oil temp, sustained climb | 110.2 °C | 115–140 | **outside** |
| Oil τ | 16.0 s | 20–400 | **outside** |
| Coolant, thermostat-regulated | 94.5 °C | 88–108 | inside |
| Coolant apparent τ | 9.5 s | 1–600 | inside |

The three misses are documented in `validation_table.md` and are **not** to be
closed by tuning toward the band.

### The reward gate

| check | result | detail |
|---|---|---|
| neutral scores ≈ zero | PASS | −0.00438 (want \|r\| < 0.05) |
| refusing torque is punished | PASS | starver **−0.28044** vs neutral −0.00438 |
| disabling preview changes the observation | PASS | max \|Δobs\| = 1.44 |
| rewards are finite | PASS | 1499 / 1499 / 1499 steps |

For information, not pass/fail: a random policy scores −0.08197.

---

## Changes made on 9 September

Two fixes and one documentation correction. **No calculation changed; every
number above is identical before and after.**

### 1. `gymnasium` was not installed

Installed **1.3.0**. It is an active line in `requirements.txt` (only the SB3 and
torch lines are commented out), so this was a missing environment, not a missing
dependency declaration.

### 2. Console encoding — six scripts crashed or mangled their own output

`build_dataset.py` wrote all three CSVs successfully and **then died** printing
its summary table, because a Windows console defaults to cp1252 and cannot encode
`λ`. The data was fine; the run looked failed. `validate.py` printed `—` as `?`
in its title.

Fixed by forcing UTF-8 on stdout in the six scripts that print non-ASCII:
`build_dataset.py`, `validate.py`, `compare_log.py`, `extract_steady.py`,
`generality_test.py`, `train.py`.

All six re-run clean at exit code 0. **`train.py`'s patch is the one exception —
it is unverified at runtime**, because the script exits immediately with a clean
"stable-baselines3 is not installed" message and never reaches its print
statements. It compiles; it will be confirmed the first time SB3 is present.

An audit of all 13 scripts confirms **no script prints non-ASCII without the
guard**. The remaining seven confine theirs to comments and docstrings.

### 3. `CLAUDE.md` carried a stale drive count

It said "seven drives, 113 minutes, five carrying samples." The data says **eight
drives, 168.1 minutes, six carrying samples**.

The old sentence was also wrong in a subtler way, and the correction records the
distinction: **`fb988991` does carry samples** — 16.3 minutes of them — but not
one of its windows survives the span and gap checks, so it contributes zero
*operating points*. Six carry samples; five carry points. Three different counts.

---

## Open problems, honestly stated

### 1. Phase F's H2b threshold rule does not survive the correct engine

H2b sets the constraint at the 80th percentile of the unprotected trace, which
assumes the temperature spends a *minority* of the episode near its peak. The
standard scenario is a sustained climb — nine of its twelve minutes at the top —
so p80 lands on the peak and the top three rows saturate at 100 % for both
policies.

Today's run confirms it, unchanged:

| C_turb J/K | τ s | H/τ | t_ref K | reactive | predictive | edge |
|---|---|---|---|---|---|---|
| 800 | 6.7 | 4.47 | 1152 | 100.0 % | 100.0 % | 0.0 |
| 2500 | 21.0 | 1.43 | 1152 | 100.0 % | 100.0 % | 0.0 |
| 6000 | 50.3 | 0.60 | 1146 | 100.0 % | 100.0 % | 0.0 |
| 18000 | 150.9 | 0.20 | 1022 | 0.0 % | 57.0 % | **57.0** |
| 60000 | 503.1 | 0.06 | 752 | 0.0 % | 9.7 % | 9.7 |

**Until the percentile rule is replaced, use the fixed-limit H2 table:**

| C_turb J/K | τ s | H/τ | reactive | predictive | preview edge |
|---|---|---|---|---|---|
| 800 | 6.7 | 4.47 | 79.6 % | 96.1 % | 16.5 pts |
| 2500 | 21.0 | 1.43 | 78.7 % | 96.7 % | 18.0 pts |
| 6000 | 50.3 | 0.60 | 73.2 % | 99.1 % | **26.0 pts** |
| 18000 | 150.9 | 0.20 | — | — | never exceeds the limit |
| 60000 | 503.1 | 0.06 | — | — | never exceeds the limit |

Preview edge rises as τ grows — **16.5 → 18.0 → 26.0** as H/τ falls from 4.47 to
0.60 — then the component becomes massive enough that the constraint stops
binding. That is the direction the physical argument predicts.

**These numbers moved from 0.0 / 0.1 / 0.2 at the old 930 K trigger. Nothing
about the plant changed — only the threshold.** Report the threshold with every
preview figure.

### 2. Known limitations to state in the thesis, not fix quietly

- **Vehicle validation covers 31–82 kPa only.** Steady points require steady
  driving, which is light-load driving.
- **The two manifold-pressure estimates diverge under boost.** Above 200 g/s:
  inverted 297 kPa against a logged 233 kPa, a 28 % gap. The inversion is right
  at part load and wrong under boost.
- **Peak power is not a prediction.** Manifold pressure is an input. An operating
  line is not a compressor map.
- **The compressor envelope is unmeasured above 0.303 kg/s corrected**, because
  that is where the MAF saturates. Only the 0.33–0.36 kg/s bin remains empty and
  no drive can fill it with this sensor.
- **The radiator is not identifiable on this car**, and the channel census proves
  it: every water-pump and fan-actual channel is all-zero. A constrained fit
  gives R² = 0.157 with a negative ram coefficient. Stop trying.
- **Oil above 103 °C is extrapolation.** The hottest oil anywhere in the logs is
  107 °C.
- **Steady points are steady for fast quantities only.** The 60 s window is fully
  settled for air, lambda, spark and manifold pressure, and reaches just **71 %**
  of a turbine thermal step (τ = 48 s). Never validate a thermal quantity at a
  steady point.
- **Enrichment uses dwell above 200 kPa as a proxy** for turbine inlet
  temperature, which this vehicle does not expose. The weakest cell of the fit is
  3500–4500 rpm at short dwell.

---

## What to do next, in order

1. `pip install "stable-baselines3[extra]"` — **2 minutes**. Also confirms the
   last unverified encoding patch.
2. `python train.py --steps 50000 --seed 0` — **about 4.6 hours on one CPU core**,
   measured not guessed: the environment runs at 19.5 steps/s alone and 3.0
   steps/s once SAC's gradient updates are included. **Plan an overnight, not an
   evening.** Checkpoints land every 10 000 steps. Expect a poor result; it
   running is the point.
3. `python test_reward.py` before trusting any training curve.
4. **Five seeds, one per team member, overnight** — `--seed 0` through `--seed 4`.
   Then the same five with `--no-preview`. That is Phase D's input.
5. **Phase D**: three baselines, one fixed evaluation protocol of 20 episodes,
   median and interquartile range over five seeds.

> **Once the 20 evaluation episodes are fixed they never change.** Changing the
> test set after seeing results is the one mistake this project cannot recover
> from.

Full detail: [handoff.md](handoff.md).

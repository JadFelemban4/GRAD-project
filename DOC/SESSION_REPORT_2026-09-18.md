# Session report — 18–19 September 2026

**Audience:** the team. It assumes you know the project and that at least one of
you knows engines, so there is no H/τ primer and no tour of the cycle model.
Everything is in the order it happened, including the four things that were
wrong on the first attempt.

**Branch:** everything is on **`JMF-2340550-sep17`**. `JMF-new-plan` and `main`
were not touched. `git diff 5ef1aa2..HEAD` is this session and nothing else.

---

## Headline

| | |
|---|---|
| **The scenario blocker is gone.** | Locked at 12 % / 130 km/h, chosen from a measured envelope before any training existed. |
| **Phase C ran for the first time.** | Two agents trained, 63 min each. |
| **Phase D has a protocol and a first point.** | Twenty frozen episodes. **Sighted beats blinded by +11.7 points.** One seed each — not quotable yet. |
| **A gearbox defect was found and fixed.** | The model upshifted into top gear halfway up a 12 % grade. |

---

# Part 1 · The merge, and verifying the tree

`main` on the laptop was **behind both remote branches** and carried no commit
they lacked. `JMF-2340550` held everything but one commit; `JMF-new-plan` added
`aca526d`, which only creates `ABSTRACT.md`, `CONTROL_SCOPE.md`, three
`DOC/Abstract_*.docx` and `presentation/plan.html`.

Fast-forward, then merge: **zero conflicts**.

Dependencies installed (`torch` 2.14.0, `stable-baselines3` 2.9.0, `pandas`
3.0.5, `gymnasium` 1.3.0, plus `fastapi`/`obd` for the app), then every script
run on the merged tree:

| script | result |
|---|---|
| `verify_docs.py` | 38 of 38, 311 figure mentions |
| `test_reward.py` | 4 of 4 |
| `python -m app.test_replay` | **49 of 49** |
| `compare_log.py` | PASS, 1.3 % derived / 1.1 % fitted, 23 points |
| `check_premise.py` | baseline 294.2 at 812 °C, constraint does not bind |
| `train.py --steps 3000` | ran; SAC trains |

---

# Part 2 · Six stale figures, all from the same cause

The 16 September audit fixes moved the code and no document followed. **Mistake
11 for the fifth time.**

| where | said | the script prints |
|---|---|---|
| CLAUDE.md, README.md, handoff.md | 256.5 · 801 °C · 2.2 pts | **294.2 · 812 °C · 1.8 pts** |
| CLAUDE.md, handoff.md | 36 of 36 / 46 of 46, peak 884.9 °C | **49 of 49**, peak **890.6 °C** |
| CLAUDE.md phase table + app section | "six known bugs", "none of these is fixed" | **all six are fixed** |
| presentation/README.md | 801 °C, "thirteen mistakes" | 812 °C, **sixteen** |

<!-- RETIRED-OK: quoting the void headline IS the finding -->
**The most dangerous one was not in that table.** `CLAUDE.md` stated *"reactive
cuts damage 33.8 %, predictive 47.2 % — 13.4 points"* as a plain sentence near
the top of the file, with the retraction three paragraphs down under a different
heading — and a parenthesis underneath asserting the 13.4-point gap was
*"unchanged"*, which had stopped being true. **A reader who stopped at the bold
number would have carried a void figure into a meeting.** It is now a `VOID`
heading that says what to run instead.

<!-- RETIRED-OK: the figures named are the ones the run rejected -->
**`verify_docs.py` caught the author mid-edit**, correctly: explaining the void
figure re-quoted 829.2 and 548.6, and the run failed naming `CLAUDE.md:187`. The
errata came out with the figure. **When a number goes void, its corrections go
with it.**

---

# Part 3 · The university name, and a guard for it

<!-- RETIRED-OK: the wrong name is the subject of this section -->
`CLAUDE.md` line 13 read **"King Abdulaziz University, Jeddah"** until commit
`d57f3da` (14 September), where it became **"University of Jeddah"** — inside a
commit whose subject was *"docs: add REFERENCES.md"*, so the change is invisible
from the log. Any copy taken from `main` before this session still has the wrong
name. The two are genuinely confusable: the University of Jeddah was split out of
King Abdulaziz University in 2014.

Confirmed with the team: **University of Jeddah**.

<!-- RETIRED-OK: naming the guarded string is the point -->
`King Abdul[aA]ziz` is now a `RETIRED` pattern. **Verified by planting the string
in `handoff.md` and watching the run fail** (`WRONG handoff.md:387`), then
reverting.

`DOC/*.docx`, `DOC/*.pdf` and `presentation/index.html` were checked by hand —
**none carries a university name at all**, which is open if the submission
template needs one.

---

# Part 4 · The training-time figure was wrong by 6.4×

`train.py` carried `STEPS_PER_S = 3.0`, quoted everywhere as *"about 4.6 hours on
one CPU core"*, which turned Phase D into "five overnights, twice" in
`handoff.md`.

Re-measured by timing 2000 SAC steps with gradient updates already running:

```
OMP_NUM_THREADS=1   torch=1   19.19 steps/s   ->  50k = 0.72 h
OMP_NUM_THREADS=6   torch=6   18.14 steps/s   ->  50k = 0.77 h
```

**Both halves of the old claim were wrong, and neither is a hardware
difference:**

- *"on one CPU core"* is meaningless — **one thread is marginally faster than
  six**; the policy network is small enough that threading overhead exceeds the
  gain.
- **SAC's gradient updates do not cost 6.5×. They cost about 2 %**: the
  environment alone runs 19.5 steps/s and the full training loop 19.2. An env
  step runs six engine cycles at ~9 ms against ~1 ms for a gradient step, so the
  combustion model is the entire cost — and **`plant.DTHETA_DEG` is what sets
  it**, which matters because it was halved on 16 September.

`STEPS_PER_S` → 19.2. This changes a printed estimate and nothing else.

**A full run later measured 63 minutes, not 45.** The 2000-step probe was
optimistic; quote 63.

---

# Part 5 · `team/` — one profile per person

Five people share the repository and do not share a background. One is
comfortable with engines and lost in reinforcement learning; another is the
reverse. An explanation pitched at the wrong person is wasted in both directions.

The mechanism is **`git config user.email`**, because it is already per clone —
each person sets it once and it needs no coordination. `CLAUDE.md` now opens by
telling the assistant to run it and read the matching profile, and to **say so**
if none matches.

```
team/README.md     how it works, how to add yourself, and what does NOT
                   belong in a committed profile
team/_TEMPLATE.md  copy this; it asks for the awkward parts on purpose
team/jad.md        written from his own learning notes
team/ghassan.md    a STUB, marked as one
```

`ghassan.md` carries only what the team actually stated — student number
**2340394**, GitHub **`badcloor`**, engines yes, this project yes. **Every other
section says "unrecorded" rather than guessing**, because a profile that guesses
someone's background steers every explanation they get afterwards.

---

# Part 6 · Where the constraint actually binds

## 6.1 · All nine drives replayed against the trigger

| drive | minutes | peak turbine °C | vs trigger | seconds above |
|---|---|---|---|---|
| `7475b5d7` | 55.1 | **890.6** | **+40.8** | **36** |
| `670063b2` | 7.3 | 780.3 | −69.5 | 0 |
| `cb67b01f` | 21.6 | 728.0 | −121.9 | 0 |
| `3aca2ec1` | 41.7 | 676.1 | −173.7 | 0 |
| `683640a0` | 24.0 | 664.1 | −185.7 | 0 |
| `pull01` | 7.4 | 608.0 | −241.8 | 0 |
| `fb988991` | 14.7 | 607.9 | −242.0 | 0 |
| `3f64372e` | 0.7 | 340.1 | −509.8 | 0 |
| `f51686d7` | — | no estimate | — | — |
| **total** | **172.6** | | | **36 s = 0.351 %** |

**One drive of nine binds, for 36 seconds in 172.6 minutes.** The synthetic climb
reached 812 °C, so **the car's own driving was 78 K hotter than the scenario
written to stress it.** The scenario was the problem, not the trigger.

Note the gap between the top two: 890.6 and 780.3. `7475b5d7` is not a
"close" drive — it is an outlier, 110 K clear of the next.

**0.351 % is itself a result about H/τ** and belongs in the thesis: on this
vehicle, in this driving, the protected component is near its limit a third of
one percent of the time. It is **not** a measurement of the sustained-climb duty
cycle the project targets, because no logged drive is one. Say which you mean.

## 6.2 · The scenario envelope

Neutral policy, 42 °C, 12 minutes:

| grade | km/h | peak turbine °C | vs trigger |
|---|---|---|---|
| 12 % | 90 | 756.0 | −93.8 |
| 12 % | 110 | 812.3 | −37.6 |
| **12 %** | **130** | **899.4** | **+49.5** |
| 12 % | 150 | 942.6 | +92.7 |
| 7 % | 130 | 758.8 | −91.0 |
| 7 % | 150 | 820.4 | −29.5 |
| **16 %** | **110** | **906.2** | **+56.3** |
| 4 % | 150 | 708.5 | −141.4 |

**Three rows bind; the boundary is near 12 % at ~120 km/h.**

`12 % @ 130` and `16 % @ 110` demand **88.7 and 88.5 kW** of road power and reach
**899 and 906 °C** — different grade, different speed, same power, same
temperature. If preview value is a function of H/τ alone, those two should land
together in Phase D: near-identical exhaust flow means near-identical turbine τ.
**That is a free test of the project's own claim.**

**But one row breaks a pure-power reading:** `12 % @ 90` (54.7 kW → 756 °C) is
*hotter* than `4 % @ 150` (60.4 kW → 709 °C). The slower row sits at 2018 rpm
against 2790, so it runs a higher load per cycle and a hotter EGT, and
`ua_gas_turb · ṁ_exh · (EGT − T_turb)` carries both terms. **Not promoted to a
law; the exception is recorded beside it.**

---

# Part 7 · The published towing standard, tried and rejected

`SAE J2807` §4.3.5, Davis Dam — read off the standard's own PDF, not a summary:
Arizona SR 68, **18.3 km (11.4 miles)**, grade **0–7 %** (Figure 2, GPS data
11/2004), minimum **64.4 km/h (40 mph)**, minimum ambient **37.8 °C**, air
conditioning at maximum.

**The web summaries report "11.4" as a percent grade. It is the length in
miles.** Only opening the standard settled it.

| trailer | peak turbine °C | vs trigger | peak torque Nm |
|---|---|---|---|
| none | 432.4 | −417.5 | 140 |
| 1000 kg | 587.0 | −262.9 | 224 |
| **2000 kg** | **756.3** | **−93.5** | **308** |

**Two tonnes behind a 1520 kg sports car and still 94 K short.** Extrapolating
puts the crossing near four tonnes.

**Why it fails is worth more than the failure.** Compare the last row with the
standard climb: 308 Nm → 756 °C against 297 Nm → 812 °C. **Nearly the same
torque, 56 K apart.** J2807 is a truck standard at truck speeds: 40 mph puts the
engine at low speed and low airflow, so a heavily loaded engine grinding slowly
uphill produces a *cool* turbine.

---

# Part 8 · Does a rolling road rescue preview? No.

If preview loses because the road changes **once** — flat for three minutes, then
a constant grade — then 30 s of lookahead buys a single head start in 720 s. Test:
alternate the grade about the same mean at the same speed, sweeping only the
period.

## 8.1 · The first attempt was blind, and that matters more than its output

It alternated **8 % ↔ 16 %**. Both policies normalise grade as
`clip(grade/0.08, 0, 1)` — **8 % gives 1.0 and 16 % gives 1.0 after the clip.**

**The road varied and neither policy could see it.** Every row printed −0.1
points, which looked like a finding and was **zero information**. `AUDIT.md` C3's
lesson one level down: *a test that cannot see cannot measure*, exactly as a test
that cannot fail cannot confirm.

## 8.2 · Re-run at 2 % ↔ 16 % — the policies' own deadband and engine headroom

| road period | baseline | grade-now | predictive | preview edge |
|---|---|---|---|---|
| constant | 1402.0 | 697.3 | 705.7 | −0.6 pts |
| 60 s | 1395.4 | 992.9 | 1025.4 | **−2.3 pts** |
| 120 s | 937.6 | 655.1 | 674.0 | −2.0 pts |
| 240 s | 754.5 | 502.3 | 514.0 | −1.5 pts |
| 480 s | 791.9 | 473.5 | 478.2 | −0.6 pts |

**The faster the road varies, the worse preview does.** The hypothesis is
refuted.

**The mechanism is one line, and it is the policy, not the information.**
`check_premise.p_predictive` takes `max(preview[+15 s], preview[+30 s])`, so on a
road that keeps climbing there is always a steep section in view and it protects
almost continuously — including through the easy sections, where protection costs
and buys nothing. A driver braking for a red light half a kilometre early.

---

# Part 9 · A live visual replay

An HTML page that plays the run back second by second: the road in elevation
profile, three cars at the same position tinted by their own turbine
temperature, live readouts for turbine / damage / rpm / torque / spark / lambda,
and the temperature chart with the 850 °C line and a playhead.

Published privately at
<https://claude.ai/artifact/89VtkFZFzJN3dXxXS6d4cz>. Data dumped from the
simulator, so its numbers match `check_premise.py` exactly.

Built because "preview and current-grade behave almost identically" had been
explained twice in prose without landing. On the page you see it in two seconds:
the blue and violet traces lie on top of each other.

---

# Part 10 · The scenario, locked

`make_grade_climb` defaults: **`v_kmh` 110 → 130**. One number, and it propagates
to `check_premise`, `generality_test`, `test_reward` and `train.py` — no two
places can say different things.

The docstring now carries the envelope table, why 130 and not 110, the other two
binding rows as the team's second and third scenarios, what was tried and
rejected, and a header saying it is **locked and does not move after a result is
seen**.

---

# Part 11 · The gearbox defect — mistake 17

With the scenario locked, **`test_reward.py` failed**: the neutral action — which
by construction reproduces the baseline ECU — scored **−0.124** against a ±0.05
band.

**The script's printed advice was for the wrong failure.** It says *"raise the
tracking coefficient"*, written for *"refusing torque is not punished"* — a check
that passed. Following it would have made this worse.

## 11.1 · Diagnosis

Across the whole climb the **baseline demanded 381 Nm and delivered 359** — short
**5.7 %** on **519 of 519 samples**. `TRACK_TOL` is 5 %, so the hinge fired every
single step. **The baseline itself could not hold the demand**, and no reward
weight fixes a scenario asking for torque the vehicle cannot make.

## 11.2 · Root cause

`Vehicle.gear_for` selected on **road speed alone** — a fixed ladder at
22 / 40 / 62 / 88 / 115 km/h.

| km/h | gear | demand Nm | shortfall |
|---|---|---|---|
| 110 | 5th (0.82) | 297 | 0.0 % |
| **115** | **6th (0.68)** | **364** | **7.8 %** |

**A 4 % step in road speed moved the torque demand 23 %.** That is the ratio
dropping at the 115 km/h rung: **the model upshifted into top gear halfway up a
12 % grade at wide-open throttle**, then asked the engine for the whole hill at
**2137 rpm**. Every automatic downshifts under that load.

## 11.3 · The fix, and the guard that it is a correction

`gear_for` now takes the tractive force and hands back a gear while the required
torque exceeds `SHIFT_LOAD × PEAK_TORQUE_NM` — a **25 % torque reserve**, declared
ASSUMED — unless the lower gear would hit the limiter.

**Every operating point this environment had already been used at keeps its
gear:**

| case | gear before | gear after |
|---|---|---|
| 110 km/h flat cruise | 5th | 5th |
| 110 km/h, 12 % — the old scenario | 5th | 5th |
| 110 km/h, 16 % — scenario #3 | 5th | 5th |
| 90 km/h flat | 5th | 5th |
| 50 km/h town | 2nd | 2nd |
| **130 km/h, 12 %** | 6th | **5th** |
| **150 km/h, 12 %** | 6th | **5th** |

The old scenario is bit-identical. **Had the rule been tuned to make a scenario
bind, it would have moved something else.**

## 11.4 · What it cost, and a known limit

Peak turbine at 130 km/h falls **899.4 → 857.0 °C** — the downshift raises rpm and
lowers load per cycle, so EGT drops. The scenario still binds, by **7 K instead of
49**, and protection still does real work: current-grade cuts damage **29.7 %**.
The gate passes at **+0.00048**.

**The starver's margin narrowed from −2.16 to −0.10**, because an engine that
meets its demand easily makes refusing to work a smaller crime. **That is the
first number to watch if a trained agent turns lazy.**

**Known limit, not tuned away:** 500 Nm is peak torque, not torque at every rpm,
so the ceiling is flat on an rpm-dependent quantity. **115–125 km/h still
over-ask** at 364–375 Nm, under the ceiling, while the engine cannot deliver that
at 2137 rpm. The ceiling was not lowered to smooth the table, because that would
have moved `16 % @ 110`, the team's third scenario. The right fix is an
rpm-dependent torque limit — a larger change.

**Third defect in this project invisible until the load became real**, after the
wrong engine (mistake 1) and the reward hack (mistake 5). Same shape every time.

---

# Part 12 · Phase C ran — the project trained something for the first time

Until this session `train.py` had **never executed past its import guard**. It
has now run twice, to completion:

```bash
python train.py --steps 50000 --seed 0                # sighted
python train.py --steps 50000 --seed 0 --no-preview    # blinded
```

**63 minutes each.** Identical in every respect except one: with `--no-preview`,
`env._preview()` returns zeros instead of the grade at +2 / +5 / +15 / +30 s, so
four of the twenty-three observation slots carry no road ahead.

What the run reported at the end, sighted:

```
ep_len_mean     4.5e+03        actor_loss     -13.7
episodes        8              critic_loss     0.0109
fps             13             ent_coef        0.0069
total_timesteps 35992          n_updates       35891
```

Nothing diverged: the critic loss is small and stable, the entropy coefficient
annealed on its own from SAC's automatic tuning, and every step produced a finite
reward. **Five checkpoints per run** landed at 10k / 20k / 30k / 40k / 50k, so a
closed laptop costs minutes rather than the run — which is the fix `AUDIT.md` H6
asked for and it is now exercised rather than assumed.

**`fps 13` is the number to plan with, not the 19.2 of Part 4.** That probe ran
2000 steps on an otherwise idle machine; a full run alongside anything else gives
13. **Eight remaining runs at 63 min ≈ 8.4 hours.**

## 12.1 · THE TRAINING CURVES POINT THE WRONG WAY — read this before trusting one

Both runs, episode returns in order:

| | ep 0–4 | ep 5–10 | first 5 | last 5 |
|---|---|---|---|---|
| **sighted** | −177.2 · −439.1 · −506.4 · −100.8 · **+643.6** | −191.5 · −97.3 · +277.4 · +297.7 · −52.5 · +93.3 | −115.99 | **+103.71** |
| **blinded** | −179.8 · −457.7 · −403.8 · −177.7 · **+610.2** | −122.8 · −26.0 · +353.9 · +353.1 · +87.8 · +189.8 | −121.76 | **+191.71** |

`train.py` prints "the curve improved" for both. **And by that measure the
BLINDED agent looks nearly twice as good — +191.71 against +103.71.**

**The evaluation says the opposite**: sighted 194.7 damage against blinded 261.4,
a **+11.7 point** advantage the other way.

So the training curve does not merely fail to prove learning — **on this pair it
actively inverts the ranking.** Two reasons, both structural:

- **`reset()` redraws the preference vector every episode**, so each row is scored
  with a different ruler. Eleven rows spanning **−506.4 to +643.6**, with the
  single best episode of each run sitting in the FIRST five, is the weight draw.
- **A blinded agent sees four fewer live inputs**, so its observation is less
  varied and its returns cluster differently. That is a property of the input,
  not of the policy's quality.

**This is the concrete argument for the protocol**, and it is better than the
abstract one: if the team had read the curves and stopped, the conclusion would
have been *"preview makes it worse"* — the exact opposite of what twenty fixed
episodes show.

## 12.2 · Why `evaluate.py` had to exist first

**Training-curve returns are not comparable to each other.** `reset()` redraws the
preference vector every episode, so each row is scored with a different ruler.
Seed 0 sighted:

```
ep 0  -177.2      ep 4  +643.6      ep 8  +297.7
ep 1  -439.1      ep 5  -191.5      ep 9   -52.5
ep 2  -506.4      ep 6   -97.3      ep 10  +93.3
ep 3  -100.8      ep 7  +277.4
```

Range **−506.4 to +643.6** over eleven episodes, **with the single best episode
in the FIRST five**. `train.py` summarises this as *"first 5 −115.99 → last 5
+103.71, the curve improved"*. **That is the weight draw, not learning.**

So: **twenty frozen episodes**, `(seed, weights)` written as literals, pinned
after `reset()`, identical for every policy. A difference between two rows is
then a difference between the **policies**.

## 12.3 · The table

| policy | damage med | IQR | worst | fuel med | peak °C |
|---|---|---|---|---|---|
| baseline ECU | 572.8 | 0.0 | 572.8 | 4528 | 857 |
| reactive | 540.9 | 0.0 | 540.9 | 4552 | 852 |
| current-grade | 402.6 | 0.0 | 402.6 | 4796 | 834 |
| **agent, sighted** | **194.7** | 35.6 | 378.8 | 5337 | 835 |
| **agent, blinded** | **261.4** | 19.9 | 336.9 | 5008 | 825 |

```
agent over current-grade:  +36.3 points
SIGHTED over BLINDED:      +11.7 points     (66.0 % against 54.4 %)
```

## 12.4 · Five limits on the +11.7

1. **n = 1 against n = 1.** The protocol wants five seeds each.
2. **The worst episode reverses it:** blinded **336.9** against sighted **378.8**.
3. **The sighted agent burns 6.6 % more fuel:** 5337 against 5008 g.
4. **The sighted agent is more variable:** IQR 35.6 against 19.9.
5. **The twenty episodes vary the preference weights only** — not road, not
   ambient. That is why every hand-written policy shows IQR 0.0: for them it is
   the same episode twenty times. **The protocol compares policies; it does not
   test robustness.**

## 12.5 · This reverses the hand-written result, and that is the finding

Earlier the same day, preview lost on **five scenarios** with hand-written
policies, between −0.1 and −2.3 points. With trained agents it **wins by 11.7**.

`AUDIT.md` C3 argued hand-written policies cannot settle this question. **It is
now measured: the two verdicts differ by 12 points.**

---

# Part 13 · Exactly what changed in the repository

Ten commits. `git diff 5ef1aa2..HEAD --stat` → **19 files, ~1600 insertions**.

## Code — 361 lines added, 38 removed

| file | what |
|---|---|
| **`engine_env.py`** | `gear_for(v_mps)` → `gear_for(v_mps, force_n=None)`, the load-aware downshift. New `PEAK_TORQUE_NM = 500.0`, `SHIFT_LOAD = 0.75`, `SHIFT_RPM_MAX = 6000.0`. `demand()` computes tractive force first. `make_grade_climb(..., v_kmh=110.0)` → **`130.0`**. |
| **`evaluate.py`** | **NEW, 193 lines.** `EPISODES` (twenty literals), `run_episode()` pins the weights, `main()` scores the hand-written policies plus any SAC models passed as arguments, prints median / IQR / worst. |
| **`train.py`** | `STEPS_PER_S 3.0 → 19.2` — printed estimate only. Docstring carries the measured thread table. |
| **`verify_docs.py`** | One `RETIRED` pattern: `King Abdul[aA]ziz`. |

**Nothing in `plant.py` or `thermal.py` moved**, so `validate.py` and the
validation table are untouched — the 8-of-11 row is unchanged.

## New directories

| path | what |
|---|---|
| **`team/`** | `README.md`, `_TEMPLATE.md`, `jad.md`, `ghassan.md`. |
| **`results/`** | `runs/` is gitignored, so: `phase_d_seed0.txt` (the table as printed) and two `curve_*.csv`, with a README on why the curves prove nothing. |

## Documents

`CLAUDE.md` +350 — mistake 17, the towing rejection, the rolling sweep, the
envelope, the `VOID` heading. `CHECKPOINT.md` +180 — two dated session entries.
`README.md`, `handoff.md`, `presentation/README.md` — the six-figure sweep.

## The commits, newest first

```
95cbda7  docs: list exactly what changed in the repo, in Ghassan's brief
67e9c17  docs: session brief for Ghassan, and a stub profile for him
a68715f  phase D: the evaluation protocol, and the first measured preview advantage
1df41a2  env: the gearbox upshifted mid-climb, and the scenario is now locked
5923e29  docs: a rolling road makes preview WORSE, and why Phase D is the only route
9f41082  docs: the published towing standard does not bind, and what does
517fc53  team: one profile per person, matched by git config user.email
b087a45  docs: CHECKPOINT entry for the 17 September session
6fff693  docs: the training-time figure was wrong by 6.4x
12a4de8  docs: sweep the documents behind the audit fixes, and guard the university
```

**Every commit message carries the command output that justifies it.** If a
figure here disagrees with a script, the script is right.

**If you read one diff:** `git show 1df41a2 -- engine_env.py` — the gearbox fix
and the locked scenario, the session's only change to what the simulator does.

---

# Part 14 · Four things that were wrong on the first attempt

Recorded because the project's own standard is to report against itself.

1. **"The axis to move is road speed, not grade."** Written into `CLAUDE.md` after
   the J2807 result, refuted by the next sweep within the hour: `16 % @ 110`
   binds with no extra speed at all. Both axes work. Corrected in place, with the
   correction named.
2. **The blind rolling sweep** (Part 8.1). Five rows of −0.1 that looked like a
   finding and were zero information.
3. **"36 s of that 42-minute drive."** `7475b5d7` is **55.1 minutes**. The figure
   came from memory instead of `data/manifest.csv`, and went into three documents
   before being caught. The 42-minute drive is `3aca2ec1`.
4. **The first version of this report assumed its reader did not know the
   project.** Ghassan is on the team. Rewritten.

A fifth, of a different kind: `git checkout handoff.md` — used to clean up after
planting the university test string — **discarded uncommitted edits to that same
file**. They were redone. Do not use `git checkout <file>` as an undo while you
have unsaved work in it.

---

# Part 15 · What did not change

- **Phase D is not done.** Eight runs remain: seeds 1–4, sighted and blinded,
  **63 min each, ~8.4 hours**.
- **Phase E has not started.** `battery.py` does not exist, and **with one plant
  the H/τ claim cannot be tested at all** — you get a curve, never an overlap.
- **The knock model is still not validated against this car:** correlation
  **−0.149** over 13 592 paired samples between the model's knock integral and
  the retard the vehicle publishes.
- **`c_turb` = 6000 J/K is still ASSUMED**, and it sets τ.
- **Charge temperature is still not measured**, and both logged pressure channels
  are still pre-throttle, so there is still no part-load test of
  `volumetric_efficiency()`.

---

# Part 16 · Next, and what is locked

```bash
python train.py --steps 50000 --seed <n>
python train.py --steps 50000 --seed <n> --no-preview
python evaluate.py runs/sighted_seed<n> runs/blind_seed<n>
```

Seeds 1–4 both ways, then median and IQR across the five. **That is the number
that goes in the thesis.**

**Locked and not to be changed:** the scenario at 12 % / 130 km/h, and the twenty
episodes in `evaluate.EPISODES`. Changing the test set after seeing a result is
the one mistake this project cannot recover from.

---

# Part 17 · Open questions, for Ghassan in particular

1. **The gear rule.** A flat torque ceiling on an rpm-dependent quantity is
   wrong. What is the right shape, and is a 25 % reserve sensible for this box?
2. **The row that breaks the power reading** — `12 % @ 90` hotter than
   `4 % @ 150` on less power. Is the rpm / load-per-cycle explanation enough?
3. **The 115–125 km/h band** is still over-asked, deliberately not tuned away.
4. **The twenty episodes:** weights only, or should ambient and grade vary too?
   Adding them would make the protocol test robustness as well as ranking — but
   it is a change to a locked artefact, so it needs deciding before seed 1 runs,
   not after.

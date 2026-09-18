# 18–19 September 2026 — what changed, and what needs a second pair of eyes

**Written for Ghassan Alrefaei (2340394, `badcloor`)** — you know the project and
you know engines, so there is no H/τ primer here, no tour of the phases, and no
explanation of the cycle model. This is what moved, the numbers that moved it,
and the four places I want you to argue with me.

**Two lines:** the evaluation scenario changed to **12 % at 130 km/h** and is now
locked. Getting it there exposed **a defect in the gearbox model**. With that
fixed, the first two agents in this project's history were trained, and the first
proper ablation ran: **sighted beats blinded by +11.7 points**. One seed against
one seed, so do not quote it yet.

---

## 1 · Why the scenario had to move at all

`AUDIT.md` C2: `BaselineECU` was scheduled on `_map_for(...)`, an open-loop guess
of **224 kPa** while the tracking loop settled at **175**. It commanded
knock-limited spark for a phantom load and carried roughly ten degrees of retard
the engine never called for.

**Fixing C2 took the heat out with the bug.** Peak turbine housing on
`12 % @ 110 km/h` fell to **812 °C** against an **850 °C** trigger. The constraint
stopped binding, so a protecting policy and a do-nothing policy scored the same —
and that was the wall in front of Phase D.

**Worth internalising:** the "879 °C turbine" the documents quoted for weeks was
never the engine. It was a scheduling error.

---

## 2 · The envelope was measured before a row was picked

Neutral policy, 42 °C ambient, 12 minutes:

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

**Three rows bind; the boundary sits near 12 % at ~120 km/h.**

### One physical observation I want checked

`12 % @ 130` and `16 % @ 110` demand **88.7 and 88.5 kW** of road power and reach
**899 and 906 °C**. Completely different grade and speed, same power, same
temperature. If preview value really is a function of H/τ alone, those two should
also land together in Phase D — near-identical exhaust flow means near-identical
turbine τ. That is a free test of the project's own claim.

**But one row breaks a pure-power law:** `12 % @ 90` (54.7 kW → **756 °C**) is
*hotter* than `4 % @ 150` (60.4 kW → **709 °C**). Less power, more heat.

My reading: 2018 rpm against 2790. The slower row runs a higher load per cycle
and so a hotter EGT, and `ua_gas_turb · ṁ_exh · (EGT − T_turb)` carries both
terms, not flow alone. **It was not promoted to a law, and the exception is
recorded beside it.** If you read it differently, say so.

### The published towing standard was tried and rejected by measurement

`SAE J2807` §4.3.5, Davis Dam: 18.3 km, grade **0–7 %**, minimum **64.4 km/h**,
minimum ambient **37.8 °C**. Figures read off the standard's own PDF, not a
summary — and the web summaries report "11.4" as a *percent grade* when it is the
**length in miles**.

| trailer | peak turbine °C | vs trigger |
|---|---|---|
| none | 432.4 | −417.5 |
| 1000 kg | 587.0 | −262.9 |
| **2000 kg** | **756.3** | **−93.5** |

**Two tonnes behind a 1520 kg car and still 94 K short.** 64 km/h is a truck
speed: low rpm, low airflow, so a modest road power however much torque the
trailer adds.

---

## 3 · The defect — this section is why you are getting this file

Scenario locked, then **`test_reward.py` failed**: the neutral action scored
**−0.124** against a ±0.05 band.

**And the script's printed advice was for the wrong failure.** It says "raise the
tracking coefficient", which is written for *"refusing torque is not punished"* —
a check that passed. Following it would have made this worse.

### Diagnosis, on the shipped trace

Across the whole climb the **baseline demanded 381 Nm and delivered 359** — short
**5.7 %** on **519 of 519 samples**. `TRACK_TOL` is 5 %, so the hinge fired every
single step.

**The baseline itself could not hold the demand.** No reward weight fixes a
scenario asking for torque the vehicle cannot make.

### Root cause

`Vehicle.gear_for` selected on road speed alone — a fixed ladder at
22 / 40 / 62 / 88 / 115 km/h.

| km/h | gear | demand Nm | shortfall |
|---|---|---|---|
| 110 | 5th (0.82) | 297 | 0.0 % |
| **115** | **6th (0.68)** | **364** | **7.8 %** |

**A 4 % step in road speed moved the torque demand 23 %.**

In your terms: **the model upshifted into top gear halfway up a 12 % grade at
wide-open throttle**, then asked the engine for the whole hill at **2137 rpm**.
Every automatic downshifts under that load.

### The fix, and the guard that it is a correction and not a convenience

`gear_for` now takes the tractive force and hands back a gear while the required
torque exceeds `SHIFT_LOAD × PEAK_TORQUE_NM` — a **25 % torque reserve** — unless
the lower gear would hit the limiter.

**Every operating point this environment had already been used at keeps its
gear:** 110 flat, 110 at 12 %, 110 at 16 %, 90 flat, 50 km/h town. The old
scenario is bit-identical. Only 130 and 150 km/h on 12 % downshift:
**381 → 316 Nm at 2913 rpm**.

### What it cost

Peak turbine at 130 km/h falls **899.4 → 857.0 °C**. The scenario still binds, by
**7 K instead of 49**. And the starver's margin in `test_reward` narrowed from
**−2.16 to −0.10** — an engine that meets its demand easily makes refusing to
work a smaller crime. **That is the first number to watch if a trained agent
turns lazy.**

### The known limit in my fix — your second review point

**500 Nm is peak torque, not torque at every rpm**, so the ceiling is flat on an
rpm-dependent quantity. Consequence: **115–125 km/h still over-ask** at
364–375 Nm, under the ceiling, while the engine cannot deliver that at 2137 rpm.

The ceiling was **not** lowered to smooth the table, because lowering it would
have moved `16 % @ 110`, the team's third scenario. **The right fix is an
rpm-dependent torque limit**, which is a larger change. I want your view on the
shape of it.

---

## 4 · Phase C ran, and Phase D has a protocol

`train.py` got past its import guard **for the first time**: 50 000 steps, seed 0,
sighted and blinded, **63 minutes each** — not the 45 a 2000-step probe predicted.
Quote 63.

### `evaluate.py` is new, and the reason matters

**Training-curve returns are not comparable to each other.** `reset()` redraws the
preference vector every episode, so each row is scored with a different ruler.
Seed 0 sighted ranged **−506.4 to +643.6** over eleven episodes, **with its single
best episode in the FIRST five**, and `train.py` summarises that as "the curve
improved". That is the weight draw, not learning.

So: **twenty frozen episodes**, weights written as literals and pinned after
`reset()`, identical for every policy. A difference between two rows is then a
difference between the **policies**.

| policy | damage med | IQR | worst | fuel med | peak °C |
|---|---|---|---|---|---|
| baseline ECU | 572.8 | 0.0 | 572.8 | 4528 | 857 |
| reactive | 540.9 | 0.0 | 540.9 | 4552 | 852 |
| current-grade | 402.6 | 0.0 | 402.6 | 4796 | 834 |
| **agent, sighted** | **194.7** | 35.6 | 378.8 | 5337 | 835 |
| **agent, blinded** | **261.4** | 19.9 | 336.9 | 5008 | 825 |

```
SIGHTED over BLINDED:  +11.7 points     (66.0 % against 54.4 %)
```

---

## 5 · Why this reverses what was measured hours earlier

Earlier the same day, before any training, preview was measured with the
**hand-written policies** across five scenarios — constant grade and four rolling
periods. **It lost in every one**, between −0.1 and −2.3 points.

One line explains it, in `check_premise.p_predictive`:

```python
ahead = max(env._preview()[2], env._preview()[3])
```

On a road that keeps climbing there is always a steep section in view, so the
policy protects **continuously**, including through the easy sections where
protection costs and buys nothing. A driver braking for a red light half a
kilometre early.

**`AUDIT.md` C3 argued hand-written policies cannot settle this question. It is
now measured: the two verdicts differ by 12 points.**

**One slip of mine worth recording.** The first rolling sweep I wrote alternated
**8 % ↔ 16 %**, and both policies normalise grade as `clip(grade/0.08, 0, 1)` —
8 % gives 1.0 and 16 % gives 1.0 after the clip. **The road varied and neither
policy could see it.** It printed −0.1 five times, which looked like a finding and
was zero information. Re-run at 2 % ↔ 16 % — the policies' own deadband and engine
headroom.

---

## 6 · Five limits on the +11.7

1. **n = 1 against n = 1.** The protocol wants five seeds each.
2. **The worst episode reverses it:** blinded **336.9** against sighted **378.8**.
3. **The sighted agent burns 6.6 % more fuel:** 5337 against 5008 g.
4. **The sighted agent is more variable:** IQR 35.6 against 19.9.
5. **The twenty episodes vary the preference weights only** — not the road, not
   the ambient. That is why every hand-written policy shows IQR 0.0: for them it
   is the same episode twenty times. **The protocol compares policies; it does
   not test robustness.**

---

## 7 · What did not change, and still applies to every figure above

- **The knock model is not validated against this car.** Correlation between the
  model's knock integral and the retard the vehicle publishes: **−0.149** over
  13 592 paired samples.
- **`c_turb` = 6000 J/K is ASSUMED**, and it sets τ.
- **Charge temperature is not measured** — the channel named "before throttle
  valve" is a compressor outlet; the B58's cooler sits inside the manifold.
- **Both logged pressure channels are pre-throttle**, so there is no part-load
  test of `volumetric_efficiency()` at all.
- **Phase E has not started.** `battery.py` does not exist, and with one plant the
  H/τ claim cannot be tested — you get a curve, never an overlap.

---

## 8 · Next

Eight runs: seeds 1–4, sighted and blinded. **63 min each, ~8.4 hours total.**

```bash
python train.py --steps 50000 --seed <n>
python train.py --steps 50000 --seed <n> --no-preview
python evaluate.py runs/sighted_seed<n> runs/blind_seed<n>
```

Then median and IQR across the five seeds. **That is the number that goes in the
thesis.**

**Locked, and not to be changed:** the scenario at 12 % / 130 km/h, and the twenty
episodes in `evaluate.EPISODES`.

---

## 9 · Exactly what changed in the repository

Nine commits, all on **`JMF-2340550-sep17`**. `JMF-new-plan` and `main` were not
touched. Diff base is `5ef1aa2`, the merge that brought the two branches
together — so `git diff 5ef1aa2..HEAD` is this session and nothing else.

### Code — 361 lines added, 38 removed, four files

| file | what |
|---|---|
| **`engine_env.py`** | `Vehicle.gear_for(v_mps)` → `gear_for(v_mps, force_n=None)`: the load-aware downshift. New constants `PEAK_TORQUE_NM = 500.0`, `SHIFT_LOAD = 0.75`, `SHIFT_RPM_MAX = 6000.0`. `demand()` now computes tractive force first and passes it in. And `make_grade_climb(..., v_kmh=110.0)` → **`v_kmh=130.0`**, the locked scenario, with the envelope table in its docstring. |
| **`evaluate.py`** | **NEW, 193 lines.** Phase D's protocol. `EPISODES` is twenty `(seed, weights)` literals; `run_episode()` pins the weights after `reset()`; `main()` scores the three hand-written policies plus any SAC models passed as arguments and prints median / IQR / worst. |
| **`train.py`** | `STEPS_PER_S 3.0 → 19.2`, printed-estimate only, nothing about training behaviour. Docstring carries the measured table — 19.19 steps/s at one thread, 18.14 at six, so thread count does not matter and SAC's gradient updates cost ~2 %, not the 6.5× the old figure implied. |
| **`verify_docs.py`** | One `RETIRED` pattern added: `King Abdul[aA]ziz`. CLAUDE.md line 13 carried the wrong university until `d57f3da`, inside a commit about REFERENCES.md, so the change is invisible from the log. Guard verified by planting the string and watching the run fail. |

**Nothing in `plant.py` or `thermal.py` moved**, so `validate.py` and the
validation table are untouched — the 8-of-11 row is the same as before this
session.

### New directories

| path | what |
|---|---|
| **`team/`** | One profile per person, matched by `git config user.email`. `README.md` explains it, `_TEMPLATE.md` is what you copy, `jad.md` and `ghassan.md` exist — **yours is a stub with almost everything marked "unrecorded"**, because guessing someone's background steers every explanation they get afterwards. `CLAUDE.md` now opens by telling the assistant to read it first. |
| **`results/`** | `runs/` is gitignored, so the evidence lives here: `phase_d_seed0.txt` is the evaluation table exactly as printed, and the two `curve_*.csv` are the learning curves — with a README saying why the curves prove nothing. |

### Documents

`CLAUDE.md` (+350 lines) gains **mistake 17**, the towing-standard rejection, the
rolling-road sweep, the scenario envelope, and a `VOID` heading over the old
preview figures that were still reading as a live claim near the top of the file.
`CHECKPOINT.md` (+180) gains two dated session entries. `README.md`, `handoff.md`
and `presentation/README.md` were swept for six stale figures the 16 September
audit fixes had left behind — `256.5 → 294.2`, `801 → 812 °C`, `2.2 → 1.8`
points, `46 of 46 → 49 of 49`, peak `884.9 → 890.6 °C`, and the line claiming the
app's six audit findings were unfixed when all six are.

### The commits, newest first

```
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
figure here disagrees with a script, the script is right — run it.

### If you only read one diff

```bash
git show 1df41a2 -- engine_env.py
```

That is the gearbox fix and the locked scenario, and it is the only change in
this session that alters what the simulator does.

---

## 10 · What I want from you specifically

1. **The gear rule.** A flat ceiling on an rpm-dependent quantity is wrong. What
   is the right shape, and is a 25 % torque reserve sensible for a box like this?
2. **The row that breaks the power law** — `12 % @ 90` hotter than `4 % @ 150`.
   Is the rpm/load-per-cycle reading enough, or is something else going on?
3. **The 115–125 km/h band** is still over-asked and deliberately not tuned away.
4. **The twenty episodes:** weights only, or should ambient and grade vary too?

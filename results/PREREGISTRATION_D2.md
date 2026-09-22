# PREREGISTRATION — Phase D2, the preview ablation on a randomised climb

**Written 22 September 2026, BEFORE any Phase D2 agent was trained.** Committed
before seed 0 of either arm started. That ordering is the whole point of this
file, exactly as it was for `PREREGISTRATION.md`: a hypothesis declared after
the numbers are in is a description.

> **Status: complete. No line in this file is open.** Unlike Phase D, the
> minimum effect of interest is set here, before the first run — which is what
> lets this experiment's null, if it is one, be classified rather than merely
> reported.

---

## 1. The question

The same question as Phase D, on a road the blind agent cannot memorise:

**Does an agent that can see the road ahead protect the turbine better than an
identically trained agent that cannot?**

This file preregisters the PREVIEW question only. Whether learned supervision
beats the `current-grade` comparator is a different and easier question, and a
yes to it is not evidence for preview (`AUDIT.md` C3).

## 2. Why a second experiment

Phase D returned a null — 5 of 8 seeds positive, sign p = 0.3633 — and then
`PREREGISTRATION.md` limit 7 found that **its blinded arm was not blind.** The
road was the same hill at the same second in every episode, and the blind
agent's thermal state is a clock, so it could learn when the hill comes with no
preview channel at all. Four explanations for the null were live:

| | explanation | does Phase D2 address it? |
|---|---|---|
| (i) | preview genuinely buys little at this configuration | this is what D2 tests |
| (ii) | the agents are undertrained — C1, 11 episodes | **no** — same budget, on purpose |
| (iii) | the preview carries almost nothing: one step in 900 s | partly — each episode is a different step |
| (iv) | the blinded arm is not blind | **yes — removed by design, and checked** |

**Phase D2 removes (iv) and changes nothing else it can avoid changing.** Same
plant, same budget, same seeds, same twenty preference vectors, same statistic.
The one difference is the road.

- If the arms **separate**, the fixed road was hiding the effect.
- If they **still do not**, (iv) is ruled out as the explanation; (i) and (ii)
  remain, and the next experiment is the training budget (C4) — with its own
  preregistration.

## 3. The plant, pinned

Every run carries a `meta.json` fingerprint and `evaluate.py` refuses a model
whose plant differs. D2's fingerprint differs from Phase D's in exactly two
fatal fields — `scenario` and `episodes_sha` — so a Phase D agent cannot be
scored under this protocol, nor a D2 agent under Phase D's.

| field | value |
|---|---|
| gearbox | ZF 8HP51, ratios 5.250 3.360 2.172 1.720 1.316 1.000 0.822 0.640 |
| final drive | 3.150 |
| crank-angle step | `plant.DTHETA_DEG` = 0.25° |
| protection trigger | `TURB_PROTECT_K` = 1123 K (850 °C) |
| `plant_sha` | **`b5a3069f32a83754` — identical to Phase D.** `engine_env.py` is untouched; the road is a wrapper (`random_road.py`) |
| **scenario** | **climb start uniform on [120, 300] s, grade uniform on [12, 16] %, drawn per episode.** 130 km/h, 42 °C ambient |
| road code | `random_road.py`, `road_sha` **`1a29dc46db24f233`** (its code, docstrings excluded) |
| training episode | 900 s at dt 0.2, a fresh road every episode, seeded from `--seed` |
| evaluation | 720 s at dt 1.0, the twenty frozen episodes `evaluate.EPISODES_D2`, hash **`1c5d49852290d27c`** |

**Why a wrapper and not an edit.** `fingerprint.py` hashes the code of
`engine_env.py`. Adding even a harmless `start_s` keyword there would have moved
`plant_sha` and made `evaluate.py` refuse all sixteen Phase D agents — the first
experiment's evidence. Checked after the change: all 16 Phase D `meta.json`
files still match the Phase D protocol, and 0 of 16 match D2's.

## 4. The design

| | |
|---|---|
| arms | **sighted** (`train.py --road random --seed N`) and **blinded** (`--road random --no-preview`) |
| seeds | **0 … 7** — eight per arm, sixteen runs |
| steps | **50 000 per run — the C1 budget**, as Phase D |
| pairing | by seed: sighted seed *k* against blinded seed *k* |
| training roads | iid from the two ranges, a new road every episode, stream seeded by `--seed` |
| test set | **`evaluate.EPISODES_D2` — frozen, hash `1c5d49852290d27c`. It does not change.** |

### The test set

Twenty episodes, each `(episode seed, weights, start, grade)`:

- **The seeds and weights are Phase D's twenty, unchanged.** Episode *k* of D2
  differs from episode *k* of Phase D in the road and nothing else, so a
  difference between the two experiments cannot be a difference in the
  preference draw.
- **The roads are a Latin hypercube** over [120, 300] s × [12, 16] %, drawn once
  from `numpy.default_rng(20260922)` by `random_road.frozen_episodes()`. Each
  range is cut into twenty strata and each stratum used once, so the set covers
  both ranges evenly — marginally still uniform, the preregistered distribution.
  Twenty iid draws could have skipped the gearbox notch or piled into it. Two
  frozen episodes sit just past the shift (13.988 % and 14.029 %) and carry the
  thinnest margins of the twenty, +12.5 and +13.3 K. The notch's deepest point,
  13.73 % at +6.9 K, falls between strata and no frozen episode lands on it.
  `python random_road.py` regenerates the set from its seed and checks it
  against the literal.

### Why eight seeds and C1, knowing the power

Decided by the team on 22 September 2026 **after** being shown section 5a. The
design removes limit 7's confound whatever its power, it fits in one session,
and C4 is the next experiment either way. Stated here so the low power is a
declared limit rather than a discovered excuse.

## 5. The statistic — Phase D's, unchanged, plus the MEI

- **Primary outcome:** per-seed **median damage** over the twenty frozen D2
  episodes, as `evaluate.py --protocol d2` reports it.
- **Comparison:** paired by seed, `damage_blind[k] − damage_sighted[k]`;
  positive means preview helped.
- **Test:** exact one-sided sign test on the eight paired differences, with an
  exact paired permutation test beside it as a sensitivity check. If they
  disagree, **both are reported** and neither is chosen after the fact.
- **α = 0.05, one-sided.** A significant result in the other direction is
  reported as preview costing damage, never converted into a two-sided win.
- **Minimum effect of interest: 50 damage units.** Set by the team (Jad),
  22 September 2026, **before any D2 agent was trained.** About 5 % of baseline
  damage (959.8 on Phase D's episodes), four times the largest known
  measurement artefact (the dt effect, 12.5 units), about 15 % of what
  supervision alone buys (326.6). It also agrees with the audit's own
  suggestion, made independently on 20 September: `AUDIT2.md` Part 5 point 4
  proposed "at least 5 points" relative to the baseline, and 5 points on
  Phase D's baseline is 48 units.

### The classification rule, fixed now

With an MEI a result falls into exactly one of three cells. The rule is
implemented in `analyse_phase_d2.py`, committed with this file:

| cell | condition |
|---|---|
| **PREVIEW HELPS** | the primary sign test rejects "no effect" at α 0.05. Report the effect size and whether its mean reaches 50 — a significant effect below the MEI is real but, by the team's own threshold, not worth acquiring preview for |
| **SMALLER THAN THE MEI** | the primary test does not reject, **and** the exact one-sided sign test on (50 − difference) rejects "the effect is at least 50". A positive finding about preview |
| **INCONCLUSIVE** | neither rejects. The experiment cannot tell "no effect" from "an effect the team would care about" |

The permutation test runs on the same shifted differences as a sensitivity
check; a disagreement is reported, not resolved.

## 5a. Power — declared before the run, from `power_analysis.py`

`python power_analysis.py` works from Phase D's measured spread, since no D2
spread exists yet:

| | |
|---|---|
| Phase D paired differences | sd **214.4** about a mean of **+4.8** |
| the sign test at 8 seeds | needs **7 of 8** to agree |
| power against the MEI (50) at 8 seeds | **0.10** |
| effect with 80 % power at 8 seeds | **~269 damage units** — 28 % of baseline damage |
| seeds needed for 80 % power against 50 | **186 per arm** |

**The expected cell is therefore INCONCLUSIVE**, unless the randomised road
changes the seed-to-seed spread a great deal or the effect is very large. The
spread is training variance between seeds; each seed is already a median over
twenty episodes, so evaluation episodes do not shrink it, and randomising the
climb is not expected to either. `analyse_phase_d2.py` prints D2's own spread
beside Phase D's so this prediction can be checked rather than assumed.

**This experiment is run anyway, and knowingly.** Its purpose is to remove
explanation (iv), which it does at any power: if the arms separate despite 10 %
power, the effect is large; if they do not, the design flaw is no longer a
candidate and the question moves to the budget.

## 6. Everything reported, whatever it says

As `PREREGISTRATION.md` section 6, without exception:

- All sixteen runs are reported, including any that fail to learn. A run is
  **not** dropped for a poor curve.
- A crashed run is re-run **with the same seed**, and the crash is recorded in
  section 6a below. It is not replaced by a different seed.
- Median, interquartile range **and worst episode** are reported for every arm.
- The `current-grade` comparator is reported beside both arms.
- **Both experiments are reported side by side.** `analyse_phase_d2.py` prints
  Phase D's table and classification beside D2's on every run — Phase D's
  labelled post-hoc, because its MEI was set after its result.

## 6a. Run log — failures and re-runs

*(Empty at commit. Filled if any run fails, as section 6 requires.)*

## 7. Stopping rule

Sixteen runs, then stop. **No seed is added after any result is seen.** More
seeds, or the C4 budget, is a third experiment with its own preregistration,
and all three get reported.

## 8. Known limits that apply to whatever comes out

Declared now so none of them can be discovered later as an excuse.

1. **Underpowered by design** — section 5a. The single most important limit on
   a null from this experiment.
2. **C1 budget** — 50 000 steps, 11 training episodes (`PREREGISTRATION.md`
   limit 6). A null says *"with agents trained to the C1 budget"*, never
   *"preview does not help"*. On a randomised road the task is harder than
   Phase D's — the agent must generalise across roads rather than learn one —
   so eleven episodes buy less here, not more.
3. **The blind agent is blind to the road AHEAD, not to everything.** Once on
   the climb it sees the current grade (observation 13) — the signal the
   `current-grade` comparator uses, which a real car gets from an
   accelerometer. And it can learn the **distribution**: every climb comes
   between 120 and 300 s and is 12–16 % steep, so a blind policy can hedge —
   protect early, just in case. That is a prior, not a preview; a real driver
   has one too. It means "blind" is "no foresight of THIS road", which is what
   the ablation is about.
4. **Grade is not a hotter knob.** The peak is a sawtooth in grade because the
   gearbox hands back a gear near 14 % (`NEXT_EXPERIMENT_DESIGN.md`). The paired
   design hits both arms equally, so the difference is unbiased — but no figure
   may be binned by grade and read as a trend.
5. **Severity is not realistic, and cannot be.** 12–16 % at 130 km/h is steeper
   than any road this project has driven. The Taif mountain drive peaks 52 K
   below the trigger; the car's own driving is above it 0.206 % of the time.
   On this car realistic severity and a binding constraint are mutually
   exclusive. D2 is realistic in **variability** — when and how steep — not in
   severity.
6. **dt mismatch** — trained at 0.2, scored at 1.0, as Phase D
   (`PREREGISTRATION.md` limit 1). Shared by both arms; symmetry unmeasured.
7. **The baseline never enriches on the 12 % climb** (it sits at 2706 rpm;
   `base_lambda` returns 1.000 there). **At other grades in 12–16 % this is
   unmeasured.** Both arms hold the enrichment lever, so the ablation is
   unaffected; "cuts N % versus baseline" figures may be inflated by it.
8. **The knock model is not validated against this car** (correlation −0.149
   with the car's own retard), and **`c_turb` = 6000 J/K is assumed** — both as
   Phase D limits 3 and 4.
9. **Do not rescue a null with H/τ** (`PREREGISTRATION.md` limit 8). On a
   randomised road τ varies per episode with the grade's exhaust flow, so D2
   does not sit at one H/τ at all.
10. **The reward barely punishes torque refusal on the steepest roads.** At
    16 % the torque-starver scores −0.025 to −0.039 against neutral's +0.0006,
    clearing the gate by 0.006 (section 10). An agent could learn to cut boost
    on steep climbs at little cost. That is not automatically a hack — if the
    torque is still delivered, cutting boost is legitimate protection — but it
    is the lever a lazy policy would pull. **Both arms face the same reward**,
    so it does not bias the ablation; it can move every "cuts N %" figure.
    Inspect the agents' torque-violation and fuel columns before quoting any
    D2 damage figure.

## 9. How to run it

```bash
# 0. the gates -- both must PASS before step 1
python check_random_road.py           # every road binds; the blind arm is blind
python test_reward.py --road random   # the reward gate on the D2 corners

# 1. sixteen runs, memory-capped, into runs_d2/ -- runs/ is never touched
python run_phase_d.py --road random

# 2. eight evaluations, one per seed, into results/d2_seed<N>.txt
python run_phase_d.py --road random --evaluate

# 3. the preregistered test, both experiments side by side
python analyse_phase_d2.py
```

## 10. The gates, as they stood at commit

Both were run on the tree this file is committed with, before any D2 agent
existed. Neither involves a trained agent, so neither can have been tuned to a
D2 result.

### `python check_random_road.py` — EXIT 0, PASS (38.1 min)

```
A. road identical across 3 resets with different seeds : False
   distinct climb starts [146.2, 154.1, 227.1] s; grades [13.66, 13.88, 14.54] %
   (Phase D printed True, [0.0, 0.12] and t = 180 s -- limit 7.)

B. two roads: climb at 150 s / 12 % and at 250 s / 16 %, same seed and weights
   BLIND   observations first differ at t = 150 s   (want 150)
   SIGHTED observations first differ at t = 120 s   (want 120)

C. 121 grades at the worst-case start (300 s), dt 1.0, 720 s
   0.05 % steps over 12-16 %, 0.01 % over 13.60-14.10 %
   weakest: 13.73 % at +6.9 K, 233 s above
   grades that do NOT bind: 0 of 121

D. evaluate.EPISODES_D2, dt 1.0, 720 s
   weakest frozen episode: 13.988 %, start 199.7 s, +12.5 K, 361 s above
   frozen episodes that do NOT bind: 0 of 20

E. training condition, dt 0.2, 900 s
   13.73 % from 300 s and from 120 s, and 12 % from 300 s: all bind
   peak at the thinnest grade: dt 1.0 -> 856.8 C, dt 0.2 -> 856.8 C
```

**The fine sweep found a deeper notch than the design record.** The 0.5 % grid
named 14.0 % (+12.7 K) the weakest grade; the real minimum is **13.73 % at
+6.9 K**, between two grid points. Every grade still binds, so the design
stands, and the finding is recorded in `NEXT_EXPERIMENT_DESIGN.md`'s addendum.
It is also why the reward gate below tests 13.73 %, not 14 %.

### `python test_reward.py --road random` — EXIT 0, all pass

```
PHASE D2 reward gate -- 5 roads x 4 rollouts, 480 s each at dt 0.2
road                  neutral    starver     random   |d obs|   verdict
  120 s / 12.00 %     +0.00043   -1.54083   -0.03149      1.44   PASS
  300 s / 12.00 %     +0.00049   -0.80662   -0.03837      1.44   PASS
  120 s / 16.00 %     +0.00058   -0.02549   -0.01202      1.92   PASS
  300 s / 16.00 %     +0.00056   -0.03889   -0.02633      1.92   PASS
  300 s / 13.73 %     +0.00078   -0.04571   -0.02689     1.648   PASS
```

And the default, fixed-road run on the same tree — **unchanged from Phase D**:
neutral −0.00038, starver −0.90349, preview delta 1.44, 4 of 4 PASS. The D2
code did not move Phase D's reward surface.

**THE STARVER'S MARGIN COLLAPSES ON STEEP GRADES, AND THAT IS DECLARED NOW.**
The gate's rule is "starver < neutral − 0.02". At 12 % the starver is punished
by 0.8–1.5; **at 16 % by only 0.026–0.039, clearing the rule by 0.006 at
120 s / 16 %.** `CLAUDE.md` mistake 17 recorded the same narrowing on the fixed
road (−2.16 to −0.10) and named it *"the number to watch first if a trained
agent turns lazy."* The likely mechanism is mistake 17's own: on a steep grade
the gearbox holds a lower gear, the engine turns faster, and pinning boost trim
low costs little delivered torque — so refusing boost stops being much of a
refusal. The gate passes as written and **nothing was retuned to widen the
margin**; changing the reward now would be changing the experiment to suit a
check. It is limit 10 below, and it is the first thing to inspect if the D2
agents' fuel or tracking figures look unlike Phase D's.

---

## Signed off

| | |
|---|---|
| written | 22 September 2026 |
| code it pins | **`8e91276`** — `random_road.py`, `evaluate.EPISODES_D2`, the gates; `plant_sha` `b5a3069f32a83754`, `road_sha` `1a29dc46db24f233`, episodes `1c5d49852290d27c` |
| minimum effect set by | **the team (Jad), 22 September 2026 — 50 damage units, BEFORE any D2 run** |
| design (option B) chosen by | **the team (Jad), 22 September 2026** — `results/NEXT_EXPERIMENT_DESIGN.md` |
| eight seeds at C1, knowing the power | **the team (Jad), 22 September 2026** — section 5a |

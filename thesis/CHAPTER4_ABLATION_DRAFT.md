# Chapter 4 — The preview ablation: Phase D and Phase D2

**DRAFT, 23 September 2026.** Written while C4 trains, from the committed
result files and preregistrations only, and reviewed adversarially before its
first commit. Every figure below is printed by a named script or stands in a
committed file under `results/`, and is cited beside it; re-run the script
before quoting a figure, because this draft will not move when the data does
(`CLAUDE.md`, mistake 11).

Two findings are reported here and they are kept apart on purpose: **the
preview ablation** (4.2–4.6), which is INCONCLUSIVE in both experiments, and
**learned supervision** (4.7), a separate and descriptive comparison. Reading
the second as evidence for the first is the error `AUDIT.md` C3 names.

---

## 4.1 The question, and why it needs two trained agents

The project's claim is about when preview information is worth acquiring. The
experiments in this chapter ask the narrow version of that claim on one plant:

> **Does an agent that can see the road ahead protect the turbine better than
> an identically trained agent that cannot?**

Before these experiments the repository answered with a hand-written table in
which "predictive, preview disabled" equalled "reactive" to the decimal. That
equality was **guaranteed by construction**: with preview disabled the
predictive policy computed no look-ahead and returned the reactive policy's
action on every step, so the two rows were one rollout (`AUDIT.md` C3). An
ablation is evidence only when the blinded policy *could* have behaved
differently. That requires an agent trained blind, set beside one trained
sighted, under identical conditions — which is what Phase D and Phase D2 are.

One hand-written way of using preview — protecting against the worst grade in
the next 30 s — lost to a policy that acts only on the grade the car is on now
(`current-grade`) by 0.4 points in `check_premise.py`, and lost in every
scenario tried (`results/PREREGISTRATION.md` section 2). The project traced
that to the policy's worst-case-ahead rule rather than to the information, and
concluded that hand-written policies cannot answer the preview question
(`CLAUDE.md`, "A rolling road makes preview worse"). Neither experiment was run
because a positive result was expected.

## 4.2 The design both experiments share

| | |
|---|---|
| plant | the 0-D B58 model of Chapter 3 — validated within the limits stated there; its knock model is not validated (4.9) — with the car's ZF 8HP51 gearbox; `plant_sha` `b5a3069f32a83754` in both experiments |
| arms | **sighted** (four preview channels, 2–30 s ahead) and **blinded** (the same channels zeroed), trained by the same SAC recipe |
| seeds | 0–7 per arm, paired by seed: sighted *k* against blinded *k* |
| training budget | **50 000 steps per run — the "C1" budget**, about 11 training episodes of 900 s at dt 0.2 |
| test set | twenty frozen episodes per experiment, scored at dt 1.0 over 720 s, identical for every policy (Phase D `05a598a574268b20`; D2 `1c5d49852290d27c` — the same episode seeds and preference weights, different roads) |
| primary outcome | per-seed **median damage** over the twenty episodes: the damage integral of `engine_env.damage_rate` — a turbine-housing term with its knee at 1123 K (850 °C), plus an oil term and a knock term |
| test | exact one-sided sign test on the eight paired differences (blind − sighted; positive = preview helped), α = 0.05, with an exact paired permutation test beside it as a sensitivity check |
| minimum effect of interest (MEI) | **50 damage units — preregistered for Phase D2 only.** Set on 22 September, after Phase D's result was known; applied to Phase D post hoc and labelled so wherever it appears (4.3) |

Both experiments were **preregistered**: `results/PREREGISTRATION.md` and
`results/PREREGISTRATION_D2.md` were committed before the first agent of each
trained, and the analysis scripts (`analyse_phase_d.py`,
`analyse_phase_d2.py`) apply the declared statistic and nothing else. Phase D's
file, however, gained its MEI, its power calculation and its limits 6–8 after
its result; each is dated there, and this chapter marks them (4.9). Each file
records, in a run log, every failure and relaunch; no seed was added, dropped
or replaced in either experiment. Phase D's eight evaluations ran on a working
tree with uncommitted changes outside the plant files (`git_dirty` True, no
plant file dirty); D2's ran on a clean tree.

The paired design is what makes eight seeds usable at all: at eight seeds the
sign test tolerates one dissenting seed (p = 0.0352 at 7 of 8), while at five
to seven seeds it passes only on a unanimous result (`PREREGISTRATION.md`
section 4).

## 4.3 Phase D: a fixed climb

**Road.** Flat for three minutes, then a 12 % grade at 130 km/h in 42 °C air,
the same in every training and evaluation episode.

**Result** (`python analyse_phase_d2.py`, the Phase D block):

| seed | baseline ECU | current-grade | sighted | blinded | blind − sighted |
|---|---|---|---|---|---|
| 0 | 959.8 | 633.2 | 340.5 | 350.3 | +9.8 |
| 1 | 959.8 | 633.2 | 354.0 | 348.2 | −5.8 |
| 2 | 959.8 | 633.2 | 308.2 | 376.8 | +68.6 |
| 3 | 959.8 | 633.2 | 302.5 | 689.7 | +387.2 |
| 4 | 959.8 | 633.2 | 639.5 | 367.8 | −271.7 |
| 5 | 959.8 | 633.2 | 525.7 | 237.5 | −288.2 |
| 6 | 959.8 | 633.2 | 498.5 | 549.5 | +51.0 |
| 7 | 959.8 | 633.2 | 331.5 | 418.6 | +87.1 |

| | |
|---|---|
| seeds where preview helped | 5 of 8 |
| mean difference | +4.8 damage units |
| sd of the paired differences | 214.4 |
| exact one-sided sign test | **p = 0.3633** |
| exact paired permutation test | p = 0.4922 |
| **verdict** | **not significant** |

**Spread across episodes and worst episode**, as the preregistration requires
for every arm (`results/phase_d_seed*.txt`). On the fixed road the two
hand-written policies score the same damage in every episode — baseline 959.8
and `current-grade` 633.2, interquartile range (IQR) 0.0 — because their
actions do not depend on the preference weights, which are all that differs
between episodes.

| seed | sighted IQR | sighted worst | blinded IQR | blinded worst |
|---|---|---|---|---|
| 0 | 21.1 | 519.6 | 89.5 | 603.7 |
| 1 | 58.1 | 703.3 | 36.6 | 376.0 |
| 2 | 61.7 | 335.0 | 4.8 | 422.7 |
| 3 | 61.1 | 773.2 | 211.5 | 1004.3 |
| 4 | 41.6 | 665.4 | 150.1 | 499.9 |
| 5 | 18.4 | 589.6 | 8.7 | 737.4 |
| 6 | 81.5 | 789.7 | 37.4 | 588.2 |
| 7 | 53.2 | 735.1 | 40.3 | 701.2 |

**The seed-to-seed spread is the result.** Seed 3 says preview saves 387
damage units; seed 5 says it costs 288. A mean of +4.8 across differences that
large is noise, and separating a result from a coincidence of that kind is why
eight seeds were run rather than one.

**The minimum effect of interest was set after this result**, on
22 September, for Phase D2 (4.5). It cannot move Phase D's verdict — the
primary test never uses it — but it can label the null, and under the MEI rule
Phase D reads **INCONCLUSIVE** (4 of 8 seeds below 50, sign p = 0.6367). That
label is a post-hoc reading and is printed as one every time. **The label
depends on the threshold:** any MEI from 87.2 to 387 units would have
classified Phase D as SMALLER THAN THE MEI by the sign test (the permutation
test disagreeing below about 150), and a 96-unit option was offered. That label
would have counted against preview; INCONCLUSIVE does not. What guards the
choice is the record of how it was made, not which way it points: Phase D's
classification under each option was not shown to the team when 50 was chosen,
and the stated rationale was the dt artefact and the size of supervision
(`PREREGISTRATION.md` section 5).

## 4.4 The design flaw found after Phase D: the blinded arm was not blind

Three limits were added to Phase D's preregistration after its result (limits
6, 7 and 8, dated 22 September), along with its MEI and power calculation
(section 5). This section takes up 6 and 7; 4.8 takes up 8.

**Limit 6 — the budget.** 50 000 steps is what `train.py` itself called "the
first bad run". At about 11 episodes, a null has two readings the experiment
cannot separate: preview does not pay here, or the agents never learned to use
it. Preview is a timing cue, and timing is plausibly the last thing a policy
learns.

**Limit 7 — the blinded arm was not blind.** Verified directly, not relayed
(`PREREGISTRATION.md` limit 7): the road never changed between episodes, and
the blind agent's turbine reading took 900 distinct values in the 900 steps
before the climb. On a fixed road a thermal state is a clock, and a clock on a
memorised road is a preview obtained with no preview channel. **Phase D
therefore compared an explicit preview channel with an implicit one, not
foresight with none.** Whether the blind agents used the clock is unmeasured;
with 11 episodes they may not have. The point is that the experiment cannot
tell. Four explanations for the null were live, beside a fifth — that the
experiment was underpowered (4.6) — and Phase D separated none of them:

| | explanation |
|---|---|
| (i) | preview genuinely buys little at this configuration |
| (ii) | the agents are undertrained — the C1 budget |
| (iii) | the preview carries almost nothing: one grade step per episode |
| (iv) | the blinded arm is not blind — a fixed road and a thermal clock |

## 4.5 Phase D2: the same ablation on a randomised climb

Phase D2 changed the road and nothing else it could avoid changing (`results/
PREREGISTRATION_D2.md`). Every episode draws its own climb — start uniform on
[120, 300] s, grade uniform on [12, 16] % — through a wrapper
(`random_road.py`), so that the environment's code, and therefore every
Phase D agent's fingerprint, is untouched. The twenty evaluation episodes keep
Phase D's seeds and preference weights; only the road differs, drawn once as a
Latin hypercube over the two ranges. The design (vary both when and how steep)
was the team's choice over varying the start alone, because real roads vary in
both and the blind agent should be blind to both (`results/NEXT_EXPERIMENT_
DESIGN.md`).

**The blind arm was verified blind before training.** `check_random_road.py`
part B drives two roads (a climb at 150 s / 12 % and at 250 s / 16 %) with the
same seed and weights: the blind agent's observations first differ at
t = 150 s, when its own climb begins, and the sighted agent's at t = 120 s,
thirty seconds earlier, through the preview channel. Part C checked that every
grade in the range still pushes the turbine past the trigger (0 of 121 grades
fail to bind; the weakest, 13.73 %, by 6.9 K, where the gearbox hands back a
gear). Both outputs are recorded in `PREREGISTRATION_D2.md` section 10.

**The minimum effect of interest was set in advance: 50 damage units.** Set by
the team before any D2 agent trained, after being shown the power analysis:
about 5 % of Phase D's baseline damage (959.8), four times the largest known
measurement artefact (the dt effect, 12.5 units, measured between two
hand-written policies on Phase D's road), and about 15 % of the 326.6 units
that hand-written supervision (`current-grade`) saves on Phase D's episodes
(`power_analysis.py`). On D2's episodes, where the production ECU scores 1118.0,
the same 50 units is a smaller fraction. With an MEI a result falls into one of
three preregistered cells: PREVIEW HELPS (the primary test rejects), SMALLER
THAN THE MEI (a test that the effect is at least 50 rejects), or INCONCLUSIVE
(neither).

**Result** (`python analyse_phase_d2.py`):

| seed | baseline ECU | current-grade | sighted | blinded | blind − sighted |
|---|---|---|---|---|---|
| 0 | 1118.0 | 653.5 | 353.5 | 575.2 | +221.7 |
| 1 | 1118.0 | 653.5 | 485.7 | 411.3 | −74.4 |
| 2 | 1118.0 | 653.5 | 627.8 | 624.1 | −3.7 |
| 3 | 1118.0 | 653.5 | 331.4 | 332.3 | +0.9 |
| 4 | 1118.0 | 653.5 | 357.3 | 407.8 | +50.5 |
| 5 | 1118.0 | 653.5 | 587.1 | 520.0 | −67.1 |
| 6 | 1118.0 | 653.5 | 442.8 | 359.9 | −82.9 |
| 7 | 1118.0 | 653.5 | 400.6 | 406.8 | +6.2 |

| | |
|---|---|
| seeds where preview helped | 4 of 8 |
| mean difference | +6.4 damage units |
| sd of the paired differences | 98.8 |
| preview helps — sign / permutation | **p = 0.6367** / 0.4688 |
| effect below the MEI — sign / permutation | p = 0.1445 / 0.1250 (6 of 8 seeds below 50) |
| **cell** | **INCONCLUSIVE** |

**Spread across episodes and worst episode** (`results/d2_seed*.txt`). On
random roads the hand-written policies vary too: the production ECU has an IQR
of 715.9 and a worst episode of 2363.8; `current-grade` an IQR of 295.5 and a
worst of 907.0.

| seed | sighted IQR | sighted worst | blinded IQR | blinded worst |
|---|---|---|---|---|
| 0 | 204.2 | 838.0 | 349.7 | 1112.7 |
| 1 | 414.8 | 947.4 | 177.7 | 666.3 |
| 2 | 337.0 | 1124.3 | 310.8 | 1183.8 |
| 3 | 545.4 | 1244.3 | 136.4 | 590.6 |
| 4 | 243.7 | 1121.1 | 221.1 | 1053.2 |
| 5 | 382.5 | 1142.5 | 210.3 | 762.1 |
| 6 | 210.6 | 714.7 | 214.9 | 949.8 |
| 7 | 287.1 | 801.0 | 215.6 | 746.9 |

Described, not tested — no test was preregistered on either column: the
sighted agent has the wider IQR in 6 of 8 seeds and the worse worst episode in
5 of 8. If anything, that points away from preview rather than towards it.

Baseline damage is higher than in Phase D (1118.0 against 959.8) because D2's
roads differ from Phase D's in grade and start time; limit 4 of D2 forbids
reading that as "steeper is hotter", and cuts-versus-baseline figures from the
two experiments are not comparable without their baselines beside them.

**What the result says.** With a blinded arm that is verifiably blind, the arms
still do not separate. So explanation (iv) is not needed to explain a null at
this budget. That does **not** show that the fixed road hid nothing in Phase D:
at eight seeds D2 could reliably detect only an effect of about 124 units (4.6),
and D2 changed more than (iv) — its roads are harder to learn at the same
budget (D2 limit 2), and its preview carries grade as well as timing. What D2
rules out is that the fixed road was hiding an effect large enough for eight
seeds to see. Explanations (i) and (ii) remain, (iii) is partly addressed, and
INCONCLUSIVE is a statement about the experiment's size: it cannot tell "no
effect" from "an effect the team would care about".

## 4.6 Power, and a prediction that failed

`power_analysis.py` was written after Phase D's result and before Phase D2
ran. From Phase D's spread it computed that eight seeds had **power 0.10**
against an effect of 50 units, reaching 80 % only near **269 units** — 28 % of
Phase D's baseline damage, close to the whole benefit of supervision. Phase D's
design was therefore underpowered, though nobody computed it before the run:
0.10 is a post-hoc calculation from Phase D's own spread, against an MEI chosen
after its result. D2 was run knowingly at that power, because its design
removes explanation (iv) at any power; whether (iv) mattered in Phase D is a
separate question, and D2 answers it only for large effects (4.5). The team's
decision to run it anyway is recorded in `PREREGISTRATION_D2.md` section 4.

**The preregistration also predicted that randomising the climb would not
shrink the seed-to-seed spread. That prediction was wrong.** The spread fell
from 214.4 to 98.8 — to 46 % of Phase D's. Its cause is not established; one
untested candidate is that Phase D's largest swings came from blind agents
that did or did not memorise the fixed road. At D2's spread, eight seeds have
power **0.24** against the MEI; 80 % power needs an effect of about **124**
units at eight seeds, or about **42 seeds per arm** against 50
(`python power_analysis.py`, the D2 section). These figures assume normally
distributed paired differences, which eight heavy-tailed values cannot
establish — `power_analysis.py` calls them a guide to order of magnitude — and
they rest on a spread estimated from eight differences, so 42 seeds is a point
estimate, not a requirement known to two figures. They plan the next
experiment; they change nothing about D2's preregistered result.

The failed prediction is reported because a preregistration that is only ever
right is not being tested. It was stated before the run, the run contradicted
it, and the contradiction is printed by the script every time it is run.

## 4.7 A separate finding: learned supervision against the best hand-written policy

The second question is whether a trained supervisor beats the best
hand-written one. The comparator is `current-grade`, a policy that protects
according to the grade the car is on now — information a vehicle gets from an
accelerometer. **This comparison is not about preview.** Beating
`current-grade` is necessary for preview to matter but is not evidence of it;
in D2 the blinded agents beat it too, and only the sighted-versus-blinded
comparison of 4.3–4.5 isolates the preview channel.

| | Phase D | Phase D2 |
|---|---|---|
| sighted agent over `current-grade`, per seed, points of median-damage cut | −0.7 to +34.5; positive on 7 of 8 (seed 4 −0.7; seeds 5 and 6 +11.2 and +14.0; the other five +29.1 to +34.5) | positive on **8 of 8**, +2.3 to +28.8 |
| blinded agents' median against `current-grade` | 7 of 8 below its 633.2 (seed 3: 689.7) — but Phase D's blinded arm was not blind (4.4), so this row separates nothing | **all 8 below** its 653.5 (blinded medians 332.3–624.1) |
| worst episode against `current-grade`'s worst | 5 of 8 sighted and 3 of 8 blinded agents are worse than its 633.2 | 5 of 8 sighted and 4 of 8 blinded agents are worse than its 907.0 |

(`python analyse_phase_d2.py`, `results/PHASE_D_RESULT.txt`,
`results/phase_d_seed*.txt`, `results/d2_seed*.txt`; points are percentage
points of cut in median damage against each experiment's own baseline.)

**Neither preregistration declared a test for this comparison.** It is
reported, as both require, and described, not tested. On the median the agents
beat the hand-written policy — in D2 every agent of both arms does, so what the
agents gain does not require the preview channel; that is the separation
`AUDIT.md` C3 asked for, measured rather than argued. **On the worst episode
they do not**, which both preregistrations name as the test of a protection
policy ("good typically and occasionally terrible is not a protection
policy"). Learned supervision is a claim about typical episodes, not about
worst cases. In D2, seed 2's agents beat `current-grade` by less than the
50-unit MEI (sighted 627.8, blinded 624.1, against 653.5).

**The D2 margins are not bought with torque.** The reward barely punishes
torque refusal on the steepest roads (`PREREGISTRATION_D2.md` limit 10), and
five D2 agents burn less fuel than the baseline ECU — the shape refusal would
take. `python check_d2_tracking.py` measured each agent's torque tracking on
the twenty episodes, as the mean per-step torque error above a 3 % band, as a
share of the requested torque: **0 of 16 D2 agents track more than one
percentage point worse than the baseline ECU**, every median within 0.05
points of it (recorded in `PREREGISTRATION_D2.md` section 11). The tails are
not clean: in its worst episode, blinded seed 3 has a per-step excess torque
error of 10.47 %, against 4.39 % in `current-grade`'s worst. The check and its
one-point threshold were written after the D2 damage result, as limit 10
required, and fixed before the tracking figures were read.

**Phase D's agents were not checked.** Five of them also have median fuel below
the baseline ECU's 4664 (blinded seeds 3, 6 and 7; sighted seeds 5 and 6;
`results/phase_d_seed*.txt`). Phase D's 12 % road punishes the torque-starver
far harder than D2's steepest roads (−0.90 against neutral's −0.0004,
`PREREGISTRATION_D2.md` section 10), which makes refusal less attractive but
does not show it absent, so Phase D's supervision margins carry no torque
clearance.

## 4.8 What the two nulls do and do not say

**The defensible sentence, for both experiments:** *with agents trained to the
C1 budget, preview does not separate from seed noise.* Neither result supports
"preview does not help", and neither is written that way anywhere in this
thesis.

| explanation | after Phase D | after Phase D2 |
|---|---|---|
| (i) preview buys little here | live | live |
| (ii) the agents are undertrained (C1) | live | live — the next suspect. Context, not a test: on C4's practice episodes, 15 of 16 D2 agents moved by more than 25 units between 30 000 and 50 000 steps (median 118.2; `results/c4_convergence_calibration.txt`) |
| (iii) the preview carries little | live | partly addressed: each episode is a different step |
| (iv) the blinded arm is not blind | live | removed from D2 by design, and checked; its share in Phase D's null is not separable |
| (v) an effect exists, below what eight seeds can detect | post hoc: power 0.10 against 50 | live: 80 % power only above about 124 units |

**The null is not rescued by H/τ.** Phase D sits at H/τ between about 0.2 (on
the flat approach, where preview can first act) and 0.6 (on the climb); both
rest on the assumed `c_turb` = 6000 J/K, so neither is a measurement. It is
tempting to argue that a null below 1 is what the criterion predicts. That
argument was drafted and refuted (`PREREGISTRATION.md` limit 8): no value "near
1" appears anywhere in the project's statement of the criterion; the only H/τ
curve the project produced — itself void — put the largest preview value near
0.6, which is where Phase D sits, so on the project's own curve, void as it is,
the null is in tension with the criterion, not consistent with it; and a rule
that turns any null into a confirmation cannot be falsified. On a randomised
road τ varies per episode with the grade, so D2 does not sit at one H/τ at all.
The honest position is that these experiments measured one configuration, and
the project has no valid H/τ curve yet to place it on.

## 4.9 Limits, and when each was declared

A limit declared before a result is a limit; one found after it is a finding
about the experiment, and is marked so. The table gives, for each, where it
stands in each preregistration.

| limit | Phase D (`PREREGISTRATION.md`) | Phase D2 (`PREREGISTRATION_D2.md`) |
|---|---|---|
| underpowered | section 5, **after** the result: power 0.10, a post-hoc calculation | limit 1, **before**: power 0.10 declared; 0.24 computed after, from D2's own spread |
| the C1 budget | limit 6, **after** | limit 2, **before**: "eleven episodes buy less here, not more" |
| blinded arm not blind | limit 7, **after** | removed by design; limit 3, **before**, says what the blind agent still sees — the grade it is on, and the distribution of climbs, a prior rather than a preview |
| no H/τ rescue | limit 8, **after** | limit 9, **before** |
| scenario and severity | limit 5, **before**: the mildest grid row reaching the damage knee, on a gearbox corrected the next day; the external candidates tried (SAE J2807, the Taif drive) do not reach the trigger | limit 5, **before**: severity is not realistic and cannot be on this car — the Taif mountain drive peaks 52 K below the trigger, and the car's own driving is above it 0.206 % of the time; realistic in variability only |
| grade is not a hotter knob | — | limit 4, **before**: the gearbox notch near 14 %; no figure is binned by grade |
| dt 0.2 in training, 1.0 in scoring | limit 1, **before** | limit 6, **before** |
| the baseline never enriches | limit 2, **before**: on the 12 % climb | limit 7, **before**: at D2's other grades, unmeasured |
| knock model and `c_turb` | limits 3–4, **before** | limit 8, **before** |
| torque refusal | — | limit 10, **before**; checked after (4.7) |

Three of these need their consequence stated, not just their name:

- **The dt mismatch may push toward the null.** Both arms share the handicap,
  and whether it is symmetric is unmeasured — but there is a reason to doubt it.
  The sighted agent's advantage, if it has one, is timing, and a coarser step
  may cost a timing policy more than a blind one (`PREREGISTRATION.md` limit 1).
  Any asymmetry would therefore push toward the null that both experiments
  returned. The step alone moves the gap between two fixed hand-written policies
  by 1.3 points (12.5 units, `power_analysis.py`); for trained agents and for
  D2's roads its size is unmeasured.
- **The knock model sits inside the primary outcome.** It is not validated
  against this car (correlation −0.149 with the car's own retard), and the
  damage integral both tests are run on contains a knock term, so part of the
  measured quantity rests on a model the car does not support
  (`PREREGISTRATION.md` limit 3). The turbine housing's heat capacity
  (`c_turb` = 6000 J/K) is assumed, and it sets τ, the denominator of H/τ.
- **Enrichment inflates cuts, not the ablation.** The baseline ECU never
  enriches on the 12 % climb; at D2's other grades this is unmeasured. Both
  arms hold the lever, so the ablation is unaffected; "cuts N % versus
  baseline" figures are inflated by it in Phase D and may be in D2.

## 4.10 What comes next: C4, one variable at a time

After D2, two routes remained: train the same agents longer (explanation ii),
or run many more seeds (power). The team chose to change **one variable at a
time** — in Jad's words, *«ولا كذا ما نعرف مين السبب، فنسويهم واحد واحد عشان
نقدر نحدد»* (otherwise we cannot tell which one was the cause, so we do them
one at a time, so that we can tell; `PREREGISTRATION_C4.md` section 2) — and to
run the budget first.

**C4** is D2's design at **300 000 steps** per run (about 66 training climbs),
preregistered in `results/PREREGISTRATION_C4.md` before any of its sixteen
agents trained. One identity probe, stopped at 10 000 steps and never
evaluated, ran before the commit and is disclosed there; its weights were
bit-identical to its D2 twin's, and the first ten C4 runs matched their twins
too at 10 000 steps (section 6a). If `check_c4_start.py` finds the same for all
sixteen runs from 10 000 to 50 000 steps, C4 can be read as D2's agents at a
later training age. For the same reason it is not an independent replication,
and its p-value will be the third unadjusted look at this question on the same
seeds (C4 limits 11 and 13). At D2's spread it has the same power, 0.24,
against the MEI, and can separate the arms only if the effect is large or
convergence shrinks the spread; an INCONCLUSIVE C4, even with converged agents,
would leave (ii) undecided for effects near the MEI (C4 section 2a). It fixes
its readings, its convergence rule and a paired test of whether the budget
changed preview's effect in advance, and its result will be reported beside
Phase D and D2, never pooled with them.

---

*Draft notes, to remove before submission:* the tables are copied from
`python analyse_phase_d2.py` and the committed result files (23 September
2026) — regenerate them from a fresh run before the thesis is compiled; the
torque figures should cite a captured output (`check_d2_tracking.py --out`)
once the machine is free of C4; section 4.10 must be rewritten when C4's
result exists; figure numbering and citations to Chapters 2–3 are not yet in
place.

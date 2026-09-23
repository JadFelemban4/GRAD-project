# `results/` — Phase D and Phase D2

## Phase D2 — the same ablation, with a blind arm that is blind: INCONCLUSIVE

```bash
python analyse_phase_d2.py      # D2's preregistered test, Phase D beside it
```

Phase D's null had a design flaw: its blinded arm could memorise one fixed road
(`PREREGISTRATION.md` limit 7). **Phase D2 re-ran the ablation on a randomised
climb** — start 120–300 s, grade 12–16 %, drawn per episode — under
`PREREGISTRATION_D2.md`, committed before any D2 agent trained, with the
minimum effect of interest set in advance at **50 damage units**.
`check_random_road.py` verified the blind arm is blind: its observations are
identical on every road until its climb arrives.

| | Phase D | **Phase D2** |
|---|---|---|
| blinded arm | not blind (a memorisable road) | **blind — checked** |
| seeds where preview helped | 5 of 8 | **4 of 8** |
| mean effect (blind − sighted) | +4.8 | **+6.4** damage units |
| preview helps — sign p | 0.3633 | **0.6367** |
| effect below the MEI — sign p | 0.6367 (post-hoc) | **0.1445** (6 of 8 below 50) |
| sd of the paired differences | 214.4 | **98.8** |
| **cell** | INCONCLUSIVE (post-hoc) | **INCONCLUSIVE** |

- **Removing the memorisable road did not pull the arms apart.** The design
  flaw is not what hid a preview effect in Phase D. What remains: preview buys
  little at this configuration, or C1 agents (50 000 steps, 11 episodes) cannot
  learn to use it. **INCONCLUSIVE is not "preview does not help"** — at eight
  seeds this experiment has power 0.24 against 50 units.
- **The spread halved, against the preregistered prediction.** `power_analysis.py`
  prints what that buys: 80 % power against 50 units now needs about 42 seeds
  per arm, down from 186. That plans the next experiment.
- **Supervision, a separate claim, is cleaner than in Phase D:** the sighted
  agent beats `current-grade` on 8 of 8 seeds (+2.3 to +28.8 points), and so
  does every blind agent — the gain over the hand-written comparator does not
  need the preview channel.
- **Before quoting any D2 damage figure as protection,** read
  `check_d2_tracking.py` (`PREREGISTRATION_D2.md` limit 10): five agents burn
  less fuel than the baseline ECU, which is what refusing torque would look like.

Full account, with every limit: `PREREGISTRATION_D2.md` section 11.

---

# Phase D

**Phase D has run. The result is a NULL, and a null is a result.**

Reproduce all of it in seconds:

```bash
python analyse_phase_d.py
```

## The result

Sixteen agents — eight seeds per arm, sighted and blinded, 50 000 steps each —
trained on the current ZF 8HP51 plant under `PREREGISTRATION.md`, **which was
committed before any of them started**, and scored over the twenty frozen
episodes in `evaluate.EPISODES`.

| seed | baseline | current-grade | sighted | blinded | blind − sighted |
|---|---|---|---|---|---|
| 0 | 959.8 | 633.2 | 340.5 | 350.3 | +9.8 |
| 1 | 959.8 | 633.2 | 354.0 | 348.2 | −5.8 |
| 2 | 959.8 | 633.2 | 308.2 | 376.8 | +68.6 |
| 3 | 959.8 | 633.2 | 302.5 | 689.7 | **+387.2** |
| 4 | 959.8 | 633.2 | 639.5 | 367.8 | **−271.7** |
| 5 | 959.8 | 633.2 | 525.7 | 237.5 | **−288.2** |
| 6 | 959.8 | 633.2 | 498.5 | 549.5 | +51.0 |
| 7 | 959.8 | 633.2 | 331.5 | 418.6 | +87.1 |

```
positive (preview helped) : 5 of 8
mean difference           : +4.8 damage units
exact one-sided sign test        p = 0.3633
exact paired permutation test    p = 0.4922   (sensitivity)
alpha 0.05                       ->  NOT SIGNIFICANT
```

### What that means, and what it does not

**Preview cannot be shown to help.** Read the last column: seed 3 says preview
saves 387 damage units and seed 5 says it costs 288. The seed-to-seed spread is
tens of times the effect, and a mean of +4.8 across it is noise.

**That is what eight seeds were for.** Train seed 3 alone and the answer reads
"+387, preview works" — and it would have been written up. The seeds are the
only thing separating a result from a coincidence.

**A SECOND FINDING, POSITIVE, AND NOT THE SAME CLAIM.** The trained agent beats
the `current-grade` comparator — the honest no-preview comparator — by **+29 to
+34 points** on five of eight seeds, and is positive on seven of eight.

> **Learned supervision works. PREVIEW SPECIFICALLY is what cannot be shown.**
> Two separate claims. Only the second was preregistered as the hypothesis, and
> reading the first as evidence for it is exactly the conflation `AUDIT.md` C3
> is about.

This agrees with everything measured before it: the hand-written policies put
preview at **−0.4 points** against current-grade, and five scenarios gave the
same sign.

### The training budget, which belongs beside the null and not under it

Every agent above is a **C1** agent. `train.py`'s own usage block:

```
python train.py --steps 50000  --seed 0   # C1: the first bad run
python train.py --steps 300000 --seed 0   # C4: a real run
```

50 000 steps at 4 500 steps per episode is **11 training episodes**. A null has
two readings and eleven episodes cannot separate them: preview may genuinely not
pay off here, or the agents may never have learned to exploit it. Preview is a
timing cue, and timing is plausibly the last thing a policy learns.

**So the defensible sentence is narrower than "preview does not help":**

> With agents trained to this project's C1 budget, preview does not separate
> from seed noise.

All sixteen curves do improve (first five versus last five, 16 of 16), which is
C1's criterion and is not evidence of convergence. Settling it means the same
sixteen runs at 300 000 steps — **a SECOND experiment, with its own
preregistration**, because section 7 forbids extending this one.

`PREREGISTRATION.md` limit 6.

### THE BLINDED ARM IS NOT BLIND — the most serious limit on this result

Found 22 September and **verified directly**:

```
road identical across 3 resets with different seeds : True
distinct grade values in the road                   : [0.0, 0.12]
step location                                        : t = 180 s
blind agent, flat phase: obs[7] over 900 steps      : 900 distinct values
```

The road is **the same hill at the same second** in every training episode and
every evaluation episode. The blind agent sees zeros where the preview should
be, but its thermal state takes a distinct value at every step — so it has a
clock, on a road it can memorise.

**So this experiment compared an explicit preview channel with an implicit one,
not foresight with none.** If both arms learned where the hill is, a null is
what should come out, and it says nothing about whether foresight is worth
acquiring. Whether the blind agents actually did this is unmeasured — with 11
training episodes they may not have — and that is the problem: **four
explanations for the null are live, and this experiment separates none of
them.** `PREREGISTRATION.md` limit 7 lists them.

**The fix is cheap and comes before C4:** randomise the climb's start time and
grade per episode. Then no memorisation tells the blind agent when the hill
arrives, and the preview channel is the only route to knowing — which is what an
ablation of preview has to mean.

**That fix is now Phase D2,** preregistered in `PREREGISTRATION_D2.md` before
any D2 agent trained: the climb's start time (120–300 s) and grade (12–16 %)
drawn per episode, with a minimum effect of interest of 50 damage units set in
advance. Training launched on 22 September. **No D2 result exists yet.**

**This does not touch the +29 to +34 point finding.** That compares the agent
with a hand-written policy, and learning the road is a legitimate thing for a
supervisor to do. It is a finding about learned supervision on this road.

### Do not rescue the null with H/τ

Phase D sits at H/τ ≈ 0.23 (while the preview can first act, on the flat) to
0.62 (on the climb). It is tempting to say "that is below where preview matters,
so the null fits the theory". **It does not.** The project's only H/τ curve —
void, but the only one — puts the largest preview value near 0.6, which is where
Phase D sits. The reading was drafted, checked and refuted on 22 September.
`PREREGISTRATION.md` limit 8 says why in full.

### The minimum effect of interest — set late, and the experiment is underpowered

**It was set on 22 September 2026, at 50 damage units — AFTER this result was
known.** `PREREGISTRATION.md` section 5 says so plainly. It cannot move the
verdict above, because the sign test never uses it; it can only label the null,
and that label is marked post-hoc wherever it is printed.

**The power analysis matters more.** `power_analysis.py`: at Phase D's spread,
eight seeds have **power 0.10** against an effect of 50, and reach 80 % power
only against **~269 units**. So this null — from C1-budget agents, which is a
separate limit above — cannot tell "preview is worth
nothing" from "the experiment was too small to see it", and that is the first
question an examiner will ask.

## The files

| file | what it is |
|---|---|
| `PREREGISTRATION.md` | the rules, committed before any agent trained. Section 6a logs two failed launches and their causes |
| `PREREGISTRATION_D2.md` | Phase D2's rules — the same ablation on a randomised climb — committed before any D2 agent trained. Its section 11 is the outcome, marked as added after the result |
| `d2_seed0.txt` … `seed7.txt` | one D2 evaluation per seed, each with the D2 plant fingerprint (`scenario` random-climb, episodes `1c5d49852290d27c`) |
| `NEXT_EXPERIMENT_DESIGN.md` | the design record D2's preregistration was written from. Not itself a preregistration |
| `phase_d_seed0.txt` … `seed7.txt` | one evaluation per seed, each opening with the **plant fingerprint** of the tree that produced it |
| `PHASE_D_RESULT.txt` | the output of `analyse_phase_d.py`, captured |
| `curve_*.csv` | learning curves |
| `void/` | result files that are **not** results. Read its README before quoting anything from it |

## How it was produced

```bash
python run_phase_d.py                 # 16 runs, memory-capped, ~1 h
python run_phase_d.py --evaluate      # 8 evaluations, ~2.5 h
python analyse_phase_d.py             # the preregistered test
```

Phase D2, the same launcher with the road randomised (into `runs_d2/`, never
`runs/`; `runs_d2/LAUNCH.txt` and `PREREGISTRATION_D2.md` §6a log two
relaunches, neither of which interrupted a run):

```bash
python check_random_road.py                  # gate: every road binds, blind arm blind
python test_reward.py --road random          # gate: the reward on the D2 corners
python run_phase_d.py --road random          # 16 runs
python run_phase_d.py --road random --evaluate
python analyse_phase_d2.py                   # the preregistered test, both experiments
python check_d2_tracking.py                  # limit 10: torque delivery per agent
```

`evaluate.py` writes the plant fingerprint into every result file and **refuses
a model whose plant disagrees with the tree it is run on**. That is why these
files can be trusted to belong to the plant quoted beside them — and it is the
thing the file now in `void/` could not do.

## What this file used to say

<!-- RETIRED-OK: section 11.7, 7.5 -- quoting the void figures IS this section; void/README.md says why they are void -->
It led with *"phase_d_seed0.txt — THE FIRST MEASURED PREVIEW ADVANTAGE"* and
*"sighted +11.7 points over blinded, from a proper ablation"*.

That pair was trained on an invented six-speed gearbox which commit `27e720c`
replaced **seven hours after the file was committed** (`a68715f`), and nothing in the file
recorded it. See `void/README.md`. **Do not quote +11.7, or the +7.5 that
re-scoring the same pair produced.** Neither is a result.

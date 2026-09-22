# `results/` — Phase D

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

### Outstanding before this is written up

**The minimum effect of interest is not set** — `PREREGISTRATION.md` section 5,
marked TEAM DECISION. Until it is, "preview does not help" cannot be
distinguished from "the experiment was too small to see it", and that is the
first question an examiner will ask. `analyse_phase_d.py` prints a warning
while it is unset.

## The files

| file | what it is |
|---|---|
| `PREREGISTRATION.md` | the rules, committed before any agent trained. Section 6a logs two failed launches and their causes |
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

`evaluate.py` writes the plant fingerprint into every result file and **refuses
a model whose plant disagrees with the tree it is run on**. That is why these
files can be trusted to belong to the plant quoted beside them — and it is the
thing the file now in `void/` could not do.

<!-- RETIRED-OK: 11.7 -- naming the void figure IS this section -->
## What this file used to say

It led with *"phase_d_seed0.txt — THE FIRST MEASURED PREVIEW ADVANTAGE"* and
*"sighted +11.7 points over blinded, from a proper ablation"*.

That pair was trained on an invented six-speed gearbox which commit `27e720c`
replaced **seven hours before the file was written up**, and nothing in the file
recorded it. See `void/README.md`. **Do not quote +11.7, or the +7.5 that
re-scoring the same pair produced.** Neither is a result.

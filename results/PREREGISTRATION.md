# PREREGISTRATION — Phase D, the preview ablation

**Written 21 September 2026, BEFORE any agent was trained on this plant.**
Committed before seed 0 of either arm started. That ordering is the whole point
of this file: a hypothesis declared after the numbers are in is not a
hypothesis, it is a description.

> **Status:** two lines were marked **TEAM DECISION**. They had to be settled,
> and this file re-committed, **before `evaluate.py` is run** — not merely
> before the thesis is written. Setting a threshold after seeing where the
> result landed is the same failure as changing the test set.
>
> **That rule was broken for one of the two lines, and it is stated here
> rather than tidied away.** The seed count (eight) was accepted before any
> agent trained. **The minimum effect of interest was not set until
> 22 September 2026 — after Phase D's result had been seen.** See section 5
> for what that does and does not touch. In short: it cannot move the verdict,
> because the primary test never uses it; it can only label the null, and that
> label is marked post-hoc wherever it is printed.

---

## 1. The question

Does an agent that can see the road ahead protect the turbine better than an
identically trained agent that cannot?

Not "does supervision help" — that is a different and easier question, answered
by the `current-grade` comparator. **This file preregisters the PREVIEW
question only.**

## 2. Why this has to be a trained pair, and not the table the repo already has

`check_premise.py` prints a five-row table in which "predictive, preview
disabled" equals "reactive" to the decimal. That identity is **guaranteed by
construction** and is not evidence: with `use_preview=False` the preview vector
is zeros, so `p_predictive` computes `k_ahead = 0` and returns `p_reactive`'s
own action on every step. The two rows are the same rollout. (`AUDIT.md` C3.)

An ablation is evidence only when the blinded policy **could** have behaved
differently and did not. That requires a blinded agent that was TRAINED blind,
which is what this preregistration is for.

It also matters that the hand-written policies currently say preview **loses**:
on the locked scenario `check_premise.py` prints preview at **−0.4 points**
against `current-grade`. Five scenarios have now shown the same sign. So this
experiment is not being run because a positive result is expected.

## 3. The plant, pinned

Every run is fingerprinted by `fingerprint.py` and `evaluate.py` refuses a model
whose plant differs. The values below are the ones in force; a run that does not
carry them is not part of this experiment.

| field | value |
|---|---|
| gearbox | ZF 8HP51, ratios 5.250 3.360 2.172 1.720 1.316 1.000 0.822 0.640 |
| final drive | 3.150 |
| crank-angle step | `plant.DTHETA_DEG` = 0.25° |
| protection trigger | `TURB_PROTECT_K` = 1123 K (850 °C) |
| scenario | 12 % grade, 130 km/h, 42 °C ambient |
| training episode | 900 s at dt 0.2 |
| evaluation | 720 s at dt 1.0, the twenty frozen episodes |

## 4. The design

| | |
|---|---|
| arms | **sighted** (`train.py --seed N`) and **blinded** (`--no-preview`) |
| seeds | **0 … 7** — EIGHT per arm, sixteen runs |
| steps | 50 000 per run |
| pairing | by seed: sighted seed *k* against blinded seed *k* |
| test set | the twenty `(seed, weights)` pairs frozen in `evaluate.EPISODES`, hash `05a598a574268b20`. **They do not change.** |

### Why eight and not five

The brief that led here said five, and called it "a floor, not a choice". The
arithmetic says the floor is too low. One-sided sign test, smallest attainable
*p*:

| seeds per arm | all agree | one dissents | two dissent |
|---|---|---|---|
| 5 | 0.0312 ✓ | 0.1875 ✗ | 0.5000 ✗ |
| 6 | 0.0156 ✓ | 0.1094 ✗ | 0.3438 ✗ |
| 7 | 0.0078 ✓ | 0.0625 ✗ | 0.2266 ✗ |
| **8** | **0.0039 ✓** | **0.0352 ✓** | 0.1445 ✗ |

At five, six or seven seeds the test passes **only on a unanimous result**: a
single seed falling the other way puts *p* above 0.05 whatever the effect size.
**Eight is the first count that tolerates one dissenting seed** — and the audit
already measured seed-level variance in this environment (re-scoring the one
existing pair swapped their interquartile ranges).

Sixteen runs is about an hour of wall clock on this machine: each run is
single-threaded — 19.19 steps/s on one thread against 18.14 on six, so threads
do not help — and the machine has twelve cores, so the runs go in parallel as
separate processes rather than one after another.

**Eight is a choice and it is reversible before the runs start, not after.**

## 5. The statistic

- **Primary outcome:** per-seed **median damage** over the twenty frozen
  episodes, as `evaluate.py` reports it.
- **Comparison:** paired, by seed. For seed *k*, `damage_blind[k] −
  damage_sighted[k]`; positive means preview helped.
- **Test:** exact one-sided sign test on the eight paired differences.
  A paired permutation test on the same differences is reported beside it as a
  sensitivity check; if the two disagree, **both are reported** and neither is
  chosen after the fact.
- **α = 0.05, one-sided.** One-sided because the pre-registered direction is
  "preview helps"; a significant result in the *other* direction is reported as
  what it is — preview costing damage — and not converted into a two-sided win.
- **Minimum effect of interest: 50 damage units — SET 22 SEPTEMBER 2026, AFTER
  THIS EXPERIMENT'S RESULT WAS KNOWN.** Set by the team (Jad), for Phase D2's
  preregistration (`results/PREREGISTRATION_D2.md`), and recorded here to close
  this line. About 5 % of baseline damage (959.8), four times the largest known
  measurement artefact (the dt effect, 12.5 units), and about 15 % of what
  supervision alone buys (326.6).

  **What the late setting cannot touch.** The primary test — the sign test on
  "preview helps" — never uses the MEI, so Phase D's verdict is exactly what it
  was: **not significant, p = 0.3633.** No threshold chosen afterwards can move
  that.

  **What it can touch, and how that is kept honest.** With an MEI a null can be
  classified: "preview's effect is shown to be below 50" versus "the experiment
  cannot tell". `analyse_phase_d2.py` applies that rule to Phase D and prints
  **INCONCLUSIVE** (4 of 8 seeds below 50, sign p = 0.6367) — labelled
  *"MEI set AFTER this result"* every time. It is a reading, not a finding, and
  it must not be quoted as though it had been preregistered.

  **Was 50 chosen to flatter Phase D?** That is the question to ask of any late
  threshold, so it was computed rather than asserted — and the first answer
  written here was WRONG. It said "every MEI from 10 to 400 classifies Phase D
  INCONCLUSIVE". Computed, Phase D's post-hoc label DOES depend on the MEI:

  | MEI | seeds below it | sign p | permutation p | label |
  |---|---|---|---|---|
  | 10 – 87.1 | 4 – 6 of 8 | ≥ 0.0625 | ≥ 0.1328 | INCONCLUSIVE |
  | 87.2 – 387 | 7 of 8 | 0.0352 | 0.1289 → 0.0078 | SMALLER THAN THE MEI (sign); **permutation disagrees below ~150** |
  | ≥ 388 | 8 of 8 | 0.0039 | 0.0039 | SMALLER THAN THE MEI |

  So the 96-unit option the team was also offered would have labelled Phase D
  "smaller than the MEI" by the primary test, with the sensitivity test
  disagreeing. **50 gives the weaker label, not the stronger one.** Phase D's
  classification was not shown to the team when the choice was made; the choice
  rested on the artefact floor and the size of supervision
  (`power_analysis.py`), and on the number becoming the D2 threshold, where it
  IS preregistered. Recorded here so a reader does not have to take that on
  trust — the table is what `analyse_phase_d2.py`'s functions compute.

  **And the reason the line mattered is now measured, not argued.**
  `power_analysis.py`: at Phase D's spread, eight seeds have **power 0.10**
  against an effect of 50, and reach 80 % power only against **~269 units** —
  28 % of baseline damage, close to the whole benefit of supervision. So
  Phase D's null is consistent with preview being worth nothing and equally
  consistent with it being worth 100 units. That is a fifth thing to set beside
  the four live explanations in limit 7: **the experiment was underpowered by
  design.**

## 6. Everything reported, whatever it says

- All sixteen runs are reported, including any that fail to learn. A run is
  **not** dropped for a poor curve; `train.py`'s own docstring records that
  first-five-versus-last-five on eleven episodes is the weight draw, not
  learning, so "it did not learn" is not a filter this experiment may apply.
- If a run crashes, it is re-run **with the same seed** and the crash is
  recorded here. It is not replaced by a different seed.
- Median, interquartile range **and worst episode** are reported for every arm.
  A protection policy that is good typically and occasionally terrible is not a
  protection policy.
- The `current-grade` comparator is reported beside both arms. Beating the
  baseline ECU proves supervision helps; only beating `current-grade` says
  anything about preview.

## 6a. Run log — failures and re-runs, recorded as section 6 requires

**21 September 2026, first launch: 13 of 16 runs died of MemoryError.**

`run_phase_d.py` started all sixteen at once. SB3's default replay buffer is
1 000 000 transitions and is allocated in full at construction — about 200 MB
per run — so sixteen parallel runs asked for 3.2 GB of buffer on top of their
own process memory, on a machine already at 62 % of 31 GB. Thirteen raised
`numpy MemoryError` inside `SAC.__init__`, before a single training step.

| | |
|---|---|
| completed | `sighted_seed1`, `blind_seed1`, `sighted_seed7` |
| failed | the other thirteen, all in `SAC.__init__` |
| cause | machine memory, not the environment, the reward or the plant |

**Fix:** the buffer is sized to the run — a buffer larger than `--steps` can
never fill. 50 000 steps needs 50 000 slots, which is 10 MB instead of 200.

**Why this does not make the thirteen incomparable with the three.** A replay
buffer changes behaviour only when it EVICTS, and neither size evicts when the
run is shorter than the smaller buffer. That is an argument, so it was checked:
the same seed was trained both ways and every network parameter compared —
**32 tensors, 368 398 values, largest difference 0.000e+00.** Identical. The
three completed runs stand and the thirteen are re-run **with their original
seeds**, as section 6 requires.

Re-run the proof at any time with:

```bash
python run_phase_d.py --prove-buffer
```

**21 September, second launch: 8 of 13 died again, of the same shortage by a
different route.** With the buffer fixed the `numpy MemoryError` was gone, but
nine concurrent runs still exhausted memory and torch raised `RuntimeError: bad
allocation` inside its forward pass. Five completed.

The cause was a guess. The concurrency cap had been computed from an ESTIMATE
of 0.9 GB per run. One process was then actually watched:

```
peak RSS of ONE train.py process: 1522 MB
```

**1.5 GB, not 0.9 — the estimate was 70 % low**, which is the whole margin
between a cap that works and one that does not. `run_phase_d.py` now carries
the measured figure, and checks free memory again *before each launch* rather
than trusting a number computed once at the start.

This is the session's own lesson arriving twice: the first launch guessed
nothing and counted cores, the second guessed the wrong number, and only the
measurement settled it.

**Completed by the end of the second launch:** seeds 1, 2, 3 and 7, both arms —
four complete pairs.

**No seed was changed, added or dropped because of any of this.** Every failure
was mechanical, every one happened in the first minute before an agent had
learned anything, and no evaluation had been run when they were fixed. Seeds 0,
4, 5 and 6 were re-launched under their original numbers.

## 7. Stopping rule

Sixteen runs, then stop. **No seed is added after any result is seen.** If the
team later wants more seeds, that is a second experiment with its own
preregistration, and both get reported.

## 8. Known limits that apply to whatever comes out

These are declared now so they cannot be discovered later as excuses.

1. **The agents are scored at a step they were not trained at.** Training is
   dt 0.2, evaluation dt 1.0. The damage integral moves with the step — the
   headline "cuts N %" shifts about 7 points between dt 0.2 and 2.0, and 94 % of
   that is one knock spike at the grade discontinuity. The handicap is shared by
   both arms, so it is not a bias by construction; whether it is **symmetric**
   is unmeasured, and a policy whose value is timing may lose more to a coarse
   step than one with no preview at all. (`AUDIT2.md` H2-2.)
2. **The baseline never enriches on this scenario.** The climb sits at 2706 rpm
   and `base_lambda` returns 1.000 there at any load and any dwell. Enrichment
   is one of the four protection levers and the agent can pull it where the
   production ECU would not, so any "cuts N % versus baseline" figure is
   inflated by a lever the baseline never uses. **The sighted-versus-blinded
   comparison is unaffected — both arms hold the same lever.**
3. **The knock model is not validated against this car.** Model knock integral
   against the car's own retard: correlation **−0.149** over 13 592 paired
   samples. The damage function contains a knock term, so part of the quantity
   being optimised rests on a model the car does not support.
4. **`c_turb` = 6000 J/K is assumed, not measured**, and it sets the time
   constant that is the denominator of this project's central ratio.
5. **The scenario was selected as the mildest grid row that reaches the damage
   knee**, on a gearbox that was corrected the next day. It is not an external
   duty cycle; the two external candidates tried (SAE J2807, the Taif drive) do
   not reach the trigger and that is disclosed.

6. **THE AGENTS ARE TRAINED FOR 50 000 STEPS, WHICH THIS PROJECT'S OWN CODE
   CALLS "THE FIRST BAD RUN" — and of the six limits here this is the one that
   bears hardest on a null.** Added 22 September, after the result, because it
   was missing and the result cannot be read honestly without it.

   `train.py`'s usage block defines the two budgets:

   ```
   python train.py --steps 50000  --seed 0   # C1: the first bad run
   python train.py --steps 300000 --seed 0   # C4: a real run
   ```

   Every agent behind the table above is a **C1** agent. At 4 500 steps per
   episode that is **11 training episodes** — and `evaluate.py`'s own docstring
   already warns that eleven episodes of this environment span −506 to +644
   purely on the weight draw.

   **A null has two readings and eleven episodes cannot separate them:**

   | reading | what it would mean |
   |---|---|
   | preview genuinely does not pay off here | a result about H/τ, which is the project's claim |
   | the agents never learned to exploit preview | a limit of the experiment, not of the phenomenon |

   The second is live: preview is a timing cue, not a crude signal, and timing
   is plausibly the last thing a policy learns. **Do not write "preview does not
   help on this plant" without this paragraph beside it.** The defensible
   sentence is narrower: *with agents trained to this project's C1 budget,
   preview does not separate from seed noise.*

   What would settle it, and it is the obvious next experiment: the same
   sixteen runs at `--steps 300000` (C4). On this machine that is about six
   hours at the measured concurrency. **It is a SECOND experiment and needs its
   own preregistration** — section 7 forbids extending this one — and both get
   reported whichever way it goes.

   All sixteen curves did improve (first five versus last five, 16 of 16), so
   the agents learned *something*. That is C1's criterion and not evidence of
   convergence; `train.py` prints the same caveat under its own curve summary.

7. **THE BLINDED ARM IS NOT BLIND. This is the most serious limit on the null,
   and it is a flaw in the ablation's design, not in its execution.** Added
   22 September, after the result, and marked so for the same reason as limit 6.
   Found by an adversarial check of a different claim (see `CHECKPOINT.md`,
   22 September) and then **verified directly**, not relayed:

   ```
   road identical across 3 resets with different seeds : True
   distinct grade values in the road                   : [0.0, 0.12]
   step location                                        : t = 180 s
   blind agent, flat phase: obs[7] over 900 steps      : 900 distinct values
   preview channels                                     : [0.0, 0.0, 0.0, 0.0]
   ```

   **The road never changes.** `make_grade_climb()` builds one cycle — flat for
   three minutes, then 12 % from t = 180 s — and `reset()` never rebuilds it;
   only the preference weights are redrawn. Every training episode and every one
   of the twenty evaluation episodes is the same hill at the same second.

   **And the blinded agent can tell what second it is.** Its preview channels
   are zeros, but its thermal state is not: the turbine reading alone takes 900
   distinct values in the 900 steps before the climb. On a fixed road, "the
   turbine has reached this temperature" is a clock, and a clock plus a
   memorised road is an unlimited preview obtained with no preview channel at
   all.

   **So Phase D did not compare "30 s of foresight" against "no foresight".** It
   compared *an explicit preview channel* against *an implicit clock on a road
   the agent can memorise*. If both arms learned where the hill is, the null is
   exactly what should come out — and it says nothing about whether foresight is
   worth acquiring.

   **Whether the blind agents actually exploited this is UNMEASURED.** With 11
   training episodes (limit 6) they may not have. That is the point: this
   experiment cannot tell. **Four explanations for the null are live and it
   separates none of them:**

   | | explanation |
   |---|---|
   | (i) | preview genuinely buys little at this configuration |
   | (ii) | the agents are undertrained — C1, 11 episodes (limit 6) |
   | (iii) | the preview carries almost nothing: one 0 → 0.12 step in 900 s |
   | (iv) | the blinded arm is not blind — a fixed road plus a thermal clock |

   **The fix is cheap and decisive, and it comes before C4:** randomise the climb
   per episode — its start time, and its grade — so that no amount of
   memorisation tells the blind agent when the hill arrives. Then, and only then,
   the only route to anticipating it is the preview channel, which is what an
   ablation of preview has to mean. It is a SECOND experiment with its own
   preregistration.

   **What this does NOT touch:** the SEPARATE finding that the trained agent
   beats `current-grade` by +29 to +34 points. That compares the agent with a
   hand-written policy, not sighted with blind, and memorising the road is a
   legitimate thing for a supervisor to learn. It is a claim about learned
   supervision on this road, and it should be written as exactly that.

8. **WHERE PHASE D SITS ON H/τ — and a tempting reading of it that is WRONG.**
   Added 22 September. Recorded in full because the wrong reading was drafted,
   checked, and refuted, and the next person will draft it again.

   **The measured position, with its conditions:**

   | quantity | value | condition |
   |---|---|---|
   | longest preview horizon H | 30 s | `engine_env.PREVIEW_S = (2, 5, 15, 30)` |
   | turbine τ on the climb | 48 s | neutral policy, locked scenario |
   | turbine τ on the flat approach | 129 s | same run — τ is set by exhaust flow |
   | **H/τ while preview can first act** | **≈ 0.23** | t = 150–180 s, on the flat |
   | **H/τ once the climb is under way** | **≈ 0.62** | on the climb |

   **τ is not one number.** Over the locked episode it spans 40–239 s, a factor
   of six, because it is `c_turb / UA` and UA rises with exhaust flow. Quoting a
   single τ is mistake 15, which is about exactly that. And `c_turb = 6000 J/K`
   is ASSUMED (`REFERENCES.md` section 4), so every τ and every H/τ here is an
   assumed number to within that constant. Do not quote H/τ to two decimals.

   **THE WRONG READING — do not write it.** It runs: *"H/τ is below 1, preview
   is predicted to matter near 1, so the null is CONSISTENT with the project's
   theory."* Three things are wrong with it:

   1. **"Near 1" appears nowhere in this repository.** The theory says preview
      matters where H and τ are "comparable" (`CLAUDE.md`, "What this project
      is") and never locates that band numerically.
   2. **The only numbers the project ever produced say the opposite.** The H2
      sweep in `README.md` puts the LARGEST preview edge at H/τ ≈ 0.6 — which is
      where Phase D sits. On the repository's own curve the null is in
      **tension** with the theory, not consistent with it. That curve is void
      (`AUDIT.md` C1, M12), so it cannot refute anything either — but it rules
      out using the theory as a rescue.
   3. **It is unfalsifiable.** A rule that turns any null into a confirmation
      without measuring where the point sits on a curve is `AUDIT.md` C3's error
      pointed the other way.

   **The defensible sentence:** *Phase D measured one configuration, at H/τ
   between about 0.23 and 0.62 depending on the phase. The project has no valid
   H/τ curve to place it on, and four explanations for the null are live
   (limit 7).*

   **And the H/τ axis itself is currently broken.** `generality_test.py` line 81
   reads `info.get("mdot")`, but the environment never puts `mdot` in `info`, so
   `_exhaust_of_climb()` returns nothing and line 197 falls back to the assumed
   112.5 g/s on every run. The `AUDIT.md` M12 fix — "the flow is measured from the
   baseline trajectory instead" — does not work. Verified 22 September by calling
   the function: 0 samples. **Fix it before quoting any H/τ axis from that
   script.**

   **What a preview horizon longer than 30 s would buy is untested.** A real map
   is worse than this simulation in accuracy and far better in reach: it sees the
   whole route, not 30 s. Lengthening `PREVIEW_S` is a legitimate experiment —
   but on a fixed road it would be confounded by limit 7 exactly as this one is,
   so it belongs AFTER the climb is randomised, not before.

## 9. How to run it

```bash
# sixteen runs, in parallel; about an hour on a twelve-core machine
for s in 0 1 2 3 4 5 6 7; do
  python train.py --steps 50000 --seed $s &
  python train.py --steps 50000 --seed $s --no-preview &
done
wait

# then, per seed
python evaluate.py --out results/phase_d_seed$s.txt \
    runs/sighted_seed$s runs/blind_seed$s
```

`evaluate.py` writes the plant fingerprint into every result file and refuses a
model whose plant disagrees, so a result produced on the wrong plant cannot be
filed under this preregistration without the mismatch being printed in it.

---

## Signed off

| | |
|---|---|
| written | 21 September 2026 |
| commit this file was committed in | *(filled by the commit that adds it)* |
| minimum effect set by | **the team (Jad), 22 September 2026 — 50 damage units. AFTER the result; see section 5** |
| seeds agreed by | **the team — eight, accepted before any agent trained** (`CHECKPOINT.md`, session close 21–22 September) |

# PREREGISTRATION — Phase D, the preview ablation

**Written 21 September 2026, BEFORE any agent was trained on this plant.**
Committed before seed 0 of either arm started. That ordering is the whole point
of this file: a hypothesis declared after the numbers are in is not a
hypothesis, it is a description.

> **Status:** two lines are marked **TEAM DECISION** and are not filled in.
> They must be settled, and this file re-committed, **before `evaluate.py` is
> run** — not merely before the thesis is written. Setting a threshold after
> seeing where the result landed is the same failure as changing the test set.

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
- **Minimum effect of interest:** **TEAM DECISION — NOT YET SET.** See the
  banner at the top. The number belongs here because without it a null result
  cannot be told apart from an underpowered one.

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
| minimum effect set by | **TEAM DECISION — OUTSTANDING** |
| seeds agreed by | **TEAM DECISION — eight proposed above; say so if it is five** |

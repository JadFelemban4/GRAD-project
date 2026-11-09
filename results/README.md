# `results/` — Phase D, Phase D2, C4, the 29 September retrain, X1, X2 and Run 2

## Run 2 — the held-out validation of the three EPA engines: ALL THREE DROPPED (5–6 November 2026)

```bash
python -c "import json; d = json.load(open('results/EPA_VALIDATION/summary.json', encoding='utf-8')); [print(e, v['drop'], v['drop_rows'], v['governed_by'], v['labels']) for e, v in d['engines'].items()]"
# each engine: dropped or not, the rows that dropped it, the entry that governs it, its labels.
# Every row with its E, u_val and κ: results/VALIDATION_DECISIONS.md section Q (one script extracted it
# from the committed records, a second recomputed it: 3,423 comparisons, no discrepancy).
```

Its own experiment, with no agent in it. The four-engine test (decision 24) needed the Mazda
2.5 T, the Honda L15B7 and the Ford 2.7 TT to pass a held-out validation against EPA's test-cell data
before any of them could train. Run 2 is that validation: each engine's plant as Run 1 froze it
(`25437ba`, form A+B+C+D, no form passing in-sample, decisions 82 and 93) against the held-out rows, by
the contract committed before any fit (`ENGINE_THRESHOLDS.md`, version 5, with section I's version-6
rows), on the team laptop, one engine at a time, in the order Mazda, Honda, Ford (row 106). The runs of
F2, F3 and F4 each have outcome "ok", and their run records list nothing outside the allowlist; F1, the
Mazda's first run, crashed before writing any output (below). Commits: the Mazda's E1 `c3ff39e` and
F1 `768a90f` (the crash), the defect route of rows 144-145 (V `115300b`, V2 `3c5fa47`, X `3879805`,
K2 `cc9f906`), its E2 `1e5a54d` and F2 `4181eb6`; the Honda's E3 `30f6400` and F3 `580d39d`; the Ford's
E4 `d7b5fcb` and F4 `9140941`, with summary.json; the labels, L `52aab23`.

Section 7 drops an engine for an off d row (the contract, section 7). The rows that decided it, each E in
its row's unit against R:

| engine | dropped by | L1, housing temperature (K; R 9.9) | E4b (%; R 16.6) | E8 (%; R 16.6) | D1 (%; R 16.6) | governing entry |
|---|---|---|---|---|---|---|
| Mazda 2.5 T | E4b off, L1 off | 15.2977, **off**, κ 1.7168 | 74.1392, **off**, κ 6.1739 | 8.2135, untested, κ 1.9768 | 4.0659, limited (validated as computed; the cap) | `rows_rerun1.json`, the defect re-run |
| Honda L15B7 | L1 off, E8 off | 17.4417, **off**, κ 1.8714 | −20.7385, limited, κ 1.5180 | 158.8072, **off**, κ 11.4575 | 2.9623, validated | `rows.json` |
| Ford 2.7 TT | L1 off, E8 off | 34.9137, **off**, κ 3.7328 | 223.9956, untested, κ 26.0360 | 157.8508, **off**, κ 11.4056 | 3.7770, validated | `rows.json` |

- **L1 reads off on all three.** It is the only held-out test of the housing model the four engines
  share: every EPA housing carries the B58's c_turb, ua_gas_turb and ua_turb_amb (row 102's Disclosed).
  It had failed in-sample beyond its noise on all three as well (section I's note).
- **The level rows bind but never drop an engine.** E1a reads off on all three; the 850 °C level label
  reads off on all three (section Q.2).
- **Version 5 beside version 6** (section Q.4): version 5 has no reading of a summary cell that is not a
  finite number, so the Mazda's C3 is absent there, and E4b and L1 lie outside it: the Mazda is dropped
  under version 5 too. The Honda's and the Ford's records agree under both versions. No EPA engine
  survives under either.
- **The Mazda's two attempts** (section Q.3; row 144). Attempt 1 crashed in `d3_rows.read_summary` at a
  modal-fuel cell that is not a finite number (`EPA_VALIDATION/mazda_25t/crash_1.txt`), before writing
  any output: statistics were computed in memory and never written or seen. Attempt 2, the defect re-run
  on the fix X, reads every label limited at best by the contract's cap; the cap changed 7 label paths in
  `rows_rerun1.json`, 5 in `e6_rerun1.json` and none in `c3_rerun1.json`, and it changes nothing in
  section 7, whose drop is decided by off rows. 7 of C3's 43 tests had an empty modal fuel cell, each
  left out of the Direct2 check alone (`direct2_compared_n` 36).
- **The descriptive rows** (section Q.6), reported and gating nothing:

| engine | E1b | E1i (transient) | E2b | E3b | C3a / C4's fuel, hot | C3c / C4's air, hot |
|---|---|---|---|---|---|---|
| Mazda 2.5 T | 6.3546 % | −2.4517 % | 6.1172 % | 31.0571 K | −13.5443 % (C3a) | −8.4737 % (C3c) |
| Honda L15B7 | 8.3225 % | 4.4642 % | 7.7189 % | 27.3341 K | −7.0440 % (C4) | −8.9357 % (C4) |
| Ford 2.7 TT | 7.1232 % | 12.0202 % | 6.9588 % | 36.5898 K | — | — |

  The Honda's C4 on the Accord's fired segments reads fuel 12.3278 % and air 13.4586 %, descriptive, C4
  being the Accord's engine and not EPA's L15B7.
- **What follows, by rules written before Run 2** (the contract: "If no EPA engine survives, the
  four-engine test does not run, and the failed validations are reported as results"; row 107 (2)): the
  four-engine test does not run. No collapse on H/τ and no test of H/τ against H is claimed or
  computed. A B58 study across H follows, a declared exploratory study, never a test of the criterion
  (rows 146 and 147, section R): three arms, 20 seeds per arm, expected to read null (row 147 (7)), its
  across-H contrast predicted at about 3.4 points with an interval of about ±10-12 points (row 147 (6)).
- **The roads after Run 2** (R4, `34cca5b`, 6 November): with every EPA engine dropped the B58 alone
  gates version 6, and no slot fails, so decision 34's twenty stand as drawn; version 5, every engine
  gating, fails 58 of the 75 slots on the Ford at 7.102 % and redraws them (129 redraws, 22 slots at the
  cap). Version 5's set is reported and never scored (row 146 (1); `EPA_ROADS/redraws.json`).
- **Row 102's hand-written four-engine comparison**, computed on the drawn roads before Run 2
  (`EPA_ROADS/roads.json`, `report.grids`), is reported as computed and labelled "hand-written savings on
  plants dropped by Run 2's validation; describes the models, not the engines; never evidence for or
  against the criterion" (row 147 (9)). Its mean spread is 0.1566 on the H/τ axis and 0.0603 on the H
  axis for the four engines, 0.1699 and 0.1790 with the one-housing Ford beside them, and 0.0881 and
  0.0592 without the Ford (`B58H_DESIGN/power_b58.txt`).

**The sentence that may be said:** *"The three EPA engines' models, calibrated on EPA's test-cell data,
failed the held-out validation fixed before their fit: the housing-temperature row L1 read off on all
three, so the four-engine test of the H/τ criterion did not run."* Never "the H/τ criterion fails":
nothing about the criterion was tested. And never "the B58 is validated": it was never held out (section
I; `thesis/LIMITATIONS.md`, Run 2).

The full record: `results/VALIDATION_DECISIONS.md` section Q (labels, κ, drops, both versions) and
section P (the Mazda's defect route); `EPA_VALIDATION/summary.json` and each engine's records;
`SESSION_REPORT_2026-10-31_build-step-2.md` sections 13 and 14.

## X2 — wider air, 5 seeds a side, 1200 episodes: INCONCLUSIVE, not converged (11–13 October 2026)

```bash
python analyse_x2.py            # X2's preregistered test -> X2_RESULT.txt, X2_RESULT.json
python check_x2_convergence.py  # had the agents settled? -> x2_convergence.txt
python x2_agents.py             # what the agents did, and why X2 failed -> x2_agents.json (X2_AGENTS.md)
```

`PREREGISTRATION_X2.md`, committed `06f4686` before any X2 agent trained. X1's
plant and X1's roads, with the air widened (ambient 0–45 °C, pressure
80–101.3 kPa; `wide_air.py`), five seeds a side, about 22 times X1's training.
Four changes at once against X1, so X2 against X1 is descriptive (its section 2).

| reading | X2 |
|---|---|
| pairs (5 seeds a side) where preview helped | 1 of 5 |
| mean / sd of sighted − blinded, points of cut | −4.40 / 20.51 |
| effect below the MEI (5.43 points) — sign / permutation | 0.1875 (4 of 5) / 0.1875 |
| **cell**, total damage and thermal-only alike | **INCONCLUSIVE** |
| convergence, C4's rule at 720k/900k/1080k steps | **NOT-CONVERGED**: 0 of 5 sighted, 1 of 5 blinded, 0 of 5 pairs settled |

- **The sentence that may be said** (its section 6): *"INCONCLUSIVE on five
  pairs: the paired differences have an sd of 20.51 points, at which a test
  needs 143 seeds for 80 % power against the MEI. The agents were still changing
  at 1200 episodes."* Never "preview does not help".
- **Supervision, separately:** 7 of 10 beat `current-grade`; 4 of 10 do more
  damage than the baseline ECU on some frozen episode.
- **The logged-drive check:** 0 of 10 pass; with life weighted most, 59 of 60
  runs burn more than 1 % over the ECU car (median +6.92 %), more than X1's
  (`logged_check_wideair_dt1.json`). **The probe:** no agent passes.
- **Transfer, descriptive** (five episodes a condition, `conditions_wideair_dt1/`):
  held out, 8 of 10 beat that condition's `current-grade` at 50 °C, 6 of 10 at
  76 kPa (partly by refusing torque there) and 5 of 10 at 25 °C on the 21.75 %
  hill (X1: 26, 25 and 30 of 46); one agent does more damage than its baseline
  ECU (sighted seed 2, 25 °C).
- **Why it failed, measured after the result** (`X2_AGENTS.md`): the sighted
  agents use the preview in opposite directions on a climb training rarely drew;
  the policies never settled (practice cuts span 6.0–88.5 points along training);
  and the extra fuel buys off the baseline ECU's one-step knock spike at every
  jump in the torque request, charged by the untested knock model.

Every agent: `agents/wideair_dt1/README.md`. The scoring log:
`x2_score/SCORE_LOG.txt`. The full account: `PREREGISTRATION_X2.md` section 12.

## X1 — the extremes design, 23 seeds a side: SMALLER THAN THE MEI (8–9 October 2026)

```bash
python analyse_x1.py            # X1's preregistered test -> X1_RESULT.txt, X1_RESULT.json
```

`PREREGISTRATION_X1.md`, committed `75ca65f` before any X1 agent trained. X1
trains on the plant with the four steps agreed on 30 September (the thermal
network sub-stepped, the derived constants fingerprinted, the spark trim capped
at 0, every grade change ramped) and on decision 12's extremes design: ambient
25–45 °C, a speed target that changes mid-run, hills to 18 %. It changes many
things at once against 29 September, so X1 against the earlier sets is
descriptive (its section 2).

| reading | X1 |
|---|---|
| pairs (23 seeds a side) where preview helped | 10 of 23 |
| mean / sd of sighted − blinded, points of cut | −10.35 / 24.78 |
| effect below the MEI (5.43 points) — sign / permutation | 0.0173 (17 of 23) / 0.0027 — they agree |
| **cell**, total damage and thermal-only alike | **SMALLER THAN THE MEI** |

- **The sentence that may be said** (its section 6): *"Preview's effect on the
  locked climb is below the MEI (5.43 points of cut) for agents trained on the
  extremes design at 50 000 steps."* Never "preview does not help".
- **What it rests on:** a spread three times 29 September's, and six sighted
  agents (seeds 4, 13, 16, 17, 21, 22) and no blinded one that protect little
  on the scored climb, though they protected on their own training roads. That
  is post hoc, not a test.
- **Supervision, separately:** 39 of 46 agents beat `current-grade`.
- **The logged-drive check:** 1 of 46 passes; the agents deliver the torque and
  burn fuel protecting where nothing needs it (`logged_check_extremes_dt1.json`).
- **Transfer, descriptive:** held out, 30 of 46 beat their condition's
  `current-grade` at 25 °C on a 21.75 % hill and 26 of 46 at 50 °C; in range,
  29 and 42 (`conditions_extremes_dt1/conditions_test.json`).

Every agent: `agents/extremes_dt1/README.md`. The scoring log:
`x1_score/SCORE_LOG.txt`. The full account: `PREREGISTRATION_X1.md` section 12.

## The 29 September retrain — twenty agents on the merged plant

Ten seeds a side on varied roads, a record of the plant before the agreed
fixes; its agents are refused on X1's plant, correctly. Every table:
`agents/terrain_dt1/README.md`, and `agents/terrain_dt1/KNOCK_MARGIN.md` for the
spark-advance diagnostic.

## C4 — D2's design at 300 000 steps: SMALLER THAN THE MEI, not converged (24 September 2026)

```bash
python analyse_c4.py            # C4's preregistered test, D2 and Phase D beside it
```

`PREREGISTRATION_C4.md`, committed `79568e2` before any C4 agent trained. C4
changes ONE variable from D2 — the training budget, 50 000 → 300 000 steps —
by the team's rule: one variable at a time. Every C4 agent retraced its D2
twin bit for bit through 50 000 steps (`c4_identity.txt`, 80 of 80).

| | Phase D | Phase D2 | **C4** |
|---|---|---|---|
| budget | C1 | C1 | **300 000 steps** |
| seeds where preview helped | 5 of 8 | 4 of 8 | **3 of 8** |
| mean / sd of blind − sighted | +4.8 / 214.4 | +6.4 / 98.8 | **+30.2 / 139.9** (median −1.3) |
| effect below the MEI — sign / permutation | 0.6367 / 0.2578 (post-hoc) | 0.1445 / 0.1250 | **0.0352 / 0.3867 — they disagree** |
| **cell** | INCONCLUSIVE (post-hoc) | INCONCLUSIVE | **SMALLER THAN THE MEI** (primary test) |
| convergence | — | — | **NOT-CONVERGED** (`c4_convergence.txt`) |

- **The preregistered reading:** preview's effect is below the MEI at
  300 000 steps — (i) is supported AT THIS BUDGET; the agents were still
  changing, so (ii) is not ruled out.
- **It hangs on one seed:** 7 of 8 is the sign test's exact threshold, and the
  permutation test disagrees because seed 0 carries +360.6. Most seeds show no
  benefit from preview; one shows a large one.
- **The budget did not measurably change preview's effect** (5c, p = 0.6367).
- **Supervision, separately:** the sighted agent beats `current-grade` on the
  median in 8 of 8 seeds, the blinded agent in 7 of 8; on the worst episode it
  does not. No agent refuses torque (`c4_tracking.txt`).

The full account is `PREREGISTRATION_C4.md` section 11; the captured output is
`C4_RESULT.txt`.

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
- **Torque delivery, checked (`check_d2_tracking.py`, limit 10):** five agents
  burn less fuel than the baseline ECU, which is what refusing torque would look
  like — and none of them is refusing it. 0 of 16 track torque more than one
  point worse than the baseline. The D2 damage figures read as protection.

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

Every agent above is a **C1** agent. `train.py`'s usage block said, at the time:

```
python train.py --steps 50000  --seed 0   # C1: the first bad run
python train.py --steps 300000 --seed 0   # C4: a real run
```

*(The second line is now refused as written: with the default `--out` it would
resume a Phase D agent. C4 is `--steps 300000 --road random --out runs_c4`, and
its rules are `PREREGISTRATION_C4.md`. Corrected 23 September 2026. On
`GRA-test`, since 20 October 2026, both lines also stop at once without
`--engine b58`, which `train.py` requires: there is no default engine.)*

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
| `EPA_CALIBRATION/<engine>/` | Run 1's records of each EPA engine (build step 2; frozen at `25437ba`): its freeze record and fit records, the in-sample stage, E6's refit variants, T0 and the poison proof, the completion, and the check records. Written by `calibrate_epa.py`, never edited |
| `EPA_CALIBRATION/bounds_active_corrected.json` | decision 92's corrected bound lists beside the frozen ones, every fitted parameter's distance to its bound (rows 109 and 141), written once by `bounds_active_corrected.py write` in commit G; `bounds_active_corrected.py check` recomputes it. The frozen records keep their own lists |
| `EPA_VALIDATION/` | Run 2's records (its section above): each engine's `ARMED.json`, rows, E6 and D3 records and run record, the invocation logs, and `summary.json`. Written by `validate_epa.py`, never edited; `verify_docs.py` recomputes the Run 2 section's figures from them |

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

These are the commands as they ran, on the plant those agents trained on. On
`GRA-test`, since 20 October 2026, `run_phase_d.py`, `train.py` and `evaluate.py`
also require `--engine b58` (no default engine), and a Phase D or D2 agent is
refused there anyway: its `meta.json` is fingerprint schema 2.

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

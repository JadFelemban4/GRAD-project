# Validation plan: the simulator against the car

**DRAFT, 7 October 2026, for Jad and Ghassan to agree. Revised the same day
after Jad's review (section 12).** Nothing in it changes the plant, the reward,
the twenty frozen episodes or any published label. It proposes how the labels
should be computed, and it lists the decisions that have to be taken **before**
any label is recomputed: a required accuracy chosen after seeing the
comparison is the tuning this project has refused since mistake 12.

Every number below is printed by a script, named beside it:

```
python validate.py            the eleven-row validation table
python model_vs_data.py       the comparisons against the car
python validation_numbers.py  channel resolution, and how far an error moves the climb
python car_spark_boost.py     the car's spark under boost against the model's baseline
python timestep_study.py      u_num: the thermal model stepped 1 to 100 times finer
python damage_robustness.py   the frozen episodes re-scored under eight other damage rulers
python conditions_test.py     the twenty agents at other ambient temperatures and pressures
python damage_constants.py    every damage constant: what can set it, and the re-score (8 October)
```

The last five are new (7 October) and diagnostics only: none changes a hashed
plant file. `damage_robustness.py` reads the per-step records
(`eval_record.npz`), which are gitignored and live on Ghassan's laptop, the
machine that trained the twenty; it runs only there. `conditions_test.py` needs
the trained networks (`runs/terrain_dt1/`), also only there.

---

## 1. Why this plan exists

The page's scorecard calls each comparison *agrees*, *limited*, *untested* or
*not covered*. `make_page.py` says so in its own header: those statuses "are
assigned by reading each comparison". No tolerance was ever written down, so
two people could label the same row differently, and an examiner can ask what
"agrees" means and get no number.

Validation has standards for exactly this. This plan adopts two of them, one
for each half of the question.

## 2. The two standards, and how they fit together

| layer | standard | question | what it gives each comparison |
|---|---|---|---|
| top | **ASME V&V 40-2018**, or **NASA-STD-7009B** (pick one) | How accurate must the model be, for this use? | a context of use, a risk, a required accuracy |
| bottom | **ASME V&V 20-2009** | How accurate is it, against the car? | E, u_val, and the interval E ± k·u_val |

**V&V 20** (verification and validation in computational fluid dynamics and
heat transfer; our thermal model is heat transfer) defines the comparison:

- the comparison error **E = S − D**, simulation minus data;
- the validation uncertainty **u_val = √(u_num² + u_input² + u_D²)**: the
  numerical error, the error carried in from the model's inputs, and the
  measurement's own uncertainty;
- the model's real error lies in **E ± k·u_val**. When |E| is well above
  u_val, the model error is about E; when |E| ≤ u_val, the model error is
  inside the noise of the comparison.

**V&V 40** (or **NASA-STD-7009B**) sets how strict to be. Each use of the
model gets a *context of use*: the question the model answers. Its *risk*
combines how much the decision rests on the model (model influence) with how
bad a wrong decision would be (decision consequence). The required evidence
grows with the risk. V&V 40 was written for medical devices and is sold by
ASME; NASA-STD-7009B (March 2024) does the same job for any model, grades
credibility on a five-level scale (0 to 4), and is free. **Use one of the two,
not both.**

The sources are listed in section 11. This plan was written from summaries of
the standards; by this project's own rule (`REFERENCES.md`), open the
documents before citing them in the thesis.

## 3. The contexts of use

The simulator is used for four different things, and each needs its own
accuracy.

| id | question the model answers | quantity of interest | model influence | consequence if wrong | risk |
|---|---|---|---|---|---|
| **COU-1** | Which control policy does less damage on the locked climb, and does preview change that? (Phase D, the ablation and the supervision claim) | turbine housing and oil temperature over the episode; the knock integral | **total**: no sensor on the car reads turbine temperature | a wrong thesis claim | **high** |
| **COU-2** | Where does this component sit on the H/τ axis? | the turbine housing's time constant τ | total, and `c_turb` is assumed | the point is misplaced on the criterion's curve | **high**, softened by design (section 6, τ row) |
| **COU-3** | Does the locked climb need protection at all? | the baseline's peak turbine temperature against the 850 °C trigger | total | the experiment tests protection on a road that would not need it | **high** |
| **COU-4** | The live app's driver-facing estimate and alerts | turbine and oil estimates against their alert limits | high | a missed or false alert on a screen; nothing reaches the car | medium. A second deliverable, outside the thesis claim |

## 4. Required accuracy: PROPOSED, for the team to decide

These come from what an error would change, measured on the committed climb
(`validation_numbers.py`, sections 2 and 3).

<!-- RETIRED-OK: 920.1, 520.5 -- measured on the merged plant of 30 September; the plant of 8 October changes the damages, not the scale of the argument -->
**What a temperature error does to damage.** A uniform turbine error of
**+2.6 / −2.7 K** moves the baseline's damage (920.1) by the 50-unit minimum
effect of interest; for current-grade (520.5) it is **+4.8 / −5.4 K**. No
comparison could ever confirm turbine temperature to ±3 K, and no sensor
reads it at all, so **absolute damage figures cannot be validated, and the
thesis must state its damage claims as relative ones**: points of cut against
the baseline, and sighted-against-blinded differences in those points. A
uniform turbine error multiplies every policy's turbine damage by the same
factor, e^(ΔT/45): ×1.25 at 10 K. A cut in points is close to invariant to
that; a difference counted in damage units is not, because it scales with the
factor. Real model errors are not perfectly uniform, so this is approximate.

**So the minimum effect of interest has to move with it.** It is 50 damage
units (`results/PREREGISTRATION_D2.md`), an absolute amount: under a 10 K
uniform error a true 50-unit effect would read 40 or 62.5. Restated against the
baseline's damage on the merged plant, it is 50 of 920.1, **5.43 % of the
baseline's damage, i.e. 5.43 points of cut**. The next preregistration should
state it that way (decision 5).

Each required accuracy below comes from a consequence, written beside it,
because E is already known for most rows: the basis is the guard against
choosing an R to fit an E.

| proposal | required accuracy | basis |
|---|---|---|
| **R1** (COU-1, COU-3) | turbine-equivalent error **≤ 10 K** | keeps every policy's damage ratio within ×1.25, and stays under a third of the 33 K by which the climb binds (its peak turbine temperature, 883.0 °C, against the 850 °C trigger) |
| **R2** (COU-1) | oil temperature error **≤ 20 K** on the climb | the climb's oil peaks at 94 °C, far below its 135 °C knee; it takes **+23 K** of oil error to move the baseline's damage by 5.43 % of itself, the restated minimum effect |
| ~~R3~~ (COU-2) | **withdrawn** (review point 7) | τ has nothing on this car to be compared with: its only check is a literature band, and the step test recomputes C/UA rather than measuring it. COU-2's credibility rests on the design instead: the H/τ sweep spans `c_turb` over a factor of 75, so the claim does not depend on one τ |
| **R4** (COU-4) | to be set with the app's alert design | the oil alert sits at the 135 °C knee, where a 12 K miss matters; out of scope here |

**R1 carried to what the car can measure.** One input error at a time on the
locked climb, neutral action, frozen episode 1 (`validation_numbers.py`,
section 3):

| input error | peak turbine moves | damage moves | input error worth 10 K (R1), about |
|---|---|---|---|
| spark +0.75° / −0.75° | −5.76 / +5.81 K | −93.9 / +110.4 | **1.3°** of spark |
| lambda −0.01 (richer) | −6.08 K | −103.7 | **0.016** of lambda, rich side |
| lambda +0.01 (leaner) | −0.37 K | −7.7 | far larger; the climb runs at λ 1.00 |
| ambient +1 K / +5 K | +3.43 / +17.22 K | +67.1 / +398.8 | **2.9 K** of ambient |
| boost ceiling +3.4 kPa | +0.00 K | +0.2 | none: the climb runs at 174.9 kPa, below the ceiling |

The last column assumes the effect is linear in the error, which holds only
roughly. Two consequences matter at once:

- **One logged step of spark (0.75°) moves the climb's damage by about twice
  the minimum effect of interest.** Spark at the climb's operating point is the
  most sensitive input this model has.
- **The boost ceiling does not act on the climb at all.** Its 1600 to 2000 rpm
  miss (−20 %) matters for the training roads that run there, not for the
  scored climb.

**Does the ruler itself decide anything?** Every constant of the damage model
is a design choice, so the twenty frozen episodes of every policy were
re-scored under eight other rulers, one constant changed at a time
(`damage_robustness.py`, from the recorded steps; the published ruler
reproduces the committed damage to float32 precision):

| ruler | every agent beats current-grade | sighted minus blinded, 95 % interval |
|---|---|---|
| as published | 20 of 20 | +1.17 [−4.44, +6.78] |
| turbine scale 30 K / 60 K | 20 of 20 / 20 of 20 | +1.07 [−3.76, +5.91] / +1.37 [−4.24, +6.97] |
| turbine knee −25 K / +25 K | 20 of 20 / 20 of 20 | −0.04 [−5.68, +5.59] / +3.00 [−2.68, +8.68] |
| no oil term / oil ×4 | 20 of 20 / 20 of 20 | +1.17 [−4.50, +6.83] / +1.18 [−4.27, +6.62] |
| no knock term | 20 of 20 | −1.50 [−7.10, +4.10] |
| knock term ×4 (**post-hoc**, see below) | 20 of 20 | +7.21 [+0.89, +13.52], 8 of 10 seeds |

**The supervision claim survives every damage ruler. It does not survive
forbidding spark advance:** with the trim capped at zero, the median margin
over current-grade goes from +24.4 points to −1.8, and 9 of 20 agents still
beat it (`knock_margin.py`, `results/agents/terrain_dt1/KNOCK_MARGIN.md`).
None of these rulers touches the knock model the agents exploit; whether the
car has that spark margin is drive C's question.

The ablation stays inconclusive under eight of nine rulers. The ninth, knock
weighted four times, is one look among nine chosen after the result was known:
its exact two-sided Wilcoxon p is 0.0137, and corrected for nine looks
(Bonferroni) 0.12. **It is a post-hoc reading and must never be quoted as a
preview effect.** What it does show is where any preview value lives: on the
knock term, i.e. the one-second knock spike at the grade step (the merge
review's second finding; agreed step 4 ramps it away). The agents were trained
on the published ruler, so this tests the evaluation's sensitivity, not what an
agent trained on another ruler would learn.

## 5. Measuring the uncertainty (V&V 20)

### 5a. u_D, the measurement

| channel | smallest logged step | standard uncertainty from that step alone (step/√12) |
|---|---|---|
| spark angle | 0.75° | 0.22° |
| oil | 1 °C | 0.29 K |
| coolant | 0.1 °C | 0.03 K |
| ambient | 0.5 °C | 0.14 K |
| air mass | 1.11 g/s | 0.32 g/s |
| lambda | 0.01 | 0.003 |

This is resolution only. No sensor datasheet is available, so the true
accuracy is unknown and no better than this. Two further parts of u_D are
specific to how this car is logged and must be counted for each comparison:

- **Sampling.** The logger reads one channel per row in turn, so a channel's
  readings can be seconds apart and the rows between them are copies.
  Uncertainty is computed from the number of genuine readings, never from rows
  (AUDIT.md H4).
- **Time alignment.** Two channels compared at "the same moment" were read at
  different moments. On `7475b5d7`, 68 % of the target and actual ignition
  readings fall within 1 s of each other (`model_vs_data.py`).

### 5b. u_input, the model's inputs

- **Fuel** for the thermal replays is computed from measured air and lambda
  (air / 14.7 λ), so it carries the air channel's 1020 kg/h ceiling and
  lambda's 0.01 step.
- **Ambient** on drive B is the 42 °C fallback, not a reading
  (`t_amb_assumed`); at 3.43 K of turbine per kelvin of ambient on the climb,
  an assumed ambient is a large input uncertainty wherever it is used.
- **The constants derived from the logs** carry their fit's scatter: the oil
  fit scores 2.39 K on the drives it was fitted to and 3.18 K held out
  (`model_vs_data.py`).
- **`c_turb`** = 6000 J/K is assumed; it sets τ (COU-2).

### 5c. u_num, the numerical error: MEASURED FOR THE 1 s STEP

V&V 20 estimates u_num from a convergence study: the same case solved with a
finer and finer step, and the result's change measured. `timestep_study.py`
does this without editing `thermal.py`: inside its own process, each thermal
step is split into n equal sub-steps with the inputs held.

**At the 1 s step every published quantity is converged:**

| quantity | 1 s step (as shipped) | 50 sub-steps | u_num estimate |
|---|---|---|---|
| peak turbine on the climb, neutral policy | 883.00 °C | 883.02 °C | 0.016 K |
| damage on the climb, neutral policy | 920.1 | 917.4 | 2.7 units (0.3 %) |
| current-grade's cut | 43.42 % | 43.40 % | 0.02 points |
| `validate.py` row 8, drive10 oil, hottest 10 min | 97.04 °C | 97.11 °C | 0.07 K |
| `validate.py` row 11, drive10 coolant | 92.19 °C | 92.21 °C | 0.015 K |

The coolant's oscillation is real (2.14 K from one step to the next on the
climb, the sign flipping on every step) and **two sub-steps remove it
completely**. It sits around the right mean, and the turbine is heated by gas,
not by the coolant, so it barely reaches any quantity above. The 2 s step of
the H/τ sweep is section 5d.

**Why the coolant oscillates (review point 8, checked).** `validate.py`'s
"block step τ = 1.2 s" is not the block's thermal mass. It is the coolant
REGULATOR the fit produced: inside the heat-management valve's opening span
(2.85 K) the radiator's full conductance (about 3 560 W/K at 25 m/s with the
fan on) switches in, so with the coolant about 50 K above ambient the
radiator's heat changes by roughly 62 kW per kelvin, against a block capacity
of 36 350 J/K: an effective time constant of about 0.58 s
(`data/derived_params.json`; arithmetic, not a run). **Sub-stepping makes this
converge; it does not make it physical.** A 0.6 s regulator is a property of
the fit, not of the engine. `calibrate_thermal.py` fits these constants with
its own copy of the equations, stepped once per second, so when agreed step 1
lands, the fit must be re-run with the shared integrator and the fitted span
reported: if it stays this narrow, it says so; if it widens, the derived
thermal constants move, and that is a plant change.

The cycle model's crank-angle step (`plant.DTHETA_DEG`, 0.25° since AUDIT.md
H1) still needs the same check.

### 5d. u_num at the H/τ sweep's 2 s step: TOO LARGE FOR THE SWEEP

`generality_test.py` runs the sweep at dt 2.0. The same study at that step
(`timestep_study.py`, section C; 100 sub-steps is 0.02 s):

| quantity | 2 s step (as shipped) | 100 sub-steps |
|---|---|---|
| coolant swing on the climb, neutral policy | 10.32 K | 0.00 K |
| coolant mean on the climb, neutral policy | 90.33 °C | 92.84 °C |
| damage on the climb, neutral policy | 971.3 | 979.3 |
| current-grade's cut | 39.19 % | 39.41 % |

At 2 s the coolant is wrong by 2.5 K on average and swings 10 K, and a
policy's cut moves by 0.22 points on the step alone. The sweep's measured
preview effects are a few hundredths of a point (the results page, "Preview on
the H/τ sweep"), **ten times smaller than this numerical error**. So the
sweep's figures are not just unquotable by agreement: they sit inside u_num.
Agreed step 1 settles it.

## 6. The comparisons, one row each

E is today's value. The last column is what is still missing before a label
can be **computed**; no label is proposed here.

| comparison | serves | E today (script) | still missing for a computed label |
|---|---|---|---|
| Boosted MAP, inverted from air mass | COU-1, via charge temperature | median +1.9 % (`model_vs_data.py`) | u_D of the boost channel; how far a charge-temperature error moves the climb's turbine (not yet in `validation_numbers.py`) |
| Load, relative air filling | none | 1.44 % | **excluded**: a consistency check between two car channels that cannot see the breathing model (mistake 12) |
| Part-load spark | COU-1 at part load only | mean +0.00°, RMS 2.50° over 26 points, 30–75 kPa | outside the climb's operating point; see the next row |
| **Spark under boost** | **COU-1, the most sensitive input** | **car minus model −3.81°** (median of 31 genuine readings, 2000–4000 rpm, 140–240 kPa, five drives; standard error 2.07°, quartiles −9.62 to +3.01). In the climb's own cell (2400–3000 rpm, 165–185 kPa) 4 readings, −1.78° (`car_spark_boost.py`) | **By the rule in section 7 it is *untested*:** 2·u_val is at least 4.1° from sampling alone, against R1's 1.3°, so these readings cannot tell a good spark schedule from a bad one. The point estimate leans one way: read linearly at 5.8 K per 0.75°, −3.8° of spark is about **+29 K of turbine the model would be missing**. Drive C is the data that decides it |
| Enrichment, lambda | COU-1 | worst cell 0.033 lean, 3500–4500 rpm at long dwell | E in the cell that contains the climb (2706 rpm, where neither the model nor the car enriches) |
| Knock | COU-1, the knock term | correlation −0.119 over 14 318 paired samples; 404 target and 410 actual readings in 55 min | **untested by the rule**: a reading every ~8 s cannot resolve a retard that lasts 1–2 s. Drive C |
| Oil, long drive (drive10) | COU-1, COU-4 | median −1.6 K, but drive10 is in the fit; its hottest ten minutes miss by −12.0 K (`validate.py` row 8: 4.6 K of it the coolant, 7.3 K the oil node) | u_num is 0.07 K (section 5c); still the held-out value for drive10 itself. Against R2 (20 K) the climb's purpose may tolerate it; COU-4's oil alert will not |
| Oil on hard pulls (7475b5d7) | COU-1 | median +5.2 K; peak 102.6 °C against the car's 107 °C | u_input |
| Oil time constant | COU-1, weakly | 60.0 s against the car's 70–100 s (row 9, outside) | how far an oil τ error moves the climb's damage |
| Coolant | COU-1, through charge temperature and the oil node | drive10 median −0.6 K; 7475b5d7 +6.2 K; rows 10 and 11 inside | u_num is 0.015 K on row 11 (section 5c); how far a coolant error moves the climb's turbine |
| Gear ratios | COU-1 | 87.9 % of samples within 4 % of a published ratio | little; the climb runs 7th at 2706 rpm |
| Compressor ceiling | the training roads, not COU-1 | −20 % at 1600–2000 rpm; −7 to +7 % from 2000 rpm up | none for the climb: it does not act there (section 4) |
| Turbine time constant | COU-2 | 48.0 s, inside 40–120 s | **no required accuracy** (R3 withdrawn): the step test recomputes C/UA, and `c_turb` is assumed. COU-2's credibility rests on the design instead: the sweep spans `c_turb` over a factor of 75 so the claim does not depend on one τ |
| Operating region | COU-1, COU-3 | 2.77 % of logged moving samples reach the climb's operating point (2706 rpm, 175 kPa): **the point is in the data, in short pulls. Holding it is not**: no drive holds that load for minutes, and drive10, the real Taif climb, never reached the 850 °C trigger | **not covered by the rule, for the sustained hold**: the climb holds the point for twelve minutes, which no drive does. Every COU-1 and COU-3 result is an extrapolation in duration, and must say so |
| Turbine temperature itself | COU-1, COU-3 | none: no sensor | **never validated directly**. The largest structural limit; state it in Chapter 3 |

## 7. The label rules: PROPOSED

With **k = 2** (about 95 %) and the required accuracy R of the comparison's
context of use:

| label | rule |
|---|---|
| **validated** | \|E\| + 2·u_val ≤ R, with E measured on data the model was not fitted to |
| **off** | \|E\| − 2·u_val > R |
| **limited** | anything in between |
| **untested** | 2·u_val > R on its own: the data cannot tell a good model from a bad one |
| **not covered** | the context of use lies outside the conditions the comparison covers |
| **excluded** | the comparison cannot see the model (a perturbation of the parameter it claims to test does not move it) |

**The rules overlap, so they are applied in this order, and the first that
fits is the label** (review point 2): **excluded, not covered, off, untested,
validated, limited.** A row can be both *off* and *untested* (|E| − 2·u_val > R
while 2·u_val > R); a model that far outside its requirement is *off* however
noisy the data, so *off* comes first. *Untested* and *validated* cannot both
hold, since validated needs 2·u_val ≤ R.

A fitted comparison scored on the drives it was fitted to can never be
*validated*; it needs its held-out value.

## 8. The validation hierarchy

| level | parts | validated against | gap |
|---|---|---|---|
| component | spark map, lambda map, air path, charge temperature, gearbox, block node, oil node, turbine node, knock integral | the car's channels, where one exists | turbine node and knock: no usable channel |
| subsystem | the cycle model to exhaust temperature; the thermal network over a whole drive | the thermal replays (`car_thermal.py`) | exhaust temperature is not logged |
| system | the locked climb's damage ranking (COU-1) | nothing on the car can score it | outside the validation domain (2.77 %), and depends on unvalidated components |

The system level can only inherit credibility from the levels below it. The
thesis should say which components carry it and which do not.

## 9. Order of work

1. **Agree sections 3, 4 and 7** (the contexts of use, the required
   accuracies, the label rules and their order). Before anything is computed.
2. **The time-step study**: DONE for u_num (section 5c). Left for agreed step
   1: the shared integrator, and `calibrate_thermal.py` re-fitted with it.
3. **u_D and u_input per comparison**, computed in `model_vs_data.py`.
4. **The missing comparisons**: spark under boost is DONE
   (`car_spark_boost.py`; untested by the rule); lambda in the climb's own
   cell is still to do.
5. **The missing sensitivities** in `validation_numbers.py`: charge
   temperature, coolant, oil τ.
6. **Compute the labels** in `model_vs_data.py`; `make_page.py` reads them
   instead of typing them; `verify_docs.py` guards them.
7. **Drives C and A** widen the validated region (`logs/DRIVE_PLAN.md`): C for
   spark and knock under load, A for sustained heat and oil.
8. **One credibility statement per context of use**, on the chosen standard's
   scale, in Chapter 3.

## 10. Decisions for Jad and Ghassan

Ghassan's recommendation and Jad's review agree on every item; the last
column is for Jad's answer, one at a time. **Since 8 October the answers are
recorded in `results/VALIDATION_DECISIONS.md`**, one column each, with six more
decisions beside these seven: the damage formula's constants (8–10,
`results/DAMAGE_CONSTANTS.md`), where the per-step records live (11), and what
the conditions test of section 11 asks of the preregistration (12–13). This
table is the plan as Jad reviewed it; the sheet is where it is decided.

| # | decision | recommended | Jad |
|---|---|---|---|
| 1 | Standards | V&V 20 for the comparisons, **NASA-STD-7009B** for the risk side: free, general-purpose and current, so it can be opened and cited now, as `REFERENCES.md` requires. Until the library provides V&V 20, cite its method through the free OSTI overview and Oberkampf and Roy | pending |
| 2 | The four contexts of use | agree | pending |
| 3 | Required accuracies | R1 (10 K) and R2 (20 K) with their bases; R3 withdrawn; R4 waits for the app | pending |
| 4 | Section 7 | the label rules, their order (excluded, not covered, off, untested, validated, limited) and k = 2 | pending |
| 5 | Relative damage only | agree, and restate the minimum effect of interest as 5.43 % of the baseline's damage (5.43 points of cut) in the next preregistration | pending |
| 6 | Extrapolation | every COU-1 and COU-3 result is labelled an extrapolation **in duration**: the operating point is in the data, the twelve-minute hold is not | pending |
| 7 | Preregistration | fold this plan into the next preregistration (agreed step 5), so the required accuracies are fixed before the next training | pending |

## 11. Outside the trained conditions

Every agent trained, and was scored, at 42 °C, 101.3 kPa and a constant
130 km/h. Ambient and pressure are inputs of its observation, but they never
changed, so the network never learned what they mean. `conditions_test.py`
(results in `results/conditions_test.json`, the figure
`results/figures/conditions_test.png`) measures what the twenty agents do when
they change:

- **Seven conditions:** the trained air, then 25, 35 and 50 °C at sea level,
  and 90, 82 (about Taif's altitude) and 76 kPa (the climb's top) at 42 °C.
- **A speed target that changes during the run** (Ghassan's design): 130 km/h,
  then 115, 130, 110, 145, 120 and 135, at no more than 0.8 m/s². Delivering
  the torque each change asks for is the agent's job.
- **Each condition on its own hill:** the gentlest grade, searched from 6 to
  30 %, at which the baseline ECU peaks at the locked climb's severity
  (883 °C), so protection is needed everywhere.
- **Current-grade is the line every agent is compared with**, in points of cut
  against that condition's own baseline.
- Frozen episodes 1, 5, 9, 13 and 17; five episodes on the locked climb were
  re-run first and equal their committed scores (the harness check).

Pressure reaches the engine only through the boost ceiling and drag, so
altitude here is milder than real (the module's docstring lists what is left
out).

**The hills put the conditions in three engine regimes** (`--gears`, the
baseline on each hill). The peak-against-grade curves drop wherever the
gearbox kicks down: a lower gear means more rpm, less load per cycle and
cooler exhaust. So the gentlest hill that reaches 883 °C does not land in the
same gear everywhere:

| regime | conditions (hill) | on the climb |
|---|---|---|
| tall gears | trained air (8.25 %), 50 °C (7.50 %), 90 kPa (8.75 %) | 8th and 7th, about 2 100–2 500 rpm |
| like the locked climb | 35 °C (12.00 %), 82 kPa (12.00 %), 76 kPa (12.25 %) | 7th, 2 300–3 000 rpm |
| high rpm | 25 °C (21.75 %) | 5th, 3 700–4 800 rpm, where the baseline also starts to enrich |

Every difference between conditions is therefore partly the air and partly
the gear the hill forces.

**The results** (medians over the five episodes; *short* is the number of the
719 steps delivering under 95 % of the torque asked for):

| condition | current-grade cut | current-grade short | sighted over current-grade | blinded over current-grade | agents beating current-grade | agents short | sighted minus blinded, 95 % interval |
|---|---|---|---|---|---|---|---|
| trained air | 36.9 % | 122 | +23.6 | +13.5 | 19 of 20 | 5 | +7.0 [−0.0, +14.0] |
| 25 °C | 41.9 % | 1 | −5.3 | −6.2 | 6 of 20 | 1 | +0.2 [−53.4, +53.8] |
| 35 °C | 34.4 % | 1 | +24.8 | +18.4 | 20 of 20 | 2 | +3.5 [−7.4, +14.4] |
| 50 °C | 34.9 % | 123 | +20.7 | +13.3 | 19 of 20 | 9 | +5.0 [−8.7, +18.7] |
| 90 kPa | 52.0 % | 303 | +14.9 | −1.3 | 11 of 20 | 25 | +10.2 [−1.1, +21.6] |
| 82 kPa | 45.1 % | 14 | +20.5 | +22.0 | 17 of 20 | 24 | +3.7 [−11.7, +19.0] |
| 76 kPa | 57.6 % | 228 | +11.7 | +13.2 | 14 of 20 | 221 | −0.3 [−16.7, +16.0] |

What it shows:

1. **The yardstick itself fails on this speed profile.** Current-grade pulls
   boost by about 10 kPa on any grade, and on the 145 km/h stretch that leaves
   it short of torque for 122 to 303 of 719 steps in four conditions. The
   baseline is short for at most 13. Where current-grade under-delivers, part
   of its cut is not protection, so the margins over it understate the agents
   there. A fairer hand-written yardstick would protect without dropping below
   the torque target.
2. **In the trained air, warmer air and the locked climb's regime, the agents
   still protect, and deliver.** 19 or 20 of 20 beat current-grade in the
   trained air, at 35 °C and at 50 °C, with a median of 2 to 9 steps short.
   The cleanest comparison is 35 °C, where current-grade also delivers: 20 of
   20, +18 to +25 points.
3. **Cooler air on a 21.75 % hill, the farthest from training, breaks them.**
   This is 5th gear at 3 700–4 800 rpm, on a grade beyond the 14 % training
   roads. The agents fall 5 to 6 points below current-grade, and only 6 of 20
   beat it. Current-grade delivers there (1 step short), so the loss is real.
   Two agents fail outright while delivering their torque: blinded seed 6 and
   sighted seed 2 do about twice the baseline's damage, with the turbine
   housing above the trigger for over 460 s of the 720 s episode.
4. **In thin air, torque delivery breaks down.** At 76 kPa the agents are
   short for a median of 221 of 719 steps (the baseline 13), and at 82 kPa
   blinded seed 2 for 519. Their boost trims, learned at sea level, now push
   them below a boost ceiling that falls with the pressure. Current-grade is
   short at 76 and 90 kPa too. **In thin air neither the agents' cuts nor
   current-grade's can be read as protection alone.**
5. **The preview ablation is inconclusive in every condition:** every 95 %
   interval includes zero, on five episodes per agent.
6. **Most agents keep their spark advance; the ones that do not are the ones
   that fail.** *(Corrected 8 October: this said "every agent keeps its spark
   trim between +3 and +4° in every condition", read off the group medians,
   which stay at +2.6 to +4.0°.)* Agent by agent (`conditions_test.py`, each
   agent's median over its episodes), 45 of the 140 agent-condition cells sit
   under +3° and 12 retard. At 25 °C the two that retard deepest, blinded
   seed 6 (−6.86°) and sighted seed 2 (−5.63°), are the two that do about
   twice the baseline's damage. The per-step records show the mechanism
   (`show_record.py`): with spark retarded the engine needs more air for the
   same torque and burns later, so the housing runs hotter, with the knock
   integral far below any knock reason to retard.

For the next preregistration (decision 7), this is evidence, not a decision:

- agents trained in one air, at one speed and on grades up to 14 % do not
  carry over to high rpm on steep grades or to thin air;
- the training conditions should span what they will be judged in, with some
  conditions held out of training to measure transfer;
- torque delivery should be scored beside damage in every condition;
- the hand-written yardstick should be one that delivers its torque.

**Limits of this test:** five episodes per agent, one speed profile, an
altitude model milder than real, hills in different gears, and a yardstick
that is itself short of torque in four of seven conditions.

## 12. Jad's review, 7 October: how each point was handled

Jad reviewed the first draft in his own session (`VALIDATION_PLAN_REVIEW.md`).
All eight points were checked here before they were taken.

| # | point | checked | handled |
|---|---|---|---|
| 1 | "The supervision claim survives every ruler" needs its other half | right: no ruler touches the knock model the agents exploit | section 4 now says it survives every damage ruler and does not survive forbidding spark advance (+24.4 → −1.8 points) |
| 2 | the label rules overlap; section 10 does not list them | right: a row can be both *off* and *untested* | section 7 gives the order (excluded, not covered, off, untested, validated, limited); decision 4 is now section 7 as a whole |
| 3 | relative-only damage collides with the MEI, which is absolute | right: a 10 K uniform error turns a true 50-unit effect into 40 or 62.5 | the MEI is restated as 5.43 % of the baseline's damage (section 4, decision 5); R2's basis restated the same way |
| 4 | push all three scripts with the plan | right, and there are now five | the header lists all five, and which machine two of them need |
| 5 | the robustness table is nine looks; its one significant row is post-hoc | right, with one correction: the review's "about 0.09" corrects the rounded p of 0.01; the exact two-sided Wilcoxon p is 0.0137, so ×9 is **0.12** | the row is labelled post-hoc, never to be quoted as a preview effect |
| 6 | the operating point is in the data; the hold is not | right, and sharper than the draft | section 6 and decision 6 name the twelve-minute hold as the extrapolation |
| 7 | R3 has nothing to be checked against | right | R3 withdrawn; COU-2 rests on the `c_turb` sweep |
| 8 | the 1.2 s is the thermostat loop, not the block's mass | right: checked against `data/derived_params.json`, about 62 kW per kelvin inside a 2.85 K span against 36 350 J/K, an effective 0.58 s | section 5c explains it, and adds: sub-stepping converges it, it does not make it physical; re-fit `calibrate_thermal.py` with the shared integrator and report the span |

## 13. Sources

Read from summaries on 7 October 2026; open the documents themselves before
citing them.

- ASME V&V 20-2009, *Standard for Verification and Validation in
  Computational Fluid Dynamics and Heat Transfer*. Overview by its committee
  chair: <https://www.osti.gov/servlets/purl/1368927>; on interpreting its
  results: <https://asmedigitalcollection.asme.org/verification/article-abstract/2/2/024501/447645/Interpretation-of-Validation-Results-Following>
- ASME V&V 40-2018, *Assessing Credibility of Computational Modeling through
  Verification and Validation: Application to Medical Devices*. The FDA
  guidance built on it: <https://www.fda.gov/media/154985/download>
- NASA-STD-7009B, *Standard for Models and Simulations* (5 March 2024), free:
  <https://standards.nasa.gov/sites/default/files/standards/NASA/B/1/NASA-STD-7009B-Final-3-5-2024.pdf>
- NIST IR 8298, a survey of industrial verification, validation and
  uncertainty practice: <https://nvlpubs.nist.gov/nistpubs/ir/2020/NIST.IR.8298.pdf>
- W. L. Oberkampf and C. J. Roy, *Verification and Validation in Scientific
  Computing*, Cambridge University Press, 2010: the textbook treatment of the
  same comparison method.

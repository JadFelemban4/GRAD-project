# Validation contract: the three EPA engines and the table backend

<!-- written by python engine_thresholds.py from thresholds/document_template.md: never edit it by hand -->

**Version 5, written 23 October 2026 by its generator, `engine_thresholds.py`, before any fit:
version 4 with decision 77 written as the rule of the in-sample stage, and Ghassan's order of the
same day that Run 1 go ahead before Jad's column is filled recorded.** Decision 77
(`results/VALIDATION_DECISIONS.md` section H, adopted under Ghassan's delegation of 21 October as
every decision of that section is) counts an in-sample statistic against a form only when its
failure exceeds its sampling noise, |E_cal| − 2·u_stat > R, and lets one that does not fail and
whose 2·u_stat > R neither block nor pass (section 2.4). T0, the synthetic recovery of
`docs/build_step_2/PLAN.md` section 5.10, raised it: under version 4's criterion a form-A truth
climbed to A+B+C+D, because its in-sample E4b failed at every form from noise alone. No R, split,
population, statistic, convention or label rule moved, and no number of version 4's JSON. Section 14
says what changed, why, and what is open; version 4's own account, in the next paragraph and in
section 13, is kept as version 4 wrote it.

**Version 4, written 22 October 2026 by its generator, `engine_thresholds.py`, after the plant
changes of build step 2 and before any fit, and corrected seven times on 23 October, after each of
its seven reviews, of which the first, fourth and fifth raised decisions 73-76, written into section
H on the same day and adopted by the agents under the delegation of 21 October as every decision of
section H is: version 3 with the rule text of decisions 39, 57 and 73-76, and every code citation
moved to the tree it was written on.** No R or split of version 3 moved. Of the populations version
3 named, one moved: E8's dl is taken over the held-out Final rows that publish a λ, and ds over
those that publish a spark, each a subset of version 3's held-out High Load Final rows that needs at
least 3 rows (version 4's reading of decision 54, sections 3 and 4). Three things were written where
version 3 named none: the steps of a scored climb C5 is taken over (decision 73), the inputs of the
rows without a reading (decision 54), and the statistic details version 3 left open (decision 57).
The first is a population, and it narrows `docs/build_step_2/PLAN.md` section 7.4's reading of
version 3, every scored-climb step, to the steps outside a climb's transitions. C5's climb slots are
shared by the four cars (decision 75), and its redraw cap, its bound on discarded candidates and its
thin share are numbers of this file, chosen from no data (decisions 76 and 73). The statistics and
rule text decisions 39, 57 and 73-76 name changed; section 13 lists them, says why, and says what is
open. Version 3, written 21 October 2026 on `GRA-test` (`ef5e14e`), before any calibration, was
version 2 with decisions 36-38 applied, written by the generator, which is committed beside this
file. Version 1, written the same day, was reviewed the same afternoon. The review's 37 findings
were each reproduced, and every one that held was applied in version 2; section 11 lists them with
the verdict and the change. Version 3 applied decisions 36-38 of `results/VALIDATION_DECISIONS.md`
section G, adopted 21 October on Ghassan's delegation: b = MEI/6 per part (section 1.3), the
collapse test's equivalence margin the MEI (section 1.1), and an untested row as a preregistered
band (section 7); section 12 lists every change. Decision 35 asks that torque, fuel and
turbine-inlet temperature be checked "against held-out EPA points, with each required accuracy
derived from its consequence on the MEI (VALIDATION_PLAN.md's method) and committed before
calibrating; the table gates likewise" (`results/VALIDATION_DECISIONS.md:158`, answered 21 October,
both agree). Decision 28 lets an engine train on its table "only if it passes accuracy gates derived
from the MEI (fixed before the table is built for a new engine)" (`:151`). This file is both, for
the Mazda 2.5 L turbo (`mazda_25t`), the Honda 1.5 L L15B7 (`honda_l15b7`) and the Ford 2.7 L twin
turbo (`ford_27tt`), and for every engine's table, the B58's included.

`results/ENGINE_THRESHOLDS.json` holds the same contract for the scripts: every R, the split, the
populations, the held-out rows by table and spreadsheet row, a flat list `thresholds` of (engine,
row, kind, part, statistic, R, unit, rows, on failure), the B58 measurements behind every
coefficient, the D3 files C3 may read with their sha256, and the sha256 of every file of the
generator that printed a number here (`generators`) and of every step output it read
(`generator_inputs_sha256`). The few numbers version 4 reads from the plant code itself, which no
sha256 here covers (the neutral action, the shared rich slope, the B58's λ clip), are recorded as
values (`version_4.plant_values`). `calibrate_epa.py` and the validation and table scripts read it
and record its sha256 in every output. Both files are written by `python engine_thresholds.py`
(section 10), and neither is edited by hand.

**Nothing has been fitted.** In the sessions that wrote this file (version 2's; version 3's, which
turned version 2's scripts into the generator and ran it; and version 4's nine, of 22 October, of 23
October after its first review, of 23 October that wrote decisions 73 and 74 in, of 23 October after
its second review, of 23 October after its third, of 23 October after its fourth, which wrote
decision 75 in, of 23 October after its fifth, which wrote decision 76 in, of 23 October after its
sixth, and of 23 October after its seventh, each of which re-ran its last two steps; and version
5's, of 23 October, which re-ran the same two) no model was run on an EPA row and no
model-versus-EPA error was computed. `calibrate_epa.py` does not exist in the working tree version 5
was written in, and no script in the tree runs the cycle on an EPA table: the files that name the
EPA tables are `epa_map.py` and `test_epa_map.py`, which export and test them, and this file's
generator (`engine_thresholds.py` and `thresholds/`), which reads their structure; the generator
checks both as it writes this file. Other files name the per-engine folders (`data/engines/<id>/`)
for the engine records and their derived files, and none of them names an EPA table. Other sessions
were editing version 3's branch at the same time, and what they ran is not known to this file;
version 4 was written in a worktree of its own, and so was version 5. WP3's scripts,
`calibrate_epa.py` among them, exist uncommitted in the main working tree (branch `wp3-work`), and
T0, as reported to version 5's session, ran WP3's fitting procedure on synthetic rows and read no
EPA output (section 14); none of them, and nothing they wrote, is in the tree version 5 was written
on. The EPA tables were read for their structure only: speeds, manifold pressures, BMEP, λ, intake
and coolant temperatures, the fuel report, which columns are present, and each channel's range.
Section 9 lists everything that was seen.

> **Rule 0. Nothing in this file changes after any fit runs:** no R, split, population, statistic,
> convention or rule of the model form, for any engine, the B58's table included. A change after
> that point is a new contract; it is disclosed, and every result is reported under both.

## The thresholds

| row | what is compared | statistic | R | kind |
|---|---|---|---|---|
| E1a | brake torque at EPA's inputs, hot rows | worst deciding line's mean signed relative error | **1.9 %** | level |
| E1b | brake torque, fired rows | mean absolute relative error | descriptive (worth b at 12.3 %) | — |
| E1i | brake torque, High Load Initial rows (a transient) | mean signed error per line | descriptive | — |
| E2a | fuel flow (Coriolis meter), hot rows | worst line's mean signed relative error | **4.0 %** | level |
| E2b | fuel flow, fired rows | mean absolute relative error | descriptive (worth b at 16.6 %) | — |
| E3a | turbine-inlet gas temperature (TIT) at λ≈1, hot rows | worst line's mean signed error | **10.0 K** | level |
| E3b | TIT at λ≈1, fired rows | mean absolute error | descriptive | — |
| E4a | TIT, enriched hot rows | worst line's mean signed error | **10.0 K** | level |
| E4b | the λ lever (TIT change with λ) | pooled fractional error | **16.6 %** | d, part P2 |
| E5 | slope of TIT with MAP along rpm lines | pooled slope ratio − 1, two windows | descriptive; **the boost lever is untested** | — |
| D1 | the exhaust flow at the demanded torque | mean absolute relative error, fired rows | **16.6 %** | d, part P1 |
| L0 | the housing equivalent at the demanded torque | worst line, f bounded | **10.0 K** | level |
| L1 | the spread of that level across lines | largest minus smallest, f bounded | **9.9 K** | d, part P3 |
| E6 | every uncertain constant moved by its band | does each row move; the error worth R1 and worth b | labels | mistake 12 |
| E8 | the baseline ECU's λ and spark at the held-out Final rows | the change of the head-start pair they predict | **16.6 %** | d, part P4 |
| C1, C2 | road load; ratios, final drive, radius, mass | largest relative difference from the source | **1e-6** | identity |
| C3a, C3c | CX-9 on Argonne D3: fuel; air against the MAF, hot segments | mean signed error | descriptive | — |
| C3b, C3d | the same, fired segments | mean absolute error | **16.6 %** each | d, part P5 |
| C4 | D3 figures already seen | as printed | descriptive | — |
| C5 | the scored climbs' distance, outside their transitions (grade ramps, speed changes), from the threshold the gearbox applies (`shift_ceiling_nm`; the CVT's kickdown threshold) | \|demand/threshold − 1\| | **more than max(1.9 %, \|E1a\| + 2u_val)** | rule |
| S1a | the table's lever effects: λ −0.05, MAP −10 kPa, spark −0.75° | aggregate fractional error | **16.6 %** each | table, P6 |
| S1b, S1c | table torque; table air and fuel | 95th percentile of the relative error | **12.3 %**; **16.6 %** (screens) | table, P6 |
| S1d | table EGT level, knock integral and flag | MAE, p95, agreement | descriptive | — |
| S2a | the hand-written preview pair per horizon, practice episodes, table against exact cycle | change of the pair difference | **0.905 points** | table, P6 |
| S2b | pilot agents trained on the table, per horizon, scored on both | mean pair gap; median agent gap | **0.905 points** | table, P6 |

**Level** rows feed each engine's 850 °C sensitivity row of decision 33. A uniform level error
cancels from every cut and from d under K3 (section 1.2), so a level row never drops an engine.
**d** rows guard the verdicts; each belongs to one of the six parts of the budget (section 1.3).
**Table** rows decide whether an engine trains on its table. Section 7 says what every label does.

## 1. From the MEI to an R

### 1.1 What the thresholds protect

The four-engine test reports one verdict per engine and per horizon on d, the sighted-minus-blinded
difference in points of cut, never pooled. The collapse is tested on those per-engine estimates as a
cross-plant comparison declared in advance (decision 26, `results/VALIDATION_DECISIONS.md:149`). It
judges d against the minimum effect of interest, 5.43 points of cut (decision 5, `:55`). A model
error matters as far as it moves d at the MEI, or moves the housing temperature that the 850 °C
sensitivity row rests on.

**The collapse test's equivalence margin is the MEI, 5.43 points** (decision 37,
`results/VALIDATION_DECISIONS.md` section G, adopted 21 October). Two engines count as equivalent
only when the difference of their d lies within ±MEI; how that is tested, with the difference's seed
uncertainty and the two engines' model bands (section 7), is the preregistration's. The margin has a
consequence behind it, the valuation of decision 5; a margin chosen for what the seed budget can
confirm would be choosing R to fit E (the review of 20 October). With the six parts of section 1.3
at their limits and independent, a true d at the MEI reads 0.59–1.41 MEI, so the preregistration's
seed reasoning (decision 30) states its false-negative risk at d_obs = 0.59 MEI, not at the MEI
(finding 28). At about 20 seeds per arm the test can refute a collapse but will rarely confirm one
within the MEI, and the preregistration says so.

The method is `results/VALIDATION_PLAN.md`'s: each required accuracy comes "from what an error
would change", written beside it, "because E is already known for most rows: the basis is the guard
against choosing an R to fit an E" (`results/VALIDATION_PLAN.md:110-112`). For these engines no E
exists yet, and every R below is derived without one.

### 1.2 Four ways an error reaches d, and one way it reaches a housing temperature

**Level.** Under decision 33 (K3, `results/VALIDATION_DECISIONS.md:156`) each engine's knee is set
on its own calibrated plant, so that its baseline spends as long above the knee on its locked climb
as the B58's baseline spends above 1123 K (413 s on the current B58 plant,
`results/ENGINE_THRESHOLDS/ecu/k3_nominal.json`). A housing error that is the same at every
operating point raises the baseline's temperatures and the knee together. Every policy's turbine
damage, exp((T + e − K − e)/45 K) (`engine_env.py:972-978`, `damage_rate`), is then unchanged, and
the error cancels exactly from every cut and from d.

It does not cancel in the 850 °C sensitivity row of decision 33, which re-scores the records at a
fixed knee. The level rows (E1a, E2a, E3a, E4a, L0) are held to **R1, 10 K of turbine-equivalent
error** (decision 3, `results/VALIDATION_DECISIONS.md:53`; its basis at
`results/VALIDATION_PLAN.md:116`), as the gas-side and operating-point inputs to that row. They do
not certify a housing temperature: the gas a thermocouple certifies is not the gas that heats a
housing (E3, item 2), so **every absolute housing statement for an EPA engine is labelled not
covered, whatever the level rows read**.

The level cancels only where it is the same at every operating point. K3 sets the knee on the locked
climb, and d is scored on decision 34's roads (`results/VALIDATION_DECISIONS.md:157`). A level that
differs between the two acts on d as a knee shift: mechanism (c) below, gated by L1.

**d, (a) a lever's effect on the gas temperature** (E4b, S1a): the TIT change with λ, or with MAP.

- Suppose the model's lever cools the gas by a fraction ε more than the engine's. Then the head
  start a preview buys is ε larger, and so is the protection of both arms. For a policy that lowers
  the housing by ΔT, the cut is c = 1 − exp(−ΔT/s). Scaling every ΔT by (1 + ε) moves d by
  ε·(1 + ln(1 − c))·d to first order.
- |1 + ln(1 − c)| ≤ 1 holds **only for 0 ≤ c ≤ 1 − e⁻² = 0.865**. Version 1 said the best cut
  measured anywhere is 72.66; that is X1's best (`results/X1_RESULT.txt:14`). Under the 20.3 K creep
  scale, decision 8's preregistered sensitivity row, the median cuts are 91.3 and 90.2 %
  (`results/DAMAGE_CONSTANTS.md:49`), where the factor is |1 + ln(0.087)| = 1.44 and
  |1 + ln(0.098)| = 1.32. Cuts below zero occur too: X1's sighted seed 4 cuts 0.60 % on the exact
  plant and −0.87 % on the table (`fe_out/strand_repo-stats-timing.md:159`), and 4 of X2's 10
  agents do more damage than the baseline on at least one frozen episode (`results/X2_RESULT.txt:34`).
  At c = −1 the factor is 1 + ln 2 = 1.69.
- So **|Δd| ≤ ε·d only while both arms' cuts lie in 0–0.865**. Every d row carries that condition.
  Outside it, the part's band is multiplied by the realised max |1 + ln(1 − c)| (section 7).

**d, (b) the exhaust flow at the demanded torque** (D1, C3b, C3d, S1c).

- A preview of length H lowers the housing by f·ΔT_gas·(1 − e^(−H/τ)), with f and τ from the
  housing node (`thermal.py:275-285`, `ThermalNetwork._substep`). Its elasticity to the flow per
  housing runs from 1 when H ≪ τ (the head start ΔT_gas·ua_g·ṁ·H/c is proportional to the flow)
  down to 1 − f when H ≫ τ.
- The head start then decays over τ = c/(ua_g·ṁ/n + ua_a), which shortens as the flow rises
  (∂ln τ/∂ln ṁ = −f).
- The two effects oppose, so **|∂ln d/∂ln ṁ| ≤ 1** at every horizon. That includes decision 27's,
  which reach about the approach's time constant (about 130 s on the B58's flat); section J of
  `results/preview_ceiling.txt:52-68` runs H/τ up to 3.85. A flow error scales a housing lowering, so
  the cut-range condition of (a) applies here too.
- Changing τ alone at fixed H moved the committed preview ceiling by an elasticity of about
  0.36–0.81: section J's rows at H = 30, 100 and 150 s, from τ 39 to 60 s
  (`results/preview_ceiling.txt:52-68`; version 1 gave 0.38–0.81).

**d, (c) the housing level's spread across operating points** (L1). A level error that differs by Δe
between the knee-setting climb and a scored climb acts on the re-scored damage as a knee shift of
−Δe there. The committed records give d's response to a knee shift directly (step 4 of the
generator, `thresholds/knee_shift.py`, re-scoring the per-step records of `terrain_dt1`, the twenty
of 29 September, before the grade ramp, and `extremes_dt1`, X1, on the ramped plant, by the
published formula, which first gives back every committed damage to 1.4e-07). The largest slope
measured over shifts of ±5, ±10, ±25 and ±57 K, both sets, both damage readings, is **0.0905 points
of d per K** (`terrain_dt1`, knock term on, +57 K). At ±10 K the largest is 0.0671. Version 1 quoted
0.91 points per 10 K from one 57 K shift and called it the most (finding 37): it was the mean slope
of that shift, and it is still the largest slope measured, so it is the one used. This mechanism is
**additive**: it moves d by points, not by a fraction of d.

**d, (d) the baseline ECU's strategy** (E8). Every policy trims the same ECU, so version 1 called its
error common to both arms and "second order". It is first order, measured in section 1.5.

### 1.3 The budget: six parts, b = MEI/6 each

The model reaches d through six parts that err independently:

| part | what | d rows |
|---|---|---|
| P1 | the operating point and its flows at the demanded torque | D1 |
| P2 | the λ lever on the gas temperature | E4b |
| P3 | the housing level's spread across operating points | L1 |
| P4 | the baseline ECU's strategy at high load | E8 |
| P5 | the car | C3b, C3d (with the identities C1, C2 and the rule C5) |
| P6 | the table | S1a, S1b, S1c, S2a, S2b |

**Each part may move d, at d = MEI, by at most b = MEI/6 = 0.905 points** (decision 38,
`results/VALIDATION_DECISIONS.md` section G, adopted 21 October). It is per part. Version 1 had five
parts at MEI/5 each, and version 2 kept that valuation for six. Torque and flow were two of version
1's parts, and they counted the same flow twice (finding 17). D1 now measures their in-use
combination as one part, and the ECU's strategy (P4) and the level's spread (P3) are new.

- With all six at their limits, aligned errors add to 6b = 5.43 points (1.00 MEI), and independent
  ones to √6·b = 2.22 points (0.41 MEI).
- Decision 38 holds the aligned total at the MEI. With version 2's b = MEI/5, six aligned parts
  added to 1.20 MEI, enough to manufacture an effect of the size the test looks for. Every d-row R
  is therefore 5/6 of version 2's before it is rounded down: D1, E4b, E8, C3b, C3d, S1a and S1c 20.0
  → 16.6 %, L1 11.9 → 9.9 K, S1b 14.7 → 12.3 % and S2 1.086 → 0.905 points
  (`budget.version_2_at_mei_over_5` in the JSON; section 12).
- **Most rows scale a true difference** (D1, E4b, E8, C3b, C3d and the S1 rows). They cannot make a
  difference out of a null, and they can shrink or inflate a real one. With all six parts at their
  limits, a true d at the MEI reads anywhere from 0.59 to 1.41 MEI if the errors are independent,
  and from 0.00 to 2.00 MEI if they align.
- **Two rows are additive** (L1, and S2 in part P6): they can make a difference out of a null, up to
  b each, i.e. √2·b = 1.28 points independent or 2b = 1.81 aligned. Version 1's sentence "the model
  alone cannot carry a null difference up to the MEI" is withdrawn; it bounded the wrong risk
  (findings 17, 28).
- These bounds cover the six gated parts. They do not cover what no row gates: the knock model, the
  boost lever, λ at part load, the housing constants, the ECU's enrichment timing (section 8).

The fraction is a valuation, like the MEI itself: decision 38's, set before any fit, and every d-row
R is proportional to it.

With the bounds of section 1.2:

- **a lever:** ε ≤ b/MEI = 16.67 %, so **16.6 %**;
- **the flow at the demanded torque:** |Δln ṁ| ≤ **16.6 %**;
- **the level's spread:** Δe ≤ b/0.0905 = 0.905/0.09054 = 9.99 K, which gives **9.9 K**;
- **the ECU's strategy:** at most **16.6 %** of the head-start pair (section 1.5).

Requirements are rounded down, never up.

### 1.4 The propagation model is the B58, with its ECU in the loop: an assumption

Each engine's own sensitivities exist only once it is calibrated, and using them would let the
calibration choose its own requirements. **So every coefficient below is the B58's**, computed for
this contract on the B58 plant alone. Each engine's own coefficients are reported beside its
results, as descriptive values, and never move an R.

The run follows `validation_numbers.py` section 3 exactly (`validation_numbers.py:103-132`): the
locked climb, the neutral action, frozen episode 1, dt 1 s. It reproduces the committed figures: the
baseline's damage is 848.05 (848.1 in `results/DRIVE_C_RULE_NUMBERS.txt:42`), the peak housing
temperature 883.02 °C (`:42`), τ on the climb 47.3 s (`results/preview_ceiling.txt:27`), and the
housing node sits 0.142 of the way from the gas to the ambient (`results/DAMAGE_CONSTANTS.md:35`).

**Version 1 held spark fixed while the load loop moved MAP (finding 1).** In the environment the
baseline ECU schedules spark on the baseline's MAP (`engine_env.py:1283`, in
`SupervisoryTunerEnv.step`), and every policy takes that spark plus its trim (`:1310`). At the
climb the schedule is the knock-limited surface (`engine_env.py:177-201`,
`BaselineECU.knock_limited_spark` and `base_spark`), whose slope there is −0.144° per kPa. A
torque bias moves MAP, so it moves the spark too. Version 2 measures the response three ways and
uses the third, which closes every loop:

| a +1 % torque bias | MAP | spark | gas | exhaust flow | housing (B58 f) |
|---|---|---|---|---|---|
| at fixed spark (version 1) | −1.496 kPa | 0 | −1.026 K | −0.890 % | −1.943 K |
| along the ECU's schedule, ∂/∂MAP at the cell | −2.247 kPa | +0.32° | −3.309 K | −1.336 % | −4.435 K |
| **in the environment**, the cycle's torque × 1.01 for baseline and agent, medians over t 400–718 s | **−2.220 kPa** | **+0.323°** | **−3.305 K** | **−1.320 %** | **−4.440 K** |
| the same, × 0.99 | +2.276 kPa | −0.325° | +3.317 K | +1.353 % | +4.463 K |

The larger magnitudes are used: **3.317 K of gas and 1.353 % of flow per 1 % of torque.** That is
2.3 times version 1's housing response and 1.5 times its flow response.

| quantity | value | from |
|---|---|---|
| the climb cell (median over t 400–718 s) | 2706 rpm, 174.9 kPa, charge 330.1 K, spark 1.16°, λ 1.00, gas 1022.27 °C, exhaust flow 120.84 g/s, 335.5 Nm | the run |
| f = ua_g·ṁ/(ua_g·ṁ + ua_a) | 0.858 | 0.90 × 120.84 = 108.76 W/K against 18 W/K (`engine_specs/b58.toml:166-167`, [thermal]) |
| G = T_gas − T_amb | **980.27 K** | 1022.27 °C against the scored roads' 42 °C |
| the flat approach (2107 rpm, 65.7 kPa) | f 0.616, τ 127.9 s; flow −0.709 % per +1 % torque along the schedule | the run |
| λ −0.01, −0.02, −0.05, −0.10, −0.15 at the climb cell | gas −7.10, −13.99, −33.47, −62.18, −86.43 K | the run (the agents' λ trim reaches −0.15, `engine_env.py:980`, `ACT_LO`) |
| spark ∓0.75° | gas ±4.10 K, torque ∓1.17 % | the run |

**The housing equivalent is bounded, not taken from the B58's f (finding 16).** At steady state the
housing T_h = f·T_gas + (1 − f)·T_amb moves by f·ΔT_gas + f(1 − f)·G·Δln ṁ. f depends on the housing
constants and on the flow per housing, so the B58's 0.858 does not transfer (review of 20 October,
`review_0` issue 9). Version 1 bounded f for gas errors but used 0.858 for flows. Every housing
equivalent in this file is now the largest over 0 ≤ f ≤ 1:

- a gas error e alone: |e|;
- a flow error δ alone: G·|δ|/4, i.e. **2.451 K per 1 %** (f = 1/2);
- a torque bias, which moves both the same way: max_f [3.317·f + 13.27·f(1 − f)] = (3.317 + 13.27)²/(4 × 13.27)
  = **5.183 K per 1 %**, at f = 0.625. With the B58's own f it would be 4.463 K.

G is the B58's. It is larger than any EPA engine's thermocouple TIT over 42 °C even with the
mass-averaging offset added (the hottest, 900.8 °C, plus 100 K gives 958.8 K), so it errs tight.

### 1.5 The ECU's strategy, measured on the B58 (new in version 2)

Version 1 made E8 descriptive because the strategy's error "is common to both arms and enters d only
at second order". No run supported that (finding 10; mistake 24). This measures it.

Step 5 of the generator, `thresholds/ecu_shift.py`, shifts the B58 baseline ECU's output by Δλ or
Δspark whenever its load input exceeds 100 kPa (the ECU's step, `BaselineECU.step`,
`engine_env.py:394-414`, called at `:1283`). Every policy inherits the shift (`:1310-1316`, in
`SupervisoryTunerEnv.step`), as it would inherit an error of a fitted ECU. Under K3 the knee is
re-set so that the shifted baseline spends 413 s above it, as the unshifted one does above 1123 K.
The run is the locked climb, frozen episode 1, dt 1 s, with the four hand-written policies of
`check_premise.py`.

d itself needs agents, so the proxy is **the head-start pair**: current-grade minus reactive,
12.98 points nominal. The two policies differ only in when they protect. The preview pair
(predictive minus current-grade) reads −0.01 point on this road, which is why decision 34 replaced it
(`results/VALIDATION_DECISIONS.md:157`), so it cannot serve.

| ECU shift above 100 kPa | K3 knee | baseline λ, spark (median t 400–718 s) | head-start pair, points | change under K3 | at the fixed 1123 K knee |
|---|---|---|---|---|---|
| none | 849.85 °C | 1.000, +1.16° | 12.98 | — | — |
| λ −0.005 | 846.74 °C | 0.995, +1.17° | 12.32 | −5.1 % | |
| λ −0.01 | 843.96 °C | 0.990, +1.18° | 11.83 | −8.9 % | |
| λ −0.02 | 838.78 °C | 0.980, +1.16° | 10.87 | −16.3 % | +61.2 % |
| λ −0.05 | 826.27 °C | 0.950, +0.99° | 8.30 | −36.1 % | +133.0 % |
| λ −0.10 | 814.18 °C | 0.900, +0.31° | 4.56 | −64.9 % | +107.2 % |
| λ +0.005 | 852.01 °C | 1.005, +0.91° | 11.72 | −9.7 % | |
| λ +0.01 | 854.46 °C | 1.010, +0.66° | 10.47 | −19.4 % | |
| λ +0.02 | 859.69 °C | 1.020, +0.14° | 7.47 | −42.4 % | −74.9 % |
| λ +0.05 | 879.12 °C | 1.050, −1.56° | 2.39 | −81.6 % | −92.2 % |
| spark −3.0° | 888.06 °C | 1.000, −3.42° | 15.54 | +19.7 % | |
| spark −1.5° | 868.46 °C | 1.000, −1.11° | 14.07 | +8.4 % | −76.1 % |
| spark −0.75° | 858.93 °C | 1.000, +0.03° | 13.39 | +3.2 % | −54.2 % |
| spark +0.75° | 840.53 °C | 1.000, +2.29° | 12.23 | −5.8 % | +59.5 % |
| spark +1.5° | 831.62 °C | 1.000, +3.40° | 11.66 | −10.2 % | |

The thermal-only reading agrees with the total within 0.48 percentage points at every shift, so the
knock damage term barely enters the pair. Reading:

- **The strategy enters d at first order.** Every λ shift from the nominal 1.00 shrinks the pair. The
  cycle's EGT has a corner at λ = 1, and a leaner baseline knock-retards: its spark falls from 1.16°
  to 0.14° at +0.02. The lean side therefore runs through the knock model, which is untested.
- K3 absorbs most of what a fixed knee shows: at a fixed knee, spark −0.75° halves the pair, and
  under K3 it moves it by 3 %.
- **The error worth b (b/MEI, 16.7 % of the pair) alone:** λ +0.0086 lean or −0.0206 rich, by
  interpolation. For spark it is −2.6° by interpolation, or about +2.6°, extrapolated beyond the
  measured +1.5°.
- **E8 is expected to read untested on every engine.** EPA's λ is "Reference Only - Uncalibrated"
  (`data/engines/<id>/epa_channels.csv`). Referencing each cell removes its closed-loop offset, but
  the Ford's two cells disagree by 0.02 at closed loop (section 3). Taken as a uniform half-width,
  u = 0.012, and through the lean side's 19.4 % per 0.01 that alone is u = 22.4 % on E8. Then
  2u = 44.7 % > R. Section 7 carries E8's band into every engine's d.
- **The B58 is not exempt.** Its own spark-under-boost row reads car minus model −3.81° (median of
  31 readings; −1.78° in the climb's own cell, 4 readings; untested,
  `results/VALIDATION_PLAN.md:292`). Through this response that is worth +10.5 % to +25.9 % of the
  head-start pair. This is a projection through a proxy, not a measured error of any B58 d. It is the
  same order as b.

## 2. The held-out split (version 2)

### 2.1 The rule (fixed now, so the calibration cannot choose it)

1. A row's **nominal speed** is its measured speed rounded to the nearest 50 rpm. Every row lies
   within 25 rpm of it (`thresholds/split.py` asserts it).
2. An engine's **lines** are the nominal speeds of all its tables together: both Ford test cells,
   steady and high load. Speeds no more than 50 rpm apart are one line (the Ford's 1750/1800 and
   2200/2250, the Honda's 1700/1750/1800). A line is held out in every table at once, so no
   held-out speed is a calibration speed in another cell or table.
   - Version 1 ran the rule on each Ford cell separately (findings 4, 22). Cell 9 held out 2000 rpm
     while HD1's 2000 rpm line stayed in the calibration. HD1 held out 1500 and 2200 rpm while Cell
     9's 1500 and 2250 rpm lines stayed in. Three of the Ford's held-out lines then tested agreement
     between cells, not interpolation in rpm: in form A VE depends on rpm alone
     (`plant.volumetric_efficiency`, `plant.py:99`).
3. A line is **eligible** only if it is interior in the engine's union of lines, in its steady lines
   (if it has steady rows) and in its high-load lines (if it has holds): never the first or the last
   of any. Every held-out population then interpolates in rpm (mistake 6).
   - Version 1 held out the Mazda's 4500 rpm holds, its last high-load line (finding 23). Its
     highest high-load calibration line was then 4000 rpm, and the steady 5000 rpm line stops at
     9.3 bar and 123 kPa, against holds reaching 17.5 bar and 229 kPa.
4. Among the eligible lines in ascending order, those at positions o + 1, o + 4, o + 7, … are held
   out. The offset o ∈ {0, 1, 2} is chosen per engine by structure alone, in this order (findings 6,
   34):
   - a. at least 2 held-out lines with at least 3 high-load holds, where any offset allows it;
   - b. the most enriched hot rows usable by E4b (on held-out lines with at least 3 boosted λ≈1 rows);
   - c. the most held-out rows;
   - d. the lowest offset.
5. With a line go all its rows: steady rows, and high-load holds. Initial and Final are one hold,
   one spreadsheet row (`epa_map.py:20-21`).

### 2.2 What it gives

| engine | offset 0 | offset 1 | offset 2 | chosen |
|---|---|---|---|---|
| Mazda | 1500, 2250, 3000 (89 rows; 3 lines with ≥ 3 holds; 6 E4b rows) | 1750, 2500, 3500 (90; 3; 6) | 2000, 2750, 4000 (90; 3; 6) | **1**, by rules c then d |
| Honda | 1250, 2000, 3000, 4500 (107; 3; 13) | 1600, 2250, 3500 (50; 3; 7) | 1700/1750/1800, 2500, 4000 (91; 3; 12) | **0**, by rule b |
| Ford | 1250, 2000, 2500, 3500, 5000 (93; 2; 4) | 1500, 2200/2250, 2600, 4000 (77; 1; 5) | 1750/1800, 2400, 2750, 4500 (70; 1; 1) | **0**, by rule a |

| engine | table | rows | held out | calibration |
|---|---|---|---|---|
| Mazda | `epa_steady.csv` | 210 | 54 | 156 |
| Mazda | High Load Initial / Final | 61 / 61 | 18 / 18 | 43 / 43 |
| Honda | `epa_steady.csv` | 190 | 75 | 115 |
| Honda | High Load Initial / Final | 65 / 65 | 16 / 16 | 49 / 49 |
| Ford | `epa_steady_cell9.csv` | 180 | 63 | 117 |
| Ford | `epa_steady_hd1.csv` | 76 | 18 | 58 |
| Ford | High Load Initial / Final (HD1) | 19 / 19 | 6 / 6 | 13 / 13 |

That is 90 held-out rows of 332 on the Mazda, 107 of 320 on the Honda and 93 of 294 on the Ford,
counting the two windows of a hold as two rows. A High Load Initial row is held out with its hold but
enters only E1i (section 3). The JSON lists each row by table and spreadsheet row
(`engines.<id>.held_out_rows`).

The held-out lines, row by row (steady rows; holds; fired steady and Final rows, of which with a
fuel meter; hot; hot λ≈1, all with a meter; hot enriched; boosted λ≈1; throttled λ≈1):

| engine | line | steady | holds | fired (meter) | hot | hot λ≈1 | hot enriched | λ≈1 ≥ 100 kPa | λ≈1 < 100 kPa |
|---|---|---|---|---|---|---|---|---|---|
| Mazda | 1750 | 20 | 6 | 20 (20) | 11 | 10 | 1 | 12 | 7 |
| Mazda | 2500 | 18 | 6 | 18 (18) | 8 | 5 | 3 | 6 | 9 |
| Mazda | 3500 | 16 | 6 | 16 (14) | 8 | 6 | 2 | 7 | 7 |
| Honda | 1250 | 20 | 0 | 14 (14) | 0 | 0 | 0 | 5 | 9 |
| Honda | 2000 | 21 | 5 | 21 (21) | 8 | 5 | 3 | 10 | 7 |
| Honda | 3000 | 19 | 5 | 19 (19) | 9 | 5 | 4 | 11 | 4 |
| Honda | 4500 | 15 | 6 | 15 (15) | 6 | 0 | 6 | 3 | 6 |
| Ford | 1250 | 13 | 0 | 11 (11) | 3 | 3 | 0 | 5 | 6 |
| Ford | 2000 | 22 | 0 | 19 (19) | 6 | 6 | 0 | 15 | 4 |
| Ford | 2500 | 21 | 0 | 17 (17) | 9 | 6 | 1 | 10 | 4 |
| Ford | 3500 | 21 | 3 | 17 (17) | 5 | 1 | 3 | 4 | 9 |
| Ford | 5000 | 4 | 3 | 6 (4) | 3 | 0 | 3 | 0 | 2 |

What decides, at 3 clusters a line:

| engine | E1a | E2a | E3a, L0 | E4a | E4b (enriched rows) | D1 rows | E8 Final rows |
|---|---|---|---|---|---|---|---|
| Mazda | 1750, 2500, 3500 | 1750, 2500, 3500 | 1750, 2500, 3500 | 2500 | 1750, 2500, 3500 (6) | 52 | 18 |
| Honda | 2000, 3000, 4500 | 2000, 3000, 4500 | 2000, 3000 | 2000, 3000, 4500 | 2000, 3000, 4500 (13) | 69 | 16 |
| Ford | 1250, 2000, 2500, 3500, 5000 | 1250, 2000, 2500, 3500 | 1250, 2000, 2500 | 3500, 5000 | 2500, 3500 (4) | 68 | 6 |

Known now, from structure:

- The Mazda's E4a rests on one line (2500 rpm, 3 rows).
- The Ford's L0 and L1 rest on its steady hot rows at 1250–2500 rpm. Its high-load lines carry 1 and
  0 hot λ≈1 rows.
- E4b's λ = 1 reference is extrapolated in MAP, by the distance between a line's highest boosted
  λ≈1 row and its enriched rows:
  - Mazda: 0.0, 56.7 and 66.6 kPa;
  - Honda: 19.2, 16.4 and 62.6 kPa;
  - Ford: 21.2 and 30.0 kPa.
- The Honda now validates 3 of its 11 high-load lines and the Ford 2 of 6 (finding 34). The Ford's
  3500 rpm line is held out. Version 3 noted it beside the F-150's climb point from the vehicles
  strand (4th at 3470 rpm, UNVERIFIED), which amendment F3 supersedes: with the plan's constants the
  F-150 climbs in 3rd at η 0.92 (decision 44), so that point no longer describes it (version 4,
  after its seventh review).

### 2.3 What the calibration may use, and what only the validation sees

**The calibration may use:**

- every row of a non-held-out line, with EPA's calculated columns (BMEP, BSFC, BTE, the injector
  estimate, cam phases, the Atkinson ratio, the effective strokes). High Load Initial rows only for
  the full-throttle torque curve, labelled a transient peak; never their TIT, λ or (absent) fuel;
- ALPHA's full-throttle and closed-throttle curves (`epa_engine.json`), only at nodes whose
  `measured_at_speed` source row is a calibration row. Ten nodes sit on held-out rows and are removed
  (`engines.<id>.alpha_nodes_removed`):
  - the Mazda's full-throttle node at 1751 rpm (High Load Initial row 18) and closed-throttle node
    at 3501 rpm (steady row 152);
  - the Honda's full-throttle nodes at 1251 rpm (steady row 43), 2012, 3003 and 4502 rpm (High Load
    Initial rows 32, 48, 64), and closed-throttle nodes at 3000 and 4499 rpm (steady rows 117, 168);
  - the Ford's full-throttle node at 2000 rpm (Cell 9 row 80) and closed-throttle node at 1251 rpm
    (Cell 9 row 15).

  EPA's unmeasured nodes are model, not data, and are labelled so (mistake 6).

**Only the validation sees** every column of every held-out row.

**Neither uses** the ALPHA fuel map (it interpolates every row, held-out ones included), the Tier 3
and LEV III packages (other fuels), the Steady State with Transmission sheets (`epa_map.py` does not
export them), the SAE 2018-01-0319 Honda dataset, or any D3 file. Section 5 uses D3 blind; the CX-9's
and the Accord's gearbox constants were set from D3 on 20 October, and those figures are descriptive.

### 2.4 The model form, and the in-sample stage (finding 26)

Version 1 froze inputs and conventions but never named the model it validated, and rule 0 left no
legal way to change a form before the held-out statistics (mistake 20: suspect the form first).
Fixed now:

- **Form A, the base.** `plant.run_cycle` unchanged, with the engine's geometry and its fuel.
  - Fitted per engine on calibration rows: the breathing (VE's base, amplitude, centre and width,
    `plant.py:99`, `plant.volumetric_efficiency`), FMEP, the burn and delay constants (base and rpm
    terms), UA_PORT, the back-pressure law (to `Turbine Inlet Press` where published), and the
    knock scale (E6 row 7).
  - Shared and not fitted: `combustion_efficiency(λ)` (`plant.py:58-72`), γ(T), the
    residual-fraction law, t_head, the port pickup, t_residual, cp_exh and the Wiebe shape.
  - Fixed valve events (`plant.py:250`, in `plant.run_cycle`): no cam input.
  - The ECU: spark the lesser of a part-load map and the knock-limited surface, λ an enrichment
    schedule, both fitted to calibration rows.
- **The alternatives, in this order, each adding to the one before:**
  - B: VE in rpm and MAP (a linear MAP term);
  - C: a per-engine rich-side slope of `combustion_efficiency`, fitted on enriched hot calibration
    rows (the Honda reaches λ 0.61, beyond any B58 data);
  - D: the intake cam phase as an input to VE, through a schedule cam(rpm, MAP) fitted to EPA's
    `Intake Cam Phase` on calibration rows and run by the ECU. EPA's engines move their intake cams
    by 55–74° across the map (Mazda −74.3 to −0.3 CAD, `data/engines/mazda_25t/epa_channels.csv:24`;
    Honda −0.5 to 61.4, `data/engines/honda_l15b7/epa_channels.csv:26`; Ford Cell 9 −2.1 to 53.4,
    `data/engines/ford_27tt/epa_channels.csv:22`).
- **The in-sample stage.** Every gating statistic of section 4 is computed on the calibration lines,
  with the same definitions, populations and line minima. These are fit residuals and are never
  labelled.
  - **Each engine its own form** (version 4, decision 49). An engine's form is the first of A,
    A+B, A+B+C, A+B+C+D at which none of its own in-sample statistics but E8 (below) fails, by
    the rule below (version 5, decision 77; version 4 required |E_cal| ≤ R of each).
    If none does, its form is A+B+C+D, and the failing in-sample statistics are reported. The three
    EPA engines need not share a form, and each engine's form and its residual structure are
    reported (mistake 20).
  - **A statistic fails a form only when its failure exceeds its sampling noise** (version 5,
    decision 77): when |E_cal| − 2·u_stat > R, with R the row's (below) and u_stat computed exactly
    as for the held-out rows (section 3): the standard error of the mean with one row or hold per
    cluster, the pooled u_stat for a pooled row (D1, E4b), L0's at its maximising f, and L1's from
    its two extreme lines. **A statistic that does not fail and has 2·u_stat > R neither blocks the
    form nor passes it**, and is recorded so per form, as a statistic with no calibration line is
    (decision 55, below). One that does not fail and has 2·u_stat ≤ R passes. This is the held-out
    rule of section 3, under which a line decides off whatever its scatter and certifies a pass only
    if 2·u_stat ≤ R, applied with the sampling term the in-sample stage has.
    - **Version 5's two readings of decision 77**, written by the agents writing it and noted in its
      row; neither Ghassan nor Jad has seen them. A statistic with |E_cal| − 2·u_stat > R fails the
      form whatever its 2·u_stat: decision 77's second clause, "a statistic whose 2 u_stat > R
      neither blocks nor passes", is read as applying to a statistic that does not fail by its
      first, since decision 77 counts a failure that exceeds its noise and takes its rule from the
      held-out off rule; read literally, a statistic failing by more than R + 2·u_stat would block
      nothing whenever 2·u_stat > R. And a per-line row (E1a, E2a, E3a, E4a, L0) is tested on each
      calibration line that meets its population's line minimum, as each deciding line is held out:
      it fails the form if any line fails, passes if no line fails and at least one line has
      2·u_stat ≤ R, and otherwise neither blocks nor passes. Its worst calibration line is reported
      as before (section 3). Testing the worst line alone, the one with the largest |E_l|, would let
      a line that fails beyond its noise pass behind a worse but noisier one.
    - **Why** (section 14): T0 failed under version 4's |E_cal| ≤ R, a form-A truth climbing to
      A+B+C+D because its in-sample E4b failed at every form from noise alone, and a criterion that
      a statistic's own noise can fail adds terms no data asks for. The cost: a form whose in-sample
      errors lie within their sampling noise is not refused in-sample. The statistics that neither
      block nor pass are reported with the form chosen, and the held-out statistics then test that
      form once, under section 7's rules, which decision 77 does not touch.
  - **The R of the in-sample stage is the one this file states for each row.** L1's is 9.9 K: its
    tightening (section 4, decision 71) is measured on decision 34's roads, drawn on the frozen
    plants after the in-sample stage (the JSON's `order_of_work`), so a tightened R gates the
    held-out L1 only (version 4, written after its fourth review).
  - **E8 is computed in-sample and reported, but it is outside the form criterion** (version 4,
    decision 39(a)). Its inputs are the ECU fit alone, the model ECU's λ and spark at the Final
    rows, which no form A–D changes, so counting it would force A+B+C+D for a reason no form
    addresses. Its held-out row (section 4) is unchanged.
  - **An in-sample statistic with no calibration line** that meets its population's line minimum
    neither blocks a form nor passes it; it is recorded per form (version 4, decision 55). The
    held-out rule is unchanged: a d row with no statistic drops the engine (section 7).
  - The form and its constants are then frozen, their sha256 recorded, and **the held-out
    statistics are computed once**.

### 2.5 The plant in use (finding 27)

**The subset fit, on calibration rows only, is the plant that trains and scores.** Its coverage is
the calibration rows' (`engines.<id>.coverage.calibration_fired`, `.calibration_hot`, per 20 kPa
band of manifold pressure). Decision 34's scored climbs must lie inside it in speed and manifold
pressure, or they are labelled not covered. With this split the CX-9's locked-climb point (4th at
4173 rpm, UNVERIFIED) sits between the Mazda's calibration lines at 4000 and 4500 rpm.

## 3. How E is computed (fixed now)

- **Inputs fed to the model at each row.** These are EPA's `Speed`, `Intake Manifold Press`,
  `Intake Manifold Temp` (as the charge temperature), `Coolant Temp`, `Spark Timing` (as published)
  and λ (below). Everything else is the calibrated model's own, the back-pressure law included,
  because that is what the environment runs (`engine_env.py:1053`, `SupervisoryTunerEnv._evaluate`).
  On a form-D engine that includes the intake cam: the model ECU's schedule cam(rpm, MAP) at the
  row's MAP (decision 41), never EPA's `Intake Cam Phase`, which only the schedule's fit reads; D1
  evaluates it at its inverted MAP (section 4).
- **λ.**
  - **λ_ref** is the median published λ of a steady table's rows at 2–8 bar BMEP: that cell's
    closed-loop reading of an uncalibrated sensor. It is Mazda 1.000 (89 rows), Honda 0.990 (63),
    Ford Cell 9 0.980 (56) and Ford HD1 1.000 (19, the mean of its two banks). A high-load hold
    takes its cell's λ_ref.
  - **A row within 0.02 of λ_ref runs at λ = 1.00.** EPA's steady points "lie below the load where
    enrichment starts" (`CATALOGUE.md:150`), so the ECU is in closed loop there. E6 row 12 runs every
    row without this snap. The snap reaches 2 of the Mazda's 21 hot λ≈1 held-out rows, none of the
    Honda's 10 and 7 of the Ford's 16 (more than 0.005 from λ_ref).
  - **Every other row runs at λ_meas − (λ_ref − 1).**
  - The 0.02 is how far one engine's two cells disagree: the Ford reads 0.980 in Cell 9 and 1.000
    in HD1.
- **Rows that lack a reading, and censored λ (version 4, decision 54).** Each is a declared
  outcome, never a stop.
  - **A fired row without λ** runs at λ = 1.00, flagged, and every statistic is also reported
    without such rows.
    - It is in no λ band: the λ≈1 and enriched bands are defined on the row's own λ, and the split
      classifies such a row into neither (`thresholds/split.py`, `classify`). So it enters, at λ =
      1.00, the statistics of the fired and hot populations (E1, E2 and D1), and none taken over a λ
      band (E3, E4, E5, L0, L1).
    - In E8, which compares the model ECU with EPA's own λ and spark, it has no λ to compare: it
      enters ds only, and dl is taken over the Final rows that publish λ. The counts behind dl and
      ds are reported. **This is version 4's reading of decision 54** (written after its fourth
      review): read literally, "every statistic" would compare such a row's EPA λ as 1.00, a value
      EPA did not publish. So the dl that gates is the one without such rows, and dl with them, at
      1.00, is reported beside it, so that dl is reported both ways, as decision 54 asks of every
      statistic. dl needs at least 3 rows that publish a λ, or E8 has no statistic (section 4).
    - **A Ford HD1 row with either bank's λ empty is a row without λ** (version 4's reading of
      decision 54, written after its sixth review). The HD1 λ is the mean of its two banks
      (`thresholds/split.py`, `lam`), which then has none, and the split already classifies such a
      row into no λ band; one bank alone is not the λ every other HD1 row is given.
  - **A row whose published spark is EPA's sentinel**, exactly −120 (the Mazda's fuel-cut points
    read so, `epa_map.py:47-48`), enters no fit. In every statistic, in-sample and held-out alike,
    it runs at the model ECU's spark (30 s dwell, no knock retard, EPA's intake temperature, as E8
    runs the ECU), flagged, and every statistic is also reported without it.
    - In E8 it has no published spark to compare: it enters dl only, and ds is taken over the Final
      rows that publish a spark. Run at the model ECU's spark, it would add a difference of zero to
      ds by construction, which is no measurement and would pull ds toward a pass. **This is version
      4's reading of decision 54** (written after its fourth review): the ds that gates is the one
      without such rows, and ds with them, at a difference of zero, as decision 54 reads literally,
      is reported beside it. ds needs at least 3 rows that publish a spark, or E8 has no statistic
      (section 4).
    - In D1, which moves EPA's spark to the inverted MAP (section 4), it runs at the model ECU's
      spark at EPA's MAP, the spark it runs at in every other statistic, plus s·(MAP − MAP_EPA), so
      that D1 treats every row alike. **Version 4's reading of decision 54** (written after its
      fourth review); the other reading, the model ECU's spark at the inverted MAP, differs from it
      by the schedule's curvature over MAP − MAP_EPA.
    - **A row whose `Spark Timing` cell is empty is a sentinel row**: it enters no fit, and in every
      statistic, E8 and D1 included, it runs as above (version 4's reading of decision 54, written
      after its sixth review, its fit named after its seventh): it publishes no spark either, and
      version 3, which fed every row its spark as published, had no rule for it. Whether any fired
      row has an empty spark, or any HD1 row an empty bank, was not looked up when these two
      readings were written: the session that wrote them opened no EPA table, `epa_channels.csv`
      included, and each rule holds either way.
  - The held-out rows' counts of both are taken only when the held-out run is armed, before any
    statistic, and with them whether each of E8's subsets holds enough rows (section 4) is decided
    before E8 is computed.
  - **Censored λ** is defined on the calibration Final rows themselves, never on all rows: an
    engine's λ is censored when at least 2 of its calibration High Load Final rows sit at their own
    minimum λ within 1e-9, or at a documented sensor floor. Censored rows are kept, treated
    one-sided in the enrichment fit, and flagged in E4a and E4b.
    - **E8 lists them too, and gates nothing on the list** (version 4, written after its sixth
      review). E8's dl compares EPA's λ on the held-out Final rows, and a reading held at the
      sensor's floor sits above the λ the engine ran, which biases dl. A held-out Final row is
      censored when its engine's λ is censored and the row's λ sits at the censoring value, the
      calibration rows' minimum within 1e-9 or the documented floor. One whose λ reads below the
      censoring value is not counted censored: it shows that the sensor reads lower (after version
      4's seventh review). E8 lists the censored rows and reports dl without them beside the dl that
      gates; the list moves no label, R, population or statistic.
  - **A sensor floor is documented** only by a source, opened and cited before the fit, that states
    the lower end of the range of the λ sensor EPA used on that engine: EPA's report of that test,
    or the datasheet of a sensor the report names. With no such source, only the two-row test
    applies.
- **Fuel (finding 35).** Each table's own fuel sets LHV and AFR_st, from its fuel report's analysis
  (`epa_engine.json`, `alpha_fuel`, of that FTAG). AFR_st comes from the carbon weight fraction, with
  hydrogen the balance and the Tier 2 fuel taken as oxygen-free.
  - Mazda (FTAG 26864): 42.908 MJ/kg, AFR_st 14.559.
  - Honda (FTAG 25842): 42.898 MJ/kg, AFR_st 14.554.
  - Ford Cell 9 (FTAG 25278): 42.908 MJ/kg, AFR_st 14.557.
  - **Ford HD1, steady and high load, on FTAG 26864, the Mazda's batch** (the tables' `fuel_report`;
    `CATALOGUE.md:167`). Version 1 gave all the Ford's rows Cell 9's batch.
  - The plant and the thermal network take these per engine. Since build step 2 the fuel is the
    engine's `engines.Fuel`: it sets the cycle's fuel mass (`plant.py:220`) and heat release
    (`:233`) and the network's fuel heat (`thermal.py:255`), and `engines.with_fuel` moves both
    together. Every calibration and validation row runs on its own table's LHV and AFR_st,
    whatever fuel the engine's plant in use carries; the Ford's is decision 69's, which is not a
    rule of this contract. The B58 keeps its 44.0 MJ/kg and 14.7 (`engine_specs/b58.toml:201-202`,
    [fuel]), so its certificate holds. E6 rows 2–3 move to 14.7 and 44.0.
  - **The convention covers LHV and AFR_st**, the two `engines.with_fuel` moves, and not the
    octane, which is `engines.CycleCal`'s. How the Ford's Cell 9 rows, of another batch than HD1's,
    treat it is declared by the calibration scripts before they are committed
    (`docs/build_step_2/HANDOFFS.md`, WP3 item 5).
- **The calibration's air** is the fuel meter × AFR_st × that λ, on steady and Final rows only:
  High Load Initial carries no meter column for any engine.
- **Populations.**
  - *Fired:* BMEP ≥ 2 bar.
  - *Hot:* High Load **Final** rows, and the steady rows at or above the engine's lowest high-load
    manifold pressure (Mazda 109.6, Honda 124.7, Ford 136.2 kPa). This is EPA's own high-load
    region, the one its stab tests chose to show the engine's protection (`CATALOGUE.md:151`). The
    test roads (decision 34) are not drawn yet, and their operating point would come from the
    calibrated plant.
  - **High Load Initial rows enter no gating statistic (finding 21).** The Initial window is the
    peak torque within 2 s of reaching the target after a 1-s ramp from about 1/3 load
    (`logs/epa/README.md:101-104`): a thermal and sensor transient, set against a model whose port
    loss uses a wall temperature fixed by coolant (`plant.py:222`, `:343-344`). The richer Final
    window reads hotter: Mazda TIT 490.7–845.9 °C Initial against 554.9–900.8 °C Final, Honda
    583.6–752.7 against 610.1–779.4, Ford minimum 677.2 against 778.9
    (`data/engines/<id>/epa_channels.csv`). Initial torque is reported as E1i, labelled a transient.
  - *λ≈1:* |λ − λ_ref| ≤ 0.02. *Enriched:* λ ≤ λ_ref − 0.05, five counts of the 0.01 resolution, so
    no closed-loop reading counts as enrichment. Rows between the two bands belong to neither.
- **Lines and clusters.** A per-line statistic is computed on each held-out line with at least 3
  clusters in its population. A steady row is one cluster, and so is a hold, which now enters through
  its Final row alone.
  - A line decides an **off** label whatever its scatter.
  - It may certify a **pass** (validated or limited) only if 2·u_stat ≤ R: by decision 4's own
    rule, a line whose sampling alone would read untested cannot vouch for the model.
  - The row's label is off if any deciding line reads off. Otherwise it is the worse of validated
    and limited among the lines that read one of them with 2·u_stat ≤ R. If no line does, the row
    reads untested.
  - A pooled statistic (D1, E4b, E8, C3) follows the same rule with its pooled u_stat.
  - **A per-line row reports its worst deciding line's E, with that line's u_val and u_stat**
    (version 4, decision 57), and every deciding line is labelled and reported. The worst deciding
    line is the one with the largest |E_l|, as the level rows' statistics take it, and of two with
    equal |E_l| the one with the larger u_val (defined after version 4's fourth review, since C5's
    re-check margin reads it, section 5).
- **u_val = √(u_num² + u_input² + u_D²), V&V 20's three terms** (`results/VALIDATION_PLAN.md:53`).
  Version 1 added a fourth, u_stat, which widened u_val most where the model scatters most
  (finding 6). Each term is the uncertainty of the population's mean: random parts divided by
  √(clusters), common parts in full.
  - **u_num** is the standard deviation, over the population, of the change when `plant.DTHETA_DEG`
    is halved (E6 row 8). The mean of that change is absorbed by constants fitted at the same step,
    and the scatter is not.
  - **u_input** counts per-row input uncertainties. A common offset absorbed by the calibration, a
    cell's λ offset for example, is an E6 row instead. C3, which no calibration absorbs, carries its
    common terms here (section 5).
  - **u_D** comes from EPA's stated accuracy where its reports give one; the PDFs have not been read
    (`CATALOGUE.md`, section 5 item 12). Otherwise it is marked "u_D unsourced", and:
    - for a thermocouple, IEC 60584-1 class 2, ±0.0075·|t| taken as a uniform half-width, so
      u = 0.0075·|t|/√3 (3.5 K at 800 °C). The class is not stated for EPA's sensors, and the
      standard was not opened in this project; the resolution/√12 of version 1 gave 0.03 K
      (finding 34);
    - for λ, the Ford's inter-cell disagreement, 0.02, as a uniform half-width (0.012);
    - otherwise resolution/√12.
  - **u_stat**, the standard error of the mean with each hold one cluster, is reported beside u_val.
    It decides only whether a line may certify a pass.
- **Labels.** Decision 4 sets them, in its order: excluded, not covered, off, untested, validated,
  limited, k = 2 (`results/VALIDATION_PLAN.md:307-327`). A row computed on calibration rows is a fit
  residual and is never labelled validated (`:326-327`).
- **Every E and C row is labelled on its own comparison's domain:** the EPA held-out rows, or the D3
  segments. "Not covered" is read on that domain, which by section 2's interior rule the populations
  do not leave.
- **Coverage of the scored context is a separate per-engine flag (findings 3, 20).** It is reported
  beside every result and in the preregistration, and it never stands in for a label. Read as
  version 1 wrote it, every row was "not covered" for decision 34's roads, so "off" could never be
  reached and no engine could be dropped. The flag today:
  - **At 42 °C ambient the charge sits above every EPA map's intake temperature.** Fired rows reach
    55.0 °C (Mazda), 51.1 °C (Honda; its hot rows only 40.4 °C) and 47.0 °C (Ford). The B58's climb
    charge is 56.9 °C, and the rig held the Mazda's and the Honda's charge air at 30–40 °C
    (`CATALOGUE.md:153`). Version 1's Honda maximum, 65.5 °C, came from an unfired row (finding 31).
  - **Any hold longer than EPA's 30 s** (`CATALOGUE.md:151`) is an extrapolation in duration.
    Decision 34's climbs of 1–2 τ are 40–120 s.
  - **Above 115 km/h** the road load is not covered (C1).
  - Coverage is computed per population (fired, hot) and per 20 kPa band of manifold pressure, on
    all rows and on the calibration rows (`engines.<id>.coverage`), not as a product of independent
    ranges.
  - **Held-out rows outside the calibration rows' MAP coverage (decision 58)**, a reporting
    procedure of the validation script that moves no label, R, population or statistic, and not a
    rule of this file (section 13): each such held-out row is flagged, and every statistic is also
    reported restricted to the calibration coverage, beside it and never instead of it. The script
    reads the coverage from `engines.<id>.coverage.calibration_fired` and `.calibration_hot` in the
    JSON.

## 4. The engine rows

Every row except E6 is computed on held-out rows only, and every d row carries the condition that
both arms' cuts lie in 0–0.865 (section 1.2a).

**E1, brake torque at EPA's inputs.**

- **E1a: R = 1.9 %** (level). It is the worst deciding line's mean signed relative error over its
  hot rows. A +x % torque bias moves, in use, the gas by 3.317·x K and the flow by 1.353·x %
  (section 1.4). The housing equivalent is at most 5.183·x K, and 10 K / 5.183 = 1.929 %, rounded
  down. Version 1 had 5.1 %, from a fixed spark and the B58's f.
- **E1b: descriptive**, the mean absolute relative error over every fired held-out row. Its d
  consequence is gated jointly with the flow's by D1. Alone it is worth b at 16.67/1.353 = 12.31 %,
  i.e. 12.3 %.
- **E1i: descriptive**, the High Load Initial rows' torque per line, labelled a transient.
- *Tests:* the burn, friction and pumping work as calibrated, interpolated across rpm lines, at
  EPA's own spark and λ.
- *Does not test:* the knock model (spark is an input, and no knock is measured), the ECU's strategy
  (E8) or the charge-temperature model.

**E2, fuel flow against EPA's Coriolis meter** (`Fuel Meter Flow`), on steady and Final rows.

- **E2a: R = 4.0 %** (level). It is the worst line's mean signed relative error over its hot rows
  with a meter reading. A flow error alone moves the housing by at most G/4 per unit ln(flow),
  2.451 K per 1 %, and 10/2.451 = 4.08 %, rounded down. Version 1 had 8.3 %, from the B58's
  f(1 − f) = 0.122.
- **E2b: descriptive**, the mean absolute relative error over every fired held-out row with a meter
  reading. D1 is the d row; E2b is worth b at 16.6 %.
- *What it can and cannot see (mistake 12).*
  - The model's fuel is its air divided by AFR_st·λ (`plant.py:220`), and the calibration's air is
    EPA's fuel × AFR_st × λ, so AFR_st and λ cancel.
  - On held-out lines, E2 tests how the volumetric efficiency and the residual fraction interpolate
    across rpm, and nothing else. It cannot see the air path's absolute level.
  - E6 rows 1–2 move AFR_st and the λ convention and show this. The only independent air reading for
    any EPA engine is the D3 CX-9's MAF (C3d).

**E3, turbine-inlet gas temperature at λ≈1.**

- **E3a: R = 10.0 K** (level). It is the worst line's mean signed error over its hot λ≈1 rows: R1
  carried to the gas with f ≤ 1, since a gas error e moves the steady housing by f·e ≤ e.
- **E3b: descriptive**, the mean absolute error over every fired held-out λ≈1 row.
- *Like with like (mistake 23).* The model's gas temperature after the port loss
  (`plant.py:338-344`, in `plant.run_cycle`) is compared with EPA's `Turbine Inlet Temp`, a
  gas-side thermocouple at the turbine inlet, not the housing metal (`logs/epa/README.md:106-108`).
- *Tests:* how the calibrated exhaust relation (UA_PORT, the burn, the back-pressure law)
  interpolates across rpm lines.
- *Does not test:*
  1. **the housing.** No source measures it, for any engine (`CATALOGUE.md:686-689`). τ is assumed,
     and R3 is withdrawn.
  2. **the gas that heats the housing.** "Thermocouple readings sit roughly 100 K below
     mass-averaged port temperature … or about 20 K below the time-averaged value"
     (`REFERENCES.md:311`, the row "EGT cruise, min"; Caton, SAE 820050, `:664-667`). UA_PORT is
     fitted to the thermocouple, so for an EPA engine the model's "gas" is the thermocouple's
     reading. The B58's model gas is not: its UA_PORT is a typed 15 W/K anchored to no exhaust
     measurement (`plant.py:335-338`; `engine_specs/b58.toml:90`; `REFERENCES.md:432`, the row
     "`UA_PORT`, `CP_EXH`, `EXH_BACKPRESSURE_RATIO`", **CANNOT**), and its climb gas is 1022 °C,
     against EPA TITs of 723–816 °C at 2500–3000 rpm and 13–16 bar (`fe_out/design.md:180`). One set
     of housing constants is applied to two definitions of the gas (finding 36). So: **absolute
     housing statements for the EPA engines are not covered** (section 1.2), and **the 850 °C row is
     reported per engine and labelled not comparable across engines**. The K3 knees are per engine
     and unaffected.
  3. **the form of the port heat transfer.** UA_PORT is fitted to the same channel, so a held-out
     residual tests interpolation, not the form (mistakes 12, 20).
  4. **on the Ford, a twin-turbo engine read through one TIT channel**, from a bank not stated,
     UNVERIFIED (`logs/epa/README.md:108-111`). Version 1 cited `review_0` issue 10 here; that issue
     is about mistake 12.
  5. **any transient.** EPA published window averages only (`CATALOGUE.md:151`, `:690`).

**E4, the enriched holds.**

- **E4a: R = 10.0 K** (level), the worst line's mean signed error over its enriched hot rows (as
  E3a). The deciding lines are the Mazda's 2500 (3 rows), the Honda's 2000, 3000 and 4500 (3, 4 and
  6), and the Ford's 3500 and 5000 (3 and 3).
- **E4b: R = 16.6 %** (d, part P2), the λ lever's pooled fractional error.
  - Let L_S = S(the row's inputs at λ = 1) − S(the row's inputs): the cooling the model gives that
    row by enriching.
  - The model's error at λ = 1 at an enriched row is estimated as ê, from the line's least-squares
    line of the λ≈1 error against MAP over its boosted λ≈1 rows (steady and Final, MAP ≥ 100 kPa,
    at least 3), **evaluated at the enriched row's own MAP** (finding 9). Version 1 used the line's
    mean λ≈1 error, from rows 33–78 kPa lower on the Mazda's version-1 lines (the review's structure
    check, reproduced). A slope error at E5's version-1 limit, 20 % of the 1.473 K per kPa the B58
    shows along its schedule, then misplaced the reference by 0.295 × (33 to 78) = 9.7–23.0 K. The
    lever it measures is 62–86 K at λ −0.10 to −0.15 on the B58 (section 1.4), and those enriched
    rows sit 0.13–0.22 below λ_ref.
  - Then ε = ΣL_S / Σ(L_S + e_enr − ê) − 1, over the enriched hot rows of those lines.
  - The basis is section 1.3: ε ≤ b/MEI.
  - The reference line is extrapolated in MAP by the distances of section 2.2, reported per line.
    The estimate assumes the error is linear in MAP along a line; this is declared.
  - The Initial-to-Final pair estimate, Σ(ΔS − ΔD)/ΣΔD over the holds whose λ drops by at least
    0.05, is reported beside it, descriptive. Finding 9 asked to make it primary where a line has 3
    pairs; finding 21 shows the Initial window is a thermal transient, so its ΔD mixes the
    enrichment with the settling. Finding 21 governs.
- *Does not test:* λ at part load, where a head start is made. EPA has no enriched part-load point,
  so this is **not covered**: an extrapolation of the same equations to another operating point.

**E5, the slope of TIT with MAP along rpm lines: descriptive (finding 9).**

- The statistic is the pooled slope ratio minus 1, Σ_lines cov(MAP, S) / Σ_lines cov(MAP, D) − 1,
  over the λ≈1 rows (steady and Final) of held-out lines with at least 3 rows in the window.
  - **Window A** is MAP below 100 kPa and BMEP at least 2 bar: throttled, under the cells'
    97.2–98.6 kPa barometer, where a head start is made.
  - **Window B** is MAP of 100 kPa and above: boosted, the climb.
- It is no longer a gate. Along EPA's schedule spark and cams move with load, and on the B58 the
  slope along the ECU's schedule is 1.473 K per kPa against 0.686 at fixed spark: 53 % of it is a
  spark term. The agents' boost lever acts at fixed spark, since their spark follows the baseline's
  MAP, not their own (`engine_env.py:1283`, `:1310`, in `SupervisoryTunerEnv.step`). So E5 cannot
  isolate the lever its R was derived for. EPA has no spark sweeps (`fe_out/design.md:59`), so
  **the boost lever is untested for every engine** and is declared so (section 8).

**D1, L0 and L1: the engine at the demanded torque (finding 30).** E1–E4 run at EPA's MAP, but the
environment runs at the demanded torque (`engine_env.py:1076`, `SupervisoryTunerEnv._track_torque`).
A breathing error moves fuel and torque together and partly cancels there. So, per fired held-out
row with a meter reading:

- invert MAP so that the model delivers EPA's measured torque, by bisection over 20–400 kPa, at
  EPA's speed, intake temperature and coolant and the row's λ convention;
- run spark at EPA's spark + s·(MAP − MAP_EPA), where s is the engine's calibrated ECU's ∂spark/∂MAP
  at the row (central difference of `base_spark`, ±2 kPa), as the environment's ECU responds (the
  coupling of finding 1);
- there take δ_D = fuel_model/fuel_meter − 1 and e_D = TIT_model − TIT_EPA. The exhaust flow's
  relative error is δ_D, since the model and EPA share AFR_st and the λ convention.

A row whose torque the model cannot reach is listed and counted at the bound. **How (version 4,
decision 57):** the inversion pre-scans the model's torque over 20–400 kPa every 10 kPa and bisects
the first bracket, the first pair of neighbouring pre-scan pressures, from 20 kPa up, between which
the model's torque crosses EPA's, to 1e-3 kPa. A row with no bracket is evaluated at the nearer
bound, the end of 20–400 kPa at which the model's torque is nearer EPA's, and counted there: that D1
is the one that gates, in-sample (section 2.4) and held-out, and D1 is also reported without those
rows. On a form-D engine the intake cam is the model ECU's schedule cam(rpm, MAP) evaluated at the
inverted MAP, not moved linearly as the spark is (`docs/build_step_2/PLAN.md` section 6.3, D1's row;
decision 41). A row with EPA's spark sentinel runs at the model ECU's spark at EPA's MAP plus s·(MAP
− MAP_EPA), version 4's reading of decision 54 (section 3). Then:

- **D1: R = 16.6 %** (d, part P1), the mean |δ_D| over the fired held-out rows, pooled: Mazda 52,
  Honda 69, Ford 68. The basis is the flow mechanism of section 1.2b, |Δln ṁ| ≤ b/MEI. D1 is torque
  and flow as one part (finding 17), at part load as well as at the climb. D1 also bounds τ's
  flow-dependent part: at the B58's f, 0.858 × 16.6 % = 14 % of τ. τ's capacity and heat-transfer part
  is assumed (E6 row 4). COU-2 has no R (R3 withdrawn), so no row gates an engine's place on the H/τ
  axis. A level failure on E2a, or C3c's reading (descriptive), leaves the absolute flow unprotected
  beyond D1's 16.6 %.
- **L0: R = 10.0 K** (level), version 1's E7a computed directly. For each deciding line, take ē and
  δ̄, the means of e_D and δ_D over its hot λ≈1 rows with a meter: the rows common to fuel and TIT,
  and the population of E3a (finding 16). L0 = max over 0 ≤ f ≤ 1 of |f·ē + f(1 − f)·G·δ̄|, G =
  980.27 K, on the worst line. It is R1 applied to the sum the separate rows cannot see.
- **L1: R = 9.9 K** (d, part P3, additive), the level's spread. With H_l(f) = f·ē_l +
  f(1 − f)·G·δ̄_l, L1 = max over f of [max over deciding lines of H_l(f) − min of H_l(f)]. Its
  u_stat is that of the two extreme lines. It needs at least 2 deciding lines: Mazda 3, Honda 2,
  Ford 3. R = b/0.0905 points per K (section 1.2c).
  - **A tightening only, measured on the B58** (version 4, decision 71). On decision 34's roads,
    before any held-out statistic, the hand-written preview pair's slope against a knee shift is
    measured on the B58 plant, the plant of E8's tightening and of L1's basis (section 1.2c). If
    it is larger than 0.0905, R becomes b/that slope. An EPA engine's own slope is reported and
    never used: its coefficients would then move its R after its fit (section 1.4). The record of
    the tightenings names the plant it was measured on, and the held-out run refuses one measured
    on any other.

**E6, perturbation rows (mistake 12).** Each uncertain constant is moved by its band and every row is
recomputed.

- **The visibility probe is sized by its consequence (finding 3), not by the fit's own standard
  error.** It is the change of the constant that moves the engine's own in-use housing equivalent at
  its locked-climb cell by R1 (for level rows), or d by b (for d rows). Where neither is computable,
  it is ±10 %.
  - **Every d row's probe is ±10 % (version 4, decision 59).** d needs agents, and no EPA engine has
    one when the validation runs (the JSON's `order_of_work`: the agents train last), so the change
    worth b is not computable for any d row: "d rows: ±10 % (d needs agents)"
    (`docs/build_step_2/PLAN.md` section 5.9, item 6). Version 3's "where neither is computable"
    already gave it; decision 59 says it outright.
  - A row whose statistic moves by less than its own u_val under the probe is **excluded for that
    constant**: its pass certifies nothing about the constant.
  - That does not change the row's own label. A row excluded for every constant it claims to test
    (its *Tests* list) has no statistic and counts as such in section 7.
  - Version 1's ±(fit uncertainty) would have called a well-fitted UA_PORT invisible because it fits
    well.
- **The Tests lists, and how they are counted** (version 4, decision 59; amendment E4). The lists
  are decision 59's (`docs/build_step_2/PLAN.md`, section 9.1, decision 59), each member with the
  E6 row that perturbs it:

  | row | Tests list (the E6 row that perturbs each member) |
  |---|---|
  | E1a | the burn and delay constants (none), FMEP (none), the back-pressure law (row 5) |
  | E2a | VE (none) |
  | E3a | UA_PORT (row 6), the burn and delay constants (none), the back-pressure law (row 5) |
  | E4a | UA_PORT (row 6), the rich slope `ce_rich_slope` (row 9) |
  | E4b | the rich slope (row 9), the flame terms `flame_lam`, `flame_width` and `flame_floor` (row 9) |
  | D1 | VE (none), the burn and delay constants (none), FMEP (none), the back-pressure law (row 5) |
  | L0, L1 | UA_PORT (row 6), the back-pressure law (row 5), VE (none), the burn and delay constants (none) |
  | E8 | no list: never excluded |
  | C3b, C3d | VE (none), the driveline efficiency η (row 10) |

  - **The counting rule.** A row is excluded for every constant it claims to test only if every
    member of its list is perturbed by an E6 row and the row is excluded for each. A member no E6
    row perturbs counts as not excluded, because the held-out statistic tests it directly.
  - VE, FMEP and the burn and delay constants are fitted, and no E6 row perturbs them: rows 1 and
    2 move VE only through their refit, and a refit row labels no exclusion for it.
  - E8 has no list and is never excluded.
- **Load-bearing.** A constant whose band moves d by more than b, or the housing equivalent by more
  than R1, becomes a preregistered sensitivity row.
- E6 never drops an engine.

A row marked "refit" re-runs the calibration with the constant moved, because the constant enters how
the calibration reads EPA's data. For those rows the question is not whether a held-out statistic
moves, since the refit may absorb the change, but how far the model in use moves. **Version 4
(decision 59; amendment E2):** rows 1, 3 and 7 report every E row's change and how far the model in
use moves, and label no exclusion; in row 2, E2, D1 and L0 must each move by less than their u_val,
and a miss is reported as a finding, not a stop. Row 9 takes, in order, the bracket, the probe and
±10 %, and says for each bracket that cannot be computed why it cannot. **The refit rows'
calibrations (rows 1, 2, 3 and 7) run before the held-out run, at the frozen form, and their
held-out statistics are computed in that same single run** (`docs/build_step_2/PLAN.md` section
6.4 and decision 59), so no refit follows a held-out statistic (section 7).

| # | constant | band (source) | refit | what it must show |
|---|---|---|---|---|
| 1 | the λ convention | as published instead of cell-referenced, i.e. the offset λ_ref − 1: 0.000 (Mazda), −0.010 (Honda), −0.020 (Ford Cell 9), 0.000 (HD1); the snap kept (row 12 moves the snap) | yes | every E row's change and how far the model in use moves, with no exclusion label: the in-use hot TIT at λ = 1, the air and τ |
| 2 | AFR_st, moved in the calibration's air and the plant's fuel together | the table's fuel, 14.554–14.559 (the convention) → 14.7 (the B58's `engines.Fuel.afr_st`, `engine_specs/b58.toml:202`) | yes | the air +0.97 %, the exhaust flow +0.91 %, τ −0.78 % (B58 f), the housing level +1.08 K (B58 f), at most +2.22 K (f bounded). **E2, D1 and L0 must not move**: none of them can see AFR_st. Each must move by less than its u_val; a miss is reported as a finding, not a stop |
| 3 | LHV, in the cycle's heat release (`plant.py:233`, `plant.run_cycle`) **and** the thermal network's fuel heat (`thermal.py:255`, `ThermalNetwork._substep`) together, through `engines.with_fuel` | the table's fuel, 42.898–42.908 MJ/kg (the convention) → 44.0 | yes | every E row's change and how far the model in use moves, with no exclusion label: the in-use heat release per gram of fuel; the coolant and oil heat. Version 1 moved `plant.LHV` only, and the thermal network's 44.0e6 would not have followed (finding 19; mistake 25) |
| 4 | c_turb, ua_gas_turb, ua_turb_amb | × 0.75 and × 1.333 each. **Proposed by this contract**: X1 drew only the heat capacity on that range (`results/PREREGISTRATION_X1.md:119`) | no | τ moves by construction. No E row can see them, so every row is excluded for them by construction. Report τ, the 850 °C baseline peak and decision 34's ceiling at each end, flagged if the ceiling falls below 2 MEI |
| 5 | the back-pressure law | ± its fit's standard uncertainty (reported); the visibility probe as above | no | E1a, E3a and L0 must move under the probe |
| 6 | UA_PORT | ± its fit's standard uncertainty (reported); the visibility probe as above | no | E3a, E3b, E4a and L0 must move under the probe |
| 7 | the knock scale, assumed KI = 1 at the High Load Final spark | KI 0.90 and 1.10 (decision 21's ±0.10 KI) | yes | no E row can see it, since EPA publishes no knock data. Every E row's change and how far the model in use moves, with no exclusion label: the knock term's share of the baseline's damage, and d both ways |
| 8 | the crank-angle step | 0.25° → 0.125° | no | gives u_num |
| 9 | the other ASSUMED cycle constants (conrod, IVC, EVO, t_head, port pickup, t_residual, cp_exh, any burn constant not fitted, the flame terms `flame_lam`, `flame_width` and `flame_floor` among them: `engines.CycleCal`, `engine_specs/b58.toml:67-69` on the B58) and, from version 4 (decision 59), the rich slope `ce_rich_slope` | in this order: the bracket EPA's calculated valve channels give, where one exists (the Honda's effective strokes, the Mazda's Atkinson ratio, the cam phases), with why each bracket that cannot be computed cannot; else the probe as above; else ±10 % (±10 crank degrees for IVC and EVO). The rich slope: a probe under forms A and B, where it is the shared 0.65; under C, where it is fitted, ± its fit's standard uncertainty (reported) and the visibility probe as above, as rows 5 and 6. Under every form, exclusion is judged under the probe only: the change worth R1 for E4a, ±10 % for E4b and every other d row (version 4's reading of amendment E3, section 13) | no | the rows the calibration says each one sets must move. Report the error worth R1 and worth b |
| 10 | the driveline efficiency η, 0.92 | 0.86–0.98, the CX-9's apparent efficiency on D3 (seen); the Accord's 0.78 is UNVERIFIED | no | C3 moves. An η error is a torque bias of the same fraction: worth R1 at 1.9 %, worth b at 12.3 % |
| 11 | the charge temperature (E rows are fed EPA's measured value) | ±6.3 K, the B58's input uncertainty (`results/DRIVE_C_RULE_NUMBERS.txt:56`) | no | report the hot TIT and the test roads' hand-written cuts |
| 12 | the λ snap | every row at λ_meas − (λ_ref − 1), no snap (finding 11) | no | E3a, E5, D1 and L0 computed both ways; each gating row labelled by the worse, in the order off > untested > limited > validated (version 4, decision 59). D1, the one d row among them, enters its part's band with the larger κ of its two readings, each computed as section 7 computes it for its own label (version 4's reading of decision 59, which fixed the labels' order and not the band). E8 is unsnapped already, and its snapped reading is reported (decision 57) |
| 13 | the enrichment timing within a hold, which EPA does not publish | the ECU's dwell gate at 0 s and at 30 s, EPA's hold length (`CATALOGUE.md:151`) | no | **a preregistered sensitivity row of d for every engine** (finding 29) |

A ±10 % probe is a probe, not an uncertainty. Where a constant has no band, the row reports how large
an error would be worth R1 or b, as the plan's own table does (`results/VALIDATION_PLAN.md:125-131`),
and a reader sets that against whatever evidence exists.

**E8, the baseline ECU's strategy at high load: R = 16.6 %** (d, part P4; findings 10, 29).

- **The statistic.** dl is the mean signed difference between the model ECU's λ and EPA's λ, both
  cell-referenced, over those held-out High Load Final rows that publish a λ, and ds the same for
  spark over those that publish a spark (section 3, version 4's reading of decision 54, with dl and
  ds over every Final row reported beside them). The held-out Final rows number Mazda 18, Honda 16
  and Ford 6. These two subsets of version 3's population are the one population version 3 named
  that version 4 moves (section 13). The ECU is evaluated at the row's speed and MAP, with a 30 s
  dwell, no knock retard and EPA's intake temperature.
  - **EPA's λ is λ_meas − (λ_ref − 1), with no snap** (version 4, decision 57). Section 3's snap is
    a rule for the λ fed to the model, and E8 compares EPA's λ, which it feeds to nothing. The
    snapped E8 is reported beside it, descriptive; E6 row 12, which moves the snap, therefore does
    not list E8.
  - **Each subset needs at least 3 rows** (version 4's reading of decision 54, written after its
    fifth review): 3 clusters, a Final row being one, the least on which this file computes a line's
    statistic (section 3). **If either has fewer, E8 has no statistic, and the engine is dropped**
    (section 7). The term of a subset that is large enough, and dl and ds over every Final row as
    decision 54 reads literally, are then reported, descriptive. E8 is the sum of the baseline's two
    levers, and the term a short subset leaves out would read that lever as exact: the guessed
    baseline mistake 3 warns of. Taking it over every Final row instead would compare a λ of 1.00,
    or a spark difference of zero, that EPA did not publish. Version 3's one population never fell
    short (the counts above); the counts that decide the subsets are taken when the held-out run is
    armed (section 3), so the outcome is fixed before E8 is computed.
- **E8 = |P_λ(dl)| + |P_spark(ds)|**, where P is the measured relative change of the head-start pair
  under K3 for an ECU shift of that size: piecewise linear through section 1.5's table (both damage
  readings, the larger). Its u_val propagates u(dl) and u(ds) through P's local slopes: the slope of
  the segment that holds the shift, and at a shift of exactly 0 the steeper of the two segments
  beside it. A shift beyond the measured ones is extrapolated linearly from the last segment
  (`thresholds.contract.interp`), and flagged (version 4, decision 57).
- **A tightening only.** The same shifts are re-run on the B58 on decision 34's roads before any
  held-out statistic, and at each shift the larger response is used: the larger |·|, its sign kept
  (decision 57).
- dl and ds are also reported alone, with the error worth b (section 1.5), and so is where each
  engine's model ECU starts to enrich against EPA's Final rows: the lowest MAP per line at which λ
  falls 0.05 below λ_ref.
- **E8 in-sample** (version 4, decision 39(a)): computed on the calibration lines with this
  definition and reported, but outside the form criterion of section 2.4, since only the ECU fit
  moves it. It has no Tests list and is never excluded (decision 59).
- Section 1.5 expects E8 to read untested on every engine.
- It is reported, too, because a guessed baseline flatters every cut (mistake 3). The Ford's
  protection modes "are not controllable in the test cell" (`CATALOGUE.md:162`). Its baseline is
  therefore ASSUMED, and a sensitivity row over its TIT cap is preregistered (`review_0` issue 17).
- **The λ clip (finding 10).** The environment clips every policy's λ, while the baseline takes the
  ECU's λ unclipped. Version 3's environment clipped every engine to 0.70–1.25 (its `engine_env.py`
  line 1006, section 13); since build step 2 it clips each to its own `ecu.lam_floor` and
  `ecu.lam_ceiling` (`engine_env.py:1316`, in `SupervisoryTunerEnv.step`), 0.70 and 1.25 on the B58
  (`engine_specs/b58.toml:143-144`), version 3's values. Under the shared clip, an ECU fitted to the
  Honda's enrichment (λ 0.61 in its High Load windows) would run the neutral agent at 0.70 against
  the baseline's 0.61, so the neutral action would not be neutral (mistake 10).
  - Before any EPA engine's ECU is built, the floor is set per engine to min(0.70, the engine's
    deepest EPA λ, cell-referenced, − 0.01): Mazda 0.684 (deepest 0.694, an Initial row), Honda
    0.610 (0.620), Ford 0.698 (0.708).
  - **The neutral-action identity (version 4, decision 39(b); amendment E1).** Version 3 asked the
    neutral action to "reproduce the baseline exactly", which holds on no engine, the B58 included:
    the agent's trims are float32, its fan and pump are not the baseline's, and its charge
    temperature comes from its own thermal network. What can hold, and must:
    - The neutral action is `engine_env.neutral_action()`. Its spark, λ and boost trims rescale to
      exactly 0.0 in float32 (`SupervisoryTunerEnv._rescale`), and its fan and pump to 1.0.
    - **The identity:** at every step, the agent's λ equals float32(λ_b) and its spark
      float32(spark_b), where λ_b and spark_b are the baseline ECU's outputs of that step
      (`BaselineECU.step`, called at `engine_env.py:1283`). The sums λ_b + trim and spark_b + trim
      are float32 (`:1310-1316`), so the λ and spark channels can be identical at float32 and at
      nothing finer. Reported: the largest |difference| on each channel over the episode, which
      must be 0, and the clip contacts, which must be 0.
    - **A clip contact** is a step at which one of the two channel clips changed the value it was
      given: np.clip(x, lo, hi) ≠ x, for x = λ_b + trim against `ecu.lam_floor` and
      `ecu.lam_ceiling` (`:1316`), and x = spark_b + trim against `ecu.spark_min` and
      `ecu.spark_max` (`:1310-1311`). A value equal to a bound is not a contact, since the clip
      returns it unchanged. Build step 2's invariant 1 − enr_depth ≥ lam_floor (`engines.Engine`,
      `engines.py:603`) lets the baseline's deepest λ sit exactly on float32(lam_floor); counting
      equality as a contact would need that invariant strict, and it is not.
    - **The comparison is the environment's own, in float32.** A Python float bound is cast to
      float32 against a float32 sum (NEP 50); a NumPy float64 one would make the comparison, and the
      result, float64. The λ bounds are Python floats by `engines.Engine`'s own check
      (`engines.py:598-602`). The spark bounds have no such check: the B58's are typed in its spec
      as floats (`engine_specs/b58.toml:119-120`), and an EPA engine's are DERIVED, which
      `engines._number` converts to a Python float (`engines.py:1032-1035`). The identity check
      therefore asserts, before it runs, that all four bounds are Python floats (`type(x) is
      float`). A script that compares with float64 bounds counts float32(lam_floor) < lam_floor as a
      contact, and is wrong. So could the environment, if a spark bound were a NumPy float64: at a
      step where `BaselineECU.step` returns exactly spark_min, the clip would compare
      float32(spark_min), which can sit below spark_min, in float64.
    - **Only the two channel clips count.** The action box (`SupervisoryTunerEnv._rescale`,
      `engine_env.py:1031`), the slew and action-range clips and the spark-trim cap (`:1249-1251`)
      are not contacts: the slew moves the fan and pump by design after reset, and a change any of
      them made to a trim would show as a difference of the identity. The certificate harness's
      `HARNESS_BIND_COUNT`, which counts equality with float32(bound), is not this count
      (`docs/build_step_2/HANDOFFS.md`, WP2 item 2).
    - **Not compared:** the fan and pump, the neutral action's 1.0 each (slewed up from 0
      after reset, `engine_env.py:1223`), against the baseline's scheduled fan and default pump.
      With the agent's own charge temperature, they make the thermal trajectories, and with them
      the agent's MAP, fuel, gas and damage, differ by design.
    - **Where:** each EPA engine's locked climb (the completion, `docs/build_step_2/PLAN.md` section
      5.9 item 3); the B58's locked climb, which has no completion step, in the roads step, which
      changes `engine_env.py` and so runs a B58 certificate of its own (`docs/build_step_2/PLAN.md`,
      WP5); and every engine's test roads of decision 34 (the roads step). A difference or a contact
      is a coding defect (section 7).
  - Trims below the deepest EPA λ are an extrapolation of the combustion model (not covered).

## 5. The cars

The Supra keeps X1's road load in this test (decision 31, `results/VALIDATION_DECISIONS.md:154`).
That road load is 15–22 % under EPA's, from a re-implementation, UNVERIFIED
(`REFERENCES.md:785-788`, section 8's "the Supra's road load 15-22 % under EPA's"; version 1 cited
`:427`, the row "vehicle mass, `cd_a`, `crr`", finding 19); this is a declared limitation, not gated
here.

**C1, road load: R = 1e-6 relative** (CX-9, Accord, F-150).

- The statistic is the largest |F_model/F_EPA − 1| on a level road at EPA's test weight, 20 °C and
  98.21 kPa, at 15, 20, …, 115 km/h, against EPA's three-term target curve (the coefficients in
  `engine_specs/cars/<car>.toml`).
- The coefficients are the data, so this is an identity: anything above round-off is a defect
  (mistake 10).
- Above 115 km/h they are **not covered** (40 CFR 1066.305(a) states 15–115 km/h). Every test-road
  speed above 115 km/h is an extrapolation, and so is the locked climb's 130 km/h.

**C2: R = 1e-6 relative**, an identity, for the gear ratios, final drive, CVT range, mass and the
rolling radius. The radius is derived from EPA's N/V in top gear with the axle ratio (CX-9 0.3704 m),
never from D3, where it reads 0.3645 m, 1.6 % less (`fe_out/strand_vehicles.md:97`). A D3-measured
radius would make C3 partly in-sample (finding 8).

**C3, the CX-9 on Argonne D3, blind.** This is the Mazda only, the one engine whose driving data comes
from the same engine family.

- **The chain.**
  1. Take the measured wheel force (`Dyno_TractiveForce[N]`) and the car's own gear
     (`Trans_gear_actual_CAN[]`).
  2. Multiply by the N/V rolling radius and divide by the gearing and η to get the engine's torque
     demand. This holds only with the converter locked, so segments are filtered for it below.
  3. At the D3 car's measured speed and coolant, find the Mazda model's MAP for that torque, with
     its own ECU's spark and λ.
  4. The CX-9's D3 files carry no intake temperature, so the charge temperature is the
     environment's model at the cell's temperature. C3 is therefore also the one test of that
     model in the car.
- **The data.** The tests on the first fuel batch, 61704001–044: 43 files, pinned by sha256 in
  `d3_files_c3` and checked against the data folder's manifest. The 95 °F hot day falls inside that
  batch (`CATALOGUE.md:291`, `:296`).
- **Every C3 row is computed on segments** (findings 8, 25). Version 1 ran C3a and C3b on every
  10 Hz sample, so their E carried engine and driveline inertia, converter slip and multiplication,
  the A/C compressor's load and the fuel meter's lag. A segment:
  - lasts at least 3 s, with engine speed within ±25 rpm;
  - has the PCM MAP channel refreshed at least twice (it holds 3–9 samples at the 90th percentile,
    `CATALOGUE.md:662-663`);
  - has the **torque converter locked throughout**: `Eng_speed_CAN` within 1 % of
    `Trans_turbine_shaft_speed_TCM`, a speed ratio of 0.99, well inside the coupling phase. The
    CX-9's converter is "mostly slipping in 1st–3rd" (`fe_out/strand_vehicles.md:104`);
  - has the **A/C compressor off throughout** (`HVAC_ACComp_cycling_switch_PCM`);
  - stays in one gear, with coolant at or above the map's lowest (83.8 °C);
  - excludes padding rows (`CATALOGUE.md:654-657`). Every window is sized in seconds (mistakes 8,
    13b).
- **Populations.** *Hot:* the car's own PCM MAP (`Eng_ManifoldAir_pressure_sensor_PCM[kPa]`) at or
  above the Mazda's hot MAP floor, 109.6 kPa: data, not the model's MAP, which would let the model
  choose its population. *Fired:* the chain's demanded torque at or above 2 bar BMEP. A row decides
  with at least 3 segments and 2·u_stat ≤ R. Segments whose modelled charge temperature falls
  outside the Mazda's EPA intake-temperature range (37.3–55.0 °C) are not covered, and are reported
  apart.
- **The fuel.** The D3 fuel's heating value is 18,659 BTU/lbm (`CATALOGUE.md:291`); the EPA map's is
  18,447 (`epa_engine.json`, `alpha_fuel`). The model's fuel is scaled by 18,447/18,659 before the
  comparison, and the scaling is reported.
- **The channels are hypotheses (mistake 13).**
  - Before any comparison, `Eng_FuelFlow_Direct2[gps]` (not clipped) is integrated over each test
    and set against the summary's modal fuel; the difference enters u_D. The clipped
    `Eng_FuelFlow_Direct[ccps]` is never used (mistake 7).
  - **The MAF is checked the same way (finding 8):** against Direct2 fuel × AFR_st × λ, with λ =
    1/`Eng_equiv_ratio_b1_s1_PCM[]`, on closed-loop segments. Its u_D includes |r̃ − 1|, the median
    disagreement of the two. A flat maximum repeated across tests marks saturation, and those
    samples are dropped (mistake 7). The PCM MAF changes on only 15–57 % of samples
    (`CATALOGUE.md:662-663`), so it is read in seconds.
  - The PCM MAP channel's meaning is checked first too: a manifold sensor reads well below
    barometric at closed throttle (mistake 2 was a channel before the throttle).
- **Input uncertainty that no calibration absorbs.** η's span 0.86–0.98 around 0.92, uniform, is
  3.77 % on the torque demand; the N/V-to-D3 radius gap, 1.6 % uniform, is 0.92 %. Together that is
  3.88 % of torque, carried to the flow at the demand ×1.353: **u_input = 5.25 % on the fuel and the
  air**, common to every segment.
- **C3a and C3c, the hot bias of fuel and of air: descriptive.** 2u_input = 10.5 % alone exceeds
  E2a's 4.0 %, so as level rows they would read untested by construction (finding 25).
- **C3b: R = 16.6 %** (d, part P5), the mean absolute relative error of the model's fuel over the
  fired segments (the flow at the demand, as D1).
- **C3d: R = 16.6 %** (d, part P5), the same for the model's air against the car's MAF
  (`Eng_mass_air_flow_PCM[gps]`). **This is the only test of the air path itself for any EPA
  engine**, and it sees what E2 cannot.
- The D3 car is not EPA's vehicle, and whether it carries the same engine calibration is UNVERIFIED
  (`CATALOGUE.md:289`). That difference sits inside u_val, and becomes a limitation if C3 reads
  limited.

**C4, the D3 figures already seen: descriptive only.** From the vehicles strand of 20 October
(`fe_out/strand_vehicles.md:15-19`, `:120`):

- the CX-9's gear agreement: 84.2 % exact, 97.2 % within one gear, 96.3 % within one on held-out
  US06 and the grade tests;
- the Accord's CVT law: a median engine-speed error of 117 rpm, in-sample;
- the CX-9's kickdown at 0.99 of T_wot;
- apparent driveline efficiency of 0.78 on the Accord and 0.86–0.98 on the CX-9.

The Accord's D3 engine is not the EPA L15B7: 143 kW against 130 kW, CR 10.3 against 10.6
(`CATALOGUE.md:681`). Its chain is run as C3 but reported as descriptive. The F-150 has no D3 data,
and its shift schedule rests on a sibling truck with the 3.5 L engine and the same 6R80 gearbox, so
beyond C2 its gearbox is **untested**.

**C5, gear robustness, a rule for decision 34's roads, all four cars.** On every scored climb the
demanded torque must sit more than m = max(1.9 %, |E1a| + 2u_val) from the threshold the car's
gearbox applies. That is E1a's R, or the torque error the validation actually leaves when E1a reads
worse, since a level row never drops an engine. Then a torque error the validation accepts cannot
change the gear the climb is driven in. A one-gear change moves rpm by a whole ratio step, far
outside every R here. The B58 has no E1a and uses 1.9 %.

**The threshold is the one the code applies (version 4, decisions 70 and 40).** Version 3 wrote
SHIFT_LOAD·T_wot, or the CVT law's λ·T_wot. Neither is what the gearbox does, and on the B58's own
locked climb the literal formula would read the gear the box holds as a kickdown (amendment F2 of
`docs/build_step_2/AMENDMENTS.md`).

- **A stepped box** (the Supra, the CX-9, the F-150). `Vehicle.gear_for` (`engine_env.py:598-633`)
  starts at the highest gear the road speed allows and hands one back while the demand
  f·r/(ratio·η) exceeds `Vehicle.shift_ceiling_nm(rpm)`, the lesser of SHIFT_LOAD·PEAK_TORQUE_NM
  and the deliverable-torque table at that gear's engine speed (`:545-548`). The held gear's demand
  must sit more than m below its ceiling, unless its next lower gear is barred (below), and each
  rejected higher gear's more than m above its own, each at the engine speed `gear_for` computes
  for that gear.
- **A downshift barred by SHIFT_RPM_MAX** cannot be caused by a torque error. The bar applies
  whenever the next lower gear's engine speed, as `gear_for` computes it, exceeds SHIFT_RPM_MAX
  (`:630-631`), whether or not the held gear's demand exceeds its ceiling: `gear_for` keeps the held
  gear either way, by its ceiling test or by the bar, so no torque error can hand it back. The held
  gear's own margin then does not gate. It is reported beside the bar's rpm margin, the lower gear's
  engine speed minus SHIFT_RPM_MAX, in rpm and as a fraction of SHIFT_RPM_MAX (positive while the
  bar holds). The rejected higher gears are still checked, as for a held lowest gear (below). A
  script must not follow `gear_for`'s control flow here: there, a held gear whose demand sits under
  its ceiling never reaches the bar's test, and would be gated as an ordinary hold. Amendment F3's
  CX-9, whose 3rd gear is barred on its locked climb as F3 computes it, is such a case.
- **The Accord's CVT**, decision 40's stateless kickdown (`CvtVehicle.ratio_for`, `:813-852`). Its
  one discrete decision is at N_eco, so the threshold is the kickdown threshold
  λ_kd·T_del(N_eco), `CvtVehicle.kickdown_threshold_nm` (`:803-807`), against T_eco: on the
  economy branch T_eco must sit more than m below it, on the kickdown and power-limited branches
  more than m above it.
  - **Decision 40's diagnostic, reported and not gated.** On the kickdown branch N* is the lowest
    engine speed of the window whose demand is at most λ_target·T_del(N), and on the power-limited
    branch, where none is, the speed of most deliverable power (`:836-852`). If that feasible set,
    {N in the window: P_e/(ω·N) ≤ λ_target·T_del(N)}, is not one interval, a torque error inside m
    can move N* into another interval: a discrete change of engine speed that the margin at N_eco
    does not see. So can a switch between the two branches. At every gated step on either branch the
    roads step, which applies C5 (`docs/build_step_2/PLAN.md` section 7.4), reports whether, with
    the demand and T_del each scaled by (1 ± m), the feasible set stays one interval and N* stays on
    its branch: at the draw, at m = 1.9 %, and again at the re-check after the held-out run, at the
    re-check margin, redrawn climbs included (below), as decision 40's recommended option asks
    ("Report as a diagnostic whether N* stays in one connected feasible interval under demand and
    T_del × (1 ± m)", `docs/build_step_2/AMENDMENTS.md` section 3, decision 40). C5 gates the law's
    one discrete decision, at N_eco; that N* moves continuously everywhere else is an assumption,
    and this diagnostic reports where it fails.
- **At a step at which the box takes no torque decision, the held gear's own margin is not gated**,
  as at a barred downshift, and the step is reported with the CVT's branch or the held gear, and the
  road speed. There are two such cases. The CVT's low-speed branch, where `ratio_for` returns no
  N_eco (`engine_env.py:820-821`), has no other margin, and the step passes. A stepped box's held
  gear when it is its lowest, since `gear_for` compares the demand with a ceiling only while g > 0
  (`engine_env.py:624`), has its rejected higher gears, and their margins are still gated. Which of
  these steps count as gated steps is said below.
- **A demand at or below zero** (f ≤ 0: the CVT's economy hold, `engine_env.py:833`, or a stepped
  box on a descent) has |demand/threshold − 1| ≥ 1 against a positive threshold, and passes unless m
  reaches 1, wherever a margin is taken: the rules above for a barred gear and for a step with no
  torque decision say first whether one is (version 4, written after its sixth review). At f ≤ 0 the
  CVT's low-speed branch, which `ratio_for` returns before its test of f (`:820-821`), still has no
  margin. A stepped box holds the highest gear the road speed allows, since the demand is under
  every ceiling, so it rejects no higher gear, and the held gear's own margin gates only when that
  gear is not its lowest and its next lower gear is not barred.
- **The steps the margin is taken over (version 4, decision 73)**: every step of a scored climb
  outside its transitions, the ramps of its grade changes and its changes of speed. A step is a
  transition step when the road's grade there differs from its grade at the step before, or the
  road's speed there differs from its speed at the step before or at the step after: the demand at a
  step is computed from the road's speed, its change to the next step and its grade
  (`engine_env.py:1254-1257`, in `SupervisoryTunerEnv.step`). Every grade change is a ramp (training
  gate item 4, `CLAUDE.md`), `GRADE_RAMP_S` long on the locked climb (`engine_env.py:1644`). In a
  transition the box changes gear by design, and the margin at the steps around the change depends
  on where the steps fall and can be arbitrarily small. The transition steps' margins and their gear
  sequence (the CVT's branch) are therefore reported beside the result and not gated; the gear the
  climb is driven in is checked at every step outside its transitions.
  - **"Differs" is exact inequality** (≠) of the float64 values of the road's grade and speed arrays
    as the roads step records them, the arrays the environment reads (`c["grade"]`, `c["v_mps"]`),
    with no tolerance (version 4, decision 73, written after its fourth review).
  - **The time step.** A road's steps are its steps at the time step its scored climbs are scored
    at, which the roads step records with the roads: the arrays the environment reads at that time
    step. The transition test and every count of steps below depend on it (`engine_env.make_terrain`
    and `make_grade_climb` take it), and C5 never re-samples a road at another (version 4, decision
    73, written after its fifth review).
  - **A gated step** is one at which at least one margin gates on the car: a step outside the
    climb's transitions at which the held gear's own margin gates, or a rejected higher gear's does.
    A step outside the transitions at which none does is not gated, and there are exactly three such
    steps: the CVT's low-speed branch, which has no margin; a stepped box's lowest gear when it is
    also the highest the road speed allows, so that no higher gear is rejected; and a stepped box's
    held gear whose next lower gear is barred by SHIFT_RPM_MAX when it is also the highest the road
    speed allows, for the same reason. At every other step at least one margin gates: on the CVT's
    economy, kickdown and power-limited branches T_eco's at N_eco, and on a stepped box the held
    gear's or a rejected higher gear's. A step that is not gated is reported with the car's gear or
    branch, and counts neither toward the minimum nor toward the gated share below. These cases
    decide first, at any demand: a step whose demand is at or below zero is gated only where one of
    its margins gates, and that margin is then at least 1, which passes (the same, written after its
    fifth review; the third case and the order of the rules after its sixth).
  - **The shares are reported with the climb** (the same, written after its fourth review, the gated
    share after its fifth): of each scored climb's steps, the share that are transition steps, and
    on each car the share that are gated. On a road whose speed changes at every step of an
    acceleration or a coast, as the extremes kind's does (`engine_env.extreme_speed_profile`), most
    of a climb can be transition steps, and C5 then gates a small part of it.
  - **C5's outcome on a car is one of three cases** (the same, the thin flag written after its fifth
    review, the cases after its seventh). For a scored climb on a car, at the margin m it is checked
    at there (1.9 % at the draw and at a redraw, the re-check margin after the held-out run, below):
    (1) **it fails** when some gated margin is at or below m; (2) **it is thinly checked** when no
    gated margin is at or below m and its gated steps on that car are fewer than half its steps; (3)
    **it passes** when neither holds. The three are exclusive, and every climb is in one on every
    car (step 7 checks the case table). A climb whose gated steps on a car are fewer than half its
    steps is **flagged thin** there, whichever case it is in, and is never reported as passed there;
    the flag is known at the draw, from the road, the car and its frozen plant, and is reported with
    the roads, with the climb's gated share. A thin climb that fails at a gated step fails C5 there,
    case (1): it is discarded at the draw and redrawn at its re-check, and a slot that keeps it at
    the cap is flagged gear-sensitive and thin on that car (below). A thin climb with no failing
    gated step is thinly checked there, case (2): it is reported so, scored and not redrawn, and it
    neither passes nor fails C5, so it does not make its car gear-sensitive. The first draw and a
    redraw both accept a candidate in case (2) on a car, if it has a gated step there (below), and
    flag it thin; each car's results are reported with and without its thin climbs. **One half is
    DESIGN, chosen from no data** (version 4, decision 73, labelled after its sixth review): no road
    has been drawn, so no climb's gated share has been seen. It is the least share at which a climb
    that C5 reports as passed was gated on at least as many of its steps as it left ungated. It
    moves what is reported as passed and nothing else: a thin climb is still scored and fails C5 as
    any climb does, and every car's results are reported with and without such climbs.
  - **Why a change of speed is a transition, and what that costs.** The reason not to gate a
    transition, that the margin near a change of gear can be arbitrarily small, holds only near the
    steps at which the gear, or the CVT's branch, actually changes. Between them a steady
    acceleration or coast holds its gear, and a torque error the validation accepts could still hand
    it back or take the next one there, which C5 does not check; the thin flag reports the climbs on
    which that matters. The other readings would gate those steps: a transition only where the grade
    or the acceleration changes, with a fixed neighbourhood (raised by version 4's fourth review),
    or only within a fixed neighbourhood of a step at which a car's gear or the CVT's branch
    changes, and of the grade ramps (raised by its fifth). Neither is taken in version 4, because
    neither has a width that follows from the reason for not gating a transition. The steps around a
    gear change made by design whose margin a torque error within m can cross are those over which
    the demand moves by about m against the threshold, so how many they are is set by how fast the
    demand crosses the threshold there: few on a ramp, many on a slow acceleration. The speed test's
    width of one step comes from the demand's own definition, which reads the speed's change to the
    next step, and not from that. A one-step neighbourhood would therefore gate, on a slow
    acceleration, steps at which a torque error within m only moves the timing of a gear change the
    box makes by design, and fail every such climb, which is what not gating a transition prevents;
    a width derived from m and the demand's rate would be a new rule that no review has examined.
    Version 4's fifth correction also gave as a reason that the second reading makes the transition
    steps each car's; its sixth review found that no objection, since the gated steps are already
    each car's and known at the draw, and it is withdrawn. Decision 73's row records both readings
    as options, with this reason.
  - **A scored climb's steps** (version 4, decision 73) run from the first step of its ramp up to
    the last step of its ramp down, and the roads step records each climb slot's first and last step
    with the roads, before any held-out statistic; the road before and after a scored climb is not
    C5's. The neighbours the transition test compares are the road's steps, inside the climb or not,
    so a climb's first and last steps are transition steps, its grade ramping there, unless the
    climb starts at the road's first step or ends at its last. The road's first step has no step
    before it and its last no step after: a missing neighbour is taken as the step itself, as the
    environment takes the step after the last (`engine_env.py:1255`), where the speed's change to
    the next step is zero.
  - **A scored climb must have at least one gated step on every car.** One with none on a car has
    not been checked by C5 there and does not pass it: it is in case (2) there. Its gated steps are
    known at the draw, from the road, the car and its frozen plant, so the roads step discards such
    a climb at the draw and at a redraw, as a climb that fails a test of the first draw (below), and
    reports it.
  - **The locked climb's transfer row** (decision 34 keeps "the locked climb ... only as a declared
    transfer row") is not one of decision 34's roads. It is never drawn or redrawn, and C5 gates
    nothing on it. Its margins, computed as on a scored climb, are reported as decision 44 asks,
    beside the gear or ratio, the rpm and the margins to the kickdown and rpm bars (version 4's
    reading of decisions 34 and 44, written after its fifth review). The locked-climb cases above
    (amendments F2 and F3) illustrate the rule; they are not scored climbs.
  - Version 3 wrote "on every scored climb" and named no steps; `docs/build_step_2/PLAN.md` section
    7.4 reads "every scored-climb step". The changes of speed and the gated-step minimum were added
    to decision 73 after version 4's second review, a scored climb's extent after its third, the
    exact comparison and the reported share after its fourth, and the time step, the gated step, the
    thin flag and the transfer row after its fifth, before any road was drawn (section 13).

**Against the held-out E1a (version 4, decisions 64 and 74-76).**

- **A climb slot is shared by the four cars** (version 4, decision 75). Decision 34 draws one set of
  test roads, whose preview ceiling is at least 2 MEI on every engine
  (`results/VALIDATION_DECISIONS.md:157`), so each slot of it is one climb for every car, the
  Supra's included. A slot per car would give the engines different roads, which ends decision 34's
  one set and would have decision 26's cross-plant comparison compare engines scored on different
  roads.
- The roads are drawn with m = 1.9 % on every car, before any held-out statistic. **The redraw
  streams** (version 4, decision 76; the derivation fixed after its sixth review): each climb slot
  has its own, the sequence of candidate climbs the first draw's code draws, one after another, from
  the generator `numpy.random.default_rng([roads_seed, 0xC5, k])`. roads_seed is the non-negative
  integer the roads step draws the roads from and records with them; 0xC5 is a label that separates
  these streams from any other drawn from that seed, as `engine_env.TerrainTrainingEnv` separates
  its road stream (`_TERRAIN_STREAM`), and the roads step draws no other stream under it; and k is
  the slot's index, from 0, in the order the slots are redrawn in (below). A slot's candidates
  therefore do not depend on how many another slot used, and the streams are fixed by the roads' own
  seed and nothing else. Version 4's drafts left the derivation to the roads step, which runs after
  the first fit, with the in-sample E1a known, as they had left the cap. The freedom that remains is
  the roads' own seed, which also picks the first draw: the roads step sets it after the freeze, as
  version 3 and decision 34 let it, and commits it with the roads.
- **The cap and the discard bound are this file's** (version 4, decision 76): at most 3 redraws per
  climb slot, and at most 100 candidates discarded per slot (below). Both are DESIGN, fixed before
  any fit and from no data. Decision 64 asks for a cap and gives none, and a cap chosen with the
  roads, after the first fit, would be chosen with the in-sample E1a known, and would decide whether
  a failing climb is redrawn or kept and flagged. Three redraws bound how far one engine's held-out
  E1a can move a slot, and leave a slot whose candidates each fail with probability p without a
  passing climb with probability p³, one in eight at p = ½. The discard bound only ends a stream
  that keeps failing the first draw's tests.
- After the held-out run, every scored climb is re-checked on every car: each EPA engine's at its
  own max(1.9 %, |E1a| + 2u_val), and the B58's at 1.9 %. |E1a| and u_val are those of E1a's worst
  deciding line (section 3), as decision 64 reads ("of the worst line", `docs/build_step_2/PLAN.md`
  decision 64). A line with a smaller |E_l| and a larger u_val can leave more than the worst line's
  |E1a| + 2u_val, which that margin does not see, so every deciding line's |E_l| + 2u_val,l is
  reported beside it.
- **A climb that fails C5 on any car, case (1), is redrawn for every car** (decision 75). A redraw
  is the next climb of the slot's stream that passes every test the roads step applies to a climb of
  its first draw, with the same code: decision 34's preview ceiling of at least 2 MEI on every
  engine, C5 at 1.9 % with at least one gated step on every car, a test a candidate passes when, on
  every car, it is in case (2) or (3) and has a gated step (one in case (2) on a car is accepted and
  flagged thin there, as at the first draw), and the roads step's own checks. Each test is applied
  as the first draw applies it: a test of a climb to the candidate, and a test of a road or of the
  road set to that road or set with the candidate in the slot and every other slot as it then
  stands. Decision 34's ceiling is of the second kind, a property of the roads ("chosen so that the
  preview ceiling ... is at least twice the MEI on every engine"), not of one climb. A candidate
  that fails one is discarded, as at the first draw: it is not a redraw and is not counted against
  the cap, and the number discarded is reported. The slots are redrawn in their order on the roads,
  the roads in the order the roads step records them and a road's slots by their first step, each
  slot's redraws ending before the next slot's begin. Every car's C5 is then checked again on the
  new climb at its re-check margin (the tests' level and the order written after version 4's fifth
  review, the order's definition after its sixth).
- **A candidate fills its slot's recorded extent** (version 4, decision 75, written after its sixth
  review): the first draw's code draws it as a climb of the slot's length, from the slot's recorded
  first step to its last, joined to the road at both ends as a climb of the first draw is. The road
  outside the slot, the slot's first and last steps and every other slot's record stay as recorded,
  so a redraw moves the transition and gated-step counts of that slot alone, and the road set
  decision 34's ceiling is computed on only inside it. A candidate that code cannot give at the
  slot's length is discarded, as one that fails a test of the first draw.
- **The cap counts a slot's redraws over all cars**: one for each redraw, whichever car's failure
  caused it (decision 75), at most 3 (decision 76).
- **A slot whose redraws discard 100 candidates stops redrawing** (decision 76): it keeps its last
  climb for every car, as a slot at the cap does (below), and the stop is reported. A slot's stream
  has no end, and discarded candidates are not counted against the cap, so without this bound a slot
  whose candidates kept failing the first draw's tests would never be settled.
- **A slot whose redraws reach the cap, or stop at the discard bound, keeps the last climb accepted
  for it, for every car**: its original or its last redraw, never a discarded candidate (decision
  74, read with 75; the climb named after version 4's sixth review). On each car on which that climb
  fails C5, case (1), the slot is scored, flagged gear-sensitive, with its margins listed, and
  flagged thin too where the climb is thin on that car, and that car's results are reported with and
  without its flagged slots. Dropping the slot would shorten that car's scored set on the strength
  of a held-out statistic (E1a), which decision 64 avoids for a whole car.
- **A car with no passing climb** is not dropped: C5 is a rule, not a gate. Its scored climbs'
  margins are listed, each slot keeping its last accepted climb as every slot at the cap does, and
  it is reported by what its climbs are on it: gear-sensitive (decision 64) when a slot is flagged
  gear-sensitive on it, thinly checked when a climb is flagged thin on it, and both when it has
  both, as it has when a slot at the cap keeps a thin climb that fails there. A thin climb with no
  failing gated step, case (2), neither passes nor fails C5: it is not a passing climb, and it does
  not make its car gear-sensitive; a thin climb that fails at a gated step, case (1), fails C5
  there, as any climb does (version 4's reading of decisions 64 and 73, written after its sixth
  review, the cases after its seventh).
- **What a redraw costs, disclosed.** A redraw moves every car's scored set on the strength of one
  engine's held-out E1a: the price of decision 34's one road set (decision 75). The redraws are
  reported per slot, with the car and the margin that caused each. L1's and E8's tightenings were
  measured on the roads as first drawn, and that is disclosed too.
- **Rule 0, the streams and the cap.** The streams are fixed by the roads' own seed, which the roads
  step sets after the freeze and before any held-out statistic, as decision 64 places it, through
  the derivation written here; that derivation, the cap and the discard bound are fixed here, before
  any fit (decision 76). None of them changes after the held-out run. Rule 0 freezes this rule and
  these numbers, as it lets the roads themselves and the L1 and E8 tightenings, which also come
  after the first fit, be set by the step this file names (section 7). The one change after the
  held-out run is the redraw: a climb that fails at its re-check margin is replaced from its slot's
  committed stream, within the cap and the discard bound, which moves the scored climbs and nothing
  else; the tightenings stay as measured on the roads as first drawn (above).

## 6. The table gates (decision 28)

Every reported agent is scored on the exact cycle (decision 28). A table's error therefore reaches a
reported number only through training: an agent learns on the table, and may learn to exploit it. A
uniform table error cancels from the baseline-relative reward (`engine_env.py:1330-1341`, in
`SupervisoryTunerEnv.step`). The table is the sixth part of the budget and is held to b. The gates
apply to every engine's table, the B58's included. The training backend and the scoring backend are
recorded as separate fingerprint fields (decision 28), with this file's sha256.

**S1, open loop: the table against the exact cycle.** The points are 6000 environment calls from
hand-written and random policies on training roads, inner-loop iterates included, and 4000 points
spread uniformly over the box those calls visit. With 6000 points, a 95th percentile rests on about
300 points beyond it.

- **S1a: R = 16.6 % per lever.** The aggregate fractional error Σ|ΔEGT_table − ΔEGT_exact| /
  Σ|ΔEGT_exact| for each lever step:
  - λ −0.05 (the hand-written head start's −0.055, `results/preview_ceiling.txt:42`);
  - MAP −10 kPa (current-grade's boost pull, `results/VALIDATION_PLAN.md:443-444`);
  - spark −0.75° (one logged step, `:181`).

  The basis is section 1.2a: a table that cools by the wrong amount teaches the wrong head start. A
  coarse λ grid can fail this gate near λ = 1, where the exact cycle's TIT has a corner.
- **S1b: R = 12.3 %**, the 95th percentile of |T_table − T_exact| / max(|T_exact|, 40 Nm), the
  denominator the B58's table was measured with (`fe_out/strand_repo-stats-timing.md:140`) and the
  environment's tracking uses (`engine_env.py:1332`). Its basis is the uniform-bias consequence:
  16.67/1.353 = 12.31 %.
- **S1c: R = 16.6 %** for air and fuel; if the flows are computed in closed form rather than
  tabulated, as the B58 prototype computes them, S1c is an identity at 1e-6.
- **S1b and S1c are screens** (finding 15). A table's errors are local, not a uniform bias, so they
  catch only a gross table; the B58's measured torque p95 is 1.17 %. S2 is the check.
- **S1d: descriptive.** EGT level, knock integral and knock-flag agreement. A uniform level error
  cancels from the relative reward, and the knock term is reported both ways.

**S2, closed loop, per preregistered horizon (finding 24).** Decision 27 gives each engine three
arms, blinded and sighted at two horizons, and decision 26 one verdict per engine per horizon. So
every S2 statistic is computed per horizon H, sighted at H against blinded.

- **Practice episodes, never the frozen test (finding 14).** These are ten episodes of decision 34's
  roads, drawn once from a seed the preregistration fixes, distinct from the frozen twenty and from
  every training seed, as `check_c4_convergence.PRACTICE` is for D2.
- **S2a: R = 0.905 points**, |d_table − d_exact| for the hand-written preview pair: the predictive
  policy reading the largest grade within the next H seconds, minus current-grade. Fixed policies
  are scored on the table and on the exact cycle, with the damage read with and without the knock
  term; both must pass.
  - Five random pairs are **reported, not gated**: an action drawn uniformly from the action box,
    redrawn every **30 s**, seeds 0–9. Version 1 tied the hold to the preview of
    `engine_env.py:993` (`PREVIEW_S`), which decision 27 changes. A relative damage error δ moves a
    cut by (1 − c)·δ, three times more at c ≈ 0 than at the agents' c ≈ 0.68, and random actions
    span the whole box. A table could fail on random pairs alone for errors no agent visits.
- **S2b: R = 0.905 points, the check decision 28 names:** agents trained on the table, scored on the
  exact cycle.
  - Pilot agents are trained on each table with the preregistered recipe (decision 29), on seeds
    outside the experiment's list, **after the preregistration is committed**. Rule 1 puts the
    preregistration before the first training step, and decision 29's pilot exception covers
    `main`'s plant only. The preregistration states the conditional backend rule.
  - They are scored on both backends on the practice episodes. The gap is g = cut_table −
    cut_exact. Two statistics are gated, per H: the mean over pairs of (g_sighted,H − g_blinded),
    which is d's share, and the median over agents of g, which is systematic exploitation. Both
    damage readings apply.
  - **4 to 8 pilot seeds per engine** (finding 37). While a label reads untested, pilot seeds are
    added up to 8; then the label stands. Pilot seeds are not experiment seeds.
  - **What S2b does not test (finding 15):** whether training on the table changes the exact-cycle
    d, compared with training on the exact cycle. If the schedule allows, a few exact-trained pilot
    pairs are scored on the same practice episodes as a declared, descriptive comparison.

**When a table does not read validated.** These remedies are aimed at the measured causes, in this
order, each at most once, and every attempt is reported:

1. **a knock-flag guard band:** the exact cycle evaluates any step whose table knock integral lies
   within S1d's p95 relative error of the ECU's detection threshold;
2. **the baseline car on the exact cycle**, the agent on the table;
3. **a denser grid.** On the B58 a denser grid cut the open-loop error but "did not shrink these cut
   differences (max 1.48). The likely cause is the baseline car's +0.7 % damage bias and discrete
   ECU events such as the knock-retard flag. UNVERIFIED" (`fe_out/strand_repo-stats-timing.md:167`).
   Version 1 allowed only this remedy (finding 13).

If the table still does not read validated, the engine trains on the exact cycle if the schedule test
of section 7 passes. The exact cycle costs 6–8 times as much per run (decision 28's measurement, one
process on a loaded machine).

## 7. What happens on each label

**Labels are the comparison's own; coverage of the scored context is a flag beside them (section 3).**

| kind | rows | validated | limited | untested | off |
|---|---|---|---|---|---|
| level | E1a, E2a, E3a, E4a, L0 | the engine's 850 °C row may cite this accuracy | 850 °C row labelled limited | 850 °C row labelled untested | 850 °C row labelled off |
| d | D1, E4b, L1, E8, C3b, C3d | the part's band is b | **the engine enters**; the part's band is ((\|E\| + 2u_val)/R)·b | **the engine enters**; band as for limited, with the measured E and u_val | **the engine is dropped** |
| table | S1a, S1b, S1c, S2a, S2b | the engine trains on its table | the remedies of section 6, then the exact cycle or the drop order | as limited (S2b: pilot seeds up to 8 first) | as limited |
| identity | C1, C2, the neutral-action identity (section 4) | — | a coding defect: fix it and re-run | | |
| rule | C5 | — | a climb slot is shared by the four cars (decision 75); a climb that fails C5 on any car is redrawn for every car, each redraw passing every test of a first draw and checked again on every car, at most 3 redraws per slot, counted over all cars, and at most 100 discarded candidates (decisions 64, 75 and 76); C5's outcome on a car is one of three exclusive cases, fails, thinly checked or passes (section 5); a climb with no gated step on a car does not pass, and the roads step discards it as a failing first draw, and one gated on fewer than half its steps on a car is flagged thin there, never passed: thinly checked when no gated margin fails, failing C5 when one does, that car reported with and without such climbs (decision 73); a slot at its cap or its discard bound keeps the last climb accepted for it, for every car, scored, and flagged gear-sensitive on each car on which it fails, and thin too where it is thin there, each such car reported with and without its flagged slots (decision 74); a car with no passing climb is never dropped, each slot keeping its last accepted climb, and is reported gear-sensitive when a slot is flagged on it and thinly checked when a climb is thin on it, a thin climb with no failing gated step neither passing nor failing (decisions 64 and 73); the locked climb's transfer row gates nothing (decisions 34 and 44) | | |
| descriptive | E1b, E1i, E2b, E3b, E5, C3a, C3c, C4, S1d | reported, never gating | | | |
| perturbation | E6 | labels (excluded for a constant) and preregistered sensitivity rows; never a drop | | | |

- **Version 1 kept an engine whose d rows read limited or untested, and dropped it only on off**
  (finding 2). Its R then bounded nothing, and the budget held only for validated rows.
  - Version 2 keeps such an engine but **carries what its rows measured**. A limited d row has
    |E| ≤ R + 2u_val, up to 2R, and its part's band grows to match. An untested row's band is as
    wide as its own data make it.
  - Version 1 also said "a gate passes on validated or limited" and, two sections later, kept
    untested d rows. Both sentences are gone.
- **A d row with no statistic drops the engine.** That is a row with no deciding line, a row
  excluded for every constant it claims to test, or E8 with a subset short of 3 rows (version 4's
  reading of decision 54, section 4). No band can be computed for it, so it is at least as strict as
  the tables, where untested ends training on the table (finding 2).
- **An untested d row that has a statistic enters with its band instead of dropping the engine**
  (decision 36, `results/VALIDATION_DECISIONS.md` section G, adopted 21 October). E8 is expected to
  read untested on every engine, the B58 included (section 1.5), so a drop would end the four-engine
  test before it began. The band carries the same information as a number: an untested row's band is
  at least b·(1 + |E|/R), and a verdict inside it reads MODEL-LIMITED.
- **The engine's model band Δ_e** is the RSS over its six parts, with the linear sum reported beside
  it. κ is a part's factor: 1 when its rows read validated, else (|E| + 2u_val)/R, the larger of its
  rows' when it has two.
  - **D1 has two readings** (E6 row 12: with and without the λ snap), and is labelled by the worse.
    Its κ is the larger of the two readings' κ, each computed as above for its own label (version
    4's reading of decision 59, which fixed the labels' order and not the band; written after its
    fourth review).
  - The multiplicative parts, P1 (D1), P2 (E4b), P4 (E8) and P5 (C3b, C3d), contribute
    κ·b·(d/MEI)·φ each, with φ = max(1, |1 + ln(1 − c)|) at both arms' realised median cuts.
  - P3 (L1) contributes κ·b.
  - P6, the table, contributes b when the engine trains on its validated table (its S2 statistics are
    additive and S1 is a screen), and nothing when it trains on the exact cycle.
  - The preregistration reports every d with its model band. **A verdict that changes when d moves
    within ±Δ_e is reported MODEL-LIMITED**, whatever its seed interval says.
  - The cross-plant comparison of decision 26 carries the bands too: d_i − d_j has a model band of
    √(Δ_i² + Δ_j²) beside its seed uncertainty, and two engines count as equivalent only within the
    MEI (decision 37, section 1.1).
- **The drop order.** When an engine must go (an off d row, a d row without a statistic, or a table
  that fails and a schedule that cannot carry the exact cycle), it is that engine. When the schedule
  forces a choice, it is **the Ford first, then the Honda**. The Mazda goes last, because it is the
  only engine with a map and driving data of the same engine (decision 24). **The B58 is never
  dropped.** If its table fails, it trains on the exact cycle, as X1 and X2 did. Version 1 gated the
  B58's table but left it out of the drop order (finding 3).
- **The schedule test, quantified (finding 3).** An engine trains on the exact cycle only if the
  seeds per arm that decision 30's window affords are at least decision 30's target of 20. The
  window is taken at the training device's measured many-run exact-cycle rate, with three arms of
  450 000 steps (decisions 27, 29, 30).

**No refit after any held-out statistic of an engine has been computed.**

- Refitting then would be tuning on the validation set (mistake 12; the guard of
  `results/VALIDATION_PLAN.md:110-112`). The in-sample stage of section 2.4 runs before, never after.
- **A coding defect is a disagreement with a specification committed before the comparison ran**
  (finding 3). It may be fixed and the comparison re-run. Both results are then reported, and the
  second can be labelled limited at best. Anything else is a modelling choice.

**Dropping an engine amends decision 24** (`results/VALIDATION_DECISIONS.md:132`), by a rule fixed
here in advance. The drop is recorded in the decision sheet with its date and the row that caused
it.

- If only the Mazda survives, the collapse test compares two plants, the B58 and the Mazda.
- If no EPA engine survives, the four-engine test does not run, and the failed validations are
  reported as results.

**The thresholds never move** (rule 0). An engine that fails is not rescued by a looser R. An R that
turns out loose is not tightened after its E is seen either: that is the same tuning pointed the
other way. The two tightenings this file allows (L1, E8) are measured on hand-written policies,
on the B58 plant and decision 34's roads (decision 71 for L1), before any held-out statistic exists.
The tightenings, the roads as first drawn, and the roads' own seed, from which C5's redraw streams
follow by the derivation of section 5, are set after the first fit, by the step this file names and
on the order it fixes (the JSON's `order_of_work`), before any held-out statistic; C5's redraw cap
and its bound on discarded candidates are this file's own numbers (decision 76, section 5). Rule 0
freezes the rules that set them, written here before any fit, and those numbers; their values come
from no held-out statistic, and none of them changes after the held-out run. After it, one thing
changes, by a rule written here: a scored climb that fails C5 at its re-check margin is redrawn from
its slot's committed stream, within the cap and the discard bound (decision 76, section 5). That
moves the scored climbs, on the strength of the held-out E1a, and nothing else: L1's and E8's
tightenings stay as measured on the roads as first drawn, and the redraws are disclosed (section 5).

## 8. What a pass does not establish

- **Cut levels stay model-dependent, by about the MEI.**
  - A lever error ε moves a cut c by ε·(1 − c)·|ln(1 − c)|. For 0 ≤ c < 1 that is at most 0.368·ε;
    for c < 0 it is larger (1.39·ε at c = −1).
  - At E4b's limit of 16.6 %, that is 5.3 points of cut at c = 0.43, and 6.1 points at c = 0.68.
  - These gates protect d, not cuts. A cut is reported as model-dependent, never as a property of
    the engine.
- **Which gates can bind (finding 32).**
  - The d rows that can realistically read worse than validated on a calibrated engine are E4b, L1
    and E8; S2 can realistically fail a table.
  - D1, C3b and C3d at 16.6 % fail only a gross model: the B58's one air-path comparison reads +1.9 %
    (`results/VALIDATION_PLAN.md:289`). S1b and S1c are screens.
  - The level rows (E1a at 1.9 %, E2a at 4.0 %, E3a, E4a, L0 at 10 K) can bind, but never drop an
    engine.
  - **The gates bound the six gated parts, not the model.**
- **What no row gates, for every engine.** Each is declared in the preregistration:
  - the knock model;
  - the boost lever (E5);
  - λ at part load (E4);
  - the housing constants (E6 row 4);
  - the enrichment timing (E6 row 13);
  - the absolute housing temperature (not covered).
- **τ is not validated.**
  - R3 is withdrawn (`results/VALIDATION_PLAN.md:118`).
  - D1 bounds the flow at the demand to 16.6 %, and so τ's flow part. The flow's absolute level rests
    on AFR_st and the λ convention (E6 rows 1–2), and only on the Mazda is it checked against a
    measured air flow (C3d).
  - The capacity and heat-transfer part of τ is assumed for every housing (decision 24), and E6
    row 4 reports what it moves.
- **The ECU's strategy is a first-order part of d that EPA's data cannot pin** (section 1.5). E8 is
  expected to read untested, and its band then enters every engine's d. The same response applies to
  the B58, whose spark under boost is itself untested (`results/VALIDATION_PLAN.md:292`).
- **The knock model is untested for the three EPA engines, and stays untested after drive C,**
  which tests the B58 only (`review_0` issue 16). Every EPA-engine result is reported with and
  without the knock term permanently, not only until drive C (gate item 3).
- **Every coefficient is the B58's** (section 1.4), except where f is bounded. For an engine whose
  own coefficient differs by a factor k, the matching requirement is effectively k times tighter or
  looser. Its own coefficients are reported, and never used to move an R.
- **Settled before any calibration.** Version 2 left three points open for the team here: the
  collapse test's equivalence margin, b with six parts, and E8's expected untested label on every
  engine with its band. Decisions 37, 38 and 36 settled them on 21 October
  (`results/VALIDATION_DECISIONS.md` section G): the margin is the MEI (section 1.1), b = MEI/6
  (section 1.3), and an untested row with a statistic enters with its band (section 7). Still open:
  Jad's column of those three decisions, and of decisions 39-77 of section H (66 dropped), whose
  rules of this file versions 4 and 5 wrote as text (sections 13 and 14); and Ghassan's own answer
  to decisions 73-76, to the readings the agents added to decisions 54, 59 and 64 on 23 October, and
  to version 5's readings of decision 77. His column of both sections records his delegation of 21
  October, and for these rows and readings it records only that. **They no longer hold the first
  fit: on 23 October 2026 Ghassan ordered Run 1 to go ahead before Jad's column is filled ("go ahead
  without it"), as X1 went ahead on his order on 8 October** (`results/VALIDATION_DECISIONS.md`, the
  notes at the top of sections G and H). His order is recorded as an order, not as an answer to any
  row. Jad's answers stay his to give. An answer of Jad's that differs, or a different answer of
  Ghassan's, given before the first fit, is applied before it, in this file's generator, as a new
  version; given after it, it cannot change version 5 or the frozen calibration (rule 0), and
  becomes a new contract version and a new fit, reported beside this one. Version 5 does not settle
  the questions the seventh review of version 4 left for a later version, and Run 1 goes ahead with
  them open (section 14).

## 9. Disclosure: what was seen before this was written

The 20 October research pass lives in the scratchpad, not in the repository:
`C:\Users\badcl\AppData\Local\Temp\claude\c--Users-badcl-Desktop-GRAD-project\14077827-1e2d-4826-b805-20b70e9c81f2\scratchpad\fe_out\`,
cited above as `fe_out/`. The lines this file quotes from it, and from the data catalogue outside
the repository, are copied verbatim in appendix A, so that the commit carries them.

**The EPA tables' structure and ranges.** Every channel's minimum and maximum
(`data/engines/<id>/epa_channels.csv`) was seen, and so were the maxima of `Turbine Inlet Temp`:

- on the Tier 2 tables used here: 900.8 °C (Mazda, High Load Final), 833.8 °C (Honda, Steady State),
  and on the Ford 840.1, 841.8, 858.6 and 856.3 °C (Cell 9 steady, HD1 steady, High Load Initial,
  High Load Final);
- in the design notes: 904.0, 833.8 and 863.3 °C, which mix Tier 2 and Tier 3 workbooks (`review_1`
  issue 13);
- **in the design notes, per-cell TIT values, not maxima:** "Settled EPA TIT at 2500–3000 rpm and
  13–16 bar is 723–816 °C" (`fe_out/design.md:180`). Version 1 omitted this (finding 13).

For the split, the populations and the coverage, each row's speed, manifold pressure, BMEP, λ,
intake and coolant temperature and fuel report were read, and which columns are present. No
torque, fuel or TIT value was compared with any model.

**The B58 table's measured errors** (`fe_out/strand_repo-stats-timing.md:140-167`;
`results/VALIDATION_DECISIONS.md:142-143` gives "within 1.5 points"):

- torque 1.17 % p95 and EGT 2.36 K p95 on 6000 environment calls;
- every cut within 1.47 points of the exact plant;
- X1/X2 pair differences within 1.14;
- hand-written cuts within 0.35–0.59;
- knock-flag agreement of 99.80–100 %;
- **"The denser grid did not shrink these cut differences (max 1.48)"**
  (`fe_out/strand_repo-stats-timing.md:167`). Version 1 omitted this while offering only a denser
  grid as the remedy (finding 13).

Set against this contract:

- S1b and S1c (12.3 %, 16.6 %) sit far above the measured torque error, and are called screens;
- S1a and S2b were never measured;
- the hand-written preview pair moved by 0.00 on the locked climb's frozen twenty. S2a is defined on
  decision 34's roads, which are not drawn yet;
- the 1.14 comes from the X1/X2 agents, trained on the exact plant and scored on the table. That is
  not an S2 statistic; as one it would exceed S2's 0.905 by 0.235.

**The draft thresholds of 20 October equalled these measured errors and were withdrawn for that
reason** (`fe_out/design.md:104-116`; `review_0` issue 7). None of the Rs here is a measured error.

**Also seen:**

- X1's and X2's results (`results/X1_RESULT.txt`, `results/X2_RESULT.txt`) and the seed statistics
  behind decisions 29–30.
- The preview ceiling: 0.13, 0.42 and 1.19 points on the locked climb (`results/preview_ceiling.txt`).
- The D3 figures of section 5 (C4), and each car's locked-climb operating point from the vehicles
  strand: the CX-9 in 4th at 4173 rpm and 305 Nm, the F-150 in 4th at 3470 rpm and 392 Nm, the
  Accord at high rpm (`fe_out/strand_vehicles.md:194`). These come from a re-implementation and are
  UNVERIFIED, and amendment F3 supersedes the F-150's (section 2.2).
- The design notes' sections 2, 3 and 4 (`fe_out/design.md:59`, `:96`, `:104-116`), both reviews of
  20 October, and the review of 21 October, whose 37 findings section 11 answers.
- **Computed for this contract on the B58 plant alone:** the sensitivities with the ECU in the loop
  (section 1.4); the ECU-strategy shifts, under K3 and at a fixed knee (section 1.5); and the
  knee-shift re-scores of the committed records (section 1.2c).
- **Seen by version 3's session**, which only turned version 2's scripts into the generator and ran
  it: version 2's two files, the decision sheet and the generator's outputs, whose steps 1, 2 and 6
  read the EPA tables' structure alone. One text search of the tree, for version 2's 1.086, printed
  a whole row of the Mazda's steady table (spreadsheet row 191, at 4501 rpm, on the calibration line
  4500); none of its values was compared with any model.
- **Seen by version 4's session** (22 October 2026), which re-ran steps 6 and 7 only and computed no
  number: version 3's two files and the generator, whose text prints all-row EPA aggregates (the TIT
  maxima and ranges of sections 3 and 9, each engine's deepest cell-referenced λ and its floor, the
  λ offsets of E6 row 1, the fuel analyses), and the generator's printouts; the build-step-2 plan,
  its amendments and hand-offs, of which `docs/build_step_2/PLAN.md:524` prints the Honda's λ
  minimum; and the plant code, to move the citations. The session opened no EPA table, read no row
  value and compared nothing with any model. The generator's own reads are version 3's: steps 6 and
  7 read the tables' `fuel_report` column and their structure.
- **Seen by the session of 23 October 2026** that corrected version 4 after its review, which also
  re-ran steps 6 and 7 only and computed no number from EPA data: the same kinds of files (version
  3's two files at `ef5e14e`, version 4's draft of both, the generator and its printouts, the
  decision sheet, the build-step-2 plan, its amendments and hand-offs, the plant code and the B58's
  spec). It opened no EPA table, read no row value and compared nothing with any model.
- **Seen by the session of 23 October 2026 that wrote decisions 73 and 74 into version 4**, under
  the delegation, which also re-ran steps 6 and 7 only and computed no number from EPA data: version
  4's two files, version 3's JSON at `ef5e14e` (to compare), the generator and its printouts (which
  print, among other things, each engine's deepest cell-referenced λ and its floor), the decision
  sheet, the build-step-2 plan and hand-offs, and the plant code that builds the grade ramps C5's
  steps are defined by (`engine_env.py`). It opened no EPA table, read no row value and compared
  nothing with any model.
- **Seen by the session of 23 October 2026 that corrected version 4 after its second review**, which
  also re-ran steps 6 and 7 only and computed no number from EPA data: version 4's two files and its
  generator, with their printouts, which print each engine's deepest cell-referenced λ with its
  table and source row, its floor, the deciding lines and the pooled counts, and the review's and
  its verification's reports, which quote them; version 3's JSON and the plant files of its tree at
  `ef5e14e` (to pin section 13's version-3 lines); the decision sheet, the build-step-2 plan, its
  amendments and hand-offs, the rows of `REFERENCES.md` this file cites, `thresholds/split.py`'s
  classifier, and the plant code (`engine_env.py`, `engines.py`, the B58's spec). It opened no EPA
  table, read no row value and compared nothing with any model.
- **Seen by the session of 23 October 2026 that corrected version 4 after its third review**, which
  also re-ran steps 6 and 7 only and computed no number from EPA data: version 4's two files, its
  generator and their printouts (the same aggregates as above: each engine's deepest cell-referenced
  λ with its table and source row, its floor, the deciding lines and the pooled counts); the third
  review's and its verification's reports, which quote them, and whose reviewer's disclosure quotes
  the intake-cam-phase ranges and row counts of the three `epa_channels.csv` lines this file cites,
  as that reviewer read them (the ranges section 2.4 already prints, rounded); version 3's two files
  at `ef5e14e`; the decision sheet, the build-step-2 plan, its amendments and hand-offs; and the
  plant code (`engine_env.py`'s step, its locked climb and its training roads). It opened no EPA
  table, read no row value and compared nothing with any model.
- **Seen by the session of 23 October 2026 that corrected version 4 after its fourth review and
  wrote decision 75 in**, which also re-ran steps 6 and 7 only and computed no number from EPA data:
  version 4's two files, its generator and their printouts (the same aggregates: each engine's
  deepest cell-referenced λ with its table and source row, its floor, the deciding lines and the
  pooled counts); the fourth review's and its verification's reports and the third round's report,
  which name them; version 3's two files at `ef5e14e`, its JSON digested to pin what version 4
  keeps; the decision sheet, the build-step-2 plan (its WP5, C5 and decision-64 lines and its lines
  on the cam), its amendments and hand-offs; and the plant code (`engine_env.py`'s demand inputs and
  its extremes speed profile). It opened no EPA table, read no row value and compared nothing with
  any model.
- **Seen by the session of 23 October 2026 that corrected version 4 after its fifth review and wrote
  decision 76 in**, which also re-ran steps 6 and 7 only and computed no number from EPA data:
  version 4's two files, its generator and their printouts (the same aggregates: each engine's
  deepest cell-referenced λ with its table and source row, its floor, the deciding lines and the
  pooled counts); the fifth review's and its verification's reports, which quote them; version 3's
  JSON at `ef5e14e`, to compare; the decision sheet, the build-step-2 plan (its sections 7.4-7.7,
  and the lines a search of it for the cap and the time step printed, its decision-62 and
  decision-64 rows among them), its amendments and hand-offs (the lines the same search printed, the
  amendments' decision-64 row among them); and the plant code (`engine_env.py`'s road generators,
  its extremes speed profile and its note on the time step). It opened no EPA table, read no row
  value and compared nothing with any model.
- **Seen by the session of 23 October 2026 that corrected version 4 after its sixth review**, which
  also re-ran steps 6 and 7 only and computed no number from EPA data: version 4's two files, its
  generator and their printouts (the same aggregates: each engine's deepest cell-referenced λ with
  its table and source row, its floor, the deciding lines and the pooled counts); the sixth review's
  and its verification's reports, which quote them; version 3's JSON at `ef5e14e`, to compare; the
  decision sheet; the lines a search of the build-step-2 plan and its amendments for censored λ and
  for C5 printed (among them the plan's line 524, which prints the Honda's λ minimum, and its E8
  row, which prints each engine's count of Final rows), and the hand-offs' items;
  `thresholds/split.py`'s loader and classifier; and the plant code (`engine_env.py`'s gearbox, its
  CVT law and its road stream's seed). It opened no EPA table, read no row value and compared
  nothing with any model.
- **Seen by the session of 23 October 2026 that corrected version 4 after its seventh review**,
  which also re-ran steps 6 and 7 only and computed no number from EPA data: version 4's two files,
  its generator and their printouts (the same aggregates: each engine's deepest cell-referenced λ
  with its table and source row, its floor, the deciding lines and the pooled counts); the seventh
  review's report and the sixth correction's, which quote them; version 3's two files at `ef5e14e`,
  to compare their numbers; the decision sheet, and the header and row numbers of the team's dated
  copy of its section H on the Desktop; the lines a search of the build-step-2 plan and its
  amendments for the values of decisions 54 and 57 printed (among them the plan's line 524, which
  prints the Honda's λ minimum), the amendments' C1, whose lines print HD1's barometer and its sweep
  as the plan states them, and F3, and the hand-offs' commit A item 12; and the plant code
  (`engine_env.py`'s extremes speed profile). It opened no EPA table, read no row value and compared
  nothing with any model.
- **Seen by version 5's session** (23 October 2026), written in a worktree of its own at `cfe6211`,
  which also re-ran steps 6 and 7 only and computed no number from EPA data: version 4's two files,
  its JSON at `a1b88e6` digested to pin what version 5 keeps, the generator and their printouts (the
  same aggregates: each engine's deepest cell-referenced λ with its table and source row, its floor,
  the deciding lines and the pooled counts); the decision sheet; `docs/build_step_2/PLAN.md`'s WP3
  test and run lists, its sections 5.9-5.11 and 10.2, and the lines a search of the plan, its
  amendments and hand-offs for T0 and synthetic rows printed, the amendments' D10-D14 among them;
  the main working tree's list of untracked files (WP3's scripts); and T0's outcome, its 12 jobs and
  587 s, as the task that ordered version 5 reported them, none of T0's outputs opened. It opened no
  EPA table, read no row value and compared nothing with any model.

**The thresholds are B58-propagated.** Section 1.4's coefficients are the B58's, at its locked
climb's cell, with its ASSUMED housing constants, except that f is bounded. The same contract with
each engine's own coefficients would give other numbers. Those are reported beside the results and
never move an R.

## 10. Reproduce

`python engine_thresholds.py` runs every step in order and writes both files; its docstring says
what each step reads and computes. Each step's output and its printout (`<step>.txt`) are kept in
`results/ENGINE_THRESHOLDS/`, with `run.json`, the Python, NumPy and platform that ran them and each
step's wall-clock time. No other output, and neither of the two files, holds a time, so a re-run on
one platform gives every one of them back byte for byte (section 12). The JSON records the sha256 of
every file of the generator (`generators`) and of every step output it read
(`generator_inputs_sha256`), each with CRLF read as LF, so that a Windows and a Linux checkout give
the same hashes. `python engine_thresholds.py --build-only` rebuilds the two files from the saved
outputs in seconds, and `--check` exits 1 if either differs from what the code writes.

1. **The split:** step 1, `thresholds/split.py`, from the EPA tables' structure alone (their sha256
   are in `epa_tables_sha256`), and step 2, `thresholds/alpha_nodes.py`. A re-derivation must
   reproduce the counts of section 2.2, or stop.
2. **The B58 coefficients:** step 3, `thresholds/b58_propagation.py`.
   1. Run the locked climb as `validation_numbers._climb` does: neutral action, frozen episode 1,
      dt 1 s.
   2. Take the median operating point over t 400–718 s.
   3. Evaluate `plant.run_cycle` there at MAP ± 2 kPa, at fixed spark and along the ECU's schedule,
      at λ −0.01 to −0.15 and at spark ±0.75°.
   4. **Run the climb again with the cycle's torque × 1.01 and × 0.99** for the baseline and the
      agent, and read the medians off (finding 1).
3. **The knee-shift slope:** step 4, `thresholds/knee_shift.py`, from the per-step records of
   `results/agents/terrain_dt1` and `extremes_dt1`, which stay on the training machine (gitignored).
4. **The ECU's strategy:** step 5, `thresholds/ecu_shift.py`, the 24 runs of section 1.5 (9 `fixed`,
   15 `k3`), each in a process of its own and independent of the others, `--jobs` at a time. It is
   most of a full run's time.
5. **The contract:** step 6, `thresholds/contract.py`, reads them all and writes the JSON. It
   recomputes every R from those numbers, the MEI, R1 and decision 38's b, and pins the D3 files by
   sha256 against the data folder's manifest. Step 7, `thresholds/document.py`, writes this file
   from `thresholds/document_template.md`, and stops instead when a sentence's wording no longer
   holds for the number it carries. It needs git and a git checkout of the repository, because its
   last claim is checked against the .py files a commit would hold. Since version 4 it also reads
   version 3's tree through git (`git show ef5e14e:<file>`: version 3's λ clip and section 13's
   version-3 lines), so the checkout must contain commit `ef5e14e`; a shallow clone or an archive
   stops it. Since version 5 it reads version 4's JSON the same way (`git show
   a1b88e6:results/ENGINE_THRESHOLDS.json`), to check what version 5 keeps of it (section 14), so
   the checkout must contain `a1b88e6` too.

Version 2's scripts (`split.py`, `alpha_nodes.py`, `b58_propagation.py`, `knee_shift.py`,
`ecu_shift_one.py` and `build_contract.py`) lived in a session's scratch folder, and version 2's
JSON carried their source text; steps 1-6 are those scripts, committed (section 12).

## 11. Version 2: the review of 21 October, finding by finding

Every finding was reproduced before it was applied: the numerical ones by re-running the scripts of
section 10, the structural ones from version 1's `split.json` and the tables, the citations by
opening them. All 37 held. Their substance, the verdict and the change, as version 2 recorded them
(at b = MEI/5; section 12 says what version 3 changed; the code citations moved to version 4's tree,
section 13):

| # | finding | verdict | change |
|---|---|---|---|
| 1 | the torque chain held spark fixed; in use the ECU moves it | confirmed: −2.247 kPa, −3.309 K, −1.336 %, −4.435 K along the schedule; the environment gives −4.44 K and −1.32 % | section 1.4 measured with the ECU in the loop; E1a 1.9 %, S1b 14.7 %, C5, E6 row 10 recomputed; reproduce step 2.4 |
| 2 | limited and untested d rows kept the engine, so R bounded nothing | confirmed (`VALIDATION_PLAN.md:312-315`) | section 7: limited and untested rows carry ((\|E\| + 2u)/R)·b into a preregistered band, and a verdict inside the band is model-limited; a row with no statistic drops the engine; line 277's rule removed. Untested does not drop, because E8 is expected untested on every engine: the team's call (section 8), since decision 36 (section 12) |
| 3 | decision 4's order lets "not covered" pre-empt "off"; no rule for excluded, no deciding line, the B58, the schedule, a coding defect | confirmed | labels on the comparison's domain, coverage a separate flag; probes sized by consequence; the B58 never dropped; schedule test quantified; coding defect defined |
| 4 | the Ford's split ran per cell, so held-out speeds stayed in the other cell's calibration | confirmed from version 1's `split.json` | the union of the Ford's speeds, held out in every table (rule 2) |
| 5 | level errors may differ by line; K3's road is not d's; nothing bounds the spread | confirmed | L1, R = b/0.0905 = 11.9 K, tightened on decision 34's roads; D1's bound on τ's flow part stated; H/τ placement unprotected stated |
| 6 | u_stat widened u_val where the model is worst; sparse lines could not fail | confirmed (`VALIDATION_PLAN.md:53` has three terms) | V&V 20's three terms; u_stat decides only whether a line may certify a pass (2u_stat ≤ R); off always decides; offset rule a |
| 7 | the lever bound holds only for 0 ≤ c ≤ 0.865; the "best cut 72.66" is wrong | confirmed: 91.3 / 90.2 % under 20.3 K, factor 1.44 / 1.32; negative cuts exist | the condition on every d row; φ multiplies the band outside it; the sentence corrected |
| 8 | C3 on transient, slipping samples; MAF unchecked; radius and population MAP open | confirmed (`fe_out/strand_vehicles.md:104`, `:97`; `CATALOGUE.md:662-663`) | C3 on locked, A/C-off segments; N/V radius; the car's PCM MAP defines "hot"; MAF and MAP channel checks |
| 9 | E5's slope is half spark term; E4b's λ = 1 reference sits tens of kPa low | confirmed: 1.473 against 0.686 K/kPa; version 1's reference sat 33–78 kPa below the Mazda's enriched rows | E4b's reference from the line's regression on MAP at each enriched row; E5 descriptive and the boost lever untested; the pair estimate kept descriptive, because finding 21 governs |
| 10 | E8's "second order" had no number; the Honda's λ floor | confirmed by measurement: under K3, λ ±0.02 moves the head-start pair −16 / −42 %, ±0.05 −36 / −82 %; the Honda reaches 0.610 | E8 a d row (part P4) with R from the measurement; the per-engine λ floor |
| 11 | the λ snap is never tested | confirmed: on this split 7 of the Ford's 16 hot λ≈1 held-out rows read rich of λ_ref (six by 0.010, one by 0.020), and 2 of the Mazda's 21 | E6 row 12; E3a, E5, D1 and L0 both ways, labelled by the worse |
| 12 | level rows cannot certify the gas that heats a housing | confirmed (`REFERENCES.md:311`, "EGT cruise, min"; `:664-667`, Caton; `plant.py:335-338`) | absolute housing statements not covered; level rows restated as the 850 °C row's inputs |
| 13 | two seen items undisclosed; "by anyone" claims too much | confirmed (`fe_out/design.md:180`; `strand_repo-stats-timing.md:167`) | both disclosed; the claim limited to this session; remedies aimed at the measured cause |
| 14 | S2a read the frozen test episodes before the preregistration | confirmed | S2a on practice episodes |
| 15 | S2b measures exploitation, not the backend's effect on d; S1b/S1c cannot fail a realistic table | confirmed | stated; an optional exact-trained comparison; S1b and S1c named screens |
| 16 | E7a used the B58's f against the f ≤ 1 rule; e's population unnamed | confirmed | f bounded everywhere (5.183 K, 2.451 K per 1 %); L0's e from the hot λ≈1 rows |
| 17 | the five parts double-counted the flow; the null-difference sentence did not follow | confirmed | torque and flow one part (D1); the sentence withdrawn; additive parts named |
| 18 | the JSON's flat list lacked the B58's C5; the generators were uncommitted | confirmed | the B58's C5 added; sources and sha256 in the JSON; committed in version 3 (`engine_thresholds.py`, section 10) |
| 19 | two citations wrong; LHV moved in the plant but not the thermal network | confirmed (`REFERENCES.md:785-788`, the Supra's road load; `PREREGISTRATION_X1.md:119`; `thermal.py:255`) | citations corrected; bands "proposed by this contract"; E6 row 3 moves both |
| 20 | the label-to-action rule was incomplete and self-contradictory | confirmed (as finding 3) | section 7 rewritten with every label |
| 21 | the hot population mixed in the High Load Initial transient | confirmed: no meter in any Initial table; the Final reads hotter though richer | Initial rows out of every gating statistic; E1i descriptive |
| 22 | the Ford's per-cell split tested cells, not rpm | confirmed (as finding 4) | rule 2 |
| 23 | the Mazda's 4500 rpm holds were an extrapolation | confirmed | the interior rule on the high-load lines (rule 3) |
| 24 | S2 ignored horizons; random pairs fell outside b; the only remedy was measured not to work | confirmed (`fe_out/strand_repo-stats-timing.md:165`, `:167`) | S2 per horizon; a 30 s random hold, reported, not gated; three remedies; pilots after the preregistration; backends as fingerprint fields |
| 25 | the C3 chain carried converter, inertia and A/C effects and an unchecked MAF | confirmed | as finding 8; η's span as u_input (5.25 %), so C3a and C3c descriptive; D3 files pinned |
| 26 | the model form was never named and could not legally change | confirmed | section 2.4: form A, alternatives B–D, the in-sample stage, then one held-out evaluation |
| 27 | whether the subset fit or a refit is the plant in use | confirmed open | section 2.5: the subset fit is the plant; the scored climbs stay inside its coverage |
| 28 | multiplicative errors can distort the collapse; no equivalence margin | confirmed | model bands carried into the cross-plant comparison; the margin open for the team (recommended the MEI), since set to the MEI by decision 37 (section 12); the false-negative statement |
| 29 | the ECU's strategy enters at first order and nothing checks it | confirmed (as finding 10) | E8 on held-out Final rows; E6 row 13, enrichment timing, a sensitivity row for every engine |
| 30 | E1 and E2 at EPA's MAP double-count what cancels at the demanded torque | confirmed | D1, L0 and L1 at the demanded torque; E1b and E2b descriptive |
| 31 | the coverage box was a product of ranges and counted unfired rows | confirmed: the Honda's 65.5 °C is an unfired row; fired 31.5–51.1 °C | coverage per population and per 20 kPa band, all rows and calibration rows |
| 32 | the flow d rows catch only gross failures; the budget omits ungated parts | confirmed | section 8 says which gates can bind; the bounds limited to the six gated parts |
| 33 | the contract and its sources were outside git | confirmed | appendix A copies the external lines verbatim; D3 hashes and the generators in the JSON; the B58's C5 added. The commit itself is the team's: this writer may commit nothing |
| 34 | minima counted rows, not holds; few high-load lines validated; thermocouple u_D 0.03 K | confirmed (version 1's Mazda 2250: 4 enriched rows from 2 holds) | clusters; the Honda validates 3 high-load lines and the Ford 2; IEC class 2 for thermocouples |
| 35 | AFR_st and LHV from another fuel; the Ford's HD1 batch | confirmed (FTAG 26864 on every HD1 table) | each table's own fuel; 14.7 and 44.0 become E6 rows 2–3 |
| 36 | one housing for two definitions of the gas | confirmed | both definitions stated; the 850 °C row not comparable across engines |
| 37 | S1b's denominator, the pilot cap, E6 row 4's source, the knee slope | confirmed | max(\|T\|, 40 Nm); 4–8 pilot seeds; the source corrected; the largest slope, 0.0905 per K, measured over ±5 to ±57 K |

Found while reproducing, outside the 37: version 1 cited `review_0` issue 10 for the Ford's TIT bank
(E3). That issue is about mistake 12; the source is `logs/epa/README.md:108-111`.

## 12. Version 3: decisions 36-38, and the generator committed

Written 21 October 2026, before any calibration, by `python engine_thresholds.py`. Decisions 36-38
(`results/VALIDATION_DECISIONS.md` section G) were adopted that day on Ghassan's delegation ("fix
all the way you see fit"), so that this contract could be committed before the first fit. Jad's
column is open; an answer that differs, given before the first fit, is applied before it, in the
generator. What changed from version 2:

- **Decision 38: b = MEI/6 = 0.905 points per part** (version 2: MEI/5 = 1.086). Every d-row R
  follows from b and is 5/6 of version 2's before it is rounded down: D1, E4b, E8, C3b, C3d, S1a and
  S1c 20.0 → 16.6 %, L1 11.9 → 9.9 K, S1b 14.7 → 12.3 %, S2a and S2b 1.086 → 0.905 points. The level
  rows (E1a, E2a, E3a, E4a, L0) rest on R1 and do not move.
- **What moves with b.** The errors worth b: E1b's torque 14.7 → 12.3 %, E2b's fuel 20.0 → 16.6 %,
  and E8's shifts, λ +0.0103 → +0.0086 lean and −0.0257 → −0.0206 rich; spark retard −3.0°,
  extrapolated → −2.6°, interpolated; spark advance +3.2°, extrapolated → +2.6°, extrapolated. The
  budget's totals: six aligned parts add to 1.00 MEI (was 1.20) and independent ones to 0.41 MEI
  (was 0.49); a true d at the MEI reads 0.59–1.41 MEI if the errors are independent (was 0.51–1.49)
  and 0.00–2.00 if they align (was −0.20–2.20). The sentences that quote these numbers follow them:
  D1's share of τ (section 4), the cut-level example (section 8) and the B58 table's pair gap
  against S2 (section 9).
- **Version 2's list of the MEI/6 values** (`budget.if_b_were_mei_over_6`) gave S1b 12.2 % and S2
  0.9 points: the first scaled the already rounded 14.7 %, the second rounded b to one decimal.
  Computed from b, as every R here is, they are 12.3 % and 0.905 points. The JSON keeps version 2's
  values in `budget.version_2_at_mei_over_5` instead, beside `budget.decision`.
- **Decision 37**, the collapse test's equivalence margin, is the MEI (section 1.1; `collapse_test`
  in the JSON). **Decision 36**: an untested d row with a statistic enters with its band, and a
  verdict inside the band reads MODEL-LIMITED; a row with no statistic still drops the engine
  (section 7; `on_failure.d` and `decisions` in the JSON). They close section 8's three open items.
- **The generator is committed beside this file** (section 10), and the JSON's `schema` is 3:
  `generators` holds the hashes of the committed files instead of their source text, and
  `generator_outputs`, `generator_run`, `collapse_test` and `budget.version_2_at_mei_over_5` are
  new. Its re-run of 21 October gave back version 2's outputs of steps 1-5 exactly, line endings
  normalised and the ECU runs' wall-clock `seconds` aside, so no number of version 2 moved except
  through decisions 36-38 and the three corrections below.
- **Three corrections, found while the .md was turned into a template; none is a threshold.**
  Section 1.5's pair column and its thermal-only agreement are computed from unrounded cuts: version
  2 differenced cuts already rounded to 0.01, so four pair entries move by 0.01, and the agreement,
  whose largest exact difference is at spark −3.0°, moves from 0.46 to 0.48 percentage points
  (0.4748, rounded up because the sentence states a bound). And the Honda has 11 high-load lines,
  not 12: version 2 counted its hold speeds, and 1700 and 1800 rpm are one line by rule 2.
- **Found by the independent re-run of 21 October; none is a threshold.** The thermal-only agreement
  is a bound, so it is rounded up: 0.48, where the first draft printed 0.47. The first run wrote
  each ECU run's wall-clock `seconds` into its output and every step's time into the JSON's
  `generator_run`, so no re-run could give back the JSON's sha256 of those outputs, nor the JSON
  itself. The times are now in `run.json` alone, and step 6 refuses an ECU output that still holds
  one. A full re-run after these changes gave back every output of steps 1-5 byte for byte, the
  dropped `seconds` aside, and both files byte for byte as `--build-only` wrote them from the
  outputs before it. Step 7 needs git and a git checkout (section 10): its last claim reads the .py
  files a commit would hold, and a copy without `.git` stops there with that message.

## 13. Version 4: decision 39, before any fit

Written 22 October 2026 by `python engine_thresholds.py --build-only`, after the plant changes of
build step 2's WP1 (the tree of `4461a91`) and before any fit, and corrected by the same command
seven times on 23 October, after each of its seven reviews (below), still before any fit. Decisions
73 and 74, which the first review raised, were written into section H between the first two
corrections, decision 75, which the fourth raised, with the fourth, and decision 76, which the fifth
raised, with the fifth; each was written into this file as a rule by the same command, and each is
adopted by the agents under Ghassan's delegation of 21 October, as every decision of section H is
(below). No step of 1-5 re-ran: the JSON's `generator_inputs_sha256` and `epa_tables_sha256` are
version 3's, and so is every number computed from steps 1-5; version 4 adds four rule constants, and
none is computed from data. Three are DESIGN, chosen with no data behind them, each with its reason
in section 5: decision 76's cap of 3 redraws per slot and its bound of 100 discarded candidates, and
decision 73's thin share of one half. The fourth is E8's subset minimum of 3 rows, version 3's own
minimum of clusters for a line's statistic (`thresholds/split.py`, `MIN_CLUSTERS`), applied to E8's
two subsets (section 4). The team answers these four with the rest of what the agents added on 23
October (below). Version 4 also writes the values that decisions 54 and 57 state, adopted under the
delegation of 21 October, for rules version 3 did not have: λ 1.00 for a fired row without λ, the
−120 spark sentinel, and censoring when at least 2 calibration Final rows sit at their own minimum λ
within 1e-9 (decision 54, with amendment C1; section 3); and D1's pre-scan every 10 kPa, with its
bisection to 1e-3 kPa (decision 57, as the plan's D1 row states them; section 4). Step 7 checks each
against the JSON's `conventions`. Version 4's other numbers count the JSON's entries (the Tests
lists' row numbers), name a stream (0xC5, a label, section 5), come from this tree's plant code
(`version_4.plant_values`) and from version 3's λ clip, or follow from these by arithmetic (the
cap's one in eight at p = ½). `calibrate_epa.py` does not exist, no script outside the generator,
`epa_map.py` and `test_epa_map.py` names the EPA tables, and nothing a fit writes exists (the
generator's last claims, section 10). Rule 0 lets a version be written only before the first fit,
and a version can be written without editing the generator only until a script that names the tables
exists, since step 7 then stops.

**Why.** Decision 39 (`results/VALIDATION_DECISIONS.md` section H, adopted under Ghassan's
delegation of 21 October 2026) asked for it: two of version 3's rules could not be applied as
written, and decisions 49, 54, 55, 59, 64, 70 and 71 are rules of this contract, as are decisions
73-76, which its reviews raised, and decision 57, whose details the contract's text needs (below).
The text of 39-71 comes from the review of the build-step-2 plan, `docs/build_step_2/AMENDMENTS.md`
(A1-A3, E1-E6, F1-F3 and its section 3, which govern where they differ from
`docs/build_step_2/PLAN.md`), and from the hand-offs of WP1 (`docs/build_step_2/HANDOFFS.md`,
section "WP2"). The text of 73-76 comes from neither, and the amendments' section 3 does not hold
them: it is their rows of section H, written on 23 October. **Version 4 follows section H's reading,
as WP1 did** (`docs/build_step_2/HANDOFFS.md`, commit A item 1): every decision of 39-76 but 66,
which the amendments dropped, is adopted under the delegation, and the first fit waits for both
columns. **Decisions 73-76 are adopted the same way, and so are the readings the agents added to
decisions 54, 59 and 64 on 23 October.** They were raised by the reviews of this version, two days
after the delegation, and written in by the agents writing it, as the rows of 39-72 were on 22
October; Ghassan's column records the delegation, not an answer of his to these rows or readings,
and since the fifth review each of their cells says so ("adopted by the agents 23 Oct, not yet
seen"), as the sheet's own note of 23 October does, a box of its own outside the quote of his answer
of 21 October. After the second review 73 and 74 were marked pending his own answer, his column left
empty; after the fourth they are adopted as the rest of section H is. The first fit waits for Jad's
column and, for these rows and readings, for Ghassan's own answer, which the sheet asks of both of
them before it (its note of 23 October: "Both of them answer these rows and readings before the
first fit"). Amendment A1's check, "WP2 starts only when the G1 and G2 columns are filled", is not
met, since Jad's column is empty; an answer of either that differs is applied as a new version
before the first fit (below).

**What changed.**

- **Two rules that could not be applied as written.**
  - **C5's threshold** (decision 39(c), which is decision 70, with 40; amendments F1 to F3). Version
    3's SHIFT_LOAD·T_wot is not the threshold the gearbox applies. Version 4's is
    `Vehicle.shift_ceiling_nm(rpm)` at the held gear and at every rejected higher gear, the held
    gear's own margin not gating while its next lower gear is barred by SHIFT_RPM_MAX, whose rpm
    margin is reported, and for the CVT decision 40's kickdown threshold at N_eco, with decision
    40's diagnostic of N* reported; at a step at which the box takes no torque decision the held
    gear's own margin does not gate (section 5). Version 3's CVT clause, the margin to the law's
    λ·T_wot, cannot be met on the economy branch of an economy-line law, where the demand sits on
    that threshold by construction, and a continuous law has no gear for it to protect (the
    amendments' section 2, item 9). The clause the plan drafted to replace it for an economy-line
    law (`docs/build_step_2/PLAN.md`, its decision 39(c)) would have failed on every power-limited
    step, which is where the Accord climbs, and amendment F1 dropped it when decision 40 chose the
    stateless kickdown; C5 then reads as the margin to the law's one discrete decision. Throughout
    this file, 39(c) means section H's: C5's threshold by decision 70.
  - **The neutral action** (decision 39(b); amendment E1). "Reproduce the baseline exactly" holds on
    no engine. Version 4's identity is on the λ and spark channels at float32, with no clip contact,
    a contact being one of the two channel clips changing the value it was given, compared in
    float32, with the four bounds asserted to be Python floats; the fan and pump are
    `neutral_action`'s constants and are not compared (section 4, the λ clip).
- **Rules of section H**, each marked "version 4" where it stands:
  - 39(a): E8 computed in-sample and reported, outside the form criterion (sections 2.4 and 4);
  - 49: each engine its own form (section 2.4);
  - 54: rows without λ, which belong to no λ band, the −120 spark sentinel, censored λ, a documented
    sensor floor (section 3); and version 4's readings of it, each with its reason, written after
    its fourth review and noted in decision 54's row: a sentinel row's spark in D1, the model ECU's
    spark at EPA's MAP plus s·ΔMAP; E8's dl without the rows that publish no λ and ds without the
    sentinel rows, each also reported with them (section 3); and, written after its fifth review,
    each subset's minimum of 3 rows, below which E8 has no statistic and the engine is dropped
    (section 4); and, written after its sixth, an empty `Spark Timing` cell read as the sentinel, a
    Ford HD1 row with an empty bank read as a row without λ, and E8's list of the censored held-out
    Final rows, with dl reported without them (section 3);
  - 55: an in-sample statistic with no calibration line neither blocks nor passes (section 2.4);
  - 57: the statistic details of `docs/build_step_2/PLAN.md` decision 57 that version 3 left open,
    which the contract's text needs, since each moves its statistic: D1's pre-scan, bisection and
    nearer bound, D1 also reported without its unreachable rows, and form D's cam at the inverted
    MAP (the plan's section 6.3); E8's EPA λ unsnapped, with the snapped E8 reported, P's slope at a
    zero shift the steeper side's, its linear extrapolation flagged, and the tightening's sign
    (section 4); and the worst line, defined, with its u (section 3). Decision 39(d) does not name
    57, which section H adopts as "As the plan states", and amendment A1 puts it in the group
    answered before version 4's text;
  - 59: the E6 readings (rows 1, 3 and 7 report how far the model in use moves; row 2 within u_val;
    row 9's order, its flame terms named, and the rich slope, which takes the visibility probe under
    every form, with its fit's σ reported beside it under C, as rows 5 and 6 take theirs (this is
    how version 4 reads amendment E3's "a probe under A and B, its σ under C": a σ alone would size
    the probe by the fit, which section 4's rule forbids, and would leave E4a and E4b without a
    probe for the slope); row 12's order of labels, and D1's κ under it the larger of its two
    readings', version 4's reading, noted in decision 59's row (section 7); the ±10 % probe of every
    d row; the refit rows' calibrations before the held-out run) and the Tests lists with their
    counting rule (section 4, E6);
  - 64: C5 against the held-out E1a: the roads drawn at 1.9 %, the re-check margin from E1a's worst
    deciding line, with every line's |E_l| + 2u_val,l reported beside it, the redraw streams, one
    per slot, fixed by the roads' own seed through a derivation written here, and decision 76's cap,
    none changed after the held-out run, and a car without a passing climb never dropped, each slot
    keeping its last accepted climb, and reported as gear-sensitive when a slot is flagged on it, a
    thin climb with no failing gated step neither passing nor failing (sections 5 and 7; version 4's
    readings noted in decision 64's row);
  - 71: L1's tightening measured on the B58, and the in-sample stage taking L1's untightened R
    (sections 2.4, 4 and 7);
  - 73: C5's steps: every step of a scored climb outside its transitions, the ramps of its grade
    changes and its changes of speed, a change being exact inequality of the road's recorded arrays;
    the transition steps' margins and gear sequence reported beside the result, not gated, with each
    climb's share of transition steps; at least one gated step on every scored climb, a climb with
    none not passing; and a scored climb's extent, from its ramp up to its ramp down, with the
    road's end steps; and, after the fifth review, the time step a road's steps are taken at, a
    gated step defined as one at which a margin gates, the minimum per car, a climb gated on fewer
    than half its steps flagged thin and never passed, and the locked climb's transfer row gating
    nothing; and, after the sixth, the one half labelled DESIGN, the third step with no margin (a
    barred held gear that is the highest the road speed allows), the order in which these cases
    decide, a demand at or below zero included, and the reason for not taking the fifth review's
    reading restated; and, after the seventh, C5's outcome on a car as one of three exclusive cases,
    fails, thinly checked or passes, a thin climb that fails at a gated step failing C5 (section 5);
  - 74: a climb slot whose redraws reach decision 64's cap keeps the last climb accepted for it,
    never a discarded candidate, for every car, scored, and flagged gear-sensitive on each car on
    which it fails, and each such car's results are reported with and without its flagged slots
    (sections 5 and 7);
  - 75: a climb slot is shared by the four cars: a climb that fails on any car is redrawn for every
    car, every car's C5 is checked again on the new climb, the cap counts a slot's redraws over all
    cars, and a redrawn climb passes every test of a first draw, each as the first draw applies it,
    decision 34's ceiling on every engine (on the road set with the candidate in the slot), C5 with
    a gated step on every car and the roads step's own checks among them, the slots redrawn in their
    order on the roads, and, after the sixth review, a candidate filling its slot's recorded extent;
    the cost, a redraw moving every car's scored set on one engine's held-out E1a, disclosed
    (sections 5 and 7);
  - 76: decision 64's cap, at most 3 redraws per climb slot counted over all cars, and at most 100
    candidates discarded per slot, after which the slot keeps its last climb as at the cap, both
    fixed here before any fit and from no data; and the streams, one per slot, drawn with the first
    draw's code from `numpy.random.default_rng([roads_seed, 0xC5, k])`, fixed by the roads' own seed
    alone (the derivation written after the sixth review; sections 5 and 7).
- **What moved**, each by a decision above and none after a fit. No R or split moved.
  - **Statistics, and the inputs they are computed from.** C5's: its threshold (decisions 70 and
    40), its steps and which of them are gated, at the time step its road is scored at (decision
    73), and its re-check margin, read from E1a's worst deciding line, with every line's |E_l| +
    2u_val,l reported beside it (decision 64). E6 rows 1, 2, 3, 7, 9 and 12 (decision 59): rows 1, 3
    and 7 report how far the model in use moves; row 1 keeps the snap, which row 12 moves; row 2's
    E2, D1 and L0 must each move by less than its u_val; row 9 follows its order, names the flame
    terms and adds the rich slope, with the probe under every form; and every d row's probe is ±10
    %. The in-sample stage's form criterion (decisions 39(a), 49 and 55): E8 aside, each engine its
    own form, and a statistic with no calibration line neither blocking nor passing; and its R, this
    file's, L1's untightened (decision 71). And the inputs of the rows version 3 did not treat
    (decision 54): λ 1.00 for a fired row without λ, in no λ band; the model ECU's spark for a
    sentinel row, which enters no fit; and censored λ, defined on the calibration Final rows, with
    E8's list of the censored held-out Final rows, reported and not gated. Version 3 had no rule for
    any of these rows, and fed every row its `Spark Timing` as published. Version 4's readings of
    decision 54: a sentinel row's spark in D1, the model ECU's spark at EPA's MAP plus s·ΔMAP, and
    E8's dl without the rows that publish no λ and ds without the sentinel rows, each also reported
    with them and each needing at least 3 rows; and an empty `Spark Timing` cell read as the
    sentinel, and a Ford HD1 row with an empty bank as a row without λ. And the details version 3
    left open (decision 57): D1's pre-scan, bisection and nearer bound, D1 also reported without its
    unreachable rows, and form D's cam at the inverted MAP; E8's EPA λ unsnapped, the snapped E8
    reported, P's slope at a zero shift and its extrapolation, and the tightening's sign; and the
    worst line, defined, with its u. D1's and E8's `statistic` text in the JSON points at these
    details (`rows`, and so `thresholds`).
  - **Label and on-failure rules.** The refit rows 1, 3 and 7 label no exclusion, and their
    calibrations run before the held-out run; the Tests lists and their counting rule; row 12's
    order of labels, off > untested > limited > validated, and D1's κ under it, the larger of its
    two readings'; row 2's miss a finding, not a stop (all decision 59). C5's outcomes for a car and
    for a climb slot: a slot shared by the four cars, a climb that fails on any car redrawn for
    every car, each redraw passing every test of a first draw, and the cap counted over all cars
    (decision 75); the redraw streams, one per slot, fixed by the roads' own seed (decisions 64 and
    76), the cap, and a car with no passing climb reported as gear-sensitive when a slot is flagged
    on it and thinly checked when a climb is thin on it (decisions 64 and 73); a candidate filling
    its slot's recorded extent (decision 75); every slot at its cap keeping its last accepted climb,
    flagged on each car on which it fails (decision 74, read with 75); C5's outcome on a car one of
    three exclusive cases, fails, thinly checked or passes, a climb with no gated step on a car not
    passing, and one gated on fewer than half its steps flagged thin, never passed, and failing C5
    when a gated margin fails (decision 73); the cap's value, 3 redraws per slot, and the bound of
    100 discarded candidates (decision 76); the locked climb's transfer row gating nothing
    (decisions 34 and 44, as version 4 reads them); and E8 with a subset short of 3 rows having no
    statistic, which drops the engine (decision 54, as read; the JSON's `on_failure.d` names it
    since the seventh review, and the d entries of `thresholds` keep version 3's `on_fail`). L1's
    tightening measured on the B58, and the held-out run refusing one measured on any other plant
    (decision 71).
  - **Populations.** One that version 3 named moved: E8's. Version 3 took dl and ds over the
    held-out High Load Final rows; version 4 takes dl over those that publish a λ and ds over those
    that publish a spark, subsets of that population that each need at least 3 rows, and reports
    both over every Final row beside them (version 4's reading of decision 54, sections 3 and 4). No
    other population version 3 named moved. One was written where version 3 named none, and it
    narrows the plan's reading of version 3: C5's steps (decision 73). Version 3's "on every scored
    climb" named the climbs and not their steps, and `docs/build_step_2/PLAN.md` section 7.4 read it
    as every step; decision 73 leaves the transition steps out of the gate and reports them, and
    says where a scored climb starts and ends and which of its steps are gated, before any fit and
    before any road is drawn.
- **The code citations** (39(e); amendment A3). Build step 2's WP1 moved or removed every line
  version 3 cited in `plant.py`, `thermal.py`, `engine_env.py` and `engine_specs/b58.toml`: version
  3's `LHV` and `AFR_STOICH` constants are gone, and the fuel is each engine's `engines.Fuel`. Every
  code citation of this file, sections 11 and 12 included, now gives its line in the tree version 4
  was written on, most with the function or record beside it, and the table below names what each
  one cites, so that it can be found again when the lines move; version 3's file (`ef5e14e`) keeps
  the old lines. **Step 7 checks the citations into the plant code, and the table's version-3
  lines.** Every `file:line` of this file and of the JSON into PLANT_CODE (`fingerprint.PLANT_CODE`)
  or `engine_specs/`, which amendment B5 freezes after commit A, is pinned in
  `thresholds/document.py` (`CODE_CITES`) with a text its line must hold, and the generator stops if
  a citation is not pinned or a pinned line no longer holds its text; `--check` on commit A's tree
  is that check on commit A (below). Every line of the table's version-3 column is pinned the same
  way (`V3_CITES`), against `ef5e14e`'s tree read through git. Citations of documents are not
  pinned, since those files are not frozen; each citation of `REFERENCES.md`, which WP7 edits after
  the first fit, when this file can no longer be rewritten, carries its row's own text beside the
  line. The decision sheet's citations are the exception: each is pinned to its row's text
  (`SHEET_CITES`, after version 4's fourth review), since the sheet is the document most likely to
  be edited before version 4 is committed, and after the first fit the claims that nothing has been
  fitted stop step 7 anyway. **Step 7 also resolves every other citation** (version 4's third
  review; amendment A3's scan). Each `file:line` of this file and of the JSON must name a file of
  the repository that holds the cited lines, read as written or under `results/`, or one of the
  files Appendix A quotes from outside it (`CATALOGUE.md`, `fe_out/`); a citation of an EPA table
  (`data/engines/<id>/epa_*.csv`) is resolved by the file's existence alone, since the generator
  opens no `epa_channels.csv` and none of version 4's sessions opened an EPA table. The scan checks
  a file and its range, not the text: a document's line that moved inside its file is not caught,
  and each was read at its line when version 4 was written, as each code citation was.
  `data/engines/` is byte for byte version 3's. **The docstrings of steps 3 and 5**
  (`thresholds/b58_propagation.py`, `thresholds/ecu_shift.py`) still give version 3's
  `engine_env.py` lines, on purpose: steps 1-5 did not run again, and the sha256 the JSON's
  `generators` records for each is that of the code that wrote the outputs version 4 reads. They are
  remapped when those steps are next edited and run. The moves:

| what is cited | version 3 (`ef5e14e`'s tree) | version 4 |
|---|---|---|
| gasoline's LHV | `plant.py` line 42 (`LHV`), `thermal.py` line 245 (the network's 44.0e6) | `engines.Fuel.lhv_j_per_kg` (`engine_specs/b58.toml:201` on the B58), read at `plant.py:233` and `thermal.py:255` |
| gasoline's AFR_st | `plant.py` line 43 (`AFR_STOICH`) | `engines.Fuel.afr_st` (`engine_specs/b58.toml:202`), read at `plant.py:220` and `:233` |
| `combustion_efficiency` | `plant.py` lines 54-60 | `plant.py:58-72` |
| VE's breathing curve | `plant.py` lines 63-66, called at line 160 | `plant.py:99` (form A's line of `volumetric_efficiency`) |
| the fuel mass, the wall temperature | `plant.py` lines 163, 165 | `plant.py:220`, `:222` |
| the fixed valve events | `plant.py` line 193 | `plant.py:250` |
| UA_PORT, typed; the exhaust temperature | `plant.py` lines 278-281, 281-287, 286-287 | `plant.py:335-338`, `:338-344`, `:343-344` |
| the housing node | `thermal.py` lines 265-275 | `thermal.py:275-285` (`ThermalNetwork._substep`) |
| `ua_turb_amb`, `ua_gas_turb` | `engine_specs/b58.toml` lines 124-125 | `engine_specs/b58.toml:166-167` |
| the knock-limited surface | `engine_env.py` lines 169-193 | `engine_env.py:177-201` |
| `BaselineECU.step` | `engine_env.py` lines 356-376 | `engine_env.py:394-414` |
| `damage_rate` | `engine_env.py` lines 690-696 | `engine_env.py:972-978` |
| `ACT_LO` (the λ trim's −0.15) | `engine_env.py` line 698 | `engine_env.py:980` |
| `PREVIEW_S` | `engine_env.py` line 711 | `engine_env.py:993` |
| the environment's cycle call, the load loop | `engine_env.py` lines 761, 784 | `engine_env.py:1053`, `:1076` |
| the ECU's call; the spark and λ trims and clips | `engine_env.py` lines 982, 1004, 1004-1006, 1006 | `engine_env.py:1283`, `:1310`, `:1310-1316`, `:1316` |
| the baseline-relative reward; `t_ref` | `engine_env.py` lines 1020-1031, 1022 | `engine_env.py:1330-1341`, `:1332` |

- **What did not move.** Every R, split, population, statistic, convention and label rule not named
  above. The JSON's per-threshold values (the engine, row, kind, part, R and unit of each of the 82
  entries of `thresholds`), every entry of `thresholds` but C5's, D1's and E8's, D1's and E8's but
  for their `statistic`, C5's but for its `statistic` and `on_fail`, and the `engines` section are
  version 3's: the generator checks each against a digest of version 3's before it writes this file,
  and stops if one differs. D1's and E8's `statistic` changed after the fourth review, so that a
  script reading `thresholds` alone is pointed at version 4's details of their statistics; their R,
  unit and every other field are version 3's.
- **The JSON's `schema` is 4**, the contract's own numbering (not the fingerprint's schema 4 of
  decisions 27-28 and 47). New keys hold the rules version 3 had no field for:
  `model_form.in_sample_rules` and `model_form.neutral_action_identity`;
  `conventions.lambda_missing`, `.spark_sentinel`, `.held_out_counts`, `.censored` and
  `.statistic_details`; `tests_lists`; C5's `steps`, `threshold` and `redraw` in `cars`; decisions
  39, 40, 49, 54, 55, 57, 59, 64, 70, 71, 73, 74, 75 and 76 in `decisions`; and `version_4`, which
  lists them and records the plant values. Every key of version 3 is kept with its meaning, and no
  other key was added: the generator checks the set of key paths, list entries included, against
  version 3's. That check sees keys, not the strings a list holds: `open_for_the_team` grew from one
  entry to four, `seen_before_writing` gained nine entries, one for each of version 4's sessions,
  and `order_of_work`'s entries were reworded, none of which it covers; this section names what they
  say.
- **Not rules of this contract.** Decision 69, the Ford's fuel in use: every row runs on its own
  table's fuel (section 3). Decision 72, the Mazda's stroke: this file names no stroke. Decision 65
  reads the contract as version 3 wrote it (`order_of_work` puts the roads and the L1 and E8
  tightenings before the held-out run) and adds no text. Decision 58 (held-out rows outside the
  calibration MAP range are flagged per row, and every statistic is also reported restricted to the
  calibration coverage beside it, never relabelled) is a reporting procedure of the validation
  script, stated in section 3 beside the other duties to report a statistic both ways; the script
  reads this file's coverage records (`engines.<id>.coverage.calibration_fired` and
  `.calibration_hot` in the JSON). Decision 39(d) does not name it among the rules this file takes,
  and it moves no R, population, statistic or label.

**Reviewed before it was committed.** A first adversarial review of 23 October 2026 re-ran the
checks above and raised six must-fix items, each corrected before this file was written again: C5's
step population, which the first draft left to the roads step after the fit, is now decisions 73 and
74, written as rules (section 5); C5's threshold where the box takes no torque decision is defined
(section 5); this section misread 39(c); the header said that no statistic moved; decision 58 was
said to add nothing; and the B58's clip bounds were literals, now filled from the plant code and
checked. Its should-fix items were taken too: the contact's float32 comparison and the clips that
count (section 4), the flame terms named in E6 row 9, the bar's rpm margin defined, the refit rows'
place in the run, the documented sensor floor and the fuel convention's scope (section 3), decision
40 in the JSON's `decisions`, the key-path check entering lists, the JSON's file-less citations, the
plant values recorded, and the check of the code citations above.

A second adversarial review, the same day, re-ran every check and raised two must-fix items, both
corrected before this file was written again. This section's account of what moved left out E6 rows
1, 2, 3 and 7, decisions 49 and 55, and decision 54's inputs, and it said that 73's and 74's text
came from the amendments; the lists above are now complete. And C5's barred downshift could be read
two ways, which give opposite answers on amendment F3's CX-9; section 5 now says that the bar
applies whenever the lower gear is barred. Its should-fix items were all taken: 73 and 74 marked as
pending Ghassan's own answer, to be asked before the commit (after the fourth review they are
adopted under the delegation, as the rest of section H is, below); decision 40's diagnostic of N*
restored for the CVT (section 5); the spark bounds' type, which no code checks, asserted by the
identity check (section 4); decision 73's transitions extended to changes of speed, with at least
one gated step on every scored climb (section 5); a row without λ placed in no λ band, and E8's dl
and ds defined for the rows without λ or spark (section 3); section 10's need for `ef5e14e`; what is
open completed (below); decision 58's reporting duty stated in section 3; the `REFERENCES.md` rows
cited by their text; the version-3 lines pinned (`V3_CITES`); the condition on commit A's tree
(below); and three points of wording, the d rows' ±10 % probe among them (section 4).

A third adversarial review, the same day, re-ran every check and raised two must-fix items, both
corrected before this file was written again. Under form C, E6 row 9 gave the rich slope only its
fit's σ, the band section 4 says a probe must not be sized by, so whether E4a and E4b are excluded
for the slope was undefined; row 9 now gives the slope the probe under every form, as rows 5 and 6
give theirs (section 4, E6). And this section said that decision 57 added no text, when it adopts
details version 3 left open, one of which, E8's snap, moves E8; they are written as decision 57's
(sections 3 and 4). Its should-fix items were all taken: the draw a slot keeps at the cap when its
car has no passing climb, and a scored climb's extent and end steps (section 5); the narrowing of
the plan's reading of C5's population, said in the header; every citation resolved by step 7, which
makes that scan part of the condition on commit A's tree (above and below); the decision sheet's
columns for decisions 73 and 74 left empty (filled after the fourth review, below), and its 21
October box dated (section H); the docstrings of steps 3 and 5 explained (above); the STARTED record
a fit writes first (below); E8's and D1's rows without a reading (section 4); the wording of a step
with no torque decision (section 5); and where the B58's locked climb runs the neutral-action
identity (section 4).

A fourth adversarial review, the same day, re-ran every check and raised one must-fix item,
corrected before this file was written again. Decisions 64 and 74 never said whether a climb slot is
one car's or all four cars', so the redraw, the cap and decision 74's slot could not be applied as
written, and a roads script would have chosen after the fit, with E1a in hand. Decision 75, written
into section H with this correction and adopted under the delegation, makes a slot shared by the
four cars, as decision 34's one road set requires, and section 5 writes it as a rule. Its fifteen
should-fix items were all taken: D1's and E8's `statistic` text in the JSON pointing at version 4's
details, with the unsnapped λ moved out of E8's population (above); decisions 73 and 74 adopted
under the delegation, as section H adopts every decision, so that the JSON, this file and the sheet
say the same; the JSON's summaries of 73 and 74 completed; section 8's open list made the same as
this section's; the readings of decision 54 credited to it as version 4's, each with its reason and
noted in its row (section 3); E8's population said to move (above); form D's cam in D1 (section 4);
D1's κ under E6 row 12 (section 7); the worst deciding line defined, and C5's margin's reading of it
disclosed (sections 3 and 5); the in-sample stage's R for L1 (section 2.4); decision 73's exact
comparison and the share of transition steps, with the other reading recorded in its row (section
5); why rule 0 lets the redraw stream and cap be set with the roads (sections 5 and 7); section 7's
C5 row completed; decision 40's diagnostic placed with the roads step (section 5); and the decision
sheet's citations pinned to their rows' text (above).

A fifth adversarial review, the same day, re-ran every check and raised three must-fix items, each
corrected before this file was written again. Section 7 said that nothing set after the first fit
changes after the held-out run, when section 5 redraws failing climbs then; it now says that the
redraw is the one change, and that the tightenings stay as measured on the roads as first drawn. The
redraw cap had no value and no rule for one, left to the roads step after the first fit, when the
in-sample E1a is known; decision 76, written into section H with this correction, fixes it here,
with a bound on discarded candidates and the stream's seed (section 5). And E8's two subsets had no
declared outcome when one is short; each now needs 3 rows, or E8 has no statistic (section 4). Of
its eight should-fix items, seven were taken in full: the readings the agents added to decisions 54,
59 and 64, and decisions 73-76, named in the sheet as rows Jad and Ghassan must answer, Ghassan's
cells for them marked, and the sheet's note of 23 October moved out of the quote of his answer of 21
October, its cited lines kept where they were; E8's subsets stated in the JSON's `thresholds`
entries, in its `version_4` record and in the header; a redraw's tests, each applied as the first
draw applies it, the slots' order, the discard bound and the time step (section 5); the locked
climb's transfer row (section 5); a gated step defined, with the minimum per car (section 5);
decision 75's summary in the JSON completed; and the lists the key-path check does not cover
(above). One was taken in its lesser form: decision 73 keeps its transitions, the changes of speed
among them, and a climb that C5 gates on fewer than half its steps on a car is flagged thinly
checked there, never passed (section 5). The review's reading, gating every step outside a fixed
neighbourhood of an actual change of gear or of the CVT's branch, is recorded in decision 73's row
as an option and not taken: it makes the transition steps each car's, set by where its calibrated
model changes gear, and it needs a neighbourhood width that nothing here sets.

A sixth adversarial review, the same day, re-ran every check and raised two must-fix items, both
corrected before this file was written again. This section, section 8 and the JSON said that the
first fit waits for Jad's column alone, when the sheet asks Jad and Ghassan both to answer decisions
73-76 and the readings of 23 October before it; they now say that the first fit also waits for
Ghassan's own answer to those (above and below). And this section said that the numbers version 4
adds count the JSON's entries or come from the plant code, when it adds four rule constants, three
of them DESIGN, chosen from no data; it now names them (above), and section 5 labels the thin share
DESIGN, with its reason. Of its eleven should-fix items ten were taken: the discard bound named in
section 7's rule-0 paragraph; a thinly checked climb said to neither pass nor fail, so that it does
not make its car gear-sensitive (section 5, as decisions 64 and 73 are read; made exact by the
seventh review, below); the order in which the gated-step cases decide, a demand at or below zero
included, and the third step with no margin, a barred held gear that is the highest the road speed
allows (section 5); the redraw streams' derivation fixed here, one stream per slot (section 5,
decision 76); a candidate filling its slot's recorded extent (section 5, decision 75); the climb a
slot keeps, never a discarded candidate (section 5); an empty `Spark Timing` cell and a Ford HD1 row
with an empty bank given their treatment (section 3); the reason for not taking the fifth review's
reading of decision 73 restated, its per-car objection withdrawn (section 5); and E8's list of the
censored held-out Final rows (section 3). Each reading is noted in its decision's row. The eleventh,
the team's dated copy of the sheet with these rows marked for both columns, is a step of the commit,
not of this file, and is left to it, as the copy for decision 72 is
(`docs/build_step_2/HANDOFFS.md`, commit A item 12).

A seventh adversarial review, the same day, re-ran every check and raised two must-fix items, both
corrected before this file was written again. Section 5 said both that a thinly checked climb is
redrawn when it fails C5 at a gated step, and flagged gear-sensitive at the cap, and that it neither
passes nor fails C5 and does not make its car gear-sensitive, so a slot at the cap that keeps a thin
climb failing on a car had opposite answers, and a redraw's C5 test could be read to refuse a thin
candidate the first draw accepts. C5's outcome on a car is now one of three exclusive cases, a thin
climb that fails at a gated step fails C5, and both draws accept a thinly checked candidate and flag
it thin (section 5; step 7 checks the case table). And this section's list of the numbers version 4
adds left out the values decisions 54 and 57 state; it now lists them (above), and step 7 checks
each against the JSON's `conventions`. Of its eleven should-fix items six were taken: the JSON's
`on_failure.d` names E8's short subset as the third way a d row has no statistic, as section 7 does;
an empty `Spark Timing` cell enters no fit, and a held-out Final row reading below the censoring
value is not counted censored (section 3); section 2.2's note on the Ford's 3500 rpm line follows
amendment F3; decision 73's row reads its "is redrawn" for a climb with no gated step as the
contract does, a climb discarded at the draw; and the open list names the team's Desktop copy of the
sheet (below). Five are left for a later version, written before any fit, and the open list says
what each leaves (below).

**What is open.**

- **Jad's column, and Ghassan's own answer to what the agents added on 23 October.** Jad's column of
  decisions 36-38 (section G) and 39-76 (section H, 66 dropped) is empty. Ghassan's column of both
  sections records his delegation of 21 October; for decisions 73-76, and for the readings the
  agents added to decisions 54, 59 and 64 on 23 October, it records only that delegation, not an
  answer of his, and their cells say so ("adopted by the agents 23 Oct, not yet seen"). The first
  fit, Run 1, waits for both: Jad's column, and Ghassan's own answer to those rows and readings, the
  four rule constants version 4 adds among them (above), as the sheet's note of 23 October says
  ("Both of them answer these rows and readings before the first fit"). They answer from the team's
  dated copy of the sheet on the Desktop, `C:/Users/badcl/Desktop/decisions_2026-10-22_H.md`, which
  holds section H as of 22 October, without decisions 73-76 and the readings of 23 October: the
  commit step updates it with the sheet as committed, before either of them is asked (after the
  seventh review). An answer of Jad's that differs from the adopted option, or a different answer of
  Ghassan's, given before the first fit, is applied before it: in the code, and, where the decision
  is a rule of this file, through a new version written by this generator. Once `calibrate_epa.py`
  exists, step 7's claims that it does not and that only the generator, `epa_map.py` and
  `test_epa_map.py` name the EPA tables stop the generator, so such a version also edits those
  claims. The edited claims must still prove that no fit has run, from what a fit leaves behind, as
  the claims that nothing a fit writes exists do now: no output of `calibrate_epa.py` under
  `results/EPA_CALIBRATION/` (`stage0.json`, `fit_<form>.json`, `freeze.json`,
  `docs/build_step_2/PLAN.md` section 8.1), no EPA engine's `data/engines/<id>/derived_params.json`,
  and no record of the held-out run under `results/EPA_VALIDATION/`. A fit that crashed before
  writing an output would leave none of these, so `calibrate_epa.py` writes a STARTED record under
  `results/EPA_CALIBRATION/` before its first model evaluation, as the held-out run writes one
  (decision 60), and the edited claims require that record to be absent; today's claim, that nothing
  exists under `results/EPA_CALIBRATION/`, already does. That version's own section says which
  claims it edited, and why.
- **Commit A's tree.** Decision 39 has version 4 generated after the plant commit, commit A. It was
  written on `4461a91`, before that commit, and its code citations are pinned to this tree, its
  citations of the decision sheet to their rows' text. Version 4 is committed only after `python
  engine_thresholds.py --check` exits 0 on commit A's tree: its claims include the pins of
  `CODE_CITES` and `SHEET_CITES` and the scan of every other citation (above), which amendment A3
  asks to resolve every `file:line` "against the commit-A tree". If a pin or the scan fails there,
  the citations are remapped and both files regenerated before the commit, still before any fit
  ("Remap against commit A's tree, not before", `docs/build_step_2/HANDOFFS.md`, WP2 item 1).
- **Left to later steps, by rules written here:** the roads' own seed, which fixes C5's redraw
  streams through the derivation of section 5 and is committed with decision 34's roads, after the
  freeze and before any held-out statistic, and never changed after the held-out run (decisions 64
  and 76; section 5, where rule 0's reach over it is said; the derivation, the cap and the discard
  bound are fixed here), and the roads themselves, with the time step they are scored at, on which
  C5's steps are counted; how the Ford's Cell 9 rows, of another fuel batch than HD1's, treat the
  octane, declared by the calibration scripts before they are committed (section 3;
  `docs/build_step_2/HANDOFFS.md`, WP3 item 5); and a documented λ-sensor floor, which only a source
  opened and cited before the fit can set (section 3).
- **Left by the seventh review for a later version of this file**, written before any fit, since the
  roads step that needs the answers runs after it, one question each:
  - whether a road of decision 34 is one grade array and one speed array that every car reads, so
    that a generator whose arrays depend on the car, as the extremes kind's do
    (`engine_env.extreme_speed_profile`), cannot draw a shared slot (section 5);
  - whether the cars and the preview ceilings of EPA engines that the held-out run drops (section 7)
    take part in the re-check and in a redraw's tests (section 5);
  - by what rule, written before it runs, the roads step takes roads_seed, and whether it records
    every seed it ran (section 5);
  - whether a candidate's extent is an input of the first draw's code or a property its draw must
    match (section 5);
  - and none from the fifth item left, four citations of lines outside the repository that Appendix
    A does not quote and the scan resolves by the file's name alone: it leaves the roads step
    nothing to settle, and that version quotes them or tightens the scan.

## 14. Version 5: decision 77, before any fit

Written 23 October 2026 by `python engine_thresholds.py --build-only`, on the tree of `cfe6211`
(version 4, `a1b88e6`, and its checkpoint; the plant code is commit A's, `7a40b9f`), in a worktree
of its own, and before any fit. No step of 1-5 re-ran: the JSON's `generator_inputs_sha256` and
`epa_tables_sha256` are version 3's, and so is every number computed from steps 1-5. Version 5 adds
no number computed from data and no rule constant. It writes one decision of section H as a rule of
this file, decision 77, and records one order of Ghassan's.

**Why.** T0, the synthetic recovery of `docs/build_step_2/PLAN.md` section 5.10, generates outputs
from a known truth at the calibration rows' input columns and runs the whole fitting procedure on
them, and it passes only if, among other things, "the A-truth seeds stop at A". Run on 23 October
2026 at the production crank step (12 jobs, 587 s, as reported to the session that wrote version 5),
it failed under version 4's criterion, every in-sample statistic but E8 at |E_cal| ≤ R: a form-A
truth climbed the ladder to A+B+C+D, because its in-sample E4b failed at every form from noise
alone. The truth lies in form A, so the data asked for none of the terms the ladder added: version
4's criterion counted a statistic's own sampling noise against the form. Decision 77, written into
section H with this version and adopted under Ghassan's delegation of 21 October as every decision
of that section is, applies to the in-sample stage the rule the held-out rows already follow, the
off rule |E| − 2·u_val > R, with the sampling term the in-sample stage has, u_stat. It moves no R,
split, population or statistic, and was decided before any fit, on synthetic data only.

**Rule 0, and T0.** As the plan specifies T0 and as its run was reported to version 5's session, T0
ran the fitting procedure on synthetic rows: it read the calibration rows' input columns, not their
outputs (`docs/build_step_2/PLAN.md` section 5.10: "No EPA output is read"), and compared no model
with an EPA torque, fuel or TIT value. Version 5 reads the fit of rule 0 as a fit to EPA data, Run
1's calibration, as this file's claims that nothing has been fitted read it (section 10): they check
that no `calibrate_epa.py`, no output of one and no EPA engine's derived file exists, and they hold
on the tree version 5 was written on. The plan runs T0 before that fit, "after the contract version
is final" (its WP3). T0 ran under version 4, and the failure it found is in version 4's criterion, a
rule of this file, which only a version written before the fit can change; version 5 is that
version.

**What changed.**

- **The in-sample stage's form criterion** (section 2.4; the JSON's `model_form.in_sample_stage`,
  `in_sample_rules.form_per_engine` and the new `in_sample_rules.sampling_noise`). Version 4: an
  engine's form is the first at which every one of its own in-sample statistics but E8 satisfies
  |E_cal| ≤ R. Version 5: the first at which none of them fails, a statistic failing only when
  |E_cal| − 2·u_stat > R; one that does not fail and has 2·u_stat > R neither blocks nor passes, and
  is recorded per form, as decision 55's statistic with no calibration line is; and u_stat is the
  held-out rows' own (section 3). E8 stays outside the criterion (decision 39(a)), a statistic with
  no calibration line still neither blocks nor passes (decision 55), and the R is still the one this
  file states for each row, L1's untightened (decision 71).
- **Version 5's two readings of decision 77** (section 2.4, and noted in decision 77's row): a
  statistic that fails beyond its noise fails the form whatever its 2·u_stat, and a per-line row is
  tested line by line. The agents writing version 5 wrote them on 23 October, each with its reason,
  and neither Ghassan nor Jad has seen them.
- **The go-ahead.** On 23 October 2026 Ghassan ordered Run 1 to go ahead before Jad's column of
  decisions 36-77 is filled ("go ahead without it"), as X1 went ahead on his order on 8 October. It
  is recorded at the top of sections G and H of the decision sheet, in section 8 and in the JSON
  (`open_for_the_team`, `version_5.go_ahead`). It is an order, not an answer to any row, and it
  changes no rule of this file.
- **The text around them:** the header, section 8's open items, sections 9 and 10, and the JSON's
  `_generated`, `decisions.77`, `open_for_the_team`, `seen_before_writing` (one entry appended,
  version 5's session) and `version_5`, this version's record.

**What did not move.**

- Every R, split, population, statistic, convention and label rule, and every rule of the model form
  but the in-sample criterion. Every part of version 4's JSON (`a1b88e6`) but the strings named
  above is version 5's, every number, R and rule included, and every key path of version 4's is
  kept: step 7 checks both against digests of version 4's JSON (`thresholds/document.py`,
  `V4_DIGESTS`, which it also checks against version 4's JSON read through git), and stops if one
  differs. Version 3's digests (section 13) still hold. The held-out stage, its labels and section
  7's on-failure rules are version 4's: decision 77 is a rule of the in-sample stage, whose
  statistics are fit residuals and are never labelled.
- **Version 4's record is kept as version 4 wrote it:** section 13 here, whose counts of version 4's
  entries step 7 reads from version 4's JSON, and `version_4` in the JSON, which the digest above
  covers. Where section 13 says what holds the first fit, section 8 and this section give the state
  under version 5.
- **The JSON's `schema` stays 4.** Version 5 adds three keys, each of a kind schema 4 already has:
  decision 77's entry in `decisions`, its rule in `model_form.in_sample_rules` (`sampling_noise`,
  with fields of its own), and `version_5`, this version's record beside `version_4`. Every key of
  version 4 is kept where it was, with its meaning, so a script that reads schema 4 reads version 5
  unchanged. The strings that changed are the ones named above, and `generators.sha256`, the
  generator's own hashes.

**What is open.**

- **Jad's column, and Ghassan's own answers.** Jad's column of decisions 36-38 (section G) and 39-77
  (section H, 66 dropped) is empty. Ghassan's column records his delegation of 21 October; for
  decisions 73-76 and the readings the agents added to decisions 54, 59 and 64 on 23 October it
  records only that, not an answer of his ("adopted by the agents 23 Oct, not yet seen"); decision
  77's cell reads "delegated 21 Oct: adopted", and version 5's readings of it have been seen by
  neither of them. Run 1 no longer waits for these answers, on Ghassan's order above. Jad's answers
  stay his to give. An answer that differs, given before the first fit, is applied before it, as a
  new version written by this generator; given after it, it cannot change version 5 or the frozen
  calibration (rule 0), and becomes a new contract version and a new fit, reported beside this one.
  They answer from the team's dated copy of the sheet on the Desktop (section 13); version 5's
  session did not open it, and the commit step brings it up to the sheet as committed, decision 77
  and the go-ahead included, before either of them is asked.
- **T0 under version 5.** `docs/build_step_2/PLAN.md` section 5.10 passes T0 only if the A-truth
  seeds stop at A and the B-truth seed's ladder stops at A+B. T0 has not run under version 5's
  criterion, and whether it passes is not known to this file. The in-sample stage that applies the
  criterion is WP3's, in scripts not committed when version 5 was written; it reads
  `model_form.in_sample_rules.sampling_noise`.
- **The seventh review's questions** (section 13). Version 5 does not settle them, and Run 1 goes
  ahead with them open. A version written before Run 1 may still settle them; one written after it
  is, by rule 0, a new contract, disclosed, with every result reported under both.
- **The claims that nothing has been fitted** hold on the tree version 5 was written on. Once
  `calibrate_epa.py` is committed, step 7's claims that it does not exist and that only the
  generator, `epa_map.py` and `test_epa_map.py` name the EPA tables stop the generator, so a later
  version edits them, still proving from what a fit leaves behind that no fit has run (section 13).
- **No review.** Version 5 has had no review; version 4 had seven.
- The rest of section 13's open list stands: the roads' own seed, the roads and the time step they
  are scored at; the octane of the Ford's Cell 9 rows; a documented λ-sensor floor.

## Appendix A. Lines cited from outside the repository, verbatim

`C:\Users\badcl\Desktop\GRAD-engine-data\CATALOGUE.md`:

- `:150` "**Steady State:** speed fixed by the dynamometer, pedal fixed, held until torque, fuel flow
  and exhaust temperature are stable, then "logged for 10 seconds at 10 hertz sampling and
  averaged". Table 7 of the same report says "30 sec avg". The Ford Cell 9 report says "30 seconds
  at 10 hz". These points lie below the load where enrichment starts."
- `:151` "**High Load Initial / Final:** the "stab test". The pedal is held at about 1/3 load,
  ramped over 1 s to the target torque, and held for about 30 s, logging at 100 Hz. The Initial
  window is the maximum torque within 2 s of reaching the target. The Final window starts once
  torque and fuel are stable, never earlier than 2 s. Only the two window averages are published.
  The 100 Hz traces, which would show the protection transient, are not in any package."
- `:153` "**Rig:** stock exhaust with catalyst, and a cooling tower at 85 °C in place of the
  radiator. Oil is held at 90 °C. Charge air is held at 30–40 °C for Mazda and Honda; Ford controls
  the airflow through its stock intercooler."
- `:162` "The reports say the engine has "manufacturer specific protection modes that are not
  controllable in the test cell"."
- `:165-167` "**Mazda:** Tier 2 26864 (RON 97.6, (R+M)/2 93.3, 42.91 MJ/kg, 0 % alcohol); Tier 3
  26781." / "**Honda:** Tier 2 25842 (RON 96.1); Tier 3 25206." / "**Ford:** Cell 9 Tier 2 25278;
  Cell 9 LEV III 24670; HD1 Tier 2 26864; HD1 Tier 3 25402."
- `:289` "… It is therefore the same certified configuration. Whether it is the same engine
  calibration as EPA's engine is UNVERIFIED: they are different vehicles."
- `:291` "Fuel heating value is 18,659 BTU/lbm for tests 61704001–044 and 17,972 for 61704045–072."
- `:654-657` "**D3 padding rows.** 17 files end with 298–300 rows whose timestamp is frozen at the
  last value, about 30 s of copies … Drop every row after the first occurrence of the maximum time."
- `:662-663` "**D3 scan-tool channels refresh slower than 10 Hz** (mistake 13b). … the PCM and PGM
  channels (MAF, MAP on the CX-9, boost, wastegate, spark, knock retard, λ/AFR, catalyst value)
  change on only 15–57 % of samples, holding for 3–9 samples at the 90th percentile"
- `:681` "**Accord ≠ L15B7.** The D3 driving data and the EPA map belong to different calibrations
  and hardware ratings: 143 kW and 260 N·m at CR 10.3, against 130 kW and 220 Nm at CR 10.6."
- `:686-690` "**Turbine-housing (metal) temperature:** no source measures it, for any engine. …
  **Protection transients:** EPA logged them at 100 Hz but published only window averages."

`fe_out/` (the scratchpad folder of section 9):

- `design.md:59` "Calibrate the B58's own cycle per engine. This keeps one model form (mistake 20).
  The maps have no spark or λ sweeps, so those sensitivities come from the physics (mistake 12)."
- `design.md:96` "| climb asks (EPA load) | 109 kW, 38 % | 133 kW, 79 % | 100–119 kW, 77–92 % of 130
  | 143 kW, 59 % |"
- `design.md:180` "Its climb-cell gas is 1022 °C (`results/DAMAGE_CONSTANTS.md:35`). Settled EPA TIT at
  2500–3000 rpm and 13–16 bar is 723–816 °C."
- `strand_repo-stats-timing.md:140` the table header "torque (% of max(|T|, 40 Nm)) MAE / p95 / max
  | EGT K MAE / p95 / max | knock integral, relative MAE / p95 | ki > 1 agreement"
- `strand_repo-stats-timing.md:159` "| X1 sighted 4 / blinded 4 | 0.60 / 51.04 | −0.87 / 50.37 |
  −1.47 / −0.67 |"
- `strand_repo-stats-timing.md:165` "Pair d, exact → surrogate: … The largest change is 1.14 points."
- `strand_repo-stats-timing.md:167` "The denser grid did not shrink these cut differences (max 1.48).
  The likely cause is the baseline car's +0.7 % damage bias and discrete ECU events such as the
  knock-retard flag. UNVERIFIED."
- `strand_vehicles.md:97` "| rolling radius | 0.3645 m measured on D3: gears 3–6 agree within 0.2 %,
  turbine rpm per mph 74.8 / 51.6 / 36.5 / 31.0. EPA N/V 30.5 gives 0.3704 m | DATA |"
- `strand_vehicles.md:104` "| converter | locked (<60 rpm slip) in 6th: 96.6 % UDDS, 96.0 % HWY,
  88.0 % US06; mostly slipping in 1st–3rd | NH519 Tables 15–17 |"
- `strand_vehicles.md:194` "On the locked climb each car settles in a different gear: Supra 7th at
  2718 rpm / 383 Nm …, CX-9 4th at 4173 rpm / 305 Nm, F-150 4th at 3470 rpm / 392 Nm, Accord at high
  rpm on the CVT."

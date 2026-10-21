<!-- template: engine_thresholds.py (step 7) fills every {{NAME}} from the run, wraps every line that starts with "@wrap ", drops this line and writes results/ENGINE_THRESHOLDS.md. Edit this file, never the .md; then python engine_thresholds.py --build-only. -->
# Validation contract: the three EPA engines and the table backend

<!-- written by python engine_thresholds.py from thresholds/document_template.md: never edit it by hand -->

@wrap **Version 3, written 21 October 2026 on `GRA-test`, before any calibration: version 2 with decisions 36-38 applied, written by its generator, `engine_thresholds.py`, which is committed beside it.** Version 1, written the same day, was reviewed the same afternoon. The review's 37 findings were each reproduced, and every one that held was applied in version 2; section 11 lists them with the verdict and the change. Version 3 applies decisions 36-38 of `results/VALIDATION_DECISIONS.md` section G, adopted 21 October on Ghassan's delegation: b = MEI/6 per part (section 1.3), the collapse test's equivalence margin the MEI (section 1.1), and an untested row as a preregistered band (section 7); section 12 lists every change. Decision 35 asks that torque, fuel and turbine-inlet temperature be checked "against held-out EPA points, with each required accuracy derived from its consequence on the MEI (VALIDATION_PLAN.md's method) and committed before calibrating; the table gates likewise" (`results/VALIDATION_DECISIONS.md:158`, answered 21 October, both agree). Decision 28 lets an engine train on its table "only if it passes accuracy gates derived from the MEI (fixed before the table is built for a new engine)" (`:151`). This file is both, for the Mazda 2.5 L turbo (`mazda_25t`), the Honda 1.5 L L15B7 (`honda_l15b7`) and the Ford 2.7 L twin turbo (`ford_27tt`), and for every engine's table, the B58's included.

@wrap `results/ENGINE_THRESHOLDS.json` holds the same contract for the scripts: every R, the split, the populations, the held-out rows by table and spreadsheet row, a flat list `thresholds` of (engine, row, kind, part, statistic, R, unit, rows, on failure), the B58 measurements behind every coefficient, the D3 files C3 may read with their sha256, and the sha256 of every file of the generator that printed a number here (`generators`) and of every step output it read (`generator_inputs_sha256`). `calibrate_epa.py` and the validation and table scripts read it and record its sha256 in every output. Both files are written by `python engine_thresholds.py` (section 10), and neither is edited by hand.

@wrap **Nothing has been fitted.** In the sessions that wrote this file (version 2's, and version 3's, which turned version 2's scripts into the generator and ran it) no model was run on an EPA row and no model-versus-EPA error was computed. `calibrate_epa.py` does not exist in the working tree, and no script in the tree runs the cycle on an EPA table: the files that name the EPA tables are `epa_map.py` and `test_epa_map.py`, which export and test them, this file's generator (`engine_thresholds.py` and `thresholds/`), which reads their structure, and `engines.py`, `derived.py` and `derive_params.py`, which name the per-engine folders. Other sessions were editing this branch at the same time, and what they ran is not known to this file. The EPA tables were read for their structure only: speeds, manifold pressures, BMEP, λ, intake and coolant temperatures, the fuel report, which columns are present, and each channel's range. Section 9 lists everything that was seen.

> **Rule 0. Nothing in this file changes after any fit runs:** no R, split, population, statistic,
> convention or rule of the model form, for any engine, the B58's table included. A change after
> that point is a new contract; it is disclosed, and every result is reported under both.

## The thresholds

| row | what is compared | statistic | R | kind |
|---|---|---|---|---|
| E1a | brake torque at EPA's inputs, hot rows | worst deciding line's mean signed relative error | **{{R_E1a:.1f}} %** | level |
| E1b | brake torque, fired rows | mean absolute relative error | descriptive (worth b at {{WB_E1b:.1f}} %) | — |
| E1i | brake torque, High Load Initial rows (a transient) | mean signed error per line | descriptive | — |
| E2a | fuel flow (Coriolis meter), hot rows | worst line's mean signed relative error | **{{R_E2a:.1f}} %** | level |
| E2b | fuel flow, fired rows | mean absolute relative error | descriptive (worth b at {{WB_E2b:g}} %) | — |
| E3a | turbine-inlet gas temperature (TIT) at λ≈1, hot rows | worst line's mean signed error | **{{R_E3a:.1f}} K** | level |
| E3b | TIT at λ≈1, fired rows | mean absolute error | descriptive | — |
| E4a | TIT, enriched hot rows | worst line's mean signed error | **{{R_E4a:.1f}} K** | level |
| E4b | the λ lever (TIT change with λ) | pooled fractional error | **{{R_E4b:g}} %** | d, part P2 |
| E5 | slope of TIT with MAP along rpm lines | pooled slope ratio − 1, two windows | descriptive; **the boost lever is untested** | — |
| D1 | the exhaust flow at the demanded torque | mean absolute relative error, fired rows | **{{R_D1:.1f}} %** | d, part P1 |
| L0 | the housing equivalent at the demanded torque | worst line, f bounded | **{{R_L0:.1f}} K** | level |
| L1 | the spread of that level across lines | largest minus smallest, f bounded | **{{R_L1:.1f}} K** | d, part P3 |
| E6 | every uncertain constant moved by its band | does each row move; the error worth R1 and worth b | labels | mistake 12 |
| E8 | the baseline ECU's λ and spark at the held-out Final rows | the change of the head-start pair they predict | **{{R_E8:g}} %** | d, part P4 |
| C1, C2 | road load; ratios, final drive, radius, mass | largest relative difference from the source | **1e-6** | identity |
| C3a, C3c | CX-9 on Argonne D3: fuel; air against the MAF, hot segments | mean signed error | descriptive | — |
| C3b, C3d | the same, fired segments | mean absolute error | **{{R_C3b:.1f}} %** each | d, part P5 |
| C4 | D3 figures already seen | as printed | descriptive | — |
| C5 | the scored climbs' distance from the kickdown threshold | \|demand/threshold − 1\| | **more than max({{R_E1a:.1f}} %, \|E1a\| + 2u_val)** | rule |
| S1a | the table's lever effects: λ −0.05, MAP −10 kPa, spark −0.75° | aggregate fractional error | **{{R_S1a:g}} %** each | table, P6 |
| S1b, S1c | table torque; table air and fuel | 95th percentile of the relative error | **{{R_S1b:.1f}} %**; **{{R_S1c:.1f}} %** (screens) | table, P6 |
| S1d | table EGT level, knock integral and flag | MAE, p95, agreement | descriptive | — |
| S2a | the hand-written preview pair per horizon, practice episodes, table against exact cycle | change of the pair difference | **{{R_S2a:.3f}} points** | table, P6 |
| S2b | pilot agents trained on the table, per horizon, scored on both | mean pair gap; median agent gap | **{{R_S2b:.3f}} points** | table, P6 |

**Level** rows feed each engine's 850 °C sensitivity row of decision 33. A uniform level error
cancels from every cut and from d under K3 (section 1.2), so a level row never drops an engine.
**d** rows guard the verdicts; each belongs to one of the six parts of the budget (section 1.3).
**Table** rows decide whether an engine trains on its table. Section 7 says what every label does.

## 1. From the MEI to an R

### 1.1 What the thresholds protect

The four-engine test reports one verdict per engine and per horizon on d, the sighted-minus-blinded
difference in points of cut, never pooled. The collapse is tested on those per-engine estimates as a
cross-plant comparison declared in advance (decision 26, `results/VALIDATION_DECISIONS.md:149`). It
judges d against the minimum effect of interest, {{MEI:.2f}} points of cut (decision 5, `:55`). A model
error matters as far as it moves d at the MEI, or moves the housing temperature that the 850 °C
sensitivity row rests on.

@wrap **The collapse test's equivalence margin is the MEI, {{MEI:.2f}} points** (decision 37, `results/VALIDATION_DECISIONS.md` section G, adopted 21 October). Two engines count as equivalent only when the difference of their d lies within ±MEI; how that is tested, with the difference's seed uncertainty and the two engines' model bands (section 7), is the preregistration's. The margin has a consequence behind it, the valuation of decision 5; a margin chosen for what the seed budget can confirm would be choosing R to fit E (the review of 20 October). With the six parts of section 1.3 at their limits and independent, a true d at the MEI reads {{IND_LO:.2f}}–{{IND_HI:.2f}} MEI, so the preregistration's seed reasoning (decision 30) states its false-negative risk at d_obs = {{IND_LO:.2f}} MEI, not at the MEI (finding 28). At about 20 seeds per arm the test can refute a collapse but will rarely confirm one within the MEI, and the preregistration says so.

The method is `results/VALIDATION_PLAN.md`'s: each required accuracy comes "from what an error
would change", written beside it, "because E is already known for most rows: the basis is the guard
against choosing an R to fit an E" (`results/VALIDATION_PLAN.md:110-112`). For these engines no E
exists yet, and every R below is derived without one.

### 1.2 Four ways an error reaches d, and one way it reaches a housing temperature

@wrap **Level.** Under decision 33 (K3, `results/VALIDATION_DECISIONS.md:156`) each engine's knee is set on its own calibrated plant, so that its baseline spends as long above the knee on its locked climb as the B58's baseline spends above 1123 K ({{K3_ABOVE_S}} s on the current B58 plant, `{{ECU_DIR}}/k3_nominal.json`). A housing error that is the same at every operating point raises the baseline's temperatures and the knee together. Every policy's turbine damage, exp((T + e − K − e)/45 K) (`engine_env.py:690-696`), is then unchanged, and the error cancels exactly from every cut and from d.

It does not cancel in the 850 °C sensitivity row of decision 33, which re-scores the records at a
fixed knee. The level rows (E1a, E2a, E3a, E4a, L0) are held to **R1, {{R1_K:g}} K of turbine-equivalent
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
  housing node (`thermal.py:265-275`). Its elasticity to the flow per housing runs from 1 when
  H ≪ τ (the head start ΔT_gas·ua_g·ṁ·H/c is proportional to the flow) down to 1 − f when H ≫ τ.
- The head start then decays over τ = c/(ua_g·ṁ/n + ua_a), which shortens as the flow rises
  (∂ln τ/∂ln ṁ = −f).
- The two effects oppose, so **|∂ln d/∂ln ṁ| ≤ 1** at every horizon. That includes decision 27's,
  which reach about the approach's time constant (about {{TAU_FLAT_ABOUT:.0f}} s on the B58's flat); section J of
  `results/preview_ceiling.txt:52-68` runs H/τ up to 3.85. A flow error scales a housing lowering, so
  the cut-range condition of (a) applies here too.
- Changing τ alone at fixed H moved the committed preview ceiling by an elasticity of about
  0.36–0.81: section J's rows at H = 30, 100 and 150 s, from τ 39 to 60 s
  (`results/preview_ceiling.txt:52-68`; version 1 gave 0.38–0.81).

@wrap **d, (c) the housing level's spread across operating points** (L1). A level error that differs by Δe between the knee-setting climb and a scored climb acts on the re-scored damage as a knee shift of −Δe there. The committed records give d's response to a knee shift directly (step 4 of the generator, `thresholds/knee_shift.py`, re-scoring the per-step records of `terrain_dt1`, the twenty of 29 September, before the grade ramp, and `extremes_dt1`, X1, on the ramped plant, by the published formula, which first gives back every committed damage to {{KNEE_WORST:.1e}}). The largest slope measured over shifts of ±5, ±10, ±25 and ±57 K, both sets, both damage readings, is **{{SLOPE:.4f}} points of d per K** (`{{SLOPE_SET}}`, knock term {{SLOPE_KNOCK}}, {{SLOPE_SHIFT}} K). At ±10 K the largest is {{SLOPE_10:.4f}}. Version 1 quoted 0.91 points per 10 K from one 57 K shift and called it the most (finding 37): it was the mean slope of that shift, and it is still the largest slope measured, so it is the one used. This mechanism is **additive**: it moves d by points, not by a fraction of d.

**d, (d) the baseline ECU's strategy** (E8). Every policy trims the same ECU, so version 1 called its
error common to both arms and "second order". It is first order, measured in section 1.5.

### 1.3 The budget: six parts, b = MEI/{{N_SHARES}} each

The model reaches d through six parts that err independently:

| part | what | d rows |
|---|---|---|
| P1 | the operating point and its flows at the demanded torque | D1 |
| P2 | the λ lever on the gas temperature | E4b |
| P3 | the housing level's spread across operating points | L1 |
| P4 | the baseline ECU's strategy at high load | E8 |
| P5 | the car | C3b, C3d (with the identities C1, C2 and the rule C5) |
| P6 | the table | S1a, S1b, S1c, S2a, S2b |

@wrap **Each part may move d, at d = MEI, by at most b = MEI/{{N_SHARES}} = {{B:.3f}} points** (decision 38, `results/VALIDATION_DECISIONS.md` section G, adopted 21 October). It is per part. Version 1 had five parts at MEI/5 each, and version 2 kept that valuation for six. Torque and flow were two of version 1's parts, and they counted the same flow twice (finding 17). D1 now measures their in-use combination as one part, and the ECU's strategy (P4) and the level's spread (P3) are new.

- With all six at their limits, aligned errors add to 6b = {{LINEAR:.2f}} points ({{LINEAR_MEI:.2f}} MEI), and independent
  ones to √6·b = {{RSS:.2f}} points ({{RSS_MEI:.2f}} MEI).
@wrap - Decision 38 holds the aligned total at the MEI. With version 2's b = MEI/{{N_SHARES_V2}}, six aligned parts added to {{LINEAR_MEI_V2:.2f}} MEI, enough to manufacture an effect of the size the test looks for. Every d-row R is therefore 5/6 of version 2's before it is rounded down: D1, E4b, E8, C3b, C3d, S1a and S1c {{R2_D1:.1f}} → {{R_D1:.1f}} %, L1 {{R2_L1:.1f}} → {{R_L1:.1f}} K, S1b {{R2_S1b:.1f}} → {{R_S1b:.1f}} % and S2 {{R2_S2a:.3f}} → {{R_S2a:.3f}} points (`budget.version_2_at_mei_over_5` in the JSON; section 12).
- **Most rows scale a true difference** (D1, E4b, E8, C3b, C3d and the S1 rows). They cannot make a
  difference out of a null, and they can shrink or inflate a real one. With all six parts at their
  limits, a true d at the MEI reads anywhere from {{IND_LO:.2f}} to {{IND_HI:.2f}} MEI if the errors are independent,
  and from {{ALN_LO:.2f}} to {{ALN_HI:.2f}} MEI if they align.
- **Two rows are additive** (L1, and S2 in part P6): they can make a difference out of a null, up to
  b each, i.e. √2·b = {{RSS2:.2f}} points independent or 2b = {{LIN2:.2f}} aligned. Version 1's sentence "the model
  alone cannot carry a null difference up to the MEI" is withdrawn; it bounded the wrong risk
  (findings 17, 28).
- These bounds cover the six gated parts. They do not cover what no row gates: the knock model, the
  boost lever, λ at part load, the housing constants, the ECU's enrichment timing (section 8).

The fraction is a valuation, like the MEI itself: decision 38's, set before any fit, and every d-row
R is proportional to it.

With the bounds of section 1.2:

- **a lever:** ε ≤ b/MEI = {{BFRAC_PCT:.2f}} %, so **{{R_E4b:.1f}} %**;
- **the flow at the demanded torque:** |Δln ṁ| ≤ **{{R_D1:g}} %**;
- **the level's spread:** Δe ≤ b/{{SLOPE:.4f}} = {{B:.3f}}/{{SLOPE:.5f}} = {{L1_RAW:t2}} K, which gives **{{R_L1:.1f}} K**;
- **the ECU's strategy:** at most **{{R_E8:g}} %** of the head-start pair (section 1.5).

Requirements are rounded down, never up.

### 1.4 The propagation model is the B58, with its ECU in the loop: an assumption

Each engine's own sensitivities exist only once it is calibrated, and using them would let the
calibration choose its own requirements. **So every coefficient below is the B58's**, computed for
this contract on the B58 plant alone. Each engine's own coefficients are reported beside its
results, as descriptive values, and never move an R.

The run follows `validation_numbers.py` section 3 exactly (`validation_numbers.py:103-132`): the
locked climb, the neutral action, frozen episode 1, dt 1 s. It reproduces the committed figures: the
baseline's damage is {{DMG0:.2f}} (848.1 in `results/DRIVE_C_RULE_NUMBERS.txt:42`), the peak housing
temperature {{PEAK0:.2f}} °C (`:42`), τ on the climb {{TAU_CLIMB:.1f}} s (`results/preview_ceiling.txt:27`), and the
housing node sits {{ONE_MINUS_F:.3f}} of the way from the gas to the ambient (`results/DAMAGE_CONSTANTS.md:35`).

**Version 1 held spark fixed while the load loop moved MAP (finding 1).** In the environment the
baseline ECU schedules spark on the baseline's MAP (`engine_env.py:982`), and every policy takes that
spark plus its trim (`:1004`). At the climb the schedule is the knock-limited surface
(`engine_env.py:169-193`), whose slope there is {{SPARK_SLOPE:.3f}}° per kPa. A torque bias moves MAP, so it moves
the spark too. Version 2 measures the response three ways and uses the third, which closes every
loop:

| a +1 % torque bias | MAP | spark | gas | exhaust flow | housing (B58 f) |
|---|---|---|---|---|---|
| at fixed spark (version 1) | {{FX_DMAP:.3f}} kPa | 0 | {{FX_DEGT:.3f}} K | {{FX_FLOW:.3f}} % | {{FX_DTH:.3f}} K |
| along the ECU's schedule, ∂/∂MAP at the cell | {{SC_DMAP:.3f}} kPa | {{SC_DSPARK:+.2f}}° | {{SC_DEGT:.3f}} K | {{SC_FLOW:.3f}} % | {{SC_DTH:.3f}} K |
| **in the environment**, the cycle's torque × 1.01 for baseline and agent, medians over t 400–718 s | **{{UP_DMAP:.3f}} kPa** | **{{UP_DSPARK:+.3f}}°** | **{{UP_DEGT:.3f}} K** | **{{UP_FLOW:.3f}} %** | **{{UP_DTH:.3f}} K** |
| the same, × 0.99 | {{DN_DMAP:+.3f}} kPa | {{DN_DSPARK:+.3f}}° | {{DN_DEGT:+.3f}} K | {{DN_FLOW:+.3f}} % | {{DN_DTH:+.3f}} K |

The larger magnitudes are used: **{{GAS_PER_PCT:.3f}} K of gas and {{FLOW_PER_PCT:.3f}} % of flow per 1 % of torque.** That is
{{RATIO_HOUSE:.1f}} times version 1's housing response and {{RATIO_FLOW:.1f}} times its flow response.

| quantity | value | from |
|---|---|---|
| the climb cell (median over t 400–718 s) | {{CL_RPM:.0f}} rpm, {{CL_MAP:.1f}} kPa, charge {{CL_IAT:.1f}} K, spark {{CL_SPARK:.2f}}°, λ {{CL_LAM:.2f}}, gas {{CL_EGT:.2f}} °C, exhaust flow {{CL_MDOT:.2f}} g/s, {{CL_TQ:.1f}} Nm | the run |
| f = ua_g·ṁ/(ua_g·ṁ + ua_a) | {{F_CLIMB:.3f}} | {{UA_G:.2f}} × {{CL_MDOT:.2f}} = {{UA_GT:.2f}} W/K against {{UA_A:g}} W/K (`engine_specs/b58.toml:124-125`) |
| G = T_gas − T_amb | **{{G_K:.2f}} K** | {{CL_EGT:.2f}} °C against the scored roads' {{T_AMB_C:g}} °C |
| the flat approach ({{FL_RPM:.0f}} rpm, {{FL_MAP:.1f}} kPa) | f {{F_FLAT:.3f}}, τ {{TAU_FLAT:.1f}} s; flow {{FL_FLOW:.3f}} % per +1 % torque along the schedule | the run |
| λ −0.01, −0.02, −0.05, −0.10, −0.15 at the climb cell | gas {{LAM_EGT_LIST}} K | the run (the agents' λ trim reaches −0.15, `engine_env.py:698`) |
| spark ∓0.75° | gas ±{{SPK_EGT:.2f}} K, torque ∓{{SPK_TQ:.2f}} % | the run |

**The housing equivalent is bounded, not taken from the B58's f (finding 16).** At steady state the
housing T_h = f·T_gas + (1 − f)·T_amb moves by f·ΔT_gas + f(1 − f)·G·Δln ṁ. f depends on the housing
constants and on the flow per housing, so the B58's 0.858 does not transfer (review of 20 October,
`review_0` issue 9). Version 1 bounded f for gas errors but used 0.858 for flows. Every housing
equivalent in this file is now the largest over 0 ≤ f ≤ 1:

- a gas error e alone: |e|;
- a flow error δ alone: G·|δ|/4, i.e. **{{HOUSE_FLOW:.3f}} K per 1 %** (f = 1/2);
- a torque bias, which moves both the same way: max_f [{{GAS_PER_PCT:.3f}}·f + {{BQ:.2f}}·f(1 − f)] = ({{GAS_PER_PCT:.3f}} + {{BQ:.2f}})²/(4 × {{BQ:.2f}})
  = **{{HOUSE_BOUND:.3f}} K per 1 %**, at f = {{F_STAR:.3f}}. With the B58's own f it would be {{HOUSE_B58:.3f}} K.

G is the B58's. It is larger than any EPA engine's thermocouple TIT over 42 °C even with the
mass-averaging offset added (the hottest, 900.8 °C, plus 100 K gives 958.8 K), so it errs tight.

### 1.5 The ECU's strategy, measured on the B58 (new in version 2)

Version 1 made E8 descriptive because the strategy's error "is common to both arms and enters d only
at second order". No run supported that (finding 10; mistake 24). This measures it.

@wrap Step 5 of the generator, `thresholds/ecu_shift.py`, shifts the B58 baseline ECU's output by Δλ or Δspark whenever its load input exceeds {{ECU_LOAD_KPA:.0f}} kPa (the ECU's step, `engine_env.py:356-376`, called at `:982`). Every policy inherits the shift (`:1004-1006`), as it would inherit an error of a fitted ECU. Under K3 the knee is re-set so that the shifted baseline spends {{K3_ABOVE_S}} s above it, as the unshifted one does above 1123 K. The run is the locked climb, frozen episode 1, dt 1 s, with the four hand-written policies of `check_premise.py`.

d itself needs agents, so the proxy is **the head-start pair**: current-grade minus reactive,
{{PAIR0:.2f}} points nominal. The two policies differ only in when they protect. The preview pair
(predictive minus current-grade) reads {{PREV_PAIR0:.2f}} point on this road, which is why decision 34 replaced it
(`results/VALIDATION_DECISIONS.md:157`), so it cannot serve.

| ECU shift above 100 kPa | K3 knee | baseline λ, spark (median t 400–718 s) | head-start pair, points | change under K3 | at the fixed 1123 K knee |
|---|---|---|---|---|---|
{{ECU_TABLE}}

The thermal-only reading agrees with the total within {{THERMAL_AGREE:c2}} percentage points at every shift, so the
knock damage term barely enters the pair. Reading:

- **The strategy enters d at first order.** Every λ shift from the nominal 1.00 shrinks the pair. The
  cycle's EGT has a corner at λ = 1, and a leaner baseline knock-retards: its spark falls from {{SPK_NOM:.2f}}°
  to {{SPK_LAMP002:.2f}}° at +0.02. The lean side therefore runs through the knock model, which is untested.
- K3 absorbs most of what a fixed knee shows: at a fixed knee, spark −0.75° halves the pair, and
  under K3 it moves it by {{K3_SPK_M075_ABS:.0f}} %.
@wrap - **The error worth b (b/MEI, {{BFRAC_PCT:.1f}} % of the pair) alone:** λ {{W_LEAN:+.4f}} lean or {{W_RICH:+.4f}} rich, by interpolation. {{SPARK_WORTH}}
- **E8 is expected to read untested on every engine.** EPA's λ is "Reference Only - Uncalibrated"
  (`data/engines/<id>/epa_channels.csv`). Referencing each cell removes its closed-loop offset, but
  the Ford's two cells disagree by {{FORD_CELL_GAP:.2f}} at closed loop (section 3). Taken as a uniform half-width,
  u = {{U_LAM:.3f}}, and through the lean side's {{LEAN_001:.1f}} % per 0.01 that alone is u = {{U_E8:.1f}} % on E8. Then
  2u = {{U2_E8:.1f}} % > R. Section 7 carries E8's band into every engine's d.
- **The B58 is not exempt.** Its own spark-under-boost row reads car minus model −3.81° (median of
  31 readings; −1.78° in the climb's own cell, 4 readings; untested,
  `results/VALIDATION_PLAN.md:292`). Through this response that is worth {{B58_SPK_LO:+.1f}} % to {{B58_SPK_HI:+.1f}} % of the
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
     between cells, not interpolation in rpm: VE depends on rpm alone (`plant.py:160`).
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
{{OFFSETS_TABLE}}

| engine | table | rows | held out | calibration |
|---|---|---|---|---|
{{TABLES_TABLE}}

That is {{HO_mazda}} held-out rows of {{NROWS_mazda}} on the Mazda, {{HO_honda}} of {{NROWS_honda}} on the Honda and {{HO_ford}} of {{NROWS_ford}} on the Ford,
counting the two windows of a hold as two rows. A High Load Initial row is held out with its hold but
enters only E1i (section 3). The JSON lists each row by table and spreadsheet row
(`engines.<id>.held_out_rows`).

The held-out lines, row by row (steady rows; holds; fired steady and Final rows, of which with a
fuel meter; hot; hot λ≈1, all with a meter; hot enriched; boosted λ≈1; throttled λ≈1):

| engine | line | steady | holds | fired (meter) | hot | hot λ≈1 | hot enriched | λ≈1 ≥ 100 kPa | λ≈1 < 100 kPa |
|---|---|---|---|---|---|---|---|---|---|
{{LINES_TABLE}}

What decides, at 3 clusters a line:

| engine | E1a | E2a | E3a, L0 | E4a | E4b (enriched rows) | D1 rows | E8 Final rows |
|---|---|---|---|---|---|---|---|
{{DECIDING_TABLE}}

Known now, from structure:

- The Mazda's E4a rests on one line ({{MAZDA_E4A_LINE}} rpm, {{MAZDA_E4A_ROWS}} rows).
@wrap - The Ford's L0 and L1 rest on its steady hot rows at {{FORD_L0_RANGE}} rpm. Its high-load lines carry {{FORD_HL_HOT_L1}} hot λ≈1 rows.
- E4b's λ = 1 reference is extrapolated in MAP, by the distance between a line's highest boosted
  λ≈1 row and its enriched rows:
  - Mazda: {{E4B_EXTRAP_mazda}} kPa;
  - Honda: {{E4B_EXTRAP_honda}} kPa;
  - Ford: {{E4B_EXTRAP_ford}} kPa.
- The Honda now validates {{HL_HELD_honda}} of its {{HL_ALL_honda}} high-load lines and the Ford {{HL_HELD_ford}} of {{HL_ALL_ford}} (finding 34). The Ford's
  3500 rpm line, beside the F-150's climb point (3470 rpm, UNVERIFIED), is held out.

### 2.3 What the calibration may use, and what only the validation sees

**The calibration may use:**

- every row of a non-held-out line, with EPA's calculated columns (BMEP, BSFC, BTE, the injector
  estimate, cam phases, the Atkinson ratio, the effective strokes). High Load Initial rows only for
  the full-throttle torque curve, labelled a transient peak; never their TIT, λ or (absent) fuel;
- ALPHA's full-throttle and closed-throttle curves (`epa_engine.json`), only at nodes whose
  `measured_at_speed` source row is a calibration row. {{ALPHA_COUNT_WORD}} nodes sit on held-out rows and are removed
  (`engines.<id>.alpha_nodes_removed`):
{{ALPHA_BULLETS}}

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
    `plant.py:63-66`), FMEP, the burn and delay constants (base and rpm terms), UA_PORT, the
    back-pressure law (to `Turbine Inlet Press` where published), and the knock scale (E6 row 7).
  - Shared and not fitted: `combustion_efficiency(λ)` (`plant.py:54-60`), γ(T), the
    residual-fraction law, t_head, the port pickup, t_residual, cp_exh and the Wiebe shape.
  - Fixed valve events (`plant.py:193`): no cam input.
  - The ECU: spark the lesser of a part-load map and the knock-limited surface, λ an enrichment
    schedule, both fitted to calibration rows.
- **The alternatives, in this order, each adding to the one before:**
  - B: VE in rpm and MAP (a linear MAP term);
  - C: a per-engine rich-side slope of `combustion_efficiency`, fitted on enriched hot calibration
    rows (the Honda reaches λ 0.61, beyond any B58 data);
  - D: the intake cam phase as an input to VE, through a schedule cam(rpm, MAP) fitted to EPA's
    `Intake Cam Phase` on calibration rows and run by the ECU. EPA's engines move their intake cams
    by 55–74° across the map (Mazda −74.3 to −0.3 CAD, `data/engines/mazda_25t/epa_channels.csv:24`;
    Honda −0.5 to 61.4, `honda_l15b7/epa_channels.csv:26`; Ford Cell 9 −2.1 to 53.4,
    `ford_27tt/epa_channels.csv:22`).
- **The in-sample stage.** Every gating statistic of section 4 is computed on the calibration lines,
  with the same definitions, populations and line minima. These are fit residuals and are never
  labelled. The form is the first of A, A+B, A+B+C, A+B+C+D at which every one of them satisfies
  |E_cal| ≤ R. If none does, the form is A+B+C+D, and the failing in-sample statistics are reported.
  The form and its constants are then frozen, their sha256 recorded, and **the held-out statistics
  are computed once**.

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
  because that is what the environment runs (`engine_env.py:761`).
- **λ.**
  - **λ_ref** is the median published λ of a steady table's rows at 2–8 bar BMEP: that cell's
    closed-loop reading of an uncalibrated sensor. It is Mazda {{LREF_mazda:.3f}} ({{LREF_N_mazda}} rows), Honda {{LREF_honda:.3f}} ({{LREF_N_honda}}),
    Ford Cell 9 {{LREF_cell9:.3f}} ({{LREF_N_cell9}}) and Ford HD1 {{LREF_hd1:.3f}} ({{LREF_N_hd1}}, the mean of its two banks). A high-load hold
    takes its cell's λ_ref.
  - **A row within 0.02 of λ_ref runs at λ = 1.00.** EPA's steady points "lie below the load where
    enrichment starts" (`CATALOGUE.md:150`), so the ECU is in closed loop there. E6 row 12 runs every
    row without this snap. The snap reaches {{SNAP_mazda}} of the Mazda's {{HL1_mazda}} hot λ≈1 held-out rows, {{SNAP_honda}} of the
    Honda's {{HL1_honda}} and {{SNAP_ford}} of the Ford's {{HL1_ford}} (more than 0.005 from λ_ref).
  - **Every other row runs at λ_meas − (λ_ref − 1).**
  - The 0.02 is how far one engine's two cells disagree: the Ford reads {{LREF_cell9:.3f}} in Cell 9 and {{LREF_hd1:.3f}}
    in HD1.
- **Fuel (finding 35).** Each table's own fuel sets LHV and AFR_st, from its fuel report's analysis
  (`epa_engine.json`, `alpha_fuel`, of that FTAG). AFR_st comes from the carbon weight fraction, with
  hydrogen the balance and the Tier 2 fuel taken as oxygen-free.
  - Mazda {{FUEL_mazda}}.
  - Honda {{FUEL_honda}}.
  - Ford Cell 9 {{FUEL_ford}}.
  - **Ford HD1, steady and high load, on FTAG {{FORD_HD1_FTAG}}, the Mazda's batch** (the tables' `fuel_report`;
    `CATALOGUE.md:167`). Version 1 gave all the Ford's rows Cell 9's batch.
  - The plant and `thermal.py:245` must take these per engine. The B58 keeps its 44.0 MJ/kg and
    14.7, so its certificate holds. E6 rows 2–3 move to 14.7 and 44.0.
- **The calibration's air** is the fuel meter × AFR_st × that λ, on steady and Final rows only:
  High Load Initial carries no meter column for any engine.
- **Populations.**
  - *Fired:* BMEP ≥ 2 bar.
  - *Hot:* High Load **Final** rows, and the steady rows at or above the engine's lowest high-load
    manifold pressure (Mazda {{FLOOR_mazda:.1f}}, Honda {{FLOOR_honda:.1f}}, Ford {{FLOOR_ford:.1f}} kPa). This is EPA's own high-load
    region, the one its stab tests chose to show the engine's protection (`CATALOGUE.md:151`). The
    test roads (decision 34) are not drawn yet, and their operating point would come from the
    calibrated plant.
  - **High Load Initial rows enter no gating statistic (finding 21).** The Initial window is the
    peak torque within 2 s of reaching the target after a 1-s ramp from about 1/3 load
    (`logs/epa/README.md:101-104`): a thermal and sensor transient, set against a model whose port
    loss uses a wall temperature fixed by coolant (`plant.py:165`, `:286-287`). The richer Final
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
    {{FIRED_IAT_MAX_mazda:.1f}} °C (Mazda), {{FIRED_IAT_MAX_honda:.1f}} °C (Honda; its hot rows only {{HOT_IAT_MAX_honda:.1f}} °C) and {{FIRED_IAT_MAX_ford:.1f}} °C (Ford). The B58's climb
    charge is {{CL_IAT_C:.1f}} °C, and the rig held the Mazda's and the Honda's charge air at 30–40 °C
    (`CATALOGUE.md:153`). Version 1's Honda maximum, 65.5 °C, came from an unfired row (finding 31).
  - **Any hold longer than EPA's 30 s** (`CATALOGUE.md:151`) is an extrapolation in duration.
    Decision 34's climbs of 1–2 τ are 40–120 s.
  - **Above 115 km/h** the road load is not covered (C1).
  - Coverage is computed per population (fired, hot) and per 20 kPa band of manifold pressure, on
    all rows and on the calibration rows (`engines.<id>.coverage`), not as a product of independent
    ranges.

## 4. The engine rows

Every row except E6 is computed on held-out rows only, and every d row carries the condition that
both arms' cuts lie in 0–0.865 (section 1.2a).

**E1, brake torque at EPA's inputs.**

- **E1a: R = {{R_E1a:.1f}} %** (level). It is the worst deciding line's mean signed relative error over its
  hot rows. A +x % torque bias moves, in use, the gas by {{GAS_PER_PCT:.3f}}·x K and the flow by {{FLOW_PER_PCT:.3f}}·x %
  (section 1.4). The housing equivalent is at most {{HOUSE_BOUND:.3f}}·x K, and {{R1_K:g}} K / {{HOUSE_BOUND:.3f}} = {{E1A_RAW:.3f}} %, rounded
  down. Version 1 had 5.1 %, from a fixed spark and the B58's f.
@wrap - **E1b: descriptive**, the mean absolute relative error over every fired held-out row. Its d consequence is gated jointly with the flow's by D1. Alone it is worth b at {{BFRAC_PCT:s2}}/{{FLOW_PER_PCT:.3f}} = {{E1B_RAW:.2f}} %, i.e. {{WB_E1b:.1f}} %.
- **E1i: descriptive**, the High Load Initial rows' torque per line, labelled a transient.
- *Tests:* the burn, friction and pumping work as calibrated, interpolated across rpm lines, at
  EPA's own spark and λ.
- *Does not test:* the knock model (spark is an input, and no knock is measured), the ECU's strategy
  (E8) or the charge-temperature model.

**E2, fuel flow against EPA's Coriolis meter** (`Fuel Meter Flow`), on steady and Final rows.

- **E2a: R = {{R_E2a:.1f}} %** (level). It is the worst line's mean signed relative error over its hot rows
  with a meter reading. A flow error alone moves the housing by at most G/4 per unit ln(flow),
  {{HOUSE_FLOW:.3f}} K per 1 %, and {{R1_K:g}}/{{HOUSE_FLOW:.3f}} = {{E2A_RAW:.2f}} %, rounded down. Version 1 had 8.3 %, from the B58's
  f(1 − f) = {{F1MF:.3f}}.
- **E2b: descriptive**, the mean absolute relative error over every fired held-out row with a meter
  reading. D1 is the d row; E2b is worth b at {{WB_E2b:g}} %.
- *What it can and cannot see (mistake 12).*
  - The model's fuel is its air divided by AFR_st·λ (`plant.py:163`), and the calibration's air is
    EPA's fuel × AFR_st × λ, so AFR_st and λ cancel.
  - On held-out lines, E2 tests how the volumetric efficiency and the residual fraction interpolate
    across rpm, and nothing else. It cannot see the air path's absolute level.
  - E6 rows 1–2 move AFR_st and the λ convention and show this. The only independent air reading for
    any EPA engine is the D3 CX-9's MAF (C3d).

**E3, turbine-inlet gas temperature at λ≈1.**

- **E3a: R = {{R_E3a:.1f}} K** (level). It is the worst line's mean signed error over its hot λ≈1 rows: R1
  carried to the gas with f ≤ 1, since a gas error e moves the steady housing by f·e ≤ e.
- **E3b: descriptive**, the mean absolute error over every fired held-out λ≈1 row.
- *Like with like (mistake 23).* The model's gas temperature after the port loss
  (`plant.py:281-287`) is compared with EPA's `Turbine Inlet Temp`, a gas-side thermocouple at the
  turbine inlet, not the housing metal (`logs/epa/README.md:106-108`).
- *Tests:* how the calibrated exhaust relation (UA_PORT, the burn, the back-pressure law)
  interpolates across rpm lines.
- *Does not test:*
  1. **the housing.** No source measures it, for any engine (`CATALOGUE.md:686-689`). τ is assumed,
     and R3 is withdrawn.
  2. **the gas that heats the housing.** "Thermocouple readings sit roughly 100 K below
     mass-averaged port temperature … or about 20 K below the time-averaged value"
     (`REFERENCES.md:311`; Caton, `:664-667`). UA_PORT is fitted to the thermocouple, so for an
     EPA engine the model's "gas" is the thermocouple's reading. The B58's model gas is not: its
     UA_PORT is a typed 15 W/K anchored to no exhaust measurement (`plant.py:278-281`;
     `REFERENCES.md:432`), and its climb gas is 1022 °C, against EPA TITs of 723–816 °C at
     2500–3000 rpm and 13–16 bar (`fe_out/design.md:180`). One set of housing constants is applied
     to two definitions of the gas (finding 36). So: **absolute housing statements for the EPA
     engines are not covered** (section 1.2), and **the 850 °C row is reported per engine and
     labelled not comparable across engines**. The K3 knees are per engine and unaffected.
  3. **the form of the port heat transfer.** UA_PORT is fitted to the same channel, so a held-out
     residual tests interpolation, not the form (mistakes 12, 20).
  4. **on the Ford, a twin-turbo engine read through one TIT channel**, from a bank not stated,
     UNVERIFIED (`logs/epa/README.md:108-111`). Version 1 cited `review_0` issue 10 here; that issue
     is about mistake 12.
  5. **any transient.** EPA published window averages only (`CATALOGUE.md:151`, `:690`).

**E4, the enriched holds.**

@wrap - **E4a: R = {{R_E4a:.1f}} K** (level), the worst line's mean signed error over its enriched hot rows (as E3a). The deciding lines are {{E4A_LINES}}.
- **E4b: R = {{R_E4b:g}} %** (d, part P2), the λ lever's pooled fractional error.
  - Let L_S = S(the row's inputs at λ = 1) − S(the row's inputs): the cooling the model gives that
    row by enriching.
  - The model's error at λ = 1 at an enriched row is estimated as ê, from the line's least-squares
    line of the λ≈1 error against MAP over its boosted λ≈1 rows (steady and Final, MAP ≥ 100 kPa,
    at least 3), **evaluated at the enriched row's own MAP** (finding 9). Version 1 used the line's
    mean λ≈1 error, from rows 33–78 kPa lower on the Mazda's version-1 lines (the review's structure
    check, reproduced). A slope error at E5's version-1 limit, 20 % of the {{SC_EGT_PER_KPA:.3f}} K per kPa the B58
    shows along its schedule, then misplaced the reference by {{E5V1_SLOPE_ERR:.3f}} × (33 to 78) = {{MISPLACE_LO:.1f}}–{{MISPLACE_HI:.1f}} K. The
    lever it measures is {{LAM010:.0f}}–{{LAM015:.0f}} K at λ −0.10 to −0.15 on the B58 (section 1.4), and those enriched
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
  slope along the ECU's schedule is {{SC_EGT_PER_KPA:.3f}} K per kPa against {{FX_EGT_PER_KPA:.3f}} at fixed spark: {{SPARK_SHARE:.0f}} % of it is a
  spark term. The agents' boost lever acts at fixed spark, since their spark follows the baseline's
  MAP, not their own (`engine_env.py:982`, `:1004`). So E5 cannot isolate the lever its R was
  derived for. EPA has no spark sweeps (`fe_out/design.md:59`), so **the boost lever is untested for
  every engine** and is declared so (section 8).

**D1, L0 and L1: the engine at the demanded torque (finding 30).** E1–E4 run at EPA's MAP, but the
environment runs at the demanded torque (`engine_env.py:784`). A breathing error moves fuel and
torque together and partly cancels there. So, per fired held-out row with a meter reading:

- invert MAP so that the model delivers EPA's measured torque, by bisection over 20–400 kPa, at
  EPA's speed, intake temperature and coolant and the row's λ convention;
- run spark at EPA's spark + s·(MAP − MAP_EPA), where s is the engine's calibrated ECU's ∂spark/∂MAP
  at the row (central difference of `base_spark`, ±2 kPa), as the environment's ECU responds (the
  coupling of finding 1);
- there take δ_D = fuel_model/fuel_meter − 1 and e_D = TIT_model − TIT_EPA. The exhaust flow's
  relative error is δ_D, since the model and EPA share AFR_st and the λ convention.

A row whose torque the model cannot reach is listed and counted at the bound. Then:

- **D1: R = {{R_D1:.1f}} %** (d, part P1), the mean |δ_D| over the fired held-out rows, pooled: Mazda {{D1_mazda}},
  Honda {{D1_honda}}, Ford {{D1_ford}}. The basis is the flow mechanism of section 1.2b, |Δln ṁ| ≤ b/MEI. D1 is torque
  and flow as one part (finding 17), at part load as well as at the climb. D1 also bounds τ's
  flow-dependent part: at the B58's f, {{F_CLIMB:.3f}} × {{R_D1:g}} % = {{TAU_FLOW_PART:.0f}} % of τ. τ's capacity and heat-transfer part
  is assumed (E6 row 4). COU-2 has no R (R3 withdrawn), so no row gates an engine's place on the H/τ
  axis. A level failure on E2a, or C3c's reading (descriptive), leaves the absolute flow unprotected
  beyond D1's {{R_D1:g}} %.
- **L0: R = {{R_L0:.1f}} K** (level), version 1's E7a computed directly. For each deciding line, take ē and
  δ̄, the means of e_D and δ_D over its hot λ≈1 rows with a meter: the rows common to fuel and TIT,
  and the population of E3a (finding 16). L0 = max over 0 ≤ f ≤ 1 of |f·ē + f(1 − f)·G·δ̄|, G =
  {{G_K:.2f}} K, on the worst line. It is R1 applied to the sum the separate rows cannot see.
- **L1: R = {{R_L1:.1f}} K** (d, part P3, additive), the level's spread. With H_l(f) = f·ē_l +
  f(1 − f)·G·δ̄_l, L1 = max over f of [max over deciding lines of H_l(f) − min of H_l(f)]. Its
  u_stat is that of the two extreme lines. It needs at least 2 deciding lines: Mazda {{L0LINES_mazda}}, Honda {{L0LINES_honda}},
  Ford {{L0LINES_ford}}. R = b/{{SLOPE:.4f}} points per K (section 1.2c).
  - **A tightening only.** On decision 34's roads, before any held-out statistic, the hand-written
    preview pair's slope against a knee shift is measured. If it is larger than {{SLOPE:.4f}}, R becomes
    b/that slope.

**E6, perturbation rows (mistake 12).** Each uncertain constant is moved by its band and every row is
recomputed.

- **The visibility probe is sized by its consequence (finding 3), not by the fit's own standard
  error.** It is the change of the constant that moves the engine's own in-use housing equivalent at
  its locked-climb cell by R1 (for level rows), or d by b (for d rows). Where neither is computable,
  it is ±10 %.
  - A row whose statistic moves by less than its own u_val under the probe is **excluded for that
    constant**: its pass certifies nothing about the constant.
  - That does not change the row's own label. A row excluded for every constant it claims to test
    (its *Tests* list) has no statistic and counts as such in section 7.
  - Version 1's ±(fit uncertainty) would have called a well-fitted UA_PORT invisible because it fits
    well.
- **Load-bearing.** A constant whose band moves d by more than b, or the housing equivalent by more
  than R1, becomes a preregistered sensitivity row.
- E6 never drops an engine.

A row marked "refit" re-runs the calibration with the constant moved, because the constant enters how
the calibration reads EPA's data. For those rows the question is not whether a held-out statistic
moves, since the refit may absorb the change, but how far the model in use moves.

| # | constant | band (source) | refit | what it must show |
|---|---|---|---|---|
| 1 | the λ convention | as published instead of cell-referenced, i.e. the offset λ_ref − 1: {{LAM_OFFSETS}} | yes | every row's change; the in-use hot TIT at λ = 1, the air and τ |
| 2 | AFR_st, moved in the calibration's air and the plant's fuel together | the table's fuel, {{AFR_MIN:.3f}}–{{AFR_MAX:.3f}} (the convention) → 14.7 (`plant.py:43`) | yes | the air {{E6_AIR:+.2f}} %, the exhaust flow {{E6_EXH:+.2f}} %, τ {{E6_TAU:.2f}} % (B58 f), the housing level {{E6_HB58:+.2f}} K (B58 f), at most {{E6_HBOUND:+.2f}} K (f bounded). **E2, D1 and L0 must not move**: none of them can see AFR_st |
| 3 | LHV, in `plant.py:42` **and** `thermal.py:245` together | the table's fuel, {{LHV_MIN:.3f}}–{{LHV_MAX:.3f}} MJ/kg (the convention) → 44.0 | yes | every row's change; the in-use heat release per gram of fuel; the coolant and oil heat. Version 1 moved `plant.LHV` only, and the thermal network's 44.0e6 would not have followed (finding 19; mistake 25) |
| 4 | c_turb, ua_gas_turb, ua_turb_amb | × 0.75 and × 1.333 each. **Proposed by this contract**: X1 drew only the heat capacity on that range (`results/PREREGISTRATION_X1.md:119`) | no | τ moves by construction. No E row can see them, so every row is excluded for them by construction. Report τ, the 850 °C baseline peak and decision 34's ceiling at each end, flagged if the ceiling falls below 2 MEI |
| 5 | the back-pressure law | ± its fit's standard uncertainty (reported); the visibility probe as above | no | E1a, E3a and L0 must move under the probe |
| 6 | UA_PORT | ± its fit's standard uncertainty (reported); the visibility probe as above | no | E3a, E3b, E4a and L0 must move under the probe |
| 7 | the knock scale, assumed KI = 1 at the High Load Final spark | KI 0.90 and 1.10 (decision 21's ±0.10 KI) | yes | no E row can see it, since EPA publishes no knock data. Report the knock term's share of the baseline's damage, and d both ways |
| 8 | the crank-angle step | 0.25° → 0.125° | no | gives u_num |
| 9 | the other ASSUMED cycle constants (conrod, IVC, EVO, t_head, port pickup, t_residual, cp_exh, any burn constant not fitted) | the bracket EPA's calculated valve channels give, where one exists (the Honda's effective strokes, the Mazda's Atkinson ratio, the cam phases); else the probe as above (±10 crank degrees for IVC and EVO where no consequence is computable) | no | the rows the calibration says each one sets must move. Report the error worth R1 and worth b |
| 10 | the driveline efficiency η, 0.92 | 0.86–0.98, the CX-9's apparent efficiency on D3 (seen); the Accord's 0.78 is UNVERIFIED | no | C3 moves. An η error is a torque bias of the same fraction: worth R1 at {{R_E1a:.1f}} %, worth b at {{R_S1b:.1f}} % |
| 11 | the charge temperature (E rows are fed EPA's measured value) | ±6.3 K, the B58's input uncertainty (`results/DRIVE_C_RULE_NUMBERS.txt:56`) | no | report the hot TIT and the test roads' hand-written cuts |
| 12 | the λ snap | every row at λ_meas − (λ_ref − 1), no snap (finding 11) | no | E3a, E5, D1 and L0 computed both ways; each gating row labelled by the worse |
| 13 | the enrichment timing within a hold, which EPA does not publish | the ECU's dwell gate at 0 s and at 30 s, EPA's hold length (`CATALOGUE.md:151`) | no | **a preregistered sensitivity row of d for every engine** (finding 29) |

A ±10 % probe is a probe, not an uncertainty. Where a constant has no band, the row reports how large
an error would be worth R1 or b, as the plan's own table does (`results/VALIDATION_PLAN.md:125-131`),
and a reader sets that against whatever evidence exists.

**E8, the baseline ECU's strategy at high load: R = {{R_E8:g}} %** (d, part P4; findings 10, 29).

- **The statistic.** dl is the mean signed difference between the model ECU's λ and EPA's λ, both
  cell-referenced, and ds the same for spark, over the held-out High Load Final rows (Mazda {{E8ROWS_mazda}}, Honda
  {{E8ROWS_honda}}, Ford {{E8ROWS_ford}}). The ECU is evaluated at the row's speed and MAP, with a 30 s dwell, no knock retard
  and EPA's intake temperature.
- **E8 = |P_λ(dl)| + |P_spark(ds)|**, where P is the measured relative change of the head-start pair
  under K3 for an ECU shift of that size: piecewise linear through section 1.5's table (both damage
  readings, the larger). Its u_val propagates u(dl) and u(ds) through P's local slopes.
- **A tightening only.** The same shifts are re-run on the B58 on decision 34's roads before any
  held-out statistic, and at each shift the larger response is used.
- dl and ds are also reported alone, with the error worth b (section 1.5), and so is where each
  engine's model ECU starts to enrich against EPA's Final rows: the lowest MAP per line at which λ
  falls 0.05 below λ_ref.
- Section 1.5 expects E8 to read untested on every engine.
- It is reported, too, because a guessed baseline flatters every cut (mistake 3). The Ford's
  protection modes "are not controllable in the test cell" (`CATALOGUE.md:162`). Its baseline is
  therefore ASSUMED, and a sensitivity row over its TIT cap is preregistered (`review_0` issue 17).
- **The λ clip (finding 10).** The environment clips every policy's λ to 0.70–1.25
  (`engine_env.py:1006`), while the baseline takes the ECU's λ unclipped. An ECU fitted to the
  Honda's enrichment (λ {{HONDA_RAW_DEEP:.2f}} in its High Load windows) would run the neutral agent at 0.70 against
  the baseline's {{HONDA_RAW_DEEP:.2f}}, so the neutral action would not be neutral (mistake 10).
  - Before any EPA engine's ECU is built, the floor is set per engine to min(0.70, the engine's
    deepest EPA λ, cell-referenced, − 0.01): Mazda {{LAMFLOOR_mazda:.3f}} (deepest {{DEEP_mazda:.3f}}{{DEEP_NOTE_mazda}}), Honda
    {{LAMFLOOR_honda:.3f}} ({{DEEP_honda:.3f}}), Ford {{LAMFLOOR_ford:.3f}} ({{DEEP_ford:.3f}}).
  - The neutral action must reproduce the baseline exactly on every engine's locked climb and test
    roads. Trims below the deepest EPA λ are an extrapolation of the combustion model (not covered).

## 5. The cars

The Supra keeps X1's road load in this test (decision 31, `results/VALIDATION_DECISIONS.md:154`).
That road load is 15–22 % under EPA's, from a re-implementation, UNVERIFIED (`REFERENCES.md:785-788`;
version 1 cited `:427`, a different row, finding 19); this is a declared limitation, not gated here.

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
- **The data.** The tests on the first fuel batch, 61704001–044: {{N_D3}} files, pinned by sha256 in
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
  above the Mazda's hot MAP floor, {{FLOOR_mazda:.1f}} kPa: data, not the model's MAP, which would let the model
  choose its population. *Fired:* the chain's demanded torque at or above 2 bar BMEP. A row decides
  with at least 3 segments and 2·u_stat ≤ R. Segments whose modelled charge temperature falls
  outside the Mazda's EPA intake-temperature range ({{FIRED_IAT_MIN_mazda:.1f}}–{{FIRED_IAT_MAX_mazda:.1f}} °C) are not covered, and are reported
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
  {{U_ETA_PCT:.2f}} % on the torque demand; the N/V-to-D3 radius gap, 1.6 % uniform, is {{U_RAD_PCT:.2f}} %. Together that is
  {{U_TQ_PCT:.2f}} % of torque, carried to the flow at the demand ×{{FLOW_PER_PCT:.3f}}: **u_input = {{U_FUEL_PCT:.2f}} % on the fuel and the
  air**, common to every segment.
- **C3a and C3c, the hot bias of fuel and of air: descriptive.** 2u_input = {{U2_FUEL_PCT:.1f}} % alone exceeds
  E2a's {{R_E2a:.1f}} %, so as level rows they would read untested by construction (finding 25).
- **C3b: R = {{R_C3b:.1f}} %** (d, part P5), the mean absolute relative error of the model's fuel over the
  fired segments (the flow at the demand, as D1).
- **C3d: R = {{R_C3d:.1f}} %** (d, part P5), the same for the model's air against the car's MAF
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
demanded torque must sit more than max({{R_E1a:.1f}} %, |E1a| + 2u_val) from the car's kickdown threshold,
SHIFT_LOAD·T_wot, or the CVT law's λ·T_wot. That is E1a's R, or the torque error the validation
actually leaves when E1a reads worse, since a level row never drops an engine. Then a torque error
the validation accepts cannot change the gear the climb is driven in. A one-gear change moves rpm by
a whole ratio step, far outside every R here. The B58 has no E1a and uses {{R_E1a:.1f}} %. A climb that fails
the rule is redrawn; the roads are not fixed yet.

## 6. The table gates (decision 28)

Every reported agent is scored on the exact cycle (decision 28). A table's error therefore reaches a
reported number only through training: an agent learns on the table, and may learn to exploit it. A
uniform table error cancels from the baseline-relative reward (`engine_env.py:1020-1031`). The table
is the sixth part of the budget and is held to b. The gates apply to every engine's table, the B58's
included. The training backend and the scoring backend are recorded as separate fingerprint fields
(decision 28), with this file's sha256.

**S1, open loop: the table against the exact cycle.** The points are 6000 environment calls from
hand-written and random policies on training roads, inner-loop iterates included, and 4000 points
spread uniformly over the box those calls visit. With 6000 points, a 95th percentile rests on about
300 points beyond it.

- **S1a: R = {{R_S1a:g}} % per lever.** The aggregate fractional error Σ|ΔEGT_table − ΔEGT_exact| /
  Σ|ΔEGT_exact| for each lever step:
  - λ −0.05 (the hand-written head start's −0.055, `results/preview_ceiling.txt:42`);
  - MAP −10 kPa (current-grade's boost pull, `results/VALIDATION_PLAN.md:443-444`);
  - spark −0.75° (one logged step, `:181`).

  The basis is section 1.2a: a table that cools by the wrong amount teaches the wrong head start. A
  coarse λ grid can fail this gate near λ = 1, where the exact cycle's TIT has a corner.
- **S1b: R = {{R_S1b:.1f}} %**, the 95th percentile of |T_table − T_exact| / max(|T_exact|, 40 Nm), the
  denominator the B58's table was measured with (`fe_out/strand_repo-stats-timing.md:140`) and the
  environment's tracking uses (`engine_env.py:1022`). Its basis is the uniform-bias consequence:
  {{BFRAC_PCT:s2}}/{{FLOW_PER_PCT:.3f}} = {{E1B_RAW:.2f}} %.
- **S1c: R = {{R_S1c:.1f}} %** for air and fuel; if the flows are computed in closed form rather than
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
- **S2a: R = {{R_S2a:.3f}} points**, |d_table − d_exact| for the hand-written preview pair: the predictive
  policy reading the largest grade within the next H seconds, minus current-grade. Fixed policies
  are scored on the table and on the exact cycle, with the damage read with and without the knock
  term; both must pass.
  - Five random pairs are **reported, not gated**: an action drawn uniformly from the action box,
    redrawn every **30 s**, seeds 0–9. Version 1 tied the hold to `engine_env.py:711`'s preview,
    which decision 27 changes. A relative damage error δ moves a cut by (1 − c)·δ, three times more
    at c ≈ 0 than at the agents' c ≈ 0.68, and random actions span the whole box. A table could fail
    on random pairs alone for errors no agent visits.
- **S2b: R = {{R_S2b:.3f}} points, the check decision 28 names:** agents trained on the table, scored on the
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
| identity | C1, C2, the neutral-action check | — | a coding defect: fix it and re-run | | |
| rule | C5 | — | a climb that fails is redrawn | | |
| descriptive | E1b, E1i, E2b, E3b, E5, C3a, C3c, C4, S1d | reported, never gating | | | |
| perturbation | E6 | labels (excluded for a constant) and preregistered sensitivity rows; never a drop | | | |

- **Version 1 kept an engine whose d rows read limited or untested, and dropped it only on off**
  (finding 2). Its R then bounded nothing, and the budget held only for validated rows.
  - Version 2 keeps such an engine but **carries what its rows measured**. A limited d row has
    |E| ≤ R + 2u_val, up to 2R, and its part's band grows to match. An untested row's band is as
    wide as its own data make it.
  - Version 1 also said "a gate passes on validated or limited" and, two sections later, kept
    untested d rows. Both sentences are gone.
- **A d row with no statistic drops the engine.** That is a row with no deciding line, or a row
  excluded for every constant it claims to test. No band can be computed for it, so it is at least
  as strict as the tables, where untested ends training on the table (finding 2).
@wrap - **An untested d row that has a statistic enters with its band instead of dropping the engine** (decision 36, `results/VALIDATION_DECISIONS.md` section G, adopted 21 October). E8 is expected to read untested on every engine, the B58 included (section 1.5), so a drop would end the four-engine test before it began. The band carries the same information as a number: an untested row's band is at least b·(1 + |E|/R), and a verdict inside it reads MODEL-LIMITED.
- **The engine's model band Δ_e** is the RSS over its six parts, with the linear sum reported beside
  it. κ is a part's factor: 1 when its rows read validated, else (|E| + 2u_val)/R, the larger of its
  rows' when it has two.
  - The multiplicative parts, P1 (D1), P2 (E4b), P4 (E8) and P5 (C3b, C3d), contribute
    κ·b·(d/MEI)·φ each, with φ = max(1, |1 + ln(1 − c)|) at both arms' realised median cuts.
  - P3 (L1) contributes κ·b.
  - P6, the table, contributes b when the engine trains on its validated table (its S2 statistics are
    additive and S1 is a screen), and nothing when it trains on the exact cycle.
  - The preregistration reports every d with its model band. **A verdict that changes when d moves
    within ±Δ_e is reported MODEL-LIMITED**, whatever its seed interval says.
@wrap   - The cross-plant comparison of decision 26 carries the bands too: d_i − d_j has a model band of √(Δ_i² + Δ_j²) beside its seed uncertainty, and two engines count as equivalent only within the MEI (decision 37, section 1.1).
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
other way. The two tightenings this file allows (L1, E8) are measured on hand-written policies
before any held-out statistic exists.

## 8. What a pass does not establish

- **Cut levels stay model-dependent, {{CUT_LEVEL_PHRASE}}.**
  - A lever error ε moves a cut c by ε·(1 − c)·|ln(1 − c)|. For 0 ≤ c < 1 that is at most 0.368·ε;
    for c < 0 it is larger (1.39·ε at c = −1).
  - At E4b's limit of {{R_E4b:g}} %, that is {{CUT_ERR_043:.1f}} points of cut at c = 0.43, and {{CUT_ERR_068:.1f}} points at c = 0.68.
  - These gates protect d, not cuts. A cut is reported as model-dependent, never as a property of
    the engine.
- **Which gates can bind (finding 32).**
  - The d rows that can realistically read worse than validated on a calibrated engine are E4b, L1
    and E8; S2 can realistically fail a table.
  - D1, C3b and C3d at {{R_D1:g}} % fail only a gross model: the B58's one air-path comparison reads +1.9 %
    (`results/VALIDATION_PLAN.md:289`). S1b and S1c are screens.
  - The level rows (E1a at {{R_E1a:.1f}} %, E2a at {{R_E2a:.1f}} %, E3a, E4a, L0 at {{R1_K:g}} K) can bind, but never drop an
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
  - D1 bounds the flow at the demand to {{R_D1:g}} %, and so τ's flow part. The flow's absolute level rests
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
@wrap - **Settled before any calibration.** Version 2 left three points open for the team here: the collapse test's equivalence margin, b with six parts, and E8's expected untested label on every engine with its band. Decisions 37, 38 and 36 settled them on 21 October (`results/VALIDATION_DECISIONS.md` section G): the margin is the MEI (section 1.1), b = MEI/6 (section 1.3), and an untested row with a statistic enters with its band (section 7). Still open: Jad's column of those three decisions. An answer that differs, given before the first fit, is applied before it, in this file's generator, as a new version.

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
- **"The denser grid did not shrink these cut differences (max 1.48)"** (`:167`). Version 1 omitted
  this while offering only a denser grid as the remedy (finding 13).

Set against this contract:

- S1b and S1c ({{R_S1b:.1f}} %, {{R_S1c:.1f}} %) sit far above the measured torque error, and are called screens;
- S1a and S2b were never measured;
- the hand-written preview pair moved by 0.00 on the locked climb's frozen twenty. S2a is defined on
  decision 34's roads, which are not drawn yet;
- the 1.14 comes from the X1/X2 agents, trained on the exact plant and scored on the table. That is
  not an S2 statistic; as one it would exceed S2's {{R_S2a:.3f}} by {{S2_EXCESS:.3f}}.

**The draft thresholds of 20 October equalled these measured errors and were withdrawn for that
reason** (`fe_out/design.md:104-116`; `review_0` issue 7). None of the Rs here is a measured error.

**Also seen:**

- X1's and X2's results (`results/X1_RESULT.txt`, `results/X2_RESULT.txt`) and the seed statistics
  behind decisions 29–30.
- The preview ceiling: 0.13, 0.42 and 1.19 points on the locked climb (`results/preview_ceiling.txt`).
- The D3 figures of section 5 (C4), and each car's locked-climb operating point from the vehicles
  strand: the CX-9 in 4th at 4173 rpm and 305 Nm, the F-150 in 4th at 3470 rpm and 392 Nm, the
  Accord at high rpm (`fe_out/strand_vehicles.md:194`). These come from a re-implementation and are
  UNVERIFIED.
- The design notes' sections 2, 3 and 4 (`fe_out/design.md:59`, `:96`, `:104-116`), both reviews of
  20 October, and the review of 21 October, whose 37 findings section 11 answers.
- **Computed for this contract on the B58 plant alone:** the sensitivities with the ECU in the loop
  (section 1.4); the ECU-strategy shifts, under K3 and at a fixed knee (section 1.5); and the
  knee-shift re-scores of the committed records (section 1.2c).
@wrap - **Seen by version 3's session**, which only turned version 2's scripts into the generator and ran it: version 2's two files, the decision sheet and the generator's outputs, whose steps 1, 2 and 6 read the EPA tables' structure alone. One text search of the tree, for version 2's 1.086, printed a whole row of the Mazda's steady table (spreadsheet row 191, at 4501 rpm, on the calibration line {{MAZDA_ROW191_LINE}}); none of its values was compared with any model.

**The thresholds are B58-propagated.** Section 1.4's coefficients are the B58's, at its locked
climb's cell, with its ASSUMED housing constants, except that f is bounded. The same contract with
each engine's own coefficients would give other numbers. Those are reported beside the results and
never move an R.

## 10. Reproduce

@wrap `python engine_thresholds.py` runs every step in order and writes both files; its docstring says what each step reads and computes. Each step's output and its printout (`<step>.txt`) are kept in `{{OUT_DIR}}/`, with `run.json`, the Python, NumPy and platform that ran them and each step's wall-clock time. No other output, and neither of the two files, holds a time, so a re-run on one platform gives every one of them back byte for byte (section 12). The JSON records the sha256 of every file of the generator (`generators`) and of every step output it read (`generator_inputs_sha256`), each with CRLF read as LF, so that a Windows and a Linux checkout give the same hashes. `python engine_thresholds.py --build-only` rebuilds the two files from the saved outputs in seconds, and `--check` exits 1 if either differs from what the code writes.

@wrap 1. **The split:** step 1, `thresholds/split.py`, from the EPA tables' structure alone (their sha256 are in `epa_tables_sha256`), and step 2, `thresholds/alpha_nodes.py`. A re-derivation must reproduce the counts of section 2.2, or stop.
@wrap 2. **The B58 coefficients:** step 3, `thresholds/b58_propagation.py`.
   1. Run the locked climb as `validation_numbers._climb` does: neutral action, frozen episode 1,
      dt 1 s.
   2. Take the median operating point over t 400–718 s.
   3. Evaluate `plant.run_cycle` there at MAP ± 2 kPa, at fixed spark and along the ECU's schedule,
      at λ −0.01 to −0.15 and at spark ±0.75°.
   4. **Run the climb again with the cycle's torque × 1.01 and × 0.99** for the baseline and the
      agent, and read the medians off (finding 1).
@wrap 3. **The knee-shift slope:** step 4, `thresholds/knee_shift.py`, from the per-step records of `results/agents/terrain_dt1` and `extremes_dt1`, which stay on the training machine (gitignored).
@wrap 4. **The ECU's strategy:** step 5, `thresholds/ecu_shift.py`, the {{N_RUNS}} runs of section 1.5 ({{N_RUNS_FIXED}} `fixed`, {{N_RUNS_K3}} `k3`), each in a process of its own and independent of the others, `--jobs` at a time. It is most of a full run's time.
@wrap 5. **The contract:** step 6, `thresholds/contract.py`, reads them all and writes the JSON. It recomputes every R from those numbers, the MEI, R1 and decision 38's b, and pins the D3 files by sha256 against the data folder's manifest. Step 7, `thresholds/document.py`, writes this file from `thresholds/document_template.md`, and stops instead when a sentence's wording no longer holds for the number it carries. It needs git and a git checkout of the repository, because its last claim is checked against the .py files a commit would hold.

@wrap Version 2's scripts (`split.py`, `alpha_nodes.py`, `b58_propagation.py`, `knee_shift.py`, `ecu_shift_one.py` and `build_contract.py`) lived in a session's scratch folder, and version 2's JSON carried their source text; steps 1-6 are those scripts, committed (section 12).

## 11. Version 2: the review of 21 October, finding by finding

Every finding was reproduced before it was applied: the numerical ones by re-running the scripts of
section 10, the structural ones from version 1's `split.json` and the tables, the citations by
opening them. All 37 held. Their substance, the verdict and the change, as version 2 recorded them
(at b = MEI/5; section 12 says what version 3 changed):

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
| 12 | level rows cannot certify the gas that heats a housing | confirmed (`REFERENCES.md:311`, `:664-667`; `plant.py:278-281`) | absolute housing statements not covered; level rows restated as the 850 °C row's inputs |
| 13 | two seen items undisclosed; "by anyone" claims too much | confirmed (`fe_out/design.md:180`; `strand_repo-stats-timing.md:167`) | both disclosed; the claim limited to this session; remedies aimed at the measured cause |
| 14 | S2a read the frozen test episodes before the preregistration | confirmed | S2a on practice episodes |
| 15 | S2b measures exploitation, not the backend's effect on d; S1b/S1c cannot fail a realistic table | confirmed | stated; an optional exact-trained comparison; S1b and S1c named screens |
| 16 | E7a used the B58's f against the f ≤ 1 rule; e's population unnamed | confirmed | f bounded everywhere (5.183 K, 2.451 K per 1 %); L0's e from the hot λ≈1 rows |
| 17 | the five parts double-counted the flow; the null-difference sentence did not follow | confirmed | torque and flow one part (D1); the sentence withdrawn; additive parts named |
| 18 | the JSON's flat list lacked the B58's C5; the generators were uncommitted | confirmed | the B58's C5 added; sources and sha256 in the JSON; committed in version 3 (`engine_thresholds.py`, section 10) |
| 19 | two citations wrong; LHV moved in the plant but not the thermal network | confirmed (`REFERENCES.md:785-788`; `PREREGISTRATION_X1.md:119`; `thermal.py:245`) | citations corrected; bands "proposed by this contract"; E6 row 3 moves both |
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

@wrap Written 21 October 2026, before any calibration, by `python engine_thresholds.py`. Decisions 36-38 (`results/VALIDATION_DECISIONS.md` section G) were adopted that day on Ghassan's delegation ("fix all the way you see fit"), so that this contract could be committed before the first fit. Jad's column is open; an answer that differs, given before the first fit, is applied before it, in the generator. What changed from version 2:

@wrap - **Decision 38: b = MEI/{{N_SHARES}} = {{B:.3f}} points per part** (version 2: MEI/{{N_SHARES_V2}} = {{B2:.3f}}). Every d-row R follows from b and is 5/6 of version 2's before it is rounded down: D1, E4b, E8, C3b, C3d, S1a and S1c {{R2_D1:.1f}} → {{R_D1:.1f}} %, L1 {{R2_L1:.1f}} → {{R_L1:.1f}} K, S1b {{R2_S1b:.1f}} → {{R_S1b:.1f}} %, S2a and S2b {{R2_S2a:.3f}} → {{R_S2a:.3f}} points. The level rows (E1a, E2a, E3a, E4a, L0) rest on R1 and do not move.
@wrap - **What moves with b.** The errors worth b: E1b's torque {{WB2_E1b:.1f}} → {{WB_E1b:.1f}} %, E2b's fuel {{WB2_E2b:.1f}} → {{WB_E2b:.1f}} %, and E8's shifts, {{E8_WORTH_CHANGE}}. The budget's totals: six aligned parts add to {{LINEAR_MEI:.2f}} MEI (was {{LINEAR_MEI_V2:.2f}}) and independent ones to {{RSS_MEI:.2f}} MEI (was {{RSS_MEI_V2:.2f}}); a true d at the MEI reads {{IND_LO:.2f}}–{{IND_HI:.2f}} MEI if the errors are independent (was {{IND_LO_V2:.2f}}–{{IND_HI_V2:.2f}}) and {{ALN_LO:.2f}}–{{ALN_HI:.2f}} if they align (was {{ALN_LO_V2:.2f}}–{{ALN_HI_V2:.2f}}). The sentences that quote these numbers follow them: D1's share of τ (section 4), the cut-level example (section 8) and the B58 table's pair gap against S2 (section 9).
@wrap - **Version 2's list of the MEI/6 values** (`budget.if_b_were_mei_over_6`) gave S1b 12.2 % and S2 0.9 points: the first scaled the already rounded 14.7 %, the second rounded b to one decimal. Computed from b, as every R here is, they are {{R_S1b:.1f}} % and {{R_S2a:.3f}} points. The JSON keeps version 2's values in `budget.version_2_at_mei_over_5` instead, beside `budget.decision`.
@wrap - **Decision 37**, the collapse test's equivalence margin, is the MEI (section 1.1; `collapse_test` in the JSON). **Decision 36**: an untested d row with a statistic enters with its band, and a verdict inside the band reads MODEL-LIMITED; a row with no statistic still drops the engine (section 7; `on_failure.d` and `decisions` in the JSON). They close section 8's three open items.
@wrap - **The generator is committed beside this file** (section 10), and the JSON's `schema` is 3: `generators` holds the hashes of the committed files instead of their source text, and `generator_outputs`, `generator_run`, `collapse_test` and `budget.version_2_at_mei_over_5` are new. Its re-run of 21 October gave back version 2's outputs of steps 1-5 exactly, line endings normalised and the ECU runs' wall-clock `seconds` aside, so no number of version 2 moved except through decisions 36-38 and the three corrections below.
@wrap - **Three corrections, found while the .md was turned into a template; none is a threshold.** Section 1.5's pair column and its thermal-only agreement are computed from unrounded cuts: version 2 differenced cuts already rounded to 0.01, so four pair entries move by 0.01, and the agreement, whose largest exact difference is at spark −3.0°, moves from 0.46 to {{THERMAL_AGREE:c2}} percentage points ({{THERMAL_AGREE:.4f}}, rounded up because the sentence states a bound). And the Honda has {{HL_ALL_honda}} high-load lines, not 12: version 2 counted its hold speeds, and 1700 and 1800 rpm are one line by rule 2.
@wrap - **Found by the independent re-run of 21 October; none is a threshold.** The thermal-only agreement is a bound, so it is rounded up: {{THERMAL_AGREE:c2}}, where the first draft printed {{THERMAL_AGREE:.2f}}. The first run wrote each ECU run's wall-clock `seconds` into its output and every step's time into the JSON's `generator_run`, so no re-run could give back the JSON's sha256 of those outputs, nor the JSON itself. The times are now in `run.json` alone, and step 6 refuses an ECU output that still holds one. A full re-run after these changes gave back every output of steps 1-5 byte for byte, the dropped `seconds` aside, and both files byte for byte as `--build-only` wrote them from the outputs before it. Step 7 needs git and a git checkout (section 10): its last claim reads the .py files a commit would hold, and a copy without `.git` stops there with that message.

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

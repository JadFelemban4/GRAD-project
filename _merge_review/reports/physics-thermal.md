# physics-thermal: whose THERMAL model is more physical, Jad's or Ghassan's?

Label: physics-thermal. Work directory: `scratchpad/work/physics-thermal/` (all runs in copies; nothing in `trees/`, `To main` or `GRAD-project` was modified; git used read-only).

## One-paragraph answer

**Exhaust flow: Ghassan, high confidence.** Coolant: Ghassan, medium. Turbine node: identical on both, so equal. **Oil: mixed.** Ghassan's oil node fits the logs much better (lower RMSE on every drive, held out) and removes the 14 s time constant and the +22 to +32 K pull spikes of Jad's. But the logs do not identify its fuel share: a flat profile across a 25x range. Its sustained-load sensitivity is about 2.5x below the car's own. It misses drive10's sustained oil exactly as badly as Jad's (row 8: 97.0 C against 96.4 C, car 103-111). At drive10's peak it is worse than Jad's (-16.9 K against -4.1 K). The 110 C and 94 C oil figures on the locked climb are both extrapolations: the logs contain no sustained window at 2500-3000 rpm above 5 g/s. The near-equal peak turbine (884.0 against 883.0 C) is a cancellation of two opposite ~6 K effects, not agreement. The preview-over-current-grade gap stays between -0.31 and -0.45 points under every thermal and exhaust variant tested.

## What was read, cover to cover

Read in full: JAD/thermal.py (192 lines), BASE/thermal.py (183), GHASSAN/thermal.py (225), GHASSAN/car_thermal.py (231), GHASSAN/calibrate_thermal.py (314), GHASSAN/derive_params.py (332), GHASSAN/derived.py (66), JAD/engine_env.py (1037), GHASSAN/engine_env.py (1279), JAD/app/estimator.py (522; GHASSAN's differs only in the 6 diff lines shown below), GHASSAN/validate.py (357), JAD/check_premise.py (219; Ghassan's differs only by the premise.json writer), GHASSAN/data/derived_params.json thermal section, GHASSAN/results/thermal_calibration.json, all 15 of Ghassan's commit messages.
Read in part (thermal-relevant sections): plant.py (run_cycle 186-341, both branches; they differ only in the boost ceiling), REFERENCES.md section 4 (both) and 4b (Ghassan), AUDIT.md M2 (JAD 368-373), AUDIT_FIXES.md M2 rows (both), GHASSAN/model_vs_data.py (thermal functions and its results JSON), JAD/fingerprint.py (grep of PLANT_FILES), MERGE/thermal.py conflict hunk.
Not read: the binaries, README/CLAUDE/CHECKPOINT beyond what was needed.

## 1. Exhaust mass flow into the turbine node (co-work C3)

Where it is:
- JAD/engine_env.py:764 `self.thermal_base.step(self.dt, base["mdot_fuel"], base["mdot_fuel"] * 15.0, ...)`, and :778 the same for the agent.
- JAD/app/estimator.py:439 `exh = fuel * 15.0`.
- GHASSAN/engine_env.py:880 and :894 use `mdot_air + mdot_fuel`, and GHASSAN/app/estimator.py:440 uses `out["mdot_air_gps"] + fuel`. This arrived in commit cbb8d09 (29 Sep 09:44 +0300). `git log -S` shows Jad never touched those lines after f6b46e9.

Jad's branch is internally inconsistent.
- plant.py:311 computes the exhaust flow for its own port heat loss as `(m_air + m_fuel)`.
- JAD/validate.py:150, identical on base and on both branches, feeds the thermal step `mf * (1 + 14.7 * 1.0)`. So the "turbine tau 48.0 s" row was computed with air + fuel while the environment runs fuel x 15.
- JAD/AUDIT.md:371 (M2 item 3) had already named exactly this: "engine_env.py:519,533 and app/estimator.py:362 use fuel x 15 ... At lambda = 0.81 the gas-side UA is 16 % high".
- JAD/AUDIT_FIXES.md:137 nonetheless marks M2 **FIXED**; only its backpressure and damage items were fixed.
- GHASSAN/AUDIT_FIXES.md (~line 377) records "M2 missed two items" and fixes it.

The formula error follows from mass conservation: exhaust/fuel = 1 + 14.7 lambda (plant.py:196 `m_fuel = m_air/(AFR_STOICH*lam)`, with AFR_STOICH = 14.7).

| lambda | true exhaust/fuel | error of fuel x 15 |
|---|---|---|
| 1.00 | 15.700 | -4.5 % |
| 0.95 | 14.965 | +0.2 % |
| 0.90 | 14.230 | +5.4 % |
| 0.85 | 13.495 | +11.2 % |
| 0.81 | 12.907 | +16.2 % |
| 0.80 | 12.760 | +17.6 % |

**What it does to the enrichment lever.** Measured at a climb-like point with the plant: 2706 rpm, 176 kPa, spark 4 deg, air held at 113.9 g/s (`work/physics-thermal/lam/lam_table.log`).

| lambda | EGT C | exhaust true g/s | exhaust f x 15 g/s | housing steady state true C | housing steady state f x 15 C | tau true s | tau f x 15 s |
|---|---|---|---|---|---|---|---|
| 1.00 | 1007.6 | 121.6 | 116.2 | 871.3 | 865.8 | 47.1 | 48.9 |
| 0.90 | 945.5 | 122.5 | 129.1 | 818.7 | 824.3 | 46.8 | 44.7 |
| 0.85 | 921.4 | 123.0 | 136.7 | 798.4 | 809.2 | 46.6 | 42.5 |

Enriching from 1.00 to 0.85 lowers EGT by 86.2 K. The housing steady state falls 72.9 K under air + fuel but only 56.7 K under fuel x 15. **Fuel x 15 credits the enrichment lever about 22 % less housing cooling** (21 % at 0.90), and it makes the rich housing about 9 % faster than it should be. At lambda 1 it runs the baseline housing 5.5 K cool.

**Measured effect alone** (J1 = JAD tree with only :764 and :778 changed to air + fuel; `check_premise.py` itself, 3806 s under load, exit 0). The trace driver `trace_premise.py` reproduced the orchestrator's `jad_check_premise.log` exactly for J0 (959.8 / 884.0 / 109.9, cuts 29.25 / 34.03 / 33.59).

| row | JAD as is (J0) | JAD, air + fuel only (J1) | delta |
|---|---|---|---|
| baseline damage | 959.8 | 1085.3 | +125.5 (+13.1 %) |
| baseline peak turbine | 884.0 C | 889.5 C | +5.5 K |
| baseline peak oil | 109.9 C | 109.9 C | 0 |
| reactive / current-grade / predictive damage | 679.0 / 633.2 / 637.4 | 690.3 / 624.0 / 627.9 | |
| cuts: reactive / current-grade / predictive | 29.3 / 34.0 / 33.6 % | 36.4 / 42.5 / 42.1 % | +7.2 / +8.5 / +8.6 pts |
| preview over current-grade | -0.44 | -0.36 | +0.08 |
| preview over reactive | +4.33 | +5.75 | +1.4 |

Why, from the per-step traces (`work/physics-thermal/attribution.log`, climb t >= 300 s):
- The baseline runs at lambda 1.000. It feeds the housing 117.7 g/s where air + fuel is 123.2 g/s, so its steady state is 884.1 C instead of 889.6 C, and its turbine damage term is 862.3 instead of 987.8.
- Current-grade runs at lambda 0.945, where fuel x 15 is nearly exact (125.3 against 124.4 g/s, 860.6 against 859.8 C).
- So fuel x 15 understates the baseline, which runs at lambda 1, and barely touches the protecting policies. Every "cuts damage N %" on Jad's branch is therefore understated by 7-9 points. The bias is conservative, not flattering.
- Sighted and blinded arms share the lever, and the preview gap barely moves.
- In Ghassan's env the reverse swap gives the same size: G1 (fuel x 15) 811.0 / 877.5 C against G0 920.1 / 883.0 C; cuts 24.8 / 34.8 / 34.4 against 32.0 / 43.4 / 43.1.

**Verdict: Ghassan, high confidence.** Air + fuel is mass conservation, the plant's own definition, and Jad's own validate.py's definition.

## 2. Every other difference between the two thermal.py files

The step equations are identical for the block and the turbine. The oil equation gains two terms: `k_oil_rpm*(rpm/3000)**n_oil_rpm` heating and `ua_oil_ram*v` sump cooling (GHASSAN/thermal.py:191-195). `rpm` is a required keyword-only argument (:168). Parameters come from data/derived_params.json through derived.py, and a missing file raises; there is no silent default.

| parameter | JAD | GHASSAN | how obtained | plausibility / comment |
|---|---|---|---|---|
| c_turb | 6000 J/K | 6000 J/K | ASSUMED on both | load-bearing; no channel measures it |
| ua_gas_turb | 0.90 W/K per g/s | 0.90 | ASSUMED on both | identical |
| ua_turb_amb | 18 W/K | 18 | ASSUMED on both | identical |
| c_oil | 12 000 J/K | 27 213 J/K | J: assumed; G: fitted, weakly identified (Ghassan says so) | the time constant is what matters, rows below |
| ua_block_oil | 800 W/K | 474 W/K | J: fitted 8 Sep on the p95 oil-coolant gap over three drives with the fuel share ASSUMED at 5 % (JAD/thermal.py:46-68); G: fitted jointly (stage 1, block pinned) | the profile (section 3d) shows this trades with the fuel share (474 to 1860 W/K) |
| ua_oil_amb | 60 W/K | 0.38 W/K | J: assumed; G: fitted | G's standstill value is negligible |
| ua_oil_ram (new) | none | 0.68 W/K per m/s (24.8 W/K at 130 km/h) | G: fitted | physically motivated (sump in the airstream); the car's own data suggest a stronger road-speed effect (section 3c) |
| frac_fuel_to_oil | 0.050 (2200 W per g/s) | 0.0042 (184 W per g/s) | J: assumed; G: fitted | **not identified** by the logs (section 3d) |
| k_oil_rpm, n_oil_rpm (new) | none | 610 W at 3000 rpm, exponent 3.86 | G: fitted; structure picked on drive10 held out (calibrate_thermal.py:27-30) | the plant's own friction power scales as rpm^1.6-1.7 (plant.py:292; `lam/fmep_scaling.log`: 3000 to 4622 rpm gives x2.1 friction against x5.3 for rpm^3.86). As a share of friction the term runs from 4 % (2706 rpm) to 13 % (4622 rpm). The steep exponent is a fit artefact absorbing correlated load and low road speed on drive10, not friction physics |
| oil tau at rest / at 130 km/h | 14.0 s / 14.0 s | 57.4 s / 54.6 s | derived | car's apparent tau 70-100 s (G's validate row 9); G is closer but still outside |
| c_block | 105 000 J/K | 36 350 J/K | J: assumed; G: fitted, identified only as a ratio with frac_fuel_to_coolant by ONE warm-up (683640a0) | implausibly small as a physical capacity for an engine block plus its coolant if read literally (engineering judgement, UNVERIFIED, no source opened). Ghassan's own docstring says quote ratios only |
| frac_fuel_to_coolant | 0.26 | 0.178 | J: assumed; G: fitted | warm-up rate with the radiator shut: J 0.109, G 0.216 K/s per g/s fuel |
| ua_block_amb | 45 W/K | 2.4 W/K | J: assumed; G: fitted | implausibly low for convection plus radiation off a hot engine (engineering judgement, UNVERIFIED); it only acts with the radiator shut |
| t_stat_open / fully open | 87.85 / 96.85 C | 92.08 / 94.93 C | J: identified loosely from coolant; G: fitted | the car's regulated median is about 93 C (section 3b); G matches it |
| ua_rad_min/ram/fan | 300 / 60 / 700 | 427 / 85 / 996 | J: unidentifiable, reasoned; G: one fitted scale x1.42 on J's split | the split remains unidentifiable on both |

Search-box caveat. When 683640a0 is held out, the LOO fit lands on the search bounds (frac_fuel_to_coolant 0.050 = lower bound, c_block 20 986 against a bound of 20 000; `results/thermal_calibration.json`). The block ratio is not identified without that one drive.

## 3. Oil and coolant against the car, like for like

Harness: `work/physics-thermal/replay/replay_both.py`, 12.8 s.
- Inputs are identical for both models, from the raw logs, which are byte-identical on both branches (sha1 checked): measured fuel = air/(14.7 lambda), logged rpm, speed and ambient on a 1 s grid, the BaselineECU fan rule on the model's own block, and exhaust = air + fuel (not scored).
- The actual thermal.py modules are imported from copies.
- The harness **reproduces GHASSAN/results/thermal_calibration.json to the second decimal on all 7 drives**: drive10 JAD 7.55 / 5.51, GH 3.57 / 2.28, LOO 3.90 / 2.35.

### 3a. Free-running (both nodes free) and pinned (block set to measured coolant = what app/estimator.py does since M11)

| drive | min | car oil max | JAD oil RMSE / peak err | GH oil RMSE / peak err | GH held-out oil RMSE | JAD ect RMSE | GH ect RMSE | GH held-out ect RMSE | pinned oil RMSE J / G / G-LOO | pinned oil peak err J / G |
|---|---|---|---|---|---|---|---|---|---|---|
| 3aca2ec1 | 41.8 | 101.0 | 3.31 / +9.7 | 1.22 / -3.8 | 1.28 | 3.81 | 1.56 | 1.65 | 3.68 / 1.40 / 1.57 | +11.5 / -4.5 |
| 670063b2 | 7.3 | 98.0 | 7.93 / +28.8 | 5.17 / -1.2 | 5.65 | 4.47 | 5.31 | 5.39 | 6.58 / 1.75 / 2.07 | +26.0 / -2.8 |
| 683640a0 | 24.4 | 103.0 | 6.55 / +1.3 | 3.30 / -3.0 | **14.26** | 6.99 | 2.93 | **14.18** | 2.59 / 1.78 / 2.11 | +4.4 / -1.2 |
| 7475b5d7 | 55.1 | 107.0 | 7.12 / **+32.2** | 6.05 / -4.5 | 6.22 | 4.84 | 6.66 | 6.82 | 4.88 / 1.74 / 1.77 | +26.2 / -4.6 |
| cb67b01f | 21.6 | 95.0 | 4.37 / +23.5 | 1.31 / -1.0 | 1.41 | 3.88 | 2.60 | 2.84 | 4.48 / 1.10 / 1.18 | +22.0 / -1.2 |
| drive10 | 119.4 | 117.0 | 7.55 / -4.1 | 3.57 / **-16.9** | 3.90 | 5.51 | 2.28 | 2.35 | 3.62 / 2.56 / 2.78 | -1.4 / -12.4 |
| fb988991 | 14.7 | 96.0 | 4.88 / -1.6 | 1.95 / -2.0 | 2.34 | 4.02 | 0.98 | 1.17 | 2.60 / 1.99 / 2.08 | -0.9 / -2.0 |
| mean of 7 | | | 5.96 | 3.22 | 5.01 | 4.79 | 3.19 | 4.91 | 4.06 / 1.76 / 1.94 | |

Reading:
- **Oil RMSE, held out:** Ghassan's is better on 6 of 7 drives free-running and 7 of 7 pinned.
- **Coolant, held out:** better on only 4 of 7. The mean is 4.91 K against Jad's 4.79 K, because of 683640a0 (14.2 against 7.0 K). In-sample it is also worse on 670063b2 and 7475b5d7.
- **Peaks:** Jad's oil overshoots on every drive with pulls (+22 to +32 K, the 14 s node heated by 5 % of fuel). Ghassan's never overshoots but undershoots sustained peaks.
- Seconds with oil above 110 C on drive10: car 201, JAD 6, GH 0. On 7475b5d7: car 0, JAD 76, GH 0.

### 3b. Coolant regulation (`replay/results/coolant_dist.log`)

- The car's median coolant after warm-up is about 93 C on 6 of 7 drives: 93.0, 91.4, 93.2, 92.3, 92.8, 93.3.
- Ghassan's block sits at 92.2-92.3 C; Jad's at 88.3-89.6 C.
- Exception: 7475b5d7 (42 C afternoon), where the car's heat-management valve runs a median of 84.8 C. Neither fixed stand-in thermostat follows the valve's load- and ambient-dependent control.
- validate.py rows 10-11 by Ghassan's own rule: G 93.0 / 92.2 C, both inside; JAD thermal (G2v) 94.5 / 88.4 C, row 11 OUTSIDE 91.8-94.

### 3c. Is oil heat "engine speed, not fuel"? The car's own data say both (`replay/results/load_table.log`)

Method: 120 s rolling windows over the 7 drives, oil minus measured coolant (the models' block pinned to coolant, so this isolates the oil node), OLS gap ~ 1 + fuel + rpm + rpm^2 + v over windows above 2000 rpm. The windows overlap heavily, so these are descriptive slopes, not significance tests.

| | K per g/s fuel (pooled) | per 100 km/h |
|---|---|---|
| car | **+2.30** | **-8.48** |
| JAD model | +2.90 | +0.31 |
| GH model | +0.90 | -1.69 |

Within-rpm-bin fuel slope (K per g/s, v as covariate):

| rpm | car | JAD | GH |
|---|---|---|---|
| 2000-2500 | +1.50 | +3.19 | +1.02 |
| 2500-3000 | +1.54 | +2.70 | +0.84 |
| 3000-3500 | +2.53 | +2.83 | +1.36 |
| 3500-4000 | +2.15 | +2.31 | +0.55 |
| 4000-5000 | +2.82 | +3.48 | +1.12 |

In every rpm bin the car's oil gap rises with fuel. Ghassan's docstring (thermal.py:62-71, "oil heat follows ENGINE SPEED ... not fuel") is refuted in its "not fuel" half. Jad's node has the load dependence (about 25 % too strong pooled, about 75 % too strong at 2500-3000 rpm) but no road-speed cooling at all, while the car shows a strong one.

### 3d. The logs do not identify the fuel share (`replay/results/profile_oil.log`, `profile_peaks.log`, `profile_climb.log`)

Stage 1 of calibrate_thermal.fit (block pinned) was re-run with frac_fuel_to_oil fixed and the other six oil parameters re-fitted by the same seeded search. The free fit reproduces the shipped derived parameters exactly.

| frac_fuel_to_oil | objective (mean pinned oil RMSE, K) | ua_block_oil | model fuel slope (car +2.30) | drive10 pinned peak (car 117.0) | locked-climb steady oil |
|---|---|---|---|---|---|
| 0.0005 | 1.800 | 512 | +0.60 | 104.7 | 92.0 C |
| 0.0020 | 1.782 | 490 | +0.71 | 104.6 | 92.8 C |
| **0.0042 (shipped)** | 1.760 | 474 | +0.90 | 104.6 | 93.9 C |
| 0.0050 | 1.753 | 463 | +0.96 | 104.7 | 94.4 C |
| **0.0100** | **1.741** | 611 | +1.17 | 104.9 | 95.7 C |
| 0.0200 | 1.743 | 972 | +1.33 | 105.0 | 96.6 C |
| 0.0300 | 1.752 | 1230 | +1.48 | 105.1 | 97.5 C |
| **0.0500 (Jad's value)** | 1.759 | 1860 | +1.56 | 105.0 | 98.1 C |

- The objective is flat across a 25x range, 1.741-1.800 K.
- The shipped 0.0042 is not the optimum of Ghassan's own objective: 0.01 gives 1.741 K.
- Jad's 5 % share fits as well as Ghassan's once c_oil (108 kJ/K) and ua_block_oil (1860 W/K) re-fit.
- So "the data rejected the fuel share" is not supported. The data rejected Jad's COMBINATION: 5 % share, 800 W/K, 12 kJ/K, no rpm or ram term, tau 14 s.
- Every point on the profile still misses drive10's sustained oil (pinned hottest-10-min median about 102 C against the car's 109 C), so row 8 is a structural gap for the whole family.

### 3e. Claim C4 and row 8

- The drive10 free-running oil RMSE did fall **7.55 -> 3.57 K** in-sample (3.90 K held out). This is reproduced through the real modules.
- That figure is a whole-drive RMSE dominated by 119 min of cruise and idle.
- In the sustained part the recalibration changed nothing. Row 8 by Ghassan's own rule (G0v/G2v validate runs): **JAD thermal 96.4 C, GH 97.0 C, car IQR 103-111** (median 109).
- At the drive's 117.0 C peak (t = 808 s, prior 120 s at 4622 rpm, 78 km/h, 4.63 g/s; coolant 99.0 C): JAD 109.6 C (free-running), GH 100.1 C, GH held-out 98.8 C.
- Row 8's 12 K miss on Ghassan's side splits into 4.6 K of coolant (the valve lets the car's coolant reach 97-99 C, the model holds 92.6) and 7.3 K of oil node. With coolant pinned, the model's oil rises 4.4 K over coolant where the car's rises 11.7 K (GHASSAN/results/model_vs_data.json row8, reproduced by my replay).
- The drive10 structure choice was also made on drive10 held out, so its "held-out" 3.90 K is not fully independent.

### 3f. Why check_premise's peak oil is 110 C (Jad) against 94 C (Ghassan), and why the car logged 117 C on Taif

- The difference is entirely the thermal model. Jad's env with Ghassan's thermal (J2) gives 93.9 C; Ghassan's env with Jad's thermal parameters (G2) gives 109.4 C.
- A steady balance at the climb's own inputs (2706 rpm, 130 km/h, 7.7 g/s, block 93.5 C, 42 C; `replay/results/derived_quantities.log`) reproduces both peaks. Jad routes 16.9 kW into the oil (5 % of fuel) and gets 109.6 C, +16 K over the block. Ghassan routes 1.83 kW (0.42 % of fuel plus 0.41 kW rpm term) and gets 94.6 C, +1 K.
- The Taif oil ran hot because of 4000-4600 rpm at 70-100 km/h, in low gears on the mountain, with the coolant allowed up to 97-99 C.
- The locked climb is 2706 rpm at 130 km/h and 7.7 g/s for 9 minutes. The logs hold no sustained window at 2500-3000 rpm above 5 g/s, and only 6 overlapping windows at 4-5 g/s (`replay/results/load_table.log`). Both climb figures are extrapolations.
- Within Ghassan's structure, any admissible fuel share gives 92.0-98.1 C. Extrapolating the car's own 2500-3000 rpm slope (+1.54 K per g/s) gives roughly +7-8 K over coolant, about 100 C (UNVERIFIED extrapolation).
- Evidence points both ways: the slope shortfall and row 8 point above Ghassan's 94 C, and the 2500-3000 rpm over-sensitivity points below Jad's 110 C.
- The oil term is 28.2 of 959.8 baseline damage units on Jad's branch (2.9 %) and 8.5 of 920.1 on Ghassan's (0.9 %). The choice barely moves the ablation: preview over current-grade is -0.44 (J0), -0.45 (J2), -0.36 (J1), -0.36 (J3).

## 4. The turbine node

- Nothing changed in how the housing temperature is computed. The turbine lines of `step` are identical (JAD/thermal.py:164-170 = GHASSAN/thermal.py:197-203), c_turb, ua_gas_turb and ua_turb_amb are the same, and the plant's EGT path is identical (plant.py differs only in the boost ceiling).
- Only the exhaust flow fed to the node, and the operating point, changed.

Attribution of the baseline peak on the locked climb (seven variants, `work/physics-thermal/*_trace.log`):

| variant | env | thermal | exhaust | baseline damage | peak turbine | peak oil | cuts R / CG / P | preview vs CG |
|---|---|---|---|---|---|---|---|---|
| J0 | Jad | Jad | f x 15 | 959.8 | 884.0 | 109.9 | 29.25 / 34.03 / 33.59 | -0.44 |
| J1 | Jad | Jad | air + fuel | 1085.3 | 889.5 | 109.9 | 36.40 / 42.51 / 42.15 | -0.36 |
| J2 | Jad | Ghassan | f x 15 | 934.7 | 883.7 | 93.9 | 29.90 / 35.16 / 34.71 | -0.45 |
| J3 | Jad | Ghassan | air + fuel | 1059.5 | 889.2 | 93.9 | 37.07 / 43.65 / 43.29 | -0.36 |
| G0 | Ghassan | Ghassan | air + fuel | 920.1 | 883.0 | 93.9 | 31.99 / 43.42 / 43.10 | -0.32 |
| G1 | Ghassan | Ghassan | f x 15 | 811.0 | 877.5 | 93.9 | 24.80 / 34.82 / 34.43 | -0.40 |
| G2 | Ghassan | Jad params | air + fuel | 943.5 | 883.3 | 109.4 | 31.38 / 42.17 / 41.86 | -0.31 |

- Exhaust fix: **+5.5 K** (J0 to J1, and G1 to G0).
- Thermal parameters: -0.3 K (J1 to J3, G2 to G0).
- Every other env or plant change: **-6.2 K** (J3 to G0).
- Net: 884.0 to 883.0 C.
- The -6.2 K comes from the road load. On the climb, Ghassan's baseline asks 336 Nm against 340, burns 7.70 against 7.85 g/s, and runs EGT 1022.3 against 1027.2 C. That is air density from the 42 C ambient (1.1205 kg/m3 against a typed 1.2): aero drag 516.4 -> 482.2 N, total 2455.8 -> 2421.6 N, 7th-gear torque 340.2 -> 335.5 Nm (`lam/drag.log`).
- So "884 and 883" is a coincidence of two opposite changes of similar size. The models do not agree on the turbine inputs, and the damage they report differs by 12-13 %.

## 5. Verdicts per component

| component | verdict | confidence |
|---|---|---|
| exhaust flow into the turbine node | GHASSAN | high |
| turbine node (c_turb 6000, ua_gas_turb 0.90, ua_turb_amb 18, EGT path) | EQUAL (identical code; all ASSUMED on both) | high |
| oil node | MIXED: Ghassan better on logged RMSE and dynamics; neither right at sustained load; fuel share unidentified; Ghassan's load sensitivity too low, Jad's time constant wrong | medium |
| coolant / block node | GHASSAN on regulation (93 C setpoint, rows 10-11), with caveats (one warm-up drive identifies the block ratio; held-out coolant not better on average) | medium |
| API / robustness | GHASSAN (required rpm keyword, derived values with no silent fallback), but see the fingerprint hazard below | medium |

What stays ASSUMED on both: c_turb = 6000 J/K (sets tau and so H/tau), ua_gas_turb, ua_turb_amb, the radiator split, the heat-management valve's control law, and the 44 MJ/kg fuel heat basis. Plus, on Jad's side, every thermal parameter except ua_block_oil.

## 6. Other findings

1. **Fingerprint hazard after the merge.**
   - JAD/fingerprint.py:85 hashes `PLANT_FILES = ("plant.py", "thermal.py", "engine_env.py")` only.
   - After the merge the thermal, boost-ceiling, spark-offset, enrichment and kickdown constants live in data/derived_params.json, which derive_params.py rewrites whenever build_dataset.py runs (a new drive).
   - The physics can then change with plant_sha unchanged, and evaluate.py would not refuse an agent trained on the old parameters.
   - Also, the merge itself changes plant_sha (thermal.py, engine_env.py code), so evaluate.py will refuse every Phase D / D2 / C4 agent. That is correct, but it must be expected.
2. **Stale claim on Jad's branch.** JAD/AUDIT_FIXES.md:137 marks M2 FIXED while M2 item 3 (fuel x 15) is live at JAD/engine_env.py:764,778 and app/estimator.py:439.
3. **Inconsistency on Jad's branch.** validate.py:150 (air + fuel) and engine_env.py (fuel x 15) define exhaust differently. The published tau 48.0 s is the validate definition; the environment's climb tau is 48.4 s (J0 trace) against 46.6 s with air + fuel (J1).
4. **Stale docstring on Ghassan's branch.** GHASSAN/engine_env.py:1237-1242 still says the neutral fan 1.0 is "exactly neutral during the climb", which JAD/engine_env.py:972-1000 measured to be backwards on 19 Sep. With Ghassan's block regulating at 92.7 C on the climb, the fan rungs at 367/372 K are still mostly off or 0.4, so the correction applies there too.
5. **For Jad's trained agents.** In the fuel x 15 env an agent that enriches to lambda 0.85 is credited about 22 % less housing cooling than mass conservation gives. How much this changed what the Phase D / D2 / C4 agents learned was NOT measured.

## 7. Runs

All under `scratchpad/work/physics-thermal/` unless stated; Python 3.12 system interpreter, PYTHONIOENCODING=utf-8. The machine was at 100 % load (about 50-70 python processes from other agents), so runtimes are 15-17x the unloaded 227 s.

| run | exit | runtime | key output |
|---|---|---|---|
| `replay/replay_both.py` on JAD raw logs | 0 | 12.8 s | table 3a; reproduces thermal_calibration.json |
| `replay/explore_load.py` | 0 | about 20 s | hardest 60 s windows; car gap table |
| `replay/load_table.py` | 0 | about 60 s | slopes in 3c |
| G0v and G2v `validate.py` (Ghassan tree; G2v with Jad thermal params) | 0 / 0 | about 60 s | rows 8-11: 97.0 / 60.0 / 93.0 / 92.2 against 96.4 / 14.0 / 94.5 / 88.4 |
| `replay/profile_oil.py` | 0 | 1856 s | profile 3d |
| `replay/profile_peaks.py`, profile_climb | 0 | about 60 s | peaks and climb column in 3d |
| `lam/` lambda table, FMEP scaling | 0 | about 5 s each | section 1 and section 2 tables |
| `trace_premise.py` in J0 J1 J2 J3 G0 G1 G2 | 1 (tables printed, then the JSON dump failed on a float32; the numbers are from the printed tables) | 3759-3892 s | section 4 table |
| J1 `check_premise.py` (canonical) | 0 | 3806 s | baseline 1085.3 / 890 C / 110 C; cuts 36.4 / 42.5 / 42.1 %; preview vs current-grade -0.4, vs reactive +5.8 |
| `trace_one.py` in J0 J1 G0 x baseline, current-grade | 0 | 392-427 s | attribution.log (climb inputs) |
| read-only git in To main | 0 | | cbb8d09 introduced air + fuel; no Jad commit touched the lines; MERGE/thermal.py has one conflict hunk (98-211), and every thermal step caller in the merge already passes rpm |

## 8. Co-work claims checked

- **C3 (exhaust was fuel x 15; Ghassan made it air + fuel; Jad's branch still has the old way): CONFIRMED.**
  - Jad's branch at 086c519 still has fuel x 15 at JAD/engine_env.py:764 and :778, and JAD/app/estimator.py:439.
  - Ghassan's branch at 74de99a has air + fuel at GHASSAN/engine_env.py:880 and :894, and app/estimator.py:440, introduced in cbb8d09.
  - Mass conservation (plant.py:196) gives exhaust = fuel x (1 + 14.7 lambda), so fuel x 15 is -4.5 % at lambda 1 and +11.2 % at 0.85.
  - Jad's own validate.py:150 and plant.py:311 already use air + fuel, and AUDIT.md:371 flagged it.
- **C4 (oil closer to the car on the Taif trip; error 7.6 -> below 4 K): PARTLY.**
  - The whole-drive free-running RMSE 7.55 -> 3.57 K (in-sample) / 3.90 K (held out) is reproduced exactly through both thermal.py modules.
  - But the sustained-load oil did not improve: validate row 8 is 96.4 C (Jad's thermal) against 97.0 C (Ghassan's), car 103-111.
  - The drive's peak error got worse: -4.1 K (Jad) against -16.9 K (Ghassan), -18.2 K held out.
  - Seconds above 110 C: car 201, Jad 6, Ghassan 0.
  - drive10 was also used to choose the oil structure.
- **C10 (check_premise: turbine 884 and 883 C; preview adds nothing over current-grade on both): CONFIRMED, with a caveat on the first half.**
  - Reproduced: J0 884.0 C, preview over current-grade -0.44 points; G0 883.0 C, -0.32 points.
  - The agreement of peak turbine is a cancellation: +5.5 K from the exhaust fix, -6.2 K from the other env changes (mainly air density at 42 C: 7th-gear torque 340.2 -> 335.5 Nm).
  - The two branches report different damage: baseline 959.8 against 920.1, and current-grade cut 34.0 % against 43.4 %. 8.5 of those 9.4 points are the exhaust fix alone.
  - The preview result is robust: -0.31 to -0.45 points across all 7 exhaust and thermal variants.

## 9. The app estimator

The estimator pins the block to measured coolant (AUDIT M11), so its oil estimate is the pinned oil node in table 3a.
- Ghassan's gives lower RMSE on all 7 drives (1.76 against 4.06 K; 1.94 held out) and no pull spikes. Jad's reads +22 to +26 K high on pulls: false positives, 76 s above 110 C on 7475b5d7 where the car never passed 107 C.
- But Ghassan's under-reads drive10's sustained peak by 12.4 K. For a driver-facing alert that is the dangerous direction, a false negative.
- Its exhaust flow (air + fuel) is the correct one. The pin in GHASSAN/app/test_replay.py moved 890.6 -> 873.1 C for 7475b5d7 (commit cbb8d09 message); I did not re-run the app suite.

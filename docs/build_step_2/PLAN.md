<!-- RETIRED-OK: file -- a dated design record, kept as written by the design workflow of 21 October 2026 and never edited, only superseded; its runtimes and counts are design-time estimates, not figures of the project. verify_docs.py reports it as skipped on every run. -->
> **What this is.** The implementation plan for build step 2 of decision 24, written read-only by AI agents on 21 October 2026: five readers mapped the contract and the code, three independent designs were each reviewed adversarially, and this plan was synthesized from them. Five more reviewers then checked it against the files (`AMENDMENTS.md`, beside this file, 22 October). **Where the two disagree, the amendments govern**, and the decisions they lead to are `results/VALIDATION_DECISIONS.md` section H. Paths into a `scratchpad` folder are the session's own working files, not kept. Nothing was fitted, and no value of any EPA row was read.

# Build step 2 of decision 24: the implementation plan

Calibrating the Mazda 2.5 T, the Honda L15B7 and the Ford 2.7 TT on the B58's cycle model, freezing them, and validating them once on held-out EPA points under `results/ENGINE_THRESHOLDS.md`. The B58 stays bit-identical to `cf43fbb`.

**How this plan was made.**

- **Read-only.** No repository file was created, edited or committed. The tree is clean at HEAD `1787d98`.
- **Nothing was fitted.** No cycle ran on an EPA row, and no model output was compared with EPA data.
- **What I read of the EPA data:**
  - the header structure of the tables;
  - `epa_channels.csv`, with ranges printed for input channels only (speed, MAP, intake and coolant temperature, spark, λ, cam, barometer, cell temperature);
  - `epa_engine.json`, without the two ALPHA curves' values.
- **Two comparisons were run, and neither touched an EPA row or the plant:**
  - turbine-inlet pressure's minimum against the barometer's, printed as a boolean only;
  - the float32 behaviour of the neutral action, in plain NumPy.
- **From the contract JSON** I printed structure and counts, never the `held_out_rows` records.
- **Scratch files** are in `C:\Users\badcl\AppData\Local\Temp\claude\c--Users-badcl-Desktop-GRAD-project\14077827-1e2d-4826-b805-20b70e9c81f2\scratchpad\plan_final\`: `json_keys.py`, `json_more.py`, `json_rows.py` and `channels_compact.txt`.

**Citation keys.**

| key | file |
|---|---|
| MD | `results/ENGINE_THRESHOLDS.md` |
| JSON | `results/ENGINE_THRESHOLDS.json`, cited by key path |
| VD | `results/VALIDATION_DECISIONS.md` |
| VP | `results/VALIDATION_PLAN.md` |
| BI | `results/B58_IDENTITY.md` |
| BIJ | `results/B58_IDENTITY.json` |
| CL | `CLAUDE.md` |
| PHYS | `.claude/rules/physics.md` |
| APP | `.claude/rules/app.md` |
| ch:N | line N of that engine's `data/engines/<id>/epa_channels.csv` |
| H | `tools/harness.py` inside `results/B58_IDENTITY/certificate_tools.tar.gz` (sha256 `a639190b…01503fb`, re-hashed here) |

Values marked **(arith.)** are computed here and must be printed by the test named beside them (mistake 22, CL:120). **(map)** marks a fact taken from the five maps that I did not re-verify. **UNVERIFIED** marks a fact no opened source supports.

---

## 1. Summary

### 1.1 The state, verified

- **The contract is committed.**
  - It was added at `ef5e14e` (2026-10-21 19:26 +0300).
  - Its blobs, JSON `9377b28f…` and MD `8de02aed…`, are identical at HEAD.
  - With CRLF read as LF they hash to JSON `a34a5ed5b4c6427621b038b85b21dade742129c179d48fa6b28e2d563f0eb303` and MD `d126c886c4b14f8fc3adccca711b2e6c311834ab8a33b23ceffa1f54315f5f52`.
  - Nothing under `thresholds/`, `engine_thresholds.py` or `results/ENGINE_THRESHOLDS/` changed after `ef5e14e`.
- **The contract binds now.** JSON `status` reads "binds from its first commit on GRA-test, which must precede calibrate_epa.py", and `calibrate_epa.py` has never existed.
- **Jad's column of decisions 36–38 is open** (VD:170-172). An answer that differs must be applied before the first fit, as a new version written by the generator (MD:1103-1105).
- **Line endings.**
  - `core.autocrlf=true`, and `results/` has no `.gitattributes`. Every text output is therefore hashed with CRLF read as LF (`thresholds/common.py:37-43`).
  - `data/engines/.gitattributes` is `* -text`, so a derived file there is stored byte for byte.

### 1.2 The base design and what is grafted on

- **The base is the physics-first design.** By the critiques' own counts it has the fewest blocking and major issues together: 2 + 8 = 10, against 1 + 10 = 11 for each of the other two. It also has the highest score, 5.5 against 5.
  - If blocking issues are ranked first, contract-literal and risk-first tie (1 blocking, 10 major, score 5).
  - I read the brief's rule as the combined count.
- **Kept from physics-first:**
  - each block of the model is fitted to the channel that measures it;
  - closed-form or profiled stages: VE without a cycle run, FMEP and UA_PORT profiled out of the cycle, cycles cached by the burn and delay values;
  - neutral forms skipped by a branch, not added as 0·x;
  - finite-step controls for switches whose neutral value is zero;
  - the thermal LHV as a field of the thermal record;
  - E6 refits run before any held-out statistic.
- **Grafted from risk-first:**
  - the failure-mode register, as the "can fail" control of every test;
  - the `Engine.__post_init__` invariants and `with_fuel`;
  - the "CARRIED FROM THE B58" marker and its registry test;
  - stage-0 channel checks;
  - the token-gated held-out reader;
  - L9, the contract's own B58 numbers re-made byte for byte;
  - two findings: the held-out run must wait for decision 34's roads, and `--check` dies once build step 2's scripts exist.
- **Grafted from contract-literal:**
  - per-plant DERIVED sets and an in-memory candidate constructor;
  - the requirement-to-function discipline;
  - the K3 knee and the own-coefficients code as importable modules, each tested by reproducing the contract's B58 outputs;
  - `test_contract_pinned.py`;
  - the C3 segment rules;
  - form D run by the ECU, which its critique asked for.

### 1.3 What is built, in order

| WP | what | commit | touches PLANT_CODE |
|---|---|---|---|
| 0 | The team answers decisions 39–68 (section 9), and Jad fills his column of 36–38. Desktop copy of the sheet | VD | no |
| 1 | **Plant commit.** Developed as six sub-steps in the working tree, one change at a time, each with the quick loop and the harness `units` job: P1 fuel per engine; P2 λ clip per engine; P3 forms B and C; P4 form D run by the ECU; P5 records, cars, vehicles and the CVT; P6 the six EPA specs and the three `PLANTS` entries. Landed **as one commit** with the full re-run list and a new B58 certificate | A | **yes** (the last PLANT_CODE edit of this step) |
| 2 | **Contract version 4**, only if decision 39 says so. `engine_thresholds.py --build-only`, then `--check`, then commit. It must come before any file that names the EPA tables, and before `calibrate_epa.py` exists | B | no |
| 3 | **The scripts.** Loader, statistics, fit, freeze, K3, own coefficients, validation, D3 reader and every test, all committed before anything runs on EPA data. Then the structural pre-checks (counts only) and the synthetic-recovery test T0 | C | no |
| 4 | **Run 1.** Calibrate → freeze → E6 refit variants → completion (table, floor, K3 knee, coefficients, probes, frozen-plant dump) → `--check` → worktree reproduction → **freeze commit**, with PHYS's items 1–4 | D | no |
| 5 | **Hand-off, not this step.** Decision 34's roads; the L1 and E8 tightening record `results/EPA_TIGHTENINGS.json` (JSON `order_of_work[2]`) | — | (the roads step's own certificate) |
| 6 | **Run 2.** `validate_epa.py --arm` (commit) → `--run` once per engine → commit → labels and any drop recorded in VD | E, F | no |
| 7 | **Documents.** CHECKPOINT, STATE_HISTORY, READMEs, the mistake-11 sweep | G | no |

Training never runs on this laptop; L8 runs on the training device (VD:155).

### 1.4 Every blocking and major finding, and where it is answered

CL = contract-literal, RF = risk-first, PF = physics-first; "B" marks a blocking finding.

| # | finding | disposition | where |
|---|---|---|---|
| CL-B | Form D computed in the plant is not the contract's D, which is "run by the ECU" (MD:473-474) | **Adopted.** `BaselineECU.cam_deg()`, a separate method so that `step()`'s 3-tuple is unchanged; scheduled on `map_b_prev` in the environment, at the row's MAP in E rows, D1 and E8; fed to `run_cycle` through a keyword | WP1-P4, §3, §5 |
| CL-1, RF-4, PF-2 | The same-commit re-run rules are broken by per-hook commits | **Adopted.** Hooks are developed separately but land as one commit carrying the full list; PHYS's items 1–4 also run at the freeze commit | WP1, WP4, §3.6 |
| CL-2, RF-5 | The certificate goes stale when `engines.py` (`PLANTS`) changes after it | **Adopted.** Every PLANT_CODE edit, the registration included, is in commit A, before the certificate. The re-run list gains `test_wide_air`, `random_road.py`, `new_drive.py` without the derived file, `test_epa_map` with `GRAD_EXTRA_DATA`, and each script this step edits | §3.6 |
| CL-3 | The run-once guard checks only that `rows.json` exists | **Adopted.** A committed ARMED record; counts-only printing; atomic per-engine writes; a re-execution allowed only on armed code with nothing written, otherwise the coding-defect route | §6.1, decision 59 |
| CL-4 | A held-out fired row without λ cannot run | **Adopted:** a pre-declared rule (decision 54) plus a structural count. **The reviewer's inference is not quite right:** "fired 21 vs 20" does not prove a λ-less row, because `l1_boost` does not require fired (`thresholds/split.py:124`), and between-band rows and non-hot enriched rows fall in neither count | §4.4 |
| CL-5 | The CVT's C5 fails by construction under the economy-line law | **Adopted** as decision 39(c) and 40: either version 4 replaces C5's CVT clause, or a kickdown law with a reserve keeps C5 literal | §7.4 |
| CL-6 | D3 data would enter the plant | **Adopted.** The gearbox constants are ASSUMED (the Supra's form and values); the CVT law's parameters are ASSUMED or DESIGN, not the strand's fitted values | §7, decision 43 |
| CL-7, PF-4 | Nothing checks the locked climb is delivered before K3; rpm may run outside the maps | **Adopted.** `rpm_max` is the top calibration line; a tracking check on the neutral trace runs before the knee; pre-declared consequence (decision 44) | §7.6 |
| CL-8 | The back-pressure floor is fitted to a channel that reads below the barometer | **Partly adopted.** I verified, as a boolean, that turbine-inlet pressure's minimum lies below the barometer's in the Mazda, Honda and Ford Cell 9 steady tables (ch:19/6, 21/6, 17/6), not in the Final tables. Rule: keep every row, report the count and size, run a reported refit without those rows. **Rejected:** excluding rows on the outcome channel (it selects on the variable being fitted), and a barometer-referenced floor, which changes "the back-pressure law" that MD:461-463 fixes (plant.py:334), so it would need version 4 | §5.2 S1, decision 52 |
| CL-9 | The Honda's λ minimum may be a sensor floor | **Adopted.** Stage-0 count of Final calibration rows at the table minimum; one-sided (censored) treatment in the enrichment fit; flagged in E4a and E4b | §5.2 S0, S3b |
| CL-10, PF-6 | Nine stage-3 constants and the ECU constants may be unidentifiable | **Adopted, without holds:** profiled separable stages, a weak declared ridge toward the B58's values, rows behind each constant printed, profile flatness reported, synthetic recovery at the real inputs. **Rejected:** "refuse below a count", which would force a procedure change after a fit (RF-1's own point) | §5, decision 50 |
| RF-B | The neutral action is not bit-exact (the trims are float32) | **Verified and adopted.** `lam_b + act[1]` with `act` float32 rounds to float32 under NumPy 2.5.3 (0.81 → 0.8100000023841858); the contract's own B58 trace is float32 (`k3_nominal.json` `base_spark_median_400_718 = 1.1640795469284058`, which is float32-exact). The identity is defined at that representation, with no clip binding; `engine_env.py:1004-1006` is X1's and untouched | §3.4, decision 39(b) |
| RF-1 | Rule 0 breaks on the failure path | **Adopted.** No fit outcome stops the run. Bound hits, non-convergence and clip contacts have pre-declared outcomes and flags; only coding defects stop | §5.6 |
| RF-2 | The freeze checks cannot run in a copy without `.git` | **Adopted.** `--check` recomputes in memory in the main tree; the reproduction runs in a `git worktree`; the poison test bypasses the table hash by monkeypatching inside the test | §4.6, §5.9 |
| RF-3, PF-B2 | "Frozen" covers the constants, not the code; the validation's plant_sha guard cannot hold | **Adopted.** The validation is guarded by a frozen-plant dump (synthetic grid, bit-exact), engine_sha, derived_sha, the spec hashes and a byte-identical re-run of the in-sample stage; never by plant_sha | §5.8, §6.1 |
| RF-6 | The resolution term collapses because `epa_map.py` writes `repr()` | **Adopted.** Per-channel resolution is declared from EPA's instrument pages (opened before the fit), or else from the steady tables' printed resolution, marked unsourced (decision 56) | §6.2 |
| RF-7 | E8's λ convention differs from the ECU fit's | **Adopted:** the ECU λ is fitted in E8's convention. Plus decision 39(a), because no cycle form can move E8 | §5.2 S3b |
| RF-8 | Median KI = 1 leaves the knock feedback live | **Partly adopted:** the estimator is declared (decision 51); the knock-flag duty is reported on the climb and during the table measurement. **Rejected:** a post-freeze gate that could only be passed by changing the model after a fit (MD:42-44). The B58 behaves the same way: its knock-limited surface is the model's own (`b58.toml:100`), and its knock term is 2.45 of 848.05 damage units (`k3_nominal.json`) | §5.2 S6 |
| RF-9 | E6 row 2 cannot be bit-equal after a refit | **Adopted.** "Must not move" means \|ΔE\| < u_val (MD:737-738's criterion), and a miss is reported | §6.4 |
| RF-10 | Parameters held at B58 values escape the CARRIED registry | **Moot:** nothing is held | §5 |
| PF-B1 | Holding burn_rpm or delay_rpm changes form A's fitted set (MD:461-463; `thresholds/contract.py:617`) | **Adopted:** all named constants are fitted, with a ridge | §5.2 S4 |
| PF-1 | E6 row 1 is redefined | **Adopted:** row 1 changes the offset only (snap kept); row 12 changes the snap only, with no refit | §5.7 |
| PF-3 | The CVT law has an empty interval at low speed | **Adopted:** a declared low-speed branch | §7.3 |
| PF-5 | The running maximum extrapolates boost | **Adopted:** the measured, non-monotone envelope, referenced to the in-use inlet | §5.2 S3c |
| PF-7 | T0 on a synthetic grid proves nothing | **Adopted:** T0 at the calibration rows' own inputs, judged by χ² over seeds | §5.10 |
| PF-8 | The version-4 route is blocked by the generator | **Adopted:** version 4 comes after commit A and before any file that names the tables; table names come from the JSON | WP2 |

---

## 2. Ordered work packages

`PY=/c/Users/badcl/Desktop/GRAD-project/.venv/Scripts/python.exe` (Python 3.13.2, BI:38-42), run from Git Bash with `export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1` (BI:43-44). `S` is the certificate archive unpacked in scratch: `tar -xzf results/B58_IDENTITY/certificate_tools.tar.gz -C $S`, never over the tree (mistake 16, CL:114).

### WP0: decisions, before any code is committed

- **Files:** `results/VALIDATION_DECISIONS.md`, a new section H with a Ghassan column and a Jad column per decision (the decision-sheet rule), and a Desktop copy.
- **What must be in before which commit:**
  - Jad's column of 36–38 (VD:170-172) and decisions 39–48 before commit A.
  - Decisions 49–64 before commit C.
  - Decisions 65–68 before the roads step and the arm commit.
- **Test:** none; a person checks that both columns are filled.

### WP1: the plant commit (commit A). Touches PLANT_CODE: yes

The sub-steps are applied one at a time (CL:141-142). After each: the quick loop of §3.6 and the harness `units` job against `cf43fbb`, bit-identical, with what happened written down. They land together with the full list (CL:137-140, PHYS:18-29).

**P1. The fuel is the engine's.**

- `engines.py`:
  - new `@_required @dataclass(frozen=True) class Fuel: lhv_j_per_kg: float; afr_st: float`;
  - `Engine.fuel` and `TypedEngine.fuel` (`engines.py:298-331`);
  - `ThermalParams.fuel_lhv_j_per_kg` (`:239-265`), copied by `_build` from `[fuel]`; `_build` refuses it if it is typed in `[thermal]`;
  - `Engine.__post_init__` raises unless `thermal.fuel_lhv_j_per_kg == fuel.lhv_j_per_kg`;
  - `with_fuel(engine, fuel)` makes both replacements in one `dataclasses.replace`. It is the only way to vary the fuel, which E6 row 3 needs ("plant.py:42 **and** thermal.py:245 together", MD:755).
- `plant.py`:
  - delete `LHV` and `AFR_STOICH` (`:42-43`); keep `R_AIR`, `H_FG` and `CP_AIR` with a comment that they are shared physics (mistake 1);
  - `:163` becomes `m_fuel = m_air / (engine.fuel.afr_st * op.lam)`;
  - `:176` becomes `q_total = min(m_fuel, m_air / engine.fuel.afr_st) * engine.fuel.lhv_j_per_kg * eta_comb`.
- `thermal.py:245` becomes `q_fuel = mdot_fuel_gps * 1e-3 * p.fuel_lhv_j_per_kg`. **`ThermalNetwork(p)` keeps its signature**, so the ten constructor calls are untouched: `engine_env.py:738-739`, `app/estimator.py:234-236`, `car_thermal.py:162`, `validate.py:158`, `thermal.py:281`, `test_plant_guards.py:70`, the lab's `server.py:205` and two tests, and H:165.
- `car_thermal.py:124-129`: `measured_fuel_gps(air_gps, lam, rpm, *, afr_st)`. Callers pass `engines.typed_engine("b58").fuel.afr_st`: `car_thermal.py:153`, `calibrate_thermal.py:154` and `model_vs_data.py:376`.
- `make_page.py:1325` reads the B58's record; `make_page.py:1413`'s source pin becomes `"return air / (afr_st * lam)"`.
- `engine_specs/b58.toml` gains `[fuel]`: `lhv_j_per_kg = 44.0e6` and `afr_st = 14.7`, both ASSUMED, with source "plant.py:42/43 on cf43fbb; REFERENCES.md:433 (fuel properties CANNOT)".
- **B58-only literals left as they are**, each pinned to the B58 record by `test_fuel_forms.py`: `calibrate_thermal.py:163, 171`; `substep_fit_check.py:41, 49`; `model_vs_data.py:399`; `validate.py:164`; `verify_docs.py:2075`.

**P2. The policies' λ clip is the engine's.**

- `EcuCal` gains `lam_floor` and `lam_ceiling` (`engines.py:204-236`).
- `Engine.__post_init__` also requires `1.0 - ecu.enr_depth >= ecu.lam_floor` and `ecu.lam_ceiling >= 1.0`, so the neutral λ can never be clipped (`engine_env.py:341-347`; MD:789-797).
- `engine_env.py:1006` becomes `float(np.clip(lam_b + act[1], eng.ecu.lam_floor, eng.ecu.lam_ceiling))`.
- `b58.toml [ecu]`: 0.70 and 1.25, DESIGN ("the literal of engine_env.py:1006").

**P3. Forms B and C.**

- `CycleCal` gains `form` (str), `ve_map`, `ve_map_ref_kpa` and `ce_rich_slope` (`engines.py:141-183`).
- `CycleCal.__post_init__` refuses:
  - an unknown form;
  - `ve_map != 0` without B;
  - `ce_rich_slope != SHARED_RICH_SLOPE` (0.65, the shared value of MD:464; `plant.py:59`) without C.
- `plant.py:54-60` becomes `combustion_efficiency(lam, *, engine)`. The rich branch is `1.0 - engine.cycle.ce_rich_slope * (1.0 - lam)`; the lean branch is unchanged; it is called at `:175`.
- `plant.py:63-66` becomes `volumetric_efficiency(rpm, map_kpa, cam_deg, *, engine)`:
  - form `"A"` returns **the old one-line expression verbatim**;
  - any other form computes `v = base + amp·exp(…)`, adds `+ ve_map·(map_kpa − ve_map_ref_kpa)` if B and `+ ve_cam·(cam_deg − cam_ref_deg)` if D, then clips;
  - it refuses `map_kpa is None` under B and `cam_deg is None` under D.
- `plant.py:160` passes `op.map_kpa, cam_deg`.
- `plant.py:520-544`: `map_from_airflow` refuses a form other than A, then calls `volumetric_efficiency(rpm, None, None, engine=engine)`. It has no EPA caller.
- `b58.toml [cycle]`:
  - `form = "A"`, DESIGN (decision 31, VD:154);
  - `ve_map = 0.0` and `ve_map_ref_kpa = 100.0`, DESIGN;
  - `ce_rich_slope = 0.65`, ASSUMED ("plant.py:59 on cf43fbb; no source").

**P4. Form D, run by the ECU (decision 41).**

- `CycleCal` gains `ve_cam` and `cam_ref_deg`.
- `EcuCal` gains:
  - `cam_on` (0 or 1);
  - six coefficients `cam_c0, cam_c_rpm, cam_c_map, cam_c_rpm2, cam_c_rpm_map, cam_c_map2` (scalars, so `_derived_value` needs no tuple case);
  - the input domain `cam_rpm_lo, cam_rpm_hi, cam_map_lo, cam_map_hi` and the output clamp `cam_lo, cam_hi`.
- `Engine.__post_init__` requires `ecu.cam_on == ("D" in cycle.form)`.
- `engine_env.BaselineECU.cam_deg(rpm, map_kpa)` returns `None` when `cam_on == 0`. Otherwise it clamps the inputs to the domain, evaluates the quadratic in (rpm/1000, MAP/100) and clamps the output.
- `plant.run_cycle(op, *, engine, dtheta=DTHETA_DEG, cam_deg=None)` and `predict(…, p_exh_kpa=None, cam_deg=None, *, engine)` pass the cam to VE. VE refuses a number for a non-D engine and `None` for a D engine.
- `engine_env.step()`:
  - `cam_b = self.ecu.cam_deg(self.rpm, self.map_b_prev)` (beside `:982`);
  - `self._track_torque(…, state, cam_deg=cam_b)` for both the baseline and the agent (`:985`, `:1007`), so every policy inherits the ECU's cam as it inherits its spark (MD:690-694);
  - `_track_torque(self, …, boost_trim, state, *, cam_deg=None)` → `_evaluate(…, *, cam_deg=None)`, which refuses a surrogate when a cam is given.
- `measure_deliverable_torque` (`:1094-1097`) passes `ecu.cam_deg(rpm, mp_prev)`.
- The cam is passed **by keyword**, so these keep working: the lab's `CapturingEnv._track_torque(*args, **kwargs)` (its `args[7]` test at `Explanatory Simulation/backend/simulation.py:154-158`), `wide_air.py:149, 182`, `compare_calibration.py:141`, and `b58_propagation`'s `ev(self, *a, **k)` patch (`thresholds/b58_propagation.py:53-55`).
- `test_engine_threading.py:102-114` `PLANTS_OWN_IF_NONE` gains `"cam_deg": "no cam input: an engine whose form has no D; a form-D engine refuses None"`.
- `b58.toml`: `ve_cam = 0.0`, `cam_ref_deg = 0.0`, `cam_on = 0` and the twelve schedule fields at 0.0, all DESIGN.

**P5. Records, constructors, cars, vehicles and guards.**

- `engines.py`:
  - `DERIVED_FIELDS` stays as it is: it is the B58's map, read at `test_engine_threading.py:711` and `substep_fit_check.py:100`.
  - New `EPA_DERIVED_FIELDS` (§5.8) and `DERIVED_BY_SET = {"b58": DERIVED_FIELDS, "epa": EPA_DERIVED_FIELDS}`, chosen by the engine spec's top-level `derived_set`.
  - `_record(cls, record, typed, source, derived_map, converted)`: a field comes from exactly one of typed, DERIVED or converted. `source` is the derived file's path, or an in-memory dict for a candidate.
  - `_derived_value` converts by field type: `str` for `form`, `int` for `cam_on`, float tuples for the envelope, `(int, float)` pairs for the table, `float` otherwise. **The B58's conversions are unchanged.**
  - `build_candidate(name, values)` builds an uncached, unregistered Plant from the specs plus an in-memory DERIVED dict. Calibration uses it, so it evaluates exactly what `engines.get` will later build from the file (mistake 10).
  - `published_car(path, kind)` converts `engine_specs/cars/<car>.toml` with exact factors (`engine_specs/cars/README.md:82-98`).
  - New records `EpaCar` (stepped box, three-term road load) and `CvtCar` (§7.1). `Car` (`:334-371`) is unchanged.
  - `_build` picks the car record by the car spec's `kind`. For an EPA plant it also checks the derived file's frozen sections against the freeze record named by the engine spec's `freeze` key (§5.8).
  - `trainable()` returns `("b58",)`.
- `engine_env.py`:
  - `vehicle_for(car)` returns `Vehicle(car)` for a `Car`, `EpaVehicle` for an `EpaCar` and `CvtVehicle` for a `CvtCar` (§7.2–7.3);
  - `:736` uses it;
  - the training-road builders `min_tractive_force`, `grade_floor` and `extreme_speed_profile` (`:1499-1551`, which read `veh.cd_a`, `crr` and `gears`) raise an explicit `TypeError` for a non-`Car`;
  - so does `wide_air.ThinAirVehicle` (`wide_air.py:211`).
- `derived.py:49-52`: `_maker` names `python calibrate_epa.py --engine <id>` for `data/engines/<id>/`.
- `fingerprint.py:439` refuses a `CvtCar` with "schema 4 records a transmission" (CHECKPOINT.md:113-114) instead of an `AttributeError`.
- `train.py:485`, `train_all.py:94`, `run_phase_d.py:247` and `evaluate.py:422` use `choices=engines.trainable()` (decision 47).
- `b58.toml` gains the top-level `derived_set = "b58"`; `a90_supra.toml` gains `kind = "two_term_stepped"` (DESIGN, decision 31).
- **The drift anchors are text and stay intact:** `"turb_knee_k = { value = 1123.0,"`, `"v_kmh = { value = 130.0,"`, `"1.000, 0.822, 0.640]"`, `"DTHETA_DEG = 0.25"` and `"12 % at 130 km/h, 42 C"` (`drift_test.py:42, 64-69, 98-99`).

**P6. The six EPA specs and the registration.**

- New files: `engine_specs/mazda_25t.toml`, `honda_l15b7.toml`, `ford_27tt.toml`, `cx9_2016.toml`, `accord_2018.toml`, `f150_2015.toml`. They hold typed values only (§7.5 and §9.2) and never a DERIVED one (`engines.py:421-423`). The cars stay out of `engine_specs/cars/`, which must hold exactly four files (`test_epa_map.py:445-447`).
- `engines.PLANTS` gains `mazda_25t: ("mazda_25t","cx9_2016")`, `honda_l15b7: ("honda_l15b7","accord_2018")` and `ford_27tt: ("ford_27tt","f150_2015")`.
- `engines.py`'s `__main__` (`:599-602`) prints "not calibrated yet (no data/engines/<id>/derived_params.json)" for a registered plant without its file, instead of stopping (`derived.py:58-64`).
- Every test that iterates the registry skips such a plant explicitly.

**Tests that prove WP1** (each with a control that must fail, mistake 12):

- `test_fuel_forms.py`:
  - the B58's fuel is exactly 44.0e6 and 14.7;
  - an AST check finds no fuel literal or module name in `run_cycle` or `_substep`;
  - `with_fuel` moves both copies;
  - a divergent `replace` raises;
  - one ulp on `afr_st` moves the fuel flow;
  - one ulp on the thermal record's LHV, built directly as a `ThermalParams`, moves the network;
  - forms A+B, A+B+C and A+B+C+D at neutral values give form A's doubles (`tobytes()`) on H's units grid and on one episode;
  - finite steps off neutral (`ve_map = 1e-4`, `ve_cam = 1e-4`, `ce_rich_slope` at λ 0.95, where the units grid's 0.70 and 0.85 do not see one ulp (H:126, :139)) come out DIFFERENT;
  - **engine_sha computed over the pre-step-2 field set equals `99d2a9658b1258a7`** (BI:33; `engines.py:591-596`).
- `test_cars.py`: C1 and C2 (§7.4); the CVT law, including v = 0 and the launch; the Supra's `Vehicle` and `Car` unchanged.
- `test_carried.py`: §9.2.
- `test_engine_threading.py`:
  - CALLS gains `combustion_efficiency` (kw engine), `vehicle_for`, `EpaVehicle` and `CvtVehicle` (positional or keyword `car`) and `with_fuel`;
  - Signatures gains `(P.combustion_efficiency, "engine")` and `(P.volumetric_efficiency, "map_kpa")`;
  - the record list (`:680-686`) gains the new records;
  - Registry runs per plant through `DERIVED_BY_SET`;
  - the `_record` call at `:815` takes the new arguments;
  - the `typed_engine` comparison (`:808`) includes `fuel`;
  - one scan control per new rule, in the `:485-542` pattern.
  - `ThermalNetwork(None)` (`:664`) stays a valid control, because the signature is unchanged.
- `test_plant_guards.py:101-134`: `DerivedFingerprint` per registered plant that has a file.

**Commands:** §3.6. **Touches the plant:** yes. This is the only PLANT_CODE edit of the step, so the certificate describes the final tree.

### WP2: contract version 4 (commit B; conditional on decision 39)

- **Files:** `thresholds/document_template.md` and `thresholds/contract.py` (the rule texts of §9.1, decision 39); `results/ENGINE_THRESHOLDS.json` and `.md`, written by the generator.
- **Commands:**
  ```bash
  $PY engine_thresholds.py --build-only   # steps 6-7 from the saved outputs (MD:1186-1187)
  $PY engine_thresholds.py --check        # exit 0
  ```
- **Why it must be here:**
  - Step 7 stops once `calibrate_epa.py` exists, or once a `.py` other than `epa_map.py`, `test_epa_map.py` and the generator contains `epa_steady` or `epa_highload` (`thresholds/document.py:489-492, 525-531`). It counts untracked files (`:169-180`).
  - WP1 creates no such file: the specs are `.toml`, and no WP1 code names the tables.
- **Test:** `--check` exits 0; a short review, as versions 2 and 3 had; `git merge-base --is-ancestor <v4> HEAD`.
- **Touches the plant:** no. The step outputs in `results/ENGINE_THRESHOLDS/` do not move.

### WP3: the scripts (commit C). Touches PLANT_CODE: no

- **New modules:**
  - `epa_rows.py`: §4;
  - `epa_stats.py`: every statistic, one definition for the in-sample stage and the held-out run (MD:478-479; mistake 10);
  - `epa_fit.py`: §5;
  - `epa_freeze.py`: hashes, the freeze record, the token, the frozen-plant dump;
  - `calibrate_epa.py`: the entry point, JSON `order_of_work[1]`;
  - `k3_knee.py`: `baseline_trace(plant)` and `knee_for(trace, seconds)`, lifted from `thresholds/ecu_shift.py:80-97`, which stays untouched because it is hash-pinned in JSON `generators`;
  - `epa_coefficients.py`: `thresholds/b58_propagation.py:43-155` made a function of any plant;
  - `validate_epa.py`: §6;
  - `d3_rows.py`: C3 and C4.
- **No new `.py` contains the strings `epa_steady` or `epa_highload`.** Table names come from JSON `engines.<id>.tables` and `epa_tables_sha256`. This keeps the generator's table-naming claim true, so only "calibrate_epa.py does not exist" stops `--check` from here on.
- **New tests:**
  - `test_contract_pinned.py` (§8.4);
  - `test_epa_rows.py` (§4.6);
  - `test_epa_stats.py`: synthetic rows with hand answers; every label branch; L0 and L1's closed forms against a 10 001-point grid; the contract's own 5.183 K from (3.317, 0.01353) (JSON `propagation_b58.used`); E8's P equal to `thresholds.contract.interp`;
  - `test_epa_fit.py`: stages on synthetic rows; two runs byte-identical; every shortcut equal to `run_cycle` within 1e-9;
  - `test_epa_freeze.py`: every refusal shown, and shown to pass once its cause is removed;
  - `test_k3_knee.py`: §7.7;
  - `test_epa_coefficients.py`: pointed at the B58, it reproduces `results/ENGINE_THRESHOLDS/b58_propagation.json`'s values bit for bit;
  - `test_validate_guards.py`: §6.1.
- **Run before the commit:**
  - `test_engine_threading.py`, which scans the new code;
  - `verify_docs.py`, which scans every new `.py`. Avoid the retired pattern `n_cyl\s*=\s*4\b` (`verify_docs.py:746`) and the sign-carrying `[-−]0\.60|[-−]0\.52|[-−]0\.38` (`:710`).
  - the structural pre-checks of §4.4, counts only;
  - **T0** (§5.10). It reads calibration inputs only and no EPA output, and runs after the contract version is final.
- **Touches the plant:** no.

### WP4: Run 1 and the freeze commit (commit D)

- **Commands:**
  ```bash
  for e in mazda_25t honda_l15b7 ford_27tt; do $PY -B calibrate_epa.py fit --engine $e --jobs 16; done  # ladder over all three (decision 49)
  for e in mazda_25t honda_l15b7 ford_27tt; do $PY -B calibrate_epa.py e6 --engine $e --jobs 16; done
  for e in mazda_25t honda_l15b7 ford_27tt; do $PY -B calibrate_epa.py complete --engine $e --jobs 16; done   # fresh process, DERIVING_PARAMS=1
  for e in mazda_25t honda_l15b7 ford_27tt; do $PY -B calibrate_epa.py check --engine $e; done   # in-memory recompute, byte compare
  git worktree add $S/repro HEAD && (cd $S/repro && <the same commands>) && cmp ...      # reproduction with .git present
  $PY -B test_epa_rows.py -k poison && $PY -B test_epa_plants.py && $PY -B test_engine_threading.py && $PY -B test_plant_guards.py
  ```
- **Freeze commit contents:** `data/engines/<id>/derived_params.json`, `results/EPA_CALIBRATION/<id>/*`.
- **Re-runs at this commit:** PHYS's items 1–4 (`data/**` is a PHYS path, PHYS:2-10, :18-29), the app suites, and `verify_docs.py`.
  - The B58's plant_sha, derived_sha and engine_sha must print unchanged (`fingerprint.py --engine b58`), so every B58 output must equal commit A's.
  - A waiver instead is decision 48.
- **Touches the plant:** no PLANT_CODE. It does change `data/**` and adds the three plants' values.

### WP5: hand-off (not this step)

- Decision 34's roads, drawn on the frozen plants with a committed script.
- On them, before any held-out statistic: the preview pair's knee-shift slope (L1's tightening, MD:726-728) and the B58 ECU shifts re-run (E8's tightening, MD:780-781).
- These are committed as `results/EPA_TIGHTENINGS.json`, whose schema `validate_epa.py` fixes now: `roads_sha`; `L1.slope_points_per_K` with set, shift and damage reading; `E8.k3_pair_change_vs_lambda_roads` and `E8.k3_pair_change_vs_spark_roads` in the format of JSON `ecu_strategy_b58`; the provenance hashes.
- C5 is applied at 1.9 % (decision 64).
- The roads step changes `engine_env.py`, so it needs its own B58 certificate.

### WP6: Run 2, the held-out validation (commits E and F)

- **Commands:** `$PY -B validate_epa.py arm --engine <id>` (all guards; writes `ARMED.json`), then commit E ("armed"), then `$PY -B validate_epa.py run --engine <id> --jobs 16`, then commit F (outputs), then a person records labels, the section 7 consequences and any drop in VD, with date and row (MD:1047-1049). §6 has the detail.

### WP7: documents (commit G)

§8.5.

---

## 3. The B58's identity, and the exact re-run list

### 3.1 The interfaces that do not change

These are what the contract's generator and the certificate harness call, so both run unedited:

- **`plant.Operating`'s seven fields.** All are required (`plant.py:95-103`). `thresholds/b58_propagation.py:44-46` builds it with exactly these, and H builds it with `**kw`.
- **`run_cycle(op, *, engine, dtheta)`**. The only addition is an optional keyword `cam_deg=None`.
- **`map_from_airflow(m, rpm, t, *, engine)`**, as H calls it.
- **`ThermalNetwork(p)`** (H:165), **`BaselineECU(cal, enrichment_map=…)`**, **`step()`'s six arguments and its 3-tuple** (`engine_env.py:356-376`), which `thresholds/ecu_shift.py:70-78` patches.
- **`Vehicle(car)`**, **`demand(v, a, grade, *, rho)`**, **`shift_ceiling_nm`** and **`DELIVERABLE_TORQUE`** (H, the units job).
- **`SupervisoryTunerEnv._evaluate`**, patched by `ev(self, *a, **k)` (`thresholds/b58_propagation.py:53-55`). The new keyword passes through.

### 3.2 Why every B58 double is the same

**The argument common to every edit:**

1. **The same doubles go in.** TOML parses a decimal with Python's correctly rounded `float()`. Checked: `44.0e6`, `14.7`, `0.65`, `0.70`, `1.25` and `42.908e6` read from TOML equal the literals; `44.0e6*1e-3 == 44.0e3`.
2. **The same operations run in the same order.** Python evaluates `a*b*c` as `(a*b)*c`. Replacing a literal by an attribute holding the same double performs no arithmetic.
3. **The same branch runs.** The B58's tag is `"A"`, and every new term sits behind a branch that tag does not take.

| site on `cf43fbb` | after | why the bits are the same |
|---|---|---|
| `plant.py:163` `m_air / (AFR_STOICH * op.lam)` | `m_air / (engine.fuel.afr_st * op.lam)` | same operands, same order |
| `plant.py:176` `min(m_fuel, m_air / AFR_STOICH) * LHV * eta_comb` | `min(…, m_air / engine.fuel.afr_st) * engine.fuel.lhv_j_per_kg * eta_comb` | same order |
| `thermal.py:245` `mdot_fuel_gps * 1e-3 * 44.0e6` | `mdot_fuel_gps * 1e-3 * p.fuel_lhv_j_per_kg` | still (ṁ·1e-3)·LHV. Never fold it into ṁ·44.0e3: the plant map measured that change on 56 780 of 200 000 values (map) |
| `plant.py:59` `1.0 - 0.65 * (1.0 - lam)` | `1.0 - engine.cycle.ce_rich_slope * (1.0 - lam)` | 0.65 typed |
| `plant.py:66` one expression | form `"A"`: **the same expression returned verbatim** | branch not taken. With a finite MAP, even form "A+B" at `ve_map = 0` adds an exact 0.0. The branch matters for a NaN MAP, where `eta_v` (an output, `plant.py:311`) would otherwise become NaN |
| `plant.py:535` VE once, before the loop | form check, then `volumetric_efficiency(rpm, None, None, engine=…)` | the A path |
| `engine_env.py:982-1007` | `cam_b = self.ecu.cam_deg(…)` → `None`; passed as a keyword down to `run_cycle` | no arithmetic |
| `engine_env.py:1006` `np.clip(lam_b + act[1], 0.70, 1.25)` | `np.clip(lam_b + act[1], eng.ecu.lam_floor, eng.ecu.lam_ceiling)` | 0.70 and 1.25 typed; under NumPy 2 (NEP 50) Python-float bounds are weak in either form |
| `engine_env.py:736` `Vehicle(plant.car)` | `vehicle_for(plant.car)` → `Vehicle(car)` for a `Car` | the same object |
| `car_thermal.py:129` `air / (AFR_STOICH * lam)` | `air / (afr_st * lam)`, with the B58's 14.7 passed | the thermal fit's inputs are unchanged, so derived_sha `326c0835548975e2` reproduces |
| `engines._derived_value` | dispatch by type, with the B58's branches unchanged | the same conversions |

### 3.3 What may move, and what may not (BI:36)

- **May move:**
  - `plant_sha` and `plant_text_sha`, because `fingerprint.py:109` hashes code;
  - `engine_sha`, because the records gain fields (`engines.py:591-596`);
  - the lab's pin (`Explanatory Simulation/tests/test_catalog.py:97`);
  - the printed lines BI section 5 lists.
- **Must not move:**
  - any computed value;
  - derived_sha `326c0835548975e2`, because `data/derived_params.json` is untouched;
  - `episodes_sha`, the gears, the final drive, the crank step, the knees, the scenario.
- **New check:** engine_sha with the added keys stripped from `asdict` equals `99d2a9658b1258a7`.

### 3.4 The neutral action and float32 (RF-B, verified)

- **How the action reaches the engine.** `act` is float32: `ACT_LO` and `ACT_HI` are float32 (`engine_env.py:698-699`), and the action is rescaled and clipped as float32 (`:939-950`). The neutral trims come out exactly `0.0`; I checked this in NumPy 2.5.3.
- **What NumPy 2 does with them.** `sp_b + act[0]` and `lam_b + act[1]` are float32 (NEP 50), so the neutral agent's λ is `float(np.float32(lam_b))`. Examples: 0.81 → 0.8100000023841858, and 1.0 → 1.0.
- **The baseline car is not rounded.** It takes `sp_b` and `lam_b` in float64 (`:985-987`). This is X1's environment, and the B58 must keep it, so `:1004-1006` is not touched.
- **The contract's own B58 numbers come through this path.** `k3_nominal.json` `base_spark_median_400_718 = 1.1640795469284058` is float32-exact: it is the agent's `info["spark"]` (`:1059`) under the neutral action (`thresholds/ecu_shift.py:80-91`).
- **The identity is therefore defined as** (decision 39(b)):
  - the neutral trims are exactly 0.0;
  - at every step, the agent's λ equals `float(np.float32(lam_b))` and its spark equals `float(np.float32(sp_b))`;
  - no clip binds.
- **No clip can bind.** Rounding is monotone, and the clip compares in float32, so `lam_b ≥ lam_floor` implies `float32(lam_b) ≥ float32(lam_floor)`. The `Engine` invariant guarantees `lam_b ≥ lam_floor`. `sp_b` is already clipped by `step()` (`:375`).

### 3.5 The certificate's new controls (mistake 12)

| control | expected | how |
|---|---|---|
| one ulp on `fuel.afr_st`, `ecu.lam_floor` | DIFFERENT | H's generic `HARNESS_PERTURB` (H:36-55). `lam_floor` binds in the extremes jobs' random λ trims |
| one ulp on `fuel.lhv_j_per_kg`, through `with_fuel` | DIFFERENT | **a recorded candidate-side harness edit**: the generic `replace` would trip the invariant |
| `cycle.form="A+B"` with `ve_map=0`; A+B+C at 0.65; A+B+C+D with zeros | IDENTICAL | a recorded value-setting mode (`HARNESS_SET`) |
| `ve_map=1e-4`, `ve_cam=1e-4` (with the ECU cam on) | DIFFERENT | the same mode. One ulp above zero (5e-324) changes no double |
| existing `thermal.c_turb`, `car.mass` | DIFFERENT | unchanged |

### 3.6 The re-run list, with commands

**Quick loop, after each sub-step P1–P6** (Git Bash, `REPO=/c/Users/badcl/Desktop/GRAD-project`):

```bash
$PY -B test_engine_threading.py            # alone: it creates _scan_probe_*.py (test_engine_threading.py:560-570)
$PY -B test_plant_guards.py; $PY -B test_fuel_forms.py; $PY -B test_cars.py
$PY -B fingerprint.py --engine b58; $PY -B engines.py
# once: mkdir -p $S/ref && git archive --format=tar cf43fbb | tar -x -C $S/ref
#       $PY -I $S/tools/run_jobs.py $S/ref ref $S/tools/jobs_all.txt 3
echo units > $S/tools/jobs_units.txt
$PY -I $S/tools/run_jobs.py $REPO cand_P<n> $S/tools/jobs_units.txt 1 && bash $S/tools/compare_all.sh ref cand_P<n>
```

The units job takes about a minute (map).

**Full list, once, before commit A.** Every command is BI:208-255's, run as it says. Writers run in copies made with `$PY -I $S/tools/copy_tree.py $REPO $S/cand`.

| # | run | rule | time measured on 21 Oct |
|---|---|---|---|
| 1 | L1–L3 harness, 34 jobs: `run_jobs.py $REPO cand jobs_all.txt 6`; `compare_all.sh ref cand` | BI:218 | 1970 s (map) |
| 2 | controls: existing (BI:220) and new (§3.5); `compare_all.sh` | mistake 12 | ~1070 s (map) |
| 3 | `CAND=$S/cand bash run_writer.sh cand premise results/premise.json check_premise.py`; `premise.json` unchanged | PHYS:20; BI:77 | 1230 s (BIJ:1498) |
| 4 | `run_l4.sh cand` and `--road random`; **output pasted into commit A's message** | CL:139-140 | 1529 s and 1930 s (BIJ:1514, :1526) |
| 5 | `run_roads_review.sh`: `check_roads.py` extremes and wideair, the 40 terrain roads, `check_random_road.py` | PHYS:20; BI:79, 88-89 | 996, 1296, 608, 2777 s (BIJ:1538, 1552, 2130, 2172) |
| 6 | `$PY validate.py` in both trees, compared with `cmp`. `validation_table.md` is updated only if the output moves; it must not | CL:137-138 | 51 s (map) |
| 7 | `run_writer.sh cand generality results/generality.json generality_test.py` | BI:82 | 3329 s (BIJ:1597) |
| 8 | `derive_params.py` in `$S/candd` plus `derived_check.py` → derived_sha `326c0835548975e2` (the thermal fit now goes through `measured_fuel_gps(afr_st=)`) | BI:81 | ~2 min |
| 9 | `bd_dump.py` (build_dataset with no derived file), and `new_drive.py` on pull01 with the derived file moved aside | BI:87, 234 | — |
| 10 | `evaluate.py --engine b58 --protocol d2`, compared with `l7_diff.py` | BI:90 | — |
| 11 | app: `run_app.sh`, `run_app_extra.sh`, `node --test "static/sim/*.test.mjs"`; `app.test_results` again **after** the commit (BI:190-191) | CL:145-152; APP:13-24 | ~40 min |
| 12 | lab: `npm ci`, `npm run build`, `$PY -m unittest discover -s tests -v`, `launch.py --no-browser` / `--check`; move `test_catalog.py:97` to the new plant_sha with a comment; `lab_dump.py` / `lab_compare.py` | PHYS:26-28; APP:26-30 | 538 s + 62 s (map) |
| 13 | L6: `l6_agents.py` for the four tags, then `check_l6.sh` (needs `runs/extremes_dt1`) | BI:84 | — |
| 14 | L7: `make_meta.py` → `evaluate.py --engine b58` → `l7_diff.py` → `l7_expect.py` | BI:85 | ~2.6 h (map) |
| 15 | `run_suites.sh quick`: `test_wide_air`, `test_engine_threading`, `test_epa_map` (also with `GRAD_EXTRA_DATA` naming MY2021 and MY2023), `test_plant_guards`, `random_road.py`, `fingerprint.py` | BI:97-103, 250 | 1623 s for test_wide_air (BIJ suites) |
| 16 | the scripts this step edits, each compared before and after: `make_page.py`, `model_vs_data.py`, `substep_fit_check.py` | mistake 25 | — |
| 17 | **L9**, in a copy: `$PY -c "from thresholds import b58_propagation as P; P.run()"` and `$PY -c "from thresholds import ecu_shift as U; U.run_all(20)"`; the sha_text of `b58_propagation.json` and of every `ecu/*.json` must equal JSON `generator_inputs_sha256`. **Never run `engine_thresholds.py` itself in the repo for this**: it rewrites the contract | MD:1310-1313 | 145 s + 1270 s (`results/ENGINE_THRESHOLDS/run.json`) |
| 18 | `verify_docs.py`, then `run_drift.sh` (`drift_test.py` in parts) and `drift_control.py` | CL:108, 128 | 399 s; 1404 s (BIJ:2415) |
| 19 | `make_archive.py` → `make_cert.py` → `make_md.py`: the new certificate; the build-step-1 page moved verbatim to `STATE_HISTORY.md` | BI:192-194; CL "where things go" | — |
| 20 | L8 (`run_l8.sh`, 600 SAC steps) **on the training device only**, with decision 32's checks | VD:155 | — |

The list is about 10–12 h of compute and parallelises to roughly 5–6 h of wall time.

**After commit A, nothing in this step edits PLANT_CODE.** Any later fix that does needs a new certificate.

---

## 4. The leak-proof loader, `epa_rows.py`, and its self-test

### 4.1 Where the held-out set comes from

- **H**, the held-out rows, is the set of `(table, source_row)` pairs in JSON `engines.<id>.held_out_rows`. Each record holds `table, source_row, nominal_rpm, line, window` (`thresholds/split.py:224-229`).
- **L**, the held-out lines, is `held_out_lines`.
- Lines come from `engines.<id>.lines`, with merged names split on "/" (`split.py:96-108`).
- λ_ref, the hot MAP floor and the fuels are read from the JSON, never recomputed on calibration rows (MD:500-503, 525-526). Recomputing them would move the populations.

### 4.2 Guards, all checked before a row is read

1. **The contract.** Its sha_text equals the blob at the contract commit (`git show <commit>:results/ENGINE_THRESHOLDS.json`); that commit is an ancestor of HEAD; JSON `schema == 3`.
2. **The generator.** `thresholds/split.py` and `common.py` equal JSON `generators.sha256`. The loader imports `split.nominal`, `merge`, `lam`, `classify`, `LAM_BAND`, `LAM_ENR`, `TOL` and `FIRED_BMEP` rather than re-implementing them (mistake 10).
3. **The tables.** Each table's raw sha256 equals JSON `epa_tables_sha256` (`common.py:27-34`), and its header equals a pinned header (mistake 13: a new column is a new hypothesis).
4. **`epa_engine.json`** is exposed only through an allowlist: `displacement_l`, `n_cylinders`, `compression_ratio`, `bore_mm`, `stroke_mm`, `geometry_notes`, `alpha_fuel`, the tables' `fuel_report` and `test_cell`, and `reference_only_columns`. The curves are never returned.

### 4.3 Streaming

- Each table is read with `csv.reader`, not `split.load`, which builds a dict of every row (`split.py:78-80`).
- For each record, `source_row` is read first.
  - **If the key is in H, the row is counted and skipped. No other field is parsed, converted, yielded or cached.**
  - Otherwise its line is recomputed from its own speed (`split.nominal`, `:89-93`). A speed that falls in no contract line raises `KeyError`; a line in L raises `SplitViolation`.
- **After each table:**
  - the held keys seen equal that table's share of H;
  - the calibration and held-out counts equal JSON `tables`: Mazda 156/43/43; Honda 115/49/49; Ford 117/58/13/13 (MD:374-382);
  - the ids are exactly 6…N+5 (`epa_map.py` writes data from row 6);
  - the High Load Initial and Final calibration ids are identical (`split.py:155-157`).
  - Any mismatch stops: "a re-derivation must reproduce the counts of section 2.2, or stop" (MD:1189-1191).
- **Row types** are frozen dataclasses with no field for a forbidden column.
  - `SteadyRow` and `FinalRow` hold:
    - provenance, line and hold id;
    - speed; MAP; intake and coolant temperature, both in K; spark;
    - λ_meas (on HD1 both banks plus `split.lam`'s mean, `:83-86`);
    - the meter, or `None`; the injector estimate, flagged and never a stand-in for the meter (mistakes 9, 19);
    - torque, BMEP, TIT, TIP;
    - the barometer and cell temperature, or `None` (HD1 has no barometer, ch:24-43);
    - the cam channel by name, `_cad_ret` or `_cad_adv` (Mazda ch:24, Honda ch:26, Ford Cell 9 ch:22; mistake 13);
    - flags `spark_sentinel` (exactly −120, `epa_map.py:44-49`), `lambda_missing`, `meter_missing`, `cam_missing`.
  - `InitialRow` holds provenance, hold id, speed and torque only, `transient=True`. Asking it for TIT raises `AttributeError` (MD:433-434).
- **Derived once, in `epa_stats`:**
  - `lam_fed`: 1.00 if `|λ−λ_ref| ≤ LAM_BAND + TOL`, else `λ − (λ_ref − 1)` (MD:504-508);
  - `lam_cellref = λ − (λ_ref − 1)`, unsnapped;
  - `air_cal = meter × AFR_st(table) × lam_fed` on steady and Final rows (MD:521-522), `None` without a meter or λ;
  - populations through `split.classify` on a minimal dict;
  - the table's fuel from JSON `fuel_by_table`.
- **ALPHA nodes**, used descriptively only:
  - the nodes in `alpha_nodes_removed` are dropped, matched on `(table, source_row)` (`thresholds/alpha_nodes.py:18-27`), **together with their `measured_at_speed` record, which holds a held-out row's torque** (`epa_map.py:519-525`);
  - unmeasured nodes are labelled model (MD:445).
- **The held-out reader** `held_out_rows(id, token)` exists only for `validate_epa.py`. It needs an `epa_freeze.Token`, issued by `verify_for_validation()` (§6.1). It yields `HeldOutRow` and `HeldOutInitialRow` records carrying every needed column, including Initial MAP, IMT, ECT, spark, λ and TIT for E1i and the descriptive Initial-to-Final pair estimate (MD:604, 676-679; MD:447).
- **`manifest(id)`** holds, per table, the sorted calibration keys and their sha256. It is written into every output.

### 4.4 Structural pre-checks before Run 1 (counts only, printed and written to `stage0.json`)

These use `thresholds.split.compute()`, which reads every row's structure as the generator did (MD:1125-1127, 1189-1191). They print no value.

- Fired rows without λ, by partition and population (fired, fired-with-meter, hot). Rule: decision 54.
- Fired calibration rows carrying the −120 sentinel; expected 0, asserted. On held-out rows this check runs at the arm step, before any statistic.
- Final calibration rows at the table's λ minimum within 1e-9 (the Honda's reads 0.6100000000000045, ch:86). Two or more means censored (decision 54).
- Fired calibration rows with TIP below their cell barometer, with the count and the largest deficit (decision 52).
- The Ford Cell 9 coolant and oil columns compared for identity, since their maxima are equal (ch:13-14; mistake 13).

### 4.5 What the calibration never opens

- the ALPHA fuel map, `logs/epa/*`, the Tier 3 and LEV III packages, the Steady State with Transmission sheets, the SAE 2018-01-0319 dataset, any D3 file (MD:449-452);
- `results/ENGINE_THRESHOLDS/split.json`'s row records;
- the min and max of `epa_channels.csv`, which are computed over all rows (`epa_map.py:566, 573-574`);
- the JSON's all-row coverage blocks (only `coverage.calibration_*` is used).

### 4.6 The self-test, `test_epa_rows.py` (each guard shown able to fail)

1. **Counts and partition.** Yielded ∩ H = ∅ and yielded ∪ H = every id. Every yielded line is outside L, and every H record's line is in L.
2. **Re-derivation.** `split.compute()` serialised in memory as `json.dumps(…, indent=1, ensure_ascii=True)` hashes to JSON `generator_inputs_sha256["split.json"]` (`common.py:51-56`).
3. **Coverage.** `split.coverage` over the yielded fired and hot rows equals JSON `coverage.calibration_fired` and `.calibration_hot` exactly. This proves the set, not just its size.
4. **Masks.** `InitialRow.turbine_inlet_temp_c` raises; removed ALPHA nodes and their records are absent.
5. **Corruptions**, each stopping the loader, and each shown to pass with its guard monkeypatched off:
   - a held id deleted from a scratch JSON;
   - a held id shifted by one;
   - a line removed from L with its rows kept;
   - one byte changed in a scratch table;
   - a different `split.py` hash;
   - a contract differing from its commit;
   - a calibration id placed at a held line's speed;
   - a held row parsed.
6. **Poison, inside the test.** The table-hash check is monkeypatched, and every non-provenance column of every held-out row is replaced with garbage. The yield and the manifest must be byte-identical; changing one calibration cell must change them. Every stage consumes only this yield (items 7 and 8), so this proves the frozen constants cannot depend on held-out values. A full-fit poison run is optional.
7. **AST and source scans over `git ls-files --cached --others --exclude-standard`:**
   - no `.py` outside {`epa_map.py`, `test_epa_map.py`, the generator} contains `epa_steady` or `epa_highload`;
   - only `epa_rows.py` opens a file under `data/engines/*/epa_*`;
   - only `validate_epa.py` and its test call `held_out_rows(`;
   - `calibrate_epa.py`, `epa_fit.py` and `k3_knee.py` never import `validate_epa` or `Token`.
8. **A runtime audit.** `sys.addaudithook` runs in a subprocess executing `calibrate_epa.py dry-load`. The set of files opened must be a subset of {the ten tables, `epa_engine.json`, the contract, `engine_specs/*`, `engine_specs/cars/*`, the code}.

---

## 5. The fitting procedure, per form

### 5.1 What every stage shares

- **Model evaluation at a row:**
  ```
  run_cycle(Operating(rpm, MAP, IMT_K, ECT_K, spark_EPA, lam_fed,
                      exhaust_backpressure_kpa(MAP, engine=e)),
            engine=with_fuel(e, fuel_of(table)), cam_deg=<form D: ecu.cam_deg(rpm, MAP)>)
  ```
  These are EPA's inputs; everything else is the model's own (MD:495-498; JSON `conventions.inputs_fed`; `engine_env.py:761`). Each table runs on its own fuel (MD:511-518).
- **Weights and scaling.** Every row has weight 1. Residuals are expressed in units of the gated statistic's R: torque and efficiency 1.9 %, air and fuel 4.0 %, TIT 10 K.
- **No fit outcome stops the run** (RF-1). The pre-declared outcomes are in §5.6.
- **Determinism.**
  - No random numbers in the fit.
  - Fixed grids and starts.
  - An ordered spawn pool that gathers results in row order.
  - One BLAS thread, asserted.
  - No wall-clock time in any output except `run.json`.

### 5.2 Form A, stage by stage

| stage | constants (fitted per engine: MD:461-463) | rows (calibration lines only) | objective | method; bounds; start |
|---|---|---|---|---|
| **S0** channel checks | — | as §4.4 | counts and medians: meter against injector estimate (mistake 14), TIP against barometer, λ floor, cam sign | — |
| **S1** back-pressure | `exh_bp_ratio`, `exh_bp_min_kpa` (`plant.py:334`) | fired steady and Final rows with TIP (every table has it: Mazda ch:19/44/70, Honda ch:21/51/82, Ford ch:17/38/57/77) | Σ (TIP − r·max(h, MAP))² | hinge h profiled on a 0.1 kPa grid over the rows' MAP range; r in closed form; floor = r·h, which fixes the ill-posed split; r ∈ [1.0, 2.5]; floor ∈ [80, 140] kPa. Report σ (for E6 row 5), the residual against rpm (the form has no rpm term: reported, not fitted), and decision 52's sensitivity refit |
| **S2** breathing | `ve_base`, `ve_amp`, `ve_rpm`, `ve_width` | fired steady and Final rows with a meter and λ | Σ [(ln η_model − ln η_target)/0.04]² + ridge. η_target = air_cal/(ρ(MAP, IMT)·V_d·(1−f_res(MAP))·n_cyl·rpm/120), built with `plant.residual_fraction` and the geometry (`plant.py:159-162, 269`) | variable projection: `ve_rpm` over the calibration lines × `ve_width` on a log grid (300–20 000), linear LS for base and amp, then a `least_squares('trf')` polish; base ∈ [0.3, 1.3], amp ∈ [−0.6, 0.6]; start at the B58's (0.86, 0.14, 3800, 2600). **Verify:** `run_cycle(...).mdot_air_gps` equals VE·A_r within 1e-12 at every row (mistake 10) |
| **S3a** ECU spark | `spark_a, spark_b, spark_c`, `kl_a..kl_d`; `spark_min`, `spark_max` | fired steady and Final rows, no sentinel | target = spark_EPA − `iat_compensation(IMT)` (− `cold_retard` if ECT < `cold_k`; asserted not to happen), as `derive_params.py:195-201` | alternating piecewise OLS. Start: MAP below the hot floor → plane; assign each row to the lower piece, refit, repeat until stable (≤ 50; else the lowest-SSE assignment visited). `spark_min`/`spark_max` = floor/ceil of the extremes over targets and fitted values, ∓1°: the B58's principle, "the car retards past TDC" (`b58.toml:98`). So no clip binds at a calibration row, by construction. `spark_ref_kpa` = 40, DESIGN |
| **S3b** ECU λ | `enr_load`, `enr_rpm_lo`, `enr_rpm_hi`, `enr_depth` (the form of `engine_env.py:341-347`, dwell 30 s, so t = 1 with the carried 1.5 and 3.0 s) | Final rows with λ | Σ (λ_ECU − λ_cellref)², λ unsnapped and **cell-referenced: E8's own convention** (MD:773-774). Censored rows (§4.4) contribute only when λ_ECU exceeds their reading | grid: gate from the hot floor − 20 to the largest Final MAP in 1 kPa steps; rpm breakpoints on the calibration lines, rpm_hi ≥ rpm_lo + 300; depth by closed-form LS in [0, 1 − `lam_floor`]. Ties go to the lowest gate, then rpm_lo, then rpm_hi. Report the SSE profile's flatness, the rows behind each constant (mistake 4), and, descriptively, how many steady hot rows the ECU would enrich at |
| **S3c** boost envelope | `envelope_flow`, `envelope_pr`, `pr_cap` | per calibration line, the highest-MAP steady or Final row with a meter | corrected flow from `air_cal`, cell temperature and (barometer − 2) (`plant.py:409-412`); **PR = MAP/`inlet_sea_kpa`**, so the in-use ceiling `inlet × PR` never exceeds a measured MAP (`plant.py:436-437`; `engine_env.py:774-775`); anchored at (0, 1); **no running maximum** (the measured shape); cap = max MAP/`inlet_sea_kpa`. HD1 barometer per decision 53. Declared as a deviation from the B58's binned p95 with ≥ 15 rows (`derive_params.py:60, 167-168`) |
| **S4** burn, friction, port | outer: `burn_base, burn_rpm, delay_base, delay_rpm`. Inner: FMEP's **four** coefficients by linear LS, and `ua_port` by Brent | fired rows in the λ≈1 band (they run at 1.00): efficiency on rows with a meter, TIT on all | Σ[(ln(T_m/T_E) − ln(F_m/F_meter))/0.019]² + Σ[(TIT_m − TIT_E)/10 K]² + ridge. Efficiency answers to burn and FMEP, the meter to VE: one channel per block, so compensating errors stay visible (mistake 20). TIT is `egt_c`, the gas after the port loss (`plant.py:281-287, 303`) | `least_squares('trf')`, forward differences: 0.5 CAD on the bases, chain rule in CAD on the rpm terms. Cycles cached by the 4-tuple: FMEP (`plant.py:263`) and UA (`:286-287`) sit outside the integration loop (`:222-255`), so their columns are analytic. Three starts: the B58's (34, 0.0022, 7, 0.0011; `b58.toml:62-65`), ×0.8, ×1.2. Bounds [5, 90], [0, 0.012], [0, 30], [0, 0.006]; FMEP [−0.5, 2] bar, [−0.05, 0.05], [−0.1, 0.4], [−0.01, 0.02]; UA [0, 1000] W/K. `max_nfev` 60 |
| **S6** knock scale | `knock_a` | Final rows | **geometric mean of KI = 1** (decision 51) | KI ∝ 1/knock_a exactly (`plant.py:254-255`), so one sweep at the B58's 0.01768 then knock_a ← 0.01768·exp(mean ln KI); re-run to confirm \|mean ln KI\| < 1e-12. Report KI's spread (a descriptive check of the correlation's shape) |
| **Verify** | — | every fitted row | every shortcut (VE target, cached cycles, profiled FMEP and UA) equals a direct `run_cycle` within 1e-9 relative; every fitted parameter moved and its Jacobian column is non-zero (mistake 25) | an assertion. A failure is a coding defect |

**The ridge, declared.** Each nonlinear stage adds √w·(θ_i − θ_i⁰)/s_i:

- the centre θ⁰ is the B58's value; for B and D terms it is 0 (`ve_map`, scale 1e-3 per kPa; `ve_cam`, scale 1e-3 per CAD); for the C slope it is 0.65 (scale 0.65);
- w = 0.01;
- s_i is a declared scale per parameter: burn_base 10 CAD, burn_rpm 0.002, delay_base 5, delay_rpm 0.001, fmep_0 0.4, fmep_pmax 0.005, fmep_sp 0.09, fmep_sp2 0.0009, UA 50 W/K, ve_rpm 1000, ve_width 1000.

It decides only directions the data leave undetermined. Each parameter is reported as "data-dominated" or "prior-dominated" (Fisher information against the prior) beside its correlations and condition number. **No constant is held**, so form A's fitted set stays the contract's (PF-B1; `thresholds/contract.py:617`).

**Excluded and listed:** rows without λ (from every stage that feeds λ); sentinel rows; rows without a meter (from S2 and from S4's efficiency term); rows between the λ bands (from S4). No closed-throttle fit is made: the model has no fuel cut (`engine_env.py:1305-1308`).

### 5.3 Forms B, C and D, each adding to the one before (MD:469-477)

- **A+B.** S2 with `ve_map` (VE in rpm and MAP), then S4 and S6 again, because the trapped mass moves.
- **A+B+C.** A+B's S2 and S4 are kept. **S5** fits `ce_rich_slope` on enriched hot calibration rows (λ ≤ λ_ref − 0.05, MD:471-472, 537) with S4's residuals, by bounded Brent on [0, 1.5]. It flags a bound hit and a physical check (η_comb at the engine's deepest calibration λ ≥ 0.5). S6 runs again.
- **A+B+C+D.**
  1. **S3d:** the cam schedule, a full quadratic in (rpm/1000, MAP/100), by OLS on calibration rows that carry a cam value. Empty cells are excluded (Honda ch:56, :87). The Ford has the channel on Cell 9 only (ch:22), so HD1 holds and every point above Cell 9's 4501 rpm (ch:2) or its MAP range are clamped and flagged as extrapolated (mistake 6).
  2. S2 with `ve_cam`; VE's cam input is **the schedule's cam** at every row, which is what the plant uses.
  3. S4, S5, S6.
  - No sign is assumed: `ve_cam` absorbs `_ret` against `_adv`. Signs are normalised only for reports across engines.

### 5.4 The ladder

- Fit form A for all three engines.
- Compute the in-sample stage (§5.5).
- If every gating statistic of every EPA engine passes, freeze A. Otherwise move all three to A+B, starting from A's solution with the new term at 0, and so on. This is decision 49's common form; the per-engine reading is its alternative.
- If none passes, freeze A+B+C+D and report the failing statistics (MD:480-481).
- Forms after the chosen one are not fitted. Every form fitted is kept in `fit_<form>.json`.

### 5.5 The in-sample stage (MD:478-481; JSON `model_form.in_sample_stage`)

These are computed by `epa_stats` on **calibration** lines, with the same definitions, populations (`split.classify`) and line minimum (≥ 3 clusters, `split.MIN_CLUSTERS`; one row is one cluster). They are fit residuals: no u, never labelled (VP:326-327).

| statistic | E_cal | R |
|---|---|---|
| E1a | worst deciding line's mean of T_m/T_E − 1, hot rows | 1.9 % |
| E2a | the same for fuel/meter, hot rows with a meter | 4.0 % |
| E3a | worst line's mean of TIT_m − TIT_E, hot λ≈1 rows | 10.0 K |
| E4a | the same, hot enriched rows | 10.0 K |
| E4b | ε pooled over lines with ≥ 3 boosted λ≈1 rows and ≥ 1 enriched hot row (`split.py:242-243`) | 16.6 % |
| D1 | mean \|δ_D\|, fired rows with a meter (§6.3) | 16.6 % |
| L0 | worst line, f bounded | 10.0 K |
| L1 | spread, ≥ 2 deciding lines | 9.9 K, untightened |
| E8 | over calibration Final rows | 16.6 %, the locked-climb P (untightened) |

- **A statistic with no deciding calibration line** neither blocks nor passes; it is recorded as such (decision 55).
- **E8** is computed and reported. Under decision 39(a) it is excluded from the cycle-form criterion, because its inputs are the ECU fit alone (MD:773-776) and no form can move it.

### 5.6 What happens when a fit misbehaves (all pre-declared; never a stop)

| event | outcome |
|---|---|
| a parameter at a bound | kept at the bound (the constrained optimum), flagged |
| no convergence within `max_nfev` | one declared second attempt (`max_nfev`×2 from the best iterate); then the best iterate is accepted and flagged, with its convergence measured: gradient norm, last step, cost change (mistake 15) |
| a VE value at a clip (0.30/1.30, DESIGN) on a calibration row | flagged, with the rows listed; the clip is a rail, never widened after a fit |
| S3b grid profile flat | reported with its width; no hold |
| a physical check outside its range (burn 20–120 CAD, delay 1–40 CAD, FMEP > 0 across calibration rpm, η_comb ≥ 0.5) | flagged |
| an assertion fails (a count, a hash, shortcut ≠ plant) | **a coding defect**: fix it, re-run the whole calibration from S0, keep both runs in a calibration-defect log beside `fit.json` |

### 5.7 E6 refit variants, fitted before any held-out statistic (MD:747-749, 1039-1042)

Each variant reruns S1–S6 at the chosen form (no new ladder) and is written to `results/EPA_CALIBRATION/<id>/e6/row<n>.json`. The plant in use stays frozen.

| row | variant |
|---|---|
| 1 | **the offset only:** every unsnapped row runs at λ_meas instead of λ_meas − (λ_ref − 1). The snap is kept, and the calibration air follows (MD:753). The Mazda and HD1 offsets are 0.000, so those variants are no-ops by construction |
| 2 | AFR_st → 14.7 in both the calibration air and the plant's fuel |
| 3 | LHV → 44.0 MJ/kg through `with_fuel` (the plant and the network together) |
| 7 | `knock_a`/0.90 and /1.10: a closed-form rescale, since KI ∝ 1/knock_a |

**Row 12** (no snap) is **no refit** (MD:764); it is evaluated in the validation.

### 5.8 The freeze: the derived file, and what is hashed

**`data/engines/<id>/derived_params.json`**, written by `common.write_json` (LF; stored byte for byte under `-text`).

- **Frozen sections** (written at the freeze):
  - `cycle`: `form`, `ve_base, ve_amp, ve_rpm, ve_width, ve_map, ve_cam, ce_rich_slope, burn_base, burn_rpm, delay_base, delay_rpm, fmep_0, fmep_pmax, fmep_sp, fmep_sp2, ua_port, exh_bp_ratio, exh_bp_min_kpa, knock_a`;
  - `ecu`: `spark_a, spark_b, spark_c, spark_min, spark_max, kl_a, kl_b, kl_c, kl_d, enr_load, enr_rpm_lo, enr_rpm_hi, enr_depth, cam_on`, the six cam coefficients, the domain and the clamp;
  - `boost_ceiling`: `envelope_flow, envelope_pr, pr_cap`.
  - Terms a form does not use are written at their neutral values.
- **Completion sections**: `deliverable_torque`, `k3.turb_knee_k`, `loop.torque_floor_nm`.
- **Bookkeeping lives in top-level `_` keys only** (`_about`, `_inputs`). `fingerprint.derived_sha` drops top-level `_` keys alone (`fingerprint.py:366`); a nested key would be hashed.
- **No timestamp.**

**`EPA_DERIVED_FIELDS`** maps these fields to their sections. `damage.turb_knee_k` maps to `k3`, `loop.torque_floor_nm` to `loop`, and `car.deliverable_torque` to `deliverable_torque`.

**`results/EPA_CALIBRATION/<id>/freeze.json`** records:

| field | what |
|---|---|
| `form` | the frozen form |
| `frozen_sections_sha256` | sha256 of the canonical JSON (sorted keys, float `repr`, LF) of `{cycle, ecu, boost_ceiling}` |
| derived file | its sha_text, and `derived_sha` at the freeze |
| contract | commit, and the sha_text of the JSON and the MD |
| data | the raw sha256 of the ten tables (equal to the JSON's), of `epa_engine.json` and of `epa_channels.csv`; the manifest's sha256 |
| code | the sha_text of `calibrate_epa.py, epa_rows.py, epa_stats.py, epa_fit.py, epa_freeze.py, k3_knee.py, epa_coefficients.py, validate_epa.py, d3_rows.py` |
| plant | `plant_sha = fingerprint._sha_files(fingerprint.plant_files(id))`, which is computable because the plant was registered in commit A |
| fits | `fit_<form>.json` and `in_sample.json` sha_text |
| versions | Python, NumPy, SciPy; `git_head` |

**`complete.json`** records the completion's outputs (§5.9), the final derived_sha and sha_text, `engine_sha` as built, the E6 variants' sha_text, and the **frozen-plant dump** sha256.

**The frozen-plant dump** is evaluated on synthetic inputs only, never EPA rows:

- `run_cycle` on a fixed grid: 9 speeds over [`rpm_min`, `rpm_max`]; MAP {30, 60, 100, 140, 180, 220} clipped to the calibration range; spark {−5, 5, 15, 25}; λ {max(0.70, `lam_floor`), 0.85, 1.0}; IMT {310, 330} K; ECT 365 K; the in-use fuel; the cam from the ECU; 16 fields each;
- `exhaust_backpressure_kpa`;
- `BaselineECU`'s `base_spark`, `knock_limited_spark`, `base_lambda` (dwell 0, 3 and 30 s), `iat_compensation` and `cam_deg` on an (rpm, MAP) grid;
- `boost_ceiling_kpa` on a flow grid;
- `charge_temperature`;
- the vehicle's `road_force_n` and `demand` on a (v, a, grade) grid;
- H's thermal sequence.
- The arrays are concatenated as float64 `tobytes()` in a fixed key order, then hashed.

`engines._build` for an EPA plant refuses a derived file whose frozen sections do not match `freeze.json` (F7).

### 5.9 Completion (`calibrate_epa.py complete`; a fresh process under `DERIVING_PARAMS=1`, as `derive_params.py:284-296`)

Before each step, assert that every float of `asdict(plant)` is finite except the field being measured (mistake 19).

1. **Deliverable-torque table.**
   - `measure_deliverable_torque(plant.car.table_rpms, plant=plant)` (`engine_env.py:1069-1101`), rounded to 0.1 Nm as `derive_params.py:297` does.
   - The grid lies inside the calibration lines, because `np.interp` clamps at the table's ends (`:510`).
   - It is re-measured at 60 settling steps, and the largest difference is reported.
   - The knock-flag duty during the measurement is reported.
2. **Torque floor.** 1.25 × the torque at a request of 0 at max(1200, `rpm_min`) rpm and 42 °C, by `b58.toml:152`'s rule. It is labelled an extrapolation, because FMEP was fitted on fired rows only.
3. **Delivery check, before the knee** (CL-7, PF-4).
   - Run the neutral policy on the car's locked climb (frozen episode 1, dt 1 s) with a provisional finite knee. A NaN knee ends the episode (`engine_env.py:1052`).
   - Report the share of steps with t > 20 s where the tracking error exceeds `TRACK_TOL` (`:650`), the largest shortfall, the gear or ratio, the rpm, and the MAP against its ceiling.
   - The consequence is decision 44's.
4. **K3 knee.** `k3_knee.knee_for(trace, 413)`, where 413 is `k3_nominal.json` `time_above_nominal_s` (verified): the midpoint of the 413th and 414th highest housing temperatures (`ecu_shift.py:93-97`). The trace is re-run with a second provisional knee and must be bit-identical, which proves the knee cannot move the neutral trajectory.
5. **Own coefficients** (`epa_coefficients`): the climb's median cell over t 400–718 s, f, τ, G_e, and the gas, flow and housing response to ±1 % torque, as `b58_propagation.py:51-155`. Descriptive only; they never move an R (MD:229-231).
6. **E6 probe sizes.**
   - Level rows: the change of each constant (row 5: the back-pressure law; row 6: UA_PORT; row 9: conrod, IVC, EVO, t_head, port pickup, t_residual, cp_exh, flame and burn terms, Wiebe) that moves the engine's **own** housing equivalent at its climb cell by R1. It is found by running the climb at ±10 % and scaling linearly (MD:733-736).
   - d rows: ±10 % (d needs agents).
   - Row 9's brackets from EPA's valve channels, on calibration rows: Honda effective strokes (slider-crank inverted); Mazda's Atkinson ratio and Ford's cam phases fall back to ±10 CAD (ch:27; ch:22-23).
   - Constants whose band moves the housing by more than R1 are listed as load-bearing.
7. **E6 row 4.** τ and the 850 °C baseline peak at ×0.75 and ×1.333 of each housing constant. The roads' ceiling is added by the roads step (MD:756).
8. **E6 row 7.** The knock term's share of the baseline's damage at KI 1.00, 0.90 and 1.10, both readings (`evaluate.py:283-293`).
9. **E6 row 13.** The variants with the dwell gate at 0 s and at 30 s, handed to the preregistration.
10. The frozen-plant dump; the final derived file. The frozen sections are asserted unchanged (their canonical hash recomputed).

### 5.10 T0: synthetic recovery at the real inputs (WP3; PF-7)

- **Setup.** For each engine, take the calibration rows' **input** columns: speed, MAP, IMT, ECT, spark, λ_fed and the table fuel. Generate synthetic outputs from a known truth θ*: torque, TIT and KI by `run_cycle`; fuel and meter from the air; TIP from the law; spark and λ from the ECU forms.
  - Truth: burn ×1.15, delay ×0.9, FMEP ×1.2, UA ×3, VE moved, back-pressure 1.45 and 102 kPa.
  - One seed's truth has `ve_map = 2e-3` per kPa, to exercise the ladder.
- **Noise.** Seeded: torque 0.5 %, meter 0.5 %, TIT 3 K, spark 0.5°, λ 0.005.
- **Then** run the whole fitting procedure over 3 seeds.
- **Pass:** for the data-dominated parameters, χ² of (θ̂ − θ*) against the reported covariance lies within the 99 % quantile for every seed; the B-truth seed's ladder stops at A+B; the A-truth seeds stop at A.
- No EPA output is read. A failure is investigated as a coding defect before commit C.

### 5.11 Runtime on this laptop

Measured per `run_cycle` call: 10.4–11.4 ms at 0.25° and 18.8–22.8 ms at 0.125° (`scratchpad\plant_map_timing\timing_out.txt`). 20 logical CPUs (`nproc`). The rest is (arith.), not measured.

| item, per engine | cycles | serial | pooled (16) |
|---|---|---|---|
| S1–S3 | 0 | seconds | — |
| S4, one form (30 iter. × 5 sweeps × ~170 rows × 3 starts) | ~77 000 | ~14 min | ~1.5 min |
| ladder, worst case (4 forms) | ×4 | ~60 min | ~6 min |
| in-sample, per form (D1 bisection ~150 rows × 25) | ~4 000 | ~45 s | — |
| E6 refits (rows 1–3 at the frozen form) | ~3 × S4 | ~45 min | ~5 min |
| completion (table 4.4k, two K3 traces 8.6k, coefficients 13.5k, probes ~30 climbs, row 4 and row 7 climbs) | ~60 000 | ~40 min | ~6 min |
| **total, three engines** | | **~6–8 h** | **~1 h** |

T0 is about four calibrations per engine, roughly 1 h pooled.

---

## 6. The held-out validation, `validate_epa.py`, run once

### 6.1 Guards, and computing it once (CL-3, RF-2, RF-3, PF-B2)

**`arm --engine <id>`** checks everything below, prints counts only, and writes `results/EPA_VALIDATION/<id>/ARMED.json` with every hash:

- the freeze and completion are committed and clean;
- the derived file's sha_text and derived_sha, the engine, car and published-car files' sha_text, and `engines.engine_sha(plant)` all equal the recorded values;
- **the frozen-plant dump, recomputed now, is bit-identical**;
- **`calibrate_epa.py check` re-runs the in-sample stage on calibration rows and gives back `in_sample.json` byte for byte**;
- the contract's sha_text equals the freeze's;
- the validation code's sha_text equals what `freeze.json` recorded, so it was committed before the first fit;
- `results/EPA_TIGHTENINGS.json` is committed (JSON `order_of_work[2]` before `[3]`);
- the 43 D3 files' raw sha256 equal JSON `d3_files_c3` and the data folder's `MANIFEST.csv` (`thresholds/contract.py:156-177`);
- no `rows.json` for this engine exists in the tree or in `git log --all`;
- **the populations reproduce** JSON `per_held_out_line`, `deciding_lines` and `pooled_counts` (`split.compute()`, structure only);
- fired held-out rows without λ and with the sentinel are counted. A fired sentinel row stops here, before any statistic (decision 54).

The person commits `ARMED.json`. That commit is the arming.

**`run --engine <id>`:**

- It refuses unless `ARMED.json` is committed at HEAD with matching hashes and the validation code is clean.
- **It prints counts and file paths only.** No statistic reaches a screen before the file holding it exists.
- Each output is written atomically: a temporary file, then a rename.
- `run.json` lists every invocation with its time and outcome.
- **If a run crashes** with nothing written and the code byte-identical to `ARMED.json`'s, it may be executed again: no statistic was seen, and nothing could have been adjusted. Otherwise only `--defect-rerun "<reason>" --fix-commit <sha>` may run; it writes `rows_rerun<k>.json` beside the first, keeps both, and caps the re-run's labels at limited (MD:1043-1045).
- **The token** (`epa_freeze.Token`) is issued only by `verify_for_validation()` after all of the above. `held_out_rows()` needs it.

### 6.2 The rules every row uses

- **The model at a held-out row** is §5.1's call with the frozen plant. Initial rows (E1i) run at their own inputs, labelled transient.
- **The line rule** (MD:539-548; VP:319-324):
  - per deciding line, with ≥ 3 clusters (one row is one cluster), compute E_l, u_val,l and u_stat,l;
  - a line reads **off** if |E| − 2u_val > R; else **untested** if 2u_val > R; else **validated** if |E| + 2u_val ≤ R; else **limited**;
  - a line certifies a pass only if 2u_stat ≤ R;
  - the row is off if any deciding line is off; otherwise the worse of the certifying lines' labels; untested if no line certifies;
  - the row **reports** its worst line's E with that line's u (decision 57);
  - pooled rows use the same rule with the pooled u.
- **u_val = √(u_num² + u_input² + u_D²)** (MD:549-552; VP:53). Each term is the uncertainty of the population's mean: random parts divided by √clusters, common parts in full. One propagation serves every statistic:
  - a common part is |stat(x+u) − stat(x)| with every row moved together;
  - a random part is √Σ_c (stat(x with cluster c moved) − stat(x))², which for a mean is SD/√n.

| term | definition (decision 56) |
|---|---|
| u_num | per row ΔS = S(0.125°) − S(0.25°) (`run_cycle(dtheta=0.125)`, `plant.py:153`; E6 row 8), mean removed, random; the undivided SD reported beside it (MD:553-555) |
| u_input | per channel (speed, MAP, IMT, ECT, spark, λ): sensitivity by central difference through the **whole** statistic, D1's bisection included, × u_j; random. u_j is EPA's stated accuracy if its instrument pages give one (opened before the fit), else the resolution of the same channel's steady table /√12 (λ 0.01, MAP 0.01 kPa, temperature 0.1 °C, speed 1 rpm; spark as printed), else a declared floor marked unsourced. **Never inferred from `repr` digits** (`epa_map.py:308-314`; RF-6). A cell's common λ offset is E6 row 1, not here (MD:556-557) |
| u_D | TIT 0.0075·\|t̄\|/√3, common (MD:561-562); λ 0.012, common, applied where EPA's λ is itself compared (E8) or enters a reference (E4b); meter and torque: EPA's stated accuracy, else resolution/√12, random. Each marked "u_D unsourced" (MD:560). In differences read by one sensor (E4b, L1), a common offset cancels by propagation |
| u_stat | SE of the mean per line, one row per cluster; E4b by the delta method on cluster sums; L0 at the maximising f* (envelope theorem); L1 √(u_a² + u_b²) of the two extreme lines at the maximising f (MD:724); E8 through P's slope |

- **Coverage flags** sit beside every label and never replace one:
  - JSON `engines.<id>.coverage`, calibration against all rows;
  - a charge at 42 °C, holds longer than 30 s, speeds above 115 km/h (MD:575-588);
  - per row, MAP outside the calibration coverage band (decision 58);
  - the barometer (cells at 97.2–98.6 kPa against the road's 101.3).
- Every d row carries "both arms' cuts in 0–0.865" (MD:592-593).

### 6.3 Row by row (counts from JSON `pooled_counts` and `deciding_lines`)

| row | population (held-out lines) | statistic | R; kind |
|---|---|---|---|
| E1a | hot rows (Final, and steady rows at or above the hot floor: Mazda 109.56, Honda 124.68, Ford 136.22 kPa); lines Mazda 1750/2500/3500, Honda 2000/3000/4500, Ford 1250/2000/2500/3500/5000 | worst line's mean T_m/T_E − 1 | 1.9 %; level |
| E1b | fired steady and Final (54/69/70) | mean \|T_m/T_E − 1\| | descriptive (worth b at 12.3 %) |
| E1i | Initial rows (18/16/6) at their own inputs | per-line mean signed error | descriptive, transient |
| E2a | hot rows with a meter; lines per `deciding_lines.E2a` (Ford without 5000) | worst line's mean fuel/meter − 1 | 4.0 %; level |
| E2b | fired rows with a meter | mean \|·\| | descriptive (worth b at 16.6 %) |
| E3a | hot λ≈1 rows: Mazda 3 lines, Honda 2000/3000, Ford 1250/2000/2500 | worst line's mean `egt_c` − TIT | 10.0 K; level |
| E3b | fired λ≈1 rows | mean \|·\| | descriptive |
| E4a | hot enriched rows: Mazda 2500; Honda 2000/3000/4500; Ford 3500/5000 | as E3a | 10.0 K; level |
| E4b | enriched hot rows of lines with ≥ 3 boosted λ≈1 rows (6/13/4) | L_S = S(λ=1) − S(row); ê from the line's least-squares fit of the λ≈1 error on MAP (MAP ≥ 100, n ≥ 3), at the row's MAP; ε = ΣL_S/Σ(L_S + e_enr − ê) − 1. Report the extrapolation distances (MD:420-424) and, descriptively, the Initial-to-Final pair estimate (MD:676-679) | 16.6 %; d, P2 |
| E5 | λ≈1 rows; window A (MAP < 100, BMEP ≥ 2) and window B (MAP ≥ 100); lines with ≥ 3 rows in the window | Σcov(MAP, S)/Σcov(MAP, D) − 1, `np.cov(ddof=1)` per line | descriptive; "the boost lever is untested" |
| D1 | fired rows with a meter (52/69/68) | per row: pre-scan torque on 20–400 kPa every 10 kPa, then bisect the first bracket to 1e-3 kPa, at EPA's speed, IMT and ECT, `lam_fed`, spark = EPA's + s·(MAP − MAP_E), s = (base_spark(MAP_E+2) − base_spark(MAP_E−2))/4; form D's cam at the bisected MAP; δ_D = fuel/meter − 1, e_D = TIT_m − TIT_E. An unbracketed row is evaluated at the nearer bound, listed, and D1 is also reported without it (decision 57) | 16.6 %; d, P1 |
| L0 | hot λ≈1 rows with a meter (21/10/16); `deciding_lines.L0` | per line ē, δ̄; max over f ∈ [0, 1] of \|fē + f(1−f)Gδ̄\| in closed form (endpoints and vertex), G = 980.27 K (JSON `propagation_b58.G_gas_over_42C_k`); worst line | 10.0 K; level |
| L1 | L0's lines (≥ 2) | max over f of [max_l H_l − min_l H_l], exact over pairs (each difference is quadratic in f) | 9.9 K, or the tightened b/slope; d, P3, additive |
| E8 | Final rows (18/16/6) | the ECU at the row's rpm and MAP, dwell 30 s, no knock retard, EPA's IMT: dl = mean(λ_ECU − λ_cellref) **unsnapped** (MD:773-774); ds = mean(spark_ECU − spark_E); E8 = \|P_λ(dl)\| + \|P_s(ds)\|, P per shift the larger \|·\| of JSON `ecu_strategy_b58.k3_pair_change_vs_*` and the roads' tables (signed value kept, as `thresholds/contract.py:71-86`), interpolated by `thresholds.contract.interp` (linear extrapolation, `:89-99`, flagged); u through the slope of the segment holding dl, at 0 the steeper side. Also reported: dl and ds alone; the error worth b (JSON `worth_b`: λ −0.0206/+0.0086, spark −2.594°/+2.625°, the last extrapolated); per line, the lowest MAP where the model's λ falls 0.05 below λ_ref, beside EPA's; the snapped E8, descriptive | 16.6 %; d, P4; expected untested (MD:325-329) |

### 6.4 E6, in the same single run (MD:730-769)

| row | how it is computed |
|---|---|
| 1, 2, 3, 7 | §5.7's variants on the held-out rows: per row ΔE, and "excluded for" when \|ΔE\| < u_val. Row 2: E2, D1 and L0 must move by less than u_val; a miss is reported as a finding, not hidden and not a stop. Row 1 also reports the in-use hot TIT at λ = 1, the air and τ. Row 3: heat release per gram, coolant and oil heat |
| 4 | completion's τ and peaks; excluded by construction; the roads' ceiling flagged below 2 MEI |
| 5, 6 | ± each constant's σ from S1/S4, and ± the probe. E1a, E3a and L0 (row 5), and E3a, E3b, E4a and L0 (row 6), must move; otherwise "excluded for" |
| 8 | is u_num |
| 9 | completion's brackets or probes; the rows each constant sets must move; the error worth R1 and worth b reported |
| 10 | C3 at η 0.86 and 0.98 |
| 11 | IMT ± 6.3 K on the hot TIT rows (MD:763); the roads' cuts come later |
| 12 | every gating row unsnapped, no refit; E3a, E5, D1 and L0 labelled by the worse, in the order off > untested > limited > validated (decision 59); E8 unsnapped is already the nominal, and snapped is reported |
| 13 | handed to the preregistration |

- The **Tests lists** behind "excluded for every constant it claims to test" are decision 59's.
- E6 never drops an engine (MD:745).

### 6.5 C3 and C4

- **C3, the CX-9 on D3, blind** (MD:820-882; `d3_rows.py`, Mazda only).
  - **Segments:** at least 3 s with speed within ±25 rpm; the PCM MAP channel refreshed at least twice; `Eng_speed_CAN` within 1 % of `Trans_turbine_shaft_speed_TCM`; `HVAC_ACComp_cycling_switch_PCM` off throughout; one gear; coolant ≥ 83.8 °C; padding dropped. Every window is in seconds (mistakes 8, 13b).
  - **The chain:**
    - torque = `Dyno_TractiveForce` × r_N/V ÷ (gear × final drive) ÷ η;
    - the Mazda's MAP by D1's bisection at the measured speed and coolant;
    - the ECU's spark and λ, with the dwell timer run on the car's own PCM MAP trace;
    - the charge from `charge_temperature`.
  - **Populations:** hot = PCM MAP ≥ 109.6 kPa (data); fired = demand ≥ 2 bar. Segments with a modelled charge outside 37.3–55.0 °C are reported apart.
  - **Model fuel** × 18 447/18 659.
  - **Channel checks first:**
    - Direct2's integral against the summary's modal fuel, into u_D (`Eng_FuelFlow_Direct` never used);
    - MAF against Direct2 × AFR_st × 1/`Eng_equiv_ratio_b1_s1_PCM` on closed-loop segments, \|r̃ − 1\| into u_D, flat maxima dropped (mistake 7);
    - the PCM MAP below barometric at closed throttle.
  - **u_input** = 5.25 %, common (`thresholds/contract.py:267-270`).
  - **Rows:** C3a and C3c descriptive; C3b and C3d at 16.6 %, deciding with ≥ 3 segments and 2u_stat ≤ R.
  - Decision 63 covers the unpinned inputs.
- **C4.** Figures already seen are cited, not recomputed. The Accord's chain runs as C3 and is reported as descriptive; its D3 files are pinned at run time. The F-150's gearbox is untested beyond C2 (MD:884-896).

### 6.6 Outputs and the hashes they record

`results/EPA_VALIDATION/<id>/` holds `ARMED.json`, `rows.json`, `e6.json`, `c3.json` (Mazda) or `c4_accord.json` (Honda), `run.json` (times only) and figures. `results/EPA_VALIDATION/summary.json` covers all three.

- **Per row:**
  - E; u_num, u_input and u_D with their "unsourced" marks; u_stat;
  - every line's value; the deciding and certifying lines; the worst line; the label;
  - κ = 1 if validated, else (|E| + 2u_val)/R (MD:1016-1017);
  - the coverage flags; the D1 unreachable list; E4b's and E8's extra reports.
- **Every file records:**
  - the contract's commit and sha_text;
  - `freeze.json` and `complete.json` sha_text and commit;
  - derived_sha, engine_sha and the dump's sha256;
  - the tightening record's sha_text and commit;
  - the table and D3 raw sha256;
  - the code's sha_text and the versions.
- **Section 7's labels** (MD:992-998) are written per engine: level rows give the 850 °C row's label; d rows give band factors; an off d row, or one with no statistic, writes **DROP** (MD:1007-1009).
- **Δ_e** (RSS and linear sum, with φ at the realised cuts) needs d, so it comes later (MD:1015-1027).
- **Drops** are entered in VD by a person (MD:1047-1049).

---

## 7. The cars, the CVT, C1–C5, the deliverable-torque table and the K3 knee

### 7.1 Records (new; `Car` unchanged for the Supra, decision 31, VD:154)

- **`EpaCar`** (CX-9, F-150) has `Car`'s fields minus `cd_a` and `crr`, plus `road_a_n`, `road_b_n_per_mps`, `road_c_n_per_mps2` and `road_rho_ref`. It keeps the `table_rpms` property.
- **`CvtCar`** (Accord) has `id, mass`, the road load, `wheel_r, final_drive, ratio_low_gear, ratio_top_gear, driveline_eff`, the law's parameters, `rpm_min, rpm_max, deliverable_torque` and `table_*`. It has no `gears`.

### 7.2 Road force and the stepped box

- `EpaVehicle(Vehicle)` has its own `__init__` and `road_force_n(v, grade, *, rho) = (A + B·v)·cos θ + C·v²·(ρ/ρ_ref) + m·g·sin θ` (decision 42).
- ρ_ref = 98 210/(287.0 × 293.15) = 1.167304 kg/m³ (arith.), with the environment's own R (`engine_env.py:958`). At the climb, ρ/ρ_ref = 0.9599 (arith.).
- `demand()` computes f = m·a + road force, then uses the inherited `gear_for`, `shift_ceiling_nm` and rpm clip (`engine_env.py:507-612`).
- It is a new class, so the Supra's `m·a + drag + rolling + grade` sum is not re-associated.

### 7.3 The Accord's CVT (decision 40)

- **Window:** N ∈ [N_lo, N_hi] with N_lo = max(`cvt_rpm_min`, n_w·0.405·5.36) and N_hi = min(`rpm_max`, n_w·2.645·5.36), where n_w is the wheel speed.
- **Low-speed branch (PF-3).** If N_hi < N_lo (below about 8.7 km/h (arith.)), the ratio is the low gear 2.645, N = `cvt_rpm_min`, and torque = f·r/(2.645·fd·η). Converter slip is ASSUMED, as the Supra's rpm clip at launch (`engine_env.py:609-611`).
- **Law (a), economy line.** N* is the smallest N in the window with P_e/ω(N) ≤ λ_cvt·T_del(N): a 10 rpm scan, then bisection to 0.01 rpm.
  - If none qualifies, N* = argmax over the window of T_del(N)·ω(N), flagged "power-limited" (mistake 9).
  - If f ≤ 0, N* = N_lo.
  - ratio = N*·2π/60·r/(v·fd), clipped to [0.405, 2.645]; torque = f·r/(ratio·fd·η).
- **Law (b), if there is no version 4.** Stateless kickdown: hold the top ratio while T_eco ≤ λ_kd·T_del(N_eco); otherwise N* is the smallest N with demand ≤ λ_target·T_del(N), with the same fallbacks.
- **The converter is locked**, as declared for the Supra (`engine_env.py:417-425`).
- **On the locked climb (arith.)**, the Accord needs about 100.6 kW at the engine at η 0.92 (97.4 kW at η 0.95) against a 130 kW rating, so it will likely sit on the power-limited branch. This is reported by §5.9's delivery check.

### 7.4 C1–C5

- **C1 (identity, 1e-6; MD:805-813).** `road_force_n(v, 0, rho=ρ_ref)` with m·a = 0, at 15, 20, …, 115 km/h, against A + B·mph + C·mph² computed independently in lbf and mph and converted with exact factors (`engine_specs/cars/README.md:82-83`). Above 115 km/h, and the 130 km/h climb, is not covered.
- **C2 (identity, 1e-6; MD:815-818).**
  - gears, final drive and CVT range equal the published values (`cx9_2016_25t.toml:21-26, 35-40`; `f150_2015_27tt.toml:24-29, 44-49`; `accord_2018_15t.toml:25-30, 39-44`);
  - mass = ETW × 0.45359237;
  - r = 26.8224 × top × axle/(2π × N/V), recomputed independently: CX-9 0.370346 (axle 4.41, N/V 30.5: "0.3704", MD:816); Accord 0.328616 (0.405, 5.36, 28.2); F-150 0.374992 (0.69, 3.31, 26) (arith.);
  - the model's implied top-gear N/V is reported beside EPA's;
  - the radius never comes from D3 (MD:816-818).
  - **Control:** a 1e-5 change to A fails C1; 4.411 in place of 4.41 fails C2's radius.
- **C3, C4:** §6.5.
- **C5 (a rule, applied by the roads step; MD:898-904).**
  - For every scored-climb step, the held gear's demand, and every rejected higher gear's, must sit more than max(1.9 %, |E1a| + 2u_val) from `shift_ceiling_nm(rpm)`, the threshold the code applies (`engine_env.py:507-510`). The `SHIFT_RPM_MAX` hold is checked too (`:586-595`).
  - The CVT's clause is decision 39(c) or law (b).
  - Order against the held-out E1a: decision 64.
  - This step supplies `c5_margin(plant, cycle)` and its test.

### 7.5 The cars' typed and converted values

| field | CX-9 | Accord | F-150 | label (source) |
|---|---|---|---|---|
| mass, kg | 2041.166 | 1587.573 | 2154.564 | converted: ETW 4500/3500/4750 lb (`cx9:68`, `accord:72`, `f150:60`) (arith.) |
| A, B, C (SI) | 179.899, 2.58073, 0.586931 | 194.610, −6.01202, 0.582947 | 100.307, 3.89060, 0.698246 | converted (`cx9:69-71`, `accord:73-75`, `f150:61-63`) (arith.) |
| wheel_r, final_drive | 0.370346, 4.411 | 0.328616, 5.36 | 0.374992, 3.31 | converted / PUBLISHED |
| driveline_eff | 0.92 | 0.92 | 0.92 | ASSUMED, CARRIED (`a90_supra.toml:21`); E6 row 10. The coast-down targets already hold driveline drag (`README.md:84-88`), so the demand is also reported at 0.95 |
| peak_torque_nm | decision 43 | — | 508.4 (375 lb-ft) | F-150 PUBLISHED (`f150:95`) |
| shift_load, upshift_min_rpm | 0.75, 2000 | — | 0.75, 2000 | ASSUMED, CARRIED (`a90_supra.toml:23, 25`); not D3 |
| shift_rpm_max | = rpm_max | — | = rpm_max | DESIGN: never hand back a gear outside the calibration |
| rpm_min, rpm_max | 1300, 5000 | 1000, 5000 | 1000, 5500 | DESIGN: the lowest and highest calibration lines (JSON `lines`; ch:2, 24, 63; mistake 6) |
| CVT: λ_cvt, cvt_rpm_min | — | 0.75, 1000 | — | ASSUMED (the Supra's `shift_load`) / DESIGN (the lowest line); not the strand's D3-derived 1250 |
| table_rpm_lo/hi/step | 1300/5000/100 | 1000/5000/100 | 1000/5500/100 | DESIGN |
| table_t_amb, table_t_block, table_settle | 315, 365, 30 | same | same | DESIGN; ASSUMED, CARRIED; ASSUMED, CARRIED (`a90_supra.toml:37-39`) |
| [scenario] grade, v_kmh, t_amb | 0.12, 130, 315 | same | same | DESIGN (`a90_supra.toml:47-49`); decision 44 |

### 7.6 The deliverable-torque table

- **Measurement:** §5.9 item 1. It is DERIVED, written to the derived file after the freeze from no EPA data, and checked against a fresh measurement by `test_epa_plants.py`.
- **Descriptive comparison** against the measured WOT nodes on calibration rows, which are transient peaks (MD:433-437).
- **The knock-flag duty during its measurement** is reported (decision 51).

### 7.7 The K3 knee (decision 33, VD:156)

§5.9 item 4. `test_k3_knee.py` checks it two ways:

- On the B58, the lifted `baseline_trace` plus `knee_for` reproduces `results/ENGINE_THRESHOLDS/ecu/k3_lam-0.02.json` and `k3_spark-0.75.json` `knee_k`, with `BaselineECU.step` patched exactly as `ecu_shift.py:70-78`.
- The B58's nominal trace gives `time_above_knee_s` 413 at 1123 K.

---

## 8. Everything this step writes, and the documents

### 8.1 Files created

| path | what it is |
|---|---|
| `engine_specs/{mazda_25t,honda_l15b7,ford_27tt,cx9_2016,accord_2018,f150_2015}.toml` | the six typed specs |
| `epa_rows.py, epa_stats.py, epa_fit.py, epa_freeze.py, calibrate_epa.py, k3_knee.py, epa_coefficients.py, validate_epa.py, d3_rows.py` | the scripts |
| `test_fuel_forms.py, test_cars.py, test_carried.py, test_contract_pinned.py, test_epa_rows.py, test_epa_stats.py, test_epa_fit.py, test_epa_freeze.py, test_k3_knee.py, test_epa_coefficients.py, test_validate_guards.py, test_epa_plants.py` | the tests |
| `data/engines/<id>/derived_params.json` | three files, written by `calibrate_epa.py`, never by hand (CL:127). Allowed beside the `epa_*` files (`test_epa_map.py:394-401`) |
| `results/EPA_CALIBRATION/<id>/` | `stage0.json, fit_<form>.json, in_sample.json, freeze.json, e6/row{1,2,3,7_090,7_110}.json, complete.json, run.json` |
| `results/EPA_VALIDATION/<id>/` and `summary.json` | §6.6 |
| `results/B58_IDENTITY.{md,json}` and `certificate_tools.tar.gz` | the new certificate |
| (version 4) | `thresholds/contract.py`, `thresholds/document_template.md`, `results/ENGINE_THRESHOLDS.{json,md}` |

- **Numbers live in `.json`.** That is not scanned by `verify_docs.py` (`verify_docs.py:189-190`).
- **Printouts** go to `.txt` only if `RETIRED_EXEMPT_RESULT_TABLES` (`verify_docs.py:929-930`) is extended to `results/EPA_(CALIBRATION|VALIDATION)/.+\.txt`. That change is followed by `drift_test.py` (CL:108).

### 8.2 Files changed

- **The plant:** `plant.py`, `thermal.py`, `engines.py`, `engine_env.py`, `derived.py`.
- **B58-only scripts and guards:** `car_thermal.py`, `calibrate_thermal.py:154`, `model_vs_data.py:376`, `make_page.py:1325, 1413`, `wide_air.py:211`, `fingerprint.py:439`, `train.py:485`, `train_all.py:94`, `run_phase_d.py:247`, `evaluate.py:422`.
- **Tests:** `test_engine_threading.py`, `test_plant_guards.py`, `Explanatory Simulation/tests/test_catalog.py:97`.
- **Specs:** `engine_specs/b58.toml`, `engine_specs/a90_supra.toml`.
- **Documents:** `results/VALIDATION_DECISIONS.md` (section H), and §8.5's.

### 8.3 The hash rules

- **sha_text** (CRLF read as LF) for the contract, every code file, every `results/` output and every spec (`thresholds/common.py:37-43`).
- **Raw sha256** for the EPA tables, `epa_engine.json`, `epa_channels.csv` and the D3 files (`:27-34`).
- **`derived_sha` plus sha_text** for derived files (`fingerprint.py:349-367`).
- **engine_sha** for values as built (`engines.py:591-596`). It covers the converted car values, so the published car files need not join `plant_files`.
- **`frozen_sections_sha256` and the dump hash**, as §5.8.

### 8.4 How the contract is verified once `--check` can no longer pass

`test_contract_pinned.py` checks:

- both contract files' sha_text equals the blobs at the contract commit (`ef5e14e`, or version 4's) and `freeze.json`'s record;
- that commit is an ancestor of `calibrate_epa.py`'s first commit (`git merge-base --is-ancestor`);
- JSON `generators.sha256` equals the generator files;
- JSON `generator_inputs_sha256` equals `results/ENGINE_THRESHOLDS/*`;
- **control:** a one-byte change in a copy is caught.

The documented manual check is `git worktree add <scratch>/cwt <commit> && (cd <scratch>/cwt && $PY engine_thresholds.py --check)`. It needs git (MD:1208-1210) and the data folder.

### 8.5 Documents (WP7)

**CHECKPOINT.md:**

- **The header** gains the new B58 plant_sha and engine_sha (derived_sha unchanged) and the certificate.
- **Verified state:** replace `:44-47` (`--check`) with §8.4. Add one line per engine: its frozen form, derived_sha, knee and delivery result, naming the commands that prove them.
- **In progress** (`:69-74`) and **next actions 8** (`:107-114`):
  - the roads step and `EPA_TIGHTENINGS.json`;
  - the validation (arm, then run);
  - schema 4 before any EPA engine trains;
  - the preregistration (row 13, the Ford's TIT-cap row, the load-bearing constants, coverage, knock both ways);
  - L8 and the dump comparison on the device.
- **Size:** the file must stay within 150 lines (`verify_docs.py:1158`). Everything replaced moves verbatim to `STATE_HISTORY.md`, never deleted.

**Other documents:**

- `README.md`: the layout (new modules, specs, `results/EPA_*`) and the figure-command table.
- `results/README.md`: entries for EPA_CALIBRATION and EPA_VALIDATION.
- `engine_specs/cars/README.md:18-21`: "read by nothing yet" becomes "read by `engines.published_car`".
- The `engine_env.py:1281` docstring ("decision 34 keeps that for every car") is corrected, leaving the drift anchor `"12 % at 130 km/h, 42 C"` intact.
- `REFERENCES.md`: the carried ASSUMED values point to their B58 entries.

**Mistake 11:**

- Grep for `ded8da308863d394` and `99d2a9658b1258a7`. They appear at `CHECKPOINT.md:5`, `test_catalog.py:97`, `B58_IDENTITY.md:31, 33, 118` and `STATE_HISTORY.md:4207, 4236`.
- Read every hit. The certificate is replaced, and the build-step-1 page moves verbatim to STATE_HISTORY.
- Whether hashes go into `verify_docs.RETIRED` is decision 67. Then run `drift_test.py`.

**The contract's follow-ups** (the contract itself is never edited):

- **Done by this step:** Jad's column; the K3 knees (decision 33); each engine's own coefficients (MD:229-231).
- **Handed on, recorded in CHECKPOINT:**
  - the roads and the tightenings (`order_of_work[2]`);
  - the held-out run (`[3]`);
  - the tables and S1/S2 (`[4]`);
  - the preregistration (`[5]`), with the 850 °C row per engine, knock both ways, the coverage flags, E6 row 13, the load-bearing constants and the Ford's TIT-cap row;
  - S2b and training (`[6]`);
  - schema 4, with H and both backends (MD:912-913; CHECKPOINT.md:113-114).

---

## 9. Decisions for `results/VALIDATION_DECISIONS.md` section H, and every ASSUMED value

### 9.1 Decisions, numbered from 39

Each has a Ghassan column and a Jad column.

**Before WP1 (the plant commit)**

| # | decision | options | recommended, and why |
|---|---|---|---|
| 39 | **Contract version 4**, generated after commit A and before any script naming the tables (WP2) | (i) v4 with: (a) E8 computed in-sample and reported, but out of the cycle-form criterion; (b) the neutral-action identity at the policy path's float32 representation, with no clip binding; (c) if 40(a), C5's CVT clause replaced by "N* at demand ±max(1.9 %, \|E1a\| + 2u_val) stays inside the ratio window and below the speed of maximum deliverable power"; (ii) no v4: E8 counts literally (A+B+C+D forced if it fails in-sample), (b) as a VD ruling, CVT law 40(b) | **(i).** Three rules cannot be met or mean nothing as written, and this is the last moment rule 0 lets them change (MD:42-44). (a) No form can move E8: its inputs are the ECU fit alone (MD:773-776). (b) No engine, the B58 included, can be bit-exact (§3.4). (c) The economy law sits on λ·T_wot, so C5 fails by construction, and the CVT has no discrete gear for C5 to protect (MD:901-903) |
| 40 | **The Accord's ratio law** | (a) economy line, λ_cvt 0.75 ASSUMED, with the low-speed branch and power fallback (§7.3); (b) stateless kickdown, λ_kd 0.75 ASSUMED and λ_target 0.65 DESIGN | **(a) with v4.** Its form is the one the only evidence supports (C4, in-sample, descriptive, MD:889), it has one parameter, and no discontinuity is invented. (b) if v4 is declined: it keeps C5 literal and meaningful. Neither uses the strand's fitted values (MD:449-452) |
| 41 | **Form D's cam** | (a) run by the ECU (§2 P4); (b) in the plant at each evaluated MAP (needs v4) | **(a).** The contract says "run by the ECU" (MD:474; JSON "scheduled by the ECU"). The agent's boost lever then acts at a fixed cam, as it acts at a fixed spark (MD:690-694) |
| 42 | **Car conventions** | mass = ETW; road force (A + B·v)·cos θ + C·v²·ρ/ρ_ref + m·g·sin θ; ρ_ref from 98.21 kPa and 20 °C with R 287.0; radius from EPA's own row (the CX-9 with axle 4.41); the plant's final drive is the published 4.411; the F-150's 4750 lb SuperCab row; η 0.92 | **As listed.** Each identity holds against its own source at 1e-6; the scalings are declared physics. The axle and final-drive discrepancy (2.3e-4) is disclosed. Mass differs from the Supra's kerb mass, a cross-car difference that is disclosed |
| 43 | **Stepped-car gearbox and peak torque** | shift constants: the Supra's (ASSUMED) or D3-derived (committed script); CX-9 peak torque: open Mazda's MZ19 sheet (PUBLISHED) or the table maximum (DERIVED) | **The Supra's, ASSUMED; MZ19 opened**, the table maximum only if MZ19 prints none. D3 stays blind for C3 (MD:449-452). The peak torque sets the kickdown, `shift_ceiling_nm` (`engine_env.py:510`) |
| 44 | **The locked climb per car, and delivery** | (a) 12 %/130 km/h/42 °C for every car; delivery reported; if the tracking error exceeds `TRACK_TOL` on more than 1 % of climb steps, the knee is still set on that trace and flagged; (b) the same grade at the highest speed delivered, in 10 km/h steps, decided before any held-out statistic | **(a), with (b) pre-declared as the remedy if the team prefers** a delivered climb. K3's reference is "its locked climb" (VD:156); mistakes 5 and 17. The Accord asks about 77 % of its rating (arith.; MD:1354-1355) |
| 45 | **Borrowed B58 constants** | type them ASSUMED in each EPA spec with source "CARRIED FROM THE B58: …", registry-tested (§9.2); or read them at build time from the B58's file | **Typed, with the marker and `test_carried.py`.** EPA's rig cannot set them (MD:1329-1331). Visible in the spec, pinned to `326c0835548975e2`. Disclosed: the heat fractions carry about 2.5 % less heat per gram at 42.9 MJ/kg |
| 46 | **Load-loop gains** | the B58's per-Nm gains, or ×V_d,B58/V_d (Mazda 1.205, Honda 2.003, Ford 1.112 (arith.)) | **Scaled** (`ff_kpa_per_nm`, `p_gain`; DESIGN). The gains are per Nm (`b58.toml:145-151`); checked by tracking at neutral (§5.9) |
| 47 | **Training and scoring guard** | refuse EPA engines in `train.py`, `train_all.py`, `run_phase_d.py` and `evaluate.py` until schema 4 and a committed validation exist | **Refuse.** Registration in commit A would otherwise accept them under schema 3 (`train.py:485`), and `fingerprint.py:439` cannot record a CVT |
| 48 | **Re-runs at commits touching only EPA files** (`data/engines/**`, specs) | (a) PHYS's items 1–4 and the app suites, as the rule's paths say; (b) a written waiver, with fingerprint and harness `units` proving the B58 unchanged | **(a).** About 3 h; PHYS:2-10, :18-29 name the paths; mistake 25 |

**Before WP3 (the scripts are committed)**

| # | decision | options | recommended, and why |
|---|---|---|---|
| 49 | **Form scope** | one common form for the three EPA engines (the first at which every gating statistic of all three passes; the B58 stays A by decision 31), or one per engine | **Common.** Mistake 20 (CL:118) and the contract's citation of design.md:59, "one model form" (MD:1352-1353). Forms are nested and terms an engine does not need stay near neutral under the ridge. Cost: one engine's misfit adds terms to the others, which the held-out test then validates |
| 50 | **The estimator** | §5.2–5.6: stage order; R-scaled residuals; efficiency for burn and FMEP; all four FMEP terms; no holds; ridge w = 0.01 with declared scales; `least_squares('trf')`, three starts, the declared second attempt; pre-declared outcomes | **As §5.** The contract leaves the procedure open (g5), so it is fixed before any EPA output is seen. No holds keeps form A's fitted set (MD:461-463) |
| 51 | **The knock scale** | (a) geometric mean of KI over Final calibration rows = 1; (b) max KI = `knock_detect_ki` | **(a)**, the least-squares reading of "KI = 1 at the High Load Final spark" (MD:759). E6 row 7's 0.90 and 1.10 are then exact rescalings. Report KI's spread, the knock-flag duty on the climb and during the table, and the knock share. `knock_detect_ki` stays carried: moving it is a separate step (VD:115) |
| 52 | **Back-pressure and TIP below the barometer** | keep all rows, report the count, refit without them as a reported sensitivity; exclude them; a barometer-referenced floor (form change, v4) | **Keep and report.** Exclusion selects on the outcome. The law is fixed (MD:461-463; `plant.py:334`). The barometer coverage flag is reported |
| 53 | **Boost envelope; HD1's barometer** | §5.2 S3c; HD1 at Cell 9's 97.6 kPa (UNVERIFIED), swept over 97.2–98.6 | **As stated.** The in-use ceiling never exceeds measured MAP (PF-5; mistakes 6, 9). HD1 has no barometer column (ch:24-43) |
| 54 | **Missing λ, the sentinel, the Honda floor** | a fired row without λ runs at λ 1.00, flagged, and statistics are also reported without it; a fired sentinel row stops before statistics; censored Final rows (≥ 2 at the minimum) are kept, one-sided in S3b, flagged in E4a/E4b | **As stated.** It keeps the contract's populations (`split.py:113-126`). Steady rows are closed loop (MD:504-505). Mistake 7 |
| 55 | **In-sample gaps** | a statistic with no deciding calibration line neither blocks nor passes | **As stated.** There is no fallback in MD:478-481; absence of evidence is not a failure |
| 56 | **u-terms** | §6.2. EPA's instrument pages are opened before the fit and each channel's stated accuracy recorded (or "none stated") | **As stated.** The contract's own rules (MD:549-568), applied uniformly; no resolution from `repr` digits (RF-6) |
| 57 | **Statistic details** | D1 pre-scan, bisection 1e-3 kPa, nearer-bound evaluation, also reported without unreachable rows; E8 unsnapped, linear extrapolation flagged, the steeper slope at 0, the tightening keeps the signed larger \|·\|; the worst line reports, every line labels | **As stated.** `thresholds/contract.py:71-99`; MD:709, 773-781; VP:319-324 |
| 58 | **MAP extrapolation of held-out populations** | flag per row; report each statistic restricted to calibration MAP coverage beside it; no relabel | **As stated.** The interior rule is in rpm only (MD:350-352); mistake 6 |
| 59 | **E6 readings** | refits before held-out at the frozen form; row 1 offset only; row 12 no snap, no refit; d-row probes ±10 %; "the worse" = off > untested > limited > validated; Tests lists: E1 {burn, FMEP, back-pressure}, E2 {VE}, E3 {UA_PORT, burn, back-pressure}, E4a {UA_PORT, rich slope}, E4b {rich slope, flame terms}, D1 {VE, burn, FMEP, back-pressure}, L0/L1 {UA_PORT, back-pressure, VE, burn}, E8 none (never excluded), C3b/C3d {VE, η} | **As stated.** MD:605-606, 621-622, 634-635 give E1–E3. The others are needed because a row excluded for its whole list drops the engine (MD:739-740, 1007-1009) |
| 60 | **Run-once mechanics** | §6.1 (ARMED commit; counts only; atomic writes; re-execution only with armed code and nothing written; otherwise the defect route) | **As stated.** "Computed once" (MD:482-483) protects against adjusting after seeing |
| 61 | **Interpreter and device** | calibrate and validate on this laptop's venv (3.13.2, `requirements-lock.txt`); re-make the frozen-plant dump on the training device and record the comparison | **As stated.** CL:89 is amended by VD:155; cross-machine identity is recorded, not required |
| 62 | **The Ford's TIT-cap row** | specify now as an ECU variant outside the frozen form (enrich by the least amount holding model TIT ≤ a cap; the cap value set in the preregistration) | **As stated.** VD:132; MD:786-788 preregister it; mistake 3 |
| 63 | **C3/C4's unpinned inputs** | the D3 summary file hashed and recorded at run time; the D3 fuel's AFR_st = 14.559, its difference in u_D (unsourced); dwell from the PCM MAP trace; cell temperature from the test metadata; the Accord's D3 files pinned at run time against `MANIFEST.csv` | **As stated.** The contract pins only the 43 CX-9 files (JSON `d3_files_c3`) |

**Before the roads step and the arm commit**

| # | decision | options | recommended, and why |
|---|---|---|---|
| 64 | **C5 against the held-out E1a** | draw the roads at 1.9 %; after validation, re-check scored climbs at max(1.9 %, \|E1a\| + 2u_val) of the worst line and redraw failures from a pre-declared seed stream before the preregistration, the tightenings standing | **As stated.** MD:726-728 and :898-904 conflict as written; the tightenings must precede any held-out statistic |
| 65 | **Waive the tightenings to validate sooner?** | no; yes (a v4 change) | **No.** JSON `order_of_work[2]` before `[3]` |
| 66 | **The replacement for `--check`** | §8.4 | **As stated.** `thresholds/document.py:489-492` makes `--check` fail once `calibrate_epa.py` exists |
| 67 | **Mistake 11 for hashes** | add the old plant_sha and engine_sha to `verify_docs.RETIRED`, with history exempt; or grep and update only | **Grep, update, move the old certificate to STATE_HISTORY**; RETIRED is for figures, the team's call |
| 68 | **CLAUDE.md:137** (already open: BI finding 9) | name `engines.py` and `engine_specs/` | **Name them**, as PHYS:2-10 already does |

### 9.2 Every value labelled ASSUMED, with its source

The same set applies to all three EPA engines unless noted. "CARRIED" means the value is bit-equal to the B58's, and `test_carried.py` checks the marker and the value.

| field(s) | value | source |
|---|---|---|
| geometry `conrod` | stroke × 0.1444/0.0946 (Mazda 0.152615, Honda 0.136463, Ford 0.126693 (arith.)) | the B58's ratio; `b58.toml:34` records no source; E6 row 9 |
| `ivc_deg`, `evo_deg` | −140, 140 | `b58.toml:37-38`; E6 row 9 |
| `fres_*`, `t_head_k`, `port_pickup_k`, `t_residual_k`, `flame_*`, `burn_res`, `delay_res`, `n_poly`, `cp_exh` | the B58's | `b58.toml:49-66, 74, 82`; shared (MD:464-465); E6 row 9 |
| `octane` | Honda 96.1 | CATALOGUE.md:166 via MD:1335; absent from its `alpha_fuel`. Mazda and Ford 97.6 are PUBLISHED (FTAG 26864's `alpha_fuel`); HD1's batch identity is UNVERIFIED (two report files). Absorbed by `knock_a` |
| `rise_k`, `block_coupling` | 12 K, 0.06 | `b58.toml:88-89`; only C3 tests them (MD:830-832) |
| `inlet_sea_kpa` | 99.3 | `b58.toml:92` |
| `iat_gain, iat_ref_c, iat_max, cold_k, cold_retard` | 0.16, 25, 9, 340, 5 | `b58.toml:108-112` |
| `knock_step, knock_max, knock_restore, knock_detect_ki` | 3, 12, 0.35, 1.0 | `b58.toml:113-116` |
| `fan_hi_k, fan_lo_k, fan_lo_duty` | 372, 367, 0.4 | `b58.toml:117-119` |
| `enr_dwell_lo, enr_dwell_hi` | 1.5, 3.0 s | the B58's DERIVED values (`data/derived_params.json` `enrichment`); E6 row 13 |
| `c_turb, ua_gas_turb, ua_turb_amb` | 6000, 0.90, 18 | `b58.toml:122, 124-125`; VD:132; E6 row 4 |
| `n_turbines` | Mazda 1, Honda 1, Ford 2 | until a source is opened: Ford from decision 24's "twin-turbo" (VD:132) and its reports' Figure 2 (`logs/epa/README.md:106-111`), UNVERIFIED; per-turbine housing as `thermal.py:268` (doubles the Ford's capacity, disclosed) |
| the 15 block, oil, radiator and thermostat fields | the B58's DERIVED doubles | `data/derived_params.json` `thermal`, derived_sha `326c0835548975e2`; EPA held coolant and oil (MD:1329-1331) |
| `egt_limit_k` | 1223 | `b58.toml:140` |
| car `driveline_eff`, `shift_load`, `upshift_min_rpm`, `table_t_block`, `table_settle`; CVT λ_cvt | 0.92, 0.75, 2000, 365, 30; 0.75 | `a90_supra.toml:21, 23, 25, 38, 39` |
| B58 additions: `[fuel]` 44.0e6 and 14.7; `ce_rich_slope` 0.65 | — | `plant.py:42-43, 59` on cf43fbb; REFERENCES.md:433 |

**Not ASSUMED:**

- Typed PUBLISHED: bore (89.0, 73.0, 83.0 mm); the Honda's and Ford's stroke (89.4, 83.0); `n_cylinders`; geometric `comp_ratio` (10.5, 10.6, 10.0) (`epa_engine.json`).
- DERIVED_ONCE:
  - the Mazda's stroke, 0.0999817 m, from 2.488 L and 89 mm, because EPA asserts none (`geometry_notes`);
  - `afr_st`: 14.559, 14.554, 14.559 (HD1) (JSON `fuel_by_table`; `thresholds/contract.py:54-58`);
  - `lam_floor`: 0.684, 0.610, 0.698 (JSON `lambda_clip_floor`).
- PUBLISHED LHV: 42.908, 42.898, 42.908 MJ/kg.
- DESIGN: `ve_lo`/`ve_hi` 0.30/1.30, `spark_ref_kpa` 40, `lam_ceiling` 1.25, the damage valuations (`b58.toml:133-139`), the loop settings, and the B58's neutral form values.

---

## 10. Risks, and what happens if the in-sample stage fails at A+B+C+D

### 10.1 Risks and their mitigations

| risk | mitigation |
|---|---|
| The generator's step 7 locks version 4 out once a table-naming `.py` or `calibrate_epa.py` exists (`thresholds/document.py:489-492`) | WP2 before WP3; table names come from the JSON |
| A B58 bit moves | sub-steps with the units job; §3.5's controls; engine_sha over the old fields; the full certificate; no PLANT_CODE edit after commit A |
| Non-identifiable constants | profiled stages, the ridge, prior-dominated flags, T0, rows behind each constant; E6 row 9 reports what an unidentified constant is worth |
| Knock feedback live by construction | reported (decision 51); the same as the B58 (`b58.toml:100`; `k3_nominal.json`) |
| The Accord cannot deliver the climb | §5.9's check; decision 44 |
| Boost or VE extrapolated in use | the MAP-referenced envelope; in-use clip contacts and MAP above the calibration range flagged |
| Missing λ, the sentinel, the λ floor, the TIP offset | stage-0 counts; decisions 52 and 54 |
| `verify_docs` false positives in new code or printouts | JSON outputs; no retired literals; the exempt-regex extension plus drift_test |
| CHECKPOINT over 150 lines | move text verbatim to STATE_HISTORY |
| A second held-out computation | §6.1 |
| Plant code changed between freeze and validation (the roads step) | the frozen-plant dump and the in-sample re-run guard (§6.1) |
| A training-device mismatch | decision 61; L8 there |
| The team's end date (23 November, VD:132) | Run 1 is about 1 h pooled; the plant commit's re-runs (about 5–6 h wall) and the roads step are the long poles |

### 10.2 If the in-sample stage fails at A+B+C+D

1. **Rule out a coding defect before freezing.**
   - T0 passes.
   - The shortcut-equals-plant assertions hold.
   - Counts and populations reproduce.
   - A defect is a disagreement with this committed specification. It is fixed, and the calibration re-runs from S0, with both runs logged.
2. **Then follow the contract literally.** Freeze A+B+C+D and report every failing statistic per line (MD:480-481). No new form, no held constant and no refit (rule 0, MD:42-44, 1055-1058). A form E would be a new contract, disclosed, with every result reported under both.
3. **Report residual structure as descriptive** (mistake 20: suspect the form): per line and per MAP band, the residuals against rpm and against MAP.
4. **Run the held-out stage once anyway** (MD:482-483) and apply section 7.
   - A failing level row only labels the 850 °C row.
   - A d row reading off, or with no statistic, drops the engine. That is recorded in VD with the date and the row, and amends decision 24 (MD:1047-1049).
   - If only the Mazda survives, the collapse compares the B58 and the Mazda. If no EPA engine survives, the four-engine test does not run, and the failed validations are reported as results (MD:1051-1053).

**Not verified here:**

- whether any λ-less or sentinel row is fired;
- how many Honda Final rows sit at λ 0.61;
- the TIP deficit's size and which rows carry it;
- any source for the turbocharger counts or the CX-9's peak torque;
- EPA's sensor accuracies (the PDFs are unread);
- the EPA engines' injection type (`plant.py:167-170` assumes direct injection);
- every runtime in §5.11, which is arithmetic from measured per-call costs;
- the 1970 s harness time, the plant map's 56 780 count and the lab and app times (map).
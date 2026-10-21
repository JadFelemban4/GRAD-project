<!-- RETIRED-OK: file -- a dated design record, kept as written by the review workflow of 22 October 2026 and never edited, only superseded; its runtimes and counts are design-time estimates, not figures of the project. verify_docs.py reports it as skipped on every run. -->
> **What this is.** The adversarial review of `PLAN.md` (beside this file), through five lenses (the B58's identity, fidelity to the contract, held-out isolation and run-once, the fit's feasibility, the cars and the environment), consolidated on 22 October 2026 by AI agents, read-only. **These amendments govern wherever they differ from the plan.** Section 3's decisions are `results/VALIDATION_DECISIONS.md` section H. Paths into a `scratchpad` folder are the session's own working files, not kept. Nothing was fitted, and no value of any EPA row was read.

# Amendments to the build-step-2 plan (`build2_plan.md`)

**Basis.**
- The tree was read-only at HEAD `1787d98` (clean). I read the plan whole, and checked every lens claim I rule on at the file:line it cites.
- Scratch files are under `C:\Users\badcl\AppData\Local\Temp\claude\c--Users-badcl-Desktop-GRAD-project\14077827-1e2d-4826-b805-20b70e9c81f2\scratchpad\plan_review\`:
  - `amend\f32_amend.py`: the NumPy 2.5.3 checks of float32 and NEP 50.
  - `amend\cert\`: the certificate archive, unpacked. Its sha256 is `a639190b…01503fb`, re-hashed.
- I re-ran four scripts. Each uses synthetic B58 points, the published car files only, or no project data:
  - `fitlens\s4_ident.py`: corr(burn_base, delay_base) −0.9980 and corr(burn_rpm, delay_rpm) −0.9968. Profiled condition number 1.85e4. Burn and delay information against the ridge is 24–28×.
  - `fitlens\time_b58.py`: 10.46 ms per call serial. A pool of 16 gives 1.89 ms wall per call (5.5×); a pool of 20 gives 1.80 ms. The CPU is an i9-12900H, 14 cores and 20 threads.
  - `cars\arith.py`.
  - `audit_spawn.py`: the parent's audit hook saw the worker's open: False. The subprocess's open: False. Its own open: True.
- **What I did not do or read:**
  - No EPA table was opened beyond its header.
  - No `held_out_rows` record, no `split.json` row record and no ALPHA curve value was read.
  - From `epa_channels.csv` I printed only the name, unit and status columns.
  - Nothing was fitted.
- **One disclosure.** The committed contract text itself prints all-row TIT ranges and maxima (MD:534-536; `thresholds/contract.py:636`). I saw them while reading and used none of them.

Severity: **15 must-fix and 53 should-fix** amendments. None of the five lenses' issues was dropped. Section 1.H lists the ones I corrected.

---

## 1. Amendments

### A. Order of work, the decision sheet and version 4

**A1 · must · Decisions that read a contract rule are scheduled after the last moment a version can be written** (contract MF-1, SF-11; leak SF-4)
- **Verified:**
  - Step 7 stops once `calibrate_epa.py` exists, or once a non-generator `.py` names the tables (`thresholds/document.py:489-492`). It counts untracked files (`:169-180`) and raises SystemExit (`:534-542`).
  - Both `--build-only` and `--check` run step 7 (`engine_thresholds.py:126-134`, `:149`).
  - The plan has decisions 49–64 "before commit C" (plan:140-142), but version 4 is commit B (plan:88, :269).
  - The §4.4 pre-checks and T0 run before commit C (plan:305-309). That contradicts plan:89 and `order_of_work[1]`, "calibrate_epa.py, committed before it runs" (`thresholds/contract.py:626`).
- **Section:** §2 WP0, WP2, WP3; §9.1 group headers.
- **Change:** regroup WP0 as in section 3 below.
  - **G1, before WP1:** 36–38 (Jad), 39–48, 61, 67, 68, 69.
  - **G2, before WP2 (version-4 text):** 49, 54, 55, 57, 58, 59, 64, 65, 70, 71. Answer G2 at the same sitting as G1, since WP2 follows commit A directly.
  - **G3, before commit C:** 50–53, 56, 60, 62, 63.
  - WP3 commits C first. §4.4/S0 then runs as the first step of Run 1, and T0 as its own step on committed code. A T0 failure is a coding defect with a logged fix commit (§5.6).
- **Check:** WP2 starts only when the G1 and G2 columns are filled. `git log` shows commit C before any `stage0.json` or T0 output.

**A2 · must · WP2's trigger omits Jad's differing answers** (contract MF-2)
- **Verified:** plan:88 and :269 make WP2 conditional on decision 39 alone. MD:1103-1105 says a differing Jad answer to 36–38 "is applied before it, in this file's generator, as a new version". Jad's column is empty (VD:170-172).
- **Change:** WP2 runs if decision 39 = (i), or if any Jad answer to 36–38 differs. A different b goes through `N_SHARES` (`thresholds/contract.py:27`), and `--build-only` recomputes every R from the saved step outputs. Decision 39 recommends (i) anyway (section 3).
- **Check:** WP0's checklist names both triggers.

**A3 · should · Version 4's text and checks** (b58 SF-14; contract SF-10; one item is mine)
- **Verified:**
  - `thresholds/document_template.md` carries 27 code citations. These include `plant.py:42`, `:43`, `:54-60`, `:63-66`, `:160`, `:163`; `thermal.py:245` (three times); `engine_env.py:982` (twice) and `:1006`. `thresholds/contract.py` cites `plant.py:42`, `:43`, `thermal.py:245`, `engine_env.py:982` and `:1006`. WP1 deletes or moves all of these.
  - The regenerated MD is scanned by `verify_docs.py`, which already guards a false positive on it (`verify_docs.py:719-722`).
  - **Mine:** `--build-only` also rewrites `results/ENGINE_THRESHOLDS/contract.txt` and `document.txt` (`common.printout(write=True)`, `engine_thresholds.py:126`, `:131`; `thresholds/common.py:79-87`). These are tracked `.txt` files that `verify_docs.py` scans (`verify_docs.py:189-190`). So plan:281's "the step outputs … do not move" is wrong for those two printouts. The 28 hashed step outputs do not move.
- **Change:**
  - WP2 remaps the template's and `contract.py`'s citations to the post-commit-A lines (or cites symbols).
  - It writes the G2 answers as rule text (decision 39).
  - It runs `verify_docs.py`, plus `drift_test.py` if the guard is touched, and commits the two printouts.
- **Check:** `--check` exits 0. `verify_docs.py` passes. A citation scan resolves every `file:line` in the regenerated MD against the commit-A tree.

### B. WP1 and the B58's identity

**B1 · must · The `lam_floor` control cannot come out DIFFERENT** (b58 MF-1)
- **Verified:**
  - H perturbs by one float64 ulp (`tools/harness.py:45`, `:49-50` in the archive).
  - `lam_b + act[1]` is float32 (`engine_env.py:698-699`, `:939-950`, `:1006`), and NEP 50 casts a Python-float bound to float32.
  - `amend\f32_amend.py`: `float32(0.70) == float32(0.7000000000000001)`. A float32 step (0.7000000476837158) changes the binding output from 0.699999988079071 to 0.7000000476837158.
  - An `np.float64` bound returns float64 0.7, which would move B58 bits.
  - The floor binds at 1 of 1,099 steps in `extremes:double:12:random` (`b58_lens\bind_*.txt`). It binds at 0 in the 9 other random-policy jobs checked; `rr:120.0:0.16:random`, `rrwrap:7:3` and `wideseq:9:4:120` were not checked.
- **Section:** §3.5; WP1 P2; `test_fuel_forms.py`.
- **Change:**
  - Perturb `ecu.lam_floor` by the float32 step through a candidate-side harness mode, on `extremes:double:12:random`, which is already in `jobs_ctl.txt`.
  - First print the count of steps with `info["lam"] == float32(lam_floor)` (1 at HEAD), so the control fails for the right reason.
  - The bounds stay Python floats. `test_fuel_forms.py` asserts `type(ecu.lam_floor) is float` and the same for `lam_ceiling`.
- **Check:** the control reads DIFFERENT at exactly the binding step. The bind count is printed beside it.

**B2 · must · §3.5's IDENTICAL and DIFFERENT form controls cannot run, or cannot fail, as specified** (b58 MF-2, SF-7; two items are mine)
- **Verified:**
  - H's units job calls `map_from_airflow` (`harness.py:157-159`), which P3 refuses for forms other than A (plan:187). It also calls `run_cycle` and `predict` without a cam (`harness.py:130`, `:139`, `:146`), and VE refuses None for a D engine (plan:202).
  - `wide_air.py:149` and `:182` also call `_track_torque` without a cam, and a `wideair` job is in `jobs_ctl.txt`.
  - H's per-record `replace` (`harness.py:47-50`) would trip `cam_on == ("D" in form)` and P3's own refusals before the companion field can be set.
  - **Mine (1):** `HARNESS_PERTURB=cycle.ce_rich_slope`, the b58 lens's proposed control, raises on the B58. P3's `CycleCal.__post_init__` refuses `ce_rich_slope != 0.65` without C (plan:180).
  - **Mine (2):** "`ve_cam=1e-4` (with the ECU cam on) → DIFFERENT" (plan:414) reads IDENTICAL. With the B58's twelve schedule fields at 0.0 (plan:210), `cam_deg` clamps its inputs to a [0,0] domain and its output to [0,0], so the cam is 0 = `cam_ref_deg`, and `ve_cam·(cam − cam_ref)` is exactly 0. That repeats mistakes 12 and 25.
- **Section:** §3.5; WP1 tests (`test_fuel_forms.py` "on H's units grid"); §3.6 item 2.
- **Change:** a recorded candidate-side `HARNESS_SET` mode that sets `cycle.form`, `ecu.cam_on` and the companion values in one `Engine` replace. The units job passes `cam_deg=BaselineECU(eng.ecu).cam_deg(rpm, map)` to `run_cycle` and `predict`; this is None under form A, so the A path is byte-identical. It skips the `map_from_airflow` block for forms other than A, recorded as by design. The controls:
  - **IDENTICAL:** A+B at `ve_map` 0; A+B+C at 0.65; A+B+C+D with zeros. Run each on units plus `terrain:single:11:neutral`, never on `wideair`.
  - **DIFFERENT:** A+B with `ve_map` 1e-4.
  - **DIFFERENT:** A+B+C+D with `cam_on` 1, `cam_c0` 10, domain [800, 7000] × [20, 260], clamp [−60, 60] and `ve_cam` 1e-4. Pair it with `ve_cam` 0 on the same schedule, which must read IDENTICAL.
  - **DIFFERENT:** A+B+C with `ce_rich_slope` one ulp above 0.65, via `predict` at λ 0.95 (`harness.py:139`). One ulp is invisible at λ 0.70, 0.85 and float32(0.81), and visible at 0.95 (`f32_amend.py`).
  - `test_fuel_forms.py` builds its grid the same way.
- **Check:** each control lists its jobs and expected outcome. The reference side (`NEW` False) of every tool stays byte-identical (BI:47-49).

**B3 · should · The quick loop never runs `step()`** (b58 SF-1)
- **Verified:** the units job builds the environment only for `MAP_CEIL_KPA` and `_map_for` (`harness.py:233-236`). P2 edits `engine_env.py:1006` and P4 edits `:982-1007`.
- **Change:** from P2 on, add `extremes:double:12:random` and `terrain:single:11:neutral` to the quick loop's jobs (plan:427).

**B4 · should · P3 uses names only P4 creates** (b58 SF-2)
- **Verified:** P3 passes `cam_deg` and adds a `ve_cam` term (plan:182-186). `cam_deg`, `ve_cam` and `cam_ref_deg` arrive in P4 (plan:195, :202).
- **Change:** in P3, VE is `volumetric_efficiency(rpm, map_kpa, *, engine)`. P4 adds `cam_deg`, the D term and its two fields (CL:141-142).

**B5 · should · WP7 edits PHYS paths after commit A** (b58 SF-3; cars SF-3)
- **Verified:**
  - plan:1035 edits the `engine_env.py:1281` docstring. This is a PLANT_CODE file (`fingerprint.py:109`); `plant_text_sha` moves (`:431`) while the code-only `plant_sha` does not (`:160-244`).
  - plan:1034 edits `engine_specs/cars/README.md:18-21`, an `engine_specs/**` path (`.claude/rules/physics.md:2-10`, `:18-29`).
  - The four car TOMLs also say "Read by nothing yet" (`a90_supra_2020.toml:6`, `cx9_2016_25t.toml:7`, `accord_2018_15t.toml:7`, `f150_2015_27tt.toml:7`), and arm hashes the published car files (plan:767).
- **Change:** make all of these edits in commit A, so the certificate covers them. Never touch these files after the freeze.

**B6 · should · `car_thermal.py:153` would name one engine inside a function given a plant** (b58 SF-4)
- **Verified:** `thermal_replay(source, params=None, pin_block=False, *, plant)` (`car_thermal.py:132`) calls `measured_fuel_gps` at `:153`.
- **Change:** pass `plant.engine.fuel.afr_st` (the same 14.7, so derived_sha `326c0835548975e2` holds). `calibrate_thermal.py:154` and `model_vs_data.py:376` may keep `typed_engine("b58")`.

**B7 · should · P5 misses two readers of `engines.known()`** (b58 SF-5)
- **Verified:** `fingerprint.py:694` uses `choices=engines.known()`. `benchmark_training.py:416` records `engines_known=engines.known()` (`:294`), with a stale comment at `:135`. An uncalibrated plant dies in `derived.py:58-64`.
- **Change:** `fingerprint.py` keeps `known()` but refuses an uncalibrated plant by name. `benchmark_training.py` records `trainable()` and `known()`, and its comment is updated (decision 47).

**B8 · should · Nothing on this laptop runs the entry points P5 edits** (b58 SF-6)
- **Verified:** L8 is the only run of `train.py:485`, and plan:456 moves it to the device (the laptop rule is CHECKPOINT.md:71-72, not VD:155). Nothing runs `train_all.py:94` or `run_phase_d.py:247`.
- **Change:** add `--help` runs of the four CLIs to the full list. Add one test per entry point: `--engine mazda_25t` refused and `--engine b58` accepted (mistake 12).

**B9 · should · The certificate tools are build-step-1 specific** (b58 SF-8)
- **Verified:** the archive's `make_cert.py:148`, `:171`, `:186` and `:202` hard-code build step 1's notes, `ded8da308863d394`, `99d2a9658b1258a7` and `3c48890dd15bc116`. H has no `HARNESS_SET`, `with_fuel` or cam pass-through.
- **Change:** list every candidate-side tool edit in §3.6 (B1, B2, the `with_fuel` route, parametrised `make_cert`/`make_md`). Keep the reference branches byte-identical, and archive the edited tools with the new certificate.

**B10 · should · Under NEP 50 the Python type of each new field is load-bearing** (b58 SF-9)
- **Verified:** `amend\f32_amend.py`: `14.7 * float32` is float32 while `np.float64(14.7) * float32` is float64, and an `np.float64` clip bound changes binding outputs. Today every typed field arrives as a Python scalar (`b58_lens\sha_old_fields.txt`).
- **Change:** require every scalar record field to be a Python float, int or str. Assert it in `test_fuel_forms.py`, `build_candidate` and `_derived_value`. A fit's numpy scalar would otherwise make the candidate differ from the file-built plant at a binding clip (`engine_env.py:1004-1006`).

**B11 · should · The `engine_sha` check over the old field set needs a pinned strip list and a control** (b58 SF-10)
- **Verified:** `engine_sha` is `json.dumps(asdict(plant), sort_keys=True)` (`engines.py:591-596`). A widened mock hashes to `023f5589215ee68e`, `99d2a9658b1258a7` once stripped, and a c_turb ulp moves it (`sha_old_fields.txt`).
- **Change:** strip exactly these keys:
  - `engine.fuel`;
  - `thermal.fuel_lhv_j_per_kg`;
  - `cycle.{form, ve_map, ve_map_ref_kpa, ce_rich_slope, ve_cam, cam_ref_deg}`;
  - `ecu.{lam_floor, lam_ceiling, cam_on}` and the 12 cam fields.

  Assert that the stripped key set equals the key set of the `cf43fbb` build (any other new field fails), and that the stripped values equal the B58's typed neutral values. Add the one-ulp c_turb control.

**B12 · should · Source-text pins sit on lines P1 and P4 edit** (b58 SF-11, corrected)
- **Verified:**
  - `make_page.py:1410` pins `"ki=r.knock_integral, unc=0.0)"`, the return line of `_evaluate` (`engine_env.py:763-765`). P4 edits `_evaluate`'s signature and its `run_cycle` call, not necessarily this line. The lens said P4 edits it.
  - `make_page.py:1400-1402` pins `Vehicle.demand`'s road-force lines; `:1325` and `:1413` are edited by P1. `_src` stops the build if text is gone (`:1265-1272`).
  - The lab anchors `"base, map_b = self._track_torque"` (`Explanatory Simulation/content.json:238-240`; `src/model/command-explanations.test.mjs:57`) on `engine_env.py:985`, which P4 edits. It also anchors `'self.spark ='` (`:1004`).
- **Change:** P4 names these as text that must survive. §3.6 items 12 and 16 catch a break.

**B13 · should · Top-level spec keys cannot carry a label** (b58 SF-13)
- **Verified:** top-level non-table values go to `_meta` unchecked (`engines.py:405-408`). A top-level `{value, label, source}` table is read as a section and refused (`:413-416`). `_spec_values` keeps top-level keys, so `plant_sha` moves (`fingerprint.py:251-267`).
- **Change:** record the label and source of `derived_set`, `kind` and `freeze` in a TOML comment, and state that they move `plant_sha`.

**B14 · should · `_derived_value` cannot dispatch "by field type"** (cars SF-7)
- **Verified:** both pairs and float tuples are annotated `tuple` (`engines.py:198-199`, `:354`). Today's converter is keyed by record and field (`:453-465`).
- **Change:** key each converter by (record, field), stored with each DERIVED-set entry. The B58's three branches, including the `()` fallbacks under `DERIVING_PARAMS=1`, stay byte for byte.

**B15 · should · The training-road guard must test the car record, not the vehicle** (cars SF-6)
- **Verified:** `min_tractive_force` reads only `gear_for`, `gears`, `final_drive`, `driveline_eff` and `wheel_r` (`engine_env.py:1499-1503`), so an `EpaVehicle` subclass of `Vehicle` passes it silently. `cd_a` and `crr` are read at `:1520` and `:1548`. `ThinAirVehicle` calls `super().__init__(plant.car)` (`wide_air.py:218-219`), which reads `car.cd_a` (`engine_env.py:439`).
- **Change:** raise unless `type(veh.car) is engines.Car`, with a control per builder for an `EpaVehicle` and a `CvtVehicle`.

**B16 · should · `step_record.gear()` breaks on a CVT** (cars SF-4)
- **Verified:** `gear()` reads `veh.gears` (`step_record.py:73-80`). `env_state` calls it (`:90`), and `step` calls `env_state` (`:113-121`), reached from `evaluate.run_episode(record=…)` (`evaluate.py:227-234`, `:280`).
- **Change:** a CVT branch (gear 0, ratio recorded). This is not PLANT_CODE, so it may follow commit A. Otherwise state that §5.9 reads `env.rpm` and `env.veh` directly and never records the Accord.

**B17 · should · `fingerprint.py:439`'s refusal text cites CHECKPOINT for a claim it does not make** (cars wrong claim)
- **Verified:** CHECKPOINT.md:113-114 says only "fingerprint schema 4 (decisions 27, 28) before any new engine trains". `fingerprint.py:439` reads `plant.car.gears`.
- **Change:** the message says "this car has no gears; fingerprint schema 3 cannot record it". Schema 4's content stays open.

### C. The leak-proof loader and the run-once validation

**C1 · must · Every fit input comes from the loader's yield or a typed DESIGN constant** (leak MF-1, MF-5; contract SF-7; fit SF-6, in part)
- **Verified:**
  - `lam_floor = round(min(0.70, lm − 0.01), 3)` uses the deepest λ over `rows_all` (`thresholds/contract.py:261-265`; `thresholds/split.py:260-267`). JSON `lambda_clip_floor.where.window` is "initial" for the Mazda and "final" for the Honda and the Ford (printed). MD:433-434 says Initial λ is never used.
  - The hot floor is the minimum MAP over every hold, held-out holds included (`split.py:163`).
  - The `epa_channels.csv` minima and maxima span all rows (`epa_map.py:564-574`).
  - The plan uses these as:
    - S3b's depth bound `[0, 1 − lam_floor]` and lower grid edge `hot floor − 20` (plan:585);
    - S3a's start (plan:584);
    - the censoring threshold "the table's λ minimum … ch:86" (plan:521, :1087);
    - S3d's domain and clamp, "Cell 9's 4501 rpm (ch:2) or its MAP range" (plan:606);
    - HD1's barometer of 97.6 kPa with a 97.2–98.6 sweep (plan:1086).

    S3b's upper edge and S3c's cap do not say which rows they use.
  - λ = 1 − depth·s·t (`engine_env.py:342-347`). A least-squares depth exceeds max(1−λ) when deep rows sit at s < 1, so the bound can bind.
- **Section:** §4.4; §5.2 S3a–S3c; §5.3 S3d; WP1 P2; §9.2; decisions 53 and 54.
- **Change:** each bound, start, edge, clamp and threshold below comes from the loader's yield or a DESIGN constant.
  - Depth ≤ 1 − (min over yielded calibration Final rows of λ_cellref − 0.01). This implies P2's invariant, which stays an assertion and never a constraint. `lam_floor` is used only for the policy clip (MD:792-797) and the dump's λ grid.
  - "Censored" means at least 2 calibration Final rows at their own minimum within 1e-9, or a documented sensor floor.
  - S3a's start and S3b's lower edge are the lowest calibration Final MAP, or DESIGN 100 kPa.
  - S3b's upper edge and S3c's cap come from calibration rows.
  - S3d's domain is the rpm and MAP range of the calibration rows carrying a cam value. Its clamp is their measured cam range.
  - HD1's barometer is the median of the yielded Cell 9 calibration rows' cell pressure, swept over their range.
  - Report whether each bound is active at the optimum and anywhere on the S3b grid. The hot floor and λ_ref stay where the contract puts them: populations and `lam_fed` (MD:500-508, :525-526).
- **Check:** C8's two-sided poison fit leaves `frozen_sections_sha256` unchanged.

**C2 · must · Stage 0 would read every column of every row inside Run 1** (leak MF-2)
- **Verified:** `split.load` is `csv.DictReader` of the whole table (`split.py:78-80`). `compute()` returns aggregates only and never reads spark, TIP, barometer, coolant or oil (`:111-127`, `:208-277`), so §4.4's checks cannot come from it (plan:517). MD:447 restricts every column of held-out rows to the validation.
- **Change:**
  - S0 (sentinel, λ minimum, TIP against barometer, coolant against oil, meter against injector, cam sign) runs on the loader's yield only.
  - Every held-out count (λ-less fired rows, sentinels) moves to `validate_epa.py arm`.
  - Only `epa_rows.py` imports `thresholds.split`, and only its pure helpers. An AST check confines `split.load`, `compute`, `run` and `report` to `test_epa_rows.py` and `validate_epa.py arm`.

**C3 · must · The poison proof's hook and scans would not fail on the leaks that exist** (leak MF-3; contract SF-9; leak SF-8(1))
- **Verified:**
  - The hook runs only on `dry-load` (plan:553). `audit_spawn.py` shows a parent hook does not see spawn workers or subprocesses, while the fit uses a spawn pool (plan:573).
  - The allowed set omits `epa_channels.csv`, which `freeze.json` hashes (plan:685), and the derived files `complete` builds from.
  - `epa_map.build_all()` rebuilds every row from the workbooks without naming the tables (`epa_map.py:550-563`), so string scans miss it.
  - `test_epa_rows.py`'s own scan needs the literals `epa_steady`/`epa_highload`. That contradicts plan:295 and its own rule (`document.py:525-531`).
  - The loader must import `split.f` (NaN on `''`, `split.py:67-71`), `ok`, `name`, `coverage`, `MIN_CLUSTERS` and `MAP_SPLIT`. Plan:476 omits them.
- **Change:**
  - Install the hook at the top of `calibrate_epa.py` for every subcommand (`fit`, `e6`, `complete`, `check`) and in the pool initializer.
  - Hook `subprocess.Popen` and refuse any argv naming `data/engines/` or `logs/epa/` except `git ls-files` and `git hash-object`.
  - Write the sorted list of opened paths to `run.json`, and test it against a per-subcommand allowlist.
  - Hash `epa_channels.csv` by its git blob id (`git ls-files -s`), or drop it from `freeze.json`.
  - Replace the string scans with import and attribute scans over every step-2 module and test. Forbid `epa_map`, `test_epa_map`, `validate_epa`, `thresholds.contract.build` and the split readers. Forbid `ENGINE_DIR`, `"data/engines"` and the JSON key `tables` outside `epa_rows.py`. Forbid `Token`, `verify_for_validation` and the held-out reader outside `validate_epa.py`.
  - Rename the reader, for example to `read_held_out`. Build the scan patterns from parts (`"epa_" + "steady"`).
  - Import the helpers listed above.

**C4 · must · The calibration reads a contract JSON that holds held-out-derived values** (leak MF-4)
- **Verified:** every engine entry carries `per_held_out_line` (held-out MAP ranges, `split.py:231-237`), all-row `coverage` blocks (`:268-273`), `lambda_clip_floor.where` (a row identity, `:267`) and `held_out_rows` (printed keys). Nothing restricts which keys fit code reads.
- **Change:**
  - One accessor, `epa_rows.calibration_contract(id)`, returns a deep-copied allowlist: lines, `held_out_lines`, table counts, `lambda_ref`, `hot_map_floor_kpa`, `fuel_by_table`, `lambda_clip_floor.floor`, `coverage.calibration_*`, `conventions`, `model_form`, the R values and `propagation_b58`.
  - An AST check limits contract loading to `epa_rows.py`, `validate_epa.py`, `epa_freeze.py` (hashing) and `test_contract_pinned.py`.
  - The poison test also garbles the forbidden keys in a scratch contract, and requires the calibration view and the yield to be byte-identical.

**C5 · must · The held-out reader trusts a token that its own tests must forge** (leak MF-6, SF-7)
- **Verified:** `held_out_rows(id, token)` needs a Token from `verify_for_validation()` (plan:512, :787), which cannot pass before the freeze. Plan:551 lets the test call the reader.
- **Change:**
  - The reader itself refuses `common.ENGINE_DIR` unless `results/EPA_VALIDATION/<id>/ARMED.json` is committed at HEAD with matching table, derived-file and code hashes, whatever token is passed.
  - Every test of the reader and of `validate_epa` runs in a temporary git repository with synthetic tables and contract. An AST check forbids tests from passing the real `ENGINE_DIR` or `CONTRACT_JSON`.
  - `d3_rows.py` is tested on synthetic traces. Its first real read is inside `validate_epa.py run` (MD:451).

**C6 · must · Run-once can be repeated undetected** (leak MF-7)
- **Verified:** `run` checks only that `ARMED.json` is committed at HEAD and the code is clean (plan:782). Any worktree or copy of the armed commit passes, and the plan uses both (:320, :433, :1014). "Nothing written" (plan:786) contradicts `run.json` listing every invocation (:785).
- **Change:** `run` refuses:
  - in a linked worktree (`git rev-parse --git-dir` ≠ `--git-common-dir`);
  - without `.git`;
  - outside the path `ARMED.json` records;
  - unless the output folder holds `ARMED.json` alone, counting tracked, untracked and ignored files;
  - if `git log --all` holds any other path under that folder.

  Before the first held-out read it writes an atomic STARTED record. Warnings are errors. Exceptions go to `crash_<k>.txt`, which counts as written, and only the exception type is printed. Re-execution is allowed only when STARTED is the only record. Reproduction re-reads the committed outputs and never re-runs. Commit F is pushed at once.

**C7 · should · ALPHA curves are both excluded and used** (leak SF-1)
- **Verified:** plan:478 versus :509-511 and :958. The contract allows only nodes whose measured source row is a calibration row (`thresholds/contract.py:625`; MD:435-436). `measured_at_speed` records hold `torque_nm` (`epa_map.py:519-529`).
- **Change:** no calibration code receives the curves. §7.6's descriptive WOT comparison uses the yielded calibration High Load Initial torque, labelled transient (MD:432-434).

**C8 · should · Poison with finite extremes; make the poison fit mandatory** (leak SF-2)
- **Verified:** text garbage becomes NaN (`split.py:67-71`) and is filtered by `ok()` (`:117-118`, `:139`, `:160`). That makes min/max-type leaks invisible.
- **Change:** poison held-out non-provenance cells twice, far below and far above each channel's range (written with `csv.writer`), plus one blank run. The poison fit of S0–S3 and S6 is mandatory for all three engines, and a full form-A poison fit is mandatory for one. Compare `frozen_sections_sha256` and `stage0.json`.

**C9 · should · Wording on tokenisation; coverage from raw strings** (leak SF-3)
- **Verified:** `source_row` is the third column (`epa_map.py:240`, `:405`), so `csv.reader` tokenises the whole row first. `split.coverage` rounds °C to 0.1 (`split.py:138-143`), while row types hold K (plan:495).
- **Change:** say "held-out rows are tokenised, never converted". Compute §4.6 item 3's coverage from the raw °C strings.

**C10 · should · Record the code at the first fit** (leak SF-5)
- **Verified:** `freeze.json` is written at the freeze (plan:677), after the ladder and any defect fixes (:647). Plan:771's inference does not follow.
- **Change:** `fit_A.json` records `git_head` and the sha_text of every step-2 module. Arm lists any change since then, with its calibration-defect log entry.

**C11 · should · Declared outcomes for two failure paths** (leak SF-6)
- **Change:**
  - **Arm guard fails after the roads step** (dump or in-sample differs): repeat Run 1 from S0 before any held-out statistic, and never relax the guard.
  - **An `epa_stats` defect after the run:** form and constants stay frozen; `in_sample.json` is recomputed beside the old; `ARMED.json` is re-made; nothing is refitted (MD:1039-1045).

**C12 · should · Generator writers** (leak SF-8(2))
- **Verified:**
  - `split.run`, `alpha_nodes.run`, `b58_propagation.run` (`:185-187`), `ecu_shift.one`/`run_all` (`:121`, `:125-138`) and `common.printout` (`common.py:79-87`) all write into `results/ENGINE_THRESHOLDS/`.
  - `b58_propagation` builds the B58 at import (`:33`).
- **Change:** an AST check forbids step-2 code and tests from calling these. `test_contract_pinned` adds `git diff --quiet -- results/ENGINE_THRESHOLDS/`.

**C13 · should · Disclose what was seen before the fit** (leak SF-9; contract and leak wrong claims)
- **Verified:** the plan's header boolean (TIP minimum against barometer; TIP is S1's target), the Honda's Final λ minimum (ch:86), Cell 9's 4501 rpm and the cam ranges (S3d's target) are all-row values (`epa_map.py:564-574`).
- **Change:** a "seen before the fit" list in `stage0.json` and the results README. Cite `rpm_min`/`rpm_max` to JSON `lines`, since the end lines are never held out (`split.py:172-174`; Mazda 1300/5000, Honda 1000/5000, Ford 1000/5500, printed).

### D. The fit (§5)

**D1 · must · S3c's envelope takes part-load points from lines without holds** (fit MF-1; cars SF-14)
- **Verified:**
  - The Mazda's 5000 rpm calibration line has no holds and stops at 123 kPa, against holds reaching 229 kPa (MD:353-355).
  - The Ford has 4 calibration high-load lines among 11 calibration lines (MD:425; JSON `lines`), so 7 have no hold. The Honda has 1 of 9.
  - `np.interp` silently needs increasing `xp` (`plant.py:436`).
  - The B58 used a running maximum (`derive_params.py:167-168`).
- **Change:** one point per calibration high-load line: its highest-MAP Final row with a meter. Sort by corrected flow, assert strictly increasing flow (refuse ties), keep the (0, 1) anchor and hold flat past the last point. Lines without holds give no point and are listed.
- **Check:** a synthetic test in which a line without holds cannot lower the ceiling, and a T0 case. Report whether the load loop settles on the locked climb's MAP trace where PR falls with flow (`engine_env.py:854-857`).

**D2 · must · S3b's gate falls to the grid's edge on a flat profile** (fit MF-2)
- **Verified:**
  - λ = 1 at or below `enr_load` (`engine_env.py:342-347`).
  - Every gate below the lowest enriched Final row gives the same SSE, and ties go to the lowest gate (plan:585), which is `hot floor − 20`. That puts the gate at an all-row quantity (C1).
  - Steady points lie "below the load where enrichment starts" (MD:1320-1323).
  - The B58's gate is a DESIGN definition (`b58.toml:104`), because five constants were not identified (`derive_params.py:241-247`).
- **Change:**
  - Add the calibration steady rows with λ to S3b's objective (dwell ≥ 30 s, so t = 1), with the same censoring.
  - Remaining ties go to the highest gate, and the flat width is reported.
  - `rpm_lo` may take values below the lowest calibration line.
  - The censored depth is a 1-D convex piecewise-quadratic problem, not closed form.
- **Check:** a T0 case whose true gate lies between the steady and the Final rows.

**D3 · should · `spark_min` ignores the IAT compensation** (fit SF-1)
- **Verified:** `step()` clips `base + iat_compensation`, and the compensation is ≤ 0 (`engine_env.py:349-354`, `:358`, `:375`). Rig charge air is 30–40 °C, and fired rows reach 47–55 °C (MD:579-582, :1329-1331). With `spark_min = floor(t_min) − 1`, the clip binds once IMT ≥ 37.5 °C.
- **Change:** `spark_min = floor(min over calibration rows of {spark_EPA, base, base + comp}) − 1`. Correct the target's sign: add `cold_retard` back, because `step()` subtracts it (`:359-360`).
- **Check:** at every calibration row, `BaselineECU.step` (dwell 30 s, no knock retard, EPA's IMT) returns `base + comp` unclipped.

**D4 · should · S4's inner solves and Jacobian are inconsistent** (fit SF-2)
- **Verified:** torque is affine in FMEP (`plant.py:263-266`), so ln T is not, and the inner "linear LS" does not minimise the stated objective. ln of a non-positive torque is NaN. The per-row chain rule (`plant.py:75-76`, `:82`) does not hold after an inner solve couples the rows.
- **Change:** fit all nine S4 parameters jointly in trf: outer columns by 0.5 CAD forward difference with the per-row chain rule, FMEP and UA columns analytic. Alternatively use the exact variable-projection Jacobian. The efficiency residual is `(T_m·F_meter/(T_E·F_m) − 1)/0.019`. Do the same for S5.

**D5 · should · Declare `x_scale` and tolerances; pin SciPy** (fit SF-3, SF-13)
- **Verified:** SciPy 1.18.1 has `x_scale=None`, meaning 1 for trf, and `ftol`, `xtol`, `gtol` of 1e-8. `max_nfev` excludes Jacobian evaluations (docstring). `requirements.txt:5-7` says nothing imports SciPy, which is already false (`git grep`: `conditions_test.py`, `make_page.py`, …). The lock pins `scipy==1.18.1` (`requirements-lock.txt:61`).
- **Change:** pass `x_scale` = the declared scales (S2's polish: 1000 for `ve_rpm` and `ve_width`), declare `ftol`/`xtol`/`gtol` above the measured finite-difference noise, record them in `fit_<form>.json`, and add scipy==1.18.1 to `requirements.txt`.

**D6 · should · Burn and delay are nearly collinear** (fit SF-4)
- **Verified:** by re-run, as listed under Basis. The weakest eigenvalue is 0.066 in scale units (about 4 units of sd), while a Fisher-against-ridge label would call all four "data-dominated".
- **Change:** per engine, report the weakest direction, its sd and its in-use consequence (KI at the climb cell, the λ lever). Add two starts at ± that direction. Hold nothing.

**D7 · should · S3a's two pieces need an empty-piece rule** (fit SF-5)
- **Verified:** the knock-limited surface has 4 coefficients and the plane 3 (`engine_env.py:169-172`, `:191`).
- **Change:** a minimum row count and rank per piece. The declared outcome is to stop at the last valid assignment and flag it.

**D8 · should · Reference constants and cam correlation** (fit SF-6)
- **Change:** type `ve_map_ref_kpa` (100) and `cam_ref_deg` (0) as DESIGN in each EPA spec. The domain and clamp follow C1. Report corr(`ve_cam`, `ve_map`).

**D9 · should · S2's polish bounds** (fit SF-7)
- **Change:** `ve_rpm` within [rpm_min, rpm_max], `ve_width` within [300, 20 000], and a bounded linear solve (`lsq_linear`) inside the projection.

**D10 · should · Verify's non-zero-column assertion would stop on legitimate outcomes** (fit SF-8)
- **Verified:** plan:589 versus :647. The `ve_rpm`/`ve_width` columns vanish when `ve_amp` → 0, and the S1 floor column is about 0 at the lowest hinge (`plant.py:66`, `:334`).
- **Change:** assert non-zero columns at the start values. Report zero columns at the optimum as a pre-declared outcome (§5.6).

**D11 · should · T0 cannot fail** (fit SF-9)
- **Verified:** the one-sided χ² is set against an undefined covariance (plan:739). At T0's noise (0.5 %, 3 K) against R (1.9 %, 10 K), an R-scaled (JᵀJ)⁻¹ is about 12× too large. Populations need BMEP (`split.py:113-115`; ch:4 "Calculated Value").
- **Change:** scale the covariance by the residual variance, test both tails (or per-parameter standardised errors), and add one seed whose truth lies outside the model's form. Add the T0 cases of D1–D3. State that populations come from `split.classify` on the calibration rows' structure.

**D12 · should · Name the D1 variant that gates in-sample** (fit SF-10)
- **Change:** the primary D1 gates (unreachable rows counted at the bound, MD:709). The without-row variant is reported only.

**D13 · should · S4 residual structure** (fit SF-11)
- **Change:** report S4's residuals per line and per population (hot λ≈1 against part load) at each form. Declare that an E1a miss on stoichiometric hot rows at form A is read as a burn/FMEP residual that no form B–D can act on (mistake 20), reported and never used to justify a form.

**D14 · should · Re-base §5.11** (fit SF-12; fit and cars wrong claims)
- **Change:**
  - **Pool speed-up:** 5.5× at 16 workers (re-measured).
  - **S4:** about 2.5 min per form pooled, so about 10 min for the four-form ladder per engine.
  - **D1:** about 53 cycles a row (39 pre-scan points and 14 bisection steps), about 8–9k per form.
  - **Completion:** about 200–230k cycles, since about 30 probe climbs alone are about 130k (`engine_env.py:800`: 6 run_cycle per step; 719 steps). That is about 40 min serial and 7 min pooled per engine.
  - **Run 1:** about 1.5 h worst case, about 1 h if form A passes.
  - T0 is rebudgeted the same way.

### E. Validation rows, E6, identities and hand-offs (§6, §8.5)

**E1 · must · The neutral-action identity: define it and run it** (b58 SF-15; contract SF-3)
- **Verified:**
  - MD:796 asks for "reproduce the baseline exactly", and MD:995 lists the neutral-action check as an identity row.
  - The neutral action sets fan and pump to 1.0 (`engine_env.py:1660-1663`), slewed up from zero after reset (`:922`, `:947-949`). The baseline runs the scheduled fan (0.4 for 97.4 % of the climb, `:1630-1658`) and the default pump (`:997-998`; `thermal.py:208-209`).
  - The agent's charge temperature comes from its own network (`:961` against `:967`).
  - The plan runs only the build-time invariant.
- **Change:** v4 text (decision 39(b)): the neutral trims are exactly 0.0; at every step the agent's λ = `float32(λ_b)` and spark = `float32(sp_b)`; clip contacts are 0; fan and pump are `neutral_action`'s documented constants, so the thermal trajectories differ by design. Add this check to §5.9 item 3 on each engine's locked climb, and hand it to the roads step.
- **Check:** a reported maximum difference of 0 and 0 clip contacts.

**E2 · should · E6 refit rows report how far the model in use moves** (contract SF-4)
- **Verified:** MD:747-749 says that for refit rows "the question is … how far the model in use moves". Plan:840 labels rows 1, 3 and 7 "excluded for".
- **Change:**
  - Rows 1, 3 and 7 report ΔE per row and the in-use changes, with no exclusion labels:
    - row 1: the hot TIT at λ = 1, the air and τ;
    - row 3: heat per gram, coolant and oil heat;
    - row 7: the knock share, and d both ways later.
  - Row 2 keeps |ΔE| < u_val for E2, D1 and L0 (MD:754).

**E3 · should · Row 9's band order and the rich slope** (contract SF-5)
- **Verified:** MD:761 names brackets for the Mazda's Atkinson ratio and the cam phases. The channels exist: Mazda ch:24-25 and ch:27 ("EPA Atkinson Ratio", Calculated); Ford Cell 9 ch:22-23. ±10 CAD applies only "where no consequence is computable". Plan:725 drops straight to ±10 CAD. `ce_rich_slope` is ASSUMED and shared under A and B (MD:464).
- **Change:** follow bracket → consequence-sized probe → ±10 CAD, and state why each bracket cannot be computed. Add `ce_rich_slope` to row 9: a probe under A and B, its σ under C.

**E4 · should · Decision 59's Tests lists need a counting rule** (contract SF-6)
- **Verified:** a d row "excluded for every constant it claims to test" has no statistic and drops the engine (MD:739-740, :1007-1009). The lists mix perturbed and unperturbed constants (plan:1092).
- **Change:** a member no E6 row perturbs counts as not excluded, because the held-out statistic tests it directly. Each list states which members are perturbed. In v4.

**E5 · should · Pre-declare L1's tightening plant** (contract SF-1)
- **Verified:** MD:726-728 names no plant. E8's tightening is the B58's (MD:780-781). L1's basis is B58 records (MD:162-172). MD:228-231 says an engine's own coefficients "never move an R".
- **Change:** decision 71: the B58. `EPA_TIGHTENINGS.json` gains a required `plant` field that arm checks.

**E6 · should · Declare the fired sentinel row's outcome now** (contract SF-12; leak decision 54)
- **Verified:** "a fired sentinel row stops" at arm (plan:776) would force a rule after fits (MD:42-44).
- **Change:** decision 54.

**E7 · should · Hand-offs are missing** (contract SF-14; cars SF-13)
- **Verified:**
  - **Contract obligations:** scored climbs must lie inside calibration coverage in speed and MAP, or be labelled not covered (MD:487-491). Trims below the deepest EPA λ are not covered (MD:797). The d-based load-bearing criterion needs agents (MD:743-744). A post-validation calibration defect allows no refit (MD:1039-1045).
  - **B58-tuned tools:** `preview_ceiling.py` is the B58 only (`:58`, `:63`, `:167`). `check_premise.py`'s policy depths are B58-tuned (`:113`, `:132`, `:147`, `:156`). The environment's action ranges and observation scalings are B58 values (`engine_env.py:698-700`, `:872-889`).
- **Change:**
  - **WP5 and the CHECKPOINT hand-off** list:
    - the coverage rule;
    - the not-covered trims;
    - the d-based load-bearing rows for the preregistration;
    - a plant-generic `preview_ceiling.py` before the roads;
    - the carried policy depths and environment scalings, as declared design values or scaled per engine before the roads.
  - **Decision 60** adds the calibration-defect route: report the defect, never refit, and cap the affected labels at limited.

### F. Cars, the CVT and completion (§5.9, §7)

**F1 · must · 39(c)'s CVT clause fails exactly where the Accord drives** (cars MF-1; contract SF-15)
- **Verified:**
  - `cars\arith.py` (re-run): the Accord needs 100.60 kW at η 0.92 and 97.42 kW at η 0.95. The economy line needs T_del·ω ≥ 134.1 kW (129.9 kW) against a 130 kW rating (`accord_2018_15t.toml:10-12`).
  - On the power-limited branch, N* is the speed of maximum deliverable power, so "below the speed of maximum deliverable power" (plan:1067) fails by construction.
  - K3 puts 413 s of the 719-step trace above the knee (`thresholds/ecu_shift.py:93-97`; `k3_nominal.json`), and the climb starts at 180 s (`engine_env.py:1274`).
  - Rule 0 fixes the clause before the first fit (MD:42-44).
- **Change:** decision 40 → law (b), and 39(c) is dropped. Otherwise (a) with the connected-interval clause and a pre-freeze synthetic feasibility check (section 3).

**F2 · must · C5's stepped-box threshold is not the one the gearbox applies** (cars MF-2)
- **Verified:**
  - The code is `min(SHIFT_LOAD·PEAK, interp(rpm, DELIVERABLE_TORQUE))` (`engine_env.py:507-510`).
  - The contract writes "SHIFT_LOAD·T_wot" (MD:898-900), with T_wot per rpm (MD:887; `strand_vehicles.md:155`).
  - On the B58's climb the code holds 7th at 340 Nm against 375 Nm, while 0.75·T_del(2706) = 288 Nm (`engine_env.py:488-489`). The literal formula would call the B58's own climb a kickdown.
- **Change:** decision 70, in v4. `c5_margin` is implemented to that text.
- **Check:** the B58's 7th-to-6th notch between 13.96 and 13.97 % at 130 km/h (`test_reward.py:229`).

**F3 · should · Report each car's locked-climb gear and its margins** (cars SF-1)
- **Verified:** with the plan's constants (`cars\arith.py`):
  - **F-150:** 4th needs 392.3 Nm against 0.75 × 508.4 = 381.3 Nm, so the box takes 3rd at 4627 rpm and 294.2 Nm (rpm within 5500). At η 0.95, 4th holds at 379.9 Nm. MD:426 assumed 4th at 3470 rpm.
  - **CX-9:** 4th needs 309.5 Nm against 315.2 Nm, 1.8 % under. 3rd would turn 5951 rpm against `shift_rpm_max` 5000, so it is barred (`engine_env.py:591-593`).
  - Both assume T_del does not bind first.
- **Change:** in §5.9 item 3, report per car the gear or ratio, rpm, demand, and the margins to `shift_ceiling_nm` and to the bar. Run K3 at η 0.86 and 0.98 as a declared sensitivity. Note that MD:426's rationale no longer describes the F-150.

**F4 · should · Decision 43's fallback leaks or cannot be typed** (contract SF-8; cars SF-2)
- **Verified:** a table maximum over all rows includes held-out torque (MD:447; `split.py:276` never read torque). The specs are typed-only in commit A (plan:237). MZ19 is Mazda USA's 2019 CX-9 sheet (`cx9_2016_25t.toml:103-106`).
- **Change:** decision 43.

**F5 · should · Lifting `b58_propagation` carries two typed B58 ambients** (cars SF-5)
- **Verified:** `thresholds/b58_propagation.py:40` (T_AMB_C 42.0) and `:60` (`t_amb=315.0`).
- **Change:** read `plant.scenario.t_amb` in `epa_coefficients`, with a test on a plant with another ambient.

**F6 · should · Specify law (b) completely** (cars SF-8)
- **Change:**
  - N_eco = max(cvt_rpm_min, n_w·0.405·5.36), and T_eco = f·v/(η·ω(N_eco)).
  - The low-speed branch, the f ≤ 0 case (N_eco) and the power fallback are as for law (a), with the 10 rpm scan and 0.01 rpm bisection.

**F7 · should · Completion: the finiteness assertion, and the knee for E6 climbs** (cars SF-9)
- **Verified:** plan:708 asserts finiteness at item 1, but the knee (item 4) and the floor (item 2) are not measured yet. Under `DERIVING_PARAMS=1`, missing keys read NaN (`derived.py:76-84`). `ecu_shift.py:109` has a fixed mode and a K3 mode.
- **Change:**
  - Assert finiteness except the named completion fields still to come.
  - Control: the table and the floor are bit-identical under two provisional knees.
  - Rows 7 and 13 report d at the frozen knee and with K3 re-set.

**F8 · should · One step population for the 1 % rule** (cars SF-10)
- **Change:** steps with t ≥ 188 s (`engine_env.py:1274`, `:1324`), using the environment's `e_track` (`:1022-1023`) against `TRACK_TOL` 0.05 (`:650`), in both §5.9 and decision 44.

**F9 · should · C1's control must be relative** (cars SF-11)
- **Verified:** an absolute 1e-5 on A moves F by at most 2.5e-7 (`cars\arith.py`).
- **Change:** use A·(1 + 1e-5).

**F10 · should · The rest of the load loop** (cars SF-12)
- **Change:** declare `ff_offset_kpa`, `map_floor_kpa`, `i_gain`, `i_clip` and `i_out` as carried unscaled (DESIGN) and say why (`engine_env.py:837`, `:857`; `b58.toml:145-151`).

**F11 · should · The TIT-cap variant has no wiring** (cars SF-15)
- **Verified:** `BaselineECU.step` has no TIT input (`engine_env.py:356`), and PLANT_CODE is frozen after commit A.
- **Change:** decision 62.

**F12 · should · The typed-value registry is incomplete** (cars SF-16)
- **Verified:** it lacks `t_block_warm`, `t_oil_warm` and `t_turb_warm` (`b58.toml:126-128`, DESIGN) and `wiebe_a`, `wiebe_m`, `knock_on`, `knock_p` and `knock_b` (`:67-73`, CORRELATION). The damage valuations are `:134-139`, not `:133-139`: `:133` is the knee, which K3 derives.
- **Change:** list every typed field of each EPA spec with label and source. `test_carried.py` covers all of them.

**F13 · should · State the road-load split's effect at 130 km/h** (cars SF-17)
- **Verified:** the Accord's A + B·v turns negative above 116.5 km/h. Alternative conventions move the climb force by +1.19 % or +0.28 % (`cars\arith.py`).
- **Change:** put this sentence beside C1's "not covered above 115 km/h" (MD:812-813).

### G. Documents

**G1 · should · The mistake-11 hit list is incomplete** (b58 SF-12)
- **Verified by `git grep`:**
  - `CHECKPOINT.md:5`
  - `Explanatory Simulation/tests/test_catalog.py:97`
  - `results/B58_IDENTITY.md:31`, `:33`, `:118`, `:131`
  - `results/B58_IDENTITY.json:54`, `:59`, `:68`, `:1216-1218`, `:1223`, `:2017`, `:2020`, `:2217`, `:2220`, `:2452`, `:2455`, `:2492`
  - `STATE_HISTORY.md:4207`, `:4236`
  - the archived `make_cert.py:186`
- **Change:** add these to plan:1040. The old certificate moves verbatim to STATE_HISTORY.

### H. Lens claims corrected (none dropped)

- **b58 SF-7:** its control (`HARNESS_PERTURB=cycle.ce_rich_slope`) raises under P3's invariant, so it runs through `HARNESS_SET` at form A+B+C (B2).
- **b58 SF-11:** P4 need not edit `_evaluate`'s return line. Naming the pin is a precaution.
- **b58 MF-1's evidence:** "the other nine random-action jobs": 9 of 12 others were checked.
- **b58 MF-2's fix:** `eng.ecu.cam_deg` should read `BaselineECU(eng.ecu).cam_deg`.
- **Contract SF-2 (moment-constrained S3a/S3b):** not adopted as the primary route, since v4 is mandatory anyway (decision 39). It is kept as the fallback.
- **Contract wrong-claim note:** "margin ≈ 2.7 %" depends on the model's maximum power. It is about 3.2 % if the model reaches its 130 kW rating; the point stands.
- **Fit SF-13:** "SciPy 1.16 changed least_squares defaults": for trf the effective `x_scale` is still 1, and the 1.16 change concerns lm and `max_nfev`. The fix stands.
- **Decision 53:** the fit lens kept 97.6 kPa and the leak lens replaced it. The leak lens's version is adopted (C1).
- **Cars MF-1:** "C5 stays literal under 40(b)" still needs one v4 sentence naming λ_kd·T_del(N_eco) as the CVT's kickdown threshold (decision 70).

---

## 2. Wrong claims in the plan, with corrections

1. **plan:114, :399.** "`engine_env.py:1004-1006` is X1's and untouched." P2 edits `:1006`'s bounds (plan:171, :377). What stays untouched is the float32 sum and the `float()` conversion.
2. **plan:411.** "One ulp on `ecu.lam_floor` → DIFFERENT; `lam_floor` binds in the extremes jobs' random λ trims." A float64 ulp is invisible in the float32 compare. The floor binds at 1 step, in `extremes:double:12:random` only, of the 10 random jobs checked (B1).
3. **plan:414.** "`ve_cam=1e-4` (with the ECU cam on) → DIFFERENT." With the B58's zero schedule (plan:210) the cam is 0 = `cam_ref_deg`, so the control reads IDENTICAL (B2).
4. **plan:87, :267, :460.** "The last/only PLANT_CODE edit; nothing after commit A edits PLANT_CODE." WP7 edits the `engine_env.py:1281` docstring and an `engine_specs/**` file (plan:1034-1035) (B5).
5. **plan:161.** "The ten constructor calls." The list names thirteen, and it is complete.
6. **plan:261-262.** The `_record` call is at `test_engine_threading.py:814` and the comparison at `:809`.
7. **plan:229.** `_maker` names `calibrate_epa.py --engine <id>`. WP4 defines subcommands (`fit`, `e6`, `complete`, `check`), so name them.
8. **plan:1067, decision 39(b).** "No engine can be bit-exact because the trims are float32." The fan also differs (1.0 against the scheduled duty), and the agent's charge comes from its own network. Only the λ and spark channels can be identical, and only at float32.
9. **plan:1067, decision 39(c) and CL-5.** "C5 fails by construction." That holds only on economy-branch steps. The sound reason is that a continuous law has no gear (MD:901-903). The proposed clause fails every power-limited step.
10. **plan:295.** "No new `.py` contains `epa_steady`/`epa_highload`." `test_epa_rows.py`'s scan needs them unless built from parts.
11. **plan:529.** "The calibration never opens the min and max of `epa_channels.csv`." Plan:521, :585 (ch:86), :606 (ch:2 and the cam ranges) and :1086 (the barometer) use all-row ranges.
12. **plan:1082, decision 49.**
    - **"Terms an engine does not need stay near neutral under the ridge."** At w = 0.01 the ridge is about 10⁴× weaker than S2's information on `ve_map`.
    - **The design.md:59 citation.** MD:694 cites it for spark sweeps; MD:1352-1353 copies it verbatim ("calibrate the B58's own cycle per engine"). It supports neither reading.
13. **plan:1136.** The Ford's `afr_st` is given as "14.559 (HD1)". The Ford has two fuels: Cell 9 FTAG 25278 at 14.557, and HD1 FTAG 26864 at 14.559 (JSON `fuel_by_table`, printed). The choice must be declared (decision 69).
14. **plan:547.** "This proves the frozen constants cannot depend on held-out values." λ_ref, the hot floor and `lam_floor` are contract constants over all rows (`split.py:159-163`, `:260-267`). Restate it as: the frozen constants depend on held-out rows only through λ_ref and the hot floor, used where the contract defines them.
15. **plan:484.** "No other field is parsed." `csv.reader` tokenises the row; no field is converted.
16. **plan:13-15.** "Neither touched an EPA row; ranges printed for input channels only." The TIP-minimum boolean (S1's target) and the cam range (S3d's target) are all-row functions of EPA rows.
17. **plan:771.** "So it was committed before the first fit." It proves only that the code is unchanged since the freeze (C10).
18. **plan:517.** "These use `split.compute()` … They print no value." `compute()` cannot supply them, and §4.4 prints "the largest deficit".
19. **plan:478 against :509-511 and :958.** The curves are "never returned", yet nodes are used. "Unmeasured nodes labelled model" conflicts with `contract.py:625`.
20. **plan:553.** The audit set must include `epa_channels.csv` and the derived files. A dry-load hook sees no spawn worker.
21. **plan:584.** "No clip binds at a calibration row, by construction." `step()`'s clip on base + compensation binds once IMT ≥ 37.5 °C. The `cold_retard` sign is also wrong: it must be added back.
22. **plan:587.** The B58 starts are at `b58.toml:61-65` (burn_res is `:63`). The plan cites `:62-65`.
23. **plan:585.** "Depth by closed-form LS": with censored rows it is a 1-D convex piecewise quadratic.
24. **plan:749-754.**
    - **Pooled time:** 16 workers give 5.5×.
    - **D1:** costs about 53 cycles a row, not 25.
    - **Completion:** is about 200–230k cycles, not 60k.
25. **plan:740.** "No EPA output is read." Populations need EPA's BMEP.
26. **plan:950, :1068.**
    - **The λ_cvt 0.75 label:** "ASSUMED (the Supra's shift_load)" omits that it is also the strand's D3 in-sample best (`strand_vehicles.md:174-175`). 0.65 is a point of the same grid.
    - **"Neither uses the strand's fitted values":** must disclose this.
27. **plan:945.** "`driveline_eff` … E6 row 10." Row 10 moves C3 only (MD:762). Nothing probes η on the locked climb, where it flips the F-150's gear.
28. **plan:1139.** The damage valuations are `b58.toml:134-139`; `:133` is the knee, which K3 derives.
29. **plan:230.** "Schema 4 records a transmission (CHECKPOINT.md:113-114)." CHECKPOINT says only "schema 4 (decisions 27, 28) before any new engine trains".
30. **plan:1071.** "D3 stays blind for C3." C3 uses the D3 car's own gear (MD:824-825). The reason is MD:449-452, "Neither uses … any D3 file".
31. **plan:281.** "The step outputs … do not move." `--build-only` rewrites `contract.txt` and `document.txt` (A3).
32. **plan:95.** "L8 runs on the training device (VD:155)." VD:155 asks for the certificate to be re-run there. The laptop restriction is CHECKPOINT.md:71-72, and BI:86's L8 ran here.
33. **plan:1040.** The hash hit list is incomplete (G1).

---

## 3. Decisions 39–71 for `results/VALIDATION_DECISIONS.md` section H

Each decision gets a Ghassan column and a Jad column.
- **G1:** before WP1.
- **G2:** before WP2 (version-4 text); answer it with G1.
- **G3:** before commit C, and before any EPA-output-derived check.

| # | decision | options | recommended, and why | by |
|---|---|---|---|---|
| 39 | Contract version 4 | (i) v4 after commit A, before any table-naming file; (ii) no v4 | **(i), and mandatory.** It is also triggered by any differing Jad answer to 36–38 (MD:1103-1105). Two rules cannot be applied as written: C5's "SHIFT_LOAD·T_wot" is not the gearbox's threshold (`engine_env.py:510`, :488-489), and "reproduce the baseline exactly" (MD:796) is unattainable on every engine. **Rule text:** (a) E8 computed in-sample and reported, outside the cycle-form criterion: its inputs are the ECU fit alone (MD:773-776), so counting it would force A+B+C+D for a reason no form addresses. (b) The identity of amendment E1, on the λ and spark channels at float32 with no clip contact; fan and pump are `neutral_action`'s constants; checked on every locked climb and test road (MD:995). (c) Dropped by 40(b). (d) Decision 70. (e) 49, 54, 55, 59's Tests-list rule, 64 and 71 as text. (f) Code citations remapped (A3). **Fallback for (a) only under (ii):** moment-constrained S3a/S3b (zero mean in-sample λ and spark residuals on calibration Final rows) | G1 |
| 40 | The Accord's ratio law | (a) economy line, λ 0.75; (b) stateless kickdown | **(b)**, λ_kd 0.75 ASSUMED, λ_target 0.65 DESIGN, specified as F6. C5 then reads literally as the margin to the kickdown threshold λ_kd·T_del(N_eco), the law's one discrete decision. Under (a), demand sits on λ·T_del(N*) on the economy branch, and the plan's 39(c) fails every power-limited step, where the Accord climbs (100.6 kW needed; the economy line needs 134 kW against 130 kW). Report as a diagnostic whether N* stays in one connected feasible interval under demand and T_del × (1 ± m). Disclose that 0.75 and 0.65 are D3-grid points (`strand_vehicles.md:174-175`), used by no gated row. **(a) only if** 39(c) is rewritten as "N* stays in the same connected interval of the feasible set under demand × (1 ± m) and T_del × (1 ± m)", plus a pre-freeze synthetic check that some 1–2 τ climb passes and exceeds the K3 knee | G1 |
| 41 | Form D's cam | (a) run by the ECU; (b) in the plant (needs v4) | **(a)** (MD:473-474). `cam_ref_deg` 0 and `ve_map_ref_kpa` 100 DESIGN in each spec. Domain and clamp from the calibration rows carrying a cam value. Report corr(`ve_cam`, `ve_map`). Its certificate controls need B2's harness edits | G1 |
| 42 | Car conventions | as listed | **As listed** (identities at 2.2e-16 to 3.3e-16, `cars\arith.py`). C1's control is A·(1+1e-5). State the split's effect at 130 km/h (F13). Disclose the 4.41/4.411 gap of 2.27e-4 | G1 |
| 43 | Gearbox constants; the CX-9's peak torque | Supra's constants or D3-derived; peak from MZ19, another published source, or DERIVED | **The Supra's shift constants, ASSUMED, CARRIED.** Peak torque from MZ19 (`cx9_2016_25t.toml:103-106`), opened and recorded before commit A. If it prints none, another opened Mazda source (PUBLISHED). Only if none exists, a DERIVED completion field: the maximum torque of the calibration High Load Initial rows (the use MD:432-434 allows), via `epa_rows`, never over all rows (MD:447). **Reason:** MD:449-452, "any D3 file", not C3's blindness | G1 |
| 44 | Locked climb and delivery | (a) 12 %/130 km/h/42 °C for every car, delivery reported, K3 on that trace; (b) highest delivered speed | **(a)**, measured over steps t ≥ 188 s with `e_track` against `TRACK_TOL` 0.05 (F8). Report per car the gear or ratio, rpm, demand and the margins to the kickdown threshold and the `SHIFT_RPM_MAX` bar (F3: the F-150 climbs in 3rd at η 0.92 and holds 4th from η 0.946). The K3 knee is also computed at η 0.86 and 0.98. (b) stays the pre-declared remedy | G1 |
| 45 | Borrowed B58 constants | typed with the CARRIED marker; read at build time | **Typed**, registry-tested, with every typed field listed (F12) and the λ_cvt coincidence disclosed | G1 |
| 46 | Load-loop gains | per-Nm B58 gains; scaled by the displacement ratio | **Scale `ff_kpa_per_nm` and `p_gain` by 1.2048, 2.0028 and 1.1125.** Declare the other loop fields carried unscaled (F10). Tested by the tracking check | G1 |
| 47 | Training and scoring guard | refuse EPA engines until schema 4 and a committed validation | **Refuse via `engines.trainable()`** in `train.py:485`, `train_all.py:94`, `run_phase_d.py:247` and `evaluate.py:422`. `fingerprint.py:694` refuses an uncalibrated plant by name. `benchmark_training.py:416` records `trainable()` and its comment `:135` is updated. One refusal test and a `--help` run per entry point (B7, B8) | G1 |
| 48 | Re-runs at commits touching only EPA files | (a) PHYS items 1–4 and the app suites; (b) a waiver | **(a)** (PHYS:2-10, :18-29). The B58 can see EPA specs through `name_of` (`engines.py:578-583`). WP7's PHYS-path edits move into commit A (B5) | G1 |
| 49 | Form scope | per engine; common to the three EPA engines | **Per engine (changed).** Both stated supports for "common" are refuted: the ridge cannot hold unneeded terms neutral (about 10⁴× weaker than S2's data), and design.md:59's "one model form" is the B58's cycle per engine (MD:694, :1352-1353). The text leans per engine (MD:461, :471). Report each engine's form and residual structure (mistake 20). If the team prefers common, v4 must state it | G2 |
| 50 | The estimator | §5 as written; as amended | **As amended:** C1 and D1–D14. In-sample E8 stays under 39(a) | G3 |
| 51 | Knock scale | (a) geometric mean of KI = 1; (b) max KI = `knock_detect_ki` | **(a).** KI ∝ 1/knock_a exactly (`plant.py:254-255`), so row 7 is an exact rescale | G3 |
| 52 | TIP below the barometer | keep and report; exclude; barometer-referenced floor (v4) | **Keep and report.** Count and deficit from the loader's yield only. Refit without those rows as a sensitivity. HD1 rows judged against decision 53's barometer. Disclose the all-row premise | G3 |
| 53 | Boost envelope; HD1's barometer | §5.2 S3c; amended | **Amended (D1, C1).** One point per calibration high-load line from Final rows, strictly increasing flow, anchored, flat past the last point. HD1's barometer is the median of the Cell 9 calibration rows, swept over their range. Check loop settling | G3 |
| 54 | λ-less rows, the sentinel, the Honda floor | as stated; amended | **In v4:** a fired row without λ runs at λ 1.00, flagged, and every statistic is also reported without it. Sentinel rows are excluded from every fit; in every statistic, in-sample and held-out alike, they run at the model ECU's spark (dwell 30 s, no knock retard, EPA's IMT), flagged, and every statistic is also reported without them. That is a declared outcome, never a stop. Held-out λ-less and sentinel counts are taken at arm only. "Censored" is defined on the calibration Final rows themselves (C1) | G2 |
| 55 | In-sample gaps | neither blocks nor passes; literal (criterion unmet) | **Neither blocks nor passes, recorded per form, in v4.** No calibration line means no evidence about the form. The held-out rule MD:1007-1009 is unchanged | G2 |
| 56 | u-terms | §6.2 | **§6.2, with every `u_input` resolution pinned as a number before commit C, spark's included** (no reading from repr, `epa_map.py:308-314`). EPA's instrument pages are opened before commit C, and the pages opened are recorded | G3 |
| 57 | Statistic details | as stated | **As stated.** The primary D1 (counted at the bound, MD:709) gates in-sample. About 53 cycles a row | G2 |
| 58 | MAP extrapolation | flags | **As stated:** flags against `coverage.calibration_*`, never a relabel (MD:350-352, :572-588) | G2 |
| 59 | E6 readings | as stated; amended | **Changed (E2–E4):** refit rows report the movement of the model in use; row 2 keeps u_val; row 9 follows bracket → probe → ±10 CAD and includes `ce_rich_slope`; unperturbed Tests-list members count as not excluded; E8 has no list and is never excluded. In v4 | G2 |
| 60 | Run-once mechanics | §6.1; amended | **Amended (C5, C6, C10, C11, E7):** the reader's own ARMED check; synthetic tests; worktree, copy and folder-state refusals; STARTED and crash records; the post-validation calibration-defect route (no refit, limited at best); the arm-failure and `epa_stats`-defect outcomes | G3 |
| 61 | Interpreter and device | this laptop's venv; the device | **Laptop venv (3.13.2, `requirements-lock.txt`) for calibration and validation.** Add scipy==1.18.1 to `requirements.txt`. Re-make the frozen-plant dump on the device and record the comparison. L8 for commit A on the device (CHECKPOINT.md:71-72), so the CLI tests of decision 47 run here | G1 |
| 62 | The Ford's TIT-cap row | specify now, cap in the preregistration; amended | **Changed:** an ECU patch outside PLANT_CODE in `ecu_shift.py:70-78`'s pattern, closing over the plant, that solves for the least λ holding model TIT ≤ cap. The cap's rule is fixed before commit C, as the highest TIT on the Ford's calibration Final rows computed at completion (or `egt_limit_k` 1223 K), never after the held-out run, which precedes the preregistration | G3 |
| 63 | C3/C4's unpinned inputs | hash at run time; at arm | **Hash the D3 summary file and the Accord's D3 files into `ARMED.json` at arm**, against `MANIFEST.csv`. `d3_rows.py` is tested on synthetic traces only | G3 |
| 64 | C5 against the held-out E1a | as stated | **As stated, plus:** a declared cap on redraws per climb slot; if a car has no passing climb, its scored climbs' margins are listed and its results are reported as gear-sensitive, not dropped (C5 is a rule, MD:996); the seed stream is committed with the roads; disclose that the tightenings were measured on the roads as first drawn; `c5_margin` per decision 70 | G2 |
| 65 | Waive the tightenings? | no; yes (a v4 change) | **No:** `order_of_work[2]` comes before `[3]` | G2 |
| 66 | Replacement for `--check` | §8.4 | **Drop as a decision.** No alternative exists once `calibrate_epa.py` exists (`document.py:489`). §8.4 stays as the specified procedure, plus `git diff --quiet -- results/ENGINE_THRESHOLDS/`, and a note that after commit C no version can be written without editing `document.py` | — |
| 67 | Mistake 11 for hashes | add to RETIRED; grep and update | **Grep, update, move the old certificate verbatim to STATE_HISTORY**, with G1's list. Hashes are not figures | G1 |
| 68 | CLAUDE.md:137 | name `engines.py` and `engine_specs/` | **Name them**, as PHYS:2-10 does | G1 |
| 69 (new) | The Ford's in-use fuel | HD1's FTAG 26864 (14.559, 42.908 MJ/kg); Cell 9's FTAG 25278 (14.557, 42.908) | **HD1's.** It is the high-load cell and the hot region the climbs use, and the octane the plan types is FTAG 26864's. The difference is 1.4e-4 in AFR_st and none in LHV. Calibration rows still run on their own table's fuel (`with_fuel`). Report the Cell 9 variant | G1 |
| 70 (new) | C5's operational threshold | the contract's SHIFT_LOAD·T_wot; the code's `shift_ceiling_nm` | **`Vehicle.shift_ceiling_nm(rpm)`** (`engine_env.py:507-510`) at the held gear's and each rejected higher gear's rpm. A downshift barred by `SHIFT_RPM_MAX` (`:591-593`) cannot be caused by a torque error and passes, with the bar's rpm margin reported. For the CVT under 40(b), the threshold is λ_kd·T_del(N_eco). In v4. Tested on `test_reward.py:229`'s notch | G2 |
| 71 (new) | L1's tightening: which plant | the B58; each EPA plant | **The B58**, on decision 34's roads: the same plant as E8's tightening (MD:780-781) and as L1's basis (MD:162-172). An EPA slope would let an engine's own coefficients move its R (MD:228-231), chosen after Run 1. `EPA_TIGHTENINGS.json` records `plant`, and arm checks it. In v4 | G2 |

---

## 4. What the plan must still settle before WP1 starts

1. **The decision sheet.** G1 and G2 answered in both columns, including Jad's 36–38, before any WP1 sub-step. Without 40, 41, 43, 69 and 70, P4, P5 and P6 cannot be written. Without 39 and G2, WP2, which follows commit A directly, has no text.
2. **The B58 certificate procedure for commit A**, written into §3.5–3.6:
   - the candidate-side tool edits (B1, B2, B9), with the reference side byte-identical (BI:47-49);
   - the control table with jobs, expected outcomes and pre-checks (bind count 1; a nonzero cam; the slope control at form A+B+C);
   - the quick-loop jobs per sub-step (B3);
   - the CLI checks (B8);
   - L8's placement (decision 61).
3. **WP1's code specification corrected:**
   - the P3/P4 split (B4);
   - `_derived_value` keyed by (record, field) (B14);
   - `type(veh.car) is engines.Car` guards with controls (B15);
   - `car_thermal.py:153` (B6);
   - `fingerprint.py:439`'s text, `fingerprint.py:694` and `benchmark_training.py:416`/`:135` (B7, B17);
   - `derived.py:49-52`'s command (wrong claim 7);
   - top-level spec keys as TOML comments (B13);
   - the Python-type requirement and assertions (B10);
   - the `engine_sha` strip list, its key-set assertion and its control (B11);
   - the source-text pins that must survive (B12);
   - the `step_record` CVT branch decided (B16).
4. **The six EPA specs' complete registry**, every field with label and source (F12):
   - per-engine `afr_st` and LHV, with the Ford per decision 69;
   - `lam_floor` (the contract's `floor`) and `lam_ceiling` 1.25;
   - `ve_lo`/`ve_hi` 0.30/1.30, `ve_map_ref_kpa` 100 and `cam_ref_deg` 0;
   - every carried value, with its source line corrected;
   - `n_turbines` (UNVERIFIED);
   - the cars' converted values, printed by `test_cars.py`;
   - the CX-9's peak torque from MZ19, opened first (decision 43);
   - the CVT law's parameters (decision 40);
   - `rpm_min`/`rpm_max` cited to JSON `lines`.
5. **WP7's PHYS-path edits moved into commit A** (B5): the `engine_env.py:1281` docstring, `engine_specs/cars/README.md:18-21` and the four car TOML headers.
6. **WP2's preconditions recorded:** the v4 rule text drafted from the G2 answers; the code citations to remap; `verify_docs.py` and `drift_test.py` in WP2's checks (A3); WP2's trigger (A2).
7. **The plan's text corrected per section 2**, so that WP1 is implemented from a specification that holds. This matters most for §3.4–3.6, which define the B58's identity.
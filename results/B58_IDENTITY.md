# The B58 identity certificate: build step 1 against cf43fbb

**21 October 2026, made again after the review.** Build step 1 of decision 24
(`results/VALIDATION_DECISIONS.md`, section F) threads an Engine record and a Car
record through the plant, the environments and every script, with no default engine
anywhere (mistake 1). Before anything is calibrated or trained on `GRA-test`, the B58
built that way has to be X1's plant, the plant of `cf43fbb`: the same doubles, not the
same figures to a tolerance. It was certified once that night; two reviews then found
21 things (section 6), the fixes changed the plant's code, and every level ran again
on the corrected tree. This file says how that was measured and what came out.
`results/B58_IDENTITY.json` holds every number below, read by `make_cert.py` from the
runs' own output files; the tools and the evidence are archived beside it (section 8).

**Verdict: BIT-IDENTICAL at every level.** On one interpreter the corrected candidate reproduces the
reference byte for byte: 2 685 037 values from the harness (units, every road family,
the premise), 8 513 840 from four X1 agents on the twenty frozen episodes, the
reward gate's whole output, `evaluate.py`'s report line for line, 600 steps of training to
the last weight (2 433 978 tensor values), every committed file the scripts rewrite,
and, without a derived file, `build_dataset.py` on all eleven drives (3 617 501
values; it could not run that way before the review). No computed value differs. What
does differ is a printed line, a label, a code hash or a fingerprint field that names the
plant, and two committed files that were already stale on `cf43fbb` (section 5). The
checks can fail: one ulp on the housing's heat capacity or on the car's mass comes out
DIFFERENT (section 2), with three measured limits stated there.

## 1. What was compared

| | reference | candidate |
|---|---|---|
| code | `cf43fbb`, `git archive` (tar sha256 `e16e7213…85665d`), extracted in scratch and checked with `tar --compare` | `GRA-test`'s working tree: build step 1 and the review's fixes uncommitted, on HEAD `e9e16ed` (`96884f1` when the runs began: another session committed a document, `results/VALIDATION_DECISIONS.md`, during them), 1217 files (manifest sha256 `fd4639ccf6330609` at the first run, `3dd6500b183b6db3` after the last: section 5 lists what changed between them) |
| `plant_sha` | `3c48890dd15bc116`, the value X1's `meta.json` records | `ded8da308863d394` (`c276354cff16132c` in the first certificate) |
| `derived_sha` | `326c0835548975e2` | `326c0835548975e2` |
| `engine`, `engine_sha`, `backend` | none (fingerprint schema 2) | `b58b30o1/a90-supra-zf8hp51`, `99d2a9658b1258a7` (`4791be491a7b6c41` in the first certificate), `cycle` (schema 3) |
| gears, final drive, crank step, knees, scenario, `episodes_sha` | 5.25 3.36 2.172 1.72 1.316 1 0.822 0.64; 3.15; 0.25°; 1123 K and 408 K; grade=0.12 t_amb=315 v_kmh=130; `05a598a574268b20` | the same, read from the plant |

**Why the hashes move although no number does.** The B58's plant files are fingerprint.plant_files('b58'): the code of plant.py, thermal.py, engine_env.py, derived.py and engines.py, and the values of engine_specs/b58.toml and a90_supra.toml. engines.py and the specs are new, and the code of the others changed form (literals became record fields): plant_sha moves although every number is the same. It moved again with the review's fixes. engine_sha hashes every value of the plant as built. The review moved the deliverable-torque table's conditions -- its grid, 42 C, the 365 K block, 30 settling steps -- from measure_deliverable_torque's defaults into the car's record (engines.Car.table_*), so the record holds six more values; every value it held before is the same. `derived_sha` does not move: `data/derived_params.json` is the same file in both trees.

**One interpreter for both trees**: `.venv\Scripts\python.exe`, Python 3.13.2, numpy 2.5.3,
scipy 1.18.1, pandas 3.0.5, torch 2.14.0+cpu, stable-baselines3 2.9.0,
gymnasium 1.3.0 (`pip freeze`: 66 packages). Rule 4 asks for 3.12, which this
machine does not have; decision 32 (revised 21 October, open) would amend it to the training
device's pinned versions and re-run this certificate on that device.
Every process is single-threaded (OMP and MKL at 1), so how many ran at once changes the
time, not a number. Each job runs in its own process in its own tree and dumps every
number it produced as float64 (`harness.py`); two dumps are compared array by array with
`tobytes()`, after dtype and shape, and element by element as bits to find the first
difference (`cmp.py`). The reference side is the first certificate's evidence, copied: the
reference tree and the reference-side code of the tools did not change. L8's reference
runs, deleted after the first certificate, were made again.

## 2. The checks can fail (mistake 12)

| control | expected | result |
|---|---|---|
| the reference against a second run of itself: units, an extremes episode with random actions, the hot thin-air WideAir corner, a conditions rollout at 82 kPa (305 222 values) | IDENTICAL | **IDENTICAL**, all four |
| the corrected candidate with one ulp on `thermal.c_turb` (6000.0 → 6000.000000000001), put through the frozen records and into `engines.get`'s cache; the same four jobs | DIFFERENT | **DIFFERENT**, 4 of 4. First differences: in units, `thermal_None` at [1100, 2], 1023.9622170545368 against 1023.9622170545367; in the extremes episode, `info` at [11, 14], 538.0972830731831 against 538.097283073183 |
| the same with one ulp on `car.mass` (1520.0 → 1520.0000000000002) | DIFFERENT | **DIFFERENT**, 4 of 4. First difference in units: `demand` at [0, 0], -45.56624988776282 against -45.56624988776284 |
| L6 on a perturbed candidate, `sighted_seed0`, against the committed files | NOT EQUAL | one ulp on the mass: 23 of 35 scores equal, the first difference damage of episode 0, 261.5112981997566 against 261.51129819975733; one ulp on `c_turb`: 30 of 35. **The per-step records do not see one ulp** (0 of 46 fields differ): `eval_record.npz` is float32. A relative 1e-9 on the mass: 2 of 14 scores equal, 32 of 46 per-step fields differ |
| L8 through a wrapper that replaces the plant before `train.main()` runs | the wrapper alone IDENTICAL; perturbed DIFFERENT | the wrapper alone: **IDENTICAL**. One ulp on the mass or on `c_turb`: **IDENTICAL weights**, although each run's `engine_sha` shows the perturbed plant reached it: the network learns from float32. A relative 1e-9 on the mass: largest weight difference 0.09445, 75 tensors; 1e-6: 0.05226 |
| the learning lab's outputs, `lab_dump.py` on a perturbed candidate | DIFFERENT | one ulp on `c_turb`: **IDENTICAL**, 36325 leaf values compared; 0 source-line numbers moved; 0 re-worded strings; 0 other differences. **The lab's 40-step sessions do not show one ulp.** A relative 1e-9: **DIFFERENT**, 36325 leaf values compared; 0 source-line numbers moved; 0 re-worded strings; 1212 other differences |

So three comparisons are exact only to their own precision: the per-step comparison
against the committed float32 records, training, and the learning lab's outputs. All
three sit on top of the full-precision comparisons, L1 to L3 and L6's comparison of the
two trees' float64 records, which do see one ulp.

## 3. The levels

| level | what ran, in both trees | compared | result |
|---|---|---|---|
| **L1** units | `run_cycle` on 1200 operating points × 16 fields, `predict`, the crank-step pair, the boost ceiling, the charge temperature, the airflow inversion, the thermal network at three housings and its cold reset, the ECU over 400 steps, the gearbox and road load, the damage model, the locked climb at three steps, every terrain family, the deliverable-torque table re-measured (the candidate on the car's own grid and conditions, `Car.table_*`), the load loop | 115 173 values | **BIT-IDENTICAL** |
| **L2** Extremes | `ExtremesTrainingEnv`, five families, neutral and seeded random actions: 10 jobs | 764 980 | **BIT-IDENTICAL** |
| **L2** Terrain | `TerrainTrainingEnv`, five families | 382 490 | **BIT-IDENTICAL** |
| **L2** random road | `random_road.climb` at dt 0.2 and the `RandomClimb` wrapper (which since the review refuses a plant whose locked climb is not the Supra's) | 527 328 | **BIT-IDENTICAL** |
| **L2** WideAir | the four corners of 0–45 C × 80–101.3 kPa, 30 C, a four-episode sequence: the thin-air kickdown table and the closed-throttle floor, measured in the car's own table conditions since the review | 406 746 | **BIT-IDENTICAL** |
| **L2** conditions | `conditions_test._run`, the four hand-written policies | 319 320 | **BIT-IDENTICAL** |
| **L3** premise | `check_premise`'s five rollouts, every step; then `check_premise.py` itself, in a copy of the candidate | 169 000 values; `results/premise.json` | **BIT-IDENTICAL**; the file equals the reference's and equals the committed one |
| **L4** reward gate | `test_reward.py`, and `--road random` | stdout, byte for byte | **identical**: 2284 and 1005 bytes, "All checks pass. The reward is safe to train against." |
| **L5** roads | `check_roads.py --road extremes` and `--road wideair`, in a copy of the candidate | the JSON each writes; stdout | **identical in both trees**, baseline past 850 C: 10 of 40 roads (extremes) and baseline past 850 C: 2 of 40 roads (wideair). Wideair's equals the committed file; extremes adds two keys to every road of the committed file, in both trees (section 5) |
| **L5** validation | `validate.py` | stdout | **identical**: 8 of 11 quantities inside their band; `validation_table.md` untouched |
| **L5** derived constants | `derive_params.py` in a scratch copy of each tree | the file each writes | **the same values**, `derived_sha` `326c0835548975e2` in both copies and the committed file; they differ in /_generated only, the time each was written |
| **L5** generality | `generality_test.py`, in a copy of the candidate | `results/generality.json`; stdout | **identical**, and it equals the committed file |
| **L5** app and lab | every `app/test_*.py` suite, the app's node tests, the lab's tests and its outputs | failing tests; the lab's values | **no failure is the candidate's alone** (section 5); the lab: 36325 leaf values compared; 178 source-line numbers moved; 88 re-worded strings; 0 other differences |
| **L6** X1 agents | `sighted_seed0`, `sighted_seed4`, `blind_seed2`, `blind_seed6` on the twenty frozen episodes through `evaluate.run_episode` with a record | the two trees: 2 128 460 values an agent; each tree against `phase_d_extremes_dt1_raw.json` and `eval_record.npz` | **BIT-IDENTICAL**, 4 of 4; 140 of 140 equal at full precision, 46 fields, 1064200 values, all identical, for every agent, in both trees |
| **L7** end to end | `evaluate.py` on `sighted_seed0`: three hand-written policies and the agent, 80 episodes; the candidate scored a scratch copy (the same `final.zip`) whose `meta.json` carries the schema-3 block and an `identity_override`; no force flag | the report, line by line, after removing the fingerprint block and the model's path | **identical**, 27 lines; VERDICT: every row equals the committed raw scores |
| **L8** training | `train.py`, 600 SAC steps, seed 0, CPU: extremes sighted, extremes blinded, wideair sighted, `--out` in scratch (deleted after) | every tensor of `final.zip`; the counters; the 600 recorded steps | **largest weight difference 0.0** in all three (IDENTICAL): 96 tensors (811 326 values), 47 fields, 47400 values, all identical |
| **finding 2** | `build_dataset.read_drive` and `derive` on all eleven drives with `data/derived_params.json` moved aside | every numeric column | **BIT-IDENTICAL**, 3 617 501 values; before the fix the candidate stopped: `FileNotFoundError` |
| **finding 11** | `check_roads.py`'s 40 terrain roads in a copy of each tree | the JSON; stdout | **identical**, baseline past 850 C: 14 of 40 roads; the committed file is stale on both (finding 13) |
| **finding 11** | `check_random_road.py` in each tree | stdout | the candidate exit 0 in 2777 s, `cf43fbb` exit 0 in 2413 s; identical but for road_sha and the run time (section 5) |
| **finding 11** | `evaluate.py --protocol d2`, end to end (no D2 agent is on this machine): the three hand-written policies on the twenty frozen D2 episodes | the report after the fingerprint block | **identical**, 23 lines; X1's agent under `--protocol d2` is refused on the FATAL scenario |
| **finding 11** | the learning lab: `npm ci`, `npm run build`, `launch.py --no-browser`, `launch.py --check`, in a copy of the candidate | its summary lines and its exit code | `npm ci`: added 134 packages, and audited 135 packages in 9m, 1 high severity vulnerability, exit 0 in 538 s; `npm run build`: ✓ built in 23.90s, exit 0 in 62 s; `launch.py --no-browser`: Supra Lab is ready: http://127.0.0.1:8765, exit 124 (124 = stopped by timeout after the check, as intended); `launch.py --check`: Local app healthy, exit 0 |

## 4. The suites

| suite | result |
|---|---|
| `test_engine_threading.py` | 20 tests, OK |
| `test_epa_map.py` | 29 tests, OK |
| `test_epa_map.py` with the MY2021 and MY2023 Test Car Lists (finding 18) | 29 tests, OK |
| `test_plant_guards.py` | 14 tests, OK |
| `test_wide_air.py` | 17 tests, OK |
| `test_plant_guards.py` on `cf43fbb` | 6 tests, OK |
| `python random_road.py` | SELF-TEST PASSES in both trees |
| `verify_docs.py` | All 74 checks pass (953 figure mentions scanned in the documents). (cf43fbb: All 74 checks pass (945 figure mentions scanned in the documents).) |
| `drift_test.py` | 18 of 18 drifts CAUGHT (all parts), run as six parts of three rows at once, each with drift_test's own control first: the undrifted copy passes verify_docs.py; exit 0: All 74 checks pass (955 figure mentions scanned in the documents). |
| `drift_test.control()` with this page, its JSON and its archive in the copy | passes with the certificate's files in the copy: exit 0: All 74 checks pass (955 figure mentions scanned in the documents). |
| `app.test_replay --full` | 59 of 59 checks pass |
| `app.test_simulation` | 16 tests, FAILED (failures=1); on `cf43fbb` (a git clone): 16 tests, FAILED (failures=1) |
| `app.test_agents` | 135 tests, FAILED (failures=1, errors=1, skipped=14); on `cf43fbb` (a git clone): 135 tests, FAILED (failures=1, errors=1, skipped=14) |
| `app.test_results` | 125 tests, FAILED (failures=5, errors=1, skipped=5); on `cf43fbb` (a git clone): 124 tests, FAILED (failures=7, errors=1, skipped=1) |
| the lab's tests (`Explanatory Simulation/tests`) | 31 tests, FAILED (failures=3, skipped=1); on `cf43fbb` (a git clone): 31 tests, FAILED (failures=4, skipped=1) |
| the other 11 `app/test_*.py` | 11 OK |
| `node --test static/sim/*.test.mjs` | 306 tests, 306 pass, 0 fail, 0 skipped (`cf43fbb`: 306 tests, 294 pass, 0 fail, 12 skipped) |

## 5. Every difference, with its first differing value

- **check_premise.py, stdout (L3)** (a printed line, no number): candidate: plant: b58b30o1/a90-supra-zf8hp51. The candidate prints the plant it names before the table; results/premise.json is byte-identical.
- **evaluate.py's report, the fingerprint block (L7)** (provenance, removed before the comparison): cf43fbb: plant_sha 3c48890dd15bc116; candidate: plant_sha ded8da308863d394. Schema 2 against schema 3: plant_sha moves (section 1), engine / engine_sha / backend are new FATAL fields, the git fields are None in the archive, plant_text_sha hashes other bytes.
- **check_roads.py --road extremes, against the committed results/training_roads_extremes.json (L5)** (a committed file older than the code that writes it, on cf43fbb as well): road 0 (seed 100) gains 'floor_nm': 15.0 and 'p_kpa': 101.3; so does every road. Both trees write the same file; the committed one predates 06f4686, which added the two keys.
- **check_roads.py (the 40 terrain roads), against the committed results/training_roads.json** (a committed file older than the plant, on cf43fbb as well; finding 13, for main): road seed 100: peak_c 736.9097825485758 committed, 736.8890366373793 now. The file was last written by cbb8d09 (29 September), before 75ca65f (8 October) sub-stepped the thermal network and ramped the grade; both trees write the same new file.
- **python -m app.test_replay --full (L5)** (a check's label, same value): cf43fbb: PASS M7: served limits match engine_env turb_c 849.9; candidate: PASS M7: served limits match the plant's damage knee turb_c 849.9. The M7 check reads the damage knee from the plant now (engine_env.TURB_PROTECT_K is gone).
- **the learning lab's outputs (L5)** (source-line numbers and three texts): re-worded /plant_5200_180/charge_temp_source; ref: 'plant.charge_temperature(ambient_k) default (+12 K; no block-temperature input)'; new: 'plant.charge_temperature(ambient_k, None) (+12 K; no block-temperature input)'; re-worded /session_locked_predictive/frames[41]/provenance/scenario_source; ref: 'evaluate.episode_cycle() / make_grade_climb()'; new: 'evaluate.episode_cycle(plant) / engine_env.locked_climb()'. lab_compare.py: no value differs; source-line numbers moved with the edited files, and the re-worded strings are three distinct texts, one under each key it lists, each naming a default which no longer exists.
- **verify_docs.py, the list of checks** (checks renamed or replaced): only in the reference: "CHECKPOINT.md 99 lines (fails above 150)", "OIL_PROTECT_K", "TURB_PROTECT_K, the damage knee", "Vehicle.final_drive", "Vehicle.gears, the ZF 8HP51 ratio set", "scenario ambient, make_grade_climb(t_amb=)", "scenario grade, make_grade_climb(grade=)", "scenario speed, make_grade_climb(v_kmh=)", "training episode length, make_grade_climb(duration=)", "training step, make_grade_climb(dt=)"; only in the candidate: "CHECKPOINT.md 111 lines (fails above 150)", "scenario ambient, the plant's locked climb (t_amb)", "scenario grade, the plant's locked climb (grade)", "scenario speed, the plant's locked climb (v_kmh)", "the car's final drive", "the car's gears, the ZF 8HP51 ratio set", "the damage knee (turb_knee_k, was TURB_PROTECT_K)", "the oil knee (oil_knee_k, was OIL_PROTECT_K)", "training episode length, train.DURATION_S and EngineEnv()", "training step, train.DESIGN_DT fixed/random, SupervisoryTunerEnv(dt=)". make_grade_climb has no defaults, so the two checks that read its duration= and dt= defaults (900 s, 0.2 s) read the values where they live now: train.DURATION_S and EngineEnv's climb, train.DESIGN_DT for Phase D's and D2's roads, SupervisoryTunerEnv's dt (the review: build step 1 had merged them into one structural check that nothing could fail independently); the others read the plant's records.
- **test_results: failing tests (L5)** (pre-existing failures): No test fails on the candidate alone; 6 fail on cf43fbb as well (a git clone, the same interpreter); the two that fail on cf43fbb only are skipped on the candidate while its plant files are uncommitted (app/test_results.py: 'the plant files or random_road.py have uncommitted changes'). Candidate only: none; `cf43fbb` only: test_a_schema_1_record_is_read_by_schema_1s_rule_and_never_called_this_plant, test_the_git_route_recomputes_plant_and_road; both: test_another_python_through_git, test_another_python_with_no_route_through_git, test_dirty_plant_files_have_no_git_route, test_the_bytes_at_the_commit_must_be_the_bytes_hashed, test_the_launcher_names_the_results_tab_and_starts_the_server, test_without_git_only_the_git_facts_go.
- **test_agents: failing tests (L5)** (pre-existing failures): No test fails on the candidate alone; 2 fail on cf43fbb as well (a git clone, the same interpreter). Candidate only: none; `cf43fbb` only: none; both: test_page_assets_ids, test_the_lab_launcher_names_the_agents_page.
- **test_simulation: failing tests (L5)** (pre-existing failures): No test fails on the candidate alone; 1 fails on cf43fbb as well (a git clone, the same interpreter). Candidate only: none; `cf43fbb` only: none; both: test_the_page_can_actually_load_every_asset_and_id_it_references.
- **lab_tests: failing tests (L5)** (pre-existing failures): No test fails on the candidate alone; 3 fail on cf43fbb as well (a git clone, the same interpreter); the one that fails on cf43fbb only is the premise pin build step 1 corrected, -0.32 to -0.01 (results/premise.json since 75ca65f; the comment beside it in test_catalog.py). Candidate only: none; `cf43fbb` only: test_results_are_current_and_inconclusive_with_explicit_caveats; both: test_frame_exposes_step_input_time_at_road_transition, test_locked_scenario_pins_source_evaluation_episode_one, test_preview_blinding_only_zeros_future_grade_channels.
- **python random_road.py, the self-test** (a code hash: the D2 protocol's road_sha): cf43fbb: road_sha : e44153fd81eeaa1e; candidate: road_sha : be19b3d0bcef435d. random_road.code_sha() hashes the module's code: its self-checks build the B58's locked climb by name, and since the review RandomClimb and evaluate.episode_cycle refuse a plant whose locked climb is not the Supra's (check_plant); climb() is unchanged and every random-road job is bit-identical.
- **check_random_road.py, stdout (finding 11)** (the D2 road_sha and the run time): cf43fbb: trigger 850 C; ranges start (120.0, 300.0) s, grade (0.12, 0.16); road_sha e44153fd81eeaa1e; candidate: trigger 850 C; ranges start (120.0, 300.0) s, grade (0.12, 0.16); road_sha be19b3d0bcef435d; cf43fbb: (40.2 min); candidate: (46.3 min). road_sha hashes random_road.py's code (the self-test above); the run time is the machine's. Every figure and the verdict, PASS, are the same in both trees.
- **training's final.zip files (L8)** (zip bytes): the 'data' member. stable-baselines3 stores run metadata there; every tensor and every counter is compared.
- **The candidate between its first and its last run**: 9 files changed: `CHECKPOINT.md`, `README.md`, `STATE_HISTORY.md`, `engine_specs/a90_supra.toml`, `fingerprint.py`, `full_run.py`, `results/VALIDATION_DECISIONS.md`, `test_wide_air.py`, `wide_air.py`. None of them is code a level computes with: CHECKPOINT.md, README.md and STATE_HISTORY.md are the documents swept with the review's results; results/VALIDATION_DECISIONS.md was committed by another session (e9e16ed: decisions 27, 32 and 34 revised); fingerprint.py changed in its docstring only (its code, _code_only, is the same), wide_air.py in a comment, and engine_specs/a90_supra.toml in a comment that named decision 34 before its revision (its values, which plant_sha and engine_sha hash, are the same: ded8da308863d394 and 99d2a9658b1258a7 printed after it); full_run.py in the expected-output text of three blocks (the test counts); test_wide_air.py in a stand-in's parameter, renamed so the name scan does not take it for plant.py (its 17 tests ran after the change).

## 6. The review of 21 October: 21 findings

Two reviews read build step 1 and its first certificate, one for correctness and one for
the project's rules. Each finding was reproduced on a copy of the tree as it stood; the
evidence of each, before and after, is in the archive (`repro/`, `F2/`, `F11/`).

| # | finding | verdict | what changed |
|---|---|---|---|
| 1 | the B58 table's grid, 42 C, a 365 K block and 30 settling steps were defaults beside plant=, and the threading test could not see them (`engine_env.py:1066 (measure_deliverable_torque); wide_air.py:114, 150`, medium) | **fixed** | measure_deliverable_torque(rpms, *, plant) and wide_air.deliverable_torque(p_kpa, rpms, *, plant) read the table's conditions from the car's record (engines.Car.table_rpm_lo/hi/step, table_t_amb, table_t_block, table_settle; typed in engine_specs/a90_supra.toml with label and source), derive_params passes plant.car.table_rpms; closed_throttle_nm(env, t_amb) reads table_t_block and wide_air.CLOSED_SETTLE; car_thermal.oil_time_constants(drives, *, plant) (the extended scan found it). test_engine_threading's new Defaults rule flags any default beside a record unless PROTOCOL_DEFAULTS or PLANTS_OWN_IF_NONE names it, with a control |
| 2 | build_dataset.py could no longer run before data/derived_params.json exists (`build_dataset.py:235; new_drive.py:178`, medium) | **fixed** | engines.typed_engine(name): the geometry, cycle and charge records from the spec alone (a record with a DERIVED field is refused, never given NaN); build_dataset._engine and new_drive.py use it |
| 3 | the thin-air ratios were cached by plant.id, which a dataclasses.replace variant keeps (`wide_air.py:184 (thin_air_ratios)`, low) | **fixed** | cached by the frozen Plant itself (value equality); test_wide_air Gearbox.test_a_variant_gets_its_own_ratios |
| 4 | plant_sha hashed the B58's two specs whatever plant was passed (`fingerprint.py:104 (PLANT_FILES)`, low) | **fixed** | fingerprint.PLANT_CODE and plant_files(name) = PLANT_CODE + engines.spec_files(name); plant_fingerprint hashes plant_files(engines.name_of(plant)), name_of refusing an unregistered or doubly registered plant; PLANT_FILES removed; app/results_provenance, app/agent_catalog, reconstruct_meta, the lab's catalog and make_page name the B58's list |
| 5 | the spec-by-values rule applied only when the text failed to parse as Python (`fingerprint.py:179 (_code_only)`, low) | **fixed** | fingerprint._file_code(name, src) picks the rule by the file's kind (.toml by its values); _sha_files, reconstruct_meta.plant_sha_at and results_provenance.code_hash (names= required) use it; _code_only no longer falls back to the spec rule |
| 6 | the FATAL backend came from a keyword default no caller passed (`fingerprint.py:320 (backend)`, low) | **fixed** | backend is required; fingerprint.backend_of(env) reads it from the environment (cycle without an engine_model; an engine_model or a non-environment refused); train.py reads it from its environment, the seven other callers pass BACKEND_CYCLE with the reason; anything but 'cycle' is refused until decision 28 |
| 7 | the 900 s and 0.2 s value checks were replaced by one that cannot fail independently (`verify_docs.py:1349`, low) | **fixed (with 8)** | see 8 |
| 8 | the guard was weakened and drift_test had no row for either value (`verify_docs.py:1349`, medium) | **fixed** | two value checks where the values live: train.DURATION_S (a module constant, --duration's default) and EngineEnv's climb (900 s); train.DESIGN_DT fixed/random, SupervisoryTunerEnv's dt and EngineEnv's (0.2 s); drift_test rows 17 (DESIGN_DT fixed 0.2 -> 0.5) and 18 (DURATION_S 900 -> 600); the certificate's sentence corrected |
| 9 | editing engines.py or engine_specs/ prompted no re-run of the plant's suites (`.claude/rules/physics.md:2; CLAUDE.md:137`, medium) | **fixed in physics.md; CLAUDE.md left for Jad and Ghassan** | physics.md's paths name engines.py and engine_specs/**; CLAUDE.md holds the permanent rules, and widening its line 137 to name engines.py and engine_specs/ is theirs to write, as the finding says |
| 10 | nothing tested that engine, engine_sha and backend are FATAL or that a schema-2 record is refused (`fingerprint.py:109 (FATAL, schema_problem)`, medium) | **fixed** | test_plant_guards.SchemaThree, 8 tests: the three fields FATAL, with a control (a FATAL tuple without engine_sha is caught); schema_problem; evaluate.check_model_fingerprint refuses a schema-2 meta.json (a synthetic one, and X1's own where the machine has it), passes a schema-3 one, refuses another engine field by field; train.refuse_old_schema, factored out of train.main, refuses schema 2 and passes a fresh directory, schema 3 and --force-plant-mismatch |
| 11 | suites that read the plant were not run (`.claude/rules/app.md:26`, medium) | **fixed (run); two plot scripts broken on cf43fbb too, reported** | the lab's npm ci, npm run build, launch.py --no-browser and --check; check_roads.py's 40 terrain roads and check_random_road.py in both trees; evaluate.py --protocol d2 end to end in both trees (no D2 agent is on this machine: the three hand-written policies, and X1's agent refused under d2); every app suite. app.test_results after the commit cannot run here (nothing is committed). plot_sim_vs_car.py and plot_study_page.py fail to import on both trees (fit_envelope has no envelope since cbb8d09): pre-existing, for main |
| 12 | the certificate's tools and evidence lived only in a session's scratch folder (`results/B58_IDENTITY.md:174`, medium) | **fixed** | results/B58_IDENTITY/certificate_tools.tar.gz: every tool and the small evidence files, its sha256 in the JSON and the .md; the shell tools find their own folder, so the archive unpacked anywhere is S; the reproduce section is written against it. Uncommitted, as the task asks; not git-ignored (*.zip is) |
| 13 | the committed terrain-road check is stale since 75ca65f, on cf43fbb too (`results/training_roads.json`, low) | **real, pre-existing; left for main** | confirmed: check_roads.py's 40 terrain roads write the same file in both trees, and it differs from the committed one. The fix -- regenerate it on main in its own commit, then grep the tree for its old figures (mistake 11) -- belongs on main, which this task must not touch |
| 14 | the frozen drive-C files were said to refuse on a plant_sha mismatch; they crash before it (`test_engine_threading.py:40; results/B58_IDENTITY.md:168`, low) | **fixed** | both sentences say what was measured: plant_check, which stages A, B and C call first, stops with an exception before its comparison (TypeError on derived_sha() before the review, AttributeError on fingerprint.PLANT_FILES after); FrozenFiles.test_drive_c_analysis_cannot_run_on_this_tree asserts it; the frozen files untouched |
| 15 | skipping logs/epa/ also hid logs/epa/README.md from the scan (`verify_docs.py:186`, low) | **fixed** | verify_docs skips EPA's own files only, the repo_path rows of logs/epa/MANIFEST.csv (epa_files); the README is scanned; drift_test run after the change |
| 16 | the live documents described the old state and quoted commands that now stop on --engine (`CHECKPOINT.md:4 and README, results/README, data.md`, low) | **fixed** | CHECKPOINT.md carries GRA-test's state (the replaced line moved verbatim to STATE_HISTORY.md part O); README.md (train_all --engine b58, the wide_air line, the new files in the layout, the drift count); results/README.md (the quoted commands kept as they ran, with what GRA-test requires); .claude/rules/data.md; fingerprint.py's docstring. The grep of 3c48890dd15bc116, 'schema 2' and '74 checks' finds main's state, X1's and X2's records and dated history only |
| 17 | unanswered decisions 31 and 34 were written as adopted; [repo_current] pointed at moved lines (`engine_specs/a90_supra.toml:15, 32; engine_specs/cars/`, low) | **fixed** | 'recommended, unanswered' wherever 31 and 34 are named; [repo_current] points at engine_specs/a90_supra.toml, and test_epa_map checks it against engines.get('b58').car, with a control |
| 18 | numbers with no committed script; two Supra EPA rows unverified; attributions missing (`engine_specs/cars/README.md:91 and the car files`, low) | **fixed** | the three numbers marked UNVERIFIED where they stand; the MY2021 and MY2023 Test Car Lists fetched into scratch with fetch_engine_data.py (sha256 equal to D3_AND_EPA_SOURCES.csv) and all nine EPA rows checked against their files, the two Supra rows among them (the team's data folder still lacks the two lists); Argonne's attribution in engine_specs/cars/README.md; REFERENCES.md section 8 for EPA and Argonne |
| 19 | single-engine assumptions: derived.PATH, D2 roads that ignore the plant, one backend field (`derived.py:37; evaluate.py:254; fingerprint.py:109`, low) | **fixed in two parts; schema 4 left until decisions 27 and 28 are answered** | derived.PATH renamed derived.B58_PATH at all eight uses; random_road.check_plant refuses a plant whose locked climb is not the Supra's speed and ambient (in RandomClimb and evaluate.episode_cycle); fingerprint schema 4 (the horizon H, separate training and scoring backends) is in CHECKPOINT.md's next actions, before any new engine trains |
| 20 | egt_limit_k was DESIGN with no source recorded (`engine_specs/b58.toml:140`, low) | **fixed** | labelled ASSUMED; labels and sources are not hashed, so plant_sha and engine_sha do not move on it |
| 21 | a stray crash dump was neither tracked nor ignored (`bash.exe.stackdump`, low) | **fixed** | *.stackdump in .gitignore: git add -A, the manifest and drift_test's copy no longer take it; the file itself is left for its owner to delete |

## 7. What this does not cover

- **Python 3.12, and the training device.** Every run is 3.13.2, on this laptop (rule 4).
  Decision 32, revised on 21 October and open, would train on another device and re-run
  this certificate there first.
- **The precision of three comparisons**, measured in section 2: the per-step records against
  the committed `eval_record.npz` are float32, training sees float32, and the learning lab's
  40-step sessions do not show one ulp of `c_turb`, so none of the three can tell one ulp of
  the plant. The plant is certified at full precision by L1–L3 and by L6's comparison of the
  two trees.
- **The jobs, not every input.** The harness samples operating points, roads, seeds, airs
  and policies; the identity holds for the code paths those jobs run (section 3). No D2
  agent is on this machine, so `--protocol d2` was scored end to end on the hand-written
  policies only.
- **The four frozen drive-C files** (`drive_c_analysis.py`, `drive_c_rule_numbers.py`,
  `drive_c_check.py`, `test_drive_c_analysis.py`) were not run as stages. They cannot run
  on `GRA-test`: `drive_c_analysis.plant_check`, which stages A, B and C call before they
  read anything, stops with an exception before its plant_sha comparison is reached
  (`AttributeError`: `fingerprint.PLANT_FILES` is gone; before the review, `TypeError`:
  `derived_sha()` requires its path). The first certificate said they "refuse by design";
  nobody had run it (finding 14). `test_engine_threading.FrozenFiles` checks it. They wait
  for stage C on `main` (decision 25).
- **What this machine lacks**: `pwsh` (one error each in `app.test_agents` and
  `app.test_results`, eight skips in `app.test_launcher`), `runs_c4/` (14 skips in
  `app.test_agents`), any D2 agent, and in the team's data folder the MY2021 and MY2023 Test
  Car Lists (checked here on downloads whose sha256 equals the list's; `python
  fetch_engine_data.py --group epa-test-car-list` adds them).
- **Nothing is committed.** `app.test_results` skips two tests while the plant files are
  uncommitted; run it again after the commit.
- **The certificate is for this tree against `cf43fbb`.** A new drive re-derives the B58
  (`data/derived_params.json`), and stage C may retune it; either one needs a new
  certificate before the B58 of `GRA-test` is called X1's plant again (decision 25).

## 8. Reproduce

Every tool and the small evidence files are in `results/B58_IDENTITY/certificate_tools.tar.gz` (586 569 bytes,
sha256 `a639190b605c177142e9bc3f95295bc7ae0c335732a4ab6a082e6dbef01503fb`). Unpacked anywhere, that folder is `S`: the tools find it
from their own location. The reference side is a fresh `git archive` of `cf43fbb` into
`S/ref`; the dumps themselves (`.npz`) are not archived and are re-made by the commands.
`make_cert.py`, run from the unpacked folder against this archive, writes this JSON again
but for two hashes of files the archive leaves out, both re-made by the commands: the
`cf43fbb` tar (`reference.archive_sha256`) and L7's scratch `final.zip`
(`levels.L7_evaluate_end_to_end.meta_json_sha256.scratch_final_zip`).
`PY` is the venv's `python.exe`, `REPO` this repository; Git Bash.

```
# reference tree (REPO)
mkdir -p $S/ref && git archive --format=tar cf43fbb | tar -x -C $S/ref
# candidate copies for the writers (any)
$PY -I $S/tools/copy_tree.py REPO $S/cand; $PY -I $S/tools/copy_tree.py REPO $S/candd
# candidate manifest, at the start and at the end (any)
$PY -I $S/tools/manifest.py REPO $S/manifest_start.txt   (and manifest_end.txt after the last run; make_cert lists every file that differs)
# fingerprints (REPO / REF)
$PY fingerprint.py --engine b58 > $S/out/fp_cand.txt; $PY engines.py   |   (in REF) $PY fingerprint.py > $S/out/fp_ref.txt
# L1, L2, L3 harness (any)
$PY -I $S/tools/run_jobs.py REPO cand $S/tools/jobs_all.txt 6; (reference: $PY -I $S/tools/run_jobs.py $S/ref ref $S/tools/jobs_all.txt 3); bash $S/tools/compare_all.sh ref cand
# controls (harness) (any)
$PY -I $S/tools/run_jobs.py REPO ctl_cturb $S/tools/jobs_ctl.txt 2 HARNESS_PERTURB=thermal.c_turb; the same with ctl_mass and HARNESS_PERTURB=car.mass; (reference: run_jobs.py $S/ref ref2 jobs_ctl.txt 2); bash $S/tools/compare_all.sh ref ref2; compare_all.sh cand ctl_cturb; compare_all.sh cand ctl_mass
# L3 check_premise (any)
CAND=$S/cand bash $S/tools/run_writer.sh cand premise results/premise.json check_premise.py   (the reference: run_writer.sh ref ... in $S/refw)
# L4 test_reward (any)
bash $S/tools/run_l4.sh cand; bash $S/tools/run_l4.sh cand --road random; (and ref); cmp $S/L4/cand_stdout.txt $S/L4/ref_stdout.txt
# L5 check_roads, and finding 11's road checks (any)
bash $S/tools/run_roads_review.sh   (--road extremes and --road wideair in $S/cand; the 40 terrain roads and check_random_road.py in $S/cand and $S/ref)
# L5 validate (REPO and REF)
$PY validate.py > out.txt in each; cmp the two
# L5 generality (any)
CAND=$S/cand bash $S/tools/run_writer.sh cand generality results/generality.json generality_test.py
# L5 derive_params (any)
(cd $S/candd && $PY derive_params.py); $PY -I $S/tools/derived_check.py REPO/data/derived_params.json $S/L5/derived_params_DERIVED_cand.json $S/L5/derived_params_DERIVED_ref.json --json $S/L5/derived_check.json
# finding 2: build_dataset without a derived file (any)
$PY -I $S/tools/bd_dump.py $S/candd $S/F2/cand.npz <every logs/raw csv>; the same in $S/ref; $PY -I $S/tools/cmp.py $S/F2/ref.npz $S/F2/cand.npz --json $S/F2/cmp.json; new_drive.py on pull01 in both copies with the derived file moved aside
# finding 11: evaluate.py --protocol d2 (REPO and REF)
$PY evaluate.py --engine b58 --protocol d2 --out $S/F11/cand_d2.txt (REPO); $PY evaluate.py --protocol d2 --out $S/F11/ref_d2.txt (REF); $PY -I $S/tools/l7_diff.py $S/F11/ref_d2.txt NONE $S/F11/cand_d2.txt NONE --json $S/F11/d2_diff.json (no model: NONE); and REPO's evaluate.py --engine b58 --protocol d2 on the L7 scratch model: refused
# finding 11: the learning lab ($S/cand/Explanatory Simulation)
npm ci; npm run build; $PY launch.py --no-browser (one window); $PY launch.py --check (another)
# L5 app suites and the learning lab's tests (any)
bash $S/tools/run_app.sh cand; bash $S/tools/run_app_extra.sh cand; (cd REPO/app && node --test static/sim/*.test.mjs) > $S/app/cand_node_tests.txt
# L5 learning-lab outputs (any)
$PY -I $S/tools/lab_dump.py REPO $S/lab/lab_cand.json; $PY -I $S/tools/lab_compare.py $S/lab/lab_ref.json $S/lab/lab_cand.json   (controls: LAB_PERTURB=thermal.c_turb and thermal.c_turb:1e-9)
# L6 X1 agents (any)
$PY -I $S/tools/l6_agents.py REPO <tag> $S/L6/cand_<tag>.npz for the four tags; bash $S/tools/check_l6.sh; controls: HARNESS_PERTURB=car.mass / thermal.c_turb (5 episodes), car.mass:1e-9 / car.mass:1e-6 (2 episodes) for sighted_seed0, then l6_check.py
# L7 evaluate.py end to end (REPO)
$PY -I $S/tools/make_meta.py REPO REPO/runs/extremes_dt1/sighted_seed0 $S/L7/cand_model/sighted_seed0; OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 $PY evaluate.py --engine b58 --out $S/L7/cand_eval.txt $S/L7/cand_model/sighted_seed0; $PY -I $S/tools/l7_diff.py $S/L7/ref_eval.txt REPO/runs/extremes_dt1/sighted_seed0 $S/L7/cand_eval.txt $S/L7/cand_model/sighted_seed0 --json $S/L7/l7_diff.json; $PY -I $S/tools/l7_expect.py $S/L7/cand_eval.txt
# L8 training (any)
bash $S/tools/run_l8.sh, then l8_perturbed.py with car.mass:1e-9 and car.mass:1e-6; $PY -I $S/tools/l8_compare.py <ref run> <cand run> --json ... for each pair and each control; run_identities.json from each run's meta.json; then the run directories deleted
# suites (any)
bash $S/tools/run_suites.sh; and test_epa_map.py with GRAD_EXTRA_DATA naming the MY2021 and MY2023 Test Car Lists fetched by fetch_engine_data.py --target <folder> --group epa-test-car-list
# drift_test (REPO)
bash $S/tools/run_drift.sh   (python drift_test.py in parts, each with drift_test's own control); then, with the certificate's page, JSON and archive in REPO, $PY -I $S/tools/drift_control.py REPO $S/suites/drift_control_with_certificate.txt (drift_test.control() in a copy that holds them, after checking that git does not ignore them)
# the certificate (any)
$PY -I $S/tools/make_archive.py REPO/results/B58_IDENTITY/certificate_tools.tar.gz; $PY -I $S/tools/make_cert.py REPO/results/B58_IDENTITY.json REPO/results/B58_IDENTITY/certificate_tools.tar.gz; $PY -I $S/tools/make_md.py REPO/results/B58_IDENTITY.json REPO/results/B58_IDENTITY.md (the archive is made after the drift control, whose output it holds, and before make_cert, which records its sha256; the drift control ran once more on the final files)
```

Every command, with its working directory, is in the JSON under `reproduce`; `tools/certify_original/` holds the first certificate's tools as they ran.

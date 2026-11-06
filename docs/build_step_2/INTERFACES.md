# Interface sheet: the code from C1b to the preregistration

*2 November 2026, branch `GRA-test`. Written by the AI agents, read-only. Sources: the eight implementation specs (C2, P1-P4, G, V, T), their cross-spec critic and the eight resolutions, read against `91c6ece` (row 134, committed and pushed), and C1b's draft of 2 November, built in a scratch clone and not pushed: section 3 names what it defines. Two adversarial checks of the first draft, one on the rules and one on the build, found 30 defects (3 blocking, 10 material, 17 minor). A second round, the same two checks of this sheet and a review of C1b's draft, found 38 more (1 blocking, 8 material, 29 minor). A third round, one check of this sheet and a review of C0's and C1b's drafts, found 19 more (6 material, 13 minor). On 2 November Ghassan answered row 136: engines leave in the order the Honda, the Mazda, the Ford, and an engine that leaves is dropped, with no table. That removes every table branch of this sheet, and six of the third round's findings with it. A fourth round, one check of this sheet and the rows, found 9 more (1 material, 8 minor). Its material finding, that the first draft of row 136 ended with the B58 alone, is settled by Ghassan's confirmation of the same day: the Ford, the last to leave, leaves only when it and the B58 cannot reach n ≥ 20, and then no EPA engine survives, the four-engine test does not run, and the failed schedule is reported as the result (row 136 (1); MD:1611-1612). Every other finding is applied here; section 16 says where, and which are moot. Nothing was run for this sheet. No held-out row, `logs/epa/` table or EPA table CSV was opened.*

*Citations: a code line is cited at `91c6ece` unless it says otherwise. Where C0 or C1b moves the lines a later commit edits (`benchmark_training.py`, `engine_gate.py`, `test_device_gate.py`, `test_four_engine_training.py`), that commit's items are cited by name. A line of `results/VALIDATION_DECISIONS.md` (VD) is cited as of the commit that lands the citation, or a row is cited by its number: O1's provenance line moves every VD line from :69 on by 4, and O2's by 3 more. A step of `docs/build_step_2/ORDER_TO_TRAINING.md` is cited by its number ("ORDER step 20"), never by its line, since O1 rewrites its rows; ORDER:5, the rule line, is the one line cited, and O1 does not move it.*

*How it binds:*
- *It is binding through rows 135-143 of `results/VALIDATION_DECISIONS.md` (section O).*
- *Where a row and this sheet differ, the row governs. Where a spec and this sheet differ, this sheet governs.*
- *Row 136 is Ghassan's own answer of 2 November, with his confirmation of the same day of where the order of leaving ends, committed in O1 with rows 137-143, before step 3's rate is known: contract version 6 for the order of leaving and the table route only. Row 135 is written after step 3, in O2. This sheet says what row 135 must fix; the committed row governs.*
- *Each name is defined once, in the section of the commit that owns it. Every other commit imports it and never retypes it (mistake 10).*
- *It is committed in O1 as `docs/build_step_2/INTERFACES.md`, outside every frozen list.*

## 0. The commits, in order

| id | ORDER step | contents | lands |
|---|---|---|---|
| R134 | 2 | row 134 and `tools/device_step3.sh` | **done**: `91c6ece`, pushed. T's W constants and PR's crash-rule clause cite it |
| O1 | docs | rows 136-143 with section O's note and its provenance line (4 lines): row 136, Ghassan's answer of 2 November, and rows 137-143; this sheet; `results/EPA_TIT_CAP/README.md:19-21` corrected (row 138 (3)); ORDER rows 12a-22, its line-3 "Next" sentence, and the clauses of ORDER:5 and step 9 rewritten to this table; CHECKPOINT's pointer. The session report records the citation conventions and the stale citations they leave: row 134's "(VD:340)" (section I's note is VD:343 at `91c6ece`, VD:347 from O1 on) and, from C1b on, row 134's `benchmark_training.py:36-38`; and the rows read through row 136 (the session note). No earlier row is edited | now, before step 3's rate and before the rehearsal |
| C0 | step 7's rule | `test_four_engine_training`'s two REAL-reveal fixtures of `ScoredShareSYNTHETIC`, which fail from R0 on (section 2). Test code only, in no hashed list | done: `fefb7af` (2 November, on Jad's `b2151af`) |
| C1b | step 7's rule | the benchmark protocol (section 3), without the dormant `--table-record` of its draft (row 136). `verify_docs` is run in the repository by whoever commits it | after C0; before O2 and E1; never between an arming and its F |
| S | (scratch, no commit) | the two measurements row 135 records, each on a scratch draft in a git clone outside the repository, on an idle laptop: the blinded arm's bit-for-bit test (row 135 (5)) and the SYNTHETIC part of the Honda's row-119 gate, every check line its command prints (rows 135 (8), 137 (6)) | before O2 |
| (none) | 3 | step 3 on the training device, `tools/device_step3.sh` | now (Team) |
| O2 | docs | row 135 | after step 3 and S, before the rehearsal (step 9) |
| E1-F3, L, R4 | 9-12 | unchanged | |
| C2 | 12a | section 4 | after R4 |
| (none) | 13 | the defect-route test and the review of F1-F3 (section 14) | after C2 |
| RV | 14 | section 5 | after step 13 |
| P | 14 | section 6: P1 + P2 + P3, one commit, carrying `results/EPA_ROADS/reverify.json` | after RV |
| Qa | 14a | Q's code (section 9) | after P, before Q's runs |
| G | 15 | section 7 | after Qa |
| V | 16 | section 8 | after G |
| RS | 16a | `rescore_rows.py` and its test (row 142) | after V, before PR |
| Q | 17 | Q's outputs (section 9). Its runs, in a clone of Qa, may start right after Qa | committed after V, before B1 |
| CU | 17a | the CUDA lock and `check_training_device.py`'s CUDA path (row 118; row 135 (6)) | only if row 135 names CUDA: after P, before Ta |
| Ta | 17b | the backend's code (section 10) | after P (and CU, if any), before B1 |
| B1 | 18 | the device's attempt files and B0 records (row 135) | from a pushed tree holding V, Q, CU (if any) and Ta |
| Tb | 19 | the backend record (section 10); with n null, the report of the failed schedule (10.2) | after B1 |
| PR | 20 | section 11; not written when Tb's n is null (row 136 (1)) | after Tb and RS |
| PL | 21 | decision 29's pilot | after PR |

There is one order to training, with no table (row 136): ... Ta, B1, Tb, PR, PL, then training (step 22). It stops at Tb when Tb's record holds n null: no EPA engine survives, so the four-engine test does not run, and the failed schedule is reported as the result (row 136 (1); MD:1611-1612; 10.2). There is no PV commit. The re-verification record is committed in P (row 140 (3)), and G and V follow P. The fourth arm, if row 135 (5) records one, is P's (6.9). Commits that edit the same file land in this table's order (P before Qa, Qa before G, G before V), and section 2 lists their edits in it.

### 0.1 The drafting order

All drafting happens in scratch `git clone`s outside the repository, never in `copy_tree` or `git archive` copies. Two rules hold throughout:
- Tests run only when the laptop runs nothing else of rule 1.3's list.
- Anything that reads `redraws.json` runs only after R4.

1. **Now, first.** Write this sheet and rows 136-143 (O1). Nothing in P or V is drafted to final before them.
2. **Now, in parallel, while step 3 runs on the device and the laptop is idle:**
   a. **C0 (committed, `fefb7af`), then C1b** (section 3). These come first, because row 135 must name C1b, and C0 clears C1b's gate. C1b's self-tests include the extremes byte-identity and the four-engine `train.py` command through `train.py`'s own parser and `check_recipe` (`train_check`). Both are drafted (2 November, in a scratch clone, not pushed); C0 and C1b take the changes section 16 lists before their commits, C1b's removal of its dormant `--table-record` (row 136) among them.
   b. **A minimal scratch draft of P1's H parameter** (`PREVIEW_H_S`, `preview_samples`, `_preview` reading `self.preview_s`) and `test_preview_horizon.BlindBitForBit`. Run it once. Its MEASURED result goes into row 135 (5).
   c. **A scratch draft of C2** (`step_record`'s CVT branch and `train.py`'s recorder, section 4). Run the SYNTHETIC part of the Honda's row-119 gate on it once: `test_reward.py --engine honda_l15b7 --train-road four_engine --synthetic-seed 101`, output outside the repository. Every check line it prints, with its result and detail, goes into row 135 (8) (row 137 (6)).
3. **After step 3 and S, before the rehearsal.** Write row 135 (O2) from step 3's merged file and S's two results.
4. **From then through R4.** All of this is text only while Run 2 runs.
   a. **C2** (section 4). Rebase onto R4 when it lands.
   b. **RV** (section 5). It needs `redraws.json`, so its tests run only after R4.
   c. **P-core: P1 and P3 on one branch** (sections 6.1, 6.2, 6.4-6.8). Measure the golden digests on C2's tree once C2 exists.
   d. **P2** (section 6.3 and its tests), on P-core's names, the backend layout of row 139 (3) and the re-run rule of row 139 (1). Rebase onto F3 and then R4 before RealTree and Openable run.
   e. **G's code, writer, record and test**, plus the WP7 documents that need neither P nor Run 2's labels (section 7).
   f. **Qa** (section 9) and **Ta's skeleton** (section 10). PROTOCOL and CPU_PROTOCOL are typed once row 135 exists. CU too, if row 135 names CUDA.
5. **Once P-core's fingerprint API is stable** (`d34_roads`, `for_arm`, `pair_problems`, the knock keyword): V (section 8), then RS's `rescore_rows.py`.
6. **After row 135 and P2's layout:** Ta final, and the PR skeleton (section 11). Its sensitivity section points at row 142, and its compute and environment at row 143.
7. **Q's command set**, once P's knock option and `FP.d34_roads` exist. Its runs start right after Qa.

### 0.2 Times and the critical path

Every time here is ASSUMED unless a source is named.

| part | time |
|---|---|
| C2 | about 3.5 h |
| step 13 | about 1 h |
| RV | about 3.5 h, of which the control is about 2.2 h (the draw's step times, `results/EPA_ROADS/attempt_1_printed.txt`) |
| P | about 13 h once drafted, of which the full roads check is about 10.7 h (ibid., assumed equal for the re-run) |
| Qa | under 1 h |
| G | about 3 h |
| V | about 3 h |
| Q | 3-8 h (row 134), in a clone, beside G and V; the share-on `check_roads.py` run per engine (section 9) is not timed (ASSUMED small) |
| CU | only on CUDA; not timed |
| Ta | under 1 h |
| B1 | 3-5 h (row 134); 4 h taken |
| Tb | about 1.5 h |
| PR | 6-16 h (row 134) |
| pilot | about 21 h (row 112) |

**The critical path after R4**: C2, step 13, RV, P, Qa, G, V, B1 and Tb, 3.5 + 1 + 3.5 + 13 + 1 + 3 + 3 + 4 + 1.5 = 33.5 h, with Qa taken at 1 h (it sits in series between P and G, since it is G's parent), then PR and the pilot, so 60.5-70.5 h (arithmetic on the parts above, each ASSUMED). Row 134's chain from 12a to the pilot is about 71-95 h. Q's tail beyond G and V can add up to about 2 h before B1 (8 h against G's and V's 6 h; arithmetic). Under row 136 no table work is on the path.

## 1. Rules for every drafter

1. **How every command runs.** `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/Scripts/python.exe -B`, on this laptop (rows 118, 126).
2. **Where drafts live.** Draft in scratch `git clone`s outside the repository, never in `copy_tree` or `git archive` copies: P's reader needs `.git` (row 139 (2)). Rebase onto R4 before running anything that reads `redraws.json`: TrainSmoke, D34Protocol, `FP.d34_roads`, V's LiveRoads, Openable, RealTree.
3. **When the laptop may run things.** During these windows, drafting is text only (ORDER step 10; rows 106, 125):
   - Nothing runs beside an arming or a run (E1-F3).
   - Nothing runs beside RV's control, or beside a roads check (`roads_reverify.py check`), except P's certificate runs during P's check. Each is single-threaded and deterministic, so only the wall time changes (ASSUMED).
   - `test_engine_threading` runs alone, because it creates `_scan_probe_*.py` files (`docs/build_step_2/PLAN.md:425`). In P it runs after the roads check and the certificate's runs. In G and V it runs while no Q run is going.
   - Q's runs may share the laptop with G's and V's other gates (ASSUMED, as above). They run in a clone of Qa, so no edit in the repository reaches them.
4. **Until R4.** Nothing in PLANT_CODE, `epa_freeze.CODE_HASHED` or roads.json's 35 hashed files changes (ORDER:5). C0, C1b, O1 and O2 touch none of them. **Every commit before R4** runs ORDER:5's two checks in its gates (C0, C1b, O1 and O2 here; E1-F3, L and R4 as ORDER already says):
   - `git diff --stat f48e5f0 -- plant.py thermal.py engine_env.py derived.py engines.py engine_specs/ evaluate.py requirements-lock.txt thresholds/split.py thresholds/common.py epa_coefficients.py epa_fit.py epa_freeze.py epa_map.py epa_rows.py epa_stats.py calibrate_epa.py k3_knee.py validate_epa.py d3_rows.py` prints nothing. The base is N (`f48e5f0`), because ORDER:5 takes the diff against N from N on.
   - `.venv/Scripts/python.exe -B -c "import epa_roads as R; print(R.verify_record(R.load_record(R.ROADS_REL), root=R.REPO))"` prints `[]`.
5. **From B1's `git_head` to Tb.** Nothing in `epa_backend.cost_files` changes (section 10). Every edit by C2, P, Qa, V, Q and CU to those files therefore lands before B1. A P re-made after B1's git_head repeats B1 (row 140 (5)).
6. **Defaults beside a record parameter.** The gate is `test_engine_threading`, and this rule cites it rather than restating it.
   - A record parameter is one of `RECORD_PARAMS = {"engine", "plant", "cal", "car"}` (`test_engine_threading.py:97`).
   - In a function that takes one, another parameter may default only if `PROTOCOL_DEFAULTS` (`:102-116`) names it with a reason, or `PLANTS_OWN_IF_NONE` (`:120-135`) names it and the default is None (`_default_allowed`, `:427-433`).
   - `record` is in `PLANTS_OWN_IF_NONE` (`:129`), so `record=None` is allowed.
   - `test_engine_threading.py` is in every code commit's gates.
7. **No default on a FATAL input (mistake 19).** `train_backend`, `score_backend`, `preview_h_s` and `reward_knock` are passed explicitly at every `plant_fingerprint` call. `test_engine_threading.CALLS['plant_fingerprint']` enforces this at every call site across the tree, and `test_engine_threading.Signatures.test_entry_points_require_their_record` at the signature (P1 replaces its `(FP.plant_fingerprint, "backend")`, `test_engine_threading.py:756`, with the four keywords). Section 2 assigns every caller to P.
8. **Guarded tests and the contract.** A `test_epa_fixtures.Guarded` test that builds a fingerprint does one of two things:
   - it patches the contract read: `mock.patch.object(FP, 'backend_contract', lambda: {'md_sha_text': 'stand-in', 'json_sha_text': 'stand-in'})`;
   - or it receives a prebuilt `live` block.

   One unguarded test reads the real contract (`test_plant_guards.BackendContract`). Never cache the contract at import.
9. **Numbers and hashes.** A number in a commit message or a document comes from the run that printed it (mistake 22). A number read by hand is not quoted. Hashes are not figures, so `verify_docs.RETIRED` is not used for them (decision 67).
10. **Every commit.** It runs `verify_docs.py` (CHECKPOINT within 150 lines) and updates the session report. `verify_docs.py` starts `compare_log.py` as a child without `-B` (`verify_docs.py:1638`), and in the scratch clone of 2 November it left a `__pycache__/` in the root (C1b's drafter, MEASURED). So it runs with `PYTHONDONTWRITEBYTECODE=1`, or the cache is deleted after it, before anything that refuses a bytecode cache beside a hashed file (RV's preconditions, section 5; R3b's launcher).
11. **Nothing waits for a row written after Run 2.** Every outcome a step can meet after the first arming has its consequence fixed now: rows 135 (4)-(5) and (8), 136 (1)-(2), 137 (6), 139 (1) and (4), 140 (5) and 141 (1). An outcome no row covers stops the step, and it is reported. It is never settled by a row written with the labels known (row 114), and no row written after Run 2 drops an engine (row 139 (4)).
12. **One environment per engine's agents** (CLAUDE.md rules 3 and 5). Every seed and arm of an engine trains on one device and one set of versions. V refuses anything else (section 8; row 143 (5)).

## 2. Who edits which file, in order

| file | edits, in commit order |
|---|---|
| `benchmark_training.py` | C1b only. Frozen from C1b on (row 135 (2)). |
| `engine_gate.py` | C1b: `share_record` and `record_name`; a required `roads_record` on `training_env`, `run_gate` and `road_table`, carried by the train tasks `job` reads; `print_gate`'s share line; the record named repository-relative wherever it is returned or printed (section 3). C2: the WHAT WAITS docstring's Accord bullet, on C1b's text (cited by name: C1b moves it). P: the H and knock keywords, `job`'s band and notch branches among them (6.6); `WaitsForPlantCommit` deleted; the WHAT WAITS docstring's H bullet and knock bullet, reworded to what P builds (6.6). Qa: `d34_roads` reads a REAL record through `FP.d34_roads`, and the WHAT WAITS docstring's decision-34 roads bullet is reworded with it (section 9). Every WHAT WAITS bullet is cited by name, since C1b moves them. |
| `test_reward.py`, `check_roads.py` | C1b: `--roads-record PATH` (with `--engine` and `--train-road four_engine` only), passed to `run_gate` and `road_table`; `check_roads.py`'s JSON keys `roads_record` (by `record_name`) and `share_seed_kind`, and its `default_table` (`_share_on` or `_share_off` on four_engine; 12.9). P (P3): `--reward-knock`, refused after every existing refusal (6.4), and `default_table`'s `_knock_in` or `_knock_out` (12.9). These two scripts are engine_gate's only command lines. |
| `test_device_gate.py` | C1b: the two `training_env` calls in Roads pass `roads_record=None`, and the `B.ROAD_OPTIONS` pin stays; `Roads.test_the_share_on_the_training_road_SYNTHETIC` and `Roads.test_the_record_is_named_relative_to_the_repository` (`record_name`, `default_table`); `Verdict.test_the_share_is_named_on_the_four_engine_road` (its gate dict gains `roads_record` and `share_kind`); Cli's refusals of C1b's options (`--merge` with `--roads-record` or `--reward-knock`; the draft's `--table-record` case goes with the option, row 136) and `Cli.test_the_benchmarks_four_engine_road_waits_for_the_plant_commit`; RunbookB1, on the runbook's own B1 and B5 text with `<row 135's interpreter>` and `$B1OUT` (section 3), and following B0's checkout, the B0 record and the CPU series once C1b's runbook takes them (section 16). P: `Roads.test_an_H_other_than_30_s_waits_for_the_plant_commit` rewritten (6.7); `reward_knock=False` in Roads' `training_env` calls and in BlindArm's `blind_check` call; `Verdict.gate`'s dict gains `reward_knock`; Cli's knock refusals (6.4); the band and notch jobs' knock test (6.6). Qa: Roads gains the REAL-record test of section 9. All named, not numbered: C1b moves this file's lines. |
| `docs/build_step_2/DEVICE_RUNBOOK.md` | C1b only: B0, B1 and B5 (section 3). |
| `step_record.py` | C2 only. |
| `train.py` | C2: the recorder (:364-428, :945). P: `build_env`, `check_recipe`'s knock refusal, `run_config`, the protocol map, the comment at :644-645, the reward line, `train_backend=FP.backend_of(...)` at :815; under four arms only, the blinded arm's `--horizon-ratio` (6.9). V: the docstring at :97-99. Nothing after B1. |
| `train_all.py` | P (P3) only: `--reward-knock`; under four arms only, `--blind-per-h` (6.9). Nothing after B1. |
| `four_engine_roads.py` | C2: the docstring at :124-127. RV: `current_reverify`, appended. P: `PREVIEW_DIVISORS`, `preview_h_problem`; under four arms only, `run_tag`'s blinded ratio (6.9). V: the docstring at :20. |
| `engine_env.py`, `fingerprint.py` | P only (P1, P3; and 6.9 under four arms). |
| `engines.py` | P only (P2: the reader). |
| `evaluate.py` | P: one merged edit (P1 + P3). V: decision 34, the practice route, the declared route, the environment check. |
| `check_training_device.py` | P: `fingerprint_dir`'s keys. CU, only if row 135 names CUDA: its CUDA path. |
| the CUDA lock | CU, only if row 135 names CUDA (row 118). |
| every other `plant_fingerprint` caller | P, in the same commit: `conditions_test.py:374`, `run_results.py:203`, `reconstruct_meta.py:249-253`, `app/agent_catalog.py:222-224`, `app/results_provenance.py:474-475`, `test_cars.py:901-908` and `:926`, `test_plant_guards.py:199`, `:279`, `:289` and `:314`, `test_epa_freeze.py:986`, `fingerprint.py:4` (the docstring) and `:740` (the CLI), and the probe line `test_engine_threading.py:582`. `evaluate.py:471` and `train.py:815` are in 6.5 and 6.4. |
| `epa_fit.py`, `calibrate_epa.py`, `validate_epa.py` | G only. |
| `roads_reverify.py`, `test_roads_reverify.py` | RV. |
| `tit_cap_rescore.py`, `test_scoring_protocol.py`, `test_tit_cap_rescore.py` | V. |
| `rescore_rows.py` and its test | RS. |
| `epa_backend.py`, `test_epa_backend.py` | Ta. |
| `results/EPA_ROADS/reverify.json` | P (written by `roads_reverify.py adopt`). |
| `results/EPA_CALIBRATION/bounds_active_corrected.json` | G. |
| `results/benchmarks/B1_*`, `results/benchmarks/B0_*` | B1 (and B1 repeated, rows 135 (4)(c), 140 (5)). Copied from `$B1OUT` on the device. |
| `results/ENGINE_GATES/<engine>/` | Q (copied from Q's clone). |
| `results/EPA_BACKEND.json` | Tb. |
| `test_cars.py` | C2: StepRecord and its docstring lines 72-73. P (P2): Fingerprint and its docstring lines 74-76; `:926`'s call. |
| `test_plant_guards.py` | P. P2: SchemaFour. P1: the golden helper, Transmission, BackendContract, Pairing, D34Protocol, GitDirtyPlantFiles, CycleBackendOnly. P3: RewardKnock, TitCapInterfaces. |
| `test_engine_threading.py` | P. P1: CALLS, Signatures (`:756`: the four keywords replace `(FP.plant_fingerprint, "backend")`), `PROTOCOL_DEFAULTS['preview_h_s']` and the probe at :582. P3: `['reward_knock']`. P2: Registry. V: CALLS for `run_road_episode` and `score_set`. |
| `test_four_engine_training.py` | C0: the two `ScoredShareSYNTHETIC` tests that fail from R0 on, at `91c6ece` and on C1b's first draft alike (`test_a_REAL_record_needs_its_reveal_checked_as_the_draw_checks_it_SYNTHETIC_reveal`, `test_a_REAL_record_trains_only_from_the_committed_roads_json`). `four_engine_roads.read_roads_record` also compares the tree's `epa_roads.COMMITMENT_G`/`COMMITMENT_J` with the reveal's lines, which R0 set, and the tests mock only `committed_hash_lines`. Each now sets both sources of the lines itself, and the first gains two controls (mistake 12). The module is unchanged, and the file is in no hashed list. C0 moves the file's later lines. P: P1: Isolation, `TrainAll.test_the_third_arm_is_refused_before_any_run_SYNTHETIC`, `TrainRefusals.test_every_H_but_30_s_waits_for_the_plant_commit`. P3: TrainSmoke's argv. V: `AFTER_V`. |
| `test_epa_tightenings.py` | V: `Isolation.test_no_hashed_module_imports_this_one`'s pin (`:949`, `len(files) == 35`) reads `35 + len(test_four_engine_training.Isolation.AFTER_V)`, the constant imported, never retyped. |
| `test_trainable.py`, `test_epa_plants.py` | P (P2). |
| `app/test_results.py` | P: the `live_side` import-error check. |
| `test_defect_route.py` | G (`LATER_HASHED`). |
| `make_meta.py` (certificate tool) | P, recorded in TOOL_EDITS.md. |

## 3. C1b: the benchmark protocol (row 135 names this commit)

### `benchmark_training.py`

Frozen from this commit to T. T checks `git diff --quiet <C1b> <git_head> -- benchmark_training.py` at every attempt's git_head (an operator fault otherwise, 10.1 `classify` (b)). Line numbers in this subsection are at `91c6ece`; C1b moves them.

**New options** (refused or admitted by `check_args` and `main`, never by the plan builder):
- `--roads-record PATH`
  - Allowed only with `--road four_engine` (`check_args`). It turns decision 29's share on (row 130 (5)).
  - PATH is repository-relative with '/' separators (`relative_path_problem`, called by `check_args`). `main` then requires, before the probe runs, `four_engine_roads.real_record_problem(<HERE>/PATH)` to be None and PATH to be spelt `epa_roads.ROADS_REL`.
- `--reward-knock {in,out}`
  - Required with `--road four_engine` (`check_args`). Refused with `--merge`.
  - Refused before P. `part_probe` reports `build_env_takes_reward_knock`, whether `'reward_knock' in inspect.signature(train.build_env).parameters`, and `main` refuses with "REFUSING: --reward-knock needs the plant commit P (row 127 (4))".
- **No `--table-record`.** C1b's draft (`dee0d9a`) carries it dormant, refused unless `train.py`'s parser has it. Row 136 builds no table, so C1b drops it before its commit, with every trace of it: the option and its help, `make_plan`'s `table_record`, `option_args`' and `train_cmd`'s `--table-record`, `PLAN_KEYS`' 'table_record', `part_probe`'s `train_takes_table_record` and `train_options()` if nothing else reads it, the `--merge` refusal's naming of it, the module docstring's "dormant until row 136's route (1)" lines, the selftest's table cases, and `test_device_gate.Cli`'s `--table-record` case (section 16).

**The plan builder and the option helpers** (finding 27 of round 1: an extremes plan is byte-identical):
- `make_plan(a) -> dict` builds the JSON's `plan` block from the parsed arguments. It applies no refusal, so a SYNTHETIC record outside the repository reaches it only in tests. It holds:
  - `road`, `engine`, `dt`;
  - with `--road four_engine` only: `roads_record` (PATH or None) and `scored_share` (True with `--roads-record`, else False). The learning-rate schedule needs no key: the frozen `train_cmd` adds `RECIPE29_TIMED` exactly when `roads_record` is set;
  - `reward_knock` ('in' or 'out'), only when given.
  - On any other road with neither option given, the plan is the pre-C1b one, key for key.
- `option_args(plan) -> list`: `--roads-record PATH` and `--reward-knock V`, each only when the plan holds it, in that order.
- `env_options(plan) -> dict`: what `train.build_env` takes beside the road's name for the runs the plan times. That is `ROAD_OPTIONS[road]` (or {}); with a roads record, `scored_share=True, roads_record=<HERE>/PATH`; then `reward_knock=(V == 'in')` when given. Section 2's parts are diagnostic: r_e comes from section 3's `train.py` runs.
- `code_info(root=HERE)`: `root` is the work tree git is asked about (the selftest names a scratch one). `git_dirty` is still `git status --porcelain` non-empty, an untracked file included.

**The timed command** (row 135 (2)):
- `RECIPE29_TIMED = ("--lr-schedule", "last-third", "--scored-share")`: `train_all.py --recipe29`'s recipe flags (`train_all.py:159-161`) without `--checkpoint-average`. The selftest compares the two.
- `train_cmd`, after the existing arguments, appends:
  - with a roads record: `RECIPE29_TIMED`, then `--roads-record PATH`;
  - then `--reward-knock V` when given.
- train.py refuses `--roads-record` without `--scored-share` (`train.py:550-553`), so the share flag is required. `--lr-schedule last-third` is legal at S steps: it is decision 29's schedule as far as a run of S steps carries it.
- `--checkpoint-average 50000` is never forwarded: train.py refuses a window longer than the run (`check_recipe`; the `window_longer_than_the_run` case of `test_four_engine_training.TrainRefusals`). The average's snapshot saves are not timed (ASSUMED small, row 135 (2)).
- Section 4's determinism runs build their commands through `train_cmd` (`benchmark_training.py:806-830`), so they carry the same flags.
- `run_part` passes `option_args(plan)` to the `--part` child, which builds `env_options(make_plan(a))`. `part_plant` and `part_sac` take it as their required keyword `options`.
- `launcher_command` appends, after `--out runs/<the experiment's own>`: `--third-arm --recipe29` with a roads record, then `option_args(plan)`. train_all.py refuses `--roads-record` without `--third-arm` or `--recipe29` (`train_all.py:197`).

**Key lists:**
- `PLAN_KEYS = ('road', 'engine', 'dt', 'steps_per_run', 'det_steps', 'roads_record', 'scored_share', 'reward_knock')`. It replaces `merge_docs`' literal (:1291) and is compared with `.get`, so an absent key reads None and step 3's extremes files still `--merge`.
- `PLANT_KEYS = ('plant_sha', 'derived_sha', 'engine', 'engine_sha', 'backend', 'reward_knock')`. Each is read from the run's config.json with `.get` (None before P), and `_plant_id` compares these keys only.
- `PRE_C1B_BLOB`: the git blob of this script before C1b (unchanged from C1 to `91c6ece`), which the extremes byte-identity reads.

**Unchanged:**
- `ROAD_OPTIONS` (:183), the default when no record is given;
- `ENGINES`, `ARMS`, `SEEDS_TARGET`, `PROD_STEPS` (:160);
- `configurations` (:923-948), `bounds`, `_days`, `schedule`, `pick_runs`;
- `recommend`, except its launcher caption and the road its validity line reads (below), which C1b words conditionally, as the module docstring now is: "train_all.py trains two arms a seed today" stays, word for word, without a roads record, and with one the caption says the command's `--third-arm` trains decision 27's three;
- `record_bytes_per_step` and its 274 B pin (:1514);
- the pre-C1b sentences on decision 28's table backend, printed word for word on every road but `four_engine`. On `--road four_engine`, `validity(engine_id, road)` and section 2's `backend_line(road, plant_s, part)` print row 136's words instead (no table is built for any engine; the cycle backend only), and the module docstring's table paragraphs stay, each with one added sentence (C1b at `d9a96fa`, the review of round 4, its first option). The extremes byte-identity and the selftest pin both, and step 3's file (`b2151af`, `--road extremes`) prints the old sentences.

**Self-tests** (`--selftest`; also a gate of C2, P, V and Ta, section 14, since only it checks the B1 command against the `train.py` those commits edit):
- `--road extremes`. This script's `main()` and `PRE_C1B_BLOB`'s (`pre_c1b_module`) run in-process on the same command lines, with the probe and the machine stood in (`main_as`). They give the same output, exit, saved plan and parts, and every command function gives the same on the saved plans. Without git or the blob the test fails; it never skips. So step 3's files stay valid and still `--merge`, whichever commit step 3 ran on.
- The four-engine `train.py` command, on a SYNTHETIC roads record outside the repository, through `train_check(cmd)`: `train.py`'s own `main()`, stopped once its `check_recipe` returns, with nothing built.
  - It passes, with road options exactly `{scored_share: True, roads_record}` and a recipe whose keys are exactly `{lr_schedule, scored_share}`: `lr_schedule` 'last-third', and `scored_share` with seed_kind 'SYNTHETIC'. There is no `reward_knock` in it.
  - Its recipe flags equal `train_all.commands`' `--recipe29` flags for the same run once `--checkpoint-average 50000` is taken out.
  - Controls (mistake 12): without `--scored-share`, and with `--checkpoint-average 50000` at S, it is refused.
  - Before P (no `reward_knock` in `train.build_env`'s signature), the command has no `--reward-knock` and `train.py` refuses the flag. From P on it carries `--reward-knock out`, and the command without it is refused. The test adapts by itself, so the frozen script's selftest stays valid after P.
- `main()` on `--road four_engine`: the record is checked first, then refused before P. From P on (the probe stood in), every command of the dry run carries the share and the knock option.
- The launcher's caption: three arms with a roads record, the pre-C1b words without.
- `code_info` on a scratch `git init` tree: two engines' attempts written outside it record `git_dirty` False. The control, written into its `results/benchmarks/`, records True.

**The comment at :450-451** reads: "the plants that may train (`engines.trainable()`: the B58 alone until the plant commit, then the engines the committed records keep, row 107 (5))".

### `engine_gate.py`, `test_reward.py`, `check_roads.py` (the training check)

`engine_gate.py` has no command line. Its training check is driven by `test_reward.py` (`:381-383`, `run_gate`) and `check_roads.py` (`:125`, `road_table`).
- `share_record(train_road, roads_record)` returns None when no record is given (the share off), or the record as `four_engine_roads.read_roads_record` reads it. It raises ValueError for a road other than four_engine, for a record train.py would refuse, and for a REAL record that `real_record_problem` refuses.
- `training_env(train_road, seed, *, plant, roads_record)`: `roads_record` is required.
  - None builds row 116's road with `FOUR_ENGINE_OPTIONS`: the general episodes.
  - A path builds it with `scored_share=True` and the path, as train.py does with `--scored-share --roads-record`, so each seed's first episode is the share's road (row 101's family).
  - A record for another road is refused.
- `run_gate(engine_id, *, train_road, roads_file, synthetic_seed, jobs, roads_record)` and `road_table(engine_id, *, train_road, roads_file, synthetic_seed, n, first_seed, jobs, roads_record)` take `roads_record` as required, None meaning the share is off. Each calls `share_record` first. The train tasks carry the record's path, and `job` passes `task['roads_record']` to `training_env`; a train task without the key fails (tested).
- **Recorded paths are repository-relative.** `record_name(share)` is the one name the gate returns and prints and `check_roads.py` records: None when the share is off; `epa_roads.ROADS_REL` for a REAL record (`share_record` refuses any other); a SYNTHETIC record inside the repository relative to it, with '/' separators; one outside it by its own path, and every table that names it is written outside the repository too. Only the tasks read the record by its absolute path. `run_gate` returns `roads_record` (`record_name`'s) and `share_kind` (the seed_kind, or None), and `road_table`'s training rows carry the same name. `run_gate`'s `synthetic` is True for a SYNTHETIC seed or a SYNTHETIC share record.
- `print_gate`, on row 116's road only, prints `decision 29's share : off (no --roads-record): the general episodes only` or `decision 29's share : on, <seed_kind> record <path> (row 130 (5)): each seed's first episode is the share's road`.
- `test_reward.py --roads-record PATH` and `check_roads.py --roads-record PATH`:
  - allowed only with `--engine` ("give --engine" otherwise);
  - `share_record`'s ValueError becomes the parser's error;
  - a SYNTHETIC share record makes `check_roads.py`'s run a test, whose `--out` must lie outside the repository;
  - `check_roads.py`'s JSON gains `roads_record` (`record_name`'s, or null) and `share_seed_kind`. Its default file is `default_table(engine_id, train_road, share_on)`: `check_roads_<train_road>.json`, and on four_engine `check_roads_four_engine_share_on.json` or `_share_off.json` (12.9), so a share-off run and a share-on run never overwrite each other.
- `FOUR_ENGINE_OPTIONS` (:111) is unchanged, so `test_device_gate`'s `B.ROAD_OPTIONS` pin holds.
- The knock option arrives in P (section 6.6).
- The B58 runs of both scripts without `--engine` print what they printed before.

### `DEVICE_RUNBOOK.md`, B0, B1 and B5

B1 writes every attempt to `$B1OUT`, outside the repository. Writing inside the clone would make every run after the first file record a dirty tree: `code_info` reads `git status --porcelain`, which lists untracked files, and `results/benchmarks/` is not ignored.

**Part B's header and B0** (C1b; at `91c6ece` they ask for "the pushed commit after P", `DEVICE_RUNBOOK.md:160-161`, `:166`):
- `B1OUT=~/grad_device/B1`, set in B0: B1's one folder, outside the repository, the same path in every session of B1 (a repeat of B1 included), never a new one. `$OUT` stays one per session for every other step. So k never restarts in a later session, and B5 copies every attempt of every session. Nothing but B1's attempts and B0's records is written there.
- B0 checks out the pushed commit holding V, Q, CU (if any) and Ta (ORDER step 18), and records its sha. The runbook cites CU as ORDER step 17a and Ta as ORDER step 17b, as section 0 numbers them (section 16, item 9).
- On CUDA (row 135), B0 first installs the environment of CU's CUDA lock (row 118); its python is `<row 135's interpreter>`, and B0's VERSIONS check runs with it.
- B0 writes `$B1OUT/B0_<git_head>.json`: `benchmark_training.code_info()` (git_head, git_dirty, benchmark_sha, train_sha) and `host` (`platform.node()`, as the benchmark's `machine` records it), with row 135's interpreter. It is written once for each commit that B1 runs from, never overwritten (it refuses an existing file), and committed by B5. Ta's `classify` reads it (10.1).

**B1:**

```
PYB=<row 135's interpreter>    # row 135's device's: $PY for cpu; for cuda, the CUDA lock's (row 118)
for E in $($PYB -B -c "import engines; print(' '.join(engines.trainable()))"); do
  k=1
  while [ -e "$B1OUT/B1_bench_$E.attempt$k.json" ] || [ -e "$B1OUT/B1_bench_$E.attempt$k.txt" ] \
     || [ -e "results/benchmarks/B1_bench_$E.attempt$k.json" ] \
     || [ -e "results/benchmarks/B1_bench_$E.attempt$k.txt" ]; do k=$((k+1)); done
  $PYB -B benchmark_training.py --engine $E --road four_engine --roads-record results/EPA_ROADS/roads.json \
      --reward-knock out --device <row 135> --runs <N> --steps <S> --repeats <R> \
      --out "$B1OUT/B1_bench_$E.attempt$k.json" 2>&1 | tee "$B1OUT/B1_bench_$E.attempt$k.txt"
done
```

The text also changes:
- `<row 135's interpreter>` is the interpreter of row 135's device: `$PY`, the lock's, on the CPU; on CUDA, the python of the environment installed from CU's CUDA lock. `$PY` holds the lock's CPU build of torch: given `--device cuda`, the benchmark finds no usable device and exits before it writes its JSON, so every CUDA attempt would be a crash, and its repeat the same.
- k counts a `.json` or a `.txt` in `$B1OUT` and in the committed `results/benchmarks/`, so a crash that left only its `.txt` is never overwritten, and an attempt of an earlier session is counted.
- A crash or an operator fault (row 135 (4)) is repeated for that engine alone, by the same block with `for E in <the engine>; do`, into the same `$B1OUT` whichever session repeats it, so no other engine gains an attempt. An engine whose last attempt is a measurement is never run again.
- On CUDA, the CPU series always runs at the same visit, for every engine: the same block with `PYB=$PY`, `--device cpu`, `--runs <row 135's CPU N>` and the names `B1_bench_$E.cpu.attempt$k`. It is read only after a fallback (row 135 (4)(c)).
- r_e = lower_min / N exactly (row 135 (3)).
- The share-off bullet and the "Before P" bullet of B1 are removed; the new text carries row 135 (4)'s crash rule in their place.
- **B5:** once every engine of B1 is done, every `$B1OUT/B1_bench_*.attempt*` file (the `.cpu.attempt*` ones among them), the JSONs and their `.txt`, and every `$B1OUT/B0_*.json` are copied into `results/benchmarks/` (`cp -n`) and committed in B1. None is renamed or deleted. B5's sentence on what T checks reads: "Commit T's classify reads every committed attempt. The last attempt of each series has code.git_dirty False, and a dirty one is an operator fault, kept and repeated (row 135 (4)(b))."
- `test_device_gate.RunbookB1` (C1b) runs the runbook's own B0, B1 and B5 text with bash on a scratch git work tree outside the repository. A stand-in takes `<row 135's interpreter>`, and `$PY` is a stand-in that refuses. B0's record lands in `$B1OUT`, and a second B0 on the same commit refuses to overwrite it. Two engines in a row land clean in `$B1OUT`, with k counted over `$B1OUT` and `results/benchmarks/`, a `.txt` alone included; the CPU series on CUDA lands as `.cpu.attempt<k>` with its own k; a later session's CUDA repeat continues k there, and B5 copies both sessions, the CPU series and the B0 records. The controls (mistake 12): attempts written inside the tree record it dirty, and the loop with `$PY` runs nothing. It is skipped without bash.

### CUDA

If row 135 names CUDA, the CUDA lock and `check_training_device.py`'s CUDA path are CU: their own commit, after P and before Ta (ORDER step 17a; row 118). B0 installs the lock's environment, and B1 names its interpreter.

## 4. C2: the CVT record (ORDER step 12a; row 137)

### `step_record.py`

| name | definition |
|---|---|
| `CVT` | `('cvt_ratio', 'cvt_branch', 'n_eco', 't_eco')`. Recorded for an `engines.CvtCar` only: after FIELDS in an evaluate record, after REC_INFO in a train record. Never part of FIELDS, INFO or ENV. |
| `CVT_BRANCHES` | `('low-speed', 'economy', 'kickdown', 'power-limited')`. Code = index + 1 (1-4); 0 = no branch (padding). Equal to `engine_env.CvtVehicle.ratio_for`'s literals (`engine_env.py:821, :834, :849, :852`), pinned both as the literal tuple and as a set. Reordering it re-codes every Honda train record. |
| `GEAR_CVT` | `-1`. A CVT record's gear on every step, moving or at rest. |
| `INT8` | `('gear', 'cvt_branch')`. Replaces the `k == 'gear'` tests at :147 and :170-171. |
| `cvt_fields(car)` | `CVT` if `type(car) is engines.CvtCar` (exact type, as `vehicle_for`), else `()`. `car` is required. |
| `cvt_state(veh)` | A dict in CVT order: `cvt_ratio = float(veh.ratio)` (without the final drive); `cvt_branch = CVT_BRANCHES.index(veh.branch) + 1`; `n_eco` and `t_eco` as floats, NaN on low-speed. Raises ValueError naming `veh.car.id` when: ratio is None; the branch is unknown; n_eco or t_eco is None off low-speed, or not None on it; an attribute is missing. |
| `env_state(env)` | A stepped car (Car, EpaCar): the same 21 keys, order and values as at `7a40b9f`. A CvtCar: the same keys with gear = GEAR_CVT, then `cvt_state(env.veh)`. Reads only. |
| `step(rec, env, action, obs_before, reward, info)` | Computes `s = env_state(env)` and `first = not rec['reward']` before any append. A missing CVT key is created only when `first`. A CVT key missing later raises ValueError and leaves `rec` unchanged. Any other unknown key raises KeyError. Append order is unchanged (:133-142). |
| `finish` / `stack` / `save` | `finish`: int8 for INT8, float64 for floats. `stack`: pads INT8 with 0 and the rest with NaN; ValueError naming the keys when episodes' key sets differ. `save`: `.json = dict(meta, fields=list(FIELDS) + the CVT keys present, steps=..., cvt_branches=list(CVT_BRANCHES) only when cvt_branch is present)`. A record without CVT fields is byte-identical to today's. |
| `gear(env)` | Still raises on a CvtCar, with the text "a CVT has no gear to count; its record holds gear GEAR_CVT and the fields step_record.CVT (env_state; rows 118 and 137, ORDER step 12a)". The stepped count (:93-97) is byte for byte. |
| unchanged | FIELDS (44), AGENT, INFO (18), ENV (22), F16, `new()`, `cast()` (:150-156), `git_head()`. |

### `train.py`

| name | definition |
|---|---|
| `REC_INFO`, `REC_VEC`, `CHUNK` | Unchanged (`step_record.INFO + step_record.ENV`, 40 names; `('applied', 'weights')`; 10 000). |
| `rec_fields(car)` | `REC_INFO + step_record.cvt_fields(car)`. `car` is required. |
| `ActionRecorder(outdir, *, info_fields)` | Buffers `('step', 'episode', 'action', 'obs', 'reward') + info_fields + REC_VEC`. The REC_INFO part is read with `info.get(k, np.nan)`; the CVT tail is read strictly with `info[k]`. `_flush` calls `_record_arrays(b, self.info_fields)`. At :945: `ActionRecorder(outdir, info_fields=rec_fields(plant.car))`. |
| `_record_arrays(b, info_fields=REC_INFO)` | Iterates `('action', 'obs', 'reward') + info_fields + REC_VEC` through `step_record.cast`. The one-argument call in `benchmark_training.record_bytes_per_step` (`:575` at `91c6ece`) still gives 274, which the benchmark's selftest pins. |

### Docstrings

- `four_engine_roads.py:124-127` reads "only when engines.trainable() names them (decision 47; from the plant commit it reads the committed records, row 107 (5))".
- `engine_gate.py`'s WHAT WAITS Accord bullet (`:60-63` at `91c6ece`; C1b moves it by its added lines) is edited on C1b's text, cited by name. It no longer says the Honda's checks wait for 12a; it names the scratch measurement of row 135 (8), every check line of it.
- `engine_env.py:776-780` is not C2's; P edits it (section 6.1).

### Tests

- **`test_step_record.py`.** The "before" module is the blob of `step_record.py` at roads.json's `commit_reveal.roads_commit`. Its `thresholds.common.sha_text` must equal roads.json's `hashes.files['step_record.py']`. If git, roads.json or the blob is missing, the test fails; it never skips. Classes:
  - B58Unchanged, SteppedEpaCars, Honda, Controls, Source;
  - **HondaTrainRecord** (row 137 (3)): ten steps of the Honda's environment through `train.ActionRecorder(outdir, info_fields=train.rec_fields(car))`, flushed into a temporary folder outside the repository. `train_record.npz` holds 51 fields with the dtypes of 12.3: gear int64 −1 on every step, cvt_branch int64, cvt_ratio, n_eco and t_eco float32. The control, the B58, gives 47.
- **`test_cars.StepRecord`.** Renamed `test_a_cvt_has_no_gear_and_the_supra_has_its_gear` (:871-892), with docstring lines 72-73. This is C2's flip; P must not re-flip it.
- **The Honda's gate, repeated** (row 137 (6)): `test_reward.py --engine honda_l15b7 --train-road four_engine --synthetic-seed 101`, output outside the repository. Every check line it prints (`engine_gate.print_gate`'s table: name, PASS, FAIL or NOT RUN, and detail) is compared with the lines row 135 (8) quotes: the gearbox table, the band, each notch, the two SYNTHETIC decision-34-road checks, the two training-road checks (worst neutral |r| and worst p95 tracking error; starver against neutral) and the blind-arm line at H = 30 s, which runs on the SYNTHETIC roads and gives PASS or FAIL before P (with no H_table, `engine_gate.horizons` asks only 30 s, which `preview_env` builds before P; only another H would read NOT RUN until P). A line whose result or detail differs is a defect of C2, fixed before C2 is committed. This is the SYNTHETIC part of the Honda's row-119 gate, run before P, so on X1's reward with the knock term; the rest, and the whole gate with `--reward-knock out` on the real roads record, runs at Q (section 9).

## 5. RV: the roads re-verification (row 140)

### Command line

- `roads_reverify.py check --jobs J --out DIR [--skip-companions] [--keep-going]`
  - Runs on any tree, P's uncommitted one included.
  - DIR lies outside every git work tree, and only `DIR/reverify_CHECK.json` is written.
  - Fail-fast by section, unless `--keep-going`.
  - `--skip-companions` gives `partial: true`, which can never be adopted.
- `roads_reverify.py adopt FILE`
  - Takes a complete EQUAL check result whose head is HEAD and pushed.
  - Re-hashes every hashed file, `roads_reverify.py` and its closure, the data inputs and the contract against that result.
  - Refuses a partial, DIFFERENT, REFUSED or stale result, and an existing `reverify.json`.
  - Writes `results/EPA_ROADS/reverify.json` once, through `epa_roads.write_once`.
- `roads_reverify.py record --jobs J [--supersede ROW]`
  - Needs a clean HEAD that is in origin's `GRA-test`.
  - Writes `OUT_REL`, or with `--supersede` the next free `reverify_<n>.json`, from a complete EQUAL result only. The next n comes from `four_engine_roads.current_reverify`'s listing.
- Exit codes: 0 EQUAL, 1 DIFFERENT, 2 REFUSED.

### Constants

- `MODULE_REL = 'roads_reverify.py'`
- `OUT_REL = 'results/EPA_ROADS/reverify.json'`
- `SCHEMA = 'epa-roads-reverify/1'`
- `IGNORED_PATHS = (('report', 'provenance'), ('report', 'wall_s'))`. Neither is step 12a's: row 140 (1) replaces row 127 (1)'s "ignoring only fields that step 12a adds".
- `ADDED_BY_STEP_12A = ()`
- `MAY_DIFFER = ('engine_env.py', 'engines.py', 'evaluate.py', 'fingerprint.py', 'step_record.py')`
- `NOT_RECOMPUTED` holds:
  - the practice set (row 96), τ (row 102) and the roads themselves (the input);
  - the draw's provenance keys: hashes, attempts, steps_log, printed, printed_earlier, files_opened, data_inputs, frozen_check, commit_reveal, started, finished, changed_during_run.

### Functions

- `class NotRecorded(Exception)`
- `class ScriptedRng(values, *, label)`, with `.integers(lo, hi)`, `.uniform(lo, hi)` and `.left()`
- `reconstruct_generated(record, *, root) -> (roads, problems)`
- `scripted_streams(record, redraws=None)`: a context manager that patches `R.replacement_rng` and `R.redraw_rng` (`epa_roads.py:392-397`) and asserts every seed is None
- `preconditions(record, *, root, mode, out_dir) -> (problems, context)`
- `recompute(record, *, root, jobs, log, sections, keep_going)`
- `compare(old, new, *, path=(), ignore=IGNORED_PATHS, added_ok=ADDED_BY_STEP_12A) -> {'values', 'differences', 'first'}`
- `reverify(*, root, jobs, mode, out_dir, log, record=None, redraws=None, sections=None, keep_going=False)`; only tests pass `sections`.
- `reference_commit(rel, *, root) -> str`. This is the one definition of Live's reference.
  - It returns the commit that added `rel`: `git log --diff-filter=A --format=%H -- <rel>`, which must print exactly one line.
  - From P on, `test_roads_reverify.Live` compares every file the current record names (each `tree_changes[*].sha_text` and every `hashed_files.sha_text_now`) with its blob at `reference_commit(<the current record>)`. It never compares them with HEAD or the work tree.
  - So G's edit of `epa_fit.py` and V's edit of `evaluate.py` do not fail it.

### The one reader of the current record (RV's edit of `four_engine_roads.py`)

- `four_engine_roads.current_reverify(*, root) -> (rel, record) | None`, appended to `four_engine_roads.py`, which imports only what it already imports.
  - It lists `results/EPA_ROADS/reverify.json` and every `reverify_<n>.json` (n >= 2) that is tracked and unmodified at HEAD.
  - It reads each as plain JSON.
  - It returns the highest n whose `roads_sha` equals `epa_roads.roads_sha(roads.json)` and whose `redraws_sha` equals `thresholds.common.sha_text(redraws.json)`, or None.
- Its callers are `roads_reverify` (the next free n), `test_roads_reverify.Live` and V's `evaluate.decision34_roads`. No other module reads a re-verification record.
- `evaluate.py` cannot import `roads_reverify` (rule below), so the reader lives in `four_engine_roads.py`. That module joins the live closure through `evaluate.py` only at V (`AFTER_V`).

### `compare` semantics

- The new side is passed through `json.loads(json.dumps(x, allow_nan=False))` first.
- `type(a) is type(b)`, so 1 and 1.0 differ, and True and 1 differ.
- Floats are compared as `struct.pack('<d', x)`, so -0.0 and 0.0 differ.
- Dicts are compared both ways. Lists by length, then item by item.
- At most 50 differences are reported, each as `{path, at_draw, now}`.

### Sections

They run in row 98's order, each logged before the next one starts: reconstruction, identities.locked_climb_b58, identities.generated, slots, c5, ceilings, passes_T, report, identities.final, cvt_diagnostic, coverage, episode_steps, H_table, design, streams, then `redraws.<reading name>`.

### Preconditions (exit 2)

- `epa_freeze.versions()` equals roads.json's `hashes.versions`.
- Threads at 1, `-B`, and no `__pycache__` beside a hashed file.
- Every `engines.engine_sha(R.plant_of(e))` equals roads.json's.
- Only MAY_DIFFER files of the 35 differ.
- The import-closure set, the contract's two files, every data input and `evaluate.EPISODES` are unchanged.
- Each τ is read through `roads_ceiling.use_recorded_taus`.
- When `engine_env` defines them (from P on): `REWARD_KNOCK_DEFAULT is True` and `preview_samples(PREVIEW_H_S) == PREVIEW_S`. The re-verifier passes neither option.

### Never, and isolation

- It never calls `FP.plant_fingerprint`, `verify_record` or `frozen_problems`. plant_sha comes only through `epa_freeze.plant_sha`.
- No module of the 35, CODE_HASHED or PLANT_CODE imports it.
- Its name and its test's name end with no plant file's name.
- Consumers read the record through `four_engine_roads.current_reverify`, as plain JSON.

### Consumed

- `epa_roads`: `layout`, `make_road`, `frozen_episodes`, `slots_of`, `with_grade`, `with_flat`, `arrays_sha256`, `c5_on_car`, `climb_tests`, `replacement_loop`, `recheck_slots`, `redraw_slot`, `cvt_diagnostics`, `coverage_flags`, `h_table`, `design`, `streams`, `pool_map`, `plant_of`, `hashed_files`, `sha_texts`, `import_closure`, `files_opened`, `data_inputs`, `write_once`, `roads_sha`, `tree_state`, `remote_state`, `install_guard`, `jsonable`, and the constants `ENGINES`, `DT`, `C5_MARGIN`, `B58_PLANT_SHA`, `REDRAWS_REL`, `ROADS_REL`. All frozen.
- `roads_ceiling`: `use_recorded_taus`, `ceilings`, `passes_T`, `report`, `slot_candidate_ceilings`, `RATIOS`, `ALL_VARIANTS`, `READINGS`, and the caches tests clear.
- Test fixtures: `test_epa_fixtures.Guarded` and `forbid_real_data`; `test_epa_roads.hashed_copy` and `flip_one_byte`.

The layout of `reverify.json` is in 12.4.

## 6. P: the plant commit (P1 + P2 + P3, one scratch branch, one commit)

### 6.1 `engine_env.py`

**Preview horizon (P1):**
- `PREVIEW_S = (2.0, 5.0, 15.0, 30.0)` stays the literal on :993, and `OBS_DIM = 23` stays on :994. Both are read by `thresholds/document.py:190`, `make_page.py`, the lab's `catalog.py` and the app.
- `PREVIEW_H_S = 30.0`.
- `PREVIEW_DIVISORS = (15.0, 6.0, 2.0, 1.0)`.
- `preview_samples(h_s) -> tuple` returns `tuple(float(h_s) / d for d in PREVIEW_DIVISORS)`.
  - TypeError for a bool or a non-real; ValueError for a non-finite value or one <= 0.
  - An import-time check raises unless `preview_samples(PREVIEW_H_S) == PREVIEW_S`.

**Knock option (P3):**
- `REWARD_KNOCK_DEFAULT = True`: X1's reward, with the knock term in r_life.

**`SupervisoryTunerEnv.__init__(self, cycle, *, plant, engine_model=None, dt=0.2, use_preview=True, uncertainty_beta=1.0, seed=None, inlet_kpa=None, preview_h_s=PREVIEW_H_S, reward_knock=REWARD_KNOCK_DEFAULT)`:**
- Sets `self.preview_h_s = float(preview_h_s)` and `self.preview_s = preview_samples(preview_h_s)`.
- Sets `self.reward_knock`, refusing `type(reward_knock) is not bool` with a TypeError naming row 113 (5).
- TerrainTrainingEnv, ExtremesTrainingEnv, EngineEnv and WideAirTrainingEnv forward both through `**kw` and are not edited.

**`_preview`:** iterates `self.preview_s` with index `min(k + int(h / dt), n - 1)`. Every sample is 0.0 when `use_preview` is off, at every H (row 117's construction; the bit-for-bit test of row 135 (5) checks it).

**r_life (P3):**
- `reward_knock` True: `(d_b - d_a) / (d_b + 0.05)`, byte for byte today's :1331.
- `reward_knock` False: `(l_b - l_a) / (l_b + 0.05)`, where `l_a = damage_rate(self.thermal.t_turb, self.thermal.t_oil, cal=eng.damage)` and `l_b` is the same on `thermal_base`.
- Unchanged in both: d_a, d_b, `e['damage']`, `e['damage_base']`, c_knock, the info keys and the reward sum.

**Cam-aware surrogate (P3):**
- A surrogate whose class attribute `takes_cam is True` gets `predict(rpm, map_kpa, iat_k, ect_k, spark, lam, *, cam_deg)`, returning `dict(torque, mdot_fuel, mdot_air, egt_k, ki, unc)`. `cam_deg` is None on an engine without form D.
- Any other surrogate given a cam is refused at the first `_evaluate`, as today, with a ValueError containing 'surrogate'.
- `_evaluate`'s signature and its call sites are unchanged, and nothing new is imported.
- P carries this path because row 94 fixes it "off at its defaults, whether or not a table is later built". Under row 136 no table is built: there is no table module, no remedy hook and no table backend string, and `fingerprint.backend_of` refuses every engine_model (6.2), so no agent trains on this path.

**Kept for `tit_cap_ecu.py` (row 127 (2)):**
- `BaselineECU.step(self, rpm, map_kpa, iat_k, ect_k, knock_observed, dt) -> (spark, lam, fan)`, defined unwrapped in the class body;
- `BaselineECU.cam_deg(self, rpm, map_kpa)`;
- `self.ecu = BaselineECU(plant.engine.ecu)`;
- the baseline's `ecu.step` and `cam_deg` calls on `map_b_prev`, then `_track_torque`, then `self.map_b_prev = map_b` (:1283-1294).

**Kept for `test_fuel_forms` (SOURCE_PINS, `_step_calls`):**
- both `_track_torque` calls take 8 positional arguments plus `cam_deg`;
- `_evaluate` takes 6 plus `cam_deg`;
- each pinned string appears once, and no docstring quotes one.

**The CvtVehicle docstring** at :777-778 reads "a CVT is recorded with gear step_record.GEAR_CVT and the fields step_record.CVT (C2, ORDER step 12a, rows 118 and 137)". The rest of the sentence stays. It is a docstring, so plant_sha does not see it.

### 6.2 `fingerprint.py` (P1)

**Schema and FATAL:**
- `SCHEMA_VERSION = 4`.
- `FATAL = ("plant_sha", "derived_sha", "engine", "engine_sha", "train_backend", "score_backend", "backend_contract", "transmission", "dtheta_deg", "turb_protect_k", "oil_protect_k", "scenario", "episodes_sha", "preview_h_s", "reward_knock")`. `backend`, `gears` and `final_drive` leave both FATAL and the block. `format_block` prints FATAL first, in this order, and prints a dict as `k=v`.
- `BACKEND_CYCLE = "cycle"` is unchanged. There is no table prefix: row 136 builds no table, so no backend string but 'cycle' exists.

**`plant_fingerprint(protocol="phase-d", *, plant, train_backend, score_backend, preview_h_s, reward_knock, **advisory)`** has no defaults on the four new keywords. It refuses:
- `plant` None (TypeError);
- `train_backend != 'cycle'` (ValueError; row 136: every engine trains on the exact cycle). Both backend fields stay in FATAL, as row 117 lists them;
- `score_backend != 'cycle'` (ValueError, permanently; MD:1462);
- a `preview_h_s` that is neither None nor accepted by `E.preview_samples`;
- a `reward_knock` that is not a bool (TypeError);
- an advisory `use_preview` that contradicts `preview_h_s`;
- a candidate plant (unchanged, :421-428);
- a protocol outside {phase-d, d2, d34};
- under d34, an advisory `eval_dt`, `eval_duration`, `scenario`, `episodes_sha` or `n_episodes` that differs from the value it computes;
- any advisory `transmission` or `backend_contract`.

The CvtCar refusal (:413-420) is deleted. `backend_contract()` is called through the module global, so a Guarded test can patch it. The block is defined in 12.1.

**Helpers:**
- `transmission_of(car)` dispatches on `type(car)`:
  - Car or EpaCar: `{"kind": "stepped", "gears": [float, ...], "final_drive": float}`;
  - CvtCar: `{"kind": "cvt", "ratio_low_gear", "ratio_top_gear", "final_drive", "kickdown_load", "target_load", "cvt_rpm_min"}`, each a float (`engines.py:807-832`);
  - anything else: TypeError.
- `backend_contract()` returns `{"md_sha_text": common.sha_text(common.CONTRACT_MD), "json_sha_text": common.sha_text(common.CONTRACT_JSON)}`. `from thresholds import common` sits inside the function; it uses sha_text only and never `json.load`.
- `backend_of(env)` (:144-156; it reads `env.engine`, the engine_model the environment was given):
  - TypeError without `engine` (a wrapper), as today;
  - returns `BACKEND_CYCLE` when `env.engine` is None;
  - refuses every engine_model, as today (row 136 admits no table). `train.py:815` already reads it (`backend_of(env.unwrapped)`); P only renames the keyword to `train_backend`.
- `preview_of(env)`: TypeError without `use_preview` and `preview_h_s` (it must be `env.unwrapped`); None when `use_preview` is off; otherwise `float(env.preview_h_s)`.
- `reward_knock_of(env)` returns `env.reward_knock`; TypeError if it is missing or not a bool.
- `for_arm(fp, *, sighted)` returns a copy. When not sighted, `preview_h_s` and `preview_samples_s` are None. It never writes a meta.json.
- `pair_problems(sighted, blind) -> list[tuple]` returns `(field, a, b)` for every FATAL field except `preview_h_s` that differs. It also returns a problem when the sighted `preview_h_s` is not a positive finite float, when the blind one is not None, or when `schema_problem` objects to either block.

**Decision 34's set:**
- `d34_roads(*, root) -> (scenario, roads)` is the one reader of the scored set. It reads `ER.ROADS_REL` plus `ER.REDRAWS_REL`'s `readings['version 6']['roads']`, and requires:
  - redraws.json's `roads_sha` equals roads.json's;
  - the 20 roads have k = 0..19 in order;
  - each road's `(episode_seed, float weights)` equals `ER.frozen_episodes(root=root)[k]`.

  It refuses a REAL record without redraws.json; a SYNTHETIC record without one uses roads.json's roads. Its imports are lazy and only `epa_roads` and `thresholds.common`. The scenario is defined in 12.10.
- `d34_set(*, root) -> (scenario, entries)`, with `entries = tuple((k, episode_seed, tuple(weights), ER.arrays_sha256([road])) for each road of d34_roads)`.
- `episodes_sha('d34') = sha256(repr(d34_set(root=HERE)[1]))[:16]`. The phase-d and d2 values are unchanged.

**Dirty files:**
- status comes from `_git('status', '--porcelain=v1', '-z', '--no-renames', '--untracked-files=all')`, and the prefix from `_git('rev-parse', '--show-prefix')`.
- `_porcelain_paths(z) = {e[3:] for e in z.split('\0') if e}`.
- `_dirty_plant(files, paths, prefix) = sorted(n for n in files if prefix + n in paths)`.
- `git_dirty` and `git_dirty_plant_files` are None when either git call returns None.

**`schema_problem(stored)`:** None only for schema 4. Schema 3 gets its own message: written before the plant commit, it has no transmission, train/score backend, decision-34 protocol, preview_h_s or reward knock option, and none is assumed. Schemas 1 and 2 keep theirs. `--force-plant-mismatch` behaves as before.

**CLI** (`:740`): `--engine` (required; `engines.known()`), `--protocol {phase-d,d2,d34}`, `--preview-h-s FLOAT` (default `PREVIEW_H_S`), `--blind`, `--reward-knock {in,out}` (default 'in'). It passes both backends as 'cycle' and exits 0 for every calibrated plant; the Honda's transmission line prints `kind=cvt`. The module docstring's example (:4) uses the new signature.

### 6.3 `engines.py`: the reader (P2; row 139)

**Constants:**
- `RECORDS_ROOT = HERE` (:117); only tests patch it.
- `VALIDATION_SUMMARY_REL = 'results/EPA_VALIDATION/summary.json'`, pinned equal to `validate_epa.VAL_REL + '/' + validate_epa.SUMMARY` and to `epa_roads.SUMMARY_REL` (`epa_roads.py:145`).
- `VALIDATION_SUMMARY_SCHEMA = 'epa-summary/1'`, pinned to `validate_epa.SUMMARY_SCHEMA`.
- `VALIDATION_DIR_REL = 'results/EPA_VALIDATION'`; `RERUN_STARTED = 'STARTED_rerun{k}'`; `RERUN_ROWS = 'rows_rerun{k}.json'`. A test in `test_trainable` pins both, for k = 1, 2 and 3, equal to `validate_epa.rerun_name(validate_epa.STARTED, k)` and `rerun_name(validate_epa.ROWS, k)` (`validate_epa.py:385-388`).
- `BACKEND_REL = 'results/EPA_BACKEND.json'`; `BACKEND_SCHEMA = 'epa-backend/1'`; `NEVER_DROPPED = 'b58'` (MD:1590).

**Functions:**
- `trainable() -> tuple[str, ...]` returns `trainable_in(RECORDS_ROOT)`. It is called with no argument by the five parsers (`train.py:646`, `train_all.py:241`, `run_phase_d.py:248`, `evaluate.py:424`, `benchmark_training.py:1764`). It never writes, never caches, and reads nothing at import.
- `trainable_in(root)`:
  - First `open_reruns(root, epa=common.EPA_ENGINES)`. If that list is not empty, ValueError naming each engine and its `STARTED_rerun<k>`, row 94 ("No training starts while such a re-run is open") and row 139 (1).
  - Then `summary = committed_record(root, VALIDATION_SUMMARY_REL)`. When it is not None, `unlisted_reruns(root, summary, epa=common.EPA_ENGINES)`; if that list is not empty, ValueError naming each engine and its `rows_rerun<k>.json`, row 139 (1) and the command that lists it: "run `validate_epa.py summary` and commit summary.json". A re-run whose rows exist is no longer open, and only that command writes its entry (`validate_epa.summary`, `validate_epa.py:2544-2561`, whose one caller in the code is the `summary` subcommand, `:2636-2641`), so without this refusal a stale summary.json would make the first entry govern.
  - Then it returns `trainable_from(summary, committed_record(root, BACKEND_REL))`.
- `open_reruns(root, *, epa) -> list[(engine, k)]`:
  - For each engine, it checks k = 1, 2, ... until neither `<VALIDATION_DIR_REL>/<id>/STARTED_rerun<k>` nor `rows_rerun<k>.json` exists, at HEAD or in the work tree.
  - It lists (engine, k) when STARTED_rerun<k> exists and rows_rerun<k>.json does not.
  - It uses `epa_freeze.committed_at_head` and `os.path.exists` only, and opens no file.
- `unlisted_reruns(root, summary, *, epa) -> list[(engine, k)]`:
  - For each engine, the same walk over k as `open_reruns`.
  - It lists (engine, k) when `rows_rerun<k>.json` exists, at HEAD or in the work tree, and `summary['engines'][<id>]['reruns']` has no key `rows_rerun<k>.json` (`RERUN_ROWS`).
  - It opens no file but the summary it is given.
- `trainable_from(summary, backend)` is public and pure:
  - (None, None) gives `('b58',)`;
  - a backend without a summary raises ValueError;
  - otherwise it computes `kept = summary_survivors(summary, epa=common.EPA_ENGINES)`, then, if a backend record exists, `kept = backend_survivors(backend, kept, epa=common.EPA_ENGINES)`;
  - a kept name not in PLANTS raises ValueError;
  - it returns `tuple(n for n in known() if n == 'b58' or n in kept)`.
- `committed_record(root, rel)` is public:
  - None when `rel` is absent both from HEAD and from the work tree;
  - `json.load` of the file when `epa_freeze.committed_at_head(rel, root=root)`;
  - otherwise ValueError: "engines.trainable: <rel> is not committed at HEAD in <root> ...; commit it or restore it (rows 107 (5), 139)";
  - `epa_freeze.GitError` and TypeError are re-raised as ValueError naming the root as "not a git work tree".
  - It uses only `cat-file --batch-check` and `hash-object`, never `git status`.
- `summary_survivors(summary, *, epa)` requires the following, with a ValueError naming the field on each failure:
  - the schema;
  - `set(summary['engines']) == set(epa)`;
  - each entry's `drop` a bool (isinstance);
  - each `reruns` a dict whose keys match `RERUN_ROWS` for k >= 1, each value carrying a bool `drop`.

  **The governing entry (row 139 (1)):** the `reruns` entry of the highest k when there is one, otherwise the engine's own entry. Its `drop` is read as `validate_epa` recorded it. The re-run's labels are capped at limited by the route itself (MD:1602-1604; `test_defect_route.py:31`), and the reader never recomputes them, never reads the first entry when a re-run entry exists, and never takes a union. It returns the frozenset of the engines whose governing entry does not drop.
- `backend_survivors(record, kept, *, epa)` requires:
  - the schema;
  - `record['engines']` keyed by exactly `{'b58'} | set(epa)`;
  - each value a dict with a bool `drop`;
  - the B58's drop is False;
  - every engine in `set(epa) - kept` reads drop True.

  It reads no other key and returns the frozenset of `kept` not dropped.

**Imports:** only `thresholds.common` and `epa_freeze`, both inside functions, both already among the 35. It never imports `validate_epa` or `epa_roads`.

### 6.4 `train.py`, `train_all.py`, `test_reward.py`, `check_roads.py`

**`train.py`:**
- `build_env(use_preview, seed, duration, road="terrain", dt=1.0, *, plant, preview_h_s=PREVIEW_H_S, reward_knock=REWARD_KNOCK_DEFAULT, **road_options)` passes both to every constructor branch. four_engine's road options stay exactly {scored_share, roads_record}.
- `--reward-knock {in,out}` (default None):
  - required with `--road four_engine`, as `check_recipe`'s last check, after checkpoint_average's: "REFUSING: --road four_engine needs --reward-knock in or out, passed explicitly (row 127 (4))";
  - accepted and recorded on every other road;
  - without it, X1's commands, stdout and meta.json are unchanged apart from schema 4's fields.
- `check_recipe` keeps its return, `(road_options, recipe, h_s)`. On four_engine, `road_options` stays exactly `{scored_share, roads_record}`, and the knock option never enters the recipe: it is recorded top-level in config.json (12.2). C1b's selftest (`train_check`) and the frozen B1 command rely on both, and P's gates run that selftest (section 14).
- Protocol map: road random gives 'd2'; four_engine gives 'd34'; anything else gives 'phase-d'.
- meta.json is written (:815) from `FP.plant_fingerprint(protocol, plant=..., train_backend=FP.backend_of(env.unwrapped), score_backend=FP.BACKEND_CYCLE, preview_h_s=FP.preview_of(env.unwrapped), reward_knock=FP.reward_knock_of(env.unwrapped), ...)`, keeping today's advisory keys (:816-821). At the defaults `backend_of` returns 'cycle', as it does today at :816.
- `run_config`: see 12.2.
- stdout prints `reward        : with the knock term (X1's)` or `without the knock term (row 113 (5))`, only when the flag is given.
- The comment at :644-645 reads "the engines the committed records keep (decision 47, row 107 (5))".

**`train_all.py`:** `--reward-knock {in,out}` is forwarded to every arm, last (after `--keep-buffer`), only when given. `check_four_engine` requires it, after every existing refusal.

**`test_reward.py` and `check_roads.py`:**
- `--reward-knock {in,out}` is required with `--engine` and refused without it ("give --engine"). Both print the option in their header.
- The refusal of a missing `--reward-knock` with `--engine` comes after every existing refusal of `main_engine`, C1b's `share_record` check among them, as train.py's is `check_recipe`'s last. So `test_device_gate.Cli`'s refusal texts hold. P adds a Cli test of the knock refusal for each script; its control, `--reward-knock` without `--engine`, reads "give --engine".
- C1b's `--roads-record` (section 3) is unchanged.
- `check_roads.py --engine`'s default output is defined in 12.9.
- Their B58 runs without `--engine` are unchanged.

### 6.5 `evaluate.py` at P (one merged edit)

- `live = FP.plant_fingerprint(plant=plant, protocol=a.protocol, train_backend=FP.BACKEND_CYCLE, score_backend=FP.BACKEND_CYCLE, preview_h_s=PREVIEW_H_S, reward_knock=(knock == 'in'), eval_dt=DT, eval_duration=DURATION)` (:471), with `PREVIEW_H_S` and `REWARD_KNOCK_DEFAULT` imported from `engine_env` beside `SupervisoryTunerEnv`.
- `--reward-knock {in,out}` defaults to None and is read as 'in' on phase-d and d2. The resolved bool goes into `live` and into every `run_episode` call. V makes the flag required for d34 and `--practice`.
- For each model, `blind = "blind" in path` is computed first, then `check_model_fingerprint(path, FP.for_arm(live, sighted=not blind), force)`.
- `run_episode(policy, seed, weights, use_preview=True, road=None, record=None, *, plant, reward_knock=REWARD_KNOCK_DEFAULT)` passes it to `SupervisoryTunerEnv`. Only `ret` depends on it.
- The comment at :422-423 reads "the engines the committed records keep (decision 47, row 107 (5))".
- Untouched: EPISODES (:142), EPISODES_D2, PROTOCOLS, the `--protocol` choices, DT, DURATION, `check_model_fingerprint`'s body, every report line after the fingerprint block, and `run_episode`'s default path.

### 6.6 `engine_gate.py`, `four_engine_roads.py`, `check_training_device.py`, the other callers, the app

**`engine_gate.py`** (edited on C1b's text, so every item is cited by name; the lines given are at `91c6ece`):
- `preview_env(cycle, *, plant, dt, use_preview, horizon_s, seed, reward_knock)` builds `E.SupervisoryTunerEnv(..., preview_h_s=float(horizon_s), reward_knock=reward_knock)`, with no H refusal.
- `reward_knock` is a required bool, with no default, on `d34_env`, `training_env` (beside C1b's `roads_record`), `preview_delta`, `obs_trace`, `blind_check`, `run_gate` and `road_table`.
- Every task dict holds `engine` and `reward_knock`; the train tasks also hold C1b's `roads_record`. `job` passes `task['reward_knock']` to every environment it builds: through `preview_env`, `d34_env` and `training_env`, and directly to `E.SupervisoryTunerEnv` in its band and notch branches (`:388`, `:392`), which would otherwise keep `REWARD_KNOCK_DEFAULT` and judge the band and notch checks on the knock-in reward under a header that says "without". `run_gate` returns `reward_knock` beside C1b's `roads_record`.
- `print_gate` prints `reward              : with|without the knock term (--reward-knock in|out; row 113 (5))`.
- `horizons(None, engine_id)` returns `[E.PREVIEW_H_S]`.
- `--reward-knock {in,out}` is required on engine_gate's two command lines, `test_reward.py --engine` and `check_roads.py --engine` (6.4).
- `WaitsForPlantCommit` (`:117`), its raise in `preview_env` (`:245`) and its catch in `job` (`:414`) are deleted. `print_gate`'s NOT COMPLETE message (`:569`) reads "did not run".
- **The WHAT WAITS docstring: P's two bullets** (cited by name; `:52-55` and `:71-78` at `91c6ece`). The H bullet ("H as an environment parameter (row 117) comes with row 94's plant commit ... any other H is refused by preview_env and printed NOT RUN") and the knock bullet ("The reward's knock option ... so it cannot be passed before that commit") become false at P. P rewords both to what it builds: H is `preview_env`'s `horizon_s`, any H that `E.preview_samples` accepts, built with no refusal, and the blind-arm check runs at every H of the roads record's H_table; `--reward-knock {in,out}` is required on both command lines, passed to every environment `job` builds, the band and notch branches included, and printed in the header. The Accord bullet is C2's (section 4), and the decision-34 roads bullet Qa's (section 9).
- `FOUR_ENGINE_OPTIONS` is unchanged.
- **Test (P, `test_device_gate`):** a band job and a notch job each build their `SupervisoryTunerEnv` with the task's `reward_knock`, read by wrapping the constructor, for a knock-out task. The control (mistake 12) is the knock-in task, whose environment reads True.

**`four_engine_roads.py`:**
- `PREVIEW_DIVISORS = E.PREVIEW_DIVISORS` (the same object).
- `preview_h_problem(h_s)` returns None for None or for any H that `E.preview_samples` accepts, and the refusal text otherwise.

**`check_training_device.py`:** `fingerprint_dir` records `train_backend`, `score_backend`, `preview_h_s` and `reward_knock` when present. `IDENTITY_CMD` (:55-56) and `--compare` are unchanged.

**The other `plant_fingerprint` callers** (every one P's; finding 20). Each passes `train_backend=FP.BACKEND_CYCLE, score_backend=FP.BACKEND_CYCLE`, and:

| caller | `preview_h_s` | `reward_knock` |
|---|---|---|
| `conditions_test.py:374` | `E.PREVIEW_H_S` | `E.REWARD_KNOCK_DEFAULT` |
| `run_results.py:203` | `E.PREVIEW_H_S` | `E.REWARD_KNOCK_DEFAULT` |
| `app/results_provenance.py:474-475` | `E.PREVIEW_H_S` | `E.REWARD_KNOCK_DEFAULT` |
| `reconstruct_meta.py:249-253` | `E.PREVIEW_H_S if cfg["preview"] else None`, since its advisory `use_preview` is checked against it (6.2) | True: X1-era agents trained with the knock term. Its derived_sha override (:249-254) stays |
| `app/agent_catalog.py:222-224` | `E.PREVIEW_H_S` | `E.REWARD_KNOCK_DEFAULT`. It builds the blind side with `FP.for_arm`. `protocol_of` keeps None for 'decision-34' |
| `test_cars.py:926` | the new signature, inside its `assertRaises(ValueError)` | |
| `test_plant_guards.py:199`, `:279`, `:289`, `:314` | the new signature; `:289`'s 'table:0123' case moves to CycleBackendOnly, as `train_backend="table:0123"`, still refused | |
| `test_epa_freeze.py:986` | 6.7 | |
| `test_engine_threading.py:582` | the probe still lacks the required keywords; its expected text names them | |

**App:**
- `results_provenance.schema_of(fp)` returns 4 when 'train_backend' is in the block, tested before 'engine'. `_plant_files(4)` and `_file_rule(4)` take schema 3's branch.
- `results_provenance.live_side` wraps its call in `except (Exception, SystemExit)` (`app/results_provenance.py:476-479`), so a wrong signature would fail silently. `app.test_results` therefore gains a check that `live_side(<the repository>)` lists no import error on the live tree.

### 6.7 Tests at P, one owner each

**`test_plant_guards.golden_digests(env, steps, *, seed)` (P1; the one definition):**
- sha256 over the float64 bytes of reward, obs and info's numeric values in sorted key order, per step;
- neutral actions for the first half, then `np.random.default_rng(seed)` actions.
- GOLDEN, seed 0:
  - the B58 on phase-d EPISODES[0] at dt 1, 300 steps;
  - the B58 on `ExtremesTrainingEnv(seed=0)`, 300 steps;
  - each EPA engine on the locked climb, 120 s at dt 1.0.
- Pinned from C2's tree, with the control re-run there before P's edits; both commits are recorded.
- P1's H-default test and P3's RewardKnock assert the same pins.

**`test_preview_horizon.py` (P1, new):** `preview_samples`; an H other than 30 s; BlindBitForBit (row 117's test, run first on a scratch draft for row 135 (5); at P a failure is a defect of P, fixed in P). It imports the golden helper.

**`test_plant_guards` (P):**
- P1: Transmission; BackendContract (unguarded); Pairing; D34Protocol; GitDirtyPlantFiles (exactness on synthetic paths); CycleBackendOnly (row 136: every train_backend and score_backend but 'cycle' refused, 'table:0123' and 'table:' with 64 hex among them, and `backend_of` refusing an environment with an engine_model; control: 'cycle' on both, and `backend_of` of an environment without one).
- P2: SchemaFour, with the FATAL tuple above verbatim and schema 3's message.
- P3: RewardKnock; TitCapInterfaces.

**`test_four_engine_training` (P1, P3):**
- Isolation's suffix test becomes the real-tree exactness test: every tracked path ending with a plant file's name without being it (`calibrate_thermal.py`, `car_thermal.py`) is not listed, and `thermal.py` is. SUFFIX_KNOWN is deleted.
- `test_the_hashed_list_is_the_35_and_closed_under_import` is unchanged.
- **The two pre-P H refusals are rewritten (P1; finding 28).** Each asserts the admitted H, the later knock refusal, and a control. Both are cited by name: C0's fix of `ScoredShareSYNTHETIC` moves this file's later lines.
  - `TrainAll.test_the_third_arm_is_refused_before_any_run_SYNTHETIC` (`:918-929` at `91c6ece`) must print "r = 1.5: tau 47.3351 s, H = 71.0026 s" and then be refused for the missing `--reward-knock`. Its control is an in-process `check_four_engine` call with `reward_knock='out'`, which is not refused at that check.
  - `TrainRefusals.test_every_H_but_30_s_waits_for_the_plant_commit` (`:693-698` at `91c6ece`) is renamed `test_an_H_other_than_30_s_is_admitted_and_the_knock_option_required`:
    - `preview_h_problem(30.000001)` is None;
    - the `H_before_the_plant_commit` case is refused by the knock check;
    - control: `preview_h_problem` of 0.0, -1.0, NaN and True is not None.
- The other in-process `check_four_engine` calls pass `reward_knock='out'` (P1).
- TrainSmoke (P3) passes `--reward-knock in` on the plain run and `out` on the full run; meta.json and config.json read True and False.
- No test of C1b's is edited at P. The selftest's four-engine check and `test_device_gate.Cli.test_the_benchmarks_four_engine_road_waits_for_the_plant_commit` each read `train.build_env`'s signature and adapt by themselves: from P on, the four-engine command carries `--reward-knock out` and passes `check_recipe`, and the command without it is refused (the control). P runs both (section 14).

**`test_device_gate` (P; every item by name, since C1b moves this file's lines):**
- `Roads.test_an_H_other_than_30_s_waits_for_the_plant_commit` (`:194-201` at `91c6ece`) becomes `test_an_H_other_than_30_s_is_admitted`:
  - for H in (29, 31, 60, 130), `preview_env(..., reward_knock=False).preview_s == E.preview_samples(H)`;
  - control: H = 0 and H = -1 are refused.
- Roads' `training_env` calls (C1b's `roads_record=None` among their keywords) add `reward_knock=False`, and so do the share test's.
- BlindArm passes `reward_knock=False` to `blind_check`. BlindArm is a class of `test_device_gate`, not of `test_four_engine_training`.
- `Verdict.gate`'s hand-built gate dict gains `reward_knock`, which `print_gate` prints from P on (C1b's share test already adds `roads_record` and `share_kind`).
- Cli: the knock refusal of `test_reward.py --engine` and `check_roads.py --engine` (6.4).
- The band and notch jobs' knock test (6.6).

**`test_engine_threading`:**
- P1: `CALLS['plant_fingerprint'] = [('kw','plant'), ('kw','train_backend'), ('kw','score_backend'), ('kw','preview_h_s'), ('kw','reward_knock')]` (replacing :185).
- P1: in `Signatures.test_entry_points_require_their_record`, `(FP.plant_fingerprint, "backend")` (`:756`) is replaced by `(FP.plant_fingerprint, "train_backend")`, `(FP.plant_fingerprint, "score_backend")`, `(FP.plant_fingerprint, "preview_h_s")` and `(FP.plant_fingerprint, "reward_knock")`. After P, `assertIn('backend', params)` would fail, and this is the test that holds the four keywords without a default at the signature (rule 1.7).
- P1: `PROTOCOL_DEFAULTS['preview_h_s'] = "the preview horizon H, s (row 117): 30 s gives PREVIEW_S on every engine; the four-engine arms pass r x tau"`.
- P3: `PROTOCOL_DEFAULTS['reward_knock'] = "the reward's knock term: True (X1's, knock in) unless a command passes --reward-knock (rows 113 (5), 118, 127 (4))"`.
- P2, Registry: `t = engines.trainable()` is a tuple; `t[0] == 'b58'`; `set(t) <= set(known())`; t is in known() order; `t == engines.trainable_in(engines.HERE)`. Line :1410 reads `assertIn('b58', engines.trainable())`.

**`test_trainable.py` (P2, rewritten):**
- `run(script, argv, *, root=None, control=False)`;
- `records_repo(summary=None, backend=None, *, state='committed', validation_files=())`, a temporary git work tree outside the repository;
- `ENTRY_POINTS = (train.py, train_all.py, run_phase_d.py, evaluate.py, benchmark_training.py)`;
- classes:
  - Help, B58, RecordsAbsent;
  - SummaryDrop (mazda_25t dropped; control: kept);
  - BackendDrop (ford_27tt dropped; control: kept);
  - RerunOpen (a `STARTED_rerun1` without `rows_rerun1.json` refuses every entry point; control: with both and the summary's re-run entry, it reads);
  - RerunGoverns (the first entry drops mazda_25t and the re-run keeps it: kept; control: the re-run drops it and the first keeps it: dropped);
  - StaleSummary (a committed `rows_rerun1.json` for mazda_25t with a committed summary.json whose `reruns` map does not list it refuses every entry point, naming the file, row 139 (1) and `validate_epa.py summary`; control: the same tree with the map listing `rows_rerun1.json` reads, and so does a summary.json with no re-run file beside it; the same refusal for a `rows_rerun1.json` present only in the work tree);
  - RerunNames (the pins to `validate_epa.rerun_name`);
  - RealTree, Reader, NotAtImport, OneDefinition;
  - Openable (protocol phase-d, `reward_knock=False`), Source, FingerprintCli.
- FingerprintCliRegistered is retired.

**`test_cars.Fingerprint` (P2; :895-909, docstring :74-76):**
- the CVT's `transmission_of` gives kind 'cvt' with its six fields;
- the Supra's `fp['transmission']['gears'] == [5.25, 3.36, 2.172, 1.72, 1.316, 1.0, 0.822, 0.64]`;
- the CVT on the B58 engine stops at `name_of` with LookupError.

**`test_epa_plants` (P2):**
- every plant's `fingerprint.py --engine` exits 0;
- the probe records `out['fingerprint_transmission']`, the stdout line starting 'transmission ', because the 2000-character tail can lose it;
- `problems()` requires 'kind=cvt' when `rep['cvt']`, else 'kind=stepped';
- the synthetic test fails a CVT that exits 1 or prints kind=stepped.

**`test_epa_freeze.Git.test_plant_sha_is_the_fingerprints` (P1):** `epa_freeze.plant_sha('b58') == FP._sha_files(FP.plant_files('b58'))` (replacing the call at :986).

**`app.test_results` (P):** `live_side()` on the live tree has an empty `import_errors`.

### 6.8 P's certificate and the sweep (row 138 (4), (6))

**The certificate:**
- PLAN.md 3.6 items 1-19 as amended, against `cf43fbb`, with commit A's added checks (B1-B3, B8, B9, B11, B12, HA.2-HA.11, HP7.1, HP7.6, HP7.7), `test_tit_cap.py` and BlindBitForBit. Item 20 (L8) is at step 18.
- `make_meta.py` writes the scratch meta.json as `FP.plant_fingerprint(protocol='phase-d', plant=engines.get('b58'), train_backend=FP.BACKEND_CYCLE, score_backend=FP.BACKEND_CYCLE, preview_h_s=E.PREVIEW_H_S, reward_knock=E.REWARD_KNOCK_DEFAULT)`, through `FP.for_arm(..., sighted=False)` for blind_seed0. The edit is recorded in TOOL_EDITS.md.
- B8 expects each entry point's usage to name `--engine {<engines.trainable() on the real tree at P, in known() order>}`. Its refusal and its control come from SummaryDrop.
- Every entry-point CLI runs in REPO or a git clone.
- The new `results/B58_IDENTITY.md`, its `.json` and the tools archive replace commit A's. Commit A's page moves verbatim to STATE_HISTORY.md (decision 67).

**The sweep (decision 67):**
- `git grep 865f8e7b7e5c2dbe`, plus each EPA engine's quoted plant_sha. Each present-tense mention gets the post-P value printed by `epa_freeze.plant_sha(e)` on P's tree.
- Lines naming the draw's or X1's plant stay. No hashed or record-bound file is edited (`epa_roads.py:143` stays).
- `Explanatory Simulation/tests/test_catalog.py:99` moves, with a comment naming P.
- No RETIRED entry is made.

**P's commit message records:**
- the four post-P plant_sha and derived_sha;
- `test_reward.py`'s output;
- `app.test_replay --full`'s output (CLAUDE.md: any change under `app/`; P edits `app/agent_catalog.py`, `app/results_provenance.py` and `app/test_results.py`);
- both of `--compare`'s lines;
- "from P on, the contract's engine_env.py citations are read at c842d74".

### 6.9 The fourth arm (only if row 135 (5) records it)

If row 135 (5) records that a blinded environment at two H gives two trajectories on a draft that meets row 117's construction, Ta's `ARMS` reads 4 and the code that trains the fourth arm lands in P, before B1. It changes the blinded arm's fingerprint (PLANT_CODE) and `train.py` (a cost file), so no later commit may carry it. Its names:
- `train_all.py --blind-per-h`, with `--third-arm` only: one blinded agent per ratio, at that ratio's H, in place of the one blinded agent. `four_engine_roads.run_tag(seed, use_preview=False, ratio=r)` then gives `blind_r<r>_seed<S>`, which it refuses today.
- `train.py` admits `--no-preview` with `--horizon-ratio`, refused today by `check_recipe` ("one blinded arm serves both ratios (row 117)").
- `fingerprint.for_arm` keeps a blinded-per-H agent's `preview_h_s`, since H then changes its environment (mistake 19), and `pair_problems` pairs it with the sighted agent at the same H.
- V's `arm_of` reads `blind_r{r:g}`, and the scores' arms gain `blind_r0.5` and `blind_r1.5`.

In that case O2 also amends this section with the full interfaces, before the rehearsal, so nothing of it is designed after Run 2.

## 7. G: commit G (row 141)

**`epa_fit.py`:**
- `epa_fit.BOUND_TOL_SCALE_UNITS = 1e-3`, in X_SCALE units (DESIGN). It sits in a new section appended after `run_t0`, so no line at or above :2776 moves.
- `epa_fit.bound_distances(names, x, *, lb, ub, x_scale) -> dict`. Per name, in order: `value`, `lower`, `upper`, `to_lower = x - lb`, `to_upper = ub - x`, `nearer`, `distance`, `x_scale` (or None), `distance_x_scale_units` (or None). Python floats; numpy and math only; no open; no new import.
- `epa_fit.bounds_at(names, x, active_mask, *, lb, ub, x_scale, tol=BOUND_TOL_SCALE_UNITS) -> list[str]`: the names, in order, where `active_mask[i] != 0`, or where both bounds are finite and `min(x[i] - lb[i], ub[i] - x[i]) <= tol * x_scale[i]`.
- `epa_fit.py:1727` reads `act = bounds_at(names, x, active, lb=lb, ub=ub, x_scale=[X_SCALE[n] for n in names])`.
- `:2002` reads `act = bounds_at(S4_PARAMS, x, act_kept, lb=lb, ub=ub, x_scale=xsc)`.
- Unchanged: line counts, STAGE_KEYS, FIT_JSON_KEYS, `_solve`, BOUNDS, X_SCALE, TOLERANCES, `perturbed`, every value.

**`calibrate_epa.py:1003`:** the path string reads "the Mazda's derived file". The tuple keeps its length and order, and Audit is untouched.

**`validate_epa.py:31-32`:** "The person commits ARMED.json, alone of / the validation folder's files, with the calibration's run.json (row 106): that commit is the arming." The line count is unchanged, and :532 and :668 are unchanged.

**`bounds_active_corrected.py write|check`:**
- Exit codes: 0 done (or no differences), 1 differences, 2 refused.
- `OUT_REL = 'results/EPA_CALIBRATION/bounds_active_corrected.json'`, `SCHEMA = 'epa-bounds-active-corrected/1'`, `ENGINES = thresholds.common.EPA_ENGINES`.
- Functions: `compute(root)`, `problems(root)`, `main(argv)`. No default on any function that takes `engine`.
- Imports: `epa_fit`, `epa_freeze`, `engines`, `thresholds.common`; never an `epa_rows` loader.
  - It imports no `fingerprint` directly and calls no `FP.*` function. `epa_freeze` imports `fingerprint` at module level (`epa_freeze.py:65`), so the check is made on the writer's own AST, never through `epa_roads.import_closure`.
- Inputs: `freeze.json` and `fit_<form>.json`, each sha_text-checked against freeze.json's `fits`, with the `frozen_sections_sha256` triple equality.
- `write` refuses an existing OUT, uses `epa_freeze.write_json_atomic`, and prints, per engine and stage, the names added and the separation. G's commit quotes that printed separation (row 141 (1)); no number read by hand is quoted. If the lists differ from row 109's, G commits with the lists as found, disclosed beside row 109's in its message and in the preregistration (row 141 (1)); the tolerance does not move.
- `check` compares every key except `versions`, and prints a versions difference.
- The layout is in 12.6.

**Tests:**
- `test_bounds_active_corrected.py`: every class Guarded; not in STEP2_TESTS; no typed frozen value. An AST test checks that the writer's own source imports no `fingerprint` and calls no `FP.*` attribute, and that no hashed module imports the writer.
- `test_epa_fit.BoundsActive(fx.Guarded)`, placed before `if __name__` (:1904).
- `test_calibrate_epa.Pieces.test_seen_before_the_fit_carries_the_disclosure`: two added assertions.
- `test_defect_route.LATER_HASHED` (:105) becomes `('epa_fit.py', 'calibrate_epa.py', 'validate_epa.py', 'evaluate.py')`, the files the test restores to the third commit F's version (:469-488), with the docstring at :31-35 updated.

**The diff gate** is `git diff --stat <G's parent> HEAD`: G lands after Qa (section 0), so its parent is Qa.

**ORDER step 20's disclosure line**, as ORDER_steps writes it ("decision 92's corrected lists and their tolerance, chosen after the distances were read (`results/EPA_CALIBRATION/bounds_active_corrected.json`, rows 109, 141)"), is written in O1. G adds only ORDER's status line.

## 8. V: the scoring protocol (ORDER step 16), and RS

### `evaluate.py` (V)

**Constants:**
- `DECISION_34 = 'd34'`, a separate constant. PROTOCOLS stays two entries, and `--protocol` choices are `sorted(PROTOCOLS) + [DECISION_34]`. A test pins it to FP.
- `D34_HEADER = 'DECISION 34 EVALUATION'`. The report is never written as `results/*_seed*.txt`.
- `SCORES_SCHEMA = 'four-engine-scores/1'`, pinned by a test equal to `four_engine_analysis.SCORES_SCHEMA` (:179). evaluate never imports the analysis.
- `PRACTICE_SCHEMA = 'four-engine-practice/1'`.
- `READING_KEYS = {'no_knock': 'damage_thermal', 'with_knock': 'damage'}`. The with-knock label is `roads_ceiling.KNOCK_LABEL`, imported lazily and pinned equal to `four_engine_analysis.WITH_KNOCK_LABEL` (:190).
- `ENV_KEYS`: config.json's `versions` (python, stable_baselines3, torch, gymnasium, numpy), `device` and `machine` (system, processor, cpus), and meta.json's advisory `python` and `numpy` (`fingerprint.py:75-76`; `train.run_config`).

**Functions:**
- `_drive(env, policy, *, plant, record)` returns `dict(ret, damage, damage_thermal, fuel, torque_viol, peak_turb, knock, steps)`. It is today's loop (:274-293), moved; `run_episode` and `run_road_episode` both call it.
- `run_road_episode(policy, road, *, plant, use_preview, preview_h_s, reward_knock, record)`:
  - builds `SupervisoryTunerEnv(epa_roads.env_cycle(road), plant=plant, dt=road['dt'], seed=road['episode_seed'], use_preview=..., preview_h_s=... (sighted; the env default for the blind arm), reward_knock=...)`;
  - then `reset(seed)`, pins w as float32, and sets `obs = env._obs()`;
  - refuses `steps != len(t) - 1` (899).
- `load_agent(path, meta, *, device)` returns `(policy, lines)`. On d34 and the practice route it uses `training_recipe.AveragedPolicy.load(run_dir, device='cpu')` and requires:
  - `train_recipe.checkpoint_average == training_recipe.DECISION_29_WINDOW`;
  - the manifest's window equal to it;
  - `total_steps == FP.model_budget(final.zip)['num_timesteps']`.

  A missing average or manifest is refused.
- `environment_problems(agents) -> list[str]` (finding 13; row 143 (5)): across every agent of one engine, every `ENV_KEYS` value must be equal. A mismatch is refused on d34 and the practice route (CLAUDE.md rules 3 and 5). The preregistration declares no environment ablation (section 11).
- `decision34_roads(*, root) -> (roads, provenance)`:
  - calls `FP.d34_roads(root=root)`;
  - checks each redrawn slot with `epa_roads.with_grade(original, slot, kept_grade)` and every other road against roads.json's;
  - runs `four_engine_roads.real_record_problem`;
  - reads the current re-verification record through `four_engine_roads.current_reverify(root=root)` (section 5) and refuses None. It requires: verdict EQUAL; roads_sha and redraws_sha the live ones; head an ancestor of HEAD (`epa_freeze.is_ancestor`); every `plants[e].plant_sha_now == epa_freeze.plant_sha(e)`.

  The provenance is in 12.7.
- `practice_set(record)` returns `record['practice']`. It requires 10 roads, road i with `k == i` and `episode_seed == epa_roads.PRACTICE_SEEDS[i]`, 3 float weights, and seeds disjoint from EPISODES'. It regenerates nothing.
- `arm_of(path, meta, roads_rec, engine) -> (arm, H_s)`:
  - blind: use_preview False and preview_h_s None;
  - sighted: `preview_h_s == four_engine_roads.horizon_s({ratios, tau, H_table}, engine, train_recipe.horizon_ratio)`, labelled 'sighted_r{r:g}';
  - the basename must equal `four_engine_roads.run_tag(seed, use_preview=..., ratio=...)`;
  - an agent whose `train_recipe.scored_share.seed_kind` is not 'REAL' is refused.
- `live_decision34(plant, *, preview_h_s, reward_knock, train_backend)` returns `FP.plant_fingerprint('d34', plant=plant, train_backend=train_backend, score_backend=FP.BACKEND_CYCLE, preview_h_s=preview_h_s, reward_knock=reward_knock)`, with no eval_dt or eval_duration. The blind side is `FP.for_arm(live, sighted=False)`. Pairing: `FP.pair_problems(...) == []` per seed, and an unpaired seed is refused.
- `check_declared(frozen_plant, variant_plant, declared)` returns the lines "DECLARED VARIANT <label>: <path> frozen <a> variant <b>" and both engine_shas. Every differing leaf of `dataclasses.asdict` must lie under a declared prefix, and every prefix must hold a difference. It takes no force parameter and never fingerprints a variant.
- `Variant`, a frozen dataclass: `label`, `frozen`, `plant`, `declared`, `context` (a picklable zero-argument factory of a context manager, or None), `damage_cal` (or None), `provenance`.
- `score_set(engine, models, roads, *, plant, reward_knock, train_backend, context, jobs, keep_records)`:
  - runs the baseline ECU, reactive and current-grade once per road, then each agent at its arm's H;
  - uses a spawn pool with one plant per worker, and is bit-identical at any jobs;
  - with keep_records, returns float64 t_turb, t_oil and ki.
- `scores_document(engine, rows, *, ratios, variant, provenance)`; `write_once_json(path, obj)`; `merge_scores(paths)`, which refuses a duplicate engine, mixed ratios or variants, or `n_roads != 20`. Versions are compared per engine (row 143 (1), (4)): every document of one engine, its primary and each row-115 variant, must record the same versions, platform and device, while two engines may differ only under row 143 (4).
- `rescore_from_records(records, *, cal)` returns `{'no_knock': [20 D], 'with_knock': [20 D]}`, a sequential Python sum of `engine_env.damage_rate(...) * dt`.
- `score_practice(engine, models, record, *, plant, reward_knock, train_backend)` and `pilot_spread(practice_doc, *, engine, ratio)`. s_p uses ddof = 1. evaluate never prints 1.5576.
- `score_declared(engine, models, *, variant)`: row 115's route. It writes `'variant': label`.

**The version-5 reading is never scored.** By row 95's own definition, "reported under both" means "Every slot that (2) changes is reported twice: as version 6 leaves it, and as it stands with the dropped engine still gating" (row 95). Scores are computed on the version-6 set only. The version-5 slots and the drop list go into the provenance (`version_5_reading`).

**CLI additions:**
- `--protocol d34`; `--practice` (needs d34); `--scores-out PATH` and `--records-out DIR` (outside the repository); `--jobs N`.
- `--reward-knock {in,out}` is required with d34 and `--practice`, never read from meta.json.
- Refused: `--force-plant-mismatch` with d34 or `--practice`, and a d34-only flag on phase-d or d2.
- The phase-d and d2 body is unchanged byte for byte.

**train_backend:** per engine, on d34 and on the practice route alike, from the committed `results/EPA_BACKEND.json` (`engines[e].backend`), read through P2's `engines.committed_record`. Under row 136 it reads 'cycle' for every surviving engine. Tb comes before PR, and so before decision 29's pilot (section 0), so every REAL scoring, the pilot's included, finds the record; a REAL scoring without it is refused. The value must equal every scored agent's meta.json `train_backend`, or the scoring is refused. SYNTHETIC tests pass it in.

### Other modules (V)

- `test_four_engine_training.Isolation.AFTER_V = ('training_recipe.py', 'four_engine_roads.py')`. The live `hashed_files` equals roads.json's 35 plus AFTER_V, and only `evaluate.py` may import them. `test_epa_tightenings.Isolation.test_no_hashed_module_imports_this_one` pins `len(files) == 35` (`test_epa_tightenings.py:949`); V makes it `35 + len(test_four_engine_training.Isolation.AFTER_V)`, the constant imported, never retyped (section 2).
- `tit_cap_rescore`:
  - `SHARED = tuple(sorted(set(tit_cap_ecu.RECORD_HASHED) & set(epa_freeze.CODE_HASHED)))`, asserted `== ('epa_rows.py',)`;
  - `RECORD = 'results/EPA_TIT_CAP/ford_27tt.json'`;
  - `cap_for_rescore(which, *, plant, root) -> (cap_k, record_sha_text, drift, lines)`, row 128 (a)-(d). The drift expected at V is calibrate_epa.py, epa_fit.py, evaluate.py and validate_epa.py;
  - `cap_context(which, *, plant, root)`;
  - the CLI `check --engine ford_27tt`.

### RS: `rescore_rows.py`

- `ROWS`: label -> (engines, builder, declared prefixes, closed-loop or records).
- Labels: `'<row>:<engine>.<field>:<end>'`.
- CLI: `score --row X --end E --primary S.json --models ... --jobs N --scores-out ...`.
- It imports evaluate, tit_cap_rescore, epa_fit and engines, and no hashed module imports it.
- Plant builders:
  - `epa_fit.perturbed(plant, *, record, field, value)` (:2756);
  - `engines.build_candidate(name, values)`, for (g), on the committed `results/EPA_CALIBRATION/<id>/e6/row7_090.json` and `row7_110.json`, the files the frozen `complete.json`'s `e6_files` names (written at `calibrate_epa.py:2680`), never a `defect_N/` copy, each checked by `epa_freeze.file_sha_text` against its digest there.
  - A test requires the (g) plant's engine_sha to equal `calibrate_epa`'s construction.

## 9. Q: the per-engine gates (ORDER steps 14a and 17)

**Qa (the code), after P:**
- `engine_gate.d34_roads(*, roads_file, synthetic_seed)` keeps its signature and its return, `(roads, H_table or None, label)`.
  - A `roads_file` whose record is REAL (its seed_kind, as `four_engine_roads.read_roads_record` reads it) must be `<root>/epa_roads.ROADS_REL`, with root the repository (`epa_roads.REPO`); any other REAL file raises ValueError.
  - Its roads are `FP.d34_roads(root=root)[1]`, the redrawn twenty, and its `H_table` is that same roads.json's. The label names the version-6 reading.
  - Any other roads file (a SYNTHETIC record) and a SYNTHETIC seed keep today's path.
- `test_device_gate.Roads` (Qa) tests it: the REAL record gives the redrawn twenty and roads.json's H_table; the control, a REAL record at another path, is refused (mistake 12).
- **The WHAT WAITS docstring's decision-34 roads bullet** (cited by name; `:64-70` at `91c6ece`) says that the code applying redraws.json is "evaluate.py's decision-34 protocol (ORDER step 16), not written yet, and --roads reads one record's roads as they stand". Qa makes that false for the REAL record, so Qa rewords it to what Qa builds: `--roads` on the repository's roads.json reads the redrawn twenty through `FP.d34_roads`, with that record's H_table, and any other roads file and a SYNTHETIC seed keep today's path.
- It is committed alone and pushed before any Q run, so every Q output names a pushed commit (finding 25).

**The runs:**
- They run in a `git clone` of the pushed Qa outside the repository, with the repository's `.venv/Scripts/python.exe -B` and the clone as the working folder. G's and V's edits in the repository therefore never reach them.
- They may start right after Qa, beside G's and V's other gates, but never beside `test_engine_threading`, an arming or a roads check (rule 1.3).
- Row 130 (5) fixes both readings of the training road: "The gate and the benchmark build the road with the share off (row 119 gates "row 116's training roads")", and engine_gate's training check also takes `--roads-record` and runs with the share on, "so that step 18 times what step 22 trains". With the share on, each training seed's first episode is a share road, so a share-on run alone would gate no general episode. Q therefore runs the gate with the share off, and the table both ways. Every Q command passes `--reward-knock out`. On every engine:
  - `test_reward.py --engine E --train-road four_engine --roads results/EPA_ROADS/roads.json`: row 119's gate, the share off (the general episodes), and decision 34's redrawn twenty;
  - `check_roads.py --engine E --train-road four_engine --roads results/EPA_ROADS/roads.json`, the share off;
  - the same `check_roads.py` command with `--roads-record results/EPA_ROADS/roads.json`, the share on: the training roads as step 22 trains them. The share's own roads are row 101's, which decision 34's checks already gate (row 130 (5)), so `test_reward.py` is not repeated with the share on;
  - the 0.05 % band and notch sweep;
  - the blind-arm check per engine and per H;
  - each engine's share below its torque floor (ORDER step 17).
- Each `check_roads.py` run writes its own file (12.9). Every gate's failure stops step 17 and is reported (rule 1.11).
- Outputs are copied into `results/ENGINE_GATES/<engine>/`, with Qa's sha beside them, and committed in Q after V, before B1.
- After a re-made P (row 140 (5)), the runs are repeated from a new clone of the pushed tree holding the re-made P and Qa's code, and committed before B1 is repeated.

## 10. T: Ta (the code) and Tb (the record)

Row 136 builds no table, so T has no table part. This sheet's drafts named that part TC (the table runtime module and `train.py`'s table option, the table builder, the S1/S2a gate script and the runbook's table-rate step, B1t) and TD (each table's records, its S1 and S2a records, and its rate's attempts). None of it is written: no table rate, no S2b pilot and no remedy.

### 10.1 `epa_backend.py` (Ta)

**Constants:**
- `PROTOCOL` is typed from row 135 and settable from neither the CLI nor the environment. It holds:
  - device, torch (the exact build), python '3.13.2';
  - runs N (one value), steps_per_run S, repeats R;
  - road 'four_engine', dt 1.0, buffer 450000;
  - roads_record 'results/EPA_ROADS/roads.json', scored_share True, reward_knock 'out', and the timed recipe flags `benchmark_training.RECIPE29_TIMED`, imported, never typed (the frozen `train_cmd` adds them to every command whose plan holds a roads record);
  - protocol_commit <C1b sha>, lock <path>.
- `CPU_PROTOCOL`, when row 135 names CUDA (row 135 (4)(c)): PROTOCOL with device 'cpu', the CPU lock and its torch build, and its own runs N, the CPU's pick in step 3's merged file (`pick_runs` on its CPU rows; row 135 (2)). Otherwise None.
- `W_S = 864_000`, `W_FIRST = '2026-11-10T00:00:00+03:00'`, `W_LAST = '2026-11-20T00:00:00+03:00'` (row 134 (1), `91c6ece`).
- `N_MIN = 20`, asserted `== benchmark_training.SEEDS_TARGET`.
- `SEED_LIMIT = 1000`; n >= 1000 is refused.
- `DROP_ORDER = ('honda_l15b7', 'mazda_25t', 'ford_27tt')` (row 136 (1): contract version 6 for the order of leaving), and `LEAVE_ORDER = DROP_ORDER`, the same object: under row 136 (2) an engine that leaves the exact cycle is dropped, with no table. The B58 is in neither (MD:1590-1591, "The B58 is never dropped"; `engines.NEVER_DROPPED`). A test pins the tuple, `LEAVE_ORDER is DROP_ORDER`, and `set(DROP_ORDER) == set(common.EPA_ENGINES)`. There is no table constant. The Ford, last in the tuple, is the last EPA engine to leave (row 136 (1); `apply_rule`).
  - `validate_epa.DROP_ORDER` is another thing: the contract's text that summary.json carries, "when the schedule forces a choice, the Ford first, then the Honda, the Mazda last" (`validate_epa.py:165-167`, written into summary.json at `:2552`). It is CODE_HASHED and is not edited. It decides nothing here; the backend record's `rule` names rows 114 and 136, and its `notes` say that summary.json's text is version 5's.
- `ARMS`: `benchmark_training.ARMS` (3), or 4 when row 135 (5) records a blinded-arm failure on a draft that meets row 117's construction (contract version 6, the arm count only; 6.9).
- `BENCH_REL = 'results/benchmarks'`; `ATTEMPT = 'B1_bench_{engine}.attempt{k}.json'`; `CPU_ATTEMPT = 'B1_bench_{engine}.cpu.attempt{k}.json'`; `B0_RECORD = 'B0_{git_head}.json'` (section 3, B0).

**Pure functions:**
- `wave_seconds(lower_min, N) = Fraction(PROD_STEPS) * N / lower_min`;
- `engine_seconds(n, lower_min, N) = ceil(ARMS * n / N) * wave_seconds(lower_min, N)`;
- `total_seconds(n, rates)`;
- `n_max(rates, w_s)`;
- `apply_rule(in_test, rates, *, w_s) -> {engines, in_test, n, trace}` (rows 114 and 136). Every engine in the test is on the exact cycle. n is `n_max` over them. While n < `N_MIN` and an EPA engine is in the test, the first engine of `DROP_ORDER` still in the test is dropped, with 12.5's schedule reason (its one definition, cited and never retyped here), and n is recomputed (row 136 (1)-(2)). The B58 is never dropped. So the Ford, last in `DROP_ORDER`, leaves only when it and the B58 together give n < `N_MIN`. When no EPA engine is left in the test, whether Run 2's drops or the schedule's left none, n is null, whatever `n_max` gives for the B58 alone: the four-engine test does not run, and the failed schedule is reported as the result (row 136 (1); MD:1611-1612; 10.2, 12.5). n is never an int below `N_MIN` (rule 0), and the B58 alone is never the four-engine test. `trace` lists, before each drop, the engines in the test, n and `total_seconds`.

**I/O functions** (none takes a default beside `engine`):
- `bench_attempts(root, engine, *, kind)`: every attempt committed at HEAD, for kind 'device' or 'cpu'.
- `classify(doc, engine, protocol, live, b0)` follows row 135 (4), where `b0` is the committed B0 record of the attempt's git_head (or None), and returns one of:
  - `('crash', why)`: (a) a status other than 'finished'; seed 0 not trained twice to the end (identical None); an N row not ok only through exit codes, a timeout, missing runs or an 'error:' line. (b) **An operator fault**, which row 135 (4)(b) makes a crash, so the series reading applies (repeated by the same protocol, every attempt kept):
    - `code.git_dirty` not False;
    - the plan's runs, steps or repeats unlike the protocol's, or any plan key unlike it: `plan.reward_knock == 'out'`, `plan.roads_record == ROADS_REL`, `plan.scored_share is True` (the learning-rate schedule follows from the roads record and the C1b diff below);
    - the device or torch build unlike the protocol's (PROTOCOL's, or CPU_PROTOCOL's for a CPU attempt);
    - the commit's `benchmark_training.py` unlike row 135's: `git diff --quiet <PROTOCOL['protocol_commit']> <git_head> -- benchmark_training.py` fails;
    - no committed B0 record for its git_head (`b0` None), or its `machine.host`, `code.benchmark_sha` or `code.train_sha` unlike that record's. They are never compared with the laptop's hashes (core.autocrlf);
    - runs on more than one plant;
    - `machine.engines_trainable` unlike `inputs.trainable_before`;
    - any row's `plant.reward_knock` not False;
    - any row's `plant.backend` not 'cycle'.
  - `('fallback', why)`: on CUDA, identical False, fits False at N, or seed0_twice False (row 135 (4)(c)).
  - `('defect', why)`: on the CPU, identical False.
  - `('stop', why)`: on the CPU, fits False at N.
  - `('measurement', lower_min)`.
- **Reading a series.** In every engine's series, every attempt but the last must classify 'crash', operator faults included. So a dirty attempt is kept and committed, and the series still reads.
  - On CUDA, every engine's CPU series exists, since B1 always runs it at the same visit (row 135 (4)(c)). It is read only after a fallback.
  - Any 'fallback' on any engine: every engine's CPU series is read instead, and the test trains on the CPU.
  - 'defect': refused (exit 2) with row 135 (4)(c)'s text: fix the defect, then repeat B1 for every engine. Attempts on a git_head before the fix are listed in `inputs.superseded` and not read.
  - 'stop': refused (exit 2) with row 135 (4)(c)'s text: the four-engine training stops before T, and it is reported.
  - A P re-made after B1's git_head (row 140 (5)) changes PLANT_CODE, a cost file. One rule covers it and the 'defect' case: every attempt whose git_head's `cost_files` differ from HEAD's is listed in `inputs.superseded` and not read. B1 is then repeated for every engine from the re-made, pushed tree, by row 135's protocol, every attempt kept. An engine with no attempt left to read refuses (exit 2), naming row 140 (5).
- `problems(root, *, live)`, `compute(root, *, live)`, `write(root, *, live)` (through `epa_roads.write_once`), `check(root, *, live)`.
- `live_plants(engine_ids)` is the only caller of `FP.plant_fingerprint` here. It passes both backends as cycle, `preview_h_s=None` and `reward_knock=False`, and maps 'backend' to `fp['train_backend']`.
- `cost_files(root, rev)`: the union of `epa_roads.import_closure(m, root=root)` for `train.py`, `train_all.py`, `benchmark_training.py` and `check_training_device.py`; FP.PLANT_CODE; `engines.spec_files(e)` for every engine; the derived files; `requirements-lock.txt` (and a CUDA lock); `results/EPA_ROADS/roads.json`. For the git_head of every attempt the series reading reads, `git diff --quiet <that git_head> HEAD -- <set>` must succeed.

**Rate and inputs:**
- `lower_min` is parsed from the JSON text through Decimal into a Fraction.
- `inputs.trainable_before = engines.trainable_from(engines.committed_record(root, engines.VALIDATION_SUMMARY_REL), None)`. An attempt whose `machine.engines_trainable` differs is an operator fault.
- Agreement on host, `benchmark_sha` and `train_sha`, the C1b diff and `code.git_dirty` are not bare conditions: each is an operator fault in `classify` (b). The last attempt of each series therefore has `code.git_dirty` False, and every dirty attempt before it classifies as an operator fault (finding 19 of round 1; row 135 (4)(b)).

**CLI:** `python -B epa_backend.py compute|write|check`, with no other argument; exit 0, or 2 when refused.

**Tests (`test_epa_backend.py`):**
- Guarded classes pass `live`.
- LiveRecord is unguarded, skipped until the record is committed, and a failure if skipped after.
- **ApplyRule** (round 4), on SYNTHETIC rates: with the B58 and the Ford at n < 20, the Ford is dropped with 12.5's schedule reason, n is null and `in_test` is ['b58']; the control (mistake 12), the same pair at n >= 20, keeps the Ford and gives that n. With all four engines at n < 20, the Honda leaves first and then the Mazda, n recomputed and traced after each. With every EPA engine dropped by Run 2, n is null without any schedule drop.
- **RunbookNames** (round 4). It reads `docs/build_step_2/DEVICE_RUNBOOK.md` from its blob at `PROTOCOL['protocol_commit']` (C1b, which alone edits it; section 2) and finds, in its B0, B1 and B5 blocks, each name pattern: B1's `B1_bench_$E.attempt$k.json` and `B1_bench_$E.cpu.attempt$k.json`, B0's `B0_{rec['git_head']}.json`, and B5's `cp -n` globs. With `$E`, `$k` and `rec['git_head']` read as `{engine}`, `{k}` and `{git_head}`, the first three must equal `ATTEMPT`, `CPU_ATTEMPT` and `B0_RECORD`, and every name those three format must match one of B5's globs. The control (mistake 12): the same text with one pattern renamed fails. So a drift between the runbook's names and Ta's fails at Ta, not at Tb after B1's device time. The runbook's shell text is the names' one definition (this sheet's "How it binds"), and Ta's constants are checked against it.
- **Preregistration** (finding 14) is unguarded, skipped until `results/PREREGISTRATION_4E.md` is committed, and a failure if skipped after. When the committed backend record's n is null (row 136 (1)), PR is never written, and the test requires the file to be absent; its control, the file present beside n null, fails. The protocol it checks against is CPU_PROTOCOL when B1's committed series read a fallback (the series reading above; `results/EPA_BACKEND.json`'s `inputs.fallback`, committed before PR, is then not null and must agree), and PROTOCOL otherwise. Every `train_all.py` command line in it must pass:
  - `--jobs` equal to that protocol's `runs`;
  - `--device` equal to that protocol's `device`;
  - `--road four_engine`, `--dt 1`, `--third-arm`, `--recipe29`, `--roads-record PROTOCOL['roads_record']`, `--reward-knock out`, `--steps 450000` and `--no-resume`;
  - `--blind-per-h` when `ARMS == 4`, and never when `ARMS == 3` (6.9);
  - `--out runs/four_engine_dt1_<engine>`.
- **The seeds.** PR follows Tb (section 0), and every command's `--seeds 0-<n-1>` is checked against the record's n for every engine in `in_test`.

### 10.2 Tb

- Order: `write`, then the drop lines and CHECKPOINT, then `verify_docs`, then commit, then `check`, `test_trainable` and `test_engine_threading` (alone), then push. No entry-point parser is built between `write` and the commit.
- It is step 19, after B1 and before PR. Row 136 builds no table, so no S2b pilot comes before it.
- Drop line: "<date>: <engine> dropped by row 114's schedule, in row 136's order (n <before> -> <after>; results/EPA_BACKEND.json <sha_text>); amends decision 24 (MD:1606-1608)", where `<after>` reads 'null' when no EPA engine is left (12.5). For the Ford, row 107 (6)'s sentence follows verbatim.
- `four_engine_analysis` context: `seeds_per_arm = record['n']`, `engines_in_test = record['in_test']`.
- **With n null** (row 136 (1); 10.1 `apply_rule`): Tb writes and commits the record as above, with the drop lines (the last EPA engine's among them) and CHECKPOINT's line that the four-engine test does not run, quoting MD:1611-1612 ("If no EPA engine survives, the four-engine test does not run, and the failed validations are reported as results"). The session report gives the failed schedule as the result: the record's `trace`, each engine's r_e, W, and row 136 (4)'s three disclosures. ORDER steps 20-22 do not run, and `four_engine_analysis` is not run. n is never typed below 20 to rescue it (rule 0).
- T flips no pin.

## 11. PR: the preregistration (ORDER step 20)

- File `results/PREREGISTRATION_4E.md`.
- Each engine trains into its own `--out runs/four_engine_dt1_<engine>`. Run tags carry no engine (`four_engine_roads.run_tag`, `four_engine_roads.py:520-528`; `train.py:750` joins `--out` and the tag), and `train.CLOSED` matches the folder's basename (`train.py:753`). So four engines in one folder would meet each other's runs.
- The pilot uses seeds 2000-2004 in `runs/four_engine_pilot_dt1_b58` (not in `train.CLOSED`).
- The command per engine, each flag checked against `train_all.py`'s parser (`train_all.py:241-268`):

  `python train_all.py --engine E --device <PROTOCOL's device, or the CPU under row 135 (4)(c)'s fallback> --road four_engine --dt 1 --third-arm --recipe29 --roads-record results/EPA_ROADS/roads.json --reward-knock out --seeds 0-<n-1> --steps 450000 --jobs <PROTOCOL's N, or CPU_PROTOCOL's under the fallback, typed as a number> --no-resume --out runs/four_engine_dt1_<E>`

  Under four arms (row 135 (5)) every command adds `--blind-per-h` (6.9). `--recipe29` is decision 29's recipe as C1 named it (`train_all.py:49-50`). `test_epa_backend.Preregistration` checks the command.
- **n.** PR follows Tb and states the n of `results/EPA_BACKEND.json`, which every command types as `--seeds 0-<n-1>`. There is one command block, for the engines of `in_test` (row 136). When the record's n is null, no EPA engine survives: PR is not written, the four-engine test does not run, and the failed schedule is reported as the result (row 136 (1); MD:1611-1612; 10.2). n is never below 20 (rule 0), and no command trains the B58 alone as the four-engine test.
- The crash rule recommended is X1's: re-run from step 0, the dead folder kept.
- Beyond ORDER step 20's list, PR states:
  - each engine's 850 °C level row and its label;
  - the coverage flags;
  - E6 row 13;
  - the load-bearing constants by name (row 142);
  - row 136, contract version 6 for the order of leaving and the table route: every engine trains and is scored on the exact cycle, its P6 contributing nothing (MD:1580-1581); engines leave in the order the Honda, the Mazda, the Ford, and an engine that leaves is dropped; the order's end, the Ford leaving only when it and the B58 cannot reach n ≥ 20, after which the test does not run (MD:1611-1612); row 107 (6)'s reading of any verdict without the Ford; and the version-5 reading beside it (under version 5 the Ford would have left first, and trained on its table had it read validated (S1, S2a, S2b), and otherwise taken the remedies, then the exact cycle or the drop order);
  - the scoring machine and budget (row 143);
  - that the four-engine result is computed on the version-6 road set only, with the version-5 slots reported per row 95;
  - that every seed and arm of an engine trains on one environment, with no ablation declared (row 143 (5));
  - the blinded arm's count and the SYNTHETIC part of the Honda's gate, both MEASURED before the first arming (row 135 (5), (8)), and the rest of the Honda's gate as Q ran it (row 137 (6));
  - every B1 attempt (row 135 (4)), and whether the CPU fallback was taken.

## 12. Record layouts (one definition each)

**12.1 The meta.json `fingerprint` block, schema 4 (P1).**
- The FATAL fields and `schema: 4`.
- Field types:
  - `preview_h_s`: a float, or null for the blinded arm.
  - `reward_knock`: a bool.
  - `train_backend`: 'cycle' (row 136).
  - `transmission`: as `transmission_of`.
  - `backend_contract`: as `backend_contract()`.
  - `scenario`: 12.10 under d34, otherwise as in schema 3.
- Advisory: `plant_text_sha`, `preview_samples_s` (a list or null), `git_head`, `git_dirty` (null when git cannot answer), `git_dirty_plant_files`, `n_episodes`, `python`, `eval_dt` and `eval_duration` (under d34 the record design's dt 1.0 and duration_s 900.0; otherwise evaluate.DT and DURATION), then the caller's advisory keys.
- Never: roads_seed, commit_reveal or any revealed integer.

**12.2 config.json (P, `train.run_config`).** Today's keys, plus, top-level and copied from `live`: `backend = live['train_backend']`, `train_backend`, `score_backend`, `preview_h_s` and `reward_knock` (a bool). Nothing new goes inside `cfg['recipe']`. Its `versions`, `device` and `machine` are V's `ENV_KEYS`.

**12.3 Step records (C2).**
- The B58's and a stepped EPA car's evaluate record holds FIELDS (44); its .json lists `list(FIELDS)`.
- The Honda's evaluate record holds FIELDS + CVT (48); its .json adds `cvt_branches`.
- The B58's `train_record.npz` holds 47 fields (5 + 40 + 2), 274 B a step.
- The Honda's holds 51 fields (gear int64 -1, cvt_branch int64, cvt_ratio, n_eco and t_eco float32), about 294 B a step (ASSUMED; computed at B1 as the sum of nbytes of `train._record_arrays` over a one-step dict built from `train.rec_fields(engines.get('honda_l15b7').car)`). `test_step_record.HondaTrainRecord` checks the fields and dtypes.

**12.4 `results/EPA_ROADS/reverify.json` (RV; written by `adopt` in P).** LF, ASCII, no NaN. It writes no line to `attempts.jsonl`. Fields:
- schema; row 'rows 94, 97, 127 (1), 140'; mode 'adopted-check' or 'record'; verdict 'EQUAL'; partial false;
- roads_sha and redraws_sha (64 hex, or null);
- head (40 hex), pushed, clean;
- tree_changes [{path, sha_text}] (empty in record mode);
- started, finished, jobs;
- env {OMP_NUM_THREADS, MKL_NUM_THREADS, python_B};
- versions;
- plants {e: {plant_sha_at_draw, plant_sha_now, engine_sha_at_draw, engine_sha_now, engine_sha_complete_json}};
- hashed_files {may_differ, changed_since_draw, sha_text_now};
- contract_equal, data_inputs_equal, files_opened_new [];
- taus_read_from_the_record;
- reconstruction {generated_arrays_sha256, steps_log_step2, final_arrays_sha256, steps_log_step4a, equal};
- sections {name: {values, differences, first}};
- ignored {paths, why}, added_by_step_12a [], not_recomputed, changed_during_run;
- code {sha_text of roads_reverify.py and its closure};
- supersedes (null, or {path, sha_text, row});
- steps_log.

Successor records are `reverify_<n>.json` for n >= 2. The current record is the one `four_engine_roads.current_reverify` returns, and Live's reference commit is `roads_reverify.reference_commit` of it (section 5).

**12.5 `results/EPA_BACKEND.json` (P2 reads it; Tb writes it once).**
- Top-level: `{schema 'epa-backend/1', rule, window, constants, protocol, drop_order, inputs, trace, engines, in_test, n, seconds_at_n, total_s, slack_s, notes, provenance}`.
  - `rule` names rows 114 and 136; `drop_order` is `epa_backend.DROP_ORDER`, as a list.
  - `notes` say that every engine trains on the exact cycle with no table (row 136, contract version 6 for the order of leaving and the table route), that summary.json's `drop_order` text is version 5's (10.1), and, when n is null, that the four-engine test does not run (row 136 (1); MD:1611-1612).
- `engines = {id: {drop: bool, backend: 'cycle' or null, reason: str or null}}` for exactly b58, ford_27tt, honda_l15b7 and mazda_25t, in known() order.
  - The B58's drop is false, and its backend is 'cycle'.
  - backend is 'cycle' for every engine kept and null exactly when drop is true.
  - Each Run-2 drop is repeated as true, with reason 'Run 2: results/EPA_VALIDATION/summary.json <sha_text> (row 107 (1))'. After a defect re-run, the governing entry is row 139 (1)'s.
  - Each schedule drop has reason 'rows 114 and 136: the schedule (n <before> -> <after>)', where `<after>` is the n recomputed after the drop, or 'null' when no EPA engine is left. This is the one definition of a schedule drop's reason: `apply_rule` (10.1) cites it and never retypes it.
- `in_test`: the kept ids in known() order.
- `n`: an int >= 20, or null when no EPA engine survives, from Run 2's drops or the schedule's (row 136 (1)). With n null, `in_test` is ['b58'], `seconds_at_n`, `total_s` and `slack_s` are null (DESIGN), `trace` keeps every n before each drop, and the four-engine test does not run (MD:1611-1612; 10.2).
- `inputs` holds:
  - `trainable_before`;
  - `summary {path, sha_text}`;
  - `benchmarks {e: {path, sha_text, git_head, host, device, torch, python, benchmark_sha, train_sha, plant, runs, lower_by_repeat, lower_min (string), r_e ('p/q'), r_e_steps_per_s, steady, loaded, fits, determinism, git_dirty}}`;
  - `fallback` (null, or the CUDA failure that sent every engine to the CPU);
  - `superseded [{engine, path, sha_text, git_head, why}]`, why naming the defect fix or the re-made P (10.1);
  - `crashes [{engine, path, sha_text, why}]`;
  - `b0 [{path, sha_text, git_head}]`, every committed B0 record that `classify` read.
- There is no top-level 'drops' key. P reads only `schema` and `engines[*].drop`.

**12.6 `results/EPA_CALIBRATION/bounds_active_corrected.json` (G).**
- schema; decisions ['decision 92', 'row 109', 'row 141']; rule;
- tolerance {value 1e-3, unit 'epa_fit.X_SCALE units', constant 'epa_fit.BOUND_TOL_SCALE_UNITS', chosen_after 'the distances were read (disclosed)'};
- bounds (BOUNDS, with ve_rpm null); x_scale;
- engines {id: {form, inputs {file: sha_text}, frozen_sections_sha256, ve_rpm_bounds_from, distances {name: bound_distances entry plus stage}, stages {S2, S4: {params, recorded, corrected, added, flag_recorded, flag_corrected}; S1, S3b, S5: {recorded, rule}}, other_forms {file: 'not corrected'}}};
- code_sha_text; versions; fit_run false; frozen_records_rewritten false; not_rewritten_note.
- No timestamp and no HEAD.

**12.7 Scores, practice and per-step records (V).**
- Scores follow `four-engine-scores/1` (`four_engine_analysis.py:179` and its validator): arms blind, sighted_r0.5 and sighted_r1.5; seed keys as decimal strings; D and D_base over 20 roads per reading.
- provenance = {protocol 'd34', scenario, episodes_sha, roads_sha, redraws_sha, reverify {path, sha_text}, arrays_sha256, reading 'version 6', dropped, version_5_reading, reward_knock false, train_backend per engine, score_backend 'cycle', versions, platform, device 'cpu', environment (the agents' common `ENV_KEYS`), agents {arm: {seed: {path, H_s, r, manifest_sha256}}}, variant_lines, rescored_engines, copied_from}.
- Practice documents follow `four-engine-practice/1`.
- Per-step records are `<DIR>/<engine>/<arm>_seed<S>.npz` and `<DIR>/<engine>/baseline.npz`: float64 t_turb, t_oil and ki of shape (20, 899) plus dt, in road k order, outside the repository. A committed `<scores>.records.json` holds {files: {rel: sha256}, scores_sha256, command}.

**12.8 B1 attempt files (row 135 (4); C1b's runbook).**
- They are written on the device to `$B1OUT`, the one folder B0 sets for every session of B1, as `B1_bench_<engine>.attempt<k>.json` and `.txt`, with k = 1, 2, ... counted over a `.json` or a `.txt` in `$B1OUT` and in the committed `results/benchmarks/`.
- On CUDA there are also `B1_bench_<engine>.cpu.attempt<k>.*`, always.
- Beside them, `B0_<git_head>.json` for each commit B1 ran from (section 3, B0).
- A repeat of B1 (rows 135 (4)(c), 140 (5)) continues k in the same folder; nothing is overwritten.
- Every attempt is copied into `results/benchmarks/` only for its commit, after the last engine, and is committed, never renamed or deleted.
- Ta's `classify` reads every attempt. In each series, the last attempt is the measurement or row 135 (4)(c)'s outcome, and every earlier one classifies as a crash. The last attempt of each series has `code.git_dirty` False, and every dirty attempt classifies as an operator fault (row 135 (4)(b)).

**12.9 `check_roads.py --engine` output (C1b, P3).** `check_roads.default_table` names it. From C1b: `results/ENGINE_GATES/<engine>/check_roads_<train_road>.json`, and on four_engine `check_roads_four_engine_share_on.json` or `check_roads_four_engine_share_off.json`. P3 adds a `reward_knock` argument and appends `_knock_in` or `_knock_out` (so `check_roads_four_engine_share_off_knock_out.json`). The keys: `roads_record` (`engine_gate.record_name`'s: `epa_roads.ROADS_REL` for a REAL record, or null) and `share_seed_kind` (C1b), and `reward_knock` (a bool, P3).

**12.10 The d34 scenario (P1).** `{protocol: 'decision-34', seed_kind, roads_sha: ER.roads_sha(roads.json), redraws_sha: common.sha_text(redraws.json) or None (SYNTHETIC without redraws only), reading: 'version 6' | 'first draw', design_sha: sha256(json.dumps(record['design'], sort_keys=True))[:16]}`.

## 13. Values read, never typed

- **roads.json's `hashes.versions`** (read by grep on 2 November): python 3.13.2, numpy 2.5.3, scipy 1.18.1, platform Windows-11-10.0.26200-SP0. The re-verifier compares against the record, not these words.
- **engine_sha that P must keep**, as roads.json records them: b58 023f5589215ee68e, mazda_25t 2558cb2bcad4f2c6, honda_l15b7 ae07dfb4edb9ceb3, ford_27tt 671b624ae11e0916. Tests read the record.
- **plant_sha at the draw**: the B58's is `epa_roads.B58_PLANT_SHA` (865f8e7b7e5c2dbe). The post-P values are printed on P's tree by `epa_freeze.plant_sha` and recorded in P's message and in `reverify.json`.
- **Other constants, read from their owners**: `training_recipe.DECISION_29_WINDOW` (50 000), `four_engine_analysis.D_BASE_RTOL` (1e-9), `epa_roads.PRACTICE_SEEDS`, `four_engine_roads.reserved_seeds()`, and `engines.get('b58').engine.damage.turb_knee_k` (1123.0 K, `engine_specs/b58.toml:175`) for row 142 (e).
- **The E6 row-7 records** (row 142 (g)): `git ls-files` on 2 November lists `results/EPA_CALIBRATION/<id>/e6/row7_090.json` and `row7_110.json` for each EPA engine, plus the Mazda's `defect_1/` and `defect_2/` copies. Only the first are read.

## 14. Gates, commit by commit

"(alone)" means rule 1.3's `test_engine_threading` window. "ORDER:5's two checks" are rule 1.4's.

- **O1:** `verify_docs`; ORDER:5's two checks.
- **C0:** `test_four_engine_training`, every test passing, with the control: the same two tests without C0's two `ER.COMMITMENT_*` patches fail with the refusal they fail with at `91c6ece`; `verify_docs`; ORDER:5's two checks. All three are run on C0's own commit, and their printed lines go in C0's message.
- **C1b:**
  - `benchmark_training.py --selftest`: the extremes byte-identity against `PRE_C1B_BLOB`, the four-engine command through `train.py`'s parser and `check_recipe`, and `code_info` on a scratch work tree among them;
  - `test_four_engine_training`, every test passing on C0;
  - `test_device_gate` (RunbookB1 with B0's record and the CPU series, the share tests, Cli's C1b refusals and the four-engine benchmark's wait for P among them);
  - `test_engine_threading` (alone);
  - `test_trainable` (unchanged refusals);
  - `test_reward.py` and `check_roads.py` at the B58 defaults, their output identical to the same runs at `91c6ece`, the comparison in C1b's message;
  - `verify_docs`, run in the repository by whoever commits C1b, since it reads `logs/epa/MANIFEST.csv`; ORDER:5's two checks.
- **C0 and C1b, both:** committed with the identity the repository's other commits carry, not the drafts' placeholder `draft <draft@local>`, and C1b's subject without "(DRAFT)" (section 16).
- **S (no commit):** BlindBitForBit on the scratch H draft; the SYNTHETIC part of the Honda's gate on the scratch C2 draft, every check line it prints. Both outputs go outside the repository, and row 135 quotes them.
- **O2:** `verify_docs`; ORDER:5's two checks.
- **C2:**
  - `check_training_device.py --identity` on C2's clean parent. The run may start in a detached clone once R4 is pushed. If a docs-only commit intervened, `git diff --stat <R4> <parent> -- '*.py' requirements-lock.txt engine_specs/` must print nothing.
  - `--identity` on the final tree, then `--compare`: "compared N tensors, 47 record fields, 8 counters and the curve", then "VERDICT: IDENTICAL TRAINING". This proves the B58 unchanged; HondaTrainRecord covers the Honda.
  - `test_trainable`, `test_step_record` (HondaTrainRecord among them), `test_cars`, `benchmark_training.py --selftest` (C2 edits `train.py`'s recorder; the 274 B pin), `test_engine_threading` (alone), `verify_docs`.
  - The Honda's gate repeated (section 4), printing row 135 (8)'s check lines, each with the same result and detail.
- **Step 13:**
  - `test_defect_route` passes.
  - Each of F1, F2 and F3 touches only the files ORDER step 10 names for it.
  - Arm's and run's printed verdicts are in their records.
  - summary.json's `reruns` maps are empty, or every re-run is complete, listed in the committed summary.json, and read by row 139 (1).
  - L's labels match each record.
  - Every F is pushed, and nothing but the label record changed between an F and the next E.
- **RV:** `test_roads_reverify` (its SYNTHETIC full-shape test mandatory, `current_reverify` and `reference_commit` among its tests); `check --jobs 14 --out <outside> --skip-companions` on RV's clean tree prints EQUAL; then `test_engine_threading` (alone); `verify_docs`.
- **P:** ORDER step 14's list, extended:
  - `check_premise.py`; `validate.py` with `validation_table.md`; `test_reward.py` (its output in the message); `check_roads.py`;
  - every STEP2_TESTS suite;
  - `test_carried`, `test_fuel_forms`, `test_cars`, `test_trainable`, `test_plant_guards`, `test_preview_horizon`, `test_step_record`;
  - `test_epa_roads`, `test_roads_ceiling`, `test_epa_tightenings`, `test_defect_route`, `test_roads_reverify`;
  - `test_four_engine_training`, `test_device_gate`, `test_tit_cap.py`;
  - `benchmark_training.py --selftest`: the frozen B1 command through P's `train.py` parser and `check_recipe`, with `--reward-knock out` (6.4);
  - `app.test_replay --full` (its output in the message), `app.test_simulation`, `app.test_agents` (record its skip count), `app.test_results` (the `live_side` check among them), and `node --test "static/sim/*.test.mjs"`;
  - the lab pins; the certificate (6.8);
  - `--identity` on RV and on P's tree, then `--compare`;
  - `roads_reverify.py check --jobs 14` EQUAL on P's candidate tree, beside the certificate's runs only; then `adopt`;
  - `test_engine_threading` alone, after the roads check and the certificate's runs;
  - `drift_test.py` if its guard is touched; `verify_docs`.
- **Qa:** `test_device_gate` (Roads' REAL-record test among it); `test_engine_threading` (alone); `verify_docs`.
- **G:**
  - `test_epa_fit`; `test_validate_guards`; `test_calibrate_epa`; `test_epa_rows` (green);
  - every STEP2_TESTS suite (row 120);
  - `test_bounds_active_corrected`; `test_defect_route`; `test_epa_roads`; `test_roads_ceiling`; the `test_roads_reverify` suite;
  - `test_engine_threading` (alone, while no Q run is going);
  - `bounds_active_corrected.py write`, then `check`;
  - `verify_docs`.
  - Its diff gate is `git diff --stat <G's parent> HEAD`, G's parent being Qa (section 7).
- **V:**
  - On G (before) and on V (after): `evaluate.py --engine b58 --protocol phase-d --force-plant-mismatch --out <outside>/v_gate/{before,after}.txt runs/extremes_dt1/sighted_seed0 runs/extremes_dt1/blind_seed0`, and the d2 hand-written run (certificate item 10). Each pair is compared by `l7_diff.py`.
  - `test_tit_cap`, `test_epa_roads`, `test_roads_ceiling`, `test_scoring_protocol` (the environment check, the version-6-only scoring and the practice route's train_backend read from the backend record among it), `test_tit_cap_rescore`, `test_four_engine_training`, `test_epa_tightenings` (its pin at 35 + AFTER_V), `test_four_engine_analysis`, `test_plant_guards`, `test_trainable`, `test_step_record`, `app.test_results`, `app.test_agents`, `drift_test` row 15;
  - `benchmark_training.py --selftest` (V edits `train.py`'s docstring);
  - `test_engine_threading` (alone, while no Q run is going); `verify_docs`.
- **RS:** its test; `test_engine_threading` (alone); `verify_docs`.
- **Q:** the gates themselves, run from Qa in a clone, with their outputs and Qa's sha committed.
- **CU (only on CUDA):** `check_training_device.py --identity` before and after, then `--compare` (IDENTICAL TRAINING on the CPU path); its CUDA path's own test; `test_device_gate`; `test_engine_threading` (alone); `verify_docs`.
- **Ta:** `test_epa_backend` (ApplyRule and RunbookNames among it, each with its control); `benchmark_training.py --selftest` (the last gate before B1 that runs it); `test_engine_threading` (alone); `verify_docs`.
- **B1:** L8 with `run_l8.sh`; `test_epa_plants` on the device; `--identity` and `--compare` (recorded). Ta's `classify` reads every attempt. The last attempt of each series has `code.git_dirty` False, and every dirty attempt classifies as an operator fault (row 135 (4)(b)). A repeat of B1 after a defect's fix or a re-made P (rows 135 (4)(c), 140 (5)) has the same gates.
- **Tb:** the order in 10.2.
- **PR:** `verify_docs`; `test_epa_backend.Preregistration`; push. PR is not written when Tb's n is null (row 136 (1); 10.2).

## 15. Where the resolutions disagreed, and the pick

1. **The re-verification's route.** The critic proposed RV, P, then a PV commit; G and V wrote "after PV". P4's resolution: check P's candidate tree, then `adopt` into P. **Picked: P4's.** Row 94 wants a mismatch "fixed in it before it is committed". Commit A's certificate set the precedent. It is one full run instead of two or three. G and V read "after PV" as "after P".
2. **A re-made P.** G proposed a scratch branch; P4 a restore commit on GRA-test. **Picked: P4's.** Row 132 already chose a restore commit, pushed, for the same problem, and the record names a pushed commit.
3. **When the Ford's cap went stale.** The critic, P1, P3 and P4 said "from P"; V said "since N". **Picked: V's**, MEASURED 2 November by sha256 of the git blobs (row 138 (3)).
4. **The reader of decision 34's set.** V reloaded redraws.json after `FP.d34_set`. **Picked: P1's `d34_roads`**, which returns the roads themselves. V and Q call it and add their own checks.
5. **The golden-trace helper.** P1 put it in `test_preview_horizon`, P3 in `test_plant_guards`. **Picked: `test_plant_guards`**, which is on ORDER step 14's list. It carries P1's two B58 traces and P3's EPA traces, with seed 0, pinned on C2's tree.
6. **The CvtVehicle docstring.** **Picked: C2's wording** (it names GEAR_CVT and CVT), applied by P3's engine_env edit.
7. **A Run-2 drop's `reason`.** P2: 'section 7 (summary.json)'. T: the summary's sha_text. **Picked: T's**, since T owns `reason`.
8. **A dropped engine's `backend`.** The critic: 'cycle' or a table's string. P2 and T: null. **Picked: null.**
9. **The plant_sha sweep.** P1 wanted a row; P4 and T cited decision 67. **Picked: decision 67**, with no RETIRED entry. Row 138 (6) records only the reading: present tense is updated, history is kept.
10. **The table route.** T recommended "not built". The sheet picked row 114 as answered, because row 114 rejected the skip explicitly, and left the trade to Ghassan. **Settled by Ghassan, row 136:** no table is built, and engines leave in the order the Honda, the Mazda, the Ford, each one dropped. His confirmation of the same day fixes the end: the Ford leaves only when it and the B58 cannot reach n ≥ 20, and then the four-engine test does not run, and the failed schedule is reported (MD:1611-1612). Every table branch of this sheet is gone with it.
11. **`reward_knock` in PLANT_KEYS.** P3: optional. T: conditional. **Picked: added in C1b**, so T checks what trained (mistake 19).
12. **The benchmark's knock flag before P.** **Picked: both rules.** It is required with four_engine and refused before P, so four_engine cannot be benchmarked before P, which nothing needs.
13. **evaluate.py's knock default.** P1: 'in'. P3: None, read as 'in'. **Picked: P3's form.** It lets V require the flag on d34.
14. **P's `--identity` "before" run.** P3 would reuse C2's "after" file. **Picked: a fresh run on RV.** The saving is one 600-step run.
15. **G's readings row.** G committed it in G. **Picked: committed in O1, before Run 2.** The tolerance is then fixed before any held-out result; its numbers come from the writer's run at G.
16. **When `rescore_rows.py` lands.** V allowed everything in V. **Picked: its own commit RS** after V, outside T's window, off the path to B1.
17. **The benchmark protocol and a later table route.** No resolution covered this. The sheet added a dormant option to C1b for a table's rate. **Withdrawn under row 136:** no table's rate is measured, so C1b drops the option before its commit (section 3).
18. **Where the one re-verification reader lives.** `evaluate.py` cannot import `roads_reverify`. **Picked: `four_engine_roads.current_reverify`**, written by RV, joining the closure through `evaluate.py` only at V.

## 16. The adversarial checks: each finding, and where it is applied

Row 136 (Ghassan's answer of 2 November) supersedes every finding of rounds 1 and 2 that was about the table route, and the table part of five more: round 1's 3 and 8; round 2's r6, r14, b1 and b13, and the table parts of r2, r3, b3, b11 and c3. Their "applied in" cells name the sections as they stood before row 136, and are marked. Those sections' table parts are gone; everything else in them stays as applied.

### Round 1: the two checks of the first draft

| # | severity | finding | applied in |
|---|---|---|---|
| 1 | blocking | B1's attempts inside the clone record a dirty tree | 3 (runbook, RunbookB1), 10.1, 12.8; row 135 (4) |
| 2 | material | row 135 (5)'s 4n is undeclared version-6 text; a failure at P is left open | row 135 (5); 6.7; 10.1 `ARMS` |
| 3 | material | route (2) needs a forbidden re-measurement; the table rate has no protocol | superseded by row 136 (no table); was 0, 6.1, 6.2, 10.3, 10.4, 15 (10) |
| 4 | material | non-crash unusable B1 rows wait for a post-Run-2 row | 10.1 `classify`; row 135 (4) |
| 5 | material | row 139 (1) defers which drop governs | 6.3; 6.7 `test_trainable`; row 139 (1) |
| 6 | material | the Honda's gate first runs after Run 2 | 0, 0.1 (2c), 4, 14; rows 135 (8), 137 (6) |
| 7 | material | commits before R4 skip ORDER:5's checks | 1.4, 14 |
| 8 | material | Tb before PR in every case | superseded by row 136: with no table, Tb before PR is the one order (0, 10.2, 11; ORDER steps 19-20) |
| 9 | minor | section O's note hides the rows each row replaces | section O's note; rows 137-143 |
| 10 | minor | row 141 quotes hand-read factors | row 141; 1.9; 7 |
| 11 | minor | row 142 names E6 files that do not exist | 8 (RS), 13; row 142 (2)(g) |
| 12 | minor | R134 called staged; VD:340 stale | header, 0 |
| 13 | minor | no check that an engine's agents share one environment | 1.12, 8, 12.7; row 143 (5) |
| 14 | minor | nothing ties PR's `--jobs` to row 135's N | 10.1 Preregistration, 11; row 135 (2) |
| 15 | minor | version 5 never scored, with no citation | 8, 11 |
| 16 | minor | Q beside G's and V's `test_engine_threading` | 1.3, 9, 14 |
| 17 | minor | row 137 (3) claims coverage no test gives | 4, 14; row 137 (3) |
| 18 | blocking | the timed train.py command lacks `--scored-share`; the launcher lacks the third arm | 3; row 135 (2) |
| 19 | blocking | B1's untracked outputs make every attempt dirty | 3, 10.1, 12.8 |
| 20 | material | `plant_fingerprint` callers with no owner | 2, 6.6, 6.7 |
| 21 | material | engine_gate has no command line; test_device_gate unowned; BlindArm misplaced | 2, 3, 6.6, 6.7 |
| 22 | material | Live's reference commit undefined | 5, 12.4 |
| 23 | minor | V reads a superseded record after a re-made P | 5, 8, 12.4 |
| 24 | minor | rule 1.6 stricter than the gate | 1.6 |
| 25 | minor | `test_engine_threading` beside other runs; Q runs uncommitted code | 1.3, 9, 14 |
| 26 | minor | R134's instruction stale | 0 |
| 27 | minor | extremes plans gain two keys | 3 |
| 28 | minor | two P tests assert the pre-P H refusal | 6.7 |
| 29 | minor | an import-closure test of the writer cannot pass | 7 |
| 30 | minor | the critical path does not add up | 0.2 |

Found on re-reading the code, outside the 30: the four engines' runs in one `--out` would meet each other's run folders (`four_engine_roads.py:520-528`, `train.py:750`, `:753`), so section 11 gives each engine its own folder. Also, the part_probe comment is at `benchmark_training.py:450-451`, not :451-453.

### Round 2: the two checks of this sheet, and the review of C1b's draft

The rules check (r), the build check (b) and the review of C1b's draft (c). Two parts of round 1 were applied in substance, not to the letter, and stay so: the MEASURED neutral |r| goes into row 135 (8), since row 137 is committed before the scratch run can happen; and V's environment check compares config.json's `machine`, since config.json records no host name.

| # | severity | finding | applied in |
|---|---|---|---|
| r1 | material | row 139 (4) sends a drop to a row written after Run 2 | 1.11; row 139 (4) |
| r2 | material | B1's gate requires every attempt clean, so one kept dirty attempt blocks it | 10.1 (`classify`, "Rate and inputs"), 12.8, 14 (B1); ORDER step 18 (TD's part superseded by row 136) |
| r3 | material | the Preregistration check refuses row 135's CPU fallback | 10.1 Preregistration, 11; row 135 (2) (the table part superseded by row 136) |
| r4 | minor | row 135 (4) amends row 114 without naming its words | row 135 (4); O2's sentence in section O's note |
| r5 | minor | row 135 makes the CPU series conditional, the runbook runs it always | 3 (runbook), 10.1 (series), 12.8; row 135 (4)(c) |
| r6 | minor | the table builder and the S1/S2a gate script come after B1 (round 1's finding 3, in part) | superseded by row 136 (no table code); was 0, 0.1 (2d), 2, 10.4 |
| r7 | minor | step 22 does not wait for step 21 without a table | 0; ORDER 22 |
| r8 | minor | ORDER text outside rows 12a-22 goes stale: line 5's freeze, step 9's check, step 14's hours | 0 (O1); ORDER_steps section 3, step 14 |
| r9 | minor | P's commit message omits `app.test_replay --full` | 6.8, 14 (P); row 138 |
| r10 | minor | row 141 (1): G both stops before its commit and commits | 7; row 141 (1) |
| r11 | minor | row 137 (6) claims the whole Honda gate before the first arming | 4, 11, 14 (S); row 137 (6) and its title |
| r12 | minor | row 143 (1) contradicts (4); `merge_scores` refuses mixed versions across engines | 8 (`merge_scores`); row 143 (1) |
| r13 | minor | a re-made P re-runs no Q gate | 9; rows 135 (4)(c), 140 (5) |
| r14 | minor | a table remedied after S2b has no slot for its S1/S2a or rate | superseded by row 136 (no table, no remedy); was 0, 10.1 (`apply_rule`), 10.3, 10.4, 11, 12.5 |
| r15 | minor | the fourth arm: no owning commit, no Preregistration form, row 134 (1)'s 3n unnamed | 0, 2, 6.9, 10.1, 11; row 135 (5) |
| r16 | minor | "rows 135 and 136 stay reserved (row 134 (2))": row 134 (2) reserves row 135 only | section O's note; the provenance line |
| b1 | material | under a table, the pilots are read before the backend record exists, which V refuses | superseded by row 136: Tb comes before every pilot (8, train_backend; ORDER step 21) |
| b2 | material | `job`'s band and notch branches never receive the knock option | 2, 6.6 (and its test), 6.7 |
| b3 | material | the Preregistration test fails under the CUDA fallback and under a table | 10.1, 11 (the table part superseded by row 136) |
| b4 | minor | `Signatures` still requires `backend`; rule 1.7 cites CALLS only | 1.7, 2, 6.7 |
| b5 | minor | `test_epa_tightenings`' 35-file pin has no owner | 2, 8, 14 (V) |
| b6 | minor | `test_device_gate`'s row misses C1b's and P's edits; the knock refusal's place is unstated | 2, 6.4, 6.7 |
| b7 | minor | Qa's `d34_roads` is underspecified | 2, 9, 14 (Qa) |
| b8 | minor | BenchmarkArgv's "plan builder" does not exist | 3 (`make_plan`; the selftest's `train_check` replaces BenchmarkArgv), 6.7 |
| b9 | minor | the runbook's B0 checks out "the pushed commit after P" | 3 (B0) |
| b10 | minor | step 22 waits for Tb alone; section 0's "follows Tb" | 0; ORDER 22 |
| b11 | minor | the CUDA lock, the fourth arm and TD's device procedure have no slot or owner | 0 (CU), 2, 3, 6.9; ORDER steps 17a, 18 (TD's part superseded by row 136) |
| b12 | minor | `classify` omits the C1b diff and the host and benchmark_sha agreement | 3 (the B0 record), 10.1 `classify` (b); row 135 (4)(b) |
| b13 | minor | LEAVE_ORDER and TC's presence per TABLE_ROUTE are undefined | superseded by row 136: one `DROP_ORDER`, with `LEAVE_ORDER` the same object, and no TC (10.1) |
| b14 | minor | O1's provenance block moves the VD lines O1 and O2 cite | header, 0, 8; rows 135-143; the session note |
| c1 | blocking | `test_four_engine_training`, a C1b gate, fails 2 of 48 on the draft and at `91c6ece`; `verify_docs` not run | 0 (C0, its own commit before C1b), 2, 14 (C0, C1b) |
| c2 | material | B1 runs `$PY`, a CPU build, when row 135 names CUDA | 3 (B0, B1, RunbookB1), 12.8; row 135 (2) |
| c3 | material | no gate after C1b runs the selftest; `check_recipe`'s shape is unstated | 3, 6.4, 6.7, 14 (C2, P, V, Ta; TC's part superseded by row 136) |
| c4 | minor | k and B5 see one session's `$OUT` only | 3 (`B1OUT`), 12.8; row 135 (4) |
| c5 | minor | the share record's absolute path is recorded; the share-on and share-off files collide | 3, 9, 12.9 |
| c6 | minor | `--lr-schedule last-third` is not timed | 3 (`make_plan`, `train_cmd`); row 135 (2) |
| c7 | minor | `recommend`'s caption says two arms before a `--third-arm` command | 3 (Unchanged) |
| c8 | minor | C1b moves the lines P and C2 cite; row 134's `benchmark_training.py:36-38` goes stale | header, 2, 4, 6.6, 6.7; the session note |

Raised by C1b's drafter and settled here: with `--roads-record`, the training check drives only share roads, so section 9 runs the gate with the share off and `check_roads.py` both ways (row 130 (5)).

**C1b's draft against this sheet.** The draft was revised while this round was applied: C0 now fixes the two fixtures in its own commit, and C1b forwards `RECIPE29_TIMED`, words the caption conditionally, names the record by `record_name`, splits `default_table` by the share, and gives B1 `PYB=<row 135's interpreter>` and B0's `$B1OUT`. This sheet follows those names. Round 3's review (below) confirmed what C1b's runbook still lacks; the full list is after the round-3 table.

### Round 3: the check of this sheet (s), and the review of C0's and C1b's drafts (v)

Row 136 was answered after this round ran. Six of its findings are moot under it, and one in part; the column says which.

| # | severity | finding | applied in, or moot |
|---|---|---|---|
| s1 | material | the table builder and the S1/S2a gate script land in TC, after P and so after Run 2's labels | moot under row 136: no table builder, gate script or table design exists |
| s2 | material | the contract's second table remedy (the baseline car on the exact cycle) needs a PLANT_CODE hook no commit before B1 owns | moot under row 136: no remedy, so no remedy-2 hook in P (6.1) |
| s3 | material | the Honda's gate before the first arming reacts to one number of the many check lines its command prints | 0 (S), 0.1 (2c), 4 (the repeat), 14 (S, C2); rows 135 (8), 137 (6); ORDER step 12a |
| s4 | minor | on CUDA under a table, a remedied table's fallback after the preregistration fails the Preregistration check | moot under row 136: no table rate, and B1's series are all read before Tb and PR |
| s5 | minor | a P re-made after B1's git_head changes PLANT_CODE in the cost-file window, and no row repeats B1 | 1.5, 2, 10.1 (series reading, `cost_files`), 12.5 (`superseded`), 12.8, 14 (B1); row 140 (5); row 135 (4)(c) points to it; ORDER step 18 |
| s6 | minor | after a re-run's rows exist, a stale summary.json lets `trainable()` read the first entry | 6.3 (`unlisted_reruns`), 6.7 (StaleSummary, with its control); row 139 (1) |
| s7 | minor | ORDER line citations point at lines O1 itself moves; section 7 misquotes the disclosure | header, 1.3, 7, 9, 11, 14 (P), 15 (5): steps by number; rows 138 (5), 143 (1)'s Why; row 135; the session note's convention 1b |
| s8 | minor | S1 is placed on the practice episodes, where the contract draws it from training roads | moot under row 136: no S1 |
| s9 | minor | nothing fixes the S2b pilots' seeds or folders | moot under row 136: no S2b pilot |
| s10 | minor | the commit order of TC against V, and of G against Qa, is stated two ways | TC's part moot under row 136; G after Qa in 0, 7, 14 (G) and ORDER step 15; 2 lists every file's edits in section 0's order (`test_device_gate.py`: C1b, P, Qa) |
| s11 | minor | ORDER's new "Next" sentence leaves out C0 | ORDER_steps section 1 |
| s12 | minor | the runbook's table-rate loop B1t has no test and no owner | moot under row 136: no B1t |
| v1 | material | C1b's runbook: B0 checks out "the pushed commit after P", and installs nothing on CUDA | 3 (B0); the list below, item 1 |
| v2 | material | C1b's runbook: B0 writes no B0 record, and B5 does not copy one | 3 (B0, B5, RunbookB1); the list below, item 2 |
| v3 | material | C1b's runbook never runs the CPU series on CUDA | 3 (B1, B5, RunbookB1); the list below, item 3 |
| v4 | minor | C1b's B5 says every attempt must be clean | 3 (B5's sentence); the list below, item 4 |
| v5 | minor | C0's message records neither `verify_docs` nor ORDER:5's two checks at C0 | 14 (C0); the list below, item 6 |
| v6 | minor | C1b's message records no run of `test_reward.py` and `check_roads.py` at the B58 defaults | 14 (C1b); the list below, item 7 |
| v7 | minor | both draft commits carry the placeholder identity `draft <draft@local>`; C1b's subject says "(DRAFT)" | 14 (C0 and C1b); the list below, item 8 |

Also from round 3, the C0/C1b drafter's open points: `verify_docs.py`'s child leaves a `__pycache__/` (rule 1.10); C1b moves `benchmark_training.py`'s and `engine_gate.py`'s lines again, so they are cited by name (the header; the session note); and on CUDA `<row 135's interpreter>` has a value only once CU exists (section 3, CUDA). The reviewer's note that `results/training_roads.json`, committed at `cbb8d09`, differs from what `91c6ece` and C1b regenerate is older than C1b and is not C1b's; it is recorded in the session report, and no commit here edits that file.

**Before their commits, C0 and C1b take** (C0 drafted at `e7259ae` and committed as `fefb7af`; C1b drafted at `dee0d9a`, then `4a77e38`, and final at `d9a96fa`, in a scratch clone, not pushed; round 4 below says which items each has taken):
1. B0 checks out the pushed commit holding V, Q, CU (if any) and Ta (ORDER step 18), where the draft keeps "the pushed commit after P" (Part B's header, B0's checkout, and the B1 bullets that name "the commit after P" and "row 118's CUDA commit"); on CUDA it installs the CU lock's environment first, and runs its VERSIONS check with that environment's python.
2. B0 writes `$B1OUT/B0_<git_head>.json` (`code_info()` and the host), refusing an existing file, and B5 copies every `$B1OUT/B0_*.json` with the attempts, for `classify` (b). The line that says nothing but B1's attempts is written in `$B1OUT` reads "B1's attempts and B0's records".
3. On CUDA, the CPU series: the same block with `PYB=$PY`, `--device cpu`, the CPU's N and the names `B1_bench_$E.cpu.attempt$k`, always, at the same visit, with its own k loop and the same crash-repeat rule.
4. B5's sentence on what T checks is reworded as section 3 gives it: only the last attempt of a series must be clean.
5. The dormant `--table-record` is removed from `benchmark_training.py`, with every trace of it, and from `test_device_gate.Cli` (section 3; row 136).
6. C0's message carries the printed lines of `verify_docs` and ORDER:5's two checks, run at C0.
7. C1b's message carries `test_reward.py` and `check_roads.py` at the B58 defaults, identical to the same runs at `91c6ece`.
8. Both are re-committed with the repository's identity, and C1b's subject loses "(DRAFT)".
9. The runbook cites CU as ORDER step 17a and Ta as ORDER step 17b, as section 0 and ORDER number them since row 136 removed TC (round 4's review of `4a77e38`: B0's CUDA line, B0's commit bullet and "What is not here" still give CU as step 17b, and the commit bullet gives Ta as step 17c, the numbering from before row 136).

RunbookB1 follows 1-3 (section 3). The committer runs `verify_docs` (rule 1.10) and ORDER:5's two checks in the repository, with the session report and CHECKPOINT.

### Round 4: the check of this sheet and the rows (w), and Ghassan's confirmation

One check of this sheet and the rows, on the version that applied row 136. It found no blocking defect, 1 material and 8 minor. The material one needed Ghassan's word, since row 136 is recorded as his answer; he confirmed on 2 November, "Test doesn't run, reported (Recommended)" (section O's note quotes the question and his text).

| # | severity | finding | applied in |
|---|---|---|---|
| w1 | material | row 136 (1) ends the order of leaving with the B58 alone, against Ghassan's "B58 + Ford is the minimum", and nothing says what follows when no EPA engine is left | Ghassan's confirmation (section O's note); row 136 (1), (2), (3), its Why, other options, Disclosed and To implement; 0 (Tb, PR, the order), 10.1 (`apply_rule`, ApplyRule, Preregistration), 10.2, 11, 12.5 (`n`, `notes`), 14 (Ta, PR), 15 (10); ORDER_steps' preamble, section 1's status clause, steps 17b, 19 and 20 |
| w2 | minor | the SYNTHETIC Honda command's blind-arm line at H = 30 s gives a result before P; it does not read NOT RUN | 4 (the repeat); rows 137 (6), 135 (8) |
| w3 | minor | `validate_epa.DROP_ORDER` cited at :164-166 (the tuple is :165-167); row 136 (2) puts P6 inside MD:1460-1540 (it is MD:1580-1581) | 10.1; row 136 (2), (3); the session note |
| w4 | minor | the version-5 disclosure says the Ford "would have ... trained on a validated table", an outcome version 5 does not give | 11; row 136 (4) and its Disclosed; ORDER step 20 |
| w5 | minor | a schedule drop's reason is defined twice, in 10.1 and 12.5 | 12.5 (the one definition), 10.1 (`apply_rule` cites it) |
| w6 | minor | engine_gate's WHAT WAITS H, knock and decision-34 roads bullets become false at P and Qa, and no commit owns their edit | 2, 6.6 (P: the H and knock bullets), 9 (Qa: the decision-34 roads bullet) |
| w7 | minor | the runbook's B0, B1 and B5 file names and Ta's constants are written twice, with no test tying them | 10.1 (RunbookNames, with its control), 14 (Ta); ORDER step 17b |
| w8 | minor | the critical path leaves out Qa, which sits between P and G | 0.2 (33.5 h; 60.5-70.5 h with PR and the pilot) |
| w9 | minor | row 136 (2) names the never-written code TC, TD and B1t, which the sheet never defines | row 136 (2), by what each is; 10's opening line |

**C1b's final draft, `4a77e38`** (round 4's review of it; a scratch clone on C0 `e7259ae`, not pushed). It is committed as badcloor, without "(DRAFT)", and takes items 1-5 and 7 of the list above, and item 8 for C1b. Items 6 and 8 for C0 are closed: C0 landed as `fefb7af`, as badcloor, its message carrying verify_docs and ORDER:5's two checks. Item 9 (CU 17a, Ta 17b) is taken in C1b's final draft, `d9a96fa`, with round 4's other C1b findings (PYC set in every session; the four-engine wording of `validity()` and `backend_line()`). The review's other runbook findings are C1b's to settle before its commit; this sheet changes nothing for them.

## 17. Rows 146-147: the B58 study across H (6 November 2026)

*Written by the AI agents on 6 November 2026 with rows 146 and 147 of `results/VALIDATION_DECISIONS.md`
(section R), after R4 (`34cca5b`) and before ORDER step 13. Run 2 dropped all three EPA engines (section
Q), so the four-engine test does not run and the B58 study of row 107 (2) follows. This section lists
every change those two rows make to this sheet, and, under "Words replaced", the sentences beside it that
they replace. **Where rows 146-147 and this sheet differ, the rows govern** (this sheet's "How it
binds"); where this section and an earlier section differ, this section governs for the B58 study.
Everything not named here stands as written.*

**0. The commits, in order.** R4 is done (`34cca5b`, pushed). Then: D146 (rows 146-147, section R, the
statements, ORDER's rows 12a-22, this section, the README's Run 2 section, the limitation, CHECKPOINT,
the session report, `results/B58H_DESIGN/`); step 13 (no commit unless its test fails); RV; P; Qa; G; V;
Q; Ta; B1 (committed and pushed on Jad's PC; the laptop then runs `git pull --ff-only`); Tb; AB (step
19a, new: the study's analysis code); PR-B (`results/PREREGISTRATION_B58H.md`, whose own commit is `T*`,
the commit the pilot and the training run from); PL-B (trained on Jad's PC from `T*`, scored and committed
on the laptop). C2, RS and CU are not made. PR (`results/PREREGISTRATION_4E.md`) is never written.
Section 0's "It stops at Tb when Tb's record holds n null" (`INTERFACES.md:42`) holds for the four-engine
test; for this study the order goes on past Tb, as listed here. The order's rule ("Commits that edit the
same file land in this table's order") is unchanged.

**0.1 The drafting order.** C2's drafts (2c, 4a) are dropped. P's golden digests are measured on step
13's tree, not on C2's.

**0.2 Times** (row 146 (7); MEASURED: R4's 25 312 s, the rest ASSUMED; `results/B58H_DESIGN/budget.txt`,
printed by `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -I -B results/B58H_DESIGN/budget.py.txt`
from the repository root):

| part | time |
|---|---|
| step 13 | about 1 h |
| RV | about 10.5 h: 3.5 h plus R4's 7.0 h, since RV's sections include every reading of redraws.json (row 140 (1); section 5's `redraws.<reading name>`); its control about 9.2 h of it (2.2 h plus R4's 7.0 h) |
| P | about 20 h once drafted: the full roads check about 10.7 + 7.0 = 17.7 h |
| Qa | 0.5-1 h |
| G | about 3 h, with Q's runs (the B58 only) beside G and V |
| V | about 3 h, plus its after-run of X1's two checkers (8 below; `conditions_test.py` about 2.5 h on 18 workers by its docstring, ASSUMED; `logged_check.py` UNKNOWN), not in the total |
| Ta | 0.5-1 h |
| B1 | 3-5 h on Jad's PC |
| Tb | about 1.5 h |
| AB | 0.5-1 h |
| PR-B | 1-2 h if drafted during the steps before it; up to 16 h from scratch (row 134) |
| PL-B | one wave of 10 runs, 14.13 h at step 3's rate (450 000 / (106.19/12) s), plus 1-2 h of transfer and reading; row 112's 21 h was the laptop's rate |
| training | 5 waves, 70.63 h; latest start ending inside W 17 November 01:22 AST (16 November 15:22 AST with the primary scoring inside W) |

The machine time from R4's commit to "ready for training" is 60.8-81.4 h. Not in it, each UNKNOWN: the
agents' drafting time, Jad's availability, V's after-run of X1's two checkers and the descriptive rows'
scoring (row 147 (11)).

**1. Rules.** Rule 1.11 stands: row 146 (4) maps every foreseeable outcome of the study's route to the
consequence already written, and any other outcome stops the step and is reported. Its heading, "Nothing
waits for a row written after Run 2" (`INTERFACES.md:116`), is read for the outcomes of steps: rows
146-147 are the design row that Q.5 (VD:622) and row 107 (2) call for, written before anything of the
study trains, and they settle no step's outcome, so step 13's waiting for D146 does not breach it (row
146 (9)). Rule 1.5's window is closed at `T*` for this study: PR-B's gate runs `epa_backend.py check` and
`git diff --quiet <B1's git_head> <T*> -- <the paths of epa_backend.cost_files>` (row 146 (6)). Rule
1.4's two checks end with R4's commit (ORDER:5's freeze of the hashed files); its rule on the laptop's
venv and Windows continues until the study's last scoring (row 143 (2); row 146 (8)). Rule 1.10: every
`__pycache__` folder is deleted before RV's and P's roads checks.

**2. Who edits which file.** Void: C2's lines (`step_record.py`; `train.py`'s recorder; the docstring
at `four_engine_roads.py:124-127`; `engine_gate.py`'s WHAT WAITS Accord bullet; `test_cars.StepRecord`);
RS's (`rescore_rows.py` and its test); V's `tit_cap_rescore.py`, `test_tit_cap_rescore.py` and the
declared sensitivity route (`check_declared`, `Variant`, `score_declared`; row 147 (10)). Added: V writes
the readers of the descriptive rows for schema-4 agents in a new module, `b58h_descriptive.py`, with
`test_b58h_descriptive.py`, and adds a declared transfer route in `evaluate.py` (row 147 (11)); V edits
neither `logged_check.py` nor `conditions_test.py` (P's edit of `conditions_test.py:374`, in section 2's
"every other `plant_fingerprint` caller" row, stands); G registers Run 2's figures with `verify_docs.py`
(7 below); AB writes `b58h_analysis.py` and `test_b58h_analysis.py` (row 147 (12)); Ta adds
`test_epa_backend.PreregistrationB58H` (row 146 (5)); B1 writes `results/benchmarks/B1_device/` and
`results/B58_IDENTITY/L8_device/` (row 146 (6)).

**3. The runbook.** Part B's header (`DEVICE_RUNBOOK.md:166-168`) reads "with C1 and C1b in its history"
(its "and C2" replaced). Every session of B1, of PL-B and of the training runs the runbook's "Before you
start" block (`DEVICE_RUNBOOK.md:14-22`) first, with a new `OUT`, since B1's loop
(`DEVICE_RUNBOOK.md:250-259`) uses paths relative to `$REPO`. The placeholders are device `cpu`, N 12,
S 3000, R 2, `PYB=$PY`, `B1OUT=~/grad_device/B1`; the loop runs `b58` alone, and there is no CUDA series.
B4 (`DEVICE_RUNBOOK.md:367-376`) runs and is recorded, and for this study it decides nothing: it re-makes
only the frozen dumps of the calibrated EPA plants, all three dropped, and the B58's identity on the
device is covered by L8 and B2 (its "It must pass", `:375`, is among the words replaced). B5's open
question is settled: L8's record goes to `results/B58_IDENTITY/L8_device/`, a record of its own beside the
certificate, never an edit of `results/B58_IDENTITY.md`; `B2_identity_device.json`, `B2_compare.txt` and
`B4_test_epa_plants.txt` go to `results/benchmarks/B1_device/`. B1 is committed on Jad's PC from the
detached HEAD B0's checkout leaves at Ta, in `$REPO`:

```bash
git add results/benchmarks/B1_bench_b58.attempt*.json results/benchmarks/B1_bench_b58.attempt*.txt \
        results/benchmarks/B0_*.json results/benchmarks/B1_device/ results/B58_IDENTITY/L8_device/
git status --porcelain            # those paths, and nothing else
git commit -m "build step 2, ORDER step 18 (B1): the B58's benchmark on Jad's PC, with B2, B4 and L8"
git push origin HEAD:GRA-test
```

Nothing is pushed from the laptop between Ta's push and B1's, and the laptop takes B1 with
`git pull --ff-only` before Tb. For PL-B and the training, Jad checks out `T*` (`git -C "$REPO" fetch &&
git -C "$REPO" checkout <T*>`), checks that `git status --porcelain` prints nothing and that
`git -C "$REPO" log --diff-filter=A --format=%H -- results/PREREGISTRATION_B58H.md` prints `T*`. After
the pilot he returns `runs/b58h_pilot_dt1` and its logs zipped with SHA256SUMS; the practice route scores
them on the laptop (row 143 (1)), and PL-B is committed from the laptop. After training he returns the
run folders and their logs the same way.

**4. C2.** Not built (row 146 (3)).

**5. RV.** Unchanged, but it follows step 13, not C2: row 140 (3)'s "after C2 and step 13", and the same
words in row 140's To-implement (VD:535), read "after step 13". Its control and its check include both
readings of redraws.json (0.2's times).

**6.1.** The cam-aware surrogate path is not built: row 94's "and the cam-aware surrogate path, off at
its defaults, whether or not a table is later built" and row 136 (3)'s "Row 94's cam-aware surrogate path
stays in P, off at its defaults, as row 94 fixes it" are replaced by row 146 (9). The CvtVehicle
docstring at `engine_env.py:777-778` stays as it is, since C2 is not built.

**6.7.** "Pinned from C2's tree, with the control re-run there before P's edits; both commits are
recorded" reads: pinned on step 13's tree (D146's, since step 13 waits for D146), with the control re-run
there before P's edits; both commits are recorded. `test_step_record` is not written and leaves P's list
(6.7, 14).

**6.9.** Not built: row 135 (5) measured the blinded arm bit for bit at every H.

**7. G.** Besides section 7's contents, G registers Run 2's figures in `results/README.md` (its Run 2
section, from D146) with `verify_docs.py`, so that they are recomputed from the committed records and
checked like every published figure (the science review's M1 of rows 146-147, which D146, a documents-only
commit, assigns here; section R's note), and runs `drift_test.py`, since the guard is touched (CLAUDE.md
mistake 11). G keeps its place before B1 (row 146 (3)).

**8. V.** Without `tit_cap_rescore`, `test_tit_cap_rescore` and the declared sensitivity route (row 147
(10)). With: the transfer route in `evaluate.py`, and the descriptive rows' readers in
`b58h_descriptive.py` (the averaged policy, H and the arm from each agent's meta.json through
`evaluate.arm_of`, this sheet's section 8), each with a control that fails (row 147 (11)); each arm's
fuel, the baseline ECU's fuel and the share of demand steps short of the tracking tolerance, per road, in
the scores' provenance (12.7), which `four_engine_analysis` copies untouched (row 147 (5)). Its
`train_backend` is read from Tb's record, where `engines.b58.backend` is 'cycle' beside n null. V's gate
compares with `tools/l7_diff.py`, inside `results/B58_IDENTITY/certificate_tools.tar.gz`, extracted
outside the repository. V's gate adds a run of `logged_check.py --set /c/Users/badcl/Desktop/GRAD-project/runs/extremes_dt1` and
`conditions_test.py --set /c/Users/badcl/Desktop/GRAD-project/runs/extremes_dt1 --resume-all` on G's tree before and on V's after
(the laptop's set by its absolute path: `runs/` is in no clone, and both scripts keep an absolute path,
`logged_check.py:252-253`, `conditions_test.py:209-211`), each in a scratch clone outside the repository
with `results/logged_check_extremes_dt1.json` and `results/conditions_extremes_dt1/` removed from the clone,
so that every part is recomputed. Each run first finds the set's agents, as many as the set holds; then
the JSON outputs are compared field by field and the records by their arrays, never their bytes, leaving
out only the records' `commit` (`conditions_test.py:190-196`) and logged_check's elapsed minutes
(`logged_check.py:290-293`). A refusal counts only when both trees print it after the agents were found. X1's and
X2's published results, `make_page.py:1383`'s anchor in `conditions_test.py` and `record_extracts.py:55`'s
import of it rest on those two files, which V leaves as they are.

**8, RS.** Not built (row 147 (10)).

**9. Q.** The B58 only: row 119's gate is "Before any agent of an EPA engine trains", and none trains.
Two commands, each with `--reward-knock out`: `test_reward.py --engine b58 --train-road four_engine
--roads results/EPA_ROADS/roads.json`, which prints the band and notch sweep, the blind-arm check at each
H of the record's H_table (`engine_gate.horizons`, never typed) and each road's share below the torque
floor (`engine_gate.run_gate`, `engine_gate.py:509-528`, `:410`, `:347-369`); and `check_roads.py` with
the same options, share off, then with `--roads-record results/EPA_ROADS/roads.json`, share on. Its
outputs go to `results/ENGINE_GATES/b58/`. "On every engine" (ORDER step 17, this section) reads "on the
B58".

**10.1.** Unchanged (n null, in_test ['b58']). `Preregistration` keeps requiring
`results/PREREGISTRATION_4E.md` to be absent. Added, `PreregistrationB58H` (row 146 (5)): unguarded,
skipped until `results/PREREGISTRATION_B58H.md` is committed, a failure if skipped after; every
`train_all.py` line carries this section's flag list (`--jobs` = PROTOCOL's runs, `--device` = PROTOCOL's
device, `--road four_engine`, `--dt 1`, `--third-arm`, `--recipe29`, `--roads-record
PROTOCOL['roads_record']`, `--reward-knock out`, `--steps 450000`, `--no-resume`, never `--blind-per-h`)
and `--engine b58`; the training line `--seeds 0-19 --out runs/b58h_dt1`, with no `--ratios`; the pilot
line `--seeds 2000-2004 --ratios 1.5 --out runs/b58h_pilot_dt1`. Each line runs through
`train_all.main()` in-process, with `sys.argv` patched to the line's arguments and `train_all.commands`
replaced by a stub that raises a sentinel, so that `main()` runs its own `parse_args`, `seeds()` and
`check_four_engine` and stops before any directory or run exists (`train_all.py:271-280`); the sentinel
carries the parsed arguments and the record `check_four_engine` returned, and the test checks them.
`train_all.py` is not edited for it. The control, one flag changed, fails.

**10.2.** "ORDER steps 20-22 do not run, and `four_engine_analysis` is not run" holds for the four-engine
test. For the B58 study, `four_engine_analysis` runs on its scores with the context AB assembles; the
context's "`seeds_per_arm = record['n']`" (`INTERFACES.md:972`) reads 20 (row 147 (4)), and
`engines_in_test` is ['b58']. Run 2's drops leave `apply_rule` no schedule drop (`INTERFACES.md:957`), so
Tb writes no drop line, and its session report gives the failed validations as the result (MD:1611-1612),
not a failed schedule: `INTERFACES.md:973`'s "with the drop lines (the last EPA engine's among them)" and
"The session report gives the failed schedule as the result" read so. `validate_context` requires the
recorded status to equal row 103 (4)'s rule (`four_engine_analysis.py:425-429`), so the context may read
'confirmatory' while the analysis prints exploratory with one engine (`:668-669`); the report's first
line, "FOUR-ENGINE TEST (row 113)" (`:860`), is the committed script's fixed header (row 147 (12)). The
context's model band is computed by AB's code after scoring, per ratio and reading, from the d the
analysis reads and both arms' realised median cuts (`four_engine_analysis.py:44-56`; MD:1569-1586).

**11. PR → PR-B.** File `results/PREREGISTRATION_B58H.md`. `T*` is its own commit, the one that adds it,
found by `git log --diff-filter=A --format=%H -- results/PREREGISTRATION_B58H.md` (X1's precedent,
`results/PREREGISTRATION_X1.md:355`); AB's commit is its parent, and `git diff --stat <AB> <T*>` lists
that file, the session report and CHECKPOINT (rule 1.10), none in `epa_backend.cost_files` or a hashed module. Folders: `runs/b58h_dt1` (training) and `runs/b58h_pilot_dt1` (the pilot), in place of
`runs/four_engine_dt1_<engine>` and of `INTERFACES.md:980`'s "The pilot uses seeds 2000-2004 in
`runs/four_engine_pilot_dt1_b58`". Neither is in `train.CLOSED`. The commands are row 147 (3)'s; the
crash rule is X1's. PR-B copies rows 146 and 147 and adds no choice.

**12.7.** The scores keep `four-engine-scores/1` (arms blind, sighted_r0.5, sighted_r1.5); the delivery
figures ride in its provenance.

**13. Values read, never typed.** H 23.667534571895 s and 71.002603715685 s (roads.json `H_table.b58`);
C(0.5) 1.8191 and C(1.5) 5.2319 (roads.json `ceilings.per_engine.b58.by[r].C`); E8's κ 3.4226
(`results/EPA_TIGHTENINGS.json`, `E8.b58_u_val_kappa.with_roads.kappa`, Q.2); the companion's κ 1.7168
and 3.7328 (summary.json, each engine's `kappa.L1`); s* from `four_engine_analysis.status_star`.

**14. Gates.** P without `test_step_record`. G with `verify_docs.py` checking Run 2's figures, and
`drift_test.py`. V without `test_tit_cap_rescore` and `test_step_record`, with `test_scoring_protocol`'s
transfer-route test, `test_b58h_descriptive` and the before/after run of X1's two checkers (8). Ta with
`PreregistrationB58H`. AB: `test_b58h_analysis`, `test_four_engine_analysis`, `test_engine_threading`
(alone), `verify_docs`. PR-B: on its staged tree, `epa_backend.py check` and `git diff --cached --quiet <B1's
git_head> -- <the paths of epa_backend.cost_files>`; at `T*`, the same two, `git diff --stat <AB> <T*>`,
`verify_docs`, `Preregistration` (4E absent), `PreregistrationB58H`; push.

**Words replaced** beside this sheet (row 146 (9) lists them all): `DEVICE_RUNBOOK.md:166-168`'s "and
C2"; B4's "It must pass" (`DEVICE_RUNBOOK.md:375`) and ORDER step 18's `test_epa_plants` gate
(`ORDER_TO_TRAINING.md:33` at `34cca5b`), read as recorded only for this study; ORDER step 19's "then the
drop lines" and "A person records any drop" (`ORDER_TO_TRAINING.md:34` at `34cca5b`); and, in this sheet,
`INTERFACES.md:42`, `:116`'s heading, `:972`, `:973` and `:980`, read as 0, 1, 10.2 and 11 above say.

**Citations corrected** (from the route plan): the WMI check is `docs/build_step_2/RUN2_CHECKLIST.md:65-68`;
`epa_roads.py`'s exit codes 2 and 3 are at `:2088-2094`; the runbook's B1 loop is
`DEVICE_RUNBOOK.md:250-259`, and Part B ends at its line 395 (`:397-404` is "What is not here");
`l7_diff.py` and `make_meta.py` are `tools/l7_diff.py` and `tools/make_meta.py` inside
`results/B58_IDENTITY/certificate_tools.tar.gz`.

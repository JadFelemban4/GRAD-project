# Trial build of the proposed merge resolution -- 30 September 2026

Merge under test: Jad `JMF-2340550-sep17` (HEAD 086c519) + Ghassan `origin/JMF-2340550` (74de99a),
merge base f6b46e9, in progress in "To main" (15 conflicted files). Nothing in "To main",
"GRAD-project" or `$SP/trees` was modified (read-only git only). Every figure below is from a
run in this session; logs are in `$SP/work/trial/logs/` (one `.log` per check, `summary.txt`
has exit code and wall time of each).

## 1. The build

`$SP/work/trial/merged` = the working tree of "To main" (tar, `.git` excluded; To main had no
ignored or untracked files), then resolved. It was later made a throw-away git repo with one
commit (`git init`, `git add -A`), because three checks need `git`: `verify_docs.py`
(`git ls-files`), `drift_test.py` (`git ls-files`), and `app/test_agents.py`
(`git check-ignore`, `git status`). 454 tracked files -- identical to the union of the two
branch trees (250 + 271, 67 shared), apart from the one move in 3a.

### How each conflicted file was resolved

| file | resolution used | note |
|---|---|---|
| thermal.py | Ghassan's side of the hunk | byte-identical (CRLF aside) to `:3:thermal.py` -- Jad changed nothing else in the file |
| engine_env.py | Ghassan's side of both hunks, HUNK-LEVEL | `:3:engine_env.py` would also drop Jad's auto-merged comments and docstrings (the dt / PI-loop comment block, the gearbox docstring). The code is identical either way; plant_sha is the same |
| evaluate.py | `$SP/work/conflict-evaluate/proposed/evaluate.py` | |
| train.py | `$SP/work/conflict-train/m/train_merged.py` | |
| test_reward.py | `$SP/work/conflict-test_reward/test_reward.PROPOSED.py` | |
| generality_test.py | hunk 1 Ghassan (`vals.append(info["mdot_exh"])`), hunk 2 Jad (refuse with SystemExit when no exhaust samples, then `np.mean`) | Ghassan's engine_env emits `mdot_exh` = air + fuel, which is what the merged thermal network is handed; Jad's `fuel x 15` is no longer what the turbine node sees. Jad's guard is kept because Ghassan's bare `np.mean([])` gives nan, not an error. A dead `prev = env.ep["fuel"]` line stays, and Jad's docstring above it ("WHY NOT ADD THE KEY TO info INSTEAD") now contradicts the code -- a docstring to rewrite |
| .gitignore | union: Jad's `app/node_modules/`, `app/static/vendor/`, `.env`, `.env.*`, `*typesafe_key*` + Ghassan's `results/agents/**/train_record.npz`, `eval_record.npz` | |
| verify_docs.py | asked: Jad's side. **That crashes** (see 4a-1). Trial used a union: `$SP/work/trial/verify_docs.UNION2.py` (patch against Jad's side: `$SP/work/trial/verify_docs.union.patch`) | |
| CLAUDE.md, README.md, REFERENCES.md, CHECKPOINT.md, handoff.md, validation_table.md, presentation/index.html | Jad's side of every hunk, HUNK-LEVEL | `git show :2:<file>` would also throw away Ghassan's non-conflicting edits in the same files (253 lines in CLAUDE.md, 193 in REFERENCES.md, ...), and for verify_docs.py it would drop Ghassan's drive-B expectations (11 drives, 321.7 min, 568 pinned) and `_file_is_retired`. Hunk-level is what a real merge commit would contain |

No file in `merged/` carries a line starting `<<<<<<<` or `>>>>>>>` (grep over the whole tree).

### Extra edits, each measured WITHOUT first

a. `results/phase_d_seed0_110kmh.txt` -> `results/void/`. Without the move,
`analyse_phase_d.py` reads 9 files through its `results/phase_d_seed*.txt` glob and prints
**6 of 9, mean +4.9, sign p 0.2539, permutation p 0.4902**, with "seed 0" listed twice
(+30.5 and +15.7 over current-grade). After the move: **5 of 8, +4.8, 0.3633, 0.4922** --
the preregistered figures. `analyse_phase_d2.py`'s Phase D column moves the same way (6 of 9
-> 5 of 8; its below-MEI line 5 of 9 p 0.5000 -> 4 of 8 p 0.6367); its D2 result is
unaffected (4 of 8, +6.4, 0.6367, 0.4688 both times). NEEDED. (Side note: the file is named
110kmh but its header line reads "scenario: 12 % at 130 km/h".)
Also add a line for it to `results/void/README.md`, which says why each file there is void.

b. `app/agent_trace.py` `run_lanes` must return `damage_thermal`. Without it,
`app.test_agents` fails `ProofTests.test_tracer_equals_run_episode`:
`AssertionError: Lists differ: [{'re[52 chars]45, 'fuel': 5269.298190766288, ... != [{'re[52 chars]45, 'damage_thermal': 1977.6647608036885, ...`
The edit (patch `$SP/work/trial/agent_trace.patch`): import `damage_rate` from engine_env,
start each lane with `"thermal": 0.0`, add
`s["thermal"] += damage_rate(info["t_turb"], info["t_oil"]) * env.dt` after the peak update
(the same expression and order as `evaluate.run_episode`), and put
`damage_thermal=s["thermal"]` in the returned dict. **It needs a second line:**
`RESULT_KEYS` in `app/test_agents.py:199` must gain `"damage_thermal"` -- measured: with the
agent_trace edit alone, `TraceTests.test_lane_stops_on_divergence` fails
`AssertionError: Items in the first set but not the second: 'damage_thermal'`
(patch `$SP/work/trial/test_agents.patch`). With both: 129 tests OK, 14 skipped.

## 2. Results

| check | exit | time | result |
|---|---|---|---|
| `import random_road` | 0 | <1 s | ok |
| `random_road.py` self-test | 0 | <1 s | SELF-TEST PASSES, road_sha 1a29dc46db24f233, EPISODES_D2 regenerates |
| `analyse_phase_d.py` | 0 | <1 s | 5 of 8, +4.8, sign 0.3633, perm 0.4922 (after 3a) -- preregistered figures |
| `analyse_phase_d2.py` | 0 | <1 s | D2 4 of 8, +6.4, sign 0.6367, perm 0.4688, INCONCLUSIVE -- preregistered figures |
| `analyse_c4.py` (bonus) | 0 | <1 s | 3 of 8, +30.2, below-MEI sign 0.0352 / perm 0.3867, NOT-CONVERGED; identical to `results/C4_RESULT.txt` except one added note that the 16 zips are absent (certified from the recorded evaluation) |
| `validate.py` | 0 | 16 s | 8 of 11 inside band (literature 6 of 7, our car 2 of 4); OUTSIDE: EGT cruise max 787.7 (600-750), oil sustained 97.0 (103-111), oil tau 60.0 (70-100) |
| `test_reward.py` | 0 | 322 s | all 8 checks PASS, "The reward is safe to train against". Neutral -0.00028; starver -0.13265 (97 % from the 0-20 s launch); training-road starver -2.32655; worst training road -0.00047 |
| `check_premise.py` | 0 | 195 s | baseline 920.1 damage, peak 883 C; preview over current grade -0.3 -- the expected Ghassan-physics figures. Rewrote `results/premise.json` byte-identically |
| `python -m app.test_simulation` | 1, then 0 | 2 s | without `app/static/vendor/`: 14 of 15, FAIL `import map points at missing vendor/three/three.module.js`. With the vendor folder copied from GRAD-project's working tree: 15 of 15 |
| `python -m app.test_replay` | 0 | 270 s | 49 of 49. Pins it carries are Ghassan's: pull01 peak 604.8 C, 0 thermal |
| `python -m app.test_replay --full` | 0 | 185 s | 59 of 59. 7475b5d7 peak 873.1 C, 14 thermal alerts (pins match) |
| `python -m unittest app.test_agents` | 0 | 167 s | 129 run, OK, 14 skipped (all need runs/, runs_d2/, runs_c4/, runs_sixspeed_18sep/ or --full) |
| `node --test app/static/sim/` | 1 | <1 s | `Cannot find module '...app\static\sim'` -- Node 24 does not take a directory (CHECKPOINT.md:1976 already says so) |
| `cd app && node --test "static/sim/*.test.mjs"` (app/package.json's form) | 0 | 4 s | 148 tests, 140 pass, 0 fail, 8 skipped |
| `check_roads.py` | 0 | 328 s | PASS: 40 roads, 14 past 850 C, worst neutral -0.0020 (seed 134), worst p95 0.016 (seed 113). Rewrote `results/training_roads.json` byte-identically |
| `generality_test.py` (checks the union in 1) | 0 | 763 s | runs; tau axis 121.3 g/s; rewrote `results/generality.json` byte-identically to Ghassan's committed file |
| `train.py --help`, `import evaluate, train`, `evaluate.py --help` | 0 | 1 s | all load |
| `fingerprint.py` | 0 | <1 s | plant_sha **c236a8db3e201090** (= Ghassan's tree; Jad's is b5a3069f32a83754, base aade4a59e9647b93), episodes_sha 05a598a574268b20 (unchanged) |
| `verify_docs.py`, Jad's side as instructed | 1 | 21 s | CRASH: `NameError: name 'check_derived' is not defined` |
| `verify_docs.py`, union (UNION2) | 1 | 60-116 s | **7 of 73 checks failed**; 125 document-vs-data WRONG mentions; 50 live retired-figure mentions in 16 files |
| `drift_test.py` | 1 | 69 s | CRASH in the reader thread: `UnicodeDecodeError: 'charmap' codec can't decode byte 0x81`, then `TypeError: unsupported operand type(s) for +: 'NoneType' and 'str'` (drift_test.py:116) |
| `drift_test.py` under PYTHONUTF8=1 (on verify_docs UNION) | 0 | 898 s | **16 of 16 CAUGHT -- but VACUOUS**: the baseline run already fails, and the reason drift_test prints (the first WRONG line) is the pre-existing `check_premise baseline damage 920.1 vs 959.8` for rows 1, 2, 4-8 and 11-14; row 9's reason is blank. Only rows 3 (DTHETA_DEG), 10 (TURB_PROTECT_K), 15 (EPISODES hash) and 16 (gears) name their own drift. The guard cannot be tested until verify_docs is green on the merged tree |

Control runs on plain copies of the unmerged branches (git-initialised, in `$SP/work/trial/jadcopy`,
`ghcopy`): `verify_docs.py` on Jad's branch **All 67 checks pass (846 figure mentions)**; on
Ghassan's **All 44 checks pass (348 mentions)**; `drift_test.py 1 2` on Jad's branch 2 of 2
CAUGHT, no crash; `app.test_simulation` on Jad's branch without vendor: the same 1 failure.

Skipped (need the gitignored trained agents): `evaluate.py <models>`, `check_c4_convergence.py`,
`check_c4_start.py`, `check_d2_tracking.py`, `record_agents.py`, and the 14 agent-bound
unittest cases above.

## 3. verify_docs on the merged tree: what fails

Of the 7 failed checks, 5 are `check_scenario` pins (Jad's `THE EXPERIMENT'S OWN CONSTANTS`)
that were written on Jad's physics:

| pinned in verify_docs.py | merged tree gives | Jad's pin |
|---|---|---|
| check_premise baseline damage | 920.1 | 959.8 |
| check_premise baseline peak turbine | 883 C | 884 C |
| app peak 7475b5d7 | 873.1 C | 890.6 C |
| app peak pull01 | 604.8 C | 608.0 C |
| app thermal alerts on 7475b5d7 | 14 | 15 |

The other two are the document scans. DOCUMENTS vs DATA, 125 mentions, by figure:
check_premise baseline damage 959.8 (48), total minutes 295.0 vs 321.7 (26), drives in the
manifest 10 vs 11 (18), baseline peak 884 vs 883 (10), MAF pinned 547 vs 568 (4), preview
over current grade -0.4 vs -0.3 (4), app peak 890.6 (4), ceiling drives 6 vs 7 (3), thermal
alerts 15 vs 14 (3), validate rows (2, in results/page/*.html, which say "4"), drives with
samples 7 vs 8 (2), premise baseline damage (1, README.md:132 reads 4664, a fuel figure).
By file: CHECKPOINT.md 14, CLAUDE.md 13, handoff.md 12, README.md 10, results/page/index.html 8,
validation_table.md 7, figures/study/page.html 6, figures/study/index.html 6, REFERENCES.md 5,
presentation/README.md 4, compare_calibration.py 4, NEXT_SESSION_2026-09-22.md 4, then 1-2 each
in validate.py, engine_env.py, thesis/CHAPTER4_ABLATION_DRAFT.md, presentation/plan.html,
figures/agent_pairs/*, CONTROL_SCOPE.md, ABSTRACT.md, record_agents.py,
results/PREREGISTRATION*.md, results/page/template.html, and **results/phase_d_seed0..7.txt**
(1 each: their baseline row reads 959.8 -- frozen result files scored on Jad's plant).

RETIRED FIGURES, 50 mentions in 16 files: "295.0 minutes (before drive B)" 35, "every
enrichment cell within 0.027" 5, premise 951.9/671.1/624.5/628.4 3, old load residual 3,
hottest oil before 7475b5d7 2, replayed minutes before drive10 1, combustion/MAF ratio 1.
Files: presentation/index.html 11, results/page/index.html 10, CLAUDE.md 4,
validation_table.md 4, CONTROL_SCOPE.md 3, figures/study/index.html 3, figures/study/page.html 3,
ABSTRACT.md 2, handoff.md 2, presentation/plan.html 2, and 1 each in CHECKPOINT.md,
NEXT_SESSION_2026-09-22.md, README.md, figures/study/numbers.txt, plot_study_page.py,
presentation/meeting-update-2026-09-20/index.html.

The first union (`verify_docs.UNION.py`, Ghassan's SESSION_REPORT_/results/agents exemptions
in the retired scan only) gave the same 7 of 73 with 137 mentions; the extra 12 were
Ghassan's `SESSION_REPORT_2026-09-19/28/28_evening.md`. UNION2 applies those two exemptions
to Jad's `ALL` list too, because Jad's comment says the exempt set governs BOTH scans.

## 4. Failures, grouped

### (a) caused by the merge resolution

1. **verify_docs.py, Jad's side, crashes** -- `verify_docs.py:1119 check_derived(here)` ->
   `NameError: name 'check_derived' is not defined`. The call is in an auto-merged region
   (Ghassan's), the definition is in Ghassan's side of hunk 4. All six hunks are
   "both sides added" and need a union. Fix = the union in `verify_docs.UNION2.py`:
   hunk 1 Ghassan's `_file_is_retired` skip then Jad's `read_lines`; hunk 2 both RETIRED
   lists; hunk 3 Jad's comment + Ghassan's exemptions, with Ghassan's
   `RETIRED_EXEMPT_DIRS = (os.path.join("results","agents") + os.sep,)` RENAMED to
   `RETIRED_EXEMPT_AGENT_DIRS = ("results/agents/",)` -- Jad defines
   `RETIRED_EXEMPT_DIRS = ("results/void/",)` 46 lines later, which would silently replace
   Ghassan's value, and Jad's `tracked_files()` returns "/" paths, not `os.sep`; hunk 4 both
   functions (`check_scenario` and `check_derived`); hunk 5 Jad's `tracked_files` list plus
   Ghassan's prefix and agent-report exemptions; hunk 6 Jad's `(?<!adds )` guard plus
   Ghassan's `11|eleven`. Plus the two exemptions in `ALL`.
2. **The 7 of 73 verify_docs failures**: both branches are green on their own (67 of 67,
   44 of 44). They exist only because Jad's documents and Jad's pins now sit on Ghassan's
   physics and data. Fix: sweep the documents (section 3), and decide the 5 `check_scenario`
   pins (920.1 / 883 / 873.1 / 604.8 / 14 is what the merged tree prints). They are
   expected values, and verify_docs.py and CLAUDE.md both say never to edit an expected
   value to make a run pass -- so moving them is a team decision, made with a dated note
   of the measurement, the way Ghassan's side moved 295.0 -> 321.7 for drive B. The 8
   `results/phase_d_seed*.txt` hits need an exemption (frozen results scored on the old
   plant), not an edit.
3. **drift_test.py crashes** on the merged tree: `subprocess.run(..., text=True)` at
   drift_test.py:114 decodes verify_docs' output as cp1252, and the merged run's WRONG lines
   echo Arabic text (presentation/plan.html:890 is one) whose UTF-8 bytes include 0x81.
   It does not crash on Jad's branch because that run is green and echoes no such line.
   Fix: `encoding="utf-8", errors="replace"` in that call (or run with PYTHONUTF8=1).
   The character is the bug, not the data -- the same shape CLAUDE.md records under mistake 16.
   With the crash avoided (PYTHONUTF8=1) it reports 16 of 16, which proves nothing while
   the baseline is red (section 2); re-run it after item 2 is fixed.
4. **Phase D would read n = 9** without extra edit a (section 1). Fix: the move.
5. **app/test_agents.py ProofTests** without extra edit b (section 1). Fix: the
   agent_trace edit plus the RESULT_KEYS line.

### (b) expected: figures that move with Ghassan's physics or data

- check_premise 920.1 at 883 C and -0.3 points (was 959.8 / 884 / -0.4 on Jad's plant).
- app replay pins: 7475b5d7 873.1 C / 14 thermal, pull01 604.8 C (Jad's 890.6 / 15 / 608.0).
  app/test_replay.py carries Ghassan's pins and passes; only Jad's verify_docs pins and Jad's
  documents carry the old ones.
- Dataset: 11 drives, 321.7 min, 8 carrying samples, 568 pinned MAF samples across 7 drives
  (drive B). Every Jad-side document quoting 295.0 / ten drives is now stale.
- plant_sha moves to c236a8db3e201090 (Ghassan's), so every agent trained on Jad's plant
  (b5a3069f...) will be refused by `evaluate.py` without `--force-plant-mismatch`.
- validate.py 8 of 11 with rows 8-11 scored against the car; verify_docs agrees (8, and 4
  car rows).
- **Fingerprint gap, not a failure but worth knowing:** `PLANT_FILES = ("plant.py",
  "thermal.py", "engine_env.py")` (fingerprint.py:85). On the merged tree `plant.py` and
  `engine_env.py` read constants from `data/derived_params.json` at run time (through
  `derived.py`), and neither file is hashed. Re-deriving the JSON changes the physics
  without moving `plant_sha`. Fix: add `data/derived_params.json` (byte hash) and
  `derived.py` to the fingerprint -- which itself moves plant_sha once.

### (c) pre-existing, also on the unmerged branches, or artefacts of the trial

- `app/static/vendor/` is gitignored (Jad's .gitignore), so a clean checkout fails
  `app.test_simulation`'s import-map test and `app.test_agents`' `test_page_assets_ids`
  (`run app\start-simulation.ps1 once to vendor Three.js`). Same on Jad's branch. Not a
  merge problem; running the vendoring script once fixes it.
- `node --test app/static/sim/` does not work on Node 24; the documented glob form passes.
- Trial artefacts, gone once the folder was a git repo and the runs were serialised:
  5 `test_key_files_are_ignored` failures (`128 != 0` -- `git check-ignore` outside a
  repository), and a `tearDownModule` "the suite changed files on disk" error caused by
  check_premise rewriting results/premise.json and by the vendor copy, both while the
  suite ran in parallel.

## 5. Files left for the caller

- `$SP/work/trial/merged` -- the resolved tree (a git repo with one commit; working tree
  holds `verify_docs.UNION.py` as verify_docs.py, the version drift_test ran on), vendor folder present.
- `$SP/work/trial/merged2` -- the same tree with `verify_docs.UNION2.py` installed.
- `$SP/work/trial/verify_docs.UNION2.py`, `verify_docs.union.patch` (against Jad's side),
  `agent_trace.patch`, `test_agents.patch`, `union_verify_docs.py` (builds UNION from the
  conflicted file), `logs/`.

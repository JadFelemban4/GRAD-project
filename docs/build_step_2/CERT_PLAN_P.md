# P's B58 identity certificate: the run plan (build step 2, ORDER step 14)

Written 5 November 2026 with P2's draft (the interface sheet 6.8; row 138 (4) and (6)), before any of
it ran, and brought to P's port onto step 13's tree on 6 November 2026 (D146, `a3cd3a3`: no C2, no
cam-aware surrogate path and no fourth arm, row 146 (3); the interface sheet 17). **Nothing in this
plan has been run.** It is commit A's plan (`CERT_PLAN_A.md`, inside
`results/B58_IDENTITY/certificate_tools.tar.gz`), changed only where the plant commit P changes what
a step reads or expects; every step it does not name runs as commit A's plan writes it. Item 20
(L8, training) runs on the training device at ORDER step 18, never here (decision 61), and its record
goes to `results/B58_IDENTITY/L8_device/`, never into `results/B58_IDENTITY.md` (row 146 (6)).

**What is certified.** PLAN.md 3.6 items 1-19 as `AMENDMENTS.md` amends them, run against `cf43fbb`
as commit A ran them, with commit A's added checks (B1-B3, B8, B9, B11, B12, HA.2-HA.11, HP7.1,
HP7.6, HP7.7), `test_tit_cap.py` and `test_preview_horizon.BlindBitForBit` (row 138 (4)). The
claim is row 94's: the B58 is identical at every default. Its plant_sha moves, because P edits
two files of PLANT_CODE (`engine_env.py`, `engines.py`; `fingerprint.py`, which P also edits, is not in
PLANT_CODE, `fingerprint.py:133`); its engine_sha and derived_sha do not.

**The candidate.** P's one commit on step 13's tree (`a3cd3a3`), after RV, committed and clean, in
REPO's place as commit A's `wp1-work` was. On P's ported tree (6 November, uncommitted)
`epa_freeze.plant_sha` printed `36655cab94800e30` for the B58, `a8dd5aeadf909e67` for the Ford,
`e5f59cf2cff3d1a5` for the Honda and `a1c89b974124e1cc` for the Mazda; at `a3cd3a3` they are
`865f8e7b7e5c2dbe`, `cec3e3faefe47172`, `a4e6138b9d258b1f` and `f86baf59389dea29` (as at C1b; the
drafts' values on C2's tree, `1dbac5ce36bd7ca3` and the rest, held the cam-aware surrogate path that
row 146 (3) leaves out). derived_sha and engine_sha did not move on any engine. The run reads them
again at its start and its end on P's tree, and only those readings are quoted.

## 1. What changes, step by step

**Precondition (row 139 (2)): every entry-point command runs in REPO or a git clone.** The five
entry points (`train.py`, `train_all.py`, `run_phase_d.py`, `evaluate.py`, `benchmark_training.py`)
build their `--engine` choices with `engines.trainable()`, which refuses a folder that is no git
work tree. Commit A's `copy_tree.py` copies (`S/cand`, `S/candd`, `S/candw`, `S/candt`) have no
`.git`. Before the run, every job file and script a copy runs is searched:

```bash
grep -n -E 'train(_all)?\.py|run_phase_d\.py|evaluate\.py|benchmark_training\.py|trainable' \
  $S/tools/*.sh $S/tools/*.py $S/tools/certify_original/jobs_*.txt
```

A hit whose job runs in a copy moves to a git clone of the candidate (`git clone --no-hardlinks
$REPO $S/candg`, its HEAD recorded beside the copies' manifests). G6.3 and G6.4 run `evaluate.py`
in REPO, as commit A did.

**G1.0 identity.** `fingerprint.py --engine b58` prints the schema-4 block (row 138 (2)). Expected:
plant_sha P's (as read at the start), derived_sha `326c0835548975e2`, engine
`b58b30o1/a90-supra-zf8hp51`, engine_sha `023f5589215ee68e`, train_backend and score_backend
`cycle`, backend_contract the sha_text of `results/ENGINE_THRESHOLDS.md` and `.json`, transmission
`final_drive=3.15 gears=5.25 3.36 2.172 1.72 1.316 1 0.822 0.64 kind=stepped`, dtheta 0.25, knees
1123 and 408, scenario `grade=0.12 t_amb=315 v_kmh=130`, episodes_sha `05a598a574268b20`,
preview_h_s 30, reward_knock True, preview_samples_s `2 5 15 30`, git_dirty False,
git_dirty_plant_files empty, python 3.13.2. These are the values P's ported tree printed on 6
November (its block read git_dirty True, `engine_env.py` uncommitted), plant_sha then
`36655cab94800e30`; `S/out/fp_ref.txt` (cf43fbb) stays the reference.
`engines.py` lists the four plants with their engine_sha and derived file (all calibrated since
commit D).

**G6.3 L7 and G6.4: `tools/make_meta.py` (inside `results/B58_IDENTITY/certificate_tools.tar.gz`,
extracted outside the repository) writes a schema-4 scratch meta.json** (recorded in `TOOL_EDITS.md`,
section "commit P"). The live block is built with every FATAL input passed
(rule 1.7, mistake 19), and the blinded agent's through `FP.for_arm`:

```python
import engine_env as E  # noqa: E402
live = FP.plant_fingerprint(protocol="phase-d", plant=engines.get("b58"), train_backend=FP.BACKEND_CYCLE,
                            score_backend=FP.BACKEND_CYCLE, preview_h_s=E.PREVIEW_H_S,
                            reward_knock=E.REWARD_KNOCK_DEFAULT)
live = FP.for_arm(live, sighted="blind" not in os.path.basename(src))    # evaluate.py's arm rule
```

Its `identity_override` reason names P's certificate and "this tree's schema-4 block" instead of
build step 1's and schema 3. L7 scores `sighted_seed0` as commit A did, and `blind_seed0` beside it
(the blinded arm's FATAL block has preview_h_s None, row 117). Expected as commit A's G6.3: `FATAL
disagreements with the live tree: none`, `schema_problem: None`, evaluate.py exit 0 with no
`--force-plant-mismatch`, `NO DIFFERENCE` after the fingerprint block and the model path, and
`VERDICT: every row equals the committed raw scores`, for each agent. The run passes
`--reward-knock` only if P's evaluate.py requires it on phase-d; it does not (row 138 (1): absent
reads 'in').

**G7.0 and G7.2: the suites.** G7.0 (`test_engine_threading.py`, alone) as commit A ran it, after
the roads check and the certificate's other runs (rule 1.3). G7.2 adds `test_preview_horizon.py`
(BlindBitForBit among it), `test_tit_cap.py` and `test_epa_plants.py` to commit A's list
(`test_step_record.py` is never written, row 146 (3)). Every count is the run's own "Ran N tests"
(HP7.6); none is quoted here. `test_trainable.py` printed "Ran 23 tests ... OK" on P2's draft and
again on P's port (6 November), and `full_run.py` states that count; the certificate's run states
its own.

**G7.3: amendment B8's --help runs, five entry points.** `benchmark_training.py` joins the four.

```bash
WANT=$(cd $REPO && $PY -B -c "import engines; print('--engine {' + ','.join(engines.trainable()) + '}')")
for f in train train_all run_phase_d evaluate benchmark_training; do ( cd $REPO && $PY -B $f.py --help > $S/suites/P_G7_help_$f.txt 2>&1; echo "exit $?" >> $S/suites/P_G7_help_$f.txt ); done
grep -h -o "\-\-engine {[^}]*}" $S/suites/P_G7_help_*.txt; echo "want: $WANT"
```

Expected: five exit 0, each usage naming `$WANT`, `engines.trainable()` on the real tree at P in
known() order (the B58 first). Run 2's committed summary.json drops all three EPA engines (the
Mazda by its re-run's governing entry; section Q), so at P it is `--engine {b58}`, as
`test_trainable.RealTree` printed on P's port ("the expectation ('b58',); engines.trainable()
('b58',)"). Commit A
expected `--engine {b58}` from a typed tuple; the refusal and its control are now
`test_trainable.SummaryDrop` (mazda_25t dropped on synthetic committed records, B8's literal case),
with RecordsAbsent and BackendDrop beside it, all in G7.2.

**G7.4: the documents.** HA.5's count check reads `full_run.py`'s and README's `test_trainable.py`
lines as P2 wrote them (README states no count). HP7.6 compares every stated count with G7.0's and
G7.2's runs.

## 2. The records

The new `results/B58_IDENTITY.md`, its `.json` and the tools archive (with this plan and the
`TOOL_EDITS.md` section "commit P") replace commit A's, made by `make_cert.py` and `make_md.py`
with a P config as commit A's `cert_A.json` (amendment B9). Commit A's `results/B58_IDENTITY.md`
moves verbatim to the end of `STATE_HISTORY.md` (decision 67).

## 3. The sweep (decision 67; row 138 (6))

Run on P's final tree, after the certificate: `git grep -n 865f8e7b7e5c2dbe`, and the same for the
EPA engines' pre-P plant_sha above. Each present-tense mention gets the value `epa_freeze.plant_sha(e)`
prints on P's tree; no RETIRED entry is made. On P's ported tree (6 November) the hits were:

| where | what it says | at P |
|---|---|---|
| `Explanatory Simulation/tests/test_catalog.py:106` | the lab's live plant_sha pin | moved to `36655cab94800e30` on P's port, with a comment naming P (the lab's tests passed, 10 of 10); re-read on P's final tree |
| `CHECKPOINT.md:5` | "the B58: plant_sha 865f8e7b7e5c2dbe ... fingerprint schema 3" | rewritten with P's checkpoint: P's value and schema 4 |
| `results/B58_IDENTITY.md`, `.json` | commit A's certificate | replaced by P's (section 2) |
| `epa_roads.py:143`, `epa_tightenings.py:54` and `:428`, `test_epa_tightenings.py:1108`, `results/EPA_ROADS/*` (README, roads.json and the attempt records), `results/EPA_TIGHTENINGS.json` | the draw's plant | stay (hashed or record-bound) |
| `results/VALIDATION_DECISIONS.md` (rows 102, 111, 127, 146), `docs/build_step_2/ROW111_STATEMENTS.md:32`, `docs/build_step_2/ROW146_STATEMENTS.md:52`, `docs/build_step_2/ORDER_TO_TRAINING.md:36`, `docs/build_step_2/INTERFACES.md:728`, `:1094`, `SESSION_REPORT_2026-10-30_run1.md`, `STATE_HISTORY.md`, `results/benchmarks/step3_2026-11-02/*` | the draw's or X1's plant, a signed statement, the plan, or a dated record | stay |
| the EPA engines' C1b plant_sha | only in `results/EPA_CALIBRATION/*`, `results/EPA_ROADS/*` and `results/EPA_TIT_CAP/ford_27tt.json` | stay (records) |

## 4. P's commit message

The four post-P plant_sha and derived_sha; `test_reward.py`'s output; `app.test_replay --full`'s
output; both of `--compare`'s lines; RealTree's printed expectation beside `engines.trainable()` on
the real tree; and "from P on, the contract's engine_env.py citations are read at c842d74".

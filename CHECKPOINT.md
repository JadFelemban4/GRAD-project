# CHECKPOINT — Current Project State

Last verified: 2026-10-31 (on `GRA-test`, at R3a, after R0a, C1, N and K) — verify_docs.py 74/74 · drift_test.py 18/18 (R0a's gate) · the app suites at R0a: the known `?v=` asset checks and the `pwsh` launcher test fail, as on 15 October (`SESSION_REPORT_2026-10-31_build-step-2.md`)
main: the merge and the documentation restructure (14 October), the results tab's schema fix (15 October, on Jad's go) · sim-v1 not tagged yet (plan v3 phase 3) · plant_sha 3c48890dd15bc116 (Python 3.12.10) · derived_sha 326c0835548975e2 · fingerprint schema 2
GRA-test: build step 2's commits A (WP1, certified 23 October, `results/B58_IDENTITY.md`), C (the calibration and validation scripts, WP3) and D (`25437ba`, 30 October: Run 1, the three EPA engines calibrated and frozen), on contract version 5 (`c842d74`, unchanged since the first fit) · the B58: plant_sha 865f8e7b7e5c2dbe (Python 3.13.2) · derived_sha 326c0835548975e2 · engine_sha 023f5589215ee68e · fingerprint schema 3, unchanged by Run 1 (decision 48's re-runs) · pending: L8 on the training device

The previous CHECKPOINT.md, every session from 9 September to 14 October, is
`STATE_HISTORY.md` part B, verbatim. This file holds the current state only: the
permanent rules are `CLAUDE.md`, the history is `STATE_HISTORY.md`.

## Current objective

Test whether preview information is worth acquiring (the H/τ criterion,
`CLAUDE.md`). The two newest ablations, X1 and X2, did not settle it, and the
knock model the agents learn against is untested until drive C. Since 19 October
the project is on the research track; the team plans in Notion (gates G0–G9).

## Verified current state (each line names the script or file that proves it)

- Drive C was driven on 18–19 October and covered neither part: the logging
  was right, the driving was not (Jad's side's check, `drive_c_check.py`).
- X2 (11–13 October): INCONCLUSIVE on five pairs, the agents not converged
  (`python analyse_x2.py` -> `results/X2_RESULT.txt`; `results/x2_convergence.txt`).
- X1 (8–9 October): preview's effect below the MEI of 5.43 points of cut, 17 of
  23 pairs, sign p 0.0173 (`python analyse_x1.py` -> `results/X1_RESULT.txt`).
- The plant carries the four steps agreed on 30 September (`75ca65f`), and the
  premise reads baseline 848.1 at 883 °C (`python check_premise.py`).
- Ghassan's `GRA-2340394` (`c16b857`) was merged into Jad's work on 14 October
  (`cc5468f`; every conflict, both sides, in `conflict_2026-10-14.md`). Every
  simulation file is byte-identical to his last push, and his `check_premise`,
  `validate` and `test_reward` print his figures on Jad's machine.
- `python verify_docs.py`: 74 of 74 checks pass, the SIZE check among them.
- `GRA-test` (21 October): no default engine anywhere
  (`python test_engine_threading.py`), and the B58 through `engines.get("b58")`
  is cf43fbb's plant to the bit at every level L1–L8, after the review's fixes
  (build step 1's certificate, `STATE_HISTORY.md` part S; commit A's is
  `results/B58_IDENTITY.md`). The EPA maps of the Mazda 2.5 T, Honda L15B7
  and Ford 2.7 TT are in `logs/epa/`, read by `epa_map.py` into `data/engines/`
  (`python test_epa_map.py`); the four cars' published values in
  `engine_specs/cars/`.
- On the locked climb the λ trim at its bound saves 0.068 points of cut in the
  30 s before the climb (0.062 open loop, 0.044 with knock), and 0.208 over the
  whole flat with unlimited preview (0.203, 0.185), against the MEI of 5.43
  (`python roads_ceiling.py control` -> `results/EPA_ROADS/control.txt`): the climb
  that X1 and X2 were scored on cannot show a preview effect (decision 34).
- No road the ceiling probe tried reaches decision 34's 2 MEI on all four engines:
  λ is the only lever that cools the housing, and the Ford's best is 4.24 points,
  0.78 MEI (`results/EPA_ROADS/probe_2026-10-30/summary.txt`; section I, row 103).
- `python test_contract_pinned.py` (19 OK): the validation contract (`results/ENGINE_THRESHOLDS.md`
  and `.json`, version 5) is `c842d74`'s and freeze.json's; `engine_thresholds.py --check` cannot pass
  once a fit exists (`docs/build_step_2/PLAN.md` 8.4: its manual check is a worktree of `c842d74`).
- Run 1 (`25437ba`; `results/EPA_CALIBRATION/<id>/`; `python test_epa_plants.py` rebuilds each plant
  against them, 7 OK): no form passes in-sample, so all three froze at A+B+C+D (decisions 82, 93).
  Mazda: fails E1a E2a E3a L0 L1, knee 1030.32 K, derived_sha e8318dd80c3375f2. Ford: the same
  fails, knee 937.17 K, derived_sha 61f84c7d02b6b816. Honda: fails E4a too, knee 911.80 K, no
  schema-3 fingerprint (CVT, decision 91). Delivery: no step over the tolerance on any engine;
  the worktree reproduction byte for byte (decision 89). No held-out row read.
- `python check_training_device.py`: this laptop matches `requirements-lock.txt`;
  its `--identity`/`--compare` modes decide whether a second machine trains
  identical agents (decision 32). Not yet run on the training device.
- G-CTX passed: in a fresh session every memory file together is 5.8k tokens
  (Jad's `/context`, 14 October).
- The results tab names the plant of Phase D, D2 and C4: made on another plant,
  `sep17-before-merge`'s, each file read by its own fingerprint schema
  (`ca2cd73`, `2fd9aed`; `SESSION_REPORT_2026-10-15_results-schema.md`).
- App suites (15 October, Python 3.12.10): `python -m app.test_replay` 49 of 49,
  node 306 of 306, `app.test_results` 123 of 124 (the one needs `pwsh`);
  `app.test_agents` 22 failing, 19 of them the agents page refusing the old
  agents, and `app.test_simulation` 1 (its asset check), both as on `main` before.

## In progress (who · branch · what)

- Ghassan · `main` · drive C: the rule AGREED 19 October (decisions 14–23;
  `results/DRIVE_C_RULE.md`) and its analysis script committed
  (`drive_c_analysis.py`, `python -m unittest test_drive_c_analysis` 105 of 105;
  `SESSION_REPORT_2026-10-19_driveC-rule.md`). The repeat drive is next.
- Jad · the drive C check and the proposal's evaluation: both accept, four
  corrections asked (`SESSION_REPORT_2026-10-19_driveC-and-evaluation.md`).
- Ghassan · `GRA-test` · the four-engine test (decision 24): commits A, C and D
  made (Run 1 frozen, 30 October; `SESSION_REPORT_2026-10-30_run1.md`). Both have
  answered decisions 1-132 (`results/VALIDATION_DECISIONS.md`; I, 30 October: A+G, no
  knock term; J-L, 31 October, L under Ghassan's standing approval). Roads code: R0a; R0
  waits for the two sha256 lines. The Ford's cap: R2a `9e37551`, R2b `2f8e4a5`.
  Training runs on another device, not this laptop (21 October).

## Blockers

- The knock model is untested: drive C decides how much of every agent's
  margin is real.
- Stage A has not run on the 18–19 October files (Jad's `Downloads/2026-10-19`).

## Next actions (in order)

1. Drive C: put the 18–19 October files in `logs/drive_c/` (never `logs/raw/`) and
   run `python drive_c_analysis.py stage-a --c2 <files> --c1 <files>` (blind) to
   count what they give; repeat drive C (`logs/DRIVE_PLAN.md`); then stage A on
   all files, stage B (the freeze), commit the frozen list, stage C once. Then A
   and D on one trip.
2. The proposal's corrections, and the two-plant claim in `CLAUDE.md`
   (`docs/supervisor/2026-10-19_proposal-evaluation.md`, sections 4 to 6).
3. The four-engine preregistration, once build step 2, the test roads (decision
   34), the training recipe (29) and the device benchmark (32) are in: every one
   of decisions 1-35 is answered (21 October), so nothing else waits for them.
4. The learning lab's pins move to the live plant (`team/jad.md`). The agents
   page reads each agent's own fingerprint schema and its tests stop copying
   `runs_c4`'s `meta.json`; `test_simulation`'s asset check learns the `?v=`
   suffix (`SESSION_REPORT_2026-10-15_results-schema.md`, section 2).
5. Plan v3 phase 3: tag `sim-v1`, write `CHANGELOG.md` and the results index.
6. The parallel items of 30 September (Ghassan's twenty on multi-climb roads,
   the spark-capped rescoring of Jad's 48, Chapter 4 with both branches side by
   side and never pooled, the battery of Phase E) and the app's backlog are
   `STATE_HISTORY.md` part E, verbatim. X1 and X2 came after them: check an item
   before taking it up.
7. `main`'s `train.py` `CLOSED` list still has no `wideair_dt1` (X2, published 13
   October); `GRA-test`'s has it since C1 (ORDER step 7).
8. `GRA-test`, build step 2: `docs/build_step_2/ORDER_TO_TRAINING.md`, steps 3-22 in
   order (sections I-L). Done 31 October: R0a, C1, N, K, R3a. Next: each of you sends the sha256
   of a private 256-bit integer (row 96); then R0, the push and the reveal. Pause Windows
   updates now (row 126). Run 2's checklist: `docs/build_step_2/RUN2_CHECKLIST.md`. Nothing
   else in CODE_HASHED or PLANT_CODE changes before the last commit F; `test_epa_rows` fails once until commit G (row 120).
9. `main`, its own commit: re-run `python check_roads.py`, commit the new
   `results/training_roads.json` (stale since `75ca65f`), grep its old figures.
10. On the training device, before any training: install from
   `requirements-lock.txt` (and, to measure its GPU, the CUDA build of the same
   torch in a second environment); run `python benchmark_training.py --engine b58 --road
   extremes --device cpu` there (C1 made both options required), which decides CPU or GPU
   and checks that seed 0 trains identically twice; then
   `python check_training_device.py --identity device.json` there and on this
   laptop, and `--compare` the two (recorded, not required; decision 32).
11. The literature (`docs/literature/READING_LIST.md`, 183 sources): one person does
   its ten-minute SDL login check and asks the librarian about interlibrary loan,
   then buy what remains ($392.00 whatever the login shows). Each source is read
   in full by a named team member before it is cited.

## Files outside git (where · last backup · manifest)

- Trained agents (`runs*/`) and the per-step records (`*_record.npz`) live on
  the machines that trained them. Jad's machine: a backup of 14 October, 4,391
  files, 2.5 GB, VERIFIED, with its `MANIFEST.csv` and `SHA256SUMS`; one copy,
  on the same disk; a Google Drive copy and a USB copy are still to make.
  Checked 15 October: its 978 agent files are unchanged on disk, and `C:` is
  still the only disk (session report of 15 October, 2.4).
- `GRAD-agent-backups/2026-09-23` and `2026-09-24` (`runs_c4`, sha-checked).
- Drive C's six CSVs and the evaluation workbook: Jad's Downloads, one copy
  (SHA-256 in `logs/DRIVE_C_CHECK_2026-10-19.md` and the evaluation file).

## References

`CLAUDE.md` (Training gate) · `README.md` · `results/README.md` ·
`STATE_HISTORY.md` · `HISTORY.md` and `CHANGELOG.md` (not written yet)

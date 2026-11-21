# CHECKPOINT — Current Project State

Last verified: 2026-11-15 (on `GRA-test`, after `T*` `720587d`: CK's record in `results/B58H_CHECK/`, PR-B section 15) — verify_docs.py: all 170 checks pass (PR-B section 14's step 2 gate on CK's record) · drift_test.py 18/18 (R3b's gate) · the app suites on P's tree: every failure one RV's own run had, the known `?v=` asset checks, the `pwsh` launcher tests and five provenance tests of app.test_results (`SESSION_REPORT_2026-10-31_build-step-2.md`, section 17)
main: the merge and the documentation restructure (14 October), the results tab's schema fix (15 October, on Jad's go) · sim-v1 not tagged yet (plan v3 phase 3) · plant_sha 3c48890dd15bc116 (Python 3.12.10) · derived_sha 326c0835548975e2 · fingerprint schema 2
GRA-test: build step 2's commits A (WP1, certified 23 October), C (the calibration and validation scripts, WP3), D (`25437ba`, 30 October: Run 1, the three EPA engines calibrated and frozen), P (ORDER step 14, the plant commit: H as a parameter, fingerprint schema 4, the knock option; certified 8 November, `results/B58_IDENTITY.md`), Qa, G, V, Q and Ta (`0329456`, 13 November), and B1 (`891e29a`, 14 November, results only, from Jad's PC), on contract version 5 (`c842d74`, unchanged since the first fit) · the B58: plant_sha 36655cab94800e30 (Python 3.13.2) · derived_sha 326c0835548975e2 · engine_sha 023f5589215ee68e · fingerprint schema 4 · L8 on the training device: PASS at B1

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
- `python verify_docs.py`: all 170 checks pass (15 November, at `891e29a` with this file rewritten), the SIZE check among them.
- `GRA-test` (21 October): no default engine anywhere
  (`python test_engine_threading.py`), and the B58 through `engines.get("b58")`
  is cf43fbb's plant to the bit at every level L1–L8, after the review's fixes
  (build step 1's certificate, `STATE_HISTORY.md` part S; commit A's, part AK; P's is
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
- B1 (ORDER step 18), on Jad's PC on 14 November from Ta `0329456` (B1's git_head), committed there as `891e29a` and pulled here on 15 November (his report, `SESSION_REPORT_2026-11-14_B1-visit.md`): seed 0 trains identically twice, `cpu: IDENTICAL` (`results/benchmarks/B1_bench_b58.attempt1.txt:31`); the rate is 107.46 steps/s at 12 runs at once, the lower bound of repeat 1, the lower of two (repeat 2 is flagged `loaded` and read higher; the flag decides nothing) (`results/B58H_DESIGN/d148_figures.txt:6-10`). At that rate the B58's 60 runs take 5 waves, 69.79 h, and CK 1.55 h (`:44`, `:54`); step 3's 106.19 is superseded (`:11`, `:46`).
- L8 on the training device, at B1: PASS. 11 runs exit 0; the three pairs and the wrapper read IDENTICAL, both relative-step controls DIFFERENT (`results/B58_IDENTITY/L8_device/_status.txt`, `_verdicts.txt`, read by `tools/run_l8.sh`'s rule). These files answer `results/B58_IDENTITY.md`'s "pending" for L8, a file that is not edited (row 146 (6)). B4: 7 tests, OK (`results/benchmarks/B1_device/B4_test_epa_plants.txt:12-14`).
- `python check_training_device.py`: this laptop matches `requirements-lock.txt`, and Jad's PC printed "VERSIONS: match the lock" at B1. B2, `--identity` on both machines and `--compare` (decision 32): NOT IDENTICAL, 100 differences (`results/benchmarks/B1_device/B2_compare.txt:23`), 75 of 96 weight tensors and 25 of 47 record fields, with the counters, meta and command equal (Jad's count from both files, his report's section 2; the curve compares nothing, since 0 episodes ran). Recorded, deciding nothing. Its cause is not attributed: the processor, the Windows build, the patch level and the Python build all differ. PR-B discloses it.
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
- Ghassan · `GRA-test` · build step 2 (decision 24): commits A, C, D, P, Qa, G, V, Q, Ta, D148, Tc, Tb and PR-B (its own commit is `T*`) made, and B1 from Jad's PC (Run 1 frozen, 30 October;
  `SESSION_REPORT_2026-10-30_run1.md`). Decisions 1-153 are answered (`results/VALIDATION_DECISIONS.md`; I: A+G,
  no knock term; J-L; M: he works alone, row 133; N: W; O: rows 135-143; P: rows 144-145; Q: Run 2's labels, all
  three EPA engines dropped; R: rows 146-147, the B58 study, under row 133 (2) as his answer Q1 extends it; n, the reward and the two statements his own answers Q3, Q4, Q2; S: rows 148-153, the decisions of 14 November, his and Jad's together, with his answers to points P1-P13 of 15 November (Jad, relayed on 15 November: "No objections") and his words re-confirming Q3, "I confirm the n= 20", of 15 November).
  Roads: R0 `bb91848`, R1 `fb20ab2`, R4 `34cca5b` (the redraws), RV `a443607` (the re-verifier, 7 November; its full check EQUAL on P's tree, `results/EPA_ROADS/reverify.json`, which P carries); the tightenings: R3b `4da4a31`. The Ford's cap: R2a `9e37551`, R2b `2f8e4a5`.
  Training runs on another device, not this laptop (21 October).

## Blockers

- The knock model is untested: drive C decides how much of every agent's
  margin is real.
- Stage A has not run on the 18–19 October files (Jad's `Downloads/2026-10-19`).
- Decision 1 of the 14 November sheet (the literature review's step 14, its A25 bullet; `decisions_2026-11-14.md`, on the Desktop) is still unanswered; the sheet asks for it before `T*`, the agents' deadline, which no row sets (section S's note), and PR-B does not wait for it. The training ran on Jad's PC from `T*` (`720587d`), 15 November 19:43:23 to 18 November 13:04:24, inside W, and its return passed every check on 19 November (PR-B section 15). AB is committed (`dd49844`). The scoring started on 20 November (Ghassan's choice, PR-B:476-478): items (a) to (c) are committed in `results/B58H_RESULT/`: the primary scoring, the analysis (`analysis_b58h.txt`), decision 12's three rows, the core rows and the practice spread; no route was written, so items (d)-(f), row 152 (5)'s anchors and row 153 (2) read "not computed (code)". After item (c), a print of decision 12's three rows (`b58h_descriptive_print.txt`) and a deviation are committed: `verify_docs.py`, a file present at `T*`, changed at `a6032e8` and the practice route ran there, against PR-B sections 6.0 and 5.2 (PR-B section 15). PR-B section 16, the outcome, is written. Open: PH1 and PH2, post hoc (`SESSION_REPORT_2026-11-15_D148.md`, sections 14 to 19).

## Next actions (in order)

1. Drive C: put the 18–19 October files in `logs/drive_c/` (never `logs/raw/`) and
   run `python drive_c_analysis.py stage-a --c2 <files> --c1 <files>` (blind) to
   count what they give; repeat drive C (`logs/DRIVE_PLAN.md`); then stage A on
   all files, stage B (the freeze), commit the frozen list, stage C once. Then A
   and D on one trip.
2. The proposal's corrections, and the two-plant claim in `CLAUDE.md`
   (`docs/supervisor/2026-10-19_proposal-evaluation.md`, sections 4 to 6).
3. The four-engine preregistration is never written: Run 2 dropped all three EPA engines (section Q). The B58
   study's is `results/PREREGISTRATION_B58H.md` (ORDER step 20; rows 146-153), its own commit `T*`; Run 2's failed validations are
   in `results/README.md` and `thesis/LIMITATIONS.md`.
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
8. `GRA-test`, build step 2: `docs/build_step_2/ORDER_TO_TRAINING.md`, steps 13-22b for the B58 study (sections I-S).
   Run 2 is done (5-6 November): **section 7 drops all three EPA engines**, so the four-engine test does not run: Tb's record, `results/EPA_BACKEND.json`, holds n null and in_test ['b58'], with no schedule drop, and MD:1611-1612 applies: "If no EPA engine survives, the four-engine test does not run, and the failed validations are reported as results" (INTERFACES 10.2, read through 17's 10.2).
   R4 is done (`34cca5b`: version 6, the B58 alone gating, redraws nothing; version 5, 58 Ford slots, reported, never
   scored). Rows 146-147 (D146) fix the B58 study across H: three arms, n = 20 (Ghassan's answer Q3), knock out of the reward,
   exploratory, never a test of the criterion, from `T*` (PR-B's own commit), before drive C (`docs/build_step_2/ROW146_STATEMENTS.md`). Committed: step 13 (no commit), RV, P, Qa, G, V, Q and Ta, 7-13 November (the session report of 31 October, sections 16-22), and B1 (`891e29a`, pushed from Jad's PC on 14 November and taken here on 15 November with `git pull --ff-only`). D148 (section S, rows 148-153; `SESSION_REPORT_2026-11-15_D148.md`): a check run CK, the pilot's command at 50 000 steps, replaces PL-B (row 148); the analysis code AB moves after `T*` (149); four descriptive rows stand beside d (150-153); `results/B58H_DESIGN/` gains `d148_figures`, `grids_b58` and `hw_opt/` (row 153 (1)).
   Tc, Tb and PR-B are done (15 November; `SESSION_REPORT_2026-11-15_D148.md`, sections 10, 12 and 13): step 18a, `epa_backend.py`'s check-run line, row 148 (1)'s in place of the pilot's; step 19, the backend record, n null; step 20, `results/PREREGISTRATION_B58H.md`, whose own commit is `T*` (`git log --diff-filter=A --format=%H -- results/PREREGISTRATION_B58H.md`), with Tb's commit its parent; `T*` is `720587d`, pushed. The ONE visit to Jad's PC from `T*` began on 15 November, by the sheet `VISIT2_SHEET.md` (`For Jad - Visit 2` on Ghassan's Desktop; session report sections 14 and 15), from PR-B's section 14: CK (step 21) printed "CHECK RUN: OK" (18:28-19:43, the device's clock), its record is committed in `results/B58H_CHECK/`, and the training (step 22) started at 19:43:23 (Jad's agent's message; PR-B section 15 records the agent as a deviation). Next, on this laptop during training: AB (step 22a) and the routes (step 22b). Then the scoring, in row 149 (5)'s order (a)-(f), with (d)-(f) run only if started by 23 November 2026 00:00 AST. Latest starts (`results/B58H_DESIGN/d148_figures.txt`): the training by 17 November 02:12 AST to end inside W (`:140`), and by 16 November 16:12 for the primary scoring to end inside W too (`:141`); step 3's 01:22 and 15:22 are superseded (`:149`).
   Updates paused to 30 November; the laptop stays frozen until the study's last scoring; `test_epa_rows` passes from G (G's commit message); the battery's hills file is checked by its engine_sha alone (an open item for the decision sheet). On a fresh clone with core.autocrlf=true, test_epa_tightenings' LiveRecord fails: the ecu folder is hashed by its raw bytes (the session report of 31 October, section 20).
   Open (Qa, not its own): a SYNTHETIC record passed to engine_gate as `--roads` leaves run_gate's synthetic flag False, so print_gate can call the reward safe to train against on a hand-made file; Q passes the REAL record. Open (Q): a repeat of Q after a re-made P (row 140 (5)) is not built into Q's gate; its commit would modify Q's paths.
9. `main`, its own commit: re-run `python check_roads.py`, commit the new
   `results/training_roads.json` (stale since `75ca65f`), grep its old figures.
10. The training device, Jad's PC (`DESKTOP-VF1MO3H`; `SESSION_REPORT_2026-11-14_B1-visit.md`, sections 1, 3 and 4): the clone is `C:\Users\admin\grad_device\GRAD-project-device`, fresh from GitHub (step 3's worktree was removed on 11 November at Jad's request), detached at `T*` since the visit of 15 November (every CK run's `git_head` `T*`, `git_dirty` false; `results/B58H_CHECK/`) until the training ends; the interpreter is step 3's lock venv, moved to `C:\Users\admin\grad-venv-lock-3.13.2` (its newest `site-packages` entries 2 November). `core.autocrlf=true` gives a CRLF work tree, as at step 3: keep it (every FATAL fingerprint field is independent of line ends; section S's note).
   Windows Update was not paused there from 1 October to 14 November: KB5132061 (build 26300.9974) and KB5132688 on 11 November, Windows App Runtime updates on 11-12 November, and the NVIDIA driver 617.42 -> 621.24 on 13 November (torch is a CPU build there, so the driver enters no training). Jad paused updates at 19:52 on 14 November, before the benchmark, until 28 November. Jad, relayed by Ghassan on 15 November: nothing was installed after the pause ("No"), and NVIDIA's own updater is off ("Yes") (`SESSION_REPORT_2026-11-15_D148.md`, section 11).
   B1's environment is the one CK and the training keep. The visit's sheet sets those clone and interpreter paths, checks the pause and `core.autocrlf`, records the environment before CK and after the last run, and says who re-runs `train_all.py` after a FAILED line or a restart (`SESSION_REPORT_2026-11-15_D148.md`, section 8).
11. The literature (`docs/literature/READING_LIST.md`, 183 sources): one person does
   its ten-minute SDL login check and asks the librarian about interlibrary loan,
   then buy what remains ($392.00 whatever the login shows). Each source is read
   in full by a named team member before it is cited.
12. Frozen from B1's git_head `0329456` until the study's last scoring: every path of `epa_backend.cost_files` (`evaluate.py`, `train.py` and its import closure, `train_all.py`, `benchmark_training.py`, `check_training_device.py`, the plant code, `engine_specs/*`, `data/*`, the lock, `roads.json`, the `freeze.json` files), and `results/ENGINE_THRESHOLDS.*`, which feed the FATAL field backend_contract but are not in that list. So the label and source corrections of `engine_specs/b58.toml` and `engine_specs/a90_supra.toml` wait, and `wheel_r` does not change. Between `T*` and the first scoring command no path present at `T*` changes but CHECKPOINT.md, STATE_HISTORY.md, the session report and PR-B's section 15 (row 149 (3)).
13. After the last scoring: `benchmark_training.py`'s "x 4 engines" line multiplies by `ENGINES = 4`, not by the engines that train (`results/B58H_DESIGN/d148_figures.txt:45`), so it is no schedule. The source corrections from the reading of 14 November (Heywood 2018's pages, Chen & Flynn 1965, Landerl 2015, the MY23 eBrochure, the car's non-stock tyres) go into `engine_specs/b58.toml`, `engine_specs/a90_supra.toml` and `REFERENCES.md`, with verify_docs.py's retirements of Heywood's old figures. `REFERENCES.md` and verify_docs.py are no cost files and are hashed nowhere, so their half could have gone in before Tb; Tb landed first, so they wait until after the last scoring (`SESSION_REPORT_2026-11-15_D148.md`, section 12).

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
- B1's console output, `B0_versions.txt`, `B3_L8.txt` (L8's printed verdict) and the dry run's output: Jad's PC, `C:\Users\admin\grad_device\2026-11-14_B1\` and `~/grad_device/B1`, one copy (his report, section 4). The laptop's B2 identity file and its `.sha256`: the Desktop folder "For Jad - B1", not committed.
- hw_opt's run folder, with its `RESULT_SUMMARY.md` (hand-worked numbers, not committed): the Desktop folder "B58H tuned hand-written strategies (14 Nov 2026)"; its committed files are `results/B58H_DESIGN/hw_opt/`.

## References

`CLAUDE.md` (Training gate) · `README.md` · `results/README.md` ·
`STATE_HISTORY.md` · `HISTORY.md` and `CHANGELOG.md` (not written yet)

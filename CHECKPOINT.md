# CHECKPOINT — Current Project State

Last verified: 2026-10-21 (on `GRA-test`) — verify_docs.py 74/74 · drift_test.py 18/18 · the app suites below as of 15 October on main (`GRA-test`'s of 21 October: `results/B58_IDENTITY.md`)
main: the merge and the documentation restructure (14 October), the results tab's schema fix (15 October, on Jad's go) · sim-v1 not tagged yet (plan v3 phase 3) · plant_sha 3c48890dd15bc116 (Python 3.12.10) · derived_sha 326c0835548975e2 · fingerprint schema 2
GRA-test: build step 1 of decision 24 (four engines), reviewed, corrected and committed 21 October · plant_sha ded8da308863d394 (Python 3.13.2) · derived_sha 326c0835548975e2 · engine_sha 99d2a9658b1258a7 · fingerprint schema 3 · the B58 bit-identical to cf43fbb (`results/B58_IDENTITY.md`)

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
  (`results/B58_IDENTITY.md`). The EPA maps of the Mazda 2.5 T, Honda L15B7 and
  Ford 2.7 TT are in `logs/epa/`, read by `epa_map.py` into `data/engines/`
  (`python test_epa_map.py`); the four cars' published values in
  `engine_specs/cars/`.
- On the locked climb no use of the preview can save more than 0.13 points of cut
  with the agent's own levers (0.42 with unlimited preview) against the MEI of
  5.43 (`python preview_ceiling.py` -> `results/preview_ceiling.txt`): the climb
  that X1 and X2 were scored on cannot show a preview effect (decision 34).
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
- Ghassan · `GRA-test` · the four-engine test (decision 24): build step 1
  committed; build step 2 calibrates the three EPA engines and their cars. Training
  runs on another device, not this laptop (Ghassan, 21 October); decisions 25–35
  open.

## Blockers

- The knock model is untested: drive C decides how much of every agent's
  margin is real.
- Stage A has not run on the 18–19 October files (Jad's `Downloads/2026-10-19`).
- Thirteen validation decisions wait for Jad's and Ghassan's columns
  (`results/VALIDATION_DECISIONS.md`); nothing is relabelled, re-preregistered
  or retrained until they are answered.

## Next actions (in order)

1. Drive C: put the 18–19 October files in `logs/drive_c/` (never `logs/raw/`) and
   run `python drive_c_analysis.py stage-a --c2 <files> --c1 <files>` (blind) to
   count what they give; repeat drive C (`logs/DRIVE_PLAN.md`); then stage A on
   all files, stage B (the freeze), commit the frozen list, stage C once. Then A
   and D on one trip.
2. The proposal's corrections, and the two-plant claim in `CLAUDE.md`
   (`docs/supervisor/2026-10-19_proposal-evaluation.md`, sections 4 to 6).
3. The validation decisions.
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
7. For Ghassan, before the next training: `train.py`'s `CLOSED` list has no
   `wideair_dt1`, though X2's result was published on 13 October (session
   report of 15 October, 2.3).
8. `GRA-test`, build step 2: calibrate the Mazda, Honda and Ford on the B58's cycle
   model from `data/engines/` (thresholds fixed first, decision 35), their cars and
   the Accord's CVT, each validated on held-out EPA points; then the test roads by
   `preview_ceiling.py`'s rule (decision 34). For Jad and Ghassan: CLAUDE.md's
   re-run rule to name `engines.py` and `engine_specs/` (`.claude/rules/physics.md`
   does); fingerprint schema 4 (decisions 27, 28) before any new engine trains.
9. `main`, its own commit: re-run `python check_roads.py`, commit the new
   `results/training_roads.json` (stale since `75ca65f`), grep its old figures.
10. On the training device, before any training: install from
   `requirements-lock.txt`, then `python check_training_device.py --identity
   device.json` there and on this laptop, and `--compare` the two (decision 32).

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

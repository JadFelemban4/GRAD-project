# CHECKPOINT — Current Project State

Last verified: 2026-10-14 — verify_docs.py 74/74 · drift_test.py 16/16 (the full run, on the restructure's final commit)
main: the merge and the documentation restructure, both pushed on 14 October · sim-v1 not tagged yet (plan v3 phase 3) · plant_sha 3c48890dd15bc116 (Python 3.12.10) · derived_sha 326c0835548975e2 · fingerprint schema 2

The previous CHECKPOINT.md, every session from 9 September to 14 October, is
`STATE_HISTORY.md` part B, verbatim. This file holds the current state only: the
permanent rules are `CLAUDE.md`, the history is `STATE_HISTORY.md`.

## Current objective

Test whether preview information is worth acquiring (the H/τ criterion,
`CLAUDE.md`). The two newest ablations, X1 and X2, did not settle it, and the
knock model the agents learn against is untested until drive C.

## Verified current state (each line names the script or file that proves it)

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
- App suites after the merge (14 October): `python -m app.test_replay` 49 of 49
  and node 305 of 305; `app.test_results` and `app.test_agents` fail more than
  before the merge, because the results tab assumes fingerprint schema 1 (the
  open item in `team/jad.md`).

## In progress (who · branch · what)

- Nothing. The documentation restructure (plan v3 phase 4) is finished and on
  `main`: every move in `_merge_review/MIGRATION_LEDGER.md`, the session in
  `SESSION_REPORT_2026-10-14_merge-and-restructure.md`.

## Blockers

- The knock model is untested: drive C decides how much of every agent's
  margin is real.
- Thirteen validation decisions wait for Jad's and Ghassan's columns
  (`results/VALIDATION_DECISIONS.md`); nothing is relabelled, re-preregistered
  or retrained until they are answered.

## Next actions (in order)

1. Fix drive C's decision-rule numbers with Ghassan, before the drive; then
   drive C, then A and D on one trip (`logs/DRIVE_PLAN.md`, revised 14 October,
   `c16b857`).
2. A fresh Claude Code session at the root: `/context` must show `CLAUDE.md`
   under 200 lines (gate G-CTX).
3. The validation decisions.
4. The results tab learns fingerprint schema 2, and the learning lab's pins move
   to the live plant (both in `team/jad.md`).
5. Plan v3 phase 3: tag `sim-v1`, write `CHANGELOG.md` and the results index.
6. The parallel items of 30 September (Ghassan's twenty on multi-climb roads,
   the spark-capped rescoring of Jad's 48, Chapter 4 with both branches side by
   side and never pooled, the battery of Phase E) and the app's backlog are
   `STATE_HISTORY.md` part E, verbatim. X1 and X2 came after them: check an item
   before taking it up.

## Files outside git (where · last backup · manifest)

- Trained agents (`runs*/`) and the per-step records (`*_record.npz`) live on
  the machines that trained them. Jad's machine: a backup of 14 October, 4,391
  files, 2.5 GB, VERIFIED, with its `MANIFEST.csv` and `SHA256SUMS`; one copy,
  on the same disk; a Google Drive copy and a USB copy are still to make.
- `GRAD-agent-backups/2026-09-23` and `2026-09-24` (`runs_c4`, sha-checked).

## References

`CLAUDE.md` (Training gate) · `README.md` · `results/README.md` ·
`STATE_HISTORY.md` · `HISTORY.md` and `CHANGELOG.md` (not written yet)

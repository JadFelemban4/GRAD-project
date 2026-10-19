# CHECKPOINT — Current Project State

Last verified: 2026-10-19 — verify_docs.py 74/74 · the app suites as of 15 October (below; nothing under `app/` changed since) · drift_test.py 16/16 last run on 14 October (the restructure's final commit)
main: the merge and the documentation restructure (14 October), the results tab's schema fix (15 October, on Jad's go) · sim-v1 not tagged yet (plan v3 phase 3) · plant_sha 3c48890dd15bc116 (Python 3.12.10) · derived_sha 326c0835548975e2 · fingerprint schema 2

The previous CHECKPOINT.md, every session from 9 September to 14 October, is
`STATE_HISTORY.md` part B, verbatim. This file holds the current state only: the
permanent rules are `CLAUDE.md`, the history is `STATE_HISTORY.md`.

## Current objective

Test whether preview information is worth acquiring (the H/τ criterion,
`CLAUDE.md`). The two newest ablations, X1 and X2, did not settle it, and the
knock model the agents learn against is untested until drive C. Since 19 October
the project is on the department's research track (Jad), and the team plans in
Notion (the GRAD Project Dashboard: gates G0–G9, 12 October to 23 November).

## Verified current state (each line names the script or file that proves it)

- Drive C's first attempt (18–19 October) covers neither C1 nor C2, checked
  blind; its CSVs stay outside `logs/raw/` (`python drive_c_check.py <folder>`).
- The proposal's evaluation: both evaluators accept, four corrections asked
  (`docs/supervisor/2026-10-19_proposal-evaluation.md`).
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

- Jad · `JMF-2340550-driveC-check` · the drive C check and the proposal's
  evaluation (`SESSION_REPORT_2026-10-19_driveC-and-evaluation.md`).
- Ghassan · drive C again, C2 then C1, once the rule's numbers are fixed.

## Blockers

- The knock model is untested: drive C decides how much of every agent's
  margin is real.
- Thirteen validation decisions wait for Jad's and Ghassan's columns
  (`results/VALIDATION_DECISIONS.md`); nothing is relabelled, re-preregistered
  or retrained until they are answered.

## Next actions (in order)

1. Drive C's ten rule numbers (`logs/DRIVE_C_CHECK_2026-10-19.md` section 9):
   Claude proposes, Jad and Ghassan fix them; Ghassan then drives C2 and C1 in the
   warmest hours, before G3 (2 November); then A and D if still needed.
2. The proposal's corrections (`docs/supervisor/2026-10-19_proposal-evaluation.md`
   sections 4 and 6): ask Dr. Hammam the deadline and which track's form; bring
   the literature review (Notion C9-03, 16–18 November) forward; restate the gap
   for one engine; the team decides on `CLAUDE.md`'s two-plant claim.
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

## Files outside git (where · last backup · manifest)

- Trained agents (`runs*/`) and the per-step records (`*_record.npz`) live on
  the machines that trained them. Jad's machine: a backup of 14 October, 4,391
  files, 2.5 GB, VERIFIED, with its `MANIFEST.csv` and `SHA256SUMS`; one copy,
  on the same disk; a Google Drive copy and a USB copy are still to make.
  Checked 15 October: its 978 agent files are unchanged on disk, and `C:` is
  still the only disk (session report of 15 October, 2.4).
- `GRAD-agent-backups/2026-09-23` and `2026-09-24` (`runs_c4`, sha-checked).
- Drive C's six CSVs and the evaluation workbook (19 October): Jad's Downloads,
  one copy; SHA-256 in `logs/DRIVE_C_CHECK_2026-10-19.md` section 7 and in
  `docs/supervisor/2026-10-19_proposal-evaluation.md`.

## References

`CLAUDE.md` (Training gate) · `README.md` · `results/README.md` ·
`STATE_HISTORY.md` · `HISTORY.md` and `CHANGELOG.md` (not written yet)

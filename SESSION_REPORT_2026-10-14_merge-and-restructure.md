# Session report — 14 October 2026: Phase 0, the merge, the documentation restructure

Jad, with Claude Code, one long session. Read this first to resume.

## 1. Plan v3 Phase 0 on Jad's PC (prompt `reorganization/CLAUDE_CODE_PHASE0_PROMPT.md`)

- Prompt v1's self-test: 135 passed, 2 failed (S18, A23: the CRLF guard; Git
  for Windows' grep strips CR, so `grep -q $'\r'` never matches). Diagnosed,
  sent to the chat that wrote the plan, which issued prompt v2 and v2 tools:
  139 passed, 0 failed, 6 skipped (the expected ones).
- Freeze hooks and deny rules installed, then removed later the same day
  when Jad dropped the rest of the plan's merge procedure.
- Snapshot `jad-wip-2026-10-14_164818` (bundle sha256 a0b75ec0...), BACKUP
  VERIFIED; Jad reviewed it («راجعت التقرير»).
- Training-files backup: `C:\Users\admin\Documents\New folder\jad-2026-10-14_172127`,
  4,391 files, 2.5 GB, VERIFIED, one copy (same disk). The npm cache was
  skipped (third-party, one file looked like a key).
- The whole record is OUTSIDE the repo: `C:\Users\admin\GRAD-phase0\`
  (`PHASE0_jad_DONE.md`, `PROGRESS.md`, `DECISIONS.md`, `REVIEW_jad.md`, logs).
- **Still Jad's, later:** a Google Drive and a USB copy of the backup, and
  step 0.6 (the snapshot to the team Drive) — `PHASE0_jad_DONE.md` lists how.

## 2. The merge (a normal merge, Jad's decision)

Jad's rule: Ghassan's work is the more accurate; delete nothing; every
conflict goes into a conflict file.

- Jad's work in progress committed as `efa3a3d` (141 files).
- `origin/GRA-2340394` (`c16b857`) merged into `JMF-2340550-results-tab` as
  `cc5468f`: 10 conflict blocks in 6 files, both sides of each in
  `conflict_2026-10-14.md`. Documents took Ghassan's text; code kept both
  where they add different things (taking his side alone would have broken
  the app), his side where they decide the same thing. One connecting edit:
  `agent_catalog.run_directory` resolves runs names through his `runs_dir`.
- Tests against a baseline run before the merge: `app.test_results` 1 -> 55
  failing, `app.test_agents` 21 -> 22, everything else unchanged, node 305 of
  305. Cause: his fingerprint schema 2 (8 October) against the results tab's
  schema 1. Not a resolution error (`HISTORY.md`, HIST-0001).
- Pushed to `main` on Jad's direct instruction: `3b6953a..39fce4b`
  (fast-forward), with the open items in `team/jad.md`.

## 3. The documentation restructure (plan v3 phase 4) — LOCAL, not pushed

Branch `docs-restructure-2026-10-14`, 16 commits (`bf8e0af`..`0d17aa2`) on
top of `main` `39fce4b`. Every move verbatim, gates after each step, ledger
`_merge_review/MIGRATION_LEDGER.md`.

- CLAUDE.md 3,588 -> 198 lines; CHECKPOINT.md 2,394 -> 73; handoff.md -> a
  12-line pointer.
- New homes: `STATE_HISTORY.md` (parts A-G), `docs/MISTAKES.md`,
  `thesis/LIMITATIONS.md`, `HISTORY.md`, `.claude/rules/{data,physics,training,app}.md`;
  `README.md` received the numbers, the phase table and the layout.
- `verify_docs.py` 74 of 74 (a new SIZE check: CLAUDE.md <= 300, CHECKPOINT.md
  <= 150); `drift_test.py` 16 of 16 on the final commit, as on main before.
- **Waits for Ghassan's OK** (patch 28 and the shared documents); Jad sent him
  the message. Push then: check `git ls-remote origin refs/heads/main` is still
  `39fce4b`, then `git push origin docs-restructure-2026-10-14:main`. Then a
  fresh Claude Code session at the root: `/context` must show CLAUDE.md under
  200 lines (gate G-CTX).

## 4. Against Ghassan's last push (asked by Jad at the end)

- GitHub's `GRA-2340394` is still `c16b857`, the commit that was merged.
- Every simulation file is byte-identical to his: plant.py, thermal.py,
  engine_env.py, derived.py, derive_params.py, fingerprint.py, random_road.py,
  wide_air.py, evaluate.py, train.py, train_all.py, step_record.py and data/.
  None of his files is missing. What differs is Jad's app, learning lab, plans
  and decks, the restructured documents and the two doc guards.
- His core checks on Jad's machine: see section 7.

## 5. Ghassan's data proposals (`c16b857`, `logs/DRIVE_PLAN.md`)

- **Drive C first** (knock), before the next training: C1, twenty or more
  steady loaded segments through the climb's own operating point; C2, twenty
  or more sudden pedal steps in a held gear; six channels, gearbox in M. It
  decides whether the car pulls timing on a load step (the spike X1's and X2's
  agents spend fuel avoiding), the knock knee, and spark under boost.
- **Its decision rule is a DRAFT**: Jad and Ghassan fix its numbers before the
  drive, as a preregistration is fixed before training.
- Then **drives A and D on one trip** (Taif): A for heat (plus ambient
  pressure), D for boost and the car's own torque request at sea level and in
  thin air.

## 6. Open, in order

1. Ghassan's OK, then push the restructure (section 3).
2. Drive C's decision-rule numbers, with Ghassan; then drive C.
3. The open items in `team/jad.md`: the results tab learns schema 2; the
   learning lab's `tests/test_catalog.py` pins move to the live plant.
4. The validation decisions (`results/VALIDATION_DECISIONS.md`); whether X1
   is the gate's step 5.
5. Jad's backup copies (section 1).

Machine notes: use `C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe`
(the project `.venv` is blocked by Application Control) with
`PYTHONIOENCODING=utf-8`; a full `drift_test.py` run takes about 50 minutes.

## 7. Ghassan's core checks on Jad's machine (on the restructure branch)

Run on 14 October on `8258a1a`, Python 3.12.10; every figure as Ghassan's
boxes record it:

- `python check_premise.py`: baseline 848.1 at 883 °C, current-grade cuts
  47.0 %, preview over current-grade -0.0 points.
- `python validate.py`: 8 of 11 quantities inside their band.
- `python test_reward.py`: 12 of 12, "All checks pass. The reward is safe to
  train against."
- No tracked file changed: `check_premise.py` rewrote `results/premise.json`
  byte for byte as Ghassan had committed it.

So the simulation on Jad's machine is Ghassan's, and nothing in it is
needed from him; what is needed is his OK on the restructure and the drive-C
rule numbers.

## 8. Closing, the same evening

- The restructure is on `main`: `39fce4b..cc338f8`, on Jad's go.
- G-CTX passed: in a fresh session, every memory file together came to 5.8k
  tokens; CLAUDE.md is 12,469 bytes (about 3k tokens) against 223,697 (about
  55k) before.
- Jad's folder `graduation project` now holds `GRAD-project` and
  `GRAD-agent-backups`; `reorganization/` (plan v3, the Phase 0 prompt) and the
  ZIP of Ghassan's branch went to the Windows Recycle Bin, at his request.
- The close routine writes a session report and rewrites CHECKPOINT.md; it
  never appends a session to CHECKPOINT.md or CLAUDE.md.

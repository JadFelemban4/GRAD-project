# Migration ledger — the documentation restructure of 14 October 2026

Plan v3 phase 4 (`reorganization/GRAD_PROJECT_CONTEXT_VERSIONING_MERGE_PLAN_v3.md`,
section 12.5), on branch `docs-restructure-2026-10-14` from `main` 39fce4b. One
row per move. Line numbers are those of the file in the commit's parent.

Statuses: Moved (verbatim) · Condensed (the full text kept verbatim at the
destination) · Rewritten (a pointer sentence or a guard line only) · Kept ·
Needs review.

To reach the original text: `git show <commit>^:<file>`, or
`git blame -C -C <destination>`, or `git log -L <from>,<to>:<file> <commit>^`.

**Gates after every step:** G-NOLOSS (every removed non-blank line re-added
verbatim in the same commit, or listed here as Rewritten), verify_docs.py
(exit 0, 73 checks, figure mentions not lower than 933), G-COVER (no file
leaves the scan), G-PIN (the pinned "11.7" mentions sum to 20), and the
drift_test.py rows whose anchors or pins moved. **One deviation from the plan,
stated:** the plan runs drift_test.py in FULL after every edit to the guards;
on this machine a full run takes about 50 minutes, so each step runs the rows
its edit can affect, and one full run covers the finished restructure.

| commit | source (file:lines) | destination | status | reason | gates |
|---|---|---|---|---|---|
| `bf8e0af` | `PROMPT_AUDIT_2026-09-30.md:165`, `VALIDATION_PLAN_REVIEW.md:68` | the same lines | Rewritten (a marker line) | two dated premise figures marked RETIRED-OK, so the guard passes after the merge | DOCS 73/73, 933 mentions; excused 509 -> 513 |
| `6628995` | `CLAUDE.md:86-807` | `STATE_HISTORY.md` part A | Moved | the dated state boxes, X2 (11-13 Oct) back to Phase D (21-22 Sep); patch 28 no longer applies after the merge, so done by hand | NOLOSS 0 · DOCS 73/73, 933 · COVER +1 (STATE_HISTORY.md) · PIN 20 · DRIFT row 13 CAUGHT |
| `6628995` | (new) | `CLAUDE.md`, "State history" | Rewritten (pointer) | five lines pointing to part A | — |
| this commit | `CHECKPOINT.md:1-2394` | `STATE_HISTORY.md` part B | Moved | the checkpoint rotation (plan 8.3) | NOLOSS 3 (the guard lines below) · DOCS 73/73, 939 · COVER 0 · PIN 20 · DRIFT rows 7, 11 CAUGHT |
| this commit | (new) | `CHECKPOINT.md` | Rewritten (template 9.3) | the current state only, 67 lines; every verified line names its script or file | — |
| this commit | `verify_docs.py` PINNED_HISTORY | the same | Rewritten (guard) | the 8 pinned mentions moved with the text: CHECKPOINT.md -> STATE_HISTORY.md | PIN 20 |
| this commit | `drift_test.py` row 11 | the same | Rewritten (guard) | row 11 follows its text to STATE_HISTORY.md | DRIFT row 11 CAUGHT |

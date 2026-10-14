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
| `f666778` | `CHECKPOINT.md:1-2394` | `STATE_HISTORY.md` part B | Moved | the checkpoint rotation (plan 8.3) | NOLOSS 3 (the guard lines below) · DOCS 73/73, 939 · COVER 0 · PIN 20 · DRIFT rows 7, 11 CAUGHT |
| `f666778` | (new) | `CHECKPOINT.md` | Rewritten (template 9.3) | the current state only, 67 lines; every verified line names its script or file | — |
| `f666778` | `verify_docs.py` PINNED_HISTORY | the same | Rewritten (guard) | the 8 pinned mentions moved with the text: CHECKPOINT.md -> STATE_HISTORY.md | PIN 20 |
| `f666778` | `drift_test.py` row 11 | the same | Rewritten (guard) | row 11 follows its text to STATE_HISTORY.md | DRIFT row 11 CAUGHT |
| `9518115` | `CLAUDE.md:690-1753` ("Twenty-five mistakes already made") | `docs/MISTAKES.md` | Moved | the story and evidence of every mistake | NOLOSS 2 (the guard lines below) · DOCS 73/73, 939 · COVER +1 (docs/MISTAKES.md) · PIN 20 · DRIFT row 7 CAUGHT |
| `9518115` | `CLAUDE.md:513-576` (mistake 17, inside "The numbers that matter") | `docs/MISTAKES.md`, between 16 and 18 | Moved | mistake 17 had been left among the numbers by an earlier merge | — |
| `9518115` | (new) | `CLAUDE.md`, "Mistakes already made: one rule each" | Condensed | one rule line per mistake (1-25, 13b, 17); the full text is docs/MISTAKES.md | — |
| `9518115` | `verify_docs.py` PINNED_HISTORY | the same | Rewritten (guard) | mistake 11's 2 pinned mentions moved to docs/MISTAKES.md: CLAUDE.md 3 -> 1 | PIN 20 |
| `4c91e79` | `CLAUDE.md:183-348` ("The numbers that matter": the scripts and what they print, the two app figures, the console-encoding note) | `README.md`, at its end | Moved | the live figures and the command behind each | NOLOSS 6 (the drift rows below) · DOCS 73/73, 939 · COVER +1 (thesis/LIMITATIONS.md) · PIN 20 · DRIFT rows 6, 12, 13 CAUGHT |
| `4c91e79` | `CLAUDE.md:349-406` (the VOID headline and the ablation identity) | `STATE_HISTORY.md` part C | Moved | void since 16 September; history | — |
| `4c91e79` | `CLAUDE.md:407-625` (the drive replays and the Taif drive; the rolling road; the towing standard) | `thesis/LIMITATIONS.md` | Moved | measured findings the thesis must state | — |
| `4c91e79` | (new) | `CLAUDE.md`, "The numbers that matter" | Rewritten (pointer) | five lines pointing to the three destinations | — |
| `4c91e79` | `drift_test.py` rows 6, 12, 13 | the same | Rewritten (guard) | each row follows its text: README.md, thesis/LIMITATIONS.md, and CHECKPOINT.md (the live premise) | DRIFT rows 6, 12, 13 CAUGHT |
| `8c6a759` | `CLAUDE.md` "Known limitations to state in the thesis, not fix quietly" (426 lines, with the knock model, the live app's limits and the 14 September audit) | `thesis/LIMITATIONS.md` | Moved | thesis material | NOLOSS 0 · DOCS 73/73, 939 · COVER 0 · PIN 20 · DRIFT row 14 CAUGHT (its other anchor stays in CLAUDE.md for now) |
| `8c6a759` | `CLAUDE.md` "Open, and honest about it" (84 lines: the discretisation of Phase D, D2 and C4; Phase F's threshold rule) | `thesis/LIMITATIONS.md` | Moved | measured limits | — |
| `8c6a759` | (new) | `CLAUDE.md`, "Known limitations, and what is open" | Rewritten (pointer) | four lines | — |
| `756bc7e` | `CLAUDE.md:92-121, 135-148, 166-182` ("Where every phase stands": the phase table, where the app sits, the manifest-versus-sample drive counts, what a passing project means) | `README.md`, at its end | Moved | live status | NOLOSS 6 (the drift rows below) · DOCS 73/73, 939 · COVER 0 · PIN 20 · DRIFT rows 4, 5, 14 CAUGHT |
| `756bc7e` | `CLAUDE.md:122-134, 149-165` ("What changed since 11 September", "What changed since 8 September") | `STATE_HISTORY.md` part D | Moved | history | — |
| `756bc7e` | (new) | `CLAUDE.md`, "Where every phase stands" | Rewritten (pointer) | four lines | — |
| `756bc7e` | `drift_test.py` rows 4, 5, 14 | the same | Rewritten (guard) | rows 4 and 14 (live figures) to README.md; row 5 (historical by design) to STATE_HISTORY.md | DRIFT rows 4, 5, 14 CAUGHT |
| `bf9afcd` | `CLAUDE.md:143-374` ("Repository layout") | `README.md`, at its end, beside README's own "Files" list | Moved | where everything is; nothing cut from either list | NOLOSS 3 (the guard lines below) · DOCS 73/73, 939 · COVER 0 · PIN 20 · DRIFT row 7 CAUGHT |
| `bf9afcd` | (new) | `CLAUDE.md`, "Repository layout" | Rewritten (pointer) | a pointer and the app's two structural rules, restated from the layout's closing paragraph | — |
| `bf9afcd` | `verify_docs.py` PINNED_HISTORY | the same | Rewritten (guard) | the layout's pinned mention moved to README.md: CLAUDE.md 1 -> 0 (key dropped), README.md 1 | PIN 20 |
| `0e512a6` | `CLAUDE.md:239-518` ("What to do next, in order": the live list of 30 September with Ghassan's note of 9 October, its parallel items, the C4 box, the lists of 22-23 September, the route Phase D took, the comparisons to improve, the app's backlog) | `STATE_HISTORY.md` part E | Moved | superseded and dated lists; the live list's six items became the Training gate | NOLOSS 0 · DOCS 73/73, 939 · COVER 0 · PIN 20 · no drift anchor moved |
| `0e512a6` | (new) | `CLAUDE.md`, "Training gate" | Rewritten | the six items verbatim, each with its status and closing commit, taken from Ghassan's note of 9 October; the plan's sentence "no training run while any item is open" was NOT added, because the live list's own words are the agreement and X1 and X2 trained with items 5 and 6 open on Ghassan's order | — |
| `0e512a6` | (new) | `CHECKPOINT.md`, next action 6 | Rewritten (pointer) | the parallel items of 30 September and the app's backlog, with "check an item before taking it up": the plan put "In parallel" in CHECKPOINT.md, but X1 and X2 overtook parts of it | — |
| this commit | `CLAUDE.md:191-238` ("When a new drive CSV arrives") | `.claude/rules/data.md` (paths: the data scripts and `logs/**`) | Moved | a procedure, loaded when a data file is read or edited; 65 lines with its header, over the plan's 40 because it is verbatim | NOLOSS 0 · DOCS 73/73, 939 · COVER +1 (.claude/rules/data.md) · PIN 20 · no drift anchor moved |
| this commit | (new) | `CLAUDE.md`, "When a new drive CSV arrives" | Condensed | the two commands and the one fact that matters before anything runs (a drive re-derives the plant); running a script does not load a rules file | — |

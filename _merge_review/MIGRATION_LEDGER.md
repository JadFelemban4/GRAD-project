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
| `30e9e4c` | `CLAUDE.md:191-238` ("When a new drive CSV arrives") | `.claude/rules/data.md` (paths: the data scripts and `logs/**`) | Moved | a procedure, loaded when a data file is read or edited; 65 lines with its header, over the plan's 40 because it is verbatim | NOLOSS 0 · DOCS 73/73, 939 · COVER +1 (.claude/rules/data.md) · PIN 20 · no drift anchor moved |
| `30e9e4c` | (new) | `CLAUDE.md`, "When a new drive CSV arrives" | Condensed | the two commands and the one fact that matters before anything runs (a drive re-derives the plant); running a script does not load a rules file | — |
| `8e0bdc9` | `CLAUDE.md:1-11` (title) and `12-54` ("Before anything else: ask who you are talking to") | `STATE_HISTORY.md` part F | Moved, and Condensed in CLAUDE.md | the full original text of the two sections CLAUDE.md now keeps short, with the same meaning | NOLOSS 52, all accounted for: 48 are lines written during this restructure (the pointer sections of earlier steps, folded into the map; the Training gate, rewrapped with its statuses on each item's first line; its original list is part E), and 4 are original lines whose copies already moved (the headings "The numbers that matter" and "Repository layout", with their sections, in 4c91e79 and bf9afcd; two "---" separators) · DOCS 73/73, 939 · COVER 0 · PIN 20 · no drift anchor in CLAUDE.md |
| `8e0bdc9` | (new) | `CLAUDE.md` | Rewritten | the assembly of plan section 4.3: title, who, the project, the hard constraint (with the app's two rules), the Training gate, the rules for a reported experiment (plan 6.4, 6.6, 7), the mistakes, the conventions (kept), the new-drive lines, where things go, the map, the tone note. 198 lines | — |
| `6094ada` | (new) | `.claude/rules/physics.md`, `training.md`, `app.md` | Rewritten (new procedure files, plan section 4.4) | procedures and pointers only, each under 40 lines; every statement in them is taken from text that already stood in the project (the conventions, the repository layout, `train.py`, the plan's G-LAB gate) | NOLOSS 1 (the CHECKPOINT line below) · DOCS 73/73, 939 · COVER +3 · PIN 20 |
| `6094ada` | `CHECKPOINT.md` next action 4; `team/jad.md` | the same | Rewritten | a third open item from the merge, measured today: the learning lab's `tests/test_catalog.py` pins the plant of 30 September and fails one of its ten tests | — |
| `359b9b0` | `handoff.md:1-466` | `STATE_HISTORY.md` part G | Moved | the plan's open decision 2, put to Ghassan the same day: handoff.md becomes a pointer, so the 23 files that name it still lead somewhere | NOLOSS 0 · DOCS 73/73, 939 · COVER 0 · PIN 20 · no drift anchor in handoff.md |
| `359b9b0` | (new) | `handoff.md` | Rewritten (pointer, 12 lines) | CLAUDE.md, CHECKPOINT.md and README.md, in that order | — |
| `9cbd7b0` | (new) | `HISTORY.md` | Rewritten (new index, plan section 9.1) | the 48 dated documents (date from the name or the first commit, title from the file's own first line), STATE_HISTORY.md's parts, the backups outside git, and HIST-0001: the merge's conflict git could not see | NOLOSS 0 · DOCS 73/73, 939 · COVER +1 · PIN 20 |
| `8309d66` | (new) | `verify_docs.py`, check SIZE | Rewritten (guard, gate G-SIZE) | fails if CLAUDE.md passes 300 lines or CHECKPOINT.md 150; shown to fail on a scratch copy padded to 318 lines | DOCS 74/74 (73 + SIZE), 939 · NOLOSS 0 · COVER 0 · PIN 20; the full drift_test run follows on this commit |

## The result

| | `main` 39fce4b, before | `8309d66`, after |
|---|---|---|
| CLAUDE.md | 3588 lines | 198 lines |
| CHECKPOINT.md | 2394 lines | 73 lines |
| handoff.md | 466 lines | 12 lines (a pointer) |
| verify_docs.py | 72 of 73 (two dated figures; fixed first, `bf8e0af`) | 74 of 74 (73 + SIZE), 939 figure mentions |
| files in the scan | 274 | 282 (none left; 8 joined) |
| pinned "11.7" mentions | 20 | 20 |
| drift_test.py, full run | 16 of 16 CAUGHT | 16 of 16 CAUGHT, each row at its text's new home |

Every removed non-blank line of CLAUDE.md, CHECKPOINT.md and handoff.md is in
the repository verbatim at its destination, except the lines listed as
Rewritten above. G-CTX, after the push (`cc338f8`): Jad ran `/context` in a fresh Claude Code
session at the repository root. Every memory file together, CLAUDE.md
included, came to 5.8k tokens; CLAUDE.md itself is 12,469 bytes, about 3k
tokens, against 223,697 bytes, about 55k, on `main` before. PASS.

# Session report — 10 to 11 November 2026: the top 40 sources, the paid sources, every branch merged

Jad's session. It worked on `JMF-2340550-literature` (from `origin/GRA-test` at
`a60dcae`), then merged every branch into `JMF-2340550-merge-2026-11-11`, which
`GRAD-project` is on since 11 November. Nothing in the physics, the data or the
training changed. New: `docs/literature/TOP40.md`,
`docs/literature/PAID_SOURCES_CHECK.md`, `conflict_2026-11-11.md`, this report and
`NEXT_SESSION_2026-11-11.md`; edited: `CHECKPOINT.md`, `STATE_HISTORY.md` (parts
AN to AP), `HISTORY.md`.

## 1. What was done

- **The top 40 sources** (`docs/literature/TOP40.md`, `9738da8`): 40 of the 183 in
  `docs/literature/READING_LIST.md`, for the two chapters Jad asked for: 19 for
  the Research Methodology, 21 for the Literature Review, in sections M1-M7 and
  L1-L9. Four selections, each through one lens (methods, the gap, an examiner,
  realism), then a vote, a merge, a check of every quoted figure against the list
  and the project files (all matched), and a critic. 27 picks had 4 votes, 9 had
  3, 4 had 2; all 40 are MUST on the list; price and access decided no place.
  Each pick carries why it is in and what to read it for. A private web page of
  the same list was made for Jad; it is not in the repository.
- **Ghassan's paid sources checked** (`docs/literature/PAID_SOURCES_CHECK.md`,
  `f7a5a21`, `b3158fd`). His voice note, transcribed locally (Whisper large-v3),
  asked to check that the paid sources in his zip are there and say what is
  missing, and to read nothing yet. Two zips: the second (11 November) adds C47
  and is otherwise byte-identical to the first. 9 of the 12 paid items of the 40
  are present, each with a matching title and page count. Missing: D01 (ASME
  V&V 20, $72), A03 (Tomizuka & Whitney 1975, $25; the zip has the 1974 thesis
  A06 instead) and C36 (Heywood's textbook). The first version's paragraph on
  extra files was deleted at Ghassan's request.
- **Every branch merged** (`923c2c4` on `JMF-2340550-merge-2026-11-11`):
  `origin/GRA-test` (the same commit as `origin/Mohammed`, and already holding
  `JMF-2340550-step3-fix`), the three literature commits, `origin/khaled` (clean)
  and `JMF-2340550-anatomy-housing`. Two conflicted documents, resolved by the
  rule of 14 October, both sides in `conflict_2026-11-11.md`. Every other branch,
  local or on GitHub, was already in `main`; none has a commit the merge lacks.
- **One project folder** (Jad, 11 November). The worktrees
  `GRAD-project-literature`, `GRAD-project-merged` and `GRAD-project-step3` were
  removed and `GRAD-project` was switched to the merge branch; its ignored
  files (`runs*`, `node_modules`, `.venv`) are untouched. The step3 worktree held
  the lock's environment (Python 3.13.2, torch 2.14.0+cpu, sb3 2.9.0,
  gymnasium 1.3.0, numpy 2.5.3; 1.2 GB, made by `tools/device_step3.sh` on 2
  November): it was moved, not deleted, to `grad-venv-lock-3.13.2` in Jad's user
  folder, and runs there. `GRAD-agent-backups` stays: agent backups, not a copy
  of the project.

## 2. What was found and left alone

- **The merge broke one caller without a text conflict** (mistake 25).
  `Explanatory Simulation/figures/housing-lag/export_params.py` calls the plant
  as `main` had it (no engine); `GRA-test` made the engine a required argument on
  20 October. So `tests/test_housing_figure.py`'s
  `test_params_match_the_live_plant` errors on the merged tree. The figure still
  builds from its committed `params.json`; whether those numbers match the
  merged plant is unchecked until the exporter is ported
  (`conflict_2026-11-11.md`, last section; `CHECKPOINT.md` item 4). Not fixed: Jad's
  call.
- Citing the thesis A06 in place of A03 is the team's call
  (`PAID_SOURCES_CHECK.md`).
- In a fresh worktree 12 of the lab's Node test files fail with
  `ERR_MODULE_NOT_FOUND`: no `node_modules`, not the code. With the main
  folder's `node_modules` linked for the run, 146 of 147 pass.

## 3. Checks at the close

- `python verify_docs.py` on the merged tree: all 170 checks pass (1157 figure
  mentions), as on `GRA-test`; again at the close, read by its exit code (see
  the commit).
- The learning lab on the merged tree (Python 3.12.10, Node 24.18.0): Python 35
  run, 3 failures as on `GRA-test` alone (31 run there) and 1 error, the
  exporter; Node 147 run, 146 pass, the one failure as on `main`; `tsc` no error;
  `figures/housing-lag/build.mjs` builds.

## 4. Next

Jad's plan: a shared tracker for the papers, Google Sheets or Notion, one row per
paper where every member writes what we learned from it and whether it bears on
the claim, visible to everyone. It follows Dr. Hammam's lecture on reading and
classifying papers (research methods, chapter 3, two parts, in Jad's folder of
project meetings); Jad has watched part 1. The prompt: `NEXT_SESSION_2026-11-11.md`.
Still waiting on Jad: the exporter's port, and whether to push this branch.

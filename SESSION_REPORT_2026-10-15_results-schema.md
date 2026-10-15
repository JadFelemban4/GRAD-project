# Session report — 15 October 2026: the results tab reads each file by its own fingerprint schema

Jad, with Claude Code. Branch `JMF-2340550-results-schema2`, from `main` at
`4d6d3f2`. Not pushed: Jad, «ابدا بالاصلاح بعدين نشوف فين نرفع».

## 1. The fix: the open item of 14 October in `team/jad.md`

**The cause, measured before any change.** After the merge of Ghassan's branch
(`cc5468f`) the results tab hashed every result file by fingerprint schema 2:
four plant files, `derived.py` among them, and the source-text code hash. The
24 files of Phase D, D2 and C4 were written under schema 1: `plant.py`,
`thermal.py` and `engine_env.py`, the code hash being `ast.dump` of the syntax
tree. Schema 1's rule, run on each file's own commit from git, gives back what
the files record:

| files | plant_sha | plant_text_sha | road_sha |
|---|---|---|---|
| `d2_seed*`, `c4_seed*` (16) | `b5a3069f32a83754` | `e37311f29851876c` | `1a29dc46db24f233` |
| `phase_d_seed*` (8) | `b5a3069f32a83754` | `1db9acf0be408e74` | none (fixed road) |

`b5a3069f32a83754` is also the plant of the tag `sep17-before-merge` by the
same rule.

**The change.** `ca2cd73`: `app/results_provenance.py` reads a block's schema
(`derived_sha` present means schema 2), hashes a schema-1 file's plant and road
by schema 1's rule on both sides, and names its tag by that rule. `2fd9aed`:
the page says which schema made the two hashes it shows, because this tree by
schema 1's rule (`b22873b5ccfb947b`) is not the plant hash the page's header
gives by today's rule (`3c48890dd15bc116`).

**What the tab says now**, for Phase D, D2 and C4: made on another plant, the
plant of `sep17-before-merge`. They differ on `plant_sha`, and D2 and C4 on
`scenario` as well (`random_road.py` changed on 8 October).

**Tests**, Python 3.12.10:

| suite | main `4d6d3f2` | after `2fd9aed` |
|---|---|---|
| `python -m app.test_results` | 55 of 120 failing | 1 of 124 failing (needs `pwsh`) |
| `python -m app.test_agents` | 22 failing | 22 failing (section 2.1) |
| `python -m app.test_simulation` | 1 failing | 1 failing (section 2.2) |
| `python -m app.test_replay` | — | 49 of 49 |
| `test_results_comparisons`, `_sets`, `_records`, `_graphics` | — | pass |
| `node --test static/sim` | 305 of 305 | 306 of 306 |
| `python verify_docs.py` | — | 74 of 74 |

## 2. Found on the way, not fixed

1. **The agents page, `app.test_agents`: 22 failing, of which the 14 October
   merge added one.** Measured on this branch, the same as on `main`: 19 come
   from the page refusing the old agents on today's plant ("plant mismatch:
   plant_sha, derived_sha, scenario"); the suite's fixtures copy
   `runs_c4/*/meta.json`, written on the sep17 plant, so even its synthetic
   agents are refused. One of the 19 is the "plant_sha alone" line the merge
   added. One needs `pwsh`, one is the asset check of 2.2
   (`sim/agents.mjs?v=20261009`), one is the catalog fixture's shape. The
   page's own mismatch lines also compare a schema-1 `meta.json` with today's
   hashes, the same cross-rule comparison this session fixed in the results
   tab. A separate item, for the agents page.
2. **`app.test_simulation`: 1 failing on `main`.** The asset check looks for
   `sim/main.mjs?v=20261009` as a file under that full name. Recorded before the
   merge only in `efa3a3d`'s commit message.
3. **`train.py` does not close X2's directory.** Its `CLOSED` list has
   `extremes_dt1` (X1, added in X2's preregistration commit `06f4686`, commented
   "closed 9 Oct 2026, after its result"), but not `wideair_dt1`, though X2's
   result was published on 13 October. `train.py` is Ghassan's file: for him.
4. **The trained agents are backed up on one disk only.** Checked today: the 978
   files under `runs/`, `runs_d2/`, `runs_c4/` and `runs_sixspeed_18sep/` are
   unchanged since the backup of 14 October (none is newer than its
   `MANIFEST.csv`). That backup and `GRAD-agent-backups/` are on `C:`, the only
   disk; no USB disk and no Google Drive app on this machine today. The backup
   sits in `Documents\New folder\jad-2026-10-14_172127`, outside
   `GRAD-agent-backups/`. `PHASE0_jad_DONE.md` says to re-run "step 0.4 of the
   prompt" for the next copies, and that prompt went to the Recycle Bin with
   `reorganization/` on 14 October; a plain copy checked against the backup's
   `SHA256SUMS` does the same job.

## 3. Still open from the merge

- The learning lab's pins (`team/jad.md`, the third item).
- Where this branch goes: Jad decides.

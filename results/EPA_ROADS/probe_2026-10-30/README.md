# The ceiling probe of 30 October 2026 (section I of `results/VALIDATION_DECISIONS.md`)

These scripts asked one question before any road is drawn: can decision 34's roads reach a
preview ceiling of 2 MEI on all four frozen plants, using only the agent's own levers? They ran
on this laptop at `48435a2` from the agents' scratchpad. They are copied here verbatim, so the
paths written inside them (`REPO`, the scratchpad) are those of that run, and stored as
`.py.txt` so that no repository scan reads them as project code (`test_engine_threading`
refuses their default arguments there; rename one to run it). No script opened a
held-out row, a `logs/epa/*` table or any `data/engines/*/epa_*.csv`: the audit hook in `lib.py.txt`
refused each of them. `repo_files_opened.txt` lists every repository file that was opened.
Nothing here trains, calibrates or validates.

| file | what it is |
|---|---|
| `lib.py.txt` | the road family, the policies (current-grade, (a), (b), (c)) and the audit hook |
| `repro.py.txt`, `repro_an.py.txt` -> `repro.txt`, `repro_an.txt`, `repro.json` | the B58's locked climb against `results/premise.json` and section G's rows |
| `c5tau.py.txt` -> `c5tau.txt`, `c5tau.json` | τ per engine, by the frozen definition |
| `grid.py.txt` -> `grid_log.txt`, `table.json`, `table_full.csv`, `table_pilot.json` | the grid: 108 families × 4 engines × 6 H × variants × two readings |
| `analyse.py.txt`, `summary.py.txt` -> `analyse_stdout.txt`, `summary.txt` | the families kept and dropped, and the best per engine |
| `headstart.py.txt` -> `headstart.txt`, `headstart.json` | the head-start part of each saving |
| `dtcheck.py.txt` -> `dtcheck_*.txt`, `dtcheck_*.json` | dt 1 s against 0.5 s on one family |
| `t_time.py.txt` | the time of one run |
| `calc/` | the design's slot bounds, the savings at matched H/τ and the three aggregations (rows 101-103) |
| `review/` | the scientific review's power arithmetic and blind-timed check (rows 103, 113) |

What was left out: `runs/` (107 MB of per-run arrays), `repro_traces.npz` and the per-worker
open logs, whose union is `repo_files_opened.txt`. All three stay in the scratchpad of the
session that ran them, and none of them is cited by section I.

# hw_opt: the tuned hand-written lambda strategies (row 153 (1))

Written by the AI agents on 15 November 2026 for D148 (`results/VALIDATION_DECISIONS.md` section S, row 153 (1)).
Every number below is printed by a committed file, cited by file and line. File times and the session's own record
of its commands are named as such; no committed file prints them.

It describes the B58 model on decision 34's twenty roads. It reads no agent, decides nothing, and is never a bound
on d (its own label, `hw_opt.py.txt:202-203`).

## What was run, by what, and where

- **The script.** `hw_opt.py.txt` is `hw_opt.py`, renamed so that no scan of committed `.py` files runs it. Its
  docstring gives its three commands (`hw_opt.py.txt:3-6`). It ran outside the repository, in a folder of the
  agents' scratchpad, and wrote only beside itself (`:8`, `:36`). It puts the clone first on its path and works
  from it (`:25-28`), reads the twenty roads through `fingerprint.d34_roads` (`:46`), and reuses
  `roads_ceiling.py`'s runner unchanged, on the frozen plant only (`:126`).
- **The clone.** `C:\Users\badcl\grad_hw` at HEAD `0329456` (Ta), with an empty `git status --porcelain`
  (`control_record.txt:18-19`).
- **The plant.** The B58's plant_sha `36655cab94800e30` there (`control_record.txt:20`), the plant_sha B1 printed on
  Jad's PC (`results/B58H_DESIGN/d148_figures.txt:154`).
- **The environment.** Python 3.13.2 and NumPy 2.5.3 on this laptop (Windows build 26200, an Intel processor),
  as `control_record.txt:21` prints it. That line was printed when the control was re-printed on 15 November
  (`:1`). The session's record of its commands shows the same interpreter path, the project's `.venv`, for the
  run on 14 November; run.log itself prints no environment.
- **The settings.** 41 on each road, 820 runs in all: current-grade and the baseline ECU; sighted, 12 at each r;
  blind, 15 (`results/B58H_DESIGN/d148_figures.txt:152-153`, which counts them from `hw_opt.py.txt`'s
  FRACS, DELTAS, DELAYS and RATIOS and from `runs.jsonl`). The families are defined in the docstring
  (`hw_opt.py.txt:13-17`).

## When

- On 14 November 2026: `hw_opt.py` was written at 16:08 AST, and the run started at 16:11 AST (the session's
  record of its commands). The control's 12 runs had run first, so the run started with "820 runs asked, 12
  cached, 808 to run at 14 jobs" (`run.log:1`). The 808 runs took 136.5 min (`run.log:59`). `runs.jsonl` and
  `run.log` were last written at 18:27 AST (file times).
- **It started before decision 12 was answered.** The decision sheet that holds decision 12's answer was last saved
  at 17:13 AST on 14 November when the rows were drafted (a file time read then, as row 153's Disclosed sentence
  records). The sheet has been saved again since, so that time can no longer be read from it.

## The control

`hw_opt.py control` re-ran current-grade, the baseline ECU, (a) at both r, (b) and (a_b) on roads 0 and 1 and
compared their damage in both readings, fuel and return with `results/EPA_ROADS/roads.json`'s per-road values
(`hw_opt.py.txt:167-190`). Re-printed from the cache on 15 November, running nothing ("12 runs asked, 12 cached, 0
to run", `control_record.txt:2`), it prints "CONTROL: largest difference from roads.json 0.000e+00 -> PASS"
(`control_record.txt:15`) and exits 0 (`:16`).

## A change to hw_opt.py after the run

At 19:11 AST on 14 November, after the run had ended, the agents edited two places in `report()`, which only
reads the cache:

- `blind_at` (`hw_opt.py.txt:250-251`). As run, past the blind front's last point it returned that point's
  saving: `if x >= fb[-1][0]: return fb[-1][1]`. Now it returns `None` there ("not compared").
- the gaps line (`:259`), which now skips a sighted point whose `blind_at` is `None`.

Nothing else changed. The session's record of the file holds one Write and three edits. Replayed in order, they
give `hw_opt.py.txt` byte for byte, so the script as run is this file with the old text of those two places. The
only edit before the run, made before the control, added `roads_ceiling`'s open-file guard to the entry point
(`:275-276`).

`hw_opt.py report` was then run again from the cache at 19:11 AST, and it rewrote `hw_opt_report.txt` and
`hw_opt_result.json`. Its report equals, line for line once line ends are ignored, the report the run printed
at 18:27 (`run.log:60-177` against `hw_opt_report.txt:1-118`). The two cannot differ. Every blind front ends
at 6.55 % extra fuel (`hw_opt_report.txt:49`, `:55`, `:108`, `:114`), and every sighted front ends at 3.96 % or
less (`:50`, `:52`, `:56`, `:58`, `:109`, `:111`, `:115`, `:117`). So no sighted point lies past the blind front's
end, where the two versions differ.

## What it prints, and where to read it

`hw_opt_report.txt` gives the no-knock reading first (`:2-59`) and the with-knock reading beside it (`:61-118`).
For each setting it prints the saving over current-grade in the mean form and in `evaluate.py`'s form, the extra
fuel and the highest peak in C. Then come each family's front, and the largest sighted-minus-blind saving at
equal extra fuel. In that comparison the blind front is a straight line between its own tuned points, and past
its last point it is not compared (ASSUMED: a mix of two blind settings reaches the line). The largest
sighted-minus-blind saving at equal extra fuel, in points of cut over current-grade:

| reading, form | r = 0.5 | r = 1.5 |
|---|---|---|
| no knock, mean form | +0.258 (`hw_opt_report.txt:51`) | +0.577 (`:53`) |
| no knock, `evaluate.py`'s form | +0.573 (`:57`) | +1.104 (`:59`) |
| with knock, mean form | +0.134 (`:110`) | +0.551 (`:112`) |
| with knock, `evaluate.py`'s form | +0.551 (`:116`) | +1.083 (`:118`) |

`hw_opt_result.json` holds the same tables and fronts as JSON. Each line of `runs.jsonl` is one run: its setting
and its totals (`hw_opt.py.txt:131-133`).

## The files

- `hw_opt.py.txt`: the script, as described above.
- `runs.jsonl`: the 820 runs, the cache that `report` and `control` read.
- `run.log`: the run's printout, its progress and then its report.
- `hw_opt_report.txt` and `hw_opt_result.json`: the report, re-written at 19:11 AST from the cache.
- `control_record.txt`: the control, re-printed from the cache, then the clone's HEAD, its status, the B58's
  plant_sha there and the environment.
- `verify/`: the review checks written by the agents on 14 November after the run, each renamed `.py.txt`:
  `recompute.py.txt` (a recomputation from `runs.jsonl` that does not import `hw_opt.py`), `skeptic.py.txt`,
  `gaps.py.txt`, `union.py.txt`, `extra.py.txt`, `rets.py.txt`, `knockoff.py.txt` and `knockoff_report.py.txt`.
  Only one printout of theirs was kept: `knockoff.py`'s re-run of a subset of the settings with the study's
  reward, without the knock term, in `knockoff.jsonl` and `knockoff.log` ("202 to run at 16 jobs",
  `knockoff.log:1`; "202/202 32.4 min", `:14`). The other checks' printouts were not saved, so this folder
  quotes none of their numbers.

The summary written beside these files on 14 November (`RESULT_SUMMARY.md`) is not committed. It quotes numbers
worked out by hand from `runs.jsonl`, and rule 1.9 lets no committed document do that.

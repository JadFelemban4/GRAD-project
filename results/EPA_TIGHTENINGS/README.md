# results/EPA_TIGHTENINGS: row 104's tightenings of L1 and E8

The tightenings of section I of `results/VALIDATION_DECISIONS.md` (row 104, with row 107 (4) for the B58's E8
band), measured on the B58 plant only, on decision 34's roads as first drawn, with hand-written policies and no
agent. The code is `epa_tightenings.py`, a module of its own that imports the roads module and that no module
roads.json hashes imports (row 121 (2)). ORDER step 8 (`docs/build_step_2/ORDER_TO_TRAINING.md`) runs it, last
before the first arming. The writer refuses code that is not committed, so the code is committed first and the
record it writes is committed after it. Run every command with `.venv/Scripts/python.exe -B` and
`OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`, after deleting every `__pycache__` folder in the tree.

This folder holds no figure of its own. The record itself is one level up, at `results/EPA_TIGHTENINGS.json`,
the path `validate_epa.py` reads (`TIGHTENINGS_REL`).

| file | what it is | written by |
|---|---|---|
| `../EPA_TIGHTENINGS.json` | the tightenings record, written once and never edited: the layout `validate_epa.load_tightenings` takes, with every measurement beside it | `python -B epa_tightenings.py run --jobs J`; after a roads stop, `python -B epa_tightenings.py stopped` instead (row 129 (4), below) |
| `timing.json` | one SYNTHETIC road of the design through the whole chain, timed at J jobs, with the real run's wall time predicted from it (mistake 22) | `python -B epa_tightenings.py timing --out results/EPA_TIGHTENINGS --jobs J`, from committed, clean code |
| `README.md` | this file | by hand |

## When it may run, and what it refuses

`run` writes the record only when all of these hold, checked before anything is computed and again before the
write: the record is absent and was never committed; the Python running it writes no bytecode (`-B`); the code
(the module's import closure, the step-2 code that arm hashes, and the B58's plant files) is committed and clean,
and no compiled file stands beside it in a `__pycache__` folder (`-B` stops Python writing those, not reading
them, and git does not see them); the run's data inputs (the contract, `results/car_spark_boost.json` and the
pinned `results/ENGINE_THRESHOLDS/ecu/`) are committed and clean; every output of the roads step under
`results/EPA_ROADS/` is committed and clean; `roads.json` is committed at HEAD, is the record its attempts log's
one roads outcome names by roads_sha, holds the roads_seed the reveal gives and the hash lines of the roads
commit; its roads are the tightenings' (twenty, road k paired with `evaluate.EPISODES[k]`, the B58's tau and H
on the plant row 102 names); and every file, plant and version roads.json hashes is as it recorded
(`epa_roads.verify_record`). During the run, ecu_shift's above0 and every K3 knee are compared with the pinned
files as soon as their locked-climb task ends (those tasks run first), and a difference stops the run before the
road runs it would set. Before the file is linked into place it is read back by
`validate_epa.load_tightenings` and checked by `validate_epa.tightening_problems` against the contract's shift
grid and the B58 as built; a refusal leaves nothing.

`synthetic` and `timing` run the same chain on SYNTHETIC roads from `epa_roads.generate` with a SYNTHETIC seed,
which is never roads_seed, and write outside every git work tree (the timing record may also be written here,
from committed, clean code).

## When the roads stop (row 129 (4))

If the roads stop for anything but a coding defect (row 103 (3)), no road set exists and the tightenings have
nothing to be measured on. The only such stop is a reveal that does not match its hash line, which
`epa_roads.py draw` logs before roads_seed is computed and after which it refuses every attempt; a withheld or
lost integer is entered there as 2**128, typed as its decimal, `340282366920938463463374607431768211456` (the
text `2**128` is refused before anything is logged, and the step does not end), so that the draw itself logs the
stop, and the commit that records it says whose integer it was. Run 2 still runs, with L1 and E8 untightened:
`python -B epa_tightenings.py stopped`
writes `../EPA_TIGHTENINGS.json` once, in the same layout, with roads_sha `none`, roads_seed −1 and seed_kind
`NONE`; L1's slope, set, knock reading and shift are the contract's `knee_shift.largest`, so L1's held-out R is
the contract's on every engine; E8's two roads tables are the contract's own locked-climb tables
(`ecu_strategy_b58`), verbatim, so P is the contract's at every shift; the B58's E8 band is the locked-climb
reading, built by the same code as `run`'s, and so are the provenance and the read-back before the write. It
refuses unless the record is absent and was never committed, `roads.json` is absent and was never committed, the
attempts log is committed at HEAD, never rewritten, holds no roads outcome and ends in exactly one stop that is
not a coding defect, right after its own start line, whose logged reveals, checked again against the roads
commit's hash lines, do not both match, every start line being one the draw writes (numbered 1, 2, ... in order,
two integers of at least 2**128, the match the draw computed, the roads commit's hash lines); HEAD is origin's
GRA-test as the remote reports it (`epa_roads.remote_state`: so pull, push the stop, and run it on the branch's
tip); and the code, its data inputs and `results/EPA_ROADS/` are committed and clean, with no compiled file
beside the code and Python run with `-B`. The shared-branch gate is there because a clone left at the roads
commit can run the draw and log a stop of its own while GRA-test already holds a drawn set (a review of
31 October measured it), and a record written there would give Run 2 its least strict L1 and E8 beside a set
that exists. One case is let through and named, not refused: an earlier attempt that logged both right integers
and crashed after roads_seed was computed, followed by an attempt that stopped. No road set exists then, but
the seed can be computed from the log; row 129 (4) discloses that either person could force a stop after the
reveal, so whether to refuse it is the team's call. The record lists those attempts
(`no_roads.earlier_attempts_both_matching`) and the summary prints them. Every summary it prints labels L1 and
E8 "untightened: no roads (row 103 (3))". While `roads.json` is absent, `test_epa_tightenings.LiveRecord` and
`test_epa_roads.py`'s Tightenings class accept this record and no other (`epa_tightenings.stopped_record_problems`,
which also reads origin's GRA-test, so it needs the network and a fetched clone).

Two things the arming does not do, so they are done by hand after a stop:

- `validate_epa arm` takes any tightenings record in the layout while `roads.json` is absent (MEASURED by the
  review: a NONE record one ulp tighter, and a REAL or a SYNTHETIC one, all armed). Before `validate_epa arm`,
  run `python -B -m unittest test_epa_tightenings.LiveRecord test_epa_roads.Tightenings` on the committed
  record; both must pass. They skip only while `../EPA_TIGHTENINGS.json` is absent, so once it exists a skip is
  a failure.
- `validate_epa`'s outputs record the tightenings' path, sha_text, commit and plant, not their seed kind, so no
  Run 2 output says the tightenings are absent. When the committed record's `seed_kind` is `NONE`, every Run 2
  report names L1 and E8 "untightened: no roads (row 103 (3))", taken from the record (`untightened`,
  `L1.label`, `E8.label`), and pastes the summary `stopped` printed.

Every subcommand installs the roads module's audit hook first, in every worker too: it refuses any open of
`logs/epa*`, `data/engines/<id>/epa_*`, `results/EPA_VALIDATION` and any `.csv`. No EPA table and no held-out row
is read. The record lists every repository file the run opened.

## The record

- The layout `validate_epa.py` fixes (WP3_INTERFACES 7.5): `schema` `epa-tightenings/1`, `plant` `b58`,
  `roads_sha` (roads.json's sha_text), `roads_seed`, `L1` with `slope_points_per_K`, `set`, `shift_k` and
  `damage_reading`, `E8` with `k3_pair_change_vs_lambda_roads` and `k3_pair_change_vs_spark_roads` on the
  contract's grid of `ecu_strategy_b58`, and `provenance` with `commit`, `code_sha_text`, `plant_sha` and
  `engine_sha`, the last two as `validate_epa.b58_identity` builds them for the arming.
- Beside the layout, read by no other code: in `L1`, every per-road damage at every knee shift and reading,
  the pair at each H, every slope, the horizons and the re-score's worst difference from each run's own damage;
  in `E8`, each run of the grid with its K3 knee and the seconds it was set at, the pinned knee it must equal,
  the medians and the pair in both readings, on how many roads the reactive policy's damage equals the neutral
  one's (where reactive never acts, the head-start pair is current-grade's cut alone) and the neutral peak
  housing against the knee, the seconds the nominal trace spends above the B58's knee, and `b58_u_val_kappa`,
  row 107 (4)'s band with the locked-climb-only reading beside it and both readings again at the sign of E8's
  own statistic (model minus car, descriptive); the contract's two sha_text; the pinned folder's hash before
  and after; in the provenance, whether the code and the data inputs were clean and the compiled files found
  beside the code; the timing, each task's own seconds among it; the files opened.

## How each part is measured

- **The scoring** is `evaluate.py`'s: a policy's cut is the median damage over the twenty roads against the
  neutral policy's median ("baseline ECU"), and a pair is the difference of two cuts
  (`roads_ceiling.aggregate`'s evaluate_form). The damage is read with and without the knock term.
- **L1.** The preview pair is S2a's predictive policy at H minus current-grade: `check_premise.p_predictive`
  itself, reading the largest grade within the next H seconds in place of its two fixed samples. H is the
  B58's two horizons from roads.json's table of H (row 102). Each policy runs once per road and H; the per-step
  records are re-scored at the B58's knee shifted over `thresholds/knee_shift.py`'s grid, and the slope recorded
  is the largest over both H, every shift and both readings (row 104), the first in that order on a tie.
- **E8.** Every shift of the contract's grid is its own run, through `k3_knee.shifted_ecu`, `k3` and
  `with_knee`, the knee re-set on the locked climb as `thresholds/ecu_shift.py` sets it, and compared with the
  pinned `results/ENGINE_THRESHOLDS/ecu/k3_<name>.json`; `ecu_shift.one` and `run_all` are never called, and that
  folder is never written. The relative change of the head-start pair is `thresholds.contract.response` on the
  medians, both readings, the larger with its sign.
- **The B58's E8 band** (row 107 (4)) takes P as the larger of the locked-climb and the roads responses
  (`epa_stats.e8_response`), and the spark-under-boost reading of `results/car_spark_boost.json`. Its u_val is
  used only when `car_spark_boost.summary` gives back the standard error of the median from that record's
  readings, the model spark recomputed on the B58 as built (whether every other printed field comes back is
  recorded beside it); otherwise u_val is missing and kappa takes row 107 (3)'s floor. No row defines a u_stat
  for this reading, so the line certifies nothing and the row reads untested, as row 107 (4) writes it, with
  kappa by row 107 (3); if it read off, no row gives a kappa, and the record leaves kappa empty and names the
  case for the team.

The tests are `test_epa_tightenings.py`; its `LiveRecord` class checks the committed record once it exists
(the real run's seed kind, roads, clean code at an ancestor commit whose blobs give code_sha_text, the pinned
knees; or, while `roads.json` is absent, the no-roads record of row 129 (4)), what the arming does not. ORDER step 8 also runs `test_epa_roads.py` (its check that the tightenings
name roads.json's roads_sha and roads_seed, or are the no-roads record), `test_validate_guards.py` (the
loader), `test_contract_pinned.py` and `verify_docs.py`. R3a's commit is four files: `epa_tightenings.py`,
`test_epa_tightenings.py`, `test_epa_roads.py` (its Tightenings check) and this README; after a stop that is not
a coding defect, R3b's record is written by `stopped`, not `run`.

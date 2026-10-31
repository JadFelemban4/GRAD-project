# results/EPA_ROADS: decision 34's test roads

The roads step of section I of `results/VALIDATION_DECISIONS.md` (rows 94-103). The roads module,
`epa_roads.py`, writes the roads and their records. The ceiling script, `roads_ceiling.py`, writes the
control, the sweep and the timing, and computes every ceiling the roads module records. Run every
command with `.venv/Scripts/python.exe` and `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`.

Both scripts install an audit hook that refuses to open `logs/epa*`, `data/engines/<id>/epa_*`,
`results/EPA_VALIDATION` and any `.csv`, matched anywhere in the path. Each of roads_ceiling's worker
processes installs it too. The one exception is `results/EPA_VALIDATION/summary.json`, which `recheck`
and `redraw` may open; `--summary` names exactly that file or the command is refused. The roads record
lists every repository file the draw opened, its workers' included (`files_opened`), and the sha_text
of each one that is not already hashed (`data_inputs`).

| file | what it is | written by |
|---|---|---|
| `probe_2026-10-30/` | the ceiling probe that rows 101-103 were chosen from, with its own README | committed with section I, never rewritten |
| `control.json`, `control.txt` | the B58's locked-climb control against `results/premise.json`, and the direct-run λ rows that retire 0.13 and 0.42 (row 103) | `python roads_ceiling.py control --jobs 14` |
| `sweep.json`, `sweep.txt` | row 101's sweep before the draw: C5's margins and current-grade's delivery at 130 km/h, 10-12 % in 0.05 % steps, on every car; C5 again over the design's own slot extent (one climb of L 67 s and of L 85 s) | `python roads_ceiling.py sweep --jobs J` |
| `timing.json`, `timing.txt` | one 900 s SYNTHETIC road timed closed loop (mistake 22; ORDER step 0 (c)) | `python roads_ceiling.py timing --jobs 14` |
| `attempts.jsonl` | the attempts log of row 96: append-only, one JSON line per event, each with its `step` (`draw`, `recheck` or `redraw`). A `start` line is written before anything is computed: the time, the commit, whether the tree was clean, the remote's sha, the roads commit as found and as announced, the reveal, the hashes of every file the record will hash and, for a later attempt, its note and every file and commit since the roads commit. The `outcome` line follows: `crash`, `stop` (with `coding_defect`), `roads`, `recheck` or `redraws`, with the printed file's sha_text | `epa_roads.py draw`, `recheck`, `redraw` |
| `attempt_<n>_printed.txt` | everything attempt n printed, stdout and stderr (row 96). roads.json names the earlier attempts' files with their sha_text | `epa_roads.py draw` |
| `roads.json` | the roads record of row 97, written once and never edited; roads_sha is its `sha_text` (`thresholds/common.py`). Beside row 97's list it holds every engine's τ with its climb cell (row 102, read back by the redraws, never recomputed), row 102's table of H with the step of each preview sample, the episode length the environment runs (899 steps on a 900-sample road, below), and the frozen-plant check | `epa_roads.py draw` |
| `redraws.json` | the C5 re-check and the redraws after Run 2 (rows 95, 97, 98), written once; it names roads_sha. Each accepted redraw carries its identity, its re-check on every car and decision 40's diagnostic at the Honda's re-check margin (MD:1239-1240) | `epa_roads.py redraw` |

## The commit and reveal, and the draw (row 96)

1. Each of Ghassan and Jad runs `python epa_roads.py commitment` once. It draws a private integer of
   256 bits with Python's `secrets` module and prints it with its hash line. Keep the integer offline,
   where it cannot be lost. A private integer below 2^128 is refused, at the hash and at the reveal,
   because a small one could be found from its hash line.
2. In the roads commit, each sets one line of `epa_roads.py`: `COMMITMENT_G` (Ghassan) or
   `COMMITMENT_J` (Jad). Both lines go in that one commit and never change after it.
   `test_epa_roads.py` checks their form before the push.
3. After the push, both reveal their integers at the same time, each naming the roads commit's full
   sha.
4. The draw runs on the roads commit itself. If later commits exist, check it out first
   (`git switch --detach <sha>`). Then run
   `python epa_roads.py draw --reveal-g A --reveal-j B --roads-commit <sha> --jobs 14`.
5. Commit `attempts.jsonl`, `attempt_1_printed.txt` and `roads.json` in the next commit, on top of
   whatever was pushed meanwhile.

roads_seed is `int(sha256(f"{a_G}:{a_J}:{roads_commit_sha}").hexdigest()[:15], 16)`.

The draw refuses, before it writes anything, when:
- a reveal is not an integer of at least 2^128 in canonical decimal;
- the hash lines are missing, were set in two commits, or held other values;
- the announced roads commit is not the one HEAD's history holds (a commit remade after the reveal
  would give another seed);
- `roads.json` exists, or was ever committed in HEAD's history;
- the tree is not clean, or HEAD is not in origin's `GRA-test` as `git ls-remote` reports it;
- the committed attempts log was ever deleted or rewritten, or the tree's copy is not HEAD's;
- an earlier attempt drew a set (no second set, row 103 (3)), or stopped for a reason that is not a
  coding defect, such as a reveal that did not match (that ends the roads step);
- it is the first attempt and HEAD is not the roads commit itself;
- it is a later attempt without `--note`, which names the defect and the commits that fixed it;
- any EPA engine's plant_sha is not its `freeze.json`'s, its engine_sha is not its `complete.json`'s, or
  its τ is not `complete.json`'s `e6_row4.frozen.tau_s` exactly; the B58's plant_sha is not
  865f8e7b7e5c2dbe (row 102); or `epa_freeze.versions()` is not `freeze.json`'s (the platform among them).

A reveal that does not match its hash line is logged and stops the roads step (rows 96, 103 (3)). A
crash, or a stop for a coding defect (row 98: an identity difference, a clip contact, a hashed file that
changed during the draw, found before the ceilings print, before the last identity and at the end),
allows a later attempt on the same roads_seed. Before it: commit the log and the printed file, make the
fix in its own commit, then rerun with `--note`.

## After Run 2: the re-check and the redraws

`python epa_roads.py redraw --summary results/EPA_VALIDATION/summary.json --dropped <ids or none> --jobs J`

`--dropped` must agree with `summary.json`'s per-engine `drop` (section 7). The B58 is never dropped.
The redraw refuses unless:
- the tree is clean and pushed;
- `roads.json` is committed at HEAD;
- every hashed file, version, plant_sha and engine_sha is `roads.json`'s, and the set of hashed modules
  is still the import closure;
- no package shadows a hashed module;
- no earlier redraw run wrote its record.

It logs its start and outcome lines in `attempts.jsonl`. The redraws read each engine's τ from
`roads.json`. `python epa_roads.py recheck` takes the same arguments, with an optional `--out FILE`.
It logs its lines too, and redraws nothing; if it runs first, commit and push `attempts.jsonl` before
the redraw, which refuses a log that is not HEAD's. Row 97's export route for a coding defect that forces
a change to a hashed module before the last redraw is not built: these commands refuse to run outside a
git work tree. Row 132 replaces it: both run on `GRA-test` from a commit that restores every hashed file
changed since the roads commit to its R1 version, committed and pushed; the fix is re-applied after R4.

## SYNTHETIC runs

Nothing SYNTHETIC is written here. `python epa_roads.py smoke --synthetic-seed N --out DIR --jobs J`
runs the chain on 2 roads, with the B58 and the Ford at r = 1.5 and no companions. With `--full`, it
runs the real draw's path on 1 road: all four engines, every variant, both readings and both ratios,
`roads_ceiling.report`'s companions, and the Honda's decision-40 diagnostic. `--with-redraw` adds a
re-check and the redraws of one slot at SYNTHETIC margins (the Ford's at 0.5). The seed must be an
integer below 2^32, so roads_seed can never run as one. DIR must lie outside the repository.

## What the reviews raised, and where it is settled

The reviews of 30 October 2026 raised eight points. Section J of `results/VALIDATION_DECISIONS.md` settles
the ones that are the team's (rows 121-123); none changes a design value of section I.
1. **What roads.json hashes** (row 121). The record hashes 35 files, the import closure, `step_record.py`
   (through `evaluate.py`), `random_road.py`, `check_premise.py` and `fingerprint.py` among them. So
   `step_record`'s CVT branch comes after the redraws (ORDER step 12a); the tightenings code goes in
   `epa_tightenings.py`, which no hashed module imports (step 8); the training wrapper is a new module (step 7).
2. **ORDER's check before every commit** names the step-2 files one by one, since a glob `epa_*.py` would
   match `epa_roads.py` (row 121).
3. **Row 94's defect route** (`test_defect_route.py`) passes on a branch from commit F. On a later descendant,
   PLANT_CODE and every CODE_HASHED file changed after the third arming are restored first (row 122 (1)).
4. **The readings the code makes** (E6 rows 4 and 11, the five curves of row 102, the ±6.3 K wrapper,
   `evaluate.py`'s baseline, the usable window both ways) and section G's 68.12 K are row 122 (3)-(4).
5. **The sweep** (`sweep.txt`): the Ford fails C5 at 1.9 % at 11.20-11.80 %, 13 of 41 grades, so the
   accepted grades will not be uniform on [10, 12] %. A Ford re-check margin above 0.089 after Run 2 leaves
   no passing grade (row 123).
6. **The episode length** is 899 steps on a 900-sample road (row 122 (2)); the record states it.
7. **The draw's run time is ASSUMED.** `python roads_ceiling.py timing --jobs 14` (`timing.txt`) timed 14
   closed-loop runs of one 900 s road at once: a median of 153.9 s a run, 0.1712 s a step (31 October; 148.0 s on 30 October). ORDER step 6's
   10-13 h is an extrapolation from such a rate.
8. **`verify_docs.py` and `drift_test.py` open files under `logs/epa/`.** `verify_docs.py` reads the
   manifest's `repo_path` column, to skip EPA's own files, and scans `logs/epa/README.md`, a project
   document. `drift_test.py` copies the tree, EPA's tables among its bytes. Neither parses an EPA table. Both
   run at the roads commit, as at every earlier commit of `GRA-test` (ORDER step 4).

**Checked by** `python -B test_epa_roads.py` and `python -B test_roads_ceiling.py`. Once `roads.json`
exists, `test_epa_roads.py` checks that its roads_seed is the reveal's and that its hash lines are the
roads commit's (ORDER step 6). Once `results/EPA_TIGHTENINGS.json` exists, it checks that the
tightenings name roads_sha and roads_seed (row 97, ORDER step 8). It fails when the tightenings exist
without `roads.json`.

# The training device: the runbook (31 October 2026)

The commands to run on the training device, in order, and where each output goes. They implement
rows 32, 114 and 118 of `results/VALIDATION_DECISIONS.md` and decision 61, and they are ORDER steps 3
and 18 (`docs/build_step_2/ORDER_TO_TRAINING.md`). Nothing here trains an agent: every `train.py` run
below is a benchmark or an identity test, into a temporary folder outside the repository, deleted
after. Training itself is ORDER step 22, from the commit the preregistration names.

Each claim is labelled as section I labels them: MEASURED (a run printed it, and it is named), BUILT
(the code does it, file and line given), DESIGN (a choice made here), ASSUMED (not checked).

## Before you start

```bash
REPO=~/GRAD-project            # the clone, at the pushed commit named in the step
OUT=~/grad_device/2026-11-01   # a NEW folder outside the repository, one per session
PY=$REPO/.venv/Scripts/python.exe      # Windows (Git Bash); on Linux: $REPO/.venv/bin/python
PYC=~/grad_venv_cuda_lock/Scripts/python.exe   # on CUDA (Part B): the CUDA lock's python, installed by B0;
                                               # on Linux: ~/grad_venv_cuda_lock/bin/python
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONIOENCODING=utf-8
mkdir -p "$OUT" && cd "$REPO"
```

- Every command runs from `$REPO` with `$PY`, the lock's interpreter, and writes only into `$OUT`
  unless the step says otherwise. `benchmark_training.py` writes its JSON into the current folder when
  `--out` is not given (BUILT, `default_out`), so `--out` is always given here, outside the repository.
- On CUDA, `$PYC` is Part B's interpreter: the python of the environment B0 installs from CU's CUDA
  lock (row 118), which runs B0's record lines and B1. It is set here, where every session sets it, so
  a later session of B1 has it too (the review of 2 November 2026); on the CPU nothing uses it. A4
  sets its own `PYC`, its own environment's (`~/grad_venv_cuda`), for Part A only.
- A benchmark file is never overwritten (BUILT, `resolve_out`): a second attempt needs a new `--out`.
- Never write into `runs*/`, never commit from the device except the records each step names.
- Git Bash on Windows and bash on Linux both run these commands (DESIGN); `tools/run_l8.sh` uses no
  `cygpath`. Part A has a route on Windows only (A1's note), and `tools/device_step3.sh` refuses Linux.

## Part A: now, before the first arming (ORDER step 3; rows 32, 114, 118)

This fixes the device type and its torch build on the B58, once, for every seed, arm and engine
(decision 32, rule 3). It needs only the commit that carries C1 (ORDER step 7).

**In one command** (row 134 (4)): `bash tools/device_step3.sh --python <python 3.13.2>` runs A0-A6
below, with `--window-days 10` (row 134's W), into a new `$OUT`, and packs it into `$OUT.tar.gz`, the
one file to bring back. Before its first long step it checks the interpreter (3.13.2, 64-bit, not
free-threaded), the clone (clean, pushed, carrying C1), the GPU's compute capability, the driver's CUDA
version, the CUDA index and the free disk (BUILT, `tools/device_step3.sh`). Before you run it: AC power,
sleep set to Never (the script also asks Windows to stay awake while it runs), Windows Update paused,
nothing else running, and on an NVIDIA card the driver's "CUDA - Sysmem Fallback Policy" set to "Prefer
No Sysmem Fallback" (A4).

**A0. The commit.**

```bash
git -C "$REPO" fetch && git -C "$REPO" checkout <the pushed commit carrying C1>
git -C "$REPO" rev-parse HEAD > "$OUT/A0_commit.txt"
git -C "$REPO" status --porcelain > "$OUT/A0_status.txt"     # must be empty
```

**A1. The lock install** (`requirements-lock.txt`, but not its header's `/whl/cpu` line, which A2 refuses;
the lock is frozen until step 12, ORDER's rule, so the header stays as it is). Python 3.13.2, 64-bit.

```bash
<python 3.13.2> -m venv .venv
$PY -m pip install -r requirements-lock.txt       # Windows: torch 2.14.0 from PyPI, as the laptop's
```

On Windows, install torch from PyPI with the rest, not from the `/whl/cpu` index the lock's header
names. PyPI's Windows torch 2.14.0 is the CPU build and is the team laptop's own (its metadata reads
`2.14.0`, `torch.__version__` `2.14.0+cpu`). The `/whl/cpu` wheel carries the same binaries but its
metadata reads `2.14.0+cpu`, and `check_training_device.py`'s package check then fails with "torch
2.14.0+cpu (lock: 2.14.0) <-- DIFFERENT, critical" (MEASURED on the team laptop, 2 November 2026, in a
fresh clone: `torch_cpu.dll` and `c10.dll` equal by sha256 and the two file lists equal). On Linux,
PyPI's torch is a CUDA build, so neither route passes A2 there yet; bring that back to the team.

The lock was captured on the team laptop, Windows (its header). On another operating system a pinned
package with no wheel there stops `pip`; stop, and bring the message back (ASSUMED: not tried on
Linux).

**A2. The versions** (decision 32).

```bash
$PY check_training_device.py | tee "$OUT/A2_versions.txt"
```

It must end `VERSIONS: match the lock` and exit 0 (BUILT, `check_training_device.py:94-119`). A
critical difference stops Part A.

**A3. The CPU benchmark, in the lock's environment.**

```bash
$PY -B benchmark_training.py --selftest
$PY -B benchmark_training.py --engine b58 --road extremes --device cpu --dry-run --out "$OUT/A3_bench_cpu.json"
$PY -B benchmark_training.py --engine b58 --road extremes --device cpu --out "$OUT/A3_bench_cpu.json" \
    [--window-days D] 2>&1 | tee "$OUT/A3_bench_cpu.txt"
```

Run the selftest on an idle device: its hung-run case kills its child at a 2 s deadline, and on a
loaded machine the child had not yet written its PID by then (MEASURED on the team laptop, 31 October
2026, with over 30 python.exe processes running, by tasklist: `FileNotFoundError` on `grandchild.pid`;
the same day it passed once in a git archive of 22561da and twice in the step-7 tree).

`--engine` and `--road` are required (BUILT, 31 October 2026, `check_args`); `--engine b58 --road
extremes` runs the commands the script ran before they existed (MEASURED on the team laptop, 31
October 2026: `--dry-run`, 28 lines, and `--quick --runs 1 --steps 1000 --repeats 1 --no-determinism`,
43 lines, in a git archive of 22561da and in the step-7 tree, printed the same lines once every number,
folder and live reading was masked; the one masked difference was a column's width, the CPU load before
the batch reading 100 % against 90 %). Section 4 must print `cpu: IDENTICAL` (seed 0 trained twice,
decision 32). `--window-days` is row 114's W: 10 days (row 134).

**A4. The CUDA benchmark, in its own environment** (only if `nvidia-smi` lists a GPU).

```bash
<python 3.13.2> -m venv ~/grad_venv_cuda            # outside the repository (.gitignore holds .venv/ only)
PYC=~/grad_venv_cuda/Scripts/python.exe             # Linux: ~/grad_venv_cuda/bin/python
$PYC -m pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/<the CUDA build the driver takes>
$PYC -m pip install -r requirements-lock.txt
$PYC -B benchmark_training.py --engine b58 --road extremes --device cuda --out "$OUT/A4_bench_cuda.json" \
    [--window-days D] 2>&1 | tee "$OUT/A4_bench_cuda.txt"
```

- Of the nine indexes queried (cu118, cu124, cu126, cu128-cu133), torch 2.14.0 is on cu126, cu130
  and cu132 only (MEASURED on the team laptop, 2 November 2026: `pip index versions torch
  --index-url https://download.pytorch.org/whl/<index>`). A card of compute capability 10 or more
  (Blackwell, the RTX 50 series among them) needs a CUDA 12.8 or newer build (ASSUMED), so cu130,
  which needs a driver for CUDA 13.0 (NVIDIA 580 or newer, ASSUMED), or cu132; `tools/device_step3.sh` takes the first of cu130, cu132, cu126 that the driver
  supports, never cu126 on such a card. The lock's
  `torch==2.14.0` is met by the CUDA build, so every other package is the lock's version; `--merge`
  refuses two files whose Python or packages differ beyond torch (BUILT, `merge_docs`).
- On Windows, set the NVIDIA driver's "CUDA - Sysmem Fallback Policy" to "Prefer No Sysmem Fallback"
  for this `python.exe` first (the benchmark's docstring).
- Do not run `check_training_device.py` in this environment as a gate: it reads one lock and requires
  the `+cpu` build (BUILT, `check_training_device.py:49`, `:100-105`).

**A5. One decision from both files**, in the CPU environment.

```bash
$PY -B benchmark_training.py --merge "$OUT/A3_bench_cpu.json" "$OUT/A4_bench_cuda.json" \
    [--window-days D] --out "$OUT/A5_bench_merged.json" | tee "$OUT/A5_bench_merged.txt"
# no GPU on the device: the CPU file alone (it names the CPU only if nvidia-smi ran and listed no GPU)
$PY -B benchmark_training.py --merge "$OUT/A3_bench_cpu.json" --out "$OUT/A5_bench_merged.json"
```

`--merge` takes no `--engine` or `--road`: each file names what it measured (BUILT, `check_args`).

**A6. The device type.** The `RECOMMENDATION:` line names CPU or CUDA, or no device.

- CPU: the lock's environment is the experiment's. Record the device, its CPU, the torch build and
  the concurrency for the preregistration (decision 32; row 114: "the device and its torch build,
  chosen once ... before the first arming").
- CUDA: stop here. The CUDA build then gets its own lock file (decision 32), and
  `check_training_device.py` gains a path for it (row 118). Neither is built: row 118 builds them only
  if this step chooses CUDA, and it has not run. Bring the files back to the team before anything
  else runs on CUDA.
- No device named: the text says why (determinism not checked, a GPU not measured, no clear winner,
  which keeps the CPU). Fix the cause and repeat into a new `--out`.
- CUDA cannot run on the card with torch 2.14.0 (the build the card needs is installed, the driver
  supports it, and the CUDA dry run still finds CUDA unusable): the device is the CPU, recorded with the
  probe's text (row 134 (3)). The CPU file is merged alone, and its "no device is named" is expected.
  An old driver is not this case: update it and run Part A again.

**A7. Where Part A's outputs go.** `$OUT`, outside the repository. B0, optional: the three JSON
files committed under `results/benchmarks/` (`benchmark_training.py`'s docstring, OUTPUT: they carry
no agent and no result), with `A0_commit.txt` and `A2_versions.txt` beside them.

## Part B: after the plant commit (ORDER step 18; rows 114, 118, 135; decision 61)

It needs ORDER step 18's pushed commit: the one holding V, Q, CU (if any) and Ta, on top of P (ORDER
step 14, which opens `trainable()` to the EPA engines and makes H an environment parameter), with C1,
C1b and C2 in its history. B0 checks it out and records its sha.

**B0. The commit, the environment, the versions and B0's record.**

```bash
git -C "$REPO" fetch && git -C "$REPO" checkout <the pushed commit holding V, Q, CU (if any) and Ta>
git -C "$REPO" rev-parse HEAD > "$OUT/B0_commit.txt"
git -C "$REPO" status --porcelain > "$OUT/B0_status.txt"     # must be empty
$PY check_training_device.py | tee "$OUT/B0_versions.txt"          # VERSIONS: match the lock
```

On CUDA (row 135 names it), first the environment of CU's CUDA lock (ORDER step 17a; row 118), installed
outside the repository, then its versions, checked with that environment's python, `$PYC` as Before you
start sets it:

```bash
<python 3.13.2> -m venv ~/grad_venv_cuda_lock          # a new environment, not A4's ~/grad_venv_cuda;
                                                       # $PYC, as Before you start sets it, is its python
$PYC -m pip install -r <CU's CUDA lock>
$PYC check_training_device.py <CU's CUDA path> | tee "$OUT/B0_versions_cuda.txt"   # VERSIONS: match the CUDA lock
```

Then B0's record, with row 135's interpreter. Every session that runs any of B1 runs these lines first,
unchanged:

```bash
PYB=<row 135's interpreter>    # row 135's device's: $PY for cpu; for cuda, $PYC, the CUDA lock's (Before you start)
B1OUT=~/grad_device/B1         # B1's one folder, outside the repository: this same path in every session
mkdir -p "$B1OUT"
$PYB -B - "$B1OUT" <<'EOF'
import json, os, platform, sys
import benchmark_training as B
rec = dict(B.code_info(os.getcwd()), host=platform.node())
if rec["git_head"] is None or rec["git_dirty"] is not False:
    sys.exit(f"REFUSING: B0's record needs a clean git work tree at a commit: {rec}")
path = os.path.join(sys.argv[1], f"B0_{rec['git_head']}.json")
text = json.dumps(rec, indent=1, sort_keys=True) + "\n"
if os.path.exists(path):
    with open(path, encoding="utf-8") as fh:
        if fh.read() != text:
            sys.exit(f"REFUSING: {path} exists and differs from {rec}: a B0 record is never overwritten")
    print(f"{path}: already written, the same; not rewritten")
else:
    with open(path, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(f"wrote {path}")
EOF
```

- The commit is ORDER step 18's, pushed: it holds V (step 16), Q (step 17), CU (step 17a, only if row
  135 names CUDA) and Ta (step 17b). `B0_commit.txt` records its sha, and `B0_status.txt` must be
  empty, as A0's: an attempt run from a dirty tree is an operator fault (row 135 (4)(b)).
- `$PY` is A1's environment, the lock's. Its versions are checked on either device, since on CUDA B1's
  CPU series runs in it (row 135 (4)(c)). A critical difference stops Part B.
- On CUDA, `<row 135's interpreter>` is `$PYC`, as Before you start sets it, the python of the
  environment installed here from CU's CUDA lock: a new environment (DESIGN), so nothing A4 installed
  in `~/grad_venv_cuda` is carried over, and never `$PY`. CU commits the CUDA lock and
  `check_training_device.py`'s CUDA path, only if row 135 names CUDA (row 118). Neither exists yet:
  `<CU's CUDA lock>` and `<CU's CUDA path>` are placeholders here, and CU says how its lock installs
  (ASSUMED: `pip install -r`, as A1, with its CUDA index in the lock). Its VERSIONS check must match the
  CUDA lock; a critical difference stops Part B.
- `$B1OUT` is B1's output folder, fixed here once for the whole of B1 (DESIGN; the review of 2
  November 2026). `$OUT` is new each session; `$B1OUT` is not. Every session that runs any of B1 (an
  engine on another day, a crash repeated later) sets `REPO`, `OUT`, `PY` and, on CUDA, `PYC` as Before
  you start does (on CUDA, `$PYC` is the interpreter of the record's lines and of B1), then runs the
  record's lines above again, with the `B1OUT=` line unchanged, and never a new path, so B1's k counts
  every earlier attempt and B5 copies all of them (the interface sheet
  (`docs/build_step_2/INTERFACES.md`, added in O1), 12.8: every attempt is committed, and the last is
  the measurement). Nothing but B1's attempts and B0's records is written there.
- B0's record, `$B1OUT/B0_<git_head>.json`, holds `benchmark_training.code_info()` of the work tree it
  runs in (`$REPO`, so `code_info()`'s own: git_head, git_dirty, benchmark_sha, train_sha) and `host`
  (`platform.node()`, as the benchmark's `machine` records it), written by row 135's interpreter. It is
  written once for each commit B1 runs from and never overwritten: a later session on the same commit
  and host finds it the same and leaves it, one that differs is refused, and a tree that is dirty or at
  no commit writes none (DESIGN). B5 commits it, and Ta's `classify` reads it: an attempt with no record
  for its git_head, or whose host, benchmark_sha or train_sha differs from its record's, is an operator
  fault (row 135 (4)(b)). BUILT: `test_device_gate.py`'s RunbookB1 runs these lines on a scratch work
  tree, with their controls (a record that differs, a dirty tree, a tree at no commit).

**B1. Each engine's many-run rate, by row 114's protocol, once** (row 135's protocol, commit C1b).

```bash
PYB=<row 135's interpreter>    # row 135's device's: $PY for cpu; for cuda, $PYC, the CUDA lock's (Before you start)
for E in $($PYB -B -c "import engines; print(' '.join(engines.trainable()))"); do
  k=1
  while [ -e "$B1OUT/B1_bench_$E.attempt$k.json" ] || [ -e "$B1OUT/B1_bench_$E.attempt$k.txt" ] \
     || [ -e "results/benchmarks/B1_bench_$E.attempt$k.json" ] \
     || [ -e "results/benchmarks/B1_bench_$E.attempt$k.txt" ]; do k=$((k+1)); done
  $PYB -B benchmark_training.py --engine $E --road four_engine --roads-record results/EPA_ROADS/roads.json \
      --reward-knock out --device <row 135> --runs <N> --steps <S> --repeats <R> \
      --out "$B1OUT/B1_bench_$E.attempt$k.json" 2>&1 | tee "$B1OUT/B1_bench_$E.attempt$k.txt"
done
```

On CUDA only, at the same visit, for every engine: the CPU series (row 135 (4)(c)), in the lock's
environment.

```bash
PYB=$PY                        # the lock's CPU environment (A1), on CUDA too
for E in $($PYB -B -c "import engines; print(' '.join(engines.trainable()))"); do
  k=1
  while [ -e "$B1OUT/B1_bench_$E.cpu.attempt$k.json" ] || [ -e "$B1OUT/B1_bench_$E.cpu.attempt$k.txt" ] \
     || [ -e "results/benchmarks/B1_bench_$E.cpu.attempt$k.json" ] \
     || [ -e "results/benchmarks/B1_bench_$E.cpu.attempt$k.txt" ]; do k=$((k+1)); done
  $PYB -B benchmark_training.py --engine $E --road four_engine --roads-record results/EPA_ROADS/roads.json \
      --reward-knock out --device cpu --runs <row 135's CPU N> --steps <S> --repeats <R> \
      --out "$B1OUT/B1_bench_$E.cpu.attempt$k.json" 2>&1 | tee "$B1OUT/B1_bench_$E.cpu.attempt$k.txt"
done
```

- The engines are `engines.trainable()` on B0's commit: the B58 and the engines the committed records
  keep (row 107 (5)), in `engines.known()` order (BUILT, P).
- `<row 135>`, `<N>`, `<S>` and `<R>` are row 135's device, concurrency, steps per run and repeats,
  part 2 of row 114's schedule row, fixed before the first arming (row 134 (2)). `<row 135's CPU N>`
  is the CPU series' own concurrency on CUDA, the CPU's pick in step 3's merged file (`pick_runs` on
  its CPU rows; row 135 (2)). They are placeholders here.
- `<row 135's interpreter>` is the interpreter of row 135's device: `$PY`, the lock's, for cpu; for
  cuda, `$PYC` (Before you start), the python of the environment B0 installs from CU's CUDA lock (row
  118; CU exists only if row 135 names CUDA, and neither its lock nor that environment is built yet).
  It is a placeholder here. `$PY` holds the lock's CPU build of torch: given `--device cuda` the
  benchmark finds no usable device and exits before it writes its JSON (BUILT, `main`'s "no requested
  device is usable here"; the selftest's `--device cuda --dry-run` on a CPU build), so with `$PY` every
  CUDA attempt would be a crash, and its repeat the same (the review of 2 November 2026).
- On CUDA, the CPU series always runs at the same visit, for every engine (row 135 (4)(c)): the second
  block, with `PYB=$PY`, `--device cpu`, `--runs <row 135's CPU N>` and the names
  `B1_bench_$E.cpu.attempt$k`, whose k counts the CPU series alone, over `$B1OUT` and
  `results/benchmarks/` alike. It is read only after a fallback: an engine's CUDA row reading identical
  False, fits False at N or seed0_twice False, when every engine takes its CPU row. Ta classifies only
  after the visit, so a CPU series begun only once a CUDA failure was seen would not exist when it is
  needed. On the CPU there is no second series: the first block is the CPU's.
- Every attempt is written into `$B1OUT`, outside the repository, and numbered there: k counts the
  attempts already in `$B1OUT` and in the committed `results/benchmarks/`, a `.json` or a `.txt`
  alike, so a crash that left only its `.txt` is never overwritten, and an attempt of an earlier
  session is counted (B0's `$B1OUT`). The benchmark records `git_dirty` from
  `git status --porcelain` when it starts (BUILT, `code_info`), and that lists an untracked file too:
  an attempt written inside the clone made every run record a dirty tree, the first included, since
  `tee` makes its `.txt` before the benchmark starts (the review of 2 November 2026). BUILT: the
  selftest's two engines in a row on a scratch work tree, and `test_device_gate.py`'s RunbookB1, which
  runs both blocks' own text with a stand-in interpreter. Never give `--out` inside the repository here.
- The road timed is the one the engines will train on, as step 22 trains it: row 116's generator as it
  passed ORDER step 17's gates, with decision 29's share on (`--roads-record`, row 130 (5)) and the
  reward without the knock term (`--reward-knock out`, row 113 (5)). Each `train.py` run is given
  `--lr-schedule last-third --scored-share --roads-record results/EPA_ROADS/roads.json --reward-knock
  out` (BUILT, `train_cmd`): decision 29's recipe as `train_all.py --recipe29` gives it, but
  `--checkpoint-average`, which `train.py` refuses at `--steps <S>` under its 50 000-step window, so the
  average's snapshots are not timed. The selftest passes that command line through `train.py`'s own
  parser and `check_recipe`, and compares its recipe flags with `train_all.py`'s.
  `--roads-record` must be the committed, unchanged `roads.json` (BUILT, `real_record_problem`).
- r_e = lower_min / N exactly (row 135 (3)): `lower_min` of the row at runs N in the JSON's
  `recommendation.configurations`, the lowest lower bound over the R repeats (BUILT,
  `configurations`). Keep section 4 on (no `--no-determinism`).
- A crash is defined as in row 135 (4), an operator fault among them ((b)). A crash's attempt is kept
  and that engine alone runs again into its next k, in the same series: the same block with its `for`
  line `for E in <the engine>; do` (the second block for a CPU attempt), into B0's `$B1OUT` whichever
  session repeats it, so no other engine gains an attempt. An engine whose last attempt in a series is
  a measurement is never run again in it; after a coding defect's fix, B1 is repeated for every engine
  (row 135 (4)(c)). The last attempt of each series is the measurement, or row 135 (4)(c)'s outcome,
  and every earlier one classifies as a crash (the interface sheet (`docs/build_step_2/INTERFACES.md`,
  added in O1), 12.8).

**B2. The identity against the team laptop** (recorded, not required: row 32).

```bash
$PY check_training_device.py --identity "$OUT/B2_identity_device.json"
$PY check_training_device.py --compare <the laptop's --identity file at the same commit> \
    "$OUT/B2_identity_device.json" | tee "$OUT/B2_compare.txt"
```

`IDENTICAL TRAINING` or `NOT IDENTICAL` is recorded either way; a different processor can round the
last bit differently (decision 32). The laptop's file is made on the laptop at the same commit and
carried to the device (open: where the team keeps it).

**B3. L8, with the fixed script** (results/B58_IDENTITY.md item 3.6.20; decision 61).

```bash
bash tools/run_l8.sh --cand "$REPO" --py "$PY" --out "$OUT/B3_L8_dry" --dry-run    # nothing trains
bash tools/run_l8.sh --cand "$REPO" --py "$PY" --out "$OUT/B3_L8" 2>&1 | tee "$OUT/B3_L8.txt"
```

- `tools/run_l8.sh` (BUILT, 31 October 2026) takes the candidate, the interpreter and the output
  folder as required arguments, makes `ref/` (git archive `cf43fbb`, checked with `tar --compare`),
  `tools/` (the tarball's `l8_compare.py` and `l8_perturbed.py`, byte for byte, their sha256 in
  `L8/provenance.txt`) and `L8/` itself, and converts no path with `cygpath`. The tarball
  `results/B58_IDENTITY/certificate_tools.tar.gz` is left as the certificate made it.
- It runs eleven 600-step runs: the three pairs (extremes sighted and blind, wideair sighted, in the
  candidate and in `cf43fbb`), the wrapper alone, one ulp on `car.mass` and on `thermal.c_turb`, and
  the relative steps 1e-9 and 1e-6 on `car.mass`; then every comparison.
- It must end `L8 VERDICT: PASS`: every run exits 0, the three pairs and the wrapper alone are
  IDENTICAL TRAINING, and both relative-step controls are NOT IDENTICAL (mistake 12). The two one-ulp
  controls are printed and not judged (build step 1's L8 found them identical: STATE_HISTORY.md, its
  L8 row). Each comparison is judged on the verdict `l8_compare.py` prints together with its exit
  code; a comparison that printed no verdict (a traceback also exits 1) reads ERROR in
  `_verdicts.txt` and fails L8 whatever it was expected to read, the one-ulp controls included.
- The candidate's repository must hold `cf43fbb` (the script refuses otherwise).
- The dry run makes `ref/`, `tools/` and `L8/` as the real run does and runs each of the eleven
  commands with `--help` appended (MEASURED on the team laptop, 31 October 2026, in the step-7 tree
  on 22561da: `bash tools/run_l8.sh --cand <the tree> --py <its venv> --out <scratch> --dry-run`: each of
  the eleven exited 0, `ref/` equal to the archive, 36 s; `test_device_gate.py` RunL8 repeats it).

**B4. The frozen-plant dumps** (decision 61; `epa_freeze.py:1331-1342`).

```bash
$PY -B test_epa_plants.py 2>&1 | tee "$OUT/B4_test_epa_plants.txt"
```

For each calibrated EPA plant it re-makes the frozen-plant dump on the device and compares it with
its `results/EPA_CALIBRATION/<id>/complete.json`'s `dump.sha256`, with the engine_sha and the
deliverable-torque table (BUILT, `test_epa_plants.py:47-67`, `:86-112`). It must pass; a dump that
differs is the device's result to report, never a reason to re-freeze.

**B5. Where Part B's outputs go.** `$OUT`, outside the repository, and B1's attempts and B0's records
in B0's `$B1OUT`. Commit B1 (ORDER step 18), once every engine of B1 is done: every B1 attempt of every
session (on CUDA the CPU series' too) and every B0 record, copied from `$B1OUT` into
`results/benchmarks/` only now and never renamed or deleted,

```bash
mkdir -p results/benchmarks
cp -n "$B1OUT"/B1_bench_*.attempt*.json "$B1OUT"/B1_bench_*.attempt*.txt "$B1OUT"/B0_*.json results/benchmarks/
```

then `B2_compare.txt`, `B4_test_epa_plants.txt`, and L8's record from `$OUT/B3_L8/L8/`
(`provenance.txt`, `_status.txt`, `_verdicts.txt`, `compare_*.txt`, `cmp/*.json`,
`run_identities.json`). Ta's `classify` reads every committed attempt, with its commit's B0 record.
The last attempt of each series has `code.git_dirty` False, and a dirty one is an operator fault, kept
and repeated (row 135 (4)(b)). How L8's record enters
`results/B58_IDENTITY.md`, which `make_md.py` writes from `results/B58_IDENTITY.json` (never by hand),
is a question for the team: a new record through the certificate's tools, or a record of its own beside
the certificate.

## What is not here, and why

- The per-engine gates (ORDER step 17: `test_reward.py --engine`, `check_roads.py --engine`) run on
  the team laptop or the device, after P and the redraws, on `roads.json`'s roads: they are not
  device steps. Their code is `engine_gate.py`.
- The CUDA build's lock file and the CUDA path of `check_training_device.py`: CU's (ORDER step 17a),
  only if row 135 names CUDA; B0 installs and checks them.
- Training (ORDER step 22).

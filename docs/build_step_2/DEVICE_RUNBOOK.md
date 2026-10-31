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
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONIOENCODING=utf-8
mkdir -p "$OUT" && cd "$REPO"
```

- Every command runs from `$REPO` with `$PY`, the lock's interpreter, and writes only into `$OUT`
  unless the step says otherwise. `benchmark_training.py` writes its JSON into the current folder when
  `--out` is not given (BUILT, `default_out`), so `--out` is always given here, outside the repository.
- A benchmark file is never overwritten (BUILT, `resolve_out`): a second attempt needs a new `--out`.
- Never write into `runs*/`, never commit from the device except the records each step names.
- Git Bash on Windows and bash on Linux both run these commands (DESIGN); `tools/run_l8.sh` uses no
  `cygpath`.

## Part A: now, before the first arming (ORDER step 3; rows 32, 114, 118)

This fixes the device type and its torch build on the B58, once, for every seed, arm and engine
(decision 32, rule 3). It needs only the commit that carries C1 (ORDER step 7).

**A0. The commit.**

```bash
git -C "$REPO" fetch && git -C "$REPO" checkout <the pushed commit carrying C1>
git -C "$REPO" rev-parse HEAD > "$OUT/A0_commit.txt"
git -C "$REPO" status --porcelain > "$OUT/A0_status.txt"     # must be empty
```

**A1. The lock install** (the lock's own header, `requirements-lock.txt:1-11`). Python 3.13.2, 64-bit.

```bash
<python 3.13.2> -m venv .venv
$PY -m pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cpu
$PY -m pip install -r requirements-lock.txt
```

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
decision 32). `--window-days` is row 114's W once the schedule row fixes it.

**A4. The CUDA benchmark, in its own environment** (only if `nvidia-smi` lists a GPU).

```bash
<python 3.13.2> -m venv ~/grad_venv_cuda            # outside the repository (.gitignore holds .venv/ only)
PYC=~/grad_venv_cuda/Scripts/python.exe             # Linux: ~/grad_venv_cuda/bin/python
$PYC -m pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/<the CUDA build the driver takes>
$PYC -m pip install -r requirements-lock.txt
$PYC -B benchmark_training.py --engine b58 --road extremes --device cuda --out "$OUT/A4_bench_cuda.json" \
    [--window-days D] 2>&1 | tee "$OUT/A4_bench_cuda.txt"
```

- Which CUDA build of torch 2.14.0 is the team's choice (ASSUMED: one the driver supports). The lock's
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

**A7. Where Part A's outputs go.** `$OUT`, outside the repository. B0, optional: the three JSON
files committed under `results/benchmarks/` (`benchmark_training.py`'s docstring, OUTPUT: they carry
no agent and no result), with `A0_commit.txt` and `A2_versions.txt` beside them.

## Part B: after the plant commit (ORDER step 18; rows 114, 118; decision 61)

It needs the pushed commit after P (ORDER step 14, which opens `trainable()` to the EPA engines and
makes H an environment parameter), with C1 and C2 in its history.

**B0. The commit and the versions.**

```bash
git -C "$REPO" fetch && git -C "$REPO" checkout <the pushed commit after P>
git -C "$REPO" rev-parse HEAD > "$OUT/B0_commit.txt"
$PY check_training_device.py | tee "$OUT/B0_versions.txt"          # VERSIONS: match the lock
```

**B1. Each engine's many-run rate, by row 114's protocol, once.**

```bash
for E in b58 mazda_25t honda_l15b7 ford_27tt; do
  $PY -B benchmark_training.py --engine $E --road four_engine --device <A6's device> \
      --runs <N_e> --steps <S> --repeats <R> --out "$OUT/B1_bench_$E.json" 2>&1 | tee "$OUT/B1_bench_$E.txt"
done
```

- `<N_e>` (the concurrency the engine trains at), `<S>` and `<R>` are the protocol's, fixed in the
  committed schedule row before the first arming (row 114). They are placeholders here.
- The road timed is the one the engines will train on: the commit carries row 116's generator as it
  passed ORDER step 17's gates (`check_roads.py --engine`, `test_reward.py --engine`).
- `--road four_engine` is row 116's training road, `train.py`'s name for it (C1). The benchmark's
  runs train it with its general episodes, as `train.py` does with neither `--scored-share` nor
  `--roads-record` (BUILT, `benchmark_training.py`'s `ROAD_OPTIONS`); the share's step is the same
  plant step (ASSUMED: its rate is not separately measured).
- r_e, the rate statistic, is the per-run lower rate in the benchmark's waves: the
  `steps/s per run` the recommendation prints at `<N_e>`, which is `lower_min / runs` of that row in
  the JSON's `recommendation.configurations` (BUILT, `schedule`). Keep section 4 on (no
  `--no-determinism`): without it the recommendation prints no schedule line.
- Before P, `--engine` refuses the three EPA engines at the parser (BUILT: `engines.trainable()`,
  decision 47). A crash is logged and the run repeated; nothing else is repeated (row 114).

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

**B5. Where Part B's outputs go.** `$OUT`, outside the repository. Commit B1 (ORDER step 18): the
four `B1_bench_*.json` under `results/benchmarks/`, `B2_compare.txt`, `B4_test_epa_plants.txt`, and
L8's record from `$OUT/B3_L8/L8/` (`provenance.txt`, `_status.txt`, `_verdicts.txt`,
`compare_*.txt`, `cmp/*.json`, `run_identities.json`). How L8's record enters
`results/B58_IDENTITY.md`, which `make_md.py` writes from `results/B58_IDENTITY.json` (never by hand),
is a question for the team: a new record through the certificate's tools, or a record of its own beside
the certificate.

## What is not here, and why

- The per-engine gates (ORDER step 17: `test_reward.py --engine`, `check_roads.py --engine`) run on
  the team laptop or the device, after P and the redraws, on `roads.json`'s roads: they are not
  device steps. Their code is `engine_gate.py`.
- The CUDA build's lock file and the CUDA path of `check_training_device.py`: only if A6 names CUDA.
- Training (ORDER step 22).

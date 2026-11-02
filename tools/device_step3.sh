#!/usr/bin/env bash
# device_step3.sh -- ORDER step 3 on the training device in one command: Part A of
# docs/build_step_2/DEVICE_RUNBOOK.md (A0-A6). It checks the machine first, then makes the lock's
# environment and checks its versions, makes the CUDA environment and runs its probe when nvidia-smi
# lists a GPU, times the CPU, times CUDA, merges the two files into one decision, and packs everything
# into one archive to carry back to the team laptop. Nothing trains an agent, nothing is committed,
# and nothing is written into the repository but its .venv.
#
#   bash tools/device_step3.sh --python <python 3.13.2> [--out <new folder>] [--cuda-venv <folder>]
#                              [--cuda-index <cu130|cu132|cu126>] [--smoke]
#
#   --python      the Python 3.13.2 (64-bit, not free-threaded) both environments are made from, e.g.
#                 "C:/Users/<you>/AppData/Local/Programs/Python/Python313/python.exe"
#   --out         a folder that does not exist yet, outside the repository (default:
#                 ~/grad_device/<date>_<hour><minute>_step3); the archive is <out>.tar.gz beside it
#   --cuda-venv   the CUDA environment, outside the repository (default ~/grad_venv_cuda)
#   --cuda-index  the PyTorch wheel index of the CUDA build (default: chosen below; a given one is
#                 checked by the same rule)
#   --smoke       a test of THIS SCRIPT only (the benchmark's --quick at one concurrency, one repeat,
#                 no merge): its files decide nothing and are never step 3's
#
# WHY (rows 114, 118 and 134 of results/VALIDATION_DECISIONS.md; decision 32). The device and its torch
# build are chosen once, on the B58, by benchmark_training.py, before Run 2's first arming. Part A is a
# sequence of installs and multi-hour benchmarks on a machine nobody from the team watches. Every check
# that can fail is made before the first long step, the CUDA probe among them, so a visit is not lost
# to a wrong Python, a missing driver or wheel, or a card CUDA cannot run on. It runs under Git Bash on
# Windows only: A1's route has no Linux equivalent yet (DEVICE_RUNBOOK.md, A1).
#
# THE CUDA BUILD (MEASURED on the team laptop, 2 November 2026, `pip index versions torch --index-url
# https://download.pytorch.org/whl/<index>`): of the nine indexes queried (cu118, cu124, cu126,
# cu128-cu133), torch 2.14.0 is on cu126, cu130 and cu132 only. A card of compute capability 10 or more
# (Blackwell: the RTX 50 series among them) needs a CUDA 12.8 or newer build (ASSUMED), so cu130 or
# cu132; the probe checks it on the card. The default is the first of cu130, cu132, cu126 whose CUDA
# version the driver supports ("CUDA Version" in nvidia-smi's header), never cu126 on such a card.
#
# THE DECISION (A6) is the merge's RECOMMENDATION line. CPU, or "NO CLEAR WINNER, KEEP CPU": step 3 is
# done. CUDA: stop there (row 118: the CUDA lock file and the CUDA path of check_training_device.py are
# built first). CUDA cannot run on this card with torch 2.14.0 (the card's build installed, the driver
# supporting it, and the probe's own verdict "CUDA does not run here"): the device is the CPU, by row
# 134 (3), recorded with the probe's text; the CPU file is merged alone, and its "no device is named"
# line is expected. Any other failure stops the script.
set -u

WINDOW_DAYS=10          # row 134: W is 10 November 2026 00:00 to 20 November 2026 00:00 AST, 240 h
TORCH=2.14.0            # requirements-lock.txt
C1=523a75a              # ORDER step 7 (C1): the commit that gave the benchmark --engine and --road
BRANCH=GRA-test
INDEX_URL=https://download.pytorch.org/whl
CANNOT_RUN="CUDA does not run here"   # benchmark_training.py's part_probe: the CUDA test raised

die() { echo; echo "device_step3.sh: STOPPED: $*" >&2; exit 2; }
say() { echo; echo "== $*"; }
usage() { sed -n '9,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

PYBASE= OUT= CUDA_VENV= CUDA_INDEX= SMOKE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --python) PYBASE=${2-}; shift 2 || die "--python needs an interpreter" ;;
    --out) OUT=${2-}; shift 2 || die "--out needs a folder" ;;
    --cuda-venv) CUDA_VENV=${2-}; shift 2 || die "--cuda-venv needs a folder" ;;
    --cuda-index) CUDA_INDEX=${2-}; shift 2 || die "--cuda-index needs an index name" ;;
    --smoke) SMOKE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage; die "unknown argument $1" ;;
  esac
done
[ -n "$PYBASE" ] || { usage; die "--python is required"; }
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) ;; *) die "this script runs under Git Bash on Windows only (DEVICE_RUNBOOK.md, A1): bring this message back to the team" ;; esac

REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd) || die "cannot find the repository"
PY="$REPO/.venv/Scripts/python.exe"
TAG=step3; [ "$SMOKE" = 1 ] && TAG=step3_SMOKE
[ -n "$OUT" ] || OUT="$HOME/grad_device/$(date +%Y-%m-%d_%H%M)_$TAG"
[ -n "$CUDA_VENV" ] || CUDA_VENV="$HOME/grad_venv_cuda"
if [ -e "$OUT" ] && [ -n "$(ls -A "$OUT" 2>/dev/null)" ]; then die "$OUT exists and is not empty: pass a new --out"; fi
case "$OUT/" in "$REPO"/*) die "--out must be outside the repository" ;; esac
case "$CUDA_VENV/" in "$REPO"/*) die "--cuda-venv must be outside the repository" ;; esac
mkdir -p "$OUT" || die "cannot make $OUT"
OUT=$(cd "$OUT" && pwd)
PYC="$CUDA_VENV/Scripts/python.exe"
SMOKE_ARGS=(); [ "$SMOKE" = 1 ] && SMOKE_ARGS=(--quick --runs 1 --repeats 1 --steps 1000)

# keep the machine awake while this runs: a PowerShell loop that asks Windows to stay on every 30 s,
# writes one line once the first call succeeds, and ends when the marker file goes (at this script's
# exit) or after 48 h
AWAKE="$OUT/.keep_awake"
keep_awake() {
  : > "$AWAKE"
  local w; w=$(cygpath -w "$AWAKE")
  powershell.exe -NoProfile -Command "\$t = Add-Type -Name K -Namespace W -PassThru -MemberDefinition '[DllImport(\"kernel32.dll\")] public static extern uint SetThreadExecutionState(uint f);'; \$end = (Get-Date).AddHours(48); \$said = \$false; while ((Test-Path -LiteralPath '$w') -and ((Get-Date) -lt \$end)) { \$r = \$t::SetThreadExecutionState([uint32]2147483649); if (-not \$said) { 'keep-awake: SetThreadExecutionState returned ' + \$r + ' (0 means it failed)'; \$said = \$true }; Start-Sleep -Seconds 30 }; 'keep-awake: ended'" > "$OUT/keep_awake.log" 2>&1 &
}
trap 'rm -f "$AWAKE"' EXIT

run_all() {
  export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONIOENCODING=utf-8
  cd "$REPO" || die "cannot enter $REPO"
  echo "device_step3.sh, $(date '+%Y-%m-%d %H:%M:%S %z'), repository $REPO, out $OUT"
  [ "$SMOKE" = 1 ] && echo "SMOKE TEST: a test of this script only; nothing here is step 3's"

  say "Checks before any long step"
  local v; v=$("$PYBASE" -I -c "import sys, struct, platform, sysconfig; print(platform.python_version(), struct.calcsize('P') * 8, sys.implementation.name, 'free-threaded' if sysconfig.get_config_var('Py_GIL_DISABLED') else 'gil')" 2>&1) \
    || die "--python $PYBASE does not run: $v"
  echo "  python: $v"
  # 3.13.2 and 64-bit: requirements-lock.txt:4; CPython with the GIL: this script's own check (DESIGN)
  [ "$v" = "3.13.2 64 cpython gil" ] || die "the lock needs Python 3.13.2, 64-bit (requirements-lock.txt:4), CPython, not free-threaded; $PYBASE is: $v"
  git -C "$REPO" fetch origin "$BRANCH" || die "git fetch failed: the clone needs github access"
  [ -z "$(git -C "$REPO" status --porcelain)" ] || { git -C "$REPO" status --short; die "the clone is not clean"; }
  local head; head=$(git -C "$REPO" rev-parse HEAD)
  git -C "$REPO" merge-base --is-ancestor "$head" "origin/$BRANCH" || die "HEAD $head is not on origin/$BRANCH: check out a pushed commit"
  git -C "$REPO" merge-base --is-ancestor "$C1" "$head" || die "HEAD $head does not carry C1 ($C1)"
  [ "$head" = "$(git -C "$REPO" rev-parse "origin/$BRANCH")" ] || echo "  NOTE: HEAD is not origin/$BRANCH's tip: run 'git pull' first unless the team named this commit"
  echo "  commit: $head (clean, pushed, carries C1)"

  # nvidia-smi: benchmark_training.py names the CPU alone only when nvidia-smi ran and lists no GPU
  # (its docstring); when it gives no answer, no device can be named, so that stops here
  command -v nvidia-smi >/dev/null 2>&1 || die "nvidia-smi is not on PATH: install or repair the NVIDIA driver (benchmark_training.py names no device without nvidia-smi's answer)"
  local smi; smi=$(nvidia-smi -L 2>&1) || die "nvidia-smi fails: $smi. Install or repair the NVIDIA driver"
  {
    echo "date: $(date '+%Y-%m-%d %H:%M:%S %z')"; uname -a
    echo "$smi"
    nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv
    nvidia-smi | grep -o "CUDA Version: [0-9.]*"
    powershell.exe -NoProfile -Command "Get-CimInstance Win32_Processor | Format-List Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed; 'RAM_GB ' + [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1); \$o = Get-CimInstance Win32_OperatingSystem; \$o.Caption + ' ' + \$o.Version"
    df -h "$HOME" | tail -1
  } > "$OUT/A_machine.txt" 2>&1
  sed 's/^/  /' "$OUT/A_machine.txt"

  local gpu=0 cap="" drv="" idx=""
  if echo "$smi" | grep -q "^GPU "; then
    gpu=1
    cap=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader 2>/dev/null | head -1 | tr -d ' \r')
    drv=$(nvidia-smi 2>/dev/null | grep -o "CUDA Version: [0-9.]*" | head -1 | awk '{print $3}')
    [ -n "$drv" ] || die "nvidia-smi lists a GPU but prints no CUDA Version: update the NVIDIA driver"
    local new=0; case "$cap" in 1[0-9].*|[2-9][0-9].*) new=1 ;; esac   # capability 10 or more: CUDA 12.8+
    allowed() {   # is the index $1 usable with this driver and card?
      local cv="${1:2:2}.${1:4}"
      awk -v a="$cv" -v b="$drv" 'BEGIN { exit !(a + 0 <= b + 0) }' || return 1
      { [ "$new" = 1 ] && [ "$1" = cu126 ]; } && return 1
      return 0
    }
    if [ -n "$CUDA_INDEX" ]; then
      allowed "$CUDA_INDEX" || die "--cuda-index $CUDA_INDEX does not suit compute capability $cap with a driver for CUDA $drv"
      idx=$CUDA_INDEX
    else
      local c; for c in cu130 cu132 cu126; do allowed "$c" && { idx=$c; break; }; done
      if [ -z "$idx" ]; then
        if [ "$new" = 1 ]; then die "compute capability $cap with a driver for CUDA $drv: torch $TORCH's builds for this card need a driver for CUDA 13.0 or newer (cu130, cu132). Update the NVIDIA driver (580 or newer, ASSUMED), then run this again with a new --out"
        else die "compute capability $cap with a driver for CUDA $drv: torch $TORCH's builds need a driver for CUDA 12.6 or newer (cu126). Update the NVIDIA driver, then run this again with a new --out"; fi
      fi
    fi
    local ix; ix=$("$PYBASE" -m pip index versions torch --index-url "$INDEX_URL/$idx" 2>&1) || die "pip could not read the index $idx: $ix"
    echo "$ix" | grep -q "[ ,]$TORCH+$idx\b" || die "the index $idx has no torch $TORCH+$idx (pip: $(echo "$ix" | grep -i "available" | head -1))"
    echo "  GPU: compute capability $cap, driver for CUDA $drv; the CUDA build will be torch $TORCH+$idx"
  else
    echo "  GPU: nvidia-smi ran and lists none (A4 is skipped; the CPU file is merged alone)"
  fi
  local free_gb; free_gb=$(df -Pk "$HOME" | awk 'NR == 2 { printf "%d", $4 / 1048576 }')
  [ "${free_gb:-0}" -ge 15 ] || die "only ${free_gb} GB free on the disk of $HOME: the two environments need about 15 GB (ASSUMED)"

  say "A0. The commit"
  git -C "$REPO" rev-parse HEAD > "$OUT/A0_commit.txt"
  git -C "$REPO" status --porcelain > "$OUT/A0_status.txt"
  cat "$OUT/A0_commit.txt"

  say "A1. The lock's environment ($REPO/.venv)"
  if [ -e "$REPO/.venv" ]; then
    [ "$("$PY" -I -c "import platform; print(platform.python_version())" 2>/dev/null)" = 3.13.2 ] \
      || die "$REPO/.venv exists and is not a Python 3.13.2 environment: delete it, then run this again with a new --out"
    echo "  $REPO/.venv exists (Python 3.13.2): installing into it"
  else
    "$PYBASE" -m venv "$REPO/.venv" || die "venv failed"
  fi
  # torch from PyPI, as the team laptop's: on Windows PyPI's torch 2.14.0 IS the CPU build, and its
  # metadata reads 2.14.0, which check_training_device.py's package check needs. The /whl/cpu wheel
  # that the lock's header names carries the same binaries but reads 2.14.0+cpu, and that check
  # refuses it (MEASURED on the team laptop, 2 November 2026: torch_cpu.dll and c10.dll equal by
  # sha256, the file lists equal; check_training_device.py "torch 2.14.0+cpu (lock: 2.14.0) <--
  # DIFFERENT, critical" on a fresh /whl/cpu install)
  "$PY" -m pip install --disable-pip-version-check -r requirements-lock.txt || die "pip: requirements-lock.txt"

  say "A2. The versions"
  "$PY" check_training_device.py 2>&1 | tee "$OUT/A2_versions.txt"
  local rc=${PIPESTATUS[0]}
  { [ "$rc" = 0 ] && grep -q "VERSIONS: match the lock" "$OUT/A2_versions.txt"; } \
    || die "A2: the versions do not match the lock (exit $rc; $OUT/A2_versions.txt). If $REPO/.venv was made before this run, delete it and run this again with a new --out"

  local cuda=none
  if [ "$gpu" = 1 ]; then
    say "A4, first part: the CUDA environment and its probe ($CUDA_VENV, torch $TORCH+$idx), before the long steps"
    if [ -e "$PYC" ]; then
      [ "$("$PYC" -I -c "import platform; print(platform.python_version())" 2>/dev/null)" = 3.13.2 ] \
        || die "$CUDA_VENV exists and is not a Python 3.13.2 environment: delete it, then run this again with a new --out"
    else
      "$PYBASE" -m venv "$CUDA_VENV" || die "venv failed ($CUDA_VENV)"
    fi
    # the exact build: torch==2.14.0 alone is met by any installed 2.14.0+<build> (PEP 440 ignores the
    # local label), so a reused environment could keep another build
    "$PYC" -m pip install --disable-pip-version-check "torch==$TORCH+$idx" --index-url "$INDEX_URL/$idx" || die "pip: torch $TORCH+$idx"
    "$PYC" -m pip install --disable-pip-version-check -r requirements-lock.txt || die "pip: requirements-lock.txt (CUDA environment)"
    local tv; tv=$("$PYC" -I -c "import torch; print(torch.__version__, torch.version.cuda)" 2>&1) || die "torch does not import in $CUDA_VENV: $tv"
    echo "  torch $tv" | tee "$OUT/A4_torch.txt"
    case "$tv" in "$TORCH+$idx "[0-9]*) ;; *) die "the CUDA environment holds torch $tv, not $TORCH+$idx with CUDA" ;; esac
    "$PYC" -B benchmark_training.py --engine b58 --road extremes --device cuda --dry-run --out "$OUT/A4_bench_cuda.json" 2>&1 | tee "$OUT/A4_dry_cuda.txt"
    rc=${PIPESTATUS[0]}
    if [ "$rc" = 0 ] && grep -q "dry run: only the probe ran" "$OUT/A4_dry_cuda.txt"; then
      cuda=probe_ok
    elif grep -q "$CANNOT_RUN" "$OUT/A4_dry_cuda.txt"; then
      cuda=cannot_run
      echo "  CUDA DOES NOT RUN HERE with torch $TORCH+$idx (the probe's text is in A4_dry_cuda.txt): by row 134 (3) the device is the CPU"
    else
      die "A4: the CUDA dry run failed for a reason that is not the probe's '$CANNOT_RUN' (exit $rc; $OUT/A4_dry_cuda.txt): fix it and run this again with a new --out"
    fi
  fi

  say "A3. The CPU benchmark"
  local ok=0 i
  for i in 1 2; do
    "$PY" -B benchmark_training.py --selftest > "$OUT/A3_selftest_$i.txt" 2>&1 && { ok=1; break; }
    echo "  the selftest failed (try $i; its hung-run case is timing-sensitive on a busy machine)"; tail -5 "$OUT/A3_selftest_$i.txt"
  done
  [ "$ok" = 1 ] || die "A3: the selftest failed twice: close every other program and run this again with a new --out"
  echo "  selftest: passed"
  "$PY" -B benchmark_training.py --engine b58 --road extremes --device cpu --dry-run --out "$OUT/A3_bench_cpu.json" 2>&1 | tee "$OUT/A3_dry_cpu.txt"
  [ "${PIPESTATUS[0]}" = 0 ] || die "A3: the CPU dry run failed ($OUT/A3_dry_cpu.txt)"
  "$PY" -B benchmark_training.py --engine b58 --road extremes --device cpu --window-days "$WINDOW_DAYS" "${SMOKE_ARGS[@]}" \
      --out "$OUT/A3_bench_cpu.json" 2>&1 | tee "$OUT/A3_bench_cpu.txt"
  [ "${PIPESTATUS[0]}" = 0 ] || die "A3: the CPU benchmark failed ($OUT/A3_bench_cpu.txt)"
  grep -Eq "^ +cpu: IDENTICAL" "$OUT/A3_bench_cpu.txt" || die "A3: section 4 did not print 'cpu: IDENTICAL' (decision 32)"

  if [ "$cuda" = probe_ok ]; then
    say "A4, second part: the CUDA benchmark"
    "$PYC" -B benchmark_training.py --engine b58 --road extremes --device cuda --window-days "$WINDOW_DAYS" "${SMOKE_ARGS[@]}" \
        --out "$OUT/A4_bench_cuda.json" 2>&1 | tee "$OUT/A4_bench_cuda.txt"
    [ "${PIPESTATUS[0]}" = 0 ] || die "A4: the CUDA benchmark failed ($OUT/A4_bench_cuda.txt)"
    cuda=measured
  fi

  say "A5. One decision"
  if [ "$SMOKE" = 1 ]; then
    echo "  smoke test: a --quick file cannot be merged (benchmark_training.py refuses it), so A5 is skipped"
  elif [ "$cuda" = measured ]; then
    "$PY" -B benchmark_training.py --merge "$OUT/A3_bench_cpu.json" "$OUT/A4_bench_cuda.json" --window-days "$WINDOW_DAYS" \
        --out "$OUT/A5_bench_merged.json" 2>&1 | tee "$OUT/A5_bench_merged.txt"
    [ "${PIPESTATUS[0]}" = 0 ] || die "A5: the merge failed ($OUT/A5_bench_merged.txt)"
  else
    "$PY" -B benchmark_training.py --merge "$OUT/A3_bench_cpu.json" --window-days "$WINDOW_DAYS" \
        --out "$OUT/A5_bench_merged.json" 2>&1 | tee "$OUT/A5_bench_merged.txt"
    [ "${PIPESTATUS[0]}" = 0 ] || die "A5: the merge failed ($OUT/A5_bench_merged.txt)"
  fi

  say "A6. The device type"
  {
    echo "commit $(cat "$OUT/A0_commit.txt")"
    echo "cuda: $cuda${idx:+ (torch $TORCH+$idx)}"
    grep -h -A3 "^RECOMMENDATION:" "$OUT/A5_bench_merged.txt" "$OUT/A3_bench_cpu.txt" "$OUT/A4_bench_cuda.txt" 2>/dev/null | head -30
    case "$cuda" in
      cannot_run) echo "READ: CUDA cannot run on this card with torch $TORCH: the device is the CPU (row 134 (3)); the merge's 'no device is named' is expected" ;;
      measured) echo "READ: the RECOMMENDATION line names the device: CPU or 'NO CLEAR WINNER, KEEP CPU' ends step 3; CUDA stops it (row 118)" ;;
      none) echo "READ: nvidia-smi ran and lists no GPU: the RECOMMENDATION line names the CPU" ;;
    esac
    [ "$SMOKE" = 1 ] && echo "SMOKE TEST: none of this is step 3's"
  } | tee "$OUT/A6_summary.txt"
}

keep_awake
run_all 2>&1 | tee "$OUT/step3_log.txt"
rc=${PIPESTATUS[0]}
rm -f "$AWAKE"
tar -czf "$OUT.tar.gz" -C "$(dirname "$OUT")" "$(basename "$OUT")" && echo && echo "Bring this one file back to the team laptop: $OUT.tar.gz"
[ "$rc" = 0 ] && echo "device_step3.sh: finished" || echo "device_step3.sh: stopped (exit $rc): send $OUT.tar.gz anyway"
exit "$rc"

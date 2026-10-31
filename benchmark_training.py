"""benchmark_training.py -- CPU or GPU on the training device? Measured there, before any training.

    python benchmark_training.py --engine b58 --road extremes --device cpu
                                                   in the CPU environment (requirements-lock.txt)
    python benchmark_training.py --engine b58 --road extremes --device cuda
                                                   in the CUDA environment: the GPU only
    python benchmark_training.py --merge CPU.json CUDA.json [--window-days D]
                                                   the two environments' files, one decision
    python benchmark_training.py --engine E --road R --quick
                                                   a SMOKE TEST of the harness on this machine (1 and
                                                   every usable CPU, 1 500 steps, one repeat): its
                                                   numbers are not for decisions 30 and 32
    python benchmark_training.py --engine E --road R --dry-run
                                                   the machine, the plan and every command; nothing
                                                   is trained or timed (CUDA is probed, in a child)
    python benchmark_training.py --selftest        the harness on dummy work (seconds; no SAC, no plant)

--engine AND --road ARE REQUIRED (31 October 2026, rows 114 and 118): every run that measures names
the plant and the road it times, as train.py's own --engine (CLAUDE.md mistake 1: there is no
default engine) and as the launchers pass --road (a default that selects an experiment is the trap
train.py's docstring names). --engine takes engines.trainable(), as train.py does, so an engine that
may not train is refused by the parser; --road is any road train.DESIGN_DT holds, checked by the
probe, whose design step must be this script's DT. Until 31 October the script hard-coded the B58
and the extremes roads; "--engine b58 --road extremes" runs exactly what it ran then. --merge reads
both from the two files' plans and refuses two files that differ in either, as before; --selftest
takes neither. Row 114's protocol, once per engine after the plant commit, is
docs/build_step_2/DEVICE_RUNBOOK.md's.

Asked by Ghassan, 21 October 2026: the four-engine test trains on a new device, and before it
does, measure whether training there is faster on its CPU or its GPU. RUN IT ON THE TRAINING
DEVICE, not on the team laptop. Revised the same day after two reviews of it, one of what it
measures and one of how it behaves when it runs.

WHY THE ANSWER IS NOT OBVIOUS, AND WHY IT HAS TO BE MEASURED THERE
------------------------------------------------------------------
A training step is two jobs. The PLANT (the engine cycle and the thermal network, numpy on one
CPU core) was 84 % of a step on the team laptop on 29 September (61.6 ms of plant against
11.5 ms of SAC update), and a GPU cannot run it. Only SAC's gradient update, a small network
([256, 256], batch 256), can move to a GPU, and a network that small gains little there while
every run on the GPU pays for a CUDA context in video memory. So on the plant as it is, a GPU
can save at most the update's share of a step, and running many CPU processes at once is the
usual winner. But that is the laptop's arithmetic. A machine with few CPU cores and a strong GPU,
or the table backend of decision 28 (which makes the plant 6-8 times cheaper, so the update
becomes the larger part), can turn it around. Hence a measurement, on the machine that will
train, at the concurrency it would train at.

Two rules decide the choice, not the speed alone:
  * CPU and CUDA train DIFFERENT agents from one seed (train.py). Rule 3 trains every seed, arm
    and engine of an experiment in ONE environment, so the device type is chosen once, before
    training, and written into the preregistration (decision 32). Never mix the two.
  * A device that does not train the same agent twice from the same seed cannot be used: section
    4 runs seed 0 twice on each device, before section 3, and compares the trained networks bit
    for bit; on CUDA two copies of seed 0 also train inside every row of section 3 with two runs
    or more, sharing the GPU as production will.

WHAT IT MEASURES, in the order it runs (1, 2, 4, 3)
  1. The machine: the CPU, the CPUs this process may use (its affinity, and a Linux cgroup's
     quota), the cores, RAM, the power plan, every GPU nvidia-smi sees and its driver, the torch
     build, the versions check_training_device.CRITICAL names, and whether CUDA RUNS here (a
     kernel and a cuBLAS product in a child process, not torch.cuda.is_available()).
  2. The parts of one step, each in a child process with one thread, so this process never holds
     a CUDA context: the plant step (the --road roads, the --engine plant, the neutral action), and on
     each device SAC's gradient update as training makes it (train() with gradient_steps=1, batch
     256) and the choice of one action (predict: on CUDA a round trip to the GPU every step).
     They say WHY section 3 comes out as it does; section 3 is the measurement.
  4. Determinism on each device: seed 0 trained twice, one run at a time, for 1 800 steps (two
     finished extremes episodes of 899 steps, so the curve holds something), compared by
     check_training_device.fingerprint_dir: every tensor, the counters, every recorded step and
     the curve. A device that fails it is not timed in section 3.
  3. Training as train_all.py runs it: N copies of train.py at once (one thread each, --engine,
     --road, --dt and --device passed explicitly, --buffer 450000 so each run allocates
     what a 450 000-step run does), for each device and each N, every N measured --repeats times,
     the repeats interleaved. In the two-environment workflow below each run of this script
     measures one device, so the CPU's rows and the GPU's are hours apart, never interleaved,
     and --merge refuses two files that are not one environment apart from the torch build. N:
     1, half the physical cores, the physical cores and every usable CPU, capped on each device
     after its single-run row by what fits at production size (RAM, and on CUDA video memory).
     Per row, from each run's config.json:
       UPPER  the sum of the runs' own rates, each over its own learn() window, part of which it
              spent with fewer competitors (another run still starting, or already done);
       LOWER  every step of every run over the span from the first start to the last finish,
              which counts that ramp and tail at the rate of a part-empty machine.
     The rate train_all.py sustains with every slot full lies between the two while adding a run
     does not lower the total (below saturation). EVERY DECISION USES THE LOWER BOUND. Beside
     them: the overlap (the time all N ran at once, as a share of a run; under 0.9 the row is
     "not steady": re-run with more --steps), the machine's available memory before the batch and
     its lowest during it, the production estimate, the video memory per run, the CPU load
     before the batch. SB3 makes no update and no prediction in its first 100 steps, 3.3 % of a
     3 000-step run: at the laptop's 16 % update share both bounds read about 0.5 % high
     (arithmetic, not a measurement).
Every run trains into a temporary folder outside the repository and is deleted afterwards, the
folder SB3's logger makes with it (SB3_LOGDIR): a benchmark, not an experiment. Nothing is written
to runs/.

THE RULE. A device is named only when its lowest lower bound over the repeats, at its best
concurrency, beats the other device's highest upper bound over the repeats and over EVERY one of
its usable concurrencies (those that ran cleanly in every repeat planned and fit at production
size, on a device that trained the identical agent twice); otherwise "no clear winner, keep CPU",
the environment the lock, X1, X2 and the L8 certificate already describe. A device is named alone
only when the other cannot be used: it did not train the identical agent twice, or none of its
concurrencies ran cleanly in every repeat planned and fitted. When a device's seed 0 was not
trained twice to the end (--no-determinism, a timeout, an error), no device is named: unchecked
is not failed. One environment's file names the CPU alone only when nvidia-smi ran and lists no
GPU; when nvidia-smi gives no answer, whether a GPU is here is not known. The days: 4 engines x
ceil(3 arms x seeds / N) waves of 450 000-step runs at the per-run lower rate (decisions 24, 27,
29, 30); --window-days gives the most seeds per arm that fit. On the device named, N is the
concurrency that trains the experiment soonest, waves counted, which need not be the fastest.
The launcher's command is printed; train_all.py trains two arms a seed today (blinded and one
sighted horizon), not decision 27's three, so its runs are not the ones the days count.

VALID FOR THE CYCLE BACKEND AND THE ENGINE MEASURED ONLY. Decision 28 trains on each engine's table
if it passes its gates, a plant 6-8 times cheaper, which can reverse the answer; section 2 prints
that case, as arithmetic. Re-run this on the table backend, and on each engine once it exists, before
the device type is written into the preregistration. Row 114 (30 October 2026) fixes how: the device
is chosen once, on the B58 and the extremes roads, before the first arming; after the plant commit
each engine's many-run rate is measured once, with --engine and --road, at the training's
concurrency, on row 116's training road (the runbook's commands).

THE GPU NEEDS ITS OWN TORCH. requirements-lock.txt pins the CPU build (torch 2.14.0+cpu). Run this
script in that environment with --device cpu. Install the CUDA build of the same torch version in
a separate environment and run it there with --device cuda ONLY: in a CUDA build every process
loads cuBLAS and cuDNN, so its CPU rows are not the lock's. Then --merge the two files. If CUDA
wins it gets its own lock file, and the experiment's environment is that one (decision 32). The
CUDA children run with CUBLAS_WORKSPACE_CONFIG set to check_training_device.CUBLAS_WORKSPACE (the
one value train.py accepts on CUDA; that constant says why) and torch's deterministic
algorithms, as train.py trains on CUDA. On Windows set the NVIDIA driver's "CUDA - Sysmem
Fallback Policy" to "Prefer No Sysmem Fallback" for this python.exe while benchmarking:
otherwise a GPU short of video memory spills into system RAM and its row reads as merely slow
(rows at 95 % of the GPU's memory are flagged). Only GPU 0 is used.

OUTPUT: a table, a recommendation, and a JSON file written after every section (--out; by default
benchmark_<host>_torch<build>_<date>_<time>.json in the current folder; an existing file is never
overwritten). Commit it under results/benchmarks/ if it should be kept; it carries no agent and
no result.
"""
import argparse
import glob
import hashlib
import json
import math
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, "train.py")
# The engine and the road are the run's --engine and --road (rows 114 and 118): they were the
# constants ENGINE = "b58" and ROAD = "extremes" until 31 October 2026. They travel in the run's
# `plan` (the JSON's "plan" block: plan["engine"], plan["road"], plan["dt"]) to every command.
DT = 1.0                             # the step every road is benchmarked at, passed explicitly; the probe
                                     # refuses a --road whose train.DESIGN_DT differs
# The experiment the day counts are for: 4 engines x 3 arms x seeds x 450 000 steps (decisions
# 24, 27, 29), seeds per arm fixed from this rate and the window, target at least 20 (decision 30).
ENGINES, ARMS, SEEDS_TARGET, PROD_STEPS = 4, 3, 20, 450_000
PROD_BUFFER = PROD_STEPS             # train.buffer_size of a 450 000-step run: the run's own length
DET_STEPS = 1_800                    # two finished extremes episodes of 899 steps (engine_env: truncated at k >= n - 1)
REPEATS = 2                          # each concurrency measured twice, interleaved
# The limits below are the reviews' (21 October 2026), not measurements; each says what it guards.
RESERVE_GB = 5.0                     # RAM kept free at production size: run_phase_d.py's RESERVE_GB
VRAM_RESERVE_GB = 1.0                # video memory kept free at production size
VRAM_FULL = 0.95                     # memory.used at this share of the GPU's: flagged (a Windows driver may spill into RAM)
LOAD_LIMIT_PCT = 5.0                 # CPU load before a batch above this: the row is flagged "loaded"
STEADY_OVERLAP = 0.9                 # all N together for less than this share of a run: "not steady"
RECORDER_LISTS_GB = 0.02             # ActionRecorder's lists at their fullest (CHUNK = 10 000 steps of 47 fields as Python objects): the review's estimate
BATCH_SLACK_S = 600                  # a batch's timeout: this, plus three times its expected training time
SAVE_TRIES, SAVE_WAIT_S = 5, 1.0     # the JSON's write retried this often, this far apart: on Windows a reader holding it open refuses os.replace
# What a run timed, from its config.json: --merge refuses two files whose rows timed different plants
PLANT_KEYS = ("plant_sha", "derived_sha", "engine", "engine_sha", "backend")
# PYTHONDONTWRITEBYTECODE: no child leaves a __pycache__ in the repository (the review of 31 October
# 2026, R0-4); it changes no trained bit
ONE_THREAD = dict(OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONUNBUFFERED="1",
                  PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
PART_TAG = "BENCHMARK_PART "         # the line a --part child prints its result on
# The options train.build_env takes for a road beside its name, as train.py passes them for a run with
# neither --scored-share nor --roads-record (train.py, road_options): section 2 builds the environment
# that section 3's train.py runs build. Row 116's road takes two; every other road takes none.
ROAD_OPTIONS = {"four_engine": dict(scored_share=False, roads_record=None)}


def validity(engine_id):
    """The recommendation's last line, naming the engine measured (the B58's words, as they were
    printed before --engine existed, for engine_id "b58")."""
    return (f"Valid for the cycle backend and the {engine_id.upper()} only. Decision 28 trains on each "
            "engine's table if it passes its gates (a 6-8x cheaper plant), which can reverse this. Re-run "
            "on the table backend, and on each engine once it exists, before the device type is written "
            "into the preregistration.")


# ------------------------------------------------------------------------- the machine
def cpu_name():
    try:
        if sys.platform == "win32":
            import winreg
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                               r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            return winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()
        if os.path.exists("/proc/cpuinfo"):
            with open("/proc/cpuinfo", encoding="utf-8") as fh:
                for line in fh:
                    if line.startswith("model name"):
                        return line.split(":", 1)[1].strip()
        if sys.platform == "darwin":
            return subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                                  capture_output=True, text=True).stdout.strip()
    except Exception:
        pass
    return platform.processor() or "unknown"


def usable_cpus():
    """The CPUs this process may run on: its affinity (os.process_cpu_count, Python 3.13; Linux's
    sched_getaffinity before it) and, on Linux, the cgroup's CPU quota (cpu.max, or v1's cfs
    files), a fraction of a CPU rounded down. os.cpu_count() counts the whole machine: under
    Docker --cpus=8 or a Slurm allocation on a 64-thread host the grid would have put 64 runs on
    8 CPUs and never tried 8 (the review of 21 October 2026)."""
    if hasattr(os, "process_cpu_count"):
        n = os.process_cpu_count()
    elif hasattr(os, "sched_getaffinity"):
        n = len(os.sched_getaffinity(0))
    else:
        n = os.cpu_count()
    quota = None
    try:
        with open("/sys/fs/cgroup/cpu.max", encoding="utf-8") as fh:
            q, p = fh.read().split()[:2]
        quota = None if q == "max" else int(q) / int(p)
    except (OSError, ValueError):
        try:
            with open("/sys/fs/cgroup/cpu/cpu.cfs_quota_us", encoding="utf-8") as fh:
                q = int(fh.read())
            with open("/sys/fs/cgroup/cpu/cpu.cfs_period_us", encoding="utf-8") as fh:
                p = int(fh.read())
            quota = q / p if q > 0 else None
        except (OSError, ValueError):
            pass
    if quota is not None:
        n = min(n or 1, max(1, int(quota)))
    return max(1, n or 1)


def power_plan():
    """The setting that moves per-core speed: Windows' active power scheme (powercfg), Linux's
    frequency governor of cpu0. None when neither can be read."""
    try:
        if sys.platform == "win32":
            r = subprocess.run(["powercfg", "/getactivescheme"], capture_output=True, text=True,
                               errors="replace", timeout=20)
            return r.stdout.strip() or None
        with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor", encoding="utf-8") as fh:
            return fh.read().strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def nvidia_smi(*query):
    """The rows nvidia-smi answers a --query-... with (csv, no header, no units), each a list of
    fields, or None when there is no nvidia-smi or it fails. nvidia-smi is its own process: asking
    it touches no CUDA in this one."""
    try:
        r = subprocess.run(["nvidia-smi", *query, "--format=csv,noheader,nounits"],
                           capture_output=True, text=True, errors="replace", timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return [[f.strip() for f in line.split(",")] for line in r.stdout.splitlines() if line.strip()]


def gpus():
    """Every GPU nvidia-smi sees: index, name, memory and driver, and on Windows the driver model
    (WDDM or TCC). An empty list when nvidia-smi ran and lists none; None when it gave no answer
    (none installed, or it failed), so that not knowing is never read as "no GPU" (the review of
    21 October 2026)."""
    rows = nvidia_smi("--query-gpu=index,name,memory.total,driver_version")
    if rows is None:
        return None
    out = [dict(index=r[0], name=r[1], memory_total_mib=_num(r[2]), driver=r[3])
           for r in rows if len(r) >= 4]
    if out and sys.platform == "win32":
        for g, r in zip(out, nvidia_smi("--query-gpu=driver_model.current") or []):
            g["driver_model"] = r[0]
    return out


def gpu_presence(m):
    """Whether the machine `m` (machine()'s dict) has a GPU: True when nvidia-smi lists one or
    CUDA ran here, False when nvidia-smi ran and lists none, None when it gave no answer."""
    if m.get("gpus") or (m.get("cuda") or {}).get("ok"):
        return True
    return None if m.get("gpus") is None else False


def gpu_memory():
    """[(used MiB, total MiB, utilisation %), ...], one per GPU, or None without nvidia-smi."""
    rows = nvidia_smi("--query-gpu=memory.used,memory.total,utilization.gpu")
    return None if rows is None else [tuple(_num(f) for f in (r + [None] * 3)[:3]) for r in rows]


def machine(probe):
    """The machine, with what the probe child found out about torch and CUDA. This process never
    imports torch to ask."""
    import psutil
    import check_training_device as CTD
    have = CTD.installed()
    vm = psutil.virtual_memory()
    m = dict(host=platform.node(), platform=platform.platform(), cpu=cpu_name(),
             logical_cpus=os.cpu_count(), usable_cpus=usable_cpus(),
             physical_cpus=psutil.cpu_count(logical=False),
             ram_gb=round(vm.total / 2**30, 1), available_gb=round(vm.available / 2**30, 1),
             python=platform.python_version(), torch=probe["torch"], torch_cuda=probe["torch_cuda"],
             packages={k: have.get(k) for k in CTD.CRITICAL}, power=power_plan(), gpus=gpus(),
             cuda=probe.get("cuda"), engines_known=probe.get("engines_known"),
             engines_trainable=probe.get("engines_trainable"))
    return m


def devices_available(asked, m):
    """The asked devices that can be measured here, and a note for each one that cannot."""
    out, notes = [], []
    cuda = m.get("cuda") or {}
    for d in asked:
        if d == "cuda" and not cuda.get("ok"):
            notes.append(f"cuda skipped: {cuda.get('why')}."
                         + ("" if m.get("torch_cuda") else
                            " Install the CUDA build of the same torch version in a separate "
                            "environment and run this script there with --device cuda."))
        else:
            out.append(d)
    if "cpu" in out and m.get("torch_cuda"):
        notes.append(f"the cpu rows are measured with torch {m['torch']}, a CUDA build, not "
                     "requirements-lock.txt's CPU build: measure the CPU in the lock's environment "
                     "and combine the two files with --merge")
    if m.get("gpus") and "cuda" not in asked and not cuda.get("ok"):
        notes.append(f"a GPU is here ({m['gpus'][0]['name']}, nvidia-smi) and this torch cannot use it: "
                     "measure it in a CUDA environment with --device cuda, then --merge the two files; "
                     "until then no device is named")
    if m.get("gpus") is None and not cuda.get("ok"):
        notes.append("nvidia-smi gave no answer here (none installed, or it failed): whether this "
                     "machine has a GPU is not known, so a CPU file names no device on its own")
    if len(m.get("gpus") or []) > 1:
        notes.append(f"{len(m['gpus'])} GPUs: only GPU 0 is used, as train.py's --device cuda uses it")
    return out, notes


def code_info():
    """Which code measured this: the commit, whether the tree was dirty, and the bytes of this
    file and of train.py (sha256, 16 characters), so two files from two versions are told apart."""
    def sha(path):
        try:
            with open(path, "rb") as fh:
                return hashlib.sha256(fh.read()).hexdigest()[:16]
        except OSError:
            return None

    def git(*args):
        try:
            r = subprocess.run(["git", *args], cwd=HERE, capture_output=True, text=True, timeout=30)
            return r.stdout.strip() if r.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            return None
    status = git("status", "--porcelain")
    return dict(git_head=git("rev-parse", "--short", "HEAD"),
                git_dirty=None if status is None else bool(status),
                benchmark_sha=sha(os.path.abspath(__file__)), train_sha=sha(TRAIN))


# ---------------------------------------------------- the child processes (--part)
def child_env(device, **extra):
    """Every child's environment: one thread, as train_all.py gives each run, and on CUDA the
    cuBLAS workspace train.py requires there (check_training_device.CUBLAS_WORKSPACE, the one
    constant every launcher sets)."""
    import check_training_device as CTD
    env = dict(os.environ, **ONE_THREAD, **extra)
    if device == "cuda":
        env["CUBLAS_WORKSPACE_CONFIG"] = CTD.CUBLAS_WORKSPACE
    return env


def child_result(cmd, env, timeout_s, label):
    """Run one child to its end, or kill it at timeout_s, and return the last PART_TAG line it
    printed. A child that died or was killed after printing one still returns it, `child_exit`
    saying how it ended: the probe prints a first line before its CUDA test, so a driver fault or
    a hang there reads as CUDA failing, not as torch failing to import (the review of 21 October
    2026). RuntimeError when it printed none."""
    p = subprocess.Popen(cmd, cwd=HERE, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, encoding="utf-8", errors="replace")
    killed = False
    try:
        so, se = p.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        _kill([p])
        try:
            so, se = p.communicate(timeout=30)
        except subprocess.TimeoutExpired:            # a process stuck in a driver call, unkillable
            raise RuntimeError(f"{label} hung for {timeout_s:g} s and could not be stopped") from None
        killed = True
    except BaseException:
        _kill([p])
        raise
    ended = f"killed after {timeout_s:g} s" if killed else f"exited {p.returncode}"
    for line in reversed(so.splitlines()):
        if line.startswith(PART_TAG):
            try:
                res = json.loads(line[len(PART_TAG):])
            except ValueError:                       # cut short by the crash: an earlier line may be whole
                continue
            if killed or p.returncode != 0:
                res["child_exit"] = ended + (": " + se[-400:].strip() if se.strip() else "")
            return res
    raise RuntimeError(f"{label} {ended}: " + (se or so)[-800:].strip())


def run_part(name, plan, device=None, timeout_s=900):
    """One part run in a child process (--part), its result read off the line it prints. A child,
    so this process never holds a CUDA context: torch keeps one until its process exits, a GPU in
    EXCLUSIVE_PROCESS mode then refuses every train.py, and in the default mode it takes video
    memory the rows would have had (the review of 21 October 2026). The plant is timed there too,
    under the one thread train_all.py gives a run. The child is given the run's --engine and
    --road (`plan`), as every train.py is."""
    cmd = [sys.executable, os.path.abspath(__file__), "--part", name,
           "--engine", plan["engine"], "--road", plan["road"]]
    if device:
        cmd += ["--device", device]
    return child_result(cmd, child_env(device), timeout_s, f"--part {name} {device or ''}".strip())


def part_probe(road):
    """--part probe: this environment's torch, the design step train.py holds for the road (None
    when train.py has no such road, with the roads it has), and whether CUDA RUNS here: an
    element-wise kernel and a cuBLAS product under the deterministic settings train.py trains CUDA
    with. torch.cuda.is_available() alone says yes to a GPU the wheel has no kernels for ('no
    kernel image is available'), to one that is busy and to one with no memory left (the review of
    21 October 2026)."""
    import torch
    import engines
    from train import DESIGN_DT
    # the plants that may train beside the ones registered (decision 47, amendment B7, 22 October
    # 2026): an EPA engine is registered and refused by train.py until schema 4 and its validation
    out = dict(torch=torch.__version__, torch_cuda=torch.version.cuda, design_dt=DESIGN_DT.get(road),
               roads_known=sorted(DESIGN_DT),
               engines_known=engines.known(), engines_trainable=list(engines.trainable()))
    if torch.version.cuda is None:
        out["cuda"] = dict(ok=False, why=f"this torch ({torch.__version__}) is a CPU build")
        return out
    # a first line, before the CUDA test: if a driver fault kills this process in it, or it
    # hangs there, the parent reads this one (child_result), not "torch does not import"
    print(PART_TAG + json.dumps(dict(out, cuda=dict(ok=False, why="the CUDA test did not finish"))),
          flush=True)
    try:
        torch.use_deterministic_algorithms(True)
        x = torch.ones(1, device="cuda").add_(1)
        y = torch.ones(64, 64, device="cuda") @ torch.ones(64, 64, device="cuda")
        if x.item() != 2.0 or y[0, 0].item() != 64.0:
            raise RuntimeError(f"wrong answers on the GPU: {x.item()}, {y[0, 0].item()}")
        p = torch.cuda.get_device_properties(0)
        out["cuda"] = dict(ok=True, gpu=p.name, gpu_memory_gb=round(p.total_memory / 2**30, 1),
                           gpu_count=torch.cuda.device_count(), capability=f"{p.major}.{p.minor}")
    except Exception as e:
        out["cuda"] = dict(ok=False, why=f"CUDA does not run here: {e!r}")
    return out


def part_plant(engine_id, road, n_steps=200):
    """--part plant: seconds per environment step, the plant alone (the --road roads, the --engine
    plant, the neutral action), and the backend it was computed on."""
    import numpy as np
    import engines
    import fingerprint as FP
    from engine_env import neutral_action
    from train import DURATION_S, build_env
    env = build_env(True, 0, DURATION_S, road, DT, plant=engines.get(engine_id), **ROAD_OPTIONS.get(road, {}))
    env.reset(seed=0)
    a = np.asarray(neutral_action(), dtype=np.float32)
    for _ in range(10):                              # warm-up
        env.step(a)
    t0 = time.perf_counter()
    for _ in range(n_steps):
        _, _, term, trunc, _ = env.step(a)
        if term or trunc:
            env.reset()
    return dict(plant_s=(time.perf_counter() - t0) / n_steps, steps=n_steps,
                backend=FP.backend_of(env.unwrapped), engines_timed=[engine_id])


def part_sac(device, engine_id, road, n_updates=200, warm=20, n_predict=500):
    """--part sac: on one device, seconds per SAC gradient update as training makes it (train()
    with gradient_steps=1 and batch 256 after every environment step, the [256, 256] network
    train.py uses, its per-call learning-rate update and logging included), on random transitions
    in the replay buffer; seconds per action chosen (predict: the observation to the device, the
    actor, the action back); and the bytes one replay-buffer transition and one recorded step
    take, for the production memory estimate. Nothing learned is kept."""
    import numpy as np
    import torch
    from stable_baselines3 import SAC
    from stable_baselines3.common.logger import Logger
    import engines
    import train as T
    torch.set_num_threads(1)                         # what train_all.py's OMP_NUM_THREADS=1 gives
    if device == "cuda":
        torch.use_deterministic_algorithms(True)     # as train.check_device sets it for CUDA
    env = T.build_env(True, 0, T.DURATION_S, road, DT, plant=engines.get(engine_id), **ROAD_OPTIONS.get(road, {}))
    model = SAC("MlpPolicy", env, seed=0, device=device, buffer_size=5000, learning_starts=0,
                verbose=0)
    if model.device.type != device:
        raise RuntimeError(f"asked for {device}, stable-baselines3 gave {model.device}")
    # A Logger with no folder: configure(None, []) would leave an SB3-<time> folder in the
    # system's temporary directory (the review of 21 October 2026).
    model.set_logger(Logger(folder=None, output_formats=[]))
    rb = model.replay_buffer
    per_transition = sum(x[0].nbytes for x in (rb.observations, getattr(rb, "next_observations", None),
                                               rb.actions, rb.rewards, rb.dones, rb.timeouts)
                         if x is not None)
    rng = np.random.default_rng(0)
    ob = env.observation_space.shape
    ac = env.action_space.shape
    for _ in range(2000):
        model.replay_buffer.add(rng.standard_normal((1, *ob)).astype(np.float32),
                                rng.standard_normal((1, *ob)).astype(np.float32),
                                rng.uniform(-1, 1, (1, *ac)).astype(np.float32),
                                rng.standard_normal(1).astype(np.float32),
                                np.zeros(1, dtype=np.float32), [{}])
    sync = torch.cuda.synchronize if device == "cuda" else (lambda: None)
    for _ in range(warm):
        model.train(gradient_steps=1, batch_size=256)
    sync()
    t0 = time.perf_counter()
    for _ in range(n_updates):
        model.train(gradient_steps=1, batch_size=256)
    sync()
    update_s = (time.perf_counter() - t0) / n_updates
    obs = env.reset(seed=0)[0]
    for _ in range(20):
        model.predict(obs, deterministic=False)
    sync()
    t0 = time.perf_counter()
    for _ in range(n_predict):
        model.predict(obs, deterministic=False)
    sync()
    predict_s = (time.perf_counter() - t0) / n_predict
    return dict(device=str(model.device), update_s=update_s, predict_s=predict_s,
                bytes_per_transition=int(per_transition), record_bytes_per_step=record_bytes_per_step(ob, ac))


def record_bytes_per_step(ob, ac):
    """The bytes one step takes as ActionRecorder keeps it, through train._record_arrays: what
    train.merge_records holds per step. Its dtypes follow step_record.cast, by the field's name
    (float16 for the observation) and by its value's type (an integer is kept as it is, float32
    for every other value), so each field of the synthetic step has the type the recorder is
    given: the step and the episode ints (int32 in _record_arrays), the gear an int too
    (step_record.gear; int64), every other field a float. 274 B a step with the env's 23 inputs
    and 5 actions, as in each of X1's 46 records (runs/extremes_dt1/*/train_record.npz on the team
    laptop: 13 700 000 B over 50 000 steps, the same 47 fields and dtypes; checked 21 October
    2026); a float gear gave 270 (the review of 21 October 2026). An import of train: no SAC is
    built, no plant stepped."""
    import numpy as np
    import train as T
    one = {k: [1.0] for k in T.REC_INFO}
    one.update(step=[1], episode=[0], reward=[0.0], gear=[1], action=[np.zeros(ac, np.float32)],
               obs=[np.zeros(ob, np.float32)])
    for k in T.REC_VEC:
        one[k] = [np.zeros(5 if k == "applied" else 3, np.float32)]
    return int(sum(v.nbytes for v in T._record_arrays(one).values()))


# ------------------------------------------------------------------ a batch of runs
def _memory(me):
    """One snapshot of this process's descendants: their resident and their private bytes, each
    summed. Enumerated afresh every time, so a reaped PID is never read, and each process guarded
    on its own, so one that exits mid-poll costs only itself (the review of 21 October 2026).
    Private: Windows' committed private bytes; Linux's resident less shared, its anonymous memory,
    read from statm, where USS would walk every mapping of every process at every poll, on the
    CPU the rows are timing."""
    import psutil
    rss = private = 0
    for ch in me.children(recursive=True):
        try:
            mi = ch.memory_info()
        except psutil.Error:
            continue
        rss += mi.rss
        private += getattr(mi, "private", 0) or max(0, mi.rss - getattr(mi, "shared", 0))
    return rss, private


def _kill(procs):
    """Every child still running killed, its own children first (on Windows a venv's python.exe
    is a launcher whose interpreter is its child), then reaped."""
    import psutil
    for p in procs:
        if p.poll() is not None:
            continue
        try:
            kids = psutil.Process(p.pid).children(recursive=True)
        except psutil.Error:
            kids = []
        for k in kids:
            try:
                k.kill()
            except psutil.Error:
                pass
        try:
            p.kill()
        except OSError:
            pass
        try:
            p.wait(timeout=30)
        except subprocess.TimeoutExpired:
            pass


def run_batch(cmds, workdir, env_extra=None, poll_s=2.0, deadline_s=None, device="cpu"):
    """Start every command at once; wait for all of them, or until deadline_s, and return what
    the batch took: the wall seconds, the exit codes, whether the deadline killed it; the
    machine's available memory before the launch and its lowest while the batch ran (the memory
    the batch took, a shared library page counted once, which a sum over processes counts once
    per process), with the peaks of the processes' resident and private sums beside it; and on
    CUDA the video memory nvidia-smi saw, every GPU before the launch and at its peak. Every child
    is killed on the way out, on Ctrl+C or an error too, and each child's SB3 logger folder lands
    in workdir (SB3_LOGDIR), which the caller deletes."""
    import psutil
    env = dict(child_env(device, SB3_LOGDIR=os.path.join(workdir, "sb3")), **(env_extra or {}))
    me = psutil.Process()
    gpu0 = gpu_memory() if device == "cuda" else None
    gpu_peak = [g[0] or 0.0 for g in gpu0] if gpu0 else None
    util_peak = None
    avail0 = min_avail = psutil.virtual_memory().available
    peak_rss = peak_private = 0
    logs, procs, timed_out = [], [], False
    t0 = time.perf_counter()
    try:
        for i, c in enumerate(cmds):
            fh = open(os.path.join(workdir, f"run{i}.log"), "w", encoding="utf-8")
            logs.append(fh)
            procs.append(subprocess.Popen(c, cwd=HERE, env=env, stdout=fh, stderr=subprocess.STDOUT))
        polls = 0
        while any(p.poll() is None for p in procs):
            min_avail = min(min_avail, psutil.virtual_memory().available)
            rss, private = _memory(me)
            peak_rss, peak_private = max(peak_rss, rss), max(peak_private, private)
            polls += 1
            # nvidia-smi is a process of its own: every fifth poll, so the CUDA rows do not pay
            # for it on the CPU they wait on (a context's memory, once made, stays until the end)
            if gpu_peak is not None and polls % 5 == 1:
                for j, g in enumerate((gpu_memory() or [])[:len(gpu_peak)]):
                    gpu_peak[j] = max(gpu_peak[j], g[0] or 0.0)
                    if g[2] is not None:
                        util_peak = max(util_peak or 0.0, g[2])
            if deadline_s is not None and time.perf_counter() - t0 > deadline_s:
                timed_out = True
                break
            time.sleep(poll_s)
    finally:
        _kill(procs)
        for fh in logs:
            fh.close()
    out = dict(wall_s=round(time.perf_counter() - t0, 1), codes=[p.returncode for p in procs],
               timed_out=timed_out,
               ram=dict(avail_before_gb=round(avail0 / 2**30, 2), avail_min_gb=round(min_avail / 2**30, 2),
                        used_gb=round((avail0 - min_avail) / 2**30, 2),
                        peak_rss_sum_gb=round(peak_rss / 2**30, 2),
                        peak_private_sum_gb=round(peak_private / 2**30, 2)))
    if gpu0:
        grew = [pk - (g[0] or 0.0) for pk, g in zip(gpu_peak, gpu0)]
        j = max(range(len(grew)), key=grew.__getitem__)       # the GPU the batch used
        total = gpu0[j][1]
        out["vram"] = dict(gpu_index=j, before_mib=gpu0[j][0], peak_mib=gpu_peak[j], total_mib=total,
                           per_run_mib=round(grew[j] / max(1, len(cmds)), 1), util_peak_pct=util_peak,
                           near_full=bool(total) and gpu_peak[j] >= VRAM_FULL * total)
    elif device == "cuda":
        # not measured is not none used: fits() and cap_runs() cannot judge the video memory,
        # and the recommendation says so (the review of 21 October 2026)
        out["vram"] = dict(unknown=("nvidia-smi gave no answer" if gpu0 is None else "nvidia-smi listed no GPU")
                           + " before the batch: video memory not measured")
    return out


def read_runs(out):
    """Every run under `out` that wrote a config.json, with what it says about the session:
    train.py writes `started` just before learn() and, once it returns and the run is saved,
    `finished`, the rate and the device it trained on; and the plant it trained on (PLANT_KEYS,
    meta.json's fingerprint fields that config.json repeats)."""
    runs = []
    for cfg in sorted(glob.glob(os.path.join(glob.escape(out), "**", "config.json"), recursive=True)):
        try:
            with open(cfg, encoding="utf-8") as fh:
                c = json.load(fh)
        except (OSError, ValueError):
            continue
        runs.append(dict(dir=os.path.dirname(cfg), seed=c.get("seed"), device=c.get("device"),
                         status=c.get("status"), started=c.get("started"), finished=c.get("finished"),
                         rate=c.get("steps_per_s_this_session"),
                         plant={k: c.get(k) for k in PLANT_KEYS}))
    return runs


def _plant_id(plant):
    return json.dumps(plant, sort_keys=True)


def bounds(runs, steps):
    """The throughput of the runs at once, bracketed (the measurement review of 21 October 2026):

      upper  the sum of the runs' own rates. Each rate is over its own learn() window, and while
             another run was still starting or already done, that run had more of the machine.
      lower  every step of every run over the span from the first start to the last finish, so
             the ramp and the tail count at the rate of a part-empty machine.

    Both hold while adding a run does not lower the total (below saturation); the rate with every
    slot full, which train_all.py sustains by refilling a slot within 20 s, lies between.
    `started` and `finished` are written to the second, truncated, so one second is added to every
    finish. overlap: the time all of them ran at once, as a share of the mean run (1.0: they
    started and stopped together); stagger_s: the spread of the starts."""
    rates = [r["rate"] for r in runs]
    a = [datetime.fromisoformat(r["started"]).timestamp() for r in runs]
    b = [datetime.fromisoformat(r["finished"]).timestamp() + 1.0 for r in runs]
    n = len(runs)
    mean_run = sum(bi - ai for ai, bi in zip(a, b)) / n
    return dict(upper_steps_per_s=round(sum(rates), 2),
                lower_steps_per_s=round(n * steps / (max(b) - min(a)), 2),
                overlap=round((min(b) - max(a)) / mean_run, 3), stagger_s=round(max(a) - min(a), 1),
                per_run_min=round(min(rates), 2), per_run_max=round(max(rates), 2))


def row_verdict(device, n, batch, runs, deadline_s):
    """Why a row is not clean, or [] when it is: every run exited 0 inside the deadline, all n
    finished, every one trained on the device asked for (config.json's device; SB3 falls back to
    the CPU without a word when CUDA is missing, and train.py now refuses that), and all on one
    plant (the code changed mid-batch otherwise)."""
    why = []
    if batch["timed_out"]:
        why.append(f"timed out after {deadline_s:.0f} s")
    if any(c != 0 for c in batch["codes"]):
        why.append(f"exit codes {batch['codes']}")
    if len(runs) != n:
        why.append(f"{len(runs)} of {n} runs finished")
    wrong = sorted({str(r["device"]) for r in runs if str(r["device"]).split(":")[0] != device})
    if wrong:
        why.append(f"trained on {', '.join(wrong)}")
    if len({_plant_id(r.get("plant")) for r in runs}) > 1:
        why.append("its runs trained on more than one plant (config.json's " + ", ".join(PLANT_KEYS) + ")")
    return why


def fingerprint_diff(a, b):
    """What differs between two check_training_device fingerprints: every tensor, every recorded
    field, the stable-baselines3 counters and the curve, the parts check_training_device.compare
    reads."""
    import check_training_device as CTD
    diff = [f"{part} {k}" for part in ("weights", "record") for k in sorted(set(a[part]) | set(b[part]))
            if a[part].get(k) != b[part].get(k)]
    diff += [f"counter {k}" for k in CTD.COUNTERS if a["counters"].get(k) != b["counters"].get(k)]
    if a["curve"] != b["curve"]:
        diff.append("curve.csv")
    return diff


def compare_runs(dir_a, dir_b):
    """Two run directories of one seed, fingerprinted and compared. The saved tensors are read
    onto the CPU (map_location), so this touches no CUDA here."""
    import check_training_device as CTD
    diff = fingerprint_diff(CTD.fingerprint_dir(dir_a), CTD.fingerprint_dir(dir_b))
    return dict(identical=not diff, n_differences=len(diff), first=diff[:5])


def _tail(out, i, n=600):
    try:
        with open(os.path.join(out, f"run{i}.log"), encoding="utf-8", errors="replace") as fh:
            return fh.read()[-n:]
    except OSError:
        return ""


def train_cmd(device, seed, steps, out, plan, buffer=None):
    """One train.py run as train_all.py starts it: --engine, --road and --dt explicit (a default
    that selects an experiment is the trap train.py's docstring names), --device always given;
    the engine, the road and the step are the run's plan's."""
    cmd = [sys.executable, TRAIN, "--engine", plan["engine"], "--road", plan["road"], "--dt", f"{plan['dt']:g}",
           "--steps", str(steps), "--seed", str(seed), "--device", device, "--out", out]
    if buffer is not None:
        cmd += ["--buffer", str(buffer)]
    return cmd


def batch_deadline(part, plant_s, n, steps, physical):
    """A batch's timeout: BATCH_SLACK_S for starting and saving, plus three times its expected
    training, a run's step from section 2 (plant, update, action) slowed by n / the physical cores
    where n is more. A CUDA child that hangs after a driver reset no longer blocks the benchmark."""
    step = plant_s + part["update_s"] + part["predict_s"]
    return BATCH_SLACK_S + 3 * steps * step * max(1.0, n / max(1, physical))


# ---------------------------------------------------------------- 4. determinism
def determinism(device, root, deadline, plan):
    """Section 4 on one device: seed 0 trained twice, one run at a time, DET_STEPS steps each
    with the default buffer (check_training_device's identity command, longer), and the two
    compared: every tensor of final.zip, the counters, every recorded step, the curve. Each run
    must have trained on `device`."""
    import check_training_device as CTD
    fps = []
    for k in (0, 1):
        out = tempfile.mkdtemp(prefix=f"det_{device}_{k}_", dir=root)
        try:
            b = run_batch([train_cmd(device, 0, DET_STEPS, out, plan)], out, deadline_s=deadline, device=device)
            runs = [r for r in read_runs(out) if r["rate"]]
            why = row_verdict(device, 1, b, runs, deadline)
            if why:
                return dict(device=device, identical=None, steps=DET_STEPS,
                            why=f"run {k}: " + "; ".join(why) + " -- " + _tail(out, 0, 300).strip())
            fps.append(CTD.fingerprint_dir(runs[0]["dir"]))
        finally:
            shutil.rmtree(out, ignore_errors=True)
    diff = fingerprint_diff(*fps)
    return dict(device=device, identical=not diff, steps=DET_STEPS, n_differences=len(diff),
                first=diff[:5], compared=dict(tensors=len(fps[0]["weights"]),
                                              record_fields=len(fps[0]["record"]),
                                              counters=len(CTD.COUNTERS)))


# ------------------------------------------------- 3. training as train_all.py runs it
def benchmark_concurrency(device, n, steps, root, deadline, plan):
    """Section 3, one row: n copies of train.py at once on `device`, each with the production
    replay buffer (--buffer PROD_BUFFER: the allocation a 450 000-step run makes; samples come
    from the filled part only, so the timing is the default buffer's). On CUDA with n >= 2 seed 0
    runs twice in the row (seeds 0, 0, 1, ..., n-2) and the two copies are compared as section 4
    compares its pair: determinism under the contention production will have."""
    import psutil
    out = tempfile.mkdtemp(prefix=f"{device}_{n}_", dir=root)
    try:
        seeds = [0, 0] + list(range(1, n - 1)) if device == "cuda" and n >= 2 else list(range(n))
        cmds = [train_cmd(device, s, steps, os.path.join(out, f"r{i}"), plan, buffer=PROD_BUFFER)
                for i, s in enumerate(seeds)]
        load = psutil.cpu_percent(interval=5)        # the machine's own load, before the batch
        b = run_batch(cmds, out, deadline_s=deadline, device=device)
        runs = [r for r in read_runs(out) if r["rate"]]
        why = row_verdict(device, n, b, runs, deadline)
        row = dict(device=device, runs=n, seeds=seeds, steps_per_run=steps, buffer=PROD_BUFFER,
                   background_cpu_pct=load, loaded=load > LOAD_LIMIT_PCT, wall_s=b["wall_s"],
                   exit_codes=b["codes"], ok=not why, why=why,
                   launcher_steps_per_s=round(n * steps / b["wall_s"], 2), ram=b["ram"],
                   plant=runs[0]["plant"] if runs else None)
        if "vram" in b:
            row["vram"] = b["vram"]
        if not why:
            row.update(bounds(runs, steps))
            row["steady"] = row["overlap"] >= STEADY_OVERLAP
            if device == "cuda" and n >= 2:
                twins = [r["dir"] for r in runs if r["seed"] == 0]
                row["seed0_twice"] = (compare_runs(*twins) if len(twins) == 2 else
                                      dict(identical=None, why=f"{len(twins)} runs of seed 0 found"))
        else:
            row["log_tails"] = [_tail(out, i) for i in range(len(cmds))]
        return row
    finally:
        shutil.rmtree(out, ignore_errors=True)        # a benchmark, not an experiment


def production_gb(row, part):
    """The memory the row's n runs would take at their peak as PROD_STEPS-step runs, GB: what the
    row took (the drop in the machine's available memory), plus for each run what a short run
    never holds -- the rest of its replay buffer (allocated at PROD_BUFFER by --buffer, only the
    first steps_per_run rows written, and a page never written takes no RAM; counted again if the
    system had taken it, an over-estimate, never under), train.merge_records's three copies of
    the whole record at the end (the chunks, their concatenation and the de-duplicated copy) and
    the recorder's lists at their fullest. None without the bytes it needs."""
    bt, br = (part or {}).get("bytes_per_transition"), (part or {}).get("record_bytes_per_step")
    if not (bt and br) or not row.get("ram"):
        return None
    per_run = ((PROD_BUFFER - row["steps_per_run"]) * bt + 3 * PROD_STEPS * br) / 2**30 + RECORDER_LISTS_GB
    return round(row["ram"]["used_gb"] + row["runs"] * per_run, 2)


def fits(row, part):
    """Whether the row's n runs fit at production size: production_gb within the available memory
    before the batch less RESERVE_GB, and on CUDA the GPU's peak during the batch -- what it held
    before the batch included, the desktop's or another job's -- within its total less
    VRAM_RESERVE_GB, the GPU never near full. A run's video memory does not grow with its length:
    the replay buffer is numpy in RAM, and only each sampled batch goes to the device
    (stable_baselines3/common/buffers.py, ReplayBuffer and to_torch). None when the RAM, or on
    CUDA the video memory, is not known (and the RAM fits)."""
    prod = production_gb(row, part)
    if prod is None:
        return None
    ok = prod <= row["ram"]["avail_before_gb"] - RESERVE_GB
    v = row.get("vram")
    if v and v.get("unknown"):
        return None if ok else False
    if v:
        ok = ok and not v["near_full"] and (not v["total_mib"] or
                                            v["peak_mib"] <= v["total_mib"] - 1024 * VRAM_RESERVE_GB)
    return ok


def cap_runs(row, part):
    """The most runs at once a device can hold at production size, from its single-run row: RAM
    by production_gb, and on CUDA the video memory left after what the GPU held before the batch
    and VRAM_RESERVE_GB, by what the one run took. Video memory that was not measured caps
    nothing (the recommendation says so)."""
    caps = []
    prod = production_gb(row, part)
    if prod:
        caps.append(int((row["ram"]["avail_before_gb"] - RESERVE_GB) / prod))
    v = row.get("vram")
    if v and v.get("per_run_mib") and v.get("total_mib"):
        caps.append(int((v["total_mib"] - (v.get("before_mib") or 0.0) - 1024 * VRAM_RESERVE_GB)
                        / v["per_run_mib"]))
    return max(1, min(caps)) if caps else None


# ---------------------------------------------------------------------- the report
def configurations(rows):
    """The rows of each (device, runs) taken together: clean only if it was measured in every
    repeat planned (a row's repeats_planned; 1 for a row without one) and every repeat ran
    cleanly -- once a lower concurrency fails in a repeat, that repeat skips the higher ones, and
    their one clean repeat is not the spread the rule asks for (the review of 21 October 2026);
    its lower bound the lowest repeat's, its upper bound the highest's."""
    groups = {}
    for r in rows:
        groups.setdefault((r["device"], r["runs"]), []).append(r)
    out = []
    for (d, n), rs in sorted(groups.items()):
        good = [r for r in rs if r.get("ok")]
        lows = [r["lower_steps_per_s"] for r in good]
        ups = [r["upper_steps_per_s"] for r in good]
        planned = max(r.get("repeats_planned", 1) for r in rs)
        out.append(dict(device=d, runs=n, repeats=len(rs), repeats_planned=planned,
                        ok=len(good) == len(rs) >= planned,
                        fits=all(r.get("fits") is not False for r in rs),
                        fits_known=all(r.get("fits") is not None for r in rs),
                        vram_unknown=any((r.get("vram") or {}).get("unknown") for r in rs),
                        steady=all(r.get("steady") for r in good), loaded=any(r.get("loaded") for r in rs),
                        lower_min=min(lows) if lows else None, lower_max=max(lows) if lows else None,
                        lower_median=statistics.median(lows) if lows else None,
                        upper_min=min(ups) if ups else None, upper_max=max(ups) if ups else None,
                        seed0_twice=[r["seed0_twice"].get("identical") for r in rs if r.get("seed0_twice")]))
    return out


def _days(lower, n, seeds):
    # in one product, so a whole number of seconds stays exact in floating point
    return ENGINES * math.ceil(ARMS * seeds / n) * PROD_STEPS * n / lower / 86400


def schedule(lower, n, seeds):
    """Days to train ENGINES x ARMS x seeds runs of PROD_STEPS, n at a time, at the lower bound.
    train_all.py takes one engine per call, so each engine runs ceil(ARMS x seeds / n) waves of
    runs at the per-run rate lower / n; a wave that is not full still takes a run's time."""
    waves = math.ceil(ARMS * seeds / n)
    return dict(seeds=seeds, per_run_steps_per_s=round(lower / n, 2),
                per_run_days=round(PROD_STEPS * n / lower / 86400, 2), waves_per_engine=waves,
                idle_slots_last_wave=waves * n - ARMS * seeds, days=round(_days(lower, n, seeds), 1))


def seeds_in_window(lower, n, window_days):
    """The most seeds per arm whose schedule fits in window_days (0 when not even one does). The
    days never fall as seeds are added, so the first that does not fit ends the search."""
    s = 0
    while s < 10_000 and _days(lower, n, s + 1) <= window_days:
        s += 1
    return s


def pick_runs(confs, window_days):
    """Of one device's usable concurrencies, the one that trains the experiment soonest at its
    lowest lower bound: with a window, the most seeds per arm in it (then the fewest days);
    without, the fewest days for SEEDS_TARGET seeds. The waves are counted, so a concurrency
    that packs the ARMS x seeds runs into full waves can beat a faster one that leaves slots
    idle (the measurement review of 21 October 2026)."""
    def key(c):
        days = _days(c["lower_min"], c["runs"], SEEDS_TARGET)
        return (-seeds_in_window(c["lower_min"], c["runs"], window_days), days) if window_days else (days,)
    return min(confs, key=key)


def _packing_lines(confs, window_days):
    out = [f"  every usable concurrency, at its lowest lower bound ({SEEDS_TARGET} seeds per arm"
           + (f"; seeds that fit {window_days:g} days" if window_days else "") + "):"]
    for c in sorted(confs, key=lambda c: c["runs"]):
        s = schedule(c["lower_min"], c["runs"], SEEDS_TARGET)
        out.append(f"    {c['runs']:>4} at once  {c['lower_min']:>8} steps/s  {s['per_run_steps_per_s']:>6} a run  "
                   f"{s['waves_per_engine']:>3} waves  {s['days']:>6} days"
                   + (f"  {seeds_in_window(c['lower_min'], c['runs'], window_days):>4} seeds" if window_days else ""))
    return out


def launcher_command(device, n, seeds, plan):
    return (f"python train_all.py --engine {plan['engine']} --road {plan['road']} --dt {plan['dt']:g} "
            f"--device {device} --jobs {n} --seeds 0-{seeds - 1} --steps {PROD_STEPS} "
            "--out runs/<the experiment's own>")


def _schedule_lines(c, window_days):
    s = schedule(c["lower_min"], c["runs"], SEEDS_TARGET)
    out = [f"  {c['runs']} at once: {s['per_run_steps_per_s']} steps/s per run, so a "
           f"{PROD_STEPS:,}-step run takes {s['per_run_days']} days; {SEEDS_TARGET} seeds per arm "
           f"are {ARMS} x {SEEDS_TARGET} runs per engine in {s['waves_per_engine']} waves "
           f"({s['idle_slots_last_wave']} slots idle in the last), x {ENGINES} engines: "
           f"{s['days']} days of training, before scoring"]
    if window_days:
        k = seeds_in_window(c["lower_min"], c["runs"], window_days)
        out.append(f"  in a {window_days:g}-day window: at most {k} seeds per arm (decision 30)")
    return out


def recommend(rows, det, measured, gpu_present, builds, window_days=None, smoke=False, *, plan):
    """THE RULE (the docstring), applied to section 3's rows and section 4's verdicts, from one
    environment's file or, by --merge, from both. `device` is None unless a device may be named:
    seed 0 trained twice to the end on every device measured, both device types measured (or
    nvidia-smi ran and lists no GPU: gpu_present False; None is "nvidia-smi gave no answer"),
    and not a smoke test. The margin compares one device's lowest lower bound, at its best
    concurrency, with the other's highest upper bound at ANY of its usable concurrencies: the
    other's throughput could be that high wherever it peaks (the review of 21 October 2026).
    Every number it gives is the lower bound's. `plan` is the run's (its engine, road and step:
    the launcher's command and the validity line name them)."""
    confs = configurations(rows)
    validity_line = validity(plan["engine"])
    res = dict(device=None, runs=None, clear=None, smoke_test=smoke, validity=validity_line,
               configurations=confs)
    if not measured:
        res["text"] = "no device was measured"
        return res
    if not det:
        res["text"] = ("determinism was not checked (--no-determinism): no device is recommended "
                       "until seed 0 trains identically twice on it")
        return res
    # unchecked is not failed: a device whose pair did not finish (not checked, timed out, an
    # error) would otherwise hand the other one the win as "the only usable device"
    unknown = {d: str((det.get(d) or {}).get("why") or "not checked") for d in sorted(measured)
               if (det.get(d) or {}).get("identical") is None}
    if unknown:
        res.update(not_checked=unknown)
        res["text"] = "\n".join(
            ["determinism is not known on every device measured, so no device is named: seed 0 must "
             "train the identical agent twice on each (section 4)"]
            + [f"  {d.upper()} (torch {builds.get(d)}): seed 0 was not trained twice to the end ({w})"
               for d, w in unknown.items()])
        return res
    best, top, usable_by, why_not = {}, {}, {}, {}
    for d in sorted(measured):
        v = det[d]
        twins = [t for c in confs if c["device"] == d for t in c["seed0_twice"]]
        usable = [c for c in confs if c["device"] == d and c["ok"] and c["fits"]]
        if v["identical"] is not True:
            why_not[d] = ("seed 0 did not train the identical agent twice ("
                          + str(v.get("first") or v.get("why") or "") + ")")
        elif False in twins:
            why_not[d] = "two copies of seed 0 trained different agents while they shared the GPU"
        elif not usable:
            why_not[d] = "no concurrency ran cleanly in every repeat planned and fitted at 450 000-step size"
        else:
            usable_by[d] = usable
            best[d] = max(usable, key=lambda c: c["lower_min"])   # the device's throughput, for the rule
            top[d] = max(usable, key=lambda c: c["upper_max"])    # the most it could be, anywhere
    res.update(best={d: dict(runs=c["runs"], lower_min=c["lower_min"], upper_max=c["upper_max"],
                             highest_upper=top[d]["upper_max"], highest_upper_runs=top[d]["runs"])
                     for d, c in best.items()}, not_usable=why_not)
    lines = [f"  {d.upper()} (torch {builds.get(d)}): best {c['runs']} runs at once, "
             f"{c['lower_min']} to {c['upper_max']} steps/s in all (the lowest lower bound to the "
             f"highest upper bound of {c['repeats']} repeat(s)); its highest upper bound at any usable "
             f"concurrency {top[d]['upper_max']} ({top[d]['runs']} at once)" for d, c in sorted(best.items())]
    lines += [f"  {d.upper()} (torch {builds.get(d)}): not usable: {w}" for d, w in sorted(why_not.items())]
    if not best:
        res["text"] = "\n".join(["no device both ran cleanly, fitted at 450 000-step size and trained "
                                 "identically twice: do not train yet"] + lines)
        return res
    if len(measured) < 2:
        (d,) = measured
        if d != "cpu" or gpu_present is not False:
            other = "cuda" if d == "cpu" else "cpu"
            head = (f"only {d} measured, and nvidia-smi gave no answer here, so whether this machine has "
                    "a GPU is not known: no device is named. If it has one, measure cuda in its own "
                    "environment (--device cuda) and combine the two files with --merge CPU.json CUDA.json"
                    if d == "cpu" and gpu_present is None else
                    f"only {d} measured in this environment, so no device is named: measure {other} in "
                    f"its own environment (--device {other}) and combine the two files with "
                    "--merge CPU.json CUDA.json")
            res["text"] = "\n".join(
                [head] + lines
                + _schedule_lines(pick_runs(usable_by[d], window_days), window_days)
                + _packing_lines(usable_by[d], window_days) + [validity_line])
            return res
        chosen, clear, how = "cpu", True, "the only device here: nvidia-smi ran and lists no GPU"
    else:
        c, g = best.get("cpu"), best.get("cuda")
        if c and g:
            if g["lower_min"] > top["cpu"]["upper_max"]:
                chosen, clear, how = "cuda", True, (
                    f"its lowest lower bound, {g['lower_min']} ({g['runs']} at once), beats CPU's highest "
                    f"upper bound, {top['cpu']['upper_max']} ({top['cpu']['runs']} at once)")
            elif c["lower_min"] > top["cuda"]["upper_max"]:
                chosen, clear, how = "cpu", True, (
                    f"its lowest lower bound, {c['lower_min']} ({c['runs']} at once), beats CUDA's highest "
                    f"upper bound, {top['cuda']['upper_max']} ({top['cuda']['runs']} at once)")
            else:
                chosen, clear, how = "cpu", False, (
                    f"NO CLEAR WINNER, KEEP CPU: neither device's lowest lower bound beats the other's "
                    f"highest upper bound (CPU {c['lower_min']} against CUDA's {top['cuda']['upper_max']}, "
                    f"CUDA {g['lower_min']} against CPU's {top['cpu']['upper_max']})")
        else:
            chosen = "cpu" if c else "cuda"
            other = "cuda" if c else "cpu"
            clear, how = True, f"the only usable device ({other.upper()}: {why_not[other]})"
    b = pick_runs(usable_by[chosen], window_days)                 # the concurrency, by days
    if b is not best[chosen]:
        how += (f"; {b['runs']} at once, not the fastest {best[chosen]['runs']}, because its waves "
                f"pack the {ARMS} x seeds runs better")
    s = schedule(b["lower_min"], b["runs"], SEEDS_TARGET)
    k = seeds_in_window(b["lower_min"], b["runs"], window_days) if window_days else None
    seeds = k if k is not None else SEEDS_TARGET
    cmd = launcher_command(chosen, b["runs"], seeds, plan) if seeds >= 1 else None
    caution = []
    if not b["steady"]:
        caution.append(f"its rows were not steady (overlap under {STEADY_OVERLAP}): re-run with more --steps")
    if b["loaded"]:
        caution.append(f"a repeat started with the CPU more than {LOAD_LIMIT_PCT:g} % busy")
    if not b["fits_known"]:
        caution.append("its memory at 450 000-step size was not estimated")
    if b.get("vram_unknown"):
        caution.append("its video memory was not measured (nvidia-smi gave no reading), so how many "
                       "runs fit on the GPU at once is not known")
    if chosen == "cpu" and not str(builds.get("cpu", "")).endswith("+cpu"):
        caution.append(f"the CPU rows were measured with torch {builds.get('cpu')}, not "
                       "requirements-lock.txt's CPU build")
    text = ([f"{chosen.upper()} with {b['runs']} runs at once (torch {builds.get(chosen)}): {how}."]
            + lines + _schedule_lines(b, window_days) + _packing_lines(usable_by[chosen], window_days)
            + ([f"  the launcher, for each engine (--engine and --road are what was measured, --out is the "
                "experiment's own; train_all.py trains two arms a seed today, the days count three, "
                f"decision 27):\n    {cmd}"] if cmd else ["  not even one seed per arm fits the window"])
            + [f"  CAUTION: {x}" for x in caution] + [validity_line])
    if smoke:
        text = ["SMOKE TEST (--quick): NOT FOR DECISIONS 30 AND 32, no device is named. The rule "
                "would say:"] + text
    res.update(device=None if smoke else chosen, runs=b["runs"], clear=clear, schedule=s,
               seeds_in_window=k, command=cmd, caution=caution, text="\n".join(text))
    return res


def _fmt(x, nd=1):
    return "-" if x is None else f"{x:.{nd}f}"


def print_table(rows):
    print(f"\n{'device':<7}{'runs':>5}{'rep':>4}{'lower':>9}{'upper':>9}{'overlap':>8}{'wall s':>8}"
          f"{'RAM GB':>8}{'at 450k':>9}{'VRAM/run':>9}{'load%':>6}  ok")
    for r in rows:
        v = r.get("vram") or {}
        twin = r.get("seed0_twice")
        print(f"{r['device']:<7}{r['runs']:>5}{r.get('repeat', 0) + 1:>4}"
              f"{_fmt(r.get('lower_steps_per_s')):>9}{_fmt(r.get('upper_steps_per_s')):>9}"
              f"{_fmt(r.get('overlap'), 2):>8}{_fmt(r.get('wall_s'), 0):>8}"
              f"{_fmt((r.get('ram') or {}).get('used_gb')):>8}{_fmt(r.get('production_gb')):>9}"
              f"{_fmt(v.get('per_run_mib'), 0):>9}{_fmt(r.get('background_cpu_pct'), 0):>6}  "
              + ("yes" if r.get("ok") else "NO: " + "; ".join(r.get("why") or ["?"]))
              + ("" if r.get("steady", True) else ", not steady")
              + (", loaded" if r.get("loaded") else "")
              + (", does not fit at 450 000 steps" if r.get("fits") is False else "")
              + (", VRAM near full" if v.get("near_full") else "")
              + ("" if not twin else ", seed 0 twice " + ("IDENTICAL" if twin.get("identical")
                                                         else "NOT IDENTICAL")))
    print("  lower, upper: steps/s of all the runs together (the docstring); RAM GB: the machine's "
          "available memory, its drop;\n  at 450k: the production estimate; VRAM/run: MiB; load%: "
          "the CPU's load before the batch")


def plan_grid(usable, physical, runs_arg, quick):
    """The concurrencies: --runs as given (sorted, duplicates dropped), else 1, half the physical
    cores, the physical cores and every usable CPU (the review of 21 October 2026: on a hybrid or
    non-SMT processor half the logical CPUs is not the core count, often the CPU's optimum);
    --quick: 1 and every usable CPU. Each device's grid is capped after its single-run row."""
    if runs_arg:
        return sorted(set(runs_arg))
    L = max(1, usable)
    P = max(1, min(physical or L, L))
    return sorted({1, L}) if quick else sorted({1, max(1, P // 2), P, L})


def check_args(a):
    """What is wrong with the command line, or None (the review of 21 October 2026: --runs 0 ran
    nothing and counted as ok, --steps 0 became 3000, and under about 1000 steps SAC makes so few
    updates that the CPU and CUDA rows time almost none). Every run that measures names its engine
    and its road (31 October 2026, rows 114 and 118; mistake 1); --merge takes them from its files."""
    if a.merge is not None:
        if a.engine is not None or a.road is not None:
            return ("--merge takes no --engine or --road: each file names the engine and the road it "
                    "measured (its plan), and two files that differ in either are refused")
    elif a.engine is None:
        return "--engine is required: there is no default engine (CLAUDE.md mistake 1)"
    elif a.road is None:
        return ("--road is required: the road names the design whose training is timed (a default that "
                "selects an experiment is the trap train.py's docstring names)")
    if a.runs is not None and min(a.runs) < 1:
        return "--runs must be 1 or more"
    if a.steps is not None and a.steps < 1000:
        return "--steps must be 1000 or more: SAC makes no update in its first 100 steps"
    if a.repeats is not None and a.repeats < 1:
        return "--repeats must be 1 or more"
    if a.window_days is not None and a.window_days <= 0:
        return "--window-days must be more than 0"
    if a.merge is not None and len(a.merge) > 2:
        return "--merge takes CPU.json CUDA.json (or one file, to apply the rule again)"
    return None


def default_out(host, torch_version, now):
    return f"benchmark_{host}_torch{(torch_version or 'unknown').replace('+', '_')}_{now:%Y%m%d_%H%M%S}.json"


def resolve_out(path):
    """The JSON's absolute path, its folder made, refused if the file exists. Resolved after the
    probe (the default name carries the torch build the probe reports) and before anything is
    trained or timed, so a bad --out fails in seconds rather than after an hour, and a second run
    (the CUDA environment's after the CPU one's) can never overwrite the first."""
    out = os.path.abspath(path)
    if os.path.exists(out):
        sys.exit(f"{out} exists: pass another --out (a benchmark's file is never overwritten)")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    return out


def save(result, out, tries=SAVE_TRIES, wait_s=SAVE_WAIT_S):
    """The JSON, whole, written beside itself and moved into place, so a crash or Ctrl+C
    mid-write leaves the previous version, never half a file. On Windows os.replace is refused
    while another process holds the file open (an editor, a viewer, the indexer: WinError 5,
    reproduced on the team laptop on 21 October 2026), and save() runs outside the rows' error
    handling, so one such refusal would end the benchmark: tried `tries` times, `wait_s` apart,
    then raised."""
    tmp = out + ".tmp"
    for k in range(tries):
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(result, fh, indent=1)
            os.replace(tmp, out)
            return
        except PermissionError:
            if k == tries - 1:
                raise
            time.sleep(wait_s)


# ------------------------------------------------------------------------ --merge
def _torch_base(version):
    return str(version or "").split("+")[0]           # "2.14.0+cu126" -> "2.14.0"


def merge_docs(docs, window_days=None):
    """--merge: the CPU environment's file and the CUDA environment's, one decision: the CPU's
    rows and determinism from the first, the GPU's from the second (the CUDA environment's CPU
    rows are left out: they were not measured with the lock's build). Refused when the two do not
    describe one machine, one measurement and one environment apart from the torch build: the
    Python, the packages check_training_device.CRITICAL names (numpy runs the plant), the torch
    version under the two builds, train.py, and the plant the rows timed. A different power
    plan, commit or version of this script is a caution in the recommendation, not a refusal
    (the review of 21 October 2026). A --no-determinism file is refused as a --quick one is:
    its device would read as failed, and the other would be named by default. One file: the
    rule applied to it again."""
    for d in docs:
        if d.get("status") != "finished":
            sys.exit(f"cannot merge a file whose run did not finish (status {d.get('status')!r})")
        if d["plan"].get("smoke_test"):
            sys.exit("cannot merge a --quick file: a smoke test, not for decisions 30 and 32")
        if d["plan"].get("no_determinism"):
            sys.exit("cannot merge a --no-determinism file: no device is named until seed 0 trains "
                     "the identical agent twice on it (section 4)")
    caution = []
    if len(docs) == 1:
        (a,) = docs
        rows, det = a["concurrency"], a["determinism"]
        measured = set(a["devices"])
        builds = {d: a["machine"]["torch"] for d in measured}
        gpu_present = gpu_presence(a["machine"])
        machines = dict(only=a["machine"])
    else:
        a, b = docs
        ma, mb = a["machine"], b["machine"]
        ca, cb = a.get("code") or {}, b.get("code") or {}
        problems = []
        if ma["host"] != mb["host"]:
            problems.append(f"two machines ({ma['host']}, {mb['host']})")
        for k in ("road", "engine", "dt", "steps_per_run", "det_steps"):
            if a["plan"].get(k) != b["plan"].get(k):
                problems.append(f"{k} {a['plan'].get(k)!r} against {b['plan'].get(k)!r}")
        if ma.get("torch_cuda"):
            problems.append(f"the first file is not the CPU environment's (torch {ma['torch']})")
        if not mb.get("torch_cuda"):
            problems.append(f"the second file is not the CUDA environment's (torch {mb['torch']})")
        if ma.get("python") != mb.get("python"):
            problems.append(f"Python {ma.get('python')} against {mb.get('python')}")
        if _torch_base(ma.get("torch")) != _torch_base(mb.get("torch")):
            problems.append(f"torch {ma.get('torch')} against {mb.get('torch')}: not two builds of "
                            "one version")
        pa, pb = ma.get("packages") or {}, mb.get("packages") or {}
        for k in sorted((set(pa) | set(pb)) - {"torch"}):
            if pa.get(k) != pb.get(k):
                problems.append(f"{k} {pa.get(k)} against {pb.get(k)}")
        if ca.get("train_sha") != cb.get("train_sha"):
            problems.append(f"train.py differs (sha {ca.get('train_sha')} against {cb.get('train_sha')})")
        rows = ([r for r in a["concurrency"] if r["device"] == "cpu"]
                + [r for r in b["concurrency"] if r["device"] == "cuda"])
        plants = sorted({_plant_id(r.get("plant")) for r in rows if r.get("ok")})
        if len(plants) > 1:
            problems.append("the rows timed more than one plant: " + " against ".join(plants))
        if problems:
            sys.exit("cannot merge: " + "; ".join(problems))
        caution = [f"{what} differs between the two files: {x!r} against {y!r}" for what, x, y in (
            ("the power plan", ma.get("power"), mb.get("power")),
            ("the commit", ca.get("git_head"), cb.get("git_head")),
            ("this script (benchmark_sha)", ca.get("benchmark_sha"), cb.get("benchmark_sha")))
            if x != y]
        det = {d: doc["determinism"][d] for d, doc in (("cpu", a), ("cuda", b))
               if d in (doc.get("determinism") or {})}
        measured = {d for d, doc in (("cpu", a), ("cuda", b)) if d in doc["devices"]}
        builds = {"cpu": ma["torch"], "cuda": mb["torch"]}
        gpu_present = True
        machines = dict(cpu=ma, cuda=mb)
    # the engine, road and step the rows timed: one file's, or the two files' (refused above unless
    # they agree)
    rec = recommend(rows, det, measured, gpu_present, builds, window_days, plan=docs[0]["plan"])
    if caution:
        rec["caution"] = list(rec.get("caution") or []) + caution
        rec["text"] += "".join(f"\n  CAUTION: {x}" for x in caution)
    return dict(benchmark="benchmark_training.py --merge", machines=machines, devices=sorted(measured),
                code=[d.get("code") for d in docs], concurrency=rows, determinism=det,
                window_days=window_days, recommendation=rec)


def merge(paths, out_arg, window_days):
    docs = []
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            docs.append(json.load(fh))
    merged = merge_docs(docs, window_days)
    merged["merged_from"] = [os.path.abspath(p) for p in paths]
    host = (docs[0].get("machine") or {}).get("host", "unknown")
    out = resolve_out(out_arg or f"benchmark_{host}_merged_{datetime.now():%Y%m%d_%H%M%S}.json")
    print_table(merged["concurrency"])
    print("\nRECOMMENDATION:", merged["recommendation"]["text"])
    save(merged, out)
    print(f"\nwritten to {out}")


# ---------------------------------------------------------------------- the selftest
def selftest():
    """The harness on dummy work, with no SAC, no plant and no CUDA (seconds): the batch launcher,
    its deadline and its kill, a part's result line, nvidia-smi giving no answer, the run reader
    and the bounds, the device and plant checks, the fingerprint comparison, the grid and the
    input checks (--engine and --road required to measure, refused with --merge), the engine and
    the road in every command, a recorded step's bytes (train imported, nothing built), the memory
    estimate and its caps, the rule and its margins, the days and the window, --merge and its
    refusals, and the output file's refusal to overwrite, its whole-file writes and their retries."""
    global nvidia_smi                                # stubbed below, restored before the end
    import psutil
    import check_training_device as CTD
    root = tempfile.mkdtemp(prefix="bench_selftest_")
    try:
        # the launcher: three at once, an exit code, a deadline that kills
        cmd = [sys.executable, "-c", "import time; time.sleep(0.6)"]
        b = run_batch([cmd, cmd, cmd], root, poll_s=0.1)
        assert b["codes"] == [0, 0, 0], b
        assert 0.6 <= b["wall_s"] < 5.0, f"three 0.6 s sleeps at once took {b['wall_s']} s"
        assert b["ram"]["avail_before_gb"] > 0 and not b["timed_out"], b
        b = run_batch([[sys.executable, "-c", "import sys; sys.exit(3)"]], root, poll_s=0.1)
        assert b["codes"] == [3], b
        # a hung run with a child of its own (as train.py's git calls are), which only a kill of
        # the whole tree reaches: on Windows the venv launcher's job takes its interpreter down
        # with it, but not what that interpreter started, and an orphan is no longer a
        # descendant, so the child records its own child's PID
        pidfile = os.path.join(root, "grandchild.pid")
        hang = ("import subprocess, sys, time; q = subprocess.Popen([sys.executable, '-c', "
                f"'import time; time.sleep(120)']); open({pidfile!r}, 'w').write(str(q.pid)); "
                "time.sleep(120)")
        t = time.perf_counter()
        b = run_batch([[sys.executable, "-c", hang]], root, poll_s=0.1, deadline_s=2.0)
        assert b["timed_out"] and b["codes"][0] != 0 and time.perf_counter() - t < 60, b

        def running(pid):
            try:
                q = psutil.Process(pid)
                return q.is_running() and q.status() != psutil.STATUS_ZOMBIE
            except psutil.Error:
                return False
        with open(pidfile, encoding="utf-8") as fh:
            orphan = int(fh.read())
        for _ in range(50):
            if not running(orphan):
                break
            time.sleep(0.1)
        assert not running(orphan), "the hung run's own child outlived the kill"

        # a part's result (child_result): the last PART_TAG line wins; a child that dies or hangs
        # after its first line still returns it and says how it ended (the probe's CUDA test);
        # one that printed none raises
        def child(*code):
            return [sys.executable, "-c", "; ".join(("import json, os, sys, time",) + code)]

        def emit(x):
            return f"print({PART_TAG!r} + json.dumps({x!r}), flush=True)"
        env = dict(os.environ)
        assert child_result(child(emit(dict(n=1)), emit(dict(n=2))), env, 60, "two") == dict(n=2)
        r = child_result(child(emit(dict(n=1)), "os._exit(3)"), env, 60, "died")
        assert r["n"] == 1 and r["child_exit"].startswith("exited 3"), r
        # a crash mid-print cuts the last line short: the whole line before it is read instead
        half = PART_TAG + '{"n": 2'
        r = child_result(child(emit(dict(n=1)), f"sys.stdout.write({half!r})", "sys.stdout.flush()",
                               "os._exit(3)"), env, 60, "cut")
        assert r["n"] == 1 and r["child_exit"].startswith("exited 3"), r
        t = time.perf_counter()
        r = child_result(child(emit(dict(n=1)), "time.sleep(120)"), env, 2, "hung")
        assert r["n"] == 1 and r["child_exit"].startswith("killed after 2 s"), r
        assert time.perf_counter() - t < 60, "the hung part was not killed at its timeout"
        try:
            child_result(child("sys.exit(1)"), env, 60, "silent")
        except RuntimeError as e:
            assert str(e).startswith("silent exited 1"), e
        else:
            raise AssertionError("a part that printed no result line must raise")

        # nvidia-smi giving no answer is not "no GPU", and a CUDA row then says its video memory
        # was not measured instead of carrying no block at all (the review of 21 October 2026)
        real_smi = nvidia_smi
        try:
            nvidia_smi = lambda *q: None
            assert gpus() is None and gpu_presence(dict(gpus=gpus(), cuda=dict(ok=False))) is None
            b = run_batch([[sys.executable, "-c", "pass"]], root, poll_s=0.1, device="cuda")
            assert b["codes"] == [0] and "unknown" in b["vram"], b
            nvidia_smi = lambda *q: []
            assert gpus() == [] and gpu_presence(dict(gpus=gpus(), cuda=dict(ok=False))) is False
        finally:
            nvidia_smi = real_smi
        assert gpu_presence(dict(gpus=[dict(name="GPU")])) is True
        assert gpu_presence(dict(gpus=None, cuda=dict(ok=True))) is True

        # the runs' config.json files, the bounds and the device check
        out = os.path.join(root, "row")
        for i, (seed, dev, start, finish, rate) in enumerate(((0, "cpu", "12:00:00", "12:05:00", 10.0),
                                                              (1, "cpu", "12:00:30", "12:04:40", 12.0))):
            d = os.path.join(out, f"r{i}", f"sighted_seed{seed}")
            os.makedirs(d)
            with open(os.path.join(d, "config.json"), "w", encoding="utf-8") as fh:
                json.dump(dict(seed=seed, device=dev, status="finished", started=f"2026-10-21T{start}",
                               finished=f"2026-10-21T{finish}", steps_per_s_this_session=rate), fh)
        runs = read_runs(out)
        assert [r["rate"] for r in runs] == [10.0, 12.0], runs
        bd = bounds(runs, 3000)
        # upper 10 + 12; lower 2 x 3000 steps over 0 s .. 300 s + 1 s; overlap (281 - 30) / 276
        assert (bd["upper_steps_per_s"], bd["lower_steps_per_s"]) == (22.0, 19.93), bd
        assert (bd["overlap"], bd["stagger_s"]) == (0.909, 30.0), bd
        clean = dict(codes=[0, 0], timed_out=False)
        assert row_verdict("cpu", 2, clean, runs, 100.0) == []
        assert row_verdict("cuda", 2, clean, runs, 100.0) == ["trained on cpu"], "a CPU fallback must fail a cuda row"
        assert row_verdict("cuda", 1, dict(codes=[0], timed_out=False),
                           [dict(runs[0], device="cuda:0")], 100.0) == []
        bad = row_verdict("cpu", 3, dict(codes=[0, 0, 1], timed_out=True), runs, 100.0)
        assert len(bad) == 3 and bad[0].startswith("timed out"), bad
        moved = [runs[0], dict(runs[1], plant=dict(runs[1]["plant"], plant_sha="another"))]
        assert [w for w in row_verdict("cpu", 2, clean, moved, 100.0) if "more than one plant" in w], \
            "two plants in one row (the code changed mid-batch) must fail it"

        # the fingerprint comparison reads the counters too
        fa = dict(weights={"w": "1"}, record={"r": "2"}, counters={k: 0 for k in CTD.COUNTERS}, curve="c")
        fb = json.loads(json.dumps(fa))
        assert fingerprint_diff(fa, fb) == []
        fb["counters"]["_n_updates"] = 1
        assert fingerprint_diff(fa, fb) == ["counter _n_updates"]

        # the grid, the input checks, the commands
        assert plan_grid(20, 14, None, False) == [1, 7, 14, 20]
        assert plan_grid(8, 16, None, False) == [1, 4, 8]
        assert plan_grid(1, 1, None, True) == [1]
        assert plan_grid(20, 14, [12, 6, 6], False) == [6, 12]
        # every run that measures names its engine and its road (rows 114 and 118; mistake 1), and
        # --merge takes both from its files
        base = dict(runs=None, steps=None, repeats=None, window_days=None, merge=None, engine="b58",
                    road="extremes")
        for wrong in (dict(runs=[0]), dict(runs=[-1, 2]), dict(steps=999), dict(repeats=0),
                      dict(window_days=0.0), dict(merge=["a", "b", "c"], engine=None, road=None),
                      dict(engine=None), dict(road=None), dict(merge=["a", "b"]),
                      dict(merge=["a", "b"], engine=None)):
            assert check_args(argparse.Namespace(**dict(base, **wrong))), wrong
        assert "mistake 1" in check_args(argparse.Namespace(**dict(base, engine=None)))
        assert check_args(argparse.Namespace(**dict(base, runs=[1], steps=1000, repeats=1))) is None
        assert check_args(argparse.Namespace(**dict(base, merge=["a", "b"], engine=None, road=None))) is None
        P58 = dict(engine="b58", road="extremes", dt=DT)      # what this script measured before --engine
        c = train_cmd("cuda", 3, 3000, "OUT", P58, buffer=PROD_BUFFER)
        assert (c[c.index("--dt") + 1], c[c.index("--device") + 1], c[c.index("--buffer") + 1]) == \
            ("1", "cuda", "450000"), c
        assert (c[c.index("--engine") + 1], c[c.index("--road") + 1]) == ("b58", "extremes"), c
        assert "--buffer" not in train_cmd("cpu", 0, DET_STEPS, "OUT", P58), "section 4 keeps the default buffer"
        # another engine and road reach every train.py, the launcher's command and the validity line
        PX = dict(engine="mazda_25t", road="four_engine", dt=DT)
        c = train_cmd("cpu", 0, DET_STEPS, "OUT", PX)
        assert (c[c.index("--engine") + 1], c[c.index("--road") + 1]) == ("mazda_25t", "four_engine"), c
        assert launcher_command("cpu", 14, 20, PX).startswith(
            "python train_all.py --engine mazda_25t --road four_engine --dt 1 --device cpu --jobs 14"), \
            launcher_command("cpu", 14, 20, PX)
        assert validity("b58").startswith("Valid for the cycle backend and the B58 only. ")
        assert validity("mazda_25t").startswith("Valid for the cycle backend and the MAZDA_25T only. ")
        assert 1 <= usable_cpus() <= (os.cpu_count() or 1)

        # the memory at production size, and the cap it sets
        # a recorded step's bytes (an import of train, nothing built): 274, as in X1's records;
        # a float gear gave 270 (the review of 21 October 2026)
        assert record_bytes_per_step((23,), (5,)) == 274, record_bytes_per_step((23,), (5,))
        r1 = dict(runs=1, steps_per_run=3000, ram=dict(used_gb=0.5, avail_before_gb=30.0))
        # 216 B a transition: two observations of 23 float32, 5 actions, three flags (the review)
        part = dict(bytes_per_transition=216, record_bytes_per_step=274)
        want = round(0.5 + ((450_000 - 3000) * 216 + 3 * 450_000 * 274) / 2**30 + RECORDER_LISTS_GB, 2)
        assert production_gb(r1, part) == want == 0.95, (production_gb(r1, part), want)
        assert cap_runs(r1, part) == int((30.0 - RESERVE_GB) / want) == 26
        r1v = dict(r1, vram=dict(per_run_mib=500.0, total_mib=8192.0, near_full=False))
        assert cap_runs(r1v, part) == 14, cap_runs(r1v, part)       # (8 GB - 1 GB) / 0.49 GB
        assert fits(r1, part) and not fits(dict(r1, runs=60), part)      # 0.5 + 60 x 0.45 > 30 - 5
        assert production_gb(r1, {}) is None and fits(r1, {}) is None
        # what the GPU held before the batch counts (the review of 21 October 2026): 8 GiB with
        # 1.5 GiB in use and 500 MiB a run leaves (8192 - 1536 - 1024) / 500 = 11.3 runs
        r1b = dict(r1, vram=dict(before_mib=1536.0, per_run_mib=500.0, total_mib=8192.0, near_full=False))
        assert cap_runs(r1b, part) == 11, cap_runs(r1b, part)

        def on_gpu(n):                # n runs on that GPU; its peak stays under VRAM_FULL up to 12
            pk = 1536.0 + 500.0 * n
            return dict(r1, runs=n, ram=dict(used_gb=0.5, avail_before_gb=60.0),
                        vram=dict(before_mib=1536.0, peak_mib=pk, per_run_mib=500.0, total_mib=8192.0,
                                  near_full=pk >= VRAM_FULL * 8192.0))
        assert fits(on_gpu(11), part) and not fits(on_gpu(12), part)    # 7036, 7536 MiB of 8192 - 1024
        unmeasured = dict(r1, vram=dict(unknown="nvidia-smi gave no answer"))
        assert fits(unmeasured, part) is None and fits(dict(unmeasured, runs=60), part) is False
        assert cap_runs(unmeasured, part) == 26, "unmeasured video memory caps nothing"

        # the rule: a device is named only when its lowest lower bound beats the other's highest upper
        def row(d, n, lo, up, rep=0, **kw):
            return dict(dict(device=d, runs=n, repeat=rep, ok=True, fits=True, steady=True,
                             lower_steps_per_s=lo, upper_steps_per_s=up), **kw)
        same = dict(seed0_twice=dict(identical=True))
        rows = [row("cpu", 2, 100.0, 110.0), row("cpu", 2, 104.0, 112.0, 1),
                row("cuda", 2, 105.0, 118.0, **same), row("cuda", 2, 108.0, 120.0, 1, **same)]
        fast = rows[:2] + [row("cuda", 2, 130.0, 140.0, **same), row("cuda", 2, 131.0, 141.0, 1, **same)]
        det = {"cpu": dict(identical=True), "cuda": dict(identical=True)}
        both = {"cpu", "cuda"}
        builds = {"cpu": "2.14.0+cpu", "cuda": "2.14.0+cu126"}
        r = recommend(rows, det, both, True, builds, plan=P58)
        assert (r["device"], r["clear"]) == ("cpu", False), r["text"]          # 105 does not beat 112
        assert "NO CLEAR WINNER" in r["text"], r["text"]
        r = recommend(fast, det, both, True, builds, plan=P58)
        assert (r["device"], r["clear"], r["runs"]) == ("cuda", True, 2), r["text"]
        # the spread of the repeats counts: CUDA's 120 beats one CPU repeat's upper bound (110) but
        # not the other's (125), so there is no clear winner
        spread = [row("cpu", 2, 100.0, 110.0), row("cpu", 2, 104.0, 125.0, 1),
                  row("cuda", 2, 120.0, 130.0, **same), row("cuda", 2, 121.0, 131.0, 1, **same)]
        assert recommend(spread, det, both, True, builds, plan=P58)["clear"] is False
        assert "--device cuda --jobs 2 --seeds 0-19" in r["command"], r["command"]
        # the other side is the other device's highest upper bound at ANY usable concurrency:
        # CUDA's 115 beats CPU x14's 110 but not CPU x20's 130 (the review of 21 October 2026)
        peak = [row("cpu", 14, 100.0, 110.0), row("cpu", 14, 101.0, 109.0, 1),
                row("cpu", 20, 95.0, 130.0), row("cpu", 20, 96.0, 128.0, 1),
                row("cuda", 14, 115.0, 120.0, **same), row("cuda", 14, 116.0, 121.0, 1, **same)]
        r = recommend(peak, det, both, True, builds, plan=P58)
        assert (r["device"], r["clear"]) == ("cpu", False) and "130.0" in r["text"], r["text"]
        assert (r["best"]["cpu"]["runs"], r["best"]["cpu"]["highest_upper"]) == (14, 130.0), r["best"]
        # and the mirror: CPU's 115 beats CUDA x7's 110 but not CUDA x14's 130, so CPU is kept,
        # not named clear
        mirror = [row("cuda", 7, 100.0, 110.0, **same), row("cuda", 7, 101.0, 109.0, 1, **same),
                  row("cuda", 14, 95.0, 130.0, **same), row("cuda", 14, 96.0, 128.0, 1, **same),
                  row("cpu", 14, 115.0, 120.0), row("cpu", 14, 116.0, 121.0, 1)]
        r = recommend(mirror, det, both, True, builds, plan=P58)
        assert (r["device"], r["clear"]) == ("cpu", False) and "130.0" in r["text"], r["text"]
        assert recommend(fast, dict(det, cuda=dict(identical=False)), both, True, builds,
                         plan=P58)["device"] == "cpu", "a device that is not deterministic must never be chosen"
        # unchecked is not failed: a pair that timed out, or a device missing from the verdicts,
        # names no device, where a pair that differed hands the other device the win
        for unchecked in (dict(det, cpu=dict(identical=None, why="timed out")), {"cuda": det["cuda"]}):
            r = recommend(fast, unchecked, both, True, builds, plan=P58)
            assert r["device"] is None and "not known" in r["text"], r["text"]
        r = recommend(fast, dict(det, cpu=dict(identical=False, first=["weights x"])), both, True, builds,
                      plan=P58)
        assert r["device"] == "cuda" and "the only usable device (CPU:" in r["text"], r["text"]
        # a concurrency measured in fewer repeats than planned is not clean: x7 failed in repeat 2,
        # which then skipped x14, so x14 has one clean repeat of two (the review of 21 October 2026)
        skipped = [row("cpu", 1, 14.0, 14.5, repeats_planned=2), row("cpu", 7, 60.0, 64.0, repeats_planned=2),
                   row("cpu", 14, 100.0, 104.0, repeats_planned=2),
                   row("cpu", 1, 14.1, 14.4, 1, repeats_planned=2),
                   row("cpu", 7, 0.0, 0.0, 1, ok=False, repeats_planned=2)]
        assert [c["ok"] for c in configurations(skipped)] == [True, False, False]
        assert recommend(skipped, {"cpu": det["cpu"]}, {"cpu"}, False, builds, plan=P58)["runs"] == 1
        differ = rows[:2] + [row("cuda", 2, 130.0, 140.0, seed0_twice=dict(identical=False))]
        assert recommend(differ, det, both, True, builds, plan=P58)["device"] == "cpu", \
            "seed 0 twice under contention"
        cpu_only = {"cpu": det["cpu"]}
        assert recommend(rows[:2], cpu_only, {"cpu"}, True, builds, plan=P58)["device"] is None, \
            "a GPU here, unmeasured"
        assert recommend(rows[:2], cpu_only, {"cpu"}, False, builds, plan=P58)["device"] == "cpu", "no GPU at all"
        r = recommend(rows[:2], cpu_only, {"cpu"}, None, builds, plan=P58)
        assert r["device"] is None and "nvidia-smi gave no answer" in r["text"], "not knowing is not 'no GPU'"
        assert recommend(rows, {}, both, True, builds, plan=P58)["device"] is None
        assert recommend([], {}, set(), True, builds, plan=P58)["text"] == "no device was measured"
        too_big = [dict(x, fits=False) for x in rows[:2]] + fast[2:]
        assert recommend(too_big, det, both, True, builds, plan=P58)["device"] == "cuda", "a row that does not fit"
        one_failed = [rows[0], dict(rows[1], ok=False)] + fast[2:]
        assert recommend(one_failed, det, both, True, builds, plan=P58)["device"] == "cuda", "a repeat that failed"
        assert recommend(fast, det, both, True, builds, smoke=True, plan=P58)["device"] is None, "--quick names none"
        r = recommend(fast, det, both, True, dict(builds, cpu="2.14.0+cu126"), plan=P58)
        assert r["device"] == "cuda"
        r = recommend(rows, det, both, True, dict(builds, cpu="2.14.0+cu126"), plan=P58)
        assert any("not requirements-lock.txt's" in x for x in r["caution"]), r["caution"]

        # the days and the window: lower 100 at 20 runs is 5 steps/s a run, 1.04 days a run,
        # 3 waves of 20 for 60 runs, x 4 engines
        s = schedule(100.0, 20, 20)
        assert (s["waves_per_engine"], s["idle_slots_last_wave"], s["days"]) == (3, 0, 12.5), s
        assert seeds_in_window(100.0, 20, 12.5) == 20
        assert seeds_in_window(100.0, 20, 12.4) == 13         # 13 seeds: 39 runs, 2 waves; 14: 42 runs, 3 waves, 12.5 days
        assert seeds_in_window(100.0, 20, 1.0) == 0
        # 130 steps/s at 2 runs: one seed is 3 runs, 2 waves, x 4 engines, 0.64 days
        assert recommend(fast, det, both, True, builds, window_days=0.1, plan=P58)["command"] is None
        # the concurrency is picked by days: 16 at once is the faster (100 against 97 steps/s),
        # but 60 runs take 4 waves either way, so 15 at once finishes first (12.9 days, not 13.3)
        pack = [row("cpu", 16, 100.0, 105.0), row("cpu", 15, 97.0, 101.0)]
        r = recommend(pack, cpu_only, {"cpu"}, False, builds, plan=P58)
        assert (r["device"], r["runs"]) == ("cpu", 15), r["text"]
        r = recommend(pack, cpu_only, {"cpu"}, False, builds, window_days=13.0, plan=P58)
        assert (r["runs"], r["seeds_in_window"]) == (15, 20), r["text"]       # 16 at once fits 16 seeds

        # --merge: the CPU from the first file, the GPU from the second (dummy versions and hashes)
        def doc(devs, rows_, det_, torch="2.14.0+cpu", torch_cuda=None, host="dev1", machine=None,
                code=None, **plan):
            return dict(status="finished", devices=devs, concurrency=rows_, determinism=det_,
                        machine=dict(dict(host=host, torch=torch, torch_cuda=torch_cuda, gpus=[dict(name="GPU")],
                                          python="P1", packages=dict(numpy="N1", torch="T"), power="plan A"),
                                     **(machine or {})),
                        plan=dict(dict(road="extremes", engine="b58", dt=DT, steps_per_run=3000,
                                       det_steps=DET_STEPS, smoke_test=False), **plan),
                        code=dict(dict(benchmark_sha="x", train_sha="t1", git_head="h1"), **(code or {})))
        cuda_env = dict(torch="2.14.0+cu126", torch_cuda="12.6")
        cpu_doc = doc(["cpu"], rows[:2], cpu_only)
        cuda_doc = doc(["cpu", "cuda"], [row("cpu", 2, 1.0, 2.0)] + fast[2:], det,
                       machine=dict(packages=dict(numpy="N1", torch="T+cu")), **cuda_env)
        merged = merge_docs([cpu_doc, cuda_doc])
        assert [x["lower_steps_per_s"] for x in merged["concurrency"] if x["device"] == "cpu"] == [100.0, 104.0], \
            "the CUDA environment's CPU rows must be left out"
        assert merged["recommendation"]["device"] == "cuda", merged["recommendation"]["text"]
        assert not merged["recommendation"]["caution"], merged["recommendation"]["caution"]
        assert "--engine b58 --road extremes" in merged["recommendation"]["command"], merged["recommendation"]
        # the engine and the road come from the files: two Mazda files give the Mazda's command and line
        mz = merge_docs([doc(["cpu"], rows[:2], cpu_only, engine="mazda_25t", road="four_engine"),
                         doc(["cpu", "cuda"], [row("cpu", 2, 1.0, 2.0)] + fast[2:], det, engine="mazda_25t",
                             road="four_engine", machine=dict(packages=dict(numpy="N1", torch="T+cu")), **cuda_env)])
        assert "--engine mazda_25t --road four_engine" in mz["recommendation"]["command"], mz["recommendation"]
        assert mz["recommendation"]["text"].endswith(validity("mazda_25t")), mz["recommendation"]["text"]
        for wrong in ([cuda_doc, cpu_doc], [cpu_doc, dict(cuda_doc, machine=dict(cuda_doc["machine"], host="dev2"))],
                      # two engines, or two roads, are two measurements
                      [cpu_doc, doc(["cuda"], fast[2:], det, engine="mazda_25t", **cuda_env)],
                      [cpu_doc, doc(["cuda"], fast[2:], det, road="four_engine", **cuda_env)],
                      [cpu_doc, doc(["cuda"], fast[2:], det, torch_cuda="12.6", steps_per_run=1500)],
                      [cpu_doc, dict(cuda_doc, status="interrupted (Ctrl+C)")],
                      [doc(["cpu"], rows[:2], cpu_only, smoke_test=True), cuda_doc],
                      # an unchecked device would read as failed (the review of 21 October 2026)
                      [doc(["cpu"], rows[:2], {}, no_determinism=True), cuda_doc],
                      # one environment apart from the torch build, timing one plant
                      [cpu_doc, doc(["cuda"], fast[2:], det, machine=dict(python="P2"), **cuda_env)],
                      [cpu_doc, doc(["cuda"], fast[2:], det, machine=dict(packages=dict(numpy="N2")), **cuda_env)],
                      [cpu_doc, doc(["cuda"], fast[2:], det, torch="2.15.0+cu126", torch_cuda="12.6")],
                      [cpu_doc, doc(["cuda"], fast[2:], det, code=dict(train_sha="t2"), **cuda_env)],
                      [cpu_doc, doc(["cuda"], [dict(x, plant=dict(plant_sha="p2")) for x in fast[2:]], det,
                                    **cuda_env)]):
            try:
                merge_docs(wrong)
            except SystemExit:
                continue
            raise AssertionError("a merge of two files that are not one measurement must be refused")
        warned = merge_docs([cpu_doc, doc(["cuda"], fast[2:], det, machine=dict(power="plan B"),
                                          code=dict(git_head="h2", benchmark_sha="y"), **cuda_env)])
        rc = warned["recommendation"]
        assert rc["device"] == "cuda" and len([x for x in rc["caution"] if "differs between" in x]) == 3, rc["caution"]
        assert rc["text"].count("CAUTION: ") == 3, rc["text"]
        assert merge_docs([cpu_doc])["recommendation"]["device"] is None      # one environment, a GPU here
        assert merge_docs([doc(["cpu"], rows[:2], cpu_only, machine=dict(gpus=None))])["recommendation"]["device"] \
            is None, "nvidia-smi's silence is not 'no GPU'"
        assert merge_docs([doc(["cpu"], rows[:2], cpu_only, machine=dict(gpus=[]))])["recommendation"]["device"] \
            == "cpu", "nvidia-smi ran and lists no GPU"

        # the output file: never overwritten, written whole
        existing = os.path.join(root, "exists.json")
        open(existing, "w").close()
        try:
            resolve_out(existing)
        except SystemExit:
            pass
        else:
            raise AssertionError("an existing file must never be overwritten")
        new = resolve_out(os.path.join(root, "made", "for", "it.json"))
        assert os.path.isdir(os.path.dirname(new)) and not os.path.exists(new)
        save(dict(a=1), new)
        save(dict(a=2), new)
        with open(new, encoding="utf-8") as fh:
            assert json.load(fh) == dict(a=2) and not os.path.exists(new + ".tmp")
        # on Windows os.replace is refused while another process holds the file open: retried,
        # then raised once the tries are spent
        real_replace, calls = os.replace, []

        def held_twice(src, dst):
            calls.append(dst)
            if len(calls) <= 2:
                raise PermissionError(13, "held open by another process", dst)
            real_replace(src, dst)
        os.replace = held_twice
        try:
            save(dict(a=3), new, wait_s=0.01)
            assert len(calls) == 3, calls
            calls.clear()
            try:
                save(dict(a=4), new, tries=2, wait_s=0.01)
            except PermissionError:
                pass
            else:
                raise AssertionError("save() must raise once its tries are spent")
        finally:
            os.replace = real_replace
        with open(new, encoding="utf-8") as fh:
            assert json.load(fh) == dict(a=3)
        assert default_out("dev1", "2.14.0+cpu", datetime(2026, 10, 21, 9, 5, 7)) == \
            "benchmark_dev1_torch2.14.0_cpu_20261021_090507.json"
        print(f"SELFTEST PASSES (three runs at once, an exit code, a hung run killed by its deadline "
              f"with its child, a part's result line kept when its child dies, hangs or cuts its "
              f"last line short, nvidia-smi's silence not read as no GPU, the bounds, a CPU fallback "
              f"and a second plant refused, the counters compared, the grid and the input checks, the "
              f"engine and the road in every command, a "
              f"recorded step's bytes, the production memory and its caps, the rule's margins "
              f"against the other device's peak, unchecked determinism and "
              f"skipped repeats, the days and the window, --merge and its refusals and cautions, the "
              f"output file and its retries)")
    finally:
        stray = psutil.Process().children(recursive=True)         # nothing outlives a failed test
        try:
            with open(os.path.join(root, "grandchild.pid"), encoding="utf-8") as fh:
                q = psutil.Process(int(fh.read()))
            if "time.sleep(120)" in " ".join(q.cmdline()):          # never a reused PID's process
                stray.append(q)
        except (OSError, ValueError, psutil.Error):
            pass
        for ch in stray:
            try:
                ch.kill()
            except psutil.Error:
                pass
        shutil.rmtree(root, ignore_errors=True)


# -------------------------------------------------------------------------- main
def main():
    import engines                                   # numpy and the specs only: no torch in this process
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    # engines.trainable(), not known(), as train.py (decision 47): an engine that may not train is
    # refused here, before anything runs. REQUIRED for every run that measures (check_args)
    ap.add_argument("--engine", choices=engines.trainable(),
                    help="the plant to time (engines.get), one that may train (engines.trainable()). "
                         "Required to measure: there is no default engine (CLAUDE.md mistake 1)")
    ap.add_argument("--road", help="the training road to time, a road train.DESIGN_DT holds whose design "
                                   "step is DT (the probe checks both). Required to measure")
    ap.add_argument("--device", nargs="+", choices=("cpu", "cuda"),
                    help="the devices to measure (default: cpu in a CPU build of torch, cuda in a "
                         "CUDA build: the docstring's two environments)")
    ap.add_argument("--runs", nargs="+", type=int, help="concurrencies (default: 1, half the physical "
                    "cores, the physical cores and every usable CPU; --quick: 1 and every usable CPU)")
    ap.add_argument("--steps", type=int, help="steps per run in section 3 (default 3000; --quick 1500; "
                    "at least 1000)")
    ap.add_argument("--repeats", type=int, help=f"times each concurrency is measured, interleaved "
                    f"(default {REPEATS}; --quick 1)")
    ap.add_argument("--window-days", type=float, help="the training window in days: the most seeds "
                    "per arm that fit it are reported (decision 30)")
    ap.add_argument("--quick", action="store_true", help="a smoke test of the harness: its numbers "
                    "are not for decisions 30 and 32, and no device is named")
    ap.add_argument("--no-determinism", action="store_true",
                    help="skip section 4 (not advised: then no device is named)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--merge", nargs="+", metavar="JSON",
                    help="CPU.json CUDA.json: the two environments' files, one decision")
    ap.add_argument("--out", help="the JSON file (default benchmark_<host>_torch<build>_<date>_<time>"
                    ".json; never overwritten)")
    ap.add_argument("--part", choices=("probe", "plant", "sac"), help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.part:
        res = (part_probe(a.road) if a.part == "probe" else part_plant(a.engine, a.road) if a.part == "plant"
               else part_sac(a.device[0], a.engine, a.road))
        print(PART_TAG + json.dumps(res), flush=True)
        return
    if a.selftest:
        selftest()
        return
    err = check_args(a)
    if err:
        ap.error(err)
    if a.merge:
        merge(a.merge, a.out, a.window_days)
        return

    # what is measured, the JSON's "plan" block (its engine, road and step travel to every command)
    plan = dict(road=a.road, engine=a.engine, dt=DT)
    try:
        probe = run_part("probe", plan, "cuda", timeout_s=600)
    except RuntimeError as e:
        sys.exit(f"the probe printed no result: torch, train.py or engines.py does not import here, "
                 f"or the probe could not be stopped ({e})")
    if probe.get("child_exit"):                     # it died or hung after its first line: in the CUDA test
        if not (probe.get("cuda") or {}).get("ok"):
            probe["cuda"]["why"] += f" ({probe['child_exit']})"
    if probe["design_dt"] is None:
        sys.exit(f"train.py has no road {a.road!r}: train.DESIGN_DT holds {', '.join(probe['roads_known'])}")
    if probe["design_dt"] != DT:
        sys.exit(f"train.DESIGN_DT[{a.road!r}] is {probe['design_dt']} and this benchmark passes "
                 f"--dt {DT:g}: change DT here, and say why, before measuring")
    m = machine(probe)
    asked = a.device or (["cuda"] if m["torch_cuda"] else ["cpu"])
    devices, notes = devices_available(asked, m)
    if probe.get("child_exit") and (probe.get("cuda") or {}).get("ok"):
        notes.append(f"the probe ended badly after its CUDA test passed: {probe['child_exit']}")
    runs = plan_grid(m["usable_cpus"], m["physical_cpus"], a.runs, a.quick)
    steps = a.steps if a.steps is not None else (1500 if a.quick else 3000)
    repeats = a.repeats if a.repeats is not None else (1 if a.quick else REPEATS)
    physical = max(1, min(m["physical_cpus"] or m["usable_cpus"], m["usable_cpus"]))
    # the whole plan, in the key order the JSON has always had (road, engine, dt first)
    plan.update(steps_per_run=steps, det_steps=DET_STEPS, runs_grid=runs, repeats=repeats, buffer=PROD_BUFFER,
                smoke_test=a.quick, window_days=a.window_days, no_determinism=a.no_determinism)
    now = datetime.now()
    out_path = a.out or default_out(m["host"], m["torch"], now)
    print("THE MACHINE")
    for k, v in m.items():
        print(f"  {k:<14} {v}")
    for n in notes:
        print("  NOTE:", n)
    if not devices:
        sys.exit("no requested device is usable here: " + "; ".join(notes))
    print(f"\nPLAN: devices {devices}; first seed 0 twice per device ({DET_STEPS} steps each); then "
          f"concurrencies {runs} (each device's capped after its single-run row by what fits at "
          f"{PROD_STEPS:,} steps), {steps} steps per run with --buffer {PROD_BUFFER}, {repeats} "
          f"repeat(s) interleaved; the {a.road} roads, the {a.engine.upper()}, one thread per run"
          + ("\n  --quick: A SMOKE TEST, its numbers are not for decisions 30 and 32" if a.quick else ""))
    if a.dry_run:
        for d in devices:
            print(f"  section 4, {d} (twice, one at a time):",
                  " ".join(train_cmd(d, 0, DET_STEPS, f"<tmp>/det_{d}", plan)))
            for n in runs:
                seeds = [0, 0] + list(range(1, n - 1)) if d == "cuda" and n >= 2 else list(range(n))
                print(f"  section 3, {d} x{n}: "
                      + " ".join(train_cmd(d, seeds[0], steps, f"<tmp>/{d}_{n}/r0", plan, buffer=PROD_BUFFER))
                      + (f" (seeds {seeds})" if n > 1 else ""))
        print(f"  the JSON: {os.path.abspath(out_path)}"
              + ("  -- EXISTS: a real run would refuse it" if os.path.exists(out_path) else ""))
        print("dry run: only the probe ran, in a child process; nothing was trained or timed")
        return

    out = resolve_out(out_path)
    result = dict(benchmark="benchmark_training.py", asked_by="Ghassan, 21 October 2026", status="running",
                  date=now.isoformat(timespec="seconds"), code=code_info(), machine=m,
                  devices_asked=asked, devices=list(devices), notes=notes, plan=plan,
                  parts={}, determinism={}, concurrency=[], recommendation=None)
    save(result, out)
    print(f"  the JSON: {out} (written after every section)")
    root = tempfile.mkdtemp(prefix="bench_train_")
    try:
        print("\n2. THE PARTS OF ONE STEP (each in a child process, one thread)")
        parts = result["parts"]
        try:
            parts["plant"] = run_part("plant", plan)
        except Exception as e:
            parts["plant"] = dict(error=repr(e))
            result["status"] = "failed: the plant step"
            save(result, out)
            sys.exit(f"the plant step failed, and every train.py would fail with it: {e}")
        plant_s = parts["plant"]["plant_s"]
        print(f"  plant step (CPU, numpy, backend {parts['plant']['backend']})   {1000 * plant_s:.2f} ms")
        for d in list(devices):
            try:
                parts[d] = run_part("sac", plan, d)
            except Exception as e:
                parts[d] = dict(error=repr(e))
                devices.remove(d)
                notes.append(f"{d} dropped: section 2 failed ({e})")
                print(f"  {d}: FAILED, not measured further: {e}")
                continue
            p = parts[d]
            step = plant_s + p["update_s"] + p["predict_s"]
            fast_plant = [plant_s / k for k in (8, 6)]
            share_table = [100 * x / (x + p["update_s"] + p["predict_s"]) for x in fast_plant]
            print(f"  on {d}: SAC update {1000 * p['update_s']:.2f} ms, choosing an action "
                  f"{1000 * p['predict_s']:.2f} ms -> the plant is {100 * plant_s / step:.0f} % of a step")
            print(f"     on the table backend (arithmetic, not a measurement: a plant 6-8x cheaper, "
                  f"decision 28) it would be {share_table[0]:.0f}-{share_table[1]:.0f} %")
        result["devices"] = list(devices)
        print("  Section 3 is the measurement; these say why it comes out as it does.")
        save(result, out)
        if not devices:
            result["status"] = "failed: no device passed section 2"
            save(result, out)
            sys.exit("no device passed section 2: " + "; ".join(notes))

        timed = list(devices)
        if not a.no_determinism:
            print(f"\n4. DETERMINISM, BEFORE SECTION 3 (seed 0 twice, {DET_STEPS} steps each; every "
                  "tensor, counter, recorded step and the curve compared)")
            for d in devices:
                try:
                    v = determinism(d, root, batch_deadline(parts[d], plant_s, 1, DET_STEPS, physical), plan)
                except Exception as e:
                    v = dict(device=d, identical=None, why=f"error: {e!r}")
                result["determinism"][d] = v
                save(result, out)
                verdict = {True: "IDENTICAL", False: "NOT IDENTICAL"}.get(v["identical"], "NOT CHECKED")
                print(f"  {d}: {verdict} {v.get('first') or v.get('why') or ''}")
                if v["identical"] is not True:
                    timed.remove(d)
                    notes.append(f"{d}: not timed in section 3, it did not train the identical agent twice")
                    print(f"     {d} cannot be used (decision 32): it is not timed in section 3")

        print(f"\n3. TRAINING AS train_all.py RUNS IT (N copies of train.py at once, {repeats} repeat(s))")
        grid = {d: list(runs) for d in timed}
        failed_at = {}
        for rep in range(repeats):
            last = 0
            while True:
                pending = sorted({n for d in timed for n in grid[d]
                                  if last < n < failed_at.get(d, math.inf)})
                if not pending:
                    break
                n = last = pending[0]
                for d in timed:
                    if n not in grid[d] or n >= failed_at.get(d, math.inf):
                        continue
                    print(f"  repeat {rep + 1}, {d} x{n} ...", flush=True)
                    dl = batch_deadline(parts[d], plant_s, n, steps, physical)
                    try:
                        row = benchmark_concurrency(d, n, steps, root, dl, plan)
                    except Exception as e:
                        row = dict(device=d, runs=n, steps_per_run=steps, ok=False, why=[f"error: {e!r}"])
                    row["repeat"] = rep
                    row["repeats_planned"] = repeats     # a concurrency skipped in a repeat is not clean
                    row["production_gb"] = production_gb(row, parts[d])
                    row["fits"] = fits(row, parts[d])
                    result["concurrency"].append(row)
                    save(result, out)
                    print(f"     lower {_fmt(row.get('lower_steps_per_s'))}, upper "
                          f"{_fmt(row.get('upper_steps_per_s'))} steps/s in all, overlap "
                          f"{_fmt(row.get('overlap'), 2)}, RAM {_fmt((row.get('ram') or {}).get('used_gb'))} GB "
                          f"({_fmt(row['production_gb'])} GB at {PROD_STEPS:,} steps), ok {row['ok']}"
                          + ("" if row["ok"] else ": " + "; ".join(row["why"])), flush=True)
                    if not row["ok"]:
                        failed_at[d] = n
                        print(f"     a run failed; higher concurrencies on {d} are skipped")
                    elif rep == 0 and n == 1:
                        cap = cap_runs(row, parts[d])
                        if (row.get("vram") or {}).get("unknown"):
                            print(f"     {d}: {row['vram']['unknown']}; its concurrencies are capped by "
                                  "RAM only")
                        if cap is not None and cap < max(grid[d]):
                            grid[d] = sorted({min(x, cap) for x in grid[d]})
                            print(f"     {d}: at most {cap} runs fit at {PROD_STEPS:,}-step size; "
                                  f"its concurrencies are now {grid[d]}")
        result["status"] = "finished"
    except KeyboardInterrupt:
        result["status"] = "interrupted (Ctrl+C)"
        save(result, out)
        sys.exit(f"\ninterrupted: the children were stopped; what was measured is in {out}")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print_table(result["concurrency"])
    rec = recommend(result["concurrency"], {} if a.no_determinism else result["determinism"],
                    set(result["devices"]), gpu_presence(m), {d: m["torch"] for d in result["devices"]},
                    a.window_days, smoke=a.quick, plan=plan)
    result["recommendation"] = rec
    save(result, out)
    print("\nRECOMMENDATION:", rec["text"])
    print("  The device type is chosen ONCE, for every seed, arm and engine, and goes into the "
          "preregistration (decision 32). CPU and CUDA train different agents.")
    print(f"\nwritten to {out}")


if __name__ == "__main__":
    main()

"""run_phase_d.py — launch Phase D's sixteen training runs in parallel.

    python run_phase_d.py              seeds 0-7, both arms, 50 000 steps
    python run_phase_d.py --seeds 0 1  a subset
    python run_phase_d.py --dry-run    print the commands and stop

WHY IN PARALLEL, AND WHY THAT IS NOT A SHORTCUT
------------------------------------------------
`train.py`'s docstring measures 19.19 steps/s at one thread against 18.14 at
six: the policy network is tiny and the combustion model is the whole cost, so
THREADS DO NOT HELP A SINGLE RUN. It concludes "one evening on one machine, or
under an hour if the five of you run one seed each" -- and stops there, because
it is thinking about threads inside one process.

Sixteen SEPARATE single-threaded processes on a twelve-core machine is a
different arrangement, and it turns 11 hours of sequential work into about one.
Each child gets OMP_NUM_THREADS=1 so no run tries to grab cores from its
neighbours, which is what makes the arrangement hold.

Nothing about the experiment changes: each run is the same `train.py`
invocation with the same seed it would have had, writing the same
`runs/<tag>/meta.json`. Parallelism is a property of the machine, not of the
method, and it is recorded here so nobody has to wonder later whether the runs
were somehow shared.

READ results/PREREGISTRATION.md BEFORE RUNNING THIS. It was committed before
any of these runs started, which is the only thing that makes them evidence.

C4, AND THE THREE THINGS THIS FILE WILL NO LONGER DO   (23 September 2026)
--------------------------------------------------------------------------
    python run_phase_d.py --road random --steps 300000 --out runs_c4 --dry-run

Preparing C4 -- Phase D2's design at 300 000 steps -- found that this launcher
could destroy the two experiments before it, and that nothing would have said
so until afterwards:

  1. IT RELAUNCHED INTO DIRECTORIES THAT HOLD TRAINED AGENTS. Without
     `--skip-done`, a directory holding `final.zip` got `train.py` again, and
     `train.py` resumed it (`train.py`, "A RESUME IS NOT A LONGER RUN"). Now a
     directory with `final.zip` is ALWAYS skipped and named, and one that was
     started and not finished is skipped too. It is re-run only with
     `--seeds <k> --restart-crashed`, which moves it aside into
     `<out>/_crashed/` and trains that seed from scratch -- C4's crash rule --
     and only if no process is training it (`train.py` holds a `RUNNING` mark
     while it trains) and nothing in it has changed for 30 minutes. The first
     version of this fix could not tell a live run from a crashed one, and
     would have moved live runs; the review of the fixes caught it.
  2. IT TRUNCATED THE TRAINING LOGS AT LAUNCH. `<logs>/<tag>.log` was opened
     in "w" mode, so the old log was gone the moment a run started -- even one
     killed a second later. Logs are appended to now, under a dated banner.
  3. IT WROTE EVERY EVALUATION OF A RANDOM ROAD INTO results/d2_seed<N>.txt.
     The prefix was hard-coded, so scoring C4's agents would have overwritten
     D2's committed results. The prefix now follows `--out` (runs -> phase_d,
     runs_d2 -> d2, runs_c4 -> c4), an existing result file is never
     overwritten, and a non-default prefix is passed to `evaluate.py` as the
     report's title so the file says which experiment it belongs to.

And what it now DOES:

  * it refuses to launch from a dirty tree without `--allow-dirty`, and
    re-checks before EVERY start, holding the queue while the tree is dirty --
    a second wave starts hours after the first, and each run records
    `git_dirty` from its own start. A preregistration that pins a commit
    means the commit, not the commit plus whatever was being edited;
  * it refuses any new work in a CLOSED experiment -- `runs/`, `runs_d2/`, and
    the `phase_d` / `d2` result prefixes -- because a new seed there would be
    globbed into a pinned analysis as if it had always belonged;
  * it refuses when the directory's agents were trained for a different
    budget than `--steps` (the wrong-`--out` case) instead of skipping all
    sixteen and reporting success;
  * it passes `--no-resume` to every run of a new experiment, so `train.py`
    itself refuses to resume one;
  * every launch appends a line to `<out>/LAUNCH.txt`.
"""
import argparse
import os
import shutil
import subprocess
import sys
import time

import fingerprint as FP

HERE = os.path.dirname(os.path.abspath(__file__))

# Which analysis script reads which result prefix. Printed as the "next:" hint.
ANALYSIS = {"phase_d": "analyse_phase_d.py", "d2": "analyse_phase_d2.py",
            "c4": "analyse_c4.py"}
PREREG = {"phase_d": "PREREGISTRATION.md", "d2": "PREREGISTRATION_D2.md",
          "c4": "PREREGISTRATION_C4.md"}


def result_prefix(out):
    """The `results/<prefix>_seed<N>.txt` prefix an --out directory scores into.

    runs -> phase_d and runs_d2 -> d2 reproduce the two prefixes this file
    always used; every other directory gets its own (runs_c4 -> c4), so an
    evaluation can only land on another experiment's results if someone TYPES
    that experiment's prefix.
    """
    base = os.path.basename(os.path.normpath(out))
    if base == "runs":
        return "phase_d"
    return base[len("runs_"):] if base.startswith("runs_") else base


# Experiments whose preregistrations say "sixteen runs, then stop" -- the same
# set train.py refuses to add to. Their directories and result prefixes take no
# new work: a new seed there would be globbed into a pinned analysis.
CLOSED_OUT = {"runs": "Phase D", "runs_d2": "Phase D2"}
CLOSED_PREFIX = {"phase_d": "Phase D", "d2": "Phase D2"}

# A crashed run is moved aside only if nothing in it has changed for this long.
# A live C4 run writes a checkpoint every 10 000 steps -- about 9-15 minutes --
# and its log more often. Belt and braces behind the RUNNING mark.
QUIET_MIN = 30


def run_state(d):
    """What a run directory holds.

      running   a live process is training it (fingerprint.running_pid)
      trained   final.zip, readable
      corrupt   final.zip that is not a readable stable-baselines3 zip
      partial   started -- meta.json or a checkpoint -- and not finished, with
                no live process: a crash
      fresh     nothing there

    A run that is still training and a run that crashed look the same on disk.
    Until 23 September 2026 this function could not tell them apart, and the
    crash rule moved live runs (the review of the C4 trap fixes found it).
    """
    if FP.running_pid(d):
        return "running"
    final = os.path.join(d, "final.zip")
    if os.path.exists(final):
        return "trained" if FP.model_budget(final) else "corrupt"
    if os.path.isdir(d) and any(
            f == "meta.json" or (f.endswith(".zip") and
                                 (f.startswith("ckpt_") or f == "checkpoint.zip"))
            for f in os.listdir(d)):
        return "partial"
    return "fresh"


def quiet_minutes(d, log):
    """Minutes since anything in the run directory, or its log, last changed."""
    paths = [os.path.join(d, f) for f in os.listdir(d)] if os.path.isdir(d) else []
    if os.path.exists(log):
        paths.append(log)
    newest = max((os.path.getmtime(p) for p in paths), default=0.0)
    return (time.time() - newest) / 60


def git_status(ignore_prefix=None):
    """`git status --porcelain` -- the same question the fingerprint asks for
    `git_dirty` -- or None if git cannot be asked.

    `ignore_prefix`: during an evaluation, the result files it is itself
    writing (`results/<prefix>_seed<N>.txt`, untracked until committed) are
    not dirt."""
    try:
        r = subprocess.run(["git", "status", "--porcelain"], cwd=HERE,
                           capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    lines = r.stdout.strip().splitlines()
    if ignore_prefix:
        own = f"?? results/{ignore_prefix}_seed"
        lines = [ln for ln in lines if not ln.startswith(own)]
    return "\n".join(lines)


def git_head():
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=HERE,
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else "?"
    except (OSError, subprocess.SubprocessError):
        return "?"


def stamp():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def record(out, line):
    """Append one line to `<out>/LAUNCH.txt`. Phase D2 kept this file by hand."""
    os.makedirs(os.path.join(HERE, out), exist_ok=True)
    with open(os.path.join(HERE, out, "LAUNCH.txt"), "a", encoding="utf-8") as fh:
        fh.write(line.rstrip() + "\n")


def _free_gb():
    """Free physical memory in GB, or 0.0 if it cannot be asked.

    MEMORY, NOT CORES, IS THE LIMIT -- and the first launch of this script
    proved it the expensive way. Twelve cores said "run sixteen at once";
    thirteen of them died in `SAC.__init__` before training a single step,
    because each was allocating a replay buffer sized for a run twenty times
    longer than the one it was doing. Cores tell you how many runs can make
    progress; memory tells you how many can START.
    """
    try:
        import ctypes

        class MS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

        m = MS()
        m.dwLength = ctypes.sizeof(MS)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return m.ullAvailPhys / 2 ** 30
    except Exception:
        try:
            return (os.sysconf("SC_AVPHYS_PAGES")
                    * os.sysconf("SC_PAGE_SIZE") / 2 ** 30)
        except (ValueError, OSError, AttributeError):
            return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="*", default=None,
                    help="default 0-7. Duplicates are dropped. REQUIRED with "
                         "--restart-crashed, which must name the seed it means")
    ap.add_argument("--steps", type=int, default=50_000)
    ap.add_argument("--road", choices=("fixed", "random"), default="fixed",
                    help="'fixed' is Phase D. 'random' is the randomised "
                         "climb (Phase D2's design, and C4's): trains with "
                         "--road random, evaluates with --protocol d2. Where "
                         "agents and results go is --out and --prefix, NOT "
                         "the road: runs_d2/ and results/d2_* by default, "
                         "runs_c4/ and results/c4_* with --out runs_c4.")
    ap.add_argument("--out", default=None,
                    help="default runs/ (fixed) or runs_d2/ (random). A NEW "
                         "experiment gets its own, e.g. runs_c4/")
    ap.add_argument("--logs", default=None,
                    help="default <out>/_logs")
    ap.add_argument("--prefix", default=None,
                    help="--evaluate writes results/<prefix>_seed<N>.txt. "
                         "Default: from --out (runs -> phase_d, runs_d2 -> "
                         "d2, runs_c4 -> c4)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-done", action="store_true",
                    help="kept for old command lines; it is now ALWAYS on. A "
                         "directory holding final.zip is never relaunched and "
                         "an existing result file is never overwritten.")
    ap.add_argument("--restart-crashed", action="store_true",
                    help="a directory with checkpoints but no final.zip is a "
                         "crashed run. By default it is skipped and named. "
                         "With this flag it is moved to <out>/_crashed/ and "
                         "that seed trains FROM SCRATCH -- never resumed.")
    ap.add_argument("--allow-dirty", action="store_true",
                    help="launch from a tree with uncommitted changes. The "
                         "fingerprint will record git_dirty True.")
    ap.add_argument("--jobs", type=int, default=None,
                    help="how many runs at once. Default: sized to free memory "
                         "-- see MEMORY, NOT CORES, IS THE LIMIT in the "
                         "docstring.")
    ap.add_argument("--prove-buffer", action="store_true",
                    help="train one seed with both buffer sizes and compare "
                         "every network weight, then exit")
    ap.add_argument("--evaluate", action="store_true",
                    help="score the trained pairs instead of training: one "
                         "evaluate.py per seed, under the same memory cap")
    a = ap.parse_args()
    d2 = a.road == "random"
    if a.out is None:
        a.out = "runs_d2" if d2 else "runs"
    if a.logs is None:
        a.logs = os.path.join(a.out, "_logs")
    res_prefix = a.prefix or result_prefix(a.out)
    default_prefix = "d2" if d2 else "phase_d"
    closed = (CLOSED_OUT.get(os.path.basename(os.path.normpath(a.out)))
              or CLOSED_PREFIX.get(res_prefix))

    if a.prove_buffer:
        if a.dry_run:
            print("would run: python prove_buffer.py  (trains 2 x 2500 steps "
                  "into a temporary directory)")
            return 0
        return subprocess.call([sys.executable, "prove_buffer.py"], cwd=HERE)

    # --restart-crashed moves directories. It acts only on seeds named on the
    # command line: a crash is one seed, and the default 0-7 would sweep every
    # directory that merely looks unfinished -- including live ones.
    if a.restart_crashed and a.seeds is None:
        raise SystemExit("--restart-crashed needs --seeds naming the crashed "
                         "seed(s) -- it never acts on all eight by default.")
    seeds = sorted(set(a.seeds)) if a.seeds is not None else list(range(8))

    # Everything below is decided BEFORE anything launches, and printed, so the
    # dry run shows exactly what a real launch would touch.
    jobs, done, blocked, crashed = [], [], [], []
    wrong_budget = []
    if a.evaluate:
        # ONE evaluate.py PER SEED, not one for all of them. Each writes its
        # own results/phase_d_seed<N>.txt with its own fingerprint block, so a
        # seed can be re-run without touching the others and a result file is
        # never a summary of runs it cannot name.
        #
        # This re-scores the three hand-written policies once per seed, which
        # is redundant -- they do not depend on the agent. It is left redundant
        # on purpose: collapsing them would mean editing the evaluation
        # protocol after preregistering it, to save an hour of CPU.
        for s in seeds:
            tag = f"eval_seed{s}"
            res = os.path.join("results", f"{res_prefix}_seed{s}.txt")
            # NEVER OVERWRITE A RESULT FILE. They are committed evidence; to
            # re-score one, delete it yourself so the decision is in your
            # shell history, not in a default.
            if os.path.exists(os.path.join(HERE, res)):
                done.append(f"{tag} ({res} exists)")
                continue
            models = [os.path.join(a.out, f"{arm}_seed{s}")
                      for arm in ("sighted", "blind")]
            missing = [m for m in models
                       if not os.path.exists(os.path.join(HERE, m, "final.zip"))]
            if missing:
                blocked.append(f"{tag}: no final.zip in {', '.join(missing)}")
                continue
            argv = [sys.executable, "evaluate.py", "--out", res,
                    "--protocol", "d2" if d2 else "phase-d"]
            if res_prefix != default_prefix:
                # evaluate.py titles its report by PROTOCOL, and C4 is scored
                # on D2's protocol -- so without this every C4 result file
                # would open "PHASE D2 EVALUATION".
                argv += ["--label", f"{res_prefix.upper()} EVALUATION "
                                    f"(agents from {a.out}/)"]
            jobs.append((tag, argv + models))
    else:
        for s in seeds:
            for blind in (False, True):
                tag = f"{'blind' if blind else 'sighted'}_seed{s}"
                d = os.path.join(HERE, a.out, tag)
                state = run_state(d)
                if state == "running":
                    blocked.append(f"{tag}: being trained right now by process "
                                   f"{FP.running_pid(d)} -- left alone")
                    continue
                if state == "trained":
                    done.append(tag)
                    # A trained directory at a DIFFERENT budget means the wrong
                    # --out: "--steps 300000" without "--out runs_c4" lands on
                    # D2's agents, skips all sixteen and used to report success.
                    m = FP.read(os.path.join(d, "meta.json")) or {}
                    if m.get("steps_requested") not in (None, a.steps):
                        wrong_budget.append(f"{tag} ({m['steps_requested']:,})")
                    continue
                if state == "corrupt":
                    blocked.append(f"{tag}: final.zip is not a readable "
                                   "stable-baselines3 zip -- inspect it by hand")
                    continue
                if state == "partial":
                    if not a.restart_crashed:
                        blocked.append(
                            f"{tag}: started, not finished, no live process -- "
                            "a crash. NOT resumed. To re-run it from scratch: "
                            f"--seeds {s} --restart-crashed")
                        continue
                    crashed.append((tag, d))
                argv = [sys.executable, "train.py", "--steps", str(a.steps),
                        "--seed", str(s), "--out", a.out, "--road", a.road]
                if blind:
                    argv.append("--no-preview")
                if not closed:
                    # Every new experiment's runs are never resumed: a crash is
                    # re-run from scratch (PREREGISTRATION_C4.md section 6).
                    argv.append("--no-resume")
                jobs.append((tag, argv))

    free = _free_gb()
    # MEASURED, NOT ESTIMATED -- and the difference cost two launches.
    #
    # The first launch guessed nothing and started sixteen: thirteen died
    # allocating replay buffers. The second guessed 0.9 GB per run and started
    # nine: eight died with `RuntimeError: bad allocation` inside torch's
    # forward pass. Then one process was actually watched:
    #
    #     peak RSS of ONE train.py process: 1522 MB
    #
    # 1.5 GB, not 0.9 -- the guess was 70 % low, which is exactly the margin
    # that turned a safe cap into a failing one. PEAK_GB below is a
    # measurement; re-measure it if the network, the observation space or the
    # torch version changes, and do not adjust it to make a number of runs fit.
    PEAK_GB = 1.5
    RESERVE_GB = 5.0
    cap = a.jobs or max(1, min(os.cpu_count() or 4,
                               int((free - RESERVE_GB) / PEAK_GB) if free else 2))
    what = "evaluations" if a.evaluate else f"runs, {a.steps:,} steps each"
    print(f"{len(jobs)} {what} to launch")
    print(f"  agents   {a.out}/")
    print(f"  logs     {a.logs}/   (appended to, never truncated)")
    if a.evaluate:
        print(f"  results  results/{res_prefix}_seed<N>.txt   (an existing file "
              "is never overwritten)")
    if done:
        print(f"  skipping {len(done)} already done: {', '.join(done)}")
    for line in blocked:
        print(f"  BLOCKED  {line}")
    for tag, d in crashed:
        print(f"  CRASHED  {tag}: would be moved to "
              f"{os.path.join(a.out, '_crashed')}/ and trained from scratch")
    if wrong_budget:
        print(f"\nWRONG --out? {a.out}/ holds agents trained for a different "
              f"budget than --steps {a.steps:,}:\n  " + ", ".join(wrong_budget))
        print("A new budget is a new experiment with its own --out "
              "(e.g. --out runs_c4). Nothing launched.")
        return 1
    if closed and jobs:
        print(f"\nREFUSING: {a.out}/ and results/{res_prefix}_* belong to "
              f"{closed}, a closed experiment ('sixteen runs, then stop').")
        print("A new seed or budget goes in its own --out. Nothing launched.")
        return 1
    dirty = git_status(res_prefix if a.evaluate else None)
    if dirty is None:
        print("  tree     git could not be asked")
    elif dirty:
        print(f"  tree     DIRTY, {len(dirty.splitlines())} entries -- "
              + ("--allow-dirty given" if a.allow_dirty
                 else "a launch is REFUSED without --allow-dirty"))
    else:
        print(f"  tree     clean at {git_head()}")
    print(f"  {os.cpu_count()} cores, {free:.1f} GB free  ->  {cap} at a time")
    for tag, argv in jobs:
        print(f"  {tag:<18} {' '.join(argv[1:])}")
    if a.dry_run:
        return 0
    if not jobs:
        # Nothing to do is not a launch: no LAUNCH.txt line, no "next:" hint.
        print("\nnothing to launch.")
        return 1 if blocked else 0
    if dirty and not a.allow_dirty:
        print("\nREFUSING to launch from a dirty tree:\n" + dirty)
        print("Commit first, or pass --allow-dirty and say so beside the result.")
        return 1

    # The crash rule, checked AGAIN at the moment of the move: the directory
    # must still be unfinished, have no live process, and have been quiet for
    # QUIET_MIN minutes. A run that finished, or came back, since the plan was
    # printed is left alone and its job dropped.
    for tag, d in list(crashed):
        log = os.path.join(HERE, a.logs, f"{tag}.log")
        quiet = quiet_minutes(d, log)
        if run_state(d) != "partial" or quiet < QUIET_MIN:
            print(f"  NOT moving {tag}: state {run_state(d)}, quiet for "
                  f"{quiet:.0f} min (need {QUIET_MIN}) -- it may still be "
                  "training. Confirm the process is gone and retry.")
            crashed.remove((tag, d))
            jobs = [j for j in jobs if j[0] != tag]
    if not jobs:
        print("\nnothing to launch.")
        return 1

    os.makedirs(os.path.join(HERE, a.logs), exist_ok=True)
    record(a.out, f"launch {stamp()} at {git_head()}"
           f"{' DIRTY' if dirty else ''}: {' '.join(sys.argv[1:])} "
           f"-- {len(jobs)} jobs, cap {cap}")
    for tag, d in crashed:
        dest = os.path.join(HERE, a.out, "_crashed",
                            f"{tag}_{time.strftime('%Y%m%dT%H%M%S')}")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.move(d, dest)
        record(a.out, f"crashed {stamp()}: {tag} moved to "
                      f"{os.path.relpath(dest, HERE)}; retrained from scratch")
        print(f"  moved {tag} -> {os.path.relpath(dest, HERE)}")
    if a.evaluate:
        os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", OMP_NUM_THREADS="1",
               MKL_NUM_THREADS="1")

    # IN WAVES, not all at once. The first launch started all sixteen and
    # thirteen died allocating memory; a cap is the difference between "twelve
    # cores" and "twelve runs that can actually start".
    pending, live, failed, ok, t0 = list(jobs), [], [], [], time.time()
    held_dirty = False
    while pending or live:
        # THE TREE IS CHECKED BEFORE EVERY START, not once. Each train.py and
        # evaluate.py records git_dirty from its own start, and a second wave
        # starts hours after the first -- an uncommitted edit made in between
        # would stamp those runs dirty. Hold the queue instead, and say so.
        if pending and not a.allow_dirty:
            dirt = git_status(res_prefix if a.evaluate else None)
            if dirt:
                if not held_dirty:
                    print(f"  holding {len(pending)} queued: the tree is dirty "
                          "-- commit, and the queue resumes:\n    "
                          + dirt.replace("\n", "\n    "))
                held_dirty = True
            elif held_dirty:
                print("  tree clean again -- resuming the queue")
                held_dirty = False
        while pending and len(live) < cap and not held_dirty:
            # A CAP COMPUTED AT THE START IS A PREDICTION; this is a check.
            # Free memory moves while the runs are going -- other processes
            # come and go, and a run's own footprint grows as its buffer
            # fills -- so a cap that was right at launch can be wrong twenty
            # minutes later. Refuse to add a run when there is no room for one,
            # and wait instead of failing it.
            if live and _free_gb() and _free_gb() < RESERVE_GB + PEAK_GB:
                print(f"  holding {len(pending)} queued: "
                      f"{_free_gb():.1f} GB free, need "
                      f"{RESERVE_GB + PEAK_GB:.1f} to start another")
                break
            tag, argv = pending.pop(0)
            # APPEND, NEVER "w". This used to open the log in "w" mode, which
            # erased a finished run's training log the instant a relaunch
            # started -- before train.py had even decided whether to refuse.
            fh = open(os.path.join(HERE, a.logs, f"{tag}.log"), "a",
                      encoding="utf-8")
            fh.write(f"\n===== {stamp()} run_phase_d.py launch at "
                     f"{git_head()}: {' '.join(argv[1:])} =====\n")
            fh.flush()
            p = subprocess.Popen(argv, cwd=HERE, env=env, stdout=fh,
                                 stderr=subprocess.STDOUT)
            live.append((tag, p, fh))
            print(f"launched {tag:<18} pid {p.pid}   "
                  f"({len(live)} running, {len(pending)} queued)")
        time.sleep(5)
        for entry in list(live):
            tag, p, fh = entry
            rc = p.poll()
            if rc is None:
                continue
            fh.close()
            live.remove(entry)
            (ok if rc == 0 else failed).append(tag)
            mark = "ok  " if rc == 0 else "FAIL"
            print(f"  {mark} {tag:<18} exit {rc}   "
                  f"({(time.time() - t0) / 60:.0f} min elapsed, "
                  f"{len(ok)} done, {len(failed)} failed)")

    print(f"\n{len(ok)} of {len(jobs)} jobs finished cleanly "
          f"in {(time.time() - t0) / 60:.0f} min")
    record(a.out, f"done {stamp()}: {len(ok)} ok, {len(failed)} failed"
                  + (f" ({', '.join(failed)})" if failed else ""))
    pre = PREREG.get(res_prefix, "the experiment's preregistration")
    if failed or blocked:
        # PREREGISTRATION section 6: a failed run is RE-RUN WITH THE SAME SEED
        # and the failure is recorded. It is not replaced by a different seed
        # and it is not quietly dropped. For C4 the re-run is FROM SCRATCH
        # (--restart-crashed), because a resume is not the same agent.
        if failed:
            print("failed: " + ", ".join(failed))
        if blocked:
            print("blocked: " + "; ".join(blocked))
        print("Re-run each with the SAME seed and record the failure in "
              f"results/{pre} -- section 6.")
        if not a.evaluate and not closed:
            print("A crashed run of a new experiment is re-run FROM SCRATCH, "
                  "once its process is gone:\n  python run_phase_d.py "
                  f"--road {a.road} --steps {a.steps} --out {a.out} "
                  "--seeds <k> --restart-crashed")
        return 1
    road = f" --road {a.road}"
    out = f" --out {a.out}"
    if a.evaluate:
        print(f"\nnext: python {ANALYSIS.get(res_prefix, '<the experiment analysis script>')}")
    else:
        print(f"\nnext: python run_phase_d.py --evaluate{road}{out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

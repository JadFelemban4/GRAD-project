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
"""
import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))


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
    ap.add_argument("--seeds", type=int, nargs="*", default=list(range(8)))
    ap.add_argument("--steps", type=int, default=50_000)
    ap.add_argument("--out", default="runs")
    ap.add_argument("--logs", default="runs/_logs")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-done", action="store_true",
                    help="leave a run alone if runs/<tag>/final.zip exists. "
                         "For resuming after a partial launch.")
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

    if a.prove_buffer:
        return subprocess.call([sys.executable, "prove_buffer.py"], cwd=HERE)

    jobs, done = [], []
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
        os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
        for s in a.seeds:
            tag = f"eval_seed{s}"
            res = os.path.join("results", f"phase_d_seed{s}.txt")
            if a.skip_done and os.path.exists(os.path.join(HERE, res)):
                done.append(tag)
                continue
            jobs.append((tag, [sys.executable, "evaluate.py", "--out", res,
                               os.path.join(a.out, f"sighted_seed{s}"),
                               os.path.join(a.out, f"blind_seed{s}")]))
    else:
        for s in a.seeds:
            for blind in (False, True):
                tag = f"{'blind' if blind else 'sighted'}_seed{s}"
                if a.skip_done and os.path.exists(
                        os.path.join(HERE, a.out, tag, "final.zip")):
                    done.append(tag)
                    continue
                argv = [sys.executable, "train.py", "--steps", str(a.steps),
                        "--seed", str(s), "--out", a.out]
                if blind:
                    argv.append("--no-preview")
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
    print(f"{len(jobs)} runs to launch, {a.steps:,} steps each")
    if done:
        print(f"  skipping {len(done)} already finished: {', '.join(done)}")
    print(f"  {os.cpu_count()} cores, {free:.1f} GB free  ->  {cap} at a time")
    for tag, argv in jobs:
        print(f"  {tag:<18} {' '.join(argv[1:])}")
    if a.dry_run:
        return 0

    os.makedirs(os.path.join(HERE, a.logs), exist_ok=True)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", OMP_NUM_THREADS="1",
               MKL_NUM_THREADS="1")

    # IN WAVES, not all at once. The first launch started all sixteen and
    # thirteen died allocating memory; a cap is the difference between "twelve
    # cores" and "twelve runs that can actually start".
    pending, live, failed, ok, t0 = list(jobs), [], [], [], time.time()
    while pending or live:
        while pending and len(live) < cap:
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
            fh = open(os.path.join(HERE, a.logs, f"{tag}.log"), "w",
                      encoding="utf-8")
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

    print(f"\n{len(ok)} of {len(jobs)} runs finished cleanly "
          f"in {(time.time() - t0) / 60:.0f} min")
    if failed:
        # PREREGISTRATION section 6: a failed run is RE-RUN WITH THE SAME SEED
        # and the failure is recorded. It is not replaced by a different seed
        # and it is not quietly dropped.
        print("failed: " + ", ".join(failed))
        print("Re-run each with the SAME seed and record the failure in "
              "results/PREREGISTRATION.md -- section 6.")
        return 1
    print("\nnext, per seed:")
    print("  python evaluate.py --out results/phase_d_seed<N>.txt \\")
    print("      runs/sighted_seed<N> runs/blind_seed<N>")
    return 0


if __name__ == "__main__":
    sys.exit(main())

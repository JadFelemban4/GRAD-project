"""train_all.py -- every seed of Phase D's pair, on one machine.

    python train_all.py                  # seeds 0-9, sighted and blinded: 20 runs
    python train_all.py --seeds 0 1 2    # a subset
    python train_all.py --jobs 10        # at most ten at once

Each run is `python train.py --steps STEPS --seed S [--no-preview]` in its own
process with OMP_NUM_THREADS=1, logging to runs/terrain_dt1/log_<tag>.txt.
Re-running resumes every run from its last checkpoint (train.py), so a closed
laptop costs at most the 10 000 steps since the last one.

WHY ONE PROCESS PER RUN, ON THE CPU (29 September 2026, measured): a step is
84 % plant, which is numpy on one core, so the runs parallelise across cores
and not across anything else; see train.py's docstring for the timing. On
19 September ten runs sharing the 20-thread team laptop ran about 4.5 steps/s
each, against 13.7 alone.

Then score and document them:

    python record_agents.py runs/terrain_dt1
"""
import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=list(range(10)))
    ap.add_argument("--steps", type=int, default=50_000)
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--out", default=os.path.join("runs", "terrain_dt1"))
    a = ap.parse_args()

    runs = [(s, blind) for s in a.seeds for blind in (False, True)]
    os.makedirs(os.path.join(HERE, a.out), exist_ok=True)
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONUNBUFFERED="1")
    queue, live, done = list(runs), {}, []
    t0 = time.time()
    print(f"{len(runs)} runs, {a.steps:,} steps each, at most {a.jobs} at once -> {a.out}/")
    while queue or live:
        while queue and len(live) < a.jobs:
            s, blind = queue.pop(0)
            tag = f"{'blind' if blind else 'sighted'}_seed{s}"
            cmd = [sys.executable, "train.py", "--steps", str(a.steps), "--seed", str(s), "--out", a.out]
            if blind:
                cmd.append("--no-preview")
            log = open(os.path.join(HERE, a.out, f"log_{tag}.txt"), "a")
            live[tag] = (subprocess.Popen(cmd, cwd=HERE, env=env, stdout=log, stderr=subprocess.STDOUT), log)
            print(f"  started {tag}")
        time.sleep(20)
        for tag, (p, log) in list(live.items()):
            if p.poll() is not None:
                log.close()
                done.append((tag, p.returncode))
                del live[tag]
                print(f"  {'finished' if p.returncode == 0 else 'FAILED (exit %d)' % p.returncode} {tag}"
                      f"  after {(time.time() - t0) / 60:.0f} min")
    bad = [t for t, rc in done if rc != 0]
    print(f"\nall done in {(time.time() - t0) / 60:.0f} min; "
          + (f"FAILED: {', '.join(bad)} -- read their logs, then re-run to resume" if bad else "every run finished"))
    print("next: python record_agents.py " + a.out)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

"""train_all.py -- every seed of Phase D's pair, on one machine.

    python train_all.py --road extremes --seeds 0-19 --no-resume   # the 8 Oct design: 40 runs
    python train_all.py --road terrain                 # the 29 Sep design (CLOSED: runs/terrain_dt1)
    python train_all.py --road extremes --jobs 10      # at most ten at once

THE ROAD IS REQUIRED (8 October 2026). Until then this launcher passed no
--road and no --dt and leaned on train.py's defaults, which is the trap AUDIT2.md
Part 3 names: a default that selects an experiment. Both are passed explicitly.

Each run is `python train.py --road R --dt 1 --steps STEPS --seed S --out OUT
[--no-preview] [--no-resume]` in its own process with OMP_NUM_THREADS=1,
logging to OUT/log_<tag>.txt.

CRASHES. Without --no-resume, re-running resumes every run from its last
checkpoint, so a closed laptop costs at most the 10 000 steps since the last
one -- but SAC.load does not restore the replay buffer, so a resumed agent is
not the agent an unbroken run would have trained. With --no-resume (C4's crash
rule, and the 8 October preregistration's), a run that died is moved aside to
OUT/<tag>.crashed<N> -- kept, never deleted -- and trained again from step 0;
on the CPU with one thread a fresh run from the same seed is the same agent
(C4 retraced its D2 twins bit for bit).

WHY ONE PROCESS PER RUN, ON THE CPU (29 September 2026, measured): a step is
84 % plant, which is numpy on one core, so the runs parallelise across cores
and not across anything else; see train.py's docstring for the timing. On
19 September ten runs sharing the 20-thread team laptop ran about 4.5 steps/s
each, against 13.7 alone.

Then score and document them:

    python record_agents.py runs/<road>_dt1
"""
import argparse
import json
import os
import subprocess
import sys
import time

import fingerprint as FP

HERE = os.path.dirname(os.path.abspath(__file__))


def seeds(spec):
    """'0-19' or '0 1 2' -> a list of ints."""
    out = []
    for part in spec:
        lo, _, hi = part.partition("-")
        out += list(range(int(lo), int(hi) + 1)) if hi else [int(lo)]
    return out


def move_crashed(outdir):
    """A --no-resume run that died: moved aside, kept, and named for what it is."""
    if not os.path.isdir(outdir) or os.path.exists(os.path.join(outdir, "final.zip")):
        return None
    if FP.running_pid(outdir):
        raise SystemExit(f"{outdir} is being trained right now; stop that first.")
    try:
        with open(os.path.join(outdir, "meta.json"), encoding="utf-8") as fh:
            if json.load(fh).get("resume_allowed") is not False:
                return None
    except (OSError, ValueError):
        pass
    n = 1
    while os.path.exists(f"{outdir}.crashed{n}"):
        n += 1
    os.rename(outdir, f"{outdir}.crashed{n}")
    return f"{outdir}.crashed{n}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--road", required=True, choices=("terrain", "extremes"))
    ap.add_argument("--dt", type=float, default=1.0)
    ap.add_argument("--seeds", nargs="+", default=["0-9"], help="'0-19' or '0 1 2'")
    ap.add_argument("--steps", type=int, default=50_000)
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--out", default=None, help="default runs/<road>_dt1")
    ap.add_argument("--no-resume", action="store_true",
                    help="a crash is re-run from step 0, never resumed (see the docstring)")
    a = ap.parse_args()
    a.seeds = seeds(a.seeds)
    if a.out is None:
        a.out = os.path.join("runs", f"{a.road}_dt{a.dt:g}".replace(".", "p"))

    runs = [(s, blind) for s in a.seeds for blind in (False, True)]
    os.makedirs(os.path.join(HERE, a.out), exist_ok=True)
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONUNBUFFERED="1")
    queue, live, done = list(runs), {}, []
    t0 = time.time()
    print(f"{len(runs)} runs ({a.road}, dt {a.dt:g}), {a.steps:,} steps each, "
          f"at most {a.jobs} at once -> {a.out}/")
    while queue or live:
        while queue and len(live) < a.jobs:
            s, blind = queue.pop(0)
            tag = f"{'blind' if blind else 'sighted'}_seed{s}"
            if a.no_resume:
                moved = move_crashed(os.path.join(HERE, a.out, tag))
                if moved:
                    print(f"  {tag} had crashed: moved aside to {moved}, training it again from 0")
            cmd = [sys.executable, "train.py", "--road", a.road, "--dt", f"{a.dt:g}",
                   "--steps", str(a.steps), "--seed", str(s), "--out", a.out]
            if blind:
                cmd.append("--no-preview")
            if a.no_resume:
                cmd.append("--no-resume")
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
          + (f"FAILED: {', '.join(bad)} -- read their logs, then re-run this command"
             + (" (each is moved aside and trained again from 0)" if a.no_resume else " to resume")
             if bad else "every run finished"))
    print("next: python record_agents.py " + a.out)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

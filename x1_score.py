"""x1_score.py -- score X1 once its training has finished, in the preregistered order.

    python x1_score.py            wait for the 46 runs, then every step below
    python x1_score.py --from 5   start at step 5 (the earlier ones already ran)

Written 8 October 2026, after X1's preregistration (results/PREREGISTRATION_X1.md)
and while its agents trained; it runs nothing the preregistration does not name,
in the order of its section 10, and it changes no rule. Started in its own
window so that a scoring job of several hours does not depend on any one
terminal or session staying open.

    0  wait     every run has final.zip, train_all.py has printed "all done", and
                every run's meta.json carries X1's plant -- or stop and say why
    1  python run_results.py phase_d --agents=runs/extremes_dt1
    2  python record_agents.py runs/extremes_dt1        needs 1 (its regression check)
    3  python analyse_x1.py                             needs 2 -> results/X1_RESULT.txt
    4  python sanity_probe.py runs/extremes_dt1         needs 2
    5  python conditions_test.py --set runs/extremes_dt1 --resume-all     needs 2
    6  python logged_check.py --set runs/extremes_dt1   needs only the agents

Each step's output goes to results/x1_score/<n>_<name>.log, and one line per
step -- command, start, end, exit code -- to results/x1_score/SCORE_LOG.txt. A
failed step stops the steps that need it and none of the others.
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SET = "runs/extremes_dt1"
N_RUNS = 46
PLANT_SHA = "3c48890dd15bc116"
DERIVED_SHA = "326c0835548975e2"
OUT = os.path.join(HERE, "results", "x1_score")
STEPS = [
    (1, "phase_d", ["run_results.py", "phase_d", f"--agents={SET}"], []),
    (2, "record_agents", ["record_agents.py", SET], [1]),
    (3, "analyse_x1", ["analyse_x1.py"], [2]),
    (4, "sanity_probe", ["sanity_probe.py", SET], [2]),
    (5, "conditions", ["conditions_test.py", "--set", SET, "--resume-all"], [2]),
    (6, "logged_check", ["logged_check.py", "--set", SET], []),
]


def log(line):
    os.makedirs(OUT, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join(OUT, "SCORE_LOG.txt"), "a", encoding="utf-8") as fh:
        fh.write(f"{stamp}  {line}\n")
    print(f"{stamp}  {line}", flush=True)


def training_done():
    d = os.path.join(HERE, SET)
    finals = glob.glob(os.path.join(d, "*_seed*", "final.zip"))
    try:
        with open(os.path.join(d, "LAUNCH.txt"), encoding="utf-8", errors="replace") as fh:
            launch = fh.read()
    except OSError:
        launch = ""
    if "FAILED" in launch and "all done" in launch:
        raise SystemExit("train_all.py reports FAILED runs: re-run its command (the crash rule moves "
                         "each dead run aside and trains it again from 0), then start this again")
    return len(finals) >= N_RUNS and "all done" in launch, len(finals)


def check_plant():
    bad = []
    for m in sorted(glob.glob(os.path.join(HERE, SET, "*_seed*", "meta.json"))):
        with open(m, encoding="utf-8") as fh:
            meta = json.load(fh)
        if meta.get("plant_sha") != PLANT_SHA or meta.get("derived_sha") != DERIVED_SHA:
            bad.append(os.path.basename(os.path.dirname(m)))
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", type=int, default=1)
    a = ap.parse_args()
    log(f"x1_score.py started (from step {a.start})")
    while True:
        done, n = training_done()
        if done:
            break
        time.sleep(300)
    log(f"training finished: {n} final.zip")
    bad = check_plant()
    if bad:
        log(f"STOP: {len(bad)} runs carry another plant: {', '.join(bad)}")
        sys.exit(1)
    failed = set()
    env = dict(os.environ, PYTHONIOENCODING="utf-8", OMP_NUM_THREADS="1")
    for n, name, args, needs in STEPS:
        if n < a.start:
            continue
        if failed & set(needs):
            log(f"step {n} {name}: SKIPPED, it needs step(s) {sorted(failed & set(needs))}")
            failed.add(n)
            continue
        cmd = [sys.executable, "-u"] + args
        t0 = time.time()
        log(f"step {n} {name}: {' '.join(args)}")
        with open(os.path.join(OUT, f"{n}_{name}.log"), "w", encoding="utf-8") as fh:
            rc = subprocess.run(cmd, cwd=HERE, env=env, stdout=fh, stderr=subprocess.STDOUT).returncode
        log(f"step {n} {name}: exit {rc} after {(time.time() - t0) / 60:.0f} min")
        if rc != 0:
            failed.add(n)
    log("x1_score.py finished" + (f"; FAILED steps {sorted(failed)}" if failed else "; every step exited 0"))


if __name__ == "__main__":
    main()

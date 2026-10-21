"""ecu_shift.py -- step 5 of engine_thresholds.py: the B58 baseline ECU's boosted output shifted.

The B58 plant ONLY: no EPA data, no fit, no training. One row of the E8 measurement of
results/ENGINE_THRESHOLDS.md (review of 21 October, findings 10 and 29) per run: the baseline ECU's
output while its own load input exceeds 100 kPa shifted by DSPARK deg and DLAMBDA. Every policy takes
the ECU's spark and lambda plus its trim (engine_env.py:982, :1004-1006), so the shift moves the
baseline and every policy at once, as an ECU-strategy error of a fitted model would.

  MODE fixed: the knee stays at the B58's 1123 K (the 850 C row's fixed-knee scoring).
  MODE k3:    decision 33's rule K3 (VALIDATION_DECISIONS.md:156) is applied after the shift: the knee
              K' is set so that the shifted baseline spends as long above K' on the locked climb as the
              unshifted baseline spends above 1123 K; the hand-written policies trigger on that knee
              (check_premise.trigger_k reads the plant's knee) and damage is scored against it.

The locked climb, frozen episode 1, dt 1 s, the four hand-written policies of check_premise.py. RUNS
lists the 24 runs (9 fixed, 15 k3); each takes about 10-16 minutes and is independent of the others.
The patch of BaselineECU.step is global, so every run gets a process of its own:

    python -m thresholds.ecu_shift MODE NAME DSPARK DLAMBDA     one run, from the repository root

run_all() starts them, `jobs` at a time. Each writes results/ENGINE_THRESHOLDS/ecu/<MODE>_<NAME>.json
and prints that file's content as one line. The file holds no wall-clock time (version 2's and the
first version 3 run's held `seconds`): it is a function of the code and the plant alone, so a re-run
gives it back byte for byte, and the contract's sha256 of it with it. The step's time is in run.json.
"""
import dataclasses
import json
import os
import subprocess
import sys
import tempfile
import time

from thresholds import common

ECU_LOAD_KPA = 100.0      # the shift acts while the ECU's own load input is above this
SEL = slice(400, 719)     # the medians' window, t 400-718 s
RUNS = (
    ("fixed", "nominal", 0.0, 0.0),
    ("fixed", "lam-0.02", 0.0, -0.02), ("fixed", "lam-0.05", 0.0, -0.05), ("fixed", "lam-0.10", 0.0, -0.1),
    ("fixed", "lam+0.02", 0.0, 0.02), ("fixed", "lam+0.05", 0.0, 0.05),
    ("fixed", "spark-1.5", -1.5, 0.0), ("fixed", "spark-0.75", -0.75, 0.0), ("fixed", "spark+0.75", 0.75, 0.0),
    ("k3", "nominal", 0.0, 0.0),
    ("k3", "lam-0.005", 0.0, -0.005), ("k3", "lam-0.01", 0.0, -0.01), ("k3", "lam-0.02", 0.0, -0.02),
    ("k3", "lam-0.05", 0.0, -0.05), ("k3", "lam-0.10", 0.0, -0.1),
    ("k3", "lam+0.005", 0.0, 0.005), ("k3", "lam+0.01", 0.0, 0.01), ("k3", "lam+0.02", 0.0, 0.02),
    ("k3", "lam+0.05", 0.0, 0.05),
    ("k3", "spark-3.0", -3.0, 0.0), ("k3", "spark-1.5", -1.5, 0.0), ("k3", "spark-0.75", -0.75, 0.0),
    ("k3", "spark+0.75", 0.75, 0.0), ("k3", "spark+1.5", 1.5, 0.0),
)


def path(mode, name):
    return os.path.join(common.ECU_DIR, f"{mode}_{name}.json")


def one(mode, name, ds, dl):
    """One run, in this process. Patches engine_env.BaselineECU.step and restores it."""
    import numpy as np
    import check_premise as C
    import engine_env as E
    import engines
    import evaluate as V

    PLANT = engines.get("b58")
    ORIG_STEP = E.BaselineECU.step
    POL = [("baseline", C.p_neutral), ("reactive", C.p_reactive), ("current-grade", C.p_grade_now),
           ("predictive", C.p_predictive)]

    def patch(ds, dl):
        def step(self, rpm, map_kpa, iat_k, ect_k, knock_observed, dt):
            sp, lam, fan = ORIG_STEP(self, rpm, map_kpa, iat_k, ect_k, knock_observed, dt)
            if map_kpa > ECU_LOAD_KPA:
                c = self.cal
                sp = float(np.clip(sp + ds, c.spark_min, c.spark_max))
                lam = lam + dl
            return sp, lam, fan
        E.BaselineECU.step = step

    def baseline_trace(plant):
        seed, w = V.EPISODES[0]
        env = E.SupervisoryTunerEnv(V.episode_cycle(None, plant=plant), plant=plant, dt=V.DT, seed=seed)
        env.reset(seed=seed)
        env.w = np.asarray(w, dtype=np.float32)
        tt, lam, sp = [], [], []
        while True:
            _, _, term, trunc, info = env.step(np.array(E.neutral_action(), dtype=np.float32))
            tt.append(info["t_turb"]); lam.append(info["lam"]); sp.append(info["spark"])
            if term or trunc:
                break
        return np.array(tt), np.array(lam), np.array(sp)

    def knee_for(trace, seconds):
        """The knee K with exactly `seconds` of the trace above it (dt 1 s): the trace's sorted values."""
        s = np.sort(trace)[::-1]
        n = int(round(seconds))
        return float(0.5 * (s[n - 1] + s[n])) if 0 < n < len(s) else float(s[min(max(n, 0), len(s) - 1)])

    def with_knee(plant, k):
        dmg = dataclasses.replace(plant.engine.damage, turb_knee_k=k)
        return dataclasses.replace(plant, engine=dataclasses.replace(plant.engine, damage=dmg))

    k0 = PLANT.engine.damage.turb_knee_k
    tr0, _, _ = baseline_trace(PLANT)
    above0 = int((tr0 > k0).sum())
    patch(ds, dl)
    try:
        tr, lam, sp = baseline_trace(PLANT)
        k = k0 if (mode == "fixed" or (ds == 0.0 and dl == 0.0)) else knee_for(tr, above0)
        p = with_knee(PLANT, k)
        seed, w = V.EPISODES[0]
        r = {n: V.run_episode(pol, seed, w, plant=p) for n, pol in POL}
    finally:
        E.BaselineECU.step = ORIG_STEP
    out = dict(mode=mode, name=name, dspark=ds, dlambda=dl, knee_k=k, knee_shift_k=k - k0,
               time_above_nominal_s=above0, time_above_knee_s=int((tr > k).sum()),
               base_peak_c=float(tr.max() - 273.15), base_lambda_median_400_718=float(np.median(lam[SEL])),
               base_spark_median_400_718=float(np.median(sp[SEL])),
               damage={n: v["damage"] for n, v in r.items()},
               damage_thermal={n: v["damage_thermal"] for n, v in r.items()})
    common.write_json(path(mode, name), out)
    return out


def run_all(jobs):
    """Every run of RUNS, each in its own process, `jobs` at a time; prints each run's line in RUNS
    order. Stops if any run fails. A run's own output goes to a temporary file, so no pipe can fill."""
    os.makedirs(common.ECU_DIR, exist_ok=True)
    pending = list(RUNS)
    running, done = [], {}
    t0 = time.time()
    try:
        while pending or running:
            while pending and len(running) < jobs:
                mode, name, ds, dl = pending.pop(0)
                log = tempfile.TemporaryFile(mode="w+", encoding="utf-8")
                cmd = [sys.executable, "-m", "thresholds.ecu_shift", mode, name, repr(ds), repr(dl)]
                running.append(((mode, name), log, subprocess.Popen(cmd, cwd=common.REPO, stdout=log,
                                                                    stderr=subprocess.STDOUT)))
            time.sleep(2.0)
            for item in list(running):
                key, log, proc = item
                if proc.poll() is None:
                    continue
                running.remove(item)
                log.seek(0)
                text = log.read()
                log.close()
                if proc.returncode != 0:
                    raise RuntimeError(f"ECU run {key} failed (exit {proc.returncode}):\n{text}")
                done[key] = text.strip().splitlines()[-1]
                print(f"   [{len(done)}/{len(RUNS)}] {key[0]} {key[1]} done at {time.time() - t0:.0f} s",
                      file=sys.stderr, flush=True)
    finally:
        for _, log, proc in running:
            proc.kill()
            log.close()
    for mode, name, _, _ in RUNS:
        print(done[(mode, name)])


def main():
    mode, name, ds, dl = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
    out = one(mode, name, ds, dl)
    print(json.dumps(out))


if __name__ == "__main__":
    sys.path.insert(0, common.REPO)
    os.chdir(common.REPO)
    main()

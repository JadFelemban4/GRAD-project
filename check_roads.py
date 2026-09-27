"""check_roads.py -- is every training road a fair one?

    python check_roads.py              # 40 roads, about two minutes on 20 cores
    python check_roads.py --n 100

train.py draws a new road every episode (engine_env.TerrainTrainingEnv). A road
is only fit to train on if the BASELINE can drive it: if the baseline cannot
deliver the torque the road asks for, every policy pays the same tracking
penalty, the neutral policy stops scoring zero, and the agent is paid for
covering the load loop rather than for protecting the turbine. That is exactly
what the first sample of these roads found, before the gearbox's shift rule
learned what the engine can deliver (engine_env.Vehicle.DELIVERABLE_TORQUE).

For each road this drives the neutral policy -- the baseline ECU, untouched --
and reports the family, the grade range, the turbine peak, how long it spends
above the protection trigger, the neutral policy's mean reward, and the p95
torque-tracking error in the reward's own units. It writes
results/training_roads.json, which make_page.py draws.

PASS means every road keeps the neutral reward inside +-0.05 and its p95
tracking error inside the reward's tolerance band. It also prints how many
roads push the baseline past the trigger: training needs both kinds, roads
where protection is needed and roads where it only costs fuel.

Evaluation never uses these roads. evaluate.py scores the locked climb only.
"""
import argparse
import collections
import json
import os
from concurrent.futures import ProcessPoolExecutor

os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIRST_SEED = 100


def drive(seed):
    from engine_env import TerrainTrainingEnv, neutral_action, TURB_PROTECT_K
    env = TerrainTrainingEnv(duration=900.0, dt=1.0, seed=seed)
    env.reset(seed=seed)
    act = neutral_action()
    rs, errs, turb = [], [], []
    while True:
        _, r, term, trunc, info = env.step(act)
        rs.append(r)
        errs.append(abs(info["torque_req"] - info["torque"]) / max(info["torque_req"], 40.0))
        turb.append(info["t_turb"])
        if term or trunc:
            break
    turb = np.array(turb)
    g = env.cycle["grade"]
    return dict(seed=seed, family=env.cycle["family"],
                grade_min=float(g.min()), grade_max=float(g.max()),
                peak_c=float(turb.max() - 273.15),
                above_pct=float(100.0 * (turb > TURB_PROTECT_K).mean()),
                neutral_r=float(np.mean(rs)), p95_err=float(np.percentile(errs, 95)),
                grade=[round(float(x), 4) for x in g[::5]],
                elev_m=[round(float(x), 1) for x in env.cycle["elev_m"][::5]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    a = ap.parse_args()
    from engine_env import TRACK_TOL

    with ProcessPoolExecutor(max_workers=min(18, a.n)) as ex:
        R = list(ex.map(drive, range(FIRST_SEED, FIRST_SEED + a.n)))

    print(f"{'seed':>5} {'road':<8}{'grade %':>15}{'peak C':>8}{'>850 C':>8}"
          f"{'neutral r':>11}{'p95 err':>9}")
    for r in R:
        print(f"{r['seed']:>5} {r['family']:<8}{100 * r['grade_min']:>6.1f} to{100 * r['grade_max']:>5.1f}"
              f"{r['peak_c']:>8.0f}{r['above_pct']:>7.1f}%{r['neutral_r']:>+11.4f}{r['p95_err']:>9.3f}")

    worst_r = max(R, key=lambda r: abs(r["neutral_r"]))
    worst_e = max(R, key=lambda r: r["p95_err"])
    binding = sum(r["peak_c"] > 850.0 for r in R)
    ok = abs(worst_r["neutral_r"]) < 0.05 and worst_e["p95_err"] < TRACK_TOL
    print(f"\nroads by family:      {dict(collections.Counter(r['family'] for r in R))}")
    print(f"baseline past 850 C:  {binding} of {len(R)} roads")
    print(f"worst neutral reward: {worst_r['neutral_r']:+.4f}  (seed {worst_r['seed']}, want |r| < 0.05)")
    print(f"worst p95 tracking:   {worst_e['p95_err']:.3f}  (seed {worst_e['seed']}, "
          f"tolerance band {TRACK_TOL})")
    print("\nPASS -- every road is one the baseline can drive." if ok else
          "\nFAIL -- some road asks for torque the baseline cannot deliver. Do not train.")

    out = os.path.join(HERE, "results", "training_roads.json")
    with open(out, "w") as fh:
        json.dump(dict(roads=R, binding=binding, n=len(R),
                       worst_neutral_r=worst_r["neutral_r"], worst_p95_err=worst_e["p95_err"],
                       tolerance=TRACK_TOL, passed=ok), fh)
    print(f"wrote {os.path.relpath(out, HERE)}")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

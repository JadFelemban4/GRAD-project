"""check_roads.py -- is every training road a fair one?

    python check_roads.py              # 40 roads, about two minutes on 20 cores
    python check_roads.py --n 100
    python check_roads.py --road extremes   # decision 12's roads (8 Oct): ambient,
                                            # speed and housing capacity drawn too
    python check_roads.py --road wideair    # X2's (11 Oct): the extremes roads at
                                            # 0-45 C and 80-101.3 kPa

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
results/training_roads.json (or training_roads_extremes.json, training_roads_
wideair.json), which make_page.py draws. On the extremes and wideair roads each row
also carries the ambient, the speed range and the housing-capacity scale the road
drew, and on the wideair roads the air pressure.

PASS means every road keeps the neutral reward inside +-0.05 and its p95
tracking error inside the reward's tolerance band. It also prints how many
roads push the baseline past the trigger: training needs both kinds, roads
where protection is needed and roads where it only costs fuel.

Evaluation never uses these roads. evaluate.py scores the locked climb only.

THE PLANT IS NAMED (20 October 2026): the roads are the B58 Supra's, and the
committed results/training_roads*.json are its (PLANT_NAME). Another engine's
roads are a later step (check_roads.py --engine, writing results/<id>/).

    python check_roads.py --engine E --train-road R --roads FILE [--n 40] [--out FILE]
    python check_roads.py --engine E --train-road R --synthetic-seed N --out FILE

THE PER-ENGINE TABLE (31 October 2026, row 119; ORDER_TO_TRAINING.md step 7).
`--engine E` drives the neutral action on n roads of training road R as train.py
builds it (train.build_env; R is row 116's road, by train.py's name for it) and on
every road of decision 34's set, in E's own car (engine_gate.py), and prints this
table with E's own turbine knee, the shares of steps asking under E's torque
floor or over its deliverable torque (row 116), and the same PASS rule. It
writes results/ENGINE_GATES/<E>/check_roads_<R>.json, or --out; a SYNTHETIC
seed's run is a test of the code, and its --out is required and must lie
outside the repository. Without --engine this file is the B58's, as above, and
prints and writes what it did before --engine existed (no default engine,
CLAUDE.md mistake 1: the run without --engine names its plant in PLANT_NAME).
"""
import argparse
import collections
import json
import os
from concurrent.futures import ProcessPoolExecutor

os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np

import engines

HERE = os.path.dirname(os.path.abspath(__file__))
FIRST_SEED = 100
PLANT_NAME = "b58"
GATES_DIR = os.path.join("results", "ENGINE_GATES")      # the per-engine tables, one folder per engine


def drive(job):
    seed, road = job
    import engines
    from engine_env import ExtremesTrainingEnv, TerrainTrainingEnv, neutral_action
    plant = engines.get(PLANT_NAME)
    if road == "wideair":
        from wide_air import WideAirTrainingEnv as cls
    else:
        cls = ExtremesTrainingEnv if road == "extremes" else TerrainTrainingEnv
    env = cls(duration=900.0, dt=1.0, seed=seed, plant=plant)
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
    g, v = env.cycle["grade"], env.cycle["v_mps"]
    extra = {}
    if road in ("extremes", "wideair"):
        extra = dict(t_amb_c=float(env.cycle["t_amb"]) - 273.15,
                     p_kpa=float(env.cycle.get("p_baro", 101.3)),
                     floor_nm=float(env.floor_nm),
                     v_min_kmh=float(v[20:].min() * 3.6), v_max_kmh=float(v.max() * 3.6),
                     c_turb_scale=float(env.c_turb_scale),
                     v_kmh=[round(float(x) * 3.6, 1) for x in v[::5]])
    return dict(seed=seed, family=env.cycle["family"], **extra,
                grade_min=float(g.min()), grade_max=float(g.max()),
                peak_c=float(turb.max() - 273.15),
                above_pct=float(100.0 * (turb > plant.engine.damage.turb_knee_k).mean()),
                neutral_r=float(np.mean(rs)), p95_err=float(np.percentile(errs, 95)),
                grade=[round(float(x), 4) for x in g[::5]],
                elev_m=[round(float(x), 1) for x in env.cycle["elev_m"][::5]])


def main_engine(a, ap):
    """The per-engine table (the module docstring), for row 119's gate."""
    import engine_gate as G
    import epa_roads as ER
    if a.road is not None:
        ap.error("--road is the B58's table; with --engine the training road is --train-road")
    if not a.train_road:
        ap.error("--train-road is required with --engine: the training road row 116 names, as train.py calls it")
    if a.roads is None and a.synthetic_seed is None:
        ap.error("decision 34's roads: give --roads FILE (a roads record) or --synthetic-seed N")
    if a.synthetic_seed is not None and (a.out is None or not ER.outside_repo(a.out)):
        ap.error("a SYNTHETIC run writes only outside the repository: give --out outside it")
    out = a.out or os.path.join(HERE, GATES_DIR, a.engine, f"check_roads_{a.train_road}.json")
    plant = engines.get(a.engine)
    knee_c = float(plant.engine.damage.turb_knee_k) - 273.15
    train, d34, label = G.road_table(a.engine, train_road=a.train_road, roads_file=a.roads,
                                     synthetic_seed=a.synthetic_seed, n=a.n, first_seed=FIRST_SEED,
                                     jobs=a.jobs if a.jobs is not None else 18)
    print(f"PER-ENGINE ROADS (row 119): {a.engine} in its own car ({plant.id}); training road {a.train_road} "
          f"(train.build_env), seeds {FIRST_SEED}-{FIRST_SEED + a.n - 1}; decision 34's roads: {label}")
    if a.synthetic_seed is not None:
        print("SYNTHETIC: a test of this code, not row 119's gate (no roads_seed exists)")
    print(f"\n{'road':>9} {'family':<8}{'grade %':>15}{'peak C':>8}{f'>{knee_c:.0f} C':>8}{'neutral r':>11}"
          f"{'p95 err':>9}{'<floor':>8}{'>deliv':>8}")
    rows = [("seed", r.get("seed"), r) for r in train] + [("d34", r.get("k"), r) for r in d34]
    for kind, key, r in rows:
        tag = f"{key}" if kind == "seed" else f"d34 {key}"
        if "error" in r:
            print(f"{tag:>9} ERROR: {r['error']}")
            continue
        g_lo, g_hi = (r["grade_min"], r["grade_max"]) if kind == "seed" else (0.0, r["grade_max"])
        what = (r.get("family") or "-") if kind == "seed" else f"{r['climbs']} climbs"
        print(f"{tag:>9} {what:<8}{100 * g_lo:>6.1f} to"
              f"{100 * g_hi:>5.1f}{r['peak_c']:>8.0f}{100 * r['above_knee_s'] / r['steps']:>7.1f}%"
              f"{r['mean_r']:>+11.4f}{r['p95_err']:>9.3f}{100 * r['below_floor']:>7.1f}%"
              f"{100 * r['above_deliverable']:>7.1f}%"
              + (f"   {r['t_amb_c']:4.1f} C  {r['v_min_kmh']:3.0f}-{r['v_max_kmh']:3.0f} km/h"
                 if kind == "seed" else ""))
    good = [r for _, _, r in rows if "error" not in r]
    errors = [r for _, _, r in rows if "error" in r]
    ok = not errors and bool(good) and all(abs(r["mean_r"]) < G.NEUTRAL_BAND and r["p95_err"] < G.TRACK_TOL
                                           for r in good)
    if good:
        worst_r = max(good, key=lambda r: abs(r["mean_r"]))
        worst_e = max(good, key=lambda r: r["p95_err"])
        print(f"\nbaseline past {knee_c:.0f} C:  {sum(r['peak_c'] > knee_c for r in good)} of {len(good)} roads")
        print(f"worst neutral reward: {worst_r['mean_r']:+.4f}  (want |r| < {G.NEUTRAL_BAND})")
        print(f"worst p95 tracking:   {worst_e['p95_err']:.3f}  (tolerance band {G.TRACK_TOL})")
        print(f"steps under the torque floor: {100 * np.mean([r['below_floor'] for r in good]):.2f} % (worst "
              f"road {100 * max(r['below_floor'] for r in good):.2f} %); over the deliverable torque "
              f"{100 * np.mean([r['above_deliverable'] for r in good]):.2f} % (worst road "
              f"{100 * max(r['above_deliverable'] for r in good):.2f} %); reported, not judged (row 116)")
    if errors:
        print(f"\n{len(errors)} road(s) did not run: {errors[0]['error']}")
    print("\nPASS -- every road is one the baseline can drive." if ok else
          "\nFAIL -- some road asks for torque the baseline cannot deliver, or did not run. Do not train.")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(dict(engine=a.engine, plant=plant.id, train_road=a.train_road, roads=label,
                       synthetic=a.synthetic_seed is not None, first_seed=FIRST_SEED, n=a.n,
                       training=train, decision_34=d34, knee_c=knee_c, tolerance=G.TRACK_TOL,
                       neutral_band=G.NEUTRAL_BAND, passed=ok), fh)
    print(f"wrote {os.path.relpath(out, HERE) if not ER.outside_repo(out) else out}")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    # None so that --engine can refuse it; without --engine it is "terrain", as it always was
    ap.add_argument("--road", choices=("terrain", "extremes", "wideair"), default=None)
    ap.add_argument("--engine", choices=engines.known(), default=None,
                    help="ROW 119: this engine's table, in its own car (engine_gate.py). No default engine: "
                         "without it this file is the B58's")
    ap.add_argument("--train-road", help="with --engine: the training road, as train.py names it (row 116's)")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--roads", metavar="FILE", help="with --engine: decision 34's roads, a roads record")
    src.add_argument("--synthetic-seed", type=int, help="with --engine: decision 34's generator on a SYNTHETIC "
                                                        "seed, a test of the code (no roads_seed)")
    ap.add_argument("--out", help="with --engine: the JSON (default results/ENGINE_GATES/<engine>/"
                                  "check_roads_<road>.json)")
    ap.add_argument("--jobs", type=int, default=None, help="with --engine: processes (default 18, the B58 table's)")
    a = ap.parse_args()
    if a.engine is not None:
        raise SystemExit(main_engine(a, ap))
    if any(x is not None for x in (a.train_road, a.roads, a.synthetic_seed, a.out, a.jobs)):
        ap.error("--train-road, --roads, --synthetic-seed, --out and --jobs belong to the per-engine table: "
                 "give --engine")
    a.road = a.road or "terrain"
    from engine_env import TRACK_TOL

    with ProcessPoolExecutor(max_workers=min(18, a.n)) as ex:
        R = list(ex.map(drive, [(s, a.road) for s in range(FIRST_SEED, FIRST_SEED + a.n)]))

    print(f"{'seed':>5} {'road':<8}{'grade %':>15}{'peak C':>8}{'>850 C':>8}"
          f"{'neutral r':>11}{'p95 err':>9}")
    for r in R:
        print(f"{r['seed']:>5} {r['family']:<8}{100 * r['grade_min']:>6.1f} to{100 * r['grade_max']:>5.1f}"
              f"{r['peak_c']:>8.0f}{r['above_pct']:>7.1f}%{r['neutral_r']:>+11.4f}{r['p95_err']:>9.3f}"
              + (f"   {r['t_amb_c']:4.1f} C {r['p_kpa']:5.1f} kPa  {r['v_min_kmh']:3.0f}-"
                 f"{r['v_max_kmh']:3.0f} km/h  c_turb x{r['c_turb_scale']:.2f}"
                 if a.road in ("extremes", "wideair") else ""))

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

    out = os.path.join(HERE, "results", "training_roads.json" if a.road == "terrain"
                       else f"training_roads_{a.road}.json")
    with open(out, "w") as fh:
        json.dump(dict(road=a.road, roads=R, binding=binding, n=len(R),
                       worst_neutral_r=worst_r["neutral_r"], worst_p95_err=worst_e["p95_err"],
                       tolerance=TRACK_TOL, passed=ok), fh)
    print(f"wrote {os.path.relpath(out, HERE)}")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

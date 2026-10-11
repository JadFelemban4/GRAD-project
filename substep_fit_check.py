"""substep_fit_check.py -- the thermal fit, re-run with the plant's sub-stepping.

    python substep_fit_check.py     about 15 minutes -> results/substep_fit_check.json

A DIAGNOSTIC: it writes nothing the plant reads. Found 9 October 2026 (CLAUDE.md
mistake 25). Since 8 October thermal.ThermalNetwork splits every step into
sub-steps of at most thermal.DT_SUB_MAX (0.1 s), but the fit that derives the
block and oil constants (calibrate_thermal.simulate) still takes one
explicit-Euler step per 1 s sample. This script swaps a sub-stepped copy of
simulate() into calibrate_thermal for this process only, re-runs the same
search (same seeds and population), and then runs check_premise.py's baseline
ECU and current-grade on the locked climb under today's constants and under the
re-fitted ones, swapped into derived's in-memory cache.

What it prints, and what it does not decide: how far the constants and the
premise would move. Shipping a sub-stepped fit changes derived_sha, which
refuses every agent trained on the present constants, so it is a plant change
and goes with the next one (a new drive, or the next experiment's plant).
The first premise row must reproduce check_premise.py (848.1 and 449.6), or the
harness is wrong.
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "results", "substep_fit_check.json")

import calibrate_thermal as K  # noqa: E402
import derived  # noqa: E402
import thermal  # noqa: E402

N = int(round(1.0 / thermal.DT_SUB_MAX))          # sub-steps per 1 s sample


def _oil_rate(to, tb, i, d, P):
    q = d["fuel"][i] * 44.0e3
    r = d["rpm"][i] / 3000.0 if d["rpm"][i] > 400.0 else 0.0
    q_in = P["frac_fuel_to_oil"] * q + P["k_oil_rpm"] * r ** P["n_oil_rpm"]
    ua_amb = P["ua_oil_amb"] + P["ua_oil_ram"] * d["v"][i]
    return (q_in + P["ua_block_oil"] * (tb - to) - ua_amb * (to - d["amb"][i])) / P["c_oil"]


def _block_rate(tb, to, i, d, P):
    q = d["fuel"][i] * 44.0e3
    running = d["rpm"][i] > 400.0
    stat = np.clip((tb - P["t_stat_open"]) / P["t_stat_span"], 0.0, 1.0)
    fan = np.where(tb > 372.0, 1.0, np.where(tb > 367.0, 0.4, 0.0)) * running
    ua_rad = P["ua_rad_scale"] * stat * (K.UA_RAD_MIN + K.UA_RAD_RAM * d["v"][i] + K.UA_RAD_FAN * fan)
    return (P["frac_fuel_to_coolant"] * q - (ua_rad + P["ua_block_amb"]) * (tb - d["amb"][i])
            - P["ua_block_oil"] * (tb - to)) / P["c_block"]


def simulate_sub(d, P, mode):
    """calibrate_thermal.simulate with each 1 s sample split into N sub-steps,
    the sample's inputs held, as ThermalNetwork.step does."""
    n = len(np.atleast_1d(P["c_oil"] if "c_oil" in P else P["c_block"]))
    tb = np.full(n, d["ect"][0])
    to = np.full(n, d["oil"][0])
    se_b, se_o, nb, no = np.zeros(n), np.zeros(n), 0, 0
    h = 1.0 / N
    for i in range(len(d["fuel"])):
        for _ in range(N):
            tb_now = d["ect_filled"][i] if mode == "oil" else tb
            to_now = d["oil_filled"][i] if mode == "block" else to
            new_to = to + h * _oil_rate(to, tb_now, i, d, P) if mode in ("oil", "free") else to
            new_tb = tb + h * _block_rate(tb, to_now, i, d, P) if mode in ("block", "free") else tb
            to, tb = new_to, new_tb
        if mode != "oil" and np.isfinite(d["ect"][i]):
            se_b += (tb - d["ect"][i]) ** 2; nb += 1
        if mode != "block" and np.isfinite(d["oil"][i]):
            se_o += (to - d["oil"][i]) ** 2; no += 1
    rb = np.sqrt(se_b / nb) if nb else np.full(n, np.nan)
    ro = np.sqrt(se_o / no) if no else np.full(n, np.nan)
    return rb, ro, (np.array([]), np.array([]))


def premise(D, TH0, patch):
    """check_premise.py's baseline ECU and current-grade, constants swapped in."""
    import check_premise as CP
    D["thermal"] = dict(TH0)
    if patch:
        p = dict(patch)
        scale = p.pop("ua_rad_scale")
        D["thermal"].update(p)
        D["thermal"]["ua_rad_min"] = K.UA_RAD_MIN * scale
        D["thermal"]["ua_rad_ram"] = K.UA_RAD_RAM * scale
        D["thermal"]["ua_rad_fan"] = K.UA_RAD_FAN * scale
    b, g = CP.rollout(CP.p_neutral), CP.rollout(CP.p_grade_now)
    return dict(baseline=b["damage"], current_grade=g["damage"], cut=100.0 * (1.0 - g["damage"] / b["damage"]))


def main():
    t0 = time.time()
    D = derived._load()
    TH0 = dict(D["thermal"])
    cur = {k: TH0[k] for k in TH0 if not k.startswith("_") and not k.startswith("ua_rad_")}
    cur["ua_rad_scale"] = TH0["_ua_rad_scale"]
    names, _ = K.usable_drives()
    drives = [d for d in (K.load_drive(s) for s in names) if d is not None]
    one = K.one(cur)
    free_1s = [K.simulate(d, one, "free") for d in drives]
    free_sub = [simulate_sub(d, one, "free") for d in drives]
    print(f"today's constants, free-running over {len(drives)} drives, mean RMSE: "
          f"1 s steps coolant {np.mean([r[0][0] for r in free_1s]):.3f} K oil {np.mean([r[1][0] for r in free_1s]):.3f} K; "
          f"sub-stepped coolant {np.mean([r[0][0] for r in free_sub]):.3f} K oil {np.mean([r[1][0] for r in free_sub]):.3f} K",
          flush=True)
    real = K.simulate
    K.simulate = simulate_sub
    try:
        p, j_oil, j_blk = K.fit(drives)
    finally:
        K.simulate = real
    print(f"\n{'constant':24s} {'today (1 s steps)':>18s} {'sub-stepped fit':>16s} {'change':>9s}")
    for k in p:
        a, b = cur[k], p[k]
        print(f"{k:24s} {a:18.5g} {b:16.5g} {100 * (b / a - 1):+8.1f} %")
    print(f"fit RMSE, sub-stepped: oil {j_oil:.3f} K, coolant {j_blk:.3f} K "
          f"(today's fit: oil {TH0['_fit_oil_rmse_k']:.3f} K, coolant {TH0['_fit_coolant_rmse_k']:.3f} K)", flush=True)
    rows = dict(today=premise(D, TH0, None), substepped=premise(D, TH0, p))
    D["thermal"] = dict(TH0)
    print("\nthe locked climb (check_premise.py's policies):")
    for k, r in rows.items():
        print(f"  {k:12s} baseline {r['baseline']:7.1f}   current-grade {r['current_grade']:7.1f}   cut {r['cut']:6.2f} %")
    moved = dict(baseline=rows["substepped"]["baseline"] - rows["today"]["baseline"],
                 cut=rows["substepped"]["cut"] - rows["today"]["cut"])
    print(f"  moved: baseline {moved['baseline']:+.1f} damage units, current-grade's cut {moved['cut']:+.2f} points")
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(dict(n_sub=N, drives=names, today=cur, substepped=p,
                       fit_rmse_substepped=dict(oil=j_oil, coolant=j_blk),
                       fit_rmse_today=dict(oil=TH0["_fit_oil_rmse_k"], coolant=TH0["_fit_coolant_rmse_k"]),
                       premise=rows, moved=moved, seconds=round(time.time() - t0)), fh, indent=1)
        fh.write("\n")
    print(f"\nwrote {os.path.relpath(OUT, HERE)} ({round(time.time() - t0)} s). Nothing the plant reads was written.")


if __name__ == "__main__":
    main()

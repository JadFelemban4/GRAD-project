"""Dump per-second traces of the four check_premise policies to JSON.

Read-only: imports the repo's own env and the exact policies from
check_premise.py. Writes nothing into the repository.
"""
import json, sys, os
import numpy as np
# AUDIT.md L11: was a hard-coded absolute path from one
# machine, so these scripts ran for exactly one person.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine_env import SupervisoryTunerEnv, make_grade_climb, TURB_PROTECT_K
import check_premise as cp


def rollout(policy, use_preview=True, seed=0):
    env = SupervisoryTunerEnv(make_grade_climb(duration=720.0, dt=1.0), dt=1.0,
                              seed=seed, use_preview=use_preview)
    obs, _ = env.reset(seed=seed)
    tr = dict(t=[], turb=[], oil=[], block=[], dmg_cum=[], torque=[], torque_req=[],
              spark=[], lam=[], map=[], rpm=[], grade=[], fuel_cum=[], egt=[], ki=[])
    cum = 0.0
    while True:
        a = policy(env, obs)
        obs, r, term, trunc, info = env.step(a)
        s = env.ep
        tr["t"].append(round(env.k * 1.0, 1))
        tr["turb"].append(round(info["t_turb"] - 273.15, 1))
        tr["oil"].append(round(info["t_oil"] - 273.15, 1))
        tr["block"].append(round(env.thermal.t_block - 273.15, 1))
        tr["dmg_cum"].append(round(s["damage"], 2))
        tr["torque"].append(round(float(info.get("torque", 0.0)), 1))
        tr["torque_req"].append(round(float(env.torque_req), 1))
        tr["spark"].append(round(float(env.spark), 2))
        tr["lam"].append(round(float(env.lam), 3))
        tr["map"].append(round(float(env.map_kpa), 1))
        tr["rpm"].append(round(float(env.rpm), 0))
        tr["grade"].append(round(float(env.cycle["grade"][min(env.k, len(env.cycle["grade"])-1)]), 3))
        tr["fuel_cum"].append(round(s["fuel"], 1))
        tr["egt"].append(round(float(info["egt_c"]), 1))
        tr["ki"].append(round(float(info["ki"]), 3))
        if term or trunc:
            break
    s = info.get("episode_summary", env.ep)
    tr["summary"] = dict(fuel=round(s["fuel"], 1), damage=round(s["damage"], 1),
                         peak_turb=round(max(tr["turb"]), 1),
                         peak_oil=round(max(tr["oil"]), 1),
                         knock=s["knock_events"])
    return tr


if __name__ == "__main__":
    out = {"trigger_c": round(TURB_PROTECT_K - 273.15, 1),
           "trigger_k": TURB_PROTECT_K, "dt": 1.0}
    runs = [("baseline", cp.p_neutral, True),
            ("reactive", cp.p_reactive, True),
            ("predictive", cp.p_predictive, True),
            ("blinded", cp.p_predictive, False)]
    for name, pol, prev in runs:
        print("running", name, flush=True)
        out[name] = rollout(pol, use_preview=prev)
        print("  ", name, out[name]["summary"], flush=True)
    dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "traces.json")
    json.dump(out, open(dst, "w"), separators=(",", ":"), default=float)
    print("wrote", dst, os.path.getsize(dst), "bytes")

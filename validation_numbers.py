"""validation_numbers.py -- the numbers results/VALIDATION_PLAN.md is built on.

    python validation_numbers.py        prints three tables, writes results/validation_numbers.json

The plan (ASME V&V 20 for the comparisons, a risk-based standard for how
strict to be) needs three kinds of number before any label can be computed,
and none of them existed until 7 October 2026:

1. WHAT THE CAR'S CHANNELS CAN RESOLVE. The smallest step each logged channel
   takes in data/master_samples.csv. Resolution only: no sensor datasheet is
   available, so the true accuracy is unknown and no better than this.
2. HOW FAR A TEMPERATURE ERROR MOVES DAMAGE. The committed locked-climb traces
   (results/traces_130kmh.json) re-scored with one uniform offset on the
   turbine or the oil temperature, through engine_env.damage_rate itself, to
   find the offset that moves a policy's damage by the minimum effect of
   interest (50 damage units).
3. HOW FAR AN INPUT ERROR MOVES THE CLIMB. The locked climb run with the
   neutral action, which reproduces the baseline ECU (test_reward.py), and
   then with ONE offset at a time: a trim through the action (spark, lambda,
   the boost ceiling) or the ambient through the cycle. Scored as
   evaluate.run_episode scores, on frozen episode 1. Nothing in the plant,
   the reward or the twenty episodes is changed.

These are SENSITIVITIES of the model, not validation. They say how large a
model error would have to be to matter; whether the model's errors are that
large is what the comparisons against the car decide.
"""
import concurrent.futures as cf
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

MEI = 50.0                      # damage units, set 22 Sep (PREREGISTRATION_D2.md)
CHANNELS = ("spark", "oil_c", "ect_c", "t_amb", "air_gps", "lam")
OFFSETS = [
    ("none", {}),
    ("spark +0.75 deg", {"act": (0, +0.75)}),
    ("spark -0.75 deg", {"act": (0, -0.75)}),
    ("lambda +0.01", {"act": (1, +0.01)}),
    ("lambda -0.01", {"act": (1, -0.01)}),
    ("boost ceiling +3.4 kPa", {"act": (2, +3.4)}),
    ("ambient +1 K", {"t_amb": +1.0}),
    ("ambient +5 K", {"t_amb": +5.0}),
]


def resolution():
    """{channel: smallest step between distinct logged values}."""
    import pandas as pd
    m = pd.read_csv(os.path.join(HERE, "data", "master_samples.csv"), usecols=list(CHANNELS),
                    low_memory=False)
    out = {}
    for c in CHANNELS:
        v = np.sort(pd.to_numeric(m[c], errors="coerce").dropna().unique())
        steps = np.diff(v)
        out[c] = float(np.round(steps[steps > 1e-9].min(), 4))
    return out


def damage_bias():
    """For each policy in the committed climb traces: its damage, and the
    uniform turbine and oil offsets that move that damage by MEI units."""
    from engine_env import damage_rate
    with open(os.path.join(HERE, "results", "traces_130kmh.json"), encoding="utf-8") as fh:
        traces = json.load(fh)
    out = {}
    for name in ("baseline ECU", "current-grade"):
        tr = traces[name]
        dt = float(np.median(np.diff(tr["t"])))
        tt = np.asarray(tr["t_turb"], float) + 273.15          # the traces are in C
        to = np.asarray(tr["t_oil"], float) + 273.15
        ki = np.asarray(tr["ki"], float)

        def dmg(bt=0.0, bo=0.0):
            return dt * sum(damage_rate(a + bt, b + bo, k) for a, b, k in zip(tt, to, ki))

        base = dmg()
        assert abs(base - tr["dmg_cum"][-1]) < 0.05, "the re-score must equal the committed damage"
        row = {"damage": round(base, 1), "peak_turb_c": round(float(tt.max()) - 273.15, 1),
               "peak_oil_c": round(float(to.max()) - 273.15, 1)}
        for node, key in (("turbine", "bt"), ("oil", "bo")):
            for sign in (+1, -1):
                lo, hi = 0.0, 100.0
                for _ in range(50):
                    mid = 0.5 * (lo + hi)
                    if abs(dmg(**{key: sign * mid}) - base) < MEI:
                        lo = mid
                    else:
                        hi = mid
                # 100.0 means no offset within 100 K moves damage that far
                row[f"{node}_{'up' if sign > 0 else 'down'}_k"] = round(sign * lo, 1)
        out[name] = row
    return out


def _climb(spec):
    import engine_env as E
    import evaluate as V
    label, change = spec
    seed, weights = V.EPISODES[0]
    cycle = E.make_grade_climb(duration=V.DURATION, dt=V.DT,
                               t_amb=315.0 + change.get("t_amb", 0.0))
    env = E.SupervisoryTunerEnv(cycle, dt=V.DT, seed=seed, use_preview=True)
    env.reset(seed=seed)
    env.w = np.asarray(weights, dtype=np.float32)
    a = np.array(E.neutral_action(), dtype=np.float32)
    if "act" in change:
        i, delta = change["act"]
        phys = E.ACT_LO[i] + (a[i] + 1.0) * 0.5 * (E.ACT_HI[i] - E.ACT_LO[i]) + delta
        a[i] = 2.0 * (phys - E.ACT_LO[i]) / (E.ACT_HI[i] - E.ACT_LO[i]) - 1.0
    peak, thermal, maps = 0.0, 0.0, []
    while True:
        _, _, term, trunc, info = env.step(a)
        peak = max(peak, info["t_turb"])
        thermal += E.damage_rate(info["t_turb"], info["t_oil"]) * env.dt
        maps.append(float(env.map_kpa))
        if term or trunc:
            break
    s = info["episode_summary"]
    return label, {"peak_turb_c": round(peak - 273.15, 2), "damage": round(s["damage"], 1),
                   "damage_thermal": round(thermal, 1),
                   "map_climb_kpa": round(float(np.median(maps[200:])), 1)}


def climb_sensitivity():
    with cf.ProcessPoolExecutor(max_workers=len(OFFSETS)) as pool:
        return dict(pool.map(_climb, OFFSETS))


def main():
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    res = resolution()
    bias = damage_bias()
    sens = climb_sensitivity()

    print("1. smallest logged step per channel (resolution, not accuracy)")
    for c, v in res.items():
        print(f"   {c:10s} {v:g}")
    print(f"\n2. uniform temperature offset that moves a policy's damage by {MEI:.0f} units (locked climb)")
    for name, r in bias.items():
        print(f"   {name:14s} damage {r['damage']:7.1f}  peak turbine {r['peak_turb_c']:.1f} C  "
              f"peak oil {r['peak_oil_c']:.1f} C   turbine {r['turbine_up_k']:+.1f} / "
              f"{r['turbine_down_k']:+.1f} K   oil {r['oil_up_k']:+.1f} / {r['oil_down_k']:+.1f} K")
    print("   (an oil entry of 100 means no offset within 100 K moves damage that far)")
    ref = sens["none"]
    print("\n3. one input error on the locked climb, neutral action, frozen episode 1")
    print(f"   {'input error':24s} {'peak C':>8s} {'d peak K':>9s} {'damage':>8s} {'d damage':>9s} "
          f"{'MAP kPa':>8s}")
    for label, r in sens.items():
        print(f"   {label:24s} {r['peak_turb_c']:8.2f} {r['peak_turb_c'] - ref['peak_turb_c']:+9.2f} "
              f"{r['damage']:8.1f} {r['damage'] - ref['damage']:+9.1f} {r['map_climb_kpa']:8.1f}")

    out = {"mei": MEI, "resolution": res, "damage_bias": bias, "climb_sensitivity": sens}
    path = os.path.join(HERE, "results", "validation_numbers.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
        fh.write("\n")
    print(f"\nwrote {os.path.relpath(path, HERE)}")


if __name__ == "__main__":
    main()

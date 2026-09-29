"""compare_calibration.py -- the 28 September derivation, before against after.

    python compare_calibration.py      # ~2 min; writes results/calibration_comparison.json
    python make_figures.py             # draws figures 20-25 from it

Every comparison behind the 28 September change, computed from the data and the
simulator as they stand, so each figure can be regenerated:

  thermal   thermal.py's block and oil nodes FREE-RUNNING over whole drives
            (raw logs), with the constants assumed until 28 September and with
            the constants derived from the logs; per-drive RMSE, before, after,
            and HELD OUT (results/thermal_calibration.json, calibrate_thermal.py)
  boost     the car's full-throttle manifold pressure against engine speed
            (drive B, genuine readings only) beside what the modelled engine
            reaches at the ceiling -- with the 8 September formula and with the
            derived envelope; and the envelope bins against both curves
  torque    the kickdown table, as typed until 28 September and as derived
  rows      validate.py rows 8-11, before and after, against the car's bands

Two things here are RECORDS, not regenerable, and are labelled so: the premise
at each step of the change (measured once per step, in order, on 28 September --
each step needs the code as it stood at that step), and the oil-structure
comparison that chose the oil node's form (calibrate_thermal.py's docstring).
"""
import json
import os
import sys

os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "results", "calibration_comparison.json")

# The kickdown table exactly as typed in engine_env.Vehicle until 28 September.
TORQUE_BEFORE = ((1000, 237), (1200, 254), (1400, 271), (1600, 288), (1800, 306), (2000, 323),
                 (2200, 341), (2400, 358), (2600, 375), (2800, 391), (3000, 407), (3200, 422),
                 (3400, 436), (3600, 449), (3800, 458), (4000, 466), (4200, 470), (4400, 472),
                 (4600, 470), (4800, 467), (5000, 459), (5200, 447), (5400, 446), (5600, 444),
                 (5800, 442), (6000, 440), (6200, 438), (6400, 435), (6600, 434))
BOOST_BEFORE = dict(A=14.5023, B=6.4019, cap=2.6)

# validate.py rows 8-11 as the table stood at commit c628564 (28 Sep, before).
ROWS_BEFORE = {"Oil, sustained load (drive10, hottest 10 min)": 96.4,
               "Oil apparent time constant (identified)": 14.0,
               "Coolant, regulated (synthetic climb)": 94.5,
               "Coolant, whole drive (drive10, free-running)": 88.4}

# RECORD: check_premise.py after each step, in the order the steps were made.
# RETIRED-OK: the first rows are the premise BEFORE the derivation, on purpose.
PREMISE_STEPS = [
    dict(step="as committed (c628564)", baseline=951.9, reactive=671.1, current_grade=624.5,
         predictive=628.4, peak_turb=884, peak_oil=110, preview_vs_grade=-0.4),
    dict(step="1  thermal block + oil derived", baseline=926.9, reactive=647.4, current_grade=597.5,
         predictive=601.3, peak_turb=884, peak_oil=94, preview_vs_grade=-0.4),
    dict(step="2  + boost, spark, kickdown table derived", baseline=928.2, reactive=648.7,
         current_grade=599.3, predictive=603.3, peak_turb=884, peak_oil=94, preview_vs_grade=-0.4),
    dict(step="3  + ceiling = measured envelope, at ambient", baseline=927.3, reactive=647.5,
         current_grade=596.6, predictive=599.8, peak_turb=884, peak_oil=94, preview_vs_grade=-0.3),
    dict(step="4  + exhaust = air + fuel", baseline=1052.1, reactive=658.9, current_grade=587.5,
         predictive=590.3, peak_turb=889, peak_oil=94, preview_vs_grade=-0.3),
    dict(step="5  + enrichment dwell derived", baseline=1052.1, reactive=658.9, current_grade=587.5,
         predictive=590.3, peak_turb=889, peak_oil=94, preview_vs_grade=-0.3),
    dict(step="6  + air density from ambient", baseline=920.1, reactive=625.7, current_grade=520.5,
         predictive=523.5, peak_turb=883, peak_oil=94, preview_vs_grade=-0.3),
]

# RECORD: the oil node's structure, chosen with the block pinned to measured
# coolant, fitted on six drives, scored on drive10 HELD OUT (28 September).
OIL_STRUCTURES = [
    dict(structure="as shipped: 5 % of fuel, constant 60 W/K", drive10_rmse=7.55, note="free-running"),
    dict(structure="fuel share, constant cooling (refitted)", drive10_rmse=3.84, note="block pinned"),
    dict(structure="engine speed, constant cooling", drive10_rmse=3.09, note="block pinned"),
    dict(structure="fuel share, road-speed cooling", drive10_rmse=3.30, note="block pinned"),
    dict(structure="engine speed, road-speed cooling  (chosen)", drive10_rmse=2.78, note="block pinned"),
    dict(structure="engine speed + fuel, road-speed cooling", drive10_rmse=2.68, note="block pinned"),
    dict(structure="+ a separate oil-sensor lag", drive10_rmse=2.79, note="block pinned"),
]


def thermal():
    import calibrate_thermal as K
    import derived
    before = dict(K.shipped_params())
    th = derived.get("thermal")
    after = {k: th[k] for k in before if k in th}
    after["ua_rad_scale"] = th["_ua_rad_scale"]
    out = {}
    for src in ("drive10-20260918_233912.csv", "7475b5d7-20260908_142743.csv",
                "683640a0-20260907_070212.csv"):
        d = K.load_drive(src)
        _, _, (bb, bo) = K.simulate(d, K.one(before), "free")
        _, _, (ab, ao) = K.simulate(d, K.one(after), "free")
        k = 273.15
        step = 5
        out[src] = dict(t_min=(np.arange(len(bb)) / 60.0)[::step].round(2).tolist(),
                        car_coolant=(d["ect"] - k)[::step].round(2).tolist(),
                        car_oil=(d["oil"] - k)[::step].round(2).tolist(),
                        before_coolant=(bb - k)[::step].round(2).tolist(),
                        before_oil=(bo - k)[::step].round(2).tolist(),
                        after_coolant=(ab - k)[::step].round(2).tolist(),
                        after_oil=(ao - k)[::step].round(2).tolist())
    cal = json.load(open(os.path.join(HERE, "results", "thermal_calibration.json")))
    return dict(traces=out, per_drive=cal["per_drive"], before=before, after=after)


def _map_at_ceiling(rpms, before):
    """MAP the environment's load loop reaches at a 1000 Nm request, per rpm.
    `before` re-creates the 8 September ceiling: the formula, sampled finely,
    evaluated at the CHARGE temperature, as the environment did until then."""
    import plant
    import engine_env as E
    orig = plant.boost_ceiling_constants
    if before:
        m = np.linspace(0.0, 0.6, 601)
        pr = 1.0 + BOOST_BEFORE["A"] * m / (1.0 + BOOST_BEFORE["B"] * m)
        plant.boost_ceiling_constants = lambda: dict(envelope_flow=m.tolist(), envelope_pr=pr.tolist(),
                                                     pr_cap=BOOST_BEFORE["cap"])
    try:
        env = E.SupervisoryTunerEnv(E.make_grade_climb(duration=60.0, dt=1.0), dt=1.0, seed=0)
        env.reset(seed=0)
        iat = plant.charge_temperature(315.0, 365.0)
        if before:
            env.cycle["t_amb"] = iat
        out = []
        for r in rpms:
            ecu, st, mp, kn = E.BaselineECU(), {}, 150.0, False
            for _ in range(30):
                sp, lam, _ = ecu.step(r, mp, iat, 365.0, kn, 1.0)
                o, mp = env._track_torque(1000.0, r, iat, 365.0, sp, lam, 0.0, st)
                kn = o["ki"] > 1.0
            out.append(dict(rpm=r, map_kpa=float(mp), torque=float(o["torque"])))
        return out
    finally:
        plant.boost_ceiling_constants = orig


def boost():
    import derived
    import derive_params as D
    raw = pd.read_csv(os.path.join(HERE, "logs", "raw", "driveB_rollons-20260928_140513.csv"))
    c = {k.lower(): k for k in raw.columns}
    rpm = raw[c["engine speed"]].to_numpy()
    bst = raw[c["boost pressure"]].to_numpy()
    pa = raw[c["ambient pressure"]].to_numpy()
    thr = raw[c["target value for throttle valve angle, based on (lower) stop"]].to_numpy()
    air = raw[c["air mass flow"]].to_numpy()
    fresh = np.r_[True, np.diff(bst) != 0]
    sel = fresh & (thr >= 95) & (pa > 0) & (air < 1019.9)
    # 29 September 2026: engine speed is INTERPOLATED to the moment each boost
    # reading was taken, between its own genuine readings. Until then each boost
    # reading was paired with the last engine-speed reading, up to ~0.45 s old
    # while a pull is building (mistake 13b). It moves the points ~55 rpm and
    # leaves every per-band comparison within a few points of where it was.
    t = pd.to_numeric(raw[c["time"]], errors="coerce").to_numpy(dtype=float)
    fr = np.r_[True, np.diff(rpm) != 0]
    rpm_at = np.interp(t, t[fr], rpm[fr])
    car = dict(rpm=rpm_at[sel].round(0).tolist(), map_kpa=((bst[sel] + pa[sel]) * 6.894757).round(1).tolist(),
               rpm_shift_median=float(np.median(rpm_at[sel] - rpm[sel])))
    rpms = list(range(1400, 4201, 100))
    S = pd.read_csv(os.path.join(HERE, "data", "master_samples.csv"), low_memory=False)
    bins, _ = D.envelope_bins(S)
    bc = derived.get("boost_ceiling")
    return dict(car_wot=car, model_before=_map_at_ceiling(rpms, True),
                model_after=_map_at_ceiling(rpms, False),
                bins=[dict(flow=b[0], pr=b[1], rows=b[2], readings=b[3]) for b in bins],
                envelope_flow=bc["envelope_flow"], envelope_pr=bc["envelope_pr"],
                pr_cap=bc["pr_cap"], formula_before=BOOST_BEFORE,
                torque_before=[list(x) for x in TORQUE_BEFORE],
                torque_after=derived.get("deliverable_torque"))


def rows():
    import validate as V
    now, _ = V.full_rows()
    return [dict(name=r["name"], before=ROWS_BEFORE[r["name"]], after=float(r["value"]),
                 lo=float(r["lo"]), hi=float(r["hi"]), inside=bool(r["ok"]))
            for r in now if r["name"] in ROWS_BEFORE]


def main():
    out = dict(thermal=thermal(), boost=boost(), rows=rows(),
               premise_steps=PREMISE_STEPS, oil_structures=OIL_STRUCTURES,
               _records=("premise_steps and oil_structures are records of measurements made "
                         "once on 28 September 2026; everything else is computed on this run"))
    with open(OUT, "w") as fh:
        json.dump(out, fh)
    print(f"wrote {os.path.relpath(OUT, HERE)}")
    for r in out["rows"]:
        print(f"  {r['name'][:46]:<46} before {r['before']:6.1f}  after {r['after']:6.1f}  "
              f"band {r['lo']:g}-{r['hi']:g}  {'inside' if r['inside'] else 'OUTSIDE'}")


if __name__ == "__main__":
    main()

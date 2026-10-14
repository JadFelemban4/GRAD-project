"""car_spark_boost.py -- the car's spark under boost against the model's baseline.

    python car_spark_boost.py     prints the table, writes results/car_spark_boost.json
                                  and results/figures/car_spark_boost.png

WHY THIS COMPARISON COMES FIRST (results/VALIDATION_PLAN.md, section 6). On the
locked climb one logged step of spark, 0.75 deg, moves the turbine by about
5.8 K and the damage by about 100 units (validation_numbers.py), so spark at
the climb's operating point is the most sensitive input the model has. The
merge review (conflict.md section 3a) found the car's boosted spark 3-8 deg
BELOW what BaselineECU commands at the same conditions, from a script that was
never committed. This is that comparison, in the repository, with its counts.

THE METHOD
- Car: `Actual ignition angle` (data/master_samples.csv column `spark`). The
  logger reads one channel per row in turn and copies the rest forward, so only
  rows where the value CHANGES are counted as readings (AUDIT.md H4); a poll
  that returns the same value is missed, so the count is a lower bound.
- Model: what BaselineECU.step would command at that row's engine speed,
  manifold pressure, ambient and coolant, with no knock retard and no history:
  base_spark (the fitted part-load map, or the knock-limited surface in
  boost) plus the intake-temperature compensation at plant.charge_temperature.
- Rows: 2000-4000 rpm, manifold pressure 140-240 kPa, air-mass sensor not at
  its ceiling, ambient measured (not drive B's fallback).

WHAT IT CANNOT SEE
- The manifold pressure is inverted from measured air mass through the model
  (plant.map_from_airflow, in build_dataset.py); both pressure channels on this
  car read before the throttle.
- The engine speed and air mass beside a spark reading were read at their own,
  earlier moments: under a transient they can be seconds apart.
- It tests the baseline's SPARK SCHEDULE, not the knock model directly: the car
  may run less advance for reasons other than knock (torque management,
  catalyst, its own margins).
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
BINS = (140.0, 160.0, 180.0, 200.0, 240.0)
RPM = (2000.0, 4000.0)
CLIMB = dict(rpm=(2400.0, 3000.0), map=(165.0, 185.0))   # around 2706 rpm, 175 kPa
TURB_K_PER_DEG = 5.8 / 0.75                                # validation_numbers.py, section 3


def readings():
    m = pd.read_csv(os.path.join(HERE, "data", "master_samples.csv"), low_memory=False)
    m = m.sort_values(["source", "t"])
    prev = m.groupby("source")["spark"].shift()
    changed = m["spark"].notna() & (m["spark"] != prev)
    r = m[changed].copy()
    keep = (r.rpm.between(*RPM) & r.map_kpa.between(BINS[0], BINS[-1])
            & np.isfinite(r.t_amb) & np.isfinite(r.ect_c)
            & (r.maf_pinned.fillna(0) == 0) & (r.t_amb_assumed.fillna(0) == 0))
    return r[keep].copy(), int(changed.sum())


def model_spark(r):
    from engine_env import BaselineECU
    from plant import charge_temperature
    ecu = BaselineECU()
    out = []
    for rpm, mp, ta, ect in zip(r.rpm, r.map_kpa, r.t_amb, r.ect_c):
        iat = charge_temperature(ta + 273.15, ect + 273.15)
        s = ecu.base_spark(rpm, mp) + ecu.iat_compensation(iat)
        if ect + 273.15 < 340.0:
            s -= 5.0
        out.append(float(np.clip(s, ecu.SPARK_MIN, ecu.SPARK_MAX)))
    return np.array(out)


def summary(r):
    d = r.spark.to_numpy() - r.model.to_numpy()
    n = len(d)
    se = 1.2533 * d.std(ddof=1) / np.sqrt(n) if n > 1 else float("nan")   # s.e. of a median
    return dict(readings=n, drives=int(r.source.nunique()),
                car_median=round(float(r.spark.median()), 2),
                model_median=round(float(r.model.median()), 2),
                diff_median=round(float(np.median(d)), 2),
                diff_q1=round(float(np.percentile(d, 25)), 2), diff_q3=round(float(np.percentile(d, 75)), 2),
                diff_se=round(float(se), 2),
                ambient_median=round(float(r.t_amb.median()), 1))


def main():
    r, total = readings()
    r["model"] = model_spark(r)
    rows = {}
    for lo, hi in zip(BINS[:-1], BINS[1:]):
        b = r[(r.map_kpa >= lo) & (r.map_kpa < hi)]
        if len(b):
            rows[f"{lo:.0f}-{hi:.0f} kPa"] = summary(b)
    climb = r[r.rpm.between(*CLIMB["rpm"]) & r.map_kpa.between(*CLIMB["map"])]
    rows["the climb's cell, 2400-3000 rpm, 165-185 kPa"] = summary(climb) if len(climb) > 1 else dict(readings=len(climb))
    rows["all, 140-240 kPa"] = summary(r)

    print(f"genuine readings of Actual ignition angle in the dataset: {total}; "
          f"in the window (2000-4000 rpm, 140-240 kPa, MAF not pinned, ambient measured): {len(r)}\n")
    print(f"{'cell':46s} {'n':>3s} {'drives':>6s} {'car':>7s} {'model':>7s} {'car - model':>12s} "
          f"{'IQR':>15s} {'s.e.':>5s} {'ambient':>8s}")
    for name, s in rows.items():
        if s.get("readings", 0) < 2:
            print(f"{name:46s} {s.get('readings', 0):3d}   too few readings")
            continue
        print(f"{name:46s} {s['readings']:3d} {s['drives']:6d} {s['car_median']:+7.2f} {s['model_median']:+7.2f} "
              f"{s['diff_median']:+12.2f} [{s['diff_q1']:+6.2f},{s['diff_q3']:+6.2f}] {s['diff_se']:5.2f} "
              f"{s['ambient_median']:7.1f}C")
    a = rows["all, 140-240 kPa"]
    print(f"\nread at the climb, linearly: {a['diff_median']:+.2f} deg of spark is about "
          f"{-a['diff_median'] * TURB_K_PER_DEG:+.0f} K of turbine the model would be missing "
          f"(5.8 K per 0.75 deg, validation_numbers.py); R1 in VALIDATION_PLAN.md is 10 K")

    out = {"window": dict(rpm=RPM, map_kpa=(BINS[0], BINS[-1])), "genuine_total": total,
           "cells": rows, "readings": r[["source", "t", "rpm", "map_kpa", "t_amb", "ect_c",
                                         "spark", "model"]].round(3).to_dict("records")}
    path = os.path.join(HERE, "results", "car_spark_boost.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
        fh.write("\n")
    print(f"wrote {os.path.relpath(path, HERE)}")
    figure(r)


def figure(r):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.4))
    sc = a1.scatter(r.model, r.spark, c=r.map_kpa, cmap="viridis", s=26, edgecolor="none")
    lo = float(min(r.model.min(), r.spark.min())) - 1
    hi = float(max(r.model.max(), r.spark.max())) + 1
    a1.plot([lo, hi], [lo, hi], color="#7c8388", ls="--", lw=1, label="car = model")
    a1.set_xlabel("BaselineECU's commanded spark at the same conditions, deg BTDC")
    a1.set_ylabel("car, Actual ignition angle, deg BTDC")
    a1.set_title(f"Each genuine reading, 2000-4000 rpm, 140-240 kPa (n = {len(r)})", fontsize=10)
    a1.legend(fontsize=8, loc="upper left")
    fig.colorbar(sc, ax=a1, label="manifold pressure, kPa")
    d = r.spark - r.model
    a2.scatter(r.map_kpa, d, color="#2a78d6", s=22, edgecolor="none", label="car minus model, one reading")
    for lo_, hi_ in zip(BINS[:-1], BINS[1:]):
        b = d[(r.map_kpa >= lo_) & (r.map_kpa < hi_)]
        if len(b):
            a2.plot([lo_, hi_], [b.median()] * 2, color="#eb6834", lw=2.5)
    a2.plot([], [], color="#eb6834", lw=2.5, label="median per bin")
    a2.axhline(0, color="#7c8388", lw=1, ls="--")
    a2.axvspan(165, 185, color="#e4e7e3", zorder=0, label="the climb's pressure")
    a2.set_xlabel("manifold pressure, kPa (inverted from air mass)")
    a2.set_ylabel("car minus model, deg")
    a2.set_title("Where the car's spark sits against the model's", fontsize=10)
    a2.legend(fontsize=8)
    fig.tight_layout()
    path = os.path.join(HERE, "results", "figures", "car_spark_boost.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=130)
    print(f"wrote {os.path.relpath(path, HERE)}")


if __name__ == "__main__":
    main()

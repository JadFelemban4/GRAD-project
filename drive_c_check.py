"""drive_c_check.py -- did a drive C log cover what drive C needs? Judged BLIND.

    python drive_c_check.py <csv or folder> [<csv or folder> ...]

WHY THIS EXISTS (19 October 2026)
---------------------------------
Ghassan logged the first drive with drive C's six channels on the night of
18-19 October, before the draft decision rule in logs/DRIVE_PLAN.md was fixed.
The question was whether the logs are ENOUGH, or whether drive C must be driven
again. That can be answered without drive C's answer: this script never
subtracts the two ignition angles and never prints an angle's value, so the
rule can still be fixed before anyone looks at the retard (CLAUDE.md, Training
gate, item 6: "its decision rule written before the drive").

WHAT IT COUNTS, against the plan's own targets (logs/DRIVE_PLAN.md, drive C)
- Each channel's reading interval. The logger reads one channel per row in a
  fixed rotation (AUDIT.md H4), so a channel's readings are the rows of its
  turn, including the ones whose value did not change.
- Part C1: loaded segments at 2000-3500 rpm and 140 kPa or more (the plan:
  twenty or more, 20-30 s each); the readings of each angle in the climb's
  cell, 2400-3000 rpm and 165-185 kPa (the plan: hundreds; the dataset holds
  4), and in car_spark_boost.py's window (the dataset holds 31).
- Part C2: rises in air mass from a steady cruise in a held gear (the plan:
  twenty or more, from 1500-2500 rpm, held 5 s, a minute apart).
- The conditions: the clock (from the file name), coolant and ambient.

WHAT IT CANNOT SEE
- The gear. Drive C logs no road speed, so a held gear shows only as a steady
  engine speed, and a kickdown as a jump in it.
- The altitude. Drive C logs no ambient pressure.
- The manifold pressure is inverted from air mass through the model
  (plant.map_from_airflow, CLAUDE.md mistake 2), as build_dataset.py does.

READ-ONLY. It opens the CSVs and prints.
"""
import datetime as dt
import glob
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from car_spark_boost import BINS, CLIMB, RPM               # noqa: E402
from plant import charge_temperature, map_from_airflow     # noqa: E402

CHANNELS = {"rpm": "engine speed", "air": "air mass flow",
            "act": "actual ignition angle",
            "tgt": "target ignition angle from torque intervention",
            "ect": "coolant temperature", "amb": "ambient temperature"}
MAF_CEILING_KGH = 1019.9        # build_dataset.py (mistake 7)
WARM_C = 75.0                   # build_dataset.py's warm filter
C1_RPM = (2000.0, 3500.0)       # DRIVE_PLAN.md, part C1, step 2
C1_KPA = BINS[0]                # 140 kPa, the bottom of car_spark_boost.py's window
STEP_RISE = 1.5                 # the draft rule: "a rise of at least ~50 % between two readings"
CRUISE_S = 20.0                 # the draft rule: "its median over the 20 s before"
CRUISE_RPM_RANGE = 450.0        # chosen here: a held gear at a steady speed moves less than this
COLDEST_C = 19.0                # the coldest air in data/master_samples.csv (DRIVE_PLAN.md, 13 October)
KICKDOWN_RPM = 500.0            # chosen here: a rise this fast within 6 s is a gear change or a low gear


def load(path):
    df = pd.read_csv(path, encoding="utf-8-sig")
    cols = [c for c in df.columns if c != "Time"]
    low = {c.strip().lower(): c for c in cols}
    missing = [n for n in CHANNELS.values() if n not in low]
    if missing:
        raise SystemExit(f"{os.path.basename(path)}: not drive C's channel set, missing {missing}")
    n = len(cols)
    changed = df[cols].diff().fillna(0).to_numpy() != 0
    rows = np.arange(len(df))
    d = {"t": df["Time"].to_numpy(float)}
    for key, name in CHANNELS.items():
        v = pd.to_numeric(df[low[name]], errors="coerce").to_numpy(float)
        idx = np.nonzero(changed[:, cols.index(low[name])])[0]
        turn = int(np.bincount(idx % n, minlength=n).argmax()) if len(idx) else -1
        first = int(np.argmax(v != 0)) if (v != 0).any() else len(v)   # placeholder zeros (AUDIT.md M8)
        d[key] = v
        d[key + "_rows"] = rows[(rows % n == turn) & (rows >= first)]
    return d


def manifold_kpa(d, r):
    rpm, air, ect, amb = d["rpm"][r], d["air"][r], d["ect"][r], d["amb"][r]
    if not (rpm > 500 and 1 < air < MAF_CEILING_KGH and ect > WARM_C and amb > 0):
        return np.nan
    return map_from_airflow(air / 3.6, rpm, charge_temperature(amb + 273.15, ect + 273.15))


def runs(mask):
    edges = np.diff(np.concatenate([[0], mask.astype(int), [0]]))
    return list(zip(np.nonzero(edges == 1)[0], np.nonzero(edges == -1)[0] - 1))


def files_from(args):
    out = []
    for a in args:
        out += sorted(glob.glob(os.path.join(a, "*.csv"))) if os.path.isdir(a) else [a]
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    segs, steps, boosted, bursts, cold = [], [], [], [], 0
    cell, window = {"act": 0, "tgt": 0}, {"act": 0, "tgt": 0}
    for path in files_from(sys.argv[1:]):
        d = load(path)
        t = d["t"]
        name = os.path.basename(path)
        try:
            t0 = dt.datetime.strptime(name[:19], "%Y-%m-%d_%H-%M-%S")
        except ValueError:
            t0 = None
        clock = (lambda s: f"{t0 + dt.timedelta(seconds=float(s)):%H:%M:%S}") if t0 else (lambda s: f"{s:7.1f} s")
        print(f"{name}: {clock(t[0])} to {clock(t[-1])}, {(t[-1] - t[0]) / 60:.1f} min")
        if t[-1] - t[0] < 30:
            print("  under 30 s: a false start, skipped")
            continue
        gaps = np.diff(t[d["act_rows"]])
        amb, ect = d["amb"][d["amb_rows"]], d["ect"][d["ect_rows"]]
        ar = d["air_rows"]
        air, rpm_a = d["air"][ar], d["rpm"][ar]
        print(f"  each angle read every {np.median(gaps):.2f} s (median), p99 {np.percentile(gaps, 99):.2f} s;"
              f" ambient {amb.min():.1f} to {amb.max():.1f} C ({amb[0]:.1f} first, {amb[-1]:.1f} last); coolant {ect.min():.1f} to {ect.max():.1f} C;"
              f" engine speed up to {d['rpm'][d['rpm_rows']].max():.0f} rpm;"
              f" air mass at its ceiling {int((air >= MAF_CEILING_KGH).sum())} times")

        # part C1
        kpa = np.array([manifold_kpa(d, r) for r in ar])
        loaded = (kpa >= C1_KPA) & (rpm_a >= C1_RPM[0]) & (rpm_a <= C1_RPM[1])
        segs += [t[ar[b]] - t[ar[a]] + np.median(np.diff(t[ar])) for a, b in runs(loaded)]
        boosted += list(rpm_a[kpa >= C1_KPA])
        bursts += [t[ar[b]] - t[ar[a]] + np.median(np.diff(t[ar])) for a, b in runs(kpa >= C1_KPA)]
        cold += int((amb < COLDEST_C).sum())
        for ang in ("act", "tgt"):
            rr = d[ang + "_rows"]
            k = np.array([manifold_kpa(d, r) for r in rr])
            n = d["rpm"][rr]
            cell[ang] += int(((n >= CLIMB["rpm"][0]) & (n <= CLIMB["rpm"][1])
                         & (k >= CLIMB["map"][0]) & (k <= CLIMB["map"][1])).sum())
            window[ang] += int(((n >= RPM[0]) & (n <= RPM[1]) & (k >= BINS[0]) & (k <= BINS[-1])).sum())

        # part C2
        rr = d["rpm_rows"]
        tr, rpm = t[rr], d["rpm"][rr]
        ta, last = t[ar], -1e9
        for j in range(1, len(ar)):
            before = (tr >= ta[j - 1] - CRUISE_S) & (tr <= ta[j - 1])
            rb = rpm[before]
            if before.sum() < 15 or rb.min() < 1000 or np.ptp(rb) > CRUISE_RPM_RANGE:
                continue
            cruise = np.median(air[(ta >= ta[j - 1] - CRUISE_S) & (ta <= ta[j - 1])])
            if not (air[j] >= STEP_RISE * air[j - 1] and air[j] >= 1.6 * cruise
                    and air[j] - cruise >= 30 and ta[j] - last > 4):
                continue
            after = (ta >= ta[j]) & (ta <= ta[j] + 8)
            k = j
            while k + 1 < len(ar) and air[k + 1] >= 1.5 * cruise and ta[k + 1] - ta[j] < 30:
                k += 1
            jump = rpm[(tr >= ta[j]) & (tr <= ta[j] + 6)].max() - np.median(rb)
            steps.append(dict(log=name[11:19], at=clock(ta[j]), rpm=np.median(rb), cruise=cruise,
                              peak=air[after].max(), held=ta[k] - ta[j] + np.median(np.diff(ta)),
                              jump=jump, gap=ta[j] - last if last > -1e8 else np.nan))
            last = ta[j]

    segs, boosted = np.array(segs), np.array(boosted)
    print()
    print("PART C1, steady loaded segments (plan: twenty or more, 20-30 s each)")
    print(f"  segments at {C1_RPM[0]:.0f}-{C1_RPM[1]:.0f} rpm and {C1_KPA:.0f} kPa or more: {len(segs)},"
          f" of which 20 s or longer: {int((segs >= 20).sum())}; longest {segs.max() if len(segs) else 0:.1f} s")
    if len(boosted):
        print(f"  air-mass readings at {C1_KPA:.0f} kPa or more at any engine speed: {len(boosted)},"
              f" median {np.median(boosted):.0f} rpm, {int((boosted <= C1_RPM[1]).sum())} of them at 3500 rpm or less,"
              f" in {len(bursts)} bursts, the longest {max(bursts):.1f} s")
    print(f"  readings in the climb's cell, {CLIMB['rpm'][0]:.0f}-{CLIMB['rpm'][1]:.0f} rpm and"
          f" {CLIMB['map'][0]:.0f}-{CLIMB['map'][1]:.0f} kPa: actual angle {cell['act']}, target angle"
          f" {cell['tgt']} (plan: hundreds of each)")
    print(f"  readings in car_spark_boost.py's window, {RPM[0]:.0f}-{RPM[1]:.0f} rpm and"
          f" {BINS[0]:.0f}-{BINS[-1]:.0f} kPa: actual angle {window['act']}, target angle {window['tgt']}")
    print(f"  ambient readings below {COLDEST_C:.1f} C, the dataset's coldest: {cold}")
    print()
    print("PART C2, load steps from a steady cruise in a held gear (plan: twenty or more)")
    s = pd.DataFrame(steps)
    if s.empty:
        print("  none")
        return
    s["plan_like"] = (s.rpm.between(1500, 2500) & (s.held >= 4.5) & (s.jump < KICKDOWN_RPM)
                      & ~(s.gap < 60))
    print(s.round(1).to_string(index=False))
    print(f"  rises from a steady cruise: {len(s)}; as the plan drives them (1500-2500 rpm, held 5 s,"
          f" no jump of {KICKDOWN_RPM:.0f} rpm, a minute apart): {int(s.plan_like.sum())}")


if __name__ == "__main__":
    main()

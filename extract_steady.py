"""extract_steady.py — Phase B, step B2.

Finds the steady-state operating points in a BimmerLink CSV export and collapses
duplicates, so that what comes out is a table of DISTINCT operating points rather
than a count of windows.

    python extract_steady.py mylog.csv
    python extract_steady.py mylog.csv --out steady_points.csv

A window counts as steady when, over WINDOW_S seconds, vehicle speed varies by
less than SPEED_TOL and engine speed by less than RPM_TOL. Windows that land on
the same operating point are then merged, because ten windows at the same cruise
condition are one data point, not ten.
"""
import argparse
import csv
import sys

import numpy as np

WINDOW_S = 60.0
SPEED_TOL = 3.0        # km/h, peak-to-peak inside the window
RPM_TOL = 150.0        # rpm, peak-to-peak inside the window
MIN_SPEED = 5.0        # km/h, ignore stationary windows
DEDUPE_RPM = 100.0     # merge points closer than this in engine speed
DEDUPE_LOAD = 5.0      # ...and this in relative filling (%)

# Channels we try to carry through. Missing ones are skipped with a warning.
WANTED = [
    "Engine speed",
    "Vehicle speed",
    "Relative air filling",
    "Air mass flow",
    "Mass flow through throttle valve bank 1",
    "Intake manifold absolute pressure",
    "Boost pressure",
    "Ambient pressure",
    "Intake air temperature before throttle valve, measured",
    "Coolant temperature",
    "Engine radiator outlet temperature (coolant)",
    "Oil temperature",
    "Ambient temperature",
    "Throttle valve angle related to the lower stop",
    "Actual gear",
    "Lambda actual value",
    "Actual ignition angle",
    "Condition brake test switch actuated",
]


def load(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rdr = csv.reader(f)
        header = [h.strip() for h in next(rdr)]
        rows = list(rdr)
    idx = {h: i for i, h in enumerate(header)}
    if "Time" not in idx:
        sys.exit("No 'Time' column. Is this a BimmerLink export?")

    def col(name):
        i = idx[name]
        out = np.full(len(rows), np.nan)
        for k, r in enumerate(rows):
            if i < len(r):
                v = r[i].strip()
                if v:
                    try:
                        out[k] = float(v)
                    except ValueError:
                        pass
        return out

    present = [w for w in WANTED if w in idx]
    absent = [w for w in WANTED if w not in idx]
    return col("Time"), {w: col(w) for w in present}, present, absent


def find_windows(t, data):
    rate = len(t) / (t[-1] - t[0])
    w = max(4, int(round(WINDOW_S * rate)))
    v, n = data["Vehicle speed"], data["Engine speed"]
    hits, i = [], 0
    while i + w <= len(t):
        vs, ns = v[i:i + w], n[i:i + w]
        if (np.isfinite(vs).all() and np.isfinite(ns).all()
                and np.ptp(vs) < SPEED_TOL and np.ptp(ns) < RPM_TOL
                and vs.mean() > MIN_SPEED):
            hits.append({k: float(np.nanmean(a[i:i + w])) for k, a in data.items()})
            hits[-1]["t_start"] = float(t[i])
            hits[-1]["n_samples"] = w
            i += w                       # non-overlapping
        else:
            i += max(1, w // 12)
    return rate, w, hits


def dedupe(points):
    """Merge windows that are really the same operating point."""
    load_key = "Relative air filling"
    merged = []
    for p in points:
        for m in merged:
            same_rpm = abs(m["Engine speed"] - p["Engine speed"]) < DEDUPE_RPM
            if load_key in p and load_key in m:
                same_load = abs(m[load_key] - p[load_key]) < DEDUPE_LOAD
            else:
                same_load = abs(m["Vehicle speed"] - p["Vehicle speed"]) < 5.0
            if same_rpm and same_load:
                m["_n"] += 1
                for k in m:
                    if k not in ("_n", "t_start", "n_samples"):
                        m[k] = (m[k] * (m["_n"] - 1) + p[k]) / m["_n"]
                break
        else:
            q = dict(p)
            q["_n"] = 1
            merged.append(q)
    return merged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out", default="steady_points.csv")
    a = ap.parse_args()

    t, data, present, absent = load(a.csv)
    if absent:
        print(f"note: {len(absent)} expected channel(s) not in this log:")
        for x in absent:
            print(f"      - {x}")
        print()

    rate, w, raw = find_windows(t, data)
    pts = dedupe(raw)

    print(f"log        : {a.csv}")
    print(f"duration   : {(t[-1] - t[0]) / 60:.1f} min at {rate:.2f} Hz")
    print(f"window     : {WINDOW_S:.0f} s = {w} samples")
    print(f"windows    : {len(raw)} steady")
    print(f"DISTINCT   : {len(pts)} operating points after de-duplication\n")

    if len(pts) < 6:
        print("FEWER THAN 6 DISTINCT POINTS.")
        print("The drive was not varied enough, or not steady enough. Repeat it")
        print("on a quieter road, and make sure you change GEAR as well as speed —")
        print("same speed in a different gear is a different operating point.\n")

    cols = ["t_start", "Engine speed", "Vehicle speed", "Actual gear"]
    cols += [c for c in present if c not in cols]
    hdr = f"{'t[s]':>7} {'rpm':>7} {'km/h':>6} {'gear':>5} {'load%':>7} {'air':>7} {'lam':>6} {'spark':>7}"
    print(hdr)
    print("-" * len(hdr))
    for p in sorted(pts, key=lambda x: x["Engine speed"]):
        print(f"{p['t_start']:>7.0f} {p['Engine speed']:>7.0f} {p['Vehicle speed']:>6.1f} "
              f"{p.get('Actual gear', float('nan')):>5.0f} "
              f"{p.get('Relative air filling', float('nan')):>7.1f} "
              f"{p.get('Air mass flow', float('nan')):>7.1f} "
              f"{p.get('Lambda actual value', float('nan')):>6.3f} "
              f"{p.get('Actual ignition angle', float('nan')):>7.1f}")

    with open(a.out, "w", newline="") as f:
        wtr = csv.DictWriter(f, fieldnames=cols + ["_n"], extrasaction="ignore")
        wtr.writeheader()
        for p in pts:
            wtr.writerow(p)
    print(f"\nwrote {a.out}  ({len(pts)} rows) — this is the input to compare_log.py")


if __name__ == "__main__":
    main()

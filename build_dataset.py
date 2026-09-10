"""build_dataset.py — assembles every drive into one master dataset.

    python build_dataset.py logs/raw/*.csv

Writes three files into data/ and prints a summary. Re-run it whenever a new
drive arrives; it rebuilds from scratch, so the outputs are always the union of
whatever you pass in. Never edit the outputs by hand.

    data/manifest.csv        one row per drive — when, how long, what it covers
    data/master_points.csv   steady operating points, pooled, de-duplicated
    data/master_samples.csv  per-sample rows with derived physics columns

WHY THREE FILES

  manifest      is what Chapter 3 cites when it says how much data exists.
  master_points is what compare_log.py validates the cycle model against.
  master_samples is what the ECU calibration is fitted to — lambda and spark
                versus manifold pressure, and the compressor operating line.
                Sample-level, because calibration needs the scatter, not means.

DERIVED COLUMNS, AND WHY THEY ARE NOT JUST COPIED FROM THE LOG

  map_kpa        inverted from air mass flow, NOT read from the pressure channel.
                 The channel named "intake manifold absolute pressure" on this
                 vehicle is a pre-throttle sensor: it never drops below ~92 kPa,
                 even at idle where physics demands about 31. Using it gives 75%
                 error; inverting air mass gives 1.3%.
  corr_flow      compressor-corrected mass flow, kg/s. Inlet conditions are
                 AMBIENT, not the post-intercooler intake temperature.
  press_ratio    compressor pressure ratio, (ambient + boost) / ambient.
  stable         True when air mass and boost are both changing slowly. Channels
                 are sampled at slightly different instants, so during a
                 transient they pair up wrongly — raw data shows pressure ratio
                 2.5 at 0.04 kg/s, which is deep surge and did not happen.
                 Anything fitting a compressor curve must filter on this.
"""
import argparse
import csv
import glob
import os
import sys
from datetime import datetime

import numpy as np

np.seterr(divide="ignore", invalid="ignore")
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plant import map_from_airflow, corrected_flow      # noqa: E402

PSI_TO_KPA = 6.89476
KGH_TO_GPS = 1000.0 / 3600.0

# Channels we read if present. Missing ones become NaN rather than an error,
# because the channel set grew between drives.
CH = {
    "rpm":      "Engine speed",
    "v_kmh":    "Vehicle speed",
    "air_kgh":  "Air mass flow",
    "air2_kgh": "Mass flow through throttle valve bank 1",
    "air_comb": "Air mass flow participating in combustion",
    "load_pct": "Relative air filling",
    "map_raw":  "Intake manifold absolute pressure",
    "boost":    "Boost pressure",
    "p_amb":    "Ambient pressure",
    "t_amb":    "Ambient temperature",
    "iat_pre":  "Intake air temperature before throttle valve, measured",
    "iat_amb":  "Intake air temperature",
    "ect":      "Coolant temperature",
    "rad_out":  "Engine radiator outlet temperature (coolant)",
    "oil":      "Oil temperature",
    "tps":      "Throttle valve angle related to the lower stop",
    "gear":     "Actual gear",
    "lam":      "Lambda actual value",
    "spark":    "Actual ignition angle",
    "wg":       "Is position electrical wastegate (0: WG closed, 100 WG open)",
    "brake":    "Condition brake test switch actuated",
    # Added to the recording set on 8 Sep (afternoon), drive 7475b5d7.
    "spk_tgt":  "Target ignition angle from torque intervention",
    "oil_filt": "Oil temperature after filter",
    "bst_tgt":  "Boost pressure setpoint",
    "trq_whl":  "Coordinated target torque on the wheel",
}

# WINDOW_S = 60 s, and the choice is now justified by the drives rather than
# assumed. Checked 8 September against the DRIVE_1 card, which asked for
# three-minute holds:
#
#     22 steady holds of 60 s or more across the seven drives
#      6 steady holds of 180 s or more
#     median hold 55-130 s depending on the drive
#
# Asking for 180 s would throw away three quarters of the dataset. Public roads
# do not grant three uninterrupted minutes on demand, and that is a road
# limitation, not a driving mistake.
#
# WHAT A 60 s WINDOW DOES NOT SETTLE. Everything this dataset is actually
# fitted on -- air mass, lambda, spark, manifold pressure -- responds in
# milliseconds and is fully settled. The TURBINE HOUSING is not: its measured
# time constant is 48 s, so 60 s reaches only 1 - exp(-60/48) = 71 % of a
# thermal step, and 180 s would reach 98 %.
#
# This costs nothing today, because compare_log.py validates air and load, not
# turbine temperature. It would matter the moment someone tries to validate a
# thermal quantity "at the steady points". Do not do that without either the
# 180 s windows or a time-series comparison over the whole drive.
WINDOW_S, SPEED_TOL, RPM_TOL, MIN_SPEED = 60.0, 3.0, 150.0, 5.0

# A window is sized in samples but validated in seconds. SPAN_TOL is how far its
# real wall-clock duration may stray from WINDOW_S; MAX_HOLE_X is the largest
# gap it may contain, as a multiple of that drive's median sample interval.
# See steady_points() for the drive that made these necessary.
SPAN_TOL, MAX_HOLE_X = 0.20, 4.0
DEDUPE_RPM, DEDUPE_LOAD = 100.0, 5.0


def read_drive(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rdr = csv.reader(f)
        header = [h.strip() for h in next(rdr)]
        rows = list(rdr)
    idx = {h: i for i, h in enumerate(header)}
    if "Time" not in idx:
        return None
    n = len(rows)

    def col(name):
        i = idx.get(name)
        out = np.full(n, np.nan)
        if i is None:
            return out
        for k, r in enumerate(rows):
            if i < len(r) and r[i].strip():
                try:
                    out[k] = float(r[i])
                except ValueError:
                    pass
        return out

    d = {k: col(v) for k, v in CH.items()}
    d["t"] = col("Time")
    d["_file"] = os.path.basename(path)
    d["_n"] = n
    d["_present"] = {k: (CH[k] in idx) for k in CH}
    return d


def derive(d):
    """Add the physics columns. Everything here is computed, never copied."""
    air_gps = d["air_kgh"] * KGH_TO_GPS
    iat_k = d["iat_pre"] + 273.15
    d["air_gps"] = air_gps

    mp = np.full(len(air_gps), np.nan)
    ok = np.isfinite(air_gps) & np.isfinite(iat_k) & (d["rpm"] > 500) & (air_gps > 1)
    for i in np.nonzero(ok)[0]:
        mp[i] = map_from_airflow(air_gps[i], d["rpm"][i], iat_k[i])
    d["map_kpa"] = mp

    # compressor inlet is AMBIENT, not the post-intercooler temperature
    t01 = d["iat_amb"].copy()
    t01 = np.where(np.isfinite(t01), t01, d["t_amb"]) + 273.15
    p01 = d["p_amb"] * PSI_TO_KPA * 0.98
    d["corr_flow"] = corrected_flow(air_gps, t01, p01)
    d["press_ratio"] = ((d["p_amb"] + d["boost"]) * PSI_TO_KPA) / p01

    # THE MAF CHANNEL SATURATES. "Air mass flow" tops out at exactly 1020.0 kg/h
    # on five separate drives -- 3aca2ec1, 670063b2, 683640a0, cb67b01f and
    # 7475b5d7 -- 517 samples in all. That is a sensor range limit, not a
    # coincidence: on the same samples "Air mass flow participating in
    # combustion" reads higher, median ratio 1.095.
    #
    # A pinned sample reports less air than the engine is actually breathing, so
    # it corrupts anything fitted on air mass: manifold pressure inverted from it
    # comes out too low, and the compressor pressure ratio at that flow comes out
    # too high. Those are the samples at the very top of the boost ceiling, which
    # is exactly where the fit is most exposed.
    #
    # They are flagged, not repaired. The combustion-air channel is the ECU's
    # modelled trapped charge, a different quantity (median ratio 1.095 over the
    # 517 pinned samples; 1.163 before the eighth drive), and splicing two
    # definitions into one series would put a
    # step in the middle of the curve. Everything fitted on air mass uses
    # `stable`, which excludes them; `maf_pinned` is kept so the thesis can say
    # how much of the envelope is unmeasured and why.
    d["maf_pinned"] = d["air_kgh"] >= 1019.9

    dt = np.gradient(d["t"])
    with np.errstate(invalid="ignore", divide="ignore"):
        d_air = np.abs(np.gradient(d["air_kgh"]) / dt)
        d_bst = np.abs(np.gradient(d["boost"]) / dt)
    d["stable"] = (d_air < 40) & (d_bst < 0.6) & (~d["maf_pinned"])
    return d


def steady_points(d):
    """Find windows where speed and engine speed both hold still.

    THE WINDOW IS SIZED IN SAMPLES BUT MUST BE CHECKED IN SECONDS.

    `w` comes from the drive's AVERAGE sample rate, so on a drive whose rate is
    not constant a "60 second window" is nothing of the sort. Measured on the
    seven drives before this check existed:

        3aca2ec1   windows spanned 42.8 - 68.7 s
        cb67b01f   windows spanned 65.6 - 65.8 s
        fb988991   windows spanned 46.0 - 73.7 s, with an internal gap of 3.18 s

    The last one matters most, and the cause is not a mistake. `fb988991` and
    `f51686d7` are RECONNAISSANCE runs, logged with all 655 channels selected on
    purpose to establish which parameters this car publishes. At that channel
    count the logger cannot keep up: 196 gaps larger than three times the median
    interval, 222 of its 980 seconds missing entirely. **Nearly a quarter of
    that drive was never recorded.** A window straddling a five-second hole is
    not a steady observation -- the samples either side of it were steady, and
    what happened in between is unknown.

    A census log is supposed to be unusable as driving data; that is the trade
    it makes, and it paid for itself. See logs/CHANNEL_CENSUS.md for what those
    two recordings established, including the fact that the radiator can never
    be identified on this vehicle because every water-pump channel reads zero.

    That drive is also the one that produced the fuel-cut point with a 124 %
    residual, and the one whose load channel disagrees with its own airflow.
    Those are all the same root cause.

    So a candidate window is now rejected unless it really covers WINDOW_S
    seconds and contains no hole. Both tolerances are deliberately loose: the
    point is to exclude the pathological, not to demand a metronome.
    """
    t = d["t"]
    span = t[-1] - t[0]
    if span <= 0:
        return []
    rate = len(t) / span
    w = max(4, int(round(WINDOW_S * rate)))
    dt_med = float(np.median(np.diff(t))) if len(t) > 1 else 0.0
    v, n = d["v_kmh"], d["rpm"]
    hits, i = [], 0
    rejected_span = rejected_gap = 0
    while i + w <= len(t):
        vs, ns = v[i:i + w], n[i:i + w]
        if (np.isfinite(vs).all() and np.isfinite(ns).all()
                and np.ptp(vs) < SPEED_TOL and np.ptp(ns) < RPM_TOL
                and vs.mean() > MIN_SPEED):
            wall = t[i + w - 1] - t[i]
            hole = float(np.max(np.diff(t[i:i + w]))) if w > 1 else 0.0
            if not (WINDOW_S * (1 - SPAN_TOL) <= wall <= WINDOW_S * (1 + SPAN_TOL)):
                rejected_span += 1
                i += max(1, w // 12)
                continue
            if dt_med > 0 and hole > MAX_HOLE_X * dt_med:
                rejected_gap += 1
                i += max(1, w // 12)
                continue
            row = {k: float(np.nanmean(d[k][i:i + w]))
                   for k in list(CH) + ["air_gps", "map_kpa", "corr_flow", "press_ratio"]}
            row["t_start"] = float(t[i])
            row["t_span"] = wall
            row["max_gap"] = hole
            row["source"] = d["_file"]
            hits.append(row)
            i += w
        else:
            i += max(1, w // 12)
    if rejected_span or rejected_gap:
        print(f"  {d['_file'][:8]}: rejected {rejected_span} window(s) for wall-clock "
              f"span and {rejected_gap} for containing a logger gap")
    return hits


def dedupe(points):
    merged = []
    for p in points:
        for m in merged:
            same_rpm = abs(m["rpm"] - p["rpm"]) < DEDUPE_RPM
            same_load = abs(m["load_pct"] - p["load_pct"]) < DEDUPE_LOAD
            if same_rpm and same_load:
                m["_merged"] += 1
                k = m["_merged"]
                for key, val in p.items():
                    if isinstance(val, float) and key in m and isinstance(m[key], float):
                        m[key] = (m[key] * (k - 1) + val) / k
                break
        else:
            q = dict(p)
            q["_merged"] = 1
            merged.append(q)
    return merged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csvs", nargs="+")
    ap.add_argument("--out", default="data")
    ap.add_argument("--sample-every", type=int, default=1,
                    help="keep every Nth sample in master_samples.csv")
    a = ap.parse_args()

    paths = []
    for pat in a.csvs:
        paths.extend(sorted(glob.glob(pat)) or [pat])
    os.makedirs(a.out, exist_ok=True)

    manifest, all_points, sample_rows = [], [], []

    for path in paths:
        if not os.path.exists(path):
            print(f"  skip (not found): {path}")
            continue
        d = read_drive(path)
        if d is None:
            print(f"  skip (no Time column): {path}")
            continue
        d = derive(d)
        t = d["t"]
        span = float(t[-1] - t[0]) if len(t) > 1 else 0.0
        warm = np.isfinite(d["ect"]) & (d["ect"] > 75)
        run = d["rpm"] > 500

        pts = steady_points(d)
        all_points.extend(pts)

        manifest.append({
            "file": d["_file"],
            "samples": d["_n"],
            "duration_s": round(span, 1),
            "duration_min": round(span / 60, 2),
            "rate_hz": round(len(t) / span, 2) if span > 0 else 0,
            "channels_present": sum(d["_present"].values()),
            "steady_windows": len(pts),
            "max_rpm": round(float(np.nanmax(d["rpm"])), 0),
            "max_speed_kmh": round(float(np.nanmax(d["v_kmh"])), 0),
            "max_load_pct": round(float(np.nanmax(d["load_pct"])), 1),
            "max_map_kpa": round(float(np.nanmax(d["map_kpa"])), 0) if np.isfinite(d["map_kpa"]).any() else "",
            "min_lambda": round(float(np.nanmin(np.where((d["lam"] > 0.5) & (d["lam"] < 1.3), d["lam"], np.nan))), 3)
                           if np.isfinite(d["lam"]).any() else "",
            "warm_samples": int(np.sum(warm & run)),
        })

        keep = warm & run & np.isfinite(d["map_kpa"])
        for i in np.nonzero(keep)[0][::a.sample_every]:
            sample_rows.append({
                "source": d["_file"], "t": round(float(t[i]), 3),
                "rpm": d["rpm"][i], "map_kpa": round(float(d["map_kpa"][i]), 2),
                # v_kmh and t_amb are here because thermal.py cannot be validated
                # without them: radiator UA scales with road speed and every heat
                # flow is driven by the gap to ambient.
                "v_kmh": d["v_kmh"][i], "t_amb": d["t_amb"][i],
                "load_pct": d["load_pct"][i], "air_gps": round(float(d["air_gps"][i]), 2),
                "lam": d["lam"][i], "spark": d["spark"][i],
                "iat_pre_c": d["iat_pre"][i], "ect_c": d["ect"][i], "oil_c": d["oil"][i],
                "rad_out_c": d["rad_out"][i], "tps": d["tps"][i], "gear": d["gear"][i],
                "wastegate": d["wg"][i],
                "spark_tgt": d["spk_tgt"][i], "oil_filt_c": d["oil_filt"][i],
                "boost_tgt": d["bst_tgt"][i], "trq_wheel": d["trq_whl"][i],
                "corr_flow": round(float(d["corr_flow"][i]), 5),
                "press_ratio": round(float(d["press_ratio"][i]), 4),
                "stable": int(bool(d["stable"][i])),
                "maf_pinned": int(bool(d["maf_pinned"][i])),
            })

    # Sanity floor. A "steady point" at 15 kPa or 600 rpm is an idle or overrun
    # window that slipped the speed filter, not an operating point worth
    # validating a combustion model against.
    before = len(all_points)
    all_points = [p for p in all_points
                  if np.isfinite(p.get("map_kpa", np.nan)) and p["map_kpa"] >= 25
                  and p["rpm"] >= 800 and p["v_kmh"] >= 20]
    if before != len(all_points):
        print(f"  dropped {before - len(all_points)} window(s) below the sanity floor "
              f"(map < 25 kPa, rpm < 800, or speed < 20 km/h)")

    # Combustion filter. The cycle model assumes the cylinder fires. On overrun
    # the ECU cuts fuel: spark goes deeply negative and the lambda sensor reads
    # air (this vehicle logs 16.0). Those windows are real vehicle behaviour and
    # they stay in master_samples, but they are not operating points a
    # combustion model can be scored against, so they leave master_points.
    before = len(all_points)
    all_points = [p for p in all_points
                  if float(p.get("spark", 0.0)) > 0.0
                  and 0.70 <= float(p.get("lam", 1.0)) <= 1.10]
    if before != len(all_points):
        print(f"  dropped {before - len(all_points)} window(s) with fuel cut "
              f"(negative spark, or lambda outside 0.70-1.10)")
    points = dedupe(all_points)

    def write(name, rows, cols=None):
        p = os.path.join(a.out, name)
        if not rows:
            print(f"  {name}: nothing to write")
            return
        cols = cols or list(rows[0].keys())
        with open(p, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"  {name:22s} {len(rows):6d} rows")

    print(f"\nMASTER DATASET  ({datetime.now():%Y-%m-%d %H:%M})\n")
    write("manifest.csv", manifest)
    write("master_points.csv", points)
    write("master_samples.csv", sample_rows)

    # ASCII only. This header used to print a Greek lambda, which is not in
    # cp1252, so on a Windows console the script raised UnicodeEncodeError
    # HERE -- after all three CSVs were already written. The data was fine and
    # the traceback said otherwise, which is the worst combination. Anyone
    # following the "when a new drive arrives" routine on Windows saw a crash
    # and a non-zero exit on a run that had actually succeeded.
    print(f"\n{'drive':44s} {'min':>6} {'Hz':>6} {'ch':>4} {'pts':>5} {'maxMAP':>7} {'minlam':>7}")
    print("-" * 84)
    for m in manifest:
        print(f"{m['file'][:44]:44s} {m['duration_min']:6.1f} {m['rate_hz']:6.2f} "
              f"{m['channels_present']:4d} {m['steady_windows']:5d} "
              f"{str(m['max_map_kpa']):>7} {str(m['min_lambda']):>7}")
    print("-" * 84)
    tot = sum(m["duration_min"] for m in manifest)
    print(f"{'TOTAL':44s} {tot:6.1f} min across {len(manifest)} drives, "
          f"{len(points)} distinct operating points\n")

    if points:
        mp = np.array([p["map_kpa"] for p in points if np.isfinite(p["map_kpa"])])
        if len(mp):
            print(f"operating points span {mp.min():.0f} - {mp.max():.0f} kPa manifold pressure")
    cf = np.array([r["corr_flow"] for r in sample_rows if r["stable"]])
    if len(cf):
        gap = [(lo, lo + 0.03) for lo in np.arange(0, 0.33, 0.03)
               if np.sum((cf >= lo) & (cf < lo + 0.03)) < 15]
        if gap:
            print("compressor flow bins still EMPTY (kg/s):",
                  ", ".join(f"{a_:.2f}-{b:.2f}" for a_, b in gap))
        else:
            print("compressor operating line: every flow bin populated")


if __name__ == "__main__":
    main()

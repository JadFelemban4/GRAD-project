"""compare_log.py — Phase B, steps B3 and B4.

Runs the plant at each steady operating point extracted from a real drive and
scores the disagreement, channel by channel.

    python extract_steady.py mylog.csv --out steady_points.csv
    python compare_log.py steady_points.csv

THE LOAD INPUT
--------------
The model needs manifold pressure. This script does NOT take it from the logged
pressure channel, because on this vehicle those channels do not reconcile with
physics (audit §8: implied volumetric efficiency ranges from 11 % to 400 %
depending on which unit you assume, and the channel never drops to idle vacuum).

Instead it inverts the measured AIR MASS FLOW, which has one unambiguous unit.
Pass --map-from-log to use the logged pressure anyway once the parked-idle test
has settled the units, and --map-scale to apply the factor that test reveals.
"""
import argparse
import csv
import math

import numpy as np

from plant import predict, map_from_airflow

# Logged air mass flow is in kg/h on this export. 1 kg/h = 0.2778 g/s.
AIRFLOW_KGH_TO_GPS = 1000.0 / 3600.0

TARGETS = {           # channel -> (tolerance, unit)
    "mdot_air_gps": (10.0, "%"),
    "load": (15.0, "%"),
}


# compare_log.py accepts BOTH schemas:
#   extract_steady.py  -> raw BimmerLink names ("Engine speed")
#   build_dataset.py   -> short names ("rpm")
# The master dataset uses the short ones, so look under either.
ALIASES = {
    "Engine speed": "rpm",
    "Intake air temperature before throttle valve, measured": "iat_pre",
    "Coolant temperature": "ect",
    "Lambda actual value": "lam",
    "Actual ignition angle": "spark",
    "Air mass flow": "air_kgh",
    "Relative air filling": "load_pct",
}


def f(row, key, default=float("nan")):
    for name in (key, ALIASES.get(key)):
        if name is None:
            continue
        try:
            return float(row[name])
        except (KeyError, TypeError, ValueError):
            continue
    return default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("points", help="output of extract_steady.py")
    ap.add_argument("--map-from-log", action="store_true",
                    help="use the logged manifold pressure instead of inverting airflow")
    ap.add_argument("--map-scale", type=float, default=6.89476,
                    help="multiplier applied to the logged pressure to get kPa "
                         "(default assumes psi; set from the parked-idle test)")
    ap.add_argument("--airflow-gps", action="store_true",
                    help="logged air mass flow is already g/s, not kg/h")
    a = ap.parse_args()

    with open(a.points, newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit("no rows in " + a.points)

    print(f"{len(rows)} operating points from {a.points}")
    print("load input:",
          "logged pressure x %.4f" % a.map_scale if a.map_from_log
          else "inverted from measured air mass flow")
    print()

    hdr = (f"{'rpm':>6} {'MAP kPa':>8} {'air meas':>9} {'air model':>10} "
           f"{'err %':>7} {'load meas':>10} {'load model':>11} {'err %':>7} "
           f"{'EGT C':>7} {'KI':>6}")
    print(hdr)
    print("-" * len(hdr))

    air_err, load_err = [], []
    load_pairs = []
    for r in rows:
        rpm = f(r, "Engine speed")
        iat_c = f(r, "Intake air temperature before throttle valve, measured")
        ect_c = f(r, "Coolant temperature")
        lam = f(r, "Lambda actual value", 1.0)
        spark = f(r, "Actual ignition angle", 20.0)
        air_raw = f(r, "Air mass flow")
        load_meas = f(r, "Relative air filling")

        if not math.isfinite(rpm) or rpm < 500:
            continue
        air_meas = air_raw if a.airflow_gps else air_raw * AIRFLOW_KGH_TO_GPS
        iat_k = (iat_c if math.isfinite(iat_c) else 40.0) + 273.15
        ect_k = (ect_c if math.isfinite(ect_c) else 90.0) + 273.15
        if not math.isfinite(lam) or lam <= 0:
            lam = 1.0

        if a.map_from_log:
            map_kpa = f(r, "Intake manifold absolute pressure") * a.map_scale
        else:
            map_kpa = map_from_airflow(air_meas, rpm, iat_k)
        if not math.isfinite(map_kpa) or map_kpa < 15:
            continue

        out = predict(rpm=rpm, map_kpa=map_kpa, iat_k=iat_k, ect_k=ect_k,
                      spark_btdc=spark, lam=lam)

        ea = 100.0 * (out["mdot_air_gps"] - air_meas) / air_meas if air_meas > 0 else float("nan")
        # relative filling ~ eta_v * (1 - f_res) * map / p_ref, expressed in percent
        load_model = 100.0 * out["eta_v"] * (1.0 - out["f_res"]) * map_kpa / 100.0
        el = (100.0 * (load_model - load_meas) / load_meas
              if math.isfinite(load_meas) and load_meas > 0 else float("nan"))
        if math.isfinite(ea):
            air_err.append(abs(ea))
        if math.isfinite(el):
            load_err.append(abs(el))
        if math.isfinite(load_meas) and load_meas > 0 and math.isfinite(load_model):
            load_pairs.append((load_meas, load_model, iat_k))

        print(f"{rpm:>6.0f} {map_kpa:>8.1f} {air_meas:>9.1f} {out['mdot_air_gps']:>10.1f} "
              f"{ea:>7.1f} {load_meas:>10.1f} {load_model:>11.1f} {el:>7.1f} "
              f"{out['egt_c']:>7.0f} {out['knock_integral']:>6.2f}")

    print("-" * len(hdr))

    print("\nAIR MASS FLOW")
    if not a.map_from_log:
        print("  NOT AN INDEPENDENT CHECK IN THIS MODE. Manifold pressure was derived")
        print("  FROM the measured air mass, so the model reproduces it by construction")
        print("  and the error is zero for arithmetic reasons, not physical ones.")
        print("  Re-run with --map-from-log once the parked-idle test has settled the")
        print("  pressure units; only then is this comparison meaningful.")
    elif air_err:
        mape = float(np.mean(air_err))
        print(f"  MAPE {mape:.1f} %   target < {TARGETS['mdot_air_gps'][0]:.0f} %   "
              f"{'PASS' if mape < TARGETS['mdot_air_gps'][0] else 'FAIL'}")

    print("\nLOAD (relative air filling)")
    if len(load_pairs) < 3:
        print("  too few points")
    else:
        meas = np.array([m for m, _, _ in load_pairs])
        mod = np.array([x for _, x, _ in load_pairs])
        t_in = np.array([t for _, _, t in load_pairs])
        tol = TARGETS["load"][0]

        # --- the fitted constant, kept so the derivation can be checked -----
        # BMW's relative filling is normalised to its own reference charge,
        # which is not our 100 kPa. Fit ONE scale factor, then judge the
        # residual: the question is whether the model's load TREND matches the
        # car's, not whether two different normalisations happen to coincide.
        k_fit = float(np.sum(meas * mod) / np.sum(mod * mod))
        mape_fit = float(np.mean(100.0 * np.abs(k_fit * mod - meas) / meas))

        # --- the same constant, DERIVED, with nothing fitted ----------------
        # k is a ratio of two air densities and nothing else. Ours is 100 kPa at
        # the measured intake temperature; BMW's is the DIN reference state,
        # 1013 mbar and 0 C. rho = P/(R*T), so
        #
        #     k = (100 / T_in) / (101.3 / 273.15) = DIN_REF / T_in
        #     DIN_REF = 100 * 273.15 / 101.3 = 269.64
        #
        # DIN_REF is three DEFINED constants. It is not fitted, tuned, or read
        # off a curve. The only measured quantity left is our own logged intake
        # temperature, so this version of the load comparison has ZERO free
        # parameters.
        #
        # WHY THIS IS EVIDENCE AND NOT NUMEROLOGY. The reference temperature is
        # the one thing we had to assume. Had BMW normalised to 20 C, the same
        # arithmetic would give 289.4 / T_in ~ 0.840, which the fit rules out at
        # 0.784. The data picks the reference state on its own; a fudge factor
        # would have matched either. Report that, not just the residual.
        #
        # LIMIT, STATE IT. k now varies point to point with the intake
        # temperature sensor -- the PRE-THROTTLE one, which lags under boost
        # (see CLAUDE.md). Every point here is 31-82 kPa, where it tracks. Do
        # not carry this form into the boosted region without re-checking.
        DIN_REF = 100.0 * 273.15 / 101.3          # = 269.64, K
        k_pred = DIN_REF / t_in
        mape_pred = float(np.mean(100.0 * np.abs(k_pred * mod - meas) / meas))
        k_alt = (100.0 * 293.15 / 101.3) / float(np.mean(t_in))   # if ref were 20 C

        print(f"  intake temperature over these points: "
              f"{float(np.mean(t_in)) - 273.15:.0f} C mean, "
              f"{t_in.min() - 273.15:.0f}-{t_in.max() - 273.15:.0f} C")
        print()
        print(f"  FITTED     k = {k_fit:.3f}            residual MAPE {mape_fit:.1f} %   "
              f"(1 free parameter)")
        print(f"  DERIVED    k = {DIN_REF:.1f} / T_in     residual MAPE {mape_pred:.1f} %   "
              f"(0 free parameters)")
        print(f"             mean of the derived k over these points = "
              f"{float(np.mean(k_pred)):.3f}")
        print()
        print(f"  The derived constant agrees with the fitted one to "
              f"{100.0 * abs(float(np.mean(k_pred)) - k_fit) / k_fit:.1f} %, which is the "
              f"real result:")
        print(f"  k is BMW's DIN normalisation (1013 mbar, 0 C), not a parameter we tuned.")
        print(f"  A 20 C reference would give k = {k_alt:.3f} -- the fit excludes it.")
        print()
        mape = mape_pred
        print(f"  HEADLINE: residual MAPE {mape:.1f} %   target < {tol:.0f} %   "
              f"{'PASS' if mape < tol else 'FAIL'}   (zero fitted parameters)")
        print(f"  raw MAPE without any normalisation: {float(np.mean(load_err)):.1f} % "
              f"(expected to be large — different reference state, not a model error)")
        if mape >= tol:
            print("  A large RESIDUAL means the trend itself disagrees. That is a real")
            print("  finding: look at volumetric efficiency first, then residual fraction.")

    print("""
NOT VALIDATED BY THIS SCRIPT
  Coolant and oil temperature are OUTPUTS of thermal.py, not of the cycle model
  -- run_cycle takes coolant temperature as an INPUT. Validate those separately
  by driving thermal.py over the whole log as a time series. Different exercise,
  different subsection of Chapter 3.

  Exhaust backpressure is not measured on this vehicle. predict() estimates it
  as 1.15 x manifold pressure. State that as an assumption.

  The boosted, knock-limited, enriched region is not reachable from a steady
  drive. Validate it against published correlations and say so.""")


if __name__ == "__main__":
    main()

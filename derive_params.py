"""derive_params.py -- every constant the car's logs can set, recomputed from them.

    python derive_params.py            # ~2 min; writes data/derived_params.json
                                       # build_dataset.py runs it at the end

WHAT THIS REPLACES. Until 28 September these were numbers typed into modules --
each fitted once, on the data of that day, and then frozen while the data moved
on. The load constant k showed the better way: it is DERIVED (269.6 / T_charge
at each point), so it can never go stale. This file applies that to everything
the data can set, and says for each whether it is a definition or an estimate:

  thermal     block and oil nodes of thermal.py        ESTIMATED   calibrate_thermal.fit,
                                                                   seeded, on every drive
                                                                   that qualifies
  boost       plant.boost_ceiling_kpa: A, B, cap       ESTIMATED   least squares on the
                                                                   binned envelope; the cap
                                                                   is the highest pressure
                                                                   ratio the car reached
  spark       BaselineECU.SPARK_A, the offset          DEFINED     the offset at which the
                                                                   commanded spark has zero
                                                                   mean bias against the car
                                                                   (solved, not searched)
  torque      Vehicle.DELIVERABLE_TORQUE               MEASURED    through the plant, after
              (the gearbox's kickdown table)           ON THE      the above
                                                           MODEL

A PLANT THAT MOVES WITH THE DATA MOVES THE LOCKED SCENARIO. Adding a drive and
re-running this changes the simulator, and a trained agent is only valid for the
simulator it trained on. The file carries a fingerprint of its inputs; record
the commit of data/derived_params.json beside any Phase D result, and retrain
after it changes (CLAUDE.md, "A plant change after the retrain means retraining").

WHAT IS STILL TYPED, AND WHY: see REFERENCES.md section 4b. In short -- the
turbine node, the exhaust backpressure, the port heat loss and the combustion
correlations have no channel on this car to be derived from.
"""
import hashlib
import json
import os
import subprocess
import sys
import time

os.environ["DERIVING_PARAMS"] = "1"          # see derived.py: import before the file exists

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.path.join(HERE, "data", "derived_params.json")

BIN_KGS, MIN_ROWS, PCTL = 0.03, 15, 95.0        # the envelope method, as documented since 8 Sep


def fingerprint():
    """What the derivation was computed FROM. verify_docs.py fails if the data
    has moved on and this file has not been re-derived."""
    h = hashlib.sha1()
    for name in ("master_samples.csv", "master_points.csv"):
        with open(os.path.join(HERE, "data", name), "rb") as fh:
            h.update(fh.read().replace(b"\r\n", b"\n"))
    raw = sorted(os.listdir(os.path.join(HERE, "logs", "raw")))
    return dict(data_sha1=h.hexdigest()[:16], raw_logs=raw)


# ------------------------------------------------------------------ thermal
def derive_thermal():
    import calibrate_thermal as K
    names, excluded = K.usable_drives()
    drives = [d for d in (K.load_drive(s) for s in names) if d is not None]
    p, j_oil, j_blk = K.fit(drives)
    scale = p.pop("ua_rad_scale")
    out = dict(p)
    out["ua_rad_min"] = K.UA_RAD_MIN * scale
    out["ua_rad_ram"] = K.UA_RAD_RAM * scale
    out["ua_rad_fan"] = K.UA_RAD_FAN * scale
    out["_ua_rad_scale"] = scale
    out["_oil_tau_rest_s"] = K.tau_oil({**p}, 0.0)
    out["_fit_oil_rmse_k"] = j_oil
    out["_fit_coolant_rmse_k"] = j_blk
    out["_drives"] = names
    out["_excluded"] = excluded
    out["_method"] = ("calibrate_thermal.fit: stage 1 oil with block pinned to measured coolant, "
                      "stage 2 block with oil pinned; cross-entropy search, seed 0")
    return out


# ---------------------------------------------------------- boost ceiling
def envelope_bins(S, assumed_inlet_c=None):
    """p95 pressure ratio per corrected-flow bin. `assumed_inlet_c` re-scales the
    rows whose ambient was NOT logged (t_amb_assumed) to another inlet
    temperature, for the sensitivity check -- nothing else moves."""
    use = S[(S.stable == 1) & (S.maf_pinned == 0) & np.isfinite(S.corr_flow)
            & np.isfinite(S.press_ratio) & (S.corr_flow > 0.01) & S.press_ratio.between(0.8, 6.0)].copy()
    if assumed_inlet_c is not None and "t_amb_assumed" in use:
        import build_dataset as B
        k = use.t_amb_assumed == 1
        use.loc[k, "corr_flow"] *= np.sqrt((273.15 + assumed_inlet_c) / (273.15 + B.AMB_FALLBACK_C))
    rows = []
    for lo in np.arange(0.0, use.corr_flow.max() + BIN_KGS, BIN_KGS):
        b = use[(use.corr_flow >= lo) & (use.corr_flow < lo + BIN_KGS)]
        if len(b) >= MIN_ROWS:
            fresh = sum(int((d.sort_values("t").corr_flow.diff().fillna(1.0) != 0).sum())
                        for _, d in b.groupby("source"))
            rows.append((lo + BIN_KGS / 2, float(np.percentile(b.press_ratio, PCTL)), len(b), fresh))
    return rows, float(use.press_ratio.max())


def fit_ceiling(m, pr):
    """PR = 1 + A m / (1 + B m), least squares. Started from the exact linear
    form 1/(PR-1) = (1/A)(1/m) + B/A, then Gauss-Newton; deterministic."""
    y = 1.0 / np.maximum(pr - 1.0, 1e-6)
    slope, icpt = np.polyfit(1.0 / m, y, 1)
    a, b = 1.0 / slope, icpt / slope
    for _ in range(200):
        f = 1.0 + a * m / (1.0 + b * m)
        r = pr - f
        ja = m / (1.0 + b * m)
        jb = -a * m ** 2 / (1.0 + b * m) ** 2
        J = np.column_stack([ja, jb])
        step, *_ = np.linalg.lstsq(J, r, rcond=None)
        a, b = a + step[0], b + step[1]
        if np.max(np.abs(step)) < 1e-10:
            break
    rms = float(np.sqrt(np.mean((pr - (1.0 + a * m / (1.0 + b * m))) ** 2)))
    return float(a), float(b), rms


def derive_boost(S):
    bins, pr_max = envelope_bins(S)
    m = np.array([b[0] for b in bins]); pr = np.array([b[1] for b in bins])
    a, b, rms = fit_ceiling(m, pr)
    # Sensitivity: the one drive without an ambient channel (drive B) re-scaled
    # to the coolest and hottest ambient ever logged on this car.
    sens = {}
    if "t_amb_assumed" in S and (S.t_amb_assumed == 1).any():
        amb = S.loc[(S.t_amb_assumed == 0) & (S.t_amb > -40.0), "t_amb"].dropna()
        for t in (float(amb.min()), float(amb.max())):
            bb, _ = envelope_bins(S, assumed_inlet_c=t)
            aa, bbb, rr = fit_ceiling(np.array([x[0] for x in bb]), np.array([x[1] for x in bb]))
            sens[f"{t:.0f} C"] = dict(A=aa, B=bbb, rms=rr)
    # THE CEILING THE PLANT USES IS THE MEASURED ENVELOPE ITSELF -- the binned
    # p95, made monotone by a running maximum (a ceiling cannot fall as flow
    # rises; a dip between bins is sampling, not physics), anchored at PR 1 with
    # no flow, interpolated linearly between bins and held flat past the last.
    # No constant is fitted to it. A and B are kept beside it only so the move
    # from the 8 September formula can be seen: that form cannot follow the
    # envelope's jump between 0.075 and 0.105 kg/s, which is where drive B's
    # low-rpm roll-ons sit.
    env_flow = [0.0] + [float(x) for x in m]
    env_pr = [1.0] + [float(x) for x in np.maximum.accumulate(pr)]
    pr_env = np.interp(m, env_flow, env_pr)
    return dict(envelope_flow=env_flow, envelope_pr=env_pr,
                envelope_rms_vs_bins=float(np.sqrt(np.mean((pr - pr_env) ** 2))),
                A=a, B=b, pr_cap=pr_max, rms=rms,
                bins=[dict(flow=x[0], pr_p95=x[1], rows=x[2], readings=x[3]) for x in bins],
                sensitivity_to_assumed_ambient=sens,
                _method=(f"p{PCTL:.0f} pressure ratio per {BIN_KGS} kg/s corrected-flow bin, "
                         f">= {MIN_ROWS} rows, stable and not MAF-pinned; the plant interpolates "
                         "the running maximum of the bins (no fitted constant); A and B are a "
                         "least-squares PR = 1 + A m/(1 + B m) kept for comparison only; "
                         "cap = highest stable pressure ratio observed"))


# ------------------------------------------------------------ spark offset
def derive_spark(P):
    """SPARK_A such that BaselineECU's commanded part-load spark has zero mean
    bias against the car's logged spark over the operating points. B and C,
    the slopes, are the 7 September fit and are NOT re-derived: refitting them
    extends a part-load slope into boost (mistake 6; engine_env.BaselineECU)."""
    from engine_env import BaselineECU
    from plant import charge_temperature
    ecu = BaselineECU()
    pts = P[np.isfinite(P.spark)]
    amb = pts.t_amb.fillna(25.0).to_numpy() + 273.15
    ect = pts.ect.fillna(90.0).to_numpy() + 273.15
    comp = np.array([ecu.iat_compensation(charge_temperature(a, e)) for a, e in zip(amb, ect)])
    rpm, mp, meas = pts.rpm.to_numpy(), pts.map_kpa.to_numpy(), pts.spark.to_numpy()
    kl = np.array([ecu.knock_limited_spark(r, m) for r, m in zip(rpm, mp)])

    def cmd(a):
        line = a + ecu.SPARK_B * rpm - ecu.SPARK_C * (mp - 40.0)
        return np.clip(np.minimum(line, kl), ecu.SPARK_MIN, ecu.SPARK_MAX) + comp, line <= kl

    lo, hi = -40.0, 80.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if np.mean(cmd(mid)[0] - meas) < 0:
            lo = mid
        else:
            hi = mid
    a = 0.5 * (lo + hi)
    c, line_sets = cmd(a)
    e = c - meas
    return dict(SPARK_A=a, bias=float(e.mean()), rms=float(np.sqrt(np.mean(e ** 2))),
                n_points=int(len(pts)), line_sets=int(line_sets.sum()),
                _method="solved for zero mean bias over master_points (bisection); slopes held")


# ------------------------------------------------------------- enrichment
def _genuine_lambda_above_gate(S):
    from verify_docs import dwell_column
    from engine_env import BaselineECU
    gate = BaselineECU.ENR_LOAD
    S2 = dwell_column(S, thr=gate)
    h = S2[(S2.map_kpa > gate) & S2.lam.between(0.5, 1.3)]
    fresh = []
    for _, d in h.groupby("source"):
        d = d.sort_values("t")
        fresh.append(d[d.lam.diff().fillna(1.0) != 0])
    h = pd.concat(fresh)
    return h.rpm.to_numpy(), h.dwell.to_numpy(), h.lam.to_numpy(), h.groupby("source").size().to_dict()


def derive_enrichment(S):
    """ENR_DWELL_LO / ENR_DWELL_HI of BaselineECU.base_lambda, on the TIMESTAMP
    dwell axis, from the car's genuine lambda readings above ENR_LOAD.

    WHY THESE TWO. They were the 8 September fit, made on the row-count dwell
    axis AUDIT.md H3 retired, and never re-derived: wrong-axis numbers. They are
    now solved on the right axis by least squares over a fixed grid (0.25 s),
    with ENR_RPM_LO/HI and ENR_DEPTH held.

    WHY NOT ALL FIVE -- TRIED, AND RECORDED. A free fit of all five on the same
    readings puts ENR_RPM_LO on the lowest candidate in its grid (2500 rpm) and
    a depth that cannot reach the car's measured 0.79-0.81 floor: ~100 genuine
    readings do not identify five constants. Its result is kept in the output
    as `free_fit_all_five`, as the evidence, and is not used. ENR_LOAD is a
    definition (mistake 13), not a fit.
    """
    from engine_env import BaselineECU
    E = BaselineECU
    rpm, dw, lam, by_drive = _genuine_lambda_above_gate(S)
    s = np.clip((rpm - E.ENR_RPM_LO) / (E.ENR_RPM_HI - E.ENR_RPM_LO), 0.0, 1.0)

    def rmse(l0, l1, depth=E.ENR_DEPTH, ss=s):
        return float(np.sqrt(np.mean((1.0 - depth * ss * np.clip((dw - l0) / (l1 - l0), 0, 1) - lam) ** 2)))
    best = min(((rmse(l0, l1), l0, l1) for l0 in np.arange(0.0, 6.01, 0.25)
                for l1 in np.arange(l0 + 0.5, 15.01, 0.25)), key=lambda x: x[0])

    # the free five-constant fit, for the record only
    y = 1.0 - lam
    free = None
    for r0 in np.arange(2500.0, 4501.0, 100.0):
        for r1 in np.arange(r0 + 300.0, 6501.0, 100.0):
            ss = np.clip((rpm - r0) / (r1 - r0), 0.0, 1.0)
            for l0 in np.arange(0.0, 6.01, 0.25):
                l1s = np.arange(l0 + 0.5, 15.01, 0.5)
                g = ss[None, :] * np.clip((dw[None, :] - l0) / (l1s[:, None] - l0), 0.0, 1.0)
                gg = (g * g).sum(axis=1)
                dep = np.clip(np.where(gg > 0, (g * y[None, :]).sum(axis=1) / np.maximum(gg, 1e-12), 0), 0, 0.5)
                sse = ((y[None, :] - dep[:, None] * g) ** 2).sum(axis=1)
                k = int(np.argmin(sse))
                if free is None or sse[k] < free[0]:
                    free = (float(sse[k]), r0, r1, l0, float(l1s[k]), float(dep[k]))
    return dict(ENR_DWELL_LO=float(best[1]), ENR_DWELL_HI=float(best[2]), rmse=best[0],
                rmse_8sep_2_9s=rmse(2.0, 9.0), readings=int(len(lam)),
                readings_above_rpm_lo=int((rpm > E.ENR_RPM_LO).sum()), by_drive=by_drive,
                held=dict(ENR_RPM_LO=E.ENR_RPM_LO, ENR_RPM_HI=E.ENR_RPM_HI, ENR_DEPTH=E.ENR_DEPTH),
                free_fit_all_five=dict(ENR_RPM_LO=free[1], ENR_RPM_HI=free[2], ENR_DWELL_LO=free[3],
                                       ENR_DWELL_HI=free[4], ENR_DEPTH=free[5],
                                       rmse=float(np.sqrt(free[0] / len(y))),
                                       note="NOT USED: RPM_LO on the grid edge, floor 1-DEPTH above the car's 0.79"),
                _method="least squares over genuine lambda readings above ENR_LOAD, timestamp dwell, 0.25 s grid")


# ---------------------------------------------------- deliverable torque
def derive_torque():
    """Measured through the plant in a FRESH process, so it sees the boost
    ceiling and spark offset just written rather than the ones this process
    imported."""
    env = dict(os.environ, DERIVING_PARAMS="1")
    code = ("import json, engine_env as E; "
            "print(json.dumps(E.measure_deliverable_torque()))")
    r = subprocess.run([sys.executable, "-c", code], cwd=HERE, env=env,
                       capture_output=True, text=True, check=True)
    return [[int(a), round(float(b), 1)] for a, b in json.loads(r.stdout.strip().splitlines()[-1])]


def write(d):
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=1)


def main():
    t0 = time.time()
    S = pd.read_csv(os.path.join(HERE, "data", "master_samples.csv"), low_memory=False)
    P = pd.read_csv(os.path.join(HERE, "data", "master_points.csv"))
    out = dict(_about="Every constant computed from the car's logs. Regenerate with "
                      "python derive_params.py; never edit by hand. See derived.py.",
               _generated=time.strftime("%Y-%m-%d %H:%M"), _inputs=fingerprint())

    print("thermal: fitting the block and oil nodes to every qualifying drive ...")
    out["thermal"] = derive_thermal()
    th = out["thermal"]
    print(f"   {len(th['_drives'])} drives; oil tau at rest {th['_oil_tau_rest_s']:.1f} s; "
          f"stat opens {th['t_stat_open'] - 273.15:.1f} C; radiator x{th['_ua_rad_scale']:.2f}")

    print("boost ceiling: the envelope, binned and fitted ...")
    out["boost_ceiling"] = derive_boost(S)
    bc = out["boost_ceiling"]
    print(f"   envelope over {len(bc['bins'])} bins, cap PR {bc['pr_cap']:.3f}, monotone-envelope RMS "
          f"{bc['envelope_rms_vs_bins']:.3f}  (the old formula's A {bc['A']:.3f} B {bc['B']:.3f} "
          f"would leave RMS {bc['rms']:.3f})")
    for k, v in bc["sensitivity_to_assumed_ambient"].items():
        print(f"   drive B's inlet at {k}: A {v['A']:.4f}  B {v['B']:.4f}")

    print("enrichment: dwell thresholds on the timestamp axis ...")
    out["enrichment"] = derive_enrichment(S)
    en = out["enrichment"]
    print(f"   ENR_DWELL_LO {en['ENR_DWELL_LO']:.2f} s  ENR_DWELL_HI {en['ENR_DWELL_HI']:.2f} s  RMSE {en['rmse']:.4f} "
          f"(8 Sep 2/9 s: {en['rmse_8sep_2_9s']:.4f}) over {en['readings']} genuine readings")

    print("spark offset: solved for zero mean bias ...")
    out["spark"] = derive_spark(P)
    sp = out["spark"]
    print(f"   SPARK_A {sp['SPARK_A']:.3f}  bias {sp['bias']:+.3f} deg  RMS {sp['rms']:.2f} deg  "
          f"line sets spark at {sp['line_sets']} of {sp['n_points']} points")

    write(out)
    print("deliverable torque: measured through the plant (fresh process) ...")
    out["deliverable_torque"] = derive_torque()
    write(out)
    tq = dict(out["deliverable_torque"])
    print(f"   {tq[1600]:.0f} Nm at 1600 rpm, {tq[2000]:.0f} at 2000, {tq[2600]:.0f} at 2600, "
          f"{tq[4400]:.0f} at 4400")
    print(f"\nwrote {os.path.relpath(OUT, HERE)}  ({(time.time() - t0) / 60:.1f} min)")


if __name__ == "__main__":
    main()

"""model_vs_data.py -- every place the simulation can be laid beside the car.

    python model_vs_data.py            # ~3 min on a multi-core machine

Writes results/model_vs_data.json for make_figures.py and the results page, and
prints each comparison with the figure the project documents beside it, so a
reader can see at once whether this run reproduces what the documents claim.

WHAT IS COMPARED, AND WHAT EACH COMPARISON CAN AND CANNOT SEE
------------------------------------------------------------
Each section below says what its residual is sensitive to. That is the lesson
of CLAUDE.md mistake 12: a residual computed through an inversion of the same
model cannot test that model, so the question "what would move this number?"
is asked of every comparison here before its result is quoted.

  load          relative air filling at the steady operating points. Blind to
                the breathing model (mistake 12); sensitive to displacement.
  boost         manifold pressure inverted from measured air mass against the
                car's own boost channel, under boost only (mistake 13).
  enrichment    base_lambda against measured lambda, speed band x dwell.
  spark         the fitted part-load spark map against logged spark.
  thermal       thermal.py free-running over a whole drive against the
                logged coolant and oil channels.
  knock         the model knock integral against the car's own retard.
  gearbox       overall ratio from engine and road speed against the eight
                published ZF 8HP51 ratios (mistake 18).
  envelope      logged pressure ratio against plant.boost_ceiling_kpa.
  duty cycle    where the car was driven against where Phase D is scored.
  literature    validate.py's rows against their bands. Published ranges, not
                car data, and REFERENCES.md grades which are sourced.

It reads data/master_samples.csv and data/master_points.csv and never writes
to data/ or logs/raw/. Every number it prints is computed on this run.
"""
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

OUT = os.path.join(HERE, "results", "model_vs_data.json")


def _clean(o):
    """JSON-safe: numpy scalars to Python, NaN to None."""
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not math.isfinite(float(o)) else round(float(o), 5)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


# =================================================================== load
def load_residual():
    """Relative air filling: model (derived k, zero free parameters) vs car.

    Also re-runs the same residual with the geometry forced to the wrong
    engine, because displacement is the one thing this residual CAN see.
    """
    from plant import predict, map_from_airflow, charge_temperature, b58, Geometry
    P = pd.read_csv(os.path.join(HERE, "data", "master_points.csv"))
    din = 100.0 * 273.15 / 101.3

    def score(geo):
        rows = []
        for _, r in P.iterrows():
            ect_k = (r.ect if np.isfinite(r.ect) else 90.0) + 273.15
            amb_k = (r.t_amb if np.isfinite(r.t_amb) else 25.0) + 273.15
            t_in = charge_temperature(amb_k, ect_k)
            mp = map_from_airflow(r.air_kgh / 3.6, r.rpm, t_in, geo=geo)
            lam = r.lam if np.isfinite(r.lam) and r.lam > 0 else 1.0
            spk = r.spark if np.isfinite(r.spark) else 20.0
            o = predict(rpm=r.rpm, map_kpa=mp, iat_k=t_in, ect_k=ect_k,
                        spark_btdc=spk, lam=lam, geo=geo)
            model = (din / t_in) * 100.0 * o["eta_v"] * (1 - o["f_res"]) * mp / 100.0
            rows.append(dict(rpm=r.rpm, map_kpa=mp, meas=r.load_pct, model=model))
        err = [100 * abs(x["model"] - x["meas"]) / x["meas"] for x in rows]
        return rows, float(np.mean(err))

    rows, mape = score(b58())
    # RETIRED-OK: the 2.0 L four of mistake 1 is rebuilt here ON PURPOSE, to
    # show that this residual can see displacement. Bore and stroke are
    # scaled together to 1998 cc; the residual cares only about swept volume.
    g6 = b58()
    four = Geometry(bore=g6.bore, stroke=g6.stroke, n_cyl=4)
    k = (1998.0 / (four.vd_total * 1e6)) ** (1 / 3)
    wrong = Geometry(bore=g6.bore * k, stroke=g6.stroke * k, n_cyl=4)
    _, wrong_mape = score(wrong)
    return dict(points=rows, mape=mape, wrong_engine_mape=wrong_mape,
                wrong_engine_cc=wrong.vd_total * 1e6)


# ================================================================== boost
def boost_gap(S):
    """Inverted manifold pressure under boost vs the car's own boost channel."""
    import glob
    from plant import map_from_airflow
    hi = S[(S.map_kpa > 200) & (~S.maf_pinned.astype(bool))].copy()
    # The same samples re-inverted with the raw pre-throttle sensor as the
    # charge temperature -- what the model did before mistake 13.
    raw = [map_from_airflow(a, n, t + 273.15)
           for a, n, t in zip(hi.air_gps, hi.rpm, hi.iat_pre_c)
           if np.isfinite(t)]
    logged = []
    for f in sorted(glob.glob(os.path.join(HERE, "logs", "raw", "*.csv"))):
        if os.path.basename(f) not in set(hi.source):
            continue
        d = pd.read_csv(f)
        bc = [c for c in d.columns if c.lower() == "boost pressure"]
        ac = [c for c in d.columns if "ambient" in c.lower() and "press" in c.lower()]
        if not bc:
            continue
        b = pd.to_numeric(d[bc[0]], errors="coerce").dropna()
        a = pd.to_numeric(d[ac[0]], errors="coerce").median() if ac else 14.23
        logged += list((b[b > 15.0] + a) * 6.894757)
    med_l = float(np.median(logged))
    return dict(model=hi.map_kpa.round(1).tolist(), raw_sensor=list(np.round(raw, 1)),
                logged=list(np.round(logged, 1)),
                median_model=float(hi.map_kpa.median()),
                median_raw=float(np.median(raw)), median_logged=med_l,
                gap_model_pct=100 * (float(hi.map_kpa.median()) - med_l) / med_l,
                gap_raw_pct=100 * (float(np.median(raw)) - med_l) / med_l,
                n_model=len(hi), n_logged=len(logged))


# ============================================================= enrichment
def enrichment(S):
    """base_lambda vs measured lambda, in the speed-band x dwell grid."""
    from verify_docs import dwell_column
    from engine_env import BaselineECU
    ecu = BaselineECU()
    S2 = dwell_column(S)
    h = S2[(S2.map_kpa > 180) & S2.lam.between(0.5, 1.3)].copy()
    h["model"] = [ecu.base_lambda(r, m, d) for r, m, d in zip(h.rpm, h.map_kpa, h.dwell)]
    bands = ((1000, 3500), (3500, 4500), (4500, 7000))
    dwells = ((0, 4), (4, 8), (8, 1e9))
    # The dwell axis AUDIT.md H3 retired -- a run of ROWS over an assumed 4.6 Hz
    # -- kept only so the table can show where the documented cell values came
    # from. It is not used for any comparison.
    old = []
    for _, d in h.groupby("source"):
        d = d.sort_values("t").copy()
        full = S2[S2.source == d.source.iloc[0]].sort_values("t")
        acc, run = 0, {}
        for i, v in zip(full.index, (full.map_kpa > 180).fillna(False)):
            acc = acc + 1 if v else 0
            run[i] = acc / 4.6
        d["dwell_rows"] = [run.get(i, np.nan) for i in d.index]
        old.append(d)
    h = pd.concat(old)
    cells = []
    for lo, hi_ in bands:
        for dlo, dhi in dwells:
            sel = (h.rpm > lo) & (h.rpm <= hi_)
            c = h[sel & (h.dwell >= dlo) & (h.dwell < dhi)]
            c_old = h[sel & (h.dwell_rows >= dlo) & (h.dwell_rows < dhi)]
            cells.append(dict(rpm=f"{lo}-{hi_}",
                              dwell=f"{dlo}-{int(dhi)} s" if dhi < 1e8 else f"{dlo}+ s",
                              n=len(c),
                              meas=float(c.lam.median()) if len(c) else None,
                              model=float(c.model.median()) if len(c) else None,
                              meas_rows_axis=(float(c_old.lam.median())
                                              if len(c_old) else None)))
    worst = max(abs(c["meas"] - c["model"]) for c in cells if c["meas"] is not None)
    return dict(cells=cells, worst_abs=worst, n=len(h))


# ================================================================== spark
def spark(P):
    """Commanded part-load spark against logged spark at every operating point.

    THREE VERSIONS, because they tell apart two things that look like one.
    BaselineECU commands base_spark() PLUS iat_compensation(), and the map's
    constants were fitted with the compensation fed by the PRE-THROTTLE sensor
    -- before mistake 13 showed that sensor is a compressor outlet. The
    environment now feeds the compensation plant.charge_temperature() instead,
    which is right, but the map was not refitted after the input moved.

      at_fit    compensation at the pre-throttle sensor: how the map was fitted
      as_run    compensation at the modelled charge: what the simulator commands
      base      base_spark() alone, no compensation: for reference only
    """
    from engine_env import BaselineECU
    from plant import charge_temperature
    ecu = BaselineECU()
    pts = []
    for _, r in P.iterrows():
        if not (np.isfinite(r.spark) and np.isfinite(r.iat_pre)):
            continue
        amb = (r.t_amb if np.isfinite(r.t_amb) else 25.0) + 273.15
        ect = (r.ect if np.isfinite(r.ect) else 90.0) + 273.15
        base = ecu.base_spark(r.rpm, r.map_kpa)
        pts.append(dict(rpm=r.rpm, map_kpa=r.map_kpa, meas=r.spark, base=base,
                        as_run=base + ecu.iat_compensation(charge_temperature(amb, ect)),
                        at_fit=base + ecu.iat_compensation(r.iat_pre + 273.15)))

    def stats(key):
        e = np.array([p[key] - p["meas"] for p in pts])
        return dict(mean=float(e.mean()), mae=float(np.abs(e).mean()),
                    rmse=float(np.sqrt((e ** 2).mean())))
    return dict(points=pts, as_run=stats("as_run"), at_fit=stats("at_fit"),
                base=stats("base"))


# ========================================== thermal replay, and knock (heavy)
def replay(source):
    """Drive the plant and thermal.py over one logged drive, FREE-RUNNING.

    Unlike the app's estimator, the block node is NOT reset to the measured
    coolant: the point is to see what the thermal network does on its own when
    fed the car's operating points. Seeded from the measured coolant and oil at
    the first sample, per mistake 15 -- a seed outside the physics is worse
    than none.

    Inputs at 1 Hz: the round-robin logger refreshes each channel every few
    seconds (mistake 13b), so finer steps add rows, not information.
    """
    from plant import predict, charge_temperature
    from thermal import ThermalNetwork
    from engine_env import BaselineECU, GEO
    S = pd.read_csv(os.path.join(HERE, "data", "master_samples.csv"))
    d = S[S.source == source].sort_values("t").reset_index(drop=True)
    t0 = d.t.iloc[0]
    grid = np.arange(0.0, d.t.iloc[-1] - t0, 1.0)
    idx = np.searchsorted(d.t.to_numpy() - t0, grid, side="right") - 1
    d = d.iloc[np.clip(idx, 0, len(d) - 1)].reset_index(drop=True)
    d["tr"] = grid

    # AUDIT.md M8: BimmerLink writes exact zeros into a column until the ECU
    # first answers for that channel. A coolant or oil of exactly 0 C on a warm
    # engine is a placeholder, not a reading -- seeding from one starts the
    # node 90 K cold and the first minutes of the comparison are the seed.
    for col in ("ect_c", "oil_c", "t_amb"):
        d.loc[d[col] == 0.0, col] = np.nan

    def first_real(col, default):
        v = d[col].dropna()
        return float(v.iloc[0]) if len(v) else default

    tn, ecu = ThermalNetwork(), BaselineECU()
    amb = first_real("t_amb", 30.0) + 273.15
    tn.reset(t_amb=amb, warm=True)
    tn.t_block = first_real("ect_c", 90.0) + 273.15
    tn.t_oil = first_real("oil_c", 90.0) + 273.15

    out = dict(t=[], ect_meas=[], ect_model=[], oil_meas=[], oil_model=[],
               ki=[], retard=[], rpm=[], v=[], egt=[])
    for _, r in d.iterrows():
        amb = (r.t_amb if np.isfinite(r.t_amb) else amb - 273.15) + 273.15
        ect_k = (r.ect_c if np.isfinite(r.ect_c) else 90.0) + 273.15
        if not (np.isfinite(r.rpm) and r.rpm > 400 and np.isfinite(r.map_kpa)):
            continue
        t_ch = charge_temperature(amb, tn.t_block)
        _, lam_ecu, fan = ecu.step(r.rpm, r.map_kpa, t_ch, tn.t_block, False, 1.0)
        lam = r.lam if np.isfinite(r.lam) and 0.5 < r.lam < 1.5 else lam_ecu
        spk = r.spark if np.isfinite(r.spark) else 20.0
        o = predict(rpm=r.rpm, map_kpa=r.map_kpa, iat_k=t_ch, ect_k=tn.t_block,
                    spark_btdc=spk, lam=lam, geo=GEO)
        fuel = o["mdot_fuel_gps"]
        v = (r.v_kmh if np.isfinite(r.v_kmh) else 0.0) / 3.6
        tn.step(1.0, fuel, fuel * 15.0, o["egt_c"] + 273.15, amb, v, fan)
        out["t"].append(r.tr)
        out["ect_meas"].append(r.ect_c)
        out["ect_model"].append(tn.t_block - 273.15)
        out["oil_meas"].append(r.oil_c)
        out["oil_model"].append(tn.t_oil - 273.15)
        out["ki"].append(o["knock_integral"])
        rt = (r.spark_tgt - r.spark) if (np.isfinite(r.spark_tgt)
                                         and np.isfinite(r.spark)) else np.nan
        out["retard"].append(rt)
        out["rpm"].append(r.rpm)
        out["v"].append(v * 3.6)
        out["egt"].append(o["egt_c"])
    return source, out


def knock_all_samples():
    """AUDIT.md H5 reproduced on every sample of 7475b5d7, not the 1 Hz grid."""
    from plant import predict, charge_temperature
    from engine_env import GEO
    S = pd.read_csv(os.path.join(HERE, "data", "master_samples.csv"))
    d = S[(S.source == "7475b5d7-20260908_142743.csv")].copy()
    d = d[np.isfinite(d.spark_tgt) & np.isfinite(d.spark) & np.isfinite(d.map_kpa)
          & (d.rpm > 400)]
    ki = []
    for _, r in d.iterrows():
        t_ch = charge_temperature((r.t_amb if np.isfinite(r.t_amb) else 30.0) + 273.15,
                                  (r.ect_c if np.isfinite(r.ect_c) else 90.0) + 273.15)
        lam = r.lam if np.isfinite(r.lam) and 0.5 < r.lam < 1.5 else 1.0
        o = predict(rpm=r.rpm, map_kpa=r.map_kpa, iat_k=t_ch,
                    ect_k=(r.ect_c if np.isfinite(r.ect_c) else 90.0) + 273.15,
                    spark_btdc=r.spark, lam=lam, geo=GEO)
        ki.append(o["knock_integral"])
    ret = (d.spark_tgt - d.spark).to_numpy()
    ki = np.array(ki)
    return dict(n=len(ki), corr=float(np.corrcoef(ki, ret)[0, 1]),
                ki_active_pct=100 * float((ki > 0.85).mean()),
                retard_active_pct=100 * float((ret > 1.0).mean()),
                ki=list(np.round(ki, 3)), retard=list(np.round(ret, 2)))


# ================================================================ gearbox
def gearbox(S):
    """Overall ratio the car actually ran, against the published ratios."""
    from engine_env import Vehicle
    veh = Vehicle()
    m = S[(S.v_kmh > 20) & (S.rpm > 700)]
    overall = (m.rpm * 2 * np.pi / 60.0) * veh.wheel_r / (m.v_kmh / 3.6)
    overall = overall[np.isfinite(overall) & (overall > 1.0) & (overall < 20.0)]
    pub = np.array(veh.gears) * veh.final_drive
    near = np.min(np.abs(overall.to_numpy()[:, None] / pub[None, :] - 1.0), axis=1)
    hist, edges = np.histogram(np.log(overall), bins=160)
    clamp = S.loc[m.index, "gear"] if "gear" in S.columns else None
    return dict(published=list(pub), gears=list(veh.gears),
                within4_pct=100 * float((near < 0.04).mean()), n=int(len(overall)),
                hist=hist.tolist(), edges=list(np.exp(edges)),
                gear_channel_max=(float(clamp.max()) if clamp is not None else None))


# =============================================================== envelope
def envelope(S):
    """Logged operating ceiling against plant.boost_ceiling_kpa."""
    from plant import boost_ceiling_kpa, corrected_flow
    st = S[(S.stable == 1) & np.isfinite(S.corr_flow) & np.isfinite(S.press_ratio)
           & (S.corr_flow > 0.01) & S.press_ratio.between(0.8, 6.0)]
    rng = np.random.default_rng(0)
    take = st.iloc[rng.choice(len(st), size=min(4000, len(st)), replace=False)]
    flows = np.linspace(0.01, 0.36, 80)
    # boost_ceiling_kpa takes a mass flow; invert corrected_flow at reference
    # inlet conditions so the curve is drawn on the corrected axis it was fit on.
    t_ref, p_ref = 298.0, 99.3
    per_gps = corrected_flow(1.0, t_ref, p_ref)
    curve = [boost_ceiling_kpa(f / per_gps, t_ref, p_ref) / p_ref for f in flows]
    return dict(flow=take.corr_flow.round(4).tolist(),
                pr=take.press_ratio.round(3).tolist(),
                curve_flow=list(flows), curve_pr=curve, n=len(st),
                pr_max=float(st.press_ratio.max()))


# ============================================================= duty cycle
def duty_cycle(S):
    """Where the car was driven, against where the scenario is scored."""
    from engine_env import SupervisoryTunerEnv, make_grade_climb, neutral_action
    m = S[(S.v_kmh > 5) & np.isfinite(S.map_kpa) & np.isfinite(S.rpm)]
    H, xe, ye = np.histogram2d(m.rpm, m.map_kpa, bins=[np.linspace(600, 7000, 65),
                                                        np.linspace(20, 260, 61)])
    env = SupervisoryTunerEnv(make_grade_climb(duration=720.0, dt=1.0), dt=1.0, seed=0)
    env.reset(seed=0)
    a = neutral_action()
    rpm, mp = [], []
    for k in range(719):
        _, _, term, trunc, _ = env.step(a)
        if k > 300:                      # the settled climb, not the approach
            rpm.append(env.rpm)
            mp.append(env.map_kpa)
        if term or trunc:
            break
    return dict(H=H.tolist(), rpm_edges=list(xe), map_edges=list(ye), n=len(m),
                load_median_by_drive={s: float(g.load_pct.median())
                                      for s, g in m.groupby("source")},
                load_over_120_pct=100 * float((m.load_pct > 120).mean()),
                scenario_rpm=float(np.median(rpm)), scenario_map=float(np.median(mp)),
                logs_map_p99=float(m.map_kpa.quantile(0.99)),
                frac_logs_at_or_above_scenario=100 * float(
                    (m.map_kpa >= np.median(mp)).mean()))


# ============================================================= literature
def literature():
    import validate
    rows = []
    for r in (validate.check_displacement(), validate.check_mfb50()[0],
              validate.check_bsfc()[0], validate.check_knock_limit(),
              *validate.check_egt(), *validate.check_time_constants()[0]):
        rows.append(dict(name=r["name"], value=r["value"], unit=r["unit"],
                         lo=r["lo"], hi=r["hi"], ok=bool(r["ok"])))
    return rows


# ================================================================== main
def _heavy(job):
    kind, arg = job
    if kind == "replay":
        return kind, replay(arg)
    if kind == "knock":
        return kind, knock_all_samples()
    if kind == "load":
        return kind, load_residual()
    if kind == "literature":
        return kind, literature()
    if kind == "duty":
        S = pd.read_csv(os.path.join(HERE, "data", "master_samples.csv"))
        return kind, duty_cycle(S)
    raise ValueError(kind)


def main():
    t0 = time.time()
    S = pd.read_csv(os.path.join(HERE, "data", "master_samples.csv"))
    P = pd.read_csv(os.path.join(HERE, "data", "master_points.csv"))
    res = {}

    jobs = [("replay", "drive10-20260918_233912.csv"),
            ("replay", "7475b5d7-20260908_142743.csv"),
            ("knock", None), ("load", None), ("literature", None), ("duty", None)]
    with ProcessPoolExecutor(max_workers=len(jobs)) as ex:
        futs = [ex.submit(_heavy, j) for j in jobs]
        res["boost"] = boost_gap(S)
        res["enrichment"] = enrichment(S)
        res["spark"] = spark(P)
        res["gearbox"] = gearbox(S)
        res["envelope"] = envelope(S)
        res["thermal"] = {}
        for f in futs:
            kind, val = f.result()
            if kind == "replay":
                res["thermal"][val[0]] = val[1]
            else:
                res[kind] = val

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(_clean(res), fh)

    L, B, E, K = res["load"], res["boost"], res["enrichment"], res["knock"]
    print(f"model vs data, {(time.time() - t0) / 60:.1f} min -> "
          f"{os.path.relpath(OUT, HERE)}\n")
    print("  what                                   this run     documented")
    print(f"  load residual, derived k, 26 points     {L['mape']:6.2f} %     1.4 %")
    if L["wrong_engine_mape"] is not None:
        print(f"  same, on a {L['wrong_engine_cc']:.0f} cc four-cylinder     "
              f"{L['wrong_engine_mape']:6.1f} %     48.1 %")
    print(f"  boosted MAP vs car, charge_temperature  {B['gap_model_pct']:+6.1f} %     +1.9 %")
    print(f"  boosted MAP vs car, raw sensor          {B['gap_raw_pct']:+6.1f} %     +23.7 % (older population)")
    print(f"  enrichment, worst cell |model - meas|   {E['worst_abs']:6.3f}       "
          "0.027 (on the retired row-count dwell axis, AUDIT.md H3)")
    Sp = res["spark"]
    print(f"  spark, as fitted (sensor T), RMS        {Sp['at_fit']['rmse']:6.2f} deg   "
          f"mean {Sp['at_fit']['mean']:+.2f}")
    print(f"  spark, as the simulator runs it, RMS    {Sp['as_run']['rmse']:6.2f} deg   "
          f"mean {Sp['as_run']['mean']:+.2f}   <- not refitted after mistake 13")
    print(f"  knock integral vs retard, correlation   {K['corr']:+6.3f}       -0.149")
    print(f"    paired samples                        {K['n']:6d}       13 592")
    print(f"  gearbox, samples within 4 % of a ratio  {res['gearbox']['within4_pct']:6.1f} %     86.7 %")
    print(f"  gear channel maximum                    {res['gearbox']['gear_channel_max']}")
    for src, th in res["thermal"].items():
        om = np.array(th["oil_model"], float); oo = np.array(th["oil_meas"], float)
        em = np.array(th["ect_model"], float); eo = np.array(th["ect_meas"], float)
        ok_o, ok_e = np.isfinite(oo), np.isfinite(eo)
        print(f"  thermal, {src[:8]}  oil  model-meas median {np.median(om[ok_o] - oo[ok_o]):+6.1f} K"
              f"   max meas {np.nanmax(oo):.0f} C, max model {np.nanmax(om):.0f} C")
        print(f"                      coolant model-meas median {np.median(em[ok_e] - eo[ok_e]):+6.1f} K")
    D = res["duty"]
    print(f"  scenario operating point                {D['scenario_rpm']:.0f} rpm, {D['scenario_map']:.0f} kPa")
    print(f"  logged moving samples at or above it    {D['frac_logs_at_or_above_scenario']:6.2f} %")
    print(f"  literature bands                        "
          f"{sum(r['ok'] for r in res['literature'])} of {len(res['literature'])} inside")


if __name__ == "__main__":
    main()

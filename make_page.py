"""make_page.py -- build the phone-readable results page from results/.

    python model_vs_data.py      # if the comparisons are stale
    python compare_calibration.py   # the 28 Sep before/after
    python generality_test.py    # the H/tau sweep -> results/generality.json
    python make_page.py          # writes results/page/index.html

The page is results/page/template.html with two kinds of hole filled:

  /*__DATA__*/null     the chart data, packed small enough to ship inline
  {{key|fmt}}          a single number in the prose, looked up in the same data

EVERY RESULT IN THE PAGE'S TEXT COMES FROM A TOKEN. No measured or simulated
figure is typed into the template, so the prose cannot drift from the run that
produced it -- the failure verify_docs.py exists to catch, closed at the
source. What IS written as itself is what defines the experiment rather than
what it found: the locked scenario, the trigger, the time steps, the published
bands' edges. An unknown token stops the build rather than printing a blank.

One count is a judgement, not a measurement: the scorecard's statuses (agrees,
limited, off, negative, not covered) and the "agree" tally in the headline are
assigned by reading each comparison, and the page says what each rests on.
"""
import glob
import json
import os
import re
import subprocess
from datetime import date

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
PAGE = os.path.join(RES, "page")


def _load(name):
    with open(os.path.join(RES, name)) as fh:
        return json.load(fh)


def _r(x, n=2):
    if x is None:
        return None
    if isinstance(x, (list, tuple, np.ndarray)):
        return [_r(v, n) for v in x]
    x = float(x)
    return None if not np.isfinite(x) else round(x, n)


def phase_d():
    tr = _load("traces_130kmh.json")
    names = ["baseline ECU", "reactive", "current-grade", "predictive (hand)"]
    t = tr[names[0]]["t"]
    step = 2
    trace = dict(t=_r(t[::step], 0),
                 series=[dict(name=n, turb=_r(tr[n]["t_turb"][::step], 1),
                              dmg=_r(tr[n]["dmg_cum"][::step], 1),
                              damage=_r(tr[n]["summary"]["damage"], 1),
                              fuel=_r(tr[n]["summary"]["fuel"], 0),
                              peak=_r(max(tr[n]["t_turb"]), 1))
                         for n in names],
                 climb_from=float(t[int(np.argmax(np.array(tr[names[0]]["grade"]) > 0))]))
    peaks = [max(tr[n]["t_turb"]) for n in names]
    trace["spread"] = _r(max(peaks) - min(peaks), 1)

    sw = _load("sweep_speed_grade.json")
    speeds = sorted({r["v_kmh"] for r in sw})
    grades = sorted({r["grade"] for r in sw})
    cell = {(r["v_kmh"], r["grade"]): r for r in sw}
    sweep = dict(speeds=speeds, grades=grades,
                 peak=[[_r(cell[(v, g)]["peak_c"], 1) for g in grades] for v in speeds],
                 above=[[_r(cell[(v, g)]["frac_above"], 1) for g in grades] for v in speeds])

    rows = _load("phase_d_130kmh_raw.json")
    order = []
    for r in rows:
        if r["policy"] not in order:
            order.append(r["policy"])

    def col(n, k):
        return np.array([r[k] for r in rows if r["policy"] == n], dtype=float)

    base = float(np.median(col("baseline ECU", "damage")))
    base_f = float(np.median(col("baseline ECU", "fuel")))

    def kind(n):
        return ("sighted" if "sighted" in n else "blinded" if "blind" in n
                else "hand")

    ev = []
    for n in order:
        d = col(n, "damage")
        q1, me, q3 = np.percentile(d, [25, 50, 75])
        ev.append(dict(name=n.replace("runs/", ""), kind=kind(n), med=_r(me, 1),
                       q1=_r(q1, 1), q3=_r(q3, 1), worst=_r(d.max(), 1),
                       fuel=_r(np.median(col(n, "fuel")), 0),
                       fuel_pct=_r(100 * (np.median(col(n, "fuel")) / base_f - 1), 2),
                       peak=_r(col(n, "peak_turb").max(), 1),
                       cut=_r(100 * (1 - me / base), 2)))
    # Differences from the UNROUNDED cuts, so the page and results/*.txt agree
    # to the last printed digit.
    cut = {n.replace("runs/", ""): 100.0 * (1.0 - float(np.median(col(n, "damage"))) / base)
           for n in order}
    fuel = {n.replace("runs/", ""): 100.0 * (float(np.median(col(n, "fuel"))) / base_f - 1.0)
            for n in order}
    seeds = [dict(seed=s, s=_r(cut[f"sighted_seed{s}"], 2), b=_r(cut[f"blind_seed{s}"], 2),
                  d=_r(cut[f"sighted_seed{s}"] - cut[f"blind_seed{s}"], 4),
                  fs=_r(fuel[f"sighted_seed{s}"], 2), fb=_r(fuel[f"blind_seed{s}"], 2))
             for s in range(5)]
    dd = np.array([x["d"] for x in seeds])
    sd = float(dd.std(ddof=1))
    half = 2.776 * sd / np.sqrt(len(dd))           # t(0.975, 4)
    from scipy import stats
    s_med = float(np.median([x["s"] for x in seeds]))
    ablation = dict(seeds=seeds, mean=_r(dd.mean(), 4), median=_r(np.median(dd), 4),
                    sd=_r(sd, 4), lo=_r(dd.mean() - half, 4), hi=_r(dd.mean() + half, 4),
                    p_t=_r(stats.ttest_1samp(dd, 0.0).pvalue, 2),
                    p_w=_r(stats.wilcoxon(dd).pvalue, 2),
                    grade_cut=cut["current-grade"], predictive_cut=cut["predictive (hand)"],
                    sighted_median=_r(s_med, 1),
                    agent_over_grade=_r(s_med - cut["current-grade"], 1),
                    within=int((np.abs(dd) <= 0.75).sum()),
                    pred_minus_grade=_r(cut["predictive (hand)"] - cut["current-grade"], 2))

    # 29 September 2026: the sentences about which agents beat which policy were
    # typed, and went false when the agents were re-scored on the derived plant
    # ("all ten beat every hand-written policy" -- three do not). They are
    # computed now, and the claims the text makes without a number are asserted.
    hand = [n for n in order if kind(n) == "hand"]
    agents = [n.replace("runs/", "") for n in order if kind(n) != "hand"]
    best_hand = max(cut[n] for n in hand)
    below = [a for a in agents if cut[a] <= best_hand]
    assert all(cut[a] > cut["reactive"] for a in agents), "the text says every agent beats reactive"

    def names_(xs):
        xs = [shortish(x) for x in xs]
        return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]

    def shortish(n):
        return n.replace("sighted_seed", "sighted ").replace("blind_seed", "blinded ")

    def seeds_(xs):
        return names_([f"__{x}" for x in xs]).replace("__", "")

    agents_ = dict(n=len(agents), beat=len(agents) - len(below), n_below=len(below),
                   below=names_(below) if below else "none",
                   below_lo=_r(min(cut[a] for a in below), 1) if below else None,
                   below_hi=_r(max(cut[a] for a in below), 1) if below else None,
                   best_hand=_r(best_hand, 1))
    low_fuel = [x["seed"] for x in seeds if x["fs"] < 0 and x["fb"] < 0]
    lf_cuts = [c for x in seeds if x["seed"] in low_fuel for c in (x["s"], x["b"])]
    more = [x for x in seeds if x["d"] > 0.75]
    less = [x for x in seeds if x["d"] < -0.75]
    fmt = lambda v: f"{v:.1f}"
    trade = dict(low_fuel=seeds_(low_fuel), lf_lo=_r(min(lf_cuts), 1), lf_hi=_r(max(lf_cuts), 1),
                 more=seeds_([x["seed"] for x in more]),
                 more_cut=names_([f"__{fmt(x['d'])}" for x in more]).replace("__", ""),
                 more_fuel=names_([f"__{fmt(x['fs'] - x['fb'])}" for x in more]).replace("__", ""),
                 less=seeds_([x["seed"] for x in less]))
    assert low_fuel and more, "the damage-against-fuel text needs both kinds of seed"

    curves = []
    for f in sorted(glob.glob(os.path.join(HERE, "runs", "*", "curve.csv"))):
        tag = os.path.basename(os.path.dirname(f))
        d = np.loadtxt(f, delimiter=",", skiprows=1, usecols=(0, 1, 2))
        curves.append(dict(run=tag, blind=tag.startswith("blind"), ret=_r(d[:, 1], 1)))

    # Damage split by term, on the hand-written traces. The knock term rests on
    # the knock model the car's logs have not been able to test.
    split = {}
    for nm in names:
        T_ = tr[nm]
        tt = np.array(T_["t_turb"]) + 273.15
        to = np.array(T_["t_oil"]) + 273.15
        ki = np.array(T_["ki"])
        turb = float(np.sum(np.exp((tt - 1123.0) / 45.0)))
        oil = float(np.sum(0.4 * np.exp((to - 408.0) / 12.0)))
        knk = float(np.sum(40.0 * np.maximum(0.0, ki - 0.85) ** 2))
        split[nm] = dict(turb=turb, oil=oil, knock=knk, thermal=turb + oil,
                         knock_pct=100.0 * knk / (turb + oil + knk))
    tb = split["baseline ECU"]["thermal"]
    cut_th = {nm: 100.0 * (1.0 - v["thermal"] / tb) for nm, v in split.items()}
    split_out = dict(knock_pct_base=_r(split["baseline ECU"]["knock_pct"], 1),
                     knock_pct_grade=_r(split["current-grade"]["knock_pct"], 1),
                     knock_pct_pred=_r(split["predictive (hand)"]["knock_pct"], 1),
                     thermal_grade=_r(split["current-grade"]["thermal"], 1),
                     thermal_pred=_r(split["predictive (hand)"]["thermal"], 1),
                     preview_thermal=_r(cut_th["predictive (hand)"] - cut_th["current-grade"], 2))

    from engine_env import make_grade_climb
    c720 = make_grade_climb(duration=720.0, dt=1.0)
    climb_m = float(np.sum(c720["v_mps"] * c720["grade"]))
    isa = 101.325 * (1.0 - 2.25577e-5 * climb_m) ** 5.25588     # standard atmosphere
    elev = dict(climb_m=_r(climb_m, 0), isa_kpa=_r(isa, 0), p_model=c720["p_baro"])

    return dict(trace=trace, sweep=sweep, eval=ev, base_med=_r(base, 1), split=split_out, elev=elev,
                base_fuel=_r(base_f, 0), ablation=ablation, curves=curves, agents=agents_, trade=trade,
                n_episodes=len(col("baseline ECU", "damage")))


def model_vs_car():
    R = _load("model_vs_data.json")
    out = {}

    L = R["load"]
    out["load"] = dict(points=[[_r(p["meas"], 2), _r(p["model"], 2), _r(p["rpm"], 0),
                                _r(p["map_kpa"], 1)] for p in L["points"]],
                       mape=_r(L["mape"], 2), wrong=_r(L["wrong_engine_mape"], 1),
                       n=len(L["points"]))

    B = R["boost"]

    def cdf(v, n=160):
        v = np.sort(np.asarray(v, dtype=float))
        q = np.linspace(0, 1, n)
        return [[_r(np.quantile(v, x), 1), _r(x, 3)] for x in q]
    out["boost"] = dict(car=cdf(B["logged"]), sim=cdf(B["model"]), raw=cdf(B["raw_sensor"]),
                        med_car=_r(B["median_logged"], 1), med_sim=_r(B["median_model"], 1),
                        med_raw=_r(B["median_raw"], 1), gap_sim=_r(B["gap_model_pct"], 1),
                        gap_raw=_r(B["gap_raw_pct"], 1), n_sim=B["n_model"],
                        n_car=B["n_logged"])

    E = R["enrichment"]
    out["enrich"] = dict(cells=[dict(rpm=c["rpm"], dwell=c["dwell"], n=c["n"],
                                     car=_r(c["meas"], 3), sim=_r(c["model"], 3),
                                     old=_r(c["meas_rows_axis"], 3)) for c in E["cells"]],
                         worst=_r(E["worst_abs"], 3), n=E["n"])

    Sp = R["spark"]
    out["spark"] = dict(points=[[_r(p["meas"], 1), _r(p["before"], 1), _r(p["after"], 1),
                                 _r(p["rpm"], 0), _r(p["map_kpa"], 1)]
                                for p in Sp["points"]],
                        before=dict((k, _r(v, 2)) for k, v in Sp["before"].items()),
                        after=dict((k, _r(v, 2)) for k, v in Sp["after"].items()),
                        a_before=Sp["spark_a_before"], a_after=Sp["spark_a_after"],
                        n=len(Sp["points"]))

    # Row 8's miss split into the coolant's share and the oil node's own (29 Sep).
    out["row8"] = {k: _r(v, 1) for k, v in R["row8"].items()}

    th = {}
    for key, name, step in (("drive10-20260918_233912.csv", "drive10", 3),
                            ("7475b5d7-20260908_142743.csv", "7475b5d7", 2)):
        T = R["thermal"][key]
        oc = np.array(T["oil_meas"], dtype=float)
        ec = np.array(T["ect_meas"], dtype=float)
        oc[oc == 0.0] = np.nan                      # AUDIT.md M8 placeholder
        ec[ec == 0.0] = np.nan
        om = np.array(T["oil_model"], dtype=float)
        em = np.array(T["ect_model"], dtype=float)
        ok_o, ok_e = np.isfinite(oc), np.isfinite(ec)
        th[name] = dict(t=_r(np.array(T["t"])[::step] / 60.0, 2),
                        oil_car=_r(oc[::step], 1), oil_sim=_r(om[::step], 1),
                        ect_car=_r(ec[::step], 1), ect_sim=_r(em[::step], 1),
                        oil_med=_r(np.median(om[ok_o] - oc[ok_o]), 1),
                        ect_med=_r(np.median(em[ok_e] - ec[ok_e]), 1),
                        oil_peak_car=_r(np.nanmax(oc), 0), oil_peak_sim=_r(np.nanmax(om), 0),
                        ect_peak_car=_r(np.nanmax(ec), 0), ect_peak_sim=_r(np.nanmax(em), 0),
                        minutes=_r(T["t"][-1] / 60.0, 0))
    out["thermal"] = th

    K = R["knock"]
    ki = np.array(K["ki"], dtype=float)
    rt = np.array(K["retard"], dtype=float)
    kx = np.arange(0.0, 1.64, 0.04)
    ky = np.arange(-2.0, 20.5, 0.5)
    H, _, _ = np.histogram2d(ki, rt, bins=[kx, ky])
    cells = [[_r(kx[i], 2), _r(ky[j], 1), int(H[i, j])]
             for i in range(H.shape[0]) for j in range(H.shape[1]) if H[i, j] > 0]
    # the car's median retard where the model says knock, and where it says none
    out["knock"] = dict(cells=cells, dx=0.04, dy=0.5, corr=_r(K["corr"], 3), n=K["n"],
                        above20=int((rt > 20).sum()),
                        ki_active=_r(K["ki_active_pct"], 1),
                        rt_active=_r(K["retard_active_pct"], 1),
                        med_rt_knock=_r(np.median(rt[ki > 0.85]), 2),
                        med_rt_quiet=_r(np.median(rt[ki <= 0.85]), 2))

    G = R["gearbox"]
    out["gear"] = dict(hist=G["hist"], edges=_r(G["edges"], 4), published=_r(G["published"], 3),
                       within=_r(G["within4_pct"], 1), n=G["n"], clamp=G["gear_channel_max"])

    V = R["envelope"]
    idx = np.random.default_rng(1).choice(len(V["flow"]), size=min(1800, len(V["flow"])),
                                          replace=False)
    out["env"] = dict(pts=[[_r(V["flow"][i], 4), _r(V["pr"][i], 3)] for i in sorted(idx)],
                      curve=[[_r(f, 4), _r(p, 3)] for f, p in zip(V["curve_flow"], V["curve_pr"])],
                      n=V["n"], shown=len(idx), pr_max=_r(V["pr_max"], 2))

    D = R["duty"]
    H = np.array(D["H"])
    re_, me_ = D["rpm_edges"], D["map_edges"]
    out["duty"] = dict(cells=[[_r(re_[i], 0), _r(me_[j], 1), int(H[i, j])]
                              for i in range(H.shape[0]) for j in range(H.shape[1])
                              if H[i, j] > 0],
                       drpm=_r(re_[1] - re_[0], 1), dmap=_r(me_[1] - me_[0], 2),
                       scen_rpm=_r(D["scenario_rpm"], 0), scen_map=_r(D["scenario_map"], 0),
                       frac=_r(D["frac_logs_at_or_above_scenario"], 1), n=D["n"],
                       over120=_r(D["load_over_120_pct"], 1),
                       # drives that did not log `Relative air filling` (drive B) carry
                       # no median; they are left out rather than read as zero
                       load_med_lo=_r(min(v for v in D["load_median_by_drive"].values() if v is not None), 0),
                       load_med_hi=_r(max(v for v in D["load_median_by_drive"].values() if v is not None), 0))

    KS = R["knock_sampling"]
    out["knock_s"] = dict(fresh=min(KS["fresh_target"], KS["fresh_actual"]),
                          minutes=_r(KS["minutes"], 0),
                          every_s=_r(60.0 * KS["minutes"] / min(KS["fresh_target"], KS["fresh_actual"]), 0),
                          within1=_r(KS["paired_within_1s_pct"], 0),
                          late_pct=_r(100.0 - KS["paired_within_1s_pct"], 0))

    out["lit"] = [dict(name=r["name"], value=_r(r["value"], 1), unit=r["unit"],
                       lo=r["lo"], hi=r["hi"], ok=r["ok"], basis=r["basis"])
                  for r in R["literature"]]
    out["lit_ok"] = sum(r["ok"] for r in R["literature"])
    out["lit_n"] = len(R["literature"])
    for tag, basis in (("lit_l", "literature"), ("lit_c", "our car")):
        rows_b = [r for r in R["literature"] if r["basis"] == basis]
        out[tag + "_ok"], out[tag + "_n"] = sum(r["ok"] for r in rows_b), len(rows_b)
    return out


def training_roads():
    """The roads train.py draws from, as check_roads.py drove them."""
    path = os.path.join(RES, "training_roads.json")
    if not os.path.exists(path):
        raise SystemExit("results/training_roads.json missing -- run check_roads.py")
    T = _load("training_roads.json")
    pick = {}
    for r in T["roads"]:
        pick.setdefault(r["family"], r)
    fams = ["locked", "single", "rolling", "double", "flat"]
    count = {f: sum(r["family"] == f for r in T["roads"]) for f in fams}
    return dict(examples=[dict(family=f, elev=pick[f]["elev_m"], grade=pick[f]["grade"],
                               gmax=_r(100 * pick[f]["grade_max"], 1))
                          for f in fams if f in pick],
                roads=[dict(family=r["family"], peak=_r(r["peak_c"], 0),
                            gmin=_r(100 * r["grade_min"], 1), gmax=_r(100 * r["grade_max"], 1),
                            r=_r(r["neutral_r"], 4))
                       for r in T["roads"]],
                count=count, n=T["n"], binding=T["binding"],
                worst_r=_r(T["worst_neutral_r"], 4), worst_err=_r(T["worst_p95_err"], 3),
                tol=T["tolerance"], step_s=5)


def calibration():
    """The 28 September derivation, before against after (compare_calibration.py)."""
    C = _load("calibration_comparison.json")
    import derived
    out = {}
    # the oil-node structures, each fitted with drive10 held out (a RECORD)
    out["structures"] = [dict(name=o["structure"].replace("(chosen)", "").strip(),
                              chosen="(chosen)" in o["structure"], rmse=o["drive10_rmse"],
                              note=o["note"]) for o in C["oil_structures"]]
    st = out["structures"]
    out["struct_shipped"] = st[0]["rmse"]
    out["struct_chosen"] = next(o["rmse"] for o in st if o["chosen"])
    best = min(st, key=lambda o: o["rmse"])
    out["struct_best"], out["struct_best_name"] = best["rmse"], best["name"]
    out["old_frac_pct"] = _r(100 * C["thermal"]["before"]["frac_fuel_to_oil"], 1)
    # every usable drive: RMSE with the old constants, fitted, and held out
    out["per_drive"] = [dict(drive=d["drive"].split("-")[0],
                             oil=[_r(d["shipped"]["oil"], 2), _r(d["fitted"]["oil"], 2), _r(d["held_out"]["oil"], 2)],
                             ect=[_r(d["shipped"]["coolant"], 2), _r(d["fitted"]["coolant"], 2),
                                  _r(d["held_out"]["coolant"], 2)])
                        for d in C["thermal"]["per_drive"]]
    tr = C["thermal"]["traces"]["7475b5d7-20260908_142743.csv"]
    out["pull"] = dict(before=_r(np.nanmax(tr["before_oil"]), 1), after=_r(np.nanmax(tr["after_oil"]), 1),
                       car=_r(np.nanmax(tr["car_oil"]), 1))
    out["rows"] = [dict(name=r["name"], before=_r(r["before"], 1), after=_r(r["after"], 1),
                        lo=r["lo"], hi=r["hi"], inside=r["inside"]) for r in C["rows"]]
    out["t_stat_c"] = _r(derived.get("thermal", "t_stat_open") - 273.15, 1)
    # the premise at each step of the change (a RECORD, measured once per step)
    out["steps"] = C["premise_steps"]
    out["steps_last_baseline"] = C["premise_steps"][-1]["baseline"]
    out["steps_pv_lo"] = min(x["preview_vs_grade"] for x in C["premise_steps"])
    out["steps_pv_hi"] = max(x["preview_vs_grade"] for x in C["premise_steps"])
    # drive B against the ceiling, per 200 rpm band: the car's HIGHEST genuine
    # full-throttle reading, because a ceiling is judged against the top of what
    # the car did, not against a transient's spool-up
    B = C["boost"]
    r = np.array(B["car_wot"]["rpm"], float)
    q = np.array(B["car_wot"]["map_kpa"], float)
    mr = np.array([m["rpm"] for m in B["model_after"]], float)
    ma = np.array([m["map_kpa"] for m in B["model_after"]], float)
    mb = np.array([m["map_kpa"] for m in B["model_before"]], float)
    bands = []
    for lo in range(1400, 4400, 200):
        k = (r >= lo) & (r < lo + 200)
        if not k.any():
            continue
        top = float(q[k].max())
        now, bef = float(np.interp(lo + 100, mr, ma)), float(np.interp(lo + 100, mr, mb))
        bands.append(dict(lo=lo, n=int(k.sum()), car=_r(top, 1), now=_r(now, 1), before=_r(bef, 1),
                          now_pct=_r(100 * (now / top - 1), 1), before_pct=_r(100 * (bef / top - 1), 1)))
    low = [b for b in bands if 1600 <= b["lo"] < 2000]
    high = [b for b in bands if b["lo"] >= 2000]
    out["boost"] = dict(car=[[_r(a, 0), _r(b, 1)] for a, b in zip(r, q)],
                        before=[[m["rpm"], _r(m["map_kpa"], 1)] for m in B["model_before"]],
                        after=[[m["rpm"], _r(m["map_kpa"], 1)] for m in B["model_after"]],
                        bands=bands, n=len(r), shift=_r(B["car_wot"].get("rpm_shift_median"), 0),
                        low_worst=min(b["now_pct"] for b in low), low_best=max(b["now_pct"] for b in low),
                        high_lo=min(b["now_pct"] for b in high), high_hi=max(b["now_pct"] for b in high),
                        before_2000=min(b["before_pct"] for b in high if b["lo"] < 2400),
                        top_readings=[B["bins"][-2]["readings"], B["bins"][-1]["readings"]])
    return out


def generality():
    """The H/tau sweep, generality_test.py, with both comparators."""
    path = os.path.join(RES, "generality.json")
    if not os.path.exists(path):
        raise SystemExit("results/generality.json missing -- run generality_test.py")
    G = _load("generality.json")
    rnd = lambda rows: [{k: (_r(v, 4) if isinstance(v, float) else v) for k, v in x.items()} for x in rows]
    h2 = [x for x in G["h2"] if x["binds"]]
    vs_g = [x["predictive"] - x["grade"] for x in h2]
    vs_r = [x["predictive"] - x["reactive"] for x in h2]
    h2b = [x for x in G["h2b"] if x["binds"]]
    return dict(h1=rnd(G["h1"]), h2=rnd(G["h2"]), h2b=rnd(G["h2b"]), exh=_r(G["exh_gps"], 1),
                horizon=G["horizon_s"], n_bind=len(h2), n_all=len(G["h2"]),
                vs_grade_lo=_r(min(vs_g), 2), vs_grade_hi=_r(max(vs_g), 2),
                vs_grade_absmax=_r(max(abs(v) for v in vs_g), 2),
                vs_react_lo=_r(min(vs_r), 1), vs_react_hi=_r(max(vs_r), 1),
                h2b_grade_max=_r(max(x["predictive"] - x["grade"] for x in h2b), 1),
                h1_grade_max=_r(max(abs(x["predictive"] - x["grade"]) for x in G["h1"]), 2))


def meta():
    def git(*a):
        try:
            return subprocess.check_output(["git", *a], cwd=HERE, text=True).strip()
        except Exception:
            return "?"
    import pandas as pd
    M = pd.read_csv(os.path.join(HERE, "data", "manifest.csv"))
    # 29 September 2026: the page said "@ c628564" while it was built from a
    # working tree 58 files ahead of it. Say so when the tree is not clean.
    dirty = git("status", "--porcelain", "--untracked-files=no") not in ("", "?")
    return dict(branch=git("branch", "--show-current"),
                commit=git("rev-parse", "--short", "HEAD") + (" + uncommitted changes" if dirty else ""),
                built=date.today().isoformat(),
                drives=len(M), minutes=_r(M.duration_min.sum(), 1))


FMT = re.compile(r"\{\{\s*([a-zA-Z0-9_.\-]+)\s*(?:\|\s*([^}\s]+))?\s*\}\}")


def _lookup(data, path):
    cur = data
    for part in path.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    return cur


def render(template, data):
    missing = []

    def sub(m):
        try:
            v = _lookup(data, m.group(1))
        except (KeyError, IndexError, ValueError):
            missing.append(m.group(1))
            return "??"
        f = m.group(2)
        if f is None:
            return str(v)
        if f == ",":
            return f"{int(v):,}".replace(",", " ")    # thin-space thousands
        s = format(float(v), f)
        if float(s) == 0.0:                          # no "−0.0"
            s = s.lstrip("+-")
            s = ("+" if f.startswith("+") else "") + s
        return s.replace("-", "−")                   # a real minus sign
    out = FMT.sub(sub, template)
    if missing:
        raise SystemExit("unknown tokens in the template: " + ", ".join(sorted(set(missing))))
    return out


def main():
    data = dict(meta=meta(), pd=phase_d(), mc=model_vs_car(), roads=training_roads(),
                cal=calibration(), gen=generality())
    # the ceiling against drive B in the band the locked climb runs in
    b = data["cal"]["boost"]
    rpm = data["mc"]["duty"]["scen_rpm"]
    b["at_climb"] = next(x["now_pct"] for x in b["bands"] if x["lo"] <= rpm < x["lo"] + 200)
    with open(os.path.join(PAGE, "template.html"), encoding="utf-8") as fh:
        tpl = fh.read()
    html = render(tpl, data)
    blob = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    html = html.replace("/*__DATA__*/null", blob)
    out = os.path.join(PAGE, "index.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"wrote {os.path.relpath(out, HERE)}  ({len(html) / 1024:.0f} KB, "
          f"data {len(blob) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()

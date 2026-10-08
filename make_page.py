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


# The agents the page shows: results/agents/<AGENT_SET>/, written by
# record_agents.py, and the same set run_results.py scores into phase_d_*.
AGENT_SET = "terrain_dt1"


def _load(name):
    with open(os.path.join(RES, name)) as fh:
        return json.load(fh)


def _minus(x):
    """A signed whole number with a real minus sign, as the page writes them."""
    return f"{x:+.0f}".replace("-", "−")


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
        ev.append(dict(name=n.split("/")[-1], kind=kind(n), med=_r(me, 1),
                       q1=_r(q1, 1), q3=_r(q3, 1), worst=_r(d.max(), 1),
                       fuel=_r(np.median(col(n, "fuel")), 0),
                       fuel_pct=_r(100 * (np.median(col(n, "fuel")) / base_f - 1), 2),
                       peak=_r(col(n, "peak_turb").max(), 1),
                       cut=_r(100 * (1 - me / base), 4)))     # 4, not 2: the chart rounds once, to 1
    # Differences from the UNROUNDED cuts, so the page and results/*.txt agree
    # to the last printed digit.
    cut = {n.split("/")[-1]: 100.0 * (1.0 - float(np.median(col(n, "damage"))) / base)
           for n in order}
    # 8 October: current-grade is the line every policy is compared with (Ghassan,
    # 7 October: "change the comparing line to the current grade"). The cut stays
    # against the baseline, as evaluate.py defines it; the charts draw each
    # policy's margin over current-grade, and its fuel against current-grade's.
    cg = next(e for e in ev if e["name"] == "current-grade")
    cg_fuel = float(np.median(col(next(n for n in order if n.endswith("current-grade")), "fuel")))
    for e in ev:
        e["over_grade"] = _r(cut[e["name"]] - cut["current-grade"], 4)
        e["fuel_vs_grade"] = _r(100.0 * (e["fuel"] / cg_fuel - 1.0), 2)
    grade_fuel_pct = cg["fuel_pct"]
    fuel = {n.split("/")[-1]: 100.0 * (float(np.median(col(n, "fuel"))) / base_f - 1.0)
            for n in order}
    seeds = [dict(seed=s, s=_r(cut[f"sighted_seed{s}"], 2), b=_r(cut[f"blind_seed{s}"], 2),
                  d=_r(cut[f"sighted_seed{s}"] - cut[f"blind_seed{s}"], 4),
                  fs=_r(fuel[f"sighted_seed{s}"], 2), fb=_r(fuel[f"blind_seed{s}"], 2))
             for s in sorted({int(k.split("seed")[-1]) for k in cut if "_seed" in k})
             if f"sighted_seed{s}" in cut and f"blind_seed{s}" in cut]
    dd = np.array([x["d"] for x in seeds])
    sd = float(dd.std(ddof=1))
    from scipy import stats as _st
    half = float(_st.t.ppf(0.975, len(dd) - 1)) * sd / np.sqrt(len(dd))    # was 2.776, t(0.975, 4)
    from scipy import stats
    s_med = float(np.median([cut[f"sighted_seed{x['seed']}"] for x in seeds]))      # unrounded, as results/*.txt
    ablation = dict(seeds=seeds, mean=_r(dd.mean(), 4), median=_r(np.median(dd), 4),
                    sd=_r(sd, 4), lo=_r(dd.mean() - half, 4), hi=_r(dd.mean() + half, 4),
                    p_t=_r(stats.ttest_1samp(dd, 0.0).pvalue, 2),
                    p_w=_r(stats.wilcoxon(dd).pvalue, 2),
                    grade_cut=cut["current-grade"], predictive_cut=cut["predictive (hand)"],
                    sighted_median=_r(s_med, 1),
                    agent_over_grade=_r(s_med - cut["current-grade"], 1),
                    within=int((np.abs(dd) <= 0.75).sum()), n=len(dd),
                    pred_minus_grade=_r(cut["predictive (hand)"] - cut["current-grade"], 2))
    lo_, hi_ = ablation["lo"], ablation["hi"]
    # 30 September 2026, agreed at the merge: an interval that spans zero is
    # INCONCLUSIVE, never "preview adds nothing". Ten pairs cannot tell no
    # effect from one a few points wide.
    ablation["verdict"] = ("Inconclusive: the interval spans zero, so these pairs cannot tell no "
                           "effect from a small one." if lo_ <= 0 <= hi_
                           else "Preview helps: the interval excludes zero." if lo_ > 0
                           else "Preview hurts: the interval excludes zero.")
    s_med_b = float(np.median([cut[f"blind_seed{x['seed']}"] for x in seeds]))
    ablation["blind_median"] = _r(s_med_b, 1)
    ablation["blind_over_grade"] = _r(s_med_b - cut["current-grade"], 1)
    g_ = cut["current-grade"]
    if lo_ <= 0 <= hi_:
        sg = lambda v: f"{v:+.1f}".replace("-", "−")
        ablation["reading"] = (
            f"The blinded agents beat current-grade by {sg(s_med_b - g_)} points and the sighted ones by "
            f"{sg(s_med - g_)}, so the gain over the hand-written policy does not need the preview "
            f"channel. Whether preview adds anything on top of it is inconclusive at this training "
            f"budget. That is one point on the H/τ curve, not the curve.")
    else:
        ablation["reading"] = (
            f"The interval excludes zero: preview {'helps' if lo_ > 0 else 'hurts'} a learned policy on this "
            f"scenario by {abs(float(dd.mean())):.1f} points on average.")

    # 29 September 2026: the sentences about which agents beat which policy were
    # typed, and went false when the agents were re-scored on the derived plant
    # ("all ten beat every hand-written policy" -- three do not). They are
    # computed now, and the claims the text makes without a number are asserted.
    hand = [n for n in order if kind(n) == "hand"]
    agents = [n.split("/")[-1] for n in order if kind(n) != "hand"]
    best_hand = max(cut[n] for n in hand)
    below = [a for a in agents if cut[a] <= best_hand]

    def names_(xs):
        xs = [shortish(x) for x in xs]
        return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]

    def shortish(n):
        return n.replace("sighted_seed", "sighted ").replace("blind_seed", "blinded ")

    def seeds_(xs):
        return names_([f"__{x}" for x in xs]).replace("__", "")

    beat_reactive = sum(cut[a] > cut["reactive"] for a in agents)
    mn = min(agents, key=lambda a: cut[a])
    if not below:
        sentence = (f"All {len(agents)} trained agents beat every hand-written policy: the weakest, "
                    f"{shortish(mn)}, cuts {cut[mn]:.1f} % against current-grade's {best_hand:.1f} %.")
    else:
        sentence = (f"{len(agents) - len(below)} of {len(agents)} trained agents beat every hand-written "
                    f"policy. The other {len(below)}, {names_(below)}, cut {min(cut[a] for a in below):.1f}"
                    f"–{max(cut[a] for a in below):.1f} %, no more than current-grade's {best_hand:.1f} %.")
    sentence += (" Every agent beats the reactive policy and the baseline." if beat_reactive == len(agents)
                 else f" {beat_reactive} of {len(agents)} beat the reactive policy.")
    agents_ = dict(n=len(agents), beat=len(agents) - len(below), n_below=len(below),
                   best_hand=_r(best_hand, 1), sentence=sentence)

    # Damage against fuel: which way does each seed's tie run? (29 Sep: the
    # sentences were typed for five seeds and went false on the retrain.)
    fuel_less = [a for a in agents if fuel[a] < 0]
    fuel_more = [fuel[a] for a in agents if fuel[a] >= 0]
    both_s = [x["seed"] for x in seeds if x["d"] > 0.75 and x["fs"] <= x["fb"]]
    both_b = [x["seed"] for x in seeds if x["d"] < -0.75 and x["fb"] <= x["fs"]]
    # Against current-grade, the comparing line (8 October): which agents beat it
    # on damage AND fuel. Current-grade pays for its protection in fuel.
    evd = {e["name"]: e for e in ev}
    both_cg = [a for a in agents if evd[a]["over_grade"] > 0 and evd[a]["fuel_vs_grade"] < 0]
    take = (f"Against current-grade, {len(both_cg)} of {len(agents)} agents cut more damage and burn less fuel; "
            f"current-grade itself burns {grade_fuel_pct:+.1f} % against the baseline, because it protects by "
            f"enriching and pulling boost. Against the baseline, {len(fuel_less)} of {len(agents)} agents burn "
            f"less fuel" + (f" and the rest {min(fuel_more):.1f}–{max(fuel_more):.1f} % more." if fuel_more else "."))
    cap = (f"A tie that ran straight up, more damage cut for the same fuel, would be a preview effect. Of "
           f"the {len(seeds)} pairs, the sighted agent is better on both damage and fuel in {len(both_s)}"
           + (f" (seed{'s' if len(both_s) > 1 else ''} {seeds_(both_s)})" if both_s else "") + f", the blinded one in {len(both_b)}"
           + (f" (seed{'s' if len(both_b) > 1 else ''} {seeds_(both_b)})" if both_b else "")
           + f", and the other {len(seeds) - len(both_s) - len(both_b)} trade one for the other or tie.")
    trade = dict(take=take, cap=cap)

    # From results/agents/ (record_agents.py), which is committed -- until 29 Sep
    # this read runs/, which is gitignored, so nobody else could rebuild it.
    curves = []
    for f in sorted(glob.glob(os.path.join(RES, "agents", AGENT_SET, "*_seed*", "curve.csv"))):
        tag = os.path.basename(os.path.dirname(f))
        d = np.loadtxt(f, delimiter=",", skiprows=1, usecols=(0, 1, 2))
        curves.append(dict(run=tag, blind=tag.startswith("blind"), ret=_r(d[:, 1], 1)))
    curve_eps = max((len(c["ret"]) for c in curves), default=0)

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
                curve_eps=curve_eps, curve_runs=len(curves), rec=agent_records(),
                n_episodes=len(col("baseline ECU", "damage")))


def agent_records():
    """Read off the evaluation records (record_agents.py): how far the agents
    advance spark and how close that takes the modelled knock integral to the
    damage knee, and every episode an agent does worse than the baseline."""
    import evaluate as E
    root = os.path.join(RES, "agents", AGENT_SET)
    # From eval_summary.json, never eval_record.npz: the records are not in git
    # (29 Sep), so the page must build from what is committed.
    with open(os.path.join(root, "baseline_ECU", "eval_summary.json")) as fh:
        B = json.load(fh)
    base_dmg = B["summary"]["damage"]["median"]
    out = dict(ki_base=_r(B["engine_on_climb"]["ki_p95"], 2), sp_base=_r(B["engine_on_climb"]["spark_median"], 1))
    trims, kis = [], []
    w_life = np.array([e[1][2] for e in E.EPISODES])
    bad = []
    for d in sorted(glob.glob(os.path.join(root, "*_seed*"))):
        with open(os.path.join(d, "eval_summary.json")) as fh:
            S_ = json.load(fh)
        trims.append(S_["engine_on_climb"]["spark_trim_median"])
        kis.append(S_["engine_on_climb"]["ki_p95"])
        eps = S_["episodes"]
        worse = [i for i, e in enumerate(eps) if e["damage"] > base_dmg]
        if worse:
            # 8 October: the page said the reward "lets it trade component life
            # for fuel". The records say otherwise -- on those episodes it burns
            # MORE fuel than the baseline too, and its return goes negative.
            fuel_pct = [100.0 * (eps[i]["fuel"] / B["episodes"][i]["fuel"] - 1.0) for i in worse]
            good = [i for i in range(len(eps)) if i not in worse]
            bad.append(dict(agent=os.path.basename(d), n=len(worse), episodes=worse,
                            worst=_r(max(eps[i]["damage"] for i in worse), 0),
                            peak=_r(max(eps[i]["peak_turb"] for i in worse), 0),
                            w_life_max=_r(max(w_life[i] for i in worse), 3),
                            lowest=sorted(worse) == sorted(np.argsort(w_life)[:len(worse)].tolist()),
                            fuel_lo=_r(min(fuel_pct), 1), fuel_hi=_r(max(fuel_pct), 1),
                            ret_bad_max=_r(max(eps[i]["ret"] for i in worse), 0),
                            ret_good_min=_r(min(eps[i]["ret"] for i in good), 0) if good else None))
    # knock_margin.py: the same agents with spark advance forbidden (a diagnostic)
    km_path = os.path.join(root, "knock_margin.json")
    if not os.path.exists(km_path):
        raise SystemExit(f"{km_path} missing -- run knock_margin.py")
    with open(km_path) as fh:
        K = json.load(fh)["summary"]
    out["km"] = dict(sighted=_r(K["sighted_cut"], 1), sighted_orig=_r(K["sighted_cut_orig"], 1),
                     blind=_r(K["blind_cut"], 1), blind_orig=_r(K["blind_cut_orig"], 1),
                     grade=_r(K["grade_cut"], 1), beat=K["beat_grade"], n=K["n"],
                     og=_r(K["over_grade_median"], 1), og_orig=_r(K["over_grade_median_orig"], 1),
                     ki_lo=_r(K["ki_p95_lo"], 2),
                     ki_hi=_r(K["ki_p95_hi"], 2), abl=_r(K["ablation"]["mean"], 2),
                     abl_lo=_r(K["ablation"]["ci95"][0], 1), abl_hi=_r(K["ablation"]["ci95"][1], 1),
                     abl_pw=_r(K["ablation"]["p_wilcoxon"], 2))
    with open(km_path) as fh:
        KA = json.load(fh)["agents"]
    out["km_agents"] = [dict(name=n, preview=v["preview"], cut=_r(v["cut"], 2), cut_orig=_r(v["cut_orig"], 2),
                             ki=_r(v["ki_p95_climb"], 3), fuel=_r(v["fuel_pct"], 2))
                        for n, v in KA.items()]

    # What the actuators did on the climb (eval_summary.json) and one episode
    # step by step (episode_trace.json) -- 30 Sep, the page's action charts.
    acts = ("spark trim (deg)", "lambda trim", "boost trim (kPa)", "fan duty", "pump duty")
    keys = ("spark", "lam", "boost", "fan", "pump")
    actions, neutral = [], None
    for tag in ["baseline_ECU", "current-grade"] + [os.path.basename(d) for d in sorted(
            glob.glob(os.path.join(root, "*_seed*")), key=lambda p: ("blind" in p, int(p.split("seed")[-1])))]:
        with open(os.path.join(root, tag, "eval_summary.json")) as fh:
            A_ = json.load(fh)["actions"]
        neutral = neutral or {k: _r(A_[a]["neutral"], 4) for k, a in zip(keys, acts)}
        actions.append(dict(name=tag.replace("_", " ") if tag == "baseline_ECU" else tag,
                            kind="hand" if "seed" not in tag else ("sighted" if tag.startswith("sighted") else "blinded"),
                            **{k: [_r(A_[a]["climb"][q], 4) for q in ("p5", "p50", "p95")] for k, a in zip(keys, acts)}))
    out["actions"], out["neutral"] = actions, neutral
    ep_path = os.path.join(root, "episode_trace.json")
    if not os.path.exists(ep_path):
        raise SystemExit(f"{ep_path} missing -- run record_agents.py {AGENT_SET} --report-only")
    with open(ep_path) as fh:
        out["ep1"] = json.load(fh)
    # 8 October: blinded seed 6 on its worst and its best frozen episode, beside
    # the baseline (record_extracts.py, a committed extract of the records).
    b6_path = os.path.join(root, "bad_episode_trace.json")
    if not os.path.exists(b6_path):
        raise SystemExit(f"{b6_path} missing -- run record_extracts.py")
    with open(b6_path) as fh:
        out["b6"] = json.load(fh)
    b6 = out["b6"]
    b6["agent_name"] = b6["agent"].replace("blind_seed", "Blinded seed ").replace("sighted_seed", "Sighted seed ")
    for e in b6["episodes"].values():
        e["episode_n"], e["w_life"] = e["episode"] + 1, e["weights"][2]
    with open(os.path.join(root, b6["agent"], "eval_summary.json")) as fh:
        a_eps = json.load(fh)["episodes"]
    wi = b6["episodes"]["worst"]["episode"]
    b6["fuel_worst_pct"] = _r(100.0 * (a_eps[wi]["fuel"] / B["episodes"][wi]["fuel"] - 1.0), 1)
    # against current-grade, the comparing line (8 October)
    with open(os.path.join(root, "current-grade", "eval_summary.json")) as fh:
        g_eps = json.load(fh)["episodes"]
    b6["fuel_worst_vs_grade"] = _r(100.0 * (a_eps[wi]["fuel"] / g_eps[wi]["fuel"] - 1.0), 1)
    b6["grade_damage"] = _r(g_eps[wi]["damage"], 0)
    # The caption says the retard is no knock response: past the one-step spike
    # every policy shows at the grade step, the worst episode's knock integral
    # stays under the 0.85 knee.
    t_ = np.array(b6["t"])
    after = t_ > t_[int(np.argmax(np.array(b6["grade"]) > 0))] + 4
    if max(np.array(b6["episodes"]["worst"]["ki"])[after]) >= 0.85:
        raise SystemExit("the seed-6 caption no longer holds (knock integral past 0.85) -- reword template.html")
    # What the charts show, counted: how many agents sit below the baseline's
    # own setting on the climb, and how much more the commands change per step
    # on the flat than on the climb (episode 1).
    ag = [a for a in actions if a["kind"] != "hand"]
    below = {k: sum(a[k][1] < neutral[k] - 1e-3 for a in ag) for k in keys}
    # ...and against current-grade, the comparing line (8 October): its own
    # median setting on the climb, lever by lever.
    cg_a = next(a for a in actions if a["name"] == "current-grade")
    out["cg_setting"] = {k: cg_a[k][1] for k in keys}
    out["vs_cg"] = dict(n=len(ag), **{f"{k}_above": sum(a[k][1] > cg_a[k][1] + 1e-3 for a in ag) for k in keys},
                        **{f"{k}_below": sum(a[k][1] < cg_a[k][1] - 1e-3 for a in ag) for k in keys})
    v_ = out["vs_cg"]
    if not (v_["spark_above"] == v_["fan_below"] == v_["pump_below"] == len(ag)):
        raise SystemExit("the actions text no longer holds (every agent advances spark past current-grade "
                         "and cools less) -- reword template.html")
    g_ = np.array(out["ep1"]["grade"])
    ratios = []
    for k in keys:
        fl, cl = [], []
        for p in out["ep1"]["policies"].values():
            if p["kind"] == "hand":
                continue
            d = np.abs(np.diff(np.array(p[k])))
            fl.append(d[g_[1:] <= 0].mean())
            cl.append(d[g_[1:] > 0].mean())
        ratios.append(float(np.median(fl)) / max(float(np.median(cl)), 1e-9))
    out["beh"] = dict(n=len(ag), fan_below=below["fan"], pump_below=below["pump"], lam_below=below["lam"],
                      boost_below=below["boost"],
                      fan_lo=_r(min(a["fan"][1] for a in ag), 2), fan_hi=_r(max(a["fan"][1] for a in ag), 2),
                      pump_lo=_r(min(a["pump"][1] for a in ag), 2), pump_hi=_r(max(a["pump"][1] for a in ag), 2),
                      chatter_lo=_r(min(ratios), 1), chatter_hi=_r(max(ratios), 1))
    # The action charts' prose states these without a number; a retrain that
    # breaks one must stop the build, not ship a false sentence (mistake 22).
    b_ = out["beh"]
    assert min(trims) > 2.0, "text: every agent holds spark well past the baseline on the climb"
    assert min(below[k] for k in ("fan", "pump", "lam", "boost")) > len(ag) / 2, \
        "text: the agents protect with spark, mixture and boost and cool less than the baseline"
    assert b_["chatter_lo"] > 2.0, "text: commands change more on the flat and settle on the climb"
    out.update(trim_lo=_r(min(trims), 1), trim_hi=_r(max(trims), 1), ki_lo=_r(min(kis), 2),
               ki_hi=_r(max(kis), 2), base_dmg=_r(base_dmg, 0), n_bad=len(bad), bad=bad)
    if bad:
        b = max(bad, key=lambda x: x["worst"])
        out["bad_sentence"] = (
            f"{b['agent'].replace('blind_seed', 'Blinded seed ').replace('sighted_seed', 'Sighted seed ')} "
            f"does more damage than the baseline on {b['n']} of the twenty episodes (worst {b['worst']:.0f} "
            f"against {base_dmg:.0f}, turbine {b['peak']:.0f} °C), and they are "
            + ("exactly the five" if b["lowest"] and b["n"] == 5 else f"the {b['n']}" if b["lowest"] else "episodes")
            + f" whose weight on component life is lowest (at most {b['w_life_max']:.3f}). "
            + f"It is not trading life for fuel: on those episodes it also burns {b['fuel_lo']:.1f}–"
            f"{b['fuel_hi']:.1f} % more fuel than the baseline, and its return is negative (at most "
            f"{_minus(b['ret_bad_max'])}, against at least {_minus(b['ret_good_min'])} on its other episodes). Its "
            "per-step records show it retarding spark on the climb, where on its other episodes it advances. "
            + (f"{len(bad) - 1} other agent" + ("s" if len(bad) > 2 else "") + " also do." if len(bad) > 1
               else "No other agent does."))
        if not (b["fuel_lo"] > 0 and b["ret_bad_max"] < 0 < b["ret_good_min"]):
            raise SystemExit("the bad-agent sentence no longer holds (fuel or return) -- reword make_page.py")
        out["bad_worst"] = dict(name=b["agent"].replace("blind_seed", "blinded seed ")
                                .replace("sighted_seed", "sighted seed "), n=b["n"],
                                fuel_lo=b["fuel_lo"], fuel_hi=b["fuel_hi"])
    else:
        out["bad_sentence"] = "No agent does more damage than the baseline on any of the twenty episodes."
    return out


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


def validation():
    """7-8 October 2026: the validation plan's diagnostics, the per-step
    records and the damage constants, for the Validation section. Every number
    is read from a results file a script wrote: conditions_test.py,
    damage_constants.py, timestep_study.py, car_spark_boost.py and
    training_roads.py; the field counts from step_record.py itself."""
    import step_record
    ct, dc = _load("conditions_test.json"), _load("damage_constants.json")
    ts, sp, rd = _load("timestep_study.json"), _load("car_spark_boost.json"), _load("train_roads_check.json")
    cond = []
    for name, s in ct["summary"].items():
        if s.get("grade") is None:
            continue
        m = list(s["margins"].values())
        cond.append(dict(name=name, grade=_r(100 * s["grade"], 2), base_peak=s["base_peak"],
                         grade_cut=s["grade_cut"], sighted=s["sighted_margin"], blind=s["blind_margin"],
                         lo=min(m), hi=max(m), beat=s["beat_grade"], n=s["n_agents"],
                         short_grade=s["short_grade"], short_agents=s["short_agents_median"],
                         abl=s["ablation_mean"], abl_lo=s["ablation_lo"], abl_hi=s["ablation_hi"],
                         spark_s=s["acts_sighted"][0], spark_b=s["acts_blind"][0]))
    by = {c["name"].split(",")[0]: c for c in cond}
    # Each agent's own climb spark at 25 C, from the committed rows (median of
    # its episodes): the group medians hide the agents that retard.
    c25 = next(c for c in ct["conditions"] if c[0].startswith("25 C"))
    sp25 = {}
    for r in ct["rows"]:
        if "_seed" in r["ref"] and r["t_amb_k"] == c25[1] and r["p_kpa"] == c25[2]:
            sp25.setdefault(r["ref"], []).append(r["act_climb"][0])
    pretty = lambda t: t.replace("sighted_seed", "sighted seed ").replace("blind_seed", "blinded seed ")
    r25 = sorted((float(np.median(v)), t) for t, v in sp25.items())[:2]
    # The page says these two are also the two that do the most damage there
    # (about twice the baseline's); check it rather than assume it.
    dmg25 = {}
    for r in ct["rows"]:
        if r["t_amb_k"] == c25[1] and r["p_kpa"] == c25[2]:
            dmg25.setdefault(r["ref"], []).append(r["damage"])
    base25 = float(np.median(dmg25["baseline ECU"]))
    worst2 = sorted((t for t in dmg25 if "_seed" in t), key=lambda t: -float(np.median(dmg25[t])))[:2]
    if sorted(worst2) != sorted(t for _, t in r25) or min(float(np.median(dmg25[t])) for t in worst2) < 1.7 * base25:
        raise SystemExit("the 25 C sentence no longer holds: the deepest retarders are not the two agents "
                         "doing about twice the baseline's damage -- reword template.html")
    short = [c["short_grade"] for c in cond if c["short_grade"] >= 100]
    thin = [c for c in cond if "kPa" in c["name"]]
    knees = {k.split()[0]: _r(v - 273.15, 1) for k, v in dc["constants"][1]["mapped"].items()}
    rows = [dict(name=k, **v) for k, v in dc["summary"].items()]
    abl_knock = next(r for r in rows if r["name"].startswith("knee") and "knock" not in r["name"]
                     and r["ablation_lo"] > 0)
    dt1, dt2 = ts["u_num_vs_finest"], ts["dt2"]
    c2 = dt2["cuts"]
    allc, climb = sp["cells"]["all, 140-240 kPa"], next(v for k, v in sp["cells"].items() if "climb" in k)
    # 8 October: the rest of the 7 October diagnostics, drawn rather than only
    # quoted. damage_robustness.py: the nine rulers; timestep_study.py: the
    # thermal step's convergence; validation_numbers.py: what one step of each
    # channel's resolution moves; conditions_traces.json: the recorded episodes.
    rb = _load("damage_robustness.json")
    robust = [dict(name=k, **v) for k, v in rb["summary"].items()]
    # Every damage formula tried: the nine rulers plus the damage constants'
    # own (less the two that repeat a ruler). The summary tiles say all twenty
    # agents beat current-grade under each, and that the formulas whose
    # ablation interval clears zero are the ones that weigh the untested knock
    # term more. Check both, so a new ruler cannot leave a false sentence.
    formulas = robust + [dict(name=k, **v) for k, v in dc["summary"].items()
                         if k not in ("as published", "as published, no knock term")]
    exceptions = sorted(f["name"] for f in formulas if not f["ablation_lo"] <= 0 <= f["ablation_hi"])
    knee_hi = next(k for k in dc["summary"] if k.startswith("knee") and "1050" in k and "knock" not in k)
    if not all(f["beat_grade"] == f["n"] for f in formulas) or set(exceptions) != {"knock term x4", knee_hi}:
        raise SystemExit("the summary's damage-formula sentences no longer hold -- reword template.html "
                         f"(exceptions now: {exceptions})")
    vn = _load("validation_numbers.json")
    sens = [dict(name=k, **v) for k, v in vn["climb_sensitivity"].items()]
    base_dmg = vn["climb_sensitivity"]["none"]["damage"]

    def ts_rows(block, subs):
        rows = []
        for s in subs:
            b, g = block["climb"][f"baseline ECU | {s}"], block["climb"][f"current-grade | {s}"]
            rows.append(dict(sub=s, peak=_r(b["peak_turb"], 3), damage=_r(b["damage"], 1),
                             cut=_r(block["cuts"][str(s)], 2), swing=_r(b["coolant_swing"], 2),
                             grade_peak=_r(g["peak_turb"], 3)))
        return rows
    with open(os.path.join(RES, "conditions_traces.json"), encoding="utf-8") as fh:
        ctr = json.load(fh)
    return dict(
        cond=cond, cond_n=len(cond), c25=by["25 C"], trained=by["42 C"],
        r25=[dict(name=pretty(t), spark=_r(v, 2)) for v, t in r25],
        warm_beat_min=min(by[k]["beat"] for k in ("42 C", "35 C", "50 C")),
        thin_short_hi=max(c["short_agents"] for c in thin),
        grade_short_n=len(short), grade_short_lo=min(short), grade_short_hi=max(short),
        dc=dict(creep=_r(dc["creep_scale_k"]["10000"], 1), creep_lo=_r(dc["creep_scale_k"]["100000"], 1),
                creep_hi=_r(dc["creep_scale_k"]["1000"], 1), oil_rule=_r(dc["oil_rule_scale_k"], 1),
                q45=_r(8.314462618 * 1123.0 ** 2 / 45.0 / 1000.0, 0), r=_r(dc["housing_fraction_r"], 3),
                gas_at_knee=_r(dc["constants"][1]["published_as_gas_c"], 0),
                gas_end=_r(dc["climb_end"]["gas_c"], 0), housing_end=_r(dc["climb_end"]["housing_c"], 0),
                knees=knees, oil_ref=_r(dc["constants"][3]["value"] - 273.15, 1),
                rows=rows, knock=abl_knock, constants=dc["constants"]),
        ts=dict(cut=_r(dt1["cut_points"], 2), peak=_r(dt1["peak_turb_k"], 3),
                swing2=_r(dt2["climb"]["baseline ECU | 1"]["coolant_swing"], 1),
                swing1=_r(ts["climb"]["baseline ECU | 1"]["coolant_swing"], 1),
                cut2=_r(abs(c2["1"] - c2["100"]), 2),
                rows1=ts_rows(ts, ts["substeps"]), rows2=ts_rows(dt2, dt2["substeps"])),
        robust=robust, formulas_n=len(formulas), formulas_exc=len(exceptions),
        formulas_zero=len(formulas) - len(exceptions),
        vn=dict(res=vn["resolution"], sens=sens, base=base_dmg,
                spark_up=_r(vn["climb_sensitivity"]["spark +0.75 deg"]["damage"] - base_dmg, 0),
                spark_dn=_r(vn["climb_sensitivity"]["spark -0.75 deg"]["damage"] - base_dmg, 0),
                mei=vn["mei"]),
        ctr=ctr,
        spark=dict(med=allc["diff_median"], n=allc["readings"], se=allc["diff_se"],
                   climb=climb["diff_median"], climb_n=climb["readings"],
                   drives=allc["drives"], genuine=sp["genuine_total"],
                   cells=[dict(name=k, **{q: v[q] for q in ("readings", "drives", "car_median", "model_median",
                                                            "diff_median", "diff_q1", "diff_q3", "diff_se")})
                          for k, v in sp["cells"].items()],
                   readings=[dict(src=r["source"].split("-")[0], rpm=_r(r["rpm"], 0), map=_r(r["map_kpa"], 1),
                                  car=_r(r["spark"], 2), model=_r(r["model"], 2), amb=_r(r["t_amb"], 1))
                             for r in sp["readings"]]),
        rec=dict(fields=len(step_record.FIELDS), train_fields=5 + len(step_record.INFO + step_record.ENV) + 2,
                 runs=rd["runs"], reproduced=rd["reproduced"], steps=rd["steps"],
                 torque_err=rd["torque_err_max_nm"], reward_err=rd["reward_err_max"]))


def trained_env():
    """The world the twenty agents trained in (record_extracts.py ->
    training_env.json, 8 October): the roads, their steepness, the gears, the
    air and the preference weights, as the page's training-environment figures
    draw them."""
    with open(os.path.join(RES, "agents", AGENT_SET, "training_env.json"), encoding="utf-8") as fh:
        T = json.load(fh)
    gears = {int(k): v for k, v in T["gears"].items()}
    tot = sum(gears.values())
    T["pct"] = dict(ge4=_r(100 * T["share"]["ge4"], 1), ge10=_r(100 * T["share"]["ge10"], 1),
                    ge12=_r(100 * T["share"]["ge12"], 1), lt0=_r(100 * T["share"]["lt0"], 1),
                    g78=_r(100 * (gears[7] + gears[8]) / tot, 1), g8=_r(100 * gears[8] / tot, 1),
                    g7=_r(100 * gears[7] / tot, 1), g5=_r(100 * gears[5] / tot, 1))
    wl = T["w_life"]
    T["wl"] = dict(le=wl["le_threshold"], n=wl["n"], thr=wl["threshold"],
                   pct=_r(100 * wl["le_threshold"] / wl["n"], 0))
    T["rise_max"] = max(f["rise_max"] for f in T["families"].values())
    return T


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
    # The commit only: a branch name here carries a student number, and the
    # page is read outside the team (30 September 2026).
    return dict(commit=git("rev-parse", "--short", "HEAD") + (" + uncommitted changes" if dirty else ""),
                built=date.today().isoformat(),
                drives=len(M), minutes=_r(M.duration_min.sum(), 1), agent_set=AGENT_SET)


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
                cal=calibration(), gen=generality(), val=validation(), tenv=trained_env())
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

"""run_results.py -- regenerate the results the figures and the page are drawn from.

    python run_results.py              # ~10-15 min on a multi-core machine
    python run_results.py traces sweep # a subset

Writes, from the simulator as it stands (data/derived_params.json):

    results/traces_130kmh.json       per-step traces, the four hand-written policies
                                     on the locked climb (check_premise.py's rollout)
    results/sweep_speed_grade.json   peak turbine over 90/110/130 km/h x 0/6/12/16 %
    results/phase_d_130kmh_raw.json  the frozen twenty-episode protocol
    results/phase_d_130kmh.txt       (evaluate.run_episode, unchanged) for the four
                                     hand-written policies and every agent in runs/

WHY THIS FILE EXISTS (28 September 2026). Those three JSON files were written by
scripts that were never committed -- the shape of AUDIT.md M6, "published figures
no shipped script prints" -- so when the plant changed there was no way to bring
them, the figures (1-4, 6) or the phone page with it. This is that script. It
calls check_premise's policies and evaluate.run_episode exactly as shipped; it
adds a parallel driver and nothing else.

THE AGENTS IN runs/ ARE STILL A RECORD, NOT A RESULT. They trained at 110 km/h,
at dt 0.2 s, on one road, on the plant before 28 September. Re-scoring them here
keeps the figures consistent with the current plant; it does not make them
Phase D's answer. The retrain does (handoff.md).
"""
import glob
import itertools
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
POLICIES = (("baseline ECU", "p_neutral"), ("reactive", "p_reactive"),
            ("current-grade", "p_grade_now"), ("predictive (hand)", "p_predictive"))


# ------------------------------------------------------------------ traces
def trace(job):
    name, fn = job
    import check_premise as C
    from engine_env import SupervisoryTunerEnv, make_grade_climb, damage_rate
    env = SupervisoryTunerEnv(make_grade_climb(duration=720.0, dt=1.0), dt=1.0, seed=0)
    obs, _ = env.reset(seed=0)
    pol = getattr(C, fn)
    keys = ("t", "t_turb", "t_oil", "dmg_cum", "torque", "torque_req", "spark", "lam",
            "grade", "egt", "ki", "t_turb_base", "dmg_base_cum")
    out = {k: [] for k in keys}
    dmg = 0.0
    while True:
        k = env.k
        obs, r, term, trunc, info = env.step(pol(env, obs))
        dmg += damage_rate(info["t_turb"], info["t_oil"], info["ki"]) * env.dt
        # float() on every value: the thermal state picks up numpy float32 from
        # the action vector, and json cannot write float32.
        row = dict(t=k * env.dt, t_turb=info["t_turb"] - 273.15, t_oil=info["t_oil"] - 273.15,
                   dmg_cum=dmg, torque=info["torque"], torque_req=info["torque_req"],
                   spark=info["spark"], lam=info["lam"], grade=env.cycle["grade"][k],
                   egt=info["egt_c"], ki=info["ki"], t_turb_base=env.thermal_base.t_turb - 273.15,
                   dmg_base_cum=env.ep["damage_base"])
        for key, val in row.items():
            out[key].append(float(val))
        if term or trunc:
            break
    out["summary"] = {k: float(v) for k, v in info["episode_summary"].items()}
    return name, out


# ------------------------------------------------------------------- sweep
def sweep_point(job):
    v, g = job
    import check_premise as C
    from engine_env import SupervisoryTunerEnv, make_grade_climb, TURB_PROTECT_K
    env = SupervisoryTunerEnv(make_grade_climb(duration=900.0, dt=1.0, grade=g / 100.0, v_kmh=v),
                              dt=1.0, seed=0)
    obs, _ = env.reset(seed=0)
    temps = []
    while True:
        obs, r, term, trunc, info = env.step(C.p_neutral(env, obs))
        temps.append(info["t_turb"])
        if term or trunc:
            break
    temps = np.array(temps)
    temps = temps.astype(float)
    return dict(v_kmh=v, grade=g, peak_c=float(temps.max() - 273.15),
                frac_above=float((temps > TURB_PROTECT_K).mean()),
                binds=bool(temps.max() > TURB_PROTECT_K))


# ------------------------------------------------------------------ phase D
def episode(job):
    label, spec, ep, seed, w = job
    import evaluate as E
    import check_premise as C
    if spec.startswith("hand:"):
        pol, prev = getattr(C, spec[5:]), True
    else:
        from stable_baselines3 import SAC
        model = SAC.load(os.path.join(HERE, spec, "final"), device="cpu")
        pol, prev = E.agent_policy(model), "blind" not in spec
    r = E.run_episode(pol, seed, w, use_preview=prev)
    r.update(policy=label, episode=ep)
    return r


def _paired(rows, base):
    """Sighted minus blinded, paired by seed, in points of damage cut."""
    cut = {}
    for r in rows:
        cut.setdefault(r["policy"], []).append(r["damage"])
    med = {k: float(np.median(v)) for k, v in cut.items()}
    diffs = []
    for s in range(5):
        a, b = f"runs/sighted_seed{s}", f"runs/blind_seed{s}"
        if a in med and b in med:
            diffs.append((s, 100 * (1 - med[a] / base), 100 * (1 - med[b] / base)))
    return med, diffs


def _signed_rank_p(d):
    """Exact two-sided Wilcoxon signed-rank p for small n (enumeration)."""
    d = np.asarray([x for x in d if x != 0.0])
    n = len(d)
    if n == 0:
        return float("nan")
    ranks = np.argsort(np.argsort(np.abs(d))) + 1
    w = ranks[d > 0].sum()
    tot = n * (n + 1) / 2
    stats = [sum(r for r, s in zip(ranks, signs) if s) for signs in itertools.product((0, 1), repeat=n)]
    stats = np.array(stats)
    return float(np.mean(np.abs(stats - tot / 2) >= abs(w - tot / 2) - 1e-9))


def phase_d(pool):
    import evaluate as E
    agents = sorted(os.path.relpath(p, HERE).replace("\\", "/")
                    for p in glob.glob(os.path.join(HERE, "runs", "*_seed*"))
                    if os.path.exists(os.path.join(p, "final.zip")))
    specs = [(n, "hand:" + f) for n, f in POLICIES] + [(a, a) for a in agents]
    jobs = [(lab, spec, i, s, w) for lab, spec in specs for i, (s, w) in enumerate(E.EPISODES)]
    rows = list(pool.map(episode, jobs, chunksize=1))
    with open(os.path.join(RES, "phase_d_130kmh_raw.json"), "w") as fh:
        json.dump(rows, fh)

    by = {}
    for r in rows:
        by.setdefault(r["policy"], []).append(r)
    base = float(np.median([r["damage"] for r in by["baseline ECU"]]))
    base_t = float(np.median([r["damage_thermal"] for r in by["baseline ECU"]]))
    lines = ["PHASE D EVALUATION -- 20 FIXED EPISODES, frozen 18 Sep 2026",
             "scenario: 12 % at 130 km/h, 42 C, 720 s, dt 1.0",
             "trigger:  850 C",
             f"run:      {time.strftime('%d %B %Y')}, by run_results.py, on the simulator with its",
             "          data-set constants DERIVED from the logs (data/derived_params.json);",
             "          evaluate.EPISODES and evaluate.run_episode unchanged", "",
             f"{'policy':<22}{'damage med':>11}{'IQR':>8}{'worst':>8}{'thermal med':>12}"
             f"{'fuel med':>10}{'peak C':>8}{'cuts %':>8}{'cuts % thermal':>16}",
             "-" * 103]
    for name, rs in by.items():
        d = np.array([r["damage"] for r in rs]); t = np.array([r["damage_thermal"] for r in rs])
        q1, q3 = np.percentile(d, [25, 75])
        lines.append(f"{name.replace('runs/', ''):<22}{np.median(d):>11.1f}{q3 - q1:>8.1f}{d.max():>8.1f}"
                     f"{np.median(t):>12.1f}{np.median([r['fuel'] for r in rs]):>10.0f}"
                     f"{max(r['peak_turb'] for r in rs):>8.0f}{100 * (1 - np.median(d) / base):>8.1f}"
                     f"{100 * (1 - np.median(t) / base_t):>16.1f}")
    lines.append("-" * 103)
    med, diffs = _paired(rows, base)
    if diffs:
        dd = np.array([a - b for _, a, b in diffs])
        lines += ["", "THE ABLATION, PAIRED BY SEED -- the only correct way to read it",
                  "seed    sighted cut %  blinded cut %   difference", "-" * 49]
        lines += [f"{s:<8}{a:>13.1f}{b:>15.1f}{a - b:>13.1f}" for s, a, b in diffs]
        m, sd = float(dd.mean()), float(dd.std(ddof=1)) if len(dd) > 1 else float("nan")
        tstat = m / (sd / np.sqrt(len(dd))) if len(dd) > 1 and sd > 0 else float("nan")
        lines += ["-" * 49, f"mean difference {m:+.1f} points, sd {sd:.1f}, paired t = {tstat:.2f} (n = {len(dd)})",
                  f"Wilcoxon signed-rank, exact two-sided p = {_signed_rank_p(dd):.2f}"]
        sighted = [a for _, a, _ in diffs]
        g = 100 * (1 - med["current-grade"] / base)
        lines.append(f"AGENT (sighted median {np.median(sighted):.1f} %) over CURRENT-GRADE "
                     f"({g:.1f} %): {np.median(sighted) - g:+.1f} points")
    lines += ["", "READ THIS BEFORE QUOTING ANY ROW. The agents in runs/ trained at 110 km/h, at",
              "dt = 0.2 s, on one road, on the plant BEFORE its constants were derived from the",
              "logs. They are a record, not Phase D's answer: the retrain is (handoff.md).",
              "The hand-written rows have zero IQR by construction: they ignore the preference",
              "weights, so all twenty episodes are one rollout repeated."]
    with open(os.path.join(RES, "phase_d_130kmh.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    want = set(sys.argv[1:]) or {"traces", "sweep", "phase_d"}
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=min(18, os.cpu_count() or 4)) as pool:
        if "traces" in want:
            tr = dict(pool.map(trace, POLICIES))
            with open(os.path.join(RES, "traces_130kmh.json"), "w") as fh:
                json.dump(tr, fh)
            print("traces:", {k: round(v["summary"]["damage"], 1) for k, v in tr.items()})
        if "sweep" in want:
            sw = list(pool.map(sweep_point, [(v, g) for v in (90, 110, 130) for g in (0, 6, 12, 16)]))
            with open(os.path.join(RES, "sweep_speed_grade.json"), "w") as fh:
                json.dump(sw, fh)
            for s in sw:
                print(f"   {s['v_kmh']} km/h {s['grade']:2d} %  peak {s['peak_c']:6.1f} C"
                      f"{'  binds' if s['binds'] else ''}")
        if "phase_d" in want:
            phase_d(pool)
    print(f"\n{(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()

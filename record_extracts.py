"""record_extracts.py -- small committed extracts of the per-step records, for the results page.

    python record_extracts.py
    python record_extracts.py --x1     X1's training world only (8 October)

The per-step records are gitignored (the team's rule, 29 September 2026) and
live on the machine that made them, while the results page must build from git
alone. So, like episode_trace.json (record_agents.py), these are small rounded
extracts of what the page draws:

  results/conditions_traces.json
        the conditions test (conditions_test.py): for each condition, the road
        (grade, speed, gear) and, for the baseline ECU, current-grade and each
        of the twenty agents, the turbine housing, spark trim, boost trim and
        cumulative damage, every 5 s of frozen episode 1
  results/agents/terrain_dt1/training_env.json
        the world the twenty agents trained in, from the roads regenerated
        beside each training record (training_roads.py): every road of the ten
        seeds as grade segments, with its family, steepest grade, climb time,
        rise and life weight; and the seconds spent per grade and per gear
  results/agents/terrain_dt1/bad_episode_trace.json
        blinded seed 6 on the frozen episode where it does the most damage and
        on the one where it does the least, beside current-grade (the comparing
        line) and the baseline ECU on the same road: spark trim, manifold
        pressure, turbine, knock integral, and the running fuel and damage,
        every 2 s (CLAUDE.md mistake 24)

  results/agents/extremes_dt1/training_env.json   (--x1)
        the world X1's agents trained in, read off their own training records,
        which carry the road at every step since 8 October: every episode of
        every seed with its ambient, steepest grade, speed range, housing
        capacity, life weight and whether the parallel baseline car passed
        850 C; and the seconds per grade, per gear and per speed

Written 8 October 2026, when Ghassan asked for the page to show the new data,
not only describe it. Re-run after the records are re-made, then make_page.py.
"""
import glob
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
COND = os.path.join(HERE, "results", "records", "conditions")
AGENTS = os.path.join(HERE, "results", "agents", "terrain_dt1")


def rnd(x, n):
    """float64 before rounding, so a float32 does not list its float64 digits."""
    return np.round(np.asarray(x, dtype=np.float64), n).tolist()


def conditions(every=5):
    import conditions_test as CT
    out = dict(every_s=every, episode=CT.EPISODES[0], conditions=[])
    for k, (name, t_amb, p) in enumerate(CT.CONDITIONS):
        d = CT._records_dir(k)
        if not os.path.isdir(d):
            raise SystemExit(f"{os.path.relpath(d, HERE)} missing -- run conditions_test.py first")
        base = np.load(os.path.join(d, "baseline_ECU.npz"))
        with open(os.path.join(d, "baseline_ECU.json"), encoding="utf-8") as fh:
            meta = json.load(fh)
        idx = np.arange(0, base["reward"].shape[1], every)
        cond = dict(name=name, grade_pct=round(100 * meta["grade"], 2), t=idx.tolist(),
                    grade=rnd(100 * base["grade"][0, idx], 2), v_kmh=rnd(base["v_kmh"][0, idx], 1),
                    gear=base["gear"][0, idx].astype(int).tolist(), policies={})
        files = ["baseline_ECU", "current_grade"] + sorted(
            (os.path.splitext(os.path.basename(f))[0] for f in glob.glob(os.path.join(d, "*_seed*.npz"))),
            key=lambda n: ("blind" in n, int(n.split("seed")[1])))
        for f in files:
            r = np.load(os.path.join(d, f + ".npz"))
            a = r["applied"][0, idx]
            kind = "hand" if "seed" not in f else ("blinded" if f.startswith("blind") else "sighted")
            cond["policies"][f] = dict(kind=kind, turb=rnd(r["t_turb"][0, idx] - 273.15, 1),
                                       spark=rnd(a[:, 0], 2), boost=rnd(a[:, 2], 1),
                                       dmg=rnd(r["damage_cum"][0, idx], 1))
        out["conditions"].append(cond)
    path = os.path.join(HERE, "results", "conditions_traces.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, separators=(",", ":"))
    print(f"wrote {os.path.relpath(path, HERE)} ({os.path.getsize(path) / 1024:.0f} kB): "
          f"{len(out['conditions'])} conditions x {len(files)} policies, every {every} s of frozen episode {out['episode']}")


def bad_episode(agent="blind_seed6", every=2):
    r = np.load(os.path.join(AGENTS, agent, "eval_record.npz"))
    b = np.load(os.path.join(AGENTS, "baseline_ECU", "eval_record.npz"))
    with open(os.path.join(AGENTS, agent, "eval_summary.json"), encoding="utf-8") as fh:
        eps = json.load(fh)["episodes"]
    worst = int(np.argmax([e["damage"] for e in eps]))
    best = int(np.argmin([e["damage"] for e in eps]))
    idx = np.arange(0, r["reward"].shape[1], every)
    out = dict(agent=agent, every_s=every, t=idx.tolist(), grade=rnd(100 * r["grade"][0, idx], 2), episodes={})
    for label, e in (("worst", worst), ("best", best)):
        out["episodes"][label] = dict(
            episode=e, seed=int(r["episode_seed"][e]), weights=rnd(r["weights"][e], 3),
            damage=round(eps[e]["damage"], 1), ret=round(eps[e]["ret"], 1),
            spark=rnd(r["applied"][e, idx, 0], 2), lam=rnd(r["applied"][e, idx, 1], 4),
            map=rnd(r["map_kpa"][e, idx], 1), turb=rnd(r["t_turb"][e, idx] - 273.15, 1),
            ki=rnd(r["ki"][e, idx], 3), fuel=rnd(r["fuel_cum"][e, idx], 1), dmg=rnd(r["damage_cum"][e, idx], 1))
    # The baseline ECU and current-grade drive the same road on every frozen
    # episode, and neither reads the weights, so one episode each stands for all.
    # Current-grade is the comparing line (Ghassan, 7 October); the baseline is
    # what the agent's reward is paid against.
    g = np.load(os.path.join(AGENTS, "current-grade", "eval_record.npz"))
    for key, rec in (("baseline", b), ("current_grade", g)):
        out[key] = dict(spark=rnd(rec["applied"][worst, idx, 0], 2), lam=rnd(rec["applied"][worst, idx, 1], 4),
                        map=rnd(rec["map_kpa"][worst, idx], 1), turb=rnd(rec["t_turb"][worst, idx] - 273.15, 1),
                        ki=rnd(rec["ki"][worst, idx], 3), fuel=rnd(rec["fuel_cum"][worst, idx], 1),
                        dmg=rnd(rec["damage_cum"][worst, idx], 1))
    path = os.path.join(AGENTS, "bad_episode_trace.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, separators=(",", ":"))
    print(f"wrote {os.path.relpath(path, HERE)} ({os.path.getsize(path) / 1024:.0f} kB): {agent}, "
          f"frozen episodes {worst + 1} (worst) and {best + 1} (best), every {every} s")


def training_env(q=0.005):
    """The world the twenty agents trained in (Ghassan, 8 October: "a graph
    showing the environment trained on: speed, hills, how steep"). From the
    roads regenerated beside each training record (training_roads.py). The
    sighted and blinded agent of a seed drove the same 56 roads with the same
    weights (checked here), so ten road sequences cover all twenty agents.

    Per seed and episode: the family, the grade as run-length segments
    (quantised to 0.5 %, every second), the steepest grade, the seconds at 4 %
    or more, the climb in metres, and the episode's weight on component life.
    Over all of it: seconds per grade, seconds per gear, and how the life
    weight was spread."""
    import engine_env as EE
    runs = os.path.join(HERE, "runs", "terrain_dt1")
    seeds, all_g, all_gear, all_wl = [], [], [], []
    for s in range(10):
        a = np.load(os.path.join(runs, f"sighted_seed{s}", "train_roads.npz"))
        b = np.load(os.path.join(runs, f"blind_seed{s}", "train_roads.npz"))
        if not (np.array_equal(a["grade"], b["grade"]) and np.array_equal(a["weights"], b["weights"])):
            raise SystemExit(f"seed {s}: the sighted and blinded agents did not drive the same roads")
        ep = a["episode"]
        eps = []
        for e in np.unique(ep):
            m = ep == e
            g, v = a["grade"][m].astype(float), a["v_kmh"][m].astype(float) / 3.6
            gq = np.round(g / q) * q
            cuts = np.flatnonzero(np.diff(gq)) + 1
            starts = np.concatenate([[0], cuts])
            ends = np.concatenate([cuts, [len(gq)]])
            eps.append(dict(family=str(a["family"][e]), steps=int(m.sum()),
                            seg=[[int(i), int(j), round(100 * float(gq[i]), 2)] for i, j in zip(starts, ends)],
                            max_pct=round(100 * float(g.max()), 2), climb_s=int((g >= 0.04 - 1e-4).sum()),
                            rise_m=round(float(np.sum(np.clip(g, 0, None) * v)), 0),
                            w_life=round(float(a["weights"][m][0][2]), 3)))
            all_wl.append(float(a["weights"][m][0][2]))
        seeds.append(dict(seed=s, episodes=eps))
        all_g.append(a["grade"].astype(float))
        all_gear.append(a["gear"].astype(int))
    g, gear = np.concatenate(all_g), np.concatenate(all_gear)
    edges = np.arange(-0.0325, 0.1425 + 1e-9, q)
    hist, _ = np.histogram(g, bins=edges)
    fam = {}
    for sd in seeds:
        for e in sd["episodes"]:
            f = fam.setdefault(e["family"], dict(n=0, max_pct=-9.0, climb_s=0, steps=0, rise_max=0.0))
            f["n"] += 1
            f["max_pct"] = max(f["max_pct"], e["max_pct"])
            f["climb_s"] += e["climb_s"]
            f["steps"] += e["steps"]
            f["rise_max"] = max(f["rise_max"], e["rise_m"])
    wl = np.array(all_wl)
    # The life weight of blinded seed 6's frozen episodes that do more damage
    # than the baseline (CLAUDE.md mistake 24): how often training met as low.
    with open(os.path.join(AGENTS, "blind_seed6", "eval_summary.json"), encoding="utf-8") as fh:
        b6 = json.load(fh)["episodes"]
    with open(os.path.join(AGENTS, "baseline_ECU", "eval_summary.json"), encoding="utf-8") as fh:
        base = json.load(fh)["summary"]["damage"]["median"]
    import evaluate as E
    thr = max(E.EPISODES[i][1][2] for i, e in enumerate(b6) if e["damage"] > base)
    out = dict(
        seeds=seeds,
        env=dict(v_kmh=130.0, launch_s=20, t_amb_c=round(315.0 - 273.15, 2), p_kpa=101.3, humidity=0.012,
                 dt_s=1.0, duration_s=900, episodes_per_agent=int(len(seeds[0]["episodes"])),
                 steps_per_agent=int(sum(e["steps"] for e in seeds[0]["episodes"])),
                 grade_min_pct=100 * EE.TERRAIN_GRADE_MIN, grade_max_pct=100 * EE.TERRAIN_GRADE_MAX,
                 flat_start_s=EE.TERRAIN_FLAT_START_S,
                 families=dict(zip(EE.TERRAIN_FAMILIES, EE.TERRAIN_WEIGHTS))),
        grade_hist=dict(lo_pct=[round(100 * x, 2) for x in edges[:-1]], seconds=hist.tolist()),
        # 1e-4 below each threshold: the records hold float32, and 0.12 stored as
        # float32 is 0.11999999, so the locked climb would fall under "12 % or more".
        share=dict(ge4=round(float((g >= 0.04 - 1e-4).mean()), 4), ge10=round(float((g >= 0.10 - 1e-4).mean()), 4),
                   ge12=round(float((g >= 0.12 - 1e-4).mean()), 4), lt0=round(float((g < -1e-4).mean()), 4)),
        gears={str(k): int((gear == k).sum()) for k in range(0, 9)},
        families=fam,
        w_life=dict(min=round(float(wl.min()), 3), max=round(float(wl.max()), 3),
                    threshold=round(float(thr), 3), le_threshold=int((wl <= thr + 1e-9).sum()), n=int(wl.size),
                    hist=np.histogram(wl, bins=np.arange(0, 0.6001, 0.025))[0].tolist()))
    path = os.path.join(AGENTS, "training_env.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, separators=(",", ":"))
    print(f"wrote {os.path.relpath(path, HERE)} ({os.path.getsize(path) / 1024:.0f} kB): 10 road sequences x "
          f"{out['env']['episodes_per_agent']} episodes, grade {g.min() * 100:.1f} to {g.max() * 100:.1f} %")


def x1_training_env(n_seeds=23):
    """X1's training world, from the 46 runs' own records. The sighted and blinded
    agent of a seed draw the same road stream and the same weights; checked
    here on every step's grade, speed, ambient, housing capacity and weights."""
    import sys
    runs = os.path.join(HERE, "runs", "extremes_dt1")
    eps, g_all, gear_all, v_all = [], [], [], []
    train_cut = {}
    for sd in range(n_seeds):
        a = np.load(os.path.join(runs, f"sighted_seed{sd}", "train_record.npz"))
        b = np.load(os.path.join(runs, f"blind_seed{sd}", "train_record.npz"))
        for k in ("grade", "v_kmh", "t_amb_c", "c_turb", "weights"):
            if not np.array_equal(a[k], b[k]):
                sys.exit(f"seed {sd}: the two arms did not drive the same roads ({k} differs)")
        ep = a["episode"]
        for e in np.unique(ep):
            m = ep == e
            if m.sum() < 600:            # the last, unfinished episode of a run
                continue
            g, v = a["grade"][m].astype(float), a["v_kmh"][m].astype(float)
            tb = a["t_turb_base"][m].astype(float)
            eps.append([sd, int(e), rnd(float(a["t_amb_c"][m][0]), 1), rnd(100 * float(g.max()), 2),
                        rnd(100 * float(g.min()), 2), rnd(float(v[20:].min()), 0), rnd(float(v.max()), 0),
                        rnd(float(a["c_turb"][m][0]) / 6000.0, 3), rnd(float(a["weights"][m][0][2]), 3),
                        int(np.nanmax(tb) - 273.15 > 850.0), int((g >= 0.12).sum())])
        # How much each agent protected on its own last ten complete training
        # roads: its damage against the parallel baseline car's on the same road.
        for tag, rec in ((f"sighted_seed{sd}", a), (f"blind_seed{sd}", b)):
            e2 = rec["episode"]
            done = [e for e in np.unique(e2) if (e2 == e).sum() >= 600][-10:]
            cuts = []
            for e in done:
                m = e2 == e
                da, db = float(rec["damage_cum"][m][-1]), float(rec["damage_base_cum"][m][-1])
                if db > 1.0:
                    cuts.append(100.0 * (1.0 - da / db))
            train_cut[tag] = rnd(float(np.median(cuts)), 1) if cuts else None
        g_all.append(a["grade"].astype(float))
        gear_all.append(a["gear"].astype(int))
        v_all.append(a["v_kmh"].astype(float))
    g, gear, v = np.concatenate(g_all), np.concatenate(gear_all), np.concatenate(v_all)
    out = dict(
        fields=["seed", "episode", "t_amb_c", "grade_max_pct", "grade_min_pct", "v_min_kmh", "v_max_kmh",
                "c_turb_scale", "w_life", "baseline_past_850", "s_at_12pct"],
        episodes=eps, seeds=n_seeds, train_cut_last10=train_cut,
        grade_s={str(k): int(((g * 100 >= k) & (g * 100 < k + 1)).sum()) for k in range(-6, 20)},
        gear_s={str(k): int((gear == k).sum()) for k in range(0, 9)},
        speed_s={str(k): int(((v >= k) & (v < k + 10)).sum()) for k in range(0, 160, 10)},
        steps=int(len(g)))
    path = os.path.join(HERE, "results", "agents", "extremes_dt1", "training_env.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, separators=(",", ":"))
    print(f"wrote {os.path.relpath(path, HERE)}: {len(eps)} episodes of {n_seeds} seeds, {len(g):,} steps")


def x1_pair_trace(every=4):
    """X1's widest seed pair: the sighted and blinded agent of the seed whose
    difference is most negative, on frozen episode 1, beside the baseline ECU and
    current-grade on the same road. Every `every` s: the turbine housing and the
    three trims applied (spark, lambda, boost). From eval_record.npz."""
    A = os.path.join(HERE, "results", "agents", "extremes_dt1")
    with open(os.path.join(A, "index.json"), encoding="utf-8") as fh:
        pairs = json.load(fh)["ablation"]["pairs"]
    worst = min(pairs, key=lambda p: p["sighted"] - p["blinded"])
    sd = worst["seed"]
    out = dict(seed=sd, episode=1, every_s=every, sighted_cut=worst["sighted"], blinded_cut=worst["blinded"])
    ep = 0
    for key, folder in (("sighted", f"sighted_seed{sd}"), ("blind", f"blind_seed{sd}"),
                        ("baseline", "baseline_ECU"), ("grade", "current-grade")):
        r = np.load(os.path.join(A, folder, "eval_record.npz"))
        n = int(r["steps"][ep]) if "steps" in r.files else r["t_turb"].shape[1]
        sl = slice(0, n, every)
        out[key] = dict(turb=rnd(r["t_turb"][ep, sl] - 273.15, 1),
                        spark=rnd(r["applied"][ep, sl, 0], 2), lam=rnd(r["applied"][ep, sl, 1], 3),
                        boost=rnd(r["applied"][ep, sl, 2], 1),
                        damage=rnd(r["damage_cum"][ep, n - 1], 1))
        if key == "baseline":
            out["t"] = list(range(0, n, every))
            out["grade"] = rnd(100 * r["grade"][ep, sl], 2)
    path = os.path.join(A, "pair_trace.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, separators=(",", ":"))
    print(f"wrote {os.path.relpath(path, HERE)}: seed {sd}, cuts {worst['sighted']:.1f} / {worst['blinded']:.1f} %")


def x1_logged_fuel():
    """Where the agents' extra fuel on the logged drives goes: summed over every
    agent record of logged_check.py, the fuel burned beyond the parallel ECU car,
    binned by how hot that car's housing was at the step."""
    files = [f for f in glob.glob(os.path.join(HERE, "results", "records", "logged", "extremes_dt1", "*.npz"))
             if "current-grade" not in os.path.basename(f)]
    bands = [(0, 500), (500, 650), (650, 750), (750, 2000)]
    extra, base, steps = np.zeros(4), np.zeros(4), np.zeros(4)
    for f in files:
        r = np.load(f)
        fa = np.diff(np.r_[0.0, r["fuel_cum"][0].astype(float)])
        fb = np.diff(np.r_[0.0, r["fuel_base_cum"][0].astype(float)])
        tb = r["t_turb_base"][0].astype(float) - 273.15
        ok = np.isfinite(fa) & np.isfinite(fb) & np.isfinite(tb)
        for i, (lo, hi) in enumerate(bands):
            m = ok & (tb >= lo) & (tb < hi)
            extra[i] += (fa[m] - fb[m]).sum()
            base[i] += fb[m].sum()
            steps[i] += m.sum()
    out = dict(records=len(files), bands=[dict(lo=lo, hi=hi, steps_pct=rnd(100 * n / steps.sum(), 1),
                                              extra_pct_of_base=rnd(100 * e / b, 2),
                                              share_of_extra_pct=rnd(100 * e / extra.sum(), 1))
                                         for (lo, hi), e, b, n in zip(bands, extra, base, steps)])
    path = os.path.join(HERE, "results", "agents", "extremes_dt1", "logged_fuel_bands.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"wrote {os.path.relpath(path, HERE)}: {len(files)} records")


if __name__ == "__main__":
    import sys as _sys
    if "--x1" in _sys.argv:
        x1_training_env()
        x1_pair_trace()
        x1_logged_fuel()
    else:
        conditions()
        bad_episode()
        training_env()

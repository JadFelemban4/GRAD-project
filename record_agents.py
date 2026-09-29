"""record_agents.py -- score, record and document trained agents.

    python record_agents.py runs/terrain_dt1              # the 29 Sep retrain (20 agents)
    python record_agents.py runs --name sep19_110kmh      # the ten agents of 19 Sep, a record
    python record_agents.py --hand                        # the four hand-written policies

Written 29 September 2026. Until then an agent left a model file in runs/ --
gitignored, so nobody but its trainer had it -- and one row per episode of
evaluate.py's scores. Nothing said what it had DONE. This writes, for every
agent, into results/agents/<set>/<tag>/:

  config.json        how it was trained: every SAC setting, the versions, the
                     commit, the plant's data fingerprint, wall time (train.py
                     writes it since 29 Sep; for older agents it is read back
                     out of the saved model, and what cannot be is said)
  curve.csv          one row per training episode: return, length, road
  train_record.npz   EVERY training step: action, observation, reward, engine
                     state (train.py's ActionRecorder; agents trained before
                     29 Sep have none, and their README says so)
  eval_record.npz    EVERY step of the twenty frozen episodes: the action the
                     policy returned, what the actuators did after the slew
                     limit, the observation, the reward and its terms, and the
                     engine: rpm, MAP, spark, lambda, torque and its request,
                     knock integral, EGT, fuel, turbine/oil/block temperature,
                     the BASELINE's turbine temperature beside it, damage rate.
                     Arrays are [episode, step, ...].
  eval_summary.json  the twenty episodes scored exactly as evaluate.py scores
                     them, the medians, the cut against the baseline, and what
                     each actuator did on the flat and on the climb
  policy.npz         the actor network's weights (what acts; the critics only
                     trained it)

and for the set: README.md (every table, generated), index.json, figures/.

THE SCORES ARE evaluate.run_episode's, UNCHANGED. Recording only reads the
environment after each step. As a check, every agent or hand-written policy that
results/phase_d_130kmh_raw.json already holds is compared episode by episode and
the run STOPS on any difference.
"""
import argparse
import glob
import json
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor

os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUTROOT = os.path.join(HERE, "results", "agents")
HAND = (("baseline ECU", "p_neutral"), ("reactive", "p_reactive"),
        ("current-grade", "p_grade_now"), ("predictive (hand)", "p_predictive"))
ACTUATORS = ("spark trim (deg)", "lambda trim", "boost trim (kPa)", "fan duty", "pump duty")
F32 = ("action", "applied", "reward", "r_fuel", "r_life", "r_resp", "t_turb", "t_oil", "t_block",
       "t_turb_base", "damage_rate", "torque", "torque_req", "spark", "lam", "ki", "egt_c",
       "mdot_fuel", "rpm", "map_kpa", "grade")

# What is known about the 19 September agents that their model files do not
# hold. Sources: CLAUDE.md "Current state -- 19 September" and train.py's
# docstring (dt was never passed until 27 Sep), runs/log_*.txt (50 000 steps,
# 4 499-step episodes = 900 s at 0.2 s).
PROVENANCE = {
    "sep19_110kmh": dict(
        trained="19 September 2026, ten runs sharing the team laptop, 173 min",
        scenario="the locked climb ONLY, at 110 km/h (the lock moved to 130 km/h the same day)",
        dt=0.2, steps_per_episode=4499, roads="one road: make_grade_climb at 110 km/h",
        plant="before 27 Sep (gearbox kickdown, spark refit) and before 28 Sep (derived constants)",
        status="A RECORD, NOT A RESULT: trained at 110 km/h where nothing binds, at dt 0.2 while "
               "scored at 1.0, on one road, on an older plant. Kept so the retrain has a before."),
}


# ---------------------------------------------------------------- workers
_MODELS = {}


def _init_worker():
    try:
        import torch
        torch.set_num_threads(1)
    except ImportError:
        pass


def _policy(spec):
    kind, ref = spec
    if kind == "hand":
        import check_premise as C
        return getattr(C, dict(HAND)[ref]), True
    import evaluate as E
    from stable_baselines3 import SAC
    if ref not in _MODELS:
        _MODELS[ref] = SAC.load(os.path.join(HERE, ref, "final"), device="cpu")
    return E.agent_policy(_MODELS[ref]), "blind" not in os.path.basename(ref)


def _job(job):
    spec, i = job
    import evaluate as E
    seed, w = E.EPISODES[i]
    pol, prev = _policy(spec)
    rec = E.new_record()
    row = E.run_episode(pol, seed, w, prev, record=rec)
    return spec, i, row, {k: np.asarray(v) for k, v in rec.items()}


# ---------------------------------------------------------------- analysis
def _physical(a):
    """The policy's [-1, 1] action as the actuator command it asks for."""
    from engine_env import ACT_LO, ACT_HI
    return ACT_LO + (np.clip(a, -1.0, 1.0) + 1.0) * 0.5 * (ACT_HI - ACT_LO)


def action_stats(rec):
    """What each actuator did, on the flat and on the climb, over all episodes."""
    from engine_env import ACT_LO, ACT_HI, neutral_action
    applied = rec["applied"].reshape(-1, 5)
    asked = np.clip(_physical(rec["action"].reshape(-1, 5)), ACT_LO, ACT_HI)
    grade = rec["grade"].reshape(-1)
    neutral = _physical(neutral_action())
    limited = np.abs(applied - asked) > 1e-3 * (ACT_HI - ACT_LO)
    out = {}
    for j, name in enumerate(ACTUATORS):
        d = dict(neutral=round(float(neutral[j]), 4))
        for part, m in (("flat", grade <= 0.0), ("climb", grade > 0.0)):
            v = applied[m, j]
            if len(v):
                d[part] = dict(mean=round(float(v.mean()), 4),
                               p5=round(float(np.percentile(v, 5)), 4),
                               p50=round(float(np.median(v)), 4),
                               p95=round(float(np.percentile(v, 95)), 4))
        d["slew_limited_pct"] = round(100.0 * float(limited[:, j].mean()), 1)
        out[name] = d
    return out


def engine_stats(rec):
    """What the engine did on the climb, over all episodes. Kept in
    eval_summary.json because the per-step records are not in git (29 Sep):
    the page and the README must build from what is committed."""
    g = rec["grade"] > 0
    ki, sp, trim = rec["ki"][g], rec["spark"][g], rec["applied"][..., 0][g]
    return dict(ki_p50=round(float(np.median(ki)), 4), ki_p95=round(float(np.percentile(ki, 95)), 4),
                ki_above_knee_pct=round(100.0 * float(np.mean(ki > 0.85)), 2),
                spark_median=round(float(np.median(sp)), 3), spark_trim_median=round(float(np.median(trim)), 3),
                t_turb_peak_c=round(float(rec["t_turb"].max()) - 273.15, 2))


def summarise(rows, base_med, base_fuel, base_thermal):
    def q(k):
        v = np.array([r[k] for r in rows], float)
        q1, me, q3 = np.percentile(v, [25, 50, 75])
        return dict(median=round(float(me), 3), q1=round(float(q1), 3), q3=round(float(q3), 3),
                    worst=round(float(v.max()), 3), best=round(float(v.min()), 3))
    s = {k: q(k) for k in ("damage", "damage_thermal", "fuel", "ret", "torque_viol", "peak_turb", "knock")}
    s["cut_pct"] = round(100.0 * (1.0 - s["damage"]["median"] / base_med), 3)
    s["thermal_cut_pct"] = round(100.0 * (1.0 - s["damage_thermal"]["median"] / base_thermal), 3)
    s["fuel_vs_baseline_pct"] = round(100.0 * (s["fuel"]["median"] / base_fuel - 1.0), 3)
    return s


def paired(sets, grade_cut):
    """Sighted minus blinded, paired by seed."""
    from scipy import stats
    seeds = sorted({v["seed"] for v in sets.values() if v.get("seed") is not None})
    pairs = []
    for s in seeds:
        a = next((v for v in sets.values() if v.get("seed") == s and v["preview"]), None)
        b = next((v for v in sets.values() if v.get("seed") == s and not v["preview"]), None)
        if a and b:
            pairs.append(dict(seed=s, sighted=a["summary"]["cut_pct"], blinded=b["summary"]["cut_pct"],
                              sighted_thermal=a["summary"]["thermal_cut_pct"],
                              blinded_thermal=b["summary"]["thermal_cut_pct"]))
    if len(pairs) < 2:
        return dict(pairs=pairs)
    d = np.array([p["sighted"] - p["blinded"] for p in pairs])
    dt_ = np.array([p["sighted_thermal"] - p["blinded_thermal"] for p in pairs])
    n = len(d)
    half = stats.t.ppf(0.975, n - 1) * d.std(ddof=1) / np.sqrt(n)
    out = dict(pairs=pairs, n=n, mean=float(d.mean()), median=float(np.median(d)), sd=float(d.std(ddof=1)),
               ci95=[float(d.mean() - half), float(d.mean() + half)],
               p_t=float(stats.ttest_1samp(d, 0.0).pvalue),
               p_wilcoxon=float(stats.wilcoxon(d).pvalue) if np.any(d != 0) else 1.0,
               smallest_possible_p_wilcoxon=2.0 / 2 ** n,
               thermal_mean=float(dt_.mean()),
               p_t_thermal=float(stats.ttest_1samp(dt_, 0.0).pvalue),
               sighted_over_grade=[round(p["sighted"] - grade_cut, 2) for p in pairs])
    return out


# ---------------------------------------------------------------- config
def config_for(agent_dir, set_name):
    """train.py's config.json, or what the saved model itself says."""
    p = os.path.join(HERE, agent_dir, "config.json")
    if os.path.exists(p):
        with open(p) as fh:
            cfg = json.load(fh)
        cfg["config_source"] = "written by train.py during training"
        return cfg
    from stable_baselines3 import SAC
    m = SAC.load(os.path.join(HERE, agent_dir, "final"), device="cpu")
    tag = os.path.basename(agent_dir)
    cfg = dict(tag=tag, seed=int(tag.split("seed")[-1]), preview="blind" not in tag,
               total_timesteps=int(m.num_timesteps), algorithm="SAC",
               sac=dict(learning_rate=float(m.learning_rate), buffer_size=m.buffer_size,
                        batch_size=m.batch_size, learning_starts=m.learning_starts, gamma=m.gamma,
                        tau=m.tau, train_freq=str(m.train_freq), gradient_steps=m.gradient_steps,
                        ent_coef=str(m.ent_coef), target_entropy=float(m.target_entropy),
                        policy="MlpPolicy", net_arch=str(m.policy.net_arch)),
               config_source="read back out of final.zip on " + time.strftime("%Y-%m-%d")
                             + "; train.py wrote no config before 29 September")
    cfg.update(PROVENANCE.get(set_name.replace("_TEST", ""), {}))
    return cfg


def export_policy(agent_dir, path):
    from stable_baselines3 import SAC
    m = SAC.load(os.path.join(HERE, agent_dir, "final"), device="cpu")
    sd = {k.replace(".", "__"): v.detach().cpu().numpy().astype(np.float32)
          for k, v in m.policy.actor.state_dict().items()}
    np.savez_compressed(path, **sd)
    return int(sum(v.size for v in sd.values()))


# ---------------------------------------------------------------- figures
def figures(outdir, agents, hand, stats_, set_name):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fdir = os.path.join(outdir, "figures")
    os.makedirs(fdir, exist_ok=True)
    SIGHT, BLIND, GREY, GREEN, INK = "#4a3aa7", "#e87ba4", "#9aa0a4", "#1baf7a", "#15181b"
    col = lambda v: SIGHT if v["preview"] else BLIND
    names = list(agents)
    written = []

    # 1. every policy, median damage and IQR
    fig, ax = plt.subplots(figsize=(9, 0.32 * (len(names) + len(hand)) + 1.4))
    rows = [(n, v["summary"], GREY if n != "current-grade" else GREEN) for n, v in hand.items()] + \
           [(n, v["summary"], col(v)) for n, v in agents.items()]
    for i, (n, s, c) in enumerate(rows):
        ax.barh(i, s["damage"]["median"], color=c, height=0.62)
        ax.plot([s["damage"]["q1"], s["damage"]["q3"]], [i, i], color=INK, lw=1.3)
        ax.text(max(s["damage"]["median"], s["damage"]["q3"]) + 8, i,
                f"cuts {s['cut_pct']:.1f} %", va="center", fontsize=8)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("median episode damage over the twenty frozen episodes (bar), interquartile range (line)")
    ax.set_title(f"{set_name}: every policy on the locked climb", loc="left", fontsize=11, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(fdir, "damage_by_policy.png"), dpi=130)
    plt.close(fig)
    written.append("damage_by_policy.png")

    # 2. the ablation, paired by seed
    P = stats_.get("pairs", [])
    if P:
        fig, ax = plt.subplots(figsize=(8, 0.42 * len(P) + 1.6))
        for i, p in enumerate(P):
            ax.plot([p["blinded"], p["sighted"]], [i, i], color=GREY, lw=1.5, zorder=1)
            ax.scatter(p["sighted"], i, color=SIGHT, s=46, zorder=2, label="sighted" if i == 0 else None)
            ax.scatter(p["blinded"], i, color=BLIND, s=46, zorder=2, label="blinded" if i == 0 else None)
            ax.text(max(p["sighted"], p["blinded"]) + 1.0, i, f"{p['sighted'] - p['blinded']:+.1f}",
                    va="center", fontsize=8)
        gc = hand["current-grade"]["summary"]["cut_pct"]
        ax.axvline(gc, color=GREEN, ls="--", lw=1.4, label="current-grade, no preview")
        ax.set_yticks(range(len(P)))
        ax.set_yticklabels([f"seed {p['seed']}" for p in P], fontsize=8)
        ax.invert_yaxis()
        ax.set_xlabel("median damage cut against the baseline ECU (%)")
        extra = (f"mean {stats_['mean']:+.2f} pts, 95 % CI {stats_['ci95'][0]:+.1f} to {stats_['ci95'][1]:+.1f}, "
                 f"t-test p {stats_['p_t']:.2f}, Wilcoxon p {stats_['p_wilcoxon']:.2f}, n {stats_['n']}") \
            if "mean" in stats_ else ""
        ax.set_title(f"{set_name}: sighted against blinded, paired by seed\n{extra}", loc="left", fontsize=10)
        ax.legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(1.0, 1.0))
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        fig.savefig(os.path.join(fdir, "ablation_by_seed.png"), dpi=130)
        plt.close(fig)
        written.append("ablation_by_seed.png")

    # 3. what each actuator did on the climb, every agent against the neutral
    fig, axs = plt.subplots(1, 5, figsize=(15, 0.28 * len(names) + 1.8), sharey=True)
    for j, (ax, act) in enumerate(zip(axs, ACTUATORS)):
        for i, n in enumerate(names):
            r = agents[n]["_rec"]
            m = r["grade"] > 0
            v = r["applied"][..., j][m]
            ax.plot([np.percentile(v, 5), np.percentile(v, 95)], [i, i], color=col(agents[n]), lw=2)
            ax.scatter(np.median(v), i, color=col(agents[n]), s=18, zorder=3)
        nv = agents[names[0]]["summary_actions"][act]["neutral"]
        ax.axvline(nv, color=INK, lw=0.9, ls=":")
        ax.set_title(act, fontsize=9)
        ax.spines[["top", "right"]].set_visible(False)
    axs[0].set_yticks(range(len(names)))
    axs[0].set_yticklabels(names, fontsize=7)
    axs[0].invert_yaxis()
    fig.suptitle(f"{set_name}: what the actuators did on the climb -- median, 5th-95th percentile; "
                 "dotted = the baseline's own setting", x=0.01, ha="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(fdir, "actions_on_the_climb.png"), dpi=130)
    plt.close(fig)
    written.append("actions_on_the_climb.png")

    # 4. one episode, step by step: every agent's actions and the turbine
    fig, axs = plt.subplots(6, 1, figsize=(11, 12), sharex=True)
    t = np.arange(agents[names[0]]["_rec"]["applied"].shape[1])
    for n in names:
        r = agents[n]["_rec"]
        for j in range(5):
            axs[j].plot(t, r["applied"][0, :, j], color=col(agents[n]), lw=0.8, alpha=0.7)
        axs[5].plot(t, r["t_turb"][0] - 273.15, color=col(agents[n]), lw=0.8, alpha=0.7)
    for hn, hc in (("baseline ECU", INK), ("current-grade", GREEN)):
        r = hand[hn]["_rec"]
        for j in range(5):
            axs[j].plot(t, r["applied"][0, :, j], color=hc, lw=1.4, ls="--")
        axs[5].plot(t, r["t_turb"][0] - 273.15, color=hc, lw=1.4, ls="--", label=hn)
    for j, act in enumerate(ACTUATORS):
        axs[j].set_ylabel(act, fontsize=8)
    axs[5].axhline(850, color="#d03b3b", lw=0.9, ls=":")
    axs[5].set_ylabel("turbine (C)", fontsize=8)
    axs[5].set_xlabel("time into episode 1 of the twenty (s); the grade starts at 180 s")
    axs[5].legend(frameon=False, fontsize=8)
    for ax in axs:
        ax.axvspan(180, t[-1], color="#ebede9", zorder=0)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"{set_name}: one frozen episode, every agent (purple sighted, pink blinded)",
                 x=0.01, ha="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(fdir, "episode1_actions.png"), dpi=120)
    plt.close(fig)
    written.append("episode1_actions.png")

    # 5. training curves, where they exist
    have = [n for n in names if agents[n].get("_curve") is not None]
    if have:
        fig, ax = plt.subplots(figsize=(10, 4.5))
        for n in have:
            c = agents[n]["_curve"]
            ax.plot(c["episode"], c["return"], color=col(agents[n]), lw=0.8, alpha=0.6)
        ax.axhline(0, color=INK, lw=0.8, ls="--")
        ax.set_xlabel("training episode")
        ax.set_ylabel("episode return")
        ax.set_title(f"{set_name}: every training run. Returns are NOT comparable episode to episode "
                     "(new weights, new road each time)", loc="left", fontsize=9)
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        fig.savefig(os.path.join(fdir, "training_curves.png"), dpi=130)
        plt.close(fig)
        written.append("training_curves.png")
    return written


# ---------------------------------------------------------------- main
def read_curve(path):
    if not os.path.exists(path):
        return None
    import pandas as pd
    c = pd.read_csv(path)
    c.columns = [x.strip() for x in c.columns]
    return dict(episode=c.iloc[:, 0].to_numpy(float), **{"return": c["return"].to_numpy(float)})


def save_record(path, rec):
    """float32 for actions, rewards and the engine; float16 for the (normalised)
    observation; integers and the preference weights exactly as they are."""
    def cast(k, v):
        if np.issubdtype(v.dtype, np.integer) or k == "weights":
            return v
        return v.astype(np.float32 if k in F32 else np.float16)
    np.savez_compressed(path, **{k: cast(k, v) for k, v in rec.items()})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("set_dir", nargs="?", help="a folder of <tag>/final.zip, e.g. runs/terrain_dt1")
    ap.add_argument("--name", help="the set's name under results/agents/ (default: from the folder)")
    ap.add_argument("--hand", action="store_true", help="record the hand-written policies only")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--report-only", action="store_true",
                    help="rebuild README, index and figures from the records already written")
    ap.add_argument("--limit", type=int, default=None,
                    help="only the first N frozen episodes -- a quick check of this script, never a result")
    a = ap.parse_args()
    import evaluate as E
    episodes = range(len(E.EPISODES) if a.limit is None else min(a.limit, len(E.EPISODES)))

    agent_dirs = []
    if a.set_dir:
        agent_dirs = sorted(os.path.relpath(os.path.dirname(p), HERE).replace(os.sep, "/")
                            for p in glob.glob(os.path.join(HERE, a.set_dir, "*_seed*", "final.zip")))
        agent_dirs.sort(key=lambda d: ("blind" in d, int(d.split("seed")[-1])))
        if not agent_dirs:
            raise SystemExit(f"no <tag>/final.zip under {a.set_dir}")
    set_name = a.name or ("hand_written" if a.hand and not a.set_dir
                          else os.path.basename(os.path.normpath(a.set_dir)))
    if a.limit is not None:
        set_name += "_TEST"
    outdir = os.path.join(OUTROOT, set_name)
    os.makedirs(outdir, exist_ok=True)
    if a.report_only:
        return report_from_disk(outdir, set_name)

    specs = [("hand", h) for h, _ in HAND] + [("agent", d) for d in agent_dirs]
    jobs = [(s, i) for s in specs for i in episodes]
    print(f"{set_name}: {len(specs)} policies x {len(episodes)} frozen episodes = {len(jobs)} episodes, "
          f"{a.jobs} workers")
    t0 = time.time()
    res = {s: [None] * len(episodes) for s in specs}
    recs = {s: [None] * len(episodes) for s in specs}
    with ProcessPoolExecutor(max_workers=a.jobs, initializer=_init_worker) as ex:
        for k, (spec, i, row, arr) in enumerate(ex.map(_job, jobs, chunksize=1)):
            res[spec][i], recs[spec][i] = row, arr
            if (k + 1) % 40 == 0:
                print(f"  {k + 1} of {len(jobs)} episodes, {(time.time() - t0) / 60:.1f} min")
    stacked = {s: {k: np.stack([r[k] for r in recs[s]]) for k in recs[s][0]} for s in specs}

    # ---- the regression check: identical to the published protocol rows
    raw_path = os.path.join(HERE, "results", "phase_d_130kmh_raw.json")
    checked, bad = 0, []
    if os.path.exists(raw_path):
        with open(raw_path) as fh:
            raw = json.load(fh)
        for s in specs:
            label = s[1]
            for r in raw:
                if r["policy"] == label and r["episode"] < len(episodes):
                    mine = res[s][r["episode"]]
                    checked += 1
                    if not np.isclose(mine["damage"], r["damage"], rtol=1e-9, atol=1e-9):
                        bad.append((label, r["episode"], mine["damage"], r["damage"]))
    if bad:
        raise SystemExit(f"RECORDING CHANGED A SCORE -- stop. {bad[:5]}")
    print(f"regression: {checked} episodes compared with results/phase_d_130kmh_raw.json, all identical")

    base = res[("hand", "baseline ECU")]
    base_med = float(np.median([r["damage"] for r in base]))
    base_fuel = float(np.median([r["fuel"] for r in base]))
    base_th = float(np.median([r["damage_thermal"] for r in base]))

    hand, agents = {}, {}
    for s in specs:
        name = s[1] if s[0] == "hand" else os.path.basename(s[1])
        d = os.path.join(outdir, name.replace(" ", "_").replace("(", "").replace(")", ""))
        os.makedirs(d, exist_ok=True)
        summ = summarise(res[s], base_med, base_fuel, base_th)
        acts = action_stats(stacked[s])
        entry = dict(summary=summ, summary_actions=acts, _rec=stacked[s], dir=d)
        if s[0] == "agent":
            cfg = config_for(s[1], set_name)
            curve = read_curve(os.path.join(HERE, s[1], "curve.csv"))
            if curve is not None:
                cfg.setdefault("episodes", int(len(curve["episode"])))
            entry.update(seed=cfg.get("seed"), preview=bool(cfg.get("preview")), config=cfg, _curve=curve)
            with open(os.path.join(d, "config.json"), "w") as fh:
                json.dump(cfg, fh, indent=1)
            for f in ("curve.csv", "train_record.npz"):
                src = os.path.join(HERE, s[1], f)
                if os.path.exists(src):
                    shutil.copy2(src, os.path.join(d, f))
            entry["policy_params"] = export_policy(s[1], os.path.join(d, "policy.npz"))
            agents[name] = entry
        else:
            # what the policy READS: only the predictive hand-written policy
            # looks at the road ahead; the others ignore the preview channel
            entry.update(preview=(name == "predictive (hand)"))
            hand[name] = entry
        save_record(os.path.join(d, "eval_record.npz"), dict(
            stacked[s], episode_seed=np.array([E.EPISODES[i][0] for i in episodes]),
            weights=np.array([E.EPISODES[i][1] for i in episodes])))
        with open(os.path.join(d, "eval_summary.json"), "w") as fh:
            json.dump(dict(policy=name, protocol="evaluate.EPISODES, twenty frozen episodes, 720 s, dt 1.0, "
                                                 "the locked 12 % / 130 km/h climb at 42 C",
                           episodes=res[s], summary=summ, actions=acts,
                           engine_on_climb=engine_stats(stacked[s])), fh, indent=1)

    report(outdir, set_name, hand, agents, checked, (time.time() - t0) / 60)
    print(f"wrote {os.path.relpath(outdir, HERE)}/  ({(time.time() - t0) / 60:.1f} min)")


def report(outdir, set_name, hand, agents, checked, minutes):
    """README, index.json and figures from the scored and recorded policies."""
    stats_ = paired(agents, hand["current-grade"]["summary"]["cut_pct"]) if agents else {}
    figs = figures(outdir, agents, hand, stats_, set_name) if agents else []
    notes = findings(hand, agents)
    write_readme(outdir, set_name, hand, agents, stats_, figs, checked, minutes, notes)
    base_med = hand["baseline ECU"]["summary"]["damage"]["median"]
    index = dict(set=set_name, generated=time.strftime("%Y-%m-%d %H:%M"), baseline_median_damage=base_med,
                 regression_checked=checked,
                 policies={n: dict(v["summary"], actions=v["summary_actions"],
                                   **({"config": v["config"]} if "config" in v else {}))
                           for n, v in {**hand, **agents}.items()},
                 ablation=stats_, findings=notes)
    with open(os.path.join(outdir, "index.json"), "w") as fh:
        json.dump(index, fh, indent=1)


def report_from_disk(outdir, set_name):
    """Everything report() needs, read back from the folders a full run wrote."""
    hand, agents = {}, {}
    old = {}
    if os.path.exists(os.path.join(outdir, "index.json")):
        with open(os.path.join(outdir, "index.json")) as fh:
            old = json.load(fh)
    for d in sorted(glob.glob(os.path.join(outdir, "*", "eval_summary.json"))):
        d = os.path.dirname(d)
        with open(os.path.join(d, "eval_summary.json")) as fh:
            S = json.load(fh)
        rec = dict(np.load(os.path.join(d, "eval_record.npz")))
        if "engine_on_climb" not in S:            # summaries written before 29 Sep, evening
            S["engine_on_climb"] = engine_stats(rec)
            with open(os.path.join(d, "eval_summary.json"), "w") as fh:
                json.dump(S, fh, indent=1)
        entry = dict(summary=S["summary"], summary_actions=S["actions"], _rec=rec, dir=d,
                     episodes=S["episodes"])
        cfg_p = os.path.join(d, "config.json")
        if os.path.exists(cfg_p):
            with open(cfg_p) as fh:
                cfg = json.load(fh)
            entry.update(seed=cfg.get("seed"), preview=bool(cfg.get("preview")), config=cfg,
                         _curve=read_curve(os.path.join(d, "curve.csv")))
            agents[S["policy"]] = entry
        else:
            entry.update(preview=(S["policy"] == "predictive (hand)"))
            hand[S["policy"]] = entry
    order = [h for h, _ in HAND]
    hand = {k: hand[k] for k in order if k in hand}
    agents = dict(sorted(agents.items(), key=lambda kv: (not kv[1]["preview"], kv[1]["seed"])))
    report(outdir, set_name, hand, agents, old.get("regression_checked", 0), 0.0)
    print(f"rebuilt the report in {os.path.relpath(outdir, HERE)}/ from its records")


def findings(hand, agents):
    """What stands out, computed from the records -- no sentence without its number."""
    import evaluate as E
    if not agents:
        return []
    out = []
    base = hand["baseline ECU"]
    br = base["_rec"]
    climb = br["grade"] > 0
    ki_base = float(np.percentile(br["ki"][climb], 95))
    sp_base = float(np.median(br["spark"][climb]))
    trims = [float(np.median(v["_rec"]["applied"][..., 0][v["_rec"]["grade"] > 0])) for v in agents.values()]
    kis = [float(np.percentile(v["_rec"]["ki"][v["_rec"]["grade"] > 0], 95)) for v in agents.values()]
    out.append(f"SPARK. On the climb every agent advances spark {min(trims):.1f}-{max(trims):.1f} deg past the "
               f"baseline (median; the trim's upper bound is +4), whose own spark there is {sp_base:.1f} deg. That "
               f"takes the modelled knock integral from the baseline's {ki_base:.2f} to {min(kis):.2f}-{max(kis):.2f} "
               f"(95th percentile), just under the 0.85 knee where the damage model starts charging for knock. "
               f"Part of what the agents save is margin the production-representative baseline keeps and the "
               f"UNTESTED knock model says is not needed (CLAUDE.md, the knock model). Sighted and blinded do "
               f"it alike, so it does not touch the ablation; it does touch every agent-versus-hand-written gap. "
               f"How much of the gain it is: KNOCK_MARGIN.md beside this file (knock_margin.py), where it exists.")
    base_dmg = base["summary"]["damage"]["median"]
    w_life = np.array([e[1][2] for e in E.EPISODES])
    for n, v in agents.items():
        eps = v.get("episodes") or []
        if not eps:
            with open(os.path.join(v["dir"], "eval_summary.json")) as fh:
                eps = json.load(fh)["episodes"]
        bad = [i for i, e in enumerate(eps) if e["damage"] > base_dmg]
        if bad:
            low = sorted(np.argsort(w_life)[:len(bad)].tolist())
            out.append(f"{n.upper()} does MORE damage than the baseline ECU on {len(bad)} of {len(eps)} episodes "
                       f"(numbers {', '.join(map(str, bad))}; worst {max(eps[i]['damage'] for i in bad):.0f} "
                       f"against {base_dmg:.0f}, peak turbine {max(eps[i]['peak_turb'] for i in bad):.0f} C). "
                       f"Their weight on component life is {', '.join(f'{w_life[i]:.3f}' for i in bad)}"
                       + (" -- exactly the lowest in the frozen set" if bad == low else "")
                       + ". The reward lets an agent trade life for fuel when life is weighted that little; "
                       "by evaluate.py's own standard a protection policy that is sometimes terrible is not one.")
    best_hand = max(h["summary"]["cut_pct"] for h in hand.values())
    beat = [n for n, v in agents.items() if v["summary"]["cut_pct"] > best_hand]
    out.append(f"{len(beat)} of {len(agents)} agents beat the best hand-written policy on median damage "
               f"({best_hand:.1f} % cut). {sum(v['summary']['fuel_vs_baseline_pct'] < 0 for v in agents.values())} "
               f"burn less fuel than the baseline.")
    return out


def _nz(v, d, sign=False):
    """A number to d decimals, never "-0.0"; with sign=True, "+" on positives."""
    s = f"{v:+.{d}f}" if sign else f"{v:.{d}f}"
    if float(s) == 0:
        s = s.lstrip("+-")
        s = ("+" if sign else "") + s
    return s


def write_readme(outdir, set_name, hand, agents, st, figs, checked, minutes, notes=()):
    L = [f"# Agents: `{set_name}`", "",
         "Generated by `python record_agents.py` -- do not edit by hand; re-run it.", ""]
    if agents:
        c0 = next(iter(agents.values()))["config"]
        L += ["## How they were trained", ""]
        for k in ("trained", "scenario", "roads", "dt", "steps", "total_timesteps", "steps_per_episode",
                  "device", "plant", "git_commit", "status", "config_source"):
            if k in c0:
                L.append(f"- **{k}**: {c0[k]}")
        L.append(f"- **SAC**: {json.dumps(c0.get('sac', {}))}")
        if c0.get("plant_inputs"):
            L.append(f"- **plant data fingerprint**: `{json.dumps(c0['plant_inputs'])[:160]}`")
        L.append("")
    L += ["## Scored on the twenty frozen episodes (`evaluate.EPISODES`)", "",
          f"The locked 12 % / 130 km/h climb, 720 s at dt 1.0, 42 C. Scores are `evaluate.run_episode`'s; "
          f"{checked} episodes were compared with `results/phase_d_130kmh_raw.json` and are identical.", "",
          "| policy | preview | median damage | IQR | worst | cut % | thermal-only cut % | fuel vs baseline % "
          "| peak turbine C | torque violation (median) | episodes trained | wall min |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for n, v in {**hand, **agents}.items():
        s, cfg = v["summary"], v.get("config", {})
        L.append(f"| {n} | {'yes' if v['preview'] else 'no'} | {s['damage']['median']:.1f} "
                 f"| {s['damage']['q1']:.0f}-{s['damage']['q3']:.0f} | {s['damage']['worst']:.1f} "
                 f"| {_nz(s['cut_pct'], 1)} | {_nz(s['thermal_cut_pct'], 1)} | {_nz(s['fuel_vs_baseline_pct'], 2, sign=True)} "
                 f"| {s['peak_turb']['worst']:.0f} | {s['torque_viol']['median']:.1f} "
                 f"| {cfg.get('episodes', '-')} | {cfg.get('wall_min_this_session', '-')} |")
    L.append("")
    if notes:
        L += ["## What stands out", ""] + [f"- {x}" for x in notes] + [""]
    if st.get("n"):
        L += ["## The ablation, paired by seed", "",
              f"Sighted minus blinded damage cut, {st['n']} pairs: mean **{st['mean']:+.2f}** points "
              f"(median {st['median']:+.2f}, sd {st['sd']:.2f}), 95 % CI {st['ci95'][0]:+.2f} to "
              f"{st['ci95'][1]:+.2f}; paired t-test p = {st['p_t']:.3f}, exact Wilcoxon p = "
              f"{st['p_wilcoxon']:.3f} (the smallest this n can give is {st['smallest_possible_p_wilcoxon']:.4f}). "
              f"Thermal-only damage (no knock term): mean {st['thermal_mean']:+.2f} points, t-test p = "
              f"{st['p_t_thermal']:.3f}.", "",
              "| seed | sighted cut % | blinded cut % | difference | sighted minus current-grade |",
              "|---|---|---|---|---|"]
        for p, g in zip(st["pairs"], st["sighted_over_grade"]):
            L.append(f"| {p['seed']} | {p['sighted']:.2f} | {p['blinded']:.2f} | "
                     f"{p['sighted'] - p['blinded']:+.2f} | {g:+.2f} |")
        L.append("")
    L += ["## What the actuators did", "",
          "Applied values after the slew limit, over all twenty episodes; median and 5th-95th percentile, "
          "flat road | climb. `neutral` is the baseline's own setting (trims 0; fan and pump at what the "
          "baseline runs). `slew %` is the share of steps where the policy asked for more movement than "
          "the slew limit allowed.", "",
          "| policy | " + " | ".join(ACTUATORS) + " |", "|---|" + "---|" * 5]
    for n, v in {**hand, **agents}.items():
        cells = []
        for act in ACTUATORS:
            d = v["summary_actions"][act]
            fl, cl = d.get("flat", {}), d.get("climb", {})
            cells.append(f"{fl.get('p50', float('nan')):.2f} [{fl.get('p5', float('nan')):.2f}, "
                         f"{fl.get('p95', float('nan')):.2f}] &#124; {cl.get('p50', float('nan')):.2f} "
                         f"[{cl.get('p5', float('nan')):.2f}, {cl.get('p95', float('nan')):.2f}]; "
                         f"slew {d['slew_limited_pct']:.0f} %")
        L.append(f"| {n} | " + " | ".join(cells) + " |")
    L += ["", "## Files", "",
          "Per policy, in its folder: `eval_summary.json` (every episode scored), `eval_record.npz` "
          "(every step of the twenty episodes, arrays `[episode, step, ...]`: `action`, `applied`, `obs`, "
          "`reward`, `r_fuel`, `r_life`, `r_resp`, `rpm`, `map_kpa`, `grade`, `spark`, `lam`, `torque`, "
          "`torque_req`, `ki`, `egt_c`, `mdot_fuel`, `t_turb`, `t_oil`, `t_block`, `t_turb_base`, "
          "`damage_rate`, plus `episode_seed` and `weights`). Per agent also: `config.json`, `curve.csv`, "
          "`policy.npz` (the actor's weights) and, for agents trained since 29 September, "
          "`train_record.npz` (every training step: `step`, `episode`, `action`, `obs`, `reward`, the "
          "reward terms and the engine state).", "",
          "**The two `*_record.npz` files are kept on disk and not in git** (the team's decision, "
          "29 September: 85 MB of binaries). They stay on the machine that trained the agents, beside "
          "the models in `runs/` (also gitignored): only there can `python record_agents.py <set>` "
          "regenerate `eval_record.npz`, and `train_record.npz` cannot be regenerated at all. Everything "
          "else here is committed, and `eval_summary.json` carries the statistics read from the records.", ""]
    if figs:
        L += ["## Figures", ""] + [f"![{f}](figures/{f})" for f in figs] + [""]
    if minutes:
        L.append(f"_{minutes:.0f} min to generate._")
    with open(os.path.join(outdir, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()

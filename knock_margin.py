"""knock_margin.py -- how much of each agent's gain rests on spark advance?

    python knock_margin.py                    # the twenty agents of runs/terrain_dt1
    python knock_margin.py runs/terrain_dt1
    python knock_margin.py --report-only      # rebuild the report from knock_margin.json

MEASURED 29 September 2026 (~40 min on the team laptop): with advance
forbidden the median cut falls from 67.9 to 41.6 % (sighted) and from 65.4 to
41.7 % (blinded), against current-grade's 43.4 %; 9 of 20 still beat it, and
the margin over it, median of all twenty, goes from +24.4 to -1.8 points. Most of what the
agents gain over the hand-written policies is spark advance the untested knock
model allows. Sighted minus blinded under the cap: -0.95 points, n = 10.

Written 29 September 2026. Every retrained agent advances spark 3.5-4 deg past
the baseline ECU on the climb, taking the modelled knock integral to 0.77-0.79
-- just under the damage model's 0.85 knee -- where the baseline, like a
production ECU, keeps a margin (0.61). The knock model is untested against this
car (CLAUDE.md, "The knock model is not validated"). So part of every agent's
gain over the hand-written policies may be margin that only the model grants.

This re-scores every agent on the twenty frozen episodes with SPARK ADVANCE
FORBIDDEN: the agent's own action at every step, except that its spark trim is
capped at zero -- the baseline's own knock-limited spark. Retard is still
allowed; nothing else the agent does is touched. The hand-written policies never
advance spark (check_premise._protect's trim is 0), so they are unaffected and
current-grade's 43.4 % is still the comparator.

A DIAGNOSTIC BESIDE THE PROTOCOL, NOT A CHANGE TO IT. evaluate.EPISODES and
evaluate.run_episode are used exactly as shipped; only the policy is wrapped.
The agents never trained with the cap, so once their spark differs the rest of
their behaviour is out of distribution. Read the result as "how much of the gain
survives when this one lever is taken away", not as what an agent trained
without it would do.

Writes results/agents/<set>/knock_margin.json, KNOCK_MARGIN.md and
figures/knock_margin.png.
"""
import glob
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
_MODELS = {}


def _spark_neutral():
    """The spark trim's zero in the policy's [-1, 1] units."""
    from engine_env import ACT_LO, ACT_HI
    return float(2.0 * (0.0 - ACT_LO[0]) / (ACT_HI[0] - ACT_LO[0]) - 1.0)


def _init():
    import torch
    torch.set_num_threads(1)


def _job(job):
    agent_dir, i = job
    import evaluate as E
    from stable_baselines3 import SAC
    if agent_dir not in _MODELS:
        _MODELS[agent_dir] = SAC.load(os.path.join(HERE, agent_dir, "final"), device="cpu")
    model, cap = _MODELS[agent_dir], _spark_neutral()

    def capped(env, obs):
        a, _ = model.predict(obs, deterministic=True)
        a = np.array(a, dtype=np.float32, copy=True)
        a[0] = min(a[0], cap)                    # no advance past the baseline's spark
        return a

    seed, w = E.EPISODES[i]
    rec = E.new_record()
    row = E.run_episode(capped, seed, w, "blind" not in os.path.basename(agent_dir), record=rec)
    g = np.asarray(rec["grade"]) > 0
    row.update(ki_p95_climb=float(np.percentile(np.asarray(rec["ki"])[g], 95)),
               trim_climb=float(np.median(np.asarray(rec["applied"])[g, 0])))
    return agent_dir, i, row


def main():
    import evaluate as E
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    set_dir = (args[0] if args else "runs/terrain_dt1").rstrip("/\\")
    if "--report-only" in sys.argv:            # rebuild the report from knock_margin.json
        res_dir = os.path.join(HERE, "results", "agents", os.path.basename(set_dir))
        with open(os.path.join(res_dir, "knock_margin.json")) as fh:
            J = json.load(fh)
        grade = dict(cut_pct=J["summary"]["grade_cut"], thermal_cut_pct=J["summary"]["grade_thermal"])
        write_all(res_dir, J["agents"], summarise(J["agents"], grade, J["summary"]["base_median_damage"],
                                                  J["summary"]["minutes"]))
        print("rebuilt the knock-margin report from knock_margin.json")
        return
    set_name = os.path.basename(set_dir)
    res_dir = os.path.join(HERE, "results", "agents", set_name)
    agents = sorted(os.path.relpath(os.path.dirname(p), HERE).replace(os.sep, "/")
                    for p in glob.glob(os.path.join(HERE, set_dir, "*_seed*", "final.zip")))
    agents.sort(key=lambda d: ("blind" in d, int(d.split("seed")[-1])))
    jobs = [(a, i) for a in agents for i in range(len(E.EPISODES))]
    print(f"{len(agents)} agents x {len(E.EPISODES)} frozen episodes, spark advance forbidden")
    t0 = time.time()
    rows = {a: [None] * len(E.EPISODES) for a in agents}
    with ProcessPoolExecutor(max_workers=os.cpu_count(), initializer=_init) as ex:
        for a, i, row in ex.map(_job, jobs, chunksize=1):
            rows[a][i] = row

    def load(name):
        with open(os.path.join(res_dir, name, "eval_summary.json")) as fh:
            return json.load(fh)
    base = load("baseline_ECU")["episodes"]
    base_med = float(np.median([r["damage"] for r in base]))
    base_th = float(np.median([r["damage_thermal"] for r in base]))
    base_f = float(np.median([r["fuel"] for r in base]))
    grade = load("current-grade")["summary"]
    out = {}
    for a in agents:
        tag = os.path.basename(a)
        orig = load(tag)["summary"]
        r = rows[a]
        med = float(np.median([x["damage"] for x in r]))
        cut = 100.0 * (1.0 - med / base_med)
        th = 100.0 * (1.0 - float(np.median([x["damage_thermal"] for x in r])) / base_th)
        out[tag] = dict(preview="blind" not in tag, seed=int(tag.split("seed")[-1]),
                        cut=cut, cut_orig=orig["cut_pct"], thermal=th, thermal_orig=orig["thermal_cut_pct"],
                        over_grade=cut - grade["cut_pct"], over_grade_orig=orig["cut_pct"] - grade["cut_pct"],
                        fuel_pct=100.0 * (float(np.median([x["fuel"] for x in r])) / base_f - 1.0),
                        fuel_pct_orig=orig["fuel_vs_baseline_pct"],
                        peak=max(x["peak_turb"] for x in r),
                        worst=max(x["damage"] for x in r),
                        ki_p95_climb=float(np.median([x["ki_p95_climb"] for x in r])),
                        trim_climb=float(np.median([x["trim_climb"] for x in r])),
                        episodes=r)

    summary = summarise(out, grade, base_med, (time.time() - t0) / 60)
    write_all(res_dir, out, summary)


def summarise(out, grade, base_med, minutes):
    """The margin over current-grade before and after, and the ablation under
    the cap. (A 'share of the gain kept' ratio was tried first and dropped: it
    reads -423 % for an agent whose margin changes sign, which says nothing.)"""
    from scipy import stats
    pairs = []
    for s in sorted({v["seed"] for v in out.values()}):
        a_, b_ = out.get(f"sighted_seed{s}"), out.get(f"blind_seed{s}")
        if a_ and b_:
            pairs.append((s, a_["cut"], b_["cut"]))
    d = np.array([x[1] - x[2] for x in pairs])
    half = stats.t.ppf(0.975, len(d) - 1) * d.std(ddof=1) / np.sqrt(len(d))
    med = lambda k, pv: float(np.median([v[k] for v in out.values() if v["preview"] == pv]))
    og = [v["over_grade"] for v in out.values()]
    return dict(
        grade_cut=grade["cut_pct"], grade_thermal=grade["thermal_cut_pct"],
        sighted_cut=med("cut", True), sighted_cut_orig=med("cut_orig", True),
        blind_cut=med("cut", False), blind_cut_orig=med("cut_orig", False),
        sighted_thermal=med("thermal", True), blind_thermal=med("thermal", False),
        beat_grade=int(sum(v["cut"] > grade["cut_pct"] for v in out.values())), n=len(out),
        over_grade_median=float(np.median(og)), over_grade_min=float(min(og)), over_grade_max=float(max(og)),
        over_grade_median_orig=float(np.median([v["over_grade_orig"] for v in out.values()])),
        ki_p95_lo=min(v["ki_p95_climb"] for v in out.values()), ki_p95_hi=max(v["ki_p95_climb"] for v in out.values()),
        ablation=dict(n=len(d), mean=float(d.mean()), ci95=[float(d.mean() - half), float(d.mean() + half)],
                      p_t=float(stats.ttest_1samp(d, 0.0).pvalue),
                      p_wilcoxon=float(stats.wilcoxon(d).pvalue) if np.any(d != 0) else 1.0,
                      pairs=[dict(seed=s, sighted=a_, blinded=b_) for s, a_, b_ in pairs]),
        worst_episode=max(v["worst"] for v in out.values()),
        worst_agent=max(out, key=lambda k: out[k]["worst"]),
        base_median_damage=base_med, minutes=minutes)


def write_all(res_dir, out, summary):
    with open(os.path.join(res_dir, "knock_margin.json"), "w") as fh:
        json.dump(dict(what="twenty frozen episodes, the agent's own action with spark trim capped at 0 "
                            "(no advance past the baseline's knock-limited spark); a diagnostic, not the protocol",
                       generated=time.strftime("%Y-%m-%d %H:%M"), summary=summary, agents=out), fh, indent=1)
    figure(res_dir, out, summary)
    report(res_dir, out, summary)
    S = summary
    print(f"sighted median cut {S['sighted_cut_orig']:.1f} -> {S['sighted_cut']:.1f} %, blinded "
          f"{S['blind_cut_orig']:.1f} -> {S['blind_cut']:.1f} % (current-grade {S['grade_cut']:.1f} %)")
    print(f"{S['beat_grade']} of {S['n']} still beat current-grade; margin over it, median of all "
          f"{S['n']}: {S['over_grade_median_orig']:+.1f} -> {S['over_grade_median']:+.1f} points")
    A = S["ablation"]
    print(f"ablation under the cap: {A['mean']:+.2f} pts, 95 % CI {A['ci95'][0]:+.2f} to {A['ci95'][1]:+.2f}, "
          f"t p {A['p_t']:.2f}, Wilcoxon p {A['p_wilcoxon']:.2f}, n {A['n']}")
    print(f"wrote {os.path.relpath(res_dir, HERE)}/knock_margin.json, KNOCK_MARGIN.md  ({S['minutes']:.0f} min)")


def figure(res_dir, out, S):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    names = list(out)
    fig, ax = plt.subplots(figsize=(9, 0.34 * len(names) + 1.6))
    for i, n in enumerate(names):
        v = out[n]
        c = "#4a3aa7" if v["preview"] else "#e87ba4"
        ax.plot([v["cut"], v["cut_orig"]], [i, i], color="#9aa0a4", lw=1.6, zorder=1)
        ax.scatter(v["cut_orig"], i, color=c, s=40, zorder=2, label="as trained" if i == 0 else None)
        ax.scatter(v["cut"], i, facecolor="none", edgecolor=c, s=46, lw=1.6, zorder=3,
                   label="spark advance forbidden" if i == 0 else None)
    ax.axvline(S["grade_cut"], color="#1baf7a", ls="--", lw=1.4, label="current-grade, hand-written")
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("median damage cut against the baseline ECU, twenty frozen episodes (%)")
    ax.set_title("How much of each agent's gain rests on spark advance (filled: as trained; "
                 "hollow: trim capped at 0)", loc="left", fontsize=9.5)
    ax.legend(frameon=False, fontsize=8, loc="lower left", bbox_to_anchor=(0.0, 1.06), ncol=3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    os.makedirs(os.path.join(res_dir, "figures"), exist_ok=True)
    fig.savefig(os.path.join(res_dir, "figures", "knock_margin.png"), dpi=130)
    plt.close(fig)


def report(res_dir, out, S):
    A = S["ablation"]
    L = ["# Knock margin: the agents with spark advance forbidden", "",
         "Generated by `python knock_margin.py` -- do not edit by hand. A diagnostic beside the twenty-episode "
         "protocol: each agent's own action, with its spark trim capped at 0 (no advance past the baseline "
         "ECU's knock-limited spark; retard allowed). The agents never trained with the cap, so everything "
         "they do after the spark differs is out of distribution.", "",
         f"- **Median cut, sighted:** {S['sighted_cut_orig']:.1f} % as trained, **{S['sighted_cut']:.1f} %** "
         f"with advance forbidden. **Blinded:** {S['blind_cut_orig']:.1f} % -> **{S['blind_cut']:.1f} %**. "
         f"Current-grade: {S['grade_cut']:.1f} %.",
         f"- **{S['beat_grade']} of {S['n']}** still beat current-grade. The margin over it, median of "
         f"all {S['n']}: **{S['over_grade_median_orig']:+.1f} points as trained, {S['over_grade_median']:+.1f} "
         f"with advance forbidden** (range {S['over_grade_min']:+.1f} to {S['over_grade_max']:+.1f}).",
         "- **Read it as a lower bound.** The agents learned everything else together with the spark "
         "advance; an agent TRAINED without the lever could do better than one that has it taken away. "
         "What it does show: most of the margin over the hand-written policies, as trained, comes from "
         "running closer to knock than the baseline does, which only the untested knock model allows.",
         f"- Knock integral on the climb, 95th percentile: {S['ki_p95_lo']:.2f}-{S['ki_p95_hi']:.2f} with the cap.",
         f"- **The ablation under the cap:** sighted minus blinded {A['mean']:+.2f} points, 95 % CI "
         f"{A['ci95'][0]:+.2f} to {A['ci95'][1]:+.2f}, paired t p = {A['p_t']:.2f}, exact Wilcoxon p = "
         f"{A['p_wilcoxon']:.2f}, n = {A['n']}.",
         f"- Worst single episode with the cap: {S['worst_episode']:.0f} ({S['worst_agent']}), against the "
         f"baseline's {S['base_median_damage']:.0f}.", "",
         "| agent | cut as trained | cut, advance forbidden | thermal-only, forbidden | over current-grade, "
         "forbidden | fuel vs baseline, forbidden | knock p95 on the climb |",
         "|---|---|---|---|---|---|---|"]
    for n, v in out.items():
        L.append(f"| {n} | {v['cut_orig']:.1f} % | {v['cut']:.1f} % | {v['thermal']:.1f} % | "
                 f"{v['over_grade']:+.1f} | {v['fuel_pct']:+.2f} % | {v['ki_p95_climb']:.2f} |")
    L += ["", "![knock margin](figures/knock_margin.png)", ""]
    with open(os.path.join(res_dir, "KNOCK_MARGIN.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()

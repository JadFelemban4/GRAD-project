"""damage_robustness.py -- do the conclusions survive another damage ruler?

    python damage_robustness.py      prints the table, writes results/damage_robustness.json
                                     and results/figures/damage_robustness.png

Every constant of the damage model is a DESIGN choice, not a property of the
car (REFERENCES.md, the DESIGN row): the 1123 K knee, the 45 K scale, the oil
term's 0.4 weight, 408 K knee and 12 K scale, and the knock term's 40 and 0.85.
This re-scores the twenty frozen episodes of every policy under rulers that
change one constant at a time, and asks whether three conclusions move:

  1. every trained agent beats current-grade (the supervision claim);
  2. sighted minus blinded, paired by seed (the ablation);
  3. predictive minus current-grade, hand-written.

It reads the per-step records record_agents.py wrote (eval_record.npz: the
turbine, oil and knock integral at every step), which stay on the training
machine (gitignored), and first re-scores them under the published ruler and
requires the committed damage to the last digit.

WHAT IT CANNOT SAY. The agents were trained on the published ruler. This is a
test of the EVALUATION's sensitivity, not of what an agent trained on another
ruler would do.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SET = os.path.join(HERE, "results", "agents", "terrain_dt1")
HAND = ("baseline_ECU", "current-grade", "reactive", "predictive_hand")
PUBLISHED = dict(knee=1123.0, scale=45.0, w_oil=0.4, oil_knee=408.0, oil_scale=12.0,
                 w_knock=40.0, knock_knee=0.85)
RULERS = (
    ("as published", {}),
    ("turbine scale 30 K", {"scale": 30.0}),
    ("turbine scale 60 K", {"scale": 60.0}),
    ("turbine knee -25 K (825 C)", {"knee": 1098.0}),
    ("turbine knee +25 K (875 C)", {"knee": 1148.0}),
    ("no oil term", {"w_oil": 0.0}),
    ("oil term x4", {"w_oil": 1.6}),
    ("no knock term", {"w_knock": 0.0}),
    ("knock term x4", {"w_knock": 160.0}),
)


def damage(rec, c, dt=1.0):
    """Episode damage under ruler c, from the recorded steps: (episodes,)."""
    tt, to, ki = rec["t_turb"], rec["t_oil"], rec["ki"]
    d = (np.exp((tt - c["knee"]) / c["scale"])
         + c["w_oil"] * np.exp((to - c["oil_knee"]) / c["oil_scale"])
         + c["w_knock"] * np.maximum(0.0, ki - c["knock_knee"]) ** 2)
    return d.sum(axis=1) * dt


def load_records():
    """Every policy's recorded turbine, oil and knock integral, checked: the
    published ruler must give back the committed damage, episode by episode.
    The records hold the temperatures as float32 (record_agents.py
    save_record), so agreement is to float32 precision, about 1e-7 relative."""
    names = list(HAND) + sorted(n for n in os.listdir(SET) if n.startswith(("sighted_seed", "blind_seed")))
    recs, committed = {}, {}
    for n in names:
        r = np.load(os.path.join(SET, n, "eval_record.npz"))
        recs[n] = {k: np.asarray(r[k], float) for k in ("t_turb", "t_oil", "ki")}
        with open(os.path.join(SET, n, "eval_summary.json"), encoding="utf-8") as fh:
            committed[n] = np.array([e["damage"] for e in json.load(fh)["episodes"]])
    worst = max(float(np.max(np.abs(damage(recs[n], PUBLISHED) - committed[n]) / committed[n]))
                for n in names)
    assert worst < 1e-6, f"the re-score does not reproduce the committed damage (worst {worst:.2e})"
    return names, recs, worst


def score(names, recs, c):
    """The three conclusions under ruler c (a complete set of constants)."""
    from scipy import stats
    seeds = sorted(int(n.split("seed")[1]) for n in names if n.startswith("sighted_seed"))
    med = {n: float(np.median(damage(recs[n], c))) for n in names}
    cut = {n: 100.0 * (1.0 - med[n] / med["baseline_ECU"]) for n in names}
    diff = np.array([cut[f"sighted_seed{k}"] - cut[f"blind_seed{k}"] for k in seeds])
    half = float(stats.t.ppf(0.975, len(diff) - 1)) * diff.std(ddof=1) / np.sqrt(len(diff))
    agents = [n for n in names if "_seed" in n]
    return dict(
        base_damage=round(med["baseline_ECU"], 1),
        grade_cut=round(cut["current-grade"], 2),
        pred_minus_grade=round(cut["predictive_hand"] - cut["current-grade"], 2),
        sighted_median=round(float(np.median([cut[f"sighted_seed{k}"] for k in seeds])), 2),
        blind_median=round(float(np.median([cut[f"blind_seed{k}"] for k in seeds])), 2),
        beat_grade=int(sum(cut[n] > cut["current-grade"] for n in agents)), n=len(agents),
        weakest=min(agents, key=lambda n: cut[n]), weakest_cut=round(min(cut[n] for n in agents), 2),
        ablation_mean=round(float(diff.mean()), 2),
        ablation_lo=round(float(diff.mean() - half), 2),
        ablation_hi=round(float(diff.mean() + half), 2),
        ablation_positive=int((diff > 0).sum()),
        ablation_p_wilcoxon=round(float(stats.wilcoxon(diff).pvalue), 2))


def main():
    names, recs, worst = load_records()
    out = {label: score(names, recs, dict(PUBLISHED, **change)) for label, change in RULERS}

    print(f"re-score check: the published ruler reproduces the committed damage of {len(names)} "
          f"policies x 20 episodes (worst relative difference {worst:.1e})\n")
    print(f"{'ruler':28s} {'base':>7s} {'grade':>6s} {'pred-grade':>10s} {'sighted':>7s} {'blind':>6s} "
          f"{'>grade':>7s} {'weakest':>16s} {'ablation, 95 % CI':>24s} {'+':>3s} {'p (W)':>6s}")
    for label, s in out.items():
        print(f"{label:28s} {s['base_damage']:7.1f} {s['grade_cut']:6.1f} {s['pred_minus_grade']:+10.2f} "
              f"{s['sighted_median']:7.1f} {s['blind_median']:6.1f} {s['beat_grade']:3d}/{s['n']:<3d} "
              f"{s['weakest']:>11s} {s['weakest_cut']:4.1f} {s['ablation_mean']:+6.2f} "
              f"[{s['ablation_lo']:+6.2f}, {s['ablation_hi']:+6.2f}] {s['ablation_positive']:3d} "
              f"{s['ablation_p_wilcoxon']:6.2f}")
    print("\ncuts are % against the baseline ECU under the same ruler; ablation = sighted minus "
          "blinded cut, paired by seed; + = seeds where sighted is better")

    path = os.path.join(HERE, "results", "damage_robustness.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"published": PUBLISHED, "rulers": dict(RULERS), "summary": out}, fh, indent=1)
        fh.write("\n")
    print(f"wrote {os.path.relpath(path, HERE)}")
    figure(out)


def figure(out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    labels = list(out)
    y = np.arange(len(labels))[::-1]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 4.6), sharey=True)
    for yy, label in zip(y, labels):
        s = out[label]
        a1.plot([s["ablation_lo"], s["ablation_hi"]], [yy, yy], color="#4b5157", lw=2)
        a1.plot(s["ablation_mean"], yy, "o", color="#4a3aa7", ms=6)
        a2.plot(s["grade_cut"], yy, "s", color="#1baf7a", ms=7, label="current-grade" if yy == y[0] else None)
        a2.plot(s["sighted_median"], yy, "o", color="#4a3aa7", ms=6, label="sighted, median" if yy == y[0] else None)
        a2.plot(s["blind_median"], yy, "o", color="#e87ba4", ms=6, label="blinded, median" if yy == y[0] else None)
    a1.axvline(0, color="#d03b3b", lw=1, ls="--")
    a1.set_yticks(y, labels, fontsize=8.5)
    a1.set_xlabel("sighted minus blinded, points (mean, 95 % interval, 10 pairs)")
    a1.set_title("The ablation under each ruler", fontsize=10)
    a2.set_xlabel("damage cut against the baseline ECU, %")
    a2.set_title("The supervision claim under each ruler", fontsize=10)
    a2.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    path = os.path.join(HERE, "results", "figures", "damage_robustness.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=130)
    print(f"wrote {os.path.relpath(path, HERE)}")


if __name__ == "__main__":
    main()

"""knee_shift.py -- step 4 of engine_thresholds.py: how far d (sighted minus blinded cut, paired by
seed) moves when the turbine knee moves by a few kelvin, re-scored from the committed per-step records.

A uniform housing-temperature error e acts on a fixed-knee re-score exactly as a knee shift of -e
(damage_rate depends on T - K only). This is the measurement section 1.2c and row L1 of
results/ENGINE_THRESHOLDS.md rest on (mistake 22: the sentence needs the run that printed it).

Reads only results/agents/<set>/*/eval_record.npz and eval_summary.json, through
damage_robustness.load_records, which first requires the published formula to give back every
committed damage. The .npz records stay on the training machine (gitignored), so this step runs
only there. No EPA data, no model run, no fit. Writes results/ENGINE_THRESHOLDS/knee_shift.json.
"""
import os

import numpy as np

import damage_robustness as DR
from thresholds import common

OUT = os.path.join(common.OUT_DIR, "knee_shift.json")
SETS = ("terrain_dt1", "extremes_dt1")   # the twenty of 29 September (before the grade ramp); X1
SHIFTS = (-57.0, -25.0, -10.0, -5.0, 0.0, +5.0, +10.0, +25.0, +57.0)


def score_set(st):
    DR.use_set(st)
    names, recs, worst = DR.load_records()
    seeds = sorted(int(n.split("seed")[1]) for n in names if n.startswith("sighted_seed"))
    res = {"n_pairs": len(seeds), "worst_reproduction": worst, "rows": {}}
    for knock in (True, False):
        for s in SHIFTS:
            c = dict(DR.PUBLISHED, knee=DR.PUBLISHED["knee"] + s)
            if not knock:
                c["w_knock"] = 0.0
            med = {n: float(np.median(DR.damage(recs[n], c))) for n in names}
            cut = {n: 100.0 * (1.0 - med[n] / med["baseline_ECU"]) for n in names}
            diff = np.array([cut[f"sighted_seed{k}"] - cut[f"blind_seed{k}"] for k in seeds])
            res["rows"][f"knock={knock} shift={s:+.0f}"] = dict(
                d_mean=float(diff.mean()), grade_cut=cut["current-grade"],
                pred_minus_grade=cut["predictive_hand"] - cut["current-grade"],
                sighted_median=float(np.median([cut[f"sighted_seed{k}"] for k in seeds])),
                blind_median=float(np.median([cut[f"blind_seed{k}"] for k in seeds])))
    return res, len(seeds), worst


def report_set(st, res, n_seeds, worst):
    print(f"== {st}: {n_seeds} pairs; published formula reproduces the committed damage to {worst:.1e}")
    for knock in (True, False):
        r0 = res["rows"][f"knock={knock} shift=+0"]["d_mean"]
        line = []
        for s in SHIFTS:
            r = res["rows"][f"knock={knock} shift={s:+.0f}"]
            slope = (r["d_mean"] - r0) / s if s else float("nan")
            line.append(f"{s:+.0f} K: d {r['d_mean']:+.2f} (slope {slope:+.4f} /K)")
        print(f"  knock term {'on ' if knock else 'off'}: " + "; ".join(line))
    for knock in (True, False):
        sl = [abs((res["rows"][f"knock={knock} shift={s:+.0f}"]["d_mean"] - res["rows"][f"knock={knock} shift=+0"]["d_mean"]) / s)
              for s in SHIFTS if s]
        print(f"  knock {'on' if knock else 'off'}: largest |slope| over the shifts {max(sl):.4f} points per K; "
              f"at +-10 K: {abs((res['rows'][f'knock={knock} shift=+10']['d_mean'] - res['rows'][f'knock={knock} shift=+0']['d_mean'])/10):.4f}, "
              f"{abs((res['rows'][f'knock={knock} shift=-10']['d_mean'] - res['rows'][f'knock={knock} shift=+0']['d_mean'])/10):.4f}")


def run():
    for st in SETS:
        probe = os.path.join(common.REPO, "results", "agents", st, "baseline_ECU", "eval_record.npz")
        if not os.path.isfile(probe):
            raise SystemExit(f"knee_shift: {common.rel(probe)} is not on this machine (the per-step records are "
                             "gitignored and stay on the training machine); run this step there, or rebuild the two "
                             "contract files from the saved outputs with --build-only")
    out = {}
    for st in SETS:
        res, n_seeds, worst = score_set(st)
        out[st] = res
        report_set(st, res, n_seeds, worst)
    common.write_json(OUT, out)
    return out

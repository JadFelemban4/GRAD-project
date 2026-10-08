"""analyse_x1.py -- X1's preregistered test, and nothing else.

    python analyse_x1.py                      X1: results/agents/extremes_dt1 -> results/X1_RESULT.txt
    python analyse_x1.py --set terrain_dt1    the same rule on the twenty of 29 September: a dry run
                                              of this script, never X1's result

Written 8 October 2026 with results/PREREGISTRATION_X1.md, BEFORE any X1 agent
trained, so the statistic is fixed before there is anything for it to read. It
reads committed result files only: results/agents/<set>/index.json and each
policy's eval_summary.json (record_agents.py writes both).

THE RULE (PREREGISTRATION_X1.md section 5), Phase D2's three cells with the
minimum effect of interest restated in points of damage cut:

    per agent    cut = 100 (1 - median damage / the baseline ECU's median
                 damage) over the twenty frozen episodes (evaluate.EPISODES)
    per seed     d = cut(sighted) - cut(blinded), points
    PREVIEW HELPS            exact one-sided sign test of d > 0, p < 0.05
    SMALLER THAN THE MEI     otherwise, if the sign test of MEI - d > 0 has p < 0.05
    INCONCLUSIVE             neither

and, as in C4 (PREREGISTRATION_C4.md 2a): if the one-sided sign test of d < 0
has p < 0.05 the reading is PREVIEW COSTS DAMAGE, whatever the cell -- the
classification would otherwise file it under SMALLER THAN THE MEI.

The MEI is 5.43 points: the 50 damage units the team set on 22 September were
5.43 % of the baseline's damage on the merged plant, and decision 5 of
results/VALIDATION_DECISIONS.md restates it as a share, so that it survives a
plant change. The exact permutation test is reported beside the sign test as
the sensitivity reading; when the two disagree that is printed, and the sign
test stays primary. Both tests are IMPORTED from analyse_phase_d, not copied.
The same rule is applied to the thermal-only cut (no knock term), the second
reading the team agreed on 30 September until drive C tests the knock model.

ALSO PRINTED, and none of it is a test of preview:
    supervision     each agent's median cut against current-grade's, in points
    worst episode   agents whose worst frozen episode does more damage than the
                    baseline ECU on that same episode (decision sheet, input to 7)
    yardstick       current-grade's steps under 95 % of the requested torque
                    (decision 13), from its own committed summary
"""
import argparse
import json
import os
import statistics

from analyse_phase_d import ALPHA, perm_test, sign_test

HERE = os.path.dirname(os.path.abspath(__file__))
MEI_PTS = 5.43
PREREGISTERED_SEEDS = 23


def classify(diffs, mei=MEI_PTS):
    """The three cells. Returns (cell, detail)."""
    k, n, p_sign = sign_test(diffs)
    p_perm = perm_test(diffs)
    shifted = [mei - d for d in diffs]
    k_lt, n_lt, p_lt_sign = sign_test(shifted)
    p_lt_perm = perm_test(shifted)
    k_neg, n_neg, p_neg = sign_test([-d for d in diffs])
    detail = dict(k=k, n=n, p_sign=p_sign, p_perm=p_perm, k_lt=k_lt, n_lt=n_lt,
                  p_lt_sign=p_lt_sign, p_lt_perm=p_lt_perm, mean=sum(diffs) / len(diffs),
                  k_neg=k_neg, p_neg=p_neg)
    if p_neg < ALPHA:
        return "PREVIEW COSTS DAMAGE", detail
    if p_sign < ALPHA:
        return "PREVIEW HELPS", detail
    if p_lt_sign < ALPHA:
        return "SMALLER THAN THE MEI", detail
    return "INCONCLUSIVE", detail


def _summary(set_name, folder):
    with open(os.path.join(HERE, "results", "agents", set_name, folder, "eval_summary.json"),
              encoding="utf-8") as fh:
        return json.load(fh)


def report(set_name):
    with open(os.path.join(HERE, "results", "agents", set_name, "index.json"), encoding="utf-8") as fh:
        idx = json.load(fh)
    pairs = idx["ablation"]["pairs"]
    out = []
    p = out.append
    p(f"X1 ANALYSIS -- {set_name}" + ("" if set_name == "extremes_dt1"
                                       else "   (DRY RUN of the rule, NOT X1's result)"))
    p(f"rule: results/PREREGISTRATION_X1.md section 5; MEI {MEI_PTS} points of cut; alpha {ALPHA}, one-sided")
    if set_name == "extremes_dt1" and len(pairs) != PREREGISTERED_SEEDS:
        p(f"!! {len(pairs)} pairs, the preregistration fixed {PREREGISTERED_SEEDS}: say so beside every figure")
    p("")
    for label, a, b in (("TOTAL DAMAGE (primary)", "sighted", "blinded"),
                        ("THERMAL-ONLY DAMAGE (no knock term; the second reading)",
                         "sighted_thermal", "blinded_thermal")):
        d = [r[a] - r[b] for r in pairs]
        cell, x = classify(d)
        p(label)
        p("  seed   sighted cut   blinded cut   difference")
        for r, di in zip(pairs, d):
            p(f"  {r['seed']:>4}   {r[a]:>11.2f}   {r[b]:>11.2f}   {di:>+10.2f}")
        sd = (sum((v - x['mean']) ** 2 for v in d) / (len(d) - 1)) ** 0.5 if len(d) > 1 else float("nan")
        p(f"  n {x['n']} (non-zero)   positive {x['k']}   mean {x['mean']:+.2f}   sd {sd:.2f} points")
        p(f"  preview helps:        sign p {x['p_sign']:.4f}   permutation p {x['p_perm']:.4f}")
        p(f"  smaller than the MEI: sign p {x['p_lt_sign']:.4f} ({x['k_lt']} of {x['n_lt']} below "
          f"{MEI_PTS})   permutation p {x['p_lt_perm']:.4f}")
        p(f"  preview costs damage: sign p {x['p_neg']:.4f} ({x['k_neg']} of {x['n']} negative)")
        if (x["p_sign"] < ALPHA) != (x["p_perm"] < ALPHA) or (x["p_lt_sign"] < ALPHA) != (x["p_lt_perm"] < ALPHA):
            p("  THE SIGN AND PERMUTATION TESTS DISAGREE. Both are reported; the sign test is primary.")
        p(f"  CELL: {cell}")
        p("")

    pol = idx["policies"]
    grade = pol["current-grade"]["cut_pct"]
    agents = {k: v for k, v in pol.items() if "_seed" in k}
    beat = [k for k, v in agents.items() if v["cut_pct"] > grade]
    p("SUPERVISION, A DIFFERENT CLAIM (never evidence for preview)")
    p(f"  current-grade cuts {grade:.2f} %; {len(beat)} of {len(agents)} agents beat it on the median")
    for arm in ("sighted", "blind"):
        m = sorted(v["cut_pct"] - grade for k, v in agents.items() if k.startswith(arm))
        if m:
            p(f"  {arm:8s} margin over current-grade, median {statistics.median(m):+.2f} points "
              f"(range {m[0]:+.2f} to {m[-1]:+.2f})")

    base = _summary(set_name, "baseline_ECU")["episodes"]
    worse = []
    for k in agents:
        eps = _summary(set_name, k)["episodes"]
        n_bad = sum(e["damage"] > b["damage"] for e, b in zip(eps, base))
        if n_bad:
            worse.append(f"{k} ({n_bad})")
    p(f"  agents doing MORE damage than the baseline ECU on at least one frozen episode: "
      f"{len(worse)} of {len(agents)}" + (f": {', '.join(worse)}" if worse else ""))

    cg = _summary(set_name, "current-grade")
    short = cg.get("yardstick", {}).get("short_steps")
    p("YARDSTICK (decision 13): current-grade's steps under 95 % of the requested torque: "
      + (f"{short}" if short is not None else "not in its summary -- see PREREGISTRATION_X1.md 4a"))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="extremes_dt1")
    a = ap.parse_args()
    text = report(a.set)
    print(text)
    if a.set == "extremes_dt1":
        with open(os.path.join(HERE, "results", "X1_RESULT.txt"), "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print("\nwrote results/X1_RESULT.txt")


if __name__ == "__main__":
    main()

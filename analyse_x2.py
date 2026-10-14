"""analyse_x2.py -- X2's preregistered test, and nothing else.

    python analyse_x2.py                                  X2: results/agents/wideair_dt1 -> results/X2_RESULT.txt
    python analyse_x2.py --set extremes_dt1 --seeds 0-4   the dry run: the rule on X1's first five pairs,
                                                          never X2's result

Written 11 October 2026 with results/PREREGISTRATION_X2.md, BEFORE any X2 agent
trained. X2's rule is X1's, IMPORTED and not copied (analyse_x1.report, whose
tests come from analyse_phase_d): per agent the cut against the baseline ECU
over the twenty frozen episodes, per seed d = cut(sighted) - cut(blinded), the
MEI 5.43 points, the exact one-sided sign test primary and the permutation test
beside it, PREVIEW COSTS DAMAGE first, both damage readings.

FIVE PAIRS, SAID BEFORE THE RESULT (PREREGISTRATION_X2.md section 5). The
smallest p the one-sided sign test can return on five pairs is 1/32 = 0.031,
so every cell except INCONCLUSIVE needs ALL FIVE pairs on one side. At X1's
spread (sd 24.78 points) the power against the MEI is 0.07; at the spread of
29 September (7.84) it is 0.25; 80 % needs an sd near 3 points. X2 is also a
measurement of that spread after 1200 episodes, which sizes the next test
(power_analysis.py), and of whether the agents had settled
(check_x2_convergence.py). The script prints both facts beside the cell.
"""
import argparse
import json
import os

import power_analysis as PA
from analyse_x1 import MEI_PTS, report

HERE = os.path.dirname(os.path.abspath(__file__))
OWN_SET = "wideair_dt1"
PREREGISTERED_SEEDS = 5


def seeds(spec):
    lo, _, hi = spec.partition("-")
    return list(range(int(lo), int(hi) + 1)) if hi else [int(s) for s in spec.split(",")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default=OWN_SET)
    ap.add_argument("--seeds", default=None, help="'0-4' or '0,2,4': a subset, for a dry run")
    a = ap.parse_args()
    text, res = report(a.set, name="X2", own_set=OWN_SET, n_fixed=PREREGISTERED_SEEDS,
                       prereg="PREREGISTRATION_X2.md", seeds=seeds(a.seeds) if a.seeds else None)
    n = res["n_pairs"]
    sd = res["readings"]["total"]["sd"]
    lines = [text, "",
             f"FIVE PAIRS (PREREGISTRATION_X2.md 5a-5b): the smallest one-sided sign p on {n} pairs is "
             f"{0.5 ** n:.4f}; a cell other than INCONCLUSIVE needs all {n} pairs on one side.",
             f"  power against the MEI ({MEI_PTS} points) at this experiment's own spread (sd {sd:.2f}): "
             f"{PA.power(MEI_PTS, sd, n):.3f}",
             "  the seeds this spread would need for 80 % power against the MEI: "
             + next((str(k) for k in range(n, 401) if PA.power(MEI_PTS, sd, k) >= 0.8), "more than 400")]
    text = "\n".join(lines)
    res["power_at_own_spread"] = round(PA.power(MEI_PTS, sd, n), 4)
    print(text)
    if a.set == OWN_SET and a.seeds is None:
        with open(os.path.join(HERE, "results", "X2_RESULT.txt"), "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        with open(os.path.join(HERE, "results", "X2_RESULT.json"), "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1)
            fh.write("\n")
        print("\nwrote results/X2_RESULT.txt and results/X2_RESULT.json")


if __name__ == "__main__":
    main()

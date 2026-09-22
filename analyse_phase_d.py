"""analyse_phase_d.py — the test that results/PREREGISTRATION.md names, and only that.

    python analyse_phase_d.py

Reads `results/phase_d_seed<N>.txt`, applies the preregistered statistic, and
prints the result. It computes nothing the preregistration did not name, and it
chooses nothing after seeing the numbers.

WHAT IT IS ALLOWED TO DO, from section 5:

    primary outcome   per-seed median damage over the twenty frozen episodes
    comparison        paired by seed, blind minus sighted; positive = preview
                      helped
    test              exact one-sided sign test on the paired differences
    sensitivity       exact paired permutation test on the same differences
    alpha             0.05, one-sided

The permutation test is REPORTED BESIDE the sign test, not instead of it, and
if the two disagree both are printed and neither is selected. That rule is in
the preregistration and is enforced here rather than left to whoever reads the
output.

WHAT IT DELIBERATELY DOES NOT DO:

  * it does not drop a seed for a poor learning curve (section 6);
  * it does not add a seed (section 7);
  * it does not switch to a two-sided test if the one-sided one fails, and it
    prints the direction plainly if the effect is negative;
  * it does not compare against the baseline ECU as though that answered the
    preview question -- the `current-grade` row is what preview must beat, and
    it is printed for every seed.
"""
import glob
import itertools
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ALPHA = 0.05

ROW = re.compile(r"^(baseline ECU|reactive|current-grade|agent \(blind\)|agent)"
                 r"\s+\S*\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s+(\d+)\s*$")


POLICIES = ("agent (blind)", "agent", "baseline ECU", "reactive",
            "current-grade")


def parse(path):
    """Damage medians out of one result file, by policy.

    SPLIT, DO NOT PATTERN-MATCH THE WHOLE LINE. `evaluate.py` writes the policy
    label with the run directory appended -- "agent (blind) runs/blind_seed0"
    -- and a path can contain digits, so a regex hunting five numbers across
    the line has to be told where the name stops. Taking the LAST five
    whitespace-separated fields as the columns needs no such instruction, and
    does not care how the path is spelled or how wide the column is.

    The five columns, as evaluate.py's header states them:
        damage med   IQR   worst   fuel med   peak C
    """
    out = {}
    for line in open(path, encoding="utf-8"):
        s = line.rstrip()
        name = next((p for p in POLICIES if s.startswith(p)), None)
        if name is None:
            continue
        parts = s.split()
        if len(parts) < 5:
            continue
        try:
            cols = [float(x) for x in parts[-5:]]
        except ValueError:
            continue
        out.setdefault(name, cols[0])          # damage med
    return out


def sign_test(diffs):
    """Exact one-sided sign test. H1: differences are positive."""
    from math import comb
    nz = [d for d in diffs if d != 0]
    n, k = len(nz), sum(1 for d in nz if d > 0)
    p = sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n if n else 1.0
    return k, n, p


def perm_test(diffs):
    """Exact one-sided paired permutation test on the mean difference."""
    obs = sum(diffs) / len(diffs)
    n = len(diffs)
    hits = 0
    for signs in itertools.product((1, -1), repeat=n):
        if sum(s * abs(d) for s, d in zip(signs, diffs)) / n >= obs:
            hits += 1
    return hits / 2 ** n


def main():
    files = sorted(glob.glob(os.path.join(HERE, "results", "phase_d_seed*.txt")),
                   key=lambda p: int(re.search(r"seed(\d+)", p).group(1)))
    if not files:
        raise SystemExit("no results/phase_d_seed*.txt -- run "
                         "`python run_phase_d.py --evaluate` first")

    print("=" * 78)
    print("PHASE D — the preregistered test")
    print("results/PREREGISTRATION.md, committed before any agent was trained")
    print("=" * 78)
    print()
    print(f"{'seed':>5}{'baseline':>11}{'curr-grade':>12}"
          f"{'sighted':>10}{'blinded':>10}{'blind-sighted':>15}")
    print("-" * 78)

    rows, diffs = [], []
    for f in files:
        seed = int(re.search(r"seed(\d+)", f).group(1))
        d = parse(f)
        need = ("baseline ECU", "current-grade", "agent", "agent (blind)")
        if not all(k in d for k in need):
            print(f"{seed:>5}   INCOMPLETE — {sorted(d)}")
            continue
        diff = d["agent (blind)"] - d["agent"]
        rows.append((seed, d, diff))
        diffs.append(diff)
        print(f"{seed:>5}{d['baseline ECU']:>11.1f}{d['current-grade']:>12.1f}"
              f"{d['agent']:>10.1f}{d['agent (blind)']:>10.1f}{diff:>+15.1f}")

    print("-" * 78)
    if len(diffs) < 2:
        raise SystemExit("too few complete seeds to test")

    k, n, p_sign = sign_test(diffs)
    p_perm = perm_test(diffs)
    mean = sum(diffs) / len(diffs)

    print()
    print(f"paired differences (blind - sighted), n = {len(diffs)}")
    print(f"  positive (preview helped) : {k} of {n}")
    print(f"  mean difference           : {mean:+.1f} damage units")
    print()
    print(f"  exact one-sided sign test        p = {p_sign:.4f}")
    print(f"  exact paired permutation test    p = {p_perm:.4f}   (sensitivity)")
    print(f"  alpha                            {ALPHA}")
    print()

    sig_sign, sig_perm = p_sign < ALPHA, p_perm < ALPHA
    if sig_sign != sig_perm:
        print("  THE TWO TESTS DISAGREE. The preregistration says both are")
        print("  reported and neither is chosen after the fact. Report both.")
    elif sig_sign:
        print(f"  RESULT: preview helps. Both tests reject at alpha {ALPHA}.")
    else:
        print(f"  RESULT: NOT SIGNIFICANT at alpha {ALPHA}.")
        # THE TRAINING BUDGET BELONGS NEXT TO A NULL, NOT IN A FOOTNOTE.
        # 50 000 steps is what train.py calls "C1: the first bad run" -- 11
        # episodes. A null from an undertrained agent and a null from a
        # converged one are different claims, and this experiment cannot tell
        # them apart. Printed here so it travels with the number.
        print("  These are C1 agents: 50 000 steps, 11 training episodes each,")
        print("  which train.py itself calls 'the first bad run'. So the claim")
        print("  is 'with agents trained to the C1 budget, preview does not")
        print("  separate from seed noise' -- NOT 'preview does not help'.")
        print("  See results/PREREGISTRATION.md limit 6.")
        # AND THE BLINDED ARM IS NOT BLIND -- the most serious limit, and a
        # design flaw rather than an execution one. The road is identical in
        # every episode and the blind agent's thermal state is a clock, so it
        # can memorise where the hill is with no preview channel at all.
        # Verified 22 September; PREREGISTRATION limit 7. Printed here so it
        # travels with the p-value instead of living in a file.
        print()
        print("  AND THE BLINDED ARM IS NOT BLIND. The road is the same hill at")
        print("  the same second in every episode, and the blind agent's thermal")
        print("  state takes a distinct value at every step -- a clock on a road")
        print("  it can memorise. So this compares an explicit preview channel")
        print("  with an implicit one, not foresight with none. Four explanations")
        print("  for the null are live and this experiment separates none of them.")
        print("  Randomise the climb per episode before reading anything into it.")
        print("  See results/PREREGISTRATION.md limits 7 and 8.")
        if mean < 0:
            print("  And the mean difference is NEGATIVE: the sighted agents")
            print("  took MORE damage than the blinded ones. Report that as")
            print("  what it is. The preregistration named this direction as")
            print("  the expected one -- five scenarios of hand-written")
            print("  policies already showed preview losing.")

    print()
    print("  Minimum effect of interest: ", end="")
    pre = os.path.join(HERE, "results", "PREREGISTRATION.md")
    txt = open(pre, encoding="utf-8").read() if os.path.exists(pre) else ""
    if "TEAM DECISION — NOT YET SET" in txt:
        print("STILL UNSET (TEAM DECISION).")
        print("  Until it is set, a null result cannot be told apart from an")
        print("  underpowered one. Set it in results/PREREGISTRATION.md.")
    else:
        print("see results/PREREGISTRATION.md section 5.")

    print()
    print("  Preview must beat CURRENT-GRADE, not the baseline ECU. Per seed:")
    for seed, d, _ in rows:
        b = d["baseline ECU"]
        edge = 100 * (1 - d["agent"] / b) - 100 * (1 - d["current-grade"] / b)
        print(f"    seed {seed}: agent over current-grade {edge:+6.1f} points")
    return 0


if __name__ == "__main__":
    sys.exit(main())

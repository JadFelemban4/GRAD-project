"""analyse_phase_d2.py — the test results/PREREGISTRATION_D2.md names, and only that.

    python analyse_phase_d2.py

Reads `results/d2_seed<N>.txt`, applies the preregistered statistic, and prints
the result -- beside Phase D's, because the preregistration requires both
experiments reported whatever either says.

WRITTEN BEFORE ANY PHASE D2 AGENT WAS TRAINED, and committed with the
preregistration. That is the point of it: the analysis is fixed while the
answer is still unknown, so nothing below can have been chosen to suit it.

THE STATISTIC IS PHASE D's, UNCHANGED (`analyse_phase_d.py`):

    primary outcome   per-seed median damage over the twenty frozen episodes
    comparison        paired by seed, blind minus sighted; positive = preview
                      helped
    test              exact one-sided sign test on the paired differences
    sensitivity       exact paired permutation test on the same differences
    alpha             0.05, one-sided

The sign-test and permutation functions are IMPORTED from `analyse_phase_d.py`
rather than copied, so the two experiments cannot quietly come to use different
arithmetic.

WHAT IS NEW, AND IT IS WHAT THE MINIMUM EFFECT OF INTEREST IS FOR
-----------------------------------------------------------------
Phase D had no minimum effect of interest, so its null had exactly one reading
available: "not significant". That sentence cannot tell "preview is worth
nothing" apart from "the experiment was too small to see it".

The team set the MEI on 22 September 2026: **50 damage units** (about 5 % of
baseline damage, four times the largest known measurement artefact). With it,
a result falls into exactly one of three cells, and the rule that assigns it is
fixed here, before the data:

  1. PREVIEW HELPS. The primary sign test rejects "no effect" at alpha 0.05.
     The effect is then reported with its size, and whether its mean reaches
     the MEI is stated -- a significant effect smaller than the MEI is real
     but, by the team's own threshold, not worth acquiring preview for.

  2. PREVIEW'S EFFECT IS SMALLER THAN THE MEI. The primary test does not
     reject, AND a one-sided test of "the effect is at least 50" DOES reject:
     the exact sign test on (difference - 50) with H1 "median below 50". This
     is a positive finding about preview, not an absence of one.

  3. INCONCLUSIVE. Neither rejects. The experiment cannot distinguish "no
     effect" from "an effect the team would care about". `power_analysis.py`
     predicted, before this experiment ran, that this is the likely cell at
     eight seeds and C1 -- which is exactly why it is named in advance rather
     than discovered.

The permutation test is run on the same shifted differences as a sensitivity
check, and a disagreement between it and the sign test is reported, never
resolved by choosing one.

WHAT IT DELIBERATELY DOES NOT DO: drop a seed, add a seed, switch tails, bin by
grade or start time (the result files hold medians over twenty episodes, not
episodes), or read "the agent beats current-grade" as "preview helps" -- that
conflation is AUDIT.md C3.
"""
import glob
import os
import re

from analyse_phase_d import ALPHA, parse, perm_test, sign_test

HERE = os.path.dirname(os.path.abspath(__file__))

# results/PREREGISTRATION_D2.md section 5. Set by the team, 22 September 2026,
# before any Phase D2 agent was trained. Do not change it after a result exists.
MEI = 50.0


def load(prefix):
    """(seed, medians, blind - sighted) for every complete result file."""
    files = sorted(glob.glob(os.path.join(HERE, "results", f"{prefix}_seed*.txt")),
                   key=lambda p: int(re.search(r"seed(\d+)", p).group(1)))
    rows, incomplete = [], []
    need = ("baseline ECU", "current-grade", "agent", "agent (blind)")
    for f in files:
        seed = int(re.search(r"seed(\d+)", f).group(1))
        d = parse(f)
        if not all(k in d for k in need):
            incomplete.append((seed, sorted(d)))
            continue
        rows.append((seed, d, d["agent (blind)"] - d["agent"]))
    return rows, incomplete


def classify(diffs):
    """The three-cell rule from the docstring. Returns (cell, detail dict)."""
    k, n, p_sign = sign_test(diffs)
    p_perm = perm_test(diffs)
    shifted = [MEI - d for d in diffs]          # positive where the effect < MEI
    k_lt, n_lt, p_lt_sign = sign_test(shifted)
    p_lt_perm = perm_test(shifted)
    detail = dict(k=k, n=n, p_sign=p_sign, p_perm=p_perm,
                  k_lt=k_lt, n_lt=n_lt, p_lt_sign=p_lt_sign, p_lt_perm=p_lt_perm,
                  mean=sum(diffs) / len(diffs))
    if p_sign < ALPHA:
        return "PREVIEW HELPS", detail
    if p_lt_sign < ALPHA:
        return "SMALLER THAN THE MEI", detail
    return "INCONCLUSIVE", detail


def report(title, rows, preregistered):
    diffs = [r[2] for r in rows]
    print(f"{'seed':>5}{'baseline':>11}{'curr-grade':>12}"
          f"{'sighted':>10}{'blinded':>10}{'blind-sighted':>15}")
    print("-" * 78)
    for seed, d, diff in rows:
        print(f"{seed:>5}{d['baseline ECU']:>11.1f}{d['current-grade']:>12.1f}"
              f"{d['agent']:>10.1f}{d['agent (blind)']:>10.1f}{diff:>+15.1f}")
    print("-" * 78)
    if len(diffs) < 2:
        print("  too few complete seeds to test")
        return None
    cell, x = classify(diffs)
    sd = (sum((d - x["mean"]) ** 2 for d in diffs) / (len(diffs) - 1)) ** 0.5
    print(f"paired differences (blind - sighted), n = {len(diffs)}")
    print(f"  positive (preview helped) : {x['k']} of {x['n']}")
    print(f"  mean difference           : {x['mean']:+.1f} damage units")
    # PREREGISTRATION_D2.md section 5a predicted INCONCLUSIVE from Phase D's
    # spread (sd 214.4). Printing this experiment's own spread is what lets
    # that prediction be checked instead of assumed.
    print(f"  sd of the differences     : {sd:.1f} damage units"
          f"   (Phase D: 214.4 -- power_analysis.py)")
    print()
    print("  H1: preview helps (difference > 0)")
    print(f"    exact one-sided sign test        p = {x['p_sign']:.4f}")
    print(f"    exact paired permutation test    p = {x['p_perm']:.4f}   (sensitivity)")
    print(f"  H1: the effect is smaller than the MEI ({MEI:.0f} units)")
    print(f"    exact one-sided sign test        p = {x['p_lt_sign']:.4f}"
          f"   ({x['k_lt']} of {x['n_lt']} seeds below {MEI:.0f})")
    print(f"    exact paired permutation test    p = {x['p_lt_perm']:.4f}   (sensitivity)")
    print(f"  alpha {ALPHA}, one-sided, both questions")
    print()
    if (x["p_sign"] < ALPHA) != (x["p_perm"] < ALPHA):
        print("  THE TWO TESTS DISAGREE on 'preview helps'. Both are reported;")
        print("  neither is chosen after the fact. The sign test is primary.")
    if (x["p_lt_sign"] < ALPHA) != (x["p_lt_perm"] < ALPHA):
        print("  THE TWO TESTS DISAGREE on 'smaller than the MEI'. Both are")
        print("  reported; neither is chosen. The sign test is primary.")
    tag = "" if preregistered else "   [MEI set AFTER this result -- see below]"
    print(f"  RESULT: {cell}{tag}")
    if cell == "PREVIEW HELPS":
        reach = "reaches" if x["mean"] >= MEI else "does NOT reach"
        print(f"  The mean effect {reach} the minimum of interest ({MEI:.0f}).")
    elif cell == "SMALLER THAN THE MEI":
        print("  Preview's effect is shown to be below the team's threshold of")
        print("  interest -- a positive finding about preview, at this budget.")
    else:
        print("  This experiment cannot tell 'no effect' from 'an effect the team")
        print("  would care about'. It is a statement about the experiment's")
        print("  size, not a statement that preview does nothing.")
        # Only D2 may say this. power_analysis.py was written on 22 September,
        # AFTER Phase D's result -- saying it "predicted" Phase D would be a
        # prediction made with the answer in hand.
        if preregistered:
            print("  power_analysis.py predicted this cell BEFORE this experiment")
            print("  ran, from Phase D's measured spread.")
        else:
            print("  power_analysis.py explains it -- but was written after this")
            print("  result, so it is an explanation, not a prediction.")
    return cell


def main():
    d2_rows, d2_bad = load("d2")
    pd_rows, _ = load("phase_d")

    print("=" * 78)
    print("PHASE D2 -- the preregistered test, randomised climb")
    print("results/PREREGISTRATION_D2.md, committed before any D2 agent was trained")
    print("=" * 78)
    print()
    if not d2_rows:
        print("  no complete results/d2_seed*.txt yet -- run")
        print("  `python run_phase_d.py --road random --evaluate` first")
        for seed, got in d2_bad:
            print(f"  seed {seed}: INCOMPLETE -- {got}")
        d2_cell = None
    else:
        for seed, got in d2_bad:
            print(f"  seed {seed}: INCOMPLETE -- {got}")
        d2_cell = report("Phase D2", d2_rows, preregistered=True)

    print()
    print("=" * 78)
    print("PHASE D, REPORTED BESIDE IT -- the preregistration requires both")
    print("=" * 78)
    print()
    if pd_rows:
        pd_cell = report("Phase D", pd_rows, preregistered=False)
        print()
        print("  Phase D's primary test is unaffected: its verdict was 'not")
        print("  significant' and still is. The MEI was set on 22 September,")
        print("  AFTER Phase D's result was known, so Phase D's classification")
        print("  under the MEI rule is a POST-HOC reading and is labelled so.")
        print("  results/PREREGISTRATION.md section 5 records the ordering.")
    else:
        pd_cell = None
        print("  no results/phase_d_seed*.txt")

    print()
    print("=" * 78)
    print("THE TWO EXPERIMENTS, ONE LINE EACH")
    print("=" * 78)
    print(f"  Phase D   fixed climb       blinded arm NOT blind (limit 7)   "
          f"{pd_cell or '--'}")
    print(f"  Phase D2  randomised climb  blinded arm blind (checked, B)    "
          f"{d2_cell or 'not run yet'}")
    print("  (B = check_random_road.py part B: before its climb arrives, the")
    print("  blind agent's observations are identical on every road.)")
    print()
    print("  Both are C1 agents -- 50 000 steps, 11 training episodes each,")
    print("  which train.py calls 'the first bad run'. A null from either says")
    print("  'with agents trained to the C1 budget', never 'preview does not")
    print("  help'. The next suspect after the design flaw is the budget (C4).")
    print()
    if d2_rows:
        print("  Preview must beat CURRENT-GRADE, not the baseline ECU. Per D2 seed:")
        for seed, d, _ in d2_rows:
            b = d["baseline ECU"]
            edge = 100 * (1 - d["agent"] / b) - 100 * (1 - d["current-grade"] / b)
            print(f"    seed {seed}: agent over current-grade {edge:+6.1f} points")
        print("  That is learned SUPERVISION, a separate claim from preview")
        print("  (AUDIT.md C3). Do not read one as evidence for the other.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""power_analysis.py — what effect size this design can actually detect.

    python power_analysis.py

WHY THIS EXISTS
---------------
`results/PREREGISTRATION.md` section 5 carries one unfilled line:

    Minimum effect of interest:  TEAM DECISION -- NOT YET SET.

It has blocked the write-up since 21 September, and the reason it matters is
stated there: **without it a null result cannot be told apart from an
underpowered one.** An examiner asks "how large an effect could you have
seen?" and "we did not say" is not an answer.

This script answers it with arithmetic rather than opinion. It takes the
spread Phase D actually measured, and reports, for the preregistered test:

  * the exact one-sided sign-test thresholds at eight seeds;
  * the power to detect an effect of a given size;
  * the effect size that reaches 80 % power;
  * how many seeds a chosen minimum effect would need.

NOTHING HERE IS A NEW MEASUREMENT. Every input is a figure `analyse_phase_d.py`
already prints, or a constant `evaluate.py` already reports. The arithmetic is
the contribution, and the arithmetic is uncomfortable -- which is the point of
running it before the second experiment rather than after.

THE UNCOMFORTABLE RESULT, so it is not buried in the output
-----------------------------------------------------------
Phase D's eight paired differences have a standard deviation of **214 damage
units** about a mean of **+4.8**. At that spread, eight seeds reach 80 % power
only for an effect of about **270 damage units** -- which is 28 % of baseline
damage, and comparable to the ENTIRE benefit of supervision (327 units, the
gap between the baseline ECU and `current-grade`).

**So Phase D could not have detected any plausible preview effect.** Its null
is consistent with preview being worth nothing, and equally consistent with
preview being worth 100 damage units -- an effect this project would call
large. That is what "underpowered" means, and it is a fourth reading of the
null to set beside the three in `PREREGISTRATION.md` limit 7.

Declaring it BEFORE the second experiment is what makes it a limit rather than
an excuse. It is also actionable: the table of seeds-versus-effect below says
what the second experiment would need in order to be able to answer.

WHAT THE SPREAD IS, AND WHAT IT IS NOT
--------------------------------------
The 214 is **seed-to-seed training variance**, not episode noise. Each seed's
number is already a median over the twenty frozen episodes, so averaging more
episodes does not shrink it. Running more seeds does not shrink it either --
it shrinks the uncertainty in its MEAN, which is what power needs. Training the
agents longer (`--steps 300000`, the C4 budget of `PREREGISTRATION.md`
limit 6) MIGHT shrink it, if different seeds converge to the same place -- or
might not, if they converge to different ones. That was a hypothesis, and C4
checked it (24 September 2026): at 300 000 steps the spread was 139.9 against
D2's 98.8 -- it did not shrink, and one seed sets most of it. `report_c4()`
prints the figures, and C4's agents had not converged by its own rule
(`results/PREREGISTRATION_C4.md` sections 5b and 11).

This paragraph said, until 23 September 2026, "Randomising the climb does NOT
shrink it." **Phase D2 measured the opposite: randomising the climb, and
changing nothing else, took the spread from 214.4 to 98.8.** The prediction was
written into `PREREGISTRATION_D2.md` section 5a before the run and failed, and
`report_d2()` below prints the failure. The sentence was left standing in this
docstring after the function beside it had refuted it -- mistake 11's shape --
and the same confidence was being placed in "convergence shrinks it". Neither
is known until measured.

A NOTE ON THE NORMAL APPROXIMATION
----------------------------------
The power column assumes the paired differences are normal with the given
standard deviation. Eight points cannot establish that, and Phase D's look
heavy-tailed (three seeds beyond two hundred units, five inside ninety). The
column is therefore a guide to ORDER OF MAGNITUDE, not a number to quote to
two figures. It does not flatter the design: a heavy-tailed distribution makes
the sign test's power WORSE than shown for a small effect, because the sign of
a difference is set by the small central mass rather than by the tails.
"""
from math import comb, erf, sqrt

# ---------------------------------------------------------------------------
# Inputs. Every one of these is printed by a script in this repository.
# ---------------------------------------------------------------------------

# analyse_phase_d.py, the "blind - sighted" column, seeds 0..7.
PHASE_D_DIFFS = (9.8, -5.8, 68.6, 387.2, -271.7, -288.2, 51.0, 87.1)

# evaluate.py on the locked scenario, median over the twenty frozen episodes.
BASELINE_DAMAGE = 959.8          # the production-representative ECU
CURRENT_GRADE_DAMAGE = 633.2     # the honest comparator for preview

# CLAUDE.md, "THE AGENT IS SCORED IN A DISCRETISATION IT DID NOT LEARN IN":
# the gap between two FIXED policies moves this much on the step size alone.
DT_ARTEFACT_POINTS = 1.3

# CLAUDE.md, the rolling-road sweep: every preview effect this project has
# measured with hand-written policies falls in this band.
HANDWRITTEN_PREVIEW_POINTS = (0.4, 2.3)

ALPHA = 0.05
SEEDS = 8


def ncdf(x, mu=0.0, sd=1.0):
    """Normal CDF. scipy is not a dependency of this repository."""
    return 0.5 * (1.0 + erf((x - mu) / (sd * sqrt(2.0))))


def binom_tail(k, n, p):
    """P(at least k successes of n | success probability p).

    Summed from an iteratively updated pmf rather than from comb(n, j) * p**j.
    At n = 400 the direct form builds 120-digit integers and multiplies them by
    denormal floats several hundred thousand times, which is what made the
    first version of this script hang rather than print.
    """
    if k > n:
        return 0.0
    if k <= 0:
        return 1.0
    if p <= 0.0:
        return 0.0
    if p >= 1.0:
        return 1.0
    pmf = (1.0 - p) ** n                 # j = 0
    total = 0.0
    for j in range(n + 1):
        if j >= k:
            total += pmf
        if j < n:
            pmf *= (n - j) / (j + 1.0) * p / (1.0 - p)
    return min(1.0, total)


def sign_test_p(k, n):
    """Exact one-sided sign test: P(at least k of n positive | p = 1/2)."""
    return sum(comb(n, j) for j in range(k, n + 1)) / 2.0 ** n


def min_positive(n, alpha=ALPHA):
    """Smallest number of positive seeds that clears alpha at n seeds."""
    for k in range(n, 0, -1):
        if sign_test_p(k, n) > alpha:
            return k + 1
    return 1


def power(delta, sd, n, alpha=ALPHA, k=None):
    """Power of the exact sign test against a normal shift of `delta`."""
    if k is None:
        k = min_positive(n, alpha)
    if k > n:
        return 0.0
    return binom_tail(k, n, 1.0 - ncdf(0.0, delta, sd))


def delta_for_power(target, sd, n, alpha=ALPHA):
    """Bisect for the effect size reaching `target` power. None if unreachable."""
    k = min_positive(n, alpha)
    if power(1e6, sd, n, alpha, k) < target:
        return None
    lo, hi = 0.0, 1e6
    for _ in range(60):                  # 1e6 / 2**60 -- far past any precision
        mid = 0.5 * (lo + hi)
        if power(mid, sd, n, alpha, k) < target:
            lo = mid
        else:
            hi = mid
    return hi


def seeds_for(mei, sd, target=0.80, alpha=ALPHA, cap=400):
    """Fewest seeds at which `mei` reaches `target` power. None inside `cap`.

    Searched by increasing n and testing the power of `mei` DIRECTLY, rather
    than by solving for each n's 80 %-power effect and comparing -- the latter
    nests a bisection inside the loop for no gain.
    """
    for n in range(4, cap + 1):
        if power(mei, sd, n, alpha) >= target:
            return n
    return None


def mean(xs):
    return sum(xs) / len(xs)


def stdev(xs):
    m = mean(xs)
    return sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def main():
    diffs = PHASE_D_DIFFS
    sd = stdev(diffs)
    unit = BASELINE_DAMAGE / 100.0        # one "point" of cuts-vs-baseline
    supervision = BASELINE_DAMAGE - CURRENT_GRADE_DAMAGE

    print("=" * 78)
    print("POWER ANALYSIS -- what effect size this design can detect")
    print("inputs from analyse_phase_d.py and evaluate.py; nothing re-measured")
    print("=" * 78)

    print("\nPHASE D, MEASURED")
    print(f"  paired differences (blind - sighted), n = {len(diffs)}")
    print(f"    {'  '.join(f'{d:+.1f}' for d in diffs)}")
    print(f"  mean                    {mean(diffs):+8.1f} damage units")
    print(f"  standard deviation      {sd:8.1f} damage units")
    print(f"  ratio sd / mean         {sd / abs(mean(diffs)):8.0f} x")

    print("\nTHE SCALE THE EFFECT IS MEASURED AGAINST")
    print(f"  baseline ECU damage             {BASELINE_DAMAGE:8.1f}")
    print(f"  current-grade damage            {CURRENT_GRADE_DAMAGE:8.1f}")
    print(f"  so supervision alone buys       {supervision:8.1f} damage units"
          f"  ({100 * supervision / BASELINE_DAMAGE:.1f} %)")
    print(f"  one percentage point of 'cuts vs baseline' = {unit:.2f} damage units")

    print("\nANCHORS -- effects this project has already measured, in the same units")
    lo, hi = HANDWRITTEN_PREVIEW_POINTS
    rows = [
        ("dt discretisation artefact, two FIXED policies",
         DT_ARTEFACT_POINTS * unit, f"{DT_ARTEFACT_POINTS:.1f} pts"),
        ("preview edge, hand-written policies (upper end)",
         hi * unit, f"{lo:.1f}-{hi:.1f} pts"),
        ("trained agent over current-grade (typical)",
         30.0 * unit, "+29 to +34 pts"),
        ("supervision over the baseline ECU",
         supervision, "34 pts"),
    ]
    for name, units, note in rows:
        print(f"  {name:<48}{units:8.1f}   ({note})")
    print("  ^ an effect smaller than the first row is inside a known artefact")
    print("    and must not be adopted as a minimum effect of interest.")

    print(f"\nEXACT ONE-SIDED SIGN TEST AT {SEEDS} SEEDS, alpha = {ALPHA}")
    for k in range(SEEDS, SEEDS - 4, -1):
        p = sign_test_p(k, SEEDS)
        print(f"  {k} of {SEEDS} positive -> p = {p:.4f}   "
              f"{'PASS' if p <= ALPHA else 'fail'}")
    print(f"  so the test needs {min_positive(SEEDS)} of {SEEDS} seeds to agree.")

    print(f"\nPOWER AT {SEEDS} SEEDS, against three assumptions about the spread")
    print(f"  {'effect':>8}  {'as pts':>7}   {'sd=' + f'{sd:.0f}' + ' (Phase D)':>16}"
          f"  {'sd=100':>8}  {'sd=50':>8}")
    for delta in (10, 20, 30, 50, 75, 100, 150, 200, 300, 400):
        cols = [power(delta, s, SEEDS) for s in (sd, 100.0, 50.0)]
        print(f"  {delta:>8.0f}  {delta / unit:>7.1f}   {cols[0]:>16.2f}"
              f"  {cols[1]:>8.2f}  {cols[2]:>8.2f}")

    print("\nEFFECT SIZE REACHING 80 % POWER")
    for s in (sd, 150.0, 100.0, 50.0):
        d = delta_for_power(0.80, s, SEEDS)
        tag = "  <- Phase D's measured spread" if abs(s - sd) < 1e-9 else ""
        print(f"  sd {s:6.1f}  ->  {d:7.1f} damage units "
              f"({d / unit:5.1f} pts, {100 * d / BASELINE_DAMAGE:4.1f} % of baseline){tag}")

    print("\nSEEDS NEEDED, at Phase D's measured spread, for 80 % power")
    print(f"  {'seeds':>6}  {'need k of n':>12}  {'as a fraction':>14}  "
          f"{'effect at 80 % power':>22}")
    prev_frac = None
    for n in (8, 10, 12, 16, 20, 30, 40):
        k = min_positive(n)
        d = delta_for_power(0.80, sd, n)
        cell = f"{d:.0f} units / {d / unit:.1f} pts" if d else "unreachable"
        worse = "  <- WORSE than the row above" if (
            prev_frac is not None and k / n > prev_frac) else ""
        print(f"  {n:>6}  {k:>7} of {n:<3}  {k / n:>14.3f}  {cell:>22}{worse}")
        prev_frac = k / n
    print("  MORE SEEDS IS NOT MONOTONICALLY BETTER, and the arrow is not a bug.")
    print("  The sign test is discrete: at eight seeds alpha buys one dissenter")
    print("  (7 of 8 = 0.875 of the seeds), at ten it buys one as well (9 of 10")
    print("  = 0.900), which is a STRICTER fraction -- so ten seeds detect a")
    print("  SMALLER effect less often than eight do. Twelve is the next count")
    print("  that genuinely improves on eight, and sixteen the one after.")
    print("  Choose a seed count off this column, never by rounding upward.")

    print("\nWHAT THIS MEANS FOR THE MINIMUM EFFECT OF INTEREST")
    for mei in (30.0, 50.0, 96.0):
        pw = power(mei, sd, SEEDS)
        need = seeds_for(mei, sd)
        tail = (f"80 % power needs {need} seeds per arm" if need
                else "80 % power out of reach inside 400 seeds")
        print(f"  MEI {mei:5.0f} units ({mei / unit:4.1f} pts, "
              f"{100 * mei / BASELINE_DAMAGE:4.1f} % of baseline): "
              f"power at 8 seeds {pw:.2f}; {tail}")

    report_d2(unit)
    report_c4(unit)

    print("\nTHE SENTENCE THIS SCRIPT EXISTS TO MAKE SAYABLE")
    d80 = delta_for_power(0.80, sd, SEEDS)
    print(f"  With eight seeds and the seed-to-seed spread Phase D measured,")
    print(f"  this design has 80 % power only against an effect of about")
    print(f"  {d80:.0f} damage units ({100 * d80 / BASELINE_DAMAGE:.0f} % of baseline damage).")
    print("  Any minimum effect of interest the team would actually care about")
    print("  is far below that, so the experiment is UNDERPOWERED BY DESIGN and")
    print("  its null must be reported as such. Fixing it means many more seeds,")
    print("  or the C4 budget IF convergence shrinks the spread (a hypothesis C4")
    print("  checks, not a fact) -- not more evaluation episodes, which do not")
    print("  touch seed-to-seed variance.")
    print("=" * 78)
    return 0


def report_d2(unit):
    """Phase D2's measured spread, and the prediction it checks.

    Added 23 September 2026, after D2's result. `PREREGISTRATION_D2.md`
    section 5a predicted, before the run, that the seed-to-seed spread would
    NOT shrink when the climb was randomised -- "randomising the climb is not
    expected to either". This section is where that prediction is checked, and
    it FAILED: the spread roughly halved. Read from the result files, not
    typed, so it cannot drift from what analyse_phase_d2.py tests.
    """
    try:
        from analyse_phase_d2 import load
        rows, _ = load("d2")
    except Exception:            # noqa: BLE001 -- the section is optional
        rows = []
    print("\nPHASE D2, MEASURED -- the pre-run prediction about the spread, checked")
    if len(rows) < 2:
        print("  no complete results/d2_seed*.txt yet")
        return
    diffs = [r[2] for r in rows]
    sd = stdev(diffs)
    base = sd_d = stdev(PHASE_D_DIFFS)
    print(f"  paired differences (blind - sighted), n = {len(diffs)}")
    print(f"    {'  '.join(f'{d:+.1f}' for d in diffs)}")
    print(f"  mean {mean(diffs):+.1f}   sd {sd:.1f}   (Phase D: sd {base:.1f})")
    print(f"  PREDICTED before the run: the spread would not shrink.")
    print(f"  MEASURED: it fell to {100 * sd / sd_d:.0f} % of Phase D's. The prediction was wrong.")
    print("  Why is not established. One candidate, NOT tested: Phase D's largest")
    print("  swings came from blind agents that did or did not memorise the fixed")
    print("  road, and randomising the road removed that source of variance.")
    print(f"\n  at D2's spread, against the MEI (50 units):")
    print(f"    power at 8 seeds                  {power(50.0, sd, 8):.2f}"
          f"   (Phase D's spread: {power(50.0, sd_d, 8):.2f})")
    d80 = delta_for_power(0.80, sd, 8)
    print(f"    effect with 80 % power, 8 seeds   {d80:.0f} units ({d80 / unit:.1f} pts)")
    need = seeds_for(50.0, sd)
    print(f"    seeds per arm for 80 % power      {need if need else 'over 400'}")
    print("    (these plan the NEXT experiment; they change nothing about D2's")
    print("    preregistered result, which stands as analyse_phase_d2.py prints it)")


def report_c4(unit):
    """C4's measured spread, for planning whatever comes after it.

    Added 24 September 2026, after C4's result. C4's preregistration made NO
    prediction about the spread (its section 5a), so nothing is checked here;
    this section exists so the figures the next decision rests on are printed
    by a script rather than typed into a prompt. Order of magnitude only --
    see the normal-approximation note in the module docstring.
    """
    try:
        from analyse_phase_d2 import load
        rows, _ = load("c4")
        d2_rows, _ = load("d2")
    except Exception:            # noqa: BLE001 -- the section is optional
        rows, d2_rows = [], []
    print("\nC4, MEASURED -- the spread at 300 000 steps, for planning only")
    if len(rows) < 2:
        print("  no complete results/c4_seed*.txt yet")
        return
    diffs = [r[2] for r in rows]
    sd = stdev(diffs)
    d2_sd = stdev([r[2] for r in d2_rows]) if len(d2_rows) > 1 else float("nan")
    print(f"  paired differences (blind - sighted), n = {len(diffs)}")
    print(f"    {'  '.join(f'{d:+.1f}' for d in diffs)}")
    print(f"  mean {mean(diffs):+.1f}   sd {sd:.1f}   (D2: sd {d2_sd:.1f}; "
          f"Phase D: {stdev(PHASE_D_DIFFS):.1f}) -- no direction was predicted")
    print(f"\n  at C4's spread, against the MEI (50 units):")
    print(f"    power at 8 seeds                  {power(50.0, sd, 8):.2f}")
    d80 = delta_for_power(0.80, sd, 8)
    print(f"    effect with 80 % power, 8 seeds   {d80:.0f} units ({d80 / unit:.1f} pts)")
    need = seeds_for(50.0, sd)
    print(f"    seeds per arm for 80 % power      {need if need else 'over 400'}")
    if need:
        near = "  ".join(f"{n}: {power(50.0, sd, n):.2f}"
                         for n in range(need, min(need + 5, 401)))
        print(f"    power just above it (not monotonic): {near}")
    # ONE SEED SETS THIS SPREAD, and the next experiment's size depends on
    # whether it is typical. Printed as a SENSITIVITY for planning, never as a
    # reason to drop the seed: C4's preregistration reports all eight.
    big = max(range(len(diffs)), key=lambda i: abs(diffs[i]))
    rest = [d for i, d in enumerate(diffs) if i != big]
    sd_rest = stdev(rest)
    need_rest = seeds_for(50.0, sd_rest)
    print(f"\n  SENSITIVITY, planning only: the largest |difference| is seed "
          f"{rows[big][0]} ({diffs[big]:+.1f}).")
    print(f"    without it, sd {sd_rest:.1f} and seeds per arm for 80 % power "
          f"{need_rest if need_rest else 'over 400'}")
    print("    So the seeds a follow-up needs range from that to the figure above,")
    print("    depending on whether that seed is typical -- which is what a seeds")
    print("    experiment would find out. It is NEVER a reason to drop the seed.")


if __name__ == "__main__":
    raise SystemExit(main())

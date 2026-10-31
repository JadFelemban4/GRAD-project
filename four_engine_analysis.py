"""four_engine_analysis.py -- the four-engine test's statistics (row 113), committed before scoring.

    python -B four_engine_analysis.py --scores S.json --context C.json [--out R.json] [--report R.txt]
    python -B four_engine_analysis.py --scores S.json --context C.json --sensitivity "LABEL=S_x.json" ...
    python -B four_engine_analysis.py --power        row 113 (6)'s and row 103 (4)'s power numbers, recomputed

ORDER_TO_TRAINING.md step 7 (commit C1, "training code outside the plant"), written 31 October 2026
before any agent of the four-engine test trained and before any road was drawn. It implements row 113
(1)-(6) of results/VALIDATION_DECISIONS.md section I, the confirmatory rule of row 103 (4), the
engine set of row 107 (1), (2) and (6), and the "sensitive to X" reading of row 115. Where this
docstring says DESIGN, the rows leave the choice open and this script makes it; the preregistration
(step 20) names this file's commit and copies those choices, or changes them before it is signed.

IT READS TWO JSON FILES AND NOTHING ELSE: no plant, no road record, no EPA table, no validation
record. It imports no plant module and nothing imports it (row 121). Every number it prints comes from
the two files, so a result can be recomputed from them alone.

THE SCORES, schema "four-engine-scores/1" (ORDER step 16's evaluate.py writes it; DESIGN here)

    {"schema": "four-engine-scores/1",
     "ratios": ["0.5", "1.5"],            r = H / tau (row 102); one or both, in this order
     "n_roads": 20,                        row 101's twenty roads; anything else is refused
     "variant": null,                      null for the primary scoring; a row 115 label otherwise
     "provenance": {...},                  optional, copied to the result untouched
     "engines": {
       "<engine id>": {                    an id of engines.PLANTS
         "arms": {
           "blind":        {"seeds": {"<seed>": SEED}, ...},
           "sighted_r0.5": {"seeds": {...}},          one sighted arm per declared ratio
           "sighted_r1.5": {"seeds": {...}}}}}}
    SEED = {"no_knock":   {"D": [20 numbers], "D_base": [20 numbers]},
            "with_knock": {"D": [20 numbers], "D_base": [20 numbers]}}

  <seed> is a decimal integer with no leading zero. D is the agent's damage on road k (k = 0..19,
  scored with evaluate.EPISODES[k], row 101) and D_base the baseline ECU's on the same road.
  "no_knock" is run_episode's damage_thermal (turbine and oil), "with_knock" its damage (BUILT:
  evaluate.py:291, :533-550). Refused: a schema string other than this one; a key not listed; a
  missing or extra arm; an engine whose arms do not hold the same seeds (an unpaired or missing seed,
  named); fewer than 2 seeds; a road count other than 20; a value that is not a finite number;
  D < 0 or D_base <= 0; and D_base that differs between an engine's arms or seeds on one road and
  reading by more than D_BASE_RTOL (the baseline ECU does not depend on the agent, so a different
  D_base means a different plant or road behind one score; DESIGN).

THE CONTEXT, schema "four-engine-context/1" (assembled after step 21 from the records named; DESIGN)

    {"schema": "four-engine-context/1",
     "engines_in_test": [...],             row 107 (1): the B58 and every EPA engine Run 2 does not drop
     "seeds_per_arm": 20,                  decision 30's n, as the preregistration fixes it
     "model_band": {"<id>": {"<ratio>": {"no_knock": D, "with_knock": D}}},   Delta_e in points
     "ceiling":    {"<id>": {"<ratio>": C}},  row 103 (1)'s C_e(S, r), no knock, mean form
     "status":     {"<id>": "confirmatory" | "exploratory"},                   row 103 (4)
     "status_basis": {"s_p": s, "pilot_pairs": 5, "s_star": {"<id>": s}},     row 103 (4), row 112
     "provenance": {...}}                  optional

  Delta_e is section 7's model band (MD:1569-1586), computed with the tightenings; it depends on d
  through phi and d/MEI, so it is given per ratio and reading. The status is checked against row 103
  (4)'s rule on the recorded s_p and s*, and refused when they disagree.

WHAT IS COMPUTED, numbered as row 113

  (1) d, per engine, ratio and seed: cut(sighted_r, seed) - cut(blind, seed), each cut
      100 x (1 - median D / median D_base) over the twenty roads (evaluate.py:533-538, np.median).
      Beside it, deciding nothing: the mean over the roads of each road's points,
      100 x (1 - D_k / D_base_k), in the same difference. Row 103's ceiling is in that mean form.
  (2) d > 0: decision 30's paired one-sided t-test over seeds (primary), and the exact sign test
      (analyse_phase_d.sign_test, the one X1's and X2's analyses used; zero differences dropped,
      p = 1 when none is left) as the declared secondary, each under its own run of one graphical
      procedure (Bretz, Maurer, Brannath and Posch 2009, Statistics in Medicine 28:586-604,
      Algorithm 1; adjusted p-values by Bretz et al. 2011, Biometrical Journal 53:894-913) at a
      family-wise alpha of 0.05. Row 113's graph: weight 1/4 on each engine's r = 1.5 test and 0 on
      its r = 0.5 test; edge 1 from an engine's r = 1.5 test to its own r = 0.5 test; edge 1/3 from
      an engine's r = 0.5 test to each other engine's r = 1.5 test.
        DESIGN, the row's words and Bretz's update. Row 113 says an r = 0.5 test's weight "is shared
        equally among the r = 1.5 tests not yet rejected, or, when none is left, among the r = 0.5
        tests not yet rejected". Bretz's update of the graph above does exactly that, except when an
        r = 0.5 test rejects while some r = 1.5 test is left and another engine stands with its r = 1.5
        test rejected and its r = 0.5 test not: the share meant for that engine's r = 1.5 test then goes
        on to its r = 0.5 test (test_four_engine_analysis.Graph checks the condition both ways on 3000
        SYNTHETIC orders of rejection). Read literally, the row's words then depend on the order in
        which tests that can both reject are taken: after B58 r = 1.5, Mazda r = 1.5 and B58 r = 0.5
        have rejected, the Honda's and the Ford's r = 1.5 tests and the Mazda's r = 0.5 test hold
        3/8, 3/8 and 1/4 in that order, and 1/3, 1/3 and 1/3 if B58 r = 0.5 rejected second; Bretz's
        update gives 1/3 each in both orders (test_four_engine_analysis.Graph). A rule whose weights
        depend on the order defines no closed test, so the words alone do not show family-wise error
        control. Bretz's update, which the row cites, is what runs here.
        DESIGN, engines and ratios not in the test. An engine Run 2 drops (row 107) and a ratio
        that is not scored are removed from the four-engine graph by Bretz's own update, so their
        weight passes along the row's edges. With k engines each r = 1.5 test then starts at 1/k
        (Holm across the k engines, as the row says of four), and with r = 1.5 alone the graph is
        Holm across the engines.
  (3) Equivalence, per ratio and pair i, j in the test: the 90 % Welch interval of d_i - d_j (the two
      engines' seeds are independent), widened on each side by B_ij = sqrt(Delta_i^2 + Delta_j^2),
      inside the open interval (-MEI, +MEI), MEI 5.43 points (decision 37): two one-sided tests at 5 %,
      whose p-values are printed. It counts toward a collapse only when both engines' d > 0 holds under
      (2) at that ratio (row 103 (4)); otherwise it reads "equivalent with no effect established: not
      a collapse". The collapse at a ratio is claimed only when every engine's d > 0 holds there and
      every pair is equivalent (intersection-union, no further adjustment); "one curve" needs it at
      both ratios. Fewer than two engines in the test: no collapse test (row 107 (2)).
  (4) Difference, per ratio and pair: the one-sided Welch tests of H0: d_i - d_j <= +B_ij and of
      H0: d_i - d_j >= -B_ij; p_ij = min(1, 2 x the smaller p); Holm's step-down over the pairs x
      ratios family (at most 12) at 0.05. Beside each pair: the unadjusted 95 % Welch interval, and
      the same widened by B_ij (p_ij < 0.05 exactly when the widened interval excludes 0).
  (5) Both readings, each through every procedure above on its own. The no-knock reading decides;
      the with-knock reading is printed beside every number, labelled "not converged in dt on these
      roads" (rows 101, 113 (5)), and decides nothing.
  (6) MODEL-LIMITED. A d > 0 verdict (either test) is MODEL-LIMITED when it changes with every
      engine's paired differences moved by -Delta_e, or by +Delta_e, the graph re-run each time.
      Both procedures are monotone in their p-values, so the two corners bound every point of the
      box (test_four_engine_analysis checks the monotonicity). An equivalence or difference verdict is
      MODEL-LIMITED when it differs from the same test with B_ij set to 0, the seed interval alone (the
      contract gives the pair the band sqrt(Delta_i^2 + Delta_j^2), MD:1584-1586). What that rule is,
      exactly (DESIGN; test_four_engine_analysis.Pairs pins it): the widened interval lies inside
      +-MEI exactly when the seed interval does at every shift of d_i - d_j within +-B_ij, so a verdict
      reached WITH B_ij holds across the band and is never MODEL-LIMITED; a verdict not reached with
      B_ij is MODEL-LIMITED exactly when the seed interval alone reaches it, i.e. when the band is what
      withholds it. The rule is one-sided, and that is the design: the band only ever withholds a
      verdict, it never supplies one, so a verdict not reached by either interval reads plainly (not
      reached), even when some shift within +-B_ij would reach it with the seed interval alone (the
      review of 31 October 2026, F3, gave that case: 20 seeds a side, means 4 and 0, sd 4, B 2). The
      difference test is the same rule with the band in its null. The collapse is MODEL-LIMITED when it
      changes at either corner: d > 0 at +Delta with B = 0, or at -Delta with B. (DESIGN: the box is
      joint, every engine at its own +-Delta_e at once.)
  Confirmatory or exploratory (row 103 (4); DESIGN where the row is silent): an engine's d > 0 tests
  at both ratios carry its recorded status; a pair is confirmatory only when both engines are; a
  collapse, and one curve, only when every engine in the test is; everything is exploratory when the
  B58 is alone (row 107 (2)), and every with-knock number is reported beside, never decided on.
  Wording (row 107 (6)): a pair without the Ford, and a collapse when the Ford is not in the test,
  reads "consistent with H/tau and with H alike (tau within 12 %)", never "a collapse on H/tau".
  Beside each ratio's pair verdicts the ceilings C_e of the context are printed, and when every one
  is below the MEI, row 103 (4)'s sentence (ASSUMED as the row labels it).
  Sensitivity (row 115): each --sensitivity file is a scores file of the same engines, arms and seeds
  re-scored on a perturbed plant, with its "variant" label; it is analysed with the primary context
  unchanged (no label or band moves), and every verdict that differs from the primary's is printed
  as "sensitive to <label>".

THE POWER NUMBERS (--power; MEASURED: python -B four_engine_analysis.py --power, 31 October 2026, on
the team laptop; noncentral t, one-sided, n = 20 pairs, true d = 3.20 points = 0.59 MEI, at the only
measured spreads of a paired d, 20.51 (X2) and 24.78 (X1) points, the inputs row 113 (6) names).
The false-negative risk is 0.968 and 0.975 at alpha/8, 0.944 and 0.956 at alpha/4, and 0.834 and
0.862 at alpha. Row 113 (6) prints "0.97 at Holm's first step and 0.83-0.86 at alpha": 0.83-0.86 is
reproduced; 0.97 is reproduced at X2's spread, and X1's 0.975 rounds to 0.98. The scientific
review's power.py (results/EPA_ROADS/probe_2026-10-30/review/power.py.txt) printed powers 0.032 and
0.025 at alpha/8 and 0.166 and 0.138 at alpha (its power.txt); this script's own code gives the same
to the printed digit. Its "Holm's first step" is alpha/8, plain Holm over eight tests, the option
row 113 rejected; under row 113 (2)'s graph an r = 1.5 test's first level is alpha/4 with four
engines, and the risk there is 0.944-0.956.

THE STATUS RULE'S s* IS RECOMPUTED HERE, AT THE GRAPH'S FIRST LEVEL (the review of 31 October 2026,
finding S3; DESIGN until the team's correction row of rows 103 (4) and 113 (6) says so in their words).
Row 103 (4)'s s* is "the spread that gives power 0.8 at Holm's first step at full ceiling capture with
the preregistered n, recomputed on the drawn set's ceilings". Under row 113 (2)'s graph ("Holm across
the four engines at r = 1.5") that first step is alpha/k for the k engines in the test (alpha/4 with
four; 1/k each after an engine is dropped, Bretz's removal). validate_context therefore recomputes
each engine's s* = s_star(C_e(1.5), n, alpha/k) from the context's own ceilings and seeds per arm and
refuses a recorded s* that differs from it by more than S_STAR_RTOL (relative): the level cannot
differ silently between whoever assembles the context (ORDER step 21) and this script. The context's
assembler should write status_star(...)'s values. At alpha/8 instead the planning s* would be 7.317,
4.174, 6.654 and 3.069; at alpha/4 they are 8.064, 4.600, 7.334 and 3.383 (B58, Mazda, Honda, Ford;
MEASURED, --power). The factor is the exact sqrt(4 / chi2_0.20,4) = 1.5576, printed with every status;
row 103 (4) prints it rounded, 1.56, and a status recorded with 1.56 disagrees with this one only when
1.5576 s_p <= s* < 1.56 s_p (finding S5): the correction row fixes the exact factor.
"""
import argparse
import hashlib
import itertools
import json
import math
import os
import sys
from fractions import Fraction

import numpy as np
from scipy import stats

from analyse_phase_d import sign_test

HERE = os.path.dirname(os.path.abspath(__file__))

SCORES_SCHEMA = "four-engine-scores/1"
CONTEXT_SCHEMA = "four-engine-context/1"
RESULT_SCHEMA = "four-engine-analysis/1"

MEI = 5.43                   # decision 37 (VD:194): the equivalence margin, points of cut
ALPHA = 0.05                 # row 113 (2) and (4): family-wise
ALPHA_TOST = 0.05            # row 113 (3): each one-sided test of the TOST, the 90 % interval
N_ROADS = 20                 # row 101: twenty roads, road k scored with evaluate.EPISODES[k]
RATIOS = ("0.5", "1.5")      # row 102: r = H / tau_e
READINGS = ("no_knock", "with_knock")
PRIMARY = "no_knock"         # row 113 (5)
WITH_KNOCK_LABEL = "not converged in dt on these roads"     # rows 101 and 113 (5)
# engines.PLANTS' ids and order (test_four_engine_analysis checks the two agree); the analysis
# itself builds no plant, so it does not import engines.
ENGINE_IDS = ("b58", "mazda_25t", "honda_l15b7", "ford_27tt")
B58 = "b58"                  # never dropped (row 107 (1); MD:1587-1592)
FORD = "ford_27tt"           # the only tau that separates H/tau from H (row 107 (6))
MAX_D_TESTS = 8              # row 113 (2): at most 4 x 2
MAX_PAIR_TESTS = 12          # row 113 (4): at most 6 x 2
PILOT_PAIRS = 5              # row 103 (4) and row 112: the B58 pilot's seed pairs
PILOT_BOUND = 0.80           # row 103 (4): the one-sided 80 % upper bound of a spread
# DESIGN: the baseline ECU's damage does not depend on the agent, so D_base is the same number for
# every arm and seed of one engine on one road. evaluate.py runs it deterministically; a relative
# spread above this is refused, since it would mean a different plant or road behind one score.
D_BASE_RTOL = 1e-9
TAU_NOTE = "consistent with H/tau and with H alike (tau within 12 %)"      # row 107 (6)
CEILING_SENTENCE = ("with every ceiling below the MEI, equivalence within the MEI is expected "
                    "whatever the criterion, if agents capture at most their ceilings (ASSUMED)")  # row 103 (4)
# Row 113 (6)'s printed power numbers and their inputs, typed from the row (results/VALIDATION_DECISIONS.md,
# row 113 (6); spreads results/README.md:19, :64 as row 103 (4) cites them). --power recomputes them.
ROW_113_6 = {"d_obs": 3.20, "spreads": (20.51, 24.78), "n": 20, "fn_first": 0.97, "fn_alpha": (0.83, 0.86)}
# Row 103 (4)'s planning ceilings at r = 1.5 (matched.txt, open loop, no knock) and power.py's s*
# (its power.txt), for --power's s* line only; the status rule reads the recorded s*.
PLANNING_C15 = {"b58": 5.96, "mazda_25t": 3.40, "honda_l15b7": 5.42, "ford_27tt": 2.50}
# Row 103 (4)'s s*: power 0.8 at the r = 1.5 test's first level of row 113 (2)'s graph, alpha / k with k
# engines in the test (THE STATUS RULE'S s*, in the docstring); a recorded s* is held to this to S_STAR_RTOL
S_STAR_POWER = 0.8
S_STAR_RATIO = "1.5"
S_STAR_RTOL = 1e-6


class AnalysisError(ValueError):
    """An input this script refuses. The message names the file, the place and the rule."""


def arm_name(ratio):
    return f"sighted_r{ratio}"


def node(eid, ratio):
    return f"{eid}@r{ratio}"


# ------------------------------------------------------------------------------------------ validation
def _keys(obj, where, required, optional=()):
    if not isinstance(obj, dict):
        raise AnalysisError(f"{where}: an object is required, found {type(obj).__name__}")
    missing = [k for k in required if k not in obj]
    extra = [k for k in obj if k not in required and k not in optional]
    if missing:
        raise AnalysisError(f"{where}: missing {missing}")
    if extra:
        raise AnalysisError(f"{where}: keys not in the schema {extra}")


def _number(v, where):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise AnalysisError(f"{where}: a finite number is required, found {v!r}")
    return float(v)


def _int(v, where):
    if isinstance(v, bool) or not isinstance(v, int):
        raise AnalysisError(f"{where}: an integer is required, found {v!r}")
    return v


def _ratios(v, where):
    if not isinstance(v, list) or not v or len(set(v)) != len(v) or any(r not in RATIOS for r in v):
        raise AnalysisError(f"{where}: one or both of {list(RATIOS)} required, found {v!r}")
    if v != [r for r in RATIOS if r in v]:
        raise AnalysisError(f"{where}: ratios in the order {list(RATIOS)}, found {v!r}")
    return tuple(v)


def _seed_key(k, where):
    if not isinstance(k, str) or not k.isdigit() or str(int(k)) != k:
        raise AnalysisError(f"{where}: a seed is a decimal integer with no leading zero, found {k!r}")
    return int(k)


def validate_scores(doc, where="scores"):
    """Check a "four-engine-scores/1" document; return {eid: {"seeds": [...], "arms": {...}}} with
    each arm's seed entries as float arrays, plus the ratios. Raises AnalysisError."""
    _keys(doc, where, ("schema", "ratios", "n_roads", "engines"), ("variant", "provenance"))
    if doc["schema"] != SCORES_SCHEMA:
        raise AnalysisError(f"{where}: schema {doc['schema']!r}, this script reads {SCORES_SCHEMA!r}")
    ratios = _ratios(doc["ratios"], f"{where}.ratios")
    if _int(doc["n_roads"], f"{where}.n_roads") != N_ROADS:
        raise AnalysisError(f"{where}.n_roads: {doc['n_roads']}, row 101 fixes {N_ROADS} roads")
    variant = doc.get("variant")
    if variant is not None and (not isinstance(variant, str) or not variant.strip()):
        raise AnalysisError(f"{where}.variant: null or a non-empty label, found {variant!r}")
    if not isinstance(doc["engines"], dict) or not doc["engines"]:
        raise AnalysisError(f"{where}.engines: at least one engine is required")
    arms_needed = ("blind",) + tuple(arm_name(r) for r in ratios)
    out = {}
    for eid, e in doc["engines"].items():
        we = f"{where}.engines.{eid}"
        if eid not in ENGINE_IDS:
            raise AnalysisError(f"{we}: not an engine id of engines.PLANTS {list(ENGINE_IDS)}")
        _keys(e, we, ("arms",))
        _keys(e["arms"], f"{we}.arms", arms_needed)
        seed_sets = {}
        arms = {}
        for arm in arms_needed:
            wa = f"{we}.arms.{arm}"
            _keys(e["arms"][arm], wa, ("seeds",))
            seeds = e["arms"][arm]["seeds"]
            if not isinstance(seeds, dict):
                raise AnalysisError(f"{wa}.seeds: an object of seeds is required")
            parsed = {}
            for k, entry in seeds.items():
                s = _seed_key(k, f"{wa}.seeds")
                ws = f"{wa}.seeds.{k}"
                _keys(entry, ws, READINGS)
                rd = {}
                for reading in READINGS:
                    wr = f"{ws}.{reading}"
                    _keys(entry[reading], wr, ("D", "D_base"))
                    vals = {}
                    for key in ("D", "D_base"):
                        lst = entry[reading][key]
                        if not isinstance(lst, list) or len(lst) != N_ROADS:
                            n = len(lst) if isinstance(lst, list) else type(lst).__name__
                            raise AnalysisError(f"{wr}.{key}: {N_ROADS} roads required, found {n}")
                        arr = np.array([_number(v, f"{wr}.{key}[{i}]") for i, v in enumerate(lst)])
                        vals[key] = arr
                    if np.any(vals["D"] < 0):
                        raise AnalysisError(f"{wr}.D: a damage below 0")
                    if np.any(vals["D_base"] <= 0):
                        raise AnalysisError(f"{wr}.D_base: a baseline damage at or below 0")
                    rd[reading] = vals
                parsed[s] = rd
            seed_sets[arm] = set(parsed)
            arms[arm] = parsed
        union = set().union(*seed_sets.values())
        unpaired = {arm: sorted(union - ss) for arm, ss in seed_sets.items() if union - ss}
        if unpaired:
            raise AnalysisError(f"{we}: unpaired seeds, missing from an arm (arm: seeds) {unpaired}")
        if len(union) < 2:
            raise AnalysisError(f"{we}: {len(union)} seed(s); a t-test over seeds needs at least 2")
        for reading in READINGS:
            base = np.array([arms[arm][s][reading]["D_base"] for arm in arms_needed for s in sorted(union)])
            spread = np.max(np.abs(base - base[0]) / base[0])
            if spread > D_BASE_RTOL:
                raise AnalysisError(f"{we}: D_base ({reading}) differs between arms or seeds by a relative "
                                    f"{spread:.3g} (> {D_BASE_RTOL:g}); the baseline ECU does not depend on "
                                    "the agent, so one score ran on another plant or road")
        out[eid] = {"seeds": sorted(union), "arms": arms}
    return {"ratios": ratios, "variant": variant, "engines": out}


def pilot_factor(pairs=PILOT_PAIRS, bound=PILOT_BOUND):
    """Row 103 (4): the one-sided `bound` upper bound of a spread from `pairs` pairs is
    s_p x sqrt((pairs - 1) / chi2_{1 - bound, pairs - 1}); 1.56 at 5 pairs and 80 %."""
    return math.sqrt((pairs - 1) / stats.chi2.ppf(1.0 - bound, pairs - 1))


def s_star_level(k):
    """The level row 103 (4)'s s* is taken at: the first level of an r = 1.5 test in row 113 (2)'s graph
    with k engines in the test, alpha / k (THE STATUS RULE'S s*, in the docstring)."""
    return ALPHA / int(k)


def status_star(ceiling_15, n):
    """{engine: s*} as validate_context requires them, for the context's assembler (ORDER step 21):
    s_star(C_e(1.5), n, alpha / k) with `ceiling_15` = {engine: C_e(1.5)} over the k engines in the test."""
    lvl = s_star_level(len(ceiling_15))
    # DESIGN: a ceiling at or below 0 gives no spread power 0.8 (the power stays at or under the level),
    # so its s* is 0 and the rule reads exploratory for any s_p above 0
    return {e: (s_star(float(c), int(n), lvl, power=S_STAR_POWER) if float(c) > 0.0 else 0.0)
            for e, c in ceiling_15.items()}


def validate_context(ctx, sc, where="context"):
    """Check a "four-engine-context/1" document against the validated scores `sc`."""
    _keys(ctx, where, ("schema", "engines_in_test", "seeds_per_arm", "model_band", "ceiling", "status",
                       "status_basis"), ("provenance",))
    if ctx["schema"] != CONTEXT_SCHEMA:
        raise AnalysisError(f"{where}: schema {ctx['schema']!r}, this script reads {CONTEXT_SCHEMA!r}")
    eit = ctx["engines_in_test"]
    if not isinstance(eit, list) or len(set(eit)) != len(eit) or any(e not in ENGINE_IDS for e in eit):
        raise AnalysisError(f"{where}.engines_in_test: distinct ids of {list(ENGINE_IDS)}, found {eit!r}")
    if B58 not in eit:
        raise AnalysisError(f"{where}.engines_in_test: the B58 is never dropped (row 107 (1))")
    engines = tuple(e for e in ENGINE_IDS if e in eit)
    absent = [e for e in engines if e not in sc["engines"]]
    if absent:
        raise AnalysisError(f"{where}.engines_in_test: {absent} in the test but not in the scores")
    n = _int(ctx["seeds_per_arm"], f"{where}.seeds_per_arm")
    for e in engines:
        if len(sc["engines"][e]["seeds"]) != n:
            raise AnalysisError(f"scores.engines.{e}: {len(sc['engines'][e]['seeds'])} seeds per arm, the "
                                f"context fixes {n} (decision 30: no seed added, none missing)")
    ratios = sc["ratios"]
    band, ceiling = {}, {}
    _keys(ctx["model_band"], f"{where}.model_band", engines)
    _keys(ctx["ceiling"], f"{where}.ceiling", engines)
    for e in engines:
        _keys(ctx["model_band"][e], f"{where}.model_band.{e}", ratios)
        _keys(ctx["ceiling"][e], f"{where}.ceiling.{e}", ratios)
        for r in ratios:
            wb = f"{where}.model_band.{e}.{r}"
            _keys(ctx["model_band"][e][r], wb, READINGS)
            for reading in READINGS:
                v = _number(ctx["model_band"][e][r][reading], f"{wb}.{reading}")
                if v < 0:
                    raise AnalysisError(f"{wb}.{reading}: a model band is at least 0, found {v}")
                band[(e, r, reading)] = v
            ceiling[(e, r)] = _number(ctx["ceiling"][e][r], f"{where}.ceiling.{e}.{r}")
    _keys(ctx["status"], f"{where}.status", engines)
    sb = ctx["status_basis"]
    _keys(sb, f"{where}.status_basis", ("s_p", "pilot_pairs", "s_star"))
    s_p = _number(sb["s_p"], f"{where}.status_basis.s_p")
    if _int(sb["pilot_pairs"], f"{where}.status_basis.pilot_pairs") != PILOT_PAIRS:
        raise AnalysisError(f"{where}.status_basis.pilot_pairs: row 103 (4)'s factor is for {PILOT_PAIRS} "
                            f"pairs, found {sb['pilot_pairs']}")
    _keys(sb["s_star"], f"{where}.status_basis.s_star", engines)
    if S_STAR_RATIO not in ratios:
        raise AnalysisError(f"{where}: row 103 (4)'s s* is taken at r = {S_STAR_RATIO}, which the scores do not "
                            f"hold ({ratios})")
    bound = pilot_factor() * s_p
    level = s_star_level(len(engines))
    want = status_star({e: ceiling[(e, S_STAR_RATIO)] for e in engines}, n)
    status = {}
    for e in engines:
        st = ctx["status"][e]
        if st not in ("confirmatory", "exploratory"):
            raise AnalysisError(f"{where}.status.{e}: 'confirmatory' or 'exploratory', found {st!r}")
        s_star_e = _number(sb["s_star"][e], f"{where}.status_basis.s_star.{e}")
        if abs(s_star_e - want[e]) > S_STAR_RTOL * want[e]:
            raise AnalysisError(f"{where}.status_basis.s_star.{e}: recorded {s_star_e!r}, but row 103 (4)'s s* "
                                f"at the graph's first level alpha/{len(engines)} = {level:g}, power "
                                f"{S_STAR_POWER:g}, n {n} and the context's ceiling C(1.5) "
                                f"{ceiling[(e, S_STAR_RATIO)]:g} is {want[e]:.6f} (status_star)")
        rule = "confirmatory" if bound <= s_star_e else "exploratory"
        if st != rule:
            raise AnalysisError(f"{where}.status.{e}: recorded {st!r}, but row 103 (4)'s rule gives {rule!r} "
                                f"({pilot_factor():.4f} x s_p {s_p:g} = {bound:.4f} against s* {s_star_e:g}; "
                                "the exact factor sqrt(4/chi2_0.20,4), which the row prints rounded as 1.56)")
        status[e] = {"status": st, "s_star": s_star_e}
    return {"engines": engines, "n": n, "band": band, "ceiling": ceiling, "status": status,
            "s_p": s_p, "bound": bound, "s_star_level": level}


# ------------------------------------------------------------------------------------------ (1) d
def cut(D, D_base):
    """evaluate.py's form (evaluate.py:533-538): 100 x (1 - median D / median D_base) over the roads."""
    return 100.0 * (1.0 - float(np.median(D)) / float(np.median(D_base)))


def road_mean_points(D, D_base):
    """The mean over the roads of each road's points, 100 x (1 - D_k / D_base_k): row 103's form."""
    return float(np.mean(100.0 * (1.0 - np.asarray(D, float) / np.asarray(D_base, float))))


def paired_d(eng, ratio, reading):
    """Per seed, in seed order: (d in evaluate.py's form, d in the road-mean form, sighted cut, blind cut)."""
    out = []
    for s in eng["seeds"]:
        sig = eng["arms"][arm_name(ratio)][s][reading]
        bl = eng["arms"]["blind"][s][reading]
        cs, cb = cut(sig["D"], sig["D_base"]), cut(bl["D"], bl["D_base"])
        ms, mb = road_mean_points(sig["D"], sig["D_base"]), road_mean_points(bl["D"], bl["D_base"])
        out.append((cs - cb, ms - mb, cs, cb))
    return out


# ------------------------------------------------------------------------------------------ (2) the tests
def t_greater(x):
    """Decision 30's paired one-sided t-test of d > 0 over seeds: t = mean / (sd / sqrt(n)), df n - 1.
    DESIGN: with every difference equal (sd 0), p is 0 when they are positive and 1 otherwise."""
    x = np.asarray(x, float)
    n = len(x)
    m, sd = float(x.mean()), float(x.std(ddof=1))
    if sd == 0.0:
        return {"n": n, "mean": m, "sd": 0.0, "t": None, "df": n - 1, "p": 0.0 if m > 0 else 1.0}
    t = m / (sd / math.sqrt(n))
    return {"n": n, "mean": m, "sd": sd, "t": t, "df": n - 1, "p": float(stats.t.sf(t, n - 1))}


def sign_greater(x):
    k, n, p = sign_test(list(map(float, x)))
    return {"positive": k, "nonzero": n, "zero": len(x) - n, "p": p}


def welch(x, y):
    """Welch's difference of means, from first principles: (diff, se, Welch-Satterthwaite df).
    DESIGN: with both spreads 0 the df is taken as n_x + n_y - 2 (se is 0, every interval a point)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    nx, ny = len(x), len(y)
    vx, vy = float(x.var(ddof=1)) / nx, float(y.var(ddof=1)) / ny
    diff = float(x.mean() - y.mean())
    se = math.sqrt(vx + vy)
    if vx + vy == 0.0:
        return diff, 0.0, float(nx + ny - 2)
    df = (vx + vy) ** 2 / (vx ** 2 / (nx - 1) + vy ** 2 / (ny - 1))
    return diff, se, df


def _sf(num, se, df):
    """P(T > num / se) for T ~ t(df); a step when se is 0 (DESIGN, as in t_greater)."""
    if se == 0.0:
        return 0.0 if num > 0 else (1.0 if num < 0 else 0.5)
    return float(stats.t.sf(num / se, df))


def equivalence(x, y, band, margin=MEI, alpha=ALPHA_TOST):
    """Row 113 (3): the (1 - 2 alpha) Welch interval of mean(x) - mean(y), widened by `band` on each
    side, inside (-margin, +margin); the two one-sided p-values of the same TOST beside it."""
    diff, se, df = welch(x, y)
    q = float(stats.t.ppf(1.0 - alpha, df))
    lo, hi = diff - q * se, diff + q * se
    p_lower = _sf(diff + margin - band, se, df)            # H0: diff <= -(margin - band)
    p_upper = _sf(margin - band - diff, se, df)            # H0: diff >= +(margin - band)
    return {"diff": diff, "se": se, "df": df, "ci90": [lo, hi], "band": band,
            "ci90_widened": [lo - band, hi + band], "p_lower": p_lower, "p_upper": p_upper,
            "equivalent": bool(lo - band > -margin and hi + band < margin)}


def difference(x, y, band):
    """Row 113 (4): the one-sided Welch tests of H0: diff <= +band and H0: diff >= -band; p twice the
    smaller, capped at 1; the unadjusted 95 % interval and the same widened by `band`."""
    diff, se, df = welch(x, y)
    p_up = _sf(diff - band, se, df)
    p_dn = _sf(-band - diff, se, df)
    q = float(stats.t.ppf(0.975, df))
    lo, hi = diff - q * se, diff + q * se
    return {"diff": diff, "se": se, "df": df, "band": band, "p_up": p_up, "p_down": p_dn,
            "p": min(1.0, 2.0 * min(p_up, p_dn)), "ci95": [lo, hi], "ci95_widened": [lo - band, hi + band]}


def holm(p, alpha=ALPHA):
    """Holm's step-down: {name: (adjusted p, rejected)}. Ties are broken by name, which moves no verdict."""
    order = sorted(p, key=lambda k: (p[k], k))
    m = len(order)
    out, running = {}, 0.0
    for i, k in enumerate(order):
        running = max(running, min(1.0, (m - i) * p[k]))
        out[k] = (running, running <= alpha)
    return out


# ------------------------------------------------------------------------------------------ the graph
def check_graph(w, G):
    """A graph of Bretz et al. (2009): weights in [0, 1] summing to at most 1; edges in [0, 1], none from
    a node to itself, each node's outgoing edges summing to at most 1."""
    if any(v < 0 or v > 1 for v in w.values()) or sum(w.values()) > 1:
        raise AnalysisError(f"graph: weights {w} are not a sub-probability")
    for (a, b), g in G.items():
        if a == b or a not in w or b not in w or g < 0 or g > 1:
            raise AnalysisError(f"graph: edge {a} -> {b} = {g} is not allowed")
    for a in w:
        if sum(g for (x, _), g in G.items() if x == a) > 1:
            raise AnalysisError(f"graph: the edges out of {a} sum above 1")


def remove_node(w, G, j):
    """Bretz et al. (2009), Algorithm 1 step 2: take node j out, passing its weight along its edges and
    re-routing every path through it. Exact in Fractions. Returns new (w, G); the inputs are unchanged."""
    rest = [n for n in w if n != j]
    zero = Fraction(0)
    w2 = {l: w[l] + w[j] * G.get((j, l), zero) for l in rest}
    G2 = {}
    for l in rest:
        g_lj = G.get((l, j), zero)
        for k in rest:
            if k == l:
                continue
            den = 1 - g_lj * G.get((j, l), zero)
            g = (G.get((l, k), zero) + g_lj * G.get((j, k), zero)) / den if den > 0 else zero
            if g:
                G2[(l, k)] = g
    return w2, G2


def graph_test(w, G, p, alpha=ALPHA):
    """Bretz et al. (2009), Algorithm 1: reject any H_j with p_j <= w_j alpha, update, repeat. Returns
    (rejected names in order, the trace of (name, weight, level, p), the weights left). The rejected set
    does not depend on which candidate is taken first (their Theorem 1); the smallest p_j / w_j is."""
    check_graph(w, G)
    w, G = dict(w), dict(G)
    rejected, trace = [], []
    while True:
        cand = [j for j in w if w[j] > 0 and p[j] <= float(w[j]) * alpha]
        if not cand:
            return rejected, trace, w
        j = min(cand, key=lambda k: (p[k] / float(w[k]), k))
        trace.append((j, w[j], float(w[j]) * alpha, p[j]))
        rejected.append(j)
        w, G = remove_node(w, G, j)


def graph_adjusted(w, G, p):
    """Adjusted p-values of the same procedure (Bretz et al. 2011, section 2.2): take the smallest
    p_j / w_j, q_j = max(that, the last q), cap 1, remove j, repeat; a node no weight reaches gets 1.
    H_j is rejected at alpha exactly when q_j <= alpha."""
    check_graph(w, G)
    w, G = dict(w), dict(G)
    q, last = {}, 0.0
    while w:
        live = [j for j in w if w[j] > 0]
        if not live:
            q.update({j: 1.0 for j in w})
            break
        j = min(live, key=lambda k: (p[k] / float(w[k]), k))
        last = min(1.0, max(last, p[j] / float(w[j])))
        q[j] = last
        w, G = remove_node(w, G, j)
    return q


def row113_graph(engines, ratios):
    """Row 113 (2)'s graph on all four engines and both ratios, with every node not in
    engines x ratios removed by Bretz's update (the docstring's DESIGN)."""
    k = len(ENGINE_IDS)
    w = {node(e, r): Fraction(0) for e in ENGINE_IDS for r in RATIOS}
    G = {}
    for e in ENGINE_IDS:
        w[node(e, "1.5")] = Fraction(1, k)
        G[(node(e, "1.5"), node(e, "0.5"))] = Fraction(1)
        for f in ENGINE_IDS:
            if f != e:
                G[(node(e, "0.5"), node(f, "1.5"))] = Fraction(1, k - 1)
    keep = {node(e, r) for e in engines for r in ratios}
    for n in [n for n in list(w) if n not in keep]:
        w, G = remove_node(w, G, n)
    check_graph(w, G)
    return w, G


# ------------------------------------------------------------------------------------------ analysis
def _d_family(x_by_node, w, G):
    """Both tests of d > 0 under the graph, for one set of paired differences per node."""
    t = {n: t_greater(x) for n, x in x_by_node.items()}
    s = {n: sign_greater(x) for n, x in x_by_node.items()}
    out = {}
    for name, res in (("t", t), ("sign", s)):
        p = {n: res[n]["p"] for n in res}
        rej, trace, _ = graph_test(w, G, p)
        q = graph_adjusted(w, G, p)
        out[name] = {"stat": res, "rejected": set(rej), "adjusted": q,
                     "trace": [(j, str(wt), lvl, pv) for j, wt, lvl, pv in trace]}
    return out


def _pair_family(x_by_node, engines, ratios, band_of):
    """Equivalence and difference for every pair and ratio, with the bands of `band_of(e, r)`."""
    eq, df = {}, {}
    for r in ratios:
        for i, j in itertools.combinations(engines, 2):
            b = math.hypot(band_of(i, r), band_of(j, r))
            key = f"{i}|{j}@r{r}"
            eq[key] = equivalence(x_by_node[node(i, r)], x_by_node[node(j, r)], b)
            df[key] = difference(x_by_node[node(i, r)], x_by_node[node(j, r)], b)
    h = holm({k: v["p"] for k, v in df.items()}) if df else {}
    for k in df:
        df[k]["holm_p"], df[k]["differ"] = h[k][0], bool(h[k][1])
    return eq, df


def _collapse(engines, ratios, d_rejected, eq):
    """Row 113 (3): at each ratio, every engine's d > 0 holds and every pair is equivalent."""
    if len(engines) < 2:
        return {r: None for r in ratios}
    return {r: all(node(e, r) in d_rejected for e in engines)
            and all(eq[f"{i}|{j}@r{r}"]["equivalent"] for i, j in itertools.combinations(engines, 2))
            for r in ratios}


def analyse(scores, context, sources=None):
    """Both documents in, the result (a JSON-able dict) out. `sources` is copied into the result."""
    sc = validate_scores(scores)
    cx = validate_context(context, sc)
    engines, ratios = cx["engines"], sc["ratios"]
    if len(engines) * len(ratios) > MAX_D_TESTS or math.comb(len(engines), 2) * len(ratios) > MAX_PAIR_TESTS:
        raise AnalysisError("more than row 113's 8 tests of d > 0 or 12 pair tests")
    w, G = row113_graph(engines, ratios)
    test_runs = len(engines) >= 2
    status = {e: ("confirmatory" if test_runs and cx["status"][e]["status"] == "confirmatory" else "exploratory")
              for e in engines}
    res = {"schema": RESULT_SCHEMA, "variant": sc["variant"], "engines_in_test": list(engines),
           "not_in_test": [e for e in ENGINE_IDS if e in sc["engines"] and e not in engines],
           "ratios": list(ratios), "seeds": {e: sc["engines"][e]["seeds"] for e in engines},
           "four_engine_test_runs": test_runs, "ford_in_test": FORD in engines, "status": status,
           "status_rule": {"s_p": cx["s_p"], "factor": pilot_factor(), "bound": cx["bound"],
                           "factor_definition": f"sqrt({PILOT_PAIRS - 1} / chi2_{1 - PILOT_BOUND:.2f},"
                                                f"{PILOT_PAIRS - 1}), exact (row 103 (4) prints 1.56)",
                           "s_star_level": cx["s_star_level"], "s_star_power": S_STAR_POWER,
                           "s_star": {e: cx["status"][e]["s_star"] for e in engines}},
           "graph": {"weights": {n: str(v) for n, v in w.items()},
                     "edges": {f"{a}->{b}": str(g) for (a, b), g in G.items()}},
           "ceiling": {node(e, r): cx["ceiling"][(e, r)] for e in engines for r in ratios},
           "constants": {"MEI": MEI, "alpha": ALPHA, "alpha_tost": ALPHA_TOST, "n_roads": N_ROADS},
           "sources": sources or {}, "provenance": {"scores": scores.get("provenance"),
                                                    "context": context.get("provenance")},
           "readings": {}}
    for reading in READINGS:
        band = {node(e, r): cx["band"][(e, r, reading)] for e in engines for r in ratios}
        rows = {node(e, r): paired_d(sc["engines"][e], r, reading) for e in engines for r in ratios}
        x = {n: [v[0] for v in rows[n]] for n in rows}
        fam = _d_family(x, w, G)
        corner = {sgn: _d_family({n: [v + sgn * band[n] for v in x[n]] for n in x}, w, G) for sgn in (-1, 1)}
        eq, dif = _pair_family(x, engines, ratios, lambda e, r: band[node(e, r)])
        eq0, dif0 = _pair_family(x, engines, ratios, lambda e, r: 0.0)
        d_rows = {}
        for n in x:
            e, r = n.split("@r")
            row = {"engine": e, "ratio": r, "n": len(x[n]), "d_per_seed": x[n],
                   "d_mean_form_per_seed": [v[1] for v in rows[n]],
                   "cut_sighted_per_seed": [v[2] for v in rows[n]], "cut_blind_per_seed": [v[3] for v in rows[n]],
                   "d_mean_form": float(np.mean([v[1] for v in rows[n]])), "band": band[n],
                   "ceiling": cx["ceiling"][(e, r)], "status": status[e]}
            for name in ("t", "sign"):
                verdict = n in fam[name]["rejected"]
                lim = any((n in corner[sgn][name]["rejected"]) != verdict for sgn in (-1, 1))
                row[name] = dict(fam[name]["stat"][n], adjusted_p=fam[name]["adjusted"][n], d_gt_0=verdict,
                                 at_minus_band=n in corner[-1][name]["rejected"],
                                 at_plus_band=n in corner[1][name]["rejected"], model_limited=lim)
            d_rows[n] = row
        pairs = {}
        for k in eq:
            i, rest = k.split("|")
            j, r = rest.split("@r")
            counts = node(i, r) in fam["t"]["rejected"] and node(j, r) in fam["t"]["rejected"]
            e_v, e0 = eq[k]["equivalent"], eq0[k]["equivalent"]
            pairs[k] = {"engines": [i, j], "ratio": r, "status": ("confirmatory" if status[i] == status[j] ==
                                                                  "confirmatory" else "exploratory"),
                        "ford_in_pair": FORD in (i, j), "counts": counts,
                        "equivalence": dict(eq[k], equivalent_without_band=e0, model_limited=e_v != e0),
                        "difference": dict(dif[k], differ_without_band=dif0[k]["differ"],
                                           holm_p_without_band=dif0[k]["holm_p"],
                                           model_limited=dif[k]["differ"] != dif0[k]["differ"])}
        col = _collapse(engines, ratios, fam["t"]["rejected"], eq)
        col_lib = _collapse(engines, ratios, corner[1]["t"]["rejected"], eq0)
        col_con = _collapse(engines, ratios, corner[-1]["t"]["rejected"], eq)
        collapse = {r: {"claimed": col[r], "model_limited": (col[r] is not None and
                                                             (col_lib[r] != col[r] or col_con[r] != col[r])),
                        "status": ("confirmatory" if test_runs and all(status[e] == "confirmatory"
                                                                        for e in engines) else "exploratory")}
                    for r in ratios}
        both = set(ratios) == set(RATIOS) and test_runs
        one = {"claimed": (all(col[r] for r in RATIOS) if both else None),
               "model_limited": (both and ((all(col_lib[r] for r in RATIOS) != all(col[r] for r in RATIOS))
                                           or (all(col_con[r] for r in RATIOS) != all(col[r] for r in RATIOS)))),
               "status": collapse[ratios[0]]["status"]}
        res["readings"][reading] = {
            "role": "primary" if reading == PRIMARY else f"beside: {WITH_KNOCK_LABEL}; decides nothing",
            "d": d_rows, "pairs": pairs, "collapse": collapse, "one_curve": one,
            "trace": {name: fam[name]["trace"] for name in ("t", "sign")}}
    return res


# ------------------------------------------------------------------------------------------ verdicts
def verdicts(res):
    """Every verdict of a result, keyed so two results can be compared (row 115)."""
    out = {}
    for reading, rd in res["readings"].items():
        for n, row in rd["d"].items():
            out[f"{reading} d>0 (t) {n}"] = row["t"]["d_gt_0"]
            out[f"{reading} d>0 (sign) {n}"] = row["sign"]["d_gt_0"]
        for k, pr in rd["pairs"].items():
            out[f"{reading} equivalent {k}"] = pr["equivalence"]["equivalent"]
            out[f"{reading} differ {k}"] = pr["difference"]["differ"]
        for r, c in rd["collapse"].items():
            out[f"{reading} collapse @r{r}"] = c["claimed"]
        out[f"{reading} one curve"] = rd["one_curve"]["claimed"]
    return out


def sensitivity(primary, variant, label):
    """Row 115: every verdict that flips between the primary result and a re-scored one reads
    "sensitive to <label>". The variant must have the same engines, ratios and seeds."""
    for key in ("engines_in_test", "ratios", "seeds"):
        if primary[key] != variant[key]:
            raise AnalysisError(f"sensitivity {label!r}: its {key} differ from the primary scoring's")
    a, b = verdicts(primary), verdicts(variant)
    return [f"sensitive to {label}: {k}: {a[k]} -> {b[k]}" for k in a if a[k] != b[k]]


# ------------------------------------------------------------------------------------------ power
def power_t(d, sigma, n, level):
    """Power of the one-sided one-sample t-test at `level`, true mean d, spread sigma, n pairs."""
    df = n - 1
    return float(stats.nct.sf(stats.t.ppf(1.0 - level, df), df, d / (sigma / math.sqrt(n))))


def s_star(ceiling, n, level, power=0.8):
    """Row 103 (4)'s s*: the spread that gives `power` at `level` with true d = the whole ceiling."""
    from scipy.optimize import brentq
    return float(brentq(lambda s: power_t(ceiling, s, n, level) - power, 1e-6, 1e3, xtol=1e-12))


def power_report():
    r6 = ROW_113_6
    levels = (("alpha/8", ALPHA / 8, "the review's \"Holm's first step\": plain Holm over 8"),
              ("alpha/4", ALPHA / 4, "row 113 (2)'s graph: an r = 1.5 test's first level, four engines"),
              ("alpha", ALPHA, "the last step"))
    L = [f"ROW 113 (6): false-negative risk (1 - power) at true d = {r6['d_obs']:.2f} points "
         f"(0.59 MEI = {0.59 * MEI:.4f}), n = {r6['n']} pairs, paired one-sided t (noncentral t)",
         f"  {'level':<18}" + "".join(f"{'spread ' + format(s, '.2f'):>16}" for s in r6["spreads"])]
    fn = {}
    for name, lvl, why in levels:
        fn[name] = [1.0 - power_t(r6["d_obs"], s, r6["n"], lvl) for s in r6["spreads"]]
        L.append(f"  {name + ' = ' + format(lvl, 'g'):<18}" + "".join(f"{v:16.4f}" for v in fn[name])
                 + f"    {why}")
    for name, printed in (("alpha/8", (r6["fn_first"],) * 2), ("alpha", r6["fn_alpha"])):
        got = [round(v, 2) for v in fn[name]]
        L.append(f"  the row prints {'-'.join(dict.fromkeys(map(str, printed)))} at {name}: "
                 + "; ".join(f"spread {s:.2f} gives {v:.4f}, {g:.2f} at two decimals "
                             f"({'reproduced' if g == pr else 'NOT reproduced'})"
                             for s, v, g, pr in zip(r6["spreads"], fn[name], got, printed)))
    L.append("  powers, for the review's power.txt: " + "; ".join(
        f"spread {s:.2f}: {power_t(r6['d_obs'], s, r6['n'], ALPHA / 8):.3f} (alpha/8) / "
        f"{power_t(r6['d_obs'], s, r6['n'], ALPHA):.3f} (alpha)" for s in r6["spreads"]))
    L.append("")
    L.append(f"ROW 103 (4): the pilot's factor sqrt({PILOT_PAIRS - 1} / chi2_0.20,{PILOT_PAIRS - 1}) = "
             f"{pilot_factor():.4f}; s* at full capture of the planning ceilings (r = 1.5, n = {r6['n']}):")
    for e, c in PLANNING_C15.items():
        L.append(f"  {e:<12} C {c:5.2f}: s* {s_star(c, r6['n'], ALPHA / 8):6.3f} at alpha/8 (power.py's), "
                 f"{s_star(c, r6['n'], ALPHA / 4):6.3f} at alpha/4 (the graph's first level)")
    return "\n".join(L), fn


# ------------------------------------------------------------------------------------------ the report
def _f(v, nd=2):
    return "-" if v is None else f"{v:.{nd}f}"


def _p(v):
    return f"{v:.4f}" if v >= 1e-4 else f"{v:.1e}"


def _iv(v):
    return f"{v[0]:.2f}..{v[1]:.2f}"


def _b(primary, with_knock, fmt):
    """A no-knock number with its with-knock number beside it, in brackets (row 113 (5))."""
    return f"{fmt(primary)} [{fmt(with_knock)}]"


def _verdict(t):
    return ("d > 0" if t["d_gt_0"] else "d > 0 not shown") + (" MODEL-LIMITED" if t["model_limited"] else "")


def _eq_word(pr):
    eq = pr["equivalence"]
    if not eq["equivalent"]:
        word = "not shown equivalent"
    else:
        word = "equivalent within the MEI" if pr["counts"] else "equivalent with no effect established: not a collapse"
    return word + (" MODEL-LIMITED" if eq["model_limited"] else "")


def _df_word(df):
    return ("differ" if df["differ"] else "not shown to differ") + (" MODEL-LIMITED" if df["model_limited"] else "")


def _collapse_word(c, res):
    if not c["claimed"]:
        word = "no collapse claimed"
    else:
        word = "a collapse on H/tau" if res["ford_in_test"] else TAU_NOTE
    return word + (" MODEL-LIMITED" if c["model_limited"] else "")


def report(res):
    """The text report. Every no-knock number has its with-knock number beside it in brackets."""
    P, K = res["readings"][PRIMARY], res["readings"]["with_knock"]
    L = [f"FOUR-ENGINE TEST (row 113) -- {'primary scoring' if res['variant'] is None else 'variant ' + res['variant']}",
         f"engines in the test (row 107): {', '.join(res['engines_in_test'])}"
         + (f"; in the scores, not in the test, not analysed: {', '.join(res['not_in_test'])}"
            if res["not_in_test"] else ""),
         f"ratios: {', '.join(res['ratios'])}; seeds per arm: "
         + ", ".join(f"{e} {len(s)}" for e, s in res["seeds"].items()),
         f"MEI {MEI} points; family-wise alpha {ALPHA}; reading: no knock (primary), "
         f"[with knock: {WITH_KNOCK_LABEL}; decides nothing]"]
    if not res["four_engine_test_runs"]:
        L.append("ONE ENGINE: the four-engine test does not run (row 107 (2)); everything below is the "
                 "B58's exploratory study, never a test of the criterion")
    if not res["ford_in_test"]:
        L.append("THE FORD IS NOT IN THE TEST: the agent study does not test H/tau against H (row 107 (6))")
    sr = res["status_rule"]
    L.append(f"status (row 103 (4)): {sr['factor']:.4f} x s_p {sr['s_p']:g} = {sr['bound']:.3f} against s*: "
             + ", ".join(f"{e} {sr['s_star'][e]:g} -> {res['status'][e]}" for e in res["engines_in_test"]))
    L.append(f"  the factor is {sr['factor_definition']}; s* at power {sr['s_star_power']:g} and the graph's "
             f"first level for an r = 1.5 test, alpha/{len(res['engines_in_test'])} = {sr['s_star_level']:g}")
    L.append("graph (row 113 (2), Bretz et al. 2009): weights "
             + ", ".join(f"{n} {v}" for n, v in res["graph"]["weights"].items() if v != "0") + "; edges "
             + ", ".join(f"{k} {v}" for k, v in res["graph"]["edges"].items()))
    L.append("")
    L.append("(1)-(2) d > 0 per engine and ratio: d = sighted cut - blind cut, paired by seed, evaluate.py's form;"
             " the mean form decides nothing")
    for n, row in P["d"].items():
        kr = K["d"][n]
        L.append(f"  {n:<20} d {_b(row['t']['mean'], kr['t']['mean'], _f)}  sd {_b(row['t']['sd'], kr['t']['sd'], _f)}"
                 f"  mean form {_b(row['d_mean_form'], kr['d_mean_form'], _f)}  band {_b(row['band'], kr['band'], _f)}"
                 f"  C {_f(row['ceiling'])}  n {row['n']}; {row['status']}")
        L.append(f"  {'':<20} t:    p {_b(row['t']['p'], kr['t']['p'], _p)}, graph p "
                 f"{_b(row['t']['adjusted_p'], kr['t']['adjusted_p'], _p)}: {_verdict(row['t'])} [{_verdict(kr['t'])}]")
        L.append(f"  {'':<20} sign: {row['sign']['positive']} of {row['sign']['nonzero']} "
                 f"[{kr['sign']['positive']} of {kr['sign']['nonzero']}] above 0, p "
                 f"{_b(row['sign']['p'], kr['sign']['p'], _p)}, graph p "
                 f"{_b(row['sign']['adjusted_p'], kr['sign']['adjusted_p'], _p)}: {_verdict(row['sign'])} "
                 f"[{_verdict(kr['sign'])}]")
    for reading, rd in ((PRIMARY, P), ("with_knock", K)):
        for name in ("t", "sign"):
            L.append(f"  the graph's rejections in order, {name}, {reading}: " + (", ".join(
                f"{j} at {lvl:.5f} (weight {wt}, p {_p(pv)})" for j, wt, lvl, pv in rd["trace"][name]) or "none"))
    if res["four_engine_test_runs"]:
        for r in res["ratios"]:
            L.append("")
            ceil = {e: res["ceiling"][node(e, r)] for e in res["engines_in_test"]}
            L.append(f"(3)-(4) pairs at r = {r}; ceilings C_e (row 103 (1)): "
                     + ", ".join(f"{e} {c:.2f}" for e, c in ceil.items()))
            if all(c < MEI for c in ceil.values()):
                L.append(f"  {CEILING_SENTENCE}")
            for k, pr in P["pairs"].items():
                if pr["ratio"] != r:
                    continue
                kp = K["pairs"][k]
                eq, df, ek, dk = pr["equivalence"], pr["difference"], kp["equivalence"], kp["difference"]
                L.append(f"  {k:<30} d_i - d_j {_b(eq['diff'], ek['diff'], _f)}  B {_b(eq['band'], ek['band'], _f)}; "
                         f"{pr['status']}" + ("" if pr["ford_in_pair"] else f"; {TAU_NOTE}"))
                L.append(f"  {'':<30} equivalence: 90 % {_b(eq['ci90'], ek['ci90'], _iv)}, widened "
                         f"{_b(eq['ci90_widened'], ek['ci90_widened'], _iv)}, TOST p "
                         f"{_p(eq['p_lower'])}/{_p(eq['p_upper'])} [{_p(ek['p_lower'])}/{_p(ek['p_upper'])}]: "
                         f"{_eq_word(pr)} [{_eq_word(kp)}]")
                L.append(f"  {'':<30} difference: p {_b(df['p'], dk['p'], _p)}, Holm p "
                         f"{_b(df['holm_p'], dk['holm_p'], _p)}: {_df_word(df)} [{_df_word(dk)}]; 95 % "
                         f"{_b(df['ci95'], dk['ci95'], _iv)}, widened {_b(df['ci95_widened'], dk['ci95_widened'], _iv)}")
            c, ck = P["collapse"][r], K["collapse"][r]
            L.append(f"  COLLAPSE at r = {r}: {_collapse_word(c, res)} [{_collapse_word(ck, res)}]; {c['status']}")
        o, ok = P["one_curve"], K["one_curve"]
        if o["claimed"] is None:
            L.append("ONE CURVE: not computed (it needs both ratios)")
        else:
            L.append(f"ONE CURVE: {'claimed' if o['claimed'] else 'not claimed'}"
                     + (" MODEL-LIMITED" if o["model_limited"] else "")
                     + f" [{'claimed' if ok['claimed'] else 'not claimed'}"
                     + (" MODEL-LIMITED" if ok["model_limited"] else "") + f"]; {o['status']}")
    return "\n".join(L)


# ------------------------------------------------------------------------------------------ CLI
def _sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _jsonable(o):
    if isinstance(o, dict):
        return {k: _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple, set)):
        return [_jsonable(v) for v in (sorted(o) if isinstance(o, set) else o)]
    if isinstance(o, float) and not math.isfinite(o):
        return None
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    return o


def _write(path, text, overwrite):
    if os.path.exists(path) and not overwrite:
        raise SystemExit(f"{path} exists; results are evidence and are not overwritten without --overwrite")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scores", help="a four-engine-scores/1 file (the primary scoring)")
    ap.add_argument("--context", help="a four-engine-context/1 file")
    ap.add_argument("--sensitivity", action="append", default=[], metavar="LABEL=PATH",
                    help="a re-scored four-engine-scores/1 file of row 115, with its label; repeatable")
    ap.add_argument("--out", help="write the result as JSON here")
    ap.add_argument("--report", help="write the text report here")
    ap.add_argument("--overwrite", action="store_true", help="replace an existing --out or --report")
    ap.add_argument("--power", action="store_true", help="print row 113 (6)'s power numbers, recomputed")
    a = ap.parse_args(argv)
    if a.power:
        print(power_report()[0])
        return 0
    if not (a.scores and a.context):
        ap.error("--scores and --context are required (or --power)")
    me = os.path.abspath(__file__)
    sources = {"scores": {"path": a.scores, "sha256": _sha(a.scores)},
               "context": {"path": a.context, "sha256": _sha(a.context)},
               "analysis": {"path": os.path.relpath(me, HERE), "sha256": _sha(me)}}
    try:
        scores = _load(a.scores)
        if scores.get("variant") is not None:
            raise AnalysisError(f"{a.scores}: the primary scoring has variant null, found {scores['variant']!r}")
        context = _load(a.context)
        res = analyse(scores, context, sources)
        text = report(res)
        flips = []
        for spec in a.sensitivity:
            label, sep, path = spec.partition("=")
            if not sep or not label.strip() or not path:
                raise AnalysisError(f"--sensitivity {spec!r}: LABEL=PATH")
            vdoc = _load(path)
            if vdoc.get("variant") != label:
                raise AnalysisError(f"{path}: variant {vdoc.get('variant')!r}, the command line says {label!r}")
            vres = analyse(vdoc, context, {"scores": {"path": path, "sha256": _sha(path)}})
            f = sensitivity(res, vres, label)
            flips += f
            res.setdefault("sensitivity", {})[label] = {"sha256": _sha(path), "flips": f}
        if a.sensitivity:
            text += "\n\nSENSITIVITY (row 115; no label, band or primary verdict moves)\n" + \
                    ("\n".join(f"  {f}" for f in flips) if flips else "  no verdict flips")
    except AnalysisError as exc:
        raise SystemExit(f"REFUSED: {exc}")
    print(text)
    if a.out:
        _write(a.out, json.dumps(_jsonable(res), indent=1, allow_nan=False) + "\n", a.overwrite)
    if a.report:
        _write(a.report, text + "\n", a.overwrite)
    return 0


if __name__ == "__main__":
    sys.exit(main())

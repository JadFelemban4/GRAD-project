"""test_four_engine_analysis.py -- four_engine_analysis.py: the schema's refusals, d, the tests of d > 0,
the graphical procedure, Holm, Welch, the equivalence and difference tests, MODEL-LIMITED, the collapse,
the sensitivity flips and the power numbers, each against an independent computation.

    python -B test_four_engine_analysis.py        48 tests in 16 s on the team laptop, 31 October 2026;
                                                   exit code 0 when all pass

ORDER_TO_TRAINING.md step 7 (row 113). Every score here is SYNTHETIC, made by this file with a fixed
NumPy seed: no agent, no road seed, no roads record, no plant run. Every class runs inside
test_epa_fixtures.forbid_real_data, so an open of an EPA table, logs/ or the contract fails the test.
The independent computations: scipy.stats.ttest_1samp and ttest_rel (the t-test), binomtest (the sign
test), ttest_ind(equal_var=False) with its confidence_interval and a hand-written Welch-Satterthwaite
(Welch), Python's statistics.median (the cut), hand-worked weights (the graph and Holm), a closed test
over every intersection (the graph's shortcut), a Monte Carlo of the t-test (the power), and the
scientific review's committed power.txt (row 113 (6)).

  Schema      a SYNTHETIC document passes; each refusal is shown able to fire: a wrong schema, a
              missing, extra or unpaired seed, 19 or 21 roads, a missing reading or arm, an extra arm, a
              non-finite or boolean value, D < 0, D_base <= 0, D_base that differs between arms, a seed
              "01", an unknown engine; the context without the B58, an engine in the test missing from
              the scores, a seed count other than seeds_per_arm, a band missing or below 0, a status
              row 103 (4)'s rule contradicts, a pilot of 4 pairs
  D           the cut is evaluate.py's form on a hand-made road set (an even count: the median is the
              mean of the two middle roads); the road-mean form beside it; both against
              statistics.median and a loop
  Tests       the t p-value against ttest_1samp and ttest_rel, one-sided; every difference equal; the
              sign test against binomtest, with ties and zeros (zeros dropped; all zero gives 1)
  Welch       diff, df, t and the 90 % and 95 % intervals against ttest_ind(equal_var=False) and a
              hand formula; the TOST p-values against shifted ttest_ind calls and against the interval
              form on 500 SYNTHETIC cases; the difference p against shifted ttest_ind calls, and p < 0.05
              exactly when the widened 95 % interval excludes 0
  Holm        a hand-worked case; the graph with equal weights and a complete graph is Holm (2000 cases)
  Graph       row 113's weights by hand on three cases (the r = 1.5 tests first, the r = 0.5 shares,
              no alpha on an r = 0.5 test before its own r = 1.5 test rejects); the adjusted p-values
              agree with the sequential test at every alpha; any order of rejection gives one set; the
              shortcut equals the closed test over all 255 intersections; monotone in the p-values; a
              dropped engine gives the direct three-engine graph; r = 1.5 alone is Holm; the row's
              literal words depend on the order (the docstring's DESIGN), Bretz's update does not; the
              two agree exactly under the docstring's condition, and differ when it breaks (3000 orders)
  Limited     a d > 0 verdict that the band can move reads MODEL-LIMITED, and with a band of 0 it does
              not; an equivalence that only the band refuses reads MODEL-LIMITED
  Collapse    every engine's d > 0 and every pair equivalent claims it; an engine without an effect
              leaves its pairs uncounted and no collapse; equivalence where no d > 0 holds reads
              "equivalent with no effect established: not a collapse"; without the Ford the
              wording is row 107 (6)'s; one curve needs both ratios; one engine runs no test; the
              end-to-end numbers against scipy on a SYNTHETIC four-engine set
  CLI         --out and --report written into a temporary folder, refused the second time without
              --overwrite; a variant that flips a verdict prints "sensitive to"; a primary scoring with
              a variant label is refused
  Power       row 113 (6)'s 0.97 and 0.83-0.86; the review's power.txt to its printed digit (every
              power and s* line); a Monte Carlo of the t-test within 4 standard errors; the factor 1.56
  Hygiene     the script imports no plant or EPA module; no hashed or frozen file names it (row 121);
              its engine ids are engines.PLANTS'
"""
import ast
import io
import itertools
import json
import math
import os
import re
import statistics
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from fractions import Fraction

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import four_engine_analysis as A  # noqa: E402
from test_epa_fixtures import Guarded  # noqa: E402  (WP3_INTERFACES.md 9.1)

POWER_TXT = os.path.join(HERE, "results", "EPA_ROADS", "probe_2026-10-30", "review", "power.txt")
E4 = A.ENGINE_IDS
B, M, H, F = E4                     # b58, mazda_25t, honda_l15b7, ford_27tt


# ------------------------------------------------------------------------------------------ SYNTHETIC data
def synthetic_scores(rng_seed, d_true, *, engines=E4, ratios=("0.5", "1.5"), n=20, sd=3.0, blind_sd=6.0,
                     ties=0, extra_engines=()):
    """A SYNTHETIC four-engine-scores/1 document. d_true[(e, r)] is the true sighted - blind cut in
    points; each seed's cuts carry normal noise; the roads carry noise of their own, so the mean form
    differs from evaluate.py's. `ties` seeds per engine get a sighted arm equal to the blind one."""
    rng = np.random.default_rng(rng_seed)
    eng = {}
    for e in tuple(engines) + tuple(extra_engines):
        base = 80.0 + 60.0 * rng.random(A.N_ROADS)
        knock_base = 5.0 + 20.0 * rng.random(A.N_ROADS)
        arms = {"blind": {"seeds": {}}, **{A.arm_name(r): {"seeds": {}} for r in ratios}}
        for s in range(n):
            c_blind = 30.0 + blind_sd * rng.standard_normal()
            road_blind = 1.0 + 0.05 * rng.standard_normal(A.N_ROADS)
            entry = {}
            for arm, c in [("blind", c_blind)] + [(A.arm_name(r), c_blind + d_true.get((e, r), 0.0)
                                                    + sd * rng.standard_normal()) for r in ratios]:
                if arm != "blind" and s < ties:
                    c, road = c_blind, road_blind
                else:
                    road = road_blind if arm == "blind" else 1.0 + 0.05 * rng.standard_normal(A.N_ROADS)
                D = base * (1.0 - c / 100.0) * road
                Dk = D + knock_base * (1.0 - (c - 2.0) / 100.0)
                arms[arm]["seeds"][str(s)] = {"no_knock": {"D": D.tolist(), "D_base": base.tolist()},
                                              "with_knock": {"D": Dk.tolist(),
                                                             "D_base": (base + knock_base).tolist()}}
        eng[e] = {"arms": arms}
    return {"schema": A.SCORES_SCHEMA, "ratios": list(ratios), "n_roads": A.N_ROADS, "variant": None,
            "provenance": {"made_by": "test_four_engine_analysis: SYNTHETIC, no agent, no road seed"},
            "engines": eng}


def synthetic_context(*, engines=E4, ratios=("0.5", "1.5"), n=20, band=1.0, s_p=None, ceiling=3.0,
                      status=None):
    """A SYNTHETIC four-engine-context/1 document. `ceiling` is one number or {engine: C}; s* is what the
    script requires (A.status_star: the graph's first level, alpha/k); s_p defaults to half the smallest
    s* over the factor, so every engine is confirmatory, as the rule then says."""
    st = status or {}
    ceil = ceiling if isinstance(ceiling, dict) else {e: ceiling for e in engines}
    s_star = A.status_star({e: ceil[e] for e in engines}, n)
    if s_p is None:
        s_p = 0.5 * min(s_star.values()) / A.pilot_factor()
    rule = {e: "confirmatory" if A.pilot_factor() * s_p <= s_star[e] else "exploratory" for e in engines}
    return {"schema": A.CONTEXT_SCHEMA, "engines_in_test": list(engines), "seeds_per_arm": n,
            "model_band": {e: {r: {"no_knock": band, "with_knock": band} for r in ratios} for e in engines},
            "ceiling": {e: {r: ceil[e] for r in ratios} for e in engines},
            "status": {e: st.get(e, rule[e]) for e in engines},
            "status_basis": {"s_p": s_p, "pilot_pairs": 5, "s_star": s_star},
            "provenance": {"made_by": "test_four_engine_analysis: SYNTHETIC"}}


def scores_from_cuts(cuts, *, ratios=("1.5",)):
    """A SYNTHETIC document whose cuts are exactly the given ones: cuts[e] = (blind list, {r: sighted
    list}); every road is the same scale of one base, so median and mean forms both equal the cut."""
    base = np.linspace(90.0, 150.0, A.N_ROADS)
    eng = {}
    for e, (blind, sighted) in cuts.items():
        arms = {"blind": {"seeds": {}}, **{A.arm_name(r): {"seeds": {}} for r in ratios}}
        for arm, cl in [("blind", blind)] + [(A.arm_name(r), sighted[r]) for r in ratios]:
            for s, c in enumerate(cl):
                D = (base * (1.0 - c / 100.0)).tolist()
                arms[arm]["seeds"][str(s)] = {rd: {"D": D, "D_base": base.tolist()} for rd in A.READINGS}
        eng[e] = {"arms": arms}
    return {"schema": A.SCORES_SCHEMA, "ratios": list(ratios), "n_roads": A.N_ROADS, "engines": eng}


def scipy_cut(D, D_base):
    return 100.0 * (1.0 - statistics.median(D) / statistics.median(D_base))


# ------------------------------------------------------------------------------------------ Schema
class Schema(Guarded):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.doc = synthetic_scores(11, {(e, r): 4.0 for e in E4 for r in A.RATIOS}, n=4)
        cls.ctx = synthetic_context(n=4)

    def fresh(self):
        return json.loads(json.dumps(self.doc)), json.loads(json.dumps(self.ctx))

    def refused(self, doc, ctx, pattern):
        with self.assertRaisesRegex(A.AnalysisError, pattern):
            A.analyse(doc, ctx)

    def test_a_synthetic_document_passes(self):
        res = A.analyse(*self.fresh())
        self.assertEqual(res["engines_in_test"], list(E4))
        self.assertEqual(res["seeds"][B], [0, 1, 2, 3])

    def test_the_schema_string(self):
        d, c = self.fresh()
        d["schema"] = "four-engine-scores/2"
        self.refused(d, c, "this script reads")
        d, c = self.fresh()
        c["schema"] = "four-engine-context/0"
        self.refused(d, c, "this script reads")

    def test_unpaired_missing_and_extra_seeds(self):
        d, c = self.fresh()
        del d["engines"][M]["arms"]["sighted_r1.5"]["seeds"]["2"]
        self.refused(d, c, r"unpaired seeds.*'sighted_r1.5': \[2\]")
        d, c = self.fresh()
        d["engines"][H]["arms"]["blind"]["seeds"]["9"] = d["engines"][H]["arms"]["blind"]["seeds"]["0"]
        self.refused(d, c, r"unpaired seeds.*\[9\]")
        d, c = self.fresh()
        for arm in d["engines"][F]["arms"].values():
            del arm["seeds"]["3"]
        self.refused(d, c, "3 seeds per arm, the context fixes 4")
        d, c = self.fresh()
        for arm in d["engines"][F]["arms"].values():
            for s in ("1", "2", "3"):
                del arm["seeds"][s]
        self.refused(d, c, "needs at least 2")

    def test_the_road_count(self):
        for n in (19, 21):
            d, c = self.fresh()
            entry = d["engines"][B]["arms"]["blind"]["seeds"]["1"]["no_knock"]
            entry["D"] = (entry["D"] * 2)[:n]
            self.refused(d, c, f"20 roads required, found {n}")
        d, c = self.fresh()
        d["n_roads"] = 19
        self.refused(d, c, "row 101 fixes 20")

    def test_arms_readings_and_values(self):
        d, c = self.fresh()
        del d["engines"][B]["arms"]["sighted_r0.5"]
        self.refused(d, c, r"missing \['sighted_r0.5'\]")
        d, c = self.fresh()
        d["engines"][B]["arms"]["sighted_r1.0"] = d["engines"][B]["arms"]["blind"]
        self.refused(d, c, "keys not in the schema")
        d, c = self.fresh()
        del d["engines"][M]["arms"]["blind"]["seeds"]["0"]["with_knock"]
        self.refused(d, c, r"missing \['with_knock'\]")
        for bad in (float("nan"), float("inf"), True, "3.0", None):
            d, c = self.fresh()
            d["engines"][M]["arms"]["blind"]["seeds"]["0"]["no_knock"]["D"][4] = bad
            self.refused(d, c, "a finite number is required")
        d, c = self.fresh()
        d["engines"][M]["arms"]["blind"]["seeds"]["0"]["no_knock"]["D"][4] = -1.0
        self.refused(d, c, "a damage below 0")
        d, c = self.fresh()
        for arm in d["engines"][M]["arms"].values():
            for s in arm["seeds"].values():
                s["no_knock"]["D_base"][2] = 0.0
        self.refused(d, c, "at or below 0")

    def test_a_baseline_that_moves_between_arms_is_refused(self):
        d, c = self.fresh()
        d["engines"][H]["arms"]["sighted_r0.5"]["seeds"]["1"]["with_knock"]["D_base"][7] *= 1.0 + 1e-6
        self.refused(d, c, r"D_base \(with_knock\) differs")
        d, c = self.fresh()                                     # the control: within D_BASE_RTOL passes
        d["engines"][H]["arms"]["sighted_r0.5"]["seeds"]["1"]["with_knock"]["D_base"][7] *= 1.0 + 1e-12
        A.analyse(d, c)

    def test_seed_keys_engines_ratios(self):
        d, c = self.fresh()
        arm = d["engines"][B]["arms"]["blind"]["seeds"]
        arm["01"] = arm.pop("1")
        self.refused(d, c, "no leading zero")
        d, c = self.fresh()
        d["engines"]["b48"] = d["engines"].pop(B)
        self.refused(d, c, "not an engine id")
        d, c = self.fresh()
        d["ratios"] = ["1.5", "0.5"]
        self.refused(d, c, "in the order")
        d, c = self.fresh()
        d["ratios"] = ["1.0"]
        self.refused(d, c, "one or both")
        d, c = self.fresh()
        d["variant"] = "  "
        self.refused(d, c, "non-empty label")

    def test_the_context(self):
        d, c = self.fresh()
        c["engines_in_test"] = [M, H]
        self.refused(d, c, "the B58 is never dropped")
        d, c = self.fresh()
        del d["engines"][H]
        self.refused(d, c, r"\['honda_l15b7'\] in the test but not in the scores")
        d, c = self.fresh()
        del c["model_band"][F]["1.5"]
        self.refused(d, c, r"missing \['1.5'\]")
        d, c = self.fresh()
        c["model_band"][F]["1.5"]["no_knock"] = -0.1
        self.refused(d, c, "at least 0")
        d, c = self.fresh()
        c["status"][M] = "exploratory"                          # every s* above 1.5576 s_p: confirmatory
        self.refused(d, c, "rule gives 'confirmatory'")
        d, c = self.fresh()
        c["status_basis"]["pilot_pairs"] = 4
        self.refused(d, c, "factor is for 5 pairs")
        d, c = self.fresh()
        c["status_basis"]["s_star"][M] *= 1.01                 # not the graph's first level's s*
        self.refused(d, c, r"s\* at the graph's first level alpha/4")
        d, c = self.fresh()
        lvl8 = A.s_star(c["ceiling"][M]["1.5"], 4, A.ALPHA / 8)   # power.py's alpha/8 (finding S3)
        c["status_basis"]["s_star"][M] = lvl8
        self.refused(d, c, r"s\* at the graph's first level alpha/4")
        # the Mazda's ceiling small enough that its s* falls under the bound: the rule says exploratory
        ceil = {B: 3.0, M: 1.0, H: 3.0, F: 3.0}
        star = A.status_star(ceil, 4)
        s_p = 0.5 * (star[M] + star[B]) / A.pilot_factor()
        c = synthetic_context(n=4, ceiling=ceil, s_p=s_p)
        self.assertEqual((c["status"][M], c["status"][B]), ("exploratory", "confirmatory"))
        c["status"][M] = "confirmatory"
        self.refused(d, c, "rule gives 'exploratory'")
        c["status"][M] = "exploratory"
        res = A.analyse(d, c)
        self.assertEqual(res["status"][M], "exploratory")
        self.assertEqual(res["status"][B], "confirmatory")
        self.assertEqual(res["status_rule"]["s_star_level"], A.ALPHA / 4)
        self.assertIn("exact", res["status_rule"]["factor_definition"])

    def test_s_star_is_taken_at_alpha_over_the_engines_in_the_test(self):
        """Finding S3: alpha/k with k engines in the test (1/k each after Bretz's removal), so with the
        Ford dropped the level is alpha/3; and the planning ceilings give --power's alpha/4 numbers."""
        self.assertEqual(A.s_star_level(4), A.ALPHA / 4)
        self.assertEqual(A.s_star_level(3), A.ALPHA / 3)
        got = A.status_star(A.PLANNING_C15, 20)
        self.assertEqual([round(v, 3) for v in got.values()], [8.064, 4.600, 7.334, 3.383])
        three = A.status_star({e: A.PLANNING_C15[e] for e in (B, M, H)}, 20)
        self.assertTrue(all(three[e] > got[e] for e in (B, M, H)))

    def test_an_engine_dropped_by_run_2_is_not_analysed(self):
        d, c = self.fresh()
        c = synthetic_context(engines=(B, M, H), n=4)          # the Ford dropped, its scores still present
        res = A.analyse(d, c)
        self.assertEqual(res["not_in_test"], [F])
        self.assertFalse(res["ford_in_test"])
        self.assertNotIn(A.node(F, "1.5"), res["readings"]["no_knock"]["d"])
        self.assertEqual(len(res["readings"]["no_knock"]["pairs"]), 6)        # 3 pairs x 2 ratios
        self.assertIn("does not test H/tau against H", A.report(res))


# ------------------------------------------------------------------------------------------ D
class D(Guarded):
    def test_the_cut_is_evaluates_form(self):
        rng = np.random.default_rng(3)
        D_ = 50 + 100 * rng.random(A.N_ROADS)
        Db = 100 + 100 * rng.random(A.N_ROADS)
        srt = sorted(D_)
        self.assertAlmostEqual(float(np.median(D_)), (srt[9] + srt[10]) / 2, places=12)
        self.assertAlmostEqual(A.cut(D_, Db), scipy_cut(D_.tolist(), Db.tolist()), places=12)
        self.assertAlmostEqual(A.road_mean_points(D_, Db),
                               sum(100 * (1 - a / b) for a, b in zip(D_, Db)) / A.N_ROADS, places=12)
        self.assertNotAlmostEqual(A.cut(D_, Db), A.road_mean_points(D_, Db), places=3)

    def test_d_is_sighted_minus_blind_paired_by_seed(self):
        doc = synthetic_scores(5, {(B, "1.5"): 4.0}, engines=(B,), ratios=("1.5",), n=6)
        sc = A.validate_scores(doc)
        rows = A.paired_d(sc["engines"][B], "1.5", "no_knock")
        for s, (d, dm, cs, cb) in enumerate(rows):
            sig = doc["engines"][B]["arms"]["sighted_r1.5"]["seeds"][str(s)]["no_knock"]
            bl = doc["engines"][B]["arms"]["blind"]["seeds"][str(s)]["no_knock"]
            self.assertAlmostEqual(d, scipy_cut(sig["D"], sig["D_base"]) - scipy_cut(bl["D"], bl["D_base"]), places=10)
            self.assertAlmostEqual(dm, A.road_mean_points(sig["D"], sig["D_base"])
                                   - A.road_mean_points(bl["D"], bl["D_base"]), places=10)


# ------------------------------------------------------------------------------------------ Tests
class Tests(Guarded):
    def test_the_t_test_against_scipy(self):
        rng = np.random.default_rng(7)
        for _ in range(50):
            n = int(rng.integers(3, 30))
            sig, bl = rng.normal(31, 8, n), rng.normal(30, 8, n)
            x = sig - bl
            t = A.t_greater(x)
            ref1 = stats.ttest_1samp(x, 0.0, alternative="greater")
            ref2 = stats.ttest_rel(sig, bl, alternative="greater")
            self.assertAlmostEqual(t["t"], float(ref1.statistic), places=10)
            self.assertAlmostEqual(t["p"], float(ref1.pvalue), places=12)
            self.assertAlmostEqual(t["p"], float(ref2.pvalue), places=12)
            self.assertEqual(t["df"], n - 1)

    def test_every_difference_equal(self):
        self.assertEqual(A.t_greater([2.0, 2.0, 2.0])["p"], 0.0)
        self.assertEqual(A.t_greater([0.0, 0.0, 0.0])["p"], 1.0)
        self.assertEqual(A.t_greater([-1.0, -1.0])["p"], 1.0)

    def test_the_sign_test_against_binomtest_with_ties_and_zeros(self):
        cases = [[1, -1, 0, 0, 2], [3, 3, 3, 3, 3], [0, 0, 0], [0.5] * 20, [-2, -2, 1, 0, 1, 1, 1, 0],
                 [1.0] * 15 + [-1.0] * 5]
        rng = np.random.default_rng(9)
        cases += [list(np.round(rng.normal(0.5, 2, int(rng.integers(5, 25))))) for _ in range(40)]
        for x in cases:
            s = A.sign_greater(x)
            pos = sum(v > 0 for v in x)
            nz = sum(v != 0 for v in x)
            self.assertEqual((s["positive"], s["nonzero"], s["zero"]), (pos, nz, len(x) - nz))
            ref = 1.0 if nz == 0 else stats.binomtest(pos, nz, 0.5, alternative="greater").pvalue
            self.assertAlmostEqual(s["p"], ref, places=12, msg=str(x))
        self.assertEqual(A.sign_greater([1, -1, 0, 0, 2])["p"], 0.5)          # by hand: 4 of 8 outcomes
        self.assertEqual(A.sign_greater([1] * 5)["p"], 1 / 32)


# ------------------------------------------------------------------------------------------ Welch
def welch_by_hand(x, y):
    nx, ny = len(x), len(y)
    mx, my = sum(x) / nx, sum(y) / ny
    vx = sum((v - mx) ** 2 for v in x) / (nx - 1) / nx
    vy = sum((v - my) ** 2 for v in y) / (ny - 1) / ny
    return mx - my, math.sqrt(vx + vy), (vx + vy) ** 2 / (vx ** 2 / (nx - 1) + vy ** 2 / (ny - 1))


class Welch(Guarded):
    def test_welch_against_scipy_and_a_hand_formula(self):
        rng = np.random.default_rng(13)
        for _ in range(100):
            nx, ny = int(rng.integers(3, 25)), int(rng.integers(3, 25))
            x, y = rng.normal(3, rng.uniform(1, 20), nx), rng.normal(1, rng.uniform(1, 20), ny)
            diff, se, df = A.welch(x, y)
            hd, hse, hdf = welch_by_hand(list(x), list(y))
            self.assertAlmostEqual(diff, hd, places=10)
            self.assertAlmostEqual(se, hse, places=10)
            self.assertAlmostEqual(df, hdf, places=8)
            ref = stats.ttest_ind(x, y, equal_var=False)
            self.assertAlmostEqual(diff / se, float(ref.statistic), places=10)
            self.assertAlmostEqual(df, float(ref.df), places=8)
            eq = A.equivalence(x, y, 0.0)
            ci = ref.confidence_interval(0.90)
            self.assertAlmostEqual(eq["ci90"][0], float(ci.low), places=9)
            self.assertAlmostEqual(eq["ci90"][1], float(ci.high), places=9)
            dif = A.difference(x, y, 0.0)
            ci = ref.confidence_interval(0.95)
            self.assertAlmostEqual(dif["ci95"][0], float(ci.low), places=9)
            self.assertAlmostEqual(dif["ci95"][1], float(ci.high), places=9)
            self.assertAlmostEqual(dif["p"], float(ref.pvalue), places=12)          # B = 0: two-sided Welch

    def test_tost_against_shifted_scipy_and_the_interval_form(self):
        rng = np.random.default_rng(17)
        agree = 0
        for _ in range(500):
            n1, n2 = int(rng.integers(4, 25)), int(rng.integers(4, 25))
            x, y = rng.normal(rng.uniform(-6, 6), rng.uniform(0.5, 8), n1), rng.normal(0, rng.uniform(0.5, 8), n2)
            band = float(rng.uniform(0, 4))
            eq = A.equivalence(x, y, band)
            lim = A.MEI - band
            p_lo = stats.ttest_ind(x + lim, y, equal_var=False, alternative="greater").pvalue
            p_hi = stats.ttest_ind(x - lim, y, equal_var=False, alternative="less").pvalue
            self.assertAlmostEqual(eq["p_lower"], float(p_lo), places=10)
            self.assertAlmostEqual(eq["p_upper"], float(p_hi), places=10)
            self.assertEqual(eq["equivalent"], max(p_lo, p_hi) < 0.05)
            agree += eq["equivalent"]
        self.assertGreater(agree, 20)                        # both verdicts occur in the SYNTHETIC cases
        self.assertLess(agree, 480)

    def test_a_band_as_wide_as_the_mei_is_never_equivalent(self):
        x, y = [1.0, 1.1, 0.9, 1.05], [1.0, 1.02, 0.98, 1.01]
        self.assertTrue(A.equivalence(x, y, 0.0)["equivalent"])
        self.assertFalse(A.equivalence(x, y, A.MEI)["equivalent"])

    def test_the_difference_test_against_shifted_scipy(self):
        rng = np.random.default_rng(19)
        for _ in range(300):
            n1, n2 = int(rng.integers(4, 25)), int(rng.integers(4, 25))
            x, y = rng.normal(rng.uniform(-15, 15), rng.uniform(0.5, 8), n1), rng.normal(0, rng.uniform(0.5, 8), n2)
            band = float(rng.uniform(0, 5))
            dif = A.difference(x, y, band)
            p_up = stats.ttest_ind(x - band, y, equal_var=False, alternative="greater").pvalue
            p_dn = stats.ttest_ind(x + band, y, equal_var=False, alternative="less").pvalue
            self.assertAlmostEqual(dif["p"], min(1.0, 2 * min(float(p_up), float(p_dn))), places=10)
            lo, hi = dif["ci95_widened"]
            self.assertEqual(dif["p"] < 0.05, lo > 0 or hi < 0)


# ------------------------------------------------------------------------------------------ Holm and the graph
def holm_graph(names):
    m = len(names)
    w = {n: Fraction(1, m) for n in names}
    G = {(a, b): Fraction(1, m - 1) for a in names for b in names if a != b}
    return w, G


def direct_three_engine_graph(engines):
    """Row 113's graph written directly for three engines: 1/3, edge 1 to the own r = 0.5 test, 1/2 to
    each other engine's r = 1.5 test."""
    w, G = {}, {}
    for e in engines:
        w[A.node(e, "1.5")], w[A.node(e, "0.5")] = Fraction(1, 3), Fraction(0)
        G[(A.node(e, "1.5"), A.node(e, "0.5"))] = Fraction(1)
        for f in engines:
            if f != e:
                G[(A.node(e, "0.5"), A.node(f, "1.5"))] = Fraction(1, 2)
    return w, G


def literal_rule(order, engines=E4):
    """Row 113 (2)'s words read literally: an r = 0.5 test's weight goes in equal shares to the r = 1.5
    tests not yet rejected, or, when none is left, to the r = 0.5 tests not yet rejected."""
    w = {A.node(e, r): (Fraction(1, len(engines)) if r == "1.5" else Fraction(0)) for e in engines for r in A.RATIOS}
    for j in order:
        wj, e = w.pop(j), j.split("@r")[0]
        if j.endswith("1.5"):
            w[A.node(e, "0.5")] += wj
        else:
            to = [n for n in w if n.endswith("1.5")] or [n for n in w if n.endswith("0.5")]
            for n in to:
                w[n] += wj / len(to)
    return w


def bretz_after(order, w, G):
    for j in order:
        w, G = A.remove_node(w, G, j)
    return w


class Holm(Guarded):
    def test_a_hand_worked_case(self):
        p = {"a": 0.01, "b": 0.04, "c": 0.03, "d": 0.005}
        h = A.holm(p)
        # sorted 0.005 x 4 = 0.02; 0.01 x 3 = 0.03; 0.03 x 2 = 0.06; 0.04 x 1 -> max(0.06, 0.04) = 0.06
        self.assertEqual({k: round(v[0], 12) for k, v in h.items()}, {"d": 0.02, "a": 0.03, "c": 0.06, "b": 0.06})
        self.assertEqual({k for k, v in h.items() if v[1]}, {"a", "d"})

    def test_the_holm_graph_is_holm(self):
        rng = np.random.default_rng(23)
        for _ in range(2000):
            m = int(rng.integers(2, 9))
            names = [f"h{i}" for i in range(m)]
            p = {n: float(v) for n, v in zip(names, rng.uniform(0, 0.08, m) ** rng.uniform(0.5, 2))}
            w, G = holm_graph(names)
            rej, _, _ = A.graph_test(w, G, p)
            h = A.holm(p)
            self.assertEqual(set(rej), {k for k, v in h.items() if v[1]})
            q = A.graph_adjusted(w, G, p)
            for k in names:
                self.assertAlmostEqual(q[k], h[k][0], places=12)


class Graph(Guarded):
    def test_row_113s_initial_graph(self):
        w, G = A.row113_graph(E4, A.RATIOS)
        for e in E4:
            self.assertEqual(w[A.node(e, "1.5")], Fraction(1, 4))
            self.assertEqual(w[A.node(e, "0.5")], 0)
            self.assertEqual(G[(A.node(e, "1.5"), A.node(e, "0.5"))], 1)
            for f in E4:
                if f != e:
                    self.assertEqual(G[(A.node(e, "0.5"), A.node(f, "1.5"))], Fraction(1, 3))
        self.assertEqual(len(G), 4 + 12)

    def test_hand_worked_one_the_r05_share_goes_to_the_r15_tests(self):
        # B58 r1.5 0.010 <= 0.05/4: rejected, its 1/4 to B58 r0.5 (0.0125); 0.011: rejected, 1/12 to each
        # other r1.5 test (1/3, 0.016667); Mazda r1.5 0.015: rejected, its 1/3 to Mazda r0.5 (0.016667);
        # Mazda r0.5 0.020 and Honda r1.5 0.030 are above 0.016667; nothing else.
        p = {A.node(B, "1.5"): 0.010, A.node(B, "0.5"): 0.011, A.node(M, "1.5"): 0.015, A.node(M, "0.5"): 0.020,
             A.node(H, "1.5"): 0.030, A.node(H, "0.5"): 1e-9, A.node(F, "1.5"): 0.2, A.node(F, "0.5"): 1e-9}
        w, G = A.row113_graph(E4, A.RATIOS)
        rej, trace, left = A.graph_test(w, G, p)
        self.assertEqual(rej, [A.node(B, "1.5"), A.node(B, "0.5"), A.node(M, "1.5")])
        self.assertEqual([t[1] for t in trace], [Fraction(1, 4), Fraction(1, 4), Fraction(1, 3)])
        self.assertEqual(left, {A.node(M, "0.5"): Fraction(1, 3), A.node(H, "1.5"): Fraction(1, 3),
                                A.node(H, "0.5"): 0, A.node(F, "1.5"): Fraction(1, 3), A.node(F, "0.5"): 0})

    def test_hand_worked_two_with_no_r15_left_the_r05_tests_share(self):
        # every r1.5 at 0.001: rejected, each r0.5 at 1/4. B58 r0.5 0.012 <= 0.0125: its 1/4 in thirds to
        # the r0.5 tests (1/3 each, 0.016667); Mazda r0.5 0.016: halves (1/2, 0.025); Honda r0.5 0.024:
        # the Ford's r0.5 at 1 (0.05); 0.049 rejects, 0.051 does not.
        for ford, n_rej in ((0.049, 8), (0.051, 7)):
            p = {A.node(e, "1.5"): 0.001 for e in E4}
            p.update({A.node(B, "0.5"): 0.012, A.node(M, "0.5"): 0.016, A.node(H, "0.5"): 0.024, A.node(F, "0.5"): ford})
            w, G = A.row113_graph(E4, A.RATIOS)
            rej, trace, _ = A.graph_test(w, G, p)
            self.assertEqual(len(rej), n_rej)
            self.assertEqual([t[1] for t in trace[4:]], [Fraction(1, 4), Fraction(1, 3), Fraction(1, 2), Fraction(1)][:n_rej - 4])

    def test_no_alpha_on_an_r05_test_before_its_r15_test_rejects(self):
        p = {A.node(e, "1.5"): 0.0126 for e in E4}
        p.update({A.node(e, "0.5"): 1e-12 for e in E4})
        w, G = A.row113_graph(E4, A.RATIOS)
        self.assertEqual(A.graph_test(w, G, p)[0], [])
        q = A.graph_adjusted(w, G, p)
        self.assertTrue(all(v > 0.05 for v in q.values()))

    def test_adjusted_p_values_agree_with_the_sequential_test(self):
        rng = np.random.default_rng(29)
        w, G = A.row113_graph(E4, A.RATIOS)
        names = list(w)
        for _ in range(500):
            p = {n: float(v) for n, v in zip(names, rng.uniform(0, 0.1, len(names)) ** rng.uniform(0.5, 3))}
            q = A.graph_adjusted(w, G, p)
            for alpha in (0.01, 0.025, 0.05, 0.1):
                rej, _, _ = A.graph_test(w, G, p, alpha)
                self.assertEqual(set(rej), {n for n in names if q[n] <= alpha})

    def test_the_rejected_set_does_not_depend_on_the_order(self):
        rng = np.random.default_rng(31)
        w0, G0 = A.row113_graph(E4, A.RATIOS)
        for _ in range(300):
            p = {n: float(v) for n, v in zip(w0, rng.uniform(0, 0.06, len(w0)))}
            ref = set(A.graph_test(w0, G0, p)[0])
            w, G, rej = dict(w0), dict(G0), set()
            while True:
                cand = [j for j in w if w[j] > 0 and p[j] <= float(w[j]) * A.ALPHA]
                if not cand:
                    break
                j = cand[int(rng.integers(len(cand)))]
                rej.add(j)
                w, G = A.remove_node(w, G, j)
            self.assertEqual(rej, ref)

    def test_the_shortcut_equals_the_closed_test(self):
        """Bretz et al. (2009), Theorem 1: H_i is rejected by the graph exactly when every intersection
        J containing it is rejected by the weighted Bonferroni test with the graph's weights on J."""
        w0, G0 = A.row113_graph(E4, A.RATIOS)
        names = list(w0)
        wJ = {}
        for k in range(1, len(names) + 1):
            for J in itertools.combinations(names, k):
                w, G = w0, G0
                for j in names:
                    if j not in J:
                        w, G = A.remove_node(w, G, j)
                self.assertLessEqual(sum(w.values()), 1)
                wJ[J] = w
        rng = np.random.default_rng(37)
        for _ in range(150):
            p = {n: float(v) for n, v in zip(names, rng.uniform(0, 0.05, len(names)) ** rng.uniform(0.7, 2))}
            closed = {i for i in names if all(any(p[j] <= float(w[j]) * A.ALPHA for j in J)
                                              for J, w in wJ.items() if i in J)}
            self.assertEqual(set(A.graph_test(w0, G0, p)[0]), closed)

    def test_the_procedure_is_monotone_in_the_p_values(self):
        rng = np.random.default_rng(41)
        w, G = A.row113_graph(E4, A.RATIOS)
        for _ in range(500):
            p = {n: float(v) for n, v in zip(w, rng.uniform(0, 0.08, len(w)))}
            smaller = {n: v * (float(rng.uniform(0, 1)) if rng.random() < 0.5 else 1.0) for n, v in p.items()}
            self.assertLessEqual(set(A.graph_test(w, G, p)[0]), set(A.graph_test(w, G, smaller)[0]))

    def test_a_dropped_engine_gives_the_direct_three_engine_graph(self):
        three = (B, M, H)
        w, G = A.row113_graph(three, A.RATIOS)
        for e in three:
            self.assertEqual(w[A.node(e, "1.5")], Fraction(1, 3))
        wd, Gd = direct_three_engine_graph(three)
        rng = np.random.default_rng(43)
        for _ in range(1000):
            p = {n: float(v) for n, v in zip(w, rng.uniform(0, 0.06, len(w)) ** rng.uniform(0.6, 2))}
            self.assertEqual(set(A.graph_test(w, G, p)[0]), set(A.graph_test(wd, Gd, p)[0]))
            qa, qd = A.graph_adjusted(w, G, p), A.graph_adjusted(wd, Gd, p)
            for n in w:
                self.assertAlmostEqual(qa[n], qd[n], places=12)
        order = [A.node(F, "1.5"), A.node(F, "0.5")]
        wf, Gf = A.row113_graph(E4, A.RATIOS)
        for o in (order, order[::-1]):                          # either removal order, one graph
            w2, G2 = wf, Gf
            for j in o:
                w2, G2 = A.remove_node(w2, G2, j)
            self.assertEqual((w2, G2), (w, G))

    def test_r15_alone_is_holm_across_the_engines(self):
        rng = np.random.default_rng(47)
        for engines in (E4, (B, M), (B,)):
            w, G = A.row113_graph(engines, ("1.5",))
            self.assertEqual(set(w), {A.node(e, "1.5") for e in engines})
            for _ in range(300):
                p = {n: float(v) for n, v in zip(w, rng.uniform(0, 0.06, len(w)))}
                h = A.holm(p)
                self.assertEqual(set(A.graph_test(w, G, p)[0]), {k for k, v in h.items() if v[1]})

    def test_the_rows_literal_words_depend_on_the_order_and_bretz_does_not(self):
        b15, m15, b05 = A.node(B, "1.5"), A.node(M, "1.5"), A.node(B, "0.5")
        first, second = [b15, m15, b05], [b15, b05, m15]
        lit1, lit2 = literal_rule(first), literal_rule(second)
        self.assertEqual((lit1[A.node(H, "1.5")], lit1[A.node(F, "1.5")], lit1[A.node(M, "0.5")]),
                         (Fraction(3, 8), Fraction(3, 8), Fraction(1, 4)))
        self.assertEqual((lit2[A.node(H, "1.5")], lit2[A.node(F, "1.5")], lit2[A.node(M, "0.5")]),
                         (Fraction(1, 3), Fraction(1, 3), Fraction(1, 3)))
        w, G = A.row113_graph(E4, A.RATIOS)
        br1, br2 = bretz_after(first, w, G), bretz_after(second, w, G)
        self.assertEqual(br1, br2)
        self.assertEqual(br1, lit2)
        # where the words and Bretz agree: an r = 0.5 test that rejects before any other r = 1.5 test
        self.assertEqual(bretz_after([b15, b05], w, G), literal_rule([b15, b05]))

    def test_where_the_rows_words_and_bretz_agree(self):
        """The docstring's condition, on 3000 SYNTHETIC rejection orders of four engines, each step taking
        a node that holds weight: the words and Bretz's update give the same weights while, at every
        r = 0.5 rejection, no r = 1.5 test is left or no other engine stands with its r = 1.5 test
        rejected and its r = 0.5 test not; at the first rejection that breaks it they differ."""
        rng = np.random.default_rng(107)
        w0, G0 = A.row113_graph(E4, A.RATIOS)
        seen = {"agree": 0, "differ": 0}
        for _ in range(3000):
            w, G, done = dict(w0), dict(G0), []
            while True:
                live = [j for j in w if w[j] > 0]
                if not live:
                    break
                j = live[int(rng.integers(len(live)))]
                holds = True
                if j.endswith("0.5"):
                    r15_left = any(n.endswith("1.5") for n in w)
                    stranded = any(n.endswith("0.5") and n != j and A.node(n.split("@r")[0], "1.5") not in w for n in w)
                    holds = not (r15_left and stranded)
                w, G = A.remove_node(w, G, j)
                done.append(j)
                if holds:
                    self.assertEqual(w, literal_rule(done), done)
                    seen["agree"] += 1
                else:
                    self.assertNotEqual(w, literal_rule(done), done)
                    seen["differ"] += 1
                    break
        self.assertGreater(seen["agree"], 1000)
        self.assertGreater(seen["differ"], 100)


# ------------------------------------------------------------------------------------------ Limited
class Limited(Guarded):
    def test_a_d_verdict_the_band_can_move_reads_model_limited(self):
        # two engines at r = 1.5: each test starts at 0.025. The B58's d (mean 2.0, sd 2.5, n 10) has
        # t p 0.0164: rejected; moved by -1.0 its p is 0.124, so the verdict is MODEL-LIMITED.
        rng = np.random.default_rng(53)
        z = rng.standard_normal(10)
        xb = 2.0 + 2.5 * (z - z.mean()) / z.std(ddof=1)
        z = rng.standard_normal(10)
        xm = 0.0 + 2.5 * (z - z.mean()) / z.std(ddof=1)
        blind = list(30.0 + rng.standard_normal(10))
        cuts = {B: (blind, {"1.5": list(np.array(blind) + xb)}), M: (blind, {"1.5": list(np.array(blind) + xm)})}
        doc = scores_from_cuts(cuts)
        p = stats.ttest_1samp(xb, 0, alternative="greater").pvalue
        self.assertLess(p, 0.025)
        self.assertGreater(stats.ttest_1samp(xb - 1.0, 0, alternative="greater").pvalue, 0.05)
        for band, limited in ((1.0, True), (0.0, False)):
            ctx = synthetic_context(engines=(B, M), ratios=("1.5",), n=10, band=band)
            row = A.analyse(doc, ctx)["readings"]["no_knock"]["d"][A.node(B, "1.5")]
            self.assertTrue(row["t"]["d_gt_0"])
            self.assertAlmostEqual(row["t"]["p"], float(p), places=10)
            self.assertEqual(row["t"]["model_limited"], limited)
            self.assertEqual(row["t"]["at_minus_band"], not limited)

    def test_an_equivalence_only_the_band_refuses_reads_model_limited(self):
        rng = np.random.default_rng(59)
        blind = list(30.0 + rng.standard_normal(20))
        xs = {e: 6.0 + 0.8 * rng.standard_normal(20) for e in (B, M)}
        cuts = {e: (blind, {"1.5": list(np.array(blind) + xs[e])}) for e in (B, M)}
        doc = scores_from_cuts(cuts)
        eq0 = A.equivalence(xs[B], xs[M], 0.0)
        self.assertTrue(eq0["equivalent"])
        b = A.MEI - max(abs(v) for v in eq0["ci90"]) + 0.2                 # just wider than the room left
        band = b / math.sqrt(2)
        res = A.analyse(doc, synthetic_context(engines=(B, M), ratios=("1.5",), band=band))
        pr = res["readings"]["no_knock"]["pairs"][f"{B}|{M}@r1.5"]
        self.assertAlmostEqual(pr["equivalence"]["band"], b, places=12)
        self.assertFalse(pr["equivalence"]["equivalent"])
        self.assertTrue(pr["equivalence"]["equivalent_without_band"])
        self.assertTrue(pr["equivalence"]["model_limited"])
        self.assertFalse(res["readings"]["no_knock"]["collapse"]["1.5"]["claimed"])
        self.assertTrue(res["readings"]["no_knock"]["collapse"]["1.5"]["model_limited"])


    def test_the_pair_rule_is_the_band_withholding_a_verdict_F3(self):
        """Finding S3/F3 of the review of 31 October 2026, pinned. (a) The widened interval is inside
        +-MEI exactly when the seed interval is at every shift of d_i - d_j within +-B (the two ends
        suffice); (b) so a verdict reached with B is reached without it, and MODEL-LIMITED is "reached
        by the seed interval alone, withheld by the band"; (c) the review's case, 20 seeds a side, means
        4 and 0, sd 4, B 2: neither interval reaches equivalence, so it is NOT MODEL-LIMITED, although a
        shift of -1 within +-B would reach it with the seed interval alone (the one-sided design)."""
        rng = np.random.default_rng(61)
        for _ in range(400):
            n = int(rng.integers(5, 25))
            x = rng.normal(rng.uniform(-6, 6), rng.uniform(0.5, 6), n)
            y = rng.normal(rng.uniform(-6, 6), rng.uniform(0.5, 6), n)
            b = float(rng.uniform(0.0, 3.0))
            wide = A.equivalence(x, y, b)["equivalent"]
            ends = [A.equivalence(x + s, y, 0.0)["equivalent"] for s in (-b, b)]
            self.assertEqual(wide, all(ends))
            if wide:
                self.assertTrue(A.equivalence(x, y, 0.0)["equivalent"])

        def standard(mean, n=20):
            z = rng.standard_normal(n)
            return mean + 4.0 * (z - z.mean()) / z.std(ddof=1)
        xb, xm = standard(4.0), standard(0.0)
        self.assertFalse(A.equivalence(xb, xm, 2.0)["equivalent"])
        self.assertFalse(A.equivalence(xb, xm, 0.0)["equivalent"])
        self.assertTrue(A.equivalence(xb - 1.0, xm, 0.0)["equivalent"])
        blind = list(30.0 + rng.standard_normal(20))
        cuts = {e: (blind, {"1.5": list(np.array(blind) + x)}) for e, x in ((B, xb), (M, xm))}
        res = A.analyse(scores_from_cuts(cuts), synthetic_context(engines=(B, M), ratios=("1.5",),
                                                                  band=2.0 / math.sqrt(2)))
        eq = res["readings"]["no_knock"]["pairs"][f"{B}|{M}@r1.5"]["equivalence"]
        self.assertAlmostEqual(eq["band"], 2.0, places=12)
        self.assertEqual((eq["equivalent"], eq["equivalent_without_band"], eq["model_limited"]),
                         (False, False, False))


# ------------------------------------------------------------------------------------------ Collapse
class Collapse(Guarded):
    def test_synthetic_collapse_claimed_with_the_ford(self):
        doc = synthetic_scores(61, {(e, r): 8.0 for e in E4 for r in A.RATIOS}, sd=1.0, blind_sd=1.0)
        res = A.analyse(doc, synthetic_context(band=0.5))
        P = res["readings"]["no_knock"]
        self.assertTrue(all(P["collapse"][r]["claimed"] for r in A.RATIOS))
        self.assertTrue(P["one_curve"]["claimed"])
        self.assertEqual(P["one_curve"]["status"], "confirmatory")
        text = A.report(res)
        self.assertIn("COLLAPSE at r = 1.5: a collapse on H/tau", text)
        self.assertIn("ONE CURVE: claimed", text)
        self.assertIn("[with knock: not converged in dt on these roads; decides nothing]", text)

    def test_synthetic_no_effect_on_one_engine_is_not_a_collapse(self):
        d = {(e, r): 8.0 for e in E4 for r in A.RATIOS}
        d[(M, "1.5")] = 0.0
        doc = synthetic_scores(67, d, sd=1.0, blind_sd=1.0)
        res = A.analyse(doc, synthetic_context(band=0.5, ceiling=3.0))
        P = res["readings"]["no_knock"]
        self.assertFalse(P["d"][A.node(M, "1.5")]["t"]["d_gt_0"])
        self.assertFalse(P["collapse"]["1.5"]["claimed"])
        self.assertFalse(P["one_curve"]["claimed"])
        for pr in P["pairs"].values():
            if M in pr["engines"] and pr["ratio"] == "1.5":
                self.assertFalse(pr["counts"])
        self.assertIn(A.CEILING_SENTENCE, A.report(res))

    def test_synthetic_equivalent_without_an_effect_reads_not_a_collapse(self):
        doc = synthetic_scores(71, {}, sd=1.0, blind_sd=1.0)          # every true d is 0
        res = A.analyse(doc, synthetic_context(band=0.5))
        P = res["readings"]["no_knock"]
        some = [k for k, pr in P["pairs"].items() if pr["equivalence"]["equivalent"] and not pr["counts"]]
        self.assertTrue(some)
        self.assertIn("equivalent with no effect established: not a collapse", A.report(res))
        self.assertFalse(any(c["claimed"] for c in P["collapse"].values()))

    def test_synthetic_without_the_ford_the_tau_wording(self):
        three = (B, M, H)
        doc = synthetic_scores(73, {(e, r): 8.0 for e in three for r in A.RATIOS}, engines=three, sd=1.0, blind_sd=1.0)
        res = A.analyse(doc, synthetic_context(engines=three, band=0.5))
        text = A.report(res)
        self.assertIn(f"COLLAPSE at r = 1.5: {A.TAU_NOTE}", text)
        self.assertNotIn("a collapse on H/tau", text)

    def test_synthetic_one_ratio_and_one_engine(self):
        doc = synthetic_scores(79, {(e, "1.5"): 8.0 for e in E4}, ratios=("1.5",), sd=1.0, blind_sd=1.0)
        res = A.analyse(doc, synthetic_context(ratios=("1.5",), band=0.5))
        self.assertIsNone(res["readings"]["no_knock"]["one_curve"]["claimed"])
        self.assertTrue(res["readings"]["no_knock"]["collapse"]["1.5"]["claimed"])
        self.assertIn("ONE CURVE: not computed", A.report(res))
        self.assertEqual(set(res["graph"]["weights"]), {A.node(e, "1.5") for e in E4})
        one = synthetic_scores(83, {(B, r): 8.0 for r in A.RATIOS}, engines=(B,), sd=1.0)
        res = A.analyse(one, synthetic_context(engines=(B,)))
        self.assertFalse(res["four_engine_test_runs"])
        self.assertEqual(res["status"], {B: "exploratory"})
        self.assertEqual(res["readings"]["no_knock"]["pairs"], {})
        self.assertIsNone(res["readings"]["no_knock"]["collapse"]["1.5"]["claimed"])
        self.assertIn("the four-engine test does not run (row 107 (2))", A.report(res))

    def test_synthetic_end_to_end_against_scipy(self):
        d = {(B, "1.5"): 6.0, (B, "0.5"): 2.0, (M, "1.5"): 3.0, (M, "0.5"): 0.5, (H, "1.5"): 5.0,
             (H, "0.5"): 1.5, (F, "1.5"): 1.0, (F, "0.5"): 0.0}
        doc = synthetic_scores(89, d, sd=4.0, ties=2)
        ctx = synthetic_context(band=1.2)
        ctx["model_band"][F]["0.5"]["with_knock"] = 2.5
        res = A.analyse(doc, ctx)
        for reading in A.READINGS:
            R = res["readings"][reading]
            xs = {}
            for e in E4:
                for r in A.RATIOS:
                    sig = [scipy_cut(doc["engines"][e]["arms"][A.arm_name(r)]["seeds"][str(s)][reading]["D"],
                                     doc["engines"][e]["arms"][A.arm_name(r)]["seeds"][str(s)][reading]["D_base"])
                           for s in range(20)]
                    bl = [scipy_cut(doc["engines"][e]["arms"]["blind"]["seeds"][str(s)][reading]["D"],
                                    doc["engines"][e]["arms"]["blind"]["seeds"][str(s)][reading]["D_base"])
                          for s in range(20)]
                    row = R["d"][A.node(e, r)]
                    x = np.array(sig) - np.array(bl)
                    xs[(e, r)] = x
                    self.assertEqual(sum(v == 0 for v in row["d_per_seed"]), 2)        # the tied seeds
                    self.assertAlmostEqual(row["t"]["p"], float(stats.ttest_rel(sig, bl, alternative="greater").pvalue), places=9)
                    pos, nz = int(np.sum(x > 1e-9)), int(np.sum(np.abs(x) > 1e-9))
                    self.assertEqual((row["sign"]["positive"], row["sign"]["nonzero"]), (pos, nz))
                    self.assertAlmostEqual(row["sign"]["p"], stats.binomtest(pos, nz, 0.5, alternative="greater").pvalue, places=12)
            ps = {A.node(e, r): R["d"][A.node(e, r)]["t"]["p"] for e in E4 for r in A.RATIOS}
            w, G = A.row113_graph(E4, A.RATIOS)
            self.assertEqual({n for n in ps if R["d"][n]["t"]["d_gt_0"]}, set(A.graph_test(w, G, ps)[0]))
            fam = {}
            for k, pr in R["pairs"].items():
                (i, j), r = pr["engines"], pr["ratio"]
                b = math.hypot(ctx["model_band"][i][r][reading], ctx["model_band"][j][r][reading])
                xi, xj = xs[(i, r)], xs[(j, r)]
                ci = stats.ttest_ind(xi, xj, equal_var=False).confidence_interval(0.90)
                self.assertAlmostEqual(pr["equivalence"]["ci90_widened"][0], float(ci.low) - b, places=8)
                self.assertEqual(pr["equivalence"]["equivalent"], float(ci.low) - b > -A.MEI and float(ci.high) + b < A.MEI)
                p_up = stats.ttest_ind(xi - b, xj, equal_var=False, alternative="greater").pvalue
                p_dn = stats.ttest_ind(xi + b, xj, equal_var=False, alternative="less").pvalue
                fam[k] = min(1.0, 2 * min(float(p_up), float(p_dn)))
                self.assertAlmostEqual(pr["difference"]["p"], fam[k], places=9)
                self.assertEqual(pr["counts"], R["d"][A.node(i, r)]["t"]["d_gt_0"] and R["d"][A.node(j, r)]["t"]["d_gt_0"])
            m = len(fam)
            self.assertEqual(m, 12)
            order = sorted(fam, key=fam.get)
            running = 0.0
            for idx, k in enumerate(order):                     # Holm by hand
                running = max(running, min(1.0, (m - idx) * fam[k]))
                self.assertAlmostEqual(R["pairs"][k]["difference"]["holm_p"], running, places=9)
        self.assertEqual(res["readings"]["no_knock"]["role"], "primary")
        self.assertIn(A.WITH_KNOCK_LABEL, res["readings"]["with_knock"]["role"])


# ------------------------------------------------------------------------------------------ CLI
class CLI(Guarded):
    def test_synthetic_files_out_report_overwrite_and_sensitivity(self):
        d = {(e, r): 8.0 for e in E4 for r in A.RATIOS}
        doc = synthetic_scores(97, d, sd=1.0, blind_sd=1.0)
        flipped = json.loads(json.dumps(doc))
        flipped["variant"] = "(g) KI 1.10 SYNTHETIC"
        for s in flipped["engines"][M]["arms"]["sighted_r1.5"]["seeds"].values():   # Mazda r1.5 loses its effect
            s["no_knock"]["D"] = [v * 1.13 for v in s["no_knock"]["D"]]
        with tempfile.TemporaryDirectory(prefix="analyse4_synthetic_") as tmp:
            paths = {}
            for name, obj in (("scores", doc), ("context", synthetic_context(band=0.5)), ("variant", flipped)):
                paths[name] = os.path.join(tmp, f"{name}.json")
                with open(paths[name], "w", encoding="utf-8") as fh:
                    json.dump(obj, fh)
            out, rep = os.path.join(tmp, "result.json"), os.path.join(tmp, "report.txt")
            argv = ["--scores", paths["scores"], "--context", paths["context"], "--out", out, "--report", rep,
                    "--sensitivity", f"(g) KI 1.10 SYNTHETIC={paths['variant']}"]
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(A.main(argv), 0)
            with open(out, encoding="utf-8") as fh:
                res = json.load(fh)
            self.assertEqual(res["schema"], A.RESULT_SCHEMA)
            self.assertEqual(res["sources"]["scores"]["sha256"], A._sha(paths["scores"]))
            flips = res["sensitivity"]["(g) KI 1.10 SYNTHETIC"]["flips"]
            self.assertIn(f"sensitive to (g) KI 1.10 SYNTHETIC: no_knock d>0 (t) {A.node(M, '1.5')}: True -> False", flips)
            self.assertIn("sensitive to (g) KI 1.10 SYNTHETIC: no_knock collapse @r1.5: True -> False", flips)
            self.assertFalse(any(" with_knock " in f for f in flips))
            with open(rep, encoding="utf-8") as fh:
                self.assertIn("SENSITIVITY (row 115", fh.read())
            with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
                A.main(argv)                                    # refused without --overwrite
            with redirect_stdout(io.StringIO()):
                self.assertEqual(A.main(argv + ["--overwrite"]), 0)
            with redirect_stdout(io.StringIO()), self.assertRaisesRegex(SystemExit, "REFUSED: .*variant null"):
                A.main(["--scores", paths["variant"], "--context", paths["context"]])
            with redirect_stdout(io.StringIO()), self.assertRaisesRegex(SystemExit, "REFUSED: .*the command line says"):
                A.main(["--scores", paths["scores"], "--context", paths["context"],
                        "--sensitivity", f"another label={paths['variant']}"])


# ------------------------------------------------------------------------------------------ Power
class Power(Guarded):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with open(POWER_TXT, encoding="utf-8") as fh:
            cls.txt = fh.read()

    def test_row_113_6(self):
        r6 = A.ROW_113_6
        fn8 = [1 - A.power_t(3.20, s, 20, 0.05 / 8) for s in r6["spreads"]]
        fn1 = [1 - A.power_t(3.20, s, 20, 0.05) for s in r6["spreads"]]
        self.assertEqual(round(fn8[0], 2), 0.97)                # X2's spread: reproduced
        self.assertEqual(round(fn8[1], 2), 0.98)                # X1's: 0.975, not the row's 0.97
        self.assertEqual((round(fn1[0], 2), round(fn1[1], 2)), (0.83, 0.86))
        text, fn = A.power_report()
        self.assertEqual(fn["alpha/8"], fn8)
        self.assertIn("0.98 at two decimals (NOT reproduced)", text)

    def test_the_reviews_power_txt_to_its_printed_digit(self):
        pat = re.compile(r"sigma +(?:X\d )?([\d.]+): power ([\d.]+) \(alpha/8\) / ([\d.]+) \(alpha\)")
        rows = pat.findall(self.txt)
        self.assertEqual(len(rows), 4)
        for s, p8, p1 in rows:
            self.assertEqual(f"{A.power_t(3.20, float(s), 20, 0.05 / 8):.3f}", p8)
            self.assertEqual(f"{A.power_t(3.20, float(s), 20, 0.05):.3f}", p1)
        ceil = {"b58": 5.96, "mazda": 3.40, "honda": 5.42, "ford": 2.50}
        block = re.compile(r"(b58|mazda|honda|ford) r1\.5 ([\d.]+)/([\d.]+)")
        sig_lines = [ln for ln in self.txt.splitlines() if ln.strip().startswith("sigma") and "r1.5" in ln]
        self.assertEqual(len(sig_lines), 4)
        for ln in sig_lines:
            s = float(re.search(r"sigma +(?:X\d )?([\d.]+):", ln).group(1))
            for e, p8, p1 in block.findall(ln):
                self.assertEqual(f"{A.power_t(ceil[e], s, 20, 0.05 / 8):.3f}", p8, (s, e))
                self.assertEqual(f"{A.power_t(ceil[e], s, 20, 0.05):.3f}", p1, (s, e))
        for e, c, s in re.findall(r"(b58|mazda|honda|ford) +r1\.5 ceiling ([\d.]+): sigma <= ([\d.]+)", self.txt):
            self.assertAlmostEqual(A.s_star(float(c), 20, 0.05 / 8), float(s), delta=0.006)
        self.assertEqual([round(A.s_star(v, 20, 0.05 / 8), 2) for v in A.PLANNING_C15.values()],
                         [7.32, 4.17, 6.65, 3.07])              # row 103 (4)'s 7.3, 4.2, 6.7 and 3.1

    def test_a_monte_carlo_of_the_t_test(self):
        rng = np.random.default_rng(101)
        reps, n = 200_000, 20
        for d, s, lvl in ((3.20, 20.51, 0.05), (3.20, 24.78, 0.05 / 8), (5.96, 7.32, 0.05 / 8)):
            x = d + s * rng.standard_normal((reps, n))
            t = x.mean(1) / (x.std(1, ddof=1) / math.sqrt(n))
            rate = float(np.mean(t > stats.t.ppf(1 - lvl, n - 1)))
            pw = A.power_t(d, s, n, lvl)
            self.assertLess(abs(rate - pw), 4 * math.sqrt(pw * (1 - pw) / reps), (d, s, lvl, rate, pw))

    def test_the_pilot_factor(self):
        self.assertEqual(round(A.pilot_factor(), 2), 1.56)
        self.assertAlmostEqual(A.pilot_factor() ** 2 * stats.chi2.ppf(0.20, 4), 4.0, places=12)


# ------------------------------------------------------------------------------------------ Hygiene
# ORDER's frozen files that roads.json does not hash (docs/build_step_2/ORDER_TO_TRAINING.md, its rule over
# every step); the hashed ones are read from epa_roads.hashed_files, their one definition (the review of 31
# October 2026, R0-5: this list was a second, typed copy of it)
ORDER_FROZEN_BEYOND_ROADS = ("epa_map.py", "calibrate_epa.py", "validate_epa.py", "d3_rows.py")


def hashed_and_frozen():
    import epa_roads as ER
    files = [f for f in ER.hashed_files(root=HERE, engines=ER.ENGINES) if f.endswith(".py")]
    return sorted(set(files) | set(ORDER_FROZEN_BEYOND_ROADS))


class Hygiene(Guarded):
    def test_the_script_imports_no_plant_or_epa_module(self):
        with open(A.__file__, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        mods = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom):
                mods.add(n.module.split(".")[0])
        self.assertEqual(mods, {"argparse", "hashlib", "itertools", "json", "math", "os", "sys", "fractions",
                                "numpy", "scipy", "analyse_phase_d"})

    def test_no_hashed_or_frozen_file_names_it(self):
        files = hashed_and_frozen()
        self.assertGreater(len(files), 25)
        for rel in files:
            with open(os.path.join(HERE, rel), encoding="utf-8") as fh:
                self.assertNotIn("four_engine_analysis", fh.read(), rel)

    def test_its_engine_ids_are_engines_plants(self):
        import engines
        self.assertEqual(A.ENGINE_IDS, tuple(engines.PLANTS))


if __name__ == "__main__":
    unittest.main(verbosity=2)

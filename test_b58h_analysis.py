"""test_b58h_analysis.py -- b58h_analysis.py (AB): the context and analyse commands, the band under every reading,
the intervals, Delta, section 9.1, section 7's sentences, section 10's beside values and the report, each against an
independent computation, and each with a named wrong implementation shown to give another number or a refusal
(mistake 12).

    python -B -m unittest test_b58h_analysis -v

PR-B section 6.0 (results/PREREGISTRATION_B58H.md:499-500): "its own tests, each computation with a control that
fails". Every score here is SYNTHETIC, made by this file or by test_four_engine_analysis's helpers with a fixed NumPy
seed; every record the commands read (roads.json, the tightenings, summary.json, the backend record, X1's and X2's
result files, reverify.json) is a SYNTHETIC copy in a temporary git repository, so no number of the study is read
here. No agent is loaded: every test runs with evaluate.load_agent and evaluate.read_agents patched to raise, inside
an audit hook that refuses any open or listing under runs/b58h_dt1 and runs/b58h_check_dt1 (and the study's other
never-opened files), and inside test_epa_fixtures.forbid_real_data.

The independent computations: statistics.median and statistics.mean over the raw road lists (the cuts, d, Delta, the
band's median cuts), scipy.stats.ttest_1samp's confidence_interval (each interval), scipy.stats.binomtest (the
two-sided sign test), the band's parts written out from PR-B 6.5's table with MEI and N_SHARES typed here, a
one-engine graph written out from PR-B 6.2's words with scipy's one-sided t-test (the corners), and loops over the
delivery block's lists (section 9.1). The named wrong implementations: ddof 0; the mean form for evaluate.py's;
signed d in the band; "b itself" for the primary; phi at the mean cut, or at the smaller arm's; kappa_E8 at 1; the
one-sided or uncapped sign test; the rounded ceiling's s*; a pooled-ratio fuel figure; a mean short share that counts
roads without demand; a loop over the roads that stops one road short; a raw sha256 recorded as a sha_text (a CRLF
checkout); a sentence that takes its d, interval, adjusted p, flag, r = 0.5 rule or below-0 test from the wrong
reading, form or run (readings_doc separates them, where scores_from_cuts makes them equal); a sign test's words
without the other reading's flag; a defect check that skips a band; a context check that skips the status basis or
the inputs; a write that precedes the refusal of an existing output. Section7Lines writes every line of section 7
out from PR-B's rules (want_text) on ten documents, each making one word of the code's choice visible: a bracket or
sign words whose flag, 'wholly below 0', adjusted p or verdict comes from the wrong test, reading, form or run; an
unadjusted p printed as the graph's; zeros counted as nonzero; a companion line with another run's flag, or none for
a with-knock or sign verdict, or the 'no verdict' line beside a named one; r = 0.5 first; the 'not shown at r = 0.5'
head without its flag. Beside it: a context with a key missing, an extra key or a list of another length; a JSON
written before the report can be created; a delivery rule that is text, or a share 1e-6 off; the band block at 2
decimals; Delta's p at a fixed 4 decimals; a with-knock ceiling that is not a finite number. WriteAll drives each of
the writer's refusals (a folder, an existing file, an open, a write that fails on a full disk) with open() replaced
inside AB alone, and checks that none leaves a file the call opened, one written in full among them.
"""
import ast
import contextlib
import copy
import errno
import hashlib
import io
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import analyse_phase_d as APD  # noqa: E402
import b58h_analysis as AB  # noqa: E402
import evaluate as V  # noqa: E402
import four_engine_analysis as FEA  # noqa: E402
import test_four_engine_analysis as T4  # noqa: E402  synthetic_scores, scores_from_cuts, scipy_cut
from test_epa_fixtures import Guarded  # noqa: E402
from thresholds import common as TC  # noqa: E402

N = AB.EB.B58H_N
B = AB.ENGINE
R_LO, R_HI = FEA.RATIOS
HAND_MEI, HAND_SHARES = 5.43, 6          # PR-B 6.5 and MD:232, typed here as the independent values
SYN = {"kappa_e8": 2.75, "kappa_l1": {"mazda_25t": 1.625, "honda_l15b7": 1.875, "ford_27tt": 3.625},
       "ceiling": {R_LO: 1.5 + 1.0 / 3.0, R_HI: 4.5 + 1.0 / 7.0},
       "ceiling_knock": {R_LO: 1.25 + 1.0 / 19.0, R_HI: 3.75 + 1.0 / 23.0},
       "c_u": {R_LO: {"noknock": (-0.25 + 1.0 / 9.0, -0.75 + 1.0 / 11.0), "knock": (-0.125, -0.625)},
               R_HI: {"noknock": (3.0 + 1.0 / 13.0, 2.5 + 1.0 / 17.0), "knock": (2.875, 2.375)}},
       "x2": (16.5, 17.25), "x1": (21.5, 22.5),
       "plants": ("aaaa1111bbbb2222", "cccc3333dddd4444")}
GIT_ENV = {"GIT_AUTHOR_NAME": "ab test", "GIT_AUTHOR_EMAIL": "ab@example.invalid",
           "GIT_COMMITTER_NAME": "ab test", "GIT_COMMITTER_EMAIL": "ab@example.invalid",
           "GIT_AUTHOR_DATE": "2026-11-19T12:00:00+03:00", "GIT_COMMITTER_DATE": "2026-11-19T12:00:00+03:00"}


# ------------------------------------------------------------------------------------------ the no-agent guard
def _n(p):
    return os.path.normcase(os.path.abspath(p))


_STUDY_DIRS = tuple(_n(os.path.join(HERE, "runs", d)) for d in ("b58h_dt1", "b58h_check_dt1"))
_NEVER_DIRS = (_n(os.path.join(HERE, "logs", "epa")),)
_NEVER_FILES = {_n(os.path.join(HERE, "results", "EPA_ROADS", "attempt_1_printed.txt"))}
_GUARD = {"on": 0, "hits": [], "installed": False}


def refused_path(path):
    """A path no AB code or test may open or list: the study's run folders, and the files PR-B's readers never
    open (the first attempt's print, logs/epa, the EPA tables, the row 96 integers)."""
    p = _n(path)
    base = os.path.basename(p)
    if p in _NEVER_FILES or base.startswith("grad_row96_integers"):
        return True
    if any(p == d or p.startswith(d + os.sep) for d in _STUDY_DIRS + _NEVER_DIRS):
        return True
    return base.startswith("epa_") and base.endswith(".csv") and (os.sep + "engines" + os.sep) in p


def _audit(event, args):
    if not _GUARD["on"] or event not in ("open", "os.listdir", "os.scandir") or not args:
        return
    path = args[0]
    if isinstance(path, bytes):
        path = os.fsdecode(path)
    if not isinstance(path, (str, os.PathLike)):
        return
    if refused_path(os.fspath(path)):
        _GUARD["hits"].append(os.fspath(path))
        raise PermissionError(f"test_b58h_analysis: a test reached {os.path.basename(os.fspath(path))}, refused")


@contextlib.contextmanager
def forbid_study():
    """While inside: evaluate.load_agent and read_agents raise, and an open or listing under the study's run
    folders raises PermissionError before the operating system sees it; leaving fails on any such attempt."""
    if not _GUARD["installed"]:
        sys.addaudithook(_audit)
        _GUARD["installed"] = True
    _GUARD["on"] += 1
    start = len(_GUARD["hits"])
    try:
        with mock.patch.object(V, "load_agent", side_effect=AssertionError("AB's code loaded an agent")), \
                mock.patch.object(V, "read_agents", side_effect=AssertionError("AB's code read the agents")):
            yield
    finally:
        _GUARD["on"] -= 1
        hits = _GUARD["hits"][start:]
        del _GUARD["hits"][start:]
    if hits:
        raise AssertionError("forbid_study: refused path(s) reached: " + ", ".join(sorted(set(hits))))


class Case(Guarded):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.enterClassContext(forbid_study())

    def setUp(self):
        super().setUp()
        self.enterContext(forbid_study())


# ------------------------------------------------------------------------------------------ SYNTHETIC records
def write(root, rel, text, *, newline="\n"):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline=newline) as fh:
        fh.write(text)
    return p


def to_crlf(path):
    """Rewrite an LF file with CRLF line ends, as a core.autocrlf checkout writes it."""
    with open(path, "rb") as fh:
        raw = fh.read()
    assert b"\r\n" not in raw, path
    with open(path, "wb") as fh:
        fh.write(raw.replace(b"\n", b"\r\n"))


def x2_text(sd_knock, sd_noknock, n=5, section=AB.X2_SP_SECTION + " (no knock term; the second reading)"):
    """X2_RESULT.txt's layout, SYNTHETIC numbers: the with-knock spread on line 11, the no-knock one on line 24."""
    L = ["X2 ANALYSIS -- SYNTHETIC", "rule: SYNTHETIC", "", "TOTAL DAMAGE (primary)",
         "  seed   sighted cut   blinded cut   difference"]
    L += [f"     {s}         50.00         50.00        +0.00" for s in range(5)]
    L += [f"  n {n} (non-zero)   positive 1   mean -1.00   sd {sd_knock} points"]
    L += ["  preview helps:        SYNTHETIC"] * 4 + ["", section, "  seed   sighted cut   blinded cut   difference"]
    L += [f"     {s}         50.00         50.00        +0.00" for s in range(5)]
    L += [f"  n {n} (non-zero)   positive 1   mean -1.00   sd {sd_noknock} points"]
    L += ["  preview helps:        SYNTHETIC"] * 4 + [""]
    assert L[10].startswith("  n ") and L[23].startswith("  n ") and L[16] == section
    return "\n".join(L) + "\n"


def x1_text(sd_knock, sd_noknock):
    """X1_RESULT.txt's layout: the TOTAL DAMAGE spread on line 29, the THERMAL-ONLY one on line 60."""
    L = ["X1 ANALYSIS -- SYNTHETIC", "rule: SYNTHETIC", "", "TOTAL DAMAGE (primary)"]
    L += ["  seed row, SYNTHETIC"] * 24
    L += [f"  n 23 (non-zero)   positive 10   mean -1.00   sd {sd_knock} points"]
    L += ["  test line, SYNTHETIC"] * 4 + ["", "THERMAL-ONLY DAMAGE (no knock term; the second reading)"]
    L += ["  seed row, SYNTHETIC"] * 24
    L += [f"  n 23 (non-zero)   positive 10   mean -1.00   sd {sd_noknock} points", ""]
    assert L[28].startswith("  n ") and L[59].startswith("  n ") and L[34].startswith("THERMAL")
    return "\n".join(L) + "\n"


def write_records(root, **over):
    v = dict(copy.deepcopy(SYN), **over)
    by = {r: {"C": v["ceiling"][r],
              "C_u": {rd: {"evaluate_form": v["c_u"][r][rd][0], "mean": v["c_u"][r][rd][1], "median": 0.0}
                      for rd in ("noknock", "knock")}} for r in FEA.RATIOS}
    if v["ceiling_knock"] is not None:            # roads_ceiling's own form: C = a.noknock.mean (G11)
        for r in FEA.RATIOS:
            by[r]["a"] = {"noknock": {"mean": v["ceiling"][r]}, "knock": {"mean": v["ceiling_knock"][r]}}
    roads = {"schema": "SYNTHETIC", "ceilings": {"readings": list(over.get("readings", ["noknock", "knock"])),
                                                 "per_engine": {B: {"by": by}}}}
    write(root, AB.ROADS, json.dumps(roads, indent=1))
    write(root, AB.TIGHTENINGS, json.dumps({"E8": {"b58_u_val_kappa": {"with_roads": {"kappa": v["kappa_e8"]}}}}))
    write(root, AB.SUMMARY, json.dumps({"engines": {e: {"kappa": {"L1": k}} for e, k in v["kappa_l1"].items()}}))
    write(root, AB.BACKEND, json.dumps({"in_test": list(over.get("in_test", [B])), "n": None}))
    write(root, AB.X2_RESULT, over.get("x2_text") or x2_text(*v["x2"]))
    write(root, AB.X1_RESULT, x1_text(*v["x1"]))
    write(root, AB.REVERIFY, json.dumps({"plants": {B: {"plant_sha_now": v["plants"][0],
                                                       "plant_sha_at_draw": v["plants"][1]}}}))


def per_entry(fuel, demand, short):
    return {"fuel": [float(x) for x in fuel], "demand_steps": [int(x) for x in demand],
            "short_steps": [int(x) for x in short],
            "short_share": [(int(s) / int(d) if int(d) else None) for s, d in zip(short, demand)]}


def synthetic_delivery(rng_seed, *, no_demand=("blind", "7"), tie=("sighted_r1.5", "3", (2, 9)),
                       top_last=("blind", "0")):
    """evaluate.delivery_block's form, SYNTHETIC: every fourth road without a demand step; one seed with none at
    all; one seed whose largest short share is tied on two roads; and one seed whose last road holds its arm's
    largest short share (every other share of that arm is below 1)."""
    rng = np.random.default_rng(rng_seed)
    nr = FEA.N_ROADS
    base_fuel = 250.0 + 150.0 * rng.random(nr)

    def draw(scale):
        demand = rng.integers(5, 60, nr)
        demand[::4] = 0
        short = np.array([rng.integers(0, d) if d else 0 for d in demand])
        return per_entry(base_fuel * scale, demand, short)

    hand = {AB.BASELINE: draw(np.ones(nr)), "reactive": draw(1.0 + 0.01 * rng.random(nr)),
            AB.CURRENT_GRADE: draw(1.0 + 0.02 * rng.random(nr))}
    arms = {arm: {str(s): draw(1.0 + 0.05 * rng.standard_normal(nr)) for s in range(N)} for arm in AB.ARMS}
    arm, s = no_demand
    arms[arm][s] = per_entry(arms[arm][s]["fuel"], [0] * nr, [0] * nr)
    arm, s, (k1, k2) = tie
    e = arms[arm][s]
    demand, short = list(e["demand_steps"]), list(e["short_steps"])
    demand[k1] = demand[k2] = 10
    short[k1] = short[k2] = 10
    arms[arm][s] = per_entry(e["fuel"], demand, short)
    arm, s = top_last
    e = arms[arm][s]
    demand, short = list(e["demand_steps"]), list(e["short_steps"])
    demand[-1] = short[-1] = 10
    arms[arm][s] = per_entry(e["fuel"], demand, short)
    rule ={"demand_step": "SYNTHETIC demand rule", "short_step": "SYNTHETIC short rule", "fuel": "SYNTHETIC grams"}
    return {"rule": rule, "hand": hand, "arms": arms}


def study_doc(root, *, rng_seed=7, d=(3.0, 5.0), sd=1.5, delivery=None, **kw):
    """A SYNTHETIC scores document of the study's shape, its provenance as the d34 route writes it."""
    doc = T4.synthetic_scores(rng_seed, {(B, R_LO): d[0], (B, R_HI): d[1]}, engines=(B,), n=N, sd=sd, **kw)
    return with_provenance(doc, root, delivery)


def with_provenance(doc, root, delivery=None):
    doc["provenance"] = {"protocol": V.DECISION_34, "reading": V.REDRAW_READING, "reward_knock": False,
                         "roads_sha": TC.sha_text(os.path.join(root, *AB.ROADS.split("/"))),
                         "delivery": synthetic_delivery(11) if delivery is None else delivery}
    return doc


def cuts_doc(root, blind, sighted):
    """A SYNTHETIC study document whose cuts are exactly the given ones (test_four_engine_analysis.scores_from_cuts:
    each road the same scale of one base, so both forms equal the cut), both readings identical."""
    doc = T4.scores_from_cuts({B: (blind, sighted)}, ratios=FEA.RATIOS)
    doc["variant"] = None
    return with_provenance(doc, root)


def readings_doc(root, cuts, *, top=(0.0, 0.5), seed=31):
    """A SYNTHETIC study document whose two readings carry their own cuts: cuts[reading] = (blind list, {r: sighted
    list}), each seed's cut exactly the given one in evaluate.py's form (every road one scale of the reading's own
    base). The last road of every sighted seed carries a further factor 1 + e, e uniform in `top`: that road stays
    the largest, so the median and evaluate.py's form do not move, while the mean form moves by -(100 - c) e / 20.
    So the readings differ, and the two forms differ (scores_from_cuts makes both equal)."""
    rng = np.random.default_rng(seed)
    nr = FEA.N_ROADS
    bases = {"no_knock": np.linspace(90.0, 150.0, nr), "with_knock": np.linspace(110.0, 190.0, nr)}
    arms = {"blind": {"seeds": {}}, **{FEA.arm_name(r): {"seeds": {}} for r in FEA.RATIOS}}
    for rd in FEA.READINGS:
        blind, sighted = cuts[rd]
        for arm, cl in [("blind", blind)] + [(FEA.arm_name(r), sighted[r]) for r in FEA.RATIOS]:
            for s, c in enumerate(cl):
                D = bases[rd] * (1.0 - c / 100.0)
                if arm != "blind":
                    D[-1] *= 1.0 + rng.uniform(*top)
                arms[arm]["seeds"].setdefault(str(s), {})[rd] = {"D": D.tolist(), "D_base": bases[rd].tolist()}
    doc = {"schema": FEA.SCORES_SCHEMA, "ratios": list(FEA.RATIOS), "n_roads": nr, "variant": None,
           "engines": {B: {"arms": arms}}}
    return with_provenance(doc, root)


def two_readings(root, no_knock, with_knock, **kw):
    """readings_doc with a blind arm at 30 points in both readings; each reading's d given as (r = 1.5, r = 0.5)."""
    blind = [30.0] * N
    return readings_doc(root, {rd: (blind, {R_HI: [30.0 + v for v in d[0]], R_LO: [30.0 + v for v in d[1]]})
                               for rd, d in (("no_knock", no_knock), ("with_knock", with_knock))}, **kw)


SCORES_REL = "results/B58H_RESULT/scores_b58h.json"


def write_scores(root, doc, rel=SCORES_REL, newline="\n"):
    return write(root, rel, json.dumps(doc, indent=1) + "\n", newline=newline)


def git(root, *args):
    out = subprocess.run(["git", "-c", "core.safecrlf=false", *args], cwd=root, capture_output=True, text=True,
                         env=dict(os.environ, **GIT_ENV))
    if out.returncode != 0:
        raise RuntimeError(f"git {args}: {out.stderr}")
    return out.stdout.strip()


def make_repo(tmp, *, doc_kw=None, doc=None, name="repo", **records):
    """A temporary git work tree holding the SYNTHETIC records and scores, committed; core.autocrlf true, as on
    the laptop. Returns (root, scores path)."""
    root = os.path.join(tmp, name)
    os.makedirs(root)
    write_records(root, **records)
    d = doc(root) if callable(doc) else study_doc(root, **(doc_kw or {}))
    scores = write_scores(root, d)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "core.autocrlf", "true")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "SYNTHETIC records and scores")
    return root, scores


def copy_repo(root, tmp, name):
    dst = os.path.join(tmp, name)
    shutil.copytree(root, dst)
    return dst, os.path.join(dst, *SCORES_REL.split("/"))


def out_paths(root, tag=""):
    d = os.path.join(root, "results", "B58H_RESULT")
    return (os.path.join(d, f"context_b58h{tag}.json"), os.path.join(d, f"analysis_b58h{tag}.json"),
            os.path.join(d, f"analysis_b58h{tag}.txt"))


def run_both(root, scores, tag=""):
    ctx, out, rep = out_paths(root, tag)
    AB.context(scores, ctx, root=root)
    AB.analyse(scores, ctx, out, rep, root=root)
    return ctx, out, rep


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def read_text(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def checked_of(doc):
    return FEA.validate_scores(doc)


def fea_part(report_text, fea_text):
    """four_engine_analysis's verbatim report inside AB's, and AB's own text around it."""
    i = report_text.index(fea_text)
    return report_text[:i] + report_text[i + len(fea_text):]


def tmpdir(case):
    t = tempfile.TemporaryDirectory(prefix="ab_test_", ignore_cleanup_errors=True)
    case.addClassCleanup(t.cleanup) if isinstance(case, type) else case.addCleanup(t.cleanup)
    return t.name


class FullDisk:
    """A file handle whose write puts half its bytes on disk, then raises OSError 28, as a full disk leaves a file
    that was being written."""

    def __init__(self, fh):
        self.fh = fh

    def write(self, raw):
        self.fh.write(raw[:len(raw) // 2])
        self.fh.flush()
        raise OSError(errno.ENOSPC, "SYNTHETIC: no space left on device")

    def close(self):
        self.fh.close()

    @property
    def closed(self):
        return self.fh.closed

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def writer_open(*, full=(), refuse=None):
    """A stand-in for open() inside AB (mock.patch.object(AB, "open", ..., create=True)): each "x" open is logged in
    order as (path, handle); a file named in `full` gets a FullDisk handle; opening refuse[0] raises refuse[1] (its
    handle logged as None). Every other open is the real one. Returns (the stand-in, the log)."""
    real_open, log = open, []

    def fake(path, mode="r", *args, **kw):
        if "x" not in mode:
            return real_open(path, mode, *args, **kw)
        if refuse is not None and _n(path) == _n(refuse[0]):
            log.append((path, None))
            raise refuse[1]
        fh = real_open(path, mode, *args, **kw)
        if any(_n(path) == _n(p) for p in full):
            fh = FullDisk(fh)
        log.append((path, fh))
        return fh
    return fake, log


# ------------------------------------------------------------------------------------------ Shared helpers
class Shared(Case):
    def test_sha256_file_is_the_raw_bytes_and_sha_text_reads_crlf_as_lf(self):
        tmp = tmpdir(self)
        p = write(tmp, "x.json", "{\n \"a\": 1\n}\n", newline="\r\n")
        with open(p, "rb") as fh:
            raw = fh.read()
        self.assertEqual(AB.sha256_file(p), hashlib.sha256(raw).hexdigest())
        self.assertEqual(TC.sha_text(p), hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest())
        self.assertNotEqual(AB.sha256_file(p), TC.sha_text(p), "control: a CRLF file's raw sha256 is not its sha_text")

    def test_t_interval_is_scipys_and_ddof_0_is_not(self):
        x = np.random.default_rng(3).normal(1.0, 2.5, N)
        iv = AB.t_interval(x)
        ci = stats.ttest_1samp(x, 0.0).confidence_interval(0.95)
        self.assertAlmostEqual(iv["lo"], ci.low, places=12)
        self.assertAlmostEqual(iv["hi"], ci.high, places=12)
        self.assertEqual((iv["n"], f"{iv['t']:.4f}"), (N, "2.0930"))       # PR-B 6.3's t, as power_b58.txt prints it
        self.assertAlmostEqual(iv["sd"], statistics.stdev(x), places=12)
        wrong = iv["mean"] - iv["t"] * float(np.std(x, ddof=0)) / math.sqrt(N)
        self.assertGreater(abs(wrong - iv["lo"]), 1e-3, "control: ddof 0 gives another interval")
        with self.assertRaises(AB.B58HError):
            AB.t_interval([1.0])

    def test_sign_counts_by_hand(self):
        self.assertEqual(AB.sign_counts([1.0, -2.0, 0.0, 3.0, 0.0]), {"positive": 2, "negative": 1, "zero": 2})

    def test_the_two_sided_sign_test_is_binomtests_capped_and_not_one_sided(self):
        cases = [[1.0] * 15 + [-1.0] * 5, [1.0, -1.0, 1.0, -1.0], [2.0] * 3 + [0.0] * 4 + [-1.0] * 9,
                 list(np.random.default_rng(5).normal(0.3, 1.0, N))]
        for x in cases:
            k, n = sum(v > 0 for v in x), sum(v != 0 for v in x)
            self.assertAlmostEqual(AB.sign_two_sided(x), stats.binomtest(k, n, 0.5).pvalue, places=12)
        self.assertEqual(AB.sign_two_sided([0.0, 0.0]), 1.0)                # no nonzero difference: p = 1
        x = cases[0]
        self.assertNotAlmostEqual(AB.sign_two_sided(x), APD.sign_test(x)[2], places=6, msg="control: one-sided")
        tie = cases[1]
        uncapped = 2.0 * min(APD.sign_test(tie)[2], APD.sign_test([-v for v in tie])[2])
        self.assertGreater(uncapped, 1.0, "control: uncapped, twice the tail passes 1 at k = n / 2")
        self.assertEqual(AB.sign_two_sided(tie), 1.0)


# ------------------------------------------------------------------------------------------ the scores' refusals
class Scores(Case):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.root = tmpdir(cls)
        write_records(cls.root)
        cls.doc = study_doc(cls.root)

    def fresh(self):
        return json.loads(json.dumps(self.doc))

    def load(self, doc, newline="\n", rel="results/B58H_RESULT/s.json"):
        p = os.path.join(self.root, *rel.split("/"))
        if os.path.exists(p):
            os.remove(p)
        write_scores(self.root, doc, rel, newline=newline)
        return AB.load_scores(p, root=self.root)

    def refused(self, doc, pattern):
        with self.assertRaisesRegex(AB.B58HError, pattern):
            self.load(doc)

    def test_the_study_document_passes(self):
        sc = self.load(self.fresh())
        self.assertEqual(set(sc), {"doc", "path", "sha_text", "sha256", "checked"})
        self.assertEqual(sc["checked"]["engines"][B]["seeds"], list(range(N)))
        with open(sc["path"], "rb") as fh:
            raw = fh.read()
        self.assertEqual((sc["sha_text"], sc["sha256"]), (TC.sha_text(sc["path"]), hashlib.sha256(raw).hexdigest()))

    def test_a_crlf_copy_has_the_same_sha_text_and_another_raw_sha256(self):
        lf = self.load(self.fresh(), rel="results/B58H_RESULT/lf.json")
        crlf = self.load(self.fresh(), newline="\r\n", rel="results/B58H_RESULT/crlf.json")
        self.assertEqual(lf["sha_text"], crlf["sha_text"])
        self.assertNotEqual(lf["sha256"], crlf["sha256"], "control: the raw sha256 moves with the line ends")

    def test_each_refusal_of_the_scores(self):
        root = self.root
        two = T4.synthetic_scores(7, {}, engines=(B, "mazda_25t"), n=N)
        self.refused(with_provenance(two, root), "the B58 alone")
        one = T4.synthetic_scores(7, {}, engines=(B,), ratios=(R_HI,), n=N)
        self.refused(with_provenance(one, root), "both")
        self.refused(with_provenance(T4.synthetic_scores(7, {}, engines=(B,), n=N - 1), root), "exactly 0-")
        shifted = self.fresh()
        for arm in shifted["engines"][B]["arms"].values():
            arm["seeds"] = {str(int(s) + 1): v for s, v in arm["seeds"].items()}
        self.refused(shifted, "exactly 0-")
        for key, value, pattern in (("protocol", "phase-d", "provenance.protocol"),
                                    ("reading", "version 5 (every engine gating)", "provenance.reading"),
                                    ("reward_knock", True, "provenance.reward_knock"),
                                    ("reward_knock", 0, "provenance.reward_knock"),
                                    ("roads_sha", "0" * 64, "roads_sha")):
            d = self.fresh()
            d["provenance"][key] = value
            self.refused(d, pattern)
        d = self.fresh()
        d["variant"] = "c_turb x0.75"
        self.refused(d, "variant")
        d = self.fresh()
        d["provenance"] = ["not", "an", "object"]
        self.refused(d, "provenance")
        d = self.fresh()
        d["schema"] = "four-engine-scores/0"
        self.refused(d, "schema")
        self.load(self.fresh())                                            # control: the document itself passes


# ------------------------------------------------------------------------------------------ the band (6.5)
def hand_band(doc, ratio, reading, *, kappa_e8, at_b, p3_kappa=None, phi_from="median", arm_phi="larger",
              signed=False):
    """PR-B 6.5's band written out from the raw road lists, with the wrong implementations as options."""
    arms = doc["engines"][B]["arms"]
    sig, bl = arms[FEA.arm_name(ratio)]["seeds"], arms["blind"]["seeds"]
    seeds = sorted(sig, key=int)
    cs = [T4.scipy_cut(sig[s][reading]["D"], sig[s][reading]["D_base"]) for s in seeds]
    cb = [T4.scipy_cut(bl[s][reading]["D"], bl[s][reading]["D_base"]) for s in seeds]
    d = statistics.mean([a - b_ for a, b_ in zip(cs, cb)])
    pick = statistics.median if phi_from == "median" else statistics.mean
    medians = [pick(c) for c in (cs, cb)]                               # the sighted arm's, then the blind arm's
    phis = [max(1.0, abs(1.0 + math.log(1.0 - c / 100.0))) for c in medians]
    phi = max(phis) if arm_phi == "larger" else min(phis)
    b = HAND_MEI / HAND_SHARES
    m = b * ((d if signed else abs(d)) / HAND_MEI) * phi
    p = [m, m, b, kappa_e8 * m, m, 0.0] if at_b == "primary" else [b, b, b, kappa_e8 * m, b, 0.0]
    if p3_kappa is not None:
        p[2] = p3_kappa * b
    return {"parts": p, "delta_e": math.sqrt(sum(v * v for v in p)), "linear_sum": sum(p), "d": d, "phi": phi,
            "medians": medians, "phis": phis}


class Band(Case):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.root = tmpdir(cls)
        write_records(cls.root)
        cls.records = {"kappa_e8": SYN["kappa_e8"], "kappa_l1": dict(SYN["kappa_l1"])}

    def bands(self, doc):
        return AB.bands(checked_of(doc)["engines"][B], self.records)

    def parts(self, tb):
        return [tb["parts"][k] for k in ("P1", "P2", "P3", "P4", "P5", "P6")]

    def test_every_reading_against_a_hand_computation(self):
        doc = study_doc(self.root)
        bd = self.bands(doc)
        k = SYN["kappa_e8"]
        lo, hi = min(SYN["kappa_l1"].values()), max(SYN["kappa_l1"].values())
        self.assertEqual((bd["companions"]["companion_min"]["engine"], bd["companions"]["companion_max"]["engine"]),
                         ("mazda_25t", "ford_27tt"))
        for r in FEA.RATIOS:
            for rd in FEA.READINGS:
                for name, kw in (("primary", {"at_b": "primary"}), ("other_at_b", {"at_b": "other"}),
                                 ("companion_min", {"at_b": "primary", "p3_kappa": lo}),
                                 ("companion_max", {"at_b": "primary", "p3_kappa": hi})):
                    want = hand_band(doc, r, rd, kappa_e8=k, **kw)
                    tb = bd["tables"][name][r][rd]
                    for a, w in zip(self.parts(tb), want["parts"]):
                        self.assertAlmostEqual(a, w, places=12)
                    self.assertAlmostEqual(tb["delta_e"], want["delta_e"], places=12)
                    self.assertAlmostEqual(tb["linear_sum"], want["linear_sum"], places=12)
                    self.assertEqual(bd["model_band"][name][B][r][rd], tb["delta_e"])
                self.assertEqual(bd["model_band"]["version_5"][B][r][rd], 0.0)
        self.assertAlmostEqual(bd["b"], HAND_MEI / HAND_SHARES, places=15)

    def test_the_companions_are_the_extreme_kappas_and_a_tie_takes_the_first_name(self):
        """C7: by value; on a tie the engine first in name order (equal kappa give equal bands)."""
        for kappas, want in (({"cc_engine": 3.0, "bb_engine": 2.0, "aa_engine": 2.0}, ("aa_engine", "cc_engine")),
                             ({"cc_engine": 1.0, "bb_engine": 3.0, "aa_engine": 3.0}, ("cc_engine", "aa_engine")),
                             ({"zz_engine": 1.25, "aa_engine": 4.5, "mm_engine": 2.0}, ("zz_engine", "aa_engine"))):
            c = AB.companions({"kappa_l1": kappas})
            self.assertEqual((c["companion_min"]["engine"], c["companion_max"]["engine"]), want, kappas)
            self.assertEqual((c["companion_min"]["kappa"], c["companion_max"]["kappa"]),
                             (min(kappas.values()), max(kappas.values())))

    def test_the_other_reading_is_b_itself_and_differs_from_the_primary(self):
        bd = self.bands(study_doc(self.root))
        for r in FEA.RATIOS:
            p, o = bd["tables"]["primary"][r]["no_knock"], bd["tables"]["other_at_b"][r]["no_knock"]
            self.assertEqual(o["parts"]["P1"], bd["b"])
            self.assertNotAlmostEqual(p["parts"]["P1"], o["parts"]["P1"], places=6)
            self.assertNotAlmostEqual(p["delta_e"], o["delta_e"], places=6)

    def test_d_enters_as_its_absolute_value(self):
        doc = study_doc(self.root, d=(-4.0, -6.0))
        bd = self.bands(doc)
        tb = bd["tables"]["primary"][R_HI]["no_knock"]
        want = hand_band(doc, R_HI, "no_knock", kappa_e8=SYN["kappa_e8"], at_b="primary")
        signed = hand_band(doc, R_HI, "no_knock", kappa_e8=SYN["kappa_e8"], at_b="primary", signed=True)
        self.assertLess(want["d"], 0.0)
        self.assertGreater(tb["parts"]["P1"], 0.0)
        self.assertAlmostEqual(tb["linear_sum"], want["linear_sum"], places=12)
        self.assertGreater(abs(signed["linear_sum"] - tb["linear_sum"]), 1.0, "control: signed d moves the sum")
        # the root sum of squares cannot see the sign; the parts and the linear sum can (row 149 (2)(ii))
        self.assertAlmostEqual(signed["delta_e"], tb["delta_e"], places=12)

    def test_phi_at_the_median_cut_of_the_larger_arm(self):
        rng = np.random.default_rng(13)
        blind = list(-60.0 + 5.0 * rng.standard_normal(N))               # cuts below 0: phi above 1
        skew = [10.0] * (N // 2) + [-150.0] * (N - N // 2 - 3) + [-400.0] * 3
        doc = cuts_doc(self.root, blind, {R_LO: skew, R_HI: [c + 2.0 for c in blind]})
        bd = self.bands(doc)
        pt = bd["points"][R_LO]["no_knock"]
        self.assertGreater(pt["phi"], 1.0)
        self.assertNotEqual(pt["phi_arm"][FEA.arm_name(R_LO)], pt["phi_arm"]["blind"])
        k = SYN["kappa_e8"]
        tb = bd["tables"]["primary"][R_LO]["no_knock"]
        want = hand_band(doc, R_LO, "no_knock", kappa_e8=k, at_b="primary")
        self.assertAlmostEqual(tb["delta_e"], want["delta_e"], places=12)
        self.assertAlmostEqual(pt["phi"], want["phi"], places=12)
        for wrong in ({"phi_from": "mean"}, {"arm_phi": "smaller"}):
            other = hand_band(doc, R_LO, "no_knock", kappa_e8=k, at_b="primary", **wrong)
            self.assertGreater(abs(other["delta_e"] - tb["delta_e"]), 1e-3, f"control: {wrong}")

    def test_kappa_e8_is_read_into_p4_and_kappa_1_is_not_it(self):
        doc = study_doc(self.root)
        bd = self.bands(doc)
        tb = bd["tables"]["primary"][R_HI]["no_knock"]
        self.assertAlmostEqual(tb["parts"]["P4"], SYN["kappa_e8"] * tb["multiplicative"], places=12)
        one = hand_band(doc, R_HI, "no_knock", kappa_e8=1.0, at_b="primary")
        self.assertGreater(abs(one["delta_e"] - tb["delta_e"]), 1e-3, "control: kappa_E8 at 1")

    def test_phi_is_1_inside_0_to_0865_and_above_1_outside(self):
        for c in (0.0, 0.3, 0.86):
            self.assertEqual(AB.phi_of(c), 1.0)
        self.assertAlmostEqual(AB.phi_of(0.9), abs(1.0 + math.log(0.1)), places=12)
        self.assertGreater(AB.phi_of(0.9), 1.0)
        self.assertAlmostEqual(AB.phi_of(-1.0), 1.0 + math.log(2.0), places=12)
        with self.assertRaisesRegex(AB.B58HError, "below 100 %"):
            AB.phi_of(1.0)

    def test_a_median_cut_at_100_percent_is_refused_with_abs_message(self):
        doc = cuts_doc(self.root, [100.0] * N, {R_LO: [50.0] * N, R_HI: [50.0] * N})
        with self.assertRaisesRegex(AB.B58HError, "the blind arm: a median cut of 100.00 %"):
            self.bands(doc)
        self.bands(cuts_doc(self.root, [99.0] * N, {R_LO: [50.0] * N, R_HI: [50.0] * N}))      # control


# ------------------------------------------------------------------------------------------ one study, end to end
class Study(Case):
    """One SYNTHETIC study committed in a temporary repository; context and analyse run once for the class."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tmp = tmpdir(cls)
        cls.root, cls.scores = make_repo(cls.tmp)
        cls.pristine = copy_repo(cls.root, cls.tmp, "pristine")[0]          # before any output exists
        cls.ctx_path, cls.out, cls.rep = run_both(cls.root, cls.scores)
        cls.ctx, cls.res, cls.text = load(cls.ctx_path), load(cls.out), read_text(cls.rep)
        cls.doc = load(cls.scores)
        cls.checked = checked_of(cls.doc)

    def fresh_repo(self, name):
        return copy_repo(self.pristine, tmpdir(self), name)


class CeilingWithKnock(Study):
    """G11: the with-knock bracket prints roads.json by[r].a.knock.mean beside C, and the JSON records it."""

    def test_the_bracket_prints_the_ceilings_with_knock_reading(self):
        for r in (R_LO, R_HI):
            ck = f"{SYN['ceiling_knock'][r]:.2f}"
            self.assertNotEqual(ck, f"{SYN['ceiling'][r]:.2f}", "control: the two readings print apart")
            want = (f"; the ceiling's with-knock reading {ck} points (roads.json a.knock.mean, beside C, the no-knock "
                    "reading's); the MEI as above]")
            bracket = [x for x in self.res["sentences"][r]["text"] if x.startswith("[with knock")]
            self.assertEqual(len(bracket), 1)
            self.assertTrue(bracket[0].endswith(want), bracket[0])
            self.assertIn(want, self.text)
            beside = [x for x in self.res["sentences"][r]["text"] if x.startswith("beside it:")]
            self.assertIn(f"the ceiling C({r}) {SYN['ceiling'][r]:.2f} points", beside[0])     # C stays no-knock
        cw = self.res["ceiling_with_knock"]
        self.assertEqual(cw["by_ratio"], SYN["ceiling_knock"])                                   # full precision
        self.assertEqual(cw["where"], f"{AB.ROADS} ceilings.per_engine.{B}.by[r].a.knock.mean")
        self.assertEqual(cw["label"], "beside C, the no-knock reading's and the context's; decides nothing (G11)")
        self.assertEqual(self.ctx["ceiling"], {B: SYN["ceiling"]}, "the context's ceiling is C, the no-knock one")

    def test_read_records_reads_a_knock_mean_and_refuses_it_missing(self):
        root = tmpdir(self)
        write_records(root)
        self.assertEqual(AB.read_records(root, check=False)["ceiling_knock"], SYN["ceiling_knock"])
        bare = tmpdir(self)
        write_records(bare, ceiling_knock=None)
        with self.assertRaisesRegex(AB.B58HError, r"no key 0\.5\.a\.knock\.mean"):
            AB.read_records(bare, check=False)

    def test_read_records_refuses_a_knock_mean_that_is_not_a_finite_number_by_its_key_path(self):
        """G11's value is a finite number, refused with its own key path (not C's) when it is a string, NaN or a
        bool; otherwise the context would be written and analyse would crash on it."""
        for bad in ("3.79", float("nan"), True):
            root = tmpdir(self)
            write_records(root, ceiling_knock={R_LO: bad, R_HI: SYN["ceiling_knock"][R_HI]})
            with self.subTest(bad=bad):
                where = re.escape(f"{AB.ROADS} ceilings.per_engine.{B}.by['{R_LO}'].a.knock.mean")
                with self.assertRaisesRegex(AB.B58HError, rf"^{where}: a finite number is required, found "
                                            rf"{re.escape(repr(bad))}$"):
                    AB.read_records(root, check=False)


class Context(Study):
    def test_it_passes_validate_context(self):
        FEA.validate_context(self.ctx, self.checked)
        self.assertEqual(self.ctx["schema"], FEA.CONTEXT_SCHEMA)

    def test_every_value_is_read_from_the_records(self):
        c = self.ctx
        self.assertEqual(c["ceiling"], {B: SYN["ceiling"]})                 # full precision, exactly
        self.assertEqual(c["status_basis"]["s_p"], SYN["x2"][1])
        self.assertEqual(c["status_basis"]["pilot_pairs"], FEA.PILOT_PAIRS)
        self.assertEqual((c["seeds_per_arm"], c["engines_in_test"]), (N, [B]))
        inputs = c["provenance"]["inputs"]
        self.assertEqual((inputs["kappa_E8"], inputs["kappa_L1"]), (SYN["kappa_e8"], SYN["kappa_l1"]))
        self.assertEqual(inputs["s_p_line"], f"{AB.X2_RESULT}:{AB.X2_SP_LINE}")
        self.assertEqual(c["provenance"]["s_p_label"],
                         "X2's spread: another plant, road and budget; not a pilot of this study")
        self.assertEqual(c["provenance"]["at_b"], "kappa 1 in the contract's form")
        for rel in AB.CONTEXT_RECORDS:
            self.assertEqual(c["provenance"]["records"][rel], TC.sha_text(os.path.join(self.root, *rel.split("/"))))
        self.assertEqual(c["provenance"]["scores"]["sha_text"], TC.sha_text(self.scores))
        self.assertEqual(c["provenance"]["scores"]["path"], SCORES_REL)
        bd = AB.bands(self.checked["engines"][B], {"kappa_e8": SYN["kappa_e8"], "kappa_l1": SYN["kappa_l1"]})
        self.assertEqual(c["model_band"], bd["model_band"]["primary"])

    def test_s_star_is_status_star_at_the_full_precision_ceiling(self):
        s = self.ctx["status_basis"]["s_star"][B]
        self.assertEqual(s, FEA.status_star({B: SYN["ceiling"][R_HI]}, N)[B])
        rounded = FEA.status_star({B: round(SYN["ceiling"][R_HI], 4)}, N)[B]
        self.assertGreater(abs(rounded - s), FEA.S_STAR_RTOL * s, "control: the rounded ceiling's s* differs")
        bad = copy.deepcopy(self.ctx)
        bad["status_basis"]["s_star"][B] = rounded
        with self.assertRaisesRegex(FEA.AnalysisError, "s_star"):
            FEA.validate_context(bad, self.checked)

    def test_status_is_the_rules_output_and_moves_with_the_file(self):
        self.assertEqual(self.ctx["status"], {B: "exploratory"})
        self.assertGreater(FEA.pilot_factor() * self.ctx["status_basis"]["s_p"],
                           self.ctx["status_basis"]["s_star"][B])
        root, scores = make_repo(tmpdir(self), x2=(16.5, 0.75), kappa_e8=3.5,
                                 ceiling={R_LO: 1.25, R_HI: 4.75})
        ctx_path = out_paths(root)[0]
        AB.context(scores, ctx_path, root=root)
        c = load(ctx_path)
        self.assertEqual(c["status_basis"]["s_p"], 0.75)                       # the file's sd, read (D8)
        self.assertEqual(c["status"], {B: "confirmatory"})                     # the rule's output, not typed
        self.assertEqual(c["ceiling"][B], {R_LO: 1.25, R_HI: 4.75})
        p4_new = c["provenance"]["band"]["parts"][R_HI]["no_knock"]["parts"]["P4"]
        m = c["provenance"]["band"]["parts"][R_HI]["no_knock"]["multiplicative"]
        self.assertAlmostEqual(p4_new, 3.5 * m, places=12)                    # kappa_E8 read into P4
        self.assertNotEqual(c["model_band"], self.ctx["model_band"])
        # section 10 (PR-B:1109): primary, the analysis's status (one engine: exploratory, FEA:668-669); beside it,
        # the context's recorded rule output, here confirmatory, so the two differ and each is its own source's
        out, rep = out_paths(root)[1:]
        AB.analyse(scores, ctx_path, out, rep, root=root)
        res = load(out)
        self.assertEqual(res["fea"]["primary"]["status"][B], "exploratory")
        self.assertEqual(res["section_10"]["status"], {"primary": "the analysis's exploratory",
                                                       "beside": "the context's recorded rule output, confirmatory"})

    def test_written_once(self):
        before = read_text(self.ctx_path)
        with self.assertRaisesRegex(AB.B58HError, "exists"):
            AB.context(self.scores, self.ctx_path, root=self.root)
        self.assertEqual(read_text(self.ctx_path), before)

    def test_a_record_or_the_scores_not_committed_is_refused(self):
        for i, rel in enumerate(AB.CONTEXT_RECORDS + (SCORES_REL,)):
            root, scores = self.fresh_repo(f"changed{i}")
            p = os.path.join(root, *rel.split("/"))
            with open(p, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(" \n")
            with self.assertRaisesRegex(AB.B58HError, f"not committed at HEAD.*{os.path.basename(rel)}"):
                AB.context(scores, out_paths(root)[0], root=root)
            self.assertFalse(os.path.exists(out_paths(root)[0]))
        root, scores = self.fresh_repo("untracked")
        git(root, "rm", "-q", "--cached", AB.SUMMARY)
        git(root, "commit", "-q", "-m", "summary untracked")
        with self.assertRaisesRegex(AB.B58HError, "summary.json"):
            AB.context(scores, out_paths(root)[0], root=root)
        root, scores = self.fresh_repo("control")
        AB.context(scores, out_paths(root)[0], root=root)                     # control: the copy itself passes

    def test_x2s_line_24_is_refused_unless_it_is_the_no_knock_spread_of_5_pairs(self):
        for i, (text, pattern) in enumerate(((x2_text(16.5, "twenty"), "does not read"),
                                             (x2_text(16.5, 17.25, n=4), "for 5 pairs"),
                                             (x2_text(16.5, 17.25, section="TOTAL DAMAGE (again)"),
                                              "THERMAL-ONLY"))):
            root, scores = self.fresh_repo(f"x2_{i}")
            write(root, AB.X2_RESULT, text)
            git(root, "commit", "-q", "-am", "X2 changed")
            with self.assertRaisesRegex(AB.B58HError, pattern):
                AB.context(scores, out_paths(root)[0], root=root)

    def test_the_scores_refusals_reach_the_context_command(self):
        root, scores = self.fresh_repo("variant")
        d = load(scores)
        d["provenance"]["reward_knock"] = True
        os.remove(scores)
        write_scores(root, d)
        git(root, "commit", "-q", "-am", "knock in")
        with self.assertRaisesRegex(AB.B58HError, "reward_knock"):
            AB.context(scores, out_paths(root)[0], root=root)

    def test_roads_json_reading_keys_must_be_roads_ceilings(self):
        root, scores = make_repo(tmpdir(self), readings=["knock", "noknock"])
        with self.assertRaisesRegex(AB.B58HError, "ceilings.readings"):
            AB.context(scores, out_paths(root)[0], root=root)


class Analyse(Study):
    def test_five_runs_each_with_its_band_reaching_four_engine_analysis(self):
        runs = self.res["fea_runs"]
        self.assertEqual(sorted(runs), sorted(AB.RUNS))
        self.assertEqual(runs["primary"]["model_band"], self.ctx["model_band"])
        for name in AB.RUNS:
            res = self.res["fea"][name]
            for r in FEA.RATIOS:
                for rd in FEA.READINGS:
                    band = res["readings"][rd]["d"][FEA.node(B, r)]["band"]
                    self.assertEqual(band, runs[name]["model_band"][B][r][rd])     # mistake 25: it reached FEA
                    if name == "version_5":
                        self.assertEqual(band, 0.0)
        self.assertNotEqual(runs["other_at_b"]["model_band"], runs["primary"]["model_band"])

    def test_the_report_holds_four_engine_analysis_verbatim_with_the_note_above(self):
        fea = FEA.report(FEA.analyse(self.doc, self.ctx))                 # an independent run of the same inputs
        self.assertEqual(self.text.count(fea), 1)
        i = self.text.index(fea)
        self.assertEqual(self.text[i - 2:i], "\n\n")
        self.assertEqual(self.text[i + len(fea)], "\n")
        lines_above = self.text[:i].rstrip("\n").split("\n")
        self.assertEqual(lines_above[-1], AB.NOTE)
        self.assertEqual(len(lines_above), 5)                                   # the 4-line header and the note
        self.assertIn("FOUR-ENGINE TEST (row 113)", AB.NOTE)
        self.assertEqual(FEA.report(self.res["fea"]["primary"]), fea)          # its JSON gives the same text
        self.assertTrue(fea.startswith("FOUR-ENGINE TEST (row 113)"))
        self.assertTrue(self.text.isascii())

    def test_the_blocks_follow_in_the_designs_order(self):
        heads = ["SECTION 7: THE VERDICTS", "INTERVALS (PR-B 6.3)", "DELTA, THE ACROSS-H CONTRAST",
                 "THE B58'S MODEL BAND", "SECTION 9.1: FUEL AND TORQUE DELIVERY", "SECTION 10: THE BESIDE VALUES"]
        at = [self.text.index("\n" + h) for h in heads]
        self.assertEqual(at, sorted(at))
        self.assertGreater(at[0], self.text.index("FOUR-ENGINE TEST (row 113)"))

    def test_no_forbidden_phrase_in_abs_own_text(self):
        fea = FEA.report(self.res["fea"]["primary"])
        own = fea_part(self.text, fea)
        self.assertEqual(AB.phrase_hits(own), [])
        self.assertEqual(AB.phrase_hits(json.dumps(self.res["sentences"])), [])
        self.assertIn("not a test of the H/tau criterion", own)               # section 7's own negation
        # controls: each phrase is caught, and four_engine_analysis's verbatim text would be caught were it AB's
        for phrase in ("a test of the criterion", "a collapse", "H/tau governs", "H/\u03c4 governs",
                       "the criterion holds", "the criterion fails", "preview does not help"):
            self.assertEqual(AB.phrase_hits(f"x {phrase} y"), [phrase.lower()])
        self.assertEqual(AB.phrase_hits(fea), ["a test of the criterion"])

    def test_a_forbidden_phrase_in_abs_text_is_a_defect(self):
        root, scores = self.fresh_repo("phrase")
        ctx, out, rep = out_paths(root)
        AB.context(scores, ctx, root=root)
        with mock.patch.object(AB, "NOT_SHOWN", AB.NOT_SHOWN + " Preview does not help."), \
                mock.patch.object(AB, "D_GT_0", AB.D_GT_0 + " Preview does not help."):
            with self.assertRaisesRegex(AB.DefectError, "never-written"):
                AB.analyse(scores, ctx, out, rep, root=root)
        self.assertFalse(os.path.exists(out) or os.path.exists(rep))
        # AB's other blocks are its own text too: Delta's statements, section 10's sentence (C13)
        for name, value in (("DELTA_STATEMENTS", AB.DELTA_STATEMENTS + ("Delta shows a collapse.",)),
                            ("PRACTICE_SENTENCE", AB.PRACTICE_SENTENCE + "; the criterion holds")):
            with mock.patch.object(AB, name, value):
                with self.assertRaisesRegex(AB.DefectError, "never-written"):
                    AB.analyse(scores, ctx, out, rep, root=root)
            self.assertFalse(os.path.exists(out) or os.path.exists(rep), name)

    def test_a_context_for_other_scores_is_refused_and_a_crlf_copy_accepted(self):
        root, scores = self.fresh_repo("other")
        other = write_scores(root, study_doc(root, rng_seed=99), "results/B58H_RESULT/other.json")
        ctx, out, rep = out_paths(root)
        AB.context(scores, ctx, root=root)
        with self.assertRaisesRegex(AB.B58HError, "made for other scores"):
            AB.analyse(other, ctx, out, rep, root=root)
        crlf = write_scores(root, load(scores), "results/B58H_RESULT/crlf.json", newline="\r\n")
        self.assertNotEqual(AB.sha256_file(crlf), AB.sha256_file(scores))
        AB.analyse(crlf, ctx, out, rep, root=root)
        res = load(out)
        self.assertEqual(res["inputs"]["scores"]["sha_text"], TC.sha_text(scores))
        self.assertEqual(res["inputs"]["scores"]["sha256"], AB.sha256_file(crlf))

    def tampered(self, name, change, pattern):
        root, scores = self.fresh_repo(name)
        ctx_path, out, rep = out_paths(root)
        AB.context(scores, ctx_path, root=root)
        ctx = load(ctx_path)
        change(ctx)
        bad = write(root, "results/B58H_RESULT/tampered.json", json.dumps(ctx, indent=1))
        if pattern is None:
            AB.analyse(scores, bad, out, rep, root=root)
            return
        with self.assertRaisesRegex(AB.B58HError, pattern):
            AB.analyse(scores, bad, out, rep, root=root)
        self.assertFalse(os.path.exists(out) or os.path.exists(rep))

    def test_a_context_for_the_other_reading_of_at_b_is_refused(self):
        self.tampered("at_b", lambda c: c["provenance"].__setitem__("at_b", AB.AT_B_OTHER), "another reading of 'at b'")

    def test_a_band_that_is_not_the_recomputed_one_is_refused(self):
        def bump(c):
            c["model_band"][B][R_HI]["no_knock"] += 1e-9
        self.tampered("band", bump, "model_band")
        other = self.res["fea_runs"]["other_at_b"]["model_band"]
        self.tampered("band_other", lambda c: c.__setitem__("model_band", copy.deepcopy(other)), "model_band")

        def within(c):
            c["model_band"][B][R_HI]["no_knock"] *= 1.0 + 1e-15
        self.tampered("band_within", within, None)                          # control: inside the tolerance

    def test_a_context_not_made_from_these_records_is_refused(self):
        def ceiling(c):
            c["ceiling"][B][R_LO] = 2.0
        self.tampered("ceiling", ceiling, "ceiling")

        def records(c):
            c["provenance"]["records"][AB.X2_RESULT] = "0" * 64
        self.tampered("records", records, "records")

        def s_p(c):                       # the status stays the rule's output at 19 (exploratory): only s_p moved
            c["status_basis"]["s_p"] = 19.0
        self.tampered("s_p", s_p, r"status_basis\.s_p: 19\.0 recorded, 17\.25 recomputed")

        def kappa(c):
            c["provenance"]["inputs"]["kappa_E8"] = 9.75
        self.tampered("kappa", kappa, r"provenance\.inputs\.kappa_E8: 9\.75 recorded")

        def no_line(c):                   # a key missing from a compared slot: section 10 would print s_p's source None
            del c["provenance"]["inputs"]["s_p_line"]
        self.tampered("no_line", no_line, r"provenance\.inputs\.s_p_line: present in one only")

        def extra(c):
            c["status_basis"]["SYNTHETIC_extra"] = 1.0
        self.tampered("extra", extra, r"status_basis\.SYNTHETIC_extra: present in one only")

        def twice(c):
            c["engines_in_test"] = [B, B]
        self.tampered("twice", twice, r"engines_in_test: lengths 2 and 1")

    def test_analyse_refuses_a_record_no_longer_committed_at_head(self):
        """C5: analyse re-reads the committed records; one untracked since the context, its bytes unchanged, is
        refused (and the same copy before the change runs: the control)."""
        root, scores = self.fresh_repo("uncommitted")
        ctx, out, rep = out_paths(root)
        AB.context(scores, ctx, root=root)
        git(root, "rm", "-q", "--cached", AB.BACKEND)
        git(root, "commit", "-q", "-m", "the backend record untracked, its bytes unchanged")
        with self.assertRaisesRegex(AB.B58HError, r"not committed at HEAD.*EPA_BACKEND\.json"):
            AB.analyse(scores, ctx, out, rep, root=root)
        self.assertFalse(os.path.exists(out) or os.path.exists(rep))
        git(root, "add", AB.BACKEND)
        git(root, "commit", "-q", "-m", "tracked again")
        AB.analyse(scores, ctx, out, rep, root=root)                          # control

    def test_a_crlf_checkout_records_every_sha_text_as_sha_text(self):
        """PR-B:461-463: a hash quoted for a document is its sha_text; the raw sha256 binds nothing. The scores, the
        records and the context checked out CRLF (core.autocrlf true, as on the laptop): context binds the scores by
        their sha_text, records each record's sha_text, and analyse accepts its own scores and records the
        context's sha_text."""
        root, scores = self.fresh_repo("crlf_checkout")
        rels = (SCORES_REL,) + AB.CONTEXT_RECORDS + (AB.X1_RESULT, AB.REVERIFY)
        for rel in rels:
            to_crlf(os.path.join(root, *rel.split("/")))
        lined = set()
        for rel in rels:
            p = os.path.join(root, *rel.split("/"))
            self.assertTrue(AB.EF.committed_at_head(rel, root=root), rel)     # a CRLF checkout of the LF blob
            with open(p, "rb") as fh:
                if b"\r\n" in fh.read():                                     # a one-line JSON record has no line end
                    lined.add(rel)
                    self.assertTrue(AB.sha256_file(p) != TC.sha_text(p), rel)   # control: raw and sha_text differ
        self.assertLessEqual({SCORES_REL, AB.ROADS, AB.X2_RESULT, AB.X1_RESULT}, lined)
        ctx, out, rep = out_paths(root)
        AB.context(scores, ctx, root=root)
        c = load(ctx)
        self.assertEqual(c["provenance"]["scores"]["sha_text"], TC.sha_text(scores))
        self.assertEqual(c["provenance"]["scores"]["sha256"], AB.sha256_file(scores))
        for rel in AB.CONTEXT_RECORDS:
            self.assertEqual(c["provenance"]["records"][rel], TC.sha_text(os.path.join(root, *rel.split("/"))), rel)
        to_crlf(ctx)
        self.assertNotEqual(AB.sha256_file(ctx), TC.sha_text(ctx))
        AB.analyse(scores, ctx, out, rep, root=root)
        res = load(out)
        self.assertEqual(res["inputs"]["context"], {"path": "results/B58H_RESULT/context_b58h.json",
                                                    "sha_text": TC.sha_text(ctx), "sha256": AB.sha256_file(ctx)})
        self.assertEqual(res["inputs"]["scores"]["sha_text"], TC.sha_text(scores))
        self.assertEqual(res["inputs"]["records"], c["provenance"]["records"])
        self.assertIn(f"context results/B58H_RESULT/context_b58h.json: sha_text {TC.sha_text(ctx)}, made for",
                      read_text(rep))

    def test_a_verdict_that_moves_under_any_one_band_is_a_defect(self):
        """PR-B:584-585 for each band beside the primary: the other reading of 'at b' and each companion."""
        root, scores = self.fresh_repo("defect_each")
        ctx, out, rep = out_paths(root)
        AB.context(scores, ctx, root=root)
        real = FEA.analyse
        for name in ("other_at_b", "companion_min", "companion_max"):
            band = self.res["fea_runs"][name]["model_band"]

            def moved(sc, cx, sources=None, band=band):
                res = real(sc, cx, sources)
                if cx["model_band"] == band:                                  # this run alone
                    row = res["readings"]["no_knock"]["d"][FEA.node(B, R_HI)]["t"]
                    row["d_gt_0"] = not row["d_gt_0"]
                return res
            with mock.patch.object(FEA, "analyse", moved):
                with self.assertRaisesRegex(AB.DefectError, f"moves with the band.* under {name}"):
                    AB.analyse(scores, ctx, out, rep, root=root)
            self.assertFalse(os.path.exists(out), name)

    def test_a_d_gt_0_verdict_that_moves_with_the_band_is_a_defect(self):
        root, scores = self.fresh_repo("defect")
        ctx, out, rep = out_paths(root)
        AB.context(scores, ctx, root=root)
        real = FEA.analyse

        def moved(sc, cx, sources=None):
            res = real(sc, cx, sources)
            row = res["readings"]["no_knock"]["d"][FEA.node(B, R_HI)]["t"]
            row["d_gt_0"] = cx["model_band"][B][R_HI]["no_knock"] > 0.0        # d > 0 now depends on the band
            return res
        with mock.patch.object(FEA, "analyse", moved):
            with self.assertRaisesRegex(AB.DefectError, "moves with the band.*version_5"):
                AB.analyse(scores, ctx, out, rep, root=root)
            with self.assertRaises(SystemExit) as cm:
                with redirect_stdout(io.StringIO()):
                    AB.main(["analyse", "--scores", scores, "--context", ctx, "--out", out, "--report", rep],
                            root=root)
            self.assertIn("a defect of AB's code", str(cm.exception.code))
        self.assertFalse(os.path.exists(out))
        AB.analyse(scores, ctx, out, rep, root=root)                          # control: FEA as committed passes
        self.assertTrue(load(out)["verdicts_fixed_under_every_band"])

    def test_outputs_are_written_once(self):
        before = read_text(self.rep)
        ctx2 = self.ctx_path
        new_txt, new_json = os.path.join(self.root, "new.txt"), os.path.join(self.root, "new.json")
        with self.assertRaisesRegex(AB.B58HError, "exists"):
            AB.analyse(self.scores, ctx2, self.out, new_txt, root=self.root)
        with self.assertRaisesRegex(AB.B58HError, "exists"):
            AB.analyse(self.scores, ctx2, new_json, self.rep, root=self.root)
        self.assertFalse(os.path.exists(new_txt) or os.path.exists(new_json), "C1: nothing is written on a refusal")
        with self.assertRaisesRegex(AB.B58HError, "twice"):
            p = os.path.join(self.root, "same.out")
            AB.analyse(self.scores, ctx2, p, p, root=self.root)
        self.assertEqual(read_text(self.rep), before)
        missing = os.path.join(self.root, "no_such_scores.json")              # C2: refused before anything is read
        with self.assertRaisesRegex(AB.B58HError, "exists"):
            AB.analyse(missing, ctx2, new_json, self.rep, root=self.root)
        with self.assertRaisesRegex(AB.B58HError, "exists"):
            AB.context(missing, self.ctx_path, root=self.root)
        with self.assertRaisesRegex(AB.B58HError, "cannot be read"):          # control: read once nothing exists
            AB.analyse(missing, ctx2, new_json, new_txt, root=self.root)
        self.assertFalse(os.path.exists(new_txt) or os.path.exists(new_json))

    def test_an_output_that_cannot_be_created_is_refused_and_none_is_written(self):
        """C1, C2 (PR-B:1159-1164): analyse makes both folders and opens both files, the JSON first, before it writes
        either, so a report whose folder would be a file, or a report that cannot be opened, is refused and leaves no
        analysis JSON behind to block the rerun; and a report whose write fails after the JSON was written in full
        (a full disk) is refused with the JSON removed too."""
        root, scores = self.fresh_repo("uncreatable")
        ctx, out, rep = out_paths(root)
        AB.context(scores, ctx, root=root)
        argv = ["analyse", "--scores", scores, "--context", ctx, "--out", out, "--report"]
        below_a_file = os.path.join(ctx, "analysis_b58h.txt")             # its folder would be the context file
        with self.assertRaisesRegex(AB.B58HError, "its folder cannot be made"):
            AB.analyse(scores, ctx, out, below_a_file, root=root)
        self.assertFalse(os.path.exists(out), "the JSON is not written when the report cannot be")
        with self.assertRaises(SystemExit) as cm:
            with redirect_stdout(io.StringIO()):
                AB.main(argv + [below_a_file], root=root)
        self.assertTrue(str(cm.exception.code).startswith("REFUSED: "), cm.exception.code)
        deeper = os.path.join(ctx, "sub", "analysis_b58h.txt")              # not a FileExistsError: still refused
        with self.assertRaises(SystemExit) as cm:
            with redirect_stdout(io.StringIO()):
                AB.main(argv + [deeper], root=root)
        self.assertTrue(str(cm.exception.code).startswith(f"REFUSED: {deeper}: its folder cannot be made"),
                        cm.exception.code)
        self.assertFalse(os.path.exists(out))
        fake, log = writer_open(refuse=(rep, PermissionError(13, "SYNTHETIC: the report cannot be opened", rep)))
        with mock.patch.object(AB, "open", fake, create=True):
            with self.assertRaisesRegex(AB.B58HError, "cannot be created"):
                AB.analyse(scores, ctx, out, rep, root=root)
        self.assertEqual([(_n(p), fh is not None) for p, fh in log], [(_n(out), True), (_n(rep), False)],
                         "the JSON is opened first, then the report (C2), so the test above is not vacuous")
        self.assertFalse(os.path.exists(out) or os.path.exists(rep), "the JSON opened first is removed, empty")
        fake, log = writer_open(full=(rep,))
        with mock.patch.object(AB, "open", fake, create=True):
            with self.assertRaises(SystemExit) as cm:
                with redirect_stdout(io.StringIO()):
                    AB.main(argv + [rep], root=root)
        self.assertEqual(str(cm.exception.code),
                         f"REFUSED: {rep}: the write failed ([Errno 28] SYNTHETIC: no space left on device); nothing "
                         f"is written (this call's files removed: {out}, {rep})")
        self.assertEqual([_n(p) for p, _ in log], [_n(out), _n(rep)])
        self.assertFalse(os.path.exists(out) or os.path.exists(rep), "the JSON written in full is removed as well")
        AB.analyse(scores, ctx, out, rep, root=root)                          # control: the rerun writes both
        self.assertEqual(load(out)["schema"], AB.SCHEMA)
        self.assertTrue(read_text(rep).startswith("B58 PREVIEW STUDY: THE ANALYSIS"))

    def test_every_output_is_ascii_lf_and_ends_with_one_line_end(self):
        """OUTPUTS: the context, the analysis JSON and the report in ASCII with LF line ends, each ending with one."""
        for p in (self.ctx_path, self.out, self.rep):
            with open(p, "rb") as fh:
                raw = fh.read()
            self.assertTrue(raw.endswith(b"\n") and not raw.endswith(b"\n\n"), p)
            self.assertNotIn(b"\r", raw, p)
            self.assertTrue(raw.isascii(), p)
        self.assertTrue(self.text.endswith("(paired t | exact sign test)\n"), self.text[-80:])  # section 10's last

    def test_the_band_block_prints_b_the_parts_phi_and_the_kappas_at_4_decimals(self):
        """C9: the band block's numbers at 4 decimals, each against hand_band's (PR-B 6.5 written out)."""
        k, lo, hi = SYN["kappa_e8"], min(SYN["kappa_l1"].values()), max(SYN["kappa_l1"].values())
        self.assertIn(f"b = MEI / 6 = {HAND_MEI / HAND_SHARES:.4f} points (MEI 5.43); kappa_E8 {k:.4f} (", self.text)
        self.assertIn(f"the companion's kappa_L1 {lo:.4f} (mazda_25t, the smallest) and {hi:.4f} (ford_27tt, the "
                      "largest)", self.text)
        self.assertIn("b = MEI / 6 = 0.9050 points", self.text)                 # control: 4 decimals, typed
        for r in FEA.RATIOS:
            for rd in FEA.READINGS:
                lab = "no knock" if rd == FEA.PRIMARY else f"with knock [{FEA.WITH_KNOCK_LABEL}]"
                w = hand_band(self.doc, r, rd, kappa_e8=k, at_b="primary")
                arm = FEA.arm_name(r)
                self.assertIn(f"\n  r = {r}, {lab}: d (t_greater's mean) {w['d']:+.2f}; median cuts {arm} "
                              f"{w['medians'][0]:+.2f} % (phi {w['phis'][0]:.4f}), blind {w['medians'][1]:+.2f} % "
                              f"(phi {w['phis'][1]:.4f}); phi {w['phi']:.4f}\n", self.text)
                for name, kw in (("primary", {"at_b": "primary"}), ("other_at_b", {"at_b": "other"}),
                                 ("companion_min", {"at_b": "primary", "p3_kappa": lo}),
                                 ("companion_max", {"at_b": "primary", "p3_kappa": hi})):
                    w = hand_band(self.doc, r, rd, kappa_e8=k, **kw)
                    parts = "  ".join(f"P{i} {v:.4f}" for i, v in enumerate(w["parts"], 1))
                    self.assertIn(f"\n    {name:<14} {parts}  Delta_e {w['delta_e']:.4f} (RSS)  linear sum "
                                  f"{w['linear_sum']:.4f}\n", self.text)
        self.assertEqual(self.text.count("\n    version_5      the band left out: Delta_e 0\n"), 4)

    def test_d_delta_verdicts_band_and_status_are_the_same_with_and_without_b58h_lambda_opt(self):
        """PR-B 9.8 item 2's control, "AB's test" (PR-B:1082-1083)."""
        root, scores = self.fresh_repo("lambda_opt")
        paths = out_paths(root)
        run_both(root, scores)
        first = [read_text(p) for p in paths]
        for p in paths:
            os.remove(p)
        write(root, "results/B58H_LAMBDA_OPT/lambda_opt.json", json.dumps({"SYNTHETIC": True, "saving": 99.0}))
        write(root, "results/B58H_LAMBDA_OPT/report.txt", "SYNTHETIC row 153 (2) output\n")
        run_both(root, scores)
        self.assertEqual([read_text(p) for p in paths], first)                # byte for byte, folder present
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "row 153 (2)'s files, committed")
        run_both(root, scores, tag="_committed")
        a, b = load(paths[1]), load(out_paths(root, "_committed")[1])
        for key in ("intervals", "delta", "band", "flags", "sentences", "delivery", "fea_runs"):
            self.assertEqual(a[key], b[key], key)
        for name in AB.RUNS:
            self.assertEqual(a["fea"][name]["readings"], b["fea"][name]["readings"])
            self.assertEqual(a["fea"][name]["status"], b["fea"][name]["status"])
        self.assertNotEqual(a["inputs"]["git_head"], b["inputs"]["git_head"])  # control: HEAD did move
        with open(os.path.join(HERE, "b58h_analysis.py"), encoding="utf-8") as fh:
            self.assertNotIn("LAMBDA_OPT", fh.read().upper())

    def test_the_cli(self):
        root, scores = self.fresh_repo("cli")
        ctx, out, rep = out_paths(root)
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(AB.main(["context", "--scores", scores, "--out", ctx], root=root), 0)
            self.assertEqual(AB.main(["analyse", "--scores", scores, "--context", ctx, "--out", out,
                                      "--report", rep], root=root), 0)
        report = read_text(rep)
        self.assertTrue(report.endswith(")\n") and buf.getvalue().endswith("\n" + report),
                        "the report is the printed text and one LF")
        with self.assertRaises(SystemExit) as cm:
            AB.main(["context", "--scores", scores, "--out", ctx], root=root)
        self.assertTrue(str(cm.exception.code).startswith("REFUSED: "))


class WriteAll(Case):
    """C1, C2: _write_all writes one command's outputs together or not at all, each opened "x", in the order given;
    every refusal is a B58HError (main's "REFUSED: ...") and leaves no file the call opened, one written in full among
    them (R3M-1). Each refusal is driven here directly, since context and analyse refuse an existing output before
    _write_all is reached."""

    def setUp(self):
        super().setUp()
        self.d = tmpdir(self)
        self.outs = [(os.path.join(self.d, "analysis.json"), '{"x": 1}\n'),
                     (os.path.join(self.d, "analysis.txt"), "a SYNTHETIC report line\n" * 64)]

    def left(self):
        return sorted(os.listdir(self.d))

    def test_both_are_written_in_full_in_order_and_closed_when_it_returns(self):
        fake, log = writer_open()
        with mock.patch.object(AB, "open", fake, create=True):
            AB._write_all(self.outs)
        self.assertEqual([p for p, _ in log], [p for p, _ in self.outs])
        self.assertTrue(all(fh.closed for _, fh in log), "every handle is closed when it returns")
        for path, text in self.outs:                         # read while the log still holds every handle
            with open(path, "rb") as fh:
                self.assertEqual(fh.read(), text.encode("utf-8"))

    def test_a_bare_file_name_is_written_in_the_current_folder(self):
        with contextlib.chdir(self.d):
            AB._write_once("bare.json", "{}\n")
        with open(os.path.join(self.d, "bare.json"), "rb") as fh:
            self.assertEqual(fh.read(), b"{}\n")

    def test_a_folder_that_cannot_be_made_is_refused_whatever_the_os_error(self):
        a_file = write(self.d, "a_file", "x")
        for bad in (os.path.join(a_file, "r.txt"), os.path.join(a_file, "sub", "r.txt")):
            with self.subTest(bad=os.path.relpath(bad, self.d)):
                with self.assertRaisesRegex(AB.B58HError, rf"^{re.escape(bad)}: its folder cannot be made \(.+\); "
                                            "nothing is written$"):
                    AB._write_all([self.outs[0], (bad, "r\n")])
                self.assertEqual(self.left(), ["a_file"])

    def test_an_output_that_exists_at_the_open_is_refused_and_kept(self):
        kept = write(self.d, "kept.json", "KEPT")
        with self.assertRaisesRegex(AB.B58HError, rf"^{re.escape(kept)} exists: a document of this study, once "
                                    r"written, is kept \(PR-B:1159-1160\); nothing is written$"):
            AB._write_once(kept, "NEW\n")
        fake, log = writer_open()
        with mock.patch.object(AB, "open", fake, create=True):
            with self.assertRaisesRegex(AB.B58HError, rf"^{re.escape(kept)} exists: .*; nothing is written \(this "
                                        rf"call's files removed: {re.escape(self.outs[0][0])}\)$"):
                AB._write_all([self.outs[0], (kept, "NEW\n")])
        self.assertEqual(self.left(), ["kept.json"], "the JSON opened before it is removed")
        self.assertTrue(log[0][1].closed)
        self.assertEqual(read_text(kept), "KEPT")

    def test_an_open_that_fails_with_any_os_error_is_refused_and_removes_what_was_opened(self):
        err = OSError(errno.EINVAL, "SYNTHETIC: an invalid file name", self.outs[1][0])
        self.assertIs(type(err), OSError, "control: no subclass of OSError, PermissionError among them")
        fake, log = writer_open(refuse=(self.outs[1][0], err))
        with mock.patch.object(AB, "open", fake, create=True):
            with self.assertRaisesRegex(AB.B58HError, rf"^{re.escape(self.outs[1][0])}: cannot be created \(\[Errno "
                                        rf"{errno.EINVAL}\] SYNTHETIC: an invalid file name: .*\); nothing is "
                                        rf"written \(this call's files removed: {re.escape(self.outs[0][0])}\)$"):
                AB._write_all(self.outs)
        self.assertEqual(self.left(), [])
        self.assertTrue(log[0][1].closed)

    def test_a_write_that_fails_is_refused_and_removes_every_file_this_call_opened(self):
        """A full disk on either file: the refusal names that file, and neither file is left, the JSON written in
        full before the report's write failed among them (R3M-1: a JSON kept would block the rerun)."""
        for i in (0, 1):
            bad = self.outs[i][0]
            fake, log = writer_open(full=(bad,))
            with self.subTest(failing=os.path.basename(bad)):
                with mock.patch.object(AB, "open", fake, create=True):
                    with self.assertRaises(AB.B58HError) as cm:
                        AB._write_all(self.outs)
                self.assertEqual(str(cm.exception), f"{bad}: the write failed ([Errno {errno.ENOSPC}] SYNTHETIC: no "
                                 "space left on device); nothing is written (this call's files removed: "
                                 f"{self.outs[0][0]}, {self.outs[1][0]})")
                self.assertEqual(self.left(), [], "no file is left, empty, partly written or written in full")
                self.assertEqual([p for p, _ in log], [p for p, _ in self.outs])
                self.assertTrue(all(fh.closed for _, fh in log), "every handle is closed before its file is removed")
        AB._write_all(self.outs)                                             # control: the same outputs, written
        self.assertEqual(self.left(), ["analysis.json", "analysis.txt"])


# ------------------------------------------------------------------------------------------ intervals and Delta
class Intervals(Study):
    def hand_d(self, ratio, reading, form):
        arms = self.doc["engines"][B]["arms"]
        sig, bl = arms[FEA.arm_name(ratio)]["seeds"], arms["blind"]["seeds"]
        f = T4.scipy_cut if form == "evaluate_form" else hand_mean_cut
        return [f(sig[s][reading]["D"], sig[s][reading]["D_base"]) - f(bl[s][reading]["D"], bl[s][reading]["D_base"])
                for s in sorted(sig, key=int)]

    def test_each_d_and_its_interval_against_a_hand_computation(self):
        for r in FEA.RATIOS:
            for rd in FEA.READINGS:
                for form in ("evaluate_form", "mean_form"):
                    x = self.hand_d(r, rd, form)
                    iv = self.res["intervals"][r][rd][form]
                    ci = stats.ttest_1samp(x, 0.0).confidence_interval(0.95)
                    self.assertAlmostEqual(iv["mean"], statistics.mean(x), places=10)
                    self.assertAlmostEqual(iv["sd"], statistics.stdev(x), places=10)
                    self.assertAlmostEqual(iv["lo"], ci.low, places=10)
                    self.assertAlmostEqual(iv["hi"], ci.high, places=10)
                ev, mf = self.res["intervals"][r][rd]["evaluate_form"], self.res["intervals"][r][rd]["mean_form"]
                self.assertGreater(abs(ev["lo"] - mf["lo"]), 1e-3, "control: the mean form is another interval")
        self.assertIn("t_0.975,19 = 2.0930 (scipy.stats.t)", self.text)


def hand_mean_cut(D, D_base):
    return statistics.mean(100.0 * (1.0 - a / b) for a, b in zip(D, D_base))


class Delta(Study):
    def hand(self, reading, form):
        arms = self.doc["engines"][B]["arms"]
        hi, lo = arms[FEA.arm_name(R_HI)]["seeds"], arms[FEA.arm_name(R_LO)]["seeds"]
        f = T4.scipy_cut if form == "evaluate_form" else hand_mean_cut
        return [f(hi[s][reading]["D"], hi[s][reading]["D_base"]) - f(lo[s][reading]["D"], lo[s][reading]["D_base"])
                for s in sorted(hi, key=int)]

    def test_delta_per_seed_its_interval_and_its_two_sided_sign_test(self):
        for rd in FEA.READINGS:
            for form in ("evaluate_form", "mean_form"):
                x = self.hand(rd, form)
                got = self.res["delta"]["readings"][rd][form]
                for s, v in enumerate(x):
                    self.assertAlmostEqual(got["per_seed"][str(s)], v, places=10)
                ci = stats.ttest_1samp(x, 0.0).confidence_interval(0.95)
                self.assertAlmostEqual(got["interval"]["lo"], ci.low, places=10)
                self.assertAlmostEqual(got["interval"]["hi"], ci.high, places=10)
                k, n = sum(v > 0 for v in x), sum(v != 0 for v in x)
                self.assertAlmostEqual(got["sign_p_two_sided"], stats.binomtest(k, n, 0.5).pvalue, places=12)
                self.assertEqual(got["sign"]["positive"], k)
        x = self.hand("no_knock", "evaluate_form")
        blind_d = [a - b for a, b in zip(self.res["fea"]["primary"]["readings"]["no_knock"]["d"]
                                         [FEA.node(B, R_HI)]["d_per_seed"],
                                         self.res["fea"]["primary"]["readings"]["no_knock"]["d"]
                                         [FEA.node(B, R_LO)]["d_per_seed"])]
        for a, b in zip(x, blind_d):                       # the blinded arm cancels: Delta = d(1.5) - d(0.5)
            self.assertAlmostEqual(a, b, places=10)

    def test_the_prediction_is_read_from_roads_json(self):
        pr = self.res["delta"]["prediction"]
        cu = SYN["c_u"]
        self.assertAlmostEqual(pr["no_knock"]["evaluate_form"], cu[R_HI]["noknock"][0] - cu[R_LO]["noknock"][0],
                               places=14)
        self.assertAlmostEqual(pr["no_knock"]["mean_form"], cu[R_HI]["noknock"][1] - cu[R_LO]["noknock"][1],
                               places=14)
        self.assertAlmostEqual(pr["with_knock"]["evaluate_form"], cu[R_HI]["knock"][0] - cu[R_LO]["knock"][0],
                               places=14)
        self.assertAlmostEqual(pr["with_knock"]["mean_form"], cu[R_HI]["knock"][1] - cu[R_LO]["knock"][1], places=14)
        self.assertNotAlmostEqual(pr["with_knock"]["evaluate_form"], pr["no_knock"]["evaluate_form"], places=6)
        self.assertNotAlmostEqual(cu[R_LO]["knock"][1], cu[R_LO]["noknock"][1], places=6)     # control: readings differ
        self.assertIn(f"{pr['with_knock']['evaluate_form']:+.4f} in evaluate.py's form, "
                      f"{cu[R_HI]['knock'][1] - cu[R_LO]['knock'][1]:+.4f} in the mean form", self.text)

    def test_the_two_sided_sign_p_is_printed_as_four_engine_analysis_prints_it(self):
        """C9 (F5): p below 1e-4 in e-notation at 2 significant digits, where a 4-decimal format reads 0.0000."""
        records = {"c_u": {r: {rd: {"evaluate_form": 0.0, "mean": 0.0} for rd in FEA.READINGS} for r in FEA.RATIOS}}
        d15, d05 = exact(9.0, 1.0, 1), exact(1.0, 1.0, 2)
        doc = cuts_doc(self.root, [30.0] * N, {R_HI: [30.0 + v for v in d15], R_LO: [30.0 + v for v in d05]})
        self.assertEqual(sum(a > b for a, b in zip(d15, d05)), N)                     # every Delta above 0
        p = stats.binomtest(N, N, 0.5).pvalue
        self.assertEqual((f"{p:.1e}", f"{p:.4f}"), ("1.9e-06", "0.0000"))
        line = [s for s in AB._block_delta(AB.delta(checked_of(doc), records))
                if s.startswith("  no knock, evaluate.py's form: ")][0]
        self.assertTrue(line.endswith(f"exact two-sided sign test: {N} positive, 0 negative, 0 zero, p 1.9e-06"), line)

    def test_the_statements_are_printed(self):
        for s in ("Delta's spread is UNKNOWN", "a Delta interval covering 0 says nothing about preview value across H",
                  "Delta decides nothing about the criterion", "exploratory"):
            self.assertIn(s, self.text)

    def test_an_interval_covers_0_only_when_it_holds_0_and_says_which(self):
        """PR-B:699-701: one that covers 0 says nothing; one that excludes it, below or above, says the sighted cut
        differed. The interval checked against scipy's, the words against the flag."""
        records = {"c_u": {r: {rd: {"evaluate_form": 0.0, "mean": 0.0} for rd in FEA.READINGS} for r in FEA.RATIOS}}
        for d15, d05, covers in ((exact(-5.0, 1.0, 1), exact(5.0, 1.0, 2), False),
                                 (exact(5.0, 1.0, 1), exact(-5.0, 1.0, 2), False),
                                 (exact(0.0, 1.0, 1), exact(0.0, 1.0, 2), True)):
            doc = cuts_doc(self.root, [30.0] * N, {R_HI: [30.0 + v for v in d15], R_LO: [30.0 + v for v in d05]})
            dl = AB.delta(checked_of(doc), records)
            x = dl["readings"]["no_knock"]["evaluate_form"]
            ci = stats.ttest_1samp([a - b for a, b in zip(d15, d05)], 0.0).confidence_interval(0.95)
            self.assertEqual(ci.low <= 0.0 <= ci.high, covers)                      # the case is the one named
            self.assertEqual(x["covers_0"], covers)
            line = [s for s in AB._block_delta(dl) if s.startswith("  no knock, evaluate.py's form: ")][0]
            self.assertIn("(covers 0)" if covers else "(excludes 0: the sighted cut differed", line)


# ------------------------------------------------------------------------------------------ 9.1
def fake_sc(doc):
    return {"doc": doc, "checked": checked_of(doc)}


class Delivery(Case):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.root = tmpdir(cls)
        write_records(cls.root)
        cls.doc = study_doc(cls.root)
        cls.block = cls.doc["provenance"]["delivery"]
        cls.dv = AB.delivery(fake_sc(cls.doc))

    def hand(self, entry):
        base = self.block["hand"][AB.BASELINE]["fuel"]
        fuel = statistics.mean(100.0 * (f / b - 1.0) for f, b in zip(entry["fuel"], base))
        shares = [s / d for s, d in zip(entry["short_steps"], entry["demand_steps"]) if d]
        return fuel, (statistics.mean(shares) if shares else None)

    def test_each_seeds_figures_against_a_hand_computation(self):
        base = self.block["hand"][AB.BASELINE]["fuel"]
        for arm in AB.ARMS:
            for s in ("0", "5", "19"):
                e = self.block["arms"][arm][s]
                f = self.dv["arms"][arm]["per_seed"][s]
                fuel, share = self.hand(e)
                self.assertAlmostEqual(f["fuel_figure"], fuel, places=10)
                self.assertAlmostEqual(f["mean_short_share"], share, places=12)
                self.assertAlmostEqual(f["pooled_short_share"], sum(e["short_steps"]) / sum(e["demand_steps"]),
                                       places=12)
                pooled_ratio = 100.0 * (sum(e["fuel"]) / sum(base) - 1.0)
                self.assertGreater(abs(pooled_ratio - fuel), 1e-6, "control: a pooled-ratio fuel figure")
                zeros = statistics.mean((x / d if d else 0.0) for x, d in zip(e["short_steps"], e["demand_steps"]))
                self.assertGreater(abs(zeros - share), 1e-6, "control: roads without demand counted as 0")
                self.assertGreater(abs(f["pooled_short_share"] - share), 1e-9, "control: pooled is not the mean")
                worst = max(x / d for x, d in zip(e["short_steps"], e["demand_steps"]) if d)
                self.assertEqual(f["worst_roads"], [k for k, (x, d) in enumerate(zip(e["short_steps"],
                                                                                    e["demand_steps"]))
                                                    if d and x / d == worst])

    def test_ties_are_listed_and_a_seed_without_demand_is_named(self):
        self.assertEqual(self.dv["arms"]["sighted_r1.5"]["per_seed"]["3"]["worst_roads"], [2, 9])
        blind = self.dv["arms"]["blind"]
        self.assertEqual(blind["no_demand_seeds"], ["7"])
        self.assertIsNone(blind["per_seed"]["7"]["mean_short_share"])
        self.assertEqual(blind["per_seed"]["7"]["worst_roads"], [])
        self.assertEqual(blind["mean_short_share"]["n"], N - 1)
        self.assertEqual(blind["fuel_figure"]["n"], N)

    def test_each_arms_statistics_and_its_worst_road_over_every_seed(self):
        for arm in AB.ARMS:
            a = self.dv["arms"][arm]
            fuels = [self.hand(self.block["arms"][arm][str(s)])[0] for s in range(N)]
            shares = [self.hand(self.block["arms"][arm][str(s)])[1] for s in range(N)]
            shares = [x for x in shares if x is not None]
            for got, xs in ((a["fuel_figure"], fuels), (a["mean_short_share"], shares)):
                self.assertAlmostEqual(got["median"], statistics.median(xs), places=10)
                self.assertAlmostEqual(got["mean"], statistics.mean(xs), places=10)
                self.assertAlmostEqual(got["min"], min(xs), places=10)
                self.assertAlmostEqual(got["max"], max(xs), places=10)
            pairs = [(s, k, e["short_steps"][k] / e["demand_steps"][k]) for s in range(N)
                     for e in [self.block["arms"][arm][str(s)]] for k in range(FEA.N_ROADS) if e["demand_steps"][k]]
            top = max(v for _, _, v in pairs)
            self.assertEqual(a["worst"]["at"], [[s, k] for s, k, v in pairs if v == top])
        self.assertEqual(self.dv["arms"]["sighted_r1.5"]["worst"]["at"], [[3, 2], [3, 9]])
        last = FEA.N_ROADS - 1                      # the last road is searched too (a range that stops one short)
        self.assertEqual(self.dv["arms"]["blind"]["worst"], {"share": 1.0, "at": [[0, last]]})
        self.assertEqual(self.dv["arms"]["blind"]["per_seed"]["0"]["worst_roads"], [last])

    def test_the_baseline_ecus_and_current_grades_own_figures_beside(self):
        self.assertEqual(self.dv["beside"][AB.BASELINE]["fuel_figure"], 0.0)
        fuel, share = self.hand(self.block["hand"][AB.CURRENT_GRADE])
        self.assertAlmostEqual(self.dv["beside"][AB.CURRENT_GRADE]["fuel_figure"], fuel, places=10)
        self.assertAlmostEqual(self.dv["beside"][AB.CURRENT_GRADE]["mean_short_share"], share, places=12)
        self.assertNotIn("reactive", self.dv["beside"])
        self.assertEqual(self.dv["label"], "no reading: fuel and torque hold no damage")

    def test_each_refusal_of_the_block(self):
        AB.validate_delivery(self.block, checked_of(self.doc), FEA.N_ROADS)       # control: the block passes

        def mut(f):
            b = copy.deepcopy(self.block)
            f(b)
            return b
        cases = [
            (None, "an object is required"),
            (mut(lambda b: b.pop("rule")), "exactly"),
            (mut(lambda b: b["hand"].pop(AB.CURRENT_GRADE)), "current-grade"),
            (mut(lambda b: b["arms"].pop("blind")), "arms"),
            (mut(lambda b: b["arms"]["blind"].pop("3")), "seeds are not the scores'"),
            (mut(lambda b: b["arms"]["blind"]["0"]["fuel"].pop()), "20 roads required"),
            (mut(lambda b: b["arms"]["blind"]["0"].pop("short_share")), "keys"),
            (mut(lambda b: b["hand"][AB.BASELINE]["fuel"].__setitem__(4, 0.0)), "the fuel figure divides"),
            (mut(lambda b: b["arms"]["blind"]["0"]["fuel"].__setitem__(1, float("nan"))), "finite"),
            (mut(lambda b: b["arms"]["blind"]["0"]["demand_steps"].__setitem__(1, -1)), "at least 0"),
            (mut(lambda b: b["arms"]["blind"]["0"]["demand_steps"].__setitem__(1, True)), "at least 0"),
            (mut(lambda b: b["arms"]["blind"]["0"]["short_steps"].__setitem__(1, 10 ** 6)), "short steps among"),
            (mut(lambda b: b["arms"]["blind"]["0"]["short_share"].__setitem__(0, 0.0)), "null required"),
            (mut(lambda b: b["arms"]["blind"]["0"]["short_share"].__setitem__(1, 0.123)), "short / demand"),
            (mut(lambda b: b["hand"]["reactive"]["short_share"].__setitem__(1, None)), "finite"),
            # the last road is checked too (a loop that stops one road short accepts these)
            (mut(lambda b: b["arms"]["blind"]["0"]["short_share"].__setitem__(-1, 0.75)), r"short_share\[19\]"),
            (mut(lambda b: b["arms"]["blind"]["0"]["fuel"].__setitem__(-1, float("inf"))), r"fuel\[19\]"),
            (mut(lambda b: b["hand"][AB.BASELINE]["fuel"].__setitem__(-1, -1.0)), r"fuel\[19\].*divides"),
            (mut(lambda b: b.__setitem__("rule", "SYNTHETIC rule as text")), r"provenance\.delivery\.rule: an object"),
        ]
        self.assertEqual(FEA.N_ROADS, 20)                               # road 19 is the last
        for block, pattern in cases:
            with self.assertRaisesRegex(AB.B58HError, pattern):
                AB.validate_delivery(block, checked_of(self.doc), FEA.N_ROADS)
        # C10's tolerance, 1e-12 on short / demand: 1e-6 off is refused, 1e-13 off is accepted
        k = next(i for i, dm in enumerate(self.block["arms"]["blind"]["1"]["demand_steps"]) if dm)
        share = self.block["arms"]["blind"]["1"]["short_share"][k]

        def off(e):
            return mut(lambda b: b["arms"]["blind"]["1"]["short_share"].__setitem__(k, share + e))
        with self.assertRaisesRegex(AB.B58HError, rf"blind\.1\.short_share\[{k}\]: .*short / demand"):
            AB.validate_delivery(off(1e-6), checked_of(self.doc), FEA.N_ROADS)
        AB.validate_delivery(off(1e-13), checked_of(self.doc), FEA.N_ROADS)

    def test_a_refused_block_is_reported_and_the_analysis_still_runs(self):
        bad = copy.deepcopy(self.block)
        bad["hand"].pop(AB.BASELINE)
        root, scores = make_repo(tmpdir(self), doc=lambda r: study_doc(r, delivery=bad))
        ctx, out, rep = run_both(root, scores)
        res, text = load(out), read_text(rep)
        self.assertEqual(set(res["delivery"]), {"refused", "label"})
        self.assertTrue(res["delivery"]["refused"].startswith("REFUSED: provenance.delivery.hand"))
        block = text[text.index("\nSECTION 9.1"):text.index("\nSECTION 10")]
        self.assertIn("REFUSED: provenance.delivery.hand", block)
        self.assertNotIn("fuel figure", block)
        for h in ("SECTION 7: THE VERDICTS", "INTERVALS", "DELTA", "THE B58'S MODEL BAND", "SECTION 10"):
            self.assertIn(h, text)
        self.assertEqual(sorted(res["fea"]), sorted(AB.RUNS))


# ------------------------------------------------------------------------------------------ section 7 and the corners
CK_IN_PROCESS = {R_LO: 2.625, R_HI: 2.875}       # the ceiling's with-knock reading beside in_process's C of 3.0 (G11)


def in_process(doc, *, kappa_e8=3.0, kappa_l1=None):
    """The five FEA runs and AB's blocks without the records' repository: the context from
    test_four_engine_analysis.synthetic_context, its band AB's PRIMARY."""
    records = {"kappa_e8": kappa_e8, "kappa_l1": kappa_l1 or {"mazda_25t": 1.5, "honda_l15b7": 1.9, "ford_27tt": 3.5}}
    checked = checked_of(doc)
    bd = AB.bands(checked["engines"][B], records)
    ctx = T4.synthetic_context(engines=(B,), n=N, s_p=20.0, ceiling=3.0)
    ctx["model_band"] = bd["model_band"]["primary"]
    results = AB.fea_runs(doc, ctx, bd, {})
    AB.check_verdicts_fixed(results)
    fl = AB.flags(results)
    ivs = AB.intervals(results["primary"])
    return results, bd, fl, ivs, AB.sentences(results, ivs, fl, bd, CK_IN_PROCESS)


def exact(mean, sd, seed):
    """N values with exactly this mean and sample sd."""
    z = np.random.default_rng(seed).standard_normal(N)
    z = (z - z.mean()) / z.std(ddof=1)
    return list(mean + sd * z)


def hand_graph(x15, x05, alpha=0.05):
    """PR-B 6.2's one-engine graph from its words: r = 1.5 at alpha; r = 0.5 at alpha only when r = 1.5 rejects."""
    p15 = stats.ttest_1samp(x15, 0.0, alternative="greater").pvalue
    p05 = stats.ttest_1samp(x05, 0.0, alternative="greater").pvalue
    hi = p15 <= alpha
    return {R_HI: bool(hi), R_LO: bool(hi and p05 <= alpha)}


class Corners(Case):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.root = tmpdir(cls)
        write_records(cls.root)
        cls.d15, cls.d05 = exact(2.0, 1.0, 21), exact(3.0, 1.0, 22)
        blind = [30.0] * N
        cls.doc = cuts_doc(cls.root, blind, {R_HI: [30.0 + v for v in cls.d15], R_LO: [30.0 + v for v in cls.d05]})
        cls.results, cls.bd, cls.fl, cls.ivs, cls.sent = in_process(cls.doc)

    def test_every_runs_t_flags_against_a_hand_graph(self):
        base = hand_graph(self.d15, self.d05)
        for name in AB.RUNS:
            mb = self.bd["model_band"][name][B]
            corner = {sgn: hand_graph([v + sgn * mb[R_HI]["no_knock"] for v in self.d15],
                                      [v + sgn * mb[R_LO]["no_knock"] for v in self.d05]) for sgn in (-1, 1)}
            for r in FEA.RATIOS:
                got = self.fl[f"no_knock d>0 (t) {FEA.node(B, r)}"][name]
                self.assertEqual(got["d_gt_0"], base[r])
                self.assertEqual(got["model_limited"], any(corner[sgn][r] != base[r] for sgn in (-1, 1)), (name, r))

    def test_the_other_reading_alone_flags_r15_and_the_sentence_says_so(self):
        key = f"no_knock d>0 (t) {FEA.node(B, R_HI)}"
        runs = self.fl[key]
        self.assertTrue(runs["primary"]["d_gt_0"])
        self.assertFalse(runs["primary"]["model_limited"])                    # control: the primary does not flag
        self.assertTrue(runs["other_at_b"]["model_limited"])
        self.assertFalse(runs["version_5"]["model_limited"])                  # a band of 0 never flags
        s = self.sent[R_HI]
        self.assertEqual(s["verdict"], "d > 0, MODEL-LIMITED under the other reading of 'at b'")
        self.assertIn("n = 20 seeds per arm), MODEL-LIMITED under the other reading of 'at b'. Exploratory",
                      s["text"][0])

    def test_a_verdict_that_depends_on_the_assumed_b_is_printed_by_name(self):
        key = f"no_knock d>0 (t) {FEA.node(B, R_HI)}"
        runs = self.fl[key]
        self.assertNotEqual(runs["primary"]["model_limited"], runs["companion_max"]["model_limited"])
        self.assertIn(key, AB.companion_named(self.fl))
        line = [x for x in self.sent[R_HI]["text"] if x.startswith(f"companion, printed by name (PR-B 6.6): '{key}'")]
        self.assertEqual(len(line), 1)
        self.assertIn("under kappa 1 no; under mazda_25t's kappa 1.5000 yes; under ford_27tt's kappa 3.5000 yes",
                      line[0])

    def test_printed_by_name_when_either_companion_alone_differs(self):
        """G1 on a table of flags written here: a verdict is named when its flag under kappa 1 differs from either
        companion's, or the two companions' differ; never when all three agree."""
        named = {(False, False, True): True, (False, True, False): True, (True, False, False): True,
                 (True, True, False): True, (False, True, True): True, (True, False, True): True,
                 (False, False, False): False, (True, True, True): False}
        fl = {}
        for i, (p, lo, hi) in enumerate(named):
            fl[f"case {i}"] = {name: {"model_limited": v, "d_gt_0": True, "at_minus_band": True, "at_plus_band": True}
                               for name, v in (("primary", p), ("companion_min", lo), ("companion_max", hi),
                                               ("other_at_b", False), ("version_5", False))}
        want = [f"case {i}" for i, key in enumerate(named) if named[key]]
        self.assertEqual(sorted(AB.companion_named(fl)), want)

    def test_a_large_d_flags_nothing_and_names_nothing(self):
        doc = cuts_doc(self.root, [30.0] * N, {R_HI: [30.0 + v for v in exact(9.0, 1.0, 5)],
                                               R_LO: [30.0 + v for v in exact(9.0, 1.0, 6)]})
        results, bd, fl, ivs, sent = in_process(doc)
        t_keys = [k for k in fl if "(t)" in k]
        self.assertEqual(len(t_keys), 4)
        self.assertFalse(any(fl[k][n]["model_limited"] for k in t_keys for n in AB.RUNS))
        self.assertEqual([k for k in AB.companion_named(fl) if "(t)" in k], [])
        self.assertEqual(sent[R_HI]["verdict"], "d > 0")
        self.assertNotIn("MODEL-LIMITED", sent[R_HI]["text"][0])


class Sentences(Case):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.root = tmpdir(cls)
        write_records(cls.root)

    def run_cuts(self, d15, d05):
        doc = cuts_doc(self.root, [30.0] * N, {R_HI: [30.0 + v for v in d15], R_LO: [30.0 + v for v in d05]})
        return in_process(doc)

    def test_d_gt_0_sentence_is_section_7s_filled(self):
        results, bd, fl, ivs, sent = self.run_cuts(exact(9.0, 1.0, 1), exact(9.0, 1.0, 2))
        row = results["primary"]["readings"]["no_knock"]["d"][FEA.node(B, R_HI)]
        iv = ivs[R_HI]["no_knock"]["evaluate_form"]
        want = ("On decision 34's roads, B58 agents that saw the grade H = 1.5 x tau ahead took less simulated turbine "
                "and oil damage (the no-knock reading) on the B58 model, which is not validated (its band assumed at "
                "b; section 12.1), than their blinded twins (paired t under the graph, adjusted p = "
                f"{FEA._p(row['t']['adjusted_p'])}; d = {row['t']['mean']:+.2f} points, two-sided 95 % t interval "
                f"{iv['lo']:+.2f} to {iv['hi']:+.2f}, against an MEI of 5.43 points; n = 20 seeds per arm). "
                "Exploratory, on one plant; not a test of the H/tau criterion.")
        self.assertEqual(sent[R_HI]["text"][0], want)
        self.assertEqual(sent[R_LO]["verdict"], "d > 0")
        beside = sent[R_HI]["text"][1]
        self.assertIn(f"the band Delta_e {row['band']:.2f} points under the primary reading", beside)
        self.assertIn(f"the ceiling C(1.5) {row['ceiling']:.2f} points", beside)
        self.assertIn("the MEI 5.43 points", beside)
        self.assertTrue(sent[R_HI]["text"][2].startswith("[with knock, not converged in dt on these roads: d +9.00"))
        sign = sent[R_HI]["text"][3]
        self.assertTrue(sign.startswith("the sign test, the declared secondary, in its own words: 20 of 20"))
        self.assertNotIn("disagree", sign)                                   # control: here the two tests agree

    def test_r05_reads_not_shown_at_r05_when_r15_does_not_reject_and_below_0_is_said(self):
        results, bd, fl, ivs, sent = self.run_cuts(exact(-3.0, 1.0, 3), exact(4.0, 1.0, 4))
        t05 = results["primary"]["readings"]["no_knock"]["d"][FEA.node(B, R_LO)]["t"]
        self.assertLess(t05["p"], 0.05)                                      # rejects unadjusted ...
        self.assertFalse(t05["d_gt_0"])                                      # ... and the graph gives it no alpha
        self.assertTrue(sent[R_LO]["verdict"].startswith(
            f"d > 0 not shown at r = 0.5 (the r = 1.5 test did not reject, so the graph gives this test no alpha; "
            f"its unadjusted p {FEA._p(t05['p'])})"))
        self.assertTrue(sent[R_LO]["text"][0].startswith("The study does not show a preview effect at H = 0.5 x tau"))
        self.assertEqual(sent[R_HI]["verdict"], "d > 0 not shown")
        below = [x for x in sent[R_HI]["text"] if x.startswith("The sighted agents at r = 1.5 took more")]
        self.assertEqual(len(below), 1)
        self.assertIn("never evidence that preview is worthless", below[0])
        self.assertFalse(any(x.startswith("The sighted agents") for x in sent[R_LO]["text"]),
                         "control: an interval above 0 says nothing of the kind")

    def test_r05_reads_plain_not_shown_when_r15_rejected_and_its_own_test_did_not(self):
        """PR-B:693-694's clause is for an r = 1.5 test that did not reject; here it rejected, so r = 0.5 had its
        alpha and reads as its own test does (a headline keyed on the r = 0.5 test would add the false clause)."""
        results, bd, fl, ivs, sent = self.run_cuts(exact(9.0, 1.0, 5), exact(-3.0, 1.0, 3))
        P = results["primary"]["readings"]["no_knock"]["d"]
        self.assertTrue(P[FEA.node(B, R_HI)]["t"]["d_gt_0"])
        self.assertFalse(P[FEA.node(B, R_LO)]["t"]["d_gt_0"])
        self.assertEqual(sent[R_HI]["verdict"], "d > 0")
        self.assertEqual(sent[R_LO]["verdict"], "d > 0 not shown")
        below = [x for x in sent[R_LO]["text"] if x.startswith("The sighted agents at r = 0.5 took more")]
        self.assertEqual(len(below), 1)

    def test_the_sign_test_is_printed_in_its_own_words_and_a_disagreement_said(self):
        d15 = [-0.5] * 15 + [10.0] * 5                                       # t rejects; 5 of 20 above 0 does not
        results, bd, fl, ivs, sent = self.run_cuts(d15, exact(3.0, 1.0, 9))
        row = results["primary"]["readings"]["no_knock"]["d"][FEA.node(B, R_HI)]
        self.assertTrue(row["t"]["d_gt_0"])
        self.assertFalse(row["sign"]["d_gt_0"])
        iv = ivs[R_HI]["no_knock"]["evaluate_form"]
        self.assertLess(iv["lo"], 0.0)                                       # an interval that covers 0 ...
        self.assertGreater(iv["hi"], 0.0)
        self.assertFalse(any(x.startswith("The sighted agents") for x in sent[R_HI]["text"]),
                         "an interval that covers 0 is not wholly below 0 (PR-B:685)")
        line = [x for x in sent[R_HI]["text"] if x.startswith("the sign test, the declared secondary")][0]
        self.assertIn("5 of 20 differences above 0", line)
        self.assertIn("it and the t-test disagree: both are reported, and the t-test's verdict stands", line)
        # at r = 0.5 the sign test's own graph gives it no alpha (its r = 1.5 test did not reject), so it does not
        # show d > 0 with 20 of 20 above 0, while the t-test, whose r = 1.5 test rejected, does: they disagree too
        line05 = [x for x in sent[R_LO]["text"] if x.startswith("the sign test, the declared secondary")][0]
        self.assertIn("20 of 20 differences above 0", line05)
        self.assertIn("it does not show d > 0 under its own graph", line05)
        self.assertIn("disagree", line05)
        # the t-test's r = 0.5 verdict holds, MODEL-LIMITED: at d - Delta_e its r = 1.5 test no longer rejects, so
        # the graph's corner gives r = 0.5 no alpha (four_engine_analysis's corners re-run the graph)
        self.assertEqual(sent[R_LO]["verdict"], "d > 0, MODEL-LIMITED")
        self.assertFalse(fl[f"no_knock d>0 (t) {FEA.node(B, R_HI)}"]["primary"]["at_minus_band"])


class TwoReadings(Case):
    """Section 7's sentences on documents whose two readings and two forms differ (readings_doc): a sentence that
    took its d, interval, adjusted p, flag, r = 0.5 rule or below-0 test from the wrong reading, form or run gives
    another text here, while on scores_from_cuts' documents it could not."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.root = tmpdir(cls)
        write_records(cls.root)
        # no knock: the Corners case, which the other reading of 'at b' alone flags at r = 1.5; with knock: d 9
        cls.nk, cls.wk = (exact(2.0, 1.0, 21), exact(3.0, 1.0, 22)), (exact(9.0, 1.0, 5), exact(9.0, 1.0, 6))
        cls.doc = two_readings(cls.root, cls.nk, cls.wk)
        cls.results, cls.bd, cls.fl, cls.ivs, cls.sent = in_process(cls.doc)

    def row(self, reading, r, run="primary"):
        return self.results[run]["readings"][reading]["d"][FEA.node(B, r)]

    def test_the_document_separates_the_readings_and_the_forms(self):
        for r, i in ((R_HI, 0), (R_LO, 1)):
            nk, wk = self.row("no_knock", r), self.row("with_knock", r)
            self.assertAlmostEqual(nk["t"]["mean"], statistics.mean(self.nk[i]), places=10)   # evaluate.py's form
            self.assertAlmostEqual(wk["t"]["mean"], statistics.mean(self.wk[i]), places=10)
            self.assertGreater(abs(nk["d_mean_form"] - nk["t"]["mean"]), 0.1)                # the forms differ
            self.assertGreater(abs(wk["d_mean_form"] - wk["t"]["mean"]), 0.1)
            self.assertNotEqual(FEA._p(nk["t"]["adjusted_p"]), FEA._p(wk["t"]["adjusted_p"]))
        ml = {rd: (self.fl[f"{rd} d>0 (t) {FEA.node(B, R_HI)}"]["primary"]["model_limited"],
                   self.fl[f"{rd} d>0 (t) {FEA.node(B, R_HI)}"]["other_at_b"]["model_limited"]) for rd in FEA.READINGS}
        self.assertEqual(ml, {"no_knock": (False, True), "with_knock": (False, False)})

    def test_the_sentence_quotes_evaluates_form_and_its_own_readings_flag(self):
        for r in (R_HI, R_LO):
            row, iv, mf = self.row("no_knock", r), self.ivs[r]["no_knock"]["evaluate_form"], \
                self.ivs[r]["no_knock"]["mean_form"]
            self.assertNotEqual(f"{iv['lo']:+.2f}", f"{mf['lo']:+.2f}")                    # control: the forms differ
            first = self.sent[r]["text"][0]
            self.assertIn(f"adjusted p = {FEA._p(row['t']['adjusted_p'])}; d = {row['t']['mean']:+.2f} points, "
                          f"two-sided 95 % t interval {iv['lo']:+.2f} to {iv['hi']:+.2f}, against an MEI of 5.43 "
                          "points", first)
            beside = [x for x in self.sent[r]["text"] if x.startswith("beside it: ")]
            self.assertEqual(len(beside), 1)
            self.assertTrue(beside[0].startswith(f"beside it: the mean form {row['d_mean_form']:+.2f} points (95 % "
                                                 f"{mf['lo']:+.2f} to {mf['hi']:+.2f}; decides nothing); the band "
                                                 f"Delta_e {row['band']:.2f} points"), beside[0])
        # the other reading alone flags the no-knock r = 1.5 verdict; its with-knock reading flags nothing
        self.assertEqual(self.sent[R_HI]["verdict"], "d > 0, MODEL-LIMITED under the other reading of 'at b'")
        self.assertIn("n = 20 seeds per arm), MODEL-LIMITED under the other reading of 'at b'. Exploratory",
                      self.sent[R_HI]["text"][0])

    def test_the_with_knock_bracket_is_the_with_knock_readings_own(self):
        for r in (R_HI, R_LO):
            k = self.row("with_knock", r)
            kiv, kmf = self.ivs[r]["with_knock"]["evaluate_form"], self.ivs[r]["with_knock"]["mean_form"]
            other = self.bd["tables"]["other_at_b"][r]["with_knock"]["delta_e"]
            self.assertFalse(self.fl[f"with_knock d>0 (t) {FEA.node(B, r)}"]["other_at_b"]["model_limited"])
            want = (f"[with knock, not converged in dt on these roads: d {k['t']['mean']:+.2f} points, 95 % "
                    f"{kiv['lo']:+.2f} to {kiv['hi']:+.2f}, adjusted p {FEA._p(k['t']['adjusted_p'])}: d > 0; its "
                    f"mean form {k['d_mean_form']:+.2f} points (95 % {kmf['lo']:+.2f} to {kmf['hi']:+.2f}; decides "
                    f"nothing); its band Delta_e {k['band']:.2f} points under the primary reading of 'at b' "
                    f"({other:.2f} under the other, 0 under version 5's); the ceiling's with-knock reading "
                    f"{CK_IN_PROCESS[r]:.2f} points (roads.json a.knock.mean, beside C, the no-knock reading's); the "
                    "MEI as above]")
            self.assertEqual([x for x in self.sent[r]["text"] if x.startswith("[with knock")], [want])
            self.assertNotAlmostEqual(k["band"], self.row("no_knock", r)["band"], places=3)  # control

    def test_r05_reads_through_the_no_knock_graph_and_below_0_is_evaluates_form(self):
        """r = 1.5 does not reject without knock and does with knock: r = 0.5 reads 'not shown at r = 0.5' by the
        no-knock graph. At r = 0.5 evaluate.py's interval covers 0 and the mean form's lies below 0: no below-0
        sentence (PR-B:685 reads the verdict's interval), and the mean form says so in its own bracket (G7)."""
        doc = two_readings(self.root, (exact(-3.0, 1.0, 3), exact(0.3, 1.0, 4)), self.wk, top=(1.0, 2.0))
        results, bd, fl, ivs, sent = in_process(doc)
        P = results["primary"]["readings"]
        self.assertFalse(P["no_knock"]["d"][FEA.node(B, R_HI)]["t"]["d_gt_0"])
        self.assertTrue(P["with_knock"]["d"][FEA.node(B, R_HI)]["t"]["d_gt_0"])          # control: they disagree
        t05 = P["no_knock"]["d"][FEA.node(B, R_LO)]["t"]
        self.assertEqual(sent[R_LO]["verdict"], "d > 0 not shown at r = 0.5 (the r = 1.5 test did not reject, so the "
                         f"graph gives this test no alpha; its unadjusted p {FEA._p(t05['p'])})")
        iv, mf = ivs[R_LO]["no_knock"]["evaluate_form"], ivs[R_LO]["no_knock"]["mean_form"]
        self.assertTrue(iv["lo"] < 0.0 < iv["hi"] and mf["hi"] < 0.0, (iv, mf))          # the case is the one named
        self.assertFalse(any(x.startswith("The sighted agents") for x in sent[R_LO]["text"]))
        beside = [x for x in sent[R_LO]["text"] if x.startswith("beside it: ")][0]
        self.assertIn(f"(95 % {mf['lo']:+.2f} to {mf['hi']:+.2f}; wholly below 0; decides nothing)", beside)
        hi = ivs[R_HI]["no_knock"]["evaluate_form"]
        below = [x for x in sent[R_HI]["text"] if x.startswith("The sighted agents at r = 1.5 took more")]
        self.assertEqual(len(below), 1)
        self.assertIn(f"d = {hi['mean']:+.2f} points, two-sided 95 % t interval {hi['lo']:+.2f} to {hi['hi']:+.2f}",
                      below[0])

    def test_a_sign_verdict_is_flagged_in_its_own_words_under_either_reading_of_at_b(self):
        """PR-B:556 (either test) and :583-584 (every verdict): the sign test's words carry MODEL-LIMITED, or
        MODEL-LIMITED under the other reading of 'at b' when that reading alone flags it; its with-knock reading
        in brackets carries its own flag."""
        cases = (([1.5] * 15 + [-1.0] * 5, "other_at_b", ", MODEL-LIMITED under the other reading of 'at b'"),
                 ([0.5] * 15 + [-1.0] * 5, "primary", ", MODEL-LIMITED"))
        for d, who, flag in cases:
            results, bd, fl, ivs, sent = in_process(two_readings(self.root, (d, d), self.wk))
            runs = fl[f"no_knock d>0 (sign) {FEA.node(B, R_HI)}"]
            self.assertTrue(runs["primary"]["d_gt_0"])
            self.assertEqual((runs["primary"]["model_limited"], runs["other_at_b"]["model_limited"]),
                             (who == "primary", True), who)
            k = fl[f"with_knock d>0 (sign) {FEA.node(B, R_HI)}"]
            self.assertFalse(k["primary"]["model_limited"] or k["other_at_b"]["model_limited"])
            line = [x for x in sent[R_HI]["text"] if x.startswith("the sign test, the declared secondary")]
            self.assertEqual(len(line), 1)
            main, bracket = line[0].split(" [with knock, not converged in dt on these roads: ")
            self.assertTrue(main.startswith("the sign test, the declared secondary, in its own words: 15 of 20 "
                                            "differences above 0 (0 zero, dropped)"), main)
            self.assertIn(f"it shows d > 0 under its own graph{flag}", main)
            if who == "primary":
                self.assertNotIn("under the other reading", main)
            self.assertTrue(bracket.startswith("20 of 20 differences above 0 (0 zero, dropped)"), bracket)
            self.assertTrue(bracket.endswith("it shows d > 0 under its own graph]"), bracket)


# ------------------------------------------------------------------------------------------ section 7, every line
ML_PRIMARY_WORDS = (", MODEL-LIMITED: it changes within the B58's model band, so the plant's unvalidated model, not "
                    "the agents, may decide it (row 113 (6))")                        # PR-B:684, in ASCII
ML_OTHER_WORDS = ", MODEL-LIMITED under the other reading of 'at b'"                 # PR-B:583-584
ML_AFTER = ", MODEL-LIMITED"                                                        # after a verdict (G8)
WK = "[with knock, not converged in dt on these roads: "


def doc_d(doc, ratio, reading, form):
    """Each seed's d from the raw road lists: statistics.median's cut (evaluate.py's form) or the mean of the road
    points (the mean form)."""
    arms = doc["engines"][B]["arms"]
    sig, bl = arms[FEA.arm_name(ratio)]["seeds"], arms["blind"]["seeds"]
    f = T4.scipy_cut if form == "evaluate_form" else hand_mean_cut
    return [f(sig[s][reading]["D"], sig[s][reading]["D_base"]) - f(bl[s][reading]["D"], bl[s][reading]["D_base"])
            for s in sorted(sig, key=int)]


def one_sided(test, x):
    """scipy's one-sided p of d > 0: the paired t-test, or the exact sign test (zeros dropped, p = 1 if none
    is left)."""
    if test == "t":
        return float(stats.ttest_1samp(x, 0.0, alternative="greater").pvalue)
    k, n = sum(v > 0 for v in x), sum(v != 0 for v in x)
    return float(stats.binomtest(k, n, 0.5, alternative="greater").pvalue) if n else 1.0


def graph(doc, reading, test, r):
    """PR-B 6.2's one-engine graph from its words, on the raw road lists: r = 1.5's adjusted p is its own p, and r =
    0.5's the larger of the two (its alpha passes only when r = 1.5 rejects). (unadjusted p, adjusted p, d > 0)."""
    p = {rr: one_sided(test, doc_d(doc, rr, reading, "evaluate_form")) for rr in FEA.RATIOS}
    adj = p[R_HI] if r == R_HI else max(p[R_HI], p[R_LO])
    return p[r], adj, adj <= 0.05


def ci(x):
    return stats.ttest_1samp(x, 0.0).confidence_interval(0.95)


def flag_words(runs, primary_words):
    """G8: the primary run's flag, else the other reading's alone, else nothing."""
    if runs["primary"]["model_limited"]:
        return primary_words
    return ML_OTHER_WORDS if runs["other_at_b"]["model_limited"] else ""


def want_text(doc, fl, bd, r):
    """Section 7's verdict and lines at ratio r, written out from PR-B 7's table and 6.2-6.6's rules on the raw road
    lists, in_process's ceiling (3.0) and the MEI typed here; the flags are the corners' (fl), the bands the tables'."""
    n, mei = FEA.node(B, r), f"{HAND_MEI:g}"

    def below(c):
        return "; wholly below 0" if c.high < 0 else ""

    def band(run, rd):
        return f"{bd['tables'][run][r][rd]['delta_e']:.2f}"
    x, m = doc_d(doc, r, "no_knock", "evaluate_form"), doc_d(doc, r, "no_knock", "mean_form")
    c, cm = ci(x), ci(m)
    p, adj, shown = graph(doc, "no_knock", "t", r)
    runs = fl[f"no_knock d>0 (t) {n}"]
    fill = {"r": r, "p": FEA._p(adj), "d": f"{statistics.mean(x):+.2f}", "lo": f"{c.low:+.2f}",
            "hi": f"{c.high:+.2f}", "mei": mei, "n": N, "flag": flag_words(runs, ML_PRIMARY_WORDS)}
    head_flag = flag_words(runs, ML_AFTER)
    if shown:
        head, lines = "d > 0" + head_flag, [AB.D_GT_0.format(**fill)]
    else:
        head = "d > 0 not shown" + head_flag
        if r == R_LO and not graph(doc, "no_knock", "t", R_HI)[2]:
            head = (f"d > 0 not shown at r = 0.5{head_flag} (the r = 1.5 test did not reject, so the graph gives this "
                    f"test no alpha; its unadjusted p {FEA._p(p)})")
        lines = [AB.NOT_SHOWN.format(**fill)]
    if c.high < 0:
        lines.append(AB.BELOW_ZERO.format(**fill))
    lines.append(f"beside it: the mean form {statistics.mean(m):+.2f} points (95 % {cm.low:+.2f} to {cm.high:+.2f}"
                 f"{below(cm)}; decides nothing); the band Delta_e {band('primary', 'no_knock')} points under the "
                 f"primary reading of 'at b' ({band('other_at_b', 'no_knock')} under the other, 0 under version 5's); "
                 f"the ceiling C({r}) 3.00 points (roads.json, the mean form); the MEI {mei} points")
    kx, km = doc_d(doc, r, "with_knock", "evaluate_form"), doc_d(doc, r, "with_knock", "mean_form")
    kc, kcm = ci(kx), ci(km)
    kadj, kshown = graph(doc, "with_knock", "t", r)[1:]
    kflag = flag_words(fl[f"with_knock d>0 (t) {n}"], ML_AFTER)
    lines.append(f"{WK}d {statistics.mean(kx):+.2f} points, 95 % {kc.low:+.2f} to {kc.high:+.2f}{below(kc)}, "
                 f"adjusted p {FEA._p(kadj)}: {'d > 0' if kshown else 'd > 0 not shown'}{kflag}; its mean form "
                 f"{statistics.mean(km):+.2f} points (95 % {kcm.low:+.2f} to {kcm.high:+.2f}{below(kcm)}; decides "
                 f"nothing); its band Delta_e {band('primary', 'with_knock')} points under the primary reading of 'at "
                 f"b' ({band('other_at_b', 'with_knock')} under the other, 0 under version 5's); the ceiling's "
                 f"with-knock reading {CK_IN_PROCESS[r]:.2f} points (roads.json a.knock.mean, beside C, the no-knock "
                 "reading's); the MEI as above]")

    def sign(rd):
        xs = doc_d(doc, r, rd, "evaluate_form")
        sp, sadj, sshown = graph(doc, rd, "sign", r)
        k, nz = sum(v > 0 for v in xs), sum(v != 0 for v in xs)
        return (f"{k} of {nz} differences above 0 ({len(xs) - nz} zero, dropped), one-sided p {FEA._p(sp)}, graph p "
                f"{FEA._p(sadj)}: it {'shows' if sshown else 'does not show'} d > 0 under its own graph"
                + flag_words(fl[f"{rd} d>0 (sign) {n}"], ML_AFTER)), sshown
    words, s_shown = sign("no_knock")
    lines.append("the sign test, the declared secondary, in its own words: " + words
                 + ("; it and the t-test disagree: both are reported, and the t-test's verdict stands"
                    if s_shown != shown else "") + f" {WK}{sign('with_knock')[0]}]")
    named = []
    for key, rr in fl.items():
        p1, lo, hi = ("yes" if rr[run]["model_limited"] else "no" for run in ("primary", "companion_min",
                                                                             "companion_max"))
        if key.endswith(f" {n}") and len({p1, lo, hi}) > 1:
            named.append(f"companion, printed by name (PR-B 6.6): '{key}' MODEL-LIMITED: under kappa 1 {p1}; under "
                         f"mazda_25t's kappa 1.5000 {lo}; under ford_27tt's kappa 3.5000 {hi}")
    lines += named or [f"companion (P3 at kappa_L1 x b): no verdict at r = {r} has a MODEL-LIMITED flag that depends "
                       "on the assumed b"]
    return head, lines


def _cuts(root, d15, d05):
    return cuts_doc(root, [30.0] * N, {R_HI: [30.0 + v for v in d15], R_LO: [30.0 + v for v in d05]})


def _d9():
    return exact(9.0, 1.0, 5), exact(9.0, 1.0, 6)


LINE_CASES = {          # what each document makes the code pick; test_each_case_is_the_one_named checks it
    "A": lambda root: two_readings(root, _d9(), (exact(2.0, 1.0, 21), exact(3.0, 1.0, 22))),
    "B": lambda root: two_readings(root, _d9(), ([0.5] * 15 + [-1.0] * 5, exact(-3.0, 1.0, 8)), top=(1.0, 2.0)),
    "C": lambda root: two_readings(root, _d9(), ([1.5] * 15 + [-1.0] * 5,) * 2),
    "D": lambda root: two_readings(root, ([20.0] * 10 + [4.9] * 5 + [-10.0] * 5,) * 2, _d9()),
    "E": lambda root: _cuts(root, [1.5] * 12 + [0.0] * 3 + [-1.0] * 5, exact(3.0, 1.0, 9)),
    "F": lambda root: two_readings(root, (exact(-3.0, 1.0, 3), exact(0.3, 1.0, 4)), _d9(), top=(1.0, 2.0)),
    "G": lambda root: _cuts(root, [-0.5] * 15 + [10.0] * 5, exact(3.0, 1.0, 9)),
    "H": lambda root: _cuts(root, exact(2.3, 1.0, 21), exact(9.0, 1.0, 22)),
    "I": lambda root: _cuts(root, [-0.5] * 15 + [10.0] * 5, exact(-3.0, 1.0, 3)),
    "J": lambda root: two_readings(root, (exact(1.0, 2.8, 5), exact(9.0, 1.0, 6)), _d9()),
}


class Section7Lines(Case):
    """Every line of section 7 at both ratios against want_text, on documents chosen so that each word the code
    picks (a flag, 'wholly below 0', an adjusted p, a verdict, a count, a band, a named companion) would print
    another text if it were picked from the wrong test, reading, form, run or ratio."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.root = tmpdir(cls)
        write_records(cls.root)
        cls.docs = {k: make(cls.root) for k, make in LINE_CASES.items()}
        cls.out = {k: in_process(doc) for k, doc in cls.docs.items()}

    def test_every_line_at_both_ratios(self):
        for case, doc in self.docs.items():
            results, bd, fl, ivs, sent = self.out[case]
            for r in (R_HI, R_LO):
                head, lines = want_text(doc, fl, bd, r)
                with self.subTest(case=case, r=r):
                    self.assertEqual(sent[r]["verdict"], head)
                    self.assertEqual(sent[r]["text"], lines)

    def test_each_case_is_the_one_named(self):
        def ml(case, key, r, runs=("primary", "other_at_b")):
            got = self.out[case][2][f"{key} {FEA.node(B, r)}"]
            return tuple(got[run]["model_limited"] for run in runs)

        def iv(case, r, rd, form):
            return ci(doc_d(self.docs[case], r, rd, form))

        def covers(c):
            return c.low < 0.0 < c.high

        def named(case, r):
            return [k for k in self.out[case][2] if k.endswith(FEA.node(B, r))
                    and len(set(ml(case, k.rsplit(" ", 1)[0], r, ("primary", "companion_min", "companion_max")))) > 1]
        d = self.docs
        # A: the with-knock t verdicts flagged by the other reading alone; at r = 0.5 the graph's adjusted p is r =
        # 1.5's, not its own, at the printed precision; the other reading's band differs by reading; named by kappa
        for r in FEA.RATIOS:
            self.assertEqual(ml("A", "with_knock d>0 (t)", r), (False, True), r)
        p, adj, _ = graph(d["A"], "with_knock", "t", R_LO)
        self.assertNotEqual(FEA._p(p), FEA._p(adj))
        other = self.out["A"][1]["tables"]["other_at_b"][R_HI]
        self.assertNotEqual(f"{other['no_knock']['delta_e']:.2f}", f"{other['with_knock']['delta_e']:.2f}")
        self.assertIn(f"with_knock d>0 (t) {FEA.node(B, R_HI)}", named("A", R_HI))
        # B: with knock at r = 1.5 not shown and flagged by the primary, its interval covering 0 and its mean form's
        # wholly below 0; at r = 0.5 its interval wholly below 0
        self.assertEqual(ml("B", "with_knock d>0 (t)", R_HI), (True, True))
        self.assertFalse(graph(d["B"], "with_knock", "t", R_HI)[2])
        self.assertTrue(covers(iv("B", R_HI, "with_knock", "evaluate_form")))
        self.assertLess(iv("B", R_HI, "with_knock", "mean_form").high, 0.0)
        self.assertLess(iv("B", R_LO, "with_knock", "evaluate_form").high, 0.0)
        # C: the with-knock sign verdict shown and flagged by the other reading alone; the with-knock t verdict by
        # the primary; the with-knock mean form's interval covering 0
        self.assertEqual(ml("C", "with_knock d>0 (sign)", R_HI), (False, True))
        self.assertTrue(graph(d["C"], "with_knock", "sign", R_HI)[2])
        self.assertTrue(ml("C", "with_knock d>0 (t)", R_HI)[0])
        self.assertTrue(covers(iv("C", R_HI, "with_knock", "mean_form")))
        # D: the no-knock sign verdict flagged by the primary alone (|d| phi > MEI: the primary band is the larger)
        self.assertEqual(ml("D", "no_knock d>0 (sign)", R_HI), (True, False))
        tb = self.out["D"][1]["tables"]
        self.assertGreater(tb["primary"][R_HI]["no_knock"]["delta_e"], tb["other_at_b"][R_HI]["no_knock"]["delta_e"])
        # E: three zero differences at r = 1.5; at r = 0.5 the sign test's graph p is not its one-sided p
        self.assertEqual(sum(v == 0.0 for v in doc_d(d["E"], R_HI, "no_knock", "evaluate_form")), 3)
        p, adj, _ = graph(d["E"], "no_knock", "sign", R_LO)
        self.assertNotEqual(FEA._p(p), FEA._p(adj))
        # F: at r = 1.5 neither no-knock test shows d > 0, and the with-knock t-test does
        self.assertFalse(graph(d["F"], "no_knock", "t", R_HI)[2] or graph(d["F"], "no_knock", "sign", R_HI)[2])
        self.assertTrue(graph(d["F"], "with_knock", "t", R_HI)[2])
        # G: every interval at r = 1.5 covers 0, in both readings and both forms; the with-knock t flagged
        for rd in FEA.READINGS:
            for form in ("evaluate_form", "mean_form"):
                self.assertTrue(covers(iv("G", R_HI, rd, form)), (rd, form))
        self.assertTrue(ml("G", "with_knock d>0 (t)", R_HI)[0])
        # H: the companions' flags differ from each other, the primary's agreeing with the smallest kappa's
        self.assertEqual(ml("H", "no_knock d>0 (t)", R_HI, ("primary", "companion_min", "companion_max")),
                         (False, False, True))
        # I: at r = 1.5 the t-test rejects and the sign test does not; at r = 0.5 the t-test does not; with-knock
        # and sign verdicts are named at r = 0.5
        self.assertTrue(graph(d["I"], "no_knock", "t", R_HI)[2])
        self.assertFalse(graph(d["I"], "no_knock", "sign", R_HI)[2] or graph(d["I"], "no_knock", "t", R_LO)[2])
        self.assertTrue(any(k.startswith("with_knock") for k in named("I", R_LO)))
        self.assertTrue(any("(sign)" in k for k in named("I", R_LO)))
        self.assertEqual(named("I", R_HI), [])
        # J: the no-knock r = 1.5 t-test does not reject, so r = 0.5 reads 'not shown at r = 0.5 (the r = 1.5 test did
        # not reject ...)', and that verdict is flagged by the primary band (its + corner moves both ratios): the
        # flag's words sit inside that head (PR-B:684, G8)
        self.assertFalse(graph(d["J"], "no_knock", "t", R_HI)[2])
        self.assertFalse(graph(d["J"], "no_knock", "t", R_LO)[2])
        self.assertEqual(ml("J", "no_knock d>0 (t)", R_LO), (True, True))

    def test_the_report_block_gives_r15_first(self):
        """C8: the block lists r = 1.5, then r = 0.5, each verdict followed by its lines."""
        sent = self.out["A"][4]
        want = []
        for r in (R_HI, R_LO):
            want += [f"  r = {r}: {sent[r]['verdict']}"] + [f"    {x}" for x in sent[r]["text"]]
        self.assertEqual(AB._block_sentences(sent)[1:], want)
        self.assertNotEqual(sent[R_HI]["text"], sent[R_LO]["text"])                      # control


# ------------------------------------------------------------------------------------------ section 10
class Section10(Study):
    def test_the_beside_values_are_read_with_their_file_and_line(self):
        b = self.res["section_10"]
        self.assertEqual(b["plant_sha"]["plant_sha_now"]["value"], SYN["plants"][0])
        self.assertEqual(b["plant_sha"]["plant_sha_at_draw"]["value"], SYN["plants"][1])
        sp = b["spreads"]
        self.assertEqual(sp[f"{AB.X2_RESULT}:11"]["value"], SYN["x2"][0])
        self.assertEqual(sp[f"{AB.X1_RESULT}:29"]["value"], SYN["x1"][0])
        self.assertEqual(sp[f"{AB.X1_RESULT}:60"]["value"], SYN["x1"][1])
        self.assertEqual(sp[f"{AB.X1_RESULT}:29"]["section"], "TOTAL DAMAGE (primary)")
        self.assertTrue(sp[f"{AB.X1_RESULT}:60"]["section"].startswith("THERMAL-ONLY DAMAGE"))
        self.assertEqual(sp[f"{AB.X1_RESULT}:60"]["n"], 23)
        self.assertEqual(b["practice"], "computed at item (c), after this analysis")
        self.assertIn(f"16.5 over 5 pairs ({AB.X2_RESULT}:11, under 'TOTAL DAMAGE (primary)')", self.text)
        self.assertIn("the status: the analysis's exploratory | beside it the context's recorded rule output, "
                      "exploratory", self.text)

    def test_a_file_not_committed_reads_not_read_and_the_analysis_still_runs(self):
        root, scores = self.fresh_repo("x1_changed")
        write(root, AB.X1_RESULT, x1_text(1.0, 2.0))
        write(root, AB.REVERIFY, json.dumps({"plants": {B: {"plant_sha_now": "eeee5555ffff6666",
                                                            "plant_sha_at_draw": "9999aaaa0000bbbb"}}}))
        ctx, out, rep = run_both(root, scores)
        b = load(out)["section_10"]
        self.assertTrue(b["spreads"][f"{AB.X1_RESULT}:29"]["not_read"].startswith("not read: not committed"))
        self.assertEqual(set(b["spreads"][f"{AB.X1_RESULT}:29"]), {"not_read"})
        self.assertRegex(b["plant_sha"]["not_read"], r"^not read: not committed at HEAD.*reverify\.json")
        self.assertEqual(b["spreads"][f"{AB.X2_RESULT}:11"]["value"], SYN["x2"][0])     # control: X2 still read
        text = read_text(rep)
        self.assertIn("not read: ", text)
        self.assertNotIn("eeee5555ffff6666", text)          # a changed, uncommitted record's value is never printed
        os.remove(os.path.join(root, *AB.REVERIFY.split("/")))
        gone = AB.beside_10(root, self.ctx, self.res["fea"]["primary"])
        self.assertTrue(gone["plant_sha"]["not_read"].startswith("not read: "))           # and an absent one


# ------------------------------------------------------------------------------------------ the guard itself
def loader_scan(src):
    """The names, imports and code strings (the module docstring aside) by which a source could load an agent or
    reach the study's run folders or the records' never-read keys."""
    tree = ast.parse(src)
    docstring = ast.get_docstring(tree, clean=False)
    names = ({n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
             | {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
             | {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names})
    imported = ({a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
                | {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module})
    strings = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
               and n.value != docstring]
    words = ("runs/", "b58h_dt1", "b58h_check_dt1", "final.zip", "commit_reveal", "roads_seed", "attempts",
             "steps_log", "attempt_1_printed", "logs/")
    return {"names": sorted(names & {"load_agent", "read_agents", "agent_policy", "AveragedPolicy",
                                     "average_lines", "torch", "zipfile"}),
            "imports": sorted(imported & {"torch", "zipfile", "stable_baselines3", "training_recipe", "train"}),
            "strings": sorted(w for w in words if any(w in s for s in strings))}


class Guard(Case):
    def test_the_guard_refuses_the_study_folders_and_the_agent_loaders(self):
        probe = os.path.join(HERE, "runs", "b58h_dt1", "probe_never_written.json")
        with self.assertRaises(AssertionError):                               # leaving the block fails ...
            with forbid_study():
                with self.assertRaises(PermissionError):                      # ... after the open was refused
                    open(probe, "rb")
        with self.assertRaises(AssertionError):
            V.load_agent("x", {}, device="cpu")
        with self.assertRaises(AssertionError):
            V.read_agents([], roads_rec={}, engine=B)
        self.assertTrue(refused_path(os.path.join(HERE, "runs", "b58h_check_dt1")))
        self.assertFalse(refused_path(os.path.join(HERE, "runs", "b58h_other")))          # control

    def test_ab_names_no_agent_loader_and_imports_no_learner(self):
        with open(os.path.join(HERE, "b58h_analysis.py"), encoding="utf-8") as fh:
            self.assertEqual(loader_scan(fh.read()), {"names": [], "imports": [], "strings": []})
        bad = ('"""doc"""\nimport zipfile\nimport evaluate as V\nm = V.load_agent(p, meta, device="cpu")\n'
               'rec = {"roads_seed": 1}\nopen("runs/b58h_dt1/final.zip")\n')
        self.assertEqual(loader_scan(bad), {"names": ["load_agent", "zipfile"], "imports": ["zipfile"],
                                            "strings": ["b58h_dt1", "final.zip", "roads_seed", "runs/"]},
                         "control: the scan sees each of them")
        out = subprocess.run([sys.executable, "-B", "-c", "import sys, b58h_analysis; "
                              "print(sorted(m for m in ('torch', 'stable_baselines3') if m in sys.modules))"],
                             cwd=HERE, capture_output=True, text=True,
                             env=dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1",
                                      PYTHONDONTWRITEBYTECODE="1"))
        self.assertEqual(out.stdout.strip(), "[]", out.stderr)


if __name__ == "__main__":
    unittest.main()

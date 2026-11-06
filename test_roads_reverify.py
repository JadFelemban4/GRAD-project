"""test_roads_reverify.py -- the roads re-verification (roads_reverify.py; row 140; the interface sheet, section 5).

    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/Scripts/python.exe -B test_roads_reverify.py
                    exit code 0 when all pass. About 2.4 h at 14 jobs on the laptop under other agents' load
                    (MEASURED on 5 November, the draft's three runs: 450 s, 3260 s with Control, Moves and
                    Redraws, 4968 s for FullShape, two passes of the draw's REAL-path shape on one road);
                    at REVERIFY_TEST_JOBS=2, 2642 s for Control, Moves and Redraws and 11728 s for FullShape,
                    run side by side (MEASURED on 6 November), the other classes about 4 min. After the
                    review's fixes (Redraws computes both readings and every section; LiveRule added), at
                    REVERIFY_TEST_JOBS=2 and alone: 2217 s for Redraws alone and 264 s for the other classes
                    but Control, Moves and FullShape (MEASURED on 6 November).
                    REVERIFY_TEST_JOBS=J sets the pool (default min(14, cpu_count)). One class alone:
                    `... test_roads_reverify.py Compare`

RV's gate (the interface sheet, section 14) is this file, its SYNTHETIC full-shape test included, then the
control `roads_reverify.py check --jobs 14 --out <outside> --skip-companions` on RV's clean tree, which must
print EQUAL (both readings of redraws.json among its sections: INTERFACES 17). Rule 0.1: anything that reads
results/EPA_ROADS/redraws.json runs only after R4, which wrote it (34cca5b). Two classes read the tree's own
records: RealRecords (roads.json, redraws.json and its one data input, Run 2's summary.json, through the
guard's one exception, as the check's preconditions read them) and Live (through
four_engine_roads.current_reverify, once a re-verification record exists). No other class reads them.

Nothing here draws a road of the test, writes in the tree, opens an EPA table, logs/ or any .csv, or a held-out
record but summary.json in RealRecords: epa_roads' audit hook is installed below, and every class is
test_epa_fixtures.Guarded (WP3_INTERFACES.md 9.1). The classes that run the draw's code give it the contract's
two files as SYNTHETIC stand-ins (contract_stand_ins), so the real contract is never opened. Each check has its
control (mistake 12).

  Isolation        roads_reverify.py is imported by no module of roads.json's 35, epa_freeze.CODE_HASHED or
                   fingerprint.PLANT_CODE; its name and this file's end with no plant file's name; its source
                   names none of the calls it must never make, nor reads commit_reveal (the scan's control: a
                   source that does is flagged); four_engine_roads' reader adds no import
  Scripted         the scripted stream hands back its draws in order and refuses a wrong type, a value outside
                   [lo, hi) and a draw past the record; scripted_streams refuses a seed and puts the streams back
  Compare          the comparison is bitwise: 0.0 and -0.0, 1 and 1.0, True and 1, x and the next float, a
                   missing key, an extra key and a longer list all differ; only report.provenance and
                   report.wall_s are ignored; at most 50 differences are listed
  Reconstruction   on SYNTHETIC roads (no plant: C5 is a stand-in): the generated roads come back from their
                   recorded draws to the steps_log's hash, and the scripted replacement loop gives the final
                   roads and the slot records back, a flat slot included; a draw moved by one ulp, a missing
                   replacement draw and a discarded climb that would fit are each found
  Control          a SYNTHETIC draw in the smoke shape (2 roads, the B58 and the Ford) re-verifies EQUAL with
                   every cache cleared, without roads_seed and with every forbidden call made to raise; a
                   recorded draw, C5 value or ceiling moved by one ulp is DIFFERENT; fail-fast stops there
  Moves            the B58's car mass moved by one part in 1e9 is found by C5; its c_turb moved by one part in
                   1e9 is not seen by C5 (C5 reads the vehicle only) and is found by the ceilings (mistake 12)
  Redraws          a SYNTHETIC redraw (the smoke run's margins: the Ford's at 0.5) with the Ford dropped writes
                   both readings, version 6 (the B58 alone gating) redrawing nothing and version 5 (both cars
                   gating) redrawing a slot, and recompute re-verifies every section and both readings EQUAL; a
                   value of either reading moved by one ulp, or a redraw the record does not hold, is
                   DIFFERENT; the readings are epa_roads.redraw's, the B58 alone gating version 6 when all
                   three EPA engines are dropped (Run 2)
  RedrawsRecord    redraws.json's refusals in a temporary repository: the control refuses nothing; summary.json
                   changed or dropping otherwise, a margin moved by one ulp, the B58 dropped, a reading missing,
                   an unknown key, another tau, seed_kind or summary path, changed_during_run, an uncommitted
                   file, and for a REAL record an attempts log that does not name it, are each refused; a REAL
                   record whose attempts log names a redraws outcome needs redraws.json
  RealRecords      the tree's roads.json and redraws.json pass the records' refusals (summary.json's among
                   them), and the sections are SECTIONS then one per reading epa_roads.redraw writes; with
                   roads_ceiling's guard installed, the check's second read of summary.json (_provenance_now)
                   gives redraws.json's margins_source sha_text, puts roads_ceiling._forbidden back and leaves
                   summary.json out of roads_ceiling.OPENED
  SummaryOpened    summary_opened gives roads_ceiling's guard epa_roads' one exception, exactly summary.json,
                   inside the block only and put back after an error too; its control: outside, roads_ceiling's
                   guard refuses it
  Refusals         every precondition of row 140 (2) on a committed copy of the hashed files: each of the 35
                   changed by one byte is refused unless it is one of MAY_DIFFER, which is listed instead; an
                   edit to evaluate.EPISODES and an import added to evaluate.py are refused (amendment P4.1's
                   two controls), and so are an entry appended to EPISODES, its last entry removed and an
                   entry no road uses changed (the whole tuple the draw read, its length both ways, from
                   HEAD's history when evaluate.py differs); the contract, a version, an engine_sha, an EPA
                   engine's complete.json naming another (row 94), a shadowing package, a data input, a tau,
                   the threads, -B, a bytecode cache (none looked for in .venv), an unknown key, P's two
                   defaults, the road shape and the --out folder; a refused run computes nothing
  RecordMode       in a temporary repository with a bare remote: check writes only under --out, once, and
                   --skip-companions leaves report out, partial; an input changed while the run lasts, or a
                   file opened that neither the draw nor the redraws opened, is REFUSED (exit 2); adopt takes
                   a complete EQUAL check of HEAD, pushed, and refuses, each by its text, a partial, DIFFERENT,
                   stale, incomplete (a reading left out, or a section with a difference under EQUAL), refused,
                   unequal-reconstruction or other-redraws_sha result and one re-hashed since (a hashed file,
                   or summary.json under a SYNTHETIC redraws.json); record writes reverify.json once from a
                   clean pushed tree, and --supersede the next reverify_<n>.json; a dirty tree, an unpushed
                   HEAD, an uncommitted roads.json and a redraws.json of another roads_sha are refused; a
                   DIFFERENT result is written nowhere in results/
  CurrentReverify  four_engine_roads.current_reverify takes the highest n that is tracked, unmodified at HEAD
                   and names the live roads_sha and redraws_sha, and nothing else
  ReferenceCommit  reference_commit is the one commit that added the file, and refuses any other count
  LiveRule         live_state, Live's skip rule, in a temporary repository: it skips only while no reverify*.json
                   was ever added in HEAD's history or exists on disk and HEAD's engine_env.py does not define
                   REWARD_KNOCK_DEFAULT (P's uncommitted tree too); a record on disk and not committed, one
                   committed and modified, deleted or naming another roads.json, and P committed without one
                   each fail, naming why; each with its control
  Live             from P on: the current record names roads.json and every file it names is its blob at the
                   commit that added the record (row 140 (3)); skipped only as live_state allows, a failure
                   naming why otherwise
  FullShape        MANDATORY (the interface sheet, section 14): a SYNTHETIC draw in smoke --full's shape (1 road,
                   the four engines, every variant and reading at both ratios, the companions) re-verifies
                   EQUAL, roads_ceiling.report included, every section computed
"""
import ast
import atexit
import contextlib
import copy
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import epa_roads as R  # noqa: E402
import four_engine_roads as FR  # noqa: E402
import roads_ceiling as RC  # noqa: E402
import roads_reverify as RV  # noqa: E402
from test_epa_fixtures import Guarded  # noqa: E402  (WP3_INTERFACES.md 9.1)
from test_epa_roads import SYNTHETIC_SEED, fake_c5, flip_one_byte, hashed_copy  # noqa: E402

R.install_guard(())
JOBS = int(os.environ.get("REVERIFY_TEST_JOBS", str(min(14, os.cpu_count() or 1))))
# The two shapes epa_roads.smoke draws (epa_roads.py:1673-1679): its default, and --full, the real draw's path
SHAPES = {"smoke": dict(n_roads=R.SMOKE_N_ROADS, engines=R.SMOKE_ENGINES, ratios=R.SMOKE_RATIOS,
                        variants=R.SMOKE_VARIANTS, readings=R.SMOKE_READINGS, companions=False),
          "full": dict(n_roads=1, engines=R.ENGINES, ratios=RC.RATIOS, variants=R.DRAW_VARIANTS,
                       readings=R.DRAW_READINGS, companions=True)}
# What the re-verifier must never call (the interface sheet, section 5; row 96: nothing that uses roads_seed)
FORBIDDEN_R = ("verify_record", "frozen_problems", "generate", "practice_roads", "training_share_road", "draw",
               "first_draw", "redraw", "recheck_or_redraw", "roads_seed_from", "new_private_integer")
ENV_OK = {"OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}


def git(root, *args):
    r = subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@local", *args], cwd=root,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


def clear_caches():
    """Every in-process cache the draw's code keeps (epa_roads._PLANTS; roads_ceiling's _PLANTS, _TAUS and
    _CACHE), so what runs next computes again rather than reads back."""
    R._PLANTS.clear()
    RC._PLANTS.clear()
    RC._TAUS.clear()
    RC._CACHE.clear()


@contextlib.contextmanager
def caches(cache=None):
    """Inside, roads_ceiling's run cache holds `cache` (empty when None) and the plant and tau caches start
    empty; outside, every cache is back as it was."""
    saved = (dict(R._PLANTS), dict(RC._PLANTS), dict(RC._TAUS), dict(RC._CACHE))
    clear_caches()
    RC._CACHE.update(cache or {})
    try:
        yield
    finally:
        clear_caches()
        R._PLANTS.update(saved[0])
        RC._PLANTS.update(saved[1])
        RC._TAUS.update(saved[2])
        RC._CACHE.update(saved[3])


_STAND_INS = []


@contextlib.contextmanager
def contract_stand_ins():
    """The contract's two files as SYNTHETIC stand-ins, outside the repository, for a test that runs the draw's
    code: roads.json hashes them (epa_roads.CONTRACT_FILES, here by absolute path) and the coverage flags read
    the JSON's engines.<id>.coverage (thresholds.common.CONTRACT_JSON), here empty on every EPA engine, so every
    climb reads as outside calibration. Never the contract's values. Written once per process and removed at its
    exit, so a record drawn in one class still names files that exist in the next."""
    from thresholds import common
    if not _STAND_INS:
        tmp = tempfile.mkdtemp(prefix="reverify_contract_")
        atexit.register(shutil.rmtree, tmp, True)
        js, md = os.path.join(tmp, "ENGINE_THRESHOLDS.json"), os.path.join(tmp, "ENGINE_THRESHOLDS.md")
        with open(js, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"SYNTHETIC": "a stand-in, never the contract",
                       "engines": {e: {"coverage": {"calibration_fired": {}, "calibration_hot": {}}}
                                   for e in R.EPA_ENGINES}}, fh)
        with open(md, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("SYNTHETIC stand-in for results/ENGINE_THRESHOLDS.md: the test's, never the contract\n")
        _STAND_INS[:] = [js, md]
    js, md = _STAND_INS
    with mock.patch.object(R, "CONTRACT_FILES", (js, md)), mock.patch.object(common, "CONTRACT_JSON", js):
        yield


_DRAWS = {}


def synthetic_draw(kind):
    """epa_roads.first_draw on SYNTHETIC_SEED in one of SHAPES, completed as epa_roads.smoke completes its
    record (epa_roads.py:1695-1702) and read back as write_once writes it (JSON, no NaN), with the cache it
    left: (record, roads_ceiling's run cache, kept for the smoke shape only). Drawn once per process, inside contract_stand_ins (the caller's)
    and with every cache cleared before and after, so a re-verification computes again."""
    if kind not in _DRAWS:
        with caches():
            steps = []
            rec = R.first_draw(SYNTHETIC_SEED, seed_kind="SYNTHETIC", jobs=JOBS, log=R.make_log(steps),
                               **SHAPES[kind])
            rec["commit_reveal"] = {"SYNTHETIC": True, "roads_seed": SYNTHETIC_SEED}
            rec["steps_log"] = steps
            rec["files_opened"] = R.files_opened()
            rec["data_inputs"] = R.data_inputs(rec["files_opened"], rec["hashes"], root=HERE)
            _DRAWS[kind] = (json.loads(json.dumps(rec, allow_nan=False)), dict(RC._CACHE) if kind == "smoke" else {})
    rec, cache = _DRAWS[kind]
    return copy.deepcopy(rec), cache


@contextlib.contextmanager
def no_roads_seed(seed):
    """Inside, every call the re-verifier must never make raises (FORBIDDEN_R, fingerprint.plant_fingerprint),
    and so does numpy.random.default_rng given `seed`, alone or in a seed list (row 96: any computation that
    uses roads_seed is an attempt). The workers of a pool are separate processes and are not patched; they run
    only the identities and roads_ceiling's runs, which take an episode seed."""
    import fingerprint as FP
    real = np.random.default_rng

    def rng(*args, **kw):
        s = args[0] if args else kw.get("seed")
        if s == seed or (isinstance(s, (list, tuple)) and seed in s):
            raise AssertionError(f"numpy.random.default_rng was given roads_seed {seed} (row 96)")
        return real(*args, **kw)

    def raiser(name):
        def f(*a, **k):
            raise AssertionError(f"the re-verifier called {name}")
        return f
    with contextlib.ExitStack() as st:
        for name in FORBIDDEN_R:
            st.enter_context(mock.patch.object(R, name, raiser(f"epa_roads.{name}")))
        st.enter_context(mock.patch.object(FP, "plant_fingerprint", raiser("fingerprint.plant_fingerprint")))
        st.enter_context(mock.patch.object(np.random, "default_rng", rng))
        yield


def sha_or_none(rel):
    from thresholds import common
    p = os.path.join(HERE, *rel.split("/"))
    return common.sha_text(p) if os.path.isfile(p) else None


def leaves(x, path=()):
    """Every (path, float) leaf of a JSON value, in order."""
    if isinstance(x, dict):
        for k, v in x.items():
            yield from leaves(v, path + (k,))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from leaves(v, path + (i,))
    elif type(x) is float:
        yield path, x


def moved(record, root_key, *, nth=0):
    """A copy of `record` with the nth finite non-zero float under record[root_key] moved by one ulp, and the
    path moved."""
    rec = copy.deepcopy(record)
    hits = [(p, v) for p, v in leaves(rec[root_key], (root_key,)) if v != 0.0 and math.isfinite(v)]
    path, v = hits[nth]
    d = rec
    for k in path[:-1]:
        d = d[k]
    d[path[-1]] = math.nextafter(v, math.inf)
    return rec, list(path)


def section_names(result):
    return [n for n, s in result["sections"].items() if s["differences"]]


# =====================================================================================================
class Isolation(Guarded):
    def test_imported_by_no_hashed_module(self):
        import epa_freeze as EF
        import fingerprint as FP
        hashed = set(R.hashed_files(root=HERE, engines=R.ENGINES))
        self.assertNotIn(RV.MODULE_REL, hashed)
        roots = sorted((hashed | set(EF.CODE_HASHED) | set(EF.STEP2_CODE) | set(FP.PLANT_CODE)) - {RV.MODULE_REL})
        for f in roots:
            if f.endswith(".py") and os.path.isfile(os.path.join(HERE, f)):
                self.assertNotIn(RV.MODULE_REL, R.import_closure(f, root=HERE), f)
        # the control (mistake 12): this module's own closure does reach it
        self.assertIn(RV.MODULE_REL, R.import_closure("test_roads_reverify.py", root=HERE))

    def test_its_name_and_this_files_end_with_no_plant_files_name(self):
        """fingerprint's dirty-file match is an endswith until P makes it exact (row 127 (5))."""
        import fingerprint as FP
        for p in FP.PLANT_CODE:
            for mine in (RV.MODULE_REL, "test_roads_reverify.py"):
                self.assertFalse(mine.endswith(p) or mine.endswith(os.path.basename(p)), (mine, p))

    @staticmethod
    def flagged(src):
        """The forbidden names a source makes: an attribute of epa_roads named in FORBIDDEN_R (as R., ER. or
        epa_roads.), any plant_fingerprint, an import of either by name, an epa_freeze private name, and a read
        of commit_reveal (a subscript or a .get)."""
        out = []
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Attribute):
                base = node.value.id if isinstance(node.value, ast.Name) else None
                if base in ("R", "ER", "epa_roads") and node.attr in FORBIDDEN_R:
                    out.append(f"{base}.{node.attr}")
                if node.attr == "plant_fingerprint":
                    out.append(f"{base}.plant_fingerprint")
                if base in ("EF", "epa_freeze") and node.attr.startswith("_"):
                    out.append(f"{base}.{node.attr}")
            elif isinstance(node, ast.ImportFrom):
                out += [a.name for a in node.names if a.name in FORBIDDEN_R + ("plant_fingerprint",)]
            elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) \
                    and node.slice.value == "commit_reveal":
                out.append("[commit_reveal]")
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" \
                    and node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == "commit_reveal":
                out.append(".get(commit_reveal)")
        return out

    def test_the_source_names_no_forbidden_call(self):
        with open(os.path.join(HERE, RV.MODULE_REL), encoding="utf-8") as fh:
            self.assertEqual(self.flagged(fh.read()), [])
        scratch = ("import epa_roads as R\nimport fingerprint as FP\nR.verify_record(r, root=x)\n"
                   "FP.plant_fingerprint('b58')\nr['commit_reveal']\nr.get('commit_reveal')\n")
        self.assertEqual(sorted(self.flagged(scratch)), sorted(["R.verify_record", "FP.plant_fingerprint",
                                                                "[commit_reveal]", ".get(commit_reveal)"]))

    def test_the_reader_adds_no_import(self):
        """The interface sheet, section 5: current_reverify is appended to four_engine_roads.py, which imports
        only what it already imports."""
        with open(os.path.join(HERE, "four_engine_roads.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())

        def imports(nodes):
            out = set()
            for n in nodes:
                for x in ast.walk(n):
                    if isinstance(x, ast.Import):
                        out |= {a.name for a in x.names}
                    elif isinstance(x, ast.ImportFrom):
                        out.add(x.module)
            return out
        mine = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("reverify_paths",
                                                                                     "current_reverify")]
        self.assertEqual(len(mine), 2)
        self.assertLessEqual(imports(mine), imports([n for n in tree.body if n not in mine]))
        self.assertIn("subprocess", imports(mine))          # the control: the scan sees the reader's import


# =====================================================================================================
class Scripted(Guarded):
    def test_the_scripted_stream(self):
        rng = RV.ScriptedRng([3, 0.11, 7], label="t")
        self.assertEqual((rng.integers(0, 5), rng.uniform(0.10, 0.12), rng.left()), (3, 0.11, 1))
        self.assertEqual(rng.integers(7, 8), 7)
        with self.assertRaises(RV.NotRecorded):             # one draw past the record
            rng.integers(0, 9)
        for values, call in (([0.5], lambda r: r.integers(0, 2)),          # a float where an int is asked
                             ([1], lambda r: r.uniform(0.0, 2.0)),         # an int where a float is asked
                             ([5], lambda r: r.integers(0, 5)),            # hi is excluded
                             ([0.0999], lambda r: r.uniform(0.10, 0.12))):  # below lo
            with self.assertRaises(RV.NotRecorded):
                call(RV.ScriptedRng(values, label="t"))

    def test_the_streams_are_the_recorded_grades_and_take_no_seed(self):
        rec = {"slots": [{"slot": 0, "candidates": [{"grade": 0.105}]},
                         {"slot": 1, "candidates": [{"grade": 0.11}, {"grade": 0.111}, {"grade": 0.112}]}]}
        red = {"slots": [{"slot": 1, "candidates": [{"grade": 0.113}, {"grade": 0.114}]}]}
        old = (R.replacement_rng, R.redraw_rng)
        with RV.scripted_streams(rec, red) as made:
            a = R.replacement_rng(None, 1)
            self.assertEqual([a.uniform(0.10, 0.12), a.uniform(0.10, 0.12), a.left()], [0.111, 0.112, 0])
            self.assertEqual(R.replacement_rng(None, 0).left(), 0)       # the first draw is not the stream's
            b = R.redraw_rng(None, 1)
            self.assertEqual([b.uniform(0.10, 0.12), b.left()], [0.113, 1])
            with self.assertRaises(AssertionError):
                R.replacement_rng(SYNTHETIC_SEED, 1)
            with self.assertRaises(AssertionError):
                R.redraw_rng(SYNTHETIC_SEED, 1)
            self.assertEqual(len(made), 3)
        self.assertEqual((R.replacement_rng, R.redraw_rng), old)
        with self.assertRaises(ValueError):
            with RV.scripted_streams(rec):
                raise ValueError("inside")
        self.assertEqual((R.replacement_rng, R.redraw_rng), old)             # back after an exception too


# =====================================================================================================
class Compare(Guarded):
    def differs(self, a, b, **kw):
        return RV.compare(a, b, **kw)["differences"]

    def test_the_comparison_is_bitwise(self):
        x = 0.1
        for a, b in ((0.0, -0.0), (1, 1.0), (True, 1), (x, math.nextafter(x, 1.0)), ({"a": 1}, {}),
                     ({}, {"a": 1}), ([1, 2], [1, 2, 3]), (None, 0), ("a", "b")):
            self.assertEqual(self.differs(a, b), 1, (a, b))
        same = {"a": [1, 2.5, {"b": None, "c": True}], "d": "e", "f": -0.0}
        res = RV.compare(same, copy.deepcopy(same))
        self.assertEqual((res["values"], res["differences"], res["first"]), (6, 0, []))

    def test_the_new_side_is_read_as_a_record_holds_it(self):
        self.assertEqual(self.differs([1, 2], (1, 2)), 0)                    # a tuple is written as a list
        self.assertEqual(self.differs({"1": 2}, {1: 2}), 0)                  # a key as a string
        self.assertEqual(self.differs(None, float("nan")), 1)                # a NaN cannot be written
        self.assertEqual(self.differs(1.0, np.float64(1.0)), 0)              # a NumPy float as a Python float

    def test_only_the_two_paths_are_ignored(self):
        self.assertEqual(RV.IGNORED_PATHS, (("report", "provenance"), ("report", "wall_s")))
        self.assertEqual(RV.ADDED_BY_STEP_12A, ())
        old = {"report": {"provenance": {"git_head": "a"}, "wall_s": 1.0, "grids": [1.0]}}
        new = {"report": {"provenance": {"git_head": "b", "x": 1}, "wall_s": 2.0, "grids": [1.0]}}
        self.assertEqual(self.differs(old["report"], new["report"], path=("report",)), 0)
        new["report"]["grids"] = [1.5]
        self.assertEqual(self.differs(old["report"], new["report"], path=("report",)), 1)
        self.assertEqual(self.differs(old, new), 1)
        self.assertEqual(self.differs({"c5": {}}, {"c5": {"added": 1}}), 1)  # nothing is added unseen
        self.assertEqual(self.differs({"report": {}}, {"report": {"wall_s": 3.0}}), 0)

    def test_at_most_50_are_listed_and_each_names_its_path(self):
        res = RV.compare([0.0] * 60, [1.0] * 60, path=("c5",))
        self.assertEqual((res["differences"], len(res["first"]), res["values"]), (60, 50, 60))
        self.assertEqual(res["first"][3], {"path": ["c5", 3], "at_draw": 0.0, "now": 1.0})


# =====================================================================================================
def stand_in_record(n_roads, verdicts):
    """A SYNTHETIC first draw without a plant: R.generate's roads labelled as first_draw labels them, the
    replacement loop at SYNTHETIC_SEED with C5 a stand-in (test_epa_roads.fake_c5), and the two steps_log
    lines whose hashes the reconstruction reads, as first_draw prints them (epa_roads.py:1349-1350,
    :1363-1364). Returns (record, generated roads, plants, gating)."""
    gen = R.generate(SYNTHETIC_SEED, n_roads=n_roads)
    for r in gen:
        r["label"] = f"SYNTHETIC road {r['k']}"
    plants = {"b58": "b58", "ford_27tt": "ford_27tt"}          # names only: C5 is the stand-in
    with mock.patch.object(R, "c5_on_car", fake_c5(verdicts)):
        final, recs, c5 = R.replacement_loop(gen, SYNTHETIC_SEED, plants=plants, gating=set(plants),
                                             log=lambda m: None)
    rec = {"seed_kind": "SYNTHETIC", "roads": final, "slots": recs, "c5": c5,
           "steps_log": [f"[t] step 2, arrays generated: {n_roads} roads, x slots, arrays sha256 "
                         f"{R.arrays_sha256(gen)}",
                         f"[t] step 4a, C5 at 1.9 %: {len(recs)} slots; final arrays sha256 {R.arrays_sha256(final)}"]}
    return json.loads(json.dumps(rec)), json.loads(json.dumps(gen)), plants, set(plants)


class Reconstruction(Guarded):
    def setUp(self):
        super().setUp()
        gen = R.generate(SYNTHETIC_SEED, n_roads=3)
        self.target = gen[0]["climbs"][1]["slot"]                  # replaced after two failing draws
        self.flat = gen[1]["climbs"][0]["slot"]                    # every draw fails: flat
        g0, g1 = gen[0]["climbs"][1]["grade"], gen[1]["climbs"][0]["grade"]
        first2 = [float(x) for x in R.replacement_rng(SYNTHETIC_SEED, self.target).uniform(0.10, 0.12, 2)]
        all100 = {float(x) for x in R.replacement_rng(SYNTHETIC_SEED, self.flat).uniform(0.10, 0.12, 100)}
        bad = {g0, g1} | set(first2) | all100
        self.verdicts = lambda car, g: "fails" if (car == "ford_27tt" and g in bad) else "passes"
        self.rec, self.gen, self.plants, self.gating = stand_in_record(3, self.verdicts)

    def replay(self, rec):
        with mock.patch.object(R, "c5_on_car", fake_c5(self.verdicts)), RV.scripted_streams(rec) as made:
            out = R.replacement_loop(self.gen, None, plants=self.plants, gating=self.gating, log=lambda m: None)
        return json.loads(json.dumps(out)), made

    def test_the_generated_and_final_roads_come_back(self):
        roads, probs = RV.reconstruct_generated(self.rec, root=HERE)
        self.assertEqual(probs, [])
        self.assertEqual(json.loads(json.dumps(roads)), self.gen)
        outcomes = {s["slot"]: s["outcome"] for s in self.rec["slots"]}
        self.assertEqual((outcomes[self.target], outcomes[self.flat]), ("replaced", "flat"))
        (final, recs, c5), made = self.replay(self.rec)
        self.assertEqual((final, recs, c5), (self.rec["roads"], self.rec["slots"], self.rec["c5"]))
        self.assertEqual(sorted(m.label for m in made), sorted(f"slot {k}'s replacement stream (0x1D)"
                                                               for k in (self.target, self.flat)))
        self.assertTrue(all(m.left() == 0 for m in made))
        block = RV.reconstruction_block(self.rec, roads)
        self.assertTrue(block["equal"], block)

    def test_a_draw_moved_by_one_ulp_is_found(self):
        rec = copy.deepcopy(self.rec)
        c = rec["roads"][2]["draws"]["climbs"][0]
        c["grade"] = math.nextafter(c["grade"], 1.0)
        _, probs = RV.reconstruct_generated(rec, root=HERE)
        self.assertEqual(probs, ["the generated roads' arrays sha256 is not the steps_log's step-2 hash"])

    def test_a_discarded_climb_that_would_fit_is_found(self):
        rec = copy.deepcopy(self.rec)
        d = rec["roads"][0]["draws"]                                   # the shortest road: every climb and gap
        d["lead_s"] = 150                                              # at its least, so the discarded climb
        for c in d["climbs"] + [d["discarded"]]:                       # fits and the layout asks for one more
            c["L_s"], c["gap_s"] = 67, 50
        self.assertLessEqual(150 + len(d["climbs"]) * 117 + 67 + R.RAMP_S, R.DURATION_S - R.TAIL_S)
        _, probs = RV.reconstruct_generated(rec, root=HERE)
        self.assertTrue(any("road 0" in p and "was asked for" in p for p in probs), probs)

    def test_a_replacement_draw_moved_or_missing_is_found(self):
        rec = copy.deepcopy(self.rec)
        s = [x for x in rec["slots"] if x["slot"] == self.target][0]
        s["candidates"][1]["grade"] = math.nextafter(s["candidates"][1]["grade"], 1.0)
        (final, recs, _), _ = self.replay(rec)
        self.assertGreater(RV.compare(self.rec["slots"], recs)["differences"], 0)
        self.assertGreater(RV.compare(self.rec["roads"], final)["differences"], 0)
        rec = copy.deepcopy(self.rec)
        s = [x for x in rec["slots"] if x["slot"] == self.flat][0]
        s["candidates"].pop()
        with self.assertRaises(RV.NotRecorded):
            self.replay(rec)

    def test_the_steps_log_must_hold_each_hash_once(self):
        rec = copy.deepcopy(self.rec)
        rec["steps_log"].append(rec["steps_log"][0])
        _, probs = RV.reconstruct_generated(rec, root=HERE)
        self.assertEqual(probs, ["the steps_log holds 2 'step 2' lines with an arrays hash, not one"])


# =====================================================================================================
_SMOKE = {}


def smoke_state():
    """The smoke-shape draw, its re-verification (every section, every cache cleared first, inside
    no_roads_seed, commit_reveal deleted from the record it is given) and the run cache that re-verification
    left. Computed once per process, inside the caller's contract_stand_ins."""
    if not _SMOKE:
        rec, _ = synthetic_draw("smoke")
        given = copy.deepcopy(rec)
        del given["commit_reveal"]
        before = {f: sha_or_none(f) for f in (R.ROADS_REL, R.ATTEMPTS_REL, R.REDRAWS_REL)}
        out = tempfile.mkdtemp(prefix="reverify_out_")
        lines = []
        with caches(), no_roads_seed(SYNTHETIC_SEED):
            res = RV.reverify(root=HERE, jobs=JOBS, mode="check", out_dir=out, log=lines.append, record=given)
            cache = dict(RC._CACHE)
        _SMOKE.update(record=rec, result=res, cache=cache, lines=lines, before=before,
                      after={f: sha_or_none(f) for f in before}, out=out)
    return _SMOKE


class Control(Guarded):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.enterClassContext(contract_stand_ins())
        cls.s = smoke_state()

    def recompute(self, rec, sections, keep_going=False):
        with caches(self.s["cache"]):
            return RV.recompute(rec, root=HERE, jobs=JOBS, log=lambda m: None, sections=sections,
                                keep_going=keep_going)

    def test_a_synthetic_draw_reverifies_equal(self):
        res = self.s["result"]
        self.assertEqual(res["refused"], [])
        self.assertEqual((res["verdict"], res["partial"], res["not_run"], res["stopped_at"]),
                         ("EQUAL", True, [], None), "\n".join(self.s["lines"][-40:]))
        self.assertEqual(list(res["sections"]), list(RV.SECTIONS))
        for name in ("identities.locked_climb_b58", "identities.generated", "identities.final", "slots", "c5",
                     "coverage", "episode_steps", "ceilings", "passes_T", "H_table", "design", "streams"):
            self.assertGreater(res["sections"][name]["values"], 0, name)
        self.assertEqual(sum(s["differences"] for s in res["sections"].values()), 0)
        self.assertTrue(res["reconstruction"]["equal"], res["reconstruction"])
        self.assertEqual((res["changed_during_run"], res["files_opened_new"]), ([], []))
        self.assertEqual(sorted(res["taus_read_from_the_record"]), sorted(self.s["record"]["engines"]))
        self.assertEqual(set(RV.RECORD_KEYS) - set(res), set())

    def test_it_wrote_nothing_in_the_tree_and_used_no_roads_seed(self):
        """roads.json, the attempts log and redraws.json are as they were (or absent), and no_roads_seed held
        for the whole run: a call it forbids would have raised inside a section, and every section is EQUAL."""
        self.assertEqual(self.s["before"], self.s["after"])
        self.assertEqual(os.listdir(self.s["out"]), [])                 # reverify itself writes nothing

    def test_a_recorded_draw_moved_by_one_ulp_is_different_and_stops_the_rest(self):
        rec = copy.deepcopy(self.s["record"])
        c = rec["roads"][0]["draws"]["climbs"][0]
        c["grade"] = math.nextafter(c["grade"], 1.0)
        out = self.recompute(rec, None)
        self.assertEqual(out["stopped_at"], "reconstruction")
        self.assertEqual(out["not_run"], list(RV.SECTIONS[1:]))
        self.assertGreater(out["sections"]["reconstruction"]["differences"], 0)
        self.assertFalse(out["reconstruction"]["equal"])

    def test_a_c5_value_moved_by_one_ulp_is_found_there(self):
        rec, path = moved(self.s["record"], "c5")
        out = self.recompute(rec, ("slots", "c5"), keep_going=True)
        self.assertEqual(section_names(out), ["c5"])
        self.assertEqual([d["path"] for d in out["sections"]["c5"]["first"]], [path])

    def test_a_ceiling_moved_by_one_ulp_is_found_there(self):
        rec, path = moved(self.s["record"], "ceilings", nth=-1)          # the last per-road number
        out = self.recompute(rec, ("ceilings", "passes_T"), keep_going=True)
        self.assertEqual(section_names(out), ["ceilings"])
        self.assertEqual([d["path"] for d in out["sections"]["ceilings"]["first"]], [path])


# =====================================================================================================
class Moves(Guarded):
    """Mistake 12: the identity alone cannot see a moved plant; C5 and the ceilings can. Each move is one part
    in 1e9 on the B58 through epa_fit.perturbed, a new plant (the frozen one untouched), given to the draw's
    code through engines.get at jobs 1, so the run stays in this process and reads the moved plant."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.enterClassContext(contract_stand_ins())
        cls.s = smoke_state()

    def moved_get(self, record, field):
        import engines
        import epa_fit
        real = engines.get

        def get(engine_id):
            p = real(engine_id)
            if engine_id != "b58":
                return p
            obj = p.car if record == "car" else p.engine.thermal
            return epa_fit.perturbed(p, record=record, field=field, value=float(getattr(obj, field)) * (1.0 + 1e-9))
        return mock.patch.object(engines, "get", get)

    def test_the_car_mass_moved_by_one_part_in_1e9_is_found_by_c5(self):
        rec = copy.deepcopy(self.s["record"])
        with caches(), self.moved_get("car", "mass"):
            out = RV.recompute(rec, root=HERE, jobs=1, log=lambda m: None, sections=("slots", "c5"), keep_going=True)
        self.assertIn("c5", section_names(out))
        # the control: the same sections on the frozen plant are equal
        with caches():
            out = RV.recompute(rec, root=HERE, jobs=1, log=lambda m: None, sections=("slots", "c5"), keep_going=True)
        self.assertEqual(section_names(out), [])

    def test_c_turb_moved_by_one_part_in_1e9_is_not_c5s_and_is_the_ceilings(self):
        """On the first road and the B58 alone (its ceilings read back from the control's run cache), so the
        moved plant's runs are few enough for one process."""
        rec = copy.deepcopy(self.s["record"])
        with caches(), self.moved_get("thermal", "c_turb"):
            out = RV.recompute(rec, root=HERE, jobs=1, log=lambda m: None, sections=("slots", "c5"), keep_going=True)
        self.assertEqual(section_names(out), [])                     # C5 reads the vehicle only
        sub = copy.deepcopy(rec)
        sub["roads"], sub["engines"] = sub["roads"][:1], ["b58"]
        with caches(self.s["cache"]):
            RC.use_recorded_taus({"b58": (float(rec["tau"]["b58"]["tau_s"]), rec["tau"]["b58"].get("cell"))})
            sub["ceilings"] = json.loads(json.dumps(R.jsonable(RC.ceilings(
                sub["roads"], engines=("b58",), ratios=tuple(rec["ratios"]), dt=R.DT, jobs=1,
                variants=tuple(rec["variants"]), readings=tuple(rec["readings"])))))
        with caches(), self.moved_get("thermal", "c_turb"):
            out = RV.recompute(sub, root=HERE, jobs=1, log=lambda m: None, sections=("ceilings",), keep_going=True)
        self.assertEqual(section_names(out), ["ceilings"])


# =====================================================================================================
class Redraws(Guarded):
    """epa_roads.redraw on the smoke draw at the smoke run's SYNTHETIC margins (the Ford's at 0.5, which every
    slot fails, epa_roads.py:1706) with the Ford dropped, its first failing slot only, so it writes both
    readings: version 6, the B58 alone gating, which every slot of the smoke draw passes at 1.9 %, redraws
    nothing; version 5, both cars gating, fails every slot on the Ford and redraws the first. Then the whole
    record and both readings re-verified by recompute, every section (sections None), under scripted 0xC5
    streams. The candidates' ceilings come from roads_ceiling's run cache, which the redraw filled: a road the
    re-verifier built otherwise would miss it and run. The C5 re-checks, the climb tests and the identities
    are computed again: once, in setUpClass (each reading as recompute computed it is kept, through a
    wrapper of _redraw_reading), and compared four ways."""
    V5 = "version 5 (every engine gating)"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.enterClassContext(contract_stand_ins())
        s = smoke_state()
        cls.record = s["record"]
        if not cls.record["passes_T"]["passes"]:
            raise unittest.SkipTest("the SYNTHETIC smoke set does not pass T, so every redraw candidate would be "
                                    "discarded after its ceilings, up to 100 times: not a unit test")
        margins = {e: (0.5 if e == "ford_27tt" else R.C5_MARGIN) for e in cls.record["engines"]}
        with caches(s["cache"]):
            red = R.redraw(cls.record, roads_sha_value="SYNTHETIC", margins=margins,
                           margins_source="SYNTHETIC margins (test_roads_reverify)", dropped=("ford_27tt",),
                           jobs=JOBS, root=HERE, log=lambda m: None, engines=tuple(cls.record["engines"]),
                           max_slots=1)
            cls.cache = dict(RC._CACHE)
        cls.redraws = json.loads(json.dumps(red, allow_nan=False))
        cls.again = {}
        real = RV._redraw_reading

        def kept(record, redraws, name, gating, **kw):
            cls.again[name] = out = real(record, redraws, name, gating, **kw)
            return out
        with caches(cls.cache), no_roads_seed(SYNTHETIC_SEED), mock.patch.object(RV, "_redraw_reading", kept):
            cls.out = RV.recompute(cls.record, root=HERE, jobs=JOBS, log=lambda m: None, sections=None,
                                   keep_going=True, redraws=cls.redraws)

    def test_both_readings_reverify_equal(self):
        r6, r5 = self.redraws["readings"]["version 6"], self.redraws["readings"][self.V5]
        self.assertEqual(sorted(self.redraws["readings"]), sorted(["version 6", self.V5]))
        self.assertEqual((r6["gating"], r5["gating"]), (["b58"], ["b58", "ford_27tt"]))
        self.assertEqual((r6["failing"], r6["slots"]), ([], []))         # the B58 alone: nothing to redraw
        self.assertEqual(len(r5["slots"]), 1)                             # the redraw path, exercised
        self.assertGreater(r5["slots"][0]["redraws"], 0)
        out = self.out
        self.assertEqual(list(out["sections"]), RV.all_sections(self.record, self.redraws))
        self.assertEqual(list(out["sections"])[-2:], ["redraws.version 6", f"redraws.{self.V5}"])
        self.assertEqual((out["not_run"], out["stopped_at"]), ([], None))
        self.assertEqual(section_names(out), [], [(n, s["first"][:3]) for n, s in out["sections"].items()
                                                   if s["differences"]])
        self.assertTrue(out["reconstruction"]["equal"], out["reconstruction"])
        self.assertGreater(out["sections"]["redraws.version 6"]["values"], 100)
        self.assertGreater(out["sections"][f"redraws.{self.V5}"]["values"], 1000)
        self.assertEqual(sorted(self.again), sorted(["version 6", self.V5]))

    def test_a_value_of_either_reading_moved_by_one_ulp_is_found(self):
        """A re-check value of each reading, and the last number of version 5's redrawn slot, moved by one
        ulp: each is found, at its path. The control: each reading as recorded is equal to its recomputation."""
        for name, key, nth in (("version 6", "recheck", 0), (self.V5, "recheck", 0), (self.V5, "slots", -1)):
            self.assertEqual(RV.compare(self.redraws["readings"][name], self.again[name])["differences"], 0, name)
            bad, path = moved(self.redraws["readings"][name], key, nth=nth)
            res = RV.compare(bad, self.again[name])
            self.assertEqual([d["path"] for d in res["first"]], [path], (name, key))

    def test_a_redraw_the_record_does_not_hold_is_found_in_its_section(self):
        """Version 5's redrawn slot's candidates emptied: the scripted 0xC5 stream holds nothing, so the first
        redraw asks for a draw the record does not hold, and the section is DIFFERENT, named (row 96: no stream
        is seeded)."""
        red = copy.deepcopy(self.redraws)
        red["readings"][self.V5]["slots"][0]["candidates"] = []
        with caches(self.cache), no_roads_seed(SYNTHETIC_SEED):
            out = RV.recompute(self.record, root=HERE, jobs=JOBS, log=lambda m: None,
                               sections=(f"redraws.{self.V5}",), keep_going=True, redraws=red)
        first = out["sections"][f"redraws.{self.V5}"]["first"]
        self.assertEqual(section_names(out), [f"redraws.{self.V5}"])
        self.assertTrue(any("NotRecorded" in str(d["now"]) for d in first), first)

    def test_the_readings_are_epa_roads_redraws(self):
        rec = {"engines": list(R.ENGINES)}
        self.assertEqual(RV.redraw_readings(rec, {"dropped": []}), [("version 6", set(R.ENGINES))])
        self.assertEqual(RV.redraw_readings(rec, {"dropped": ["ford_27tt"]}),
                         [("version 6", set(R.ENGINES) - {"ford_27tt"}),
                          ("version 5 (every engine gating)", set(R.ENGINES))])
        self.assertEqual(RV.all_sections(rec, {"dropped": ["ford_27tt"]})[-2:],
                         ["redraws.version 6", "redraws.version 5 (every engine gating)"])
        # Run 2's case (VALIDATION_DECISIONS section Q): every EPA engine dropped, the B58 alone gates version 6
        self.assertEqual(RV.redraw_readings(rec, {"dropped": sorted(R.EPA_ENGINES)}),
                         [("version 6", {R.NEVER_DROPPED}), ("version 5 (every engine gating)", set(R.ENGINES))])
        self.assertEqual(RV.all_sections(rec, None), list(RV.SECTIONS))          # before R4: no reading


# =====================================================================================================
def synthetic_redraws(root, rec, *, dropped):
    """A SYNTHETIC results/EPA_VALIDATION/summary.json (test_epa_roads.synthetic_summary: `dropped` dropped,
    each re-check margin 0.03), written through summary_opened, the guard's one exception, and a
    redraws.json built from it and root's roads.json `rec` as epa_roads.redraw builds its top level, both
    readings empty (no reading is computed), written once in root: (redraws.json as written, its sha_text)."""
    from test_epa_roads import synthetic_summary
    from thresholds import common
    assert dropped, "a drop gives epa_roads.redraw's two readings"
    spath = os.path.join(root, *R.SUMMARY_REL.split("/"))
    os.makedirs(os.path.dirname(spath))
    with RV.summary_opened(root):                      # the guard's one exception, for writing it too
        with open(spath, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(synthetic_summary({e: True for e in dropped}), fh)
        margins = R.margins_from_summary(common.load_json(spath), engines=tuple(rec["engines"]))
        source = {"path": R.SUMMARY_REL, "sha_text": common.sha_text(spath)}
    sha = R.roads_sha(os.path.join(root, *R.ROADS_REL.split("/")))
    red = {"schema": R.REDRAWS_SCHEMA, "roads_sha": sha, "seed_kind": rec["seed_kind"], "margins": margins,
           "margins_source": source, "dropped": list(dropped), "started": "SYNTHETIC",
           "readings": {"version 6": {}, "version 5 (every engine gating)": {}}, "changed_during_run": [],
           "finished": "SYNTHETIC", "files_opened": [], "steps_log": [],
           "taus_read_from_the_record": {e: rec["tau"][e]["tau_s"] for e in rec["engines"]}}
    rsha = R.write_once(os.path.join(root, *R.REDRAWS_REL.split("/")), red)
    return red, rsha


class RedrawsRecord(Guarded):
    """redraws_problems in a temporary repository holding a SYNTHETIC roads record, a SYNTHETIC summary.json
    (test_epa_roads.synthetic_summary: every EPA engine dropped, each re-check margin 0.03), a redraws.json
    built from them as epa_roads.redraw builds its top level (no reading is computed: RedrawsRecord tests the
    refusals, Redraws the readings) and, for the REAL kind, the attempts log's redraw lines as
    epa_roads.recheck_or_redraw writes them. Each refusal has its control: the record as built refuses nothing."""
    DROPPED = sorted(R.EPA_ENGINES)

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp(prefix="reverify_red_")

    def tearDown(self):
        R.install_guard(())
        shutil.rmtree(self.tmp, ignore_errors=True)

    def repo(self, kind, *, attempts=True, start=None):
        """(root, roads record, redraws.json as written) for seed_kind `kind`, committed once; `start` updates
        the attempts log's redraw start line."""
        root = tempfile.mkdtemp(prefix=f"{kind}_", dir=self.tmp)
        git(root, "init", "-q")
        rec = {"seed_kind": kind, "engines": list(R.ENGINES),
               "tau": {e: {"tau_s": 40.0 + i + 0.1, "cell": None} for i, e in enumerate(R.ENGINES)}}
        R.write_once(os.path.join(root, *R.ROADS_REL.split("/")), rec)
        red, rsha = synthetic_redraws(root, rec, dropped=self.DROPPED)
        lines = [dict({"step": "redraw", "event": "start", "attempt": 1, "kind": kind, "roads_sha": red["roads_sha"],
                       "summary": red["margins_source"], "dropped": list(self.DROPPED), "margins": red["margins"]},
                      **(start or {})),
                 {"step": "redraw", "event": "outcome", "attempt": 1, "outcome": "redraws", "sha_text": rsha}]
        if attempts:
            for x in lines:
                R.append_attempt(os.path.join(root, *R.ATTEMPTS_REL.split("/")), x)
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "SYNTHETIC records")
        return root, json.loads(json.dumps(rec)), R.load_record(os.path.join(root, *R.REDRAWS_REL.split("/")))

    def refused(self, probs, text):
        self.assertTrue(any(text in p for p in probs), probs)

    def test_the_control_and_each_refusal(self):
        root, rec, red = self.repo("SYNTHETIC")
        self.assertEqual(RV.redraws_problems(rec, red, root=root), [])           # the control
        ulp = copy.deepcopy(red)
        ulp["margins"]["ford_27tt"] = math.nextafter(ulp["margins"]["ford_27tt"], 1.0)
        cases = [(ulp, "margins_from_summary"),
                 (dict(red, dropped=["b58"] + self.DROPPED), "drops the B58"),
                 (dict(red, dropped=["mazda_25t", "ford_27tt"]), "not a sorted list"),
                 (dict(red, readings={"version 6": {}}), "epa_roads.redraw writes"),
                 (dict(red, extra=1), "neither recomputes nor names"),
                 (dict(red, seed_kind="REAL"), "seed_kind"),
                 (dict(red, changed_during_run=["epa_roads.py"]), "changed_during_run"),
                 (dict(red, margins_source=dict(red["margins_source"], path="x/summary.json")), "margins_source"),
                 (dict(red, roads_sha="0" * 64), "names roads_sha"),
                 (dict(red, schema="epa-redraws/0"), "schema")]
        tau = copy.deepcopy(red)
        tau["taus_read_from_the_record"]["b58"] = math.nextafter(tau["taus_read_from_the_record"]["b58"], 99.0)
        cases.append((tau, "taus_read_from_the_record"))
        for bad, text in cases:
            self.refused(RV.redraws_problems(rec, bad, root=root), text)
        # one engine kept by the dropped list but dropped by summary.json (the redraw's own refusal)
        kept = dict(red, dropped=["ford_27tt", "honda_l15b7"])
        self.refused(RV.redraws_problems(rec, kept, root=root), "--dropped says kept")
        # summary.json changed after the redraws: its sha_text is not margins_source's
        spath = os.path.join(root, *R.SUMMARY_REL.split("/"))
        with RV.summary_opened(root), open(spath, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(" ")
        self.refused(RV.redraws_problems(rec, red, root=root), "data input changed")
        os.remove(spath)
        self.refused(RV.redraws_problems(rec, red, root=root), "cannot be read")
        git(root, "checkout", "--", R.SUMMARY_REL)
        self.assertEqual(RV.redraws_problems(rec, red, root=root), [])           # back: the control again
        with open(os.path.join(root, *R.REDRAWS_REL.split("/")), "a", encoding="utf-8", newline="\n") as fh:
            fh.write(" ")
        self.refused(RV.redraws_problems(rec, red, root=root), "not committed at HEAD")

    def test_summary_json_is_opened_only_through_the_guards_exception(self):
        """The control of summary_opened: outside it, epa_roads' guard refuses summary.json."""
        root, rec, red = self.repo("SYNTHETIC")
        R.install_guard(())
        with self.assertRaises(PermissionError):
            open(os.path.join(root, *R.SUMMARY_REL.split("/")), encoding="utf-8").close()
        self.assertIsNotNone(RV.summary_sha(root))
        with self.assertRaises(PermissionError):                                  # nothing left allowed after
            open(os.path.join(root, *R.SUMMARY_REL.split("/")), encoding="utf-8").close()

    def test_a_real_record_needs_the_attempts_logs_redraw_lines(self):
        root, rec, red = self.repo("REAL")
        self.assertEqual(RV.redraws_problems(rec, red, root=root), [])           # the control
        root, rec, red = self.repo("REAL", attempts=False)
        self.refused(RV.redraws_problems(rec, red, root=root), "in its one redraws outcome")
        root, rec, red = self.repo("REAL", start={"dropped": ["ford_27tt"]})
        self.refused(RV.redraws_problems(rec, red, root=root), "start line does not hold")
        root, rec, red = self.repo("REAL", start={"margins": {e: 0.5 for e in R.ENGINES}})
        self.refused(RV.redraws_problems(rec, red, root=root), "start line does not hold")
        root, rec, red = self.repo("REAL", start={"attempt": 2})
        self.refused(RV.redraws_problems(rec, red, root=root), "no one start line")

    def test_a_real_record_whose_log_names_redraws_needs_redraws_json(self):
        root, rec, red = self.repo("REAL")
        real = dict(rec, companions=True, **{k: list(v) for k, v in RV.REAL_SHAPE.items()})
        missing = f"and {R.REDRAWS_REL} does not exist"
        self.assertFalse(any(missing in p for p in RV.record_problems(real, root=root)))   # the control
        os.remove(os.path.join(root, *R.REDRAWS_REL.split("/")))
        self.refused(RV.record_problems(real, root=root), missing)


# =====================================================================================================
class RealRecords(Guarded):
    """The tree's own records, as the check's preconditions read them (record_problems; redraws_problems with
    summary.json through the guard's one exception), and summary.json as its provenance reads it again after
    the run: cheap, no section computed. Skipped before the draw."""

    def test_the_trees_records_pass_their_refusals(self):
        path = os.path.join(HERE, *R.ROADS_REL.split("/"))
        if not os.path.isfile(path):
            self.skipTest("no roads.json yet")
        rec = R.load_record(path)
        self.assertEqual(RV.record_problems(rec, root=HERE), [])
        red_path = os.path.join(HERE, *R.REDRAWS_REL.split("/"))
        if not os.path.isfile(red_path):
            self.assertEqual(RV.all_sections(rec, None), list(RV.SECTIONS))
            return
        red = R.load_record(red_path)
        readings = RV.redraw_readings(rec, red)
        self.assertEqual(RV.all_sections(rec, red), list(RV.SECTIONS) + [f"redraws.{n}" for n, _ in readings])
        self.assertEqual(sorted(red["readings"]), sorted(n for n, _ in readings))
        for name, gating in readings:
            self.assertEqual(red["readings"][name]["gating"], sorted(gating), name)
        # the control (mistake 12): the same refusals see a margin moved by one ulp
        bad = copy.deepcopy(red)
        e = sorted(bad["margins"])[0]
        bad["margins"][e] = math.nextafter(bad["margins"][e], 1.0)
        self.assertTrue(any("margins" in p for p in RV.redraws_problems(rec, bad, root=HERE)))

    def test_the_summary_is_read_with_roads_ceilings_guard_installed(self):
        """The check's second read of summary.json (_provenance_now, after the recomputation) with
        roads_ceiling's guard installed in this process, as one of its in-process runs leaves it (section
        'report''s one-housing Ford tau). RV's gate, 7 November, refused the first reads and the writes of
        summary.json in six tests; this second read was found by reading reverify. Through summary_opened it
        gives redraws.json's margins_source sha_text, roads_ceiling._forbidden is put back after, and
        roads_ceiling.OPENED does not keep summary.json."""
        red_path = os.path.join(HERE, *R.REDRAWS_REL.split("/"))
        if not os.path.isfile(red_path):
            self.skipTest("no redraws.json yet (before R4)")
        red = R.load_record(red_path)
        RC.install_guard()                         # it stays for the process: a hook cannot be removed
        original, noted = RC._forbidden, set(RC.OPENED)
        self.assertTrue(original(os.path.join(HERE, *R.SUMMARY_REL.split("/"))))   # the control: it refuses it
        want = red["margins_source"]["sha_text"]
        self.assertEqual(RV.summary_sha(HERE), want)
        self.assertEqual(RC.OPENED, noted)         # the read leaves nothing (it opens summary.json alone)
        bare = {"hashes": {"files": [], "contract": []}, "engines": []}   # summary.json alone, no plant built
        self.assertEqual(RV._provenance_now(bare, root=HERE, code={}, redraws=red)["files"], {R.SUMMARY_REL: want})
        self.assertIs(RC._forbidden, original)
        self.assertNotIn(R.SUMMARY_REL, RC.OPENED)  # (its imports' first opens are noted, as without the guard's
        #                                             exception: roads_ceiling notes every repository file opened)


# =====================================================================================================
class SummaryOpened(Guarded):
    """summary_opened gives roads_ceiling's guard, which a check's in-process run installs for the rest of the
    process, the same one exception as epa_roads' guard: exactly <root>/results/EPA_VALIDATION/summary.json,
    inside the block only, put back after, an error inside included. SYNTHETIC: a temporary root, never the
    tree's records."""

    def setUp(self):
        super().setUp()
        self.root = tempfile.mkdtemp(prefix="reverify_sum_")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.addCleanup(R.install_guard, ())
        self.addCleanup(setattr, RC, "_forbidden", RC._forbidden)   # back even under a mutation of the fix
        RC.install_guard()
        self.spath = os.path.join(self.root, *R.SUMMARY_REL.split("/"))
        os.makedirs(os.path.dirname(self.spath))

    def test_the_one_path_inside_and_nothing_else(self):
        from thresholds import common
        original = RC._forbidden
        other = os.path.join(os.path.dirname(self.spath), "summary_other.json")
        csv = os.path.join(self.root, "SYNTHETIC.csv")
        self.assertTrue(original(self.spath))                      # the control: outside, refused
        with RV.summary_opened(self.root) as path:
            self.assertEqual(os.path.normcase(path), os.path.normcase(os.path.abspath(self.spath)))
            self.assertFalse(RC._forbidden(self.spath))
            self.assertFalse(RC._forbidden(self.spath.encode()))    # the hook passes bytes as well as str
            self.assertTrue(RC._forbidden(other))                  # the one path only
            self.assertTrue(RC._forbidden(csv))
            with open(self.spath, "w", encoding="utf-8", newline="\n") as fh:
                json.dump({"SYNTHETIC": True}, fh)
            want = common.sha_text(self.spath)
        self.assertIs(RC._forbidden, original)
        self.assertTrue(RC._forbidden(self.spath))
        R.install_guard((self.spath,))             # epa_roads' guard lets it open: only roads_ceiling's refuses
        with self.assertRaisesRegex(PermissionError, "roads_ceiling guard: refused to open"):
            open(self.spath, encoding="utf-8").close()
        R.install_guard(())
        self.assertEqual(RV.summary_sha(self.root), want)

    def test_put_back_after_an_error_inside(self):
        original = RC._forbidden
        with self.assertRaisesRegex(ValueError, "SYNTHETIC error inside"):
            with RV.summary_opened(self.root):
                raise ValueError("SYNTHETIC error inside")
        self.assertIs(RC._forbidden, original)
        self.assertTrue(RC._forbidden(self.spath))


# =====================================================================================================
def tree_copy(dst):
    """roads.json's 35 hashed files with the contract as SYNTHETIC stand-ins (test_epa_roads.hashed_copy), this
    module's closure, each EPA engine's complete.json (row 94's engine_sha) and one SYNTHETIC data input,
    copied to dst. Returns the data input's path."""
    hashed_copy(dst)
    files = set(RV.code_files(root=HERE)) | {f"{R.CALIBRATION_REL}/{e}/complete.json" for e in R.EPA_ENGINES}
    for f in sorted(files):
        p = os.path.join(dst, *f.split("/"))
        if not os.path.exists(p):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            shutil.copyfile(os.path.join(HERE, *f.split("/")), p)
    data = "data/SYNTHETIC_input.json"
    os.makedirs(os.path.join(dst, "data"), exist_ok=True)
    with open(os.path.join(dst, *data.split("/")), "w", encoding="utf-8", newline="\n") as fh:
        fh.write('{"SYNTHETIC": true}\n')
    return data


def tree_record(root, data):
    """A SYNTHETIC roads record of the tree at root for the preconditions: its hashes (epa_roads.provenance),
    the data input, two roads paired with evaluate.EPISODES, a tau per engine, and every other key present
    with a stand-in value (none of them is recomputed here)."""
    from thresholds import common
    eps = R.frozen_episodes(root=root)
    rec = {"schema": R.ROADS_SCHEMA, "seed_kind": "SYNTHETIC", "engines": list(R.ENGINES), "ratios": [1.5],
           "variants": ["cg", "a"], "readings": ["noknock"], "companions": False,
           "hashes": R.provenance(root=root, engines=R.ENGINES), "files_opened": R.files_opened(),
           "data_inputs": {data: common.sha_text(os.path.join(root, *data.split("/")))},
           "roads": [{"k": i, "episode_seed": s, "weights": [float(w) for w in ws]} for i, (s, ws) in enumerate(eps[:2])],
           "tau": {e: {"tau_s": 40.0 + i, "cell": None} for i, e in enumerate(R.ENGINES)},
           "steps_log": [], "commit_reveal": {"SYNTHETIC": True, "roads_seed": SYNTHETIC_SEED}}
    rec.update({k: None for k in RV.SECTION_KEYS})
    return json.loads(json.dumps(rec))


def canned(record, *, differences=0):
    """A stand-in for recompute: every section asked for computed (all_sections when `sections` is None),
    in all_sections' order, `differences` in the first; the others named not_run, as recompute names them."""
    def run(rec, *, root, jobs, log, sections, keep_going, redraws=None):
        full = RV.all_sections(rec, redraws)
        names = [n for n in full if sections is None or n in sections]
        secs = {n: {"values": 1, "differences": differences if i == 0 else 0, "first": []}
                for i, n in enumerate(names)}
        return {"sections": secs, "not_run": [n for n in full if n not in names], "stopped_at": None,
                "reconstruction": {"generated_arrays_sha256": None, "steps_log_step2": None,
                                   "final_arrays_sha256": None, "steps_log_step4a": None, "equal": True}}
    return run


def acting(act):
    """canned, with act() called while it runs: a stand-in for recompute that changes the tree or opens a
    file in the middle of the run, as a section of the real one could."""
    run = canned(None)

    def go(rec, **kw):
        act()
        return run(rec, **kw)
    return go


@contextlib.contextmanager
def clean_env():
    """The environment every command runs in (rows 118, 126; rule 1.10), whatever the test runner's."""
    with mock.patch.dict(os.environ, ENV_OK), mock.patch.object(sys, "dont_write_bytecode", True):
        yield


class Refusals(Guarded):
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp(prefix="reverify_ref_")
        self.root = os.path.join(self.tmp, "tree")
        self.data = tree_copy(self.root)
        self.rec = tree_record(self.root, self.data)
        git(self.root, "init", "-q")                    # committed, as the tree a record is re-verified on: the
        git(self.root, "add", "-A")                     # draw's evaluate.py is HEAD's (draw_episodes)
        git(self.root, "commit", "-q", "-m", "SYNTHETIC tree")
        self.out = os.path.join(self.tmp, "out")
        self.enterContext(clean_env())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def problems(self, rec=None, out=None):
        return RV.preconditions(self.rec if rec is None else rec, root=self.root, mode="check",
                                out_dir=self.out if out is None else out)

    def test_the_control_is_refused_nothing(self):
        probs, ctx = self.problems()
        self.assertEqual(probs, [])
        self.assertEqual(ctx["hashed_files"]["changed_since_draw"], [])
        self.assertEqual((ctx["contract_equal"], ctx["data_inputs_equal"], ctx["head"], ctx["tree_changes"]),
                         (True, True, git(self.root, "rev-parse", "HEAD"), []))
        self.assertEqual(sorted(ctx["plants"]), sorted(R.ENGINES))
        self.assertIn(RV.MODULE_REL, ctx["code"])

    def test_each_hashed_file_changed_by_one_byte(self):
        files = sorted(self.rec["hashes"]["files"])
        self.assertEqual(len(files), len(set(R.hashed_files(root=HERE, engines=R.ENGINES))))
        for f in files:
            p = os.path.join(self.root, *f.split("/"))
            old, i = flip_one_byte(p)
            probs, ctx = self.problems()
            if f in RV.MAY_DIFFER:
                self.assertEqual(probs, [], f)
                self.assertEqual(ctx["hashed_files"]["changed_since_draw"], [f])
            else:
                self.assertEqual(len(probs), 1, (f, probs))
                self.assertTrue(probs[0].startswith(f"{f}: its sha_text is not roads.json's"), probs)
            with open(p, "rb") as fh:
                raw = bytearray(fh.read())
            raw[i] = old
            with open(p, "wb") as fh:
                fh.write(bytes(raw))
        self.assertEqual(self.problems()[0], [])
        self.assertEqual(sorted(set(RV.MAY_DIFFER) - set(files)), [])     # every one of them is hashed

    def test_evaluate_may_differ_but_not_its_episodes_or_its_imports(self):
        """Amendment P4.1's two controls: evaluate.py may differ (P edits it, row 138 (1)), but an edit to
        EPISODES and an import added to it are refused; and EPISODES is the whole tuple the draw read, so an
        entry appended, the last entry removed (no road of the record uses it: the record pairs two roads, so
        only the length can refuse it) and an entry no road uses changed are refused too."""
        p = os.path.join(self.root, "evaluate.py")
        with open(p, encoding="utf-8", newline="") as fh:
            text = fh.read()
        n = len(R.frozen_episodes(root=self.root))
        lines = text[text.index("EPISODES = ("):].split("\n")
        first, sixth, last = lines[1], lines[6], lines[n]                 # "    (1000, (0.690154, ...)),"
        self.assertTrue(lines[n + 1].startswith(")"), lines[n + 1])      # one line per entry: `last` is the last
        end = text.index("\n)", text.index("EPISODES = ("))               # the tuple's closing line
        for edited, want in ((text.replace(first, first.replace("0.", "0.1", 1), 1),
                              ["road 0: its episode seed and weights are not evaluate.EPISODES[0]"]),
                             (text[:end] + "\n    (1020, (0.6, 0.1, 0.3))," + text[end:],
                              [f"evaluate.EPISODES holds {n + 1} episodes, and the draw's held {n}: the whole tuple "
                               "is the draw's (row 140 (2))"]),
                             (text.replace(last + "\n", "", 1),
                              [f"evaluate.EPISODES holds {n - 1} episodes, and the draw's held {n}: the whole tuple "
                               "is the draw's (row 140 (2))"]),
                             (text.replace(sixth, sixth.replace("0.", "0.1", 1), 1),
                              ["evaluate.EPISODES[5] is not the draw's"])):
            with open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write(edited)
            probs, ctx = self.problems()
            self.assertEqual(probs, want)
            self.assertEqual(ctx["hashed_files"]["changed_since_draw"], ["evaluate.py"])
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(text + "\nimport four_engine_roads  # noqa: SYNTHETIC\n")
        self.assertEqual(self.problems()[0], ["four_engine_roads.py: reached by the code as it stands, not hashed "
                                              "by roads.json"])
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        self.assertEqual(self.problems()[0], [])

    def test_the_draws_episodes_are_read_from_its_evaluate_py(self):
        """draw_episodes: the tree's tuple while evaluate.py is the draw's; once it is not, the version in HEAD's
        history that is, even when the tree's EPISODES differs (here one entry longer); and none, refused, when
        no committed version has roads.json's sha_text. _episodes_of reads as epa_roads.frozen_episodes does."""
        p = os.path.join(self.root, "evaluate.py")
        with open(p, encoding="utf-8", newline="") as fh:
            text = fh.read()
        self.assertEqual(RV._episodes_of(text), R.frozen_episodes(root=self.root))
        eps = R.frozen_episodes(root=self.root)
        self.assertEqual(RV.draw_episodes(self.rec, root=self.root), (eps, None))
        end = text.index("\n)", text.index("EPISODES = ("))
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(text[:end] + "\n    (1020, (0.6, 0.1, 0.3))," + text[end:])
        self.assertEqual(len(R.frozen_episodes(root=self.root)), len(eps) + 1)
        self.assertEqual(RV.draw_episodes(self.rec, root=self.root), (eps, None))       # HEAD's blob, the draw's
        rec = copy.deepcopy(self.rec)
        rec["hashes"]["files"]["evaluate.py"] = "0" * 64
        drawn, why = RV.draw_episodes(rec, root=self.root)
        self.assertIsNone(drawn)
        self.assertIn("cannot be compared whole", why)

    def one(self, probs, text):
        self.assertEqual(len(probs), 1, probs)
        self.assertIn(text, probs[0])

    def test_the_record_and_the_environment(self):
        cases = []
        rec = copy.deepcopy(self.rec)
        rec["hashes"]["versions"]["numpy"] = "0.0.0"
        cases.append((rec, "versions.numpy"))
        rec = copy.deepcopy(self.rec)
        rec["hashes"]["plants"]["b58"]["engine_sha"] = "0" * 16
        cases.append((rec, "b58: engine_sha"))
        rec = copy.deepcopy(self.rec)
        del rec["tau"]["ford_27tt"]
        cases.append((rec, "holds no tau for ford_27tt"))
        rec = copy.deepcopy(self.rec)
        rec["something_new"] = 1
        cases.append((rec, "neither recomputes nor names"))
        for rec, text in cases:
            self.one(self.problems(rec)[0], text)
        with mock.patch.dict(os.environ, {"OMP_NUM_THREADS": "4"}):
            self.one(self.problems()[0], "OMP_NUM_THREADS")
        with mock.patch.object(sys, "dont_write_bytecode", False):
            self.one(self.problems()[0], "-B")

    def test_an_epa_engines_complete_json_naming_another_engine_sha(self):
        """Row 94: each EPA engine's engine_sha is the one its complete.json names, read from the tree, here
        one engine's rewritten with another; restored, nothing is refused (the control)."""
        e = R.EPA_ENGINES[0]
        p = os.path.join(self.root, *R.CALIBRATION_REL.split("/"), e, "complete.json")
        with open(p, "rb") as fh:
            raw = fh.read()
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(dict(json.loads(raw), engine_sha="0" * 16), fh)
        probs = self.problems()[0]
        self.assertEqual(len(probs), 1, probs)
        self.assertTrue(probs[0].startswith(f"{e}: engine_sha ") and probs[0].endswith("is not its complete.json's "
                                                                                      + "0" * 16 + " (row 94)"), probs)
        with open(p, "wb") as fh:
            fh.write(raw)
        self.assertEqual(self.problems()[0], [])

    def test_the_tree(self):
        from thresholds import common
        c = os.path.join(self.root, *R.CONTRACT_FILES[0].split("/"))
        flip_one_byte(c)
        self.one(self.problems()[0], "the contract's sha_text")
        with open(c, "w", encoding="utf-8", newline="\n") as fh:      # hashed_copy's stand-in back
            fh.write(f"SYNTHETIC stand-in for {R.CONTRACT_FILES[0]}: the test's copy, never the contract\n")
        self.assertEqual(self.problems()[0], [])
        d = os.path.join(self.root, *self.data.split("/"))
        with open(d, "a", encoding="utf-8") as fh:
            fh.write(" ")
        self.one(self.problems()[0], "the data input's sha_text")
        with open(d, "w", encoding="utf-8", newline="\n") as fh:
            fh.write('{"SYNTHETIC": true}\n')
        self.assertEqual(common.sha_text(d), self.rec["data_inputs"][self.data])
        os.makedirs(os.path.join(self.root, "epa_stats"))
        with open(os.path.join(self.root, "epa_stats", "__init__.py"), "w", encoding="utf-8") as fh:
            fh.write("# SYNTHETIC shadow\n")
        probs = self.problems()[0]                                   # the hashed closure's and this module's
        self.assertTrue(probs and all("epa_stats.py is shadowed" in p for p in probs), probs)
        shutil.rmtree(os.path.join(self.root, "epa_stats"))
        os.makedirs(os.path.join(self.root, "__pycache__"))
        with open(os.path.join(self.root, "__pycache__", "epa_stats.cpython-313.pyc"), "wb") as fh:
            fh.write(b"SYNTHETIC")
        self.one(self.problems()[0], "a bytecode cache beside a hashed file")
        shutil.rmtree(os.path.join(self.root, "__pycache__"))
        self.assertEqual(self.problems()[0], [])
        for d in ((".venv", "__pycache__"), (".venv", "Lib", "site-packages", "__pycache__")):   # the venv's own
            os.makedirs(os.path.join(self.root, *d))                       # caches, frozen (row 146 (8)), and
            with open(os.path.join(self.root, *d, "epa_stats.cpython-313.pyc"), "wb") as fh:    # named as the
                fh.write(b"SYNTHETIC")                                     # one above: never looked at
        self.assertEqual(self.problems()[0], [])

    def test_the_plant_commits_two_defaults_and_the_road_shape(self):
        import engine_env as E
        with mock.patch.object(E, "REWARD_KNOCK_DEFAULT", False, create=True):
            self.one(self.problems()[0], "REWARD_KNOCK_DEFAULT")
        with mock.patch.object(E, "REWARD_KNOCK_DEFAULT", True, create=True), \
                mock.patch.object(E, "PREVIEW_H_S", 30.0, create=True), \
                mock.patch.object(E, "preview_samples", lambda h: tuple(E.PREVIEW_S), create=True):
            self.assertEqual(self.problems()[0], [])                 # P's defaults as the draw's: the control
            with mock.patch.object(E, "preview_samples", lambda h: (h,), create=True):
                self.one(self.problems()[0], "PREVIEW_S")

        def bad():
            raise AssertionError("epa_roads.check_engine_env: RAMP_S 8.0 is not engine_env.GRADE_RAMP_S 9.0")
        with mock.patch.object(R, "check_engine_env", bad):
            self.one(self.problems()[0], "GRADE_RAMP_S")

    def test_the_out_folder(self):
        self.one(self.problems(out=os.path.join(HERE, "no_such_folder_reverify"))[0], "inside a git work tree")
        os.makedirs(self.out)
        with open(os.path.join(self.out, RV.CHECK_NAME), "w", encoding="utf-8") as fh:
            fh.write("{}\n")
        self.one(self.problems()[0], "written once")
        # an --out the guards would refuse to write in, refused before the run (its control: self.out, above,
        # refused only for the file it already holds)
        for name in ("EPA_VALIDATION_out", os.path.join("logs", "epa_out")):
            self.one(self.problems(out=os.path.join(self.tmp, name))[0], "the audit guards refuse to open")

    def test_a_refused_run_computes_nothing(self):
        rec = copy.deepcopy(self.rec)
        rec["hashes"]["versions"]["numpy"] = "0.0.0"

        def reached(*a, **k):
            raise AssertionError("computed something after a refusal")
        with mock.patch.object(RV, "recompute", reached):
            res = RV.reverify(root=self.root, jobs=1, mode="check", out_dir=self.out, log=lambda m: None, record=rec)
        self.assertEqual((res["verdict"], res["not_run"], res["sections"]), ("REFUSED", list(RV.SECTIONS), {}))
        self.assertEqual(RV.EXIT[res["verdict"]], 2)


# =====================================================================================================
class RecordMode(Guarded):
    """A temporary repository holding the hashed files, a SYNTHETIC roads.json committed once, and a bare
    remote whose GRA-test holds HEAD. recompute is a stand-in (canned): what is tested is where each command
    writes and what it refuses, not the numbers, which Control and FullShape test."""

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp(prefix="reverify_rec_")
        self.root = os.path.join(self.tmp, "repo")
        data = tree_copy(self.root)
        R.write_once(os.path.join(self.root, *R.ROADS_REL.split("/")), tree_record(self.root, data))
        git(self.root, "init", "-q", "-b", "GRA-test")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "SYNTHETIC tree")
        self.remote = os.path.join(self.tmp, "remote.git")
        git(self.tmp, "init", "-q", "--bare", self.remote)
        git(self.root, "remote", "add", "origin", self.remote)
        self.push()
        self.out = os.path.join(self.tmp, "out")
        self.enterContext(clean_env())
        self.enterContext(mock.patch.object(RV, "recompute", canned(None)))
        self.lines = []

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def push(self):
        git(self.root, "push", "-q", "origin", "HEAD:refs/heads/GRA-test")

    def commit(self, *paths, msg="SYNTHETIC"):
        git(self.root, "add", "--", *paths)
        git(self.root, "commit", "-q", "-m", msg)

    def record(self, supersede=None):
        return RV.run_record(root=self.root, jobs=1, supersede=supersede, log=self.lines.append, steps=self.lines)

    def check(self, out=None, skip_companions=False):
        return RV.run_check(root=self.root, jobs=1, out_dir=self.out if out is None else out,
                            skip_companions=skip_companions, keep_going=False, log=self.lines.append, steps=self.lines)

    def path(self, rel):
        return os.path.join(self.root, *rel.split("/"))

    def adopt_refused(self, path, text):
        """adopt refuses the result at `path`, `text` among its reasons (mistake 12: no other refusal stands
        in for it)."""
        name = os.path.basename(path)                                 # which bad result, when one is adopted
        with self.assertRaises(R.Refused, msg=f"adopted {name}, and it should be refused: {text}") as cm:
            RV.adopt(path, root=self.root, log=self.lines.append)
        self.assertTrue(any(text in p for p in cm.exception.args[0]), (text, cm.exception.args[0]))

    def test_record_writes_once_and_supersede_writes_the_next(self):
        self.assertEqual(self.record(), 0)
        rec = R.load_record(self.path(RV.OUT_REL))
        self.assertEqual(list(rec), list(RV.RECORD_KEYS))
        self.assertEqual((rec["mode"], rec["verdict"], rec["partial"], rec["tree_changes"], rec["supersedes"]),
                         ("record", "EQUAL", False, [], None))
        self.assertEqual((rec["head"], rec["pushed"], rec["clean"]), (git(self.root, "rev-parse", "HEAD"), True, True))
        self.assertEqual(rec["roads_sha"], R.roads_sha(self.path(R.ROADS_REL)))
        with self.assertRaises(R.Refused):
            self.record()                                            # written once
        self.commit(RV.OUT_REL)
        self.push()
        self.assertEqual(FR.current_reverify(root=self.root)[0], RV.OUT_REL)
        with self.assertRaises(R.Refused):
            self.record()                                            # committed: a re-made P supersedes it
        self.assertEqual(self.record(supersede=150), 0)
        rel = f"{R.ROADS_DIR_REL}/reverify_2.json"
        from thresholds import common
        self.assertEqual(R.load_record(self.path(rel))["supersedes"],
                         {"path": RV.OUT_REL, "sha_text": common.sha_text(self.path(RV.OUT_REL)), "row": 150})
        self.commit(rel)
        self.push()
        self.assertEqual(FR.current_reverify(root=self.root)[0], rel)
        self.assertEqual(self.record(supersede=151), 0)
        self.assertTrue(os.path.isfile(self.path(f"{R.ROADS_DIR_REL}/reverify_3.json")))

    def test_record_refusals(self):
        with open(self.path("untracked.txt"), "w", encoding="utf-8") as fh:
            fh.write("x\n")
        self.assertEqual(self.record(), 2)                           # a dirty tree
        os.remove(self.path("untracked.txt"))
        with open(self.path("notes.txt"), "w", encoding="utf-8") as fh:
            fh.write("x\n")
        self.commit("notes.txt")
        self.assertEqual(self.record(), 2)                           # HEAD not in origin's GRA-test
        self.push()
        red = {"schema": R.REDRAWS_SCHEMA, "roads_sha": "0" * 64, "readings": {}}
        R.write_once(self.path(R.REDRAWS_REL), red)
        self.commit(R.REDRAWS_REL)
        self.push()
        self.assertEqual(self.record(), 2)                           # redraws.json of another roads_sha
        self.assertTrue(any("names roads_sha" in x for x in self.lines), self.lines[-5:])
        self.assertFalse(os.path.exists(self.path(RV.OUT_REL)))

    def test_an_uncommitted_roads_json_or_a_different_result_writes_nothing(self):
        p = self.path(R.ROADS_REL)
        rec = R.load_record(p)
        rec["companions"] = True
        os.remove(p)
        R.write_once(p, rec)
        self.assertEqual(self.record(), 2)
        self.assertTrue(any("not committed at HEAD" in x for x in self.lines), self.lines[-5:])
        git(self.root, "checkout", "--", R.ROADS_REL)
        with mock.patch.object(RV, "recompute", canned(None, differences=1)):
            self.assertEqual(self.record(), 1)
        self.assertEqual(git(self.root, "status", "--porcelain"), "")       # nothing written in results/

    def test_check_writes_only_under_out_and_once(self):
        self.assertEqual(self.check(), 0)
        res = R.load_record(os.path.join(self.out, RV.CHECK_NAME))
        self.assertEqual((res["verdict"], res["partial"], res["mode"]), ("EQUAL", False, "check"))
        self.assertEqual(git(self.root, "status", "--porcelain"), "")
        before = open(os.path.join(self.out, RV.CHECK_NAME), "rb").read()
        self.assertEqual(self.check(), 2)                            # written once
        self.assertEqual(open(os.path.join(self.out, RV.CHECK_NAME), "rb").read(), before)
        inside = self.path("results/inside")
        self.assertEqual(self.check(out=inside), 2)
        self.assertFalse(os.path.exists(inside))
        self.assertEqual(git(self.root, "status", "--porcelain"), "")

    def test_skip_companions_leaves_report_out_and_is_not_adopted(self):
        """RV's control, `check --skip-companions` (row 140 (3)): EQUAL, exit 0, roads_ceiling.report left out
        and named not run, so the result is partial, and adopt refuses it. The control (mistake 12): the same
        check without the flag computes report, is complete, and is adopted."""
        full = os.path.join(self.tmp, "out_full")
        for out, skip in ((self.out, True), (full, False)):
            self.assertEqual(self.check(out=out, skip_companions=skip), 0, skip)
        res = R.load_record(os.path.join(self.out, RV.CHECK_NAME))
        self.assertEqual((res["verdict"], res["partial"], res["not_run"]), ("EQUAL", True, ["report"]))
        self.assertNotIn("report", res["sections"])
        self.assertEqual(list(res["sections"]), [s for s in RV.SECTIONS if s != "report"])
        self.adopt_refused(os.path.join(self.out, RV.CHECK_NAME), "the result's partial is True, not False")
        ctrl = R.load_record(os.path.join(full, RV.CHECK_NAME))
        self.assertEqual((ctrl["verdict"], ctrl["partial"], ctrl["not_run"], list(ctrl["sections"])),
                         ("EQUAL", False, [], list(RV.SECTIONS)))
        RV.adopt(os.path.join(full, RV.CHECK_NAME), root=self.root, log=self.lines.append)

    def test_an_input_changed_or_a_file_opened_during_the_run_is_refused(self):
        """reverify's two refusals after the run (as epa_roads.first_draw's unchanged(), epa_roads.py:1321-1328),
        each made by a stand-in recompute that acts while it runs (acting): engine_env.py, a MAY_DIFFER file
        the preconditions let differ, one byte longer at the end of the run than at its start
        (changed_during_run), and a repository file opened that neither the draw nor the redraws opened
        (files_opened_new; epa_roads' guard records the files under this repository, epa_roads.py:217-234).
        Each is REFUSED with exit 2 and its refusal named, and adopt refuses the result written. The control
        (mistake 12): the stand-in doing nothing is EQUAL, exit 0, and adopted."""
        e = self.path("engine_env.py")
        new = next((f for f in (".gitignore", "CLAUDE.md", "README.md") if f not in R.files_opened()
                    and os.path.isfile(os.path.join(HERE, f))), None)
        self.assertIsNotNone(new, "every candidate file was opened earlier in this process")

        def grow():
            with open(e, "a", encoding="utf-8", newline="\n") as fh:
                fh.write("#")

        def read_new():
            with open(os.path.join(HERE, new), encoding="utf-8") as fh:
                fh.read(1)
        cases = (("control", lambda: None, 0, ("EQUAL", [], []), None),
                 ("changed", grow, 2, ("REFUSED", ["engine_env.py"], []),
                  "changed while the run lasted: ['engine_env.py']"),
                 ("opened", read_new, 2, ("REFUSED", [], [new]),
                  f"opened by this run and neither by the draw nor by the redraws: [{new!r}]"))
        for name, act, code, want, text in cases:
            out = os.path.join(self.tmp, f"out_{name}")
            with mock.patch.object(RV, "recompute", acting(act)):
                self.assertEqual(self.check(out=out), code, name)
            path = os.path.join(out, RV.CHECK_NAME)
            res = R.load_record(path)
            self.assertEqual((res["verdict"], res["changed_during_run"], res["files_opened_new"]), want, name)
            if text is None:
                self.assertEqual(res["refused"], [])
                RV.adopt(path, root=self.root, log=self.lines.append)      # the control is adopted
                os.remove(self.path(RV.OUT_REL))                          # untracked: the cases below are not
                continue                                                  # refused for it
            self.assertEqual(res["refused"], [text], name)
            key = "changed_during_run" if name == "changed" else "files_opened_new"
            self.adopt_refused(path, f"the result's {key} is {res[key]!r}, not []")

    def test_adopt(self):
        """adopt takes a complete EQUAL check of HEAD, pushed, still what the tree holds, and refuses every
        other result, each by its text: partial, DIFFERENT or stale; one that did not compute every section
        of the tree's records (a reading of redraws.json left out, partial False), or computed every one with
        a difference in one while its verdict says EQUAL (a hand-edited result); one that names refusals or
        whose reconstruction is not equal; another redraws_sha; and a tree changed since the check, a hashed
        file or redraws.json's one data input (summary.json, which only record_problems re-hashes). The tree
        holds a SYNTHETIC redraws.json and summary.json (synthetic_redraws), so the check computes SECTIONS
        and both readings. The control (mistake 12): after every refusal, the unchanged result is adopted."""
        roads = R.load_record(self.path(R.ROADS_REL))
        red, red_sha = synthetic_redraws(self.root, roads, dropped=sorted(R.EPA_ENGINES))
        self.commit(R.REDRAWS_REL, R.SUMMARY_REL)
        self.push()
        e = self.path("engine_env.py")                               # P's candidate tree: a MAY_DIFFER change
        with open(e, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("\n# SYNTHETIC: P's change\n")
        self.assertEqual(self.check(), 0)
        res_path = os.path.join(self.out, RV.CHECK_NAME)
        res = R.load_record(res_path)
        self.assertEqual([c["path"] for c in res["tree_changes"]], ["engine_env.py"])
        r5 = "redraws.version 5 (every engine gating)"
        self.assertEqual(list(res["sections"]), list(RV.SECTIONS) + ["redraws.version 6", r5])
        self.assertEqual((res["partial"], res["redraws_sha"]), (False, red_sha))
        refusals = "the result names refusals, or its reconstruction is not equal"
        for key, bad, text in (
                ("partial", dict(res, partial=True), "the result's partial is True, not False"),
                ("verdict", dict(res, verdict="DIFFERENT"), "the result's verdict is 'DIFFERENT', not 'EQUAL'"),
                ("head", dict(res, head="0" * 40), "it is stale"),
                ("sections", dict(res, sections={k: v for k, v in res["sections"].items() if k != r5}),
                 "are not every section of the tree's records"),
                ("differences", dict(res, sections={**res["sections"],                 # every section, but
                                                    "c5": dict(res["sections"]["c5"], differences=1)}),  # not each equal
                 "are not every section of the tree's records"),
                ("refused", dict(res, refused=["x"]), refusals),
                ("reconstruction", dict(res, reconstruction=dict(res["reconstruction"], equal=False)), refusals),
                ("redraws_sha", dict(res, redraws_sha="0" * 64), "the result's redraws_sha is not redraws.json's")):
            p = os.path.join(self.tmp, f"bad_{key}.json")
            R.write_once(p, bad)
            self.adopt_refused(p, text)
        with open(e, "a", encoding="utf-8", newline="\n") as fh:     # re-hashed: changed since the check
            fh.write("# and again\n")
        self.adopt_refused(res_path, "engine_env.py: its sha_text is not the result's")
        git(self.root, "checkout", "--", "engine_env.py")
        with open(e, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("\n# SYNTHETIC: P's change\n")
        spath = self.path(R.SUMMARY_REL)                              # redraws.json's data input, changed since
        with RV.summary_opened(self.root), open(spath, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(" ")
        self.adopt_refused(res_path, "the redraws' data input changed")
        git(self.root, "checkout", "--", R.SUMMARY_REL)
        RV.adopt(res_path, root=self.root, log=self.lines.append)
        rec = R.load_record(self.path(RV.OUT_REL))
        self.assertEqual((rec["mode"], rec["verdict"], list(rec)), ("adopted-check", "EQUAL", list(RV.RECORD_KEYS)))
        self.assertEqual((rec["roads_sha"], rec["redraws_sha"]), (red["roads_sha"], red_sha))
        self.adopt_refused(res_path, f"{RV.OUT_REL} exists: it is written once")      # reverify.json exists


# =====================================================================================================
class CurrentReverify(Guarded):
    def setUp(self):
        super().setUp()
        self.root = tempfile.mkdtemp(prefix="reverify_cur_")
        git(self.root, "init", "-q")
        self.put(R.ROADS_REL, {"SYNTHETIC": "roads"})
        self.roads_sha = R.roads_sha(os.path.join(self.root, *R.ROADS_REL.split("/")))
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "roads")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def put(self, rel, obj, commit=False):
        p = os.path.join(self.root, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(obj, fh)
        if commit:
            git(self.root, "add", "--", rel)
            git(self.root, "commit", "-q", "-m", rel)

    def rec(self, n, roads_sha=None, redraws_sha=None):
        return {"n": n, "roads_sha": self.roads_sha if roads_sha is None else roads_sha, "redraws_sha": redraws_sha}

    def current(self):
        cur = FR.current_reverify(root=self.root)
        return None if cur is None else (cur[0], cur[1]["n"])

    def test_the_highest_tracked_unmodified_matching_record(self):
        d = R.ROADS_DIR_REL
        self.assertIsNone(self.current())
        self.put(FR.REVERIFY_REL, self.rec(1))
        self.assertIsNone(self.current())                            # untracked
        git(self.root, "add", "--", FR.REVERIFY_REL)
        self.assertIsNone(self.current())                            # staged, not at HEAD
        git(self.root, "commit", "-q", "-m", "1")
        self.assertEqual(self.current(), (FR.REVERIFY_REL, 1))
        self.put(f"{d}/reverify_2.json", self.rec(2), commit=True)
        self.assertEqual(self.current(), (f"{d}/reverify_2.json", 2))
        self.put(f"{d}/reverify_3.json", self.rec(3, roads_sha="0" * 64), commit=True)    # another roads.json
        for name in ("reverify_02.json", "reverify_1.json", "reverify_x.json"):           # not a successor's name
            self.put(f"{d}/{name}", self.rec(9), commit=True)
        self.put("results/reverify_9.json", self.rec(9), commit=True)                   # not in the folder
        self.assertEqual(self.current(), (f"{d}/reverify_2.json", 2))
        self.assertEqual(FR.reverify_paths(root=self.root), [(1, FR.REVERIFY_REL), (2, f"{d}/reverify_2.json"),
                                                             (3, f"{d}/reverify_3.json")])
        self.put(f"{d}/reverify_2.json", self.rec(22))               # modified in the work tree
        self.assertEqual(self.current(), (FR.REVERIFY_REL, 1))
        git(self.root, "checkout", "--", f"{d}/reverify_2.json")
        self.put(R.REDRAWS_REL, {"SYNTHETIC": "redraws"}, commit=True)  # R4: every record named no redraws_sha
        self.assertIsNone(self.current())
        red = R.roads_sha(os.path.join(self.root, *R.REDRAWS_REL.split("/")))
        self.put(f"{d}/reverify_4.json", self.rec(4, redraws_sha=red), commit=True)
        self.assertEqual(self.current(), (f"{d}/reverify_4.json", 4))

    def test_outside_a_git_work_tree_nothing_is_listed(self):
        tmp = tempfile.mkdtemp(prefix="reverify_nogit_")
        try:
            self.assertEqual(FR.reverify_paths(root=tmp), [])
            self.assertIsNone(FR.current_reverify(root=tmp))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# =====================================================================================================
class ReferenceCommit(Guarded):
    def test_the_one_commit_that_added_the_file(self):
        from thresholds import common
        root = tempfile.mkdtemp(prefix="reverify_refc_")
        try:
            git(root, "init", "-q")
            p = os.path.join(root, "a.json")
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("1\n")
            git(root, "add", "a.json")
            git(root, "commit", "-q", "-m", "add")
            added = git(root, "rev-parse", "HEAD")
            sha1 = common.sha_text(p)
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("2\n")
            git(root, "commit", "-q", "-am", "edit")
            self.assertEqual(RV.reference_commit("a.json", root=root), added)
            self.assertEqual(RV.blob_sha_text(added, "a.json", root=root), sha1)
            self.assertNotEqual(RV.blob_sha_text("HEAD", "a.json", root=root), sha1)     # the control
            self.assertIsNone(RV.blob_sha_text(added, "absent.json", root=root))
            with self.assertRaises(R.Refused):
                RV.reference_commit("absent.json", root=root)                         # never added
            git(root, "rm", "-q", "a.json")
            git(root, "commit", "-q", "-m", "delete")
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("3\n")
            git(root, "add", "a.json")
            git(root, "commit", "-q", "-m", "add again")
            with self.assertRaises(R.Refused):
                RV.reference_commit("a.json", root=root)                              # added twice
        finally:
            shutil.rmtree(root, ignore_errors=True)


# =====================================================================================================
def _defines(text, name):
    """Whether a module's source binds `name` at its top level (an assignment, annotated or not, or an
    import). A source that does not parse counts as binding it: it cannot stand for 'before P'."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return True
    for node in tree.body:
        targets = (node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign)
                   else [])
        if any(isinstance(t, ast.Name) and t.id == name for t in targets):
            return True
        if isinstance(node, ast.ImportFrom) and any((a.asname or a.name) == name for a in node.names):
            return True
    return False


def live_state(*, root):
    """Live's rule (mistake 19: a skip must not read as a pass): (current, why), current being
    four_engine_roads.current_reverify's (rel, record) or None. Live may skip only while ALL of these hold,
    and then why is None: no reverify*.json of results/EPA_ROADS was ever added in HEAD's history, none
    exists on disk, and HEAD's committed engine_env.py (its blob, never the work tree's) does not define
    REWARD_KNOCK_DEFAULT, P's name: before P is committed no record can exist, and P's uncommitted
    candidate tree keeps the skip until adopt writes the record. In every other case with no current
    record, why names the failure: added in HEAD's history but not current (modified, deleted, or naming
    another roads.json or redraws.json), on disk but not committed, or P committed without a record (the
    interface sheet, 10.1: skipped until the record is committed, a failure if skipped after)."""
    cur = FR.current_reverify(root=root)
    if cur is not None:
        return cur, None

    def ours(rel):
        folder, _, name = rel.rpartition("/")
        return folder == R.ROADS_DIR_REL and name.startswith("reverify") and name.endswith(".json")
    log = subprocess.run(["git", "log", "--full-history", "--diff-filter=A", "--name-only", "--format=", "HEAD", "--",
                          R.ROADS_DIR_REL + "/"], cwd=root, capture_output=True, text=True, encoding="utf-8")
    added = sorted({x.strip() for x in log.stdout.splitlines() if ours(x.strip())}) if log.returncode == 0 else []
    folder = os.path.join(root, *R.ROADS_DIR_REL.split("/"))
    on_disk = sorted(rel for rel in (f"{R.ROADS_DIR_REL}/{n}" for n in (os.listdir(folder) if os.path.isdir(folder)
                                                                       else [])) if ours(rel))
    env = subprocess.run(["git", "show", "HEAD:engine_env.py"], cwd=root, capture_output=True, text=True,
                         encoding="utf-8")
    p_committed = env.returncode == 0 and _defines(env.stdout, "REWARD_KNOCK_DEFAULT")
    if added:
        return None, (f"{added} were added in HEAD's history, and four_engine_roads.current_reverify finds none "
                      "current: modified, deleted, or naming another roads.json or redraws.json")
    if on_disk:
        return None, f"{on_disk} exist in the tree, and none is committed (row 140 (3): P commits the record)"
    if p_committed:
        return None, ("HEAD's engine_env.py defines REWARD_KNOCK_DEFAULT, so P is committed, and no re-verification "
                      "record was committed (row 140 (3): P carries it)")
    return None, None


class LiveRule(Guarded):
    """live_state, Live's skip rule, in a temporary repository holding a SYNTHETIC roads.json and a SYNTHETIC
    engine_env.py from before P: the one state that skips, and the three that fail, each with its control."""
    BEFORE_P = "# SYNTHETIC engine_env.py, before P\nGRADE_RAMP_S = 8.0\n"
    P = BEFORE_P + "REWARD_KNOCK_DEFAULT = True\n"

    def setUp(self):
        super().setUp()
        self.root = tempfile.mkdtemp(prefix="reverify_live_")
        git(self.root, "init", "-q")
        self.put(R.ROADS_REL, json.dumps({"SYNTHETIC": "roads"}))
        self.put("engine_env.py", self.BEFORE_P)
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "before P")
        self.record = json.dumps({"roads_sha": R.roads_sha(os.path.join(self.root, *R.ROADS_REL.split("/"))),
                                  "redraws_sha": None})

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def put(self, rel, text, commit=None):
        p = os.path.join(self.root, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        if commit:
            git(self.root, "add", "--", rel)
            git(self.root, "commit", "-q", "-m", commit)

    def state(self):
        cur, why = live_state(root=self.root)
        return (None if cur is None else cur[0]), why

    def fails(self, text):
        rel, why = self.state()
        self.assertIsNone(rel)
        self.assertIsNotNone(why, f"skipped, and it should fail: {text}")
        self.assertIn(text, why)

    def test_before_p_it_skips(self):
        """The one skip: nothing added or on disk, and HEAD's engine_env.py from before P. P's uncommitted
        candidate tree (the name defined in the work tree only, before adopt) skips too: the rule reads
        HEAD's blob."""
        self.assertEqual(self.state(), (None, None))
        self.put("engine_env.py", self.P)
        self.assertEqual(self.state(), (None, None))

    def test_a_record_on_disk_and_not_committed_fails(self):
        self.put(FR.REVERIFY_REL, self.record)
        self.fails("exist in the tree, and none is committed")               # untracked
        git(self.root, "add", "--", FR.REVERIFY_REL)
        self.fails("exist in the tree, and none is committed")               # staged, not at HEAD
        git(self.root, "commit", "-q", "-m", "the record")
        self.assertEqual(self.state(), (FR.REVERIFY_REL, None))              # the control: committed, current

    def test_a_committed_record_that_is_not_current_fails(self):
        self.put(FR.REVERIFY_REL, self.record, commit="the record")
        self.assertEqual(self.state(), (FR.REVERIFY_REL, None))              # the control
        self.put(FR.REVERIFY_REL, self.record + " ")
        self.fails("were added in HEAD's history")                           # modified in the work tree
        git(self.root, "checkout", "--", FR.REVERIFY_REL)
        self.assertEqual(self.state(), (FR.REVERIFY_REL, None))              # restored: the control again
        git(self.root, "rm", "-q", "--", FR.REVERIFY_REL)
        git(self.root, "commit", "-q", "-m", "deleted")
        self.fails("were added in HEAD's history")                           # deleted: in HEAD's history only
        self.put(f"{R.ROADS_DIR_REL}/reverify_2.json", json.dumps({"roads_sha": "0" * 64, "redraws_sha": None}),
                 commit="another")
        self.fails("were added in HEAD's history")                           # naming another roads.json

    def test_p_committed_without_a_record_fails(self):
        self.put("engine_env.py", self.P, commit="P")
        self.fails("defines REWARD_KNOCK_DEFAULT")
        self.put(FR.REVERIFY_REL, self.record, commit="P's record")
        self.assertEqual(self.state(), (FR.REVERIFY_REL, None))              # the control: P carries its record

    def test_defines(self):
        for src, want in (("REWARD_KNOCK_DEFAULT = True\n", True), ("REWARD_KNOCK_DEFAULT: bool = True\n", True),
                          ("from x import REWARD_KNOCK_DEFAULT\n", True), ("def f(:\n", True),
                          ("# REWARD_KNOCK_DEFAULT = True\n", False), ("X = 'REWARD_KNOCK_DEFAULT'\n", False),
                          ("def f():\n    REWARD_KNOCK_DEFAULT = True\n", False)):
            self.assertEqual(_defines(src, "REWARD_KNOCK_DEFAULT"), want, src)


class Live(Guarded):
    """From P on (row 140 (3)): the current re-verification record names roads.json and redraws.json as they
    are, is EQUAL and complete, ran on an ancestor of HEAD, keeps every engine_sha, and every file it names
    (each tree_changes sha_text and every hashed_files.sha_text_now) is its blob at the commit that added the
    record (reference_commit), never HEAD's or the work tree's, so G's and V's edits leave it passing. It
    skips only as live_state allows (LiveRule), and fails, naming why, in every other case without one."""

    def test_the_current_record(self):
        cur, why = live_state(root=HERE)
        if cur is None and why is None:
            self.skipTest("before P: no reverify*.json was ever committed or exists, and HEAD's engine_env.py does "
                          "not define REWARD_KNOCK_DEFAULT (roads_reverify.py adopt writes the record and P commits "
                          "it, row 140 (3))")
        self.assertIsNotNone(cur, why)
        rel, rec = cur
        import epa_freeze as EF
        roads = R.load_record(os.path.join(HERE, *R.ROADS_REL.split("/")))
        self.assertEqual((rec["schema"], rec["verdict"], rec["partial"]), (RV.SCHEMA, "EQUAL", False))
        self.assertEqual(rec["roads_sha"], R.roads_sha(os.path.join(HERE, *R.ROADS_REL.split("/"))))
        self.assertEqual(rec["redraws_sha"], sha_or_none(R.REDRAWS_REL))
        self.assertTrue(EF.is_ancestor(rec["head"], "HEAD", root=HERE))
        self.assertNotIn("commit_reveal", rec)
        self.assertEqual(rec["plants"]["b58"]["plant_sha_at_draw"], R.B58_PLANT_SHA)
        for e, p in rec["plants"].items():
            self.assertEqual(p["engine_sha_now"], roads["hashes"]["plants"][e]["engine_sha"], e)
        ref = RV.reference_commit(rel, root=HERE)
        named = dict(rec["hashed_files"]["sha_text_now"])
        named.update({c["path"]: c["sha_text"] for c in rec["tree_changes"]})
        for f, sha in sorted(named.items()):
            self.assertEqual(RV.blob_sha_text(ref, f, root=HERE), sha, f)


# =====================================================================================================
class FullShape(Guarded):
    """MANDATORY (the interface sheet, section 14; resolution 6 (a)): the draw's REAL path on one SYNTHETIC
    road, as `epa_roads.py smoke --full` runs it: the four engines, every variant and both readings at both
    ratios, roads_ceiling.report's companions and the Honda's decision-40 diagnostic, re-verified EQUAL with
    every cache cleared first, report included but for its provenance and wall_s."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.enterClassContext(contract_stand_ins())
        cls.record, _ = synthetic_draw("full")
        cls.lines = []
        given = copy.deepcopy(cls.record)
        del given["commit_reveal"]
        with caches(), no_roads_seed(SYNTHETIC_SEED):
            cls.result = RV.reverify(root=HERE, jobs=JOBS, mode="check", out_dir=tempfile.mkdtemp(prefix="reverify_full_"),
                                     log=cls.lines.append, record=given)

    def test_the_full_shape_reverifies_equal(self):
        res = self.result
        self.assertEqual(res["refused"], [])
        self.assertEqual((res["verdict"], res["not_run"], res["stopped_at"]), ("EQUAL", [], None),
                         "\n".join(self.lines[-40:]))
        self.assertEqual(sum(s["differences"] for s in res["sections"].values()), 0)
        self.assertTrue(res["reconstruction"]["equal"])
        for name in RV.SECTIONS[1:]:
            self.assertGreater(res["sections"][name]["values"], 0, name)
        self.assertGreater(res["sections"]["report"]["values"], 100)
        self.assertGreater(res["sections"]["cvt_diagnostic"]["values"], 1)      # the Honda's, not a None
        self.assertLessEqual({"provenance", "wall_s"}, set(self.record["report"]))      # what is ignored exists


if __name__ == "__main__":
    unittest.main(verbosity=2)

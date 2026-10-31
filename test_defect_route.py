"""test_defect_route.py -- Run 2's defect route after the one plant commit, run in a synthetic repository
(section I of results/VALIDATION_DECISIONS.md, row 94; docs/build_step_2/ORDER_TO_TRAINING.md steps 4 and 13).

    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/Scripts/python.exe -B test_defect_route.py     exit code 0 when all pass

WHY IT EXISTS. Row 94: "Before the plant commit, a new test outside STEP2_TESTS runs the route in a synthetic
repository built from `test_validate_guards`' fixtures. If the route does not pass arm, the plant commit waits
until both of you record, in a version-6 row of its own, that Run 2's defect re-runs end with the plant commit."
The route, in row 94's words: a coding defect of Run 2 found after the plant commit "is fixed on a branch made
from the third commit F, in the armed work tree"; "on a later descendant, PLANT_CODE's code, and `epa_fit.py`
once commit G has landed, are first restored to freeze.json's, since plant_sha hashes code only"; then
`calibrate_epa.py check --defect`, `validate_epa.py arm --defect-rerun`, `run --defect-rerun`. The seventh
review's item 18 read validate_epa.py:814-815 and :1145-1147: arm --defect-rerun still runs _arm_plant, so after
a plant commit any re-run is refused. Row 94 called the route BUILT as far as the code can be read, and ASSUMED
because it had never run. This file runs it. It is not in epa_freeze.STEP2_TESTS, as row 94 asks.

THE SEQUENCE, in one synthetic repository per test (test_epa_fixtures.make_repo, made armable by
test_validate_guards.prepare, as every guard test of test_validate_guards is): the calibration frozen -> arm ->
commit E (ARMED.json alone) -> run -> commit F (the outputs and the invocation log) -> the plant commit, which
moves plant_sha (one module-level assignment appended to the COPY's engine_env.py; nothing in this tree is
edited) -> a defect fix, check --defect's records -> arm --defect-rerun, then run --defect-rerun, on three lines:

  PlantCommitLine    HEAD descends from the plant commit, the plant code as the plant commit left it (the
                     sequence item 18 reads). arm --defect-rerun is REFUSED: first at arm/tightenings (decision
                     71: the tightenings' provenance records the B58's plant_sha before the plant commit, and the
                     arming compares it with the B58 as the work tree builds it), and, that check set aside, at
                     arm/plant (plant_sha is not freeze.json's). With both set aside it arms: those two are what
                     refuse. run --defect-rerun is refused too, since ARMED.json was not re-made.
  BranchFromCommitF  row 94's route: a branch made from commit F, in the armed work tree, the plant commit outside
                     HEAD's history (it stays in `git log --all`). arm --defect-rerun PASSES, plant_sha is
                     freeze.json's, and run --defect-rerun runs, its labels capped at limited.
  RestoredDescendant row 94's other form: a later descendant of the plant commit, after a later commit to hashed
                     step-2 code that is no defect fix (as commit G's `epa_fit.py` and step 16's `evaluate.py`;
                     ORDER_TO_TRAINING.md). PLANT_CODE restored to commit F's alone is REFUSED at arm/code,
                     naming both files (C10: every change to epa_freeze.CODE_HASHED since the first fit needs its
                     defects.json entry); with those two restored as well it PASSES, and run --defect-rerun runs.

WHAT IT FOUND, in the words the run prints (tearDownModule): the route as row 94 writes it passes arm after the
plant commit, made on a branch from commit F or on a later descendant with every hashed file restored, so row
94's first branch applies; a re-run on the plant commit's own line is refused, as item 18 says. Should the
branch from commit F ever be refused, the line printed is instead "the route is refused after the plant commit:
row 94's version-6 row is needed before the plant commit". Each test asserts the behaviour the code has today
and records it before asserting, so a change in validate_epa.py that alters it fails this file, and the printed
verdict follows what was measured, not what was expected. A green exit means "the code still behaves as this
file records"; the row-94 verdict is the printed line.

WHAT STANDS IN FOR WHAT (and why the comparison is still a real one):
  * the plant: no EPA plant is calibrated in a synthetic repository, so engines.get and the frozen-plant dump are
    answered from complete.json (test_validate_guards.arm_patches). The plant_sha that _arm_plant compares, and
    the B58's plant_sha and engine_sha that _arm_tightenings compares (decision 71), are the COPY's own: its
    epa_freeze.plant_sha and engines, run in a subprocess inside the copy (copy_identity), since the ones in this
    process hash this tree, which the synthetic plant commit never touches. _arm_plant itself is validate_epa's
    own function (REAL_ARM_PLANT), called with engines.get, engines.engine_sha and epa_freeze.plant_sha answered.
  * freeze.json's plant_sha (and the provenance of poison, e6 and complete) and the tightenings' B58 provenance
    are the copy's own at the freeze (prepare runs under them), so the first arming's comparison matches
    (asserted) and the comparison after the plant commit is one between two hashes the copy's code computed.
  * the plant commit is a code line, not a comment: plant_sha hashes code only (fingerprint._sha_files), and the
    control in PlantCommitLine shows that a comment leaves it where it was (mistake 25: check the input reached it).
  * calibrate_epa.py is test_validate_guards' stub (exit 0): the real one is never run here. check --defect's two
    records (its defects.json entry and in_sample_rerun1.json) are written as stand-ins.
  * the held-out computation is test_validate_guards.FakeCompute.
  * one engine, the Ford (no D3 drive); its commit F stands for the third commit F, which descends from every
    arming.
  * no roads_seed is drawn or used: the tightenings carry test_epa_fixtures' synthetic placeholder, and nothing
    here writes results/EPA_ROADS/ or any attempts log.

THE GUARDS. Every class runs Guarded (test_epa_fixtures.forbid_real_data) like the step-2 tests, and inside
no_real_records: an open of this tree's results/**, data/** (but a read of the code files make_repo copies) or
logs/**, or a write anywhere in this tree, fails the test. The subprocess in the copy refuses any open in this
tree but its .venv. Every git command runs in the synthetic copy; this tree's records are never read or written.
Guards shows that both can fail.
"""
import contextlib
import json
import os
import subprocess
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import engines  # noqa: E402
import epa_freeze  # noqa: E402
import fingerprint  # noqa: E402
import test_epa_fixtures as fx  # noqa: E402
import test_validate_guards as tvg  # noqa: E402
import validate_epa as V  # noqa: E402

FORD = tvg.FORD
# validate_epa's own plant step and test_validate_guards' own preparation, kept before any test patches them
# (test_validate_guards.arm_patches replaces V._arm_plant inside each test).
REAL_ARM_PLANT = V._arm_plant
REAL_PREPARE = tvg.prepare
if (REAL_ARM_PLANT.__module__, REAL_ARM_PLANT.__name__) != ("validate_epa", "_arm_plant"):
    raise RuntimeError("test_defect_route: REAL_ARM_PLANT is not validate_epa._arm_plant")

# The plant commit, appended to the copy's engine_env.py: a module-level assignment nothing reads (harmless), and
# code, so plant_sha moves; the control is the comment, which plant_sha's code-only hash does not see.
PLANT_COMMIT_LINE = "\nSYNTHETIC_PLANT_COMMIT_OF_TEST_DEFECT_ROUTE = True\n"
PLANT_COMMIT_COMMENT = "\n# test_defect_route: a comment, which plant_sha's code-only hash does not see\n"
# The later commit to hashed step-2 code that is no defect fix (commit G's epa_fit.py; step 16's evaluate.py).
LATER_HASHED = ("epa_fit.py", "evaluate.py")
REFUSED_BRANCH = "the route is refused after the plant commit: row 94's version-6 row is needed before the plant commit"
PASSES_BRANCH = ("the route passes arm after the plant commit when it is made on a branch from the third commit F, "
                 "or on a later descendant with every hashed file restored: row 94's first branch applies, and no "
                 "version-6 row is needed for the route as row 94 writes it")

# What each test measured, recorded before it asserts (tearDownModule prints the verdict from it).
ROUTE = {}


# ------------------------------------------------------------------------------------- this tree's records
_RECORDS = {"on": 0, "hits": []}
_INSTALLED = []
_HERE_N = os.path.normcase(os.path.abspath(HERE)) + os.sep
_RECORD_DIRS = tuple(_HERE_N + d + os.sep for d in ("results", "data", "logs"))
_CODE_COPIES = frozenset(os.path.normcase(os.path.join(HERE, *rel.split("/"))) for rel in fx.CODE_FILES)


def _writes(args):
    """Whether an "open" audit event's (path, mode, flags) opens for writing."""
    mode = args[1] if len(args) > 1 else None
    flags = args[2] if len(args) > 2 else 0
    if isinstance(mode, str):
        return any(c in mode for c in "wax+")
    return isinstance(flags, int) and bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC))


def _records_hook(event, args):
    if event != "open" or not _RECORDS["on"] or not args or not isinstance(args[0], (str, bytes, os.PathLike)):
        return
    p = os.path.normcase(os.path.abspath(os.fsdecode(args[0])))
    if not p.startswith(_HERE_N):
        return
    write = _writes(args)
    if write and (os.sep + "__pycache__" + os.sep) not in p:
        what = "a write"
    elif p.startswith(_RECORD_DIRS) and (write or p not in _CODE_COPIES):
        what = "an open of a record"
    else:
        return
    _RECORDS["hits"].append(p)
    raise PermissionError(f"no_real_records: {what} in the real repository ({os.path.relpath(p, HERE)})")


@contextlib.contextmanager
def no_real_records():
    """While inside, an open of this tree's results/**, data/** (but a read of a file make_repo copies,
    test_epa_fixtures.CODE_FILES) or logs/**, or any write in this tree outside __pycache__, raises
    PermissionError inside the open, and leaving the block fails naming each one, even one the code caught."""
    if not _INSTALLED:
        sys.addaudithook(_records_hook)
        _INSTALLED.append(True)
    _RECORDS["on"] += 1
    start = len(_RECORDS["hits"])
    try:
        yield
    finally:
        _RECORDS["on"] -= 1
        hits = _RECORDS["hits"][start:]
        del _RECORDS["hits"][start:]
    if hits:
        raise AssertionError("no_real_records: " + ", ".join(sorted({os.path.relpath(h, HERE) for h in hits})))


# ------------------------------------------------------------------------------------- the copy's own plant
_IDENTITY_CODE = r"""
import json, os, sys
root, name, real = sys.argv[1], sys.argv[2], sys.argv[3]
real_dir = os.path.normcase(os.path.abspath(real)) + os.sep
venv_dir = os.path.normcase(os.path.abspath(os.path.join(real, ".venv"))) + os.sep
def hook(event, args):
    if event != "open" or not args or not isinstance(args[0], (str, bytes, os.PathLike)):
        return
    p = os.path.normcase(os.path.abspath(os.fsdecode(args[0])))
    if p.startswith(real_dir) and not p.startswith(venv_dir):
        raise PermissionError("the synthetic copy's subprocess opened the real repository: " + p)
sys.addaudithook(hook)
sys.path.insert(0, root)
import engines, epa_freeze
b58 = engines.get("b58")
sys.stdout.write(json.dumps({"plant_sha": epa_freeze.plant_sha(name), "b58_plant_sha": epa_freeze.plant_sha("b58"),
                             "b58_engine_sha": engines.engine_sha(b58), "engines_file": os.path.abspath(engines.__file__),
                             "epa_freeze_file": os.path.abspath(epa_freeze.__file__)}))
"""


def copy_identity(root, name):
    """{"plant_sha" (of `name`), "b58_plant_sha", "b58_engine_sha"} as the synthetic copy at `root` computes them
    from its work tree as it is now: its own epa_freeze.plant_sha and engines, in `python -I -B` inside the copy
    (the way test_epa_fixtures.split_of runs the generator there). The modules are checked to be the copy's, not
    this tree's (mistake 19: a number that could have come from the fallback)."""
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    r = subprocess.run([sys.executable, "-I", "-B", "-c", _IDENTITY_CODE, root, name, HERE], capture_output=True,
                       cwd=root, env=env)
    if r.returncode != 0:
        raise RuntimeError("the copy's identity failed: " + r.stderr.decode(errors="replace")[-2000:])
    out = json.loads(r.stdout.decode("utf-8"))
    for key in ("engines_file", "epa_freeze_file"):
        if os.path.normcase(os.path.dirname(out[key])) != os.path.normcase(os.path.abspath(root)):
            raise RuntimeError(f"the copy's identity ran {out[key]}, not the copy's module")
    return {k: out[k] for k in ("plant_sha", "b58_plant_sha", "b58_engine_sha")}


def recorded_b58(root):
    """The B58's identity the tightenings' provenance records (decision 71), read from the copy's work tree."""
    prov = tvg.read_json(os.path.join(root, *V.TIGHTENINGS_REL.split("/")))["provenance"]
    return {"engine_sha": prov["engine_sha"], "plant_sha": prov["plant_sha"]}


@contextlib.contextmanager
def the_copys_plant(root, *, b58_as_recorded, plant_as_frozen):
    """While inside (one arming): validate_epa's B58 identity (_arm_tightenings, decision 71) and its plant step
    (_arm_plant, the real function) read the plant as the copy at `root` builds it now. b58_as_recorded sets
    decision 71's comparison aside (the B58 is what the tightenings record); plant_as_frozen sets _arm_plant's
    plant_sha comparison aside (the plant_sha is freeze.json's). Both are controls, False on the route itself."""
    ident = copy_identity(root, FORD)

    def b58():
        if b58_as_recorded:
            return recorded_b58(root)
        return {"engine_sha": ident["b58_engine_sha"], "plant_sha": ident["b58_plant_sha"]}

    def plant_step(ctx):
        psha = (ctx["freeze"].get("plant") or {}).get("plant_sha") if plant_as_frozen else ident["plant_sha"]
        stand_in = object()
        with mock.patch.object(engines, "get", lambda n: stand_in), \
                mock.patch.object(engines, "engine_sha", lambda p: ctx["complete"]["engine_sha"]), \
                mock.patch.object(epa_freeze, "plant_sha", lambda n: psha):
            return REAL_ARM_PLANT(ctx)

    with mock.patch.object(V, "b58_identity", b58), mock.patch.object(V, "_arm_plant", plant_step):
        yield ident


def _append(root, rel, text):
    with open(os.path.join(root, *rel.split("/")), "a", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def _head(root):
    return fx.git(root, "rev-parse", "HEAD")


def _all_commits(root):
    return set(fx.git(root, "rev-list", "--all").split())


def _say(line):
    print(f"\ntest_defect_route: {line}", flush=True)


# ------------------------------------------------------------------------------------- one process with the roads tests
# The final verifier, 31 October 2026: `python -m unittest test_epa_roads test_roads_ceiling test_defect_route` failed
# here with three setUpClass errors. epa_roads.install_guard (test_epa_roads installs it at import) and
# roads_ceiling.install_guard add process-wide audit hooks, which cannot be removed, that refuse any path holding
# data/engines/<id>/epa_* or ending in .csv wherever it lies, so make_repo's synthetic tables were refused in its
# temporary folder. In such a process this file runs once in a child interpreter, by its own command, and stands
# on the child's exit code; run alone, it runs here as before.
_CHILD = {}
_CHILD_ENV = "TEST_DEFECT_ROUTE_CHILD"


def _tables_refused_here():
    """Whether a hook already in this process refuses the synthetic repository's tables: one such file is written
    in a fresh temporary folder outside this tree (the hook refuses it before it is created)."""
    import tempfile
    with tempfile.TemporaryDirectory(prefix="defect_route_probe_") as tmp:
        folder = os.path.join(tmp, "data", "engines", "probe")
        os.makedirs(folder)
        try:
            open(os.path.join(folder, "epa_probe.csv"), "w").close()
        except PermissionError:
            return True
    return False


def setUpModule():
    """In a process whose hooks refuse the synthetic tables, the file runs in a child interpreter: every class here
    is then skipped when the child passed (its output, the verdict included, is printed above) and an error when
    it failed."""
    if not _tables_refused_here():
        return
    if os.environ.get(_CHILD_ENV):
        raise RuntimeError("test_defect_route: the child interpreter refuses the synthetic tables too")
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONIOENCODING="utf-8")
    env[_CHILD_ENV] = "1"
    r = subprocess.run([sys.executable, "-B", os.path.join(HERE, "test_defect_route.py")], cwd=HERE, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    _CHILD["code"] = r.returncode
    print("\ntest_defect_route: a hook in this process refuses the synthetic tables (a roads guard); the file ran "
          f"in a child interpreter, exit {r.returncode}:\n{r.stdout}{r.stderr}", flush=True)
    if r.returncode != 0:
        raise RuntimeError(f"test_defect_route in a child interpreter failed, exit {r.returncode} (its output above)")
    raise unittest.SkipTest("ran in a child interpreter, exit 0 (its output above)")


# ------------------------------------------------------------------------------------- the case
class DefectRoute(tvg.Armed):
    """One synthetic repository (test_validate_guards.Armed, the Ford alone), prepared on the copy's own plant:
    freeze.json's plant_sha and the tightenings' B58 provenance are the copy's at the freeze."""
    ENGINES = (FORD,)

    @classmethod
    def setUpClass(cls):
        cls.enterClassContext(no_real_records())

        def prepare_on_the_copys_plant(repo, engines_, data_folder, *, records):
            ident = copy_identity(repo.root, FORD)
            cls.frozen_identity = ident
            b58 = {"plant_sha": ident["b58_plant_sha"], "engine_sha": ident["b58_engine_sha"]}
            with mock.patch.dict(tvg.SYNTHETIC_SHA, {"plant": ident["plant_sha"]}), \
                    mock.patch.object(fx, "b58_identity", lambda: dict(b58)):
                return REAL_PREPARE(repo, engines_, data_folder, records=records)

        with mock.patch.object(tvg, "prepare", prepare_on_the_copys_plant):
            super().setUpClass()
        if os.path.normcase(os.path.abspath(cls._tmp.name)).startswith(_HERE_N):
            raise RuntimeError("the synthetic repository would sit inside this tree")

    def setUp(self):
        super().setUp()
        self.enterContext(no_real_records())

    def prefix(self):
        """A fresh copy taken through: the calibration frozen (prepare) -> arm -> commit E -> run -> commit F ->
        the plant commit. Returns its pieces; asserts that the first arming compared the copy's real plant_sha
        and that the plant commit moved it."""
        r, src = self.repo()
        frozen_psha = tvg.read_json(tvg.cal_path(r.root, FORD, "freeze.json"))["plant"]["plant_sha"]
        with the_copys_plant(r.root, b58_as_recorded=False, plant_as_frozen=False) as ident:
            rec = self.arm(src, engine=FORD, defect=None, data_folder=self.data)
        self.assertEqual(ident, self.frozen_identity)
        self.assertEqual(rec["plant_sha"], frozen_psha)
        self.assertEqual(frozen_psha, ident["plant_sha"])
        self.assertNotEqual(frozen_psha, tvg.SYNTHETIC_SHA["plant"])     # the copy's hash, not the placeholder
        e = tvg.commit_file(r.root, f"{V.val_dir(FORD)}/{V.ARMED}", "commit E: the arming")
        res, out = self.run_(src, tvg.FakeCompute(), engine=FORD, defect=None)
        self.assertEqual(res["outcome"], "ok", out)
        f = fx.commit_all(r.root, "commit F: the first run's outputs and the invocation log")
        _append(r.root, "engine_env.py", PLANT_COMMIT_LINE)
        p = fx.commit_all(r.root, "the plant commit (synthetic: one assignment in the copy's engine_env.py)")
        moved = copy_identity(r.root, FORD)
        self.assertNotEqual(moved["plant_sha"], ident["plant_sha"])
        self.assertNotEqual(moved["b58_plant_sha"], ident["b58_plant_sha"])
        self.assertEqual(moved["b58_engine_sha"], ident["b58_engine_sha"])  # the B58's values: identical
        return {"r": r, "src": src, "E": e, "F": f, "P": p, "frozen": ident, "moved": moved}

    def defect_fix(self, root, where):
        """A defect of Run 2 found after the plant commit: the fix committed (a line of the copy's epa_stats.py,
        as test_validate_guards' defect-route test makes it), then check --defect's two records as stand-ins
        (calibrate_epa.py is the stub here): its defects.json entry and in_sample_rerun1.json, committed."""
        _append(root, "epa_stats.py", f"\n# test_defect_route: the fix of a defect of Run 2 ({where})\n")
        fix = fx.commit_all(root, f"the fix of a defect of Run 2 ({where})")
        reason = f"a synthetic defect of Run 2, found after the plant commit ({where})"
        entry = dict(tvg.defect_entry(fix), found_by="calibrate_epa.py check --defect (amendment C11): a synthetic "
                     "stand-in", assertion=reason, previous_run="in_sample.json")
        self.assertEqual(epa_freeze.defect_entry_problems(entry), [])
        tvg.write_json(tvg.cal_path(root, FORD, "defects.json"), [entry])
        tvg.write_json(tvg.cal_path(root, FORD, "in_sample_rerun1.json"), {
            "schema": "epa-in-sample/1", "synthetic": "a stand-in of check --defect's output",
            "rerun": {"k": 1, "reason": reason, "fix_commit": fix, "replaces": "in_sample.json"}})
        fx.commit_all(root, "check --defect's records (synthetic stand-ins): defects.json, in_sample_rerun1.json")
        return V.Defect(reason=reason, fix_commit=fix)

    def rearm_and_rerun(self, p, d):
        """arm --defect-rerun on the copy's plant as it is, commit ARMED.json alone, run --defect-rerun. Returns
        (the re-arming's record, or the Refused, and the run's result or None)."""
        r, src = p["r"], p["src"]
        try:
            with the_copys_plant(r.root, b58_as_recorded=False, plant_as_frozen=False):
                rec = self.arm(src, engine=FORD, defect=d, data_folder=self.data)
        except V.Refused as exc:
            return exc, None
        tvg.commit_file(r.root, f"{V.val_dir(FORD)}/{V.ARMED}", "the re-arming")
        problems = V.refusals(FORD, source=src, defect=d)
        if problems:
            return rec, problems
        res, out = self.run_(src, tvg.FakeCompute(), engine=FORD, defect=d)
        return rec, res

    def assertTheReRunRan(self, p, rec, res):
        r = p["r"]
        self.assertEqual((rec["rearm"]["k"], rec["rearm"]["first_armed_commit"]), (1, p["E"]))
        self.assertEqual(rec["plant_sha"], p["frozen"]["plant_sha"])
        self.assertIsInstance(res, dict, res)
        self.assertEqual(res["outcome"], "ok")
        files = set(os.listdir(tvg.val_path(r.root, FORD, "")))
        self.assertTrue({"STARTED_rerun1", "rows_rerun1.json", "e6_rerun1.json", "run_rerun1.json"} <= files, files)
        first = tvg.read_json(tvg.val_path(r.root, FORD, V.ROWS))
        second = tvg.read_json(tvg.val_path(r.root, FORD, "rows_rerun1.json"))
        self.assertEqual(first["rows"]["E1a"]["label"], "validated")             # the first run's record is kept
        self.assertEqual(second["rows"]["E1a"]["label"], "limited")              # the second is limited at best
        self.assertEqual(second["defect_rerun"]["capped_at"], "limited")


class PlantCommitLine(DefectRoute):
    """Item 18's sequence: arm --defect-rerun with HEAD descending from the plant commit."""

    def test_on_the_plant_commits_line_arm_defect_rerun_is_refused(self):
        p = self.prefix()
        r, src = p["r"], p["src"]
        # the control of the plant commit's form: a comment in a plant file leaves plant_sha where it was
        _append(r.root, "engine_env.py", PLANT_COMMIT_COMMENT)
        self.assertEqual(copy_identity(r.root, FORD), p["moved"])
        fx.commit_all(r.root, "a comment in the copy's engine_env.py")
        d = self.defect_fix(r.root, "on the plant commit's line")
        self.assertTrue(epa_freeze.is_ancestor(p["P"], _head(r.root), root=r.root))
        try:
            with the_copys_plant(r.root, b58_as_recorded=False, plant_as_frozen=False):
                self.arm(src, engine=FORD, defect=d, data_folder=self.data)
            ROUTE["plant_line"] = ("passes", ())
        except V.Refused as exc:
            ROUTE["plant_line"] = ("refused", exc.problems)
        outcome, problems = ROUTE["plant_line"]
        self.assertEqual(outcome, "refused")
        self.assertTrue(problems and all(x.startswith("arm/tightenings: ") for x in problems), problems)
        self.assertTrue(any("provenance.plant_sha is not the B58's as this code builds it (decision 71)" in x
                            for x in problems), problems)
        # decision 71's comparison set aside: the plant step refuses next, on plant_sha
        with the_copys_plant(r.root, b58_as_recorded=True, plant_as_frozen=False):
            with self.assertRaises(V.Refused) as cm:
                self.arm(src, engine=FORD, defect=d, data_folder=self.data)
        self.assertEqual(cm.exception.problems, ("arm/plant: the plant's code and specs (plant_sha) are not "
                                                 "freeze.json's",))
        ROUTE["plant_line_next"] = cm.exception.problems
        # run --defect-rerun has no re-arming to run on
        self.assertRefused(src, "not re-made", engine=FORD, defect=d)
        # the control (mistake 12): with both comparisons set aside the re-arming passes, so the plant commit is
        # what refuses it, and every other step of arm passes on this line
        with the_copys_plant(r.root, b58_as_recorded=True, plant_as_frozen=True):
            rec = self.arm(src, engine=FORD, defect=d, data_folder=self.data)
        self.assertEqual(rec["rearm"]["k"], 1)
        _say("on the plant commit's line, arm --defect-rerun is REFUSED: " + "; ".join(problems)
             + "; with that set aside, " + "; ".join(cm.exception.problems)
             + "; with both set aside, it arms (the control)")


class BranchFromCommitF(DefectRoute):
    """Row 94's route: the fix on a branch made from commit F, in the armed work tree."""

    def test_on_a_branch_from_commit_F_arm_defect_rerun_passes_and_run_reruns(self):
        p = self.prefix()
        r = p["r"]
        fx.git(r.root, "checkout", "-q", "-b", "defect_route", p["F"])
        self.assertEqual(_head(r.root), p["F"])
        self.assertIn(p["P"], _all_commits(r.root))                       # the plant commit exists ...
        self.assertFalse(epa_freeze.is_ancestor(p["P"], "HEAD", root=r.root))   # ... outside HEAD's history
        self.assertEqual(copy_identity(r.root, FORD), p["frozen"])         # commit F carries freeze.json's plant
        d = self.defect_fix(r.root, "on a branch from commit F")
        rec, res = self.rearm_and_rerun(p, d)
        ROUTE["branch_from_F"] = ("refused", rec.problems) if isinstance(rec, V.Refused) else (
            "passes", res if isinstance(res, tuple) else ())
        self.assertNotIsInstance(rec, V.Refused, getattr(rec, "problems", None))
        self.assertTheReRunRan(p, rec, res)
        _say("on a branch made from commit F (the plant commit outside HEAD's history), arm --defect-rerun PASSES "
             "and run --defect-rerun runs, its labels capped at limited")


class RestoredDescendant(DefectRoute):
    """Row 94's other form: a later descendant of the plant commit, the hashed code restored first."""

    def test_a_later_descendant_passes_once_every_hashed_file_is_restored(self):
        p = self.prefix()
        r, src = p["r"], p["src"]
        for rel in LATER_HASHED:
            self.assertIn(rel, epa_freeze.CODE_HASHED)
            _append(r.root, rel, "\n# test_defect_route: a later commit that is no defect fix (as commits G and V)\n")
        fx.commit_all(r.root, "a later commit to hashed code (synthetic: as commit G's epa_fit.py, step 16's evaluate.py)")
        d = self.defect_fix(r.root, "on a later descendant of the plant commit")
        fx.git(r.root, "checkout", p["F"], "--", *fingerprint.PLANT_CODE)
        fx.commit_all(r.root, "PLANT_CODE restored to commit F's (freeze.json's)")
        self.assertEqual(copy_identity(r.root, FORD), p["frozen"])
        self.assertTrue(epa_freeze.is_ancestor(p["P"], "HEAD", root=r.root))
        try:
            with the_copys_plant(r.root, b58_as_recorded=False, plant_as_frozen=False):
                self.arm(src, engine=FORD, defect=d, data_folder=self.data)
            ROUTE["plant_code_restored_alone"] = ("passes", ())
        except V.Refused as exc:
            ROUTE["plant_code_restored_alone"] = ("refused", exc.problems)
        outcome, problems = ROUTE["plant_code_restored_alone"]
        self.assertEqual(outcome, "refused")
        self.assertEqual(sorted(problems), sorted(f"arm/code: {rel} changed since the first fit without its "
                                                  "defects.json entry (C10)" for rel in LATER_HASHED))
        fx.git(r.root, "checkout", p["F"], "--", *LATER_HASHED)
        fx.commit_all(r.root, "the later hashed code restored to commit F's")
        rec, res = self.rearm_and_rerun(p, d)
        ROUTE["restored"] = ("refused", rec.problems) if isinstance(rec, V.Refused) else (
            "passes", res if isinstance(res, tuple) else ())
        self.assertNotIsInstance(rec, V.Refused, getattr(rec, "problems", None))
        self.assertTheReRunRan(p, rec, res)
        _say("on a later descendant of the plant commit, arm --defect-rerun is REFUSED with PLANT_CODE restored "
             "alone (" + "; ".join(problems) + "), and PASSES with " + " and ".join(LATER_HASHED)
             + " restored as well; run --defect-rerun then runs")


class Guards(fx.Guarded):
    """The two guards on this tree can fail (mistake 12). Neither control opens a file of this tree: each hook
    refuses inside the open, before it happens."""

    def test_no_real_records_refuses_a_record_and_a_write(self):
        record = os.path.join(HERE, "results", "test_defect_route_control_never_written.json")
        scratch = os.path.join(HERE, "test_defect_route_control_never_written.tmp")
        refused = []
        for path, mode in ((record, "rb"), (scratch, "w")):
            with self.assertRaises(AssertionError):           # leaving the block fails, though the code caught it
                with no_real_records():
                    try:
                        open(path, mode).close()
                    except PermissionError:
                        refused.append(mode)
        self.assertEqual(refused, ["rb", "w"])
        self.assertFalse(os.path.exists(scratch))
        # the one read it allows, decided without opening the file: a code file make_repo copies
        with no_real_records():
            self.assertIsNone(_records_hook("open", (os.path.join(HERE, "data", "derived_params.json"), "rb", 0)))

    def test_the_copys_subprocess_refuses_this_tree(self):
        """copy_identity pointed at this tree stops at its first open here (the import of engines), so it can
        only ever have computed a synthetic copy's hashes."""
        with self.assertRaises(RuntimeError) as cm:
            copy_identity(HERE, FORD)
        self.assertIn("opened the real repository", str(cm.exception))


def tearDownModule():
    """The verdict, from what the tests measured (ROUTE), never from what was expected."""
    if _CHILD:
        return                     # the child interpreter printed its own verdict
    def word(key):
        got = ROUTE.get(key)
        return "not measured (its test did not reach it)" if got is None else got[0]
    lines = ["ROW 94, measured in a synthetic repository (test_defect_route.py):",
             f"  on the plant commit's line (item 18's sequence): arm --defect-rerun {word('plant_line')}",
             f"  on a branch from commit F (row 94's route): arm --defect-rerun {word('branch_from_F')}",
             f"  on a later descendant, PLANT_CODE restored alone: {word('plant_code_restored_alone')}; every hashed "
             f"file restored: {word('restored')}"]
    branch = ROUTE.get("branch_from_F")
    if branch is None:
        lines.append("  VERDICT: not reached; the test of row 94's route did not run to its arming")
    elif branch[0] == "refused":
        lines.append("  VERDICT: " + REFUSED_BRANCH)
    else:
        lines.append("  VERDICT: " + PASSES_BRANCH
                     + "; a re-run on the plant commit's own line, its plant code not restored, is refused")
    print("\n" + "\n".join(lines), flush=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)

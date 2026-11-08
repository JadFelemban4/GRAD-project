"""test_trainable.py -- the five entry points that train or score take the engines the committed records keep.

    python -B test_trainable.py     about 1 min (46 s on this laptop, 5 November 2026); exit code 0 when all pass

Decision 47 (results/VALIDATION_DECISIONS.md section H; build step 2 P5, 22
October 2026) and rows 107 (5) and 139 (the plant commit P): train.py,
train_all.py, run_phase_d.py, evaluate.py and benchmark_training.py take --engine
from engines.trainable(), which reads Run 2's committed
results/EPA_VALIDATION/summary.json and, once it is committed, the backend
record results/EPA_BACKEND.json, at every call and never at import:

  the tree holds                                trainable()
  no summary.json (until Run 2's commit F3)     ("b58",)
  a committed summary.json                      the B58 and every EPA engine whose
                                                governing drop is False (row 139 (1):
                                                the re-run of the highest k, else the
                                                engine's own entry)
  that, and a committed EPA_BACKEND.json        also without the backend's drops
  a record present but not committed at HEAD    refused (ValueError), every parser
  a defect re-run open, or its rows not listed  refused (ValueError), every parser
    in the committed summary.json
  no git work tree                              refused (ValueError), every parser

Row 107 (5) asks for "a refusal and its control for each entry point". Once
summary.json exists the real tree may refuse nothing, so each refusal and its
control (mistake 12) run on synthetic committed records, in temporary git work
trees outside the repository (records_repo); nothing here creates or changes
anything under the real results/EPA_VALIDATION/ or the real EPA_BACKEND.json.
Amendment B8: nothing on this laptop runs these entry points (training runs on
the training device), so each is run as far as its argument parser, where the
choice lives, and never further: every command ends at --help, at the parser's
refusal, or at trainable()'s ValueError, and nothing trains (run_cases refuses a
command that does not end with --help). The commands of one entry point share
one child process, each a fresh runpy of the script as __main__ with its parser
built anew and trainable() read anew, so the imports are paid once per script.

  Help          each entry point's --help exits 0 and names --engine
  B58           "--engine b58 --help" passes on the real tree, on a root with no
                records and on one whose summary drops all three (MD:1590)
  RecordsAbsent no summary.json: each EPA plant refused; the control, trainable()
                made known(), lets it through
  SummaryDrop   the summary drops mazda_25t: refused, the other two through; the
                control, the same summary keeping it, lets it through
  BackendDrop   the backend record drops ford_27tt: refused, the other two
                through; the control, the record keeping it, lets it through
  RerunOpen     a STARTED_rerun1 without its rows_rerun1.json refuses every entry
                point; the control, with both and the summary's entry, reads
  RerunGoverns  the re-run's drop governs the first entry's, both ways
  StaleSummary  a rows_rerun1.json the committed summary does not list refuses
                every entry point, committed or in the work tree alone; the
                controls, listed or absent, read
  RerunNames    the two re-run names are validate_epa.rerun_name's
  RealTree      on the real tree each engine passes iff it is in the expectation
                this test computes itself from the committed records
  Reader        engines.trainable_in in process: the states, no cache, records
                not committed, malformed records, no git work tree
  NotAtImport   importing engines and the five opens no record and runs no git
                on the records' tree; the control, trainable_in called, does
  OneDefinition the record names and the drop reading agree with validate_epa's
                and epa_roads' (mistake 10)
  Openable      every engine the records may keep fingerprints under schema 4
                (the Honda's CVT among them), and each stepped one records a step
                (step_record); the CVT's step is refused, since C2 is not built
                (row 146 (3)), and the real tree's records keep no CVT
  Source        each --engine of the five is engines.trainable(), by AST, and
                fingerprint.py's engines.known() (amendment B7)
  FingerprintCli  fingerprint.py, which keeps known(), refuses an uncalibrated
                plant by name, with the command that calibrates it, and no
                traceback (amendment B7); the control: with calibrated() made to
                say yes it dies in derived.py instead

FingerprintCliRegistered is retired with the plant commit: since commit D the
three EPA plants have both their derived file and their freeze record, so its
two tests skipped every subtest, and the fingerprint check of the calibrated
plants is test_epa_plants' (its decision-91 flip). Its helpers went with it, and
with them the duplicate of test_engine_threading.uncalibrated_or_skip that
docs/build_step_2/HANDOFFS.md (review of P7, item 8) named.
"""
import ast
import json
import os
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import derived  # noqa: E402
import engines  # noqa: E402

ENTRY_POINTS = ("train.py", "train_all.py", "run_phase_d.py", "evaluate.py", "benchmark_training.py")
EPA_PLANTS = ("mazda_25t", "honda_l15b7", "ford_27tt")        # thresholds.common.EPA_ENGINES, by OneDefinition
ENV = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
MARK = "TEST_TRAINABLE_RESULTS "

# The child: for each (argv, root, control), point engines.RECORDS_ROOT at `root` (the
# real tree when None), make trainable() known() when `control` (the control of mistake
# 12), and run the script as __main__ until it exits; its exit code and its output are
# kept per command. A command that returns without exiting is reported as None.
CHILD = """
import contextlib, io, json, runpy, sys, traceback
sys.path.insert(0, {here!r})
import engines
real = engines.trainable
out = []
for argv, root, control in {cases!r}:
    engines.RECORDS_ROOT = engines.HERE if root is None else root
    engines.trainable = (lambda: tuple(engines.known())) if control else real
    sys.argv = [{script!r}] + list(argv)
    buf, rc = io.StringIO(), None
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            runpy.run_path({path!r}, run_name="__main__")
        except SystemExit as exc:
            rc = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
            if isinstance(exc.code, str):
                print(exc.code)
        except Exception:
            traceback.print_exc()
            rc = 1
    out.append([rc, buf.getvalue()])
engines.trainable, engines.RECORDS_ROOT = real, engines.HERE
sys.__stdout__.write({mark!r} + json.dumps(out) + "\\n")
"""


def run_cases(script, cases):
    """[(exit code, output)] for each (argv, root, control) of `cases`, run by the
    entry point `script` in one child process in this tree. Every argv ends with
    --help (amendment B8: nothing trains)."""
    cases = [(list(argv), root, bool(control)) for argv, root, control in cases]
    for argv, _, _ in cases:
        if argv[-1:] != ["--help"]:
            raise ValueError(f"run_cases: {argv} does not end with --help, and nothing here may train (amendment B8)")
    code = CHILD.format(here=HERE, cases=cases, script=script, path=os.path.join(HERE, script), mark=MARK)
    p = subprocess.run([sys.executable, "-B", "-c", code], cwd=HERE, capture_output=True, text=True, timeout=1200,
                       env=ENV)
    lines = [ln for ln in p.stdout.splitlines() if ln.startswith(MARK)]
    if p.returncode != 0 or len(lines) != 1:
        raise RuntimeError(f"the child of {script} stopped (exit {p.returncode}): {(p.stdout + p.stderr)[-3000:]}")
    return [tuple(r) for r in json.loads(lines[0][len(MARK):])]


def run(script, argv, *, root=None, control=False):
    """One command of run_cases: (exit code, output)."""
    return run_cases(script, [(argv, root, control)])[0]


# ------------------------------------------------------------------ synthetic records
def git(root, *args):
    """A git command in the synthetic work tree `root`, refused on a non-zero exit."""
    p = subprocess.run(["git", "-c", "user.name=test_trainable", "-c", "user.email=test@trainable.invalid", *args],
                       cwd=root, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} in {root}: exit {p.returncode}: {p.stderr.strip()}")
    return p.stdout


_TMP = None


def scratch():
    """A new empty folder under this run's temporary folder, outside the repository."""
    global _TMP
    if _TMP is None:
        _TMP = tempfile.TemporaryDirectory(prefix="test_trainable_", ignore_cleanup_errors=True)
    return tempfile.mkdtemp(dir=_TMP.name)


def tearDownModule():
    global _TMP
    if _TMP is not None:
        _TMP.cleanup()
        _TMP = None


def summary_of(drops, reruns=None):
    """A summary.json as validate_epa.summary writes it, in what the reader reads: the
    schema, and per EPA engine its drop and its "reruns" map ({file: {"drop": bool}})."""
    reruns = reruns or {}
    return {"schema": engines.VALIDATION_SUMMARY_SCHEMA, "drop_order": "synthetic, by test_trainable.py",
            "engines": {e: {"drop": drops.get(e, False), "labels": {},
                            "reruns": {f: {"drop": d, "labels": {}} for f, d in reruns.get(e, {}).items()}}
                        for e in EPA_PLANTS},
            "inputs": {}}


def backend_of(drops):
    """A backend record in the interface sheet's 12.5 layout, as far as the reader reads it."""
    return {"schema": engines.BACKEND_SCHEMA, "engines": {
        e: {"drop": drops.get(e, False), "backend": None if drops.get(e, False) else "cycle",
            "reason": "synthetic, by test_trainable.py" if drops.get(e, False) else None}
        for e in engines.known()}}


STATES = ("committed", "untracked", "staged", "modified", "deleted")


def records_repo(summary=None, backend=None, *, state="committed", validation_files=()):
    """A temporary git work tree outside the repository holding only the records under
    test: `summary` at VALIDATION_SUMMARY_REL and `backend` at BACKEND_REL (each written
    when not None), in `state` (one of STATES; a dict {"summary": ..., "backend": ...}
    for one each, "committed" by default), and `validation_files`, each a name under
    VALIDATION_DIR_REL (committed) or a (name, state) pair. A first commit holding a
    placeholder gives the tree its HEAD. Returns the root."""
    root = scratch()
    git(root, "init", "-q")
    git(root, "config", "core.autocrlf", "false")
    with open(os.path.join(root, "README"), "w", encoding="utf-8") as fh:
        fh.write("synthetic records, by test_trainable.py\n")
    git(root, "add", "README")
    git(root, "commit", "-q", "-m", "placeholder")
    states = state if isinstance(state, dict) else {"summary": state, "backend": state}
    files = []
    for key, rel, obj in (("summary", engines.VALIDATION_SUMMARY_REL, summary), ("backend", engines.BACKEND_REL, backend)):
        if obj is not None:
            files.append((rel, json.dumps(obj, indent=1) + "\n", states.get(key, "committed")))
    for v in validation_files:
        name, st = (v, "committed") if isinstance(v, str) else v
        files.append((f"{engines.VALIDATION_DIR_REL}/{name}", "{}\n", st))
    for _, _, st in files:
        if st not in STATES:
            raise ValueError(f"records_repo: state {st!r} is not one of {STATES}")
    for rel, text, _ in files:
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    staged = [rel for rel, _, st in files if st != "untracked"]
    if staged:
        git(root, "add", "--", *staged)
    committed = [rel for rel, _, st in files if st in ("committed", "modified", "deleted")]
    if committed:
        git(root, "commit", "-q", "-m", "records", "--", *committed)
    for rel, text, st in files:
        if st == "modified":
            with open(os.path.join(root, rel), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text.replace("{", "{ ", 1))
        elif st == "deleted":
            os.remove(os.path.join(root, rel))
    return root


# ------------------------------------------------------------------ the entry points' commands
def _roots():
    """The synthetic roots the subprocess classes read, by name."""
    rerun1 = engines.RERUN_ROWS.format(k=1)
    return {
        "empty": records_repo(),
        "all_dropped": records_repo(summary_of({e: True for e in EPA_PLANTS})),
        "summary_drop": records_repo(summary_of({"mazda_25t": True})),
        "summary_keep": records_repo(summary_of({})),
        "backend_drop": records_repo(summary_of({}), backend_of({"ford_27tt": True})),
        "backend_keep": records_repo(summary_of({}), backend_of({})),
        "rerun_open": records_repo(summary_of({}), validation_files=(f"mazda_25t/{engines.RERUN_STARTED.format(k=1)}",)),
        "rerun_closed": records_repo(summary_of({}, {"mazda_25t": {rerun1: False}}),
                                     validation_files=(f"mazda_25t/{engines.RERUN_STARTED.format(k=1)}",
                                                       f"mazda_25t/{rerun1}")),
        "rerun_keeps": records_repo(summary_of({"mazda_25t": True}, {"mazda_25t": {rerun1: False}}),
                                    validation_files=(f"mazda_25t/{rerun1}",)),
        "rerun_drops": records_repo(summary_of({}, {"mazda_25t": {rerun1: True}}),
                                    validation_files=(f"mazda_25t/{rerun1}",)),
        "stale": records_repo(summary_of({}), validation_files=(f"mazda_25t/{rerun1}",)),
        "stale_worktree": records_repo(summary_of({}), validation_files=((f"mazda_25t/{rerun1}", "untracked"),)),
    }


def _commands(roots):
    """{key: (argv, root, control)}: every command the subprocess classes read."""
    def eng(n):
        return ["--engine", n, "--help"]
    cmds = {"help": (["--help"], None, False)}
    for n in engines.known():
        cmds[("real", n)] = (eng(n), None, False)
    for r in ("empty", "all_dropped", "rerun_open", "rerun_closed", "stale", "stale_worktree", "summary_keep"):
        cmds[(r, "b58")] = (eng("b58"), roots[r], False)
    for n in EPA_PLANTS:
        cmds[("empty", n)] = (eng(n), roots["empty"], False)
        cmds[("empty_control", n)] = (eng(n), roots["empty"], True)
        cmds[("summary_drop", n)] = (eng(n), roots["summary_drop"], False)
        cmds[("backend_drop", n)] = (eng(n), roots["backend_drop"], False)
    for r, n in (("summary_keep", "mazda_25t"), ("backend_keep", "ford_27tt"), ("rerun_closed", "mazda_25t"),
                 ("rerun_keeps", "mazda_25t"), ("rerun_drops", "mazda_25t"), ("stale", "mazda_25t"),
                 ("summary_keep", "honda_l15b7")):
        cmds[(r, n)] = (eng(n), roots[r], False)
    return cmds


_RESULTS = None


def results():
    """{(script, key): (exit code, output)} for every entry point and command, run once."""
    global _RESULTS
    if _RESULTS is None:
        cmds = _commands(_roots())
        keys = list(cmds)
        with ThreadPoolExecutor(max_workers=len(ENTRY_POINTS)) as pool:
            out = dict(zip(ENTRY_POINTS, pool.map(lambda s: run_cases(s, [cmds[k] for k in keys]), ENTRY_POINTS)))
        _RESULTS = {(s, k): r for s in ENTRY_POINTS for k, r in zip(keys, out[s])}
    return _RESULTS


class EntryCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = results()

    def passes(self, key):
        for s in ENTRY_POINTS:
            with self.subTest(script=s, case=key):
                rc, out = self.result[(s, key)]
                self.assertEqual(rc, 0, out[-2000:])
                self.assertIn("--engine", out)

    def refused(self, key, name):
        for s in ENTRY_POINTS:
            with self.subTest(script=s, case=key):
                rc, out = self.result[(s, key)]
                self.assertEqual(rc, 2, out[-2000:])
                self.assertIn(f"invalid choice: '{name}'", out)

    def stopped(self, key, *texts):
        """trainable() raised: exit 1 at the parser, the reader's ValueError naming each of `texts`."""
        for s in ENTRY_POINTS:
            with self.subTest(script=s, case=key):
                rc, out = self.result[(s, key)]
                self.assertEqual(rc, 1, out[-2000:])
                self.assertIn("ValueError: engines.trainable:", out)
                for t in texts:
                    self.assertIn(t, out)


class Help(EntryCase):
    def test_help_exits_0(self):
        self.passes("help")


class B58(EntryCase):
    def test_the_b58_passes_on_every_root(self):
        """The real tree, a root with no records, and a root whose summary drops all three EPA engines:
        the B58 is never dropped (results/ENGINE_THRESHOLDS.md:1590)."""
        for key in (("real", "b58"), ("empty", "b58"), ("all_dropped", "b58")):
            self.passes(key)


class RecordsAbsent(EntryCase):
    def test_each_epa_plant_is_refused_and_the_control_passes(self):
        """No summary.json: each EPA plant exits 2 by trainable(); the control (mistake 12): with trainable()
        made known() the same command passes, so the refusal is trainable()'s, not a missing name."""
        for n in EPA_PLANTS:
            self.refused(("empty", n), n)
            self.passes(("empty_control", n))


class SummaryDrop(EntryCase):
    def test_a_dropped_engine_is_refused_and_its_control_passes(self):
        """A committed summary dropping mazda_25t (B8's literal case, AMENDMENTS.md:118): refused, the Honda and
        the Ford through; the control, the same summary keeping it, lets it through."""
        self.refused(("summary_drop", "mazda_25t"), "mazda_25t")
        self.passes(("summary_drop", "honda_l15b7"))
        self.passes(("summary_drop", "ford_27tt"))
        self.passes(("summary_keep", "mazda_25t"))


class BackendDrop(EntryCase):
    def test_a_backend_drop_is_refused_and_its_control_passes(self):
        """The summary drops none, and a committed backend record drops ford_27tt: refused, the other two
        through, so a later drop needs no second plant commit (row 107 (5)); the control, the record keeping
        it, lets it through."""
        self.refused(("backend_drop", "ford_27tt"), "ford_27tt")
        self.passes(("backend_drop", "mazda_25t"))
        self.passes(("backend_drop", "honda_l15b7"))
        self.passes(("backend_keep", "ford_27tt"))


class RerunOpen(EntryCase):
    def test_an_open_rerun_refuses_every_entry_point_and_its_control_reads(self):
        """Row 139 (1), row 94's "No training starts while such a re-run is open": a STARTED_rerun1 without
        its rows_rerun1.json stops every parser, the B58's command too, naming the engine and the file. The
        control: with both files and the summary's entry for the re-run, it reads."""
        self.stopped(("rerun_open", "b58"), "mazda_25t: results/EPA_VALIDATION/mazda_25t/STARTED_rerun1 without "
                     "rows_rerun1.json", "row 94", "row 139 (1)")
        self.passes(("rerun_closed", "b58"))
        self.passes(("rerun_closed", "mazda_25t"))


class RerunGoverns(EntryCase):
    def test_the_reruns_drop_governs(self):
        """Row 139 (1): the first entry drops mazda_25t and the re-run keeps it: kept. The control: the
        re-run drops it and the first keeps it: dropped."""
        self.passes(("rerun_keeps", "mazda_25t"))
        self.refused(("rerun_drops", "mazda_25t"), "mazda_25t")


class StaleSummary(EntryCase):
    def test_a_rerun_the_summary_does_not_list_refuses_every_entry_point(self):
        """Row 139 (1): a committed rows_rerun1.json for mazda_25t beside a committed summary.json whose reruns
        map does not list it stops every parser, naming the file, the row and `validate_epa.py summary`; so
        does one present only in the work tree. The controls: the map listing rows_rerun1.json reads, and so
        does a summary.json with no re-run file beside it."""
        for key in (("stale", "b58"), ("stale_worktree", "b58")):
            self.stopped(key, "results/EPA_VALIDATION/mazda_25t/rows_rerun1.json", "row 139 (1)",
                         "run `validate_epa.py summary` and commit summary.json")
        self.passes(("rerun_closed", "b58"))
        self.passes(("summary_keep", "b58"))
        self.passes(("summary_keep", "honda_l15b7"))


class RerunNames(unittest.TestCase):
    def test_the_rerun_names_are_validate_epas(self):
        import validate_epa
        for k in (1, 2, 3):
            with self.subTest(k=k):
                self.assertEqual(engines.RERUN_STARTED.format(k=k), validate_epa.rerun_name(validate_epa.STARTED, k))
                self.assertEqual(engines.RERUN_ROWS.format(k=k), validate_epa.rerun_name(validate_epa.ROWS, k))
        self.assertEqual(engines.VALIDATION_DIR_REL, validate_epa.VAL_REL)


# ------------------------------------------------------------------ the real tree
def expected_on(root):
    """This test's own reading of the records in the git work tree `root`, from plain json, `git
    ls-files` and `git status`, not engines' reader: the tuple trainable() must give, or the string
    "refused" when a record is present but not committed or a re-run is open or unlisted."""
    def state(rel):
        tracked = bool(git(root, "ls-files", "--", rel).strip())
        if not tracked:
            return "refused" if os.path.exists(os.path.join(root, rel)) else None
        return "refused" if git(root, "status", "--porcelain", "--", rel).strip() else "committed"

    def load(rel):
        with open(os.path.join(root, rel), encoding="utf-8") as fh:
            return json.load(fh)
    s_state, b_state = state(engines.VALIDATION_SUMMARY_REL), state(engines.BACKEND_REL)
    reruns = {e: [] for e in EPA_PLANTS}
    for e in EPA_PLANTS:
        k = 1
        while True:
            st = state(f"results/EPA_VALIDATION/{e}/STARTED_rerun{k}")          # None when absent
            rows = state(f"results/EPA_VALIDATION/{e}/rows_rerun{k}.json")
            if st is None and rows is None:
                break
            if rows is None:
                return "refused"
            reruns[e].append(f"rows_rerun{k}.json")
            k += 1
    if "refused" in (s_state, b_state):
        return "refused"
    if s_state is None:
        return "refused" if b_state is not None or any(reruns.values()) else ("b58",)
    summary = load(engines.VALIDATION_SUMMARY_REL)
    kept = set()
    for e in EPA_PLANTS:
        entry = summary["engines"][e]
        if any(f not in entry["reruns"] for f in reruns[e]):
            return "refused"
        last = max(entry["reruns"], key=lambda f: int(f[len("rows_rerun"):-len(".json")]), default=None)
        if not (entry["reruns"][last] if last else entry)["drop"]:
            kept.add(e)
    if b_state is not None:
        kept -= {e for e, v in load(engines.BACKEND_REL)["engines"].items() if v["drop"]}
    return tuple(n for n in sorted(["b58"] + list(EPA_PLANTS)) if n == "b58" or n in kept)


class RealTree(EntryCase):
    def test_the_real_records_decide(self):
        """On the real tree each entry point passes "--engine <n> --help" exactly for the engines this test's
        own reading of the committed records keeps: since Run 2's summary.json (F4, 9140941), which drops
        all three EPA engines, the Mazda's by its re-run's governing entry (section Q), that is ("b58",).
        The expectation is printed, for P's commit message."""
        want = expected_on(HERE)
        print(f"\nRealTree: the expectation {want!r}; engines.trainable() {engines.trainable()!r}", file=sys.stderr)
        self.assertNotEqual(want, "refused", "the real tree holds a record the reader must refuse")
        self.assertEqual(engines.trainable(), want)
        for n in engines.known():
            if n in want:
                self.passes(("real", n))
            else:
                self.refused(("real", n), n)


# ------------------------------------------------------------------ the reader, in process
class Reader(unittest.TestCase):
    def test_the_states(self):
        """Absent: ("b58",). A committed summary: the B58 and the undropped, a tuple in known() order, the
        B58 first. With a committed backend record: also without its drops. All three dropped: ("b58",).
        No cache: a changed summary committed in the same tree answers differently on the next call."""
        self.assertEqual(engines.trainable_in(records_repo()), ("b58",))
        root = records_repo(summary_of({"mazda_25t": True}))
        got = engines.trainable_in(root)
        self.assertEqual(got, ("b58", "ford_27tt", "honda_l15b7"))
        self.assertIs(type(got), tuple)
        self.assertEqual(list(got), [n for n in engines.known() if n in got])
        self.assertEqual(engines.trainable_in(records_repo(summary_of({}), backend_of({"ford_27tt": True}))),
                         ("b58", "honda_l15b7", "mazda_25t"))
        self.assertEqual(engines.trainable_in(records_repo(summary_of({e: True for e in EPA_PLANTS}))), ("b58",))
        with open(os.path.join(root, engines.VALIDATION_SUMMARY_REL), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(summary_of({}), indent=1) + "\n")
        git(root, "commit", "-q", "-m", "keep the Mazda", "--", engines.VALIDATION_SUMMARY_REL)
        self.assertEqual(engines.trainable_in(root), tuple(engines.known()))

    def test_a_record_that_is_not_committed_is_refused(self):
        """Untracked, staged, modified by one byte, deleted from the work tree: each refused, naming the file
        and "not committed", for summary.json and for the backend record, never taken for absent (mistake
        19). The control: the committed file is read, and so is a CRLF checkout of an LF blob."""
        for which, rel in (("summary", engines.VALIDATION_SUMMARY_REL), ("backend", engines.BACKEND_REL)):
            for st in STATES[1:]:
                with self.subTest(record=which, state=st):
                    root = records_repo(summary_of({}), backend_of({}), state={which: st})
                    with self.assertRaises(ValueError) as cm:
                        engines.trainable_in(root)
                    self.assertIn(f"{rel} is not committed at HEAD", str(cm.exception))
                    self.assertIn("rows 107 (5), 139", str(cm.exception))
        self.assertEqual(engines.trainable_in(records_repo(summary_of({}), backend_of({}))), tuple(engines.known()))
        root = records_repo(summary_of({"ford_27tt": True}))
        git(root, "config", "core.autocrlf", "true")
        path = os.path.join(root, engines.VALIDATION_SUMMARY_REL)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        with open(path, "w", encoding="utf-8", newline="\r\n") as fh:
            fh.write(text)
        with open(path, "rb") as fh:
            self.assertIn(b"\r\n", fh.read())
        self.assertEqual(engines.trainable_in(root), ("b58", "honda_l15b7", "mazda_25t"))

    def test_a_malformed_record_is_refused(self):
        """ValueError naming the field for each malformed record, never a fallback to ("b58",); each case
        is paired with the valid record it was made from, which passes (mistake 12)."""
        good_s, good_b = summary_of({"honda_l15b7": True}), backend_of({"honda_l15b7": True})
        self.assertEqual(engines.trainable_from(good_s, good_b), ("b58", "ford_27tt", "mazda_25t"))

        def s(edit):
            d = json.loads(json.dumps(good_s))
            edit(d)
            return d

        def b(edit):
            d = json.loads(json.dumps(good_b))
            edit(d)
            return d
        cases = [
            ("schema", s(lambda d: d.update(schema="epa-summary/0")), None, "schema is 'epa-summary/0'"),
            ("no Ford", s(lambda d: d["engines"].pop("ford_27tt")), None, "engines is"),
            ("the B58 in summary.json", s(lambda d: d["engines"].update(b58={"drop": False, "reruns": {}})), None,
             "engines is"),
            *[(f"drop {v!r}", s(lambda d, v=v: d["engines"]["mazda_25t"].update(drop=v)), None,
               "engines.mazda_25t.drop is") for v in (0, "false", None)],
            ("reruns a list", s(lambda d: d["engines"]["mazda_25t"].update(reruns=[])), None,
             "engines.mazda_25t.reruns is"),
            *[(f"reruns key {k!r}", s(lambda d, k=k: d["engines"]["mazda_25t"]["reruns"].update({k: {"drop": False}})),
               None, "reruns has the key") for k in ("rows.json", "rows_rerun0.json", "rows_rerun01.json")],
            ("re-run drop 1", s(lambda d: d["engines"]["mazda_25t"]["reruns"].update({"rows_rerun1.json": {"drop": 1}})),
             None, "reruns.rows_rerun1.json.drop is 1"),
            ("a backend record without a summary", None, good_b, "exists without"),
            ("backend schema", good_s, b(lambda d: d.update(schema="epa-backend/0")), "schema is 'epa-backend/0'"),
            ("the B58 dropped", good_s, b(lambda d: d["engines"]["b58"].update(drop=True)), "never dropped"),
            ("the Honda readmitted", good_s, b(lambda d: d["engines"]["honda_l15b7"].update(drop=False)),
             "every Run 2 drop is repeated as True"),
            ("no Ford in the backend record", good_s, b(lambda d: d["engines"].pop("ford_27tt")), "engines is"),
            ("backend drop None", good_s, b(lambda d: d["engines"]["ford_27tt"].update(drop=None)),
             "engines.ford_27tt.drop is None"),
        ]
        for name, summary, backend, text in cases:
            with self.subTest(case=name):
                with self.assertRaises(ValueError) as cm:
                    engines.trainable_from(summary, backend)
                self.assertIn(text, str(cm.exception))
                self.assertIn("row 139", str(cm.exception))
        self.assertEqual(engines.trainable_from(good_s, None), ("b58", "ford_27tt", "mazda_25t"))
        self.assertEqual(engines.trainable_from(None, None), ("b58",))

    def test_the_rerun_of_the_highest_k_governs(self):
        """Row 139 (1): the re-run entry of the highest k, else the engine's own, read as recorded; never
        the first entry once a re-run's exists, never a union. Control: without re-runs the first decides."""
        def with_reruns(first, **runs):
            return summary_of({"mazda_25t": first}, {"mazda_25t": {f"rows_rerun{k[1:]}.json": d for k, d in runs.items()}})
        self.assertNotIn("mazda_25t", engines.trainable_from(with_reruns(True), None))
        self.assertIn("mazda_25t", engines.trainable_from(with_reruns(False), None))
        self.assertIn("mazda_25t", engines.trainable_from(with_reruns(True, k1=False), None))
        self.assertNotIn("mazda_25t", engines.trainable_from(with_reruns(False, k1=True), None))
        self.assertIn("mazda_25t", engines.trainable_from(with_reruns(True, k1=True, k2=False), None))
        self.assertNotIn("mazda_25t", engines.trainable_from(with_reruns(False, k2=True, k10=True), None))
        self.assertIn("mazda_25t", engines.trainable_from(with_reruns(False, k2=True, k10=False), None))

    def test_open_and_unlisted_reruns(self):
        """open_reruns and unlisted_reruns walk k = 1, 2, ... until neither name exists, at HEAD or in the
        work tree: a STARTED_rerun2 after a closed first re-run is open; a STARTED_rerun1 deleted from the
        work tree but at HEAD still counts. Controls: the closed re-run listed, nothing open or unlisted."""
        r1, s1, s2 = engines.RERUN_ROWS.format(k=1), engines.RERUN_STARTED.format(k=1), engines.RERUN_STARTED.format(k=2)
        summary = summary_of({}, {"mazda_25t": {r1: False}})
        root = records_repo(summary, validation_files=(f"mazda_25t/{s1}", f"mazda_25t/{r1}"))
        self.assertEqual(engines.open_reruns(root, epa=EPA_PLANTS), [])
        self.assertEqual(engines.unlisted_reruns(root, summary, epa=EPA_PLANTS), [])
        self.assertEqual(engines.unlisted_reruns(root, summary_of({}), epa=EPA_PLANTS), [("mazda_25t", 1)])
        root = records_repo(summary, validation_files=(f"mazda_25t/{s1}", f"mazda_25t/{r1}",
                                                       (f"mazda_25t/{s2}", "untracked")))
        self.assertEqual(engines.open_reruns(root, epa=EPA_PLANTS), [("mazda_25t", 2)])
        root = records_repo(summary, validation_files=((f"ford_27tt/{s1}", "deleted"),))
        self.assertEqual(engines.open_reruns(root, epa=EPA_PLANTS), [("ford_27tt", 1)])

    def test_trainable_is_trainable_in_the_records_root(self):
        """RECORDS_ROOT is this module's folder, and trainable() reads it. Control: with RECORDS_ROOT patched
        to a synthetic root dropping the Honda, trainable() leaves the Honda out."""
        self.assertEqual(engines.RECORDS_ROOT, engines.HERE)
        self.assertEqual(engines.trainable(), engines.trainable_in(engines.HERE))
        with mock.patch.object(engines, "RECORDS_ROOT", records_repo(summary_of({"honda_l15b7": True}))):
            self.assertEqual(engines.trainable(), ("b58", "ford_27tt", "mazda_25t"))

    def test_outside_a_git_work_tree_every_parser_refuses(self):
        """Row 139 (2): a folder that is no git work tree is refused, naming it, and so is a root that is no
        folder. Control: the same folder after `git init` reads ("b58",)."""
        root = scratch()
        for r in (root, os.path.join(root, "absent")):
            with self.subTest(root=r):
                with self.assertRaises(ValueError) as cm:
                    engines.trainable_in(r)
                self.assertIn("is not a git work tree", str(cm.exception))
                self.assertIn("row 139 (2)", str(cm.exception))
        git(root, "init", "-q")
        self.assertEqual(engines.trainable_in(root), ("b58",))


# ------------------------------------------------------------------ never at import
IMPORT_CHILD = """
import json, os, sys
sys.path.insert(0, {here!r})
root = os.path.normcase(os.path.abspath({root!r}))
records = [os.path.normcase(os.path.abspath(os.path.join(r, p))) for r in ({here!r}, root)
           for p in ({summary_rel!r}, {backend_rel!r})]
validation = [os.path.normcase(os.path.abspath(os.path.join(r, {val_rel!r}))) for r in ({here!r}, root)]
seen, phase = {{"open": [], "git": []}}, ["engines"]
def hook(event, args):
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        p = os.path.normcase(os.path.abspath(os.fsdecode(args[0])))
        if p in records or any(p.startswith(v + os.sep) for v in validation):
            seen["open"].append(p)
    elif event == "subprocess.Popen":
        argv = args[1] if isinstance(args[1], (list, tuple)) else [args[1]]
        if args[2] is not None and argv and os.path.basename(os.fsdecode(argv[0])).startswith("git"):
            cwd = os.path.normcase(os.path.abspath(os.fsdecode(args[2])))
            # engines' own import reads the repository's records, the five's the synthetic root's
            if cwd == root or (cwd == os.path.normcase({here!r}) and phase == ["engines"]):
                seen["git"].append(" ".join(map(os.fsdecode, argv)))
sys.addaudithook(hook)
import engines
after = {{"engines": dict(open=list(seen["open"]), git=list(seen["git"]))}}
phase[0] = "entry points"
engines.RECORDS_ROOT = {root!r}
for m in ("train", "train_all", "run_phase_d", "evaluate", "benchmark_training"):
    __import__(m)
    after[m] = dict(open=list(seen["open"]), git=list(seen["git"]))
called = engines.trainable_in({root!r})
after["control"] = dict(open=list(seen["open"]), git=list(seen["git"]), trainable=list(called))
print({mark!r} + json.dumps(after))
"""


class NotAtImport(unittest.TestCase):
    def test_importing_the_entry_points_opens_no_record(self):
        """A child process records every open of a record (summary.json, EPA_BACKEND.json or anything under
        results/EPA_VALIDATION/) and every git run in the records' tree, then imports engines and, with
        RECORDS_ROOT pointing at a synthetic root holding a committed summary, the five entry points, calling
        no main: nothing is opened and no git runs, so calibrate_epa.py's audit (calibrate_epa.py:337-338)
        never meets a record at import. The control: the same child then calls trainable_in on that root, and
        the hook sees the summary opened and git run there."""
        root = records_repo(summary_of({"honda_l15b7": True}))
        code = IMPORT_CHILD.format(here=HERE, root=root, summary_rel=engines.VALIDATION_SUMMARY_REL,
                                   backend_rel=engines.BACKEND_REL, val_rel=engines.VALIDATION_DIR_REL, mark=MARK)
        p = subprocess.run([sys.executable, "-B", "-c", code], cwd=HERE, capture_output=True, text=True, timeout=1200,
                           env=ENV)
        lines = [ln for ln in p.stdout.splitlines() if ln.startswith(MARK)]
        self.assertEqual((p.returncode, len(lines)), (0, 1), (p.stdout + p.stderr)[-3000:])
        after = json.loads(lines[0][len(MARK):])
        for m in ("engines", "train", "train_all", "run_phase_d", "evaluate", "benchmark_training"):
            with self.subTest(imported=m):
                self.assertEqual(after[m], dict(open=[], git=[]))
        ctl = after["control"]
        self.assertEqual(ctl["trainable"], ["b58", "ford_27tt", "mazda_25t"])
        want = os.path.normcase(os.path.abspath(os.path.join(root, engines.VALIDATION_SUMMARY_REL)))
        self.assertIn(want, ctl["open"])
        self.assertTrue(ctl["git"], ctl)


# ------------------------------------------------------------------ one definition
class OneDefinition(unittest.TestCase):
    def test_the_record_names_and_the_drop_reading_agree(self):
        """engines' record names are validate_epa's and epa_roads' (both hashed modules that import engines,
        so engines types them); the EPA set read is thresholds.common.EPA_ENGINES; and for each of the 8
        drop patterns over the three engines, epa_roads.dropped_problems agrees with the engines trainable
        leaves out (two readers of one drop, mistake 10). The control: a --dropped list one engine off is
        refused by dropped_problems. Importing either module installs no audit hook (theirs are inside
        validate_epa.audited and epa_roads.install_guard)."""
        import itertools
        import epa_roads
        import validate_epa
        from thresholds import common
        self.assertEqual(engines.VALIDATION_SUMMARY_REL, validate_epa.VAL_REL + "/" + validate_epa.SUMMARY)
        self.assertEqual(engines.VALIDATION_SUMMARY_REL, epa_roads.SUMMARY_REL)
        self.assertEqual(engines.VALIDATION_SUMMARY_SCHEMA, validate_epa.SUMMARY_SCHEMA)
        self.assertEqual(tuple(EPA_PLANTS), tuple(common.EPA_ENGINES))
        self.assertEqual(engines.NEVER_DROPPED, "b58")
        for bits in itertools.product((False, True), repeat=len(EPA_PLANTS)):
            drops = dict(zip(EPA_PLANTS, bits))
            with self.subTest(drops=drops):
                summary = summary_of(drops)
                left_out = set(EPA_PLANTS) - set(engines.trainable_from(summary, None))
                self.assertEqual(left_out, {e for e, d in drops.items() if d})
                self.assertEqual(epa_roads.dropped_problems(summary, dropped=left_out), [])
                self.assertTrue(epa_roads.dropped_problems(summary, dropped=left_out ^ {"ford_27tt"}))


# ------------------------------------------------------------------ an engine opened reaches the recorder
class Openable(unittest.TestCase):
    def test_every_trainable_engine_can_be_recorded(self):
        """Each engine trainable() gives on the real tree, and each of the four with RECORDS_ROOT at a
        synthetic root keeping them all: its schema-4 fingerprint is built (protocol phase-d, reward_knock
        False; decision 91 flipped, the Honda's transmission kind 'cvt'), and two steps of a stepped car's
        locked climb are recorded by step_record, so an engine trainable() opens reaches train.py's
        recorder. The CVT's step is refused by step_record.gear (amendment B16), since ORDER step 12a's CVT
        branch (C2) is not built (row 146 (3): Run 2 dropped the Honda); the real tree's records therefore
        must keep no CVT, which is asserted (a re-run that kept the Honda would need C2 first)."""
        import engine_env as E
        import fingerprint as FP
        import step_record as SR
        with mock.patch.object(engines, "RECORDS_ROOT", records_repo(summary_of({}), backend_of({}))):
            every = engines.trainable()
        self.assertEqual(every, tuple(engines.known()))
        self.assertEqual([n for n in engines.trainable() if isinstance(engines.get(n).car, engines.CvtCar)], [],
                         "the real tree's records keep a CVT engine, which step_record cannot record without C2")
        for n in sorted(set(engines.trainable()) | set(every), key=engines.known().index):
            with self.subTest(engine=n):
                plant = engines.get(n)
                fp = FP.plant_fingerprint(protocol="phase-d", plant=plant, train_backend=FP.BACKEND_CYCLE,
                                          score_backend=FP.BACKEND_CYCLE, preview_h_s=E.PREVIEW_H_S,
                                          reward_knock=False)
                self.assertEqual((fp["schema"], fp["engine"]), (FP.SCHEMA_VERSION, plant.id))
                cvt = isinstance(plant.car, engines.CvtCar)
                self.assertEqual(fp["transmission"]["kind"], "cvt" if cvt else "stepped")
                env = E.SupervisoryTunerEnv(E.locked_climb(plant, duration=30.0, dt=1.0), plant=plant, dt=1.0,
                                            seed=0, use_preview=True, reward_knock=False)
                obs, _ = env.reset(seed=0)
                rec = SR.new()
                if cvt:
                    a = E.neutral_action()
                    o2, r, term, trunc, info = env.step(a)
                    with self.assertRaisesRegex(ValueError, r"A CVT is never recorded \(amendment B16\)"):
                        SR.step(rec, env, a, obs, r, info)
                    continue
                for _ in range(2):
                    a = E.neutral_action()
                    o2, r, term, trunc, info = env.step(a)
                    SR.step(rec, env, a, obs, r, info)
                    obs = o2
                self.assertEqual(len(rec["reward"]), 2)
                self.assertEqual(len(rec["gear"]), 2)
                # a stepped box's gear count, 0 at rest (the climb's first step starts from it)
                self.assertTrue(all(0 <= g <= len(plant.car.gears) for g in rec["gear"]), rec["gear"])


# ------------------------------------------------------------------ the source
class Source(unittest.TestCase):
    def test_each_engine_argument_takes_trainable(self):
        """Every add_argument("--engine", ...) of the five entry points has
        choices=engines.trainable(); fingerprint.py keeps known() (amendment B7)."""
        for s, want in [(s, "trainable") for s in ENTRY_POINTS] + [("fingerprint.py", "known")]:
            with open(os.path.join(HERE, s), encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=s)
            found = []
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "add_argument" and node.args
                        and isinstance(node.args[0], ast.Constant) and node.args[0].value == "--engine"):
                    ch = {k.arg: k.value for k in node.keywords}.get("choices")
                    found.append(ast.unparse(ch) if ch is not None else None)
            with self.subTest(script=s):
                self.assertEqual(found, [f"engines.{want}()"])


# fingerprint.py's command line on an UNCALIBRATED plant (amendment B7; the review
# of P5, 22 October 2026). The child registers mazda_25t on a probe engine spec:
# the B58's spec read through engines.read_spec with an EPA engine's top-level keys,
# whose derived file and freeze record do not exist (a folder no calibration
# writes). Nothing is built: the refusal comes before engines.get. The control
# makes engines.calibrated() say yes, so the same command reaches engines.get and
# dies there, in derived.py, with a traceback: the assertions below are the
# refusal's, and would fail if fingerprint.py stopped calling it. The probe's
# derived file is derived.engine_path's, relative with "/" as a spec writes it, so
# this file carries no literal of that folder (amendment C3's scan forbids it
# outside epa_rows.py; the review of P5, 22 October 2026).
PROBE_DERIVED = os.path.relpath(derived.engine_path("_uncalibrated_probe"), HERE).replace(os.sep, "/")
PROBE_FREEZE = "results/EPA_CALIBRATION/_uncalibrated_probe/freeze.json"
FP_CHILD = """
import runpy, sys
sys.path.insert(0, {here!r})
import engines
real = engines.read_spec
def read_spec(name):
    if name != "_uncalibrated_probe":
        return real(name)
    spec = real("b58")
    spec["_meta"] = dict(spec["_meta"], derived_set="epa", derived={derived!r}, freeze={freeze!r})
    return spec
engines.read_spec = read_spec
engines.PLANTS["mazda_25t"] = ("_uncalibrated_probe", "a90_supra")
if {control}:
    engines.calibrated = lambda name: True
sys.argv = ["fingerprint.py", "--engine", "mazda_25t"]
runpy.run_path({path!r}, run_name="__main__")
"""


class FingerprintCli(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for f in (PROBE_DERIVED, PROBE_FREEZE):
            assert not os.path.exists(os.path.join(HERE, f)), f"{f} exists: the probe would be calibrated"

        def go(control):
            code = FP_CHILD.format(here=HERE, derived=PROBE_DERIVED, freeze=PROBE_FREEZE, control=control,
                                   path=os.path.join(HERE, "fingerprint.py"))
            p = subprocess.run([sys.executable, "-B", "-c", code], cwd=HERE, capture_output=True, text=True,
                               timeout=600, env=ENV)
            return p.returncode, p.stdout + p.stderr
        cls.refused, cls.control = go(False), go(True)

    def test_an_uncalibrated_plant_is_refused_by_name(self):
        rc, out = self.refused
        self.assertNotEqual(rc, 0, out[-2000:])
        self.assertIn("fingerprint.py: plant 'mazda_25t' is not calibrated yet: no " + PROBE_DERIVED, out)
        self.assertIn("python calibrate_epa.py fit --engine _uncalibrated_probe, then e6, complete and check", out)
        self.assertNotIn("Traceback", out)

    def test_the_control_calibrated_says_yes_and_it_dies_elsewhere(self):
        """Mistake 12: without the refusal the command still fails, in derived.py,
        with a traceback and no refusal text, so the test above is the refusal's."""
        rc, out = self.control
        self.assertNotEqual(rc, 0, out[-2000:])
        self.assertIn("Traceback", out)
        self.assertIn("FileNotFoundError", out)
        self.assertNotIn("is not calibrated yet", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)

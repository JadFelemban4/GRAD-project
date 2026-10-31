"""test_tit_cap.py -- row 105's cap script (tit_cap.py) and decision 62's TIT-cap ECU (tit_cap_ecu.py), tested.

    python -B test_tit_cap.py        about 90 s (38 tests: 87.7 s and 87.9 s on 31 October 2026, each run beside two
                                     other suites); exit code 0 when all pass

ORDER step 5 (docs/build_step_2/ORDER_TO_TRAINING.md, step 5) asks for "its test (no other epa_rows reader, no
table named)". Three classes, every one inside test_epa_fixtures.forbid_real_data (Guarded), so no test opens a
real EPA table, the real contract or logs/:

  Scans     tit_cap.py names of epa_rows only tit_cap.READS_ALLOWED and calls no row reader but calibration_rows;
            it opens no file outside tit_cap.OPEN_ALLOWED, starts no child outside tit_cap.PROCESS_ALLOWED, imports
            nothing dynamically, calls no getattr and reaches no epa_rows through another module (tit_cap_scan; the
            review's three mutants and four more as controls, mistake 12); its prelude comes before the first
            project import; neither module nor this file names a table; test_epa_rows' rules (scan_source,
            scan_words) pass on all three; tit_cap_ecu.py imports no row reader; the import closure of every
            frozen, hashed and roads module holds neither new module (rule 2 of the task; row 121)
  Reader    tit_cap on a SYNTHETIC repository (test_epa_fixtures.make_repo, as test_validate_guards uses it), so no
            real row is read: the cap is the highest calibration Final TIT and moves with it; held-out rows, poisoned
            three ways (epa_rows.POISONS) or raised far above the cap, move nothing of the record; the only epa_rows
            functions called from outside epa_rows are tit_cap's audit_paths and its one calibration_rows (every
            public function wrapped); a table opened or another reader called anywhere but inside that call is
            refused at run time by the audit; the record's schema and fields, written once, never inside another
            work tree or under results/EPA_CALIBRATION/; the frozen plant, code and contract checked before any row;
            the Ford only; the command line in-process; cap_from_record and its refusals
  Patch     the ECU patch on engines.get("ford_27tt"), a short climb at dt 1 s: bit for bit the unpatched ECU at
            a cap above every TIT; at a cap below, TIT <= cap at every held step and a lambda leaner by
            LAMBDA_TOL above it (minimality), every unheld step at the lambda of least TIT in bounds and never
            hotter than the ECU's own; the lambda, spark, cam, rpm, iat, ect and MAP recorded are what the
            baseline's load loop ran; least_tit on known functions; the cap moved moves the enrichment (mistake
            12); the original step back after a normal exit and after an exception; the B58 unaffected; a copy of
            the Ford's ECU refused; climb's control and its refusal of a context that capped nothing
"""
import ast
import contextlib
import dataclasses
import hashlib
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

import calibrate_epa  # noqa: E402
import engine_env as E  # noqa: E402
import engines  # noqa: E402
import epa_freeze  # noqa: E402
import epa_rows  # noqa: E402
import fingerprint  # noqa: E402
import plant as P  # noqa: E402
import test_epa_fixtures as F  # noqa: E402
import test_epa_rows as R  # noqa: E402
import tit_cap  # noqa: E402
import tit_cap_ecu as T  # noqa: E402
from thresholds import common  # noqa: E402

FORD = "ford_27tt"
B58 = "b58"
NEW = ("tit_cap.py", "tit_cap_ecu.py")
# The modules nothing new may be imported by, at any depth: PLANT_CODE, CODE_HASHED, the training code, the roads
# record's entry and named modules (row 97: epa_roads.py, roads_ceiling.py and epa_roads.NAMED_MODULES, counted
# when they exist in this tree) and the hashed modules the task names (rule 2), and the generator.
FROZEN_IMPORTERS = ("fingerprint.py", "train.py", "step_record.py", "random_road.py", "check_premise.py",
                    "preview_ceiling.py", "evaluate.py", "epa_roads.py", "roads_ceiling.py", "epa_stats.py",
                    "k3_knee.py", "epa_coefficients.py")


def read(rel):
    with open(os.path.join(HERE, rel), encoding="utf-8") as fh:
        return fh.read()


def epa_rows_uses(src):
    """(every epa_rows name the source uses, the epa_rows functions it calls, the problems): names reached as
    <binding>.<name> where the binding is `import epa_rows [as x]`, and `from epa_rows import <name>`; a binding
    used bare (aliased, passed, given to getattr) is a problem, since a scan of attributes cannot follow it."""
    tree = ast.parse(src)
    binds, names, called, problems = set(), set(), set(), []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name == "epa_rows":
                    binds.add(a.asname or a.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "epa_rows":
            names.update(a.name for a in node.names)
            problems += [f"from epa_rows import {a.name}" for a in node.names if a.name not in tit_cap.READS_ALLOWED]
    attr_values = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in binds:
            names.add(node.attr)
            attr_values.add(id(node.value))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and \
                isinstance(node.func.value, ast.Name) and node.func.value.id in binds:
            called.add(node.func.attr)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in binds and id(node) not in attr_values:
            problems.append(f"epa_rows used bare at line {node.lineno}")
    problems += [f"epa_rows.{n}" for n in sorted(names - set(tit_cap.READS_ALLOWED))]
    return names, called, problems


def _walk(node, where=()):
    """Every node of a tree with the names of the functions enclosing it."""
    yield node, where
    inner = where + (node.name,) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else where
    for child in ast.iter_child_nodes(node):
        yield from _walk(child, inner)


# What tit_cap_scan refuses (the review's finding I1: the epa_rows scan cannot see a table opened directly, a
# reader reached through another module's attribute, or one reached by a dynamic import).
BANNED_MODULES = tuple(R.OPENER_MODULES) + ("csv", "importlib", "runpy", "builtins", "ctypes", "_ctypes", "_winapi",
                                            "multiprocessing", "concurrent", "pickle", "shelve", "zipfile", "tarfile")
BANNED_NAMES = ("__import__", "eval", "exec", "compile", "__builtins__", "globals", "vars", "locals", "getattr",
                "__loader__", "__spec__")
READER_ATTRS = ("read_text", "read_bytes", "loadtxt", "genfromtxt", "fromfile", "read_csv", "FileIO", "memmap",
                "open_code", "getline", "getlines", "updatecache")
OS_BANNED = ("open", "fdopen", "popen", "system", "startfile", "fork", "forkpty", "posix_spawn", "posix_spawnp",
             "read")


def tit_cap_scan(src):
    """[problem] of tit_cap.py's source beyond epa_rows_uses: a call to open outside tit_cap.OPEN_ALLOWED; the name
    subprocess outside tit_cap.PROCESS_ALLOWED; an os function that opens a file or starts a process; a standard
    reader of a path; an import of BANNED_MODULES; a dynamic import, an evaluation, getattr, vars or globals; any
    attribute named epa_rows (another module's re-export), sys.modules or __dict__; epa_rows imported from
    another module."""
    out = []
    for node, where in _walk(ast.parse(src)):
        line = getattr(node, "lineno", 0)
        if isinstance(node, ast.Import):
            out += [f"import {a.name} (line {line})" for a in node.names if a.name.split(".")[0] in BANNED_MODULES]
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".")[0] in BANNED_MODULES:
                out.append(f"from {node.module} import ... (line {line})")
            if node.module != "epa_rows" and any(a.name == "epa_rows" for a in node.names):
                out.append(f"from {node.module} import epa_rows (line {line})")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
            if not any(f in tit_cap.OPEN_ALLOWED for f in where):
                out.append(f"open outside {tit_cap.OPEN_ALLOWED} (line {line}, in {where})")
        elif isinstance(node, ast.Name):
            if node.id == "subprocess" and not any(f in tit_cap.PROCESS_ALLOWED for f in where):
                out.append(f"subprocess outside {tit_cap.PROCESS_ALLOWED} (line {line}, in {where})")
            if node.id in BANNED_NAMES:
                out.append(f"{node.id} (line {line})")
        elif isinstance(node, ast.Attribute):
            if node.attr == "epa_rows" or node.attr == "__dict__":
                out.append(f".{node.attr} (line {line})")
            if isinstance(node.value, ast.Name) and node.value.id == "sys" and node.attr == "modules":
                out.append(f"sys.modules (line {line})")
            if isinstance(node.value, ast.Name) and node.value.id == "os" and (
                    node.attr in OS_BANNED or node.attr.startswith(("exec", "spawn"))):
                out.append(f"os.{node.attr} (line {line})")
            if node.attr in READER_ATTRS:
                out.append(f".{node.attr} (line {line})")
    return out


def raw(path):
    with open(path, "rb") as fh:
        return fh.read()


def imports_of(src):
    out = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            out.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            out.add(node.module)
            out.update(f"{node.module}.{a.name}" for a in node.names)
    return out


def module_files(name, root):
    """The project files a module name resolves to under root (its packages' __init__.py included), as
    epa_roads._module_files resolves them."""
    parts, out = name.split("."), []
    for i in range(1, len(parts) + 1):
        base = os.path.join(root, *parts[:i])
        if os.path.isfile(base + ".py"):
            out.append("/".join(parts[:i]) + ".py")
            break
        if os.path.isfile(os.path.join(base, "__init__.py")):
            out.append("/".join(parts[:i]) + "/__init__.py")
        else:
            break
    return out


def import_closure(entries, root):
    """Every project module the entries import at any depth, at any nesting (an import inside a function counts),
    entries included, as epa_roads.import_closure computes one entry's (the roads record's hashed list, row 97)."""
    seen, todo = set(), [e for e in entries if os.path.isfile(os.path.join(root, *e.split("/")))]
    while todo:
        rel = todo.pop()
        if rel in seen:
            continue
        seen.add(rel)
        with open(os.path.join(root, *rel.split("/")), encoding="utf-8") as fh:
            for name in imports_of(fh.read()):
                todo += [f for f in module_files(name, root) if f not in seen]
    return seen


def table_names():
    return sorted({s.name for specs in epa_rows.TABLES.values() for s in specs})


# =====================================================================================================
class Scans(F.Guarded):
    def test_the_script_names_only_the_allowed_epa_rows_names(self):
        names, called, problems = epa_rows_uses(read("tit_cap.py"))
        self.assertEqual(problems, [])
        self.assertIn("calibration_rows", called)
        # the one reader of rows; audit_paths builds paths (Reader.test_audit_paths_opens_nothing)
        self.assertEqual(called - {"audit_paths"}, {"calibration_rows"})
        self.assertLessEqual(names, set(tit_cap.READS_ALLOWED))

    def test_the_allowed_names_hold_one_reader(self):
        """Of READS_ALLOWED, the callables of epa_rows are calibration_rows and audit_paths only; every other public
        callable of epa_rows (manifest, calibration_contract, engine_facts, the held-out readers ...) is out."""
        funcs = {n for n, v in vars(epa_rows).items() if not n.startswith("_") and type(v).__name__ == "function"}
        self.assertEqual(set(tit_cap.READS_ALLOWED) & funcs, {"calibration_rows", "audit_paths"})
        for n in ("manifest", "calibration_contract", "calibration_coverage", "engine_facts", "check_tables"):
            self.assertIn(n, funcs - set(tit_cap.READS_ALLOWED))

    def test_the_scan_can_fail(self):
        """Mistake 12: each way of reaching another reader is flagged."""
        for src in ("import epa_rows\nepa_rows.manifest('x', source=1)\n",
                    "import epa_rows as er\ner.calibration_contract('x', source=1)\n",
                    "from epa_rows import engine_facts\n",
                    "import epa_rows\ngetattr(epa_rows, 'held_' + 'out_keys')('x', source=1)\n",
                    "import epa_rows\nm = epa_rows\nm.calibration_coverage('x', source=1)\n"):
            self.assertNotEqual(epa_rows_uses(src)[2], [], src)
        self.assertEqual(epa_rows_uses("import epa_rows\nepa_rows.calibration_rows('x', source=1)\n")[2], [])

    def test_the_script_reaches_no_reader_another_way(self):
        self.assertEqual(tit_cap_scan(read("tit_cap.py")), [])
        self.assertEqual(set(tit_cap.OPEN_ALLOWED), {"egt_limit", "write_once"})
        self.assertEqual(set(tit_cap.PROCESS_ALLOWED), {"work_tree_of"})

    def test_the_wider_scan_can_fail(self):
        """Mistake 12, the review's finding I1: its three mutants of tit_cap.py (a table opened directly in the
        read, another reader through calibrate_epa's re-export, a held-out reader by a dynamic import), each of
        which passes epa_rows_uses, scan_source and scan_words, and four more, are each flagged by tit_cap_scan."""
        src = read("tit_cap.py")
        anchor = "    audit.sealed, audit.refuse_tables = False, False\n"
        self.assertEqual(src.count(anchor), 1)
        mutants = {
            "M1": ("    for _t in epa_rows.audit_paths(engine, source=source)['table_files']:\n"
                   "        with open(os.path.join(source.root, *_t.split('/')), encoding='utf-8') as _fh:\n"
                   "            _raw = _fh.read()\n"),
            "M2": "    _c = calibrate_epa.epa_rows.calibration_contract(engine, source=source)\n",
            "M3": ("    import importlib\n    _m = importlib.import_module('epa_' + 'rows')\n"
                   "    _k = getattr(_m, 'held_' + 'out_' + 'keys')(engine, source=source)\n"),
            "M4": "    _m = __import__('epa_' + 'rows')\n",
            "M5": "    _m = sys.modules['epa_' + 'rows']\n",
            "M6": "    subprocess.run(['git', 'show', 'HEAD:x'], capture_output=True)\n",
            "M7": "    from calibrate_epa import epa_rows as _er\n",
        }
        for k, new in mutants.items():
            m = src.replace(anchor, anchor + new)
            self.assertNotEqual(tit_cap_scan(m), [], k)
            if k in ("M1", "M2", "M3"):
                # the hole the wider scan closes: the epa_rows scan and test_epa_rows' rules pass these
                self.assertEqual(epa_rows_uses(m)[2], [], k)
                self.assertEqual(R.scan_source(m, "tit_cap.py"), [], k)

    def test_the_prelude_comes_before_any_project_import(self):
        """As test_calibrate_epa checks calibrate_epa's (WP3_INTERFACES.md 3.3): the `if __name__ == "__main__"`
        that runs _prelude comes before the first project import, and _prelude installs the hook."""
        tree = ast.parse(read("tit_cap.py"))
        project = {os.path.splitext(f)[0] for f in os.listdir(HERE) if f.endswith(".py")} | {"thresholds"}
        first_project, prelude = None, None
        for i, node in enumerate(tree.body):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                if any(n.split(".")[0] in project for n in names) and first_project is None:
                    first_project = i
            if (isinstance(node, ast.If) and "__main__" in ast.unparse(node.test) and prelude is None
                    and "_prelude" in ast.unparse(node)):
                prelude = i
        self.assertIsNotNone(prelude)
        self.assertIsNotNone(first_project)
        self.assertLess(prelude, first_project)
        src = ast.unparse(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_prelude"))
        self.assertIn("addaudithook", src)

    def test_the_patch_reads_no_rows(self):
        imp = imports_of(read("tit_cap_ecu.py"))
        for m in ("epa_rows", "calibrate_epa", "tit_cap", "epa_freeze", "validate_epa"):
            self.assertNotIn(m, imp)

    def test_no_table_is_named(self):
        names = table_names()
        self.assertTrue(names)
        for rel in NEW + ("test_tit_cap.py",):
            src = read(rel)
            self.assertEqual([n for n in names if n in src], [], rel)
            self.assertEqual(R.scan_words(src, rel), [], rel)

    def test_the_rules_of_test_epa_rows_pass(self):
        for rel in NEW + ("test_tit_cap.py",):
            self.assertEqual(R.scan_source(read(rel), rel), [], rel)
        self.assertEqual(R.unguarded_test_classes(read("test_tit_cap.py"), "test_tit_cap.py"), [])
        # the control: the scan flags a table-folder string and a held-out reader in a new module's name
        self.assertTrue(R.scan_source("import epa_rows\nepa_rows.held_out_counts('x', source=1)\n", "tit_cap.py"))
        self.assertTrue(R.scan_source(f"p = '{R.DE}/x'\n", "tit_cap_ecu.py"))

    def test_no_frozen_module_imports_the_new_ones(self):
        """The review's finding I6: the import closure (at any depth) of PLANT_CODE, CODE_HASHED, thresholds/,
        FROZEN_IMPORTERS and the roads record's modules holds neither new module; the control is a module that
        imports tit_cap_ecu two imports away, whose closure does (mistake 12)."""
        entries = set(fingerprint.PLANT_CODE) | set(epa_freeze.CODE_HASHED) | set(FROZEN_IMPORTERS)
        entries |= {f"thresholds/{f}" for f in os.listdir(os.path.join(HERE, "thresholds")) if f.endswith(".py")}
        entries = sorted(e for e in entries if e.endswith(".py"))
        closure = import_closure(entries, HERE)
        self.assertIn("plant.py", closure)
        self.assertIn("epa_rows.py", closure)
        self.assertEqual(sorted(set(NEW) & closure), [])
        for rel in NEW:
            self.assertNotIn(rel, entries)
        tmp = tempfile.mkdtemp(prefix="tit_cap_closure_")
        self.addCleanup(shutil.rmtree, tmp, True)
        for rel, text in (("a.py", "def f():\n    import b\n"), ("b.py", "from tit_cap_ecu import capped\n"),
                          ("tit_cap_ecu.py", "")):
            with open(os.path.join(tmp, rel), "w", encoding="utf-8") as fh:
                fh.write(text)
        self.assertIn("tit_cap_ecu.py", import_closure(["a.py"], tmp))

    def test_the_two_modules_agree(self):
        """Mistake 10: the constants each module keeps for the other are equal."""
        self.assertEqual(T.SCHEMA, tit_cap.SCHEMA)
        self.assertEqual(T.RECORD_DIR, tit_cap.RECORD_DIR)
        self.assertEqual(T.RECORD_HASHED, tit_cap.HASHED)


# =====================================================================================================
def frozen(repo, *, plant_sha=None, code=None, contract_commit=None):
    """The Ford's freeze.json and complete.json in a synthetic repository, with the live plant_sha (or the one
    given), the code running (or the one given), the repository's contract commit (or the one given) and the
    live engine_sha: what tit_cap.frozen_provenance compares."""
    d = os.path.join(repo.root, "results", "EPA_CALIBRATION", FORD)
    os.makedirs(d, exist_ok=True)
    for f in ("freeze.json", tit_cap.COMPLETE):
        if os.path.exists(os.path.join(d, f)):
            os.remove(os.path.join(d, f))
    epa_freeze.write_json_atomic(os.path.join(d, "freeze.json"), {
        "plant": {"plant_sha": plant_sha or epa_freeze.plant_sha(FORD)}, "versions": epa_freeze.versions(),
        "code": code or epa_freeze.code_shas(root=HERE),
        "contract": {"commit": contract_commit or repo.contract_commit, "json_sha_text": "synthetic",
                     "md_sha_text": "synthetic"}})
    epa_freeze.write_json_atomic(os.path.join(d, tit_cap.COMPLETE),
                                 {"engine_sha": engines.engine_sha(engines.get(FORD))})


def tree(folder):
    out = {}
    for dp, _d, files in os.walk(folder):
        for f in files:
            with open(os.path.join(dp, f), "rb") as fh:
                out[os.path.relpath(os.path.join(dp, f), folder)] = hashlib.sha256(fh.read()).hexdigest()
    return out


def final_spec():
    return next(s for s in epa_rows.TABLES[FORD] if s.role == "final")


def point_specs():
    """The Ford's tables that carry a TIT: its steady tables and its Final table."""
    return [s for s in epa_rows.TABLES[FORD] if s.role in ("steady", "final")]


def set_tit(repo, spec, source_rows, value):
    """The synthetic table `spec`'s turbine_inlet_temp_c set to `value` on `source_rows`, the contract's table
    hashes recorded again (test_epa_fixtures.rehash_tables); the new Repo."""
    path = os.path.join(F.engine_folder(repo.root, FORD), spec.name)

    def edit(header, rows):
        i, s = header.index("turbine_inlet_temp_c"), header.index("source_row")
        return [r[:i] + [value] + r[i + 1:] if int(r[s]) in source_rows else r for r in rows]
    F.edit_table(path, edit)
    return F.rehash_tables(repo)


@contextlib.contextmanager
def recording_epa_rows():
    """Every public function of epa_rows wrapped while inside, so that each call made from outside epa_rows is
    recorded as (the caller's module, the function); epa_rows' calls among its own functions are not. Yields the
    list (the review's finding S4: a run-time check that reaches a reader called through a helper, an alias or a
    dynamic import, which no scan of the script's source sees)."""
    calls = []
    with contextlib.ExitStack() as stack:
        for n, v in sorted(vars(epa_rows).items()):
            if n.startswith("_") or not isinstance(v, types.FunctionType) or v.__module__ != "epa_rows":
                continue

            def wrap(f=v, n=n):
                def w(*a, **kw):
                    caller = sys._getframe(1).f_globals.get("__name__")
                    if caller != "epa_rows":
                        calls.append((caller, n))
                    return f(*a, **kw)
                return w
            stack.enter_context(mock.patch.object(epa_rows, n, wrap()))
        yield calls


class Reader(F.SyntheticRepoCase):
    def setUp(self):
        super().setUp()
        self.repo = self.fresh()
        frozen(self.repo)
        self.src = F.synthetic_source(self.repo)
        self.out = os.path.join(tempfile.mkdtemp(prefix="tit_cap_", dir=self._tmp.name), "ford_27tt.json")
        self.ford = engines.get(FORD)

    def finals(self, src):
        return [r for r in epa_rows.calibration_rows(FORD, source=src).rows if type(r) is epa_rows.FinalRow]

    def table(self, spec):
        return os.path.join(F.engine_folder(self.repo.root, FORD), spec.name)

    def test_the_cap_is_the_highest_calibration_final_tit(self):
        got, audit = tit_cap.read(FORD, source=self.src)
        rows = self.finals(self.src)
        best = max(r.tit_c for r in rows)
        self.assertEqual(got["cap"]["tit_c"], best)
        self.assertEqual(got["cap"]["tit_k"], best + 273.15)
        key = got["cap"]["row_key"]
        self.assertIn((key["table"], key["source_row"]), {(r.table, r.source_row) for r in rows if r.tit_c == best})
        self.assertEqual(key["table"], final_spec().name)
        self.assertEqual(got["final_rows"]["rows"], len(rows))
        self.assertEqual(got["cap"]["rows_at_max"], sum(r.tit_c == best for r in rows))
        self.assertEqual((got["final_rows"]["tit_c_min"], got["final_rows"]["tit_c_max"]),
                         (min(r.tit_c for r in rows), best))
        self.assertEqual(audit["refused_by_audit"], [])
        self.assertEqual(audit["outside_allowlist"], [])
        self.assertFalse(audit["before_the_audit"]["watched"])

    def test_held_out_rows_move_nothing_and_a_calibration_row_moves_the_cap(self):
        """Mistake 12; the review's finding I4. The whole of cap_of's output -- the cap, the Final rows' range, the
        steady maxima beside it, the rows read -- is the same when every held-out row of the Ford is poisoned in
        each of epa_rows.POISONS' three ways (the project's C8 pattern), and when a held-out row of the Final table
        and of each steady table is raised far above the cap; a calibration Final row raised above the cap
        becomes the cap."""
        ref = tit_cap.cap_of(FORD, epa_rows.calibration_rows(FORD, source=self.src))
        for how in epa_rows.POISONS:
            dst = tempfile.mkdtemp(prefix=f"tit_cap_poison_{how}_", dir=self._tmp.name)
            ps = epa_rows.poisoned_tables(FORD, source=self.src, dst_dir=dst, how=how)
            self.assertEqual(tit_cap.cap_of(FORD, epa_rows.calibration_rows(FORD, source=ps)), ref, how)
        got, _ = tit_cap.read(FORD, source=self.src)
        self.assertEqual(got, ref)
        cal = [r for r in self.finals(self.src) if r.tit_c < ref["cap"]["tit_c"]]
        held = F.held_rows(self.repo, FORD)
        repo = self.repo
        raised = 0
        for spec in point_specs():
            rows = held.get(spec.name, [])
            if rows:
                repo = set_tit(repo, spec, {rows[0]}, "4321.0")
                raised += 1
        self.assertGreaterEqual(raised, 2, "the synthetic Ford holds held-out rows in too few tables: this tests "
                                           "nothing")
        self.assertIn(final_spec().name, held)
        got2, _ = tit_cap.read(FORD, source=F.synthetic_source(repo))
        self.assertEqual(got2, ref)
        repo = set_tit(repo, final_spec(), {cal[0].source_row}, repr(ref["cap"]["tit_c"] + 50.0))
        got3, _ = tit_cap.read(FORD, source=F.synthetic_source(repo))
        self.assertEqual(got3["cap"]["tit_c"], ref["cap"]["tit_c"] + 50.0)
        self.assertEqual(got3["cap"]["row_key"], {"table": final_spec().name, "source_row": cal[0].source_row})

    def test_only_the_one_reader_is_called(self):
        """The review's finding S4, at run time: during compute, the only epa_rows functions called from outside
        epa_rows are tit_cap's audit_paths and its calibration_rows, once; the control, another reader called
        through a helper the script uses, is recorded (mistake 12)."""
        with recording_epa_rows() as calls:
            tit_cap.compute(FORD, source=self.src, out=self.out, argv=None)
        self.assertEqual(set(calls), {("tit_cap", "audit_paths"), ("tit_cap", "calibration_rows")})
        self.assertEqual(calls.count(("tit_cap", "calibration_rows")), 1)
        real = tit_cap.egt_limit

        def helper(engine, plant):
            epa_rows.manifest(engine, source=self.src)
            return real(engine, plant)
        out = os.path.join(os.path.dirname(self.out), "control.json")
        with recording_epa_rows() as calls, mock.patch.object(tit_cap, "egt_limit", helper):
            with self.assertRaises(tit_cap.Refused):
                tit_cap.compute(FORD, source=self.src, out=out, argv=None)
        self.assertIn("manifest", {n for _, n in calls})
        self.assertFalse(os.path.exists(out))

    def test_a_table_or_another_reader_outside_the_one_call_is_refused_at_run_time(self):
        """The review's finding I1, at run time: an open of the engine's own table, or a call of another reader
        (calibration_contract, which reads the contract), in any phase of compute but the calibration_rows call
        -- while out is checked (the tables refused), and while the plant is checked, the cap computed and the
        second cap read (sealed) -- crashes in the audit and refuses the record, and the audit's list names it.
        The control: the same open inside the calibration_rows call is admitted, which is why the source scans
        stand beside the audit."""
        path = self.table(final_spec())

        def opening(fn):
            def w(*a, **kw):
                with open(path, "rb") as fh:
                    fh.read(1)
                return fn(*a, **kw)
            return w

        def contract(fn):
            def w(*a, **kw):
                epa_rows.calibration_contract(FORD, source=self.src)
                return fn(*a, **kw)
            return w
        for i, (name, how) in enumerate((("out_problem", opening), ("frozen_provenance", opening),
                                         ("cap_of", opening), ("egt_limit", opening),
                                         ("frozen_provenance", contract), ("egt_limit", contract))):
            out = os.path.join(os.path.dirname(self.out), f"refused_{i}.json")
            with mock.patch.object(tit_cap, name, how(getattr(tit_cap, name))):
                with self.assertRaises(tit_cap.Refused, msg=f"{name} {how.__name__}") as cm:
                    tit_cap.compute(FORD, source=self.src, out=out, argv=None)
            self.assertIn("refused", str(cm.exception))
            self.assertFalse(os.path.exists(out))
        real = epa_rows.calibration_rows
        with mock.patch.object(epa_rows, "calibration_rows", opening(real)):
            rec, _ = tit_cap.compute(FORD, source=self.src, out=self.out, argv=None)
        self.assertEqual(rec["audit"]["refused_by_audit"], [])

    def test_the_record(self):
        rec, sha = tit_cap.compute(FORD, source=self.src, out=self.out, argv=None)
        with open(self.out, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), rec)
        self.assertEqual(common.sha_text(self.out), sha)
        self.assertEqual(rec["schema"], "epa-tit-cap/2")
        self.assertEqual(rec["plant"], FORD)
        for k in ("rule", "decisions", "cap", "sensitivity_egt_limit", "final_rows", "rows_read", "beside_steady_max",
                  "audit", "sha_text", "provenance", "versions", "versions_equal_freeze_json", "git", "argv",
                  "started_utc", "written_utc"):
            self.assertIn(k, rec)
        # rows cited by number, never by line (the review's finding S6: the decisions file grows)
        self.assertNotRegex(json.dumps(rec["decisions"]) + rec["rule"], r"\.md:\d")
        self.assertEqual(rec["decisions"]["105"], "results/VALIDATION_DECISIONS.md, row 105")
        self.assertIsNone(rec["argv"])
        eg = rec["sensitivity_egt_limit"]
        self.assertEqual(eg["tit_k"], self.ford.engine.damage.egt_limit_k)
        self.assertEqual((eg["label"], eg["unit"], eg["field"]), ("ASSUMED", "K", "engine.damage.egt_limit_k"))
        self.assertEqual(set(rec["sha_text"]), set(tit_cap.HASHED))
        for f, v in rec["sha_text"].items():
            self.assertEqual(v, common.sha_text(os.path.join(HERE, f)))
        pv = rec["provenance"]
        self.assertEqual((pv["plant_sha"], pv["engine_sha"]), (epa_freeze.plant_sha(FORD), engines.engine_sha(self.ford)))
        self.assertTrue(pv["equal"])
        self.assertEqual(pv["code_sha_text"], epa_freeze.code_shas(root=HERE))
        self.assertEqual(pv["code_changes_since_freeze"], [])
        self.assertEqual(pv["contract"]["source_contract_commit"], self.repo.contract_commit)
        self.assertEqual(pv["contract"]["freeze_json"]["commit"], self.repo.contract_commit)
        self.assertEqual(rec["versions"], epa_freeze.versions())
        self.assertTrue(rec["versions_equal_freeze_json"])
        g = rec["git"]
        self.assertEqual(g["commit"], epa_freeze.git_head(root=self.repo.root))
        self.assertEqual(g["code_commit"], epa_freeze.git_head(root=HERE))
        self.assertEqual(g["code_paths"], list(tit_cap.CODE))
        self.assertLessEqual(set(epa_freeze.CODE_HASHED) | set(tit_cap.HASHED), set(g["code_paths"]))
        a = rec["audit"]
        paths = epa_rows.audit_paths(FORD, source=self.src)
        self.assertLessEqual(set(paths["table_files"]), set(a["opened"]))
        others = [paths["engines"] + "/" + e + "/" for e in epa_rows.TABLES if e != FORD]
        self.assertEqual([p for p in a["opened"] if p.startswith(tuple(others))], [])
        self.assertEqual(a["subcommand"], tit_cap.SUBCOMMAND)
        self.assertEqual((a["refused_by_audit"], a["outside_allowlist"]), ([], []))
        self.assertEqual(a["before_the_audit"]["watched"], False)
        # the window is the command now: the freeze record, read by the frozen-plant check, is in the audit's list
        self.assertIn(f"results/EPA_CALIBRATION/{FORD}/freeze.json", a["opened"])
        n = {s["source"]: s["calibration_rows"] for s in rec["rows_read"]["by_source"]}
        self.assertEqual(n[final_spec().name], rec["final_rows"]["rows"])
        self.assertEqual(sum(n.values()), rec["rows_read"]["yield_rows"])

    def test_written_once(self):
        tit_cap.compute(FORD, source=self.src, out=self.out, argv=None)
        before = raw(self.out)
        with self.assertRaises(tit_cap.Refused):
            tit_cap.compute(FORD, source=self.src, out=self.out, argv=None)
        self.assertEqual(raw(self.out), before)
        self.assertFalse(os.path.exists(self.out + ".partial"))

    def test_nothing_is_written_under_the_calibration_folder(self):
        cal = os.path.join(self.repo.root, "results", "EPA_CALIBRATION")
        before = tree(cal)
        tit_cap.compute(FORD, source=self.src, out=self.out, argv=None)
        self.assertEqual(tree(cal), before)
        for rel in (("results", "EPA_CALIBRATION", FORD, "tit_cap.json"), ("data", "x.json"), ("logs", "x.json"),
                    ("results", "EPA_VALIDATION", FORD, "x.json")):
            out = os.path.join(self.repo.root, *rel)
            with self.assertRaises(tit_cap.Refused):
                tit_cap.compute(FORD, source=self.src, out=out, argv=None)
            self.assertFalse(os.path.exists(out))
        self.assertEqual(tree(cal), before)

    def test_another_work_tree_is_refused(self):
        """The review's findings S8 and I3: a path inside a work tree that is neither the code's nor the source's
        -- a linked worktree of the source's repository (test_epa_fixtures.add_worktree), another repository --
        is refused, under its results/EPA_CALIBRATION/ or its data/ and under its results/EPA_TIT_CAP/ alike, even
        with the code clean; the scratch folder outside every tree is admitted (test_the_record)."""
        wt = F.add_worktree(self.repo)
        other = os.path.join(tempfile.mkdtemp(prefix="tit_cap_other_", dir=self._tmp.name), "repo")
        os.makedirs(other)
        F.git(other, "init", "-q")
        for root in (wt, other):
            for rel in (("results", "EPA_CALIBRATION", FORD, "tit_cap.json"), ("data", "engines", FORD, "x.json"),
                        (*tit_cap.RECORD_DIR.split("/"), "ford_27tt.json")):
                out = os.path.join(root, *rel)
                with mock.patch.object(tit_cap, "code_clean", lambda: (True, ())):
                    why = tit_cap.out_problem(out, roots=(self.repo.root, HERE))
                self.assertIsNotNone(why, out)
                with self.assertRaises(tit_cap.Refused):
                    tit_cap.compute(FORD, source=self.src, out=out, argv=None)
                self.assertFalse(os.path.exists(out))
        self.assertIsNone(tit_cap.out_problem(self.out, roots=(self.repo.root, HERE)))
        self.assertEqual(os.path.normcase(tit_cap.work_tree_of(os.path.join(wt, "x", "y.json"))),
                         os.path.normcase(os.path.abspath(wt)))

    def test_a_record_in_the_tree_needs_committed_code(self):
        out = os.path.join(self.repo.root, *tit_cap.RECORD_DIR.split("/"), "ford_27tt.json")
        with mock.patch.object(tit_cap, "code_clean", lambda: (False, ("tit_cap.py",))):
            with self.assertRaises(tit_cap.Refused):
                tit_cap.compute(FORD, source=self.src, out=out, argv=None)
        self.assertFalse(os.path.exists(out))
        with mock.patch.object(tit_cap, "code_clean", lambda: (True, ())):
            rec, _ = tit_cap.compute(FORD, source=self.src, out=out, argv=None)
        self.assertTrue(os.path.isfile(out))
        self.assertTrue(rec["git"]["code_clean"])

    def test_the_frozen_plant_code_and_contract_are_checked_before_any_row(self):
        def no_read(*a, **kw):
            raise AssertionError("a row was read before the plant check")
        code = dict(epa_freeze.code_shas(root=HERE))
        code["calibrate_epa.py"] = "0" * 64
        for kw in ({"plant_sha": "0" * 16}, {"code": code}, {"contract_commit": "0" * 40}):
            frozen(self.repo, **kw)
            with mock.patch.object(epa_rows, "calibration_rows", no_read):
                with self.assertRaises(tit_cap.Refused, msg=str(kw)):
                    tit_cap.compute(FORD, source=self.src, out=self.out, argv=None)
            self.assertFalse(os.path.exists(self.out))
        frozen(self.repo)
        os.remove(os.path.join(self.repo.root, "results", "EPA_CALIBRATION", FORD, tit_cap.COMPLETE))
        with self.assertRaises(tit_cap.Refused):
            tit_cap.compute(FORD, source=self.src, out=self.out, argv=None)

    def test_the_ford_only(self):
        for e in ("mazda_25t", "honda_l15b7", B58, None):
            with self.assertRaises(tit_cap.Refused):
                tit_cap.compute(e, source=self.src, out=self.out, argv=None)
            with self.assertRaises(tit_cap.Refused):
                tit_cap.read(e, source=self.src)
        self.assertFalse(os.path.exists(self.out))

    def test_the_audits_refusals_refuse_the_record(self):
        """Mistake 12: an open the audit refuses, even one the code catches, and an open outside the allowlist
        each refuse the record; the control is test_the_record's empty lists."""
        real = epa_rows.calibration_rows
        forbidden = os.path.join(self.repo.root, "results", "EPA_VALIDATION", FORD, "x.json")
        outside = os.path.join(self.repo.root, "outside.txt")
        with open(outside, "w", encoding="utf-8") as fh:
            fh.write("x")

        def leaky(path):
            def calibration_rows(engine, *, source):
                try:
                    open(path, encoding="utf-8").close()
                except (PermissionError, FileNotFoundError):
                    pass
                return real(engine, source=source)
            return calibration_rows
        for path in (forbidden, outside):
            with mock.patch.object(epa_rows, "calibration_rows", leaky(path)):
                with self.assertRaises(tit_cap.Refused) as cm:
                    tit_cap.compute(FORD, source=self.src, out=self.out, argv=None)
            self.assertIn("allowlist", str(cm.exception))
            self.assertFalse(os.path.exists(self.out))

    def test_the_prelude_is_judged(self):
        """The opens before the audit (the prelude's, on the command line) are judged by the audit's rules: one of
        the engine's tables, another engine's folder, or a child process before the audit refuses the record; the
        command line's own opens (the code, the interpreter's files) do not."""
        tab = self.table(final_spec())
        mazda = os.path.join(F.engine_folder(self.repo.root, "mazda_25t"), "x.csv")
        clean = {"installed": True, "on": True, "opened": [os.path.join(HERE, "tit_cap.py"), sys.executable],
                 "processes": []}
        for i, early in enumerate(({**clean, "opened": clean["opened"] + [tab]},
                                   {**clean, "opened": clean["opened"] + [mazda]},
                                   {**clean, "processes": ["subprocess.Popen ('git',)"]})):
            out = os.path.join(os.path.dirname(self.out), f"early_{i}.json")
            with mock.patch.dict(tit_cap._EARLY, early):
                with self.assertRaises(tit_cap.Refused):
                    tit_cap.compute(FORD, source=self.src, out=out, argv=None)
            self.assertFalse(os.path.exists(out))
        with mock.patch.dict(tit_cap._EARLY, clean):
            rec, _ = tit_cap.compute(FORD, source=self.src, out=self.out, argv=None)
            self.assertFalse(tit_cap._EARLY["on"])
        b = rec["audit"]["before_the_audit"]
        self.assertTrue(b["watched"])
        self.assertEqual((b["forbidden"], b["outside_allowlist"], b["subprocesses"]), ([], [], []))
        self.assertEqual(b["python_files_opened"], 1)

    def test_a_loader_stop_refuses(self):
        path = self.table(final_spec())
        F.edit_table(path, lambda header, rows: rows)
        with open(path, "ab") as fh:
            fh.write(b"\n")
        with self.assertRaises(tit_cap.Refused) as cm:
            tit_cap.read(FORD, source=self.src)
        self.assertIn("loader guard", str(cm.exception))

    def test_audit_paths_opens_nothing(self):
        a = calibrate_epa.install_audit(subcommand=tit_cap.SUBCOMMAND, engine=FORD, root=self.repo.root, scratch=None)
        try:
            n0 = set(a.opened)
            epa_rows.audit_paths(FORD, source=self.src)
            n1 = set(a.opened)
        finally:
            calibrate_epa.deactivate()
        self.assertEqual(n1, n0)

    def test_the_command_line(self):
        """The review's finding I5: the command line in-process, inside forbid_real_data, its Source the synthetic
        one (epa_rows.Source.repository patched), so that no order of compute's checks can make it read the real
        tables: another engine refused (exit 2), no engine an argparse error, the Ford's record written with its
        argv."""
        src = self.src
        buf = io.StringIO()
        with mock.patch.object(epa_rows.Source, "repository", staticmethod(lambda: src)), \
                contextlib.redirect_stdout(buf):
            self.assertEqual(tit_cap.main(["compute", "--engine", "mazda_25t", "--out", self.out]),
                             tit_cap.EXIT_REFUSED)
            self.assertFalse(os.path.exists(self.out))
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                tit_cap.main(["compute"])
            argv = ["compute", "--engine", FORD, "--out", self.out]
            self.assertEqual(tit_cap.main(argv), tit_cap.EXIT_OK)
        self.assertIn("refused", buf.getvalue())
        with open(self.out, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["argv"], argv)

    def test_cap_from_record(self):
        """The review's finding I2: a record tit_cap wrote is read; one spoiled in any of the ways the writer
        refuses -- an audit that refused or found a path outside, a stale hash, a cap not its tit_c + 273.15, a
        second cap not the plant's, a hand-typed record -- is refused; committed=True refuses a scratch record and
        one whose code was not committed; committed_problem admits only RECORD_DIR/<plant>.json, tracked and
        unmodified."""
        rec, _ = tit_cap.compute(FORD, source=self.src, out=self.out, argv=None)
        self.assertEqual(T.cap_from_record(self.out, plant=self.ford, which="cap", committed=False)[0],
                         rec["cap"]["tit_k"])
        self.assertEqual(T.cap_from_record(self.out, plant=self.ford, which="egt_limit", committed=False)[0],
                         rec["sensitivity_egt_limit"]["tit_k"])
        with self.assertRaises(ValueError):
            T.cap_from_record(self.out, plant=self.ford, which="steady", committed=False)
        with self.assertRaises(ValueError):
            T.cap_from_record(self.out, plant=engines.get(B58), which="cap", committed=False)
        with self.assertRaises(ValueError):
            T.cap_from_record(self.out, plant=self.ford, which="cap", committed=True)
        self.assertTrue(T.record_problems(rec, plant=self.ford, committed=True))
        d = os.path.dirname(self.out)

        def spoiled(i, edit):
            r = json.loads(json.dumps(rec))
            edit(r)
            p = os.path.join(d, f"spoiled_{i}.json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(r, fh)
            return p
        edits = (lambda r: r["audit"].update(refused_by_audit=["results/EPA_VALIDATION/ford_27tt/x.json"]),
                 lambda r: r["audit"].update(outside_allowlist=["outside.txt"]),
                 lambda r: r["audit"]["before_the_audit"].update(watched=True, forbidden=["x"], outside_allowlist=[],
                                                                  subprocesses=[]),
                 lambda r: r["audit"].pop("before_the_audit"),
                 lambda r: r["sha_text"].update({"tit_cap_ecu.py": "0" * 64}),
                 lambda r: r["provenance"]["code_sha_text"].update({"epa_fit.py": "0" * 64}),
                 lambda r: r["cap"].update(tit_k=1400.0),
                 lambda r: r["sensitivity_egt_limit"].update(tit_k=1500.0),
                 lambda r: r.update(plant="mazda_25t"),
                 lambda r: r.update(schema="epa-tit-cap/1"),
                 lambda r: r["provenance"].update(engine_sha="0" * 16),
                 lambda r: [r.pop(k) for k in list(r) if k not in ("schema", "plant", "provenance", "cap")])
        for i, e in enumerate(edits):
            with self.assertRaises(ValueError, msg=str(i)):
                T.cap_from_record(spoiled(i, e), plant=self.ford, which="cap", committed=False)
        # committed_problem in a synthetic work tree: the right path, untracked, then committed, then modified
        target = os.path.join(self.repo.root, *T.RECORD_DIR.split("/"), f"{FORD}.json")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copyfile(self.out, target)
        self.assertIsNotNone(T.committed_problem(self.out, root=self.repo.root, name=FORD))
        self.assertIsNotNone(T.committed_problem(target, root=self.repo.root, name=FORD))
        F.commit_all(self.repo.root, "synthetic: the cap record")
        self.assertIsNone(T.committed_problem(target, root=self.repo.root, name=FORD))
        with open(target, "a", encoding="utf-8") as fh:
            fh.write(" ")
        self.assertIsNotNone(T.committed_problem(target, root=self.repo.root, name=FORD))


# =====================================================================================================
STEPS = 60
# The unheld lambda's TIT against a 61-point grid of [lam_floor, lambda_ECU] the module never evaluates: at most
# this far above the grid's least, in K. MEASURED 31 October 2026 over every unheld step of this class's two capped
# climbs (cap 500 K, 59 steps; cap_below, 5 steps): at most 0.0065 K above it (and down to 0.031 K below); the
# tolerance is three times that, below the model TIT's largest reversal on the probe's grid (0.0227 K).
UNHELD_GRID_TOL_K = 0.02


def short_climb(plant, n):
    """A short climb at dt 1 s: the plant's scenario speed held from the start and its grade ramped over 20 s
    (make_grade_climb's arrays, re-timed), so that the engine is loaded within a minute."""
    sc = plant.scenario
    cyc = E.make_grade_climb(duration=float(n), dt=1.0, t_amb=sc.t_amb, grade=sc.grade, v_kmh=sc.v_kmh)
    cyc["v_mps"] = np.full(n, sc.v_kmh / 3.6)
    cyc["grade"] = sc.grade * np.clip(np.arange(n) / 20.0, 0.0, 1.0)
    return cyc


def trace(plant, cyc, *, seen):
    """Every step's reward, observation and info values, neutral action, seed 0. With `seen` (a list), each step
    also appends what the ECU was given, read off the environment before the step (the MAP map_b_prev, the
    baseline's block temperature), and what the baseline's load loop then ran (its _track_torque call on pi_base,
    engine_env.py:1291-1293: rpm, iat, ect, spark, lambda, cam)."""
    env = E.SupervisoryTunerEnv(cyc, plant=plant, dt=1.0, seed=0)
    env.reset(seed=0)
    ran = []
    if seen is not None:
        track = env._track_torque

        def tracking(torque_req, rpm, iat_k, ect_k, spark, lam, boost_trim, state, *, cam_deg=None):
            if state is env.pi_base:
                ran.append(dict(rpm=rpm, iat_k=iat_k, ect_k=ect_k, spark=spark, lam=lam, cam=cam_deg))
            return track(torque_req, rpm, iat_k, ect_k, spark, lam, boost_trim, state, cam_deg=cam_deg)
        env._track_torque = tracking
    act = np.array(E.neutral_action(), dtype=np.float32)
    out = []
    while True:
        before = dict(map_kpa=env.map_b_prev, ect_k=env.thermal_base.t_block)
        n = len(ran)
        obs, r, term, trunc, info = env.step(act)
        if seen is not None:
            if len(ran) != n + 1:
                raise AssertionError(f"{len(ran) - n} baseline load-loop calls in one step")
            seen.append({**before, "ran": ran[-1]})
        out.append((r, tuple(obs.tolist()), tuple(sorted((k, v) for k, v in info.items() if k != "episode_summary"))))
        if term or trunc:
            break
    return out


def tit(plant, s, lam):
    """The model TIT at a recorded step's operating point, computed here and not by the module."""
    eng = plant.engine
    op = P.Operating(rpm=s["rpm"], map_kpa=s["map_kpa"], iat_k=s["iat_k"], ect_k=s["ect_k"], spark_btdc=s["spark"],
                     lam=lam, p_exh_kpa=P.exhaust_backpressure_kpa(s["map_kpa"], engine=eng))
    return P.run_cycle(op, engine=eng, cam_deg=s["cam"]).egt_c + 273.15


class Patch(F.Guarded):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ford = engines.get(FORD)
        cls.b58 = engines.get(B58)
        cls.cyc = short_climb(cls.ford, STEPS)
        cls.plain = trace(cls.ford, cls.cyc, seen=None)
        # the steps' TIT at the ECU's own lambda, from a context in which every step acts (a cap below them all)
        with T.capped(cls.ford, cap_k=500.0, keep_steps=True) as st:
            trace(cls.ford, cls.cyc, seen=None)
        cls.all_acting = st
        at_one = [s["tit_ecu_k"] for s in st.steps if s["lam_ecu"] == 1.0]
        cls.cap_below = float(np.median(at_one)) - 5.0
        cls.seen = []
        with T.capped(cls.ford, cap_k=cls.cap_below, keep_steps=True) as st2:
            cls.below_trace = trace(cls.ford, cls.cyc, seen=cls.seen)
        cls.below = st2

    def test_a_cap_above_every_tit_changes_no_bit(self):
        with T.capped(self.ford, cap_k=1.0e4, keep_steps=True) as st:
            got = trace(self.ford, self.cyc, seen=None)
        self.assertEqual(got, self.plain)
        self.assertEqual((st.calls, st.acted, st.passed), (STEPS - 1, 0, 0))
        self.assertTrue(math.isfinite(st.tit_max_k) and st.tit_max_k < 1.0e4)
        self.assertEqual(st.steps, [])

    def test_below_the_cap_and_least(self):
        st = self.below
        floor = self.ford.engine.ecu.lam_floor
        held = [s for s in st.steps if s["outcome"] == "held"]
        unheld = [s for s in st.steps if s["outcome"] == "unheld"]
        self.assertGreater(len(held), 0)
        self.assertGreater(len(unheld), 0)
        self.assertEqual((st.acted, st.held, st.unheld), (len(st.steps), len(held), len(unheld)))
        for s in held:
            self.assertGreater(s["tit_ecu_k"], st.cap_k)
            self.assertTrue(floor <= s["lam"] < s["lam_ecu"])
            self.assertIs(type(s["lam"]), float)
            self.assertLessEqual(tit(self.ford, s, s["lam"]), st.cap_k)
            self.assertEqual(tit(self.ford, s, s["lam"]), s["tit_k"])
            self.assertGreater(tit(self.ford, s, s["lam"] + T.LAMBDA_TOL), st.cap_k)       # the least enrichment
        worst = 0.0
        for s in unheld[:3]:
            self.assertTrue(floor <= s["lam"] <= s["lam_ecu"])
            self.assertEqual(tit(self.ford, s, s["lam"]), s["tit_k"])
            self.assertLessEqual(s["tit_k"], s["tit_ecu_k"])
            grid = [tit(self.ford, s, float(x)) for x in np.linspace(floor, s["lam_ecu"], 61)]
            self.assertTrue(all(g > st.cap_k for g in grid))                              # none holds the cap
            worst = max(worst, s["tit_k"] - min(grid))
        self.assertLessEqual(worst, UNHELD_GRID_TOL_K)
        self.assertEqual(st.unheld_hotter, 0)
        self.assertEqual(st.calls, STEPS - 1)

    def test_every_step_acts_below_every_tit(self):
        st = self.all_acting
        floor = self.ford.engine.ecu.lam_floor
        self.assertEqual((st.calls, st.acted, st.unheld), (STEPS - 1, STEPS - 1, STEPS - 1))
        self.assertEqual((st.held, st.unheld_hotter), (0, 0))
        self.assertTrue(all(floor <= s["lam"] <= s["lam_ecu"] and s["tit_k"] <= s["tit_ecu_k"] for s in st.steps))
        self.assertEqual(st.unheld_unchanged, sum(1 for s in st.steps if s["lam"] == s["lam_ecu"]))
        # the first build's fallback, the rich bound, would have run hotter than the ECU's own lambda here
        self.assertTrue(any(tit(self.ford, s, floor) > s["tit_ecu_k"] for s in st.steps[:10] + st.steps[-10:]))

    def test_the_capped_lambda_reaches_the_plant(self):
        """The review's finding F2: at every acted step, what CapStats recorded is what the environment ran -- the
        lambda and spark returned, the cam, rpm, iat and ect are the baseline load loop's arguments, the MAP is
        map_b_prev and the ect the baseline's block before the step -- and the capped trace is not the plain one.
        A patch that computed the cap and did not apply it, or held it at a wrong operating point, fails here."""
        st = self.below
        self.assertGreater(st.acted, 0)
        self.assertEqual(len(self.seen), STEPS - 1)
        for s in st.steps:
            b = self.seen[s["call"]]
            ran = b["ran"]
            self.assertEqual((ran["lam"], ran["spark"], ran["cam"]), (s["lam"], s["spark"], s["cam"]))
            self.assertEqual((ran["rpm"], ran["iat_k"], ran["ect_k"]), (s["rpm"], s["iat_k"], s["ect_k"]))
            self.assertEqual((b["map_kpa"], b["ect_k"]), (s["map_kpa"], s["ect_k"]))
            self.assertEqual(s["cam"], E.BaselineECU(self.ford.engine.ecu).cam_deg(s["rpm"], s["map_kpa"]))
        self.assertIsNotNone(st.steps[0]["cam"])
        self.assertNotEqual(self.below_trace, self.plain)

    def test_least_tit(self):
        """least_tit on known functions: a parabola's minimum inside the scan is found to LAMBDA_TOL; a function
        rising toward the rich end returns lambda_ECU itself; the result is never above any scanned point."""
        def scan(f, lam, floor):
            xs, k = [lam], 1
            while xs[-1] > floor:
                xs.append(max(lam - k * T.SCAN_STEP, floor))
                k += 1
            return [(x, f(x)) for x in xs]
        f = lambda x: (x - 0.8137) ** 2                       # noqa: E731
        x, t = T.least_tit(f, scan(f, 1.0, 0.698))
        self.assertLess(abs(x - 0.8137), T.LAMBDA_TOL)
        g = lambda x: 1.0 - x                                 # noqa: E731  coolest at the leanest
        seen = scan(g, 0.9, 0.698)
        self.assertEqual(T.least_tit(g, seen), seen[0])
        h = lambda x: x - 0.698                               # noqa: E731  coolest at the floor
        seen = scan(h, 0.9, 0.698)
        x, t = T.least_tit(h, seen)
        self.assertEqual(x, 0.698)
        for fn in (f, g, h):
            seen = scan(fn, 0.95, 0.698)
            self.assertLessEqual(T.least_tit(fn, seen)[1], min(v for _, v in seen))

    def test_the_cap_moved_moves_the_enrichment(self):
        """Mistake 12: at one operating point, a lower cap enriches more and a higher one less."""
        st = self.below
        s = next(x for x in st.steps if x["outcome"] == "held")
        args = dict(rpm=s["rpm"], map_kpa=s["map_kpa"], iat_k=s["iat_k"], ect_k=s["ect_k"], spark=s["spark"],
                    lam=s["lam_ecu"], cam=s["cam"])
        lo = T.least_enrichment(self.ford, cap_k=st.cap_k - 3.0, **args)
        mid = T.least_enrichment(self.ford, cap_k=st.cap_k, **args)
        hi = T.least_enrichment(self.ford, cap_k=st.cap_k + 3.0, **args)
        self.assertEqual(mid[0], s["lam"])
        self.assertEqual(mid[2], "held")
        self.assertLess(lo[0], mid[0])
        self.assertTrue(hi[2] == "below" or hi[0] > mid[0])

    def test_the_original_step_comes_back(self):
        orig = E.BaselineECU.__dict__["step"]
        with T.capped(self.ford, cap_k=1200.0, keep_steps=False):
            self.assertIsNot(E.BaselineECU.__dict__["step"], orig)
        self.assertIs(E.BaselineECU.__dict__["step"], orig)
        with self.assertRaises(KeyError):
            with T.capped(self.ford, cap_k=1200.0, keep_steps=False):
                raise KeyError("inside")
        self.assertIs(E.BaselineECU.__dict__["step"], orig)
        with T.capped(self.ford, cap_k=1200.0, keep_steps=False):
            with self.assertRaises(RuntimeError):
                with T.capped(self.ford, cap_k=1100.0, keep_steps=False):
                    pass
        self.assertIs(E.BaselineECU.__dict__["step"], orig)
        for bad in (float("nan"), float("inf"), -1.0, 0.0, True, "1200"):
            with self.assertRaises(ValueError):
                with T.capped(self.ford, cap_k=bad, keep_steps=False):
                    pass
            self.assertIs(E.BaselineECU.__dict__["step"], orig)

    def test_another_plant_is_unaffected(self):
        cyc = short_climb(self.b58, 30)
        plain = trace(self.b58, cyc, seen=None)
        with T.capped(self.ford, cap_k=500.0, keep_steps=True) as st:
            got = trace(self.b58, cyc, seen=None)
        self.assertEqual(got, plain)
        self.assertEqual((st.calls, st.acted, st.passed), (0, 0, 29))

    def test_a_copy_of_the_fords_ecu_is_refused(self):
        ecu = E.BaselineECU(dataclasses.replace(self.ford.engine.ecu))
        with T.capped(self.ford, cap_k=1200.0, keep_steps=False):
            with self.assertRaises(RuntimeError):
                ecu.step(3000.0, 150.0, 330.0, 363.0, False, 1.0)
        ecu.step(3000.0, 150.0, 330.0, 363.0, False, 1.0)

    def test_climb_has_its_control_and_refuses_a_context_that_capped_nothing(self):
        """The review's findings F3 and S9: climb runs the unpatched control beside the capped run, and refuses a
        context whose patch did not reach the run's ECU (as a pool worker's would not)."""
        st, run, control, acted = T.climb(self.ford, cap_k=self.cap_below, duration=20.0, dt=1.0)
        self.assertEqual(st.calls, run["steps"])
        self.assertEqual(control["steps"], run["steps"])
        self.assertEqual(acted["acted"], st.acted)
        for k in ("realised_max_k", "realised_over_cap", "t_turb_max_k", "damage_base", "fuel_base", "lam_b_median"):
            self.assertIn(k, run)
            self.assertIn(k, control)

        @contextlib.contextmanager
        def inert(plant, *, cap_k, keep_steps):
            yield T.CapStats(cap_k=cap_k, calls=0, acted=0, held=0, unheld=0, unheld_hotter=0, unheld_unchanged=0,
                             passed=0, tit_max_k=-math.inf, steps=[])
        with mock.patch.object(T, "capped", inert):
            with self.assertRaises(RuntimeError):
                T.climb(self.ford, cap_k=self.cap_below, duration=20.0, dt=1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

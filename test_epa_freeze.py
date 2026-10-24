"""test_epa_freeze.py -- the freeze side of the EPA calibration refuses what it must, and each
refusal lets the call through once its cause is removed (build step 2 of decision 24, WP3;
written 23 October 2026; docs/build_step_2/PLAN.md 5.8, WP3_INTERFACES.md 9.6).

    python -B test_epa_freeze.py        about three minutes, nearly all of it the six dumps;
                                        exit code 0 when all pass

Every test runs on synthetic inputs in a temporary git work tree: the derived file, the freeze
record and the fit outputs are written under it, never under data/ or results/ (amendment C5).
Every test runs inside test_epa_fixtures.forbid_real_data (WP3_INTERFACES.md 9.1: no EPA table,
log, contract, split.json or data-folder file), and inside FreezeGuard, this file's stricter hook,
which also fails a test that opens anything else under data/engines/ -- the real derived files --
or under results/EPA_CALIBRATION/ and results/EPA_VALIDATION/, the real records. The plant is a
CANDIDATE (engines.build_candidate) of the registered EPA plant mazda_25t built from the B58's own
values of every field the EPA set derives: a plant no EPA row touched, which is all a test of the
freeze needs. Nothing is fitted.

  AtomicWrite   write_json_atomic writes through common.write_json (spied on: rule N6 lets only
                epa_freeze.py call it), refuses a NaN before writing, and an interruption (an
                exception, a KeyboardInterrupt) leaves the old file or none and no partial file.
                Control: the same interruption under a writer in place leaves a half-written file,
                so the interruption is real
  GuardControl  FreezeGuard refuses an open of the real derived file and freeze record, and not
                of the same names in a temporary root: the guard itself can fail (mistake 12)
  Paths         the derived file is the spec's and derived.engine_path's, the freeze record the
                spec's; a spec or a derived.py that names another is refused, and passes restored;
                the B58's file, an unknown name and a missing root are refused
  DerivedFile   the layout is engines.EPA_DERIVED_FIELDS', each refusal (a NumPy value -- amendment
                B10 --, an int for a float, a bool for cam_on, a NaN, a missing or unknown key, no
                bookkeeping) shown and shown to pass with its cause removed; the record's hashes are
                sha_text and fingerprint.derived_sha; a frozen section is rewritten only on the
                defect route, whose fix commit must exist and be an ancestor of HEAD, and only once
                the old freeze.json has moved to defect_<k>/; derived.py's cached copy is dropped
                on every write (control: without that the cache hands back the old values)
  Freeze        freeze.json's frozen_sections_sha256 is engines.frozen_sections_sha256's (control:
                with engines' function replaced, the record follows it, so it is not a copy); a
                second freeze is refused until the run moves to defect_<k>/; a frozen section edited
                after the freeze is refused by engines._check_freeze and by check_frozen, a
                completion section is not; every refusal of freeze_record and write_freeze shown
                and shown to pass with its cause removed; tree_record, the tree-side hashes the
                held-out token is checked against, is the tree as it is, and moves with one byte
  Git          the git helpers on a temporary repository: HEAD, a blob at HEAD with core.autocrlf,
                the index blob read without opening the file, the dirty list, ancestry; the code
                record and its changes
  Provenance    the data block and the provenance block (section 7.1's keys) with epa_rows stood in
                for by a stub: the tables' guard runs before any hash, epa_channels.csv is never
                opened, and no wall-clock value enters
  Dump          the frozen-plant dump is the same in another process, moves with one ulp of one
                constant (the control), reads no file, evaluates a form-D candidate with its cam,
                and the Honda's CVT car over the same keys
  Scans         no step-2 module but epa_freeze.py calls common.write_json or common.write_text, or
                names the derived file (so nothing else can write it); each scan flags a scratch
                source that breaks it
"""
import ast
import contextlib
import copy
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
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

import derived  # noqa: E402
import engines  # noqa: E402
import epa_freeze  # noqa: E402
import fingerprint  # noqa: E402
import test_epa_fixtures as fixtures  # noqa: E402
from thresholds import common  # noqa: E402

ENGINE = "mazda_25t"          # a registered EPA plant: its specs are real, its derived values synthetic
PY = sys.executable


# ------------------------------------------------------------------ the guard against real data
class FreezeGuard:
    """An audit hook, installed once, that while a test runs refuses -- and records -- an open of
    anything under the real repository's data/engines/ (the derived files beside the tables),
    logs/, results/EPA_CALIBRATION/, results/EPA_VALIDATION/, the contract's two files and
    results/ENGINE_THRESHOLDS/, or the team's data folder: test_epa_fixtures.forbid_real_data's set
    and the freeze's own outputs. The violation is recorded as well as raised, since some callers
    catch OSError (fingerprint.derived_sha returns None for one), and tearDown fails the test on any
    record. A hook cannot be removed once added, so it is armed and disarmed by a flag; a test adds
    a path of its own to `roots` to show that a file is never opened."""
    armed = False
    seen = []
    _installed = False
    _contract = os.path.join(common.REPO, "results", "ENGINE_THRESHOLDS")        # .json, .md and the folder
    roots = tuple(os.path.normcase(os.path.abspath(p)) for p in (
        os.path.join(common.REPO, "data", "engines"), os.path.join(common.REPO, "logs"),
        os.path.join(common.REPO, "results", "EPA_CALIBRATION"),
        os.path.join(common.REPO, "results", "EPA_VALIDATION"), common.DATA_FOLDER))
    prefixes = (os.path.normcase(os.path.abspath(_contract)),)

    @classmethod
    def install(cls):
        if not cls._installed:
            sys.addaudithook(cls._hook)
            cls._installed = True

    @classmethod
    def _hook(cls, event, args):
        if not cls.armed or event != "open" or not args or isinstance(args[0], int):
            return
        try:
            p = os.path.normcase(os.path.abspath(os.fsdecode(args[0])))
        except (TypeError, ValueError):
            return
        hit = any(p == r or p.startswith(r + os.sep) for r in cls.roots) or any(p.startswith(x) for x in cls.prefixes)
        if hit:
            cls.seen.append(p)
            raise PermissionError(f"test_epa_freeze opened real data: {p}")


FreezeGuard.install()


class Guarded(unittest.TestCase):
    def setUp(self):
        self.enterContext(fixtures.forbid_real_data())
        FreezeGuard.seen.clear()
        FreezeGuard.armed = True

    def tearDown(self):
        FreezeGuard.armed = False
        self.assertEqual(FreezeGuard.seen, [], "a test opened real data")


# ------------------------------------------------------------------ fixtures
def _b58_values():
    """The B58 plant's own value of every field engines.EPA_DERIVED_FIELDS names, shaped like an
    EPA derived file: test_epa_fixtures.b58_values (the shared definition, mistake 10), with the
    B58's own deliverable-torque table as [rpm, Nm] lists where the fixture leaves it empty, since
    the dump runs the car's demand, which reads the table. Synthetic for any EPA engine: no EPA row
    set them."""
    vals = fixtures.b58_values()
    vals["deliverable_torque"] = [list(p) for p in engines.get("b58").car.deliverable_torque]
    return json.loads(json.dumps(vals))


def _frozen(values):
    return {s: copy.deepcopy(values[s]) for s in engines.FROZEN_SECTIONS}


def _next_ulp(x):
    return float(np.nextafter(x, np.inf))


@dataclasses.dataclass(frozen=True)
class Fit:
    """What epa_freeze reads of an epa_fit.FormFit: its engine, form, values, stored hash and flags."""
    engine: str
    form: str
    values: dict
    frozen_sections_sha256: str
    flags: tuple = ()


def _fit(values):
    v = _frozen(values)
    return Fit(engine=ENGINE, form=v["cycle"]["form"], values=v, frozen_sections_sha256=engines.frozen_sections_sha256(v))


GIT_ENV = {"GIT_AUTHOR_NAME": "wp3 test", "GIT_AUTHOR_EMAIL": "wp3@example.invalid",
           "GIT_COMMITTER_NAME": "wp3 test", "GIT_COMMITTER_EMAIL": "wp3@example.invalid",
           "GIT_AUTHOR_DATE": "2026-10-23T12:00:00+03:00", "GIT_COMMITTER_DATE": "2026-10-23T12:00:00+03:00"}


def git(root, *args, check=True):
    out = subprocess.run(["git", "-c", "core.safecrlf=false", *args], cwd=root, capture_output=True, text=True,
                         env=dict(os.environ, **GIT_ENV))
    if check and out.returncode != 0:
        raise RuntimeError(f"git {args}: {out.stderr}")
    return out.stdout.strip()


def write(root, rel, text, *, newline="\n"):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline=newline) as fh:
        fh.write(text)
    return p


def make_repo(tmp):
    """A git work tree holding a synthetic file for each of epa_freeze.CODE_HASHED, committed."""
    root = os.path.join(tmp, "repo")
    os.makedirs(root)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "core.autocrlf", "true")      # this repository's setting (fingerprint._sha_files)
    for rel in epa_freeze.CODE_HASHED:
        write(root, rel, f"# a synthetic {rel}: test_epa_freeze.py's work tree\n")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "the code")
    return root


def provenance_for(root):
    """A provenance block (WP3_INTERFACES.md 7.1) for `root`: HEAD, the code and plant_sha as the
    freeze recomputes them, the contract and data hashes synthetic."""
    return {"engine": ENGINE,
            "contract": {"commit": "c" * 40, "json_sha_text": "1" * 64, "md_sha_text": "2" * 64, "schema": 4},
            "git": {"head": epa_freeze.git_head(root=root), "step2_clean": True, "dirty": []},
            "code_sha_text": epa_freeze.code_shas(root=root),
            "plant_sha": epa_freeze.plant_sha(ENGINE),
            "data": {"tables_sha256": {"t_one.csv": "3" * 64}, "epa_engine_sha256": "4" * 64,
                     "epa_channels_blob": "5" * 40, "manifest_sha256": "6" * 64},
            "view_sha256": "7" * 64,
            "versions": epa_freeze.versions()}


def fit_outputs(root, ladder):
    """stage0.json, in_sample.json and fit_<form>.json for every form of `ladder`, synthetic."""
    folder = epa_freeze.calibration_dir(ENGINE, root=root)
    names = ["stage0.json", "in_sample.json"] + [f"fit_{f.form}.json" for f in ladder.fits]
    files = {}
    for n in names:
        files[n] = os.path.join(folder, n)
        epa_freeze.write_json_atomic(files[n], {"schema": "synthetic", "name": n})
    return files


def frozen_run(root, values):
    """A synthetic run up to the freeze record (not written): (fit, ladder, provenance, files, record)."""
    fit = _fit(values)
    ladder = types.SimpleNamespace(fits=(fit,), chosen=fit.form)
    prov = provenance_for(root)
    epa_freeze.write_derived(ENGINE, epa_freeze.derived_values(fit, provenance=prov), allow_defect=None, root=root)
    files = fit_outputs(root, ladder)
    record = epa_freeze.freeze_record(ENGINE, fit=fit, ladder=ladder, files=files, provenance=prov, root=root)
    return fit, ladder, prov, files, record


def dump_json(path, obj):
    """A hand edit of a file, as a person would make one: not through epa_freeze."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1)


# ------------------------------------------------------------------ the tests
class AtomicWrite(Guarded):
    def test_the_form_is_common_write_jsons(self):
        """The bytes are common.write_json's: write_json_atomic hands the object to that function
        (spied on, not called here: rule N6 lets no file but epa_freeze.py call it), with the
        partial file as its path, and the bytes are json.dumps' indent-1 ASCII form with LF."""
        obj = {"b": [1.0, 0.1, 1e-300], "a": {"x": None, "y": "é"}, "n": 3}
        with tempfile.TemporaryDirectory() as tmp:
            b = os.path.join(tmp, "sub", "b.json")
            with mock.patch.object(common, "write_json", wraps=common.write_json) as spy:
                sha = epa_freeze.write_json_atomic(b, obj)
            self.assertEqual(spy.call_count, 1)
            self.assertEqual(spy.call_args.args, (b + epa_freeze.PARTIAL_SUFFIX, obj))
            with open(b, "rb") as fb:
                self.assertEqual(fb.read(), json.dumps(obj, indent=1, ensure_ascii=True).encode("ascii"))
            self.assertEqual(sha, common.sha_text(b))
            self.assertEqual(os.listdir(os.path.dirname(b)), ["b.json"])

    def test_a_nan_is_refused_before_anything_is_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "x.json")
            for bad in (float("nan"), float("inf"), -math.inf):
                with self.subTest(value=bad), self.assertRaises(ValueError):
                    epa_freeze.write_json_atomic(p, {"v": [1.0, bad]})
                self.assertEqual(os.listdir(tmp), [])
            epa_freeze.write_json_atomic(p, {"v": None})          # the absent value is a None
            self.assertEqual(common.load_json(p), {"v": None})

    def test_an_interruption_leaves_the_old_file_or_none_and_no_partial(self):
        real_dump = json.dump

        def half(obj, fh, **kw):
            buf = io.StringIO()
            real_dump(obj, buf, **kw)
            fh.write(buf.getvalue()[: len(buf.getvalue()) // 2])
            fh.flush()
            raise interrupt("interrupted mid-write")

        for interrupt in (RuntimeError, KeyboardInterrupt):
            with self.subTest(interrupt=interrupt.__name__), tempfile.TemporaryDirectory() as tmp:
                p = os.path.join(tmp, "out.json")
                with mock.patch.object(common.json, "dump", side_effect=half), self.assertRaises(interrupt):
                    epa_freeze.write_json_atomic(p, {"k": list(range(50))})
                self.assertEqual(os.listdir(tmp), [], "a first write that is interrupted leaves no file")
                epa_freeze.write_json_atomic(p, {"old": True})
                with open(p, "rb") as fh:
                    old = fh.read()
                with mock.patch.object(common.json, "dump", side_effect=half), self.assertRaises(interrupt):
                    epa_freeze.write_json_atomic(p, {"k": list(range(50))})
                with open(p, "rb") as fh:
                    self.assertEqual(fh.read(), old, "an interrupted rewrite leaves the old file")
                self.assertEqual(os.listdir(tmp), ["out.json"], "and no partial file")
                # the control: the same interruption under a writer in place (common.write_json's
                # body, without the partial file and the replace) leaves half a file
                with mock.patch.object(common.json, "dump", side_effect=half), self.assertRaises(interrupt):
                    with open(p, "w", encoding="utf-8", newline="\n") as fh:
                        json.dump({"k": list(range(50))}, fh, indent=1, ensure_ascii=True)
                with open(p, "rb") as fh:
                    torn = fh.read()
                self.assertNotEqual(torn, old)
                with self.assertRaises(ValueError):
                    json.loads(torn.decode("utf-8"))

    def test_a_partial_file_left_by_a_killed_process_is_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "out.json")
            with open(p + epa_freeze.PARTIAL_SUFFIX, "w") as fh:
                fh.write("{\"torn")
            epa_freeze.write_json_atomic(p, {"ok": 1})
            self.assertEqual(sorted(os.listdir(tmp)), ["out.json"])
            self.assertEqual(common.load_json(p), {"ok": 1})


class GuardControl(Guarded):
    def test_the_guard_refuses_the_real_derived_file_and_freeze_record(self):
        """FreezeGuard can fail (mistake 12): an open of the real derived file and of the real freeze
        record is refused inside the open and recorded -- neither exists yet, and the refusal comes
        before the file system is asked -- while the same names in a temporary root are not."""
        for p in (derived.engine_path(ENGINE), epa_freeze.freeze_path(ENGINE, root=common.REPO)):
            with self.subTest(path=os.path.relpath(p, common.REPO)), self.assertRaises(PermissionError):
                open(p, encoding="utf-8")
        self.assertEqual(len(FreezeGuard.seen), 2)
        FreezeGuard.seen.clear()
        with tempfile.TemporaryDirectory() as tmp:
            for p in (epa_freeze.derived_path(ENGINE, root=tmp), epa_freeze.freeze_path(ENGINE, root=tmp)):
                with self.assertRaises(FileNotFoundError):
                    open(p, encoding="utf-8")
        self.assertEqual(FreezeGuard.seen, [])


class Paths(Guarded):
    def test_the_files_are_the_specs_and_derived_pys(self):
        with tempfile.TemporaryDirectory() as tmp:
            want = os.path.relpath(derived.engine_path(ENGINE), derived.HERE).replace(os.sep, "/")
            self.assertEqual(epa_freeze.derived_relpath(ENGINE), want)
            self.assertEqual(engines.read_spec(engines.PLANTS[ENGINE][0])["_meta"]["derived"], want)
            self.assertEqual(epa_freeze.derived_path(ENGINE, root=tmp), os.path.join(os.path.abspath(tmp), *want.split("/")))
            self.assertEqual(epa_freeze.freeze_relpath(ENGINE), f"results/EPA_CALIBRATION/{ENGINE}/freeze.json")
            for name in ("mazda_25t", "honda_l15b7", "ford_27tt"):
                with self.subTest(engine=name):
                    epa_freeze.derived_relpath(name)
                    epa_freeze.freeze_relpath(name)

    def test_a_derived_path_other_than_the_specs_is_refused(self):
        """WP3_INTERFACES.md 9.6: a derived path different from the spec's. Two ways: derived.py
        names another file, or the spec does. Each refused; restored, each passes."""
        other = os.path.relpath(derived.engine_path(ENGINE + "_other"), derived.HERE).replace(os.sep, "/")
        real_path = derived.engine_path
        with mock.patch.object(derived, "engine_path", side_effect=lambda eid: real_path(eid + "_other")):
            with self.assertRaises(epa_freeze.DerivedPathMismatch):
                epa_freeze.derived_relpath(ENGINE)
        epa_freeze.derived_relpath(ENGINE)
        real = engines.read_spec

        def spec(field, value):
            def read(n):
                s = copy.deepcopy(real(n))
                if n == engines.PLANTS[ENGINE][0]:
                    s["_meta"][field] = value
                return s
            return read

        for field, value, fn in (("derived", other, epa_freeze.derived_relpath),
                                 ("freeze", "results/EPA_CALIBRATION/elsewhere/freeze.json", epa_freeze.freeze_relpath)):
            with self.subTest(field=field):
                with mock.patch.object(engines, "read_spec", side_effect=spec(field, value)):
                    with self.assertRaises(epa_freeze.DerivedPathMismatch):
                        fn(ENGINE)
                fn(ENGINE)

    def test_the_b58_an_unknown_name_and_a_missing_root_are_refused(self):
        with self.assertRaisesRegex(epa_freeze.DerivedPathMismatch, "derived_set is 'b58'"):
            epa_freeze.derived_relpath("b58")      # derive_params.py's file, from the car's logs
        for bad in (None, "b59"):
            with self.subTest(name=bad), self.assertRaises(KeyError):
                epa_freeze.derived_relpath(bad)
        with tempfile.TemporaryDirectory() as tmp:
            epa_freeze.derived_path(ENGINE, root=tmp)
            for bad in (None, os.path.join(tmp, "absent")):
                with self.subTest(root=bad), self.assertRaises(TypeError):
                    epa_freeze.derived_path(ENGINE, root=bad)


class DerivedFile(Guarded):
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp()
        self.root = make_repo(self.tmp)
        self.values = _b58_values()
        self.prov = provenance_for(self.root)
        self.dv = epa_freeze.derived_values(_fit(self.values), provenance=self.prov)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        super().tearDown()

    def test_the_layout_is_engines_epa_derived_fields(self):
        self.assertEqual({s: len(k) for s, k in epa_freeze.SECTION_KEYS.items()},
                         {"cycle": 20, "ecu": 26, "boost_ceiling": 3, "k3": 1, "loop": 1, "deliverable_torque": 0})
        self.assertEqual(set(self.dv), set(engines.FROZEN_SECTIONS) | set(epa_freeze.BOOKKEEPING_KEYS))
        self.assertEqual(self.dv["_inputs"]["freeze_record"], epa_freeze.freeze_relpath(ENGINE))
        self.assertEqual(engines.frozen_sections_sha256(self.dv), engines.frozen_sections_sha256(self.values))
        # the file a fit freezes builds the plant engines.build_candidate builds (mistake 10), once completed
        full = epa_freeze.with_completion(self.dv, deliverable_torque=self.values["deliverable_torque"],
                                          turb_knee_k=1123.0, torque_floor_nm=0.0)
        engines.build_candidate(ENGINE, full)

    def test_each_refusal_and_its_removal(self):
        """Every refusal of write_derived, each with nothing written, and the same values with the
        cause removed written (mistake 12): a NumPy value (amendment B10), an int for a float, a
        bool for cam_on, a NaN, an unknown key in a section, a missing frozen section, an unknown
        top-level key (a timestamp among them), the bookkeeping missing, a freeze_record path that
        is not the spec's."""
        path = epa_freeze.derived_path(ENGINE, root=self.root)

        def mutated(fn):
            v = copy.deepcopy(self.dv)
            fn(v)
            return v

        cases = [
            ("numpy float64", TypeError, lambda v: v["cycle"].__setitem__("burn_base", np.float64(v["cycle"]["burn_base"]))),
            ("numpy float32", TypeError, lambda v: v["ecu"].__setitem__("spark_a", np.float32(v["ecu"]["spark_a"]))),
            ("numpy in a list", TypeError, lambda v: v["boost_ceiling"]["envelope_pr"].__setitem__(1, np.float64(1.1))),
            ("numpy int", TypeError, lambda v: v["ecu"].__setitem__("cam_on", np.int64(0))),
            ("an int for a float", TypeError, lambda v: v["ecu"].__setitem__("enr_load", 180)),
            ("a bool for cam_on", TypeError, lambda v: v["ecu"].__setitem__("cam_on", False)),
            ("a NaN", ValueError, lambda v: v["cycle"].__setitem__("knock_a", float("nan"))),
            ("an unknown key", ValueError, lambda v: v["cycle"].__setitem__("ve_extra", 1.0)),
            ("a missing key", ValueError, lambda v: v["ecu"].pop("kl_d")),
            ("a missing section", ValueError, lambda v: v.pop("boost_ceiling")),
            ("a timestamp", ValueError, lambda v: v.__setitem__("_written_utc", "2026-10-23")),
            ("an unknown section", ValueError, lambda v: v.__setitem__("thermal", {})),
            ("no bookkeeping", ValueError, lambda v: v.pop("_inputs")),
            ("another freeze record", ValueError,
             lambda v: v["_inputs"].__setitem__("freeze_record", "results/EPA_CALIBRATION/x/freeze.json")),
        ]
        for label, exc, fn in cases:
            with self.subTest(refusal=label):
                with self.assertRaises(exc):
                    epa_freeze.write_derived(ENGINE, mutated(fn), allow_defect=None, root=self.root)
                self.assertFalse(os.path.exists(path), "a refused write writes nothing")
        # the cause removed: NumPy values converted with float() before, as B10 asks, pass
        v = mutated(lambda v: v["cycle"].__setitem__("burn_base", float(np.float64(v["cycle"]["burn_base"]))))
        rec = epa_freeze.write_derived(ENGINE, v, allow_defect=None, root=self.root)
        self.assertEqual(rec.path, epa_freeze.derived_relpath(ENGINE))
        with self.assertRaises(TypeError):     # the record's builder refuses a NumPy value too
            engines.build_candidate(ENGINE, mutated(lambda v: v["cycle"].__setitem__("burn_base", np.float64(1.0))))

    def test_the_record_is_sha_text_and_derived_sha(self):
        rec = epa_freeze.write_derived(ENGINE, self.dv, allow_defect=None, root=self.root)
        path = epa_freeze.derived_path(ENGINE, root=self.root)
        self.assertEqual(rec.sha_text, common.sha_text(path))
        self.assertEqual(rec.derived_sha, fingerprint.derived_sha(path))
        self.assertEqual(rec, epa_freeze.derived_record(path, root=self.root))
        self.assertEqual(rec, epa_freeze.derived_record(rec.path, root=self.root), "a relative path is the root's")
        # the bookkeeping moves sha_text and not derived_sha; a value moves both
        about = epa_freeze.write_derived(ENGINE, dict(self.dv, _about="another text"), allow_defect=None,
                                         root=self.root)
        self.assertNotEqual(about.sha_text, rec.sha_text)
        self.assertEqual(about.derived_sha, rec.derived_sha)
        done = epa_freeze.with_completion(self.dv, deliverable_torque=self.values["deliverable_torque"],
                                          turb_knee_k=1123.0, torque_floor_nm=0.0)
        moved = epa_freeze.write_derived(ENGINE, done, allow_defect=None, root=self.root)
        self.assertNotEqual(moved.derived_sha, rec.derived_sha)

    def test_a_frozen_section_is_rewritten_only_on_the_defect_route(self):
        root, path = self.root, epa_freeze.derived_path(ENGINE, root=self.root)
        epa_freeze.write_derived(ENGINE, self.dv, allow_defect=None, root=root)
        done = epa_freeze.with_completion(self.dv, deliverable_torque=self.values["deliverable_torque"],
                                          turb_knee_k=1123.0, torque_floor_nm=0.0)
        epa_freeze.write_derived(ENGINE, done, allow_defect=None, root=root)     # completion: no route needed
        moved = copy.deepcopy(done)
        moved["cycle"]["burn_base"] = _next_ulp(moved["cycle"]["burn_base"])
        with self.assertRaises(epa_freeze.FrozenSectionsChanged):
            epa_freeze.write_derived(ENGINE, moved, allow_defect=None, root=root)
        self.assertEqual(common.load_json(path), done, "the refused write left the file")
        # the route's authority: a commit that is not one, one off HEAD's history, a bare True
        write(root, "fix.txt", "the fix\n")
        git(root, "add", "fix.txt")
        git(root, "commit", "-q", "-m", "the fix")
        fix = git(root, "rev-parse", "HEAD")
        git(root, "checkout", "-q", "-b", "side")
        write(root, "side.txt", "elsewhere\n")
        git(root, "add", "side.txt")
        git(root, "commit", "-q", "-m", "not on main")
        side = git(root, "rev-parse", "HEAD")
        git(root, "checkout", "-q", "main")
        for label, route, exc in (("no such commit", epa_freeze.DefectRoute("a defect", "0" * 40), epa_freeze.GitError),
                                  ("an abbreviated sha", epa_freeze.DefectRoute("a defect", fix[:12]), epa_freeze.GitError),
                                  ("not an ancestor of HEAD", epa_freeze.DefectRoute("a defect", side), epa_freeze.GitError),
                                  ("no reason", epa_freeze.DefectRoute(" ", fix), ValueError),
                                  ("a bare True", True, TypeError)):
            with self.subTest(route=label), self.assertRaises(exc):
                epa_freeze.write_derived(ENGINE, moved, allow_defect=route, root=root)
        # a freeze record still in place refuses even the route; moved to defect_1/, the route passes
        fz = epa_freeze.freeze_path(ENGINE, root=root)
        epa_freeze.write_json_atomic(fz, {"frozen_sections_sha256": engines.frozen_sections_sha256(done)})
        route = epa_freeze.DefectRoute("S3c asserted a tie", fix)
        with self.assertRaises(epa_freeze.FrozenSectionsChanged):
            epa_freeze.write_derived(ENGINE, moved, allow_defect=route, root=root)
        os.makedirs(os.path.join(os.path.dirname(fz), "defect_1"))
        os.replace(fz, os.path.join(os.path.dirname(fz), "defect_1", "freeze.json"))
        epa_freeze.write_derived(ENGINE, moved, allow_defect=route, root=root)
        self.assertEqual(common.load_json(path), moved)

    def test_every_write_drops_derived_pys_cached_copy(self):
        path = epa_freeze.derived_path(ENGINE, root=self.root)
        epa_freeze.write_derived(ENGINE, self.dv, allow_defect=None, root=self.root)
        self.assertNotIn("k3", derived.all_params(path=path))         # read, and now cached
        done = epa_freeze.with_completion(self.dv, deliverable_torque=self.values["deliverable_torque"],
                                          turb_knee_k=1100.0, torque_floor_nm=0.0)
        # the control: a write that is not epa_freeze's leaves the cached copy, the old values
        dump_json(path, done)
        self.assertNotIn("k3", derived.all_params(path=path))
        epa_freeze.write_derived(ENGINE, done, allow_defect=None, root=self.root)
        self.assertEqual(derived.all_params(path=path)["k3"], {"turb_knee_k": 1100.0})


class Freeze(Guarded):
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp()
        self.root = make_repo(self.tmp)
        self.values = _b58_values()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        super().tearDown()

    def test_the_record_holds_engines_hash_never_a_copy(self):
        fit, ladder, prov, files, record = frozen_run(self.root, self.values)
        self.assertEqual(sorted(record), sorted(epa_freeze.FREEZE_KEYS))
        self.assertEqual(record["frozen_sections_sha256"], engines.frozen_sections_sha256(fit.values))
        self.assertEqual(record["derived"], epa_freeze.derived_record(
            epa_freeze.derived_path(ENGINE, root=self.root), root=self.root).as_json())
        self.assertEqual(record["fits"], {b: common.sha_text(files[b]) for b in sorted(files)})
        self.assertEqual(record["git_head"], prov["git"]["head"])
        # the control: with engines' function replaced, the record follows it -- it calls engines'
        fake = "f" * 64
        with mock.patch.object(engines, "frozen_sections_sha256", return_value=fake):
            fit2 = dataclasses.replace(fit, frozen_sections_sha256=fake)
            rec2 = epa_freeze.freeze_record(ENGINE, fit=fit2, ladder=types.SimpleNamespace(fits=(fit2,), chosen="A"),
                                            files=files, provenance=prov, root=self.root)
        self.assertEqual(rec2["frozen_sections_sha256"], fake)

    def test_a_second_freeze_is_refused_until_the_run_moves_to_defect(self):
        _fit_, _ladder, _prov, _files, record = frozen_run(self.root, self.values)
        sha = epa_freeze.write_freeze(ENGINE, record, root=self.root)
        fz = epa_freeze.freeze_path(ENGINE, root=self.root)
        self.assertEqual(sha, common.sha_text(fz))
        self.assertEqual(common.load_json(fz), record)
        with self.assertRaises(epa_freeze.AlreadyFrozen):
            epa_freeze.write_freeze(ENGINE, record, root=self.root)
        folder = epa_freeze.calibration_dir(ENGINE, root=self.root)
        os.makedirs(os.path.join(folder, "defect_1"))
        os.replace(fz, os.path.join(folder, "defect_1", "freeze.json"))
        epa_freeze.write_freeze(ENGINE, record, root=self.root)

    def test_a_frozen_section_edited_after_the_freeze_is_refused(self):
        """PLAN.md 5.8 and amendment F7, both checks: engines._check_freeze (what engines._build runs
        before building an EPA plant from its file) and check_frozen (the completion's). One ulp on
        one frozen constant, edited in the file by hand, is refused by both; restored, both pass; a
        completion section edited is not frozen, and passes."""
        _f, _l, _p, _fs, record = frozen_run(self.root, self.values)
        epa_freeze.write_freeze(ENGINE, record, root=self.root)
        path = epa_freeze.derived_path(ENGINE, root=self.root)
        good = common.load_json(path)
        epa_freeze.check_derived_file(ENGINE, root=self.root)
        epa_freeze.check_frozen(ENGINE, good, root=self.root)
        for sec, key in (("cycle", "burn_base"), ("ecu", "enr_depth"), ("boost_ceiling", "pr_cap")):
            with self.subTest(constant=f"{sec}.{key}"):
                edited = copy.deepcopy(good)
                edited[sec][key] = _next_ulp(edited[sec][key])
                dump_json(path, edited)
                with self.assertRaises(ValueError):
                    epa_freeze.check_derived_file(ENGINE, root=self.root)
                with self.assertRaises(epa_freeze.FrozenSectionsChanged):
                    epa_freeze.check_frozen(ENGINE, edited, root=self.root)
                dump_json(path, good)
                epa_freeze.check_derived_file(ENGINE, root=self.root)
                epa_freeze.check_frozen(ENGINE, good, root=self.root)
        later = epa_freeze.with_completion(good, deliverable_torque=self.values["deliverable_torque"],
                                           turb_knee_k=1100.0, torque_floor_nm=12.5)
        epa_freeze.write_derived(ENGINE, later, allow_defect=None, root=self.root)
        epa_freeze.check_derived_file(ENGINE, root=self.root)
        epa_freeze.check_frozen(ENGINE, later, root=self.root)
        os.remove(epa_freeze.freeze_path(ENGINE, root=self.root))
        with self.assertRaises(FileNotFoundError):
            epa_freeze.check_frozen(ENGINE, later, root=self.root)
        with self.assertRaises(FileNotFoundError):
            epa_freeze.check_derived_file(ENGINE, root=self.root)

    def test_each_refusal_of_the_record_and_its_removal(self):
        fit, ladder, prov, files, record = frozen_run(self.root, self.values)
        root = self.root

        def call(**kw):
            args = dict(fit=fit, ladder=ladder, files=files, provenance=prov)
            args.update(kw)
            return epa_freeze.freeze_record(ENGINE, root=root, **args)

        other = dataclasses.replace(fit, form="A+B")
        cases = [
            ("not the ladder's choice", ValueError, dict(ladder=types.SimpleNamespace(fits=(fit, other), chosen="A+B"))),
            ("another engine's fit", ValueError, dict(fit=dataclasses.replace(fit, engine="ford_27tt"))),
            ("a stored hash that is not engines'", epa_freeze.FrozenSectionsChanged,
             dict(fit=dataclasses.replace(fit, frozen_sections_sha256="0" * 64),
                  ladder=types.SimpleNamespace(fits=(dataclasses.replace(fit, frozen_sections_sha256="0" * 64),),
                                               chosen="A"))),
            ("dirty code at the start", epa_freeze.FreezeRefusal,
             dict(provenance=dict(prov, git=dict(prov["git"], step2_clean=False, dirty=["epa_fit.py"])))),
            ("a file list that is not the ladder's", ValueError, dict(files={k: files[k] for k in list(files)[:-1]})),
            ("a file outside the engine's folder", ValueError,
             dict(files=dict(files, **{"stage0.json": os.path.join(root, "stage0.json")}))),
            ("the code changed during the fit", epa_freeze.FreezeRefusal,
             dict(provenance=dict(prov, code_sha_text=dict(prov["code_sha_text"], **{"epa_fit.py": "9" * 64})))),
            ("the plant changed during the fit", epa_freeze.FreezeRefusal, dict(provenance=dict(prov, plant_sha="0" * 16))),
            ("HEAD moved during the fit", epa_freeze.FreezeRefusal,
             dict(provenance=dict(prov, git=dict(prov["git"], head="0" * 40)))),
        ]
        for label, exc, kw in cases:
            with self.subTest(refusal=label), self.assertRaises(exc):
                call(**kw)
        self.assertEqual(call(), record, "with every cause removed the record is the same")
        # a derived file whose frozen sections are not the fit's (or none)
        path = epa_freeze.derived_path(ENGINE, root=root)
        good = common.load_json(path)
        moved = copy.deepcopy(good)
        moved["ecu"]["kl_a"] = _next_ulp(moved["ecu"]["kl_a"])
        dump_json(path, moved)
        with self.assertRaises(epa_freeze.FrozenSectionsChanged):
            call()
        os.remove(path)
        with self.assertRaises(FileNotFoundError):
            call()
        dump_json(path, good)
        self.assertEqual(call()["frozen_sections_sha256"], record["frozen_sections_sha256"])

    def test_the_tree_record_is_what_the_tree_holds(self):
        """tree_record, the tree side ARMED.json and the held-out token compare (validate_epa.py uses
        it for both, mistake 10): each entry is the file's hash in `root` as it is now, None for a
        file not there yet, and a one-byte change to any of them moves it (the control)."""
        _f, _l, _p, _fs, record = frozen_run(self.root, self.values)
        epa_freeze.write_freeze(ENGINE, record, root=self.root)
        for rel in engines.spec_files(ENGINE):
            dst = os.path.join(self.root, *rel.split("/"))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(os.path.join(HERE, *rel.split("/")), dst)
        t = epa_freeze.tree_record(ENGINE, root=self.root)
        fz = epa_freeze.freeze_path(ENGINE, root=self.root)
        self.assertEqual(sorted(t), ["code", "complete", "derived", "freeze", "specs"])
        self.assertEqual(t["freeze"], {"path": epa_freeze.freeze_relpath(ENGINE), "sha_text": common.sha_text(fz)})
        self.assertEqual(t["complete"], {"path": f"results/EPA_CALIBRATION/{ENGINE}/complete.json", "sha_text": None})
        self.assertEqual(t["derived"], record["derived"])
        self.assertEqual(t["specs"], {r: common.sha_text(os.path.join(HERE, *r.split("/")))
                                      for r in engines.spec_files(ENGINE)})
        self.assertEqual(t["code"], epa_freeze.code_shas(root=self.root))
        spec = os.path.join(self.root, *engines.spec_files(ENGINE)[0].split("/"))
        with open(spec, "ab") as fh:
            fh.write(b"#")
        write(self.root, "epa_stats.py", "# changed\n")
        epa_freeze.write_json_atomic(os.path.join(os.path.dirname(fz), "complete.json"), {"done": True})
        t2 = epa_freeze.tree_record(ENGINE, root=self.root)
        self.assertNotEqual(t2["specs"], t["specs"])
        self.assertNotEqual(t2["code"]["epa_stats.py"], t["code"]["epa_stats.py"])
        self.assertIsNotNone(t2["complete"]["sha_text"])
        self.assertEqual((t2["freeze"], t2["derived"]), (t["freeze"], t["derived"]))

    def test_write_freeze_refuses_a_record_of_another_file(self):
        _f, _l, _p, _fs, record = frozen_run(self.root, self.values)
        for label, bad in (("another frozen hash", dict(record, frozen_sections_sha256="0" * 64)),
                           ("another derived record", dict(record, derived=dict(record["derived"], sha_text="0" * 64))),
                           ("a missing key", {k: v for k, v in record.items() if k != "versions"}),
                           ("another schema", dict(record, schema="epa-freeze/0"))):
            with self.subTest(refusal=label), self.assertRaises((epa_freeze.FreezeRefusal, ValueError)):
                epa_freeze.write_freeze(ENGINE, bad, root=self.root)
            self.assertFalse(os.path.exists(epa_freeze.freeze_path(ENGINE, root=self.root)))
        epa_freeze.write_freeze(ENGINE, record, root=self.root)


class DefectRouteRecords(Guarded):
    """The defect route's file work, which calibrate_epa.py leaves here (WP3's integration, 23 October 2026;
    WP3_INTERFACES.md 5.5.2: "a coding defect moves the whole engine folder's outputs, verbatim, to
    defect_<k>/ and appends to defects.json"), and the readers calibrate_epa uses since it opens nothing."""

    def test_the_run_moves_verbatim_and_defects_json_grows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp)
            folder = epa_freeze.calibration_dir(ENGINE, root=root)
            with self.assertRaises(epa_freeze.FreezeRefusal):               # no run to move
                epa_freeze.move_run_to_defect(ENGINE, root=root)
            a = write(root, f"{epa_freeze.CALIBRATION_DIR}/{ENGINE}/STARTED", "{}\n")
            write(root, f"{epa_freeze.CALIBRATION_DIR}/{ENGINE}/e6/row1.json", '{"x": 1}\r\n', newline="")
            before = {"STARTED": open(a, "rb").read(), "row1": open(os.path.join(folder, "e6", "row1.json"), "rb").read()}
            self.assertEqual(epa_freeze.move_run_to_defect(ENGINE, root=root), 1)
            self.assertEqual(sorted(os.listdir(folder)), ["defect_1"])
            with open(os.path.join(folder, "defect_1", "STARTED"), "rb") as fh:
                self.assertEqual(fh.read(), before["STARTED"])
            with open(os.path.join(folder, "defect_1", "e6", "row1.json"), "rb") as fh:
                self.assertEqual(fh.read(), before["row1"])               # byte for byte, CRLF kept
            fix = git(root, "rev-parse", "HEAD")
            entry = {"k": 1, "run_invocation": 1, "found_by": "synthetic", "assertion": "synthetic",
                     "fix_commit": fix, "previous_run": "defect_1/"}
            self.assertEqual(epa_freeze.append_defect(ENGINE, entry, root=root), [entry])
            write(root, f"{epa_freeze.CALIBRATION_DIR}/{ENGINE}/STARTED", "{}\n")
            self.assertEqual(epa_freeze.move_run_to_defect(ENGINE, root=root), 2)   # defects.json stays
            self.assertEqual(sorted(os.listdir(folder)), ["defect_1", "defect_2", epa_freeze.DEFECTS])
            self.assertEqual(len(epa_freeze.append_defect(ENGINE, dict(entry, k=2, previous_run="defect_2/"),
                                                          root=root)), 2)
            # the controls: an entry with a key missing, one with a wall-clock date (PLAN.md 5.1: run.json holds
            # the time; the entry names its invocation), and a fix that is no commit, are refused
            with self.assertRaises(ValueError):
                epa_freeze.append_defect(ENGINE, {k: v for k, v in entry.items() if k != "run_invocation"}, root=root)
            with self.assertRaises(ValueError):
                epa_freeze.append_defect(ENGINE, dict(entry, date="2026-10-23"), root=root)
            with self.assertRaises(epa_freeze.GitError):
                epa_freeze.append_defect(ENGINE, dict(entry, fix_commit="0" * 40), root=root)
            with self.assertRaises(epa_freeze.GitError):
                epa_freeze.check_defect(epa_freeze.DefectRoute(reason="r", fix_commit="0" * 40), root=root)
            self.assertIsNone(epa_freeze.check_defect(None, root=root))

    def test_the_calibration_folder_is_epa_rows_too(self):
        """epa_rows, which cannot import this module, holds the same folder for its held-out counts' guard."""
        import epa_rows
        self.assertEqual(epa_freeze.CALIBRATION_DIR, epa_rows.CALIBRATION_REL)

    def test_run1s_record_checks(self):
        """poison_problems, t0_problems and audit_problems, the one definition calibrate_epa's later steps and
        validate_epa's arming read (WP3's fix of 23 October 2026): each passes its good record and names each
        fault of a bad one."""
        import epa_rows
        poisons = tuple(epa_rows.POISONS)
        import epa_fit
        stages = {k: True for k in epa_fit.poison_run_stages()}
        stages["S3d"] = None
        run = {"copies_are_not_the_tables": True, "stage0_equal": True, "view_equal": True, "yield_equal": True,
               "manifest_equal": True, "engine_facts_equal": True, "stages": stages,
               "full_form_a": {"frozen_sections_sha256_equal": True}}
        good = {"schema": epa_freeze.POISON_SCHEMA, "runs": {h: json.loads(json.dumps(run)) for h in poisons},
                "frozen_sections_sha256": "f" * 64, "form": "A",
                "reference_equals_fit": {k: True for k in epa_fit.poison_tied_stages("A")},
                "garbled_contract_view_equal": True, "garbled_contract_yield_equal": True, "all_equal": True}

        def f(rec, **kw):
            return epa_freeze.poison_problems(rec, run_keys=epa_fit.POISON_RUN_KEYS, stages=epa_fit.poison_run_stages(),
                                              tied_of=epa_fit.poison_tied_stages, **kw)
        self.assertEqual(f(good, engine="mazda_25t", frozen_sections_sha256="f" * 64, poisons=poisons), [])
        bad = json.loads(json.dumps(good))
        bad["runs"]["low"]["stages"]["S1"] = False
        self.assertTrue(f(bad, engine="ford_27tt", frozen_sections_sha256="f" * 64, poisons=poisons))
        self.assertTrue(f(good, engine="ford_27tt", frozen_sections_sha256="e" * 64, poisons=poisons))
        no_full = json.loads(json.dumps(good))
        for h in poisons:
            no_full["runs"][h]["full_form_a"] = None
        self.assertEqual(f(no_full, engine="ford_27tt", frozen_sections_sha256="f" * 64, poisons=poisons), [])
        self.assertTrue(f(no_full, engine=epa_freeze.FULL_POISON_ENGINE, frozen_sections_sha256="f" * 64,
                          poisons=poisons))
        self.assertTrue(f(dict(good, runs={"low": run}), engine="ford_27tt", frozen_sections_sha256="f" * 64,
                          poisons=poisons))
        self.assertTrue(f(dict(good, reference_equals_fit=dict(good["reference_equals_fit"], S1=False)),
                          engine="ford_27tt", frozen_sections_sha256="f" * 64, poisons=poisons))
        # the key sets are exact (WP3's second fix of 23 October 2026, on the isolation review's finding): a run
        # without a stage, a run without a comparison, a reference without a tied stage, each refused although
        # every leaf left is true; and S3d is tied under form D
        for cut in (("runs", "low", "stages", "S2"), ("runs", "high", "view_equal"), ("reference_equals_fit", "S3b")):
            bad = json.loads(json.dumps(good))
            d = bad
            for k in cut[:-1]:
                d = d[k]
            del d[cut[-1]]
            self.assertTrue(f(bad, engine="ford_27tt", frozen_sections_sha256="f" * 64, poisons=poisons), cut)
        d_form = dict(good, form="A+B+C+D")
        self.assertTrue(f(d_form, engine="ford_27tt", frozen_sections_sha256="f" * 64, poisons=poisons))
        d_form = dict(d_form, reference_equals_fit=dict(good["reference_equals_fit"], S3d=True))
        self.assertEqual(f(d_form, engine="ford_27tt", frozen_sections_sha256="f" * 64, poisons=poisons), [])
        self.assertEqual(epa_freeze.t0_problems({"schema": epa_freeze.T0_SCHEMA, "pass": True}), [])
        self.assertTrue(epa_freeze.t0_problems({"schema": epa_freeze.T0_SCHEMA, "pass": False}))
        self.assertTrue(epa_freeze.t0_problems({}))
        ok = {"k": 1, "subcommand": "fit", "outcome": "ok", "outside_allowlist": [], "refused_by_audit": []}
        a = epa_freeze.audit_problems
        subs = epa_freeze.AUDITED_SUBCOMMANDS
        self.assertEqual(a({"invocations": [ok, dict(ok, k=2, outcome="refused: x")]}, subcommands=subs), [])
        for badinv in (dict(ok, outcome="crash: KeyError"), dict(ok, outcome="defect: opened"),
                       dict(ok, outcome="mismatch: x"), dict(ok, outside_allowlist=["notes.txt"]),
                       dict(ok, outcome="refused: y", refused_by_audit=["logs/x"])):
            self.assertEqual(len(a({"invocations": [ok, dict(badinv, k=2)]}, subcommands=subs)), 1, badinv)
        self.assertEqual(a({"invocations": [dict(ok, subcommand="dry-load", outcome="crash: X")]}, subcommands=subs), [])

    def test_the_held_out_run_is_seen_on_the_disk_and_in_git_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp)
            rel = "results/EPA_VALIDATION"
            self.assertEqual(epa_freeze.held_out_started(ENGINE, root=root, validation_rel=rel), [])
            write(root, f"{rel}/{ENGINE}/ARMED.json", "{}\n")
            self.assertEqual(epa_freeze.held_out_started(ENGINE, root=root, validation_rel=rel), [])    # ARMED alone
            write(root, f"{rel}/{ENGINE}/STARTED", "{}\n")
            self.assertTrue(epa_freeze.held_out_started(ENGINE, root=root, validation_rel=rel))
            git(root, "add", "-A")
            git(root, "commit", "-q", "-m", "the run's STARTED")
            os.remove(os.path.join(root, *rel.split("/"), ENGINE, "STARTED"))
            got = epa_freeze.held_out_started(ENGINE, root=root, validation_rel=rel)
            self.assertTrue(got and "git log --all" in got[0], got)

    def test_held_out_started_reads_the_run_once_markers(self):
        """The run-once markers (WP3's second fix of 23 October 2026): a started marker in the work tree's git
        directory holds every refit although the folder and git log are clean (a `git clean` of the run's
        records), and held_out_started passes once it is removed (the control); a marker of another engine is
        not this one's."""
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp)
            rel = "results/EPA_VALIDATION"
            self.assertEqual(epa_freeze.held_out_started(ENGINE, root=root, validation_rel=rel), [])
            blob = "a" * 40
            path = epa_freeze.run_marker_path("started", ENGINE, blob, root=root)
            self.assertEqual(os.path.dirname(os.path.normcase(path)), epa_freeze.git_dirs(root=root)[0])
            epa_freeze.write_json_atomic(path, {"engine": ENGINE})
            got = epa_freeze.held_out_started(ENGINE, root=root, validation_rel=rel)
            self.assertTrue(got and "git directory" in got[-1], got)
            self.assertEqual(epa_freeze.run_markers(ENGINE, root=root), [os.path.basename(path)])
            self.assertEqual(epa_freeze.held_out_started("ford_27tt", root=root, validation_rel=rel), [])
            os.remove(path)
            self.assertEqual(epa_freeze.held_out_started(ENGINE, root=root, validation_rel=rel), [])
            with self.assertRaises(ValueError):
                epa_freeze.run_marker_path("begun", ENGINE, blob, root=root)
            with self.assertRaises(ValueError):
                epa_freeze.run_marker_path("started", ENGINE, "not a blob", root=root)

    def test_the_defect_entry_layout_t0s_code_and_the_versions(self):
        """defect_entry_problems is append_defect's layout (the arming reads it too); t0_code_problems refuses a
        code or plant other than the one T0 ran on; version_problems compares the lock file's pins and the
        run's earlier record. Each with its control."""
        good = {"k": 1, "run_invocation": 2, "found_by": "t", "assertion": "a", "fix_commit": "f" * 40,
                "previous_run": "defect_1/"}
        self.assertEqual(epa_freeze.defect_entry_problems(good), [])
        self.assertTrue(epa_freeze.defect_entry_problems({k: v for k, v in good.items() if k != "run_invocation"}))
        self.assertTrue(epa_freeze.defect_entry_problems(dict(good, date="2026-10-23")))
        self.assertTrue(epa_freeze.defect_entry_problems(dict(good, k=0)))
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp)
            rec = {"provenance": provenance_for(root)}
            self.assertEqual(epa_freeze.t0_code_problems(rec, name=ENGINE, root=root), [])
            write(root, epa_freeze.CODE_HASHED[0], "# edited after T0\n")
            self.assertTrue(epa_freeze.t0_code_problems(rec, name=ENGINE, root=root))
            self.assertTrue(epa_freeze.t0_code_problems({}, name=ENGINE, root=root))
        now = epa_freeze.versions()
        self.assertEqual(epa_freeze.version_problems(None), [])
        self.assertEqual(epa_freeze.version_problems(now), [])
        self.assertTrue(epa_freeze.version_problems(dict(now, scipy="0.0.0")))
        # the machine too (WP3's fourth fix of 24 October 2026): another platform string than the earlier record's
        self.assertTrue(any("platform" in x for x in epa_freeze.version_problems(dict(now, platform="Other-1.0"))))
        pins = epa_freeze.lock_pins()
        with mock.patch.object(epa_freeze, "lock_pins", lambda: dict(pins, numpy="0.0.0")):
            self.assertTrue(epa_freeze.version_problems(None))

    def test_the_readers_stay_inside_the_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp)
            rel = f"{epa_freeze.CALIBRATION_DIR}/{ENGINE}/x.json"
            p = write(root, rel, '{"a": [1, 2.5]}\n')
            self.assertEqual(epa_freeze.read_json(rel, root=root), {"a": [1, 2.5]})
            self.assertEqual(epa_freeze.read_json(p, root=root), {"a": [1, 2.5]})
            # only a calibration record, a derived file or a top-level run.json (WP3's second fix of 23 October
            # 2026, on the isolation review's finding that read_json read the contract): the controls, the
            # contract's path, a JSON elsewhere under results/, another tree's calibration folder name
            # (the contract's and the tables' names built from parts: rules N1 and N3 confine the literals)
            for other in ("results/ENGINE_THRESHOLDS" + ".json", "results/x.json", "results/EPA_VALIDATION/x/ARMED.json",
                          f"{epa_freeze.CALIBRATION_DIR}/not_an_engine/x.json", "data" + f"/engines/{ENGINE}/epa_engine.json"):
                write(root, other, "{}\n")
                with self.assertRaises(ValueError):
                    epa_freeze.read_json(other, root=root)
            write(root, "run.json", '{"engine": "x", "invocations": []}\n')
            self.assertEqual(epa_freeze.read_json("run.json", root=root)["invocations"], [])
            dp = epa_freeze.derived_relpath(ENGINE)
            write(root, dp, "{}\n")
            self.assertEqual(epa_freeze.read_json(dp, root=root), {})
            from thresholds import common
            self.assertEqual(epa_freeze.file_sha_text(p, root=root), common.sha_text(p))
            outside = os.path.join(tmp, "outside.json")
            with open(outside, "w", encoding="utf-8") as fh:
                fh.write("{}\n")
            with self.assertRaises(ValueError):
                epa_freeze.read_json(outside, root=root)
            with self.assertRaises(ValueError):
                epa_freeze.file_sha_text(outside, root=root)


class Git(Guarded):
    def test_the_helpers_on_a_temporary_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp)
            head = git(root, "rev-parse", "HEAD")
            self.assertEqual(epa_freeze.git_head(root=root), head)
            # a CRLF working copy of an LF blob is committed (core.autocrlf), one byte is not
            p = write(root, "results/r.json", "{\n \"a\": 1\n}\n", newline="\r\n")
            git(root, "-c", "core.autocrlf=true", "add", "results/r.json")
            git(root, "commit", "-q", "-m", "r")
            with open(p, "rb") as fh:
                crlf = fh.read()
            self.assertIn(b"\r\n", crlf)
            self.assertTrue(epa_freeze.committed_at_head(p, root=root))
            self.assertTrue(epa_freeze.committed_at_head("results/r.json", root=root))
            self.assertEqual(epa_freeze.blob_sha256("HEAD", "results/r.json", root=root),
                             hashlib.sha256(crlf.replace(b"\r\n", b"\n")).hexdigest())
            self.assertEqual(epa_freeze.blob_sha256("HEAD", "results/r.json", root=root), common.sha_text(p))
            with open(p, "wb") as fh:
                fh.write(crlf.replace(b"1", b"2"))
            self.assertFalse(epa_freeze.committed_at_head(p, root=root))
            self.assertEqual(epa_freeze.git_clean(["results/r.json", "epa_fit.py"], root=root),
                             (False, ("results/r.json",)))
            with open(p, "wb") as fh:
                fh.write(crlf)
            self.assertTrue(epa_freeze.committed_at_head(p, root=root))
            self.assertEqual(epa_freeze.git_clean(["results/r.json"], root=root), (True, ()))
            u = write(root, "results/untracked.json", "{}\n")
            self.assertFalse(epa_freeze.committed_at_head(u, root=root))
            self.assertEqual(epa_freeze.git_clean(["results"], root=root), (False, ("results/untracked.json",)))
            os.remove(u)
            # a staged rename makes both paths dirty: the old one is gone, the new one is not committed
            git(root, "mv", "k3_knee.py", "k3_moved.py")
            self.assertEqual(epa_freeze.git_clean(["k3_knee.py", "k3_moved.py", "epa_fit.py"], root=root),
                             (False, ("k3_knee.py", "k3_moved.py")))
            git(root, "mv", "k3_moved.py", "k3_knee.py")
            self.assertEqual(epa_freeze.git_clean(["k3_knee.py", "k3_moved.py"], root=root), (True, ()))
            # the index blob, without opening the file; refused for an edited or an untracked file
            c = write(root, "eng/x/channels.csv", "name,unit\n")
            git(root, "add", "eng/x/channels.csv")
            git(root, "commit", "-q", "-m", "channels")
            blob = git(root, "hash-object", "eng/x/channels.csv")
            FreezeGuard.roots += (os.path.normcase(os.path.abspath(c)),)
            try:
                self.assertEqual(epa_freeze.git_blob(c, root=root), blob)
            finally:
                FreezeGuard.roots = FreezeGuard.roots[:-1]
            with open(c, "a", encoding="utf-8") as fh:
                fh.write("extra,1\n")
            with self.assertRaises(epa_freeze.GitError):
                epa_freeze.git_blob(c, root=root)
            with self.assertRaises(epa_freeze.GitError):
                epa_freeze.git_blob(write(root, "eng/x/new.csv", "a\n"), root=root)
            with self.assertRaises(ValueError):
                epa_freeze.git_blob(os.path.join(tmp, "outside.csv"), root=root)
            # ancestry
            self.assertTrue(epa_freeze.is_ancestor(head, "HEAD", root=root))
            self.assertFalse(epa_freeze.is_ancestor("HEAD", head, root=root))
            self.assertIsNone(epa_freeze.head_blob("results/absent.json", root=root))

    def test_the_code_record_and_its_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp)
            code = epa_freeze.code_shas(root=root)
            self.assertEqual(tuple(code), epa_freeze.CODE_HASHED)
            self.assertEqual(epa_freeze.code_changes(code, root=root), ())
            write(root, "epa_stats.py", "# a synthetic epa_stats.py: changed\n")
            self.assertEqual(epa_freeze.code_changes(code, root=root), ("epa_stats.py",))
            self.assertEqual(epa_freeze.code_changes({k: v for k, v in code.items() if k != "d3_rows.py"}, root=root),
                             ("d3_rows.py", "epa_stats.py"))
            os.remove(os.path.join(root, "k3_knee.py"))
            with self.assertRaises(FileNotFoundError):
                epa_freeze.code_shas(root=root)
        self.assertEqual(len(epa_freeze.STEP2_CODE), 9)
        self.assertEqual(len(epa_freeze.STEP2_TESTS), 12)
        self.assertEqual(epa_freeze.CODE_HASHED[9:11], ("thresholds/split.py", "thresholds/common.py"))
        # the Run 1 inputs outside the code and the plant (WP3's fourth fix of 24 October 2026, on the fourth Run 1
        # review's finding): evaluate.py, the B58's engine spec as engines names it, the environment's pins
        self.assertEqual(epa_freeze.CODE_HASHED[11:], epa_freeze.RUN1_INPUTS)
        self.assertEqual(epa_freeze.RUN1_INPUTS, ("evaluate.py", engines.spec_files("b58")[0], epa_freeze.LOCK_FILE))
        self.assertEqual(len(epa_freeze.CODE_HASHED), 14)

    def test_plant_sha_is_the_fingerprints(self):
        for name in ("b58", ENGINE):
            with self.subTest(plant=name):
                self.assertEqual(epa_freeze.plant_sha(name), fingerprint._sha_files(fingerprint.plant_files(name)))
        self.assertEqual(epa_freeze.plant_sha("b58"), fingerprint.plant_fingerprint(
            plant=engines.get("b58"), backend=fingerprint.BACKEND_CYCLE)["plant_sha"])


def stub_rows(root, engine, *, refuse):
    """A stand-in for epa_rows (another group's module, written at the same time): its TABLES, its
    table guard, its contract check and its manifest, over synthetic files in `root`. `refuse`
    makes the table guard stop, as a table that is not the contract's would."""
    calls = []
    spec = types.SimpleNamespace(engine=engine, name="t_one.csv", role="steady", index=0)

    def check_tables(name, *, source):
        calls.append(("check_tables", name))
        if refuse:
            raise RuntimeError("a table is not the contract's")
        return (spec,)

    def check_contract(*, source):
        calls.append(("check_contract",))
        return types.SimpleNamespace(commit="a" * 40, json_sha_text="b" * 64, md_sha_text="c" * 64, schema=4,
                                     generators={})

    def manifest(name, *, source):
        calls.append(("manifest", name))
        return types.SimpleNamespace(sha256="d" * 64)

    mod = types.ModuleType("epa_rows")
    mod.TABLES = {engine: (spec,)}
    mod.check_tables, mod.check_contract, mod.manifest = check_tables, check_contract, manifest
    # the loader's path helpers, as epa_rows defines them (epa_freeze joins no path under the source's tables
    # folder itself since WP3's second fix of 23 October 2026)
    mod.table_path = lambda spec_, *, source: os.path.join(source.engine_dir, spec_.engine, spec_.name)
    mod.engine_file_path = lambda eng, basename, *, source: os.path.join(source.engine_dir, eng, basename)
    source = types.SimpleNamespace(root=root, engine_dir=os.path.join(root, "eng"), allow_poisoned_tables=False)
    return mod, source, calls


class Provenance(Guarded):
    def _tree(self, tmp):
        root = make_repo(tmp)
        folder = os.path.join(root, "eng", ENGINE)
        files = {"t_one.csv": "a,b\r\n1,2\r\n", "epa_engine.json": "{}\n", "epa_channels.csv": "name,unit\n"}
        for n, text in files.items():
            write(root, f"eng/{ENGINE}/{n}", text, newline="")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "synthetic tables")
        return root, folder

    def test_the_data_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, folder = self._tree(tmp)
            mod, source, calls = stub_rows(root, ENGINE, refuse=False)
            channels = os.path.normcase(os.path.abspath(os.path.join(folder, "epa_channels.csv")))
            FreezeGuard.roots += (channels,)          # opening it fails the test: it is never opened
            try:
                with mock.patch.dict(sys.modules, {"epa_rows": mod}):
                    data = epa_freeze.data_shas(ENGINE, source=source)
            finally:
                FreezeGuard.roots = FreezeGuard.roots[:-1]
            self.assertEqual(calls[0], ("check_tables", ENGINE), "the tables' guard runs before any hash")
            self.assertEqual(data, {"tables_sha256": {"t_one.csv": common.sha_raw(os.path.join(folder, "t_one.csv"))},
                                    "epa_engine_sha256": common.sha_raw(os.path.join(folder, "epa_engine.json")),
                                    "epa_channels_blob": git(root, "hash-object", f"eng/{ENGINE}/epa_channels.csv"),
                                    "manifest_sha256": "d" * 64})
            # the control: the raw hash keeps the table's CRLF, which sha_text would not
            self.assertNotEqual(data["tables_sha256"]["t_one.csv"], common.sha_text(os.path.join(folder, "t_one.csv")))
            mod, source, calls = stub_rows(root, ENGINE, refuse=True)
            saved = FreezeGuard.roots         # a refused guard opens no file of the folder: an open fails here
            FreezeGuard.roots += (os.path.normcase(os.path.abspath(folder)),)
            try:
                with mock.patch.dict(sys.modules, {"epa_rows": mod}), self.assertRaises(RuntimeError):
                    epa_freeze.data_shas(ENGINE, source=source)
            finally:
                FreezeGuard.roots = saved
            self.assertEqual(calls, [("check_tables", ENGINE)], "a refused guard hashes nothing")

    def test_the_provenance_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _folder = self._tree(tmp)
            mod, source, _calls = stub_rows(root, ENGINE, refuse=False)
            view = types.SimpleNamespace(engine=ENGINE, sha256="e" * 64)
            with mock.patch.dict(sys.modules, {"epa_rows": mod}):
                a = epa_freeze.provenance(ENGINE, source=source, view=view)
                b = epa_freeze.provenance(ENGINE, source=source, view=view)
                with self.assertRaises(ValueError):
                    epa_freeze.provenance(ENGINE, source=source, view=types.SimpleNamespace(engine="ford_27tt", sha256=""))
            self.assertEqual(tuple(a), epa_freeze.PROVENANCE_KEYS)
            self.assertEqual(a, b, "no wall-clock value: two calls give one block")
            self.assertEqual(a["git"], {"head": git(root, "rev-parse", "HEAD"), "step2_clean": True, "dirty": []})
            self.assertEqual(a["contract"], {"commit": "a" * 40, "json_sha_text": "b" * 64, "md_sha_text": "c" * 64,
                                             "schema": 4})
            self.assertEqual(sorted(a["versions"]), ["numpy", "platform", "python", "scipy"])
            write(root, "epa_fit.py", "# changed\n")
            with mock.patch.dict(sys.modules, {"epa_rows": mod}):
                c = epa_freeze.provenance(ENGINE, source=source, view=view)
            self.assertEqual(c["git"]["dirty"], ["epa_fit.py"])
            self.assertFalse(c["git"]["step2_clean"])


DUMP_IN_A_PROCESS = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
import engines, epa_freeze
with open(sys.argv[2], encoding="utf-8") as fh:
    values = json.load(fh)
print(epa_freeze.frozen_plant_dump(engines.build_candidate(sys.argv[3], values)).sha256)
"""


def expected_dump_size(plant):
    """How many values the dump of `plant` holds, counted from the grids it is defined on: a
    second count of what _dump_arrays evaluates, so a key dropped or a grid narrowed is seen."""
    F = epa_freeze
    n_map = len(F._dump_map_grid(plant))
    n_lam = len({max(F.DUMP_LAM_FLOOR_CAP, plant.engine.ecu.lam_floor), *F.DUMP_LAM})
    n_cyc = F.DUMP_N_RPM * n_map * len(F.DUMP_SPARK_BTDC) * n_lam * len(F.DUMP_IMT_K)
    n_ecu = F.DUMP_N_RPM * len(F.DUMP_ECU_MAP_KPA)
    n_veh = len(F.DUMP_V_MPS) * len(F.DUMP_ACCEL) * len(F.DUMP_GRADE) * len(F.DUMP_RHO)
    road = len(F.DUMP_V_MPS) * len(F.DUMP_GRADE) * len(F.DUMP_RHO) if type(plant.car) is not engines.Car else 0
    steps = sum(n for n, _ in F.DUMP_THERMAL)
    return (F.DUMP_N_RPM + n_map + n_lam + 16 * n_cyc + len(F.DUMP_ECU_MAP_KPA)
            + n_ecu * (2 + len(F.DUMP_DWELL_S) + plant.engine.ecu.cam_on) + len(F.DUMP_IAT_K)
            + len(F.DUMP_T_INLET_K) * len(F.DUMP_FLOW_GPS) + len(F.DUMP_T_AMB_K) * len(F.DUMP_T_BLOCK_K)
            + road + 2 * n_veh + 3 * (steps + 1))


class Dump(Guarded):
    @classmethod
    def setUpClass(cls):
        cls.values = _b58_values()
        cls.plant = engines.build_candidate(ENGINE, copy.deepcopy(cls.values))

    def test_reproducible_in_another_process_and_moved_by_one_ulp(self):
        opened = []

        def record(event, args):
            if FreezeGuard.armed and event == "open" and args and not isinstance(args[0], int):
                opened.append(os.fsdecode(args[0]))

        sys.addaudithook(record)      # stays installed; records only while a test is armed
        n0 = len(opened)
        d = epa_freeze.frozen_plant_dump(self.plant)
        py = tuple(os.path.normcase(os.path.abspath(x)) for x in (sys.base_prefix, sys.prefix))
        reads = [p for p in opened[n0:] if not os.path.normcase(os.path.abspath(p)).startswith(py)]
        self.assertEqual(reads, [], "the dump reads no file: synthetic inputs and the plant only")
        self.assertEqual(len(d.keys), len(set(d.keys)))
        self.assertEqual(d.n_values, expected_dump_size(self.plant))
        with tempfile.TemporaryDirectory() as tmp:
            vp = os.path.join(tmp, "values.json")
            with open(vp, "w", encoding="utf-8") as fh:
                json.dump(self.values, fh)
            env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
            out = subprocess.run([PY, "-B", "-c", DUMP_IN_A_PROCESS, HERE, vp, ENGINE], capture_output=True,
                                 text=True, env=env, timeout=600)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.strip(), d.sha256, "another process gives the same dump")
        self.assertIn("run_cycle.knock_prob", d.keys)
        self.assertIn("vehicle.road_force_n", d.keys)
        self.assertIn("thermal.state", d.keys)
        self.assertNotIn("ecu.cam_deg", d.keys)     # form A: the ECU runs no cam
        # the control: one ulp on one frozen constant moves the dump
        moved = copy.deepcopy(self.values)
        moved["cycle"]["burn_base"] = _next_ulp(moved["cycle"]["burn_base"])
        d2 = epa_freeze.frozen_plant_dump(engines.build_candidate(ENGINE, moved))
        self.assertNotEqual(d2.sha256, d.sha256)
        self.assertEqual((d2.n_values, d2.keys), (d.n_values, d.keys))
        self.assertEqual(d.as_json(), {"sha256": d.sha256, "n_values": d.n_values, "keys": list(d.keys)})

    def test_a_form_d_candidate_is_dumped_with_its_cam(self):
        v = copy.deepcopy(self.values)
        v["cycle"].update(form="A+B+C+D", ve_map=1.0e-3, ve_cam=1.0e-3)
        v["ecu"].update(cam_on=1, cam_c0=10.0, cam_c_rpm=2.0, cam_c_map=-3.0, cam_rpm_lo=1300.0, cam_rpm_hi=5000.0,
                        cam_map_lo=30.0, cam_map_hi=220.0, cam_lo=0.0, cam_hi=40.0)
        d = epa_freeze.frozen_plant_dump(engines.build_candidate(ENGINE, v))
        self.assertIn("ecu.cam_deg", d.keys)
        self.assertEqual(d.keys.index("ecu.cam_deg"), d.keys.index("ecu.iat_compensation") + 1)

    def test_the_cvt_car_is_dumped_too(self):
        """The Accord's CVT (decision 40) answers demand through its own record: the Honda candidate,
        built from the same synthetic values, is dumped over the same keys, every value counted."""
        p = engines.build_candidate("honda_l15b7", copy.deepcopy(self.values))
        self.assertIsNot(type(p.car), type(self.plant.car))
        d = epa_freeze.frozen_plant_dump(p)
        self.assertEqual(d.n_values, expected_dump_size(p))
        self.assertEqual(d.keys, epa_freeze.frozen_plant_dump(self.plant).keys)

    def test_the_map_grid_is_clipped_at_the_plants_envelope(self):
        b = self.plant.engine.boost
        top = b.inlet_sea_kpa * min(max(b.envelope_pr), b.pr_cap)
        self.assertEqual(epa_freeze._dump_map_grid(self.plant), tuple(m for m in epa_freeze.DUMP_MAP_KPA if m <= top))
        low = dataclasses.replace(self.plant, engine=dataclasses.replace(
            self.plant.engine, boost=dataclasses.replace(b, pr_cap=1.5)))
        self.assertEqual(epa_freeze._dump_map_grid(low), (30.0, 60.0, 100.0, 140.0, b.inlet_sea_kpa * 1.5))


class Scans(Guarded):
    """The derived file is written only through epa_freeze (PLAN.md 5.8; WP3_INTERFACES.md 3.2 N6):
    no other step-2 module calls common.write_json or common.write_text, and none names the derived
    file, so none can build its path to write it. Modules not written yet are skipped by name."""
    WRITERS = {("common", "write_json"), ("common", "write_text")}
    NAME = "derived_" + "params"

    def scan(self, src, rel):
        """(file, line, what) for each call of a common writer, each import of one, and each string
        that names the derived file as a path (no whitespace: a sentence in a message or a docstring
        that mentions the file is not one)."""
        tree = ast.parse(src, filename=rel)
        docs = {id(n.body[0].value) for n in ast.walk(tree)
                if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.body
                and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}
        hits = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and \
                    isinstance(node.func.value, ast.Name) and (node.func.value.id, node.func.attr) in self.WRITERS:
                hits.append((rel, node.lineno, f"{node.func.value.id}.{node.func.attr}"))
            elif isinstance(node, ast.ImportFrom) and node.module == "thresholds.common" and \
                    any(a.name in ("write_json", "write_text") for a in node.names):
                hits.append((rel, node.lineno, "imports a common writer"))
            elif isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs and \
                    self.NAME in node.value and not any(c.isspace() for c in node.value):
                hits.append((rel, node.lineno, "names the derived file as a path"))
        return hits

    def test_no_other_step2_module_writes_the_derived_file(self):
        found, absent = [], []
        for rel in epa_freeze.STEP2_CODE:
            if rel == "epa_freeze.py":
                continue
            p = os.path.join(HERE, rel)
            if not os.path.exists(p):
                absent.append(rel)
                continue
            with open(p, encoding="utf-8") as fh:
                found += self.scan(fh.read(), rel)
        self.assertEqual(found, [])
        if absent:
            print(f"\n  Scans: not written yet, so not scanned: {', '.join(absent)}", file=sys.stderr)

    def test_the_scan_can_fail(self):
        for src in ("from thresholds import common\ncommon.write_json(p, v)\n",
                    "from thresholds import common\ncommon.write_text(p, 'x')\n",
                    "from thresholds.common import write_json\n",
                    "p = 'data/" + "engines/x/" + self.NAME + ".json'\n",
                    "open(" + repr(self.NAME + ".json") + ", 'w')\n"):
            with self.subTest(src=src):
                self.assertNotEqual(self.scan(src, "probe.py"), [])
        self.assertEqual(self.scan('"""Writes ' + self.NAME + '.json through epa_freeze."""\n'
                                   "raise ValueError('the file " + self.NAME + ".json is frozen')\n"
                                   "epa_freeze.write_derived(n, v, allow_defect=None, root=r)\n", "probe.py"), [],
                         "a docstring or a sentence naming the file is not a path to write")
        with open(os.path.join(HERE, "epa_freeze.py"), encoding="utf-8") as fh:
            self.assertNotEqual(self.scan(fh.read(), "epa_freeze.py"), [], "epa_freeze itself is the writer")


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""test_validate_guards.py -- the held-out validation's run-once guards, in temporary git repositories
(build step 2 of decision 24, WP3; written 23 October 2026).

    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -B test_validate_guards.py     exit code 0 when all pass

WHAT IT PROVES (docs/build_step_2/WP3_INTERFACES.md 9.9; amendments C5, C6, C10, C11, E5; decision 60).
Every test runs in a temporary git repository that test_epa_fixtures.make_repo builds: synthetic
tables for the three engines, a synthetic contract whose held-out structure is the generator's own
split, the step-2 code copied from this tree. On top of it this file writes synthetic calibration
records (freeze.json, complete.json, fit_A.json, ...), a synthetic derived file and the roads step's
tightenings, so that validate_epa.arm can arm the engine for real; only the steps that need a
calibrated plant (engines.get, the dump) are given synthetic answers, and the generator's split is
the fixture's split_of run on the same synthetic tables. For the guards, the held-out computation is
replaced by a stand-in (FakeCompute) that reads the held-out rows through epa_rows.read_held_out and
returns fixed records. HeldOutRun runs the real computation once end to end, on the Ford's synthetic
held-out rows, with a frozen candidate built from the B58's values and a toy model in the place of
RowModel (PlantToy): what it tests is the assembly -- every row, every E6 row, section 7, the hashes,
the allowlist -- never a statistic's value, which is epa_stats' and test_epa_stats.py's.

  * epa_rows.read_held_out refuses without ARMED.json committed at HEAD whatever token it is given,
    refuses a forged token, and yields only with the token verify_for_validation issues (C5);
  * run refuses in a linked worktree, without .git, outside the armed path, with any other file in
    the output folder (tracked, untracked, ignored), with another path of the folder in
    `git log --all`, with dirty validation code, and before ARMED.json is committed; each refusal
    passes once its cause is removed (C6);
  * STARTED exists when the first held-out row is read; a crash writes crash_<k>.txt, prints only the
    exception's type and blocks re-execution; a run whose STARTED is its only record runs again; the
    defect route needs the fix after the arming and a re-arming, writes *_rerun<k>.json beside the
    first outputs, and caps every label at limited (decision 60; section 7);
  * arm refuses tightenings of another plant than the B58 (E5, decision 71), a code change since the
    first fit without its defects.json entry (C10), a re-arming on the normal route, a frozen-plant
    dump or an in-sample check that does not come back, D3 files that do not hash to the manifest
    (decision 63); its held-out counts equal a hand count of the synthetic tables (decision 54);
  * a calibration record the run reads (stage0.json, the refit variants) that is not the one freeze.json
    or complete.json hashes is refused by arm and by run (C5: matching hashes);
  * a refused run is logged outside the folder, so the folder still holds ARMED.json alone;
  * the run's opened files are inside its allowlist, and one outside makes it exit non-zero (C3);
  * the whole run: every gating row labelled with its u-terms, every E6 row assembled in the same run,
    each probe reaching the rows its constant reaches and no other, section 7 and the C5 margin written,
    ARMED.json's hashes in every output, counts and paths printed only, the same rows from a second copy;
    a retag that is not the plant stops the run (HANDOFFS.md WP3 item 3);
  * neither this file nor validate_epa.py passes the real ENGINE_DIR or contract (C5's AST check).

Each check is shown able to fail (mistake 12): a control beside it trips it. Nothing here opens a real
EPA table, the real contract or the data folder: every class runs inside
test_epa_fixtures.forbid_real_data.
"""
import ast
import contextlib
import csv
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
import warnings
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import d3_rows  # noqa: E402
import epa_fit  # noqa: E402
import epa_freeze  # noqa: E402
import epa_rows  # noqa: E402
import epa_stats  # noqa: E402
import test_epa_fixtures as fx  # noqa: E402
import validate_epa as V  # noqa: E402
from thresholds import common, split  # noqa: E402

# The production pin tables, kept before any test pins them (fx.pinned_terms): ArmProofs restores them to
# show the arming pass on decision 56's u_D terms, which every report's Table 8 pins, and on the D3 summary
# columns, pinned since 24 October 2026 (decisions 78-80), and refuse once one of them is taken away.
PRODUCTION_U_D = epa_stats.U_D
PRODUCTION_UNPINNED_FOR = d3_rows.unpinned_for


def tearDownModule():
    epa_fit.close_pools()


def _warn_task(x):
    """A pool task that warns (C6: warnings are errors, in a worker too)."""
    import warnings
    warnings.warn("a synthetic warning at a held-out row", RuntimeWarning)
    return x

# The engines the guards are armed on: the Ford for the run-once guards (it has no D3 drive, so its
# arming needs no data folder), the Mazda for the held-out counts and the D3 hashes (its synthetic
# design carries decision 54's special rows on its held-out lines). A test's choice, never a default.
FORD, MAZDA = "ford_27tt", "mazda_25t"
CHECK_STUB = "import sys\nsys.exit(0)\n"        # calibrate_epa.py check, synthetic: gives the stage back
SYNTHETIC_SHA = {"frozen": "f" * 64, "dump": "d" * 64, "engine": "synthetic-engine-sha", "plant": "synthetic-plant-sha"}


# ------------------------------------------------------------------------------------------ the repo
def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(text.encode("utf-8"))


def read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path, obj):
    write(path, json.dumps(obj, indent=1, ensure_ascii=True) + "\n")


def cal_path(root, engine, rel):
    return os.path.join(root, *V.cal_dir(engine).split("/"), *rel.split("/"))


def val_path(root, engine, rel):
    return os.path.join(root, *V.val_dir(engine).split("/"), *[p for p in rel.split("/") if p])


SYNTHETIC_CENSORING = {"censored": False, "min_lambda_cellref": 0.8, "n_at_min_within_1e-9": 1,
                       "documented_floor": None, "rule": "synthetic", "final_rows_with_lambda": 9}


def default_records(engine, root):
    """The calibration records a guard test needs: a synthetic derived file and placeholder records,
    whose contents no guard reads (only their hashes and commits)."""
    return {"derived": {"_about": "synthetic", "cycle": {"synthetic": 1.0}, "ecu": {}, "boost_ceiling": {}},
            "engine_sha": SYNTHETIC_SHA["engine"], "frozen": SYNTHETIC_SHA["frozen"],
            "stage0": {"schema": "epa-stage0/1", "checks": {"censoring": dict(SYNTHETIC_CENSORING)}},
            "e6": {v: {"schema": "epa-e6/1", "variant": v} for v in V.E6_REFIT}, "complete": {}}


def prepare(repo, engines_, data_folder, *, records):
    """Make a fixture repository armable for each engine: every step-2 module present (a placeholder
    where this tree has none yet), calibrate_epa.py the synthetic check, each engine's derived file, the
    code committed as the first fit's; then the calibration's records -- stage0.json, fit_A.json,
    in_sample.json and the five refit variants first, then freeze.json and complete.json holding their
    hashes (fits, e6_files), as calibrate_epa.py writes them -- and the tightenings, committed.
    records(engine, root) gives each engine's derived file, engine_sha, frozen hash, stage0.json, e6 files
    and complete.json's further keys (default_records). Returns the first fit's commit."""
    root = repo.root
    src = fx.synthetic_source(repo)
    for rel in epa_freeze.CODE_HASHED:
        p = os.path.join(root, *rel.split("/"))
        if not os.path.isfile(p):
            write(p, f"# synthetic placeholder of {rel}: this tree has no such module yet\n")
    write(os.path.join(root, "calibrate_epa.py"), CHECK_STUB)
    recs = {eng: records(eng, root) for eng in engines_}
    for eng in engines_:
        write_json(epa_freeze.derived_path(eng, root=root), recs[eng]["derived"])
    fit_head = fx.commit_all(root, "synthetic step-2 code and derived files: the first fit's tree")
    for eng in engines_:
        rec = recs[eng]
        tree = epa_freeze.tree_record(eng, root=root)
        data = epa_freeze.data_shas(eng, source=src)
        contract = {"commit": src.contract_commit, "json_sha_text": common.sha_text(src.contract_json),
                    "md_sha_text": common.sha_text(src.contract_md)}
        write_json(cal_path(root, eng, "fit_A.json"), {"schema": "epa-fit/1", "provenance": {
            "git": {"head": fit_head}, "code_sha_text": tree["code"]}})
        write_json(cal_path(root, eng, "in_sample.json"), {"schema": "epa-in-sample/1"})
        write_json(cal_path(root, eng, "stage0.json"), rec["stage0"])
        # Run 1's proofs, which the arming reads (WP3's fix of 23 October 2026): T0 passed, C8's poison proof
        # complete and equal at the frozen sections, run.json's invocations all clean
        # t0.json with the provenance of the code T0 ran on: the first fit's (the arming lists every change
        # since t0.json's head, WP3's second fix of 23 October 2026)
        write_json(cal_path(root, eng, "t0.json"), {"schema": epa_freeze.T0_SCHEMA, "pass": True, "provenance": {
            "git": {"head": fit_head}, "code_sha_text": tree["code"]}})
        # the steps after the freeze carry the freeze's code and plant in their provenance, as calibrate_epa.py
        # writes them (validate_epa.after_freeze_problems; WP3's third fix of 24 October 2026)
        prov = {"code_sha_text": tree["code"], "plant_sha": SYNTHETIC_SHA["plant"],
                "git": {"head": fit_head, "step2_clean": True}}
        write_json(cal_path(root, eng, "poison.json"), dict(synthetic_poison(rec["frozen"]), provenance=prov))
        write_json(cal_path(root, eng, "run.json"), {"engine": eng, "invocations": [
            {"k": 1, "subcommand": "fit", "outcome": "ok", "outside_allowlist": [], "refused_by_audit": []}]})
        for v in V.E6_REFIT:
            write_json(cal_path(root, eng, f"e6/row{v}.json"), dict(rec["e6"][v], provenance=prov))
        fits = {b: common.sha_text(cal_path(root, eng, b)) for b in V.FITS_REQUIRED}
        e6_files = {f"{V.cal_dir(eng)}/e6/row{v}.json": common.sha_text(cal_path(root, eng, f"e6/row{v}.json"))
                    for v in V.E6_REFIT}
        write_json(cal_path(root, eng, "freeze.json"), {
            "schema": "epa-freeze/1", "form": "A", "frozen_sections_sha256": rec["frozen"],
            "derived": tree["derived"], "contract": contract, "data": data, "code": tree["code"],
            "plant": {"plant_sha": SYNTHETIC_SHA["plant"]}, "fits": fits, "versions": {}, "git_head": fit_head,
            "flags": [], "all_row_depth_edge": {"active": False, "flag": epa_freeze.ALL_ROW_DEPTH_FLAG}})
        write_json(cal_path(root, eng, "complete.json"), {
            "schema": "epa-complete/1", "frozen_sections_sha256": rec["frozen"], "derived": tree["derived"],
            "engine_sha": rec["engine_sha"], "dump": {"sha256": SYNTHETIC_SHA["dump"]}, "e6_files": e6_files,
            "provenance": prov, **rec["complete"]})
    fx.commit_all(root, "synthetic calibration records")
    fx.synthetic_tightenings(repo, plant=V.TIGHTENING_PLANT)
    os.makedirs(data_folder, exist_ok=True)
    return fit_head


def defect_entry(fix, k=1):
    """One defects.json entry in the layout calibrate_epa.py writes (epa_freeze.DEFECT_KEYS), synthetic."""
    return {"k": k, "run_invocation": 1, "found_by": "synthetic", "assertion": "synthetic", "fix_commit": fix,
            "previous_run": f"defect_{k}/"}


def synthetic_poison(frozen):
    """A poison.json that is C8's proof for the frozen sections `frozen` (epa_freeze.poison_problems: every
    comparison equal, the full form-A fit on every run), synthetic, as calibrate_epa.py poison writes it."""
    import epa_fit
    run = {"copies_are_not_the_tables": True, "stage0_equal": True, "view_equal": True, "yield_equal": True,
           "manifest_equal": True, "engine_facts_equal": True,
           "stages": {k: True for k in epa_fit.poison_run_stages()},
           "full_form_a": {"frozen_sections_sha256_equal": True}}
    return {"schema": epa_freeze.POISON_SCHEMA, "runs": {h: json.loads(json.dumps(run)) for h in epa_rows.POISONS},
            "frozen_sections_sha256": frozen, "form": "A",
            "reference_equals_fit": {k: True for k in epa_fit.poison_tied_stages("A")},
            "garbled_contract_view_equal": True, "garbled_contract_yield_equal": True, "all_equal": True}


def synthetic_data_folder(folder, files):
    """A data folder with a MANIFEST.csv (MANIFEST's own columns) listing `files` {rel: bytes}."""
    rows = []
    for rel, data in files.items():
        p = os.path.join(folder, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(data)
        rows.append({"url": "synthetic", "local_path": p, "bytes": len(data), "sha256": common.sha_raw(p),
                     "date_utc": "2026-10-23", "kind": "download", "http_status": "200", "verified_now": "yes",
                     "note": "synthetic"})
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]) if rows else ["url", "local_path", "sha256"])
    w.writeheader()
    w.writerows(rows)
    with open(os.path.join(folder, "MANIFEST.csv"), "w", encoding="utf-8", newline="") as fh:
        fh.write(buf.getvalue())


@contextlib.contextmanager
def arm_patches(split_result):
    """The arming's steps that need a calibrated plant or this file's own tree, answered synthetically:
    engines.get (no EPA plant is calibrated) and the dump give complete.json's records; the generator's
    split is test_epa_fixtures.split_of's, the generator's own code run on the same synthetic tables."""
    def plant(ctx):
        ctx["plant"] = None
        ctx["record"]["engine_sha"] = ctx["complete"]["engine_sha"]
        ctx["record"]["plant_sha"] = ctx["freeze"]["plant"]["plant_sha"]
        return []
    with mock.patch.object(V, "_arm_plant", plant), \
            mock.patch.object(epa_freeze, "frozen_plant_dump",
                              lambda p: epa_freeze.Dump(sha256=SYNTHETIC_SHA["dump"], n_values=0, keys=())), \
            mock.patch.object(V, "_require_this_tree", lambda ctx, what: []), \
            mock.patch.object(split, "compute", lambda: split_result):
        yield


def git(root, *args):
    return fx.git(root, *args)


def commit_file(root, rel, message):
    git(root, "add", "--", rel)
    git(root, "commit", "-q", "-m", message)
    return git(root, "rev-parse", "HEAD")


class FakeCompute:
    """The held-out computation's stand-in: it records whether STARTED existed when it was called,
    reads the held-out rows through epa_rows.read_held_out (the real first held-out read), and returns
    fixed records whose labels the defect route's cap must change. `raise_` makes it crash; `open_`
    makes it open a file the run's allowlist does not hold; `warn_` makes it warn (warnings.warn) after
    the first held-out read, as a NumPy RuntimeWarning on a real row would."""

    def __init__(self, *, raise_=None, open_=None, warn_=None):
        self.raise_, self.open_, self.warn_ = raise_, open_, warn_
        self.started_seen, self.rows_read = [], []

    def __call__(self, name, *, source, token, jobs, armed):
        self.started_seen.append(os.path.isfile(val_path(source.root, name, V.STARTED))
                                 or any(f.startswith(V.STARTED + "_rerun") for f in os.listdir(val_path(source.root, name, ""))))
        held = epa_rows.read_held_out(name, source=source, token=token)
        self.rows_read.append(len(held.rows))
        if self.open_:
            open(self.open_, "rb").close()
        if self.warn_ is not None:
            warnings.warn(self.warn_)
        if self.raise_ is not None:
            raise self.raise_
        rows = {"schema": V.ROWS_SCHEMA, "provenance": {"note": "validated stays here"},
                "rows": {"E1a": {"label": "validated", "kappa": 1.0, "lines": {"x": {"label": "validated"}}},
                         "D1": {"label": "limited", "kappa": 1.25}, "E8": {"label": "untested"},
                         "L1": {"label": "off"}},
                "reported": {"E1a": {"label": "validated", "kappa": 1.0}, "D1": {"label": "limited", "kappa": 1.25}},
                "section7": {"level_850c_label": "validated", "drop": True, "drop_rows": ["L1"]},
                "c5_recheck_margin": None}
        out = [(V.ROWS, rows), (V.E6, {"schema": V.E6_SCHEMA, "rows": {"12": {"E3a": {"label_worse": "validated"}}}})]
        if V.D3_OUTPUT[name]:
            out.append((V.D3_OUTPUT[name], {"schema": V.C3_SCHEMA, "rows": {}}))
        return out


def quiet(fn, *a, **kw):
    """Call fn with its printout captured; (result or exception, the printout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            return fn(*a, **kw), buf.getvalue()
        except BaseException as exc:          # SystemExit included: the printout is what is checked
            return exc, buf.getvalue()


# ------------------------------------------------------------------------------------------ the case
class Armed(fx.SyntheticRepoCase):
    """One synthetic repository made armable for the class; each test arms its own copy in place
    (ARMED.json records the path it was made in, so a copy cannot inherit an arming). A subclass may
    edit the synthetic contract first (contract_edit) and give its own calibration records (records)."""
    ENGINES = (FORD, MAZDA)
    contract_edit = None

    @classmethod
    def records(cls, engine, root):
        return default_records(engine, root)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if cls.contract_edit is not None:
            cls.base = fx.rewrite_contract(cls.base, cls.contract_edit)
        cls.data = os.path.join(cls._tmp.name, "data_folder")
        cls.summary_rel = V.D3_SOURCES[MAZDA]["summary"] + "/synthetic_summary.xlsx"
        synthetic_data_folder(cls.data, {cls.summary_rel: b"synthetic summary workbook\n"})
        cls.fit_head = prepare(cls.base, cls.ENGINES, cls.data, records=cls.records)
        cls.split, _ = fx.split_of(cls.base.root)
        cls.base = fx.Repo(root=cls.base.root, contract_commit=cls.base.contract_commit,
                           head=git(cls.base.root, "rev-parse", "HEAD"))

    def setUp(self):
        super().setUp()
        self.enterContext(arm_patches(self.split))
        self.enterContext(fx.pinned_terms())

    def repo(self):
        r = self.fresh()
        return r, fx.synthetic_source(r)

    def arm(self, source, *, engine, defect, data_folder):
        return V.arm(engine, source=source, jobs=1, data_folder=data_folder, defect=defect)

    def armed(self, *, engine):
        """A fresh copy, armed in place and ARMED.json committed alone."""
        r, src = self.repo()
        self.arm(src, engine=engine, defect=None, data_folder=self.data)
        commit_file(r.root, f"{V.val_dir(engine)}/{V.ARMED}", "arming")
        return r, src

    def run_(self, src, fake, *, engine, defect):
        with mock.patch.object(V, "_compute", fake):
            return quiet(V.run, engine, source=src, jobs=1, defect=defect)

    def assertRefused(self, src, needle, *, engine, defect):
        problems = V.refusals(engine, source=src, defect=defect)
        self.assertTrue(any(needle in p for p in problems), f"no refusal containing {needle!r}: {problems}")
        return problems

    def assertRuns(self, src, *, engine, defect):
        self.assertEqual(V.refusals(engine, source=src, defect=defect), ())


class ReaderGuard(Armed):
    """C5: the reader checks ARMED.json itself, whatever token it is given."""

    def test_the_reader_refuses_without_ARMED_committed_whatever_token(self):
        r, src = self.repo()
        head = git(r.root, "rev-parse", "HEAD")
        for token in (V.Token(engine=MAZDA, armed_blob="0" * 40, head=head, root=r.root),
                      types.SimpleNamespace(engine=MAZDA, armed_blob="0" * 40, head=head, root=r.root)):
            with self.assertRaises(epa_rows.NotArmed):
                epa_rows.read_held_out(MAZDA, source=src, token=token)
        self.arm(src, engine=MAZDA, defect=None, data_folder=self.data)          # written, not committed: still refused
        blob = git(r.root, "hash-object", "--", f"{V.val_dir(MAZDA)}/{V.ARMED}")
        with self.assertRaises(epa_rows.NotArmed):
            epa_rows.read_held_out(MAZDA, source=src, token=V.Token(engine=MAZDA, armed_blob=blob, head=head,
                                                                    root=r.root))

    def test_a_forged_token_is_refused_and_the_issued_one_yields(self):
        r, src = self.armed(engine=MAZDA)
        tok = V.verify_for_validation(MAZDA, source=src, defect=None)
        for forged in (V.Token(engine=MAZDA, armed_blob="1" * 40, head=tok.head, root=tok.root),
                       V.Token(engine=MAZDA, armed_blob=tok.armed_blob, head="2" * 40, root=tok.root),
                       V.Token(engine=FORD, armed_blob=tok.armed_blob, head=tok.head, root=tok.root),
                       V.Token(engine=MAZDA, armed_blob=tok.armed_blob, head=tok.head, root=r.root + "_elsewhere")):
            with self.assertRaises(epa_rows.NotArmed):
                epa_rows.read_held_out(MAZDA, source=src, token=forged)
        held = epa_rows.read_held_out(MAZDA, source=src, token=tok)
        self.assertEqual(len(held.rows), fx.read_contract(r)["engines"][MAZDA]["n_held_out_rows"])
        # the control: the same issued token once ARMED.json differs from its blob at HEAD
        p = val_path(r.root, MAZDA, V.ARMED)
        with open(p, "ab") as fh:
            fh.write(b" ")
        with self.assertRaises(epa_rows.NotArmed):
            epa_rows.read_held_out(MAZDA, source=src, token=tok)

    def test_no_token_is_issued_while_a_refusal_stands(self):
        r, src = self.armed(engine=FORD)
        with open(os.path.join(r.root, "validate_epa.py"), "a", encoding="utf-8") as fh:
            fh.write("\n# an edit after the arming\n")
        with self.assertRaises(V.Refused):
            V.verify_for_validation(FORD, source=src, defect=None)
        git(r.root, "checkout", "--", "validate_epa.py")
        self.assertEqual(V.verify_for_validation(FORD, source=src, defect=None).engine, FORD)


class RunRefusals(Armed):
    """C6: every refusal of run, each shown to pass once its cause is removed."""

    def test_a_run_in_the_armed_tree_writes_its_records(self):
        r, src = self.armed(engine=FORD)
        fake = FakeCompute()
        res, out = self.run_(src, fake, engine=FORD, defect=None)
        self.assertEqual(res["outcome"], "ok", out)
        files = set(os.listdir(val_path(r.root, FORD, "")))
        self.assertEqual(files, {V.ARMED, V.STARTED, V.ROWS, V.E6, V.RUN})
        run = read_json(val_path(r.root, FORD, V.RUN))
        inv = run["invocations"][0]
        self.assertEqual((inv["outcome"], inv["outside_allowlist"], inv["reexecution_with_started_alone"]),
                         ("ok", [], False))
        self.assertGreater(fake.rows_read[0], 0)

    def test_refused_until_ARMED_is_committed(self):
        r, src = self.repo()
        self.assertRefused(src, "not committed at HEAD", engine=FORD, defect=None)
        self.arm(src, engine=FORD, defect=None, data_folder=self.data)
        self.assertRefused(src, "not committed at HEAD", engine=FORD, defect=None)
        commit_file(r.root, f"{V.val_dir(FORD)}/{V.ARMED}", "arming")
        self.assertRuns(src, engine=FORD, defect=None)

    def test_refused_in_a_linked_worktree(self):
        r, src = self.armed(engine=FORD)
        wt = fx.add_worktree(r)
        wsrc = epa_rows.Source(root=wt, engine_dir=os.path.join(wt, os.path.relpath(src.engine_dir, r.root)),
                               contract_json=os.path.join(wt, os.path.relpath(src.contract_json, r.root)),
                               contract_md=os.path.join(wt, os.path.relpath(src.contract_md, r.root)),
                               contract_commit=src.contract_commit, allow_poisoned_tables=False)
        self.assertRefused(wsrc, "linked worktree", engine=FORD, defect=None)
        self.assertRuns(src, engine=FORD, defect=None)
        git(r.root, "worktree", "remove", "--force", wt)
        self.assertRuns(src, engine=FORD, defect=None)

    def _copy(self, r, with_git):
        dst = tempfile.mkdtemp(prefix="copy_", dir=self._tmp.name)
        root = os.path.join(dst, "repo")
        shutil.copytree(r.root, root, ignore=None if with_git else shutil.ignore_patterns(".git"))
        rr = fx.Repo(root=root, contract_commit=r.contract_commit, head=r.head)
        return fx.synthetic_source(rr)

    def test_refused_without_git(self):
        r, src = self.armed(engine=FORD)
        self.assertRefused(self._copy(r, with_git=False), "has no .git", engine=FORD, defect=None)
        self.assertRuns(src, engine=FORD, defect=None)

    def test_refused_outside_the_armed_path(self):
        r, src = self.armed(engine=FORD)
        self.assertRefused(self._copy(r, with_git=True), "not the armed path", engine=FORD, defect=None)
        self.assertRuns(src, engine=FORD, defect=None)

    def test_refused_with_an_untracked_file_in_the_folder(self):
        r, src = self.armed(engine=FORD)
        extra = val_path(r.root, FORD, "notes.json")
        write(extra, "{}\n")
        self.assertRefused(src, "notes.json", engine=FORD, defect=None)
        os.remove(extra)
        self.assertRuns(src, engine=FORD, defect=None)

    def test_refused_with_an_ignored_file_in_the_folder(self):
        r, src = self.armed(engine=FORD)
        with open(os.path.join(r.root, ".gitignore"), "a", encoding="utf-8") as fh:
            fh.write(f"{V.val_dir(FORD)}/scratch.txt\n")
        extra = val_path(r.root, FORD, "scratch.txt")
        write(extra, "scratch\n")
        self.assertEqual(fx.git(r.root, "check-ignore", f"{V.val_dir(FORD)}/scratch.txt"),
                         f"{V.val_dir(FORD)}/scratch.txt")            # git itself ignores it
        self.assertRefused(src, "scratch.txt", engine=FORD, defect=None)
        os.remove(extra)
        self.assertRuns(src, engine=FORD, defect=None)

    def test_refused_with_a_tracked_file_and_with_one_in_git_log_all(self):
        r, src = self.armed(engine=FORD)
        rel = f"{V.val_dir(FORD)}/{V.ROWS}"
        git(r.root, "checkout", "-q", "-b", "side")
        write(os.path.join(r.root, *rel.split("/")), "{}\n")
        commit_file(r.root, rel, "a rows.json on a side branch")
        self.assertRefused(src, "earlier run's records", engine=FORD, defect=None)         # tracked, in the folder: a run's record
        git(r.root, "checkout", "-q", "main")
        self.assertFalse(os.path.exists(os.path.join(r.root, *rel.split("/"))))
        self.assertRefused(src, "git log --all", engine=FORD, defect=None)                 # gone from the tree, still in the history
        git(r.root, "branch", "-q", "-D", "side")
        self.assertRuns(src, engine=FORD, defect=None)

    def test_refused_when_a_calibration_record_changed_after_the_arming(self):
        """stage0.json (the censoring the run reads) and the refit variants are held by freeze.json's fits
        and complete.json's e6_files; a change committed after the arming is refused, and passes once
        undone (C5: matching hashes)."""
        r, src = self.armed(engine=FORD)
        for rel, needle in (("stage0.json", "fits records"), ("e6/row2.json", "e6_files records")):
            p = cal_path(r.root, FORD, rel)
            before = read_bytes(p)
            obj = read_json(p)
            obj["edited_after_the_arming"] = True
            write_json(p, obj)
            fx.commit_all(r.root, f"{rel} edited after the arming")
            self.assertRefused(src, needle, engine=FORD, defect=None)
            with open(p, "wb") as fh:
                fh.write(before)
            fx.commit_all(r.root, f"{rel} restored")
            self.assertRuns(src, engine=FORD, defect=None)

    def test_refused_with_dirty_validation_code(self):
        r, src = self.armed(engine=FORD)
        for rel in ("validate_epa.py", "epa_stats.py", "thresholds/split.py"):
            p = os.path.join(r.root, *rel.split("/"))
            with open(p, "a", encoding="utf-8") as fh:
                fh.write("\n# edited after the arming\n")
            self.assertRefused(src, "not committed and clean", engine=FORD, defect=None)
            git(r.root, "checkout", "--", rel)
            self.assertRuns(src, engine=FORD, defect=None)

    def test_a_refused_run_is_logged_outside_the_folder(self):
        r, src = self.armed(engine=FORD)
        p = os.path.join(r.root, "validate_epa.py")
        with open(p, "a", encoding="utf-8") as fh:
            fh.write("\n# edited\n")
        res, _ = self.run_(src, FakeCompute(), engine=FORD, defect=None)
        self.assertIsInstance(res, V.Refused)
        self.assertEqual(set(os.listdir(val_path(r.root, FORD, ""))), {V.ARMED})
        log = read_json(os.path.join(r.root, *V.invocations_rel(FORD).split("/")))
        self.assertTrue(log["invocations"][0]["outcome"].startswith("refused: "))
        git(r.root, "checkout", "--", "validate_epa.py")
        res, _ = self.run_(src, FakeCompute(), engine=FORD, defect=None)
        self.assertEqual(res["outcome"], "ok")


class RunOnce(Armed):
    """STARTED, crash records, re-execution and the defect route (C6; decision 60; section 7)."""

    def test_STARTED_exists_when_the_first_held_out_row_is_read(self):
        r, src = self.armed(engine=FORD)
        probe = FakeCompute(raise_=StopIteration("probe only"))
        # the control: the probe, called before run on the armed tree, sees no STARTED
        self.assertRaises(StopIteration, probe, FORD, source=src, jobs=1, armed=None,
                          token=V.verify_for_validation(FORD, source=src, defect=None))
        self.assertEqual(probe.started_seen, [False])
        fake = FakeCompute()
        res, _ = self.run_(src, fake, engine=FORD, defect=None)
        self.assertEqual((res["outcome"], fake.started_seen), ("ok", [True]))

    def test_run_writes_STARTED_before_it_computes(self):
        """The order in run's own code: the STARTED write is a statement before the call of _compute;
        the control is the same check on a copy of run with the two swapped."""
        src = read_text(os.path.join(HERE, "validate_epa.py"))
        self.assertTrue(started_before_compute(src))
        swapped = src.replace("    if not reexecution:\n", "    outputs_first = _compute\n    if not reexecution:\n", 1)
        self.assertFalse(started_before_compute(swapped))

    def test_a_crash_writes_its_record_and_blocks_re_execution(self):
        r, src = self.armed(engine=FORD)
        res, out = self.run_(src, FakeCompute(raise_=ValueError("E1a is 1.2345 %")), engine=FORD, defect=None)
        self.assertIsInstance(res, SystemExit)
        self.assertIn("crash: ValueError", out)
        self.assertNotIn("1.2345", out)                  # only the exception's type is printed
        with open(val_path(r.root, FORD, "crash_1.txt"), encoding="utf-8") as fh:
            self.assertEqual(fh.readline().strip(), "attempt: first")
        inv = read_json(val_path(r.root, FORD, V.RUN))["invocations"][0]
        self.assertEqual(inv["outcome"], "crash: ValueError")
        self.assertRefused(src, "only the defect route", engine=FORD, defect=None)
        # a crash ends the run: its end marker and the log's end refuse it with every record removed (WP3's
        # second fix of 23 October 2026)
        blob = git(r.root, "rev-parse", f"HEAD:{V.val_dir(FORD)}/{V.ARMED}")
        self.assertEqual(read_json(epa_freeze.run_marker_path("ended", FORD, blob, root=r.root))["outcome"],
                         "crash: ValueError")
        # the crash record alone blocks it: a process killed after crash_1.txt and before run.json leaves
        # STARTED and the crash record -- and no end, which comes after run.json -- and that is not "STARTED
        # alone" (C6: the crash record counts as written)
        os.remove(val_path(r.root, FORD, V.RUN))
        os.remove(epa_freeze.run_marker_path("ended", FORD, blob, root=r.root))
        logp = os.path.join(r.root, *V.invocations_rel(FORD).split("/"))
        log = read_json(logp)
        log["invocations"] = [e for e in log["invocations"] if e.get("event") != "ended"]
        epa_freeze.write_json_atomic(logp, log)
        self.assertRefused(src, "only the defect route", engine=FORD, defect=None)
        os.remove(val_path(r.root, FORD, "crash_1.txt"))                # the control: STARTED alone runs again
        self.assertRuns(src, engine=FORD, defect=None)

    def test_a_warning_in_the_runs_own_process_is_a_crash(self):
        """C6: warnings are errors in validate_epa.py run's own process as in its workers (the fourth tests review:
        with run's warnings.simplefilter("error") turned to "ignore" every test passed; WorkerWarnings covers the
        spawn workers' filter only). A RuntimeWarning after the first held-out read ends the run as a crash: exit
        1, crash_1.txt written, run.json's outcome "crash: RuntimeWarning", whatever filter the caller had (here
        "ignore"). The control: the same compute without the warning, on a second armed copy under the same
        caller's filter, finishes."""
        r, src = self.armed(engine=FORD)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res, out = self.run_(src, FakeCompute(warn_=RuntimeWarning("a degenerate statistic")), engine=FORD,
                                 defect=None)
        self.assertIsInstance(res, SystemExit)
        self.assertEqual(res.code, 1)
        self.assertIn("crash: RuntimeWarning", out)
        self.assertTrue(os.path.isfile(val_path(r.root, FORD, "crash_1.txt")))
        inv = read_json(val_path(r.root, FORD, V.RUN))["invocations"][0]
        self.assertEqual(inv["outcome"], "crash: RuntimeWarning")
        r2, src2 = self.armed(engine=FORD)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res2, _ = self.run_(src2, FakeCompute(), engine=FORD, defect=None)
        self.assertEqual(res2["outcome"], "ok")

    def test_a_run_with_STARTED_alone_runs_again(self):
        r, src = self.armed(engine=FORD)
        tok = V.verify_for_validation(FORD, source=src, defect=None)
        started = val_path(r.root, FORD, V.STARTED)
        epa_freeze.write_json_atomic(started, {"engine": FORD, "head": tok.head, "armed_blob": "9" * 40,
                                               "defect_rerun": None})
        self.assertRefused(src, "STARTED is not this arming's", engine=FORD, defect=None)         # the control: another arming's
        epa_freeze.write_json_atomic(started, {"engine": FORD, "head": tok.head, "armed_blob": tok.armed_blob,
                                               "defect_rerun": None})   # as run writes it, then killed
        before = read_bytes(started)
        res, _ = self.run_(src, FakeCompute(), engine=FORD, defect=None)
        self.assertEqual(res["outcome"], "ok")
        self.assertEqual(read_bytes(started), before)            # never rewritten
        inv = read_json(val_path(r.root, FORD, V.RUN))["invocations"][0]
        self.assertTrue(inv["reexecution_with_started_alone"])
        self.assertRefused(src, "only the defect route", engine=FORD, defect=None)                # and now nothing runs twice

    def test_the_defect_route_reruns_beside_the_first_and_caps_the_labels(self):
        r, src = self.armed(engine=FORD)
        res, _ = self.run_(src, FakeCompute(), engine=FORD, defect=None)
        self.assertEqual(res["outcome"], "ok")
        fx.commit_all(r.root, "commit F: the first run's records")
        armed_commit = V.armed_commits(r.root, FORD)[0]
        # a defect found after the run: the fix committed, then listed in defects.json (C10)
        with open(os.path.join(r.root, "epa_stats.py"), "a", encoding="utf-8") as fh:
            fh.write("\n# the fix of a defect found after the run\n")
        fix = fx.commit_all(r.root, "fix")
        write_json(cal_path(r.root, FORD, "defects.json"), [defect_entry(fix)])
        fx.commit_all(r.root, "defects.json")
        d = V.Defect(reason="a synthetic defect", fix_commit=fix)
        self.assertRefused(src, "only the defect route", engine=FORD, defect=None)                 # the normal route stays shut
        self.assertRefused(src, "not re-made", engine=FORD, defect=d)                 # the defect route needs the re-arming
        with self.assertRaises(V.Refused):                               # a re-arming on the normal route
            self.arm(src, engine=FORD, defect=None, data_folder=self.data)
        with self.assertRaises(V.Refused):                               # a fix that is not after the arming
            self.arm(src, engine=FORD, defect=V.Defect(reason="x", fix_commit=self.fit_head), data_folder=self.data)
        rec = self.arm(src, engine=FORD, defect=d, data_folder=self.data)
        self.assertEqual((rec["rearm"]["k"], rec["rearm"]["first_armed_commit"]), (1, armed_commit))
        commit_file(r.root, f"{V.val_dir(FORD)}/{V.ARMED}", "re-arming")
        self.assertRuns(src, engine=FORD, defect=d)
        res, _ = self.run_(src, FakeCompute(), engine=FORD, defect=d)
        self.assertEqual(res["outcome"], "ok")
        files = set(os.listdir(val_path(r.root, FORD, "")))
        self.assertTrue({"STARTED_rerun1", "rows_rerun1.json", "e6_rerun1.json", "run_rerun1.json"} <= files)
        first = read_json(val_path(r.root, FORD, V.ROWS))
        second = read_json(val_path(r.root, FORD, "rows_rerun1.json"))
        self.assertEqual(first["rows"]["E1a"]["label"], "validated")    # the first is kept as it was
        self.assertEqual({k: v["label"] for k, v in second["rows"].items()},
                         {"E1a": "limited", "D1": "limited", "E8": "untested", "L1": "off"})
        self.assertEqual(second["rows"]["E1a"]["lines"]["x"]["label"], "limited")
        self.assertEqual(second["section7"]["level_850c_label"], "limited")
        self.assertEqual(second["provenance"]["note"], "validated stays here")
        self.assertEqual(second["defect_rerun"]["capped_at"], "limited")
        e6 = read_json(val_path(r.root, FORD, "e6_rerun1.json"))
        self.assertEqual(e6["rows"]["12"]["E3a"]["label_worse"], "limited")
        self.assertRefused(src, "re-arm for re-run 2", engine=FORD, defect=d)         # and the re-run itself runs once


class ArmGuards(Armed):
    """arm's refusals (E5, C10, C11, decision 63) and its held-out counts (decision 54)."""

    def test_arm_writes_a_record_the_run_accepts(self):
        r, src = self.repo()
        rec = self.arm(src, engine=FORD, defect=None, data_folder=self.data)
        self.assertEqual(rec["tightenings"]["plant"], V.TIGHTENING_PLANT)
        self.assertEqual(rec["held_out_structure"], {"per_held_out_line_equal": True, "deciding_lines_equal": True,
                                                     "pooled_counts_equal": True})
        self.assertEqual(rec["code_changes_since_fit"], [])
        self.assertEqual(rec["in_sample_check"]["check_exit"], 0)

    def test_arm_refuses_tightenings_of_another_plant(self):
        r, src = self.repo()
        p = os.path.join(r.root, *V.TIGHTENINGS_REL.split("/"))
        t = read_json(p)
        t["plant"] = FORD
        write_json(p, t)
        fx.commit_all(r.root, "tightenings measured on another plant")
        with self.assertRaises(V.Refused) as cm:
            self.arm(src, engine=FORD, defect=None, data_folder=self.data)
        self.assertTrue(any("arm/tightenings" in x and "decision 71" in x for x in cm.exception.problems))
        t["plant"] = V.TIGHTENING_PLANT
        write_json(p, t)
        fx.commit_all(r.root, "tightenings measured on the B58")
        self.arm(src, engine=FORD, defect=None, data_folder=self.data)

    def test_arm_refuses_a_code_change_since_the_fit_without_its_defect_entry(self):
        r, src = self.repo()
        with open(os.path.join(r.root, "epa_stats.py"), "a", encoding="utf-8") as fh:
            fh.write("\n# changed after the first fit\n")
        fix = fx.commit_all(r.root, "a change after the first fit")
        with self.assertRaises(V.Refused) as cm:
            self.arm(src, engine=FORD, defect=None, data_folder=self.data)
        self.assertTrue(any(x.startswith("arm/code") and "epa_stats.py" in x for x in cm.exception.problems))
        # an entry the writer would refuse (no run_invocation, a wall-clock date) is refused (WP3's second fix of 23
        # October 2026, on the test review's finding: arm read fix_commit and k alone)
        bad = dict(defect_entry(fix), date="2026-10-23")
        del bad["run_invocation"]
        write_json(cal_path(r.root, FORD, "defects.json"), [bad])
        fx.commit_all(r.root, "a defects.json entry in another layout")
        with self.assertRaises(V.Refused) as cm:
            self.arm(src, engine=FORD, defect=None, data_folder=self.data)
        self.assertTrue(any(x.startswith("arm/code") and "not in calibrate_epa.py's layout" in x
                            for x in cm.exception.problems), cm.exception.problems)
        write_json(cal_path(r.root, FORD, "defects.json"), [defect_entry(fix)])
        fx.commit_all(r.root, "its defects.json entry")
        rec = self.arm(src, engine=FORD, defect=None, data_folder=self.data)
        self.assertEqual(rec["code_changes_since_fit"], [{"path": "epa_stats.py", "defect_k": 1, "fix_commit": fix}])

    def test_arm_refuses_a_dump_or_an_in_sample_check_that_does_not_come_back(self):
        r, src = self.repo()
        with mock.patch.object(epa_freeze, "frozen_plant_dump",
                               lambda p: epa_freeze.Dump(sha256="e" * 64, n_values=0, keys=())):
            with self.assertRaises(V.Refused) as cm:
                self.arm(src, engine=FORD, defect=None, data_folder=self.data)
        self.assertTrue(any(x.startswith("arm/dump") for x in cm.exception.problems))
        write(os.path.join(r.root, "calibrate_epa.py"), "import sys\nsys.exit(3)\n")
        fx.commit_all(r.root, "a check that fails")
        with self.assertRaises(V.Refused) as cm:
            self.arm(src, engine=FORD, defect=None, data_folder=self.data)
        self.assertTrue(any(x.startswith("arm/code") or x.startswith("arm/in_sample") for x in cm.exception.problems))
        # with its change listed (C10), the failing check itself is what refuses
        write_json(cal_path(r.root, FORD, "defects.json"), [defect_entry(git(r.root, "rev-parse", "HEAD"))])
        fx.commit_all(r.root, "listed")
        with self.assertRaises(V.Refused) as cm:
            self.arm(src, engine=FORD, defect=None, data_folder=self.data)
        self.assertTrue(any(x.startswith("arm/in_sample") and "exited 3" in x for x in cm.exception.problems))

    def test_arm_refuses_a_calibration_record_its_freeze_does_not_hold(self):
        r, src = self.repo()
        p = cal_path(r.root, FORD, "stage0.json")
        before = read_bytes(p)
        write_json(p, dict(read_json(p), moved=True))
        fx.commit_all(r.root, "stage0.json moved after the freeze")
        with self.assertRaises(V.Refused) as cm:
            self.arm(src, engine=FORD, defect=None, data_folder=self.data)
        self.assertTrue(any(x.startswith("arm/calibration") and "stage0.json" in x for x in cm.exception.problems))
        with open(p, "wb") as fh:
            fh.write(before)
        fx.commit_all(r.root, "stage0.json as frozen")
        self.arm(src, engine=FORD, defect=None, data_folder=self.data)          # the control: as frozen, it arms

    def test_arm_refuses_after_a_run_on_the_normal_route(self):
        r, src = self.armed(engine=FORD)
        res, _ = self.run_(src, FakeCompute(), engine=FORD, defect=None)
        self.assertEqual(res["outcome"], "ok")
        with self.assertRaises(V.Refused) as cm:
            self.arm(src, engine=FORD, defect=None, data_folder=self.data)
        self.assertTrue(any(x.startswith("arm/folder") for x in cm.exception.problems))

    def test_arm_hashes_the_D3_files_against_the_manifest(self):
        r, src = self.repo()
        rec = self.arm(src, engine=MAZDA, defect=None, data_folder=self.data)
        self.assertEqual(rec["d3"]["summary"]["file"], self.summary_rel)
        # the control: a data folder whose summary is not the manifest's
        bad = os.path.join(self._tmp.name, "bad_data_" + os.path.basename(os.path.dirname(r.root)))
        shutil.copytree(self.data, bad)
        with open(os.path.join(bad, *self.summary_rel.split("/")), "ab") as fh:
            fh.write(b"one more byte")
        with self.assertRaises(V.Refused) as cm:
            self.arm(src, engine=MAZDA, defect=None, data_folder=bad)
        self.assertTrue(any(x.startswith("arm/d3") for x in cm.exception.problems))

    def test_arms_held_out_counts_equal_a_hand_count(self):
        r, src = self.repo()
        rec = self.arm(src, engine=MAZDA, defect=None, data_folder=self.data)
        self.assertEqual(rec["held_out_counts"], hand_counts(r, MAZDA))
        self.assertEqual(rec["held_out_counts"]["fired_lambda_missing"], 2)   # the design's two (fixtures)
        # the control: one more fired held-out row without lambda moves the count by one
        held = fx.held_rows(r, MAZDA)
        steady = next(s for s in epa_rows.TABLES[MAZDA] if s.role == "steady")
        path = fx.table_file(r.root, MAZDA, "steady", 0)
        want = [x for x in held[steady.name]]

        def edit(header, rows):
            i_sr, i_l, i_b = header.index("source_row"), header.index("exhaust_lambda"), header.index("bmep_bar")
            for row in rows:
                if int(row[i_sr]) in want and row[i_l] != "" and float(row[i_b]) >= 2.0:
                    row[i_l] = ""
                    break
            return rows
        fx.edit_table(path, edit)
        r2 = fx.rehash_tables(r)
        counts = epa_rows.held_out_counts(MAZDA, source=fx.synthetic_source(r2))
        self.assertEqual(counts.fired_lambda_missing, 3)
        self.assertEqual(dataclass_dict(counts), hand_counts(r2, MAZDA))

    def test_the_held_out_populations_are_the_contracts_or_arm_stops(self):
        """WP3's integration (23 October 2026): the loader's populations of the held-out rows
        (epa_rows.held_out_population_counts, split.classify at the contract's printed floor) equal the
        contract's per_held_out_line line by line (the synthetic contract's is split.compute's own), and
        arm's step `counts` passes; the control: one held-out steady row's MAP moved below the hot floor
        moves its line's hot count, and population_problems names that line."""
        r, src = self.repo()
        contract = fx.read_contract(r)
        for eng in self.ENGINES:
            got = epa_rows.held_out_population_counts(eng, source=src)
            want = contract["engines"][eng]["per_held_out_line"]
            self.assertEqual(set(got), set(want), eng)
            for line in got:
                self.assertEqual({k: got[line][k] for k in epa_rows.POPULATION_COUNT_KEYS},
                                 {k: want[line][k] for k in epa_rows.POPULATION_COUNT_KEYS}, (eng, line))
        self.assertEqual(V.population_problems(MAZDA, source=src, contract=contract), [])
        held = fx.held_rows(r, MAZDA)
        steady = next(s for s in epa_rows.TABLES[MAZDA] if s.role == "steady")
        floor = contract["engines"][MAZDA]["hot_map_floor_kpa"]
        moved = []

        def edit(header, rows):
            i_sr, i_mp = header.index("source_row"), header.index("intake_manifold_press_kpa_abs")
            for row in rows:
                if int(row[i_sr]) in held[steady.name] and float(row[i_mp]) >= floor and not moved:
                    row[i_mp] = repr(round(floor - 5.0, 2))
                    moved.append(int(row[i_sr]))
            return rows
        fx.edit_table(fx.table_file(r.root, MAZDA, "steady", 0), edit)
        self.assertEqual(len(moved), 1)
        r2 = fx.rehash_tables(r)
        got = V.population_problems(MAZDA, source=fx.synthetic_source(r2), contract=fx.read_contract(r2))
        self.assertTrue(got and all("per_held_out_line" in g for g in got), got)
        self.assertTrue(any("'s hot rows" in g for g in got), got)


class ArmProofs(Armed):
    """The arming's new steps (WP3's fix of 23 October 2026): the pins (decision 56's u_D terms and the D3
    summary columns), Run 1's proofs (T0, C8's poison, run.json's audit), check's exit read by name, and on
    the defect route the calibration the previous arming recorded."""

    def test_arm_refuses_while_a_pin_is_open(self):
        """The arming's pins step on the production tables (decision 56; WP3_INTERFACES.md 11): the production
        u_D table, which pins the meter's and the torque's terms from every report's Table 8, arms the Ford (no
        D3 chain) and records every term pinned; the production D3 summary columns, pinned since 24 October 2026
        (decisions 78-80), arm the Mazda, recorded as pinned. Controls (mistake 12): one report's torque pin taken
        away (the Ford's HD1), or every meter pin, refuses at arm/pins naming that term; a D3 summary column left
        open (d3_rows.unpinned_for patched, as WP3_INTERFACES.md 14 asks) refuses the Mazda naming it; under the
        synthetic terms the Ford arms (every other test)."""
        r, src = self.repo()
        self.assertEqual(epa_stats.unpinned_u_d(terms=PRODUCTION_U_D), {})
        with mock.patch.object(epa_stats, "U_D", PRODUCTION_U_D):
            rec = self.arm(src, engine=FORD, defect=None, data_folder=self.data)
        self.assertEqual(rec["pins"], {"u_D": "every term a gating row reads is pinned", "d3_summary": "no D3 chain"})
        torque, meter = PRODUCTION_U_D["torque"], PRODUCTION_U_D["meter"]
        short = dict(PRODUCTION_U_D, torque=dataclass_replace(
            torque, cells=tuple(c for c in torque.cells if c[0] != epa_stats.FORD_HD1)))
        bare = dict(PRODUCTION_U_D, meter=dataclass_replace(meter, cells=()))
        for terms, name in ((short, "'torque'"), (bare, "'meter'")):
            with self.subTest(term=name):
                r, src = self.repo()
                with mock.patch.object(epa_stats, "U_D", terms):
                    with self.assertRaises(V.Refused) as cm:
                        self.arm(src, engine=FORD, defect=None, data_folder=self.data)
                got = [x for x in cm.exception.problems if x.startswith("arm/pins")]
                self.assertTrue(got and all(name in x for x in got), got)
                self.assertTrue(any("D1" in x for x in got), got)
        self.assertEqual([PRODUCTION_UNPINNED_FOR(e) for e in (FORD, MAZDA, "honda_l15b7")], [(), (), ()])
        r, src = self.repo()
        with mock.patch.object(d3_rows, "unpinned_for", PRODUCTION_UNPINNED_FOR):
            rec = self.arm(src, engine=MAZDA, defect=None, data_folder=self.data)
        self.assertEqual(rec["pins"]["d3_summary"], "pinned")
        r, src = self.repo()
        with mock.patch.object(d3_rows, "unpinned_for", lambda name: ("cx9_2016.test_id",) if name == MAZDA else ()):
            with self.assertRaises(V.Refused) as cm:
                self.arm(src, engine=MAZDA, defect=None, data_folder=self.data)
        self.assertTrue(any(x.startswith("arm/pins") and "D3 summary column 'cx9_2016.test_id'" in x
                            for x in cm.exception.problems))
        r, src = self.repo()
        rec = self.arm(src, engine=FORD, defect=None, data_folder=self.data)        # the control: pinned
        self.assertEqual(rec["pins"]["d3_summary"], "no D3 chain")

    def test_arm_refuses_without_run1s_proofs(self):
        """T0 not passed, C8's proof not equal, an invocation the audit judged a defect: each refuses at
        arm/calibration, naming it; the control, the prepared records, arms (every other test)."""
        cases = (("t0.json", lambda x: dict(x, **{"pass": False}), "T0 did not pass"),
                 ("poison.json", lambda x: dict(x, all_equal=False), "all_equal is not true"),
                 ("poison.json", lambda x: dict(x, runs={h: dict(v, full_form_a=None) for h, v in x["runs"].items()}),
                  None),
                 ("run.json", lambda x: dict(x, invocations=x["invocations"] + [
                     {"k": 2, "subcommand": "e6", "outcome": "crash: KeyError", "outside_allowlist": [],
                      "refused_by_audit": []}]), "invocation 2 (e6): crash"))
        for rel, edit, needle in cases:
            for eng in (FORD, MAZDA):
                if needle is None and eng == FORD:
                    continue                         # the full form-A poison fit is the Mazda's alone
                r, src = self.repo()
                p = cal_path(r.root, eng, rel)
                write_json(p, edit(read_json(p)))
                fx.commit_all(r.root, f"{rel} edited")
                with self.assertRaises(V.Refused) as cm:
                    self.arm(src, engine=eng, defect=None, data_folder=self.data)
                want = needle or "full form-A poison fit is mandatory"
                self.assertTrue(any(x.startswith("arm/calibration") and want in x for x in cm.exception.problems),
                                (rel, eng, cm.exception.problems))
        # the full form-A fit missing on the Ford is no refusal (the control of the Mazda's case)
        r, src = self.repo()
        p = cal_path(r.root, FORD, "poison.json")
        x = read_json(p)
        write_json(p, dict(x, runs={h: dict(v, full_form_a=None) for h, v in x["runs"].items()}))
        fx.commit_all(r.root, "the Ford's poison without the full fit")
        self.arm(src, engine=FORD, defect=None, data_folder=self.data)

    def test_arm_refuses_a_step_after_the_freeze_on_other_code_or_plant(self):
        """The records of poison, e6 and complete carry the freeze's code and plant, written from committed code
        (validate_epa.after_freeze_problems; WP3's third fix of 24 October 2026, on the Run 1 review's finding that
        arm read only fit_A.json's, t0.json's and freeze.json's provenance). poison.json, which no other record
        hashes, written by another code, on another plant or from dirty code: arm/calibration refuses, naming it.
        The control: the prepared records arm (every other test), and the function passes them."""
        prov = lambda x: x["provenance"]                         # noqa: E731
        cases = (("code_sha_text", lambda p: dict(p, code_sha_text=dict(p["code_sha_text"], **{"k3_knee.py": "0" * 64})),
                  "poison.json was not written by the step-2 code freeze.json records"),
                 ("plant_sha", lambda p: dict(p, plant_sha="0" * 64), "poison.json was not written on the plant"),
                 ("step2_clean", lambda p: dict(p, git=dict(p["git"], step2_clean=False)),
                  "poison.json was written from step-2 code that was not committed and clean"))
        for what, edit, needle in cases:
            r, src = self.repo()
            p = cal_path(r.root, FORD, "poison.json")
            x = read_json(p)
            write_json(p, dict(x, provenance=edit(prov(x))))
            fx.commit_all(r.root, f"poison.json's {what} moved")
            with self.assertRaises(V.Refused) as cm:
                self.arm(src, engine=FORD, defect=None, data_folder=self.data)
            self.assertTrue(any(y.startswith("arm/calibration") and needle in y for y in cm.exception.problems),
                            (what, cm.exception.problems))
        r, _src = self.repo()
        freeze = read_json(cal_path(r.root, FORD, "freeze.json"))
        recs = {rel: read_json(cal_path(r.root, FORD, rel)) for rel in V.after_freeze_records()}
        self.assertEqual(V.after_freeze_problems(FORD, freeze=freeze, records=recs), [])
        self.assertEqual(len(V.after_freeze_records()), 7)
        recs["complete.json"] = {k: v for k, v in recs["complete.json"].items() if k != "provenance"}
        self.assertEqual(len(V.after_freeze_problems(FORD, freeze=freeze, records=recs)), 3)

    def test_arm_reads_checks_exit_by_name(self):
        """Only check's mismatch (exit 5) is C11's "repeat Run 1 from S0"; a wait (4), an audit defect (3) or
        a crash (1) is named as what it is."""
        for code, needle in ((5, "not given back byte for byte (C11: repeat Run 1 from S0)"),
                             (4, "waited on the Run 1 gate; not an in-sample comparison"),
                             (3, "opened a file outside its allowlist"), (1, "crashed")):
            r, src = self.repo()
            write(os.path.join(r.root, "calibrate_epa.py"), f"import sys\nsys.exit({code})\n")
            fix = fx.commit_all(r.root, f"a check that exits {code}")
            write_json(cal_path(r.root, FORD, "defects.json"), [defect_entry(fix)])
            fx.commit_all(r.root, "listed")
            with self.assertRaises(V.Refused) as cm:
                self.arm(src, engine=FORD, defect=None, data_folder=self.data)
            got = [x for x in cm.exception.problems if x.startswith("arm/in_sample")]
            self.assertTrue(any(f"exited {code}" in x and needle in x for x in got), (code, got))
            if code != 5:
                self.assertFalse(any("repeat Run 1" in x for x in got), got)

    def test_the_defect_route_refuses_a_refit_after_the_run(self):
        """C11: nothing is refitted. A re-arming whose complete.json (or freeze.json, or the derived file) is
        not the one the previous arming recorded refuses at arm/rearm; the control is the defect route's own
        test (RunOnce), where only the code changed."""
        r, src = self.armed(engine=FORD)
        res, _ = self.run_(src, FakeCompute(), engine=FORD, defect=None)
        self.assertEqual(res["outcome"], "ok")
        fx.commit_all(r.root, "commit F: the first run's records")
        with open(os.path.join(r.root, "epa_stats.py"), "a", encoding="utf-8") as fh:
            fh.write("\n# the fix of a defect found after the run\n")
        fix = fx.commit_all(r.root, "fix")
        write_json(cal_path(r.root, FORD, "defects.json"), [defect_entry(fix)])
        comp = read_json(cal_path(r.root, FORD, "complete.json"))
        write_json(cal_path(r.root, FORD, "complete.json"), dict(comp, refitted_after_the_run=True))
        fx.commit_all(r.root, "defects.json, and a completion re-made after the run")
        with self.assertRaises(V.Refused) as cm:
            self.arm(src, engine=FORD, defect=V.Defect(reason="a synthetic defect", fix_commit=fix),
                     data_folder=self.data)
        self.assertTrue(any(x.startswith("arm/rearm") and "complete.json" in x for x in cm.exception.problems),
                        cm.exception.problems)


class RunOnceMore(Armed):
    """C6 beyond the path: the arming's nonce in the work tree's git directory, and the start in the
    invocation log, outside the folder (WP3's fix of 23 October 2026)."""

    def test_a_tree_without_the_arming_s_nonce_does_not_run(self):
        r, src = self.armed(engine=FORD)
        self.assertRuns(src, engine=FORD, defect=None)
        path = V.nonce_path(r.root, FORD)
        kept = read_bytes(path)
        os.remove(path)                                   # a clone: its .git holds no nonce
        self.assertRefused(src, "nonce", engine=FORD, defect=None)
        with open(path, "wb") as fh:
            fh.write(b"another arming's nonce")
        self.assertRefused(src, "nonce", engine=FORD, defect=None)
        with open(path, "wb") as fh:
            fh.write(kept)
        self.assertRuns(src, engine=FORD, defect=None)    # the control

    def test_a_started_removed_from_the_folder_is_still_seen(self):
        """A run started, its records removed before commit F (none ever committed, so git log --all holds
        none): the invocation log's start refuses a second run on the normal route."""
        r, src = self.armed(engine=FORD)
        res, _ = self.run_(src, FakeCompute(), engine=FORD, defect=None)
        self.assertEqual(res["outcome"], "ok")
        log = read_json(os.path.join(r.root, *V.invocations_rel(FORD).split("/")))
        self.assertTrue(any(e.get("event") == "started" for e in log["invocations"]))
        for f in os.listdir(val_path(r.root, FORD, "")):
            if f != V.ARMED:
                os.remove(val_path(r.root, FORD, f))
        self.assertRefused(src, "invocation log records that this arming's run started", engine=FORD, defect=None)

    def test_a_cleaned_work_tree_does_not_run_again(self):
        """The second isolation review's replay (its scratch test_runonce_replay.py): every record of a run is
        untracked until commit F, so `git clean -fdx` removes them and the invocation log; the run-once
        markers in the work tree's git directory still refuse a second run. The control: with the markers
        removed too, the tree runs again (only the markers held it)."""
        r, src = self.armed(engine=FORD)
        res, _ = self.run_(src, FakeCompute(), engine=FORD, defect=None)
        self.assertEqual(res["outcome"], "ok")
        blob = git(r.root, "rev-parse", f"HEAD:{V.val_dir(FORD)}/{V.ARMED}")
        ended = epa_freeze.run_marker_path("ended", FORD, blob, root=r.root)
        started = epa_freeze.run_marker_path("started", FORD, blob, root=r.root)
        self.assertTrue(os.path.isfile(ended) and os.path.isfile(started))
        self.assertEqual(sorted(read_json(ended)["outputs"]), sorted(res["written"]))
        subprocess.run(["git", "clean", "-fdx"], cwd=r.root, capture_output=True, check=True)
        self.assertEqual(sorted(os.listdir(val_path(r.root, FORD, ""))), [V.ARMED])
        self.assertFalse(os.path.exists(os.path.join(r.root, *V.invocations_rel(FORD).split("/"))))
        self.assertRefused(src, "run ended", engine=FORD, defect=None)
        os.remove(ended)
        # the writing marker (WP3's fourth fix of 24 October 2026): the run began writing its outputs
        self.assertRefused(src, "run began writing its outputs", engine=FORD, defect=None)
        os.remove(epa_freeze.run_marker_path("writing", FORD, blob, root=r.root))
        self.assertRefused(src, "run started (its run-once marker", engine=FORD, defect=None)
        os.remove(started)
        self.assertRuns(src, engine=FORD, defect=None)

    def test_a_finished_run_with_started_alone_left_does_not_run_again(self):
        """The same review's second replay: a run that finished, every record but ARMED.json and STARTED
        removed, is not the killed process C6's one re-execution is for: refused, by the end marker and the
        invocation log's end. With both removed it is the fourth isolation review's case -- a run killed after it
        wrote rows.json, the outputs then deleted, STARTED alone left -- refused by the writing marker and the
        log's writing event (WP3's fourth fix of 24 October 2026: before it, a second normal run computed the
        held-out statistics again). The control: those removed too, STARTED alone runs again (a process killed
        before it computed anything)."""
        r, src = self.armed(engine=FORD)
        res, _ = self.run_(src, FakeCompute(), engine=FORD, defect=None)
        self.assertEqual(res["outcome"], "ok")
        for f in os.listdir(val_path(r.root, FORD, "")):
            if f not in (V.ARMED, V.STARTED):
                os.remove(val_path(r.root, FORD, f))
        self.assertRefused(src, "run ended", engine=FORD, defect=None)
        blob = git(r.root, "rev-parse", f"HEAD:{V.val_dir(FORD)}/{V.ARMED}")
        os.remove(epa_freeze.run_marker_path("ended", FORD, blob, root=r.root))
        self.assertRefused(src, "run ended", engine=FORD, defect=None)           # the log's end still holds it
        logp = os.path.join(r.root, *V.invocations_rel(FORD).split("/"))
        log = read_json(logp)
        log["invocations"] = [e for e in log["invocations"] if e.get("event") != "ended"]
        epa_freeze.write_json_atomic(logp, log)
        self.assertRefused(src, "run began writing its outputs", engine=FORD, defect=None)
        os.remove(epa_freeze.run_marker_path("writing", FORD, blob, root=r.root))
        self.assertRefused(src, "run began writing its outputs", engine=FORD, defect=None)   # the log's event
        log["invocations"] = [e for e in log["invocations"] if e.get("event") != "writing"]
        epa_freeze.write_json_atomic(logp, log)
        self.assertRuns(src, engine=FORD, defect=None)


class WorkerWarnings(fx.Guarded):
    """C6's "warnings are errors" in a spawn worker as in this process (validate_epa.worker_audit): a
    warning in a held-out row's task is an error at --jobs 2 as at --jobs 1; the control, a pool without
    the run's initializer, lets it pass (a spawn worker inherits no filter set at run time)."""

    def test_a_worker_warning_is_an_error(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            with self.assertRaises(RuntimeWarning):
                epa_fit.ordered_map(_warn_task, [1, 2], jobs=1, initializer=V.WORKER_INIT)
            with self.assertRaises(RuntimeWarning):
                epa_fit.ordered_map(_warn_task, [1, 2, 3, 4], jobs=2, initializer=V.WORKER_INIT)
            self.assertEqual(epa_fit.ordered_map(_warn_task, [1, 2, 3, 4], jobs=2, initializer=None), [1, 2, 3, 4])
        epa_fit.close_pools()


class RealCheck(fx.SyntheticRepoCase):
    """The arming with the REAL `calibrate_epa.py check` (every other arm test replaces it by a stub, so the
    command line's own exit was never seen): a synthetic repository whose epa_rows pins its own contract
    (fx.pin_contract_commit), Run 1 in this process with test_calibrate_epa's stand-ins but the REAL in-sample
    stage, committed; arm runs check in a subprocess, which recomputes that stage for real, under the audit
    installed before its imports, and exits 0 with nothing outside its allowlist. The control: in_sample.json
    moved by one number (freeze.json's hash of it moved with it, as a refit would) makes arm refuse with
    check's mismatch, exit 5, named."""

    def test_arm_with_the_real_check(self):
        import calibrate_epa as C
        import engines
        import test_calibrate_epa as T
        jobs = 4
        r = fx.pin_contract_commit(T.run_repo(self))
        src = fx.synthetic_source(r)
        # the whole ladder (A to A+B+C+D, each failing its real in-sample stage on the B58 values is no matter:
        # check gives the stage back whatever it reads), so ladder_choice takes A+B+C+D as the ladder would
        stand = T.StandIns(types.SimpleNamespace(src=src), forms=engines.CYCLE_FORMS)
        stand.judge = epa_fit.in_sample_for                 # the real in-sample stage, the one check recomputes
        tmp = os.path.dirname(r.root)
        for sub in T.SUBS[:-1]:
            scr = os.path.join(tmp, "scratch_poison") if sub == "poison" else None
            body = {"t0": lambda: C.t0(MAZDA, source=src, jobs=jobs, defect=None),
                    "fit": lambda: C.fit(MAZDA, source=src, jobs=jobs, defect=None),
                    "poison": lambda: C.poison(MAZDA, source=src, jobs=jobs, scratch=scr, full=True),
                    "e6": lambda: C.e6(MAZDA, source=src, jobs=jobs),
                    "complete": lambda: C.complete(MAZDA, source=src, jobs=jobs)}[sub]
            env = {"DERIVING_PARAMS": "1"} if sub == "complete" else {}
            with T.contextlib_all(stand.patches() + [mock.patch.object(C, "_completion_task", T.stand_in_task),
                                                     mock.patch.dict(os.environ, env)]):
                code = C.invoke(sub, MAZDA, source=src, argv=[sub], body=body, scratch=scr, audit=None)
            self.assertEqual(code, C.EXIT_OK, (sub, T.runs(src, MAZDA)[-1]["outcome"]))
        fx.commit_all(r.root, "Run 1's records")
        fx.synthetic_tightenings(r, plant=V.TIGHTENING_PLANT)
        data = os.path.join(tmp, "data_folder")
        summary = V.D3_SOURCES[MAZDA]["summary"] + "/synthetic_summary.xlsx"
        synthetic_data_folder(data, {summary: b"synthetic summary workbook\n"})
        split_result, _ = fx.split_of(r.root)

        real_get = engines.get

        def built(name):
            if name not in epa_rows.TABLES:                 # the B58 (the tightenings' plant, decision 71)
                return real_get(name)
            vals = read_json(epa_freeze.derived_path(name, root=r.root))
            return engines.build_candidate(name, {k: v for k, v in vals.items() if not k.startswith("_")})

        def arm():
            with fx.pinned_terms(), mock.patch.object(V, "_require_this_tree", lambda ctx, what: []), \
                    mock.patch.object(engines, "get", built), mock.patch.object(split, "compute", lambda: split_result):
                return V.arm(MAZDA, source=src, jobs=jobs, data_folder=data, defect=None)
        rec = arm()
        self.assertEqual(rec["in_sample_check"]["check_exit"], 0)
        # THE SEAM (WP3's fourth fix of 24 October 2026, on the fourth Run 1 review's finding that only hand-made
        # records fed validate_epa's readers): the readers the held-out run's E6 rows call, on the very files
        # calibrate_epa.py wrote here -- each refit variant's conventions and its frozen sections with the frozen
        # plant's completion sections (a buildable candidate), rows 5 and 6's sigma and probe per field, row 9's
        # sizes and records -- so that a drift of either side stops here, not after STARTED
        comp = read_json(cal_path(r.root, MAZDA, "complete.json"))
        dvals = read_json(epa_freeze.derived_path(MAZDA, root=r.root))
        for v in V.E6_REFIT:
            f = read_json(cal_path(r.root, MAZDA, f"e6/row{v}.json"))
            if f.get("conventions"):
                self.assertIsInstance(epa_stats.Conventions(**f["conventions"]), epa_stats.Conventions)
            self.assertTrue(engines.build_candidate(MAZDA, V._variant_values(MAZDA, f, dvals)).engine.id)
        probes = comp["e6_probes"]
        for row, key in ((5, "row5"), (6, "row6")):
            for part in ("sigma", "probe"):
                got = V._per_field(probes[key][part], V.E6_ROW_FIELDS[row], f"E6 row {row} {part}")
                self.assertEqual(set(got), set(V.E6_ROW_FIELDS[row]), (row, part))
        frozen = built(MAZDA)
        self.assertTrue(probes.get("row9"))
        for const, spec in probes["row9"].items():
            self.assertIsInstance(float(spec["size"]), float)
            rec9 = spec.get("record") or V.record_of(frozen.engine, const)
            self.assertIsInstance(float(getattr(getattr(frozen.engine, rec9), const)), float)
        inv = T.runs(src, MAZDA)[-1]
        self.assertEqual((inv["subcommand"], inv["outcome"], inv["outside_allowlist"], inv["refused_by_audit"]),
                         ("check", "ok", [], []))
        self.assertTrue(any(o.endswith("derived_params.json") and "engines" not in o for o in inv["opened"]),
                        "the import chain's B58 derived file was opened, and allowed")
        # the plant's identity, each guard alone (WP3's second fix of 23 October 2026, on the test review's finding
        # that both could be deleted with every test passing): a plant one ulp away refuses at arm/plant naming
        # engine_sha, and a freeze.json whose plant_sha moved refuses there naming plant_sha
        os.remove(val_path(r.root, MAZDA, V.ARMED))
        fx.commit_all(r.root, "check's invocation in run.json")

        def one_ulp(name):
            p = built(name)
            if name != MAZDA:
                return p
            import math
            return epa_fit.perturbed(p, record="cycle", field="burn_base",
                                     value=math.nextafter(p.engine.cycle.burn_base, math.inf))
        with fx.pinned_terms(), mock.patch.object(V, "_require_this_tree", lambda ctx, what: []), \
                mock.patch.object(engines, "get", one_ulp), mock.patch.object(split, "compute", lambda: split_result):
            with self.assertRaises(V.Refused) as cm:
                V.arm(MAZDA, source=src, jobs=jobs, data_folder=data, defect=None)
        self.assertTrue(any(x.startswith("arm/plant") and "engine_sha" in x for x in cm.exception.problems),
                        cm.exception.problems)
        fzp = cal_path(r.root, MAZDA, "freeze.json")
        fz0 = read_json(fzp)
        epa_freeze.write_json_atomic(fzp, dict(fz0, plant={"plant_sha": "0" * 64}))
        fx.commit_all(r.root, "freeze.json's plant_sha moved")
        # arm/calibration sees it first, in the records written after the freeze (validate_epa.after_freeze_problems,
        # WP3's third fix of 24 October 2026); with that step's check set aside, arm/plant names it alone
        with self.assertRaises(V.Refused) as cm:
            arm()
        self.assertTrue(any(x.startswith("arm/calibration") and "(plant_sha) freeze.json records" in x
                            for x in cm.exception.problems), cm.exception.problems)
        with mock.patch.object(V, "after_freeze_problems", lambda name, *, freeze, records: []):
            with self.assertRaises(V.Refused) as cm:
                arm()
        self.assertTrue(any(x.startswith("arm/plant") and "plant_sha" in x for x in cm.exception.problems),
                        cm.exception.problems)
        epa_freeze.write_json_atomic(fzp, fz0)
        fx.commit_all(r.root, "freeze.json as it was")
        self.assertEqual(arm()["in_sample_check"]["check_exit"], 0)          # the control: as it was, it arms
        # the control: in_sample.json moved by one number, freeze.json's fits moved with it
        os.remove(val_path(r.root, MAZDA, V.ARMED))
        p = cal_path(r.root, MAZDA, "in_sample.json")
        x = read_json(p)
        st = x["forms"]["A"]["statistics"]
        row = next(k for k, v in st.items() if v["E"] is not None)
        st[row]["E"] = st[row]["E"] + 1e-9
        epa_freeze.write_json_atomic(p, x)
        fz = read_json(cal_path(r.root, MAZDA, "freeze.json"))
        fz["fits"]["in_sample.json"] = common.sha_text(p)
        epa_freeze.write_json_atomic(cal_path(r.root, MAZDA, "freeze.json"), fz)
        comp = read_json(cal_path(r.root, MAZDA, "complete.json"))
        fx.commit_all(r.root, "in_sample.json moved")
        with self.assertRaises(V.Refused) as cm:
            arm()
        self.assertTrue(any(x.startswith("arm/in_sample") and "exited 5" in x and "C11" in x
                            for x in cm.exception.problems), cm.exception.problems)
        self.assertEqual(comp, read_json(cal_path(r.root, MAZDA, "complete.json")))


def dataclass_dict(x):
    import dataclasses
    return dataclasses.asdict(x)


def hand_counts(repo, engine):
    """The held-out counts of decision 54, counted here from the synthetic tables with csv alone (an
    independent count of what epa_rows.held_out_counts converts): fired = BMEP >= 2 bar; lambda missing
    = an empty lambda cell (either HD1 bank); sentinel = spark exactly -120 or empty; Final rows and
    those that publish each; E8's subsets enough at the contract's e8_min_rows."""
    held = fx.held_rows(repo, engine)
    n = dict(fired_lambda_missing=0, fired_spark_sentinel=0, final_rows=0, final_lambda_published=0,
             final_spark_published=0)
    for spec in epa_rows.TABLES[engine]:
        if spec.role == "initial":
            continue
        with open(fx.table_file(repo.root, engine, spec.role, spec.index), newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if int(row["source_row"]) not in held.get(spec.name, []):
                    continue
                fired = float(row["bmep_bar"]) >= 2.0
                lam = [row[c] for c in ("exhaust_lambda", "exhaust_lambda_left", "exhaust_lambda_right") if c in row]
                no_lam = any(c == "" for c in lam)
                sp = row["spark_timing_cad_btdc"]
                sentinel = sp == "" or float(sp) == -120.0
                n["fired_lambda_missing"] += fired and no_lam
                n["fired_spark_sentinel"] += fired and sentinel
                if spec.role == "final":
                    n["final_rows"] += 1
                    n["final_lambda_published"] += not no_lam
                    n["final_spark_published"] += not sentinel
    k = fx.read_contract(repo)["conventions"]["statistic_details"]["e8_min_rows"]
    n = {key: int(v) for key, v in n.items()}
    n["e8_subsets_enough"] = n["final_lambda_published"] >= k and n["final_spark_published"] >= k
    return n


class AuditOfTheRun(Armed):
    """C3 in record mode: what the run opens is inside its allowlist; one file outside it is a coding
    defect that makes the run exit non-zero, recorded in run.json."""

    def test_an_open_outside_the_allowlist_is_a_defect(self):
        r, src = self.armed(engine=FORD)
        stray = os.path.join(r.root, "stray_notes.txt")
        write(stray, "not the run's\n")
        res, out = self.run_(src, FakeCompute(open_=stray), engine=FORD, defect=None)
        self.assertIsInstance(res, SystemExit)
        inv = read_json(val_path(r.root, FORD, V.RUN))["invocations"][0]
        self.assertEqual(inv["outside_allowlist"], ["stray_notes.txt"])
        self.assertTrue(inv["outcome"].startswith("defect"))
        self.assertIn(f"{V.val_dir(FORD)}/{V.ARMED}", inv["opened"])


class HeldOutAssembly(Armed):
    """validate_epa's side of the held-out statistics, on the synthetic held-out rows the real reader
    gives once the engine is armed, with test_epa_fixtures.ToyModel for the plant: the sets each
    u-term needs (crank step halved, each input moved by exactly +-u_j, lambda's u_D) are built so that
    epa_stats.held_out_row accepts them, and every gating row comes back with its u-terms, label and
    kappa. u_D's meter and torque terms are pinned per report (decision 56) with no fallback, and the
    synthetic rows belong to no report (epa_stats refuses them there), so this test gives them synthetic
    terms for its own run."""

    def _rows(self):
        import epa_stats
        r, src = self.armed(engine=MAZDA)
        tok = V.verify_for_validation(MAZDA, source=src, defect=None)
        held = epa_rows.read_held_out(MAZDA, source=src, token=tok)
        points = tuple(x for x in held.rows if isinstance(x, epa_rows.HeldOutRow))
        initial = tuple(x for x in held.rows if isinstance(x, epa_rows.HeldOutInitialRow))
        view = epa_rows.calibration_contract(MAZDA, source=src)
        tight = V.load_tightenings(os.path.join(r.root, *V.TIGHTENINGS_REL.split("/"))).raw
        cens = V.censoring_of({"checks": {"censoring": {
            "censored": False, "min_lambda_cellref": 0.8, "n_at_min_within_1e-9": 1, "documented_floor": None,
            "rule": "synthetic", "final_rows_with_lambda": 9}}})
        pinned = dict(epa_stats.U_D)
        pinned["meter"] = epa_stats.UD(0.01, None, "random", "synthetic", "test_validate_guards", True)
        pinned["torque"] = epa_stats.UD(0.05, None, "random", "synthetic", "test_validate_guards", True)
        return points, initial, view, tight, cens, pinned

    def test_every_gating_row_gets_its_u_terms_and_label(self):
        import epa_stats
        points, initial, view, tight, cens, pinned = self._rows()
        rows = tuple(r for r in epa_stats.ROW_FUNCTIONS if r in view.R)
        with mock.patch.object(epa_stats, "U_D", pinned):
            ev = V._Evals(fx.ToyModel(), points, initial, view=view, conventions=epa_stats.NOMINAL, censoring=cens,
                          jobs=1)
            res = ev.labelled(tight, rows)
        unc = ev.unc()
        keys = {V._key(e) for e in ev.N}
        self.assertEqual(set(unc.evals_0125), keys)
        self.assertEqual({e.dtheta for e in unc.evals_0125.values()}, {ev.dtheta / 2.0})
        self.assertEqual(len(unc.shifted), 2 * len(epa_stats.INPUT_CHANNELS) * len(keys))
        labelled = [r for r in rows if epa_stats.KIND[r] != "descriptive" and not res[r].no_statistic]
        self.assertTrue(labelled)
        for r in labelled:
            self.assertIn(res[r].label, epa_stats.LABEL_ORDER, r)
            self.assertIsNotNone(res[r].u, r)
            self.assertIsNotNone(res[r].kappa, r)
        out = V.json_ready({r: v.as_json() for r, v in res.items()})
        json.dumps(out, allow_nan=False)
        if not res["E1a"].no_statistic:
            self.assertIn(V.c5_recheck_margin(res["E1a"])["worst_line"], res["E1a"].deciding)

    def test_e4b_reads_the_initial_rows_for_its_pair_estimate(self):
        """The contract, section 4, E4b: the Initial-to-Final pair estimate is "reported beside it, descriptive", and
        it needs each hold's Initial window (WP3's third fix of 24 October 2026, on the contract review's finding
        that the held-out run handed E4b the steady and Final rows alone, so the estimate always read no hold). One
        held-out hold's Initial lambda set 0.10 above its Final one: E4b labelled and E4b without u (E6's values) each
        read at least one hold, through rows_for, which HeldOutState.at's shifted path reads too; the control, E4b
        on the steady and Final rows alone, reads none."""
        import epa_stats
        points, initial, view, tight, cens, pinned = self._rows()
        fin = {(r.line, r.hold): r for r in points if r.kind == "final" and r.lam_meas is not None}
        pick = next(i for i, r in enumerate(initial) if (r.line, r.hold) in fin)
        r0 = initial[pick]
        initial = tuple(dataclass_replace(r, lam_meas=fin[(r.line, r.hold)].lam_meas + 0.10) if i == pick else r
                        for i, r in enumerate(initial))
        self.assertEqual(V.rows_for("E4b", ("p",), ("i",)), ("p", "i"))
        self.assertEqual((V.rows_for("E1i", ("p",), ("i",)), V.rows_for("E1a", ("p",), ("i",))), (("i",), ("p",)))
        with mock.patch.object(epa_stats, "U_D", pinned):
            ev = V._Evals(fx.ToyModel(), points, initial, view=view, conventions=epa_stats.NOMINAL, censoring=cens,
                          jobs=1)
            lab = ev.labelled(tight, ("E4b",))["E4b"]
            # values() runs every row function: here those the synthetic view has an R for
            with mock.patch.dict(epa_stats.ROW_FUNCTIONS, {r: f for r, f in epa_stats.ROW_FUNCTIONS.items()
                                                           if r in view.R}, clear=True):
                val = ev.values(tight)["E4b"]
            alone = epa_stats.row_E4b(ev.N, view=view, stage="held_out", tightening=tight)
        self.assertFalse(lab.no_statistic, lab.reason)
        for res in (lab, val):
            self.assertGreaterEqual(res.extra["pair_estimate"]["holds"], 1)
            self.assertIsNotNone(res.extra["pair_estimate"]["value_pct"])
        self.assertEqual(alone.extra["pair_estimate"]["holds"], 0)
        self.assertEqual(lab.E, alone.E, "the Initial rows move E4b's pooled value nowhere")
        # nor its u-terms (WP3_INTERFACES.md 13: "E4b's pooled value and u-terms do not move"; the fourth tests
        # review's finding that only the value was compared): E4b labelled on the steady, Final and Initial rows
        # has the u-terms of E4b labelled on the steady and Final rows alone
        with mock.patch.object(epa_stats, "U_D", pinned):
            alone_u = epa_stats.held_out_row("E4b", ev.N, view=view, tightening=tight, unc=ev.unc()).u
        self.assertEqual(lab.u, alone_u)
        self.assertIsNotNone(r0)

    def test_a_shift_that_is_not_u_j_is_refused_downstream(self):
        """The control: the sets are built from epa_stats.input_shifts, the steps u_input checks; with
        steps of half the size, held_out_row refuses them (mistake 19)."""
        import epa_stats
        points, initial, view, tight, cens, pinned = self._rows()
        halved = {k: dataclass_replace(v, value=v.value / 2.0) for k, v in epa_stats.U_INPUT.items()}
        real = epa_stats.input_shifts
        with mock.patch.object(epa_stats, "U_D", pinned), \
                mock.patch.object(epa_stats, "input_shifts", lambda *, terms=None: real(terms=halved)):
            ev = V._Evals(fx.ToyModel(), points, initial, view=view, conventions=epa_stats.NOMINAL, censoring=cens,
                          jobs=1)
            with self.assertRaises(ValueError):
                ev.labelled(tight, ("E1a",))


def dataclass_replace(x, **kw):
    import dataclasses
    return dataclasses.replace(x, **kw)


class PlantToy(fx.ToyModel):
    """test_epa_fixtures.ToyModel in the place of epa_fit.RowModel on a frozen candidate plant: no EPA
    engine is calibrated, and a real cycle at every row of every E6 probe would take half an hour. Three
    of the toy's laws are coupled to the plant's own constants, each by a known amount, so that an E6 probe
    of the constant reaches the outputs (mistake 25): TIT rises K_UA K per unit of ua_port above the
    base's (E6 rows 1 and 6), torque falls K_BP N m per unit of exh_bp_ratio (row 5), and an enriched row's
    fuel rises with the rich slope (row 9). knock_a, the heating value and the flame terms reach nothing,
    so their rows must come back unmoved: the control beside each moved row. TIT carries a term in MAP
    squared (K_Q) beside the toy's linear one: the synthetic tables' TIT is linear in MAP and blind to
    lambda, and against a model linear in MAP too E4b's data lever sums to exactly zero."""
    K_UA, K_BP, K_SLOPE, K_Q = 2.0, 40.0, 0.5, 0.05
    BASE = {}

    def __init__(self, plant, *, fuels):
        c = plant.engine.cycle
        self.ua, self.ratio, self.slope = float(c.ua_port), float(c.exh_bp_ratio), float(c.ce_rich_slope)
        self.base = dict(self.BASE)          # carried by the instance, so a spawn worker has it too

    def cycle(self, x, *, dtheta):
        import dataclasses
        out = super().cycle(x, dtheta=dtheta)
        b = self.base
        return dataclasses.replace(
            out, egt_c=out.egt_c + self.K_UA * (self.ua - b["ua_port"]) + self.K_Q * (x.map_kpa - 100.0) ** 2 / 100.0,
            torque_nm=out.torque_nm - self.K_BP * (self.ratio - b["exh_bp_ratio"]),
            fuel_gps=out.fuel_gps * (1.0 + self.K_SLOPE * (self.slope - b["ce_rich_slope"]) * (1.0 - x.lam)))


# Version 4's wording, which version 5 kept, of the E6 bands validate_epa.e6_sizes reads its sizes from
# (JSON perturbations_E6 rows 5 and 11, abridged), and of the two C3 inputs c3_eta_and_radius_gap reads
# (row 10's constant; the MD's section 5): the contract's text, which the synthetic contract carries for
# the whole run.
ROW5_BAND = ("+- its fit's standard uncertainty (reported); the visibility probe is sized by consequence: ... else "
             "+-10 %; every d row's probe is +-10 % (version 4, decision 59: d needs agents, ...)")
ROW11_BAND = "+-6.3 K (the B58's input uncertainty, DRIVE_C_RULE_NUMBERS.txt:56)"
ROW9_BAND = "the bracket, else the probe, else +-10 % (+-10 crank degrees for IVC and EVO), abridged"
ROW10_CONSTANT = "the driveline efficiency, 0.92"
MD_RADIUS = ("- **Input uncertainty that no calibration absorbs.** ... on the torque demand; the N/V-to-D3\n"
             "  radius gap, 1.6 % uniform, is ... Together that is\n")


class WorkerOpeningToy(PlantToy):
    """PlantToy that, inside a spawn worker only, opens this test file once: the parent never opens it
    while a run is audited, so its path in run.json shows that a worker's opens reached the record (C3:
    a parent's audit hook does not see a worker; epa_fit.ordered_map carries them back)."""

    def cycle(self, x, *, dtheta):
        import multiprocessing
        if multiprocessing.parent_process() is not None and not _WORKER_OPENED_ONCE:
            with open(os.path.abspath(__file__), "rb"):
                _WORKER_OPENED_ONCE.append(True)
        return super().cycle(x, dtheta=dtheta)


_WORKER_OPENED_ONCE = []


def e2e_contract(c):
    """The synthetic contract made complete for a whole run: R entries (descriptive, None) for the rows the
    fixture's contract leaves out, Tests lists in version 4's form (member, perturbed_by_E6_row), and E6
    rows 5 and 11 in version 4's wording (both kept by version 5)."""
    for p in c["perturbations_E6"]:
        p["band"] = {5: ROW5_BAND, 9: ROW9_BAND, 11: ROW11_BAND}.get(p["n"], p["band"])
    have = {(t["engine"], t["row"]) for t in c["thresholds"]}
    for eng in list(epa_rows.TABLES):
        for row, unit in (("E2b", "%"), ("E3b", "K"), ("E5", "%")):
            if (eng, row) not in have:
                c["thresholds"].append(dict(engine=eng, row=row, R=None, unit=unit, kind="synthetic",
                                            on_fail="synthetic", part="synthetic", quantity="synthetic",
                                            rows="synthetic", statistic="synthetic"))
    c["tests_lists"]["lists"] = {
        "E1a": [{"member": "the burn constants (fitted)", "perturbed_by_E6_row": None},
                {"member": "the back-pressure law", "perturbed_by_E6_row": 5}],
        "E3a": [{"member": "UA_PORT", "perturbed_by_E6_row": 6},
                {"member": "the back-pressure law", "perturbed_by_E6_row": 5}],
        "E4a": [{"member": "UA_PORT", "perturbed_by_E6_row": 6},
                {"member": "the rich slope ce_rich_slope", "perturbed_by_E6_row": 9}],
        "E4b": [{"member": "the rich slope ce_rich_slope", "perturbed_by_E6_row": 9},
                {"member": "the flame terms flame_floor (ASSUMED)", "perturbed_by_E6_row": 9}],
        "E8": []}


class HeldOutRun(Armed):
    """validate_epa.run with its real computation (held_out_outputs) end to end, on the Ford's synthetic
    held-out rows in a temporary repository, the frozen plant a candidate built from the B58's values on
    the Ford's records (no EPA value anywhere) and PlantToy in the place of RowModel: every gating row
    labelled with its u-terms, every E6 row assembled in the same run, section 7 and the C5 margin
    written, the hashes ARMED.json holds in every output, nothing opened outside the allowlist, nothing
    but counts and paths printed, and a second run in another copy giving the same rows (PLAN.md 5.1)."""
    ENGINES = (FORD,)
    contract_edit = staticmethod(e2e_contract)

    @classmethod
    def records(cls, engine, root):
        import engines
        values = fx.b58_values()
        cls.frozen = engines.build_candidate(engine, values)
        PlantToy.BASE = {k: float(values["cycle"][k]) for k in ("ua_port", "exh_bp_ratio", "ce_rich_slope")}
        frozen_vals = {s: values[s] for s in engines.FROZEN_SECTIONS}
        nominal = {"snap": True, "cell_referenced": True, "afr_st": None, "lhv_j_per_kg": None}

        def variant(v, *, cycle=None, conventions=None, knock_factor=None):
            vals = json.loads(json.dumps(frozen_vals))
            vals["cycle"].update(cycle or {})
            rec = {"schema": "epa-e6/1", "row": int(v.split("_")[0]), "variant": v, "form": vals["cycle"]["form"],
                   "values": vals, "frozen_sections_sha256": engines.frozen_sections_sha256(vals), "fit": None}
            if conventions is not None:
                rec["conventions"] = dict(nominal, **conventions)
            if knock_factor is not None:
                rec["knock_factor"] = knock_factor
            return rec
        c = values["cycle"]
        e6 = {"1": variant("1", cycle={"ua_port": c["ua_port"] * 1.05}, conventions={"cell_referenced": False}),
              "2": variant("2", conventions={"afr_st": 14.7}),
              "3": variant("3", conventions={"lhv_j_per_kg": 44.0e6}),
              "7_090": variant("7_090", cycle={"knock_a": c["knock_a"] / 0.90}, knock_factor=0.90),
              "7_110": variant("7_110", cycle={"knock_a": c["knock_a"] / 1.10}, knock_factor=1.10)}
        complete = {"e6_probes": {
            "d_rows": "+-10 %",
            "row5": {"sigma": {"ratio": 0.01, "floor_kpa": 0.5}, "probe": {"ratio": 0.05, "floor_kpa": 2.0},
                     "housing_change_k": 1.0},
            "row6": {"sigma": 1.0, "probe": 4.0, "housing_change_k": 1.0},
            "row9": {"ce_rich_slope": {"method": "probe", "why_not_bracket": "synthetic", "size": 0.1, "sigma": 0.05,
                                       "housing_change_k": 1.0, "load_bearing": True, "worth_r1": None, "worth_b": None},
                     "flame_floor": {"method": "probe", "why_not_bracket": "synthetic", "size": 0.01,
                                     "housing_change_k": 0.0, "load_bearing": False, "worth_r1": None,
                                     "worth_b": None}}},
            "e6_in_use": {"1": {"synthetic": True}}, "e6_row4": {"synthetic": True}, "e6_row13": {"synthetic": True}}
        return {"derived": values, "engine_sha": engines.engine_sha(cls.frozen),
                "frozen": engines.frozen_sections_sha256(values),
                "stage0": {"schema": "epa-stage0/1", "checks": {"censoring": dict(SYNTHETIC_CENSORING)}},
                "e6": e6, "complete": complete}

    def setUp(self):
        super().setUp()
        import engines
        import epa_fit
        import epa_stats
        real_get = engines.get
        pinned = dict(epa_stats.U_D)
        pinned["meter"] = epa_stats.UD(0.01, None, "random", "synthetic", "test_validate_guards", True)
        pinned["torque"] = epa_stats.UD(0.05, None, "random", "synthetic", "test_validate_guards", True)
        self.enterContext(mock.patch.object(engines, "get", lambda n: self.frozen if n == FORD else real_get(n)))
        self.enterContext(mock.patch.object(epa_fit, "RowModel", PlantToy))
        self.enterContext(mock.patch.object(epa_stats, "U_D", pinned))

    def real_run(self, jobs=1):
        r, src = self.armed(engine=FORD)
        res, out = quiet(V.run, FORD, source=src, jobs=jobs, defect=None)
        return r, src, res, out

    def test_the_run_refuses_a_plant_other_than_the_armed_one(self):
        """run's own engine_sha guard (WP3's second fix of 23 October 2026, on the test review's finding that it
        could be deleted with every test passing): engines.get returning another candidate after the arming --
        the frozen plant one ulp away -- crashes the run with the guard's message in its crash record, and no
        rows.json is written. The control is test_the_whole_run_writes_every_row_and_every_E6_row."""
        import engines
        import math
        r, src = self.armed(engine=FORD)
        other = epa_fit.perturbed(self.frozen, record="cycle", field="burn_base",
                                  value=math.nextafter(self.frozen.engine.cycle.burn_base, math.inf))
        real_get = engines.get
        with mock.patch.object(engines, "get", lambda n: other if n == FORD else real_get(n)):
            res, _out = quiet(V.run, FORD, source=src, jobs=1, defect=None)
        self.assertIsInstance(res, SystemExit)
        files = set(os.listdir(val_path(r.root, FORD, "")))
        self.assertNotIn(V.ROWS, files)
        crash = sorted(f for f in files if f.startswith("crash_"))
        self.assertEqual(len(crash), 1, files)
        self.assertIn("ARMED.json records (engine_sha)", read_text(val_path(r.root, FORD, crash[0])))

    def test_the_whole_run_writes_every_row_and_every_E6_row(self):
        import epa_stats
        import re
        r, src, res, out = self.real_run()
        files = set(os.listdir(val_path(r.root, FORD, "")))
        crash = [f for f in files if f.startswith("crash_")]
        self.assertEqual(crash, [], read_text(val_path(r.root, FORD, crash[0])) if crash else "")
        inv = read_json(val_path(r.root, FORD, V.RUN))["invocations"][0]
        self.assertEqual(inv["outside_allowlist"], [], inv["outside_allowlist"])
        self.assertIsInstance(res, dict, out)
        self.assertEqual(res["outcome"], "ok", out)
        self.assertEqual(files, {V.ARMED, V.STARTED, V.ROWS, V.E6, V.RUN})
        self.assertIsNone(re.search(r"\d\.\d", out), out)             # counts and paths only, no statistic
        armed = read_json(val_path(r.root, FORD, V.ARMED))
        rows = read_json(val_path(r.root, FORD, V.ROWS))
        prov = rows["provenance"]
        self.assertEqual(prov["armed_blob"], git(r.root, "rev-parse", f"HEAD:{V.val_dir(FORD)}/{V.ARMED}"))
        self.assertEqual((prov["freeze"]["sha_text"], prov["engine_sha"], prov["derived_sha"], prov["code_sha_text"]),
                         (armed["freeze"]["sha_text"], armed["engine_sha"], armed["derived"]["derived_sha"], armed["code"]))
        self.assertEqual(rows["counts"]["held_out_rows"], fx.read_contract(r)["engines"][FORD]["n_held_out_rows"])
        self.assertEqual(set(rows["rows"]), set(epa_stats.ROW_FUNCTIONS))
        labelled = 0
        for row, v in rows["rows"].items():
            if epa_stats.KIND[row] == "descriptive" or v["no_statistic"]:
                continue
            labelled += 1
            self.assertIn(v["label"], epa_stats.LABEL_ORDER, row)
            self.assertIsNotNone(v["u"]["u_val"], row)
            self.assertIsNotNone(v["kappa"], row)
        self.assertGreater(labelled, 3)
        for k in ("level_850c_label", "drop", "drop_rows", "parts"):
            self.assertIn(k, rows["section7"])
        self.assertIn("margin", rows["c5_recheck_margin"])
        e6 = read_json(val_path(r.root, FORD, V.E6))
        self.assertEqual(set(e6["rows"]), {"1", "2", "3", "4", "5", "6", "7", "8", "9", "11", "12", "13"})  # no D3: no row 10
        self.assertEqual(e6["provenance"], prov)
        # each probe reaches the rows its constant reaches, by the toy's own coupling, and no other
        six = e6["rows"]["6"]["constants"]["ua_port"]["probe"]["+"]
        self.assertNotEqual(six["E3a"], 0.0)
        self.assertEqual(six["E1a"], 0.0)                                       # torque does not see ua_port
        five = e6["rows"]["5"]["constants"]["exh_bp_ratio"]["probe"]["+"]
        self.assertNotEqual(five["E1a"], 0.0)
        self.assertEqual(five["E3a"], 0.0)                                      # TIT does not see the ratio
        self.assertNotEqual(e6["rows"]["1"]["variants"]["1"]["delta_E"]["E3a"], 0.0)
        for v in ("7_090", "7_110"):                                            # knock_a reaches no toy law
            self.assertEqual({x for x in e6["rows"]["7"]["variants"][v]["delta_E"].values() if x is not None}, {0.0})
        self.assertEqual({x for x in e6["rows"]["3"]["variants"]["3"]["delta_E"].values() if x is not None}, {0.0})
        self.assertEqual({x for x in e6["rows"]["9"]["flame_floor"]["delta_E"]["+"].values() if x is not None}, {0.0})
        self.assertTrue(e6["rows"]["9"]["ce_rich_slope"]["retag_identity"])
        # the rich slope's +- its fit's standard uncertainty, reported beside the probe (version 4's row 9); the
        # control, a constant the completion gives no sigma, reports none
        self.assertEqual(e6["rows"]["9"]["ce_rich_slope"]["sigma"], 0.05)
        self.assertTrue(any(x not in (None, 0.0) for x in e6["rows"]["9"]["ce_rich_slope"]["delta_E_sigma"]["+"].values()))
        self.assertIsNone(e6["rows"]["9"]["flame_floor"]["delta_E_sigma"])
        self.assertEqual(e6["sizes_from_the_contract"], {"row11_imt_k": 6.3, "d_rows_probe_relative": 0.1,
                                                         "d_rows_probe_ivc_evo_cad": 10.0})
        # rows 5 and 6 judge their must_move rows (a finding, never a stop); rows.json reports every label as
        # E6 row 12 reads it, and section 7 names P5's absence on the Ford in words
        self.assertIn("must_move_moved", e6["rows"]["5"])
        self.assertIsInstance(e6["rows"]["6"]["findings"], list)
        self.assertEqual(set(rows["reported"]) >= {"E3a", "L0", "D1"}, True)
        self.assertIsInstance(rows["section7"]["parts"]["P5"], str)
        self.assertEqual(rows["c5_recheck_margin"]["margin_unit"], "percent")
        self.assertEqual(sorted(e6["excluded_for_every_listed_constant"]), ["E1a", "E3a", "E4a", "E4b", "E8"])
        self.assertFalse(e6["excluded_for_every_listed_constant"]["E8"])         # E8 is never excluded
        self.assertFalse(e6["excluded_for_every_listed_constant"]["E1a"])        # an unperturbed member counts as not
        # determinism (PLAN.md 5.1): another copy, armed and run through a spawn pool of two workers, gives
        # the same rows and the same E6; the workers' opens reach run.json (C3) and stay inside the allowlist
        import epa_fit
        mine = "<code>/" + os.path.basename(os.path.abspath(__file__))
        self.assertNotIn(mine, inv["opened"])                         # the control: the one-process run
        with mock.patch.object(epa_fit, "RowModel", WorkerOpeningToy):
            r2, _, res2, out2 = self.real_run(jobs=2)
        self.assertIsInstance(res2, dict, out2)
        inv2 = read_json(val_path(r2.root, FORD, V.RUN))["invocations"][0]
        self.assertIn(mine, inv2["opened"])
        self.assertEqual(inv2["outside_allowlist"], [])
        self.assertEqual(read_json(val_path(r2.root, FORD, V.ROWS))["rows"], rows["rows"])
        self.assertEqual(read_json(val_path(r2.root, FORD, V.E6))["rows"], e6["rows"])

    def test_a_retag_that_is_not_the_plant_stops_the_run(self):
        """HANDOFFS.md WP3 item 3: the rich slope's retag is asserted before row 9's probe is read, never
        relaxed. The control is the whole run above, where it holds."""
        import epa_fit
        with mock.patch.object(epa_fit, "retag_identity", lambda plant, *, grid, dtheta: False):
            r, src, res, out = self.real_run()
        self.assertIsInstance(res, SystemExit)
        self.assertIn("crash: RuntimeError", out)
        files = set(os.listdir(val_path(r.root, FORD, "")))
        self.assertEqual(files, {V.ARMED, V.STARTED, "crash_1.txt", V.RUN})
        self.assertIn("retag", read_text(val_path(r.root, FORD, "crash_1.txt")))


class SummaryOfThree(fx.Guarded):
    """summary.json from the three rows.json (WP3_INTERFACES 7.11), a defect re-run's beside its first;
    refused while an engine has none; a rows.json whose section7 lacks a key stops it."""

    def test_the_summary_reads_each_engines_rows_and_its_reruns(self):
        with tempfile.TemporaryDirectory(prefix="summary_") as root:
            git(root, "init", "-q", "-b", "main")
            src = types.SimpleNamespace(root=root)

            def rows(label):
                return {"schema": V.ROWS_SCHEMA, "rows": {"E1a": {"label": "validated", "kappa": 1.0}},
                        "reported": {"E1a": {"label": label, "kappa": 1.0}},
                        "section7": {"level_850c_label": label, "drop": False, "drop_rows": []},
                        "c5_recheck_margin": {"margin": 1.9}}
            for eng in common.EPA_ENGINES[:2]:
                write_json(val_path(root, eng, V.ROWS), rows("validated"))
            with self.assertRaises(V.Refused):                       # the control: the Ford's is missing
                V.summary(source=src)
            write_json(val_path(root, FORD, V.ROWS), rows("off"))
            write_json(val_path(root, MAZDA, "rows_rerun1.json"), rows("limited"))
            write_json(val_path(root, MAZDA, "STARTED_rerun1"), {})
            out = V.summary(source=src)
            self.assertEqual(out["engines"][FORD]["labels"], {"E1a": "off"})
            self.assertEqual(out["engines"][MAZDA]["reruns"]["rows_rerun1.json"]["labels"], {"E1a": "limited"})
            self.assertEqual(len(out["inputs"]), 4)
            self.assertEqual(read_json(os.path.join(root, *V.VAL_REL.split("/"), V.SUMMARY)), out)
            bad = rows("off")
            del bad["section7"]["drop_rows"]
            write_json(val_path(root, FORD, V.ROWS), bad)
            with self.assertRaises(KeyError):
                V.summary(source=src)
            # the labels are the reported ones (E6 row 12 both ways), never rows' snapped ones: without them,
            # the summary stops (the control above reads "off" from `reported` where rows says validated)
            bad = rows("off")
            del bad["reported"]
            write_json(val_path(root, FORD, V.ROWS), bad)
            with self.assertRaises(KeyError):
                V.summary(source=src)


# ------------------------------------------------------------------------------------------ no repo
class Units(fx.Guarded):
    """The pure pieces, each with its control."""

    def test_the_tests_lists_are_counted_by_decision_59s_rule(self):
        lists = {"E1a": [{"member": "the burn and delay constants (fitted)", "perturbed_by_E6_row": None},
                         {"member": "the back-pressure law", "perturbed_by_E6_row": 5}],
                 "E4a": [{"member": "UA_PORT", "perturbed_by_E6_row": 6},
                         {"member": "the rich slope ce_rich_slope", "perturbed_by_E6_row": 9}],
                 "E4b": [{"member": "the rich slope ce_rich_slope", "perturbed_by_E6_row": 9},
                         {"member": "the flame terms flame_lam, flame_width and flame_floor (ASSUMED)",
                          "perturbed_by_E6_row": 9}],
                 "E8": []}
        excl = {5: {"all": {"E1a": True, "E4a": False, "E4b": True}}, 6: {"all": {"E4a": True}},
                9: {"ce_rich_slope": {"E4a": True, "E4b": True}, "flame_lam": {"E4b": True},
                    "flame_width": {"E4b": True}, "flame_floor": {"E4b": False}}}
        by_row, every = V._exclusions({"tests_lists": {"lists": lists}}, excl)
        self.assertEqual(every, {"E1a": False, "E4a": True, "E4b": False, "E8": False})
        self.assertEqual(by_row["E4b"], ["the rich slope ce_rich_slope"])
        excl[9]["flame_floor"]["E4b"] = True                     # the control: every flame term excluded
        self.assertTrue(V._exclusions({"tests_lists": {"lists": lists}}, excl)[1]["E4b"])

    def test_a_sigma_the_fit_does_not_give_is_carried_as_none(self):
        """WP3's integration (23 October 2026): S1 gives no sigma of the floor when every row lies below
        the hinge (amendment D10); complete.json then carries None, which _per_field keeps (float(None)
        would stop the one-shot run) and e6_rows skips; a number is still a number (the control), and a
        mapping of other fields is still refused."""
        f = ("exh_bp_ratio", "exh_bp_min_kpa")
        self.assertEqual(V._per_field({"ratio": None, "floor_kpa": 0.5}, f, "row 5 sigma"),
                         {"exh_bp_ratio": None, "exh_bp_min_kpa": 0.5})
        self.assertEqual(V._per_field({"ratio": 0.25, "floor_kpa": 0.5}, f, "row 5 sigma"),
                         {"exh_bp_ratio": 0.25, "exh_bp_min_kpa": 0.5})
        with self.assertRaises(ValueError):
            V._per_field({"ratio": 0.25}, f, "row 5 sigma")

    def test_row_9s_constants_are_found_in_their_own_record(self):
        import engines
        e = engines.get("b58").engine                    # the B58's own files: no EPA data
        self.assertEqual([V.record_of(e, f) for f in ("conrod", "ivc_deg", "evo_deg", "t_head_k", "ce_rich_slope")],
                         ["geometry", "geometry", "geometry", "cycle", "cycle"])
        with self.assertRaises(KeyError):                # the control: a field no record has
            V.record_of(e, "no_such_constant")

    def test_the_e6_sizes_and_c3_inputs_are_read_from_the_contracts_text(self):
        """e6_sizes and c3_eta_and_radius_gap read version 4's wording (kept by version 5); the efficiency and
        the gap are the generator's own constants (thresholds/contract.py ETA and RADIUS_GAP, which validate_epa
        may not import). The controls: a band or a text that does not state the number is refused."""
        from thresholds import contract as tc
        pert = [{"n": 5, "band": ROW5_BAND}, {"n": 9, "band": ROW9_BAND},
                {"n": 10, "constant": ROW10_CONSTANT, "band": "0.86-0.98 (...)"}, {"n": 11, "band": ROW11_BAND}]
        self.assertEqual(V.e6_sizes({"perturbations_E6": pert}), (6.3, 0.1, 10.0))
        self.assertEqual(V.c3_eta_and_radius_gap({"perturbations_E6": pert}, MD_RADIUS), (tc.ETA, tc.RADIUS_GAP))
        for bad in ([{"n": 5, "band": "+-10 %"}, {"n": 9, "band": ROW9_BAND}, {"n": 11, "band": ROW11_BAND}],
                    [{"n": 5, "band": ROW5_BAND}, {"n": 9, "band": ROW9_BAND}, {"n": 11, "band": "6.3 K"}],
                    [{"n": 5, "band": ROW5_BAND}, {"n": 9, "band": "else +-10 %"}, {"n": 11, "band": ROW11_BAND}]):
            with self.assertRaises(ValueError):
                V.e6_sizes({"perturbations_E6": bad})
        with self.assertRaises(ValueError):
            V.c3_eta_and_radius_gap({"perturbations_E6": pert}, "no radius stated here")
        with self.assertRaises(ValueError):
            V.c3_eta_and_radius_gap({"perturbations_E6": pert}, MD_RADIUS + MD_RADIUS.replace("1.6 %", "1.7 %"))

    def test_the_censoring_is_the_calibrations(self):
        c = {"checks": {"censoring": {"censored": True, "min_lambda_cellref": 0.71, "n_at_min_within_1e-9": 2,
                                      "documented_floor": None, "rule": "r", "final_rows_with_lambda": 20}}}
        got = V.censoring_of(c)
        self.assertEqual((got.censored, got.value, got.n_at_min, got.n_rows), (True, 0.71, 2, 20))
        c["checks"]["censoring"]["censored"] = False
        self.assertIsNone(V.censoring_of(c).value)                # the control: not censored, no value

    def test_the_cap_reads_validated_as_limited_outside_the_provenance(self):
        obj = {"provenance": {"x": "validated"}, "rows": {"A": {"label": "validated", "lines": [{"label": "off"},
                                                                                              {"label": "validated"}]}}}
        capped, changed = V.cap_labels(obj)
        self.assertEqual(capped["rows"]["A"]["label"], "limited")
        self.assertEqual([x["label"] for x in capped["rows"]["A"]["lines"]], ["off", "limited"])
        self.assertEqual(capped["provenance"]["x"], "validated")
        self.assertEqual(sorted(changed), ["/rows/A/label", "/rows/A/lines/1/label"])
        self.assertEqual(V.cap_labels({"rows": {"A": {"label": "untested"}}})[1], [])     # the control

    def test_the_c5_margin_reads_the_worst_deciding_line(self):
        def res(lines, deciding):
            return types.SimpleNamespace(R=1.9, unit="% of the measured torque", deciding=deciding, lines=tuple(
                types.SimpleNamespace(line=ln, E=E, u=types.SimpleNamespace(u_val=u)) for ln, E, u in lines))
        m = V.c5_recheck_margin(res([("a", 1.0, 0.1), ("b", -1.0, 0.4), ("c", 3.0, 0.0)], ("a", "b")))
        self.assertEqual((m["worst_line"], m["margin"]), ("b", max(1.9, 1.0 + 0.8)))   # equal |E|: larger u_val
        self.assertEqual(sorted(m["lines"]), ["a", "b"])                                 # c does not decide
        m2 = V.c5_recheck_margin(res([("a", 1.0, 0.4), ("b", -1.0, 0.1)], ("a", "b")))
        self.assertEqual(m2["worst_line"], "a")                                          # the control
        m3 = V.c5_recheck_margin(res([("a", 2.5, 0.5)], ("a",)))
        self.assertEqual(m3["margin"], 3.5)
        self.assertEqual(V.c5_recheck_margin(res([("a", 2.5, 0.5)], ()))["margin"], 1.9)
        # the fraction beside the percent, which epa_stats.c5_climb takes (and refuses a percent)
        self.assertEqual(m3["margin_fraction"], 3.5 * 1e-2)
        import epa_stats
        with self.assertRaises(ValueError):
            epa_stats.c5_climb([object()], margin=m3["margin"], thin_share=0.5)

    def test_the_tightenings_layout_is_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = {"schema": V.TIGHTENINGS_SCHEMA, "plant": "b58", "roads_sha": "0" * 64, "roads_seed": 7,
                    "L1": {"slope_points_per_K": 0.05, "set": "s", "shift_k": 10, "damage_reading": "d"},
                    "E8": {"k3_pair_change_vs_lambda_roads": [[-0.02, 0.0], [0.0, 0.0], [0.02, 0.0]],
                           "k3_pair_change_vs_spark_roads": [[-0.75, 0.0], [0.0, 0.0], [0.75, 0.0]]},
                    "provenance": {"commit": "c", "code_sha_text": {}, "plant_sha": "p", "engine_sha": "e"}}
            p = os.path.join(tmp, "t.json")
            write_json(p, good)
            t = V.load_tightenings(p)
            contract = {"ecu_strategy_b58": fx.CONTRACT_BLOCKS["ecu_strategy_b58"]}
            b58 = {"plant_sha": "p", "engine_sha": "e"}             # the B58 as built, stood in for here
            self.assertEqual(V.tightening_problems(t, contract, b58=b58), [])
            # WP3's second fix of 23 October 2026 (the contract review's findings): L1's slope is a magnitude,
            # finite and > 0; the provenance's engine_sha and plant_sha are the B58's as built. Each refused, the
            # good record above the control
            for slope in (-0.12, 0.0, 1e400):
                bad = json.loads(json.dumps(good))
                bad["L1"]["slope_points_per_K"] = slope
                write_json(p, bad)
                probs = V.tightening_problems(V.load_tightenings(p), contract, b58=b58)
                self.assertTrue(any("slope_points_per_K" in x for x in probs), (slope, probs))
            for key in ("engine_sha", "plant_sha"):
                probs = V.tightening_problems(t, contract, b58=dict(b58, **{key: "another plant"}))
                self.assertTrue(any(f"provenance.{key}" in x for x in probs), (key, probs))
            for edit in (lambda d: d.pop("plant"), lambda d: d.update(roads_seed=7.0),
                         lambda d: d["E8"].update(k3_pair_change_vs_spark_roads=[[0.0, "x"]]),
                         lambda d: d["L1"].pop("slope_points_per_K"), lambda d: d["provenance"].pop("engine_sha")):
                bad = json.loads(json.dumps(good))
                edit(bad)
                write_json(p, bad)
                with self.assertRaises(ValueError):
                    V.load_tightenings(p)
            bad = json.loads(json.dumps(good))
            bad["plant"] = "mazda_25t"
            bad["E8"]["k3_pair_change_vs_lambda_roads"][0][0] = -0.03
            write_json(p, bad)
            probs = V.tightening_problems(V.load_tightenings(p), contract, b58=b58)
            self.assertEqual(len(probs), 2)

    def test_the_allowlist_holds_the_records_and_not_a_stray_file(self):
        with tempfile.TemporaryDirectory() as root:
            src = types.SimpleNamespace(root=root, engine_dir=os.path.join(root, "t"),
                                        contract_json=os.path.join(root, "c", "k.json"),
                                        contract_md=os.path.join(root, "c", "k.md"))
            write_json(src.contract_json, {"generators": {"sha256": {"thresholds/template.md": "0" * 64}}})
            pats = V.run_allowlist(FORD, source=src, armed={"derived": {"path": "d/x.json"}, "d3": {}})
        ok = [f"{V.val_dir(FORD)}/rows.json", "c/k.json", "t/ford_27tt/anything.csv", "d/x.json", "<python>/x/y.py",
              "thresholds/split.py", "thresholds/template.md", "<code>/engine_specs/ford_27tt.toml", "<code>/epa_fit.py",
              os.path.abspath(os.devnull).replace(os.sep, "/")]
        self.assertEqual(V.outside(ok, pats), [])
        bad = ["t/mazda_25t/x.csv", "results/EPA_VALIDATION/mazda_25t/rows.json", "thresholds/other.md",
               "C:/elsewhere/notes.py", "/elsewhere/x/__pycache__/y.pyc", "<code>/data/" + "engines/ford_27tt/x.csv",
               "<data>/anl-d3-x/1 Test Data.txt"]
        # the controls: another engine's files, a file elsewhere whose name a root pattern's * would cross to,
        # the code tree's data, a D3 file ARMED.json did not hash
        self.assertEqual(V.outside(bad, pats), sorted(bad))

    def test_the_folders_records_are_sorted_into_their_states(self):
        self.assertEqual(V.rerun_name(V.ROWS, 2), "rows_rerun2.json")
        self.assertEqual(V.rerun_name(V.STARTED, 1), "STARTED_rerun1")
        self.assertEqual(V.first_run_names(MAZDA), (V.STARTED, V.ROWS, V.E6, V.RUN, "c3.json"))
        self.assertEqual(V.first_run_names(FORD), (V.STARTED, V.ROWS, V.E6, V.RUN))
        with self.assertRaises(KeyError):
            V._named("b58")                     # the B58 has no held-out validation


def started_before_compute(src):
    """In validate_epa.run, the statement that writes STARTED comes before any statement that calls
    _compute (or binds it)."""
    tree = ast.parse(src)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run")
    first_started = first_compute = None
    for i, stmt in enumerate(fn.body):
        names = {n.id for n in ast.walk(stmt) if isinstance(n, ast.Name)}
        if first_started is None and isinstance(stmt, ast.If) and "reexecution" in names and "started" in names:
            first_started = i
        if first_compute is None and "_compute" in names:
            first_compute = i
    return first_started is not None and first_compute is not None and first_started < first_compute


# ------------------------------------------------------------------------------------------ AST rules
FORBIDDEN_NAMES = ("ENGINE_DIR", "ENGINES_DIR", "CONTRACT_JSON", "CONTRACT_MD")


def real_source_uses(src, rel):
    """C5's AST check: (file, line, what) for every name or attribute that names the real tables'
    folder or the real contract, every call of Source.repository(), and every string constant
    holding the real tables' folder."""
    out = []
    folder = "data" + "/" + "engines"
    for n in ast.walk(ast.parse(src, filename=rel)):
        if isinstance(n, ast.Name) and n.id in FORBIDDEN_NAMES:
            out.append((rel, n.lineno, n.id))
        elif isinstance(n, ast.Attribute) and n.attr in FORBIDDEN_NAMES:
            out.append((rel, n.lineno, n.attr))
        elif isinstance(n, ast.Attribute) and n.attr == "repository":
            out.append((rel, n.lineno, "Source.repository"))
        elif isinstance(n, ast.Constant) and isinstance(n.value, str) and (
                folder in n.value or folder.replace("/", "\\") in n.value):
            out.append((rel, n.lineno, "the tables' folder"))
    return out


def table_name_literals(src, rel):
    """No new .py names a table (amendment C3; WP3_INTERFACES N9): string constants holding the joined
    table-name stems, the pattern built from parts."""
    stems = ("epa_" + "steady", "epa_" + "highload")
    return [(rel, n.lineno) for n in ast.walk(ast.parse(src, filename=rel))
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and any(s in n.value for s in stems)]


class AstRules(fx.Guarded):
    def test_this_file_passes_no_real_source(self):
        src = read_text(os.path.abspath(__file__))
        # FORBIDDEN_NAMES itself is the list, not a use: it is held as strings
        self.assertEqual(real_source_uses(src, "test_validate_guards.py"), [])

    def test_validate_epa_names_no_table_and_no_tables_folder(self):
        src = read_text(os.path.join(HERE, "validate_epa.py"))
        self.assertEqual(table_name_literals(src, "validate_epa.py"), [])
        hits = [h for h in real_source_uses(src, "validate_epa.py") if h[2] != "Source.repository"]
        self.assertEqual(hits, [])
        # Source.repository() is called once, by the command line (WP3_INTERFACES N4: production code)
        self.assertEqual(len([h for h in real_source_uses(src, "validate_epa.py") if h[2] == "Source.repository"]), 1)

    def test_check_exits_are_calibrate_epas_own(self):
        """validate_epa never imports calibrate_epa (N10), so its reading of check's exits is a second copy:
        calibrate_epa.py's EXIT_* assignment read through ast must equal CHECK_EXIT_NAMES, and CHECK_EXITS'
        codes must be those names' codes (WP3's second fix of 23 October 2026, on the test review's finding).
        The control: a renumbered assignment is seen."""
        import ast

        def exits(src):
            for node in ast.parse(src).body:
                if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Tuple)
                        and all(isinstance(t, ast.Name) and t.id.startswith("EXIT_") for t in node.targets[0].elts)):
                    return {t.id: ast.literal_eval(v) for t, v in zip(node.targets[0].elts, node.value.elts)}
            return None
        src = read_text(os.path.join(HERE, "calibrate_epa.py"))
        got = exits(src)
        self.assertEqual({k: v for k, v in got.items() if k != "EXIT_OK"}, V.CHECK_EXIT_NAMES)
        self.assertEqual(got["EXIT_OK"], 0)
        self.assertEqual(sorted(V.CHECK_EXITS), sorted(V.CHECK_EXIT_NAMES.values()))
        self.assertEqual(V.CHECK_MISMATCH, got["EXIT_MISMATCH"])
        moved = src.replace("EXIT_OK, EXIT_CRASH, EXIT_REFUSED, EXIT_DEFECT, EXIT_WAIT, EXIT_MISMATCH = 0, 1, 2, 3, 4, 5",
                            "EXIT_OK, EXIT_CRASH, EXIT_REFUSED, EXIT_DEFECT, EXIT_WAIT, EXIT_MISMATCH = 0, 1, 2, 3, 5, 4")
        self.assertNotEqual(moved, src)
        self.assertNotEqual({k: v for k, v in exits(moved).items() if k != "EXIT_OK"}, V.CHECK_EXIT_NAMES)

    def test_the_scans_can_fail(self):
        bad = ("from thresholds import common\nx = common.ENGINE_" + "DIR\ny = epa_rows.Source.repository()\n"
               "z = 'data" + "/engines/x'\nw = 'epa_" + "steady.csv'\n")
        self.assertEqual(len(real_source_uses(bad, "scratch.py")), 3)
        self.assertEqual(len(table_name_literals(bad, "scratch.py")), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

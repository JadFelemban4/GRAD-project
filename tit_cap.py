"""tit_cap.py -- row 105's cap (decision 62): the highest turbine-inlet temperature on the Ford's calibration Final
rows, with the row that set it, read once through epa_rows.calibration_rows under calibrate_epa's audit, and written
once to results/EPA_TIT_CAP/ford_27tt.json beside its second sensitivity cap, the spec's egt_limit_k.

    python -B tit_cap.py compute --engine ford_27tt [--out PATH]

    --engine is required and must be ford_27tt: decision 62 is the Ford's row (mistake 1: no default engine).
    --out defaults to results/EPA_TIT_CAP/<engine>.json. A record is written once and never overwritten. A path
    inside a git work tree (git rev-parse --show-toplevel of its nearest existing folder) is refused unless that
    tree is the code's or the source's and the path is under its results/EPA_TIT_CAP/, and only from committed,
    clean code (CODE: HASHED and epa_freeze.CODE_HASHED), so that its sha_text names a commit; so never under any
    work tree's results/EPA_CALIBRATION/, results/EPA_VALIDATION/, data/ or logs/. Outside every work tree (a
    scratch folder) it records the code's clean state as it is. Exit codes: 0 written, 2 refused.

Build step 2, ORDER step 5 (docs/build_step_2/ORDER_TO_TRAINING.md, step 5). The rule is row 105's (results/
VALIDATION_DECISIONS.md, row 105): "The cap is the highest TIT on the Ford's calibration Final rows: decision 62's
first option. Its second option, the 1223 K EGT limit (egt_limit_k), becomes a second sensitivity row. Both are
reported, and neither decides a label." Decision 62 (row 62) and its amendment (docs/build_step_2/AMENDMENTS.md,
amendment 62) fixed the two options before commit C; row 105 chose between them after commit C, before any
held-out statistic, and says so. The ECU that applies the cap is tit_cap_ecu.py; this script reads rows and writes
the record, and nothing else. Rows are cited by number, never by line: the decisions file grows.

THE ONE READER (row 105: "the guarantee is the single reader, checked by the test"). Rows come only from
epa_rows.calibration_rows (epa_rows.py:1198), which skips every held-out key in memory before converting a cell
(epa_rows._Pass, epa_rows.py:1170-1172). Of epa_rows this script names only READS_ALLOWED, and calls only
calibration_rows and audit_paths (a path builder that opens nothing). test_tit_cap checks it three ways: an AST
scan (Scans: the epa_rows names, no table named, rule N1 and test_epa_rows' rules, and no open outside
OPEN_ALLOWED, no child process outside PROCESS_ALLOWED, no dynamic import, no getattr, no epa_rows reached through
another module); a run on a synthetic repository with every public function of epa_rows wrapped, whose callers
outside epa_rows must be this script's two calls; and the audit's own refusals at run time (THE AUDIT).

THE AUDIT, OVER THE WHOLE COMMAND (31 October 2026, on the review's findings I1 and S3: the first build watched
only the read, and the audit admits the engine's table files for every subcommand, calibrate_epa.py:376-385). On
the command line a standard-library hook is installed before the first project import (the `__main__` prelude,
as calibrate_epa._prelude installs its audit, calibrate_epa.py:744-763) and records every open and every child
process until compute installs calibrate_epa.install_audit (calibrate_epa.py:704) with SUBCOMMAND, bound to
epa_rows.audit_paths plus the two derived files, as calibrate_epa._paths_for binds it (calibrate_epa.py:1115-1119).
From then to the write: an open of logs/, another engine's folder, results/EPA_VALIDATION/, a generator output or
the team's data folder is refused at once (Audit.forbidden); the engine's own tables and its epa_engine.json are
refused at once (Audit.refuse_tables) while out and the git state are checked; then the audit is sealed
(calibrate_epa.seal_now: the tables, epa_engine.json and the contract refused, a child only git in
SEALED_GIT_SHAPES) for the frozen-plant check, and stays sealed for everything but the one call
epa_rows.calibration_rows, which runs with the seal and the table refusal lifted, and is sealed again after it for
the cap, the second cap and the hashes. The opens before the audit are judged at the end by the same audit's rules
(Audit.forbidden, Audit.allowed), and a child process before it refuses the record. Any refused open or process,
and any path outside the subcommand's allowlist, anywhere in the command, refuses the record; the record carries
both lists. Called from Python (the tests) there is no prelude, and the record says the imports were not watched.
The write itself comes after the audit ends (Audit refuses os.link, LINK_EVENTS, which write_once uses).

WHICH ROWS ARE THE CALIBRATION FINAL ROWS (decision 62, "the Ford's calibration Final rows"). epa_rows builds one
TableSpec of role "final" per engine, the generator's split.ENG[engine]["hlf"], the High Load Final table
(epa_rows._tables_from_split, epa_rows.py:125-132), and its pass yields a FinalRow for every calibration row of
that table and of no other (epa_rows.py:1181); held-out rows are never in the yield (their type, HeldOutRow, is
read_held_out's alone, epa_rows.py:404-407). So the calibration Final rows are the yield's rows of type exactly
FinalRow, from one source; final_rows refuses if their table is not the one role-"final" spec, or if their count
is not the yield's calibration count for it. An Initial row carries no TIT (epa_rows.InitialRow), and a steady row
is not a Final row. thresholds/split.py and calibrate_epa.py decide the table and the refusals, so the record
hashes them with the rest of epa_freeze.CODE_HASHED (provenance.code_sha_text).

THE CHANNEL (mistakes 13, 18, 23). FinalRow.tit_c is EPA's turbine_inlet_temp_c as published, in degC, the gas-side
thermocouple (epa_rows.PointRow, epa_rows.py:336-337; converted by epa_rows._point_fields, the K channels there
get + 273.15 and tit_c does not), the quantity Run 1 fitted the model's egt_c to (epa_fit.py:2067). The cap in K is
tit_c + 273.15, the scale of engine_env's egt_k (engine_env.py:1057) that tit_cap_ecu holds; never the housing
node t_turb. The record carries the Final rows' range of tit_c, so the unit can be checked against the model's
TIT range (tit_cap_ecu.py probe), and, beside the cap and deciding nothing, the highest TIT of each calibration
steady table: a Final TIT is not a steady TIT (row 83; mistake 23).

THE PLANT AND THE CODE. The cap is the frozen Ford's (rows 94 and 102 hold the steps before the plant commit to the
frozen plants): its plant_sha must be its results/EPA_CALIBRATION/ford_27tt/freeze.json's, its engine_sha its
complete.json's, the code running (epa_freeze.code_shas over CODE_HASHED, in this file's tree) freeze.json's
"code" (epa_freeze.code_changes empty, as calibrate_epa's frozen-code guard requires, calibrate_epa.py:1287-1293),
and the source's contract commit freeze.json's "contract" commit, all checked before any row is read, or nothing
is read. The contract block is copied from freeze.json, not read again. Nothing is written under
results/EPA_CALIBRATION/, which the audit would allow (row 105).
"""
import argparse
import datetime
import json
import os
import statistics
import subprocess
import sys
import tomllib

# ---------------------------------------------------------------------------- the prelude (standard library only)
# Every open and every child process from the start of the command line until compute installs calibrate_epa's
# audit, judged there by that audit's rules (THE AUDIT). Installed only when this file is run, before the first
# project import (test_tit_cap.Scans checks the order, as test_calibrate_epa checks calibrate_epa's).
_EARLY = {"installed": False, "on": False, "opened": [], "processes": []}
_EARLY_PROCESS_EVENTS = ("subprocess.Popen", "os.system", "os.exec", "os.spawn", "os.posix_spawn",
                         "_winapi.CreateProcess", "os.startfile")


def _early_hook(event, args):
    if not _EARLY["on"]:
        return
    try:
        if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
            _EARLY["opened"].append(os.path.abspath(os.fsdecode(args[0])))
        elif event in _EARLY_PROCESS_EVENTS:
            _EARLY["processes"].append(f"{event} {args!r}"[:500])
    except Exception:                       # a hook that cannot read an event must not stop what it watches
        _EARLY["processes"].append(f"{event} <unreadable>")


def _prelude():
    sys.addaudithook(_early_hook)
    _EARLY["installed"] = _EARLY["on"] = True


if __name__ == "__main__":
    _prelude()

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import calibrate_epa  # noqa: E402
import derived  # noqa: E402
import engines  # noqa: E402
import epa_freeze  # noqa: E402
import epa_rows  # noqa: E402
from thresholds import common  # noqa: E402

SCHEMA = "epa-tit-cap/2"                     # 2: the audit over the command, the code's and contract's provenance
ENGINES = ("ford_27tt",)                     # decision 62 is the Ford's row
SUBCOMMAND = "tit-cap"                       # the audit's subcommand name (calibrate_epa.Audit takes any)
RECORD_DIR = "results/EPA_TIT_CAP"
HASHED = ("tit_cap.py", "tit_cap_ecu.py", "epa_rows.py")
CODE = tuple(dict.fromkeys(HASHED + epa_freeze.CODE_HASHED))     # committed and clean for a record in the tree
COMPLETE = "complete.json"
EXIT_OK, EXIT_REFUSED = 0, 2
# Every name of epa_rows this script may use. calibration_rows is the only one that reads a row; audit_paths and
# TABLES are paths and names, FinalRow and SteadyRow types, Source the repository, LoaderStop a guard's stop.
READS_ALLOWED = ("calibration_rows", "audit_paths", "TABLES", "FinalRow", "SteadyRow", "Source", "LoaderStop")
# The functions that may open a file (the spec's TOML, the record) and the one that may start a child (git).
OPEN_ALLOWED = ("egt_limit", "write_once")
PROCESS_ALLOWED = ("work_tree_of",)
RULE = ("The cap is the highest TIT on the Ford's calibration Final rows: decision 62's first option. Its second "
        "option, the 1223 K EGT limit (egt_limit_k), becomes a second sensitivity row. Both are reported, and "
        "neither decides a label. (results/VALIDATION_DECISIONS.md, row 105)")
DECISIONS = {"62": "results/VALIDATION_DECISIONS.md, row 62",
             "amendment_62": "docs/build_step_2/AMENDMENTS.md, amendment 62",
             "105": "results/VALIDATION_DECISIONS.md, row 105",
             "order_step": "docs/build_step_2/ORDER_TO_TRAINING.md, step 5"}
WINDOW = ("the command: on the command line every open and child process from before the first project import "
          "(before_the_audit, judged by the audit's rules), then calibrate_epa's audit from compute's start to the "
          "write, the engine's tables refused at once except inside epa_rows.calibration_rows, and sealed for "
          "everything after the git state but that call")


class Refused(Exception):
    """A refusal: the record is not written."""


def audit_paths_for(engine, *, source):
    """The paths the audit binds, as calibrate_epa._paths_for builds them (calibrate_epa.py:1115-1119): epa_rows.
    audit_paths, the engine's derived file and the B58's (derived.B58_PATH, which the import chain reads)."""
    p = dict(epa_rows.audit_paths(engine, source=source))
    p["derived"] = epa_freeze.derived_relpath(engine)
    p["b58_derived_abs"] = os.path.abspath(derived.B58_PATH)
    return p


def _key(r):
    return {"table": r.table, "source_row": int(r.source_row)}


def _highest(rows):
    """The row of the highest tit_c, the first in the yield's order on a tie, and how many rows share it."""
    best = None
    for r in rows:
        if best is None or r.tit_c > best.tit_c:
            best = r
    return best, sum(1 for r in rows if r.tit_c == best.tit_c)


def final_rows(engine, yield_):
    """(the one role-"final" table's name, its calibration Final rows): the yield's rows of type exactly FinalRow,
    refused unless every one is from that table, of origin "epa", with a finite tit_c, and their count is the
    yield's calibration count for the table."""
    specs = [s for s in epa_rows.TABLES[engine] if s.role == "final"]
    if len(specs) != 1:
        raise Refused(f"{engine} has {len(specs)} tables of role final in epa_rows.TABLES, not one")
    name = specs[0].name
    rows = [r for r in yield_.rows if type(r) is epa_rows.FinalRow]
    counts = [c.calibration for c in yield_.counts if c.name == name]
    if not rows:
        raise Refused(f"{engine}: the yield holds no FinalRow")
    if any(r.table != name or r.origin != "epa" for r in rows):
        raise Refused(f"{engine}: a FinalRow from another table, or not the loader's")
    if counts != [len(rows)]:
        raise Refused(f"{engine}: {len(rows)} FinalRow against the yield's calibration count {counts}")
    if not all(isinstance(r.tit_c, float) and r.tit_c == r.tit_c and abs(r.tit_c) != float("inf") for r in rows):
        raise Refused(f"{engine}: a Final row's tit_c is not a finite float")
    return name, rows


def cap_of(engine, yield_):
    """The cap and what the record says beside it, from a Yield: the highest tit_c over the calibration Final rows
    (final_rows) in degC and in K, its row key, line, hold and test cell, how many rows share it; the Final rows'
    tit_c range; and, deciding nothing, each calibration steady table's highest tit_c with its key."""
    name, rows = final_rows(engine, yield_)
    best, ties = _highest(rows)
    tits = [r.tit_c for r in rows]
    beside = []
    for c in yield_.counts:
        if c.role != "steady":
            continue
        st = [r for r in yield_.rows if type(r) is epa_rows.SteadyRow and r.table == c.name]
        if st:
            b, n = _highest(st)
            beside.append({"row_key": _key(b), "test_cell": b.test_cell, "line": b.line, "rows": len(st),
                           "tit_c": b.tit_c, "tit_k": b.tit_c + 273.15, "rows_at_max": n})
    return {
        "cap": {"tit_k": best.tit_c + 273.15, "tit_c": best.tit_c, "row_key": _key(best), "line": best.line,
                "nominal_rpm": int(best.nominal_rpm), "hold": best.hold, "test_cell": best.test_cell,
                "rows_at_max": ties, "unit": "K, tit_c + 273.15 (tit_c degC as published)"},
        "final_rows": {"source": name, "role": "final", "rows": len(rows),
                       "tit_c_min": min(tits), "tit_c_median": statistics.median(tits), "tit_c_max": max(tits),
                       "how_known": "epa_rows.TABLES' one role-final TableSpec (split.ENG[engine]['hlf'], "
                                    "epa_rows.py:125-132) and the yield's rows of type exactly FinalRow "
                                    "(epa_rows.py:1181); held-out keys skipped before conversion (:1170-1172)"},
        "beside_steady_max": {"note": "reported beside the cap, deciding nothing: a Final TIT is not a steady TIT "
                                      "(row 83; mistake 23)", "by_source": beside},
        "rows_read": {"yield_rows": len(yield_.rows), "yield_sha256": yield_.sha256,
                      "manifest_sha256": yield_.manifest.sha256,
                      "by_source": [{"source": c.name, "role": c.role, "calibration_rows": c.calibration}
                                    for c in yield_.counts]},
    }


def _rows_and_cap(engine, *, source, audit):
    """cap_of over the calibration rows, read by the one reader with the seal and the table refusal lifted for that
    call alone, and the audit sealed again after it (THE AUDIT). A loader guard's stop refuses (its message, which
    can name rows, is not passed on, as calibrate_epa.invoke does)."""
    audit.sealed, audit.refuse_tables = False, False
    try:
        yield_ = epa_rows.calibration_rows(engine, source=source)
    except epa_rows.LoaderStop as exc:
        raise Refused(f"a loader guard stopped ({type(exc).__name__})") from None
    finally:
        audit.refuse_tables = True
        calibrate_epa.seal_now()
    return cap_of(engine, yield_)


class _Audited:
    """calibrate_epa's audit for one engine and source, installed, bound and refusing the engine's tables on entry
    (THE AUDIT), ended on exit; a PermissionError the audit raised inside is kept (permission) and decided by
    record(), so that a refusal is a Refused with both lists, never a traceback."""

    def __init__(self, engine, *, source, early):
        self.engine, self.source, self.early = engine, source, early
        self.audit, self.permission = None, None

    def __enter__(self):
        self.audit = calibrate_epa.install_audit(subcommand=SUBCOMMAND, engine=self.engine, root=self.source.root,
                                                 scratch=None)
        try:
            self.audit.bind(audit_paths_for(self.engine, source=self.source))
            self.audit.refuse_tables = True
        except BaseException:
            calibrate_epa.deactivate()
            raise
        return self.audit

    def __exit__(self, exc_type, exc, tb):
        calibrate_epa.deactivate()
        if exc_type is not None and issubclass(exc_type, PermissionError):
            self.permission = str(exc)
            return True
        return False

    def record(self):
        """The audit's record for the cap record, refused (Refused) if the audit refused anything, a path opened
        anywhere in the command is outside the subcommand's allowlist, an open before the audit is one it forbids,
        or a child process ran before it. `opened` and `subprocesses` are the audit's; before_the_audit the
        prelude's opens as the audit records them (the interpreter's own files counted, not listed)."""
        a = self.audit
        opened = sorted(a.opened)
        refused = list(a.refused)
        outside = sorted(p for p in opened if not a.allowed(p))
        rec = {"subcommand": SUBCOMMAND, "window": WINDOW, "opened": opened, "subprocesses": a.subprocesses,
               "refused_by_audit": refused, "outside_allowlist": outside}
        bad = refused + outside
        if self.early is None:
            rec["before_the_audit"] = {"watched": False, "why": "compute called from Python, not the command line: "
                                                               "no prelude watched the imports"}
        else:
            norm = sorted({a.norm(p) for p in self.early["opened"]})
            forbidden = sorted({a.norm(p) for p in self.early["opened"] if a.forbidden(p)})
            e_out = sorted(p for p in norm if not a.allowed(p))
            rec["before_the_audit"] = {"watched": True,
                                       "opened": [p for p in norm if not p.startswith("<python>/")],
                                       "python_files_opened": sum(1 for p in norm if p.startswith("<python>/")),
                                       "subprocesses": list(self.early["processes"]), "forbidden": forbidden,
                                       "outside_allowlist": e_out}
            bad += forbidden + e_out + list(self.early["processes"])
        if self.permission is not None and not refused:
            bad.append(f"a PermissionError the audit's lists do not name: {self.permission}")
        if bad:
            raise Refused(f"the audit refused {len(refused)} and found {len(bad) - len(refused)} other problem(s) "
                          f"(outside the allowlist, forbidden before the audit, a child before it): {bad}")
        return rec


def _early_stop():
    """The prelude's records, its recording stopped, or None when the prelude did not run (called from Python)."""
    if not _EARLY["installed"]:
        return None
    _EARLY["on"] = False
    return {"opened": list(_EARLY["opened"]), "processes": list(_EARLY["processes"])}


def read(engine, *, source):
    """(cap_of's dict, the audit's record): the calibration rows read once under the audit (_Audited, sealed but for
    the one reader's call); refused as _Audited.record refuses. For the tests; compute runs the same read inside its
    own audit."""
    if engine not in ENGINES:
        raise Refused(f"tit_cap reads only {ENGINES} (decision 62 is the Ford's row), not {engine!r}")
    w = _Audited(engine, source=source, early=None)
    out = None
    with w as audit:
        calibrate_epa.seal_now()
        out = _rows_and_cap(engine, source=source, audit=audit)
    return out, w.record()


def egt_limit(engine, plant):
    """The second sensitivity cap: the plant's damage.egt_limit_k, with its spec entry's label, unit and source read
    from engine_specs/<spec>.toml (engines.read_spec drops labels; epa_freeze.spec_labels reads them the same
    way), refused unless the spec's value is the plant's."""
    spec = engines.PLANTS[engine][0]
    path = os.path.join(engines.SPECS, spec + ".toml")
    with open(path, "rb") as fh:
        entry = tomllib.load(fh)["damage"]["egt_limit_k"]
    value = plant.engine.damage.egt_limit_k
    if float(entry["value"]) != value:
        raise Refused(f"{spec}.toml's egt_limit_k {entry['value']!r} is not the plant's {value!r}")
    return {"tit_k": value, "field": "engine.damage.egt_limit_k", "spec": f"engine_specs/{spec}.toml",
            "label": entry.get("label"), "unit": entry.get("unit"), "source": entry.get("source")}


def frozen_provenance(engine, *, root, contract_commit):
    """The plant and the code the cap is computed beside (THE PLANT AND THE CODE): the live plant_sha
    (epa_freeze.plant_sha) and engine_sha (engines.engine_sha of engines.get), refused unless they are root's
    results/EPA_CALIBRATION/<id>/freeze.json plant.plant_sha and complete.json engine_sha (read with
    epa_freeze.read_json, which reads calibration records only); the code running, refused unless
    epa_freeze.code_changes against freeze.json's "code" is empty; the source's contract commit, refused unless it
    is freeze.json's "contract" commit. Returns the plant, and the comparison with both records' sha_text."""
    plant = engines.get(engine)
    live = {"plant_sha": epa_freeze.plant_sha(engine), "engine_sha": engines.engine_sha(plant)}
    fz_path = epa_freeze.freeze_path(engine, root=root)
    cp_path = os.path.join(epa_freeze.calibration_dir(engine, root=root), COMPLETE)
    for p in (fz_path, cp_path):
        if not os.path.isfile(p):
            raise Refused(f"{os.path.relpath(p, root)} does not exist: the cap is the frozen plant's (rows 94, 102)")
    fz = epa_freeze.read_json(fz_path, root=root)
    cp = epa_freeze.read_json(cp_path, root=root)
    want = {"plant_sha": (fz.get("plant") or {}).get("plant_sha"), "engine_sha": cp.get("engine_sha")}
    bad = [f"{k} {live[k]!r} is not the frozen {want[k]!r}" for k in live if live[k] != want[k]]
    code = epa_freeze.code_shas(root=HERE)
    changed = epa_freeze.code_changes(fz.get("code") or {}, root=HERE)
    if changed:
        bad.append(f"the code running differs from the code that froze the plant (freeze.json code): {list(changed)}")
    contract = fz.get("contract") or {}
    if contract.get("commit") != contract_commit:
        bad.append(f"the source's contract commit {contract_commit!r} is not freeze.json's {contract.get('commit')!r}")
    if bad:
        raise Refused(f"{engine}: " + "; ".join(bad))
    return plant, {**live, "freeze_json_plant_sha": want["plant_sha"], "complete_json_engine_sha": want["engine_sha"],
                   "equal": True, "freeze_json_sha_text": common.sha_text(fz_path),
                   "complete_json_sha_text": common.sha_text(cp_path), "freeze_json_versions": fz.get("versions"),
                   "code_sha_text": code, "code_changes_since_freeze": list(changed),
                   "contract": {"freeze_json": contract, "source_contract_commit": contract_commit, "equal": True}}


def _nc(path):
    return os.path.normcase(os.path.abspath(path))


def _inside(path, root):
    try:
        return os.path.commonpath([_nc(path), _nc(root)]) == _nc(root)
    except ValueError:
        return False


def work_tree_of(path):
    """The top level of the git work tree holding `path` (absolute), or None when no work tree holds it: `git
    rev-parse --show-toplevel` in the nearest existing folder of path, which need not exist yet."""
    d = os.path.dirname(os.path.abspath(path))
    while not os.path.isdir(d):
        up = os.path.dirname(d)
        if up == d:
            return None
        d = up
    r = subprocess.run(["git", "-C", d, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    top = r.stdout.strip()
    return os.path.abspath(top) if r.returncode == 0 and top else None


def out_problem(out, *, roots):
    """Why `out` is refused, or None: it exists (a record is written once); or it lies inside a git work tree
    (work_tree_of) that is not one of `roots`' trees (another checkout or worktree of the repository among them);
    or inside one of theirs but not under its RECORD_DIR (so never under results/EPA_CALIBRATION/, results/
    EPA_VALIDATION/, data/ or logs/), or there while CODE is not committed and clean in HERE (code_clean). A root
    git does not know refuses a path inside it the same way."""
    if os.path.exists(out):
        return f"{out} exists: the record is written once and never overwritten"
    try:
        tree = work_tree_of(out)
        trees = {_nc(t): t for t in (work_tree_of(os.path.join(r, "_")) for r in roots) if t}
    except PermissionError as exc:
        return f"{out}: the audit refused the work-tree check ({exc})"
    if tree is None:
        for root in roots:
            if _inside(out, root):
                return f"{out}: inside {root}, which git does not know: a record goes under {RECORD_DIR}/ of a tree"
        return None
    if _nc(tree) not in trees:
        return (f"{out} lies inside the work tree {tree}, which is neither the code's nor the source's: a record "
                f"in a work tree goes into one of those only, under {RECORD_DIR}/")
    rel = os.path.relpath(_nc(out), _nc(tree)).replace(os.sep, "/")
    if not rel.startswith(os.path.normcase(RECORD_DIR).replace(os.sep, "/") + "/"):
        return f"{rel}: inside the work tree a record goes under {RECORD_DIR}/ only"
    clean, dirty = code_clean()
    if not clean:
        return f"{rel}: a record in the work tree names committed code, and {', '.join(dirty)} is not"
    return None


def code_clean():
    """(clean, dirty) of CODE in HERE (epa_freeze.git_clean)."""
    return epa_freeze.git_clean(CODE, root=HERE)


def write_once(path, obj):
    """The record, written once: JSON as common.write_json writes it (indent 1, ASCII, LF), no NaN, to a partial
    file hard-linked into place (os.link), which fails if the target appeared meanwhile, then removed. Returns its
    sha_text. Called after the audit ends (calibrate_epa.LINK_EVENTS)."""
    text = json.dumps(obj, indent=1, ensure_ascii=True, allow_nan=False) + "\n"
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".partial"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    try:
        os.link(tmp, path)
    finally:
        os.remove(tmp)
    return common.sha_text(path)


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def compute(engine, *, source, out, argv):
    """Row 105's record for `engine` from `source`'s calibration rows, written once to `out`; returns the record
    and its sha_text. `argv` is the command line's (None from Python). In this order, all under the audit
    (_Audited): `out` checked (out_problem), the git state and the versions; the audit sealed; the frozen plant,
    code and contract checked (frozen_provenance) before any row is read; the rows read and the cap
    (_rows_and_cap); the second cap (egt_limit); the hashes; then, the audit ended and judged (_Audited.record),
    the record written."""
    if engine not in ENGINES:
        raise Refused(f"tit_cap computes only {ENGINES} (decision 62 is the Ford's row), not {engine!r}")
    w = _Audited(engine, source=source, early=_early_stop())
    started = _now()
    with w as audit:
        why = out_problem(out, roots=(source.root, HERE))
        if why is not None:
            raise Refused(why)
        clean_tree, dirty_tree = epa_freeze.git_clean((".",), root=source.root)
        clean_code, dirty_code = code_clean()
        git = {"commit": epa_freeze.git_head(root=source.root), "code_commit": epa_freeze.git_head(root=HERE),
               "tree_clean": clean_tree, "tree_dirty": list(dirty_tree), "code_clean": clean_code,
               "code_dirty": list(dirty_code), "code_paths": list(CODE)}
        versions = epa_freeze.versions()
        calibrate_epa.seal_now()
        plant, prov = frozen_provenance(engine, root=source.root, contract_commit=source.contract_commit)
        got = _rows_and_cap(engine, source=source, audit=audit)
        second = egt_limit(engine, plant)
        sha = {f: common.sha_text(os.path.join(HERE, f)) for f in HASHED}
    audit_rec = w.record()
    record = {
        "schema": SCHEMA, "plant": engine, "rule": RULE, "decisions": dict(DECISIONS),
        "cap": got["cap"],
        "sensitivity_egt_limit": {**second, "role": "the second sensitivity row (row 105); ASSUMED, carried from "
                                  "the B58"},
        "final_rows": got["final_rows"], "rows_read": got["rows_read"],
        "beside_steady_max": got["beside_steady_max"],
        "audit": audit_rec,
        "sha_text": sha,
        "provenance": prov,
        "versions": versions,
        "versions_equal_freeze_json": versions == prov["freeze_json_versions"],
        "git": git,
        "argv": None if argv is None else list(argv),
        "started_utc": started, "written_utc": _now(),
    }
    return record, write_once(out, record)


def main(argv):
    ap = argparse.ArgumentParser(prog="tit_cap.py", description="row 105's TIT cap (see the docstring)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compute")
    c.add_argument("--engine", required=True)
    c.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    out = args.out or os.path.join(HERE, *RECORD_DIR.split("/"), f"{args.engine}.json")
    try:
        rec, sha = compute(args.engine, source=epa_rows.Source.repository(), out=out, argv=argv)
    except Refused as exc:
        print(f"tit_cap.py compute --engine {args.engine}: refused: {exc}")
        return EXIT_REFUSED
    cap = rec["cap"]
    print(f"tit_cap.py compute --engine {args.engine}: cap {cap['tit_k']!r} K (tit_c {cap['tit_c']!r} degC) at "
          f"{cap['row_key']['table']} source_row {cap['row_key']['source_row']} (line {cap['line']}, hold "
          f"{cap['hold']}, {cap['rows_at_max']} row(s) at the maximum)")
    fr = rec["final_rows"]
    print(f"  Final rows: {fr['rows']} from {fr['source']}; tit_c {fr['tit_c_min']!r} to {fr['tit_c_max']!r} degC, "
          f"median {fr['tit_c_median']!r}; yield {rec['rows_read']['yield_rows']} rows: "
          + ", ".join(f"{s['source']} ({s['role']}) {s['calibration_rows']}" for s in rec["rows_read"]["by_source"]))
    for s in rec["beside_steady_max"]["by_source"]:
        print(f"  beside (deciding nothing): steady {s['row_key']['table']} highest tit_c {s['tit_c']!r} degC at "
              f"source_row {s['row_key']['source_row']} (line {s['line']}, {s['test_cell']})")
    eg = rec["sensitivity_egt_limit"]
    print(f"  second sensitivity cap: {eg['tit_k']!r} K ({eg['field']}, {eg['label']}, {eg['spec']})")
    a = rec["audit"]
    b = a["before_the_audit"]
    print(f"  audit ({a['subcommand']}): {len(a['opened'])} path(s) opened, {len(a['subprocesses'])} subprocess(es), "
          f"{len(a['refused_by_audit'])} refused, {len(a['outside_allowlist'])} outside the allowlist")
    if b["watched"]:
        print(f"  before the audit (the prelude): {len(b['opened'])} project path(s) and {b['python_files_opened']} "
              f"of the interpreter's opened, {len(b['subprocesses'])} subprocess(es), {len(b['forbidden'])} "
              f"forbidden, {len(b['outside_allowlist'])} outside the allowlist")
    for p in a["opened"]:
        print(f"    opened {p}")
    for s in a["subprocesses"]:
        print(f"    subprocess {' '.join(s)}")
    pv, g = rec["provenance"], rec["git"]
    print(f"  plant_sha {pv['plant_sha']} engine_sha {pv['engine_sha']} (freeze.json and complete.json: equal); "
          f"code changes since the freeze {pv['code_changes_since_freeze']}; contract commit "
          f"{pv['contract']['source_contract_commit']} (freeze.json's); commit {g['commit']}, tree clean "
          f"{g['tree_clean']}, code clean {g['code_clean']}")
    print(f"  written {out} (sha_text {sha})")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

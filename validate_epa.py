"""validate_epa.py -- the held-out validation of the three EPA engines, computed ONCE
(build step 2 of decision 24, WP3; written 23 October 2026, run in WP6, commits E and F).

    python -B validate_epa.py arm     --engine <id> --jobs <n> [--defect-rerun "<reason>" --fix-commit <sha>]
    python -B validate_epa.py run     --engine <id> --jobs <n> [--defect-rerun "<reason>" --fix-commit <sha>]
    python -B validate_epa.py summary

    OMP_NUM_THREADS=1 and MKL_NUM_THREADS=1 must be set (PLAN.md 5.1; checked before NumPy loads).

WHY IT EXISTS. results/ENGINE_THRESHOLDS.md (the contract, version 5) section 7: "No refit after
any held-out statistic of an engine has been computed." Refitting then would be tuning on the
validation set (mistake 12). So the held-out statistics are computed once, from an armed commit,
and the code makes a second computation impossible to do unnoticed (amendments C5 and C6,
decision 60). Everything else here serves that sentence.

  arm      checks every precondition of PLAN.md 6.1 as amended: the freeze and completion
           committed and clean; the derived file, the specs and the plant as built (engine_sha)
           equal to the records; the frozen-plant dump bit-identical; `calibrate_epa.py check`
           giving the in-sample stage back byte for byte; the contract equal to the freeze's; the
           code equal to the first fit's or each change listed with its defects.json entry (C10);
           the tightenings committed, their plant the B58 (E5, decision 71); the D3 files hashed
           against the data folder's MANIFEST.csv (decision 63); no earlier run in the tree or in
           `git log --all`; the held-out structure reproduced by the generator's own split.compute
           (C2); the held-out counts of rows without lambda and with the spark sentinel, and
           whether E8's subsets hold enough rows (decision 54). Since WP3's fix of 23 October 2026 also:
           every u_D term a gating row reads and the D3 summary columns pinned; Run 1's proofs (t0.json
           passed, poison.json C8's proof, run.json without an invocation the audit judged a defect);
           check's exit read by name (only its mismatch is C11's "repeat Run 1 from S0"); and on the
           defect route the calibration the previous arming recorded, unchanged (C11: nothing is
           refitted). It prints counts only, writes the arming's nonce into the work tree's own git
           directory and results/EPA_VALIDATION/<id>/ARMED.json. The person commits ARMED.json ALONE:
           that commit is the arming.
  run      refuses (C6) in a linked worktree, without .git, outside the path ARMED.json records,
           unless the output folder holds ARMED.json alone (tracked, untracked and ignored files
           all counted), if `git log --all` holds any other path under that folder, and unless
           ARMED.json is committed at HEAD with hashes that match the tree and the validation code
           committed and clean, unless the arming's nonce is in this work tree's git directory (a clone
           holds none), and when the invocation log records this arming's start while the folder holds
           no STARTED. Then it writes STARTED atomically BEFORE the first held-out read, and the start
           into the invocation log, computes every row once, writes each output atomically, and
           run.json last. Warnings are errors, in every spawn worker too. An exception writes crash_<k>.txt (it counts as written) and prints only the
           exception's type. A run may be executed again only when STARTED is its only record;
           otherwise only the defect route runs (decision 60): the fix committed after the arming,
           ARMED.json re-made by `arm --defect-rerun` (C11), then `run --defect-rerun`, which
           writes *_rerun<k>.json beside the first outputs and caps every label of the re-run at
           limited (section 7: "the second can be labelled limited at best").
  summary  results/EPA_VALIDATION/summary.json from the three engines' rows.json.

WHAT IS PRINTED. Counts, paths, booleans and exception types: no statistic reaches a screen
before the file holding it exists (PLAN.md 6.1), and no figure reaches a .txt verify_docs.py scans
(PLAN.md 8.1). The figures live in the .json outputs.

WHERE THE PIECES LIVE (docs/build_step_2/WP3_INTERFACES.md 5.8). Token and verify_for_validation
are defined HERE, as amendment C3 confines them (the plan put them in epa_freeze.py). Every guard
takes an explicit `source` (epa_rows.Source) and runs every git command in source.root, so each
is tested in a temporary git repository with synthetic tables and contract (C5). The tree-side
hashes ARMED.json records and run compares are epa_freeze.tree_record's, one definition for both
(mistake 10); every JSON output goes through epa_freeze.write_json_atomic. The statistics are
epa_stats.py's, one definition for the in-sample stage and the held-out run (mistake 10); this
file evaluates the held-out rows, takes each row's u-terms and labels from epa_stats' functions,
assembles E6 (e6_rows), runs C3 or C4 through d3_rows.run_chain, and writes the records. The
contract's numbers it needs beyond the view (E6 row 11's shift, the d rows' probe, C3's driveline
efficiency and radius gap) are read from the contract's own text, never retyped (e6_sizes,
c3_eta_and_radius_gap).

REFUSED INVOCATIONS AND `arm` ARE LOGGED OUTSIDE THE GUARDED FOLDER, in
results/EPA_VALIDATION/<id>.invocations.json (chosen here, 23 October 2026). PLAN.md 6.1 asks
run.json to list every invocation and C6 asks the folder to hold ARMED.json alone; a refusal
written into the folder would make the next legitimate run refuse, and a STARTED-only folder stop
being STARTED-only. The run's own run.json, inside the folder, records the invocation that got
past the guards.
"""
import os
import sys

if __name__ == "__main__":
    # PLAN.md 5.1: one BLAS thread, set before NumPy is first imported (epa_freeze imports it below).
    for _var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        if os.environ.get(_var) != "1":
            sys.exit(f"validate_epa.py: {_var} is {os.environ.get(_var)!r}; set it to 1 before running "
                     "(PLAN.md 5.1: one BLAS thread, set before NumPy is imported)")

import argparse
import contextlib
import csv
import dataclasses
import datetime
import fnmatch
import hashlib
import json
import math
import re
import secrets
import subprocess
import traceback
import warnings

import epa_freeze
from thresholds import common

HERE = os.path.dirname(os.path.abspath(__file__))
THIS_FILE = os.path.basename(os.path.abspath(__file__))       # "validate_epa.py", as the code records name it

# ---------------------------------------------------------------------------------------------
# Paths and record names (WP3_INTERFACES 6 and 7; PLAN.md 6.6)
# ---------------------------------------------------------------------------------------------
VAL_REL = "results/EPA_VALIDATION"          # results/EPA_VALIDATION/<id>/ holds one engine's run
CAL_REL = epa_freeze.CALIBRATION_DIR        # calibrate_epa.py's records, read only here
TIGHTENINGS_REL = "results/EPA_TIGHTENINGS.json"   # the roads step's tightenings (PLAN.md WP5; E5)
ARMED = "ARMED.json"
STARTED = "STARTED"
RUN = "run.json"
ROWS = "rows.json"
E6 = "e6.json"
# C3 is the Mazda's (its own driving data), C4's Accord chain the Honda's, and the Ford has no D3
# drive (results/ENGINE_THRESHOLDS.md section 5; PLAN.md 6.5). The keys are the three EPA engines.
D3_OUTPUT = {"mazda_25t": "c3.json", "honda_l15b7": "c4_accord.json", "ford_27tt": None}
SUMMARY = "summary.json"
# The calibration's records the arming requires committed and clean (WP3_INTERFACES 6): every one the
# run reads (stage0.json for the censoring, the e6 files for the refit variants) and fit_A.json, C10's
# record of the code at the first fit; and since WP3's fix of 23 October 2026 the three records Run 1's
# proofs leave, which _arm_calibration reads: t0.json (T0 passed, amendment A1), poison.json (C8's proof,
# mandatory) and run.json (every invocation the audit judged, PLAN.md 5.6).
CAL_RECORDS = ("freeze.json", "complete.json", "stage0.json", "fit_A.json", "in_sample.json", "e6/row1.json",
               "e6/row2.json", "e6/row3.json", "e6/row7_090.json", "e6/row7_110.json", "t0.json", "poison.json",
               "run.json")
# The fit's outputs freeze.json's `fits` must hash (epa_freeze.freeze_record writes stage0.json,
# in_sample.json and fit_<form>.json for every form fitted).
FITS_REQUIRED = ("stage0.json", "in_sample.json", "fit_A.json")

ARMED_SCHEMA = "epa-armed/1"
ROWS_SCHEMA = "epa-rows/1"
E6_SCHEMA = "epa-e6-held-out/1"
C3_SCHEMA = "epa-c3/1"
SUMMARY_SCHEMA = "epa-summary/1"
TIGHTENINGS_SCHEMA = "epa-tightenings/1"

# Decision 71 (amendment E5): L1's tightening, like E8's, is measured on the B58 plant on decision
# 34's roads; an EPA engine's own slope would let its coefficients move its R after its fit.
TIGHTENING_PLANT = "b58"
# The layout of results/EPA_TIGHTENINGS.json, fixed now (PLAN.md WP5; WP3_INTERFACES 7.5), before
# the roads step writes it: each top-level key and its type, and the nested blocks' keys.
TIGHTENINGS_KEYS = {"schema": str, "plant": str, "roads_sha": str, "roads_seed": int, "L1": dict,
                    "E8": dict, "provenance": dict}
TIGHTENINGS_L1_KEYS = {"slope_points_per_K": (float,), "set": (str,), "shift_k": (int, float),
                       "damage_reading": (str,)}
TIGHTENINGS_E8_KEYS = ("k3_pair_change_vs_lambda_roads", "k3_pair_change_vs_spark_roads")
TIGHTENINGS_PROVENANCE_KEYS = ("commit", "code_sha_text", "plant_sha", "engine_sha")

# The D3 data each engine's run reads (decision 63: hashed at the arming against the data folder's
# MANIFEST.csv). The CX-9's 43 first-batch files are the contract's own list (JSON d3_files_c3);
# its summary workbook and the Accord's files are pinned here by folder, against the manifest.
D3_SOURCES = {
    "mazda_25t": {"c3": True, "summary": "anl-d3-2016-mazda-cx9/test-summary", "accord": None},
    "honda_l15b7": {"c3": False, "summary": "anl-d3-2018-honda-accord-lx/test-summary",
                    "accord": "anl-d3-2018-honda-accord-lx/extended-datasets"},
    "ford_27tt": {"c3": False, "summary": None, "accord": None},
}
D3_TEST_FILE = re.compile(r"^[0-9]+ Test Data\.txt$")

# The defect route's cap (results/ENGINE_THRESHOLDS.md section 7; PLAN.md 6.1).
CAP_FROM, CAP_TO = "validated", "limited"

# Section 7's drop order, as text for summary.json.
DROP_ORDER = ("an engine with an off d row, a d row without a statistic, or a failing table whose schedule "
              "cannot carry the exact cycle is dropped; when the schedule forces a choice, the Ford first, then "
              "the Honda, the Mazda last; the B58 is never dropped (results/ENGINE_THRESHOLDS.md section 7)")


class Refused(Exception):
    """A guard refused; .problems lists why. Nothing past the guard was read (C6)."""

    def __init__(self, problems):
        super().__init__("; ".join(problems))
        self.problems = tuple(problems)


@dataclasses.dataclass(frozen=True)
class Token:
    """Issued only by verify_for_validation, after every refusal check passed (PLAN.md 6.1; C3 puts
    it here). epa_rows.read_held_out checks it by its FIELDS and refuses, whatever token it is given,
    unless ARMED.json is committed at HEAD with hashes matching the tree (C5): a token records what
    was verified; it is not a capability a test could forge its way past."""
    engine: str
    armed_blob: str
    head: str
    root: str


@dataclasses.dataclass(frozen=True)
class Defect:
    """The defect route's two arguments (PLAN.md 6.1; decision 60): why, and the commit that fixes it."""
    reason: str
    fix_commit: str


@dataclasses.dataclass(frozen=True)
class Tightenings:
    """results/EPA_TIGHTENINGS.json, parsed and checked (WP3_INTERFACES 7.5). `raw` is the file as
    written, which epa_stats reads by the layout's keys; the fields beside it are the ones the arming
    checks."""
    path: str
    sha_text: str
    plant: str
    roads_sha: str
    roads_seed: int
    l1_slope_points_per_k: float
    e8_lambda_roads: tuple
    e8_spark_roads: tuple
    raw: dict


# ---------------------------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------------------------
def _p(root, rel):
    return os.path.join(root, *rel.split("/"))


def val_dir(name):
    return f"{VAL_REL}/{name}"


def cal_dir(name):
    return f"{CAL_REL}/{name}"


def invocations_rel(name):
    return f"{VAL_REL}/{name}.invocations.json"


def _rel(path, root):
    return os.path.relpath(os.path.abspath(path), os.path.abspath(root)).replace(os.sep, "/")


def _canonical_sha(obj):
    """sha256 of the canonical JSON form engines.frozen_sections_sha256 uses (WP3_INTERFACES 4)."""
    return hashlib.sha256(json.dumps(obj, sort_keys=True, allow_nan=False).encode("utf-8")).hexdigest()


def _write_text_atomic(path, text):
    """A text record (crash_<k>.txt, the one .txt step 2 writes: a traceback and no figure, C6),
    to <path> + epa_freeze.PARTIAL_SUFFIX in the same folder and then os.replace, as
    epa_freeze.write_json_atomic writes JSON. LF line endings."""
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + epa_freeze.PARTIAL_SUFFIX
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.remove(tmp)
        raise


def _load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _now():
    """Wall-clock time: in run.json and the invocation log only (WP3_INTERFACES 2.5)."""
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------------------------
# git in source.root. epa_freeze's helpers where it has one (committed_at_head, is_ancestor,
# git_clean, git_head, head_blob); the queries it has no helper for, here.
# ---------------------------------------------------------------------------------------------
def _git(root, *args):
    return subprocess.run(["git", "-c", "core.quotepath=off", *args], cwd=root, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def _git_out(root, *args):
    r = _git(root, *args)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed in {root}: {r.stderr.strip()}")
    return r.stdout


def _same_path(a, b):
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def _commit(root, rev):
    """The full id of the commit `rev` names in `root`, or None."""
    if not isinstance(rev, str) or not rev.strip():
        return None
    r = _git(root, "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}")
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def committed(root, rel):
    """`rel` is in HEAD's tree in `root` and the working file is that blob (epa_freeze's test)."""
    return epa_freeze.committed_at_head(_p(root, rel), root=root)


def _blob(root, rel):
    return epa_freeze.head_blob(_p(root, rel), root=root)


def _last_commit(root, rel, since=None):
    rng = [f"{since}..HEAD"] if since else []
    out = _git_out(root, "log", "-n", "1", "--format=%H", *rng, "--", rel).strip()
    return out or None


def repository_problems(root):
    """C6's first refusals, and the arming's: no .git; a linked worktree (git-dir is not
    git-common-dir); a root that is not its work tree's top level (a copy placed inside another
    repository would otherwise borrow that repository's history)."""
    if not os.path.exists(os.path.join(root, ".git")):
        return [f"{root} has no .git: a copy of the tree is not the armed repository (C6)"]
    r = _git(root, "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir", "--show-toplevel")
    lines = r.stdout.splitlines()
    if r.returncode != 0 or len(lines) < 3:
        return [f"{root} is not a git work tree: {r.stderr.strip()}"]
    git_dir, common_dir, top = lines[:3]
    out = []
    if not _same_path(git_dir, common_dir):
        out.append(f"{root} is a linked worktree (its git-dir is not its git-common-dir): the validation runs "
                   "in the armed work tree only (C6)")
    if not _same_path(top, root):
        out.append(f"{root} is not its work tree's top level ({top})")
    return out


def folder_files(root, rel_folder):
    """Every file under `rel_folder`, relative to it with forward slashes: on the disk, and every path
    git tracks there or sees untracked or ignored (C6: "counting tracked, untracked and ignored
    files"); a tracked file deleted from the disk still counts."""
    found = set()
    base = _p(root, rel_folder)
    for dp, _dirs, files in os.walk(base):
        for fn in files:
            found.add(os.path.relpath(os.path.join(dp, fn), base).replace(os.sep, "/"))
    prefix = rel_folder.rstrip("/") + "/"
    for path in _git_out(root, "ls-files", "--cached", "--others", "-z", "--", prefix).split("\0"):
        if path.startswith(prefix):
            found.add(path[len(prefix):])
    return sorted(found)


def logged_paths(root, rel_folder):
    """Every path under `rel_folder` a commit reachable from any ref has touched (`git log --all`,
    merges with -m), relative to the folder (C6): epa_freeze.logged_paths, the one definition calibrate_epa's
    refusal to refit after a held-out run reads too."""
    return epa_freeze.logged_paths(root, rel_folder)


def armed_commits(root, name):
    """The commits that added or changed ARMED.json, oldest first: the first is the arming, a later
    one a re-arming on the defect route (C11)."""
    out = _git_out(root, "log", "--reverse", "--format=%H", "--", f"{val_dir(name)}/{ARMED}")
    return [x for x in out.split() if x]


# ---------------------------------------------------------------------------------------------
# The output folder's records (C6; decision 60)
# ---------------------------------------------------------------------------------------------
_RERUN = re.compile(r"^(STARTED|rows|e6|c3|c4_accord|run)_rerun([1-9][0-9]*)(\.json)?$")
_CRASH = re.compile(r"^crash_([1-9][0-9]*)\.txt$")


@dataclasses.dataclass(frozen=True)
class Records:
    """What results/EPA_VALIDATION/<id>/ holds, sorted into the run-once states: the arming, the first
    run's records, each defect re-run's, the crash records with the attempt each names, and anything
    else, which no state allows."""
    files: tuple
    armed: bool
    first: tuple
    reruns: dict
    crashes: dict
    unknown: tuple


def first_run_names(name):
    return (STARTED, ROWS, E6, RUN) + ((D3_OUTPUT[name],) if D3_OUTPUT[name] else ())


def rerun_name(base, k):
    """The defect route's name of a record: rows.json -> rows_rerun<k>.json, STARTED -> STARTED_rerun<k>."""
    stem, ext = os.path.splitext(base)
    return f"{stem}_rerun{k}{ext}"


def read_records(root, name):
    files = folder_files(root, val_dir(name))
    first_ok = set(first_run_names(name))
    first, unknown, reruns, crashes = [], [], {}, {}
    for f in files:
        if f == ARMED:
            continue
        if f in first_ok:
            first.append(f)
            continue
        m = _RERUN.match(f)
        if m and (rerun_name(STARTED if m.group(1) == "STARTED" else m.group(1) + ".json", int(m.group(2))) == f) \
                and (m.group(1) in ("STARTED", "rows", "e6", "run") or D3_OUTPUT[name] == m.group(1) + ".json"):
            reruns.setdefault(int(m.group(2)), []).append(f)
            continue
        m = _CRASH.match(f)
        if m:
            crashes[int(m.group(1))] = _crash_attempt(_p(root, f"{val_dir(name)}/{f}"))
            continue
        unknown.append(f)
    return Records(files=tuple(files), armed=ARMED in files, first=tuple(sorted(first)),
                   reruns={k: tuple(sorted(v)) for k, v in sorted(reruns.items())},
                   crashes=dict(sorted(crashes.items())), unknown=tuple(unknown))


def _crash_attempt(path):
    """The attempt a crash record names on its first line ("attempt: first", "attempt: rerun <k>")."""
    try:
        with open(path, encoding="utf-8") as fh:
            line = fh.readline().strip()
    except OSError:
        return "unreadable"
    return line[len("attempt: "):] if line.startswith("attempt: ") else "unnamed"


def _started_is(root, name, fname, *, blob, k):
    """Whether the STARTED record `fname` is this arming's (its ARMED.json blob) and this attempt's."""
    try:
        s = _load(_p(root, f"{val_dir(name)}/{fname}"))
    except (OSError, ValueError):
        return False
    got = (s.get("defect_rerun") or {}).get("k")
    return s.get("engine") == name and s.get("armed_blob") == blob and got == k


# ---------------------------------------------------------------------------------------------
# Tightenings (PLAN.md WP5; E5; decision 71)
# ---------------------------------------------------------------------------------------------
def load_tightenings(path):
    """Parse results/EPA_TIGHTENINGS.json and check its layout (WP3_INTERFACES 7.5). A missing key, a
    wrong type or an E8 table that is not [[shift, change], ...] raises ValueError naming it. The plant
    is required here and checked against TIGHTENING_PLANT at the arming (E5)."""
    raw = _load(path)
    bad = []
    for key, typ in TIGHTENINGS_KEYS.items():
        if key not in raw:
            bad.append(f"no key {key!r}")
        elif (type(raw[key]) is not int) if typ is int else not isinstance(raw[key], typ):
            bad.append(f"{key!r} is {type(raw[key]).__name__}, not {typ.__name__}")
    tables = {}
    if not bad:
        if raw["schema"] != TIGHTENINGS_SCHEMA:
            bad.append(f"schema {raw['schema']!r}, not {TIGHTENINGS_SCHEMA!r}")
        for key, types_ in TIGHTENINGS_L1_KEYS.items():
            v = raw["L1"].get(key)
            if type(v) not in types_:
                bad.append(f"L1.{key} is {type(v).__name__}, not {'/'.join(t.__name__ for t in types_)}")
        for key in TIGHTENINGS_E8_KEYS:
            v = raw["E8"].get(key)
            if not (isinstance(v, list) and len(v) >= 2 and all(
                    isinstance(p, list) and len(p) == 2 and all(type(x) in (int, float) for x in p) for p in v)):
                bad.append(f"E8.{key} is not a list of [shift, change] pairs")
            else:
                tables[key] = tuple((float(a), float(b)) for a, b in v)
        for key in TIGHTENINGS_PROVENANCE_KEYS:
            if key not in raw["provenance"]:
                bad.append(f"provenance.{key} missing")
    if bad:
        raise ValueError(f"{path}: " + "; ".join(bad))
    return Tightenings(path=path, sha_text=common.sha_text(path), plant=raw["plant"], roads_sha=raw["roads_sha"],
                       roads_seed=raw["roads_seed"], l1_slope_points_per_k=float(raw["L1"]["slope_points_per_K"]),
                       e8_lambda_roads=tables[TIGHTENINGS_E8_KEYS[0]], e8_spark_roads=tables[TIGHTENINGS_E8_KEYS[1]],
                       raw=raw)


def tightening_problems(tight, contract, *, b58):
    """E5 and the shift grids: the tightenings' plant is the B58 (decision 71), and each E8 table's
    shifts are the contract's own B58 grid (ecu_strategy_b58), so the larger response can be taken
    at every shift (decision 57). Since WP3's second fix of 23 October 2026 (the contract review's
    findings): L1's slope_points_per_K is a magnitude, finite and > 0 (the contract's rule, "if it is
    larger than 0.0905, R becomes b/that slope", is about a magnitude: a negative slope made every L1 read
    off and a zero one crashed the run after STARTED); and decision 71's "the held-out run refuses one
    measured on any other [plant]" is checked against the plant itself, not the file's word for it: its
    provenance's engine_sha and plant_sha must be the B58's as this code builds it (`b58`: {"engine_sha",
    "plant_sha"}, b58_identity()). The roads' own sha is compared once the roads step (WP5) names the
    record it commits."""
    out = []
    if tight.plant != TIGHTENING_PLANT:
        out.append(f"the tightenings' plant is {tight.plant!r}, not {TIGHTENING_PLANT!r} (decision 71, amendment E5)")
    slope = tight.l1_slope_points_per_k
    if not (math.isfinite(slope) and slope > 0.0):
        out.append("the tightenings' L1.slope_points_per_K is not a finite magnitude above 0 (points of d per K)")
    prov = (tight.raw or {}).get("provenance") or {}
    for key in ("engine_sha", "plant_sha"):
        if prov.get(key) != b58[key]:
            out.append(f"the tightenings' provenance.{key} is not the B58's as this code builds it (decision 71)")
    strat = contract["ecu_strategy_b58"]
    for mine, theirs in ((tight.e8_lambda_roads, "k3_pair_change_vs_lambda"),
                         (tight.e8_spark_roads, "k3_pair_change_vs_spark")):
        if [p[0] for p in mine] != [float(p[0]) for p in strat[theirs]]:
            out.append(f"the tightenings' E8 table beside {theirs} is not on the contract's shift grid")
    return out


# ---------------------------------------------------------------------------------------------
# run's refusals (C6) and the token (C3, C5)
# ---------------------------------------------------------------------------------------------
def _defect_of(defect):
    if defect is not None and not isinstance(defect, Defect):
        raise TypeError(f"defect is a validate_epa.Defect or None, not {type(defect).__name__}")
    return defect


def refusals(name, *, source, defect):
    """Every reason `run` refuses, as a tuple of strings; empty means it may run (C6, decision 60).

    In order: the repository (no .git, a linked worktree, not the top level); ARMED.json committed at
    HEAD; the armed path (ARMED.json's repo_path is this work tree); the folder's records (normal
    route: ARMED.json alone, or ARMED.json and this arming's STARTED alone, the one re-execution
    allowed; defect route: exactly the earlier attempts' records, committed, and ARMED.json re-made
    for this fix); `git log --all` (no path under the folder that is not present now); every hash
    ARMED.json records, recomputed on the tree (armed_hash_problems), the validation code committed
    and clean among them."""
    _named(name)
    defect = _defect_of(defect)
    root = source.root
    out = repository_problems(root)
    if out:
        return tuple(out)
    rel = f"{val_dir(name)}/{ARMED}"
    if not committed(root, rel):
        return (f"{rel} is not committed at HEAD: arm, commit ARMED.json alone, then run (PLAN.md 6.1; C5)",)
    armed = _load(_p(root, rel))
    blob = _blob(root, rel)
    if armed.get("schema") != ARMED_SCHEMA or armed.get("engine") != name:
        return (f"{rel} is not an {ARMED_SCHEMA} record of {name}",)
    if not isinstance(armed.get("repo_path"), str) or not _same_path(armed["repo_path"], root):
        out.append(f"{root} is not the armed path ARMED.json records (C6: a copy or a moved tree does not run)")
    head0 = _commit(root, armed.get("armed_at_head"))
    if head0 is None or not epa_freeze.is_ancestor(head0, "HEAD", root=root):
        out.append("ARMED.json's armed_at_head is not a commit in HEAD's history")
    if not nonce_matches(root, name, armed):
        out.append("the arming's nonce is not in this work tree's git directory: a clone or a copy of the armed "
                   "commit is not the armed repository (C6)")
    out += folder_problems(name, source=source, armed=armed, blob=blob, defect=defect)
    out += armed_hash_problems(name, source=source, armed=armed)
    return tuple(out)


def _git_dir(root):
    """The absolute git directory of the work tree `root` (git rev-parse --git-dir)."""
    return _git_out(root, "rev-parse", "--path-format=absolute", "--git-dir").strip()


def nonce_path(root, name):
    """Where the arming's nonce lives: the work tree's own git directory, untracked and never cloned, so that a
    clone of the armed commit -- at the same absolute path on another machine, say -- holds no nonce (C6; WP3's
    fix of 23 October 2026, on the isolation review's finding that the path rule alone passes such a clone)."""
    return os.path.join(_git_dir(root), f"epa_armed_{name}")


def nonce_matches(root, name, armed):
    """Whether the work tree's nonce file hashes to ARMED.json's run_once_nonce_sha256."""
    want = armed.get("run_once_nonce_sha256")
    try:
        with open(nonce_path(root, name), "rb") as fh:
            got = hashlib.sha256(fh.read()).hexdigest()
    except (OSError, RuntimeError):
        return False
    return isinstance(want, str) and got == want


def logged_start(root, name, *, blob, k):
    """Whether the invocation log (outside the folder) records the start of a run of the arming whose
    ARMED.json blob is `blob` (attempt k: None for the first run, the re-run's index on the defect route)."""
    return _logged(root, name, event="started", blob=blob, k=k)


def logged_end(root, name, *, blob, k):
    """Whether the invocation log records the end of that run (an "ended" event, written after run.json with
    the sha_text of every output; WP3's second fix of 23 October 2026: the log recorded starts only)."""
    return _logged(root, name, event="ended", blob=blob, k=k)


def logged_writing(root, name, *, blob, k):
    """Whether the invocation log records that run attempt k of the arming `blob` began writing its outputs (a
    "writing" event, appended before the first output is written; WP3's fourth fix of 24 October 2026)."""
    return _logged(root, name, event="writing", blob=blob, k=k)


def _logged(root, name, *, event, blob, k):
    path = _p(root, invocations_rel(name))
    try:
        log = _load(path) if os.path.isfile(path) else {}
    except (OSError, ValueError):
        return True                      # an unreadable log proves nothing absent: refuse
    return any(e.get("event") == event and e.get("armed_blob") == blob and e.get("defect_rerun_k") == k
               for e in log.get("invocations") or [])


def marker_exists(root, name, kind, *, blob):
    """Whether the run-once marker of `kind` ("started", "ended") of the arming `blob` is in the work tree's
    git directory (epa_freeze.run_marker_path): where git clean, git stash and a checkout do not reach, so a
    run whose records were removed from the work tree still shows (WP3's second fix of 23 October 2026)."""
    try:
        return os.path.exists(epa_freeze.run_marker_path(kind, name, blob, root=root))
    except (epa_freeze.GitError, ValueError, OSError):
        return True                      # a marker that cannot be looked for proves nothing absent: refuse


def write_marker(root, name, kind, *, blob, record):
    """Write a run-once marker atomically, once: an existing marker is never rewritten or removed. Returns
    whether this call wrote it."""
    path = epa_freeze.run_marker_path(kind, name, blob, root=root)
    if os.path.exists(path):
        return False
    epa_freeze.write_json_atomic(path, record)
    return True


def folder_problems(name, *, source, armed, blob, defect):
    """C6's folder rule, decision 60's defect route, and the `git log --all` rule."""
    root = source.root
    folder = val_dir(name)
    rec = read_records(root, name)
    out = [f"{folder}/{f} is not a record of this validation (C6: the folder holds ARMED.json alone)"
           for f in rec.unknown]
    rearm = armed.get("rearm")
    if defect is None:
        if rearm is not None:
            out.append("ARMED.json was re-made on the defect route: run --defect-rerun with its reason and fix "
                       "commit (C11)")
        if rec.reruns or rec.crashes or set(rec.first) - {STARTED}:
            out.append(f"{folder} holds an earlier run's records: only the defect route may run now (C6, "
                       "decision 60)")
        elif rec.first == (STARTED,) and not _started_is(root, name, STARTED, blob=blob, k=None):
            out.append("STARTED is not this arming's: it names another ARMED.json")
        elif not rec.first and logged_start(root, name, blob=blob, k=None):
            # the invocation log, outside the folder, holds this arming's start while the folder holds no
            # STARTED: a run started and its STARTED was removed (WP3's fix of 23 October 2026)
            out.append("the invocation log records that this arming's run started, and the folder holds no STARTED: "
                       "only the defect route may run now (C6)")
        # the run-once markers, in the work tree's git directory (WP3's second fix of 23 October 2026): a run
        # that ended may never run again on the normal route, and one that started may run again only from its
        # STARTED alone (a killed process, C6), whatever was removed from the work tree
        if marker_exists(root, name, "ended", blob=blob) or logged_end(root, name, blob=blob, k=None):
            out.append("this arming's run ended (its run-once marker in the work tree's git directory, or the "
                       "invocation log, says so): only the defect route may run now (C6)")
        elif marker_exists(root, name, "writing", blob=blob) or logged_writing(root, name, blob=blob, k=None):
            # a run killed after it began writing its outputs computed the held-out statistics: STARTED alone left
            # in the folder no longer means nothing was computed (WP3's fourth fix of 24 October 2026, on the fourth
            # isolation review's finding)
            out.append("this arming's run began writing its outputs (its run-once marker, or the invocation log, says "
                       "so): the held-out statistics were computed; only the defect route may run now (C6)")
        elif marker_exists(root, name, "started", blob=blob) and not (
                rec.first == (STARTED,) and _started_is(root, name, STARTED, blob=blob, k=None)):
            out.append("this arming's run started (its run-once marker in the work tree's git directory says so), and "
                       "the folder does not hold this arming's STARTED alone: only the defect route may run now (C6)")
        allowed = {ARMED} | set(rec.first)
    else:
        fix = _commit(root, defect.fix_commit)
        commits = armed_commits(root, name)
        k = (rearm or {}).get("k")
        if fix is None:
            out.append(f"the fix commit {defect.fix_commit!r} is not a commit")
        if rearm is None:
            out.append("ARMED.json was not re-made for this defect: `arm --defect-rerun` after the fix commit, "
                       "commit ARMED.json, then run (C11)")
        elif fix is not None and (_commit(root, rearm.get("fix_commit")) != fix or rearm.get("reason") != defect.reason):
            out.append("ARMED.json's re-arming names another fix commit or reason")
        if STARTED not in rec.first:
            out.append("the defect route re-runs a run that started: there is no first STARTED")
        if fix is not None and (not commits or commits[0] == fix
                                or not epa_freeze.is_ancestor(commits[0], fix, root=root)):
            out.append("the fix commit does not descend from the armed commit (PLAN.md 6.1)")
        if fix is not None and not epa_freeze.is_ancestor(fix, "HEAD", root=root):
            out.append("the fix commit is not HEAD or an ancestor of it")
        if type(k) is not int or k < 1:
            out.append("ARMED.json's re-arming carries no re-run index")
        else:
            for i in range(1, k):
                if rerun_name(STARTED, i) not in rec.reruns.get(i, ()):
                    out.append(f"re-run {i} has no STARTED_rerun{i}: re-runs are numbered without a gap")
            later = [i for i in rec.reruns if i > k]
            if later:
                out.append(f"records of later re-runs {later} exist")
            mine = rec.reruns.get(k, ())
            if mine and (mine != (rerun_name(STARTED, k),)
                         or any(a == f"rerun {k}" for a in rec.crashes.values())
                         or not _started_is(root, name, rerun_name(STARTED, k), blob=blob, k=k)):
                out.append(f"re-run {k} has records beyond its STARTED: re-arm for re-run {k + 1}")
            if not mine and logged_start(root, name, blob=blob, k=k):
                out.append(f"the invocation log records that re-run {k} started, and the folder holds no "
                           f"STARTED_rerun{k}: re-arm for re-run {k + 1} (C6)")
            if marker_exists(root, name, "ended", blob=blob) or logged_end(root, name, blob=blob, k=k):
                out.append(f"re-run {k} ended (its run-once marker, or the invocation log, says so): re-arm for "
                           f"re-run {k + 1} (C6)")
            elif marker_exists(root, name, "writing", blob=blob) or logged_writing(root, name, blob=blob, k=k):
                out.append(f"re-run {k} began writing its outputs (its run-once marker, or the invocation log, says "
                           f"so): re-arm for re-run {k + 1} (C6)")
            elif marker_exists(root, name, "started", blob=blob) and mine != (rerun_name(STARTED, k),):
                out.append(f"re-run {k} started (its run-once marker says so), and the folder does not hold its "
                           f"STARTED_rerun{k} alone: re-arm for re-run {k + 1} (C6)")
            keep = list(rec.first) + [f"crash_{j}.txt" for j in rec.crashes] + [
                f for i, fs in rec.reruns.items() if i < k for f in fs]
            for f in keep:
                if not committed(root, f"{folder}/{f}"):
                    out.append(f"{folder}/{f} is not committed: commit the earlier attempts' records before a "
                               "re-run (both results are reported, section 7)")
        allowed = set(rec.files)
    stray = sorted(set(logged_paths(root, folder)) - allowed)
    if stray:
        out.append(f"git log --all holds other paths under {folder}: {', '.join(stray)} (C6)")
    return out


def armed_hash_problems(name, *, source, armed):
    """Every hash ARMED.json records, recomputed now in source.root (C5: "with matching table,
    derived-file and code hashes"; PLAN.md 6.1). The tree side is epa_freeze.tree_record's, the one
    definition the arming used (mistake 10). The step-2 code must be committed and clean. When every
    hash above matches, the calibration records the run reads are checked against freeze.json and
    complete.json (calibration_record_problems)."""
    root = source.root
    out = []
    try:
        tree = epa_freeze.tree_record(name, root=root)
    except (OSError, ValueError, epa_freeze.FreezeRefusal) as exc:
        return [f"the tree's records cannot be hashed: {type(exc).__name__}: {exc}"]
    for key in ("freeze", "complete"):
        if {k: v for k, v in (armed.get(key) or {}).items() if k != "commit"} != tree[key]:
            out.append(f"{key} is not the file ARMED.json records")
    if armed.get("derived") != tree["derived"]:
        out.append("the derived file is not the one ARMED.json records")
    if armed.get("specs") != tree["specs"]:
        out.append("the engine's specs are not the ones ARMED.json records")
    if armed.get("code") != tree["code"]:
        bad = sorted(p for p in set(tree["code"]) | set(armed.get("code") or {})
                     if tree["code"].get(p) != (armed.get("code") or {}).get(p))
        out.append(f"the step-2 code is not the code ARMED.json records: {', '.join(bad)}")
    clean, dirty = epa_freeze.git_clean(sorted(tree["code"]), root=root)
    if not clean:
        out.append(f"the step-2 code is not committed and clean: {', '.join(dirty)}")
    c = armed.get("contract") or {}
    if (common.sha_text(source.contract_json), common.sha_text(source.contract_md)) != (
            c.get("json_sha_text"), c.get("md_sha_text")) or c.get("commit") != source.contract_commit:
        out.append("the contract is not the one ARMED.json records")
    t = armed.get("tightenings") or {}
    tp = _p(root, TIGHTENINGS_REL)
    if not os.path.isfile(tp) or common.sha_text(tp) != t.get("sha_text") or not committed(root, TIGHTENINGS_REL):
        out.append(f"{TIGHTENINGS_REL} is not the committed file ARMED.json records")
    tables = (armed.get("data") or {}).get("tables_sha256") or {}
    if not tables:
        out.append("ARMED.json records no table")
    for tname, want in sorted(tables.items()):
        p = os.path.join(source.engine_dir, name, tname)
        if not os.path.isfile(p) or common.sha_raw(p) != want:
            out.append(f"the table {name}/{tname} is not the one ARMED.json records")
    d3 = armed.get("d3") or {}
    for e in d3_entries(d3):
        p = os.path.join(d3.get("data_folder") or "", *e["file"].split("/"))
        if not os.path.isfile(p) or common.sha_raw(p) != e["sha256"]:
            out.append(f"the D3 file {e['file']} is not the one ARMED.json records")
    if not out:
        out += calibration_record_problems(root, name, freeze=_load(_p(root, tree["freeze"]["path"])),
                                           complete=_load(_p(root, tree["complete"]["path"])))
    return out


def calibration_record_problems(root, name, *, freeze, complete):
    """The calibration records the run reads beyond freeze.json and complete.json, each against the record
    that holds its hash (WP3_INTERFACES 7.2): stage0.json, in_sample.json and every fit_<form>.json against
    freeze.json's `fits`; the five refit variants against complete.json's `e6_files`, whose keys are taken
    as repository-relative paths, as every other `path` of these records is (chosen here, 23 October 2026:
    the layout names no form). freeze.json and complete.json are ARMED.json's, so a record changed after the
    arming is caught through the chain (C5: "with matching table, derived-file and code hashes")."""
    out = []
    fits = freeze.get("fits") or {}
    out += [f"freeze.json's fits records no {b}" for b in FITS_REQUIRED if b not in fits]
    for base, want in sorted(fits.items()):
        p = _p(root, f"{cal_dir(name)}/{base}")
        if not os.path.isfile(p) or common.sha_text(p) != want:
            out.append(f"{cal_dir(name)}/{base} is not the file freeze.json's fits records")
    files = complete.get("e6_files") or {}
    for v in E6_REFIT:
        rel = f"{cal_dir(name)}/e6/row{v}.json"
        p = _p(root, rel)
        if rel not in files:
            out.append(f"complete.json's e6_files records no {rel}")
        elif not os.path.isfile(p) or common.sha_text(p) != files[rel]:
            out.append(f"{rel} is not the file complete.json's e6_files records")
    return out


def d3_entries(d3):
    return list(d3.get("c3_files") or []) + list(d3.get("accord") or []) + ([d3["summary"]] if d3.get("summary") else [])


def verify_for_validation(name, *, source, defect):
    """The Token, issued only when refusals() is empty (PLAN.md 6.1; C3 confines it to this file)."""
    problems = refusals(name, source=source, defect=defect)
    if problems:
        raise Refused(problems)
    return Token(engine=name, armed_blob=_blob(source.root, f"{val_dir(name)}/{ARMED}"),
                 head=epa_freeze.git_head(root=source.root), root=os.path.realpath(source.root))


# ---------------------------------------------------------------------------------------------
# arm (PLAN.md 6.1, as C2, C10, C11, E5 and decisions 54, 63, 71 amend it)
# ---------------------------------------------------------------------------------------------
# Each step reads and fills `ctx` and returns its problems; arm stops at the first step that has
# one, so a step can rely on the records of the steps before it. They are looked up by name when arm
# runs, so a test replaces the steps that build the plant, read the real data folder or run the
# generator with synthetic ones in a temporary repository (C5), and runs every other step as is.
ARM_STEPS = ("repository", "folder", "calibration", "tree", "contract", "contract_guards", "code", "pins",
             "tightenings", "data", "plant", "dump", "rearm", "in_sample", "d3", "structure", "counts")


def arm(name, *, source, jobs, data_folder, defect):
    """Check every precondition and write ARMED.json (WP3_INTERFACES 5.8.2); return the record. Raises
    Refused with the problems of the first step that has any, having written nothing in the folder."""
    _named(name)
    defect = _defect_of(defect)
    if type(jobs) is not int or jobs < 1:
        raise ValueError(f"jobs is a positive int, not {jobs!r} (no default job count)")
    ctx = {"name": name, "source": source, "jobs": jobs, "data_folder": data_folder, "defect": defect,
           "record": {"schema": ARMED_SCHEMA, "engine": name}}
    module = sys.modules[__name__]
    for step in ARM_STEPS:
        problems = getattr(module, "_arm_" + step)(ctx)
        if problems:
            raise Refused([f"arm/{step}: {p}" for p in problems])
    ctx["record"]["versions"] = epa_freeze.versions()
    # the run-once nonce (C6; WP3's fix of 23 October 2026): random bytes in the work tree's own git directory,
    # their sha256 in ARMED.json; run requires the two to match, so no clone or copy of the armed commit runs
    nonce = secrets.token_hex(32)
    ctx["record"]["run_once_nonce_sha256"] = hashlib.sha256(nonce.encode("ascii")).hexdigest()
    _write_text_atomic(nonce_path(source.root, name), nonce)
    epa_freeze.write_json_atomic(_p(source.root, f"{val_dir(name)}/{ARMED}"), ctx["record"])
    return ctx["record"]


def _arm_repository(ctx):
    root = ctx["source"].root
    out = repository_problems(root)
    if not out:
        ctx["record"]["repo_path"] = os.path.realpath(root)
        ctx["record"]["armed_at_head"] = epa_freeze.git_head(root=root)
    return out


def _arm_folder(ctx):
    """Normal route: nothing in the folder but an uncommitted ARMED.json of an earlier attempt to arm;
    no path of the folder in `git log --all`, so no rows.json (PLAN.md 6.1). Defect route (C11): the
    first run's records, and any earlier re-run's, committed; ARMED.json committed; the fix commit
    after the arming and in HEAD's history. The re-arming record names the re-run index k, the reason,
    the fix, the previous ARMED.json's blob and the first arming commit."""
    name, root, defect = ctx["name"], ctx["source"].root, ctx["defect"]
    folder = val_dir(name)
    rec = read_records(root, name)
    logged = set(logged_paths(root, folder))
    out = [f"{folder}/{f} is not a record of this validation" for f in rec.unknown]
    if defect is None:
        if ARMED in logged:
            out.append(f"{folder}/{ARMED} has been committed: the engine is armed; a re-arming is the defect "
                       "route (C11)")
        if rec.first or rec.reruns or rec.crashes:
            out.append(f"{folder} holds a run's records: a run has started (C6)")
        if any(f == ROWS or f.startswith("rows_") for f in logged):
            out.append(f"a rows.json of {name} is in git log --all (PLAN.md 6.1)")
        if logged - {ARMED}:
            out.append(f"git log --all holds paths under {folder}: {', '.join(sorted(logged - {ARMED}))}")
        return out
    if not committed(root, f"{folder}/{ARMED}"):
        out.append("the defect route re-arms an armed engine: ARMED.json is not committed")
    if STARTED not in rec.first:
        out.append("no first run started: there is nothing for the defect route to re-run")
    for f in list(rec.first) + [f"crash_{j}.txt" for j in rec.crashes] + [
            f for fs in rec.reruns.values() for f in fs]:
        if not committed(root, f"{folder}/{f}"):
            out.append(f"{folder}/{f} is not committed: commit the run's records first")
    fix = _commit(root, defect.fix_commit)
    commits = armed_commits(root, name)
    if fix is None:
        out.append(f"the fix commit {defect.fix_commit!r} is not a commit")
    elif not commits or commits[0] == fix or not epa_freeze.is_ancestor(commits[0], fix, root=root):
        out.append("the fix commit does not descend from the armed commit (PLAN.md 6.1)")
    elif not epa_freeze.is_ancestor(fix, "HEAD", root=root):
        out.append("the fix commit is not HEAD or an ancestor of it")
    if not defect.reason.strip():
        out.append("the defect route states its reason")
    if not out:
        k = 1 + sum(1 for fs in rec.reruns.values() if any(f.startswith(STARTED) for f in fs))
        ctx["record"]["rearm"] = {"k": k, "reason": defect.reason, "fix_commit": fix,
                                  "previous_armed_blob": _blob(root, f"{folder}/{ARMED}"),
                                  "first_armed_commit": commits[0]}
        # the arming this one re-makes, as committed: _arm_rearm compares the calibration with it
        ctx["previous_armed"] = _load(_p(root, f"{folder}/{ARMED}"))
    return out


def _arm_calibration(ctx):
    """The calibration's records committed and clean (PLAN.md 6.1 "the freeze and completion are
    committed and clean"); freeze.json, complete.json and fit_A.json read; the frozen sections the
    same in both records; every other record the run reads hashing to the record that holds it
    (calibration_record_problems)."""
    root, name = ctx["source"].root, ctx["name"]
    out = [f"{cal_dir(name)}/{rel} is not committed and clean" for rel in CAL_RECORDS
           if not committed(root, f"{cal_dir(name)}/{rel}")]
    if out:
        return out
    load = lambda rel: _load(_p(root, f"{cal_dir(name)}/{rel}"))     # noqa: E731
    ctx["freeze"], ctx["complete"], ctx["fit_A"] = load("freeze.json"), load("complete.json"), load("fit_A.json")
    dp = _p(root, f"{cal_dir(name)}/defects.json")
    if os.path.isfile(dp) and not committed(root, f"{cal_dir(name)}/defects.json"):
        out.append(f"{cal_dir(name)}/defects.json is not committed and clean")
    ctx["defects"] = _load(dp) if os.path.isfile(dp) else []
    # the freeze's flags, the all-row depth edge among them, carried into ARMED.json (WP3's second fix of 23
    # October 2026: FS4 is shown where the held-out run is armed)
    ctx["record"]["fit_flags"] = list(ctx["freeze"].get("flags") or [])
    ctx["record"]["all_row_depth_edge"] = ctx["freeze"].get("all_row_depth_edge")
    if ctx["complete"].get("frozen_sections_sha256") != ctx["freeze"].get("frozen_sections_sha256"):
        out.append("complete.json's frozen_sections_sha256 is not freeze.json's: a frozen section moved")
    out += calibration_record_problems(root, name, freeze=ctx["freeze"], complete=ctx["complete"])
    # Run 1's proofs, each the record the step after it required (epa_freeze's one definition of each,
    # WP3's fix of 23 October 2026): T0 passed or its failure logged; C8's poison proof complete and equal
    # at the frozen sections; no invocation since the last defect route crashed, mismatched or opened a
    # path outside its allowlist
    import epa_rows
    ctx["t0"] = load("t0.json")
    out += epa_freeze.t0_problems(ctx["t0"])
    import epa_fit
    out += epa_freeze.poison_problems(load("poison.json"), engine=name,
                                      frozen_sections_sha256=ctx["freeze"].get("frozen_sections_sha256"),
                                      poisons=tuple(epa_rows.POISONS), run_keys=epa_fit.POISON_RUN_KEYS,
                                      stages=epa_fit.poison_run_stages(), tied_of=epa_fit.poison_tied_stages)
    out += epa_freeze.audit_problems(load("run.json"), subcommands=epa_freeze.AUDITED_SUBCOMMANDS)
    out += after_freeze_problems(name, freeze=ctx["freeze"],
                                 records={rel: load(rel) for rel in after_freeze_records()})
    return out


def after_freeze_records():
    """The records of the steps after the freeze -- poison.json, the five refit variants, complete.json -- each
    of which carries its subcommand's provenance (calibrate_epa._with_provenance)."""
    return ("poison.json",) + tuple(f"e6/row{v}.json" for v in E6_REFIT) + ("complete.json",)


def after_freeze_problems(name, *, freeze, records):
    """The records `records` ({rel: record}, after_freeze_records) written by the code and the plant freeze.json
    records, from committed and clean step-2 code (WP3's third fix of 24 October 2026, on the Run 1 review's
    finding that an edit made during e6 or complete and reverted before the arming left refit variants, a K3
    knee, a floor and a table no commit reproduces). calibrate_epa.py's poison, e6 and complete refuse on code
    or a plant other than the freeze's, so no defect route keeps the freeze and changes the code before the
    completion: no defects.json entry excuses a difference here."""
    code = freeze.get("code") or {}
    psha = (freeze.get("plant") or {}).get("plant_sha")
    out = []
    for rel in after_freeze_records():
        prov = (records.get(rel) or {}).get("provenance") or {}
        where = f"{cal_dir(name)}/{rel}"
        if not code or prov.get("code_sha_text") != code:
            out.append(f"{where} was not written by the step-2 code freeze.json records (C10)")
        if psha is None or prov.get("plant_sha") != psha:
            out.append(f"{where} was not written on the plant (plant_sha) freeze.json records")
        if (prov.get("git") or {}).get("step2_clean") is not True:
            out.append(f"{where} was written from step-2 code that was not committed and clean")
    return out


def _arm_tree(ctx):
    """epa_freeze.tree_record: freeze.json, complete.json, the derived file, the specs and the step-2
    code as the tree holds them; the derived file committed, and its record complete.json's (the
    final file, frozen and completion sections, PLAN.md 5.9 item 10)."""
    root, name = ctx["source"].root, ctx["name"]
    try:
        tree = epa_freeze.tree_record(name, root=root)
    except (OSError, ValueError, epa_freeze.FreezeRefusal) as exc:
        return [f"the tree's records cannot be hashed: {type(exc).__name__}: {exc}"]
    out = []
    d = tree["derived"]
    if d is None or not committed(root, d["path"]):
        out.append("the derived file is not committed and clean")
    elif d != ctx["complete"].get("derived"):
        out.append("the derived file is not the one complete.json records")
    for key in ("freeze", "complete"):
        tree[key] = dict(tree[key], commit=_last_commit(root, tree[key]["path"]))
    ctx["tree"] = tree
    ctx["record"].update(freeze=tree["freeze"], complete=tree["complete"], derived=d, specs=tree["specs"])
    return out


def _arm_contract(ctx):
    """The contract's sha_text equal to the freeze's, and its commit the source's (PLAN.md 6.1)."""
    src, fr = ctx["source"], ctx["freeze"].get("contract") or {}
    j, m = common.sha_text(src.contract_json), common.sha_text(src.contract_md)
    out = []
    if (j, m) != (fr.get("json_sha_text"), fr.get("md_sha_text")):
        out.append("the contract's sha_text is not freeze.json's")
    if fr.get("commit") != src.contract_commit:
        out.append("freeze.json's contract commit is not the source's")
    ctx["contract"] = _load(src.contract_json)
    ctx["record"]["contract"] = {"commit": src.contract_commit, "json_sha_text": j, "md_sha_text": m,
                                 "schema": ctx["contract"].get("schema")}
    return out


def _arm_contract_guards(ctx):
    """epa_rows' guards 1 and 2 (PLAN.md 4.2): the contract equals its commit's blobs, that commit is
    in HEAD's history, the schema is 4 (version 4's, which version 5 kept), the generators hash to the
    contract's record."""
    import epa_rows
    try:
        epa_rows.check_contract(source=ctx["source"])
    except epa_rows.LoaderStop as exc:
        return [f"the contract's guards stop: {exc}"]
    return []


def _arm_code(ctx):
    """C10: the step-2 code now against fit_A.json's record of the first fit and freeze.json's; every
    change since the first fit's git_head listed with its defects.json entry (the change's last commit
    since the fit is that entry's fix commit); the code committed and clean. validate_epa.py must be in
    the recorded code, "so it was committed before the first fit" (PLAN.md 6.1)."""
    root = ctx["source"].root
    prov = ctx["fit_A"].get("provenance") or {}
    fit_head = _commit(root, (prov.get("git") or {}).get("head"))
    fit_code = prov.get("code_sha_text") or {}
    # T0 certified the fitting code it ran on (amendment A1), so every change since t0.json's head is listed
    # too (WP3's second fix of 23 October 2026, on the fit review's finding); T0 runs before the fit, so its
    # head is the earlier
    t0p = (ctx.get("t0") or {}).get("provenance") or {}
    t0_head = _commit(root, (t0p.get("git") or {}).get("head"))
    t0_code = t0p.get("code_sha_text") or {}
    now = ctx["tree"]["code"]
    if fit_head is None:
        return ["fit_A.json records no git head of the first fit that is a commit here (C10)"]
    out = []
    if t0_head is None:
        out.append("t0.json records no git head of T0 that is a commit here (amendment A1)")
    elif not epa_freeze.is_ancestor(t0_head, fit_head, root=root):
        out.append("t0.json's head is not an ancestor of the first fit's: T0 did not certify the code before it")
    # every defects.json entry in the layout calibrate_epa.py writes (epa_freeze.defect_entry_problems, the
    # one definition; WP3's second fix of 23 October 2026, on the test review's finding)
    for i, e in enumerate(ctx["defects"], 1):
        bad = epa_freeze.defect_entry_problems(e)
        if bad:
            out.append(f"defects.json entry {i} is not in calibrate_epa.py's layout: {'; '.join(bad)}")
    if THIS_FILE not in fit_code:
        out.append(f"{THIS_FILE} is not in the code recorded at the first fit: the validation was not frozen with it")
    clean, dirty = epa_freeze.git_clean(sorted(now), root=root)
    if not clean:
        out.append(f"the step-2 code is not committed and clean: {', '.join(dirty)}")
    fixes = {}
    for e in ctx["defects"]:
        c = _commit(root, str(e.get("fix_commit", "")))
        if c:
            fixes[c] = e.get("k")
    changes = []
    since = t0_head if t0_head is not None else fit_head
    for rel in sorted(set(epa_freeze.code_changes(fit_code, root=root))
                      | set(epa_freeze.code_changes(ctx["freeze"].get("code") or {}, root=root))
                      | (set(epa_freeze.code_changes(t0_code, root=root)) if t0_code else set())):
        last = _last_commit(root, rel, since=since)
        if last is None or last not in fixes:
            out.append(f"{rel} changed since the first fit without its defects.json entry (C10)")
        else:
            changes.append({"path": rel, "defect_k": fixes[last], "fix_commit": last})
    ctx["record"]["code"] = now
    ctx["record"]["code_changes_since_fit"] = changes
    return out


def _arm_pins(ctx):
    """Nothing the one-shot run reads left unpinned (WP3's fix of 23 October 2026, on the contract review's
    finding): every u_D term a gating row reads (epa_stats.unpinned_u_d, decision 56) and, on an engine with a
    D3 chain, the summary workbook's columns (d3_rows.unpinned_for). Either would stop the held-out run after
    STARTED, leaving only the defect route with its labels capped at limited; each is named."""
    import d3_rows
    import epa_stats
    name = ctx["name"]
    out = [f"u_D's {t!r} term is not pinned (decision 56), and the gating rows {', '.join(rows)} read it"
           for t, rows in epa_stats.unpinned_u_d(terms=epa_stats.U_D).items()]
    out += [f"{name}'s D3 summary column {k!r} is not pinned (WP3_INTERFACES 11)" for k in d3_rows.unpinned_for(name)]
    if not out:
        ctx["record"]["pins"] = {"u_D": "every term a gating row reads is pinned",
                                 "d3_summary": "pinned" if name in d3_rows.SUMMARY_FOR else "no D3 chain"}
    return out


def _arm_tightenings(ctx):
    """results/EPA_TIGHTENINGS.json committed and clean (the contract's order_of_work: the roads and
    their tightenings come before the held-out run), its layout, its plant the B58 (E5, decision 71),
    its E8 shifts on the contract's grids."""
    root = ctx["source"].root
    if not committed(root, TIGHTENINGS_REL):
        return [f"{TIGHTENINGS_REL} is not committed and clean (the roads step comes first)"]
    try:
        tight = load_tightenings(_p(root, TIGHTENINGS_REL))
    except ValueError as exc:
        return [str(exc)]
    ctx["record"]["tightenings"] = {"path": TIGHTENINGS_REL, "sha_text": tight.sha_text,
                                    "commit": _last_commit(root, TIGHTENINGS_REL), "plant": tight.plant}
    return tightening_problems(tight, ctx["contract"], b58=b58_identity())


def b58_identity():
    """The B58 as this code builds it: {"engine_sha": engines.engine_sha(engines.get("b58")), "plant_sha":
    epa_freeze.plant_sha("b58")}, what the tightenings' provenance must hold (decision 71)."""
    import engines
    return {"engine_sha": engines.engine_sha(engines.get(TIGHTENING_PLANT)),
            "plant_sha": epa_freeze.plant_sha(TIGHTENING_PLANT)}


def _arm_data(ctx):
    """The tables' raw sha256 (after epa_rows' table guard), epa_engine.json's, epa_channels.csv's blob
    and the manifest (epa_freeze.data_shas), equal to the calibration's record in freeze.json."""
    data = json.loads(json.dumps(epa_freeze.data_shas(ctx["name"], source=ctx["source"])))
    ctx["record"]["data"] = data
    if _canonical_sha(ctx["freeze"].get("data")) != _canonical_sha(data):
        return ["the tables' hashes are not the ones freeze.json recorded"]
    return []


def _require_this_tree(ctx, what):
    """The plant and the split are computed by this process's own modules, so they are the armed
    tree's only when source.root is this file's tree (the CLI's epa_rows.Source.repository())."""
    if not _same_path(ctx["source"].root, HERE):
        return [f"{what} is computed by the armed tree's own code: run arm in {ctx['source'].root}"]
    return []


def _arm_plant(ctx):
    """engines.get(name) builds (engines._check_freeze compares the frozen sections with freeze.json),
    its engine_sha equals complete.json's, and the plant's code and specs (plant_sha) equal
    freeze.json's."""
    out = _require_this_tree(ctx, "the plant")
    if out:
        return out
    import engines
    name = ctx["name"]
    plant = engines.get(name)
    sha = engines.engine_sha(plant)
    if sha != ctx["complete"].get("engine_sha"):
        out.append("engine_sha of the plant as built is not complete.json's")
    psha = epa_freeze.plant_sha(name)
    if psha != (ctx["freeze"].get("plant") or {}).get("plant_sha"):
        out.append("the plant's code and specs (plant_sha) are not freeze.json's")
    ctx["plant"] = plant
    ctx["record"]["engine_sha"] = sha
    ctx["record"]["plant_sha"] = psha
    return out


def _arm_dump(ctx):
    """The frozen-plant dump recomputed now is bit-identical to complete.json's (PLAN.md 6.1, 5.8). A
    difference after the roads step repeats Run 1 from S0, and the guard is never relaxed (C11)."""
    dump = epa_freeze.frozen_plant_dump(ctx["plant"])
    ctx["record"]["dump_sha256"] = dump.sha256
    if dump.sha256 != (ctx["complete"].get("dump") or {}).get("sha256"):
        return ["the frozen-plant dump recomputed now is not complete.json's (C11: repeat Run 1 from S0)"]
    return []


def _arm_rearm(ctx):
    """On the defect route (the contract, section 7: "No refit after any held-out statistic"; C11: "form
    and constants stay frozen ... nothing is refitted"): the calibration the re-arming records must be the
    one the previous ARMED.json records -- freeze.json and complete.json (their sha_text: the frozen sections,
    the fits and the refit variants through their chain), the derived file, the plant as built (engine_sha)
    and the frozen-plant dump. Only the in-sample re-run files (in_sample_rerun<k>.json) and the fixed code
    may differ. Nothing on the normal route (WP3's fix of 23 October 2026)."""
    prev = ctx.get("previous_armed")
    if ctx["defect"] is None:
        return []
    if prev is None:
        return ["the defect route re-arms with no previous ARMED.json to compare the calibration with"]
    rec, out = ctx["record"], []
    for key in ("freeze", "complete"):
        a = {k: v for k, v in (prev.get(key) or {}).items() if k != "commit"}
        b = {k: v for k, v in (rec.get(key) or {}).items() if k != "commit"}
        if a != b:
            out.append(f"{key}.json is not the one the previous arming recorded: a refit after the held-out run (C11)")
    for key in ("derived", "engine_sha", "dump_sha256"):
        if prev.get(key) != rec.get(key):
            out.append(f"the {key} is not the one the previous arming recorded: a refit after the held-out run (C11)")
    return out


# calibrate_epa.py's exit codes (its EXIT_*), read by name: a check that waited, crashed or opened a file
# outside its allowlist is not an in-sample stage that differs (WP3's fix of 23 October 2026).
CHECK_EXITS = {1: "crashed", 2: "was refused", 3: "opened a file outside its allowlist (a coding defect, PLAN.md 5.6)",
               4: "waited on the Run 1 gate", 5: "found the in-sample stage NOT given back byte for byte"}
# calibrate_epa.py's names of the same exits (its EXIT_CRASH ... EXIT_MISMATCH; this module never imports it, so
# test_validate_guards.AstRules reads its assignment through ast and checks both against it; WP3's second fix of
# 23 October 2026, on the test review's finding that renumbering calibrate_epa's codes passed every test)
CHECK_EXIT_NAMES = {"EXIT_CRASH": 1, "EXIT_REFUSED": 2, "EXIT_DEFECT": 3, "EXIT_WAIT": 4, "EXIT_MISMATCH": 5}
CHECK_MISMATCH = CHECK_EXIT_NAMES["EXIT_MISMATCH"]


def _check_outcome(root, name):
    """The outcome calibrate_epa.py check wrote into the engine's run.json (its last invocation), or None:
    the reason of a refusal, the type of a crash, never a value (calibrate_epa's records hold none)."""
    p = _p(root, f"{cal_dir(name)}/{RUN}")
    try:
        inv = (_load(p).get("invocations") or [])[-1]
    except (OSError, ValueError, IndexError):
        return None
    return inv.get("outcome") if inv.get("subcommand") == "check" else None


def _arm_in_sample(ctx):
    """`calibrate_epa.py check` in a subprocess in the armed tree gives the in-sample stage back byte
    for byte (PLAN.md 6.1). Its output is not shown: this file prints counts only. Its exit code is read
    by name (CHECK_EXITS): only a mismatch is C11's "repeat Run 1 from S0"."""
    root, name = ctx["source"].root, ctx["name"]
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    r = subprocess.run([sys.executable, "-B", "calibrate_epa.py", "check", "--engine", name,
                        "--jobs", str(ctx["jobs"])], cwd=root, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    # C11: an epa_stats defect found after the run recomputes in_sample.json beside the old one, as
    # in_sample_rerun<k>.json (WP3_INTERFACES 5.5.2), before the re-arming; each is recorded, committed.
    folder = _p(root, cal_dir(name))
    reruns = sorted(f for f in os.listdir(folder) if re.fullmatch(r"in_sample_rerun[1-9][0-9]*\.json", f))
    ctx["record"]["in_sample_check"] = {
        "in_sample_sha_text": common.sha_text(_p(root, f"{cal_dir(name)}/in_sample.json")), "check_exit": r.returncode,
        "in_sample_reruns": {f: common.sha_text(os.path.join(folder, f)) for f in reruns}}
    out = [f"{cal_dir(name)}/{f} is not committed and clean" for f in reruns
           if not committed(root, f"{cal_dir(name)}/{f}")]
    if r.returncode == CHECK_MISMATCH:
        out.append(f"calibrate_epa.py check exited {CHECK_MISMATCH}: the in-sample stage is not given back byte for "
                   "byte (C11: repeat Run 1 from S0)")
    elif r.returncode != 0:
        what = CHECK_EXITS.get(r.returncode, "stopped")
        outcome = _check_outcome(root, name)
        out.append(f"calibrate_epa.py check exited {r.returncode}: it {what}"
                   + (f" ({outcome})" if outcome else "") + "; not an in-sample comparison")
    return out


def manifest_index(data_folder):
    """MANIFEST.csv's sha256 by the path below the data folder, from the dataset folder (anl-d3-...)
    on: its local_path is absolute, written on the machine that downloaded the file."""
    path = os.path.join(data_folder, "MANIFEST.csv")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"no MANIFEST.csv in the data folder {data_folder} (set GRAD_ENGINE_DATA)")
    out = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            parts = r["local_path"].replace("\\", "/").split("/")
            i = next((j for j, p in enumerate(parts) if p.startswith("anl-d3-")), None)
            if i is not None:
                out["/".join(parts[i:])] = r["sha256"]
    return out


def _arm_d3(ctx):
    """Decision 63: the D3 files this engine's run reads, hashed now against the data folder's
    MANIFEST.csv, and the CX-9's 43 also against the contract's d3_files_c3 (PLAN.md 6.1)."""
    name, data_folder = ctx["name"], ctx["data_folder"]
    spec = D3_SOURCES[name]
    rec = {"data_folder": data_folder, "c3_files": [], "summary": None, "accord": []}
    ctx["record"]["d3"] = rec
    if not (spec["c3"] or spec["summary"] or spec["accord"]):
        return []
    try:
        man = manifest_index(data_folder)
    except FileNotFoundError as exc:
        return [str(exc)]
    out = []

    def hashed(rel):
        p = os.path.join(data_folder, *rel.split("/"))
        h = common.sha_raw(p) if os.path.isfile(p) else None
        if h is None or man.get(rel) != h:
            out.append(f"the D3 file {rel} is missing or does not hash to MANIFEST.csv's sha256")
        return {"file": rel, "sha256": h}

    if spec["c3"]:
        for e in ctx["contract"]["d3_files_c3"]:
            got = hashed(e["file"])
            if got["sha256"] != e["sha256"]:
                out.append(f"the D3 file {e['file']} does not hash to the contract's d3_files_c3")
            rec["c3_files"].append(got)
    if spec["summary"]:
        cands = sorted(k for k in man if k.startswith(spec["summary"] + "/") and k.endswith(".xlsx"))
        if len(cands) != 1:
            out.append(f"MANIFEST.csv lists {len(cands)} summary workbooks under {spec['summary']}, not one")
        else:
            rec["summary"] = hashed(cands[0])
    if spec["accord"]:
        cands = sorted(k for k in man if k.startswith(spec["accord"] + "/") and D3_TEST_FILE.match(k.rsplit("/", 1)[-1]))
        if not cands:
            out.append(f"MANIFEST.csv lists no test files under {spec['accord']}")
        rec["accord"] = [hashed(k) for k in cands]
    return out


def structure_flags(contract_engine, computed_engine):
    """C2: whether the populations reproduce the contract's per_held_out_line, deciding_lines and
    pooled_counts, compared as canonical JSON; booleans only (structure, no value printed)."""
    return {f"{key}_equal": _canonical_sha(contract_engine.get(key)) ==
            _canonical_sha(json.loads(json.dumps(computed_engine.get(key))))
            for key in ("per_held_out_line", "deciding_lines", "pooled_counts")}


def _arm_structure(ctx):
    """split.compute(), the generator's own code (C2; WP3_INTERFACES N5: only here and in
    test_epa_rows.Structural), run in this process, so only on this file's tree."""
    out = _require_this_tree(ctx, "the split")
    if out:
        return out
    from thresholds import split
    flags = structure_flags(ctx["contract"]["engines"][ctx["name"]], split.compute()[ctx["name"]])
    ctx["record"]["held_out_structure"] = flags
    return [f"split.compute() does not reproduce the contract's {k[:-len('_equal')]}" for k, v in flags.items() if not v]


def _arm_counts(ctx):
    """epa_rows.held_out_counts: the fired held-out rows without lambda and with the spark sentinel,
    and whether each of E8's subsets holds e8_min_rows rows, decided here before E8 is computed
    (results/ENGINE_THRESHOLDS.md sections 3 and 4). A fired sentinel row is a declared outcome,
    never a stop (decision 54 supersedes PLAN.md 6.1's "stops here")."""
    import epa_rows
    counts = epa_rows.held_out_counts(ctx["name"], source=ctx["source"])
    ctx["record"]["held_out_counts"] = dataclasses.asdict(counts)
    return population_problems(ctx["name"], source=ctx["source"], contract=ctx["contract"])


def population_problems(name, *, source, contract):
    """The held-out rows' populations as the loader computes them (epa_rows.held_out_population_counts,
    split.classify at the contract's printed hot floor and lambda_ref) against the contract's
    per_held_out_line, line by line and population by population, counts only (WP3's integration, 23
    October 2026, on the loader author's finding: the contract prints hot_map_floor_kpa rounded to 0.01,
    split.compute classified at the unrounded floor, so a held-out row between the two would change
    population unseen). A difference refuses the arming, before any held-out statistic exists: "a
    re-derivation must reproduce the counts of section 2.2, or stop" (results/ENGINE_THRESHOLDS.md
    section 10)."""
    import epa_rows
    got = epa_rows.held_out_population_counts(name, source=source)
    want = contract["engines"][name]["per_held_out_line"]
    out = []
    for line in sorted(set(got) | set(want)):
        for k in epa_rows.POPULATION_COUNT_KEYS:
            g = (got.get(line) or {}).get(k)
            w = (want.get(line) or {}).get(k)
            if g != w:
                out.append(f"the held-out line {line}'s {k} rows are {g} as the loader reads them and {w} in the "
                           "contract's per_held_out_line")
    return out


# ---------------------------------------------------------------------------------------------
# The runtime audit, record mode (C3; WP3_INTERFACES 3.3, 5.8.5)
# ---------------------------------------------------------------------------------------------
class Audit:
    """Records every file opened and every subprocess started while it is active, and refuses
    nothing; at the end the opened set is compared with the run's allowlist, and a path outside it is
    a coding defect (PLAN.md 5.6), recorded in run.json, which makes the run exit non-zero."""

    def __init__(self, *, root, data_folder):
        self.root = os.path.normcase(os.path.abspath(root))
        self.data = os.path.normcase(os.path.abspath(data_folder)) if data_folder else None
        # The code's own tree: where this file, the plant code and the specs engines.py reads beside
        # itself live. It is the root on the command line (epa_rows.Source.repository()); a test's
        # temporary root differs from it, and its files are then tagged <code>/ (run_allowlist admits
        # only code, caches and specs there).
        here = os.path.normcase(HERE)
        self.code = None if here == self.root else here
        self.py = sorted({os.path.normcase(os.path.abspath(p)) for p in (sys.base_prefix, sys.prefix,
                                                                         sys.exec_prefix)}, key=len, reverse=True)
        self.opened = set()
        self.subprocesses = []

    def norm(self, path):
        """A path as run.json records it: below the Python installation, the data folder, the root or the
        code's own tree, relative with forward slashes and in its own case (the prefixes compared
        case-folded, as Windows names them, the longest first); anything else absolute."""
        a = os.path.abspath(os.fsdecode(path))
        p = os.path.normcase(a)
        pres = [(x, "<python>/") for x in self.py] + [(self.data, "<data>/"), (self.root, ""), (self.code, "<code>/")]
        for pre, tag in sorted((x for x in pres if x[0]), key=lambda x: len(x[0]), reverse=True):
            if p == pre or p.startswith(pre + os.sep):
                return tag + a[len(pre):].lstrip(os.sep + "/").replace(os.sep, "/")
        return a.replace(os.sep, "/")


_AUDITS = []
_HOOKED = []


def _audit_hook(event, args):
    if not _AUDITS:
        return
    a = _AUDITS[-1]
    try:
        if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
            a.opened.add(a.norm(args[0]))
        elif event == "subprocess.Popen" and len(args) > 1:
            argv = args[1] if isinstance(args[1], (list, tuple)) else [args[1]]
            a.subprocesses.append([os.fsdecode(x) if isinstance(x, (bytes, os.PathLike)) else str(x) for x in argv])
    except Exception:          # an audit hook never raises into the code it watches
        pass


@contextlib.contextmanager
def audited(*, root, data_folder):
    """Install the hook once per process (a hook cannot be removed) and record while inside. Spawn
    workers are not seen by it (C3's audit_spawn.py), so the run evaluates in this process unless
    --jobs asks for a pool, whose workers' opens epa_fit.ordered_map merges into POOL_OPENED."""
    if not _HOOKED:
        sys.addaudithook(_audit_hook)
        _HOOKED.append(True)
    a = Audit(root=root, data_folder=data_folder)
    _AUDITS.append(a)
    try:
        yield a
    finally:
        _AUDITS.remove(a)


def run_allowlist(name, *, source, armed):
    """WP3_INTERFACES 5.5.4 and 5.8.5: the Python installation, the repository's code and caches, the
    specs, the generator and the contract, the K3 record; this engine's calibration records, derived
    file, tables and epa_engine.json; the tightenings; the D3 files ARMED.json hashed and the
    manifest; this engine's validation folder and its invocation log; the null device."""
    tables = _rel(os.path.join(source.engine_dir, name), source.root)
    pats = ["<python>/*", "*.py", "*/__pycache__/*", "__pycache__/*", "engine_specs/*.toml",
            "engine_specs/cars/*.toml", "thresholds/*.py", "engine_thresholds.py",
            # the code's own tree when it is not the root (a test): its code, caches and specs only
            "<code>/*.py", "<code>/*/__pycache__/*", "<code>/__pycache__/*", "<code>/engine_specs/*.toml",
            "<code>/engine_specs/cars/*.toml",
            "results/ENGINE_THRESHOLDS/ecu/k3_nominal.json", f"{cal_dir(name)}/*", f"{val_dir(name)}/*",
            invocations_rel(name), TIGHTENINGS_REL, f"{tables}/*", "<data>/MANIFEST.csv",
            _rel(source.contract_json, source.root), _rel(source.contract_md, source.root),
            os.path.abspath(os.devnull).replace(os.sep, "/")]
    if (armed.get("derived") or {}).get("path"):
        pats.append(armed["derived"]["path"])
    pats += ["<data>/" + e["file"] for e in d3_entries(armed.get("d3") or {})]
    # the generator's files the reader's guard 2 hashes (epa_rows.check_contract), as the contract lists
    # them: thresholds/document_template.md among them, which no *.py pattern holds
    pats += sorted(_load(source.contract_json).get("generators", {}).get("sha256", {}))
    # the writing marker and its log event, written inside the audited block before the first output (WP3's fourth
    # fix of 24 October 2026): the marker in the work tree's git directory, and the log's partial file
    # (epa_freeze.write_json_atomic writes beside the file, then moves it over it)
    try:
        gd = epa_freeze.git_dirs(root=source.root)[0]
    except epa_freeze.GitError:
        # no work tree (a unit call on a bare folder): the run itself refuses one without .git (refusals)
        gd = os.path.join(source.root, ".git")
    pats.append(_rel(os.path.join(gd, f"epa_writing_{name}_*"), source.root))
    pats.append(invocations_rel(name) + epa_freeze.PARTIAL_SUFFIX)
    # the Run 1 inputs hashed with the code (epa_freeze.RUN1_INPUTS: evaluate.py and the B58's spec match the
    # patterns above; the environment's pins do not), read only
    pats += [f for f in epa_freeze.RUN1_INPUTS if not fnmatch.fnmatchcase(f, "*.py") and not f.endswith(".toml")]
    return pats


def _place(path):
    """Where a recorded path lies: its tag ("<python>", "<data>", "<code>"), "/" for an absolute path,
    "" for one relative to the root."""
    if path.startswith("<"):
        return path.split("/", 1)[0]
    return "/" if path.startswith("/") or path[1:2] == ":" else ""


def outside(opened, patterns):
    """The opened paths no pattern admits, sorted. A pattern admits only paths of its own place
    (_place), so a root-relative pattern such as *.py, whose * crosses folders, never admits a file
    elsewhere on the disk or in the Python installation; case-folded, as Windows names files."""
    pats = [(_place(p), p.lower()) for p in patterns]
    return sorted(o for o in opened
                  if not any(pl == _place(o) and fnmatch.fnmatchcase(o.lower(), p) for pl, p in pats))


# ---------------------------------------------------------------------------------------------
# run (PLAN.md 6.1-6.6; C5, C6, C10, C11; decision 60)
# ---------------------------------------------------------------------------------------------
def _log_invocation(root, name, entry):
    """Append an invocation to results/EPA_VALIDATION/<id>.invocations.json, OUTSIDE the guarded
    folder (the module docstring): `arm`, and `run` when it is refused."""
    path = _p(root, invocations_rel(name))
    try:
        log = _load(path) if os.path.isfile(path) else {"engine": name, "invocations": []}
    except (OSError, ValueError):
        log = {"engine": name, "invocations": [], "unreadable_before": True}
    log["invocations"].append(dict(entry, k=len(log["invocations"]) + 1))
    epa_freeze.write_json_atomic(path, log)


def output_name(base, k):
    return base if k is None else rerun_name(base, k)


def cap_labels(obj):
    """The defect route's cap (results/ENGINE_THRESHOLDS.md section 7; PLAN.md 6.1): a re-run's every
    label reads limited at best. Every string value "validated" outside `provenance` becomes "limited";
    returns (the capped object, the JSON paths changed). A kappa is left as computed: a validated
    row's is 1, and limited's (|E| + 2u_val)/R read as a band factor would be below 1 there, so the
    band is never narrowed below b by the cap."""
    changed = []

    def walk(x, p):
        if isinstance(x, dict):
            return {k: (v if k == "provenance" else walk(v, f"{p}/{k}")) for k, v in x.items()}
        if isinstance(x, list):
            return [walk(v, f"{p}/{i}") for i, v in enumerate(x)]
        if isinstance(x, str) and x == CAP_FROM:
            changed.append(p or "/")
            return CAP_TO
        return x
    return walk(obj, ""), changed


def run(name, *, source, jobs, defect):
    """The held-out run (WP3_INTERFACES 5.8.5). Returns {"outcome", "written"}. A refusal is logged
    outside the folder and raised (Refused); a crash writes crash_<k>.txt and run.json and raises
    SystemExit(1), having printed only the exception's type."""
    _named(name)
    defect = _defect_of(defect)
    if type(jobs) is not int or jobs < 1:
        raise ValueError(f"jobs is a positive int, not {jobs!r} (no default job count)")
    root = source.root
    entry = {"subcommand": "run", "argv": list(sys.argv), "started_utc": _now(),
             "defect_rerun": None if defect is None else dataclasses.asdict(defect),
             "versions": epa_freeze.versions()}
    try:
        token = verify_for_validation(name, source=source, defect=defect)
    except Refused as exc:
        with contextlib.suppress(Exception):
            _log_invocation(root, name, dict(entry, ended_utc=_now(), outcome="refused: " + "; ".join(exc.problems)))
        raise
    armed = _load(_p(root, f"{val_dir(name)}/{ARMED}"))
    k = None if defect is None else armed["rearm"]["k"]
    folder = _p(root, val_dir(name))
    started = os.path.join(folder, output_name(STARTED, k))
    reexecution = os.path.isfile(started)
    if not reexecution:
        # STARTED, atomically, BEFORE the first held-out read (C6): from here on the run has happened.
        epa_freeze.write_json_atomic(started, {
            "engine": name, "head": token.head, "armed_blob": token.armed_blob,
            "defect_rerun": None if defect is None else
            {"k": k, "reason": defect.reason, "fix_commit": armed["rearm"]["fix_commit"]}})
    # the start marker in the work tree's git directory, where no clean or stash reaches (WP3's second fix of
    # 23 October 2026), and the start in the invocation log, outside the folder, both before the first
    # held-out read: a STARTED removed later still leaves them (folder_problems; WP3's fix of 23 October 2026)
    write_marker(root, name, "started", blob=token.armed_blob,
                 record={"engine": name, "armed_blob": token.armed_blob, "defect_rerun_k": k, "head": token.head})
    _log_invocation(root, name, {"subcommand": "run", "event": "started", "armed_blob": token.armed_blob,
                                 "defect_rerun_k": k, "reexecution": reexecution, "started_utc": _now()})
    written = [_rel(started, root)]
    outcome, outside_list = "ok", None
    d3 = armed.get("d3") or {}
    with audited(root=root, data_folder=d3.get("data_folder")) as audit:
        pool0 = _pool_mark()
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error")           # C6: warnings are errors
                outputs = _compute(name, source=source, token=token, jobs=jobs, armed=armed)
                # before the first output is written: its marker in the git directory and its event in the
                # invocation log, so that a run killed from here on does not run again (WP3's fourth fix of 24
                # October 2026)
                write_marker(root, name, "writing", blob=token.armed_blob,
                             record={"engine": name, "armed_blob": token.armed_blob, "defect_rerun_k": k,
                                     "outputs": [output_name(b, k) for b, _ in outputs]})
                _log_invocation(root, name, {"subcommand": "run", "event": "writing", "armed_blob": token.armed_blob,
                                             "defect_rerun_k": k, "outputs": [output_name(b, k) for b, _ in outputs]})
                for base, obj in outputs:
                    if k is not None:
                        obj, changed = cap_labels(obj)
                        obj["defect_rerun"] = {"k": k, "reason": defect.reason,
                                               "fix_commit": armed["rearm"]["fix_commit"], "capped_at": CAP_TO,
                                               "capped": changed}
                    path = os.path.join(folder, output_name(base, k))
                    epa_freeze.write_json_atomic(path, obj)
                    written.append(_rel(path, root))
        except BaseException as exc:                     # every exception is a crash record (C6)
            outcome = f"crash: {type(exc).__name__}"
            j = 1 + max(read_records(root, name).crashes, default=0)
            crash = os.path.join(folder, f"crash_{j}.txt")
            _write_text_atomic(crash, f"attempt: {'first' if k is None else f'rerun {k}'}\n"
                                      f"exception: {type(exc).__name__}\n"
                               + "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
            written.append(_rel(crash, root))
        finally:
            _close_pools()
        opened = sorted(set(audit.opened) | set(_pool_opened(audit, since=pool0)))
        outside_list = outside(opened, run_allowlist(name, source=source, armed=armed))
        subprocesses = list(audit.subprocesses)
    if outside_list and outcome == "ok":
        outcome = "defect: a file outside the allowlist was opened"
    rec = {"engine": name, "invocations": [dict(
        entry, k=1, ended_utc=_now(), outcome=outcome, reexecution_with_started_alone=reexecution,
        git_head=token.head, armed_blob=token.armed_blob, written=list(written), opened=opened,
        subprocesses=subprocesses, outside_allowlist=outside_list)]}
    path = os.path.join(folder, output_name(RUN, k))
    epa_freeze.write_json_atomic(path, rec)              # run.json last (PLAN.md 6.1)
    written.append(_rel(path, root))
    # the end, after run.json, crash or not: the end marker with the sha_text of every output written, and
    # the same in the invocation log (WP3's second fix of 23 October 2026). Only a killed process leaves
    # STARTED without it, the one re-execution C6 allows.
    outputs = {w: common.sha_text(_p(root, w)) for w in written if os.path.isfile(_p(root, w))}
    write_marker(root, name, "ended", blob=token.armed_blob,
                 record={"engine": name, "armed_blob": token.armed_blob, "defect_rerun_k": k, "outcome": outcome,
                         "outputs": outputs})
    _log_invocation(root, name, {"subcommand": "run", "event": "ended", "armed_blob": token.armed_blob,
                                 "defect_rerun_k": k, "outcome": outcome, "outputs": outputs, "ended_utc": _now()})
    if outcome != "ok":
        print(f"validate_epa run {name}: {outcome}; records: {', '.join(written)}")
        raise SystemExit(1)
    print(f"validate_epa run {name}: {len(written)} files written: {', '.join(written)}")
    return {"outcome": outcome, "written": written}


def _pool_mark():
    """How many worker opens epa_fit.POOL_OPENED holds now (it gathers them for the whole process)."""
    mod = sys.modules.get("epa_fit")
    return len(getattr(mod, "POOL_OPENED", ())) if mod else 0


def _pool_opened(audit, *, since):
    """The paths spawn workers opened since `since` (_pool_mark before the computation), as
    epa_fit.ordered_map gathered them in task order (C3: a parent's hook does not see a worker),
    normalised as the audit's own."""
    mod = sys.modules.get("epa_fit")
    return [audit.norm(p) for p in list(getattr(mod, "POOL_OPENED", ()))[since:]] if mod else []


def _close_pools():
    """The run's spawn workers stopped before run.json is written (epa_fit keeps a pool open between
    calls); nothing to do when no pool was made. A pool that will not close does not stop run.json
    being written: the process's exit ends its workers."""
    mod = sys.modules.get("epa_fit")
    if mod is not None and hasattr(mod, "close_pools"):
        with contextlib.suppress(Exception):
            mod.close_pools()


def _compute(name, *, source, token, jobs, armed):
    """Every held-out output, as [(file name, object), ...] in writing order: rows.json, e6.json, then
    c3.json (Mazda) or c4_accord.json (Honda). Its first read of a held-out row is
    epa_rows.read_held_out, after run has written STARTED (held_out_outputs)."""
    return held_out_outputs(name, source=source, token=token, jobs=jobs, armed=armed)


# ---------------------------------------------------------------------------------------------
# The held-out computation (PLAN.md 6.2-6.6; results/ENGINE_THRESHOLDS.md sections 3-5 and 7)
# ---------------------------------------------------------------------------------------------
# E6 row 11's charge-temperature shift (the B58's input uncertainty) and every d row's probe (decision 59)
# are read from the contract JSON's own perturbations_E6 text by e6_sizes, never retyped (mistake 10).
# The refit variants calibrate_epa.py e6 wrote before the arming (PLAN.md 5.7; WP3_INTERFACES 7.2).
E6_REFIT = ("1", "2", "3", "7_090", "7_110")
# The rows each perturbation row must move (results/ENGINE_THRESHOLDS.md section 4, E6 rows 5, 6, 2, 11, 12).
E6_ROW5_MUST_MOVE = ("E1a", "E3a", "L0")
E6_ROW6_MUST_MOVE = ("E3a", "E3b", "E4a", "L0")
E6_ROW2_MUST_NOT_MOVE = ("E2a", "D1", "L0")
E6_ROW11_ROWS = ("E3a", "E3b", "E4a", "L0")
E6_ROW12_ROWS = ("E3a", "E5", "D1", "L0")
# Readings this run declares where the contract's E6 text leaves one open (WP3's second fix of 23 October
# 2026, on the contract review's findings), written into e6.json beside the rows they read.
E6_ROW1_E8_NOT_APPLICABLE = ("not applicable: the row-1 variant's ECU is refitted to EPA's lambda as published, "
                             "and E8 compares the model ECU's lambda with EPA's lambda cell-referenced (contract "
                             "section 4, E8), so its delta would be mostly the table's offset lambda_ref - 1, not how "
                             "far the model moves")
E6_ROW2_E2_READING = ("the contract's \"E2\" among row 2's rows that must not move is read as E2a, the gating "
                      "row; E2b is descriptive, has no u_val, and its dE is reported in delta_E, not judged")
E6_EXCLUSION_READING = ("a constant's exclusion is judged under the probe at both signs (rows 5 and 9) and, for the "
                        "back-pressure law, at both of its fields: the law is one constant, so a row is excluded "
                        "for it only when it moves by less than its u_val under every probe given, and a move at "
                        "either sign of either field shows the row tests it (validate_epa._excluded)")
# The constants rows 5 and 6 move (engines.CycleCal; the back-pressure law is exh_bp_ratio and
# exh_bp_min_kpa, plant.exhaust_backpressure_kpa), and the names S1's report gives the law's sigma.
E6_ROW_FIELDS = {5: ("exh_bp_ratio", "exh_bp_min_kpa"), 6: ("ua_port",)}
E6_FIELD_ALIASES = {"ratio": "exh_bp_ratio", "floor_kpa": "exh_bp_min_kpa"}
# The scored context's coverage flags beside every label (results/ENGINE_THRESHOLDS.md section 3; PLAN.md
# 6.2), named here without a figure: the figures are the contract's, whose rule (JSON conventions.labels) is
# quoted beside them in rows.json. They gate nothing.
COVERAGE_STATEMENTS = (
    "the scored roads' ambient: the charge above every EPA map's intake temperature",
    "holds longer than EPA's: an extrapolation in duration",
    "road speeds above C1's range: the road load not covered",
    "the cells' barometer against the road's")
# C3's chain, values the contract or a declared design sets (results/ENGINE_THRESHOLDS.md section 5):
# the EPA map fuel's heating value, read under this key of the engine's epa_engine.json alpha_fuel (the
# model's fuel is scaled by it over the D3 fuel's, which the summary gives per test);
# the barometric pressure the closed-throttle check is judged against where the summary holds none,
# DESIGN: the standard atmosphere, since the check's 0.7 ratio separates a manifold sensor (about a
# third of an atmosphere at idle) from one before the throttle (barometric) at any cell pressure; and
# the Accord's coolant, which its D3 files do not carry (CATALOGUE.md:625), DESIGN: a warm block,
# 365 K, the coolant of epa_freeze's dump grid. C4 is descriptive, so neither moves a label.
EPA_MAP_LHV_KEY = "energy_density_BTUplbm"
D3_BARO_KPA_DECLARED = 101.325
ACCORD_ECT_K_DECLARED = 365.0
D3_ENGINE = {"mazda_25t": ("CHANNELS", "SUMMARY_CX9", False), "honda_l15b7": ("ACCORD_CHANNELS", "SUMMARY_ACCORD", True)}


def _kernel(item):
    """One row's evaluation in a worker (picklable): epa_stats.kernel_point, the one definition."""
    import epa_stats
    model, task = item
    return epa_stats.kernel_point(model, task)


def worker_audit():
    """A spawn worker's audit hook (C3: a parent's hook does not see a worker): every open's path is
    appended to epa_fit.WORKER_OPENED, which ordered_map returns beside each task and gathers in task
    order into epa_fit.POOL_OPENED; run reads it into run.json. Records, refuses nothing. And C6's
    "warnings are errors" in the worker too, before its first task: a spawn worker does not inherit a
    filter set at run time (run's catch_warnings is the parent's), so without this a warning at a
    held-out row would be silent at --jobs > 1 and a crash at --jobs 1 (WP3's fix of 23 October 2026)."""
    warnings.simplefilter("error")
    import epa_fit

    def hook(event, args):
        if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
            try:
                epa_fit.WORKER_OPENED.append(os.path.abspath(os.fsdecode(args[0])))
            except Exception:
                pass
    sys.addaudithook(hook)


WORKER_INIT = (worker_audit, ())


def _map(fn, items, jobs):
    import epa_fit
    return epa_fit.ordered_map(fn, list(items), jobs=jobs, initializer=WORKER_INIT)


def _evaluate(model, rows, *, view, conventions, dtheta, shift, jobs):
    """Every row through epa_stats.kernel_point (WP3_INTERFACES 5.2.3), in row order, each with its own
    default needs (epa_stats.default_needs: D1 on the fired rows with a meter, lambda = 1 on the
    enriched hot rows, the ECU on the Final rows)."""
    import epa_stats
    tasks = [epa_stats.make_task(r, view=view, conventions=conventions, dtheta=dtheta,
                                 needs=epa_stats.default_needs(r), shift=shift) for r in rows]
    return tuple(_map(_kernel, [(model, t) for t in tasks], jobs))


def _key(e):
    return (e.table, int(e.source_row))


def _marked(evals, *, censoring, view):
    import epa_stats
    return epa_stats.mark_coverage(epa_stats.mark_censored(evals, censoring=censoring), view=view)


def censoring_of(stage0):
    """The engine's censoring, as the calibration decided it on its own Final rows (stage0.json, checks.
    censoring; results/ENGINE_THRESHOLDS.md section 3: defined on the calibration Final rows, never on all
    rows): an epa_stats.Censoring."""
    import epa_stats
    c = stage0["checks"]["censoring"]
    return epa_stats.Censoring(censored=bool(c["censored"]),
                               value=float(c["min_lambda_cellref"]) if c["censored"] else None,
                               n_at_min=int(c["n_at_min_within_1e-9"]), documented_floor=c["documented_floor"],
                               rule=str(c["rule"]), n_rows=int(c["final_rows_with_lambda"]))


class _Evals:
    """The held-out rows evaluated at one plant and one set of conventions: the nominal set, and on
    demand the sets each u-term needs (crank step halved; each input moved by +-u_j; lambda's u_D)."""

    def __init__(self, model, points, initial, *, view, conventions, censoring, jobs):
        import epa_stats
        import plant as plant_model
        self.model, self.points, self.initial = model, points, initial
        self.view, self.conventions, self.censoring, self.jobs = view, conventions, censoring, jobs
        self.dtheta = float(plant_model.DTHETA_DEG)
        self.es = epa_stats
        self.N = self._eval(self.dtheta, None)
        self.I = _evaluate(model, initial, view=view, conventions=conventions, dtheta=self.dtheta, shift=None,
                           jobs=jobs)
        self._unc = None

    def _eval(self, dtheta, shift):
        ev = _evaluate(self.model, self.points, view=self.view, conventions=self.conventions, dtheta=dtheta,
                       shift=shift, jobs=self.jobs)
        return _marked(ev, censoring=self.censoring, view=self.view)

    def unc(self):
        """epa_stats.UncertaintyInputs: every row at dtheta/2 (u_num, E6 row 8: 0.25 to 0.125 deg), every row
        at each +-u_j shift (u_input), every row with its lambda reading moved by lambda's u_D (E4b), every row
        with its torque reading moved by torque's u_D (D1's target, L0, L1)."""
        if self._unc is None:
            es = self.es
            fine = {_key(e): e for e in self._eval(self.dtheta / 2.0, None)}
            shifted = {}
            for ch, sg, sh in es.input_shifts(terms=es.U_INPUT):
                for e in self._eval(self.dtheta, sh):
                    shifted[(ch, sg, _key(e))] = e
            lam_u = es.U_D["lam"].value
            common_lam = {_key(e): e for e in self._eval(self.dtheta, es.InputShift("lam", float(lam_u)))}
            # D1's torque target (and L0's and L1's): every row re-evaluated with its torque reading moved by
            # torque's u_D, the inversion re-run there (epa_stats.torque_target_shift; WP3's second fix of 23
            # October 2026)
            torque = {_key(e): e for e in self._eval(self.dtheta, es.torque_target_shift(es.U_D))}
            self._unc = es.UncertaintyInputs(evals_0125=fine, shifted=shifted, common_lam=common_lam,
                                             input_terms=es.U_INPUT, d_terms=es.U_D, torque_target=torque)
        return self._unc

    def rows_for(self, r):
        """The evaluations row `r` reads: E1i the Initial rows; E4b the steady and Final rows AND the Initial
        ones, for its Initial-to-Final pair estimate (the contract, section 4, E4b: "reported beside it,
        descriptive"; WP3's third fix of 24 October 2026, on the contract review's finding that it always read
        no hold) -- its core reads the Initial rows nowhere else (their pops are None) and its u-terms'
        members exclude them; every other row the steady and Final rows."""
        return rows_for(r, self.N, self.I)

    def values(self, tight):
        """Every row's StatResult without u-terms (the E a perturbation moves: E6). `tight` is the
        tightening record as the file holds it (Tightenings.raw), the form epa_stats reads."""
        es = self.es
        out = {}
        for r, fn in es.ROW_FUNCTIONS.items():
            out[r] = fn(self.rows_for(r), view=self.view, stage="held_out", tightening=tight)
        return out

    def labelled(self, tight, rows):
        """The gating rows among `rows` with their u-terms, labels and kappa (epa_stats.held_out_row), the
        descriptive ones by their row function."""
        es = self.es
        out = {}
        for r in rows:
            if es.KIND[r] == "descriptive":
                out[r] = es.ROW_FUNCTIONS[r](self.rows_for(r), view=self.view, stage="held_out", tightening=tight)
            else:
                out[r] = es.held_out_row(r, self.rows_for(r), view=self.view, tightening=tight, unc=self.unc())
        return out

    def steady_tit(self, tight):
        """Decision 83's steady-only TIT reading on the held-out rows (epa_stats.steady_tit_reading): E3a, E4a, L0
        and L1 without the High Load Final rows, E4b without the Final rows of its reference line, each labelled
        with its u-terms from the same perturbed evaluations as the primary; a sensitivity beside the primary,
        read by nothing that decides."""
        return self.es.steady_tit_reading(None, view=self.view, stage="held_out", tightening=tight, unc=self.unc(),
                                          rows_for=self.rows_for)


def rows_for(r, points, initial):
    """The evaluations row `r` reads of the steady and Final ones (`points`) and the Initial ones (`initial`):
    _Evals.rows_for's rule, one definition for the nominal run and for HeldOutState.at under an input shift."""
    if r == "E1i":
        return tuple(initial)
    if r == "E4b":
        return tuple(points) + tuple(initial)
    return tuple(points)


def _variant_values(name, e6file, derived_values):
    """A refit variant's derived values: its frozen sections (e6/row<n>.json, checked against its own
    frozen_sections_sha256) with the frozen plant's completion sections, which no refit moves."""
    import engines
    vals = {s: e6file["values"][s] for s in engines.FROZEN_SECTIONS}
    if engines.frozen_sections_sha256(vals) != e6file["frozen_sections_sha256"]:
        raise RuntimeError(f"{name}: e6 variant {e6file.get('variant')}'s frozen sections are not its own hash")
    for s in epa_freeze.COMPLETION_SECTIONS:
        vals[s] = derived_values[s]
    return vals


def record_of(engine, field):
    """The one engine record that has `field` (E6 row 9's constants live in geometry -- the conrod, IVC,
    EVO -- and in cycle); refused when none or more than one has it."""
    names = [f.name for f in dataclasses.fields(engine) if f.name not in ("id", "derived")]
    hits = [n for n in names if dataclasses.is_dataclass(getattr(engine, n))
            and field in {f.name for f in dataclasses.fields(getattr(engine, n))}]
    if len(hits) != 1:
        raise KeyError(f"E6 row 9's constant {field!r} is in {hits or 'no'} engine record(s)")
    return hits[0]


def _per_field(x, fields, what):
    """A sigma or probe as {field: absolute change}: a mapping by field (or by S1's names, ratio and
    floor_kpa), or one number for a row that moves one field. A field's value may be None where the fit
    gives no sigma (S1's floor when every row lies below the hinge, its sigma None and flagged; amendment
    D10): that field's sigma run is then not made, and e6.json records None (WP3's integration, 23
    October 2026: float(None) would have stopped the one-shot run)."""
    if isinstance(x, dict):
        got = {E6_FIELD_ALIASES.get(k, k): (None if v is None else float(v)) for k, v in x.items()}
        if set(got) != set(fields):
            raise ValueError(f"{what}: complete.json gives {sorted(got)}, the row moves {list(fields)}")
        return got
    if isinstance(x, (int, float)) and not isinstance(x, bool) and len(fields) == 1:
        return {fields[0]: float(x)}
    raise ValueError(f"{what}: complete.json's {x!r} is not a change per field of {list(fields)}")


def must_move_findings(results, probes, rows):
    """E6 rows 5 and 6's must_move (contract section 4: "E1a, E3a and L0 must move under the probe"): each
    listed row's |dE| against its own u_val under each constant's visibility probe, at each sign; a row that
    moves by less than its u_val at some probe and sign is a finding, reported and never a stop (WP3's fix of
    23 October 2026: the rows were listed and never judged, while row 2's must_not_move was). `probes` is
    {constant: {"+": results, "-": results}}. A row without a statistic or a u is not judged (None); a
    descriptive row (row 6's E3b), which has no u_val, is reported with its dE at each probe and sign under
    "descriptive", "descriptive: no u_val" beside it (WP3's second fix of 23 October 2026, on the contract
    review's finding that it was recorded as None and could never be judged)."""
    import epa_stats
    by_row, findings, descriptive = {}, [], {}
    for r in rows:
        b = results.get(r)
        if b is not None and epa_stats.KIND.get(r) == "descriptive":
            by_row[r] = None
            descriptive[r] = {"why": "descriptive: no u_val, so the move is reported and not judged",
                              "dE": {f"{f} {s}": (None if (b.E is None or v.get(r) is None or v[r].E is None)
                                                  else float(v[r].E - b.E))
                                     for f, runs in probes.items() for s, v in runs.items()}}
            continue
        if b is None or b.no_statistic or b.u is None or b.E is None:
            by_row[r] = None
            continue
        rec = {}
        for f, runs in probes.items():
            for s, v in runs.items():
                vr = v.get(r)
                rec[f"{f} {s}"] = (None if (vr is None or vr.no_statistic or vr.E is None)
                                   else bool(abs(vr.E - b.E) >= b.u.u_val))
        by_row[r] = rec
        if any(x is False for x in rec.values()):
            findings.append(r)
    return {"by_row": by_row, "findings": findings, "descriptive": descriptive}


def _deltas(base, var, rows):
    return {r: (None if base[r].E is None or var[r].E is None else float(var[r].E - base[r].E)) for r in rows
            if r in base and r in var}


def _excluded(base, variants, rows):
    """{row: bool} for the gating rows among `rows`: excluded for the constant when its statistic moves by
    less than its own u_val under every probe given (both signs), epa_stats.excluded_for; a row without a
    statistic or without u is not judged (None)."""
    import epa_stats
    out = {}
    for r in rows:
        b = base.get(r)
        if b is None or b.no_statistic or b.u is None or any(v[r].no_statistic for v in variants):
            out[r] = None
            continue
        out[r] = all(epa_stats.excluded_for(b, v[r]) for v in variants)
    return out


def row9_probe_values(spec, v0):
    """E6 row 9's probe of one constant, from its completion record (complete.json's e6_probes row9) and its value
    v0 in the frozen plant: ({"+": value, "-": value}, size). A bracket (method "bracket") is applied as its two
    edges, "+" its upper and "-" its lower, its size None (defect D-2, 29 October 2026: the contract moves a constant
    "by its band", and row 9's band is "the bracket EPA's calculated valve channels give"; the code had applied it as
    v0 +- its farther edge, outside the bracket on one side). A bracket record without its two edges (one written
    before D-2) is refused, never applied symmetrically by a fallback (mistake 19). Any other probe is v0 +- its
    size, as before."""
    if spec.get("method") == "bracket":
        edges = spec.get("bracket")
        if not (isinstance(edges, (list, tuple)) and len(edges) == 2 and float(edges[0]) <= float(edges[1])):
            raise RuntimeError(f"E6 row 9: a bracket record without its two edges ({edges!r}); one written before "
                               "defect D-2 is not applied")
        return {"+": float(edges[1]), "-": float(edges[0])}, None
    size = float(spec["size"])
    return {"+": v0 + size, "-": v0 - size}, size


def not_visible_at_r1(spec):
    """Decision 85 (29 October 2026): the reason a completion's probe record (complete.json's e6_probes) gives for a
    constant that is not visible at R1, counted as excluded for its row's level rows, or None (a record written
    before decision 85 carries no such key, and is judged as before)."""
    if (spec or {}).get("counted_excluded"):
        return str(spec.get("counted_excluded_why") or spec.get("not_visible_at_r1") or "not visible at R1")
    return None


def level_exclusion(results, runs, rows, *, hidden):
    """{row: bool or None} for the level rows `rows` of one E6 row: excluded for it when its statistic moves by less
    than its own u_val under every probe of every constant (_excluded), a constant in `hidden` (decision 85: not
    visible at R1) counted as excluded rather than judged by its probe; with every constant hidden, every row with
    a statistic and a u is excluded. `runs` is {constant: [results under each sign of its probe]}."""
    judged = [v for c, vs in runs.items() if c not in hidden for v in vs]
    if judged:
        return _excluded(results, judged, rows)
    out = {}
    for r in rows:
        b = results.get(r)
        out[r] = None if (b is None or b.no_statistic or b.u is None) else True
    return out


@dataclasses.dataclass(frozen=True)
class HeldOutState:
    """What the held-out run has read and computed before E6 (held_out_outputs), passed whole to e6_rows:
    the view and the contract, the tightenings as the file holds them, the calibration's records the run
    reads, the frozen plant, the held-out rows (points: steady and Final; initial: High Load Initial),
    the calibration's censoring, the nominal evaluation (an _Evals) with its labelled results and its
    values without u, and the two E6 sizes read from the contract (e6_sizes)."""
    name: str
    view: object
    contract: dict
    tight: dict
    complete: dict
    e6files: dict
    derived_values: dict
    frozen: object
    points: tuple
    initial: tuple
    cens: object
    jobs: int
    nominal: object
    results: dict
    base_values: dict
    imt_k: float
    d_probe_rel: float
    d_probe_cad: float

    def at(self, plant, *, conventions, shift):
        """Every row's StatResult without u-terms (the E a perturbation moves) on another plant, conventions
        or input shift (every argument required: test_engine_threading's rule for a function that takes a
        plant). Under an input shift E1i is read at the nominal Initial rows: E6 row 11 moves the steady and
        Final rows' charge, on the hot TIT rows."""
        import epa_fit
        import epa_stats
        model = epa_fit.RowModel(plant, fuels=self.view.fuel_by_table)
        if shift is None:
            ev = _Evals(model, self.points, self.initial, view=self.view, conventions=conventions, censoring=self.cens,
                        jobs=self.jobs)
            return ev.values(self.tight)
        N = _marked(_evaluate(model, self.points, view=self.view, conventions=conventions, dtheta=self.nominal.dtheta,
                              shift=shift, jobs=self.jobs), censoring=self.cens, view=self.view)
        return {r: fn(rows_for(r, N, self.nominal.I), view=self.view, stage="held_out", tightening=self.tight)
                for r, fn in epa_stats.ROW_FUNCTIONS.items()}


def held_out_outputs(name, *, source, token, jobs, armed):
    """rows.json, e6.json and the D3 record, computed once (PLAN.md 6.2-6.6). Reads the contract's view,
    the calibration's records, then the held-out rows (epa_rows.read_held_out, the first held-out read);
    builds the frozen plant (its engine_sha checked against ARMED.json's); evaluates every held-out row;
    takes every statistic, u-term and label from epa_stats; E6 in the same run (e6_rows), C3 or C4 through
    d3_rows (_d3_chain), section 7 from epa_stats.section7; writes nothing itself (run writes each output
    atomically)."""
    import engines
    import epa_fit
    import epa_rows
    import epa_stats
    root = source.root
    view = epa_rows.calibration_contract(name, source=source)
    contract = _load(source.contract_json)
    imt_k, d_probe_rel, d_probe_cad = e6_sizes(contract)
    # checked here as at the arming; epa_stats reads the record by the file's own keys (L1, E8, plant)
    tight = load_tightenings(_p(root, TIGHTENINGS_REL)).raw
    cal = lambda rel: _load(_p(root, f"{cal_dir(name)}/{rel}"))       # noqa: E731
    complete, stage0 = cal("complete.json"), cal("stage0.json")
    e6files = {v: cal(f"e6/row{v}.json") for v in E6_REFIT}
    derived_values = _load(_p(root, armed["derived"]["path"]))
    held = epa_rows.read_held_out(name, source=source, token=token)          # the first held-out read
    points = tuple(r for r in held.rows if isinstance(r, epa_rows.HeldOutRow))
    initial = tuple(r for r in held.rows if isinstance(r, epa_rows.HeldOutInitialRow))
    frozen = engines.get(name)
    if engines.engine_sha(frozen) != armed["engine_sha"]:
        raise RuntimeError(f"{name}: the plant as built is not the plant ARMED.json records (engine_sha)")
    cens = censoring_of(stage0)
    nominal = _Evals(epa_fit.RowModel(frozen, fuels=view.fuel_by_table), points, initial, view=view,
                     conventions=epa_stats.NOMINAL, censoring=cens, jobs=jobs)
    results = nominal.labelled(tight, tuple(epa_stats.ROW_FUNCTIONS))
    # decision 83: the steady-only TIT reading, beside the primary in rows.json, never in section 7 or the labels
    steady_tit = nominal.steady_tit(tight)
    st = HeldOutState(name=name, view=view, contract=contract, tight=tight, complete=complete, e6files=e6files,
                      derived_values=derived_values, frozen=frozen, points=points, initial=initial, cens=cens,
                      jobs=jobs, nominal=nominal, results=results, base_values=nominal.values(tight), imt_k=imt_k,
                      d_probe_rel=d_probe_rel, d_probe_cad=d_probe_cad)
    e6, excl, res_u = e6_rows(st)
    # C3 (Mazda) or C4's Accord chain (Honda): its rows join section 7 (P5) and its E6 row 10
    d3_out, c3_results = (None, {})
    if D3_OUTPUT[name]:
        d3_out, c3_results, eta = _d3_chain(name, source=source, armed=armed, view=view, contract=contract,
                                            frozen=frozen, jobs=jobs)
        e6["10"] = eta["rows"]
        if eta["excluded"]:                  # C3b and C3d's Tests lists name eta (the Mazda's C3 only)
            excl[10] = eta["excluded"]
    exclusions, every = _exclusions(contract, excl)
    labelled = dict(results)
    labelled.update({r: v for r, v in c3_results.items() if v.kind == "d"})
    # E6 row 12 (contract section 4): E3a, L0 and D1 labelled by the worse of their snapped and unsnapped
    # readings, D1 with the larger kappa, in section 7 (the 850 C row and P1) and in every label reported
    # (rows.json's `reported`, which the summary reads; WP3's fix of 23 October 2026)
    row12 = {r: res_u[r] for r in epa_stats.ROW12_LABELLED}
    s7 = epa_stats.section7(labelled, engine=name, unsnapped=row12, excluded_every=every)
    prov = _provenance(name, source=source, token=token, armed=armed, view=view)
    flags = {f"{e.table}/{e.source_row}": sorted(e.flags) for e in nominal.N + nominal.I if e.flags}
    rows_out = {
        "schema": ROWS_SCHEMA, "provenance": prov,
        "counts": {"held_out_rows": len(held.rows), "by_table": dict(held.counts),
                   "fired_lambda_missing": sum(1 for e in nominal.N if e.pops.fired and "lambda_missing" in e.flags),
                   "fired_spark_sentinel": sum(1 for e in nominal.N if e.pops.fired and "spark_sentinel" in e.flags)},
        "rows": {r: v.as_json() for r, v in results.items()},
        "reported": json_ready(epa_stats.reported_labels(labelled, unsnapped=row12, excluded_every=every)),
        "coverage_flags": {"engine": {"contract_coverage": contract["engines"][name]["coverage"],
                                      "statements": list(COVERAGE_STATEMENTS),
                                      "contract_rule": contract["conventions"]["labels"]},
                           "per_row": flags},
        "section7": json_ready(s7),
        "c5_recheck_margin": c5_recheck_margin(results["E1a"]),
        "steady_only_tit": json_ready(epa_stats.steady_tit_json(steady_tit))}
    e6_out = {"schema": E6_SCHEMA, "provenance": prov, "rows": json_ready(e6), "exclusions": exclusions,
              "excluded_for_every_listed_constant": every,
              "sizes_from_the_contract": {"row11_imt_k": imt_k, "d_rows_probe_relative": d_probe_rel,
                                          "d_rows_probe_ivc_evo_cad": d_probe_cad}}
    out = [(ROWS, rows_out), (E6, e6_out)]
    if d3_out is not None:
        d3_out["provenance"] = prov
        out.append((D3_OUTPUT[name], d3_out))
    return out


def e6_rows(st):
    """E6 in the same single run (PLAN.md 6.4; results/ENGINE_THRESHOLDS.md section 4, E6; amendments E2,
    E3; decision 59), from a HeldOutState: (e6.json's rows but row 10, which C3 adds; each perturbation
    row's "excluded for" verdicts by constant, for the Tests lists; row 12's unsnapped results, whose D1
    section 7 reads).

      rows 1, 2, 3, 7  the refit variants calibrate_epa.py e6 wrote before the arming, built here from their
                       frozen sections and the frozen plant's completion sections: every row's dE, no
                       exclusion label (E2); row 2's E2a, D1 and L0 within their u_val, a miss a finding;
      row 4            completion's record, the roads' ceiling flag left to the roads step;
      rows 5, 6        +-sigma, +-the probe and +-the d rows' probe of each constant; exclusion judged under
                       the probe (level rows) and the d probe (d rows), both signs; a constant the completion
                       found not visible at R1 counted as excluded for the level rows, with its reason
                       (decision 85; level_exclusion), here and in row 9;
      row 8            u_num;
      row 9            each constant as completion sized it, a bracket at its two edges (defect D-2;
                       row9_probe_values), the rich slope after its retag identity (HANDOFFS.md WP3 item 3);
      row 11           the charge temperature +- the contract's shift, on the hot TIT rows;
      row 12           E3a, E5, D1 and L0 unsnapped, labelled by the worse; D1's larger kappa;
      row 13           handed to the preregistration."""
    import engines
    import epa_fit
    import epa_stats
    name, frozen, results, base_values = st.name, st.frozen, st.results, st.base_values
    complete, d_probe_rel = st.complete, st.d_probe_rel
    gating = tuple(r for r in epa_stats.ROW_FUNCTIONS if epa_stats.KIND[r] != "descriptive")
    level = [r for r in gating if epa_stats.KIND[r] == "level"]
    drows = [r for r in gating if epa_stats.KIND[r] == "d"]
    nominal_conv = epa_stats.NOMINAL
    signs = (("+", 1.0), ("-", -1.0))
    e6, excl, refit = {}, {}, {}
    for v in E6_REFIT:
        f = st.e6files[v]
        conv = epa_stats.Conventions(**f["conventions"]) if f.get("conventions") else nominal_conv
        refit[v] = st.at(engines.build_candidate(name, _variant_values(name, f, st.derived_values)),
                         conventions=conv, shift=None)
    in_use = complete.get("e6_in_use") or {}
    for row, vs in (("1", ("1",)), ("3", ("3",)), ("7", ("7_090", "7_110"))):
        e6[row] = {"variants": {v: {"delta_E": epa_stats.refit_movement(base_values, refit[v]),
                                    "in_use": in_use.get(v)} for v in vs}}
    # E8 under row 1 (WP3's second fix of 23 October 2026, on the contract review's finding): the variant's ECU
    # is refitted to EPA's lambda as published while E8 compares it with EPA's lambda cell-referenced, so its
    # delta would be mostly the table's offset (lambda_ref - 1), not how far the model moves: not applicable
    e6["1"]["variants"]["1"]["delta_E"]["E8"] = None
    e6["1"]["not_applicable"] = {"E8": E6_ROW1_E8_NOT_APPLICABLE}
    mnm = {}
    for r in E6_ROW2_MUST_NOT_MOVE:
        if results[r].no_statistic or refit["2"][r].no_statistic:
            mnm[r] = {"dE": None, "u_val": None, "ok": None, "reason": "no statistic"}
            continue
        dE, u, ok = epa_stats.must_not_move(results, refit["2"], (r,))[r]
        mnm[r] = {"dE": dE, "u_val": u, "ok": ok}
    e6["2"] = {"delta_E": epa_stats.refit_movement(base_values, refit["2"]), "must_not_move": mnm,
               "findings": [r for r, x in mnm.items() if x["ok"] is False],
               "e2_reading": E6_ROW2_E2_READING}
    e6["4"] = {"completion": complete.get("e6_row4"), "ceiling_below_2_mei": None}
    probes = complete["e6_probes"]
    for row, key in ((5, "row5"), (6, "row6")):
        fields = E6_ROW_FIELDS[row]
        sig = _per_field(probes[key]["sigma"], fields, f"E6 row {row} sigma")
        prb = _per_field(probes[key]["probe"], fields, f"E6 row {row} probe")
        per = {}
        for fld in fields:
            v0 = float(getattr(frozen.engine.cycle, fld))
            per[fld] = {tag: {s: st.at(epa_fit.perturbed(frozen, record="cycle", field=fld, value=v0 + sg * d),
                                       conventions=nominal_conv, shift=None) for s, sg in signs}
                        for tag, d in (("sigma", sig[fld]), ("probe", prb[fld]), ("d_probe", d_probe_rel * abs(v0)))
                        if d is not None}
        # decision 85: a constant the completion found not visible at R1 is counted as excluded for the level rows,
        # with its reason, its +-10 % probe still run and reported; the d rows are judged under the d probe as before
        hidden = {f: not_visible_at_r1((probes[key].get("detail") or {}).get(f)) for f in fields}
        hidden = {f: why for f, why in hidden.items() if why is not None}
        ex = {}
        ex.update(level_exclusion(results, {f: [per[f]["probe"][s] for s in "+-"] for f in fields}, level,
                                  hidden=hidden))
        ex.update(_excluded(results, [per[f]["d_probe"][s] for f in fields for s in "+-"], drows))
        excl[row] = {"all": ex}
        must = E6_ROW5_MUST_MOVE if row == 5 else E6_ROW6_MUST_MOVE
        moves = must_move_findings(results, {f: per[f]["probe"] for f in fields}, must)
        e6[str(row)] = {
            "constants": {f: {tag: {s: _deltas(base_values, runs[tag][s], epa_stats.ROW_FUNCTIONS) for s in "+-"}
                              for tag in runs} for f, runs in per.items()},
            "sigma": {f: sig[f] for f in fields}, "probe": {f: prb[f] for f in fields},
            "must_move": list(must), "must_move_moved": moves["by_row"], "findings": moves["findings"],
            "descriptive_must_move": moves["descriptive"], "excluded_for": ex, "exclusion_reading": E6_EXCLUSION_READING,
            "not_visible_at_r1": hidden}
    e6["8"] = {"u_num": {r: (None if results[r].u is None else results[r].u.u_num) for r in gating}}
    e6["9"], excl[9] = {}, {}
    row9 = probes.get("row9") or {}
    if "ce_rich_slope" in row9 and not epa_fit.retag_identity(frozen, grid=epa_fit.synthetic_grid(frozen),
                                                               dtheta=st.nominal.dtheta):
        # HANDOFFS.md WP3 item 3: the retag at the engine's own slope gives its own doubles, asserted
        # before the probe is read, never relaxed
        raise RuntimeError(f"{name}: the rich slope's retag is not the frozen plant at its own slope")
    for const, spec in sorted(row9.items()):
        record = spec.get("record") or record_of(frozen.engine, const)
        v0 = float(getattr(getattr(frozen.engine, record), const))
        # defect D-2 (29 October 2026): a bracket is applied as its two edges, "+" at its upper edge and "-" at its
        # lower (calibrate_epa.BRACKET_EDGES), never v0 +- its farther edge; any other probe as v0 +- its size
        values, size = row9_probe_values(spec, v0)

        def moved(val, const=const, record=record):
            if const == "ce_rich_slope":
                return epa_fit.with_rich_slope_probe(frozen, slope=val)
            return epa_fit.perturbed(frozen, record=record, field=const, value=val)
        lvl = {s: st.at(moved(values[s]), conventions=nominal_conv, shift=None) for s, _sg in signs}
        # the d rows' probe: +-10 % of the constant, and for IVC and EVO the contract's "+-10 crank degrees"
        # (its row 9 band: "else +-10 % (+-10 crank degrees for IVC and EVO)"), never 10 % of an angle
        # (WP3's fix of 23 October 2026: 10 % of -140 deg is 14 CAD)
        d_size = st.d_probe_cad if const in epa_stats.E6_ANGLE_FIELDS else d_probe_rel * abs(v0)
        dpr = {s: st.at(moved(v0 + sg * d_size), conventions=nominal_conv, shift=None) for s, sg in signs}
        # the rich slope under form C, where it is fitted: also +- its fit's standard uncertainty, reported
        # (row 9's band as version 4 wrote it and version 5 kept it, "as rows 5 and 6"); exclusion is judged
        # under the probe alone
        sigma = spec.get("sigma")
        sgm = ({s: st.at(moved(v0 + sg * float(sigma)), conventions=nominal_conv, shift=None) for s, sg in signs}
               if sigma is not None else None)
        # decision 85: not visible at R1 is counted as excluded for the level rows, with its reason
        hidden = not_visible_at_r1(spec)
        ex = {}
        ex.update(level_exclusion(results, {const: list(lvl.values())}, level,
                                  hidden={const: hidden} if hidden is not None else {}))
        ex.update(_excluded(results, list(dpr.values()), drows))
        excl[9][const] = ex
        e6["9"][const] = {"method": spec.get("method"), "why_not_bracket": spec.get("why_not_bracket"),
                          "record": record, "size": size, "bracket": spec.get("bracket") if spec.get("method") == "bracket"
                          else None, "values": values,
                          "retag_identity": True if const == "ce_rich_slope" else None,
                          "delta_E": {s: _deltas(base_values, lvl[s], epa_stats.ROW_FUNCTIONS) for s in "+-"},
                          "d_probe_size": d_size,
                          "delta_E_d_probe": {s: _deltas(base_values, dpr[s], epa_stats.ROW_FUNCTIONS) for s in "+-"},
                          "sigma": sigma, "sigma_why": spec.get("sigma_why"),
                          "delta_E_sigma": None if sgm is None else
                          {s: _deltas(base_values, sgm[s], epa_stats.ROW_FUNCTIONS) for s in "+-"},
                          "excluded_for": ex, "worth_r1": spec.get("worth_r1"), "worth_b": spec.get("worth_b"),
                          "worth_b_why": spec.get("worth_b_why"), "band": spec.get("band"),
                          "housing_change_k": spec.get("housing_change_k"),
                          "probe_housing_change_k": spec.get("probe_housing_change_k"),
                          "load_bearing": spec.get("load_bearing"), "load_bearing_why": spec.get("load_bearing_why"),
                          "not_visible_at_r1": hidden}
    e6["11"] = {}
    for tag, sg in (("plus", 1.0), ("minus", -1.0)):
        v = st.at(frozen, conventions=nominal_conv, shift=epa_stats.InputShift("imt", sg * st.imt_k))
        e6["11"][tag] = {"hot_tit": {r: {"E": v[r].E, "dE": _deltas(base_values, v, (r,))[r]} for r in E6_ROW11_ROWS}}
    unsnapped = _Evals(epa_fit.RowModel(frozen, fuels=st.view.fuel_by_table), st.points, st.initial, view=st.view,
                       conventions=epa_stats.Conventions(snap=False, cell_referenced=True, afr_st=None,
                                                         lhv_j_per_kg=None), censoring=st.cens, jobs=st.jobs)
    res_u = unsnapped.labelled(st.tight, E6_ROW12_ROWS)
    e6["12"] = {r: {"snapped": results[r].as_json(), "unsnapped": res_u[r].as_json(),
                    "label_worse": (None if results[r].label is None or res_u[r].label is None
                                    else epa_stats.worse(results[r].label, res_u[r].label))} for r in E6_ROW12_ROWS}
    d1k = [x.kappa for x in (results["D1"], res_u["D1"]) if not x.no_statistic and x.kappa is not None]
    e6["12"]["d1_kappa"] = max(d1k) if d1k else None
    e6["13"] = {"handed_on": True, "variants": complete.get("e6_row13")}
    return e6, excl, res_u


def json_ready(obj):
    """Plain JSON values for a record: a mapping with str keys, a list for a tuple, a Python float for a
    NumPy number and None for a non-finite one (allow_nan=False downstream), a dataclass by its fields."""
    import math
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return json_ready(dataclasses.asdict(obj))
    if isinstance(obj, dict) or hasattr(obj, "items"):
        return {str(k): json_ready(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_ready(v) for v in obj]
    if isinstance(obj, bool) or obj is None or isinstance(obj, str):
        return obj
    if hasattr(obj, "item") and not isinstance(obj, (int, float)):
        obj = obj.item()
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, int):
        return int(obj)
    if isinstance(obj, float):
        return float(obj) if math.isfinite(obj) else None
    raise TypeError(f"json_ready: {type(obj).__name__} is not a JSON value")


def _member_constants(member, e6_row, excl):
    """The constants of one Tests-list member (JSON tests_lists.lists) in the exclusion results: row 5's
    back-pressure law is its two constants, row 6's UA_PORT is ua_port, row 9's members name their
    constants in their text (the rich slope, the three flame terms), row 10's is the driveline efficiency."""
    if e6_row in (5, 6):
        return [(e6_row, None)]
    if e6_row == 9:
        hits = [c for c in excl.get(9, {}) if c in member]
        if not hits:
            raise KeyError(f"E6 row 9 sized no constant named in {member!r}")
        return [(9, c) for c in hits]
    if e6_row == 10:
        return [(10, None)]
    raise KeyError(f"no E6 row {e6_row} perturbs {member!r}")


def _exclusions(contract, excl):
    """{row: [members it is excluded for]} and decision 59's counting rule per row
    (epa_stats.excluded_for_every_listed_constant over the contract's tests_lists)."""
    import epa_stats
    lists = contract["tests_lists"]["lists"]
    by_row, every = {}, {}
    for row, members in lists.items():
        verdict = {}
        for m in members:
            n = m["perturbed_by_E6_row"]
            if n is None:
                continue
            if n not in excl:
                verdict = None
                break
            vals = []
            for (rr, c) in _member_constants(m["member"], n, excl):
                src = excl[rr]["all"] if c is None else excl[rr][c]
                vals.append(src.get(row))
            verdict[m["member"]] = None if any(v is None for v in vals) else all(vals)
        if verdict is None or any(v is None for v in verdict.values()):
            every[row] = None
            by_row[row] = None
            continue
        by_row[row] = sorted(k for k, v in verdict.items() if v)
        every[row] = epa_stats.excluded_for_every_listed_constant(row, verdict, tests_lists=lists)
    return by_row, every


def _provenance(name, *, source, token, armed, view):
    """WP3_INTERFACES 7.1 and 7.7: the hashes the run was armed on (every one re-checked by refusals
    against the tree before the token was issued), HEAD, and the versions."""
    clean, dirty = epa_freeze.git_clean(sorted(armed["code"]), root=source.root)
    return {"engine": name, "contract": armed["contract"],
            "git": {"head": token.head, "step2_clean": clean, "dirty": list(dirty)},
            "code_sha_text": armed["code"], "plant_sha": armed.get("plant_sha"), "data": armed["data"],
            "view_sha256": view.sha256, "versions": epa_freeze.versions(),
            "freeze": {k: armed["freeze"].get(k) for k in ("sha_text", "commit")},
            "complete": {k: armed["complete"].get(k) for k in ("sha_text", "commit")},
            "derived_sha": armed["derived"]["derived_sha"], "engine_sha": armed["engine_sha"],
            "dump_sha256": armed.get("dump_sha256"),
            "tightenings": {k: armed["tightenings"].get(k) for k in ("sha_text", "commit", "plant")},
            "d3": armed.get("d3"), "armed_blob": token.armed_blob}


@dataclasses.dataclass(frozen=True)
class _RowRead:
    """A C3 row read back from the record d3_rows.run_chain returns (StatResult.as_json's keys), for the
    two uses this file has for it: section 7's P5 (epa_stats.section7 reads no_statistic, reason, label,
    kappa) and E6 row 10's exclusion (epa_stats.excluded_for reads row, E, u.u_val, no_statistic). The
    values are the computed doubles themselves, never re-derived (run_chain returns them unserialised)."""
    row: str
    kind: str
    E: object
    u: object
    no_statistic: bool
    reason: object
    label: object
    kappa: object

    @classmethod
    def of(cls, row, rec):
        u = rec.get("u")
        return cls(row=row, kind=rec["kind"], E=rec["E"], no_statistic=bool(rec["no_statistic"]),
                   u=None if u is None or u.get("u_val") is None else _UVal(u_val=u["u_val"]),
                   reason=rec.get("reason"), label=rec.get("label"), kappa=rec.get("kappa"))


@dataclasses.dataclass(frozen=True)
class _UVal:
    u_val: float


def _d3_chain(name, *, source, armed, view, contract, frozen, jobs):
    """C3 on the CX-9 (Mazda) or C4's chain on the Accord (Honda) (results/ENGINE_THRESHOLDS.md section 5;
    PLAN.md 6.5), through d3_rows.run_chain, the chain's one composition (d3_rows' "the one entry point
    validate_epa.py run calls"; mistake 10): the files ARMED.json hashed (re-hashed by refusals), the
    contract's segment rules (checked first against the contract's own text), the summary workbook, the
    frozen plant, eta at the contract's 0.92 (E6 row 10's nominal) and at row 10's two efficiencies.
    Returns (the c3.json or c4_accord.json record, {row: _RowRead}, E6 row 10).

    run_chain returns the record's JSON rows only, so section 7's P5 rows (C3b, C3d) and row 10's
    exclusion are read back from them (_RowRead). A variant at eta's ends is the nominal row moved by the
    record's own dE (d3_rows.eta_rows): its E is base E + dE, which may differ from the variant's computed E
    in the last bit, and nothing here compares at that resolution (|dE| < u_val, epa_stats.excluded_for)."""
    import d3_rows
    import epa_fit
    import epa_rows
    import epa_stats
    import plant as plant_model
    eta, radius_gap = c3_eta_and_radius_gap(contract, _read_text(source.contract_md))
    chans_name, summary_name, descriptive = D3_ENGINE[name]
    chans, sspec = getattr(d3_rows, chans_name), getattr(d3_rows, summary_name)
    bad = d3_rows.check_rules_against_contract(d3_rows.CONTRACT_SEGMENTS, contract["c3_segments"])
    if bad:
        raise RuntimeError(f"d3_rows.CONTRACT_SEGMENTS differ from the contract's c3_segments: {bad}")
    d3 = armed["d3"]
    folder = d3["data_folder"]
    entries = d3["c3_files"] if D3_SOURCES[name]["c3"] else d3["accord"]
    files = tuple((e["file"].rsplit("/", 1)[-1].split()[0], os.path.join(folder, *e["file"].split("/")))
                  for e in entries)
    # decision 80: only the rows of the tests this chain reads, each test's base phase rows
    summary = d3_rows.read_summary(os.path.join(folder, *d3["summary"]["file"].split("/")), spec=sspec,
                                   tests=tuple(t for t, _ in files))
    # decision 63: the D3 fuel's AFR_st taken as the EPA Mazda batch's (its steady table's fuel)
    mazda_steady = next(t.name for t in epa_rows.TABLES["mazda_25t"] if t.role == "steady")
    afr_st = epa_rows.calibration_contract("mazda_25t", source=source).fuel_by_table[mazda_steady].afr_st
    table = next(t.name for t in epa_rows.TABLES[name] if t.role == "steady")
    ect_absent = ACCORD_ECT_K_DECLARED if descriptive else None
    lo, hi = d3_rows.row10_etas(contract["perturbations_E6"])
    facts = epa_rows.engine_facts(name, source=source)
    # the EPA map fuel's heating value, BTU/lbm, from the engine's epa_engine.json (alpha_fuel), where the
    # contract takes it (results/ENGINE_THRESHOLDS.md section 5: "18,447 (epa_engine.json, alpha_fuel)" on
    # the Mazda; thresholds/document.py checks that rounding): the model's fuel is scaled by it over the
    # D3 fuel's, the engine's own map fuel for C4's Accord chain too
    epa_lhv = float(facts.alpha_fuel[EPA_MAP_LHV_KEY])
    ctx = d3_rows.c3_context(
        engine_name=name, view=view, displacement_l=facts.displacement_l,
        charge_range_c=tuple(contract["engines"][name]["coverage"]["fired_intake_temp_c"]),
        fired_bmep_bar=epa_stats.FIRED_BMEP, min_segments=epa_stats.MIN_CLUSTERS,
        u_input=d3_rows.u_input_c3(eta_lo=lo, eta_hi=hi, eta=eta, radius_gap=radius_gap,
                                   flow_per_pct_torque=view.propagation_b58["used"]["flow_pct_per_pct_torque"]),
        epa_lhv_btu_per_lbm=epa_lhv, descriptive_only=descriptive)
    body = d3_rows.run_chain(
        files, summary=summary, channels=chans, car=frozen.car, model=epa_fit.RowModel(frozen, fuels=view.fuel_by_table),
        context=ctx, rules=d3_rows.CONTRACT_SEGMENTS, channel_rules=d3_rows.CHANNEL_RULES,
        dtheta=float(plant_model.DTHETA_DEG), eta=eta, etas_row10=(lo, hi), afr_st=afr_st,
        baro_kpa=D3_BARO_KPA_DECLARED, u_afr_st=None, engine_name=name, table=table,
        fuel=view.fuel_by_table[table], ect_k_if_absent=ect_absent, mapper=lambda fn, items: _map(fn, items, jobs))
    rows = {r: _RowRead.of(r, v) for r, v in body["rows"].items()}
    excluded = {}
    if not descriptive:
        variants = [{r: dataclasses.replace(rows[r], E=None if (rows[r].E is None or d is None) else rows[r].E + d,
                                            no_statistic=rows[r].no_statistic or d is None)
                     for r, d in by.items()} for by in body["eta"].values()]
        excluded = {"all": _excluded(rows, variants, ("C3b", "C3d"))}
    rec = {"schema": C3_SCHEMA, "provenance": None, **body,
           "inputs": {"eta": eta, "eta_row10": [lo, hi], "radius_gap": radius_gap, "epa_map_lhv_btu_per_lbm": epa_lhv,
                      "baro_kpa_where_the_summary_has_none_declared": D3_BARO_KPA_DECLARED,
                      "accord_coolant_k_declared": ect_absent,
                      # decision 79: the summary's modal fuel in gallons, its mass at an ASSUMED density
                      "d3_modal_fuel_g_per_us_gal_assumed": sspec.modal_fuel_to_g,
                      "d3_modal_fuel_u_rel_assumed": sspec.modal_fuel_u_rel}}
    return rec, rows, {"rows": body["eta"], "excluded": excluded}


def _read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


_ROW11_TEXT = re.compile(r"^\+-\s*([0-9]+(?:\.[0-9]+)?)\s*K\b")
_D_PROBE_TEXT = re.compile(r"every d row's probe is \+-\s*([0-9]+(?:\.[0-9]+)?)\s*%")
_CAD_TEXT = re.compile(r"\+-\s*([0-9]+(?:\.[0-9]+)?)\s*crank degrees for IVC and EVO")


def e6_sizes(contract):
    """E6 row 11's charge-temperature shift in K and every d row's relative probe, read from the contract
    JSON's perturbations_E6 where version 4 states them, in words version 5 kept: row 11's band ("+-6.3 K
    (the B58's input uncertainty, ...)") and row 5's ("... every d row's probe is +-10 % (version 4, decision 59 ...)"),
    which rows 6 and 9 take "as row 5". The percentage is parsed as the decimal printed, scaled by 1e-2 in
    the parse. And row 9's "+-10 crank degrees for IVC and EVO", the two angles' d probe (WP3's fix of 23
    October 2026). A band that does not state one is refused: no number is retyped (mistake 10). Returns
    (row 11's shift K, the d probe relative, the angles' d probe CAD)."""
    by_n = {p.get("n"): p for p in contract["perturbations_E6"]}
    m11 = _ROW11_TEXT.search(by_n.get(11, {}).get("band", ""))
    m5 = _D_PROBE_TEXT.search(by_n.get(5, {}).get("band", ""))
    m9 = _CAD_TEXT.search(by_n.get(9, {}).get("band", ""))
    if m11 is None or m5 is None or m9 is None:
        raise ValueError("the contract's perturbations_E6 does not state "
                         + " and ".join(w for w, m in (("row 11's shift in K", m11), ("the d rows' probe", m5),
                                                       ("row 9's crank degrees for IVC and EVO", m9)) if m is None))
    # the d probe is also read by epa_stats.e6_band_values, the completion's parse (calibrate_epa.py
    # complete); the two must agree, or the probe the completion reports is not the one run here
    import epa_stats
    d_probe = float(m5.group(1) + "e-2")
    try:
        shared = epa_stats.e6_band_values(contract["perturbations_E6"])["d_probe_rel"]
    except ValueError:
        shared = d_probe
    if shared != d_probe:
        raise ValueError("the d rows' probe read here is not epa_stats.e6_band_values' (mistake 10)")
    return float(m11.group(1)), d_probe, float(m9.group(1))


_ETA_TEXT = re.compile(r"driveline efficiency,?\s+([0-9]+\.[0-9]+)\s*$")
_RADIUS_TEXT = re.compile(r"N/V-to-D3\s+radius\s+gap,\s+([0-9]+(?:\.[0-9]+)?)\s*%\s+uniform")


def c3_eta_and_radius_gap(contract, contract_md_text):
    """C3's nominal driveline efficiency and the N/V-to-D3 radius gap, read where the contract states them:
    E6 row 10's constant in the JSON ("the driveline efficiency, 0.92"; d3_rows.row10_etas reads its band
    from the same entry) and section 5's input uncertainty in the MD ("the N/V-to-D3 radius gap, 1.6 %
    uniform"), the gap as the decimal the text prints, scaled by 1e-2 in the parse (float("1.6e-2")).
    thresholds/contract.py holds both as ETA and RADIUS_GAP, which validate_epa may not import
    (WP3_INTERFACES 3.1: interp only); test_validate_guards checks the two readings agree. A text that
    does not state one, or states the gap twice differently, is refused (mistake 10: no retyped number)."""
    row = [p for p in contract["perturbations_E6"] if p.get("n") == 10]
    m = _ETA_TEXT.search(row[0]["constant"]) if len(row) == 1 else None
    gaps = {g for g in _RADIUS_TEXT.findall(contract_md_text)}
    if m is None or len(gaps) != 1:
        raise ValueError("the contract does not state E6 row 10's driveline efficiency and section 5's radius gap "
                         f"once each (efficiency {'found' if m else 'not found'}, {len(gaps)} gap readings)")
    return float(m.group(1)), float(gaps.pop() + "e-2")


# ---------------------------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------------------------
def summary(*, source):
    """results/EPA_VALIDATION/summary.json from the three rows.json (WP3_INTERFACES 7.11), each defect
    re-run's beside its first (both are reported, section 7). section7's level_850c_label, drop and
    drop_rows are read as rows.json holds them (epa_stats.section7)."""
    root = source.root
    missing = [n for n in common.EPA_ENGINES if not os.path.isfile(_p(root, f"{val_dir(n)}/{ROWS}"))]
    if missing:
        raise Refused([f"no {val_dir(n)}/{ROWS}: run the engine's validation first" for n in missing])
    out = {"schema": SUMMARY_SCHEMA, "engines": {}, "drop_order": DROP_ORDER, "inputs": {}}
    for n in common.EPA_ENGINES:
        rec = read_records(root, n)
        files = [ROWS] + [rerun_name(ROWS, k) for k, fs in rec.reruns.items() if rerun_name(ROWS, k) in fs]
        entry = _summary_entry(root, n, ROWS)
        entry["reruns"] = {f: _summary_entry(root, n, f) for f in files[1:]}
        out["engines"][n] = entry
        for f in files:
            out["inputs"][f"{val_dir(n)}/{f}"] = common.sha_text(_p(root, f"{val_dir(n)}/{f}"))
    epa_freeze.write_json_atomic(_p(root, f"{VAL_REL}/{SUMMARY}"), out)
    return out


def _summary_entry(root, name, fname):
    rel = f"{val_dir(name)}/{fname}"
    rows = _load(_p(root, rel))
    s7 = rows.get("section7") or {}
    missing = [k for k in ("level_850c_label", "drop", "drop_rows") if k not in s7]
    if missing:
        raise KeyError(f"{rel}: section7 holds no {missing} (rows.json's layout, WP3_INTERFACES 7.7)")
    # the labels as reported: E6 row 12's rows by the worse of their two readings (epa_stats.reported_labels),
    # never the snapped reading alone (WP3's fix of 23 October 2026)
    if "reported" not in rows:
        raise KeyError(f"{rel}: holds no `reported` labels (rows.json's layout, WP3_INTERFACES 7.7)")
    rep = rows["reported"]
    # decision 83: the steady-only TIT reading's labels beside the primary's, a sensitivity read by nothing here
    # that decides (None for a rows.json without it)
    sto = rows.get("steady_only_tit")
    return {"rows_sha_text": common.sha_text(_p(root, rel)),
            "labels": {r: v.get("label") for r, v in sorted(rep.items())},
            "kappa": {r: v.get("kappa") for r, v in sorted(rep.items())},
            "level_850c_label": s7["level_850c_label"], "drop": s7["drop"], "drop_rows": s7["drop_rows"],
            "c5_recheck_margin": rows.get("c5_recheck_margin"),
            "steady_only_tit": None if sto is None else {
                "reading": sto.get("reading"), "decides": False,
                "labels": {r: v.get("label") for r, v in sorted((sto.get("statistics") or {}).items())},
                "E": {r: v.get("E") for r, v in sorted((sto.get("statistics") or {}).items())}}}


# ---------------------------------------------------------------------------------------------
# C5's re-check margin (decision 64)
# ---------------------------------------------------------------------------------------------
def c5_recheck_margin(e1a):
    """Decision 64 as version 4 reads it (kept by version 5): |E1a| and u_val of E1a's worst deciding line,
    the one with the largest |E| (of two equal, the larger u_val); the margin max(R, |E| + 2u_val); every deciding
    line's |E| + 2u_val beside it. `e1a` is the held-out E1a StatResult (R, deciding, lines, each line
    with E and u.u_val). With no deciding line the margin is R, flagged."""
    deciding = set(e1a.deciding)
    lines = [ls for ls in e1a.lines if ls.line in deciding and ls.u is not None]
    beside = {ls.line: abs(ls.E) + 2.0 * ls.u.u_val for ls in lines}
    # E1a is in percent; epa_stats.c5_climb compares the FRACTION |demand / threshold - 1| (and refuses a
    # margin of 1 or more), so the fraction is recorded beside the percent, its unit named (WP3's fix of 23
    # October 2026: the contract review's unit trap for WP5)
    if not str(e1a.unit).lstrip().startswith("%"):
        raise ValueError(f"c5_recheck_margin: E1a's unit {e1a.unit!r} is not a percent")
    if not lines:
        return {"worst_line": None, "E": None, "u_val": None, "R": e1a.R, "margin": e1a.R, "lines": beside,
                "margin_unit": "percent", "margin_fraction": float(e1a.R) * 1e-2, "no_deciding_line": True}
    worst = max(lines, key=lambda ls: (abs(ls.E), ls.u.u_val))
    margin = max(e1a.R, abs(worst.E) + 2.0 * worst.u.u_val)
    return {"worst_line": worst.line, "E": worst.E, "u_val": worst.u.u_val, "R": e1a.R,
            "margin": margin, "margin_unit": "percent", "margin_fraction": float(margin) * 1e-2, "lines": beside,
            "no_deciding_line": False}


def _named(name):
    """One of the three EPA engines: there is no default engine (mistake 1)."""
    if not isinstance(name, str) or name not in D3_OUTPUT:
        raise KeyError(f"validate_epa needs one of {sorted(D3_OUTPUT)}, not {name!r} (no default engine)")
    return name


# ---------------------------------------------------------------------------------------------
# The command line
# ---------------------------------------------------------------------------------------------
def main(argv):
    ap = argparse.ArgumentParser(prog="validate_epa.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for cmd in ("arm", "run"):
        p = sub.add_parser(cmd)
        p.add_argument("--engine", required=True, choices=sorted(D3_OUTPUT))
        p.add_argument("--jobs", required=True, type=int)
        p.add_argument("--defect-rerun", dest="reason")
        p.add_argument("--fix-commit")
    sub.add_parser("summary")
    a = ap.parse_args(argv)
    import epa_rows
    source = epa_rows.Source.repository()
    if a.cmd == "summary":
        out = summary(source=source)
        print(f"validate_epa summary: {len(out['engines'])} engines; wrote {VAL_REL}/{SUMMARY}")
        return 0
    if (a.reason is None) != (a.fix_commit is None):
        ap.error("--defect-rerun and --fix-commit go together (PLAN.md 6.1)")
    defect = None if a.reason is None else Defect(reason=a.reason, fix_commit=a.fix_commit)
    try:
        if a.cmd == "arm":
            entry = {"subcommand": "arm", "argv": list(argv), "started_utc": _now(), "versions": epa_freeze.versions()}
            try:
                rec = arm(a.engine, source=source, jobs=a.jobs, data_folder=common.DATA_FOLDER, defect=defect)
            except Refused as exc:
                _log_invocation(source.root, a.engine, dict(entry, ended_utc=_now(),
                                                            outcome="refused: " + "; ".join(exc.problems)))
                raise
            _log_invocation(source.root, a.engine, dict(entry, ended_utc=_now(), outcome="ok"))
            c = rec["held_out_counts"]
            print(f"validate_epa arm {a.engine}: {len(ARM_STEPS)} steps passed; held-out counts: "
                  + ", ".join(f"{k} {v}" for k, v in c.items()))
            print(f"wrote {val_dir(a.engine)}/{ARMED}; commit it alone, then run")
            return 0
        run(a.engine, source=source, jobs=a.jobs, defect=defect)
        return 0
    except Refused as exc:
        print(f"validate_epa {a.cmd} {a.engine}: refused")
        for p in exc.problems:
            print(f"  - {p}")
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""epa_freeze.py -- the EPA calibration's hashes, its derived file, its freeze record and the
frozen-plant dump (build step 2 of decision 24, WP3; written 23 October 2026).

    nothing to run: calibrate_epa.py (fit, complete, check) and validate_epa.py (arm) call it

WHAT IT IS FOR. Rule 0 of the validation contract (results/ENGINE_THRESHOLDS.md, version 5) is
that nothing changes after a fit, and the held-out run is computed once, on the plant the fit
froze. Both are claims about files, so they hold only if every file is hashed by one rule and
written by one writer. This module is that writer and those rules (docs/build_step_2/PLAN.md 5.8
and 8.3, as docs/build_step_2/AMENDMENTS.md C3, C10, B10 and F7 amend them; the interface record
docs/build_step_2/WP3_INTERFACES.md sections 4 and 5.4):

  * write_json_atomic   every JSON output of step 2, in thresholds.common.write_json's form, to a
                        temporary file in the same folder and then os.replace, so an interrupted
                        write leaves the old file or none, never half of one; NaN is refused
  * the derived file    data/engines/<id>/derived_params.json is written by write_derived and by
                        nothing else (CLAUDE.md: never by hand): the three FROZEN_SECTIONS at the
                        freeze, the completion sections after it, bookkeeping in top-level "_" keys
                        only (fingerprint.derived_sha drops those), no timestamp. A rewrite that
                        moves a frozen section is refused unless the defect route names its fix
                        commit (PLAN.md 5.6)
  * the freeze record   results/EPA_CALIBRATION/<id>/freeze.json: the form, the frozen sections'
                        hash -- engines.frozen_sections_sha256, never a copy (its docstring;
                        mistake 10) --, the derived file, the contract, the data, the code, the
                        plant and the fit outputs it came from. Written once: a second freeze is the
                        defect route, which first moves the old run to defect_<k>/
  * the dump            frozen_plant_dump, the frozen plant evaluated on a fixed grid of SYNTHETIC
                        inputs (never an EPA row) and hashed, so validate_epa.py arm can show the
                        plant it is about to validate is the plant that was frozen, bit for bit
  * provenance          the block every output of both scripts carries (WP3_INTERFACES.md 7.1)

THE HASH RULES (PLAN.md 8.3; WP3_INTERFACES.md section 4). Code, specs, the contract and every
results/ output: thresholds.common.sha_text (CRLF read as LF, so a teammate's LF clone gives the
same hash). The EPA tables and epa_engine.json: thresholds.common.sha_raw (data/engines/.gitattributes
stores them byte for byte). epa_channels.csv: its git blob id, never opened, since its minima and
maxima span every row, held-out rows included (PLAN.md 4.5; amendment C3). A derived file: its
sha_text and fingerprint.derived_sha. A blob at a commit: sha256 of `git cat-file blob
<commit>:<path>`, which equals the working file's sha_text (the blob is LF; core.autocrlf=true).

WHAT IT NEVER DOES. It reads no EPA value: it hashes the tables (raw bytes, never parsed), takes
the manifest's hash from epa_rows, and evaluates the plant only on the dump's synthetic grid. It
never writes outside the root it is given: every function that reads or writes a file takes that
root explicitly (`root`, a git work tree: the repository, or a test's temporary one), so a test
never touches data/ or results/ (amendment C5). It imports no validate_epa and no thresholds.split
(WP3_INTERFACES.md 3.1), and epa_rows only inside the two functions that need it, so the module
imports without it. The held-out token is not here: amendment C3 confines Token and
verify_for_validation to validate_epa.py; tree_record gives arm and the token's check one
definition of the tree-side hashes they compare (mistake 10).
"""
import dataclasses
import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sys

import numpy as np

import derived
import engine_env
import engines
import fingerprint
import plant as plant_model
import thermal
from thresholds import common

REPO = common.REPO

# THE STEP-2 FILES (WP3_INTERFACES.md 5.4; PLAN.md 5.8's code list). STEP2_CODE is the code whose
# sha_text the freeze, fit_A.json (amendment C10) and ARMED.json record; CODE_HASHED adds the two
# generator modules epa_rows imports helpers from (amendment C2), since their code runs in the fit.
STEP2_CODE = ("epa_rows.py", "epa_stats.py", "epa_fit.py", "epa_freeze.py", "calibrate_epa.py",
              "k3_knee.py", "epa_coefficients.py", "validate_epa.py", "d3_rows.py")
STEP2_TESTS = ("test_contract_pinned.py", "test_epa_rows.py", "test_epa_stats.py", "test_epa_fit.py",
               "test_epa_freeze.py", "test_k3_knee.py", "test_epa_coefficients.py",
               "test_validate_guards.py", "test_d3_rows.py", "test_calibrate_epa.py", "test_epa_plants.py",
               "test_epa_fixtures.py")
# THE RUN 1 INPUTS OUTSIDE THE STEP-2 CODE AND THE PLANT (WP3's fourth fix of 24 October 2026, on the fourth Run 1
# review's finding): the fit reads the B58's engine spec (epa_fit._b58_cycle, engines.typed_engine("b58"): the
# ridge's centre in S2 and S4, form A's and S2's starts, S6's reference knock_a, T0's truths; and calibrate_epa.
# e6_conventions, E6 rows 2 and 3, reads its [fuel]), the completion reads evaluate.py (k3_knee and
# epa_coefficients take DT, DURATION, EPISODES[0] and episode_cycle from it: the K3 knee, the delivery run, the
# climb cell), and every subcommand compares the environment with requirements-lock.txt (version_problems). None
# was in an EPA engine's plant_files or here, so an edit to one during Run 1, or a commit of one between the fit
# and the completion, passed every guard and left records no commit reproduces. They are hashed with the code:
# t0 and fit require them committed and clean (_clean_code), fit compares T0's (t0_code_problems), poison, e6 and
# complete the freeze's (_frozen_code_guard), and the arming lists every change (validate_epa._arm_code,
# after_freeze_problems). engines.spec_files("b58")[0] is the spec named here (test_epa_freeze checks it).
RUN1_INPUTS = ("evaluate.py", "engine_specs/b58.toml", "requirements-lock.txt")
CODE_HASHED = STEP2_CODE + ("thresholds/split.py", "thresholds/common.py") + RUN1_INPUTS

# Where the calibration's outputs live (WP3_INTERFACES.md section 6), repository-relative. epa_rows, which
# imports no plant module and so not this one, holds the same folder as CALIBRATION_REL for its held-out
# counts' guard; test_epa_freeze pins the two equal (mistake 10).
CALIBRATION_DIR = "results/EPA_CALIBRATION"

# THE DERIVED FILE'S LAYOUT (PLAN.md 5.8; WP3_INTERFACES.md 7.3), from engines.EPA_DERIVED_FIELDS,
# never retyped: each section's keys are exactly the fields that map to it, and any other key is
# refused (amendment B11's lesson applied to the file: a pinned key set, checked, with a control in
# test_epa_freeze.py). The frozen sections are engines.FROZEN_SECTIONS; the rest are completed after
# the freeze from no EPA data. Bookkeeping lives in exactly these two top-level "_" keys.
COMPLETION_SECTIONS = ("deliverable_torque", "k3", "loop")
BOOKKEEPING_KEYS = ("_about", "_inputs")
INPUTS_KEYS = ("contract_commit", "freeze_record", "view_sha256", "manifest_sha256")


def _section_keys():
    out = {}
    for (_rec, _field), (sec, key) in engines.EPA_DERIVED_FIELDS.items():
        out.setdefault(sec, set())
        if key is not None:
            out[sec].add(key)
    return {s: frozenset(k) for s, k in out.items()}


SECTION_KEYS = _section_keys()
if set(SECTION_KEYS) != set(engines.FROZEN_SECTIONS) | set(COMPLETION_SECTIONS) or \
        SECTION_KEYS["deliverable_torque"] or set(engines.FROZEN_SECTIONS) & set(COMPLETION_SECTIONS):
    raise RuntimeError("epa_freeze: engines.EPA_DERIVED_FIELDS no longer maps onto the frozen sections "
                       f"{engines.FROZEN_SECTIONS} and the completion sections {COMPLETION_SECTIONS}")
# The fields that are not a float (engines.CONVERT_BY_SET["epa"]: _str, _int, the two lists, the
# table). Every other field must be a Python float: engines' _number would take an int and convert
# it, but an int and its float write differently in JSON, so the frozen hash would depend on which
# one the fit happened to hand over (amendment B10: convert with float() before, never after).
_STR_FIELDS = {("cycle", "form")}
_INT_FIELDS = {("ecu", "cam_on")}
_LIST_FIELDS = {("boost_ceiling", "envelope_flow"), ("boost_ceiling", "envelope_pr")}

FREEZE_SCHEMA = "epa-freeze/1"
FREEZE_KEYS = ("schema", "form", "frozen_sections_sha256", "derived", "contract", "data", "code", "plant",
               "fits", "versions", "git_head", "flags", "all_row_depth_edge")
# The flag the chosen fit raises when S3b's depth sits at the invariant edge 1 - lam_floor, an all-row quantity
# (amendment C1 makes lam_floor the policy clip's and the dump grid's only; HANDOFFS.md WP3 item 1 orders the
# minimum): copied into freeze.json, so that the arming and the results show it (WP3's second fix of 23
# October 2026, on the isolation and fit reviews' finding FS4; what follows is the team's to decide before Run 1).
ALL_ROW_DEPTH_FLAG = "S3b_depth_set_by_the_all_row_floor"
PROVENANCE_KEYS = ("engine", "contract", "git", "code_sha_text", "plant_sha", "data", "view_sha256", "versions")


class FreezeRefusal(Exception):
    """A freeze-side guard refused: the message says which and how it is removed."""


class AlreadyFrozen(FreezeRefusal):
    """freeze.json exists: a re-freeze is the defect route (PLAN.md 5.6)."""


class FrozenSectionsChanged(FreezeRefusal):
    """A frozen section differs from the one the freeze record (or the file on disk) hashed."""


class DerivedPathMismatch(FreezeRefusal):
    """An engine spec names another derived file or freeze record than this module writes."""


class GitError(FreezeRefusal):
    """A git command failed, or git answered something a guard cannot accept."""


@dataclasses.dataclass(frozen=True)
class DerivedRecord:
    """A derived file's two hashes (PLAN.md 8.3): sha_text and fingerprint.derived_sha (top-level
    "_" keys dropped), beside its repository-relative path."""
    path: str
    sha_text: str
    derived_sha: str

    def as_json(self):
        return {"path": self.path, "sha_text": self.sha_text, "derived_sha": self.derived_sha}


@dataclasses.dataclass(frozen=True)
class DefectRoute:
    """The defect route's authority to rewrite frozen sections (PLAN.md 5.6; amendment C10): the
    assertion that failed and the commit that fixed it. The commit must exist and be an ancestor
    of HEAD: the fix is committed before the calibration re-runs from S0."""
    reason: str
    fix_commit: str


@dataclasses.dataclass(frozen=True)
class Dump:
    """The frozen-plant dump's record (PLAN.md 5.8): the sha256 of every array's float64 bytes in
    key order, how many values, and the keys in that order."""
    sha256: str
    n_values: int
    keys: tuple

    def as_json(self):
        return {"sha256": self.sha256, "n_values": self.n_values, "keys": list(self.keys)}


# ------------------------------------------------------------------ files and git
def _root(root):
    """`root` as an absolute directory, refused if it is not one (no default root: a forgotten
    root must never mean the repository, or a test would write into data/)."""
    if not isinstance(root, str) or not os.path.isdir(root):
        raise TypeError(f"epa_freeze needs `root`, the git work tree to read and write in; got {root!r}")
    return os.path.abspath(root)


def _abs(path, root):
    """`path` as an absolute path: a relative one is taken relative to `root`, not to the process's
    working folder, so "results/..." means the same file whoever calls."""
    return os.path.abspath(path if os.path.isabs(path) else os.path.join(_root(root), path))


def _rel(path, root):
    """`path` relative to `root` with forward slashes, refused if it lies outside it."""
    try:
        rel = os.path.relpath(_abs(path, root), _root(root))
    except ValueError:                     # another drive, on Windows
        rel = os.pardir
    if rel == os.pardir or rel.startswith(os.pardir + os.sep) or os.path.isabs(rel):
        raise ValueError(f"{path} lies outside the work tree {root}")
    return rel.replace(os.sep, "/")


def _git(root, *args, stdin=None, binary=False):
    """A git command in `root`; its CompletedProcess, any exit code. Paths in argv name only code,
    results/ and the contract, except `git ls-files` and `git hash-object`, the two calls
    calibrate_epa.py's audit hook lets name data/engines/ (amendment C3)."""
    kw = {} if binary else {"text": True, "encoding": "utf-8"}
    return subprocess.run(["git", *args], cwd=_root(root), capture_output=True, input=stdin, **kw)


def _git_ok(root, *args, stdin=None, binary=False):
    out = _git(root, *args, stdin=stdin, binary=binary)
    if out.returncode != 0:
        err = out.stderr.decode("utf-8", "replace") if binary else out.stderr
        raise GitError(f"git {' '.join(args)} in {root}: exit {out.returncode}: {err.strip()}")
    return out.stdout


PARTIAL_SUFFIX = ".partial"


def write_json_atomic(path, obj):
    """Write `obj` to `path` as thresholds.common.write_json writes (indent 1, LF, ASCII, floats as
    their repr), atomically, and return the sha_text written (WP3_INTERFACES.md 2.6; PLAN.md 6.1
    "each output is written atomically").

    The object is first serialised with allow_nan=False, so a NaN or an infinity is refused before
    anything is written: a None stands for an absent value, NaN never reaches a file. It is then
    written by common.write_json itself -- the one writer of that form (mistake 10) -- into
    `path` + PARTIAL_SUFFIX in the same folder, and moved over the target with os.replace, which is
    atomic on one volume: an interruption at any point (an exception, a KeyboardInterrupt) leaves
    the old file, or none, and the partial file is removed. The partial file's name is fixed, not
    random, so the set of paths a subcommand opens -- which calibrate_epa.py writes to run.json and
    compares with its allowlist (amendment C3) -- is the same on every run; one left by a killed
    process never replaced the target, and is overwritten."""
    json.dumps(obj, allow_nan=False)
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + PARTIAL_SUFFIX
    try:
        common.write_json(tmp, obj)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    return common.sha_text(path)


def _read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


RUN_RECORD = "run.json"


def readable_record(rel):
    """Whether read_json reads the repository-relative path `rel`: a record of an EPA engine's calibration
    folder (results/EPA_CALIBRATION/<id>/...), an EPA engine's derived file (derived_relpath), or a run.json
    at the top of `root` (dry-load's, in its scratch folder). Nothing else: the contract, a table, an
    epa_engine.json or a validation record is never a calibration record (WP3's second fix of 23 October
    2026, on the isolation review's finding that read_json read any JSON under the root, the contract with
    its held-out keys among them)."""
    import epa_rows
    if rel == RUN_RECORD:
        return True
    parts = rel.split("/")
    base = CALIBRATION_DIR.split("/")
    if parts[:len(base)] == base and len(parts) > len(base) + 1 and parts[len(base)] in epa_rows.TABLES:
        return True
    out = set()
    for n in epa_rows.TABLES:
        try:
            out.add(derived_relpath(n))
        except (KeyError, ValueError, DerivedPathMismatch):
            continue
    return rel in out


def read_json(path, *, root):
    """A JSON record inside the work tree `root` (a relative `path` is taken relative to it): the one
    reader of calibrate_epa.py's own records (freeze.json, fit_<form>.json, the e6 files, run.json,
    defects.json) and of the derived file, since calibrate_epa.py opens no file itself
    (WP3_INTERFACES.md 3.2, N8; added by WP3's integration, 23 October 2026). A path outside `root` is
    refused, so a record is never read from another tree by accident, and so is one readable_record does
    not admit (WP3's second fix of 23 October 2026)."""
    rel = _rel(path, root)
    if not readable_record(rel):
        raise ValueError(f"read_json: {rel} is not a calibration record or a derived file (readable_record)")
    return _read_json(_abs(path, root))


DEFECTS = "defects.json"
DEFECT_DIR = re.compile(r"defect_([1-9][0-9]*)")


def move_run_to_defect(name, *, root):
    """The defect route's first step (PLAN.md 5.6; WP3_INTERFACES.md 5.5.2; amendment C10): every output
    of the engine's calibration folder, results/EPA_CALIBRATION/<id>/, moved verbatim (os.replace, no
    byte rewritten) into its next defect_<k>/, k = 1 + the largest k there; the earlier defect_<j>/
    folders and defects.json stay where they are. Returns k. Refused when the folder holds no output,
    since there is then no run to keep: the defect route re-runs a calibration that ran."""
    folder = calibration_dir(name, root=root)
    if not os.path.isdir(folder):
        raise FreezeRefusal(f"move_run_to_defect: {_rel(folder, root)} does not exist: no run to move")
    names = sorted(os.listdir(folder))
    ks = [int(m.group(1)) for n in names for m in [DEFECT_DIR.fullmatch(n)] if m]
    moving = [n for n in names if n != DEFECTS and not DEFECT_DIR.fullmatch(n)]
    if not moving:
        raise FreezeRefusal(f"move_run_to_defect: {_rel(folder, root)} holds no output of a run to move")
    k = 1 + max(ks, default=0)
    dst = os.path.join(folder, f"defect_{k}")
    os.makedirs(dst)
    for n in moving:
        os.replace(os.path.join(folder, n), os.path.join(dst, n))
    return k


DEFECT_KEYS = ("k", "run_invocation", "found_by", "assertion", "fix_commit", "previous_run")


def defect_entry_problems(entry):
    """Why `entry` is not a defects.json entry in the layout append_defect writes, as a list (empty when it
    is): a dict holding exactly DEFECT_KEYS, k and run_invocation positive ints, the rest strings. The one
    definition of the layout, for append_defect and validate_epa.py arm (mistake 10; WP3's second fix of 23
    October 2026, on the test review's finding that arm admitted entries the writer would refuse)."""
    if not isinstance(entry, dict) or sorted(entry) != sorted(DEFECT_KEYS):
        return [f"an entry holds exactly {list(DEFECT_KEYS)}"]
    out = [f"{key} is a positive int" for key in ("k", "run_invocation")
           if type(entry[key]) is not int or entry[key] < 1]
    out += [f"{key} is a string" for key in ("found_by", "assertion", "fix_commit", "previous_run")
            if not isinstance(entry[key], str)]
    return out


def append_defect(name, entry, *, root):
    """Append one entry to the engine's defects.json (WP3_INTERFACES.md 7.2: [{k, run_invocation, found_by,
    assertion, fix_commit, previous_run}]), written atomically; returns the list now on disk. The
    entry's keys are checked, and its fix commit must be a full sha that is a commit and an ancestor of
    HEAD (the fix is committed before the calibration re-runs, PLAN.md 5.6). No wall-clock time: PLAN.md
    5.1 allows one in run.json only, so the entry names the run.json invocation that took the route
    (run_invocation, its k there), whose entry carries the time (WP3's fix of 23 October 2026)."""
    bad = defect_entry_problems(entry)
    if bad:
        raise ValueError(f"append_defect: {'; '.join(bad)}")
    fix = _commit_of(entry["fix_commit"], root)
    if not is_ancestor(fix, "HEAD", root=root):
        raise GitError(f"append_defect: the fix commit {fix} is not an ancestor of HEAD in {root}")
    path = os.path.join(calibration_dir(name, root=root), DEFECTS)
    old = _read_json(path) if os.path.exists(path) else []
    if not isinstance(old, list):
        raise ValueError(f"append_defect: {_rel(path, root)} is not a list")
    new = old + [entry]
    write_json_atomic(path, new)
    return new


# ---------------------------------------------------------------------------------------------------------
# The calibration's own records, checked by the step that builds on them and again at the arming: one
# definition each, for calibrate_epa.py and validate_epa.py (mistake 10; WP3's fix of 23 October 2026)
# ---------------------------------------------------------------------------------------------------------
# Amendment C8: "the poison fit of S0-S3 and S6 is mandatory for all three engines, and a full form-A
# poison fit is mandatory for one"; WP3_INTERFACES.md 5.5.1 chose the engine the drop order keeps last.
FULL_POISON_ENGINE = "mazda_25t"
POISON_SCHEMA = "epa-poison/1"
T0_SCHEMA = "epa-t0/1"
# The subcommands whose invocations later steps build on: a crash, an audit defect or a mismatch in any of
# them, or a path opened outside the allowlist or refused by the audit, stands until the defect route moves
# the run (move_run_to_defect moves run.json with it).
AUDITED_SUBCOMMANDS = ("t0", "fit", "poison", "e6", "complete", "check")


def _bool_leaves(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _bool_leaves(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _bool_leaves(v)
    elif isinstance(obj, bool):
        yield obj


def poison_problems(record, *, engine, frozen_sections_sha256, poisons, run_keys, stages, tied_of):
    """Why poison.json is not C8's proof for the freeze `frozen_sections_sha256`, as a list (empty when it
    is): its schema; one run per poison of `poisons` (epa_rows.POISONS' names); every comparison of every
    run equal (a boolean leaf False fails, and a record with no leaf proves nothing); the garbled contract's
    view and yield equal; the reference stages equal to the frozen fit's recorded ones; all_equal true; the
    frozen sections the proof ran at the freeze's; and on FULL_POISON_ENGINE the full form-A poison fit
    present in every run. THE KEY SETS ARE EXACT (WP3's second fix of 23 October 2026, on the isolation
    review's finding that a record lacking a stage or a comparison passed on its remaining leaves): each run
    holds exactly `run_keys` (epa_fit.POISON_RUN_KEYS) and its stages exactly `stages`
    (epa_fit.poison_run_stages()), and reference_equals_fit exactly tied_of(the record's form)
    (epa_fit.poison_tied_stages). The callers pass epa_fit's definitions; this module imports no epa_fit."""
    out = []
    if not isinstance(record, dict) or record.get("schema") != POISON_SCHEMA:
        return [f"poison.json is not an {POISON_SCHEMA} record"]
    runs = record.get("runs") or {}
    if sorted(runs) != sorted(poisons):
        out.append(f"poison.json holds the runs {sorted(runs)}, not one per poison {sorted(poisons)}")
    for how, r in sorted(runs.items()):
        if not isinstance(r, dict) or sorted(r) != sorted(run_keys):
            out.append(f"poison.json's run {how} does not hold exactly the comparisons {sorted(run_keys)}")
        elif not isinstance(r["stages"], dict) or sorted(r["stages"]) != sorted(stages):
            out.append(f"poison.json's run {how} does not hold exactly the stages {sorted(stages)}")
    ref0 = record.get("reference_equals_fit")
    want_tied = tuple(tied_of(record.get("form")))
    if not isinstance(ref0, dict) or sorted(ref0) != sorted(want_tied):
        out.append(f"poison.json's reference_equals_fit does not hold exactly {sorted(want_tied)}")
    leaves = list(_bool_leaves(runs))
    if not leaves or not all(leaves):
        out.append("a poisoned run's comparison is not equal (C8)")
    for key in ("garbled_contract_view_equal", "garbled_contract_yield_equal", "all_equal"):
        if record.get(key) is not True:
            out.append(f"poison.json's {key} is not true")
    ref = record.get("reference_equals_fit")
    ref_leaves = list(_bool_leaves(ref)) if isinstance(ref, dict) else []
    if not ref_leaves or not all(ref_leaves):
        out.append("poison.json's reference stages are not the frozen fit's recorded stages")
    if record.get("frozen_sections_sha256") != frozen_sections_sha256:
        out.append("poison.json ran at other frozen sections than freeze.json's")
    if engine == FULL_POISON_ENGINE and any((runs.get(h) or {}).get("full_form_a") is None for h in poisons):
        out.append(f"the full form-A poison fit is mandatory on {FULL_POISON_ENGINE} (C8; WP3_INTERFACES.md 5.5.1)")
    return out


def t0_problems(record):
    """Why the fit may not build on t0.json, as a list: T0 must have run (amendment A1: its own step of Run 1,
    before the fit) and passed. A failure is a coding defect (PLAN.md 5.10): the defect route (t0 --defect,
    or fit --defect, which re-runs T0) moves the failed record to defect_<k>/ with its defects.json entry and
    runs T0 again on the fix, whose record must then pass; a failed t0.json is never built on."""
    if not isinstance(record, dict) or record.get("schema") != T0_SCHEMA:
        return [f"t0.json is not an {T0_SCHEMA} record: T0 runs before the fit (amendment A1)"]
    if record.get("pass") is True:
        return []
    return ["T0 did not pass (PLAN.md 5.10: a coding defect, which the defect route fixes and re-runs)"]


def t0_code_problems(record, *, name, root):
    """Why the fit may not build on t0.json now although T0 passed, as a list: T0 certifies the fitting code
    it ran on (amendment A1), so the step-2 code's sha_text (code_shas) and the plant's (plant_sha) must be
    the ones t0.json's provenance recorded (WP3's second fix of 23 October 2026, on the fit review's finding
    that a module edited and committed between t0 and fit went unnoticed). The defect route re-runs T0 on
    the fix."""
    prov = (record or {}).get("provenance") or {}
    out = []
    if prov.get("code_sha_text") != code_shas(root=root):
        out.append("the step-2 code is not the code t0.json's T0 ran on")
    if prov.get("plant_sha") != plant_sha(name):
        out.append("the plant's code and specs (plant_sha) are not those t0.json's T0 ran on")
    return out


# The libraries every subcommand of Run 1 compares (CLAUDE.md's rule 4; amendment D5 pins SciPy because the
# fit depends on its version): the interpreter, NumPy and SciPy, against requirements-lock.txt's pins and
# the versions the run's first records hold (WP3's second fix of 23 October 2026, on the fit review's
# finding that they were recorded and never enforced).
VERSION_KEYS = ("python", "numpy", "scipy")
LOCK_FILE = "requirements-lock.txt"
if LOCK_FILE not in RUN1_INPUTS:                 # the pins are hashed with the code (RUN1_INPUTS; mistake 10)
    raise RuntimeError(f"epa_freeze: {LOCK_FILE} is not among RUN1_INPUTS {RUN1_INPUTS}")


def lock_pins():
    """{python, numpy, scipy: version} as the code tree's requirements-lock.txt pins them (its "# python=="
    line and its numpy== and scipy== lines); a pin it does not hold is None. The code tree's, beside this
    file: the environment that runs is the one this code was captured with."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), LOCK_FILE)
    out = dict.fromkeys(VERSION_KEYS)
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            t = line.strip().lstrip("#").strip()
            for key in VERSION_KEYS:
                if t.lower().startswith(key + "=="):
                    out[key] = t.split("==", 1)[1].strip()
    return out


def version_problems(recorded):
    """Why this process may not continue a Run 1 whose earlier record holds `recorded` (a versions block, or
    None for the first subcommand), as a list: each of VERSION_KEYS of versions() against
    requirements-lock.txt's pin (lock_pins) and against `recorded`."""
    now = versions()
    out = []
    pins = lock_pins()
    for key in VERSION_KEYS:
        if pins[key] is None:
            out.append(f"{LOCK_FILE} pins no {key}")
        elif now[key] != pins[key]:
            out.append(f"{key} {now[key]} is not {LOCK_FILE}'s {pins[key]}")
        if recorded is not None and now[key] != (recorded or {}).get(key):
            out.append(f"{key} {now[key]} is not the {key} the run's earlier record holds")
    # the machine (CLAUDE.md rule 3: every step on one environment, one machine): the platform string the run's
    # earlier record holds, compared too (WP3's fourth fix of 24 October 2026, on the fourth Run 1 review's finding
    # that it was recorded and never compared); requirements-lock.txt pins none
    if recorded is not None and now["platform"] != (recorded or {}).get("platform"):
        out.append(f"the platform {now['platform']} is not the one the run's earlier record holds (one machine)")
    return out


def audit_problems(run_record, *, subcommands):
    """The invocations of run.json ({engine, invocations}) a later step may not build on: those of
    `subcommands` whose outcome is a crash, an audit defect or a mismatch, or that opened a path outside the
    allowlist or had an open refused by the audit (PLAN.md 5.6: each is a coding defect, which only the
    defect route follows; the route moves run.json, so the file holds the invocations since the last one)."""
    out = []
    for inv in (run_record or {}).get("invocations") or []:
        if inv.get("subcommand") not in subcommands:
            continue
        outcome = str(inv.get("outcome", ""))
        why = [w for w, bad in (("crash", outcome.startswith("crash")), ("audit defect", outcome.startswith("defect")),
                                ("mismatch", outcome.startswith("mismatch")),
                                ("opened outside the allowlist", bool(inv.get("outside_allowlist"))),
                                ("an open refused by the audit", bool(inv.get("refused_by_audit")))) if bad]
        if why:
            out.append(f"run.json invocation {inv.get('k')} ({inv.get('subcommand')}): {', '.join(why)}; only the "
                       "defect route follows it (PLAN.md 5.6)")
    return out


def logged_paths(root, rel_folder):
    """Every path under `rel_folder` that a commit reachable from any ref has touched (`git log --all`,
    merges with -m), relative to the folder (amendment C6): validate_epa's run-once rule and calibrate_epa's
    refusal to refit after a held-out run read it, one definition."""
    prefix = rel_folder.rstrip("/") + "/"
    out = _git_ok(root, "log", "--all", "-m", "--no-renames", "--name-only", "--pretty=format:", "--", prefix)
    return sorted({line[len(prefix):] for line in out.splitlines() if line.startswith(prefix)})


# THE RUN-ONCE MARKERS (WP3's second fix of 23 October 2026, on the isolation review's finding that every
# record of a started or finished held-out run was an untracked file of the work tree, which `git clean
# -fd`, `git stash -u` or a deletion removes, after which a second run computed every held-out statistic
# again): validate_epa.py run writes, in the work tree's own git directory beside the arming's nonce, where
# no clean, stash or checkout reaches, epa_started_<id>_<ARMED.json blob> before its first held-out read and
# epa_ended_<id>_<blob> (the sha_text of every output it wrote) after run.json, and never removes either.
# The names are defined here, once, for validate_epa.py (which writes and reads them) and held_out_started
# (mistake 10).
# "writing" (WP3's fourth fix of 24 October 2026, on the fourth isolation review's finding): written before the run
# writes its first output, so that a run killed after an output holding held-out statistics was written -- the
# folder then cut back to STARTED alone -- does not compute them again on the normal route.
RUN_MARKER_KINDS = ("started", "writing", "ended")


def git_dirs(*, root):
    """The work tree's git directory and its common directory, absolute (one path when they are the same):
    where the run-once markers and the arming's nonce live."""
    out = []
    for flag in ("--git-dir", "--git-common-dir"):
        d = os.path.normcase(os.path.abspath(_git_ok(root, "rev-parse", "--path-format=absolute", flag).strip()))
        if d not in out:
            out.append(d)
    return out


def run_marker_path(kind, name, blob, *, root):
    """The run-once marker of `kind` ("started" or "ended") of the arming whose ARMED.json blob is `blob`,
    in the work tree's own git directory (git rev-parse --git-dir)."""
    if kind not in RUN_MARKER_KINDS:
        raise ValueError(f"run_marker_path: kind {kind!r} is not one of {RUN_MARKER_KINDS}")
    if not (isinstance(blob, str) and re.fullmatch(r"[0-9a-f]{40,64}", blob)):
        raise ValueError(f"run_marker_path: {blob!r} is not a git blob id")
    return os.path.join(git_dirs(root=root)[0], f"epa_{kind}_{name}_{blob}")


def run_markers(name, *, root):
    """Every run-once marker of `name` in the work tree's git directories, by file name, sorted: listing a
    folder opens no file, so calibrate_epa.py's audit has nothing to refuse."""
    out = set()
    for d in git_dirs(root=root):
        if os.path.isdir(d):
            out |= {f for f in os.listdir(d) for k in RUN_MARKER_KINDS if f.startswith(f"epa_{k}_{name}_")}
    return sorted(out)


def held_out_started(name, *, root, validation_rel):
    """Why the held-out run of `name` has started, as a list (empty when it has not): its folder
    validation_rel/<name>/ holds anything but ARMED.json on the disk, `git log --all` holds any path
    under it but ARMED.json, or the work tree's git directory holds a run-once marker of it (run_markers;
    WP3's second fix of 23 October 2026: a cleaned work tree keeps them). The contract, section 7: "No
    refit after any held-out statistic of an engine has been computed"; validate_epa.py run writes STARTED
    and its marker before its first held-out read (C6). Listing a folder and asking git open no file
    (WP3's fix of 23 October 2026)."""
    folder = f"{validation_rel.rstrip('/')}/{name}"
    path = os.path.join(_root(root), *folder.split("/"))
    out = []
    on_disk = []
    for dp, _dirs, files in os.walk(path):
        on_disk += [os.path.relpath(os.path.join(dp, f), path).replace(os.sep, "/") for f in files]
    extra = sorted(f for f in on_disk if f != "ARMED.json")
    if extra:
        out.append(f"{folder} holds {', '.join(extra)}: the held-out run has started")
    logged = sorted(f for f in logged_paths(root, folder) if f != "ARMED.json")
    if logged:
        out.append(f"git log --all holds {', '.join(logged)} under {folder}: the held-out run has started")
    markers = run_markers(name, root=root)
    if markers:
        out.append(f"the work tree's git directory holds {', '.join(markers)}: the held-out run has started")
    return out


def code_shas(*, root):
    """{path: sha_text} over CODE_HASHED in `root` (PLAN.md 5.8 "code"; amendment C10). A missing
    file is refused: a record of the code that ran cannot leave a module out."""
    root = _root(root)
    missing = [p for p in CODE_HASHED if not os.path.isfile(os.path.join(root, *p.split("/")))]
    if missing:
        raise FileNotFoundError(f"the step-2 code is incomplete in {root}: {missing}")
    return {p: common.sha_text(os.path.join(root, *p.split("/"))) for p in CODE_HASHED}


def code_changes(recorded, *, root):
    """The paths of CODE_HASHED whose sha_text in `root` differs from `recorded` ({path: sha_text},
    a fit_A.json or freeze.json record), or which one side lacks, sorted: what validate_epa.py arm
    must list with its defects.json entry (amendment C10)."""
    now = code_shas(root=root)
    return tuple(sorted(p for p in set(now) | set(recorded) if now.get(p) != recorded.get(p)))


def git_head(*, root):
    """The commit HEAD names in `root`, 40 hex digits."""
    return _git_ok(root, "rev-parse", "--verify", "HEAD").strip()


def git_clean(paths, *, root):
    """(clean, dirty): whether `paths` (repository-relative) are committed and unmodified in `root`,
    and the dirty ones -- modified, staged, deleted or untracked -- sorted. Read from `git status
    --porcelain -z`, which quotes nothing and keeps a path's first character (fingerprint._git's
    mistake of 22 October 2026), with --no-renames, so a renamed file is listed as its deleted old
    path and its added new one, both dirty, and every entry is one "XY path" field."""
    if not paths:
        return True, ()
    out = _git_ok(root, "status", "--porcelain=v1", "-z", "--no-renames", "--untracked-files=all", "--", *paths)
    dirty = {e[3:] for e in out.split("\0") if e}
    return not dirty, tuple(sorted(dirty))


def git_blob(path, *, root):
    """The git blob id of `path` in `root`'s index, from `git ls-files -s`, without opening the file
    (amendment C3: epa_channels.csv holds all-row ranges and is never opened). Refused if the file
    is not tracked, or if `git ls-files --modified --deleted` lists it (the working file is not the
    blob, so the id would not describe it)."""
    rel = _rel(path, root)
    lines = _git_ok(root, "ls-files", "-s", "--", rel).splitlines()     # "<mode> <blob> <stage>\t<path>"
    fields = lines[0].partition("\t")[0].split() if len(lines) == 1 else []
    if len(fields) != 3 or lines[0].partition("\t")[2] != rel:
        raise GitError(f"{rel} is not tracked in {root}, so it has no blob id")
    if _git_ok(root, "ls-files", "--modified", "--deleted", "--", rel).strip():
        raise GitError(f"{rel} differs from its blob in {root}: commit or restore it first")
    return fields[1]


def head_blob(path, *, root):
    """The blob id `path` has in HEAD's tree in `root`, or None. Asked through `git cat-file
    --batch-check` on stdin, so no argv names the path: calibrate_epa.py's audit hook refuses a git
    argv naming data/engines/ other than ls-files and hash-object (amendment C3), and the derived
    file lives there."""
    rel = _rel(path, root)
    out = _git_ok(root, "cat-file", "--batch-check", stdin=f"HEAD:{rel}\n").split()
    return out[0] if len(out) == 3 and out[1] == "blob" else None


def committed_at_head(path, *, root):
    """Whether `path` is in HEAD's tree in `root` and the working file is that blob: `git
    hash-object` applies the path's filters (core.autocrlf), so a CRLF checkout of an LF blob
    counts as committed, and one changed byte does not."""
    blob = head_blob(path, root=root)
    if blob is None or not os.path.isfile(_abs(path, root)):
        return False
    return _git_ok(root, "hash-object", "--", _rel(path, root)).strip() == blob


def blob_sha256(commit, path, *, root):
    """sha256 of the blob `path` (repository-relative) has at `commit` in `root`, as `git cat-file
    blob` gives it: no filter, so the LF blob. A working file equals it when its sha_text does
    (WP3_INTERFACES.md section 4; test_contract_pinned.py compares the contract this way)."""
    data = _git_ok(root, "cat-file", "blob", f"{commit}:{path}", binary=True)
    return hashlib.sha256(data).hexdigest()


def is_ancestor(older, newer, *, root):
    """Whether commit `older` is an ancestor of (or is) `newer` in `root` (git merge-base
    --is-ancestor: exit 0 yes, 1 no, anything else a failure)."""
    out = _git(root, "merge-base", "--is-ancestor", older, newer)
    if out.returncode not in (0, 1):
        raise GitError(f"git merge-base --is-ancestor {older} {newer} in {root}: {out.stderr.strip()}")
    return out.returncode == 0


def _commit_of(sha, root):
    """`sha` if it names a commit object in `root`, as 40 hex digits; refused otherwise."""
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise GitError(f"a fix commit is named by its full 40-digit sha, not {sha!r}")
    if _git(root, "cat-file", "-t", sha).stdout.strip() != "commit":
        raise GitError(f"{sha} is not a commit in {root}")
    return sha


# ------------------------------------------------------------------ the plant's files
def _epa_meta(name):
    """The top-level keys of the engine spec of the EPA plant `name`. Only an engine of the "epa"
    derived set has a derived file this module writes: the B58's is derive_params.py's, from the
    car's logs, and is refused here (mistake 1: no engine by default, and none by accident)."""
    if not isinstance(name, str) or name not in engines.PLANTS:
        raise KeyError(f"no plant {name!r}; known: {engines.known()}. There is no default engine "
                       "(CLAUDE.md mistake 1)")
    meta = engines.read_spec(engines.PLANTS[name][0])["_meta"]
    if meta.get("derived_set") != "epa":
        raise DerivedPathMismatch(f"{name}'s derived file is not an EPA calibration's (its derived_set is "
                                  f"{meta.get('derived_set')!r}): epa_freeze writes only those")
    return meta


def derived_relpath(name):
    """The derived file of the EPA plant `name`, repository-relative: the engine spec's `derived`
    key, asserted equal to derived.engine_path(name) (WP3_INTERFACES.md 5.4), so the file this
    module writes is the one engines._build reads and derived.py's message names."""
    meta = _epa_meta(name)
    want = os.path.relpath(derived.engine_path(name), derived.HERE).replace(os.sep, "/")
    if meta["derived"] != want:
        raise DerivedPathMismatch(f"engine_specs/{engines.PLANTS[name][0]}.toml names the derived file "
                                  f"{meta['derived']!r}, and derived.engine_path gives {want!r}: the "
                                  "calibration would write one file and the plant read another")
    return want


def derived_path(name, *, root):
    """The derived file of the EPA plant `name` inside the work tree `root` (derived_relpath)."""
    return os.path.join(_root(root), *derived_relpath(name).split("/"))


def freeze_relpath(name):
    """The freeze record of the EPA plant `name`, repository-relative: the engine spec's `freeze`
    key, asserted equal to results/EPA_CALIBRATION/<id>/freeze.json (WP3_INTERFACES.md section 6),
    the record engines._check_freeze reads."""
    meta = _epa_meta(name)
    want = f"{CALIBRATION_DIR}/{name}/freeze.json"
    if meta.get("freeze") != want:
        raise DerivedPathMismatch(f"engine_specs/{engines.PLANTS[name][0]}.toml names the freeze record "
                                  f"{meta.get('freeze')!r}, not {want!r}")
    return want


def freeze_path(name, *, root):
    return os.path.join(_root(root), *freeze_relpath(name).split("/"))


def calibration_dir(name, *, root):
    """results/EPA_CALIBRATION/<id>/ inside `root`, the folder of the freeze record."""
    return os.path.dirname(freeze_path(name, root=root))


def spec_labels(name):
    """{section: {field: label}} of the EPA plant `name`'s engine spec, engine_specs/<spec>.toml
    (engines.PLANTS[name][0]; engines.read_spec drops the labels): calibrate_epa.py's E6 row 9 reads which
    cycle constants are ASSUMED off them (WP3's second fix of 23 October 2026), and calibrate_epa.py opens
    no file itself (WP3_INTERFACES.md 3.2, N8)."""
    import tomllib
    path = os.path.join(engines.SPECS, engines.PLANTS[name][0] + ".toml")
    with open(path, "rb") as fh:
        raw = tomllib.load(fh)
    return {sec: {f: e.get("label") for f, e in val.items() if isinstance(e, dict)}
            for sec, val in raw.items() if isinstance(val, dict)}


def plant_files(name):
    """The repository-relative files plant_sha hashes (fingerprint.plant_files: PLANT_CODE, then the
    plant's own specs), as a tuple: what calibrate_epa.py requires committed and clean (WP3's third fix of
    24 October 2026)."""
    return tuple(fingerprint.plant_files(name))


def plant_sha(name):
    """fingerprint._sha_files(fingerprint.plant_files(name)): the plant's code and specs as the
    fingerprint hashes them (PLAN.md 5.8 "plant"), computable for a registered plant before its
    calibration. It is the running code's, never the validation's guard (WP3_INTERFACES.md 4, RF-3)."""
    return fingerprint._sha_files(fingerprint.plant_files(name))


# ------------------------------------------------------------------ the derived file
def _check_python_typed(values, who):
    """Amendment B10, by engines' own check (engines._plain, build_candidate's): every value a dict
    of str keys, a list, or a Python float, int or str. A NumPy scalar is refused, never converted:
    json.dumps writes a numpy.float64 as a float without a word, so after a write it could no
    longer be seen."""
    try:
        engines._plain(values, "")
    except TypeError as e:
        raise TypeError(f"{who}: {e}") from None


def _check_sections(values, who):
    """The derived values' layout (PLAN.md 5.8; WP3_INTERFACES.md 7.3): every frozen section, any
    completion section, the two bookkeeping keys, nothing else; each section exactly its fields,
    each field its type, every number finite. A NaN in a frozen section would also be refused by
    engines.frozen_sections_sha256 (allow_nan=False); one in a completion section by
    write_json_atomic; this names the field first."""
    _check_python_typed(values, who)
    if not isinstance(values, dict):
        raise TypeError(f"{who}: the derived values are a dict shaped like the file, not {type(values).__name__}")
    allowed = set(engines.FROZEN_SECTIONS) | set(COMPLETION_SECTIONS) | set(BOOKKEEPING_KEYS)
    extra = sorted(set(values) - allowed)
    missing = [s for s in engines.FROZEN_SECTIONS if s not in values]
    if extra or missing:
        raise ValueError(f"{who}: the derived values have sections {sorted(values)}; every frozen section "
                         f"{list(engines.FROZEN_SECTIONS)} is required, the completion sections "
                         f"{list(COMPLETION_SECTIONS)} and {list(BOOKKEEPING_KEYS)} are allowed, nothing else"
                         + (f" (unknown: {extra})" if extra else "") + (f" (missing: {missing})" if missing else ""))

    def finite(x, where):
        if type(x) is float and not math.isfinite(x):
            raise ValueError(f"{who}: {where} is {x!r}; a derived value is finite")

    for sec in [s for s in values if s in SECTION_KEYS]:
        v = values[sec]
        if sec == "deliverable_torque":
            if type(v) not in (list, tuple) or not all(type(p) in (list, tuple) and len(p) == 2
                                                       and type(p[0]) is int and type(p[1]) is float for p in v):
                raise TypeError(f"{who}: deliverable_torque is a list of [rpm (int), Nm (float)] pairs")
            for i, p in enumerate(v):
                finite(p[1], f"deliverable_torque[{i}]")
            continue
        if not isinstance(v, dict) or set(v) != SECTION_KEYS[sec]:
            got = sorted(v) if isinstance(v, dict) else type(v).__name__
            raise ValueError(f"{who}: section {sec} must hold exactly {sorted(SECTION_KEYS[sec])} "
                             f"(engines.EPA_DERIVED_FIELDS), and holds {got}")
        for key, x in v.items():
            where = f"{sec}.{key}"
            if (sec, key) in _STR_FIELDS:
                ok = type(x) is str
            elif (sec, key) in _INT_FIELDS:
                ok = type(x) is int
            elif (sec, key) in _LIST_FIELDS:
                ok = type(x) in (list, tuple) and all(type(e) is float for e in x)
                for i, e in enumerate(x if ok else ()):
                    finite(e, f"{where}[{i}]")
            else:
                ok = type(x) is float
                if ok:
                    finite(x, where)
            if not ok:
                raise TypeError(f"{who}: {where} is {x!r} ({type(x).__name__}), not the type its converter "
                                "takes (engines.CONVERT_BY_SET; a float field takes a Python float, amendment B10)")
    if "_about" in values and type(values["_about"]) is not str:
        raise TypeError(f"{who}: _about is a str")
    if "_inputs" in values:
        inp = values["_inputs"]
        if not isinstance(inp, dict) or set(inp) != set(INPUTS_KEYS) or not all(type(x) is str for x in inp.values()):
            raise ValueError(f"{who}: _inputs holds exactly {list(INPUTS_KEYS)}, each a str")


def _sections_json(values, names):
    """The named sections of `values` as the file will hold them: a JSON round trip, which makes
    every tuple a list and changes no number (json writes a float as its repr)."""
    return json.loads(json.dumps({s: values[s] for s in names if s in values}, allow_nan=False))


def derived_values(fit, *, provenance):
    """The derived file's dict at the freeze (WP3_INTERFACES.md 7.3): `_about`, `_inputs` (the
    contract commit, the freeze record's path, the calibration view's and the manifest's sha256,
    from `provenance`, the block of 7.1) and the three frozen sections of `fit` (an epa_fit.FormFit:
    its engine, form, values and frozen_sections_sha256), checked by _check_sections. The
    completion sections are added after the freeze by with_completion."""
    name = fit.engine
    vals = fit.values
    _check_python_typed(vals, "derived_values")
    if not isinstance(vals, dict) or sorted(vals) != sorted(engines.FROZEN_SECTIONS):
        raise ValueError(f"derived_values: a fit's values are exactly the frozen sections "
                         f"{list(engines.FROZEN_SECTIONS)}")
    _check_sections(vals, "derived_values")
    if provenance.get("engine") != name:
        raise ValueError(f"derived_values: the provenance is {provenance.get('engine')!r}'s, the fit {name!r}'s")
    if vals["cycle"]["form"] != fit.form:
        raise ValueError(f"derived_values: the fit's form is {fit.form!r} and its cycle section says "
                         f"{vals['cycle']['form']!r}")
    sha = engines.frozen_sections_sha256(vals)
    if fit.frozen_sections_sha256 != sha:
        raise FrozenSectionsChanged("derived_values: the fit's frozen_sections_sha256 is not "
                                    "engines.frozen_sections_sha256 of its values")
    out = {"_about": (f"The derived constants of {name}, written by calibrate_epa.py through "
                      "epa_freeze.write_derived (build step 2 of decision 24): the frozen sections cycle, "
                      f"ecu and boost_ceiling at the freeze of form {fit.form}, the completion sections "
                      "deliverable_torque, k3 and loop after it, from no EPA data. Never edited by hand "
                      "(CLAUDE.md); the freeze record named in _inputs hashes the frozen sections."),
           "_inputs": {"contract_commit": provenance["contract"]["commit"],
                       "freeze_record": freeze_relpath(name),
                       "view_sha256": provenance["view_sha256"],
                       "manifest_sha256": provenance["data"]["manifest_sha256"]}}
    out.update(_sections_json(vals, engines.FROZEN_SECTIONS))
    _check_sections(out, "derived_values")
    return out


def with_completion(values, *, deliverable_torque, turb_knee_k, torque_floor_nm):
    """`values` (the derived file's dict) with its three completion sections (PLAN.md 5.9; amendment
    F7): the deliverable-torque table as [rpm, Nm] pairs, K3's knee and the torque floor. The frozen
    sections are copied unchanged, and the result checked by _check_sections."""
    out = json.loads(json.dumps(values, allow_nan=False))
    _check_python_typed({"deliverable_torque": deliverable_torque, "k3": turb_knee_k, "loop": torque_floor_nm},
                        "with_completion")
    out["deliverable_torque"] = [list(p) for p in deliverable_torque]
    out["k3"] = {"turb_knee_k": turb_knee_k}
    out["loop"] = {"torque_floor_nm": torque_floor_nm}
    _check_sections(out, "with_completion")
    if engines.frozen_sections_sha256(out) != engines.frozen_sections_sha256(values):
        raise FrozenSectionsChanged("with_completion moved a frozen section")
    return out


def derived_record(path, *, root):
    """The derived file's record (WP3_INTERFACES.md section 4): its path relative to `root`, its
    sha_text and fingerprint.derived_sha (its values, top-level "_" keys dropped)."""
    full = _abs(path, root)
    sha = fingerprint.derived_sha(full)
    if sha is None:
        raise FileNotFoundError(f"{path}: no derived file to record (or not JSON)")
    return DerivedRecord(path=_rel(full, root), sha_text=common.sha_text(full), derived_sha=sha)


def _check_defect(defect, root):
    """The defect route's authority (PLAN.md 5.6): None, or a DefectRoute whose reason is stated and
    whose fix commit exists and is an ancestor of HEAD. A bare True names no fix and is refused."""
    if defect is None:
        return None
    if not isinstance(defect, DefectRoute):
        raise TypeError(f"allow_defect is None or an epa_freeze.DefectRoute naming its fix commit, not {defect!r}")
    if not isinstance(defect.reason, str) or not defect.reason.strip():
        raise ValueError("the defect route states the assertion that failed (DefectRoute.reason)")
    fix = _commit_of(defect.fix_commit, root)
    if not is_ancestor(fix, "HEAD", root=root):
        raise GitError(f"the fix commit {fix} is not an ancestor of HEAD in {root}: the calibration re-runs "
                       "from S0 on the committed fix")
    return defect


def check_defect(defect, *, root):
    """_check_defect, public: the defect route's authority checked before anything moves (calibrate_epa.py
    fit --defect and check --defect; WP3's integration, 23 October 2026)."""
    return _check_defect(defect, root)


def file_sha_text(path, *, root):
    """thresholds.common.sha_text of a file inside the work tree `root` (WP3_INTERFACES.md 4: every
    results/ output is hashed by its sha_text), for calibrate_epa.py, which imports no thresholds module
    (WP3_INTERFACES.md 3.1): complete.json's e6_files."""
    _rel(path, root)
    return common.sha_text(_abs(path, root))


def write_derived(name, values, *, allow_defect, root):
    """Write the derived file of the EPA plant `name` in `root`, and return its DerivedRecord: the
    only writer of data/engines/<id>/derived_params.json (CLAUDE.md: never by hand; PLAN.md 5.8).

    Refused, and nothing written: a layout or a type that is not the file's (_check_sections; a
    NumPy value among them, amendment B10); a spec whose derived path is not derived.engine_path's;
    and a frozen section that differs from the file already on disk or from freeze.json's hash --
    unless `allow_defect` is a DefectRoute whose fix commit is committed and an ancestor of HEAD
    (PLAN.md 5.6). Even then a freeze.json that is still in place refuses it: the defect route
    first moves the old run's outputs to defect_<k>/ (WP3_INTERFACES.md 5.5.2). A rewrite that
    keeps the frozen sections -- the completion's -- needs no defect route. `allow_defect` and
    `root` are required: no call may lean on a default for either."""
    path = derived_path(name, root=root)
    _check_sections(values, "write_derived")
    missing = [k for k in BOOKKEEPING_KEYS if k not in values]
    if missing:
        raise ValueError(f"write_derived: the derived file carries its bookkeeping {list(BOOKKEEPING_KEYS)} "
                         f"(derived_values makes them), and {missing} are missing")
    if values["_inputs"]["freeze_record"] != freeze_relpath(name):
        raise ValueError(f"write_derived: _inputs.freeze_record is {values['_inputs']['freeze_record']!r}, "
                         f"not {freeze_relpath(name)!r}")
    defect = _check_defect(allow_defect, root)
    new = engines.frozen_sections_sha256(values)
    fz = freeze_path(name, root=root)
    if os.path.exists(fz):
        held = _read_json(fz).get("frozen_sections_sha256")
        if held != new:
            raise FrozenSectionsChanged(
                f"write_derived: {_rel(fz, root)} froze sections hashing to {held}, and these hash to {new}"
                + (": a defect re-run first moves the old run's outputs, freeze.json among them, to "
                   "defect_<k>/" if defect else ": a frozen constant cannot change after the freeze "
                   "(the defect route names its fix commit)"))
    if os.path.exists(path) and defect is None:
        held = engines.frozen_sections_sha256(_read_json(path))
        if held != new:
            raise FrozenSectionsChanged(f"write_derived: {_rel(path, root)} holds frozen sections hashing to "
                                        f"{held}, and these hash to {new}: only the defect route, naming its "
                                        "fix commit, rewrites them (PLAN.md 5.6)")
    write_json_atomic(path, values)
    _forget_cached(path)
    return derived_record(path, root=root)


def _forget_cached(path):
    """Drop `path` from derived.py's per-process cache. derived._load reads a file once per process
    and keeps it; a process that rewrites the file (the completion) and then builds or checks the
    plant from it would otherwise read the old values without a word (mistake 25: an output that
    does not move after its input changed). The cache is a dict; nothing in derived.py is edited."""
    derived._CACHE.pop(os.path.normcase(os.path.abspath(path)), None)


# ------------------------------------------------------------------ the freeze record
def freeze_record(name, *, fit, ladder, files, provenance, root):
    """freeze.json's dict (PLAN.md 5.8; WP3_INTERFACES.md 7.2), the keys engines._check_freeze reads
    at the top level. `fit` is the chosen epa_fit.FormFit, `ladder` the epa_fit.Ladder it was
    chosen from, `files` {basename: path} of the fit's outputs in results/EPA_CALIBRATION/<id>/
    (stage0.json, in_sample.json and fit_<form>.json for every form fitted), `provenance` the run's
    block (7.1), `root` the work tree.

    Refused: a fit that is not the ladder's choice, or another engine's; a fit whose stored hash is
    not engines.frozen_sections_sha256 of its values (computed here, never copied: mistake 10); a
    derived file on disk whose frozen sections are not the fit's (write_derived comes first); a
    file list that is not the ladder's; code, plant or HEAD that changed since the provenance was
    taken; and step-2 code that was not committed and clean, since a freeze must be reproducible
    from its git_head (amendment C10)."""
    if fit.engine != name or provenance.get("engine") != name:
        raise ValueError(f"freeze_record({name!r}): the fit is {fit.engine!r}'s, the provenance "
                         f"{provenance.get('engine')!r}'s")
    if ladder.chosen != fit.form or fit not in tuple(ladder.fits):
        raise ValueError(f"freeze_record: the ladder chose {ladder.chosen!r}, and the fit given is form {fit.form!r}")
    if provenance["git"]["step2_clean"] is not True:
        raise FreezeRefusal(f"freeze_record: the step-2 code was not committed and clean when the fit "
                            f"started ({provenance['git']['dirty']}); a freeze is reproducible from its "
                            "git_head only from committed code")
    sha = engines.frozen_sections_sha256(fit.values)
    if fit.frozen_sections_sha256 != sha:
        raise FrozenSectionsChanged("freeze_record: the fit's stored frozen_sections_sha256 is not "
                                    "engines.frozen_sections_sha256 of its values")
    dpath = derived_path(name, root=root)
    if not os.path.exists(dpath):
        raise FileNotFoundError(f"freeze_record: no derived file {_rel(dpath, root)}; write_derived comes first")
    if engines.frozen_sections_sha256(_read_json(dpath)) != sha:
        raise FrozenSectionsChanged(f"freeze_record: {_rel(dpath, root)}'s frozen sections are not the fit's")
    want = {"stage0.json", "in_sample.json"} | {f"fit_{f.form}.json" for f in ladder.fits}
    if set(files) != want:
        raise ValueError(f"freeze_record: the fit's outputs are {sorted(want)}, and {sorted(files)} were given")
    folder = os.path.normcase(calibration_dir(name, root=root))
    for base, p in files.items():
        if os.path.basename(p) != base or os.path.normcase(os.path.dirname(os.path.abspath(p))) != folder:
            raise ValueError(f"freeze_record: {base} must be {_rel(os.path.join(folder, base), root)}, not {p}")
    code = code_shas(root=root)
    if code != provenance["code_sha_text"]:
        raise FreezeRefusal(f"freeze_record: the step-2 code changed during the fit: "
                            f"{code_changes(provenance['code_sha_text'], root=root)}")
    psha = plant_sha(name)
    if psha != provenance["plant_sha"]:
        raise FreezeRefusal("freeze_record: the plant's code or specs changed during the fit (plant_sha moved)")
    head = git_head(root=root)
    if head != provenance["git"]["head"]:
        raise FreezeRefusal(f"freeze_record: HEAD moved during the fit ({provenance['git']['head']} -> {head})")
    c = provenance["contract"]
    return {"schema": FREEZE_SCHEMA,
            "form": fit.form,
            "frozen_sections_sha256": sha,
            "derived": derived_record(dpath, root=root).as_json(),
            "contract": {"commit": c["commit"], "json_sha_text": c["json_sha_text"], "md_sha_text": c["md_sha_text"]},
            "data": provenance["data"],
            "code": code,
            "plant": {"plant_sha": psha},
            "fits": {b: common.sha_text(files[b]) for b in sorted(files)},
            "versions": provenance["versions"],
            "git_head": head,
            "flags": list(fit.flags),
            "all_row_depth_edge": {"active": ALL_ROW_DEPTH_FLAG in fit.flags, "flag": ALL_ROW_DEPTH_FLAG,
                                   "why": "S3b's depth bound is min(C1's, 1 - lam_floor); lam_floor is an all-row "
                                          "quantity, which can be the tighter edge only within the printed rounding "
                                          "of the calibration Final minimum; when active it is named in the C13 "
                                          "disclosure of the results"}}


def write_freeze(name, record, *, root):
    """Write freeze.json (WP3_INTERFACES.md 7.2) and return its sha_text. Refused if it exists: a
    re-freeze is the defect route, which moves the old run to defect_<k>/ first (PLAN.md 5.6).
    Refused, too, if the record does not describe the derived file on disk -- its frozen hash or
    its derived record -- or is not freeze_record's layout."""
    path = freeze_path(name, root=root)
    if os.path.exists(path):
        raise AlreadyFrozen(f"write_freeze: {_rel(path, root)} exists. A second freeze is the defect route: "
                            "move the run's outputs to defect_<k>/ and re-run from S0 (PLAN.md 5.6)")
    if not isinstance(record, dict) or sorted(record) != sorted(FREEZE_KEYS) or record["schema"] != FREEZE_SCHEMA:
        raise ValueError(f"write_freeze: a freeze record holds exactly {list(FREEZE_KEYS)} (schema {FREEZE_SCHEMA})")
    dpath = derived_path(name, root=root)
    if engines.frozen_sections_sha256(_read_json(dpath)) != record["frozen_sections_sha256"]:
        raise FrozenSectionsChanged(f"write_freeze: the record's frozen_sections_sha256 is not "
                                    f"{_rel(dpath, root)}'s")
    if derived_record(dpath, root=root).as_json() != record["derived"]:
        raise FrozenSectionsChanged(f"write_freeze: the record's derived file is not {_rel(dpath, root)} as it is now")
    return write_json_atomic(path, record)


def check_frozen(name, values, *, root):
    """Refuse `values` unless engines.frozen_sections_sha256(values) is the hash freeze.json holds
    (PLAN.md 5.9 item 10: the completion asserts its frozen sections unchanged). No freeze record is
    a FileNotFoundError: nothing is frozen to compare with."""
    path = freeze_path(name, root=root)
    if not os.path.exists(path):
        raise FileNotFoundError(f"check_frozen: no freeze record {_rel(path, root)}")
    held = _read_json(path).get("frozen_sections_sha256")
    got = engines.frozen_sections_sha256(values)
    if got != held:
        raise FrozenSectionsChanged(f"check_frozen: the frozen sections hash to {got}, and "
                                    f"{_rel(path, root)} holds {held}: a frozen constant changed after the freeze")


def check_derived_file(name, *, root):
    """engines' own check of the files in `root` (engines._check_freeze, the one engines._build runs
    before it builds an EPA plant from its file; amendment F7), with derived.py's cached copy of the
    file dropped first (_forget_cached), so the file is read as it is now."""
    dpath = derived_path(name, root=root)
    _forget_cached(dpath)
    engines._check_freeze(engines.PLANTS[name][0], dpath, freeze_path(name, root=root))


def tree_record(name, *, root):
    """The tree-side hashes ARMED.json records and the held-out token's check compares
    (WP3_INTERFACES.md 7.4; amendments C5, C10), in one definition for validate_epa.arm and
    verify_for_validation (mistake 10): freeze.json's and complete.json's path and sha_text (None
    for a file that does not exist), the derived file's DerivedRecord, the plant's spec files'
    sha_text, and the step-2 code's. The commits each file was made on, and the token itself, are
    validate_epa.py's (amendment C3)."""
    def text(rel):
        p = os.path.join(_root(root), *rel.split("/"))
        return {"path": rel, "sha_text": common.sha_text(p) if os.path.isfile(p) else None}

    folder = f"{CALIBRATION_DIR}/{name}"
    dpath = derived_path(name, root=root)
    specs = {}
    for rel in engines.spec_files(name):
        p = os.path.join(_root(root), *rel.split("/"))
        specs[rel] = common.sha_text(p) if os.path.isfile(p) else None
    return {"freeze": text(freeze_relpath(name)),
            "complete": text(f"{folder}/complete.json"),
            "derived": derived_record(dpath, root=root).as_json() if os.path.isfile(dpath) else None,
            "specs": specs,
            "code": code_shas(root=root)}


# ------------------------------------------------------------------ provenance
def versions():
    """The interpreter and libraries a run used (PLAN.md 5.8 "versions"; CLAUDE.md's rule 4)."""
    import scipy
    return {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
            "platform": platform.platform()}


def table_shas(name, *, source):
    """Every table's raw sha256 in the source's tables folder, after epa_rows.check_tables (a poison run's
    scratch copies included, whose guard compares their calibration records with the repository's):
    calibrate_epa.py poison shows that the copies it reads are not the tables (WP3's fix of 23 October
    2026: a poison that loaded the real tables would compare them with themselves)."""
    import epa_rows
    specs = epa_rows.check_tables(name, source=source)
    return {s.name: common.sha_raw(epa_rows.table_path(s, source=source)) for s in specs}


def data_shas(name, *, source):
    """The data block (WP3_INTERFACES.md 7.1): every table's raw sha256, after epa_rows.check_tables
    has compared them with the contract's (guard 3, so a table that is not the contract's stops
    before anything is recorded); epa_engine.json's raw sha256; epa_channels.csv's git blob id,
    never opened (git_blob); and the manifest's sha256 (epa_rows.manifest, from raw strings and keys
    alone). `source` is the epa_rows.Source the run reads; its tables lie inside its root."""
    import epa_rows
    specs = epa_rows.check_tables(name, source=source)
    tables = {s.name: common.sha_raw(epa_rows.table_path(s, source=source)) for s in specs}
    return {"tables_sha256": {k: tables[k] for k in sorted(tables)},
            "epa_engine_sha256": common.sha_raw(epa_rows.engine_file_path(name, "epa_engine.json", source=source)),
            "epa_channels_blob": git_blob(epa_rows.engine_file_path(name, "epa_channels.csv", source=source),
                                          root=source.root),
            "manifest_sha256": epa_rows.manifest(name, source=source).sha256}


def provenance(name, *, source, view):
    """The provenance block of every output of calibrate_epa.py and validate_epa.py
    (WP3_INTERFACES.md 7.1): the engine; the contract as epa_rows.check_contract verified it (its
    commit, both files' sha_text, its schema; guards 1 and 2 run here); HEAD and whether the step-2
    code is committed and clean, with the dirty paths; the code's sha_text (amendment C10: in
    fit_A.json this is the record of the code at the first fit); plant_sha; the data block; the
    calibration view's sha256 (`view`, an epa_rows.CalibrationView of this engine); the versions.
    No wall-clock time (WP3_INTERFACES.md 2.5)."""
    import epa_rows
    if view.engine != name:
        raise ValueError(f"provenance({name!r}): the calibration view is {view.engine!r}'s")
    cc = epa_rows.check_contract(source=source)
    clean, dirty = git_clean(CODE_HASHED, root=source.root)
    return {"engine": name,
            "contract": {"commit": cc.commit, "json_sha_text": cc.json_sha_text, "md_sha_text": cc.md_sha_text,
                         "schema": cc.schema},
            "git": {"head": git_head(root=source.root), "step2_clean": clean, "dirty": list(dirty)},
            "code_sha_text": code_shas(root=source.root),
            "plant_sha": plant_sha(name),
            "data": data_shas(name, source=source),
            "view_sha256": view.sha256,
            "versions": versions()}


# ------------------------------------------------------------------ the frozen-plant dump
# THE DUMP'S GRID (PLAN.md 5.8; WP3_INTERFACES.md 5.4), DESIGN: synthetic inputs, the same for every
# engine, none of them an EPA row. The cycle's: DUMP_N_RPM speeds spread evenly over the car's
# [rpm_min, rpm_max] (the calibration lines' ends on an EPA car, amendment C13); the MAPs below; the
# sparks; lambda at max(DUMP_LAM_FLOOR_CAP, the engine's lam_floor) and the two in DUMP_LAM; two
# intake temperatures; one coolant temperature; the engine's own fuel and the ECU's cam.
DUMP_N_RPM = 9
DUMP_MAP_KPA = (30.0, 60.0, 100.0, 140.0, 180.0, 220.0)
DUMP_SPARK_BTDC = (-5.0, 5.0, 15.0, 25.0)
DUMP_LAM_FLOOR_CAP = 0.70
DUMP_LAM = (0.85, 1.0)
DUMP_IMT_K = (310.0, 330.0)
DUMP_ECT_K = 365.0
# The ECU's, the back-pressure's and the boost's: finer grids, since each is a cheap closed form.
DUMP_ECU_MAP_KPA = tuple(float(m) for m in range(20, 301, 10))
DUMP_DWELL_S = (0.0, 3.0, 30.0)
DUMP_IAT_K = tuple(float(k) for k in range(270, 401, 5))
DUMP_FLOW_GPS = tuple(float(g) for g in range(0, 401, 10))
DUMP_T_INLET_K = (298.0, 315.0)
DUMP_T_AMB_K = (288.15, 298.15, 315.0, 323.15)
DUMP_T_BLOCK_K = (None, 340.0, 365.0, 380.0)
DUMP_V_MPS = (5.0, 15.0, 25.0, 130.0 / 3.6)
DUMP_ACCEL = (-0.5, 0.0, 0.5)
DUMP_GRADE = (-0.03, 0.0, 0.06, 0.12)
DUMP_RHO = (1.12, 1.2)
# THE THERMAL SEQUENCE (WP3_INTERFACES.md 5.4, chosen there: the certificate harness's own sequence
# lives in an archive no code may import). 600 steps of 1 s from the warm start at the scenario's
# ambient: 300 at a hot, loaded point, then 300 at a light one, so the network both heats and
# cools. Fixed inputs, DESIGN; no EPA or logged value.
DUMP_THERMAL_DT = 1.0
DUMP_THERMAL = ((300, {"mdot_fuel_gps": 10.0, "mdot_exh_gps": 150.0, "egt_k": 1150.0, "vehicle_mps": 36.0,
                       "fan_duty": 1.0, "rpm": 4000.0}),
                (300, {"mdot_fuel_gps": 2.0, "mdot_exh_gps": 30.0, "egt_k": 800.0, "vehicle_mps": 15.0,
                       "fan_duty": 0.0, "rpm": 1500.0}))


def _dump_map_grid(plant):
    """DUMP_MAP_KPA clipped to the calibration range as the plant itself records it. Its top: the
    highest MAP the boost envelope reaches, inlet_sea_kpa x min(max(envelope_pr), pr_cap) -- S3c
    builds the envelope from each calibration line's highest-MAP Final row (amendment D1), so that
    is the calibration's highest Final MAP. Its bottom is not clipped: no field of a plant records
    the calibration's lowest MAP, and 30 kPa is the grid's own floor (WP3_INTERFACES.md 5.4 left the
    source of "the calibration range" open; this reads it from the plant, so the dump stays a
    function of the plant alone)."""
    b = plant.engine.boost
    if not b.envelope_pr:
        raise ValueError("frozen_plant_dump: the plant has no boost envelope (a frozen plant has one)")
    top = b.inlet_sea_kpa * min(max(b.envelope_pr), b.pr_cap)
    return tuple(sorted({float(min(m, top)) for m in DUMP_MAP_KPA}))


def _dump_arrays(plant):
    """[(key, float64 array)] in the dump's fixed key order: the inputs' grids first, so a grid
    that moves with the plant (its speeds, its MAP clip, its lambda floor) moves the hash even where
    an output would not."""
    e, car, sc = plant.engine, plant.car, plant.scenario
    ecu = engine_env.BaselineECU(e.ecu)
    rpms = [float(x) for x in np.linspace(car.rpm_min, car.rpm_max, DUMP_N_RPM)]
    maps = _dump_map_grid(plant)
    lams = tuple(sorted({max(DUMP_LAM_FLOOR_CAP, e.ecu.lam_floor), *DUMP_LAM}))
    out = [("grid.rpm", rpms), ("grid.map_kpa", maps), ("grid.lam", lams)]

    fields = [f.name for f in dataclasses.fields(plant_model.CycleResult)]
    cyc = {f: [] for f in fields}
    for rpm in rpms:
        for m in maps:
            cam = ecu.cam_deg(rpm, m)
            p_exh = plant_model.exhaust_backpressure_kpa(m, engine=e)
            for spark in DUMP_SPARK_BTDC:
                for lam in lams:
                    for imt in DUMP_IMT_K:
                        op = plant_model.Operating(rpm, m, imt, DUMP_ECT_K, spark, lam, p_exh)
                        r = plant_model.run_cycle(op, engine=e, dtheta=plant_model.DTHETA_DEG, cam_deg=cam)
                        for f in fields:
                            cyc[f].append(getattr(r, f))
    out += [(f"run_cycle.{f}", cyc[f]) for f in fields]

    out.append(("exhaust_backpressure_kpa",
                [plant_model.exhaust_backpressure_kpa(m, engine=e) for m in DUMP_ECU_MAP_KPA]))
    grid = [(r, m) for r in rpms for m in DUMP_ECU_MAP_KPA]
    out.append(("ecu.base_spark", [ecu.base_spark(r, m) for r, m in grid]))
    out.append(("ecu.knock_limited_spark", [ecu.knock_limited_spark(r, m) for r, m in grid]))
    for dwell in DUMP_DWELL_S:
        out.append((f"ecu.base_lambda.dwell_{dwell:g}", [ecu.base_lambda(r, m, dwell) for r, m in grid]))
    out.append(("ecu.iat_compensation", [ecu.iat_compensation(k) for k in DUMP_IAT_K]))
    if e.ecu.cam_on:
        out.append(("ecu.cam_deg", [ecu.cam_deg(r, m) for r, m in grid]))

    out.append(("boost_ceiling_kpa", [plant_model.boost_ceiling_kpa(g, t, e.boost.inlet_sea_kpa, engine=e)
                                      for t in DUMP_T_INLET_K for g in DUMP_FLOW_GPS]))
    out.append(("charge_temperature", [plant_model.charge_temperature(t, b, engine=e)
                                       for t in DUMP_T_AMB_K for b in DUMP_T_BLOCK_K]))

    veh = engine_env.vehicle_for(plant.car)
    if hasattr(veh, "road_force_n"):          # the three-term road load (EPA's cars); the Supra has none
        out.append(("vehicle.road_force_n", [veh.road_force_n(v, g, rho=rho) for v in DUMP_V_MPS
                                             for g in DUMP_GRADE for rho in DUMP_RHO]))
    tq, rp = [], []
    for v in DUMP_V_MPS:
        for a in DUMP_ACCEL:
            for g in DUMP_GRADE:
                for rho in DUMP_RHO:
                    t, r = veh.demand(v, a, g, rho=rho)
                    tq.append(t)
                    rp.append(r)
    out += [("vehicle.demand.torque_nm", tq), ("vehicle.demand.rpm", rp)]

    net = thermal.ThermalNetwork(e.thermal, t_amb=sc.t_amb)
    states = [net.reset(t_amb=sc.t_amb, warm=True)]
    for n, inp in DUMP_THERMAL:
        for _ in range(n):
            states.append(net.step(DUMP_THERMAL_DT, inp["mdot_fuel_gps"], inp["mdot_exh_gps"], inp["egt_k"],
                                   sc.t_amb, inp["vehicle_mps"], inp["fan_duty"], rpm=inp["rpm"]))
    out.append(("thermal.state", np.concatenate([np.asarray(s, dtype=np.float64) for s in states])))
    return [(k, np.asarray(v, dtype=np.float64)) for k, v in out]


def frozen_plant_dump(plant):
    """The frozen-plant dump of `plant` (PLAN.md 5.8; WP3_INTERFACES.md 5.4): run_cycle's sixteen
    CycleResult fields over the dump's grid, the back-pressure law, the baseline ECU's base and
    knock-limited spark, its lambda at dwell 0, 3 and 30 s, its intake-temperature compensation and
    (form D) its cam on an (rpm, MAP) grid, the boost ceiling on a flow grid, the charge
    temperature, the car's road force (a three-term car) and demand on a (speed, acceleration,
    grade, air density) grid, and the thermal network along DUMP_THERMAL. Every array is taken as
    little-endian float64 and their bytes are hashed in key order.

    SYNTHETIC INPUTS ONLY: no EPA row and no logged state is an input, so the dump can be re-made on
    any machine from the plant alone (validate_epa.py arm re-makes it and compares it bit for bit;
    decision 61: again on the training device). `plant` is required (mistake 1)."""
    h = hashlib.sha256()
    keys, n = [], 0
    for key, arr in _dump_arrays(plant):
        h.update(np.ascontiguousarray(arr, dtype="<f8").tobytes())
        keys.append(key)
        n += int(arr.size)
    return Dump(sha256=h.hexdigest(), n_values=n, keys=tuple(keys))


if __name__ == "__main__":
    sys.exit("epa_freeze.py has no command line: calibrate_epa.py and validate_epa.py call it "
             "(build step 2, WP3_INTERFACES.md 5.4); its test is test_epa_freeze.py")

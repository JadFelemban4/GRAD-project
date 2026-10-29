"""calibrate_epa.py -- Run 1 of build step 2: each EPA engine calibrated on its calibration rows, its
cycle form chosen by the in-sample stage and frozen, its E6 refit variants fitted, its plant completed.

    python -B calibrate_epa.py dry-load --engine <id> --out <scratch>
    python -B calibrate_epa.py t0       --engine <id> --jobs <n> [--defect "<reason>" --fix-commit <sha>]
    python -B calibrate_epa.py fit      --engine <id> --jobs <n> [--defect "<reason>" --fix-commit <sha>]
    python -B calibrate_epa.py poison   --engine <id> --jobs <n> --scratch <dir> [--full]
    python -B calibrate_epa.py e6       --engine <id> --jobs <n>
    python -B calibrate_epa.py complete --engine <id> --jobs <n>
    python -B calibrate_epa.py check    --engine <id> --jobs <n> [--defect "<reason>" --fix-commit <sha>]

    --engine and --jobs are required: there is no default engine or job count (mistake 1).
    OMP_NUM_THREADS=1 and MKL_NUM_THREADS=1 must be set before the command (PLAN.md 5.1).
    Exit codes: 0 ok, 1 crash, 2 refused, 3 an audit defect, 4 Run 1 waits, 5 check's mismatch.

Build step 2 of decision 24, WP3, written 23 October 2026 BEFORE ANY FIT (the contract JSON's
order_of_work[1]: "calibrate each engine on its calibration rows (calibrate_epa.py, committed before it
runs), the in-sample stage included; freeze"). Its interfaces are docs/build_step_2/WP3_INTERFACES.md
section 5.5; its authorities results/ENGINE_THRESHOLDS.md and .json version 5 (c842d74), docs/build_step_2/
AMENDMENTS.md (C3, C6, C8, C10, C11, C13, E1-E3, F3, F5, F7, F8), HANDOFFS.md and PLAN.md sections 5-5.10.
It composes the other step-2 modules: the rows come from epa_rows, every stage from epa_fit, every statistic
from epa_stats, every record, hash, file and record check from epa_freeze, the K3 knee, the neutral run and
the completion's measurements from k3_knee, the engine's own coefficients from epa_coefficients. Its own
arithmetic is the completion's E6 bookkeeping -- the slider-crank inversion and valve brackets, the probe
sizes, the sigmas read from the fit, the model in use under a refit variant -- each tested by hand
(test_calibrate_epa.Pieces). It opens no file itself (rule N8): its records go through epa_freeze.

RUN 1 WAITS (the contract's open_for_the_team). Version 4's first entry held that "The first fit (Run 1)
waits for both: Jad's column, and Ghassan's own answer" (results/ENGINE_THRESHOLDS.md section 13, "What is
open"); version 5's records Ghassan's order of 23 October 2026 that Run 1 go ahead before Jad's column is
filled (section 14; the JSON's version_5.go_ahead). While the committed contract holds a Run 1 rule
(epa_rows.run1_wait, which fails closed: the commit epa_rows pins always holds it, and so does any entry of
open_for_the_team that names Run 1, as version 5's entries 0 and 3 do), the FIRST evaluation at an EPA row's
inputs waits -- dry-load, and t0 or fit while STARTED is absent -- printing that it waits and exiting with
EXIT_WAIT, having read no EPA table and written nothing (not even run.json, since the contract's claims that
no fit has run are read off what a fit leaves behind), unless the environment variable EPA_RUN1_GO names the
engine (EPA_RUN1_GO=<id>, or a comma-separated list), which whoever starts Run 1 sets, on the team's order.
Nothing in WP3 sets it. Every later subcommand (poison, e6, complete, check, and t0 or fit once STARTED
exists) builds on a run that started, so the gate does not hold it; the rule's text and the switch are
recorded in STARTED and in every run.json entry (WP3's fix of 23 October 2026, on the test review's finding
that a gated check made the arming read "repeat Run 1").

RUN 1'S ORDER AND ITS PROOFS (WP3's fix of 23 October 2026): t0, fit, poison, e6, complete, check. fit
requires t0.json passed (amendment A1; PLAN.md 5.10); e6 and complete require poison.json, C8's proof,
complete and equal (with the full form-A poison fit on epa_freeze.FULL_POISON_ENGINE); poison, e6, complete
and check refuse while run.json holds an invocation the audit judged a defect, a crash or a mismatch, which
only the defect route follows (PLAN.md 5.6); t0, fit, poison, e6 and complete refuse once the held-out run
has started (the contract, section 7: "No refit after any held-out statistic"). t0 and fit also refuse
while a u_D term a gating row reads or any engine's D3 summary column is not
pinned (epa_stats.unpinned_u_d, d3_rows.unpinned_for): pinned after the first fit, either would be a code
change only the defect route admits (amendment C10), and either would stop the one-shot held-out run. t0 and
fit require the plant's code and specs committed and clean; poison, e6 and complete the step-2 code and the
plant committed, clean and freeze.json's (WP3's third fix of 24 October 2026).

THE RUNTIME AUDIT (amendment C3; WP3_INTERFACES.md 3.3, 5.5.4). On the command line the audit hook is
installed before the first project import, for every subcommand, and every spawn worker of epa_fit's
ordered pool installs the same hook (worker_init): a parent's hook does not see a worker. It records every
open, normalised to the repository (or <python>/, <scratch>/), refuses at once an open of logs/, of any
engine's epa_channels.csv, of another engine's folder, of results/EPA_VALIDATION/, of any generator output
but ecu/k3_nominal.json and of the team's data folder -- and, in a worker always and in poison while its
poisoned stages run, of the engine's own tables and epa_engine.json -- and refuses a subprocess whose argv
names the tables' folder or logs/epa/ unless it is `git ls-files` or `git hash-object`, or that reads object
contents (git show, cat-file, log -p, diff, grep, blame, archive) of a path outside the allowlist, or of a
path it refuses to open at that moment. While sealed it refuses every child process but subprocess's git in
one of SEALED_GIT_SHAPES, word for word, in the work tree, with no environment of its own (WP3's fourth fix of
24 October 2026, on the fourth isolation review's planted forms), and epa_fit's pool spawning workers with
worker_init, a change of the process's environment, and a sealed file under another spelling (WP3's third fix
of 24 October 2026, on the third isolation review's planted leaks); sealed or not, a git -c other than
core.safecrlf=false, and a link made while the audit is active. At the
end of each invocation the opened set (the workers' merged in task order) is written to run.json and
compared with the subcommand's allowlist; a path outside it is a coding defect (PLAN.md 5.6) and the exit
is non-zero. The allowlist holds the B58's derived file, which the project's import chain reads (derived.py,
through engines; WP3's fix of 23 October 2026: on the command line every subcommand was a defect).

THE RECORDS (WP3_INTERFACES.md 6, 7.2). results/EPA_CALIBRATION/<id>/: STARTED, written atomically before
the first model evaluation at an EPA row's inputs by t0 or fit, whichever runs first, never rewritten (a
crashed fit leaves it); stage0.json, fit_<form>.json per form fitted, in_sample.json and freeze.json by
fit; t0.json; poison.json; e6/row{1,2,3,7_090,7_110}.json; complete.json; run.json, one entry per
invocation, refused ones included (a Run 1 wait excepted, above); defects.json and defect_<k>/ on the
defect route. The derived file, data/engines/<id>/ (epa_freeze.derived_relpath), is written by fit (its
frozen sections) and complete (its completion sections), through epa_freeze.write_derived alone.

THE ORDER (PLAN.md WP4): t0, fit, poison, e6, complete, check. Each subcommand refuses when its
predecessor's record is missing, or when its own record exists (a re-run is the defect route: t0 --defect
and fit --defect move the run's outputs to defect_<k>/ and re-run from T0, fit --defect then on through
S0 and the ladder; check --defect writes in_sample_rerun<k>.json, amendment C11).

WHAT IT PRINTS: counts, stage and form names, flags and paths, never a fitted constant or a statistic
(WP3_INTERFACES.md 2.4); a crash prints its exception's type and where it was raised, never its message,
which may carry a value. Numbers live in the JSON records.
"""
import argparse
import contextlib
import dataclasses
import datetime
import fnmatch
import math
import os
import shlex
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))

SUBCOMMANDS = ("dry-load", "t0", "fit", "poison", "e6", "complete", "check")
# The environment switch that lets Run 1 go while the contract still says it waits (module docstring): it
# names the engine (EPA_RUN1_GO=<id>, or a comma-separated list), so one setting starts one engine's run.
RUN1_GO = "EPA_RUN1_GO"
# The exit codes, each its own case (validate_epa.CHECK_EXITS reads them by name): a mismatch of check is
# not a refusal (WP3's fix of 23 October 2026).
EXIT_OK, EXIT_CRASH, EXIT_REFUSED, EXIT_DEFECT, EXIT_WAIT, EXIT_MISMATCH = 0, 1, 2, 3, 4, 5
# The subcommands whose first evaluation at an EPA row's inputs the Run 1 gate holds (module docstring).
GATED_ALWAYS, GATED_UNTIL_STARTED = ("dry-load",), ("t0", "fit")
# git subcommands that print an object's contents, refused unless every path they name is on the allowlist
# (a `git cat-file -p <sha>` names no folder, so the argv rule alone would pass it; WP3's fix of 23 October
# 2026). cat-file's -t, -s, -e and --batch-check print no content. The unsealed rule (the loader's phase,
# whose code the scans confine): diff prints no content only with --quiet (WP3's fourth fix of 24 October 2026,
# on the fourth isolation review's finding that --exit-code never suppresses a patch, and --name-only,
# --name-status, --stat and --numstat do not beside -p or --patch); log and whatchanged print one with any of
# GIT_PATCH_FLAGS, -U<n> and -L<...> among them.
GIT_CONTENT = ("show", "cat-file", "diff", "grep", "blame", "archive", "log", "whatchanged")
GIT_NO_CONTENT_FLAGS = {"cat-file": ("-t", "-s", "-e", "--batch-check"),
                        "diff": ("--quiet",),
                        "log": None, "whatchanged": None}
GIT_PATCH_FLAGS = ("-p", "-u", "--patch", "--patch-with-stat", "--patch-with-raw", "--binary", "--cc", "-c", "-W",
                   "--function-context", "--word-diff", "--color-words", "--unified", "-L", "--remerge-diff", "--dd")
# the same by prefix: -U<n>, --unified=<n>, -L<range>:<file>, and the pickaxe (-G<regex>, -S<string>), which
# prints no patch but selects commits by their contents, an oracle on a cell
GIT_PATCH_PREFIXES = ("-U", "--unified=", "-L", "--word-diff=", "--color-words=", "-G", "-S", "--pickaxe-regex")
# git's global options a git argv may carry (epa_rows._git passes `-C <root> -c core.safecrlf=false`), and the
# one configuration it may set: any other -c can start a child with no audit hook (core.fsmonitor=<cmd> under
# `git status`, diff.external=<cmd> under `git diff --ext-diff`; the fourth isolation review ran both), so every
# other -c, --config-env, --exec-path, --git-dir, --work-tree and the rest are refused, sealed or not (WP3's
# fourth fix of 24 October 2026).
GIT_CONFIG_ADMITTED = ("core.safecrlf=false",)
GIT_GLOBALS_WITH_VALUE = ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env", "--exec-path",
                          "--super-prefix", "--list-cmds", "--attr-source")
# THE SEAL OVER CHILD PROCESSES (WP3's third fix of 24 October 2026, on the third isolation review's planted
# leaks: a sealed stage read the contract through `git show HEAD:<contract>`, and a held-out table cell through
# a child interpreter, which has no audit hook; neither was refused and the poison still read all_equal). While
# the audit is sealed, a child process is refused unless it is git running one of SEALED_GIT_SHAPES, exactly --
# the argv shapes the step-2 code runs (epa_freeze._git, epa_rows._git), word for word, no other option, no
# pathspec magic, in the work tree, with no environment of its own (WP3's fourth fix of 24 October 2026, on the
# fourth isolation review's planted forms: `git diff --exit-code <empty tree> HEAD -- <contract>`, `git log -U0`,
# `--unified=0`, `--binary`, `-L a,b:<file>`, `--cc`, a `:(glob)` pathspec reaching a table, and `-c
# core.fsmonitor=<cmd> status` and `-c diff.external=<cmd> diff --ext-diff` starting a hookless child each
# passed the subcommand list SEALED_GIT was) -- or epa_fit's own ordered pool spawning a worker whose initializer
# is this module's worker_init (Audit._spawn_problem: the frame of epa_fit._pool, read off the stack, since the
# event carries no usable command line). The shapes whose word <rev>:<path> prints an object's contents (show,
# cat-file blob) are judged with the seal's own refusals: a path the seal refuses is refused through git too.
# os.system, os.exec*, os.spawn*, os.posix_spawn, os.startfile and a change of the process's environment
# (os.putenv, os.unsetenv: GIT_CONFIG_*, HOME or PATH would reach git) are refused while sealed. A shape's
# tokens: "<rev>" a revision word (no ':' and no option), "<rev>:<path>" a blob at a revision, "<path>" one
# repository-relative path, "<path>..." one or more; any other token is the literal word.
SEALED_GIT_SHAPES = (
    ("rev-parse", ("--path-format=absolute", "--git-dir")),
    ("rev-parse", ("--path-format=absolute", "--git-common-dir")),
    ("rev-parse", ("--verify", "<rev>")),
    ("rev-parse", ("<rev>",)),
    ("rev-parse", ("<rev>:<path>",)),
    ("status", ("--porcelain=v1", "-z", "--no-renames", "--untracked-files=all", "--", "<path>...")),
    ("ls-files", ("-s", "--", "<path>")),
    ("ls-files", ("--modified", "--deleted", "--", "<path>")),
    ("cat-file", ("--batch-check",)),
    ("cat-file", ("-t", "<rev>")),
    ("cat-file", ("blob", "<rev>:<path>")),
    ("hash-object", ("--", "<path>")),
    ("merge-base", ("--is-ancestor", "<rev>", "<rev>")),
    ("log", ("--all", "-m", "--no-renames", "--name-only", "--pretty=format:", "--", "<path>")),
    ("show", ("<rev>:<path>",)),
)
SEALED_GIT = tuple(dict.fromkeys(s for s, _ in SEALED_GIT_SHAPES))      # the subcommands, for the messages
# the shapes whose <rev>:<path> word prints the blob (rev-parse's prints its id only)
SEALED_GIT_CONTENT = ("cat-file", "show")
# The events a child process raises; _winapi.CreateProcess is judged by Audit._spawn_problem.
PROCESS_EVENTS = ("subprocess.Popen", "os.system", "os.exec", "os.spawn", "os.posix_spawn")
# The events that change the process's environment (a child inherits it), refused while sealed.
ENV_EVENTS = ("os.putenv", "os.unsetenv")
# The events that make another name for a file (a hard link, a symbolic link, a junction): refused while the
# audit is active, sealed or not, so that no file the audit refuses is reached under a path it allows (WP3's
# fourth fix of 24 October 2026, on the fourth isolation review's finding: such a link under the scratch folder
# would be recorded as <scratch>/..., which poison and dry-load allow). The step-2 code makes none.
LINK_EVENTS = ("os.link", "os.symlink", "_winapi.CreateJunction")
STARTFILE_EVENTS = ("os.startfile", "os.startfile/2")
# How a pool worker reports an open its audit refused (Audit.event, invoke): beside the paths it opened.
REFUSED_TAG = "<refused>/"
# How a pool worker reports a child process its audit refused, beside it (WP3's third fix of 24 October 2026).
REFUSED_PROCESS_TAG = REFUSED_TAG + "<process> "


# ======================================================================================================
# The audit (stdlib only: it is installed before the first project import on the command line)
# ======================================================================================================
def _strip_long(path):
    """A path without Windows' \\\\?\\ (or \\\\?\\UNC\\) prefix, which spells the same file under another string
    (WP3's third fix of 24 October 2026, on the isolation review's finding that the seal compared spellings)."""
    p = os.fsdecode(path)
    if p.startswith("\\\\?\\UNC\\"):
        return "\\\\" + p[len("\\\\?\\UNC\\"):]
    if p.startswith(("\\\\?\\", "\\\\.\\")) and len(p) > 6 and p[5] == ":":
        return p[4:]
    return p


def _norm_abs(path):
    return os.path.normcase(os.path.abspath(_strip_long(path)))


def _file_id(path):
    """(st_dev, st_ino) of an existing file, or None: the same file under any spelling (a hard link, an 8.3
    short name) has the same id. os.stat raises no audit event, so the hook may call it."""
    try:
        st = os.stat(path)
    except (OSError, ValueError, TypeError):
        return None
    return (st.st_dev, st.st_ino) if st.st_ino else None


def _slash(p):
    return p.replace("\\", "/")


def _under(path_nc, folder_nc):
    return path_nc == folder_nc or path_nc.startswith(folder_nc.rstrip(os.sep) + os.sep)


class Audit:
    """One invocation's runtime audit (WP3_INTERFACES.md 3.3): the subcommand, the engine, the work tree
    `root`, the scratch folder (dry-load's --out, poison's --scratch) and, once the project is imported,
    epa_rows.audit_paths (bind). It records every open and every subprocess while it is active, refuses
    what C3 lists, and decides each recorded path against the subcommand's allowlist (allowed)."""

    def __init__(self, *, subcommand, engine, root, scratch):
        self.subcommand, self.engine = subcommand, engine
        self.root = os.path.abspath(root)
        self.root_nc = _norm_abs(root)
        self.scratch_nc = _norm_abs(scratch) if scratch else None
        # The code's own tree, where engines.py reads the specs beside itself and the imported generator
        # modules live: the root on the command line (epa_rows.Source.repository()); a test's temporary root
        # differs from it, and its files are then tagged <code>/, where only code, caches and specs are
        # allowed (validate_epa's audit does the same)
        self.code_nc = None if _norm_abs(HERE) == self.root_nc else _norm_abs(HERE)
        self.py = sorted({_norm_abs(p) for p in (sys.base_prefix, sys.prefix, sys.exec_prefix)}, key=len,
                         reverse=True)
        self.opened, self.subprocesses, self.refused = set(), [], []
        self.paths = None
        self.own_ids, self.contract_ids = set(), set()      # the sealed files' (st_dev, st_ino), from bind
        self.always_ids = {}                                 # {(st_dev, st_ino): why} of the always-refused files
        self.on_open = None             # a worker's: epa_fit.WORKER_OPENED.append
        # THE SEAL (WP3's second fix of 23 October 2026, on the second isolation review's finding that a
        # stage could load the whole contract -- its held-out keys among them -- through the Source's
        # lower-case attribute and an unlisted helper, and that the contract was on every subcommand's
        # allowlist, workers included): while True, an open of the contract's two files, of the engine's own
        # tables or of its epa_engine.json is refused at once. True in every pool worker (worker_init: a
        # worker runs cycles on the rows it is handed and reads none of them), and in the parent through
        # every computing phase (sealed(): each subcommand loads the view, the yield, engine_facts and the
        # provenance first, then seals, so a stage, the in-sample stage, a refit, a measurement or the
        # recompute that reads any of them crashes, and refused_by_audit names it).
        self.sealed = False
        # The narrower refusal of the engine's own tables and epa_engine.json alone (the contract stays
        # readable): what a harness sets from the start of a command line whose gate it tests, so that a gate
        # that let the subcommand through would crash at its first table open instead of reading the table
        # and writing STARTED (test_calibrate_epa.Gate, the test review's finding of 23 October 2026)
        self.refuse_tables = False

    def bind(self, paths):
        """The repository-relative paths the rules name (epa_rows.audit_paths), as plain data; the B58's
        derived file (paths["b58_derived_abs"], derived.B58_PATH) recorded as norm records it."""
        self.paths = {k: (tuple(v) if isinstance(v, (list, tuple)) else v) for k, v in dict(paths).items()}
        if self.paths.get("b58_derived_abs"):
            self.paths["b58_derived"] = self.norm(self.paths["b58_derived_abs"])
        # the sealed files' identities, so that another spelling of one -- a hard link, an 8.3 short name, a
        # \\?\ prefix -- is refused at once, not only judged outside the allowlist at the end (WP3's third fix
        # of 24 October 2026, on the isolation review's finding)
        p = self.paths
        self.own_ids = {i for i in (_file_id(self._abs_nc(t)) for t in tuple(p.get("table_files", ()))
                                    + ((p["engine_json"],) if p.get("engine_json") else ())) if i}
        self.contract_ids = {i for i in (_file_id(self._abs_nc(c)) for c in p.get("contract", ())) if i}
        # and the identities of every file an open is always refused (WP3's fourth fix of 24 October 2026, on the
        # fourth isolation review's finding that those were judged by spelling alone): another engine's folder,
        # every epa_channels.csv, results/EPA_VALIDATION/, the generator's outputs but ecu/k3_nominal.json, and
        # logs/ -- so a hard link or a junction to one, under an allowed path, is refused at once. The team's
        # data folder is not walked (it is large); LINK_EVENTS refuses a link made while the audit is active.
        self.always_ids = {}
        own_nc = self._abs_nc(p["own"]) if p.get("own") else None
        k3_nc = self._abs_nc(p["k3"]) if p.get("k3") else None
        walks = ((p.get("engines"), "another engine's folder", own_nc),
                 (p.get("validation"), "results/EPA_VALIDATION/", None),
                 (p.get("outputs"), "a generator output other than ecu/k3_nominal.json", k3_nc),
                 ("logs", "logs/", None))
        for folder, why, keep in walks:
            if not folder:
                continue
            top = self._abs_nc(folder)
            for dp, _dirs, files in os.walk(top):
                for f in files:
                    fp = _norm_abs(os.path.join(dp, f))
                    if keep is not None and _under(fp, keep):
                        continue
                    i = _file_id(fp)
                    if i:
                        self.always_ids.setdefault(i, why)
        for c in p.get("channels", ()):
            i = _file_id(self._abs_nc(c))
            if i:
                self.always_ids[i] = "an epa_channels.csv (all-row ranges, plan 4.5)"

    def norm(self, path):
        """A path as run.json records it: <python>/... under the interpreter, <scratch>/... under the
        scratch folder, repository-relative with forward slashes under the root, else absolute."""
        a = os.path.abspath(_strip_long(path))
        nc = os.path.normcase(a)
        pres = [(p, "<python>/") for p in self.py] + [(self.scratch_nc, "<scratch>/"), (self.root_nc, ""),
                                                       (self.code_nc, "<code>/")]
        for pre, tag in sorted((x for x in pres if x[0]), key=lambda x: len(x[0]), reverse=True):
            if _under(nc, pre):
                return tag + _slash(a[len(pre):].lstrip("\\/"))
        return _slash(a)

    # ---------------------------------------------------------------------------- the rules
    def _abs_nc(self, rel):
        return _norm_abs(rel if os.path.isabs(rel) else os.path.join(self.root, *rel.split("/")))

    def forbidden(self, path):
        """Why an open of `path` is refused at once (C3), or None."""
        if self.paths is None:
            return None
        nc = _norm_abs(path)
        p = self.paths
        if _under(nc, self._abs_nc("logs")):
            return "logs/"
        if any(nc == self._abs_nc(c) for c in p["channels"]):
            return "an epa_channels.csv (all-row ranges, plan 4.5)"
        if _under(nc, self._abs_nc(p["engines"])) and not _under(nc, self._abs_nc(p["own"])):
            return "another engine's folder"
        if _under(nc, self._abs_nc(p["validation"])):
            return "results/EPA_VALIDATION/"
        if _under(nc, self._abs_nc(p["outputs"])) and nc != self._abs_nc(p["k3"]):
            return "a generator output other than ecu/k3_nominal.json"
        if _under(nc, _norm_abs(p["data_folder"])):
            return "the team's data folder"
        fid = _file_id(path) if (self.sealed or self.refuse_tables or self.always_ids) else None
        if fid is not None and fid in self.always_ids:
            return self.always_ids[fid] + " (under another name: the same file)"
        if self.sealed or self.refuse_tables:
            if (any(nc == self._abs_nc(t) for t in p["table_files"]) or nc == self._abs_nc(p["engine_json"])
                    or (fid is not None and fid in self.own_ids)):
                return ("the engine's own tables, read while the subcommand computes or in a pool worker (C3, C8: "
                        "every stage reads the yield it is given)")
        if self.sealed:
            if any(nc == self._abs_nc(c) for c in p["contract"]) or (fid is not None and fid in self.contract_ids):
                return ("the contract, read while the subcommand computes or in a pool worker (C4: every stage reads "
                        "the calibration view it is given)")
        return None

    def allowed(self, rec):
        """Whether a recorded path is on the subcommand's allowlist (WP3_INTERFACES.md 5.5.4). The B58's
        derived file is on every subcommand's: the project's import chain reads it (engines -> derived.py),
        read only, before the subcommand starts (WP3's fix of 23 October 2026)."""
        if rec.startswith("<python>/"):
            return True
        if rec.startswith("<scratch>/"):
            return self.subcommand in ("dry-load", "poison")
        if self.paths and rec == self.paths.get("b58_derived"):
            return True
        if rec.startswith("<code>/"):
            return self._is_code(rec[len("<code>/"):])
        low = rec.lower()
        if os.path.basename(low) in ("nul", os.devnull.lower()) or low == os.devnull.lower():
            return True
        if os.path.isabs(rec) or rec.startswith("/") or ":" in rec[:3]:
            return False
        if self._is_code(rec):
            return True
        p = self.paths or {}
        if rec in tuple(p.get("contract", ())) or rec == p.get("k3"):
            return True
        if rec in tuple(p.get("table_files", ())) or rec == p.get("engine_json"):
            return True
        if self.subcommand != "dry-load":
            if rec.startswith(f"results/EPA_CALIBRATION/{self.engine}/"):
                return True
            # the derived file, and the partial file epa_freeze.write_json_atomic moves over it
            if p.get("derived") and rec in (p["derived"], p["derived"] + epa_freeze_partial_suffix()):
                return True
        return False

    @staticmethod
    def _is_code(rec):
        """The repository's code, its caches and its specs (WP3_INTERFACES.md 5.5.4): *.py, __pycache__,
        engine_specs/*.toml and cars/*.toml, thresholds/* (the generator, hashed by guard 2)."""
        low = rec.lower()
        # requirements-lock.txt: the environment's pins, which every subcommand compares (epa_freeze.
        # version_problems; WP3's second fix of 23 October 2026), read only
        return (low.endswith(".py") or "__pycache__/" in low or low.startswith("__pycache__")
                or low == "requirements-lock.txt"
                or fnmatch.fnmatch(rec, "engine_specs/*.toml") or fnmatch.fnmatch(rec, "engine_specs/cars/*.toml")
                or fnmatch.fnmatch(rec, "thresholds/*"))

    # ---------------------------------------------------------------------------- the hook's body
    def _argv_problem(self, argv, *, event="subprocess.Popen", cwd=None, env=None, executable=None):
        """Why a subprocess's argv is refused (C3), or None: one naming the tables' folder or logs/epa/,
        unless it is `git ls-files` or `git hash-object`; a git argv with a global option or a -c that can start
        a child of its own (_git_parse; WP3's fourth fix of 24 October 2026); and a git command that prints an
        object's contents (GIT_CONTENT, less its no-content forms) unless every path it names -- a <rev>:<path>
        word, or a word after "--" -- is on the allowlist (WP3's fix of 23 October 2026: `git cat-file -p
        <sha>` names no folder). While sealed, only subprocess's git in one of SEALED_GIT_SHAPES, exactly, in
        the work tree and with no environment of its own (_sealed_problem)."""
        if self.paths is None:
            return None
        words = [argv] if isinstance(argv, (str, bytes)) else list(argv or ())
        text = _slash(" ".join(os.fsdecode(w) if isinstance(w, (bytes, os.PathLike)) else str(w) for w in words)).lower()
        bad = [x for x in (self.paths["engines"].lower().rstrip("/") + "/", "logs/epa/") if x in text]
        g = _git_parse(words)
        sub, rest = g["sub"], g["rest"]
        if g["git"] and g["problem"]:
            return g["problem"]
        if self.sealed:
            why = self._sealed_problem(event, g, cwd=cwd, env=env, executable=executable)
            if why is not None:
                return why
        if bad and sub not in ("ls-files", "hash-object"):
            return f"a subprocess naming {bad[0]}"
        if sub in GIT_CONTENT and _git_reads_content(sub, rest):
            paths = _git_paths(rest)
            if not paths or not all(self.allowed(p) for p in paths):
                return f"a git {sub} that reads object contents outside the allowlist"
            # the seal over git (WP3's third fix of 24 October 2026): a content read of a path the seal refuses
            # to open is refused too, the contract, the tables and epa_engine.json among them
            if any(self.forbidden(p if os.path.isabs(p) else os.path.join(self.root, *p.split("/"))) for p in paths):
                return f"a git {sub} that reads the contents of a path the audit refuses now"
        return None

    def _sealed_problem(self, event, g, *, cwd, env, executable):
        """Why a child is refused while the audit is sealed, or None (WP3's fourth fix of 24 October 2026, on the
        fourth isolation review's planted forms): a child has no audit hook, so only subprocess's git in one of
        SEALED_GIT_SHAPES, word for word, in the work tree (its cwd and every -C), with no executable and no
        environment of its own, is admitted."""
        if event != "subprocess.Popen":
            return f"{event} while the audit is sealed (a child has no audit hook; only subprocess's git is admitted)"
        if not g["git"]:
            return ("a child process other than git's " + ", ".join(SEALED_GIT) + " while the audit is sealed "
                    "(a child has no audit hook)")
        if executable is not None and os.path.splitext(os.path.basename(os.fsdecode(executable)))[0].lower() != "git":
            return "a git argv run by another executable while the audit is sealed"
        if env is not None:
            return "a git with an environment of its own while the audit is sealed (GIT_CONFIG_* can start a child)"
        if g["other_globals"]:
            return (f"a git global option {g['other_globals'][0]} while the audit is sealed (only -C <the work tree> "
                    f"and -c {', '.join(GIT_CONFIG_ADMITTED)})")
        where = os.path.abspath(os.fsdecode(cwd)) if cwd is not None else os.getcwd()
        for d in g["dirs"]:
            where = os.path.abspath(os.path.join(where, d))
        if _norm_abs(where) not in {self.root_nc, self.code_nc or self.root_nc}:
            return "a git run outside the work tree while the audit is sealed"
        if not _sealed_shape(g["sub"], g["rest"]):
            return ("a git argv other than the step-2 code's own (SEALED_GIT_SHAPES: "
                    + ", ".join(SEALED_GIT) + ") while the audit is sealed")
        return None

    def _spawn_problem(self):
        """Why a _winapi.CreateProcess (Windows' one process creation, whose audit event carries no usable
        command line) is refused now, or None: while sealed it must come from subprocess.Popen, whose own
        event this audit has already judged, or from epa_fit's ordered pool (epa_fit._pool) creating workers
        whose initializer is this module's worker_init, which installs this audit in them (WP3's third fix of
        24 October 2026: a pool a stage made itself, or one without the audit's initializer, is a child without
        a hook). Read off the calling frames."""
        if not self.sealed:
            return None
        ef = sys.modules.get("epa_fit")
        pool_code = getattr(getattr(ef, "_pool", None), "__code__", None)
        popen_code = getattr(getattr(sys.modules.get("subprocess"), "Popen", None), "_execute_child", None)
        popen_code = getattr(popen_code, "__code__", None)
        f = sys._getframe(1)
        while f is not None:
            if popen_code is not None and f.f_code is popen_code:
                return None
            if pool_code is not None and f.f_code is pool_code:
                init = f.f_locals.get("initializer")
                if isinstance(init, tuple) and init and init[0] is worker_init:
                    return None
                return "a pool worker spawned without the audit's initializer while the audit is sealed"
            f = f.f_back
        return "a child process created outside subprocess and epa_fit's ordered pool while the audit is sealed"

    def _refuse_process(self, shown, why):
        self.refused.append(shown)
        if self.on_open is not None:
            # a worker's refusal reaches the parent's record even when the code that made it caught the
            # PermissionError (WP3's third fix of 24 October 2026), as an open's does
            self.on_open(REFUSED_PROCESS_TAG + shown)
        raise PermissionError(f"calibrate_epa's audit refuses {why} (amendment C3)")

    def event(self, event, args):
        if event == "open":
            path = args[0] if args else None
            if not isinstance(path, (str, bytes, os.PathLike)):
                return
            rec = self.norm(path)
            self.opened.add(rec)
            if self.on_open is not None:
                self.on_open(rec)
            why = self.forbidden(os.fsdecode(path))
            if why is not None:
                self.refused.append(rec)
                if self.on_open is not None:
                    # a worker's refusal reaches the parent's record even when the code that opened caught the
                    # PermissionError (linecache does): tagged, so invoke counts it as refused, not opened
                    self.on_open(REFUSED_TAG + rec)
                raise PermissionError(f"calibrate_epa's audit refuses opening {rec}: {why} (amendment C3)")
        elif event in PROCESS_EVENTS:
            argv = {"subprocess.Popen": lambda: args[1], "os.system": lambda: args[0],
                    "os.exec": lambda: args[1], "os.spawn": lambda: args[2],
                    "os.posix_spawn": lambda: args[1]}[event]()
            shown = [os.fsdecode(a) if isinstance(a, (bytes, os.PathLike)) else str(a) for a in
                     ([argv] if isinstance(argv, (str, bytes)) else list(argv or ()))]
            self.subprocesses.append(shown)
            # subprocess.Popen's event carries (executable, args, cwd, env): the seal judges all four
            popen = event == "subprocess.Popen"
            why = self._argv_problem(argv, event=event, cwd=args[2] if popen and len(args) > 2 else None,
                                     env=args[3] if popen and len(args) > 3 else None,
                                     executable=args[0] if popen and args else None)
            if why is not None:
                self._refuse_process(" ".join(shown), why)
        elif event == "_winapi.CreateProcess":
            why = self._spawn_problem()
            if why is not None:
                app = args[0] if args else None
                self._refuse_process(f"CreateProcess {os.fsdecode(app) if isinstance(app, (str, bytes)) else app}", why)
        elif event in STARTFILE_EVENTS:
            if self.sealed:
                self._refuse_process(f"startfile {args[0] if args else ''}", "os.startfile while the audit is sealed")
        elif event in ENV_EVENTS:
            # a child inherits the process's environment: GIT_CONFIG_COUNT/KEY/VALUE, GIT_EXTERNAL_DIFF, HOME or
            # PATH set here would reach the next git (WP3's fourth fix of 24 October 2026)
            if self.sealed:
                key = args[0] if args else ""
                self._refuse_process(f"{event} {os.fsdecode(key) if isinstance(key, (str, bytes)) else key}",
                                     "a change of the process's environment while the audit is sealed")
        elif event in LINK_EVENTS:
            # another name for a file would carry a refused file under an allowed path (LINK_EVENTS)
            dst = args[1] if len(args) > 1 else ""
            self._refuse_process(f"{event} {os.fsdecode(dst) if isinstance(dst, (str, bytes, os.PathLike)) else dst}",
                                 "a link made while the audit is active (it would name a file under another path)")


def epa_freeze_partial_suffix():
    """epa_freeze.PARTIAL_SUFFIX, read when the audit decides (the audit's class is defined before the
    project is imported)."""
    return sys.modules["epa_freeze"].PARTIAL_SUFFIX if "epa_freeze" in sys.modules else ".partial"


def _git_subcommand(words):
    """The git subcommand of an argv (None if it is not git): the first word after git that is not an
    option, skipping the values of the global options that take one (GIT_GLOBALS_WITH_VALUE)."""
    return _git_args(words)[0]


def _git_args(words):
    """(the git subcommand, the words after it) of an argv; (None, []) if it is not git."""
    g = _git_parse(words)
    return g["sub"], g["rest"]


def _words(words):
    words = [os.fsdecode(w) if isinstance(w, (bytes, os.PathLike)) else str(w) for w in words]
    if len(words) == 1 and " " in words[0]:
        # Windows hands the audit event the command line (subprocess.list2cmdline), quoted where a word
        # holds a space; shlex in non-POSIX mode keeps such a word whole
        words = [w.strip('"') for w in shlex.split(words[0], posix=False)]
    return words


def _git_parse(words):
    """An argv read as git's: {"git": whether it is git, "sub": the subcommand (None if none), "rest": the
    words after it, "dirs": every -C value in order, "other_globals": every global option but -C and an
    admitted -c, "problem": why the argv is refused sealed or not, or None} (WP3's fourth fix of 24 October
    2026, on the fourth isolation review's finding that every -c was skipped unread: a -c other than
    GIT_CONFIG_ADMITTED, --config-env, --exec-path and a pager (-p, --paginate) can each start a child with
    no audit hook, and are refused whenever the audit is active)."""
    words = _words(words)
    out = {"git": False, "sub": None, "rest": [], "dirs": [], "other_globals": [], "problem": None}
    if not words or os.path.splitext(os.path.basename(words[0]))[0].lower() != "git":
        return out
    out["git"] = True
    i = 1
    while i < len(words):
        w = words[i]
        if w in GIT_GLOBALS_WITH_VALUE:
            val = words[i + 1] if i + 1 < len(words) else None
            if w == "-C" and val is not None:
                out["dirs"].append(val)
            elif w == "-c" and val in GIT_CONFIG_ADMITTED:
                pass
            else:
                out["other_globals"].append(w)
                if w in ("-c", "--config-env", "--exec-path") and out["problem"] is None:
                    out["problem"] = (f"a git {w} {val if w != '-c' else (val or '').split('=')[0]} (a configuration or "
                                      f"an exec path can start a child with no audit hook; only -c "
                                      f"{', '.join(GIT_CONFIG_ADMITTED)} is admitted)")
            i += 2
            continue
        if w.startswith("-"):
            out["other_globals"].append(w)
            if (w in ("-p", "--paginate") or w.startswith(("--config-env", "--exec-path", "-c"))) \
                    and out["problem"] is None:
                out["problem"] = f"a git {w.split('=')[0]} (it can start a child with no audit hook)"
            i += 1
            continue
        out["sub"], out["rest"] = w, words[i + 1:]
        return out
    return out


def _git_reads_content(sub, rest):
    """Whether a git command of GIT_CONTENT prints object contents: log and whatchanged with a patch flag
    (GIT_PATCH_FLAGS, GIT_PATCH_PREFIXES); cat-file and diff not in their no-content forms (diff only with
    --quiet); show, grep, blame and archive always."""
    if sub in ("log", "whatchanged"):
        return any(w in GIT_PATCH_FLAGS or w.startswith(GIT_PATCH_PREFIXES) for w in rest)
    flags = GIT_NO_CONTENT_FLAGS.get(sub)
    return not (flags and any(w in flags for w in rest))


# A revision word of a sealed git argv (a commit id, HEAD, HEAD~1): no ':' (a blob), no '..' (a range), no
# option, no '@{' (a reflog); a path word: repository-relative, no pathspec magic (':(glob)', ':!', ':/'), no
# glob character, no '..' segment, no drive or root (WP3's fourth fix of 24 October 2026, on the fourth isolation
# review's `:(glob)data/engine?/...`, which the folder rule's substring did not see).
_REV_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.~^/-")
_PATH_CHARS = (_REV_CHARS | set("+ ")) - set("~^")


def _is_rev(w):
    return (bool(w) and not w.startswith(("-", "/", ".")) and set(w) <= _REV_CHARS and ".." not in w)


def _is_path(w):
    return (bool(w) and not w.startswith(("-", "/", " ")) and set(w) <= _PATH_CHARS
            and ".." not in w.split("/") and not w.endswith(" "))


def _shape_word(token, w):
    if token == "<rev>":
        return _is_rev(w)
    if token == "<path>":
        return _is_path(w)
    if token == "<rev>:<path>":
        rev, sep, path = w.partition(":")
        return bool(sep) and _is_rev(rev) and _is_path(path)
    return w == token


def _sealed_shape(sub, rest):
    """Whether git `sub` with the words `rest` is one of SEALED_GIT_SHAPES, word for word."""
    for s, shape in SEALED_GIT_SHAPES:
        if s != sub:
            continue
        if shape and shape[-1] == "<path>...":
            head = shape[:-1]
            if (len(rest) > len(head) and all(_shape_word(t, w) for t, w in zip(head, rest))
                    and all(_is_path(w) for w in rest[len(head):])):
                return True
        elif len(rest) == len(shape) and all(_shape_word(t, w) for t, w in zip(shape, rest)):
            return True
    return False


def _git_paths(rest):
    """The repository paths a git command's words name: the path of each <rev>:<path> word, and each word
    after "--". A drive-letter path (C:\\ or C:/) is a path, not a <rev>:<path>."""
    out, after = [], False
    for w in rest:
        if w == "--":
            after = True
            continue
        if after:
            out.append(_slash(w))
        elif not w.startswith("-") and ":" in w and not (len(w) > 2 and w[1] == ":" and w[2] in "\\/"):
            out.append(_slash(w.split(":", 1)[1]))
    return out


_CURRENT = [None]          # the active Audit of this process, or None
_HOOKED = [False]


def _hook(event, args):
    a = _CURRENT[0]
    if a is None:
        return
    try:
        a.event(event, args)
    except PermissionError:
        raise
    except Exception:
        # an audit that cannot read an event must not stop what it watches -- unless it is sealed, where an event
        # it cannot judge is refused and recorded (WP3's fourth fix of 24 October 2026, on the fourth isolation
        # review's finding that the hook failed open: an argv or a path the audit could not parse was admitted)
        if a.sealed:
            a._refuse_process(f"<unreadable event> {event}", f"an {event} event the audit cannot read while sealed")


def install_audit(*, subcommand, engine, root, scratch):
    """The process's audit for one invocation (WP3_INTERFACES.md 5.5.3): sys.addaudithook(_hook) once per
    process (a hook cannot be removed), and this Audit made the active one. deactivate() ends it."""
    if not _HOOKED[0]:
        sys.addaudithook(_hook)
        _HOOKED[0] = True
    a = Audit(subcommand=subcommand, engine=engine, root=root, scratch=scratch)
    _CURRENT[0] = a
    return a


def deactivate():
    _CURRENT[0] = None


def seal_now():
    """Seal the active audit for the rest of the invocation (Audit.sealed; invoke's deactivate ends it):
    called by each subcommand once it has loaded the view, the yield, engine_facts and the provenance,
    before its first computation (WP3's second fix of 23 October 2026). Nothing when no audit is active (a
    test calling a subcommand bare)."""
    a = _CURRENT[0]
    if a is not None:
        a.sealed = True


@contextlib.contextmanager
def sealed():
    """The audit sealed for the block only, then as it was: T0 inside fit's defect route (fit loads after it)
    and poison's reference and poisoned stages."""
    a = _CURRENT[0]
    was = None if a is None else a.sealed
    if a is not None:
        a.sealed = True
    try:
        yield
    finally:
        if a is not None:
            a.sealed = was


def _prelude(argv):
    """The command line's first steps, before any project import (C3; PLAN.md 5.1; derived.py): one BLAS
    thread asserted, DERIVING_PARAMS=1 for complete (a fresh process), the audit installed."""
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        if os.environ.get(var) != "1":
            print(f"calibrate_epa.py: set {var}=1 before the command (PLAN.md 5.1: one BLAS thread, set before "
                  "NumPy is imported)", file=sys.stderr)
            raise SystemExit(EXIT_REFUSED)
    # NumPy here is scipy-openblas, which reads OPENBLAS_NUM_THREADS before OMP_NUM_THREADS: unset or 1 (WP3's
    # third fix of 24 October 2026, on the Run 1 review's finding; epa_fit.assert_one_blas_thread the same)
    if os.environ.get("OPENBLAS_NUM_THREADS", "1") != "1":
        print("calibrate_epa.py: OPENBLAS_NUM_THREADS must be unset or 1 (PLAN.md 5.1: one BLAS thread; OpenBLAS "
              "reads it before OMP_NUM_THREADS)", file=sys.stderr)
        raise SystemExit(EXIT_REFUSED)
    args = _parser().parse_args(argv)
    if args.subcommand == "complete":
        os.environ["DERIVING_PARAMS"] = "1"
    scratch = getattr(args, "out", None) or getattr(args, "scratch", None)
    install_audit(subcommand=args.subcommand, engine=args.engine, root=HERE, scratch=scratch)
    return args


def _parser():
    p = argparse.ArgumentParser(prog="calibrate_epa.py", description="Run 1 of build step 2 (see the docstring)")
    sub = p.add_subparsers(dest="subcommand", required=True)
    for name in SUBCOMMANDS:
        s = sub.add_parser(name)
        s.add_argument("--engine", required=True)
        if name == "dry-load":
            s.add_argument("--out", required=True)
        else:
            s.add_argument("--jobs", required=True, type=int)
        if name in ("t0", "fit", "check"):
            s.add_argument("--defect", default=None)
            s.add_argument("--fix-commit", dest="fix_commit", default=None)
        if name == "poison":
            s.add_argument("--scratch", required=True)
            s.add_argument("--full", action="store_true")
    return p


if __name__ == "__main__":
    _ARGS = _prelude(sys.argv[1:])

# ======================================================================================================
# The project (imported after the audit is installed, on the command line)
# ======================================================================================================
import numpy as np                                   # noqa: E402
from scipy.optimize import least_squares             # noqa: E402  E6 row 9's Atkinson fit (D-1)

import d3_rows                                       # noqa: E402  its pin check only (WP3_INTERFACES.md N11)
import derived                                       # noqa: E402  the B58's derived file's path, for the audit
import engines                                       # noqa: E402
import epa_coefficients                              # noqa: E402
import epa_fit                                       # noqa: E402
import epa_freeze                                    # noqa: E402
import epa_rows                                      # noqa: E402
import epa_stats                                     # noqa: E402
import k3_knee                                       # noqa: E402

DTHETA = epa_fit.DTHETA_DEG          # the plant's own crank step, every fit's (FATAL in the fingerprint)
STARTED = "STARTED"
RUN = "run.json"
STAGE0, IN_SAMPLE, FREEZE, T0, POISON, COMPLETE = (
    "stage0.json", "in_sample.json", "freeze.json", "t0.json", "poison.json", "complete.json")
# The refit variants (PLAN.md 5.7), by the file names validate_epa reads (E6_REFIT there).
E6_VARIANTS = ("1", "2", "3", "7_090", "7_110")


def fit_file(form):
    return f"fit_{form}.json"


def e6_file(variant):
    return f"e6/row{variant}.json"


# What was seen before the fit (amendment C13; HANDOFFS.md WP3 item 2, P7 item 3; WP3_INTERFACES.md 1.2
# and 5.5.3), written into stage0.json. Each entry names what was seen and where, and repeats no value.
SEEN_BEFORE_THE_FIT = (
    "WP1 P2's implementer, 22 October 2026: results/ENGINE_THRESHOLDS.md:789-797, the lambda clip paragraph, "
    "which prints each EPA engine's floor and its deepest EPA lambda over all rows, held-out rows included "
    "(HANDOFFS.md WP3 item 2); none used",
    "WP1 P7's implementer, 22 October 2026: printed results/ENGINE_THRESHOLDS.md:755 (E6 row 3, the tables' "
    "heating values), :789-797 (as above) and thresholds/contract.py:440-447 (E6 rows 1-3, each table's offset "
    "lambda_ref - 1) (HANDOFFS.md WP3 item 2, P7 item 3); none used",
    "the plan's authors: PLAN.md's turbine-inlet-pressure-against-barometer boolean and its all-row channel "
    "ranges (Cell 9's top speed, the cam ranges, the Honda's Final lambda minimum, the HD1 barometer), from "
    "epa_channels.csv's minima and maxima over every row (amendments C1, C13; wrong claims 11 and 16); no fit "
    "input is taken from them (amendment C1: every bound comes from the yield or a DESIGN constant)",
    "the amendments' authors: the contract's own all-row turbine-inlet-temperature ranges (the amendments' "
    "disclosure)",
    "the end lines rpm_min and rpm_max: cited to the contract JSON's lines, never held out (thresholds/split.py, "
    "amendment C13)",
    "WP3's interface author, 23 October 2026: the reads WP3_INTERFACES.md section 1.2 lists -- the contract's key "
    "paths and value types, its rule texts, version_4.plant_values, the first two points of ecu_strategy_b58 "
    "(B58 measurements), the keys (never the values) of engines.mazda_25t, its per_held_out_line and "
    "lambda_clip_floor, and of one held_out_rows record, results/ENGINE_THRESHOLDS/ecu/k3_nominal.json's keys "
    "and two B58 figures, and MANIFEST.csv's header and its anl-d3 rows' paths and byte counts; no EPA table",
) + tuple(epa_rows.SEEN) + (
    "WP3's D3 author, 23 October 2026: from the contract JSON c3_segments, perturbations_E6, the C rows of "
    "thresholds and conventions.populations, with no EPA value; no D3 file and no summary workbook",
) + tuple("WP3's D3 author, before the fit (d3_rows.SOURCES_READ): " + s for s in (
    # d3_rows.SOURCES_READ, verbatim: this module imports no d3_rows (WP3_INTERFACES.md 3.1, N11), and
    # test_calibrate_epa reads that literal through ast and checks each entry is here (mistake 10)
    "results/ENGINE_THRESHOLDS.md section 5 and appendix A (23 October 2026, d3_rows.py's channel pins)",
    "GRAD-engine-data/CATALOGUE.md:260-282, 283-405, 406-521, 591-628, 652-683 (the D3 format, tests, "
    "channels and problems; no D3 file and no summary workbook opened)",
    "GRAD-engine-data/anl-d3-documentation/aprf-dyno-testing-reference/ANL_APRF_DynoTestingReference_July2013.pdf "
    "(23 October 2026, through pdftotext into a scratch file: generic 2013 channel names, no summary header; "
    "the fuel's heating value 'at the top of the test summary result sheet')",
    "engine_specs/cars/cx9_2016_25t.toml [gear_ratios] (six forward gears, NH519 Table 4): the gear codes",
    # the D3 summary pins' reads, 24 October 2026 (decisions 78-81)
    "the D3 summary pins' author, 24 October 2026 (decision 78): the header row (row 7) of each summary workbook, "
    "GRAD-engine-data/anl-d3-2016-mazda-cx9/test-summary/2016_Mazda_CX9_Test_Summary_04052018.xlsx, sheet "
    "'Extended Test Summary', and "
    "anl-d3-2018-honda-accord-lx/test-summary/2018_Honda_Accord_Test_Summary_20191125.xlsx, sheet 'G2_TestSummary' "
    "(each file's sha256 MANIFEST.csv's), and the labelled cells above it, through a scratch script run with -I -B "
    "(the scratchpad's d3pin_scripts/summary_header.py) that printed only those strings; no row below the header, "
    "no result value",
    "the D3 summary pins' author, 24 October 2026 (decision 78 as amended): the identifier columns of every row "
    "below the header of both workbooks -- 'Test ID [#]', 'Cycle' and the Accord's 'Fuel Batch' -- through a "
    "scratch script that decoded no other column (d3pin3_scripts/summary_identifiers.py), and again through "
    "d3_rows.sum_row to check decision 80's row rule on them (d3pin5_scripts/summary_rows_check.py); no result "
    "value",
    "the D3 summary pins' author, 24 October 2026 (decision 81): GRAD-engine-data/_catalogue/d3_accord_columns.csv "
    "in full and d3_cx9_columns.csv by grep, the catalogue's derived lists of every column name, its unit as "
    "written in the name and its file count (CATALOGUE.md:54); names and counts only, no value",
    "the D3 summary pins' author, 24 October 2026 (decision 79): EPA NVFEL Fuel Analysis Reports 26781, 25206 and "
    "25402 (GRAD-engine-data/epa-ncat-benchmarking/<engine>_tier3-test-data/unzipped/6- ... .pdf), the Tier 3 test "
    "fuels of the three engines' Tier 3 packages, printed whole through pdftotext, with the embedded images of "
    "their scanned pages viewed (d3pin5_scripts/pdf_page_images.py); and the field alpha_fuel.density_kgpL_15C "
    "alone of each EPA engine's epa_engine.json (d3pin5_scripts/tier2_density.py); fuel properties, "
    "no row value",
    "the D3 summary pins' author, 24 October 2026: results/ENGINE_THRESHOLDS.md section 5 (rule text); "
    "GRAD-engine-data/CATALOGUE.md:1-120, 255-312, 404-430, 495-505 and 588-705 (the layout, the EPA packages and "
    "fuels, the D3 format and batches, parts of the CX-9's and the Accord's test tables, which print per-test cell "
    "temperatures and channel maxima of D3 files, as the catalogue lines above do, the channels and the problems); "
    "MANIFEST.csv's rows of the summaries, the column lists and the test files (paths and sha256); the earlier "
    "attempts' scratch outputs of decision 78's reads; no D3 trace file and no summary result value; none used "
    "beyond the pins",
)) + (
    "WP3's validation author, 23 October 2026: the contract's E6 row 11 shift, the d rows' probe, E6 row 10's "
    "driveline efficiency, section 5's radius gap, and each engine's epa_engine.json alpha_fuel heating value, "
    "printed once to check their parsers (contract constants and fuel properties, no row value)",
    "WP3's integrator, 23 October 2026: the contract JSON's open_for_the_team, order_of_work, status and the "
    "perturbations_E6 rows' text; the key names of engines.ford_27tt.fuel_by_table's records, of one "
    "per_held_out_line record and of engines.mazda_25t.pooled_counts; generators.sha256's and "
    "generator_inputs_sha256's key lists; results/ENGINE_THRESHOLDS.md:280-300 (the B58's climb cell), "
    ":870-960 (E6's rules) and :2340-2360 (what is open); no EPA row, no held-out value",
    "WP3's isolation reviewer, 23 October 2026: results/ENGINE_THRESHOLDS.md:980-1010 (the lambda clip "
    "paragraph, as P2's and P7's entries: each engine's floor and its deepest EPA lambda over all rows, "
    "held-out rows included) and the key names of the contract's engines, coverage, lambda_clip_floor, "
    "conventions and thresholds blocks, with the text of conventions.held_out_counts; none used",
    "WP3's contract and fit reviewers, 23 October 2026: the contract JSON's perturbations_E6 rule texts (rows "
    "2, 3 and 9: constants, bands, must_show) and its thresholds' R and units for the three engines (rule "
    "texts and contract constants, no row value); none used as a fit input beyond the R the fit already "
    "reads through the calibration view",
    "WP3's fixer, 23 October 2026: no contract text and no EPA file; the code, docs/build_step_2/AMENDMENTS.md "
    "section C and WP3_INTERFACES.md, and the reviews above",
    # the second round of reviews and its fix (23 October 2026)
    "WP3's second isolation reviewer, 23 October 2026: key names of the contract's engine blocks, lambda_clip_floor, "
    "coverage and held_out_rows records; the top-level and conventions key lists; the numeric-leaf key paths of "
    "conventions, model_form and perturbations_E6; no value, no EPA table",
    "WP3's second contract reviewer, 23 October 2026: the contract JSON's E6 band texts and the numbers its parsers "
    "take from them (rule text), and ecu_strategy_b58's k3_pair_change tables against the B58's k3 rows (B58 "
    "measurements); no EPA table, no row value",
    "WP3's second fit reviewer, 23 October 2026: the calibration and held-out row counts per table of the three "
    "engines (the contract's tables block), for a run-time estimate; T0 and the fits ran on synthetic rows only; no "
    "EPA table, no row value",
    "WP3's second test reviewer, 23 October 2026: every WP3 suite run, test_epa_rows.Structural among them (the real "
    "tables' structure, booleans and counts only) and Gate's probe of this tree's Run 1 rule text; no value printed",
    "WP3's second fixer, 23 October 2026: the contract JSON's perturbations_E6 rows 5, 6 and 9 (constant, band and "
    "must_show texts) and the engine specs' labels; no EPA table, no row value",
    "WP3's repinner to version 5, 23 October 2026: the contract JSON's diff from version 4 to version 5 (each "
    "changed line's first 400 characters, with its context lines: _generated, decisions 76-77, model_form's "
    "in-sample stage and rules, open_for_the_team, seen_before_writing, whose first entry prints the all-row "
    "turbine-inlet-temperature maxima the amendments' entry above discloses, version_5 and generators.sha256); "
    "version 5's open_for_the_team, version_5.go_ahead and version_5.schema in full; the .md's section headings "
    "at both versions and its section 14; and results/ENGINE_THRESHOLDS.md:449-452 at both versions and "
    ":467-470 at version 5 (two rows of a per-line counts table and a list of per-engine kPa figures, read while "
    "checking a line citation); no EPA table, no row value; none used",
) + tuple("WP3's pin author, before the fit (epa_stats.SOURCES_READ): " + s for s in epa_stats.SOURCES_READ) + (
    # decision 56's pins' reads, taken from epa_stats itself (calibrate_epa imports it; WP3_INTERFACES.md 11:
    # "calibrate_epa.SEEN_BEFORE_THE_FIT must take epa_stats.SOURCES_READ"), and the third round of reviews and
    # its fix (WP3's third fix of 24 October 2026; test_calibrate_epa.Pieces checks every entry is here)
    "WP3's third isolation reviewer, 24 October 2026: the contract JSON's top-level keys and the key paths and types "
    "of model_form and conventions; the text of model_form.in_sample_rules and version_5 in full; thresholds/"
    "split.py's source and thresholds/contract.py:1312-1341 (rule text); through a grep, the lam_floor line of each "
    "EPA engine spec, which prints each engine's lambda clip floor, an all-row quantity (the deepest EPA lambda over "
    "every row less 0.01, held-out rows included); epa_stats' Table 8 pin rows; planted leaks run on synthetic "
    "repositories only; no EPA table opened, no row value printed; none used",
    "WP3's third contract reviewer, 24 October 2026: the four EPA test reports (logs/epa/<engine>/3- and 3a- ... Test "
    "Report.docx) through zipfile in a scratch script, printing only each report's Table 8 (caption, header and "
    "rows), the table-of-contents lines that begin with 'Uncertainty', and as booleans whether each quoted Table 8 "
    "note occurs verbatim; nothing else printed; none used",
    "WP3's Run 1 reviewer, 24 October 2026: the contract JSON's perturbations_E6 band texts, parsed through "
    "epa_stats.e6_band_values and row10_etas, printing only key names, one boolean and two counts; `git ls-files` "
    "of the engines' data folder (file names only); PLAN.md section 5.11 (its design-time row counts); "
    "epa_stats.SOURCES_READ's text; synthetic runs only; no EPA table, no row value; none used",
    "WP3's third test reviewer, 24 October 2026: from the contract JSON, printed in full, model_form.in_sample_rules."
    "sampling_noise and version_5 (rule text only); engine_facts(...).table_sources' test cells, compared as "
    "booleans with epa_stats.REPORT_CELLS (nothing printed); the scratchpad's pre_run1_result.json 'pins' summary, "
    "which quotes the Table 8 instrument rows; test_contract_pinned on the tree; no EPA table opened, no row value "
    "seen; none used",
    "WP3's third fixer, 24 October 2026: no contract text and no EPA file; the code (epa_stats.U_D's Table 8 pin "
    "rows and SOURCES_READ among it), docs/build_step_2/WP3_INTERFACES.md and the four reviews of 24 October with "
    "their scratch prototypes (synthetic repositories only); none used",
    # the fourth round of reviews and its fix (WP3's fourth fix of 24 October 2026; test_calibrate_epa.Pieces)
    "WP3's fourth isolation reviewer, 24 October 2026: the contract JSON for rule text and the R values of the three "
    "engines and the B58-based budget (contract constants, compared as equal; no EPA value); planted git leaks run on "
    "synthetic repositories only; no EPA table opened, no row value printed; none used",
    "WP3's fourth contract reviewer, 24 October 2026: the four EPA test reports through zipfile in scratch scripts -- "
    "each report's Table 8 (its caption, the paragraph before it and its rows), the table-of-contents 'Uncertainty' "
    "lines, the HD1 paragraphs on its high-load windows and on the 'geometric sum', and the Mazda paragraph on the "
    "signals' uncertainties; from the contract JSON ecu_strategy_b58, budget, knee_shift, conventions, "
    "model_form.in_sample_rules, tests_lists, and the Mazda's per_held_out_line, deciding_lines and pooled_counts; no "
    "EPA table, workbook or data value; none used",
    "WP3's fourth Run 1 reviewer, 24 October 2026: the contract JSON's thresholds, D1's R per engine compared as "
    "booleans with 0.6 % and 1.0 % (nothing else printed); synthetic runs only; no EPA table, no row value; none used",
    "WP3's fourth test reviewer, 24 October 2026: docs/build_step_2/WP3_INTERFACES.md in full; results/"
    "ENGINE_THRESHOLDS.md lines 520-570 and 1000-1012 and the lines its greps for decision 77, version 5 and the snap "
    "printed; PLAN.md section 8.4 and AMENDMENTS.md's C12 line; mutations in scratch clones only; no EPA table, D3 "
    "file, workbook, test report or epa_engine.json content; none used",
    "WP3's fourth fixer, 24 October 2026: no contract text and no EPA file; the code, docs/build_step_2/"
    "WP3_INTERFACES.md and the four reviews of 24 October with their scratch scripts; T0's synthetic seeds fitted on "
    "test_calibrate_epa's synthetic Mazda tables under synthetic R (test_epa_stats' synthetic view, whose E1a, E2a and "
    "E3a are PLAN.md 5.1's residual scales as epa_fit._scales' docstring quotes them); none used",
    # after Run 1's first pass (24 October 2026): the defect hunt and the fixes of 29 October 2026
    "THE DISCLOSURE (Ghassan's order of 29 October 2026; results/VALIDATION_DECISIONS.md section H): the defect "
    "hunt's code-path investigator, 24 October 2026, after the Mazda's first fit, while reading the Mazda's "
    "epa_engine.json, printed part of its ALPHA full-throttle curve (wot_torque_curve), whose "
    "measured_at_speed records cite High Load Initial rows 12, 18, 24 and 30; the node of row 18, at 1751 rpm, is a "
    "held-out row's (the contract, section 2.3), so that held-out row's Initial torque was seen; only E1i, "
    "descriptive, reads Initial torque; none used, and no later check opens epa_engine.json's curve fields",
    "the defect hunt, 24 October 2026 (read-only, after the Mazda's first fit and the Honda's T0): the three engines' "
    "calibration steady and Final rows through epa_rows.calibration_rows (pickled in the scratchpad's "
    "defect_hunt/verdict/), the Mazda's frozen fits evaluated on them through epa_fit.evaluate_rows, the Mazda's "
    "Atkinson ratio and cam phases and the Honda's effective strokes, and the Mazda's and the Honda's Final and "
    "steady TIT at matched calibration points (finding F-1); calibration rows only, no held-out row",
    "the implementer of defect D-1 and decisions 82-85, 29 October 2026: the defect hunt's verdict and the Run 1 log; "
    "the three engines' calibration steady and Final rows from the hunt's pickle, through calibrate_epa.valve_brackets "
    "(D-1's evidence: the Atkinson fit and the brackets); the Honda's first-pass t0.json (its d2_gate detail: the "
    "truth's and the fitted gates and the flat intervals of its T0 seeds); the Mazda's first-pass complete.json "
    "(its E6 probe records) and the frozen Mazda plant's locked climb (model outputs: decision 85's climb-cell "
    "resolution); no held-out row, no epa_engine.json field, no contract value beyond the code's own reads",
)


# ======================================================================================================
# Refusals, the gate, and the bookkeeping of one invocation
# ======================================================================================================
class Refusal(Exception):
    """A subcommand that may not run now: a missing predecessor, a record that exists, a dirty tree. Its
    message names the cause and carries no value; run.json records it."""


class Run1Waits(Refusal):
    """The contract's Run 1 rule holds Run 1 (module docstring: RUN 1 WAITS)."""


class CompletionDefect(RuntimeError):
    """An assertion of the completion failed (PLAN.md 5.9: a non-finite field, a second knee that moved
    the trace, a table or floor that moved with the knee, a frozen section that moved): a coding defect,
    which the defect route fixes (PLAN.md 5.6)."""


def run1_go(environ, engine):
    """Whether `environ`'s EPA_RUN1_GO names `engine` (one id, or a comma-separated list of ids)."""
    return engine in {w.strip() for w in str(environ.get(RUN1_GO, "")).split(",") if w.strip()}


def run1_waits(*, source, environ, engine):
    """(waits, rule): whether Run 1 must wait for `engine` (the committed contract holds the rule,
    epa_rows.run1_wait, which fails closed, and `environ` does not name the engine in EPA_RUN1_GO), and the
    rule's text. `environ` is a mapping, os.environ on the command line, so the switch is testable without
    setting it."""
    rule = epa_rows.run1_wait(source=source)
    return (rule is not None and not run1_go(environ, engine)), rule


def gated(subcommand, name, *, source):
    """Whether the Run 1 gate holds `subcommand` now (module docstring): dry-load always, t0 and fit while
    STARTED is absent (the first evaluation at an EPA row's inputs; whether a file exists is no open)."""
    if subcommand in GATED_ALWAYS:
        return True
    return subcommand in GATED_UNTIL_STARTED and not _exists(name, source, STARTED)


def gate_record(name, *, source, subcommand):
    """What STARTED and each run.json entry record of the gate: the rule's text (None: none stands), the
    switch as set, whether the subcommand was gated, whether it waited."""
    try:
        rule = epa_rows.run1_wait(source=source)
    except epa_rows.LoaderStop as exc:
        rule = f"unreadable: {type(exc).__name__}"
    g = gated(subcommand, name, source=source)
    return {"rule": rule, "switch": os.environ.get(RUN1_GO), "gated": g,
            "waits": bool(g and rule is not None and not run1_go(os.environ, name))}


def _gate(name, source, subcommand):
    if not gated(subcommand, name, source=source):
        return
    waits, rule = run1_waits(source=source, environ=os.environ, engine=name)
    if waits:
        raise Run1Waits("Run 1 waits: the contract names Run 1 in its open_for_the_team, or is the commit epa_rows "
                        f"pins (epa_rows.run1_wait, which fails closed); {RUN1_GO}={name} lets this engine go, on "
                        "the team's order")


def _jobs(jobs):
    if type(jobs) is not int or jobs < 1:
        raise Refusal(f"--jobs must be a positive int, not {jobs!r} (no default job count)")
    return jobs


def scratch_problem(scratch, root):
    """Why a scratch folder (dry-load's --out, poison's --scratch) may not be used, or None: inside the work
    tree its files -- the poisoned copies of the tables, calibration rows intact, and a garbled contract that
    keeps held_out_rows -- could be committed (WP3's third fix of 24 October 2026, on the Run 1 review's
    finding)."""
    if not scratch:
        return None
    a = _norm_abs(os.path.realpath(scratch))
    r = _norm_abs(os.path.realpath(root))
    if _under(a, r):
        return f"the scratch folder lies inside the work tree {root}: name one outside it"
    return None


def _outside_tree(scratch, source, flag):
    why = scratch_problem(scratch, source.root)
    if why is not None:
        raise Refusal(f"{flag}: {why}")


def worker_init(subcommand, engine, root, scratch, paths):
    """The ordered pool's initializer (WP3_INTERFACES.md 3.3, 5.5.3): the same audit in every spawn worker
    (C3: a parent's hook does not see a worker), each open it records appended to epa_fit.WORKER_OPENED,
    which ordered_map returns beside each task's result and merges into epa_fit.POOL_OPENED in task order.
    `paths` is the parent's epa_rows.audit_paths as (key, value) pairs. A worker runs cycles on the rows
    it is handed and reads no table, so its audit is sealed outright: the engine's own tables,
    epa_engine.json and the contract are refused (Audit.sealed; WP3's fixes of 23 October 2026)."""
    a = install_audit(subcommand=subcommand, engine=engine, root=root, scratch=scratch)
    a.bind(dict(paths))
    a.sealed = True
    a.on_open = epa_fit.WORKER_OPENED.append


def _paths_for(name, *, source):
    p = dict(epa_rows.audit_paths(name, source=source))
    p["derived"] = epa_freeze.derived_relpath(name)
    p["b58_derived_abs"] = os.path.abspath(derived.B58_PATH)
    return p


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _where(exc):
    """Where an exception was raised, as file:line of its innermost frames, no message: read off the frames
    themselves (traceback.walk_tb), never the source files, which the audit would record as opens."""
    out = [f"{os.path.basename(f.f_code.co_filename)}:{line}" for f, line in traceback.walk_tb(exc.__traceback__)]
    return " <- ".join(reversed(out[-6:]))


def invoke(subcommand, name, *, source, argv, body, scratch, audit):
    """Run one subcommand's `body` (a callable returning a dict of counts and flags, or None) under the
    audit, and append its invocation to run.json (WP3_INTERFACES.md 7.2): k, subcommand, argv, the start
    and end (UTC), seconds, outcome ("ok", "refused: <reason>", "crash: <type>", "defect: ..."), every
    path opened (the workers' merged), every subprocess, the paths outside the allowlist and those
    refused, git's HEAD, whether the step-2 code is clean, the versions. Returns the exit code. `audit`
    is the command line's (installed by _prelude), or None to install one here (the tests)."""
    t0, started = time.time(), _now()
    if audit is None:
        audit = install_audit(subcommand=subcommand, engine=name, root=source.root, scratch=scratch)
    else:
        _CURRENT[0] = audit
    outcome, code, extra = "ok", EXIT_OK, {}
    pending = None
    mark = len(epa_fit.POOL_OPENED)
    gate = None
    try:
        paths = _paths_for(name, source=source)
        audit.bind(paths)
        gate = gate_record(name, source=source, subcommand=subcommand)
        epa_fit.set_worker_init((worker_init, (subcommand, name, os.path.abspath(source.root), scratch,
                                               tuple(sorted((k, v) for k, v in paths.items())))))
        extra = body() or {}
    except CheckFailed as exc:
        outcome, code = f"mismatch: {exc}", EXIT_MISMATCH
        print(f"calibrate_epa.py {subcommand} --engine {name}: mismatch: {exc}")
    except Refusal as exc:
        outcome, code = f"refused: {exc}", EXIT_REFUSED
        print(f"calibrate_epa.py {subcommand} --engine {name}: refused: {exc}")
    except epa_rows.LoaderStop as exc:
        # a guard of the loader stopped (the contract, a table, a header, the poisoned copies): a refusal about the
        # data or the tree, not a coding defect, so it does not force the defect route (WP3's fourth fix of 24
        # October 2026, on the fourth Run 1 review's finding that it was recorded as an audited crash). Its message,
        # which can name rows, is neither printed nor recorded; where it was raised is. An open the audit refused
        # on the way stays a defect (refused_by_audit; epa_freeze.audit_problems reads it whatever the outcome).
        outcome, code = f"refused: LoaderStop at {_where(exc)}", EXIT_REFUSED
        print(f"calibrate_epa.py {subcommand} --engine {name}: refused: a loader guard stopped at {_where(exc)}")
    except Exception as exc:                                       # noqa: BLE001 -- recorded, then the exit code
        outcome, code = f"crash: {type(exc).__name__}", EXIT_CRASH
        print(f"calibrate_epa.py {subcommand} --engine {name}: crash: {type(exc).__name__} at {_where(exc)}")
    except BaseException as exc:                                   # a KeyboardInterrupt, a SystemExit inside the body
        # recorded as a crash in run.json, then raised again after the entry is written: a killed fit leaves
        # STARTED and partial records, and its outcome must be logged (WP3's third fix of 24 October 2026, on
        # the Run 1 review's finding)
        outcome, code, pending = f"crash: {type(exc).__name__}", EXIT_CRASH, exc
        print(f"calibrate_epa.py {subcommand} --engine {name}: crash: {type(exc).__name__} at {_where(exc)}")
    finally:
        deactivate()
        epa_fit.set_worker_init(None)
        # a body that did not end ok may leave a pool with a task that never completes (a worker that died): its
        # workers are killed, not waited for, so that the entry below is written (WP3's fourth fix of 24 October
        # 2026, on the fourth Run 1 review's finding that close() then join() hung after a worker died)
        epa_fit.close_pools(terminate=outcome != "ok" or pending is not None)
    worker = list(epa_fit.POOL_OPENED[mark:])
    opened = sorted(audit.opened | {p for p in worker if not p.startswith(REFUSED_TAG)})
    refused = list(audit.refused) + [p[len(REFUSED_TAG):] for p in worker if p.startswith(REFUSED_TAG)]
    outside = sorted(p for p in opened if not audit.allowed(p))
    if outside and code == EXIT_OK:
        outcome, code = "defect: opened outside the allowlist (PLAN.md 5.6)", EXIT_DEFECT
    elif refused and code == EXIT_OK:
        # an open the audit refused is a coding defect even when the code that made it caught the refusal
        # (linecache returns no lines; WP3's second fix of 23 October 2026, on the isolation review's table leak)
        outcome, code = "defect: an open refused by the audit, the refusal caught (C3; PLAN.md 5.6)", EXIT_DEFECT
    try:
        head = epa_freeze.git_head(root=source.root)
        clean, _dirty = epa_freeze.git_clean(epa_freeze.CODE_HASHED, root=source.root)
    except Exception:                                              # noqa: BLE001
        head, clean = None, None
    entry = {"subcommand": subcommand, "argv": list(argv), "started_utc": started, "ended_utc": _now(),
             "seconds": round(time.time() - t0, 3), "outcome": outcome, "opened": opened,
             "subprocesses": audit.subprocesses, "outside_allowlist": outside, "refused_by_audit": refused,
             "git_head": head, "step2_clean": clean, "run1_gate": gate, "versions": epa_freeze.versions()}
    if extra:
        entry["result"] = extra
    path = (os.path.join(scratch, RUN) if subcommand == "dry-load"
            else os.path.join(epa_freeze.calibration_dir(name, root=source.root), RUN))
    if subcommand == "dry-load" and scratch_problem(scratch, source.root) is not None:
        # dry-load's record goes to its scratch folder, never into the work tree (scratch_problem)
        print(f"calibrate_epa.py {subcommand} --engine {name}: {outcome.split(':')[0]}; no run.json written "
              "(the scratch folder lies inside the work tree)")
        if pending is not None:
            raise pending
        return code
    _append_run(name, path, entry, root=source.root, scratch=scratch if subcommand == "dry-load" else None)
    if outside:
        print(f"calibrate_epa.py {subcommand} --engine {name}: {len(outside)} path(s) opened outside the "
              f"allowlist; see {path}")
    print(f"calibrate_epa.py {subcommand} --engine {name}: {outcome.split(':')[0]}; run.json: {path}")
    if pending is not None:
        raise pending
    return code


def _append_run(name, path, entry, *, root, scratch):
    """Append one invocation to a run.json ({engine, invocations}), k numbered from 1."""
    if scratch is None:
        old = epa_freeze.read_json(path, root=root) if os.path.exists(path) else {"engine": name, "invocations": []}
    else:
        old = epa_freeze.read_json(path, root=scratch) if os.path.exists(path) else {"engine": name, "invocations": []}
    inv = list(old.get("invocations", []))
    inv.append({"k": len(inv) + 1, **entry})
    epa_freeze.write_json_atomic(path, {"engine": name, "invocations": inv})


# ======================================================================================================
# Records
# ======================================================================================================
def _dir(name, source):
    return epa_freeze.calibration_dir(name, root=source.root)


def _p(name, source, rel):
    return os.path.join(_dir(name, source), *rel.split("/"))


def _exists(name, source, rel):
    return os.path.exists(_p(name, source, rel))


def _read(name, source, rel):
    return epa_freeze.read_json(_p(name, source, rel), root=source.root)


def _write(name, source, rel, obj):
    return epa_freeze.write_json_atomic(_p(name, source, rel), obj)


def _require(name, source, rel, why):
    if not _exists(name, source, rel):
        raise Refusal(f"{epa_freeze.CALIBRATION_DIR}/{name}/{rel} does not exist: {why}")


def _forbid(name, source, rel, why):
    if _exists(name, source, rel):
        raise Refusal(f"{epa_freeze.CALIBRATION_DIR}/{name}/{rel} exists: {why}")


def _clean_code(source, why):
    clean, dirty = epa_freeze.git_clean(epa_freeze.CODE_HASHED, root=source.root)
    if not clean:
        raise Refusal(f"the step-2 code is not committed and clean ({', '.join(dirty)}): {why}")


def _clean_plant(name, source, why):
    """The plant's code and specs (epa_freeze.plant_files: PLANT_CODE and the engine's specs, what plant_sha
    hashes) committed and clean (WP3's third fix of 24 October 2026, on the Run 1 review's finding that an
    uncommitted plant edit present throughout Run 1 passed every plant_sha comparison)."""
    clean, dirty = epa_freeze.git_clean(epa_freeze.plant_files(name), root=source.root)
    if not clean:
        raise Refusal(f"the plant's code and specs are not committed and clean ({', '.join(dirty)}): {why}")


def _frozen_code_guard(name, source, why):
    """poison, e6 and complete build on the freeze: the step-2 code and the plant committed and clean, and the
    code (code_shas) and the plant (plant_sha) the ones freeze.json records (WP3's third fix of 24 October 2026,
    on the Run 1 review's finding that an edit made during e6 or complete and reverted before arm left records
    no commit reproduces). A change after the freeze is the defect route's, which re-runs from T0."""
    _clean_code(source, why)
    _clean_plant(name, source, why)
    fz = _read(name, source, FREEZE)
    changed = epa_freeze.code_changes(fz.get("code") or {}, root=source.root)
    if changed:
        raise Refusal(f"the step-2 code is not the code freeze.json records ({', '.join(changed)}): {why}")
    if epa_freeze.plant_sha(name) != (fz.get("plant") or {}).get("plant_sha"):
        raise Refusal(f"the plant's code and specs (plant_sha) are not those freeze.json records: {why}")


def _write_started(name, *, source, first, prov):
    """STARTED (WP3_INTERFACES.md 7.2), written once, atomically, before the first model evaluation at an
    EPA row's inputs; never rewritten. It records the Run 1 gate as it stood (the rule's text, the switch;
    WP3's fix of 23 October 2026). Returns whether this call wrote it."""
    if _exists(name, source, STARTED):
        return False
    _write(name, source, STARTED, {"engine": name, "first_subcommand": first, "git_head": prov["git"]["head"],
                                   "contract_commit": prov["contract"]["commit"], "view_sha256": prov["view_sha256"],
                                   "code_sha_text": prov["code_sha_text"],
                                   "run1_gate": {"rule": epa_rows.run1_wait(source=source),
                                                 "switch": os.environ.get(RUN1_GO)}})
    return True


def _held_out_guard(name, source, why):
    """The contract, section 7: "No refit after any held-out statistic of an engine has been computed" (and
    C11: "nothing is refitted"): refused once validate_epa.py run has started this engine (epa_freeze.
    held_out_started: its folder holds anything but ARMED.json, or git log --all does). WP3's fix of 23
    October 2026."""
    problems = epa_freeze.held_out_started(name, root=source.root,
                                           validation_rel=epa_rows.audit_paths(name, source=source)["validation"])
    if problems:
        raise Refusal(f"{why}: {'; '.join(problems)} (the contract, section 7: no refit after any held-out "
                      "statistic)")


def _audit_guard(name, source):
    """Refused while run.json holds an invocation the audit judged a defect, a crash or a mismatch, or one
    that opened a path outside its allowlist or had an open refused (epa_freeze.audit_problems): PLAN.md 5.6
    makes each a coding defect, which only the defect route follows (WP3's fix of 23 October 2026)."""
    if not _exists(name, source, RUN):
        return
    problems = epa_freeze.audit_problems(_read(name, source, RUN), subcommands=epa_freeze.AUDITED_SUBCOMMANDS)
    if problems:
        raise Refusal("; ".join(problems))


def _pins_guard(name):
    """Refused while a u_D term a gating row reads, or a summary column of ANY engine's D3 chain, is not
    pinned (epa_stats.unpinned_u_d, d3_rows.unpinned_for): pinned after the first fit, either is a change to
    the step-2 code only the defect route admits (C10), and either stops the one-shot held-out run (WP3's
    fix of 23 October 2026). Every engine's columns, not only `name`'s (WP3's third fix of 24 October 2026, on
    the Run 1 review's finding): the code is shared, so pinning the Honda's or the Mazda's columns in d3_rows.py
    after the Ford's T0 would change the code the Ford's T0 certified and its arming would refuse under C10.
    Each is named, with its engine."""
    out = [f"u_D's {t!r} term (read by {', '.join(rows)})"
           for t, rows in epa_stats.unpinned_u_d(terms=epa_stats.U_D).items()]
    for engine in sorted(epa_rows.TABLES):
        out += [f"the D3 summary column {k} ({engine})" for k in d3_rows.unpinned_for(engine)]
    if out:
        raise Refusal(f"not pinned before Run 1 of any engine, {name} included (decision 56; WP3_INTERFACES.md 11): "
                      + "; ".join(out))


def _versions_guard(recorded):
    """Refused when this process's Python, NumPy or SciPy is not requirements-lock.txt's pin, or not the
    version the run's earlier record holds (`recorded`: t0.json's for fit, freeze.json's for poison, e6,
    complete and check; None for t0, the first): the poison's full refit must hash equal, the refit variants'
    no-op identity needs bit-identical refits, and amendment D5 pins SciPy because the fit depends on it
    (CLAUDE.md's rule 4; WP3's second fix of 23 October 2026, on the fit review's finding that the versions
    were recorded and never enforced)."""
    problems = epa_freeze.version_problems(recorded)
    if problems:
        raise Refusal("the environment is not Run 1's (CLAUDE.md rule 4; amendment D5): " + "; ".join(problems))


def _freeze_versions(name, source):
    return _read(name, source, FREEZE).get("versions")


def _poison_guard(name, source, frozen_sha):
    """C8's proof required before the refit variants and the completion: poison.json present, complete and
    equal at the frozen sections, with the full form-A poison fit on epa_freeze.FULL_POISON_ENGINE
    (epa_freeze.poison_problems, which the arming reads too; WP3's fix of 23 October 2026)."""
    _require(name, source, POISON, "C8's poison fit is mandatory in Run 1 and comes before e6")
    problems = epa_freeze.poison_problems(_read(name, source, POISON), engine=name,
                                          frozen_sections_sha256=frozen_sha, poisons=tuple(epa_rows.POISONS),
                                          run_keys=epa_fit.POISON_RUN_KEYS, stages=epa_fit.poison_run_stages(),
                                          tied_of=epa_fit.poison_tied_stages)
    if problems:
        raise Refusal("poison.json is not C8's proof: " + "; ".join(problems))


def _next_invocation(name, source):
    """The k this invocation will have in run.json (invoke appends it last): the defect records name it, so
    that defects.json holds no wall-clock time (PLAN.md 5.1; WP3's fix of 23 October 2026)."""
    if not _exists(name, source, RUN):
        return 1
    return len(_read(name, source, RUN).get("invocations") or []) + 1


def _load(name, *, source):
    """The calibration view (C4) and the yield (plan 4.3), after every guard."""
    return epa_rows.calibration_contract(name, source=source), epa_rows.calibration_rows(name, source=source)


def _with_provenance(rec, prov):
    """A record with its provenance second, after its schema (WP3_INTERFACES.md 7.1)."""
    out = {"schema": rec["schema"], "provenance": prov}
    out.update({k: v for k, v in rec.items() if k != "schema"})
    return out


def _defect_route(defect, fix_commit):
    """The defect route's authority from the command line, or None (PLAN.md 5.6; C10)."""
    if defect is None and fix_commit is None:
        return None
    if not defect or not fix_commit:
        raise Refusal("the defect route names both its reason (--defect) and its fix commit (--fix-commit)")
    return epa_freeze.DefectRoute(reason=str(defect), fix_commit=str(fix_commit))


def _record_defect(name, *, source, defect, found_by):
    """The defect route's records (WP3_INTERFACES.md 5.5.2, 7.2): the run's outputs moved verbatim to
    defect_<k>/ (epa_freeze.move_run_to_defect) and one entry appended to defects.json."""
    try:
        epa_freeze.check_defect(defect, root=source.root)
    except (epa_freeze.FreezeRefusal, TypeError, ValueError) as exc:
        raise Refusal(f"the defect route's authority is refused: {exc}") from None
    k = epa_freeze.move_run_to_defect(name, root=source.root)
    epa_freeze.append_defect(name, {"k": k, "run_invocation": _next_invocation(name, source), "found_by": found_by,
                                    "assertion": defect.reason, "fix_commit": defect.fix_commit,
                                    "previous_run": f"defect_{k}/"}, root=source.root)
    return k


# ======================================================================================================
# dry-load (plan 4.6 item 8)
# ======================================================================================================
def dry_load(name, *, source, out):
    """The view, the yield, the engine's facts and the provenance -- everything the fit loads -- and no
    model evaluation, so that the audit shows what loading opens (plan 4.6 item 8). Writes <out>/run.json
    only (through invoke). Returns counts and hashes for run.json, no row value."""
    _gate(name, source, "dry-load")
    if not out:
        raise Refusal("--out names the scratch folder dry-load's run.json goes to")
    _outside_tree(out, source, "--out")
    view, yield_ = _load(name, source=source)
    epa_rows.engine_facts(name, source=source)
    prov = epa_freeze.provenance(name, source=source, view=view)
    by_type = {}
    for r in yield_.rows:
        by_type[type(r).__name__] = by_type.get(type(r).__name__, 0) + 1
    return {"rows": len(yield_.rows), "by_type": dict(sorted(by_type.items())), **epa_rows.table_counts_record(yield_),
            "yield_sha256": yield_.sha256, "manifest_sha256": yield_.manifest.sha256, "view_sha256": view.sha256,
            "step2_clean": prov["git"]["step2_clean"]}


# ======================================================================================================
# t0 (PLAN.md 5.10; amendments A1, D11)
# ======================================================================================================
def t0(name, *, source, jobs, defect):
    """T0, synthetic recovery at the calibration rows' inputs, on committed code, before the fit (A1):
    epa_fit.run_t0, written to t0.json with its provenance. Writes STARTED if absent (T0 evaluates at the
    rows' inputs). Refused after a fit, when t0.json exists (unless the defect route, `defect`, moves the
    run to defect_<k>/ first: T0's failure is a coding defect, PLAN.md 5.10), on a dirty tree, while a pin
    is open (_pins_guard) and once the held-out run has started."""
    _gate(name, source, "t0")
    _jobs(jobs)
    _held_out_guard(name, source, "T0 runs before the fit")
    if defect is None:
        _forbid(name, source, T0, "T0 runs once; a re-run is the defect route (t0 --defect)")
        for rel in (STAGE0, FREEZE):
            _forbid(name, source, rel, "T0 runs before the fit (amendment A1)")
        # a T0 the audit judged a defect or a crash is not re-run plainly (WP3's third fix of 24 October 2026,
        # on the Run 1 review's finding: the fit would refuse on the crash after a re-run of tens of minutes)
        _audit_guard(name, source)
    else:
        # t0 --defect moves the calibration folder but not the derived file: after a fit, the route is fit
        # --defect, which re-runs T0 and the fit (WP3's third fix of 24 October 2026, on the Run 1 review's
        # finding that the next plain fit then crashed in write_derived after the whole ladder)
        for rel in (STAGE0, FREEZE, IN_SAMPLE):
            _forbid(name, source, rel, "a fit has run: its defect route is fit --defect, which re-runs T0 too")
        if os.path.exists(epa_freeze.derived_path(name, root=source.root)):
            raise Refusal(f"{epa_freeze.derived_relpath(name)} exists: a fit has run; its defect route is fit "
                          "--defect, which re-runs T0 too")
    _clean_code(source, "T0 runs on committed code (amendment A1)")
    _clean_plant(name, source, "T0 runs on a committed plant (amendment A1)")
    _pins_guard(name)
    _versions_guard(None)
    if defect is not None:
        _record_defect(name, source=source, defect=defect, found_by="calibrate_epa.py t0 --defect")
    return _run_t0(name, source=source, jobs=jobs)


def _run_t0(name, *, source, jobs):
    """T0 itself, after its refusals: STARTED if absent, epa_fit.run_t0, t0.json."""
    view, yield_ = _load(name, source=source)
    prov = epa_freeze.provenance(name, source=source, view=view)
    _write_started(name, source=source, first="t0", prov=prov)
    with sealed():
        body = epa_fit.run_t0(name, yield_, view=view, jobs=jobs, dtheta=DTHETA)
    _write(name, source, T0, _with_provenance(body, prov))
    print(f"t0 {name}: pass {body['pass']}; wrote {epa_freeze.CALIBRATION_DIR}/{name}/{T0}")
    return {"pass": bool(body["pass"])}


# ======================================================================================================
# fit (PLAN.md 5.2-5.5, 5.8; decisions 49-55; amendments C1, C2, C10, C13, D13)
# ======================================================================================================
# The Ford's Cell 9 octane claim (HANDOFFS.md WP3 item 5; epa_fit.FORD_CELL9_OCTANE) is measured at an
# octane other than the engine's typed one: epa_engine.json's alpha_fuel research_octane_number where it
# differs from it, else, DESIGN, the typed octane less OCTANE_STEP_RON, the size of the difference
# HANDOFFS.md records between the two batches (the claim -- the octane moves only the knock outputs -- is
# a property of the cycle model at any other octane; mistake 24 asks that it be measured, not its size).
OCTANE_STEP_RON = 1.0


def other_octane(view, facts, *, plant):
    """(octane, source) for fit_declarations, or (None, None) on an engine whose tables are on one fuel
    batch (one FTAG in the view's fuel_by_table): the octane claim is measured only where two batches
    meet."""
    if len({str(tf.ftag) for tf in view.fuel_by_table.values()}) < 2:
        return None, None
    own = float(plant.engine.cycle.octane)
    alpha = (facts.alpha_fuel or {}).get("research_octane_number")
    if isinstance(alpha, (int, float)) and not isinstance(alpha, bool) and float(alpha) != own:
        return float(alpha), "epa_engine.json alpha_fuel research_octane_number"
    return own - OCTANE_STEP_RON, f"DESIGN: the typed octane less {OCTANE_STEP_RON} RON"


def stage0_record(yield_, s0, *, view):
    """stage0.json's body (WP3_INTERFACES.md 7.2) without its provenance: the yield's counts and hashes,
    S0's checks (epa_fit.s0's report), its flags, SEEN_BEFORE_THE_FIT and the declarations."""
    initial = {r.hold for r in yield_.rows if type(r) is epa_rows.InitialRow}
    final = {r.hold for r in yield_.rows if type(r) is epa_rows.FinalRow}
    return {"schema": "epa-stage0/1",
            "yield": {**epa_rows.table_counts_record(yield_),
                      "yield_sha256": yield_.sha256, "manifest_sha256": yield_.manifest.sha256,
                      "initial_final_ids_identical": initial == final},
            "checks": s0.report, "flags": list(s0.flags), "seen_before_the_fit": list(SEEN_BEFORE_THE_FIT),
            "declarations": epa_fit.stage0_declarations(yield_, view=view)}


def in_sample_body(in_sample, *, chosen, reason):
    """in_sample.json's body without its provenance (WP3_INTERFACES.md 7.2): per form fitted, every
    in-sample statistic but E8 (each epa_stats.StatResult in its in-sample JSON form, 7.6), passes,
    failing, noise (decision 77's neither), no_line, and E8 reported apart (decision 39(a): outside the form criterion),
    and decision 83's steady-only TIT reading beside them (steady_only_tit, a sensitivity that decides nothing); the criterion,
    the chosen form and the reason. The one definition fit writes and check recomputes."""
    forms, criterion = {}, None
    for form in engines.CYCLE_FORMS:
        if form not in in_sample:
            continue
        s = in_sample[form]
        criterion = s.criterion
        # "noise": the statistics that neither block nor pass under decision 77, recorded per form beside the
        # failing ones, as the contract's "recorded so per form" asks (WP3's third fix of 24 October 2026)
        forms[form] = {"statistics": {r: v.as_json() for r, v in s.results.items() if r != "E8"},
                       "passes": bool(s.passes), "failing": list(s.failing), "noise": list(s.noise),
                       "no_line": list(s.no_line),
                       "e8": s.results["E8"].as_json() if "E8" in s.results else None,
                       # decision 83: the steady-only TIT reading beside the form's stage, a sensitivity that
                       # decides nothing (epa_stats.steady_tit_json; None on a stage built without it)
                       "steady_only_tit": epa_stats.steady_tit_json(getattr(s, "steady_tit", None))}
    return {"schema": "epa-in-sample/1", "criterion": criterion, "forms": forms, "chosen_form": chosen,
            "reason": reason}


def _canon(obj):
    return epa_rows.canonical_json(obj)


def fit(name, *, source, jobs, defect):
    """S0, the per-engine ladder (S1-S6, verify, the in-sample stage per form; decision 49), the derived
    file's frozen sections and freeze.json (PLAN.md 5.2-5.5, 5.8). Refused while freeze.json exists or a
    fit has started -- STARTED written by a fit (WP3_INTERFACES.md 5.5.1: "STARTED absent or written by
    t0"), or, after T0 wrote STARTED, stage0.json or in_sample.json there (a fit that crashed past S0) --
    unless the defect route (`defect`, an epa_freeze.DefectRoute naming its fix commit) moves the run to
    defect_<k>/ first and re-runs T0 on the fixed code (amendment A1), then S0 on;
    refused on dirty step-2 code (amendment C10: fit_A.json records the code at the first fit, and the
    freeze must be reproducible from its git_head), without a T0 that passed (t0.json, epa_freeze.
    t0_problems: amendment A1, PLAN.md 5.10), while a pin is open (_pins_guard), and once the held-out run
    has started (the contract, section 7)."""
    _gate(name, source, "fit")
    _jobs(jobs)
    _held_out_guard(name, source, "no refit after the held-out run")
    if defect is None:
        _forbid(name, source, FREEZE, "a re-freeze is the defect route (PLAN.md 5.6)")
        for rel in (STAGE0, IN_SAMPLE):
            _forbid(name, source, rel, "a fit has run; a re-fit is the defect route")
        if _exists(name, source, STARTED) and _read(name, source, STARTED).get("first_subcommand") != "t0":
            raise Refusal("a fit has started (STARTED); a re-fit is the defect route (PLAN.md 5.6)")
        # an invocation the audit judged a defect, a crash or a mismatch -- T0's among them -- is not built on
        # (WP3_INTERFACES.md 3.3; WP3's second fix of 23 October 2026, on the test review's finding that fit
        # froze on a T0 the audit had judged a defect); the defect route moves run.json with the run
        _audit_guard(name, source)
    _clean_code(source, "a freeze is reproducible from its git_head only from committed code (amendment C10)")
    _clean_plant(name, source, "a freeze is reproducible from its git_head only on a committed plant (amendment C10)")
    _pins_guard(name)
    if defect is not None:
        # the environment before anything moves (WP3's fourth fix of 24 October 2026, on the fourth Run 1 review's
        # finding that fit --defect moved the run and re-ran T0 before refusing the wrong NumPy or SciPy), as t0 does
        _versions_guard(None)
        _record_defect(name, source=source, defect=defect, found_by="calibrate_epa.py fit --defect")
        # the defect route re-runs from T0: the run's t0.json moved with it, and T0 certifies the fitting
        # code, which the fix changed (amendment A1; WP3's fix of 23 October 2026)
        _run_t0(name, source=source, jobs=jobs)
    if not _exists(name, source, T0):
        raise Refusal(f"{epa_freeze.CALIBRATION_DIR}/{name}/{T0} does not exist: T0 runs before the fit (amendment A1)")
    t0rec = _read(name, source, T0)
    problems = epa_freeze.t0_problems(t0rec)
    if problems:
        raise Refusal("; ".join(problems) + ": the defect route re-runs T0 on the fix (t0 --defect)")
    # T0 certified the code it ran on (amendment A1): the step-2 code and the plant must be that code still,
    # and the environment T0's (WP3's second fix of 23 October 2026, on the fit review's findings)
    problems = epa_freeze.t0_code_problems(t0rec, name=name, root=source.root)
    if problems:
        raise Refusal("; ".join(problems) + ": the defect route re-runs T0 on the code the fit runs (fit --defect)")
    _versions_guard((t0rec.get("provenance") or {}).get("versions"))
    view, yield_ = _load(name, source=source)
    facts = epa_rows.engine_facts(name, source=source)
    prov = epa_freeze.provenance(name, source=source, view=view)
    _write_started(name, source=source, first="fit", prov=prov)
    seal_now()           # from here on no table, no epa_engine.json and no contract is read (Audit.sealed)
    s0 = epa_fit.s0(yield_, view=view)
    _write(name, source, STAGE0, _with_provenance(stage0_record(yield_, s0, view=view), prov))
    print(f"fit {name}: S0 done ({len(s0.flags)} flag(s)); the ladder starts")
    lad = epa_fit.ladder(name, yield_, view=view, jobs=jobs, dtheta=DTHETA)
    files = {STAGE0: _p(name, source, STAGE0)}
    prev = None
    for f in lad.fits:
        cand = epa_fit.candidate(name, f.values)
        octane, osrc = other_octane(view, facts, plant=cand)
        decl = epa_fit.fit_declarations(cand, view=view, other_octane=octane, dtheta=DTHETA)
        decl["octane_source"] = osrc
        rec = epa_fit.fit_record(f, view=view, start=prev, dtheta=DTHETA, jobs=jobs, declarations=decl)
        _write(name, source, fit_file(f.form), _with_provenance(rec, prov))
        files[fit_file(f.form)] = _p(name, source, fit_file(f.form))
        print(f"fit {name}: form {f.form} fitted ({len(f.flags)} flag(s))")
        prev = f
    _write(name, source, IN_SAMPLE, _with_provenance(in_sample_body(lad.in_sample, chosen=lad.chosen,
                                                                     reason=lad.reason), prov))
    files[IN_SAMPLE] = _p(name, source, IN_SAMPLE)
    chosen = next(f for f in lad.fits if f.form == lad.chosen)
    epa_freeze.write_derived(name, epa_freeze.derived_values(chosen, provenance=prov), allow_defect=defect,
                             root=source.root)
    record = epa_freeze.freeze_record(name, fit=chosen, ladder=lad, files=files, provenance=prov, root=source.root)
    epa_freeze.write_freeze(name, record, root=source.root)
    print(f"fit {name}: froze form {lad.chosen}; wrote {epa_freeze.CALIBRATION_DIR}/{name}/{FREEZE}")
    return {"forms_fitted": [f.form for f in lad.fits], "chosen": lad.chosen,
            "flags": sorted({fl for f in lad.fits for fl in f.flags} | set(s0.flags))}


def _frozen_fit(name, *, source):
    """The frozen fit as the records hold it: freeze.json, and the chosen form's fit_<form>.json as an
    epa_fit.FormFit carrying its values (no stages), its hash checked against freeze.json's and
    recomputed by engines.frozen_sections_sha256 (mistake 10)."""
    fz = _read(name, source, FREEZE)
    rec = _read(name, source, fit_file(fz["form"]))
    values = {s: rec["values"][s] for s in engines.FROZEN_SECTIONS}
    sha = engines.frozen_sections_sha256(values)
    if not (sha == rec["frozen_sections_sha256"] == fz["frozen_sections_sha256"]):
        raise CompletionDefect(f"{fit_file(fz['form'])}'s frozen sections are not the ones freeze.json froze")
    return fz, rec, epa_fit.FormFit(engine=name, form=fz["form"], stages={}, values=values,
                                     frozen_sections_sha256=sha, flags=())


# ======================================================================================================
# poison (amendment C8; WP3_INTERFACES.md 5.5.1)
# ======================================================================================================
def _stage_bytes(st):
    return None if st is None else _canon(epa_fit.stage_json(st))


# The stages the poison's reference must also equal as the chosen fit recorded them: epa_fit's (one
# definition, beside POISON_STAGES; WP3's second fix of 23 October 2026).
POISON_TIED_STAGES = epa_fit.POISON_TIED_STAGES




def poison(name, *, source, jobs, scratch, full):
    """C8's proof that no held-out cell reaches the calibration, mandatory in Run 1 (WP3_INTERFACES.md
    5.5.1; e6 and the arming require poison.json): the tables' held-out cells poisoned three ways
    (epa_rows.POISONS: -1e+06, 1e+06, empty) in scratch copies, epa_engine.json's unread keys garbled; for
    each the copies shown not to be the tables (a raw sha256 differs), and the view, the yield, the manifest,
    engine_facts, S0 (against stage0.json) and S1-S3d and S6 at the frozen sections (epa_fit.poison_stages,
    against the same stages on the real yield) compared byte for byte; with `full` (mandatory on
    epa_freeze.FULL_POISON_ENGINE), the whole form-A fit, whose frozen sections must hash to fit_A.json's.
    The reference stages are tied to the fit: S1, S3a-S3c (S3d under D) equal the chosen fit_<form>.json's
    recorded ones. And the contract with every key the loader never reads garbled (C4): the view and the
    yield must come out the same. EVERY READ OF THE REAL TABLES AND OF THE CONTRACT COMES FIRST -- the
    references' loads, the garbled contract, the copies, each poisoned load's own guards -- and the audit is
    sealed (Audit.sealed) while the reference stages, the poisoned stages and the full fit run, so a stage
    that reads the repository's own tables, its epa_engine.json or the contract crashes there (WP3's fixes
    of 23 October 2026, on the isolation reviews' findings: a stage reading the tables passed the
    comparison, and one reading the contract passed everything, the garbled contract reaching the view and
    the yield only). Requires freeze.json; writes poison.json, then raises CompletionDefect if any
    comparison is not equal."""
    _jobs(jobs)
    _held_out_guard(name, source, "the poison proof is Run 1's")
    _require(name, source, FREEZE, "the poison fit compares with the freeze (C8)")
    _forbid(name, source, POISON, "the poison proof is written once")
    _audit_guard(name, source)
    if not scratch:
        raise Refusal("--scratch names the folder the poisoned copies are written to")
    if name == epa_freeze.FULL_POISON_ENGINE and not full:
        raise Refusal(f"the full form-A poison fit is mandatory on {epa_freeze.FULL_POISON_ENGINE} (C8; "
                      "WP3_INTERFACES.md 5.5.1): pass --full")
    _outside_tree(scratch, source, "--scratch")
    _frozen_code_guard(name, source, "the poison proof runs on the code and the plant the freeze ran on (C10)")
    _versions_guard(_freeze_versions(name, source))
    fz, rec_fit, frozen = _frozen_fit(name, source=source)
    view0, y0 = _load(name, source=source)
    m0 = epa_rows.manifest(name, source=source)
    facts0 = epa_rows.engine_facts(name, source=source)
    t_real = epa_freeze.table_shas(name, source=source)
    prov = epa_freeze.provenance(name, source=source, view=view0)
    stage0 = _read(name, source, STAGE0)
    tied = epa_fit.poison_tied_stages(frozen.form)
    recorded = rec_fit.get("stages") or {}
    fit_a = _read(name, source, fit_file("A")) if full else None
    # every read of the real tables and the contract, before the seal: the garbled contract, the copies,
    # and each copy's load (whose guards hash the real tables and compare the copies' calibration records
    # with theirs)
    sg = epa_rows.garbled_source(source, dst_dir=os.path.join(scratch, "garbled"))
    vg, yg = _load(name, source=sg)
    loads = {}
    for how in epa_rows.POISONS:
        sp = epa_rows.poisoned_tables(name, source=source, dst_dir=os.path.join(scratch, how), how=how)
        vp, yp = _load(name, source=sp)
        t_p = epa_freeze.table_shas(name, source=sp)
        loads[how] = (sp, vp, yp, epa_rows.manifest(name, source=sp), epa_rows.engine_facts(name, source=sp),
                      epa_rows.tables_moved(sp, source=source) and any(t_p[t] != t_real[t] for t in t_real))
    runs = {}
    with sealed():
        real_st = epa_fit.poison_stages(name, y0, view=view0, values=frozen.values, jobs=jobs, dtheta=DTHETA)
        real = {k: _stage_bytes(v) for k, v in real_st.items()}
        ref_eq = {k: (k in recorded and real[k] == _canon(recorded[k])) for k in tied}
        for how, (sp, vp, yp, mp, fp, differ) in loads.items():
            s0p = epa_fit.s0(yp, view=vp)
            stages = {"S0": _canon(s0p.report) == _canon(stage0["checks"])}
            got = epa_fit.poison_stages(name, yp, view=vp, values=frozen.values, jobs=jobs, dtheta=DTHETA)
            stages.update({k: _stage_bytes(v) == real[k] for k, v in got.items()})
            full_a = None
            if full:
                ff = epa_fit.fit_form(name, yp, view=vp, form="A", start=None, jobs=jobs, dtheta=DTHETA)
                full_a = {"frozen_sections_sha256_equal": ff.frozen_sections_sha256 == fit_a["frozen_sections_sha256"]}
            runs[how] = {"copies_are_not_the_tables": bool(differ), "stage0_equal": stages["S0"],
                         "view_equal": vp.sha256 == view0.sha256, "yield_equal": yp.sha256 == y0.sha256,
                         "manifest_equal": mp.sha256 == m0.sha256, "engine_facts_equal": fp == facts0,
                         "stages": stages, "full_form_a": full_a}
            print(f"poison {name}: {how}: every comparison equal {all(_flat_true(runs[how]))}")
    rec = {"schema": epa_freeze.POISON_SCHEMA, "runs": runs, "frozen_sections_sha256": frozen.frozen_sections_sha256,
           "form": frozen.form, "reference_equals_fit": ref_eq,
           "garbled_contract_view_equal": vg.sha256 == view0.sha256,
           "garbled_contract_yield_equal": yg.sha256 == y0.sha256}
    rec["all_equal"] = bool(all(_flat_true(runs)) and all(ref_eq.values()) and rec["garbled_contract_view_equal"]
                            and rec["garbled_contract_yield_equal"])
    _write(name, source, POISON, _with_provenance(rec, prov))
    if not rec["all_equal"]:
        raise CompletionDefect("a poisoned or garbled input moved the calibration, or the reference is not the "
                               "fit's (C8): see poison.json")
    return {"all_equal": True}


def _flat_true(obj):
    """Every boolean leaf of a poison record (None leaves skipped)."""
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _flat_true(v)
    elif isinstance(obj, bool):
        yield obj


# ======================================================================================================
# e6 (PLAN.md 5.7; amendment E2)
# ======================================================================================================
def e6_conventions(view):
    """The refit variants' conventions (PLAN.md 5.7; the contract's E6 rows 1-3): row 1 the lambda as
    published (cell_referenced False, the snap kept); row 2 AFR_st 14.7 in the calibration air and the
    plant's fuel, the B58's engines.Fuel.afr_st; row 3 the LHV 44.0 MJ/kg through engines.with_fuel, the
    B58's typed heating value (the literal every engine carried until build step 2). Both read from the
    B58's spec (engine_specs/b58.toml [fuel]), never retyped (mistake 10)."""
    b58 = engines.read_spec("b58")["fuel"]
    nominal = dataclasses.asdict(epa_stats.NOMINAL)
    return {"1": epa_stats.Conventions(**{**nominal, "cell_referenced": False}),
            "2": epa_stats.Conventions(**{**nominal, "afr_st": float(b58["afr_st"])}),
            "3": epa_stats.Conventions(**{**nominal, "lhv_j_per_kg": float(b58["lhv_j_per_kg"])})}


def _ladder_fits(name, *, source, form):
    """{form: epa_fit.FormFit} of every form the frozen ladder fitted up to `form`, each from its
    fit_<form>.json (values only, its hash checked against its own and recomputed, mistake 10): what
    epa_fit.refit_variant re-runs the frozen form's fit from."""
    out = {}
    for f in engines.CYCLE_FORMS[:engines.CYCLE_FORMS.index(form) + 1]:
        rec = _read(name, source, fit_file(f))
        values = {s: rec["values"][s] for s in engines.FROZEN_SECTIONS}
        sha = engines.frozen_sections_sha256(values)
        if sha != rec["frozen_sections_sha256"]:
            raise CompletionDefect(f"{fit_file(f)}'s frozen sections are not its own hash")
        out[f] = epa_fit.FormFit(engine=name, form=f, stages={}, values=values, frozen_sections_sha256=sha, flags=())
    return out


def e6(name, *, source, jobs):
    """The E6 refit variants before any held-out statistic (PLAN.md 5.7): rows 1, 2 and 3, the frozen form's
    own fit re-run under the variant's conventions as the frozen ladder ran it (epa_fit.refit_variant, from
    the frozen ladder's fits: no new ladder, S4's first start the frozen form's), and row 7's knock scale at
    KI x 0.90 and x 1.10 (epa_fit.knock_rescale, exact). Each to e6/row<n>.json; the plant in use stays
    frozen (validate_epa reports how far the model in use moves, amendment E2). Requires freeze.json and
    C8's proof (poison.json); refused when any e6 file exists, after an audited defect (_audit_guard) and once
    the held-out run has started."""
    _jobs(jobs)
    _held_out_guard(name, source, "the refit variants come before the held-out run")
    _require(name, source, FREEZE, "the refit variants start from the frozen fit (PLAN.md 5.7)")
    for v in E6_VARIANTS:
        _forbid(name, source, e6_file(v), "the refit variants are written once")
    _audit_guard(name, source)
    _frozen_code_guard(name, source, "the refit variants run on the code and the plant the freeze ran on (C10)")
    _versions_guard(_freeze_versions(name, source))
    fz, _rec, start = _frozen_fit(name, source=source)
    _poison_guard(name, source, start.frozen_sections_sha256)
    fits = _ladder_fits(name, source=source, form=start.form)
    view, yield_ = _load(name, source=source)
    prov = epa_freeze.provenance(name, source=source, view=view)
    seal_now()           # the refits read the yield and the view they are given (Audit.sealed)
    bands = epa_stats.e6_band_values(view.perturbations_e6)
    ki = bands["row7_ki"]
    if [f"7_{round(k * 100):03d}" for k in ki] != ["7_090", "7_110"]:
        raise CompletionDefect(f"the contract's row 7 scales {ki} are not the variants 7_090 and 7_110 "
                               "validate_epa reads")
    for v, conv in e6_conventions(view).items():
        ff = epa_fit.refit_variant(name, yield_, view=view, form=start.form, conventions=conv, ladder_fits=fits,
                                   jobs=jobs, dtheta=DTHETA)
        _write(name, source, e6_file(v), _with_provenance(
            {"schema": "epa-e6/1", "row": int(v), "variant": v, "conventions": dataclasses.asdict(conv),
             "knock_factor": None, "form": ff.form, "values": ff.values,
             "frozen_sections_sha256": ff.frozen_sections_sha256,
             "fit": {k: epa_fit.stage_json(s) for k, s in ff.stages.items()}}, prov))
        print(f"e6 {name}: row {v} refitted ({len(ff.flags)} flag(s))")
    for v, k in zip(("7_090", "7_110"), ki):
        vals = epa_fit.knock_rescale(start.values, factor=k)
        _write(name, source, e6_file(v), _with_provenance(
            {"schema": "epa-e6/1", "row": 7, "variant": v, "conventions": None, "knock_factor": k,
             "form": start.form, "values": vals, "frozen_sections_sha256": engines.frozen_sections_sha256(vals),
             "fit": None}, prov))
    print(f"e6 {name}: wrote {len(E6_VARIANTS)} files under {epa_freeze.CALIBRATION_DIR}/{name}/e6/")
    return {"variants": list(E6_VARIANTS), "form": fz["form"]}


# ======================================================================================================
# complete (PLAN.md 5.9, as F7, F8, E1, E3, F3, F5 amend it; WP3_INTERFACES.md 5.5.1)
# ======================================================================================================
# The two provisional knees every run before the K3 knee carries (amendment F7: a NaN knee ends the episode,
# and the table, the floor and the K3 trace must not move with it): the B58's typed 1123 K, epa_fit's
# provisional, and DESIGN 50 K above it, a second finite knee far enough to change every damage figure.
PROVISIONAL_KNEES = (float(epa_fit.PROVISIONAL_COMPLETION["k3"]["turb_knee_k"]),
                     float(epa_fit.PROVISIONAL_COMPLETION["k3"]["turb_knee_k"]) + 50.0)
# PLAN.md 5.9 item 1: the table re-measured at 60 settling steps.
REMEASURE_SETTLE = 60
# The completion fields measured after the freeze, which PLAN.md 5.9's finiteness assertion excludes until
# they are measured (amendment F7), by their path in dataclasses.asdict(plant).
COMPLETION_FIELDS = {"table": "car.deliverable_torque", "knee": "engine.damage.turb_knee_k",
                     "floor": "engine.loop.torque_floor_nm"}
# E6 rows 5 and 6's constants (the back-pressure law, plant.exhaust_backpressure_kpa; UA_PORT) and row 9's
# (the contract's list: conrod, IVC, EVO, t_head, port pickup, t_residual, cp_exh, the burn constants no
# stage fits, the flame terms, the Wiebe shape; and the rich slope from version 4), by engine record.
ROW5_FIELDS = (("cycle", "exh_bp_ratio"), ("cycle", "exh_bp_min_kpa"))
ROW6_FIELDS = (("cycle", "ua_port"),)
ROW9_FIELDS = (("geometry", "conrod"), ("geometry", "ivc_deg"), ("geometry", "evo_deg"), ("cycle", "t_head_k"),
               ("cycle", "port_pickup_k"), ("cycle", "t_residual_k"), ("cycle", "cp_exh"), ("cycle", "burn_res"),
               ("cycle", "delay_res"), ("cycle", "flame_lam"), ("cycle", "flame_width"), ("cycle", "flame_floor"),
               ("cycle", "wiebe_a"), ("cycle", "wiebe_m"), ("cycle", "ce_rich_slope"))
# Row 9's list is "the other ASSUMED cycle constants (conrod, IVC, EVO, ..., the flame terms ... among
# them)": the parenthesis names some of them, not all (WP3's second fix of 23 October 2026, on the contract
# review's finding that the residual-fraction law and n_poly were neither probed nor declared). So row 9
# probes ROW9_FIELDS (the names the text gives, the Wiebe shape among them as "a burn constant not fitted")
# and every other field of the engine's spec [geometry] and [cycle] labelled ASSUMED (row9_fields: the
# residual-fraction law fres_*, n_poly, and the Honda's octane), read off the labels, never retyped. A field
# labelled CORRELATION that the text does not name (the knock correlation knock_on, knock_p, knock_b) is not
# an ASSUMED constant, and is listed with that reason (row9_not_probed): the knock scale is row 7's.
ROW9_SPEC_LABEL = "ASSUMED"
ROW9_RECORDS = ("geometry", "cycle")
# Worth b on d (the contract's row 9: "report the error worth R1 and worth b"): d needs agents, and no EPA
# engine has one when the validation runs (decision 59), so it is never computable.
WORTH_B_WHY = ("d needs agents, and no EPA engine has one when the validation runs (the contract's E6, decision "
               "59): worth b on d is computable for no d row")


def row9_fields(name):
    """E6 row 9's (record, field) pairs for the engine `name`: ROW9_FIELDS, then every ASSUMED field of its
    spec's [geometry] and [cycle] not among them, in the spec's order (the module's note above)."""
    labels = epa_freeze.spec_labels(name)
    out = list(ROW9_FIELDS)
    have = {f for _r, f in out}
    for rec in ROW9_RECORDS:
        for k, lab in (labels.get(rec) or {}).items():
            if lab == ROW9_SPEC_LABEL and k not in have:
                out.append((rec, k))
                have.add(k)
    return tuple(out)


def row9_not_probed(name):
    """{field: why} for the spec's [geometry] and [cycle] fields labelled CORRELATION that row 9 does not
    probe (row9_fields)."""
    labels = epa_freeze.spec_labels(name)
    have = {f for _r, f in row9_fields(name)}
    return {k: "labelled CORRELATION, not ASSUMED: row 9 names the ASSUMED cycle constants; the knock scale "
               "knock_a is E6 row 7's" for rec in ROW9_RECORDS for k, lab in (labels.get(rec) or {}).items()
            if lab == "CORRELATION" and k not in have}
ANGLES = epa_stats.E6_ANGLE_FIELDS        # IVC and EVO, whose probes the contract states in crank degrees
# E6 row 4's housing constants (the contract's list), on the thermal record.
ROW4_FIELDS = ("c_turb", "ua_gas_turb", "ua_turb_amb")
# S1's names of the back-pressure law's two constants, as its report gives their sigma.
S1_SIGMA_NAMES = {"exh_bp_ratio": "ratio", "exh_bp_min_kpa": "floor_kpa"}


def _assert_finite(plant, *, excluded, step):
    """PLAN.md 5.9, amendment F7: every float of dataclasses.asdict(plant) finite before a step, except
    the named completion fields still to come (mistake 19: a value that could have come from a fallback,
    here derived.py's NaN under DERIVING_PARAMS=1)."""
    bad = []

    def walk(x, path):
        if path in excluded:
            return
        if isinstance(x, dict):
            for k, v in x.items():
                walk(v, f"{path}.{k}" if path else str(k))
        elif isinstance(x, (list, tuple)):
            for i, v in enumerate(x):
                walk(v, f"{path}[{i}]")
        elif isinstance(x, float) and not math.isfinite(x):
            bad.append(path)
    walk(dataclasses.asdict(plant), "")
    if bad:
        raise CompletionDefect(f"before {step}: non-finite plant fields {bad} (PLAN.md 5.9)")


def _completed(frozen_values, *, table, knee, floor):
    """The derived values of a candidate during the completion: the frozen sections and the completion
    values measured so far, provisional ones for the rest (WP3_INTERFACES.md 10, choice 21: the plant
    measured is the plant get() will build)."""
    v = {s: frozen_values[s] for s in engines.FROZEN_SECTIONS}
    v["deliverable_torque"] = [[int(r), float(t)] for r, t in table]
    v["k3"] = {"turb_knee_k": float(knee)}
    v["loop"] = {"torque_floor_nm": float(floor)}
    return v


def _plant(name, values):
    return engines.build_candidate(name, values)


def _same_tree(root):
    """Whether `root` is this file's own work tree, where engines.get reads its files."""
    return os.path.normcase(os.path.realpath(root)) == os.path.normcase(os.path.realpath(HERE))


def _completion_task(item):
    """One measurement of the completion, a function of a plant alone, so the ordered pool runs them side
    by side (picklable; WP3_INTERFACES.md 3.3: each in a worker whose audit is worker_init's)."""
    kind, plant, kw = item
    if kind == "table":
        return k3_knee.deliverable_table(plant, settle=kw["settle"])
    if kind == "floor":
        return k3_knee.torque_floor(plant, settle=kw["settle"])
    if kind == "delivery":
        run = k3_knee.locked_neutral_run(plant)
        return {"delivery": k3_knee.delivery(run, plant=plant, t_from_s=k3_knee.T_FROM_S).as_json(),
                "identity": k3_knee.neutral_identity(run, ecu=plant.engine.ecu).as_json()}
    if kind == "k3":
        return k3_knee.k3(plant, seconds=kw["seconds"], provisional=kw["provisional"])
    if kind == "coefficients":
        return epa_coefficients.coefficients(plant)
    if kind == "climb_cell":
        return epa_coefficients.climb_cell(plant)
    if kind == "cell_resolution":
        return epa_coefficients.climb_cell_resolution(plant)
    if kind == "peak":
        return float(k3_knee.baseline_trace(plant).t_turb_k.max() - 273.15)
    if kind == "damage":
        return k3_knee.damage_readings(plant)
    raise ValueError(f"no completion task {kind!r}")


def _tasks(items, jobs):
    """Every item through _completion_task in the ordered pool (epa_fit.ordered_map: results in
    submission order, each worker audited)."""
    return epa_fit.ordered_map(_completion_task, list(items), jobs=jobs, initializer=epa_fit.WORKER_INIT)


def slider_crank_angle(stroke_from_tdc_m, *, stroke_m, conrod_m):
    """The crank angle (deg from TDC, 0-180) at which the piston is `stroke_from_tdc_m` below TDC, the
    slider-crank x = r(1 - cos t) + l - sqrt(l^2 - r^2 sin^2 t), r the half stroke, l the rod, inverted by
    bisection (x rises monotonically from 0 at TDC to the stroke at BDC); None outside [0, stroke]. E6 row
    9's bracket from EPA's effective strokes (PLAN.md 5.9 item 6: "Honda effective strokes (slider-crank
    inverted)")."""
    r, l = 0.5 * stroke_m, conrod_m
    if not (0.0 <= stroke_from_tdc_m <= stroke_m) or l <= r:
        return None

    def x(t):
        return r * (1.0 - math.cos(t)) + l - math.sqrt(l * l - (r * math.sin(t)) ** 2)
    lo, hi = 0.0, math.pi
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if x(mid) < stroke_from_tdc_m:
            lo = mid
        else:
            hi = mid
    return math.degrees(0.5 * (lo + hi))


# E6 row 9's valve events from the Atkinson ratio and the two cam phases (defect D-1, found 24 October 2026 by
# the read-only defect hunt after Run 1's first pass, fixed 29 October 2026 on the defect route, WP3_INTERFACES.md
# 5.5.2 and PLAN.md 5.6). EPA's Atkinson ratio is the effective EXPANSION STROKE over the effective COMPRESSION
# STROKE, x(EVO) / x(IVC), x the slider-crank's piston travel from TDC, with IVC = IVC0 + the intake cam and EVO =
# EVO0 + the exhaust cam: on the Mazda's 199 calibration steady and Final rows that reading fits to rms 7.6e-16
# (max 2.4e-15) at one solution every one of 27 starts reached, the two cams nearly independent (corr 0.19);
# EPA's printed description (compression over expansion) gives rms 0.38, and a ratio of the two effective
# compression ratios rms 2.0e-3 (the hunt's scratch scripts atk.py and atk_cr.py; mistake 13). The fit is three
# unknowns -- IVC0, EVO0 and the rod over the half stroke -- on the rows that carry the ratio and both phases,
# least squares from every start of ATKINSON_STARTS, accepted only when it is EXACT: some start's largest
# |residual| below ATKINSON_EXACT, every exact start at one solution within ATKINSON_AGREE, the Jacobian there of
# full rank, and at least ATKINSON_MIN_ROWS distinct (intake, exhaust) cam pairs, so that exactness tests the
# reading (three unknowns on three rows always fit). Anything else gives no bracket, with the reason.
ATKINSON_EXACT = 1e-9               # DESIGN: a residual of the ratio, far above the 1e-15 the reading reaches
ATKINSON_AGREE = 1e-6               # DESIGN: deg on IVC0 and EVO0, relative on the rod over the half stroke
ATKINSON_MIN_ROWS = 4               # an over-determined fit of three unknowns
ATKINSON_STARTS = tuple((i, e, lam) for i in (-120.0, -90.0, -60.0) for e in (100.0, 130.0, 160.0)
                        for lam in (2.4, 3.6, 6.0))          # the hunt's 27 starts (rods 0.12, 0.18, 0.30 m / 50 mm)
ATKINSON_BOUNDS = ((-179.0, 1.0, 1.0 + 1e-6), (-1.0, 179.0, 40.0))     # IVC0, EVO0 deg aTDC firing; rod / half stroke
# the sign of each published cam channel on its event (epa_rows maps both intake spellings to cam_cad): a retard
# moves the event later, an advance earlier
CAM_SIGN = {"intake_cam_phase_cad_ret": 1.0, "intake_cam_phase_cad_adv": -1.0}
ATKINSON_CHANNELS = "epa_atkinson_ratio with the intake and exhaust cam phases"


def _travel(deg, lam):
    """The slider-crank's piston travel from TDC at crank angle `deg`, in half strokes: 1 - cos t + lam -
    sqrt(lam^2 - sin^2 t), lam the rod over the half stroke (slider_crank_angle's x / r)."""
    t = np.radians(deg)
    return 1.0 - np.cos(t) + lam - np.sqrt(lam * lam - np.sin(t) ** 2)


def atkinson_events(rows):
    """(fit, why): IVC0, EVO0 and the rod over the half stroke from EPA's Atkinson ratio and the two cam phases on
    `rows` (the module's note above: ratio = x(EVO0 + exhaust cam) / x(-(IVC0 + s intake cam)), s CAM_SIGN's), or
    (None, the reason no bracket follows). fit: {ivc0_deg, evo0_deg, rod_over_half_stroke, max_abs_residual, rows,
    distinct_cam_pairs, starts, starts_exact, intake_cam_sign, intake_cam_range_cad, exhaust_cam_range_cad}."""
    use = [r for r in rows if all(getattr(r, a, None) is not None and math.isfinite(float(getattr(r, a)))
                                  for a in ("atkinson_ratio", "cam_cad", "exhaust_cam_cad"))]
    if not use:
        return None, "no row carries the Atkinson ratio with both cam phases"
    chans = sorted({str(getattr(r, "cam_channel", None)) for r in use})
    if len(chans) != 1 or chans[0] not in CAM_SIGN:
        return None, (f"the intake cam channel {chans} has no sign on IVC (CAM_SIGN), so the ratio is not read")
    s = CAM_SIGN[chans[0]]
    cam = np.array([float(r.cam_cad) for r in use])
    exh = np.array([float(r.exhaust_cam_cad) for r in use])
    ratio = np.array([float(r.atkinson_ratio) for r in use])
    pairs = len({(float(a), float(b)) for a, b in zip(cam, exh)})
    if pairs < ATKINSON_MIN_ROWS:
        return None, (f"the rows that carry the Atkinson ratio and both cam phases give {pairs} distinct cam pair(s), "
                      f"fewer than {ATKINSON_MIN_ROWS}: three unknowns (IVC0, EVO0, the rod) on fewer rows always fit, "
                      "so an exact fit would not test the reading")

    def resid(p):
        with np.errstate(all="ignore"):
            r = _travel(p[1] + exh, p[2]) / _travel(-(p[0] + s * cam), p[2]) - ratio
        return np.where(np.isfinite(r), r, 1e3)
    sols = []
    for x0 in ATKINSON_STARTS:
        try:
            q = least_squares(resid, np.array(x0, dtype=float), bounds=ATKINSON_BOUNDS, method="trf", xtol=1e-15,
                              ftol=1e-15, gtol=1e-15, max_nfev=2000)
        except (ValueError, FloatingPointError):
            continue
        sols.append((float(np.max(np.abs(q.fun))), q))
    if not sols:
        return None, "no start of the Atkinson fit could be evaluated"
    exact = [(m, q) for m, q in sols if m < ATKINSON_EXACT]
    best = min(m for m, _ in sols)
    if not exact:
        return None, (f"the Atkinson ratio is not x(EVO0 + exhaust cam) / x(-(IVC0 + intake cam)) on these rows: no "
                      f"exact fit over {len(use)} rows (the least largest residual {best:.3g}, {len(sols)} starts)")
    m0, q0 = min(exact, key=lambda t: t[0])
    p0 = q0.x
    agree = all(abs(q.x[0] - p0[0]) <= ATKINSON_AGREE and abs(q.x[1] - p0[1]) <= ATKINSON_AGREE
                and abs(q.x[2] / p0[2] - 1.0) <= ATKINSON_AGREE for _m, q in exact)
    sv = np.linalg.svd(np.asarray(q0.jac, dtype=float), compute_uv=False)
    full = bool(sv.size == 3 and sv[-1] > 1e-10 * sv[0])
    if not (agree and full):
        return None, (f"the exact fits of the Atkinson ratio do not identify IVC0, EVO0 and the rod "
                      f"({len(exact)} exact starts {'agree' if agree else 'disagree'}; the Jacobian "
                      f"{'has' if full else 'lacks'} full rank)")
    return {"ivc0_deg": float(p0[0]), "evo0_deg": float(p0[1]), "rod_over_half_stroke": float(p0[2]),
            "max_abs_residual": float(m0), "rows": len(use), "distinct_cam_pairs": pairs,
            "starts": len(ATKINSON_STARTS), "starts_exact": len(exact), "intake_cam_channel": chans[0],
            "intake_cam_sign": s, "intake_cam_range_cad": [float(cam.min()), float(cam.max())],
            "exhaust_cam_range_cad": [float(exh.min()), float(exh.max())], "exact_below": ATKINSON_EXACT}, None


def valve_brackets(rows, *, geometry):
    """E6 row 9's brackets for IVC and EVO from EPA's calculated valve channels on the calibration rows
    (the contract: "the bracket EPA's calculated valve channels give, where one exists (the Honda's
    effective strokes, the Mazda's Atkinson ratio, the cam phases), with why each bracket that cannot be
    computed cannot"). {field: {"bracket": [lo, hi] deg aTDC firing or None, "rows": n, "rows_outside": n,
    "channel", "method" ("strokes", "atkinson" or None), "why_not_bracket": str or None}}, and under the
    Atkinson method its fit (atkinson_events) and the rod in metres at the plant's stroke. In order:
      - the effective strokes (the Honda): the effective compression stroke is the piston's travel from IVC
        to TDC, the effective expansion stroke from TDC to EVO, so IVC = -angle and EVO = +angle of the
        inverted slider-crank at the plant's stroke and rod;
      - the Atkinson ratio with both cam phases (the Mazda; defect D-1, 29 October 2026): the ratio is the
        effective expansion stroke over the effective compression stroke, x(EVO0 + exhaust cam) /
        x(-(IVC0 + intake cam)), so an exact fit of IVC0, EVO0 and the rod over the half stroke places both
        events, and the cams' ranges over the rows bracket them: IVC0 + the intake cam's [min, max], EVO0 +
        the exhaust cam's (atkinson_events, its acceptance rules in the note above). The docstring this
        replaces read the ratio as one of an effective expansion to an effective compression RATIO and the
        phases as shifts from a base nobody could recover, so that no event followed; both were wrong: the
        ratio's own rows recover the base timing exactly;
      - a cam phase alone (the Ford's Cell 9: the two phases, no ratio, strokes or overlap) is a shift from
        a base timing EPA does not publish: the phases bracket how far the event travels across the map,
        not where it is, so no bracket follows."""
    out = {}
    stroke, rod = float(geometry.stroke), float(geometry.conrod)
    atk_fit = None
    for field, attr, sign in (("ivc_deg", "eff_compression_stroke_mm", -1.0), ("evo_deg", "eff_expansion_stroke_mm", 1.0)):
        vals = [getattr(r, attr) for r in rows if getattr(r, attr, None) is not None]
        if vals:
            ang = [slider_crank_angle(v / 1000.0, stroke_m=stroke, conrod_m=rod) for v in vals]
            ok = [a for a in ang if a is not None]
            out[field] = {"bracket": sorted([sign * min(ok), sign * max(ok)]) if ok else None, "rows": len(ok),
                          "rows_outside": len(ang) - len(ok), "channel": attr, "method": "strokes" if ok else None,
                          "why_not_bracket": None if ok else "every row's effective stroke lies outside the stroke"}
            continue
        atk = any(getattr(r, "atkinson_ratio", None) is not None for r in rows)
        cam = any(getattr(r, "cam_cad", None) is not None or getattr(r, "exhaust_cam_cad", None) is not None
                  for r in rows)
        if atk:
            if atk_fit is None:
                atk_fit = atkinson_events(rows)
            fit, why_atk = atk_fit
            if fit is not None:
                if field == "ivc_deg":
                    ends = [fit["ivc0_deg"] + fit["intake_cam_sign"] * c for c in fit["intake_cam_range_cad"]]
                else:
                    ends = [fit["evo0_deg"] + c for c in fit["exhaust_cam_range_cad"]]
                out[field] = {"bracket": sorted(float(e) for e in ends), "rows": fit["rows"], "rows_outside": 0,
                              "channel": ATKINSON_CHANNELS, "method": "atkinson", "why_not_bracket": None,
                              "atkinson_fit": fit, "rod_m_at_plant_stroke": fit["rod_over_half_stroke"] * 0.5 * stroke}
                continue
            out[field] = {"bracket": None, "rows": 0, "rows_outside": 0, "channel": None, "method": None,
                          "why_not_bracket": why_atk}
            continue
        why = []
        if cam:
            why.append("a cam phase is a shift from a base timing EPA does not publish, and no Atkinson ratio or "
                       "effective stroke is published to recover it: the phases bracket how far the event travels "
                       "across the map, not where it is")
        if not why:
            why.append("no valve channel is published for this engine")
        out[field] = {"bracket": None, "rows": 0, "rows_outside": 0, "channel": None, "method": None,
                      "why_not_bracket": "; ".join(why)}
    return out


# DECISION 85 (Ghassan, 29 October 2026; results/VALIDATION_DECISIONS.md section H): an E6 probe whose response
# slope is below its numerical noise -- so the size that would move the housing by R1 (or d by b) is outside
# any physical range, as the first pass's exh_bp_min_kpa's 2.28e6 kPa -- is reported "not visible at R1" and
# probed at the contract's own fallback ("Where neither is computable, it is +-10 %"; +-10 crank degrees for
# IVC and EVO, row 9), and counted as excluded for that row with the reason (validate_epa's E6 rows count it,
# never judging its probe). The contract's fallback, not a rule of it (rule 0). The numerical noise is measured,
# not typed: the climb cell is a median over epa_coefficients.CLIMB_S, and a change smaller than the median's
# resolution (epa_coefficients.median_resolution: the gap to the next order statistic) may only reorder
# samples around it, so the noise of the probe's housing response is the housing equivalent of the gas's and
# the flow's resolutions at the frozen plant's climb (|f| x egt's + |dTh per ln mdot| x mdot's / mdot,
# numerical_noise_k), and a probe is visible only when its antisymmetric response |h(+) - h(-)| / 2 exceeds
# it. A constant the climb does not see at all (h 0 both ways) is not visible either. A bracket is a band, not a
# visibility probe, and is kept.
NOT_VISIBLE_AT_R1 = ("not visible at R1: the probe's response slope is below the climb cell's numerical noise, "
                     "so the change worth R1 is not computable and the probe is the contract's +-10 % fallback "
                     "(decision 85); counted as excluded for this row's level rows, with this reason")
NOISE_RULE = ("decision 85: the housing equivalent of the climb cell's median resolution over CLIMB_S at the "
              "frozen plant, |f| x the gas's + |dTh per unit ln mdot| x the flow's / the flow "
              "(epa_coefficients.climb_cell_resolution); a probe is visible when |h(+) - h(-)| / 2 exceeds it")


def numerical_noise_k(hs, resolution):
    """Decision 85's numerical noise of a probe's housing response, K: the housing equivalent of the climb cell's
    median resolution (`resolution`, epa_coefficients.climb_cell_resolution's record) with the engine's own f and
    G term `hs`, each channel's taken at its magnitude so that the two add (NOISE_RULE)."""
    return (abs(float(hs["f"])) * float(resolution["egt_resolution_k"])
            + abs(float(hs["dTh_per_unit_ln_mdot"])) * float(resolution["mdot_resolution_gps"]) / float(resolution["mdot"]))


def probe_sizes(base_cell, hs, cells, *, r1_k, rel, else_rel, else_cad, fields, brackets, v0, sigmas,
                noise_k=None):
    """E6 probe sizes (PLAN.md 5.9 item 6; the contract's E6, "the visibility probe is sized by its
    consequence"): for each (record, field) of `fields`, the housing equivalent of moving it by +-rel
    (epa_coefficients.housing_equivalent at the frozen climb cell, the engine's own f and G term `hs`, from
    the climb cells `cells[(field, +1)]` and `cells[(field, -1)]` against `base_cell`), its slope per unit
    of the constant, the change worth R1 (r1_k / |slope|), and the size used: the bracket where `brackets`
    gives one, else the change worth R1, else +-else_rel of the value (+-else_cad for IVC and EVO). `v0`
    {field: value}.

    LOAD-BEARING IS JUDGED AT THE CONSTANT'S BAND, NOT AT THE PROBE (WP3's second fix of 23 October 2026, on
    the contract review's finding): the contract's rule is "a constant whose band moves d by more than b,
    or the housing equivalent by more than R1, becomes a preregistered sensitivity row", and a probe sized
    by its consequence moves the housing equivalent by R1 by construction, so judging it there decided
    load_bearing by float rounding. The band is the bracket where one exists (its farther edge from the
    value, the size the probe moves the constant by), else the fit's standard uncertainty where `sigmas`
    ({field: sigma or None}) gives one (rows 5 and 6, the rich slope under form C); housing_change_k is
    |slope| x the band, and load_bearing whether it exceeds R1. A constant with neither has no band: an
    ASSUMED constant's +-10 % is a probe, not an uncertainty (the contract's E6), so load_bearing is None
    with its reason, and its worth R1 is reported. The probe's own housing change is reported beside it as
    probe_housing_change_k, never judged. worth_b is None, with WORTH_B_WHY.

    NOT VISIBLE AT R1 (decision 85, the note above): with `noise_k` (numerical_noise_k; None keeps the rule
    off, the visibility then None), a constant without a bracket whose antisymmetric response |h(+) - h(-)| / 2
    is at or below noise_k takes the fallback size, visible_at_r1 False, not_visible_at_r1 NOT_VISIBLE_AT_R1
    with its numbers, worth_r1 None with that reason, and counted_excluded True, which validate_epa reads to
    count the constant excluded for its row's level rows. Returns {field: record}."""
    out = {}
    for record, field in fields:
        val = float(v0[field])
        h = {}
        for sg in (1, -1):
            c = cells[(field, sg)]
            h[sg] = epa_coefficients.housing_equivalent(hs, c["egt"] - base_cell["egt"],
                                                        math.log(c["mdot"] / base_cell["mdot"]))
        step = rel * abs(val)
        slope = (h[1] - h[-1]) / (2.0 * step) if step > 0.0 else float("nan")
        worth = r1_k / abs(slope) if (math.isfinite(slope) and slope != 0.0) else None
        # decision 85: the probe's antisymmetric response against the climb cell's numerical noise
        response = abs(h[1] - h[-1]) / 2.0
        visible = None if noise_k is None else bool(math.isfinite(slope) and response > float(noise_k))
        hidden = None
        b = (brackets or {}).get(field)
        if b and b.get("bracket"):
            lo, hi = b["bracket"]
            size, method = max(abs(lo - val), abs(hi - val)), "bracket"
        elif visible is False:
            size, method = (else_cad if field in ANGLES else else_rel * abs(val)), "fallback"
            hidden = (f"{NOT_VISIBLE_AT_R1} (|h(+) - h(-)|/2 = {response:.3g} K at +-{rel * 100:g} %, the noise "
                      f"{float(noise_k):.3g} K)")
            worth = None
        elif worth is not None:
            size, method = worth, "probe"
        else:
            size, method = (else_cad if field in ANGLES else else_rel * abs(val)), "fallback"
        if method == "bracket":
            band = {"size": float(size), "source": "the bracket EPA's valve channels give (its farther edge from "
                                                   "the value)"}
        elif sigmas.get(field) is not None:
            band = {"size": float(sigmas[field]), "source": "the fit's standard uncertainty"}
        else:
            band = None
        finite = math.isfinite(slope)
        hc = abs(slope) * band["size"] if (band is not None and finite) else None
        why = None if hc is not None else ("no band (ASSUMED): worth R1 reported" if band is None
                                           else "the housing equivalent's slope is not finite")
        out[field] = {"record": record, "value": val, "method": method, "size": float(size),
                      "why_not_bracket": None if method == "bracket" else (
                          (b or {}).get("why_not_bracket") or "EPA publishes no channel that brackets it"),
                      "housing_eq_k": {"+": h[1], "-": h[-1]}, "slope_k_per_unit": slope if finite else None,
                      "worth_r1": worth, "worth_b": None, "worth_b_why": WORTH_B_WHY, "band": band,
                      "housing_change_k": hc, "probe_housing_change_k": abs(slope) * size if finite else None,
                      "load_bearing": None if hc is None else bool(hc > r1_k), "load_bearing_why": why,
                      "response_k": response, "numerical_noise_k": None if noise_k is None else float(noise_k),
                      "visible_at_r1": visible, "not_visible_at_r1": hidden,
                      "worth_r1_why": hidden, "counted_excluded": hidden is not None,
                      "counted_excluded_why": hidden}
    return out


def _sigmas(fit_rec):
    """E6 rows 5, 6 and 9's sigmas from the chosen form's fit (fit_<form>.json): S1's sigma of the law's two
    constants (None where S1 gives none: amendment D10), S4's standard deviation of UA_PORT from its
    covariance (None without one), and S5's standard uncertainty of the rich slope (None without form C or
    without information). Returns (row 5's, row 6's, the slope's)."""
    s1 = (fit_rec["stages"].get("S1") or {}).get("report", {}).get("sigma") or {}
    row5 = {S1_SIGMA_NAMES[f]: (None if s1.get(S1_SIGMA_NAMES[f]) is None else float(s1[S1_SIGMA_NAMES[f]]))
            for _rec, f in ROW5_FIELDS}
    rep = (fit_rec["stages"].get("S4") or {}).get("report", {})
    ua = None
    if rep.get("covariance") is not None and "ua_port" in list(rep.get("params") or ()):
        i = list(rep["params"]).index("ua_port")
        var = float(rep["covariance"][i][i])
        ua = math.sqrt(var) if var >= 0.0 else None
    s5 = (fit_rec["stages"].get("S5") or {}).get("report", {}).get("sigma")
    return row5, {"ua_port": ua}, (None if s5 is None else float(s5))


def _variant_plant(plant, conventions):
    """A refit variant's plant in use (amendment E2; the contract's E6 rows 2 and 3): its refitted sections
    on the plant's own fuel moved as the variant's conventions move it -- row 2's AFR_st "in the
    calibration air and the plant fuel together", row 3's LHV "in the cycle's heat release and the thermal
    network's fuel heat together, through engines.with_fuel" (epa_fit.perturbed's fuel record) -- so the
    model in use the variant reports is the variant's (WP3's fix of 23 October 2026, on the test review's
    finding that rows 2 and 3 ran the frozen plant's fuel). Rows 1 and 7 move no fuel: the plant as built.
    `conventions` is the e6 file's (a dict, or None for row 7)."""
    if not conventions:
        return plant
    for field in ("afr_st", "lhv_j_per_kg"):
        if conventions.get(field) is not None:
            plant = epa_fit.perturbed(plant, record="fuel", field=field, value=float(conventions[field]))
    return plant


def _in_use(plant, point, *, t_amb_c, frozen_cell):
    """How far the model in use moves under a refit variant (amendment E2), at the frozen plant's climb
    cell inputs (the loop not re-closed, so the constants' own effect is read): the hot TIT at lambda 1,
    the gas, the air and exhaust flows, the housing's tau and its equivalent change against the frozen
    plant's, the heat release per gram of fuel (the fuel's LHV, which engines.with_fuel moves in the cycle
    and the network together), the coolant's and the oil's fuel-heat inputs (thermal.py: q_fuel x
    frac_fuel_to_coolant, x frac_fuel_to_oil)."""
    p = point
    at = epa_coefficients.cyc(plant, p["rpm"], p["map"], p["iat"], p["ect"], p["spark"], p["lam"])
    at1 = epa_coefficients.cyc(plant, p["rpm"], p["map"], p["iat"], p["ect"], p["spark"], 1.0)
    hs = epa_coefficients.housing(plant, at["egt"], at["mdot"], t_amb_c=t_amb_c)
    th, fuel = plant.engine.thermal, plant.engine.fuel
    q = at["fuel"] * 1e-3 * th.fuel_lhv_j_per_kg
    out = {"hot_tit_at_lambda1_c": at1["egt"], "egt_c": at["egt"], "air_gps": at["mdot"] - at["fuel"],
           "exhaust_gps": at["mdot"], "fuel_gps": at["fuel"], "tau_s": hs["tau_s"],
           "heat_per_gram_j": fuel.lhv_j_per_kg * 1e-3, "coolant_heat_w": q * th.frac_fuel_to_coolant,
           "oil_heat_w": q * th.frac_fuel_to_oil}
    if frozen_cell is not None:
        out["housing_eq_k"] = epa_coefficients.housing_equivalent(
            frozen_cell["hs"], at["egt"] - frozen_cell["egt"], math.log(at["mdot"] / frozen_cell["mdot"]))
    return out


def complete(name, *, source, jobs):
    """PLAN.md 5.9 items 1-10 in a fresh process with DERIVING_PARAMS=1 set before any project import
    (derived.py; the command line sets it), on build_candidate plants built from the frozen sections and
    the completion values measured so far (WP3_INTERFACES.md 10, choice 21). Requires the five e6 files;
    writes the derived file's completion sections and complete.json (7.2). Every number goes to
    complete.json; nothing is printed but steps and paths. Refused after an audited defect (_audit_guard),
    without C8's proof (poison.json) and once the held-out run has started."""
    _jobs(jobs)
    if os.environ.get("DERIVING_PARAMS") != "1":
        raise Refusal("complete runs in a fresh process with DERIVING_PARAMS=1 set before any project import "
                      "(derived.py; the command line sets it)")
    _held_out_guard(name, source, "the completion comes before the held-out run")
    for v in E6_VARIANTS:
        _require(name, source, e6_file(v), "the completion follows the refit variants (PLAN.md WP4)")
    _forbid(name, source, COMPLETE, "the completion is written once; a re-run is the defect route")
    _audit_guard(name, source)
    _require(name, source, FREEZE, "the completion completes the frozen fit (PLAN.md 5.9)")
    _frozen_code_guard(name, source, "the completion runs on the code and the plant the freeze ran on (C10)")
    _versions_guard(_freeze_versions(name, source))
    root = source.root
    fz, fit_rec, frozen = _frozen_fit(name, source=source)
    _poison_guard(name, source, frozen.frozen_sections_sha256)
    dpath = epa_freeze.derived_path(name, root=root)
    file_values = epa_freeze.read_json(dpath, root=root)
    # the derived file's frozen sections against freeze.json's hash, before any measurement (check_frozen);
    # freeze.json's is the frozen fit's (_frozen_fit checks the two equal), so no second comparison is made
    # (WP3's second fix of 23 October 2026, on the test review's finding that it could never fire alone)
    epa_freeze.check_frozen(name, file_values, root=root)
    view, yield_ = _load(name, source=source)
    prov = epa_freeze.provenance(name, source=source, view=view)
    seal_now()           # every measurement reads the plant, the yield and the view it is given (Audit.sealed)
    bands = epa_stats.e6_band_values(view.perturbations_e6)
    etas = epa_stats.row10_etas(view.perturbations_e6)
    fv = frozen.values
    asserted = []
    ka, kb = PROVISIONAL_KNEES

    def check(plant, step, still):
        _assert_finite(plant, excluded={COMPLETION_FIELDS[k] for k in still}, step=step)
        asserted.append({"step": step, "excluded": sorted(COMPLETION_FIELDS[k] for k in still)})

    # (1) the deliverable-torque table, and the F7 control's table at the second knee
    p0a = _plant(name, _completed(fv, table=(), knee=ka, floor=0.0))
    p0b = _plant(name, _completed(fv, table=(), knee=kb, floor=0.0))
    check(p0a, "1 table", ("table", "knee", "floor"))
    settle = int(p0a.car.table_settle)
    tab_a, tab_b, tab_60 = _tasks([("table", p0a, {"settle": settle}), ("table", p0b, {"settle": settle}),
                                   ("table", p0a, {"settle": REMEASURE_SETTLE})], jobs)
    table = [list(x) for x in tab_a.table]
    rpm_t = np.array([r for r, _ in tab_a.table], dtype=float)
    nm_t = np.array([t for _, t in tab_a.table], dtype=float)
    wot = [{"line": r.line, "key": [r.table, int(r.source_row)], "initial_torque_nm": float(r.torque_nm),
            "model_nm": float(np.interp(r.speed_rpm, rpm_t, nm_t)), "label": "transient"}
           for r in yield_.rows if type(r) is epa_rows.InitialRow]
    print(f"complete {name}: (1) the deliverable-torque table, {len(table)} speeds")
    # (2) the torque floor, and its F7 twin at the second knee
    p1a = _plant(name, _completed(fv, table=tab_a.table, knee=ka, floor=0.0))
    p1b = _plant(name, _completed(fv, table=tab_a.table, knee=kb, floor=0.0))
    check(p1a, "2 floor", ("knee", "floor"))
    fl_a, fl_b = _tasks([("floor", p1a, {"settle": settle}), ("floor", p1b, {"settle": settle})], jobs)
    f7 = (tab_a.raw == tab_b.raw and tab_a.table == tab_b.table and fl_a.closed_nm == fl_b.closed_nm
          and fl_a.nm == fl_b.nm)
    if not f7:
        raise CompletionDefect("the table or the floor moved with the provisional knee (amendment F7)")
    print(f"complete {name}: (2) the torque floor; the F7 control holds")
    # (3) the delivery check and the neutral-action identity; (4) the K3 knee, at eta 0.86 and 0.98 too
    p2 = _plant(name, _completed(fv, table=tab_a.table, knee=ka, floor=fl_a.nm))
    check(p2, "3 delivery and 4 K3", ("knee",))
    seconds = int(view.k3_seconds)
    eta_plants = [k3_knee.with_driveline_eff(p2, float(e)) for e in etas]
    out34 = _tasks([("delivery", p2, {})] + [("delivery", p, {}) for p in eta_plants]
                   + [("k3", p2, {"seconds": seconds, "provisional": PROVISIONAL_KNEES})]
                   + [("k3", p, {"seconds": seconds, "provisional": PROVISIONAL_KNEES}) for p in eta_plants], jobs)
    deliv, deliv_eta = out34[0], out34[1:1 + len(etas)]
    kn, kn_eta = out34[1 + len(etas)], out34[2 + len(etas):]
    for d in [deliv] + list(deliv_eta):
        idn = d["identity"]
        if not (idn["max_abs_dlam"] == 0.0 and idn["max_abs_dspark"] == 0.0 and idn["contacts_lam"] == 0
                and idn["contacts_spark"] == 0 and idn["bounds_are_python_floats"]):
            raise CompletionDefect("the neutral-action identity does not hold (decision 39(b); MD section 7: a "
                                   "coding defect)")
    for k in [kn] + list(kn_eta):
        if not k.second_knee_identical:
            raise CompletionDefect("the K3 trace moved with the provisional knee (PLAN.md 5.9 item 4)")
    print(f"complete {name}: (3) the delivery check and the identity; (4) the K3 knee")
    # (5)-(8): the final plant's coefficients, the E6 probes, row 4 and row 7
    values = _completed(fv, table=tab_a.table, knee=kn.knee_k, floor=fl_a.nm)
    pf = _plant(name, values)
    check(pf, "5-10 the coefficients, E6 and the dump", ())
    grid = epa_fit.synthetic_grid(pf)
    if not epa_fit.retag_identity(pf, grid=grid, dtheta=DTHETA):
        raise CompletionDefect("the rich slope's retag is not the engine at its own slope (HANDOFFS.md WP3 item 3)")
    rel = bands["else_rel"]
    row9 = row9_fields(name)
    probe_fields = ROW5_FIELDS + ROW6_FIELDS + row9
    v0 = {f: float(getattr(getattr(pf.engine, rec), f)) for rec, f in probe_fields}
    items = [("coefficients", pf, {})]
    for rec, f in probe_fields:
        for sg in (1, -1):
            # +-rel of the value's size, so the +1 cell lies above it whatever its sign (IVC near -140 deg;
            # WP3's fix of 23 October 2026: v0 x (1 + rel) put it below), the step probe_sizes divides by
            val = v0[f] + sg * rel * abs(v0[f])
            p = (epa_fit.with_rich_slope_probe(pf, slope=val) if f == "ce_rich_slope"
                 else epa_fit.perturbed(pf, record=rec, field=f, value=val))
            items.append(("climb_cell", p, {}))
    r4f = bands["row4_factors"]
    for f in ROW4_FIELDS:
        for fac in r4f:
            items.append(("peak", epa_fit.perturbed(pf, record="thermal", field=f,
                                                    value=float(getattr(pf.engine.thermal, f)) * fac), {}))
    items.append(("peak", pf, {}))
    ki = bands["row7_ki"]
    r7 = [("1.00", pf)] + [(f"{k:.2f}", _plant(name, {**values, **epa_fit.knock_rescale(fv, factor=k)})) for k in ki]
    items += [("damage", p, {}) for _, p in r7]
    # decision 85: the frozen plant's climb cell's numerical resolution, the probes' noise floor (last in the pool)
    items.append(("cell_resolution", pf, {}))
    res = _tasks(items, jobs)
    coef = res[0]
    base_cell, hs = coef["climb"]["point"], coef["climb"]["housing"]
    cells, i = {}, 1
    for _rec, f in probe_fields:
        for sg in (1, -1):
            cells[(f, sg)] = res[i]
            i += 1
    peaks = res[i:i + len(ROW4_FIELDS) * len(r4f) + 1]
    i += len(ROW4_FIELDS) * len(r4f) + 1
    damages = res[i:-1]
    cell_res = res[-1]
    r1 = float(view.r1_housing_k)
    rows_cal = epa_fit.cal_rows(yield_)
    brackets = valve_brackets(rows_cal, geometry=pf.engine.geometry)
    sig5, sig6, sig_slope = _sigmas(fit_rec)
    form_c = "C" in frozen.form.split("+")
    # each constant's band where the fit gives one (probe_sizes judges load-bearing there): rows 5 and 6's
    # sigmas, and the rich slope's under form C, where it is fitted
    sigmas = {f: sig5[S1_SIGMA_NAMES[f]] for _r, f in ROW5_FIELDS}
    sigmas.update(sig6)
    sigmas["ce_rich_slope"] = sig_slope if form_c else None
    # decision 85: the noise floor is the frozen climb cell's own (its medians are coefficients' climb point, checked
    # equal, so the resolution is the base cell's and never a fallback's: mistake 19)
    if (float(cell_res["egt"]), float(cell_res["mdot"])) != (float(base_cell["egt"]), float(base_cell["mdot"])):
        raise CompletionDefect("the climb cell's resolution was not measured on the climb the coefficients read "
                               "(decision 85)")
    noise = numerical_noise_k(hs, cell_res)
    sizes = probe_sizes(base_cell, hs, cells, r1_k=r1, rel=rel, else_rel=bands["else_rel"],
                        else_cad=bands["else_cad"], fields=probe_fields, brackets=brackets, v0=v0, sigmas=sigmas,
                        noise_k=noise)
    e6_probes = {
        "d_rows": f"+-{bands['d_probe_rel'] * 100:g} % (d needs agents; the contract's E6, decision 59)",
        "d_probe_rel": bands["d_probe_rel"], "probe_rel": rel, "r1_housing_k": r1,
        "climb_cell": {"point": base_cell, "housing": hs},
        "numerical_noise": {"housing_k": noise, "egt_resolution_k": cell_res["egt_resolution_k"],
                            "mdot_resolution_gps": cell_res["mdot_resolution_gps"], "samples": cell_res["samples"],
                            "rule": NOISE_RULE},
        "not_visible_at_r1": sorted(f for f, v in sizes.items() if v["visible_at_r1"] is False),
        "row5": {"sigma": sig5, "probe": {f: sizes[f]["size"] for _r, f in ROW5_FIELDS},
                 "housing_change_k": {f: sizes[f]["housing_change_k"] for _r, f in ROW5_FIELDS},
                 "detail": {f: sizes[f] for _r, f in ROW5_FIELDS}},
        "row6": {"sigma": sig6, "probe": {f: sizes[f]["size"] for _r, f in ROW6_FIELDS},
                 "housing_change_k": {f: sizes[f]["housing_change_k"] for _r, f in ROW6_FIELDS},
                 "detail": {f: sizes[f] for _r, f in ROW6_FIELDS}},
        # the rich slope under form C, where it is fitted: its fit's standard uncertainty beside the probe
        # (version 4's row 9: "+- its fit's standard uncertainty (reported) and the visibility probe"), from
        # S5's report (epa_fit.s5_rich_slope's sigma; WP3's fix of 23 October 2026)
        "row9": {f: dict(sizes[f], **({"sigma": sig_slope, "sigma_why": None if sig_slope is not None else
                                       "S5 gives no standard uncertainty (no enriched row, or no information)"}
                                      if (f == "ce_rich_slope" and form_c) else {}))
                 for _r, f in row9},
        "row9_not_probed": row9_not_probed(name),
        "brackets": brackets}
    th = pf.engine.thermal
    e6_row4 = {"frozen": {"tau_s": hs["tau_s"], "peak_c": peaks[-1]}}
    j = 0
    for f in ROW4_FIELDS:
        e6_row4[f] = {}
        for fac in r4f:
            pp = epa_fit.perturbed(pf, record="thermal", field=f, value=float(getattr(th, f)) * fac)
            e6_row4[f][f"x{fac:g}"] = {"tau_s": epa_coefficients.housing(pp, base_cell["egt"], base_cell["mdot"],
                                                                        t_amb_c=epa_coefficients.T_AMB_C)["tau_s"],
                                      "peak_c": peaks[j]}
            j += 1
    e6_row7 = {key: d for (key, _p), d in zip(r7, damages)}
    print(f"complete {name}: (5) the coefficients; (6) {len(sizes)} E6 probes; (7) row 4; (8) row 7")
    # (9) row 13's variants, handed to the preregistration
    ecu = pf.engine.ecu
    width = ecu.enr_dwell_hi - ecu.enr_dwell_lo
    e6_row13 = {}
    for g in bands["row13_dwell_s"]:
        new = dataclasses.replace(pf.engine, ecu=dataclasses.replace(ecu, enr_dwell_lo=float(g),
                                                                     enr_dwell_hi=float(g) + width))
        e6_row13[f"dwell_{g:g}s"] = {"ecu": {"enr_dwell_lo": new.ecu.enr_dwell_lo, "enr_dwell_hi": new.ecu.enr_dwell_hi},
                                     "builds": True}
    e6_row13["rule"] = ("the enrichment ramp moved whole so that it starts at the gate, its width the engine's "
                        "(enr_dwell_hi - enr_dwell_lo), each variant built through engines.Engine's invariants")
    # the refit variants in use (amendment E2), at the frozen climb cell
    frozen_cell = {"egt": base_cell["egt"], "mdot": base_cell["mdot"], "hs": hs}
    e6_in_use = {"frozen": _in_use(pf, base_cell, t_amb_c=epa_coefficients.T_AMB_C, frozen_cell=frozen_cell)}
    e6_files = {}
    for v in E6_VARIANTS:
        f = _read(name, source, e6_file(v))
        vals = {**{s: f["values"][s] for s in engines.FROZEN_SECTIONS},
                **{s: values[s] for s in epa_freeze.COMPLETION_SECTIONS}}
        if engines.frozen_sections_sha256({s: vals[s] for s in engines.FROZEN_SECTIONS}) != f["frozen_sections_sha256"]:
            raise CompletionDefect(f"{e6_file(v)}'s frozen sections are not its own hash")
        e6_in_use[v] = _in_use(_variant_plant(_plant(name, vals), f.get("conventions")), base_cell,
                               t_amb_c=epa_coefficients.T_AMB_C, frozen_cell=frozen_cell)
        e6_files[f"{epa_freeze.CALIBRATION_DIR}/{name}/{e6_file(v)}"] = epa_freeze.file_sha_text(
            _p(name, source, e6_file(v)), root=root)
    for key, v in (("0.90", "7_090"), ("1.10", "7_110")):
        e6_in_use[v]["knock_share"] = e6_row7[key]["knock_share"]
    e6_in_use["frozen"]["knock_share"] = e6_row7["1.00"]["knock_share"]
    # (10) the final derived file, the frozen sections asserted unchanged, the plant get() builds, the dump
    final = epa_freeze.with_completion(file_values, deliverable_torque=[[int(r), float(t)] for r, t in tab_a.table],
                                       turb_knee_k=float(kn.knee_k), torque_floor_nm=float(fl_a.nm))
    rec_d = epa_freeze.write_derived(name, final, allow_defect=None, root=root)
    epa_freeze.check_frozen(name, final, root=root)
    epa_freeze.check_derived_file(name, root=root)
    built = _plant(name, {k: v for k, v in epa_freeze.read_json(dpath, root=root).items() if not k.startswith("_")})
    if _same_tree(root):
        # engines.get reads the specs and the derived file beside engines.py: the plant get() builds is the
        # file's only in this tree (a test's temporary root holds its own copy, which build_candidate reads
        # through the same constructor, mistake 10)
        built = engines.get(name)
    if engines.engine_sha(built) != engines.engine_sha(pf):
        raise CompletionDefect("the plant built from the final file is not the plant the completion measured "
                               "(WP3_INTERFACES.md 10, choice 21)")
    dump = epa_freeze.frozen_plant_dump(built)
    rec = {"schema": "epa-complete/1", "frozen_sections_sha256": frozen.frozen_sections_sha256,
           "deliverable_torque": {"table": table, "grid": {"lo": int(pf.car.table_rpms[0]), "hi": int(pf.car.table_rpms[-1]),
                                                           "step": int(pf.car.table_rpms[1] - pf.car.table_rpms[0])},
                                  "settle_steps": settle,
                                  "remeasured_60_max_abs_diff_nm": float(max(abs(a[1] - b[1]) for a, b in
                                                                             zip(tab_a.raw, tab_60.raw))),
                                  "knock_flag_duty": tab_a.knock_flag_duty, "knock_flag_duty_60": tab_60.knock_flag_duty,
                                  "wot_comparison": wot},
           "torque_floor": {"nm": fl_a.nm, "rpm": fl_a.rpm, "t_amb_k": fl_a.t_amb_k, "rule": fl_a.rule,
                            "extrapolation": fl_a.extrapolation, "closed_nm": fl_a.closed_nm},
           "delivery": dict(deliv["delivery"], identity=deliv["identity"],
                            eta={f"{e:.2f}": dict(d["delivery"], identity=d["identity"]) for e, d in zip(etas, deliv_eta)},
                            provisional_knee_k=ka),
           "k3": {"seconds": kn.seconds, "knee_k": kn.knee_k, "time_above_knee_s": kn.time_above_knee_s,
                  "trace_sha256": kn.trace_sha256, "second_knee_identical": kn.second_knee_identical,
                  "provisional_knees_k": list(PROVISIONAL_KNEES),
                  "knee_k_at_eta": {f"{e:.2f}": k.knee_k for e, k in zip(etas, kn_eta)}},
           "f7_table_and_floor_identical_under_two_knees": bool(f7),
           "coefficients": coef, "e6_probes": e6_probes, "e6_row4": e6_row4, "e6_row7": e6_row7,
           "e6_row13": e6_row13, "e6_in_use": e6_in_use, "dump": dump.as_json(), "derived": rec_d.as_json(),
           "engine_sha": engines.engine_sha(built), "e6_files": e6_files,
           "finiteness": {"asserted_before": asserted, "excluded_fields": dict(COMPLETION_FIELDS)}}
    _write(name, source, COMPLETE, _with_provenance(epa_fit.json_safe(rec), prov))
    print(f"complete {name}: (9) row 13; (10) the dump and the final derived file; wrote "
          f"{epa_freeze.CALIBRATION_DIR}/{name}/{COMPLETE}")
    return {"steps": [a["step"] for a in asserted]}


# ======================================================================================================
# check (PLAN.md 6.1; amendment C11)
# ======================================================================================================
def _rerun_files(name, source):
    folder = _dir(name, source)
    ks = sorted(int(f[len("in_sample_rerun"):-len(".json")]) for f in os.listdir(folder)
                if f.startswith("in_sample_rerun") and f.endswith(".json") and f[len("in_sample_rerun"):-len(".json")].isdigit())
    return [f"in_sample_rerun{k}.json" for k in ks]


def recompute_in_sample(name, *, source, jobs, record, view, yield_):
    """The in-sample stage recomputed in memory from the records (PLAN.md 6.1): every form `record` (an
    in_sample.json) names, its frozen sections from its fit_<form>.json (hash checked), each through
    epa_fit.in_sample_for -- the function the ladder judged with -- then epa_fit.ladder_choice and
    in_sample_body, the one definition fit wrote. `view` and `yield_` are loaded by the caller before its
    audit is sealed (check). Returns the body (no provenance)."""
    ins = {}
    for form in record["forms"]:
        rec = _read(name, source, fit_file(form))
        values = {s: rec["values"][s] for s in engines.FROZEN_SECTIONS}
        sha = engines.frozen_sections_sha256(values)
        if sha != rec["frozen_sections_sha256"]:
            raise CompletionDefect(f"{fit_file(form)}'s frozen sections are not its own hash")
        ff = epa_fit.FormFit(engine=name, form=form, stages={}, values=values, frozen_sections_sha256=sha, flags=())
        ins[form] = epa_fit.in_sample_for(name, ff, yield_, view=view, jobs=jobs, dtheta=DTHETA)
    chosen, reason = epa_fit.ladder_choice(ins)
    return in_sample_body(ins, chosen=chosen, reason=reason)


def check(name, *, source, jobs, defect):
    """The in-sample stage recomputed in memory and compared byte for byte with in_sample.json (or the
    latest in_sample_rerun<k>.json), and the frozen sections of the derived file with freeze.json's and
    the chosen fit's (PLAN.md 6.1; validate_epa.arm runs it as a subprocess and requires exit 0). Returns
    True when both hold. On the defect route (amendment C11: an epa_stats defect found after the held-out
    run), the recomputed stage is written as in_sample_rerun<k>.json beside the old one, with a defects.json
    entry, and nothing is refitted. Requires complete.json; refused after an audited defect (_audit_guard);
    writes run.json only (and the re-run file). A comparison that fails raises CheckFailed, which invoke
    records as a mismatch (EXIT_MISMATCH), apart from every refusal."""
    _jobs(jobs)
    _require(name, source, COMPLETE, "check runs after the completion (PLAN.md WP4)")
    _audit_guard(name, source)
    _versions_guard(_freeze_versions(name, source))
    fz, _rec, frozen = _frozen_fit(name, source=source)
    values = epa_freeze.read_json(epa_freeze.derived_path(name, root=source.root), root=source.root)
    # against freeze.json's hash, which _frozen_fit has shown is the chosen fit's: one comparison (WP3's second
    # fix of 23 October 2026, on the test review's finding that the second could never fire alone)
    epa_freeze.check_frozen(name, values, root=source.root)
    view = epa_rows.calibration_contract(name, source=source)
    if view.contract_sha_text != fz["contract"]["json_sha_text"]:
        raise Refusal("the contract is not the one freeze.json records")
    reruns = _rerun_files(name, source)
    target_name = reruns[-1] if reruns else IN_SAMPLE
    target = _read(name, source, target_name)
    yield_ = epa_rows.calibration_rows(name, source=source)
    prov = None if defect is None else epa_freeze.provenance(name, source=source, view=view)
    seal_now()           # the recompute reads the yield and the view it is given (Audit.sealed)
    body = recompute_in_sample(name, source=source, jobs=jobs, record=target, view=view, yield_=yield_)
    if defect is not None:
        try:
            epa_freeze.check_defect(defect, root=source.root)
        except (epa_freeze.FreezeRefusal, TypeError, ValueError) as exc:
            raise Refusal(f"the defect route's authority is refused: {exc}") from None
        k = len(reruns) + 1
        out = _with_provenance(body, prov)
        out["rerun"] = {"k": k, "reason": defect.reason, "fix_commit": defect.fix_commit, "replaces": target_name}
        _write(name, source, f"in_sample_rerun{k}.json", out)
        epa_freeze.append_defect(name, {"k": len(_defects(name, source)) + 1,
                                        "run_invocation": _next_invocation(name, source),
                                        "found_by": "calibrate_epa.py check --defect (amendment C11)",
                                        "assertion": defect.reason, "fix_commit": defect.fix_commit,
                                        "previous_run": target_name}, root=source.root)
        print(f"check {name}: wrote in_sample_rerun{k}.json beside {target_name}; nothing refitted (C11)")
        return {"same": None, "rerun": k}
    want = {k: v for k, v in target.items() if k not in ("provenance", "rerun")}
    same = _canon(body) == _canon(want)
    print(f"check {name}: the in-sample stage is {'given back byte for byte' if same else 'NOT given back'} "
          f"({target_name}); the frozen sections are freeze.json's")
    if not same:
        raise CheckFailed(f"the in-sample stage recomputed is not {target_name}")
    return {"same": True, "compared": target_name}


class CheckFailed(Refusal):
    """check's comparison failed: the in-sample stage is not given back byte for byte. invoke records it as
    a mismatch and exits EXIT_MISMATCH, so that validate_epa.arm tells it from a refusal or a crash."""


def _defects(name, source):
    return _read(name, source, epa_freeze.DEFECTS) if _exists(name, source, epa_freeze.DEFECTS) else []


# ======================================================================================================
# The command line
# ======================================================================================================
def _body(args, source):
    name = args.engine
    if args.subcommand == "dry-load":
        return lambda: dry_load(name, source=source, out=args.out)
    jobs = args.jobs
    if args.subcommand == "t0":
        return lambda: t0(name, source=source, jobs=jobs, defect=_defect_route(args.defect, args.fix_commit))
    if args.subcommand == "fit":
        return lambda: fit(name, source=source, jobs=jobs, defect=_defect_route(args.defect, args.fix_commit))
    if args.subcommand == "poison":
        return lambda: poison(name, source=source, jobs=jobs, scratch=args.scratch, full=bool(args.full))
    if args.subcommand == "e6":
        return lambda: e6(name, source=source, jobs=jobs)
    if args.subcommand == "complete":
        return lambda: complete(name, source=source, jobs=jobs)
    if args.subcommand == "check":
        return lambda: check(name, source=source, jobs=jobs, defect=_defect_route(args.defect, args.fix_commit))
    raise ValueError(args.subcommand)


def main(args, *, argv):
    """The command line after _prelude: the Run 1 gate first for the subcommands it holds (gated; it writes
    nothing), then the subcommand under invoke, which records it in run.json. Returns the exit code. On the
    waiting path the audit's record is checked to hold no table of the engine and no epa_engine.json: a gate
    moved after the loader would show there (WP3's fix of 23 October 2026), and is a defect."""
    source = epa_rows.Source.repository()
    if args.engine not in epa_rows.TABLES:
        print(f"calibrate_epa.py: --engine must be one of {sorted(epa_rows.TABLES)}, not {args.engine!r} (mistake 1)")
        return EXIT_REFUSED
    try:
        waits = gated(args.subcommand, args.engine, source=source) and run1_waits(
            source=source, environ=os.environ, engine=args.engine)[0]
    except epa_rows.LoaderStop as exc:
        print(f"calibrate_epa.py {args.subcommand} --engine {args.engine}: the contract's guards stop: {exc}")
        return EXIT_REFUSED
    if waits:
        return wait_exit(args.subcommand, args.engine, source=source)
    scratch = getattr(args, "out", None) or getattr(args, "scratch", None)
    why = scratch_problem(scratch, source.root)
    if why is not None and args.subcommand == "dry-load":
        # dry-load's run.json goes to the scratch folder itself, so its refusal is printed, never written
        print(f"calibrate_epa.py {args.subcommand} --engine {args.engine}: refused: --out: {why}")
        deactivate()
        return EXIT_REFUSED
    return invoke(args.subcommand, args.engine, source=source, argv=argv, body=_body(args, source),
                  scratch=os.path.abspath(scratch) if scratch else None, audit=_CURRENT[0])


def wait_exit(subcommand, name, *, source):
    """The Run 1 gate's exit (main's waiting path): the audit's record shown to hold no table of the engine
    and no epa_engine.json (EXIT_DEFECT and the paths' count if it does), then EXIT_WAIT. Writes nothing."""
    a = _CURRENT[0]
    if a is not None:
        a.bind(_paths_for(name, source=source))
        paths = a.paths
        read = sorted(p for p in a.opened if p in set(paths["table_files"]) | {paths["engine_json"]})
        deactivate()
        if read:
            print(f"calibrate_epa.py {subcommand} --engine {name}: Run 1 waits, and {len(read)} EPA file(s) were "
                  "opened before the gate: a coding defect (PLAN.md 5.6)")
            return EXIT_DEFECT
    print(f"calibrate_epa.py {subcommand} --engine {name}: Run 1 waits. The contract names Run 1 in its "
          "open_for_the_team, or is the commit epa_rows pins (epa_rows.run1_wait, which fails closed). Nothing was "
          f"read from an EPA table and nothing was written. Set {RUN1_GO}={name} to start Run 1 on this engine, "
          "on the team's order (version 5 records Ghassan's go-ahead of 23 October 2026: version_5.go_ahead).")
    return EXIT_WAIT


if __name__ == "__main__":
    sys.exit(main(_ARGS, argv=sys.argv[1:]))

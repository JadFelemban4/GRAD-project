"""Where the numbers on the results tab came from: git, the live plant, the plant states.

READ-ONLY. Nothing here writes a file, and every git command it runs only
reads. GIT_OPTIONAL_LOCKS is set to "0" for the whole process the moment this
module is imported, before anything can call fingerprint.py: fingerprint._git
runs `git status` with the inherited environment, and a status allowed to
take its optional lock may rewrite .git/index.

THE GIT HELPER. One class, Git, makes every git call of a build, each with a
timeout. A missing git, a folder that is not a checkout, a timeout or any
other failure to run git leaves the helper unavailable, with a reason, and
every later call returns None without running anything: a build without git
omits the git facts and changes nothing else. A commit named in a result file
reaches git only after it matches a plain ref pattern, so the text of a file
can never become a git option.

THE LIVE SIDE. live_side() describes this tree: the plant hashes read from
disk, the hash of the derived constants and of the logs they were derived
from, and the live fingerprint block of each protocol, rendered by
fingerprint.format_block and parsed back by results_eval, so that a result
file's block and the live one are compared as the same text. The two data
hashes are copies of train.derived_sha and derive_params.fingerprint, each
tested equal to its original in a subprocess. This module never imports
derive_params (importing it sets DERIVING_PARAMS for the whole process, which
turns every missing derived constant into NaN), train, record_agents or
knock_margin.

THE PYTHON VERSION. fingerprint._code_only hashes the interpreter's own syntax
tree, so a plant hash depends on the Python minor version. A hash recorded
under another Python is compared only through git: the recorded commit's
plant files are read from git and hashed under this Python (plant_at,
road_sha_at), cached per commit, since a commit never changes.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

# Before the fingerprint import below, on purpose: see the module docstring.
os.environ["GIT_OPTIONAL_LOCKS"] = "0"

import fingerprint as FP  # the repository root; standard library only at import
from app import results_eval as EV

TAGS = ("sep17-before-merge", "ghassan-before-merge")
STATES = ("forced", "not_recorded", "another", "cannot_compare", "same_code", "same")
GIT_TIMEOUT_S = 15
# The plant code on disk when this module was imported, which is the plant the
# server runs when the module is imported at start. live_side compares the
# files on disk against it; a difference means the server needs a restart.
IMPORT_PLANT_SHA = FP._sha_files(FP.PLANT_FILES)

# A ref git may be asked about: a hex sha, a tag or HEAD. No leading dash (an
# option), no revision syntax, no spaces.
_REF = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._/-]{0,199}$")
_OBJECT_ID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_PLANT_AT = {}
_ROAD_AT = {}


class Git:
    """Every git call of a build: read-only, each with a timeout.

    `available` turns False, and `reason` says why, the first time git cannot
    be run ("missing", "timeout", "error") or the folder is not a checkout
    ("not_a_repo"); from then on every call returns None and runs nothing. A
    command that runs and fails, such as asking for a commit this clone does
    not have, returns None and leaves the helper available: an unknown commit
    is an answer, not a broken git.
    """

    def __init__(self, root, exe: str = "git", timeout: float = GIT_TIMEOUT_S):
        self.root = Path(root)
        self.exe = exe
        self.timeout = timeout
        self.available = True
        self.reason = None
        self._resolved = {}
        if not self.root.is_dir():
            self._lose("not_a_repo")
        elif self.run("rev-parse", "--git-dir") is None and self.available:
            self._lose("not_a_repo")

    def _lose(self, reason):
        self.available = False
        self.reason = reason

    def run(self, *args: str, binary: bool = False):
        """git's stdout (text, or bytes when `binary`), or None on any failure."""
        if not self.available:
            return None
        try:
            out = subprocess.run([self.exe, *args], cwd=self.root, capture_output=True,
                                 timeout=self.timeout,
                                 env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
        except FileNotFoundError:
            self._lose("missing")
            return None
        except subprocess.TimeoutExpired:
            self._lose("timeout")
            return None
        except (OSError, ValueError, subprocess.SubprocessError):
            self._lose("error")
            return None
        if out.returncode != 0:
            return None
        return out.stdout if binary else out.stdout.decode("utf-8", errors="replace")

    def resolve(self, sha: str):
        """The full commit id a recorded sha, a tag or HEAD names here, or None:
        unknown here, ambiguous, not a commit, or not a plain ref at all."""
        if not isinstance(sha, str) or not _REF.match(sha):
            return None
        if sha not in self._resolved:
            out = self.run("rev-parse", "--verify", "--quiet", sha + "^{commit}")
            full = (out or "").strip()
            self._resolved[sha] = full if _OBJECT_ID.match(full) else None
        return self._resolved[sha]

    def show(self, commit: str, relpath: str):
        """The bytes of `relpath` as `commit` holds it, or None."""
        if not isinstance(commit, str) or not _REF.match(commit):
            return None
        return self.run("show", f"{commit}:{relpath}", binary=True)

    def head_short(self):
        """The short id of HEAD, or None."""
        return (self.run("rev-parse", "--short", "HEAD") or "").strip() or None

    def last_commits(self, relpaths: list[str]) -> dict[str, dict]:
        """Each file's newest commit, from ONE log pass over `relpaths`.

        rel (forward slashes, from the repository root) -> {"short", "date"},
        the date being the committer date in ISO form. A merge names a file
        only when the merge itself changed it against every parent, so a file
        a merge only carried over keeps the commit that made it.
        """
        if not relpaths:
            return {}
        out = self.run("-c", "core.quotePath=false", "log", "--format=%x00%h%x09%cI",
                       "--name-only", "--diff-merges=dense-combined", "--",
                       *[str(p).replace("\\", "/") for p in relpaths])
        found = {}
        for record in (out or "").split("\x00")[1:]:
            head, _, names = record.partition("\n")
            short, _, date = head.partition("\t")
            for name in names.splitlines():
                if name and name not in found:
                    found[name] = {"short": short.strip(), "date": date.strip()}
        return found

    def status(self, relpaths: list[str]) -> dict[str, str]:
        """rel -> its git status code ("M", "??", ...) for every changed or
        untracked file under `relpaths`, from ONE status call; a clean file is
        absent. Read with -z, so no path is quoted and a rename is
        "XY to" followed by "from"."""
        if not relpaths:
            return {}
        out = self.run("status", "--porcelain=v1", "-z", "--untracked-files=all", "--",
                       *[str(p).replace("\\", "/") for p in relpaths])
        fields = (out or "").split("\x00")
        codes, i = {}, 0
        while i < len(fields):
            entry, i = fields[i], i + 1
            if len(entry) < 4:
                continue
            code = entry[:2]
            codes[entry[3:]] = code.strip()
            if "R" in code or "C" in code:
                i += 1
        return codes


def minor(version_text: str | None) -> str | None:
    """The minor version of a version text, or None when there is none."""
    m = re.match(r"\s*(\d+)\.(\d+)", version_text) if isinstance(version_text, str) else None
    return f"{m.group(1)}.{m.group(2)}" if m else None


def code_hash(sources: list[bytes]) -> str:
    """fingerprint._sha_files(code_only=True) over sources already read."""
    h = hashlib.sha256()
    for raw in sources:
        raw = raw.replace(b"\r\n", b"\n")
        code = FP._code_only(raw.decode("utf-8", errors="replace"))
        h.update(code.encode("utf-8") if code is not None else raw)
    return h.hexdigest()[:16]


def byte_hash(sources: list[bytes]) -> str:
    """fingerprint._sha_files(code_only=False) over sources already read."""
    h = hashlib.sha256()
    for raw in sources:
        h.update(raw.replace(b"\r\n", b"\n"))
    return h.hexdigest()[:16]


def _commit_id(git, commit):
    """A full object id as it is; anything else through git.resolve."""
    if isinstance(commit, str) and _OBJECT_ID.match(commit):
        return commit
    return git.resolve(commit)


def plant_at(git: Git, commit: str) -> dict | None:
    """{"plant_sha", "plant_text_sha"} of fingerprint.PLANT_FILES as `commit`
    holds them, hashed under THIS Python; None when git cannot read them."""
    full = _commit_id(git, commit)
    if full is None:
        return None
    if full not in _PLANT_AT:
        sources = []
        for name in FP.PLANT_FILES:
            raw = git.show(full, name)
            if raw is None:
                return None
            sources.append(raw)
        _PLANT_AT[full] = {"plant_sha": code_hash(sources), "plant_text_sha": byte_hash(sources)}
    return dict(_PLANT_AT[full])


def _road_code_sha(raw):
    """random_road.code_sha's rule over a file's bytes: the text as inspect
    reads it (UTF-8, a byte-order mark dropped, universal newlines), its code
    without docstrings by fingerprint._code_only, then SHA-256."""
    src = raw.decode("utf-8-sig", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    code = FP._code_only(src)
    return hashlib.sha256((code if code is not None else src).encode("utf-8")).hexdigest()[:16]


def road_sha_at(git: Git, commit: str) -> str | None:
    """random_road.py's road_sha as `commit` holds the file, under THIS Python."""
    full = _commit_id(git, commit)
    if full is None:
        return None
    if full not in _ROAD_AT:
        raw = git.show(full, "random_road.py")
        if raw is None:
            return None
        _ROAD_AT[full] = _road_code_sha(raw)
    return _ROAD_AT[full]


def data_fingerprint(root) -> str | None:
    """derive_params.fingerprint()["data_sha1"], copied: the logs the derived
    constants were made from. None when either file cannot be read."""
    h = hashlib.sha1()
    try:
        for name in ("master_samples.csv", "master_points.csv"):
            h.update((Path(root) / "data" / name).read_bytes().replace(b"\r\n", b"\n"))
    except OSError:
        return None
    return h.hexdigest()[:16]


def _values_sha(d):
    """train.derived_sha's hash of a loaded derived_params.json."""
    vals = {k: v for k, v in d.items() if not k.startswith("_")}
    return hashlib.sha256(json.dumps(vals, sort_keys=True).encode()).hexdigest()[:16]


def derived_sha(root) -> str | None:
    """train.derived_sha(), copied, over root/data/derived_params.json."""
    try:
        d = json.loads((Path(root) / "data" / "derived_params.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return _values_sha(d) if isinstance(d, dict) else None


def derived_loaded_differs(root) -> bool:
    """True when derived.py holds constants in memory and they are not the
    ones in root/data/derived_params.json on disk. False when derived.py was
    never imported or has not loaded its file yet."""
    mod = sys.modules.get("derived")
    cache = getattr(mod, "_CACHE", None)
    if not isinstance(cache, dict) or "d" not in cache:
        return False
    loaded = cache["d"]
    if not isinstance(loaded, dict):
        return True
    try:
        return _values_sha(loaded) != derived_sha(root)
    except (TypeError, ValueError):
        return True


def live_side(root, protocols=("phase-d", "d2")) -> dict:
    """This tree as the results tab compares against it. See the module docstring.

    A protocol whose live fingerprint cannot be built (an import that fails,
    an assertion at import, an unknown protocol) is absent from "blocks" and
    listed in "import_errors" with the exception's type name; KeyboardInterrupt
    is never caught."""
    python = platform.python_version()
    plant_sha = FP._sha_files(FP.PLANT_FILES)
    blocks, errors = {}, []
    for protocol in protocols:
        try:
            text = FP.format_block(FP.plant_fingerprint(protocol))
        except (Exception, SystemExit) as exc:
            errors.append({"module": f"fingerprint.plant_fingerprint({protocol})",
                           "type": type(exc).__name__})
            continue
        blocks[protocol] = EV.parse_fingerprint_block(text.splitlines())
    return {
        "python": python,
        "minor": minor(python),
        "plant_sha": plant_sha,
        "plant_text_sha": FP._sha_files(FP.PLANT_FILES, code_only=False),
        "restart_needed": plant_sha != IMPORT_PLANT_SHA,
        "derived_sha": derived_sha(root),
        "data_sha1": data_fingerprint(root),
        "derived_loaded_differs": derived_loaded_differs(root),
        "blocks": blocks,
        "import_errors": errors,
    }

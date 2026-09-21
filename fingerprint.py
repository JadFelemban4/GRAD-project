"""fingerprint.py — what plant produced this result, written down beside it.

    from fingerprint import plant_fingerprint, compare, format_block

WHY THIS FILE EXISTS
--------------------
RETIRED-OK: 11.7 -- naming the void figure IS the reason this file exists
AUDIT2.md C2-1. On 18 September two SAC agents were trained and `evaluate.py`
scored them at **+11.7 points**, written into `results/phase_d_seed0.txt` under
the line "THE ABLATION. This is the project's result." Seven hours later commit
`27e720c` replaced the gearbox -- an invented six-speed became the car's real
ZF 8HP51 -- and the plant those agents were trained on stopped existing in this
repository. The same command on the corrected plant prints **+7.5**.

Nothing failed. Nothing warned. `results/phase_d_seed0.txt` carries a header
that is a hardcoded string, byte-identical on both plants:

    print(f"scenario: 12 % at 130 km/h, 42 C, {DURATION:.0f} s, dt {DT}")

That sentence was true. It was also silent about the gearbox, the crank-angle
step, the protection trigger, the eight gear ratios and the git commit -- every
one of which moves the damage integral the result is made of. **A header that
cannot distinguish two plants is not provenance, it is decoration.**

WHAT A FINGERPRINT IS FOR, AND WHAT IT IS NOT FOR
-------------------------------------------------
It does not make a result correct. It makes a result *attributable*: it answers
"which plant produced this number" without anyone having to remember. That is
the whole job. `train.py` writes one into `runs/<tag>/meta.json` when it starts;
`evaluate.py` builds one from the LIVE objects, refuses a model whose fatal
fields differ, and writes its own block into the result file.

THE PLANT SOURCE HASH IS THE LOAD-BEARING FIELD, NOT THE GIT COMMIT
-------------------------------------------------------------------
The audit measured that the 18 September sighted run started **26 seconds
before** the commit that locked the scenario, from an uncommitted working tree.
So `git rev-parse HEAD` describes a tree the run did not use. It is recorded
anyway -- it is what a reader will look for -- but it is ADVISORY, and the
fatal comparison is a SHA-256 over the actual bytes of `plant.py`,
`thermal.py` and `engine_env.py`. Those three files are the physics. A dirty
tree changes the hash; a commit that does not touch them does not.

FATAL VERSUS ADVISORY, AND WHY `dt` IS NOT FATAL
-------------------------------------------------
`train.py` builds its environment at dt 0.2 over 900 s; `evaluate.py` scores at
dt 1.0 over 720 s. That asymmetry is real, it is a known open problem
(CLAUDE.md, "THE AGENT IS SCORED IN A DISCRETISATION IT DID NOT LEARN IN", and
AUDIT2.md H2-2), and it is DELIBERATE on both sides -- so comparing the two
would refuse every legitimate evaluation this project performs. It is reported
side by side instead, with the discrepancy named, so nobody has to remember it.

Fatal means: the two runs are not about the same physical system, and comparing
their numbers is meaningless.

    plant_sha          the bytes of plant.py + thermal.py + engine_env.py
    gears, final_drive the transmission
    dtheta_deg         the crank-angle integration step (AUDIT.md H1)
    turb_protect_k     the protection trigger; the damage knee
    oil_protect_k      the same for the oil node
    scenario           grade / v_kmh / t_amb from make_grade_climb's defaults
    episodes_sha       the twenty frozen evaluation episodes

Advisory means: worth knowing, not worth refusing over.

    git_head, git_dirty, git_dirty_plant_files, python, numpy, dt, duration,
    steps, seed, use_preview, created (a caller-supplied stamp)

`episodes_sha` is fatal on purpose. `evaluate.py`'s own docstring says THE
TWENTY EPISODES ARE FROZEN and that changing the test set after seeing a result
is "the one mistake this project cannot recover from". A frozen set that moves
is exactly the event that must stop a run, not warn about one.
"""
import ast
import hashlib
import json
import os
import platform
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# The files that ARE the physics. If any byte of these changes, two results are
# not comparable, whatever the commit says. Order is fixed so the hash is.
PLANT_FILES = ("plant.py", "thermal.py", "engine_env.py")

# Fields whose disagreement makes two numbers incomparable. Everything else in
# the block is printed for the reader and never refused over.
FATAL = ("plant_sha", "gears", "final_drive", "dtheta_deg", "turb_protect_k",
         "oil_protect_k", "scenario", "episodes_sha")

SCHEMA_VERSION = 1


def _code_only(src):
    """A file's CODE, with comments and docstrings removed.

    THIS IS THE CENTRAL DESIGN DECISION IN THIS FILE, so here is the argument.

    The obvious fingerprint is a hash of the source bytes. It is wrong, and it
    is wrong in a way that would have made this whole mechanism a liability
    rather than a guard.

    This project's documents ARE its source files. `verify_docs.py` scans every
    tracked `.py` and compares the figures in their docstrings against the data,
    and the next scheduled task is a sweep that rewrites exactly those
    docstrings. `engine_env.py`'s `make_grade_climb` docstring currently carries
    the line "130 km/h, invented gearbox 857 C", and 857 is a figure the
    repository has already retired.

    With a byte hash, correcting that sentence -- a change no engine can feel --
    would change `plant_sha`, and `evaluate.py` would then refuse every agent
    trained before the sweep. The guard would fire hardest on the project doing
    the right thing, and the obvious way out would be `--force-plant-mismatch`,
    which is how a refusal becomes a habit and then becomes noise.

    So the fatal hash is over the code: the source parsed to an AST with every
    docstring stripped, then dumped. A changed constant, a changed formula, a
    changed default, a renamed symbol and a deleted branch all move it. A
    comment, a docstring, a blank line and a reflowed paragraph do not.

    The raw byte hash is kept beside it as an ADVISORY field, so a reader can
    still see that the file changed at all.

    If the source does not parse, the byte hash is used instead -- a file that
    cannot be parsed is a file this project cannot run, and the caller will
    find that out one line later.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
            continue
        body = node.body
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            node.body = body[1:] or [ast.Pass()]
    return ast.dump(tree)


def _sha_files(names, code_only=True):
    """SHA-256 over `names`, in the given order.

    LINE ENDINGS ARE NORMALISED AND THAT IS LOAD-BEARING for the byte form.

    This repository is configured `core.autocrlf=true` and carries no
    `.gitattributes`, so the SAME COMMIT checks out as CRLF on Windows and as LF
    everywhere else. `engine_env.py` in this working copy is 1037 CRLF line
    endings and zero bare LFs; a teammate on Linux holds the identical file
    1037 bytes shorter.

    A raw byte hash would therefore give two people running the same commit two
    different fingerprints, and `evaluate.py` would refuse to score one of their
    agents -- in exactly the workflow Phase D is built around, which is five
    people training one seed each on five machines and pooling the results.
    That is the failure mode the refusal exists to prevent, arriving as the
    refusal itself. Measured: the CRLF and LF forms of this tree hash
    identically once normalised, and still differ after a one-constant edit.

    `code_only` additionally drops comments and docstrings -- see `_code_only`.
    """
    h = hashlib.sha256()
    for n in names:
        p = os.path.join(HERE, n)
        with open(p, "rb") as fh:
            raw = fh.read().replace(b"\r\n", b"\n")
        if code_only:
            code = _code_only(raw.decode("utf-8", errors="replace"))
            h.update(code.encode("utf-8") if code is not None else raw)
        else:
            h.update(raw)
    return h.hexdigest()[:16]


def _git(*args):
    """A git field, or None. Never raises: a fingerprint must not fail to build
    because the result is being produced outside a checkout."""
    try:
        out = subprocess.run(("git",) + args, cwd=HERE, capture_output=True,
                             text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def episodes_sha():
    """A hash of `evaluate.EPISODES`, the twenty frozen (seed, weights) pairs.

    Imported lazily. `evaluate` imports `check_premise`, which imports
    `engine_env`, and `train.py` should not pay for that import graph twice.
    """
    import evaluate
    return hashlib.sha256(repr(evaluate.EPISODES).encode()).hexdigest()[:16]


def plant_fingerprint(**advisory):
    """The block, built from the LIVE objects. Never from a literal.

    Every value here is read out of the imported module at the moment of the
    call, which is the point: a fingerprint typed as a constant would drift the
    same way the header string did.
    """
    import inspect

    import engine_env as E
    import evaluate as V
    from plant import DTHETA_DEG

    sig = inspect.signature(E.make_grade_climb).parameters
    scenario = {k: float(sig[k].default) for k in ("grade", "v_kmh", "t_amb")}

    dirty = _git("status", "--porcelain")
    dirty_plant = sorted(
        n for n in PLANT_FILES
        if dirty and any(line[3:].strip().endswith(n) for line in dirty.splitlines())
    )

    fp = {
        "schema": SCHEMA_VERSION,
        # --- fatal -----------------------------------------------------------
        "plant_sha": _sha_files(PLANT_FILES),
        # --- advisory, but it belongs beside its fatal twin ------------------
        # The byte hash moves when a comment or a docstring moves and the code
        # does not. It is recorded so a reader can see the file changed at all;
        # it is NOT compared, for the reason `_code_only` sets out.
        "plant_text_sha": _sha_files(PLANT_FILES, code_only=False),
        "gears": [float(g) for g in E.Vehicle.gears],
        "final_drive": float(E.Vehicle.final_drive),
        "dtheta_deg": float(DTHETA_DEG),
        "turb_protect_k": float(E.TURB_PROTECT_K),
        "oil_protect_k": float(E.OIL_PROTECT_K),
        "scenario": scenario,
        "episodes_sha": episodes_sha(),
        # --- advisory --------------------------------------------------------
        "git_head": _git("rev-parse", "HEAD"),
        # None, not False, when git could not be asked. `bool(None)` is False,
        # which would print "git_dirty False" into a result file produced from
        # an exported zip with no .git -- indistinguishable from a genuinely
        # clean tree. Unknown is not clean.
        "git_dirty": None if dirty is None else bool(dirty),
        "git_dirty_plant_files": None if dirty is None else dirty_plant,
        "eval_dt": float(V.DT),
        "eval_duration": float(V.DURATION),
        "n_episodes": len(V.EPISODES),
        "python": platform.python_version(),
    }
    fp.update(advisory)
    return fp


def compare(a, b):
    """Fields on which two fingerprints disagree, as (field, a, b) triples.

    FATAL fields only. `a` is conventionally the stored one (meta.json) and `b`
    the live one, and the caller decides what to do about a non-empty list.
    """
    out = []
    for k in FATAL:
        if a.get(k) != b.get(k):
            out.append((k, a.get(k), b.get(k)))
    return out


def advisory_diff(a, b):
    """The same for the fields that are reported and never refused over."""
    keys = [k for k in dict(a, **b) if k not in FATAL and k != "schema"]
    return [(k, a.get(k), b.get(k)) for k in sorted(keys) if a.get(k) != b.get(k)]


def format_block(fp, title="PLANT FINGERPRINT"):
    """The block as it is printed and as it is written into a result file.

    One line per field, sorted with the fatal fields first, so that a human
    diffing two result files reads the fields that decide comparability before
    the ones that do not.
    """
    def fmt(v):
        if isinstance(v, float):
            return f"{v:g}"
        if isinstance(v, (list, tuple)):
            return " ".join(f"{x:g}" if isinstance(x, float) else str(x) for x in v)
        if isinstance(v, dict):
            return " ".join(f"{k}={fmt(x)}" for k, x in sorted(v.items()))
        return str(v)

    rest = [k for k in sorted(fp) if k not in FATAL and k != "schema"]
    lines = [f"--- {title} " + "-" * max(0, 58 - len(title))]
    for k in list(FATAL) + rest:
        if k in fp:
            lines.append(f"  {k:<24} {fmt(fp[k])}")
    lines.append("-" * 62)
    return "\n".join(lines)


def write(path, fp):
    """Write a fingerprint as JSON, creating the directory if needed."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(fp, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def read(path):
    """Read a fingerprint, or None if it is absent or unreadable.

    A corrupt or unreadable meta.json is treated exactly like a missing one --
    the caller's "no fingerprint" branch already refuses, and a traceback here
    would hide that behind an encoding error.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            got = json.load(fh)
        return got if isinstance(got, dict) else None
    except (OSError, ValueError):
        return None


if __name__ == "__main__":
    print(format_block(plant_fingerprint(), "PLANT FINGERPRINT (live)"))
    sys.exit(0)

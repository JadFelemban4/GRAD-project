"""fingerprint.py — what plant produced this result, written down beside it.

    from fingerprint import plant_fingerprint, compare, format_block, BACKEND_CYCLE
    live = plant_fingerprint(plant=engines.get("b58"), train_backend=BACKEND_CYCLE,
                             score_backend=BACKEND_CYCLE, preview_h_s=engine_env.PREVIEW_H_S,
                             reward_knock=engine_env.REWARD_KNOCK_DEFAULT)

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
fatal comparison is a SHA-256 over what was actually on disk: the code of
PLANT_CODE (`plant.py`, `thermal.py` and `engine_env.py`; `derived.py` joined on
8 October 2026 and `engines.py` on 20 October) and the values of the passed
plant's own typed specs (plant_files). Those are the physics. A dirty tree
changes the hash; a commit that does not touch them does not.

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

    plant_sha          the code of PLANT_CODE (plant.py, thermal.py, engine_env.py,
                       derived.py, engines.py) and the VALUES of the passed plant's
                       own typed specs (plant_files: engine_specs/b58.toml and
                       a90_supra.toml for the B58)
    derived_sha        the plant's derived file (data/derived_params.json for the B58)
    engine             the plant's id, engine and car ("b58b30o1/a90-supra-zf8hp51")
    engine_sha         every value of the plant as built, from the live objects
    train_backend      what computes the engine in training, and in scoring:
    score_backend      "cycle", the 0-D cycle model, the only one (row 136);
                       every caller says which (backend_of), none is assumed
    backend_contract   the contract's two files, MD and JSON, by sha_text
    transmission       the car's box: stepped (gears, final_drive) or the
                       CVT's ratio range, final drive and law (transmission_of)
    dtheta_deg         the crank-angle integration step (AUDIT.md H1)
    turb_protect_k     the protection trigger; the damage knee
    oil_protect_k      the same for the oil node
    scenario           grade / v_kmh / t_amb of the plant's locked climb
                       (phase-d), random_road.spec() (d2), or decision 34's
                       roads record (d34; d34_roads)
    episodes_sha       the twenty frozen evaluation episodes
    preview_h_s        H, the preview horizon the agent saw, s; null for the
                       blinded arm (row 117)
    reward_knock       the reward's knock option, True for X1's knock term

Advisory means: worth knowing, not worth refusing over.

    plant_text_sha, preview_samples_s, git_head, git_dirty,
    git_dirty_plant_files, n_episodes, python, eval_dt, eval_duration, and the
    caller's own: dt, duration, steps, seed, use_preview, created (a stamp)

`episodes_sha` is fatal on purpose. `evaluate.py`'s own docstring says THE
TWENTY EPISODES ARE FROZEN and that changing the test set after seeing a result
is "the one mistake this project cannot recover from". A frozen set that moves
is exactly the event that must stop a run, not warn about one.

SCHEMA 3, 20 OCTOBER 2026 (the four-engine build, decision 24). The plant is
passed: plant_fingerprint(plant=engines.get(name)), and every plant field is
read from it -- the gears, the final drive and the knees were class attributes
and module constants of engine_env, the scenario make_grade_climb's defaults,
the derived file the B58's by default. Three FATAL fields join: `engine`,
`engine_sha` and `backend`. A schema-2 record names no engine, so it is refused
with a message that says so (schema_problem), never matched to one implicitly:
X1's and X2's agents are scored on main, and B58 agents trained on GRA-test are
a new experiment (CLAUDE.md rule 5).

SCHEMA 4, THE PLANT COMMIT (ORDER step 14; rows 94, 117, 127 and 136; decisions
27, 28, 34 and 91; interface sheet 6.2). `backend` becomes train_backend and
score_backend, each 'cycle' only (row 136 builds no table; the scoring stays on
the exact cycle permanently, MD:1462), beside the contract they are judged under
(backend_contract). `gears` and `final_drive` become `transmission`, which a CVT
can fill: schema 3 refused the Accord by name (amendment B17). Decision 34's
protocol, d34, reads its scenario and its twenty roads from the roads record
(d34_roads). preview_h_s and reward_knock are FATAL and have no default
(mistake 19): the blinded arm records preview_h_s null, and pair_problems is row
117's rule for pairing a sighted agent with a blinded one. plant_sha's files and
rule are unchanged. git_dirty_plant_files matches whole paths (row 127 (5)). A
schema-3 record is refused by schema_problem with its own message.
"""
import ast
import hashlib
import json
import os
import platform
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# The code that IS the physics, whatever the engine. If any of it changes, two
# results are not comparable, whatever the commit says. Order is fixed so the
# hash is. engines.py joined on 20 October 2026 (schema 3), and with it each
# plant's typed specs, which plant_files appends: a spec is hashed by its
# VALUES, not its labels and sources (_file_code).
PLANT_CODE = ("plant.py", "thermal.py", "engine_env.py", "derived.py", "engines.py")


def plant_files(name):
    """The files the plant registered as `name` (engines.PLANTS) is hashed by, in
    order: PLANT_CODE, then that plant's own typed specs (engines.spec_files).

    Until 21 October 2026 this was one tuple, PLANT_FILES, naming the B58's two
    specs for every plant: an edit to the B58's spec would have moved every
    engine's plant_sha, and an edit to another engine's spec none (the review of
    build step 1). The B58's list is the tuple it was."""
    import engines
    return PLANT_CODE + engines.spec_files(name)

# Fields whose disagreement makes two numbers incomparable. Everything else in
# the block is printed for the reader and never refused over.
FATAL = ("plant_sha", "derived_sha", "engine", "engine_sha", "train_backend", "score_backend",
         "backend_contract", "transmission", "dtheta_deg", "turb_protect_k", "oil_protect_k", "scenario",
         "episodes_sha", "preview_h_s", "reward_knock")

# 2 since 8 October 2026 (conflict.md decision 2, agreed by Jad and Ghassan):
# the derived constants are fatal (derived_sha), derived.py is a plant file, and
# the code hash no longer depends on the Python version (_code_only).
# 3 since 20 October 2026 (the four-engine build): the plant is passed, and
# engine, engine_sha and backend are fatal. See the module docstring.
# 4 since the plant commit (ORDER step 14; rows 117 and 127 (3)): transmission,
# train_backend and score_backend with the contract, decision 34's protocol,
# preview_h_s and reward_knock. See the module docstring.
SCHEMA_VERSION = 4

# What computes the engine, in training (train_backend) and in scoring
# (score_backend). Only the 0-D cycle model exists, and row 136 builds no table,
# so no other backend string exists. plant_fingerprint has no default for either
# (21 October 2026, the review of build step 1): a FATAL field filled from a
# keyword default would record "cycle" for an agent whose caller forgot to say
# what computed its engine, and the comparison would then pass it (mistake 19).
BACKEND_CYCLE = "cycle"


def backend_of(env):
    """The backend of a SupervisoryTunerEnv (or anything with its `engine`
    attribute): the 0-D cycle model when it was given no engine_model, which is
    every environment this project builds. An engine_model has no backend name
    (row 136 builds no table), so it is refused, never called "cycle"; so is an
    object with no `engine` at all (a wrapper: pass env.unwrapped). train.py
    records it as train_backend (schema 4)."""
    if not hasattr(env, "engine"):
        raise TypeError(f"backend_of needs the SupervisoryTunerEnv itself (env.unwrapped), "
                        f"not a {type(env).__name__}")
    if env.engine is None:
        return BACKEND_CYCLE
    raise ValueError(f"the environment computes its engine with {type(env.engine).__name__}, which "
                     "has no backend name (row 136 builds no table); fingerprint.py records only "
                     f"{BACKEND_CYCLE!r}, the 0-D cycle model")


def preview_of(env):
    """H, s, as an environment holds it (row 117): None for the blinded arm, which sees no grade ahead at
    any H, else float(env.preview_h_s). TypeError for an object without use_preview and preview_h_s (a
    wrapper: pass env.unwrapped)."""
    if not (hasattr(env, "use_preview") and hasattr(env, "preview_h_s")):
        raise TypeError(f"preview_of needs the SupervisoryTunerEnv itself (env.unwrapped), "
                        f"not a {type(env).__name__}")
    return float(env.preview_h_s) if env.use_preview else None


def reward_knock_of(env):
    """The reward's knock option an environment computes (row 113 (5)): env.reward_knock, a bool. TypeError
    when it is missing (a wrapper: pass env.unwrapped) or not a bool."""
    v = getattr(env, "reward_knock", None)
    if type(v) is not bool:
        raise TypeError(f"reward_knock_of needs the SupervisoryTunerEnv itself (env.unwrapped), whose "
                        f"reward_knock is a bool; a {type(env).__name__} gives {v!r}")
    return v


def transmission_of(car):
    """The car's box as schema 4 records it, read from the car record (dispatched on its type, so a new
    kind of car is a TypeError until it has a form here):

        engines.Car, engines.EpaCar   {"kind": "stepped", "gears": [...], "final_drive": ...}
        engines.CvtCar                {"kind": "cvt", "ratio_low_gear", "ratio_top_gear", "final_drive",
                                       "kickdown_load", "target_load", "cvt_rpm_min"}: the published
                                       range and decision 40's law (engines.py, CvtCar)"""
    import engines
    if type(car) in (engines.Car, engines.EpaCar):
        return {"kind": "stepped", "gears": [float(g) for g in car.gears], "final_drive": float(car.final_drive)}
    if type(car) is engines.CvtCar:
        return {"kind": "cvt", **{k: float(getattr(car, k)) for k in (
            "ratio_low_gear", "ratio_top_gear", "final_drive", "kickdown_load", "target_load", "cvt_rpm_min")}}
    raise TypeError(f"transmission_of: {type(car).__name__} is not an engines.Car, EpaCar or CvtCar")


def backend_contract():
    """The contract a backend is judged under (MD:1466-1467; row 117): the sha_text of both of its files,
    results/ENGINE_THRESHOLDS.md and .json (thresholds.common). The files are hashed, never parsed. Read
    at every call, never at import, so a guarded test patches this function (interface sheet 1.8)."""
    from thresholds import common
    return {"md_sha_text": common.sha_text(common.CONTRACT_MD),
            "json_sha_text": common.sha_text(common.CONTRACT_JSON)}


def for_arm(fp, *, sighted):
    """A copy of a live block for one arm: the blinded arm's H is None (row 117), so its preview_h_s and
    preview_samples_s are None. The live side of a comparison; it never writes a meta.json."""
    out = dict(fp)
    if not sighted:
        out.update(preview_h_s=None, preview_samples_s=None)
    return out


def pair_problems(sighted, blind):
    """Row 117's pairing rule, as (field, a, b) triples, [] for a pair: every FATAL field but preview_h_s
    agrees; the sighted agent's H is a positive finite float and the blinded agent's is None; and neither
    block is of another schema (schema_problem)."""
    import math
    out = [(k, sighted.get(k), blind.get(k)) for k in FATAL
           if k != "preview_h_s" and sighted.get(k) != blind.get(k)]
    h = sighted.get("preview_h_s")
    if not (type(h) is float and math.isfinite(h) and h > 0.0):
        out.append(("preview_h_s", h, "the sighted agent's H is not a positive finite float"))
    if blind.get("preview_h_s") is not None:
        out.append(("preview_h_s", blind.get("preview_h_s"), "the blinded agent's H is not None"))
    for side, block in (("sighted", sighted), ("blind", blind)):
        why = schema_problem(block)
        if why:
            out.append(("schema", side, why))
    return out


def _d34(root):
    """(scenario, roads, design) of decision 34's scored set; d34_roads says what is read and refused."""
    import epa_roads as ER
    from thresholds import common
    path = os.path.join(root, ER.ROADS_REL)
    record = ER.load_record(path)
    roads_sha = ER.roads_sha(path)
    rpath = os.path.join(root, ER.REDRAWS_REL)
    if os.path.exists(rpath):
        redraws = ER.load_record(rpath)
        if redraws.get("roads_sha") != roads_sha:
            raise ValueError(f"decision 34: {ER.REDRAWS_REL} was redrawn from another roads.json "
                             f"(its roads_sha is not {ER.ROADS_REL}'s)")
        roads, reading, redraws_sha = redraws["readings"]["version 6"]["roads"], "version 6", common.sha_text(rpath)
    elif record["seed_kind"] == "REAL":
        raise ValueError(f"decision 34: a REAL {ER.ROADS_REL} without {ER.REDRAWS_REL}: the decision-34 set "
                         "is final only once R4 commits the redraws (ORDER step 12; row 95 (2))")
    else:
        roads, reading, redraws_sha = record["roads"], "first draw", None
    episodes = ER.frozen_episodes(root=root)
    if [r.get("k") for r in roads] != list(range(len(episodes))):
        raise ValueError(f"decision 34: the roads are not k = 0..{len(episodes) - 1} in order")
    for r in roads:
        w = r["weights"]
        if (type(r["episode_seed"]) is not int or not all(type(x) is float for x in w)
                or (r["episode_seed"], tuple(w)) != episodes[r["k"]]):
            raise ValueError(f"decision 34: road {r['k']}'s (episode_seed, weights) is not evaluate.EPISODES"
                             f"[{r['k']}]")
    scenario = {"protocol": "decision-34", "seed_kind": record["seed_kind"], "roads_sha": roads_sha,
                "redraws_sha": redraws_sha, "reading": reading,
                "design_sha": hashlib.sha256(json.dumps(record["design"], sort_keys=True).encode()).hexdigest()[:16]}
    return scenario, roads, record["design"]


def d34_roads(*, root):
    """(scenario, roads): decision 34's scored set, the one reader of it (interface sheet 6.2 and 12.10).
    roads.json's twenty roads as R4's redraws.json reads them under version 6 (row 95 (2)), whose
    roads_sha must be roads.json's; a SYNTHETIC record without redraws.json is its first draw, and a REAL
    one without it is refused. The roads must be k = 0..19 in order, each with evaluate.EPISODES[k]'s
    seed and float weights. Nothing of commit_reveal (roads_seed and the revealed integers) is read into
    the scenario. Imports only epa_roads and thresholds.common, lazily."""
    scenario, roads, _ = _d34(root)
    return scenario, roads


def d34_set(*, root):
    """(scenario, entries): one entry (k, episode_seed, weights, the arrays' sha256) per road of
    d34_roads, which episodes_sha('d34') hashes."""
    scenario, roads = d34_roads(root=root)
    return scenario, _d34_entries(roads)


def _d34_entries(roads):
    import epa_roads as ER
    return tuple((r["k"], r["episode_seed"], tuple(r["weights"]), ER.arrays_sha256([r])) for r in roads)


def _porcelain_paths(z):
    """The paths of `git status --porcelain=v1 -z --no-renames`: NUL-separated, never quoted, whole."""
    return {e[3:] for e in z.split("\0") if e}


def _dirty_plant(files, paths, prefix):
    """The plant files among git's paths, matched whole (row 127 (5)): git names a path from the
    repository's root, and `prefix` (rev-parse --show-prefix) is this directory's path there."""
    return sorted(n for n in files if prefix + n in paths)


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

    So the fatal hash is over the code: the source with every docstring
    stripped (see below for how, since 8 October). A changed constant, a changed formula, a
    changed default, a renamed symbol and a deleted branch all move it. A
    comment, a docstring, a blank line and a reflowed paragraph do not.

    The raw byte hash is kept beside it as an ADVISORY field, so a reader can
    still see that the file changed at all.

    If the source does not parse, the byte hash is used instead -- a file that
    cannot be parsed is a file this project cannot run, and the caller will
    find that out one line later.

    A TYPED SPEC IS HASHED BY ITS VALUES (20 October 2026), by _file_code, which
    picks the rule by the file's kind: engine_specs/*.toml is not Python, and
    for it the "code" is every value with its label, source and unit dropped
    (_spec_values), so correcting a source moves nothing and a changed number
    moves the hash -- the same rule, one level over. Until 21 October 2026 the
    spec rule was this function's fallback for text that failed to parse as
    Python, and the same spec written as TOML tables ([geometry.bore] then
    value = ..., which engines.read_spec reads alike) parses as Python, so a
    source correction moved plant_sha (the review of build step 1).

    THE FORM CHANGED ON 8 OCTOBER 2026, and the reason is the same argument one
    level down. `ast.dump` is not a stable format: Python 3.12 and 3.13 print the
    same tree differently, so two people on the same commit with different
    Pythons got different `plant_sha` values (found 30 September, the agents
    page report). The code is now the SOURCE TEXT with every docstring and every
    comment cut out by position, trailing spaces dropped and blank lines removed.
    The positions come from `ast` and `tokenize`, which agree across versions;
    the text itself is what was written. A changed constant, formula, default,
    name or branch still moves it; a comment, a docstring or a blank line does not.
    """
    import io
    import tokenize
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    lines = src.splitlines()
    drop = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
            continue
        body = node.body
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            drop.update(range(body[0].lineno - 1, body[0].end_lineno))
    cut = {}
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                row, col = tok.start
                cut[row - 1] = min(col, cut.get(row - 1, col))
    except (tokenize.TokenError, IndentationError):
        return None
    out = []
    for i, line in enumerate(lines):
        if i in drop:
            continue
        if i in cut:
            line = line[:cut[i]]
        line = line.rstrip()
        if line:
            out.append(line)
    return "\n".join(out)


def _spec_values(src):
    """A typed spec's values as canonical text (engines.read_spec's format):
    every { value = ..., ... } entry reduced to its value, top-level keys kept.
    None when `src` is not such a TOML file."""
    import tomllib
    try:
        raw = tomllib.loads(src)
    except (tomllib.TOMLDecodeError, TypeError):
        return None

    def values(node):
        if isinstance(node, dict):
            if "value" in node and set(node) <= {"value", "label", "source", "unit"}:
                return node["value"]
            return {k: values(v) for k, v in node.items()}
        return node
    return json.dumps(values(raw), sort_keys=True)


def _file_code(name, src):
    """What plant_sha hashes of the file `name` holding `src`, or None for its
    bytes: a typed spec (.toml) by its values (_spec_values), anything else as
    Python by its code (_code_only). By the file's kind, not by whether the text
    happens to parse as Python (_code_only's docstring)."""
    if name.endswith(".toml"):
        return _spec_values(src)
    return _code_only(src)


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

    `code_only` additionally drops comments and docstrings, and a typed spec's
    labels and sources -- see `_code_only` and `_file_code`.
    """
    h = hashlib.sha256()
    for n in names:
        p = os.path.join(HERE, n)
        with open(p, "rb") as fh:
            raw = fh.read().replace(b"\r\n", b"\n")
        if code_only:
            code = _file_code(n, raw.decode("utf-8", errors="replace"))
            h.update(code.encode("utf-8") if code is not None else raw)
        else:
            h.update(raw)
    return h.hexdigest()[:16]


def _git(*args):
    """A git field, or None. Never raises: a fingerprint must not fail to build
    because the result is being produced outside a checkout.

    Only the line ends are stripped (22 October 2026, build step 2 P7; found on
    the way by the reviews of P2, P3, P4 and P6, outside their scope). `git
    status --porcelain` begins each line with two status columns, the first a
    space for a file changed in the work tree only (" M engine_env.py"); the
    strip() this was dropped that space from the first line alone, so
    git_dirty_plant_files read that line's path without its first character
    ("ngine_env.py") and never named the first dirty file. A git_dirty_plant_files
    recorded before this can be short by that one file."""
    try:
        out = subprocess.run(("git",) + args, cwd=HERE, capture_output=True,
                             text=True, timeout=10)
        return out.stdout.rstrip("\r\n") if out.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def _episode_set(protocol):
    """The frozen evaluation set a protocol is scored on."""
    if protocol == "d34":
        return d34_set(root=HERE)[1]
    import evaluate
    if protocol == "phase-d":
        return evaluate.EPISODES
    if protocol == "d2":
        return evaluate.EPISODES_D2
    raise ValueError(f"unknown protocol {protocol!r}; expected 'phase-d', 'd2' or 'd34'")


def episodes_sha(protocol="phase-d"):
    """A hash of the protocol's frozen episode set.

    Phase D: `evaluate.EPISODES`, twenty (seed, weights) pairs -- UNCHANGED, so
    every Phase D `meta.json` still matches. Phase D2: `evaluate.EPISODES_D2`,
    the same twenty plus a pinned (start, grade) road each. Decision 34 (schema
    4): d34_set's twenty entries, each road's k, seed, weights and arrays.

    Imported lazily. `evaluate` imports `check_premise`, which imports
    `engine_env`, and `train.py` should not pay for that import graph twice.
    """
    return hashlib.sha256(repr(_episode_set(protocol)).encode()).hexdigest()[:16]


def derived_sha(path):
    """A hash of a derived file's VALUES (keys starting with "_" are
    bookkeeping: inputs, timestamps). Since 28 September the plant's thermal,
    boost, spark, enrichment and gearbox constants live there; since 8 October
    a change to them is fatal, like a change to the code (conflict.md decision 2).

    `path` is REQUIRED (20 October 2026): it defaulted to the B58's file,
    data/derived_params.json, for every engine. The fingerprint hashes the
    plant's own (plant.engine.derived); test_plant_guards.py hashes a copy to
    show that one changed constant moves the hash and a timestamp does not,
    without touching the real file."""
    p = path
    try:
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        return None
    vals = {k: v for k, v in d.items() if not k.startswith("_")}
    return hashlib.sha256(json.dumps(vals, sort_keys=True).encode()).hexdigest()[:16]


def plant_fingerprint(protocol="phase-d", *, plant, train_backend, score_backend, preview_h_s, reward_knock,
                      **advisory):
    """The block, built from the LIVE objects. Never from a literal.

    Every value here is read out of the plant passed in and the imported
    modules at the moment of the call, which is the point: a fingerprint typed
    as a constant would drift the same way the header string did. `plant` (an
    engines.Plant) is REQUIRED (schema 3, 20 October 2026), and so is every
    FATAL input a caller knows and the plant does not (schema 4; mistake 19):
    `train_backend` and `score_backend`, what computes the engine in training
    and in scoring (backend_of(env), or BACKEND_CYCLE from a caller whose
    episodes run the 0-D cycle model; 'cycle' only, row 136); `preview_h_s`,
    the agent's H (preview_of(env); None for the blinded arm, row 117); and
    `reward_knock`, the reward's knock option (reward_knock_of(env)). None has
    a default. plant_sha hashes the code and the passed plant's own specs
    (plant_files, by engines.name_of).

    `protocol` selects the experiment, and it changes two FATAL fields:

        phase-d   scenario = the plant's locked climb, (grade, v_kmh, t_amb)
                  (make_grade_climb's defaults until 20 October 2026)
                  episodes_sha = evaluate.EPISODES
        d2        scenario = random_road.spec(): the two ranges, speed,
                  ambient and a hash of random_road.py's own code
                  episodes_sha = evaluate.EPISODES_D2
        d34       scenario = decision 34's roads record (d34_roads; interface
                  sheet 12.10), eval_dt and eval_duration its design's
                  episodes_sha = d34_set's twenty roads

    So a Phase D agent scored under D2, or the reverse, is REFUSED on
    `scenario` -- which is correct: neither number would belong to either
    experiment.

    Refused: an advisory `use_preview` that contradicts preview_h_s; an
    advisory transmission or backend_contract (both FATAL, read here, never
    passed); and under d34 an advisory eval_dt, eval_duration, scenario,
    episodes_sha or n_episodes that differs from the value read here.
    """
    import engines
    import engine_env as E
    import evaluate as V
    from plant import DTHETA_DEG

    if plant is None:
        raise TypeError("plant_fingerprint(plant=engines.get(name)): there is no default engine")
    # BOTH BACKENDS ARE THE CYCLE (row 136: every engine trains on the exact cycle, and no table is
    # built; the scoring stays on it permanently, MD:1462). Both stay FATAL, as row 117 lists them.
    for name, value in (("train_backend", train_backend), ("score_backend", score_backend)):
        if value != BACKEND_CYCLE:
            raise ValueError(f"{name} {value!r}: only {BACKEND_CYCLE!r}, the 0-D cycle model, exists "
                             "(row 136 builds no table)")
    if preview_h_s is not None:
        try:
            samples = list(E.preview_samples(preview_h_s))
        except (TypeError, ValueError) as exc:
            raise type(exc)(f"plant_fingerprint: preview_h_s {preview_h_s!r} is neither None (the blinded "
                            f"arm) nor an H the environment takes: {exc}") from None
    if type(reward_knock) is not bool:
        raise TypeError(f"plant_fingerprint: reward_knock is a bool, the reward's knock option "
                        f"(row 113 (5)), not {reward_knock!r}")
    if "use_preview" in advisory and bool(advisory["use_preview"]) != (preview_h_s is not None):
        raise ValueError(f"plant_fingerprint: use_preview {advisory['use_preview']!r} contradicts "
                         f"preview_h_s {preview_h_s!r}: the blinded arm's H is None, a sighted arm's a number")
    passed = sorted(k for k in ("transmission", "backend_contract") if k in advisory)
    if passed:
        raise ValueError(f"plant_fingerprint: {passed} are FATAL and read here (transmission_of, "
                         "backend_contract), never passed")
    # A CANDIDATE IS NEVER FINGERPRINTED (22 October 2026, the review of build step
    # 2 P5): engines.build_candidate builds it from a calibration's in-memory
    # values, and derived_sha below would hash the file on disk its engine.derived
    # names, which it was not built from.
    if engines.is_candidate(plant):
        raise ValueError(f"{plant.id}: a candidate (engines.build_candidate), built from in-memory DERIVED "
                         f"values, not from {plant.engine.derived}: a fingerprint would record that file's "
                         "derived_sha for it. Fingerprint the plant engines.get builds from the file")
    files = plant_files(engines.name_of(plant))
    eval_dt, eval_duration = float(V.DT), float(V.DURATION)
    if protocol == "phase-d":
        sc = plant.scenario
        scenario = {"grade": float(sc.grade), "v_kmh": float(sc.v_kmh), "t_amb": float(sc.t_amb)}
        episodes = _episode_set(protocol)
    elif protocol == "d2":
        import random_road as RR
        scenario = RR.spec()
        episodes = _episode_set(protocol)
    elif protocol == "d34":
        scenario, roads, design = _d34(HERE)
        episodes = _d34_entries(roads)
        eval_dt, eval_duration = float(design["dt"]), float(design["duration_s"])
    else:
        raise ValueError(f"unknown protocol {protocol!r}; expected 'phase-d', 'd2' or 'd34'")
    ep_sha = hashlib.sha256(repr(episodes).encode()).hexdigest()[:16]
    if protocol == "d34":
        own = {"eval_dt": eval_dt, "eval_duration": eval_duration, "scenario": scenario, "episodes_sha": ep_sha,
               "n_episodes": len(episodes)}
        differ = sorted(k for k, v in own.items() if k in advisory and advisory[k] != v)
        if differ:
            raise ValueError(f"plant_fingerprint: under d34, {differ} are the roads record's, and the "
                             "caller's differ")

    # the exact match (row 127 (5)): -z keeps every path whole and unquoted, --no-renames lists a
    # rename as its two paths, and --untracked-files=all names each new file (20 October 2026: without
    # it git folds a new directory into one line, "?? engine_specs/"). The paths are the repository's,
    # so this directory's prefix is added to each plant file's name; the suffix match this replaces
    # named thermal.py for a dirty car_thermal.py.
    status = _git("status", "--porcelain=v1", "-z", "--no-renames", "--untracked-files=all")
    prefix = _git("rev-parse", "--show-prefix")
    paths = None if status is None or prefix is None else _porcelain_paths(status)

    fp = {
        "schema": SCHEMA_VERSION,
        # --- fatal -----------------------------------------------------------
        "plant_sha": _sha_files(files),
        # --- advisory, but it belongs beside its fatal twin ------------------
        # The byte hash moves when a comment or a docstring moves and the code
        # does not. It is recorded so a reader can see the file changed at all;
        # it is NOT compared, for the reason `_code_only` sets out.
        "plant_text_sha": _sha_files(files, code_only=False),
        # The constants the logs set live in the plant's derived file, not in
        # the files above: a new drive changes the plant without touching them.
        "derived_sha": derived_sha(os.path.join(HERE, plant.engine.derived)),
        # which plant, and every value it was built with (schema 3)
        "engine": plant.id,
        "engine_sha": engines.engine_sha(plant),
        # what computed the engine, and the contract it is judged under (schema 4)
        "train_backend": train_backend,
        "score_backend": score_backend,
        "backend_contract": backend_contract(),
        "transmission": transmission_of(plant.car),
        "dtheta_deg": float(DTHETA_DEG),
        "turb_protect_k": float(plant.engine.damage.turb_knee_k),
        "oil_protect_k": float(plant.engine.damage.oil_knee_k),
        "scenario": scenario,
        "episodes_sha": ep_sha,
        # the agent's H and the reward's knock option (schema 4; rows 113 (5) and 117)
        "preview_h_s": None if preview_h_s is None else float(preview_h_s),
        "reward_knock": reward_knock,
        # --- advisory --------------------------------------------------------
        "preview_samples_s": None if preview_h_s is None else samples,
        "git_head": _git("rev-parse", "HEAD"),
        # None, not False, when git could not be asked. `bool(None)` is False,
        # which would print "git_dirty False" into a result file produced from
        # an exported zip with no .git -- indistinguishable from a genuinely
        # clean tree. Unknown is not clean.
        "git_dirty": None if paths is None else bool(paths),
        "git_dirty_plant_files": None if paths is None else _dirty_plant(files, paths, prefix),
        "n_episodes": len(episodes),
        "python": platform.python_version(),
        "eval_dt": eval_dt,
        "eval_duration": eval_duration,
    }
    fp.update(advisory)
    return fp


def schema_problem(stored):
    """Why a stored fingerprint cannot be compared with this tree's, or None.

    A record of an older schema names no engine (schema 3, 20 October 2026):
    comparing it field by field would list engine, engine_sha and backend as
    "mismatches" and hide the reason, so the callers ask this first and refuse
    with its message. A schema-3 record has its own (schema 4, the plant
    commit): it names its engine but not what schema 4 adds."""
    s = stored.get("schema")
    if s == SCHEMA_VERSION:
        return None
    if s == 3:
        return ("its meta.json is fingerprint schema 3, written before the plant commit (ORDER step 14): "
                "it records no transmission, train/score backend, decision-34 protocol, preview_h_s or "
                f"reward knock option, and none is assumed. This tree writes schema {SCHEMA_VERSION}; an "
                "agent trained on it is a new experiment (CLAUDE.md rule 5).")
    return (f"its meta.json is fingerprint schema {s}, written before the four-engine "
            f"build; this tree writes schema {SCHEMA_VERSION}. A schema-{s} record names no "
            "engine (no engine, engine_sha or backend), and none is assumed for it. Agents "
            "trained before 20 October 2026 -- X1's and X2's among them -- are scored on "
            "main; a B58 agent trained on this tree is a new experiment (CLAUDE.md rule 5).")


def compare(a, b):
    """Fields on which two fingerprints disagree, as (field, a, b) triples.

    FATAL fields only. `a` is conventionally the stored one (meta.json) and `b`
    the live one, and the caller decides what to do about a non-empty list.
    A stored record of an older schema lacks the schema-3 or schema-4 fields, so
    they show here as disagreements; ask schema_problem first for the reason. A
    blinded agent is compared with for_arm(live, sighted=False).
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


def model_budget(zip_path):
    """How long a saved agent was ACTUALLY trained, read out of the zip itself.

    Added 23 September 2026 for C4. The fingerprint above cannot tell a C4
    agent from a Phase D2 agent: same plant, same scenario, same episodes. The
    only field that differs is `steps_requested`, which is ADVISORY and lives
    in `meta.json` -- a file a resume never rewrites. So a D2 agent resumed to
    300 000 steps would carry a 50 000-step certificate, and a C4 result could
    be computed on an agent that is not a C4 agent with nothing to say so.

    stable-baselines3 writes its own counters into the zip's `data` member,
    and those are written by the training loop, not by us:

        num_timesteps            steps actually taken
        total_timesteps          what the LAST learn() call was asked for
        num_timesteps_at_start   0 for a fresh run; the resume point otherwise
        buffer_size              the replay buffer the run held -- a resume
                                 restores the OLD size, so a 50 000-step run
                                 resumed to 300 000 still says 50 000
        sha                      the first 16 hex of SHA-256 over the zip's
                                 bytes, so a result file can name exactly
                                 which artefact it scored

    Read with `zipfile` and `json` only: no stable-baselines3 import, no torch,
    no device. Returns None if the file is absent or is not an SB3 zip.
    """
    import zipfile
    try:
        with zipfile.ZipFile(zip_path) as z:
            data = json.loads(z.read("data"))
        with open(zip_path, "rb") as fh:
            sha = hashlib.sha256(fh.read()).hexdigest()[:16]
    except (OSError, KeyError, ValueError, zipfile.BadZipFile):
        return None

    def num(k):
        v = data.get(k)
        return int(v) if isinstance(v, (int, float)) else None

    return {
        "num_timesteps": num("num_timesteps"),
        "total_timesteps": num("_total_timesteps"),
        "num_timesteps_at_start": num("_num_timesteps_at_start"),
        "buffer_size": num("buffer_size"),
        "sha": sha,
    }


RUNNING = "RUNNING"


def pid_alive(pid):
    """True if a process with this pid exists. It is never signalled.

    NOT `os.kill(pid, 0)` on Windows: there `os.kill` with any signal other
    than the two console events calls TerminateProcess, so the POSIX idiom for
    "is it alive?" would kill the training run it was asking about. The
    Windows branch opens the process for query only and reads its exit code
    (259, STILL_ACTIVE, while it runs). A recycled pid reads as alive -- the
    safe direction, since the caller then leaves the directory alone.
    """
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.OpenProcess.restype = wintypes.HANDLE
        k32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        k32.GetExitCodeProcess.argtypes = (wintypes.HANDLE,
                                           ctypes.POINTER(wintypes.DWORD))
        k32.CloseHandle.argtypes = (wintypes.HANDLE,)
        h = k32.OpenProcess(0x1000, False, pid)   # QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = wintypes.DWORD()
        ok = k32.GetExitCodeProcess(h, ctypes.byref(code))
        k32.CloseHandle(h)
        return bool(ok) and code.value == 259
    try:
        os.kill(pid, 0)          # POSIX: signal 0 tests existence, sends nothing
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def running_pid(run_dir):
    """The pid of the process training `run_dir` right now, or None.

    Added 23 September 2026 after the C4 review. A run that is still training
    and a run that crashed look identical on disk -- checkpoints, no
    final.zip -- and the launcher's crash rule moved the one it meant to
    restart. `train.py` now writes `<run_dir>/RUNNING` with its pid while it
    trains and removes it when it finishes; a crash leaves the file behind
    with a pid that is no longer alive.
    """
    try:
        with open(os.path.join(run_dir, RUNNING), encoding="utf-8") as fh:
            pid = int(json.load(fh)["pid"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return pid if pid_alive(pid) else None


def claim_running(run_dir):
    """Mark `run_dir` as being trained by this process."""
    import time
    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, RUNNING), "w", encoding="utf-8") as fh:
        json.dump({"pid": os.getpid(),
                   "started": time.strftime("%Y-%m-%dT%H:%M:%S%z")}, fh)


def release_running(run_dir):
    """Remove the mark, only if it is this process's own."""
    p = os.path.join(run_dir, RUNNING)
    try:
        with open(p, encoding="utf-8") as fh:
            mine = int(json.load(fh)["pid"]) == os.getpid()
        if mine:
            os.remove(p)
    except (OSError, ValueError, KeyError, TypeError):
        pass


def format_budget(b):
    """One line for a result file. Parsed back by `analyse_c4.py`."""
    if b is None:
        return "budget unreadable"
    return (f"trained {b['num_timesteps']} steps of {b['total_timesteps']} "
            f"requested, from step {b['num_timesteps_at_start']}, "
            f"buffer {b['buffer_size']}, zip sha {b['sha']}")


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


def refuse_uncalibrated(name):
    """Stop, naming the plant, when the plant registered as `name` has no derived
    file yet (or, an EPA engine, no freeze record): engines.get would die inside
    derived.py with a traceback, and a fingerprint of a plant that cannot be built
    is no fingerprint (22 October 2026, build step 2 P5; amendment B7). The CLI
    below keeps every registered plant among its choices (engines.known()), so
    that a fingerprint can be asked of any of them, and refuses this one by name."""
    import derived
    import engines
    if not engines.calibrated(name):
        spec = engines.read_spec(engines.PLANTS[name][0])["_meta"]
        raise SystemExit(f"fingerprint.py: plant {name!r} is not calibrated yet: no {spec['derived']}"
                         + (f" or no {spec['freeze']}" if "freeze" in spec else "")
                         + f". Make it with: {derived._maker(os.path.join(HERE, spec['derived']))}")


if __name__ == "__main__":
    import argparse
    import engine_env
    import engines
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True, choices=engines.known())
    ap.add_argument("--protocol", default="phase-d", choices=("phase-d", "d2", "d34"))
    ap.add_argument("--preview-h-s", type=float, default=engine_env.PREVIEW_H_S,
                    help="the sighted agent's H, s (row 117; default %(default)s)")
    ap.add_argument("--blind", action="store_true", help="the blinded arm's block: preview_h_s null")
    ap.add_argument("--reward-knock", choices=("in", "out"), default="in",
                    help="the reward's knock option (row 113 (5)); default 'in', X1's")
    a = ap.parse_args()
    refuse_uncalibrated(a.engine)
    # every environment this tree builds runs the 0-D cycle model (backend_of), in training and in
    # scoring (row 136)
    print(format_block(plant_fingerprint(a.protocol, plant=engines.get(a.engine), train_backend=BACKEND_CYCLE,
                                         score_backend=BACKEND_CYCLE,
                                         preview_h_s=None if a.blind else a.preview_h_s,
                                         reward_knock=a.reward_knock == "in"),
                       "PLANT FINGERPRINT (live)"))
    sys.exit(0)

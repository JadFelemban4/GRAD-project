"""epa_roads.py -- decision 34's test roads: the roads module of section I, rows 94-103.

    python epa_roads.py control --jobs J               roads_ceiling.control, the B58's locked-climb control,
    python epa_roads.py sweep --jobs J                 roads_ceiling.sweep, row 101's sweep before the draw, and
    python epa_roads.py timing --jobs J                roads_ceiling.timing, one 900 s road timed (mistake 22),
                                                      each written by roads_ceiling.write_record to
                                                      results/EPA_ROADS/<name>.json and .txt
    python epa_roads.py smoke --synthetic-seed N [--out DIR] [--jobs J] [--with-redraw] [--full]
                                                      the whole chain on a SYNTHETIC seed (an int below
                                                      2**32), 2 roads, the B58 and the Ford, r = 1.5, no
                                                      companions; --full: the real draw's path on 1 road,
                                                      all four engines, every variant and reading, with
                                                      roads_ceiling.report; writes only under DIR (default a
                                                      new temporary folder), which must lie outside the
                                                      repository; J defaults to 4
    python epa_roads.py commitment                    a fresh private integer of 256 bits and its hash line
                                                      (row 96), printed for the one person who runs it
    python epa_roads.py draw --reveal-g A --reveal-j B --roads-commit SHA --jobs J [--note TEXT]
                                                      the single draw (row 96): results/EPA_ROADS/roads.json;
                                                      SHA is the roads commit as announced before the reveal;
                                                      a later attempt (after a crash or a coding-defect stop)
                                                      needs --note, naming the defect and its fix commits
    python epa_roads.py recheck --summary results/EPA_VALIDATION/summary.json --dropped LIST --jobs J [--out FILE]
    python epa_roads.py redraw --summary results/EPA_VALIDATION/summary.json --dropped LIST --jobs J [--note TEXT]
                                                      after Run 2 (rows 95, 97, 98): the C5 re-check, and the
                                                      redraws written once to results/EPA_ROADS/redraws.json;
                                                      both log a start line before they compute anything and
                                                      an outcome line after (row 96)

Every subcommand installs an audit hook first (install_guard): it refuses any open of logs/epa*, of
data/engines/<id>/epa_*, of results/EPA_VALIDATION (recheck and redraw are let open exactly
results/EPA_VALIDATION/summary.json, and no other path given as --summary) and of any .csv, and it lists
every repository file opened, which the records carry with roads_ceiling's workers' own list.

THE DRAW'S REFUSALS (rows 96, 97, 102, 103 (3); the integrity review of 30 October 2026). Before it
writes anything the draw refuses unless: both hash lines are set in one roads commit and the roads
commit announced before the reveal is that commit; roads.json is absent and was never committed;
the tree is clean and HEAD is in origin's GRA-test as `git ls-remote` reads it; the attempts log was
never deleted or rewritten in HEAD's history; no earlier attempt drew a set or stopped for a reason
that is not a coding defect; the first attempt runs on the roads commit itself (HEAD is the roads
commit), and a later one follows a crash or a coding-defect stop and carries a note; the plants are the
frozen ones (each EPA engine's plant_sha is its freeze.json's, its engine_sha its complete.json's, its
tau complete.json's e6_row4.frozen.tau_s exactly; the B58's plant_sha is 865f8e7b7e5c2dbe) and the
versions are freeze.json's. A hashed file that changes while the draw runs is found before the
ceilings print, before the last identity and at the end.

WHAT STAYS OUT OF IT (row 121). Every module this one imports at any depth is hashed, step_record.py
among them through evaluate.py, so nothing later is written here or in them before the last redraw is
recorded: the tightenings code goes in epa_tightenings.py, which imports this module and which no hashed
module imports; step_record's CVT branch comes after the redraws (ORDER step 12a); the training wrapper is
a new module. ORDER's check before every commit names the step-2 files one by one, not `epa_*.py`.

WHAT THIS MODULE OWNS (rows 95-103). The generator of row 101, which takes no vehicle (row 95 (1));
the slots and their global index k; the four streams of row 96 and the training share's; the
replacement loop at the first draw (row 101) with its climb tests, C5 at 1.9 % with a gated step on
every car and row 98's two checks; the reports that discard nothing (decision 40's CVT diagnostic on the
Honda's car, the contract's coverage flags); the neutral-action identities in row 98's order; the commit
and reveal (row 96); the attempts log (row 96), whose first entry is the draw's first write; the records
of row 97, roads.json written once and redraws.json, and the refusal of a re-check or a redraw when any
hashed file, version, plant_sha or engine_sha differs from roads.json's.

WHAT IT DOES NOT OWN. The ceilings, their companions, tau and the control are roads_ceiling.py's (the
interface of the roads step: roads_ceiling.ceilings, passes_T, slot_candidate_ceilings, report, tau_s,
control); this module calls them by that interface and records what they return.

THE GENERATOR IMPORTS NOTHING THAT DESCRIBES A CAR. generate() and practice's layout run on NumPy and
the standard library alone. The frozen twenty's seeds and weights are read from evaluate.py's EPISODES
literal as text (frozen_episodes, ast.literal_eval), because importing evaluate imports random_road,
which builds the B58 at import. The one constant the generator shares with the plant, the 8 s ramp, is
held here as RAMP_S and checked equal to engine_env.GRADE_RAMP_S, with the speed profile and the ramp's
expression checked against make_grade_climb element for element (check_engine_env), before any draw.
Two definitions of one road shape is how this project acquires drift (mistake 11), so the check is not
optional: first_draw runs it first. The practice set draws its preference weights as
SupervisoryTunerEnv.reset draws them, so practice_roads reads engine_env's two TRACK_W constants; it
still reads no vehicle.

A CYCLE IN A ROAD AND A CYCLE IN THE ENVIRONMENT. A road's cycle is JSON: t, v_mps, grade and t_amb as
lists of floats (the interface of the roads step), p_baro and humidity as numbers. The environment
reads t_amb as one number (engine_env.py SupervisoryTunerEnv._obs and step), so env_cycle(road) gives
the environment's form, and refuses a t_amb that is not constant.
"""
import ast
import contextlib
import copy
import datetime
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import traceback

import numpy as np

REPO = os.path.dirname(os.path.abspath(__file__))
MODULE_REL = "epa_roads.py"

# ------------------------------------------------------------------ the records' paths (row 97)
ROADS_DIR_REL = "results/EPA_ROADS"
ROADS_REL = "results/EPA_ROADS/roads.json"
REDRAWS_REL = "results/EPA_ROADS/redraws.json"
ATTEMPTS_REL = "results/EPA_ROADS/attempts.jsonl"
CONTRACT_FILES = ("results/ENGINE_THRESHOLDS.json", "results/ENGINE_THRESHOLDS.md")
TIGHTENINGS_REL = "results/EPA_TIGHTENINGS.json"
ROADS_SCHEMA = "epa-roads/1"
REDRAWS_SCHEMA = "epa-redraws/1"

# ------------------------------------------------------------------ the design (row 101), DESIGN values
N_ROADS = 20
DURATION_S = 900.0
DT = 1.0
V_KMH = 130.0
SPEED_RAMP_S = 20.0           # 0 -> 130 km/h over the first 20 s, as make_grade_climb builds it
T_AMB_K = 315.0
P_BARO_KPA = 101.3
HUMIDITY = 0.012
LEAD_LO, LEAD_HI = 150, 211   # integers(150, 211): a flat lead-in of 150-210 s
L_LO, L_HI = 67, 86           # integers(67, 86): L of 67-85 s, onset to the start of the ramp-down
GRADE_LO, GRADE_HI = 0.10, 0.12
G_LO, G_HI = 50, 151          # integers(50, 151): the next climb starts at s + L + G
TAIL_S = 60.0                 # a climb is added only if its ramp-down ends at least 60 s before 900 s
RAMP_S = 8.0                  # engine_env.GRADE_RAMP_S (row 98 (a)); check_engine_env holds them equal
REPLACEMENTS = 100            # decision 76's bound, applied at the first draw (row 101)
C5_MARGIN = 0.019             # C5 at 1.9 % on every car (MD:1374, :1401-1405), a fraction
REDRAW_CAP = 3                # thresholds.contract.REDRAW_CAP (MD:1387); check_engine_env holds them equal
REDRAW_DISCARDS = 100         # thresholds.contract.REDRAW_DISCARDS

# ------------------------------------------------------------------ the streams (row 96)
STREAM_REPLACE = 0x1D         # slot k's replacement grades at the first draw: default_rng([roads_seed, 0x1D, k])
STREAM_REDRAW = 0xC5          # slot k's redraws after Run 2 (thresholds.contract.REDRAW_STREAM_TAG)
STREAM_PRACTICE = 0x50        # the ten practice roads: default_rng([roads_seed, 0x50])
STREAM_TRAINING = 0x7A        # the training share (row 116): default_rng([roads_seed, 0x7A, seed])
N_PRACTICE = 10
PRACTICE_SEEDS = tuple(range(4000, 4010))

ENGINES = ("b58", "mazda_25t", "honda_l15b7", "ford_27tt")
EPA_ENGINES = ("mazda_25t", "honda_l15b7", "ford_27tt")
CVT_ENGINE = "honda_l15b7"
CVT_GATED_BRANCHES = ("kickdown", "power-limited")   # MD:1236: "at every gated step on either branch"
NEVER_DROPPED = "b58"         # MD:1587-1592; row 95 (2)
B58_PLANT_SHA = "865f8e7b7e5c2dbe"   # row 102: the B58's tau is computed on this plant_sha, never again
CALIBRATION_REL = "results/EPA_CALIBRATION"
SUMMARY_REL = "results/EPA_VALIDATION/summary.json"   # the one held-out record recheck and redraw read
SYNTHETIC_SEED_LIMIT = 2 ** 32       # a SYNTHETIC seed is below it; roads_seed is a 60-bit integer
ROADS_SEED_LIMIT = 16 ** 15          # int(sha256(...).hexdigest()[:15], 16) is below it (row 96)
EPISODE_STEPS_NOTE = ("the environment truncates at k >= n - 1 (engine_env.py, step), so a road of n = 900 "
                      "samples is an episode of 899 steps; row 101 writes 900")

# What the draw asks of roads_ceiling (row 103 (1)): every variant it computes (roads_ceiling.ALL_VARIANTS:
# current-grade, (a), (b), (a_b), the neutral policy for evaluate.py's form, (c) and section G's replay)
# in both readings. The smoke run asks for the primary pair only (current-grade and (a), no knock), at r = 1.5.
DRAW_VARIANTS = ("cg", "a", "b", "a_b", "neutral", "c", "G")
DRAW_READINGS = ("noknock", "knock")
SMOKE_VARIANTS = ("cg", "a")
SMOKE_READINGS = ("noknock",)
SMOKE_ENGINES = ("b58", "ford_27tt")
SMOKE_RATIOS = (1.5,)
SMOKE_N_ROADS = 2

# ------------------------------------------------------------------ the commit and reveal (row 96)
# Each line is the sha256 of one person's private integer a, as
# hashlib.sha256(str(a).encode("ascii")).hexdigest(), 64 lowercase hex digits. Both are recorded in the
# roads commit, in that one commit, and never changed afterwards: find_roads_commit refuses a history in
# which they were set in two commits or changed. None until Ghassan and Jad supply them. The integer is
# at least 2**128 (MIN_PRIVATE_INT), so that its hash cannot be searched: `python epa_roads.py
# commitment` draws one of 256 bits with the secrets module and prints it with its line.
COMMITMENT_G = None
COMMITMENT_J = None
MIN_PRIVATE_INT = 2 ** 128
REMOTE_NAME = "origin"
REMOTE_BRANCH = "GRA-test"
_HEX64 = re.compile(r"[0-9a-f]{64}")
_SHA40 = re.compile(r"[0-9a-f]{40}")
_CANONICAL_INT = re.compile(r"(0|[1-9][0-9]*)")

# The modules row 97 names beside the import closure (every one is also reached by it today; the list
# keeps them hashed if an import moves).
NAMED_MODULES = ("roads_ceiling.py", "check_premise.py", "random_road.py", "epa_stats.py", "k3_knee.py",
                 "epa_coefficients.py", "evaluate.py")


class Refused(Exception):
    """A precondition does not hold: nothing was drawn and nothing was written."""


class RoadsStop(Exception):
    """The roads stop. A stop that is not a coding defect (row 96: a reveal that does not match) ends the
    roads step as row 103 (3) ends it: draw() refuses every later attempt."""


class CodingDefect(RoadsStop):
    """A stop for a coding defect (row 98: an identity difference, a clip contact, a run that stops; a
    hashed file changed while the draw ran): fixed in its own commit, after which the roads are drawn
    again from the same roads_seed, the first attempt's record kept (rows 96, 98)."""


# =====================================================================================================
# The audit guard (as the probe's lib.py.txt installs it)
# =====================================================================================================
OPENED = set()
_GUARD = {"installed": False, "allow": frozenset()}


def _norm(path):
    return os.path.normcase(os.path.abspath(path))


def refused_path(path):
    """Whether the guard refuses `path`: logs/epa*, data/engines/<id>/epa_*, results/EPA_VALIDATION, any .csv."""
    s = os.path.abspath(path).replace("\\", "/").lower()
    return ("logs/epa" in s or re.search(r"data/engines/[^/]+/epa_", s) is not None
            or "epa_validation" in s or s.endswith(".csv"))


def _audit(event, args):
    if event != "open" or not args:
        return
    p = args[0]
    if isinstance(p, int) or p is None:
        return
    try:
        s = os.fsdecode(p) if not isinstance(p, str) else p
    except Exception:
        return
    n = _norm(s)
    if n not in _GUARD["allow"] and refused_path(s):
        raise PermissionError(f"epa_roads guard: refused to open {s}")
    root = os.path.normcase(REPO) + os.sep
    if n.startswith(root):
        rel = os.path.relpath(os.path.abspath(s), REPO).replace("\\", "/")
        if not (rel.startswith(".venv/") or "/__pycache__/" in f"/{rel}" or rel.startswith(".git/")):
            OPENED.add(rel)


def install_guard(allow):
    """Install the audit hook once per process; `allow` is the exact set of paths it lets open although
    refused_path names them (recheck and redraw: the one summary file given). A hook cannot be removed."""
    _GUARD["allow"] = frozenset(_norm(p) for p in allow)
    if not _GUARD["installed"]:
        sys.addaudithook(_audit)
        _GUARD["installed"] = True


def _worker_init(allow):
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    install_guard(allow)


def summary_path_allowed(path, *, root):
    """The --summary of recheck and redraw, refused before the guard is installed unless it is exactly
    <root>/results/EPA_VALIDATION/summary.json: the guard lets open only that one held-out record (the
    integrity review: an --summary naming a table would otherwise pass it)."""
    if _norm(path) != _norm(os.path.join(root, SUMMARY_REL)):
        raise Refused([f"--summary {path!r} is not {SUMMARY_REL}: the only held-out record the re-check and "
                       "the redraws read"])
    return os.path.abspath(path)


# =====================================================================================================
# The generator (rows 95 (1) and 101): no vehicle
# =====================================================================================================
def frozen_episodes(*, root):
    """evaluate.EPISODES as evaluate.py holds the literal, read as text (no import: importing evaluate
    builds the B58). test_epa_roads checks it equals the imported tuple."""
    with open(os.path.join(root, "evaluate.py"), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "EPISODES"
                                                for t in node.targets):
            return tuple((int(s), tuple(float(x) for x in w)) for s, w in ast.literal_eval(node.value))
    raise KeyError("evaluate.py holds no EPISODES literal")


def layout(rng):
    """One road's draws in row 101's order from `rng` (anything with integers and uniform): the lead-in,
    then L, g and G for each climb in turn. A climb is kept only if its ramp-down ends at least TAIL_S
    before DURATION_S (s + L + RAMP_S <= 840); the draws of the first climb that does not fit are made
    and discarded, and the rest of the road is flat. Returns (lead_s, [(s, L, g, G), ...], discarded)."""
    lead = int(rng.integers(LEAD_LO, LEAD_HI))
    s = lead
    climbs = []
    while True:
        L = int(rng.integers(L_LO, L_HI))
        g = float(rng.uniform(GRADE_LO, GRADE_HI))
        G = int(rng.integers(G_LO, G_HI))
        if s + L + RAMP_S > DURATION_S - TAIL_S:
            return lead, climbs, (L, g, G)
        climbs.append((s, L, g, G))
        s = s + L + G


def time_and_speed():
    """t and v_mps of every road: make_grade_climb's expressions at 900 s, dt 1.0 and 130 km/h."""
    n = int(DURATION_S / DT)
    t = np.arange(n) * DT
    v = np.full(n, V_KMH / 3.6)
    v[:int(SPEED_RAMP_S / DT)] = np.linspace(0.0, V_KMH / 3.6, int(SPEED_RAMP_S / DT))
    return t, v


def climb_profile(t, s, L, g):
    """One climb: up over RAMP_S from s (make_grade_climb's expression with s for 180), g until s + L,
    down over RAMP_S from s + L."""
    up = np.clip((t - s) / RAMP_S, 0.0, 1.0)
    down = np.clip(1.0 - (t - (s + L)) / RAMP_S, 0.0, 1.0)
    return g * np.minimum(up, down)


def grade_from_climbs(t, climbs):
    out = np.zeros(len(t))
    for c in climbs:
        out = np.maximum(out, climb_profile(t, float(c["onset_s"]), float(c["L_s"]), float(c["grade"])))
    return out


def _climb_record(slot, s, L, g, G):
    return {"slot": int(slot), "onset_s": float(s), "L_s": float(L), "grade": float(g), "gap_s": float(G),
            "first_step": int(round(s / DT)), "last_step": int(round((s + L + RAMP_S) / DT))}


def make_road(*, k, episode_seed, weights, lead, climbs, discarded, first_slot):
    """A road dict of the roads step's interface from one layout; slots numbered from first_slot."""
    t, v = time_and_speed()
    crec = [_climb_record(first_slot + i, s, L, g, G) for i, (s, L, g, G) in enumerate(climbs)]
    grade = grade_from_climbs(t, crec)
    n = len(t)
    return {"k": k, "episode_seed": None if episode_seed is None else int(episode_seed),
            "weights": None if weights is None else [float(w) for w in weights], "dt": DT,
            "cycle": {"t": [float(x) for x in t], "v_mps": [float(x) for x in v],
                      "grade": [float(x) for x in grade], "t_amb": [T_AMB_K] * n, "p_baro": P_BARO_KPA,
                      "humidity": HUMIDITY},
            "climbs": crec, "flat_slots": [],
            "draws": {"lead_s": int(lead), "climbs": [{"L_s": int(L), "grade": float(g), "gap_s": int(G)}
                                                       for _, L, g, G in climbs],
                      "discarded": {"L_s": int(discarded[0]), "grade": float(discarded[1]),
                                    "gap_s": int(discarded[2])}}}


def generate(rng_seed_material, *, n_roads=N_ROADS, episodes=None):
    """Row 101's roads from numpy.random.default_rng(rng_seed_material) (roads_seed at the draw): roads
    0..n_roads-1 in order, road k paired with episodes[k]'s seed and weights (evaluate.EPISODES, read as
    text, when None). Reads no vehicle and imports no plant module (row 95 (1))."""
    eps = frozen_episodes(root=REPO) if episodes is None else tuple(episodes)
    if n_roads > len(eps):
        raise ValueError(f"{n_roads} roads, {len(eps)} frozen episodes to pair them with")
    rng = np.random.default_rng(rng_seed_material)
    roads, slot = [], 0
    for k in range(n_roads):
        lead, climbs, discarded = layout(rng)
        seed, w = eps[k]
        roads.append(make_road(k=k, episode_seed=seed, weights=w, lead=lead, climbs=climbs,
                               discarded=discarded, first_slot=slot))
        slot += len(climbs)
    return roads


def practice_weights(rng):
    """One preference draw exactly as SupervisoryTunerEnv.reset draws it (engine_env.py, reset), as
    float64 values (the environment stores them as float32)."""
    import engine_env as E
    w_track = float(E.TRACK_W_MIN + (E.TRACK_W_MAX - E.TRACK_W_MIN) * rng.random())
    w_rest = rng.dirichlet(np.ones(2)) * (1.0 - w_track)
    return [w_track, float(w_rest[0]), float(w_rest[1])]


def practice_roads(roads_seed):
    """Row 96's ten practice roads from default_rng([roads_seed, 0x50]): each road's layout, then its
    weights from the same stream; no replacement loop; episode seeds 4000-4009. Reads no vehicle."""
    rng = np.random.default_rng([int(roads_seed), STREAM_PRACTICE])
    out, slot = [], 0
    for i in range(N_PRACTICE):
        lead, climbs, discarded = layout(rng)
        w = practice_weights(rng)
        out.append(make_road(k=i, episode_seed=PRACTICE_SEEDS[i], weights=w, lead=lead, climbs=climbs,
                             discarded=discarded, first_slot=slot))
        slot += len(climbs)
    return out


def training_share_road(roads_seed, seed):
    """Row 116's training share: one road of row 101's generator from default_rng([roads_seed, 0x7A,
    seed]), no replacement loop. Its weights are None: the environment draws its own at reset."""
    rng = np.random.default_rng([int(roads_seed), STREAM_TRAINING, int(seed)])
    lead, climbs, discarded = layout(rng)
    return make_road(k=None, episode_seed=seed, weights=None, lead=lead, climbs=climbs, discarded=discarded,
                     first_slot=0)


def replacement_rng(roads_seed, k):
    return np.random.default_rng([int(roads_seed), STREAM_REPLACE, int(k)])


def redraw_rng(roads_seed, k):
    return np.random.default_rng([int(roads_seed), STREAM_REDRAW, int(k)])


def slots_of(roads):
    """Every slot in the recorded order (roads in order, a road's slots by first step), flat ones
    included: [(road index, slot record)]."""
    out = []
    for i, r in enumerate(roads):
        for c in sorted(list(r["climbs"]) + list(r["flat_slots"]), key=lambda c: c["first_step"]):
            out.append((i, c))
    return out


def env_cycle(road):
    """The environment's cycle for a road: NumPy arrays, t_amb one number (refused if not constant)."""
    c = road["cycle"]
    ta = np.asarray(c["t_amb"], dtype=float)
    if ta.ndim and not np.all(ta == ta.flat[0]):
        raise ValueError("env_cycle: the road's ambient is not constant; the environment reads one t_amb")
    return {"t": np.asarray(c["t"], dtype=float), "v_mps": np.asarray(c["v_mps"], dtype=float),
            "grade": np.asarray(c["grade"], dtype=float), "t_amb": float(ta.flat[0] if ta.ndim else ta),
            "p_baro": float(c["p_baro"]), "humidity": float(c["humidity"])}


def arrays_sha256(roads):
    h = hashlib.sha256()
    for r in roads:
        for key in ("t", "v_mps", "grade", "t_amb"):
            h.update(np.asarray(r["cycle"][key], dtype=np.float64).tobytes())
    return h.hexdigest()


def check_engine_env():
    """The one road shape this module shares with the plant, and the contract's redraw constants: RAMP_S
    is engine_env.GRADE_RAMP_S; t, v_mps, t_amb, p_baro and humidity are make_grade_climb's at this
    design; a climb from 180 s with no ramp-down in the road is make_grade_climb's grade element for
    element; the redraw tag, cap and discard bound are the contract's. Raises on any difference."""
    import engine_env as E
    from thresholds import contract as K
    problems = []
    if RAMP_S != E.GRADE_RAMP_S:
        problems.append(f"RAMP_S {RAMP_S} is not engine_env.GRADE_RAMP_S {E.GRADE_RAMP_S}")
    for g in (GRADE_LO, 0.11, GRADE_HI):
        ref = E.make_grade_climb(duration=DURATION_S, dt=DT, t_amb=T_AMB_K, grade=g, v_kmh=V_KMH)
        t, v = time_and_speed()
        for key, mine in (("t", t), ("v_mps", v)):
            if not np.array_equal(ref[key], mine):
                problems.append(f"{key} differs from make_grade_climb's at grade {g}")
        if not np.array_equal(ref["grade"], climb_profile(t, 180.0, 10.0 * DURATION_S, g)):
            problems.append(f"the ramp up differs from make_grade_climb's at grade {g}")
        for key, mine in (("t_amb", T_AMB_K), ("p_baro", P_BARO_KPA), ("humidity", HUMIDITY)):
            if ref[key] != mine:
                problems.append(f"{key} {mine} differs from make_grade_climb's {ref[key]}")
    for name, mine in (("REDRAW_STREAM_TAG", STREAM_REDRAW), ("REDRAW_CAP", REDRAW_CAP),
                       ("REDRAW_DISCARDS", REDRAW_DISCARDS)):
        if getattr(K, name) != mine:
            problems.append(f"thresholds.contract.{name} {getattr(K, name)} is not this module's {mine}")
    if REPLACEMENTS != K.REDRAW_DISCARDS:
        problems.append("the first draw's replacement bound is not decision 76's discard bound")
    if problems:
        raise AssertionError("epa_roads.check_engine_env: " + "; ".join(problems))
    return True


# =====================================================================================================
# Row 98's two checks
# =====================================================================================================
def ramp_problems(grade, *, dt):
    """Row 98 (a): every grade change of the road is a linear ramp of RAMP_S (8 steps at dt 1 s) between
    two held grades. Returns the problems, [] when the road passes."""
    g = np.asarray(grade, dtype=float)
    d = np.diff(g)
    n_ramp = int(round(RAMP_S / dt))
    out = []
    nz = np.flatnonzero(d != 0.0)
    if not len(nz):
        return out
    runs, start, prev = [], nz[0], nz[0]
    for i in nz[1:]:
        if i != prev + 1:
            runs.append((start, prev + 1))
            start = i
        prev = i
    runs.append((start, prev + 1))
    for a, b in runs:
        seg = d[a:b]
        if b - a != n_ramp:
            out.append(f"a grade change over steps {int(a)}-{int(b)} lasts {int(b - a)} steps, not {n_ramp}")
        elif not (np.all(np.sign(seg) == np.sign(seg[0])) and np.allclose(seg, seg[0], rtol=1e-9, atol=0.0)):
            out.append(f"the grade change over steps {int(a)}-{int(b)} is not one linear ramp")
    return out


def climb_of(road, slot):
    for c in road["climbs"]:
        if c["slot"] == slot:
            return c
    return None


def extent_problems(slot_record, candidate, reference):
    """Row 98 (b): the candidate's climb fills its slot's recorded extent (MD:1417-1423): a climb of the
    slot's length from the slot's first step to its last, as the generator draws it, joined to the road
    at both ends; the road outside the extent is the reference road's."""
    out = []
    c = climb_of(candidate, slot_record["slot"])
    if c is None:
        return [f"slot {slot_record['slot']}: the candidate holds no climb in it"]
    for key in ("first_step", "last_step", "onset_s", "L_s"):
        if c[key] != slot_record[key]:
            out.append(f"slot {slot_record['slot']}: {key} {c[key]} is not the recorded {slot_record[key]}")
    if out:
        return out
    t = np.asarray(candidate["cycle"]["t"], dtype=float)
    g = np.asarray(candidate["cycle"]["grade"], dtype=float)
    ref = np.asarray(reference["cycle"]["grade"], dtype=float)
    a, b = int(slot_record["first_step"]), int(slot_record["last_step"])
    want = climb_profile(t, float(c["onset_s"]), float(c["L_s"]), float(c["grade"]))
    if not np.array_equal(g[a:b + 1], want[a:b + 1]):
        out.append(f"slot {slot_record['slot']}: the grade over steps {a}-{b} is not the climb's profile")
    if np.any(want[:a] != 0.0) or np.any(want[b + 1:] != 0.0):
        out.append(f"slot {slot_record['slot']}: the climb reaches outside steps {a}-{b}")
    outside = np.ones(len(g), dtype=bool)
    outside[a:b + 1] = False
    if not np.array_equal(g[outside], ref[outside]):
        out.append(f"slot {slot_record['slot']}: the road outside steps {a}-{b} moved")
    if (a > 0 and g[a] != g[a - 1]) or (b + 1 < len(g) and g[b] != g[b + 1]):
        out.append(f"slot {slot_record['slot']}: the climb is not joined to the road at both ends")
    return out


def with_grade(road, slot, grade):
    """The road with slot `slot`'s climb at a new grade, every other value as it stands (a candidate
    filling the slot's recorded extent: same onset, same L)."""
    out = copy.deepcopy(road)
    c = climb_of(out, slot)
    if c is None:
        raise KeyError(f"road {road['k']}: no climb in slot {slot}")
    c["grade"] = float(grade)
    t = np.asarray(out["cycle"]["t"], dtype=float)
    out["cycle"]["grade"] = [float(x) for x in grade_from_climbs(t, out["climbs"])]
    return out


def with_flat(road, slot):
    """The road with slot `slot` made flat: its climb leaves `climbs` (no scored climb there) and its
    record, with its index, goes to `flat_slots` (row 101)."""
    out = copy.deepcopy(road)
    c = climb_of(out, slot)
    if c is None:
        raise KeyError(f"road {road['k']}: no climb in slot {slot}")
    out["climbs"] = [x for x in out["climbs"] if x["slot"] != slot]
    flat = dict(c, grade=0.0, flat=True)
    out["flat_slots"] = sorted(out["flat_slots"] + [flat], key=lambda x: x["first_step"])
    t = np.asarray(out["cycle"]["t"], dtype=float)
    out["cycle"]["grade"] = [float(x) for x in grade_from_climbs(t, out["climbs"])]
    return out


# =====================================================================================================
# C5 and the reports beside it (rows 97, 98)
# =====================================================================================================
_PLANTS = {}


def plant_of(engine_id):
    """engines.get(engine_id), once per process."""
    if engine_id not in _PLANTS:
        import engines as ENG
        _PLANTS[engine_id] = ENG.get(engine_id)
    return _PLANTS[engine_id]


def c5_on_car(plant, road, climb, *, margin):
    """C5 on one scored climb on one car: epa_stats.c5_steps over the climb's first..last step at the
    road's dt, read by epa_stats.c5_climb at `margin` (a fraction) and the contract's thin share."""
    import epa_stats as ES
    from thresholds import contract as K
    steps = ES.c5_steps(plant, env_cycle(road), first=int(climb["first_step"]), last=int(climb["last_step"]),
                        dt=float(road["dt"]))
    return steps, ES.c5_climb(steps, margin=margin, thin_share=K.C5_THIN_SHARE)


def jsonable(x):
    """A result of another module made JSON-able as a record holds it: NumPy scalars and arrays as
    Python values, a NaN or an infinity as None (a record never holds NaN)."""
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, np.ndarray):
        return [jsonable(v) for v in x.tolist()]
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        return float(x) if np.isfinite(x) else None
    return x


def _jf(x):
    if x is None:
        return None
    x = float(x)
    return x if np.isfinite(x) else None


def c5_json(steps, out, *, with_steps):
    gm = [m for s in steps if s.gated for (_, m, gates) in s.margins if gates]
    d = {"outcome": out.outcome, "case": {"fails": 1, "thinly_checked": 2, "passes": 3}[out.outcome],
         "gated_share": _jf(out.gated_share), "transition_share": _jf(out.transition_share),
         "failing_steps": [int(k) for k in out.failing_steps], "thin": bool(out.thin),
         "n_steps": int(out.n_steps), "n_gated": int(out.n_gated),
         "smallest_gated_margin": _jf(min(gm)) if gm else None}
    if with_steps:
        d["steps"] = [{"k": int(s.k), "transition": bool(s.transition), "gated": bool(s.gated), "held": s.held,
                       "margins": [[a, _jf(b), bool(c)] for a, b, c in s.margins],
                       "bar_rpm_margin": _jf(s.bar_rpm_margin), "bar_rpm_margin_frac": _jf(s.bar_rpm_margin_frac),
                       "no_margin_case": s.no_margin_case, "v_mps": _jf(s.v_mps), "grade": _jf(s.grade),
                       "demand_nm": _jf(s.demand_nm), "rpm": _jf(s.rpm)} for s in steps]
    return d


def c5_failure(engine_id, out, *, margin):
    """The test a climb fails on one car, or None: case (1) at `margin`, or no gated step (MD:1349-1353)."""
    if out.outcome == "fails":
        return f"C5 case (1) at {margin * 100:.4g} % on {engine_id}"
    if out.n_gated == 0:
        return f"no gated step on {engine_id}"
    return None


def climb_tests(slot_record, candidate, reference, *, plants, gating, margin):
    """The first draw's climb tests on a candidate in its slot (rows 98 and 101): row 98 (a) and (b), then
    C5 at `margin` with a gated step on every car in `gating`. C5 is computed and recorded on every car of
    `plants` (row 95 (2): a dropped engine's outcome is still recorded). Returns (failed tests, {car: c5})."""
    failed = []
    rp = ramp_problems(candidate["cycle"]["grade"], dt=float(candidate["dt"]))
    if rp:
        failed.append({"test": "row 98 (a): every grade change an 8 s ramp", "problems": rp})
    ep = extent_problems(slot_record, candidate, reference)
    if ep:
        failed.append({"test": "row 98 (b): the candidate fills its slot's recorded extent", "problems": ep})
    c5 = {}
    if not ep:
        climb = climb_of(candidate, slot_record["slot"])
        for e, p in plants.items():
            steps, out = c5_on_car(p, candidate, climb, margin=margin)
            c5[e] = (steps, out)
            why = c5_failure(e, out, margin=margin)
            if why and e in gating:
                failed.append({"test": why, "failing_steps": [int(k) for k in out.failing_steps]})
    return failed, c5


def replacement_loop(roads, roads_seed, *, plants, gating, log):
    """Row 101's replacement at the first draw. Each slot in the recorded order: its climb as drawn, and
    if it fails a climb test, a new grade on [0.10, 0.12] at the same L from default_rng([roads_seed,
    0x1D, k]), at most REPLACEMENTS times; after that the slot is flat road, keeps its index, and is
    reported. Returns (final roads, slot records, {car: {slot: c5 json with steps}} for the final climbs)."""
    roads = copy.deepcopy(roads)
    records, final_c5 = [], {e: {} for e in plants}
    for i, slot0 in slots_of(roads):
        k = slot0["slot"]
        slot_record = {key: slot0[key] for key in ("slot", "onset_s", "L_s", "first_step", "last_step")}
        reference = roads[i]
        cands = []
        failed, c5 = climb_tests(slot_record, reference, reference, plants=plants, gating=gating,
                                 margin=C5_MARGIN)
        cands.append({"source": "first draw", "grade": float(slot0["grade"]), "failed": failed,
                      "c5": {e: c5_json(*v, with_steps=False) for e, v in c5.items()}})
        accepted, c5_acc = (reference, c5) if not failed else (None, None)
        if failed:
            rng = replacement_rng(roads_seed, k)
            for n in range(REPLACEMENTS):
                g = float(rng.uniform(GRADE_LO, GRADE_HI))
                cand = with_grade(reference, k, g)
                failed, c5 = climb_tests(slot_record, cand, reference, plants=plants, gating=gating,
                                         margin=C5_MARGIN)
                cands.append({"source": f"0x1D draw {n + 1}", "grade": g, "failed": failed,
                              "c5": {e: c5_json(*v, with_steps=False) for e, v in c5.items()}})
                if not failed:
                    accepted, c5_acc = cand, c5
                    break
        if accepted is None:
            roads[i] = with_flat(reference, k)
            outcome = "flat"
            log(f"slot {k} (road {roads[i]['k']}): {len(cands) - 1} replacement grades failed; made flat, index kept")
        else:
            roads[i] = accepted
            outcome = "accepted" if len(cands) == 1 else "replaced"
            if outcome == "replaced":
                log(f"slot {k} (road {roads[i]['k']}): grade {cands[0]['grade']:.6f} failed "
                    f"{[f['test'] for f in cands[0]['failed']]}; replaced by 0x1D draw {len(cands) - 1}, "
                    f"grade {cands[-1]['grade']:.6f}")
            for e, (steps, out) in c5_acc.items():
                final_c5[e][str(k)] = c5_json(steps, out, with_steps=True)
        records.append(dict(slot_record, road=int(roads[i]["k"]), outcome=outcome,
                            final_grade=None if accepted is None else float(climb_of(accepted, k)["grade"]),
                            thin_on=sorted(e for e, (_, o) in (c5_acc or {}).items() if o.thin),
                            candidates=cands))
    return roads, records, final_c5


def cvt_diagnostics(plant, road, climb, steps, run, *, margin):
    """Decision 40's diagnostic (MD:1230-1242) at every gated step of one scored climb on the CVT car:
    epa_stats.cvt_diagnostic with the step's speed and the tractive force the environment gave the box
    at that step (the neutral run's force_n). Reported, never gated."""
    import epa_stats as ES
    out = []
    for s in steps:
        if not s.gated:
            continue
        if float(run["v_mps"][s.k]) != float(s.v_mps):
            raise AssertionError(f"cvt_diagnostics: step {s.k}: the run's speed is not C5's")
        d = ES.cvt_diagnostic(plant, v_mps=float(s.v_mps), force_n=float(run["force_n"][s.k]), margin=margin)
        out.append({"k": int(s.k), "branch": d["branch"], "connected": bool(d["connected"]),
                    "stays_on_branch": bool(d["stays_on_branch"]), "cases": d["cases"]})
    res = {"climb": int(climb["slot"]), "margin": margin, "steps": out}
    res.update(cvt_totals([res]))       # counted on the kickdown and power-limited branches, every branch beside
    return res


def coverage_flags(engine_id, road, climb, run, *, coverage):
    """The coverage flag of row 98 (MD:579-583) for one scored climb on one EPA car, from the contract's
    committed engines.<id>.coverage (calibration_fired and calibration_hot, per 20 kPa MAP band, its
    speed range), on the neutral run's MAP and engine speed at the climb's steps; with row 101's three
    counts beside it (MD:749-755). Reported, discards nothing."""
    import epa_stats as ES
    ks = range(int(climb["first_step"]), int(climb["last_step"]) + 1)

    def outside(bands):
        n = 0
        for k in ks:
            b = bands.get(ES.map_band_key(run["map_kpa"][k]))
            rng = None if b is None else b.get("speed_rpm")
            if rng is None or not (rng[0] <= run["rpm"][k] <= rng[1]):
                n += 1
        return n
    fired, hot = outside(coverage["calibration_fired"]), outside(coverage["calibration_hot"])
    v = np.asarray(road["cycle"]["v_mps"], dtype=float)[list(ks)] * 3.6
    hold = float(climb["L_s"]) - RAMP_S
    return {"engine": engine_id, "climb": int(climb["slot"]), "steps": len(ks),
            "steps_outside_calibration_fired": fired, "steps_outside_calibration_hot": hot,
            "covered_fired": fired == 0, "covered_hot": hot == 0,
            "map_kpa": [float(min(run["map_kpa"][k] for k in ks)), float(max(run["map_kpa"][k] for k in ks))],
            "rpm": [float(min(run["rpm"][k] for k in ks)), float(max(run["rpm"][k] for k in ks))],
            "steps_above_115_kmh": int(np.count_nonzero(v > 115.0)), "full_grade_hold_s": hold,
            "hold_longer_than_30_s": hold > 30.0,
            "charge_temperature": "at 42 C ambient, above every EPA map's intake temperature (MD:749-752; "
                                  "stated by the contract, not computed here)",
            "verdict": "on plants extrapolated in speed, hold duration and charge temperature"}


# =====================================================================================================
# The neutral-action identities (row 98)
# =====================================================================================================
def _identity_task(task):
    engine_id, road, keep = task
    import k3_knee as K3
    res = {"engine": engine_id, "road": road["k"], "error": None}
    try:
        p = plant_of(engine_id)
        run = K3.neutral_run(p, cycle=env_cycle(road), seed=int(road["episode_seed"]),
                             weights=tuple(float(w) for w in road["weights"]))
        idt = K3.neutral_identity(run, ecu=p.engine.ecu)
        res.update(identity=idt.as_json(), holds=bool(idt.holds))
        if keep:
            res["arrays"] = {"rpm": [float(x) for x in run.rpm], "map_kpa": [float(x) for x in run.map_kpa],
                             "v_mps": [float(x) for x in run.v_mps], "force_n": [float(x) for x in run.force_n]}
    except Exception as exc:
        res.update(identity=None, holds=False, error=f"{type(exc).__name__}: {exc}")
    res["opened"] = sorted(OPENED)
    return res


def _locked_task(engine_id):
    import k3_knee as K3
    p = plant_of(engine_id)
    run = K3.locked_neutral_run(p)
    idt = K3.neutral_identity(run, ecu=p.engine.ecu)
    return {"engine": engine_id, "road": "locked climb", "identity": idt.as_json(), "holds": bool(idt.holds),
            "error": None, "opened": sorted(OPENED)}


def pool_map(fn, tasks, *, jobs):
    """fn over tasks, in-process at jobs 1, else in a spawn pool of min(jobs, len(tasks)) workers, each
    with the guard installed."""
    tasks = list(tasks)
    if jobs <= 1 or len(tasks) <= 1:
        return [fn(t) for t in tasks]
    import multiprocessing as mp
    with mp.get_context("spawn").Pool(min(jobs, len(tasks)), initializer=_worker_init,
                                      initargs=(tuple(_GUARD["allow"]),)) as pool:
        return pool.map(fn, tasks, chunksize=1)


def identities(roads, *, engines, jobs, keep_arrays, label):
    """The identity on every engine's arrays of every road; a difference, a clip contact or a run that
    stops is a coding defect and stops the roads (row 98). Returns ({road k: {engine: result}}, opened)."""
    res = pool_map(_identity_task, [(e, r, keep_arrays) for r in roads for e in engines], jobs=jobs)
    out, opened, bad = {}, set(), []
    for x in res:
        opened.update(x.pop("opened"))
        out.setdefault(str(x["road"]), {})[x["engine"]] = x
        if not x["holds"]:
            bad.append(f"road {x['road']} on {x['engine']}: {x['error'] or x['identity']}")
    if bad:
        raise CodingDefect(f"the neutral-action identity fails ({label}), a coding defect (row 98): " + "; ".join(bad))
    return out, opened


# =====================================================================================================
# The hashes (row 97)
# =====================================================================================================
def _imports_of(path):
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
            names.append(node.module)
            names += [f"{node.module}.{a.name}" for a in node.names]
    return names


def _shadowed(base):
    """What Python would import instead of base + ".py": a regular package base/__init__.py, or an
    extension module beside it, both of which the import system takes before a source module."""
    import importlib.machinery as M
    out = [base + s for s in M.EXTENSION_SUFFIXES if os.path.isfile(base + s)]
    if os.path.isfile(os.path.join(base, "__init__.py")):
        out.append(os.path.join(base, "__init__.py"))
    return out


def _module_files(name, root):
    """The project files a module name resolves to under `root` (its packages' __init__.py included).
    Refused when a package or an extension module of the same name sits beside a source module: the
    import system would load that one, while the hashes name the .py (the integrity review)."""
    parts = name.split(".")
    out = []
    for i in range(1, len(parts) + 1):
        base = os.path.join(root, *parts[:i])
        if os.path.isfile(base + ".py"):
            sh = _shadowed(base)
            if sh:
                raise Refused([f"{'/'.join(parts[:i])}.py is shadowed by {[os.path.relpath(x, root) for x in sh]}: "
                               "Python imports that, not the hashed source"])
            out.append("/".join(parts[:i]) + ".py")
            break
        if os.path.isfile(os.path.join(base, "__init__.py")):
            out.append("/".join(parts[:i]) + "/__init__.py")
        else:
            break
    return out


def import_closure(entry, *, root):
    """Every project module `entry` imports at any depth, at any nesting (an import inside a function
    counts), as repository-relative paths, `entry` included; modules outside `root` are not listed."""
    seen, todo = set(), [entry]
    while todo:
        rel = todo.pop()
        if rel in seen:
            continue
        seen.add(rel)
        for name in _imports_of(os.path.join(root, rel)):
            for f in _module_files(name, root):
                if f not in seen:
                    todo.append(f)
    return sorted(seen)


def hashed_files(*, root, engines):
    """Row 97's list: this module and its import closure, the modules it names (NAMED_MODULES), the plant
    files (fingerprint.PLANT_CODE and every engine's specs). Refused if a named module is missing."""
    import engines as ENG
    import fingerprint as FP
    files = set(import_closure(MODULE_REL, root=root))
    for m in NAMED_MODULES:
        if not os.path.isfile(os.path.join(root, m)):
            raise Refused([f"{m} is missing: row 97 hashes it"])
        files.update(import_closure(m, root=root))
    files.update(FP.PLANT_CODE)
    for e in engines:
        files.update(ENG.spec_files(e))
    return sorted(files)


def sha_texts(files, *, root):
    from thresholds import common
    return {f: common.sha_text(os.path.join(root, f)) for f in files}


def live_provenance(engines):
    """The running code's plant_sha and engine_sha per engine, and epa_freeze.versions()."""
    import engines as ENG
    import epa_freeze
    return {"plants": {e: {"plant_sha": epa_freeze.plant_sha(e), "engine_sha": ENG.engine_sha(plant_of(e))}
                       for e in engines},
            "versions": epa_freeze.versions()}


def provenance(*, root, engines):
    files = hashed_files(root=root, engines=engines)
    live = live_provenance(engines)
    return {"files": sha_texts(files, root=root), "contract": sha_texts(CONTRACT_FILES, root=root),
            "plants": live["plants"], "versions": live["versions"]}


def frozen_problems(engines, *, root, jobs):
    """The draw runs on the frozen plants only (row 102; the ordering rule above row 94): each EPA engine's
    plant_sha is its results/EPA_CALIBRATION/<id>/freeze.json's, its engine_sha its complete.json's, its
    tau (roads_ceiling.tau_table, row 102's one definition) complete.json's e6_row4.frozen.tau_s exactly,
    and epa_freeze.versions() (the platform among them) its freeze.json's ("on this laptop", row 96); the
    B58's plant_sha is 865f8e7b7e5c2dbe, the plant row 102 computes its tau on. Returns (problems, what
    was compared)."""
    from thresholds import common
    live = live_provenance(engines)
    probs, seen = [], {"plants": live["plants"], "versions": live["versions"], "frozen": {}}
    taus = _ceiling_module().tau_table(list(engines), variant=("frozen",), jobs=jobs)
    for e in engines:
        ps, es, tau = live["plants"][e]["plant_sha"], live["plants"][e]["engine_sha"], float(taus[e][0])
        if e not in EPA_ENGINES:
            seen["frozen"][e] = {"plant_sha": B58_PLANT_SHA, "tau_s": tau}
            if ps != B58_PLANT_SHA:
                probs.append(f"{e}: plant_sha {ps} is not {B58_PLANT_SHA}, the B58 row 102 fixes")
            continue
        fz = common.load_json(os.path.join(root, CALIBRATION_REL, e, "freeze.json"))
        cp = common.load_json(os.path.join(root, CALIBRATION_REL, e, "complete.json"))
        want = {"plant_sha": fz["plant"]["plant_sha"], "engine_sha": cp["engine_sha"],
                "tau_s": float(cp["e6_row4"]["frozen"]["tau_s"]), "versions": fz["versions"]}
        seen["frozen"][e] = want
        for key, got in (("plant_sha", ps), ("engine_sha", es), ("tau_s", tau)):
            if got != want[key]:
                probs.append(f"{e}: {key} {got!r} is not the frozen {want[key]!r}")
        for key, v in sorted(want["versions"].items()):
            if live["versions"].get(key) != v:
                probs.append(f"{e}: versions.{key} {live['versions'].get(key)!r} is not freeze.json's {v!r}")
    seen["taus"] = {e: {"tau_s": float(taus[e][0]), "cell": jsonable(taus[e][1])} for e in engines}
    return probs, seen


def verify_record(record, *, root):
    """Row 97's refusal, before a re-check or a redraw draws anything: every hashed file's sha_text, the
    contract's two, every engine's plant_sha and engine_sha and epa_freeze.versions() must be the
    record's. Returns the problems, [] when everything agrees."""
    from thresholds import common
    h = record["hashes"]
    out = []
    for group in ("files", "contract"):
        for f, sha in sorted(h[group].items()):
            p = os.path.join(root, f)
            if not os.path.isfile(p):
                out.append(f"{f}: missing (roads.json hashes it)")
            elif common.sha_text(p) != sha:
                out.append(f"{f}: its sha_text is not roads.json's")
    if not out:
        # every hashed file is as recorded: is the set still the one the code imports? A package placed
        # beside a hashed module, or a module the closure no longer reaches, changes what runs while
        # every recorded hash still matches (the integrity review)
        try:
            now = set(hashed_files(root=root, engines=tuple(h["plants"])))
        except Refused as exc:
            out += [f"the import closure: {p}" for p in exc.args[0]]
        else:
            rec = set(h["files"])
            out += [f"{f}: reached by the code as it stands, not hashed by roads.json" for f in sorted(now - rec)]
            out += [f"{f}: hashed by roads.json, no longer reached by the code" for f in sorted(rec - now)]
    live = live_provenance(tuple(h["plants"]))
    for e, rec in sorted(h["plants"].items()):
        for key in ("plant_sha", "engine_sha"):
            if live["plants"][e][key] != rec[key]:
                out.append(f"{e}: {key} {live['plants'][e][key]} is not roads.json's {rec[key]}")
    for key, v in sorted(h["versions"].items()):
        if live["versions"].get(key) != v:
            out.append(f"versions.{key} {live['versions'].get(key)!r} is not roads.json's {v!r}")
    return out


# =====================================================================================================
# The commit and reveal (row 96)
# =====================================================================================================
def _private_int_ok(a):
    return isinstance(a, int) and not isinstance(a, bool) and a >= MIN_PRIVATE_INT


def commitment_hash(a):
    """The hash line of a private integer: hashlib.sha256(str(a).encode("ascii")).hexdigest(). Refused
    (ValueError) below 2**128: a small integer could be found from its line before the reveal, and row 96's
    seed "cannot be chosen by either of them" only if neither can know the other's."""
    if not _private_int_ok(a):
        raise ValueError("a private integer is an int of at least 2**128 (row 96): draw one with "
                         "`python epa_roads.py commitment`")
    return hashlib.sha256(str(a).encode("ascii")).hexdigest()


def new_private_integer():
    """A fresh private integer for the commit and reveal: 256 bits from the secrets module, the top bit
    set, so it is at least 2**255 and has 77 or 78 decimal digits."""
    import secrets
    return secrets.randbits(256) | (1 << 255)


def reveal_matches(a, line):
    return (_private_int_ok(a) and isinstance(line, str) and _HEX64.fullmatch(line) is not None
            and commitment_hash(a) == line)


def parse_reveal(text):
    """A revealed integer as typed: canonical decimal only (no sign, no leading zero, no space), so that
    str(int(text)) is the text that was hashed, and at least 2**128 (commitment_hash)."""
    if not isinstance(text, str) or _CANONICAL_INT.fullmatch(text) is None:
        raise Refused([f"the reveal {text!r} is not a non-negative integer in canonical decimal"])
    a = int(text)
    if a < MIN_PRIVATE_INT:
        raise Refused([f"the reveal {text!r} is below 2**128: a commitment to it hides nothing (row 96)"])
    return a


def roads_seed_from(a_g, a_j, roads_commit_sha):
    """roads_seed = int(sha256(f"{a_G}:{a_J}:{roads_commit_sha}").hexdigest()[:15], 16) (row 96)."""
    if not re.fullmatch(r"[0-9a-f]{40}", str(roads_commit_sha)):
        raise ValueError("the roads commit is named by its full 40-digit sha")
    return int(hashlib.sha256(f"{a_g}:{a_j}:{roads_commit_sha}".encode("ascii")).hexdigest()[:15], 16)


def committed_values(src):
    """(COMMITMENT_G, COMMITMENT_J) as a source text of this module assigns them; (None, None) if absent."""
    vals = {}
    for node in ast.parse(src).body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in ("COMMITMENT_G", "COMMITMENT_J")):
            vals[node.targets[0].id] = ast.literal_eval(node.value)
    return vals.get("COMMITMENT_G"), vals.get("COMMITMENT_J")


def _git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8")


def _git_ok(root, *args):
    r = _git(root, *args)
    if r.returncode != 0:
        raise Refused([f"git {' '.join(args)}: {r.stderr.strip()}"])
    return r.stdout


def _show(root, commit, rel):
    r = _git(root, "show", f"{commit}:{rel}")
    return r.stdout if r.returncode == 0 else None


def find_roads_commit(*, root):
    """The roads commit: the one commit in HEAD's history that set both hash lines of this module from
    None to their values at HEAD. Refused if either is missing at HEAD, if either is not 64 hex digits,
    if they were set in two commits, or if either ever held another value."""
    head = _show(root, "HEAD", MODULE_REL)
    if head is None:
        raise Refused([f"{MODULE_REL} is not committed at HEAD"])
    g, j = committed_values(head)
    probs = [f"{who}'s hash line is missing" for who, v in (("Ghassan", g), ("Jad", j)) if v is None]
    probs += [f"{who}'s hash line is not 64 lowercase hex digits" for who, v in (("Ghassan", g), ("Jad", j))
              if v is not None and (not isinstance(v, str) or _HEX64.fullmatch(v) is None)]
    if probs:
        raise Refused(probs)
    commits = _git_ok(root, "log", "--full-history", "--format=%H", "HEAD", "--", MODULE_REL).split()
    found, seen = [], set()
    for c in commits:
        src = _show(root, c, MODULE_REL)
        vals = (None, None) if src is None else committed_values(src)
        seen.add(vals)
        if vals != (g, j):
            continue
        parents = _git_ok(root, "rev-list", "--parents", "-n", "1", c).split()[1:]
        pvals = [(None, None) if _show(root, p, MODULE_REL) is None else committed_values(_show(root, p, MODULE_REL))
                 for p in parents]
        if all(v == (None, None) for v in pvals):
            found.append(c)
    other = sorted(str(v) for v in seen - {(None, None), (g, j)})
    if other:
        raise Refused([f"the hash lines held other values in HEAD's history ({', '.join(other)}): nobody "
                       "retries with a new integer (row 96)"])
    if len(found) != 1:
        raise Refused([f"{len(found)} commits set both hash lines from None; the roads commit is one"])
    return found[0], g, j


def _lf(text):
    return None if text is None else text.replace("\r\n", "\n")


def committed_versions(root, rel):
    """Every version of `rel` committed in HEAD's history, oldest first: [(commit, text or None where the
    commit deleted it)], CRLF read as LF (the repository is core.autocrlf=true)."""
    commits = _git_ok(root, "log", "--full-history", "--topo-order", "--reverse", "--format=%H", "HEAD", "--",
                      rel).split()
    return [(c, _lf(_show(root, c, rel))) for c in commits]


def remote_state(root, head):
    """Whether HEAD is in origin's GRA-test as the remote itself reports it (`git ls-remote`, not the
    local ref, which may be stale or set by hand). Returns (pushed, the remote's sha or None, why not)."""
    r = _git(root, "ls-remote", REMOTE_NAME, f"refs/heads/{REMOTE_BRANCH}")
    sha = r.stdout.split()[0] if r.returncode == 0 and r.stdout.strip() else None
    if sha is None:
        return False, None, f"{REMOTE_NAME}'s {REMOTE_BRANCH} cannot be read ({r.stderr.strip() or 'no such branch'})"
    r = _git(root, "merge-base", "--is-ancestor", head, sha)
    if r.returncode == 0:
        return True, sha, None
    if r.returncode == 1:
        return False, sha, f"HEAD {head} is not in {REMOTE_NAME}'s {REMOTE_BRANCH} ({sha}): push it first"
    return False, sha, f"{REMOTE_NAME}'s {REMOTE_BRANCH} is at {sha}, which this clone does not hold: fetch first"


def tree_state(root):
    """(HEAD, clean, the status lines): clean means no change and no untracked file."""
    head = _git_ok(root, "rev-parse", "--verify", "HEAD").strip()
    status = _git_ok(root, "status", "--porcelain=v1", "--untracked-files=all")
    return head, status.strip() == "", status.splitlines()


def attempts_log_problems(*, root):
    """Row 96's attempts log is never rewritten: in HEAD's history every committed version extends the one
    before it and none deletes it, and the tree's copy is HEAD's. Returns (problems, HEAD's text or None)."""
    probs, prev = [], None
    for c, text in committed_versions(root, ATTEMPTS_REL):
        if text is None:
            probs.append(f"{ATTEMPTS_REL} was deleted in commit {c}: the attempts log is never removed (row 96)")
            continue
        if prev is not None and not text.startswith(prev):
            probs.append(f"{ATTEMPTS_REL} at commit {c} does not extend the version before it: the log is "
                         "append-only (row 96)")
        prev = text
    head_text = _lf(_show(root, "HEAD", ATTEMPTS_REL))
    if prev is not None and head_text is None:
        probs.append(f"{ATTEMPTS_REL} was committed in HEAD's history and is not at HEAD")
    path = os.path.join(root, ATTEMPTS_REL)
    work = None
    if os.path.exists(path):
        with open(path, encoding="utf-8", newline="") as fh:
            work = _lf(fh.read())
    if work != head_text:
        probs.append(f"{ATTEMPTS_REL} in the tree is not HEAD's: commit the log between attempts (row 96)")
    return probs, head_text


def draw_preconditions(*, root, roads_commit):
    """The draw's refusals before anything is written (rows 96, 97, 103 (3)): roads.json absent and never
    committed in HEAD's history; the tree clean; HEAD in origin's GRA-test (remote_state); HEAD a
    descendant of the roads commit; the attempts log never rewritten (attempts_log_problems). Whether the
    attempt may run on HEAD (the first on the roads commit itself) is draw()'s, which knows the attempt's
    number. Returns (problems, context: HEAD, clean, pushed, the remote's sha, the files and commits since
    the roads commit)."""
    probs = []
    if os.path.exists(os.path.join(root, ROADS_REL)):
        probs.append(f"{ROADS_REL} exists: it is written once (row 97)")
    if committed_versions(root, ROADS_REL):
        probs.append(f"{ROADS_REL} was committed in HEAD's history: a set was drawn, and no second set is drawn "
                     "(row 103 (3))")
    head, clean, status = tree_state(root)
    if not clean:
        probs.append("the tree is not clean: " + "; ".join(status[:10]))
    pushed, remote_sha, why = remote_state(root, head)
    if not pushed:
        probs.append(why)
    r = _git(root, "merge-base", "--is-ancestor", roads_commit, "HEAD")
    descends = r.returncode == 0
    if not descends:
        probs.append(f"HEAD is not a descendant of the roads commit {roads_commit}")
    lp, _ = attempts_log_problems(root=root)
    probs += lp
    since_files = _git_ok(root, "diff", "--name-only", roads_commit, "HEAD").split() if descends else None
    since_commits = _git_ok(root, "rev-list", "--reverse", f"{roads_commit}..HEAD").split() if descends else None
    return probs, {"head": head, "clean": clean, "pushed": pushed, "remote_sha": remote_sha,
                   "roads_commit": roads_commit, "files_changed_since_roads_commit": since_files,
                   "commits_since_roads_commit": since_commits}


# =====================================================================================================
# The attempts log and the records (rows 96, 97)
# =====================================================================================================
def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def append_attempt(path, entry):
    """Append one JSON line to the attempts log; it is never rewritten (row 96)."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    line = json.dumps(entry, allow_nan=False, ensure_ascii=True, sort_keys=True)
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(line + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def read_attempts(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


def write_once(path, obj):
    """Write a record once (row 97): refused if the file exists; written to a partial file and linked
    into place, which fails if the target appeared meanwhile. LF, ASCII, no NaN. Returns its sha_text."""
    from thresholds import common
    path = os.path.abspath(path)
    if os.path.exists(path):
        raise Refused([f"{path} exists: it is written once and never edited (row 97)"])
    text = json.dumps(obj, allow_nan=False, ensure_ascii=True, separators=(",", ":")) + "\n"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".partial"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    try:
        os.link(tmp, path)
    finally:
        os.remove(tmp)
    return common.sha_text(path)


def roads_sha(path):
    """roads_sha: the sha_text of roads.json (row 97), the project's LF-normalised hash."""
    from thresholds import common
    return common.sha_text(path)


class _Tee(io.TextIOBase):
    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            st.write(s)
            st.flush()
        return len(s)

    def flush(self):
        for st in self.streams:
            st.flush()


@contextlib.contextmanager
def printed_to(path):
    """Everything printed inside, to stdout or to stderr (roads_ceiling's progress goes there), goes to
    its stream and to `path` too (the attempt's printed outputs, row 96)."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = _Tee(old_out, fh), _Tee(old_err, fh)
        try:
            yield
        finally:
            sys.stdout, sys.stderr = old_out, old_err


def printed_sha(path):
    """The sha_text of a printed-outputs file, or None when it does not exist."""
    from thresholds import common
    return common.sha_text(path) if os.path.isfile(path) else None


def files_opened():
    """Every repository file this process, its own workers and roads_ceiling's workers opened."""
    RC = sys.modules.get("roads_ceiling")
    return sorted(OPENED | set(getattr(RC, "OPENED", set())))


def data_inputs(opened, hashes, *, root):
    """The sha_text of every file the run opened that the record's hashes do not already name (data and
    records: the derived files, complete.json, freeze.json, the traces), so that a change to one shows."""
    named = set(hashes["files"]) | set(hashes["contract"])
    return sha_texts([f for f in opened if f not in named and not f.startswith(ROADS_DIR_REL + "/")
                      and os.path.isfile(os.path.join(root, f))], root=root)


def make_log(steps):
    def log(msg):
        line = f"[{now_utc()}] {msg}"
        steps.append(line)
        print(line, flush=True)
    return log


# =====================================================================================================
# The first draw (rows 96-103, in row 98's order)
# =====================================================================================================
def _ceiling_module():
    try:
        import roads_ceiling as RC
    except ImportError as exc:
        raise Refused([f"roads_ceiling.py cannot be imported ({exc}): the ceilings are its"]) from exc
    return RC


def first_draw(roads_seed, *, seed_kind, n_roads, engines, ratios, variants, readings, companions, jobs, log):
    """The first draw from roads_seed, in row 98's order, each step logged before the next prints a
    number: (1) the identity on the B58's locked climb; (2) the arrays; (3) the identity on every engine's
    arrays; (4) C5 and the replacement grades, then the ceilings (roads_ceiling.ceilings, passes_T and,
    with companions, report); (5) the identity on the final arrays. Then what is reported and discards
    nothing (decision 40's diagnostic, the coverage flags), the practice set and tau. Returns the record
    without the attempts log and the commit and reveal, which the caller adds. A REAL draw is refused
    unless it asks for the whole of row 103 (1) on the four engines; a SYNTHETIC seed is an int below
    2**32, so roads_seed never runs here as one (the integrity review). The tree is compared with the
    hashes taken at the start before the ceilings print, before the last identity and at the end."""
    RC = _ceiling_module()
    why = _seed_problem(roads_seed, seed_kind=seed_kind)
    if why:
        raise Refused([why])
    if seed_kind == "REAL" and (tuple(engines) != ENGINES or set(variants) != set(RC.ALL_VARIANTS)
                                or set(readings) != set(RC.READINGS) or not companions):
        raise Refused([f"a REAL draw computes every variant {RC.ALL_VARIANTS}, both readings and the companions on "
                       f"{ENGINES} (row 103 (1)); asked for {tuple(variants)}, {tuple(readings)} on {tuple(engines)}"])
    t_start = now_utc()
    check_engine_env()
    log(f"check_engine_env: the road shape is make_grade_climb's, ramp {RAMP_S} s ({seed_kind} seed)")
    prov0 = provenance(root=REPO, engines=engines)
    changed = []

    def unchanged(before):
        now = _changed(prov0, provenance(root=REPO, engines=engines))
        if now and seed_kind == "REAL":
            raise CodingDefect(f"hashed files, versions or plants changed during the draw, found before {before}: "
                               f"{now}")
        if now:
            log(f"SYNTHETIC run: these changed in the tree before {before} (other work in progress): {now}")
        changed.extend(x for x in now if x not in changed)
    log(f"provenance: {len(prov0['files'])} files hashed; plant_sha " +
        ", ".join(f"{e} {v['plant_sha']}" for e, v in prov0["plants"].items()))
    opened = set()

    # (1)
    if "b58" in engines:
        locked = _locked_task("b58")
        opened.update(locked.pop("opened"))
        log(f"step 1, identity on the B58's locked climb: holds {locked['holds']} {locked['identity']}")
        if not locked["holds"]:
            raise CodingDefect("the identity fails on the B58's locked climb, a coding defect (row 98)")
    else:
        locked = None
        log("step 1, identity on the B58's locked climb: not run (the B58 is not in this run)")

    # (2)
    generated = generate(roads_seed, n_roads=n_roads)
    for r in generated:
        r["label"] = f"{seed_kind} road {r['k']}"
    n_slots = sum(len(r["climbs"]) for r in generated)
    log(f"step 2, arrays generated: {len(generated)} roads, {n_slots} slots, climbs per road "
        f"{[len(r['climbs']) for r in generated]}, arrays sha256 {arrays_sha256(generated)}")

    # (3)
    gen_id, op = identities(generated, engines=engines, jobs=jobs, keep_arrays=False, label="generated arrays")
    opened |= op
    log(f"step 3, identity on every engine's generated arrays: {len(generated) * len(engines)} runs, all hold")

    # (4)
    plants = {e: plant_of(e) for e in engines}
    final, slot_records, final_c5 = replacement_loop(generated, roads_seed, plants=plants, gating=set(engines),
                                                     log=log)
    n_rep = sum(1 for s in slot_records if s["outcome"] == "replaced")
    n_flat = sum(1 for s in slot_records if s["outcome"] == "flat")
    log(f"step 4a, C5 at {C5_MARGIN * 100:.1f} % and row 98's checks on every car: {len(slot_records)} slots, "
        f"{n_rep} replaced, {n_flat} flat; final arrays sha256 {arrays_sha256(final)}")
    unchanged("the ceilings print (step 4b)")
    ceil = RC.ceilings(final, engines=engines, ratios=ratios, dt=DT, jobs=jobs, variants=variants,
                       readings=readings)
    passes, at_15 = RC.passes_T(ceil, engines=engines)
    ceil, at_15 = jsonable(ceil), jsonable(at_15)
    log(f"step 4b, ceilings: passes T {passes}; C at r = 1.5 " + ", ".join(f"{e} {v}" for e, v in at_15.items()))
    report = jsonable(RC.report(final, engines=engines, dt=DT, jobs=jobs)) if companions else None
    log("step 4c, companions: " + ("computed (roads_ceiling.report)" if companions else "not computed (smoke)"))
    unchanged("the identity on the final arrays (step 5)")

    # (5)
    fin_id, op = identities(final, engines=engines, jobs=jobs, keep_arrays=True, label="final arrays")
    opened |= op
    OPENED.update(opened)          # the record lists the files this module's workers opened too
    log(f"step 5, identity on every engine's final arrays: {len(final) * len(engines)} runs, all hold")

    # reported, discarding nothing
    from thresholds import common
    contract = common.load_json(common.CONTRACT_JSON)
    cvt, cov = {}, {}
    for i, slot in slots_of(final):
        if slot.get("flat"):
            continue
        road = final[i]
        for e in engines:
            run = fin_id[str(road["k"])][e]["arrays"]
            if e == CVT_ENGINE:
                steps, _ = c5_on_car(plants[e], road, slot, margin=C5_MARGIN)
                cvt[str(slot["slot"])] = cvt_diagnostics(plants[e], road, slot, steps, run, margin=C5_MARGIN)
            if e in EPA_ENGINES:
                cov.setdefault(e, {})[str(slot["slot"])] = coverage_flags(
                    e, road, slot, run, coverage=contract["engines"][e]["coverage"])
    if CVT_ENGINE in engines:
        tot = cvt_totals(cvt.values())
        log(f"decision 40's diagnostic on {CVT_ENGINE}: {tot['gated_steps']} gated steps on the kickdown and "
            f"power-limited branches, {tot['not_connected']} not one interval, {tot['leaves_branch']} leaving the "
            f"branch ({tot['all_branches']['gated_steps']} gated steps on every branch, "
            f"{tot['all_branches']['not_connected']} and {tot['all_branches']['leaves_branch']})")
    for e, v in cov.items():
        log(f"coverage on {e}: {sum(1 for x in v.values() if x['covered_fired'])}/{len(v)} climbs inside "
            f"calibration_fired, {sum(1 for x in v.values() if x['covered_hot'])}/{len(v)} inside calibration_hot")
    for road in fin_id.values():
        for x in road.values():
            x.pop("arrays", None)
    episode_steps = sorted({int(x["identity"]["steps"]) for road in fin_id.values() for x in road.values()})
    log(f"episode length: {episode_steps} steps on {len(final[0]['cycle']['t'])}-sample roads ({EPISODE_STEPS_NOTE})")
    practice = practice_roads(roads_seed)
    log(f"practice set: {len(practice)} roads, climbs per road {[len(r['climbs']) for r in practice]}")
    # row 102: every engine's tau by the one definition, written once here and read from here by the
    # re-check and the redraws (roads_ceiling.use_recorded_taus); never recomputed after the draw
    taus = RC.tau_table(list(engines), variant=("frozen",), jobs=jobs)
    tau = {}
    for e in engines:
        tau[e] = {"tau_s": float(taus[e][0]), "cell": jsonable(taus[e][1]),
                  "plant_sha": prov0["plants"][e]["plant_sha"], "engine_sha": prov0["plants"][e]["engine_sha"],
                  "definition": "row 102: epa_coefficients.housing at epa_coefficients.climb_cell (roads_ceiling)"}
        if e in EPA_ENGINES:
            cp = os.path.join(REPO, CALIBRATION_REL, e, "complete.json")
            if os.path.isfile(cp):
                with open(cp, encoding="utf-8") as fh:
                    tau[e]["complete_json_frozen_tau_s"] = float(json.load(fh)["e6_row4"]["frozen"]["tau_s"])
                tau[e]["equals_complete_json"] = tau[e]["tau_s"] == tau[e]["complete_json_frozen_tau_s"]
        log(f"tau of {e} by row 102's definition: {tau[e]['tau_s']} s on plant_sha {tau[e]['plant_sha']}"
            + (f" (complete.json: equal {tau[e]['equals_complete_json']})" if "equals_complete_json" in tau[e] else ""))
    htab = h_table({e: tau[e]["tau_s"] for e in engines}, RC.RATIOS, dt=DT)
    unchanged("the record is written")
    return {"schema": ROADS_SCHEMA, "seed_kind": seed_kind, "started": t_start, "finished": now_utc(),
            "design": design(), "streams": streams(),
            "engines": list(engines), "ratios": list(ratios), "variants": list(variants),
            "readings": list(readings), "companions": bool(companions),
            "roads": final, "slots": slot_records, "c5": final_c5,
            "cvt_diagnostic": ({CVT_ENGINE: cvt, "totals": cvt_totals(cvt.values())} if CVT_ENGINE in engines
                               else None),
            "coverage": cov,
            "identities": {"locked_climb_b58": locked, "generated": gen_id, "final": fin_id},
            "episode_steps": {"measured": episode_steps, "note": EPISODE_STEPS_NOTE},
            "ceilings": ceil, "passes_T": {"passes": bool(passes), "at_r_1.5": at_15},
            "report": report if companions else "not computed (smoke)",
            "practice": practice, "tau": tau, "H_table": htab, "hashes": prov0, "changed_during_run": changed}


def _seed_problem(seed, *, seed_kind):
    """Why a seed may not run as `seed_kind`, or None: a SYNTHETIC seed is an int in [0, 2**32), so that
    the 60-bit roads_seed can never be passed as one (as roads_ceiling.synthetic_roads refuses it); a REAL
    one is row 96's, in [0, 16**15)."""
    ok_int = isinstance(seed, int) and not isinstance(seed, bool)
    if seed_kind == "SYNTHETIC":
        if not (ok_int and 0 <= seed < SYNTHETIC_SEED_LIMIT):
            return f"the SYNTHETIC seed {seed!r} is not an int below 2**32: roads_seed never runs as a SYNTHETIC seed"
    elif seed_kind == "REAL":
        if not (ok_int and 0 <= seed < ROADS_SEED_LIMIT):
            return f"roads_seed {seed!r} is not row 96's 60-bit integer"
    else:
        return f"seed_kind {seed_kind!r} is neither REAL nor SYNTHETIC"
    return None


def _changed(prov0, prov1):
    """The hashed files, contract files, plants and versions that differ between two provenance reads."""
    out = sorted(f for g in ("files", "contract") for f in set(prov0[g]) | set(prov1[g])
                 if prov0[g].get(f) != prov1[g].get(f))
    return out + [g for g in ("plants", "versions") if prov0[g] != prov1[g]]


def h_table(taus, ratios, *, dt):
    """Row 102's table of H: per engine and r, tau, H = r tau and the step each preview sample falls on,
    row 117's samples at H x (1/15, 1/6, 1/2, 1), each at step int(h / dt)."""
    out = {}
    for e, tau in taus.items():
        out[e] = {}
        for r in ratios:
            H = float(r) * float(tau)
            out[e][f"{r:g}"] = {"tau_s": float(tau), "H_s": H,
                                "sample_steps": [int((H / d) / dt) for d in (15.0, 6.0, 2.0, 1.0)]}
    return out


def cvt_totals(diags):
    """Decision 40's totals over the climbs' diagnostics: over the gated steps on the kickdown and the
    power-limited branches, the steps MD:1236 asks it at ("at every gated step on either branch"), with
    the totals over every branch beside them, labelled."""
    steps = [s for d in diags for s in d["steps"]]
    either = [s for s in steps if s["branch"] in CVT_GATED_BRANCHES]

    def count(xs):
        return {"gated_steps": len(xs), "not_connected": sum(1 for s in xs if not s["connected"]),
                "leaves_branch": sum(1 for s in xs if not s["stays_on_branch"])}
    by = {}
    for s in steps:
        by[s["branch"]] = by.get(s["branch"], 0) + 1
    return dict(count(either), branches=list(CVT_GATED_BRANCHES), all_branches=count(steps), steps_by_branch=by)


def design():
    return {"n_roads": N_ROADS, "duration_s": DURATION_S, "dt": DT, "v_kmh": V_KMH, "speed_ramp_s": SPEED_RAMP_S,
            "t_amb_k": T_AMB_K, "p_baro_kpa": P_BARO_KPA, "humidity": HUMIDITY,
            "lead_in_s": "integers(150, 211)", "L_s": "integers(67, 86)", "grade": "uniform(0.10, 0.12)",
            "gap_s": "integers(50, 151)", "tail_s": TAIL_S, "ramp_s": RAMP_S, "replacements": REPLACEMENTS,
            "c5_margin": C5_MARGIN, "slot_extent": "s .. s + L + 8 s", "rows": "section I, rows 95-103",
            "episode_steps": EPISODE_STEPS_NOTE}


def streams():
    return {"first_draw": "default_rng(roads_seed)", "replacement": "default_rng([roads_seed, 0x1D, k])",
            "redraw": "default_rng([roads_seed, 0xC5, k])", "practice": "default_rng([roads_seed, 0x50])",
            "training_share": "default_rng([roads_seed, 0x7A, seed])",
            "k": "the slot's index from 0 over every slot: roads in order, a road's slots by first step"}


def _outcome(entry, **kw):
    return dict(entry, **kw, time=now_utc())


def _draw_entries(entries):
    """The first draw's lines of the attempts log (the re-check's and the redraws' carry their own step)."""
    return [x for x in entries if x.get("step", "draw") == "draw"]


def _step_rules(earlier, *, what, note):
    """Row 96's rules between attempts of one step, from that step's earlier lines: refused once one drew
    its record (a set: row 103 (3); the redraws: written once, row 97) or stopped for a reason that is not
    a coding defect (the step has ended; only a row of its own reopens it); a later attempt follows a
    crash, an interrupted run or a coding-defect stop and carries a note naming the defect and the commits
    that fixed it. Returns (problems, the attempt's number, whether the last attempt was interrupted)."""
    probs = []
    done = [x for x in earlier if x.get("event") == "outcome" and x.get("outcome") in ("roads", "redraws")]
    if done:
        probs.append(f"attempt {done[0]['attempt']} wrote its record ({done[0]['outcome']}): {what} runs once "
                     "and is never repeated (rows 97, 103 (3))")
    ended = [x for x in earlier if x.get("event") == "outcome" and x.get("outcome") == "stop"
             and not x.get("coding_defect")]
    if ended:
        probs.append(f"attempt {ended[0]['attempt']} stopped for a reason that is not a coding defect "
                     f"({ended[0].get('reason')}): {what} has ended (rows 96, 103 (3)); only a row of its own "
                     "reopens it")
    starts = [x for x in earlier if x.get("event") == "start"]
    n = len(starts) + 1
    interrupted = None
    if n > 1:
        last = starts[-1]["attempt"]
        interrupted = not any(x.get("event") == "outcome" and x.get("attempt") == last for x in earlier)
        if not (isinstance(note, str) and note.strip()):
            probs.append(f"attempt {n} of {what} follows attempt {last}: --note names the defect and the commits "
                         "that fixed it (rows 96, 98)")
    return probs, n, interrupted


def draw(reveal_g, reveal_j, *, roads_commit_announced, note, root, jobs):
    """The single draw (row 96). Refused before anything is written unless: the reveals are integers of at
    least 2**128 in canonical decimal; both hash lines are set in one roads commit, and the roads commit
    announced before the reveal is that commit (a commit remade after the reveal would give another
    seed); draw_preconditions holds (roads.json absent and never committed, a clean tree, HEAD in
    origin's GRA-test, the attempts log never rewritten); _step_rules holds (no set drawn before, no
    non-defect stop, a note on a later attempt); the first attempt runs on the roads commit itself (row
    96: "on the roads commit"; ORDER step 6: "on R0"); and frozen_problems finds nothing (the frozen
    plants, taus and versions). Then its FIRST write: the attempt's start line, appended to the attempts
    log before roads_seed is computed, with the hashes of every file roads.json will hash and, for a
    later attempt, every file and commit since the roads commit. A reveal that does not match its hash is
    logged and stops the roads (row 96). Everything printed, stdout and stderr, goes to the attempt's
    printed file too, whose sha_text the outcome line records; roads.json lists the earlier attempts'."""
    a_g, a_j = parse_reveal(reveal_g), parse_reveal(reveal_j)
    roads_commit, h_g, h_j = find_roads_commit(root=root)
    if not isinstance(roads_commit_announced, str) or _SHA40.fullmatch(roads_commit_announced) is None:
        raise Refused([f"--roads-commit {roads_commit_announced!r} is not a full 40-digit lowercase sha"])
    if roads_commit_announced != roads_commit:
        raise Refused([f"the roads commit announced before the reveal, {roads_commit_announced}, is not the one "
                       f"HEAD's history holds, {roads_commit}: the roads commit is fixed at the reveal (row 96)"])
    probs, ctx = draw_preconditions(root=root, roads_commit=roads_commit)
    log_path = os.path.join(root, ATTEMPTS_REL)
    earlier = _draw_entries(read_attempts(log_path))
    sp, n, interrupted = _step_rules(earlier, what="the roads step", note=note)
    probs += sp
    if n == 1 and ctx["head"] != roads_commit:
        probs.append(f"the first attempt runs on the roads commit {roads_commit} itself (row 96; ORDER step 6), "
                     f"not on {ctx['head']}: check the roads commit out")
    if probs:
        raise Refused(probs)
    fp, frozen = frozen_problems(ENGINES, root=root, jobs=jobs)
    if fp:
        raise Refused(fp)
    prov = provenance(root=root, engines=ENGINES)
    match = {"ghassan": reveal_matches(a_g, h_g), "jad": reveal_matches(a_j, h_j)}
    entry = {"step": "draw", "event": "start", "attempt": n, "kind": "REAL", "time": now_utc(),
             "commit": ctx["head"], "clean": ctx["clean"], "pushed": ctx["pushed"], "remote_sha": ctx["remote_sha"],
             "roads_commit": roads_commit, "roads_commit_announced": roads_commit_announced,
             "hash_lines": {"ghassan": h_g, "jad": h_j}, "reveal": {"ghassan": a_g, "jad": a_j},
             "reveal_matches": match, "jobs": int(jobs), "versions": frozen["versions"], "plants": frozen["plants"],
             "files": prov["files"], "contract": prov["contract"],
             "files_changed_since_roads_commit": ctx["files_changed_since_roads_commit"],
             "commits_since_roads_commit": ctx["commits_since_roads_commit"],
             "note": note if n > 1 else None, "follows_interrupted_attempt": interrupted}
    append_attempt(log_path, entry)
    end = {"step": "draw", "event": "outcome", "attempt": n}
    if not all(match.values()):
        append_attempt(log_path, _outcome(end, outcome="stop", coding_defect=False,
                                          reason="a reveal does not match its hash line; roads_seed was not "
                                                 "computed (row 96)"))
        raise RoadsStop("a reveal does not match its hash line: the roads step ends (rows 96, 103 (3))")
    printed = os.path.join(root, ROADS_DIR_REL, f"attempt_{n}_printed.txt")
    earlier_printed = []
    for x in [x for x in earlier if x.get("event") == "start"]:
        rel = f"{ROADS_DIR_REL}/attempt_{x['attempt']}_printed.txt"
        earlier_printed.append({"attempt": x["attempt"], "path": rel,
                                "sha_text": printed_sha(os.path.join(root, rel))})
    try:
        with printed_to(printed):
            roads_seed = roads_seed_from(a_g, a_j, roads_commit)
            steps = []
            log = make_log(steps)
            log(f"attempt {n}: roads_seed {roads_seed} from the reveal and the roads commit {roads_commit}")
            record = first_draw(roads_seed, seed_kind="REAL", n_roads=N_ROADS, engines=ENGINES,
                                ratios=_ceiling_module().RATIOS, variants=DRAW_VARIANTS, readings=DRAW_READINGS,
                                companions=True, jobs=jobs, log=log)
            record["commit_reveal"] = {"hash_lines": {"ghassan": h_g, "jad": h_j},
                                       "reveal": {"ghassan": a_g, "jad": a_j}, "roads_commit": roads_commit,
                                       "roads_commit_announced": roads_commit_announced,
                                       "roads_seed": roads_seed, "rule": "int(sha256(f'{a_G}:{a_J}:{roads_commit_sha}')"
                                       ".hexdigest()[:15], 16) (row 96)"}
            record["frozen_check"] = frozen
            record["attempts"] = read_attempts(log_path)
            record["steps_log"] = steps
            record["printed"] = os.path.relpath(printed, root).replace("\\", "/")
            record["printed_earlier"] = earlier_printed
            opened = files_opened()
            record["files_opened"] = opened
            record["data_inputs"] = data_inputs(opened, record["hashes"], root=root)
            sha = write_once(os.path.join(root, ROADS_REL), record)
            print(f"roads.json written: roads_sha {sha}")
    except RoadsStop as exc:
        append_attempt(log_path, _outcome(end, outcome="stop", coding_defect=isinstance(exc, CodingDefect),
                                          reason=str(exc), printed_sha_text=printed_sha(printed)))
        raise
    except BaseException as exc:
        append_attempt(log_path, _outcome(end, outcome="crash", reason=f"{type(exc).__name__}: {exc}",
                                          traceback=traceback.format_exc()[-4000:],
                                          printed_sha_text=printed_sha(printed)))
        raise
    append_attempt(log_path, _outcome(end, outcome="roads", roads_sha=sha, passes_T=record["passes_T"]["passes"],
                                      printed_sha_text=printed_sha(printed)))
    return sha


def outside_repo(path):
    p = os.path.normcase(os.path.abspath(path))
    root = os.path.normcase(REPO)
    return p != root and not p.startswith(root + os.sep)


def smoke(synthetic_seed, *, out_dir, jobs, with_redraw, full):
    """A reduced end-to-end run on a SYNTHETIC seed, an int below 2**32 (roads_seed is refused), written
    only under out_dir, which must lie outside the repository: it never writes roads.json or the real
    attempts log. By default 2 roads, the B58 and the Ford, r = 1.5, current-grade and (a) in the no-knock
    reading, no companions. full: the real draw's path on 1 road: the four engines, every variant and
    both readings at both ratios, with roads_ceiling.report's companions and the Honda's decision-40
    diagnostic (the correctness review: the path the draw takes, run before the draw). The frozen-plant
    check is run and reported, never refused. with_redraw: the re-check and the redraws of the first
    failing slot, at SYNTHETIC margins (the Ford's 0.5), which every slot fails."""
    if not outside_repo(out_dir):
        raise Refused([f"{out_dir} is inside the repository: a SYNTHETIC run writes outside it"])
    why = _seed_problem(synthetic_seed, seed_kind="SYNTHETIC")
    if why:
        raise Refused([why])
    seed = synthetic_seed
    log_path = os.path.join(out_dir, "attempts_SYNTHETIC.jsonl")
    rec_path = os.path.join(out_dir, "roads_SYNTHETIC.json")
    printed = os.path.join(out_dir, "printed_SYNTHETIC.txt")
    if os.path.exists(rec_path):
        raise Refused([f"{rec_path} exists: a smoke record is written once too"])
    if full:
        RC = _ceiling_module()
        shape = dict(n_roads=1, engines=ENGINES, ratios=RC.RATIOS, variants=DRAW_VARIANTS, readings=DRAW_READINGS,
                     companions=True)
    else:
        shape = dict(n_roads=SMOKE_N_ROADS, engines=SMOKE_ENGINES, ratios=SMOKE_RATIOS, variants=SMOKE_VARIANTS,
                     readings=SMOKE_READINGS, companions=False)
    head = _git(REPO, "rev-parse", "HEAD").stdout.strip()
    clean = _git(REPO, "status", "--porcelain=v1", "--untracked-files=all").stdout.strip() == ""
    entry = {"step": "draw", "event": "start", "attempt": 1, "kind": "SYNTHETIC", "synthetic_seed": seed,
             "time": now_utc(), "commit": head, "clean": clean, "jobs": int(jobs), "full": bool(full),
             "with_redraw": bool(with_redraw)}
    append_attempt(log_path, entry)
    end = {"step": "draw", "event": "outcome", "attempt": 1}
    try:
        with printed_to(printed):
            steps = []
            log = make_log(steps)
            log(f"SYNTHETIC seed {seed}: not roads_seed; nothing here is a road of the test")
            fp, frozen = frozen_problems(shape["engines"], root=REPO, jobs=jobs)
            log("the frozen-plant check (SYNTHETIC: reported, never refused): "
                + ("; ".join(fp) if fp else "every plant_sha, engine_sha, tau and version is the frozen one"))
            record = first_draw(seed, seed_kind="SYNTHETIC", jobs=jobs, log=log, **shape)
            record["frozen_check"] = {"problems": fp, "seen": frozen}
            record["commit_reveal"] = {"SYNTHETIC": True, "roads_seed": seed}
            record["attempts"] = read_attempts(log_path)
            record["steps_log"] = steps
            opened = files_opened()
            record["files_opened"] = opened
            record["data_inputs"] = data_inputs(opened, record["hashes"], root=REPO)
            sha = write_once(rec_path, record)
            log(f"SYNTHETIC record written: sha_text {sha} ({rec_path})")
            if with_redraw:
                margins = {e: (0.5 if e == "ford_27tt" else C5_MARGIN) for e in shape["engines"]}
                red = redraw(record, roads_sha_value=sha, margins=margins, margins_source="SYNTHETIC margins",
                             dropped=(), jobs=jobs, root=REPO, log=log, engines=shape["engines"], max_slots=1)
                red["steps_log"] = list(steps)
                rsha = write_once(os.path.join(out_dir, "redraws_SYNTHETIC.json"), red)
                log(f"SYNTHETIC redraws written: sha_text {rsha}")
    except RoadsStop as exc:
        append_attempt(log_path, _outcome(end, outcome="stop", coding_defect=isinstance(exc, CodingDefect),
                                          reason=str(exc), printed_sha_text=printed_sha(printed)))
        raise
    except BaseException as exc:
        append_attempt(log_path, _outcome(end, outcome="crash", reason=f"{type(exc).__name__}: {exc}",
                                          traceback=traceback.format_exc()[-4000:],
                                          printed_sha_text=printed_sha(printed)))
        raise
    append_attempt(log_path, _outcome(end, outcome="roads", sha_text=sha, printed_sha_text=printed_sha(printed)))
    return sha


# =====================================================================================================
# After Run 2: the C5 re-check and the redraws (rows 95, 97, 98; MD:1395-1423)
# =====================================================================================================
def margins_from_summary(summary, *, engines):
    """Each EPA engine's re-check margin (a fraction) from results/EPA_VALIDATION/summary.json's
    engines.<id>.c5_recheck_margin (validate_epa.c5_recheck_margin: max(R, |E| + 2u_val) of E1a's worst
    deciding line, R being 1.9 %); the B58's at 1.9 % (MD:1395-1396)."""
    out = {}
    for e in engines:
        if e == "b58":
            out[e] = C5_MARGIN
            continue
        m = summary["engines"][e]["c5_recheck_margin"]
        f = float(m["margin_fraction"])
        if not (C5_MARGIN <= f < 1.0):
            raise Refused([f"{e}: re-check margin {f!r} is not a fraction at or above 1.9 %"])
        out[e] = f
    return out


def _honda_runs(roads, *, jobs):
    res = pool_map(_identity_task, [(CVT_ENGINE, r, True) for r in roads], jobs=jobs)
    return {str(x["road"]): x for x in res}


def recheck_slots(roads, *, margins, plants, gating, jobs):
    """Every scored climb re-checked on every car at its margin; a slot fails when it is in case (1), or
    has no gated step, on a car in `gating` (row 95 (2)). The CVT diagnostic at the Honda's margin."""
    out, failing = {}, []
    runs = _honda_runs(roads, jobs=jobs) if CVT_ENGINE in plants else {}
    for i, slot in slots_of(roads):
        if slot.get("flat"):
            continue
        road = roads[i]
        k = str(slot["slot"])
        out[k] = {"road": int(road["k"]), "cars": {}}
        why = []
        for e, p in plants.items():
            steps, res = c5_on_car(p, road, slot, margin=margins[e])
            out[k]["cars"][e] = dict(c5_json(steps, res, with_steps=False), margin=margins[e])
            w = c5_failure(e, res, margin=margins[e])
            if w and e in gating:
                why.append(w)
            if e == CVT_ENGINE:
                out[k]["cvt_diagnostic"] = cvt_diagnostics(p, road, slot, steps, runs[str(road["k"])]["arrays"],
                                                           margin=margins[e])
        out[k]["fails"] = why
        if why:
            failing.append(slot["slot"])
    return out, failing


def redraw_slot(roads, i, slot, *, roads_seed, plants, gating, margins, kept_recheck, jobs, RC, log):
    """One slot's redraws (MD:1401-1435): candidates from default_rng([roads_seed, 0xC5, k]) at the
    slot's recorded L, in the slot's recorded extent; a candidate that fails a first-draw test (row 98's
    checks, C5 at 1.9 % with a gated step on every gating car, T on the set with the candidate in its
    slot and every other slot as it then stands) is discarded, at most REDRAW_DISCARDS; one that passes
    them all is a redraw, at most REDRAW_CAP, the identity is run on it, and every car's C5 is checked
    again at its re-check margin. A slot at the cap or the discard bound keeps the last climb accepted for
    it, its original or its last redraw, flagged gear-sensitive on each gating car it fails there.
    `kept_recheck` is the original climb's re-check ({car: c5 json}, with "fails"). roads[i] is updated."""
    k = slot["slot"]
    slot_record = {key: slot[key] for key in ("slot", "onset_s", "L_s", "first_step", "last_step")}
    rng = redraw_rng(roads_seed, k)
    redraws, discards, history, stop = 0, 0, [], None
    kept = {"source": "original", "recheck": kept_recheck["cars"], "fails": list(kept_recheck["fails"])}
    while kept["fails"]:
        if redraws >= REDRAW_CAP:
            stop = "cap"
            break
        accepted = None
        while accepted is None and discards < REDRAW_DISCARDS:
            g = float(rng.uniform(GRADE_LO, GRADE_HI))
            cand = with_grade(roads[i], k, g)
            failed, c5 = climb_tests(slot_record, cand, roads[i], plants=plants, gating=gating, margin=C5_MARGIN)
            entry = {"draw": len(history) + 1, "grade": g, "failed": failed,
                     "c5": {e: c5_json(*v, with_steps=False) for e, v in c5.items()}}
            if not failed:
                ceil = jsonable(RC.slot_candidate_ceilings(roads, k, cand, engines=tuple(plants), dt=DT, jobs=jobs))
                # T on the gating engines only (row 95 (2)); every engine's C is in the result, and the
                # verdict over every engine given is kept under its own name, so one candidate has one
                # passes_T (the spec review)
                ceil["passes_T_every_engine_given"] = ceil.pop("passes_T")
                passes, at_15 = RC.passes_T(ceil["result"], engines=tuple(e for e in plants if e in gating))
                entry["ceilings"] = ceil
                entry["passes_T"] = {"passes": bool(passes), "at_r_1.5": jsonable(at_15),
                                     "engines": sorted(e for e in plants if e in gating)}
                if not passes:
                    failed.append({"test": "row 103 (2): the set's ceiling at r = 1.5 below T", "at_r_1.5": at_15})
            history.append(entry)
            if failed:
                discards += 1
            else:
                accepted = cand
        if accepted is None:
            stop = "discard bound"
            break
        redraws += 1
        ident, _ = identities([accepted], engines=tuple(plants), jobs=jobs, keep_arrays=True,
                              label=f"redraw {redraws} of slot {k}")
        roads[i] = accepted
        recheck, why, cvt = {}, [], None
        for e, p in plants.items():
            steps, res = c5_on_car(p, accepted, climb_of(accepted, k), margin=margins[e])
            recheck[e] = dict(c5_json(steps, res, with_steps=True), margin=margins[e])
            w = c5_failure(e, res, margin=margins[e])
            if w and e in gating:
                why.append(w)
            if e == CVT_ENGINE:
                # MD:1239-1240: decision 40's diagnostic again at the re-check, at the re-check margin,
                # redrawn climbs included, on the force the identity's neutral run gave the box
                cvt = cvt_diagnostics(p, accepted, climb_of(accepted, k), steps,
                                      ident[str(accepted["k"])][e]["arrays"], margin=margins[e])
        for x in ident[str(accepted["k"])].values():
            x.pop("arrays", None)
        history[-1].update(redraw=redraws, identity=ident, recheck=recheck, recheck_fails=why, cvt_diagnostic=cvt)
        kept = {"source": f"redraw {redraws}", "recheck": recheck, "fails": why}
        log(f"slot {k}: redraw {redraws} at grade {history[-1]['grade']:.6f}; re-check fails: {why or 'none'}")
    if stop:
        log(f"slot {k}: stopped at the {stop}; keeps its {kept['source']} climb, failing {kept['fails']}")
    return {"slot": k, "road": int(roads[i]["k"]), "redraws": redraws, "discarded": discards, "stopped_at": stop,
            "kept": kept["source"], "kept_grade": float(climb_of(roads[i], k)["grade"]),
            "gear_sensitive": kept["fails"],
            "thin_on": sorted(e for e, v in kept["recheck"].items() if v.get("thin")),
            "candidates": history}


def redraw(record, *, roads_sha_value, margins, margins_source, dropped, jobs, root, log, engines, max_slots):
    """The C5 re-check and the redraws after Run 2, from a roads record: refused before anything is drawn
    if any hashed file, version, plant_sha or engine_sha differs from the record's (row 97). Version 6
    (row 95 (2)): an engine whose drop is recorded leaves the gating, its C5 outcome and its ceilings still
    recorded; with a drop, version 5's reading (every engine gating) is run beside it and reported.
    max_slots is None for the redraws; the SYNTHETIC smoke run redraws its first failing slot only."""
    probs = verify_record(record, root=root)
    if probs:
        raise Refused(probs)
    if NEVER_DROPPED in dropped:
        raise Refused(["the B58 is never dropped (MD:1587-1592)"])
    RC = _ceiling_module()
    taus = record.get("tau") or {}
    missing = [e for e in engines if e not in taus or "tau_s" not in taus[e]]
    if missing:
        raise Refused([f"roads.json holds no tau for {missing}: the redraws read each tau from the record (row 102)"])
    RC.use_recorded_taus({e: (float(taus[e]["tau_s"]), taus[e].get("cell")) for e in engines})
    seed = int(record["commit_reveal"]["roads_seed"])
    plants = {e: plant_of(e) for e in engines}
    gating6 = set(engines) - set(dropped)
    readings = [("version 6", gating6)] + ([("version 5 (every engine gating)", set(engines))] if dropped else [])
    out = {"schema": REDRAWS_SCHEMA, "roads_sha": roads_sha_value, "seed_kind": record["seed_kind"],
           "margins": margins, "margins_source": margins_source, "dropped": sorted(dropped), "started": now_utc(),
           "readings": {}}
    for name, gating in readings:
        roads = copy.deepcopy(record["roads"])
        rc, failing = recheck_slots(roads, margins=margins, plants=plants, gating=gating, jobs=jobs)
        log(f"{name}: re-check on every car; slots failing: {failing}")
        slots = []
        todo = failing if max_slots is None else failing[:max_slots]
        for i, slot in slots_of(roads):
            if slot["slot"] in todo:
                slots.append(redraw_slot(roads, i, slot, roads_seed=seed, plants=plants, gating=gating,
                                         margins=margins, kept_recheck=rc[str(slot["slot"])], jobs=jobs, RC=RC,
                                         log=log))
        out["readings"][name] = {"gating": sorted(gating), "recheck": rc, "failing": failing, "slots": slots,
                                 "roads": roads}
    probs = verify_record(record, root=root)
    if probs and record["seed_kind"] == "REAL":
        raise CodingDefect("a hashed file, a version or a plant changed during the redraws: " + "; ".join(probs))
    if probs:
        log(f"SYNTHETIC run: these changed in the tree during the run (other work in progress): {probs}")
    out["changed_during_run"] = probs
    out["finished"] = now_utc()
    out["files_opened"] = files_opened()
    out["taus_read_from_the_record"] = {e: float(taus[e]["tau_s"]) for e in engines}
    return out


def load_record(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def dropped_problems(summary, dropped):
    """Row 95 (2): an engine leaves the gating once its section-7 drop is recorded; the drop is the one
    Run 2's summary.json records per engine (validate_epa._summary_entry's "drop", a boolean). A --dropped
    list that disagrees with it is refused: what the person recorded (step 11) and what Run 2 wrote must
    agree, or a row of its own says why (the spec review)."""
    probs = []
    for e in EPA_ENGINES:
        d = summary["engines"][e].get("drop")
        if not isinstance(d, bool):
            probs.append(f"{e}: summary.json's drop {d!r} is not a boolean")
        elif d != (e in dropped):
            probs.append(f"{e}: --dropped says {'dropped' if e in dropped else 'kept'}, summary.json's section 7 "
                         f"says {'dropped' if d else 'kept'}")
    return probs


def recheck_or_redraw(kind, *, summary_path, dropped, note, jobs, root, out_path):
    """The C5 re-check (kind "recheck") or the redraws ("redraw") after Run 2, from the committed roads
    record. Refused before anything is computed when: redraws.json exists (a redraw); roads.json's hashes,
    versions or plants are not the running code's (verify_record, row 97); --summary is not
    results/EPA_VALIDATION/summary.json; --dropped disagrees with summary.json's drops. A redraw, which
    uses roads_seed's 0xC5 streams (row 96: "any computation that uses roads_seed ... is an attempt"),
    is refused too unless the tree is clean, HEAD is pushed, roads.json is committed at HEAD, redraws.json
    was never committed, the attempts log was never rewritten, and _step_rules holds (no redraw run
    finished before; a note after a crash or a coding-defect stop). Both write a start line to the
    attempts log before they compute anything (the commit, whether the tree is clean, the summary's
    sha_text, the dropped list, the margins) and an outcome line after."""
    import epa_freeze
    from thresholds import common
    rec_path = os.path.join(root, ROADS_REL)
    if kind == "redraw" and os.path.exists(os.path.join(root, REDRAWS_REL)):
        raise Refused([f"{REDRAWS_REL} exists: it is written once (row 97)"])
    record = load_record(rec_path)
    probs = verify_record(record, root=root)
    if probs:
        raise Refused(probs)
    summary_path = summary_path_allowed(summary_path, root=root)
    with open(summary_path, encoding="utf-8") as fh:
        summary = json.load(fh)
    margins = margins_from_summary(summary, engines=ENGINES)
    probs = dropped_problems(summary, dropped)
    if probs:
        raise Refused(probs)
    source = {"path": os.path.relpath(os.path.abspath(summary_path), root).replace("\\", "/"),
              "sha_text": common.sha_text(summary_path)}
    log_path = os.path.join(root, ATTEMPTS_REL)
    head, clean, status = tree_state(root)
    pushed, remote_sha, why = remote_state(root, head)
    earlier = [x for x in read_attempts(log_path) if x.get("step") == kind]
    if kind == "redraw":
        probs, n, interrupted = _step_rules(earlier, what="the redraws", note=note)
        if not clean:
            probs.append("the tree is not clean: " + "; ".join(status[:10]))
        if not pushed:
            probs.append(why)
        if _show(root, "HEAD", ROADS_REL) is None:
            probs.append(f"{ROADS_REL} is not committed at HEAD: the redraws run from the committed roads record")
        if committed_versions(root, REDRAWS_REL):
            probs.append(f"{REDRAWS_REL} was committed in HEAD's history: it is written once (row 97)")
        probs += attempts_log_problems(root=root)[0]
        if probs:
            raise Refused(probs)
    else:
        n, interrupted = len([x for x in earlier if x.get("event") == "start"]) + 1, None
    entry = {"step": kind, "event": "start", "attempt": n, "kind": record["seed_kind"], "time": now_utc(),
             "commit": head, "clean": clean, "pushed": pushed, "remote_sha": remote_sha,
             "roads_sha": roads_sha(rec_path), "summary": source, "dropped": sorted(dropped), "margins": margins,
             "note": note, "follows_interrupted_attempt": interrupted, "jobs": int(jobs),
             "versions": epa_freeze.versions()}
    append_attempt(log_path, entry)
    end = {"step": kind, "event": "outcome", "attempt": n}
    steps = []
    log = make_log(steps)
    try:
        if kind == "recheck":
            roads = copy.deepcopy(record["roads"])
            rc, failing = recheck_slots(roads, margins=margins, plants={e: plant_of(e) for e in ENGINES},
                                        gating=set(ENGINES) - set(dropped), jobs=jobs)
            res = {"roads_sha": roads_sha(rec_path), "margins": margins, "margins_source": source,
                   "dropped": sorted(dropped), "recheck": rc, "failing": failing}
            log(f"re-check: failing slots {failing}")
            sha = write_once(out_path, res) if out_path else None
            outcome = {"outcome": "recheck", "failing": failing, "sha_text": sha}
        else:
            res = redraw(record, roads_sha_value=roads_sha(rec_path), margins=margins, margins_source=source,
                         dropped=tuple(dropped), jobs=jobs, root=root, log=log, engines=ENGINES, max_slots=None)
            res["steps_log"] = steps
            sha = write_once(os.path.join(root, REDRAWS_REL), res)
            print(f"redraws.json written: sha_text {sha}")
            outcome = {"outcome": "redraws", "sha_text": sha}
    except RoadsStop as exc:
        append_attempt(log_path, _outcome(end, outcome="stop", coding_defect=isinstance(exc, CodingDefect),
                                          reason=str(exc)))
        raise
    except BaseException as exc:
        append_attempt(log_path, _outcome(end, outcome="crash", reason=f"{type(exc).__name__}: {exc}",
                                          traceback=traceback.format_exc()[-4000:]))
        raise
    append_attempt(log_path, _outcome(end, **outcome))
    return res


# =====================================================================================================
# The command line
# =====================================================================================================
def _dropped(text):
    if text == "none":
        return ()
    out = tuple(x.strip() for x in text.split(",") if x.strip())
    bad = [x for x in out if x not in EPA_ENGINES]
    if bad:
        raise Refused([f"--dropped names {bad}, not EPA engines (the B58 is never dropped)"])
    return out


def _delegate(name, jobs):
    """control, sweep and timing are roads_ceiling's: its function, its text and its own writer
    (results/EPA_ROADS/<name>.json and .txt), exactly as `python roads_ceiling.py <name>` runs them."""
    RC = _ceiling_module()
    missing = [f for f in (name, f"{name}_text", "write_record") if not hasattr(RC, f)]
    if missing:
        raise Refused([f"roads_ceiling has no {missing}"])
    res = getattr(RC, name)(jobs=jobs)
    txt = getattr(RC, f"{name}_text")(res)
    RC.write_record(name, res, txt, out_dir=RC.OUT_DIR)
    sys.stdout.write(txt)
    return res


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="epa_roads.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("control", "sweep", "timing"):
        s = sub.add_parser(name)
        s.add_argument("--jobs", type=int, required=True)
    s = sub.add_parser("smoke")
    s.add_argument("--synthetic-seed", type=int, required=True, help="a SYNTHETIC seed, an int below 2**32")
    s.add_argument("--out", default=None, help="a folder outside the repository (default: a new temporary one)")
    s.add_argument("--jobs", type=int, default=4)
    s.add_argument("--with-redraw", action="store_true")
    s.add_argument("--full", action="store_true", help="the real draw's path on 1 road and the four engines")
    sub.add_parser("commitment")
    s = sub.add_parser("draw")
    s.add_argument("--reveal-g", required=True)
    s.add_argument("--reveal-j", required=True)
    s.add_argument("--roads-commit", required=True, help="the roads commit's full sha, as announced before the reveal")
    s.add_argument("--note", default=None, help="a later attempt: the defect and the commits that fixed it")
    s.add_argument("--jobs", type=int, required=True)
    for name in ("recheck", "redraw"):
        s = sub.add_parser(name)
        s.add_argument("--summary", required=True, help=SUMMARY_REL)
        s.add_argument("--dropped", required=True, help="comma-separated EPA engines whose drop is recorded, or none")
        s.add_argument("--note", default=None, help="a later redraw run: the defect and the commits that fixed it")
        s.add_argument("--jobs", type=int, required=True)
        if name == "recheck":
            s.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    try:
        allow = (summary_path_allowed(a.summary, root=REPO),) if a.cmd in ("recheck", "redraw") else ()
        install_guard(allow)
        if a.cmd in ("control", "sweep", "timing"):
            _delegate(a.cmd, a.jobs)
        elif a.cmd == "commitment":
            x = new_private_integer()
            print("Your private integer (keep it offline, where it cannot be lost; reveal it only after the roads "
                  "commit is pushed, at the same time as the other person, row 96):")
            print(f"  {x}")
            print("Its hash line, for epa_roads.py's COMMITMENT_G (Ghassan) or COMMITMENT_J (Jad), set in the "
                  "roads commit:")
            print(f"  {commitment_hash(x)!r}")
        elif a.cmd == "smoke":
            if a.out is None:
                import tempfile
                a.out = tempfile.mkdtemp(prefix="epa_roads_smoke_")
            print(f"SYNTHETIC smoke run, writing to {a.out}", flush=True)
            smoke(a.synthetic_seed, out_dir=a.out, jobs=a.jobs, with_redraw=a.with_redraw, full=a.full)
        elif a.cmd == "draw":
            draw(a.reveal_g, a.reveal_j, roads_commit_announced=a.roads_commit, note=a.note, root=REPO, jobs=a.jobs)
        else:
            recheck_or_redraw(a.cmd, summary_path=a.summary, dropped=_dropped(a.dropped), note=a.note, jobs=a.jobs,
                              root=REPO, out_path=getattr(a, "out", None))
    except Refused as exc:
        print("REFUSED:\n  " + "\n  ".join(exc.args[0] if exc.args and isinstance(exc.args[0], list)
                                           else [str(exc)]), file=sys.stderr)
        return 2
    except RoadsStop as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())

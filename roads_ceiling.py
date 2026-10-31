"""roads_ceiling.py -- decision 34's ceiling on a road set, and everything row 103 (1) reports beside it.

    python roads_ceiling.py control [--jobs N]   the B58's locked climb against results/premise.json, and
                                                 the direct-run lambda rows -> results/EPA_ROADS/control.*
    python roads_ceiling.py sweep [--jobs N]     row 101's sweep before the draw -> results/EPA_ROADS/sweep.*
    python roads_ceiling.py timing [--jobs N]    one 900 s SYNTHETIC road timed closed loop
                                                 -> results/EPA_ROADS/timing.*
    python roads_ceiling.py smoke --out DIR      report() on one short SYNTHETIC road, written to DIR only

Section I of results/VALIDATION_DECISIONS.md governs this file: rows 99-103 (the ceiling, its
companions, tau and H), row 100 (E6 rows 4 and 11, decision 13's count) and row 101 (the road design,
the sweep, the dt 0.5 s repeat). docs/build_step_2/ORDER_TO_TRAINING.md step 4 builds it. The roads
module (epa_roads.py, row 94) owns the generator, the streams, the slots, the replacement loop, C5,
the identities and the records; it hands this module its roads and calls the functions below. The
road dict and the function signatures are the interface the two modules share:

    a road  {"k", "episode_seed", "weights": [w0, w1, w2], "dt": 1.0,
             "cycle": {"t", "v_mps", "grade", "t_amb", "p_baro", "humidity"},   lists of floats
             "climbs": [{"slot", "onset_s", "L_s", "grade", "first_step", "last_step"}, ...]}

    tau_s(engine_id)                    row 102's one definition of tau
    ceilings(roads, *, engines, ratios, dt, jobs, variants, readings)
    passes_T(result, *, engines)        row 103 (2)
    slot_candidate_ceilings(roads, slot, candidate_road, *, engines, dt, jobs)
    report(roads, *, engines, dt, jobs) every companion row 103 (1) lists, rows 99-102's reports
    control(*, jobs) / sweep(*, jobs) / timing(*, jobs)

THE CEILING (row 103 (1); version 6). C_e(S, r) = the mean over the roads of S of each road's points,
100 (D_cg - D_a) / D_base, in the no-knock reading: the turbine and oil terms of the engine's own damage
model at its own knee (engine_env.damage_rate without the knock integral, cal = plant.engine.damage, the
reading evaluate.run_episode calls damage_thermal). D_base is the same damage of the environment's
parallel baseline network on the same run (SupervisoryTunerEnv.thermal_base). cg is
check_premise.p_grade_now, imported unchanged at row 99's depths. (a) is cg with the lambda trim
commanded at its bound, engine_env.ACT_LO[1] = -0.15 (the normalised action -1), for the H = r tau_e
seconds before each climb's first step; the window starts no earlier than the end of the previous
climb's full grade (its onset + L, where its ramp down begins), or 20 s into the road for the road's
first climb. The trim's slew is the environment's own (SLEW 0.03 per second). Every (road, engine,
policy) is one closed-loop run of the frozen plant at dt 1 s with road k's frozen seed and weights: a
direct run, not a replay, because section G's open-loop rows overstated the lambda bound by about two
times (row 103; control() below prints the direct-run rows that replace them).

THE COMPANIONS, each deciding nothing and labelled as row 103 labels them: the with-knock reading
("not converged in dt on these roads", row 101); r = 0.5; (b) lambda at its bound over each whole gap;
(a_b) lambda at its bound from 50 s after each ramp down starts (150 s on the lead-in) until the onset,
with C_blind = 100 (D_cg - D_ab) / D_base and C_u = 100 (D_ab - D_a) / D_base; (c) the exhaust at
ambient over (a)'s windows, replayed on the housing node from cg's own recorded inputs; the head-start
part of each saving, outside the lever's windows; the extra fuel of (a), (b) and (a_b); for each road's
weights, the variant with the highest episode reward in the sighted set {cg, a, a_b, b} and in the
blind set {cg, a_b, b}; the pooled form (sum saved over sum base), the median of the road points and
evaluate.py's form (100 (median D_cg - median D_a) / median D_neutral, the neutral policy's damage
being evaluate.py's "baseline ECU" row); section G's trace-replay value (cg's housing replayed with
the exhaust lowered by the drop results/preview_ceiling.py assumes, at cg's flow); every engine's C
against 2 MEI (version 5's test, reported as such).

A FLAT SLOT (row 101: a slot whose 100 replacement grades all failed is made flat road and keeps its
index) has grade 0 and is no climb: it opens no lever window and ends none.

E6 ROW 11'S WRAPPER (row 100 (2)). The charge temperature is plant.charge_temperature, t_amb + rise_k +
block_coupling (t_block - t_amb) (plant.py:573-576), affine in engines.ChargeCal.rise_k with slope one,
and rise_k is read nowhere else. So charge_shifted(plant, offset_k=+-6.3) -- epa_fit.perturbed on that
one field, outside PLANT_CODE, no file edited -- is a plant whose charge temperature is the frozen one
plus exactly the offset at every input, the ECU's, the cycle's and both networks' alike, and nothing
else of the plant moves (test_roads_ceiling.py proves both, and that the damage moves: mistake 12).

TAU (row 102). tau_e = epa_coefficients.housing(plant, cell["egt"], cell["mdot"], t_amb_c=T_AMB_C)
["tau_s"] at cell = epa_coefficients.climb_cell(plant), on every engine, the B58 included. For the
three EPA engines it equals complete.json's e6_row4.frozen.tau_s exactly (test_roads_ceiling.py).

WHAT IT READS. The four frozen plants (engines.get), results/premise.json (control), the committed
traces results/preview_ceiling.py reads (section G's assumed drop), and results/EPA_CALIBRATION/<id>/
complete.json (E6 row 4's frozen tau, beside the recomputed one). Never an EPA table, a logs/epa file,
a validation record or any .csv: every worker process, and this process before its first in-process
run, installs an audit hook that refuses them (_forbidden), matched anywhere in the normalised path, and
records every repository file it opens (OPENED; a worker returns its set with each result), so that
the roads record lists what the workers read. It writes only results/EPA_ROADS/control.*, sweep.* and
timing.* (the CLI), or the directory the smoke run is given. A re-check or a redraw reads each tau from
the roads record (use_recorded_taus) and never recomputes it (row 102).

SYNTHETIC ROADS. No roads_seed exists until the reveal (row 96). synthetic_roads() draws row 101's
family from a SYNTHETIC seed, for timing, smoke runs and tests only: it is not the generator of record
(epa_roads.generate), it refuses any seed of 2**32 or more (roads_seed is a 60-bit integer, so it can
never be passed here by mistake), and every road it makes carries "label": "SYNTHETIC".

Every function that runs a plant takes the engine explicitly; none has a default engine (mistake 1;
test_engine_threading). Numbers are written to the records the functions return; the CLI writes them.
"""
import argparse
import hashlib
import json
import math
import os
import re
import statistics
import subprocess
import sys
import time

import numpy as np

import check_premise as CP
import engine_env as E
import engines as engine_registry      # the module: `engines` is the interface's parameter name
import evaluate as V
from thermal import ThermalNetwork

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "results", "EPA_ROADS")
PREMISE = os.path.join(HERE, "results", "premise.json")
CALIBRATION_DIR = os.path.join(HERE, "results", "EPA_CALIBRATION")

# ------------------------------------------------------------------ the interface's constants
ENGINES = ("b58", "mazda_25t", "honda_l15b7", "ford_27tt")
EPA_ENGINES = ("mazda_25t", "honda_l15b7", "ford_27tt")
MEI = 5.43                          # points of cut (decision 5, VD:57; thresholds.contract.MEI)
T_POINTS = MEI / 4                  # row 103 (2): the bar at the draw and at every redraw
TWO_MEI = 2 * MEI                   # decision 34's (version 5's) bar, reported per engine
RATIOS = (0.5, 1.5)                 # row 102: H = r tau_e, the same on every engine
GRID_RATIOS = (0.5, 2 / 3, 1.0, 1.25, 1.5, 1.947)    # row 102's H/tau axis, as the row writes it
GRID_H_S = (20.0, 30.0, 45.0, 65.0, 100.0, 130.0)    # row 102's H axis, s

# ------------------------------------------------------------------ the design's values (rows 99, 101, 103)
DT = 1.0                            # row 101
DT_REPEAT = 0.5                     # row 101: the dt 0.5 s repeat of cg and (a) at r = 1.5
RAMP_S = float(E.GRADE_RAMP_S)      # 8 s, every grade change (row 98 (a))
SPEED_RAMP_S = 20.0                 # make_grade_climb's 0 -> v over the first 20 s
LAM_INDEX = 1                       # the action's lambda trim
LAM_BOUND = float(E.ACT_LO[LAM_INDEX])               # -0.15
LAM_BOUND_NORM = -1.0               # the normalised action that rescales to ACT_LO
FIRST_WINDOW_FROM_S = 20.0          # (a) and (b): the first climb's window starts no earlier
AB_DELAY_S = 50.0                   # (a_b): 50 s after each ramp down starts ...
AB_LEAD_FROM_S = 150.0              # ... and from 150 s on the lead-in
DESIGN_V_KMH = 130.0                # row 101
DESIGN_T_AMB_K = 315.0              # row 101: 315 K, 101.3 kPa, humidity 0.012
SWEEP_GRADES = tuple((1000 + 5 * i) / 10000.0 for i in range(41))   # 10.00 ... 12.00 %, 0.05 % steps
SWEEP_DURATION_S = 720.0            # the locked climb's length; its grade from 180 s (make_grade_climb)
SWEEP_ONSET_S = 180.0
C5_MARGIN = 0.019                   # C5 at 1.9 % (MD:1401-1405), a fraction
DESIGN_LONGEST_FULL_GRADE_S = 77.0  # L - 8 s at the design's longest L, 85 s (row 101)
SWEEP_DESIGN_L_S = (67.0, 85.0)     # row 101's shortest and longest L: the sweep's C5 over a slot's extent
TORQUE_SHORT = 0.95                 # decision 13: steps under 95 % of the requested torque
CHARGE_OFFSET_K = 6.3               # E6 row 11 (MD:989): the B58's input uncertainty
ROW4_FIELDS = ("c_turb", "ua_gas_turb", "ua_turb_amb")   # E6 row 4 (MD:982; calibrate_epa.ROW4_FIELDS)
ROW4_FACTORS = (0.75, 1.333)        # MD:982; complete.json's e6_row4 keys "x0.75" and "x1.333"
OBS_CLIP = 10.0                     # engine_env.py's observation clip
READINGS = ("noknock", "knock")
ALL_VARIANTS = ("cg", "a", "b", "a_b", "neutral", "c", "G")
KNOCK_LABEL = "not converged in dt on these roads"
COMPANION_LABEL = "savings of hand-written lambda strategies over current-grade, never bounds on d"
OBS_NAMES = ("rpm", "map", "tps", "spark", "lambda", "t_block", "t_oil", "t_turb", "iat", "t_amb",
             "p_baro", "humidity", "v", "grade", "preview_2s", "preview_5s", "preview_15s", "preview_30s",
             "torque_req", "aggression", "w_track", "w_fuel", "w_life")

# SYNTHETIC seeds: tests, smoke runs and timing only (row 96: no roads_seed exists before the reveal)
SYNTHETIC = "SYNTHETIC"
SYNTHETIC_SEED_LIMIT = 2 ** 32
SYNTHETIC_SEED_TIMING = 101
SYNTHETIC_SEED_SMOKE = 202

# control(): the probe's horizons (repro.py HS), and the locked climb's onset
CONTROL_HS = (14, 15, 30, 45, 47, 60, 90, 100, 130, 150)
LOCKED_ONSET_S = 180.0
LOCKED_DURATION_S = 720.0
PREMISE_NEUTRAL = "baseline ECU (true neutral)"
PREMISE_CG = "current-grade protection"

# this file as it was imported: the records name the code that ran, not a later edit of it
with open(os.path.abspath(__file__), "rb") as _fh:
    MODULE_SHA256 = hashlib.sha256(_fh.read()).hexdigest()

if E.OBS_DIM != len(OBS_NAMES):
    raise ImportError(f"roads_ceiling: engine_env.OBS_DIM is {E.OBS_DIM}, OBS_NAMES names {len(OBS_NAMES)}")
if E.ACT_LO[LAM_INDEX] != np.float32(-0.15) or float(E.ACT_LO[LAM_INDEX] + (LAM_BOUND_NORM + 1.0) * 0.5
                                                    * (E.ACT_HI[LAM_INDEX] - E.ACT_LO[LAM_INDEX])) != LAM_BOUND:
    raise ImportError("roads_ceiling: the lambda bound is not engine_env.ACT_LO[1] = -0.15 at action -1")


# ------------------------------------------------------------------ the guard
def _forbidden(path):
    """Whether a path is a file this module never opens: logs/epa*, data/engines/<id>/epa_*,
    results/EPA_VALIDATION/** or any .csv (hard rule of the roads step; WP3_INTERFACES.md 9.1's
    spirit). Matched anywhere in the normalised path, as epa_roads.refused_path matches it, so that a
    \\\\?\\ long path or an exported copy of the tree is refused too (the integrity review, 30 October)."""
    try:
        s = os.path.abspath(os.fsdecode(path)).replace("\\", "/").lower()
    except (TypeError, ValueError):
        return False
    return ("logs/epa" in s or re.search(r"data/engines/[^/]+/epa_", s) is not None
            or "epa_validation" in s or s.endswith(".csv"))


# The repository files this process opened (the hook records them; a worker returns its own set with
# each result and execute() merges it here), so that the roads record lists the files every worker read.
OPENED = set()


def _note_open(path):
    try:
        a = os.path.abspath(os.fsdecode(path))
    except (TypeError, ValueError):
        return
    if os.path.normcase(a).startswith(os.path.normcase(HERE) + os.sep):
        rel = os.path.relpath(a, HERE).replace("\\", "/")
        if not (rel.startswith((".venv/", ".git/")) or "/__pycache__/" in f"/{rel}"):
            OPENED.add(rel)


def _hook(event, args):
    if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        if _forbidden(args[0]):
            raise PermissionError(f"roads_ceiling guard: refused to open {os.fsdecode(args[0])}")
        _note_open(args[0])


_GUARD = []


def install_guard():
    """Install the audit hook once per process (a hook cannot be removed: it stays)."""
    if not _GUARD:
        sys.addaudithook(_hook)
        _GUARD.append(True)


def _worker_init():
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    install_guard()


# ------------------------------------------------------------------ roads
def _const(x, what):
    """A cycle scalar given as a number or as a constant list."""
    if isinstance(x, (list, tuple, np.ndarray)):
        a = np.asarray(x, dtype=float)
        if a.size == 0 or not np.all(a == a[0]):
            raise ValueError(f"roads_ceiling: the cycle's {what} is not constant; the environment reads one value")
        return float(a[0])
    return float(x)


CYCLE_KEYS = ("t", "v_mps", "grade", "t_amb", "p_baro", "humidity")


def check_road(road):
    """Refuse a road that is not the interface's dict (every key named; the cycle's ambient, pressure
    and humidity explicit, since the environment's defaults are not the design's: humidity 0.01 there,
    0.012 in row 101)."""
    for key in ("k", "episode_seed", "weights", "dt", "cycle", "climbs"):
        if key not in road:
            raise KeyError(f"roads_ceiling: a road has no {key!r}")
    for key in CYCLE_KEYS:
        if key not in road["cycle"]:
            raise KeyError(f"roads_ceiling: road {road['k']}'s cycle has no {key!r}")
    n = len(road["cycle"]["t"])
    if len(road["cycle"]["v_mps"]) != n or len(road["cycle"]["grade"]) != n:
        raise ValueError(f"roads_ceiling: road {road['k']}'s arrays differ in length")
    if len(road["weights"]) != 3:
        raise ValueError(f"roads_ceiling: road {road['k']}'s weights are not three")
    t = np.asarray(road["cycle"]["t"], dtype=float)
    if n > 1 and not np.allclose(np.diff(t), float(road["dt"]), rtol=0, atol=1e-9):
        raise ValueError(f"roads_ceiling: road {road['k']}'s t does not step at its dt {road['dt']!r}")
    return road


def _json_default(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, np.generic):
        return o.item()
    raise TypeError(f"roads_ceiling: {type(o).__name__} is not JSON-able")


def road_sha(road):
    """sha256 of the road as canonical JSON (sorted keys): the cache's name for it."""
    return hashlib.sha256(json.dumps(road, sort_keys=True, default=_json_default).encode("utf-8")).hexdigest()


def climbs_of(road):
    """The road's climbs that are climbs (grade > 0), in onset order: (onset_s, L_s, grade, record)."""
    out = [(float(c["onset_s"]), float(c["L_s"]), float(c["grade"]), c)
           for c in road["climbs"] if float(c["grade"]) > 0.0]
    return sorted(out, key=lambda x: x[0])


def _family_arrays(road, *, dt):
    """The road's speed and grade at time step dt, from its climbs, as row 101 (and the probe's
    lib.road) builds them: 0 -> v over the first 20 s, then held; each climb ramps up over 8 s from
    its onset s, holds its grade to s + L and ramps down over 8 s."""
    c = road["cycle"]
    duration = len(c["t"]) * float(road["dt"])
    n = int(round(duration / dt))
    t = np.arange(n) * dt
    v_hold = float(c["v_mps"][-1])
    v = np.full(n, v_hold)
    v[:int(SPEED_RAMP_S / dt)] = np.linspace(0.0, v_hold, int(SPEED_RAMP_S / dt))
    g = np.zeros(n)
    for s, L, gr, _c in climbs_of(road):
        up = np.clip((t - s) / RAMP_S, 0.0, 1.0)
        down = np.clip(1.0 - (t - (s + L)) / RAMP_S, 0.0, 1.0)
        g = np.maximum(g, gr * np.minimum(up, down))
    return t, v, g


def env_cycle(road, *, dt):
    """The environment's cycle dict for the road at time step dt. At the road's own dt, its arrays as
    given. At another dt (row 101's 0.5 s repeat), the road rebuilt at that dt from its climbs, but only
    if the rebuild at the road's own dt gives back the road's arrays (else ValueError: the road is not
    the family's, and resampling it would invent a road)."""
    check_road(road)
    c = road["cycle"]
    scal = dict(t_amb=_const(c["t_amb"], "t_amb"), p_baro=_const(c["p_baro"], "p_baro"),
                humidity=_const(c["humidity"], "humidity"))
    if float(dt) == float(road["dt"]):
        return dict(t=np.asarray(c["t"], dtype=float), v_mps=np.asarray(c["v_mps"], dtype=float),
                    grade=np.asarray(c["grade"], dtype=float), **scal)
    t0, v0, g0 = _family_arrays(road, dt=float(road["dt"]))
    if not (np.allclose(v0, np.asarray(c["v_mps"], float), rtol=0, atol=1e-12)
            and np.allclose(g0, np.asarray(c["grade"], float), rtol=0, atol=1e-12)):
        raise ValueError(f"roads_ceiling: road {road['k']}'s arrays are not its climbs' ramps; it cannot be "
                         f"rebuilt at dt {dt!r}")
    t, v, g = _family_arrays(road, dt=float(dt))
    return dict(t=t, v_mps=v, grade=g, **scal)


def _windows_before(onsets_L, *, H, first_from):
    """[start, onset) before each climb: H seconds (None: the whole gap), starting no earlier than the
    previous climb's full-grade end (its onset + L) or `first_from` for the first climb. Empty windows
    are dropped."""
    out, prev_end = [], first_from
    for s, L in onsets_L:
        a = prev_end if H is None else max(s - H, prev_end)
        if a < s:
            out.append((float(a), float(s)))
        prev_end = s + L
    return tuple(out)


def windows_a(road, *, H):
    """(a)'s windows: the H s before each climb's first step (row 103 (1))."""
    return _windows_before([(s, L) for s, L, _g, _c in climbs_of(road)], H=float(H), first_from=FIRST_WINDOW_FROM_S)


def windows_b(road):
    """(b)'s windows: each whole gap, from the previous climb's full-grade end (20 s on the lead-in)."""
    return _windows_before([(s, L) for s, L, _g, _c in climbs_of(road)], H=None, first_from=FIRST_WINDOW_FROM_S)


def windows_ab(road):
    """(a_b)'s windows: from 50 s after each ramp down starts (150 s on the lead-in) until the onset."""
    out, start = [], AB_LEAD_FROM_S
    for s, L, _g, _c in climbs_of(road):
        if start < s:
            out.append((float(start), float(s)))
        start = s + L + AB_DELAY_S
    return tuple(out)


def in_windows(t, wins):
    return any(a <= t < b for a, b in wins)


def family_road(*, k, episode_seed, weights, lead_s, climbs, v_kmh, duration_s, dt, t_amb_k, slot_start,
                label):
    """A road of row 101's shape from explicit parameters: a flat lead-in, then climbs (L_s, grade,
    gap_after_s) whose onsets follow s_{i+1} = s_i + L_i + G_i; arrays as _family_arrays builds them; the
    ambient 315 K row's 101.3 kPa and humidity 0.012. For hand-made test roads, the probe's families and
    SYNTHETIC draws; never the roads of record."""
    onsets, s = [], float(lead_s)
    for L, g, G in climbs:
        onsets.append((s, float(L), float(g)))
        s = s + float(L) + float(G)
    n = int(round(float(duration_s) / dt))
    rec = []
    for i, (s, L, g) in enumerate(onsets):
        rec.append(dict(slot=int(slot_start + i), onset_s=s, L_s=L, grade=g, first_step=int(round(s / dt)),
                        last_step=int(round((s + L + RAMP_S) / dt))))
    stub = dict(k=int(k), dt=float(dt), climbs=rec,
                cycle=dict(t=[0.0] * n, v_mps=[float(v_kmh) / 3.6] * n))
    t, v, g = _family_arrays(stub, dt=float(dt))
    return dict(k=int(k), episode_seed=int(episode_seed), weights=[float(w) for w in weights], dt=float(dt),
                cycle=dict(t=[float(x) for x in t], v_mps=[float(x) for x in v], grade=[float(x) for x in g],
                           t_amb=[float(t_amb_k)] * n, p_baro=[101.3] * n, humidity=[0.012] * n),
                climbs=rec, label=label)


def synthetic_roads(synthetic_seed, *, n_roads, duration_s):
    """SYNTHETIC roads of row 101's family, for timing, smoke runs and tests only (not the generator of
    record, epa_roads.generate). Draw order as row 101 writes it: per road the lead-in integers(150, 211),
    then L integers(67, 86), g uniform(0.10, 0.12) and G integers(50, 151) for each climb in turn; a
    climb is kept only if its ramp down ends at least 60 s before the road's end, and the draws of one
    that does not fit are made and discarded. Road k is paired with evaluate.EPISODES[k % 20]. A seed of
    2**32 or more is refused: roads_seed (row 96) is a 60-bit integer and must never reach this."""
    if not isinstance(synthetic_seed, int) or not (0 <= synthetic_seed < SYNTHETIC_SEED_LIMIT):
        raise ValueError(f"synthetic_roads: {synthetic_seed!r} is not a SYNTHETIC seed (an int below 2**32)")
    rng = np.random.default_rng(synthetic_seed)
    roads, slot = [], 0
    for k in range(n_roads):
        lead = int(rng.integers(150, 211))
        s, climbs = lead, []
        while True:
            L = int(rng.integers(67, 86))
            g = float(rng.uniform(0.10, 0.12))
            G = int(rng.integers(50, 151))
            if s + L + RAMP_S > duration_s - 60.0:
                break
            climbs.append((L, g, G))
            s = s + L + G
        seed, w = V.EPISODES[k % len(V.EPISODES)]
        roads.append(family_road(k=k, episode_seed=seed, weights=w, lead_s=lead, climbs=climbs,
                                 v_kmh=DESIGN_V_KMH, duration_s=duration_s, dt=DT, t_amb_k=DESIGN_T_AMB_K,
                                 slot_start=slot, label=f"{SYNTHETIC} (seed {synthetic_seed}, not roads_seed)"))
        slot += len(climbs)
    return roads


# ------------------------------------------------------------------ plants
_PLANTS = {}


def charge_shifted(plant, *, offset_k):
    """E6 row 11's wrapper (row 100 (2)): the plant with its charge temperature moved by offset_k at
    every input. plant.charge_temperature is t_amb + rise_k + block_coupling (t_block - t_amb), so moving
    engines.ChargeCal.rise_k by offset_k moves it by exactly offset_k, and nothing else reads rise_k.
    Built by epa_fit.perturbed, outside PLANT_CODE: a new plant, the frozen one untouched."""
    import epa_fit
    if type(offset_k) is not float:
        raise TypeError(f"charge_shifted: offset_k must be a Python float, not {type(offset_k).__name__}")
    return epa_fit.perturbed(plant, record="charge", field="rise_k",
                             value=float(plant.engine.charge.rise_k) + offset_k)


def plant_for(engine_id, variant):
    """The plant a run uses, memoised per process: ("frozen",); ("thermal", field, factor), E6 row 4's
    perturbation as calibrate_epa.py:2645-2652 builds it; ("one_housing",), row 102's Ford with
    n_turbines 1; ("charge", offset_k), E6 row 11."""
    key = (engine_id, tuple(variant))
    if key not in _PLANTS:
        p = engine_registry.get(engine_id)
        kind = variant[0]
        if kind == "frozen":
            pass
        elif kind == "thermal":
            import epa_fit
            field, factor = variant[1], float(variant[2])
            p = epa_fit.perturbed(p, record="thermal", field=field,
                                  value=float(getattr(p.engine.thermal, field)) * factor)
        elif kind == "one_housing":
            import epa_fit
            p = epa_fit.perturbed(p, record="thermal", field="n_turbines", value=1)
        elif kind == "charge":
            p = charge_shifted(p, offset_k=float(variant[1]))
        else:
            raise ValueError(f"roads_ceiling: unknown plant variant {variant!r}")
        _PLANTS[key] = p
    return _PLANTS[key]


def tau_of_plant(plant):
    """Row 102's definition on any plant: the housing's time constant at the plant's climb cell.
    Returns (tau_s, cell)."""
    import epa_coefficients as EC
    cell = EC.climb_cell(plant)
    hs = EC.housing(plant, cell["egt"], cell["mdot"], t_amb_c=EC.T_AMB_C)
    return float(hs["tau_s"]), cell


_TAUS = {}


def tau_s(engine_id):
    """Row 102's tau of the frozen engine, s (one neutral locked climb, about a minute; memoised)."""
    key = (engine_id, ("frozen",))
    if key not in _TAUS:
        install_guard()
        _TAUS[key] = tau_of_plant(plant_for(engine_id, ("frozen",)))
    return _TAUS[key][0]


def frozen_tau_record(engine_id):
    """complete.json's e6_row4 of an EPA engine (its frozen tau and the row-4 taus), or None."""
    path = os.path.join(CALIBRATION_DIR, engine_id, "complete.json")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh).get("e6_row4")


# ------------------------------------------------------------------ policies and runs
def _lam_policy(wins):
    def p(env, obs):
        a = CP.p_grade_now(env, obs)
        if in_windows(float(env.cycle["t"][env.k]), wins):
            a = np.array(a, dtype=np.float32).copy()
            a[LAM_INDEX] = LAM_BOUND_NORM
        return a
    return p


def make_policy(spec):
    """A policy from its spec: ("cg",), ("neutral",), ("reactive",), ("pred",), or ("lam", windows): cg
    with the lambda trim commanded at its bound inside the windows."""
    kind = spec[0]
    if kind == "cg":
        return CP.p_grade_now
    if kind == "neutral":
        return CP.p_neutral
    if kind == "reactive":
        return CP.p_reactive
    if kind == "pred":
        return CP.p_predictive
    if kind == "lam":
        return _lam_policy(tuple(tuple(w) for w in spec[1]))
    raise ValueError(f"roads_ceiling: unknown policy {spec!r}")


def damage_split(T, O, K, *, cal, dt):
    """Per-step turbine, oil and knock terms of the engine's damage model (engine_env.damage_rate's
    three terms, written out so they can be reported apart); their sum is checked against
    damage_rate itself at every step (mistake 10: a copy that drifts is refused)."""
    T, O, K = (np.asarray(x, dtype=float) for x in (T, O, K))
    turb = np.exp((T - cal.turb_knee_k) / cal.turb_scale_k) * dt
    oil = cal.oil_weight * np.exp((O - cal.oil_knee_k) / cal.oil_scale_k) * dt
    knock = cal.ki_weight * np.clip(K - cal.ki_knee, 0.0, None) ** 2 * dt
    ref = np.array([E.damage_rate(a, b, c, cal=cal) for a, b, c in zip(T, O, K)]) * dt
    if not np.allclose(turb + oil + knock, ref, rtol=1e-12, atol=0.0):
        raise AssertionError("roads_ceiling.damage_split: the split no longer sums to engine_env.damage_rate")
    return turb, oil, knock


def run_episode_record(plant, cycle, policy, *, seed, weights, dt, egt_ambient_windows, detail):
    """One closed-loop episode, as evaluate.run_episode runs it (the weights pinned after reset), with
    every per-step quantity the reports read. egt_ambient_windows: where the step's time lies in them,
    the AGENT's housing is fed exhaust at ambient (the impossible row, closed loop; control only), by an
    instance wrapper on env.thermal.step that also records what the network was given. detail: "light"
    (totals, per-step no-knock damage, observation ranges), "cg" (plus temperatures, torques and the
    network's inputs, for the replays and the delivery counts) or "full"."""
    env = E.SupervisoryTunerEnv(cycle, plant=plant, dt=dt, seed=seed, use_preview=True)
    obs, _ = env.reset(seed=seed)
    env.w = np.asarray(weights, dtype=np.float32)
    obs = env._obs()
    inputs = []
    orig = env.thermal.step
    wins = tuple(egt_ambient_windows or ())

    def step(dt_, mf, mex, egt_k, t_amb, vm, fan, pump, *, rpm):
        if wins and in_windows(float(env.cycle["t"][env.k]), wins):
            egt_k = t_amb
        inputs.append((dt_, mf, mex, egt_k, t_amb, vm, float(fan), float(pump), rpm))
        return orig(dt_, mf, mex, egt_k, t_amb, vm, fan, pump, rpm=rpm)
    env.thermal.step = step
    dm = plant.engine.damage
    o_min = np.array(obs, dtype=float)
    o_max = np.array(obs, dtype=float)
    o_clip = (np.abs(np.asarray(obs, dtype=float)) >= OBS_CLIP).astype(int)
    keys = ("t", "t_turb", "t_oil", "ki", "tb_turb", "tb_oil", "torque", "torque_req", "fuel", "lam_trim",
            "mdot_exh", "egt_k", "ret")
    rec = {k: [] for k in keys}
    ret, term, info = 0.0, False, {}
    t0 = time.perf_counter()
    while True:
        t = float(env.cycle["t"][env.k])
        a = policy(env, obs)
        obs, r, term, trunc, info = env.step(a)
        ret += r
        ob = np.asarray(obs, dtype=float)
        o_min = np.minimum(o_min, ob)
        o_max = np.maximum(o_max, ob)
        o_clip += (np.abs(ob) >= OBS_CLIP).astype(int)
        rec["t"].append(t)
        rec["t_turb"].append(info["t_turb"])
        rec["t_oil"].append(info["t_oil"])
        rec["ki"].append(info["ki"])
        rec["tb_turb"].append(env.thermal_base.t_turb)
        rec["tb_oil"].append(env.thermal_base.t_oil)
        rec["torque"].append(info["torque"])
        rec["torque_req"].append(info["torque_req"])
        rec["fuel"].append(info["mdot_fuel"] * dt)
        rec["lam_trim"].append(float(env.prev_act[LAM_INDEX]))
        rec["mdot_exh"].append(info["mdot_exh"])
        rec["egt_k"].append(inputs[-1][3])
        rec["ret"].append(r)
        if term or trunc:
            break
    seconds = time.perf_counter() - t0
    if term:
        raise RuntimeError("roads_ceiling: the episode terminated (a non-finite reward)")
    A = {k: np.asarray(v, dtype=float) for k, v in rec.items()}
    turb, oil, knock = damage_split(A["t_turb"], A["t_oil"], A["ki"], cal=dm, dt=dt)
    b_turb, b_oil, _ = damage_split(A["tb_turb"], A["tb_oil"], np.zeros(len(A["t"])), cal=dm, dt=dt)
    s = info["episode_summary"]
    out = dict(steps=int(len(A["t"])), seconds=seconds, ret=float(ret),
               D_noknock=float((turb + oil).sum()), D_knock=float(s["damage"]),
               base_noknock=float((b_turb + b_oil).sum()), base_knock=float(s["damage_base"]),
               turb=float(turb.sum()), oil=float(oil.sum()), knockterm=float(knock.sum()),
               base_turb=float(b_turb.sum()), base_oil=float(b_oil.sum()),
               fuel=float(s["fuel"]), fuel_base=float(s["fuel_base"]),
               torque_viol=float(s["torque_viol"]), knock_events=int(s["knock_events"]),
               peak_turb_k=float(A["t_turb"].max()), base_peak_turb_k=float(A["tb_turb"].max()),
               obs_min=o_min.tolist(), obs_max=o_max.tolist(), obs_clip_steps=o_clip.tolist(),
               d_noknock=(turb + oil), egt_k=A["egt_k"])
    if detail in ("cg", "full"):
        I = np.asarray(inputs, dtype=float)
        out.update(t=A["t"], t_turb=A["t_turb"], t_oil=A["t_oil"], tb_turb=A["tb_turb"], tb_oil=A["tb_oil"],
                   torque=A["torque"], torque_req=A["torque_req"], inputs=I)
    if detail == "full":
        out.update(ki=A["ki"], fuel_steps=A["fuel"], lam_trim=A["lam_trim"], mdot_exh=A["mdot_exh"],
                   egt_k=A["egt_k"], d_turb=turb, d_oil=oil, d_knock=knock, ret_steps=A["ret"])
    return out


def replay_turb(plant, inputs, *, egt):
    """The housing replayed open loop on the plant's own ThermalNetwork from a run's recorded network
    inputs (`inputs`, run_episode_record's), with the gas temperature of each step replaced by egt[k]
    (an array; the recorded gas where it is the recorded value). The other nodes follow the recorded
    inputs, which the housing does not read. Returns the housing temperature after each step."""
    th = ThermalNetwork(plant.engine.thermal)
    th.reset(t_amb=float(inputs[0, 4]), warm=True)
    T = np.empty(len(inputs))
    for k in range(len(inputs)):
        d, mf, mex, _e, ta, vm, fan, pump, rpm = inputs[k]
        th.step(float(d), float(mf), float(mex), float(egt[k]), float(ta), float(vm), float(fan), float(pump),
                rpm=float(rpm))
        T[k] = th.t_turb
    return T


def replay_inputs(inputs, *, egt, mex):
    """A copy of recorded network inputs with the gas temperature and the exhaust flow replaced."""
    I = np.array(inputs, dtype=float, copy=True)
    I[:, 3] = egt
    I[:, 2] = mex
    return I


# ------------------------------------------------------------------ the pool and its cache
_CACHE = {}


def _spec_key(spec):
    s = dict(spec)
    if "road" in s:
        s["road"] = road_sha(s["road"])
    return hashlib.sha256(json.dumps(s, sort_keys=True, default=_json_default).encode("utf-8")).hexdigest()


def _cycle_of(spec, plant):
    c = spec["cycle"]
    if c == "road":
        return env_cycle(spec["road"], dt=spec["dt"])
    if c == "locked":
        return E.locked_climb(plant, duration=LOCKED_DURATION_S, dt=spec["dt"])
    if c == "grade_climb":
        return E.make_grade_climb(duration=spec["duration"], dt=spec["dt"], t_amb=spec["t_amb"],
                                  grade=spec["grade"], v_kmh=spec["v_kmh"])
    raise ValueError(f"roads_ceiling: unknown cycle {c!r}")


def _task(spec):
    """One run, in a worker or in-process: ("run", spec) or ("tau", engine_id, variant)."""
    if spec["kind"] == "tau":
        p = plant_for(spec["engine_id"], tuple(spec["variant"]))
        t0 = time.perf_counter()
        tau, cell = tau_of_plant(p)
        return dict(tau_s=tau, cell=cell, seconds=time.perf_counter() - t0)
    p = plant_for(spec["engine_id"], tuple(spec["variant"]))
    cyc = _cycle_of(spec, p)
    return run_episode_record(p, cyc, make_policy(tuple(spec["policy"])), seed=spec["seed"],
                              weights=tuple(spec["weights"]), dt=spec["dt"],
                              egt_ambient_windows=tuple(tuple(w) for w in spec.get("egt_windows", ())),
                              detail=spec["detail"])


def _cost(spec):
    if spec["kind"] == "tau":
        return LOCKED_DURATION_S
    if spec["cycle"] == "road":
        return len(spec["road"]["cycle"]["t"]) * float(spec["road"]["dt"]) / spec["dt"]
    return spec.get("duration", LOCKED_DURATION_S) / spec["dt"]


def execute(specs, *, jobs):
    """Run every spec not already cached (at most `jobs` processes), longest first; return the results
    in the specs' order. The cache lives for the process, so a redraw's test re-runs only its road."""
    keys = [_spec_key(s) for s in specs]
    todo, seen = [], set()
    for k, s in zip(keys, specs):
        if k not in _CACHE and k not in seen:
            todo.append((k, s))
            seen.add(k)
    todo.sort(key=lambda ks: -_cost(ks[1]))
    if todo:
        t0 = time.perf_counter()
        if jobs <= 1 or len(todo) == 1:
            install_guard()
            for i, (k, s) in enumerate(todo, 1):
                _CACHE[k] = _task(s)
                _progress(i, len(todo), t0)
        else:
            import multiprocessing as mp
            ctx = mp.get_context("spawn")
            with ctx.Pool(min(int(jobs), len(todo)), initializer=_worker_init) as pool:
                for i, (k, res, opened) in enumerate(pool.imap_unordered(_keyed_task, todo), 1):
                    _CACHE[k] = res
                    OPENED.update(opened)
                    _progress(i, len(todo), t0)
    return [_CACHE[k] for k in keys]


def _keyed_task(ks):
    res = _task(ks[1])
    return ks[0], res, sorted(OPENED)


def _progress(i, n, t0):
    if i == n or i % 10 == 0:
        print(f"[roads_ceiling] {i}/{n} runs, {time.perf_counter() - t0:.0f} s", file=sys.stderr, flush=True)


def _run_spec(*, engine_id, variant, road, dt, policy, detail):
    return dict(kind="run", engine_id=engine_id, variant=list(variant), cycle="road", road=road, dt=float(dt),
                seed=int(road["episode_seed"]), weights=[float(w) for w in road["weights"]],
                policy=_json_policy(policy), detail=detail)


def _json_policy(policy):
    if policy[0] == "lam":
        return ["lam", [[float(a), float(b)] for a, b in policy[1]]]
    return list(policy)


def tau_pairs(pairs, *, jobs):
    """Row 102's tau for several (engine_id, variant) pairs, in one pool batch, memoised."""
    need = [(e, tuple(v)) for e, v in pairs if (e, tuple(v)) not in _TAUS]
    if need:
        res = execute([dict(kind="tau", engine_id=e, variant=list(v)) for e, v in need], jobs=jobs)
        for key, r in zip(need, res):
            _TAUS[key] = (r["tau_s"], r["cell"])
    return {(e, tuple(v)): _TAUS[(e, tuple(v))] for e, v in pairs}


def tau_table(engine_ids, *, variant, jobs):
    """{engine_id: (tau_s, cell)} by row 102's definition, run in the pool and memoised."""
    got = tau_pairs([(e, variant) for e in engine_ids], jobs=jobs)
    return {e: got[(e, tuple(variant))] for e in engine_ids}


def use_recorded_taus(taus):
    """Row 102: each engine's tau is computed once, at the draw, and written into the roads record; the
    re-check and the redraws read it from there and never recompute it. `taus` is {engine_id: (tau_s,
    cell)} as the record holds them; every later ceilings() call in this process reads these. Refused
    (ValueError) if this process already holds a different value for an engine."""
    for e, (tau, cell) in taus.items():
        key = (e, ("frozen",))
        if key in _TAUS and _TAUS[key][0] != float(tau):
            raise ValueError(f"roads_ceiling: {e}'s tau {_TAUS[key][0]!r} in this process is not the recorded "
                             f"{float(tau)!r}")
        _TAUS[key] = (float(tau), cell)


# ------------------------------------------------------------------ a road set's runs
def _rkey(r):
    return f"{r:g}"


def _policy_specs(road, *, horizons, policies):
    """{name: policy spec} for one road: cg, a@<label> per horizon, b, a_b, neutral, reactive."""
    out = {"cg": ("cg",)}
    if "a" in policies:
        for label, H in horizons.items():
            out[f"a@{label}"] = ("lam", windows_a(road, H=H))
    if "b" in policies:
        out["b"] = ("lam", windows_b(road))
    if "a_b" in policies:
        out["a_b"] = ("lam", windows_ab(road))
    if "neutral" in policies:
        out["neutral"] = ("neutral",)
    if "reactive" in policies:
        out["reactive"] = ("reactive",)
    return out


def set_specs(roads, *, engine_ids, variant, horizons, dt, policies):
    """The run specs of a set and their names (i, engine, name): see run_set."""
    specs, names = [], []
    for i, road in enumerate(roads):
        for e in engine_ids:
            for name, pol in _policy_specs(road, horizons=horizons[e], policies=policies).items():
                specs.append(_run_spec(engine_id=e, variant=variant, road=road, dt=dt, policy=pol,
                                       detail="cg" if name == "cg" else "light"))
                names.append((i, e, name))
    return specs, names


def run_set(roads, *, engine_ids, variant, horizons, dt, jobs, policies):
    """Every (road, engine, policy) run of a set: {(i, engine, name): result}. horizons is
    {engine: {label: H_s}}; policies a subset of ("a", "b", "a_b", "neutral", "reactive"), cg always."""
    specs, names = set_specs(roads, engine_ids=engine_ids, variant=variant, horizons=horizons, dt=dt,
                             policies=policies)
    return dict(zip(names, execute(specs, jobs=jobs)))


# ------------------------------------------------------------------ aggregation
def _reading(res, reading):
    return res["D_noknock"] if reading == "noknock" else res["D_knock"]


def _base(res, reading):
    return res["base_noknock"] if reading == "noknock" else res["base_knock"]


def aggregate(refs, vars_, bases, *, neutral):
    """The four forms of one saving over a road set, from per-road damages of the reference policy
    (refs), the variant (vars_) and the baseline network (bases), all in one reading: the mean of the
    road points 100 (ref - var) / base (row 103's C), the pooled form 100 sum(ref - var) / sum(base),
    the median of the road points, and evaluate.py's form 100 (median ref - median var) / median neutral
    (None without the neutral runs). Per-road points beside them."""
    refs, vars_, bases = (np.asarray(x, dtype=float) for x in (refs, vars_, bases))
    pts = 100.0 * (refs - vars_) / bases
    ev = None
    if neutral is not None:
        ev = float(100.0 * (np.median(refs) - np.median(vars_)) / np.median(np.asarray(neutral, dtype=float)))
    return dict(mean=float(pts.mean()), pooled=float(100.0 * (refs - vars_).sum() / bases.sum()),
                median=float(np.median(pts)), evaluate_form=ev, per_road=[float(x) for x in pts])


def _section_g_drop_k():
    """Section G's assumed exhaust drop at the lambda bound, as results/preview_ceiling.py computes it
    (its section F's measured hand-written drop on 150-179 s, scaled linearly to -0.15 / -0.055): read
    from the traces it reads, with its own infer_ua (imported, not edited)."""
    import preview_ceiling as PC
    with open(PC.TRACES, encoding="utf-8") as fh:
        d = json.load(fh)
    _ua, _T, e_cg = PC.infer_ua(d["current-grade"])
    _ua, _T, e_pr = PC.infer_ua(d["predictive (hand)"])
    return float(np.median(e_cg[150:180] - e_pr[150:180])) * 0.15 / 0.055


def _step_times(road, *, dt, steps):
    return env_cycle(road, dt=dt)["t"][:steps]


def _mask(t, wins):
    m = np.zeros(len(t), dtype=bool)
    for a, b in wins:
        m |= (t >= a) & (t < b)
    return m


def summarise_set(roads, runs, *, engine_ids, variant, horizons, dt, readings, variants, egt_drop_k):
    """Per engine: per-road damages and points, and per horizon label every form of every saving in
    every reading, with the companions row 103 (1) lists that the runs allow."""
    out = {}
    n = len(roads)
    for e in engine_ids:
        plant = plant_for(e, variant)
        cal = plant.engine.damage
        per_road = []
        for i, road in enumerate(roads):
            cg = runs[(i, e, "cg")]
            row = dict(k=int(road["k"]), episode_seed=int(road["episode_seed"]), weights=list(road["weights"]),
                       pairing=_pairing(road), road_sha=road_sha(road)[:16],
                       D_base={r: _base(cg, r) for r in READINGS},
                       D={}, fuel={}, ret={}, steps=cg["steps"])
            names = [nm for (ii, ee, nm) in runs if ii == i and ee == e]
            for nm in sorted(names):
                res = runs[(i, e, nm)]
                row["D"][nm] = {r: _reading(res, r) for r in READINGS}
                row["fuel"][nm] = res["fuel"]
                row["ret"][nm] = res["ret"]
            row["cg_cut"] = {r: 100.0 * (1.0 - row["D"]["cg"][r] / row["D_base"][r]) for r in READINGS}
            t = _step_times(road, dt=dt, steps=cg["steps"])
            hs = {}
            for nm in names:
                if nm == "cg" or nm in ("neutral", "reactive"):
                    continue
                wins = (windows_b(road) if nm == "b" else windows_ab(road) if nm == "a_b"
                        else windows_a(road, H=horizons[e][nm[2:]]))
                d = cg["d_noknock"] - runs[(i, e, nm)]["d_noknock"]
                m = _mask(t, wins)
                # row 101: the exhaust drop at the lambda bound, named beside any difference between
                # engines: the median over the variant's window steps of current-grade's exhaust minus
                # the variant's, the gas each run's housing was given
                drop = cg["egt_k"] - runs[(i, e, nm)]["egt_k"]
                hs[nm] = dict(inside=float(100.0 * d[m].sum() / cg["base_noknock"]),
                              outside=float(100.0 * d[~m].sum() / cg["base_noknock"]),
                              egt_drop_k=float(np.median(drop[m])) if m.any() else None)
            row["head_start"] = hs
            if "c" in variants or "G" in variants:
                I = cg["inputs"]
                T_self = replay_turb(plant, I, egt=I[:, 3])
                row["replay_self_max_abs_k"] = float(np.max(np.abs(T_self - cg["t_turb"])))
                O = cg["t_oil"]
                zero = np.zeros(len(O))
                t_ref, o_ref, _ = damage_split(T_self, O, zero, cal=cal, dt=dt)
                d_ref = float((t_ref + o_ref).sum())
                row["c"], row["G"] = {}, {}
                for label, H in horizons[e].items():
                    m = _mask(t, windows_a(road, H=H))
                    if "c" in variants:
                        Tc = replay_turb(plant, I, egt=np.where(m, I[:, 4], I[:, 3]))
                        tc, oc, _ = damage_split(Tc, O, zero, cal=cal, dt=dt)
                        row["c"][label] = float(100.0 * (d_ref - float((tc + oc).sum())) / cg["base_noknock"])
                    if "G" in variants:
                        Tg = replay_turb(plant, I, egt=np.where(m, I[:, 3] - egt_drop_k, I[:, 3]))
                        tg, og, _ = damage_split(Tg, O, zero, cal=cal, dt=dt)
                        row["G"][label] = float(100.0 * (d_ref - float((tg + og).sum())) / cg["base_noknock"])
            per_road.append(row)
        by = {}
        neutral = {r: ([pr["D"]["neutral"][r] for pr in per_road] if "neutral" in per_road[0]["D"] else None)
                   for r in READINGS}
        for label, H in horizons[e].items():
            blk = dict(H_s=float(H))
            for nm, key in (("a", f"a@{label}"), ("b", "b"), ("a_b", "a_b")):
                if key not in per_road[0]["D"]:
                    continue
                blk[nm] = {}
                for r in readings:
                    agg = aggregate([pr["D"]["cg"][r] for pr in per_road], [pr["D"][key][r] for pr in per_road],
                                    [pr["D_base"][r] for pr in per_road], neutral=neutral[r])
                    if r == "knock":
                        agg["label"] = KNOCK_LABEL
                    if nm != "a":
                        agg["companion"] = COMPANION_LABEL
                    blk[nm][r] = agg
            if "a" in blk and "noknock" in blk["a"]:
                C = blk["a"]["noknock"]["mean"]
                blk["C"] = C
                blk["two_mei"] = dict(test="version 5's (decision 34's): C >= 2 MEI", two_mei=TWO_MEI,
                                      C=C, reaches=bool(C >= TWO_MEI), reading="noknock")
                blk["below_T"] = bool(C < T_POINTS)
            if "a_b" in per_road[0]["D"] and f"a@{label}" in per_road[0]["D"]:
                blk["C_blind"], blk["C_u"] = {}, {}
                for r in readings:
                    blk["C_blind"][r] = aggregate([pr["D"]["cg"][r] for pr in per_road],
                                                  [pr["D"]["a_b"][r] for pr in per_road],
                                                  [pr["D_base"][r] for pr in per_road], neutral=neutral[r])
                    blk["C_u"][r] = aggregate([pr["D"]["a_b"][r] for pr in per_road],
                                              [pr["D"][f"a@{label}"][r] for pr in per_road],
                                              [pr["D_base"][r] for pr in per_road], neutral=neutral[r])
            for nm in ("c", "G"):
                if nm in per_road[0] and label in per_road[0][nm]:
                    vals = [pr[nm][label] for pr in per_road]
                    blk[nm] = dict(mean=float(np.mean(vals)), median=float(np.median(vals)), per_road=vals,
                                   reading="noknock (turbine and oil; the replay moves the housing only)",
                                   companion=COMPANION_LABEL)
            if "G" in blk:
                blk["G"]["egt_drop_k"] = egt_drop_k
            hsb = {}
            for nm, key in (("a", f"a@{label}"), ("b", "b"), ("a_b", "a_b")):
                if key in per_road[0]["head_start"]:
                    ins = [pr["head_start"][key]["inside"] for pr in per_road]
                    outs = [pr["head_start"][key]["outside"] for pr in per_road]
                    drops = [pr["head_start"][key]["egt_drop_k"] for pr in per_road
                             if pr["head_start"][key]["egt_drop_k"] is not None]
                    hsb[nm] = dict(inside_mean=float(np.mean(ins)), outside_mean=float(np.mean(outs)),
                                   reading="noknock",
                                   egt_drop_k_median=float(np.median(drops)) if drops else None,
                                   egt_drop_what="the exhaust drop at the lambda bound: median over the roads "
                                                 "of each road's median, over the variant's window steps, of "
                                                 "current-grade's exhaust minus the variant's (row 101)")
            blk["head_start"] = hsb
            fx = {}
            for nm, key in (("a", f"a@{label}"), ("b", "b"), ("a_b", "a_b")):
                if key in per_road[0]["fuel"]:
                    v = [100.0 * (pr["fuel"][key] / pr["fuel"]["cg"] - 1.0) for pr in per_road]
                    fx[nm] = dict(mean=float(np.mean(v)), per_road=v)
            blk["fuel_extra_pct"] = fx
            sighted = [nm for nm in ("cg", f"a@{label}", "a_b", "b") if nm in per_road[0]["ret"]]
            best = [max(sighted, key=lambda nm: pr["ret"][nm]) for pr in per_road]
            blk["best_sighted"] = dict(set=sighted, per_road=best,
                                       counts={nm: best.count(nm) for nm in sighted})
            by[label] = blk
        blind = [nm for nm in ("cg", "a_b", "b") if nm in per_road[0]["ret"]]
        bb = [max(blind, key=lambda nm: pr["ret"][nm]) for pr in per_road]
        out[e] = dict(knee_k=float(cal.turb_knee_k), by=by, per_road=per_road,
                      best_blind=dict(set=blind, per_road=bb, counts={nm: bb.count(nm) for nm in blind}),
                      n_roads=n)
    return out


def _pairing(road):
    k = int(road["k"])
    if 0 <= k < len(V.EPISODES):
        s, w = V.EPISODES[k]
        return bool(int(road["episode_seed"]) == s and [float(x) for x in road["weights"]] == list(w))
    return False


# ------------------------------------------------------------------ the interface
def _check_engines(engine_ids):
    bad = [e for e in engine_ids if e not in ENGINES]
    if bad or not engine_ids:
        raise ValueError(f"roads_ceiling: engines {list(engine_ids)!r} are not a subset of {ENGINES}")
    return tuple(engine_ids)


def _check_variants(variants):
    v = tuple(variants)
    bad = [x for x in v if x not in ALL_VARIANTS]
    if bad or "cg" not in v or "a" not in v:
        raise ValueError(f"roads_ceiling: variants {v!r} must hold cg and a, from {ALL_VARIANTS}")
    return v


def ceilings(roads, *, engines, ratios, dt, jobs, variants, readings):
    """Row 103 (1)'s ceiling C_e(S, r) on the road set, per engine and ratio, in the no-knock reading
    (primary) and the with-knock one ("not converged in dt on these roads"), with the pooled form, the
    median, evaluate.py's form (when "neutral" is among the variants) and the per-road points beside it,
    and every companion the variants ask for: variants is a subset of ALL_VARIANTS holding "cg" and "a"."""
    engine_ids = _check_engines(engines)
    variants = _check_variants(variants)
    readings = tuple(readings)
    if not set(readings) <= set(READINGS) or "noknock" not in readings:
        raise ValueError(f"roads_ceiling: readings {readings!r} must hold noknock, from {READINGS}")
    for road in roads:
        check_road(road)
    taus = tau_table(engine_ids, variant=("frozen",), jobs=jobs)
    horizons = {e: {_rkey(r): float(r) * taus[e][0] for r in ratios} for e in engine_ids}
    policies = tuple(x for x in variants if x in ("a", "b", "a_b", "neutral"))
    runs = run_set(roads, engine_ids=engine_ids, variant=("frozen",), horizons=horizons, dt=dt, jobs=jobs,
                   policies=policies)
    egt_drop = _section_g_drop_k() if "G" in variants else None
    per = summarise_set(roads, runs, engine_ids=engine_ids, variant=("frozen",), horizons=horizons, dt=dt,
                        readings=readings, variants=variants, egt_drop_k=egt_drop)
    for e in engine_ids:
        per[e]["tau_s"] = taus[e][0]
        per[e]["ratios"] = {_rkey(r): float(r) for r in ratios}
    return dict(what="row 103 (1): C_e(S, r) = mean over the roads of 100 (D_cg - D_a) / D_base, no-knock "
                     "reading primary", T_points=T_POINTS, two_mei=TWO_MEI, mei=MEI, dt=float(dt),
                ratios=[float(r) for r in ratios], engines=list(engine_ids), variants=list(variants),
                readings=list(readings), n_roads=len(roads),
                roads=[dict(k=int(r["k"]), road_sha=road_sha(r), label=r.get("label")) for r in roads],
                synthetic=any(SYNTHETIC in str(r.get("label", "")) for r in roads),
                per_engine=per)


def ceiling_at(result, engine_id, r):
    """C_e(S, r), the no-knock mean of the road points, from a ceilings() result."""
    return float(result["per_engine"][engine_id]["by"][_rkey(r)]["a"]["noknock"]["mean"])


def passes_T(ceiling_result, *, engines):
    """Row 103 (2): C_e(S, 1.5) >= T = MEI / 4 on every engine in the test (the no-knock reading).
    Returns (passes, {engine: C at r = 1.5})."""
    c = {e: ceiling_at(ceiling_result, e, 1.5) for e in _check_engines(engines)}
    return all(v >= T_POINTS for v in c.values()), c


def slot_candidate_ceilings(roads, slot, candidate_road, *, engines, dt, jobs):
    """Row 103 (2) at a redraw: the set with the candidate road in the place of the road that holds the
    slot, its C_e(S, 1.5) on every engine given, and whether it passes T. Only the candidate's road is
    run when the set's other roads are in this process's cache (a ceilings() call on the set first)."""
    idx = [i for i, r in enumerate(roads) if any(int(c["slot"]) == int(slot) for c in r["climbs"])]
    if len(idx) != 1:
        raise ValueError(f"roads_ceiling: slot {slot!r} is on {len(idx)} roads, not one")
    if not any(int(c["slot"]) == int(slot) for c in candidate_road["climbs"]):
        raise ValueError(f"roads_ceiling: the candidate road holds no slot {slot!r}")
    new = list(roads)
    new[idx[0]] = candidate_road
    res = ceilings(new, engines=engines, ratios=(1.5,), dt=dt, jobs=jobs, variants=("cg", "a"),
                   readings=("noknock",))
    ok, c = passes_T(res, engines=engines)
    per_road = {e: res["per_engine"][e]["by"]["1.5"]["a"]["noknock"]["per_road"][idx[0]] for e in res["engines"]}
    return dict(slot=int(slot), road_index=idx[0], passes_T=ok, C=c, T_points=T_POINTS,
                candidate_road_points=per_road, result=res)


# ------------------------------------------------------------------ report()
def _usable(roads, taus, ratios):
    """Row 101: L / tau per slot, and the usable window min(H, G) / tau, G the time from the previous
    climb's full-grade end to the onset, with P(G < H), under two conventions, each named: "gaps_only"
    leaves each road's first climb out, as row 101's figures did (the scientific review's power.py:
    "first climb unclipped ignored"), and "every_window" counts it with G its onset minus 20 s, the
    start (a)'s window may take on the lead-in."""
    out = {}
    for e, tau in taus.items():
        Ls, Gs, first = [], [], []
        for road in roads:
            prev_end = FIRST_WINDOW_FROM_S
            for j, (s, L, _g, _c) in enumerate(climbs_of(road)):
                Ls.append(L)
                Gs.append(s - prev_end)
                first.append(j == 0)
                prev_end = s + L
        Ls, Gs, first = np.asarray(Ls), np.asarray(Gs), np.asarray(first, dtype=bool)
        blk = dict(tau_s=tau, n_slots=int(len(Ls)),
                   L_over_tau=dict(min=float((Ls / tau).min()), max=float((Ls / tau).max()),
                                   mean=float((Ls / tau).mean())) if len(Ls) else None, by_r={},
                   conventions=dict(gaps_only="each road's first climb left out (row 101's figures)",
                                    every_window="the first climb counted, G = its onset - 20 s"))
        for r in ratios:
            H = r * tau
            row = dict(H_s=H)
            for name, sel in (("gaps_only", ~first), ("every_window", np.ones(len(Gs), dtype=bool))):
                g = Gs[sel]
                u = np.minimum(H, g) / tau
                row[name] = dict(n=int(len(g)), usable_over_tau_mean=float(u.mean()) if len(u) else None,
                                 P_G_below_H=float((g < H).mean()) if len(g) else None)
            blk["by_r"][_rkey(r)] = row
        out[e] = blk
    return out


def _knee_shares(roads, runs, engine_ids):
    """Each slot's baseline peak (housing and oil, over the slot's first step to the next slot's) against
    the engine's knees, and the share of slots whose baseline passes each."""
    out = {}
    for e in engine_ids:
        cal = plant_for(e, ("frozen",)).engine.damage
        slots = []
        for i, road in enumerate(roads):
            cg = runs[(i, e, "cg")]
            cl = climbs_of(road)
            for j, (s, L, g, c) in enumerate(cl):
                a = int(c["first_step"])
                b = int(cl[j + 1][3]["first_step"]) if j + 1 < len(cl) else cg["steps"]
                tb, ob = cg["tb_turb"][a:b], cg["tb_oil"][a:b]
                slots.append(dict(slot=int(c["slot"]), road=int(road["k"]),
                                  turb_peak_minus_knee_k=float(tb.max() - cal.turb_knee_k),
                                  oil_peak_minus_knee_k=float(ob.max() - cal.oil_knee_k)))
        nt = sum(1 for s in slots if s["turb_peak_minus_knee_k"] > 0)
        no = sum(1 for s in slots if s["oil_peak_minus_knee_k"] > 0)
        out[e] = dict(turb_knee_k=cal.turb_knee_k, oil_knee_k=cal.oil_knee_k, slots=slots,
                      share_turb=nt / len(slots) if slots else None, share_oil=no / len(slots) if slots else None)
    return out


def _decision13(roads, runs, engine_ids, dt):
    """Decision 13's yardstick (VD:86; row 100 (3)): current-grade's steps under 95 % of the requested
    torque, and its steps over the tracking tolerance, over every step after the 20 s speed ramp and over
    the climbs' full grade, per engine; the largest shortfall."""
    out = {}
    for e in engine_ids:
        tot = dict(steps=0, under95=0, over_tol=0, climb_steps=0, climb_under95=0, climb_over_tol=0,
                   largest_shortfall_nm=0.0, climb_largest_shortfall_nm=0.0)
        per = []
        for i, road in enumerate(roads):
            cg = runs[(i, e, "cg")]
            t = cg["t"]
            req, tq = cg["torque_req"], cg["torque"]
            e_track = np.abs(req - tq) / np.maximum(req, 40.0)
            after = t >= SPEED_RAMP_S
            climb = np.zeros(len(t), dtype=bool)
            for s, L, _g, _c in climbs_of(road):
                climb |= (t >= s + RAMP_S) & (t < s + L)
            u95 = tq < TORQUE_SHORT * req
            row = dict(k=int(road["k"]), under95=int((u95 & after).sum()), over_tol=int((e_track[after] > E.TRACK_TOL).sum()),
                       climb_under95=int((u95 & climb).sum()), climb_over_tol=int((e_track[climb] > E.TRACK_TOL).sum()),
                       climb_steps=int(climb.sum()))
            per.append(row)
            tot["steps"] += int(after.sum())
            tot["under95"] += row["under95"]
            tot["over_tol"] += row["over_tol"]
            tot["climb_steps"] += row["climb_steps"]
            tot["climb_under95"] += row["climb_under95"]
            tot["climb_over_tol"] += row["climb_over_tol"]
            short = req - tq
            tot["largest_shortfall_nm"] = max(tot["largest_shortfall_nm"], float(short[after].max()))
            if climb.any():
                tot["climb_largest_shortfall_nm"] = max(tot["climb_largest_shortfall_nm"], float(short[climb].max()))
        out[e] = dict(total=tot, per_road=per, rule="torque < 0.95 x torque_req, after the 20 s speed ramp; "
                                                     "e_track > engine_env.TRACK_TOL beside it")
    return out


def _obs_ranges(runs, engine_ids):
    """Row 99: the range of every observation on the test roads per engine (over every run of the
    set), and the steps at the +-10 clip (engine_env's observation clip)."""
    out = {}
    for e in engine_ids:
        rs = [v for (i, ee, nm), v in runs.items() if ee == e]
        lo = np.min([r["obs_min"] for r in rs], axis=0)
        hi = np.max([r["obs_max"] for r in rs], axis=0)
        cl = np.sum([r["obs_clip_steps"] for r in rs], axis=0)
        out[e] = dict(runs=len(rs), ranges={n: [float(a), float(b)] for n, a, b in zip(OBS_NAMES, lo, hi)},
                      clip_steps={n: int(c) for n, c in zip(OBS_NAMES, cl) if c},
                      any_clip=bool(cl.sum() > 0))
    return out


def _spread_stat(curves, axis_labels, norm_label):
    """Row 102's spread statistic: each curve normalised by its value at the largest abscissa; at each
    abscissa the largest normalised value minus the smallest; their mean."""
    norm = {k: {a: v[a] / v[norm_label] if v[norm_label] else float("nan") for a in axis_labels}
            for k, v in curves.items()}
    sp = {a: float(max(n[a] for n in norm.values()) - min(n[a] for n in norm.values())) for a in axis_labels}
    return dict(normalised=norm, spread=sp, mean_spread=float(np.mean(list(sp.values()))))


def _grid_sets(engine_ids):
    sets = [(e, ("frozen",)) for e in engine_ids]
    if "ford_27tt" in engine_ids:
        sets.append(("ford_27tt", ("one_housing",)))
    return sets


def _grid_horizons(tau):
    hz = {f"r{_rkey(r)}": float(r) * tau for r in GRID_RATIOS}
    hz.update({f"H{_rkey(h)}": float(h) for h in GRID_H_S})
    return hz


def _report_plan(roads, *, engine_ids, dt, taus):
    """Every set report() runs, as set_specs' arguments, so that one pool batch runs them all (the
    sections then read the cache): the main set, row 102's grids, E6 rows 4 and 11, the dt repeat."""
    plan = [(list(engine_ids), ("frozen",), {e: {_rkey(r): float(r) * taus[(e, ("frozen",))][0] for r in RATIOS}
                                             for e in engine_ids}, dt, ("a", "b", "a_b", "neutral"))]
    for e, var in _grid_sets(engine_ids):
        plan.append(([e], var, {e: _grid_horizons(taus[(e, var)][0])}, dt, ("a",)))
    for e in [x for x in engine_ids if x in EPA_ENGINES]:
        hz = {e: {"1.5": 1.5 * taus[(e, ("frozen",))][0]}}
        for f in ROW4_FIELDS:
            for fac in ROW4_FACTORS:
                plan.append(([e], ("thermal", f, fac), hz, dt, ("a",)))
        for off in (0.0, CHARGE_OFFSET_K, -CHARGE_OFFSET_K):
            plan.append(([e], ("frozen",) if off == 0.0 else ("charge", off), hz, dt, ("a", "neutral", "reactive")))
    try:
        for road in roads:
            env_cycle(road, dt=DT_REPEAT)
        plan.append((list(engine_ids), ("frozen",), {e: {"1.5": 1.5 * taus[(e, ("frozen",))][0]} for e in engine_ids},
                     DT_REPEAT, ("a",)))
    except ValueError:
        pass                                 # _dt_repeat reports it as not computed
    return plan


def _grids(roads, *, engine_ids, dt, jobs):
    """Row 102's two grids, computed once on the roads as first drawn: each engine's C (no knock, mean
    of road points) at r = GRID_RATIOS on the H/tau axis and at H = GRID_H_S, with the Ford on its
    one-housing plant beside it (epa_fit.perturbed(n_turbines=1)), and the spread statistic on both axes,
    with and without the one-housing Ford."""
    sets = _grid_sets(engine_ids)
    curves_r, curves_h, detail = {}, {}, {}
    for e, var in sets:
        tau = tau_table([e], variant=var, jobs=jobs)[e][0]
        hz = _grid_horizons(tau)
        runs = run_set(roads, engine_ids=[e], variant=var, horizons={e: hz}, dt=dt, jobs=jobs, policies=("a",))
        per = summarise_set(roads, runs, engine_ids=[e], variant=var, horizons={e: hz}, dt=dt,
                            readings=READINGS, variants=("cg", "a"), egt_drop_k=None)[e]
        name = e if var == ("frozen",) else f"{e} (one housing)"
        curves_r[name] = {_rkey(r): per["by"][f"r{_rkey(r)}"]["a"]["noknock"]["mean"] for r in GRID_RATIOS}
        curves_h[name] = {_rkey(h): per["by"][f"H{_rkey(h)}"]["a"]["noknock"]["mean"] for h in GRID_H_S}
        detail[name] = dict(tau_s=tau, plant_variant=list(var),
                            knock={lab: per["by"][lab]["a"]["knock"]["mean"] for lab in hz},
                            H_s={lab: h for lab, h in hz.items()})
    ar, ah = [_rkey(r) for r in GRID_RATIOS], [_rkey(h) for h in GRID_H_S]
    groups = {"four_engines": [e for e in engine_ids],
              "with_one_housing_ford": [e for e in engine_ids] + (["ford_27tt (one housing)"]
                                                                  if "ford_27tt" in engine_ids else []),
              "without_ford": [e for e in engine_ids if e != "ford_27tt"]}
    spreads = {}
    for g, members in groups.items():
        if len(members) < 2:
            continue
        spreads[g] = dict(members=members,
                          H_over_tau_axis=_spread_stat({m: curves_r[m] for m in members}, ar, ar[-1]),
                          H_axis=_spread_stat({m: curves_h[m] for m in members}, ah, ah[-1]))
    return dict(what="row 102: C_e (no knock, mean of road points) on the H/tau axis and the H axis; descriptive",
                H_over_tau=curves_r, H_s=curves_h, detail=detail, spreads=spreads)


def _e6_row4(roads, *, engine_ids, dt, jobs, frozen_taus):
    """E6 row 4 (row 100 (1); MD:982): the ceiling at r = 1.5, at the frozen H, with c_turb, ua_gas_turb
    and ua_turb_amb each at x0.75 and x1.333 (epa_fit.perturbed, as calibrate_epa.py:2645-2652), flagged
    below 2 MEI and below T; tau at the frozen climb cell beside it, and complete.json's."""
    out = {}
    for e in [x for x in engine_ids if x in EPA_ENGINES]:
        tau0, cell = frozen_taus[e]
        rec = frozen_tau_record(e)
        out[e] = dict(frozen_tau_s=tau0, H_s=1.5 * tau0, complete_json_frozen_tau_s=(rec or {}).get("frozen", {}).get("tau_s"),
                      cases={})
        for f in ROW4_FIELDS:
            for fac in ROW4_FACTORS:
                var = ("thermal", f, fac)
                import epa_coefficients as EC
                pp = plant_for(e, var)
                tau_cell = float(EC.housing(pp, cell["egt"], cell["mdot"], t_amb_c=EC.T_AMB_C)["tau_s"])
                hz = {"1.5": 1.5 * tau0}
                runs = run_set(roads, engine_ids=[e], variant=var, horizons={e: hz}, dt=dt, jobs=jobs, policies=("a",))
                per = summarise_set(roads, runs, engine_ids=[e], variant=var, horizons={e: hz}, dt=dt,
                                    readings=READINGS, variants=("cg", "a"), egt_drop_k=None)[e]
                C = per["by"]["1.5"]["a"]["noknock"]["mean"]
                key = f"x{fac:g}"
                out[e]["cases"][f"{f} {key}"] = dict(
                    tau_at_frozen_cell_s=tau_cell,
                    complete_json_tau_s=((rec or {}).get(f, {}).get(key, {}) or {}).get("tau_s"),
                    C=C, C_knock=per["by"]["1.5"]["a"]["knock"]["mean"], knock_label=KNOCK_LABEL,
                    below_two_mei=bool(C < TWO_MEI), below_T=bool(C < T_POINTS),
                    per_road=per["by"]["1.5"]["a"]["noknock"]["per_road"])
    return dict(what="E6 row 4 (MD:982): C at r = 1.5 (H fixed at 1.5 x the frozen tau), each constant at "
                     "each end; flagged below 2 MEI (MD:982) and below row 103's T", engines=out)


def _cuts(per, label):
    """The hand-written cuts of one set over the baseline network: per policy, mean of the road cuts
    100 (1 - D / D_base) and evaluate.py's form 100 (1 - median D / median D_neutral)."""
    out = {}
    pr = per["per_road"]
    for nm in sorted(pr[0]["D"]):
        blk = {}
        for r in READINGS:
            cuts = [100.0 * (1.0 - x["D"][nm][r] / x["D_base"][r]) for x in pr]
            ev = None
            if "neutral" in pr[0]["D"]:
                ev = float(100.0 * (1.0 - np.median([x["D"][nm][r] for x in pr])
                                    / np.median([x["D"]["neutral"][r] for x in pr])))
            blk[r] = dict(mean_cut=float(np.mean(cuts)), evaluate_form_cut=ev, per_road=cuts)
        out[nm] = blk
    out["C"] = per["by"][label]["a"]["noknock"]["mean"]
    return out


def _e6_row11(roads, *, engine_ids, dt, jobs, frozen_taus):
    """E6 row 11 (row 100 (2); MD:989): the test roads' hand-written cuts (neutral, reactive, current-
    grade, and (a) at r = 1.5) with the charge temperature moved by +-6.3 K through charge_shifted, and
    at 0 K beside them. Run 2 writes the row's hot TIT; this writes the roads' part."""
    out = {}
    for e in [x for x in engine_ids if x in EPA_ENGINES]:
        tau0 = frozen_taus[e][0]
        hz = {"1.5": 1.5 * tau0}
        blk = {}
        for off in (0.0, CHARGE_OFFSET_K, -CHARGE_OFFSET_K):
            var = ("frozen",) if off == 0.0 else ("charge", off)
            runs = run_set(roads, engine_ids=[e], variant=var, horizons={e: hz}, dt=dt, jobs=jobs,
                           policies=("a", "neutral", "reactive"))
            per = summarise_set(roads, runs, engine_ids=[e], variant=var, horizons={e: hz}, dt=dt,
                                readings=READINGS, variants=("cg", "a"), egt_drop_k=None)[e]
            blk[f"{off:+.1f} K"] = _cuts(per, "1.5")
        out[e] = blk
    return dict(what="E6 row 11 (MD:989): the hand-written cuts with the charge temperature offset by "
                     "+-6.3 K (charge_shifted: engines.ChargeCal.rise_k moved, outside PLANT_CODE)",
                computed=True, engines=out)


def _dt_repeat(roads, *, engine_ids, jobs, taus):
    """Row 101: current-grade and (a) at r = 1.5 at dt 0.5 s, both readings, beside dt 1 s."""
    try:
        for road in roads:
            env_cycle(road, dt=DT_REPEAT)
    except ValueError as exc:
        return dict(computed=False, why=str(exc))
    hz = {e: {"1.5": 1.5 * taus[e][0]} for e in engine_ids}
    out = {}
    for dtx in (DT, DT_REPEAT):
        runs = run_set(roads, engine_ids=engine_ids, variant=("frozen",), horizons=hz, dt=dtx, jobs=jobs,
                       policies=("a",))
        per = summarise_set(roads, runs, engine_ids=engine_ids, variant=("frozen",), horizons=hz, dt=dtx,
                            readings=READINGS, variants=("cg", "a"), egt_drop_k=None)
        for e in engine_ids:
            out.setdefault(e, {})[f"dt {dtx:g}"] = dict(
                noknock=per[e]["by"]["1.5"]["a"]["noknock"]["mean"],
                knock=per[e]["by"]["1.5"]["a"]["knock"]["mean"],
                base_noknock_mean=float(np.mean([p["D_base"]["noknock"] for p in per[e]["per_road"]])),
                base_knock_mean=float(np.mean([p["D_base"]["knock"] for p in per[e]["per_road"]])))
    for e in out:
        out[e]["moved"] = {r: out[e][f"dt {DT_REPEAT:g}"][r] - out[e][f"dt {DT:g}"][r] for r in READINGS}
    return dict(computed=True, what="row 101: cg and (a) at r = 1.5, dt 0.5 s against 1 s", knock_label=KNOCK_LABEL,
                engines=out)


def provenance(engine_ids):
    """What a record names: the commit, how many tracked files differ from it, the versions, and each
    plant's plant_sha and engine_sha."""
    import epa_freeze

    def git(*a):
        try:
            return subprocess.run(["git", *a], cwd=HERE, capture_output=True, text=True, timeout=30).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return None
    status = git("status", "--porcelain")
    return dict(git_head=git("rev-parse", "HEAD"),
                tree_changes=None if status is None else len([x for x in status.splitlines() if x.strip()]),
                versions=epa_freeze.versions(), cpu_count=os.cpu_count(),
                plants={e: dict(plant_sha=epa_freeze.plant_sha(e), engine_sha=engine_registry.engine_sha(
                    plant_for(e, ("frozen",)))) for e in engine_ids},
                module_sha256=MODULE_SHA256)


def report(roads, *, engines, dt, jobs):
    """Everything row 103 (1) lists beside the ceiling, and rows 99-102's reports, on the roads as first
    drawn: the ceilings with every companion at RATIOS; row 102's two grids with the one-housing Ford; E6
    rows 4 and 11 on the EPA engines; decision 13's count; the observation ranges and clip contacts; the
    Honda's (every engine's) current-grade cut against its baseline; the share of slots whose baseline
    passes each knee; L/tau and the usable window per engine and r; the dt 0.5 s repeat; and version 5's
    2-MEI test per engine."""
    engine_ids = _check_engines(engines)
    t0 = time.perf_counter()
    for road in roads:
        check_road(road)
    tp = tau_pairs([(e, ("frozen",)) for e in engine_ids] + [p for p in _grid_sets(engine_ids)
                                                              if p[1] != ("frozen",)], jobs=jobs)
    specs = []
    for ids, var, hz, dtx, pols in _report_plan(roads, engine_ids=engine_ids, dt=dt, taus=tp):
        specs += set_specs(roads, engine_ids=ids, variant=var, horizons=hz, dt=dtx, policies=pols)[0]
    execute(specs, jobs=jobs)                # one batch: every section below reads the cache
    main = ceilings(roads, engines=engine_ids, ratios=RATIOS, dt=dt, jobs=jobs, variants=ALL_VARIANTS,
                    readings=READINGS)
    taus = tau_table(engine_ids, variant=("frozen",), jobs=jobs)
    horizons = {e: {_rkey(r): float(r) * taus[e][0] for r in RATIOS} for e in engine_ids}
    runs = run_set(roads, engine_ids=engine_ids, variant=("frozen",), horizons=horizons, dt=dt, jobs=jobs,
                   policies=("a", "b", "a_b", "neutral"))
    out = dict(what="roads_ceiling.report: row 103 (1)'s ceiling and companions, rows 99-102's reports",
               synthetic=main["synthetic"], ceilings=main)
    out["two_mei"] = {e: {lab: main["per_engine"][e]["by"][lab]["two_mei"] for lab in main["per_engine"][e]["by"]}
                      for e in engine_ids}
    out["passes_T"] = dict(zip(("passes", "C"), passes_T(main, engines=engine_ids)))
    out["cg_vs_baseline"] = {e: dict(mean_cut_noknock=float(np.mean([p["cg_cut"]["noknock"] for p in
                                                                     main["per_engine"][e]["per_road"]])),
                                     per_road=[p["cg_cut"]["noknock"] for p in main["per_engine"][e]["per_road"]],
                                     below_baseline_roads=sum(1 for p in main["per_engine"][e]["per_road"]
                                                              if p["cg_cut"]["noknock"] < 0))
                             for e in engine_ids}
    out["decision13"] = _decision13(roads, runs, engine_ids, dt)
    out["observations"] = _obs_ranges(runs, engine_ids)
    out["knee_shares"] = _knee_shares(roads, runs, engine_ids)
    out["usable_window"] = _usable(roads, {e: taus[e][0] for e in engine_ids}, RATIOS)
    out["grids"] = _grids(roads, engine_ids=engine_ids, dt=dt, jobs=jobs)
    out["e6_row4"] = _e6_row4(roads, engine_ids=engine_ids, dt=dt, jobs=jobs, frozen_taus=taus)
    out["e6_row11"] = _e6_row11(roads, engine_ids=engine_ids, dt=dt, jobs=jobs, frozen_taus=taus)
    out["dt_repeat"] = _dt_repeat(roads, engine_ids=engine_ids, jobs=jobs, taus=taus)
    out["provenance"] = provenance(engine_ids)
    out["wall_s"] = time.perf_counter() - t0
    return out


# ------------------------------------------------------------------ control()
def _locked_spec(*, policy, egt_windows, detail):
    seed, w = V.EPISODES[0]
    return dict(kind="run", engine_id="b58", variant=["frozen"], cycle="locked", dt=DT, duration=LOCKED_DURATION_S,
                seed=int(seed), weights=[float(x) for x in w], policy=_json_policy(policy),
                egt_windows=[[float(a), float(b)] for a, b in egt_windows], detail=detail)


def control(*, jobs):
    """The control of row 103's "To implement": the probe's reproduction on the B58's locked climb
    (720 s, dt 1 s, onset 180 s, evaluate.EPISODES[0]), against results/premise.json (neutral damage
    848.052, damage_base 848.885; current-grade 449.625), and the direct-run lambda rows that replace
    section G's open-loop ones: lambda at its bound for H s before the climb (H 30 s among them) and over
    the whole flat (20-179 s, unlimited preview), each in points of 848.885, open loop (the housing
    replayed with the variant's gas and flow before 180 s, cg's after), closed loop with and without
    knock; the exhaust at ambient for 30 s and over the flat; and the hand-written predictive head start.
    The columns are the probe's repro.txt's."""
    with open(PREMISE, encoding="utf-8") as fh:
        prem = json.load(fh)
    base_ref = float(prem[PREMISE_NEUTRAL]["damage_base"])
    climb = [(LOCKED_ONSET_S, LOCKED_DURATION_S - LOCKED_ONSET_S)]
    rows = [("neutral", ("neutral",), ()), ("cg", ("cg",), ()), ("pred", ("pred",), ())]
    rows += [(f"lam_H{h}", ("lam", _windows_before(climb, H=float(h), first_from=FIRST_WINDOW_FROM_S)), ())
             for h in CONTROL_HS]
    rows.append(("lam_all", ("lam", _windows_before(climb, H=None, first_from=FIRST_WINDOW_FROM_S)), ()))
    rows.append(("egt_H30", ("cg",), _windows_before(climb, H=30.0, first_from=FIRST_WINDOW_FROM_S)))
    rows.append(("egt_all", ("cg",), _windows_before(climb, H=None, first_from=FIRST_WINDOW_FROM_S)))
    specs = [_locked_spec(policy=p, egt_windows=w, detail="full") for _n, p, w in rows]
    t0 = time.perf_counter()
    res = dict(zip([n for n, _p, _w in rows], execute(specs, jobs=jobs)))
    wall = time.perf_counter() - t0
    plant = plant_for("b58", ("frozen",))
    neu, cg = res["neutral"], res["cg"]
    Tcg = cg["t_turb"]
    t = cg["t"]
    I = cg["inputs"]
    self_err = float(np.max(np.abs(replay_turb(plant, I, egt=I[:, 3]) - Tcg)))
    cal = plant.engine.damage
    zero = np.zeros(len(t))

    def turb_damage(T):
        a, _o, _k = damage_split(T, cg["t_oil"], zero, cal=cal, dt=DT)
        return float(a.sum())
    D_turb_cg = turb_damage(Tcg)
    egt_drop = _section_g_drop_k()
    out_rows = {}
    for name, pol, wins in rows[2:]:
        r = res[name]
        w = (_windows_before(climb, H=30.0, first_from=FIRST_WINDOW_FROM_S) if name == "pred"
             else (pol[1] if pol[0] == "lam" else wins))
        sel = _mask(t, w)
        degt = float(np.median(cg["egt_k"][sel] - r["egt_k"][sel])) if name.startswith(("lam", "pred")) else None
        if name.startswith("egt"):
            Trep = replay_turb(plant, I, egt=np.where(sel, I[:, 4], I[:, 3]))
        else:
            before = t < LOCKED_ONSET_S
            gas = np.where(before, r["inputs"][:, 3], I[:, 3])
            Trep = replay_turb(plant, replay_inputs(I, egt=gas, mex=np.where(before, r["inputs"][:, 2], I[:, 2])),
                               egt=gas)
        k179 = int(np.flatnonzero(t == LOCKED_ONSET_S - 1.0)[0])
        out_rows[name] = dict(
            windows=[list(x) for x in w], dEGT_K=degt, dT_179_K=float(Tcg[k179] - r["t_turb"][k179]),
            open_loop_pts=float(100.0 * (D_turb_cg - turb_damage(Trep)) / base_ref),
            closed_knock_pts=float(100.0 * (cg["D_knock"] - r["D_knock"]) / base_ref),
            closed_noknock_pts=float(100.0 * (cg["D_noknock"] - r["D_noknock"]) / base_ref),
            d_turb=cg["turb"] - r["turb"], d_oil=cg["oil"] - r["oil"], d_knockterm=cg["knockterm"] - r["knockterm"],
            fuel_extra_pct=float(100.0 * (r["fuel"] / cg["fuel"] - 1.0)), seconds=r["seconds"])
    # section G's own assumption, replayed on today's plant (cg's flow, the gas lowered by its drop), H 30 s
    w30 = _mask(t, _windows_before(climb, H=30.0, first_from=FIRST_WINDOW_FROM_S))
    Tg = replay_turb(plant, I, egt=np.where(w30, I[:, 3] - egt_drop, I[:, 3]))
    k179 = int(np.flatnonzero(t == LOCKED_ONSET_S - 1.0)[0])
    sec_g = dict(egt_drop_k=egt_drop, dT_179_K=float(Tcg[k179] - Tg[k179]),
                 points=float(100.0 * (D_turb_cg - turb_damage(Tg)) / base_ref),
                 what="section G's method (results/preview_ceiling.py's assumed drop, cg's flow), replayed "
                      "on today's sub-stepped housing, lambda bound for 30 s",
                 drop_source="preview_ceiling.py's own drop, from the 30 September traces it reads, unrounded; "
                             "row 103's 68.2 K is the probe's 25.0 K x 0.15 / 0.055 "
                             "(probe_2026-10-30/repro_an.py.txt), which gives 8.79 K there")
    tau_series = plant.engine.thermal.c_turb / (plant.engine.thermal.ua_gas_turb
                                                * np.maximum(I[:, 2] / plant.engine.thermal.n_turbines, 0.5)
                                                + plant.engine.thermal.ua_turb_amb)
    checks = dict(
        neutral_damage=neu["D_knock"], neutral_damage_base=neu["base_knock"], cg_damage=cg["D_knock"],
        premise_neutral_damage=float(prem[PREMISE_NEUTRAL]["damage"]),
        premise_damage_base=base_ref, premise_cg_damage=float(prem[PREMISE_CG]["damage"]),
        neutral_matches=round(neu["D_knock"], 3) == round(float(prem[PREMISE_NEUTRAL]["damage"]), 3),
        base_matches=round(neu["base_knock"], 3) == round(base_ref, 3),
        cg_matches=round(cg["D_knock"], 3) == round(float(prem[PREMISE_CG]["damage"]), 3),
        replay_self_max_abs_k=self_err)
    return dict(what="the control (row 103, 'To implement'): the B58's locked climb against results/premise.json, "
                     "and the direct-run lambda rows that replace section G's open-loop ones",
                points_of=base_ref, rows=out_rows, checks=checks, section_g_replay=sec_g,
                tau_cg_flat_median_s=float(np.median(tau_series[150:180])),
                tau_cg_climb_median_s=float(np.median(tau_series[230:])),
                retired=dict(lam_H30=dict(direct_open=out_rows["lam_H30"]["open_loop_pts"],
                                          direct_closed_knock=out_rows["lam_H30"]["closed_knock_pts"],
                                          direct_closed_noknock=out_rows["lam_H30"]["closed_noknock_pts"]),
                             lam_all=dict(direct_open=out_rows["lam_all"]["open_loop_pts"],
                                          direct_closed_knock=out_rows["lam_all"]["closed_knock_pts"],
                                          direct_closed_noknock=out_rows["lam_all"]["closed_noknock_pts"])),
                runs=len(rows), jobs=int(jobs), wall_s=wall, provenance=provenance(["b58"]))


def control_text(c):
    k = c["checks"]
    L = [f"CONTROL: the B58's locked climb (720 s, dt 1 s, onset 180 s, evaluate.EPISODES[0]); "
         f"{c['runs']} direct runs at {c['jobs']} jobs, wall {c['wall_s']:.0f} s",
         f"neutral damage {k['neutral_damage']:.3f} (damage_base {k['neutral_damage_base']:.3f}); "
         f"results/premise.json {k['premise_neutral_damage']:.3f} / {k['premise_damage_base']:.3f}: "
         f"{'MATCH' if k['neutral_matches'] and k['base_matches'] else 'DIFFER'}",
         f"current-grade damage {k['cg_damage']:.3f}; results/premise.json {k['premise_cg_damage']:.3f}: "
         f"{'MATCH' if k['cg_matches'] else 'DIFFER'}",
         f"replay check: current-grade's housing replayed from its own inputs, max |dT| {k['replay_self_max_abs_k']:.2e} K",
         f"tau of the housing on current-grade: flat 150-179 s median {c['tau_cg_flat_median_s']:.1f} s, "
         f"climb 230-718 s median {c['tau_cg_climb_median_s']:.1f} s",
         "",
         f"head start at the climb start, and the points it buys (points = 100 x saved / {c['points_of']:.3f}, "
         "the premise's damage_base)",
         f"   {'row':<12}{'dEGT K':>8}{'dT@179 K':>10}{'open-loop pts':>15}{'closed pts kn':>15}"
         f"{'closed pts nk':>15}{'fuel %':>9}"]
    order = ["pred", "lam_H30", "lam_all", "egt_H30", "egt_all"] + [f"lam_H{h}" for h in CONTROL_HS if h != 30]
    for nm in order:
        r = c["rows"][nm]
        de = "nan" if r["dEGT_K"] is None else f"{r['dEGT_K']:.1f}"
        L.append(f"   {nm:<12}{de:>8}{r['dT_179_K']:10.2f}{r['open_loop_pts']:15.3f}{r['closed_knock_pts']:15.3f}"
                 f"{r['closed_noknock_pts']:15.3f}{r['fuel_extra_pct']:+9.3f}")
    L.append("")
    L.append("   term split of the closed-loop saving (units): turbine / oil / knock")
    for nm in order:
        r = c["rows"][nm]
        L.append(f"   {nm:<12}{r['d_turb']:9.3f}{r['d_oil']:9.3f}{r['d_knockterm']:9.3f}")
    g = c["section_g_replay"]
    L += ["", f"section G's method on today's housing (its assumed drop {g['egt_drop_k']:.2f} K at cg's flow, "
              f"lambda bound for 30 s): dT@179 {g['dT_179_K']:.2f} K, {g['points']:.3f} points",
          f"   (the drop: {g['drop_source']})",
          "lam_H30 is lambda at its bound for the 30 s before the climb (the agent's own levers); lam_all over "
          "the whole flat, 20-179 s (unlimited preview); egt rows hold the agent's exhaust at ambient (impossible)."]
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ sweep()
def _design_climb(t, *, onset_s, L_s, grade):
    """One climb of row 101's shape on the time axis t: up over 8 s from onset_s, held to onset_s + L_s,
    down over 8 s from there (the ramps of _family_arrays)."""
    t = np.asarray(t, dtype=float)
    up = np.clip((t - onset_s) / RAMP_S, 0.0, 1.0)
    down = np.clip(1.0 - (t - (onset_s + L_s)) / RAMP_S, 0.0, 1.0)
    return grade * np.minimum(up, down)


def _c5_summary(steps, out):
    full = [s for s in steps if not s.transition]
    mins = {}
    for s in full:
        for name, m, gates in s.margins:
            key = name.split("_")[-1] + ("" if gates else " (ungated)")
            mins[key] = min(mins.get(key, float("inf")), float(m))
    return dict(outcome=out.outcome, gated_share=out.gated_share, thin=out.thin, n_steps=out.n_steps,
                n_gated=out.n_gated, failing_steps=len(out.failing_steps), held=sorted({s.held for s in full}),
                min_margins=mins, no_margin_case=sorted({str(s.no_margin_case) for s in full}),
                rpm_median=float(np.median([s.rpm for s in full])) if full else None,
                demand_median_nm=float(np.median([s.demand_nm for s in full])) if full else None)


def sweep(*, jobs):
    """Row 101's sweep before the draw: on every car at 130 km/h, grade 10-12 % in 0.05 % steps, on a
    locked-climb-style cycle at that grade (make_grade_climb: 720 s, 0 -> 130 km/h over 20 s, the grade
    ramped up over 8 s from 180 s, 315 K): C5 at 1.9 % with the contract's thin share (epa_stats.c5_steps
    and c5_climb over the climb, c5_margin over the road), C5 again over the design's own slot extent
    (one climb of L 67 s and of L 85 s at that grade, ramped down, first step 180 to last 180 + L + 8,
    as the draw reads a slot), and current-grade's delivery from the end of the ramp (steps over the
    tracking tolerance, steps under 95 % of the request, the largest shortfall), over the whole climb and
    over its first 77 s (the design's longest full grade)."""
    import epa_stats as ES
    from thresholds import contract as K
    specs, keys = [], []
    for e in ENGINES:
        for g in SWEEP_GRADES:
            seed, w = V.EPISODES[0]
            specs.append(dict(kind="run", engine_id=e, variant=["frozen"], cycle="grade_climb", dt=DT,
                              duration=SWEEP_DURATION_S, t_amb=DESIGN_T_AMB_K, grade=g, v_kmh=DESIGN_V_KMH,
                              seed=int(seed), weights=[float(x) for x in w], policy=["cg"], detail="cg"))
            keys.append((e, g))
    t0 = time.perf_counter()
    res = dict(zip(keys, execute(specs, jobs=jobs)))
    wall = time.perf_counter() - t0
    out = {}
    for e in ENGINES:
        p = plant_for(e, ("frozen",))
        rows = []
        for g in SWEEP_GRADES:
            cyc = E.make_grade_climb(duration=SWEEP_DURATION_S, dt=DT, t_amb=DESIGN_T_AMB_K, grade=g,
                                     v_kmh=DESIGN_V_KMH)
            n = len(cyc["t"])
            steps = ES.c5_steps(p, cyc, first=int(SWEEP_ONSET_S / DT), last=n - 1, dt=DT)
            c5 = _c5_summary(steps, ES.c5_climb(steps, margin=C5_MARGIN, thin_share=K.C5_THIN_SHARE))
            whole = ES.c5_margin(p, cyc, dt=DT)
            gated = [m for s in whole if s.gated for (_nm, m, gates) in s.margins if gates]
            c5["road_min_gated_margin"] = float(min(gated)) if gated else None
            # the design's own slot (row 101): the same grade as one climb of the shortest and the
            # longest L, ramped up over 8 s from 180 s and down over 8 s from 180 + L, C5 over its
            # recorded extent, first step 180 to last step 180 + L + 8, as the draw reads it
            c5["design_extent"] = {}
            for L in SWEEP_DESIGN_L_S:
                cx = dict(cyc, grade=_design_climb(cyc["t"], onset_s=SWEEP_ONSET_S, L_s=L, grade=g))
                st = ES.c5_steps(p, cx, first=int(SWEEP_ONSET_S / DT),
                                 last=int(round((SWEEP_ONSET_S + L + RAMP_S) / DT)), dt=DT)
                c5["design_extent"][f"L{L:g}"] = _c5_summary(
                    st, ES.c5_climb(st, margin=C5_MARGIN, thin_share=K.C5_THIN_SHARE))
            r = res[(e, g)]
            t, req, tq = r["t"], r["torque_req"], r["torque"]
            e_track = np.abs(req - tq) / np.maximum(req, 40.0)
            dl = {}
            for lab, hi in (("whole_climb", float("inf")), ("first_77s", SWEEP_ONSET_S + RAMP_S
                                                            + DESIGN_LONGEST_FULL_GRADE_S)):
                m = (t >= SWEEP_ONSET_S + RAMP_S) & (t < hi)
                dl[lab] = dict(steps=int(m.sum()), over_tol=int((e_track[m] > E.TRACK_TOL).sum()),
                               share_over_tol=float((e_track[m] > E.TRACK_TOL).mean()),
                               under95=int((tq[m] < TORQUE_SHORT * req[m]).sum()),
                               largest_shortfall_nm=float((req[m] - tq[m]).max()))
            rows.append(dict(grade=g, c5=c5, delivery=dl, base_peak_turb_k=r["base_peak_turb_k"],
                             cg_peak_turb_k=r["peak_turb_k"], knee_k=float(p.engine.damage.turb_knee_k)))
        out[e] = rows
    return dict(what="row 101's sweep before the draw: C5 at 1.9 % and current-grade's delivery at 130 km/h, "
                     "10-12 % in 0.05 % steps, every car", grades=list(SWEEP_GRADES), margin=C5_MARGIN,
                thin_share=K.C5_THIN_SHARE, track_tol=E.TRACK_TOL, cars=out, runs=len(specs), jobs=int(jobs),
                wall_s=wall, provenance=provenance(list(ENGINES)))


def sweep_text(s):
    L = [f"SWEEP BEFORE THE DRAW (row 101): every car at 130 km/h on make_grade_climb (720 s, grade from 180 s, "
         f"315 K), 10-12 % in 0.05 % steps; {s['runs']} current-grade runs at {s['jobs']} jobs, wall {s['wall_s']:.0f} s",
         f"C5 at {100 * s['margin']:.1f} % (thin share {s['thin_share']}); delivery from 188 s: steps over "
         f"TRACK_TOL {s['track_tol']}, steps under 95 % of the request, the largest shortfall",
         ""]
    for e, rows in s["cars"].items():
        L.append(f"{e}")
        out = {}
        for r in rows:
            out.setdefault(r["c5"]["outcome"], []).append(r["grade"])
        L.append("   C5 outcomes: " + "; ".join(f"{k} {len(v)} grades ({100 * min(v):.2f}-{100 * max(v):.2f} %)"
                                               for k, v in out.items()))
        for lab in (rows[0]["c5"].get("design_extent") or {}):
            ox = {}
            for r in rows:
                ox.setdefault(r["c5"]["design_extent"][lab]["outcome"], []).append(r["grade"])
            mins = [(min([v for kk, v in r["c5"]["design_extent"][lab]["min_margins"].items()
                          if "ungated" not in kk] or [float("nan")]), r["grade"]) for r in rows]
            lo = min(mins)
            L.append(f"   C5 over the design's slot extent, {lab} (180 s to 180 + L + 8 s): "
                     + "; ".join(f"{k} {len(v)} grades ({100 * min(v):.2f}-{100 * max(v):.2f} %)"
                                 for k, v in ox.items())
                     + f"; smallest gated margin {lo[0]:.4f} at {100 * lo[1]:.2f} %")
        keys = sorted({k for r in rows for k in r["c5"]["min_margins"]})
        for kk in keys:
            vals = [(r["c5"]["min_margins"].get(kk), r["grade"]) for r in rows if kk in r["c5"]["min_margins"]]
            lo = min(vals)
            L.append(f"   smallest {kk} margin {lo[0]:.4f} at {100 * lo[1]:.2f} %; largest {max(vals)[0]:.4f}")
        held = sorted({h for r in rows for h in r["c5"]["held"]})
        L.append(f"   held: {held}; gated share {min(r['c5']['gated_share'] for r in rows):.3f}-"
                 f"{max(r['c5']['gated_share'] for r in rows):.3f}")
        for lab in ("whole_climb", "first_77s"):
            ot = [r["delivery"][lab]["over_tol"] for r in rows]
            u9 = [r["delivery"][lab]["under95"] for r in rows]
            sh = [r["delivery"][lab]["largest_shortfall_nm"] for r in rows]
            st = rows[0]["delivery"][lab]["steps"]
            bad = [100 * r["grade"] for r in rows if r["delivery"][lab]["over_tol"] > 0]
            L.append(f"   delivery, {lab} ({st} steps): over tolerance {min(ot)}-{max(ot)} steps"
                     + (f" (at {', '.join(f'{x:.2f}' for x in bad)} %)" if bad else "")
                     + f"; under 95 % {min(u9)}-{max(u9)}; largest shortfall {max(sh):.2f} Nm")
        L.append(f"   baseline peak minus knee {min(r['base_peak_turb_k'] - r['knee_k'] for r in rows):+.1f} to "
                 f"{max(r['base_peak_turb_k'] - r['knee_k'] for r in rows):+.1f} K")
        L.append("")
    L.append("per grade (C5 outcome, smallest gated margin, delivery over tolerance whole/first 77 s):")
    for e, rows in s["cars"].items():
        L.append(f"  {e}: " + " ".join(
            f"{100 * r['grade']:.2f}:{r['c5']['outcome'][0]}/"
            f"{min([v for kk, v in r['c5']['min_margins'].items() if 'ungated' not in kk] or [float('nan')]):.3f}/"
            f"{r['delivery']['whole_climb']['over_tol']}/{r['delivery']['first_77s']['over_tol']}" for r in rows))
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ timing()
def timing(*, jobs):
    """One 900 s SYNTHETIC road (synthetic_roads, SYNTHETIC_SEED_TIMING) timed closed loop with `jobs`
    runs at once: the four engines under cg, (b), (a_b) and the neutral policy, the first `jobs` of them
    in one wave (mistake 22: the draw's time is estimated from this, not assumed)."""
    road = synthetic_roads(SYNTHETIC_SEED_TIMING, n_roads=1, duration_s=900.0)[0]
    pols = [("cg", ("cg",)), ("b", ("lam", windows_b(road))), ("a_b", ("lam", windows_ab(road))),
            ("neutral", ("neutral",))]
    specs, names = [], []
    for nm, pol in pols:
        for e in ENGINES:
            specs.append(_run_spec(engine_id=e, variant=("frozen",), road=road, dt=DT, policy=pol, detail="light"))
            names.append((e, nm))
    specs, names = specs[:int(jobs)], names[:int(jobs)]
    for s in specs:                          # a timing is a fresh run: never served from the cache
        _CACHE.pop(_spec_key(s), None)
    others = _python_processes()
    t0 = time.perf_counter()
    res = execute(specs, jobs=jobs)
    wall = time.perf_counter() - t0
    per = [dict(engine=e, policy=nm, seconds=r["seconds"], steps=r["steps"], s_per_step=r["seconds"] / r["steps"])
           for (e, nm), r in zip(names, res)]
    sec = [p["seconds"] for p in per]
    sps = [p["s_per_step"] for p in per]
    return dict(what="one 900 s SYNTHETIC road timed closed loop, all runs at once", label=road["label"],
                road=dict(k=road["k"], climbs=[dict(onset_s=c["onset_s"], L_s=c["L_s"], grade=c["grade"])
                                               for c in road["climbs"]], steps=len(road["cycle"]["t"])),
                jobs=int(jobs), concurrent_runs=len(specs), wall_s=wall, runs=per,
                python_processes_before=others,
                seconds=dict(min=min(sec), median=float(np.median(sec)), max=max(sec)),
                s_per_step=dict(min=min(sps), median=float(np.median(sps)), max=max(sps)),
                provenance=provenance(list(ENGINES)))


def _python_processes():
    """How many python.exe processes run on this machine (Windows tasklist; None elsewhere): the
    timing's load, which this module does not control (other work may run beside it)."""
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV", "/NH"],
                             capture_output=True, text=True, timeout=30).stdout
        return sum(1 for line in out.splitlines() if line.lower().startswith('"python.exe"'))
    except (OSError, subprocess.SubprocessError):
        return None


def timing_text(t):
    # the road's sample count, not the episode's steps: the environment runs n - 1 steps on n samples, and
    # each run below prints the steps it measured (row 122 (2))
    L = [f"TIMING: one 900 s road ({t['label']}; {len(t['road']['climbs'])} climbs, {t['road']['steps']} samples), "
         f"{t['concurrent_runs']} closed-loop runs at once at {t['jobs']} jobs; wall {t['wall_s']:.1f} s",
         f"per run: min {t['seconds']['min']:.1f} s, median {t['seconds']['median']:.1f} s, max {t['seconds']['max']:.1f} s",
         f"per step: min {t['s_per_step']['min']:.4f} s, median {t['s_per_step']['median']:.4f} s, "
         f"max {t['s_per_step']['max']:.4f} s",
         f"cpu_count {t['provenance']['cpu_count']}; python.exe processes running before the wave (this one "
         f"included): {t['python_processes_before']}; other work on the machine is not controlled",
         ("" if t["jobs"] == 14 else f"docs/build_step_2/ORDER_TO_TRAINING.md step 0 (c) times the road at 14 jobs; "
                                    f"this run used {t['jobs']} (the cap while other work runs beside it)"),
         ""]
    for p in t["runs"]:
        L.append(f"   {p['engine']:<12} {p['policy']:<8} {p['seconds']:7.1f} s  {p['steps']} steps  "
                 f"{p['s_per_step']:.4f} s/step")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ writing
def _jsonable(x):
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, np.ndarray):
        return [_jsonable(v) for v in x.tolist()]
    if isinstance(x, (np.floating, float)):
        v = float(x)
        return v if math.isfinite(v) else None
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    return x


def write_record(name, result, text, *, out_dir):
    """Write <out_dir>/<name>.json and .txt. Refuses roads.json and the attempts log of the real draw
    (row 96: they are the roads module's)."""
    if name in ("roads", "redraws") or "attempt" in name:
        raise ValueError(f"roads_ceiling.write_record: {name!r} is the roads module's record, never this one's")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f"{name}.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(_jsonable(result), fh, indent=1)
        fh.write("\n")
    with open(os.path.join(out_dir, f"{name}.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def smoke_text(r):
    L = [f"SMOKE (report() on {r['ceilings']['n_roads']} SYNTHETIC road(s); no number here is a result)"]
    for e, blk in r["ceilings"]["per_engine"].items():
        for lab, b in blk["by"].items():
            L.append(f"  {e:<12} r {lab:<4} H {b['H_s']:6.1f} s  C {b['C']:7.3f}  pooled "
                     f"{b['a']['noknock']['pooled']:7.3f}  knock {b['a']['knock']['mean']:7.3f}")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("what", choices=("control", "sweep", "timing", "smoke"))
    ap.add_argument("--jobs", type=int, default=12)
    ap.add_argument("--out", default=None, help="smoke only: the directory to write to (required)")
    a = ap.parse_args()
    install_guard()
    if a.what == "control":
        c = control(jobs=a.jobs)
        txt = control_text(c)
        write_record("control", c, txt, out_dir=OUT_DIR)
    elif a.what == "sweep":
        s = sweep(jobs=a.jobs)
        txt = sweep_text(s)
        write_record("sweep", s, txt, out_dir=OUT_DIR)
    elif a.what == "timing":
        t = timing(jobs=a.jobs)
        txt = timing_text(t)
        write_record("timing", t, txt, out_dir=OUT_DIR)
    else:
        if not a.out or os.path.abspath(a.out).replace("\\", "/").lower().startswith(
                OUT_DIR.replace("\\", "/").lower()):
            raise SystemExit("smoke: --out DIR is required, outside results/EPA_ROADS/")
        road = synthetic_roads(SYNTHETIC_SEED_SMOKE, n_roads=1, duration_s=600.0)
        r = report(road, engines=ENGINES, dt=DT, jobs=a.jobs)
        txt = smoke_text(r)
        write_record("smoke_report", r, txt, out_dir=a.out)
    sys.stdout.write(txt)


if __name__ == "__main__":
    main()

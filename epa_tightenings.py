"""epa_tightenings.py -- row 104's tightenings of L1 and E8, measured on the B58 on the roads as first drawn.

    python -B epa_tightenings.py run --jobs J
        ORDER step 8: the tightenings on results/EPA_ROADS/roads.json, written once to
        results/EPA_TIGHTENINGS.json. Refused unless this tree's code, its data inputs (the contract,
        results/car_spark_boost.json, results/ENGINE_THRESHOLDS/ecu/) and results/EPA_ROADS/ are committed
        and clean, no compiled file stands beside the code (run with -B, every __pycache__ deleted first),
        roads.json is the committed record its attempts log names, its roads_seed is the reveal's, and every
        file, plant and version it hashes is as it recorded (epa_roads.verify_record). The code must be
        committed before the record is written, so the code and the record are two commits.
    python -B epa_tightenings.py synthetic --synthetic-seed N --roads n --out DIR --jobs J [--roads-record PATH]
        The whole chain on SYNTHETIC roads: epa_roads.generate from a SYNTHETIC seed (an int below 2**32, so
        never roads_seed), n roads, written with the B58's tau to DIR/roads_SYNTHETIC.json, then the
        tightenings to DIR/EPA_TIGHTENINGS_SYNTHETIC.json. --roads-record reads an existing SYNTHETIC record
        instead (epa_roads.py smoke writes one). DIR lies outside every git work tree.
    python -B epa_tightenings.py timing --out DIR --jobs J
        One SYNTHETIC 900 s road through the whole chain at J jobs (mistake 22), and the real run's wall time
        predicted from the per-task seconds it measured. DIR lies outside every git work tree, or is this
        tree's results/EPA_TIGHTENINGS/ with the code committed and clean.
    python -B epa_tightenings.py stopped
        Row 129 (4): the roads stopped for a reason that is not a coding defect (row 103 (3)), so no road set
        exists. Writes results/EPA_TIGHTENINGS.json once, L1 and E8 untightened (NO ROADS below). Refused unless
        the record is absent and was never committed; roads.json is absent and was never committed; the attempts
        log is committed at HEAD and never rewritten, its draw lines hold no roads outcome and end in exactly one
        stop that is not a coding defect, right after its own start line, whose logged reveals, checked again
        against the roads commit's hash lines, do not both match, every start line as draw writes it; HEAD is
        origin's GRA-test, as the remote reports it (the stop pushed, and nothing newer on the shared branch); and
        the code, its data inputs and results/EPA_ROADS/ are committed and clean, with no compiled file beside the
        code and Python run with -B (real_problems' own gates).

    OMP_NUM_THREADS=1 and MKL_NUM_THREADS=1 must be set (PLAN.md 5.1). Exit codes: 0 written, 2 refused.

WHERE IT SITS (row 121 (2)). Row 104 puts the L1 preview policy and the writer "in the roads module". Written
in epa_roads.py at ORDER step 8 they would change a file roads.json hashes, and every redraw would refuse. So
they are here: this module imports the roads module, and no hashed module imports it (test_epa_tightenings
checks the import closure of the hashed files). Nothing here edits a hashed file, a pinned folder or a record.

THE ROADS (rows 101, 104, 122 (2)). Road k of the record's "roads" (the final arrays of the first draw) runs
with its own episode_seed and weights, which must be evaluate.EPISODES[k]'s (refused otherwise), at its dt,
900 samples and so 899 steps. Every run is one closed-loop episode of the B58 through
roads_ceiling.run_episode_record, the weights pinned after reset as evaluate.run_episode pins them.

THE SCORING (row 104; row 122 (4)). A policy's cut is evaluate.py's, 100 (1 - median D / median D_base) over
the roads, D_base the neutral policy's ("baseline ECU", evaluate.py:475, :533-538). A pair of two policies is
the difference of their cuts, 100 (median D_ref - median D_var) / median D_base: roads_ceiling.aggregate's
evaluate_form, the one implementation of that form on a road set. D is read two ways, with the knock term
(the episode's damage) and without it (evaluate.run_episode's damage_thermal).

L1 (row 104; MD:1500-1502, S2a's definition). The preview pair is the predictive policy reading the largest
grade within the next H seconds, minus current-grade. HorizonPredictive is check_premise.p_predictive itself,
given a view of the environment whose preview reads that largest grade (steps k+1 .. k+int(H/dt), clipped at
the road's last sample, zero when the preview is off) in place of the +15 s and +30 s samples; its levers,
depth and thresholds are p_predictive's. H is the B58's two horizons from the roads record's H_table (row 102:
r = 0.5 and 1.5 times the B58's tau, 23.67 s and 71.00 s on the plant of 865f8e7b7e5c2dbe). Each policy
(neutral, current-grade, the predictive policy at each H) runs once per road. The per-step housing, oil and
knock integral are re-scored at the B58's knee shifted over thresholds/knee_shift.py's grid (SHIFTS), by
roads_ceiling.damage_split, which checks its sum against engine_env.damage_rate at every step; the re-score
at a shift of 0 must give back each run's own two damages within 1e-6 (RESCORE_TOL). The slope at a shift s is |pair(s) - pair(0)| / |s|
(knee_shift.py:56-60); the slope recorded is the largest over both H, every shift and both readings, the first
in that order on a tie (DESIGN). `set`, `damage_reading` and `shift_k` name what gave it.

E8 (row 104; MD:1020-1028). The fifteen runs of the contract's grid (ecu_strategy_b58: every shift of
k3_pair_change_vs_lambda and _vs_spark, the nominal included), each its own run, on the head-start pair
(current-grade minus reactive), with the neutral policy for evaluate.py's form. The ECU is shifted through
k3_knee.shifted_ecu; the knee is re-set as thresholds/ecu_shift.py sets it (:10-13; decision 33): the
unshifted baseline's seconds above the B58's knee on the locked climb (k3_knee.baseline_trace, measured here,
compared with results/ENGINE_THRESHOLDS/ecu/k3_nominal.json), then k3_knee.k3 on the shifted locked climb (the
nominal keeps the B58's knee, as ecu_shift.one keeps it), and the policies run on k3_knee.with_knee(B58, knee),
so that they trigger on that knee (check_premise.trigger_k) and damage is scored against it. Each knee is
compared with the pinned k3_<name>.json's (read, never written); in the real run a difference, or an above0
that is not k3_nominal.json's, is refused as soon as its task ends, before the road runs it would set. The
locked-climb tasks go to the front of the queue. Each shift records on how many roads the reactive policy's
damage equals the neutral one's, and the neutral peak housing against that shift's knee: where reactive never
acts, the head-start pair is current-grade's cut alone. thresholds/ecu_shift.py's one and run_all are
never called: they write results/ENGINE_THRESHOLDS/ecu/, which test_contract_pinned pins. The relative change
per shift, both readings and the larger |change| with its sign, is thresholds.contract.response, the function
that built the contract's own tables, on the medians over the roads.

THE B58'S E8 BAND (row 107 (4)). P is the larger of the locked-climb and the roads responses at each shift
(epa_stats.e8_response, as the held-out run takes it). E is |P_spark| at the larger end of the B58's
spark-under-boost reading, car minus model, -3.81 deg (31 readings) or -1.78 deg (the climb's cell, 4
readings), and u_val is 2.07 deg (the standard error of that median) through P's local slope there
(epa_stats.p_slope), both from results/car_spark_boost.json. u_val is used only when car_spark_boost.summary
gives back the 31 readings and their standard error from the record's readings, the model spark recomputed by
car_spark_boost.model_spark on the B58 as built (row 107 (4)'s condition; otherwise u_val is missing and kappa
takes row 107 (3)'s floor); whether every other printed field of both cells comes back too is recorded beside
it. No row defines a u_stat for this reading, so the line is labelled with u_stat None (epa_stats.line_label:
it certifies nothing) and the row reads untested, as row 107 (4) writes it, or off: kappa is
max(1 + |E|/R, epa_stats.kappa) when untested (row 107 (3)); an off row has no kappa in any row, so kappa is
None and the record names the case for the team. The locked-climb-only reading is beside it, and so is each
reading in the sign of E8's own statistic (model minus car, epa_stats._core_E8), labelled descriptive.

THE RECORD (validate_epa.load_tightenings; WP3_INTERFACES 7.5). schema "epa-tightenings/1", plant "b58",
roads_sha (the roads record's sha_text), roads_seed, L1 {slope_points_per_K, set, shift_k, damage_reading},
E8 {k3_pair_change_vs_lambda_roads, k3_pair_change_vs_spark_roads}, provenance {commit, code_sha_text,
plant_sha, engine_sha}; plant_sha and engine_sha are validate_epa.b58_identity()'s, as arm builds them;
code_sha_text covers this module's import closure, epa_freeze.CODE_HASHED and the B58's plant files (DESIGN).
Every other key is beside the layout and read by nobody: every per-road damage, the pairs, every slope, each
knee, the B58's band, the timing. Before it is linked into place the written file is read back by
validate_epa.load_tightenings and checked by validate_epa.tightening_problems against the contract's grid and
the B58 as built; a refusal leaves nothing.

NO ROADS (row 129 (4)). If the roads stop for anything but a coding defect (row 103 (3)), no road set exists and
"measured on that set" has no referent. The only such stop is a reveal that does not match its hash line, which
epa_roads.draw logs before roads_seed is computed (epa_roads.py:1598-1602 against :1611) and after which it
refuses every attempt. A withheld or lost integer is entered in `epa_roads.py draw` as 2**128, the smallest
integer parse_reveal takes, typed as its canonical decimal 340282366920938463463374607431768211456 (the text
"2**128" is refused before anything is logged), so that the draw itself logs the stop. Run 2 then runs with L1
and E8 untightened (UNTIGHTENED), and `stopped` writes the record in the layout above: roads_sha "none",
roads_seed -1 (an int), seed_kind "NONE"; L1's slope_points_per_K, set, damage_reading and shift_k the
contract's knee_shift.largest, so epa_stats._R's min(R, b/slope rounded down) gives every engine the contract's
R; E8's two roads tables the contract's own locked-climb tables (ecu_strategy_b58), verbatim, so
epa_stats.e8_response's larger response is the contract's at every shift; the B58's E8 band b58_band's on those
tables, which is the locked-climb reading; the provenance provenance()'s and the write write_checked's, as `run`
builds them (untightened is the one place the writer and the check read L1 and E8 from the contract, mistake
10). The log is read as draw writes it: the stop right after its own start line, the start lines numbered 1, 2,
... in order, each logging parse_reveal's two ints, the reveal_matches draw computed and the roads commit's hash
lines (a decimal string, a null or a missing reveal is not a line draw writes). The roads step is a step of the
shared branch, so `stopped` also reads origin's GRA-test as the draw does (epa_roads.remote_state): a clone left
at the roads commit can log a stop of its own while the branch holds a drawn set, and its record would stand on
nothing. An earlier attempt whose logged reveals both match (it crashed after roads_seed was computed, and a
later attempt stopped) is not refused: row 129 (4) discloses that either person could force a stop after the
reveal; the record names those attempts (no_roads.earlier_attempts_both_matching) and the summary prints them.
stopped_record_problems is what validate_epa's arming does not check of that record once committed (the arming
takes any record in the layout: results/EPA_TIGHTENINGS/README.md says which tests must pass before it);
test_epa_tightenings.LiveRecord and test_epa_roads.Tightenings accept it, and no other record, while roads.json
is absent. Every summary printed of it labels L1 and E8 "untightened: no roads (row 103 (3))"; validate_epa's own
outputs carry no such label, so a Run 2 report takes it from the record (untightened, L1.label, E8.label).

THE GUARD. Every subcommand installs epa_roads' audit hook first, and every worker process does
(epa_roads._worker_init): an open of logs/epa*, data/engines/<id>/epa_*, results/EPA_VALIDATION or any .csv is
refused, matched anywhere in the path. No EPA table and no held-out row is read, and no epa_rows reader is
called. The record lists every repository file the run and its workers opened, and every compiled file found
beside the code (python -B stops Python writing bytecode, not reading it; the real run refuses any).

TIME (mistake 22). The probe measured 0.169-0.173 s per step at 14 jobs (results/EPA_ROADS/timing.txt,
`python roads_ceiling.py timing --jobs 14`). The real run is 20 roads x (4 + 3 x 15) = 980 road runs of 899
steps and 15 locked-climb tasks: at the probe's rate, 980 x 899 x 0.171 / 14 s, about 3 h on an idle machine
(arithmetic; ASSUMED that the rate carries over). Its wall time is predicted by `timing` from the seconds it
measures, and every run records its own (each task's own seconds as task_s).
"""
import os
import sys

if __name__ == "__main__":
    # PLAN.md 5.1: one BLAS thread, set before NumPy is first imported
    for _var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        if os.environ.get(_var) != "1":
            sys.exit(f"epa_tightenings.py: {_var} is {os.environ.get(_var)!r}; set it to 1 before running "
                     "(PLAN.md 5.1: one BLAS thread, set before NumPy is imported)")

import argparse
import collections
import contextlib
import copy
import dataclasses
import datetime
import hashlib
import json
import subprocess
import time
import types

import numpy as np

import check_premise as CP
import engine_env as E
import epa_freeze
import epa_roads as R
import epa_stats as ES
import evaluate as V
import fingerprint as FP
import k3_knee as K
import roads_ceiling as RC
import validate_epa as VE
from thresholds import common
from thresholds import contract as TC
from thresholds import ecu_shift as ECU
from thresholds import knee_shift as KS

REPO = os.path.dirname(os.path.abspath(__file__))
MODULE_REL = "epa_tightenings.py"
PLANT = VE.TIGHTENING_PLANT                     # "b58": decision 71, amendment E5
OUT_REL = VE.TIGHTENINGS_REL                    # results/EPA_TIGHTENINGS.json
OUT_DIR_REL = "results/EPA_TIGHTENINGS"         # the timing record's folder in the tree, and the README's
SCHEMA = VE.TIGHTENINGS_SCHEMA
SYNTHETIC_ROADS_NAME = "roads_SYNTHETIC.json"
SYNTHETIC_OUT_NAME = "EPA_TIGHTENINGS_SYNTHETIC.json"
TIMING_NAME = "timing.json"
SYNTHETIC_SEED_TIMING = 303                     # SYNTHETIC: the timing's road, never roads_seed

RATIOS = RC.RATIOS                              # row 102: H = r tau, r = 0.5 and 1.5
SHIFTS_K = tuple(float(s) for s in KS.SHIFTS)   # knee_shift's grid, 0 among them (BUILT, knee_shift.py:22)
READINGS = ("knock", "noknock")                 # the order of the slope rule's tie (DESIGN)
READING_TEXT = {"knock": "knock term on (the episode's damage)",
                "noknock": "knock term off (evaluate.run_episode's damage_thermal)"}
CONTRACT_KEY = {"knock": "damage", "noknock": "damage_thermal"}   # thresholds.contract.pair's two readings
L1_POLICIES = ("neutral", "cg")                 # with "pred@<r>" per ratio
E8_POLICIES = {"neutral": "baseline", "reactive": "reactive", "cg": "current-grade"}   # mine: contract.pair's
GRID_KEYS = {"lambda": "k3_pair_change_vs_lambda", "spark": "k3_pair_change_vs_spark"}
ROADS_KEYS = {"lambda": VE.TIGHTENINGS_E8_KEYS[0], "spark": VE.TIGHTENINGS_E8_KEYS[1]}
# DESIGN, as calibrate_epa.PROVISIONAL_KNEES takes its second knee: 50 K above the plant's own (amendment F7)
PROVISIONAL_STEP_K = 50.0
# the re-score at 0 K gives back each run's own damage within this (relative): the bound
# damage_robustness.load_records puts on knee_shift's basis. The environment sums its damage from the
# network's state as it holds it, in float32 where the float32 trims reach it (NEP 50), and the re-score in
# float64, so the two are not bit for bit: the record carries the worst difference (rescore_worst_relative),
# and test_epa_tightenings.KneeReal checks a real run against this bound
RESCORE_TOL = 1e-6

# row 107 (4): the B58's spark under boost, results/car_spark_boost.json (car_spark_boost.py:101-102 name its
# cells). The sign is the row's: car minus model, the ECU shift that moves the model's spark to the car's.
SPARK_RECORD_REL = "results/car_spark_boost.json"
SPARK_CELL_ALL = "all, 140-240 kPa"
SPARK_CELL_CLIMB = "the climb's cell, 2400-3000 rpm, 165-185 kPa"

# the run's data inputs, read from the tree the gates check: the contract (ecu_strategy_b58, E8's R, the L1
# basis), the spark-under-boost record and the pinned K3 folder (thresholds/ecu_shift.py's path)
ECU_DIR_REL = os.path.relpath(common.ECU_DIR, common.REPO).replace(os.sep, "/")
CONTRACT_JSON_REL = os.path.relpath(common.CONTRACT_JSON, common.REPO).replace(os.sep, "/")
DATA_INPUTS = tuple(R.CONTRACT_FILES) + (SPARK_RECORD_REL, ECU_DIR_REL)
# the locked-climb tasks wait at the front of the queue: the knees are then known, and in the real run
# checked, before the road runs they set, and the longest tasks start first
URGENT = ("above0", "k3")

# row 129 (4): the roads stopped for a reason that is not a coding defect (row 103 (3)), so no road set exists
NONE_KIND = "NONE"                              # the record's seed_kind
NONE_ROADS_SHA = "none"                         # its roads_sha: no roads.json was written
NONE_ROADS_SEED = -1                            # its roads_seed, an int: roads_seed was never computed
UNTIGHTENED = "untightened: no roads (row 103 (3))"
NEEDS_B = ("run with python -B: a run that writes bytecode leaves compiled files beside the code, which the gates "
           "refuse")

# the real run's shape, for the prediction (rows 101, 104): 20 roads, the L1 runs and the E8 runs per road
REAL_ROADS = R.N_ROADS
REAL_EPISODE_STEPS = int(R.DURATION_S / R.DT) - 1      # 899 (row 122 (2))

if R.TIGHTENINGS_REL != OUT_REL:
    raise ImportError("epa_tightenings: epa_roads and validate_epa name different tightenings records")
if PLANT != R.NEVER_DROPPED:
    raise ImportError("epa_tightenings: the tightenings' plant is not the B58 the roads module records")
if CONTRACT_JSON_REL not in R.CONTRACT_FILES or os.path.normcase(common.REPO) != os.path.normcase(REPO):
    raise ImportError("epa_tightenings: thresholds.common and epa_roads name different contracts or trees")


class Refused(Exception):
    """A precondition does not hold: nothing was computed or nothing was written."""


class TighteningsDefect(Exception):
    """A check of the computation failed (a re-score that does not give back a damage, a second knee that
    moves the trace, a grid that is not the contract's): a coding defect, and nothing is written."""


# =====================================================================================================
# The policies (row 104, L1)
# =====================================================================================================
def largest_grade_ahead(env, h_s):
    """The largest grade on the environment's cycle over the next h_s seconds: the samples at steps
    k+1 .. k+int(h_s/dt), the index clipped at the cycle's last sample as engine_env's _preview clips it,
    and 0.0 when the environment's preview is off (as _preview reads it). The window is DESIGN until a row
    fixes it, and it moves L1's slope (a review measured a few per cent on SYNTHETIC roads against k..k+int(H)
    and against row 117's four samples). This is the one implementation of S2a's "largest grade within the
    next H seconds" (MD:1500-1502): S2a's preview pair takes it from here, or from a copy a test compares with
    it, so that L1's tightening and S2a measure the same pair (mistake 10)."""
    if not env.use_preview:
        return 0.0
    g = env.cycle["grade"]
    j1 = min(env.k + int(h_s / env.dt), len(g) - 1)
    j0 = env.k + 1
    return float(np.max(np.asarray(g[j0:j1 + 1], dtype=float))) if j1 >= j0 else 0.0


class _HorizonView:
    """The environment as check_premise.p_predictive reads it, with the preview's +15 s and +30 s samples
    both read as the largest grade within the next H seconds. Every other attribute is the environment's."""

    def __init__(self, env, ahead):
        self._env = env
        self._ahead = float(ahead)

    def __getattr__(self, name):
        return getattr(self._env, name)

    def _preview(self):
        return [0.0, 0.0, self._ahead, self._ahead]


class HorizonPredictive:
    """S2a's predictive policy at horizon h_s (MD:1500-1502): check_premise.p_predictive, its levers and its
    depth unchanged, triggered by the largest grade within the next h_s seconds."""

    def __init__(self, h_s):
        if type(h_s) is not float or not h_s > 0.0:
            raise ValueError(f"HorizonPredictive: H {h_s!r} is not a Python float above 0 s")
        self.h_s = h_s

    def __call__(self, env, obs):
        return CP.p_predictive(_HorizonView(env, largest_grade_ahead(env, self.h_s)), obs)


def policy_of(spec):
    """("neutral",), ("reactive",), ("cg",) as roads_ceiling.make_policy builds them, or ("pred", H_s)."""
    if spec[0] == "pred":
        return HorizonPredictive(float(spec[1]))
    return RC.make_policy(tuple(spec))


# =====================================================================================================
# The runs, one task each, in-process or in a spawn worker
# =====================================================================================================
def _b58():
    return R.plant_of(PLANT)


def _task(task):
    """One task: "above0" (the unshifted locked-climb trace's seconds above the B58's knee, ecu_shift.one's
    above0), "k3" (k3_knee.k3 under k3_knee.shifted_ecu) or "road" (one closed-loop episode, at a knee, under a
    shift or none). Returns its result with the wall seconds it took (task_s; a K3 record's own "seconds" is
    the seconds its knee was set at) and the files this process has opened."""
    t0 = time.perf_counter()
    plant = _b58()
    k0 = plant.engine.damage.turb_knee_k
    kind = task["kind"]
    if kind == "above0":
        tr = K.baseline_trace(plant)
        out = {"time_above_nominal_s": int((tr.t_turb_k > k0).sum()), "trace_sha256": K.trace_sha256(tr),
               "steps": int(len(tr.t_turb_k)), **K.medians(tr)}
    elif kind == "k3":
        with K.shifted_ecu(task["ds"], task["dl"]):
            k = K.k3(plant, seconds=task["seconds"], provisional=(k0, k0 + PROVISIONAL_STEP_K))
        out = dict(k.as_json(), steps=None)
    elif kind == "road":
        knee = task["knee_k"]
        p = plant if knee == k0 else K.with_knee(plant, knee)
        ctx = K.shifted_ecu(task["ds"], task["dl"]) if task["shifted"] else contextlib.nullcontext()
        with ctx:
            res = RC.run_episode_record(p, task["cycle"], policy_of(task["policy"]), seed=task["seed"],
                                        weights=tuple(task["weights"]), dt=task["dt"], egt_ambient_windows=(),
                                        detail="full" if task["per_step"] else "light")
        out = {"D_knock": float(res["D_knock"]), "D_noknock": float(res["D_noknock"]), "steps": int(res["steps"]),
               "ret": float(res["ret"]), "peak_turb_k": float(res["peak_turb_k"])}
        if task["per_step"]:
            out.update(t_turb=np.asarray(res["t_turb"], dtype=float), t_oil=np.asarray(res["t_oil"], dtype=float),
                       ki=np.asarray(res["ki"], dtype=float))
    else:
        raise ValueError(f"epa_tightenings: unknown task {kind!r}")
    out["task_s"] = time.perf_counter() - t0
    out["opened"] = sorted(R.OPENED)
    return out


def road_task(road, *, policy, knee_k, ds, dl, shifted, per_step):
    """A road run's task: road k's cycle in the environment's form, its own seed and weights."""
    return {"kind": "road", "cycle": RC.env_cycle(road, dt=float(road["dt"])), "seed": int(road["episode_seed"]),
            "weights": [float(w) for w in road["weights"]], "dt": float(road["dt"]), "policy": list(policy),
            "knee_k": float(knee_k), "ds": float(ds), "dl": float(dl), "shifted": bool(shifted),
            "per_step": bool(per_step)}


def schedule(initial, on_done, *, jobs, log):
    """Run every task: `initial` [(key, task)], and whatever on_done(key, result) returns as each one ends.
    The tasks wait in one queue, those whose kind is in URGENT at its front (in their order), the rest at its
    back; at most `jobs` run at once. In-process at jobs 1, else in a spawn pool of `jobs` workers, each with
    epa_roads' guard. Returns {key: result}; a task's exception, or on_done's, stops the pool (the tasks
    already running finish, none waiting starts) and is raised."""
    results = {}
    t0 = time.perf_counter()
    last = [t0]
    queue = collections.deque()

    def add(items):
        items = list(items)
        for kt in reversed([x for x in items if x[0][0] in URGENT]):
            queue.appendleft(kt)
        queue.extend(x for x in items if x[0][0] not in URGENT)
        return len(items)

    def progress(n_done, n_known):
        now = time.perf_counter()
        if n_done == n_known or n_done % 25 == 0 or now - last[0] > 120.0:
            last[0] = now
            log(f"{n_done}/{n_known} tasks done, {now - t0:.0f} s")

    known = add(initial)
    if jobs <= 1:
        while queue:
            key, task = queue.popleft()
            results[key] = _task(task)
            known += add(on_done(key, results[key]))
            progress(len(results), known)
        return results
    import concurrent.futures as cf
    import multiprocessing as mp
    ex = cf.ProcessPoolExecutor(max_workers=int(jobs), mp_context=mp.get_context("spawn"),
                                initializer=R._worker_init, initargs=(tuple(R._GUARD["allow"]),))
    running = {}
    try:
        while queue or running:
            while queue and len(running) < int(jobs):
                key, task = queue.popleft()
                running[ex.submit(_task, task)] = key
            done, _ = cf.wait(running, return_when=cf.FIRST_COMPLETED)
            for f in done:
                key = running.pop(f)
                results[key] = f.result()
                known += add(on_done(key, results[key]))
                progress(len(results), known)
    except BaseException:
        ex.shutdown(wait=True, cancel_futures=True)
        raise
    ex.shutdown(wait=True)
    return results


# =====================================================================================================
# The roads record (rows 96, 97, 101, 102)
# =====================================================================================================
def horizons(record):
    """{"0.5": H_s, "1.5": H_s}: the B58's two horizons from the record's H_table (row 102)."""
    return {f"{r:g}": float(record["H_table"][PLANT][f"{r:g}"]["H_s"]) for r in RATIOS}


def roads_problems(record, *, kind):
    """Why a roads record cannot be the tightenings' roads, [] when it can: its schema and seed kind; its
    roads_seed (row 96's 60-bit integer, or a SYNTHETIC one below 2**32); 20 roads when REAL; road k paired
    with evaluate.EPISODES[k]'s seed and weights at the design's dt (row 101); each road the interface's dict
    (roads_ceiling.check_road); the B58's tau and H as h_table writes them (row 102), on 865f8e7b7e5c2dbe
    when REAL."""
    out = []
    if record.get("schema") != R.ROADS_SCHEMA:
        out.append(f"the roads record's schema is {record.get('schema')!r}, not {R.ROADS_SCHEMA!r}")
    if record.get("seed_kind") != kind:
        out.append(f"the roads record's seed_kind is {record.get('seed_kind')!r}, not {kind!r}")
    seed = (record.get("commit_reveal") or {}).get("roads_seed")
    why = R._seed_problem(seed, seed_kind=kind)
    if why:
        out.append(why)
    roads = record.get("roads")
    if not isinstance(roads, list) or not roads:
        return out + ["the roads record holds no roads"]
    if kind == "REAL" and len(roads) != R.N_ROADS:
        out.append(f"the roads record holds {len(roads)} roads, not {R.N_ROADS} (row 101)")
    if len(roads) > len(V.EPISODES):
        out.append(f"{len(roads)} roads, {len(V.EPISODES)} frozen episodes to pair them with")
    for i, road in enumerate(roads[:len(V.EPISODES)]):
        try:
            RC.check_road(road)
        except (KeyError, ValueError) as exc:
            out.append(f"road {i}: {exc}")
            continue
        seed_k, w_k = V.EPISODES[i]
        if road["k"] != i or road["episode_seed"] != seed_k or tuple(road["weights"]) != tuple(w_k):
            out.append(f"road {i} is not paired with evaluate.EPISODES[{i}] (row 101)")
        if float(road["dt"]) != R.DT:
            out.append(f"road {i}'s dt {road['dt']!r} is not the design's {R.DT}")
    try:
        tau = float(record["tau"][PLANT]["tau_s"])
        H = horizons(record)
        for r in RATIOS:
            if H[f"{r:g}"] != float(r) * tau:
                out.append(f"the record's H at r = {r:g} is not r times the B58's tau (row 102)")
        if kind == "REAL" and record["tau"][PLANT].get("plant_sha") != R.B58_PLANT_SHA:
            out.append(f"the B58's tau is not on plant_sha {R.B58_PLANT_SHA} (row 102)")
    except (KeyError, TypeError, ValueError) as exc:
        out.append(f"the roads record holds no B58 tau or H table ({type(exc).__name__}: {exc})")
    return out


def synthetic_roads_record(synthetic_seed, *, n_roads, roads, tau_s, jobs):
    """A SYNTHETIC roads record in the layout the tightenings read: epa_roads.generate(synthetic_seed) (or the
    roads given, for tests), the B58's tau by row 102's definition (roads_ceiling.tau_table; or tau_s given)
    and epa_roads.h_table's H. No replacement loop, no C5, no identity: never a roads record of the test."""
    why = R._seed_problem(synthetic_seed, seed_kind="SYNTHETIC")
    if why:
        raise Refused([why])
    if roads is None:
        roads = R.generate(synthetic_seed, n_roads=n_roads)
        for r in roads:
            r["label"] = f"SYNTHETIC road {r['k']} (seed {synthetic_seed}, not roads_seed)"
    cell = None
    if tau_s is None:
        tau_s, cell = RC.tau_table([PLANT], variant=("frozen",), jobs=jobs)[PLANT]
    ident = VE.b58_identity()
    tau = {PLANT: {"tau_s": float(tau_s), "cell": R.jsonable(cell), "plant_sha": ident["plant_sha"],
                   "engine_sha": ident["engine_sha"],
                   "definition": "row 102: epa_coefficients.housing at epa_coefficients.climb_cell (roads_ceiling)"
                                 if cell is not None else "given (a test), not computed"}}
    return {"schema": R.ROADS_SCHEMA, "seed_kind": "SYNTHETIC", "design": R.design(), "streams": R.streams(),
            "engines": [PLANT], "ratios": list(RATIOS), "roads": roads,
            "commit_reveal": {"SYNTHETIC": True, "roads_seed": int(synthetic_seed)},
            "tau": tau, "H_table": R.h_table({PLANT: float(tau_s)}, RATIOS, dt=R.DT),
            "note": "built by epa_tightenings for a SYNTHETIC run: no replacement loop, no C5, no identity; "
                    "not a roads record of the test"}


# =====================================================================================================
# L1 (row 104)
# =====================================================================================================
def rescored(run, *, cal, shift_k, reading, dt):
    """A run's damage re-scored at the knee cal.turb_knee_k + shift_k, with or without the knock term, from
    its per-step housing, oil and knock integral (roads_ceiling.damage_split, checked against
    engine_env.damage_rate at every step)."""
    c = dataclasses.replace(cal, turb_knee_k=float(cal.turb_knee_k) + float(shift_k))
    turb, oil, knock = RC.damage_split(run["t_turb"], run["t_oil"], run["ki"], cal=c, dt=dt)
    return float((turb + oil + knock).sum() if reading == "knock" else (turb + oil).sum())


def evaluate_pair(D_ref, D_var, D_base):
    """The pair var minus ref in points, in evaluate.py's form: roads_ceiling.aggregate's evaluate_form,
    100 (median D_ref - median D_var) / median D_base."""
    return float(RC.aggregate(D_ref, D_var, D_base, neutral=D_base)["evaluate_form"])


def slope_rule(pairs, *, shifts):
    """Row 104's slope: at every nonzero shift s, |pair(s) - pair(0)| / |s| (thresholds/knee_shift.py:56-60),
    for every H and both readings of `pairs` ({H label: {reading: {shift: pair in points}}}). Returns (every
    slope, the largest: the first in the order H, reading, shift on a tie)."""
    every = []
    for h, by_reading in pairs.items():
        for reading in READINGS:
            p = by_reading[reading]
            for s in shifts:
                if s == 0.0:
                    continue
                every.append({"H": h, "reading": reading, "shift_k": float(s), "pair_points": float(p[s]),
                              "pair_at_0_points": float(p[0.0]), "slope_points_per_K": abs(p[s] - p[0.0]) / abs(s)})
    if not every:
        raise ValueError("slope_rule: no nonzero shift")
    best = every[0]
    for x in every[1:]:
        if x["slope_points_per_K"] > best["slope_points_per_K"]:
            best = x
    return every, best


def l1_block(runs, roads, *, H, roads_ref):
    """L1 from the runs {(road index, policy): run with per-step arrays}: the per-road damages at every shift
    and reading, the pairs, every slope and the record's four keys."""
    cal = _b58().engine.damage
    pols = list(L1_POLICIES) + [f"pred@{h}" for h in H]
    D = {p: {rd: {s: [] for s in SHIFTS_K} for rd in READINGS} for p in pols}
    worst = 0.0
    for i, road in enumerate(roads):
        dt = float(road["dt"])
        for p in pols:
            run = runs[(i, p)]
            for rd in READINGS:
                for s in SHIFTS_K:
                    D[p][rd][s].append(rescored(run, cal=cal, shift_k=s, reading=rd, dt=dt))
                own = run["D_knock"] if rd == "knock" else run["D_noknock"]
                got = D[p][rd][0.0][-1]
                worst = max(worst, abs(got - own) / abs(own) if own else abs(got))
    if worst > RESCORE_TOL:
        raise TighteningsDefect(f"L1: the re-score at 0 K does not give back the runs' damage (worst relative "
                                f"{worst:.2e} > {RESCORE_TOL:g}): a coding defect")
    pairs = {h: {rd: {s: evaluate_pair(D["cg"][rd][s], D[f"pred@{h}"][rd][s], D["neutral"][rd][s])
                      for s in SHIFTS_K} for rd in READINGS} for h in H}
    every, best = slope_rule(pairs, shifts=SHIFTS_K)
    h = best["H"]
    set_text = (f"{roads_ref}: the {len(roads)} roads as first drawn, road k with evaluate.EPISODES[k]'s seed and "
                f"weights; the hand-written preview pair (S2a's predictive policy at H {H[h]:.2f} s, r = {h} x the "
                f"B58's tau, minus current-grade) in evaluate.py's form, re-scored at the B58's knee shifted over "
                f"thresholds/knee_shift.py's grid")
    sk = lambda s: f"{s:+g}"      # noqa: E731
    return {
        "slope_points_per_K": float(best["slope_points_per_K"]), "set": set_text, "shift_k": float(best["shift_k"]),
        "damage_reading": READING_TEXT[best["reading"]],
        "H": h, "H_s": H[h], "reading": best["reading"],
        "rule": ("row 104: the largest |pair(s) - pair(0)| / |s| over both H, every shift of knee_shift.SHIFTS and "
                 "both readings, the first in the order H, reading, shift on a tie"),
        "knee_k": float(cal.turb_knee_k), "shifts_k": list(SHIFTS_K), "horizons_s": dict(H),
        "rescore_worst_relative": worst,
        "pairs_points": {hh: {rd: {sk(s): v for s, v in by.items()} for rd, by in x.items()} for hh, x in pairs.items()},
        "slopes": every,
        "per_road_damage": {p: {rd: {sk(s): v for s, v in by.items()} for rd, by in x.items()} for p, x in D.items()},
        "peak_turb_k": {p: [runs[(i, p)]["peak_turb_k"] for i in range(len(roads))] for p in pols},
    }


# =====================================================================================================
# E8 (row 104)
# =====================================================================================================
def _name_of(ds, dl):
    for mode, name, a, b in ECU.RUNS:
        if mode == "k3" and (a, b) == (ds, dl):
            return name
    return f"spark{ds:+g}" if ds else f"lam{dl:+g}"


def e8_shifts(strategy):
    """The runs of the contract's grid ([(name, dspark, dlambda)], the nominal first): every shift of
    k3_pair_change_vs_lambda and _vs_spark, named as thresholds/ecu_shift.py names its k3 runs."""
    lam = [float(s) for s, _ in strategy[GRID_KEYS["lambda"]]]
    spk = [float(s) for s, _ in strategy[GRID_KEYS["spark"]]]
    if 0.0 not in lam or 0.0 not in spk:
        raise Refused(["the contract's E8 grids carry no shift of 0 (ecu_strategy_b58)"])
    out = [("nominal", 0.0, 0.0)]
    out += [(_name_of(0.0, dl), 0.0, dl) for dl in lam if dl != 0.0]
    out += [(_name_of(ds, 0.0), ds, 0.0) for ds in spk if ds != 0.0]
    if len({n for n, _, _ in out}) != len(out):
        raise Refused(["two of the contract's E8 shifts share a name"])
    return out


def e8_block(runs, knees, shifts, roads, *, strategy, above0, pinned):
    """E8 from the runs {(shift name, road index, policy): run} and the knees {name: k3 record}: the medians
    over the roads, the pair per shift and reading, and the two tables by thresholds.contract.response. Each
    shift also records on how many roads reactive's damage equals neutral's bit for bit (the reactive policy
    never acted, so the head-start pair there is current-grade's cut alone) and the neutral peak housing minus
    that shift's knee, values only (a review of 31 October; no rule reads them)."""
    table, per = {}, {}
    n = len(roads)
    for name, ds, dl in shifts:
        D = {pol: {rd: [runs[(name, i, pol)]["D_" + rd] for i in range(n)] for rd in READINGS}
             for pol in E8_POLICIES}
        med = {CONTRACT_KEY[rd]: {E8_POLICIES[pol]: float(np.median(D[pol][rd])) for pol in E8_POLICIES}
               for rd in READINGS}
        table[name] = dict(dlambda=dl, dspark=ds, **med)
        kn = knees[name]
        pin = (pinned or {}).get("knees", {}).get(name)
        per[name] = {"dspark": ds, "dlambda": dl, "knee_k": kn["knee_k"], "knee_shift_k": kn["knee_k"] - kn["k0"],
                     "k3_seconds": kn.get("seconds"),
                     "time_above_knee_s": kn.get("time_above_knee_s"), "second_knee_identical": kn.get("second_knee_identical"),
                     "trace_sha256": kn.get("trace_sha256"), "pinned_knee_k": pin,
                     "knee_equals_pinned": None if pin is None else kn["knee_k"] == pin,
                     "medians": med, "pair_points": {rd: 100.0 * TC.pair(table[name], CONTRACT_KEY[rd]) for rd in READINGS},
                     "reactive_identical_to_neutral_roads": {
                         rd: int(sum(a == b for a, b in zip(D["reactive"][rd], D["neutral"][rd]))) for rd in READINGS},
                     "neutral_peak_minus_knee_k": [float(runs[(name, i, "neutral")]["peak_turb_k"]) - float(kn["knee_k"])
                                                   for i in range(n)],
                     "per_road_damage": D}
    for rd in READINGS:
        if TC.pair(table["nominal"], CONTRACT_KEY[rd]) == 0.0:
            raise Refused([f"E8: the nominal head-start pair is 0 in the {rd} reading, so its relative change is "
                           "undefined (row 104's scratch check)"])
    out = {}
    for lever in ("lambda", "spark"):
        got = [[float(s), float(c)] for s, c in TC.response(table, lever)]
        want = [float(s) for s, _ in strategy[GRID_KEYS[lever]]]
        if [s for s, _ in got] != want:
            raise TighteningsDefect(f"E8: the {lever} table's shifts {[s for s, _ in got]} are not the contract's {want}")
        out[ROADS_KEYS[lever]] = got
    out.update({
        "rule": ("row 104: each shift of the contract's grid its own run on the roads, through k3_knee.shifted_ecu, k3 "
                 "and with_knee; the K3 knee re-set as thresholds/ecu_shift.py sets it, on the locked climb; the relative "
                 "change of the head-start pair (current-grade minus reactive) in evaluate.py's form, both readings, the "
                 "larger |change| with its sign (thresholds.contract.response)"),
        "time_above_nominal_s": above0["time_above_nominal_s"], "above0_measured": above0.get("measured", True),
        "pinned_time_above_nominal_s": (pinned or {}).get("time_above_nominal_s"),
        "knees_equal_pinned": all(v["knee_equals_pinned"] for v in per.values() if v["knee_equals_pinned"] is not None)
        if any(v["knee_equals_pinned"] is not None for v in per.values()) else None,
        "nominal_pair_points": per["nominal"]["pair_points"],
        "reactive_identical_to_neutral": {
            "roads": {rd: int(sum(v["reactive_identical_to_neutral_roads"][rd] for v in per.values())) for rd in READINGS},
            "of": n * len(per),
            "reading": ("the (shift, road) runs on which reactive's damage equals neutral's bit for bit: there the "
                        "head-start pair is current-grade's cut alone (values only; no rule reads them)")},
        "shifts": per,
    })
    return out


# =====================================================================================================
# The B58's E8 band (row 107 (4))
# =====================================================================================================
def spark_inputs(*, root):
    """Row 107 (4)'s inputs from results/car_spark_boost.json: car_spark_boost.summary of its readings, the
    model spark recomputed by car_spark_boost.model_spark on the B58 as built. Row 107 (4)'s condition is that
    the 31 readings' standard error is reproduced from the tree: the "all" cell's count of readings and its
    diff_se must come back as printed, and then u is that standard error; otherwise u is None (row 107 (4):
    missing). The shift ends are the two cells' printed medians. Whether every other field of both cells comes
    back too is recorded beside it (reproduced_cells_all_fields) and changes nothing."""
    import pandas as pd
    import car_spark_boost as CSB
    path = os.path.join(root, *SPARK_RECORD_REL.split("/"))
    rec = common.load_json(path)
    r = pd.DataFrame(rec["readings"])
    r["model"] = CSB.model_spark(r)
    climb = r[r.rpm.between(*CSB.CLIMB["rpm"]) & r.map_kpa.between(*CSB.CLIMB["map"])]
    got = {SPARK_CELL_ALL: CSB.summary(r), SPARK_CELL_CLIMB: CSB.summary(climb)}
    printed = {c: rec["cells"][c] for c in got}
    g, p = got[SPARK_CELL_ALL], printed[SPARK_CELL_ALL]
    se_back = bool(g["readings"] == p["readings"] and g["diff_se"] == p["diff_se"])
    every = bool(all(got[c] == printed[c] for c in got))
    return {"source": SPARK_RECORD_REL, "sha_text": common.sha_text(path), "reproduced": se_back,
            "reproduced_what": (f"the {SPARK_CELL_ALL!r} cell's readings and diff_se (row 107 (4): the 31 "
                                "readings' standard error)"),
            "reproduced_cells_all_fields": every,
            "how": ("car_spark_boost.summary over the record's readings, the model spark recomputed by "
                    "car_spark_boost.model_spark on the B58 as built"),
            "reproduced_cells": R.jsonable(got), "printed_cells": printed,
            "ends_deg": [float(p["diff_median"]), float(printed[SPARK_CELL_CLIMB]["diff_median"])],
            "u_deg": float(p["diff_se"]) if se_back else None,
            "sign": "car minus model: the ECU shift that moves the model's spark to the car's (row 107 (4))"}


OFF_NOTE = ("the B58's E8 line reads off (|E| - 2u_val > R): row 107 (4) expects untested, and row 107 (3) defines "
            "no kappa for an off row, so kappa is None; the team's call before section 7 is recorded")
NO_U_STAT = ("no row defines a u_stat for the B58's spark-under-boost reading: labelled with u_stat None, which "
             "certifies nothing (epa_stats.line_label), so the row reads untested, as row 107 (4) writes it, or off")


def _band_of(ps, *, r_pct, ends, u_deg):
    """Row 107 (4) on one P_spark table: E at the end of `ends` where |P| is larger, u_val = u_deg through P's
    local slope there, the line labelled with u_stat None, kappa by row 107 (3)."""
    ev = []
    for ds in ends:
        P = float(TC.interp(ps, ds))
        ev.append({"ds_deg": float(ds), "P": P, "extrapolated": bool(ds < ps[0][0] or ds > ps[-1][0]),
                   "slope_per_deg": float(ES.p_slope(ps, ds))})
    pick = ev[0]
    for x in ev[1:]:
        if abs(x["P"]) > abs(pick["P"]):
            pick = x
    E = 100.0 * abs(pick["P"])
    out = {"P_spark": [[float(a), float(b)] for a, b in ps], "ends": ev, "E_pct": E, "E_from_ds_deg": pick["ds_deg"],
           "R_pct": float(r_pct), "u_ds_deg": u_deg, "u_stat_pct": None, "u_stat_note": NO_U_STAT}
    floor = 1.0 + E / r_pct
    if u_deg is None:
        out.update(u_val_pct=None, two_u_val_pct=None, label="untested", line_label=None, certifies=None,
                   kappa_formula=None, kappa=floor, floor_binds=True,
                   note="u_val missing (the 31 readings' standard error is not reproduced): kappa is row 107 (3)'s floor")
        return out
    u = 100.0 * float(u_deg) * abs(pick["slope_per_deg"])
    lab, cert = ES.line_label(E, u, None, r_pct)
    row = ES.row_label([types.SimpleNamespace(label=lab, certifies=cert)])
    if cert or row not in ("untested", "off"):
        raise TighteningsDefect(f"the B58's E8 band certified a line without a u_stat ({lab}, {row}): a coding defect")
    formula = ES.kappa(E, u, r_pct, row)
    out.update(u_val_pct=u, two_u_val_pct=2.0 * u, label=row, line_label=lab, certifies=cert, kappa_formula=formula)
    if row == "untested":
        out.update(kappa=max(floor, formula), floor_binds=bool(floor > formula))
    else:
        out.update(kappa=None, floor_binds=None, kappa_undefined=True, note=OFF_NOTE)
    return out


def b58_band(tables, *, strategy, r_pct, spark):
    """Row 107 (4): the B58's E8 u_val and kappa, on P the larger of the locked-climb and the roads responses
    (epa_stats.e8_response), with the locked-climb-only reading beside it. Beside both, the same readings at
    the ends' opposite sign, model minus car, the sign of E8's own statistic (epa_stats._core_E8 evaluates P
    at model minus EPA), labelled descriptive: no row reconciles the two signs, and row 107 (4)'s is primary."""
    view = types.SimpleNamespace(ecu_strategy_b58=strategy)
    tight = {"plant": PLANT, "E8": tables}
    _, ps = ES.e8_response(view, tightening=tight)
    _, ps0 = ES.e8_response(view, tightening=None)
    kw = dict(r_pct=r_pct, ends=spark["ends_deg"], u_deg=spark["u_deg"])
    neg = dict(kw, ends=[-float(x) for x in spark["ends_deg"]])
    desc = ("descriptive: the ends at model minus car, the sign of E8's own statistic (epa_stats._core_E8); "
            "row 107 (4) writes car minus model, the primary reading")
    return {"rule": ("row 107 (4): E = |P_spark| at the larger end of the B58's spark-under-boost reading, u_val its "
                     "standard error through P's local slope (MD:1020-1023), P the larger of the locked-climb and the roads "
                     "responses (MD:1026-1028); kappa by row 107 (3)"),
            "spark_inputs": spark, "with_roads": _band_of(ps, **kw), "locked_climb_only": _band_of(ps0, **kw),
            "model_minus_car": {"reading": desc, "with_roads": _band_of(ps, **neg),
                                "locked_climb_only": _band_of(ps0, **neg)}}


# =====================================================================================================
# The computation
# =====================================================================================================
def compute(record, *, roads_ref, strategy, r_e8_pct, spark, pinned, seconds, jobs, log, pinned_strict=False):
    """The tightenings on a roads record (roads_problems must be [] for its kind; the caller checks): every run,
    then L1, E8 and the B58's band. `strategy` is the contract's ecu_strategy_b58, r_e8_pct E8's R, `spark`
    spark_inputs' result, `pinned` pinned_k3's (or None), `seconds` None to measure ecu_shift's above0 (the
    real run) or an int. pinned_strict (the real run): the measured above0 must be the pinned
    time_above_nominal_s, and each K3 knee the pinned one bit for bit, each checked as its task ends, before the
    road runs it sets are queued (TighteningsDefect otherwise). Returns (L1, E8, the timing, the files opened)."""
    if pinned_strict and (pinned is None or seconds is not None):
        raise ValueError("compute: pinned_strict needs the pinned record and above0 measured (seconds None)")
    roads = record["roads"]
    H = horizons(record)
    plant = _b58()
    k0 = float(plant.engine.damage.turb_knee_k)
    shifts = e8_shifts(strategy)
    by_name = {n: (ds, dl) for n, ds, dl in shifts}
    initial = []
    for i, road in enumerate(roads):
        for p in L1_POLICIES:
            initial.append((("l1", i, p), road_task(road, policy=(p,), knee_k=k0, ds=0.0, dl=0.0, shifted=False,
                                                    per_step=True)))
        for h, H_s in H.items():
            initial.append((("l1", i, f"pred@{h}"), road_task(road, policy=("pred", H_s), knee_k=k0, ds=0.0, dl=0.0,
                                                              shifted=False, per_step=True)))
        for pol in E8_POLICIES:
            initial.append((("e8", "nominal", i, pol), road_task(road, policy=(pol,), knee_k=k0, ds=0.0, dl=0.0,
                                                                 shifted=True, per_step=False)))

    def k3_tasks(sec):
        return [(("k3", n), {"kind": "k3", "ds": ds, "dl": dl, "seconds": int(sec)})
                for n, ds, dl in shifts if n != "nominal"]
    if seconds is None:
        initial.insert(0, (("above0",), {"kind": "above0"}))
    else:
        initial = k3_tasks(seconds) + initial

    def on_done(key, res):
        if key[0] == "above0":
            if pinned_strict and res["time_above_nominal_s"] != pinned["time_above_nominal_s"]:
                raise TighteningsDefect(
                    f"E8: the nominal trace spends {res['time_above_nominal_s']} s above the knee, not k3_nominal.json's "
                    f"{pinned['time_above_nominal_s']}: the knee is not re-set as thresholds/ecu_shift.py set it")
            return k3_tasks(res["time_above_nominal_s"])
        if key[0] == "k3":
            if res["second_knee_identical"] is not True:
                raise TighteningsDefect(f"E8 {key[1]}: the second provisional knee moved the locked-climb trace "
                                        "(k3_knee.k3), a coding defect")
            if pinned_strict and res["knee_k"] != pinned["knees"].get(key[1]):
                raise TighteningsDefect(f"E8 {key[1]}: the K3 knee {res['knee_k']!r} is not k3_{key[1]}.json's "
                                        f"{pinned['knees'].get(key[1])!r}: the knee is not re-set as "
                                        "thresholds/ecu_shift.py set it")
            ds, dl = by_name[key[1]]
            return [(("e8", key[1], i, pol), road_task(road, policy=(pol,), knee_k=res["knee_k"], ds=ds, dl=dl,
                                                       shifted=True, per_step=False))
                    for i, road in enumerate(roads) for pol in E8_POLICIES]
        return []

    log(f"{len(roads)} roads, H {H}, {len(shifts)} E8 runs of the grid; {len(initial)} tasks to start, at {jobs} jobs")
    t0 = time.perf_counter()
    res = schedule(initial, on_done, jobs=jobs, log=log)
    wall = time.perf_counter() - t0
    opened = sorted(set().union(*(set(v.pop("opened")) for v in res.values())) | R.OPENED)
    above0 = res[("above0",)] if seconds is None else {"time_above_nominal_s": int(seconds), "measured": False}
    knees = {"nominal": {"knee_k": k0, "k0": k0, "time_above_knee_s": None, "second_knee_identical": None}}
    for n, _, _ in shifts:
        if n != "nominal":
            knees[n] = dict(res[("k3", n)], k0=k0)
    l1 = l1_block({(k[1], k[2]): v for k, v in res.items() if k[0] == "l1"}, roads, H=H, roads_ref=roads_ref)
    e8 = e8_block({(k[1], k[2], k[3]): v for k, v in res.items() if k[0] == "e8"}, knees, shifts, roads,
                  strategy=strategy, above0=above0, pinned=pinned)
    e8["b58_u_val_kappa"] = b58_band({ROADS_KEYS[x]: e8[ROADS_KEYS[x]] for x in ROADS_KEYS}, strategy=strategy,
                                     r_pct=r_e8_pct, spark=spark)
    timing = timing_of(res, wall=wall, jobs=jobs, n_roads=len(roads), n_shifts=len(shifts))
    return l1, e8, timing, opened


def timing_of(res, *, wall, jobs, n_roads, n_shifts):
    """Each kind's measured seconds (road runs per step), the wall time, and the real run's predicted wall
    time at these jobs: 20 roads x (4 + 3 x 15) road runs of 899 steps, one above0 and 14 k3 tasks, divided by
    the jobs (ASSUMED: the load this run measured is the real run's)."""
    road = [v for k, v in res.items() if k[0] in ("l1", "e8")]
    sps = [v["task_s"] / v["steps"] for v in road]
    k3s = [v["task_s"] for k, v in res.items() if k[0] == "k3"]
    a0 = [v["task_s"] for k, v in res.items() if k[0] == "above0"]
    n_real_road = REAL_ROADS * (len(L1_POLICIES) + len(RATIOS) + len(E8_POLICIES) * n_shifts)
    pred = None
    if sps and k3s:
        work = (n_real_road * float(np.median(sps)) * REAL_EPISODE_STEPS + (n_shifts - 1) * float(np.median(k3s))
                + (float(np.median(a0)) if a0 else float(np.median(k3s)) / 2.0))
        pred = work / max(int(jobs), 1)
    return {"jobs": int(jobs), "wall_s": float(wall), "cpu_count": os.cpu_count(),
            "python_processes": RC._python_processes(),
            "tasks": {"road": len(road), "k3": len(k3s), "above0": len(a0)},
            "road_s_per_step": None if not sps else {"min": min(sps), "median": float(np.median(sps)), "max": max(sps)},
            "k3_s": None if not k3s else {"min": min(k3s), "median": float(np.median(k3s)), "max": max(k3s)},
            "above0_s": a0[0] if a0 else None,
            "real_run": {"roads": REAL_ROADS, "road_runs": n_real_road, "episode_steps": REAL_EPISODE_STEPS,
                         "k3_tasks": n_shifts - 1, "above0_tasks": 1, "predicted_wall_s": pred,
                         "assumed": "the per-task seconds measured here, at these jobs and this load, divided by the jobs"}}


# =====================================================================================================
# The gates, the provenance and the writer (rows 97, 104, 121; tit_cap.py's and epa_roads' gates)
# =====================================================================================================
def code_files(*, root):
    """The code the record's code_sha_text covers (DESIGN): this module's import closure (the roads module's
    among it), epa_freeze.CODE_HASHED (what arm hashes) and the B58's plant files."""
    return sorted(set(R.import_closure(MODULE_REL, root=root)) | set(epa_freeze.CODE_HASHED)
                  | set(FP.plant_files(PLANT)))


def work_tree_of(path):
    """The top level of the git work tree holding `path`, or None: git rev-parse --show-toplevel in its nearest
    existing folder (as tit_cap.work_tree_of)."""
    d = os.path.abspath(path)
    while not os.path.isdir(d):
        up = os.path.dirname(d)
        if up == d:
            return None
        d = up
    r = subprocess.run(["git", "-C", d, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    top = r.stdout.strip()
    return os.path.normcase(os.path.abspath(top)) if r.returncode == 0 and top else None


def outside_work_trees(path):
    return work_tree_of(path) is None


def bytecode_caches(files, *, root):
    """Every compiled file Python could load in place of a code file's source: __pycache__/<stem>.*.pyc beside
    each .py of `files`, repository-relative. python -B stops Python writing these, not reading them, and a
    gitignored cache is invisible to git_clean (a review of 31 October found three at this tree's root)."""
    out = []
    for f in files:
        if not f.endswith(".py"):
            continue
        d, name = os.path.split(os.path.join(root, *f.split("/")))
        cache = os.path.join(d, "__pycache__")
        if not os.path.isdir(cache):
            continue
        stem = name[:-3] + "."
        out += [os.path.relpath(os.path.join(cache, c), root).replace(os.sep, "/") for c in sorted(os.listdir(cache))
                if c.startswith(stem) and c.endswith(".pyc")]
    return sorted(out)


def git_state(*, root):
    """The commit, whether the code, the data inputs and the whole tree are committed and clean
    (epa_freeze.git_clean), and the compiled files beside the code."""
    files = code_files(root=root)
    code_clean, code_dirty = epa_freeze.git_clean(files, root=root)
    data_clean, data_dirty = epa_freeze.git_clean(DATA_INPUTS, root=root)
    tree_clean, tree_dirty = epa_freeze.git_clean((".",), root=root)
    return {"commit": epa_freeze.git_head(root=root), "code_clean": code_clean, "code_dirty": list(code_dirty),
            "data_inputs_clean": data_clean, "data_inputs_dirty": list(data_dirty),
            "bytecode_caches": bytecode_caches(files, root=root),
            "tree_clean": tree_clean, "tree_dirty": list(tree_dirty)}


def provenance(*, root):
    """The record's provenance: the commit, code_sha_text over code_files, and the B58's plant_sha and
    engine_sha as validate_epa's arm builds them (b58_identity), with the versions and the git state."""
    files = code_files(root=root)
    return {"commit": epa_freeze.git_head(root=root), "code_sha_text": R.sha_texts(files, root=root),
            **VE.b58_identity(), "versions": epa_freeze.versions(), "git": git_state(root=root)}


def real_problems(*, root):
    """Why the real tightenings may not run or be written, [] when they may (rows 97, 104; ORDER step 8):
    results/EPA_TIGHTENINGS.json absent and never committed; this tree's code committed and clean, with no
    compiled file beside it; the data inputs (DATA_INPUTS: the contract, results/car_spark_boost.json and the
    pinned K3 folder) committed and clean; every output of the roads step (results/EPA_ROADS/) committed and
    clean (those four: shared_gates, the no-roads route's too); roads.json committed at HEAD, the record its
    attempts log's one "roads" outcome names by roads_sha, its roads_seed the reveal's and its hash lines the
    roads commit's, the tightenings' roads (roads_problems), and every file, plant and version it hashes as it
    recorded (epa_roads.verify_record); the B58 as built on row 102's plant (b58_problems).
    Returns (problems, the roads record or None, its roads_sha or None)."""
    out = shared_gates(root=root)
    path = os.path.join(root, *R.ROADS_REL.split("/"))
    if not os.path.isfile(path):
        return out + [f"{R.ROADS_REL} is absent: the roads come first (ORDER step 6)"], None, None
    if not epa_freeze.committed_at_head(R.ROADS_REL, root=root):
        out.append(f"{R.ROADS_REL} is not committed at HEAD")
    sha = R.roads_sha(path)
    rec = common.load_json(path)
    outs = [x for x in R.read_attempts(os.path.join(root, *R.ATTEMPTS_REL.split("/")))
            if x.get("step", "draw") == "draw" and x.get("event") == "outcome" and x.get("outcome") == "roads"]
    if len(outs) != 1 or outs[0].get("roads_sha") != sha:
        out.append(f"the attempts log does not name this roads.json's roads_sha {sha} in its one roads outcome")
    try:
        cr = rec["commit_reveal"]
        if cr["roads_seed"] != R.roads_seed_from(cr["reveal"]["ghassan"], cr["reveal"]["jad"], cr["roads_commit"]):
            out.append("roads.json's roads_seed is not the one the reveal gives (row 96)")
        if not (R.reveal_matches(cr["reveal"]["ghassan"], cr["hash_lines"]["ghassan"])
                and R.reveal_matches(cr["reveal"]["jad"], cr["hash_lines"]["jad"])):
            out.append("roads.json's reveals do not match its hash lines (row 96)")
        commit, g, j = R.find_roads_commit(root=root)
        if (cr["roads_commit"], cr["hash_lines"]["ghassan"], cr["hash_lines"]["jad"]) != (commit, g, j):
            out.append("roads.json's roads commit or hash lines are not the ones HEAD's history holds (row 96)")
    except (KeyError, TypeError, ValueError, R.Refused) as exc:
        out.append(f"roads.json's commit and reveal cannot be checked ({type(exc).__name__}: {exc})")
    out += roads_problems(rec, kind="REAL")
    try:
        out += [f"roads.json: {p}" for p in R.verify_record(rec, root=root)]
    except (KeyError, TypeError, R.Refused) as exc:
        out.append(f"roads.json's hashes cannot be verified ({type(exc).__name__}: {exc})")
    out += b58_problems()
    return out, rec, sha


def b58_problems():
    """The B58 as built (validate_epa.b58_identity) on the plant row 102 names, R.B58_PLANT_SHA; [] when it is."""
    ident = VE.b58_identity()
    if ident["plant_sha"] != R.B58_PLANT_SHA:
        return [f"the B58 as built is plant_sha {ident['plant_sha']}, not {R.B58_PLANT_SHA} (row 102)"]
    return []


def shared_gates(*, root):
    """The gates both routes take before anything is computed, [] when all hold (rows 97, 104, 129 (4)):
    results/EPA_TIGHTENINGS.json absent and never committed; the code committed and clean, with no compiled file
    beside it; the data inputs (DATA_INPUTS) committed and clean; every output of the roads step
    (results/EPA_ROADS/) committed and clean."""
    out = []
    if os.path.exists(os.path.join(root, *OUT_REL.split("/"))):
        out.append(f"{OUT_REL} exists: it is written once")
    if R.committed_versions(root, OUT_REL):
        out.append(f"{OUT_REL} was committed in HEAD's history: the tightenings are measured once")
    files = code_files(root=root)
    clean, dirty = epa_freeze.git_clean(files, root=root)
    if not clean:
        out.append("the code is not committed and clean: " + ", ".join(dirty))
    pyc = bytecode_caches(files, root=root)
    if pyc:
        out.append("compiled files stand beside the code, and Python would load them in place of the committed "
                   "source (delete every __pycache__ and run with python -B): " + ", ".join(pyc))
    clean, dirty = epa_freeze.git_clean(DATA_INPUTS, root=root)
    if not clean:
        out.append("the run's data inputs are not committed and clean: " + ", ".join(dirty))
    clean, dirty = epa_freeze.git_clean((R.ROADS_DIR_REL,), root=root)
    if not clean:
        out.append(f"{R.ROADS_DIR_REL}/ is not committed and clean (every output of the roads step comes first): "
                   + ", ".join(dirty))
    return out


def start_line_problems(start, *, commit, h_g, h_j):
    """Why a draw start line is not one epa_roads.draw writes (epa_roads.py:1586-1595), [] when it is: each logged
    reveal parse_reveal's int of at least 2**128 (epa_roads._private_int_ok; a decimal string, a null or a missing
    reveal is not), the logged reveal_matches the one draw computes from them (epa_roads.reveal_matches against
    the roads commit's hash lines, checked again here), and the hash lines and the roads commit those HEAD's
    history holds (epa_roads.find_roads_commit). No reveal is printed. Returns (problems, the re-check)."""
    n = start.get("attempt")
    rev = start.get("reveal") if isinstance(start.get("reveal"), dict) else {}
    out = [f"attempt {n!r}'s start line logs {who}'s reveal as a {type(rev.get(who)).__name__}, not an int of at least "
           "2**128: draw logs parse_reveal's integer (epa_roads.py:1565, :1590)" for who in ("ghassan", "jad")
           if not R._private_int_ok(rev.get(who))]
    recheck = {"ghassan": R.reveal_matches(rev.get("ghassan"), h_g), "jad": R.reveal_matches(rev.get("jad"), h_j)}
    if start.get("reveal_matches") != recheck:
        out.append(f"attempt {n!r}'s logged reveal_matches {start.get('reveal_matches')!r} is not {recheck}, the logged "
                   "reveals checked again against the roads commit's hash lines: draw logs the match it computed "
                   "(epa_roads.py:1586, :1591)")
    if start.get("hash_lines") != {"ghassan": h_g, "jad": h_j}:
        out.append(f"attempt {n!r}'s logged hash lines are not the roads commit's (row 96)")
    if start.get("roads_commit") != commit:
        out.append(f"attempt {n!r}'s start line names the roads commit {start.get('roads_commit')!r}, not {commit}, the "
                   "one HEAD's history holds (row 96)")
    return out, recheck


def no_roads_problems(*, root):
    """Row 129 (4)'s case read off the committed roads step, [] when it holds: roads.json absent and never committed
    in HEAD's history (no set was drawn, row 103 (3)); the attempts log committed at HEAD and never rewritten
    (epa_roads.attempts_log_problems); its draw lines hold no roads outcome and end in exactly one stop that is not
    a coding defect (outcome "stop", coding_defect false), right after its own attempt's start line (draw appends
    it there, epa_roads.py:1596-1599); the start lines numbered 1, 2, ... in order (draw numbers each attempt one
    more than the start lines before it, epa_roads._step_rules), each one draw writes (start_line_problems: the
    roads commit and hash lines HEAD's history holds, epa_roads.find_roads_commit; two ints of at least 2**128;
    the reveal_matches they give); and the stopped attempt's logged reveals, checked again against that commit's
    hash lines (epa_roads.reveal_matches), do not both match: the log's own verdict is not taken. An earlier
    attempt whose reveals both match is named, not refused (row 129 (4)'s disclosure: after the reveal either
    person could force a stop). Returns (problems, what was found: the stop line, its attempt and start commit, the
    roads commit, the reveal_matches logged and re-checked, the earlier attempts whose reveals both match; each None
    where not found)."""
    out = []
    found = {"stop": None, "attempt": None, "start_commit": None, "roads_commit": None,
             "reveal_matches_logged": None, "reveal_matches_rechecked": None, "earlier_attempts_both_matching": None}
    if os.path.exists(os.path.join(root, *R.ROADS_REL.split("/"))):
        out.append(f"{R.ROADS_REL} exists: a road set was drawn, and the tightenings are measured on it (`run`)")
    if R.committed_versions(root, R.ROADS_REL):
        out.append(f"{R.ROADS_REL} was committed in HEAD's history: a road set was drawn (row 103 (3))")
    if not epa_freeze.committed_at_head(R.ATTEMPTS_REL, root=root):
        out.append(f"{R.ATTEMPTS_REL} is not committed at HEAD: the stop is committed before the record (row 96)")
    out += R.attempts_log_problems(root=root)[0]
    lines = R._draw_entries(R.read_attempts(os.path.join(root, *R.ATTEMPTS_REL.split("/"))))
    if any(x.get("event") == "outcome" and x.get("outcome") == "roads" for x in lines):
        out.append("the attempts log holds a roads outcome: a road set was drawn (row 103 (3))")
    stops = [x for x in lines if x.get("event") == "outcome" and x.get("outcome") == "stop"
             and x.get("coding_defect") is False]
    if len(stops) != 1 or lines[-1] is not stops[0]:
        out.append(f"the attempts log's draw lines do not end in exactly one stop that is not a coding defect "
                   f"({len(stops)} such stops; the last draw line: "
                   f"{(lines[-1].get('event'), lines[-1].get('outcome')) if lines else None}) (row 129 (4))")
        return out, found
    stop = stops[0]
    found.update(stop=stop, attempt=stop.get("attempt"))
    start = lines[-2] if len(lines) >= 2 else {}
    if start.get("event") != "start" or start.get("attempt") != stop.get("attempt"):
        out.append(f"the stop of attempt {stop.get('attempt')!r} does not follow its own start line: draw appends it "
                   "right after that line (epa_roads.py:1596-1599)")
        return out, found
    starts = [x for x in lines if x.get("event") == "start"]
    numbers = [x.get("attempt") for x in starts]
    if numbers != list(range(1, len(starts) + 1)):
        out.append(f"the draw's start lines are numbered {numbers}, not 1 to {len(starts)} in order: draw numbers each "
                   "attempt one more than the start lines before it (epa_roads._step_rules)")
        return out, found
    try:
        commit, h_g, h_j = R.find_roads_commit(root=root)
    except R.Refused as exc:
        out.append("the roads commit cannot be found: " + "; ".join(exc.args[0]))
        return out, found
    rechecks = {}
    for x in starts:
        probs, rechecks[x["attempt"]] = start_line_problems(x, commit=commit, h_g=h_g, h_j=h_j)
        out += probs
    recheck = rechecks[start["attempt"]]
    found.update(start_commit=start.get("commit"), roads_commit=commit,
                 reveal_matches_logged=start.get("reveal_matches"), reveal_matches_rechecked=recheck,
                 earlier_attempts_both_matching=[n for n, rc in rechecks.items()
                                                 if n != start["attempt"] and all(rc.values())])
    if all(recheck.values()):
        out.append("the stopped attempt's logged reveals both match the roads commit's hash lines: that stop is not "
                   "row 129 (4)'s (a reveal that does not match its hash line)")
    return out, found


def origin_problems(*, root):
    """The shared branch at the write, [] when it holds (row 129 (4)): HEAD is origin's GRA-test as the remote itself
    reports it (epa_roads.remote_state, as draw reads it: git ls-remote, the objects fetched), so the stop is
    committed and pushed and the branch holds nothing this clone has not read. HEAD merely in the branch is not
    enough: a clone left at the roads commit logs a stop of its own (draw's first attempt runs on that commit, which
    the branch always holds), and its commit merged into a branch that holds a drawn set would be in the branch.
    Returns (problems, the branch's sha or None)."""
    head = epa_freeze.git_head(root=root)
    pushed, tip, why = R.remote_state(root, head)
    if not pushed:
        return [f"the shared branch: {why} (row 129 (4): the stop is committed and pushed before the record)"], tip
    if tip != head:
        return [f"the shared branch: {R.REMOTE_NAME}'s {R.REMOTE_BRANCH} is at {tip}, not at HEAD {head}: write the "
                "record on the branch's tip, so that nothing pushed there (a set drawn in another clone among it) is "
                "left unread (row 129 (4))"], tip
    return [], tip


def stopped_problems(*, root):
    """Why `stopped` may not write, [] when it may (row 129 (4)): shared_gates (the record absent and never
    committed; the code, its data inputs and results/EPA_ROADS/ committed and clean, with no compiled file beside
    the code), no_roads_problems (roads.json absent and never committed; the attempts log committed at HEAD,
    append-only, as draw writes it, its draw lines holding no roads outcome and ending in exactly one non-defect
    stop whose reveals, checked again, do not both match), origin_problems (HEAD is origin's GRA-test) and
    b58_problems. Returns (problems, no_roads_problems' findings with the branch's sha beside them)."""
    out = shared_gates(root=root)
    probs, found = no_roads_problems(root=root)
    branch, tip = origin_problems(root=root)
    return (out + probs + branch + b58_problems(),
            dict(found, shared_branch_at_write={"remote": R.REMOTE_NAME, "branch": R.REMOTE_BRANCH, "sha": tip}))


def out_problem(path, *, in_tree_rel):
    """Why `path` may not be written, or None: it exists (written once); or it lies inside a git work tree
    that is not this one, or inside this one but not at `in_tree_rel` (None: nowhere in a tree), or there
    while the code is not committed and clean (as tit_cap.out_problem)."""
    if os.path.exists(path):
        return f"{path} exists: it is written once"
    tree = work_tree_of(path)
    if tree is None:
        return None
    if in_tree_rel is None:
        return f"{path} lies inside the git work tree {tree}: a SYNTHETIC record is written outside every work tree"
    if tree != os.path.normcase(os.path.abspath(REPO)):
        return f"{path} lies inside the work tree {tree}, which is not this code's"
    rel = os.path.relpath(os.path.abspath(path), REPO).replace(os.sep, "/")
    if not (rel == in_tree_rel or rel.startswith(in_tree_rel.rstrip("/") + "/")):
        return f"{rel}: inside the work tree this record goes under {in_tree_rel} only"
    for what, paths in (("code", code_files(root=REPO)), ("data inputs", DATA_INPUTS)):
        clean, dirty = epa_freeze.git_clean(paths, root=REPO)
        if not clean:
            return f"{rel}: a record in the work tree names committed {what}, and {', '.join(dirty)} is not"
    return None


def pinned_k3(*, root):
    """The pinned K3 knees and seconds (results/ENGINE_THRESHOLDS/ecu/k3_*.json under `root`, named as
    thresholds/ecu_shift.py's path names them), read only, and the folder's state before the run."""
    knees, nominal = {}, None
    for mode, name, _ds, _dl in ECU.RUNS:
        if mode != "k3":
            continue
        j = common.load_json(os.path.join(root, *ECU_DIR_REL.split("/"), os.path.basename(ECU.path(mode, name))))
        knees[name] = float(j["knee_k"])
        if name == "nominal":
            nominal = int(j["time_above_nominal_s"])
    return {"knees": knees, "time_above_nominal_s": nominal, "folder": ecu_folder_state(root=root)}


def ecu_folder_state(*, root=REPO):
    """sha256 over results/ENGINE_THRESHOLDS/ecu/'s file names and raw bytes, sorted: what the run must leave."""
    d = os.path.join(root, *ECU_DIR_REL.split("/"))
    h = hashlib.sha256()
    for name in sorted(os.listdir(d)):
        p = os.path.join(d, name)
        if os.path.isfile(p):
            h.update(name.encode("utf-8") + b"\0" + common.sha_raw(p).encode("ascii") + b"\n")
    return h.hexdigest()


def contract_inputs(*, root=REPO):
    """The contract's ecu_strategy_b58, E8's R and knee_shift's largest slope (the basis), read once from the
    tree under `root`."""
    c = common.load_json(os.path.join(root, *CONTRACT_JSON_REL.split("/")))
    r = [x for x in c["rows"] if x.get("id") == "E8"]
    if len(r) != 1:
        raise Refused(["the contract holds no single E8 row"])
    return {"ecu_strategy_b58": c["ecu_strategy_b58"], "r_e8_pct": float(r[0]["R"]),
            "basis": c["knee_shift"]["largest"], "sha_text": {f: common.sha_text(os.path.join(root, *f.split("/")))
                                                              for f in R.CONTRACT_FILES}}


def assemble(*, roads_sha_value, roads_seed, kind, l1, e8, prov, extra):
    rec = {"schema": SCHEMA, "plant": PLANT, "roads_sha": roads_sha_value, "roads_seed": int(roads_seed),
           "L1": l1, "E8": e8, "provenance": prov, "seed_kind": kind}
    rec.update(extra)
    return R.jsonable(rec)


def write_checked(path, record, *, strategy):
    """The record written once, LF and ASCII, indent 1: to a partial file read back by
    validate_epa.load_tightenings and checked by validate_epa.tightening_problems (the contract's grid, the
    B58 as built), then hard-linked into place (it fails if the target appeared meanwhile). Returns its
    sha_text. A refusal removes the partial file and writes nothing."""
    path = os.path.abspath(path)
    if os.path.exists(path):
        raise Refused([f"{path} exists: it is written once"])
    text = json.dumps(record, indent=1, ensure_ascii=True, allow_nan=False) + "\n"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".partial"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    try:
        try:
            t = VE.load_tightenings(tmp)
        except ValueError as exc:
            raise Refused([f"validate_epa.load_tightenings refuses the record: {exc}"]) from None
        probs = VE.tightening_problems(t, {"ecu_strategy_b58": strategy}, b58=VE.b58_identity())
        if probs:
            raise Refused(["validate_epa.tightening_problems: " + p for p in probs])
        os.link(tmp, path)
    finally:
        os.remove(tmp)
    return common.sha_text(path)


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def make_log():
    def log(msg):
        print(f"[{now_utc()}] {msg}", file=sys.stderr, flush=True)
    return log


# =====================================================================================================
# The subcommands
# =====================================================================================================
def run_real(*, jobs, log, root=REPO):
    """ORDER step 8: the tightenings on results/EPA_ROADS/roads.json, written to results/EPA_TIGHTENINGS.json,
    everything read from and written to the tree under `root` (this one; test_epa_tightenings runs a synthetic
    repository). Refused under a Python that writes bytecode (python -B), and whenever real_problems finds a
    problem, before anything is computed and again before the write."""
    if not sys.dont_write_bytecode:
        raise Refused([NEEDS_B])
    probs, rec, sha = real_problems(root=root)
    if probs:
        raise Refused(probs)
    started = now_utc()
    prov0 = provenance(root=root)
    ci = contract_inputs(root=root)
    spark = spark_inputs(root=root)
    pinned = pinned_k3(root=root)
    l1, e8, timing, opened = compute(rec, roads_ref=f"{R.ROADS_REL} (roads_sha {sha})",
                                     strategy=ci["ecu_strategy_b58"], r_e8_pct=ci["r_e8_pct"], spark=spark,
                                     pinned=pinned, seconds=None, jobs=jobs, log=log, pinned_strict=True)
    real_checks(e8, pinned)
    probs, _, sha1 = real_problems(root=root)
    prov1 = provenance(root=root)
    if (probs or sha1 != sha or prov1["code_sha_text"] != prov0["code_sha_text"]
            or ecu_folder_state(root=root) != pinned["folder"]):
        raise Refused(["the tree, the roads record, the code or results/ENGINE_THRESHOLDS/ecu/ changed while the "
                       "tightenings ran"] + probs)
    record = assemble(roads_sha_value=sha, roads_seed=rec["commit_reveal"]["roads_seed"], kind="REAL", l1=l1, e8=e8,
                      prov=prov0, extra=_extra(ci, timing, opened, started, pinned, root=root))
    return write_checked(os.path.join(root, *OUT_REL.split("/")), record, strategy=ci["ecu_strategy_b58"]), record


def real_checks(e8, pinned):
    """The real run's own checks, again at the end (compute's pinned_strict checks each as its task ends):
    ecu_shift's above0 is the pinned 413 s, every K3 knee is the pinned one bit for bit (the knee re-set as
    ecu_shift sets it), and each knee was set at that above0."""
    bad = []
    if e8["time_above_nominal_s"] != pinned["time_above_nominal_s"] or e8.get("above0_measured") is not True:
        bad.append(f"the nominal trace spends {e8['time_above_nominal_s']} s above the knee (measured: "
                   f"{e8.get('above0_measured')}), not k3_nominal.json's {pinned['time_above_nominal_s']}")
    bad += [f"{n}: the K3 knee {v['knee_k']!r} is not k3_{n}.json's {v['pinned_knee_k']!r}"
            for n, v in e8["shifts"].items() if v["knee_equals_pinned"] is not True]
    bad += [f"{n}: the K3 knee was set at {v['k3_seconds']!r} s, not above0's {e8['time_above_nominal_s']}"
            for n, v in e8["shifts"].items() if n != "nominal" and v.get("k3_seconds") != e8["time_above_nominal_s"]]
    if bad:
        raise TighteningsDefect("E8: the knee is not re-set as thresholds/ecu_shift.py set it: " + "; ".join(bad))


def _extra(ci, timing, opened, started, pinned, *, root=REPO):
    return {"decisions": {"104": "results/VALIDATION_DECISIONS.md, row 104", "107": "row 107 (4)",
                          "121": "row 121 (2)", "122": "row 122 (4)", "71": "row 71", "order": "ORDER step 8"},
            "contract_sha_text": ci["sha_text"],
            "L1_basis": {"knee_shift_largest": ci["basis"], "source": "results/ENGINE_THRESHOLDS.json knee_shift.largest"},
            "ecu_folder_sha256": {"before": pinned["folder"], "after": ecu_folder_state(root=root)},
            "timing": timing, "files_opened": opened, "started_utc": started, "written_utc": now_utc()}


def untightened(ci):
    """Row 129 (4)'s L1 and E8 roads tables from contract_inputs' result: L1's four layout keys the contract's
    knee_shift.largest (its slope, set, knock reading and shift), and E8's two roads tables the contract's own
    locked-climb tables (ecu_strategy_b58), verbatim. The one place the writer and the record's check read them
    from the contract (mistake 10). Returns (L1's checked fields, the two tables)."""
    basis = ci["basis"]
    if type(basis.get("knock")) is not bool:
        raise Refused([f"the contract's knee_shift.largest names no knock reading (knock {basis.get('knock')!r})"])
    l1 = {"slope_points_per_K": float(basis["slope"]), "set": str(basis["set"]), "shift_k": float(basis["shift_k"]),
          "damage_reading": READING_TEXT["knock" if basis["knock"] else "noknock"], "tightened": False,
          "label": UNTIGHTENED}
    strategy = ci["ecu_strategy_b58"]
    return l1, {ROADS_KEYS[lv]: copy.deepcopy(strategy[GRID_KEYS[lv]]) for lv in ("lambda", "spark")}


def stopped_blocks(ci, spark):
    """The no-roads record's L1 and E8 (untightened), the B58's E8 band built by b58_band on those tables, as the
    real run builds it (row 107 (4)): with the contract's own tables, the locked-climb reading."""
    l1, tables = untightened(ci)
    l1["rule"] = ("row 129 (4): no road set exists, so L1 is not tightened: its slope, set, knock reading and shift "
                  "are the contract's knee_shift.largest, the basis of L1's R in-sample, so the held-out R "
                  "(epa_stats._R: the smaller of R and b/slope rounded down) is the contract's on every engine")
    e8 = dict(tables, tightened=False, label=UNTIGHTENED,
              rule=("row 129 (4): no road set exists, so E8 is not tightened: each roads table is the contract's own "
                    "locked-climb table (ecu_strategy_b58), verbatim, so at every shift P, the larger of the two "
                    "responses (epa_stats.e8_response), is the contract's"))
    e8["b58_u_val_kappa"] = b58_band(tables, strategy=ci["ecu_strategy_b58"], r_pct=ci["r_e8_pct"], spark=spark)
    return l1, e8


def run_stopped(*, log, root=REPO):
    """Row 129 (4): the no-roads record, written once to results/EPA_TIGHTENINGS.json under `root` (this tree;
    test_epa_tightenings runs a synthetic repository). Refused under a Python that writes bytecode, and whenever
    stopped_problems finds a problem, before anything is built and again before the write (with the code, the
    contract, what the attempts log holds and the shared branch's sha unchanged). Built by contract_inputs, spark_inputs, provenance,
    b58_band and assemble, and written by write_checked, as run_real builds and writes its record. Returns
    (its sha_text, the record)."""
    if not sys.dont_write_bytecode:
        raise Refused([NEEDS_B])
    probs, found = stopped_problems(root=root)
    if probs:
        raise Refused(probs)
    started = now_utc()
    prov0 = provenance(root=root)
    ci = contract_inputs(root=root)
    spark = spark_inputs(root=root)
    log(f"no roads (row 129 (4)): attempt {found['attempt']} of the draw stopped, not for a coding defect; "
        f"L1 and E8 {UNTIGHTENED}")
    l1, e8 = stopped_blocks(ci, spark)
    probs, found1 = stopped_problems(root=root)
    prov1 = provenance(root=root)
    if (probs or found1 != found or prov1["code_sha_text"] != prov0["code_sha_text"]
            or contract_inputs(root=root)["sha_text"] != ci["sha_text"]):
        raise Refused(["the tree, the attempts log, the code or the contract changed while the record was built"]
                      + probs)
    log_path = os.path.join(root, *R.ATTEMPTS_REL.split("/"))
    extra = {"decisions": {"129": "results/VALIDATION_DECISIONS.md, row 129 (4)", "103": "row 103 (3)",
                           "96": "row 96", "104": "row 104", "107": "row 107 (4)", "71": "row 71",
                           "order": "ORDER step 8"},
             "untightened": UNTIGHTENED,
             "no_roads": dict(found, attempts_log=R.ATTEMPTS_REL, attempts_sha_text=common.sha_text(log_path),
                              roads_json="absent and never committed in HEAD's history"),
             "contract_sha_text": ci["sha_text"],
             "L1_basis": {"knee_shift_largest": ci["basis"], "source": "results/ENGINE_THRESHOLDS.json knee_shift.largest"},
             "files_opened": sorted(R.OPENED), "started_utc": started, "written_utc": now_utc()}
    record = assemble(roads_sha_value=NONE_ROADS_SHA, roads_seed=NONE_ROADS_SEED, kind=NONE_KIND, l1=l1, e8=e8,
                      prov=prov0, extra=extra)
    return write_checked(os.path.join(root, *OUT_REL.split("/")), record, strategy=ci["ecu_strategy_b58"]), record


def provenance_problems(t, *, root):
    """A committed tightenings record's provenance against the repository under `root`, [] when it holds (the real
    run's record and the no-roads one alike): the code and the data inputs committed and clean at the run, with no
    compiled file beside the code; the B58's plant_sha R.B58_PLANT_SHA; the record committed, provenance.commit an
    ancestor of (or) its last commit, and each code_sha_text the sha256 of that file's blob at provenance.commit,
    this module's among them."""
    out = []
    prov = t.get("provenance") or {}
    g = prov.get("git") or {}
    for key in ("code_clean", "data_inputs_clean"):
        if g.get(key) is not True:
            out.append(f"provenance.git.{key} is {g.get(key)!r}")
    if g.get("bytecode_caches") != []:
        out.append(f"provenance.git.bytecode_caches is {g.get('bytecode_caches')!r}")
    if prov.get("plant_sha") != R.B58_PLANT_SHA:
        out.append(f"provenance.plant_sha {prov.get('plant_sha')!r} is not {R.B58_PLANT_SHA}")
    try:
        last = R._git_ok(root, "log", "-1", "--format=%H", "--", OUT_REL).strip()
        if not last:
            out.append(f"{OUT_REL} is not committed")
        elif not epa_freeze.is_ancestor(str(prov.get("commit")), last, root=root):
            out.append(f"provenance.commit {prov.get('commit')!r} is not an ancestor of the record's commit {last}")
        else:
            code = prov.get("code_sha_text") or {}
            if MODULE_REL not in code:
                out.append(f"code_sha_text does not cover {MODULE_REL}")
            out += [f"{f}: code_sha_text is not its blob's at provenance.commit" for f, s in sorted(code.items())
                    if epa_freeze.blob_sha256(prov["commit"], f, root=root) != s]
    except (epa_freeze.GitError, R.Refused, RuntimeError) as exc:
        out.append(f"the record's commits cannot be checked ({type(exc).__name__}: {exc})")
    return out


def origin_record_problems(*, root):
    """The committed no-roads record against the shared branch, [] when it holds (row 129 (4)): origin's GRA-test, as
    the remote itself reports it (epa_roads.remote_state: git ls-remote, the objects fetched), holds the record's
    last commit; its history holds no roads.json (a set drawn in another clone and pushed is a set, row 103 (3); read
    with --full-history, so a set on a side branch merged away counts); and its attempts log and its record are
    HEAD's."""
    try:
        last = R._git_ok(root, "log", "-1", "--format=%H", "--", OUT_REL).strip()
        if not last:
            return [f"{OUT_REL} is not committed, so {R.REMOTE_NAME}'s {R.REMOTE_BRANCH} cannot hold it"]
        pushed, tip, why = R.remote_state(root, last)
        if not pushed:
            return [f"the shared branch does not hold the record's commit {last}: {why}"]
        out = []
        if R._git_ok(root, "log", "--full-history", "--format=%H", tip, "--", R.ROADS_REL).split():
            out.append(f"{R.REMOTE_NAME}'s {R.REMOTE_BRANCH} ({tip}) holds {R.ROADS_REL} in its history: a road set was "
                       "drawn and pushed (row 103 (3)), so the no-roads record stands on nothing (row 129 (4))")
        for rel in (R.ATTEMPTS_REL, OUT_REL):
            if R._lf(R._show(root, tip, rel)) != R._lf(R._show(root, "HEAD", rel)):
                out.append(f"{rel} at {R.REMOTE_NAME}'s {R.REMOTE_BRANCH} ({tip}) is not HEAD's")
        return out
    except R.Refused as exc:
        return ["the shared branch cannot be read: " + "; ".join(exc.args[0])]


def stopped_record_problems(t, *, root):
    """What validate_epa's arming does not check of a committed results/EPA_TIGHTENINGS.json written by `stopped`
    (row 129 (4)), [] when all holds, read against the repository under `root` (the arming takes any record in the
    layout with the B58's plant_sha and engine_sha): the roads step as no_roads_problems reads it (roads.json absent
    and never committed; the attempts log committed, append-only, as draw writes it, ending in the one non-defect
    stop whose reveals, checked again, do not both match), and the record's no_roads block every key it finds, with
    the log's sha_text, which is the log's at provenance.commit too (the record was built after the stop was
    committed); seed_kind NONE and the constant fields (schema, plant, roads_sha "none", roads_seed the int -1, and
    the top-level untightened label, which a Run 2 report takes beside L1.label and E8.label); L1's
    slope, set, knock reading and shift and E8's two roads tables the contract's (untightened), both marked
    untightened, and the B58's band b58_band's on those tables recomputed from the contract and
    results/car_spark_boost.json (row 107 (4)'s locked-climb reading); the provenance (provenance_problems:
    provenance.commit an ancestor of the record's commit, code_sha_text the blobs at that commit); and the shared
    branch (origin_record_problems)."""
    probs, found = no_roads_problems(root=root)
    out = [f"the roads step: {p}" for p in probs]
    for key, want in (("schema", SCHEMA), ("plant", PLANT), ("seed_kind", NONE_KIND), ("roads_sha", NONE_ROADS_SHA),
                      ("untightened", UNTIGHTENED)):
        if t.get(key) != want:
            out.append(f"{key} is {t.get(key)!r}, not {want!r} (row 129 (4))")
    if type(t.get("roads_seed")) is not int or t.get("roads_seed") != NONE_ROADS_SEED:
        out.append(f"roads_seed is {t.get('roads_seed')!r}, not the int {NONE_ROADS_SEED} (row 129 (4))")
    try:
        ci = contract_inputs(root=root)
        l1_want, tables = untightened(ci)
        band_want = json.loads(json.dumps(R.jsonable(b58_band(tables, strategy=ci["ecu_strategy_b58"],
                                                              r_pct=ci["r_e8_pct"], spark=spark_inputs(root=root))),
                                          allow_nan=False))
    except (KeyError, TypeError, ValueError, OSError, Refused) as exc:
        return out + [f"the contract's L1 basis and E8 tables, or the B58's band, cannot be read "
                      f"({type(exc).__name__}: {exc})"]
    l1 = t.get("L1") if isinstance(t.get("L1"), dict) else {}
    for key, want in l1_want.items():
        if type(l1.get(key)) is not type(want) or l1.get(key) != want:
            out.append(f"L1.{key} is {l1.get(key)!r}, not {want!r}: untightened, L1 is the contract's "
                       "knee_shift.largest (row 129 (4))")
    e8 = t.get("E8") if isinstance(t.get("E8"), dict) else {}
    for key, want in tables.items():
        if e8.get(key) != want:
            out.append(f"E8.{key} is not the contract's own locked-climb table: untightened, P is the contract's "
                       "(row 129 (4))")
    for key, want in (("tightened", False), ("label", UNTIGHTENED)):
        if type(e8.get(key)) is not type(want) or e8.get(key) != want:
            out.append(f"E8.{key} is {e8.get(key)!r}, not {want!r} (row 129 (4))")
    if e8.get("b58_u_val_kappa") != band_want:
        out.append("E8.b58_u_val_kappa is not b58_band's on the contract's own tables, recomputed from the contract and "
                   "results/car_spark_boost.json (row 107 (4): the locked-climb reading)")
    nr = t.get("no_roads") if isinstance(t.get("no_roads"), dict) else {}
    out += [f"no_roads.{key} is not the attempts log's (row 129 (4))" for key, want in found.items()
            if key not in nr or nr[key] != want]
    log_path = os.path.join(root, *R.ATTEMPTS_REL.split("/"))
    if nr.get("attempts_sha_text") != common.sha_text(log_path):
        out.append("no_roads.attempts_sha_text is not the committed attempts log's")
    try:
        at_prov = epa_freeze.blob_sha256(str((t.get("provenance") or {}).get("commit")), R.ATTEMPTS_REL, root=root)
    except epa_freeze.GitError:
        at_prov = None
    if at_prov is None or at_prov != nr.get("attempts_sha_text"):
        out.append(f"{R.ATTEMPTS_REL} at provenance.commit is not the log the record names (no_roads.attempts_sha_text): "
                   "the record is built after the stop is committed (row 129 (4))")
    return out + provenance_problems(t, root=root) + origin_record_problems(root=root)


def run_synthetic(*, synthetic_seed, n_roads, out_dir, roads_record, jobs, log):
    """The chain on SYNTHETIC roads, written under out_dir (outside every git work tree)."""
    out_dir = os.path.abspath(out_dir)
    if not outside_work_trees(out_dir):
        raise Refused([f"{out_dir} lies inside a git work tree: a SYNTHETIC run writes outside every work tree"])
    out = os.path.join(out_dir, SYNTHETIC_OUT_NAME)
    if os.path.exists(out):
        raise Refused([f"{out} exists: it is written once"])
    started = now_utc()
    if roads_record is None:
        rpath = os.path.join(out_dir, SYNTHETIC_ROADS_NAME)
        if os.path.exists(rpath):
            raise Refused([f"{rpath} exists: it is written once"])
        rec = synthetic_roads_record(synthetic_seed, n_roads=n_roads, roads=None, tau_s=None, jobs=jobs)
        R.write_once(rpath, rec)
        log(f"SYNTHETIC roads record written: {rpath}")
    else:
        rpath = os.path.abspath(roads_record)
    rec = common.load_json(rpath)
    probs = roads_problems(rec, kind="SYNTHETIC")
    if probs:
        raise Refused(probs)
    sha = R.roads_sha(rpath)
    prov = provenance(root=REPO)
    ci = contract_inputs()
    spark = spark_inputs(root=REPO)
    pinned = pinned_k3(root=REPO)
    l1, e8, timing, opened = compute(rec, roads_ref=f"SYNTHETIC roads {os.path.basename(rpath)} (roads_sha {sha})",
                                     strategy=ci["ecu_strategy_b58"], r_e8_pct=ci["r_e8_pct"], spark=spark,
                                     pinned=pinned, seconds=None, jobs=jobs, log=log)
    record = assemble(roads_sha_value=sha, roads_seed=rec["commit_reveal"]["roads_seed"], kind="SYNTHETIC", l1=l1,
                      e8=e8, prov=prov, extra=dict(_extra(ci, timing, opened, started, pinned),
                                                   roads_record=rpath))
    return write_checked(out, record, strategy=ci["ecu_strategy_b58"]), record, out


def run_timing(*, out_dir, jobs, log):
    """One SYNTHETIC 900 s road through the whole chain (mistake 22), written to out_dir/timing.json with the
    SYNTHETIC tightenings and roads beside it."""
    out_dir = os.path.abspath(out_dir)
    tpath = os.path.join(out_dir, TIMING_NAME)
    why = out_problem(tpath, in_tree_rel=OUT_DIR_REL)
    if why:
        raise Refused([why])
    in_tree = not outside_work_trees(out_dir)
    scratch = out_dir if not in_tree else None
    if in_tree:
        import tempfile
        scratch = tempfile.mkdtemp(prefix="epa_tightenings_timing_")
    sha, rec, path = run_synthetic(synthetic_seed=SYNTHETIC_SEED_TIMING, n_roads=1, out_dir=scratch, roads_record=None,
                                   jobs=jobs, log=log)
    t = dict(rec["timing"], what="one SYNTHETIC 900 s road through the whole chain (mistake 22)",
             synthetic_seed=SYNTHETIC_SEED_TIMING, tightenings_SYNTHETIC=path, tightenings_sha_text=sha,
             provenance={"commit": rec["provenance"]["commit"], "git": rec["provenance"]["git"]}, written_utc=now_utc())
    R.write_once(tpath, R.jsonable(t))
    return t, tpath


def _kappa_text(band):
    return "undefined (off: the team's call, row 107 (3))" if band["kappa"] is None else f"{band['kappa']:.3f}"


def stopped_summary_lines(rec):
    """The no-roads record's summary (row 129 (4)): every line about L1 or E8 labels them UNTIGHTENED."""
    l1, e8, nr = rec["L1"], rec["E8"], rec["no_roads"]
    bands = e8["b58_u_val_kappa"]
    band = bands["with_roads"]
    stop = nr["stop"]
    earlier = nr.get("earlier_attempts_both_matching")
    return [f"no roads (row 129 (4)): attempt {stop.get('attempt')} of the draw stopped, not for a coding defect "
            f"({stop.get('reason')}); the reveals checked again against the roads commit {nr['roads_commit']}: "
            f"{nr['reveal_matches_rechecked']}",
            "earlier attempts whose logged reveals both match (roads_seed was computable from the log; not refused, "
            f"row 129 (4)'s disclosure): {earlier if earlier else 'none'}; "
            f"{(nr.get('shared_branch_at_write') or {}).get('remote')}'s "
            f"{(nr.get('shared_branch_at_write') or {}).get('branch')} at the write: "
            f"{(nr.get('shared_branch_at_write') or {}).get('sha')}",
            f"roads_sha {rec['roads_sha']!r}, roads_seed {rec['roads_seed']}, seed_kind {rec['seed_kind']}",
            f"L1 {UNTIGHTENED}: slope {l1['slope_points_per_K']:.4f} points per K, the contract's knee_shift.largest "
            f"(set {l1['set']}, {l1['damage_reading']}, shift {l1['shift_k']:+g} K)",
            f"E8 {UNTIGHTENED}: lambda roads table, the contract's own: "
            + ", ".join(f"{s:+g} {c:+.4f}" for s, c in e8[ROADS_KEYS["lambda"]]),
            f"E8 {UNTIGHTENED}: spark roads table, the contract's own: "
            + ", ".join(f"{s:+g} {c:+.4f}" for s, c in e8[ROADS_KEYS["spark"]]),
            f"B58 E8 band (row 107 (4); E8 {UNTIGHTENED}), the locked-climb reading: E {band['E_pct']:.2f} %, "
            f"u_val {band['u_val_pct']}, label {band['label']}, kappa {_kappa_text(band)}; model minus car "
            f"(descriptive): kappa {_kappa_text(bands['model_minus_car']['with_roads'])}"]


def summary_lines(rec):
    if rec.get("seed_kind") == NONE_KIND:
        return stopped_summary_lines(rec)
    l1, e8 = rec["L1"], rec["E8"]
    bands = e8["b58_u_val_kappa"]
    band = bands["with_roads"]
    same = e8["reactive_identical_to_neutral"]
    t = rec["timing"]
    out = [f"L1: slope {l1['slope_points_per_K']:.4f} points per K (H {l1['H']} = {l1['H_s']:.2f} s, "
           f"{l1['reading']}, shift {l1['shift_k']:+g} K); the basis {rec['L1_basis']['knee_shift_largest']['slope']:.4f}",
           "E8 lambda roads: " + ", ".join(f"{s:+g} {c:+.4f}" for s, c in e8[ROADS_KEYS["lambda"]]),
           "E8 spark roads:  " + ", ".join(f"{s:+g} {c:+.4f}" for s, c in e8[ROADS_KEYS["spark"]]),
           f"E8 nominal pair: {e8['nominal_pair_points']}; above0 {e8['time_above_nominal_s']} s "
           f"(pinned {e8['pinned_time_above_nominal_s']}); knees equal the pinned ones: {e8['knees_equal_pinned']}",
           f"E8 runs on which reactive's damage equals neutral's (the head-start pair is then current-grade's cut "
           f"alone): knock {same['roads']['knock']}/{same['of']}, noknock {same['roads']['noknock']}/{same['of']}",
           f"B58 E8 band (row 107 (4)): E {band['E_pct']:.2f} %, u_val {band['u_val_pct']}, label {band['label']}, "
           f"kappa {_kappa_text(band)}; locked climb only: kappa {_kappa_text(bands['locked_climb_only'])}; "
           f"model minus car (descriptive): kappa {_kappa_text(bands['model_minus_car']['with_roads'])}",
           f"timing: {t['tasks']} tasks, wall {t['wall_s']:.0f} s at {t['jobs']} jobs; the real run predicted "
           f"{(t['real_run']['predicted_wall_s'] or float('nan')) / 3600.0:.2f} h"]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="row 104's tightenings of L1 and E8 on the B58")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("run")
    a.add_argument("--jobs", type=int, required=True)
    b = sub.add_parser("synthetic")
    b.add_argument("--synthetic-seed", type=int, required=True)
    b.add_argument("--roads", type=int, required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--jobs", type=int, required=True)
    b.add_argument("--roads-record", default=None)
    c = sub.add_parser("timing")
    c.add_argument("--out", required=True)
    c.add_argument("--jobs", type=int, required=True)
    sub.add_parser("stopped")
    args = ap.parse_args(argv)
    R.install_guard(())
    log = make_log()
    try:
        if args.cmd == "run":
            sha, rec = run_real(jobs=args.jobs, log=log)
            print(f"written {OUT_REL}: sha_text {sha}")
            print("\n".join(summary_lines(rec)))
        elif args.cmd == "stopped":
            sha, rec = run_stopped(log=log)
            print(f"written {OUT_REL} (row 129 (4), no roads; L1 and E8 {UNTIGHTENED}): sha_text {sha}")
            print("\n".join(summary_lines(rec)))
        elif args.cmd == "synthetic":
            if not 1 <= args.roads <= R.N_ROADS:
                raise Refused([f"--roads {args.roads}: 1 to {R.N_ROADS}"])
            sha, rec, path = run_synthetic(synthetic_seed=args.synthetic_seed, n_roads=args.roads, out_dir=args.out,
                                           roads_record=args.roads_record, jobs=args.jobs, log=log)
            print(f"SYNTHETIC tightenings written: {path} (sha_text {sha})")
            print("\n".join(summary_lines(rec)))
        else:
            t, path = run_timing(out_dir=args.out, jobs=args.jobs, log=log)
            print(f"timing written: {path}")
            print(json.dumps({k: t[k] for k in ("jobs", "wall_s", "tasks", "road_s_per_step", "k3_s", "above0_s",
                                                "real_run", "python_processes")}, indent=1))
    except Refused as exc:
        print("REFUSED:\n  " + "\n  ".join(str(p) for p in (exc.args[0] if exc.args and isinstance(exc.args[0], list)
                                                          else exc.args)), file=sys.stderr)
        return 2
    except R.Refused as exc:
        print("REFUSED:\n  " + "\n  ".join(str(p) for p in exc.args[0]), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""b58h_descriptive.py -- decision 12's three checks, as the B58 study's descriptive rows (row 147 (11)).

    python -B b58h_descriptive.py locked  --engine b58 --set runs/b58h_dt1 --reward-knock out --out DIR [--jobs N]
    python -B b58h_descriptive.py battery --engine b58 --set runs/b58h_dt1 --reward-knock out --out DIR [--jobs N]
                                          --grades results/conditions_b58h_dt1/conditions_grades.json
    python -B b58h_descriptive.py logged  --engine b58 --set runs/b58h_dt1 --reward-knock out --out DIR [--jobs N]

WHY THIS FILE (row 147 (11) of results/VALIDATION_DECISIONS.md; ORDER step 16, commit V). Decision 12's
direction, to train on the extremes and check on logged states, is not reversed silently: the B58 study
reports its check on logged states (logged_check.py, X1's step 5e), its transfer secondary at 50 C and on
hills of 18-22 % (conditions_test.py; row 116's declared secondary) and decision 34's locked-climb transfer
row (VD:200), each per arm and seed, labelled descriptive, deciding nothing. The committed scripts do not
score schema-4 agents as they stand: they list only sighted_seed* and blind_seed* folders
(logged_check._agent_tags, conditions_test._agent_tags), so they miss sighted_r0.5_seed* and
sighted_r1.5_seed*; they load final.zip, not decision 29's checkpoint average; and they build the
environment at the default H, never at the agent's. Both stay as X1 left them, since X1's and X2's
published results rest on them, make_page.py anchors source text in conditions_test.py and
record_extracts.py imports it. So this module is their reader for schema-4 agents, and it edits neither.

WHAT IS READ, AND FROM WHOM (one definition each, mistake 11):
  the agents   every run folder of the set named blind_seed<S> or sighted_r<r>_seed<S> (and sighted_seed<S>,
               which evaluate.arm_of then refuses) that holds final.zip (agent_dirs); the arm and H from each
               meta.json through evaluate.arm_of (evaluate.read_agents), H checked against r x tau of the
               committed roads record; one environment (evaluate.environment_problems, row 143 (5)); row
               117's pairs (evaluate.pairing_problems); the backend record's train_backend
               (evaluate.committed_train_backend and backend_problems)
  the policy   decision 29's checkpoint average, evaluate.load_agent (training_recipe.AveragedPolicy), after
               evaluate.average_lines' checks
  the route    evaluate.check_transfer, the declared transfer route: every FATAL field of an agent's
               meta.json but scenario and episodes_sha must be phase-d's block on this plant at the agent's
               own H and the --reward-knock given (transfer_live); both of those are printed, as trained and
               as scored, and nothing is forced. The logged drives and the battery are no protocol of their
               own, so the other FATAL fields are checked against phase-d's block too (the plant, H, reward
               and backends are what the check is for), while the scored side of the two printed fields is
               the row's own (route_scored): phase-d's for the locked climb; for the battery, the hills
               file by path and sha_text, the conditions with their hills, the speed target and episodes
               1, 5, 9, 13 and 17; for the logged drives, results/logged_cycles.json by path and sha_text,
               its drives and the two weightings
  the episode  evaluate.run_cycle_episode, evaluate._drive's one loop, at the agent's H; X1's per-step counts
               through its observe hook (BatteryCounts, LoggedCounts), which only read
  the choices  every fixed choice of the two scripts is imported from them, never retyped:
               conditions_test's CONDITIONS, EPISODES, HAND, speed_profile and TRIGGER_C; logged_check's
               drives and weightings (results/logged_cycles.json, re-checked by logged_check._check_cycles),
               drive_cycle, DEMAND_NM, T_LIMIT, F_LIMIT, COLD_C and HAND. Three literals of their loops are
               named here, BATTERY_SHORT (conditions_test._run's 0.95), LOGGED_ABOVE_C (logged_check.run's
               850.0) and LOGGED_DT (its 1.0), and test_b58h_descriptive pins each against its script's text

THE THREE ROWS, per arm and seed:
  locked   the plant's locked climb over the twenty frozen episodes (evaluate.episode_cycle, EPISODES):
           every policy's damage in both readings, its cut against the baseline ECU in evaluate.py's form
           (evaluate.median_cut), and per ratio and seed the sighted cut minus the blinded one
  battery  conditions_test.py's seven conditions, each on its own hill (--grades), on the varying speed
           target, the compressor inlet following the pressure, over episodes 1, 5, 9, 13 and 17:
           conditions_test._run's counts, the cut against the condition's own baseline ECU and the margin
           over its current-grade, in both readings, and per ratio and seed the sighted cut minus the blinded
  logged   logged_check.py's drives, replayed flat at their own speed and ambient, at both weightings: T
           and F exactly as logged_check.run computes them, per drive, and whether an agent meets both on
           every drive and weighting

WHAT IS NOT DECIDED HERE. Every number is descriptive (row 147 (11)): nothing here tests the criterion, and
no verdict of the study reads it.

THE HILLS ARE FIXED IN Q, BEFORE ANY AGENT OF THE STUDY TRAINS (conditions_test.py's own rule: "the hills
are fixed on the current plant with --hills-only BEFORE any of them trains"). In ORDER step 17 (Q, the
B58's gates), in Q's git clone of the pushed Qa outside the repository, with no roads check and no
test_engine_threading beside it:

    export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
    PY=/c/Users/badcl/Desktop/GRAD-project/.venv/Scripts/python.exe
    $PY -B conditions_test.py --set runs/b58h_dt1 --hills-only

It needs no agent (conditions_test.calibrate with harness False: the baseline ECU alone) and writes
results/conditions_b58h_dt1/conditions_grades.json (conditions_test.use_set), whose fixed_before_training
names the set, plant_sha, derived_sha, engine and engine_sha. The file is copied into the repository and
committed with Q's outputs, before PL-B and T*, and PR-B names it; after a re-made P, Q's repeated runs
fix it again (ORDER step 17). Its run time, by reading conditions_test.calibrate: per condition the
25-grade coarse grid and up to three 0.25 % steps, one baseline-ECU episode of 720 s each, so at most 196
episodes in 14-21 rounds of the --workers pool (18 by default on the 20-thread laptop);
results/PREREGISTRATION_X2.md (5e and 11) records a --hills-only run that had fixed four of the seven
hills when it was stopped at a 30-minute limit, so about one hour (ASSUMED; never timed on this tree). It
takes no --reward-knock: the hills are the baseline ECU's peaks, which the reward does not move.
read_grades refuses a hills file whose fixed_before_training.engine_sha is not this plant's (X1's file
records no engine_sha, and is refused).

Outputs: <DIR>/b58h_<row>.json, written once (evaluate.write_once_json), outside the repository; its own
step commits it.
"""
import argparse
import hashlib
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import check_premise as CP  # noqa: E402
import conditions_test as CT  # noqa: E402
import engine_env as E  # noqa: E402
import engines  # noqa: E402
import evaluate as V  # noqa: E402
import fingerprint as FP  # noqa: E402
import logged_check as LC  # noqa: E402

ROWS = ("locked", "battery", "logged")
SCHEMA = "b58h-descriptive/1"
LABEL = "descriptive (row 147 (11)): reported per arm and seed, deciding nothing"
ROUTES = {"locked": "the locked climb (decision 34's transfer row)",
          "battery": "the conditions battery (decision 12's transfer secondary)",
          "logged": "the logged drives (decision 12's check on logged states)"}
# the run folders read: the three arms of the study, and sighted_seed<S>, which arm_of refuses by name
RUN_NAME = re.compile(r"(blind|sighted(_r[0-9]+(\.[0-9]+)?)?)_seed[0-9]+")
# literals of the two scripts' loops, each pinned against its source by test_b58h_descriptive
BATTERY_SHORT = 0.95           # conditions_test._run: a step delivering under 95 % of the torque asked for
LOGGED_ABOVE_C = 850.0         # logged_check.run: a step with the housing above the trigger, C
LOGGED_DT = 1.0                # logged_check.run's step, s


def _hand(row):
    """The hand-written policies each row runs beside the agents, as its own script runs them."""
    return {"locked": V.HAND_POLICIES, "battery": CT.HAND, "logged": LC.HAND}[row]


# ---------------------------------------------------------------------------------------------- the agents
def agent_dirs(set_dir):
    """Every run folder of the set this module reads, sorted by arm then seed: a folder named by RUN_NAME
    that holds final.zip. A crashed run moved aside (<run>.crashed<N>) and anything else are left out."""
    root = set_dir if os.path.isabs(set_dir) else os.path.join(HERE, set_dir)
    out = [os.path.join(root, n) for n in os.listdir(root)
           if RUN_NAME.fullmatch(n) and os.path.isfile(os.path.join(root, n, "final.zip"))]

    def key(path):
        arm, _, seed = os.path.basename(path).rpartition("_seed")
        return arm, int(seed)
    return sorted(out, key=key)


def read_set(set_dir, *, roads_rec, engine, train_backend):
    """The set's agents (evaluate.read_agents: the arm and H through evaluate.arm_of), refused unless they
    trained on one environment, on the backend record's train_backend, and pair by row 117's rule."""
    paths = agent_dirs(set_dir)
    if not paths:
        raise SystemExit(f"\nREFUSING: {set_dir} holds no run folder named blind_seed<S> or sighted_r<r>_seed<S> "
                         "with a final.zip")
    agents = V.read_agents(paths, roads_rec=roads_rec, engine=engine)
    for check, problems in (("one environment (row 143 (5))",
                             V.environment_problems([(x["path"], x["meta"], x["config"]) for x in agents])),
                            ("the backend record's train_backend", V.backend_problems(agents, train_backend)),
                            ("row 117's pairs", V.pairing_problems(agents))):
        if problems:
            raise SystemExit(f"\nREFUSING {set_dir}: {check}: " + "; ".join(problems))
    return agents


def transfer_live(plant, *, preview_h_s, reward_knock, train_backend):
    """The block every agent is checked against on the declared transfer route: phase-d's, on this plant, at
    the agent's own H (None for the blinded arm) and the reward's knock option, the cycle model scoring."""
    return FP.plant_fingerprint("phase-d", plant=plant, train_backend=train_backend, score_backend=FP.BACKEND_CYCLE,
                                preview_h_s=preview_h_s, reward_knock=reward_knock)


def _episodes_sha(episodes):
    """fingerprint.episodes_sha's form for the episodes a row runs: the first 16 hex digits of the sha256 of
    their repr."""
    return hashlib.sha256(repr(tuple(episodes)).encode()).hexdigest()[:16]


def route_scored(row, *, cases, inputs):
    """{scenario, episodes_sha}: what the row scores, the scored side of its declared transfer (row 147 (11);
    evaluate.check_transfer prints it beside the trained side). locked: {}, since phase-d's own block is the
    locked climb and the twenty frozen episodes, what the row runs. battery: the hills file
    (inputs['grades'], its path and sha_text), each condition climbed with its ambient, pressure and hill,
    the speed target (conditions_test.SPEED_STEPS and ACCEL_MAX) at evaluate's duration and step. logged:
    the drives' record (inputs['cycles'], results/logged_cycles.json's path and sha_text), its drives in
    order and the step. episodes_sha hashes the (episode, (seed, weights)) pairs the row's cases run, from
    evaluate.EPISODES. `cases` are cases_for's."""
    if row == "locked":
        return {}
    if row == "battery":
        eps = sorted({c[3] for c in cases})
        scenario = {"route": "battery", "hills": inputs["grades"],
                    "conditions": [[CT.CONDITIONS[k][0], CT.CONDITIONS[k][1], CT.CONDITIONS[k][2], g]
                                   for k, g in sorted({(c[1], c[2]) for c in cases})],
                    "speed_steps": [list(s) for s in CT.SPEED_STEPS], "accel_max_mps2": CT.ACCEL_MAX,
                    "duration_s": V.DURATION, "dt": V.DT}
    elif row == "logged":
        eps = sorted({c[2] for c in cases})
        scenario = {"route": "logged", "cycles": inputs["cycles"], "drives": list(dict.fromkeys(c[1] for c in cases)),
                    "dt": LOGGED_DT}
    else:
        raise ValueError(f"row {row!r} is not one of {ROWS}")
    return {"scenario": scenario, "episodes_sha": _episodes_sha((i, V.EPISODES[i - 1]) for i in eps)}


def check_agents(agents, *, plant, reward_knock, train_backend, route, scored):
    """(lines, manifests): evaluate.check_transfer for every agent against transfer_live's block with
    `scored` (route_scored's: the row's own scenario and episodes_sha, {} for the locked climb) in place of
    phase-d's two, so that the declaration prints what the row scores; refused on any FATAL field but those
    two. Then evaluate.average_lines' checks of each checkpoint average. Refused (ValueError): a `scored`
    naming any field but evaluate.TRANSFER_EXEMPT's."""
    other = sorted(set(scored) - set(V.TRANSFER_EXEMPT))
    if other:
        raise ValueError(f"the scored side of a transfer replaces only {list(V.TRANSFER_EXEMPT)}, not {other}")
    lines, manifests, lives = [], {}, {}
    for x in agents:
        h = x["H_s"]
        if h not in lives:
            lives[h] = dict(transfer_live(plant, preview_h_s=h, reward_knock=reward_knock,
                                          train_backend=train_backend), **scored)
        lines += V.check_transfer(x["path"], x["meta"], lives[h], route=route)
        manifests[x["path"]], more = V.average_lines(x["path"], x["meta"])
        lines += more
    return lines, manifests


def read_grades(path, *, plant):
    """The battery's hills, fixed in Q before the study trains (THE HILLS, the module docstring): the file
    conditions_test.py --set runs/b58h_dt1 --hills-only writes, refused unless its
    fixed_before_training.engine_sha is this plant's and it holds a hill (a grade, or None where none reaches
    the target) for every condition of conditions_test.CONDITIONS."""
    with open(path, encoding="utf-8") as fh:
        got = json.load(fh)
    fixed = got.get("fixed_before_training") if isinstance(got.get("fixed_before_training"), dict) else {}
    want = engines.engine_sha(plant)
    if fixed.get("engine_sha") != want:
        raise SystemExit(f"\nREFUSING the hills {path}: they were fixed on engine_sha {fixed.get('engine_sha')!r}, "
                         f"and this plant's is {want} (Q fixes them on the study's plant: conditions_test.py "
                         "--set runs/b58h_dt1 --hills-only)")
    missing = [name for name, _, _ in CT.CONDITIONS if not isinstance(got.get(name), dict) or "grade" not in got[name]]
    if missing:
        raise SystemExit(f"\nREFUSING the hills {path}: no hill for {missing}")
    return got


# ---------------------------------------------------------------------------------------------- the counts
class BatteryCounts:
    """conditions_test._run's per-step counts, read after each step through evaluate._drive's observe: the
    steps delivering under BATTERY_SHORT of the torque asked for, the steps with the housing above
    conditions_test.TRIGGER_C, and the applied actuators on the climb (the cycle's grade above 0 at the
    step's own index, env.k before the step, which is env.k - 1 after it)."""

    def __init__(self, cycle):
        self.grade = cycle["grade"]
        self.short = 0
        self.above = 0
        self.applied = []

    def __call__(self, env, action, info):
        self.short += int(info["torque"] < BATTERY_SHORT * info["torque_req"])
        self.above += int(info["t_turb"] - 273.15 > CT.TRIGGER_C)
        if self.grade[env.k - 1] > 0:
            self.applied.append(np.array(env.prev_act, dtype=float))

    def row(self, *, dt):
        acts = np.median(np.array(self.applied), axis=0) if self.applied else None
        return dict(short_steps=int(self.short), s_above=float(self.above * dt),
                    act_climb=None if acts is None else [round(float(v), 4) for v in acts])


class LoggedCounts:
    """logged_check.run's per-step counts, read after each step through evaluate._drive's observe: the
    demand steps (torque_req above logged_check.DEMAND_NM), those the agent and the parallel baseline ECU
    each deliver more than engine_env.TRACK_TOL short and those the agent alone does, the steps above
    LOGGED_ABOVE_C for each, the baseline's peak, and the applied actuators while the baseline's housing is
    under logged_check.COLD_C."""

    def __init__(self):
        self.demand = self.short_a = self.short_b = self.short_only = 0
        self.above_a = self.above_b = 0
        self.peak_base = -np.inf
        self.cold = []

    def __call__(self, env, action, info):
        req = info["torque_req"]
        if req > LC.DEMAND_NM:
            self.demand += 1
            sa = bool(info["torque"] < (1.0 - E.TRACK_TOL) * req)
            sb = bool(info["torque_base"] < (1.0 - E.TRACK_TOL) * req)
            self.short_a += sa
            self.short_b += sb
            self.short_only += sa and not sb
        self.above_a += bool(info["t_turb"] - 273.15 > LOGGED_ABOVE_C)
        self.above_b += bool(env.thermal_base.t_turb - 273.15 > LOGGED_ABOVE_C)
        self.peak_base = max(self.peak_base, float(env.thermal_base.t_turb))
        if env.thermal_base.t_turb - 273.15 < LC.COLD_C:
            self.cold.append(np.array(env.prev_act, dtype=float))

    def row(self, out):
        acts = np.median(np.array(self.cold), axis=0) if self.cold else None
        return dict(steps=int(out["steps"]), demand_steps=int(self.demand), short_agent=int(self.short_a),
                    short_base=int(self.short_b), short_agent_only=int(self.short_only), fuel=float(out["fuel"]),
                    fuel_base=float(out["fuel_base"]), damage=float(out["damage"]),
                    damage_thermal=float(out["damage_thermal"]), damage_base=float(out["damage_base"]),
                    peak_turb=float(out["peak_turb"]), peak_turb_base=float(self.peak_base - 273.15),
                    s_above=int(self.above_a), s_above_base=int(self.above_b), cold_steps=len(self.cold),
                    act_cold=None if acts is None else [round(float(v), 4) for v in acts])


def logged_verdict(row):
    """(T, F) of one logged run, as logged_check.run decides them: T, the agent-only shortfall steps at most
    T_LIMIT of the demand steps; F, the agent's fuel at most F_LIMIT times the baseline ECU's."""
    return (row["short_agent_only"] <= LC.T_LIMIT * max(row["demand_steps"], 1),
            row["fuel"] <= LC.F_LIMIT * row["fuel_base"])


# ---------------------------------------------------------------------------------------------- the episodes
def battery_cycle(plant, *, t_amb, p_baro, grade):
    """(cycle, inlet_kpa) of one condition's hill, built as conditions_test._run builds it: the locked
    climb's cycle at this ambient and grade, its pressure, the varying speed target
    (conditions_test.speed_profile) and the compressor inlet following the pressure."""
    cycle = E.make_grade_climb(duration=V.DURATION, dt=V.DT, t_amb=t_amb, grade=grade, v_kmh=plant.scenario.v_kmh)
    cycle["p_baro"] = p_baro
    cycle["v_mps"] = CT.speed_profile(cycle["v_mps"], V.DT)
    return cycle, p_baro * plant.engine.boost.inlet_sea_kpa / 101.3


def locked_episode(policy, i, *, plant, use_preview, preview_h_s, reward_knock):
    """Frozen episode i (1-20) on the plant's locked climb at the arm's H: run_episode's seven values."""
    seed, weights = V.EPISODES[i - 1]
    out = V.run_cycle_episode(policy, V.episode_cycle(None, plant=plant), seed, weights, plant=plant, dt=V.DT,
                              use_preview=use_preview, preview_h_s=preview_h_s, reward_knock=reward_knock,
                              inlet_kpa=None, record=None, observe=None)
    return {k: out[k] for k in V.EPISODE_KEYS}


def battery_episode(policy, k, grade, i, *, plant, use_preview, preview_h_s, reward_knock):
    """Episode i of condition k on its hill `grade` at the arm's H: conditions_test._run's row."""
    _, t_amb, p_baro = CT.CONDITIONS[k]
    cycle, inlet = battery_cycle(plant, t_amb=t_amb, p_baro=p_baro, grade=grade)
    seed, weights = V.EPISODES[i - 1]
    counts = BatteryCounts(cycle)
    out = V.run_cycle_episode(policy, cycle, seed, weights, plant=plant, dt=V.DT, use_preview=use_preview,
                              preview_h_s=preview_h_s, reward_knock=reward_knock, inlet_kpa=inlet, record=None,
                              observe=counts)
    return dict({key: out[key] for key in V.EPISODE_KEYS}, **counts.row(dt=V.DT))


_W = {"key": None, "policy": None, "cycles": {}}


def logged_episode(policy, drive, ep, *, plant, use_preview, preview_h_s, reward_knock):
    """One logged drive, replayed flat (logged_check.drive_cycle), at weighting ep, at the arm's H:
    logged_check.run's row, with T and F."""
    if drive not in _W["cycles"]:
        _W["cycles"][drive] = LC.drive_cycle(drive)
    seed, weights = V.EPISODES[ep - 1]
    counts = LoggedCounts()
    out = V.run_cycle_episode(policy, dict(_W["cycles"][drive]), seed, weights, plant=plant, dt=LOGGED_DT,
                              use_preview=use_preview, preview_h_s=preview_h_s, reward_knock=reward_knock,
                              inlet_kpa=None, record=None, observe=counts)
    row = counts.row(out)
    row["T"], row["F"] = (bool(v) for v in logged_verdict(row))
    return row


def _policy(kind, ref):
    """A job's policy, kept while the next job is the same policy's: a check_premise policy by its function
    name, or an agent's checkpoint average (evaluate.load_agent)."""
    if _W["key"] != (kind, ref):
        _W.update(key=None, policy=None)
        if kind == "hand":
            pol = getattr(CP, ref)
        else:
            avg, _ = V.load_agent(ref, FP.read(os.path.join(ref, "meta.json")), device="cpu")
            pol = V.agent_policy(avg)
        _W.update(key=(kind, ref), policy=pol)
    return _W["policy"]


def run_job(job):
    """One policy on one case, in this process or a spawn worker. A refusal becomes a RuntimeError."""
    row, engine, kind, ref, use_preview, h_s, reward_knock, case = job
    plant = engines.get(engine)
    kw = dict(plant=plant, use_preview=use_preview, preview_h_s=h_s, reward_knock=reward_knock)
    try:
        policy = _policy(kind, ref)
        if case[0] == "locked":
            return locked_episode(policy, case[1], **kw)
        if case[0] == "battery":
            return battery_episode(policy, case[1], case[2], case[3], **kw)
        return logged_episode(policy, case[1], case[2], **kw)
    except SystemExit as exc:
        raise RuntimeError(f"{ref} on {case}: {exc}") from None


def cases_for(row, *, grades):
    """Every case a policy runs on this row, in order: locked ('locked', i); battery ('battery', condition,
    grade, i) for each condition with a hill; logged ('logged', drive, weighting), the drives re-checked
    against results/logged_cycles.json first (logged_check._check_cycles)."""
    if row == "locked":
        return [("locked", i) for i in range(1, len(V.EPISODES) + 1)]
    if row == "battery":
        return [("battery", k, grades[name]["grade"], i) for k, (name, _, _) in enumerate(CT.CONDITIONS)
                if grades[name]["grade"] is not None for i in CT.EPISODES]
    fixed = LC._check_cycles()
    eps = (fixed["episodes"]["life_most"], fixed["episodes"]["life_least"])
    return [("logged", r["drive"], ep) for r in fixed["drives"] for ep in eps]


def plan(row, agents, *, engine, reward_knock, grades):
    """(jobs, keys, cases): each hand-written policy of the row, then each agent, every case in order."""
    cases = cases_for(row, grades=grades)
    jobs, keys = [], []
    for label, fn in _hand(row):
        jobs += [(row, engine, "hand", fn, True, E.PREVIEW_H_S, reward_knock, c) for c in cases]
        keys.append(("hand", label))
    for x in agents:
        jobs += [(row, engine, "agent", x["path"], x["H_s"] is not None, x["H_s"], reward_knock, c) for c in cases]
        keys.append(("agents", (x["arm"], x["seed"])))
    return jobs, keys, cases


def _one_thread():
    try:
        import torch
    except ImportError:
        return
    torch.set_num_threads(1)


def _worker_init():
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    _one_thread()


def run_jobs(jobs, *, n_jobs, chunk):
    """Every job, in order: in this process at n_jobs 1, else in a spawn pool, one policy's cases per chunk."""
    if n_jobs <= 1:
        _one_thread()
        return [run_job(j) for j in jobs]
    import multiprocessing as mp
    import b58h_descriptive as _self    # pickled by this module's name, as a script too
    with mp.get_context("spawn").Pool(min(int(n_jobs), len(jobs)), initializer=_self._worker_init) as pool:
        return pool.map(_self.run_job, jobs, chunksize=max(1, chunk))


def group(keys, results, n):
    """{'hand': {label: [result per case]}, 'agents': {(arm, seed): [...]}} from run_jobs' results."""
    out = {"hand": {}, "agents": {}}
    for i, (g, key) in enumerate(keys):
        out[g][key] = results[i * n:(i + 1) * n]
    return out


# ---------------------------------------------------------------------------------------------- the rows
def _d(cuts, agents_keys):
    """{ratio: {seed: {reading: sighted cut - blinded cut}}} from {(arm, seed): {reading: cut}}."""
    out = {}
    for arm, seed in agents_keys:
        if arm == "blind" or ("blind", seed) not in cuts:
            continue
        r = arm[len("sighted_r"):] if arm.startswith("sighted_r") else arm
        out.setdefault(r, {})[str(int(seed))] = {reading: cuts[(arm, seed)][reading] - cuts[("blind", seed)][reading]
                                                 for reading in V.READING_KEYS}
    return out


def _cuts(rs, base):
    return {reading: V.median_cut([float(x[key]) for x in rs], [float(b[key]) for b in base])
            for reading, key in V.READING_KEYS.items()}


def _nest(agents_rows, value):
    """{arm: {seed: value(rows)}} from {(arm, seed): rows}."""
    out = {}
    for (arm, seed), rs in sorted(agents_rows.items(), key=lambda kv: (kv[0][0], int(kv[0][1]))):
        out.setdefault(arm, {})[str(int(seed))] = value(rs)
    return out


def locked_summary(grouped):
    """The locked-climb row: every policy's damage per episode in both readings, fuel and peak, and its cut
    against the baseline ECU; per ratio and seed the sighted cut minus the blinded."""
    base = grouped["hand"][V.BASELINE]

    def one(rs):
        return {"no_knock": [float(x["damage_thermal"]) for x in rs], "with_knock": [float(x["damage"]) for x in rs],
                "fuel": [float(x["fuel"]) for x in rs], "peak_turb": [float(x["peak_turb"]) for x in rs],
                "cut": _cuts(rs, base)}
    cuts = {key: _cuts(rs, base) for key, rs in grouped["agents"].items()}
    return {"episodes": len(base), "hand": {label: one(rs) for label, rs in grouped["hand"].items()},
            "agents": _nest(grouped["agents"], one), "d": _d(cuts, sorted(grouped["agents"]))}


def battery_summary(grouped, cases, grades):
    """The battery row, per condition: its hill, every policy's per-episode rows, each agent's cut against
    the condition's own baseline ECU and margin over its current-grade, in both readings, and per ratio and
    seed the sighted cut minus the blinded. A condition with no hill is reported as such."""
    out = {}
    for k, (name, t_amb, p) in enumerate(CT.CONDITIONS):
        g = grades[name]["grade"]
        if g is None:
            out[name] = {"grade": None, "note": "no hill reaches the target (conditions_test's calibration)"}
            continue
        idx = [j for j, c in enumerate(cases) if c[1] == k]

        def at(rs):
            return [rs[j] for j in idx]
        hand = {label: at(rs) for label, rs in grouped["hand"].items()}
        agents = {key: at(rs) for key, rs in grouped["agents"].items()}
        base, cg = hand["baseline ECU"], _cuts(hand["current-grade"], hand["baseline ECU"])

        def one(rs):
            c = _cuts(rs, base)
            return {"rows": rs, "cut": c, "margin_over_current_grade": {r: c[r] - cg[r] for r in c},
                    "short_steps_median": float(np.median([x["short_steps"] for x in rs])),
                    "s_above_median": float(np.median([x["s_above"] for x in rs])),
                    "peak_turb_max": float(max(x["peak_turb"] for x in rs))}
        cuts = {key: _cuts(rs, base) for key, rs in agents.items()}
        out[name] = {"grade": g, "t_amb_k": t_amb, "p_kpa": p, "episodes": list(CT.EPISODES),
                     "hand": {label: one(rs) for label, rs in hand.items()}, "agents": _nest(agents, one),
                     "d": _d(cuts, sorted(agents))}
    return out


def logged_summary(grouped, cases):
    """The logged row: every policy's run per drive and weighting with T and F, and whether it meets both on
    every one (logged_check's pass)."""
    def one(rs):
        runs = [dict(r, drive=c[1], episode=c[2]) for r, c in zip(rs, cases)]
        return {"runs": runs, "T_ok": sum(bool(r["T"]) for r in rs), "F_ok": sum(bool(r["F"]) for r in rs),
                "n": len(rs), "pass": all(bool(r["T"]) and bool(r["F"]) for r in rs)}
    return {"criteria": {"demand_nm": LC.DEMAND_NM, "track_tol": E.TRACK_TOL, "t_limit": LC.T_LIMIT,
                         "f_limit": LC.F_LIMIT, "cold_c": LC.COLD_C},
            "hand": {label: one(rs) for label, rs in grouped["hand"].items()}, "agents": _nest(grouped["agents"], one)}


# ---------------------------------------------------------------------------------------------- the command
def main(argv=None):
    import platform
    import epa_freeze as EF
    import epa_roads as ER
    import four_engine_roads as FER
    from thresholds import common
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("row", choices=ROWS)
    ap.add_argument("--engine", required=True, choices=engines.trainable(),
                    help="the plant (engines.get); REQUIRED, there is no default engine (CLAUDE.md mistake 1)")
    ap.add_argument("--set", required=True, help="the agents' folder, e.g. runs/b58h_dt1")
    ap.add_argument("--reward-knock", required=True, choices=("in", "out"),
                    help="the reward the agents trained with, a FATAL field, never read from meta.json")
    ap.add_argument("--out", required=True, help="a folder outside the repository for b58h_<row>.json")
    ap.add_argument("--grades", default=None, help="battery only: conditions_test.py --hills-only's file")
    ap.add_argument("--jobs", type=int, default=1, help="spawn workers; the numbers are the same at any N")
    a = ap.parse_args(argv)
    if (a.row == "battery") != (a.grades is not None):
        raise SystemExit("\nREFUSING: --grades is the battery's, and the battery needs it")
    if FER.inside_repository(a.out):
        raise SystemExit(f"\nREFUSING --out {a.out}: it lies inside the repository; the row is written outside it")
    out_path = os.path.join(a.out, f"b58h_{a.row}.json")
    if os.path.exists(out_path):
        raise SystemExit(f"\nREFUSING: {out_path} exists: it is written once")
    knock = a.reward_knock == "in"
    plant = engines.get(a.engine)
    grades = read_grades(a.grades, plant=plant) if a.row == "battery" else None
    rec_path = os.path.join(HERE, *ER.ROADS_REL.split("/"))
    try:
        roads_rec = FER.read_roads_record(rec_path)
    except FER.Refused as exc:
        raise SystemExit(f"\nREFUSING: {exc}") from None
    if roads_rec["seed_kind"] == "REAL":
        problem = FER.real_record_problem(rec_path)
        if problem:
            raise SystemExit(f"\nREFUSING: {problem}")
    train_backend = V.committed_train_backend(a.engine, root=HERE)
    agents = read_set(a.set, roads_rec=roads_rec, engine=a.engine, train_backend=train_backend)
    jobs, keys, cases = plan(a.row, agents, engine=a.engine, reward_knock=knock, grades=grades)
    inputs = {}
    if a.row == "battery":
        inputs["grades"] = {"path": a.grades, "sha_text": common.sha_text(a.grades)}
    if a.row == "logged":
        inputs["cycles"] = {"path": os.path.relpath(LC.CYCLES_JSON, HERE).replace(os.sep, "/"),
                            "sha_text": common.sha_text(LC.CYCLES_JSON)}
    # every transfer is declared, and refused if it must be, before any episode runs
    lines, manifests = check_agents(agents, plant=plant, reward_knock=knock, train_backend=train_backend,
                                    route=ROUTES[a.row], scored=route_scored(a.row, cases=cases, inputs=inputs))
    grouped = group(keys, run_jobs(jobs, n_jobs=a.jobs, chunk=len(cases)), len(cases))
    if a.row == "locked":
        results = locked_summary(grouped)
    elif a.row == "battery":
        results = battery_summary(grouped, cases, grades)
    else:
        results = logged_summary(grouped, cases)
    doc = {"schema": SCHEMA, "row": a.row, "label": LABEL, "route": ROUTES[a.row], "set": a.set,
           "engine": a.engine, "reward_knock": knock, "train_backend": train_backend, "transfer_lines": lines,
           "inputs": inputs,
           "provenance": {"versions": EF.versions(), "platform": platform.platform(), "device": "cpu",
                          "environment": V.env_of(agents[0]["meta"], agents[0]["config"]),
                          "agents": V.agents_provenance(agents, manifests),
                          "recipe_checks": V.recipe_checks(agents, manifests)},
           "results": results}
    sha = V.write_once_json(out_path, doc)
    print(f"{LABEL}\n{ROUTES[a.row]}: {len(agents)} agents, {len(cases)} cases each; written to {out_path}, "
          f"sha256 {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

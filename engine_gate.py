"""engine_gate.py -- each engine's own reward and road gate (row 119): what test_reward.py --engine and
check_roads.py --engine run, on the engine in its own car.

    python test_reward.py --engine E --train-road R --synthetic-seed N [--jobs J]
    python test_reward.py --engine E --train-road R --roads FILE [--jobs J]
    python check_roads.py --engine E --train-road R --synthetic-seed N --out FILE [--n 40]
    python check_roads.py --engine E --train-road R --roads FILE [--out FILE] [--n 40]

WHY EACH ENGINE GETS ITS OWN GATE (row 119 of results/VALIDATION_DECISIONS.md; ORDER_TO_TRAINING.md
steps 7 and 17). test_reward.py's gate is the B58's: its band grade and its D2 notch are that car's
gearbox, measured on it (its docstring, THE PLANT IS NAMED, which row 119 quotes at 22561da's
test_reward.py:105-110), and a changed scenario once made the neutral action fail the gate (its
docstring, PHASE D2; mistakes 5 and 17). The four-engine test trains every engine on row
116's training road and scores it on decision 34's roads, so each engine is gated there, in its own car,
before any agent of it trains: the B58 too, whose committed gate covers neither road.

WHAT RUNS. Every rollout is at dt 1.0, the four-engine test's step, with the neutral action
(engine_env.neutral_action) unless another policy is named; the starver is test_reward.torque_starver,
imported, so the two gates share one definition.
  the sweep     C5's margins (epa_stats.c5_steps: the thresholds the gearbox applies, decision 70) at the
                car's locked-climb speed and air, which must be decision 34's (130 km/h, 315 K, 101.3 kPa;
                check_scenario), every 0.05 % of grade over row 116's 0-18 %, as check_random_road.py C
                sweeps D2's range (:23-30). A NOTCH is a grade of the sweep at which the box holds another
                gear than 0.05 % below it (the CVT: another branch of decision 40's law; its first, from
                economy to kickdown, is the kickdown threshold). The BAND grade is the last grade before
                the first notch: the steepest the top held gear (the CVT's economy branch) serves. Both
                are computed from the plant each time the gate runs and printed with its output, so a
                plant that moves moves them (test_reward.py's D2 notch did not move with its plant:
                "THE NOTCH MOVED WITH THE MERGE, AND THIS TUPLE WAS NOT MOVED WITH IT").
  the table     the car's deliverable-torque table against a fresh engine_env.measure_deliverable_torque
                at every speed of its grid: the worst drift under 1.5 %, as test_reward.py's check.
  the band      the car's locked climb with the band grade from 30 s, 300 s (test_reward.py's band road
                at the engine's own grade): the baseline delivers (p95 tracking error under TRACK_TOL)
                and the neutral action scores about zero.
  each notch    make_grade_climb at the notch grade, 480 s (the D2 gate's length): the D2 gate's four
                checks, the neutral action about zero, the starver punished, the preview changing the
                observation and every reward finite; the random policy for information.
  decision 34   every road of the set, at its frozen episode's seed and weights (row 101): neutral about
                zero and inside TRACK_TOL; the starver punished on the first road.
  training      the training road as train.py builds it (train.build_env), at TRAIN_SEEDS: neutral about
                zero and inside TRACK_TOL; the starver punished on the first seed's road. Each road's
                share of steps asking less than the engine's torque floor (engine.loop.torque_floor_nm)
                or more than its deliverable torque at the step's engine speed is reported, not judged
                (row 116: "measured on drawn episodes and reported before training").
  the blind arm check_random_road.py B on decision 34's roads, per H (decision 27; row 119): the set's
                first road with a climb, and its twin with that climb's onset BLIND_SHIFT_S later, both
                neutral; a blinded agent's observations must not differ before the two grades do, and a
                sighted agent's must first differ int(H / dt) steps before that (row 117's furthest
                sample). Both are printed.

WHAT WAITS, refused rather than approximated:
  * H as an environment parameter (row 117) comes with row 94's plant commit. Until then the
    environment previews PREVIEW_S, whose furthest sample is 30 s, so the blind-arm check runs at
    H = 30 s only; any other H is refused by preview_env and printed NOT RUN, and a gate with a check
    not run does not pass.
  * Row 116's training road is train.py's mode "four_engine" (four_engine_roads.py, written beside this
    file on 31 October 2026), passed by name, --train-road, and driven on its general episodes
    (FOUR_ENGINE_OPTIONS). X1's extremes builders refuse every EPA car (engine_env.py:1827-1832;
    amendment B15), so an EPA engine's training checks fail with that refusal on any other road.
  * The Accord's training road: train.build_env's _StepState records step_record.env_state at every
    step, and step_record refuses a CVT (step_record.py:88-91) until its CVT branch, ORDER step 12a
    (C2, row 118). Until then the Honda's training checks fail with that refusal (MEASURED, 31 October
    2026: test_reward.py --engine honda_l15b7 --train-road four_engine --synthetic-seed 101).
  * Decision 34's roads exist once roads.json is drawn (ORDER step 6) and redrawn (step 12). --roads reads
    a roads record's "roads" and "H_table" (epa_roads.first_draw writes both); until then a SYNTHETIC seed
    draws the generator's roads (epa_roads.generate, SMOKE_N_ROADS of them) at H = 30 s, and every
    output says SYNTHETIC: such a run is a test of this code, not row 119's gate. After the redraws the
    scored set is roads.json's with redraws.json's accepted candidates in their slots; the code that
    applies them is evaluate.py's decision-34 protocol (ORDER step 16), not written yet, and --roads
    reads one record's roads as they stand.
  * The reward's knock option. The team chose the reward without the knock term for this test (row
    113 (5); ORDER's status line, "A+G, the reward without the knock term"), and row 119 says "If row
    113 (5)'s reward option is chosen, the gate runs with it". The option is an environment option of
    row 94's plant commit (row 118: default knock in, X1's), so it cannot be passed before that commit,
    and until then this gate runs the environment's reward as it stands, WITH the knock term. Once the
    plant commit lands, run_gate must pass the option to every environment it builds (the training
    road through train.build_env included), and the gate's output names it; a gate run without it is
    not row 119's gate for this test.

THE B58 AT ITS DEFAULTS IS NOT TOUCHED (row 118): nothing here is imported by train.py, by the
environment or by any module roads.json hashes (row 121), and test_reward.py and check_roads.py run
this code only when --engine is given.
"""
import copy
import json
import os

import numpy as np

import engine_env as E
import epa_roads as ER

HERE = os.path.dirname(os.path.abspath(__file__))

DT = ER.DT                       # 1.0 s: decision 34's roads and the four-engine test's step (row 101)
SWEEP_STEP = 0.0005              # 0.05 % of grade (row 119; check_random_road.py C)
SWEEP_GRADES = (0.0, 0.18)       # row 116's training grades, 0-18 %; decision 34's 10-12 % lie inside
TRACK_TOL = E.TRACK_TOL
NEUTRAL_BAND = 0.05              # |mean reward| under this: test_reward.py's "about zero"
STARVER_GAP = 0.02               # the starver under neutral by more than this: test_reward.py's
DRIFT_MAX = 0.015                # the table's worst drift: test_reward.py's 1.5 %
BAND_DURATION_S, BAND_START_S = 300.0, 30.0   # test_reward.py's band road (road_roll, "band")
NOTCH_DURATION_S = 480.0         # test_reward.py's D2_DURATION
NOTCH_SAMPLE_S = 10.0            # the preview check samples this long after the climb starts (the D2 gate's)
TRAIN_SEEDS = tuple(range(11, 21))   # ten training roads (test_reward.py's extremes check drives ten)
# Row 116's road, as train.py names it, built with its general episodes only: decision 29's scored share
# is row 101's generator's road (epa_roads.training_share_road), the kind the decision-34 checks drive,
# and a fresh environment's first episode would be a share episode (0, 10, 20, ...), so with the share on
# the gate would drive nothing else. The two options are train.build_env's for that road (DESIGN).
FOUR_ENGINE_ROAD = "four_engine"
FOUR_ENGINE_OPTIONS = dict(scored_share=False, roads_record=None)
BLIND_SHIFT_S = 20.0             # DESIGN: under every gap's G - RAMP_S (G >= 50 s, row 101), so the
                                 # moved climb never meets the next one
SYNTHETIC_ROADS = ER.SMOKE_N_ROADS


class WaitsForPlantCommit(NotImplementedError):
    """What this gate cannot run until row 94's plant commit: H as an environment parameter (row 117)."""


# ------------------------------------------------------------------ the sweep
def check_scenario(plant):
    """The car's locked climb runs at decision 34's speed and air, so the sweep's band and notches are
    those of decision 34's roads too; refused otherwise."""
    sc = plant.scenario
    if (float(sc.v_kmh), float(sc.t_amb)) != (ER.V_KMH, ER.T_AMB_K):
        raise ValueError(f"{plant.id}: the locked climb runs at {float(sc.v_kmh):g} km/h in {float(sc.t_amb):g} K, "
                         f"decision 34's roads at {ER.V_KMH:g} km/h in {ER.T_AMB_K:g} K (epa_roads.py): the "
                         "sweep would not describe the scored roads")


def sweep_grades():
    lo, hi = SWEEP_GRADES
    return np.round(np.arange(lo, hi + SWEEP_STEP / 2, SWEEP_STEP), 6)


def sweep(plant):
    """C5's step at every grade of sweep_grades(), on a road at the locked climb's steady speed and in its
    air (epa_stats.c5_steps; one sample per grade, so the speed's change is 0): per grade the gear held (the
    CVT: its branch), the torque asked, the engine speed and the margins to every threshold the box applies."""
    import epa_stats as ES
    check_scenario(plant)
    g = sweep_grades()
    n = len(g)
    sc = plant.scenario
    cycle = {"t": np.arange(n) * DT, "v_mps": np.full(n, float(sc.v_kmh) / 3.6), "grade": g,
             "t_amb": float(sc.t_amb), "p_baro": ER.P_BARO_KPA}
    steps = ES.c5_steps(plant, cycle, first=0, last=n - 1, dt=DT)
    return [{"grade": float(s.grade), "held": s.held, "demand_nm": float(s.demand_nm), "rpm": float(s.rpm),
             "margin": min((float(m) for _, m, _ in s.margins), default=None)} for s in steps]


def notches(rows):
    """Every grade of the sweep at which the box holds another gear (or branch) than at the grade below."""
    return [{"grade": b["grade"], "below": a["grade"], "from": a["held"], "to": b["held"], "margin": b["margin"]}
            for a, b in zip(rows, rows[1:]) if a["held"] != b["held"]]


def band_grade(rows):
    """The last grade before the first notch: the steepest the top held gear serves; the top of the range
    when the box holds one gear over all of it."""
    for a, b in zip(rows, rows[1:]):
        if a["held"] != b["held"]:
            return a["grade"]
    return rows[-1]["grade"]


def kickdown_threshold(cuts):
    """Decision 40's kickdown threshold on the sweep: the first grade on the kickdown branch, from economy
    (None on a stepped box, or when the range never leaves economy)."""
    for c in cuts:
        if c["from"] == "economy" and c["to"] == "kickdown":
            return c["grade"]
    return None


# ------------------------------------------------------------------ the roads
def band_cycle(plant, grade):
    """test_reward.py's band road at `grade`: the car's locked climb, the grade ramped in from 30 s."""
    c = E.locked_climb(plant, duration=BAND_DURATION_S, dt=DT)
    c["grade"] = grade * np.clip((c["t"] - BAND_START_S) / E.GRADE_RAMP_S, 0.0, 1.0)
    return c


def notch_cycle(plant, grade):
    """The car's locked climb at `grade`: flat for 180 s, then the climb, ramped (make_grade_climb)."""
    sc = plant.scenario
    return E.make_grade_climb(duration=NOTCH_DURATION_S, dt=DT, t_amb=float(sc.t_amb), grade=float(grade),
                              v_kmh=float(sc.v_kmh))


def d34_roads(*, roads_file, synthetic_seed):
    """Decision 34's roads: (roads, H_table or None, label). From a roads record (`roads_file`: its "roads"
    and "H_table", as epa_roads.first_draw writes them), or SYNTHETIC: epa_roads.generate on a seed below
    2**32 (never roads_seed), SYNTHETIC_ROADS roads."""
    if (roads_file is None) == (synthetic_seed is None):
        raise ValueError("decision 34's roads: give exactly one of a roads record and a SYNTHETIC seed")
    if roads_file is not None:
        with open(roads_file, encoding="utf-8") as fh:
            rec = json.load(fh)
        return rec["roads"], rec.get("H_table"), f"{os.path.basename(roads_file)} ({len(rec['roads'])} roads)"
    s = int(synthetic_seed)
    if not 0 <= s < ER.SYNTHETIC_SEED_LIMIT:
        raise ValueError(f"a SYNTHETIC seed is an integer in [0, 2**32), not {synthetic_seed!r}")
    return (ER.generate(s, n_roads=SYNTHETIC_ROADS), None,
            f"SYNTHETIC seed {s}, not roads_seed ({SYNTHETIC_ROADS} roads of epa_roads.generate)")


def horizons(h_table, engine_id):
    """The arms' horizons for one engine, s: every H of the roads record's H_table (row 102), or the
    environment's own furthest preview sample when there is no record (a SYNTHETIC run)."""
    if h_table is None:
        return [float(max(E.PREVIEW_S))]
    return sorted({float(v["H_s"]) for v in h_table[engine_id].values()})


def onset_twin(road):
    """(twin, slot, first differing step): `road` with its first climb's onset BLIND_SHIFT_S later and
    everything else as it stands, the grade rebuilt as epa_roads builds it and its ramps checked (row 98
    (a)). The road's own grade must be its climbs' (so the twin differs in that onset only)."""
    if not road["climbs"]:
        raise ValueError(f"road {road['k']}: no climb to move")
    t = np.asarray(road["cycle"]["t"], dtype=float)
    if not np.array_equal(ER.grade_from_climbs(t, road["climbs"]), np.asarray(road["cycle"]["grade"], dtype=float)):
        raise ValueError(f"road {road['k']}: its grade is not its climbs' (epa_roads.grade_from_climbs)")
    twin = copy.deepcopy(road)
    first = min(twin["climbs"], key=lambda c: c["onset_s"])
    first["onset_s"] = float(first["onset_s"]) + BLIND_SHIFT_S
    first["first_step"] = int(round(first["onset_s"] / DT))
    first["last_step"] = int(round((first["onset_s"] + first["L_s"] + ER.RAMP_S) / DT))
    twin["cycle"]["grade"] = [float(x) for x in ER.grade_from_climbs(t, twin["climbs"])]
    bad = ER.ramp_problems(twin["cycle"]["grade"], dt=DT)
    if bad:
        raise ValueError(f"road {road['k']}: the twin breaks row 98 (a): {bad}")
    diff = np.flatnonzero(np.asarray(twin["cycle"]["grade"]) != np.asarray(road["cycle"]["grade"], dtype=float))
    return twin, int(first["slot"]), int(diff[0])


# ------------------------------------------------------------------ the environments
def preview_env(cycle, *, plant, dt, use_preview, horizon_s, seed):
    """The environment at preview horizon `horizon_s`. H is not an environment parameter until row 94's
    plant commit (row 117, its default 30 s giving today's PREVIEW_S exactly), so until then only the
    horizon the environment has is built, and any other is refused, never approximated."""
    if float(horizon_s) != float(max(E.PREVIEW_S)):
        raise WaitsForPlantCommit(f"H = {float(horizon_s):g} s: the environment previews {E.PREVIEW_S} s; H as an "
                                  "environment parameter comes with row 94's plant commit (row 117)")
    return E.SupervisoryTunerEnv(cycle, plant=plant, dt=dt, use_preview=use_preview, seed=seed)


def d34_env(road, *, plant, use_preview):
    """One road of decision 34's set as evaluate.py's decision-34 protocol will score it (row 101): its
    frozen episode's seed at reset, and its weights pinned after it (k3_knee.neutral_run's order)."""
    seed = int(road["episode_seed"])
    env = E.SupervisoryTunerEnv(ER.env_cycle(road), plant=plant, dt=float(road["dt"]), use_preview=use_preview,
                                seed=seed)
    env.reset(seed=seed)
    env.w = np.asarray(road["weights"], dtype=np.float32)
    return env


def training_env(train_road, seed, *, plant):
    """The training road as train.py builds it (build_env: its wrappers, its design step, 900 s), reset at
    `seed`. A road train.py does not have is refused by name. Row 116's road is built with its general
    episodes only (FOUR_ENGINE_OPTIONS)."""
    import train as T
    if train_road not in T.DESIGN_DT:
        raise ValueError(f"train.py has no road {train_road!r} (train.DESIGN_DT: {sorted(T.DESIGN_DT)})")
    opts = FOUR_ENGINE_OPTIONS if train_road == FOUR_ENGINE_ROAD else {}
    env = T.build_env(True, seed, T.DURATION_S, train_road, T.DESIGN_DT[train_road], plant=plant, **opts)
    env.reset(seed=seed)
    return env


def wrapper_attr(env, name):
    """An attribute any layer of a wrapped environment holds (the episode's c_turb scale is the extremes
    environment's own, and the four-engine wrapper's), or None."""
    try:
        return env.get_wrapper_attr(name)
    except AttributeError:
        return None


# ------------------------------------------------------------------ the rollouts
def policy_action(policy, env, rng):
    if policy == "neutral":
        return E.neutral_action()
    if policy == "starver":
        from test_reward import torque_starver
        return torque_starver()
    if policy == "random":
        return rng.uniform(-1.0, 1.0, env.action_space.shape).astype(np.float32)
    raise ValueError(f"no policy {policy!r}")


def rollout(env, policy, *, plant):
    """One episode of `policy` on a reset environment: the mean reward, the p95 tracking error in the
    reward's own units, the turbine's peak and its time above the knee, and the shares of steps whose
    request is under the torque floor or over the deliverable torque at the step's engine speed."""
    u = env.unwrapped
    rpm_t, nm_t = (np.asarray(x, dtype=float) for x in zip(*plant.car.deliverable_torque))
    floor, knee = float(plant.engine.loop.torque_floor_nm), float(plant.engine.damage.turb_knee_k)
    rng = np.random.default_rng(0)
    rs, errs, turb, below, above = [], [], [], 0, 0
    while True:
        _, r, term, trunc, info = env.step(policy_action(policy, env, rng))
        rs.append(float(r))
        req = float(info["torque_req"])
        errs.append(abs(req - info["torque"]) / max(req, 40.0))
        turb.append(float(info["t_turb"]))
        below += req < floor
        above += req > float(np.interp(u.rpm, rpm_t, nm_t))
        if term or trunc:
            break
    n = len(rs)
    return {"mean_r": float(np.mean(rs)), "p95_err": float(np.percentile(errs, 95)),
            "peak_c": max(turb) - 273.15, "above_knee_s": float(np.count_nonzero(np.asarray(turb) > knee) * u.dt),
            "steps": n, "below_floor": below / n, "above_deliverable": above / n,
            "finite": bool(np.all(np.isfinite(rs)))}


def preview_delta(plant, cycle, *, start_s):
    """test_reward.obs_differs_without_preview on `cycle`: the largest difference between the sighted and
    the blinded observation NOTCH_SAMPLE_S after the climb begins, neutral, both arms."""
    seen = []
    n = int(min(len(cycle["t"]) * DT - 5.0, start_s + NOTCH_SAMPLE_S) / DT)
    for use_preview in (True, False):
        env = preview_env(cycle, plant=plant, dt=DT, use_preview=use_preview, horizon_s=max(E.PREVIEW_S), seed=0)
        obs, _ = env.reset(seed=1)
        for _ in range(n):
            obs, *_ = env.step(E.neutral_action())
        seen.append(np.asarray(obs, dtype=float))
    return float(np.max(np.abs(seen[0] - seen[1])))


def obs_trace(road, *, plant, use_preview, horizon_s, n):
    """(env.k, observation) after reset and each of n neutral steps on a decision-34 road (check_random_road
    obs_trace's form), keyed on the environment's own step counter."""
    seed = int(road["episode_seed"])
    env = preview_env(ER.env_cycle(road), plant=plant, dt=float(road["dt"]), use_preview=use_preview,
                      horizon_s=horizon_s, seed=seed)
    env.reset(seed=seed)
    env.w = np.asarray(road["weights"], dtype=np.float32)
    out = [(env.k, np.asarray(env._obs(), dtype=float))]
    for _ in range(n):
        obs, *_ = env.step(E.neutral_action())
        out.append((env.k, np.asarray(obs, dtype=float)))
    return out


def first_difference(a, b):
    """The step (env.k) of the first observation that differs between two traces, or None."""
    for (k, x), (_, y) in zip(a, b):
        if np.max(np.abs(x - y)) > 0.0:
            return int(k)
    return None


def blind_check(plant, road, *, horizon_s):
    """check_random_road.py B at H = horizon_s on one decision-34 road and its onset twin."""
    twin, slot, d = onset_twin(road)
    lead = int(horizon_s / DT)
    n = d + 5
    blind = first_difference(*(obs_trace(r, plant=plant, use_preview=False, horizon_s=horizon_s, n=n)
                               for r in (road, twin)))
    sight = first_difference(*(obs_trace(r, plant=plant, use_preview=True, horizon_s=horizon_s, n=n)
                               for r in (road, twin)))
    want_sight = max(0, d - lead)
    return {"H_s": float(horizon_s), "road": road["k"], "slot": slot, "grades_differ_at": d,
            "blind_first": blind, "sighted_first": sight, "sighted_want": want_sight,
            "blind_ok": blind is not None and blind >= d, "sighted_ok": sight == want_sight}


# ------------------------------------------------------------------ the jobs (one process each)
def job(task):
    """One unit of the gate, by kind, in its own process; the plant built there by name (engines.get).
    An error is returned as text with the task, never raised: a refusal is a result."""
    import engines
    kind, engine_id = task["kind"], task["engine"]
    try:
        plant = engines.get(engine_id)
        if kind == "table":
            rpms = [int(r) for r, _ in plant.car.deliverable_torque]
            fresh = dict(E.measure_deliverable_torque(rpms, plant=plant))
            table = dict(plant.car.deliverable_torque)
            worst = max(rpms, key=lambda r: abs(fresh[r] - table[r]) / table[r])
            return dict(task, drift=abs(fresh[worst] - table[worst]) / table[worst], worst_rpm=worst, rpms=len(rpms))
        if kind == "band":
            env = E.SupervisoryTunerEnv(band_cycle(plant, task["grade"]), plant=plant, dt=DT, seed=0)
            env.reset(seed=0)
            return dict(task, **rollout(env, task["policy"], plant=plant))
        if kind == "notch":
            env = E.SupervisoryTunerEnv(notch_cycle(plant, task["grade"]), plant=plant, dt=DT, seed=0)
            env.reset(seed=1)
            return dict(task, **rollout(env, task["policy"], plant=plant))
        if kind == "notch-preview":
            return dict(task, delta=preview_delta(plant, notch_cycle(plant, task["grade"]), start_s=180.0))
        if kind == "d34":
            env = d34_env(task["road"], plant=plant, use_preview=True)
            road = task.pop("road")
            return dict(task, k=road["k"], climbs=len(road["climbs"]),
                        grade_max=max(road["cycle"]["grade"]), **rollout(env, task["policy"], plant=plant))
        if kind == "train":
            env = training_env(task["train_road"], task["seed"], plant=plant)
            c = env.unwrapped.cycle
            g, v = np.asarray(c["grade"], dtype=float), np.asarray(c["v_mps"], dtype=float)
            road = {"family": c.get("family"), "grade_min": float(g.min()), "grade_max": float(g.max()),
                    "t_amb_c": float(c["t_amb"]) - 273.15, "v_min_kmh": float(v[20:].min() * 3.6),
                    "v_max_kmh": float(v.max() * 3.6), "c_turb_scale": wrapper_attr(env, "c_turb_scale")}
            return dict(task, **road, **rollout(env, task["policy"], plant=plant))
        if kind == "blind":
            road = task.pop("road")
            return dict(task, **blind_check(plant, road, horizon_s=task["H_s"]))
        raise ValueError(f"no job kind {kind!r}")
    except WaitsForPlantCommit as exc:
        task.pop("road", None)
        return dict(task, waits=str(exc))
    except Exception as exc:                                  # noqa: BLE001 -- a refusal is a result
        task.pop("road", None)
        return dict(task, error=f"{type(exc).__name__}: {exc}")


def pool_map(tasks, *, jobs):
    if jobs <= 1:
        return [job(t) for t in tasks]
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=min(jobs, len(tasks))) as ex:
        return list(ex.map(job, tasks))


# ------------------------------------------------------------------ test_reward.py --engine
def _worst(rows, key):
    return max(rows, key=lambda r: abs(r[key]))


def _first_error(rows):
    return next((r["error"] for r in rows if "error" in r), None)


def _road_checks(what, neutral, starver, key, label):
    """The pair of checks a road set gets: neutral about zero and inside TRACK_TOL on every road, and the
    starver punished on the first (key names a road: 'k' for decision 34's, 'seed' for a training road;
    label names the set in the details)."""
    err = _first_error(neutral + [starver])
    if err:
        return [(f"neutral scores about zero on every {what}", False, err),
                (f"refusing torque is punished on a {what}", False, err)]
    w = _worst(neutral, "mean_r")
    n0 = next(r for r in neutral if r[key] == starver[key])
    return [(f"neutral scores about zero on every {what}",
             all(abs(r["mean_r"]) < NEUTRAL_BAND and r["p95_err"] < TRACK_TOL for r in neutral),
             f"worst {key} {w[key]} {w['mean_r']:+.5f}, {len(neutral)} roads ({label}); worst p95 err "
             f"{max(r['p95_err'] for r in neutral):.3f}"),
            (f"refusing torque is punished on a {what}", starver["mean_r"] < n0["mean_r"] - STARVER_GAP,
             f"starver {starver['mean_r']:+.5f}  vs  neutral {n0['mean_r']:+.5f}   ({label}, {key} {n0[key]})")]


def run_gate(engine_id, *, train_road, roads_file, synthetic_seed, jobs):
    """Every unit of the gate in the module docstring, run in `jobs` processes. Returns the sweep, every
    unit's result and the checks, each (name, True, False or None when it did not run, detail)."""
    import engines
    plant = engines.get(engine_id)
    rows = sweep(plant)
    cuts = notches(rows)
    band = band_grade(rows)
    roads, h_table, label = d34_roads(roads_file=roads_file, synthetic_seed=synthetic_seed)
    hs = horizons(h_table, engine_id)
    blind_road = next((r for r in roads if r["climbs"]), None)
    base = dict(engine=engine_id)
    tasks = [dict(base, kind="table"), dict(base, kind="band", grade=band, policy="neutral")]
    for c in cuts:
        tasks += [dict(base, kind="notch", grade=c["grade"], policy=p) for p in ("neutral", "starver", "random")]
        tasks.append(dict(base, kind="notch-preview", grade=c["grade"]))
    tasks += [dict(base, kind="d34", road=r, policy="neutral") for r in roads]
    tasks.append(dict(base, kind="d34", road=roads[0], policy="starver"))
    tasks += [dict(base, kind="train", train_road=train_road, seed=s, policy="neutral") for s in TRAIN_SEEDS]
    tasks.append(dict(base, kind="train", train_road=train_road, seed=TRAIN_SEEDS[0], policy="starver"))
    tasks += [dict(base, kind="blind", road=blind_road, H_s=h) for h in hs if blind_road is not None]
    res = pool_map(tasks, jobs=jobs)

    def of(kind, policy=None):
        return [r for r in res if r["kind"] == kind and (policy is None or r.get("policy") == policy)]
    checks = []
    t = of("table")[0]
    checks.append(("gearbox table still matches the plant", "error" not in t and t["drift"] < DRIFT_MAX,
                   t.get("error") or f"worst drift {100 * t['drift']:.2f} % at {t['worst_rpm']} rpm, {t['rpms']} "
                                     f"speeds of the car's table   (want < {100 * DRIFT_MAX:g} %)"))
    b = of("band")[0]
    checks.append((f"baseline delivers torque on the band, {100 * band:.2f} %",
                   "error" not in b and b["p95_err"] < TRACK_TOL and abs(b["mean_r"]) < NEUTRAL_BAND,
                   b.get("error") or f"p95 tracking error {b['p95_err']:.3f}, neutral {b['mean_r']:+.5f}"))
    for c in cuts:
        got = {r.get("policy", "preview"): r for r in of("notch") + of("notch-preview") if r["grade"] == c["grade"]}
        name = f"the notch at {100 * c['grade']:.2f} % ({c['from']} -> {c['to']})"
        err = _first_error(list(got.values()))
        if err:
            checks.append((name, False, err))
            continue
        rn, rs, rr, dp = (got["neutral"]["mean_r"], got["starver"]["mean_r"], got["random"]["mean_r"],
                          got["preview"]["delta"])
        checks.append((name, abs(rn) < NEUTRAL_BAND and rs < rn - STARVER_GAP and dp > 1e-6
                       and all(got[p]["finite"] for p in ("neutral", "starver", "random")),
                       f"neutral {rn:+.5f}  starver {rs:+.5f}  random {rr:+.5f}  |d obs| {dp:.4g}"))
    checks += _road_checks("decision-34 road", of("d34", "neutral"), of("d34", "starver")[0], "k",
                           "SYNTHETIC" if synthetic_seed is not None else "the record")
    checks += _road_checks("training road", of("train", "neutral"), of("train", "starver")[0], "seed", train_road)
    if blind_road is None:
        checks.append(("the blind arm is blind", False, "no road of the set has a climb"))
    for r in sorted(of("blind"), key=lambda r: r["H_s"]):
        name = f"the blind arm is blind at H = {r['H_s']:g} s"
        if "waits" in r:
            checks.append((name, None, "NOT RUN: " + r["waits"]))
        elif "error" in r:
            checks.append((name, False, r["error"]))
        else:
            checks.append((name, r["blind_ok"] and r["sighted_ok"],
                           f"road {r['road']} slot {r['slot']}: the grades differ from step {r['grades_differ_at']}; "
                           f"BLIND first differs at {r['blind_first']} (want >= {r['grades_differ_at']}), "
                           f"SIGHTED at {r['sighted_first']} (want {r['sighted_want']})"))
    return dict(engine=engine_id, plant_id=plant.id, cvt=isinstance(plant.car, engines.CvtCar), sweep=rows,
                notches=cuts, band=band, kickdown=kickdown_threshold(cuts), label=label,
                synthetic=synthetic_seed is not None, horizons=hs, train_road=train_road, results=res, checks=checks)


def print_gate(g):
    """The per-engine gate in test_reward.py's layout. Returns the exit code: 0 only when every check ran
    and passed."""
    rows, cuts = g["sweep"], g["notches"]
    print(f"PER-ENGINE REWARD GATE (row 119): {g['engine']} in its own car ({g['plant_id']})")
    print(f"decision 34's roads : {g['label']}")
    if g["synthetic"]:
        print("                      SYNTHETIC: a test of this code, not row 119's gate (no roads_seed exists)")
    print(f"training road       : {g['train_road']} (train.build_env), seeds {TRAIN_SEEDS[0]}-{TRAIN_SEEDS[-1]}")
    print(f"preview horizons    : {', '.join(f'{h:g}' for h in g['horizons'])} s")
    print(f"neutral action      : {np.round(E.neutral_action(), 3)}\n")
    print(f"THE SWEEP: {len(rows)} grades, {100 * SWEEP_STEP:g} % apart over {100 * SWEEP_GRADES[0]:g}-"
          f"{100 * SWEEP_GRADES[1]:g} %, at {ER.V_KMH:g} km/h and {ER.T_AMB_K:g} K (epa_stats.c5_steps)")
    print(f"  held at {100 * rows[0]['grade']:g} %: {rows[0]['held']}. Each notch, with the grade 0.05 % below "
          "it and C5's smallest margin at it:")
    for c in cuts:
        print(f"    {100 * c['grade']:6.2f} %  (below: {100 * c['below']:.2f} %)  {c['from']} -> {c['to']}  margin "
              + ("-" if c["margin"] is None else f"{c['margin']:.4f}"))
    if not cuts:
        print("    none: the box holds one gear over the whole range")
    print(f"  band grade: {100 * g['band']:.2f} % (the last grade before the first notch)")
    if g["cvt"]:
        kd = g["kickdown"]
        print("  kickdown threshold (decision 40): " + ("not reached in the range" if kd is None
                                                       else f"{100 * kd:.2f} %"))
    print(f"\n{'check':46s} {'result':>7}   detail")
    print("-" * 96)
    for name, ok, detail in g["checks"]:
        print(f"{name:46s} {'PASS' if ok else 'NOT RUN' if ok is None else 'FAIL':>7}   {detail}")
    print("-" * 96)
    for kind, what in (("train", f"the {g['train_road']} roads"), ("d34", "decision 34's roads")):
        rs = [r for r in g["results"] if r["kind"] == kind and r.get("policy") == "neutral" and "error" not in r]
        if rs:
            print(f"FOR INFORMATION, NOT A PASS/FAIL (row 116): on {what}, neutral, steps asking under the torque "
                  f"floor {100 * np.mean([r['below_floor'] for r in rs]):.2f} % (worst road "
                  f"{100 * max(r['below_floor'] for r in rs):.2f} %), over the deliverable torque "
                  f"{100 * np.mean([r['above_deliverable'] for r in rs]):.2f} % (worst road "
                  f"{100 * max(r['above_deliverable'] for r in rs):.2f} %), {len(rs)} roads")
    oks = [c[1] for c in g["checks"]]
    if all(ok is True for ok in oks):
        print(f"\nAll checks pass on {g['engine']}." + (" SYNTHETIC roads: run it again on roads.json before "
                                                        "training." if g["synthetic"] else
                                                        " The reward is safe to train this engine against."))
        return 0
    if False not in oks:
        print(f"\nNOT COMPLETE: {oks.count(None)} check(s) did not run; each waits for the plant commit. Do not "
              "train this engine yet.")
        return 1
    print("\nSTOP. Do not train this engine until this passes. Diagnose WHICH check failed on WHICH road before\n"
          "changing anything -- mistake 17 was a scenario failure that looked like a weight problem.")
    return 1


# ------------------------------------------------------------------ check_roads.py --engine
def road_table(engine_id, *, train_road, roads_file, synthetic_seed, n, first_seed, jobs):
    """check_roads.py's table on one engine: the neutral action on n training roads (seeds from first_seed)
    and on every road of decision 34's set. Returns (training rows, decision-34 rows, the set's label)."""
    roads, _, label = d34_roads(roads_file=roads_file, synthetic_seed=synthetic_seed)
    base = dict(engine=engine_id, policy="neutral")
    tasks = ([dict(base, kind="train", train_road=train_road, seed=s) for s in range(first_seed, first_seed + n)]
             + [dict(base, kind="d34", road=r) for r in roads])
    res = pool_map(tasks, jobs=jobs)
    return [r for r in res if r["kind"] == "train"], [r for r in res if r["kind"] == "d34"], label

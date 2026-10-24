"""k3_knee.py -- an engine's K3 knee, its neutral run on the locked climb and the delivery check.

Build step 2, WP3 (23 October 2026): docs/build_step_2/PLAN.md section 5.9 items 3 and 4 and
section 7.7, as amendments E1, F3, F7 and F8 amend them; docs/build_step_2/WP3_INTERFACES.md
section 5.6. It reads no EPA data and fits nothing: every function takes a plant, and
calibrate_epa.py complete hands it the engine's frozen plant (or a candidate built from it).

THE K3 KNEE (decision 33, results/VALIDATION_DECISIONS.md:156; results/ENGINE_THRESHOLDS.md
section 1.2). Each engine's damage knee is set so that its baseline spends as long above the knee
on its locked climb as the B58's baseline spends above 1123 K: 413 s on the current B58 plant
(results/ENGINE_THRESHOLDS/ecu/k3_nominal.json, time_above_nominal_s). baseline_trace and
knee_for are thresholds/ecu_shift.py:80-97 lifted line for line, and with_knee and shifted_ecu
its :99-101 and :70-78. ecu_shift.py itself stays untouched: the contract JSON's `generators`
pins its sha256, and its functions are local to ecu_shift.one(), which runs a whole step of the
generator. The 413 is an argument here, never a literal: the contract's generator measured it
on the B58 (ecu_shift.one, above0), and the calibration hands it in from that measurement.

THE NEUTRAL RUN AND ITS IDENTITY (decision 39(b); amendment E1; the contract JSON's
model_form.neutral_action_identity). neutral_run drives the environment as baseline_trace does
and records what the identity needs: the baseline ECU's lambda_b and spark_b of each step, read
by wrapping the `step` of the environment's own BaselineECU INSTANCE (an instance attribute set
on one object; no class and no file is edited, amendment B5), and the action the environment
applied, env.prev_act after each step. SupervisoryTunerEnv.step calls self.ecu.step on that
instance once per step (engine_env.py:1283), so the wrapper sees every call; neutral_run counts
the calls and stops if they are not one per step, since the identity could then not be checked
without a plant change (WP3_INTERFACES.md section 11). The gearbox and the load loop are read
the same way, through the instance's gear_for (or a CVT's ratio_for) and _track_torque. Every
wrapper calls the original with the same arguments and returns its result unchanged; the test
shows the neutral run's trace bit-identical to baseline_trace's.

THE DELIVERY CHECK (PLAN.md 5.9 item 3; amendments F3, F8; decision 44). Over the steps of the
locked climb at t >= 188 s, the end of the grade's 8 s ramp from 180 s (engine_env.
make_grade_climb, GRADE_RAMP_S): the share of steps whose tracking error e_track exceeds
TRACK_TOL, the environment's own e_track (SupervisoryTunerEnv.step) against its TRACK_TOL 0.05;
the largest shortfall; the gear (or the CVT's branch and ratio), the rpm and the demand; the
margins to the threshold the box applies (Vehicle.shift_ceiling_nm at the held gear and each
rejected higher gear, decision 70; the CVT's kickdown_threshold_nm at N_eco, decision 40) and
the SHIFT_RPM_MAX bar's rpm margin (results/ENGINE_THRESHOLDS.md, C5); and the MAP against the
load loop's ceiling. Descriptive: decision 44 says what follows from it, and C5's gated margin is
epa_stats.c5_margin's, on decision 34's roads, never this.

Numbers live in the records this module returns, which calibrate_epa.py writes to complete.json;
nothing here prints (PLAN.md 8.1).
"""
import contextlib
import dataclasses
import hashlib
import inspect
import math

import numpy as np

import engine_env as E
import engines
import evaluate as V
from thresholds.ecu_shift import ECU_LOAD_KPA, SEL

# The class's own step, as imported: shifted_ecu patches the class and restores this, and refuses
# to stack one shift on another (a second patch would wrap the first and shift twice).
_ECU_STEP = E.BaselineECU.step

# The delivery check's population starts here (amendment F8, decision 44: "the tracking error over
# t >= 188 s"): the locked climb's grade is ramped from 180 s over engine_env.GRADE_RAMP_S, 8 s, so
# it holds its full value from 188 s. test_k3_knee checks it against the cycle (full_grade_from_s).
T_FROM_S = 188.0


def full_grade_from_s(cycle):
    """The first time (s) at which the cycle's grade reaches its largest value: where the locked
    climb's ramp ends. T_FROM_S is checked against it, so a ramp that moved would be seen."""
    g = np.asarray(cycle["grade"])
    return float(cycle["t"][int(np.flatnonzero(g == g.max())[0])])


def _plant(plant, who):
    """Refuse anything but an engines.Plant by name: there is no default engine (mistake 1)."""
    if not isinstance(plant, engines.Plant):
        raise TypeError(f"{who} needs an engines.Plant (engines.get or engines.build_candidate), not "
                        f"{type(plant).__name__}: there is no default engine (CLAUDE.md mistake 1)")
    return plant


def _python_float(x, what):
    """A value that becomes a record field is a finite Python float (amendment B10: under NEP 50 a
    NumPy scalar moves a result's bits wherever it meets a float32)."""
    if type(x) is not float:
        raise TypeError(f"{what} must be a Python float, not {type(x).__name__} ({x!r}): amendment B10")
    if not math.isfinite(x):
        raise ValueError(f"{what} must be finite, not {x!r}")
    return x


def _finite_knee(plant, who):
    """A knee that is not finite ends the episode at its first step (damage_rate goes NaN, so does
    the reward, and SupervisoryTunerEnv.step terminates; PLAN.md 5.9 item 3). Under
    DERIVING_PARAMS=1 an EPA plant's knee reads NaN until K3 sets it (derived.py), so every run
    before the knee is measured takes a provisional one, with_knee (amendment F7)."""
    k = plant.engine.damage.turb_knee_k
    if not math.isfinite(k):
        raise ValueError(f"{who}: the plant's turbine knee is {k!r}; run it with a provisional finite knee "
                         "(k3_knee.with_knee), since a NaN knee ends the episode at its first step")


# ------------------------------------------------------------------ the K3 knee (ecu_shift.py:70-101)
@dataclasses.dataclass(frozen=True, eq=False)
class BaselineTrace:
    """The neutral agent's housing temperature (K), lambda and spark (deg BTDC) at each step of the
    locked climb: info["t_turb"], info["lam"], info["spark"], as ecu_shift.one's baseline_trace
    returns them (float64 arrays, 719 steps on frozen episode 1 at dt 1 s)."""
    t_turb_k: np.ndarray
    lam: np.ndarray
    spark: np.ndarray


def baseline_trace(plant):
    """The neutral action on the plant's locked climb, frozen episode 1, dt 1 s: thresholds/
    ecu_shift.py:80-91 line for line, with the plant passed in. The neutral action's trace is
    called the baseline's there because the identity makes the two the same on lambda and spark
    (decision 39(b)); the housing is the agent's network, which ecu_shift reads (info["t_turb"]).
    Stops if the episode ended before its last step: a truncated trace has fewer than 719 values,
    and its 413th-highest would be another climb's (mistake 19)."""
    _plant(plant, "k3_knee.baseline_trace")
    _finite_knee(plant, "k3_knee.baseline_trace")
    seed, w = V.EPISODES[0]
    env = E.SupervisoryTunerEnv(V.episode_cycle(None, plant=plant), plant=plant, dt=V.DT, seed=seed)
    env.reset(seed=seed)
    env.w = np.asarray(w, dtype=np.float32)
    tt, lam, sp = [], [], []
    while True:
        _, _, term, trunc, info = env.step(np.array(E.neutral_action(), dtype=np.float32))
        tt.append(info["t_turb"]); lam.append(info["lam"]); sp.append(info["spark"])
        if term or trunc:
            break
    if term:
        raise RuntimeError(f"k3_knee.baseline_trace: the episode terminated at step {len(tt)} (a non-finite "
                           "reward), so the trace is not the climb's")
    return BaselineTrace(np.array(tt), np.array(lam), np.array(sp))


def knee_for(trace, seconds):
    """The knee K with exactly `seconds` of the trace above it (dt 1 s): the midpoint of the
    `seconds`-th and next highest values of the trace, thresholds/ecu_shift.py:93-97 line for
    line. `trace` is the housing temperature array (BaselineTrace.t_turb_k). At either end of the
    trace there is no midpoint, and ecu_shift's rule hands back an end value; k3() refuses those
    `seconds` before it gets here."""
    if isinstance(trace, BaselineTrace):
        raise TypeError("k3_knee.knee_for takes the housing temperature array, BaselineTrace.t_turb_k, "
                        "not the whole trace")
    s = np.sort(trace)[::-1]
    n = int(round(seconds))
    return float(0.5 * (s[n - 1] + s[n])) if 0 < n < len(s) else float(s[min(max(n, 0), len(s) - 1)])


def with_knee(plant, knee_k):
    """The plant with its turbine damage knee set to knee_k (K): thresholds/ecu_shift.py:99-101. A
    new plant by dataclasses.replace; the plant passed in is never changed (engines.get's
    docstring). knee_k must be a finite Python float (amendment B10)."""
    _plant(plant, "k3_knee.with_knee")
    _python_float(knee_k, "k3_knee.with_knee: knee_k")
    dmg = dataclasses.replace(plant.engine.damage, turb_knee_k=knee_k)
    return dataclasses.replace(plant, engine=dataclasses.replace(plant.engine, damage=dmg))


def with_driveline_eff(plant, eta):
    """The plant with its car's driveline efficiency set to eta: decision 44's sensitivity, the K3
    knee and the delivery also at eta 0.86 and 0.98 (amendment F3; the ends of the contract's
    span, thresholds/contract.py ETA_LO and ETA_HI). Every car record carries driveline_eff (the
    Supra's Car, EpaCar, CvtCar), and its vehicle model reads it in demand and in the shift test."""
    _plant(plant, "k3_knee.with_driveline_eff")
    _python_float(eta, "k3_knee.with_driveline_eff: eta")
    if not 0.0 < eta <= 1.0:
        raise ValueError(f"k3_knee.with_driveline_eff: eta {eta!r} is not an efficiency in (0, 1]")
    return dataclasses.replace(plant, car=dataclasses.replace(plant.car, driveline_eff=eta))


@contextlib.contextmanager
def shifted_ecu(ds, dl):
    """BaselineECU.step's output shifted while its own load input exceeds ECU_LOAD_KPA (100 kPa):
    spark by ds deg, clipped to the ECU's spark range, and lambda by dl. thresholds/ecu_shift.py:
    70-78 line for line, its ECU_LOAD_KPA imported, so the B58's k3_*.json knees can be reproduced
    (PLAN.md 7.7). The patch is of the class, as ecu_shift's is, so every BaselineECU in this
    process is shifted until the block exits; it is restored then, and a second shift inside the
    first is refused. ds and dl are Python floats (amendment B10)."""
    _python_float(ds, "k3_knee.shifted_ecu: ds")
    _python_float(dl, "k3_knee.shifted_ecu: dl")
    if E.BaselineECU.step is not _ECU_STEP:
        raise RuntimeError("k3_knee.shifted_ecu: BaselineECU.step is already patched; one shift at a time")
    orig = _ECU_STEP

    def step(self, rpm, map_kpa, iat_k, ect_k, knock_observed, dt):
        sp, lam, fan = orig(self, rpm, map_kpa, iat_k, ect_k, knock_observed, dt)
        if map_kpa > ECU_LOAD_KPA:
            c = self.cal
            sp = float(np.clip(sp + ds, c.spark_min, c.spark_max))
            lam = lam + dl
        return sp, lam, fan

    E.BaselineECU.step = step
    try:
        yield
    finally:
        E.BaselineECU.step = orig


def trace_sha256(trace):
    """sha256 of the trace's three arrays as little-endian float64 bytes, housing, lambda, spark, in
    that order: what complete.json records, so the knee's trace can be compared across runs."""
    h = hashlib.sha256()
    for a in (trace.t_turb_k, trace.lam, trace.spark):
        h.update(np.ascontiguousarray(a, dtype="<f8").tobytes())
    return h.hexdigest()


def traces_identical(a, b):
    """Whether two traces are the same to the bit: every array's bytes, and their lengths."""
    return all(x.shape == y.shape and np.ascontiguousarray(x, dtype="<f8").tobytes()
               == np.ascontiguousarray(y, dtype="<f8").tobytes()
               for x, y in ((a.t_turb_k, b.t_turb_k), (a.lam, b.lam), (a.spark, b.spark)))


def medians(trace):
    """ecu_shift.one's three trace figures (thresholds/ecu_shift.py:117-118): the peak housing in C
    and the lambda and spark medians over t 400-718 s (SEL, imported)."""
    return dict(base_peak_c=float(trace.t_turb_k.max() - 273.15),
                base_lambda_median_400_718=float(np.median(trace.lam[SEL])),
                base_spark_median_400_718=float(np.median(trace.spark[SEL])))


@dataclasses.dataclass(frozen=True)
class K3:
    """An engine's K3 knee (PLAN.md 5.9 item 4): the knee (K), the seconds of the trace above it,
    the seconds asked for, the trace's sha256 and whether a second provisional knee gave the trace
    back bit for bit (the proof that the knee cannot move the neutral trajectory it is set on)."""
    seconds: int
    knee_k: float
    time_above_knee_s: int
    trace_sha256: str
    second_knee_identical: bool

    def as_json(self):
        return dataclasses.asdict(self)


def k3(plant, *, seconds, provisional):
    """Decision 33's knee on this plant: knee_for(the neutral trace, seconds), seconds the B58's
    413 (k3_nominal.json's time_above_nominal_s, handed in by the caller). The trace is run twice,
    at the two provisional knees `provisional` (two different finite Python floats, amendment F7),
    and the second must give it back bit for bit; the first is the one the knee is read off.
    `seconds` must leave a value above and below it (1 to steps - 1), where knee_for's midpoint
    exists. Returns K3; calibrate_epa.complete asserts second_knee_identical (a False is a coding
    defect, MD section 7) and writes the record."""
    _plant(plant, "k3_knee.k3")
    if type(seconds) is not int:
        raise TypeError(f"k3_knee.k3: seconds must be a Python int, not {type(seconds).__name__} ({seconds!r})")
    if len(provisional) != 2:
        raise ValueError("k3_knee.k3: provisional is two knees, the trace's and the second one's")
    ka, kb = (_python_float(k, "k3_knee.k3: a provisional knee") for k in provisional)
    if ka == kb:
        raise ValueError("k3_knee.k3: the two provisional knees are equal, so the second run could not "
                         "show that the knee leaves the trace unchanged (mistake 12)")
    tr = baseline_trace(with_knee(plant, ka))
    tr2 = baseline_trace(with_knee(plant, kb))
    if not 0 < seconds < len(tr.t_turb_k):
        raise ValueError(f"k3_knee.k3: {seconds} s leaves no midpoint on a {len(tr.t_turb_k)}-step trace")
    knee = knee_for(tr.t_turb_k, seconds)
    return K3(seconds=seconds, knee_k=knee, time_above_knee_s=int((tr.t_turb_k > knee).sum()),
              trace_sha256=trace_sha256(tr), second_knee_identical=traces_identical(tr, tr2))


# ------------------------------------------------------------------ the neutral run (E1, F3, F8)
@dataclasses.dataclass(frozen=True, eq=False)
class NeutralRun:
    """One neutral episode, step by step (n steps; every array has length n):

      t            the cycle's time at the step (s): cycle["t"][k], k the index the step reads
      t_turb_k, lam, spark   info["t_turb"], info["lam"], info["spark"]: the agent's, as BaselineTrace
      lam_b, spark_b         the baseline ECU's outputs of the step (BaselineECU.step's return)
      act          (n, 5) float32: the action the step applied, env.prev_act after it
      torque, torque_req     the agent's delivered torque and the request (Nm)
      e_track      the environment's tracking error, |request - torque| / max(request, 40 Nm)
      rpm, map_kpa env.rpm, env.map_kpa (the agent's load loop's MAP after the step)
      ceiling_kpa  the agent's loop's MAP ceiling at its last inner iteration (_track_torque)
      v_mps, force_n         the road speed and the tractive force the gearbox was given
      held         per step, the 1-based gear (a stepped box) or the CVT's branch, as a str
      gear_index   the 0-based gear gear_for returned; -1 on a CVT
      cvt_ratio, n_eco, t_eco   a CVT's ratio and economy point (CvtVehicle.ratio_for); NaN where
                   absent (a stepped box; the CVT's low-speed branch has no N_eco)
    plant_id and box ("stepped" or "cvt") name what ran; ecu_calls counts BaselineECU.step's calls,
    one per step."""
    t: np.ndarray
    t_turb_k: np.ndarray
    lam: np.ndarray
    spark: np.ndarray
    lam_b: np.ndarray
    spark_b: np.ndarray
    act: np.ndarray
    torque: np.ndarray
    torque_req: np.ndarray
    e_track: np.ndarray
    rpm: np.ndarray
    map_kpa: np.ndarray
    ceiling_kpa: np.ndarray
    v_mps: np.ndarray
    force_n: np.ndarray
    held: tuple
    gear_index: np.ndarray
    cvt_ratio: np.ndarray
    n_eco: np.ndarray
    t_eco: np.ndarray
    plant_id: str
    box: str
    ecu_calls: int

    @property
    def steps(self):
        return len(self.t)

    def trace(self):
        """The run's housing, lambda and spark as a BaselineTrace."""
        return BaselineTrace(self.t_turb_k, self.lam, self.spark)


# _track_torque's parameters, so a wrapped call's boost trim and state are read by name
_TRACK_SIG = inspect.signature(E.SupervisoryTunerEnv._track_torque)


def neutral_run(plant, *, cycle, seed, weights):
    """The neutral action on `cycle` (the plant's locked climb: V.episode_cycle(None, plant=...)),
    at dt evaluate.DT, the episode seeded `seed` with its weights pinned to `weights` after reset,
    as baseline_trace and evaluate.run_episode do. Records NeutralRun. The environment's own
    BaselineECU instance's step, its vehicle's gear_for (or ratio_for) and its _track_torque are
    wrapped on the instance to read what they were given and returned (module docstring); each is
    counted, and a count that is not one per step (two for the load loop: the baseline's and the
    agent's) stops the run, since what it records would not be every call (WP3_INTERFACES.md
    section 11)."""
    _plant(plant, "k3_knee.neutral_run")
    _finite_knee(plant, "k3_knee.neutral_run")
    env = E.SupervisoryTunerEnv(cycle, plant=plant, dt=V.DT, seed=seed)
    env.reset(seed=seed)
    env.w = np.asarray(weights, dtype=np.float32)
    eng = plant.engine
    cvt = isinstance(env.veh, E.CvtVehicle)
    ecu_out, box_calls, agent_track = [], [], []

    orig_ecu_step = env.ecu.step

    def ecu_step(*a, **k):
        out = orig_ecu_step(*a, **k)
        ecu_out.append(out)
        return out
    env.ecu.step = ecu_step

    if cvt:
        orig_ratio_for = env.veh.ratio_for

        def ratio_for(*a, **k):
            out = orig_ratio_for(*a, **k)
            b = inspect.signature(orig_ratio_for).bind(*a, **k).arguments
            box_calls.append((b["v_mps"], b["force_n"], out))
            return out
        env.veh.ratio_for = ratio_for
    else:
        orig_gear_for = env.veh.gear_for

        def gear_for(*a, **k):
            g = orig_gear_for(*a, **k)
            b = inspect.signature(orig_gear_for).bind(*a, **k).arguments
            box_calls.append((b["v_mps"], b.get("force_n"), g))
            return g
        env.veh.gear_for = gear_for

    orig_track = env._track_torque
    track_calls = [0]

    def track(*a, **k):
        out, mp = orig_track(*a, **k)
        track_calls[0] += 1
        b = _TRACK_SIG.bind(env, *a, **k).arguments
        if b["state"] is env.pi_agent:
            # the ceiling _track_torque applied at its last inner iteration, from the out it returns
            # (engine_env.SupervisoryTunerEnv._track_torque): the same expression on the same values
            ceil = min(env.MAP_CEIL_KPA,
                       E.boost_ceiling_kpa(out["mdot_air"], env.cycle["t_amb"], env.inlet_kpa,
                                           engine=eng) + b["boost_trim"])
            agent_track.append(float(ceil))
        return out, mp
    env._track_torque = track

    rows = []
    while True:
        k = env.k
        before = (len(ecu_out), len(box_calls), track_calls[0], len(agent_track))
        _, r, term, trunc, info = env.step(np.array(E.neutral_action(), dtype=np.float32))
        after = (len(ecu_out), len(box_calls), track_calls[0], len(agent_track))
        if tuple(y - x for x, y in zip(before, after)) != (1, 1, 2, 1):
            raise RuntimeError(f"k3_knee.neutral_run: at step {k} the wrapped calls were "
                               f"{tuple(y - x for x, y in zip(before, after))} (ECU step, gearbox, load loop, "
                               "agent's loop), not (1, 1, 2, 1): the instance wrappers do not see every call, "
                               "and the identity cannot be checked without a plant change (WP3_INTERFACES.md "
                               "section 11; amendment B5): stop and report it")
        sp_b, lam_b, _ = ecu_out[-1]
        tq, treq = info["torque"], info["torque_req"]
        e = abs(treq - tq) / max(treq, 40.0)
        # the environment's own tracking error, checked against the reward term it feeds
        # (SupervisoryTunerEnv.step): a formula that drifted from the environment's stops here
        if info["r_resp"] != -(e + E.TRACK_HINGE * max(0.0, e - E.TRACK_TOL)):
            raise RuntimeError(f"k3_knee.neutral_run: at step {k} the tracking error recomputed here does not "
                               "give the environment's r_resp back: SupervisoryTunerEnv.step's e_track changed")
        v, f, box = box_calls[-1]
        if cvt:
            ratio, _, branch, n_eco, t_eco = box
            held, gi = branch, -1
            cr = float(ratio)
            ne = float("nan") if n_eco is None else float(n_eco)
            te = float("nan") if t_eco is None else float(t_eco)
        else:
            held, gi, cr, ne, te = str(box + 1), box, float("nan"), float("nan"), float("nan")
        rows.append((float(cycle["t"][k]), info["t_turb"], info["lam"], info["spark"], lam_b, sp_b,
                     env.prev_act.copy(), tq, treq, e, env.rpm, env.map_kpa, agent_track[-1],
                     float(v), float(f), held, gi, cr, ne, te))
        if term or trunc:
            break
    if term:
        raise RuntimeError(f"k3_knee.neutral_run: the episode terminated at step {len(rows)} (a non-finite "
                           "reward), so the run is not the climb's")
    col = list(zip(*rows))
    arr = lambda i: np.array(col[i], dtype=np.float64)  # noqa: E731
    return NeutralRun(
        t=arr(0), t_turb_k=arr(1), lam=arr(2), spark=arr(3), lam_b=arr(4), spark_b=arr(5),
        act=np.array(col[6], dtype=np.float32), torque=arr(7), torque_req=arr(8), e_track=arr(9),
        rpm=arr(10), map_kpa=arr(11), ceiling_kpa=arr(12), v_mps=arr(13), force_n=arr(14),
        held=tuple(col[15]), gear_index=np.array(col[16], dtype=np.int64), cvt_ratio=arr(17),
        n_eco=arr(18), t_eco=arr(19), plant_id=plant.id, box="cvt" if cvt else "stepped",
        ecu_calls=len(ecu_out))


# ------------------------------------------------------------------ the identity (39(b), E1)
def clip_contacts(x, lo, hi):
    """The steps at which a channel clip changed the value it was given: np.clip(x, lo, hi) != x
    (the contract's `contact`). x is the float32 sum SupervisoryTunerEnv.step forms, baseline plus
    trim, and the comparison is NumPy's own promotion of x and the bounds, as the environment's
    clip is: a Python float bound is cast to float32 against a float32 x (NEP 50), a NumPy float64
    one makes the clip and the comparison float64. A value equal to a bound is not a contact. The
    caller decides which bounds are legitimate; neutral_identity asserts Python floats first."""
    x = np.asarray(x)
    return int(np.count_nonzero(np.clip(x, lo, hi) != x))


@dataclasses.dataclass(frozen=True)
class Identity:
    """The neutral-action identity over one run (the contract's model_form.neutral_action_identity):
    the largest |agent - float32(baseline)| on each channel, which must be 0.0, the clip contacts
    on each, which must be 0, that the four bounds were Python floats, and the steps compared."""
    max_abs_dlam: float
    max_abs_dspark: float
    contacts_lam: int
    contacts_spark: int
    bounds_are_python_floats: bool
    steps: int

    def as_json(self):
        return dataclasses.asdict(self)

    @property
    def holds(self):
        return (self.max_abs_dlam == 0.0 and self.max_abs_dspark == 0.0 and self.contacts_lam == 0
                and self.contacts_spark == 0 and self.bounds_are_python_floats)


def neutral_identity(run, *, ecu):
    """Decision 39(b)'s identity on a NeutralRun, with `ecu` the engine's EcuCal (plant.engine.ecu)
    whose four bounds the environment clips with (engine_env.py:1310-1316). First asserts that all
    four are Python floats, type(x) is float (the contract: a float64 bound would make the clip
    compare float64 and count float32(lam_floor) < lam_floor as a contact); then, at every step:

      lambda  x = float32(lam_b) + act[1], the float32 sum lam_b + trim of SupervisoryTunerEnv.step
              (NEP 50: a Python float meets a float32 trim as a float32); the agent's lambda must
              equal float32(lam_b), and np.clip(x, lam_floor, lam_ceiling) must leave x unchanged
      spark   the same with spark_b, act[0], spark_min and spark_max

    Returns Identity; a difference or a contact is a coding defect (MD section 7, on_failure.identity),
    which the caller reports. The fan and pump are not compared (the contract's not_compared)."""
    bounds = dict(lam_floor=ecu.lam_floor, lam_ceiling=ecu.lam_ceiling, spark_min=ecu.spark_min,
                  spark_max=ecu.spark_max)
    bad = {n: type(v).__name__ for n, v in bounds.items() if type(v) is not float}
    if bad:
        raise TypeError(f"k3_knee.neutral_identity: the clip bounds {bad} are not Python floats; the "
                        "environment would compare in float64 and the identity is defined in float32 (the "
                        "contract's model_form.neutral_action_identity, contact)")
    lam_b32 = run.lam_b.astype(np.float32)
    sp_b32 = run.spark_b.astype(np.float32)
    x_lam = lam_b32 + run.act[:, 1]
    x_sp = sp_b32 + run.act[:, 0]
    if x_lam.dtype != np.float32 or x_sp.dtype != np.float32:
        raise TypeError("k3_knee.neutral_identity: the sums are not float32; the run's act must be float32")
    return Identity(
        max_abs_dlam=float(np.max(np.abs(run.lam - lam_b32.astype(np.float64)))),
        max_abs_dspark=float(np.max(np.abs(run.spark - sp_b32.astype(np.float64)))),
        contacts_lam=clip_contacts(x_lam, ecu.lam_floor, ecu.lam_ceiling),
        contacts_spark=clip_contacts(x_sp, ecu.spark_min, ecu.spark_max),
        bounds_are_python_floats=True, steps=run.steps)


# ------------------------------------------------------------------ the delivery check (F3, F8)
def _spread(x):
    """min, median and max of a non-empty float array, as Python floats."""
    x = np.asarray(x, dtype=np.float64)
    return dict(min=float(np.min(x)), median=float(np.median(x)), max=float(np.max(x)))


def _gear_rpm(veh, v, ratio):
    """The engine speed at road speed v in this overall ratio, as Vehicle.gear_for computes it."""
    return v / veh.wheel_r * ratio * 60.0 / (2 * np.pi)


def _gear_demand(veh, f, ratio):
    """The torque this tractive force asks in this overall ratio, as Vehicle.gear_for and demand do."""
    return f * veh.wheel_r / max(ratio, .1) / veh.driveline_eff


@dataclasses.dataclass(frozen=True)
class Delivery:
    """The delivery check over the steps at t >= t_from_s (PLAN.md 5.9 item 3; amendments F3, F8;
    decision 44). Each spread is {min, median, max}. A margin is demand/threshold - 1, signed
    (negative below the threshold), the statistic whose absolute value C5 gates on decision 34's
    roads (results/ENGINE_THRESHOLDS.md, C5); here it is reported, never gated.

      steps                  the population's size
      share_over_track_tol   share of those steps with e_track > TRACK_TOL (0.05)
      largest_shortfall_nm   max(request - torque), signed: at or below 0, no step fell short
      held                   {"box", "counts": {gear or branch: steps}} and, on a CVT, its ratio's spread
      rpm, demand_nm         spreads of env.rpm and the request
      margin_to_threshold    stepped: "held", the held gear's margin to shift_ceiling_nm at its own
                             gear_for rpm (its lowest gear, which takes no torque decision, counted
                             apart in "held_lowest_steps"); "rejected_higher", the least margin of a
                             rejected higher gear at its own rpm, None if no step rejected one.
                             CVT: "economy_point", T_eco/kickdown_threshold_nm(N_eco) - 1 on the
                             steps with an N_eco
      bar_rpm_margin         stepped: the next lower gear's gear_for rpm - SHIFT_RPM_MAX, in rpm and
                             as a fraction of SHIFT_RPM_MAX (positive while the bar holds), with the
                             steps it holds at; None on a CVT, or when every step is in the lowest gear
      map_vs_ceiling_kpa     the agent's loop's ceiling - MAP, and the steps at the ceiling"""
    t_from_s: float
    steps: int
    share_over_track_tol: float
    largest_shortfall_nm: float
    held: dict
    rpm: dict
    demand_nm: dict
    margin_to_threshold: dict
    bar_rpm_margin: object
    map_vs_ceiling_kpa: dict

    def as_json(self):
        return dataclasses.asdict(self)


def delivery(run, *, plant, t_from_s):
    """The delivery check of a NeutralRun of this plant over its steps at t >= t_from_s, which is
    T_FROM_S, 188 s, on the locked climb (amendment F8). The thresholds are the plant's own car's,
    from a fresh vehicle model (engine_env.vehicle_for), at the speed, force and gear the run's
    gearbox was given and chose; the held gear's demand is the request the environment computed."""
    _plant(plant, "k3_knee.delivery")
    t_from_s = _python_float(t_from_s, "k3_knee.delivery: t_from_s")
    if run.plant_id != plant.id:
        raise ValueError(f"k3_knee.delivery: the run is of {run.plant_id}, the plant {plant.id}")
    veh = E.vehicle_for(plant.car)
    cvt = isinstance(veh, E.CvtVehicle)
    if cvt != (run.box == "cvt"):
        raise ValueError(f"k3_knee.delivery: the run's box is {run.box}, the plant's car's is "
                         f"{'cvt' if cvt else 'stepped'}")
    idx = np.flatnonzero(run.t >= t_from_s)
    if len(idx) == 0:
        raise ValueError(f"k3_knee.delivery: no step of the run is at t >= {t_from_s!r} s")
    counts = {}
    for i in idx:
        counts[run.held[i]] = counts.get(run.held[i], 0) + 1
    held = {"box": run.box, "counts": dict(sorted(counts.items()))}
    if cvt:
        held["ratio"] = _spread(run.cvt_ratio[idx])
        eco = [float(run.t_eco[i] / veh.kickdown_threshold_nm(run.n_eco[i]) - 1.0)
               for i in idx if math.isfinite(run.n_eco[i])]
        margin = {"threshold": "CvtVehicle.kickdown_threshold_nm(N_eco)",
                  "economy_point": _spread(eco) if eco else None, "steps_without_n_eco": len(idx) - len(eco)}
        bar = None
    else:
        held_m, lowest, rejected, bar_rpm = [], 0, [], []
        for i in idx:
            g, v, f = int(run.gear_index[i]), float(run.v_mps[i]), float(run.force_n[i])
            ratio = veh.gears[g] * veh.final_drive
            m = _gear_demand(veh, f, ratio) / veh.shift_ceiling_nm(_gear_rpm(veh, v, ratio)) - 1.0
            if g == 0:
                lowest += 1
            else:
                held_m.append(m)
                lower = veh.gears[g - 1] * veh.final_drive
                bar_rpm.append(_gear_rpm(veh, v, lower) - veh.SHIFT_RPM_MAX)
            for h in range(g + 1, veh.gear_for(v) + 1):        # the higher gears the speed allows
                rh = veh.gears[h] * veh.final_drive
                rejected.append(_gear_demand(veh, f, rh) / veh.shift_ceiling_nm(_gear_rpm(veh, v, rh)) - 1.0)
        margin = {"threshold": "Vehicle.shift_ceiling_nm",
                  "held": _spread(held_m) if held_m else None, "held_lowest_steps": lowest,
                  "rejected_higher": float(min(rejected)) if rejected else None,
                  "rejected_higher_steps": len(rejected)}
        bar = None if not bar_rpm else {
            "rpm": _spread(bar_rpm), "fraction": _spread(np.asarray(bar_rpm) / veh.SHIFT_RPM_MAX),
            "barred_steps": int(np.count_nonzero(np.asarray(bar_rpm) > 0.0)),
            "shift_rpm_max": float(veh.SHIFT_RPM_MAX)}
    head = run.ceiling_kpa[idx] - run.map_kpa[idx]
    return Delivery(
        t_from_s=t_from_s, steps=int(len(idx)),
        share_over_track_tol=float(np.count_nonzero(run.e_track[idx] > E.TRACK_TOL) / len(idx)),
        largest_shortfall_nm=float(np.max(run.torque_req[idx] - run.torque[idx])),
        held=held, rpm=_spread(run.rpm[idx]), demand_nm=_spread(run.torque_req[idx]),
        margin_to_threshold=margin, bar_rpm_margin=bar,
        map_vs_ceiling_kpa={**_spread(head), "at_ceiling_steps": int(np.count_nonzero(head <= 0.0))})


# ------------------------------------------------------------------ completion measurements (5.9 items 1, 2, 8)
# Added by WP3's integration, 23 October 2026: calibrate_epa.py complete composes the completion and
# imports no plant module (WP3_INTERFACES.md 3.1), so the measurements that drive the environment
# live here, beside the neutral run, each a function of the plant alone (so the completion's ordered
# pool can run them side by side).

# The torque floor's rule, the B58's (engine_specs/b58.toml [loop] torque_floor_nm, DERIVED_ONCE: "1.25
# x the 12.0 Nm the engine makes with the throttle shut at 1200 rpm and 42 C", measured 8 October 2026
# with _track_torque at a request of 0), applied to each engine at max(FLOOR_RPM, its rpm_min) (PLAN.md
# 5.9 item 2): DESIGN, carried with its source, never refitted. The start of the closed-throttle loop is
# wide_air.closed_throttle_nm's (30 kPa, the throttle shut) and its reading the same: the largest torque
# over the second half of the settled window.
FLOOR_FACTOR = 1.25
FLOOR_RPM = 1200.0
CLOSED_MAP_START_KPA = 30.0


@contextlib.contextmanager
def _counted_loop():
    """SupervisoryTunerEnv._track_torque wrapped at the class while the block runs, recording each call's
    knock integral (out["ki"], the value measure_deliverable_torque turns into the ECU's knock flag), and
    restored after; a second wrap inside the first is refused. The wrapper calls the original with the
    same arguments and returns its result unchanged, so the measurement is the environment's own
    (PLAN.md 5.9 item 1: "the knock-flag duty during the measurement")."""
    orig = E.SupervisoryTunerEnv._track_torque
    if getattr(orig, "_k3_counted", False):
        raise RuntimeError("k3_knee._counted_loop: the load loop is already wrapped; one count at a time")
    seen = []

    def track(self, *a, **k):
        out, mp = orig(self, *a, **k)
        seen.append(float(out["ki"]))
        return out, mp
    track._k3_counted = True
    E.SupervisoryTunerEnv._track_torque = track
    try:
        yield seen
    finally:
        E.SupervisoryTunerEnv._track_torque = orig


@dataclasses.dataclass(frozen=True)
class DeliverableTable:
    """PLAN.md 5.9 item 1: engine_env.measure_deliverable_torque at the car's own grid and conditions
    (plant.car.table_*), with `settle` settling steps per speed. `table` is [[rpm (int), Nm (float)]]
    rounded to 0.1 Nm as derive_params.py rounds the B58's; `raw` the unrounded pairs; knock_flag_duty
    the share of the load loop's calls whose knock integral is above the ECU's knock_detect_ki (the
    flag the measurement feeds back), over `calls` calls."""
    settle: int
    table: tuple
    raw: tuple
    knock_flag_duty: float
    calls: int

    def as_json(self):
        return {"settle": self.settle, "table": [list(p) for p in self.table], "raw": [list(p) for p in self.raw],
                "knock_flag_duty": self.knock_flag_duty, "calls": self.calls}


def deliverable_table(plant, *, settle):
    """The plant's deliverable-torque table, measured as derive_params.py measures the B58's
    (engine_env.measure_deliverable_torque(plant.car.table_rpms, plant=...)), at `settle` settling steps
    (an int: the car's table_settle for the table, 60 for the re-measurement PLAN.md 5.9 item 1 asks),
    with the knock flag's duty during it. The plant passed in is never changed."""
    _plant(plant, "k3_knee.deliverable_table")
    if type(settle) is not int or settle < 2:
        raise TypeError(f"k3_knee.deliverable_table: settle must be a Python int >= 2, not {settle!r}")
    p = plant if settle == plant.car.table_settle else dataclasses.replace(
        plant, car=dataclasses.replace(plant.car, table_settle=settle))
    with _counted_loop() as kis:
        raw = E.measure_deliverable_torque(p.car.table_rpms, plant=p)
    thr = plant.engine.ecu.knock_detect_ki
    return DeliverableTable(settle=settle, table=tuple((int(r), round(float(t), 1)) for r, t in raw),
                            raw=tuple((int(r), float(t)) for r, t in raw),
                            knock_flag_duty=float(sum(1 for k in kis if k > thr) / len(kis)) if kis else 0.0,
                            calls=len(kis))


@dataclasses.dataclass(frozen=True)
class TorqueFloor:
    """PLAN.md 5.9 item 2: FLOOR_FACTOR x the closed-throttle torque at `rpm` and the car's table ambient
    and block (`t_amb_k`), rounded to 0.1 Nm as the table is; `closed_nm` the measurement. Labelled an
    extrapolation: FMEP was fitted on fired rows only, and a shut throttle is below every one of them."""
    nm: float
    closed_nm: float
    rpm: float
    t_amb_k: float
    settle: int
    rule: str
    extrapolation: bool

    def as_json(self):
        return dataclasses.asdict(self)


def torque_floor(plant, *, settle):
    """The torque floor (PLAN.md 5.9 item 2), by the B58's rule (FLOOR_FACTOR, FLOOR_RPM): the
    environment's own load loop at a request of 0 Nm (SupervisoryTunerEnv._track_torque, the loop
    measure_deliverable_torque runs at 1000 Nm), BaselineECU.step for spark and lambda with its knock
    feedback, the ECU's cam on a form-D engine, at max(FLOOR_RPM, the car's rpm_min) and the car's
    table ambient and block, `settle` steps; the largest torque over the second half (wide_air.
    closed_throttle_nm's reading)."""
    _plant(plant, "k3_knee.torque_floor")
    if type(settle) is not int or settle < 2:
        raise TypeError(f"k3_knee.torque_floor: settle must be a Python int >= 2, not {settle!r}")
    car, sc = plant.car, plant.scenario
    rpm = float(max(FLOOR_RPM, float(car.rpm_min)))
    t_amb, t_block = car.table_t_amb, car.table_t_block
    env = E.SupervisoryTunerEnv(E.make_grade_climb(duration=60.0, dt=1.0, t_amb=t_amb, grade=sc.grade,
                                                   v_kmh=sc.v_kmh), plant=plant, dt=1.0, seed=0)
    env.reset(seed=0)
    iat = E.charge_temperature(t_amb, t_block, engine=plant.engine)
    ecu, state, mp, knock, hist = E.BaselineECU(plant.engine.ecu), {}, CLOSED_MAP_START_KPA, False, []
    for _ in range(settle):
        sp, lam, _ = ecu.step(rpm, mp, iat, t_block, knock, 1.0)
        cam = ecu.cam_deg(rpm, mp)
        r, mp = env._track_torque(0.0, rpm, iat, t_block, sp, lam, 0.0, state, cam_deg=cam)
        knock = r["ki"] > ecu.cal.knock_detect_ki
        hist.append(r["torque"])
    closed = float(max(hist[settle // 2:]))
    return TorqueFloor(nm=round(FLOOR_FACTOR * closed, 1), closed_nm=closed, rpm=rpm, t_amb_k=float(t_amb),
                       settle=settle, extrapolation=True,
                       rule=(f"{FLOOR_FACTOR} x the torque with the throttle shut (the load loop at a request of 0 "
                             f"Nm) at max({FLOOR_RPM:g} rpm, rpm_min) and the car's table ambient, the B58's rule "
                             "(engine_specs/b58.toml [loop] torque_floor_nm); an extrapolation below every fired "
                             "calibration row"))


def locked_neutral_run(plant):
    """neutral_run on the plant's own locked climb, frozen episode 1 (evaluate.episode_cycle(None, ...)
    and evaluate.EPISODES[0], as baseline_trace runs it): the run PLAN.md 5.9 item 3's delivery check and
    the neutral-action identity read, for a caller that imports no plant module (calibrate_epa.py)."""
    _plant(plant, "k3_knee.locked_neutral_run")
    seed, w = V.EPISODES[0]
    return neutral_run(plant, cycle=V.episode_cycle(None, plant=plant), seed=seed, weights=w)


def damage_readings(plant):
    """E6 row 7's two readings of the baseline's damage on the locked climb (PLAN.md 5.9 item 8;
    evaluate.run_episode's DAMAGE TWO WAYS): the neutral action on frozen episode 1, its damage with the
    knock term (`total`) and without (`thermal`), and the knock term's share of the total. The plant's
    knee must be finite (a NaN knee ends the episode)."""
    _plant(plant, "k3_knee.damage_readings")
    _finite_knee(plant, "k3_knee.damage_readings")
    seed, w = V.EPISODES[0]
    neutral = np.array(E.neutral_action(), dtype=np.float32)
    res = V.run_episode(lambda env, obs: neutral, seed, w, plant=plant)
    total, thermal = float(res["damage"]), float(res["damage_thermal"])
    return {"total": total, "thermal": thermal,
            "knock_share": None if total == 0.0 else float((total - thermal) / total)}

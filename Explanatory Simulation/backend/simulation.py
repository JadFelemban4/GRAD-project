"""In-memory adapter around the source project's engine environment.

This module never opens a vehicle connection and never persists a session.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
from pathlib import Path
import re
import sys
import threading
import uuid

import numpy as np


# Keep read-only imports from the parent project from leaving __pycache__ in
# that source tree.  The bridge's own module cache may also remain in-memory.
sys.dont_write_bytecode = True
EX_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = EX_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from check_premise import p_grade_now, p_neutral, p_predictive, p_reactive  # noqa: E402
from engine_env import (  # noqa: E402
    ACT_HI,
    ACT_LO,
    OBS_DIM,
    PREVIEW_S,
    BaselineECU,
    SupervisoryTunerEnv,
    Vehicle,
    damage_rate,
    make_grade_climb,
    make_terrain,
)


MAX_SESSIONS = 12
MAX_STEPS_PER_CALL = 120
EPISODE_DURATION_S = 900.0
SIM_DT = 1.0
_SESSIONS: dict[str, "SimulationSession"] = {}
_LOCK = threading.RLock()
_ACTOR_RE = re.compile(r"^(sighted|blind)_seed([0-9])$")


def _finite_number(value, name: str, low: float, high: float) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number") from None
    if not math.isfinite(out) or not low <= out <= high:
        raise ValueError(f"{name} must be between {low:g} and {high:g}")
    return out


def physical_to_normalized(values) -> list[float]:
    """Convert five physical actuator commands to the Gym policy's [-1,1]."""
    arr = np.asarray(values, dtype=np.float64)
    if arr.shape != (5,) or not np.all(np.isfinite(arr)):
        raise ValueError("trims must be five finite physical actuator values")
    if np.any(arr < ACT_LO) or np.any(arr > ACT_HI):
        raise ValueError("trims are outside the physical action bounds")
    result = 2.0 * (arr - ACT_LO) / (ACT_HI - ACT_LO) - 1.0
    result[arr == ACT_LO] = -1.0
    result[arr == ACT_HI] = 1.0
    return result.astype(np.float32).tolist()


def _current_derived_inputs() -> dict:
    import derived

    return dict(derived.all_params().get("_inputs") or {})


def _load_actor(policy: str) -> tuple[dict[str, np.ndarray], dict]:
    match = _ACTOR_RE.fullmatch(policy)
    if not match:
        raise ValueError(f"unsupported policy {policy!r}")
    tag = policy
    folder = PROJECT_ROOT / "results" / "agents" / "terrain_dt1" / tag
    config_path, weights_path = folder / "config.json", folder / "policy.npz"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"actor {tag} has no readable run config: {exc}") from None
    expected = _current_derived_inputs()
    recorded = config.get("plant_inputs") or {}
    if not expected or recorded.get("data_sha1") != expected.get("data_sha1") \
            or recorded.get("raw_logs") != expected.get("raw_logs"):
        raise ValueError(f"actor {tag} derived-data fingerprint does not match this checkout")
    if config.get("dt") != SIM_DT or config.get("preview") != (match.group(1) == "sighted"):
        raise ValueError(f"actor {tag} has incompatible step size or preview training mode")
    if config.get("sac", {}).get("net_arch") != "[256, 256]":
        raise ValueError(f"actor {tag} has an unsupported network architecture")
    try:
        with np.load(weights_path, allow_pickle=False) as z:
            weights = {k: np.asarray(z[k], dtype=np.float32) for k in z.files}
    except (OSError, ValueError) as exc:
        raise ValueError(f"actor {tag} has no readable exported weights: {exc}") from None
    required_shapes = {
        "latent_pi__0__weight": (256, OBS_DIM), "latent_pi__0__bias": (256,),
        "latent_pi__2__weight": (256, 256), "latent_pi__2__bias": (256,),
        "mu__weight": (5, 256), "mu__bias": (5,),
    }
    if any(k not in weights or weights[k].shape != shape for k, shape in required_shapes.items()):
        raise ValueError(f"actor {tag} exported weights do not match the supported SAC actor")
    if any(not np.all(np.isfinite(weights[k])) for k in required_shapes):
        raise ValueError(f"actor {tag} contains non-finite weights")
    provenance = {
        "tag": tag,
        "algorithm": "SAC deterministic actor mean",
        "derived_data_match": True,
        "code_fingerprint": "unavailable",
        "educational_rerun_only": True,
        "warning": "Actor weights have no fatal source-code fingerprint; this rerun is not a scored evaluation.",
    }
    return weights, provenance


def _actor_action(weights: dict[str, np.ndarray], obs: np.ndarray) -> np.ndarray:
    """SB3 SAC deterministic actor: two ReLU layers, then tanh(mu)."""
    x = np.asarray(obs, dtype=np.float32)
    for layer in ("latent_pi__0", "latent_pi__2"):
        x = np.maximum(weights[layer + "__weight"] @ x + weights[layer + "__bias"], 0.0)
    return np.tanh(weights["mu__weight"] @ x + weights["mu__bias"]).astype(np.float32)


class CapturingBaselineECU(BaselineECU):
    def step(self, *args, **kwargs):
        spark, lam, fan = super().step(*args, **kwargs)
        self.last_command = {"spark": float(spark), "lam": float(lam), "fan": float(fan)}
        return spark, lam, fan


class CapturingEnv(SupervisoryTunerEnv):
    """Capture the existing parallel baseline output without touching core code."""

    def _track_torque(self, *args, **kwargs):
        out, mp = super()._track_torque(*args, **kwargs)
        if len(args) >= 8 and args[7] is self.pi_base:
            self.last_baseline_out = dict(out)
            self.last_baseline_map = float(mp)
        return out, mp

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ecu = CapturingBaselineECU()


@dataclass
class SimulationSession:
    id: str
    env: CapturingEnv
    scenario: str
    policy: str
    preview: bool
    seed: int
    road: dict
    actor_weights: dict[str, np.ndarray] | None = None
    provenance: dict = field(default_factory=dict)
    done: bool = False


def _cycle_for(scenario: str, seed: int) -> tuple[dict, dict]:
    rng = np.random.default_rng(seed)
    if scenario == "locked":
        from evaluate import DURATION, DT, EPISODES

        episode_seed, weights = EPISODES[0]
        cycle = make_grade_climb(duration=DURATION, dt=DT)
        road = {"scenario": "locked", "family": "locked", "nominal_grade_pct": 12.0,
                "nominal_speed_kmh": 130.0, "ambient_c": float(cycle["t_amb"] - 273.15)}
        provenance = {"scenario_source": "evaluate.episode_cycle() / make_grade_climb()",
                      "episode": 1, "episode_seed": int(episode_seed),
                      "weights_source": "evaluate.EPISODES[0]",
                      "weights": [float(x) for x in weights],
                      "seed_ignored_for_scenario": True,
                      "dt": float(DT), "duration_s": float(DURATION)}
    elif scenario == "flat":
        cycle = make_terrain(rng, duration=EPISODE_DURATION_S, dt=SIM_DT, family="flat")
        road = {"scenario": "flat", "family": "flat", "nominal_grade_pct": None,
                "nominal_speed_kmh": 130.0, "ambient_c": float(cycle["t_amb"] - 273.15)}
        provenance = {"scenario_source": "engine_env.make_terrain(family='flat')",
                      "episode": None, "weights_source": "SupervisoryTunerEnv.reset(seed)",
                      "seed_ignored_for_scenario": False, "dt": SIM_DT,
                      "duration_s": EPISODE_DURATION_S}
    elif scenario == "terrain":
        cycle = make_terrain(rng, duration=EPISODE_DURATION_S, dt=SIM_DT)
        road = {"scenario": "terrain", "family": cycle["family"], "nominal_grade_pct": None,
                "nominal_speed_kmh": 130.0, "ambient_c": float(cycle["t_amb"] - 273.15)}
        provenance = {"scenario_source": "engine_env.make_terrain(seed)",
                      "episode": None, "weights_source": "SupervisoryTunerEnv.reset(seed)",
                      "seed_ignored_for_scenario": False, "dt": SIM_DT,
                      "duration_s": EPISODE_DURATION_S}
    else:
        raise ValueError("scenario must be one of: locked, flat, terrain")
    return cycle, road, provenance


def create_session(*, scenario="locked", preview=True, policy="manual", seed=0) -> SimulationSession:
    try:
        seed = int(seed)
    except (TypeError, ValueError):
        raise ValueError("seed must be an integer") from None
    if not 0 <= seed <= 2**32 - 1:
        raise ValueError("seed must be between 0 and 4294967295")
    cycle, road, scenario_provenance = _cycle_for(str(scenario), seed)
    actor_weights = None
    provenance = {}
    policy = str(policy)
    valid = {"baseline", "current-grade", "reactive", "predictive", "manual"}
    if policy not in valid:
        actor_weights, provenance = _load_actor(policy)
    effective_preview = bool(preview) and not policy.startswith("blind_")
    env = CapturingEnv(cycle, dt=SIM_DT, use_preview=effective_preview, seed=seed)
    env_seed = int(scenario_provenance.get("episode_seed", seed))
    env.reset(seed=env_seed)
    if scenario == "locked":
        env.w = np.asarray(scenario_provenance["weights"], dtype=np.float32)
        env._obs()  # establish the exact evaluation observation after pinning weights
    provenance.update(scenario_provenance)
    provenance["requested_seed"] = seed
    provenance["environment_seed"] = env_seed
    with _LOCK:
        if len(_SESSIONS) >= MAX_SESSIONS:
            raise RuntimeError("simulation session capacity reached")
        session = SimulationSession(uuid.uuid4().hex, env, str(scenario), policy,
                                    effective_preview, seed, road, actor_weights, provenance)
        _SESSIONS[session.id] = session
    return session


def get_session(session_id: str) -> SimulationSession:
    with _LOCK:
        try:
            return _SESSIONS[session_id]
        except KeyError:
            raise KeyError("unknown or expired session") from None


def _apply_controls(session: SimulationSession, controls: dict | None) -> list[float] | None:
    if controls is None:
        return None
    if not isinstance(controls, dict):
        raise ValueError("controls must be an object")
    allowed = {"speed_kmh", "grade_pct", "ambient_c", "trims"}
    unknown = set(controls) - allowed
    if unknown:
        raise ValueError(f"unsupported controls: {', '.join(sorted(unknown))}")
    # Validate every requested field before mutating the cycle, so bad requests
    # leave the session at exactly the same state.
    speed = _finite_number(controls["speed_kmh"], "speed_kmh", 0.0, 260.0) if "speed_kmh" in controls else None
    grade = _finite_number(controls["grade_pct"], "grade_pct", -20.0, 20.0) / 100.0 if "grade_pct" in controls else None
    ambient = _finite_number(controls["ambient_c"], "ambient_c", -20.0, 60.0) + 273.15 if "ambient_c" in controls else None
    trims = None
    if "trims" in controls:
        try:
            trims = [float(v) for v in controls["trims"]]
        except (TypeError, ValueError):
            raise ValueError("trims must be an array of five finite physical values") from None
        physical_to_normalized(trims)
        if session.policy != "manual":
            raise ValueError("trims can only control a manual session")
    k = session.env.k
    if speed is not None:
        session.env.cycle["v_mps"][k:] = speed / 3.6
        session.road["nominal_speed_kmh"] = speed
    if grade is not None:
        session.env.cycle["grade"][k:] = grade
        session.road["nominal_grade_pct"] = grade * 100.0
    if ambient is not None:
        session.env.cycle["t_amb"] = ambient
        session.road["ambient_c"] = ambient - 273.15
    if any(value is not None for value in (speed, grade, ambient)):
        session.road["customized"] = True
    return trims


def _policy_action(session: SimulationSession, obs: np.ndarray, trims=None) -> np.ndarray:
    env = session.env
    if session.policy == "manual":
        physical = trims if trims is not None else [0.0, 0.0, 0.0, 1.0, 1.0]
        return np.asarray(physical_to_normalized(physical), dtype=np.float32)
    if session.actor_weights is not None:
        return _actor_action(session.actor_weights, obs)
    policy_fn = {
        "baseline": p_neutral,
        "current-grade": p_grade_now,
        "reactive": p_reactive,
        "predictive": p_predictive,
    }[session.policy]
    return np.asarray(policy_fn(env, obs), dtype=np.float32)


def _gear(session: SimulationSession, k: int) -> int:
    env, c = session.env, session.env.cycle
    v = float(c["v_mps"][k])
    nxt = float(c["v_mps"][min(k + 1, len(c["v_mps"]) - 1)])
    accel = (nxt - v) / env.dt
    grade = float(c["grade"][k])
    rho = c.get("p_baro", 101.3) * 1000.0 / (287.0 * c["t_amb"])
    f = (env.veh.mass * accel + 0.5 * rho * env.veh.cd_a * v ** 2
         + env.veh.crr * env.veh.mass * 9.81 * np.cos(np.arctan(grade))
         + env.veh.mass * 9.81 * np.sin(np.arctan(grade)))
    return int(env.veh.gear_for(v, force_n=f) + 1)


def _frame(session: SimulationSession, *, time_s: float, obs_in, obs, action, info=None, initial=False) -> dict:
    env = session.env
    if initial:
        base_out = None
        base_map = env.map_b_prev
        r = {}
        applied = [0.0] * 5
        reward = None
    else:
        base_out = env.last_baseline_out
        base_map = env.last_baseline_map
        r = info or {}
        applied = env.prev_act.astype(float).tolist()
        reward = float(r["reward"]) if "reward" in r else None
    grade = float(env.cycle["grade"][min(max(0, env.k - (0 if initial else 1)), len(env.cycle["grade"]) - 1)])
    preview = [float(x) / 12.0 * 100.0 for x in np.asarray(obs_in)[14:18]]
    btherm = env.thermal_base
    bdamage = damage_rate(btherm.t_turb, btherm.t_oil,
                          base_out.get("ki") if base_out else None)
    base_command = getattr(env.ecu, "last_command", {})
    baseline = {
        "map_kpa": float(base_map),
        "torque": float(base_out["torque"]) if base_out else None,
        "egt_c": float(base_out["egt_k"] - 273.15) if base_out else None,
        "spark": base_command.get("spark"),
        "lam": base_command.get("lam"),
        "fan": base_command.get("fan"),
        "mdot_fuel": float(base_out["mdot_fuel"]) if base_out else None,
        "mdot_air": float(base_out["mdot_air"]) if base_out else None,
        "ki": float(base_out["ki"]) if base_out else None,
        "t_turb": float(btherm.t_turb),
        "t_oil": float(btherm.t_oil),
        "t_block": float(btherm.t_block),
        "damage_rate": float(bdamage),
        "reference_note": "Parallel production-representative ECU reference; fan schedule is not reproduced by a constant neutral action.",
    }
    # ECU spark/lambda are not exposed by SupervisoryTunerEnv; retain null rather
    # than reconstructing an after-the-fact value from mutated ECU state.
    numeric = lambda key, default=None: float(r[key]) if key in r else default
    act_json = None if action is None else np.asarray(action, dtype=np.float32).astype(float).tolist()
    totals = {
        "fuel_g": float(env.ep["fuel"]), "fuel_base_g": float(env.ep["fuel_base"]),
        "damage": float(env.ep["damage"]), "damage_base": float(env.ep["damage_base"]),
        "knock_events": int(env.ep["knock_events"]), "steps": int(env.ep["steps"]),
    }
    return {
        "time_s": float(time_s), "rpm": float(env.rpm), "map_kpa": float(env.map_kpa),
        "input_time_s": float(time_s if initial else time_s - env.dt),
        "dt": float(env.dt),
        "policy": session.policy,
        "mode": "trained_actor" if session.actor_weights is not None else (
            "manual" if session.policy == "manual" else "hand_policy"),
        "evidence": (session.provenance.get("warning") if session.provenance else
                     ("Neutral trims with full fan and pump approximate the ECU reference; the fan schedule differs."
                      if session.policy == "baseline" else
                      ("Manual physical actuator commands in the simulator." if session.policy == "manual"
                       else "Source hand-written comparison policy; not a trained agent."))),
        "provenance": dict(session.provenance),
        "speed_kmh": float(env.v * 3.6), "grade_pct": grade * 100.0,
        "gear": _gear(session, max(0, min(env.k - (0 if initial else 1), len(env.cycle["v_mps"]) - 1))),
        "torque_req": float(env.torque_req), "torque": numeric("torque", None),
        "egt_c": numeric("egt_c", None), "t_turb": float(env.thermal.t_turb),
        "t_oil": float(env.thermal.t_oil), "t_block": float(env.thermal.t_block),
        "ambient_c": float(env.cycle["t_amb"] - 273.15),
        "thermostat": None if initial else getattr(env.thermal, "thermostat", None),
        "spark": numeric("spark", None), "lam": numeric("lam", None),
        "mdot_fuel": numeric("mdot_fuel", None),
        "mdot_air": float(r["mdot_exh"] - r["mdot_fuel"]) if "mdot_exh" in r and "mdot_fuel" in r else None,
        "ki": numeric("ki", None), "damage_rate": float(damage_rate(env.thermal.t_turb, env.thermal.t_oil, r.get("ki"))),
        "reward": reward, "r_resp": numeric("r_resp", None), "r_fuel": numeric("r_fuel", None),
        "r_life": numeric("r_life", None), "cost_torque": numeric("cost_torque", None),
        "cost_knock": numeric("cost_knock", None), "cost_egt": numeric("cost_egt", None),
        "action": act_json,
        "requested": None if action is None else env._rescale(np.asarray(action, np.float32)).astype(float).tolist(),
        "command": applied,
        "obs": np.asarray(obs, dtype=np.float32).astype(float).tolist(),
        "obs_in": np.asarray(obs_in, dtype=np.float32).astype(float).tolist(),
        "preview_pct": preview, "baseline": baseline, "totals": totals,
    }


def initial_frame(session: SimulationSession) -> dict:
    obs = session.env._obs().copy()
    session.env.v = float(session.env.cycle["v_mps"][0])
    return _frame(session, time_s=0.0, obs_in=obs, obs=obs, action=None, initial=True)


def step_session(session: SimulationSession, *, steps=1, controls=None) -> dict:
    if session.done:
        raise ValueError("session is complete; create a new session")
    if isinstance(steps, bool) or not isinstance(steps, int) or not 1 <= steps <= MAX_STEPS_PER_CALL:
        raise ValueError(f"steps must be an integer from 1 to {MAX_STEPS_PER_CALL}")
    # Validate before mutation. `_apply_controls` also validates all fields before
    # applying any of them.
    trims = _apply_controls(session, controls)
    frames = []
    for _ in range(steps):
        k = session.env.k
        if k >= len(session.env.cycle["v_mps"]) - 1:
            session.done = True
            break
        obs_in = session.env._obs().copy()
        action = _policy_action(session, obs_in, trims)
        next_obs, reward, terminated, truncated, info = session.env.step(action)
        info = dict(info)
        info["reward"] = reward
        # `env.step` integrates one full interval using sample k and then
        # increments env.k.  The returned thermal state/observation is at the
        # interval end, so stamp it with sample k+1 rather than duplicating the
        # initial t=0 snapshot on the first response frame.
        end_k = min(k + 1, len(session.env.cycle["t"]) - 1)
        frames.append(_frame(session, time_s=float(session.env.cycle["t"][end_k]),
                             obs_in=obs_in, obs=next_obs, action=action, info=info))
        if terminated or truncated:
            session.done = True
            break
    return {"frames": frames, "done": bool(session.done)}


def reset_frame(session: SimulationSession) -> dict:
    """Return a displayable zero-step snapshot for session creation."""
    obs = session.env._obs().copy()
    env = session.env
    return {
        "time_s": 0.0, "rpm": float(env.rpm), "map_kpa": float(env.map_kpa),
        "input_time_s": 0.0, "dt": float(env.dt),
        "policy": session.policy,
        "mode": "trained_actor" if session.actor_weights is not None else (
            "manual" if session.policy == "manual" else "hand_policy"),
        "evidence": (session.provenance.get("warning") if session.provenance else
                     ("Neutral trims with full fan and pump approximate the ECU reference; the fan schedule differs."
                      if session.policy == "baseline" else
                      ("Manual physical actuator commands in the simulator." if session.policy == "manual"
                       else "Source hand-written comparison policy; not a trained agent."))),
        "provenance": dict(session.provenance),
        "speed_kmh": float(env.v * 3.6), "grade_pct": float(env.cycle["grade"][0] * 100),
        "gear": None, "torque_req": 0.0, "torque": None, "egt_c": None,
        "t_turb": float(env.thermal.t_turb), "t_oil": float(env.thermal.t_oil),
        "t_block": float(env.thermal.t_block),
        "ambient_c": float(env.cycle["t_amb"] - 273.15), "thermostat": None, "spark": None, "lam": None,
        "mdot_fuel": None, "mdot_air": None, "ki": None, "damage_rate": None,
        "reward": None, "r_resp": None, "r_fuel": None, "r_life": None,
        "cost_torque": None, "cost_knock": None, "cost_egt": None,
        "action": None, "requested": None, "command": [0.0] * 5,
        "obs": obs.astype(float).tolist(), "obs_in": obs.astype(float).tolist(),
        "preview_pct": [float(env.cycle["grade"][min(int(h / env.dt), len(env.cycle["grade"]) - 1)] * 100)
                        if session.preview else 0.0 for h in PREVIEW_S],
        "baseline": {"map_kpa": float(env.map_b_prev), "torque": None, "egt_c": None,
                      "spark": None, "lam": None, "fan": None, "mdot_fuel": None, "mdot_air": None,
                      "ki": None, "t_turb": float(env.thermal_base.t_turb),
                      "t_oil": float(env.thermal_base.t_oil), "t_block": float(env.thermal_base.t_block),
                      "damage_rate": None},
        "totals": {"fuel_g": 0.0, "fuel_base_g": 0.0, "damage": 0.0,
                   "damage_base": 0.0, "knock_events": 0, "steps": 0},
    }

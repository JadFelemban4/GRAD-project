"""One frozen test episode, stepped live, for the agent replay page (/agents).

run_lanes() mirrors evaluate.run_episode (evaluate.py:175-202) for several
lanes at once, so that every number the page shows comes from the SAME steps
the scored evaluation took. app/test_agents.py proves the mirror == to
run_episode on whole result dicts; if that proof ever fails, the fix is to
find the cause, never to add a tolerance.

What this module never does:

- it never writes: no file, no cache, no result; traces live in memory only;
- it never edits engine_env: it reads env attributes after each step
  (env.prev_act, env.map_kpa, env.ep) instead of adding a key to `info`,
  because editing engine_env.py would move `plant_sha` and lock out every
  trained agent;
- route() never calls the plant and never writes into the cycle it reads:
  the road is drawn FROM the scenario and nothing it returns reaches an env.
"""
from __future__ import annotations

import numpy as np

import random_road as RR
from app.replay import finite
from engine_env import PREVIEW_S, SupervisoryTunerEnv, damage_rate, make_grade_climb
from evaluate import DT, DURATION, EPISODES, EPISODES_D2

# An episode is 719 steps, not 720: engine_env.py truncates at k >= n - 1.
STEPS = 719
# Observation indices 14..17 are the preview, each grade multiplied by 12
# (engine_env._obs). Horizons always come from engine_env.PREVIEW_S.
PREVIEW = slice(14, 14 + len(PREVIEW_S))
GRADE_OBS_SCALE = 12.0
PROTOCOL_EPISODES = {"phase-d": EPISODES, "d2": EPISODES_D2}


def jsonable(x):
    """A JSON-safe copy of `x`: numpy scalars and arrays become Python values.

    app.replay.finite() accepts only Python int and float, and numpy float32
    is neither, so without this every action and preview value would reach
    the page as null. NaN and infinity become None. bool is tested before int
    because bool is a subclass of int.
    """
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, np.ndarray):
        return [jsonable(v) for v in x.tolist()]
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        return finite(float(x))
    if x is None or isinstance(x, str):
        return x
    raise TypeError(f"not JSON-safe: {type(x).__name__}")


def episode(protocol, idx):
    """Frozen episode `idx` (1-based) of a protocol: 'phase-d' or 'd2'.

    idx 1 is the table's first row. The seed and the weights are the scored
    ones, untouched; `road` is None for Phase D's fixed climb and
    (start_s, grade) for a randomised one. KeyError for anything else.
    """
    table = PROTOCOL_EPISODES[protocol]
    if isinstance(idx, bool) or not isinstance(idx, int) or not 1 <= idx <= len(table):
        raise KeyError(f"no episode {idx!r} in {protocol}")
    row = table[idx - 1]
    road = None if protocol == "phase-d" else (float(row[2]), float(row[3]))
    return {"protocol": protocol, "idx": idx, "seed": int(row[0]),
            "weights": tuple(float(w) for w in row[1]), "road": road}


def build_cycle(ep):
    """A fresh cycle on every call, built exactly as evaluate.run_episode does.

    Never random_road.RandomClimb: that wrapper draws its own road.
    """
    if ep["road"] is None:
        return make_grade_climb(duration=DURATION, dt=DT)
    return RR.climb(ep["road"][0], ep["road"][1], duration=DURATION, dt=DT)


def route(cycle):
    """The road as geometry: 720 vertices along a straight-in-plan route.

    theta = atan(grade), the slope engine_env's vehicle model uses. Over the
    719 stepped samples, ds_k = v_k * DT, and x and z are the cumulative sums
    of ds*cos(theta) and ds*sin(theta). Reads the cycle and returns new lists.
    """
    v = np.asarray(cycle["v_mps"], dtype=float)
    g = np.asarray(cycle["grade"], dtype=float)
    ds = v[:STEPS] * DT
    theta = np.arctan(g[:STEPS])
    s = np.concatenate([[0.0], np.cumsum(ds)])
    x = np.concatenate([[0.0], np.cumsum(ds * np.cos(theta))])
    z = np.concatenate([[0.0], np.cumsum(ds * np.sin(theta))])
    on_climb = np.flatnonzero(g > 0)
    return jsonable({
        "s_m": s, "x_m": x, "z_m": z,
        "grade_pct": g * 100.0,
        "speed_kmh": v * 3.6,
        "length_m": float(s[-1]),
        "rise_m": float(z[-1]),
        "climb_start_s": float(cycle["t"][on_climb[0]]) if on_climb.size else None,
        "p_baro_kpa": float(cycle.get("p_baro", 101.3)),
        "t_amb_c": float(cycle["t_amb"]) - 273.15,
    })


def episode_row(ep, road):
    """The picker's row for one frozen episode, read from the road the env steps.

    `road` is route(build_cycle(ep)). climb_start_s is route()'s: the first
    step whose grade is above zero, 141.0 for D2 episode 1 although the table
    says 141.05, because random_road.climb starts the grade at int(start_s /
    dt). grade is the table's own value for a randomised climb, and for Phase
    D's fixed road the grade at that step (0.12). Both are None on a road with
    no climb. Pure; JSON-safe.
    """
    start = road["climb_start_s"]
    if start is None:
        grade = None
    elif ep["road"] is not None:
        grade = float(ep["road"][1])
    else:
        grade = road["grade_pct"][int(round(start / DT))] / 100.0
    return {"idx": ep["idx"], "seed": ep["seed"], "weights": list(ep["weights"]),
            "climb_start_s": start, "grade": grade}


def _car(env, cmd, obs_in, info):
    """One lane's step, read from the env AFTER the step; nothing is added to it.

    `act` is env.prev_act: the APPLIED action, after rescaling, the slew limit
    and the bounds (engine_env.py:724-726). `held` marks where that differs
    from the network's command. `preview_pct` is decoded from the observation
    the policy was actually given, so the blind car's zeros are its real ones.
    """
    cmd = np.asarray(cmd, dtype=np.float32)
    act = np.array(env.prev_act, dtype=np.float32)
    return {
        "cmd": cmd,
        "act": act,
        "held": act != env._rescale(cmd),
        "preview_pct": obs_in[PREVIEW] / GRADE_OBS_SCALE * 100.0,
        "map_kpa": float(env.map_kpa),
        "turb_c": info["t_turb"] - 273.15,
        "oil_c": info["t_oil"] - 273.15,
        "torque_nm": info["torque"],
        "torque_req_nm": info["torque_req"],
        "damage": float(env.ep["damage"]),
    }


def run_lanes(lanes, ep, on_frame=None):
    """Step one frozen episode for N (policy, use_preview) lanes, interleaved.

    A copy of evaluate.run_episode, step for step, for each lane: its own
    cycle, its own env, reset once with the episode seed, the weights pinned
    after the reset and the observation rebuilt, then step until terminated
    or truncated. At step k lane 0 steps, then lane 1, and so on; then
    on_frame(frame, seen) is called once, where seen[i] is a float32 copy of
    the observation lane i's policy received (None once lane i has stopped).
    A lane that terminates early stops; its later cars are None.

    Returns one dict per lane with exactly run_episode's keys and values.
    Lane order is the caller's; everywhere in this feature lane 0 is the
    sighted agent and lane 1 the blind one.
    """
    state = []
    for policy, use_preview in lanes:
        cycle = build_cycle(ep)
        env = SupervisoryTunerEnv(cycle, dt=DT, seed=ep["seed"], use_preview=use_preview)
        obs, _ = env.reset(seed=ep["seed"])
        env.w = np.asarray(ep["weights"], dtype=np.float32)   # override the fresh draw
        obs = env._obs()
        state.append({"policy": policy, "env": env, "obs": obs, "ret": 0.0,
                      "peak": 0.0, "thermal": 0.0, "info": None, "done": False})
    k = 0
    while not all(s["done"] for s in state):
        cars, seen = [], []
        for s in state:
            if s["done"]:
                cars.append(None)
                seen.append(None)
                continue
            env, obs_in = s["env"], s["obs"]
            a = s["policy"](env, obs_in)
            obs, r, term, trunc, info = env.step(a)
            s["ret"] += r
            s["peak"] = max(s["peak"], info["t_turb"])
            s["thermal"] += damage_rate(info["t_turb"], info["t_oil"]) * env.dt   # as evaluate.run_episode
            s["obs"], s["info"], s["done"] = obs, info, bool(term or trunc)
            cars.append(_car(env, a, obs_in, info))
            seen.append(np.array(obs_in, dtype=np.float32, copy=True))
        if on_frame is not None:
            on_frame(jsonable({"k": k, "cars": cars}), seen)
        k += 1
    out = []
    for s in state:
        e = s["info"]["episode_summary"]
        out.append(dict(ret=s["ret"], damage=e["damage"], damage_thermal=s["thermal"], fuel=e["fuel"],
                        torque_viol=e["torque_viol"], peak_turb=s["peak"] - 273.15,
                        knock=e["knock_events"]))
    return out

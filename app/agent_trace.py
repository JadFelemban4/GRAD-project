"""One frozen test episode, and its road, for the agent replay page (/agents).

episode() and build_cycle() rebuild a scored episode exactly as
evaluate.run_episode builds it (evaluate.py:175-202). route() turns that
episode's cycle into road geometry for the page. jsonable() makes numpy values
safe for JSON.

What this module never does:

- it never writes: no file, no cache, no result;
- route() never calls the plant and never writes into the cycle it reads:
  the road is drawn FROM the scenario and nothing it returns reaches an env.
"""
from __future__ import annotations

import numpy as np

import random_road as RR
from app.replay import finite
from engine_env import PREVIEW_S, make_grade_climb
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

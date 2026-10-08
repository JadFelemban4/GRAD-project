"""step_record.py -- what a recorded step holds: ONE definition for every script
that runs episodes, so that every record can be read the same way.

Asked by Ghassan, 7 October 2026: "make sure that everything from the
environment to the actions of the agents is recorded for monitoring and
understanding". Until then each script kept its own subset, and the ones that
mattered most kept nothing per step: the conditions test kept a summary per
episode, the knock-margin run threw its records away, and training kept no
road, no speed and no gear.

Used by evaluate.py (and through it record_agents.py and knock_margin.py), by
conditions_test.py, and by train.py's recorder. Everything is READ off the
environment after env.step() returns, so an episode with a record is the
episode without one (record_agents.py and conditions_test.py both check this
against their committed scores).

PER STEP

  the agent      action        what the policy returned, in [-1, 1]
                 applied       what the actuators did after the slew limit and the
                               bounds, in physical units: spark trim deg, lambda
                               trim, boost trim kPa, fan duty, pump duty
                 obs           the 23 inputs the action was chosen from (preview
                               included); the observation BEFORE the step
                 reward        and its three terms r_fuel, r_life, r_resp, and the
                               three constraint costs cost_torque, cost_knock, cost_egt
  the road       grade         the grade under the car this step
                 v_kmh         the road speed (the car follows its speed trace exactly)
                 gear          1-8, inferred from engine and road speed: exact while the
                               engine is between 800 and 6500 rpm (Vehicle.demand clips
                               there); the gearbox keeps no state to read it from
  the engine     rpm, map_kpa, tps, iat_c (the charge temperature), torque_req,
                 torque, spark, lam, ki (the knock integral), egt_c, mdot_fuel,
                 mdot_exh (g/s; it sets the turbine's time constant)
  the heat       t_turb, t_oil, t_block (K), thermostat (the opening, 0-1)
  the baseline   the baseline ECU drives the same road in parallel and defines
                 the reward's reference: t_turb_base, t_oil_base, t_block_base,
                 thermostat_base, map_kpa_base, knock_retard_base (deg) and
                 hot_dwell_base (s, its enrichment timer)
  the ledger     damage_rate (per s, the agent's car, knock term included);
                 damage_cum, damage_base_cum, fuel_cum, fuel_base_cum: the
                 episode's running totals, so the baseline's damage and fuel RATES
                 are their differences, exactly as the environment summed them

PER EPISODE (in the .npz as arrays, and in the .json beside it): the frozen
episode's seed and preference weights, and whatever the script that ran it
says about the road and the air (ambient, pressure, grade, speed profile).

Records are large (about 0.4 MB an episode, compressed) and stay on the machine
that made them: results/records/ and every eval_record.npz / train_record.npz
are gitignored, the team's rule since 29 September. show_record.py draws one
episode of any record.
"""
import json
import os

import numpy as np

AGENT = ("action", "applied", "obs", "reward")
INFO = ("t_turb", "t_oil", "t_block", "torque", "torque_req", "torque_base", "spark", "lam", "ki",
        "egt_c", "mdot_fuel", "mdot_exh", "r_fuel", "r_life", "r_resp",
        "cost_torque", "cost_knock", "cost_egt")
ENV = ("rpm", "map_kpa", "grade", "v_kmh", "gear", "tps", "iat_c", "thermostat",
       "t_turb_base", "t_oil_base", "t_block_base", "thermostat_base", "map_kpa_base",
       "knock_retard_base", "hot_dwell_base",
       "damage_rate", "damage_cum", "damage_base_cum", "fuel_cum", "fuel_base_cum",
       "t_amb_c", "c_turb")         # per episode on the extremes roads (8 Oct): ambient, housing capacity
FIELDS = AGENT + ENV + INFO
F16 = ("obs",)                     # normalised inputs; everything else float32
INTS = ("gear", "steps", "episode_seed", "episode", "step")


def gear(env):
    """The gear the box is in, 1-8, from engine speed and road speed; 0 at rest."""
    veh = env.veh
    if env.v < 1.0:
        return 0
    wheel_rpm = env.v / veh.wheel_r * 60.0 / (2 * np.pi)
    ratios = np.asarray(veh.gears) * veh.final_drive
    return int(np.argmin(np.abs(ratios - env.rpm / wheel_rpm))) + 1


def env_state(env):
    """What the environment holds after a step that its info dict does not: the
    road, the gearbox, the parallel baseline car, the running totals. Reads only."""
    e = env.ep
    nan = float("nan")
    return dict(
        rpm=float(env.rpm), map_kpa=float(env.map_kpa),
        grade=float(env.cycle["grade"][env.k - 1]), v_kmh=float(env.v) * 3.6, gear=gear(env),
        tps=float(env.tps), iat_c=float(env.iat_k) - 273.15,
        thermostat=float(getattr(env.thermal, "thermostat", nan)),
        t_turb_base=float(env.thermal_base.t_turb), t_oil_base=float(env.thermal_base.t_oil),
        t_block_base=float(env.thermal_base.t_block),
        thermostat_base=float(getattr(env.thermal_base, "thermostat", nan)),
        map_kpa_base=float(env.map_b_prev),
        knock_retard_base=float(env.ecu.knock_retard), hot_dwell_base=float(env.ecu.hot_dwell),
        damage_cum=float(e["damage"]), damage_base_cum=float(e["damage_base"]),
        fuel_cum=float(e["fuel"]), fuel_base_cum=float(e["fuel_base"]),
        t_amb_c=_at(env.cycle["t_amb"], env.k - 1) - 273.15, c_turb=float(env.thermal.p.c_turb))


def _at(x, k):
    """A cycle entry that is a scalar on some roads and a series on others."""
    a = np.atleast_1d(np.asarray(x, float))
    return float(a[min(max(k, 0), a.size - 1)])


def new():
    return {k: [] for k in FIELDS}


def step(rec, env, action, obs_before, reward, info):
    """Append one step: call right after env.step() returns, before anything resets."""
    from engine_env import damage_rate
    rec["action"].append(np.asarray(action, np.float32))
    rec["applied"].append(np.asarray(env.prev_act, np.float32))
    rec["obs"].append(np.asarray(obs_before, np.float32))
    rec["reward"].append(float(reward))
    for k, v in env_state(env).items():
        rec[k].append(v)
    rec["damage_rate"].append(damage_rate(info["t_turb"], info["t_oil"], info["ki"]))
    for k in INFO:
        rec[k].append(float(info[k]))


def finish(rec):
    """One episode's lists as arrays."""
    return {k: np.asarray(v, dtype=np.int8 if k == "gear" else None) for k, v in rec.items()}


def cast(k, v):
    """float16 for the normalised observation, integers and the preference
    weights as they are, float32 for everything else."""
    v = np.asarray(v)
    if np.issubdtype(v.dtype, np.integer) or k == "weights":
        return v
    return v.astype(np.float16 if k in F16 else np.float32)


def stack(episodes):
    """Episodes (each finish()ed) as one array per field, episode first. A
    shorter episode (one that ended early) is padded with NaN (gear with 0),
    and every episode's length is kept in `steps`."""
    n = max(len(e["reward"]) for e in episodes)
    out = {"steps": np.array([len(e["reward"]) for e in episodes], dtype=np.int32)}
    for k in episodes[0]:
        rows = []
        for e in episodes:
            a = np.asarray(e[k], dtype=float)
            rows.append(np.pad(a, [(0, n - a.shape[0])] + [(0, 0)] * (a.ndim - 1),
                               constant_values=0.0 if k == "gear" else np.nan))
        out[k] = np.stack(rows).astype(np.int8) if k == "gear" else np.stack(rows)
    return out


def save(path, episodes, meta, seeds=None, weights=None):
    """A policy's episodes as one compressed .npz, and `meta` -- what produced
    the record and under which conditions -- as JSON beside it."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    arrays = stack(episodes)
    if seeds is not None:
        arrays["episode_seed"] = np.asarray(seeds, dtype=np.int64)
    if weights is not None:
        arrays["weights"] = np.asarray(weights, dtype=float)
    np.savez_compressed(path, **{k: cast(k, v) for k, v in arrays.items()})
    with open(os.path.splitext(path)[0] + ".json", "w", encoding="utf-8") as fh:
        json.dump(dict(meta, fields=list(FIELDS), steps=arrays["steps"].tolist()), fh,
                  indent=1, default=str)
        fh.write("\n")
    return path


def git_head():
    import subprocess
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True,
                                       stderr=subprocess.DEVNULL,
                                       cwd=os.path.dirname(os.path.abspath(__file__))).strip()
    except Exception:
        return None

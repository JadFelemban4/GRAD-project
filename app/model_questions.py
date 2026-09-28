"""The one question both language models are asked, and the one way an answer
becomes an action (agent replay M3, design section 7.3).

jev (app/jev.py) and Laya (app/laya_bridge.py) both import this module, so
both are asked the same thing about the same second: build_state(trace, step)
and QUESTIONS, the same module-level object. Laya is also asked
QUESTIONS_REVERSED, the same five questions with each question's five options
listed in reverse order, so the page can show whether a choice moved with the
order alone (design 7.5b).

The state is the sighted agent's own observation, trace.obs[0][step], decoded
from engine_env._obs back into named physical units, plus one fixed task
paragraph. Nothing else is sent: not the agents' actions, not the experiment
or its verdict, and nothing from the recorded drives. Its spark and lambda are
the values applied in the previous second, with the sighted agent's trims
already in them.

What this module never does: write, open a connection, or parse a model's
text. An option key maps back to a level by dictionary lookup, and every key
is ASCII (design C12).
"""
from __future__ import annotations

import math
import os
from pathlib import Path

import numpy as np

from app.agent_api import Trace
from engine_env import (ACT_HI, ACT_LO, OIL_PROTECT_K, PREVIEW_S, TURB_PROTECT_K,
                        neutral_action)

REPO = Path(__file__).resolve().parent.parent


class BadAnswer(ValueError):
    """An answer that cannot become an action. It carries none of the answer's text."""


# The five actions, in engine_env's order (agent-view.mjs ACTIONS: spark,
# lambda, boost, fan, pump).
IDS = ("spark_trim", "lambda_trim", "boost_ceiling", "cooling_fan", "coolant_pump")

KEYS = {
    "spark_trim": ("retard 8 deg", "retard 4 deg", "no change", "advance 2 deg",
                   "advance 4 deg"),
    "lambda_trim": ("richer by 0.15", "richer by 0.075", "no change", "leaner by 0.03",
                    "leaner by 0.06"),
    "boost_ceiling": ("ceiling -40 kPa", "ceiling -20 kPa", "no change", "ceiling +7.5 kPa",
                      "ceiling +15 kPa"),
    "cooling_fan": ("fan 0 %", "fan 25 %", "fan 50 %", "fan 75 %", "fan 100 %"),
    "coolant_pump": ("pump 30 %", "pump 47.5 %", "pump 65 %", "pump 82.5 %", "pump 100 %"),
}

# Levels in physical units: for the three trims the two limits, the neutral
# and the two midpoints; for the fan and the pump five evenly spaced duties.
# The neutral is agent_api.page_constants()'s neutral_phys formula, which is
# engine_env._rescale(neutral_action()) written out.
_NEUTRAL = ACT_LO + (neutral_action() + 1.0) * 0.5 * (ACT_HI - ACT_LO)
LEVELS = np.array(
    [[ACT_LO[i], (ACT_LO[i] + _NEUTRAL[i]) / 2, _NEUTRAL[i], (_NEUTRAL[i] + ACT_HI[i]) / 2,
      ACT_HI[i]] for i in range(3)]
    + [np.linspace(ACT_LO[i], ACT_HI[i], 5) for i in (3, 4)],
    dtype=np.float32)
# The network's units, computed vectorised in float32 exactly as neutral_action()
# computes them, so the neutral levels are bitwise neutral_action().
NET = np.clip(2.0 * (LEVELS - ACT_LO[:, None]) / (ACT_HI - ACT_LO)[:, None] - 1.0,
              -1.0, 1.0).astype(np.float32)
OPTIONS = {qid: {key: j for j, key in enumerate(keys)} for qid, keys in KEYS.items()}

DESCRIPTIONS = {
    "spark_trim": ("spark trim -8 deg", "spark trim -4 deg", "spark trim 0 deg",
                   "spark trim +2 deg", "spark trim +4 deg"),
    "lambda_trim": ("lambda trim -0.15", "lambda trim -0.075", "lambda trim 0",
                    "lambda trim +0.03", "lambda trim +0.06"),
    "boost_ceiling": ("boost ceiling -40 kPa", "boost ceiling -20 kPa", "boost ceiling 0 kPa",
                      "boost ceiling +7.5 kPa", "boost ceiling +15 kPa"),
    "cooling_fan": ("cooling fan 0 %", "cooling fan 25 %", "cooling fan 50 %",
                    "cooling fan 75 %", "cooling fan 100 %"),
    "coolant_pump": ("coolant pump 30 %", "coolant pump 47.5 %", "coolant pump 65 %",
                     "coolant pump 82.5 %", "coolant pump 100 %"),
}
INSTRUCTIONS = {
    "spark_trim": "Following `task`, how should spark timing be trimmed for the next second?",
    "lambda_trim": ("Following `task`, how should the air-fuel ratio be trimmed? "
                    "Richer cools the exhaust and costs fuel."),
    "boost_ceiling": ("Following `task`, by how much should the ceiling of the "
                      "boost-pressure loop be offset? It matters only if manifold pressure "
                      "(`engine.manifold_pressure_kPa`) would otherwise reach the ceiling."),
    "cooling_fan": ("Following `task`, what cooling fan duty should run? "
                    "It cools the coolant loop, not the turbine directly."),
    "coolant_pump": "Following `task`, what coolant pump duty should run (minimum 30 %)?",
}
QUESTIONS = {qid: {"type": "choice", "instructions": INSTRUCTIONS[qid],
                   "criteria": dict(zip(KEYS[qid], DESCRIPTIONS[qid]))} for qid in IDS}
QUESTIONS_REVERSED = {qid: {"type": "choice", "instructions": q["instructions"],
                            "criteria": dict(reversed(list(q["criteria"].items())))}
                      for qid, q in QUESTIONS.items()}

TASK = ("Decide the supervisory settings for the next one second. Deliver the requested "
        f"torque. Keep the turbine housing below {TURB_PROTECT_K - 273.15:.0f} °C and the "
        f"oil below {OIL_PROTECT_K - 273.15:.0f} °C. Weigh the three by `engine.priorities`. "
        "Spark and lambda trims are added to the modelled engine computer's values. The "
        "boost setting offsets only the ceiling of the pressure loop and matters only if "
        "pressure would otherwise reach it. Fan and pump are absolute duties.")
NOTE = "simulated synthetic stress scenario, not a recorded drive"


def decode(obs):
    """engine_env._obs inverted: 23 observation values -> named physical units.

    Each field is computed in float64 from the float32 value and rounded to
    the digits it can carry. ValueError for any other shape, or for a value
    that is not finite: nothing is substituted.
    """
    o = np.asarray(obs, dtype=np.float32).astype(np.float64)
    if o.shape != (23,) or not np.all(np.isfinite(o)):
        raise ValueError("an observation is 23 finite values")

    def r(v, digits):
        return round(float(v), digits)

    return {
        "engine_speed_rpm": r((o[0] + 1.0) * 3000.0, 1),
        "manifold_pressure_kPa": r((o[1] + 1.0) * 120.0, 2),
        "throttle_fraction": r(o[2], 4),
        "spark_advance_deg_BTDC": r((o[3] + 1.0) * 20.0, 2),
        "lambda": r(o[4] / 8.0 + 1.0, 4),
        "engine_block_C": r(o[5] * 25.0 + 363.0 - 273.15, 2),
        "oil_C": r(o[6] * 30.0 + 373.0 - 273.15, 2),
        "turbine_housing_C": r(o[7] * 200.0 + 873.0 - 273.15, 1),
        "charge_air_C": r(o[8] * 25.0 + 303.0 - 273.15, 2),
        "ambient_C": r(o[9] * 15.0 + 293.0 - 273.15, 2),
        "barometric_kPa": r(o[10] * 8.0 + 101.3, 2),
        "humidity_kg_per_kg": r((o[11] + 0.5) / 40.0, 5),
        "road_speed_kmh": r((o[12] + 1.0) * 25.0 * 3.6, 2),
        "grade_now_percent": r(o[13] / 12.0 * 100.0, 3),
        "grade_ahead_percent": {f"in_{h:g}_s": r(o[14 + i] / 12.0 * 100.0, 3)
                                for i, h in enumerate(PREVIEW_S)},
        "torque_requested_Nm": r((o[18] + 1.0) * 200.0, 1),
        "driver_aggression_0_to_1": r(o[19], 4),
        "priorities": {"deliver_torque": r(o[20], 4), "save_fuel": r(o[21], 4),
                       "protect_components": r(o[22], 4)},
        "note": NOTE,
    }


def build_state(trace, step):
    """{'engine': the sighted agent's observation at `step`, decoded; 'task': TASK}.

    Only a store Trace is accepted, so browser state can never be sent.
    """
    if not isinstance(trace, Trace):
        raise TypeError("build_state takes an agent_api.Trace, never browser state")
    return {"engine": decode(trace.obs[0][step]), "task": TASK}


def _probability(v):
    if (isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
            or not 0.0 <= v <= 1.0):
        raise BadAnswer("a probability that is not a number in [0, 1]")
    return float(v)


def to_action(answers):
    """Per question id: the chosen option as a level, and its probabilities.

    {qid: {choice, level_phys, level_net, probabilities (in KEYS order),
    chosen_p, options: [{key, level_phys}] x5}}. The model's confidence,
    answer_confidence and action are dropped (design C9), and so are ids that
    were not asked. BadAnswer for a missing id, a choice outside its options,
    probabilities that do not name exactly its options, or a probability that
    is not a finite number in [0, 1].
    """
    if not isinstance(answers, dict):
        raise BadAnswer("answers is not an object")
    out = {}
    for i, qid in enumerate(IDS):
        a = answers.get(qid)
        if not isinstance(a, dict):
            raise BadAnswer(f"{qid}: no answer")
        choice = a.get("choice")
        if not isinstance(choice, str) or choice not in OPTIONS[qid]:
            raise BadAnswer(f"{qid}: the choice is not one of its options")
        probs = a.get("probabilities")
        if not isinstance(probs, dict) or set(probs) != set(KEYS[qid]):
            raise BadAnswer(f"{qid}: the probabilities do not name exactly its options")
        ordered = {key: _probability(probs[key]) for key in KEYS[qid]}
        j = OPTIONS[qid][choice]
        out[qid] = {"choice": choice,
                    "level_phys": float(LEVELS[i, j]),
                    "level_net": float(NET[i, j]),
                    "probabilities": ordered,
                    "chosen_p": ordered[choice],
                    "options": [{"key": key, "level_phys": float(LEVELS[i, m])}
                                for m, key in enumerate(KEYS[qid])]}
    return out


def user_setting(env_var, file_name, environ=None):
    """(value, 'env' | 'file'), or (None, None).

    The environment variable wins. Otherwise the file
    <APPDATA>/grad-project/<file_name> is read, and refused if it resolves
    inside the repository: a git-ignored file in the working tree still
    travels in a zip or a copy (CLAUDE.md mistakes 11 and 16). A VALUE is
    never treated as a path: the server runs from the repository root, so a
    key resolved as a path would always land inside it.
    """
    env = os.environ if environ is None else environ
    value = (env.get(env_var) or "").strip()
    if value:
        return value, "env"
    appdata = env.get("APPDATA")
    if not appdata:
        return None, None
    path = (Path(appdata) / "grad-project" / file_name).resolve()
    if path == REPO or REPO in path.parents:
        return None, None
    try:
        text = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return None, None
    return (text, "file") if text else (None, None)

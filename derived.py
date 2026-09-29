"""derived.py -- the ONE reader of data/derived_params.json.

Every constant this project can compute from the car's own logs lives in that
file, not in the code, and is recomputed by derive_params.py whenever the data
changes (build_dataset.py runs it at the end). The modules that use them --
thermal.py, plant.py, engine_env.py -- read them through here.

WHY, 28 September 2026. The load constant k used to be a fitted constant; it is now
DERIVED, 269.6 / T_charge at each point, so it moves with the data by
construction. The team asked for the same treatment everywhere it is possible:
no fitted number typed into a module, where the data can set it. A constant that
has to be ESTIMATED rather than defined (the thermal network, the boost
ceiling) is still estimated -- but by a fixed, seeded method that re-runs on
whatever drives are present, so nothing is frozen at the value one person got
on one day.

NO SILENT FALLBACK. If the file is missing this raises, naming the command that
makes it. A default that quietly substitutes some other number is mistake 1
(the 2.0 L inline-four that ran for three weeks because a default picked it).
The one exception is derive_params.py itself, which sets DERIVING_PARAMS=1 so
the modules can be imported while the file is being made; in that mode a missing
value is NaN, which propagates visibly rather than looking like a number.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "data", "derived_params.json")

_CACHE = {}


def _load():
    if "d" not in _CACHE:
        if not os.path.exists(PATH):
            if os.environ.get("DERIVING_PARAMS") == "1":
                _CACHE["d"] = {}
            else:
                raise FileNotFoundError(
                    f"{PATH} is missing. It holds every constant computed from the car's "
                    "logs. Make it with:  python derive_params.py")
        else:
            with open(PATH, encoding="utf-8") as fh:
                _CACHE["d"] = json.load(fh)
    return _CACHE["d"]


def get(section, key=None):
    """A derived value. NaN only while derive_params.py is building the file."""
    d = _load().get(section)
    if d is None:
        if os.environ.get("DERIVING_PARAMS") == "1":
            return math.nan if key is not None else None
        raise KeyError(f"data/derived_params.json has no '{section}'. Run: python derive_params.py")
    if key is None:
        return d
    if key not in d:
        if os.environ.get("DERIVING_PARAMS") == "1":
            return math.nan
        raise KeyError(f"data/derived_params.json has no '{section}.{key}'. Run: python derive_params.py")
    return d[key]


def all_params():
    return _load()

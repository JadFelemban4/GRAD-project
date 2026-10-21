"""derived.py -- the ONE reader of every engine's derived file.

Every constant this project can compute from data lives in a file, not in the
code, and is recomputed whenever the data changes. For the B58 that file is
data/derived_params.json, written by derive_params.py from the car's own logs
(build_dataset.py runs it at the end); every later engine gets
data/engines/<id>/derived_params.json (engine_path). engines.py reads them
through here when it builds a plant, and engines.DERIVED_FIELDS says which field
of which record comes from where.

WHY, 28 September 2026. The load constant k used to be a fitted constant; it is now
DERIVED, 269.6 / T_charge at each point, so it moves with the data by
construction. The team asked for the same treatment everywhere it is possible:
no fitted number typed into a module, where the data can set it. A constant that
has to be ESTIMATED rather than defined (the thermal network, the boost
ceiling) is still estimated -- but by a fixed, seeded method that re-runs on
whatever drives are present, so nothing is frozen at the value one person got
on one day.

EVERY READ NAMES ITS FILE (20 October 2026, the four-engine build). get() and
all_params() take the file as a required keyword: a reader that left it out
would get the B58's constants for whatever engine it meant, which is mistake 1
in a new place. B58_PATH is the B58's file, by name: it was PATH until 21
October 2026, a generic name for one engine's file (the review of build step 1).

NO SILENT FALLBACK. If a file is missing this raises, naming the command that
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
B58_PATH = os.path.join(HERE, "data", "derived_params.json")     # the B58's, from the car's logs
ENGINES_DIR = os.path.join(HERE, "data", "engines")

_CACHE = {}


def engine_path(engine_id):
    """A later engine's derived file: data/engines/<id>/derived_params.json."""
    return os.path.join(ENGINES_DIR, engine_id, "derived_params.json")


def _maker(path):
    if os.path.normcase(os.path.abspath(path)) == os.path.normcase(B58_PATH):
        return "python derive_params.py"
    return "that engine's calibration script (none is written yet: build step 1 has the B58 only)"


def _load(path):
    key = os.path.normcase(os.path.abspath(path))
    if key not in _CACHE:
        if not os.path.exists(path):
            if os.environ.get("DERIVING_PARAMS") == "1":
                _CACHE[key] = {}
            else:
                raise FileNotFoundError(
                    f"{path} is missing. It holds every constant computed from data for "
                    f"its engine. Make it with:  {_maker(path)}")
        else:
            with open(path, encoding="utf-8") as fh:
                _CACHE[key] = json.load(fh)
    return _CACHE[key]


def get(section, key=None, *, path):
    """A derived value from `path`. NaN only while derive_params.py is building the file."""
    d = _load(path).get(section)
    name = os.path.relpath(path, HERE)
    if d is None:
        if os.environ.get("DERIVING_PARAMS") == "1":
            return math.nan if key is not None else None
        raise KeyError(f"{name} has no '{section}'. Run: {_maker(path)}")
    if key is None:
        return d
    if key not in d:
        if os.environ.get("DERIVING_PARAMS") == "1":
            return math.nan
        raise KeyError(f"{name} has no '{section}.{key}'. Run: {_maker(path)}")
    return d[key]


def all_params(*, path):
    return _load(path)

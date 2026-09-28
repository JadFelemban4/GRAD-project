"""The agent replay page's server side: the model loader, the episode store and
the three routes.

Imported only from the --simulation branch of app/server.py, which calls
install(app), so --live and --replay never load agent code, SB3 or torch.

What this module never does: write to disk, train, evaluate, or call
evaluate.check_model_fingerprint (it raises SystemExit). stable-baselines3 and
torch are imported lazily inside load_pair, so importing this module costs
neither, and versions() only reads what is already loaded.
"""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import importlib.util
from pathlib import Path
import re
import sys
import threading

import numpy as np

from app import agent_catalog
from app import agent_catalog as C
from app import agent_trace
from app.replay import BuildCancelled
from engine_env import (ACT_HI, ACT_LO, OBS_DIM, OIL_PROTECT_K, PREVIEW_S, SLEW,
                        TURB_PROTECT_K, neutral_action)
from evaluate import agent_policy

ROOT = C.ROOT


def pair_paths(runs, seed):
    """(sighted, blind) model paths for one seed, spelled as evaluate.py:370 does.

    `runs` must be a runs directory NAME, never a path: anything failing
    agent_catalog.RUNS_NAME is a KeyError, and so is a seed that is not a
    non-negative int.
    """
    if not isinstance(runs, str) or not C.RUNS_NAME.fullmatch(runs):
        raise KeyError(f"unknown runs directory {runs!r}")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise KeyError(f"unknown seed {seed!r}")
    return tuple(str(ROOT / runs / f"{arm}_seed{seed}") + "/final" for arm in C.ARMS)


def load_pair(runs, seed):
    """(sighted, blind) SAC models, loaded exactly as evaluate.py:370 loads them.

    SAC.load(dir + "/final") with NO device argument: SB3's "auto", which is
    cuda on this machine. CPU and CUDA give different episodes (recon
    section 2), so the device is recorded and shown, never chosen here.
    """
    sighted, blind = pair_paths(runs, seed)
    from stable_baselines3 import SAC
    return SAC.load(sighted), SAC.load(blind)


def as_policy(m):
    """A policy(env, obs) callable: an SB3 model is wrapped as evaluate wraps it.

    A plain callable passes through unchanged: that is the proof's no-SB3 path,
    which runs check_premise's hand-written policies through the same store.
    """
    return agent_policy(m) if hasattr(m, "predict") else m


def versions():
    """torch and stable-baselines3 versions AS LOADED; never imports either."""
    return {"torch": getattr(sys.modules.get("torch"), "__version__", None),
            "sb3": getattr(sys.modules.get("stable_baselines3"), "__version__", None)}


# ---- the episode store: one worker, streaming, cancellable, bounded ---------
#
# Modelled on app.replay.ReplayStore (replay.py:259-322), which cannot stream
# partial frames. THE LOCK IS NEVER HELD DURING SLOW WORK: episode_for (a
# fingerprint and two zip hashes), the loader (torch import, SAC.load, CUDA
# start-up: about 5 s on the first build) and the tracer (about 75 s) all run
# outside it. Only publishing a frame, the device or the result takes it, so a
# poll always answers at once -- and the first answer after «احسب» is 'loading'.

BUILD_FAILED = "build failed: {kind}"


@dataclass
class Trace:
    """One finished pair: what the page plays, and what the policies saw.

    `frames` are JSON-safe already (run_lanes passes each through
    agent_trace.jsonable). `results` are run_lanes' RAW dicts, NaN on a
    diverged lane, because the == proof compares them as run_episode returns
    them: pass them through agent_trace.jsonable before serving them.
    """
    key: tuple
    frames: list
    results: list
    obs: list
    device: str
    versions: dict


def key_str(key):
    """('runs_c4', 5, 1) -> 'runs_c4/5/1'."""
    runs, seed, idx = key
    return f"{runs}/{seed}/{idx}"


def default_episode_for(runs, seed, idx):
    """The frozen episode for this pair's protocol. find_pair runs again here,
    so the fatal fingerprint and the scored-artefact check are repeated
    immediately before the networks are loaded."""
    return agent_trace.episode(agent_catalog.find_pair(runs, seed)["protocol"], idx)


def _lane_obs(seen_rows, lane):
    rows = [row[lane] for row in seen_rows if row[lane] is not None]
    if not rows:
        return np.zeros((0, OBS_DIM), dtype=np.float32)
    return np.stack(rows).astype(np.float32, copy=False)


class EpisodeStore:
    """One daemon 'agent-builder' worker, one pair at a time, keep = 2 finished.

    Any other key gets 'busy'; only preempt=True cancels, and only the first
    request after «احسب» sends it. A cancelled or partial trace is never kept.
    Errors -- SystemExit included -- are reported once as a fixed message,
    never str(exc), then forgotten so the next poll can retry.
    """

    def __init__(self, loader=load_pair, tracer=agent_trace.run_lanes, keep=2,
                 episode_for=default_episode_for):
        self._loader, self._tracer = loader, tracer
        self._keep, self._episode_for = keep, episode_for
        self.needs_sb3 = loader is load_pair
        self._lock = threading.Lock()
        self._cache = OrderedDict()
        self._errors = {}
        self._active = None
        self._frames = []
        self._device = None
        self._versions = None
        self._cancel = threading.Event()

    def trace(self, key):
        """A finished Trace, or None (never a partial one)."""
        with self._lock:
            return self._cache.get(key)

    def poll(self, key, since=0, preempt=False):
        since = max(0, int(since))
        base = {"steps": agent_trace.STEPS, "since": since}
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                tr = self._cache[key]
                return dict(base, status="ready", progress=1.0, frames=tr.frames[since:],
                            device=tr.device, versions=tr.versions)
            if key in self._errors:
                return dict(base, status="error", progress=0.0, frames=[], device=None,
                            versions=None, message=self._errors.pop(key))
            if self._active == key:
                n = len(self._frames)
                return dict(base, status="building" if n else "loading",
                            progress=n / agent_trace.STEPS, frames=self._frames[since:],
                            device=self._device, versions=self._versions)
            if self._active is not None:
                if preempt:
                    self._cancel.set()
                runs, seed, idx = self._active
                return dict(base, status="busy", progress=0.0, frames=[], device=None,
                            versions=None, active={"runs": runs, "seed": seed, "ep": idx})
            self._cancel = threading.Event()
            self._active, self._frames = key, []
            self._device = self._versions = None
            threading.Thread(target=self._build, args=(key, self._cancel), daemon=True,
                             name="agent-builder").start()
            return dict(base, status="loading", progress=0.0, frames=[], device=None,
                        versions=None)

    def _build(self, key, cancel):
        runs, seed, idx = key
        frames, seen_rows = [], []

        def on_frame(frame, seen):
            if cancel.is_set():
                raise BuildCancelled(key_str(key))
            with self._lock:
                frames.append(frame)
                seen_rows.append(seen)
                self._frames = frames

        try:
            ep = self._episode_for(runs, seed, idx)
            m_s, m_b = self._loader(runs, seed)
            devices = {str(getattr(m, "device", "n/a")) for m in (m_s, m_b)}
            if len(devices) != 1:
                raise RuntimeError("the two networks loaded on different devices")
            device, vers = devices.pop(), versions()
            if cancel.is_set():
                raise BuildCancelled(key_str(key))
            with self._lock:
                self._device, self._versions = device, vers
            results = self._tracer([(as_policy(m_s), True), (as_policy(m_b), False)],
                                   ep, on_frame)
            trace = Trace(key, frames, results, [_lane_obs(seen_rows, 0), _lane_obs(seen_rows, 1)],
                          device, vers)
            with self._lock:
                self._cache[key] = trace
                while len(self._cache) > self._keep:
                    self._cache.popitem(last=False)
        except BuildCancelled:
            pass                     # superseded, not failed: nothing kept, nothing reported
        except (Exception, SystemExit) as exc:
            with self._lock:
                self._errors[key] = BUILD_FAILED.format(kind=type(exc).__name__)
        finally:
            with self._lock:
                self._active = None


# ---- routes: added by install(app), and only under --simulation ------------
#
# app/server.py calls install(app) inside `if a.simulation:` in main(), so the
# --live and --replay processes never import this module. Every route here is
# a GET and answers with Cache-Control: no-store. A request names an episode
# by three strings that must match fixed patterns before anything is looked up;
# no path is ever built from a request.

NO_STORE = {"Cache-Control": "no-store"}
SEED_TEXT = re.compile(r"[0-9]{1,3}")
EP_TEXT = re.compile(r"[0-9]{1,2}")
SINCE_TEXT = re.compile(r"[0-9]{1,4}")
STATIC = Path(__file__).resolve().parent / "static"
_ROADS = {}


def sb3_available():
    """True when stable-baselines3 can be imported. Looked up, not imported."""
    return importlib.util.find_spec("stable_baselines3") is not None


def page_constants():
    """The preview horizons, the action space and the two protection limits,
    JSON-safe: the same three fields in the catalog and in every episode's
    meta, computed in one place. neutral_phys keeps M1's formula,
    engine_env._rescale(neutral_action()) written out: 0 for the three trims,
    1.0 for the fan and the pump."""
    neutral_phys = ACT_LO + (neutral_action() + 1.0) * 0.5 * (ACT_HI - ACT_LO)
    return agent_trace.jsonable({
        "preview_s": list(PREVIEW_S),
        "act": {"lo": ACT_LO, "hi": ACT_HI, "slew": SLEW, "neutral_phys": neutral_phys},
        "limits": {"turb_c": round(TURB_PROTECT_K - 273.15, 1),
                   "oil_c": round(OIL_PROTECT_K - 273.15, 1)},
    })


def episode_meta(pair, ep, road, verdict):
    """Everything the page needs once per episode, JSON-safe. The device and
    the torch/SB3 versions are NOT here: they are known only after the worker
    has loaded the networks, so they travel in every poll response instead.

    `episode` is the picker's own row (agent_trace.episode_row), read from the
    road the env steps, so Phase D's grade is 0.12 rather than None; preview_s,
    act and limits are page_constants(), the catalog's own."""
    agents = pair["agents"]
    row = agent_trace.episode_row(ep, road)
    consts = page_constants()
    return agent_trace.jsonable({
        "experiment": pair["experiment"],
        "runs": pair["runs"],
        "prefix": pair["prefix"],
        "protocol": pair["protocol"],
        "seed": pair["seed"],
        "ep": ep["idx"],
        "episode": {k: row[k] for k in ("seed", "weights", "climb_start_s", "grade")},
        "dt": agent_trace.DT,
        "duration_s": agent_trace.DURATION,
        "steps": agent_trace.STEPS,
        "train_dt": {a["arm"]: a["train_dt"] for a in agents},
        "agents": [{"tag": a["tag"], "arm": a["arm"], "budget_line": a["budget_line"],
                    "zip_sha": a["zip_sha"], "scored": a["scored"]} for a in agents],
        "result_file": pair["result_file"],
        "preview_s": consts["preview_s"],
        "act": consts["act"],
        "limits": consts["limits"],
        "scenario": {"v_kmh": max(road["speed_kmh"]), "t_amb_c": road["t_amb_c"],
                     "p_baro_kpa": road["p_baro_kpa"]},
        "verdict": verdict,
        "fingerprint_taken": agent_catalog.FINGERPRINT_TAKEN.get(pair["protocol"]),
    })


def _road(ep):
    """The episode's road, from the cycle arrays only (no plant), cached."""
    key = (ep["protocol"], ep["idx"])
    if key not in _ROADS:
        _ROADS[key] = agent_trace.route(agent_trace.build_cycle(ep))
    return _ROADS[key]


def catalog_episodes():
    """The picker's row for every frozen episode of both protocols, each read
    from the road the env steps (agent_trace.episode_row): Phase D's twenty
    all climb 12 % at 180 s and differ only in their weights."""
    out = {}
    for protocol in ("d2", "phase-d"):
        rows = []
        for idx in range(1, len(agent_trace.PROTOCOL_EPISODES[protocol]) + 1):
            ep = agent_trace.episode(protocol, idx)
            rows.append(agent_trace.episode_row(ep, _road(ep)))
        out[protocol] = rows
    return out


def catalog(root=ROOT, sb3=None):
    """Everything the picker needs, JSON-safe: every runs*/ directory with its
    pairs, their status and quoted table rows, and its quoted verdict
    (agent_catalog.discover, read-only, no thread); the frozen episodes of
    both protocols; the page's constants; and whether stable-baselines3 can
    be imported (`sb3`, looked up unless the caller says). Computes nothing."""
    body = {"experiments": agent_catalog.discover(root), "episodes": catalog_episodes()}
    body.update(page_constants())
    body["sb3"] = sb3_available() if sb3 is None else bool(sb3)
    return agent_trace.jsonable(body)


def install(app, store=None):
    """Add GET /agents, GET /api/agents/catalog and GET /api/agents/episode to `app`."""
    from fastapi.responses import HTMLResponse, JSONResponse

    store = store if store is not None else EpisodeStore()
    app.state.agent_store = store

    def answer(body, status=200):
        return JSONResponse(body, status_code=status, headers=NO_STORE)

    @app.get("/agents", response_class=HTMLResponse)
    def agents_page():
        """The agent replay page. Read-only; computes nothing until «احسب»."""
        return HTMLResponse((STATIC / "agents.html").read_text(encoding="utf-8"),
                            headers=NO_STORE)

    @app.get("/api/agents/catalog")
    def agents_catalog():
        """Every experiment, pair and episode the picker offers. Read-only;
        starts nothing. A failure is a fixed text, never str(exc)."""
        try:
            return answer(catalog(sb3=(not store.needs_sb3) or sb3_available()))
        except Exception as exc:
            return answer({"detail": f"catalog failed: {type(exc).__name__}"}, 500)

    @app.get("/api/agents/episode")
    def agents_episode(runs: str = "", seed: str = "", ep: str = "",
                       since: str = "0", preempt: str = ""):
        """Start or poll one episode of one pair. since=0 also carries meta and road.

        Every parameter is taken as text and checked here, so a malformed one
        gets this route's own 404 with no-store rather than FastAPI's 422.
        Anything else unexpected is a 500 with a fixed text and no-store, never
        str(exc). The road and the meta are built before the store is polled,
        so a request that fails never starts a build.
        """
        unknown = answer({"detail": "unknown episode"}, 404)
        if (not agent_catalog.RUNS_NAME.fullmatch(runs) or not SEED_TEXT.fullmatch(seed)
                or not EP_TEXT.fullmatch(ep) or not 1 <= int(ep) <= 20
                or not SINCE_TEXT.fullmatch(since)):
            return unknown
        seed_n, idx, since_n = int(seed), int(ep), int(since)
        preempt_on = preempt in ("1", "true")
        try:
            try:
                pair = agent_catalog.find_pair(runs, seed_n)
                episode = agent_trace.episode(pair["protocol"], idx)
            except KeyError:
                return unknown
            except agent_catalog.Refused as refused:
                return answer({"status": "refused", "problems": refused.problems}, 409)
            if store.needs_sb3 and not sb3_available():
                return answer({"detail": "stable-baselines3 is not installed"}, 503)
            first = {}
            if since_n == 0:
                road = _road(episode)
                first = {"road": road,
                         "meta": episode_meta(pair, episode, road,
                                              agent_catalog.verdict(pair["prefix"]))}
            out = store.poll((runs, seed_n, idx), since=since_n, preempt=preempt_on)
            out.update(first)
            return answer(out)
        except Exception as exc:
            return answer({"detail": f"server error: {type(exc).__name__}"}, 500)

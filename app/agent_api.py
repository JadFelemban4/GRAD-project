"""The agent replay page's server side: the model loader and the episode store.

Imported only from the --simulation branch of app/server.py (install() is
added in a later task), so --live and --replay never load agent code, SB3 or
torch.

What this module never does: write to disk, train, evaluate, or call
evaluate.check_model_fingerprint (it raises SystemExit). stable-baselines3 and
torch are imported lazily inside load_pair, so importing this module costs
neither, and versions() only reads what is already loaded.
"""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import sys
import threading

import numpy as np

from app import agent_catalog
from app import agent_catalog as C
from app import agent_trace
from app.replay import BuildCancelled
from engine_env import OBS_DIM
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

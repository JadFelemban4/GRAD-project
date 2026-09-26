"""The agent replay page's server side: the model loader, and later the store.

Imported only from the --simulation branch of app/server.py (install() is
added in a later task), so --live and --replay never load agent code, SB3 or
torch.

What this module never does: write to disk, train, evaluate, or call
evaluate.check_model_fingerprint (it raises SystemExit). stable-baselines3 and
torch are imported lazily inside load_pair, so importing this module costs
neither, and versions() only reads what is already loaded.
"""
from __future__ import annotations

import sys

from app import agent_catalog as C
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

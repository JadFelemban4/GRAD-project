"""Assemble display-only graphic readers. Never run or write scientific producers."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

from .results_comparisons import read_reference_panels
from .results_sets import read_agent_sets, read_training_panels
from .results_records import read_episode_panel


def build_graphics(root: Path) -> dict:
    root = Path(root).resolve()
    sets = read_agent_sets(root)
    for entry in sets:
        entry['panels'].append(read_episode_panel(root, entry['relative_path']))
    experiments = {}
    # A legacy run folder maps to its own experiment. No grouping of separate
    # run generations, and no checkpoint/inference reads.
    for run_dir in sorted(root.glob('runs*')):
        if not run_dir.is_dir() or not run_dir.resolve().is_relative_to(root):
            continue
        prefix = 'phase_d' if run_dir.name == 'runs' else run_dir.name.removeprefix('runs_')
        experiments[prefix] = read_training_panels(run_dir, root)
    return {'schema_version':1,'reference_panels':read_reference_panels(root),
            'agent_sets':sets,'experiment_panels':experiments}

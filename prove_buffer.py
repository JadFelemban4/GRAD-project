"""Prove that sizing the replay buffer to the run changes nothing that is learned.

Trains the SAME seed twice -- once with SB3's default 1 000 000 buffer, once
with a buffer sized to the run -- and compares every parameter of every network.

A replay buffer changes behaviour only when it EVICTS. Neither size evicts when
the run is shorter than the smaller buffer, so the two should agree bit for bit.
This asserts that rather than assuming it, because 3 of the 16 Phase D runs
completed on the old setting and the other 13 must be comparable with them.
"""
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
STEPS = 2500          # long enough to pass learning_starts and do real updates
SEED = 42

sys.path.insert(0, ROOT)
env = dict(os.environ, PYTHONIOENCODING="utf-8", OMP_NUM_THREADS="1")
tmp = tempfile.mkdtemp(prefix="bufproof_")

runs = {}
for label, buf in (("default_1e6", 1_000_000), ("sized", STEPS)):
    out = os.path.join(tmp, label)
    r = subprocess.run(
        [sys.executable, "train.py", "--steps", str(STEPS), "--seed", str(SEED),
         "--out", out, "--buffer", str(buf)],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=1800)
    print(f"{label:<12} buffer={buf:<9,} exit {r.returncode}")
    if r.returncode != 0:
        print(r.stdout[-1500:], r.stderr[-1500:])
        sys.exit(1)
    runs[label] = os.path.join(out, f"sighted_seed{SEED}", "final.zip")

from stable_baselines3 import SAC
import torch

a = SAC.load(runs["default_1e6"], device="cpu")
b = SAC.load(runs["sized"], device="cpu")

pa = dict(a.policy.state_dict())
pb = dict(b.policy.state_dict())
assert set(pa) == set(pb), "different parameter sets"

worst, nparam = 0.0, 0
for k in sorted(pa):
    d = (pa[k].float() - pb[k].float()).abs().max().item()
    nparam += pa[k].numel()
    worst = max(worst, d)

print()
print(f"parameters compared : {len(pa)} tensors, {nparam:,} values")
print(f"largest difference  : {worst:.3e}")
print()
if worst == 0.0:
    print("IDENTICAL -- buffer size does not affect what is learned at this "
          "step count.")
else:
    print("DIFFERENT -- the two settings are NOT interchangeable. Re-run all "
          "sixteen with one setting.")
sys.exit(0 if worst == 0.0 else 1)

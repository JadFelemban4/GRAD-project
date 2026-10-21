"""check_training_device.py -- is this machine fit to train the four-engine test? (decision 32)

    python check_training_device.py                        versions against requirements-lock.txt
    python check_training_device.py --identity OUT.json    + 600 SAC steps, seed 0, CPU, fingerprinted
    python check_training_device.py --fingerprint-dir RUN OUT.json   fingerprint an existing run directory
    python check_training_device.py --compare A.json B.json          two fingerprints: IDENTICAL or not

WHY THIS EXISTS. Training moves to another device (Ghassan, 21 October 2026), and rule 3
trains every seed, arm and engine in ONE environment. Two machines are one environment
only if they train the same agent from the same seed, bit for bit. A version check alone
cannot show that: CPU and CUDA train different agents from one seed (train.py), and a
library can change a result without changing its name. So the decision is made the way
results/B58_IDENTITY.md's level L8 made it between two code trees: 600 SAC steps, seed
0, CPU, one thread, on each machine, and every trained tensor, every recorded step and
the learning curve compared by their bytes. Run `--identity` on the team laptop and on
the training device, then `--compare` the two files. IDENTICAL means the device may train;
anything else means it may not, until the difference is found.

The --identity run is an identity test, not an experiment: it trains into a temporary
directory outside the repository and deletes it once the fingerprint is written. It is the
same command certificate level L8 ran (results/B58_IDENTITY.json, "L8_training"):
    train.py --engine b58 --steps 600 --seed 0 --device cpu --road extremes

WHAT A FINGERPRINT HOLDS. sha256 of every tensor in final.zip's .pth members (actor,
critics, targets, optimizer states, log_ent_coef), each over its dtype, shape and bytes;
stable-baselines3's counters from the zip's `data`; sha256 of every field of
train_record.npz; sha256 of curve.csv; the versions and the machine. The zip's `data`
member also holds timestamps, so it is never hashed whole.
"""
import argparse
import hashlib
import importlib.metadata as md
import io
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
LOCK = os.path.join(HERE, "requirements-lock.txt")
# The packages a trained agent's numbers pass through. A mismatch here fails the check;
# any other mismatch with the lock is printed as a warning.
CRITICAL = ("numpy", "torch", "stable_baselines3", "gymnasium", "scipy", "pandas")
COUNTERS = ("num_timesteps", "_total_timesteps", "_n_updates", "_episode_num", "seed",
            "learning_starts", "buffer_size", "batch_size")
IDENTITY_CMD = ["--engine", "b58", "--steps", "600", "--seed", "0", "--device", "cpu",
                "--road", "extremes"]


def _norm(name):
    return name.lower().replace("-", "_")


def read_lock(path=LOCK):
    """{package: version} and the Python version the lock names."""
    pins, python = {}, None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("# python=="):
                python = line.split("==", 1)[1].strip()
            elif line and not line.startswith("#") and "==" in line:
                name, ver = line.split("==", 1)
                pins[_norm(name)] = ver.strip()
    return pins, python


def installed():
    return {_norm(d.metadata["Name"]): d.version for d in md.distributions()
            if d.metadata["Name"]}


def check_versions():
    """Print every difference from the lock; return True when nothing critical differs."""
    pins, python = read_lock()
    have = installed()
    ok = True
    py = platform.python_version()
    print(f"python   {py}   (lock: {python})", "" if py == python else "  <-- DIFFERENT")
    ok &= py == python
    import torch
    print(f"torch    {torch.__version__}   (lock: {pins.get('torch')}, CPU build)",
          "" if torch.__version__ == f"{pins.get('torch')}+cpu" else "  <-- DIFFERENT")
    ok &= torch.__version__ == f"{pins.get('torch')}+cpu"
    warn = []
    for name, ver in sorted(pins.items()):
        got = have.get(name)
        if got == ver:
            continue
        if name in CRITICAL:
            print(f"{name:<18} {got}   (lock: {ver})  <-- DIFFERENT, critical")
            ok = False
        else:
            warn.append(f"{name} {got} (lock {ver})")
    if warn:
        print(f"{len(warn)} non-critical difference(s): " + "; ".join(warn))
    print("VERSIONS:", "match the lock" if ok else "DO NOT match the lock")
    return ok


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def _tensors(obj, prefix=""):
    import torch
    if torch.is_tensor(obj):
        yield prefix, obj.detach()
    elif isinstance(obj, dict):
        for k in sorted(obj, key=str):
            yield from _tensors(obj[k], f"{prefix}.{k}" if prefix else str(k))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from _tensors(v, f"{prefix}[{i}]")


def fingerprint_dir(run):
    """The fingerprint of one train.py run directory (OUT/<tag>/)."""
    import numpy as np
    import torch
    z = zipfile.ZipFile(os.path.join(run, "final.zip"))
    weights = {}
    for member in sorted(n for n in z.namelist() if n.endswith(".pth")):
        state = torch.load(io.BytesIO(z.read(member)), map_location="cpu", weights_only=True)
        for path, t in _tensors(state):
            a = t.numpy()
            weights[f"{member}:{path}"] = _sha(f"{a.dtype}|{a.shape}|".encode() + a.tobytes())
    data = json.loads(z.read("data"))
    rec = np.load(os.path.join(run, "train_record.npz"))
    record = {k: _sha(f"{rec[k].dtype}|{rec[k].shape}|".encode() + rec[k].tobytes())
              for k in sorted(rec.files)}
    with open(os.path.join(run, "curve.csv"), "rb") as fh:
        curve = _sha(fh.read())
    meta = {}
    if os.path.exists(os.path.join(run, "meta.json")):
        with open(os.path.join(run, "meta.json"), encoding="utf-8") as fh:
            m = json.load(fh)
        fp = m.get("fingerprint", m)
        meta = {k: fp.get(k) for k in ("plant_sha", "derived_sha", "engine", "engine_sha",
                                       "backend", "python") if k in fp}
    return dict(weights=weights, counters={k: data.get(k) for k in COUNTERS},
                record=record, curve=curve, meta=meta)


def describe_machine():
    pins, python = read_lock()
    have = installed()
    import torch
    return dict(machine=platform.platform(), processor=platform.processor(),
                python=platform.python_version(), torch=torch.__version__,
                packages={k: have.get(k) for k in CRITICAL})


def run_identity(out_json):
    tmp = tempfile.mkdtemp(prefix="device_check_")
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONIOENCODING="utf-8")
    try:
        cmd = [sys.executable, os.path.join(HERE, "train.py"), *IDENTITY_CMD, "--out", tmp]
        print("running:", " ".join(cmd))
        r = subprocess.run(cmd, cwd=HERE, env=env)
        if r.returncode != 0:
            sys.exit(f"train.py exited {r.returncode}; no fingerprint written")
        runs = [os.path.join(tmp, d) for d in os.listdir(tmp)
                if os.path.exists(os.path.join(tmp, d, "final.zip"))]
        if len(runs) != 1:
            sys.exit(f"expected one run directory with final.zip in {tmp}, found {len(runs)}")
        fp = fingerprint_dir(runs[0])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)        # an identity test, not an experiment
    fp["command"] = "train.py " + " ".join(IDENTITY_CMD)
    fp["device"] = describe_machine()
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(fp, fh, indent=1)
    print(f"fingerprint written to {out_json}: {len(fp['weights'])} tensors, "
          f"{len(fp['record'])} record fields")


def compare(a_path, b_path):
    with open(a_path, encoding="utf-8") as fh:
        a = json.load(fh)
    with open(b_path, encoding="utf-8") as fh:
        b = json.load(fh)
    bad = []
    for part in ("weights", "record"):
        for k in sorted(set(a[part]) | set(b[part])):
            if a[part].get(k) != b[part].get(k):
                bad.append(f"{part} {k}")
    for k in COUNTERS:
        if a["counters"].get(k) != b["counters"].get(k):
            bad.append(f"counter {k}: {a['counters'].get(k)} vs {b['counters'].get(k)}")
    if a["curve"] != b["curve"]:
        bad.append("curve.csv")
    print(f"A: {a.get('device', {}).get('machine')}  |  B: {b.get('device', {}).get('machine')}")
    print(f"compared {len(a['weights'])} tensors, {len(a['record'])} record fields, "
          f"{len(COUNTERS)} counters and the curve")
    for x in bad[:20]:
        print("  DIFFERENT:", x)
    print("VERDICT:", "IDENTICAL TRAINING" if not bad else f"NOT IDENTICAL ({len(bad)} differences)")
    return not bad


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--identity", metavar="OUT.json")
    g.add_argument("--fingerprint-dir", nargs=2, metavar=("RUN", "OUT.json"))
    g.add_argument("--compare", nargs=2, metavar=("A.json", "B.json"))
    a = ap.parse_args()
    if a.compare:
        sys.exit(0 if compare(*a.compare) else 1)
    if a.fingerprint_dir:
        fp = fingerprint_dir(a.fingerprint_dir[0])
        fp["device"] = describe_machine()
        with open(a.fingerprint_dir[1], "w", encoding="utf-8") as fh:
            json.dump(fp, fh, indent=1)
        print(f"fingerprint of {a.fingerprint_dir[0]} written to {a.fingerprint_dir[1]}")
        return
    ok = check_versions()
    if a.identity:
        if not ok:
            sys.exit("the versions do not match the lock; fix them before the identity run")
        run_identity(a.identity)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

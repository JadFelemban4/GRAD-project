"""reconstruct_meta.py -- a certificate for agents trained before train.py wrote one.

    python reconstruct_meta.py                        runs/terrain_dt1, episodes 1 and 20
    python reconstruct_meta.py runs/terrain_dt1 --episodes all
    python reconstruct_meta.py --check                verify everything, write nothing
    python reconstruct_meta.py --force                rewrite certificates already there

WHAT THIS IS, AND WHAT IT IS NOT
--------------------------------
`train.py` writes `meta.json` -- the plant fingerprint -- BEFORE an agent's first
step, from the live objects (fingerprint.py, AUDIT2.md C2-1). The twenty agents
of the 29 September retrain were trained by the `train.py` of `JMF-2340550`,
which wrote `config.json` and no `meta.json`. Every guard on the merged tree
therefore calls them "plant unknown", and the agent replay page (`/agents`)
lists none of them.

This script writes `meta_reconstructed.json` beside such an agent. It is NOT
`meta.json`, and it is never named that:

- `evaluate.py` and `train.py` read `meta.json`. They still refuse these
  agents, exactly as before. No scoring path and no resume path changed.
- Only `app/agent_catalog.py` reads `meta_reconstructed.json`, for the replay
  page, which shows one episode as an illustration and says on the page that
  the certificate was reconstructed, when, and against what.

A certificate written after the fact is worth only the evidence inside it, so
nothing is written unless ALL of this holds for the agent:

1. `config.json` says the run finished, and `final.zip` is a readable
   stable-baselines3 zip holding the steps the config asked for.
2. The plant's CODE (fingerprint.PLANT_FILES, docstrings stripped) is identical
   on the live tree, at the commit `config.json` names, and at the commit that
   added the agent's scores to git. `config.json` records `git_dirty`, so the
   first of those is a statement about the commit, not about the tree the run
   used -- which is why step 4 exists.
3. The derived plant constants (`data/derived_params.json`, by value) are the
   same at the scores' commit and now, and the data fingerprint `config.json`
   recorded is the one the live constants were derived from.
4. THE AGENT REPRODUCES ITS COMMITTED SCORES. The chosen frozen episodes are
   re-run through `evaluate.run_episode` on the live plant, the network loaded
   exactly as `evaluate.py` and the replay page load it, and every number of
   every result -- return, damage both ways, fuel, torque violation, peak
   turbine, knock events -- must EQUAL the row committed in
   `results/agents/<set>/<tag>/eval_summary.json`. Equal, not close: a
   different plant, a different network or a different device moves the last
   digits. That file must be tracked and unmodified.

What it still cannot show, and the certificate says so: that the tree was
clean WHILE the agent trained. Steps 2 to 4 show the plant was the same before
training (the named commit), after it (the scores' commit) and now, and that
the scores made in that session are reproduced to the digit.

The certificate names the `final.zip` it re-ran by sha, and
`app/agent_catalog.py` refuses any other zip found beside it. It also moves
with the plant like any fingerprint: after the next plant change these agents
are refused again, which is the guard doing its job.

`plant_sha` depends on the Python version that computes it (30 September:
`ast.dump` prints differently on 3.11, 3.12 and 3.13), so a certificate written
here is good on the interpreter that wrote it.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fingerprint as FP                                        # noqa: E402
from app.agent_catalog import AGENT_NAME, RECONSTRUCTED         # noqa: E402

DEFAULT_SET = "runs/terrain_dt1"
DEFAULT_EPISODES = (1, 20)
# config.json of the 29 September train.py names the road in words, not by key.
ROAD_OF_TEXT = {"a new road every episode (TerrainTrainingEnv)": "terrain"}
STATEMENT = ("NOT written when training started. Reconstructed afterwards from "
             "config.json, and only after the frozen episodes listed under "
             "'evidence' were re-run on the live plant and equalled the committed "
             "scores exactly. It cannot show that the tree was clean while the "
             "agent trained.")


class Refused(Exception):
    """One agent that gets no certificate, with the reason."""


def _git(*args):
    out = subprocess.run(("git",) + args, cwd=HERE, capture_output=True)
    return out.stdout if out.returncode == 0 else None


def plant_sha_at(commit):
    """fingerprint.py's code-only plant hash, over the files AS COMMITTED."""
    h = hashlib.sha256()
    for name in FP.PLANT_FILES:
        raw = _git("show", f"{commit}:{name}")
        if raw is None:
            raise Refused(f"git cannot show {name} at {commit}")
        raw = raw.replace(b"\r\n", b"\n")
        code = FP._code_only(raw.decode("utf-8", errors="replace"))
        h.update(code.encode("utf-8") if code is not None else raw)
    return h.hexdigest()[:16]


def derived_sha_of(params):
    """train.derived_sha's hash, over a dict already read: the values of
    data/derived_params.json, its '_' bookkeeping keys left out."""
    vals = {k: v for k, v in params.items() if not k.startswith("_")}
    return hashlib.sha256(json.dumps(vals, sort_keys=True).encode()).hexdigest()[:16]


def live_derived():
    with open(os.path.join(HERE, "data", "derived_params.json"), encoding="utf-8") as fh:
        return json.load(fh)


def committed(path):
    """The short hash of the commit that ADDED `path`, or None. Refuses a file
    that is untracked or differs from HEAD: the scores must be the committed ones."""
    if _git("ls-files", "--error-unmatch", path) is None:
        raise Refused(f"{path} is not tracked by git")
    if subprocess.run(("git", "diff", "--quiet", "HEAD", "--", path), cwd=HERE).returncode:
        raise Refused(f"{path} differs from the committed file")
    added = _git("log", "--diff-filter=A", "--format=%h", "--", path)
    return added.decode().split()[-1] if added and added.strip() else None


def parse_episodes(text, n):
    if text == "all":
        return tuple(range(1, n + 1))
    idx = tuple(sorted({int(t) for t in text.split(",")}))
    if not idx or idx[0] < 1 or idx[-1] > n:
        raise SystemExit(f"--episodes takes 'all' or numbers from 1 to {n}, e.g. 1,20")
    return idx


# ---------------------------------------------------------------- the re-run
_MODEL = {}


def _init_worker():
    try:
        import torch
        torch.set_num_threads(1)
    except ImportError:
        pass


def _rerun(job):
    """One frozen episode of one agent, as evaluate.py scores it. The network
    is loaded with NO device argument, as evaluate.py and the replay page load
    it, so the device that reproduced the scores is the one the page will use."""
    agent_dir, idx = job
    import evaluate as E
    from stable_baselines3 import SAC
    if agent_dir not in _MODEL:
        _MODEL[agent_dir] = SAC.load(os.path.join(HERE, agent_dir, "final"))
    model = _MODEL[agent_dir]
    seed, weights = E.EPISODES[idx - 1]
    sighted = "blind" not in os.path.basename(agent_dir)      # evaluate.py's own arm rule
    row = E.run_episode(E.agent_policy(model), seed, weights, sighted)
    return agent_dir, idx, row, str(model.device)


def differences(got, want):
    """Every key on which a re-run row differs from the committed one."""
    return [f"{k}: committed {want.get(k)!r} re-run {got.get(k)!r}"
            for k in sorted(set(got) | set(want)) if got.get(k) != want.get(k)]


# ---------------------------------------------------------------- one agent
def static_evidence(set_dir, tag, live_plant, derived):
    """Steps 1 to 3 for one agent: everything that needs no episode. Returns
    (config, the committed episode rows, the evidence so far, the zip's budget)."""
    agent_dir = os.path.join(HERE, set_dir, tag)
    if os.path.exists(os.path.join(agent_dir, "meta.json")):
        raise Refused("has meta.json, its own certificate: nothing to reconstruct")
    try:
        with open(os.path.join(agent_dir, "config.json"), encoding="utf-8") as fh:
            cfg = json.load(fh)
    except (OSError, ValueError):
        raise Refused("no readable config.json") from None
    if cfg.get("status") != "finished":
        raise Refused(f"config.json says status {cfg.get('status')!r}, not 'finished'")
    if cfg.get("tag") != tag or bool(cfg.get("preview")) != ("blind" not in tag):
        raise Refused("config.json describes another agent (tag or preview)")
    road = cfg.get("road") or ROAD_OF_TEXT.get(cfg.get("roads"))
    if road is None:
        raise Refused(f"config.json names a road this script does not know: {cfg.get('roads')!r}")
    budget = FP.model_budget(os.path.join(agent_dir, "final.zip"))
    if budget is None:
        raise Refused("final.zip is missing or is not a stable-baselines3 zip")
    if budget["num_timesteps"] != cfg.get("steps"):
        raise Refused(f"final.zip holds {budget['num_timesteps']} steps, config.json asked for "
                      f"{cfg.get('steps')}")

    scores = f"results/agents/{os.path.basename(os.path.normpath(set_dir))}/{tag}/eval_summary.json"
    scored_commit = committed(scores)
    with open(os.path.join(HERE, scores), encoding="utf-8") as fh:
        rows = json.load(fh)["episodes"]

    plant_code = []
    for commit, what in ((cfg.get("git_commit"), "config.json's git_commit"),
                         (scored_commit, "the commit that added the scores")):
        if not commit:
            raise Refused(f"{what} is not recorded")
        sha = plant_sha_at(commit)
        if sha != live_plant:
            raise Refused(f"the plant's code at {commit} ({what}) is {sha}, the live plant is "
                          f"{live_plant}")
        plant_code.append({"commit": commit, "what": what, "plant_sha": sha})

    then = _git("show", f"{scored_commit}:data/derived_params.json")
    if then is None:
        raise Refused(f"git cannot show data/derived_params.json at {scored_commit}")
    then_sha, now_sha = derived_sha_of(json.loads(then)), derived_sha_of(derived)
    if then_sha != now_sha:
        raise Refused(f"the derived constants at {scored_commit} ({then_sha}) are not the live "
                      f"ones ({now_sha})")
    data_cfg = (cfg.get("plant_inputs") or {}).get("data_sha1")
    data_live = (derived.get("_inputs") or {}).get("data_sha1")
    if not data_cfg or data_cfg != data_live:
        raise Refused(f"config.json's data fingerprint {data_cfg!r} is not the one the live "
                      f"constants were derived from ({data_live!r})")

    evidence = {"plant_code": plant_code,
                "derived": {"derived_sha": now_sha, "at_commit": scored_commit,
                            "data_sha1": data_live},
                "scores": scores, "scores_commit": scored_commit}
    return dict(cfg, road=road), rows, evidence, budget


def certificate(cfg, evidence, budget, device, derived):
    """The fingerprint train.py would have written, from the LIVE objects, with
    the block that says it was not written then. What describes this moment
    (the head, the dirty flag, the interpreter) goes inside the block, so no
    top-level field can be read as a record of the training session."""
    fp = FP.plant_fingerprint(
        protocol="phase-d", train_dt=float(cfg["dt"]), train_duration=float(cfg["duration_s"]),
        steps_requested=int(cfg["steps"]), seed=int(cfg["seed"]),
        use_preview=bool(cfg["preview"]), tag=cfg["tag"], train_road=cfg["road"],
        train_device=cfg.get("device"), derived_sha=derived_sha_of(derived))
    at = {k: fp.pop(k, None) for k in ("git_head", "git_dirty", "git_dirty_plant_files", "python")}
    fp["reconstructed"] = {
        "statement": STATEMENT,
        "by": os.path.basename(__file__),
        "written": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "at": at,
        "zip_sha": budget["sha"],
        "reproduced_device": device,
        "config": {k: cfg.get(k) for k in ("git_commit", "git_dirty", "started", "finished")},
        "evidence": evidence,
    }
    return fp


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("set_dir", nargs="?", default=DEFAULT_SET,
                    help=f"a folder of <tag>/final.zip and config.json (default {DEFAULT_SET})")
    ap.add_argument("--episodes", default=",".join(map(str, DEFAULT_EPISODES)),
                    help="frozen episodes to re-run per agent: 'all', or numbers like 1,20")
    ap.add_argument("--check", action="store_true", help="verify and report; write nothing")
    ap.add_argument("--force", action="store_true",
                    help="re-verify and rewrite certificates that already exist")
    ap.add_argument("--workers", type=int, default=max(1, min(8, (os.cpu_count() or 2) - 2)))
    a = ap.parse_args()

    # One thread per worker, as train_all.py runs them. Set here, not at
    # import: a worker inherits it, and importing this module changes nothing.
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    import evaluate as E
    set_dir = a.set_dir.replace("\\", "/").rstrip("/")
    root = os.path.join(HERE, set_dir)
    if not os.path.isdir(root):
        raise SystemExit(f"{set_dir} is not a directory")
    episodes = parse_episodes(a.episodes, len(E.EPISODES))
    tags = sorted(t for t in os.listdir(root)
                  if AGENT_NAME.fullmatch(t) and os.path.isdir(os.path.join(root, t)))
    if not tags:
        raise SystemExit(f"{set_dir} holds no sighted_seed<N> or blind_seed<N> folder")

    live_plant = FP._sha_files(FP.PLANT_FILES)
    derived = live_derived()
    print(f"set            : {set_dir}   ({len(tags)} agents)")
    print(f"live plant_sha : {live_plant}   (python {sys.version.split()[0]})")
    print(f"episodes re-run: {', '.join(map(str, episodes))} of {len(E.EPISODES)}, per agent\n")

    ready, refused, skipped = {}, {}, []
    for tag in tags:
        if os.path.exists(os.path.join(root, tag, RECONSTRUCTED)) and not (a.force or a.check):
            skipped.append(tag)
            continue
        try:
            ready[tag] = static_evidence(set_dir, tag, live_plant, derived)
        except Refused as why:
            refused[tag] = str(why)

    jobs = [(f"{set_dir}/{tag}", i) for tag in ready for i in episodes]
    got, device, t0 = {}, {}, time.time()
    if jobs:
        print(f"re-running {len(jobs)} episodes on {a.workers} workers ...")
        with cf.ProcessPoolExecutor(max_workers=a.workers, initializer=_init_worker) as pool:
            for n, (agent_dir, idx, row, dev) in enumerate(pool.map(_rerun, jobs), 1):
                tag = os.path.basename(agent_dir)
                got[tag, idx] = row
                device.setdefault(tag, set()).add(dev)
                if n % 10 == 0 or n == len(jobs):
                    print(f"  {n}/{len(jobs)}   {time.time() - t0:.0f} s")

    written = []
    for tag, (cfg, rows, evidence, budget) in ready.items():
        bad = [f"episode {i}: {d}" for i in episodes for d in differences(got[tag, i], rows[i - 1])]
        if bad:
            refused[tag] = "the re-run does not equal the committed scores -- " + "; ".join(bad[:4])
            continue
        if len(device[tag]) != 1:
            refused[tag] = f"the network loaded on more than one device: {sorted(device[tag])}"
            continue
        evidence = dict(evidence, episodes=list(episodes), identical=True)
        if not a.check:
            FP.write(os.path.join(root, tag, RECONSTRUCTED),
                     certificate(cfg, evidence, budget, device[tag].pop(), derived))
        written.append(tag)

    print()
    for tag in tags:
        if tag in refused:
            print(f"  REFUSED   {tag}: {refused[tag]}")
        elif tag in skipped:
            print(f"  kept      {tag}: {RECONSTRUCTED} is already there (--force rewrites it)")
        else:
            print(f"  {'verified ' if a.check else 'written  '} {tag}: re-ran episode"
                  f"{'s' if len(episodes) > 1 else ''} {', '.join(map(str, episodes))}, "
                  "equal to the committed scores")
    print(f"\n{len(written)} {'verified' if a.check else 'written'}, {len(skipped)} kept, "
          f"{len(refused)} refused.")
    if written and not a.check:
        print(f"Each certificate is {set_dir}/<tag>/{RECONSTRUCTED}. evaluate.py and train.py do\n"
              "not read it; the agent replay page does, and says it was reconstructed.")
    return 1 if refused else 0


if __name__ == "__main__":
    sys.exit(main())

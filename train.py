"""train.py — Phase C, steps C1 and C4.

Trains a SAC agent on the engine environment and saves everything Phase D needs.

    pip install "stable-baselines3[extra]"      # once; also uncomment it in requirements.txt

    python train.py --steps 50000 --seed 0                 # sighted, a new road every episode
    python train.py --steps 50000 --seed 0 --no-preview    # the blinded baseline
    python train.py --steps 50000 --seed 0 --fixed-road    # the locked climb only, as before

Output goes to runs/terrain_dt1/<tag>/, NOT runs/<tag>/ -- see --out below.

WHAT CHANGED ON 27 SEPTEMBER, AND WHY
-------------------------------------
Two things, both before any Phase D training on the locked 130 km/h climb:

  * dt = 1.0, passed explicitly. It was never passed, so every earlier run
    trained at 0.2 s and was scored by evaluate.py at 1.0 s. See build_env.
  * a new road every episode (engine_env.TerrainTrainingEnv). On one fixed
    climb the road ahead never changes, so preview has nothing to say.
    evaluate.py still scores on the locked climb alone.

HOW LONG THIS TAKES — read before you start
--------------------------------------------
MEASURED 27 September 2026 on the 20-core team machine: 13.7 steps/s for one
run alone, with SAC's gradient updates running, on the varied roads at
dt = 1.0. 50 000 steps is about an hour. Ten runs sharing the machine ran at
about 4.5 steps/s each on 19 September, 173 min for the lot -- about five times
better than running them one after another. Cap each at OMP_NUM_THREADS=1.

      50,000 steps    ~1 h alone,   ~3 h with ten sharing a 20-core box
     300,000 steps    ~6 h alone

Agree who takes which seed BEFORE anyone starts, or you will end up with three
copies of seed 0. `python train_all.py` launches every seed of both halves on
one machine, one process each.

TEN SEEDS, NOT FIVE (29 September 2026). The ablation is paired by seed, and
with five pairs the smallest two-sided p-value an exact Wilcoxon signed-rank
test can return is 2/32 = 0.0625: five seeds could never show a preview effect
at the 5 % level however large it was. Ten pairs can (2/1024).

THE GPU DOES NOT HELP HERE, AND IT WAS MEASURED (29 September 2026). One
training step, one thread, on the team laptop: the plant 61.6 ms, SAC's
gradient update 11.5 ms, choosing the action 0.2 ms -- 13.6 steps/s, and the
network is 16 % of the step. The plant is numpy on the CPU. Even a GPU that
made the network free would make a run at most 1.19x faster, and twenty runs
at once would need twenty CUDA contexts on a 4 GB laptop card. Training
therefore runs on the CPU (--device cpu, the default); the installed torch is
a CPU build anyway. Re-measure before changing it.

WHAT IS RECORDED, so the agents are documented and not just saved
-----------------------------------------------------------------
  config.json          every SAC setting, the versions, the git commit, the
                       plant's data fingerprint, wall time and steps/s
  curve.csv            one row per episode: return, length, road
  train_record.npz     EVERY step of training: the action the agent took, the
                       observation it took it from, the reward and what the
                       engine did (ActionRecorder, below)
  final.zip, ckpt_*    the model itself (gitignored; record_agents.py exports
                       the policy weights into results/agents/)

Checkpoints are written every 10,000 steps, so a closed laptop costs you minutes
rather than the whole run. Re-running the same seed resumes from its checkpoint.
"""
import argparse
import glob
import json
import platform
import re
import os
import subprocess
import time
from datetime import datetime

import numpy as np

from engine_env import SupervisoryTunerEnv, TerrainTrainingEnv, make_grade_climb

try:
    from stable_baselines3 import SAC
    from stable_baselines3.common.monitor import Monitor
    from stable_baselines3.common.callbacks import BaseCallback, CallbackList, CheckpointCallback
except ImportError:
    raise SystemExit(
        "stable-baselines3 is not installed.\n\n"
        '    pip install "stable-baselines3[extra]"\n\n'
        "Then uncomment the two lines under 'Phase C onward' in requirements.txt\n"
        "so the rest of the team installs the same thing."
    )


def build_env(use_preview, seed, duration, dt=1.0, fixed_road=False):
    """The training environment. dt is passed EXPLICITLY, on both halves.

    Until 27 September this built SupervisoryTunerEnv(make_grade_climb(...))
    with no dt at all, so both the cycle and the env took their 0.2 s default
    while evaluate.py scores at 1.0 s. Since AUDIT.md M16 made the slew limit
    SLEW * dt, the same network output moved each actuator five times further
    per step at evaluation than it ever could in training: every agent trained
    before that date was scored in a discretisation it had never seen.

    dt = 1.0 matches the protocol, and it is also five times cheaper per
    simulated second -- a step costs six combustion evaluations whatever dt is --
    so the same step budget buys five times the episodes: 50 000 steps is 55
    episodes of 900 s instead of 11.

    By default every episode is a new road (engine_env.TerrainTrainingEnv).
    --fixed-road trains on the locked climb alone, as every run before
    27 September did.
    """
    if fixed_road:
        env = SupervisoryTunerEnv(make_grade_climb(duration=duration, dt=dt), dt=dt,
                                  use_preview=use_preview, seed=seed)
    else:
        env = TerrainTrainingEnv(duration=duration, dt=dt, use_preview=use_preview, seed=seed)
    return Monitor(env)


# What the engine did on each training step, read off the step's info dict.
REC_INFO = ("t_turb", "t_oil", "t_block", "torque_req", "torque", "mdot_fuel", "ki",
            "spark", "lam", "egt_c", "r_fuel", "r_life", "r_resp")
REC_F32 = ("r_fuel", "r_life", "r_resp")
CHUNK = 10_000          # the checkpoint interval; a chunk is written with each one


class ActionRecorder(BaseCallback):
    """Every action the agent takes while it learns, and what it cost.

    Written 29 September 2026: until then a training run left a model and a
    one-row-per-episode curve, and nothing of the 50 000 decisions in between.

    Per step: the timestep, the episode, the ACTION (the network's output in
    [-1, 1], exactly what went to env.step), the OBSERVATION it was chosen from
    (which carries the grade now and the four preview values, zero when
    blinded), the reward, and the engine quantities in REC_INFO. The action,
    reward and reward terms are float32; the observation and engine quantities
    float16, which is far finer than anything they are read for.

    A chunk is written every CHUNK steps, with the checkpoint, so a resumed run
    keeps what it had recorded; train.py merges the chunks at the end.
    """

    def __init__(self, outdir):
        super().__init__()
        self.dir = os.path.join(outdir, "record")
        os.makedirs(self.dir, exist_ok=True)
        self._clear()

    def _clear(self):
        self.buf = {k: [] for k in ("step", "episode", "action", "obs", "reward") + REC_INFO}

    def _on_training_start(self):
        # Episodes continue their numbering across a resume. learn() resets the
        # environment, so a resumed run always starts a fresh episode.
        prev = [np.load(f)["episode"] for f in glob.glob(os.path.join(self.dir, "rec_*.npz"))]
        prev = [p for p in prev if len(p)]
        self.episode = int(max(p.max() for p in prev)) + 1 if prev else 0

    def _on_step(self):
        b = self.buf
        b["step"].append(self.num_timesteps)
        b["episode"].append(self.episode)
        b["action"].append(np.asarray(self.locals["actions"][0], np.float32))
        # _last_obs is the observation the action was chosen from: SB3 replaces
        # it only after this callback has run.
        b["obs"].append(np.asarray(self.model._last_obs[0], np.float32))
        b["reward"].append(float(self.locals["rewards"][0]))
        info = self.locals["infos"][0]
        for k in REC_INFO:
            b[k].append(float(info.get(k, np.nan)))
        if self.locals["dones"][0]:
            self.episode += 1
        if self.num_timesteps % CHUNK == 0:
            self._flush()
        return True

    def _on_training_end(self):
        self._flush()

    def _flush(self):
        b = self.buf
        if not b["step"]:
            return
        path = os.path.join(self.dir, f"rec_{b['step'][0]:07d}_{b['step'][-1]:07d}.npz")
        np.savez_compressed(path, **_record_arrays(b))
        self._clear()


def _record_arrays(b):
    out = dict(step=np.asarray(b["step"], np.int32), episode=np.asarray(b["episode"], np.int32),
               action=np.asarray(b["action"], np.float32), reward=np.asarray(b["reward"], np.float32),
               obs=np.asarray(b["obs"], np.float16))
    for k in REC_INFO:
        out[k] = np.asarray(b[k], np.float32 if k in REC_F32 else np.float16)
    return out


def merge_records(outdir):
    """The chunks, in step order, as one train_record.npz. A step recorded twice
    (a chunk written after the last checkpoint, then the same steps again on
    resume) keeps its LAST recording, the one the saved model continued from."""
    files = glob.glob(os.path.join(outdir, "record", "rec_*.npz"))
    if not files:
        return None
    parts = [dict(np.load(f)) for f in sorted(files, key=os.path.getmtime)]
    cat = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    rev = cat["step"][::-1]
    _, first_in_rev = np.unique(rev, return_index=True)
    keep = np.sort(len(rev) - 1 - first_in_rev)
    cat = {k: v[keep] for k, v in cat.items()}
    path = os.path.join(outdir, "train_record.npz")
    np.savez_compressed(path, **cat)
    return path, int(len(keep))


def _git(*args):
    try:
        return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def run_config(a, tag, model, outdir):
    """Everything needed to say what this agent is, written beside it."""
    import stable_baselines3
    import torch
    import gymnasium
    try:
        with open(os.path.join("data", "derived_params.json")) as fh:
            plant = json.load(fh).get("_inputs")
    except FileNotFoundError:
        plant = None
    return dict(
        tag=tag, seed=a.seed, preview=not a.no_preview, steps=a.steps, dt=a.dt,
        duration_s=a.duration, steps_per_episode=int(round(a.duration / a.dt)),
        roads="the locked climb only" if a.fixed_road else "a new road every episode (TerrainTrainingEnv)",
        device=str(model.device), algorithm="SAC",
        sac=dict(learning_rate=a.lr, buffer_size=model.buffer_size, batch_size=model.batch_size,
                 learning_starts=model.learning_starts, gamma=model.gamma, tau=model.tau,
                 train_freq=str(model.train_freq), gradient_steps=model.gradient_steps,
                 ent_coef=str(model.ent_coef), target_entropy=float(model.target_entropy),
                 policy="MlpPolicy", net_arch=str(model.policy.net_arch)),
        versions=dict(python=platform.python_version(), stable_baselines3=stable_baselines3.__version__,
                      torch=torch.__version__, gymnasium=gymnasium.__version__, numpy=np.__version__),
        git_commit=_git("rev-parse", "--short", "HEAD"),
        git_dirty=bool(_git("status", "--porcelain", "--untracked-files=no")),
        plant_inputs=plant, output=outdir.replace(os.sep, "/"),
        machine=dict(system=platform.system(), processor=platform.processor(), cpus=os.cpu_count(),
                     omp_threads=os.environ.get("OMP_NUM_THREADS")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=50_000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-preview", action="store_true",
                    help="the blinded baseline for Phase D step D3")
    ap.add_argument("--duration", type=float, default=900.0,
                    help="episode length in seconds; 900 is the standard scenario")
    ap.add_argument("--lr", type=float, default=3e-4,
                    help="divide by 3 if the reward curve climbs then collapses")
    ap.add_argument("--dt", type=float, default=1.0,
                    help="step length in seconds; 1.0 is what evaluate.py scores at")
    ap.add_argument("--fixed-road", action="store_true",
                    help="train on the locked climb only, as runs before 27 Sep did")
    ap.add_argument("--device", default="cpu",
                    help="cpu (measured: the plant is 84 %% of a step, see the docstring), "
                         "cuda or auto")
    # NOT "runs". train.py resumes from any checkpoint in its output folder, and
    # runs/ holds the ten agents trained at 110 km/h and dt = 0.2 on 19 September.
    # Pointing a new run there would silently CONTINUE one of those instead of
    # starting fresh on the new roads.
    ap.add_argument("--out", default=None,
                    help="default runs/terrain_dt1, or runs/locked_dt1 with --fixed-road")
    a = ap.parse_args()
    if a.out is None:
        a.out = os.path.join("runs", ("locked" if a.fixed_road else "terrain")
                             + f"_dt{a.dt:g}".replace(".", "p"))

    tag = f"{'blind' if a.no_preview else 'sighted'}_seed{a.seed}"
    outdir = os.path.join(a.out, tag)
    os.makedirs(outdir, exist_ok=True)

    print(f"configuration : {'BLINDED (no preview)' if a.no_preview else 'sighted'}")
    print(f"roads         : {'the locked climb only' if a.fixed_road else 'a new road every episode'}")
    print(f"step          : dt = {a.dt:g} s, {a.duration / a.dt:.0f} steps per episode, "
          f"{a.steps / (a.duration / a.dt):.0f} episodes")
    print(f"seed          : {a.seed}")
    print(f"steps         : {a.steps:,}")
    # MEASURED 27 September 2026, one run alone on the team machine, gradient
    # updates running, varied roads at dt = 1.0: 13.7 steps/s. This read 3.0
    # until then, a figure the sep17 branch had already shown was 6x too slow.
    # Re-measure if you change the plant or move machines; with ten runs
    # sharing one box, expect about a third of this each.
    STEPS_PER_S = 13.7
    mins_est = a.steps / STEPS_PER_S / 60
    print(f"estimate      : about {mins_est:.0f} minutes "
          f"({mins_est / 60:.1f} h) at a measured {STEPS_PER_S:.1f} steps/s on CPU")
    print(f"output        : {outdir}/\n")

    env = build_env(not a.no_preview, a.seed, a.duration, a.dt, a.fixed_road)

    ckpt_path = os.path.join(outdir, "checkpoint.zip")

    # AUDIT.md H6. The periodic callback writes `ckpt_<n>_steps.zip` every
    # 10 000 steps; this used to look ONLY for `checkpoint.zip`, which is
    # written once, after learn() returns. So a laptop closed at hour 3 of a
    # 4.6-hour run had nothing the script would load -- exactly the case the
    # docstring promised to cover. And on the one path where checkpoint.zip did
    # exist (a finished run) it restarted the step count from zero and trained
    # a second full run.
    periodic = sorted(glob.glob(os.path.join(outdir, "ckpt_*_steps.zip")),
                      key=lambda f: int(re.search(r"ckpt_(\d+)_steps", f).group(1)))
    resume_from = periodic[-1] if periodic else (ckpt_path if os.path.exists(ckpt_path) else None)
    done_steps = 0
    if resume_from:
        m = re.search(r"ckpt_(\d+)_steps", resume_from)
        done_steps = int(m.group(1)) if m else 0
        print(f"resuming from {resume_from} at {done_steps} steps")
        model = SAC.load(resume_from, env=env, device=a.device)
    else:
        model = SAC("MlpPolicy", env, seed=a.seed, learning_rate=a.lr,
                    verbose=1, tensorboard_log=None, device=a.device)

    cb = CallbackList([CheckpointCallback(save_freq=CHUNK, save_path=outdir,
                                          name_prefix="ckpt", verbose=0),
                       ActionRecorder(outdir)])

    cfg_path = os.path.join(outdir, "config.json")
    cfg = run_config(a, tag, model, outdir)
    cfg.update(started=datetime.now().isoformat(timespec="seconds"), resumed_from=resume_from,
               status="running")
    with open(cfg_path, "w") as fh:
        json.dump(cfg, fh, indent=1)

    t0 = time.time()
    remaining = max(0, a.steps - done_steps)
    if remaining == 0:
        print(f"already at {done_steps} of {a.steps} steps; nothing to do")
    # reset_num_timesteps=False so the resumed run CONTINUES the schedule
    # rather than starting a second one (AUDIT.md H6).
    model.learn(total_timesteps=remaining, callback=cb, progress_bar=False,
                reset_num_timesteps=(resume_from is None))
    mins = (time.time() - t0) / 60

    model.save(os.path.join(outdir, "final"))
    model.save(ckpt_path)
    merged = merge_records(outdir)

    # the learning curve — Monitor recorded every episode return
    rewards = np.array(env.get_episode_rewards(), dtype=float)
    lengths = np.array(env.get_episode_lengths(), dtype=float)
    # The road each episode ran on. Returns from different roads are not on one
    # scale -- a flat road has nothing to protect -- so the curve is only
    # readable with the road beside it. road_log[i] is episode i's road; it has
    # one entry more than there are finished episodes, because the last reset
    # starts an episode that learn() never finishes.
    log = list(getattr(env.unwrapped, "road_log", []))
    roads = [log[i] if i < len(log) else ("locked" if a.fixed_road else "?")
             for i in range(len(rewards))]
    with open(os.path.join(outdir, "curve.csv"), "w") as fh:
        fh.write("episode,return,length,road\n")
        for i, (r, n) in enumerate(zip(rewards, lengths)):
            fh.write(f"{i},{r:.6f},{n:.0f},{roads[i]}\n")

    cfg.update(status="finished", finished=datetime.now().isoformat(timespec="seconds"),
               wall_min_this_session=round(mins, 1),
               steps_per_s_this_session=round(remaining / max(mins * 60, 1e-9), 2),
               episodes=int(len(rewards)), total_timesteps=int(model.num_timesteps),
               recorded_steps=merged[1] if merged else 0)
    with open(cfg_path, "w") as fh:
        json.dump(cfg, fh, indent=1)

    print(f"\ntrained in {mins:.0f} min | {len(rewards)} episodes"
          + (f" | {merged[1]:,} steps recorded in {merged[0]}" if merged else ""))
    # This used to compare the first five episode returns with the last five
    # and call the curve improved. It cannot say that: every episode draws new
    # preference weights, and now a new road, so consecutive returns are scored
    # with different rulers. On 19 September eleven episodes ranged -506 to
    # +644 and the largest was in the FIRST five (evaluate.py's docstring).
    # Learning is judged on the frozen episodes and nowhere else.
    print("\n  Episode returns vary with the road and the preference weights, so this")
    print("  curve cannot show learning. Score the run with evaluate.py:")
    print(f"      python evaluate.py {outdir}")
    print("  If the agent does not beat the baseline there, re-run test_reward.py")
    print("  before changing anything else -- a broken reward trains normally.")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        if len(rewards) >= 5:
            k = max(1, len(rewards) // 40)
            smooth = np.convolve(rewards, np.ones(k) / k, mode="valid")
            plt.figure(figsize=(7, 4))
            plt.plot(rewards, lw=0.8, alpha=0.35, color="#9AA7AE", label="episode return")
            plt.plot(np.arange(len(smooth)) + k - 1, smooth, lw=2, color="#E8871E",
                     label=f"moving average ({k})")
            plt.axhline(0, color="#5E6C75", lw=0.8, ls="--")
            plt.xlabel("episode"); plt.ylabel("return")
            plt.title(f"{tag} — {a.steps:,} steps")
            plt.legend(); plt.tight_layout()
            png = os.path.join(outdir, "curve.png")
            plt.savefig(png, dpi=130)
            print(f"  curve written to {png}")
    except ImportError:
        print("  (matplotlib not installed — curve.csv written, no plot)")

    print("\nnext: every seed 0-9, with and without --no-preview (python train_all.py),")
    print("then python record_agents.py runs/terrain_dt1 to score and document them.")


if __name__ == "__main__":
    main()

"""train.py — Phase C, steps C1 and C4.

Trains a SAC agent on the engine environment and saves everything Phase D needs.

    pip install "stable-baselines3[extra]"      # once; also uncomment it in requirements.txt

    python train.py --steps 50000  --seed 0                # C1: the first bad run
    python train.py --steps 300000 --seed 0                # C4: a real run
    python train.py --steps 300000 --seed 0 --no-preview   # the blinded baseline

HOW LONG THIS TAKES — read before you start
--------------------------------------------
MEASURED 17 September 2026, by timing 2000 SAC steps with gradient updates
already running (200 warm-up steps first, past learning_starts):

      OMP_NUM_THREADS=1   19.19 steps/s   ->  50k steps = 0.72 h
      OMP_NUM_THREADS=6   18.14 steps/s   ->  50k steps = 0.77 h

      50,000 steps   ~45 minutes
     300,000 steps   ~4.5 hours

TWO THINGS THAT SURPRISED US, AND BOTH CORRECT THIS FILE'S OWN OLD ADVICE.

**Thread count does not matter.** One thread is marginally FASTER than six --
the policy network is tiny, so threading overhead exceeds the gain. Any
"on one CPU core" qualifier attached to these figures is meaningless.

**SAC's gradient updates are nearly free.** The environment alone runs at
19.5 steps/s and the full training loop at 19.2, so the updates cost about 2 %.
The docstring used to say they "bring the training loop down to 3.0 steps/s" --
a 6.4x error that made Phase D look like a week of overnights. Each env step
runs six engine cycles at ~9 ms; a gradient step on this network is ~1 ms. The
combustion model dominates completely and nothing else is close.

Caveat on the measurement: 2000 steps, no episode boundary crossed (an episode
is 4500 steps at dt = 0.2). Re-time it if you change `plant.DTHETA_DEG`, which
is what actually sets the cost -- halving it roughly doubles the run.

Phase D needs FIVE seeds of each of two configurations: ten runs, about
**7.5 hours total**. One evening on one machine, or under an hour if the five
of you run one seed each. Agree who takes which seed BEFORE anyone starts, or
you will end up with three copies of seed 0.

Checkpoints are written every 10,000 steps, so a closed laptop costs you minutes
rather than the whole run. Re-running the same seed resumes from its checkpoint.
"""
import argparse
import glob
import re
import os
import time

import numpy as np

from engine_env import SupervisoryTunerEnv, make_grade_climb

try:
    from stable_baselines3 import SAC
    from stable_baselines3.common.monitor import Monitor
    from stable_baselines3.common.callbacks import CheckpointCallback
except ImportError:
    raise SystemExit(
        "stable-baselines3 is not installed.\n\n"
        '    pip install "stable-baselines3[extra]"\n\n'
        "Then uncomment the two lines under 'Phase C onward' in requirements.txt\n"
        "so the rest of the team installs the same thing."
    )


def build_env(use_preview, seed, duration):
    env = SupervisoryTunerEnv(make_grade_climb(duration=duration),
                              use_preview=use_preview, seed=seed)
    return Monitor(env)


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
    ap.add_argument("--out", default="runs")
    a = ap.parse_args()

    tag = f"{'blind' if a.no_preview else 'sighted'}_seed{a.seed}"
    outdir = os.path.join(a.out, tag)
    os.makedirs(outdir, exist_ok=True)

    print(f"configuration : {'BLINDED (no preview)' if a.no_preview else 'sighted'}")
    print(f"seed          : {a.seed}")
    print(f"steps         : {a.steps:,}")
    # MEASURED 17 September 2026 -- see the docstring for the full table.
    # 2000 SAC steps with gradient updates running: 19.19 steps/s at one thread,
    # 18.14 at six. Threads do not matter and the gradient updates cost ~2 %;
    # the combustion model is the whole cost.
    #
    # This was 3.0 until 17 September, quoted as "measured on one CPU core" and
    # wrong by 6.4x. It made 50k steps look like 4.6 hours instead of 45 minutes
    # and turned Phase D into "five overnights, twice" in every document that
    # repeated it. THE ERROR WAS IN THE FIGURE, NOT IN THE HARDWARE -- do not
    # re-introduce a per-machine qualifier to explain it away.
    #
    # Re-measure if you change plant.DTHETA_DEG, which is what actually sets the
    # cost, or move to a GPU. An estimate wrong by a factor of six is how five
    # people plan two weeks around work that fits in an evening.
    STEPS_PER_S = 19.2
    mins_est = a.steps / STEPS_PER_S / 60
    print(f"estimate      : about {mins_est:.0f} minutes "
          f"({mins_est / 60:.1f} h) at a measured {STEPS_PER_S:.1f} steps/s on CPU")
    print(f"output        : {outdir}/\n")

    env = build_env(not a.no_preview, a.seed, a.duration)

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
        model = SAC.load(resume_from, env=env)
    else:
        model = SAC("MlpPolicy", env, seed=a.seed, learning_rate=a.lr,
                    verbose=1, tensorboard_log=None)

    cb = CheckpointCallback(save_freq=10_000, save_path=outdir,
                            name_prefix="ckpt", verbose=0)

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

    # the learning curve — Monitor recorded every episode return
    rewards = np.array(env.get_episode_rewards(), dtype=float)
    lengths = np.array(env.get_episode_lengths(), dtype=float)
    np.savetxt(os.path.join(outdir, "curve.csv"),
               np.column_stack([np.arange(len(rewards)), rewards, lengths]),
               delimiter=",", header="episode,return,length", comments="")

    print(f"\ntrained in {mins:.0f} min | {len(rewards)} episodes")
    if len(rewards) >= 10:
        first = float(np.mean(rewards[:5]))
        last = float(np.mean(rewards[-5:]))
        print(f"mean return: first 5 episodes {first:+.2f}  ->  last 5 {last:+.2f}")
        if last <= first:
            print("\n  The curve did not improve. Before changing anything else:")
            print("    1. re-run test_reward.py — a broken reward trains normally and means nothing")
            print("    2. if that passes, divide the learning rate by 3 (--lr 1e-4)")
            print("    3. if it still will not learn, cut the action space: fix lambda")
            print("       at nominal and let the agent control only spark and boost trim.")
        else:
            print("\n  The curve improved. 'Flat at the end and above zero' is the only")
            print("  stopping criterion you need — if it is still climbing, train longer.")

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

    print(f"\nnext: run the same command with --seed 1, 2, 3, 4 on other machines,")
    print(f"then the same five again with --no-preview. Phase D needs both sets.")


if __name__ == "__main__":
    main()

"""train.py — Phase C, steps C1 and C4.

Trains a SAC agent on the engine environment and saves everything Phase D needs.

    pip install "stable-baselines3[extra]"      # once; also uncomment it in requirements.txt

    python train.py --steps 50000  --seed 0                # C1: the first bad run
    python train.py --steps 300000 --seed 0                # C4: a real run
    python train.py --steps 300000 --seed 0 --no-preview   # the blinded baseline

HOW LONG THIS TAKES — read before you start
--------------------------------------------
The environment runs at about 21 steps per second on a laptop, because every
step evaluates the combustion model several times. Add SAC's own gradient
updates and the real figure is roughly half that.

      50,000 steps   ~1.5 hours
     300,000 steps   ~8 hours

Phase D needs FIVE seeds of each of two configurations. Run sequentially that is
over three days of wall-clock time. Do not do that.

    There are five of you. Each person runs one seed, on their own laptop,
    overnight. Two nights covers both configurations. Agree who takes which
    seed BEFORE anyone starts, or you will end up with three copies of seed 0.

Checkpoints are written every 10,000 steps, so a closed laptop costs you minutes
rather than the whole run. Re-running the same seed resumes from its checkpoint.
"""
import argparse
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
    # MEASURED, not guessed. The old formula assumed 10.75 effective steps/s and
    # under-estimated by 3.6x. Timed on 8 September on one CPU core, after the
    # engine-geometry correction: the environment alone runs at 19.5 steps/s,
    # and SAC's gradient updates bring the training loop down to 3.0 steps/s.
    # 3200 steps took 18 minutes; 50000 steps takes about 4.6 hours.
    #
    # Re-measure if you change the plant or move to a GPU. An estimate that is
    # wrong by a factor of four is how five people plan an evening around a run
    # that is still going at breakfast.
    STEPS_PER_S = 3.0
    mins_est = a.steps / STEPS_PER_S / 60
    print(f"estimate      : about {mins_est:.0f} minutes "
          f"({mins_est / 60:.1f} h) at a measured {STEPS_PER_S:.1f} steps/s on CPU")
    print(f"output        : {outdir}/\n")

    env = build_env(not a.no_preview, a.seed, a.duration)

    ckpt_path = os.path.join(outdir, "checkpoint.zip")
    if os.path.exists(ckpt_path):
        print(f"resuming from {ckpt_path}")
        model = SAC.load(ckpt_path, env=env)
    else:
        model = SAC("MlpPolicy", env, seed=a.seed, learning_rate=a.lr,
                    verbose=1, tensorboard_log=None)

    cb = CheckpointCallback(save_freq=10_000, save_path=outdir,
                            name_prefix="ckpt", verbose=0)

    t0 = time.time()
    model.learn(total_timesteps=a.steps, callback=cb, progress_bar=False)
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

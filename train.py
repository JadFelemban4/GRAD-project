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

WHAT `runs/<tag>/meta.json` IS, AND WHY IT IS NOT OPTIONAL   (AUDIT2.md C2-1)
----------------------------------------------------------------------------
Every run now writes a fingerprint of the plant it is training against before
the first step: the SHA of plant.py + thermal.py + engine_env.py, the eight gear
ratios, the final drive, the crank-angle step, the protection trigger, the
scenario tuple and a hash of the twenty frozen evaluation episodes. See
`fingerprint.py` for what each field means and which ones are fatal.

RETIRED-OK: 11.7 -- naming the void figure IS the reason this mechanism exists
This is not bookkeeping. On 18 September two agents were trained here, scored at
+11.7 points, and written up as the project's result. Seven hours later the
gearbox under them was replaced and nothing in `runs/` recorded which gearbox
had produced them. The same pair scores +7.5 on the corrected plant, and the
+11.7 cannot be regenerated from this tree at all. `evaluate.py` now refuses a
model whose fingerprint disagrees with the live one, and the only way it can do
that is if this file wrote one down.

TWO RESUME DEFECTS FIXED AT THE SAME TIME   (AUDIT2.md H2-3)
-------------------------------------------
`curve.csv` is the only record of how a run learned, and the resume path used to
**overwrite** it with whatever the current process had in its Monitor -- so a
re-run of a finished agent blanked a twelve-episode curve down to its header,
and a mid-run resume kept only the post-resume episodes. It appends now.

And a re-run with nothing left to do used to call `learn(0)` and then re-save
`final.zip`, rewriting the only copy of a trained agent for no reason. It now
stops before either.
"""
import argparse
import glob
import re
import os
import time

import numpy as np

import fingerprint as FP
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


def buffer_size(a):
    """How many transitions the replay buffer holds.

    `--buffer` if given, otherwise the run's own length, floored at 10 000 so a
    very short smoke run still has somewhere to sample from, and capped at
    SB3's default so this can only ever ask for LESS memory than before.
    """
    if a.buffer is not None:
        return int(a.buffer)
    return int(min(1_000_000, max(10_000, a.steps)))


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
    ap.add_argument("--buffer", type=int, default=None,
                    help="SAC replay buffer size. Default: sized to the run, "
                         "because a buffer bigger than --steps can never fill "
                         "and costs memory for nothing. See the docstring.")
    ap.add_argument("--force-plant-mismatch", action="store_true",
                    help="resume into a run whose meta.json describes a "
                         "DIFFERENT plant. Almost never what you want: the "
                         "resulting agent has seen two physical systems and "
                         "belongs to neither. See AUDIT2.md C2-1.")
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

    # ---- the fingerprint, written BEFORE the first step -------------------
    # AUDIT2.md C2-1. Built from the live objects by fingerprint.py; see that
    # file for which fields are fatal and why the plant SHA outranks the git
    # commit.
    meta_path = os.path.join(outdir, "meta.json")
    live = FP.plant_fingerprint(train_dt=float(env.unwrapped.dt),
                                train_duration=a.duration,
                                steps_requested=a.steps, seed=a.seed,
                                use_preview=not a.no_preview, tag=tag)
    stored = FP.read(meta_path)

    if resume_from:
        m = re.search(r"ckpt_(\d+)_steps", resume_from)
        done_steps = int(m.group(1)) if m else 0
        # A checkpoint with no meta.json predates this mechanism. Refuse rather
        # than guess: `runs_sixspeed_18sep/` holds exactly such a pair and
        # resuming into one is how an agent comes to have been trained on two
        # different gearboxes with nothing recording either.
        if stored is None:
            raise SystemExit(
                f"\n{resume_from} exists but {meta_path} does not.\n"
                "This run predates the plant fingerprint (AUDIT2.md C2-1), so\n"
                "there is no way to tell which plant it was trained on. Train\n"
                "into a fresh --out directory, or delete the old one on purpose."
            )
        bad = FP.compare(stored, live)
        if bad:
            print(FP.format_block(stored, "STORED (meta.json)"))
            print(FP.format_block(live, "LIVE (this tree)"))
            print("\nfields that disagree:")
            for k, was, now in bad:
                print(f"  {k:<20} stored {was!r}  live {now!r}")
            if not a.force_plant_mismatch:
                raise SystemExit(
                    "\nREFUSING to resume: the checkpoint was trained on a "
                    "different plant.\n"
                    "Resuming would produce an agent that has seen two physical "
                    "systems and\nbelongs to neither -- which is exactly how "
                    "results/phase_d_seed0.txt happened.\n"
                    "Train into a fresh --out directory, or pass "
                    "--force-plant-mismatch if you\nreally mean it and will say "
                    "so beside every number the run produces."
                )
            print("\n  --force-plant-mismatch given; continuing anyway. The "
                  "resulting agent has\n  seen two plants. Say so beside every "
                  "number it produces.")
        # The advisory fields are not refused over, but a resume that silently
        # changes the EPISODE LENGTH or the step is training a different task:
        # `--duration 300` on the second call trains 50 000 further steps on
        # 300-second episodes while meta.json still records 900. Report every
        # advisory move, and refuse on the two that change what is learned.
        adv = FP.advisory_diff(stored, live)
        learned = [t for t in adv if t[0] in ("train_duration", "train_dt")]
        if adv:
            print("\nadvisory fields that moved since this run started:")
            for k, was, now in adv:
                print(f"  {k:<22} stored {was!r}  live {now!r}")
        if learned and not a.force_plant_mismatch:
            raise SystemExit(
                "\nREFUSING to resume: the episode length or the step has "
                "changed.\nThe agent would be trained on two different tasks "
                "and meta.json would record\nonly the first. Pass the original "
                "values, use a fresh --out directory, or\npass "
                "--force-plant-mismatch and say so beside the result.")
        print(f"resuming from {resume_from} at {done_steps} steps")
        model = SAC.load(resume_from, env=env)
    else:
        # A FRESH START THAT IS NOT A FRESH DIRECTORY IS THE DANGEROUS CASE,
        # and it was missed on the first pass. `resume_from` keys on the
        # CHECKPOINT files only, so a directory holding `final.zip` and no
        # checkpoints -- which is what you get when you copy a teammate's
        # trained agent without its 16 MB of checkpoints, or delete them to
        # reclaim disk -- takes this branch. It then rewrote meta.json with the
        # CURRENT plant while the OLD `final.zip` sat beside it untouched, and
        # `evaluate.py` afterwards found a matching fingerprint and scored a
        # six-speed agent as a ZF one.
        #
        # That is `results/phase_d_seed0.txt` again WITH A CERTIFICATE
        # ATTACHED, which is worse than no certificate. Reproduced on this tree
        # before the guard below existed.
        if os.path.exists(os.path.join(outdir, "final.zip")):
            raise SystemExit(
                f"\n{outdir}/final.zip exists but no checkpoint does, so this "
                "would be a\nFRESH run in a directory that already holds a "
                "trained agent. Whatever is\nwritten to meta.json here would "
                "describe THIS tree while final.zip came from\nsomewhere else "
                "-- a certificate on the wrong artefact, which is how\n"
                "results/phase_d_seed0.txt happened (AUDIT2.md C2-1).\n\n"
                "Train into a fresh --out directory. If you meant to retrain "
                "over this one,\ndelete it yourself so the decision is "
                "yours and is in your shell history.")
        if stored is not None and FP.compare(stored, live):
            print(FP.format_block(stored, "STORED (meta.json)"))
            print(FP.format_block(live, "LIVE (this tree)"))
            if not a.force_plant_mismatch:
                raise SystemExit(
                    f"\n{meta_path} describes a different plant and there is no "
                    "checkpoint to\nresume. Overwriting it would erase the only "
                    "record of what this directory\nheld. Use a fresh --out "
                    "directory, or pass --force-plant-mismatch.")
        FP.write(meta_path, live)
        print(FP.format_block(live, "PLANT FINGERPRINT (written to meta.json)"))
        print()
        # SIZE THE REPLAY BUFFER TO THE RUN. SB3's default is 1 000 000
        # transitions, which for a 50 000-step run is a buffer that can never
        # be more than 5 % full -- and it is allocated in full at construction:
        # (1000000, 1, 23) float32 is 87.7 MB for the observations alone, about
        # 200 MB per run once actions, rewards and next-observations are added.
        #
        # Sixteen of those in parallel is 3.2 GB of buffers nothing will ever
        # write to, and on 21 September it is what made 13 of 16 Phase D runs
        # die with numpy MemoryError while 3 survived.
        #
        # THIS CANNOT CHANGE WHAT IS LEARNED, and that is not an assumption --
        # `run_phase_d.py --prove-buffer` trains the same seed both ways and
        # compares every network weight. A buffer only affects behaviour when
        # it EVICTS, and neither size evicts when the run is shorter than the
        # smaller of the two.
        model = SAC("MlpPolicy", env, seed=a.seed, learning_rate=a.lr,
                    buffer_size=buffer_size(a), verbose=1, tensorboard_log=None)

    cb = CheckpointCallback(save_freq=10_000, save_path=outdir,
                            name_prefix="ckpt", verbose=0)

    t0 = time.time()
    remaining = max(0, a.steps - done_steps)

    # AUDIT2.md H2-3. This used to fall through to `learn(0)` and then re-save
    # `final.zip` and blank `curve.csv`, so re-running a FINISHED run destroyed
    # the only record of it while printing "nothing to do". `runs/` holds the
    # only copies of the trained agents; a no-op must be a genuine no-op.
    if remaining == 0:
        print(f"already at {done_steps} of {a.steps} steps; nothing to do.")
        print(f"  {outdir}/final.zip and curve.csv left untouched.")
        print("  To train further, pass a larger --steps. To retrain from "
              "scratch, use a\n  fresh --out directory rather than deleting "
              "this one in place.")
        return

    # reset_num_timesteps=False so the resumed run CONTINUES the schedule
    # rather than starting a second one (AUDIT.md H6).
    model.learn(total_timesteps=remaining, callback=cb, progress_bar=False,
                reset_num_timesteps=(resume_from is None))
    mins = (time.time() - t0) / 60

    model.save(os.path.join(outdir, "final"))
    model.save(ckpt_path)

    # the learning curve — Monitor recorded every episode return
    #
    # AUDIT2.md H2-3: APPEND. `Monitor` only knows the episodes THIS process
    # ran, so writing it out wholesale threw away everything before a resume --
    # measured on a scratch copy, a finished twelve-episode run came back as a
    # header-only file. The curve is the only evidence of how a run learned.
    curve_path = os.path.join(outdir, "curve.csv")
    rewards = np.array(env.get_episode_rewards(), dtype=float)
    lengths = np.array(env.get_episode_lengths(), dtype=float)
    prior = np.empty((0, 3))
    if os.path.exists(curve_path):
        try:
            prior = np.atleast_2d(
                np.loadtxt(curve_path, delimiter=",", skiprows=1, ndmin=2))
        except (OSError, ValueError):
            prior = np.empty((0, 3))
        if prior.size and prior.shape[1] != 3:
            prior = np.empty((0, 3))
    fresh = np.column_stack([np.arange(len(rewards)) + len(prior), rewards, lengths])
    np.savetxt(curve_path, np.vstack([prior, fresh]) if prior.size else fresh,
               delimiter=",", header="episode,return,length", comments="")
    if prior.size:
        print(f"  curve.csv: {len(prior)} earlier episodes kept, "
              f"{len(rewards)} appended")

    # Summarise the WHOLE curve, not this process's slice of it: after a resume
    # "first 5 -> last 5" over the post-resume episodes alone is a comparison
    # between two halves of the same tail.
    curve = np.concatenate([prior[:, 1], rewards]) if prior.size else rewards
    print(f"\ntrained in {mins:.0f} min | {len(curve)} episodes")
    if len(curve) >= 10:
        first = float(np.mean(curve[:5]))
        last = float(np.mean(curve[-5:]))
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
        if len(curve) >= 5:
            k = max(1, len(curve) // 40)
            smooth = np.convolve(curve, np.ones(k) / k, mode="valid")
            plt.figure(figsize=(7, 4))
            plt.plot(curve, lw=0.8, alpha=0.35, color="#9AA7AE", label="episode return")
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

"""check_d2_tracking.py — do the Phase D2 agents deliver the torque they are asked for?

    python check_d2_tracking.py          all sixteen agents, about 40 minutes
    python check_d2_tracking.py runs_c4  the same check on C4's agents

THE DIRECTORY IS AN ARGUMENT, and until 23 September 2026 it was not: RUNS was
hard-coded to runs_d2/, so running this "for C4" would have re-inspected the
D2 agents and printed their clean limit-10 result -- a false clearance with a
C4 label on it. Each agent's row now also carries the steps its final.zip was
actually trained for, read from the zip (`fingerprint.model_budget`), so the
output says which agents it looked at; and `--out` writes the report where
`analyse_c4.py` can read it.

`results/PREREGISTRATION_D2.md` limit 10, declared before any D2 agent trained:

    "The reward barely punishes torque refusal on the steepest roads. At 16 %
     the torque-starver ... clears the gate by 0.006. ... Inspect the agents'
     torque-violation and fuel columns before quoting any D2 damage figure."

This is that inspection. `evaluate.py` prints damage and fuel but not torque
delivery, and fuel alone cannot tell protection from refusal: an agent that
pins boost low burns LESS fuel and makes LESS heat -- which reads as a good
protector -- while the car is not doing what the driver asked. Five D2 agents
median BELOW the baseline ECU's fuel on the frozen episodes, which is the
shape to check.

WHAT IS MEASURED. For every policy, on the twenty frozen D2 episodes
(`evaluate.EPISODES_D2`, exactly as `evaluate.py --protocol d2` runs them):

    tracking  the environment's own `torque_viol` counter divided by the steps:
              the mean, per step, of the torque error ABOVE 3 % of the
              reference torque (`engine_env.step`, `c_torque`). 0 means the
              demand was met to within 3 % on every step.
    fuel      grams over the episode
    damage    the damage integral, as evaluate.py reports it

Each is summarised as the median over the twenty episodes, and every agent is
set beside the baseline ECU run on the same episodes. The baseline is the
reference because it is what the car does unsupervised: an agent is refusing
torque when it tracks materially WORSE than the controller it supervises.

WHAT IT DOES NOT DO. It does not change or re-run the preregistered test,
which is on damage and is `analyse_phase_d2.py`'s alone. It qualifies how
the damage figures may be READ. It chooses nothing: every agent is printed.
"""
import argparse
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

import fingerprint as FP

HERE = os.path.dirname(os.path.abspath(__file__))


def one_policy(job):
    """(label, model_dir or None, kind) -> per-episode arrays."""
    label, mdir, kind = job
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    import check_premise as C
    import evaluate as E

    if mdir is None:
        pol = C.p_neutral if kind == "baseline" else C.p_grade_now
        preview = True
    else:
        from stable_baselines3 import SAC
        model = SAC.load(os.path.join(mdir, "final"))   # same device as evaluate.py
        pol = E.agent_policy(model)
        preview = "blind" not in os.path.basename(mdir)
    track, fuel, dmg = [], [], []
    for s, w, st, g in E.EPISODES_D2:
        r = _episode_with_steps(E, pol, s, w, preview, (st, g))
        track.append(r["track"])
        fuel.append(r["fuel"])
        dmg.append(r["damage"])
    return label, np.array(track), np.array(fuel), np.array(dmg)


def _episode_with_steps(E, policy, seed, weights, use_preview, road):
    """evaluate.run_episode's loop, keeping the step count for a per-step mean."""
    import random_road as RR
    from engine_env import SupervisoryTunerEnv
    env = SupervisoryTunerEnv(RR.climb(road[0], road[1], duration=E.DURATION, dt=E.DT),
                              dt=E.DT, seed=seed, use_preview=use_preview)
    obs, _ = env.reset(seed=seed)
    env.w = np.asarray(weights, dtype=np.float32)
    obs = env._obs()
    while True:
        obs, r, term, trunc, info = env.step(policy(env, obs))
        if term or trunc:
            break
    s = info["episode_summary"]
    return dict(track=100.0 * s["torque_viol"] / max(1, s["steps"]),
                fuel=s["fuel"], damage=s["damage"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="?", default="runs_d2",
                    help="the directory of trained agents (default runs_d2)")
    ap.add_argument("--out", default=None,
                    help="also write the report to this file -- for C4, "
                         "results/c4_tracking.txt, which analyse_c4.py reads "
                         "(PREREGISTRATION_C4.md limit 10). Never overwritten.")
    a = ap.parse_args()
    if a.out and os.path.exists(os.path.join(HERE, a.out)):
        raise SystemExit(f"{a.out} exists -- it is never overwritten")
    runs = os.path.join(HERE, a.runs)
    name = os.path.basename(os.path.normpath(a.runs))
    t0 = time.time()
    jobs = [("baseline ECU", None, "baseline"), ("current-grade", None, "grade")]
    steps = {}
    for s in range(8):
        for arm in ("sighted", "blind"):
            d = os.path.join(runs, f"{arm}_seed{s}")
            if not os.path.exists(os.path.join(d, "final.zip")):
                raise SystemExit(f"missing {d}/final.zip")
            jobs.append((f"{arm}_seed{s}", d, "agent"))
            b = FP.model_budget(os.path.join(d, "final.zip"))
            steps[f"{arm}_seed{s}"] = b
    n_agents = len(jobs) - 2
    n = max(1, min(10, (os.cpu_count() or 4) - 2))
    lines = []

    def say(line=""):
        print(line)
        lines.append(line)

    say("=" * 78)
    title = "PHASE D2" if name == "runs_d2" else f"{name}/ (on the D2 episodes)"
    say(f"{title} -- torque delivery and fuel, per agent (PREREGISTRATION_D2 limit 10)")
    say(f"the twenty frozen D2 episodes, dt 1.0, 720 s; {len(jobs)} policies, {n} in parallel")
    say(f"agents from {a.runs}/; each row's 'steps' is read from its own final.zip")
    say("=" * 78)
    with Pool(n) as pool:
        out = pool.map(one_policy, jobs)
    res = {lab: (t, f, d) for lab, t, f, d in out}
    bt, bf, bd = res["baseline ECU"]
    b_track, b_fuel = float(np.median(bt)), float(np.median(bf))

    say(f"\n{'policy':<16}{'tracking %':>11}{'vs base':>9}{'worst ep':>10}"
        f"{'fuel g':>8}{'vs base':>9}{'damage':>9}{'steps':>10}")
    say("-" * 82)
    flagged, med = [], {}
    for lab, _, _ in jobs:
        t, f, d = res[lab]
        tm, fm, dm = float(np.median(t)), float(np.median(f)), float(np.median(d))
        med[lab] = tm
        dt_ = tm - b_track
        df_ = 100.0 * (fm / b_fuel - 1.0)
        # "Materially worse" is fixed here, before looking: a median per-step
        # excess error one percentage point above the baseline's. The reward's
        # own tolerance is 5 % (TRACK_TOL) and the counter starts at 3 %.
        flag = lab not in ("baseline ECU", "current-grade") and dt_ > 1.0
        if flag:
            flagged.append(lab)
        b = steps.get(lab)
        st = "--" if lab not in steps else ("unread" if b is None else f"{b['num_timesteps']:,}")
        say(f"{lab:<16}{tm:>11.2f}{dt_:>+9.2f}{float(np.max(t)):>10.2f}"
            f"{fm:>8.0f}{df_:>+8.1f}%{dm:>9.1f}{st:>10}"
            + ("   <- tracks worse" if flag else ""))
    say("-" * 82)
    say("tracking % = median over episodes of the per-step torque error above")
    say("3 % of the reference torque (engine_env's torque_viol / steps).")
    below = [lab for lab, _, _ in jobs[2:] if float(np.median(res[lab][1])) < b_fuel]
    say(f"\nagents whose median fuel is BELOW the baseline ECU's: {len(below)} of {n_agents}"
        + (f"  ({', '.join(below)})" if below else ""))
    say(f"agents tracking torque >1 point worse than the baseline: {len(flagged)} of {n_agents}"
        + (f"  ({', '.join(flagged)})" if flagged else ""))
    # PER SEED, sighted minus blind. The ablation is a difference between the
    # arms, and only the sighted arm can see a climb coming and cut boost
    # early, so the arms can use the torque-refusal lever DIFFERENTLY -- which
    # a per-agent flag against the baseline cannot show. Added for C4
    # (PREREGISTRATION_C4.md limit 10); analyse_c4.py reads the GAP lines.
    say("\nper seed, tracking % sighted minus blind (positive = sighted tracks worse):")
    for s in range(8):
        gap = med[f"sighted_seed{s}"] - med[f"blind_seed{s}"]
        say(f"GAP seed{s} {gap:+.2f}")
    for lab in flagged:
        say(f"FLAGGED {lab}")
    if flagged:
        say("\nREAD THEIR DAMAGE FIGURES AS PARTLY BOUGHT WITH TORQUE, not only with")
        say("protection -- the lever limit 10 named. The paired ablation is unaffected")
        say("in construction (both arms face one reward), but these agents' damage")
        say("is not the damage of a car doing what the driver asked.")
    else:
        say("\nNo agent tracks torque materially worse than the baseline ECU. Fuel")
        say("below the baseline is then not torque refusal, and the damage figures")
        say("can be read as protection.")
    say(f"\n({(time.time() - t0) / 60:.1f} min)")
    if a.out:
        with open(os.path.join(HERE, a.out), "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print(f"written to {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

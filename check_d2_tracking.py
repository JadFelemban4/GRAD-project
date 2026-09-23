"""check_d2_tracking.py — do the Phase D2 agents deliver the torque they are asked for?

    python check_d2_tracking.py          all sixteen agents, about 40 minutes

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
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs_d2")


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
    t0 = time.time()
    jobs = [("baseline ECU", None, "baseline"), ("current-grade", None, "grade")]
    for s in range(8):
        for arm in ("sighted", "blind"):
            d = os.path.join(RUNS, f"{arm}_seed{s}")
            if not os.path.exists(os.path.join(d, "final.zip")):
                raise SystemExit(f"missing {d}/final.zip")
            jobs.append((f"{arm}_seed{s}", d, "agent"))
    n = max(1, min(10, (os.cpu_count() or 4) - 2))
    print("=" * 78)
    print("PHASE D2 -- torque delivery and fuel, per agent (PREREGISTRATION_D2 limit 10)")
    print(f"the twenty frozen D2 episodes, dt 1.0, 720 s; {len(jobs)} policies, {n} in parallel")
    print("=" * 78)
    with Pool(n) as pool:
        out = pool.map(one_policy, jobs)
    res = {lab: (t, f, d) for lab, t, f, d in out}
    bt, bf, bd = res["baseline ECU"]
    b_track, b_fuel = float(np.median(bt)), float(np.median(bf))

    print(f"\n{'policy':<16}{'tracking %':>11}{'vs base':>9}{'worst ep':>10}"
          f"{'fuel g':>8}{'vs base':>9}{'damage':>9}")
    print("-" * 72)
    flagged = []
    for lab, _, _ in jobs:
        t, f, d = res[lab]
        tm, fm, dm = float(np.median(t)), float(np.median(f)), float(np.median(d))
        dt_ = tm - b_track
        df_ = 100.0 * (fm / b_fuel - 1.0)
        # "Materially worse" is fixed here, before looking: a median per-step
        # excess error one percentage point above the baseline's. The reward's
        # own tolerance is 5 % (TRACK_TOL) and the counter starts at 3 %.
        flag = lab not in ("baseline ECU", "current-grade") and dt_ > 1.0
        if flag:
            flagged.append(lab)
        print(f"{lab:<16}{tm:>11.2f}{dt_:>+9.2f}{float(np.max(t)):>10.2f}"
              f"{fm:>8.0f}{df_:>+8.1f}%{dm:>9.1f}" + ("   <- tracks worse" if flag else ""))
    print("-" * 72)
    print("tracking % = median over episodes of the per-step torque error above")
    print("3 % of the reference torque (engine_env's torque_viol / steps).")
    below = [lab for lab, _, _ in jobs[2:] if float(np.median(res[lab][1])) < b_fuel]
    print(f"\nagents whose median fuel is BELOW the baseline ECU's: {len(below)} of 16"
          + (f"  ({', '.join(below)})" if below else ""))
    print(f"agents tracking torque >1 point worse than the baseline: {len(flagged)} of 16"
          + (f"  ({', '.join(flagged)})" if flagged else ""))
    if flagged:
        print("\nREAD THEIR DAMAGE FIGURES AS PARTLY BOUGHT WITH TORQUE, not only with")
        print("protection -- the lever limit 10 named. The paired ablation is unaffected")
        print("in construction (both arms face one reward), but these agents' damage")
        print("is not the damage of a car doing what the driver asked.")
    else:
        print("\nNo agent tracks torque materially worse than the baseline ECU. Fuel")
        print("below the baseline is then not torque refusal, and the damage figures")
        print("can be read as protection.")
    print(f"\n({(time.time() - t0) / 60:.1f} min)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

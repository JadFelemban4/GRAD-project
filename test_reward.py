"""test_reward.py — Phase C, step C2.

The sanity checks that must pass before you trust a single training curve.
A broken reward does not announce itself: it produces training curves that look
completely normal while measuring nothing. Run this after ANY change to the
reward, and commit the output with the change.

    python test_reward.py                # 300 s, about two minutes
    python test_reward.py --duration 900 # the full scenario, slower
    python test_reward.py --road random  # PHASE D2: the same four checks on
                                         # the corners of the randomised climb

PHASE D2 -- `--road random`
---------------------------
A changed scenario is a changed reward surface (CLAUDE.md mistakes 5 and 17):
the reward is only safe relative to the dynamics it scores, and mistake 17 was
a scenario change that made the NEUTRAL action fail this gate, because the
baseline could no longer hold the torque the road asked for. Phase D2 draws its
climb from 12-16 % and 120-300 s, so the gate is run on the roads most likely
to break it:

    both ends of the grade range, at both ends of the start range  (4 roads)
    the gearbox notch at 13.73 %, where the box hands back a gear   (1 road)

16 % asks the most torque of anything D2 draws; the notch is where a shift
happens mid-climb, which is exactly the shape of mistake 17. Each road runs
long enough to hold 180 s of climb after the latest start. The preview check
samples 10 s after the drawn climb begins -- not at a fixed 190 s, which on a
road whose climb starts at 300 s would compare two flat roads and fail for a
reason that has nothing to do with the reward.

The default invocation (no --road) is unchanged.

TWO THINGS THIS FILE EXISTS TO STOP YOU GETTING WRONG
-----------------------------------------------------
1. "Neutral" is not a vector of zeros, and it is not the midpoint of the action
   range. Three actions are trims whose neutral is zero; two are the cooling fan
   and the coolant pump, whose neutral is what the baseline ECU commands. Using
   the midpoint leaves the fan off and the pump at 30 %, which is quietly worse
   than the baseline and drags the check off zero for a reason that has nothing
   to do with the reward. See neutral_action() in engine_env.py.

2. The episode must be long enough to contain the climb. make_grade_climb()
   puts the grade at t = 180 s, so a 60 s episode never reaches it, nothing ever
   gets hot, and every policy scores about the same. Short-episode checks tell
   you nothing.
"""
import argparse

import numpy as np

from engine_env import (SupervisoryTunerEnv, make_grade_climb,
                        neutral_action)


def true_neutral():
    """Zero trims, cooling left where the baseline ECU puts it.

    This used to patch actions 3 and 4 locally because `neutral_action()` got
    them wrong. That fix now lives in engine_env.neutral_action() itself, so
    this is a pass-through kept for the name. Same vector, same numbers.
    """
    return neutral_action()


def torque_starver():
    """Neutral, except boost trim pinned to its minimum.

    This policy cannot deliver the requested torque. It should therefore score
    clearly NEGATIVE. If it does not, the tracking term has no teeth, and an
    agent will discover that refusing torque is a cheap way to avoid damage --
    the exact reward hack the handbook warns about in step C3.
    """
    a = true_neutral().copy()
    a[2] = -1.0                       # boost trim at ACT_LO
    return a.astype(np.float32)


def roll(action_fn, duration, seed=1, cycle=None):
    env = SupervisoryTunerEnv(cycle if cycle is not None
                              else make_grade_climb(duration=duration), seed=0)
    obs, _ = env.reset(seed=seed)
    rs = []
    for _ in range(int(duration / 0.2) + 5):
        obs, r, term, trunc, _ = env.step(action_fn(env, obs))
        rs.append(r)
        if term or trunc:
            break
    return float(np.mean(rs)), len(rs)


def obs_differs_without_preview(duration, cycle_fn=None, start_s=180.0):
    """The blinded baseline in Phase D must actually see something different.

    Sample AFTER the climb has entered the preview window. The longest preview
    horizon is 30 s and the grade starts at 180 s, so before t = 150 s both the
    sighted and blinded observations correctly read "flat road ahead" and are
    identical. Testing before then proves nothing.

    `cycle_fn` builds the road (a fresh one per arm) and `start_s` says where
    its climb begins, for Phase D2's drawn roads; the sample is then taken
    10 s after that start instead of at the fixed 190 s.
    """
    a = true_neutral()
    n_steps = int(min(duration - 5.0, start_s + 10.0) / 0.2)
    seen = []
    for use_preview in (True, False):
        cyc = cycle_fn() if cycle_fn is not None else make_grade_climb(duration=duration)
        env = SupervisoryTunerEnv(cyc, use_preview=use_preview, seed=0)
        obs, _ = env.reset(seed=1)
        for _ in range(n_steps):
            obs, *_ = env.step(a)
        seen.append(np.asarray(obs, dtype=float).copy())
    return float(np.max(np.abs(seen[0] - seen[1]))), seen


# ---------------------------------------------------------------------------
# PHASE D2 -- the gate on the randomised climb
# ---------------------------------------------------------------------------
# (start_s, grade). The four corners of the D2 range, plus the gearbox notch:
# the grade `check_random_road.py` finds with the thinnest margin over the
# trigger, where the box hands back a gear mid-climb. See the module docstring.
#
# 13.73 %, NOT 14.0 %. The design record measured grade in 0.5 % steps and
# named 14.0 % (+12.7 K) the weakest. check_random_road.py's 0.01 % sweep over
# the notch, 22 September 2026, found the real minimum at 13.73 % (+6.9 K) --
# between two grid points, which is exactly why a continuous draw had to be
# swept finely before it was trained on.
D2_ROADS = (
    (120.0, 0.12),
    (300.0, 0.12),
    (120.0, 0.16),
    (300.0, 0.16),
    (300.0, 0.1373),
)
D2_DURATION = 480.0      # 180 s of climb after the latest start


def _d2_job(job):
    """One rollout for the D2 gate. Module-level so multiprocessing can pickle it."""
    import random_road as RR
    kind, start_s, grade, dur = job

    def cyc():
        return RR.climb(start_s, grade, duration=dur, dt=0.2)

    if kind == "preview":
        d, _ = obs_differs_without_preview(dur, cycle_fn=cyc, start_s=start_s)
        return d
    if kind == "neutral":
        n = true_neutral()
        fn = lambda e, o: n                                    # noqa: E731
    elif kind == "starve":
        fn = lambda e, o: torque_starver()                     # noqa: E731
    else:
        rng = np.random.default_rng(0)
        fn = lambda e, o: rng.uniform(-1.0, 1.0, e.action_space.shape).astype(np.float32)  # noqa: E731
    r, _ = roll(fn, dur, cycle=cyc())
    return r


def main_random_road(jobs):
    from multiprocessing import Pool

    kinds = ("neutral", "starve", "random", "preview")
    work = [(k, s, g, D2_DURATION) for s, g in D2_ROADS for k in kinds]
    print(f"PHASE D2 reward gate -- {len(D2_ROADS)} roads x {len(kinds)} rollouts, "
          f"{D2_DURATION:.0f} s each at dt 0.2, {jobs} in parallel")
    print(f"neutral action : {np.round(true_neutral(), 3)}\n")
    with Pool(jobs) as pool:
        got = pool.map(_d2_job, work)
    res = {(k, s, g): v for (k, s, g, _), v in zip(work, got)}

    print(f"{'road':<18}{'neutral':>11}{'starver':>11}{'random':>11}"
          f"{'|d obs|':>10}   verdict")
    print("-" * 84)
    all_ok = True
    for s, g in D2_ROADS:
        rn, rs, rr, dp = (res[("neutral", s, g)], res[("starve", s, g)],
                          res[("random", s, g)], res[("preview", s, g)])
        fails = []
        if not abs(rn) < 0.05:
            fails.append("neutral not ~0")
        if not rs < rn - 0.02:
            fails.append("REWARD HACK: starver not punished")
        if not dp > 1e-6:
            fails.append("preview changes nothing")
        if not all(np.isfinite(x) for x in (rn, rs, rr)):
            fails.append("non-finite")
        all_ok &= not fails
        print(f"{s:5.0f} s / {100 * g:5.2f} %  {rn:+11.5f}{rs:+11.5f}{rr:+11.5f}"
              f"{dp:10.4g}   {'PASS' if not fails else 'FAIL: ' + ', '.join(fails)}")
    print("-" * 84)
    print("checks per road: neutral |r| < 0.05; starver < neutral - 0.02; "
          "preview changes the\nobservation; all finite. The random column is "
          "for information, as in the default run.")
    if all_ok:
        print("\nAll checks pass on every D2 road. The reward is safe to train "
              "against on the randomised climb.")
        return 0
    print("\nSTOP. Do not train Phase D2 until this passes. Diagnose WHICH check "
          "failed on WHICH road\nbefore taking the advice below -- mistake 17 "
          "was a scenario failure that looked like a\nweight problem.")
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, default=300.0)
    ap.add_argument("--road", choices=("fixed", "random"), default="fixed",
                    help="'random' runs the four checks on the Phase D2 roads "
                         "listed in D2_ROADS instead of the fixed climb")
    ap.add_argument("--jobs", type=int, default=10,
                    help="parallel rollouts for --road random")
    a = ap.parse_args()
    if a.road == "random":
        raise SystemExit(main_random_road(a.jobs))
    dur = a.duration

    neutral = true_neutral()
    print(f"episode length : {dur:.0f} s   (grade starts at 180 s)")
    print(f"neutral action : {np.round(neutral, 3)}\n")

    r_neutral, n1 = roll(lambda e, o: neutral, dur)
    r_starve, n2 = roll(lambda e, o: torque_starver(), dur)
    # AUDIT.md M13: `action_space.sample()` was unseeded, so this "for
    # information" figure moved between runs (-0.08782, -0.08293, -0.09590 on
    # three consecutive runs here). Seeded, so it is at least reproducible.
    _rng = np.random.default_rng(0)
    r_random, n3 = roll(
        lambda e, o: _rng.uniform(-1.0, 1.0, e.action_space.shape).astype(np.float32),
        dur)
    d_prev, _ = obs_differs_without_preview(dur)

    checks = [
        ("neutral action scores about zero",
         abs(r_neutral) < 0.05,
         f"mean reward {r_neutral:+.5f}   (want |r| < 0.05)"),
        ("refusing torque is punished",
         r_starve < r_neutral - 0.02,
         f"starver {r_starve:+.5f}  vs  neutral {r_neutral:+.5f}"
         + ("   <-- REWARD HACK PRESENT" if r_starve >= r_neutral else "")),
        ("disabling preview changes the observation",
         d_prev > 1e-6,
         f"max |delta obs| = {d_prev:.4g}"),
        ("rewards are finite",
         all(np.isfinite(x) for x in (r_neutral, r_starve, r_random)),
         f"{n1}, {n2}, {n3} steps"),
    ]

    print(f"{'check':46s} {'result':>7}   detail")
    print("-" * 96)
    for name, ok, detail in checks:
        print(f"{name:46s} {'PASS' if ok else 'FAIL':>7}   {detail}")
    print("-" * 96)

    print(f"\nFOR INFORMATION, NOT A PASS/FAIL: random policy scores "
          f"{r_random:+.5f}")
    if r_random > r_neutral:
        print("""  Random currently scores ABOVE neutral. That is not automatically a bug.
  The reward is baseline-relative and pays for protection, and random actions
  include spark retard and enrichment, which genuinely do protect. But it does
  mean protection is cheap to earn by accident, so watch the fuel and tracking
  terms in step C3 -- if the agent's gains come mostly from the damage term,
  the weights need rebalancing before Phase D scores anything.""")

    if all(c[1] for c in checks):
        print("\nAll checks pass. The reward is safe to train against.")
    else:
        print("""
STOP. Do not train until this passes. Fix the reward, not the agent.

If "refusing torque is punished" failed, the tracking penalty is too weak
relative to the damage reward: a policy that simply declines to make torque
scores better than one that does its job. An agent will find this within a few
thousand steps, and every number in Phase D would then be an artefact of it.

The fix is a weight change, not a redesign. Raise the tracking coefficient
(w[0]) until the starver scores clearly negative, re-run this file, and record
both the old and new weights in the log. Do it before Phase C, not after.""")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

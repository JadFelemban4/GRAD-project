"""test_reward.py — Phase C, step C2.

The sanity checks that must pass before you trust a single training curve.
A broken reward does not announce itself: it produces training curves that look
completely normal while measuring nothing. Run this after ANY change to the
reward, and commit the output with the change.

    python test_reward.py                # 300 s, about two minutes
    python test_reward.py --duration 900 # the full scenario, slower

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

THE TRAINING ROADS ARE CHECKED TOO (27 September 2026). A reward is only safe
relative to the dynamics it scores (mistake 5), and train.py now trains across
varied roads (engine_env.TerrainTrainingEnv) at dt = 1.0. The first sample of
those roads found grades of about 9 % at 130 km/h where the baseline itself
could not deliver the torque request and the neutral policy scored -0.26 per
step. The gearbox fix is guarded here by a road sitting in that band, and every
road family is checked for neutral-about-zero and a punished starver.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from engine_env import (SupervisoryTunerEnv, TerrainTrainingEnv, Vehicle,
                        make_grade_climb, measure_deliverable_torque,
                        neutral_action, TRACK_TOL)

# The grade the old shift rule could not serve at 130 km/h: 8th gear is asked
# for 366 Nm, under the 375 Nm downshift threshold, where the modelled engine
# sustains 333. With the deliverable-torque rule the box hands back 7th.
BAND_GRADE = 0.093


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


def roll(action_fn, duration, seed=1):
    env = SupervisoryTunerEnv(make_grade_climb(duration=duration), seed=0)
    obs, _ = env.reset(seed=seed)
    rs = []
    for _ in range(int(duration / 0.2) + 5):
        obs, r, term, trunc, _ = env.step(action_fn(env, obs))
        rs.append(r)
        if term or trunc:
            break
    return float(np.mean(rs)), len(rs)


def obs_differs_without_preview(duration):
    """The blinded baseline in Phase D must actually see something different.

    Sample AFTER the climb has entered the preview window. The longest preview
    horizon is 30 s and the grade starts at 180 s, so before t = 150 s both the
    sighted and blinded observations correctly read "flat road ahead" and are
    identical. Testing before then proves nothing.
    """
    a = true_neutral()
    n_steps = int(min(duration - 5.0, 190.0) / 0.2)
    seen = []
    for use_preview in (True, False):
        env = SupervisoryTunerEnv(make_grade_climb(duration=duration),
                                  use_preview=use_preview, seed=0)
        obs, _ = env.reset(seed=1)
        for _ in range(n_steps):
            obs, *_ = env.step(a)
        seen.append(np.asarray(obs, dtype=float).copy())
    return float(np.max(np.abs(seen[0] - seen[1]))), seen


def road_roll(job):
    """One road at dt = 1.0, the step train.py uses. Returns mean reward and the
    p95 torque-tracking error, in the same units as the reward's tolerance band."""
    kind, seed, policy, duration = job
    act = true_neutral() if policy == "neutral" else torque_starver()
    if kind == "band":
        c = make_grade_climb(duration=duration, dt=1.0)
        c["grade"][30:] = BAND_GRADE
        env = SupervisoryTunerEnv(c, dt=1.0, seed=seed)
        env.reset(seed=seed)
    else:
        env = TerrainTrainingEnv(duration=duration, dt=1.0, seed=seed)
        env.reset(seed=seed, options={"family": kind})
    rs, errs = [], []
    while True:
        _, r, term, trunc, info = env.step(act)
        rs.append(r)
        errs.append(abs(info["torque_req"] - info["torque"]) / max(info["torque_req"], 40.0))
        if term or trunc:
            break
    return kind, policy, float(np.mean(rs)), float(np.percentile(errs, 95))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, default=300.0)
    a = ap.parse_args()
    dur = a.duration

    # The training-road rollouts are independent; run them while the rest runs.
    roads = [("band", 0, "neutral", 300.0)] + [
        (fam, 11, "neutral", 600.0) for fam in ("single", "rolling", "double", "flat")] + [
        ("rolling", 11, "starver", 600.0)]
    pool = ProcessPoolExecutor(max_workers=len(roads))
    road_futs = [pool.submit(road_roll, j) for j in roads]

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

    # The shift rule's table must still describe the plant it was measured on.
    probe = [1600, 2200, 2600, 3200, 4400]
    table = dict(Vehicle.DELIVERABLE_TORQUE)
    fresh = dict(measure_deliverable_torque(probe))
    drift = max(abs(fresh[r] - table[r]) / table[r] for r in probe)

    road = {(k, p): (r, e) for k, p, r, e in (f.result() for f in road_futs)}
    pool.shutdown()
    band_r, band_e = road[("band", "neutral")]
    fams = ("single", "rolling", "double", "flat")
    worst_fam = max(fams, key=lambda f: abs(road[(f, "neutral")][0]))
    r_roll_n, r_roll_s = road[("rolling", "neutral")][0], road[("rolling", "starver")][0]

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
        ("gearbox table still matches the plant",
         drift < 0.015,
         f"worst drift {100 * drift:.2f} % at {len(probe)} speeds   (want < 1.5 %)"),
        (f"baseline delivers torque on a {100 * BAND_GRADE:.1f} % grade",
         band_e < TRACK_TOL and abs(band_r) < 0.05,
         f"p95 tracking error {band_e:.3f}, neutral {band_r:+.5f}   (was 0.09 before)"),
        ("neutral scores about zero on every training road",
         all(abs(road[(f, "neutral")][0]) < 0.05 for f in fams),
         f"worst {worst_fam} {road[(worst_fam, 'neutral')][0]:+.5f}   "
         + "  ".join(f"{f} {road[(f, 'neutral')][1]:.3f}" for f in fams) + "  (p95 err)"),
        ("refusing torque is punished on a training road",
         r_roll_s < r_roll_n - 0.02,
         f"starver {r_roll_s:+.5f}  vs  neutral {r_roll_n:+.5f}   (rolling hills)"),
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

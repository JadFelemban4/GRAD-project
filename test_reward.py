"""test_reward.py — Phase C, step C2.

The sanity checks that must pass before you trust a single training curve.
A broken reward does not announce itself: it produces training curves that look
completely normal while measuring nothing. Run this after ANY change to the
reward, and commit the output with the change.

    python test_reward.py                # 300 s locked climb, plus the training
                                         # roads; 367-370 s on 29 Sep 2026 with
                                         # the machine shared (not re-timed idle)
    python test_reward.py --duration 900 # the full scenario, slower
    python test_reward.py --road random  # PHASE D2: the four ORIGINAL checks on
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

16 % asks the most road power of anything D2 draws (not the most engine torque:
that is just under the notch, about 375 Nm in 7th); the notch is where a shift
happens mid-climb, which is exactly the shape of mistake 17. 13.73 % is the
notch on the plant D2 was gated and trained on -- see D2_ROADS for where it sits
on the merged plant. Each road runs long enough to hold 180 s of climb after
the latest start. The preview check samples 10 s after the drawn climb begins
-- not at a fixed 190 s, which on a road whose climb starts at 300 s would
compare two flat roads and fail for a reason that has nothing to do with the
reward.

The default invocation (no --road) is NOT only Phase D's gate any more. Since
the two branches were merged it runs Phase D's four checks on the locked climb
AND the four training-road checks from the other branch (27 September, below).
`--road random` runs only the four original checks, per D2 road.

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
step. A road sitting in that band is driven here, and every road family is
checked for neutral-about-zero and a punished starver.

ON THE PLANT OF 29 SEPTEMBER THE BAND ROAD NO LONGER SEPARATES THE TWO SHIFT
RULES. With the boost ceiling derived from drive B and air density from ambient,
the OLD flat rule (kick down only above 375 Nm) also tracks there: p95 error
0.006 at 9.3 %, and 0.026 at 9.84 %, the steepest grade the old rule keeps 8th
on (measured 29 September by reverting Vehicle.shift_ceiling_nm). The drift
check is what guards the kickdown table; the band road is kept as a road the
baseline must be able to drive.

WHICH STARVER CHECK EXERCISES THE HINGE. On the same plant the boost ceiling on
the locked climb sits about 41 kPa above the pressure the climb needs, so boost
trim pinned at -40 kPa no longer cuts torque there: the fixed-road starver's
penalty comes almost entirely from the 0-130 km/h launch (97 % of it, measured
29 September). The training-road starver is the one that holds a sustained
shortfall. Both stay required, and the launch share is printed beside the
fixed-road figure so that a small margin is not read as a tested climb.

THE EXTREMES ROADS ARE CHECKED TOO (8 October 2026). Decision 12 trains on
engine_env.ExtremesTrainingEnv: the same families, plus an ambient of 25-45 C,
a speed target that changes mid-run, hills to 18 % and the housing's heat
capacity drawn per episode. Two checks hold it to the same standard as the
terrain roads: neutral about zero on every family, at two seeds each, over the
full 900 s; and a punished starver on an extremes road. The first draft of
these roads failed the first check by a factor of ten (neutral -0.11 to -0.69
per step): slowing down faster than the road itself slows the car asks the
engine for negative torque, which this model does not make. Slowdowns are now
coasts (extreme_speed_profile).

THE BAND ROAD IS RAMPED (8 October). Its 9.3 % arrived as a one-step jump at
30 s until then; every grade change in the project is ramped over GRADE_RAMP_S
now, the fourth step agreed on 30 September.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from engine_env import (ExtremesTrainingEnv, GRADE_RAMP_S, SupervisoryTunerEnv,
                        TerrainTrainingEnv, Vehicle, make_grade_climb,
                        measure_deliverable_torque, neutral_action, TRACK_TOL)

# The grade the old shift rule could not serve at 130 km/h ON THE PLANT OF
# 27 SEPTEMBER: 8th was asked for 366 Nm, under the 375 Nm downshift threshold,
# where the modelled engine then sustained 333. With the deliverable-torque rule
# the box hands back 7th. On the plant of 29 September (air density from
# ambient, the derived table) 8th would be asked 360.5 Nm against a table value
# of 348.1 Nm at 2107 rpm, and the old rule tracks here too -- see the module
# docstring. Kept as a road the baseline must drive, not as the table's guard.
BAND_GRADE = 0.093

# The extremes roads (decision 12): every family at two seeds, full length.
XFAMS = ("locked", "single", "rolling", "double", "flat")
XSEEDS = (11, 12)


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

    Whether it CAN deliver depends on the plant: -40 kPa is a cut to the boost
    ceiling, so it only refuses torque where the road needs more than the
    ceiling minus 40 kPa. main() prints where its penalty comes from.
    """
    a = true_neutral().copy()
    a[2] = -1.0                       # boost trim at ACT_LO
    return a.astype(np.float32)


def roll(action_fn, duration, seed=1, cycle=None, log=None):
    """Mean reward over one episode. Pass a list as `log` to also collect
    (t, reward, tracking error) per step; the rollout itself is unchanged."""
    env = SupervisoryTunerEnv(cycle if cycle is not None
                              else make_grade_climb(duration=duration), seed=0)
    obs, _ = env.reset(seed=seed)
    rs = []
    for _ in range(int(duration / 0.2) + 5):
        t = env.k * env.dt
        obs, r, term, trunc, info = env.step(action_fn(env, obs))
        rs.append(r)
        if log is not None:
            log.append((t, float(r), abs(info["torque_req"] - info["torque"])
                        / max(info["torque_req"], 40.0)))
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
#
# THE NOTCH MOVED WITH THE MERGE, AND THIS TUPLE WAS NOT MOVED WITH IT. 13.73 %
# is the notch on the plant D2 was gated and trained on (22 September). On the
# merged plant -- air density from ambient and the deliverable-torque shift
# rule -- the 7th-to-6th kickdown at 130 km/h sits between 13.96 and 13.97 %
# (Vehicle.demand swept in 0.01 % steps, 29 September), so 13.73 % is now a
# 7th-gear road just below it. The +6.9 K margin is the old plant's too. D2 is
# closed, so the tuple stays as it was gated; before this gate is used for any
# NEW training, re-run check_random_road.py's notch sweep and move it.
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


def road_roll(job):
    """One road at dt = 1.0, the step train.py uses. Returns mean reward and the
    p95 torque-tracking error, in the same units as the reward's tolerance band."""
    kind, seed, policy, duration = job
    act = true_neutral() if policy == "neutral" else torque_starver()
    if kind == "band":
        c = make_grade_climb(duration=duration, dt=1.0)
        c["grade"] = BAND_GRADE * np.clip((c["t"] - 30.0) / GRADE_RAMP_S, 0.0, 1.0)
        env = SupervisoryTunerEnv(c, dt=1.0, seed=seed)
        env.reset(seed=seed)
    elif kind.startswith("x-"):
        env = ExtremesTrainingEnv(duration=duration, dt=1.0, seed=seed)
        env.reset(seed=seed, options={"family": kind[2:]})
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
    ap.add_argument("--road", choices=("fixed", "random"), default="fixed",
                    help="'random' runs the four checks on the Phase D2 roads "
                         "listed in D2_ROADS instead of the fixed climb")
    ap.add_argument("--jobs", type=int, default=10,
                    help="parallel rollouts for --road random")
    a = ap.parse_args()
    if a.road == "random":
        raise SystemExit(main_random_road(a.jobs))
    dur = a.duration

    # The training-road rollouts are independent; run them while the rest runs.
    roads = [("band", 0, "neutral", 300.0)] + [
        (fam, 11, "neutral", 600.0) for fam in ("single", "rolling", "double", "flat")] + [
        ("rolling", 11, "starver", 600.0)] + [
        ("x-" + fam, sd, "neutral", 900.0) for fam in XFAMS for sd in XSEEDS] + [
        ("x-rolling", XSEEDS[0], "starver", 900.0)]
    pool = ProcessPoolExecutor(max_workers=len(roads))
    road_futs = [pool.submit(road_roll, j) for j in roads]

    neutral = true_neutral()
    print(f"episode length : {dur:.0f} s   (grade starts at 180 s)")
    print(f"neutral action : {np.round(neutral, 3)}\n")

    r_neutral, n1 = roll(lambda e, o: neutral, dur)
    starve_log = []
    r_starve, n2 = roll(lambda e, o: torque_starver(), dur, log=starve_log)
    total_pen = sum(r for _, r, _ in starve_log)
    launch_share = (sum(r for t, r, _ in starve_log if t < 20.0) / total_pen
                    if total_pen < 0 else float("nan"))
    climb_err = [e for t, _, e in starve_log if t >= 180.0]
    e_climb = float(np.mean(climb_err)) if climb_err else float("nan")
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
    table = dict(Vehicle().DELIVERABLE_TORQUE)     # derived: data/derived_params.json
    fresh = dict(measure_deliverable_torque(probe))
    drift = max(abs(fresh[r] - table[r]) / table[r] for r in probe)

    road = {}
    for (k, sd, p, _), f in zip(roads, road_futs):
        _, _, r, e = f.result()
        road[(k, p)] = road[(k, p, sd)] = (r, e)
    pool.shutdown()
    band_r, band_e = road[("band", "neutral")]
    fams = ("single", "rolling", "double", "flat")
    worst_fam = max(fams, key=lambda f: abs(road[(f, "neutral")][0]))
    r_roll_n, r_roll_s = road[("rolling", "neutral")][0], road[("rolling", "starver")][0]
    xs = [(f, sd) for f in XFAMS for sd in XSEEDS]
    worst_x = max(xs, key=lambda k: abs(road[("x-" + k[0], "neutral", k[1])][0]))
    r_xr_n = road[("x-rolling", "neutral", XSEEDS[0])][0]
    r_xr_s = road[("x-rolling", "starver", XSEEDS[0])][0]

    checks = [
        ("neutral action scores about zero",
         abs(r_neutral) < 0.05,
         f"mean reward {r_neutral:+.5f}   (want |r| < 0.05)"),
        ("refusing torque is punished",
         r_starve < r_neutral - 0.02,
         f"starver {r_starve:+.5f}  vs  neutral {r_neutral:+.5f}"
         + ("   <-- REWARD HACK PRESENT" if r_starve >= r_neutral else "")
         + f"   ({100 * launch_share:.0f} % of it from the 0-20 s launch)"),
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
         f"p95 tracking error {band_e:.3f}, neutral {band_r:+.5f}"),
        ("neutral scores about zero on every training road",
         all(abs(road[(f, "neutral")][0]) < 0.05 for f in fams),
         f"worst {worst_fam} {road[(worst_fam, 'neutral')][0]:+.5f}   "
         + "  ".join(f"{f} {road[(f, 'neutral')][1]:.3f}" for f in fams) + "  (p95 err)"),
        ("refusing torque is punished on a training road",
         r_roll_s < r_roll_n - 0.02,
         f"starver {r_roll_s:+.5f}  vs  neutral {r_roll_n:+.5f}   (rolling hills)"),
        ("neutral scores about zero on every extremes road",
         all(abs(road[("x-" + f, "neutral", sd)][0]) < 0.05 for f, sd in xs),
         f"worst {worst_x[0]} seed {worst_x[1]} "
         f"{road[('x-' + worst_x[0], 'neutral', worst_x[1])][0]:+.5f}, "
         f"{len(xs)} roads; worst p95 err "
         f"{max(road[('x-' + f, 'neutral', sd)][1] for f, sd in xs):.3f}"),
        ("refusing torque is punished on an extremes road",
         r_xr_s < r_xr_n - 0.02,
         f"starver {r_xr_s:+.5f}  vs  neutral {r_xr_n:+.5f}   (rolling hills, seed {XSEEDS[0]})"),
    ]

    print(f"{'check':46s} {'result':>7}   detail")
    print("-" * 96)
    for name, ok, detail in checks:
        print(f"{name:46s} {'PASS' if ok else 'FAIL':>7}   {detail}")
    print("-" * 96)

    print(f"\nFOR INFORMATION, NOT A PASS/FAIL: the fixed-road starver's mean "
          f"tracking error after 180 s is {e_climb:.3f} (TRACK_TOL {TRACK_TOL})")
    if not e_climb > TRACK_TOL:
        print("""  The starver does NOT starve on the climb: boost trim at -40 kPa leaves the
  climb inside the boost ceiling, so "refusing torque is punished" passed on
  the launch. "refusing torque is punished on a training road" is the check
  that holds a sustained shortfall; do not drop it.""")

    print(f"\nFOR INFORMATION, NOT A PASS/FAIL: random policy scores "
          f"{r_random:+.5f}")
    if r_random > r_neutral:
        print("""  Random currently scores ABOVE neutral. That is not automatically a bug.
  The reward is baseline-relative and pays for protection. Slew-limited, the
  random actions settle near the middle of each range -- about 2 deg of retard,
  lambda 0.95, -13 kPa of boost trim -- and that enrichment cools the turbine
  on the climb. This episode's preference draw (reset seed 1) also weights fuel
  lightly, so the extra fuel costs little. Watch the fuel and tracking terms
  when an agent trains -- if its gains come mostly from the damage term, the
  weights need rebalancing before an experiment scores anything.""")

    if all(c[1] for c in checks):
        print("\nAll checks pass. The reward is safe to train against.")
    else:
        print("""
STOP. Do not train until this passes. Diagnose WHICH check failed before
changing anything -- mistake 17 was a scenario failure that looked like a
weight problem.

If "gearbox table still matches the plant" failed, the plant moved under the
stored kickdown table: run python derive_params.py, which re-measures it.

If "baseline delivers torque" or "neutral scores about zero on every training
road" failed, the BASELINE cannot drive a road. That is a plant or scenario
defect (mistake 17), not a weight problem; python check_roads.py names it.

If "refusing torque is punished" (either road) failed, the tracking penalty is
too weak relative to the damage reward: a policy that simply declines to make
torque scores better than one that does its job. An agent will find this within
a few thousand steps, and every number an experiment reports would then be an
artefact of it.

That fix is a weight change, not a redesign. Raise the tracking coefficient
(w[0]) until the starver scores clearly negative, re-run this file, and record
both the old and new weights in the log. Do it before training, not after.""")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

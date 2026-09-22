"""check_random_road.py — does every Phase D2 road bind, and is the blind arm blind?

    python check_random_road.py            everything, about fifteen minutes
    python check_random_road.py --quick    skip the fine grade sweep

Run BEFORE any Phase D2 agent is trained. Its output is what
`results/PREREGISTRATION_D2.md` quotes; a figure there that this script does not
print should not be there.

WHAT IT CHECKS, and why each one is load-bearing
------------------------------------------------
A. **The road changes between resets.** Limit 7 of `PREREGISTRATION.md` was
   found by a check that printed `road identical across 3 resets with
   different seeds : True`. The same line, on the D2 wrapper, must print False.

B. **The blind arm is blind.** Two roads, identical except for when and how
   steep the climb is. Before the earlier climb starts, a blind agent's
   observations must be IDENTICAL on both -- that is what "cannot know the road
   ahead" means, measured rather than argued. A sighted agent's must differ
   from 30 s before (the longest preview horizon), which proves the check can
   see a difference when there is one. A test that cannot fail cannot confirm
   (AUDIT.md C3), so B prints both.

C. **Every grade in the range binds, not only the nine that were measured.**
   `results/NEXT_EXPERIMENT_DESIGN.md` measured 12-16 % in 0.5 % steps and all
   nine bind, weakest 14.0 % at +12.7 K. But training draws grade from a
   CONTINUOUS range, and the peak is a sawtooth: it drops 58 K between 13.5 %
   and 14.0 %, where the gearbox hands back a gear. A notch between two grid
   points could be deeper than either. So the whole range is swept at 0.05 %,
   and the notch region again at 0.01 %. Run at the WORST-CASE start, 300 s,
   in a 720 s evaluation episode -- the shortest climb any D2 episode has.

D. **Every one of the twenty frozen evaluation episodes binds.** An episode
   that never reaches the trigger carries no protection signal and dilutes the
   rest; the preregistration requires all twenty.

E. **The training condition binds too.** Training runs dt 0.2 over 900 s, not
   dt 1.0 over 720 s. CLAUDE.md measured the peak dt-invariant at one point
   (12 %, 180 s); E re-checks it at the thinnest grade C finds, at the latest
   start.

All of it uses the NEUTRAL policy -- the baseline ECU, unsupervised -- because
"binds" is a property of the road, not of whoever is protecting against it.
"""
import argparse
import os
import time
from multiprocessing import Pool

import numpy as np

import check_premise as C
import random_road as RR
from engine_env import (PREVIEW_S, SupervisoryTunerEnv, TURB_PROTECT_K,
                        make_grade_climb)

TRIGGER_C = TURB_PROTECT_K - 273.15
EVAL_DT, EVAL_DUR = 1.0, 720.0
TRAIN_DT, TRAIN_DUR = 0.2, 900.0
WORST_START = RR.RANGES["start_s"][1]          # 300 s: the shortest climb


def neutral_episode(job):
    """(start_s, grade, dt, duration, seed, weights) -> binding figures."""
    start_s, grade, dt, dur, seed, w = job
    env = SupervisoryTunerEnv(RR.climb(start_s, grade, duration=dur, dt=dt),
                              dt=dt, seed=seed)
    obs, _ = env.reset(seed=seed)
    if w is not None:
        env.w = np.asarray(w, dtype=np.float32)
        obs = env._obs()
    peak, above = 0.0, 0.0
    while True:
        obs, _, term, trunc, info = env.step(C.p_neutral(env, obs))
        peak = max(peak, info["t_turb"])
        if info["t_turb"] > TURB_PROTECT_K:
            above += dt
        if term or trunc:
            break
    return dict(start_s=start_s, grade=grade, dt=dt, peak=peak - 273.15,
                margin=peak - TURB_PROTECT_K, above=above)


def obs_trace(start_s, grade, use_preview, n):
    """(env.k, observation) after each of the first n steps, neutral, dt 1.0.

    Keyed on the environment's own step counter rather than the list index:
    the observation returned by the i-th step is built with k = i + 1, and at
    dt 1.0 k IS the time in seconds, so the reported instant is the one the
    agent actually sees.
    """
    env = SupervisoryTunerEnv(RR.climb(start_s, grade, duration=EVAL_DUR, dt=EVAL_DT),
                              dt=EVAL_DT, seed=1000, use_preview=use_preview)
    obs, _ = env.reset(seed=1000)
    out = [(env.k, np.asarray(obs, dtype=float).copy())]
    for _ in range(n):
        obs, *_ = env.step(C.p_neutral(env, obs))
        out.append((env.k, np.asarray(obs, dtype=float).copy()))
    return out


def first_difference(a, b):
    """The time, in seconds at dt 1.0, of the first observation that differs."""
    for (k, x), (_, y) in zip(a, b):
        if np.max(np.abs(x - y)) > 0.0:
            return int(round(k * EVAL_DT))
    return None


def row(r):
    ok = "binds" if r["margin"] > 0 else "DOES NOT BIND"
    return (f"  {100 * r['grade']:7.2f} %  start {r['start_s']:6.1f} s  "
            f"peak {r['peak']:6.1f} C  margin {r['margin']:+6.1f} K  "
            f"{r['above']:5.0f} s above   {ok}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true",
                    help="skip C, the fine grade sweep (~10 of the ~15 minutes)")
    ap.add_argument("--jobs", type=int,
                    default=max(1, min(10, (os.cpu_count() or 4) - 2)))
    a = ap.parse_args()
    t0 = time.time()
    failures = []

    print("=" * 78)
    print("PHASE D2 -- does every road bind, and is the blind arm blind?")
    print(f"trigger {TRIGGER_C:.0f} C;  ranges start {RR.RANGES['start_s']} s, "
          f"grade {RR.RANGES['grade']};  road_sha {RR.code_sha()}")
    print("=" * 78)

    # ---- A ------------------------------------------------------------------
    env = RR.RandomClimb(SupervisoryTunerEnv(make_grade_climb(), seed=0), seed=0)
    roads = []
    for s in (0, 1, 2):
        _, info = env.reset(seed=s)
        roads.append((round(info["road"]["start_s"], 6), round(info["road"]["grade"], 8)))
    same = len(set(roads)) == 1
    grades = sorted({g for _, g in roads})
    starts = sorted({s for s, _ in roads})
    print("\nA. THE ROAD CHANGES BETWEEN RESETS")
    print(f"  road identical across 3 resets with different seeds : {same}")
    print(f"  distinct climb starts                               : "
          f"{[round(s, 1) for s in starts]} s")
    print(f"  distinct grades                                     : "
          f"{[round(100 * g, 2) for g in grades]} %")
    print("  (Phase D printed True, [0.0, 0.12] and t = 180 s -- limit 7.)")
    if same:
        failures.append("A: the road does not change between resets")

    # ---- B ------------------------------------------------------------------
    early, late = (150.0, 0.12), (250.0, 0.16)
    n = int(late[0]) + 5
    blind = [obs_trace(*early, False, n), obs_trace(*late, False, n)]
    sight = [obs_trace(*early, True, n), obs_trace(*late, True, n)]
    kb = first_difference(*blind)
    ks = first_difference(*sight)
    horizon = int(max(PREVIEW_S))
    print("\nB. THE BLIND ARM IS BLIND")
    print(f"  two roads: climb at {early[0]:.0f} s / {100 * early[1]:.0f} % and "
          f"at {late[0]:.0f} s / {100 * late[1]:.0f} %, same seed and weights")
    print(f"  BLIND   observations first differ at t = {kb} s   "
          f"(want {early[0]:.0f}: the moment the earlier climb begins)")
    print(f"  SIGHTED observations first differ at t = {ks} s   "
          f"(want {early[0] - horizon:.0f}: {horizon} s of preview earlier)")
    print("  So before its climb arrives, the blind agent sees exactly the same")
    print("  thing whichever road it is on. The sighted row proves the check can")
    print("  see a difference when one exists.")
    if kb is None or kb < int(early[0]):
        failures.append(f"B: blind observations differ at t = {kb} s, BEFORE the "
                        f"climb at {early[0]:.0f} s -- the blind arm can see ahead")
    if ks is None or ks >= int(early[0]):
        failures.append(f"B: sighted observations do not lead the blind ones "
                        f"(t = {ks} s) -- the check cannot see a difference")

    pool = Pool(a.jobs)

    # ---- C ------------------------------------------------------------------
    sweep = []
    if not a.quick:
        g_lo, g_hi = RR.RANGES["grade"]
        coarse = np.round(np.arange(g_lo, g_hi + 1e-9, 0.0005), 5)
        notch = np.round(np.arange(0.1360, 0.1410 + 1e-9, 0.0001), 5)
        grid = sorted(set(coarse.tolist()) | set(notch.tolist()))
        print(f"\nC. EVERY GRADE BINDS -- {len(grid)} grades at the worst-case start "
              f"({WORST_START:.0f} s), dt {EVAL_DT}, {EVAL_DUR:.0f} s")
        print("   0.05 % steps over the whole range, 0.01 % over 13.60-14.10 %;"
              f" {a.jobs} in parallel")
        jobs = [(WORST_START, g, EVAL_DT, EVAL_DUR, 1000, None) for g in grid]
        sweep = pool.map(neutral_episode, jobs)
        worst = min(sweep, key=lambda r: r["margin"])
        nonbind = [r for r in sweep if r["margin"] <= 0]
        for r in sweep:
            if (abs(r["grade"] * 1e4 - round(r["grade"] * 1e4 / 50) * 50) < 1e-6
                    or r is worst or r["margin"] <= 0):
                print(row(r) + ("   <- WEAKEST" if r is worst else ""))
        print(f"  ... {len(sweep)} grades in all; every 0.5 % point, the weakest and "
              "any failure shown")
        print(f"  weakest: {100 * worst['grade']:.2f} % at {worst['margin']:+.1f} K, "
              f"{worst['above']:.0f} s above")
        print(f"  grades that do NOT bind: {len(nonbind)} of {len(sweep)}")
        if nonbind:
            failures.append(f"C: {len(nonbind)} grades do not bind, e.g. "
                            f"{100 * nonbind[0]['grade']:.2f} %")

    # ---- D ------------------------------------------------------------------
    import evaluate
    print(f"\nD. EVERY FROZEN EVALUATION EPISODE BINDS -- evaluate.EPISODES_D2, "
          f"dt {EVAL_DT}, {EVAL_DUR:.0f} s")
    jobs = [(st, g, EVAL_DT, EVAL_DUR, s, w) for s, w, st, g in evaluate.EPISODES_D2]
    frozen = pool.map(neutral_episode, jobs)
    for (s, *_), r in zip(evaluate.EPISODES_D2, frozen):
        print(f"  ep {s}" + row(r)[1:])
    fw = min(frozen, key=lambda r: r["margin"])
    nb = [r for r in frozen if r["margin"] <= 0]
    print(f"  weakest frozen episode: {100 * fw['grade']:.3f} %, start "
          f"{fw['start_s']:.1f} s, {fw['margin']:+.1f} K, {fw['above']:.0f} s above")
    print(f"  frozen episodes that do NOT bind: {len(nb)} of {len(frozen)}")
    print(f"  neutral damage is not reported here: this checks the ROAD, and the")
    print(f"  damage figures belong to evaluate.py --protocol d2.")
    if nb:
        failures.append(f"D: {len(nb)} frozen episodes do not bind")

    # ---- E ------------------------------------------------------------------
    thin = min(sweep, key=lambda r: r["margin"])["grade"] if sweep else fw["grade"]
    tjobs = [(WORST_START, thin, TRAIN_DT, TRAIN_DUR, 0, None),
             (RR.RANGES["start_s"][0], thin, TRAIN_DT, TRAIN_DUR, 0, None),
             (WORST_START, RR.RANGES["grade"][0], TRAIN_DT, TRAIN_DUR, 0, None)]
    print(f"\nE. THE TRAINING CONDITION BINDS -- dt {TRAIN_DT}, {TRAIN_DUR:.0f} s")
    tr = pool.map(neutral_episode, tjobs)
    for r in tr:
        print(row(r))
    ev = {round(r["grade"], 6): r["peak"] for r in sweep}
    if sweep and round(thin, 6) in ev:
        print(f"  peak at the thinnest grade: dt {EVAL_DT} -> {ev[round(thin, 6)]:.1f} C, "
              f"dt {TRAIN_DT} -> {tr[0]['peak']:.1f} C")
    if any(r["margin"] <= 0 for r in tr):
        failures.append("E: a training-condition road does not bind")

    pool.close()
    pool.join()

    print("\n" + "=" * 78)
    if failures:
        print("FAIL -- do NOT train Phase D2 until each of these is resolved:")
        for f in failures:
            print("  " + f)
    else:
        print("PASS -- every road in the range binds and the blind arm is blind.")
    print(f"({(time.time() - t0) / 60:.1f} min)")
    print("=" * 78)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

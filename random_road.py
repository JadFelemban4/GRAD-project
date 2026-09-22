"""random_road.py — the randomised climb for Phase D2. A WRAPPER, not an edit.

    python random_road.py          self-test: reproduces Phase D's road exactly,
                                   draws differ between resets, the frozen set
                                   regenerates from its seed

WHY THIS EXISTS
---------------
`results/PREREGISTRATION.md` limit 7: **the blinded arm of Phase D was not
blind.** `make_grade_climb()` builds one road -- flat, then 12 % from t = 180 s
-- and `reset()` never rebuilds it, so every training and evaluation episode is
the same hill at the same second. The blind agent's thermal state takes a
distinct value at every step, which on a fixed road is a clock. A clock plus a
memorised road is a preview obtained without the preview channel.

This file removes that. Every episode draws its own climb:

    start time   uniform on [120, 300] s
    grade        uniform on [12, 16] %

so no amount of memorisation tells the blind agent when -- or how hard -- the
hill arrives. The preview channel becomes the only route to anticipating it,
which is what an ablation of preview has to mean. The design, the options that
were rejected, and the measurement behind the ranges are in
`results/NEXT_EXPERIMENT_DESIGN.md`; the decision (option B) was the team's.

WHY A WRAPPER AND NOT A CHANGE TO `engine_env.py`
-------------------------------------------------
Because `fingerprint.py` hashes the CODE of `engine_env.py`, and every Phase D
agent's `meta.json` records that hash. Adding so much as a `start_s=180.0`
keyword to `make_grade_climb` -- a change no engine can feel -- would move
`plant_sha`, and `evaluate.py` would then REFUSE all sixteen Phase D agents.
Phase D's `runs/` are the first experiment's evidence, and a guard that fires on
the project's own follow-up experiment is the failure `fingerprint.py`'s
docstring already warns about for the document sweep.

So this module builds the cycle ITSELF and hands it to the unchanged
environment. `engine_env.py` is byte-identical before and after it, and the
self-test below proves the road it builds at (180 s, 12 %) is the Phase D road
to the last element.

IT IS STILL FINGERPRINTED. Its own code is hashed into the Phase D2 scenario
(`spec()["road_sha"]`), so a D2 agent trained on one version of this file is
refused by an evaluation running another -- the same guarantee the plant files
get, without dragging Phase D into it.

THE ONE LINE THIS DUPLICATES, stated rather than hidden
-------------------------------------------------------
`make_grade_climb` places the climb with `g[int(180 / dt):] = grade`. `climb()`
below repeats that expression with `start_s` in place of 180. That is two
definitions of "where the hill starts", and a second source of truth is how
this project acquires drift (CLAUDE.md mistake 11). It is guarded rather than
tolerated: `_check_phase_d_road()` asserts that `climb(180, 0.12)` equals
`make_grade_climb()` element for element, at both steps the project uses, and
runs every time this module is imported. If `make_grade_climb`'s road shape is
ever changed, the import fails instead of the two quietly diverging.

WHAT THE BLIND AGENT CAN STILL KNOW, and it is legitimate
---------------------------------------------------------
Once the climb starts, observation index 13 carries the grade the car is ON --
the same signal the `current-grade` comparator uses, which a real car gets from
a nose-down accelerometer. That is "no preview", not "no information". What the
blind agent can no longer know is anything about the road AHEAD: before the
climb, its observations are identical whichever road was drawn, because the
physics is causal and the flat approach is the same flat approach. The
verification script `check_random_road.py` measures exactly that.

The speed profile (0 -> 130 km/h in 20 s, then constant) is the same in every
draw, so `torque_req` and `aggression` -- the only other observation channels
built from the road -- carry nothing about the climb either.
"""
import hashlib
import inspect

import gymnasium as gym
import numpy as np

from engine_env import make_grade_climb

# ---------------------------------------------------------------------------
# THE DESIGN, as decided 22 September 2026 (results/NEXT_EXPERIMENT_DESIGN.md,
# "Decision -- OPTION B"). Changing any of these is a NEW experiment.
# ---------------------------------------------------------------------------
RANGES = {
    "start_s": (120.0, 300.0),     # when the climb begins
    "grade": (0.12, 0.16),         # how steep it is -- every value here binds
}
V_KMH = 130.0                      # as Phase D
T_AMB_K = 315.0                    # 42 C, as Phase D

# A fixed tag mixed into every road seed, so the road stream is statistically
# independent of the preference-weight stream that `engine_env.reset()` draws
# from the same integer seed. "ROAD" in ASCII.
ROAD_STREAM = 0x524F4144

# The frozen evaluation set is drawn from this, once. See frozen_episodes().
FROZEN_SEED = 20260922
N_FROZEN = 20


def climb(start_s, grade, duration=900.0, dt=0.2, t_amb=T_AMB_K, v_kmh=V_KMH):
    """One climb: flat, then `grade` from `start_s` to the end of the episode.

    Built by asking `make_grade_climb` for everything it already defines -- the
    time base, the speed ramp, ambient, pressure, humidity -- and then placing
    the grade step at `start_s` instead of 180 s, with the SAME expression
    `make_grade_climb` uses. See "THE ONE LINE THIS DUPLICATES" above.
    """
    c = make_grade_climb(duration=duration, dt=dt, t_amb=t_amb, grade=grade,
                         v_kmh=v_kmh)
    g = np.zeros_like(c["grade"])
    g[int(start_s / dt):] = grade
    c["grade"] = g
    return c


def draw(rng, ranges=RANGES):
    """One (start_s, grade) pair, uniform on each range, from `rng`."""
    s = float(rng.uniform(*ranges["start_s"]))
    g = float(rng.uniform(*ranges["grade"]))
    return s, g


def road_rng(seed):
    """The road stream for an integer seed -- independent of the weight stream."""
    return np.random.default_rng([ROAD_STREAM, int(seed)])


class RandomClimb(gym.Wrapper):
    """Rebuild the environment's road at every reset.

    `reset(seed=s)` reseeds the road stream from `s`; a plain `reset()` draws
    the next road from the stream it already has. That matches how
    stable-baselines3 calls it -- seeded once, then unseeded for every episode
    after -- so a training run is a deterministic sequence of roads given its
    seed.

    `reset(options={"start_s": s, "grade": g})` PINS the road instead of
    drawing one. Evaluation does not need it (it builds the pinned cycle
    directly), but it makes a single episode reproducible from its two numbers.

    The drawn road is returned in `info["road"]` and kept on `self.road`.
    """

    def __init__(self, env, seed=None, duration=900.0, ranges=RANGES):
        super().__init__(env)
        self.duration = float(duration)
        self.ranges = ranges
        self._rng = road_rng(0 if seed is None else seed)
        self.road = None

    def reset(self, *, seed=None, options=None):
        if seed is not None:
            self._rng = road_rng(seed)
        opts = dict(options or {})
        if "start_s" in opts or "grade" in opts:
            start_s, grade = float(opts.pop("start_s")), float(opts.pop("grade"))
        else:
            start_s, grade = draw(self._rng, self.ranges)
        base = self.env.unwrapped
        base.cycle = climb(start_s, grade, duration=self.duration, dt=base.dt)
        self.road = {"start_s": start_s, "grade": grade}
        obs, info = self.env.reset(seed=seed, options=opts or None)
        info = dict(info)
        info["road"] = dict(self.road)
        return obs, info


def frozen_episodes(seed=FROZEN_SEED, n=N_FROZEN):
    """The Phase D2 evaluation set, regenerated from its seed.

    TWENTY EPISODES, each (episode seed, weights, start_s, grade):

    * **The seeds and weights are Phase D's twenty, unchanged**
      (`evaluate.EPISODES`). The two experiments therefore score every policy
      with the same twenty rulers, and the ONLY thing that differs between
      Phase D's episode k and Phase D2's episode k is the road. A difference
      between the experiments cannot be a difference in the preference draw.

    * **The roads are a Latin hypercube, not twenty independent draws.** Each
      range is cut into twenty equal strata and every stratum is used exactly
      once, then the two axes are paired by a random permutation. Marginally
      that is still uniform on each range -- the preregistered distribution --
      but twenty iid draws can leave a quarter of the grade range empty, and
      the grade range contains the gearbox notch, where the box hands back a
      gear and the margin over the trigger collapses -- to +6.9 K at 13.73 %,
      the deepest point `check_random_road.py`'s 0.01 % sweep found (the 0.5 %
      design grid had put it at 14.0 %, +12.7 K). A test set that happened to
      skip the notch, or pile into it, would be a test set chosen by luck.

    Training draws iid from `RANGES`; only the frozen TEST set is stratified.

    Values are rounded (0.01 s, 1e-5 in grade) so the literal in `evaluate.py`
    is readable and exact. `evaluate.EPISODES_D2` must equal this function's
    output; `python random_road.py` checks that it does.
    """
    import evaluate
    rng = np.random.default_rng(seed)
    (s_lo, s_hi), (g_lo, g_hi) = RANGES["start_s"], RANGES["grade"]
    u_s = (rng.permutation(n) + rng.random(n)) / n
    u_g = (rng.permutation(n) + rng.random(n)) / n
    out = []
    for i, (ep_seed, w) in enumerate(evaluate.EPISODES[:n]):
        s = round(s_lo + (s_hi - s_lo) * float(u_s[i]), 2)
        g = round(g_lo + (g_hi - g_lo) * float(u_g[i]), 5)
        out.append((ep_seed, w, s, g))
    return tuple(out)


def code_sha():
    """SHA-256 over this module's CODE, docstrings and comments excluded.

    Uses `fingerprint._code_only` so the rule is the one the plant files get:
    correcting a sentence in this docstring does not invalidate a trained
    agent, changing a range or the climb expression does.
    """
    import fingerprint as FP
    src = inspect.getsource(inspect.getmodule(code_sha))
    src = src.replace("\r\n", "\n")
    code = FP._code_only(src)
    return hashlib.sha256((code if code is not None else src).encode("utf-8")
                          ).hexdigest()[:16]


def spec():
    """What goes into the Phase D2 fingerprint's `scenario` field.

    A DIFFERENT VALUE from Phase D's `{grade, t_amb, v_kmh}`, on purpose: a
    Phase D agent scored under this protocol, or a D2 agent scored under
    Phase D's, is refused by `fingerprint.compare` rather than producing a
    number that belongs to neither experiment.
    """
    return {
        "protocol": "random-climb",
        "start_s": [float(x) for x in RANGES["start_s"]],
        "grade": [float(x) for x in RANGES["grade"]],
        "v_kmh": float(V_KMH),
        "t_amb": float(T_AMB_K),
        "road_sha": code_sha(),
    }


def _check_phase_d_road():
    """climb(180, 0.12) must BE Phase D's road. Runs at import; see docstring."""
    for dt, dur in ((0.2, 900.0), (1.0, 720.0)):
        ref = make_grade_climb(duration=dur, dt=dt)
        got = climb(180.0, 0.12, duration=dur, dt=dt)
        for k in ("t", "v_mps", "grade"):
            if not np.array_equal(ref[k], got[k]):
                raise AssertionError(
                    f"random_road.climb(180, 0.12) differs from make_grade_climb() "
                    f"in '{k}' at dt {dt}. The road shape in engine_env.py has "
                    "changed and the duplicated expression here no longer "
                    "matches it. Fix climb() before trusting any Phase D2 "
                    "result -- see 'THE ONE LINE THIS DUPLICATES'.")
        for k in ("t_amb", "p_baro", "humidity"):
            if ref[k] != got[k]:
                raise AssertionError(f"random_road.climb: '{k}' differs from "
                                     "make_grade_climb().")


_check_phase_d_road()


def _selftest():
    import evaluate
    from engine_env import SupervisoryTunerEnv

    print("random_road.py self-test")
    print("-" * 64)
    print("  climb(180 s, 12 %) == make_grade_climb(), dt 0.2 and 1.0 : True"
          "   (checked at import)")

    env = RandomClimb(SupervisoryTunerEnv(make_grade_climb(), seed=0), seed=0)
    roads = []
    for s in (0, 1, 2):
        _, info = env.reset(seed=s)
        roads.append((info["road"]["start_s"], info["road"]["grade"]))
    same = len(set(roads)) == 1
    print(f"  road identical across 3 resets with different seeds     : {same}")
    for s, (st, g) in zip((0, 1, 2), roads):
        print(f"      seed {s}: start {st:6.1f} s   grade {100 * g:5.2f} %")

    env.reset(seed=7)
    a = [tuple(env.road.values()) for _ in range(1)]
    for _ in range(3):
        env.reset()
        a.append(tuple(env.road.values()))
    env.reset(seed=7)
    b = [tuple(env.road.values())]
    for _ in range(3):
        env.reset()
        b.append(tuple(env.road.values()))
    print(f"  same seed -> same sequence of roads (4 resets)          : {a == b}")
    print(f"  unseeded resets draw NEW roads                          : "
          f"{len(set(a)) == len(a)}")

    fe = frozen_episodes()
    lit = getattr(evaluate, "EPISODES_D2", None)
    match = lit is not None and tuple(lit) == fe
    print(f"  evaluate.EPISODES_D2 regenerates from seed {FROZEN_SEED}     : {match}")
    print(f"  road_sha                                                : {code_sha()}")
    print("-" * 64)
    ok = (not same) and a == b and len(set(a)) == len(a) and match
    if lit is None:
        print("  evaluate.EPISODES_D2 does not exist yet. The set it must hold:")
        for e in fe:
            print(f"    ({e[0]}, {e[1]!r}, {e[2]:.2f}, {e[3]:.5f}),")
    print("SELF-TEST " + ("PASSES" if ok else "FAILS"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(_selftest())

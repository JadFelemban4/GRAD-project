"""evaluate.py — Phase D's evaluation protocol. TWENTY FIXED EPISODES.

    python evaluate.py                          the hand-written policies only
    python evaluate.py runs/sighted_seed0        add one trained agent
    python evaluate.py runs/sighted_seed0 runs/blind_seed0    sighted vs blinded

================================================================================
THE TWENTY EPISODES ARE FROZEN. DO NOT EDIT `EPISODES`.
Changing the test set after seeing a result is the one mistake this project
cannot recover from -- CLAUDE.md, "What to do next", step 5. If the protocol has
to change, that is a new protocol with a new name, and BOTH get reported.
================================================================================

WHY A FIXED SET EXISTS AT ALL, and it is not bureaucracy.

`SupervisoryTunerEnv.reset()` draws a fresh preference vector every episode --
how much the agent is asked to weigh torque tracking against fuel and against
component life. So **every episode is scored with a different ruler**, and an
episode return cannot be compared with the next one.

That is not a hypothetical. The first training run, 50 000 steps on seed 0,
produced eleven episodes ranging from **-506.4 to +643.6**, and `train.py`
summarised them as "first 5 -115.99 -> last 5 +103.71, the curve improved". The
largest positive episode in that run (+643.6) is in the FIRST five. **With that
spread and eleven samples, first-five-versus-last-five is not evidence of
learning.** It is the weight draw.

This file removes the ruler as a variable: twenty (seed, weights) pairs, drawn
once from seed 20260918, written below as literals, and used identically for
every policy. A difference between two rows is then a difference between the
POLICIES.

WHAT IS REPORTED, and why median and IQR rather than a mean.

Damage is an exponential in temperature, so its distribution is skewed and a
single hot episode drags a mean around. The median says what a typical episode
costs; the interquartile range says how much the policy varies. Report both, and
report the worst episode too -- a protection policy that is good on average and
occasionally terrible is not a protection policy.

THE COMPARATORS, and the middle one is the one that matters.

  baseline ECU    the production-representative controller, no supervision
  reactive        acts on the turbine temperature it can already measure
  current-grade   acts on the slope the car is on RIGHT NOW, with NO preview
  agent           trained, with preview
  agent (blind)   the same training with the preview channel zeroed

**`current-grade` is the honest comparator for preview**, because it is what a
vehicle gets for free from a nose-down accelerometer. Beating `baseline` proves
supervision helps; only beating `current-grade` proves the PREVIEW helped. See
AUDIT.md C3.
"""
import sys
import numpy as np

import check_premise as C
from engine_env import SupervisoryTunerEnv, make_grade_climb, TURB_PROTECT_K

DT = 1.0
DURATION = 720.0

# Drawn once from numpy's default_rng(20260918), exactly as reset() draws them.
# (episode seed, (w_track, w_fuel, w_life))
EPISODES = (
    (1000, (0.690154, 0.012829, 0.297017)),
    (1001, (0.682741, 0.181419, 0.135840)),
    (1002, (0.690313, 0.060454, 0.249233)),
    (1003, (0.484162, 0.022753, 0.493085)),
    (1004, (0.583678, 0.036390, 0.379932)),
    (1005, (0.529443, 0.168930, 0.301627)),
    (1006, (0.690245, 0.057769, 0.251987)),
    (1007, (0.590381, 0.320322, 0.089297)),
    (1008, (0.699723, 0.046890, 0.253387)),
    (1009, (0.506395, 0.277739, 0.215866)),
    (1010, (0.538101, 0.136805, 0.325095)),
    (1011, (0.552078, 0.178668, 0.269254)),
    (1012, (0.540735, 0.424900, 0.034366)),
    (1013, (0.592943, 0.187398, 0.219659)),
    (1014, (0.685668, 0.285069, 0.029263)),
    (1015, (0.571092, 0.379759, 0.049149)),
    (1016, (0.654867, 0.283297, 0.061836)),
    (1017, (0.508297, 0.185553, 0.306150)),
    (1018, (0.673297, 0.013299, 0.313404)),
    (1019, (0.592214, 0.097373, 0.310413)),
)


def run_episode(policy, seed, weights, use_preview=True):
    """One episode with the weights PINNED after reset, so every policy sees
    the same ruler on the same episode."""
    env = SupervisoryTunerEnv(make_grade_climb(duration=DURATION, dt=DT),
                              dt=DT, seed=seed, use_preview=use_preview)
    obs, _ = env.reset(seed=seed)
    env.w = np.asarray(weights, dtype=np.float32)   # override the fresh draw
    obs = env._obs()
    ret, peak = 0.0, 0.0
    while True:
        obs, r, term, trunc, info = env.step(policy(env, obs))
        ret += r
        peak = max(peak, info["t_turb"])
        if term or trunc:
            break
    s = info["episode_summary"]
    return dict(ret=ret, damage=s["damage"], fuel=s["fuel"],
                torque_viol=s["torque_viol"], peak_turb=peak - 273.15,
                knock=s["knock_events"])


def agent_policy(model, use_preview=True):
    """Wrap a stable-baselines3 model as a policy(env, obs) callable."""
    def p(env, obs):
        a, _ = model.predict(obs, deterministic=True)
        return a
    return p


def summarise(rows, key):
    v = np.array([r[key] for r in rows], dtype=float)
    q1, med, q3 = np.percentile(v, [25, 50, 75])
    return med, q3 - q1, v.max(), v.min()


def main():
    policies = [
        ("baseline ECU",  C.p_neutral,     True),
        ("reactive",      C.p_reactive,    True),
        ("current-grade", C.p_grade_now,   True),
    ]

    for path in sys.argv[1:]:
        try:
            from stable_baselines3 import SAC
        except ImportError:
            raise SystemExit('stable-baselines3 is not installed.\n'
                             '    pip install "stable-baselines3[extra]"')
        blind = "blind" in path
        model = SAC.load(path.rstrip("/\\") + "/final")
        policies.append((("agent (blind)" if blind else "agent") + " " + path,
                         agent_policy(model), not blind))

    print(f"PHASE D EVALUATION -- {len(EPISODES)} FIXED EPISODES, frozen 18 Sep 2026")
    print(f"scenario: 12 % at 130 km/h, 42 C, {DURATION:.0f} s, dt {DT}")
    print(f"trigger:  {TURB_PROTECT_K - 273.15:.0f} C\n")
    print(f"{'policy':<28}{'damage med':>12}{'IQR':>9}{'worst':>9}"
          f"{'fuel med':>10}{'peak C':>9}")
    print("-" * 77)

    out = {}
    for name, pol, prev in policies:
        rows = [run_episode(pol, s, w, prev) for s, w in EPISODES]
        out[name] = rows
        dm, di, dw, _ = summarise(rows, "damage")
        fm, _, _, _ = summarise(rows, "fuel")
        pk = max(r["peak_turb"] for r in rows)
        print(f"{name:<28}{dm:>12.1f}{di:>9.1f}{dw:>9.1f}{fm:>10.0f}{pk:>9.0f}")

    print("-" * 77)
    base = np.median([r["damage"] for r in out["baseline ECU"]])
    for name in out:
        if name == "baseline ECU":
            continue
        med = np.median([r["damage"] for r in out[name]])
        print(f"  {name:<26} cuts median damage {100*(1-med/base):5.1f} %")

    grade = next((n for n in out if n.startswith("current-grade")), None)
    agent = next((n for n in out if n.startswith("agent ") and "blind" not in n), None)
    blind = next((n for n in out if "blind" in n), None)

    print()
    if agent and grade:
        a = np.median([r["damage"] for r in out[agent]])
        g = np.median([r["damage"] for r in out[grade]])
        edge = 100*(1-a/base) - 100*(1-g/base)
        print(f"  AGENT over CURRENT-GRADE: {edge:+.1f} points")
    if agent and blind:
        a = np.median([r["damage"] for r in out[agent]])
        b = np.median([r["damage"] for r in out[blind]])
        print(f"  SIGHTED over BLINDED:     {100*(1-a/base) - 100*(1-b/base):+.1f} points"
              "   <- THE ABLATION. This is the project's result.")
    elif agent:
        print("  No blinded agent supplied, so THERE IS NO ABLATION YET. Train one\n"
              "  with --no-preview and pass it as the second argument. Until then\n"
              "  nothing here separates preview from the rest of the policy.")
    else:
        print("  Hand-written policies only. AUDIT.md C3: these say the environment\n"
              "  rewards anticipation; they do NOT say what an agent would gain, and\n"
              "  five scenarios have now shown preview losing to current-grade with\n"
              "  policies a human wrote. Only a trained pair settles it.")


if __name__ == "__main__":
    main()

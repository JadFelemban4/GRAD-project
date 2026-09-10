"""Does the environment actually reward anticipation?

If a hand-written policy that acts on the PREVIEW beats one that acts on the
same information too late, the premise of the whole thesis is sound and RL has
something to find. If it does not, no amount of SAC tuning will help.
"""
import numpy as np
from engine_env import (SupervisoryTunerEnv, make_grade_climb, ACT_LO, ACT_HI,
                        TURB_PROTECT_K)

NEUTRAL = (2.0 * (0.0 - ACT_LO) / (ACT_HI - ACT_LO) - 1.0).astype(np.float32)

# Protection trigger, in kelvin of turbine housing temperature.
#
# ANCHORED TO THE DAMAGE MODEL, NOT TUNED, AND NOT A PERCENTILE.
#
# It used to be the constant 930 K, chosen when this environment was
# accidentally simulating a 2.0 L four-cylinder. On the real 3.0 L six over a
# grade that actually loads it the turbine reaches 1152 K, so a 930 K trigger is
# active from the first second: both policies saturate, act identically, and the
# gap between them collapses for a reason that has nothing to do with preview.
#
# The obvious repair -- a percentile of the baseline's own trace, as
# generality_test.py's H2b table uses -- does not transfer here. That rule
# assumes the temperature spends a minority of the episode near its peak. This
# scenario is a sustained climb: nine of its twelve minutes sit at the top, so
# the 80th percentile lands ON the peak and the trigger never fires.
#
# So the trigger comes from the physics instead. The damage model in
# engine_env.step is
#
#     exp((t_turb - 1123) / 45)
#
# and 1123 K is where the turbine term reaches unity -- the knee above which
# damage stops being negligible and starts compounding. Protecting from there is
# a statement about the component, not about this episode, and it transfers to
# any scenario without being re-derived.
#
# The constant lives in engine_env next to the damage model it comes from, and
# generality_test.py imports the same one, so the two experiments cannot drift.
TRIGGER_K = TURB_PROTECT_K


def to_norm(trims):
    return (2.0 * (np.asarray(trims, np.float32) - ACT_LO) / (ACT_HI - ACT_LO) - 1.0
            ).astype(np.float32)


def rollout(policy, use_preview=True, seed=0, w=None):
    env = SupervisoryTunerEnv(make_grade_climb(duration=720.0, dt=1.0), dt=1.0,
                              seed=seed, use_preview=use_preview)
    obs, _ = env.reset(seed=seed)
    if w is not None:
        env.w = np.asarray(w, np.float32)
        obs = env._obs()
    peak_turb, peak_oil = 0.0, 0.0
    while True:
        obs, r, term, trunc, info = env.step(policy(env, obs))
        peak_turb = max(peak_turb, info["t_turb"])
        peak_oil = max(peak_oil, info["t_oil"])
        if term or trunc:
            break
    s = info["episode_summary"]
    return dict(fuel=s["fuel"], fuel_base=s["fuel_base"],
                damage=s["damage"], damage_base=s["damage_base"],
                peak_turb=peak_turb - 273.15, peak_oil=peak_oil - 273.15,
                knock=s["knock_events"])


def p_neutral(env, obs):
    return NEUTRAL


def p_reactive(env, obs):
    """Acts only on the turbine temperature it can already measure."""
    over = env.thermal.t_turb - TRIGGER_K
    if over <= 0:
        return NEUTRAL
    k = float(np.clip(over / 25.0, 0.0, 1.0))
    return to_norm([0.0, -0.10 * k, -18.0 * k, k, 1.0])


def p_predictive(env, obs):
    """Same levers, but triggered by the +15 s and +30 s gradient preview."""
    ahead = max(env._preview()[2], env._preview()[3])
    over = env.thermal.t_turb - TRIGGER_K
    k_now = float(np.clip(over / 25.0, 0.0, 1.0))
    k_ahead = float(np.clip(ahead / 0.08, 0.0, 1.0)) if ahead > 0.02 else 0.0
    k = max(k_now, 0.55 * k_ahead)
    if k <= 0:
        return NEUTRAL
    return to_norm([0.0, -0.10 * k, -18.0 * k, k, 1.0])


if __name__ == "__main__":
    print(f"protection trigger: {TRIGGER_K:.0f} K ({TRIGGER_K - 273.15:.0f} C) "
          f"= the knee of the turbine damage term\n")
    rows = [("baseline ECU (neutral trims)", p_neutral, True),
            ("reactive protection", p_reactive, True),
            ("predictive protection", p_predictive, True),
            ("predictive, preview disabled", p_predictive, False)]
    print(f"{'policy':<32}{'fuel g':>9}{'damage':>10}{'peak turb C':>13}{'peak oil C':>12}")
    print("-" * 76)
    base = None
    for name, pol, prev in rows:
        r = rollout(pol, use_preview=prev)
        if base is None:
            base = r
        print(f"{name:<32}{r['fuel']:>9.0f}{r['damage']:>10.1f}"
              f"{r['peak_turb']:>13.0f}{r['peak_oil']:>12.0f}")
    print("-" * 76)

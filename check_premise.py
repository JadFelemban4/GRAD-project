"""Does the environment actually reward anticipation?

If a hand-written policy that acts on the PREVIEW beats one that acts on the
same information too late, the premise of the whole thesis is sound and RL has
something to find. If it does not, no amount of SAC tuning will help.
"""
import numpy as np
from engine_env import (SupervisoryTunerEnv, make_grade_climb, ACT_LO, ACT_HI,
                        TURB_PROTECT_K, neutral_action)

# AUDIT.md C1, 15 September 2026. This file used to define its own
#
#     NEUTRAL = 2*(0 - ACT_LO)/(ACT_HI - ACT_LO) - 1
#
# which maps ALL FIVE actions to "zero" -- and actions 3 and 4 are not trims,
# they are absolute duties. Zero means the COOLING FAN OFF and the coolant pump
# at its 0.3 floor, and the pump term came out at -1.857, outside the action
# space the env declares. `engine_env.neutral_action()` was written to fix
# exactly this (mistake 10) and this file never called it.
#
# So every preview figure in the repository was measured against a baseline
# with its cooling switched off, while the protection policies switched the
# pump back to 1.0 whenever they acted -- crediting them with cooling the
# baseline row never had. Import the one definition instead.
NEUTRAL = neutral_action()

# The fan and pump duties a protecting policy may command. Never BELOW neutral:
# a policy that "protects" by cooling less than the baseline is not protecting.
NEUTRAL_FAN = float(ACT_LO[3] + (NEUTRAL[3] + 1.0) * 0.5 * (ACT_HI[3] - ACT_LO[3]))
NEUTRAL_PUMP = float(ACT_LO[4] + (NEUTRAL[4] + 1.0) * 0.5 * (ACT_HI[4] - ACT_LO[4]))

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


def _protect(k):
    """The protection action at depth k. ONE lever set, used by every policy.

    AUDIT.md C1: the fan and pump are clamped at their NEUTRAL values from
    below. They used to be commanded as `k` and `1.0`, so at small k a
    "protecting" policy ran LESS cooling than the baseline.
    """
    if k <= 0:
        return NEUTRAL
    fan = max(NEUTRAL_FAN, k)
    pump = max(NEUTRAL_PUMP, 1.0)
    return to_norm([0.0, -0.10 * k, -18.0 * k, fan, pump])


def p_neutral(env, obs):
    return NEUTRAL


def p_reactive(env, obs):
    """Acts only on the turbine temperature it can already measure.

    AUDIT.md C3. This used to saturate at k = 0.36 while `p_predictive` held
    k >= 0.55, so the two policies differed in HOW HARD THEY PROTECTED as well
    as in when -- and the headline gap was being read as a preview effect. The
    depth is now the same on both, so the only remaining difference is timing,
    which is what the experiment is supposed to be about.
    """
    over = env.thermal.t_turb - TRIGGER_K
    if over <= 0:
        return NEUTRAL
    return _protect(float(np.clip(over / 25.0, 0.0, 1.0)))


def p_grade_now(env, obs):
    """A THIRD baseline: acts on the grade it is on RIGHT NOW, with no preview.

    AUDIT.md C3 asked for this and it is the most useful row in the table.
    A policy that keys on the current road gradient -- information every car
    already has from a nose-down accelerometer -- lands within 0.1 points of
    the predictive policy. That is the honest comparator for "is PREVIEW worth
    acquiring", because it is what you get without buying any.
    """
    grade_now = float(env.cycle["grade"][min(env.k, len(env.cycle["grade"]) - 1)])
    over = env.thermal.t_turb - TRIGGER_K
    k_now = float(np.clip(over / 25.0, 0.0, 1.0))
    k_grade = float(np.clip(grade_now / 0.08, 0.0, 1.0)) if grade_now > 0.02 else 0.0
    return _protect(max(k_now, 0.55 * k_grade))


def p_predictive(env, obs):
    """Same levers and the same depth, triggered by the +15 s / +30 s preview."""
    ahead = max(env._preview()[2], env._preview()[3])
    over = env.thermal.t_turb - TRIGGER_K
    k_now = float(np.clip(over / 25.0, 0.0, 1.0))
    k_ahead = float(np.clip(ahead / 0.08, 0.0, 1.0)) if ahead > 0.02 else 0.0
    return _protect(max(k_now, 0.55 * k_ahead))


if __name__ == "__main__":
    print(f"protection trigger: {TRIGGER_K:.0f} K ({TRIGGER_K - 273.15:.0f} C) "
          f"= the knee of the turbine damage term\n")
    rows = [("baseline ECU (true neutral)", p_neutral, True),
            ("reactive protection", p_reactive, True),
            ("current-grade protection", p_grade_now, True),
            ("predictive protection", p_predictive, True),
            ("predictive, preview disabled", p_predictive, False)]
    print(f"{'policy':<32}{'fuel g':>9}{'damage':>10}{'peak turb C':>13}{'peak oil C':>12}")
    print("-" * 76)
    out = {}
    for name, pol, prev in rows:
        r = rollout(pol, use_preview=prev)
        out[name] = r
        print(f"{name:<32}{r['fuel']:>9.0f}{r['damage']:>10.1f}"
              f"{r['peak_turb']:>13.0f}{r['peak_oil']:>12.0f}")
    print("-" * 76)

    b = out["baseline ECU (true neutral)"]["damage"]
    for name in ("reactive protection", "current-grade protection",
                 "predictive protection"):
        d = out[name]["damage"]
        print(f"  {name:<30} cuts damage {100.0 * (1.0 - d / b):5.1f} %")
    gap = (100.0 * (1.0 - out["predictive protection"]["damage"] / b)
           - 100.0 * (1.0 - out["reactive protection"]["damage"] / b))
    grade_gap = (100.0 * (1.0 - out["predictive protection"]["damage"] / b)
                 - 100.0 * (1.0 - out["current-grade protection"]["damage"] / b))
    print(f"\n  preview over reactive      {gap:+5.1f} points")
    print(f"  preview over current grade {grade_gap:+5.1f} points   <- THE HONEST ONE")

    # AUDIT.md C2. Say it loudly rather than letting a reader infer it from a
    # small number: if the baseline never reaches the trigger, this experiment
    # is not measuring protection at all.
    peak_b = out["baseline ECU (true neutral)"]["peak_turb"]
    if peak_b < TRIGGER_K - 273.15:
        print(f"""
  *** THE CONSTRAINT DOES NOT BIND ON THIS SCENARIO ***
  The baseline peaks at {peak_b:.0f} C against a {TRIGGER_K - 273.15:.0f} C trigger, so the reactive
  policy never acts and its row is the baseline row. Until the scenario is
  re-chosen so the trigger is reached FOR A PHYSICAL REASON, no number in this
  table is a measurement of preview value.

  It used to bind, and it bound for the wrong reason: the baseline ECU was
  scheduled on an open-loop guess at manifold pressure -- 224 kPa where the
  engine actually ran 175 -- so it commanded knock-limited spark for a load it
  was not at and cooked the turbine with ~10 degrees of phantom retard. The
  879 C peak the documents quote was that error, not the engine.

  CHOOSE THE NEW SCENARIO FROM SOMETHING PHYSICAL -- a real grade, a published
  towing duty cycle, a measured ambient -- and NOT by turning a knob until the
  gap looks good. That is mistake 12 waiting to happen to Phase D.""")

    print("""
READ THIS BEFORE QUOTING ANY OF IT.  (AUDIT.md C1 and C3)

1. These policies are HAND-WRITTEN, not trained. They say the environment
   rewards anticipation; they do not say how much an agent would gain.

2. The three protecting rows now use the SAME protection DEPTH, so the only
   difference between reactive and predictive is TIMING. Until 16 September
   the reactive policy saturated at k = 0.36 while predictive held k >= 0.55,
   and the gap between them was partly just protecting harder.

3. "Predictive, preview disabled" equals "reactive" BY CONSTRUCTION, not as a
   finding. With use_preview=False the preview term is literally zero, so
   p_predictive returns p_reactive's vector on every step. The identity CANNOT
   fail and it is not evidence. It becomes a real ablation only when a TRAINED
   blinded agent is compared with a trained sighted one -- that is Phase D.

4. The row that matters is CURRENT-GRADE PROTECTION. It uses no preview at all,
   only the gradient the car is on now, which any vehicle can measure. If
   preview beats it by little, then preview is not worth acquiring HERE -- and
   that is a result about this operating point, which is what H/tau is for.""")

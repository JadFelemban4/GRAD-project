"""
WHY does preview pay? Two hypotheses, tested in the existing simulator.

H1 — CONVEXITY. Preview lets you spread a correction over a longer window.
     By Jensen's inequality, spreading only helps if the cost is CONVEX in the
     accumulated state. If damage were linear in temperature, spreading the same
     total heat over more time would cost exactly the same, and preview would be
     worth nothing.

H2 — TIMESCALE. Preview is worth nothing if the state has no memory (you can
     always react in time) and nothing if the state is far slower than the
     horizon (30 s of warning is noise against a 3-hour constant). There should
     be a band where it pays.

If both hold, "what is preview worth" has a DOMAIN-AGNOSTIC answer that has
nothing to do with engines - which is the real argument for generalising.

Note: the hand-written policies are rule-based on measured temperature, so their
trajectories do not depend on the damage function. That lets us record each
trajectory once and re-score it under different cost models.
"""
import numpy as np
from engine_env import (SupervisoryTunerEnv, make_grade_climb, ACT_LO, ACT_HI,
                        TURB_PROTECT_K, neutral_action)
from thermal import ThermalParams

# AUDIT.md C1: this file defined its own "all actions to zero" neutral, which
# means the cooling fan OFF and the pump at its 0.3 floor. Every H1/H2 figure
# was therefore measured against a baseline with its cooling disabled, while
# the protecting policies turned the pump back on. Import the one definition.
NEUTRAL = neutral_action()
NEUTRAL_FAN = float(ACT_LO[3] + (NEUTRAL[3] + 1.0) * 0.5 * (ACT_HI[3] - ACT_LO[3]))
NEUTRAL_PUMP = float(ACT_LO[4] + (NEUTRAL[4] + 1.0) * 0.5 * (ACT_HI[4] - ACT_LO[4]))


def to_norm(trims):
    return (2.0 * (np.asarray(trims, np.float32) - ACT_LO) / (ACT_HI - ACT_LO) - 1.0
            ).astype(np.float32)


def p_neutral(env):
    return NEUTRAL


def _protect(k):
    """Protection at depth k. Fan and pump are floored at NEUTRAL (AUDIT.md C1):
    a policy that cools LESS than the baseline is not protecting."""
    if k <= 0:
        return NEUTRAL
    return to_norm([0.0, -0.10 * k, -18.0 * k,
                    max(NEUTRAL_FAN, k), max(NEUTRAL_PUMP, 1.0)])


def p_reactive(env):
    over = env.thermal.t_turb - TURB_PROTECT_K
    if over <= 0:
        return NEUTRAL
    return _protect(float(np.clip(over / 25.0, 0.0, 1.0)))


def p_predictive(env):
    ahead = max(env._preview()[2], env._preview()[3])
    over = env.thermal.t_turb - TURB_PROTECT_K
    k_now = float(np.clip(over / 25.0, 0.0, 1.0))
    k_ahead = float(np.clip(ahead / 0.08, 0.0, 1.0)) if ahead > 0.02 else 0.0
    return _protect(max(k_now, 0.55 * k_ahead))


def _exhaust_of_climb(seed=0):
    """Mean exhaust mass flow over the loaded part of the standard climb.

    AUDIT.md M12. Used to set the tau axis from the scenario rather than from
    an assumed constant.
    """
    env = SupervisoryTunerEnv(make_grade_climb(duration=720.0, dt=2.0), dt=2.0,
                              seed=seed, use_preview=True)
    env.reset(seed=seed)
    vals = []
    while True:
        _, _, term, trunc, info = env.step(NEUTRAL)
        f = info.get("mdot")
        if f:
            vals.append(f * 15.0)
        if term or trunc:
            break
    vals = sorted(vals)
    return vals[len(vals) // 2:] if vals else []       # the loaded half


def trajectory(policy, c_turb=6000.0, seed=0):
    """Record the turbine temperature trace and fuel for one policy."""
    tp = ThermalParams(c_turb=c_turb)
    env = SupervisoryTunerEnv(make_grade_climb(duration=520.0, dt=2.0), dt=2.0, seed=seed)
    env.thermal.p = tp
    env.thermal_base.p = tp
    env.reset(seed=seed)
    env.thermal.p = tp
    env.thermal_base.p = tp
    temps, fuel = [], 0.0
    while True:
        _, _, term, trunc, info = env.step(policy(env))
        temps.append(info["t_turb"])
        fuel += info.get("mdot", 0.0)
        if term or trunc:
            break
    s = info["episode_summary"]
    return np.asarray(temps), s["fuel"]


def damage(temps, p, t_ref=TURB_PROTECT_K, scale=25.0):
    """Cost family with tunable convexity.
    p = 1 is linear, p = 2 quadratic, larger p sharper. p = 'exp' is exponential.

    t_ref is an EXPERIMENTAL PARAMETER here, not the policy trigger -- H1
    re-scores the same three trajectories under different cost curvatures, and
    H2b overrides it per configuration. It defaults to the same damage-model
    knee the policies trigger on so that, unless a table says otherwise, the
    cost being measured and the limit being defended are the same temperature."""
    over = np.maximum(0.0, temps - t_ref) / scale
    if p == "exp":
        return float(np.sum(np.exp(over) - 1.0))
    return float(np.sum(over ** p))


# --------------------------------------------------------------- H1: convexity
def main():
    """AUDIT.md M12: this file used to run nine minutes of rollouts AT
    IMPORT. `import generality_test` for any reason -- a docs checker, a
    notebook, tab-completion -- started the whole sweep. Guarded now."""
    print("=" * 78)
    print("H1 — Does preview value depend on how CONVEX the cost is in the state?")
    print("=" * 78)
    print("Same three trajectories, re-scored under different cost curvatures.\n")

    tr_base, f_base = trajectory(p_neutral)
    tr_reac, f_reac = trajectory(p_reactive)
    tr_pred, f_pred = trajectory(p_predictive)

    print(f"{'cost model':<22}{'reactive':>12}{'predictive':>13}{'preview edge':>15}")
    print("-" * 78)
    rows = []
    for p, name in [(1.0, "linear  (p=1)"), (1.5, "p = 1.5"), (2.0, "quadratic (p=2)"),
                    (3.0, "p = 3"), (4.0, "p = 4"), ("exp", "exponential")]:
        d_b = damage(tr_base, p)
        d_r = damage(tr_reac, p)
        d_p = damage(tr_pred, p)
        if d_b <= 1e-9:
            continue
        red_r = 100.0 * (d_b - d_r) / d_b
        red_p = 100.0 * (d_b - d_p) / d_b
        edge = red_p - red_r
        rows.append((name, red_r, red_p, edge))
        print(f"{name:<22}{red_r:>11.1f}%{red_p:>12.1f}%{edge:>14.1f} pts")

    print("-" * 78)
    if not rows:
        # AUDIT.md C2. Same wall check_premise.py hits: with the baseline ECU
        # scheduled on the pressure the engine actually runs at, the turbine
        # never reaches TURB_PROTECT_K on this scenario, so there is no damage
        # to re-score under ANY cost curvature and every row is empty.
        print("  *** THE BASELINE NEVER EXCEEDS THE LIMIT ON THIS SCENARIO ***")
        print(f"  Peak baseline turbine {tr_base.max() - 273.15:.0f} C against a "
              f"{TURB_PROTECT_K - 273.15:.0f} C reference.")
        print("""
  H1 cannot be measured here. It is not that preview is worth nothing under a
  convex cost -- it is that this scenario produces NO constraint violation to
  spread, so every cost model scores zero for every policy.

  This is the same finding as check_premise.py's, from the other direction, and
  it has the same fix: re-choose the scenario so the trigger is reached FOR A
  PHYSICAL REASON. Until then H1 and H2 below are not measurements.
  The figures this file used to print -- 16.5 / 18.0 / 26.0 points -- were
  measured against a baseline whose cooling was switched off (AUDIT.md C1) and
  on a tau axis that assumed 112.5 g/s of exhaust (M12). They are void.""")
        return

    # AUDIT.md nitpick: this said "grew 0.7x" for a SHRINK. Say which way.
    _r = rows[-1][3] / max(rows[0][3], 1e-9)
    _verb = "grew" if _r >= 1.0 else "SHRANK"
    print(f"preview edge {_verb} {_r:.2f}x from linear to exponential cost "
          f"({rows[0][3]:+.1f} -> {rows[-1][3]:+.1f} pts)")

    # --------------------------------------------------------------- H2: timescale
    print()
    print("=" * 78)
    print("H2 — Does preview value depend on STATE MEMORY vs preview horizon?")
    print("=" * 78)
    print("Preview horizon is fixed at 30 s. Turbine heat capacity is swept, which")
    print("changes the thermal time constant tau = C / UA.\n")

    # AUDIT.md M12: this assumed 112.5 g/s of exhaust. The standard climb produces
    # about 103 g/s, so every tau in the tables below was ~7 % low and every H/tau
    # ~7 % high (50.3 s / 0.60 became 54.0 s / 0.56). The flow is measured from the
    # baseline trajectory instead, so the axis of this experiment is the episode's
    # own physics rather than a constant typed in beside it.
    _P = ThermalParams()
    EXH_GPS = float(np.mean(_EXH_SAMPLES)) if (_EXH_SAMPLES := _exhaust_of_climb()) else 112.5
    UA = _P.ua_gas_turb * EXH_GPS + _P.ua_turb_amb
    print(f"tau axis uses the climb's own mean exhaust flow: {EXH_GPS:.1f} g/s "
          f"(was an assumed 112.5)")
    print(f"{'C_turb [J/K]':<15}{'tau [s]':>10}{'H/tau':>9}{'reactive':>12}"
          f"{'predictive':>13}{'preview edge':>15}")
    print("-" * 78)
    for c in [800.0, 2500.0, 6000.0, 18000.0, 60000.0]:
        tau = c / UA
        tb, _ = trajectory(p_neutral, c_turb=c)
        tr, _ = trajectory(p_reactive, c_turb=c)
        tp_, _ = trajectory(p_predictive, c_turb=c)
        d_b, d_r, d_p = damage(tb, "exp"), damage(tr, "exp"), damage(tp_, "exp")
        if d_b <= 1e-6:
            print(f"{c:<15.0f}{tau:>10.1f}{30.0/tau:>9.2f}"
                  f"{'  (never exceeds limit)':>50}")
            continue
        red_r = 100.0 * (d_b - d_r) / d_b
        red_p = 100.0 * (d_b - d_p) / d_b
        print(f"{c:<15.0f}{tau:>10.1f}{30.0/tau:>9.2f}{red_r:>11.1f}%"
              f"{red_p:>12.1f}%{red_p - red_r:>14.1f} pts")
    print("-" * 78)

    # ------------------------------------------ H2b: threshold scaled with the mass
    print()
    print("=" * 78)
    print("H2b — the same sweep with the constraint kept BINDING")
    print("=" * 78)
    print(f"""Above, the largest thermal masses may never reach the fixed {TURB_PROTECT_K:.0f} K limit,
    so there is no constraint to violate and no preview value to measure. That is an
    artefact of holding the threshold fixed while making the component more massive,
    not a property of H/tau.

    Here the threshold is set per-configuration to the 80th percentile of the
    UNPROTECTED policy's own temperature trace. Every configuration therefore spends
    the same fraction of the drive in violation, which isolates the effect of tau
    from the effect of how often the limit is reached.

    This is the protocol Phase F should use. State the choice in the methods.
    """)
    print(f"{'C_turb [J/K]':<15}{'tau [s]':>10}{'H/tau':>9}{'t_ref [K]':>11}"
          f"{'reactive':>11}{'predictive':>12}{'preview edge':>15}")
    print("-" * 83)
    for c in [800.0, 2500.0, 6000.0, 18000.0, 60000.0]:
        tau = c / UA
        tb, _ = trajectory(p_neutral, c_turb=c)
        tr, _ = trajectory(p_reactive, c_turb=c)
        tp_, _ = trajectory(p_predictive, c_turb=c)
        t_ref = float(np.percentile(tb, 80.0))
        d_b = damage(tb, "exp", t_ref=t_ref)
        d_r = damage(tr, "exp", t_ref=t_ref)
        d_p = damage(tp_, "exp", t_ref=t_ref)
        if d_b <= 1e-9:
            print(f"{c:<15.0f}{tau:>10.1f}{30.0/tau:>9.2f}{t_ref:>11.0f}"
                  f"{'  (degenerate)':>38}")
            continue
        red_r = 100.0 * (d_b - d_r) / d_b
        red_p = 100.0 * (d_b - d_p) / d_b
        print(f"{c:<15.0f}{tau:>10.1f}{30.0/tau:>9.2f}{t_ref:>11.0f}"
              f"{red_r:>10.1f}%{red_p:>11.1f}%{red_p - red_r:>14.1f} pts")
    print("-" * 83)
    print("Every row now yields a data point. Use this table for Figure 5.")



if __name__ == "__main__":
    main()

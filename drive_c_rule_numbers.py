"""drive_c_rule_numbers.py -- the numbers drive C's PROPOSED decision rule rests on.

    python drive_c_rule_numbers.py            -> prints, and writes results/DRIVE_C_RULE_NUMBERS.txt

Written 19 October 2026 for results/DRIVE_C_RULE.md (decisions 14-23 of
results/VALIDATION_DECISIONS.md). It reads NO drive C log and computes no
ignition retard on any log: the rule is fixed blind, before its analysis runs.

1. C2's verdict cuts. Each valid load step either shows a pull or not. A car
   that never pulls timing still shows some (channel jitter, rate q per step);
   a car that pulls on every step still misses some (the logged actual angle is
   the cylinder being computed, so a one-cylinder retard shows on about one
   reading in six: miss rate m per step). Steps driven on one stretch in one
   heat soak are alike, so they are treated as blocks of 7 with an intra-block
   correlation (ICC) of 0.1: a beta-binomial per block, convolved. The cuts:
   "pulls" needs a count a never-pulling car reaches at most 5 % of the time;
   "does not" needs a count a car pulling on 60 % of steps reaches at most 5 %
   of the time. Design values q 0.075 (six late-window readings at the 1.3 %
   per-reading jitter of steady light cruise) and m 0.45 (one retarded cylinder
   of six, four to five readings). The rule computes the cuts AT FREEZE from the
   real block sizes with this same function; the table here is for planning.

2. The spark requirement. results/VALIDATION_PLAN.md's R1 is 10 K of turbine,
   about x1.25 of damage. A model error in the boosted spark SCHEDULE moves every
   car, the baseline included, so the like-for-like test shifts
   BaselineECU.base_spark by delta at >= 140 kPa for every car, in this process
   only, on the locked climb with the baseline (neutral action).

3. The knee. damage_rate's knock term is 40*max(0, KI - knee)^2 per second
   (engine_env.damage_rate, knee 0.85). From the same baseline run's knock
   integral, the knock damage and its share of all damage at other knees.
"""
import concurrent.futures as cf
import os
import sys

import numpy as np
from scipy.stats import betabinom, binom

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "DRIVE_C_RULE_NUMBERS.txt")
BLOCK, ICC, ALPHA = 7, 0.10, 0.05
Q_DESIGN, M_DESIGN = 0.075, 0.45
SPARK_DELTAS = (-0.85, 0.0, 0.85)
KNEES = (0.65, 0.75, 0.85, 0.95, 1.00)


# ---- 1. the C2 cuts -----------------------------------------------------------
def block_pmf(n, p, icc=ICC):
    if icc <= 0 or p <= 0 or p >= 1:
        return binom.pmf(np.arange(n + 1), n, p)
    s = 1.0 / icc - 1.0
    return betabinom.pmf(np.arange(n + 1), n, p * s, (1 - p) * s)


def pmf_k(blocks, p, icc=ICC):
    """The distribution of K, the number of pulling steps, over blocks of the given sizes."""
    out = np.array([1.0])
    for b in blocks:
        out = np.convolve(out, block_pmf(b, p, icc))
    return out


def p_step(pi, q, m):
    """Chance that one valid step reads as a pull, for a car pulling on a share pi of steps."""
    seen = pi * (1 - m)
    return seen + (1 - seen) * q


def blocks_of(n, block=BLOCK):
    return [block] * (n // block) + ([n % block] if n % block else [])


def cuts(blocks, q=Q_DESIGN, m=M_DESIGN, icc=ICC, alpha=ALPHA):
    """(k_yes, k_no, false 'pulls', false 'does not') for the realised block sizes."""
    n = sum(blocks)
    sf0 = np.cumsum(pmf_k(blocks, p_step(0.0, q, m), icc)[::-1])[::-1]     # P(K >= k | never pulls)
    cdf6 = np.cumsum(pmf_k(blocks, p_step(0.6, q, m), icc))                # P(K <= k | pulls on 60 %)
    k_yes = next(k for k in range(n + 1) if sf0[k] <= alpha)
    ok = [k for k in range(n + 1) if cdf6[k] <= alpha]
    k_no = max(ok) if ok else -1
    return k_yes, k_no, float(sf0[k_yes]), float(cdf6[k_no]) if k_no >= 0 else 0.0


def part1(say):
    say("1. C2 VERDICT CUTS (blocks of 7, ICC 0.1; design q 0.075, m 0.45; both errors <= 5 %)")
    say(f"   {'valid steps N':>13s}  {'pulls if K >=':>13s}  {'does not if K <=':>16s}  {'false pulls':>11s}  {'false does-not':>14s}")
    for n in (16, 18, 20, 22, 24, 26, 28, 30, 32, 35):
        ky, kn, a, b = cuts(blocks_of(n))
        say(f"   {n:13d}  {ky:13d}  {kn:16d}  {100*a:10.1f} %  {100*b:13.1f} %")
    ky, kn, _, _ = cuts(blocks_of(24))
    say(f"\n   N 24, cuts >= {ky} / <= {kn}: chance of each verdict by the car's true pull rate")
    say(f"   {'true rate':>9s}  {'pulls':>7s}  {'inconclusive':>12s}  {'does not':>8s}")
    for pi in (0.0, 0.1, 0.2, 0.3, 0.4, 0.6, 0.8):
        f = pmf_k(blocks_of(24), p_step(pi, Q_DESIGN, M_DESIGN))
        say(f"   {pi:9.1f}  {100*f[ky:].sum():6.1f} %  {100*f[kn+1:ky].sum():11.1f} %  {100*f[:kn+1].sum():7.1f} %")
    say("\n   sensitivity at N 24 (cuts held): false 'does not' for a 60 % puller if m is")
    say("   (0.20 = two cylinders retarded; 0.45 = one of six, four to five readings; 0.58 = one, three readings)")
    for m in (0.20, 0.45, 0.58):
        f = pmf_k(blocks_of(24), p_step(0.6, Q_DESIGN, m))
        say(f"     m {m:.2f}: {100*f[:kn+1].sum():.1f} %")
    say("   false 'pulls' for a never-pulling car if q is (the sham windows measure q on the day)")
    for q in (0.05, 0.075, 0.10, 0.15):
        f = pmf_k(blocks_of(24), p_step(0.0, q, M_DESIGN))
        say(f"     q {q:.3f}: {100*f[ky:].sum():.1f} %")
    say("   one block of 24 instead of blocks of 7 (no break between steps): cuts "
        + "{} / {}".format(*cuts([24])[:2]))


# ---- 2 and 3. the spark schedule shift and the knee, on the locked climb ---------
def climb(delta):
    os.chdir(HERE)
    sys.path.insert(0, HERE)
    import engine_env as E
    orig = E.BaselineECU.base_spark

    def shifted(self, rpm, map_kpa):
        d = delta if map_kpa >= 140.0 else 0.0
        return float(np.clip(orig(self, rpm, map_kpa) + d, self.SPARK_MIN, self.SPARK_MAX))
    E.BaselineECU.base_spark = shifted
    env = E.SupervisoryTunerEnv(E.make_grade_climb(duration=720.0, dt=1.0), dt=1.0, seed=0)
    env.reset(seed=0)
    a = np.array(E.neutral_action(), dtype=np.float32)
    peak, ki, tt, to = 0.0, [], [], []
    while True:
        _, _, term, trunc, info = env.step(a)
        peak = max(peak, info["t_turb"])
        ki.append(float(info["ki"]))
        tt.append(float(info["t_turb"]))
        to.append(float(info["t_oil"]))
        if term or trunc:
            break
    s = info["episode_summary"]
    return delta, dict(peak_c=peak - 273.15, damage=float(s["damage"]), ki=np.array(ki),
                       t_turb=np.array(tt), t_oil=np.array(to), dt=float(env.dt))


def part23(say):
    import engine_env as E
    with cf.ProcessPoolExecutor(max_workers=3, max_tasks_per_child=1) as pool:
        res = dict(pool.map(climb, SPARK_DELTAS))
    base = res[0.0]
    say("\n2. THE SPARK REQUIREMENT: the boosted schedule (>= 140 kPa) shifted for every car,")
    say("   locked climb, baseline ECU (neutral action)")
    for d in SPARK_DELTAS:
        r = res[d]
        say(f"   shift {d:+.2f} deg: peak turbine {r['peak_c']:.2f} C ({r['peak_c'] - base['peak_c']:+.2f} K), "
            f"damage {r['damage']:.1f} (x{r['damage'] / base['damage']:.3f})")
    say("   R1 is 10 K / x1.25 of damage (results/VALIDATION_PLAN.md section 4): about 0.85 deg of schedule.")

    say("\n3. THE KNEE: knock damage on the same baseline run, at other knees")
    thermal = sum(E.damage_rate(t, o) for t, o in zip(base["t_turb"], base["t_oil"])) * base["dt"]
    k85 = float(np.sum(40.0 * np.maximum(0.0, base["ki"] - 0.85) ** 2) * base["dt"])
    say(f"   climb knock integral: median {np.median(base['ki'][180:]):.3f} on the climb, max {base['ki'].max():.3f}")
    for kn in KNEES:
        k = float(np.sum(40.0 * np.maximum(0.0, base["ki"] - kn) ** 2) * base["dt"])
        say(f"   knee {kn:.2f}: knock damage {k:7.2f} (x{k / k85:.2f} of the 0.85 value), "
            f"{100 * k / (thermal + k):5.2f} % of the run's damage")
    say("   On the locked climb the knock term is the one-step spike plus little else; what a knee")
    say("   shift moves is mainly the knock cost the agents meet in ordinary driving (results/X2_AGENTS.md).")


def part4(say):
    """The model's charge temperature has no boost or heat-soak term, and the boosted
    inversion runs +1.9 % high against the car (plant.charge_temperature's docstring).
    Read as a temperature error, 1.9 % of ~330 K is ~6.3 K, and it reaches both C1 rows
    by two paths: the inverted MAP, and the IAT compensation (spark row) or the knock
    integral at fixed spark (knee row). Treated as a uniform bound: u = shift / sqrt(3)."""
    from scipy.optimize import brentq
    import plant
    from engine_env import BaselineECU
    ecu, t_cool, rpm, d_t = BaselineECU(), 273.15 + 90.0, 2706.0, 6.3
    say("\n4. INPUT UNCERTAINTY FROM THE CHARGE TEMPERATURE (+6.3 K, the +1.9 % boosted-MAP gap), at the")
    say("   climb's cell (2706 rpm, 175 kPa, coolant 90 C)")
    for amb in (25.0, 42.0):
        tch = plant.charge_temperature(273.15 + amb, t_cool)
        mdot = brentq(lambda m: plant.map_from_airflow(m, rpm, tch) - 175.0, 20, 300)
        sp = ecu.base_spark(rpm, 175.0) + ecu.iat_compensation(tch)
        ki = plant.predict(rpm, 175.0, tch, t_cool, sp, 1.0)["knock_integral"]
        map_t = plant.map_from_airflow(mdot, rpm, tch + d_t)
        d_map = ecu.base_spark(rpm, map_t) - ecu.base_spark(rpm, 175.0)
        d_iat = ecu.iat_compensation(tch + d_t) - ecu.iat_compensation(tch)
        d_ki = plant.predict(rpm, map_t, tch + d_t, t_cool, sp, 1.0)["knock_integral"] - ki
        say(f"   ambient {amb:.0f} C: spark {d_map:+.2f} deg via the MAP + {d_iat:+.2f} via the IAT compensation "
            f"= {d_map + d_iat:+.2f} deg -> u_input {abs(d_map + d_iat) / np.sqrt(3):.2f} deg; "
            f"knock integral at fixed spark {d_ki:+.3f} -> u_input {abs(d_ki) / np.sqrt(3):.3f} KI")


def main():
    lines = []

    def say(s=""):
        print(s, flush=True)
        lines.append(s)
    say("DRIVE C RULE NUMBERS -- for results/DRIVE_C_RULE.md (python drive_c_rule_numbers.py)")
    say("No drive C log is read and no ignition retard is computed on any log.\n")
    part1(say)
    part23(say)
    part4(say)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\nwrote {os.path.relpath(OUT, HERE)}")


if __name__ == "__main__":
    main()

"""preview_ceiling.py -- the most ANY use of the preview could save on the scored climb.

    python preview_ceiling.py                 prints the bound, writes results/preview_ceiling.txt
    python preview_ceiling.py --no-write      prints only

Asked by Ghassan, 21 October 2026: why did no trained agent ever show preview helping?
This measures the size of the prize before asking whether an agent found it. Decision 34
(results/VALIDATION_DECISIONS.md) uses it to choose the four-engine test's roads: test
only where the ceiling is at least twice the MEI (5.43 points of cut). Written from the
scratch calculations of that day's diagnosis (why/preview_bound/a1, a2, a5 and a9) so
that the sentence "about 0.3 points" has a committed run behind it (mistake 22).

INPUTS, AND ONLY THESE. results/traces_130kmh.json (run_results.py at cbb8d09: the
merged plant of 30 September, the grade a STEP at t = 180 s, the thermal network one
explicit-Euler step per 1 s) and results/premise.json (the 8 October plant's baseline, to
restate the points on it). No plant run. The B58's constants come from
engines.get("b58"); its housing, damage and ambient values are the ones the traces were
made with (thermal.py and engine_env.py at cbb8d09 hold the same numbers).

WHY A HEAD START IS ALL PREVIEW CAN ADD HERE. The scored road is flat until 180 s, then
12 % to the end of the 720 s episode. The preview looks 2/5/15/30 s ahead, its index
clips at the last sample, and every agent also sees the grade it is on, so from the
moment the climb is under the car every preview channel equals what the blinded agent
already knows. Before t = 150 s every channel reads 0. Preview's whole value is the state
an agent can build in those 30 s, and the only state a lever moves ahead of the climb is
the housing temperature (the housing is heated by exhaust gas only; fan and pump already
run at 1.0 in neutral; spark can only retard, which heats the exhaust; enrichment heats
the oil). So the bound is: how much turbine damage does a cooler housing at t = 180 s
save, if the difference then decays with the reference run's own time constant? For this
node that decay is exact: c dT/dt = ua_gt (EGT - T) - ua_amb (T - T_amb) is linear in T,
and EGT and exhaust flow do not depend on T. Section F checks it on the one head start
the traces contain (the hand-written predictive policy against current-grade).

WHAT IT CANNOT SAY. It bounds the simulator, which is what the agents were scored in, not
the real car. The traces are the 30 September plant; the 8 October plant ramps the grade
over 8 s and sub-steps the network, so its points are restated with the 8 October
baseline (section G's last column), not re-run. The EGT drop at the lambda bound is
scaled linearly from the measured hand-written one (ASSUMED); the "impossible" rows do not
depend on it. Section I is a SYNTHETIC first-order illustration, not the plant.
"""
import argparse
import io
import json
import os
import sys
from contextlib import redirect_stdout

import numpy as np

import engines

HERE = os.path.dirname(os.path.abspath(__file__))
TRACES = os.path.join(HERE, "results", "traces_130kmh.json")
PREMISE = os.path.join(HERE, "results", "premise.json")
OUT = os.path.join(HERE, "results", "preview_ceiling.txt")
MEI_PTS = 5.43                         # results/PREREGISTRATION_X1.md section 5 (decision 5)

PLANT = engines.get("b58")
TH, DM = PLANT.engine.thermal, PLANT.engine.damage
K = 273.15
C, UA_AMB, UA_G = TH.c_turb, TH.ua_turb_amb, TH.ua_gas_turb
TAMB = PLANT.scenario.t_amb
ONSET = 180                           # make_grade_climb's climb start on the 30 September plant
WARM_K = TH.t_turb_warm               # the housing's warm reset, the Euler step's start


def turb_rate(T):
    return np.exp((T - DM.turb_knee_k) / DM.turb_scale_k)


def terms(p):
    tt = np.array(p["t_turb"], float) + K
    to = np.array(p["t_oil"], float) + K
    ki = np.array(p["ki"], float)
    return (turb_rate(tt), DM.oil_weight * np.exp((to - DM.oil_knee_k) / DM.oil_scale_k),
            DM.ki_weight * np.clip(ki - DM.ki_knee, 0.0, None) ** 2)


def infer_ua(p):
    """Invert T_k = T_{k-1} + (ua (EGT_k - T_{k-1}) - ua_amb (T_{k-1} - T_amb)) / c."""
    T = np.array(p["t_turb"], float) + K
    E = np.array(p["egt"], float) + K
    Tprev = np.concatenate([[WARM_K], T[:-1]])
    ua = (C * (T - Tprev) + UA_AMB * (Tprev - TAMB)) / (E - Tprev)
    return ua, T, E


def decay_gain(T_ref, tau_ref, k0, delta0):
    """Turbine damage saved if T is lower by delta0 at the end of step k0-1 and the
    deviation then decays under the reference run's own inputs."""
    dl = np.zeros_like(T_ref)
    x = delta0
    for k in range(k0, len(T_ref)):
        x *= 1.0 - 1.0 / tau_ref[k]
        dl[k] = x
    return float((turb_rate(T_ref) - turb_rate(T_ref - dl)).sum())


def cool_window(T_start, ua, E, k_from, k_to, egt_drop_K=0.0, egt_floor=None, c=None):
    """Integrate the node over [k_from, k_to) with EGT lowered by egt_drop_K (or held at
    egt_floor) on the same flow; return how much cooler the housing ends."""
    c = C if c is None else c
    t_ref = t_new = T_start
    for k in range(k_from, k_to):
        e_new = egt_floor if egt_floor is not None else E[k] - egt_drop_K
        t_ref = t_ref + (ua[k] * (E[k] - t_ref) - UA_AMB * (t_ref - TAMB)) / c
        t_new = t_new + (ua[k] * (e_new - t_new) - UA_AMB * (t_new - TAMB)) / c
    return t_ref - t_new


def report(d, base_8oct):
    base_30sep = d["baseline ECU"]["summary"]["damage_base"]
    print("PREVIEW CEILING ON THE SCORED CLIMB -- the most any use of the preview could save")
    print(f"inputs: results/traces_130kmh.json (30 September plant), results/premise.json; "
          f"plant {PLANT.engine.id}; MEI {MEI_PTS} points of cut\n")

    print("A. reconstruction check: the rebuilt per-step damage against each trace's own total")
    for name, p in d.items():
        a, b, c = terms(p)
        print(f"   {name:<18} rebuilt {(a + b + c).sum():8.2f}   trace {p['dmg_cum'][-1]:8.2f}   "
              f"turbine {a.sum():7.2f}  oil {b.sum():6.2f}  knock {c.sum():6.2f}")

    print("\nB. where the damage accrues (step = second; the climb starts at 180 s; tau on the climb ~47 s)")
    # verify_docs.py reads the output file: the baseline's total below is the 30 September
    # plant's, the plant these traces were made on, quoted on purpose (the marker names it).
    print("   RETIRED-OK: 920.1 -- the 30 September plant's baseline, whose traces this reads")
    windows = [("0-149    flat, the preview reads nothing", 0, 150),
               ("150-179  flat, the climb inside the 30 s preview", 150, 180),
               ("180-227  climb start to +1 tau", 180, 228),
               ("228-323  1 to 3 tau", 228, 324),
               ("324-718  more than 3 tau after the start", 324, 719)]
    for name in ("baseline ECU", "current-grade"):
        a, b, c = terms(d[name])
        tot = a + b + c
        print(f"   {name}: total {tot.sum():.1f} units")
        for lab, i0, i1 in windows:
            s = tot[i0:i1].sum()
            print(f"      {lab:<50} {s:8.2f}  {100 * s / tot.sum():5.1f} %   "
                  f"(turbine {a[i0:i1].sum():7.2f}, oil {b[i0:i1].sum():5.2f}, knock {c[i0:i1].sum():6.2f})")

    inf = {n: infer_ua(p) for n, p in d.items()}
    print("\nE. the housing's time constant tau = c / (ua_gt + ua_amb), solved from each trace")
    print("   RETIRED-OK: 127.9 -- a time constant in seconds on the flat, not a damage figure")
    for n, (ua, T, E) in inf.items():
        tau = C / (ua + UA_AMB)
        print(f"   {n:<18} flat 150-179 s: {np.median(tau[150:180]):6.1f} s   "
              f"climb 230-718 s: {np.median(tau[230:]):5.1f} s")

    ua_cg, T_cg, E_cg = inf["current-grade"]
    ua_pr, T_pr, E_pr = inf["predictive (hand)"]
    tau_cg = C / (ua_cg + UA_AMB)
    delta = T_cg - T_pr
    print("\nF. the one head start the traces hold: hand-written predictive minus current-grade")
    d_egt = float(np.median(E_cg[150:180] - E_pr[150:180]))
    print(f"   EGT lower on 150-179 s by a median {d_egt:.1f} K; housing cooler by "
          f"{delta[179]:.2f} K at 179 s")
    pred, k0 = [delta[182]], 182
    for k in range(k0 + 1, len(T_cg)):
        pred.append(pred[-1] * (1.0 - 1.0 / tau_cg[k]))
    for k in (190, 228, 276, 324):
        print(f"   t = {k} s: measured {delta[k]:.3f} K, linear-node prediction {pred[k - k0]:.3f} K")
    g = float((turb_rate(T_cg) - turb_rate(T_pr)).sum())
    print(f"   turbine damage it saved: {g:.3f} units = {100 * g / base_30sep:.3f} points")

    ua_b, T_b, E_b = inf["baseline ECU"]
    tau_b = C / (ua_b + UA_AMB)
    egt_bound = d_egt * 0.15 / 0.055            # the lambda trim's bound, -0.15 (ASSUMED linear)
    rows = [
        ("measured: the hand-written head start (lambda -0.055, 30 s)", float(delta[179])),
        ("lambda at its -0.15 bound for 30 s", cool_window(T_cg[149], ua_cg, E_cg, 150, 180, egt_bound)),
        ("lambda -0.15 over the whole flat, 20-179 s (unlimited preview)",
         cool_window(T_cg[19], ua_cg, E_cg, 20, 180, egt_bound)),
        ("IMPOSSIBLE: exhaust gas at ambient for 30 s",
         cool_window(T_cg[149], ua_cg, E_cg, 150, 180, egt_floor=TAMB)),
        ("IMPOSSIBLE: exhaust gas at ambient over the whole flat",
         cool_window(T_cg[19], ua_cg, E_cg, 20, 180, egt_floor=TAMB)),
        ("ABSURD: the housing at ambient when the climb starts", float(T_cg[179] - TAMB)),
    ]
    print("\nG. THE CEILING: turbine damage a cooler housing at the climb start can save")
    print(f"   {'head start':<64}{'K':>7}{'units':>8}{'points':>8}{'points, 8 Oct':>15}"
          f"{'x MEI':>7}")
    for lab, d0 in rows:
        g_cg = decay_gain(T_cg, tau_cg, ONSET, d0)
        print(f"   {lab:<64}{d0:7.1f}{g_cg:8.2f}{100 * g_cg / base_30sep:8.2f}"
              f"{100 * g_cg / base_8oct:15.2f}{100 * g_cg / base_8oct / MEI_PTS:7.2f}")
    print("   (reference: current-grade's own trajectory; the baseline's gives the same order: "
          f"{100 * decay_gain(T_b, tau_b, ONSET, rows[1][1]) / base_30sep:.2f} points at the lambda bound)")

    a = turb_rate(T_cg)
    w = np.ones_like(T_cg)
    x = 1.0
    for k in range(ONSET, len(T_cg)):
        x *= 1.0 - 1.0 / tau_cg[k]
        w[k] = x
    print(f"\nH. the weight the climb-start state carries where the damage accrues "
          f"(sum of rate x memory / sum of rate, on the climb): "
          f"{(a[ONSET:] * w[ONSET:]).sum() / a[ONSET:].sum():.4f}")

    print("\nJ. the horizons decision 27 first proposed, on the locked climb, housing capacity "
          "scaled to the four engines' estimated tau")
    tau_c6000 = float(np.median(C / (ua_cg[230:] + UA_AMB)))
    oil_b = float(terms(d["baseline ECU"])[1].sum())
    knock_b = float(terms(d["baseline ECU"])[2][:ONSET].sum())

    def replay(E, u, c, f=None):
        T, out = WARM_K, np.empty_like(E)
        for k in range(len(E)):
            e = E[k] if f is None else f(k, E[k])
            T = T + (u[k] * (e - T) - UA_AMB * (T - TAMB)) / c
            out[k] = T
        return out
    print(f"   {'tau s':>6}{'H s':>6}{'H/tau':>7}{'points, lambda bound':>22}{'points, EGT at ambient':>24}")
    for tau_t in (39.0, 47.0, 60.0):
        c = C * tau_t / tau_c6000
        Tg, Tb = replay(E_cg, ua_cg, c), replay(E_b, ua_b, c)
        Db = turb_rate(Tb).sum() + oil_b + knock_b
        for H in (int(round(0.3 * tau_t)), 30, int(round(tau_t)), 100, 150):
            Tx = replay(E_cg, ua_cg, c, lambda k, e: e - egt_bound if ONSET - H <= k < ONSET else e)
            Ty = replay(E_cg, ua_cg, c, lambda k, e: TAMB if ONSET - H <= k < ONSET else e)
            print(f"   {tau_t:6.0f}{H:6d}{H / tau_t:7.2f}{100 * (turb_rate(Tg) - turb_rate(Tx)).sum() / Db:22.2f}"
                  f"{100 * (turb_rate(Tg) - turb_rate(Ty)).sum() / Db:24.2f}")

    print("\nI. SYNTHETIC first-order illustration (not the plant): the share of a reference's own")
    print("   damage a head start saves, by climb length L, the climb's and flat's tau from section E")
    tau_c = float(np.median(tau_cg[230:]))
    tau_f = float(np.median(tau_cg[150:180]))
    t_c = float(T_cg[179])

    def road(L, Teq, d0, post=300):
        T, dl, tot, saved = t_c, d0, 0.0, 0.0
        for k in range(L + post):
            tau = tau_c if k < L else tau_f
            target = Teq if k < L else t_c
            T += (target - T) / tau
            dl *= 1 - 1 / tau
            r = float(turb_rate(T))
            tot += r
            saved += r - float(turb_rate(T - dl))
        return tot, saved
    d30, dall = rows[1][1], rows[2][1]
    print(f"   {'plateau C':>10}{'L s':>6}{'saved, 30 s':>13}{'saved, unlimited':>18}")
    for Teq_c in (853.3, 920.0, 1000.0):
        for L in (60, 120, 240, 540):
            tot, s1 = road(L, Teq_c + K, d30)
            _, s2 = road(L, Teq_c + K, dall)
            print(f"   {Teq_c:10.1f}{L:6d}{100 * s1 / tot:12.2f}%{100 * s2 / tot:17.2f}%")
    print(f"   For scale: the MEI is {MEI_PTS} % of the baseline's damage, about 10 % of a "
          "current-grade-like reference's own.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--no-write", action="store_true", help="print only")
    a = ap.parse_args()
    with open(TRACES, encoding="utf-8") as fh:
        d = json.load(fh)
    with open(PREMISE, encoding="utf-8") as fh:
        base_8oct = json.load(fh)["baseline ECU (true neutral)"]["damage_base"]
    buf = io.StringIO()
    with redirect_stdout(buf):
        report(d, base_8oct)
    text = buf.getvalue()
    sys.stdout.write(text)
    if not a.no_write:
        with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"\nwritten to {os.path.relpath(OUT, HERE)}")


if __name__ == "__main__":
    main()

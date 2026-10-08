"""damage_constants.py -- every constant of the damage formula: what could set
it, what it comes to wherever something can, and whether the conclusions move.

    python damage_constants.py     prints the account, writes results/damage_constants.json
                                   and results/figures/damage_constants.png

    d = exp((T_turb - 1123)/45) + 0.4 exp((T_oil - 408)/12) + 40 max(0, KI - 0.85)^2   per second

Asked by Ghassan, 7 October 2026: "Every constant in the formula is a design
choice, not a property of the car. Look for every constant, and if we can
calculate it, do it." REFERENCES.md section 4b lists all seven as DESIGN. This
goes through them one at a time, with the sources opened that day.

A DIAGNOSTIC, NOT A CHANGE. engine_env.damage_rate is untouched; changing it
changes the reward, every damage figure and the hand-written policies' trigger
(TURB_PROTECT_K is the turbine knee), so it means retraining, and adopting any
value below is a decision for Jad and Ghassan in the next preregistration. The
agents were trained on the published formula: a re-score says how sensitive
the EVALUATION is, not what an agent trained on another formula would do.

WHAT THE STRUCTURE ALREADY SETTLES (identities, no source needed):
  - In an exponential term a weight and a knee are ONE number:
    w exp((T - K)/s) = exp((T - K - s ln w)/s). The oil term's 0.4 and 408 K are
    one reference temperature, 397.0 K, at which the oil term is 1 per second.
  - Only relative damage is reported (cut % against the baseline ECU under the
    same formula), so one factor multiplying all three terms changes nothing
    reported. What is left to set: the two temperature scales, where the oil and
    knock terms sit against the turbine term, and the knock term's shape.

THE SEVEN, AND WHAT CAN SET EACH ONE:
  turbine scale 45 K   CALCULATED FOR ONE MECHANISM. If the term stands for creep
                       rupture: the Larson-Miller form, t_r = 10^(P/T - C), gives
                       an e-folding scale T / (ln10 (C + log10 t_r)); with C = 20
                       (Larson and Miller's value, as quoted by Abdallah et al.
                       2014) at 1123 K that is 20.3 K for a 10 000 h life (19.5 K
                       to 21.2 K over 1 000 to 100 000 h). If it stands for
                       oxidation (parabolic scale growth), the scale is R T^2/Q:
                       45 K is Q = 233 kJ/mol, and no opened source gives Q for
                       the housing's alloy, whose grade BMW does not publish (ST1505
                       5.2.1: "one single cast steel part"). The failure mode
                       housings are designed against is thermo-mechanical fatigue,
                       counted per heat-up cycle (BorgWarner: life "calculated
                       based on load spectra"), which no per-second rate can stand
                       for. So: 20.3 K if creep, 45 K is oxidation-like, and the
                       choice of mechanism is the team's.
  turbine knee 1123 K  BRACKETED. A housing-node temperature, so a published GAS
                       limit has to be carried to the housing: at steady state
                       thermal.py's turbine node sits a fixed fraction of the way
                       from the gas to the ambient, read here off the baseline's
                       own climb. BorgWarner's load-spectrum parameter (time above
                       900 C exhaust), Conway et al.'s 930 C pre-turbine limit and
                       BorgWarner's 1050 C rating for cast-steel housings land on
                       the housing at the temperatures this script prints; the
                       published 850 C sits inside them. Which limit the knee means
                       is the team's. It is also the hand-written policies' trigger.
  oil scale 12 K       CALCULATED FROM A RULE OF THUMB: "for every 10 C the rate of
                       lubricant oxidation doubles" (Fitch, Machinery Lubrication,
                       2024) is an e-folding scale of 10/ln2 = 14.4 K. Holloway
                       (Plant Services, 2026) shows the rule is not universal. No
                       opened measurement gives an engine oil's OXIDATION activation
                       energy at sump temperature (Tripathi and Vinu 2015 measure
                       decomposition under nitrogen, a stability marker -- not this).
  oil weight 0.4 and   ONE NUMBER, A VALUATION: where oil damage equals turbine
  knee 408 K           damage is a statement of relative cost. Nothing physical
                       sets it; it would need each component's life and cost.
  knock knee 0.85      CANNOT YET: drive C (logs/DRIVE_PLAN.md) gives the knock
                       integral at which the car's own ECU starts to retard.
  knock weight 40,     A VALUATION: no published law gives knock damage per second
  the square           from a knock integral; knock damage follows knock intensity,
                       which the model does not compute.

Reads the per-step records (eval_record.npz, gitignored) through
damage_robustness.load_records, which first requires the published formula to
give back every committed damage to float32 precision.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import damage_robustness as DR  # noqa: E402

R_GAS = 8.314462618               # J/(mol K)
T_AMB_K = 315.0                   # the locked climb's ambient
LM_C = 20.0                       # Larson and Miller's constant (Abdallah et al. 2014)
LIVES_H = (1e3, 1e4, 1e5)
GAS_LIMITS_C = (                  # published gas temperatures at the turbine inlet
    (900.0, "BorgWarner: housing life from load spectra; the deciding parameter is the time "
            "at full load above 900 C exhaust (assumed 5 % of the time)"),
    (930.0, "Conway et al. 2018, SAE 2018-01-1423, p. 10: 930 C pre-turbine protection limit "
            "on a production-like 1.6 L turbo GDI"),
    (1050.0, "BorgWarner: turbochargers for 1050 C exhaust need heat-resistant austenitic "
             "cast-steel housings"),
)
SOURCES = {
    "ST1505": "BMW Group University, Technical training, B58 Engine, ST1505 (April 2015), section "
              "5.2.1: 'The exhaust manifold of the 3rd and 4th cylinder and the turbocharger housing "
              "form one single cast steel part'. Unofficial copy, archive.org item "
              "BMWTechnicalTrainingDocuments (REFERENCES.md, grey source).",
    "BorgWarner": "Simon, V., Oberholz, G., Mayer, M., BorgWarner Turbo Systems technical paper on "
                  "turbochargers for 1050 C exhaust gas temperature (BWTS library 105/327, undated, "
                  "cites work of 2000), printed pp. 3-4: 950 C at the inlet heats the inner wall near the "
                  "flange to the gas temperature, with a gradient of about 100 C inside the housing; "
                  "Ni-resist D5S 'maximum application temperature of 850 C, in special cases of up "
                  "to 900 C'; 'the service life of the turbine housing is calculated based on load "
                  "spectra. A deciding parameter in this regard is the percentage of time at full "
                  "capacity at exhaust temperatures over 900 C ... assume this is the case 5% of the "
                  "time'; heat-resistant austenitic cast steel for 1050 C.",
    "Conway2018": "Conway, G. et al., SAE 2018-01-1423, p. 10 (REFERENCES.md): 900 C exhaust port, "
                  "930 C pre-turbine.",
    "Abdallah2014": "Abdallah et al., 'A critical analysis of the conventionally employed creep "
                    "lifing methods', Materials (Basel), 2014, PMC5453208: P_LM = T (C_LM + log t_f); "
                    "'Larson and Miller ... suggesting that the value of C_LM to be taken as 20 for "
                    "metallic materials', and that C varies between alloys.",
    "Fitch2024": "Fitch, B., 'How heat affects lubricants: understanding the Arrhenius rate rule', "
                 "Machinery Lubrication (2024): 'For every 10 C (18 F) increase in temperature, the "
                 "rate of lubricant oxidation doubles'.",
    "Holloway2026": "Holloway, M. D., 'What the 10-degree rule gets wrong about lubricant life', "
                    "Plant Services (28 Sep 2026): no universal law; doubling between 60 and 70 C "
                    "alone needs about 66 kJ/mol, and the multiplier changes with temperature.",
    "Tripathi2015": "Tripathi, A. K., Vinu, R., Lubricants 3 (2015) 54-79: 89-106 kJ/mol are "
                    "activation energies of DECOMPOSITION under nitrogen (TGA), a stability marker "
                    "-- not the oxidation rate in a sump. Opened and NOT used.",
}


def creep_scale(t_k, life_h, c=LM_C):
    """e-folding temperature of a Larson-Miller rupture rate at constant stress."""
    return t_k / (np.log(10.0) * (c + np.log10(life_h)))


def q_for_scale(scale_k, t_k):
    """The activation energy an Arrhenius rate needs for this e-folding scale."""
    return R_GAS * t_k ** 2 / scale_k / 1000.0


def knee_map(rec_base):
    """Where a gas temperature lands on the housing node at the climb's steady
    state: T_h = T_gas - r (T_gas - T_amb), with r read off the baseline's own
    last minute of climbing (thermal.py: r = UA_amb / (UA_gas + UA_amb))."""
    egt = np.asarray(rec_base["egt_c"], float)[:, -60:] + 273.15
    tt = np.asarray(rec_base["t_turb"], float)[:, -60:]
    r = float(np.median((egt - tt) / (egt - T_AMB_K)))
    to_housing = lambda gas_c: gas_c + 273.15 - r * (gas_c + 273.15 - T_AMB_K)
    gas_at_knee = (1123.0 - r * T_AMB_K) / (1.0 - r) - 273.15
    return r, to_housing, gas_at_knee, float(np.median(egt[:, -1])) - 273.15, float(np.median(tt[:, -1])) - 273.15


def shares(rec, c):
    """Each term's share of the damage, summed over every episode."""
    tt, to, ki = (np.asarray(rec[k], float) for k in ("t_turb", "t_oil", "ki"))
    turb = np.exp((tt - c["knee"]) / c["scale"]).sum()
    oil = (c["w_oil"] * np.exp((to - c["oil_knee"]) / c["oil_scale"])).sum()
    knock = (c["w_knock"] * np.maximum(0.0, ki - c["knock_knee"]) ** 2).sum()
    tot = turb + oil + knock
    return dict(turbine=round(100 * turb / tot, 2), oil=round(100 * oil / tot, 3), knock=round(100 * knock / tot, 2))


def main():
    names, recs, worst = DR.load_records()
    P = DR.PUBLISHED
    base = np.load(os.path.join(DR.SET, "baseline_ECU", "eval_record.npz"))
    r, to_housing, gas_at_knee, egt_end, tt_end = knee_map(base)

    s_creep = {int(l): float(creep_scale(P["knee"], l)) for l in LIVES_H}
    oil_rule = 10.0 / np.log(2.0)
    knees = [(g, float(to_housing(g)), why) for g, why in GAS_LIMITS_C]
    oil_ref = P["oil_knee"] + P["oil_scale"] * np.log(P["w_oil"])

    print("THE STRUCTURE")
    print(f"  oil weight {P['w_oil']} and knee {P['oil_knee']:.0f} K are one number: the oil term is 1 per second "
          f"at {oil_ref:.1f} K ({oil_ref - 273.15:.1f} C)")
    print("  only relative damage is reported, so one factor on all three terms changes nothing reported")
    print("\nTHE TURBINE SCALE (published 45 K)")
    print(f"  creep rupture, Larson-Miller with C = {LM_C:.0f}, at {P['knee']:.0f} K: "
          + ", ".join(f"{v:.1f} K for a {k:,} h life" for k, v in s_creep.items()))
    print(f"  oxidation, R T^2 / Q: the published 45 K is Q = {q_for_scale(45.0, P['knee']):.0f} kJ/mol; "
          f"20.3 K would be {q_for_scale(s_creep[10000], P['knee']):.0f} kJ/mol "
          "(no opened source gives Q for the housing's alloy)")
    print("\nTHE TURBINE KNEE (published 1123 K, 850 C, on the housing node)")
    print(f"  the baseline's climb ends at {egt_end:.1f} C gas, {tt_end:.1f} C housing: the housing sits "
          f"r = {r:.4f} of the way from the gas to the ambient")
    print(f"  so the published knee is a gas temperature of {gas_at_knee:.0f} C at the climb's operating point")
    for g, h, why in knees:
        print(f"  {g:6.0f} C gas -> {h - 273.15:6.1f} C housing ({h:.1f} K)   {why[:80]}")
    print("\nTHE OIL SCALE (published 12 K)")
    print(f"  'doubles every 10 C' is an e-folding scale of {oil_rule:.2f} K; the published 12 K doubles every "
          f"{12.0 * np.log(2.0):.1f} K (Q = {q_for_scale(12.0, P['oil_knee']):.0f} kJ/mol at {P['oil_knee']:.0f} K, "
          f"against {q_for_scale(oil_rule, P['oil_knee']):.0f} for the rule)")

    rulers = [
        ("as published", {}),
        (f"turbine scale {s_creep[10000]:.1f} K (creep rupture)", {"scale": s_creep[10000]}),
        (f"oil scale {oil_rule:.1f} K (10 C doubling rule)", {"oil_scale": oil_rule}),
        (f"both calculated scales", {"scale": s_creep[10000], "oil_scale": oil_rule}),
    ] + [(f"knee {h - 273.15:.0f} C (from {g:.0f} C gas)", {"knee": h}) for g, h, _ in knees] + [
        # The highest knee shrinks the turbine term until the knock term -- the
        # untested one -- is a fifth to a third of the damage. Without it:
        (f"knee {knees[-1][1] - 273.15:.0f} C, no knock term", {"knee": knees[-1][1], "w_knock": 0.0}),
        ("as published, no knock term", {"w_knock": 0.0}),
    ]
    out = {label: DR.score(names, recs, dict(P, **change)) for label, change in rulers}
    groups = {"baseline ECU": ["baseline_ECU"], "current-grade": ["current-grade"],
              "trained agents": [n for n in names if "_seed" in n]}
    share = {}
    for label, change in rulers:
        c = dict(P, **change)
        share[label] = {g: shares({k: np.concatenate([recs[n][k] for n in ns]) for k in ("t_turb", "t_oil", "ki")}, c)
                        for g, ns in groups.items()}

    print(f"\nRE-SCORED: {len(names)} policies x 20 frozen episodes (the published formula gives back every "
          f"committed damage, worst relative difference {worst:.1e})")
    print(f"{'formula':36s} {'base':>8s} {'grade':>6s} {'pred-grade':>10s} {'sighted':>7s} {'blind':>6s} "
          f"{'>grade':>7s} {'ablation, 95 % CI':>24s} {'p (W)':>6s}")
    for label, s in out.items():
        print(f"{label:36s} {s['base_damage']:8.1f} {s['grade_cut']:6.1f} {s['pred_minus_grade']:+10.2f} "
              f"{s['sighted_median']:7.1f} {s['blind_median']:6.1f} {s['beat_grade']:3d}/{s['n']:<3d} "
              f"{s['ablation_mean']:+6.2f} [{s['ablation_lo']:+6.2f}, {s['ablation_hi']:+6.2f}] "
              f"{s['ablation_p_wilcoxon']:6.2f}")
    print("\neach term's share of the damage, over all twenty episodes")
    for label, by in share.items():
        print(f"  {label:36s} " + "   ".join(f"{g}: turbine {v['turbine']:.1f} %, oil {v['oil']:.2f} %, "
                                             f"knock {v['knock']:.1f} %" for g, v in by.items()))

    constants = [
        dict(constant="turbine scale", published=45.0, unit="K", status="CALCULATED FOR ONE MECHANISM",
             value=round(s_creep[10000], 2), range=[round(s_creep[100000], 2), round(s_creep[1000], 2)],
             how="creep rupture: T / (ln10 (C + log10 t_r)), Larson-Miller C = 20, t_r 1e3-1e5 h; oxidation "
                 "would be R T^2/Q (45 K = Q 233 kJ/mol, Q for the alloy not found); TMF is per cycle",
             sources=["Abdallah2014", "ST1505", "BorgWarner"]),
        dict(constant="turbine knee", published=1123.0, unit="K (housing node)", status="BRACKETED",
             value=None, range=[round(knees[0][1], 1), round(knees[-1][1], 1)],
             how=f"published gas limits carried to the housing at the climb's steady state, r = {r:.4f}",
             mapped={f"{g:.0f} C gas": round(h, 1) for g, h, _ in knees},
             published_as_gas_c=round(gas_at_knee, 1), sources=["BorgWarner", "Conway2018"]),
        dict(constant="oil scale", published=12.0, unit="K", status="CALCULATED FROM A RULE OF THUMB",
             value=round(oil_rule, 2), how="10 C doubling = 10/ln2; the rule is not universal",
             sources=["Fitch2024", "Holloway2026", "Tripathi2015"]),
        dict(constant="oil weight and knee", published=[0.4, 408.0], unit="- , K", status="VALUATION (one number)",
             value=round(oil_ref, 2), how="w exp((T-K)/s) = exp((T-K-s ln w)/s): one reference temperature; "
                                          "relative cost of oil against housing life", sources=[]),
        dict(constant="knock knee", published=0.85, unit="knock integral", status="CANNOT YET (drive C)",
             value=None, how="the knock integral at which the car's ECU starts to retard", sources=[]),
        dict(constant="knock weight and square", published=[40.0, 2], unit="-", status="VALUATION",
             value=None, how="no published law for knock damage per second from a knock integral", sources=[]),
    ]
    path = os.path.join(HERE, "results", "damage_constants.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(dict(published=P, constants=constants, creep_scale_k=s_creep, oil_rule_scale_k=oil_rule,
                       housing_fraction_r=r, climb_end=dict(gas_c=egt_end, housing_c=tt_end),
                       rulers=dict(rulers), summary=out, shares=share, sources=SOURCES), fh, indent=1)
        fh.write("\n")
    print(f"\nwrote {os.path.relpath(path, HERE)}")
    figure(recs, names, out, P, s_creep[10000], knees)


def figure(recs, names, out, P, s_creep, knees):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.8))
    T = np.linspace(1000.0, 1180.0, 300)
    a = ax[0]
    a.semilogy(T - 273.15, np.exp((T - P["knee"]) / P["scale"]), color="#2a78d6", lw=1.8, label="published, 45 K")
    a.semilogy(T - 273.15, np.exp((T - P["knee"]) / s_creep), color="#d0802a", lw=1.8,
               label=f"creep rupture, {s_creep:.1f} K")
    for g, h, _ in knees:
        a.axvline(h - 273.15, color="#8a9096", lw=0.9, ls=":")
        a.text(h - 273.15, 2e-3, f" {g:.0f} C gas", rotation=90, fontsize=7, color="#4b5157", va="bottom")
    a.axvline(P["knee"] - 273.15, color="#d03b3b", lw=1.0, ls="--", label="the knee, 850 C")
    a.set_xlabel("turbine housing, C"); a.set_ylabel("turbine damage per second")
    a.set_title("The turbine term, two scales", fontsize=10); a.legend(fontsize=8, loc="upper left")
    a = ax[1]
    bins = np.arange(700, 900, 4)
    climb = lambda n: np.asarray(recs[n]["t_turb"], float)[:, 180:].ravel() - 273.15
    a.hist(climb("baseline_ECU"), bins=bins, color="#8a9096", alpha=0.7, label="baseline ECU")
    a.hist(np.concatenate([climb(n) for n in names if "_seed" in n]), bins=bins, color="#2a78d6", alpha=0.55,
           weights=np.full(sum(climb(n).size for n in names if "_seed" in n), 1.0 / 20), label="agents, per agent")
    a.axvline(P["knee"] - 273.15, color="#d03b3b", lw=1.0, ls="--")
    a.set_xlabel("turbine housing on the climb, C"); a.set_ylabel("seconds, 20 episodes")
    a.set_title("Where the climb spends its time", fontsize=10); a.legend(fontsize=8, loc="upper left")
    a = ax[2]
    labels = list(out)
    y = np.arange(len(labels))[::-1]
    for yy, label in zip(y, labels):
        s = out[label]
        a.plot([s["ablation_lo"], s["ablation_hi"]], [yy, yy], color="#4b5157", lw=2)
        a.plot(s["ablation_mean"], yy, "o", color="#4a3aa7", ms=6)
        a.text(s["ablation_hi"] + 0.4, yy, f"{s['beat_grade']}/{s['n']} beat current-grade", fontsize=7,
               va="center", color="#4b5157")
    a.axvline(0, color="#d03b3b", lw=1, ls="--")
    a.set_yticks(y, labels, fontsize=8)
    a.set_xlabel("sighted minus blinded, points (mean, 95 % interval)")
    a.set_title("The ablation under the calculated values", fontsize=10)
    a.set_xlim(right=max(s["ablation_hi"] for s in out.values()) + 9)
    fig.tight_layout()
    path = os.path.join(HERE, "results", "figures", "damage_constants.png")
    fig.savefig(path, dpi=130)
    print(f"wrote {os.path.relpath(path, HERE)}")


if __name__ == "__main__":
    main()

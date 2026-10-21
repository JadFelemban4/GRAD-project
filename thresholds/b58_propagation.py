"""b58_propagation.py -- step 3 of engine_thresholds.py: the B58 sensitivities the contract propagates
with, the baseline ECU in the loop. About three minutes (157 s on 21 October).

The B58 plant only (engines.get("b58")). It reads no EPA data and fits nothing. Writes
results/ENGINE_THRESHOLDS/b58_propagation.json.

WHY THE ECU IS IN THE LOOP (review of 21 October, finding 1). Version 1 moved MAP at a FIXED spark. In
the environment the baseline ECU schedules spark on the baseline's MAP (engine_env.py:982), every policy
takes that spark plus its trim (engine_env.py:1004), and at the climb base_spark is the knock-limited
surface (engine_env.py:169-193). A torque bias moves MAP, so it moves the spark too, and the in-use
sensitivity is larger. This step measures it three ways:

  1. fixed spark (version 1's numbers, kept for the record);
  2. the chain along the ECU's schedule: dspark/dMAP from ecu.base_spark at the settled cell (+-2 kPa);
  3. IN THE ENVIRONMENT: the torque the cycle returns multiplied by (1 +- 0.01) for the baseline and the
     agent alike, the locked climb run again, and the medians over t 400-718 s read off. This is the
     number the contract uses (the in-use response, every loop closed).

The climb is run as validation_numbers._climb runs it: the neutral action, frozen episode 1, dt 1 s.
The median over t 100-179 s is the flat approach.
"""
import os

import numpy as np

import engine_env as E
import engines
import evaluate as V
from plant import Operating, run_cycle, exhaust_backpressure_kpa
from thresholds import common

OUT = os.path.join(common.OUT_DIR, "b58_propagation.json")
plant = engines.get("b58")
eng = plant.engine
th = eng.thermal
ecu = E.BaselineECU(eng.ecu)
ORIG_EVAL = E.SupervisoryTunerEnv._evaluate
CLIMB_S, FLAT_S = (400, 718), (100, 179)     # the medians' windows, s
H_KPA = 2.0                                  # the central differences' half-step
T_AMB_C = 42.0                               # the scored roads' ambient


def cyc(rpm, map_kpa, iat_k, ect_k, spark, lam):
    r = run_cycle(Operating(rpm=rpm, map_kpa=map_kpa, iat_k=iat_k, ect_k=ect_k, spark_btdc=spark,
                            lam=lam, p_exh_kpa=exhaust_backpressure_kpa(map_kpa, engine=eng)),
                  engine=eng)
    return dict(torque=r.torque_nm, egt=r.egt_c, mdot=r.mdot_air_gps + r.mdot_fuel_gps,
                fuel=r.mdot_fuel_gps, ki=r.knock_integral)


def run_climb(bias=0.0):
    """The locked climb as validation_numbers._climb runs it, the model's torque scaled by (1 + bias)."""
    def ev(self, *a, **k):
        out = dict(ORIG_EVAL(self, *a, **k))
        out["torque"] = out["torque"] * (1.0 + bias)
        return out
    E.SupervisoryTunerEnv._evaluate = ev
    try:
        seed, weights = V.EPISODES[0]
        cycle = E.make_grade_climb(duration=V.DURATION, dt=V.DT, t_amb=315.0,
                                   grade=plant.scenario.grade, v_kmh=plant.scenario.v_kmh)
        env = E.SupervisoryTunerEnv(cycle, plant=plant, dt=V.DT, seed=seed, use_preview=True)
        env.reset(seed=seed)
        env.w = np.asarray(weights, dtype=np.float32)
        a = np.array(E.neutral_action(), dtype=np.float32)
        rec = []
        while True:
            _, _, term, trunc, info = env.step(a)
            rec.append(dict(t=env.k, rpm=env.rpm, map=env.map_kpa, iat=env.iat_k,
                            ect=info["t_block"], spark=info["spark"], lam=info["lam"],
                            egt=info["egt_c"], mdot=info["mdot_exh"], torque=info["torque"],
                            treq=info["torque_req"], t_turb=info["t_turb"] - 273.15))
            if term or trunc:
                break
    finally:
        E.SupervisoryTunerEnv._evaluate = ORIG_EVAL
    return rec, info["episode_summary"]


def median_point(rec, t0, t1):
    sel = [r for r in rec if t0 <= r["t"] <= t1]
    return {k: float(np.median([r[k] for r in sel])) for k in sel[0] if k != "t"}


def housing(p_egt_c, mdot_gps):
    n = th.n_turbines
    ua_gt = th.ua_gas_turb * mdot_gps / n
    f = ua_gt / (ua_gt + th.ua_turb_amb)
    tau = th.c_turb / (ua_gt + th.ua_turb_amb)
    return dict(f=f, tau_s=tau, dTh_per_unit_ln_mdot=f * (1.0 - f) * (p_egt_c - T_AMB_C),
                ua_gas_turb=th.ua_gas_turb, ua_turb_amb=th.ua_turb_amb, c_turb=th.c_turb)


def chain(p, hs, dsp):
    """+1 % torque bias through the load loop, with spark moving dsp deg per kPa of MAP."""
    base = cyc(p["rpm"], p["map"], p["iat"], p["ect"], p["spark"], p["lam"])
    h = H_KPA
    up = cyc(p["rpm"], p["map"] + h, p["iat"], p["ect"], p["spark"] + dsp * h, p["lam"])
    dn = cyc(p["rpm"], p["map"] - h, p["iat"], p["ect"], p["spark"] - dsp * h, p["lam"])
    d = {k: (up[k] - dn[k]) / (2 * h) for k in ("torque", "egt", "mdot", "fuel")}
    dmap = -0.01 * base["torque"] / d["torque"]
    tb = dict(dmap_kpa=dmap, degt_k=d["egt"] * dmap, dmdot_rel=d["mdot"] * dmap / base["mdot"])
    tb["dTh_ss_k"] = hs["f"] * tb["degt_k"] + hs["dTh_per_unit_ln_mdot"] * tb["dmdot_rel"]
    return base, dict(per_kpa=d, torque_bias_1pct=tb)


def partials(p, hs):
    base, fixed = chain(p, hs, 0.0)
    h = H_KPA
    dsp = (ecu.base_spark(p["rpm"], p["map"] + h) - ecu.base_spark(p["rpm"], p["map"] - h)) / (2 * h)
    _, sched = chain(p, hs, dsp)
    sched.update(dspark_dmap_deg_per_kpa=dsp, base_spark=ecu.base_spark(p["rpm"], p["map"]),
                 knock_limited_spark=ecu.knock_limited_spark(p["rpm"], p["map"]))
    out = {"point": p, "base": base, "fixed_spark": fixed, "ecu_schedule": sched}
    lam = {}
    for dl in (-0.01, -0.02, -0.05, -0.10, -0.15):
        r = cyc(p["rpm"], p["map"], p["iat"], p["ect"], p["spark"], p["lam"] + dl)
        lam[f"{dl:+.2f}"] = dict(egt=r["egt"], degt=r["egt"] - base["egt"],
                                 dtorque_rel=r["torque"] / base["torque"] - 1.0)
    out["lambda"] = lam
    sp = {}
    for ds in (-0.75, +0.75):
        r = cyc(p["rpm"], p["map"], p["iat"], p["ect"], p["spark"] + ds, p["lam"])
        sp[f"{ds:+.2f}"] = dict(degt=r["egt"] - base["egt"], dtorque_rel=r["torque"] / base["torque"] - 1.0)
    out["spark"] = sp
    return out


def compute():
    rec0, summ0 = run_climb(0.0)
    climb = median_point(rec0, *CLIMB_S)
    flat = median_point(rec0, *FLAT_S)
    res = {"episode_summary": summ0, "peak_t_turb_c": max(r["t_turb"] for r in rec0)}
    for key, p in (("climb", climb), ("flat", flat)):
        hs = housing(p["egt"], p["mdot"])
        res[key] = partials(p, hs)
        res[key]["housing"] = hs
    env = {}
    for bias in (+0.01, -0.01):
        rec, summ = run_climb(bias)
        m = median_point(rec, *CLIMB_S)
        env[f"{bias:+.2f}"] = dict(
            dmap_kpa=m["map"] - climb["map"], dspark_deg=m["spark"] - climb["spark"],
            degt_k=m["egt"] - climb["egt"], dmdot_rel=m["mdot"] / climb["mdot"] - 1.0,
            dTh_median_k=m["t_turb"] - climb["t_turb"],
            dpeak_k=max(r["t_turb"] for r in rec) - res["peak_t_turb_c"],
            damage=summ["damage"], damage_unbiased=summ0["damage"])
    res["env_torque_bias"] = env
    up, dn = env["+0.01"], env["-0.01"]
    res["env_coefficients"] = dict(
        housing_k_per_pct_central=(dn["dTh_median_k"] - up["dTh_median_k"]) / 2.0,
        housing_k_per_pct_larger=max(abs(up["dTh_median_k"]), abs(dn["dTh_median_k"])),
        flow_pct_per_pct_central=100.0 * (dn["dmdot_rel"] - up["dmdot_rel"]) / 2.0,
        flow_pct_per_pct_larger=100.0 * max(abs(up["dmdot_rel"]), abs(dn["dmdot_rel"])))
    return res


def report(res):
    c = res["climb"]
    climb = c["point"]
    summ0 = res["episode_summary"]
    print("climb cell", {k: round(v, 3) for k, v in climb.items()})
    print("damage %.2f, peak housing %.2f C" % (summ0["damage"], res["peak_t_turb_c"]))
    print("housing: f %.4f, tau %.2f s, dTh/dln m %.2f K" % (
        c["housing"]["f"], c["housing"]["tau_s"], c["housing"]["dTh_per_unit_ln_mdot"]))
    for k in ("fixed_spark", "ecu_schedule"):
        tb = c[k]["torque_bias_1pct"]
        print(f"{k}: per kPa {c[k]['per_kpa']}; +1 % torque bias: MAP {tb['dmap_kpa']:.3f} kPa, "
              f"gas {tb['degt_k']:.3f} K, flow {100 * tb['dmdot_rel']:.3f} %, housing {tb['dTh_ss_k']:.3f} K")
    print("ECU spark slope %.4f deg/kPa (base_spark %.3f, knock limit %.3f)" % (
        c["ecu_schedule"]["dspark_dmap_deg_per_kpa"], c["ecu_schedule"]["base_spark"],
        c["ecu_schedule"]["knock_limited_spark"]))
    for b, v in res["env_torque_bias"].items():
        print(f"env torque bias {b}: " + ", ".join(f"{k} {x:+.4f}" for k, x in v.items()))
    print("env coefficients", {k: round(v, 4) for k, v in res["env_coefficients"].items()})
    f = res["flat"]
    print("flat: f %.4f tau %.2f; ecu-schedule flow per +1 %% torque %.3f %%, housing %.3f K" % (
        f["housing"]["f"], f["housing"]["tau_s"], 100 * f["ecu_schedule"]["torque_bias_1pct"]["dmdot_rel"],
        f["ecu_schedule"]["torque_bias_1pct"]["dTh_ss_k"]))
    print("lambda at the climb", {k: round(v["degt"], 2) for k, v in c["lambda"].items()})
    print("spark at the climb", {k: (round(v["degt"], 2), round(100 * v["dtorque_rel"], 2))
                                 for k, v in c["spark"].items()})


def run():
    res = compute()
    common.write_json(OUT, res)
    report(res)
    return res

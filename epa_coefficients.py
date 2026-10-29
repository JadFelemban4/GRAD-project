"""epa_coefficients.py -- an engine's own propagation coefficients on its locked climb, descriptive.

Build step 2, WP3 (23 October 2026): docs/build_step_2/PLAN.md section 5.9 item 5; amendment F5;
docs/build_step_2/HANDOFFS.md, WP3 item 4; docs/build_step_2/WP3_INTERFACES.md section 5.7. It
reads no EPA data and fits nothing: calibrate_epa.py complete hands it the engine's frozen plant
(its K3 knee set, PLAN.md 5.9 item 4) and writes what it returns to complete.json.

WHAT IT IS. thresholds/b58_propagation.py:43-155 made a function of any plant: the climb's median
cell over t 400-718 s and the flat approach's over t 100-179 s, the housing's gain f, time constant
tau and the gas-to-housing term G of each, the gas, flow and housing response to a +1 % torque
bias through the load loop at a fixed spark and along the ECU's own spark schedule, the lambda and
spark partials, and the environment's response to a +-1 % torque bias with every loop closed. On
the B58 it gives results/ENGINE_THRESHOLDS/b58_propagation.json back bit for bit (test_epa_
coefficients.py). b58_propagation.py itself stays untouched: the contract JSON's `generators` pins
its sha256, and it builds the B58 at import (amendment C12), so no step-2 module imports it.

DESCRIPTIVE ONLY. An EPA engine's coefficients never move an R (results/ENGINE_THRESHOLDS.md
section 1.4; PLAN.md 5.9 item 5): the contract's R are set from the B58's, which errs tight.

WHAT CHANGED IN THE LIFT, AND WHY:
  - the plant is an argument everywhere (mistake 1), and the ECU is the plant's own
    (engine_env.BaselineECU(plant.engine.ecu)), built where it is used;
  - cyc() passes the ECU's intake cam, BaselineECU.cam_deg(rpm, map_kpa), to plant.run_cycle, as
    measure_deliverable_torque does (HANDOFFS WP3 item 4): None on every engine whose form has no
    D, the B58 among them, which is what b58_propagation's cyc passed implicitly; a form-D engine
    is evaluated at its scheduled cam, where b58_propagation's cyc would be refused (plant.
    volumetric_efficiency: "cam_deg is None");
  - the climb's ambient is the plant's own, plant.scenario.t_amb (amendment F5): b58_propagation
    typed 315.0 (:60), the B58's scenario, so a plant with another ambient would have climbed at
    the B58's;
  - the housing's G stays the contract's reference, the gas over 42 C, thresholds.contract.T_AMB_C
    (the "42C" of propagation_b58.G_gas_over_42C_k; b58_propagation.py:40 typed it apart from the
    climb's 315.0), passed to housing() by keyword: the scored roads' ambient, not the climb's;
  - the torque bias is applied by wrapping one environment INSTANCE's _evaluate, where
    b58_propagation patched the class for the whole process: the same call, the same product,
    with nothing left behind if a run stops.
  - a run whose knee is not finite, or whose episode ends early, is refused: the medians would be
    of another climb (mistake 19).
"""
import math

import numpy as np

import engine_env as E
import engines
import evaluate as V
from plant import Operating, run_cycle, exhaust_backpressure_kpa
from thresholds.contract import T_AMB_C

CLIMB_S, FLAT_S = (400, 718), (100, 179)     # the medians' windows, s (b58_propagation.py:38)
H_KPA = 2.0                                  # the central differences' half-step (b58_propagation.py:39)
BIASES = (+0.01, -0.01)                      # the environment's torque biases (b58_propagation.py:139)


def _plant(plant, who):
    """Refuse anything but an engines.Plant by name: there is no default engine (mistake 1)."""
    if not isinstance(plant, engines.Plant):
        raise TypeError(f"{who} needs an engines.Plant (engines.get or engines.build_candidate), not "
                        f"{type(plant).__name__}: there is no default engine (CLAUDE.md mistake 1)")
    return plant


def cyc(plant, rpm, map_kpa, iat_k, ect_k, spark, lam):
    """One cycle of the plant's engine at this point, with its backpressure and its ECU's cam at
    (rpm, map_kpa): the torque (Nm), the gas temperature (C), the exhaust flow (air + fuel, g/s),
    the fuel (g/s) and the knock integral. b58_propagation.py:43-48 with the cam passed (HANDOFFS
    WP3 item 4)."""
    eng = _plant(plant, "epa_coefficients.cyc").engine
    cam = E.BaselineECU(eng.ecu).cam_deg(rpm, map_kpa)
    r = run_cycle(Operating(rpm=rpm, map_kpa=map_kpa, iat_k=iat_k, ect_k=ect_k, spark_btdc=spark,
                            lam=lam, p_exh_kpa=exhaust_backpressure_kpa(map_kpa, engine=eng)),
                  engine=eng, cam_deg=cam)
    return dict(torque=r.torque_nm, egt=r.egt_c, mdot=r.mdot_air_gps + r.mdot_fuel_gps,
                fuel=r.mdot_fuel_gps, ki=r.knock_integral)


def climb_cycle(plant):
    """The plant's locked climb as b58_propagation.py:60-61 builds it, at the plant's own ambient
    (amendment F5): evaluate.DURATION and DT, the scenario's grade, speed and ambient."""
    sc = _plant(plant, "epa_coefficients.climb_cycle").scenario
    return E.make_grade_climb(duration=V.DURATION, dt=V.DT, t_amb=sc.t_amb, grade=sc.grade, v_kmh=sc.v_kmh)


def run_climb(plant, *, bias):
    """The locked climb as validation_numbers._climb runs it -- the neutral action, frozen episode
    1, dt 1 s -- with the model's torque scaled by (1 + bias) for the baseline and the agent alike:
    b58_propagation.py:51-77. Returns the step records and the episode summary. bias is a Python
    float (amendment B10)."""
    _plant(plant, "epa_coefficients.run_climb")
    if type(bias) is not float:
        raise TypeError(f"epa_coefficients.run_climb: bias must be a Python float, not {type(bias).__name__}")
    k = plant.engine.damage.turb_knee_k
    if not math.isfinite(k):
        raise ValueError(f"epa_coefficients.run_climb: the plant's turbine knee is {k!r}; a NaN knee ends "
                         "the episode at its first step, so set the K3 knee first (PLAN.md 5.9 item 4)")
    seed, weights = V.EPISODES[0]
    env = E.SupervisoryTunerEnv(climb_cycle(plant), plant=plant, dt=V.DT, seed=seed, use_preview=True)
    orig = env._evaluate

    def ev(*a, **kw):
        out = dict(orig(*a, **kw))
        out["torque"] = out["torque"] * (1.0 + bias)
        return out
    env._evaluate = ev
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
    if term:
        raise RuntimeError(f"epa_coefficients.run_climb: the episode terminated at step {len(rec)} (a "
                           "non-finite reward), so the medians would not be the climb's")
    return rec, info["episode_summary"]


def median_point(rec, t0, t1):
    """Every channel's median over the records with t0 <= t <= t1 (b58_propagation.py:80-82)."""
    sel = [r for r in rec if t0 <= r["t"] <= t1]
    return {k: float(np.median([r[k] for r in sel])) for k in sel[0] if k != "t"}


def housing(plant, egt_c, mdot_gps, *, t_amb_c):
    """The turbine housing node of the plant's thermal network at this gas temperature (C) and
    exhaust flow (g/s): its gain f = UA_gt/(UA_gt + UA_amb), its time constant, and G's term
    f(1 - f)(T_gas - t_amb_c), the housing's response to a unit change of ln(flow)
    (b58_propagation.py:85-91). t_amb_c is the reference G is taken over, the contract's 42 C
    (thresholds.contract.T_AMB_C) in coefficients(); required, so it is never the climb's by
    accident (amendment F5)."""
    th = _plant(plant, "epa_coefficients.housing").engine.thermal
    n = th.n_turbines
    ua_gt = th.ua_gas_turb * mdot_gps / n
    f = ua_gt / (ua_gt + th.ua_turb_amb)
    tau = th.c_turb / (ua_gt + th.ua_turb_amb)
    return dict(f=f, tau_s=tau, dTh_per_unit_ln_mdot=f * (1.0 - f) * (egt_c - t_amb_c),
                ua_gas_turb=th.ua_gas_turb, ua_turb_amb=th.ua_turb_amb, c_turb=th.c_turb)


def chain(plant, point, hs, dsp):
    """A +1 % torque bias through the load loop at this point, with the spark moving dsp deg per
    kPa of MAP (b58_propagation.py:94-104): the per-kPa central differences, the MAP change that
    takes 1 % of torque back, and the gas, flow and steady housing change that follow."""
    p, h = point, H_KPA
    base = cyc(plant, p["rpm"], p["map"], p["iat"], p["ect"], p["spark"], p["lam"])
    up = cyc(plant, p["rpm"], p["map"] + h, p["iat"], p["ect"], p["spark"] + dsp * h, p["lam"])
    dn = cyc(plant, p["rpm"], p["map"] - h, p["iat"], p["ect"], p["spark"] - dsp * h, p["lam"])
    d = {k: (up[k] - dn[k]) / (2 * h) for k in ("torque", "egt", "mdot", "fuel")}
    dmap = -0.01 * base["torque"] / d["torque"]
    tb = dict(dmap_kpa=dmap, degt_k=d["egt"] * dmap, dmdot_rel=d["mdot"] * dmap / base["mdot"])
    tb["dTh_ss_k"] = hs["f"] * tb["degt_k"] + hs["dTh_per_unit_ln_mdot"] * tb["dmdot_rel"]
    return base, dict(per_kpa=d, torque_bias_1pct=tb)


def partials(plant, point, hs):
    """At this point: chain() at a fixed spark and along the plant's ECU's spark schedule
    (dspark/dMAP from its base_spark, +-H_KPA), and the gas and torque change for lambda -0.01 to
    -0.15 and spark +-0.75 deg (b58_propagation.py:107-126)."""
    p, h = point, H_KPA
    ecu = E.BaselineECU(_plant(plant, "epa_coefficients.partials").engine.ecu)
    base, fixed = chain(plant, p, hs, 0.0)
    dsp = (ecu.base_spark(p["rpm"], p["map"] + h) - ecu.base_spark(p["rpm"], p["map"] - h)) / (2 * h)
    _, sched = chain(plant, p, hs, dsp)
    sched.update(dspark_dmap_deg_per_kpa=dsp, base_spark=ecu.base_spark(p["rpm"], p["map"]),
                 knock_limited_spark=ecu.knock_limited_spark(p["rpm"], p["map"]))
    out = {"point": p, "base": base, "fixed_spark": fixed, "ecu_schedule": sched}
    lam = {}
    for dl in (-0.01, -0.02, -0.05, -0.10, -0.15):
        r = cyc(plant, p["rpm"], p["map"], p["iat"], p["ect"], p["spark"], p["lam"] + dl)
        lam[f"{dl:+.2f}"] = dict(egt=r["egt"], degt=r["egt"] - base["egt"],
                                 dtorque_rel=r["torque"] / base["torque"] - 1.0)
    out["lambda"] = lam
    sp = {}
    for ds in (-0.75, +0.75):
        r = cyc(plant, p["rpm"], p["map"], p["iat"], p["ect"], p["spark"] + ds, p["lam"])
        sp[f"{ds:+.2f}"] = dict(degt=r["egt"] - base["egt"], dtorque_rel=r["torque"] / base["torque"] - 1.0)
    out["spark"] = sp
    return out


def climb_cell(plant):
    """The plant's in-use climb cell: every channel's median over CLIMB_S of the unbiased locked climb
    (run_climb at bias 0.0, the neutral action with every loop closed), the cell coefficients() reads
    as res["climb"]["point"]. One climb, about 50 s at 0.25 deg; a function of the plant alone, so
    calibrate_epa.py complete can run one per E6 probe in its ordered pool (PLAN.md 5.9 item 6: the
    probes are "found by running the climb at +-10 % and scaling linearly"; added by WP3's
    integration, 23 October 2026)."""
    rec, _summary = run_climb(_plant(plant, "epa_coefficients.climb_cell"), bias=0.0)
    return median_point(rec, *CLIMB_S)


def median_resolution(values):
    """(median, resolution) of a window of values: the median as np.median takes it, and how far it moves when
    one sample crosses it -- the larger gap between the order statistics that form the median and their outer
    neighbours. A change of the window smaller than that may only reorder samples around the median, so the
    median does not resolve it (decision 85, 29 October 2026). Needs at least 3 values."""
    v = np.sort(np.asarray(values, dtype=float))
    n = len(v)
    if n < 3:
        raise ValueError(f"median_resolution needs at least 3 values, not {n}")
    med = float(np.median(v))
    lo_i, hi_i = (n // 2, n // 2) if n % 2 else (n // 2 - 1, n // 2)
    gaps = [med - float(v[lo_i - 1]), float(v[hi_i + 1]) - med]
    return med, max(gaps)


def climb_cell_resolution(plant):
    """The climb cell's numerical resolution (decision 85, 29 October 2026: an E6 probe whose response slope is
    below its numerical noise is not visible at R1): the unbiased locked climb run as climb_cell runs it, and for
    the gas and the exhaust flow over CLIMB_S their medians (climb_cell's own, which the caller checks equal) and
    median_resolution's resolution. {"egt", "mdot", "egt_resolution_k", "mdot_resolution_gps", "samples"}."""
    rec, _summary = run_climb(_plant(plant, "epa_coefficients.climb_cell_resolution"), bias=0.0)
    sel = [r for r in rec if CLIMB_S[0] <= r["t"] <= CLIMB_S[1]]
    egt, egt_res = median_resolution([r["egt"] for r in sel])
    mdot, mdot_res = median_resolution([r["mdot"] for r in sel])
    return {"egt": egt, "mdot": mdot, "egt_resolution_k": egt_res, "mdot_resolution_gps": mdot_res,
            "samples": len(sel)}


def housing_equivalent(hs, d_egt_k, d_ln_mdot):
    """The housing equivalent of a change at the climb cell (results/ENGINE_THRESHOLDS.md section 1.4:
    the housing T_h = f T_gas + (1 - f) T_amb moves by f dT_gas + f(1 - f) G d ln(mdot)), with the
    engine's OWN f and G term at its climb cell (`hs`, housing()'s record there; the contract's E6:
    "the engine's own in-use housing equivalent at its locked-climb cell"), the steady housing change
    chain() writes as dTh_ss_k. K."""
    return hs["f"] * d_egt_k + hs["dTh_per_unit_ln_mdot"] * d_ln_mdot


def coefficients(plant):
    """The plant's own coefficients, in b58_propagation.compute()'s structure and key order
    (b58_propagation.py:129-155): the unbiased climb's summary and peak housing; the climb's and
    the flat approach's partials and housing, G over the contract's 42 C; the environment's
    response to +-1 % torque bias; and its central and larger coefficients. About three climbs."""
    _plant(plant, "epa_coefficients.coefficients")
    rec0, summ0 = run_climb(plant, bias=0.0)
    climb = median_point(rec0, *CLIMB_S)
    flat = median_point(rec0, *FLAT_S)
    res = {"episode_summary": summ0, "peak_t_turb_c": max(r["t_turb"] for r in rec0)}
    for key, p in (("climb", climb), ("flat", flat)):
        hs = housing(plant, p["egt"], p["mdot"], t_amb_c=T_AMB_C)
        res[key] = partials(plant, p, hs)
        res[key]["housing"] = hs
    env = {}
    for bias in BIASES:
        rec, summ = run_climb(plant, bias=bias)
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

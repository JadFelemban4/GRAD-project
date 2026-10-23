"""
Single-zone, zero-dimensional SI engine cycle model.

Physics:
  - Slider-crank volume
  - Wiebe heat-release
  - Woschni convective wall heat transfer
  - Chen-Flynn friction correlation
  - Douaud & Eyzat knock induction-time integral

Reference engine: BMW B58B30O1 — 3.0 L turbocharged INLINE-SIX, direct
injection. The engine in the 2023 Toyota GR Supra this project logs.

NO DEFAULT ENGINE (20 October 2026)
-----------------------------------
This file used to default to a generic 2.0 L inline-FOUR, with `b58()` offered
as an opt-in override. That was a trap, and the project fell into it: not one
call to `run_cycle()` anywhere in the repo passed a geometry, so the entire
Gymnasium environment, the premise check, the reward tests and ten of the eleven
rows of the validation table silently simulated a 1998 cc four-cylinder while
every document said 2998 cc six. Torque came out 33 % low (mistake 1).

The repair of September made the defaults the B58, so that no code path could
pick the wrong engine by omission while there was one engine. Decision 24 makes
the H/tau test four engines, and a default that is the B58 is then the same trap
pointed the other way. So there are no defaults: every function here takes the
engine as a required keyword -- an `engines.Engine`, built by `engines.get(name)`
from the typed values in engine_specs/ and the derived values in the engine's
derived file -- and every engine-specific number below is read from it. The
arithmetic is the September plant's, operation for operation, so the B58 built
through `engines.get("b58")` computes the same doubles.
"""

import numpy as np
from dataclasses import dataclass

# Properties of gasoline and air, shared physics, the same for every engine here
# (mistake 1: an engine's own number is never a module constant). The engine's
# own numbers -- geometry, breathing, burn, knock, friction, port, backpressure,
# octane, and its fuel's heating value and stoichiometric ratio -- are fields of
# engines.Engine (engines.Geometry, engines.CycleCal, engines.Fuel; the geometry
# moved there on 20 October 2026 with its volume functions). LHV = 44.0e6 and
# AFR_STOICH = 14.7 stood here until 22 October 2026 (build step 2, P1): each
# EPA engine was mapped on its own test fuel, and the validation contract makes
# the plant take each engine's LHV and AFR_st (results/ENGINE_THRESHOLDS.json,
# conventions.fuel). The latent heat is not among them, and stays shared.
R_AIR = 287.0          # J/kg/K
H_FG = 3.50e5          # J/kg, gasoline latent heat of vaporisation
CP_AIR = 1005.0        # J/kg/K


def gamma_of_T(T):
    """Ratio of specific heats. The steep fall above ~2000 K stands in for
    dissociation, which absorbs energy the single-zone model cannot resolve."""
    return np.clip(1.38 - 1.02e-4 * (T - 300.0), 1.19, 1.40)


def combustion_efficiency(lam, *, engine):
    """Fraction of the air-limited chemical energy actually released.
    Rich mixtures leave energy in CO and H2; very lean mixtures burn
    incompletely and partially misfire.

    THE RICH SLOPE IS THE ENGINE'S (22 October 2026, build step 2 P3): a literal
    0.65 here for every engine until then, engine.cycle.ce_rich_slope now. The
    validation contract's form C fits each engine its own on its enriched hot
    rows (the Honda runs to lambda 0.61, beyond any B58 data); forms A and B
    share 0.65 (engines.SHARED_RICH_SLOPE, which CycleCal holds them to). The
    B58's is that double, so the product is the same. The lean branch is shared
    by every form, unchanged."""
    if lam < 1.0:
        return 1.0 - engine.cycle.ce_rich_slope * (1.0 - lam)
    return np.clip(1.0 - 0.55 * (lam - 1.08) ** 2 / 0.04 * (lam > 1.08), 0.80, 1.0)


def volumetric_efficiency(rpm, map_kpa, cam_deg, *, engine):
    """Simple breathing curve, normalised to intake manifold density.

    FORM B ADDS A MAP TERM (22 October 2026, build step 2 P3; the contract's form
    B, "VE in rpm and MAP (a linear MAP term)"): ve_map * (map_kpa -
    ve_map_ref_kpa) on the rpm curve, before the clip. map_kpa is required, never
    defaulted (mistake 1). Form A, the B58's, returns the old one-line expression
    VERBATIM and never reads map_kpa, which may then be None (map_from_airflow,
    which solves for the MAP). Not form B's sum at ve_map 0: that adds an exact
    0.0 for a finite MAP, but 0.0 times a NaN MAP is NaN, and eta_v is an output
    (PLAN.md section 3.2).

    FORM D ADDS A CAM TERM (22 October 2026, build step 2 P4; decision 41, the
    contract's form D, "the intake cam phase as an input to VE, through a
    schedule cam(rpm, MAP) ... run by the ECU"): ve_cam * (cam_deg -
    cam_ref_deg), after form B's term and before the clip. The cam is the ECU's
    (engine_env.BaselineECU.cam_deg), handed down by run_cycle's caller; cam_deg
    is required here, never defaulted. A form without D refuses a number, since
    its breathing would ignore it, and form D refuses None. Form A's check is a
    comparison before its line, no arithmetic: the line is unchanged."""
    c = engine.cycle
    if c.form == "A":
        if cam_deg is not None:
            raise ValueError(f"cycle form 'A' has no cam input (form D's), and cam_deg is {cam_deg!r}")
        return np.clip(c.ve_base + c.ve_amp * np.exp(-((rpm - c.ve_rpm) / c.ve_width) ** 2), c.ve_lo, c.ve_hi)
    v = c.ve_base + c.ve_amp * np.exp(-((rpm - c.ve_rpm) / c.ve_width) ** 2)
    if "B" in c.form.split("+"):
        if map_kpa is None:
            raise ValueError(f"cycle form {c.form!r} reads the MAP (ve_map, form B): map_kpa is None")
        v = v + c.ve_map * (map_kpa - c.ve_map_ref_kpa)
    if "D" in c.form.split("+"):
        if cam_deg is None:
            raise ValueError(f"cycle form {c.form!r} reads the intake cam (ve_cam, form D): cam_deg is None. "
                             "The ECU schedules it (engine_env.BaselineECU.cam_deg)")
        v = v + c.ve_cam * (cam_deg - c.cam_ref_deg)
    elif cam_deg is not None:
        raise ValueError(f"cycle form {c.form!r} has no cam input (form D's), and cam_deg is {cam_deg!r}")
    return np.clip(v, c.ve_lo, c.ve_hi)


def burn_duration(rpm, lam, f_res, *, engine):
    """Total Wiebe burn duration in crank-angle degrees."""
    c = engine.cycle
    # laminar flame speed peaks slightly rich
    speed_factor = np.exp(-((lam - c.flame_lam) / c.flame_width) ** 2)
    speed_factor = np.clip(speed_factor, c.flame_floor, 1.0)
    base = c.burn_base + c.burn_rpm * rpm         # turbulence scales with rpm, but so does time
    return base / speed_factor * (1.0 + c.burn_res * f_res)


def ignition_delay(rpm, lam, f_res, *, engine):
    c = engine.cycle
    speed_factor = np.clip(np.exp(-((lam - c.flame_lam) / c.flame_width) ** 2), c.flame_floor, 1.0)
    return (c.delay_base + c.delay_rpm * rpm) / speed_factor * (1.0 + c.delay_res * f_res)


def residual_fraction(map_kpa, *, engine):
    """Residual gas fraction: high at low load (small fresh charge, same
    clearance volume). ONE definition, for run_cycle and map_from_airflow."""
    c = engine.cycle
    return np.clip(c.fres_a + c.fres_b / max(map_kpa, c.fres_map_min), c.fres_lo, c.fres_hi)


# Every input is required (20 October 2026). The octane is the ENGINE's fuel now
# (engines.CycleCal.octane): it was a default of 95 RON here, the B58's fuel,
# which any other engine would have inherited without a word.
@dataclass
class Operating:
    rpm: float
    map_kpa: float        # intake manifold absolute pressure
    iat_k: float          # intake air temperature
    ect_k: float          # engine coolant temperature
    spark_btdc: float     # spark advance, deg before TDC
    lam: float            # lambda (AFR / AFR_stoich)
    p_exh_kpa: float      # exhaust manifold backpressure


@dataclass
class CycleResult:
    torque_nm: float
    power_kw: float
    bmep_bar: float
    imep_bar: float
    fmep_bar: float
    bsfc_gpkwh: float
    egt_c: float
    p_max_bar: float
    knock_integral: float
    knock_prob: float
    mfb50_deg: float
    mdot_fuel_gps: float
    t_max_k: float
    mdot_air_gps: float = float('nan')   # air mass flow, g/s
    eta_v: float = float('nan')          # volumetric efficiency actually used
    f_res: float = float('nan')          # residual gas fraction


# Crank-angle step for the cycle integration, in degrees.
#
# CHOSEN BY A CONVERGENCE STUDY, 16 September 2026 (AUDIT.md H1). It was 0.5
# deg, with no study behind it, and the model is NOT converged there. The
# integration is explicit Euler, so the error is first order and halves with
# the step -- measured against a 0.0625 deg reference:
#
#   dtheta   torque err   EGT err   knock-integral err
#   1.0      -1.0 to -3.9 %   -30 to -44 K   -4.0 to -4.5 %
#   0.5      -0.5 to -1.8 %   -14 to -21 K   -1.9 to -2.5 %   <- was shipped
#   0.25     -0.2 to -0.8 %    -6 to  -9 K   -0.8 to -1.1 %   <- shipped now
#   0.125    -0.1 to -0.3 %    -2 to  -3 K   -0.3 to -0.4 %
#
# 0.25 halves the error for double the cost (9 ms a cycle against 5). It is not
# converged either, and that is the point of publishing the table: THE RESIDUAL
# DISCRETISATION ERROR IS ABOUT 7 K OF EGT AND 0.25 % OF TORQUE, and it belongs
# beside any figure quoted to finer precision than that.
#
# Every EGT the model reports is therefore ~7 K LOW, which pushes the cruise-band
# EGT row of validate.py further outside its band rather than closer to it. That
# is the honest direction and it is why the step was not left alone.
#
# test_convergence() in validate.py fails if halving the step moves a headline
# by more than the precision that headline is quoted to.
DTHETA_DEG = 0.25


def run_cycle(op: Operating, *, engine, dtheta: float = DTHETA_DEG, cam_deg=None) -> CycleResult:
    """One closed cycle of `engine`, an engines.Engine: required, no default.

    `cam_deg` is the intake cam phase, crank degrees, that the engine's ECU
    commands (engine_env.BaselineECU.cam_deg; 22 October 2026, build step 2 P4,
    decision 41): a number for an engine whose cycle form has D, and None, no cam
    input, for every other, the B58 among them. The breathing refuses either the
    wrong way round. A keyword beside the operating point, not an Operating field:
    Operating's seven fields are what the contract's generator and the
    certificate harness build (PLAN.md section 3.1)."""
    geo, c = engine.geometry, engine.cycle
    # the engine's fuel (engines.Fuel, 22 October 2026): 14.7 and 44.0 MJ/kg on
    # the B58, the module constants they replace, read in the same order
    fuel = engine.fuel

    # ---------------- charge preparation ----------------
    # residual fraction: high at low load (small fresh charge, same clearance volume)
    f_res = residual_fraction(op.map_kpa, engine=engine)
    eta_v = volumetric_efficiency(op.rpm, op.map_kpa, cam_deg, engine=engine)   # B's MAP, D's cam
    rho_int = op.map_kpa * 1000.0 / (R_AIR * op.iat_k)
    m_air = eta_v * rho_int * geo.vd_cyl * (1.0 - f_res)
    m_fuel = m_air / (fuel.afr_st * op.lam)

    t_wall = 0.5 * op.ect_k + 0.5 * (op.ect_k + c.t_head_k)      # crude head/liner mean

    # direct injection: vaporising the fuel cools the trapped charge.
    # This is the mechanism behind "enrichment protects against knock".
    m_charge = m_air + m_fuel
    dt_evap = m_fuel * H_FG / (m_charge * CP_AIR)
    t_fresh = op.iat_k + c.port_pickup_k - dt_evap          # port/wall pickup, +12 K on the B58
    t_ivc = (1.0 - f_res) * t_fresh + f_res * c.t_residual_k

    # combustion is air-limited when rich, and rich products retain energy as CO/H2
    eta_comb = combustion_efficiency(op.lam, engine=engine)
    q_total = min(m_fuel, m_air / fuel.afr_st) * fuel.lhv_j_per_kg * eta_comb

    # ---------------- Wiebe schedule ----------------
    delay = ignition_delay(op.rpm, op.lam, f_res, engine=engine)
    dur = burn_duration(op.rpm, op.lam, f_res, engine=engine)
    theta_soc = -op.spark_btdc + delay
    a_w, m_w = c.wiebe_a, c.wiebe_m

    def mfb(theta):
        x = (theta - theta_soc) / dur
        if x <= 0.0:
            return 0.0
        if x >= 1.0:
            return 1.0
        return 1.0 - np.exp(-a_w * x ** (m_w + 1.0))

    # ---------------- integrate the closed cycle ----------------
    theta = np.arange(geo.ivc_deg, geo.evo_deg + dtheta, dtheta)
    n = len(theta)
    P = np.zeros(n)
    T = np.zeros(n)

    v_ivc = geo.volume(geo.ivc_deg)
    # trapped mass follows from the charge, not from MAP: enrichment adds mass,
    # which is part of why a rich cylinder runs cooler
    m_tot = m_charge / (1.0 - f_res)
    T[0] = t_ivc
    P[0] = m_tot * R_AIR * t_ivc / v_ivc

    omega = op.rpm * 6.0                      # deg/s
    dt = dtheta / omega                        # s per step
    sp_mean = 2.0 * geo.stroke * op.rpm / 60.0

    ki = 0.0
    q_ht_total = 0.0
    work = 0.0
    prev_mfb = 0.0

    # motored reference for Woschni
    p_mot = P[0] * (v_ivc / geo.volume(theta)) ** 1.32

    # the end gas's polytropic exponent and the knock correlation, read once
    n_poly = c.n_poly                   # polytropic, not isentropic: the end gas loses heat
    knock_a, knock_on, knock_p, knock_b = c.knock_a, c.knock_on, c.knock_p, c.knock_b
    octane = c.octane                   # the engine's fuel, RON

    for i in range(1, n):
        th0, th1 = theta[i - 1], theta[i]
        v0, v1 = geo.volume(th0), geo.volume(th1)
        dv = v1 - v0

        g = gamma_of_T(T[i - 1])

        x0, x1 = prev_mfb, mfb(th1)
        dq_burn = q_total * (x1 - x0)
        prev_mfb = x1

        # Woschni heat transfer
        w_gas = 2.28 * sp_mean
        if x1 > 1e-6:
            w_gas += 3.24e-3 * (geo.vd_cyl * t_ivc / (P[0] * v_ivc)) * (P[i - 1] - p_mot[i - 1])
        w_gas = max(w_gas, 1.0)
        h_c = 3.26 * geo.bore ** -0.2 * (P[i - 1] / 1000.0) ** 0.8 * T[i - 1] ** -0.55 * w_gas ** 0.8
        dq_ht = h_c * geo.liner_area(th0) * (T[i - 1] - t_wall) * dt
        q_ht_total += dq_ht

        dP = (g - 1.0) / v0 * (dq_burn - dq_ht) - g * P[i - 1] / v0 * dv
        P[i] = max(P[i - 1] + dP, 1.0e4)
        T[i] = P[i] * v1 / (m_tot * R_AIR)

        work += 0.5 * (P[i] + P[i - 1]) * dv

        # ---- knock induction integral over the unburned end gas ----
        # Integrated from spark to the end of combustion. Before spark the end gas
        # is far too cold to contribute; after burn-out there is no end gas left.
        if -op.spark_btdc <= th1 and x1 < 0.99:
            t_unburned = t_ivc * (P[i] / P[0]) ** ((n_poly - 1.0) / n_poly)
            p_atm = P[i] / 101325.0
            tau = knock_a * (octane / 100.0) ** knock_on * p_atm ** knock_p * np.exp(knock_b / t_unburned)
            ki += dt / tau

    # ---------------- work accounting ----------------
    imep_gross = work / geo.vd_cyl                       # Pa
    pmep = (op.map_kpa - op.p_exh_kpa) * 1000.0          # Pa, positive when boosted
    imep_net = imep_gross + pmep

    p_max_bar = P.max() / 1e5
    fmep_bar = c.fmep_0 + c.fmep_pmax * p_max_bar + c.fmep_sp * sp_mean + c.fmep_sp2 * sp_mean ** 2
    bmep = imep_net - fmep_bar * 1e5

    torque = bmep * geo.vd_total / (4.0 * np.pi)
    power_w = torque * op.rpm * 2.0 * np.pi / 60.0
    mdot_fuel = m_fuel * geo.n_cyl * op.rpm / 120.0      # kg/s
    mdot_air = m_air * geo.n_cyl * op.rpm / 120.0        # kg/s

    bsfc = (mdot_fuel * 3.6e6) / (power_w / 1000.0) if power_w > 500.0 else float("nan")

    # ---------------- exhaust temperature ----------------
    # Blowdown: the charge expands irreversibly to manifold pressure, then loses
    # heat to the port and runner walls on the way to the thermocouple.
    # Port heat loss is a counterflow-style effectiveness: at low flow the gas has
    # time to cool, at high flow it barely does. This is why EGT climbs with load.
    # UA_PORT is the one openly empirical constant here - calibrate it against your
    # own logged EGT in Phase 2. Both are the engine's: 15 W/K and 1150 J/kg/K
    # on the B58 (engine_specs/b58.toml).
    UA_PORT = c.ua_port     # W/K
    CP_EXH = c.cp_exh       # J/kg/K
    mdot_exh = (m_air + m_fuel) * geo.n_cyl * op.rpm / 120.0
    t_evo = T[-1]
    t_blowdown = t_evo * (op.p_exh_kpa / (P[-1] / 1000.0)) ** 0.20
    retained = np.exp(-UA_PORT / max(mdot_exh * CP_EXH, 1.0))
    t_exh = t_wall + (t_blowdown - t_wall) * retained

    # MFB50
    mfb_arr = np.array([mfb(t) for t in theta])
    idx50 = int(np.argmax(mfb_arr >= 0.5))
    mfb50 = theta[idx50] if mfb_arr[-1] >= 0.5 else np.nan

    knock_prob = float(1.0 / (1.0 + np.exp(-12.0 * (ki - 1.0))))

    return CycleResult(
        torque_nm=float(torque),
        power_kw=float(power_w / 1000.0),
        bmep_bar=float(bmep / 1e5),
        imep_bar=float(imep_net / 1e5),
        fmep_bar=float(fmep_bar),
        bsfc_gpkwh=float(bsfc),
        egt_c=float(t_exh - 273.15),
        p_max_bar=float(p_max_bar),
        knock_integral=float(ki),
        knock_prob=knock_prob,
        mfb50_deg=float(mfb50),
        mdot_fuel_gps=float(mdot_fuel * 1000.0),
        t_max_k=float(T.max()),
        mdot_air_gps=float(mdot_air * 1000.0),
        eta_v=float(eta_v),
        f_res=float(f_res),
    )


# ---------------------------------------------------------------------------
# Shared plant interface
# ---------------------------------------------------------------------------
# Every plant in this project exposes predict(): keyword inputs in, a plain dict
# of named outputs out. battery.py must expose the same contract so that the
# agent code can drive either plant without modification. Documents refer to
# this function by name -- do not rename it.

def exhaust_backpressure_kpa(map_kpa, *, engine):
    """Exhaust manifold pressure is not measured on this vehicle. It is modelled as
    a fixed multiple of intake manifold pressure, floored -- 1.15 and 105 kPa on the
    B58 (engines.CycleCal.exh_bp_ratio, exh_bp_min_kpa). This is a stated
    ASSUMPTION, not a measurement -- say so in Chapter 3.

    THE ONE DEFINITION (AUDIT.md M2: the ratio was 1.12 in the environment and
    1.15 here). predict() and the environment both call it; it replaces the
    module constant EXH_BACKPRESSURE_RATIO, which was the B58's for every engine."""
    c = engine.cycle
    return max(c.exh_bp_min_kpa, map_kpa * c.exh_bp_ratio)


def predict(rpm, map_kpa, iat_k, ect_k, spark_btdc, lam,
            p_exh_kpa=None, cam_deg=None, *, engine) -> dict:
    """Run one engine cycle and return named outputs.

    Temperatures in kelvin, pressures in kPa absolute, spark in degrees BTDC.
    If p_exh_kpa is omitted it is estimated from map_kpa (exhaust_backpressure_kpa).
    `engine` is required; the fuel's octane is the engine's. `cam_deg` is
    run_cycle's: the ECU's intake cam for a form-D engine, None for every other
    (22 October 2026, build step 2 P4).
    """
    if p_exh_kpa is None:
        p_exh_kpa = exhaust_backpressure_kpa(map_kpa, engine=engine)
    r = run_cycle(Operating(rpm=rpm, map_kpa=map_kpa, iat_k=iat_k, ect_k=ect_k,
                            spark_btdc=spark_btdc, lam=lam,
                            p_exh_kpa=p_exh_kpa),
                  engine=engine, cam_deg=cam_deg)
    return dict(
        torque_nm=r.torque_nm, power_kw=r.power_kw,
        bmep_bar=r.bmep_bar, imep_bar=r.imep_bar, fmep_bar=r.fmep_bar,
        bsfc_gpkwh=r.bsfc_gpkwh, egt_c=r.egt_c, p_max_bar=r.p_max_bar,
        knock_integral=r.knock_integral, knock_prob=r.knock_prob,
        mfb50_deg=r.mfb50_deg, mdot_fuel_gps=r.mdot_fuel_gps,
        mdot_air_gps=r.mdot_air_gps, t_max_k=r.t_max_k,
        eta_v=r.eta_v, f_res=r.f_res,
    )


# ---------------------------------------------------------------------------
# Compressor boost ceiling -- DERIVED from the logs, re-derived with every drive
# ---------------------------------------------------------------------------
# This is NOT a compressor map. It is the OPERATING CEILING: the highest
# pressure ratio the vehicle was observed to reach at a given corrected mass
# flow, over every quasi-steady, MAF-unpinned sample in data/master_samples.csv.
#
# The difference matters. A compressor map shows what the compressor CAN do,
# bounded by surge and choke, with efficiency islands and shaft-speed lines.
# This curve shows what the CAR DID, which is the compressor's capability
# combined with wastegate control and the knock limit. At low flow the ratio is
# low because the wastegate is open, not because the compressor ran out.
#
# For our purpose that is the right object anyway: the model's defect was that
# manifold pressure was an unbounded input, so it would produce whatever power
# the commanded boost implied. This bounds it to what the vehicle actually does.
#
# THE CEILING IS THE MEASURED ENVELOPE ITSELF (28 September 2026): the 95th
# percentile of pressure ratio in each 0.03 kg/s corrected-flow bin, made
# monotone by a running maximum (a ceiling cannot fall as flow rises), anchored
# at PR 1 with no flow, interpolated linearly between bins, and capped at the
# highest stable pressure ratio in the logs. NO CONSTANT IS FITTED. It is
# computed by derive_params.py every time the data changes and read from
# data/derived_params.json, which also carries each bin's row and
# independent-reading counts. Since 20 October engines.py reads it into the
# engine's record (engines.BoostCal) when the plant is built.
#
# What it replaced: PR = 1 + A*m/(1 + B*m) with A = 14.5023, B = 6.4019, fitted
# once on 8 September, capped at 2.6 "observed peak plus margin" -- a margin
# nobody measured. That form was chosen because a quadratic turned over above
# 0.25 kg/s; the running maximum guarantees the same thing without a formula,
# and unlike it can follow the envelope's jump from PR 1.6 at 0.075 kg/s to 2.1
# at 0.105 kg/s -- exactly where drive B's low-rpm roll-ons sit, and where the
# formula left the modelled engine short of torque at 1600-2200 rpm.
#
# Drive B (28 September) was logged for exactly this: full-throttle roll-ons in
# a held 6th, 7th and 8th from 1440-2000 rpm, where the flat-road logs had never
# asked for boost. It logged no ambient temperature, so its corrected flow uses
# an ambient taken from our own afternoon logs (build_dataset.AMB_FALLBACK_C);
# derive_params.py re-derives A and B at the coolest and hottest ambient ever
# logged and records both, so the effect of that assumption is on file.
#
# REMAINING GAP: above 0.314 kg/s corrected, where the MAF saturates.

T_REF_CORR, P_REF_CORR = 298.0, 101.3


def corrected_flow(mdot_air_gps, t_inlet_k, p_inlet_kpa):
    """Compressor-corrected mass flow, kg/s — the x-axis of any compressor map."""
    return ((mdot_air_gps * 1e-3) * np.sqrt(t_inlet_k / T_REF_CORR)
            / (p_inlet_kpa / P_REF_CORR))


def boost_ceiling_kpa(mdot_air_gps, t_inlet_k, p_inlet_kpa, *, engine):
    """Highest manifold pressure this vehicle was observed to reach at this flow.

    Returns kPa absolute. Use it to clamp map_kpa so the model cannot invent
    boost the car has never produced.

    t_inlet_k IS THE COMPRESSOR INLET — ambient air, roughly 300-320 K in Jeddah.
    It is NOT "intake air temperature before throttle valve", which is measured
    downstream of the compressor and the intercooler and runs 70-170 C. Passing
    the downstream temperature inflates corrected flow and raises the ceiling by
    about 10 %, which quietly defeats the point of having a ceiling.

    t_inlet_k AND p_inlet_kpa ARE REQUIRED (20 October 2026). They were defaults of
    298 K and 99.3 kPa -- the B58's sea-level inlet, which wide_air.py and
    conditions_test.py had to monkeypatch to move. The caller says which air the
    compressor breathes; at sea level that is the engine's boost.inlet_sea_kpa
    (99.3 on the B58: 101.3 less a 2 kPa filter loss). The envelope and its cap
    are the engine's, DERIVED (engines.BoostCal).
    """
    b = engine.boost
    m = corrected_flow(mdot_air_gps, t_inlet_k, p_inlet_kpa)
    pr = float(np.interp(m, b.envelope_flow, b.envelope_pr))
    return float(p_inlet_kpa * min(pr, b.pr_cap))


def charge_temperature(t_amb_k, t_block_k, *, engine) -> float:
    """Temperature of the air actually trapped in the cylinder, in K.

    THE ONE DEFINITION. Import this everywhere. Do not inline the formula and
    do not substitute a logged channel -- see below for what that cost.

    WHY THIS EXISTS (10 September 2026)
    -----------------------------------
    `build_dataset.py` and `compare_log.py` used to feed the logged channel
    `Intake air temperature before throttle valve` straight into
    map_from_airflow() as the charge temperature, because
    logs/CHANNEL_SET_FINAL.md labelled it "post-intercooler".

    THAT LABEL WAS WRONG. The channel reads 149 C under boost, and peaks at
    163 C. No working water-to-air charge cooler, with its circuit sitting near
    ambient, delivers 149 C air to the ports. What it matches instead is a
    COMPRESSOR OUTLET: at pressure ratio 2.3 and 70 % efficiency from 40 C
    inlet air, isentropic compression gives 160 C. The B58 carries its charge
    cooler INSIDE the intake manifold, downstream of the throttle body, so
    "before throttle valve" is before the cooler.

    The car settles it, at a gate chosen so that the two populations describe
    the same operating region. THE GATE IS 200 kPa AND IT IS NOT ARBITRARY: the
    logged side keeps `Boost pressure` above 15 psi gauge, and
    (15 + 14.23) * 6.894757 = 201.5 kPa absolute, so gating the model side at
    200 kPa matches the logged population BY CONSTRUCTION. Gate the model at
    180 instead and it admits samples 20 kPa below anything the logged set
    contains, which drags the model median down and flatters the gap.

    At the matched gate: 587 boosted, MAF-unpinned model samples against 887
    logged readings of the vehicle's own `Boost pressure` channel, whose median
    is 226 kPa absolute.

        charge temperature used              | inverted MAP | gap vs the car
        the raw sensor (117 C median)        | 279.5 kPa    | +23.7 %
        charge_temperature(), THIS FUNCTION  | 232.7 kPa    | +1.9 %
        ambient + 8 K (45 C median)          | 227.5 kPa    | +0.7 %

    CLAUDE.md used to blame that 23.7 % on the breathing model -- fitted at part
    load, said to understate breathing under boost. IT IS NOT THE BREATHING
    MODEL. It is the temperature. `volumetric_efficiency()` is cleared by this
    correction, not convicted by it -- and note exactly what that leaves: there
    is NO part-load test of it against this car, because both logged pressure
    channels sit upstream of the throttle and there is nothing to compare a
    modelled manifold pressure against.

    WHY NOT `ambient + 8 K`, WHICH SCORES +0.7 %
    --------------------------------------------
    Because that is a knob tuned to hit the target, and this project has
    already been burned by exactly that move once this week -- see CLAUDE.md
    mistake 12. The formula below was written independently for the Gymnasium
    environment, months before this question came up, and was never touched to
    make this number agree. It carries NO parameter fitted to the boost
    channel.

    Be honest about how thin that contrast is. At the matched gate `ambient +
    8 K` scores +0.7 %, not the +0.0 % a looser gate reported, and +0.7 %
    against +1.9 % is a smaller margin than the rhetoric wants. The rejection
    stands anyway, on the same ground: a 3.0 % gap from a model with no
    parameter fitted to the boost channel says more than a closer gap from one
    tuned against it. Report +1.9 %; do not tune it away.

    LIMIT, STATE IT IN CHAPTER 3. There is no measured charge-temperature
    channel on this car: `Temperature after the intercooler` exists in the
    census and reads all-zero on every sample. This is a MODEL of the charge
    temperature, anchored to ambient, not a measurement. The +1.9 % gap over
    587 boosted samples above 200 kPa is the evidence for it and the whole of
    the evidence for it.

    THE TWO CONSTANTS ARE THE ENGINE'S (20 October 2026): +12 K and 0.06 of the
    block's excess on the B58 (engines.ChargeCal). `t_block_k` is required: pass
    None, explicitly, for the charge with no block coupling (an environment's
    reset, a server with no block input).
    """
    c = engine.charge
    if t_block_k is None:
        return t_amb_k + c.rise_k
    return t_amb_k + c.rise_k + c.block_coupling * (t_block_k - t_amb_k)


def map_from_airflow(mdot_air_gps, rpm, iat_k, *, engine) -> float:
    """Invert the speed-density relation: given a MEASURED air mass flow, return
    the manifold pressure the model needs.

    Use this instead of a logged pressure channel. Air mass flow has one
    unambiguous unit; the pressure channels on this vehicle do not reconcile
    with physics until the parked-idle test settles them. See the audit, §8.

    Residual fraction depends on manifold pressure, which is what we are solving
    for, so this iterates. Three passes converge to well under 1 %.

    `engine` is required (20 October 2026): the inversion runs through that
    engine's own geometry, breathing and residual fraction.

    FORM A ONLY (22 October 2026, build step 2 P3). The breathing is read once,
    before the loop, at no MAP; under form B it depends on the MAP solved for,
    and an inversion would have to iterate it too and be shown to converge
    (mistake 15). Nothing asks for one: every caller inverts the B58's logged
    air, and no EPA row is inverted (PLAN.md WP1 P3). Any other form is refused,
    never inverted with a breathing that ignores its own MAP term. Form A has no
    cam input either (P4), so the breathing is given None for both.
    """
    if engine.cycle.form != "A":
        raise ValueError(f"map_from_airflow inverts form A only; this engine's cycle form is "
                         f"{engine.cycle.form!r}, whose breathing reads the MAP being solved for")
    geo = engine.geometry
    eta_v = volumetric_efficiency(rpm, None, None, engine=engine)
    map_kpa = 100.0
    for _ in range(6):
        f_res = float(residual_fraction(map_kpa, engine=engine))
        denom = eta_v * geo.vd_cyl * (1.0 - f_res) * geo.n_cyl * rpm / 120.0
        if denom <= 0:
            return float("nan")
        rho = (mdot_air_gps * 1e-3) / denom
        map_kpa = float(rho * R_AIR * iat_k / 1000.0)
    return map_kpa


if __name__ == "__main__":
    # Mistake 1: NEVER let a call site take a default engine. These four sweeps
    # used to rely on one, which is the exact shape of the bug that ran a 1998 cc
    # four-cylinder for three weeks. One name, passed explicitly, everywhere.
    import engines
    eng = engines.get("b58").engine
    amb = dict(iat_k=298.0, ect_k=363.0)     # what Operating's defaults used to supply

    print("=== A. Naturally aspirated cruise, 2500 rpm, 60 kPa, lambda 1.0 ===")
    for spark in [10, 15, 20, 25, 30, 35, 40]:
        r = run_cycle(Operating(rpm=2500, map_kpa=60, spark_btdc=spark, lam=1.0, **amb,
                                p_exh_kpa=exhaust_backpressure_kpa(60, engine=eng)), engine=eng)
        print(f"  spark {spark:3d} BTDC | T {r.torque_nm:6.1f} Nm | BSFC {r.bsfc_gpkwh:6.1f} "
              f"| MFB50 {r.mfb50_deg:5.1f} | EGT {r.egt_c:5.0f} C | KI {r.knock_integral:5.2f}")

    print("\n=== B. Full load boosted, 3000 rpm, 200 kPa, lambda 0.85 ===")
    for spark in [4, 8, 12, 16, 20, 24]:
        r = run_cycle(Operating(rpm=3000, map_kpa=200, spark_btdc=spark, lam=0.85, **amb, p_exh_kpa=230),
                      engine=eng)
        print(f"  spark {spark:3d} BTDC | T {r.torque_nm:6.1f} Nm | BSFC {r.bsfc_gpkwh:6.1f} "
              f"| Pmax {r.p_max_bar:5.1f} bar | EGT {r.egt_c:5.0f} C | KI {r.knock_integral:5.2f} "
              f"| Pknock {r.knock_prob:.2f}")

    print("\n=== C. Lambda sweep at 3000 rpm, 180 kPa, 14 BTDC ===")
    for lam in [0.75, 0.80, 0.85, 0.90, 1.00, 1.10, 1.20]:
        r = run_cycle(Operating(rpm=3000, map_kpa=180, spark_btdc=14, lam=lam, **amb, p_exh_kpa=210),
                      engine=eng)
        print(f"  lambda {lam:4.2f} | T {r.torque_nm:6.1f} Nm | BSFC {r.bsfc_gpkwh:6.1f} "
              f"| EGT {r.egt_c:5.0f} C | KI {r.knock_integral:5.2f}")

    print("\n=== D. IAT sensitivity, 3000 rpm, 180 kPa, 16 BTDC, lambda 0.88 ===")
    for iat_c in [15, 25, 35, 45, 55]:
        r = run_cycle(Operating(rpm=3000, map_kpa=180, spark_btdc=16, lam=0.88,
                                iat_k=273.15 + iat_c, ect_k=363.0, p_exh_kpa=210), engine=eng)
        print(f"  IAT {iat_c:3d} C | T {r.torque_nm:6.1f} Nm | EGT {r.egt_c:5.0f} C "
              f"| KI {r.knock_integral:5.2f} | Pknock {r.knock_prob:.2f}")

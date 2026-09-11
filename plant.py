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

THE DEFAULTS ARE THE B58, DELIBERATELY
--------------------------------------
This file used to default to a generic 2.0 L inline-FOUR, with `b58()` offered
as an opt-in override. That was a trap, and the project fell into it: not one
call to `run_cycle()` anywhere in the repo passed a geometry, so the entire
Gymnasium environment, the premise check, the reward tests and ten of the eleven
rows of the validation table silently simulated a 1998 cc four-cylinder while
every document said 2998 cc six. Torque came out 33 % low.

There is exactly one engine in this project. `Geometry()` and `b58()` now return
the same thing, so no code path can pick the wrong one by omission. If a second
engine is ever added, pass it explicitly — do not change these defaults back.
"""

import numpy as np
from dataclasses import dataclass, field

R_AIR = 287.0          # J/kg/K
LHV = 44.0e6           # J/kg, gasoline lower heating value
AFR_STOICH = 14.7


@dataclass
class Geometry:
    """BMW B58B30O1 by default. See the module docstring for why."""
    bore: float = 0.0820        # m
    stroke: float = 0.0946      # m
    conrod: float = 0.1444      # m
    n_cyl: int = 6
    comp_ratio: float = 10.2
    ivc_deg: float = -140.0     # aTDC firing
    evo_deg: float = 140.0      # aTDC firing

    def __post_init__(self):
        self.crank = self.stroke / 2.0
        self.area_piston = np.pi * self.bore ** 2 / 4.0
        self.vd_cyl = self.area_piston * self.stroke
        self.vd_total = self.vd_cyl * self.n_cyl
        self.vc = self.vd_cyl / (self.comp_ratio - 1.0)

    def volume(self, theta_deg):
        """Instantaneous cylinder volume, theta in deg aTDC firing."""
        th = np.radians(theta_deg)
        a, l = self.crank, self.conrod
        s = a * np.cos(th) + np.sqrt(l ** 2 - (a * np.sin(th)) ** 2)
        return self.vc + self.area_piston * (l + a - s)

    def dvolume_dtheta(self, theta_deg):
        """dV/dtheta in m^3 per degree."""
        th = np.radians(theta_deg)
        a, l = self.crank, self.conrod
        root = np.sqrt(l ** 2 - (a * np.sin(th)) ** 2)
        ds_dth = -a * np.sin(th) - (a ** 2 * np.sin(th) * np.cos(th)) / root
        return -self.area_piston * ds_dth * np.pi / 180.0

    def liner_area(self, theta_deg):
        """Exposed liner + head + piston crown area."""
        v = self.volume(theta_deg)
        x = (v - self.vc) / self.area_piston      # exposed liner height
        return 2.0 * self.area_piston + np.pi * self.bore * x


H_FG = 3.50e5          # J/kg, gasoline latent heat of vaporisation
CP_AIR = 1005.0        # J/kg/K


def gamma_of_T(T):
    """Ratio of specific heats. The steep fall above ~2000 K stands in for
    dissociation, which absorbs energy the single-zone model cannot resolve."""
    return np.clip(1.38 - 1.02e-4 * (T - 300.0), 1.19, 1.40)


def combustion_efficiency(lam):
    """Fraction of the air-limited chemical energy actually released.
    Rich mixtures leave energy in CO and H2; very lean mixtures burn
    incompletely and partially misfire."""
    if lam < 1.0:
        return 1.0 - 0.65 * (1.0 - lam)
    return np.clip(1.0 - 0.55 * (lam - 1.08) ** 2 / 0.04 * (lam > 1.08), 0.80, 1.0)


def volumetric_efficiency(rpm):
    """Simple breathing curve, normalised to intake manifold density."""
    return np.clip(0.86 + 0.14 * np.exp(-((rpm - 3800.0) / 2600.0) ** 2), 0.60, 1.02)


def burn_duration(rpm, lam, f_res):
    """Total Wiebe burn duration in crank-angle degrees."""
    # laminar flame speed peaks slightly rich
    speed_factor = np.exp(-((lam - 0.90) / 0.42) ** 2)
    speed_factor = np.clip(speed_factor, 0.25, 1.0)
    base = 34.0 + 0.0022 * rpm                    # turbulence scales with rpm, but so does time
    return base / speed_factor * (1.0 + 2.0 * f_res)


def ignition_delay(rpm, lam, f_res):
    speed_factor = np.clip(np.exp(-((lam - 0.90) / 0.42) ** 2), 0.25, 1.0)
    return (7.0 + 0.0011 * rpm) / speed_factor * (1.0 + 1.5 * f_res)


def b58() -> Geometry:
    """BMW B58B30O1 - 2021+ six-port head, 387 PS / 500 Nm. INLINE-SIX.
    The engine in the 2023 GR Supra 3.0. Displacement comes out at 2997.5 cc,
    matching the factory figure.

    Kept as a named constructor because the documents refer to it, but it is now
    identical to `Geometry()`. See the module docstring: the defaults were a
    different engine, and every call site that omitted a geometry got that
    different engine without saying so.
    """
    return Geometry()


@dataclass
class Operating:
    rpm: float = 3000.0
    map_kpa: float = 100.0        # intake manifold absolute pressure
    iat_k: float = 298.0          # intake air temperature
    ect_k: float = 363.0          # engine coolant temperature
    spark_btdc: float = 20.0      # spark advance, deg before TDC
    lam: float = 1.00             # lambda (AFR / AFR_stoich)
    p_exh_kpa: float = 105.0      # exhaust manifold backpressure
    octane: float = 95.0          # RON


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


def run_cycle(op: Operating, geo: Geometry = None, dtheta: float = 0.5) -> CycleResult:
    geo = geo or Geometry()

    # ---------------- charge preparation ----------------
    # residual fraction: high at low load (small fresh charge, same clearance volume)
    f_res = np.clip(0.035 + 6.5 / max(op.map_kpa, 25.0), 0.03, 0.18)
    eta_v = volumetric_efficiency(op.rpm)
    rho_int = op.map_kpa * 1000.0 / (R_AIR * op.iat_k)
    m_air = eta_v * rho_int * geo.vd_cyl * (1.0 - f_res)
    m_fuel = m_air / (AFR_STOICH * op.lam)

    t_wall = 0.5 * op.ect_k + 0.5 * (op.ect_k + 90.0)      # crude head/liner mean

    # direct injection: vaporising the fuel cools the trapped charge.
    # This is the mechanism behind "enrichment protects against knock".
    m_charge = m_air + m_fuel
    dt_evap = m_fuel * H_FG / (m_charge * CP_AIR)
    t_fresh = op.iat_k + 12.0 - dt_evap                     # +12 K from port/wall pickup
    t_ivc = (1.0 - f_res) * t_fresh + f_res * 780.0

    # combustion is air-limited when rich, and rich products retain energy as CO/H2
    eta_comb = combustion_efficiency(op.lam)
    q_total = min(m_fuel, m_air / AFR_STOICH) * LHV * eta_comb

    # ---------------- Wiebe schedule ----------------
    delay = ignition_delay(op.rpm, op.lam, f_res)
    dur = burn_duration(op.rpm, op.lam, f_res)
    theta_soc = -op.spark_btdc + delay
    a_w, m_w = 5.0, 2.0

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
            n_poly = 1.32                       # polytropic, not isentropic: the end gas loses heat
            t_unburned = t_ivc * (P[i] / P[0]) ** ((n_poly - 1.0) / n_poly)
            p_atm = P[i] / 101325.0
            tau = 0.01768 * (op.octane / 100.0) ** 3.402 * p_atm ** -1.7 * np.exp(3800.0 / t_unburned)
            ki += dt / tau

    # ---------------- work accounting ----------------
    imep_gross = work / geo.vd_cyl                       # Pa
    pmep = (op.map_kpa - op.p_exh_kpa) * 1000.0          # Pa, positive when boosted
    imep_net = imep_gross + pmep

    p_max_bar = P.max() / 1e5
    fmep_bar = 0.40 + 0.005 * p_max_bar + 0.090 * sp_mean + 0.0009 * sp_mean ** 2
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
    # own logged EGT in Phase 2.
    UA_PORT = 15.0          # W/K
    CP_EXH = 1150.0         # J/kg/K
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

EXH_BACKPRESSURE_RATIO = 1.15
"""Exhaust manifold pressure is not measured on this vehicle. It is modelled as
a fixed multiple of intake manifold pressure. This is a stated ASSUMPTION, not a
measurement -- say so in Chapter 3."""


def predict(rpm, map_kpa, iat_k, ect_k, spark_btdc, lam,
            p_exh_kpa=None, octane=95.0, geo=None) -> dict:
    """Run one engine cycle and return named outputs.

    Temperatures in kelvin, pressures in kPa absolute, spark in degrees BTDC.
    If p_exh_kpa is omitted it is estimated from map_kpa; see the note above.
    """
    if p_exh_kpa is None:
        p_exh_kpa = max(105.0, map_kpa * EXH_BACKPRESSURE_RATIO)
    r = run_cycle(Operating(rpm=rpm, map_kpa=map_kpa, iat_k=iat_k, ect_k=ect_k,
                            spark_btdc=spark_btdc, lam=lam,
                            p_exh_kpa=p_exh_kpa, octane=octane),
                  geo=geo or b58())
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
# Compressor boost ceiling — measured, refit dated 8 September 2026
# ---------------------------------------------------------------------------
# This is NOT a compressor map. It is the OPERATING CEILING: the highest
# pressure ratio the vehicle was observed to reach at a given corrected mass
# flow, across 43 853 quasi-steady samples over 168.1 minutes and eight drives.
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
# REFITTED 8 September 2026, after the mid-load drive (cb67b01f) filled the
# empty middle. The shipped constants stand on the quasi-steady set named above,
# whose size verify_docs.py checks against the shipped data on every run — so if
# this comment and the data ever part company again, the run says so.
#
# RETIRED-OK: the FIRST version of this curve stood on 13 764 samples from the
# two 7 September drives alone. That is why its middle was empty and its shape
# was wrong. It is void, and none of the numbers below come from it.
#
# Measured envelope (95th percentile of pressure ratio per flow bin, n >= 15):
#     0.021 kg/s -> 1.175      0.194 kg/s -> 2.219
#     0.039 kg/s -> 1.314      0.230 kg/s -> 2.415
#     0.070 kg/s -> 1.537      0.260 kg/s -> 2.287
#     0.105 kg/s -> 1.933      0.289 kg/s -> 2.515
#     0.134 kg/s -> 2.283      0.303 kg/s -> 2.395
#     0.164 kg/s -> 2.353
#
# THE FIT SHAPE CHANGED, AND THAT IS THE POINT. The old quadratic was fitted
# across an empty middle and under-predicted badly once the middle was measured
# (1.53 against 2.28 observed at 0.134 kg/s). Worse, a parabola refitted to the
# filled data turns over and falls above 0.25 kg/s, which no boost ceiling does.
#
# The shipped form is monotone and saturating,
#
#     PR = 1 + a*m / (1 + b*m)
#
# which is the shape the physics gives: pressure ratio climbs with flow until
# the wastegate opens to hold the boost target, then flattens. RMS residual
# against the binned envelope is 0.129 in pressure ratio.
#
# REMAINING GAP: 0.33-0.36 kg/s corrected. Above 0.30 the car is at full
# throttle and does not stay there long enough to log a steady window.

BOOST_CEIL_A, BOOST_CEIL_B = 14.5023, 6.4019      # PR = 1 + A*m/(1 + B*m)
T_REF_CORR, P_REF_CORR = 298.0, 101.3


def corrected_flow(mdot_air_gps, t_inlet_k, p_inlet_kpa):
    """Compressor-corrected mass flow, kg/s — the x-axis of any compressor map."""
    return ((mdot_air_gps * 1e-3) * np.sqrt(t_inlet_k / T_REF_CORR)
            / (p_inlet_kpa / P_REF_CORR))


def boost_ceiling_kpa(mdot_air_gps, t_inlet_k=298.0, p_inlet_kpa=99.3):
    """Highest manifold pressure this vehicle was observed to reach at this flow.

    Returns kPa absolute. Use it to clamp map_kpa so the model cannot invent
    boost the car has never produced.

    t_inlet_k IS THE COMPRESSOR INLET — ambient air, roughly 300-320 K in Jeddah.
    It is NOT "intake air temperature before throttle valve", which is measured
    downstream of the compressor and the intercooler and runs 70-170 C. Passing
    the downstream temperature inflates corrected flow and raises the ceiling by
    about 10 %, which quietly defeats the point of having a ceiling.
    """
    m = corrected_flow(mdot_air_gps, t_inlet_k, p_inlet_kpa)
    pr = 1.0 + BOOST_CEIL_A * m / (1.0 + BOOST_CEIL_B * m)
    return float(p_inlet_kpa * min(pr, 2.6))       # 2.6 = observed peak plus margin


def charge_temperature(t_amb_k, t_block_k=None) -> float:
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
        the raw sensor (107 C median)        | 279.5 kPa    | +23.7 %
        charge_temperature(), THIS FUNCTION  | 232.7 kPa    | +3.0 %
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
    against +3.0 % is a smaller margin than the rhetoric wants. The rejection
    stands anyway, on the same ground: a 3.0 % gap from a model with no
    parameter fitted to the boost channel says more than a closer gap from one
    tuned against it. Report +3.0 %; do not tune it away.

    LIMIT, STATE IT IN CHAPTER 3. There is no measured charge-temperature
    channel on this car: `Temperature after the intercooler` exists in the
    census and reads all-zero on every sample. This is a MODEL of the charge
    temperature, anchored to ambient, not a measurement. The +3.0 % gap over
    587 boosted samples above 200 kPa is the evidence for it and the whole of
    the evidence for it.
    """
    if t_block_k is None:
        return t_amb_k + 12.0
    return t_amb_k + 12.0 + 0.06 * (t_block_k - t_amb_k)


def map_from_airflow(mdot_air_gps, rpm, iat_k, geo=None) -> float:
    """Invert the speed-density relation: given a MEASURED air mass flow, return
    the manifold pressure the model needs.

    Use this instead of a logged pressure channel. Air mass flow has one
    unambiguous unit; the pressure channels on this vehicle do not reconcile
    with physics until the parked-idle test settles them. See the audit, §8.

    Residual fraction depends on manifold pressure, which is what we are solving
    for, so this iterates. Three passes converge to well under 1 %.
    """
    geo = geo or b58()
    eta_v = volumetric_efficiency(rpm)
    map_kpa = 100.0
    for _ in range(6):
        f_res = float(np.clip(0.035 + 6.5 / max(map_kpa, 25.0), 0.03, 0.18))
        denom = eta_v * geo.vd_cyl * (1.0 - f_res) * geo.n_cyl * rpm / 120.0
        if denom <= 0:
            return float("nan")
        rho = (mdot_air_gps * 1e-3) / denom
        map_kpa = float(rho * R_AIR * iat_k / 1000.0)
    return map_kpa


if __name__ == "__main__":
    print("=== A. Naturally aspirated cruise, 2500 rpm, 60 kPa, lambda 1.0 ===")
    for spark in [10, 15, 20, 25, 30, 35, 40]:
        r = run_cycle(Operating(rpm=2500, map_kpa=60, spark_btdc=spark, lam=1.0))
        print(f"  spark {spark:3d} BTDC | T {r.torque_nm:6.1f} Nm | BSFC {r.bsfc_gpkwh:6.1f} "
              f"| MFB50 {r.mfb50_deg:5.1f} | EGT {r.egt_c:5.0f} C | KI {r.knock_integral:5.2f}")

    print("\n=== B. Full load boosted, 3000 rpm, 200 kPa, lambda 0.85 ===")
    for spark in [4, 8, 12, 16, 20, 24]:
        r = run_cycle(Operating(rpm=3000, map_kpa=200, spark_btdc=spark, lam=0.85, p_exh_kpa=230))
        print(f"  spark {spark:3d} BTDC | T {r.torque_nm:6.1f} Nm | BSFC {r.bsfc_gpkwh:6.1f} "
              f"| Pmax {r.p_max_bar:5.1f} bar | EGT {r.egt_c:5.0f} C | KI {r.knock_integral:5.2f} "
              f"| Pknock {r.knock_prob:.2f}")

    print("\n=== C. Lambda sweep at 3000 rpm, 180 kPa, 14 BTDC ===")
    for lam in [0.75, 0.80, 0.85, 0.90, 1.00, 1.10, 1.20]:
        r = run_cycle(Operating(rpm=3000, map_kpa=180, spark_btdc=14, lam=lam, p_exh_kpa=210))
        print(f"  lambda {lam:4.2f} | T {r.torque_nm:6.1f} Nm | BSFC {r.bsfc_gpkwh:6.1f} "
              f"| EGT {r.egt_c:5.0f} C | KI {r.knock_integral:5.2f}")

    print("\n=== D. IAT sensitivity, 3000 rpm, 180 kPa, 16 BTDC, lambda 0.88 ===")
    for iat_c in [15, 25, 35, 45, 55]:
        r = run_cycle(Operating(rpm=3000, map_kpa=180, spark_btdc=16, lam=0.88,
                                iat_k=273.15 + iat_c, p_exh_kpa=210))
        print(f"  IAT {iat_c:3d} C | T {r.torque_nm:6.1f} Nm | EGT {r.egt_c:5.0f} C "
              f"| KI {r.knock_integral:5.2f} | Pknock {r.knock_prob:.2f}")

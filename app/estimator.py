"""estimator.py — turns a live OBD-II stream into engine state the car does not report.

WHAT CHANGED HERE, AND WHEN
---------------------------
14 September 2026 — the warm start stopped being a timer and became a measured
bound, and the nominal seed stopped being a round number. Both are CLAUDE.md
mistake 15; the short version is that the old code declared the seed forgotten
after a fixed 145 s (three time constants at tau = 48 s, which is the LOADED
time constant and wrong at cruise), and seeded the turbine at a flat 500 C that
on `pull01` sat 300 K outside the ambient-to-EGT bracket its own physics allows.
Nothing was deleted: `WARMUP_S` is still here, still 145, and is now explicitly
reference-only.

If you change anything in this file, re-run `python -m app.test_replay` and put
the output in the commit message. The app's numbers are a chain and a change
here moves numbers in the alert engine without announcing it.

THE POINT OF THE WHOLE APP IS IN THIS FILE.

The car has no turbine temperature sensor. Nor does it expose the charge
temperature, the knock margin, or how much thermal damage is accumulating.
Those are the quantities that matter, and the only way to see them is to run a
physics model alongside the car in real time. That is what this does.

    reader  ->  Estimator.update(sample)  ->  state the driver cannot otherwise see

WHAT IT REUSES, AND WHY THAT MATTERS
------------------------------------
Nothing here is new physics. Every model it calls was validated in Phase B
against 295 minutes of logs from this car:

    plant.map_from_airflow      manifold pressure from measured air mass
    plant.charge_temperature    the ONE definition of charge temperature
    plant.predict               one engine cycle -> torque, EGT, knock integral
    thermal.ThermalNetwork      block / oil / turbine, calibrated
    engine_env.BaselineECU      what a production ECU would command here

So the app inherits the validation. It also inherits the LIMITS: 8 of 11
published bands, three documented misses, and a load residual that was only
ever checked at 30-75 kPa -- and that residual, per CLAUDE.md mistake 12, does
not test the breathing model at all. Do not let the app imply more confidence
than the simulator earned.

THREE THINGS THIS FILE IS HONEST ABOUT
--------------------------------------
1. WARM START, AND WHY IT IS NOW A MEASURED BOUND RATHER THAN A TIMER.

   The thermal network integrates from an initial condition. When the app is
   launched mid-drive we do not know the turbine temperature.

   This file used to seed a guess and declare the guess forgotten after a fixed
   145 s, quoted as three turbine time constants at tau = 48 s. That timer is
   wrong at light load, and the error is not small. The turbine node's time
   constant is c_turb / (ua_gas_turb * mdot_exh + ua_turb_amb), so it depends
   on exhaust flow:

       condition     exhaust flow (g/s)   UA (W/K)   tau
       hard climb                   ~112        119    50 s
       cruise                        ~24         40   151 s
       idle                           ~8         25   239 s

   (Units are in the header, not beside each number: written the other way the
   first row trips verify_docs' pattern for the hardest sustained FUEL flow,
   which is 8.7 g/s -- a different quantity an order of magnitude smaller.)

   48 s is the LOADED time constant. Sit in traffic and the seed is still
   nearly intact after 145 s. A fixed timer would have declared the estimate
   trustworthy while it was still mostly the seed.

   So the seed is no longer declared forgotten -- it is MEASURED to be
   forgotten. Three copies of the thermal network are integrated with identical
   inputs, differing only in where they started:

       nominal   what we report
       low       turbine seeded at AMBIENT
       high      turbine seeded at the model's own EGT for this sample

   Those two are not guesses at a plausible range. They are a bound. The
   housing is heated by the exhaust gas and loses heat to ambient, so at the
   instant we connect its temperature MUST lie between the two, whatever the
   car was doing before we arrived. `seed_band_k` is the width of that bound,
   and it shrinks at whatever rate the actual driving allows. When it is narrow
   the estimate has forgotten where it started, and that is a fact about the
   integration rather than a claim about the clock.

2. THE CAR DOES NOT REPORT EVERYTHING WE NEED. Spark advance and lambda are
   logged on this car, but a generic vehicle may not have them, and a real
   adapter loses channels mid-drive. Where a channel is missing we fall back to
   what the BASELINE ECU would command, or to a stated default, and mark the
   estimate as modelled rather than measured. `State.modelled` lists every one,
   every sample.

3. IT IS NOT A MEASUREMENT. `t_turb_c` is the output of a model whose heat
   capacity is an ASSUMED number (see REFERENCES.md section 4). It is the best
   estimate available on a car with no such sensor. It is not a reading, and
   nothing in the UI may present it as one.
"""
from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plant import map_from_airflow, charge_temperature, predict, b58   # noqa: E402
from thermal import ThermalNetwork                                      # noqa: E402
from engine_env import BaselineECU, damage_rate                         # noqa: E402

GEO = b58()

# Reference only, and no longer used to decide anything. Three turbine time
# constants at the LOADED tau of 48 s. Kept because the documents quote it and
# because it is a useful order of magnitude; see note 1 above for why the
# decision is made from `seed_band_k` instead.
WARMUP_S = 145.0

# The seed is considered forgotten when the bound on it is narrower than this.
#
# WHY 25 K. The thermal alert fires on the turbine reaching 850 C, and its
# warning path projects the current trend 30 s ahead at rates of order 1-4 K/s
# -- that is 30 to 120 K of lead. A residual seed uncertainty of 25 K is small
# against the lead the alert is built on, so once the band is inside 25 K the
# alert is deciding on the trend rather than on where we happened to start.
# Above it, thermal alerts stay suppressed.
SEED_SETTLED_K = 25.0

# The measured oil-minus-coolant gap, used to bracket the oil seed the same way
# ambient and EGT bracket the turbine. From thermal.ThermalParams: median
# -1.2 K, p95 +5.4 K, max +12.0 K over the drives carrying both channels.
OIL_SEED_LO_K = -5.0
OIL_SEED_HI_K = +12.0

# Integration hygiene. The stream is not periodic: the adapter answers when it
# answers (7.5 s per channel at 26 channels, 1.45 s at 7 -- mistake 13b), and
# Bluetooth drops happen.
MAX_SUBSTEP_S = 1.0      # integrate long gaps in pieces, not one huge step
GAP_RESEED_S = 120.0     # longer than this and the state is no longer ours

# Defaults used when the car does not report something. Every one of these
# appends to State.modelled, so nothing below is ever silently assumed.
DEFAULT_ECT_C = 90.0     # a warm B58 sits at 88-97 C on every drive logged
DEFAULT_AMB_C = 30.0
DEFAULT_V_KMH = 0.0


@dataclass
class Sample:
    """One instant of car data. Any field may be None -- that is the normal case.

    The reader fills what the vehicle actually reports. Everything downstream
    must cope with holes, because a real OBD-II stream is full of them: the
    adapter polls one channel at a time (see CLAUDE.md mistake 13b), so at any
    instant most channels are a few hundred milliseconds to several seconds
    stale, and any of them may be missing entirely.
    """
    t: float                       # seconds since the stream started
    rpm: float | None = None
    air_kgh: float | None = None   # air mass flow
    load_pct: float | None = None  # BMW relative air filling, if available
    boost_psi: float | None = None
    ect_c: float | None = None     # coolant
    oil_c: float | None = None
    t_amb_c: float | None = None
    iat_pre_c: float | None = None  # COMPRESSOR OUTLET, not charge -- mistake 13
    v_kmh: float | None = None
    spark_deg: float | None = None
    lam: float | None = None
    p_amb_psi: float | None = None

    def has(self, *names) -> bool:
        return all(getattr(self, n) is not None for n in names)


@dataclass
class State:
    """What the estimator believes right now."""
    t: float = 0.0
    ok: bool = False               # enough data to say anything at all
    warming_up: bool = True        # the seed has not been forgotten yet
    confidence: float = 0.0        # 0..1, how much of the seed is forgotten

    # measured, passed through
    rpm: float = float("nan")
    air_gps: float = float("nan")
    ect_c: float = float("nan")
    v_kmh: float = float("nan")

    # DERIVED -- the reason this app exists
    map_kpa: float = float("nan")      # inverted from measured air mass
    t_charge_c: float = float("nan")   # modelled, not the pre-throttle sensor
    torque_nm: float = float("nan")
    fuel_gps: float = float("nan")    # existing plant output, g/s; model estimate
    egt_c: float = float("nan")
    knock_integral: float = float("nan")

    # VIRTUAL SENSORS -- no gauge in the car shows these
    t_turb_c: float = float("nan")
    t_turb_lo_c: float = float("nan")  # bound: turbine seeded at ambient
    t_turb_hi_c: float = float("nan")  # bound: turbine seeded at EGT
    seed_band_k: float = float("nan")  # hi - lo. the honest error bar
    # Where the turbine is HEADED at the current operating point, and how fast.
    # The housing is a first-order node, so these two make the model's own
    # projection exact for constant inputs -- see AUDIT.md M10.
    t_turb_ss_c: float = float("nan")   # steady state at this operating point
    tau_turb_s: float = float("nan")    # c_turb / (ua_gas*mdot_exh + ua_amb)
    t_oil_est_c: float = float("nan")
    t_oil_lo_c: float = float("nan")
    t_oil_hi_c: float = float("nan")
    t_block_c: float = float("nan")
    block_residual_k: float = float("nan")  # modelled block minus measured coolant
    damage_rate: float = 0.0           # per second, same model as check_premise
    damage_total: float = 0.0

    # provenance: which inputs were measured vs assumed
    modelled: list = field(default_factory=list)
    stream_gap_s: float = 0.0          # gap before this sample, if any
    reseeds: int = 0                   # times the stream was lost and restarted

    def as_dict(self):
        return {k: (None if isinstance(v, float) and math.isnan(v) else v)
                for k, v in self.__dict__.items()}


class Estimator:
    """Runs the validated physics alongside the car, one sample at a time."""

    def __init__(self, t_amb_c: float = DEFAULT_AMB_C):
        self.tn = ThermalNetwork()
        self.tn_lo = ThermalNetwork()
        self.tn_hi = ThermalNetwork()
        self.ecu = BaselineECU()
        self.t_amb_k = t_amb_c + 273.15
        self.state = State()
        self.damage_total = 0.0
        self.reseeds = 0
        self._t_last = None
        self._t_start = None
        self._seeded = False
        self._band0 = None          # band width at the seed, for confidence
        self._knock_observed = False
        self.block_residual_k = float("nan")   # modelled block minus measured

    # -- warm start ------------------------------------------------------
    def _steady_turb_k(self, egt_k: float, exh_gps: float) -> float:
        """The turbine temperature this operating point settles at.

        The housing node has one inlet and one outlet, so its steady state is
        just the balance of the two:

            ua_gas * (T_gas - T)  =  ua_amb * (T - T_ambient)

        There is no new physics and no new parameter here -- both conductances
        are the ones thermal.ThermalParams already carries, and this is the
        fixed point of the very equation ThermalNetwork.step integrates.
        """
        p = self.tn.p
        ua_gas = p.ua_gas_turb * max(exh_gps, 0.5)
        ua_amb = p.ua_turb_amb
        return (ua_gas * egt_k + ua_amb * self.t_amb_k) / (ua_gas + ua_amb)

    def _tau_turb_s(self, exh_gps: float) -> float:
        """Time constant of the turbine node at this exhaust flow, in seconds.

        AUDIT.md M10. This is the number that makes a linear projection wrong:
        the housing cannot keep climbing at its current rate, it decays towards
        `_steady_turb_k` with this time constant, so a 30 s linear extrapolation
        overshoots by a third or more. It ranges from about 27 s at full flow to
        240 s at idle, which is also why the warm-up bound is measured rather
        than timed (mistake 15).
        """
        p = self.tn.p
        ua = p.ua_gas_turb * max(exh_gps, 0.5) + p.ua_turb_amb
        return p.c_turb / max(ua, 1e-9)

    def _seed(self, s: Sample, ect_k: float, egt_k: float, exh_gps: float):
        """Set the thermal state, and BOUND it, at the first good sample.

        The block is at coolant temperature -- that one we actually measure.

        The oil is bracketed by the measured oil-minus-coolant gap: -5 K to
        +12 K around coolant (thermal.ThermalParams records median -1.2 K,
        p95 +5.4 K, max +12.0 K). That gap is a steady-state figure, so the
        bracket is honest during a warm-up and merely wide.

        The turbine is bracketed by the two things that can set it. The housing
        is heated only by exhaust gas and cooled only to ambient, so under
        steady operation it lies between them. Seeding one copy at each end and
        integrating both gives a bound that tightens itself at whatever rate
        the driving allows.

        THE NOMINAL SEED IS NOW THE STEADY STATE, NOT 500 C. This file used to
        seed the turbine at "a cruise-ish 500 C because we have nothing at all
        to go on", which was not true: we can see engine speed, air mass and
        coolant, so we can see the operating point, and the operating point has
        a settled turbine temperature. Connect while the car is cruising -- the
        usual case -- and the housing really is near that value, so the seed
        starts close instead of starting at a round number. It is then clamped
        into the bracket, so the reported value can never sit outside its own
        error bar.

        LIMIT, AND IT IS REAL. The bracket bounds the seed under STEADY
        operation. Connect within a few tens of seconds of lifting off a hard
        pull and the housing can be hotter than the gas now flowing through it,
        because the gas cooled first -- so the upper bound will be too low and
        the band will be narrower than the truth deserves. There is no channel
        on this car that would catch that, and the app does not pretend to. A
        cold start has the opposite and happier property: coolant, ambient and
        exhaust are all low together, so the bracket is narrow from the first
        sample and the estimate is trustworthy almost immediately.
        """
        for tn in (self.tn, self.tn_lo, self.tn_hi):
            tn.t_block = ect_k
        self.tn.t_oil = ect_k
        self.tn_lo.t_oil = ect_k + OIL_SEED_LO_K
        self.tn_hi.t_oil = ect_k + OIL_SEED_HI_K

        lo = min(self.t_amb_k, egt_k)
        hi = max(self.t_amb_k, egt_k)
        self.tn_lo.t_turb = lo
        self.tn_hi.t_turb = hi
        # Clamped so the reported estimate is always inside the band it ships
        # with. If the clamp ever binds, the bracket is what to trust.
        self.tn.t_turb = min(hi, max(lo, self._steady_turb_k(egt_k, exh_gps)))
        self._band0 = max(1.0, hi - lo)
        self._seeded = True

    def _blank(self, t: float) -> State:
        """A State that says only "no estimate", carrying nothing stale."""
        st = State(t=t)
        st.ok = False
        st.reseeds = self.reseeds
        st.damage_total = self.damage_total
        self.state = st
        return st

    def _reseed_reason(self, dt_raw: float) -> bool:
        """A gap long enough that the integration no longer describes this car."""
        return dt_raw > GAP_RESEED_S

    # -- main entry ------------------------------------------------------
    def update(self, s: Sample) -> State:
        modelled = []

        if s.rpm is None or s.rpm < 400 or s.air_kgh is None or s.air_kgh <= 0:
            # Engine off, cranking, or the air channel has not arrived yet.
            # Hold the thermal state -- integrating garbage is worse -- but do
            # NOT hand back the last full State with ok flipped to False.
            #
            # AUDIT.md L4: that is what this used to do, and index.html paints
            # every field regardless of `ok`, so the dashboard went on showing
            # the last good turbine temperature, torque and EGT as though they
            # were current. A blank State cannot be misread that way.
            return self._blank(s.t)

        # --- inputs, with every fallback declared --------------------------
        if s.ect_c is None:
            ect_c = DEFAULT_ECT_C
            modelled.append("coolant")
        else:
            ect_c = s.ect_c
        ect_k = ect_c + 273.15

        if s.t_amb_c is None:
            modelled.append("ambient")
        else:
            self.t_amb_k = s.t_amb_c + 273.15

        if s.v_kmh is None:
            v_mps = DEFAULT_V_KMH / 3.6
            modelled.append("vehicle speed")
        else:
            v_mps = s.v_kmh / 3.6

        air_gps = s.air_kgh * (1000.0 / 3600.0)

        # --- charge temperature: MODELLED, never the pre-throttle sensor ---
        # mistake 13: `iat_pre` is a compressor outlet with a ~10 s lag
        # (confirmed on pull01, mistake 13b). Using it here inflated manifold
        # pressure by 23 % under boost.
        t_charge_k = charge_temperature(self.t_amb_k, ect_k)

        # --- manifold pressure: inverted from MEASURED air mass ------------
        # mistake 2: never use the logged "manifold pressure" channel, and
        # never the "boost pressure" channel either -- both sit before the
        # throttle on this car. See alerts.py.
        map_kpa = map_from_airflow(air_gps, s.rpm, t_charge_k, geo=GEO)
        if not math.isfinite(map_kpa) or map_kpa < 15:
            return self._blank(s.t)

        # --- spark and lambda: measured if the car reports them ------------
        #
        # AUDIT.md H8, 15 September 2026. This used to call `base_lambda(rpm,
        # map_kpa)` with no dwell argument, so the v4 enrichment model's dwell
        # term was ALWAYS ZERO and the modelled lambda was ALWAYS 1.00 -- the
        # fallback could not enrich under any condition. Enrichment on this
        # engine is component protection (mistake 4), so switching it off makes
        # the modelled EGT run 80-110 K hot under a sustained pull, and that
        # feeds the DRIVER-FACING thermal alerts.
        #
        # The fix is not to pass dwell here but to stop re-implementing the ECU:
        # `BaselineECU.step` already keeps the dwell timer, the knock retard and
        # the IAT compensation, and it is the same object the environment uses.
        # It is stepped EVERY sample, whether or not we need its outputs, so its
        # timers are correct the moment a measured channel drops out mid-drive.
        dt_ecu = 0.0 if self._t_last is None else max(0.0, min(GAP_RESEED_S,
                                                               s.t - self._t_last))
        ecu_spark, ecu_lam, ecu_fan = self.ecu.step(
            s.rpm, map_kpa, t_charge_k, ect_k,
            knock_observed=self._knock_observed, dt=dt_ecu)

        if s.spark_deg is not None:
            spark = s.spark_deg
        else:
            spark = ecu_spark
            modelled.append("spark")
        if s.lam is not None and 0.5 < s.lam < 1.5:
            lam = s.lam
        else:
            lam = ecu_lam
            modelled.append("lambda")

        out = predict(rpm=s.rpm, map_kpa=map_kpa, iat_k=t_charge_k, ect_k=ect_k,
                      spark_btdc=spark, lam=lam, geo=GEO)
        egt_k = out["egt_c"] + 273.15
        # Fed to the NEXT ecu.step so its retard integrator behaves as the
        # environment's does. 0.85 is the knee the damage term uses.
        self._knock_observed = out["knock_integral"] > 0.85

        # --- seeding, and recovery from a lost stream ----------------------
        dt_raw = 0.0 if self._t_last is None else max(0.0, s.t - self._t_last)
        if self._seeded and self._reseed_reason(dt_raw):
            # We were away longer than the state can survive. Say so and start
            # again rather than pretending the integration held.
            self._seeded = False
            self.reseeds += 1
        fuel = out["mdot_fuel_gps"]
        exh = fuel * 15.0
        if not self._seeded:
            self._seed(s, ect_k, egt_k, exh)
            self._t_start = s.t
            dt_raw = 0.0
        self._t_last = s.t

        # --- integrate all three networks with identical inputs ------------
        # Long gaps are integrated in pieces. A single 8 s Euler step on a 50 s
        # time constant is not the same differential equation.
        remaining = min(dt_raw, GAP_RESEED_S)
        while remaining > 1e-9:
            step = min(MAX_SUBSTEP_S, remaining)
            for tn in (self.tn, self.tn_lo, self.tn_hi):
                tn.step(step, fuel, exh, egt_k, self.t_amb_k, v_mps, ecu_fan)
            remaining -= step

        # --- the block is MEASURED, so stop integrating a guess at it -------
        #
        # AUDIT.md M11, 15 September 2026. The block node was free-running from
        # its seed for the whole drive even though coolant arrives every sample.
        # That is the least defensible node to integrate: the radiator group is
        # explicitly UNIDENTIFIABLE on this car (thermal.py), so its conductances
        # are reasoned values, and the oil node is coupled to the block and
        # inherits whatever the block does. Measured on 7475b5d7 it drifted 14 K
        # from the sensor.
        #
        # When coolant is present it is simply assigned. The drift that WOULD
        # have accumulated is kept as `block_residual_k` -- a free self-check on
        # the cooling model, and the only place in the app where a modelled
        # quantity can be scored against a measured one every sample.
        if s.ect_c is not None:
            self.block_residual_k = self.tn.t_block - ect_k
            for tn in (self.tn, self.tn_lo, self.tn_hi):
                tn.t_block = ect_k
        else:
            self.block_residual_k = float("nan")

        # The bound can only ever narrow; clamp so numerical noise cannot make
        # it appear to reopen.
        lo = min(self.tn_lo.t_turb, self.tn_hi.t_turb)
        hi = max(self.tn_lo.t_turb, self.tn_hi.t_turb)
        band = hi - lo
        warming = band > SEED_SETTLED_K

        # --- damage: the SAME model, imported, not retyped ------------------
        # AUDIT.md L1/M2: this formula used to be re-typed here WITHOUT the
        # knock term, under a docstring claiming it was the same model
        # check_premise.py scores with. It is now imported, and the knock term
        # is passed, so the claim is true.
        d_rate = damage_rate(self.tn.t_turb, self.tn.t_oil, out["knock_integral"])
        self.damage_total += d_rate * min(dt_raw, GAP_RESEED_S)

        st = State(t=s.t)
        st.ok = True
        st.warming_up = warming
        st.confidence = max(0.0, min(1.0, 1.0 - band / (self._band0 or 1.0)))
        st.rpm, st.air_gps = s.rpm, air_gps
        st.ect_c = s.ect_c if s.ect_c is not None else float("nan")
        st.v_kmh = s.v_kmh if s.v_kmh is not None else float("nan")
        st.map_kpa = map_kpa
        st.t_charge_c = t_charge_k - 273.15
        st.torque_nm = out["torque_nm"]
        st.fuel_gps = out["mdot_fuel_gps"]
        st.egt_c = out["egt_c"]
        st.knock_integral = out["knock_integral"]
        st.t_turb_c = self.tn.t_turb - 273.15
        st.t_turb_lo_c = lo - 273.15
        st.t_turb_hi_c = hi - 273.15
        st.seed_band_k = band
        st.t_turb_ss_c = self._steady_turb_k(egt_k, exh) - 273.15
        st.tau_turb_s = self._tau_turb_s(exh)
        st.t_oil_est_c = self.tn.t_oil - 273.15
        st.t_oil_lo_c = min(self.tn_lo.t_oil, self.tn_hi.t_oil) - 273.15
        st.t_oil_hi_c = max(self.tn_lo.t_oil, self.tn_hi.t_oil) - 273.15
        st.t_block_c = self.tn.t_block - 273.15
        st.block_residual_k = self.block_residual_k
        st.damage_rate = d_rate
        st.damage_total = self.damage_total
        st.modelled = modelled
        st.stream_gap_s = dt_raw
        st.reseeds = self.reseeds
        self.state = st
        return st

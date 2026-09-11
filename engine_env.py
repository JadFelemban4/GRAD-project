"""
Gymnasium environment: preference-conditioned, constraint-carrying supervisory
tuner over the BMW B58B30O1 -- a 3.0 L turbocharged INLINE-SIX, the engine
in the 2023 Toyota GR Supra this project logs.

The agent outputs TRIMS relative to a production-representative baseline, so the
zero action reproduces the baseline exactly and reward at zero action is ~0.
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces

from plant import Operating, run_cycle, b58, charge_temperature
from thermal import ThermalNetwork

# The one engine in this project. Passed EXPLICITLY to every run_cycle call
# below -- relying on the default is what let this environment simulate a
# 2.0 L four-cylinder for three weeks. See plant.py's module docstring.
GEO = b58()

# The charge temperature is IMPORTED, not re-typed. Both branches of it used to
# sit inline in reset() and step() as literal arithmetic; plant.charge_temperature
# is the one definition, and a formula that exists in two files drifts in one of
# them. The imported values are identical to what was inlined -- this was a
# de-duplication, not a recalibration, and test_reward.py reports the same
# neutral score before and after.

# ------------------------------------------------------------------ baseline
class BaselineECU:
    """B1: base maps + IAT compensation + knock feedback.

    CALIBRATED AGAINST THE REAL CAR — spark 7 Sep 2026, lambda 8 Sep 2026
    ---------------------------------------------------------------------
    The spark map comes from a 41.8-minute log (3aca2ec1-20260907_072817). The
    lambda strategy comes from 168.1 minutes pooled across eight drives, six of
    which carry usable samples, because the single-drive version of it was wrong
    twice. Two things changed from the original guessed calibration, and both
    matter:

    1. ENRICHMENT IS THERMAL, NOT LOAD-BASED. Over the 1055 samples above
       ENR_LOAD, manifold pressure carries almost nothing about lambda, and the
       little it does carry has the WRONG SIGN for a load table -- +0.23, which
       says more boost goes with a LEANER mixture. What lambda tracks instead is
       engine speed (-0.56), air mass flow (-0.49), and how long the engine has
       been held at high load (-0.47). The car runs stoichiometric through the
       first seconds of a pull at any boost, and never enriches below about
       3300 rpm however long the boost is held. See base_lambda() for the
       measured table and the history of getting this wrong three times.

       Set enrichment_map=True to restore the original guessed map for
       before/after work. Do not do that for the Phase D baseline.

    2. THE SPARK MAP WAS ABOUT 10 DEGREES TOO ADVANCED. Refitted on the eleven
       steady operating points extracted from that drive, holding the IAT
       compensation fixed at its physically correct sign. Residual RMS dropped
       from 8.43 deg to 1.66 deg.

       The clip floor moved from +2 to -10 deg because the real car demonstrably
       retards past TDC: median -1.5 deg at 140-189 % load, minimum -9 deg. A
       baseline that cannot retard past TDC cannot reproduce what this engine
       actually does to protect itself.

    The knock feedback is deliberately asymmetric - pull fast, restore slowly -
    because that is what production strategies do and it changes the dynamics
    the agent has to work against.
    """
    # Fitted 2026-09-07 on 11 steady points, 1551-4185 rpm, 43-79 kPa.
    SPARK_A = 26.18       # was 34.0
    SPARK_B = 0.00695     # was 0.0028   per rpm
    SPARK_C = 0.1307      # was 0.155    per kPa above 40
    SPARK_MIN = -10.0     # was +2.0     measured minimum -9 deg at full load
    SPARK_MAX = 46.0

    def __init__(self, enrichment_map=False):
        self.knock_retard = 0.0
        self.hot_dwell = 0.0
        self.ltft = 0.0
        self.enrichment_map = enrichment_map

    def reset(self):
        self.knock_retard = 0.0
        self.hot_dwell = 0.0
        self.ltft = 0.0

    # Knock-limited spark surface, fitted to plant.run_cycle on a 9x9 grid
    # (1500-5500 rpm, 80-240 kPa, lambda 1, IAT 55 C). Residual RMS 0.95 deg.
    # This is what governs the boosted region -- see base_spark().
    KL_A, KL_B, KL_C, KL_D = 33.636, 0.00641, -0.3673, 0.6385

    def knock_limited_spark(self, rpm, map_kpa):
        return (self.KL_A + self.KL_B * rpm + self.KL_C * map_kpa
                + self.KL_D * map_kpa ** 2 / 1000.0)

    def base_spark(self, rpm, map_kpa):
        """The lesser of the fitted part-load map and the knock limit.

        WHY TWO PIECES. The part-load map is fitted to eleven measured steady
        points spanning 43-79 kPa. Extrapolating that straight line into boost
        would put the baseline at +21 deg at 240 kPa, which no turbocharged
        engine survives -- the real car runs a median of -1.5 deg up there.

        Above the fitted range the production ECU is knock-limited, so the model
        is too: the second term is the knock limit computed from the plant's own
        Douaud-Eyzat integral. The transition is wherever the two cross, which is
        around 90-110 kPa depending on engine speed.

        Do not extend the fitted map upward without steady high-load measurements,
        and steady high-load measurements are not obtainable on a public road.
        """
        fitted = self.SPARK_A + self.SPARK_B * rpm - self.SPARK_C * (map_kpa - 40.0)
        return float(np.clip(min(fitted, self.knock_limited_spark(rpm, map_kpa)),
                             self.SPARK_MIN, self.SPARK_MAX))

    # Enrichment, v4 — fitted 8 Sep 2026 (a.m.) on the dataset as it stood that
    # morning, re-checked the same afternoon against the full 168.1 minutes over
    # eight drives. The structure held and no refit was needed; see base_lambda().
    # Load gates the timer; SPEED and DWELL set the depth.
    # 200.0 until 10 September. The gate is expressed in MANIFOLD PRESSURE, and
    # manifold pressure changed definition when the charge temperature was
    # corrected (plant.charge_temperature). The dataset's MAP had been inverted
    # with the compressor-outlet sensor and was inflated; THIS environment always
    # computed its own MAP from the modelled charge temperature, so the two were
    # on DIFFERENT SCALES the whole time and the gate fired at a physically
    # higher load here than the calibration data intended.
    #
    # 180 kPa on the corrected scale selects exactly the population that 200 kPa
    # selected on the old one -- 1055 samples -- and every fitted figure below
    # reproduces to the decimal: n = 422 / 168 / 465 by speed band, corr with
    # engine speed -0.56, with air mass -0.49, with dwell -0.47. Nothing was
    # refitted. Only the units the gate is written in were corrected.
    #
    # LESSON: a threshold written in a DERIVED quantity silently moves when that
    # quantity's definition changes. Gating on air mass flow, which is measured
    # and did not change, would have been immune. Consider that for v5.
    ENR_LOAD   = 180.0    # kPa; above this the high-load timer runs
    ENR_RPM_LO = 3300.0   # rpm; below this the engine stays stoichiometric
    ENR_RPM_HI = 5200.0   # rpm; full speed authority
    ENR_DWELL_LO = 2.0    # s of sustained high load before enrichment starts
    ENR_DWELL_HI = 9.0    # s at which it is fully applied
    ENR_DEPTH  = 0.19     # lambda deficit at full authority -> floor 0.81

    def base_lambda(self, rpm, map_kpa, dwell_s=0.0):
        """Enrichment is thermal protection, not a load table. MEASURED, THREE TIMES.

        This map has now been wrong in three different ways, and the history is
        the clearest lesson in the project about fitting to too little data.

        v1 (guessed)      enriched from 120 kPa down to 0.82.   too early.
        v2 (7 Sep, a.m.)  lambda 1.00 everywhere.               never enriches.
        v3 (7 Sep, p.m.)  stoichiometric to 207 kPa, then 0.85. right effect,
                          WRONG VARIABLE.  (207 is that breakpoint restated on
                          the corrected charge-temperature pressure scale; it
                          was written as 230 on the old one.)
        v4 (this)         function of engine speed and sustained dwell.

        v3 was fitted to seventeen seconds at high load. The two 8 September
        drives took that to 178 seconds, and with the larger sample manifold
        pressure turns out to carry almost nothing about lambda -- and what it
        does carry has the WRONG SIGN for a load table (+0.23: more boost, LEANER).

        All figures below are over the 1055 samples ABOVE 180 kPa -- the same
        gate ENR_LOAD uses, so the model and its evidence share a threshold.
        180 kPa on the corrected charge-temperature scale selects EXACTLY the
        1055 samples that 200 kPa selected on the old one, so the population
        behind every figure here is unchanged and nothing was refitted; only the
        units the gate is written in were corrected. See ENR_LOAD above.

            corr(lambda, engine speed)              -0.56
            corr(lambda, air mass flow)             -0.49
            corr(lambda, dwell above 180 kPa)       -0.47
            corr(lambda, MANIFOLD PRESSURE)         +0.23   <-- POSITIVE

        Read that last row carefully. It is not merely weak, it is the WRONG WAY
        ROUND for a load table: on these 1055 samples more boost goes with a
        LEANER mixture, not a richer one. A load-gated enrichment map would be
        fitting against the sign of its own evidence.

        RE-CHECKED 8 Sep (afternoon) on a 55-minute drive that added 73 % more
        high-load samples. The structure held and the dwell correlation
        STRENGTHENED to -0.47 -- the smaller sample had been understating the
        very variable this model is built on, so the correction made the case
        for v4 stronger, not weaker. Manifold pressure stayed weak and, on the
        corrected scale, wrong-signed. No refit was needed.

        Median lambda, pooled, above 180 kPa:

            rpm \\ dwell     0-4 s    4-8 s    8+ s      n
            1000-3500 rpm     0.99     0.99    0.98    422
            3500-4500 rpm     0.99     0.98    0.90    168
            4500-7000 rpm     0.98     0.87    0.79    465

        Read across the bottom row: at the same load, the car runs
        stoichiometric for the first seconds of a pull and only enriches once it
        has been up there a while. Read down the first column: at 2000 rpm it
        never enriches no matter how long the boost is held. That is component
        protection scheduled on exhaust enthalpy, which rises with mass flow and
        accumulates with time — not a boost threshold.

        This matters beyond calibration accuracy. Enrichment is one of the
        actions the supervisory agent controls, and it is a THERMAL action. A
        load-only baseline would have enriched on the wrong signal, making the
        agent's advantage look larger than it is for the wrong reason.

        REMAINING LIMITATION. The true schedule uses measured turbine-inlet
        temperature, which this vehicle does not expose. Dwell above 180 kPa is
        a proxy for it. State the proxy in Chapter 3.

        Model against the enlarged table: at 5500 rpm and 12 s dwell it gives
        0.81 against a measured 0.79; at 4500-7000 rpm and 6 s it gives 0.89
        against 0.87; below 3500 rpm it gives 1.00 against 0.98-0.99. The
        weakest cell is 3500-4500 rpm at long dwell, where the model reads 0.93
        against a measured 0.90.
        """
        if self.enrichment_map:            # v1, kept only for before/after work
            if map_kpa <= 120.0:
                return 1.00
            if map_kpa <= 180.0:
                return 1.00 - 0.08 * (map_kpa - 120.0) / 60.0
            return float(np.clip(0.92 - 0.07 * (map_kpa - 180.0) / 60.0, 0.82, 0.92))
        if map_kpa <= self.ENR_LOAD:
            return 1.00
        s = np.clip((rpm - self.ENR_RPM_LO) / (self.ENR_RPM_HI - self.ENR_RPM_LO), 0.0, 1.0)
        t = np.clip((dwell_s - self.ENR_DWELL_LO)
                    / (self.ENR_DWELL_HI - self.ENR_DWELL_LO), 0.0, 1.0)
        return float(1.00 - self.ENR_DEPTH * s * t)

    def iat_compensation(self, iat_k):
        """Pull timing as intake air heats up: the classic compensation table."""
        iat_c = iat_k - 273.15
        return -float(np.clip(0.16 * (iat_c - 25.0), 0.0, 9.0))

    def step(self, rpm, map_kpa, iat_k, ect_k, knock_observed, dt):
        spark = self.base_spark(rpm, map_kpa) + self.iat_compensation(iat_k)
        if ect_k < 340.0:                      # cold: extra retard for catalyst heating
            spark -= 5.0
        if knock_observed:
            self.knock_retard = min(self.knock_retard + 3.0, 12.0)     # fast pull
        else:
            self.knock_retard = max(self.knock_retard - 0.35 * dt, 0.0)  # slow restore
        spark -= self.knock_retard
        # Sustained-high-load timer. This is the proxy for turbine inlet
        # temperature that base_lambda() is scheduled on; it accumulates while
        # the engine is above ENR_LOAD and resets the moment it drops off.
        if map_kpa > self.ENR_LOAD:
            self.hot_dwell += dt
        else:
            self.hot_dwell = 0.0
        lam = self.base_lambda(rpm, map_kpa, self.hot_dwell)
        fan = 1.0 if ect_k > 372.0 else (0.4 if ect_k > 367.0 else 0.0)
        return (float(np.clip(spark, self.SPARK_MIN, self.SPARK_MAX)),
                float(lam), fan)


# ------------------------------------------------------------------ vehicle
class Vehicle:
    mass = 1520.0
    cd_a = 0.66
    crr = 0.011
    wheel_r = 0.33
    final_drive = 3.4
    gears = (3.6, 2.1, 1.4, 1.0, 0.82, 0.68)

    def gear_for(self, v_mps):
        kmh = v_mps * 3.6
        for i, lim in enumerate((22.0, 40.0, 62.0, 88.0, 115.0)):
            if kmh < lim:
                return i
        return 5

    def demand(self, v_mps, accel, grade):
        f = (self.mass * accel
             + 0.5 * 1.2 * self.cd_a * v_mps ** 2
             + self.crr * self.mass * 9.81 * np.cos(np.arctan(grade))
             + self.mass * 9.81 * np.sin(np.arctan(grade)))
        g = self.gear_for(v_mps)
        ratio = self.gears[g] * self.final_drive
        torque = f * self.wheel_r / max(ratio, .1) / 0.92
        rpm = float(np.clip(v_mps / self.wheel_r * ratio * 60.0 / (2 * np.pi), 800.0, 6500.0))
        return float(torque), rpm


# ------------------------------------------------------------------ env
# Torque tracking is always weighted at least this much. See reset().
TRACK_W_MIN = 0.45
TRACK_W_MAX = 0.70

# Torque tracking is a CONSTRAINT wearing the clothes of a reward term.
#
# A purely linear tracking penalty is tradeable: the agent compares the cost of
# a torque shortfall against the damage it avoids, and if the exchange rate is
# favourable it simply refuses to make torque. On the 2.0 L four-cylinder this
# file used to simulate by mistake, the scenario never loaded the engine hard
# enough for that trade to be available, so a linear term with a weight floor
# looked sufficient. On the real 3.0 L six, at a grade that actually loads it,
# the trade came straight back: the starver scored +0.011 against neutral's
# -0.027.
#
# So the penalty now has a tolerance band and a steep hinge beyond it:
#
#     r_resp = -(e + TRACK_HINGE * max(0, e - TRACK_TOL)),   e = |dT| / T_req
#
# TRACK_TOL is a driveability allowance -- 5 % torque error is not something a
# driver notices. TRACK_HINGE is set so the penalty beyond it cannot be bought:
# the largest damage saving physically available is r_life = 1 (all damage
# eliminated) weighted by at most 1 - TRACK_W_MIN = 0.55, while the tracking
# term carries at least TRACK_W_MIN = 0.45. Requiring
#
#     0.45 * (e + TRACK_HINGE * (e - 0.05))  >  0.55   at e = 0.10
#
# gives TRACK_HINGE > 22.4. At 25 the guarantee is:
#
#     NO ACHIEVABLE DAMAGE SAVING PAYS FOR A SUSTAINED TORQUE SHORTFALL
#     BEYOND 10 %.
#
# State that sentence in Chapter 4. It is the reason the Phase D numbers mean
# what they claim to mean. test_reward.py checks it every run.
TRACK_TOL = 0.05
TRACK_HINGE = 25.0

# Turbine protection trigger, shared by every hand-written policy in the repo.
#
# ONE CONSTANT, DERIVED FROM THE DAMAGE MODEL, IMPORTED EVERYWHERE.
#
# The turbine damage term in step() is exp((t_turb - 1123) / 45): 1123 K is the
# knee, above which damage stops being negligible and starts compounding.
# Protecting from there is a statement about the component, so it transfers
# between scenarios without being re-derived.
#
# It used to be a literal 930.0 copy-pasted into check_premise.py and
# generality_test.py. That number was chosen when this file was accidentally
# simulating a 2.0 L four-cylinder; on the real six the turbine reaches 1152 K,
# so a 930 K trigger is active from the first second, both policies saturate,
# and the gap between them collapses for reasons unrelated to preview. Worse,
# the two files could drift apart and quietly report different experiments.
#
# If you change the damage model, change this with it. They are the same number.
TURB_PROTECT_K = 1123.0

ACT_LO = np.array([-8.0, -0.15, -40.0, 0.0, 0.3], dtype=np.float32)
ACT_HI = np.array([+4.0, +0.06, +15.0, 1.0, 1.0], dtype=np.float32)
SLEW = np.array([1.5, 0.03, 10.0, 0.25, 0.2], dtype=np.float32)

PREVIEW_S = (2.0, 5.0, 15.0, 30.0)
OBS_DIM = 23


class SupervisoryTunerEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, cycle, engine_model=None, dt=0.2,
                 use_preview=True, uncertainty_beta=1.0, seed=None):
        super().__init__()
        self.cycle = cycle                      # dict: t, v_mps, grade, t_amb
        self.engine = engine_model              # None -> use the physics plant
        self.dt = dt
        self.use_preview = use_preview
        self.beta = uncertainty_beta
        self.rng = np.random.default_rng(seed)

        self.veh = Vehicle()
        self.ecu = BaselineECU()
        self.thermal = ThermalNetwork()
        self.thermal_base = ThermalNetwork()

        # network sees [-1,1]; the env rescales
        self.action_space = spaces.Box(-1.0, 1.0, shape=(5,), dtype=np.float32)
        self.observation_space = spaces.Box(-10.0, 10.0, shape=(OBS_DIM,), dtype=np.float32)

    # -------------------------------------------------------------- helpers
    def _rescale(self, a):
        a = np.clip(a, -1.0, 1.0)
        return ACT_LO + (a + 1.0) * 0.5 * (ACT_HI - ACT_LO)

    def _evaluate(self, rpm, map_kpa, iat_k, ect_k, spark, lam):
        """One engine evaluation. Physics plant, or surrogate if supplied."""
        if self.engine is not None:
            return self.engine.predict(rpm, map_kpa, iat_k, ect_k, spark, lam)
        r = run_cycle(Operating(rpm=rpm, map_kpa=map_kpa, iat_k=iat_k, ect_k=ect_k,
                                spark_btdc=spark, lam=lam,
                                p_exh_kpa=max(105.0, map_kpa * 1.12)), geo=GEO)
        return dict(torque=r.torque_nm, mdot_fuel=r.mdot_fuel_gps,
                    egt_k=r.egt_c + 273.15, ki=r.knock_integral, unc=0.0)

    # Hard ceiling on manifold pressure, MEASURED not guessed. Across 43 853
    # quasi-steady samples from eight drives -- with the saturated MAF samples
    # excluded -- the highest pressure ratio the car reached is 2.52, which
    # against a 99.3 kPa inlet is 250 kPa absolute. This replaces the 240 that
    # used to sit here as a round number. See plant.boost_ceiling_kpa for the
    # flow-dependent version of the same envelope.
    MAP_CEIL_KPA = 250.0

    def _map_for(self, torque_req, rpm, boost_trim):
        """Open-loop feed-forward guess at the manifold pressure for a torque."""
        base = 40.0 + 0.62 * max(torque_req, 0.0)
        return float(np.clip(base + boost_trim, 25.0, self.MAP_CEIL_KPA))

    def _track_torque(self, torque_req, rpm, iat_k, ect_k, spark, lam,
                      boost_trim, state):
        """Inner load loop: a PI controller on manifold pressure that makes
        delivered torque follow demand.

        Real ECUs are structured this way - the driver's pedal becomes a torque
        request, the torque request becomes an airflow target, and throttle and
        wastegate close the loop. Without this the supervisory agent inherits a
        torque error it cannot fix with spark and lambda alone, and the tracking
        constraint is violated from the first step for reasons that have nothing
        to do with the policy.
        """
        ff = self._map_for(torque_req, rpm, boost_trim)
        mp = float(np.clip(state.get("map", ff), 25.0, self.MAP_CEIL_KPA + boost_trim))
        out = None
        for _ in range(3):                       # 3 inner iterations is plenty
            out = self._evaluate(rpm, mp, iat_k, ect_k, spark, lam)
            err = torque_req - out["torque"]
            state["i"] = float(np.clip(state.get("i", 0.0) + 0.05 * err, -60.0, 60.0))
            mp = float(np.clip(mp + 0.35 * err + state["i"] * 0.02,
                               25.0, min(self.MAP_CEIL_KPA, 200.0 + boost_trim)))
        state["map"] = mp
        return out, mp

    def _preview(self):
        out = []
        for h in PREVIEW_S:
            j = min(self.k + int(h / self.dt), len(self.cycle["grade"]) - 1)
            out.append(self.cycle["grade"][j] if self.use_preview else 0.0)
        return out

    def _obs(self):
        c = self.cycle
        t = self.thermal.state()
        o = [
            self.rpm / 3000.0 - 1.0,
            self.map_kpa / 120.0 - 1.0,
            self.tps,
            self.spark / 20.0 - 1.0,
            (self.lam - 1.0) * 8.0,
            (t[0] - 363.0) / 25.0,
            (t[1] - 373.0) / 30.0,
            (t[2] - 873.0) / 200.0,
            (self.iat_k - 303.0) / 25.0,
            (c["t_amb"] - 293.0) / 15.0,
            (c.get("p_baro", 101.3) - 101.3) / 8.0,
            c.get("humidity", 0.01) * 40.0 - 0.5,
            self.v / 25.0 - 1.0,
            c["grade"][self.k] * 12.0,
        ]
        o += [g * 12.0 for g in self._preview()]
        o += [
            self.torque_req / 200.0 - 1.0,
            self.aggression,
            float(self.w[0]), float(self.w[1]), float(self.w[2]),
        ]
        return np.clip(np.asarray(o, dtype=np.float32), -10.0, 10.0)

    # -------------------------------------------------------------- api
    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        self.k = 0
        self.ecu.reset()
        t_amb = self.cycle["t_amb"]
        self.thermal.reset(t_amb=t_amb, warm=True)
        self.thermal_base.reset(t_amb=t_amb, warm=True)

        # Preference vector: resampled every episode so one agent spans the front.
        #
        # TRACKING IS NOT A PREFERENCE. w[0] weights torque tracking, and an
        # unconstrained Dirichlet over three terms lets it land near zero -- on
        # those episodes refusing to make torque becomes free, and a policy that
        # pins boost trim to minimum outscores neutral by two orders of
        # magnitude. That is a reward hack, and test_reward.py catches it.
        #
        # Delivering the requested torque is the job. How you trade fuel against
        # component life is the preference. So w[0] gets a floor and the
        # remainder is split over fuel and life, which is the two-dimensional
        # trade-off the Pareto stretch goal actually needs.
        w_track = float(TRACK_W_MIN + (TRACK_W_MAX - TRACK_W_MIN) * self.rng.random())
        w_rest = self.rng.dirichlet(np.ones(2)) * (1.0 - w_track)
        self.w = np.array([w_track, w_rest[0], w_rest[1]], dtype=np.float32)

        self.prev_act = np.zeros(5, dtype=np.float32)
        self.pi_base, self.pi_agent = {}, {}
        self.knock_flag_base = False
        self.v = float(self.cycle["v_mps"][0])
        self.rpm, self.map_kpa, self.tps = 900.0, 40.0, 0.0
        self.spark, self.lam = 20.0, 1.0
        self.iat_k = charge_temperature(t_amb)
        self.torque_req, self.aggression = 0.0, 0.0
        self.ep = dict(fuel=0.0, fuel_base=0.0, damage=0.0, damage_base=0.0,
                       knock_events=0, torque_viol=0.0, egt_viol=0.0, steps=0)
        return self._obs(), {}

    def step(self, action):
        c = self.cycle
        n = len(c["v_mps"])
        raw = self._rescale(np.asarray(action, dtype=np.float32))
        act = np.clip(raw, self.prev_act - SLEW, self.prev_act + SLEW)
        act = np.clip(act, ACT_LO, ACT_HI)

        # --- driver demand -------------------------------------------------
        self.v = float(c["v_mps"][self.k])
        nxt = float(c["v_mps"][min(self.k + 1, n - 1)])
        accel = (nxt - self.v) / self.dt
        grade = float(c["grade"][self.k])
        self.torque_req, self.rpm = self.veh.demand(self.v, accel, grade)
        self.aggression = float(np.clip(abs(accel) / 2.5, 0.0, 1.0))
        self.iat_k = charge_temperature(c["t_amb"], self.thermal.t_block)

        # --- baseline controller (runs in parallel, defines the reference) ---
        sp_b, lam_b, fan_b = self.ecu.step(self.rpm, self._map_for(self.torque_req, self.rpm, 0.0),
                                           self.iat_k, self.thermal_base.t_block,
                                           self.knock_flag_base, self.dt)
        base, map_b = self._track_torque(self.torque_req, self.rpm, self.iat_k,
                                         self.thermal_base.t_block, sp_b, lam_b,
                                         0.0, self.pi_base)
        self.knock_flag_base = base["ki"] > 1.0
        self.thermal_base.step(self.dt, base["mdot_fuel"], base["mdot_fuel"] * 15.0,
                               base["egt_k"], c["t_amb"], self.v, fan_b)

        # --- agent ---------------------------------------------------------
        # Same bounds as the baseline. If the agent is floored at 0 while the
        # baseline may retard to -10, the neutral action stops being neutral and
        # every baseline-relative reward term is silently offset.
        self.spark = float(np.clip(sp_b + act[0],
                                   BaselineECU.SPARK_MIN, BaselineECU.SPARK_MAX))
        self.lam = float(np.clip(lam_b + act[1], 0.70, 1.25))
        out, self.map_kpa = self._track_torque(self.torque_req, self.rpm, self.iat_k,
                                               self.thermal.t_block, self.spark, self.lam,
                                               act[2], self.pi_agent)
        self.tps = float(np.clip(self.map_kpa / self.MAP_CEIL_KPA, 0.0, 1.0))
        self.thermal.step(self.dt, out["mdot_fuel"], out["mdot_fuel"] * 15.0,
                          out["egt_k"], c["t_amb"], self.v, act[3], act[4])

        # --- damage rates ---------------------------------------------------
        def damage(tn, ki):
            d = np.exp((tn.t_turb - 1123.0) / 45.0) + 0.4 * np.exp((tn.t_oil - 408.0) / 12.0)
            return float(d + 40.0 * max(0.0, ki - 0.85) ** 2)

        d_a = damage(self.thermal, out["ki"])
        d_b = damage(self.thermal_base, base["ki"])

        # --- reward: every term baseline-relative and dimensionless ---------
        eps = 1e-6
        r_fuel = (base["mdot_fuel"] - out["mdot_fuel"]) / (base["mdot_fuel"] + eps)
        r_life = (d_b - d_a) / (d_b + 0.05)
        t_ref = max(self.torque_req, 40.0)
        e_track = abs(self.torque_req - out["torque"]) / t_ref
        r_resp = -(e_track + TRACK_HINGE * max(0.0, e_track - TRACK_TOL))

        smooth = float(np.sum(((act - self.prev_act) / (ACT_HI - ACT_LO)) ** 2))
        reward = (self.w[1] * r_fuel + self.w[2] * r_life + self.w[0] * r_resp
                  - self.beta * out.get("unc", 0.0) - 0.05 * smooth)

        # --- constraint costs ------------------------------------------------
        c_torque = max(0.0, abs(self.torque_req - out["torque"]) / t_ref - 0.03)
        c_knock = 1.0 if out["ki"] > 1.0 else 0.0
        c_egt = max(0.0, out["egt_k"] - 1223.0) / 100.0

        # --- bookkeeping ------------------------------------------------------
        e = self.ep
        e["fuel"] += out["mdot_fuel"] * self.dt
        e["fuel_base"] += base["mdot_fuel"] * self.dt
        e["damage"] += d_a * self.dt
        e["damage_base"] += d_b * self.dt
        e["knock_events"] += int(c_knock)
        e["torque_viol"] += c_torque
        e["egt_viol"] += c_egt
        e["steps"] += 1

        self.prev_act = act
        self.k += 1
        terminated = not np.isfinite(reward)          # simulation divergence only
        truncated = self.k >= n - 1

        info = dict(cost_torque=c_torque, cost_knock=c_knock, cost_egt=c_egt,
                    torque=out["torque"], torque_req=self.torque_req,
                    egt_c=out["egt_k"] - 273.15, ki=out["ki"],
                    spark=self.spark, lam=self.lam,
                    t_turb=self.thermal.t_turb, t_oil=self.thermal.t_oil,
                    r_fuel=r_fuel, r_life=r_life, r_resp=r_resp)
        if truncated or terminated:
            info["episode_summary"] = dict(e)
        return self._obs(), float(reward), bool(terminated), bool(truncated), info


# ------------------------------------------------------------------ cycles
def make_grade_climb(duration=900.0, dt=0.2, t_amb=315.0, grade=0.12, v_kmh=110.0):
    """Sustained mountain grade at motorway speed, 42 C ambient.

    THE DEFAULTS CHANGED ON 8 SEPTEMBER, AND THE REASON IS THE ENGINE.

    They were 10 % at 90 km/h, which asks a 1520 kg car for 244 Nm. That loaded
    the 2.0 L four-cylinder this file used to simulate by mistake. The real
    B58 makes 500 Nm and answers 244 Nm at about 130 kPa -- well inside its
    range, with the boost ceiling never approached. The torque constraint
    therefore never bound, and a scenario where the constraint never binds
    cannot show a torque-versus-damage trade-off, which is the entire subject
    of the project.

    12 % at 110 km/h asks 297 Nm, 59 % of peak torque, held for twelve minutes
    in 42 C air. That is a real sustained climb, it loads the real engine, and
    the constraint binds. Phase D's evaluation protocol should fix these numbers
    and never move them again.
    """
    n = int(duration / dt)
    t = np.arange(n) * dt
    v = np.full(n, v_kmh / 3.6)
    v[:int(20 / dt)] = np.linspace(0.0, v_kmh / 3.6, int(20 / dt))
    g = np.zeros(n)
    g[int(180 / dt):] = grade                    # 3 min flat, then the climb
    return dict(t=t, v_mps=v, grade=g, t_amb=t_amb, p_baro=101.3, humidity=0.012)


# ---------------------------------------------------------------------------
# Convenience alias + default constructor
# ---------------------------------------------------------------------------
# The handbook and the roles document refer to this environment as "EngineEnv".
# Keep both names working: the descriptive one for the code, the short one for
# the documents and for anything written from them.

def EngineEnv(cycle=None, **kw):
    """SupervisoryTunerEnv with a sensible default scenario.

    EngineEnv()  ->  the 900 s grade climb at 42 C, which is the standard
    evaluation scenario. Pass your own cycle dict to override it.
    """
    return SupervisoryTunerEnv(cycle if cycle is not None else make_grade_climb(), **kw)


def neutral_action():
    """The action vector that means 'do exactly what the baseline ECU would do'.

    NOT zeros. The network sees [-1, 1] and the env rescales, so a do-nothing
    trim sits wherever zero happens to fall in that range.

    THE FIVE ACTIONS ARE NOT THE SAME KIND OF THING. Actions 0-2 are TRIMS
    added to what the baseline commands, so their neutral value is 0. Actions
    3 and 4 are ABSOLUTE DUTIES -- cooling fan and coolant pump -- and their
    neutral is what the baseline runs, not zero.

    This function used to map all five to "zero", which put the fan OFF and the
    pump at its 0.3 floor, and returned -1.857 for the pump: outside the
    Box(-1, 1) action space it claims to sample from. That is not a neutral
    policy, it is a policy with the cooling disabled, and it drags every
    baseline-relative reward term negative for a reason that has nothing to do
    with the reward. `test_reward.py` carried a local `true_neutral()` fixing
    this; the fix belongs here, where the mistake was.

    CAVEAT, STATE IT RATHER THAN HIDE IT. The baseline's fan is SCHEDULED on
    coolant temperature (off / 0.4 / 1.0 -- see BaselineECU.step), so no single
    constant action reproduces it over a whole episode. 1.0 is the value it
    holds once the engine is hot, which is the part of the episode the
    constraint binds in. Exactly neutral during the climb, slightly
    over-cooled during the first three minutes of flat running.
    """
    a = 2.0 * (0.0 - ACT_LO) / (ACT_HI - ACT_LO) - 1.0
    a[3] = 2.0 * (1.0 - ACT_LO[3]) / (ACT_HI[3] - ACT_LO[3]) - 1.0     # fan  1.0
    a[4] = 2.0 * (1.0 - ACT_LO[4]) / (ACT_HI[4] - ACT_LO[4]) - 1.0     # pump 1.0
    return np.clip(a, -1.0, 1.0).astype(np.float32)


if __name__ == "__main__":
    from gymnasium.utils.env_checker import check_env

    env = SupervisoryTunerEnv(make_grade_climb(duration=60.0), seed=0)
    check_env(env, skip_render_check=True)
    print("env_checker: PASS")

    # A SMOKE TEST, NOT THE REWARD CHECK. This rolls 40 s of flat cruise. The
    # grade in make_grade_climb() starts at t = 180 s, so nothing here ever gets
    # hot, no constraint binds, and the mean reward is NOT the neutral-action
    # figure. It reads about -0.05 for a reason that has nothing to do with the
    # reward: cold engine, baseline still warming, torque tracking dominated by
    # transients. Quoting it as "neutral scores -0.06" was wrong, and it is the
    # exact mistake test_reward.py's docstring was written to prevent.
    #
    # The real check is `python test_reward.py`, which runs 300 s so the episode
    # actually contains the climb, and reports neutral at -0.004.
    obs, _ = env.reset(seed=1)
    neutral = neutral_action()
    assert env.action_space.contains(neutral), "neutral action outside action space"
    rs = []
    for _ in range(200):
        obs, r, term, trunc, info = env.step(neutral)
        rs.append(r)
        if term or trunc:
            break
    print(f"smoke test: {len(rs)} steps of flat cruise, mean reward {np.mean(rs):+.5f}")
    print(f"final torque {info['torque']:.1f} Nm vs demand {info['torque_req']:.1f} Nm")
    print(f"EGT {info['egt_c']:.0f} C | turbine {info['t_turb']-273.15:.0f} C | KI {info['ki']:.2f}")
    print("this is NOT the neutral-reward check -- run test_reward.py for that")

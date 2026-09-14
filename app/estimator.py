"""estimator.py — turns a live OBD-II stream into engine state the car does not report.

THE POINT OF THE WHOLE APP IS IN THIS FILE.

The car has no turbine temperature sensor. Nor does it expose the charge
temperature, the knock margin, or how much thermal damage is accumulating.
Those are the quantities that matter, and the only way to see them is to run a
physics model alongside the car in real time. That is what this does.

    reader  ->  Estimator.update(sample)  ->  state the driver cannot otherwise see

WHAT IT REUSES, AND WHY THAT MATTERS
------------------------------------
Nothing here is new physics. Every model it calls was validated in Phase B
against 175 minutes of logs from this car:

    plant.map_from_airflow      manifold pressure from measured air mass
    plant.charge_temperature    the ONE definition of charge temperature
    plant.predict               one engine cycle -> torque, EGT, knock integral
    thermal.ThermalNetwork      block / oil / turbine, calibrated
    engine_env.BaselineECU      what a production ECU would command here

So the app inherits the validation. It also inherits the LIMITS: 8 of 11
published bands, three documented misses, and a load residual that was only
ever checked at 30-74 kPa. Do not let the app imply more confidence than the
simulator earned.

THREE THINGS THIS FILE IS HONEST ABOUT
--------------------------------------
1. WARM START. The thermal network integrates from an initial condition. When
   the app is launched mid-drive we do not know the turbine temperature. We
   seed from coolant temperature and report LOW CONFIDENCE until roughly three
   turbine time constants have passed (~145 s). Anything shown before that is
   a guess converging on an answer.

2. THE CAR DOES NOT REPORT EVERYTHING WE NEED. Spark advance and lambda are
   logged on this car, but a generic vehicle may not have them. Where a channel
   is missing we fall back to what the BASELINE ECU would command, and mark the
   estimate as modelled rather than measured. Every output carries that flag.

3. IT IS NOT A MEASUREMENT. `t_turb_c` is the output of a model whose heat
   capacity is an ASSUMED number (see REFERENCES.md section 4). It is the best
   estimate available on a car with no such sensor. It is not a reading.
"""
from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plant import map_from_airflow, charge_temperature, predict, b58   # noqa: E402
from thermal import ThermalNetwork                                      # noqa: E402
from engine_env import BaselineECU                                      # noqa: E402

GEO = b58()

# Three turbine time constants. tau = 48 s measured, so the thermal state has
# forgotten its initial condition to within 5 % after this long.
WARMUP_S = 145.0


@dataclass
class Sample:
    """One instant of car data. Any field may be None -- that is the normal case.

    The reader fills what the vehicle actually reports. Everything downstream
    must cope with holes, because a real OBD-II stream is full of them: the
    adapter polls one channel at a time (see CLAUDE.md mistake 8 and 13b), so
    at any instant most channels are a few hundred milliseconds stale.
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
    warming_up: bool = True        # thermal state has not forgotten its seed
    confidence: float = 0.0        # 0..1, how much to trust the thermal numbers

    # measured, passed through
    rpm: float = float("nan")
    air_gps: float = float("nan")
    ect_c: float = float("nan")
    v_kmh: float = float("nan")

    # DERIVED -- the reason this app exists
    map_kpa: float = float("nan")      # inverted from measured air mass
    t_charge_c: float = float("nan")   # modelled, not the pre-throttle sensor
    torque_nm: float = float("nan")
    egt_c: float = float("nan")
    knock_integral: float = float("nan")

    # VIRTUAL SENSORS -- no gauge in the car shows these
    t_turb_c: float = float("nan")
    t_oil_est_c: float = float("nan")
    t_block_c: float = float("nan")
    damage_rate: float = 0.0           # per second, same model as check_premise
    damage_total: float = 0.0

    # provenance: which inputs were measured vs assumed
    modelled: list = field(default_factory=list)

    def as_dict(self):
        d = {k: (None if isinstance(v, float) and math.isnan(v) else v)
             for k, v in self.__dict__.items()}
        return d


class Estimator:
    """Runs the validated physics alongside the car, one sample at a time."""

    def __init__(self, t_amb_c: float = 30.0):
        self.tn = ThermalNetwork()
        self.ecu = BaselineECU()
        self.t_amb_k = t_amb_c + 273.15
        self.state = State()
        self._t_last = None
        self._t_start = None
        self._seeded = False
        self.knock_flag = False

    # -- warm start ------------------------------------------------------
    def _seed(self, s: Sample):
        """Set the thermal state from what we can see at the first good sample.

        The block is at coolant temperature -- that one we actually measure.
        The oil we assume equals coolant, which is true within a few kelvin at
        steady state (measured median gap -1.2 K over three drives) but wrong
        during a warm-up. The turbine we seed at a cruise-ish 500 C because we
        have nothing at all to go on.

        This is why `warming_up` exists. Do not present turbine temperature to
        anyone during the first ~145 s as though it were known.
        """
        ect = s.ect_c if s.ect_c is not None else 90.0
        self.tn.t_block = ect + 273.15
        self.tn.t_oil = ect + 273.15
        self.tn.t_turb = 773.0
        if s.t_amb_c is not None:
            self.t_amb_k = s.t_amb_c + 273.15
        self._seeded = True

    # -- main entry ------------------------------------------------------
    def update(self, s: Sample) -> State:
        st = State(t=s.t)
        modelled = []

        if s.rpm is None or s.rpm < 400 or s.air_kgh is None or s.air_kgh <= 0:
            # Engine off, cranking, or the air channel has not arrived yet.
            # Hold the previous thermal state rather than integrating garbage.
            self.state.t = s.t
            self.state.ok = False
            return self.state

        if not self._seeded:
            self._seed(s)
            self._t_start = s.t

        if s.t_amb_c is not None:
            self.t_amb_k = s.t_amb_c + 273.15

        dt = 0.0 if self._t_last is None else max(0.0, min(2.0, s.t - self._t_last))
        self._t_last = s.t

        air_gps = s.air_kgh * (1000.0 / 3600.0)
        ect_k = (s.ect_c if s.ect_c is not None else 90.0) + 273.15
        if s.ect_c is None:
            modelled.append("coolant")

        # --- charge temperature: MODELLED, never the pre-throttle sensor ---
        # mistake 13: `iat_pre` is a compressor outlet with a ~10 s lag. Using
        # it here inflated manifold pressure by 23 % under boost.
        t_charge_k = charge_temperature(self.t_amb_k, ect_k)

        # --- manifold pressure: inverted from MEASURED air mass ------------
        # mistake 2: never use the logged "manifold pressure" channel.
        map_kpa = map_from_airflow(air_gps, s.rpm, t_charge_k, geo=GEO)
        if not math.isfinite(map_kpa) or map_kpa < 15:
            self.state.ok = False
            return self.state

        # --- spark and lambda: measured if the car reports them ------------
        if s.spark_deg is not None:
            spark = s.spark_deg
        else:
            spark = self.ecu.base_spark(s.rpm, map_kpa)
            modelled.append("spark")
        if s.lam is not None and 0.5 < s.lam < 1.5:
            lam = s.lam
        else:
            lam = self.ecu.base_lambda(s.rpm, map_kpa)
            modelled.append("lambda")

        out = predict(rpm=s.rpm, map_kpa=map_kpa, iat_k=t_charge_k, ect_k=ect_k,
                      spark_btdc=spark, lam=lam, geo=GEO)

        # --- integrate the thermal network ---------------------------------
        if dt > 0:
            fan = 1.0 if self.tn.t_block > 373.0 else 0.0
            self.tn.step(dt, out["mdot_fuel_gps"], out["mdot_fuel_gps"] * 15.0,
                         out["egt_c"] + 273.15, self.t_amb_k,
                         (s.v_kmh or 0.0) / 3.6, fan)

        # --- damage: the SAME model check_premise.py scores with -----------
        d_rate = (math.exp((self.tn.t_turb - 1123.0) / 45.0)
                  + 0.4 * math.exp((self.tn.t_oil - 408.0) / 12.0))
        self.state.damage_total += d_rate * dt

        elapsed = s.t - (self._t_start or s.t)
        warming = elapsed < WARMUP_S

        st.ok = True
        st.warming_up = warming
        st.confidence = min(1.0, elapsed / WARMUP_S)
        st.rpm, st.air_gps = s.rpm, air_gps
        st.ect_c = s.ect_c if s.ect_c is not None else float("nan")
        st.v_kmh = s.v_kmh if s.v_kmh is not None else float("nan")
        st.map_kpa = map_kpa
        st.t_charge_c = t_charge_k - 273.15
        st.torque_nm = out["torque_nm"]
        st.egt_c = out["egt_c"]
        st.knock_integral = out["knock_integral"]
        st.t_turb_c = self.tn.t_turb - 273.15
        st.t_oil_est_c = self.tn.t_oil - 273.15
        st.t_block_c = self.tn.t_block - 273.15
        st.damage_rate = d_rate
        st.damage_total = self.state.damage_total
        st.modelled = modelled
        self.state = st
        return st

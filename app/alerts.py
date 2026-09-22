"""alerts.py — the three kinds of irregular state, and what to do about each.

WHAT CHANGED HERE, AND WHEN
---------------------------
14 September 2026 — the mismatch detector was rebuilt. It was comparing two
sides of the throttle plate and firing on 95.7 % of a normal drive; the long
note further down records the whole investigation, and CLAUDE.md mistake 14 is
the summary. The threshold also moved, 15 % -> 25 %, for a measured reason that
is written beside the constant. Nothing was removed: the three alert types, their
audiences and the 1123 K / 408 K limits are unchanged.

THIS IS THE ONLY FILE THAT WRITES TO DISK.

Raw car data is never stored (see reader.py). What gets persisted is what the
model MARKS: an event, its evidence, and the advice given. That file is what a
workshop or fleet owner reads afterwards. Nothing here writes a sample stream,
and the evidence dictionaries are a handful of scalars per event by design.

THE THREE TYPES ARE GENUINELY DIFFERENT, AND THEY HAVE DIFFERENT AUDIENCES
--------------------------------------------------------------------------

  THERMAL   the estimated turbine or oil temperature is heading for the knee of
            the damage curve.
            -> THE DRIVER, now. This is the only type that should interrupt
               someone who is driving.

  MISMATCH  the car is not behaving the way the validated model says it should:
            measured air mass disagrees with the car's own pressure sensor.
            -> A MECHANIC, afterwards. This is a diagnostic, not an emergency.
               A boost leak, a drifting MAF and a sticking wastegate all look
               like this, and none of them needs the driver's attention at
               110 km/h.

  NOVEL     the engine is somewhere our 295 minutes of data never went.
            -> US. It means the estimate is extrapolating and should be trusted
               less. It is a confidence flag, not a fault.

Keeping them separate is what makes the app defensible. One undifferentiated
"something is wrong" light would be worthless to all three audiences.

WHY THE THRESHOLDS ARE WHAT THEY ARE
------------------------------------
Every number below traces to something this project measured. Where a number
changed, the measurement that changed it is recorded beside it.

  1123 K      the knee of the turbine damage term, exp((T-1123)/45). The same
              constant check_premise.py scores with -- deliberately the same
              number, imported from one place.
  408 K       the oil term's knee in the same damage model.
  30-75 kPa   the manifold pressure range the model was actually validated at.
              RETIRED-OK: 31, 82 -- the pre-correction span, kept as history:
              CLAUDE.md mistake 13 moved the range here from 31-82 kPa, the
              span on the compressor-outlet sensor. Outside it we are
              extrapolating and say so.

The mismatch numbers have their own section below, because the detector this
file shipped with was measuring the wrong thing.

DO NOT TUNE THESE TO MAKE THE DEMO LOOK GOOD. If a threshold changes, the
reason has to be a measurement, and it goes in the docstring.


THE MISMATCH DETECTOR WAS COMPARING TWO SIDES OF THE THROTTLE PLATE
------------------------------------------------------------------
Investigated 14 September 2026, on the replay of 7475b5d7 and then on all nine
drives. This is CLAUDE.md mistake 2 recurring in a third channel, and it is
worth reading before touching anything below.

The detector compared the manifold pressure INVERTED from measured air mass
against the pressure computed from the car's own `Boost pressure` channel. It
reported 55 events on 7475b5d7, which looked like an over-sensitive threshold.

It was not. The condition was true for 13669 of 14278 samples -- 95.7 % of the
drive -- at a median disagreement of -52 %. It only produced 55 events because
a 60 s cooldown was collapsing a continuous, systematic disagreement into a
handful of discrete-looking ones. A detector that fires on 96 % of normal
driving is not sensitive, it is measuring something else.

What it was measuring: `Boost pressure` on this vehicle, like `Intake manifold
absolute pressure` before it (mistake 2), sits BEFORE THE THROTTLE. At part
throttle the pressure before the plate and the pressure after it are physically
different quantities, and the throttle is what makes them different. Binned by
the logged throttle angle on 7475b5d7:

    throttle   0-25 %   n=13431   median  -52.5 %    98.8 % over the old 15 %
    throttle  25-50 %   n=  222   median  -61.1 %    90.1 %
    throttle 90-100 %   n=  236   median  -33.1 %    59.3 %

and binned by the pre-throttle pressure itself:

    logged  90-110 kPa  n= 8538   median  -56.7 %
    logged 110-130 kPa  n= 4782   median  -44.0 %
    logged 200-250 kPa  n=  157   median   +7.7 %     8.3 % over

The -52 % is not a fault and never was. It is the throttle doing its job, and
it is the same 44-52 % that CLAUDE.md mistake 14 records for the steady points
as they stood then (RETIRED-OK: 22 -- measured over 22 points; 26 today). The
comparison is only valid where the throttle is not restricting -- that is, at
wide-open throttle under real boost, which is exactly the condition mistake 13
used when it validated the inversion against this same channel and got +1.9 %.

Three gates follow from that, and they are the fix. The threshold was not the
problem and is not where the fix went.

  1. WIDE-OPEN THROTTLE ONLY, expressed as a pressure ratio so it needs no
     extra channel. Pooled over all nine drives (the nine drives of 14 September -- this
     measurement was never re-run with drive10; commit 6e40cd8 changed
     'nine' to 'ten' here without re-measuring, and 22 Sep restored it), MAF-unpinned:

         PR >= 1.5   n=919   median +6.4 %   33.6 % over 15 %
         PR >= 1.7   n=696   median +6.5 %   17.5 %
         PR >= 1.8   n=661   median +6.5 %   14.1 %
         PR >= 2.0   n=626   median +6.5 %    9.6 %

     1.8 is where the median stops moving and the tail is mostly gone. Under
     that gate the four drives that reach boost agree with the model at a
     median of +7.7 / +6.8 / +3.6 / +1.2 %, consistent with the +1.9 % that
     plant.charge_temperature() records for this comparison.

  2. MAF NOT SATURATED. `Air mass flow` pins at exactly 1020.0 kg/h and keeps
     reporting (mistake 7). A pinned sample under-reports air, so the inverted
     pressure comes out low for a known reason that is not a fault.

     Worth recording that the original suspicion here was wrong: pinned samples
     are the ones that AGREE. On 7475b5d7 the 325 pinned samples sit at a
     median -5.4 % against -52.5 % for the rest, because pinning happens at
     wide-open throttle, which is the only place the comparison was ever valid.
     Excluding them is still right -- they are biased low by a known sensor
     limit -- but they were never the cause of the 55 events.

  3. PERSISTENCE OVER DISTINCT READINGS, NOT OVER SAMPLES. The adapter polls
     one channel per round trip, so air mass and boost in the same row were
     measured up to 7.5 s apart at 26 channels (mistake 13b). During a pull
     that skew alone produces large instantaneous disagreements in both
     directions -- the p05 of the gated population is -38 % against a median
     of +6.5 %. A boost leak is a PERSISTENT offset; polling skew is not.

     But a median over raw samples does not measure persistence, because the
     exported stream is FORWARD-FILLED. Every channel appears on every 0.15 s
     row and only changes when it is actually polled. The worst window found on
     a healthy drive makes the point exactly -- cb67b01f at t = 825 s:

         21 consecutive samples, all reading +40.9 %, spanning 4.8 s,
         containing exactly ONE air-mass reading and ONE boost reading.

     The median of twenty-one copies of one measurement is that measurement.
     So the window counts DISTINCT readings -- a sample whose air mass and
     boost both repeat the previous one carries no new measurement and is not
     counted -- and it must also SPAN at least one full channel refresh
     interval, measured at 6.0 s on the 26-channel drives (air mass 6.00 s,
     boost 6.00 s, engine speed 6.00 s; ambient pressure 18.0 s). A window that
     spans a refresh interval necessarily contains readings from more than one
     poll cycle, which is the minimum that can tell a standing offset from
     skew. Sweeping that span requirement over all nine drives (14 Sep; drive10
     not included -- see above), at the SHIPPED
     30 s window (AUDIT.md L6 -- this table was captioned 20 s in error; the
     numbers were always the 30 s configuration and are unchanged):

         span >=  0 s   n=89 windows   worst |median|  34.5 %
         span >=  4 s   n=74           worst           16.6 %
         span >=  6 s   n=45           worst           13.6 %   <- shipped
         span >=  8 s   n=30           worst            9.2 %
         span >= 12 s   n=16           worst            6.9 %

     6 s is where the requirement is the measured refresh interval rather than
     a number chosen from this table, and it still leaves 45 windows.

     An earlier attempt gated on the operating point being STEADY instead, and
     it was actively wrong: it selected cruise at a closed throttle with the
     compressor still making pressure behind it -- a genuine, blameless -60 %
     -- and rejected the wide-open pulls, which are the only valid samples and
     are transient by nature. A steady-state gate cannot work here.
"""
from __future__ import annotations

import json
import math
import os
import statistics
import sys
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# AUDIT.md L1: both protection limits are imported, not re-typed. 408.0 used to
# be a literal here and a second literal in engine_env's damage function.
from engine_env import TURB_PROTECT_K, OIL_PROTECT_K   # noqa: E402
LEAD_S = 30.0                  # how far ahead we project the thermal trend

# -- mismatch gates. See the long note in the module docstring. --------------
PSI_TO_KPA = 6.894757
MAF_CEILING_KGH = 1020.0       # exact sensor ceiling, mistake 7
WOT_PR_MIN = 1.8               # pre-throttle pressure / ambient
MISMATCH_WINDOW_S = 30.0       # persistence window
MISMATCH_MIN_READINGS = 4      # DISTINCT readings, not forward-filled samples
MISMATCH_MIN_SPAN_S = 6.0      # = the measured channel refresh interval

# The disagreement that counts as a fault, as a median over the window above.
#
# THIS WAS 15 %, JUSTIFIED BY THE MODEL'S 1.4 % LOAD RESIDUAL. Both halves of
# that justification were wrong:
#
#   * the 1.4 % residual does not test this comparison, or any part of the
#     breathing model. CLAUDE.md mistake 12 works the algebra: it reduces to
#     the MAF channel against the load channel through the DIN reference state,
#     with volumetric efficiency and temperature cancelled out. It cannot bound
#     the error of a pressure inversion.
#
#   * measured directly, the model's own error ON THIS COMPARISON is close to
#     15 %. Under the three gates above, across all nine drives of 14 Sep
#     (drive10 was never added to this measurement), the 30 s
#     windowed median of the disagreement on a car with nothing wrong with it
#     reaches 13.6 % over 45 qualifying windows (p50 5.0 %, p95 9.2 %). A 15 %
#     threshold sits 1.4 points above the worst healthy reading, which is no
#     margin at all.
#
# 25 % is above every value nine healthy drives produced, with an 11-point
# margin, and still far below what a boost leak large enough to matter shows.
#
# Raising it is NOT making the demo quiet. The gates above are what removed the
# 55 events, and they removed them because those events were the throttle, not
# a fault. With the gates in place and the threshold left at 15 %, the replay
# of 7475b5d7 fires ZERO mismatch alerts either way -- the threshold change
# buys margin for the drives where the worst healthy window sits at 13.6 %.
MISMATCH_PCT = 25.0

# The two regions where the inversion HAS evidence, and they are not the same
# kind. 30-75 kPa is the span of the 26 operating points (steady in road and
# engine speed only, AUDIT.md M3); above 200 kPa is where the inverted pressure
# was compared against the car's own boost channel and agreed to +1.9 %
# (mistake 13). Between them there is neither.
VALID_MAP_LO, VALID_MAP_HI = 30.0, 74.0   # the steady operating points
BOOST_CHECKED_KPA = 200.0                 # mistake 13's comparison threshold

SEV = {"info": 0, "watch": 1, "warn": 2, "critical": 3}


@dataclass
class Alert:
    kind: str          # thermal | mismatch | novel
    severity: str      # info | watch | warn | critical
    t: float           # seconds into the drive
    title: str         # one line, readable at a glance
    advice: str        # what to DO -- never just a description
    audience: str      # driver | mechanic | engineer
    evidence: dict     # the numbers behind it, for the review file

    def to_record(self, session: str, source: str):
        return {"session": session, "source": source,
                "wall": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                **asdict(self)}


class AlertEngine:
    """Watches the estimator's output and marks irregular states.

    Stateful on purpose. Thermal alerts need a TREND, not an instant: a turbine
    at 800 C and falling is fine; at 800 C and climbing 4 K/s it is 30 seconds
    from trouble, and only the second deserves the driver's attention. Mismatch
    alerts need PERSISTENCE for the reason in the module docstring.
    """

    def __init__(self, review_path: str = "app/review_log.jsonl",
                 session: str | None = None, source: str = "unknown"):
        self.review_path = review_path
        self.session = session or datetime.now().strftime("%Y%m%d-%H%M%S")
        self.source = source
        self._hist = deque()            # (t, t_turb, t_oil) for the trend
        self._mm = deque()              # (t, diff_pct), distinct readings only
        self._last_reading = None       # (air_kgh, boost_psi) of the last one
        self._last_fired = {}           # (kind, severity) -> t, to stop spam
        self.alerts = []
        self.gated_samples = 0          # samples that passed the WOT gate
        self.gated_readings = 0         # of those, ones that were new readings
        os.makedirs(os.path.dirname(review_path) or ".", exist_ok=True)

    # -- persistence: ONLY marked events, never the raw stream ------------
    def _persist(self, a: Alert):
        rec = a.to_record(self.session, self.source)
        try:
            with open(self.review_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
        except OSError:
            # A review file we cannot write is not a reason to stop watching
            # the engine. The alert still reaches the screen.
            pass

    def _fire(self, a: Alert, cooldown: float = 20.0):
        """Emit an alert unless one of the same kind fired very recently."""
        last = self._last_fired.get((a.kind, a.severity))
        if last is not None and a.t - last < cooldown:
            return None
        self._last_fired[(a.kind, a.severity)] = a.t
        self.alerts.append(a)
        self._persist(a)
        return a

    # -- 1. THERMAL: for the driver, right now ----------------------------
    def _thermal(self, st) -> list:
        """Every thermal condition, evaluated. Returns a list, possibly empty.

        AUDIT.md L2: this used to `return self._fire(...)` from the turbine
        branch, and `_fire` returns None while a cooldown is running -- so
        whenever the turbine was at or near its limit, the OIL check below it
        was skipped entirely. The branch that mattered most silenced the one
        underneath it.

        AUDIT.md M10 is the bigger fix and it is about honesty rather than
        coverage. The projection used to be linear: `T + rate x 30 s`. The
        housing is a FIRST-ORDER node heading for the steady state its current
        operating point implies, with a time constant of 27-240 s, so it
        reaches only 61-75 % of that straight line. On 7475b5d7 five of the ten
        warnings projected to within 5 K of the limit while the model's own
        dynamics put them 20-110 K short of it -- and "threshold in about N s"
        is a quantitative claim to a driver.

        The projection is now the analytic solution of the node the app is
        already integrating:

            T(dt) = T_ss + (T - T_ss) * exp(-dt / tau)

        which is exact for constant inputs, and it carries a consequence worth
        having: **if T_ss is below the limit, the turbine cannot reach the limit
        at this operating point, however fast it is climbing right now.** No
        time-to-threshold is quoted in that case, because there is not one.
        """
        out = []
        if not st.ok or st.warming_up:
            # Never alarm on a seeded guess. `warming_up` is the measured width
            # of the seed bound, not a timer -- see estimator.py note 1.
            return out
        self._hist.append((st.t, st.t_turb_c, st.t_oil_est_c))
        while self._hist and st.t - self._hist[0][0] > 20.0:
            self._hist.popleft()
        if len(self._hist) < 5:
            return out

        t0, turb0, _ = self._hist[0]
        span = st.t - t0
        if span < 5.0:
            return out
        rate = (st.t_turb_c - turb0) / span          # K/s, for display only
        limit_c = TURB_PROTECT_K - 273.15            # 850 C

        # the model's own projection, not a straight line
        ss, tau = st.t_turb_ss_c, st.tau_turb_s
        if math.isfinite(ss) and math.isfinite(tau) and tau > 0:
            projected = ss + (st.t_turb_c - ss) * math.exp(-LEAD_S / tau)
            reachable = ss >= limit_c
        else:                                    # no dynamics: fall back, and say so
            projected = st.t_turb_c + rate * LEAD_S
            reachable = projected >= limit_c

        ev = {"t_turb_c": round(st.t_turb_c, 1), "rate_k_s": round(rate, 2),
              "projected_c": round(projected, 1), "limit_c": round(limit_c, 1),
              "heading_for_c": round(ss, 1) if math.isfinite(ss) else None,
              "tau_s": round(tau, 1) if math.isfinite(tau) else None,
              "seed_band_k": round(st.seed_band_k, 1),
              "confidence": round(st.confidence, 2)}

        if st.t_turb_c >= limit_c:
            a = self._fire(Alert(
                "thermal", "critical", st.t,
                f"Turbine {st.t_turb_c:.0f} C - above the {limit_c:.0f} C damage threshold",
                "Ease off now. Damage accumulates exponentially above this point.",
                "driver", ev))
            if a:
                out.append(a)
        elif reachable and projected >= limit_c and rate > 0.5:
            # Time to the limit along the first-order curve, not the tangent.
            secs = -tau * math.log(max(1e-6, (limit_c - ss) / (st.t_turb_c - ss)))                 if ss > limit_c and st.t_turb_c < ss else LEAD_S
            a = self._fire(Alert(
                "thermal", "warn", st.t,
                f"Turbine {st.t_turb_c:.0f} C, rising {rate:.1f} K/s - "
                f"threshold in about {secs:.0f} s at this load",
                "Lift slightly or change up. Backing off now avoids the heat entirely.",
                "driver", ev))
            if a:
                out.append(a)

        oil_limit = OIL_PROTECT_K - 273.15
        if st.t_oil_est_c >= oil_limit:
            a = self._fire(Alert(
                "thermal", "warn", st.t,
                f"Oil {st.t_oil_est_c:.0f} C - at the protection threshold",
                "Reduce sustained load. Oil cools far more slowly than it heats.",
                "driver", {"t_oil_c": round(st.t_oil_est_c, 1),
                           "limit_c": round(oil_limit, 1),
                           "seed_band_k": round(st.seed_band_k, 1)}))
            if a:
                out.append(a)
        return out

    # -- 2. MISMATCH: for a mechanic, afterwards ---------------------------
    def _mismatch(self, st, s):
        """The inverted manifold pressure against the car's own sensor.

        Only at wide-open throttle, only with the MAF off its ceiling, and only
        as a median over 20 s. The module docstring explains all three; the
        short version is that below wide-open throttle these two numbers are
        measuring opposite sides of the throttle plate and MUST disagree.
        """
        if not st.ok or s.boost_psi is None or s.p_amb_psi is None:
            return None
        if s.air_kgh is None or not math.isfinite(st.map_kpa):
            return None

        amb_kpa = s.p_amb_psi * PSI_TO_KPA
        logged_kpa = (s.boost_psi + s.p_amb_psi) * PSI_TO_KPA
        if amb_kpa < 50.0 or logged_kpa < 50.0:
            return None

        # gate 1: wide-open throttle, inferred from the pressure ratio
        if logged_kpa / amb_kpa < WOT_PR_MIN:
            return None
        # gate 2: the air-mass sensor is not pinned at its ceiling (mistake 7)
        if s.air_kgh >= MAF_CEILING_KGH:
            return None

        self.gated_samples += 1

        # gate 3: persistence, counted in DISTINCT readings. A sample whose air
        # mass and boost both repeat the previous one is a forward-filled copy
        # of a measurement already in the window -- it carries no new
        # information, and counting it would let one reading outvote the window.
        reading = (s.air_kgh, s.boost_psi)
        while self._mm and st.t - self._mm[0][0] > MISMATCH_WINDOW_S:
            self._mm.popleft()
        if reading == self._last_reading:
            return None
        self._last_reading = reading

        diff = 100.0 * (st.map_kpa - logged_kpa) / logged_kpa
        self._mm.append((st.t, diff))
        self.gated_readings += 1

        if len(self._mm) < MISMATCH_MIN_READINGS:
            return None
        span = st.t - self._mm[0][0]
        if span < MISMATCH_MIN_SPAN_S:
            return None
        med = statistics.median([d for _, d in self._mm])
        if abs(med) < MISMATCH_PCT:
            return None

        ev = {"median_disagreement_pct": round(med, 1),
              "map_from_air_kpa": round(st.map_kpa, 1),
              "map_from_sensor_kpa": round(logged_kpa, 1),
              "pressure_ratio": round(logged_kpa / amb_kpa, 2),
              "window_s": MISMATCH_WINDOW_S,
              "readings_in_window": len(self._mm),
              "window_span_s": round(span, 1),
              "threshold_pct": MISMATCH_PCT}
        if med > 0:
            cause = ("Air mass implies more pressure than the boost sensor sees. "
                     "Consistent with a boost leak after the sensor, or a MAF "
                     "reading high.")
        else:
            cause = ("Boost sensor sees more pressure than the air mass implies. "
                     "Consistent with a restricted intake or a MAF reading low.")
        return self._fire(Alert(
            "mismatch", "watch", st.t,
            f"Air mass and boost sensor disagree by {med:+.0f} % at full throttle",
            cause + " Worth checking on a lift - not a driving hazard.",
            "mechanic", ev), cooldown=60.0)

    # -- 3. NOVEL: for us, a confidence flag -------------------------------
    def _novel(self, st):
        """Flag the region where the INVERSION has the least support.

        AUDIT.md L7. This used to say "outside the validated range" of
        30-75 kPa, which is the span of the 26 operating points (steady in
        road and engine speed only, AUDIT.md M3) behind the LOAD RESIDUAL --
        and mistake 12 established that the load residual
        cancels the breathing model and therefore validates nothing about the
        pressure inversion this app depends on. So the flag was naming the
        wrong evidence: it called the boosted region "extrapolation" when the
        boosted region is the ONE place the inversion was actually checked
        against an independent channel (+1.9 %, mistake 13).

        The honest statement is narrower. Between the steady-point span and the
        boost-checked region there is a band with neither kind of evidence, and
        that is what this now flags.
        """
        if not st.ok:
            return None
        if VALID_MAP_LO <= st.map_kpa <= VALID_MAP_HI:
            return None
        if st.map_kpa >= BOOST_CHECKED_KPA:
            return None          # checked against the car's own boost channel
        where = "above" if st.map_kpa > VALID_MAP_HI else "below"
        return self._fire(Alert(
            "novel", "info", st.t,
            f"Operating between the evidence bands ({st.map_kpa:.0f} kPa, "
            f"{where} the steady points)",
            "Neither the steady operating points nor the boost comparison "
            "covers this region. Treat the turbine temperature as indicative, "
            "not quantitative.",
            "engineer",
            {"map_kpa": round(st.map_kpa, 1),
             "steady_point_range_kpa": [VALID_MAP_LO, VALID_MAP_HI],
             "boost_checked_above_kpa": BOOST_CHECKED_KPA}),
            cooldown=120.0)

    # -- entry point -------------------------------------------------------
    def check(self, st, s) -> list:
        out = list(self._thermal(st))
        for a in (self._mismatch(st, s), self._novel(st)):
            if a is not None:
                out.append(a)
        return out

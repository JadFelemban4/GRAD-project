"""alerts.py — the three kinds of irregular state, and what to do about each.

THIS IS THE ONLY FILE THAT WRITES TO DISK.

Raw car data is never stored (see reader.py). What gets persisted is what the
model MARKS: an event, its evidence, and the advice given. That file is what a
workshop or fleet owner reads afterwards.

THE THREE TYPES ARE GENUINELY DIFFERENT, AND THEY HAVE DIFFERENT AUDIENCES
--------------------------------------------------------------------------

  THERMAL   the estimated turbine or oil temperature is heading for the knee of
            the damage curve.
            -> THE DRIVER, now. This is the only type that should interrupt
               someone who is driving.

  MISMATCH  the car is not behaving the way the validated model says it should:
            measured air mass disagrees with what this speed and load imply.
            -> A MECHANIC, afterwards. This is a diagnostic, not an emergency.
               A boost leak, a drifting MAF and a sticking wastegate all look
               like this, and none of them needs the driver's attention at
               110 km/h.

  NOVEL     the engine is somewhere our 175 minutes of data never went.
            -> US. It means the estimate is extrapolating and should be trusted
               less. It is a confidence flag, not a fault.

Keeping them separate is what makes the app defensible. One undifferentiated
"something is wrong" light would be worthless to all three audiences.

WHY THE THRESHOLDS ARE WHAT THEY ARE
------------------------------------
Every number below traces to something the project measured or published:

  1123 K      the knee of the turbine damage term, exp((T-1123)/45). The same
              constant check_premise.py scores with -- they are deliberately
              the same number, imported from one place.
  408 K       the oil term's knee in the same damage model.
  15 %        the air-mass disagreement that counts as a fault. The model's
              validated load residual is 1.4 % over 22 points, and the worst
              per-drive figure is 3.9 %. 15 % is an order of magnitude above
              the model's own error, so it cannot fire on modelling noise.
  30-74 kPa   the manifold pressure range the model was actually validated at.
              Outside it we are extrapolating and say so.

DO NOT TUNE THESE TO MAKE THE DEMO LOOK GOOD. If a threshold changes, the
reason has to be a measurement, and it goes in the docstring.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine_env import TURB_PROTECT_K   # noqa: E402  the SAME 1123 K

OIL_PROTECT_K = 408.0          # the oil knee in the damage model
LEAD_S = 30.0                  # how far ahead we project the thermal trend
MISMATCH_PCT = 15.0            # see docstring
VALID_MAP_LO, VALID_MAP_HI = 30.0, 74.0   # where the model was validated

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

    Stateful on purpose: thermal alerts need a TREND, not an instant. A turbine
    at 800 C and falling is fine; at 800 C and climbing 4 K/s is 30 seconds from
    trouble. Only the second deserves the driver's attention.
    """

    def __init__(self, review_path: str = "app/review_log.jsonl",
                 session: str | None = None, source: str = "unknown"):
        self.review_path = review_path
        self.session = session or datetime.now().strftime("%Y%m%d-%H%M%S")
        self.source = source
        self._hist = []                 # (t, t_turb, t_oil) for the trend
        self._last_fired = {}           # kind -> t, to stop alert spam
        self.alerts = []
        os.makedirs(os.path.dirname(review_path) or ".", exist_ok=True)

    # -- persistence: ONLY marked events, never the raw stream ------------
    def _persist(self, a: Alert):
        rec = a.to_record(self.session, self.source)
        with open(self.review_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")

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
    def _thermal(self, st):
        if not st.ok or st.warming_up:
            return None            # never alarm on a seeded guess
        self._hist.append((st.t, st.t_turb_c, st.t_oil_est_c))
        self._hist = [h for h in self._hist if st.t - h[0] <= 20.0]
        if len(self._hist) < 5:
            return None

        t0, turb0, oil0 = self._hist[0]
        span = st.t - t0
        if span < 5.0:
            return None
        rate = (st.t_turb_c - turb0) / span          # K/s
        projected = st.t_turb_c + rate * LEAD_S
        limit_c = TURB_PROTECT_K - 273.15            # 850 C

        ev = {"t_turb_c": round(st.t_turb_c, 1), "rate_k_s": round(rate, 2),
              "projected_c": round(projected, 1), "limit_c": round(limit_c, 1),
              "confidence": round(st.confidence, 2)}

        if st.t_turb_c >= limit_c:
            return self._fire(Alert(
                "thermal", "critical", st.t,
                f"Turbine {st.t_turb_c:.0f} C - above the {limit_c:.0f} C damage threshold",
                "Ease off now. Damage accumulates exponentially above this point.",
                "driver", ev))
        if projected >= limit_c and rate > 0.5:
            secs = max(1.0, (limit_c - st.t_turb_c) / rate)
            return self._fire(Alert(
                "thermal", "warn", st.t,
                f"Turbine {st.t_turb_c:.0f} C, rising {rate:.1f} K/s - "
                f"threshold in about {secs:.0f} s",
                "Lift slightly or change up. Backing off now avoids the heat entirely.",
                "driver", ev))
        oil_limit = OIL_PROTECT_K - 273.15
        if st.t_oil_est_c >= oil_limit:
            return self._fire(Alert(
                "thermal", "warn", st.t,
                f"Oil {st.t_oil_est_c:.0f} C - at the protection threshold",
                "Reduce sustained load. Oil cools far more slowly than it heats.",
                "driver", {"t_oil_c": round(st.t_oil_est_c, 1),
                           "limit_c": round(oil_limit, 1)}))
        return None

    # -- 2. MISMATCH: for a mechanic, afterwards ---------------------------
    def _mismatch(self, st, s):
        """Measured air mass against what the model expects at this state.

        The model was validated to 1.4 % on load, worst drive 3.9 %. A 15 %
        disagreement is far outside that, so it is the CAR that has changed,
        not the model that is wrong.
        """
        if not st.ok or s.boost_psi is None or s.p_amb_psi is None:
            return None
        # Compare the manifold pressure we INVERTED from air mass against the
        # pressure the car's own boost sensor reports. These are independent
        # measurements of the same thing.
        logged_kpa = (s.boost_psi + s.p_amb_psi) * 6.894757
        if logged_kpa < 50 or not math.isfinite(st.map_kpa):
            return None
        diff = 100.0 * (st.map_kpa - logged_kpa) / logged_kpa
        if abs(diff) < MISMATCH_PCT:
            return None
        ev = {"map_from_air_kpa": round(st.map_kpa, 1),
              "map_from_sensor_kpa": round(logged_kpa, 1),
              "disagreement_pct": round(diff, 1),
              "threshold_pct": MISMATCH_PCT}
        if diff > 0:
            cause = ("Air mass implies more pressure than the boost sensor sees. "
                     "Consistent with a boost leak after the sensor, or a MAF "
                     "reading high.")
        else:
            cause = ("Boost sensor sees more pressure than the air mass implies. "
                     "Consistent with a restricted intake or a MAF reading low.")
        return self._fire(Alert(
            "mismatch", "watch", st.t,
            f"Air mass and boost sensor disagree by {diff:+.0f} %",
            cause + " Worth checking on a lift - not a driving hazard.",
            "mechanic", ev), cooldown=60.0)

    # -- 3. NOVEL: for us, a confidence flag -------------------------------
    def _novel(self, st):
        if not st.ok:
            return None
        if VALID_MAP_LO <= st.map_kpa <= VALID_MAP_HI:
            return None
        where = "above" if st.map_kpa > VALID_MAP_HI else "below"
        return self._fire(Alert(
            "novel", "info", st.t,
            f"Operating {where} the validated range ({st.map_kpa:.0f} kPa)",
            "Estimates here are extrapolation. Treat the turbine temperature as "
            "indicative, not quantitative.",
            "engineer",
            {"map_kpa": round(st.map_kpa, 1),
             "validated_range_kpa": [VALID_MAP_LO, VALID_MAP_HI]}),
            cooldown=120.0)

    # -- entry point -------------------------------------------------------
    def check(self, st, s) -> list:
        out = []
        for a in (self._thermal(st), self._mismatch(st, s), self._novel(st)):
            if a is not None:
                out.append(a)
        return out

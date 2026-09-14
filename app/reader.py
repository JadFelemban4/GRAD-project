"""reader.py — gets data off the car, or replays a log as though it were live.

RAW DATA IS NEVER WRITTEN TO DISK.

The stream is a live mirror of the ECU's own dashboard: it exists in memory,
goes out over the websocket, and is gone. Only what the model MARKS -- the
alerts in alerts.py -- is persisted, and that goes to the shared review file.
If you ever add a line here that opens a file for writing, you have changed the
product's privacy model. Do not do it by accident.

TWO MODES, AND REPLAY IS THE IMPORTANT ONE
------------------------------------------
    replay  -- feed one of our own CSV logs through at real speed or faster.
               No car, no adapter, no driving. Five people can develop against
               the same 175 minutes of real data simultaneously.
    live    -- an ELM327 adapter over Bluetooth/WiFi/USB.

Build and test everything in replay. Touch the car only to confirm.

THE CHANNEL BUDGET IS THE WHOLE DESIGN CONSTRAINT
-------------------------------------------------
The adapter polls ONE channel per round trip. Whatever total rate the link
sustains is divided by the number of channels you ask for. Measured on this car
(CLAUDE.md mistake 13b):

    26 channels -> a new value for each one every 7.5 s
     7 channels -> every 1.45 s        5.2x faster, same adapter

The thermal state we care about moves on a 48 s time constant, so ~1.5 s per
channel is comfortable and 7.5 s is not. KEEP THE SET SMALL. Every channel
someone adds "because it might be interesting" slows down every other channel.
"""
from __future__ import annotations

import csv
import os
import sys
import time
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.estimator import Sample   # noqa: E402

# The live set. Six channels, chosen because the estimator cannot work without
# them -- not because they are interesting. Adding an eighth costs every other
# channel about 14 % of its update rate.
#
#   rpm, air mass   -> manifold pressure, torque, EGT, fuel flow
#   coolant         -> thermal state, and the warm-start seed
#   ambient temp    -> charge temperature, and every heat flow's boundary
#   vehicle speed   -> radiator ram air
#   boost           -> sanity check on the inverted manifold pressure
LIVE_PIDS = {
    "rpm":     "Engine speed",
    "air_kgh": "Air mass flow",
    "ect_c":   "Coolant temperature",
    "t_amb_c": "Ambient temperature",
    "v_kmh":   "Vehicle speed",
    "boost_psi": "Boost pressure",
}

# Optional extras. The estimator MODELS these when absent and says so, which is
# honest but weaker. Add them only if the link has rate to spare.
OPTIONAL_PIDS = {
    "spark_deg": "Actual ignition angle",
    "lam":       "Lambda actual value",
    "oil_c":     "Oil temperature",
    "load_pct":  "Relative air filling",
}

CSV_ALIASES = {**LIVE_PIDS, **OPTIONAL_PIDS,
               "iat_pre_c": "Intake air temperature before throttle valve, measured",
               "p_amb_psi": "Ambient pressure"}


def _f(row, name):
    v = row.get(name, "")
    if v is None or v == "":
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return None if x != x else x


class ReplayReader:
    """Plays one of our CSV logs back as a live stream.

    speed=1.0 is real time; speed=0 is as fast as the consumer will take it,
    which is what the tests use.
    """

    def __init__(self, path: str, speed: float = 1.0):
        self.path = path
        self.speed = speed
        with open(path, newline="", encoding="utf-8-sig") as fh:
            self.rows = list(csv.DictReader(fh))
        if not self.rows:
            raise SystemExit(f"no rows in {path}")
        self.name = os.path.basename(path)

    def __iter__(self):
        t0 = None
        wall0 = time.monotonic()
        for row in self.rows:
            t = _f(row, "Time")
            if t is None:
                continue
            if t0 is None:
                t0 = t
            rel = t - t0
            if self.speed > 0:
                target = wall0 + rel / self.speed
                gap = target - time.monotonic()
                if gap > 0:
                    time.sleep(min(gap, 1.0))
            yield Sample(
                t=rel,
                **{k: _f(row, col) for k, col in CSV_ALIASES.items()}
            )


class LiveReader:
    """ELM327 over the OBD-II port.

    Deliberately thin, and deliberately tolerant. A real adapter drops
    connections, returns 'NO DATA' for PIDs the car does not support, and
    varies its rate with traffic on the bus. None of that should stop the app;
    a missing channel becomes None and the estimator reports it as modelled.

    Requires `pip install obd`. Not imported at module load so that replay-mode
    development needs no adapter library installed.
    """

    def __init__(self, port: str | None = None, rate_hz: float = 5.0):
        try:
            import obd
        except ImportError:
            raise SystemExit(
                "Live mode needs the 'obd' package:  pip install obd\n"
                "Develop in replay mode instead:  python -m app.server --replay <csv>")
        self.obd = obd
        self.conn = obd.OBD(port) if port else obd.OBD()
        if not self.conn.is_connected():
            raise SystemExit("no OBD-II adapter found. Check pairing and ignition.")
        self.rate_hz = rate_hz
        self.name = "live"
        # Ask the car what it actually supports, rather than assuming.
        self.available = {c.name for c in self.conn.supported_commands}

    def _q(self, cmd_name):
        cmd = getattr(self.obd.commands, cmd_name, None)
        if cmd is None or cmd.name not in self.available:
            return None
        r = self.conn.query(cmd)
        if r.is_null():
            return None
        try:
            return float(r.value.magnitude)
        except AttributeError:
            return float(r.value)

    def __iter__(self):
        t0 = time.monotonic()
        period = 1.0 / self.rate_hz
        while True:
            start = time.monotonic()
            s = Sample(t=start - t0)
            s.rpm = self._q("RPM")
            maf_gps = self._q("MAF")                  # standard PID is g/s
            if maf_gps is not None:
                s.air_kgh = maf_gps * 3.6
            s.ect_c = self._q("COOLANT_TEMP")
            s.t_amb_c = self._q("AMBIANT_AIR_TEMP")
            s.v_kmh = self._q("SPEED")
            s.spark_deg = self._q("TIMING_ADVANCE")
            yield s
            gap = period - (time.monotonic() - start)
            if gap > 0:
                time.sleep(gap)


class Stream:
    """Reader + a short in-memory history. NOTHING HERE TOUCHES THE DISK."""

    def __init__(self, reader, history: int = 600):
        self.reader = reader
        self.buf = deque(maxlen=history)   # ~2 minutes at 5 Hz, memory only

    def __iter__(self):
        for s in self.reader:
            self.buf.append(s)
            yield s

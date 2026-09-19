"""reader.py — gets data off the car, or replays a log as though it were live.

WHAT CHANGED HERE, AND WHEN
---------------------------
14 September 2026 — hardened for a real adapter, and the channel list became a
table that carries its own justification. Before this, `LIVE_PIDS` declared
`boost_psi` but `LiveReader` never polled it, so the mismatch detector was dead
code on the car; unsupported PIDs were asked for forever; a dropped link was not
counted; and every channel was polled at the same rate whether it moved on a
timescale of milliseconds or minutes. `LIVE_PIDS`, `OPTIONAL_PIDS` and
`CSV_ALIASES` are all still exported, built from the table, because other code
and the tests read them.

RAW DATA IS NEVER WRITTEN TO DISK.

The stream is a live mirror of the ECU's own dashboard: it exists in memory,
goes out over the websocket, and is gone. Only what the model MARKS -- the
alerts in alerts.py -- is persisted, and that goes to the shared review file.
If you ever add a line here that opens a file for writing, you have changed the
product's privacy model. Do not do it by accident.

READ-ONLY, PERMANENTLY. Every OBD call in this file is a query. There is no
write command, no mode 08, no bus write of any kind, and there is no code path
from this module to anything that could produce one.

TWO MODES, AND REPLAY IS THE IMPORTANT ONE
------------------------------------------
    replay  -- feed one of our own CSV logs through at real speed or faster.
               No car, no adapter, no driving. Five people can develop against
               the same 295 minutes of real data simultaneously.
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
channel is comfortable and 7.5 s is not. KEEP THE SET SMALL.

Two mechanisms defend the budget, and both are in the CHANNELS table below:

  1. Every channel carries a `why`. A channel with no reason to be there is a
     channel that is stealing rate from the ones that matter.
  2. Every channel carries a `min_period_s`. Ambient pressure moves on a
     timescale of minutes -- polling it as often as engine speed wastes 1/n of
     the entire link. Slow channels are polled slowly and the budget goes to
     the fast ones. Measured refresh intervals on 7475b5d7 (26 channels):
     engine speed 6.0 s, air mass 6.0 s, boost 6.0 s, ambient pressure 18.0 s.

DEGRADE, NEVER CRASH
--------------------
A real adapter drops Bluetooth mid-drive, returns NO DATA for PIDs the car does
not support, and answers slowly when the bus is busy. None of that is an error
condition for this app:

  * a channel the car does not support is retired after `MAX_MISSES` misses,
    which GIVES ITS RATE BACK to the channels that do work;
  * a channel that simply did not answer this cycle stays None for that sample,
    and the estimator marks whatever depended on it as modelled;
  * a dropped connection is retried with a backoff, forever, while the app
    keeps serving the last state it had;
  * `ChannelHealth` records all of it so the UI can show which channels are
    actually alive rather than implying the whole set is.
"""
from __future__ import annotations

import csv
import os
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.estimator import Sample   # noqa: E402


# The BimmerLink logs record both pressures in psi, so the Sample carries psi
# and the standard OBD-II PIDs (which answer in kPa) are converted on the way in.
KPA_PER_PSI_INV = 1.0 / 6.894757


@dataclass(frozen=True)
class Channel:
    """One thing we ask the car for.

    `field`        the attribute it fills on Sample
    `csv`          the BimmerLink column name, for replay
    `obd`          the python-obd command name, for live. None means this car
                   publishes it but no standard OBD-II PID does, so live mode
                   simply will not have it and the estimator must model it.
    `scale`        converts the adapter's unit into the Sample's unit
    `min_period_s` do not re-poll faster than this. See the budget note above.
    `why`          why this channel is worth a slice of the link. REQUIRED.
    """
    field: str
    csv: str
    obd: str | None
    why: str
    scale: Callable[[float], float] = lambda x: x
    min_period_s: float = 0.0


# ---------------------------------------------------------------------------
# THE LIVE SET. Six channels, because the estimator cannot work without them.
# Adding a seventh costs every other channel about 14 % of its update rate, so
# a new entry here needs a reason in `why` that survives being read out loud.
# ---------------------------------------------------------------------------
LIVE_CHANNELS = (
    Channel("rpm", "Engine speed", "RPM",
            "every cycle the model runs is indexed on engine speed"),
    Channel("air_kgh", "Air mass flow", "MAF",
            "the ONE load input. manifold pressure is inverted from it "
            "(mistake 2), and fuel flow, torque and EGT all follow",
            scale=lambda gps: gps * 3.6),          # obd MAF is g/s, we want kg/h
    Channel("ect_c", "Coolant temperature", "COOLANT_TEMP",
            "the thermal network's measured node, and the warm-start seed"),
    Channel("t_amb_c", "Ambient temperature", "AMBIANT_AIR_TEMP",
            "boundary condition for every heat flow, and the anchor of "
            "charge_temperature(). slow-moving, so polled slowly",
            min_period_s=10.0),
    Channel("v_kmh", "Vehicle speed", "SPEED",
            "radiator ram air. the difference between 22 and 33 m/s is most "
            "of the block's heat rejection"),
    Channel("boost_psi", "Boost pressure", None,
            "the car's own pressure sensor, used ONLY as an independent check "
            "on the inverted manifold pressure (the mismatch detector). "
            "live mode derives it from INTAKE_PRESSURE - BAROMETRIC_PRESSURE"),
)

# Optional extras. The estimator MODELS these when absent and says so, which is
# honest but weaker. Add them only if the link has rate to spare.
OPTIONAL_CHANNELS = (
    Channel("spark_deg", "Actual ignition angle", "TIMING_ADVANCE",
            "measured spark beats the baseline ECU's modelled spark"),
    Channel("lam", "Lambda actual value", "COMMANDED_EQUIV_RATIO",
            "measured lambda beats base_lambda(). note this is the COMMANDED "
            "ratio on standard OBD-II, not the measured one BimmerLink logs"),
    Channel("oil_c", "Oil temperature", "OIL_TEMP",
            "would let the oil node be measured instead of estimated"),
    Channel("load_pct", "Relative air filling", None,
            "BMW's relative filling. no standard PID publishes it"),
    Channel("p_amb_psi", "Ambient pressure", "BAROMETRIC_PRESSURE",
            "absolute reference for the boost channel. barely moves, so it is "
            "polled every 30 s and costs almost nothing",
            scale=lambda kpa: kpa * KPA_PER_PSI_INV,   # the PID answers in kPa
            min_period_s=30.0),
    Channel("iat_pre_c", "Intake air temperature before throttle valve, measured",
            "INTAKE_TEMP",
            "COMPRESSOR OUTLET with a ~10 s lag, not charge temperature "
            "(mistakes 13 and 13b). Carried for display and diagnosis ONLY. "
            "plant.charge_temperature() is what the model uses. Never feed "
            "this into map_from_airflow()."),
)

ALL_CHANNELS = LIVE_CHANNELS + OPTIONAL_CHANNELS

# Kept as plain dicts because the rest of the app and the tests read them.
LIVE_PIDS = {c.field: c.csv for c in LIVE_CHANNELS}
OPTIONAL_PIDS = {c.field: c.csv for c in OPTIONAL_CHANNELS}
CSV_ALIASES = {c.field: c.csv for c in ALL_CHANNELS}

# A channel that misses this many polls in a row is assumed unsupported and is
# retired for the rest of the session. The point is not tidiness: a retired
# channel stops consuming round trips, so the channels that DO answer speed up.
MAX_MISSES = 5

# Reconnection backoff, seconds. Capped so a car that comes back after a long
# stop is picked up within half a minute.
RECONNECT_BACKOFF = (1.0, 2.0, 5.0, 10.0, 20.0, 30.0)


@dataclass
class ChannelHealth:
    """Per-channel liveness. The UI shows this so nobody assumes a full set."""
    ok: int = 0
    misses: int = 0
    consecutive_misses: int = 0
    retired: bool = False
    last_ok_t: float | None = None

    def note_ok(self, t):
        self.ok += 1
        self.consecutive_misses = 0
        self.last_ok_t = t

    def note_miss(self):
        self.misses += 1
        self.consecutive_misses += 1
        if self.consecutive_misses >= MAX_MISSES:
            self.retired = True


@dataclass
class ReaderStatus:
    """What the reader knows about its own link. Read by the server, shown in
    the UI. Never persisted."""
    mode: str = "-"
    source: str = "-"
    connected: bool = False
    reconnects: int = 0
    samples: int = 0
    last_error: str | None = None
    health: dict = field(default_factory=dict)

    def as_dict(self):
        return {"mode": self.mode, "source": self.source,
                "connected": self.connected, "reconnects": self.reconnects,
                "samples": self.samples, "last_error": self.last_error,
                "channels": {k: {"ok": v.ok, "misses": v.misses,
                                 "retired": v.retired}
                             for k, v in self.health.items()}}


# Physically impossible readings, per field. A value outside these is a
# placeholder or a decode error, not a measurement.
#
# AUDIT.md M8, 15 September 2026: BimmerLink writes 0 for every channel until
# its first poll, so the opening rows of every export read coolant 0, ambient 0
# and ambient pressure 0. Those reached the estimator as REAL readings -- on
# 3f64372e coolant is 0 for the first 14 rows and ambient pressure for 17 --
# and the engine passes the rpm/air gate before they arrive, so the thermal
# state was being seeded with a block at 273 K.
#
# A guard on the physics catches it without needing to know the logger's
# habits: this engine cannot be at -273 C, and ambient pressure cannot be zero
# at any altitude a car reaches.
# Channels whose LEADING run of exact zeros is a placeholder rather than a
# reading. Restricted on purpose: a vehicle speed of 0 at the start of a log is
# a real measurement of a stationary car, and an air mass of 0 is a real
# measurement of a stopped engine. A coolant or ambient TEMPERATURE of exactly
# 0.000, before that channel has ever reported anything else, is not.
ZERO_IS_PLACEHOLDER = ("ect_c", "oil_c", "t_amb_c", "iat_pre_c", "p_amb_psi")

PLAUSIBLE = {
    "ect_c":     (-40.0, 150.0),
    "oil_c":     (-40.0, 200.0),
    "t_amb_c":   (-50.0, 70.0),
    "iat_pre_c": (-50.0, 250.0),
    "p_amb_psi": (7.0, 16.5),     # 7 psi is ~5500 m; 16.5 is a deep mine
    "rpm":       (0.0, 9000.0),
    "air_kgh":   (0.0, 2000.0),
    "v_kmh":     (0.0, 350.0),
    "lam":       (0.4, 1.8),
    "spark_deg": (-40.0, 60.0),
}


def _f(row, name, field=None):
    """One CSV cell to a float, or None. Never raises: a log is a measurement
    and a malformed cell is a fact about the logger, not a reason to stop.

    When `field` is given, the value is also range-checked -- see PLAUSIBLE.
    """
    v = row.get(name, "")
    if v is None:
        return None
    if isinstance(v, str):
        v = v.strip()
        if v == "" or v.lower() in ("nan", "null", "-", "n/a", "no data"):
            return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if x != x:
        return None
    if field is not None:
        lo, hi = PLAUSIBLE.get(field, (-float("inf"), float("inf")))
        if not (lo <= x <= hi):
            return None
    return x


class ReplayReader:
    """Plays one of our CSV logs back as a live stream.

    speed=1.0 is real time; speed=0 is as fast as the consumer will take it,
    which is what the tests use.

    Tolerant on purpose. These files come off a phone over Bluetooth and some
    of them are reconnaissance logs with a quarter of their samples missing
    (CLAUDE.md mistake 8). Rows without a usable timestamp are skipped and
    counted; time that runs backwards is skipped rather than trusted.
    """

    def __init__(self, path: str, speed: float = 1.0, loop: bool = False):
        self.path = path
        self.speed = max(0.0, speed)
        self.loop = loop
        if not os.path.exists(path):
            raise SystemExit(f"no such log: {path}")
        with open(path, newline="", encoding="utf-8-sig", errors="replace") as fh:
            self.rows = list(csv.DictReader(fh))
        if not self.rows:
            raise SystemExit(f"no rows in {path}")
        self.name = os.path.basename(path)
        self.skipped_rows = 0
        # Which of our channels this log actually carries. A 7-channel drive
        # like pull01 has most of them missing, and that is the normal case.
        cols = set(self.rows[0].keys())
        self.present = {c.field for c in ALL_CHANNELS if c.csv in cols}
        # AUDIT.md M8: index of the first row on which each placeholder-prone
        # channel reports something other than exactly zero. Everything before
        # it is the logger filling the column before the ECU has answered.
        self._first_real = {}
        for c in ALL_CHANNELS:
            if c.field not in ZERO_IS_PLACEHOLDER or c.csv not in cols:
                continue
            idx = 0
            for i, row in enumerate(self.rows):
                v = _f(row, c.csv)
                if v is not None and v != 0.0:
                    idx = i
                    break
            self._first_real[c.field] = idx
        self.status = ReaderStatus(
            mode="replay", source=self.name, connected=True,
            health={c.field: ChannelHealth(retired=c.csv not in cols)
                    for c in ALL_CHANNELS})

    def __iter__(self):
        while True:
            t0 = None
            t_prev = None
            wall0 = time.monotonic()
            for row_i, row in enumerate(self.rows):
                t = _f(row, "Time")
                if t is None:
                    self.skipped_rows += 1
                    continue
                if t0 is None:
                    t0 = t
                if t_prev is not None and t < t_prev:
                    # Time ran backwards. Trust the file, not the clock.
                    self.skipped_rows += 1
                    continue
                t_prev = t
                rel = t - t0
                if self.speed > 0:
                    target = wall0 + rel / self.speed
                    gap = target - time.monotonic()
                    if gap > 0:
                        time.sleep(min(gap, 1.0))
                vals = {}
                for c in ALL_CHANNELS:
                    v = _f(row, c.csv, c.field)
                    if v == 0.0 and row_i < self._first_real.get(c.field, 0):
                        v = None            # placeholder, not a reading
                    h = self.status.health[c.field]
                    if v is None:
                        if c.csv in row:
                            h.note_miss()
                    else:
                        h.note_ok(rel)
                    vals[c.field] = v
                self.status.samples += 1
                yield Sample(t=rel, **vals)
            if not self.loop:
                return
            self.status.reconnects += 1


class LiveReader:
    """ELM327 over the OBD-II port. READ-ONLY.

    Deliberately thin, and deliberately tolerant. A real adapter drops
    connections, returns 'NO DATA' for PIDs the car does not support, and
    varies its rate with traffic on the bus. None of that should stop the app.

    What it does about each:

      unsupported PID     asked once, and if the car does not answer it
                          MAX_MISSES times running the channel is retired.
                          That hands its share of the link back to the rest.
      slow bus            no fixed rate is assumed. The loop runs as fast as
                          the adapter answers and timestamps every sample, so
                          the estimator integrates real elapsed time rather
                          than an assumed period.
      dropped link        caught, counted, backed off, reconnected. The app
                          keeps serving the last state it had throughout.

    Requires `pip install obd`. Not imported at module load so that replay-mode
    development needs no adapter library installed.
    """

    def __init__(self, port: str | None = None, optional: bool = False):
        try:
            import obd
        except ImportError:
            raise SystemExit(
                "Live mode needs the 'obd' package:  pip install obd\n"
                "Develop in replay mode instead:  python -m app.server --replay <csv>")
        self.obd = obd
        self.port = port
        self.name = "live"
        self.channels = list(LIVE_CHANNELS)
        if optional:
            # Only those with a standard PID are reachable live at all.
            self.channels += [c for c in OPTIONAL_CHANNELS if c.obd]
        else:
            # `boost_psi` is a live channel but has no PID of its own: it is
            # intake pressure minus barometric, so barometric has to come too.
            # This does NOT make the live set seven channels in the sense the
            # budget cares about -- barometric carries min_period_s = 30 s, so
            # it is one round trip every half minute rather than one per cycle.
            self.channels += [c for c in OPTIONAL_CHANNELS
                              if c.field == "p_amb_psi"]
        self.status = ReaderStatus(
            mode="live", source="live OBD-II",
            health={c.field: ChannelHealth() for c in self.channels})
        self.conn = None
        self._last_poll: dict[str, float] = {}
        self._supported: set[str] | None = None
        self._ever_connected = False

    # -- connection ------------------------------------------------------
    def _connect(self):
        """Open the port. Returns True on success, never raises."""
        try:
            self.conn = self.obd.OBD(self.port) if self.port else self.obd.OBD()
            if not self.conn.is_connected():
                self.status.last_error = "adapter not connected"
                self.status.connected = False
                return False
        except Exception as e:                      # adapter libraries throw widely
            self.status.last_error = f"{type(e).__name__}: {e}"
            self.status.connected = False
            return False
        self.status.connected = True
        self.status.last_error = None
        try:
            self._supported = {c.name for c in self.conn.supported_commands}
        except Exception:
            self._supported = None        # unknown: try everything and find out
        return True

    def _close(self):
        try:
            if self.conn is not None:
                self.conn.close()
        except Exception:
            pass
        self.conn = None
        self.status.connected = False

    # -- one channel -----------------------------------------------------
    def _query(self, cmd_name):
        """Query one PID. Returns a float, or None for every kind of failure.

        This is a READ. `conn.query` issues a mode 01/22 request and returns
        the response; nothing here writes to the bus.
        """
        cmd = getattr(self.obd.commands, cmd_name, None)
        if cmd is None:
            return None
        if self._supported is not None and cmd.name not in self._supported:
            return None
        try:
            r = self.conn.query(cmd)
        except Exception as e:
            self.status.last_error = f"{type(e).__name__}: {e}"
            raise ConnectionError(str(e))
        if r is None or r.is_null() or r.value is None:
            return None
        v = getattr(r.value, "magnitude", r.value)
        try:
            v = float(v)
        except (TypeError, ValueError):
            return None
        return None if v != v else v

    def _due(self, c: Channel, now: float) -> bool:
        """Budget: a slow channel is not re-polled just because the loop came
        round again. See the channel-budget note at the top of the file."""
        if c.min_period_s <= 0:
            return True
        last = self._last_poll.get(c.field)
        return last is None or (now - last) >= c.min_period_s
    def __iter__(self):
        t0 = time.monotonic()
        attempt = 0
        held: dict[str, float] = {}     # last good value, for slow channels
        while True:
            if self.conn is None or not self.status.connected:
                if attempt:
                    # First retry is immediate; only a REPEATED failure backs
                    # off, so a Bluetooth blip costs a sample, not ten seconds.
                    time.sleep(RECONNECT_BACKOFF[min(attempt - 1,
                                                     len(RECONNECT_BACKOFF) - 1)])
                attempt += 1
                if not self._connect():
                    continue
                # Counted against "have we ever been connected", not against
                # the retry counter: the retry counter is reset by every
                # success, so it cannot tell a reconnect from the first
                # connect, and a drop that reconnects on the first try would
                # go unrecorded.
                if self._ever_connected:
                    self.status.reconnects += 1
                self._ever_connected = True
                attempt = 0

            now = time.monotonic()
            s = Sample(t=now - t0)
            try:
                for c in self.channels:
                    if c.obd is None:
                        continue          # derived, not polled -- see below
                    h = self.status.health[c.field]
                    if h.retired:
                        continue
                    if not self._due(c, now):
                        # Not due. Re-serve the held value so the estimator
                        # sees a complete sample rather than a hole.
                        if c.field in held:
                            setattr(s, c.field, held[c.field])
                        continue
                    v = self._query(c.obd)
                    if v is None:
                        # AUDIT.md M9: `_last_poll` used to be advanced HERE,
                        # before the query, so a single NO DATA on a slow
                        # channel meant it was not re-asked for its whole
                        # period. Barometric carries min_period_s = 30, and
                        # boost is derived from it, so one transient miss
                        # silenced the mismatch detector for the session. A
                        # miss now does not count as a poll.
                        h.note_miss()
                        if c.field in held:
                            setattr(s, c.field, held[c.field])
                        continue
                    self._last_poll[c.field] = now
                    h.note_ok(s.t)
                    v = c.scale(v)
                    held[c.field] = v
                    setattr(s, c.field, v)

                self._derive_boost(held, s)
            except ConnectionError:
                self._close()
                continue

            self.status.samples += 1
            yield s

    def _derive_boost(self, held, s):
        """Fill `boost_psi`, which no standard OBD-II PID reports.

        The only way the standard set allows is intake pressure minus
        barometric. `p_amb_psi` has already been polled by the loop above (it
        has its own PID and its own 30 s period), so this costs one round trip.

        ON THIS CAR the intake pressure sensor is PRE-THROTTLE -- mistake 2,
        and mistake 13 again for the temperature beside it. That is not a
        problem here, because the only consumer is the mismatch detector, which
        gates itself to wide-open throttle precisely because the channel is
        pre-throttle. It must never be used as manifold pressure; the estimator
        inverts that from air mass instead.
        """
        h = self.status.health["boost_psi"]
        if h.retired:
            return
        intake_kpa = self._query("INTAKE_PRESSURE")
        if intake_kpa is None:
            intake_kpa = held.get("_intake_kpa")
            if intake_kpa is None:
                h.note_miss()
                return
        else:
            held["_intake_kpa"] = intake_kpa
        if s.p_amb_psi is None:
            # AUDIT.md M9. Boost is DERIVED from barometric, so a missing
            # barometric reading is not evidence that boost is unsupported --
            # it is evidence about barometric. Counting a boost miss here
            # retired the channel, and with it the mismatch detector, after
            # five cycles of a transient that had nothing to do with it. Only
            # barometric being retired outright is a real reason to give up.
            if self.status.health["p_amb_psi"].retired:
                h.note_miss()
            return
        h.note_ok(s.t)
        s.boost_psi = intake_kpa * KPA_PER_PSI_INV - s.p_amb_psi


class Stream:
    """Reader + a short in-memory history. NOTHING HERE TOUCHES THE DISK.

    The buffer exists so the review page can show the seconds around an alert
    without the raw stream ever reaching a file. It is a deque with a maxlen:
    old samples are dropped, not archived.
    """

    def __init__(self, reader, history: int = 600):
        self.reader = reader
        self.buf = deque(maxlen=history)   # ~2 minutes at 5 Hz, memory only

    @property
    def status(self):
        return getattr(self.reader, "status", None)

    def __iter__(self):
        for s in self.reader:
            self.buf.append(s)
            yield s

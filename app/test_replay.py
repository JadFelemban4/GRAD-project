"""test_replay.py — the app's regression checks. Replay-driven, no car needed.

    python -m app.test_replay           # fast set, about a minute
    python -m app.test_replay --full    # adds the full 7475b5d7 replay, slower

WHY THIS FILE EXISTS
--------------------
Every number the app reports is the output of a chain: reader -> estimator ->
alert engine. A change anywhere in that chain moves numbers everywhere in it,
and none of the moves announce themselves. Pinning the pipeline against a known
log is what makes a regression visible at all.

It also pins the two product rules that are not about numbers, because those
are the ones a well-meaning change is most likely to break quietly:

    READ-ONLY        no code path in app/ can transmit to the vehicle
    NO RAW ON DISK   a whole replay must create exactly one file, the review
                     log, and that file must contain only marked events

THE BASELINE NUMBERS
--------------------
`pull01` is the fast one: 7 channels, 2193 rows, about 90 seconds to replay at
speed 0. `7475b5d7` is the 26-channel, 40-minute drive the project quotes, and
it takes several minutes, so it is opt-in behind --full.

A count that moves is not automatically a failure -- but it must be EXPLAINED,
and the explanation goes next to the number, the same as any threshold.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.reader import ReplayReader                        # noqa: E402
from app.estimator import Estimator, Sample                # noqa: E402
from app.alerts import AlertEngine, MAF_CEILING_KGH, PSI_TO_KPA  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
LOG_FAST = os.path.join(ROOT, "logs", "raw", "pull01-20260913_093527.csv")
LOG_FULL = os.path.join(ROOT, "logs", "raw", "7475b5d7-20260908_142743.csv")

# ---------------------------------------------------------------------------
# Measured 14 September 2026 on the pipeline as shipped. Regenerate with
# --print if a justified change moves them, and say why in the commit.
# ---------------------------------------------------------------------------
EXPECT_FAST = {           # pull01, 7 channels, 1.45 s per channel
    "rows": 2193, "estimated": 2186,
    "peak_turb_c": 593.7, "thermal": 0, "mismatch": 0, "novel": 4,
}
EXPECT_FULL = {           # 7475b5d7, 26 channels, 7.5 s per channel
    "rows": 14340, "estimated": 14278,
    "peak_turb_c": 884.9, "thermal": 13, "mismatch": 0, "novel": 19,
}

checks: list[tuple[str, bool, str]] = []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"   {detail}" if detail else ""))
    return ok


def replay(path, review_path, speed=0.0):
    """Run the whole pipeline over a log and report what it produced."""
    r = ReplayReader(path, speed=speed)
    est = Estimator()
    al = AlertEngine(review_path=review_path, source=r.name)
    out = {"rows": 0, "estimated": 0, "peak_turb_c": -1e9,
           "thermal": 0, "mismatch": 0, "novel": 0,
           "band_settled_t": None, "first_t": None,
           "nominal_outside_band": 0, "band_widened": 0,
           "thermal_while_warming": 0, "modelled": set()}
    prev_band = None
    for s in r:
        out["rows"] += 1
        st = est.update(s)
        if not st.ok:
            continue
        out["estimated"] += 1
        if out["first_t"] is None:
            out["first_t"] = st.t
        out["peak_turb_c"] = max(out["peak_turb_c"], st.t_turb_c)
        out["modelled"].update(st.modelled)
        if not (st.t_turb_lo_c - 1e-6 <= st.t_turb_c <= st.t_turb_hi_c + 1e-6):
            out["nominal_outside_band"] += 1
        if prev_band is not None and st.seed_band_k > prev_band + 1e-6:
            out["band_widened"] += 1
        prev_band = st.seed_band_k
        if not st.warming_up and out["band_settled_t"] is None:
            out["band_settled_t"] = st.t
        for a in al.check(st, s):
            out[a.kind] += 1
            if a.kind == "thermal" and st.warming_up:
                out["thermal_while_warming"] += 1
    return out


def compare(label, got, want):
    for k, v in want.items():
        g = got[k]
        if isinstance(v, float):
            ok = abs(g - v) <= 0.5
            check(f"{label}: {k}", ok, f"got {g:.1f}, expected {v:.1f}")
        else:
            check(f"{label}: {k}", g == v, f"got {g}, expected {v}")


# ---------------------------------------------------------------------------
# 1. the reader degrades instead of crashing
# ---------------------------------------------------------------------------
def test_reader_tolerance(tmp):
    """A real export is not clean. None of this may raise."""
    path = os.path.join(tmp, "nasty.csv")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write('Time,"Engine speed","Air mass flow","Coolant temperature"\n')
        fh.write('0.0,800,25,90\n')
        fh.write('not_a_number,900,26,90\n')       # unparseable timestamp
        fh.write('0.5,,27,90\n')                   # empty cell
        fh.write('1.0,NaN,28,90\n')                # literal NaN
        fh.write('0.2,1000,29,90\n')               # time runs backwards
        fh.write('1.5,1100,NO DATA,90\n')          # adapter's own miss string
        fh.write('2.0,1200,31\n')                  # short row
    r = ReplayReader(path, speed=0)
    samples = list(r)
    check("reader: survives malformed rows", len(samples) > 0,
          f"{len(samples)} usable, {r.skipped_rows} skipped")
    check("reader: skips bad timestamps and backwards time", r.skipped_rows == 2,
          f"skipped {r.skipped_rows}")
    check("reader: empty and NaN cells become None",
          samples[1].rpm is None and samples[2].rpm is None)
    check("reader: 'NO DATA' becomes None",
          any(s.air_kgh is None for s in samples))
    check("reader: absent columns are marked absent, not invented",
          r.status.health["boost_psi"].retired and "boost_psi" not in r.present)

    est = Estimator()
    for s in samples:
        est.update(s)          # must not raise on any of the above
    check("estimator: survives the same rows", True)


class _FakeObd:
    """An ELM327 that behaves like a real one on a bad day.

    Real adapters do three things this must survive: answer NO DATA for PIDs
    the car does not publish, drop the link mid-drive, and come back. None of
    them may raise out of the reader, and the unsupported PIDs must be RETIRED
    rather than asked forever -- retiring them is what gives their share of the
    link back to the channels that work.
    """
    def __init__(self, drop_at=40):
        self.drop_at = drop_at
        self.calls = 0
        self.connects = 0
        self.dropped_once = False
        fake = type(sys)("obd")
        fake.commands = type("C", (), {})()
        for n in ("RPM", "MAF", "COOLANT_TEMP", "AMBIANT_AIR_TEMP", "SPEED",
                  "TIMING_ADVANCE", "COMMANDED_EQUIV_RATIO", "OIL_TEMP",
                  "BAROMETRIC_PRESSURE", "INTAKE_PRESSURE", "INTAKE_TEMP"):
            setattr(fake.commands, n, type("Cmd", (), {"name": n})())
        outer = self

        class OBD:
            def __init__(self, port=None):
                outer.connects += 1
            def is_connected(self):
                return True
            @property
            def supported_commands(self):
                # the car does not publish oil temperature or lambda
                return [c for c in vars(fake.commands).values()
                        if c.name not in ("OIL_TEMP", "COMMANDED_EQUIV_RATIO")]
            def query(self, cmd):
                outer.calls += 1
                if not outer.dropped_once and outer.calls > outer.drop_at:
                    outer.dropped_once = True
                    raise OSError("bluetooth went away")
                val = {"RPM": 3000.0, "MAF": 120.0, "COOLANT_TEMP": 92.0,
                       "AMBIANT_AIR_TEMP": 35.0, "SPEED": 100.0,
                       "TIMING_ADVANCE": 12.0, "BAROMETRIC_PRESSURE": 99.0,
                       "INTAKE_PRESSURE": 180.0, "INTAKE_TEMP": 60.0,
                       }.get(cmd.name)
                null = val is None
                return type("R", (), {
                    "is_null": lambda self, _n=null: _n,
                    "value": type("V", (), {"magnitude": val})()})()
            def close(self):
                pass
        fake.OBD = OBD
        self.module = fake


def test_live_reader_degrades():
    from app.reader import LiveReader, MAX_MISSES
    fake = _FakeObd(drop_at=40)
    sys.modules["obd"] = fake.module
    try:
        r = LiveReader(port="fake")
        got = []
        for s in r:
            got.append(s)
            if len(got) >= 25:
                break
    finally:
        sys.modules.pop("obd", None)

    check("live: yields samples through a dropped connection",
          len(got) == 25, f"{len(got)} samples")
    check("live: reconnected after the drop", r.status.reconnects >= 1,
          f"{r.status.reconnects} reconnects, {fake.connects} connects")
    check("live: supported channels keep answering",
          all(getattr(got[-1], f) is not None
              for f in ("rpm", "air_kgh", "ect_c", "t_amb_c", "v_kmh")))
    check("live: MAF converted to kg/h", abs(got[-1].air_kgh - 120.0 * 3.6) < 1e-6,
          f"{got[-1].air_kgh:.1f} kg/h")
    check("live: boost derived from intake minus barometric",
          got[-1].boost_psi is not None
          and abs(got[-1].boost_psi - (180.0 - 99.0) / 6.894757) < 1e-3,
          f"{got[-1].boost_psi:.2f} psi")
    unsupported = [f for f in ("oil_c", "lam")
                   if r.status.health[f].retired]
    check("live: PIDs the car refuses are RETIRED, not asked forever",
          len(unsupported) == 2,
          f"retired {unsupported}; each after {MAX_MISSES} misses")
    check("live: the link never raised out of the reader", True)


def test_missing_channels(tmp):
    """A log without coolant must be MODELLED and SAID, not silently defaulted."""
    out = replay(LOG_FAST, os.path.join(tmp, "r.jsonl"))
    check("estimator: names every modelled input",
          {"coolant", "ambient"} <= out["modelled"],
          f"modelled: {sorted(out['modelled'])}")


# ---------------------------------------------------------------------------
# 2. the warm-start bound behaves like a bound
# ---------------------------------------------------------------------------
def test_warm_start(fast):
    check("warm start: nominal never leaves the band",
          fast["nominal_outside_band"] == 0,
          f"{fast['nominal_outside_band']} samples outside")
    check("warm start: the band never widens on a continuous stream",
          fast["band_widened"] == 0, f"{fast['band_widened']} widenings")
    check("warm start: no thermal alert fires while warming up",
          fast["thermal_while_warming"] == 0)
    check("warm start: the band does settle",
          fast["band_settled_t"] is not None,
          f"settled at t={fast['band_settled_t']:.0f} s"
          if fast["band_settled_t"] is not None else "never settled")


def test_warm_start_is_not_a_timer():
    """The seed is forgotten at whatever rate the driving allows.

    This is the point of CLAUDE.md-style honesty here: a fixed 145 s timer
    assumed tau = 48 s, which is the LOADED time constant. Idling, the turbine
    node's tau is nearer 240 s. Two synthetic streams, identical except for
    load, must therefore settle at visibly different times.
    """
    def settle(air_kgh, rpm):
        est = Estimator()
        t, last = 0.0, None
        while t < 3000.0:
            st = est.update(Sample(t=t, rpm=rpm, air_kgh=air_kgh, ect_c=92.0,
                                   t_amb_c=35.0, v_kmh=100.0))
            if st.ok and not st.warming_up:
                return t
            last = st
            t += 1.0
        return None
    idle = settle(40.0, 900)          # barely breathing
    load = settle(700.0, 4000)        # working hard
    ok = idle is not None and load is not None and idle > load * 1.5
    check("warm start: settles later at light load than under load", ok,
          f"light load {idle} s vs loaded {load} s")


# ---------------------------------------------------------------------------
# 3. the mismatch detector only speaks where the comparison is valid
# ---------------------------------------------------------------------------
def _sample(air_kgh, boost_psi, p_amb_psi=14.3, t=0.0):
    return Sample(t=t, rpm=4000, air_kgh=air_kgh, ect_c=92.0, t_amb_c=35.0,
                  v_kmh=120.0, boost_psi=boost_psi, p_amb_psi=p_amb_psi)


def test_mismatch_gates(tmp):
    amb_kpa = 14.3 * PSI_TO_KPA

    # part throttle: pre-throttle sensor near ambient. This is the -52 % that
    # produced 55 false events, and it must now produce none.
    est, al = Estimator(), AlertEngine(review_path=os.path.join(tmp, "a.jsonl"))
    fired = 0
    for i in range(400):
        s = _sample(150.0, 0.5, t=i * 0.25)       # PR ~ 1.03
        st = est.update(s)
        fired += sum(1 for a in al.check(st, s) if a.kind == "mismatch")
    check("mismatch: silent at part throttle", fired == 0, f"{fired} fired")
    check("mismatch: part-throttle samples never reach the window",
          al.gated_samples == 0, f"{al.gated_samples} gated")

    # MAF pinned at its ceiling under real boost: excluded (mistake 7)
    est, al = Estimator(), AlertEngine(review_path=os.path.join(tmp, "b.jsonl"))
    for i in range(400):
        s = _sample(MAF_CEILING_KGH, 2.0 * amb_kpa / PSI_TO_KPA, t=i * 0.25)
        st = est.update(s)
        al.check(st, s)
    check("mismatch: a pinned MAF never reaches the window",
          al.gated_samples == 0, f"{al.gated_samples} gated")

    # forward-filled repeats must not fill the window on their own
    est, al = Estimator(), AlertEngine(review_path=os.path.join(tmp, "c.jsonl"))
    boost_psi = (2.2 * amb_kpa) / PSI_TO_KPA - 14.3
    for i in range(500):
        s = _sample(300.0, boost_psi, t=i * 0.15)    # identical reading, held
        st = est.update(s)
        al.check(st, s)
    check("mismatch: forward-filled repeats count as ONE reading",
          al.gated_readings == 1,
          f"{al.gated_samples} samples -> {al.gated_readings} readings")

    # A real, persistent, wide-open-throttle disagreement DOES still fire.
    #
    # 400 kg/h at 4000 rpm inverts to 114 kPa against a sensor reading 217 kPa
    # -- a standing -47 %, which is what a badly restricted intake looks like.
    # (800 kg/h is where the two agree at this operating point, so this is a
    # genuine fault signature and not a gate artefact.) The small jitter makes
    # each sample a distinct reading rather than a forward-filled repeat.
    est, al = Estimator(), AlertEngine(review_path=os.path.join(tmp, "d.jsonl"))
    fired = 0
    for i in range(60):
        s = _sample(400.0 + (i % 5) * 0.5, boost_psi, t=i * 1.0)
        st = est.update(s)
        fired += sum(1 for a in al.check(st, s) if a.kind == "mismatch")
    check("mismatch: a persistent full-throttle disagreement still fires",
          fired > 0, f"{fired} fired, {al.gated_readings} readings")


# ---------------------------------------------------------------------------
# 4. the two product rules
# ---------------------------------------------------------------------------
def test_read_only():
    """No code path in app/ can transmit to the vehicle.

    Structural, not behavioural: the guarantee is that the code to do it does
    not exist. python-obd's only write paths are the low-level interface, so
    those names are what this looks for.
    """
    banned = [
        (r"send_and_parse", "low-level ELM327 write"),
        (r"\.write\s*\(", "raw port write"),
        (r"import\s+serial", "direct serial access, bypassing obd"),
        (r"CLEAR_DTC|clear_dtc", "mode 04, a write"),
        (r"obd\.protocols\..*send", "protocol-level send"),
    ]
    bad = []
    for fn in sorted(os.listdir(HERE)):
        # This file is the checker, not the product: it necessarily contains
        # the forbidden patterns as the things it searches for.
        if not fn.endswith(".py") or fn == os.path.basename(__file__):
            continue
        src = open(os.path.join(HERE, fn), encoding="utf-8").read()
        # strip docstrings/comments so the prohibition text itself is not a hit
        code = re.sub(r'""".*?"""', "", src, flags=re.S)
        code = re.sub(r"#.*", "", code)
        for pat, why in banned:
            for m in re.finditer(pat, code):
                # the review file and the websocket are not the vehicle
                line = code[:m.start()].count("\n") + 1
                seg = code.splitlines()[line - 1] if line <= len(code.splitlines()) else ""
                if "fh.write" in seg or "sock.send" in seg:
                    continue
                bad.append(f"{fn}:{line} {why}")
    check("READ-ONLY: no write path to the vehicle exists in app/",
          not bad, "; ".join(bad) if bad else "checked 5 patterns")


def test_no_raw_on_disk(tmp):
    """A whole replay must create exactly one file, and it holds only events."""
    sandbox = os.path.join(tmp, "privacy")
    os.makedirs(sandbox)
    review = os.path.join(sandbox, "review_log.jsonl")
    before = set(os.listdir(sandbox))
    replay(LOG_FAST, review)
    after = set(os.listdir(sandbox))
    created = after - before
    check("NO RAW ON DISK: a replay creates exactly one file",
          created == {"review_log.jsonl"}, f"created {sorted(created)}")

    allowed = {"session", "source", "wall", "kind", "severity", "t",
               "title", "advice", "audience", "evidence"}
    leaked, n = set(), 0
    with open(review, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            n += 1
            rec = json.loads(line)
            leaked |= set(rec) - allowed
    check("NO RAW ON DISK: records carry only marked-event fields",
          not leaked, f"{n} records, unexpected keys: {sorted(leaked)}"
          if leaked else f"{n} records")

    # A sample stream would be orders of magnitude bigger than its alerts.
    rows = sum(1 for _ in open(LOG_FAST, encoding="utf-8", errors="replace"))
    check("NO RAW ON DISK: far fewer records than samples", n < rows / 50,
          f"{n} records against {rows} rows")


def test_channel_budget():
    """Every live channel must justify its slice of the link."""
    from app.reader import LIVE_CHANNELS
    missing = [c.field for c in LIVE_CHANNELS if not c.why or len(c.why) < 20]
    check("channel budget: every live channel carries a reason", not missing,
          f"{len(LIVE_CHANNELS)} channels" if not missing else str(missing))
    check("channel budget: the live set is still six", len(LIVE_CHANNELS) == 6,
          f"{len(LIVE_CHANNELS)} channels")


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--full", action="store_true",
                    help="also replay 7475b5d7 end to end (several minutes)")
    ap.add_argument("--print", dest="show", action="store_true",
                    help="print what the pipeline produces, and do not compare")
    a = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        if a.show:
            for label, log in (("pull01", LOG_FAST), ("7475b5d7", LOG_FULL)):
                if log == LOG_FULL and not a.full:
                    continue
                out = replay(log, os.path.join(tmp, f"{label}.jsonl"))
                print(f"\n{label}:")
                for k in ("rows", "estimated", "peak_turb_c", "thermal",
                          "mismatch", "novel", "band_settled_t"):
                    print(f"    {k:16s} {out[k]}")
            return

        print("\nreader")
        test_reader_tolerance(tmp)
        test_live_reader_degrades()

        print("\nreplay: pull01 (7 channels, the fast regression)")
        fast = replay(LOG_FAST, os.path.join(tmp, "fast.jsonl"))
        compare("pull01", fast, EXPECT_FAST)
        test_missing_channels(tmp)

        print("\nwarm start")
        test_warm_start(fast)
        test_warm_start_is_not_a_timer()

        print("\nmismatch detector")
        test_mismatch_gates(tmp)

        print("\nproduct rules")
        test_read_only()
        test_no_raw_on_disk(tmp)
        test_channel_budget()

        if a.full:
            print("\nreplay: 7475b5d7 (26 channels, the quoted drive)")
            full = replay(LOG_FULL, os.path.join(tmp, "full.jsonl"))
            compare("7475b5d7", full, EXPECT_FULL)
            test_warm_start(full)

    n_ok = sum(1 for _, ok, _ in checks if ok)
    print(f"\n{n_ok} of {len(checks)} checks pass")
    if n_ok != len(checks):
        print("""
A count that moved is not automatically a bug, but it is not nothing either.
Find out WHICH stage moved it -- reader, estimator or alert engine -- before
updating the expected value, and put the reason next to the number the same way
a threshold change carries its measurement.""")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

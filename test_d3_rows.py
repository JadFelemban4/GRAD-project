"""test_d3_rows.py -- C3 and C4's reader, segments, chain and rows, on SYNTHETIC traces only (amendment C5;
WP3_INTERFACES.md 9.10). Written 23 October 2026, build step 2, WP3.

    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python test_d3_rows.py

No test here opens a D3 file, a D3 summary, an EPA table, the data folder, logs/ or the real contract:
every class runs inside test_epa_fixtures.forbid_real_data, an audit hook that fails the test on such an
open, and the hook is itself shown to fire (mistake 12). d3_rows' first real read is inside validate_epa.py
run (MD:451). RealModel and WholeChain run epa_fit.RowModel on the B58 at synthetic inputs only.

Each rule is shown both ways: the trace that passes it gives its segment (the control), and the same
trace with only that rule broken loses or splits it. A check that cannot fail is not a check.

What each class proves:
  Guard        the shared audit hook refuses an open under the data folder and logs/, and fails its block
  Reader       the header is resolved before any value is converted; a missing or doubled channel stops;
               the clipped Direct channel is never converted; the padding rows go; units are converted
  Segments     every rule of MD section 5 cuts (3 s, +-25 rpm, two MAP refreshes, the converter within
               1 %, A/C, one gear, coolant 83.8 C), windows are sized in seconds, not samples, and a gear
               code the car has no ratio for is cut (mistake 18); on the Accord the converter and A/C rules
               cut with its own channels (decision 81)
  Demand       demand_torque against a hand value, for a stepped box and for the CVT's power balance
  Checks       Direct2 against the summary, the MAF against Direct2 x AFR_st x lambda on closed-loop
               segments, flat maxima found and dropped (and a scan-tool hold not taken for one), the
               lambda reading's diagnostic, the PCM MAP at closed throttle
  Summary      the workbook read through zipfile; the real specs pinned, each pin with its source, and a pin
               without one refused; decision 80's rows (the base phase rows summed, the sum rows left out, a
               test with one row, the section headings and another test's cells never read, disagreeing
               heating values refused); decision 79's assumed density and its u in the Direct2 check
  Contract     the rules against the contract's wording, u_input 5.25 %, E6 row 10's two efficiencies,
               the gear codes against the CX-9's published ratios
  Chain        D1's inversion by hand, the ECU's dwell run on the car's own PCM MAP, a segment end to end
  Rows         C3's populations and its labels through epa_stats
  RealModel    the dwell timer and a segment end to end through epa_fit.RowModel on the B58
  WholeChain   run_chain from files to a JSON-safe c3.json body, through epa_fit.ordered_map
  Imports      d3_rows imports no plant module and no epa_rows, prints nothing, names no EPA table
"""
import ast
import math
import os
import sys
import tempfile
import types
import unittest
import zipfile
from unittest import mock
from dataclasses import dataclass, replace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np                                    # noqa: E402

import d3_rows                                        # noqa: E402
import test_epa_fixtures as fx                        # noqa: E402
from thresholds import common                         # noqa: E402

# Imported unconditionally (WP3's second fix of 23 October 2026, on the test review's finding): the tests that
# read epa_stats and epa_fit skipped silently while either was missing a name, a leftover of the parallel
# writing, so they could no longer fail on it; commit C ships every step-2 module together.
import epa_stats                                      # noqa: E402

# Every number below is synthetic; the AFR_st and the heating values are made-up round figures, never
# the contract's, so no test leans on a real value (only Contract checks the contract's own arithmetic).
AFR = 14.5
EPA_LHV, D3_LHV = 18000.0, 18300.0


# ============================================================================ the guard

# The shared guard (WP3_INTERFACES.md 9.1): every class here runs its setup and each test inside
# test_epa_fixtures.forbid_real_data, which refuses an open of the real EPA tables, logs/, the real
# contract, the generator's split.json and the team's data folder, and fails the block on any attempt.
Guarded = fx.Guarded


# ============================================================================ synthetic traces

def base_arrays(*, seconds=20.0, dt=0.1, t0=0.0, rpm=2000.0, gear=4.0, map_kpa=60.0, refresh_every=5,
                force=1500.0, direct2=3.0, lam=1.0, coolant=90.0, speed=80.0):
    """A synthetic CX-9 cruise: everything steady and inside every rule, the PCM MAP stepping by 0.5 kPa
    every refresh_every samples (a scan-tool channel's hold), the MAF exactly Direct2 x AFR x lambda."""
    n = int(round(seconds / dt)) + 1
    t = t0 + dt * np.arange(n)
    mp = map_kpa + 0.5 * ((np.arange(n) // refresh_every) % 2)
    return {"time": t, "force": np.full(n, force), "gear": np.full(n, gear), "rpm": np.full(n, rpm),
            "turbine_rpm": np.full(n, rpm * 0.997), "ac": np.zeros(n), "map": mp,
            "direct2": np.full(n, direct2), "maf": np.full(n, direct2 * AFR * lam),
            "lam": np.full(n, 1.0 / lam), "coolant": np.full(n, coolant), "speed": np.full(n, speed)}


def trace(arrays, test="T1"):
    return d3_rows.make_trace(test, channels=d3_rows.CHANNELS, arrays=arrays)


def segs(arrays, rules=None, test="T1"):
    return d3_rows.segments(trace(arrays, test), rules=rules or d3_rows.CONTRACT_SEGMENTS, afr_st=AFR)


def mid(arrays, key, value, a_s, b_s):
    """Set arrays[key] to value for a_s <= t < b_s; returns arrays."""
    t = arrays["time"]
    arrays[key] = np.where((t >= a_s) & (t < b_s), value, arrays[key])
    return arrays


def write_d3(path, channels, arrays, *, header_pick=0, extra=(), drop=(), double=None, garbage=None):
    """A D3-style file: tab-separated latin-1, one header row. extra: (header, cell) columns appended
    (the clipped Direct channel, a latin-1 name). drop: roles left out of the header. double: a role
    written twice. garbage: (role or extra header, row index) whose cell is not a number."""
    cols = [(ch.headers[min(header_pick, len(ch.headers) - 1)][0], ch.role) for ch in channels.channels
            if ch.role not in drop]
    if double:
        cols.append(next(c for c in cols if c[1] == double))
    n = len(arrays["time"])
    names = [c[0] for c in cols] + [h for h, _ in extra]
    with open(path, "w", encoding=channels.dialect.encoding, newline="") as fh:
        fh.write("\t".join(names) + "\r\n")
        for k in range(n):
            cells = []
            for h, role in cols:
                v = arrays[role][k]
                f = dict(next(ch for ch in channels.channels if ch.role == role).headers)[h]
                cells.append(repr(float(v) / f))
            cells += [c for _, c in extra]
            if garbage is not None and garbage[1] == k:
                j = names.index(garbage[0]) if garbage[0] in names else [c[1] for c in cols].index(garbage[0])
                cells[j] = "n/a?"
            fh.write("\t".join(cells) + "\r\n")


# ============================================================================ a toy model (hand answers)

@dataclass(frozen=True)
class ToyOut:
    torque_nm: float
    fuel_gps: float
    air_gps: float
    egt_c: float
    knock_integral: float
    eta_v: float


@dataclass(frozen=True)
class ToyEcu:
    spark_btdc: float
    lam: float
    cam_deg: object


class ToyModel:
    """The model protocol of WP3_INTERFACES.md 5.2.2 in closed form: torque = 2 (MAP - 30) N m, fuel =
    0.05 MAP g/s, air = fuel x AFR x lambda; the ECU's spark 20 - 0.1 MAP, its lambda 1 until the MAP has
    sat above GATE for DWELL_S seconds, then 0.85 (a dwell timer, run sample by sample along a trace);
    the charge t_amb + 12 + 0.06 (block - t_amb)."""
    GATE, DWELL_S = 150.0, 4.0

    def __init__(self):
        self.calls = 0

    def cycle(self, x, *, dtheta):
        self.calls += 1
        f = 0.05 * x.map_kpa * (1.0 + 0.001 * dtheta)
        return ToyOut(torque_nm=2.0 * (x.map_kpa - 30.0), fuel_gps=f, air_gps=f * AFR * x.lam, egt_c=700.0,
                      knock_integral=0.0, eta_v=0.9)

    def ecu_at(self, rpm, map_kpa, iat_k, ect_k):
        return ToyEcu(spark_btdc=20.0 - 0.1 * map_kpa, lam=1.0, cam_deg=None)

    def ecu_trace(self, rpm, map_kpa, iat_k, ect_k, dt):
        # dt one scalar, as epa_fit.RowModel.ecu_trace passes it to every BaselineECU.step
        self.dt_seen = dt
        dwell, lam = 0.0, np.ones(len(rpm))
        for k in range(len(rpm)):
            dwell = dwell + dt if map_kpa[k] > self.GATE else 0.0
            lam[k] = 0.85 if dwell >= self.DWELL_S else 1.0
        return 20.0 - 0.1 * np.asarray(map_kpa), lam

    def charge(self, t_amb_k, t_block_k):
        return t_amb_k + 12.0 + (0.0 if t_block_k is None else 0.06 * (t_block_k - t_amb_k))

    def cam(self, rpm, map_kpa):
        return None


CX9 = types.SimpleNamespace(id="cx9_synthetic", wheel_r=0.37, final_drive=4.0, gears=(3.5, 2.0, 1.45, 1.0, 0.7, 0.6))
CVT = types.SimpleNamespace(id="cvt_synthetic", wheel_r=0.33, final_drive=5.0)


# ============================================================================ the tests

class Guard(Guarded):
    def test_an_open_of_real_data_is_refused(self):
        # The control: the hook fires before the OS opens anything (neither path exists), and the block
        # it was attempted in fails on leaving, though the test caught the refusal.
        for p in (os.path.join(common.DATA_FOLDER, "__never_opened__.txt"),
                  os.path.join(common.REPO, "logs", "__never_opened__.csv")):
            with self.assertRaises(AssertionError):
                with fx.forbid_real_data():
                    with self.assertRaises(PermissionError):
                        open(p, "rb")

    def test_a_scratch_file_is_not_refused(self):
        """The guard's other side: a scratch file is written and read back inside forbid_real_data, and leaving the
        block raises nothing (WP3's third fix of 24 October 2026: the test asserted nothing)."""
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.txt")
            with fx.forbid_real_data():
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write("ok")
                with open(p, encoding="utf-8") as fh:
                    self.assertEqual(fh.read(), "ok")


class Reader(Guarded):
    def setUp(self):
        super().setUp()                                   # the guard, per test (Guarded.setUp)
        self.d = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.d.name, "61700000 Test Data.txt")

    def tearDown(self):
        self.d.cleanup()

    def test_a_file_reads_back_as_written(self):
        a = base_arrays(seconds=5.0)
        write_d3(self.path, d3_rows.CHANNELS, a)
        tr = d3_rows.read_trace(self.path, test="61700000", channels=d3_rows.CHANNELS)
        self.assertEqual(len(tr), len(a["time"]))
        for role, fld in d3_rows._FIELD.items():
            np.testing.assert_allclose(getattr(tr, fld), a[role], rtol=1e-15, atol=0.0, err_msg=role)

    def test_the_clipped_direct_channel_is_never_converted(self):
        # Its cells hold text that float() refuses: the read passes only because it never converts them.
        a = base_arrays(seconds=2.0)
        write_d3(self.path, d3_rows.CHANNELS, a, extra=(("Eng_FuelFlow_Direct[ccps]", "clipped!"),
                                                        ("Engine_Bay_Temp[°C]", "21.5")))
        d3_rows.read_trace(self.path, test="x", channels=d3_rows.CHANNELS)
        # Control: the same text in a pinned column stops the read, naming no value.
        write_d3(self.path, d3_rows.CHANNELS, a, garbage=("direct2", 3))
        with self.assertRaises(d3_rows.TraceDefect) as cm:
            d3_rows.read_trace(self.path, test="x", channels=d3_rows.CHANNELS)
        self.assertNotIn("n/a?", str(cm.exception))

    def test_a_header_missing_a_channel_stops_before_any_value_is_converted(self):
        a = base_arrays(seconds=2.0)
        for role in [ch.role for ch in d3_rows.CHANNELS.channels]:
            # A garbage cell in row 0: a reader that converted before checking the header would raise
            # TraceDefect (or ValueError) instead of HeaderDefect.
            keep = next(c.role for c in d3_rows.CHANNELS.channels if c.role != role)
            write_d3(self.path, d3_rows.CHANNELS, a, drop=(role,), garbage=(keep, 0))
            with self.assertRaises(d3_rows.HeaderDefect, msg=role):
                d3_rows.read_trace(self.path, test="x", channels=d3_rows.CHANNELS)

    def test_a_channel_twice_stops(self):
        a = base_arrays(seconds=2.0)
        write_d3(self.path, d3_rows.CHANNELS, a, double="maf")
        with self.assertRaises(d3_rows.HeaderDefect):
            d3_rows.read_trace(self.path, test="x", channels=d3_rows.CHANNELS)
        # Two accepted spellings of one channel are a channel twice too.
        write_d3(self.path, d3_rows.CHANNELS, a, extra=(("Eng_speed_CAN", "2000"),))
        with self.assertRaises(d3_rows.HeaderDefect):
            d3_rows.read_trace(self.path, test="x", channels=d3_rows.CHANNELS)
        # Control: either spelling alone reads.
        write_d3(self.path, d3_rows.CHANNELS, a, header_pick=1)
        d3_rows.read_trace(self.path, test="x", channels=d3_rows.CHANNELS)

    def test_the_padding_rows_are_dropped(self):
        a = base_arrays(seconds=10.0)
        n = len(a["time"])
        pad = {k: np.concatenate([v, np.full(300, v[-1])]) for k, v in a.items()}
        pad["time"] = np.concatenate([a["time"], np.full(300, a["time"][-1])])   # the frozen stamp
        pad["rpm"][n:] = 2600.0          # a padding row that a segment would otherwise reach into
        write_d3(self.path, d3_rows.CHANNELS, pad)
        tr = d3_rows.read_trace(self.path, test="x", channels=d3_rows.CHANNELS)
        self.assertEqual(len(tr), n)
        self.assertEqual(tr.padding_dropped, 300)
        self.assertEqual(float(tr.rpm.max()), 2000.0)
        # Control: drop_padding keeps a trace whose maximum is its last stamp whole.
        self.assertEqual(d3_rows.drop_padding(a["time"]), n)

    def test_time_that_runs_backwards_stops(self):
        a = base_arrays(seconds=2.0)
        a["time"] = a["time"].copy()
        a["time"][5] = a["time"][3]
        with self.assertRaises(d3_rows.TraceDefect):
            trace(a)

    def test_the_road_speed_is_converted_from_mph(self):
        a = base_arrays(seconds=1.0, speed=80.0)
        write_d3(self.path, d3_rows.CHANNELS, a)
        with open(self.path, encoding="latin-1") as fh:
            row = fh.read().splitlines()[1].split("\t")
        names = [ch.headers[0][0] for ch in d3_rows.CHANNELS.channels]
        self.assertAlmostEqual(float(row[names.index("Dyno_Spd[mph]")]), 80.0 / 1.609344, places=12)
        tr = d3_rows.read_trace(self.path, test="x", channels=d3_rows.CHANNELS)
        self.assertAlmostEqual(float(tr.speed_kph[0]), 80.0, places=12)

    def test_the_accord_reads_its_own_channels_and_not_the_cx9s(self):
        a = base_arrays(seconds=2.0)
        acc = {r: a[r] for r in d3_rows.ACCORD_CHANNELS.roles()}
        acc["lam"] = np.full(len(a["time"]), AFR)
        write_d3(self.path, d3_rows.ACCORD_CHANNELS, acc)
        tr = d3_rows.read_trace(self.path, test="x", channels=d3_rows.ACCORD_CHANNELS)
        self.assertIsNone(tr.gear)
        self.assertIsNone(tr.coolant_c)
        np.testing.assert_allclose(d3_rows.lam_of(tr, afr_st=AFR), 1.0)
        np.testing.assert_allclose(tr.turbine_rpm, a["turbine_rpm"])            # decision 81's channels read
        np.testing.assert_allclose(tr.ac, a["ac"])
        # Control: the CX-9's pins do not read an Accord file, and an Accord file without the turbine speed
        # stops at its header (decision 81 made it a pinned channel).
        with self.assertRaises(d3_rows.HeaderDefect):
            d3_rows.read_trace(self.path, test="x", channels=d3_rows.CHANNELS)
        write_d3(self.path, d3_rows.ACCORD_CHANNELS, acc, drop=("turbine_rpm",))
        with self.assertRaises(d3_rows.HeaderDefect):
            d3_rows.read_trace(self.path, test="x", channels=d3_rows.ACCORD_CHANNELS)


class Segments(Guarded):
    R = d3_rows.CONTRACT_SEGMENTS

    def test_the_control_trace_is_one_segment(self):
        s = segs(base_arrays(seconds=20.0))
        self.assertEqual(len(s), 1)
        self.assertEqual((s[0].i0, s[0].n), (0, 201))
        self.assertEqual(s[0].gear, 4)

    def test_three_seconds(self):
        self.assertEqual(len(segs(base_arrays(seconds=3.0))), 1)
        self.assertEqual(len(segs(base_arrays(seconds=2.9))), 0)

    def test_windows_are_seconds_not_samples(self):
        # Mistake 8: 7 samples at 0.5 s span 3 s and are a segment; 30 samples at 0.05 s span 1.45 s and
        # are not, though they are four times as many samples.
        slow = base_arrays(seconds=3.0, dt=0.5, refresh_every=1)
        self.assertEqual(len(segs(slow, rules=replace(self.R, max_gap_s=0.6))), 1)
        fast = base_arrays(seconds=1.45, dt=0.05)
        self.assertEqual(len(fast["time"]), 30)
        self.assertEqual(len(segs(fast)), 0)

    def test_twenty_five_rpm(self):
        a = base_arrays(seconds=20.0)
        a["rpm"] = 2000.0 + 24.0 * np.sin(np.arange(len(a["time"])))          # inside +-25: kept whole
        a["turbine_rpm"] = a["rpm"] * 0.997
        self.assertEqual(len(segs(a)), 1)
        b = base_arrays(seconds=20.0)
        b = mid(b, "rpm", 2060.0, 10.0, 30.0)                                   # a 60 rpm step at 10 s
        b["turbine_rpm"] = b["rpm"] * 0.997
        s = segs(b)
        self.assertEqual([x.rpm_mean for x in s], [2000.0, 2060.0])

    def test_two_map_refreshes(self):
        a = base_arrays(seconds=5.0, refresh_every=10 ** 6)                     # the MAP never changes
        self.assertEqual(len(segs(a)), 0)
        b = base_arrays(seconds=5.0)
        b["map"] = np.where(b["time"] < 1.0, 60.0, np.where(b["time"] < 2.0, 61.0, 60.0))  # two changes
        self.assertEqual(len(segs(b)), 1)
        self.assertEqual(segs(b)[0].map_refreshes, 2)
        c = base_arrays(seconds=5.0)
        c["map"] = np.where(c["time"] < 1.0, 60.0, 61.0)                        # one change
        self.assertEqual(len(segs(c)), 0)

    def test_the_converter_locked_within_one_percent(self):
        a = base_arrays(seconds=20.0)
        a["turbine_rpm"] = a["rpm"] / 1.0099                                   # 0.99 % slip: locked
        self.assertEqual(len(segs(a)), 1)
        b = mid(base_arrays(seconds=20.0), "turbine_rpm", 2000.0 / 1.02, 9.0, 10.0)   # 2 % slip for 1 s
        s = segs(b)
        self.assertEqual(len(s), 2)
        self.assertTrue(all(x.t1_s < 9.0 or x.t0_s >= 10.0 for x in s))

    def test_ac_off(self):
        s = segs(mid(base_arrays(seconds=20.0), "ac", 1.0, 9.0, 10.0))
        self.assertEqual(len(s), 2)
        self.assertTrue(all(x.t1_s < 9.0 or x.t0_s >= 10.0 for x in s))
        self.assertEqual(len(segs(mid(base_arrays(seconds=20.0), "ac", np.nan, 9.0, 10.0))), 2)

    def test_one_gear(self):
        a = mid(base_arrays(seconds=20.0), "gear", 5.0, 10.0, 30.0)
        s = segs(a)
        self.assertEqual([x.gear for x in s], [4, 5])
        # Control: with the rule off the gear change no longer cuts (the flag governs it, nothing else).
        self.assertEqual(len(segs(a, rules=replace(self.R, one_gear=False))), 1)
        self.assertEqual(len(segs(mid(base_arrays(seconds=20.0), "gear", 0.0, 9.0, 10.0))), 2)   # neutral

    def test_a_gear_code_that_is_not_a_forward_gear_is_cut(self):
        # Mistake 18: the channel's range, not only its name. Five seconds at a code the car has no ratio
        # for (7, or 2.5) are no segment, and every segment left prices through the car's own ratios.
        for code in (7.0, 2.5, -1.0):
            a = mid(base_arrays(seconds=30.0), "gear", code, 10.0, 15.0)
            s = segs(a)
            self.assertEqual([x.gear for x in s], [4, 4], msg=code)
            for x in s:
                d3_rows.demand_torque(x, car=CX9, eta=0.92)
        # Control: the same five seconds in 6th, a gear the car has, are a segment of their own.
        s = segs(mid(base_arrays(seconds=30.0), "gear", 6.0, 10.0, 15.0))
        self.assertEqual([x.gear for x in s], [4, 6, 4])
        # A car record with a gear channel must say which codes are gears (no silent default, mistake 1).
        with self.assertRaises(ValueError):
            replace(d3_rows.CHANNELS, gear_codes=None)

    def test_coolant_floor(self):
        self.assertEqual(len(segs(base_arrays(seconds=20.0, coolant=83.8))), 1)   # at the floor: kept
        s = segs(mid(base_arrays(seconds=20.0), "coolant", 83.0, 9.0, 10.0))
        self.assertEqual(len(s), 2)
        self.assertEqual(len(segs(base_arrays(seconds=20.0, coolant=83.0))), 0)

    def test_a_time_gap_is_never_bridged(self):
        a = base_arrays(seconds=20.0)
        a["time"] = a["time"] + np.where(a["time"] >= 10.0, 0.5, 0.0)
        self.assertEqual(len(segs(a)), 2)

    def test_the_census_names_what_each_rule_cut(self):
        a = mid(mid(base_arrays(seconds=20.0), "ac", 1.0, 9.0, 10.0), "coolant", 80.0, 14.0, 15.0)
        c = d3_rows.segment_census(trace(a), rules=self.R)
        self.assertEqual(c["cut_by"]["ac_off"], 10)
        self.assertEqual(c["cut_by"]["coolant"], 10)
        self.assertEqual(c["cut_by"]["converter_locked"], 0)
        self.assertEqual(c["not_applied"], [])
        acc = {r: base_arrays(seconds=5.0)[r] for r in d3_rows.ACCORD_CHANNELS.roles()}
        acc["lam"] = np.full(len(acc["time"]), AFR)
        tr = d3_rows.make_trace("A", channels=d3_rows.ACCORD_CHANNELS, arrays=acc)
        na = d3_rows.segment_census(tr, rules=self.R)["not_applied"]
        # decision 81: the converter and A/C rules apply on the Accord; only the gear and coolant do not
        self.assertEqual(na, ["one_gear (no gear channel: a CVT)", "coolant (no live coolant channel)"])

    def test_the_accords_converter_and_ac_rules_cut(self):
        """Decision 81: the Accord's chain applies the converter-lock and A/C rules as C3 does, with its own
        channels (Trans_torque_converter_turbine_spd_AT__rpm, HVAC_AC_clutch_PGM, each in 56 of 56 files by
        the catalogue's column list), and its time and road-speed headers are the list's. Controls: the
        steady trace is one segment; one second of 2 % slip, or of the compressor clutched, splits it."""
        self.assertEqual(d3_rows.ACCORD_CHANNELS.roles(),
                         ("time", "force", "rpm", "turbine_rpm", "ac", "map", "direct2", "maf", "lam", "speed"))
        heads = {c.role: c.headers for c in d3_rows.ACCORD_CHANNELS.channels}
        self.assertEqual(heads["turbine_rpm"], (("Trans_torque_converter_turbine_spd_AT__rpm", 1.0),))
        self.assertEqual(heads["ac"], (("HVAC_AC_clutch_PGM", 1.0),))
        self.assertEqual(heads["time"], (("Time[s]_RawFacilities", 1.0),))
        self.assertEqual(heads["speed"], (("Dyno_Spd__mph", d3_rows.MPH_TO_KPH),))
        self.assertFalse(any("UNVERIFIED" in c.source or "analogy" in c.source for c in d3_rows.ACCORD_CHANNELS.channels))

        def accord(arrays):
            acc = {r: arrays[r] for r in d3_rows.ACCORD_CHANNELS.roles()}
            acc["lam"] = np.full(len(acc["time"]), AFR)
            return d3_rows.segments(d3_rows.make_trace("A", channels=d3_rows.ACCORD_CHANNELS, arrays=acc),
                                    rules=self.R, afr_st=AFR)

        self.assertEqual(len(accord(base_arrays(seconds=20.0))), 1)
        for key, value in (("turbine_rpm", 2000.0 / 1.02), ("ac", 1.0)):
            s = accord(mid(base_arrays(seconds=20.0), key, value, 9.0, 10.0))
            self.assertEqual(len(s), 2, msg=key)
            self.assertTrue(all(x.t1_s < 9.0 or x.t0_s >= 10.0 for x in s), msg=key)

    def test_the_cvt_needs_the_car_to_move(self):
        acc = {r: base_arrays(seconds=20.0)[r] for r in d3_rows.ACCORD_CHANNELS.roles()}
        acc["lam"] = np.full(len(acc["time"]), AFR)
        tr = d3_rows.make_trace("A", channels=d3_rows.ACCORD_CHANNELS, arrays=acc)
        self.assertEqual(len(d3_rows.segments(tr, rules=self.R, afr_st=AFR)), 1)
        acc["speed"] = np.zeros(len(acc["time"]))
        tr = d3_rows.make_trace("A", channels=d3_rows.ACCORD_CHANNELS, arrays=acc)
        self.assertEqual(len(d3_rows.segments(tr, rules=self.R, afr_st=AFR)), 0)


class Demand(Guarded):
    def seg(self, **kw):
        return replace(segs(base_arrays(seconds=5.0))[0], **kw)

    def test_a_stepped_box_against_a_hand_value(self):
        s = self.seg(force_n_mean=1500.0, gear=4)
        # 1500 N x 0.37 m / (1.0 x 4.0) / 0.92 = 150.815... N m, by hand
        self.assertAlmostEqual(d3_rows.demand_torque(s, car=CX9, eta=0.92), 1500.0 * 0.37 / 4.0 / 0.92, places=12)
        self.assertAlmostEqual(d3_rows.demand_torque(s, car=CX9, eta=0.92), 150.81521739130434, places=10)
        # Control: another gear, another eta, another torque.
        self.assertAlmostEqual(d3_rows.demand_torque(replace(s, gear=2), car=CX9, eta=0.92), 1500 * 0.37 / 8.0 / 0.92)
        self.assertNotEqual(d3_rows.demand_torque(s, car=CX9, eta=0.86), d3_rows.demand_torque(s, car=CX9, eta=0.92))
        with self.assertRaises(ValueError):
            d3_rows.demand_torque(replace(s, gear=7), car=CX9, eta=0.92)

    def test_the_cvt_by_engine_and_wheel_speed(self):
        s = self.seg(force_n_mean=1000.0, power_w_mean=1000.0 * 20.0, rpm_mean=2000.0, gear=None)
        t = d3_rows.demand_torque(s, car=CVT, eta=0.92)
        omega = 2000.0 * 2.0 * math.pi / 60.0
        self.assertAlmostEqual(t, 1000.0 * 20.0 / (omega * 0.92), places=10)
        # The same as F r / (i eta) with i the overall ratio omega_e r / v, whatever r is.
        i = omega * CVT.wheel_r / 20.0
        self.assertAlmostEqual(t, 1000.0 * CVT.wheel_r / (i * 0.92), places=10)

    def test_bmep(self):
        # 2 bar on 2.5 L is 2e5 x 2.5e-3 / (4 pi) = 39.789 N m
        self.assertAlmostEqual(d3_rows.bmep_bar(2e5 * 2.5e-3 / (4 * math.pi), displacement_l=2.5), 2.0, places=12)


def srow(test, cell_temp_c, modal_fuel_g, lhv=D3_LHV, *, u=0.0):
    """A summary row as read_summary builds it from one base row, the modal fuel already in grams (u its
    relative u, 0 unless a test sets decision 79's)."""
    return d3_rows.SummaryRow(test=test, cell_temp_c=cell_temp_c, modal_fuel_g=modal_fuel_g, fuel_lhv_btu_per_lbm=lhv,
                              baro_kpa=None, modal_fuel_u_rel=u, base_rows=1, sum_rows=0, cell_temp_spread_c=0.0)


def _summary(traces, scale=1.0, *, u=0.0):
    out = {}
    for tr in traces:
        g, _ = d3_rows._integral(tr.t_s, tr.direct2_gps, 0.0)
        out[tr.test] = srow(tr.test, 25.0, g * scale, u=u)
    return out


def _checks(traces, summary=None, *, u_afr=None, baro=100.0):
    all_segs = [s for tr in traces for s in d3_rows.segments(tr, rules=d3_rows.CONTRACT_SEGMENTS, afr_st=AFR)]
    return d3_rows.channel_checks(traces, summary or _summary(traces), segs=all_segs, afr_st=AFR,
                                  baro_kpa=baro, rules=d3_rows.CHANNEL_RULES, u_afr_st=u_afr), all_segs


class Checks(Guarded):
    def test_direct2_against_the_summary(self):
        a = base_arrays(seconds=20.0, t0=-5.0, direct2=3.0)
        tr = trace(a)
        summ = {"T1": srow("T1", 25.0, 45.0)}                                        # 3 g/s x 15 s
        c, _ = _checks([tr], summ)
        (test, g, modal, ratio, pre, nan_k), = c.direct2_vs_summary
        self.assertAlmostEqual(g, 45.0, places=9)
        self.assertAlmostEqual(pre, 15.0, places=9)                                  # the pre-roll, apart
        self.assertAlmostEqual(c.u_d_fuel, 0.0, places=12)
        # Control: a facility that measured 4 % more moves the fuel's u_D to 4 %.
        summ = {"T1": srow("T1", 25.0, 45.0 * 1.04)}
        c, _ = _checks([tr], summ)
        self.assertAlmostEqual(c.u_d_fuel, 1.0 - 1.0 / 1.04, places=12)

    def test_the_modal_fuels_density_u_enters_the_fuels_u_d(self):
        """Decision 79: the summary's modal fuel, a volume at an ASSUMED density, carries that density's u,
        and the Direct2 check's u_D combines it with Direct2's disagreement, sqrt((r - 1)^2 + u^2). The
        fuel rows record it among their notes, the air rows do not. Controls: the same rows at u 0 give
        |r - 1| alone (the u reached the output, mistake 25); rows carrying two different u are refused."""
        a = base_arrays(seconds=20.0, t0=-5.0, direct2=3.0)
        tr = trace(a)
        u = d3_rows.D3_FUEL_DENSITY.u_rel
        c, _ = _checks([tr], {"T1": srow("T1", 25.0, 45.0, u=u)})
        self.assertAlmostEqual(c.u_modal_fuel, u, places=15)
        self.assertAlmostEqual(c.u_d_fuel, u, places=15)                            # Direct2 agrees: u alone
        self.assertEqual(len(c.assumed_fuel), 1)
        self.assertIn("decision 79", c.assumed_fuel[0])
        self.assertEqual(c.as_json()["u_modal_fuel"], u)
        c4, _ = _checks([tr], {"T1": srow("T1", 25.0, 45.0 * 1.04, u=u)})
        self.assertAlmostEqual(c4.u_d_fuel, math.hypot(1.0 - 1.0 / 1.04, u), places=15)
        # Control: at u 0 the term vanishes and nothing is noted.
        c0, _ = _checks([tr], {"T1": srow("T1", 25.0, 45.0 * 1.04)})
        self.assertAlmostEqual(c0.u_d_fuel, 1.0 - 1.0 / 1.04, places=15)
        self.assertNotEqual(c0.u_d_fuel, c4.u_d_fuel)
        self.assertEqual(c0.assumed_fuel, ())
        # Through the rows: the fuel's u_D carries it, the air's does not.
        rows = d3_rows.c3_rows(Rows().evals(), context=CTX, checks=replace(c4, u_d_air=0.02),
                               evals_half=Rows().evals(half=True))
        self.assertAlmostEqual(rows["C3b"].u.u_D, 100.0 * c4.u_d_fuel, places=12)
        self.assertIn(c4.assumed_fuel[0], rows["C3b"].u.unsourced)
        self.assertNotIn(c4.assumed_fuel[0], rows["C3d"].u.unsourced)
        # Two tests whose rows carry different u: one u_D term cannot carry both.
        t2 = trace(base_arrays(seconds=20.0, direct2=3.1), "T2")
        with self.assertRaises(ValueError):
            _checks([tr, t2], {"T1": srow("T1", 25.0, 45.0, u=u), "T2": srow("T2", 25.0, 62.0, u=2 * u)})
        _checks([tr, t2], {"T1": srow("T1", 25.0, 45.0, u=u), "T2": srow("T2", 25.0, 62.0, u=u)})

    def test_the_maf_against_direct2(self):
        tr = trace(base_arrays(seconds=20.0))
        c, _ = _checks([tr])
        self.assertAlmostEqual(c.maf_ratio_median, 1.0, places=12)
        self.assertEqual(c.maf_ratio_n, 1)
        self.assertAlmostEqual(c.u_d_air, 0.0, places=12)
        # Control: a MAF reading 5 % high, then decision 63's AFR_st term on top of it.
        a = base_arrays(seconds=20.0)
        a["maf"] = a["maf"] * 1.05
        c, _ = _checks([trace(a)])
        self.assertAlmostEqual(c.maf_ratio_median, 1.05, places=12)
        self.assertAlmostEqual(c.u_d_air, 0.05, places=12)
        self.assertTrue(any("not sized" in u for u in c.unsourced))
        c, _ = _checks([trace(a)], u_afr=0.01)
        self.assertAlmostEqual(c.u_d_air, math.hypot(0.05, 0.01), places=12)

    def test_an_open_loop_segment_is_not_in_the_maf_check(self):
        # T2's Direct2 differs from T1's: two tests holding one constant maximum would read as a flat
        # maximum repeated across tests, and be dropped (that rule's own test is below).
        rich = trace(base_arrays(seconds=20.0, lam=0.85, direct2=3.1), "T2")
        c, _ = _checks([trace(base_arrays(seconds=20.0)), rich])
        self.assertEqual(c.maf_ratio_n, 1)
        self.assertEqual(c.lambda_reading["open_loop_n"], 1)

    def test_the_lambda_reading_is_checked(self):
        # MD section 5 reads lambda = 1/channel; CATALOGUE.md:606 calls the channel lambda-like. A
        # synthetic car whose channel IS lambda (0.85 at a rich segment) and whose MAF follows it:
        # the nominal reading puts the open-loop ratio at 0.85^2, the other at 1 (mistake 13).
        a = base_arrays(seconds=20.0, lam=0.85)
        a["lam"] = np.full(len(a["time"]), 0.85)
        c, _ = _checks([trace(a)])
        self.assertAlmostEqual(c.lambda_reading["open_loop_median_nominal"], 0.85 * 0.85, places=12)
        self.assertAlmostEqual(c.lambda_reading["open_loop_median_if_channel"], 1.0, places=12)
        # Control: a car whose channel is 1/lambda, as the contract reads it, gives the opposite.
        c, _ = _checks([trace(base_arrays(seconds=20.0, lam=0.85))])
        self.assertAlmostEqual(c.lambda_reading["open_loop_median_nominal"], 1.0, places=12)

    def _pinned(self, test, top, hold_s):
        a = base_arrays(seconds=20.0)
        a["maf"] = np.where((a["time"] >= 10.0) & (a["time"] < 10.0 + hold_s), top, a["maf"])
        a["direct2"] = np.where((a["time"] >= 10.0) & (a["time"] < 10.0 + hold_s), top / AFR, a["direct2"])
        return trace(a, test)

    def test_a_flat_maximum_repeated_across_tests_is_dropped(self):
        traces = [self._pinned("T1", 99.0, 2.0), self._pinned("T2", 99.0, 2.0), trace(base_arrays(), "T3")]
        c, all_segs = _checks(traces)
        self.assertEqual(c.flat_maxima, {"direct2": 99.0 / AFR, "maf": 99.0})
        hit = [s for s in all_segs if d3_rows.saturated(s, flats=c.flat_maxima)]
        self.assertEqual(c.flat_maxima_dropped, len(hit))
        self.assertGreater(len(hit), 0)
        self.assertTrue(all(s.test in ("T1", "T2") for s in hit))

    def test_one_test_or_a_scan_tool_hold_is_not_a_flat_maximum(self):
        c, _ = _checks([self._pinned("T1", 99.0, 2.0), trace(base_arrays(), "T2")])       # one test only
        self.assertEqual(c.flat_maxima, {})
        c, _ = _checks([self._pinned("T1", 99.0, 0.5), self._pinned("T2", 99.0, 0.5)])    # held 0.5 s
        self.assertEqual(c.flat_maxima, {})
        c, _ = _checks([self._pinned("T1", 99.0, 2.0), self._pinned("T2", 98.0, 2.0)])    # not the same value
        self.assertEqual(c.flat_maxima, {})

    def _idle(self, map_kpa, idle_s):
        a = base_arrays(seconds=20.0)
        idle = a["time"] < idle_s
        a["speed"] = np.where(idle, 0.0, a["speed"])
        a["rpm"] = np.where(idle, 700.0, a["rpm"])
        a["map"] = np.where(idle, map_kpa, a["map"])
        return trace(a)

    def test_the_pcm_map_reads_below_barometric_at_closed_throttle(self):
        c, _ = _checks([self._idle(35.0, 5.0)], baro=99.0)
        self.assertTrue(c.closed_throttle["below_baro"])
        self.assertEqual(c.closed_throttle["n"], 1)
        # Control: a pressure channel before the throttle (mistake 2) reads barometric at idle.
        c, _ = _checks([self._idle(98.5, 5.0)], baro=99.0)
        self.assertFalse(c.closed_throttle["below_baro"])
        # And an idle shorter than idle_min_s is no window (seconds, mistake 8): no verdict, not a pass.
        c, _ = _checks([self._idle(35.0, 2.0)], baro=99.0)
        self.assertEqual(c.closed_throttle["n"], 0)
        self.assertFalse(c.closed_throttle["below_baro"])


def write_xlsx(path, sheet, rows):
    """A minimal workbook: one sheet, strings shared, numbers inline, a title row above the header."""
    strings, idx = [], {}

    def sid(s):
        if s not in idx:
            idx[s] = len(strings)
            strings.append(s)
        return idx[s]

    def col(k):
        s = ""
        k += 1
        while k:
            k, r = divmod(k - 1, 26)
            s = chr(65 + r) + s
        return s

    xr = []
    for i, r in enumerate(rows, start=1):
        cells = []
        for k, v in enumerate(r):
            ref = f"{col(k)}{i}"
            if isinstance(v, str):
                cells.append(f'<c r="{ref}" t="s"><v>{sid(v)}</v></c>')
            elif v is not None:
                cells.append(f'<c r="{ref}"><v>{v!r}</v></c>')
        xr.append(f'<row r="{i}">{"".join(cells)}</row>')
    m = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    r_ = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/workbook.xml", f'<workbook xmlns="{m}" xmlns:r="{r_}"><sheets>'
                   f'<sheet name="Cover" sheetId="1" r:id="rId1"/><sheet name="{sheet}" sheetId="2" r:id="rId2"/>'
                   f'</sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="ws" Target="worksheets/sheet1.xml"/>'
                   '<Relationship Id="rId2" Type="ws" Target="worksheets/sheet2.xml"/></Relationships>')
        z.writestr("xl/worksheets/sheet1.xml", f'<worksheet xmlns="{m}"><sheetData/></worksheet>')
        z.writestr("xl/worksheets/sheet2.xml", f'<worksheet xmlns="{m}"><sheetData>{"".join(xr)}</sheetData></worksheet>')
        z.writestr("xl/sharedStrings.xml", f'<sst xmlns="{m}">' + "".join(
            f"<si><t>{s}</t></si>" for s in strings) + "</sst>")


SPEC = d3_rows.SummarySpec(car="synthetic", sheet="Tests", test_id="Test ID", cycle="Cycle", cell_temp_c="Cell C",
                           modal_fuel="Fuel modal kg", modal_fuel_to_g=1000.0, modal_fuel_u_rel=0.0, fuel_lhv="HV BTU/lb",
                           fuel_lhv_to_btu_per_lbm=1.0, baro=None, baro_to_kpa=None,
                           sources=tuple((k, "synthetic") for k in d3_rows.SUMMARY_NEED))
HEAD = ["Test ID", "Cycle", "Cell C", "Fuel modal kg", "HV BTU/lb"]


def read(rows, tests, spec=SPEC):
    """read_summary on a synthetic workbook holding `rows` under a title row and a blank one."""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "summary.xlsx")
        write_xlsx(p, spec.sheet, [["A synthetic summary"], []] + rows)
        return d3_rows.read_summary(p, spec=spec, tests=tests)


# A test with phases and sum rows, as decision 78's identifier read found the sheets laid out (the labels'
# forms are the CX-9's and the Accord's; every number is made up): the sum rows carry the sum of their phases,
# so a reader that counted them would double the fuel.
UDDS = [[61700001.0, "UDDS #1, Ph 1", 24.0, 0.10, 18300.0],
        [61700001.0, "UDDS #1, Ph 2", 25.0, 0.20, 18300.0],
        [61700001.0, "UDDS #1, Ph 1+2", 24.5, 0.30, 18300.0],
        [61700001.0, "UDDS #2, Ph 3", 25.5, 0.15, 18300.0],
        [61700001.0, "UDDS #2, Ph 4", 26.0, 0.25, 18300.0],
        [61700001.0, "UDDS #2, Ph 3+4", 25.7, 0.40, 18300.0]]
US06 = [[61700002.0, "US06x2 p1", 23.0, 0.5, 18300.0],
        [61700002.0, "US06x2 p2", 23.5, 0.6, 18300.0],
        [61700002.0, "US06x2 p1+2", 23.2, 1.1, 18300.0]]
WOT = [[61700003.0, "WOTs x3", 22.0, 0.05, 18300.0]]


class Summary(Guarded):
    # The strings decision 78's header read printed (24 October 2026; the scratchpad's d3pin/stage2_*.txt):
    # the same five on both sheets, the heating value's with a line break inside the cell.
    HEADERS = {"test_id": "Test ID [#]", "cycle": "Cycle", "cell_temp_c": "Test Cell Temp [C]",
               "modal_fuel": "Fuel used modal [gal]", "fuel_lhv": "Fuel Heating Value\n[BTU/lbm]"}

    def test_the_real_specs_are_pinned_each_from_a_source(self):
        """The twelve open pins of commit C, closed 24 October 2026 (decisions 78 and 79), and decision 80's
        cycle column and decision 79's u beside them: every field read_summary needs is set and carries its
        source, each header's source quotes it, and the guard (unpinned_for) names nothing on any engine.
        Controls (mistake 12): a pin with its source taken away, or the pin itself, is named by the guard,
        and read_summary refuses it before the file is opened."""
        for spec, sheet in ((d3_rows.SUMMARY_CX9, "Extended Test Summary"), (d3_rows.SUMMARY_ACCORD, "G2_TestSummary")):
            self.assertEqual(spec.sheet, sheet)
            self.assertEqual(spec.unpinned(), ())
            for k, h in self.HEADERS.items():
                self.assertEqual(getattr(spec, k), h, msg=(spec.car, k))
                self.assertIn(f"'{h}'".replace("\n", "\\n"), dict(spec.sources)[k], msg=(spec.car, k))
            self.assertEqual(spec.fuel_lhv_to_btu_per_lbm, 1.0)
            self.assertEqual(spec.modal_fuel_to_g, d3_rows.D3_FUEL_DENSITY.g_per_us_gal)
            self.assertEqual(spec.modal_fuel_u_rel, d3_rows.D3_FUEL_DENSITY.u_rel)
            self.assertTrue(all(dict(spec.sources).get(k) for k in d3_rows.SUMMARY_NEED))
            self.assertIn("decision 79", dict(spec.sources)["modal_fuel_to_g"])
            # Controls: a source taken away, a pin taken away.
            for k in ("modal_fuel_to_g", "fuel_lhv", "cycle"):
                bare = replace(spec, sources=tuple(x for x in spec.sources if x[0] != k))
                self.assertEqual(bare.unpinned(), (k,))
                with self.assertRaises(d3_rows.SummaryNotPinned):
                    d3_rows.read_summary(os.path.join(HERE, "__no_such_summary__.xlsx"), spec=bare, tests=("1",))
            self.assertEqual(replace(spec, modal_fuel_to_g=None).unpinned(), ("modal_fuel_to_g",))
        for engine in ("mazda_25t", "honda_l15b7", "ford_27tt"):
            self.assertEqual(d3_rows.unpinned_for(engine), ())
        open_cx9 = dict(d3_rows.SUMMARY_FOR, mazda_25t=replace(d3_rows.SUMMARY_CX9, modal_fuel_to_g=None))
        with mock.patch.object(d3_rows, "SUMMARY_FOR", open_cx9):
            self.assertEqual(d3_rows.unpinned_for("mazda_25t"), ("cx9_2016.modal_fuel_to_g",))
            self.assertEqual(d3_rows.unpinned_for("honda_l15b7"), ())
        # Control of the control: a pinned spec does open the path (which does not exist).
        with self.assertRaises(FileNotFoundError):
            d3_rows.read_summary(os.path.join(HERE, "__no_such_summary__.xlsx"), spec=SPEC, tests=("1",))

    def test_the_real_pins_read_a_synthetic_workbook_in_their_units(self):
        """The real specs end to end on a SYNTHETIC workbook that prints their headers (names only, every value
        made up): gallons become grams at decision 79's assumed density, the heating value is taken as it
        stands, and each row carries the density's u. Control: the heating value's heading without its line
        break is not the pinned header, and the read stops before any value."""
        for spec in (d3_rows.SUMMARY_CX9, d3_rows.SUMMARY_ACCORD):
            head = [spec.test_id, spec.cycle, "Test Time", spec.cell_temp_c, spec.modal_fuel, spec.fuel_lhv]
            rows = [head, [61700001.0, "HWY, Ph 1", "x", 21.0, 0.25, 18000.0],
                    [61700001.0, "HWY, Ph 2", "x", 21.5, 0.5, 18000.0]]
            out = read(rows, ("61700001",), spec=spec)["61700001"]
            self.assertAlmostEqual(out.modal_fuel_g, 0.75 * d3_rows.D3_FUEL_DENSITY.g_per_us_gal, places=9)
            self.assertAlmostEqual(out.modal_fuel_g, 0.75 * 0.745015 * 3785.411784, places=6)   # by hand
            self.assertEqual(out.fuel_lhv_btu_per_lbm, 18000.0)
            self.assertEqual(out.modal_fuel_u_rel, d3_rows.D3_FUEL_DENSITY.u_rel)
            flat = [[h.replace("\n", " ") for h in head]] + rows[1:]
            with self.assertRaises(d3_rows.HeaderDefect):
                read(flat, ("61700001",), spec=spec)

    def test_a_workbook_is_read(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "summary.xlsx")
            write_xlsx(p, "Tests", [["A synthetic summary"], [], HEAD,
                                    [61700001.0, "US06", 24.5, 1.25, 18300.0],
                                    ["61700002", "HWY", 23.0, 0.5, 18300.0], [None, None]])
            out = d3_rows.read_summary(p, spec=SPEC, tests=("61700001", "61700002"))
            self.assertEqual(sorted(out), ["61700001", "61700002"])
            self.assertEqual(out["61700001"].modal_fuel_g, 1250.0)
            self.assertEqual(out["61700002"].cell_temp_c, 23.0)
            # Controls: a header the workbook does not print, and another sheet, stop before any value.
            with self.assertRaises(d3_rows.HeaderDefect):
                d3_rows.read_summary(p, spec=replace(SPEC, fuel_lhv="Heating value"), tests=("61700001",))
            with self.assertRaises(d3_rows.HeaderDefect):
                d3_rows.read_summary(p, spec=replace(SPEC, sheet="Extended Test Summary"), tests=("61700001",))

    def test_the_base_phase_rows_are_summed_and_the_sum_rows_left_out(self):
        """Decision 80 on a test with two UDDS halves, each a sum row after its two phases: the modal fuel is
        the four phases' sum (0.70 kg), the cell temperature the first phase's (24.0 C) with the spread over
        the four reported (2.0 K), and the two sum rows are counted apart. Control: the same rows read with
        the sum rows taken as phases give twice the fuel, so a reader that kept them fails here; and the
        Accord's "p1+2" form is a sum row too."""
        out = read([HEAD] + UDDS + US06, ("61700001", "61700002"))
        r = out["61700001"]
        self.assertAlmostEqual(r.modal_fuel_g, 1000.0 * (0.10 + 0.20 + 0.15 + 0.25), places=9)
        self.assertEqual((r.cell_temp_c, r.cell_temp_spread_c, r.base_rows, r.sum_rows), (24.0, 2.0, 4, 2))
        self.assertEqual(r.as_json(), {"base_rows": 4, "sum_rows_excluded": 2, "cell_temp_c": 24.0,
                                       "cell_temp_spread_c": 2.0})
        r2 = out["61700002"]
        self.assertAlmostEqual(r2.modal_fuel_g, 1100.0, places=9)
        self.assertEqual((r2.cell_temp_c, r2.base_rows, r2.sum_rows), (23.0, 2, 1))
        # Control: every row a phase (the labels' "+" removed) doubles the fuel.
        as_phases = [[t, c.replace("+", " and "), *rest] for t, c, *rest in UDDS]
        self.assertAlmostEqual(read([HEAD] + as_phases, ("61700001",))["61700001"].modal_fuel_g, 1400.0, places=9)
        for label, is_sum in (("UDDS #1, Ph 1+2", True), ("UDDS #2, Ph 3+4", True), ("UDDS cold start p1+2", True),
                              ("US06x2 p3+4", True), ("UDDS hot #2 start p1+2", True), ("Hwyx3, Ph 1", False),
                              ("HWYx2  p1", False), ("US06x3 p1 ", False), ("LA92x2 ph1", False),
                              ("SSS 0-80-0 30 sec 0,3,6% grade - SSS warmup", False), ("WOTs x3", False)):
            self.assertIs(d3_rows.sum_row(label), is_sum, msg=label)

    def test_a_test_with_one_row_is_that_row(self):
        """Decision 80: a test with one row (a WOT run) is that row. Control: a test with sum rows only has
        no base phase row and is refused by name."""
        r = read([HEAD] + WOT, ("61700003",))["61700003"]
        self.assertEqual((r.modal_fuel_g, r.cell_temp_c, r.cell_temp_spread_c, r.base_rows, r.sum_rows),
                         (50.0, 22.0, 0.0, 1, 0))
        with self.assertRaises(d3_rows.TraceDefect) as cm:
            read([HEAD, [61700004.0, "US06x2 p1+2", 23.0, 1.0, 18300.0]], ("61700004",))
        self.assertIn("61700004", str(cm.exception))

    def test_disagreeing_heating_values_are_refused_by_name(self):
        """Decision 80: a test's base rows must share one heating value; one that differs refuses the test by
        name, without printing a value. Control: the same rows with the values equal read."""
        odd = [list(x) for x in US06]
        odd[1][4] = 18301.0
        with self.assertRaises(d3_rows.TraceDefect) as cm:
            read([HEAD] + odd, ("61700002",))
        self.assertIn("61700002", str(cm.exception))
        self.assertIn("disagree", str(cm.exception))
        self.assertNotIn("18301", str(cm.exception))
        self.assertEqual(read([HEAD] + US06, ("61700002",))["61700002"].fuel_lhv_btu_per_lbm, 18300.0)

    def test_headings_and_other_tests_rows_are_never_converted(self):
        """Decision 80's code: a row whose test ID cell is not a whole number (a day's heading, the disclaimer
        at the foot, an empty cell) is skipped, and so is every row of a test the chain does not read, so its
        empty or odd cells never stop the read; a test the sheet does not list is absent. Controls: the same
        odd test asked for stops, naming the test and the column but not the cell; a cycle label that holds
        "+" in another form is refused, never guessed."""
        rows = ([HEAD, ["Day 1 Standard Cycles"]] + UDDS + [["Day 2, Standard Cycles Repeat 1", None, None]]
                + [[61700009.0, "HWY, Ph 1", "n/a?", None, 18300.0]] + WOT
                + [["-This publication is distributed by ..."], [None, None]])
        out = read(rows, ("61700001", "61700003", "61700005"))
        self.assertEqual(sorted(out), ["61700001", "61700003"])
        with self.assertRaises(d3_rows.TraceDefect) as cm:
            read(rows, ("61700009",))
        self.assertIn("61700009", str(cm.exception))
        self.assertIn("Cell C", str(cm.exception))
        self.assertNotIn("n/a?", str(cm.exception))
        with self.assertRaises(d3_rows.TraceDefect):
            read([HEAD, [61700006.0, "UDDS + HWY", 23.0, 1.0, 18300.0]], ("61700006",))
        with self.assertRaises(ValueError):
            d3_rows.sum_row("UDDS + HWY")
        with self.assertRaises(ValueError):
            read([HEAD] + WOT, ())

    def test_the_assumed_density(self):
        """Decision 79: the six NVFEL densities (three Tier 2, three Tier 3), their union 0.74227-0.74776 kg/L,
        the assumed density its midpoint 0.745015 kg/L, the half-width 0.002745 kg/L, its uniform u 0.2127 %
        of the midpoint, and 2820.19 g per US gallon, each by hand. Controls: the rule on two made-up fuels;
        the band moves when its widest fuel is left out; no fuel is refused."""
        f = d3_rows.D3_FUEL_DENSITIES
        self.assertEqual(sorted(x.ftag for x in f), ["25206", "25278", "25402", "25842", "26781", "26864"])
        self.assertEqual(sorted(x.grade for x in f), ["Tier 2"] * 3 + ["Tier 3"] * 3)
        self.assertTrue(all(x.source for x in f))
        d = d3_rows.D3_FUEL_DENSITY
        self.assertAlmostEqual(d.kg_per_l, 0.745015, places=12)
        self.assertAlmostEqual(d.half_width_kg_per_l, 0.002745, places=12)
        self.assertAlmostEqual(d.u_rel, 0.002745 / math.sqrt(3.0) / 0.745015, places=15)
        self.assertEqual(round(100 * d.u_rel, 4), 0.2127)
        self.assertAlmostEqual(d.g_per_us_gal, 0.745015 * 3785.411784, places=9)
        self.assertEqual(round(d.g_per_us_gal, 2), 2820.19)
        self.assertAlmostEqual(d3_rows.L_PER_US_GAL, 231 * 2.54 ** 3 / 1000, places=12)
        two = d3_rows.assumed_density((replace(f[0], kg_per_l=0.70), replace(f[1], kg_per_l=0.80)))
        self.assertAlmostEqual(two.kg_per_l, 0.75, places=15)
        self.assertAlmostEqual(two.u_rel, 0.05 / math.sqrt(3.0) / 0.75, places=15)
        narrower = d3_rows.assumed_density(tuple(x for x in f if x.ftag != "25206"))
        self.assertAlmostEqual(narrower.kg_per_l, (0.74227 + 0.74506) / 2, places=12)
        self.assertLess(narrower.u_rel, d.u_rel)
        with self.assertRaises(ValueError):
            d3_rows.assumed_density(())


class Contract(Guarded):
    # The contract's wording of the rules, as results/ENGINE_THRESHOLDS.md section 5 and JSON c3_segments
    # write it (copied as text here: this file never opens the contract).
    WORDING = ("C3 segments: at least 3 s; engine speed within +-25 rpm; the PCM MAP channel refreshed at "
               "least twice; the torque converter locked throughout (Eng_speed_CAN within 1 % of "
               "Trans_turbine_shaft_speed_TCM); the A/C compressor off throughout (HVAC_ACComp_cycling_switch_PCM); "
               "one gear (Trans_gear_actual_CAN); coolant at or above the map's lowest (83.8 C); padding rows dropped")

    def test_the_rules_are_the_contracts(self):
        self.assertEqual(d3_rows.check_rules_against_contract(d3_rows.CONTRACT_SEGMENTS, self.WORDING), ())
        # Control: a drifted copy of a rule is caught.
        bad = replace(d3_rows.CONTRACT_SEGMENTS, coolant_min_c=84.0)
        self.assertEqual(len(d3_rows.check_rules_against_contract(bad, self.WORDING)), 1)
        bad = replace(d3_rows.CONTRACT_SEGMENTS, rpm_band=30.0)
        self.assertEqual(len(d3_rows.check_rules_against_contract(bad, self.WORDING)), 1)

    def test_u_input_is_five_point_two_five_percent(self):
        # MD section 5: eta 0.86-0.98 around 0.92, uniform, 3.77 % on the torque; the radius gap 1.6 %,
        # uniform, 0.92 %; together 3.88 %, x 1.353 = 5.25 % on the fuel and the air.
        u = d3_rows.u_input_c3(eta_lo=0.86, eta_hi=0.98, eta=0.92, radius_gap=0.016, flow_per_pct_torque=1.353)
        self.assertEqual(round(100 * u, 2), 5.25)
        self.assertAlmostEqual(0.06 / 0.92 / math.sqrt(3), 0.0377, places=4)
        # Control: the term moves with its inputs.
        self.assertNotEqual(round(100 * d3_rows.u_input_c3(eta_lo=0.80, eta_hi=0.98, eta=0.92, radius_gap=0.016,
                                                           flow_per_pct_torque=1.353), 2), 5.25)

    def test_the_gear_codes_are_the_cars(self):
        # CHANNELS' six codes against the CX-9's published ratios (engine_specs/cars, not a D3 file).
        import tomllib
        with open(os.path.join(HERE, "engine_specs", "cars", "cx9_2016_25t.toml"), "rb") as fh:
            ratios = tomllib.load(fh)["gear_ratios"]["value"]
        self.assertEqual(d3_rows.CHANNELS.gear_codes, tuple(range(1, len(ratios) + 1)))
        self.assertEqual(d3_rows.check_channels_against_car(d3_rows.CHANNELS, CX9), ())
        self.assertEqual(d3_rows.check_channels_against_car(d3_rows.ACCORD_CHANNELS, CVT), ())
        # Controls: a five-speed record, a CVT under the CX-9's channels, and the reverse, each refused.
        five = types.SimpleNamespace(id="five", wheel_r=0.37, final_drive=4.0, gears=CX9.gears[:5])
        self.assertEqual(len(d3_rows.check_channels_against_car(d3_rows.CHANNELS, five)), 1)
        self.assertEqual(len(d3_rows.check_channels_against_car(d3_rows.CHANNELS, CVT)), 1)
        self.assertEqual(len(d3_rows.check_channels_against_car(d3_rows.ACCORD_CHANNELS, CX9)), 1)

    def test_row_10s_efficiencies_from_the_band(self):
        e6 = [{"n": 9, "band": "x"}, {"n": 10, "band": "0.86-0.98 (the CX-9's apparent efficiency on D3, seen)"}]
        self.assertEqual(d3_rows.row10_etas(e6), (0.86, 0.98))


class Chain(Guarded):
    def test_the_inversion_by_hand(self):
        # torque = 2 (MAP - 30): 150 N m at exactly 105 kPa.
        p, br, bound, n = d3_rows.invert_map(lambda m: 2.0 * (m - 30.0), 150.0)
        self.assertTrue(br)
        self.assertIsNone(bound)
        self.assertLess(abs(p - 105.0), d3_rows.MAP_TOL_KPA)
        # A target on a scan point is that point.
        self.assertEqual(d3_rows.invert_map(lambda m: 2.0 * (m - 30.0), 2.0 * (110.0 - 30.0))[0], 110.0)
        # Unreachable: the nearer bound, flagged.
        self.assertEqual(d3_rows.invert_map(lambda m: 2.0 * (m - 30.0), 5000.0)[:3], (400.0, False, 400.0))
        self.assertEqual(d3_rows.invert_map(lambda m: 2.0 * (m - 30.0), -100.0)[:3], (20.0, False, 20.0))
        # The FIRST bracket from 20 kPa up, of two (a torque that rises, falls and rises).
        f = lambda m: 100.0 - abs(m - 200.0) if m < 300 else m - 200.0   # noqa: E731
        self.assertLess(abs(d3_rows.invert_map(f, 50.0)[0] - 150.0), d3_rows.MAP_TOL_KPA)

    def test_the_search_is_d1s(self):
        # One definition (mistake 10): the scan and the tolerance are epa_stats', and on a torque curve that
        # does not depend on spark (spark_slope 0) invert_map lands where epa_stats.d1_invert lands, bit for
        # bit, bracketed, on a scan point, beyond either end, and on a curve with two crossings.
        self.assertEqual(d3_rows.MAP_SCAN_KPA, epa_stats.D1_SCAN_KPA)
        self.assertEqual(d3_rows.MAP_TOL_KPA, epa_stats.D1_BISECT_KPA)
        x = epa_stats.RowInputs(engine="toy", table="t", source_row=0, rpm=2500.0, map_kpa=100.0, iat_k=320.0,
                                ect_k=363.15, spark_btdc=10.0, lam=1.0, lam_source="published",
                                spark_source="published", fuel=None)

        class Curve(ToyModel):
            def __init__(self, f):
                super().__init__()
                self.f = f

            def cycle(self, x, *, dtheta):
                return replace(super().cycle(x, dtheta=dtheta), torque_nm=self.f(x.map_kpa))

        curves = (lambda m: 2.0 * (m - 30.0), lambda m: 300.0 * math.tanh((m - 25.0) / 120.0),
                  lambda m: 100.0 - abs(m - 200.0) if m < 300 else m - 200.0)
        for f in curves:
            model = Curve(f)
            for target in (150.0, 160.0, 50.0, -500.0, 5000.0, 2.0 * (110.0 - 30.0)):
                mine = d3_rows.invert_map(lambda m: model.cycle(replace(x, map_kpa=m), dtheta=0.25).torque_nm, target)
                d1 = epa_stats.d1_invert(x, target, model=model, dtheta=0.25, spark_slope=0.0)
                self.assertEqual((mine[0], mine[1], mine[2]), (d1.map_kpa, d1.bracketed, d1.bound_kpa), msg=target)

    def test_the_ecu_dwell_runs_on_the_cars_own_pcm_map(self):
        model = ToyModel()
        a = base_arrays(seconds=20.0, map_kpa=160.0)          # the car above the toy's 150 kPa gate
        e = d3_rows.ecu_along(trace(a), model=model, t_cell_k=298.15, ect_k_if_absent=None)
        t = a["time"]
        self.assertAlmostEqual(model.dt_seen, 0.1, places=12)               # the trace's own step
        self.assertEqual(e.nonuniform_steps, 0)
        self.assertTrue(np.all(e.lam[t < 3.85] == 1.0))
        self.assertTrue(np.all(e.lam[t > 4.05] == 0.85))
        # Control: the same trace with the car's MAP below the gate never enriches.
        b = base_arrays(seconds=20.0, map_kpa=100.0)
        self.assertTrue(np.all(d3_rows.ecu_along(trace(b), model=model, t_cell_k=298.15,
                                                 ect_k_if_absent=None).lam == 1.0))
        # The charge is the model's at the cell's temperature, the block taken as the coolant.
        self.assertAlmostEqual(float(e.iat_k[0]), 298.15 + 12.0 + 0.06 * (363.15 - 298.15), places=9)

    def test_one_segment_end_to_end(self):
        model = ToyModel()
        a = base_arrays(seconds=20.0, map_kpa=60.0, force=1500.0)
        tr = trace(a)
        s = d3_rows.segments(tr, rules=d3_rows.CONTRACT_SEGMENTS, afr_st=AFR)[0]
        e = d3_rows.ecu_along(tr, model=model, t_cell_k=298.15, ect_k_if_absent=None)
        task = d3_rows.c3_task(s, car=CX9, eta=0.92, engine_name="toy", table="t", fuel=None, ecu=e,
                               t_cell_k=298.15, ect_k_if_absent=None, d3_lhv_btu_per_lbm=D3_LHV)
        ev = d3_rows.c3_evaluate(task, model=model, dtheta=0.25)
        want_t = 1500.0 * 0.37 / 4.0 / 0.92
        want_map = want_t / 2.0 + 30.0
        self.assertLess(abs(ev.map_kpa - want_map), d3_rows.MAP_TOL_KPA)
        self.assertAlmostEqual(ev.model_fuel_gps, 0.05 * ev.map_kpa * (1 + 0.00025), places=12)
        self.assertAlmostEqual(ev.spark_btdc, 20.0 - 0.1 * ev.map_kpa, places=12)
        self.assertEqual(ev.lam, 1.0)
        self.assertTrue(ev.bracketed)
        # Control: another efficiency moves the demand and so the MAP.
        ev2 = d3_rows.c3_evaluate(replace(task, eta=0.86, demand_nm=d3_rows.demand_torque(s, car=CX9, eta=0.86)),
                                  model=model, dtheta=0.25)
        self.assertGreater(ev2.map_kpa, ev.map_kpa)


def _ev(i, *, fuel_err=0.0, air_err=0.0, pcm_map=120.0, demand=200.0, iat_c=45.0, bracketed=True,
        maxes=(1.0, 1.0), test="T1", d3_lhv=D3_LHV):
    """A synthetic C3Eval whose model fuel, after the heating-value scaling, is (1 + fuel_err) x Direct2."""
    direct2, maf = 10.0, 145.0
    return d3_rows.C3Eval(
        test=test, i0=i, eta=0.92, demand_nm=demand, rpm=2500.0, ect_k=363.15, iat_k=iat_c + 273.15, lam=1.0,
        map_kpa=150.0, bracketed=bracketed, bound_kpa=None if bracketed else 400.0, spark_btdc=5.0, n_cycles=50,
        model_torque_nm=demand, model_fuel_gps=direct2 * (1.0 + fuel_err) * d3_lhv / EPA_LHV,
        model_air_gps=maf * (1.0 + air_err), d3_lhv_btu_per_lbm=d3_lhv, direct2_gps=direct2, maf_gps=maf,
        pcm_map_kpa=pcm_map, direct2_max=maxes[0], maf_max=maxes[1])


CTX = d3_rows.C3Context(engine="toy", R={"C3a": None, "C3b": 16.6, "C3c": None, "C3d": 16.6},
                        hot_map_floor_kpa=110.0, fired_bmep_bar=2.0, displacement_l=2.5, charge_range_c=(37.0, 55.0),
                        min_segments=3, u_input=0.0525, epa_lhv_btu_per_lbm=EPA_LHV, descriptive_only=False)


def _fake_checks(u_d_fuel=0.01, u_d_air=0.02, flats=None):
    return d3_rows.ChannelChecks(direct2_vs_summary=(), u_d_fuel=u_d_fuel, u_modal_fuel=0.0,
                                 maf_ratio_median=1.0 + u_d_air, maf_ratio_n=5, u_afr_st=None, u_d_air=u_d_air,
                                 lambda_reading={}, flat_maxima=flats or {}, flat_maxima_dropped=0, closed_throttle={},
                                 unsourced=(), assumed_fuel=())


class Rows(Guarded):
    ERRS = (0.02, -0.03, 0.05, 0.01, -0.04)

    def evals(self, half=False, **kw):
        bump = 0.001 if half else 0.0
        return [_ev(i, fuel_err=e + bump * (i % 2), air_err=-e, **kw) for i, e in enumerate(self.ERRS)]

    def test_the_context_takes_r_from_the_view_and_refuses_a_fall_through(self):
        view = types.SimpleNamespace(R={"C3a": (None, "%"), "C3b": (16.6, "%"), "C3c": (None, "%"),
                                        "C3d": (16.6, "%"), "E2a": (4.0, "%")}, hot_map_floor_kpa=110.0)
        kw = dict(engine_name="toy", displacement_l=2.5, charge_range_c=(37.0, 55.0), fired_bmep_bar=2.0,
                  min_segments=3, u_input=0.0525, epa_lhv_btu_per_lbm=EPA_LHV)
        ctx = d3_rows.c3_context(view=view, descriptive_only=False, **kw)
        self.assertEqual(ctx.R, {"C3a": None, "C3b": 16.6, "C3c": None, "C3d": 16.6})
        self.assertEqual(ctx.hot_map_floor_kpa, 110.0)
        # Controls (mistake 19): a view without C3d's R, or with C3b's in another unit, is refused for C3,
        # never read as a descriptive row; C4's descriptive chain needs no R.
        short = types.SimpleNamespace(R={k: v for k, v in view.R.items() if k != "C3d"}, hot_map_floor_kpa=110.0)
        with self.assertRaises(ValueError):
            d3_rows.c3_context(view=short, descriptive_only=False, **kw)
        kelvin = types.SimpleNamespace(R=dict(view.R, C3b=(16.6, "K")), hot_map_floor_kpa=110.0)
        with self.assertRaises(ValueError):
            d3_rows.c3_context(view=kelvin, descriptive_only=False, **kw)
        honda = types.SimpleNamespace(R={"E2a": (4.0, "%")}, hot_map_floor_kpa=110.0)
        self.assertEqual(d3_rows.c3_context(view=honda, descriptive_only=True, **kw).R,
                         {"C3a": None, "C3b": None, "C3c": None, "C3d": None})

    def test_the_populations(self):
        p = d3_rows.populations(_ev(0, pcm_map=109.9, demand=30.0, iat_c=36.9), ctx=CTX, flats={})
        self.assertEqual((p["hot"], p["fired"], p["covered"]), (False, False, False))
        p = d3_rows.populations(_ev(0, pcm_map=110.0, demand=2e5 * 2.5e-3 / (4 * math.pi) * 1.000001, iat_c=37.5),
                                ctx=CTX, flats={})
        self.assertEqual((p["hot"], p["fired"], p["covered"]), (True, True, True))
        p = d3_rows.populations(_ev(0, maxes=(5.0, 1.0)), ctx=CTX, flats={"direct2": 5.0})
        self.assertEqual((p["fuel_ok"], p["air_ok"]), (False, True))

    def test_c3_rows_and_their_labels_through_epa_stats(self):
        rows = d3_rows.c3_rows(self.evals(), context=CTX, checks=_fake_checks(), evals_half=self.evals(half=True))
        b = rows["C3b"]
        self.assertAlmostEqual(b.E, 100.0 * np.mean(np.abs(self.ERRS)), places=10)
        self.assertAlmostEqual(rows["C3a"].E, 100.0 * np.mean(self.ERRS), places=10)
        self.assertAlmostEqual(rows["C3c"].E, -100.0 * np.mean(self.ERRS), places=10)
        self.assertEqual((b.kind, rows["C3a"].kind), ("d", "descriptive"))
        self.assertIsNone(rows["C3a"].label)
        self.assertIsNone(rows["C3c"].label)
        # The label is epa_stats', from the u-terms epa_stats combined (one definition, mistake 10).
        u = b.u
        self.assertAlmostEqual(u.u_input, 5.25, places=12)
        self.assertAlmostEqual(u.u_D, 1.0, places=12)
        self.assertAlmostEqual(u.u_stat, float(epa_stats.u_stat_line([100 * abs(e) for e in self.ERRS])), places=12)
        lab, cert = epa_stats.line_label(b.E, u.u_val, u.u_stat, 16.6)
        self.assertEqual(b.lines[0].label, lab)
        self.assertEqual(b.label, epa_stats.row_label(b.lines))
        self.assertEqual(b.kappa, float(epa_stats.kappa(b.E, u.u_val, 16.6, b.label)))
        # Control: errors far beyond R read off.
        big = [_ev(i, fuel_err=0.6 + 0.01 * i) for i in range(5)]
        bigh = [_ev(i, fuel_err=0.6 + 0.01 * i + 0.0001) for i in range(5)]
        self.assertEqual(d3_rows.c3_rows(big, context=CTX, checks=_fake_checks(), evals_half=bigh)["C3b"].label, "off")

    def test_fewer_than_three_segments_is_no_statistic(self):
        rows = d3_rows.c3_rows(self.evals()[:2], context=CTX, checks=_fake_checks(), evals_half=self.evals(half=True)[:2])
        self.assertTrue(rows["C3b"].no_statistic)
        self.assertIsNone(rows["C3b"].label)
        rows = d3_rows.c3_rows(self.evals()[:3], context=CTX, checks=_fake_checks(), evals_half=self.evals(half=True)[:3])
        self.assertFalse(rows["C3b"].no_statistic)

    def test_the_fuel_is_scaled_and_the_uncovered_reported_apart(self):
        ev = self.evals() + [_ev(9, fuel_err=0.5, iat_c=60.0)]           # charge outside the range
        rows = d3_rows.c3_rows(ev, context=CTX, checks=_fake_checks(), evals_half=None)
        self.assertAlmostEqual(rows["C3b"].E, 100.0 * np.mean(np.abs(self.ERRS)), places=10)
        self.assertEqual(rows["C3b"].extra["outside_charge_range"]["n"], 1)
        self.assertIsNone(rows["C3b"].label)                              # no u_num without evals_half
        # Control: without the heating-value scaling the error is the scaling's.
        unscaled = replace(CTX, epa_lhv_btu_per_lbm=D3_LHV)
        e0 = d3_rows.c3_rows([_ev(i) for i in range(3)], context=unscaled, checks=_fake_checks(), evals_half=None)
        self.assertAlmostEqual(e0["C3a"].E, 100.0 * (D3_LHV / EPA_LHV - 1.0), places=10)
        # The scaling is reported as 7.9's float when one heating value is met; with two, one factor each,
        # and each segment was scaled by its own test's (the premise's failure shown, not a crash).
        self.assertEqual(d3_rows.fuel_scaling([_ev(0), _ev(1)], context=CTX), EPA_LHV / D3_LHV)
        two = d3_rows.fuel_scaling([_ev(0), _ev(1, d3_lhv=18400.0)], context=CTX)
        self.assertEqual(two, {repr(D3_LHV): EPA_LHV / D3_LHV, repr(18400.0): EPA_LHV / 18400.0})
        e2 = d3_rows.c3_rows([_ev(i, d3_lhv=18400.0 if i == 1 else D3_LHV) for i in range(3)], context=CTX,
                             checks=_fake_checks(), evals_half=None)
        self.assertAlmostEqual(e2["C3a"].E, 0.0, places=10)
        self.assertIsNone(d3_rows.fuel_scaling([], context=CTX))

    def test_unreachable_and_flat_maxima(self):
        ev = self.evals()
        ev[0] = replace(ev[0], bracketed=False, bound_kpa=400.0)
        rows = d3_rows.c3_rows(ev, context=CTX, checks=_fake_checks(), evals_half=None)
        self.assertEqual(rows["C3b"].extra["unreachable"], [["T1", 0]])
        self.assertAlmostEqual(rows["C3b"].without["unreachable"], 100.0 * np.mean(np.abs(self.ERRS[1:])), places=10)
        ev = [replace(e, maf_max=7.0) if e.i0 == 1 else e for e in self.evals()]
        rows = d3_rows.c3_rows(ev, context=CTX, checks=_fake_checks(flats={"maf": 7.0}), evals_half=None)
        self.assertEqual(rows["C3d"].n_rows, 4)
        self.assertEqual(rows["C3b"].n_rows, 5)

    def test_c4_is_descriptive_only(self):
        with self.assertRaises(ValueError):
            d3_rows.c4_accord(self.evals(), context=CTX, checks=_fake_checks(), evals_half=None)
        rows = d3_rows.c4_accord(self.evals(), context=replace(CTX, descriptive_only=True), checks=_fake_checks(),
                                 evals_half=self.evals(half=True))
        self.assertTrue(all(r.kind == "descriptive" and r.label is None for r in rows.values()))

    def test_e6_row_10(self):
        base = d3_rows.c3_rows(self.evals(), context=CTX, checks=_fake_checks(), evals_half=None)
        moved = {0.86: [replace(e, model_fuel_gps=e.model_fuel_gps * 1.07) for e in self.evals()],
                 0.98: self.evals()}
        out = d3_rows.eta_rows(moved, context=CTX, checks=_fake_checks(), base=base)
        self.assertEqual(out["0.98"], {"C3b": 0.0, "C3d": 0.0})
        self.assertGreater(out["0.86"]["C3b"], 0.0)


import engine_env                                     # noqa: E402
import engines                                        # noqa: E402
import epa_fit                                        # noqa: E402
import epa_rows                                       # noqa: E402
import plant                                          # noqa: E402


class RealModel(Guarded):
    """The chain through the model the held-out run passes in, epa_fit.RowModel, on the B58 (the one
    calibrated plant), at SYNTHETIC inputs: no EPA row, no D3 file. It shows the protocol d3_rows calls
    is the one RowModel provides (mistake 25: check the input reached the output)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()                              # the guard covers building the plant too
        cls.plant = engines.get("b58")
        f = cls.plant.engine.fuel
        cls.tf = epa_rows.TableFuel(ftag="synthetic", fuel_report="synthetic", lhv_j_per_kg=f.lhv_j_per_kg,
                                    afr_st=f.afr_st)
        cls.model = epa_fit.RowModel(cls.plant, fuels={"t": cls.tf})

    def test_the_dwell_timer_is_the_baseline_ecus(self):
        cal = self.plant.engine.ecu
        a = base_arrays(seconds=30.0, rpm=cal.enr_rpm_hi, map_kpa=cal.enr_load + 20.0)
        tr = trace(a)
        e = d3_rows.ecu_along(tr, model=self.model, t_cell_k=298.15, ect_k_if_absent=None)
        # The step is the trace's own 0.1 s, checked against the typed value first: a hand run that only
        # took e.dt_s back would follow a wrong step into the reference (mistake 12; the mutation check
        # of 23 October found that gap).
        self.assertAlmostEqual(e.dt_s, 0.1, places=12)
        ecu = engine_env.BaselineECU(cal)
        hand = [ecu.step(float(r), float(m), float(i), float(c) + 273.15, False, e.dt_s)[1]
                for r, m, i, c in zip(tr.rpm, tr.map_kpa, e.iat_k, tr.coolant_c)]
        self.assertEqual(list(e.lam), hand)
        self.assertLess(float(e.lam.min()), 1.0)
        self.assertEqual(float(e.iat_k[0]), plant.charge_temperature(298.15, 363.15, engine=self.plant.engine))
        # Control: the car's MAP under the gate never enriches.
        b = base_arrays(seconds=30.0, rpm=cal.enr_rpm_hi, map_kpa=cal.enr_load - 20.0)
        self.assertTrue(np.all(d3_rows.ecu_along(trace(b), model=self.model, t_cell_k=298.15,
                                                 ect_k_if_absent=None).lam == 1.0))

    def test_a_segment_end_to_end(self):
        a = base_arrays(seconds=10.0, rpm=2500.0, force=1500.0)
        tr = trace(a)
        s = d3_rows.segments(tr, rules=d3_rows.CONTRACT_SEGMENTS, afr_st=self.tf.afr_st)[0]
        e = d3_rows.ecu_along(tr, model=self.model, t_cell_k=298.15, ect_k_if_absent=None)
        kw = dict(car=CX9, engine_name="b58", table="t", fuel=self.tf, ecu=e, t_cell_k=298.15,
                  ect_k_if_absent=None, d3_lhv_btu_per_lbm=D3_LHV)
        task = d3_rows.c3_task(s, eta=0.92, **kw)
        ev = d3_rows.c3_evaluate(task, model=self.model, dtheta=plant.DTHETA_DEG)
        self.assertTrue(ev.bracketed)
        self.assertLess(abs(ev.model_torque_nm - task.demand_nm), 0.05)
        self.assertEqual(ev.spark_btdc, self.model.ecu_at(ev.rpm, ev.map_kpa, ev.iat_k, ev.ect_k).spark_btdc)
        self.assertAlmostEqual(ev.model_air_gps / ev.model_fuel_gps, self.tf.afr_st * ev.lam, places=9)
        # Control: a lower efficiency asks more torque, so a higher MAP.
        ev2 = d3_rows.c3_evaluate(d3_rows.c3_task(s, eta=0.86, **kw), model=self.model, dtheta=plant.DTHETA_DEG)
        self.assertGreater(ev2.map_kpa, ev.map_kpa)


class WholeChain(Guarded):
    """run_chain, validate_epa's one call, from synthetic files to the body of c3.json (WP3_INTERFACES.md
    7.9), through epa_fit.ordered_map at one job."""

    def test_files_to_a_json_body(self):
        import functools
        import json
        with tempfile.TemporaryDirectory() as d:
            files, summ = [], {}
            for k, d2 in enumerate((3.0, 3.1, 3.2, 3.3)):
                a = base_arrays(seconds=12.0, map_kpa=115.0 + 5 * k, direct2=d2, force=1500.0 + 300.0 * k)
                t = f"6170000{k}"
                p = os.path.join(d, f"{t} Test Data.txt")
                write_d3(p, d3_rows.CHANNELS, a)
                files.append((t, p))
                g, _ = d3_rows._integral(a["time"], a["direct2"], 0.0)
                summ[t] = srow(t, 25.0, g)
            body = d3_rows.run_chain(
                tuple(files), summary=summ, channels=d3_rows.CHANNELS, car=CX9, model=ToyModel(), context=CTX,
                rules=d3_rows.CONTRACT_SEGMENTS, channel_rules=d3_rows.CHANNEL_RULES, dtheta=0.25, eta=0.92,
                etas_row10=(0.86, 0.98), afr_st=AFR, baro_kpa=99.0, u_afr_st=None, engine_name="toy", table="t",
                fuel=None, ect_k_if_absent=None,
                mapper=functools.partial(epa_fit.ordered_map, jobs=1, initializer=None))
        json.dumps(body, allow_nan=False)
        for k in ("files", "segments", "channel_checks", "fuel_scaling", "rows", "eta"):   # 7.9's keys
            self.assertIn(k, body)
        self.assertEqual(body["files"], 4)
        self.assertEqual(body["segments"]["n"], 4)
        self.assertEqual(sorted(body["rows"]), ["C3a", "C3b", "C3c", "C3d"])
        self.assertEqual(sorted(body["eta"]), ["0.86", "0.98"])
        for k in ("direct2_vs_summary", "maf_vs_direct2", "pcm_map_closed_throttle", "flat_maxima_dropped",
                  "u_modal_fuel"):
            self.assertIn(k, body["channel_checks"])
        self.assertEqual(body["summary_rows"]["61700000"], {"base_rows": 1, "sum_rows_excluded": 0, "cell_temp_c": 25.0,
                                                            "cell_temp_spread_c": 0.0})
        self.assertEqual(body["fuel_scaling"], EPA_LHV / D3_LHV)
        self.assertEqual(body["rows"]["C3b"]["n_rows"], 4)
        self.assertIsNotNone(body["rows"]["C3b"]["label"])                 # labelled: u_num from half dtheta
        # Control: a missing summary row stops before any model call.
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.txt")
            write_d3(p, d3_rows.CHANNELS, base_arrays(seconds=5.0))
            m = ToyModel()
            with self.assertRaises(d3_rows.TraceDefect):
                d3_rows.run_chain((("61709999", p),), summary={}, channels=d3_rows.CHANNELS, car=CX9, model=m,
                                  context=CTX, rules=d3_rows.CONTRACT_SEGMENTS, channel_rules=d3_rows.CHANNEL_RULES,
                                  dtheta=0.25, eta=0.92, etas_row10=(0.86, 0.98), afr_st=AFR, baro_kpa=99.0,
                                  u_afr_st=None, engine_name="toy", table="t", fuel=None, ect_k_if_absent=None,
                                  mapper=lambda fn, items: [fn(i) for i in items])
            self.assertEqual(m.calls, 0)
        # Control: channels that disagree with the car record stop before any file is read (the path
        # does not exist, so a read would raise FileNotFoundError instead).
        with self.assertRaises(ValueError):
            d3_rows.run_chain((("61709999", os.path.join(HERE, "__no_such_trace__.txt")),), summary={},
                              channels=d3_rows.CHANNELS, car=CVT, model=ToyModel(), context=CTX,
                              rules=d3_rows.CONTRACT_SEGMENTS, channel_rules=d3_rows.CHANNEL_RULES, dtheta=0.25,
                              eta=0.92, etas_row10=(0.86, 0.98), afr_st=AFR, baro_kpa=99.0, u_afr_st=None,
                              engine_name="toy", table="t", fuel=None, ect_k_if_absent=None,
                              mapper=lambda fn, items: [fn(i) for i in items])


class Imports(Guarded):
    PLANT = {"plant", "thermal", "engines", "engine_env", "derived", "fingerprint", "evaluate", "epa_rows",
             "epa_map", "test_epa_map", "validate_epa", "calibrate_epa", "epa_fit"}

    @staticmethod
    def imported(src):
        out = set()
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.Import):
                out |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                out.add(node.module.split(".")[0])
        return out

    @staticmethod
    def prints(src):
        return [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name) and n.func.id == "print"]

    def test_d3_rows_imports_no_plant_module_and_prints_nothing(self):
        with open(os.path.join(HERE, "d3_rows.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(self.imported(src) & (self.PLANT | {"thresholds"}), set())
        self.assertEqual(self.imported(src) - {"csv", "dataclasses", "math", "os", "re", "xml", "zipfile", "typing",
                                               "numpy", "collections", "functools", "epa_stats"}, set())
        self.assertEqual(self.prints(src), [])
        for part in (("epa_", "steady"), ("epa_", "highload")):            # built from parts (amendment C3)
            self.assertNotIn("".join(part), src)
        # Controls: the same scans flag a scratch source that breaks them.
        self.assertEqual(self.imported("import plant\nfrom engines import get\n") & self.PLANT, {"plant", "engines"})
        self.assertEqual(len(self.prints("print(1.5)\n")), 1)


if __name__ == "__main__":
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    unittest.main(verbosity=2)

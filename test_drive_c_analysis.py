"""test_drive_c_analysis.py -- drive_c_analysis.py holds to results/DRIVE_C_RULE.md, on synthetic logs.

    python test_drive_c_analysis.py        # about a minute

Written 19 October 2026 with drive_c_analysis.py, before the repeat drive, and extended the
same day with a regression test for every finding of its three reviews (fidelity,
blindness and robustness, statistics). No drive C log exists in this repository and none
is read here, and no ignition retard is computed on any real log: every log below is
SYNTHETIC, written to a temporary directory in BimmerLink's form (a Time column, one
channel polled per row in column order, the others forward-filled, 0 until a channel's
first poll). Each scenario puts its steps, retards and segments on the poll grid, so the
right answer is known before the script runs. The one real file touched is
results/car_spark_boost.json, for the legacy dry run the rule asks for (car spark minus
model spark, already published).

  Blind         stage A never asks read_csv for an ignition column; stage B converts
                ignition cells inside the pre-windows only, and never one in a response
                window; two logs that differ only inside the response windows freeze alike
  Overlap       IC36: a press from a held step, a long-held step, the plan's minute
                between presses (anchor (a) in the next pre-window); stage B refuses an
                overlap that reaches it; a time reset never widens a pre-window
  Genuine       D1: every poll found (repeats included), placeholders, blanks and
                out-of-range values dropped, a scrambled logger flagged
  Detector      item 1 on clean, wobbly and late-trigger steps; no step without a
                trigger or a confirmation
  Validity      each of V1-V8 rejects the step built to fail it, V8 both ways, a pinned
                air reading counts as high
  Shams         anchor (b) keeps clear of a step in another run; a blank first time
  Pairing       D2 can miss a pull, never create one, whichever way the target moves,
                and a lost target poll drops the pair (IC37)
  Windows       the late window decides, the early one does not; the lift guard;
                unreadable steps; angles compared exactly
  Verdict       a car that never pulls, one that always does, a borderline one; the
                cuts are drive_c_rule_numbers.cuts for the realised blocks; the sham
                Fisher gate, the channel check, n_B, refused below 16
  Freeze        stage C refuses a changed list, a wrong hash, an uncommitted freeze or
                script, changed code, another plant, a changed or moved log
  RunOnce       guard 5: a second run in the folder or from a copy, a run that died,
                the result written before it is shown; stage B after stage C
  Integrity     IC33: a hand-edited stage_a.json or frozen.json is refused
  Files         guard 1, one log under two names, recorded paths, a trailing comma,
                another separator or encoding, a console that cannot print a name
  KneeScan      item 7 on hand-built pairs: the first evidence decides; a retard in two
                counts; the right-censored bound; a KI that cannot be computed
  Knee          the Turnbull median recovers a known median; a flat at one half; the
                retune logic; an end-to-end knee with a known onset; the speed halves
  Stats         Holm's family, blocks over the side set, the cut's design values,
                v-hat, the single-session floor
  Spark         item 8's action rule and label, end to end, one session and two
  DryRun        -3.81 / 2.07 and -1.78 on car_spark_boost.py's committed readings
"""
import contextlib
import hashlib
import io
import json
import math
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import drive_c_analysis as D                              # noqa: E402
import drive_c_rule_numbers as RN                         # noqa: E402

ORDER = ["Engine speed", "Air mass flow", "Actual ignition angle",
         "Target ignition angle from torque intervention", "Coolant temperature", "Ambient temperature"]
ROW_S = 0.15
ACT = "Actual ignition angle"


# ---- the synthetic logger ----------------------------------------------------------
def write_log(path, duration, sig, order=ORDER, row_s=ROW_S, phase=0, chooser=None, raw=None):
    """Row i at i * row_s polls order[(i - phase) % N] (or chooser(i)); every other channel
    keeps its last value; a channel reads 0 until its first poll (AUDIT.md M8)."""
    n = int(round(duration / row_s))
    N = len(order)
    cur = ["0"] * N
    out = ["Time," + ",".join(f'"{c}"' for c in order)]
    for i in range(n):
        t = round(i * row_s, 3)
        c = (i - phase) % N if chooser is None else chooser(i)
        v = sig[order[c]](t)
        cur[c] = v if isinstance(v, str) else f"{v:.2f}"
        if raw is not None and (i, order[c]) in raw:
            cur[c] = raw[(i, order[c])]
        out.append(f"{t:.3f}," + ",".join(cur))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    return path


def grid(t, name="Air mass flow", order=ORDER, phase=0):
    """The first poll of a channel at or after t."""
    n_ch, p = len(order), order.index(name)
    i = int(math.ceil(t / ROW_S - 1e-9))
    while (i - phase) % n_ch != p:
        i += 1
    return round(i * ROW_S, 3)


@contextlib.contextmanager
def quiet():
    with contextlib.redirect_stdout(io.StringIO()):
        yield


@contextlib.contextmanager
def unlocked(results_root=None):
    """Stages B and C on synthetic logs from a working copy: the script and the freeze count as
    committed (committed() is tested on its own), and an earlier stage C is looked for under
    results_root (default: nowhere but the frozen list's folder)."""
    root = results_root if results_root is not None else os.path.join(tempfile.gettempdir(), "no-such-folder-dc")
    with mock.patch.object(D, "committed", return_value=True), mock.patch.object(D, "RESULTS_ROOT", root):
        yield


class C2Drive:
    """Light cruise with load steps; every channel a function of time. Each press sits on
    the air poll grid, so t1 is the press and t0 = t1 - 0.9 s; with ORDER the actual is
    polled 0.15 s and the target 0.30 s after each air poll."""

    def __init__(self, presses, hold=7.0, level=450.0, cruise=60.0, rpm=1800.0, cool=90.0, amb=25.0,
                 order=ORDER, phase=0, rise=0.0):
        self.order, self.phase, self.rise = order, phase, rise
        self.presses = [grid(t, order=order, phase=phase) for t in presses]
        n = len(self.presses)
        self.hold = list(hold) if isinstance(hold, (list, tuple)) else [hold] * n
        self.level = list(level) if isinstance(level, (list, tuple)) else [level] * n
        self.cruise, self.rpm0, self.cool, self.amb = cruise, rpm, cool, amb
        self.ret, self.air_over, self.rpm_over, self.tgt_over = [], [], [], []

    def step(self, t):
        for j, ts in enumerate(self.presses):
            if ts <= t < ts + self.hold[j]:
                return j
        return None

    def air(self, t):
        for lo, hi, v in self.air_over:
            if lo <= t < hi:
                return v
        j = self.step(t)
        if j is not None:
            return self.level[j] + self.rise * (t - self.presses[j])
        return self.cruise + 1.5 * math.sin(t / 5.0)

    def rpm(self, t):
        for lo, hi, v in self.rpm_over:
            if lo <= t < hi:
                return v
        j = self.step(t)
        return self.rpm0 + 3.0 * math.sin(t / 7.0) + (20.0 * (t - self.presses[j]) if j is not None else 0.0)

    def target(self, t):
        for lo, hi, v in self.tgt_over:
            if lo <= t < hi:
                return v
        return 3.0 if self.step(t) is not None else 20.25

    def actual(self, t):
        return self.target(t) - sum(d for lo, hi, d in self.ret if lo <= t < hi)

    def coolant(self, t):
        return self.cool + 0.2 * math.sin(t / 30.0)

    def ambient(self, t):
        return self.amb + 0.1 * math.sin(t / 40.0)

    # retards placed on the grid, relative to each step's t1
    def late(self, j, deg=3.0):
        t1 = self.presses[j]
        self.ret.append((t1 + 1.9, t1 + 4.7, deg))

    def early(self, j, deg=3.0):
        t1 = self.presses[j]
        self.ret.append((t1 + 0.1, t1 + 0.2, deg))

    def pre(self, j, deg=1.5):
        t0 = self.presses[j] - 0.9
        self.ret.append((t0 - 20.0 + 0.01, t0 + 0.01, deg))

    def signals(self):
        f = {"Engine speed": self.rpm, "Air mass flow": self.air, "Actual ignition angle": self.actual,
             "Target ignition angle from torque intervention": self.target,
             "Coolant temperature": self.coolant, "Ambient temperature": self.ambient}
        return {c: f[c] for c in self.order}

    def write(self, path, duration=None, **kw):
        duration = duration or (self.presses[-1] + 130.0)
        return write_log(path, duration, self.signals(), order=self.order, phase=self.phase, **kw)


def timeline(n_blocks=4, per_block=6, period=75.0, gap=330.0, lead=90.0):
    """Press times: blocks of steps 75 s apart, blocks 5+ minutes apart."""
    out, t = [], lead
    for _ in range(n_blocks):
        out += [t + j * period for j in range(per_block)]
        t += per_block * period + gap
    return out


class C1Drive:
    """Loaded segments in a held gear: cruise at 80 kg/h between them."""

    def __init__(self, starts, seg_len=25.0, rpm=2700.0, air_seg=427.4, cruise=80.0, target=6.0,
                 cool=90.0, amb=25.0):
        self.starts = [grid(t) for t in starts]
        n = len(self.starts)
        self.seg_len = seg_len
        self.rpm_ = list(rpm) if isinstance(rpm, (list, tuple)) else [rpm] * n
        self.air_seg = list(air_seg) if isinstance(air_seg, (list, tuple)) else [air_seg] * n
        self.cruise, self.cool, self.amb = cruise, cool, amb
        self.target_fn = target if callable(target) else (lambda j, t: target)
        self.ret = []
        self.retard_fn = None

    def seg(self, t):
        for j, ts in enumerate(self.starts):
            if ts <= t < ts + self.seg_len:
                return j
        return None

    def which_rpm(self, t):
        j = self.seg(t)
        if j is None:
            later = [k for k, ts in enumerate(self.starts) if ts > t]
            j = later[0] if later else len(self.starts) - 1
        return self.rpm_[j]

    def air(self, t):
        j = self.seg(t)
        return self.air_seg[j] if j is not None else self.cruise + 1.5 * math.sin(t / 5.0)

    def rpm(self, t):
        return self.which_rpm(t) + 3.0 * math.sin(t / 7.0)

    def target(self, t):
        j = self.seg(t)
        return self.target_fn(j, t) if j is not None else 20.25

    def actual(self, t):
        r = sum(d for lo, hi, d in self.ret if lo <= t < hi)
        if self.retard_fn is not None:
            r += self.retard_fn(t)
        return self.target(t) - r

    def coolant(self, t):
        return self.cool + 0.2 * math.sin(t / 30.0)

    def ambient(self, t):
        return self.amb + 0.1 * math.sin(t / 40.0)

    def onset(self, j, after=15.0, deg=3.0):
        ts = self.starts[j]
        self.ret.append((ts + after, ts + self.seg_len, deg))

    def signals(self):
        return {"Engine speed": self.rpm, "Air mass flow": self.air, "Actual ignition angle": self.actual,
                "Target ignition angle from torque intervention": self.target,
                "Coolant temperature": self.coolant, "Ambient temperature": self.ambient}

    def write(self, path, duration=None):
        return write_log(path, duration or (self.starts[-1] + self.seg_len + 40.0), self.signals())


def run_all(tmp, c2, c1, name="out", logs=None):
    """Stages A, B and C into tmp/name, as the command line runs them."""
    out = os.path.join(tmp, name)
    with quiet(), unlocked(out):
        sa = D.stage_a(c2, c1, out)
        fz = D.stage_b(out)
        res = D.stage_c(os.path.join(out, "frozen.json"), os.path.join(out, "frozen.sha256"), logs)
    return sa, fz, res


def freeze(tmp, c2, c1, name="out"):
    """Stages A and B into tmp/name; returns (stage A, frozen list, out folder)."""
    out = os.path.join(tmp, name)
    with quiet(), unlocked(out):
        sa = D.stage_a(c2, c1, out)
        fz = D.stage_b(out)
    return sa, fz, out


class Tmp(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.tmp = self._td.name

    def tearDown(self):
        self._td.cleanup()

    def path(self, name):
        return os.path.join(self.tmp, name)


def channel_c1(path, n=4):
    """A C1 file whose segments each hold one persistent onset (the channel check passes)."""
    d = C1Drive([60.0 + 60.0 * j for j in range(n)])
    for j in range(n):
        d.onset(j)
    return d.write(path)


_MOD = {}


def setUpModule():
    _MOD["tmp"] = tempfile.TemporaryDirectory()


def tearDownModule():
    _MOD["tmp"].cleanup()


def c2_16():
    """A C2 file with 16 valid primary steps that never pull: stage C runs only from 16 (item 5),
    so every C1 scenario below is driven beside it. Written once; never changed."""
    if "c2" not in _MOD:
        _MOD["c2"] = C2Drive(timeline(2, 8)).write(os.path.join(_MOD["tmp"].name, "c2_16.csv"))
    return _MOD["c2"]


# ---- differential blindness: retards only inside the response windows ---------------
def response_windows(sa):
    """Every window whose retard decides something, per file: each detected step's early and late
    windows, each stage-A-valid sham's window, each C1 segment (stage B reads no C1 value)."""
    out = {}
    for s in sa["steps"]:
        out.setdefault(s["file"], []).append(D.response_window(s))
    for h in sa["shams"]:
        if h["stage_a_valid"]:
            out.setdefault(h["file"], []).append(tuple(h["window"]))
    for g in sa["segments"]:
        out.setdefault(g["file"], []).append((g["first_t"] - 1.0, g["last_reading_t"] + 1.0))
    return out


def with_response_retard(sig, windows, deg=6.0):
    """The same signals with the actual angle `deg` lower strictly inside the windows."""
    act = sig[ACT]

    def a(t):
        return act(t) - (deg if any(lo < t <= hi for lo, hi in windows) else 0.0)
    return dict(sig, **{ACT: a})


def frozen_view(fz):
    """The frozen list without what must differ between two different files (timestamps, paths,
    SHA-256s): what stage C would be told."""
    x = D.canon(fz)
    for f in x["files"]:
        f.pop("sha256", None)
        f.pop("name", None)
    return x


# =====================================================================================
class Blind(Tmp):
    def test_stage_a_never_loads_an_ignition_column(self):
        d = C2Drive(timeline(1, 2))
        p = d.write(self.path("c2.csv"))
        c1 = channel_c1(self.path("c1.csv"))
        hdr = D.read_header(p)
        ign = {i for i, h in enumerate(hdr) if h.lower() in D.IGN_NAMES}
        self.assertEqual(len(ign), 2)
        seen = []
        real = D.pd.read_csv

        def spy(path, *a, **k):
            seen.append(k.get("usecols"))
            return real(path, *a, **k)
        with mock.patch.object(D.pd, "read_csv", side_effect=spy), quiet():
            D.stage_a([p], [c1], self.path("out"))
        self.assertTrue(seen)
        for cols in seen:
            self.assertIsNotNone(cols, "a read without usecols loads every column")
            self.assertFalse(set(cols) & ign, f"stage A asked for an ignition column: {cols}")

    def test_stage_b_converts_inside_the_pre_windows_only(self):
        d = C2Drive(timeline(1, 3))
        p = d.write(self.path("c2.csv"))
        captured = []
        real = D.ignition_genuine

        def spy(lf, runs_info, text, allowed=None):
            out = real(lf, runs_info, text, allowed)
            captured.append((allowed, out))
            return out
        with quiet():
            sa = D.stage_a([p], [], self.path("out"))
        with mock.patch.object(D, "ignition_genuine", side_effect=spy), quiet(), unlocked():
            D.stage_b(self.path("out"))
        self.assertEqual(len(captured), 1)
        allowed, out = captured[0]
        t, _ = D.load_blind(D.LogFile(p, "C2"))
        union = np.zeros(len(t), bool)
        for x in sa["steps"] + sa["shams"]:
            if x["stage_a_valid"]:
                union |= (t > x["P"][0]) & (t <= x["P"][1])
        self.assertTrue(np.array_equal(allowed, union))
        self.assertTrue(np.any(allowed) and np.any(~allowed))
        for s in sa["steps"]:                     # no early or late window is ever convertible
            lo, hi = D.response_window(s)
            self.assertFalse(np.any(allowed & (t > lo) & (t <= hi)))
        for h in sa["shams"]:                     # nor a sham's window
            if h["stage_a_valid"]:
                self.assertFalse(np.any(allowed & (t > h["window"][0]) & (t <= h["window"][1])))
        for k in D.IGN:
            gen, vals = out[k]
            self.assertFalse(np.any(np.isfinite(vals[~allowed])))
            self.assertTrue(np.any(np.isfinite(vals[allowed])))

    def differential(self, sig_fn, duration, c1=None):
        """Two logs equal but for a 6 deg retard inside every response window freeze alike."""
        pa = write_log(self.path("a.csv"), duration, sig_fn())
        sa, fza, _ = freeze(self.tmp, [pa], [c1] if c1 else [], "oa")
        wins = response_windows(sa)
        pb = write_log(self.path("b.csv"), duration, with_response_retard(sig_fn(), wins.get(0, [])))
        _, fzb, _ = freeze(self.tmp, [pb], [c1] if c1 else [], "ob")
        self.assertEqual(frozen_view(fza), frozen_view(fzb), D.first_difference(frozen_view(fza), frozen_view(fzb)))
        return sa, fza

    def test_response_windows_never_reach_the_freeze(self):
        d = C2Drive(timeline(2, 4))
        for j in (1, 4):
            d.pre(j)                           # baselines that sit on the B rule's edge
        sa, fz = self.differential(d.signals, d.presses[-1] + 130.0)
        self.assertEqual(fz["N"] + fz["n_B"], 8)

    def test_a_c1_file_never_reaches_the_freeze(self):
        d = C1Drive([60.0 + 60.0 * j for j in range(4)])
        pa = d.write(self.path("c1a.csv"))
        sa, fza, _ = freeze(self.tmp, [], [pa], "oa")
        d.ret.append((0.0, 1e9, 3.0))            # a different car in every C1 reading
        pb = d.write(self.path("c1b.csv"))
        _, fzb, _ = freeze(self.tmp, [], [pb], "ob")
        self.assertEqual(frozen_view(fza), frozen_view(fzb))


# =====================================================================================
def press_from_held_step():
    """Review repro r1: a half press (60 -> 95 kg/h, easing to 82, held 11 s), then full pedal
    from the held level; step 1 pulls 3 deg through its hold."""
    t1 = grid(100.0)
    t2 = grid(t1 + 11.0)

    def air(t):
        if t1 <= t < t1 + 2.0:
            return 95.0
        if t1 + 2.0 <= t < t2:
            return 82.0
        if t2 <= t < t2 + 7.0:
            return 250.0
        return 60.0 + 1.5 * math.sin(t / 5.0)
    return {"Engine speed": lambda t: 1500.0 + 2.0 * math.sin(t / 7.0), "Air mass flow": air,
            ACT: lambda t: 20.25 - (3.0 if t1 + 1.0 < t < t2 - 0.5 else 0.0),
            "Target ignition angle from torque intervention": lambda t: 20.25,
            "Coolant temperature": lambda t: 90.0, "Ambient temperature": lambda t: 25.0}, (t1, t2)


def long_held_step(late_pull=False):
    """Review repro r8: 60 -> 120 kg/h, easing to a held ~98 (no fall), then full pedal 22 s
    later from the held level; the last 9 s before the second press read 1.5 deg."""
    t1 = grid(90.0)
    t2 = grid(t1 + 22.0)
    rel = t2 + 7.0

    def air(t):
        if t1 <= t < t1 + 1.8:
            return 120.0
        if t1 + 1.8 <= t < t1 + 3.6:
            return 110.0
        if t1 + 3.6 <= t < t2:
            return 98.0 + 1.0 * math.sin(t)
        if t2 <= t < rel:
            return 450.0
        return 60.0 + 1.5 * math.sin(t / 5.0)

    def target(t):
        return 3.0 if t2 <= t < rel else (12.0 if t1 <= t < t2 else 20.25)

    def retard(t):
        r = 1.5 if (t2 - 0.9) - 9.0 < t <= (t2 - 0.9) + 0.01 else 0.0
        return r + (6.0 if late_pull and t1 + 1.0 < t <= t1 + 5.0 else 0.0)
    return {"Engine speed": lambda t: 1800.0 + 3.0 * math.sin(t / 7.0) + (20.0 * (t - t2) if t2 <= t < rel else 0.0),
            "Air mass flow": air, ACT: lambda t: target(t) - retard(t),
            "Target ignition angle from torque intervention": target,
            "Coolant temperature": lambda t: 90.0 + 0.2 * math.sin(t / 30.0),
            "Ambient temperature": lambda t: 25.0 + 0.1 * math.sin(t / 40.0)}, rel + 120.0


class Overlap(Tmp):
    """IC36: no pre-window stage B reads may hold a response window."""

    def test_a_press_from_a_held_step_fails_v3(self):
        sig, (t1, t2) = press_from_held_step()
        p = write_log(self.path("r1.csv"), 260.0, sig)
        sa, fz, _ = freeze(self.tmp, [p], [])
        s1, s2 = sa["steps"][0], sa["steps"][1]
        self.assertTrue(s1["stage_a_valid_primary"], s1["reasons"])
        self.assertTrue(s2["redetection"])
        self.assertFalse(s2["flags"]["V3"])
        self.assertIn("IC36", " ".join(s2["reasons"]["V3"]))
        self.assertEqual(fz["n_B"], 0, "step 1's late-window pull was read into step 2's baseline")
        self.assertEqual(fz["N"], 1)

    def test_a_long_held_step_fails_v3_and_its_late_window_stays_unread(self):
        froz = []
        for pull in (False, True):
            sig, dur = long_held_step(pull)
            p = write_log(self.path(f"r8_{pull}.csv"), dur, sig)
            sa, fz, _ = freeze(self.tmp, [p], [], f"o{pull}")
            froz.append(fz)
            s2 = [s for s in sa["steps"] if s["redetection"]][0]
            self.assertFalse(s2["stage_a_valid"])
            self.assertIn("IC36", " ".join(s2["reasons"]["V3"]))
        self.assertEqual(frozen_view(froz[0]), frozen_view(froz[1]))

    def test_the_plans_minute_puts_anchor_a_in_the_next_pre_window(self):
        d = C2Drive([90.0 + 67.0 * j for j in range(7)])
        p = d.write(self.path("plan.csv"))
        sa, fz, _ = freeze(self.tmp, [p], [])
        self.assertEqual(fz["N"], 7)
        inside = [h for h in sa["shams"] if h["anchor"] == "a" and "P" in h["reasons"]]
        self.assertEqual(len(inside), 6, "each press but the last puts its anchor (a) in the next pre-window")
        for h in inside:
            self.assertFalse(h["stage_a_valid"])
            self.assertIn("IC36", " ".join(h["reasons"]["P"]))
        for h in sa["shams"]:
            if h["stage_a_valid"]:
                for s in sa["steps"]:
                    if s["stage_a_valid"]:
                        self.assertFalse(D._meets(h["window"], s["P"]))
        pb = write_log(self.path("planb.csv"), d.presses[-1] + 130.0,
                       with_response_retard(d.signals(), response_windows(sa)[0]))
        _, fzb, _ = freeze(self.tmp, [pb], [], "ob")
        self.assertEqual(frozen_view(fz), frozen_view(fzb))

    def test_stage_b_refuses_an_overlap_that_reaches_it(self):
        sig, _ = press_from_held_step()
        p = write_log(self.path("r1.csv"), 260.0, sig)
        out = self.path("o")
        with mock.patch.object(D, "ic36_steps", lambda steps: None), quiet(), unlocked():
            D.stage_a([p], [], out)
            with self.assertRaises(SystemExit) as cm:
                D.stage_b(out)
        self.assertIn("IC36", str(cm.exception))
        self.assertIn("no ignition value was converted", str(cm.exception))

    def test_a_time_reset_never_widens_a_pre_window(self):
        t = np.r_[np.arange(0, 60, 0.15), np.arange(0, 60, 0.15)]
        runs = [dict(start=0, end=399), dict(start=400, end=799)]
        step = dict(file=0, run=1, P=[20.0, 40.0], t0=40.0, t1=40.9, t_W=45.9)
        allowed, forbid = D.pre_window_rows(t, runs, [step], [step], [])
        self.assertFalse(np.any(allowed[:400]), "rows of the other run at the same clock times")
        self.assertTrue(np.all(allowed[400:][(t[400:] > 20.0) & (t[400:] <= 40.0)]))
        self.assertFalse(np.any(forbid[:400]))
        self.assertFalse(np.any(allowed & forbid))


# =====================================================================================
class Genuine(Tmp):
    def _file(self, **kw):
        sig = {"Engine speed": lambda t: 1800.0 if t < 20 else 1800.0 + t,
               "Air mass flow": lambda t: 60.0 + t,
               "Actual ignition angle": lambda t: 10.5,
               "Target ignition angle from torque intervention": lambda t: 10.5,
               "Coolant temperature": lambda t: 150.0 if 30.0 <= t < 31.0 else 85.0 + 0.01 * t,
               "Ambient temperature": lambda t: 25.0 + 0.01 * t}
        return write_log(self.path("g.csv"), 60.0, sig, **kw)

    def test_every_poll_found_repeats_included(self):
        p = self._file()
        lf = D.LogFile(p, "C2")
        t, vals = D.load_blind(lf)
        info, _ = D.runs_info_of(t, vals, lf)
        self.assertEqual(len(info), 1)
        self.assertFalse(info[0]["flagged"])
        self.assertEqual(info[0]["phase"], 0)
        self.assertEqual(info[0]["share"], 1.0)
        rpm = D.blind_genuine(vals["rpm"], lf, "rpm", info)
        polls = np.flatnonzero(rpm)
        self.assertEqual(len(polls), 400 // 6 + 1)              # every sixth row from row 0
        self.assertTrue(np.all(polls % 6 == 0))
        changes = np.flatnonzero(np.r_[True, np.diff(vals["rpm"]) != 0])
        self.assertLess(len(changes), len(polls), "the constant first 20 s repeat their value")

    def test_placeholders_blanks_and_range(self):
        p = self._file()
        lf = D.LogFile(p, "C2")
        t, vals = D.load_blind(lf)
        info, _ = D.runs_info_of(t, vals, lf)
        cool = D.blind_genuine(vals["cool"], lf, "cool", info)
        rows = np.flatnonzero(cool)
        self.assertEqual(rows[0], 4)                            # rows 0-3 are the placeholder zero
        self.assertFalse(np.any((t[rows] >= 30.0) & (t[rows] < 31.0)), "150 C is outside 40-130 C")
        # ignition text: a leading zero literal before the first answer, and a blank cell
        raw = {(2, "Actual ignition angle"): "0.00", (8, "Actual ignition angle"): "0",
               (14, "Actual ignition angle"): "", (3, "Target ignition angle from torque intervention"): "0"}
        p2 = write_log(self.path("g2.csv"), 60.0, {**{c: (lambda t: 10.5) for c in ORDER[2:4]},
                                                   "Engine speed": lambda t: 1800.0 + t,
                                                   "Air mass flow": lambda t: 60.0 + t,
                                                   "Coolant temperature": lambda t: 85.0 + 0.01 * t,
                                                   "Ambient temperature": lambda t: 25.0 + 0.01 * t}, raw=raw)
        lf2 = D.LogFile(p2, "C2")
        t2, v2 = D.load_blind(lf2)
        info2, _ = D.runs_info_of(t2, v2, lf2)
        ign = D.ignition_genuine(lf2, info2, D.load_ignition_text(lf2), None)
        act_rows = np.flatnonzero(ign["act"][0])
        self.assertEqual(act_rows[0], 20, "rows 2 and 8 are placeholders, 14 is blank")
        self.assertEqual(np.flatnonzero(ign["tgt"][0])[0], 9)

    def test_a_scrambled_logger_is_flagged(self):
        rng = np.random.default_rng(3)
        choice = rng.integers(0, 6, 4000)
        p = self._file(chooser=lambda i: int(choice[i]))
        lf = D.LogFile(p, "C2")
        t, vals = D.load_blind(lf)
        info, _ = D.runs_info_of(t, vals, lf)
        self.assertTrue(info[0]["flagged"])
        self.assertLess(info[0]["share"], 0.99)
        g = D.blind_genuine(vals["air"], lf, "air", info)
        ch = np.r_[False, np.diff(vals["air"]) != 0]
        self.assertTrue(np.array_equal(g, ch & (vals["air"] >= 4)), "a flagged run counts value changes only")

    def test_a_logger_break_starts_a_new_run(self):
        t = np.r_[np.arange(0, 30, 0.15), np.arange(40, 70, 0.15)]
        runs, med = D.find_runs(t)
        self.assertEqual(len(runs), 2)
        self.assertAlmostEqual(med, 0.15)

    def test_a_dropped_row_is_a_break_not_a_lost_run(self):
        """One poll skipped mid-file shifts the phase with no time gap: two clean runs, and
        the steps on both sides of it stay valid."""
        drop = 1500                                       # row 1500, t = 225 s
        d = C2Drive([90.0, 300.0])
        p = d.write(self.path("drop.csv"), chooser=lambda i: i % 6 if i < drop else (i + 1) % 6)
        lf = D.LogFile(p, "C2")
        t, vals = D.load_blind(lf)
        info, _ = D.runs_info_of(t, vals, lf)
        good = [r for r in info if not r["flagged"]]
        self.assertEqual([r["phase"] for r in good], [0, 5])
        self.assertTrue(all(r["share"] == 1.0 for r in good))
        self.assertLessEqual(sum(r["end"] - r["start"] + 1 for r in info if r["flagged"]), 12)
        with quiet():
            sa = D.stage_a([p], [], self.path("o"))
        firsts = [s for s in sa["steps"] if not s["redetection"]]
        self.assertEqual(len(firsts), 2)
        self.assertTrue(all(s["stage_a_valid_primary"] for s in firsts), [s["reasons"] for s in firsts])


# =====================================================================================
def readings(values, dt=0.9, t0=0.0):
    v = np.asarray(values, float)
    t = t0 + dt * np.arange(len(v))
    return D.Readings(np.arange(len(v)) * 6, t, v)


class Detector(unittest.TestCase):
    def test_clean_step(self):
        s = D.detect_steps(readings([60.0] * 30 + [450.0] * 8 + [60.0] * 30))
        self.assertEqual(len(s), 1)
        self.assertEqual((s[0]["k"], s[0]["trig"], s[0]["trigger"]), (30, 30, "k"))
        self.assertAlmostEqual(s[0]["t0"], 29 * 0.9)
        self.assertAlmostEqual(s[0]["M"], 60.0)
        self.assertEqual(s[0]["f"], 38)
        self.assertAlmostEqual(s[0]["t_W"], min(30 * 0.9 + 5.0, 37 * 0.9 - 0.6))

    def test_wobbly_cruise_gives_no_step(self):
        w = [60.0 + (8.0 if i % 2 else -8.0) for i in range(80)]
        self.assertEqual(D.detect_steps(readings(w)), [])

    def test_late_trigger(self):
        s = D.detect_steps(readings([60.0] * 30 + [80.0] + [450.0] * 8 + [60.0] * 30))
        self.assertEqual(len(s), 1)
        self.assertEqual((s[0]["k"], s[0]["trig"], s[0]["trigger"]), (30, 31, "k+1"))
        self.assertAlmostEqual(s[0]["t0"], 29 * 0.9)
        self.assertAlmostEqual(s[0]["t1"], 31 * 0.9)

    def test_no_trigger_and_no_confirmation(self):
        self.assertEqual(D.detect_steps(readings([60.0] * 30 + [80.0, 80.0] + [60.0] * 30)), [])
        self.assertEqual(D.detect_steps(readings([60.0] * 30 + [450.0] + [60.0] * 30)), [])
        self.assertEqual(D.detect_steps(readings([60.0] * 30 + [450.0, 450.0, 80.0] + [60.0] * 30)), [],
                         "the second confirming reading is under 1.5 M")
        self.assertEqual(D.detect_steps(readings([10.0] * 30 + [16.0, 30.0, 30.0] + [10.0] * 30)), [],
                         "the first confirming reading is under M + 25 kg/h")

    def test_plateau_wobble_is_a_fall(self):
        s = D.detect_steps(readings([60.0] * 30 + [450.0, 450.0, 360.0] + [450.0] * 5 + [60.0] * 30))
        self.assertEqual(s[0]["f"], 32, "360 is under 0.85 x 450")
        self.assertAlmostEqual(s[0]["t_W"], 31 * 0.9 - 0.6)

    def test_held_step_rescanned_after_10_s(self):
        s = D.detect_steps(readings([60.0] * 30 + list(np.linspace(300, 900, 20)) + [60.0] * 30))
        self.assertGreaterEqual(len(s), 2)
        self.assertFalse(s[0]["redetection"])
        self.assertTrue(s[1]["redetection"])

    def test_every_redetection_fails_v3(self):
        """IC10 / IC36: a re-detection fails V3 by construction, whatever M did."""
        steps = D.detect_steps(readings([60.0] * 30 + list(np.linspace(300, 900, 20)) + [60.0] * 30))
        for s in steps:
            s.update(id=f"S{s['k']}", file=0, run=0, flags={"V3": True}, reasons={}, stage_a_valid=True,
                     stage_a_valid_primary=True)
        D.ic36_steps(steps)
        for s in steps:
            self.assertEqual(s["flags"]["V3"], not s["redetection"])


# =====================================================================================
class Validity(Tmp):
    """One step per file, built to fail exactly one criterion."""

    def one(self, name, drive=None, order=ORDER, presses=(90.0,), **kw):
        d = drive or C2Drive(list(presses), order=order, **kw)
        p = d.write(self.path(name + ".csv"))
        with quiet():
            sa = D.stage_a([p], [], self.path(name))
        first = [s for s in sa["steps"] if not s["redetection"]]
        return first[0], d, sa

    def test_a_good_step_passes(self):
        s, _, _ = self.one("good")
        self.assertTrue(s["stage_a_valid_primary"], s["reasons"])
        self.assertGreater(s["KI1"], 1.0)

    def test_v1_unsteady_cruise(self):
        d = C2Drive([90.0])
        d.air_over.append((d.presses[0] - 10.2, d.presses[0] - 9.0, 36.0))
        s, _, _ = self.one("v1", drive=d)
        self.assertFalse(s["flags"]["V1"])
        self.assertEqual([k for k, v in s["flags"].items() if not v], ["V1"])

    def test_v1_engine_speed(self):
        d = C2Drive([90.0])
        d.rpm_over.append((d.presses[0] - 12.0, d.presses[0] - 6.0, 1900.0))
        d.rpm_over.append((d.presses[0] - 6.0, d.presses[0] - 0.95, 1890.0))
        s, _, _ = self.one("v1r", drive=d)
        self.assertFalse(s["flags"]["V1"])
        self.assertIn("max/min", " ".join(s["reasons"]["V1"]))

    def test_v2_load_too_high(self):
        s, _, _ = self.one("v2", cruise=120.0)
        self.assertEqual([k for k, v in s["flags"].items() if not v], ["V2"])

    def test_v3_spacing(self):
        d = C2Drive([90.0])
        d.air_over.append((d.presses[0] - 30.0, d.presses[0] - 29.1, 100.0))
        s, _, _ = self.one("v3", drive=d)
        self.assertEqual([k for k, v in s["flags"].items() if not v], ["V3"])

    def test_v4_gear_change(self):
        d = C2Drive([90.0])
        d.rpm_over.append((d.presses[0] + 2.0, d.presses[0] + 7.0, 2300.0))
        s, _, _ = self.one("v4", drive=d)
        self.assertEqual([k for k, v in s["flags"].items() if not v], ["V4"])

    def test_v5_held_too_short(self):
        s, _, _ = self.one("v5", hold=2.6)
        self.assertFalse(s["flags"]["V5"])

    def test_v6_cold_and_no_ambient(self):
        s, _, _ = self.one("v6", cool=70.0)
        self.assertFalse(s["flags"]["V6"])
        order = [c for c in ORDER if c != "Ambient temperature"]
        s, _, _ = self.one("v6b", order=order)
        self.assertIn("ambient not logged", s["reasons"]["V6"])

    def test_v7_primary_side_and_out(self):
        s, _, _ = self.one("v7s", level=105.0)
        self.assertEqual(s["set"], "side")
        self.assertTrue(0.85 < s["KI1"] <= 1.0)
        self.assertTrue(s["stage_a_valid"])
        self.assertFalse(s["stage_a_valid_primary"])
        s, _, _ = self.one("v7o", level=95.0)
        self.assertEqual(s["set"], "out")
        self.assertFalse(s["stage_a_valid"])

    def test_v7_a_pinned_air_reading_counts_as_high(self):
        """V7: "A pinned air reading counts as high; its KI1 is flagged as a lower bound" -- even
        where the KI1 computed from the pinned value would not reach 1.0."""
        with mock.patch.object(D, "knock_integral", return_value=0.5):
            s, _, _ = self.one("v7p", level=1020.0)
            self.assertEqual(s["set"], "primary")
            self.assertTrue(s["KI1_lower_bound"])
            self.assertTrue(s["stage_a_valid_primary"], s["reasons"])
            s, _, _ = self.one("v7q", level=1000.0)
            self.assertEqual(s["set"], "out", "unpinned, the value decides")

    def test_v8_both_orders(self):
        rev = ORDER[:2] + [ORDER[3], ORDER[2]] + ORDER[4:]
        s, _, _ = self.one("v8r", order=rev)
        self.assertEqual([k for k, v in s["flags"].items() if not v], ["V8"])
        lf = D.LogFile(self.path("v8r.csv"), "C2")
        self.assertEqual(lf.v8["lag_rows"], 5)
        wrap = [ORDER[3]] + ORDER[:2] + ORDER[4:] + [ORDER[2]]       # actual last, target first
        hdr = self.path("wrap.csv")
        with open(hdr, "w") as fh:
            fh.write("Time," + ",".join(wrap) + "\n0,0,0,0,0,0,0\n")
        self.assertTrue(D.LogFile(hdr, "C2").v8["ok"])
        gap2 = ORDER[:2] + [ORDER[2], ORDER[4], ORDER[3], ORDER[5]]
        with open(hdr, "w") as fh:
            fh.write("Time," + ",".join(gap2) + "\n0,0,0,0,0,0,0\n")
        self.assertEqual(D.LogFile(hdr, "C2").v8["lag_rows"], 2)
        self.assertTrue(D.LogFile(hdr, "C2").v8["ok"])

    def test_d1_flagged_run_excludes_its_steps(self):
        d = C2Drive([90.0], rise=10.0)            # a moving plateau: value changes see every poll
        rng = np.random.default_rng(5)
        choice = rng.integers(0, 6, 2000)
        p = d.write(self.path("d1.csv"), chooser=lambda i: int(choice[i]))
        with quiet():
            sa = D.stage_a([p], [], self.path("d1"))
        self.assertTrue(sa["files"][0]["runs"][0]["flagged"])
        self.assertTrue(sa["steps"], "value changes still find the step")
        for s in sa["steps"]:
            self.assertFalse(s["flags"]["D1"])
            self.assertFalse(s["stage_a_valid"])


# =====================================================================================
class Shams(Tmp):
    def test_anchor_b_keeps_clear_of_a_step_in_another_run(self):
        """'More than 50 s after any fall': a logger break after a step does not reset that."""
        d = C2Drive([94.5])
        p = d.write(self.path("c2.csv"), duration=400.0)
        with open(p, encoding="utf-8") as fh:
            rows = fh.read().splitlines()
        out = [rows[0]]
        for r in rows[1:]:                    # a 1 s gap in the log at t = 103 s
            t, rest = r.split(",", 1)
            out.append(f"{float(t) + (1.0 if float(t) >= 103.0 else 0.0):.3f},{rest}")
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(out) + "\n")
        with quiet():
            sa = D.stage_a([p], [], self.path("o"))
        self.assertEqual(len(sa["files"][0]["runs"]), 2)
        s = sa["steps"][0]
        self.assertEqual(s["run"], 0)
        fall = s["tau_f"]
        b = [h["a"] for h in sa["shams"] if h["anchor"] == "b"]
        self.assertFalse([g for g in b if fall < g <= fall + 50.0], "a grid anchor within 50 s of the fall")
        self.assertIn(180.0, b)

    def test_a_blank_first_time_keeps_the_grid(self):
        p = C2Drive(timeline(1, 2)).write(self.path("a.csv"))
        with open(p, encoding="utf-8") as fh:
            rows = fh.read().splitlines()
        rows[1] = "," + rows[1].split(",", 1)[1]
        q = self.path("b.csv")
        with open(q, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(rows) + "\n")
        with quiet():
            sa = D.stage_a([p], [], self.path("oa"))
            sb = D.stage_a([q], [], self.path("ob"))
        ga = sorted(h["a"] for h in sa["shams"] if h["anchor"] == "b")
        gb = sorted(h["a"] for h in sb["shams"] if h["anchor"] == "b")
        self.assertTrue(ga)
        self.assertEqual(len(ga), len(gb), "the grid runs from the first row that has a time")
        self.assertTrue(np.allclose(ga, np.asarray(gb) - ROW_S))


# =====================================================================================
class Pairing(unittest.TestCase):
    """D2: retard = min(target before, target after) - actual."""

    def make(self, tgt_vals, act_vals, n=6):
        # target at rows 3 + 6m, actual at rows 2 + 6m: the target is polled one row after
        tr = np.arange(len(tgt_vals)) * n + 3
        ar = np.arange(len(act_vals)) * n + 2 + n
        tgt = D.Readings(tr, tr * ROW_S, tgt_vals)
        act = D.Readings(ar, ar * ROW_S, act_vals)
        return D.make_pairs(act, tgt, 1, n)

    def test_rising_and_falling_targets_never_create_a_pull(self):
        rng = np.random.default_rng(11)
        for _ in range(300):
            k = 12
            true_t = np.cumsum(rng.choice([-0.75, 0.0, 0.75], size=3 * k)) * rng.choice([1, 4]) + 20.0
            tgt_vals = true_t[0::3][:k]
            # the actual is read between two target reads; its true target lies between them
            lo = np.minimum(tgt_vals[:-1], tgt_vals[1:])
            hi = np.maximum(tgt_vals[:-1], tgt_vals[1:])
            true_target = lo + rng.uniform(0, 1, k - 1) * (hi - lo)
            true_retard = rng.choice([0.0, 0.0, 3.0], size=k - 1)
            act_vals = true_target - true_retard
            p = self.make(tgt_vals, act_vals)
            self.assertEqual(len(p), k - 1)
            self.assertTrue(np.all(p.retard <= true_retard + 1e-9))

    def test_a_step_change_between_reads(self):
        p = self.make(np.array([20.25, 3.0]), np.array([3.0]))
        self.assertEqual(float(p.retard[0]), 0.0, "the before-target alone would read 17.25")
        p = self.make(np.array([3.0, 20.25]), np.array([20.25]))
        self.assertEqual(float(p.retard[0]), -17.25)

    def test_the_before_target_must_be_recent(self):
        tgt = D.Readings([1, 7], [0.0, 3.0], [10.0, 10.0])
        act = D.Readings([6], [1.3], [7.0])
        self.assertEqual(len(D.make_pairs(act, tgt, 1, 6)), 0)
        act = D.Readings([6], [1.2], [7.0])
        self.assertEqual(len(D.make_pairs(act, tgt, 1, 6)), 1)

    def test_a_lost_target_poll_drops_the_pair(self):
        """IC37 (review): the actual follows a target dip to 10 deg; the target's own poll right
        after it is lost, so the next genuine target is a cycle later and reads 20 again. Taking
        it would read a 10 deg pull that never happened."""
        tgt = D.Readings([1, 13], [0.15, 1.95], [20.0, 20.0])     # row 7 (t 1.05) lost
        act = D.Readings([6], [0.90], [10.0])
        self.assertEqual(len(D.make_pairs(act, tgt, 1, 6)), 0)
        tgt = D.Readings([1, 7, 13], [0.15, 1.05, 1.95], [20.0, 10.0, 20.0])
        p = D.make_pairs(act, tgt, 1, 6)
        self.assertEqual(float(p.retard[0]), 0.0)
        self.assertEqual(len(D.make_pairs(act, tgt, 3, 6)), 0, "V8: a lag of 3 rows gives no pair")

    def test_window_membership(self):
        p = D.Pairs([1.0, 2.0], [1.5, 2.5], [1.6, 2.6], [10.0, 10.0], [7.0, 7.0])
        self.assertEqual(list(p.inside(1.0, 3.0)), [False, True], "the before-target at 1.0 is outside (1, 3]")
        self.assertEqual(list(p.inside(0.0, 2.5)), [True, False])


# =====================================================================================
class Windows(unittest.TestCase):
    """Item 3 on one step: only L decides; above 12 deg the step is unreadable."""
    step = dict(L=[11.0, 15.0], E=[9.0, 11.0])

    def pairs(self, times, retards):
        ta = np.asarray(times, float)
        return D.Pairs(ta - 0.75, ta, ta + 0.15, np.full(len(ta), 3.0), 3.0 - np.asarray(retards, float))

    def test_the_late_window_decides(self):
        p = self.pairs([9.9, 11.9, 12.8, 13.7, 14.6], [0, 3.0, 0, 0, 0])
        r = D.step_result(self.step, p, 0.0)
        self.assertTrue(r["pull"])
        self.assertEqual(r["timing"], "late")

    def test_the_early_window_does_not(self):
        p = self.pairs([9.9, 10.5, 11.9, 12.8, 13.7, 14.6], [3.0, 4.5, 0, 0, 0, 0])
        r = D.step_result(self.step, p, 0.0)
        self.assertFalse(r["pull"])
        self.assertTrue(r["early_pull"])
        self.assertEqual(r["timing"], "early only")

    def test_baseline_and_counts(self):
        p = self.pairs([11.9, 12.8, 13.7, 14.6], [2.25, 2.25, 0, 0])
        self.assertTrue(D.step_result(self.step, p, 0.0)["pull"])
        self.assertFalse(D.step_result(self.step, p, 0.75)["pull"], "1.5 deg above B is 2 counts")
        self.assertTrue(D.step_result(self.step, p, -0.75)["pull"])

    def test_unreadable_and_short(self):
        p = self.pairs([11.9, 12.8, 13.7], [12.75, 0, 0])
        r = D.step_result(self.step, p, 0.0)
        self.assertTrue(r["unreadable"])
        self.assertFalse(r["pull"])
        p = self.pairs([11.9, 12.8, 13.7], [12.0, 0, 0])
        self.assertTrue(D.step_result(self.step, p, 0.0)["pull"], "12 deg itself is readable")
        r = D.step_result(self.step, self.pairs([11.9, 12.8], [3.0, 3.0]), 0.0)
        self.assertTrue(r["short"] and r["unreadable"] and not r["pull"])

    def test_angles_are_compared_exactly(self):
        """IC7 (review): a tolerance on an angle threshold can only create a pull."""
        p = self.pairs([11.9, 12.8, 13.7], [2.2499995, 0, 0])
        self.assertFalse(D.step_result(self.step, p, 0.0)["pull"])
        p = self.pairs([11.9, 12.8, 13.7], [12.0000005, 0, 0])
        self.assertTrue(D.step_result(self.step, p, 0.0)["unreadable"])
        p = self.pairs([9.9, 11.9, 12.8, 13.7], [2.2499995, 0, 0, 0])
        self.assertFalse(D.step_result(self.step, p, 0.0)["early_pull"])


class LiftGuard(Tmp):
    def test_pairs_straddling_the_release_stay_out_of_L(self):
        # air polled first, actual third, target fourth: a target read 0.45 s after each air
        # poll lands inside the 0.6 s guard before tau_(f-1)
        order = ["Air mass flow", "Engine speed", "Actual ignition angle",
                 "Target ignition angle from torque intervention", "Coolant temperature", "Ambient temperature"]
        press = grid(90.0, order=order)
        hold = 5.0 + 0.5
        d = C2Drive([press], hold=hold, order=order)
        t1 = d.presses[0]
        tf_prev = max(x for x in [t1 + 0.9 * k for k in range(12)] if x < t1 + hold - 1e-9)
        tw = min(t1 + 5.0, tf_prev - 0.6)
        guard_act = round(tf_prev - 0.6, 3)            # its after-target is tf_prev - 0.45
        d.ret.append((guard_act - 0.01, guard_act + 0.01, 6.0))
        p = d.write(self.path("lift.csv"))
        with quiet():
            sa = D.stage_a([p], [], self.path("o"))
        s = sa["steps"][0]
        self.assertAlmostEqual(s["t_W"], tw, places=6)
        lf = D.LogFile(p, "C2")
        t, vals = D.load_blind(lf)
        runs = D.build_runs(lf, t, vals, sa["files"][0]["runs"])
        ign = D.ignition_genuine(lf, sa["files"][0]["runs"], D.load_ignition_text(lf), None)
        pr = D.run_pairs(runs[0], ign)
        hit = np.flatnonzero(np.isclose(pr.ta, guard_act))
        self.assertEqual(len(hit), 1)
        self.assertTrue(pr.tc[hit[0]] > tw and pr.tc[hit[0]] <= tf_prev, "the pair sits inside the guard")
        r = D.step_result(s, pr, 0.0)
        self.assertFalse(r["pull"], "the 0.6 s guard keeps the release out of L")
        unguarded = dict(s, L=[s["L"][0], tf_prev])
        self.assertTrue(D.step_result(unguarded, pr, 0.0)["pull"], "without the guard it would read as a pull")


# =====================================================================================
class Verdict(Tmp):
    """End to end on 24 steps in 4 blocks of 6, with a C1 file for the channel check."""

    @classmethod
    def setUpClass(cls):
        cls._ctd = tempfile.TemporaryDirectory()
        cls.c1_ok = channel_c1(os.path.join(cls._ctd.name, "c1_ok.csv"))
        cls.c1_none = C1Drive([60.0 + 60.0 * j for j in range(4)]).write(os.path.join(cls._ctd.name, "c1_no.csv"))

    @classmethod
    def tearDownClass(cls):
        cls._ctd.cleanup()

    def drive(self, n_blocks=4, per_block=6):
        return C2Drive(timeline(n_blocks, per_block))

    def run_drive(self, d, c1=None, name="c2.csv"):
        p = d.write(self.path(name))
        return run_all(self.tmp, [p], [c1 or self.c1_ok])

    def test_the_cuts_are_the_rule_numbers_for_the_realised_blocks(self):
        _, fz, res = self.run_drive(self.drive())
        self.assertEqual(fz["N"], 24)
        self.assertEqual(fz["blocks"], [6, 6, 6, 6])
        ky, kn, _, _ = RN.cuts([6, 6, 6, 6])
        self.assertEqual((fz["cuts"]["k_yes"], fz["cuts"]["k_no"]), (ky, kn))
        self.assertEqual((res["C2"]["k_yes"], res["C2"]["k_no"]), (ky, kn))
        self.assertGreaterEqual(fz["valid_shams"], 24)
        self.assertEqual(fz["late_pairs_median"], 4)

    def test_a_car_that_never_pulls(self):
        _, fz, res = self.run_drive(self.drive())
        c2 = res["C2"]
        self.assertEqual(c2["K"], 0)
        self.assertTrue(c2["channel"]["passes"])
        self.assertEqual(c2["verdict"], "does not")
        self.assertEqual(c2["remedy"], "a")
        self.assertEqual(c2["ci90"][0], 0.0)

    def test_early_pulls_alone_give_remedy_d(self):
        d = self.drive()
        for j in range(24):
            d.early(j)
        _, _, res = self.run_drive(d)
        c2 = res["C2"]
        self.assertEqual(c2["K"], 0)
        self.assertEqual(c2["K_early"], 24)
        self.assertEqual(c2["verdict"], "does not")
        self.assertEqual(c2["remedy"], "d")
        self.assertTrue(all(r["timing"] == "early only" for r in c2["steps"]))

    def test_a_car_that_always_pulls(self):
        d = self.drive()
        for j in range(24):
            d.late(j)
        _, _, res = self.run_drive(d)
        c2 = res["C2"]
        self.assertEqual(c2["K"], 24)
        self.assertLess(c2["shams"]["fisher_p"], 0.05)
        self.assertEqual(c2["verdict"], "pulls")
        self.assertEqual(c2["remedy"], "b", "below 2000 rpm no late reading is in the C1 band")
        self.assertEqual([b["pulls"] for b in c2["per_block"]], [6, 6, 6, 6])

    def test_a_borderline_car(self):
        d = self.drive()
        for j in (0, 7, 14, 21):
            d.late(j)
        _, _, res = self.run_drive(d)
        self.assertEqual(res["C2"]["K"], 4)
        self.assertEqual(res["C2"]["verdict"], "inconclusive")

    def test_the_sham_gate(self):
        d = self.drive()
        for j in range(24):
            d.late(j)
        # a 3 deg blip on one actual read in three, all through the cruise
        for x in np.arange(0.3, 3000.0, 2.7):
            d.ret.append((x - 0.01, x + 0.01, 3.0))
        _, fz, res = self.run_drive(d)
        c2 = res["C2"]
        self.assertGreaterEqual(c2["K"], c2["k_yes"])
        self.assertGreater(c2["shams"]["rate"], 0.9)
        self.assertGreater(c2["shams"]["fisher_p"], 0.05)
        self.assertEqual(c2["verdict"], "inconclusive (shams)")

    def test_the_channel_check(self):
        _, _, res = self.run_drive(self.drive(), c1=self.c1_none)
        c2 = res["C2"]
        self.assertEqual(c2["K"], 0)
        self.assertFalse(c2["channel"]["passes"])
        self.assertEqual(c2["verdict"], "inconclusive (channel)")

    def test_steps_excluded_for_the_baseline(self):
        d = self.drive()
        for j in (5, 11, 17, 23):
            d.pre(j)
        _, fz, res = self.run_drive(d)
        self.assertEqual(fz["N"], 20)
        self.assertEqual(fz["n_B"], 4)
        self.assertEqual(fz["blocks"], [5, 5, 5, 5])
        self.assertEqual(fz["blocks_with_B"], [6, 6, 6, 6])
        c2 = res["C2"]
        self.assertEqual(c2["K"], 0)
        self.assertLessEqual(c2["K"], c2["k_no"])
        self.assertGreater(c2["K"] + c2["n_B"], c2["k_no_with_B"])
        self.assertEqual(c2["verdict"], "inconclusive (baseline)")

    def test_unreadable_steps(self):
        d = self.drive()
        for j in range(7):
            d.late(j, deg=15.0)
        _, _, res = self.run_drive(d)
        self.assertEqual(res["C2"]["unreadable"], 7)
        self.assertEqual(res["C2"]["verdict"], "inconclusive (unreadable)")

    def test_refused_below_16_and_nothing_read(self):
        """Item 5: below 16 valid primary steps C2 is untested and stage C is not run, C1
        included; nothing is read beyond the pre-windows and the single run is not spent."""
        d = self.drive(n_blocks=2, per_block=5)
        p = d.write(self.path("small.csv"))
        sa, fz, out = freeze(self.tmp, [p], [self.c1_ok], "o")
        self.assertEqual(fz["N"], 10)
        self.assertFalse(fz["c2_testable"])
        boom = AssertionError("a response window was read")
        with unlocked(out), quiet(), mock.patch.object(D, "c2_analysis", side_effect=boom), \
                mock.patch.object(D, "c1_analysis", side_effect=boom):
            with self.assertRaises(SystemExit) as cm:
                D.stage_c(os.path.join(out, "frozen.json"), os.path.join(out, "frozen.sha256"))
        self.assertIn("16", str(cm.exception))
        self.assertFalse(os.path.exists(os.path.join(out, D.MARKER)))
        with contextlib.redirect_stderr(io.StringIO()):          # the first draft's flag is gone
            self.assertRaises(SystemExit, D.main, ["stage-c", "--frozen", "x", "--hash", "y", "--accept-c2-untested"])


# =====================================================================================
class Freeze(Tmp):
    def setUp(self):
        super().setUp()
        self.c2 = shutil.copy(c2_16(), self.path("c2.csv"))
        _, _, self.out = freeze(self.tmp, [self.c2], [], "o")
        self.fz, self.h = os.path.join(self.out, "frozen.json"), os.path.join(self.out, "frozen.sha256")

    def stage_c(self, committed=True, logs=None):
        with mock.patch.object(D, "committed", return_value=committed), \
                mock.patch.object(D, "RESULTS_ROOT", self.out), quiet():
            return D.stage_c(self.fz, self.h, logs)

    def test_the_hash_file_is_the_lists_sha256(self):
        with open(self.fz, "rb") as fh:
            self.assertEqual(D.read_hash(self.h), hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest())

    def test_a_changed_list_is_refused(self):
        with open(self.fz, encoding="utf-8") as fh:
            d = json.load(fh)
        d["N"] = 99
        with open(self.fz, "w", encoding="utf-8") as fh:
            json.dump(d, fh)
        with self.assertRaises(SystemExit) as cm:
            self.stage_c()
        self.assertIn("SHA-256", str(cm.exception))

    def test_a_wrong_hash_is_refused(self):
        with open(self.h, "w") as fh:
            fh.write("0" * 64 + "  frozen.json\n")
        with self.assertRaises(SystemExit):
            self.stage_c()

    def test_an_uncommitted_freeze_is_refused(self):
        with self.assertRaises(SystemExit) as cm:
            self.stage_c(committed=False)
        self.assertIn("committed", str(cm.exception))
        self.assertFalse(D.committed(self.fz), "a file outside the repository is never committed")

    def test_an_uncommitted_script_is_refused(self):
        """IC39: stages B and C run only on the committed script."""
        only_freeze = lambda p: not p.endswith(".py")                 # noqa: E731
        with mock.patch.object(D, "committed", side_effect=only_freeze), quiet():
            with self.assertRaises(SystemExit) as cm:
                D.stage_c(self.fz, self.h)
            self.assertIn("drive_c_analysis.py", str(cm.exception))
            with self.assertRaises(SystemExit) as cm:
                D.stage_b(self.out)
            self.assertIn("not committed", str(cm.exception))
        self.assertFalse(os.path.exists(os.path.join(self.out, D.MARKER)))

    def test_missing_files_are_refused_plainly(self):
        with self.assertRaises(SystemExit) as cm:
            with quiet(), unlocked():
                D.stage_c(self.path("none.json"), self.h)
        self.assertIn("does not exist", str(cm.exception))

    def test_changed_code_and_another_plant(self):
        with mock.patch.object(D, "code_sha", return_value="changed"), self.assertRaises(SystemExit) as cm:
            self.stage_c()
        self.assertIn("changed since the freeze", str(cm.exception))
        with mock.patch.object(D, "PLANT_SHA", "0000000000000000"), self.assertRaises(SystemExit):
            self.stage_c()
        with mock.patch.object(D, "DERIVED_SHA", "0000000000000000"), self.assertRaises(SystemExit):
            D.plant_check()
        with mock.patch.object(D, "code_sha", return_value="changed"), self.assertRaises(SystemExit) as cm:
            with quiet(), unlocked():
                D.stage_b(self.out)
        self.assertIn("since stage A", str(cm.exception))

    def test_a_changed_log_is_refused(self):
        with open(self.c2, "a") as fh:
            fh.write("9999.000,1,1,1,1,1,1\n")
        with self.assertRaises(SystemExit) as cm:
            self.stage_c()
        self.assertIn("SHA-256 differs", str(cm.exception))
        with self.assertRaises(SystemExit):
            with quiet(), unlocked():
                D.stage_b(self.out)
        self.assertFalse(os.path.exists(os.path.join(self.out, D.MARKER)))

    def test_a_moved_log_is_found_by_its_sha256(self):
        """IC38: the SHA-256 is the log's identity, the path only where to look."""
        moved = os.path.join(self.tmp, "moved")
        os.makedirs(moved)
        os.replace(self.c2, os.path.join(moved, "c2.csv"))
        with self.assertRaises(SystemExit) as cm:
            self.stage_c()
        self.assertIn("missing", str(cm.exception))
        other = os.path.join(self.tmp, "other")
        os.makedirs(other)
        with open(os.path.join(other, "c2.csv"), "w") as fh:
            fh.write("Time,x\n0,1\n")
        with self.assertRaises(SystemExit) as cm:
            self.stage_c(logs=other)
        self.assertIn("SHA-256 differs", str(cm.exception))
        res = self.stage_c(logs=moved)
        self.assertEqual(res["C2"]["verdict"], "inconclusive (channel)")


# =====================================================================================
class RunOnce(Tmp):
    """Guard 5: stage C runs once on every drive C file."""

    def setUp(self):
        super().setUp()
        self.c2 = shutil.copy(c2_16(), self.path("c2.csv"))
        _, _, self.out = freeze(self.tmp, [self.c2], [], "o")
        self.fz, self.h = os.path.join(self.out, "frozen.json"), os.path.join(self.out, "frozen.sha256")

    def go(self, fz=None, h=None):
        with unlocked(self.tmp), quiet():
            return D.stage_c(fz or self.fz, h or self.h)

    def test_twice_in_its_folder(self):
        self.go()
        with self.assertRaises(SystemExit) as cm:
            self.go()
        self.assertIn("runs once", str(cm.exception))
        with self.assertRaises(SystemExit) as cm:
            with quiet(), unlocked(self.tmp):
                D.stage_b(self.out)
        self.assertIn("already run", str(cm.exception))
        with self.assertRaises(SystemExit):
            with quiet():
                D.stage_a([self.c2], [], self.out)

    def test_from_a_copy_of_the_freeze(self):
        self.go()
        copy = self.path("copy")
        os.makedirs(copy)
        for n in ("frozen.json", "frozen.sha256"):
            shutil.copy(os.path.join(self.out, n), copy)
        with self.assertRaises(SystemExit) as cm:
            self.go(os.path.join(copy, "frozen.json"), os.path.join(copy, "frozen.sha256"))
        self.assertIn("already run on one of these logs", str(cm.exception))
        self.assertFalse(os.path.exists(os.path.join(copy, D.RESULT)))
        with quiet():                             # a new freeze of the same log is refused too
            D.stage_a([self.c2], [], self.path("again"))
        with self.assertRaises(SystemExit) as cm:
            with quiet(), unlocked(self.tmp):
                D.stage_b(self.path("again"))
        self.assertIn("already run on one of these logs", str(cm.exception))

    def test_a_run_that_died_is_not_run_again(self):
        with mock.patch.object(D, "c1_analysis", side_effect=RuntimeError("power cut")):
            with self.assertRaises(RuntimeError):
                self.go()
        self.assertTrue(os.path.exists(os.path.join(self.out, D.MARKER)))
        self.assertFalse(os.path.exists(os.path.join(self.out, D.RESULT)))
        with self.assertRaises(SystemExit) as cm:
            self.go()
        self.assertIn("runs once", str(cm.exception))

    def test_the_result_is_written_before_it_is_shown(self):
        res_path = os.path.join(self.out, D.RESULT)
        seen = []

        class Console(io.StringIO):
            encoding = "utf-8"

            def write(self, s):
                if "VERDICT" in s:
                    seen.append(os.path.exists(res_path))
                return super().write(s)
        with unlocked(self.tmp), contextlib.redirect_stdout(Console()):
            D.stage_c(self.fz, self.h)
        self.assertEqual(seen, [True])


# =====================================================================================
class Integrity(Tmp):
    """IC33: stages B and C recompute what they were handed and refuse a difference."""

    def setUp(self):
        super().setUp()
        self.c2 = shutil.copy(c2_16(), self.path("c2.csv"))

    def test_an_edited_stage_a_is_refused(self):
        out = self.path("o")
        with quiet():
            D.stage_a([self.c2], [], out)
        sa_path = os.path.join(out, "stage_a.json")
        with open(sa_path, encoding="utf-8") as fh:
            sa = json.load(fh)
        sa["steps"][3]["stage_a_valid"] = sa["steps"][3]["stage_a_valid_primary"] = False
        with open(sa_path, "w", encoding="utf-8") as fh:
            json.dump(sa, fh)
        with self.assertRaises(SystemExit) as cm:
            with quiet(), unlocked():
                D.stage_b(out)
        self.assertIn("stage_a.json is not what this code computes", str(cm.exception))

    def test_an_edited_freeze_with_a_new_hash_is_refused(self):
        _, _, out = freeze(self.tmp, [self.c2], [], "o")
        fz_path = os.path.join(out, "frozen.json")
        with open(fz_path, encoding="utf-8") as fh:
            fz = json.load(fh)
        fz["steps"][2]["valid_primary"] = False
        raw = (json.dumps(fz, indent=1, sort_keys=True) + "\n").encode("utf-8")
        with open(fz_path, "wb") as fh:
            fh.write(raw)
        with open(os.path.join(out, "frozen.sha256"), "w") as fh:
            fh.write(hashlib.sha256(raw).hexdigest() + "  frozen.json\n")
        with self.assertRaises(SystemExit) as cm:
            with quiet(), unlocked(self.tmp), mock.patch.object(D, "c2_analysis",
                                                                 side_effect=AssertionError("read")):
                D.stage_c(fz_path, os.path.join(out, "frozen.sha256"))
        self.assertIn("not what this code computes", str(cm.exception))
        self.assertFalse(os.path.exists(os.path.join(out, D.MARKER)))


# =====================================================================================
class Files(Tmp):
    def test_guard_1_refuses_a_log_with_the_angles_in_logs_raw(self):
        raw = self.path("raw")
        os.makedirs(raw)
        p = C2Drive([90.0]).write(os.path.join(raw, "c2.csv"))
        with mock.patch.object(D, "RAW_DIR", raw), quiet():
            with self.assertRaises(SystemExit) as cm:
                D.stage_a([p], [], self.path("o"))
            self.assertIn("Guard 1", str(cm.exception))
            order = [c for c in ORDER if "ignition" not in c]     # drive B's kind: no angle logged
            q = C2Drive([90.0], order=order).write(os.path.join(raw, "b.csv"))
            sa = D.stage_a([q], [], self.path("o2"))
        self.assertFalse(sa["files"][0]["v8"]["ok"])

    def test_one_log_under_two_names_is_refused(self):
        p = C2Drive([90.0]).write(self.path("a.csv"))
        q = shutil.copy(p, self.path("b.csv"))
        with self.assertRaises(SystemExit) as cm:
            with quiet():
                D.stage_a([p], [q], self.path("o"))
        self.assertIn("identical SHA-256", str(cm.exception))

    def test_a_path_inside_the_repository_is_recorded_relative(self):
        self.assertEqual(D.recorded_path(os.path.join(D.HERE, "logs", "driveC", "c2.csv")), "logs/driveC/c2.csv")
        self.assertTrue(os.path.isabs(D.recorded_path(self.path("c2.csv"))))

    def test_a_trailing_comma_reads_the_same(self):
        p = C2Drive(timeline(1, 2)).write(self.path("a.csv"))
        with open(p, encoding="utf-8") as fh:
            rows = fh.read().splitlines()
        q = self.path("b.csv")
        with open(q, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join([rows[0]] + [r + "," for r in rows[1:]]) + "\n")
        with quiet():
            sa = D.stage_a([p], [], self.path("oa"))
            sb = D.stage_a([q], [], self.path("ob"))
        strip = lambda x: [{k: v for k, v in s.items() if k != "file"} for s in x]    # noqa: E731
        self.assertEqual(strip(D.canon(sa)["steps"]), strip(D.canon(sb)["steps"]))
        lf = D.LogFile(q, "C2")
        text = D.load_ignition_text(lf)
        self.assertEqual(text["act"][-1], rows[-1].split(",")[3])

    def test_another_separator_or_encoding_is_refused_plainly(self):
        p = self.path("semi.csv")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("Time;" + ";".join(ORDER) + "\n0;0;0;0;0;0;0\n")
        with self.assertRaises(SystemExit) as cm:
            D.LogFile(p, "C2")
        self.assertIn("';'", str(cm.exception))
        q = self.path("latin.csv")
        with open(q, "wb") as fh:
            fh.write(b"Time,\"Coolant temperature \xb0C\"\n0,0\n")
        with self.assertRaises(SystemExit) as cm:
            D.LogFile(q, "C2")
        self.assertIn("UTF-8", str(cm.exception))

    def test_a_console_that_cannot_print_a_name(self):
        buf = io.BytesIO()
        out = io.TextIOWrapper(buf, encoding="cp1252", errors="strict")
        with contextlib.redirect_stdout(out):
            D.say([], "مين معي.csv")
        out.flush()
        self.assertIn(b"\\u0645", buf.getvalue())


# =====================================================================================
def seg_pairs(times, retard, target=20.0):
    ta = np.asarray(times, float)
    tgt = np.full(len(ta), target)
    return D.Pairs(ta - 0.3, ta, ta + 0.3, tgt, tgt - np.asarray(retard, float))


class KneeScan(unittest.TestCase):
    """Item 7 on one segment of hand-built pairs, one a second, the KI rising 0.02 a second
    from 0.60 (review, statistics: check5)."""
    g = dict(id="G1", s0=0.0)
    times = np.arange(0.0, 30.0, 1.0)

    def run_seg(self, ret, ki=None):
        kiv = 0.60 + 0.02 * self.times
        p = seg_pairs(self.times, ret)
        rpm = np.full(len(self.times), 2700.0)
        onsets = []
        row = D.knee_segment(self.g, p, rpm, ki or (lambda i: float(kiv[i])), np.flatnonzero(rpm <= 3300), onsets)
        return row, onsets, kiv

    def test_a_clean_onset(self):
        ret = np.where(self.times >= 12, 3.0, 0.0)
        row, onsets, kiv = self.run_seg(ret)
        self.assertEqual(row["cls"], "onset")
        self.assertAlmostEqual(row["interval"][0], kiv[11])
        self.assertAlmostEqual(row["interval"][1], kiv[12])
        self.assertTrue(onsets[0]["confirmed"] and onsets[0]["persists"])

    def test_the_first_candidate_ends_the_scan(self):
        """F4: 'the first pair ... with retard >= B_seg + 2.25' is the onset; unconfirmed, the
        segment has no confirmed onset, and a later candidate (here at 20 s, behind a quiet
        window again) is not taken instead: the code confirmed it and counted it toward the 8."""
        ret = np.zeros(len(self.times))
        ret[8] = 2.25
        ret[20:] = 3.0
        row, onsets, kiv = self.run_seg(ret)
        self.assertEqual(len(onsets), 1)
        self.assertFalse(onsets[0]["confirmed"])
        self.assertEqual(row["cls"], "no confirmed onset")
        self.assertEqual(row["interval"], (kiv[7], float("inf")), "quiet pairs before the candidate only")
        self.assertEqual(D.confirmed_onsets(onsets), [])

    def test_a_retard_in_two_counts(self):
        """B4: 1.5 deg, then 3 deg held: no quiet window is left for the 3 deg pair, and the
        segment must not read as quiet up to its highest KI."""
        ret = np.zeros(len(self.times))
        ret[14] = 1.5
        ret[15:] = 3.0
        row, onsets, kiv = self.run_seg(ret)
        self.assertEqual(row["cls"], "retarded without a quiet baseline")
        self.assertEqual(row["interval"], (float("-inf"), kiv[15]))
        self.assertEqual(onsets, [], "not an onset: it counts toward neither the 8 nor the channel check")

    def test_a_gradual_rise_that_recovers(self):
        """S1 (check5 case 2): knock at KI 0.80-0.82, gone again while the KI keeps rising; the
        code read (1.18, inf) here."""
        ret = np.zeros(len(self.times))
        ret[10] = 1.5
        ret[11:15] = 3.0
        row, _, kiv = self.run_seg(ret)
        self.assertLessEqual(kiv[11], row["interval"][1])
        self.assertTrue(row["interval"][0] < 0.81 <= row["interval"][1], row)

    def test_the_bound_stops_at_the_first_pull_reading(self):
        """S1: an unconfirmed pull (one cylinder in six) and quiet readings after it: the
        right-censored bound is the last quiet KI before it."""
        ret = np.zeros(len(self.times))
        ret[12] = 3.0
        ret[20] = 3.0
        row, _, kiv = self.run_seg(ret)
        self.assertEqual(row["cls"], "no confirmed onset")
        self.assertEqual(row["interval"], (kiv[11], float("inf")))

    def test_an_early_pull_bounds_the_segment_too(self):
        """S1, the first 5 s: an unconfirmed pull before any onset can be read still ends what the
        later quiet readings can claim (the code read (1.18, inf) here)."""
        ret = np.zeros(len(self.times))
        ret[2] = 3.0
        row, _, kiv = self.run_seg(ret)
        self.assertEqual(row["cls"], "no onset")
        self.assertEqual(row["interval"], (kiv[1], float("inf")))

    def test_retarded_from_its_first_pairs(self):
        ret = np.zeros(len(self.times))
        ret[1:4] = 3.0
        row, _, kiv = self.run_seg(ret)
        self.assertEqual(row["cls"], "retarded from its first pairs")
        self.assertEqual(row["interval"], (float("-inf"), kiv[1]))

    def test_a_ki_that_cannot_be_computed(self):
        """S3 / F13: a NaN K* gives no interval, and the onset counts toward neither the 8 nor
        the channel check."""
        ret = np.where(self.times >= 12, 3.0, 0.0)
        kiv = 0.60 + 0.02 * self.times
        row, onsets, _ = self.run_seg(ret, ki=lambda i: float("nan") if i == 12 else float(kiv[i]))
        self.assertIsNone(row["interval"])
        self.assertTrue(onsets[0]["confirmed"])
        self.assertEqual(D.confirmed_onsets(onsets), [])


# =====================================================================================
class Knee(unittest.TestCase):
    def test_turnbull_recovers_a_known_median(self):
        rng = np.random.default_rng(7)
        true = rng.normal(0.80, 0.06, 400)
        iv = []
        for k in true:
            x = np.sort(rng.uniform(0.55, 1.05, 6))          # the KIs one segment visits
            above = np.flatnonzero(x >= k)
            if len(above) == 0:
                iv.append((x[-1], float("inf")))
            elif above[0] == 0:
                iv.append((float("-inf"), x[0]))
            else:
                iv.append((x[above[0] - 1], x[above[0]]))
        m = D.turnbull_median(iv)
        self.assertTrue(m["identified"])
        self.assertAlmostEqual(m["point"], 0.80, delta=0.02)
        self.assertLessEqual(m["lo"], m["point"])
        self.assertLessEqual(m["point"], m["hi"])

    def test_unidentified_medians(self):
        # most segments never retard below 0.9, and every onset is under 0.7
        m = D.turnbull_median([(0.9, float("inf"))] * 5 + [(0.5, 0.7)] * 2)
        self.assertFalse(m["identified"])
        self.assertIn("onset above 0.900", m["reason"])
        m = D.turnbull_median([(float("-inf"), 0.5)] * 5 + [(0.6, 0.9)] * 2)
        self.assertFalse(m["identified"])
        self.assertIn("onset below 0.500", m["reason"])
        # a censored segment whose bound lies under an onset puts its mass there: identified
        m = D.turnbull_median([(0.6, float("inf"))] * 5 + [(0.5, 0.7)] * 2)
        self.assertTrue(m["identified"])
        self.assertEqual((m["lo"], m["hi"]), (0.6, 0.7))

    def test_a_flat_at_one_half(self):
        """IC28: F = 1/2 across a gap. The median set is both innermost intervals and the gap; next
        to an open interval it is not identified."""
        m = D.turnbull_median([(0.60, 0.70)] * 2 + [(0.80, 0.90)] * 2)
        self.assertEqual((m["lo"], m["hi"], m["point"]), (0.60, 0.90, 0.75))
        self.assertTrue(m["identified"])
        m = D.turnbull_median([(0.5, 0.7)] * 2 + [(0.9, float("inf"))] * 2)
        self.assertFalse(m["identified"], "half the segments are known only to be quiet above 0.9")
        self.assertEqual(m["point"], 0.8)

    def test_a_flat_the_em_only_approaches(self):
        """S2 (review, statistics: check4): the EM leaves F at 0.500000426 where the NPMLE has
        exactly 1/2; read as a crossing inside (0.742, 0.745] the median retuned the knee to
        0.74, while the true median set [0.745, 0.753] does not."""
        inf = float("inf")
        iv = [(0.753, 0.852), (-inf, 0.64), (0.741, 0.808), (0.561, 0.634), (0.634, 0.779), (0.686, 0.73),
              (0.666, 0.831), (0.684, 0.715), (0.732, 0.852), (0.633, 0.778), (0.737, 0.856), (0.528, 0.608),
              (0.586, 0.681), (0.535, 0.745), (0.724, 0.765), (0.572, 0.658), (0.808, 0.952), (0.531, 0.759),
              (0.742, 0.786)]
        _, s = D.turnbull(iv)
        self.assertGreater(abs(np.cumsum(s)[6] - 0.5), 1e-9, "the EM's F is not exactly one half")
        m = D.turnbull_median(iv)
        self.assertLessEqual(m["lo"], 0.745)
        self.assertGreaterEqual(m["hi"], 0.753)
        ok = dict(limited=False, why="")
        for h in (0.03, 0.05, 0.07):
            self.assertFalse(D.knee_decision(m, 10, h, ok)["retune"])

    def test_bootstrap_is_seeded_and_infinite_when_unidentified(self):
        iv = [(0.6 + 0.01 * j, 0.62 + 0.01 * j) for j in range(10)]
        a, b = D.boot_median(iv, n=300), D.boot_median(iv, n=300)
        self.assertEqual(a, b)
        self.assertTrue(np.isfinite(a["h"]))
        c = D.boot_median([(0.9, float("inf"))] * 3 + [(0.5, 0.7)] * 3, n=300)
        self.assertEqual(c["h"], float("inf"))

    def test_the_retune_logic(self):
        ok = dict(limited=False, why="")
        med = dict(identified=True, point=0.65, lo=0.64, hi=0.66, reason="")
        d = D.knee_decision(med, 10, 0.02, ok)
        self.assertTrue(d["retune"])
        self.assertEqual(d["new_knee"], 0.65)
        self.assertAlmostEqual(d["two_u_val"], math.sqrt(0.02 ** 2 + 0.064 ** 2))
        self.assertTrue(d["ecu_threshold_off"])
        self.assertFalse(D.knee_decision(dict(med, point=0.80, lo=0.79, hi=0.81), 10, 0.02, ok)["retune"])
        self.assertFalse(D.knee_decision(dict(med, lo=0.60, hi=0.78), 10, 0.02, ok)["retune"],
                         "the whole median interval must be beyond the threshold")
        self.assertFalse(D.knee_decision(med, 10, 0.25, ok)["retune"], "2 u_val 0.26 > 0.20")
        self.assertEqual(D.knee_decision(med, 7, 0.02, ok)["status"], "untested")
        self.assertEqual(D.knee_decision(dict(med, identified=False, reason="onset above 0.9"), 10, 0.02, ok)["status"],
                         "untested")
        self.assertEqual(D.knee_decision(med, 10, 0.02, dict(limited=True, why="halves"))["status"], "limited")
        self.assertEqual(D.knee_decision(med, 10, float("inf"), ok)["status"], "no retune")


def fake_ki(rpm, map_kpa, amb, cool, spark):
    """A knock integral linear in spark: 0.85 at 9 deg, 0.65 at 5 deg."""
    return 0.40 + 0.05 * spark


class KneeEndToEnd(Tmp):
    """C1 segments with a target ramp; the car retards 3 deg once the pair's own KI (at its
    target) reaches the segment's true knee, and stays retarded."""

    def make(self, knees, rpms, theta0s):
        starts = [60.0 + 60.0 * j for j in range(len(knees))]
        air = [{2450: 383.8, 2900: 462.4, 2700: 427.4}[r] for r in rpms]
        d = C1Drive(starts, rpm=rpms, air_seg=air)
        ramp = lambda j, t: theta0s[j] + 0.75 * math.floor((t - d.starts[j]) / 2.7)      # noqa: E731
        d.target_fn = ramp
        on = {}

        def retard(t):
            j = d.seg(t)
            if j is None:
                return 0.0
            tb, tc = round(t - 0.75, 3), round(t + 0.15, 3)
            if not (d.seg(tb) == j and d.seg(tc) == j):
                return 3.0 if on.get(j) else 0.0
            if fake_ki(0, 0, 0, 0, min(ramp(j, tb), ramp(j, tc))) >= knees[j] or on.get(j):
                on[j] = True
                return 3.0
            return 0.0
        d.retard_fn = retard
        return d

    def analyse(self, d):
        p = d.write(self.path("c1.csv"))
        with mock.patch.object(D, "knock_integral", side_effect=fake_ki):
            _, _, res = run_all(self.tmp, [c2_16()], [p])
        return res["C1_knee"]

    def test_a_low_knee_is_found_and_retunes(self):
        n = 12
        th = [-1.5, -0.75, 0.0, 0.75, 1.5, 2.25] * 2
        k = self.analyse(self.make([0.65] * n, [2450] * 6 + [2900] * 6, th))
        self.assertGreaterEqual(k["confirmed"], 8)
        self.assertAlmostEqual(k["median"]["point"], 0.65, delta=0.04)
        self.assertFalse(k["halves"]["limited"], k["halves"]["why"])
        self.assertEqual(k["decision"]["status"], "retune")
        self.assertAlmostEqual(k["decision"]["new_knee"], 0.65, delta=0.04)

    def test_a_knee_at_085_does_not_retune(self):
        th = [2.25, 3.0, 3.75, 4.5, 5.25, 6.0] * 2
        k = self.analyse(self.make([0.85] * 12, [2450] * 6 + [2900] * 6, th))
        self.assertAlmostEqual(k["median"]["point"], 0.85, delta=0.04)
        self.assertEqual(k["decision"]["status"], "no retune")

    def test_the_speed_halves_disagreeing_is_limited(self):
        th = [-1.5, -0.75, 0.0, 0.75, 1.5, 2.25] + [2.25, 3.0, 3.75, 4.5, 5.25, 6.0]
        k = self.analyse(self.make([0.65] * 6 + [0.85] * 6, [2450] * 6 + [2900] * 6, th))
        self.assertTrue(k["halves"]["limited"])
        self.assertEqual(k["decision"]["status"], "limited")

    def test_the_logistic_secondary_uses_every_pair(self):
        """F10: 'over all pairs' -- at 3400 rpm no onset can be read (3300 rpm and below), yet
        every pair enters the secondary fit."""
        d = C1Drive([60.0 + 60.0 * j for j in range(4)], rpm=3400.0, air_seg=540.0)
        p = d.write(self.path("c1.csv"))
        with mock.patch.object(D, "knock_integral", side_effect=fake_ki):
            _, fz, res = run_all(self.tmp, [c2_16()], [p])
        k = res["C1_knee"]
        self.assertGreater(sum(1 for g in fz["segments"] if g["counting"]), 0)
        self.assertGreater(k["logistic"]["n"], 0)
        self.assertEqual(k["confirmed"], 0)


# =====================================================================================
class Stats(unittest.TestCase):
    def test_holm_keeps_its_family(self):
        """S4: a secondary that cannot be computed is still one of the two."""
        h = D.holm({"size": 0.04, "ambient": None})
        self.assertEqual(h["size"]["threshold"], 0.025)
        self.assertFalse(h["size"]["significant"])
        self.assertFalse(h["ambient"]["significant"])
        h = D.holm({"size": 0.02, "ambient": 0.04})
        self.assertTrue(h["size"]["significant"] and h["ambient"]["significant"])

    def test_blocks_break_over_every_stage_a_valid_step(self):
        """S5: a side-set step driven between two primary steps is driving: no 5-minute break."""
        mk = lambda i, t0: dict(id=i, file=0, t0=t0, tau_f=t0 + 8.0, tau_f_prev=t0 + 7.0)     # noqa: E731
        prim = [mk("S1", 0.0), mk("S3", 400.0)]
        side = [mk("S2", 200.0)]
        self.assertEqual(D.blocks_of(prim)[1], [1, 1])
        of, sizes = D.blocks_of(prim + side, ["S1", "S3"])
        self.assertEqual(sizes, [2])
        self.assertEqual(of, {"S1": 0, "S3": 0})
        self.assertGreaterEqual(D.cut_pair([2])["k_yes"], D.cut_pair([1, 1])["k_yes"])

    def test_the_cuts_use_the_rules_design_values(self):
        """S6: the cut is computed with item 4's numbers, and drive_c_rule_numbers.py must hold them."""
        self.assertEqual(D.cut_pair([7, 7, 7])["k_yes"], RN.cuts([7, 7, 7], q=0.075, m=0.45, icc=0.10, alpha=0.05)[0])
        with mock.patch.object(RN, "Q_DESIGN", 0.10), self.assertRaises(AssertionError):
            D.cut_pair([7, 7, 7])

    def test_visibility_counts_the_pairs_that_exist(self):
        """S7: an onset two pairs from the segment's end has two chances to show, not three."""
        conf = [dict(visible_next3=2, n_next3=2), dict(visible_next3=1, n_next3=3)]
        self.assertAlmostEqual(D.visibility(conf), 3 / 5)
        self.assertIsNone(D.visibility([]))

    def test_one_sessions_variance_has_the_grids_floor(self):
        """S7 / IC30: identical segment values do not give u_D = 0."""
        self.assertAlmostEqual(D.pooled_u([-3.0] * 16), math.sqrt(0.75 ** 2 / 12 / 16))
        self.assertAlmostEqual(D.pooled_u([-3.0, -1.0] * 8), float(np.std([-3.0, -1.0] * 8, ddof=1) / 4))
        self.assertEqual(D.pooled_u([-3.0]), float("inf"))


# =====================================================================================
class Spark(Tmp):
    def test_the_action_rule_and_the_label(self):
        d = D.spark_decision(-3.0, 0.2, 0.1, 20)
        self.assertTrue(d["retune"])
        self.assertEqual(d["offset"], -3.0)
        self.assertAlmostEqual(d["u_input"], math.sqrt(0.1 ** 2 + 0.86 ** 2))
        self.assertEqual(d["label"], "off")
        d = D.spark_decision(-1.5, 0.2, 0.1, 20)
        self.assertFalse(d["retune"], "2 u_val is about 1.76: a retune needs |E| above it")
        self.assertEqual(d["label"], "untested")
        self.assertEqual(D.spark_decision(-3.0, 0.2, 0.1, 14)["status"], "untested")
        self.assertEqual(D.spark_decision(-3.0, 0.2, 0.1, 20, dry_ok=False)["status"], "untested")
        self.assertFalse(D.spark_decision(-3.0, 0.2, 0.1, 20, e_pooled=-0.5)["retune"])
        self.assertEqual(D.plan_label(0.1, 0.5, 0.85), "validated")
        self.assertEqual(D.plan_label(0.6, 0.5, 0.85), "limited")
        self.assertEqual(D.plan_label(2.0, 1.0, 0.85), "off")
        self.assertEqual(D.plan_label(1.0, 1.0, 0.85), "untested")

    def drive(self, e_true, n=16, start=60.0):
        starts = [start + 60.0 * j for j in range(n)]
        d = C1Drive(starts)
        d.target_fn = lambda j, t: 20.25
        model = D.model_spark(2700.0, D.inv_map(427.4, 2700.0, 25.0, 90.0), 25.0, 90.0)
        q = round((model + e_true) / 0.75) * 0.75
        d.retard_fn = lambda t: (20.25 - q) if d.seg(t) is not None else 0.0
        return d, q - model

    def test_end_to_end_one_session(self):
        for e_true, status, label in ((-3.0, "retune", "off"), (-1.0, "no retune", "untested")):
            d, e_q = self.drive(e_true)
            p = d.write(self.path(f"c1_{e_true}.csv"))
            with mock.patch.object(D, "knock_integral", side_effect=fake_ki):
                _, _, res = run_all(self.tmp, [c2_16()], [p], name=f"o{e_true}")
            s = res["C1_spark"]
            self.assertEqual(s["cell"], "primary")
            self.assertEqual(s["n_segments"], 16)
            self.assertAlmostEqual(s["E"], e_q, delta=0.15)
            self.assertEqual(s["decision"]["status"], status)
            self.assertEqual(s["decision"]["label"], label)
            self.assertTrue(res["dry_run"]["ok"])

    def test_two_sessions_use_random_effects(self):
        d1, e_q = self.drive(-3.0, n=8)
        d2, _ = self.drive(-3.0, n=8, start=90.0)
        p1, p2 = d1.write(self.path("s1.csv")), d2.write(self.path("s2.csv"))
        with mock.patch.object(D, "knock_integral", side_effect=fake_ki):
            _, _, res = run_all(self.tmp, [c2_16()], [p1, p2])
        s = res["C1_spark"]
        self.assertIn("random_effects", s)
        self.assertEqual(len(s["random_effects"]["sessions"]), 2)
        self.assertAlmostEqual(s["E"], e_q, delta=0.15)
        self.assertEqual(s["decision"]["status"], "retune")

    def test_too_few_segments_is_untested(self):
        d, _ = self.drive(-3.0, n=10)
        p = d.write(self.path("few.csv"))
        with mock.patch.object(D, "knock_integral", side_effect=fake_ki):
            sa, fz, res = run_all(self.tmp, [c2_16()], [p])
        self.assertEqual(sa["cell"], "fallback", "fewer than 15 primary counting segments")
        self.assertEqual(res["C1_spark"]["decision"]["status"], "untested")


# =====================================================================================
class DryRun(unittest.TestCase):
    def test_the_legacy_numbers(self):
        if not os.path.exists(D.LEGACY_JSON):
            self.skipTest("results/car_spark_boost.json is not in this checkout")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r = D.dry_run_spark()
        self.assertTrue(r["ok"], r)
        self.assertEqual((r["median"], r["se"], r["cell_median"]), (-3.81, 2.07, -1.78))
        self.assertIn("-3.81 / 2.07", buf.getvalue())
        self.assertIn("-1.78", buf.getvalue())
        self.assertLess(r["max_model_vs_committed"], 0.01, "the same schedule as car_spark_boost.model_spark")


if __name__ == "__main__":
    unittest.main(verbosity=2)

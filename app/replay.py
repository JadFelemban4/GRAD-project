"""Read-only, in-memory replay datasets for the 3D lab.

Original CSV timestamps drive Estimator, once per sample, at speed=0. Browser
playback never enters this module. No raw data, frames or alerts are persisted.
This adapter exposes the existing physics; road geometry has no input here.
"""
from __future__ import annotations

from collections import OrderedDict
import csv
import hashlib
import math
from pathlib import Path
import statistics
import subprocess
import threading

from app.estimator import Estimator, MAX_SUBSTEP_S, GAP_RESEED_S
from app.reader import ReplayReader, _f
from engine_env import Vehicle, PREVIEW_S

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / 'logs' / 'raw'
# These are classification guards, NOT gearbox parameters or tuning of physics.
# 4% is the documented ratio-agreement band (CLAUDE mistake 18). Below 15 km/h,
# converter slip and speed quantization make ratio inference unreliable.
RATIO_TOLERANCE = .04
INFERENCE_MIN_KMH = 15.0


def finite(value):
    return float(value) if isinstance(value, (int, float)) and math.isfinite(value) else None


def vehicle_metadata():
    return dict(name='ZF 8HP51', gears=list(Vehicle.gears), final_drive=Vehicle.final_drive,
                wheel_radius_m=Vehicle.wheel_r, converter='assumed_locked',
                upshift_min_rpm=Vehicle.UPSHIFT_MIN_RPM, shift_load=Vehicle.SHIFT_LOAD,
                peak_torque_nm=Vehicle.PEAK_TORQUE_NM, shift_rpm_max=Vehicle.SHIFT_RPM_MAX,
                inference_tolerance=RATIO_TOLERANCE, inference_min_kmh=INFERENCE_MIN_KMH)


def infer_gear(rpm, speed_kmh, recorded=None, internal=None):
    """Prefer a credible recorded gear; retain raw even when its channel clips.

    Return no inferred gear if locked-converter kinematics do not match. These
    are sampled observations, not an implementation of Vehicle.gear_for's shift
    schedule. Never use that schedule to replace an actual drive's speed/RPM.

    `internal` IS ACCEPTED AND DELIBERATELY IGNORED. `Internal gear (including
    neutral and reverse)` was briefly trusted to corroborate a ratio-inferred
    gear and promote it from `estimated` to `recorded`. Measured 21 September:
    on `fb988991` it reads 8.0 on all 3259 populated rows and 0.0 on the other
    193 -- including 233 rows at standstill -- and on `f51686d7` it is 0.0
    throughout. It is a constant, not a gear. Trusting it labelled an INFERRED
    eighth gear as a MEASURED one on 62 % of that drive, on a car whose gear
    channel saturates at 6 (mistake 18), so an eighth gear can never be a
    recorded value here. Fifth channel on this car that is not what its name
    says. The argument is kept with the parameter so nobody re-adds the branch.
    """
    rpm, speed = finite(rpm), finite(speed_kmh)
    raw = finite(recorded)
    out = dict(gear=None, gear_source='unavailable', gear_raw=raw,
               gear_note='insufficient_data', ratio_error=None)
    if rpm is None or speed is None or rpm < 400 or speed <= 0:
        return out
    if speed < INFERENCE_MIN_KMH:
        # 7 at standstill in this logger is not a validated seventh forward gear.
        if raw in (1, 2, 3, 4, 5):
            out.update(gear=int(raw), gear_source='recorded', gear_note='low_speed_recording')
        else:
            out['gear_note'] = 'low_speed_or_slip'
        return out
    actual_ratio = rpm * 2 * math.pi * Vehicle.wheel_r / (60 * (speed / 3.6))
    errors = [abs(actual_ratio / (r * Vehicle.final_drive) - 1) for r in Vehicle.gears]
    best = min(range(len(errors)), key=errors.__getitem__)
    out['ratio_error'] = errors[best]
    if errors[best] > RATIO_TOLERANCE:
        out['gear_note'] = 'ratio_mismatch_or_slip'
        return out
    gear = best + 1
    if raw == gear and 1 <= raw <= 6:
        out.update(gear=gear, gear_source='recorded', gear_note='recorded_ratio_checked')
    else:
        out.update(gear=gear, gear_source='estimated',
                   gear_note='clipped_channel' if raw == 6 and gear > 6 else 'rpm_speed_ratio')
    return out


def resolve_trip(trip_id):
    # Match against actual filenames, never resolve user-supplied filesystem paths.
    for p in LOGS.glob('*.csv'):
        if trip_id == p.stem and p.resolve().parent == LOGS.resolve():
            return p
    raise KeyError(trip_id)


_CATALOG = {}


def trip_catalog():
    """Cached against the directory's own state, not for the process lifetime.

    `lru_cache` meant a drive copied into logs/raw while the server was running
    never appeared, and CLAUDE.md's "when a new drive CSV arrives" routine
    starts with exactly that copy. Keyed on each file's name, size and mtime,
    so a new or re-exported log invalidates it and nothing else re-reads.
    """
    try:
        key = tuple(sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns)
                           for p in LOGS.glob('*.csv')))
    except OSError:
        key = None
    if key is not None and _CATALOG.get('key') == key:
        return _CATALOG['value']
    trips = []
    for p in sorted(LOGS.glob('*.csv')):
        if p.resolve().parent != LOGS.resolve():
            continue
        count, first, last, moves = 0, None, None, False
        with p.open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            fields = reader.fieldnames or []
            for row in reader:
                t = finite(_f(row, 'Time'))
                if t is None or (last is not None and t < last):
                    continue
                if first is None:
                    first = t
                last = t
                count += 1
                v = finite(_f(row, 'Vehicle speed'))
                if v is not None and v > 0:
                    moves = True
        # has_speed is a HEADER fact and has_motion is a DATA fact. 3f64372e
        # carries the column and reads 0.0 on all of it, so a header check alone
        # promises a moving car and delivers a parked one.
        trips.append(dict(id=p.stem, name=p.name, rows=count,
                          duration_s=(last - first) if first is not None else 0,
                          has_speed='Vehicle speed' in fields,
                          has_motion=moves,
                          has_gear='Actual gear' in fields,
                          has_coolant='Coolant temperature' in fields,
                          has_oil='Oil temperature' in fields))
    if key is not None:
        _CATALOG.update(key=key, value=trips)
    return trips


def fingerprint(path):
    code = {}
    for name in ('plant.py', 'thermal.py', 'engine_env.py', 'app/estimator.py', 'app/reader.py', 'app/replay.py'):
        code[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                                         stderr=subprocess.DEVNULL, timeout=3).decode().strip()
    except (OSError, subprocess.SubprocessError):
        commit = None
    return dict(git_commit=commit, code_sha256=code,
                source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                vehicle=vehicle_metadata(), preview_s=list(PREVIEW_S),
                integration=dict(timestamps='original_csv', max_substep_s=MAX_SUBSTEP_S,
                                 reseed_gap_s=GAP_RESEED_S))


def _raw_rows(reader):
    """Mirror only Reader's timestamp filtering to associate auxiliary channels."""
    first, last = None, None
    for row in reader.rows:
        t = _f(row, 'Time')
        if t is None or (last is not None and t < last):
            continue
        if first is None:
            first = t
        last = t
        yield t - first, row


def build_replay(path, progress=None):
    path = Path(path)
    reader = ReplayReader(str(path), speed=0)
    estimator = Estimator()
    raw_rows = list(_raw_rows(reader))
    times = [t for t, _ in raw_rows if finite(t) is not None]
    intervals = [b - a for a, b in zip(times, times[1:]) if b > a]
    # Four median sample intervals is the dataset's documented logger-gap rule.
    gap_limit = 4 * statistics.median(intervals) if intervals else 1.0
    frames, events = [], []
    distance, distance_partial = 0.0, False
    previous = None
    previous_gear = None
    for i, (sample, (t, raw)) in enumerate(zip(reader, raw_rows)):
        if finite(t) is None:
            continue
        st = estimator.update(sample)
        speed, rpm = finite(sample.v_kmh), finite(sample.rpm)
        dt = sample.t - previous['t'] if previous else 0.0
        gap = previous is not None and dt > gap_limit
        valid_segment = previous is not None and not gap and speed is not None and previous['speed_kmh'] is not None
        if valid_segment:
            distance += .5 * (speed + previous['speed_kmh']) / 3.6 * dt
        elif previous:
            distance_partial = True
        gear = infer_gear(rpm, speed, _f(raw, 'Actual gear'),
                          _f(raw, 'Internal gear (including neutral and reverse)'))
        oil_measured = finite(sample.oil_c)
        oil_est = finite(st.t_oil_est_c)
        frame = dict(t=sample.t, s_m=distance if speed is not None else None,
                     distance_partial=distance_partial, speed_kmh=speed, rpm=rpm,
                     **gear, grade_pct=None, coolant_c=finite(sample.ect_c),
                     oil_c=oil_measured if oil_measured is not None else oil_est,
                     oil_source='recorded' if oil_measured is not None else ('estimated' if oil_est is not None else 'unavailable'),
                     turbine_c=finite(st.t_turb_c), turbine_lo_c=finite(st.t_turb_lo_c),
                     turbine_hi_c=finite(st.t_turb_hi_c), block_c=finite(st.t_block_c),
                     fuel_gps=finite(st.fuel_gps), torque_nm=finite(st.torque_nm),
                     map_kpa=finite(st.map_kpa), ambient_c=finite(sample.t_amb_c),
                     modelled=list(st.modelled), ok=st.ok, gap=gap,
                     warming_up=st.warming_up, seed_band_k=finite(st.seed_band_k),
                     # Denominator of this project's central ratio H/tau. Already
                     # computed by Estimator; exposed, never recomputed here. It
                     # moves with exhaust flow, so it is NOT the 48 s loaded value.
                     tau_turb_s=finite(st.tau_turb_s),
                     # Where the housing is HEADED: the steady state the current
                     # operating point implies, which is the fixed point of the
                     # same equation ThermalNetwork.step integrates. A value band
                     # alone cannot warn early, because the node is first-order --
                     # it can sit well below the limit and still be climbing to
                     # well above it. This is the Estimator's own number.
                     turbine_ss_c=finite(st.t_turb_ss_c))
        if gear['gear'] is not None:
            if previous_gear is not None and not gap and previous_gear['gear'] != gear['gear']:
                events.append(dict(t=sample.t, from_t=previous_gear['t'],
                                   from_gear=previous_gear['gear'], to_gear=gear['gear'],
                                   source='recorded' if gear['gear_source'] == previous_gear['gear_source'] == 'recorded' else 'estimated'))
            previous_gear = frame
        else:
            previous_gear = None  # Never claim a shift across missing/uncertain data.
        frames.append(frame)
        previous = frame
        if progress and (i % 64 == 0 or i + 1 == len(raw_rows)):
            progress((i + 1) / max(1, len(raw_rows)))
    if not frames:
        raise ValueError('The recording contains no usable timestamps')
    meta = fingerprint(path)
    meta.update(trip_id=path.stem, source=path.name, mode='replay',
                duration_s=frames[-1]['t'], sample_count=len(frames),
                road='illustrative_not_geographic', grade='unavailable_unvalidated',
                distance_partial=distance_partial, gap_limit_s=gap_limit,
                interpolation='distance_only; telemetry=previous_original_sample',
                shift_timing='sample_intervals_not_exact_mechanical_shift_times',
                comparison_available=False)
    return dict(status='ready', progress=1.0, frames=frames, events=events, meta=meta)


class BuildCancelled(Exception):
    """Raised inside the progress callback to abandon a superseded build."""


class ReplayStore:
    """One daemon builder, two completed datasets, no disk cache or queue growth.

    The builder is CANCELLABLE. Estimator runs about 75 samples/s (measured
    21 Sep: 79 rows/s on 3f64372e, 74 on 670063b2), so the longest recording
    takes minutes; without cancellation one mis-click on it locks every other
    trip behind it for that whole time.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._cache = OrderedDict()
        self._active = None
        self._progress = 0.0
        self._errors = {}
        self._cancel = threading.Event()

    def request(self, trip_id, preempt=False):
        """`preempt` is a USER ACTION, never a poll.

        If every poll for a different trip cancelled the build in flight, two
        browser tabs on two recordings would cancel each other forever and
        neither would ever finish. Only the first request after someone picks a
        drive may pre-empt; the polls that follow it wait their turn.
        """
        path = resolve_trip(trip_id)
        with self._lock:
            if trip_id in self._cache:
                self._cache.move_to_end(trip_id)
                return self._cache[trip_id]
            # Report a failure once, then forget it: a transient error must not
            # poison this recording for the rest of the process's life.
            if trip_id in self._errors:
                return dict(status='error', message=self._errors.pop(trip_id))
            if self._active == trip_id:
                return dict(status='building', progress=self._progress, active_trip_id=trip_id)
            if self._active:
                if preempt:
                    self._cancel.set()
                return dict(status='busy', progress=0, active_trip_id=self._active)
            self._cancel = threading.Event()
            self._active, self._progress = trip_id, 0.0
            threading.Thread(target=self._build, args=(trip_id, path, self._cancel),
                             daemon=True, name='replay-builder').start()
            return dict(status='building', progress=0.0, active_trip_id=trip_id)

    def _build(self, trip_id, path, cancel):
        def report(p):
            if cancel.is_set():
                raise BuildCancelled(trip_id)
            with self._lock:
                self._progress = p
        try:
            result = build_replay(path, report)
            with self._lock:
                self._cache[trip_id] = result
                while len(self._cache) > 2:
                    self._cache.popitem(last=False)
        except BuildCancelled:
            pass          # superseded, not failed: leave no error for the user
        except Exception as exc:
            with self._lock:
                self._errors[trip_id] = f'{type(exc).__name__}: {exc}'
        finally:
            with self._lock:
                self._active = None


store = ReplayStore()

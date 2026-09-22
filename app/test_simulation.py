"""Behavioral checks for the read-only simulation viewer. No vehicle needed."""
import csv
import importlib
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

from app.estimator import Estimator, Sample
from plant import predict, b58, map_from_airflow, charge_temperature


class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.present = importlib.util.find_spec('app.replay') is not None
        cls.replay = importlib.import_module('app.replay') if cls.present else None

    def need_replay(self):
        self.assertTrue(self.present, 'The replay data adapter is not implemented')
        return self.replay

    def test_saturated_six_is_estimated_as_eight_without_changing_rpm(self):
        r = self.need_replay().infer_gear(1944.59, 120.0, 6)
        self.assertEqual((r['gear'], r['gear_source'], r['gear_raw']), (8, 'estimated', 6))

    def test_valid_recorded_lower_gear_is_preferred(self):
        r = self.need_replay().infer_gear(3413.15, 60.0, 3)
        self.assertEqual((r['gear'], r['gear_source']), (3, 'recorded'))

    def test_slip_and_missing_speed_do_not_invent_gears(self):
        for rpm, speed in [(2900, 120), (900, 3), (2000, None), (None, 90), (0, 0)]:
            with self.subTest(rpm=rpm, speed=speed):
                r = self.need_replay().infer_gear(rpm, speed)
                self.assertIsNone(r['gear'])

    def test_path_traversal_cannot_select_arbitrary_files(self):
        r = self.need_replay()
        for name in ('../plant.py', '..\\plant.py', 'C:/secret.csv', 'unknown.csv'):
            with self.assertRaises(KeyError):
                r.resolve_trip(name)

    def test_fuel_is_existing_engine_output_not_a_new_fuel_model(self):
        s = Sample(t=0, rpm=2000, air_kgh=72, ect_c=90, t_amb_c=30,
                   v_kmh=60, spark_deg=20, lam=1.0)
        st = Estimator().update(s)
        self.assertTrue(hasattr(st, 'fuel_gps'), 'State must expose the already computed fuel output')
        charge = charge_temperature(303.15, 363.15)
        map_kpa = map_from_airflow(20, 2000, charge, geo=b58())
        expected = predict(2000, map_kpa, charge, 363.15, 20, 1.0, geo=b58())
        self.assertEqual(st.fuel_gps, expected['mdot_fuel_gps'])

    def test_replay_keeps_original_timing_and_matches_direct_estimator(self):
        r = self.need_replay()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'fixture.csv'
            p.write_text('Time,Engine speed,Air mass flow,Coolant temperature,Oil temperature,Ambient temperature,Vehicle speed,Actual ignition angle,Lambda actual value,Actual gear\n'
                         '0,1944.59,72,90,92,30,120,20,1,6\n'
                         '0.5,1944.59,75,90,92,30,120,20,1,6\n'
                         '2,1944.59,90,91,93,30,120,20,1,6\n', encoding='utf-8')
            data = r.build_replay(p)
            from app.reader import ReplayReader
            estimator = Estimator()
            direct = [estimator.update(s) for s in ReplayReader(str(p), speed=0)]
            self.assertEqual([f['t'] for f in data['frames']], [0, .5, 2])
            for frame, state in zip(data['frames'], direct):
                self.assertEqual(frame['rpm'], state.rpm)
                self.assertEqual(frame['speed_kmh'], state.v_kmh)
                self.assertEqual(frame['turbine_c'], state.t_turb_c)
                self.assertEqual(frame['fuel_gps'], state.fuel_gps)
                self.assertEqual(frame['gear'], 8)
            self.assertAlmostEqual(data['frames'][-1]['s_m'], 200/3)
            self.assertEqual(sorted(x.name for x in Path(tmp).iterdir()), ['fixture.csv'])
            json.dumps(data, allow_nan=False)

    def test_turbine_tau_is_passed_through_not_recomputed(self):
        """H/tau is the project's claim, so tau must be the Estimator's own value.

        It is flow-dependent (mistake 15): a loaded pull and an idle sit do not
        share one time constant, so a constant here would be a fabricated axis.
        """
        r = self.need_replay()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'tau.csv'
            p.write_text('Time,Engine speed,Air mass flow,Coolant temperature,Ambient temperature,Vehicle speed,Actual ignition angle,Lambda actual value\n'
                         '0,1200,18,90,30,40,20,1\n'
                         '4,5200,520,95,30,150,12,0.85\n', encoding='utf-8')
            data = r.build_replay(p)
            from app.reader import ReplayReader
            estimator = Estimator()
            direct = [estimator.update(s) for s in ReplayReader(str(p), speed=0)]
            for frame, state in zip(data['frames'], direct):
                self.assertEqual(frame['tau_turb_s'], state.tau_turb_s)
            taus = [f['tau_turb_s'] for f in data['frames']]
            self.assertTrue(all(t is not None and t > 0 for t in taus))
            # Flow rose ~29x, so tau must fall. A constant would mean a stub.
            self.assertLess(taus[1], taus[0])
            json.dumps(data, allow_nan=False)

    def test_absent_speed_and_invalid_model_state_stay_unavailable(self):
        r = self.need_replay()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'missing.csv'
            p.write_text('Time,Engine speed,Air mass flow\n0,0,0\n1,2000,72\n', encoding='utf-8')
            data = r.build_replay(p)
            self.assertTrue(all(f['speed_kmh'] is None and f['s_m'] is None for f in data['frames']))
            self.assertIsNone(data['frames'][0]['turbine_c'])
            self.assertIsNone(data['frames'][0]['fuel_gps'])
            self.assertIsNone(data['frames'][1]['coolant_c'])
            json.dumps(data, allow_nan=False)

    def test_the_internal_gear_channel_cannot_promote_an_inferred_gear(self):
        """`Internal gear` is the constant 8.0 on fb988991, not a reading.

        It was briefly used to corroborate a ratio-inferred gear and call it
        `recorded`. On a car whose gear channel saturates at 6 (mistake 18) an
        eighth gear can never be a recorded value, so this asserted a
        measurement the vehicle cannot produce.
        """
        r = self.need_replay()
        with_internal = r.infer_gear(1944.59, 120.0, 6, 8)
        self.assertEqual(with_internal['gear'], 8)
        self.assertEqual(with_internal['gear_source'], 'estimated')
        self.assertEqual(with_internal['gear_note'], 'clipped_channel')
        # The internal channel must change nothing at all.
        self.assertEqual(with_internal, r.infer_gear(1944.59, 120.0, 6))
        # A genuinely recorded low gear is still preferred.
        self.assertEqual(r.infer_gear(3413.15, 60.0, 3, 3)['gear_source'], 'recorded')

    def test_a_recording_that_never_moves_is_not_advertised_as_having_speed(self):
        """3f64372e carries `Vehicle speed` and reads 0.0 on every row.

        A header check promises a moving car and delivers a parked one, so the
        catalog separates the column existing from the car having moved.
        """
        r = self.need_replay()
        by_id = {t['id']: t for t in r.trip_catalog()}
        parked = by_id.get('3f64372e-20260907_070041')
        self.assertIsNotNone(parked, 'the zero-speed recording is missing from logs/raw')
        self.assertTrue(parked['has_speed'], 'the column is present in this log')
        self.assertFalse(parked['has_motion'], 'no row of this log has a non-zero speed')
        moving = by_id.get('670063b2-20260907_142018')
        self.assertTrue(moving['has_speed'] and moving['has_motion'])

    def test_a_second_request_cancels_the_build_in_flight(self):
        """drive10 is ~9 minutes of Estimator; one mis-click must not lock the lab."""
        import threading
        import time
        r = self.need_replay()
        store = r.ReplayStore()
        started = threading.Event()
        finished = threading.Event()

        def slow(path, progress=None):
            started.set()
            for i in range(2000):
                progress(i / 2000)      # raises BuildCancelled once cancelled
                time.sleep(0.004)
            finished.set()
            return dict(status='ready', progress=1.0, frames=[], events=[], meta={})

        ids = [t['id'] for t in r.trip_catalog()]
        self.assertGreaterEqual(len(ids), 2)
        original = r.build_replay
        r.build_replay = slow
        try:
            self.assertEqual(store.request(ids[0])['status'], 'building')
            self.assertTrue(started.wait(5), 'the builder thread never started')

            # A POLL for another trip must NOT cancel. If it did, two browser
            # tabs on two recordings would cancel each other forever.
            for _ in range(5):
                self.assertEqual(store.request(ids[1])['status'], 'busy')
                time.sleep(0.05)
            self.assertEqual(store._active, ids[0], 'a mere poll cancelled the build')
            self.assertFalse(store._cancel.is_set(), 'a mere poll set the cancel flag')

            # A USER PICKING another drive does cancel.
            self.assertEqual(store.request(ids[1], preempt=True)['status'], 'busy')
            for _ in range(500):
                if store._active is None:
                    break
                time.sleep(0.02)
            self.assertIsNone(store._active, 'the superseded build was never cancelled')
            self.assertFalse(finished.is_set(), 'the cancelled build ran to completion')
            self.assertEqual(store._errors, {}, 'a cancellation must not be recorded as a failure')
        finally:
            r.build_replay = original

    def test_a_failure_is_reported_once_and_then_allows_a_retry(self):
        r = self.need_replay()
        store = r.ReplayStore()
        trip = r.trip_catalog()[0]['id']
        store._errors[trip] = 'RuntimeError: boom'
        first = store.request(trip)
        self.assertEqual(first['status'], 'error')
        self.assertIn('boom', first['message'])
        original = r.build_replay
        r.build_replay = lambda path, progress=None: dict(status='ready', progress=1.0,
                                                          frames=[], events=[], meta={})
        try:
            # The same trip must be buildable again; one failure cannot poison
            # the recording for the lifetime of the process.
            self.assertNotEqual(store.request(trip)['status'], 'error')
        finally:
            r.build_replay = original

    def test_no_translated_string_is_built_without_a_language(self):
        """Arabic leaked into English mode because two call sites dropped the arg.

        `gearState` and `previewCaption` take a language and default to Arabic,
        so calling them bare is silent: the page renders, and one panel simply
        stays in the wrong language. A default that silently picks a different
        behaviour is a trap -- CLAUDE.md mistake 1, one level down.
        """
        import re
        sim = Path(__file__).resolve().parent / 'static' / 'sim'
        main = (sim / 'main.mjs').read_text(encoding='utf-8')

        # Every function in panel.mjs whose signature takes a language.
        panel = (sim / 'panel.mjs').read_text(encoding='utf-8')
        takes_lang = set(re.findall(r'export function (\w+)\([^)]*\blang\b', panel))
        self.assertIn('gearState', takes_lang)
        self.assertIn('previewCaption', takes_lang)

        for name in sorted(takes_lang):
            for call in re.finditer(rf'\b{name}\(([^;]*?)\)[;,)\s]', main):
                args = call.group(1)
                self.assertTrue(
                    'lang' in args.lower(),
                    f'{name}(...) is called in main.mjs without a language: {args[:70]!r}')

        # t() is the other way a string is built; it must never be called bare.
        for call in re.finditer(r"[^.\w]t\(\s*([^,)]*)", main):
            first = call.group(1).strip()
            self.assertTrue(
                'lang' in first.lower(),
                f't() called with {first!r} as the language in main.mjs')

    def test_the_page_can_actually_load_every_asset_and_id_it_references(self):
        """The shipped page was dead for a day because main.mjs did not exist.

        Nothing failed: both suites passed, the route returned 200, and the
        browser silently 404'd one module. A missing id is the same failure one
        level down -- `$('typo')` returns null and that panel just never updates.
        """
        import re
        static = Path(__file__).resolve().parent / 'static'
        html = (static / 'simulation.html').read_text(encoding='utf-8')

        for src in re.findall(r'<script[^>]+src="/static/([^"]+)"', html):
            self.assertTrue((static / src).is_file(), f'{src} is referenced by the page and does not exist')
        for href in re.findall(r'<link[^>]+href="/static/([^"]+)"', html):
            self.assertTrue((static / href).is_file(), f'{href} is referenced by the page and does not exist')
        for mapped in re.findall(r'"(?:three|three/addons/)":\s*"/static/([^"]+)"', html):
            target = static / mapped
            self.assertTrue(target.is_file() or target.is_dir(), f'import map points at missing {mapped}')

        main = (static / 'sim' / 'main.mjs').read_text(encoding='utf-8')
        declared = set(re.findall(r'\sid="([^"]+)"', html))
        used = set(re.findall(r"\$\('([^']+)'\)", main))
        self.assertTrue(used, 'the id scan found nothing; the pattern has drifted')
        self.assertFalse(used - declared, f'main.mjs reads ids the page does not define: {sorted(used - declared)}')

        # syncPlayButton swaps these two sprites; a missing symbol is an empty button.
        for symbol in re.findall(r"setAttribute\('href', [^)]*?'(#i-[a-z]+)'", main):
            self.assertIn(f'id="{symbol[1:]}"', html, f'{symbol} is not in the icon library')

        # Every module main.mjs imports must resolve as a real sibling file.
        for spec in re.findall(r"from '(\./[^']+)'", main):
            self.assertTrue((static / 'sim' / spec[2:]).is_file(), f'main.mjs imports missing {spec}')

    def test_http_catalog_exposes_live_ratios_and_rejects_writes(self):
        from fastapi.testclient import TestClient
        from app.server import app
        with TestClient(app) as client:
            response = client.get('/api/replay/trips')
            self.assertEqual(response.status_code, 200)
            catalog = response.json()
            self.assertEqual(len(catalog['vehicle']['gears']), 8)
            self.assertEqual(catalog['vehicle']['gears'][-1], .640)
            self.assertTrue(any(t['id'].startswith('670063b2') for t in catalog['trips']))
            self.assertEqual(client.get('/api/replay/trips/not-a-trip').status_code, 404)
            self.assertEqual(client.post('/api/replay/trips').status_code, 405)


if __name__ == '__main__':
    unittest.main()

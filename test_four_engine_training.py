"""test_four_engine_training.py -- ORDER step 7's training code: the four-engine roads, decision 29's recipe, the third arm.

    python test_four_engine_training.py        about 8-9 min; exit code 0 when all pass

Rows 116-118 of results/VALIDATION_DECISIONS.md, built by docs/build_step_2/ORDER_TO_TRAINING.md step 7
(commit C1, "training code outside the plant"): four_engine_roads.py (the wrapper and its generator),
training_recipe.py (the learning-rate schedule and the checkpoint average), train.py's road mode
`four_engine` and recipe flags, train_all.py's third arm. NO ROADS SEED EXISTS until the reveal (row 96):
every roads seed here is SYNTHETIC (SYNTHETIC_ROADS_SEED, below 2**32, so it can never be roads_seed),
and the tests that use one say SYNTHETIC in their names. Nothing here trains an experiment: the two
train.py runs are smoke runs of 600 and 1000 steps into temporary folders outside the repository,
deleted after (the identity check, check_training_device.py --identity and --compare, is run beside
this file, not by it). No EPA table and no held-out row is read; the EPA plants are built through
engines.get, which reads their specs, derived files and freeze records.

  Generator      the general episode takes a random stream and nothing else; its arrays and its c_turb
                 draw are the same on all four engines; decision 12's ranges (ambient 25-45 C, speed
                 60-150 km/h once launched, every change at most EXTREME_ACCEL both ways from rest on,
                 grades 0-18 % flat for 30 s, every change an 8 s ramp by epa_roads.ramp_problems); the
                 draws in ExtremesTrainingEnv's order; the speed profile makes extreme_speed_profile's
                 draws, follows their targets, and leaves them only where a limit of the notional car binds
  NotionalCar    the notional car's climb and coast lie inside every car's own (four_engine_roads.
                 car_bounds, a coarse grid) and the two limits can both hold; on drawn episodes no request
                 of any of the four cars falls under its torque floor or over its deliverable torque, and
                 without the limits it does (mistake 12)
  ScoredShareSYNTHETIC  the share's first road is epa_roads.training_share_road exactly; episodes 0, 10,
                 20, ... are the share's and no others; the general roads are the same with the share on
                 and off; every share road a fresh, ramped layout of row 101's family, its c_turb drawn
                 from the share stream after it; apart from the practice stream; the refusals
  Wrapper        both networks get the drawn c_turb on a NEW record, the plant's untouched; a seeded
                 reset restarts the sequence and an unseeded one continues it (RandomClimb's rule); the
                 observation reads the drawn ambient; the road log; train.build_env's road mode
  Requests       requests() equals env.step's torque request and engine speed on every engine, element
                 for element; the counts can fail (a zero table, a huge floor); the measurement's shares
  Recipe         LastThird; the constant schedule is the float itself; the snapshot steps and their
                 refusals; the manifest refuses a changed or missing snapshot
  TrainRefusals  train.py refuses each inconsistent flag before it makes a directory: the share without
                 a record, a record with no flag, the share off the four-engine road, another step, a
                 SYNTHETIC share into the repository, every H but 30 s (row 117), H on the blinded arm,
                 a ratio the record does not hold, a bad average window, a training seed row 96 reserves;
                 X2's runs/wideair_dt1 is CLOSED; build_env names the four-engine road's two options
  TrainSmoke     train.py --road four_engine at X1's defaults (600 steps): no recipe recorded, no
                 snapshot; with every recipe flag on (1000 steps, SYNTHETIC share): the first episode is
                 the share's road, the second the general stream's first, the learning rate ends at 0 in
                 the saved optimizer, five snapshots and the manifest, and AveragedPolicy is their mean
  TrainAll       the pair's commands are the ones train_all.py built before, argument for argument; the
                 third arm's runs and commands; --recipe29; the third arm refused before any run, with
                 every engine's H and its preview steps, which are row 102's
  Isolation      roads.json's 35 files are the list the roads commit hashes, their import closure lies
                 inside it, and no file of this commit is among them (row 121); no new file's name ends
                 in a plant file's (fingerprint's git_dirty_plant_files matches by suffix)

The roads code's own tau (roads_ceiling.tau_table, row 102's one definition) is computed once, in a
subprocess, for the third arm's SYNTHETIC record (about 1.5 min at 4 jobs): roads_ceiling installs an
audit hook that would refuse this file's reads of a run's curve.csv.
"""
import argparse
import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

import engine_env as E  # noqa: E402
import engines  # noqa: E402
import epa_roads as ER  # noqa: E402
import four_engine_roads as F  # noqa: E402
import training_recipe as TR  # noqa: E402

SYNTHETIC_ROADS_SEED = 4242          # SYNTHETIC: below 2**32, never roads_seed (row 96)
ENGINE_IDS = ER.ENGINES
ENV = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONIOENCODING="utf-8")
STATE = {}


def setUpModule():
    """One temporary folder outside the repository, two SYNTHETIC roads records in it (one without tau,
    one with the roads code's tau for every engine) and nothing else."""
    tmp = tempfile.mkdtemp(prefix="four_engine_test_")
    assert not F.inside_repository(tmp), tmp
    STATE["tmp"] = tmp
    STATE["record"] = F.write_synthetic_record(os.path.join(tmp, "roads.SYNTHETIC.json"), SYNTHETIC_ROADS_SEED)
    code = ("import json, roads_ceiling as RC\n"
            "t = RC.tau_table(list(RC.ENGINES), variant=('frozen',), jobs=4)\n"
            "print(json.dumps(dict(taus={e: t[e][0] for e in t}, ratios=list(RC.RATIOS))))\n")
    p = subprocess.run([sys.executable, "-B", "-c", code], cwd=HERE, env=ENV, capture_output=True, text=True,
                       timeout=1800)
    if p.returncode != 0:
        raise RuntimeError("roads_ceiling.tau_table failed:\n" + p.stdout[-2000:] + p.stderr[-2000:])
    got = json.loads(p.stdout.strip().splitlines()[-1])
    STATE["taus"], STATE["ratios"] = got["taus"], got["ratios"]
    STATE["tau_record"] = F.write_synthetic_record(os.path.join(tmp, "roads.SYNTHETIC.tau.json"),
                                                   SYNTHETIC_ROADS_SEED, taus=got["taus"], ratios=got["ratios"])
    print(f"\n[SYNTHETIC roads seed {SYNTHETIC_ROADS_SEED}] tau by roads_ceiling.tau_table: "
          + ", ".join(f"{e} {t:.4f} s" for e, t in got["taus"].items()) + f"; ratios {got['ratios']}")


def tearDownModule():
    shutil.rmtree(STATE.get("tmp", ""), ignore_errors=True)


_PLANTS = {}


def plant_of(engine_id):
    if engine_id not in _PLANTS:
        _PLANTS[engine_id] = engines.get(engine_id)
    return _PLANTS[engine_id]


def wrapper(engine_id, *, seed, record=None, duration=F.DURATION_S):
    """The four-engine roads on one engine; the share on when a record is given."""
    return F.FourEngineRoads(F._base_env(plant_of(engine_id), seed=seed), seed=seed, duration=duration,
                             scored_share=record is not None, roads_record=record)


def episodes(w, n, *, seed):
    """n episodes as training draws them: the first reset seeded, the rest not. [(cycle, road)]."""
    out = []
    for i in range(n):
        w.reset(seed=seed if i == 0 else None)
        c = w.unwrapped.cycle
        out.append(({k: (np.array(v) if isinstance(v, np.ndarray) else v) for k, v in c.items()}, dict(w.road)))
    return out


def same_cycle(a, b):
    return all(np.array_equal(np.asarray(a[k]), np.asarray(b[k])) for k in ("t", "v_mps", "grade")) and \
        all(float(a[k]) == float(b[k]) for k in ("t_amb", "p_baro", "humidity"))


# =====================================================================================================
class Generator(unittest.TestCase):
    def test_the_generator_takes_a_stream_and_nothing_else(self):
        """Row 116: no vehicle. The general episode's only parameter is its stream, and no function of the
        generator names a plant, a car, a vehicle or the registry."""
        self.assertEqual(list(F.general_episode.__code__.co_varnames[:F.general_episode.__code__.co_argcount]),
                         ["rng"])
        import inspect
        for fn in (F.general_episode, F.grade_profile, F.speed_profile, F.climb_limit, F.coast_limit,
                   F.coast_road, F.c_turb_scale, F.share_episode):
            names = {n.id for n in ast.walk(ast.parse(inspect.getsource(fn))) if isinstance(n, ast.Name)}
            names |= {n.attr for n in ast.walk(ast.parse(inspect.getsource(fn))) if isinstance(n, ast.Attribute)}
            with self.subTest(fn=fn.__name__):
                self.assertEqual(names & {"plant", "car", "veh", "engines", "vehicle_for", "engine"}, set())

    def test_the_arrays_are_the_same_on_every_engine_SYNTHETIC(self):
        """Twelve episodes (the share's 0 and 10 among them) drawn through the wrapper on each engine:
        every cycle and every c_turb scale equal to the B58's."""
        ref = episodes(wrapper("b58", seed=9000, record=STATE["record"]), 12, seed=9000)
        for e in ENGINE_IDS[1:]:
            got = episodes(wrapper(e, seed=9000, record=STATE["record"]), 12, seed=9000)
            for i, ((c0, r0), (c1, r1)) in enumerate(zip(ref, got)):
                with self.subTest(engine=e, episode=i):
                    self.assertTrue(same_cycle(c0, c1))
                    self.assertEqual((r0["kind"], r0["c_turb_scale"]), (r1["kind"], r1["c_turb_scale"]))

    def test_decision_12s_ranges(self):
        """300 general episodes: ambient 25-45 C, one value; 900 samples at dt 1; from rest at EXTREME_ACCEL
        (row 116's "limited to EXTREME_ACCEL both ways", the launch included), then 60-150 km/h, every
        change at most EXTREME_ACCEL both ways, and a speed that changes; every step inside the notional
        car's climb and coast; grades 0-18 %, flat for 30 s, every change an 8 s linear ramp (row 98 (a)),
        changes at least 60 s apart; pressure and humidity make_grade_climb's."""
        ref = E.make_grade_climb(duration=900.0, dt=1.0, t_amb=315.0, grade=0.12, v_kmh=130.0)
        tol = 1e-9
        for s in range(300):
            c, scale = F.general_episode(F.general_rng(s))
            v, g = np.asarray(c["v_mps"]), np.asarray(c["grade"])
            with self.subTest(seed=s):
                self.assertTrue(np.isscalar(c["t_amb"]) or np.ndim(c["t_amb"]) == 0)
                self.assertTrue(25.0 <= c["t_amb"] - 273.15 <= 45.0)
                self.assertEqual(len(v), 900)
                self.assertTrue(np.array_equal(c["t"], np.arange(900) * 1.0))
                self.assertEqual(v[0], 0.0)
                self.assertTrue(np.allclose(np.diff(v[:20]), E.EXTREME_ACCEL, rtol=0, atol=tol))
                launched = int(np.argmax(v * 3.6 >= 60.0 - tol))
                self.assertGreater(launched, 0)
                after = v[launched:]
                self.assertTrue(np.all(after * 3.6 >= 60.0 - tol) and np.all(after * 3.6 <= 150.0 + tol))
                a = np.diff(v)
                self.assertLessEqual(np.abs(a).max(), E.EXTREME_ACCEL * 1.0 + tol)
                self.assertGreater(np.ptp(after), 0.0)
                pull = F.G0 * np.sin(np.arctan(g[:-1]))
                climb = np.array([F.climb_limit(x) for x in v[:-1]])
                coast = np.array([F.coast_limit(x, y) for x, y in zip(v[:-1], g[:-1])])
                self.assertTrue(np.all(a + pull <= climb + tol))
                self.assertTrue(np.all(-a <= coast + tol))
                self.assertTrue(np.all(v[:-1][a < -tol] * 3.6 >= 60.0 - tol))
                self.assertTrue(g.min() >= 0.0 and g.max() <= E.EXTREME_GRADE_MAX)
                self.assertTrue(np.all(g[:30] == 0.0))
                self.assertEqual(ER.ramp_problems(g, dt=1.0), [])
                starts = [i for i in range(1, len(g) - 1) if g[i + 1] != g[i] and g[i] == g[i - 1]]
                self.assertTrue(all(b - a >= 60 for a, b in zip(starts, starts[1:])), starts)
                self.assertEqual((c["p_baro"], c["humidity"]), (ref["p_baro"], ref["humidity"]))
                self.assertTrue(E.EXTREME_C_TURB[0] <= scale <= E.EXTREME_C_TURB[1])

    def test_the_draws_come_in_extremes_order(self):
        """ExtremesTrainingEnv.reset's order: the ambient, the road, the speed, then the housing's scale,
        log-uniform on EXTREME_C_TURB -- replayed here by hand from the same stream."""
        for s in (0, 1, 77):
            c, scale = F.general_episode(F.general_rng(s))
            rng = np.random.default_rng([s, F.GENERAL_STREAM])
            t_amb = 273.15 + rng.uniform(25.0, 45.0)
            g = F.grade_profile(rng, 900, 1.0)
            v = F.speed_profile(rng, 900, 1.0, g)
            want = float(np.exp(rng.uniform(np.log(0.75), np.log(1.333))))
            with self.subTest(seed=s):
                self.assertEqual(c["t_amb"], t_amb)
                self.assertTrue(np.array_equal(c["grade"], g) and np.array_equal(c["v_mps"], v))
                self.assertEqual(scale, want)

    def test_the_speed_makes_extreme_speed_profiles_draws_and_follows_them(self):
        """X1's extreme_speed_profile and this speed profile, on one stream, consume the same draws (the
        stream is in the same state after both: the limits move the speed, never a draw); the targets
        replayed by hand from the stream are what the speed follows: every step moves toward the step's
        target by at most EXTREME_ACCEL, and a step that is not the clipped move toward the target is one
        where a limit of the notional car binds (mistake 11: one schedule, two writings, checked)."""
        plant = plant_of("b58")
        veh = F._base_env(plant, seed=0).veh
        tol = 1e-9
        for s in (0, 3, 11, 29):
            g = F.grade_profile(np.random.default_rng([s, 1]), 900, 1.0)
            r1, r2, r3 = (np.random.default_rng(s) for _ in range(3))
            v = F.speed_profile(r1, 900, 1.0, g)
            E.extreme_speed_profile(r2, 900, 1.0, g, 315.0, veh, plant.engine.loop.torque_floor_nm)
            target = np.empty(900)
            tg, nxt = r3.uniform(*E.EXTREME_V_KMH) / 3.6, 20 + int(r3.uniform(*E.EXTREME_HOLD_S))
            for i in range(1, 900):
                if i >= nxt:
                    tg, nxt = r3.uniform(*E.EXTREME_V_KMH) / 3.6, i + int(r3.uniform(*E.EXTREME_HOLD_S))
                target[i] = tg
            with self.subTest(seed=s):
                self.assertEqual(r1.random(), r2.random())
                bound = 0
                for i in range(1, 900):
                    free = v[i - 1] + float(np.clip(target[i] - v[i - 1], -E.EXTREME_ACCEL, E.EXTREME_ACCEL))
                    if abs(v[i] - free) > tol:
                        pull = F.G0 * np.sin(np.arctan(g[i - 1]))
                        a = v[i] - v[i - 1]
                        self.assertTrue(abs(a + pull - F.climb_limit(v[i - 1])) < 1e-9
                                        or abs(-a - F.coast_limit(v[i - 1], g[i - 1])) < 1e-9, (s, i))
                        bound += 1
                self.assertGreater(bound, 0)


# =====================================================================================================
class NotionalCar(unittest.TestCase):
    """The review of 31 October 2026 (findings S1, F1): row 116's generator as first written asked the
    engines for less than their closed-throttle torque in its 0.8 m/s^2 slowdowns and for more than their
    deliverable torque on steep, fast holds, and failed row 119's road gate. The notional car's two limits
    are what keeps every request of every car inside both, with arrays that read no car."""

    def test_the_notional_car_lies_inside_every_cars_bounds(self):
        """car_bounds on a coarse grid (every 5 km/h, grades every 6 %; `four_engine_roads.py bounds` runs
        the fine one): no problem on any car, and an 18 % hill never asks a slowdown past EXTREME_ACCEL."""
        res = F.bounds(list(ENGINE_IDS), jobs=4, speeds_kmh=tuple(float(x) for x in range(5, 151, 5)),
                       coast_kmh=tuple(float(x) for x in range(60, 151, 5)), grades=(0.0, 0.06, 0.12, 0.18))
        for r in res:
            with self.subTest(engine=r["engine"]):
                self.assertEqual(r["problems"], [])
        self.assertEqual(F.feasibility_problems(), [])
        print("\n" + "\n".join(F.bounds_lines(res)))

    def _counts(self, episodes_per_seed, seeds):
        """Below-floor and above-deliverable request counts of every car on drawn general episodes."""
        envs = {e: F._base_env(plant_of(e), seed=0) for e in ENGINE_IDS}
        tot = {e: dict(steps=0, below_floor=0, above_deliverable=0) for e in ENGINE_IDS}
        for s in seeds:
            rng = F.general_rng(s)
            for _ in range(episodes_per_seed):
                cycle, _ = F.general_episode(rng)
                for e, env in envs.items():
                    env.cycle = cycle
                    c = F.episode_counts(env)
                    for k in tot[e]:
                        tot[e][k] += c[k]
        return tot

    def test_no_drawn_request_leaves_any_cars_floor_or_deliverable(self):
        """Twelve general episodes (four seeds of three): every request of every car at or above its torque
        floor and at or under its deliverable torque. The control (mistake 12): with the two limits
        lifted, the same episodes ask some car for less than its floor and some for more than it delivers."""
        got = self._counts(3, (9100, 9101, 9102, 9103))
        for e, c in got.items():
            with self.subTest(engine=e):
                self.assertEqual(c["steps"], 12 * 899)
                self.assertEqual((c["below_floor"], c["above_deliverable"]), (0, 0), c)
        with mock.patch.object(F, "CLIMB_P_W_PER_KG", 1e9), mock.patch.object(F, "COAST_AT_60", 1e9):
            lifted = self._counts(3, (9100, 9101, 9102, 9103))
        self.assertGreater(sum(c["below_floor"] for c in lifted.values()), 0, lifted)
        self.assertGreater(sum(c["above_deliverable"] for c in lifted.values()), 0, lifted)


# =====================================================================================================
class ScoredShareSYNTHETIC(unittest.TestCase):
    def test_SYNTHETIC_the_first_share_road_is_training_share_road(self):
        """The share's first road of each seed is epa_roads.training_share_road(roads_seed, seed), the
        road dict and its environment cycle alike."""
        for seed in (0, 7, 9000):
            cy, _, road = F.share_episode(F.share_rng(SYNTHETIC_ROADS_SEED, seed), seed=seed)
            ref = ER.training_share_road(SYNTHETIC_ROADS_SEED, seed)
            with self.subTest(seed=seed):
                self.assertEqual(road, ref)
                self.assertTrue(same_cycle(cy, ER.env_cycle(ref)))
            w = wrapper("b58", seed=seed, record=STATE["record"])
            w.reset(seed=seed)
            with self.subTest(seed=seed, via="wrapper"):
                self.assertTrue(same_cycle(w.unwrapped.cycle, ER.env_cycle(ref)))

    def test_SYNTHETIC_episodes_0_10_20_and_no_others(self):
        eps = episodes(wrapper("ford_27tt", seed=3, record=STATE["record"]), 25, seed=3)
        kinds = [r["kind"] for _, r in eps]
        self.assertEqual([i for i, k in enumerate(kinds) if k == "scored"], [0, 10, 20])
        for i, (c, r) in enumerate(eps):
            if r["kind"] == "scored":
                with self.subTest(episode=i):
                    self.assertEqual(c["t_amb"], ER.T_AMB_K)
                    self.assertTrue(np.all(np.asarray(c["v_mps"])[19:] == ER.V_KMH / 3.6))
                    self.assertEqual(r["seed_kind"], "SYNTHETIC")

    def test_SYNTHETIC_the_general_roads_do_not_move_with_the_share(self):
        """The general stream feeds general episodes only: a seed's general roads, in order, are the same
        with the share on and off."""
        on = [(c, r) for c, r in episodes(wrapper("b58", seed=5, record=STATE["record"]), 22, seed=5)
              if r["kind"] == "general"]
        off = episodes(wrapper("b58", seed=5), len(on), seed=5)
        for i, ((c0, r0), (c1, r1)) in enumerate(zip(on, off)):
            with self.subTest(general_episode=i):
                self.assertTrue(same_cycle(c0, c1))
                self.assertEqual(r0["c_turb_scale"], r1["c_turb_scale"])

    def test_SYNTHETIC_share_roads_are_fresh_ramped_layouts_from_the_share_stream(self):
        """Three share roads of one seed: replayed from default_rng([roads_seed, 0x7A, seed]) as a layout,
        a road and a c_turb scale each, in that order; all different; every grade change ramped; row
        101's family (130 km/h, 315 K, climbs of 10-12 %)."""
        w = wrapper("mazda_25t", seed=8, record=STATE["record"])
        got = [(c, r) for c, r in episodes(w, 21, seed=8) if r["kind"] == "scored"]
        rng = np.random.default_rng([SYNTHETIC_ROADS_SEED, 0x7A, 8])
        leads = []
        for i, (c, r) in enumerate(got):
            lead, climbs, discarded = ER.layout(rng)
            road = ER.make_road(k=None, episode_seed=8, weights=None, lead=lead, climbs=climbs,
                                discarded=discarded, first_slot=0)
            scale = float(np.exp(rng.uniform(np.log(0.75), np.log(1.333))))
            with self.subTest(share_road=i):
                self.assertTrue(same_cycle(c, ER.env_cycle(road)))
                self.assertEqual(r["c_turb_scale"], scale)
                self.assertEqual(ER.ramp_problems(c["grade"], dt=1.0), [])
                self.assertTrue(all(0.10 <= x["grade"] <= 0.12 for x in road["climbs"]))
            leads.append((lead, tuple(x[:2] for x in climbs)))
        self.assertEqual(len(set(leads)), len(leads))

    def test_SYNTHETIC_the_share_stream_is_not_the_practice_stream(self):
        prac = ER.practice_roads(SYNTHETIC_ROADS_SEED)[0]
        share = ER.training_share_road(SYNTHETIC_ROADS_SEED, 0)
        self.assertNotEqual(prac["draws"], share["draws"])

    def test_SYNTHETIC_refusals(self):
        tmp = STATE["tmp"]
        with self.assertRaises(F.Refused):
            F.FourEngineRoads(F._base_env(plant_of("b58"), seed=0), seed=0, duration=F.DURATION_S,
                              scored_share=True, roads_record=None)
        with self.assertRaises(F.Refused):
            F.FourEngineRoads(F._base_env(plant_of("b58"), seed=0), seed=0, duration=F.DURATION_S,
                              scored_share=False, roads_record=STATE["record"])
        with self.assertRaises(F.Refused):
            F.read_roads_record(os.path.join(tmp, "no_such_roads.json"))
        with self.assertRaises(F.Refused):
            F.read_roads_record(None)
        bad = os.path.join(tmp, "bad.SYNTHETIC.json")
        for change in (lambda r: r["commit_reveal"].update(roads_seed=2 ** 40),
                       lambda r: r["commit_reveal"].pop("SYNTHETIC"),
                       lambda r: r["streams"].update(training_share="default_rng([roads_seed, 0x50])"),
                       lambda r: r.update(seed_kind="MAYBE")):
            with open(STATE["record"], encoding="utf-8") as fh:
                rec = json.load(fh)
            change(rec)
            with open(bad, "w", encoding="utf-8") as fh:
                json.dump(rec, fh)
            with self.subTest(change=change):
                with self.assertRaises(F.Refused):
                    F.read_roads_record(bad)
        with self.assertRaises(F.Refused):
            F.write_synthetic_record(os.path.join(HERE, "roads.SYNTHETIC.json"), SYNTHETIC_ROADS_SEED)
        self.assertFalse(os.path.exists(os.path.join(HERE, "roads.SYNTHETIC.json")))
        for dur, dt in ((300.0, 1.0), (900.0, 0.2)):
            env = E.SupervisoryTunerEnv(E.locked_climb(plant_of("b58"), duration=dur, dt=dt), plant=plant_of("b58"),
                                        dt=dt, seed=0)
            with self.subTest(duration=dur, dt=dt):
                with self.assertRaises(F.Refused):
                    F.FourEngineRoads(env, seed=0, duration=dur, scored_share=False, roads_record=None)

    def test_a_REAL_record_needs_its_reveal_checked_as_the_draw_checks_it_SYNTHETIC_reveal(self):
        """A REAL record is read only when its reveal holds as epa_roads.draw holds it (row 96; the review
        of 31 October 2026, R0-2): each integer at least 2**128 and matching its hash line, the two lines
        the roads commit's COMMITMENT_G and COMMITMENT_J (git show; mocked here, since no roads commit
        exists), and roads_seed the one the reveal gives. The reveal is two made-up integers and a made-up
        commit: SYNTHETIC, so the seed is never roads_seed. The control (mistake 12): the record that holds
        all of it is read, and each change of one part is refused."""
        a_g, a_j, commit = 2 ** 200 + 1, 2 ** 201 + 3, "0123456789abcdef0123456789abcdef01234567"
        lines = {"ghassan": ER.commitment_hash(a_g), "jad": ER.commitment_hash(a_j)}
        seed = ER.roads_seed_from(a_g, a_j, commit)
        good = {"seed_kind": "REAL", "streams": ER.streams(),
                "commit_reveal": {"hash_lines": dict(lines), "reveal": {"ghassan": a_g, "jad": a_j},
                                  "roads_commit": commit, "roads_seed": seed}}
        path = os.path.join(STATE["tmp"], "real_kind.SYNTHETIC_reveal.json")

        def read(rec, committed=(lines["ghassan"], lines["jad"])):
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(rec, fh)
            with mock.patch.object(F, "committed_hash_lines", return_value=committed):
                return F.read_roads_record(path)
        self.assertEqual(read(good)["roads_seed"], seed)
        bad_cases = {
            "seed + 1": lambda r: r["commit_reveal"].update(roads_seed=seed + 1),
            "no hash lines": lambda r: r["commit_reveal"].pop("hash_lines"),
            "a line that does not match": lambda r: r["commit_reveal"]["hash_lines"].update(jad="0" * 64),
            "an integer below 2**128": lambda r: r["commit_reveal"]["reveal"].update(ghassan=12345),
        }
        for name, change in bad_cases.items():
            rec = json.loads(json.dumps(good))
            change(rec)
            with self.subTest(change=name):
                with self.assertRaises(F.Refused):
                    read(rec)
        with self.subTest(change="lines that are not the roads commit's"):
            with self.assertRaises(F.Refused):
                read(good, committed=(lines["ghassan"], "f" * 64))
        with self.subTest(change="no roads commit in this repository"):
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(good, fh)
            with self.assertRaises(F.Refused):
                F.read_roads_record(path)               # the made-up commit is not in this repository

    def test_a_REAL_record_trains_only_from_the_committed_roads_json(self):
        """train.check_recipe and train_all.check_four_engine refuse a REAL record anywhere but the
        committed, unmodified results/EPA_ROADS/roads.json (R0-2); the record here passes read_roads_record
        with the roads commit's lines mocked, so only the path refuses it."""
        import train
        import train_all as TA
        a_g, a_j, commit = 2 ** 200 + 5, 2 ** 201 + 7, "89abcdef0123456789abcdef0123456789abcdef"
        lines = {"ghassan": ER.commitment_hash(a_g), "jad": ER.commitment_hash(a_j)}
        rec = {"seed_kind": "REAL", "streams": ER.streams(),
               "commit_reveal": {"hash_lines": lines, "reveal": {"ghassan": a_g, "jad": a_j},
                                 "roads_commit": commit, "roads_seed": ER.roads_seed_from(a_g, a_j, commit)}}
        path = os.path.join(STATE["tmp"], "real_elsewhere.SYNTHETIC_reveal.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(rec, fh)
        self.assertIn(ER.ROADS_REL, F.real_record_problem(path))
        a = argparse.Namespace(road="four_engine", dt=1.0, duration=900.0, seed=0, scored_share=True,
                               horizon_ratio=None, roads_record=path, out=os.path.join(HERE, "runs", "x"),
                               no_preview=False, checkpoint_average=None, lr_schedule="constant", steps=600,
                               engine="b58")
        with mock.patch.object(F, "committed_hash_lines", return_value=(lines["ghassan"], lines["jad"])):
            with self.assertRaisesRegex(SystemExit, "REAL roads record is read only from"):
                train.check_recipe(a)
            with self.assertRaisesRegex(SystemExit, "REAL roads record is read only from"):
                TA.check_four_engine(namespace(road="four_engine", recipe29=True, roads_record=path, steps=600))


# =====================================================================================================
class Wrapper(unittest.TestCase):
    def test_both_networks_get_the_drawn_c_turb_on_a_new_record(self):
        plant = plant_of("honda_l15b7")
        c0 = float(plant.engine.thermal.c_turb)
        w = wrapper("honda_l15b7", seed=4)
        scales = []
        for i in range(40):
            w.reset(seed=4 if i == 0 else None)
            base = w.unwrapped
            scales.append(w.c_turb_scale)
            with self.subTest(episode=i):
                self.assertEqual(base.thermal.p.c_turb, c0 * w.c_turb_scale)
                self.assertEqual(base.thermal_base.p.c_turb, c0 * w.c_turb_scale)
                self.assertIsNot(base.thermal.p, plant.engine.thermal)
                self.assertEqual(float(plant.engine.thermal.c_turb), c0)
        self.assertTrue(min(scales) >= 0.75 and max(scales) <= 1.333 and len(set(scales)) == 40)

    def test_a_seeded_reset_restarts_and_an_unseeded_one_continues(self):
        w = wrapper("b58", seed=6)
        a = [r["c_turb_scale"] for _, r in episodes(w, 4, seed=6)]
        b = [r["c_turb_scale"] for _, r in episodes(w, 4, seed=6)]
        c = [r["c_turb_scale"] for _, r in episodes(w, 4, seed=7)]
        self.assertEqual(a, b)
        self.assertEqual(len(set(a)), 4)
        self.assertNotEqual(a, c)

    def test_the_environment_reads_the_drawn_road(self):
        w = wrapper("ford_27tt", seed=2, record=STATE["record"])
        for i in range(3):
            obs, info = w.reset(seed=2 if i == 0 else None)
            base = w.unwrapped
            with self.subTest(episode=i):
                self.assertEqual(obs[9], np.float32((base.cycle["t_amb"] - 293.0) / 15.0))
                self.assertEqual(base.v, float(base.cycle["v_mps"][0]))
                self.assertEqual(info["road"], w.road)
                self.assertEqual(w.road_log[-1].split()[0], w.road["kind"])
        self.assertTrue(w.road_log[0].startswith("scored SYNTHETIC"))

    def test_train_build_env_four_engine(self):
        import train
        env = train.build_env(True, 3, 900.0, "four_engine", 1.0, plant=plant_of("b58"),
                              scored_share=True, roads_record=STATE["record"])
        env.reset(seed=3)
        self.assertEqual(env.get_wrapper_attr("road_log")[0].split()[:2], ["scored", "SYNTHETIC"])
        self.assertEqual(train.DESIGN_DT["four_engine"], 1.0)
        with self.assertRaises(ValueError):
            train.build_env(True, 3, 900.0, "extremes", 1.0, plant=plant_of("b58"), scored_share=False,
                            roads_record=None)
        # F4: the four-engine road's two options are both named, never a bare KeyError
        for opts in ({}, dict(scored_share=False), dict(roads_record=None),
                     dict(scored_share=False, roads_record=None, extra=1)):
            with self.subTest(options=sorted(opts)):
                with self.assertRaisesRegex(ValueError, "needs both of its options"):
                    train.build_env(True, 3, 900.0, "four_engine", 1.0, plant=plant_of("b58"), **opts)


# =====================================================================================================
class Requests(unittest.TestCase):
    def test_requests_equal_env_step_on_every_engine(self):
        """Each engine's first general episode (150 steps: the launch, the first ramps) and the Honda's and
        the Ford's first SYNTHETIC share episode (100 steps), through env.step with the neutral action:
        the torque request and the engine speed equal requests()' element for element."""
        tasks = [("verify", e, dict(seed=9001, steps=150, scored_share=False, roads_record=None))
                 for e in ENGINE_IDS]
        tasks += [("verify", e, dict(seed=9001, steps=100, scored_share=True, roads_record=STATE["record"]))
                  for e in ("honda_l15b7", "ford_27tt")]
        import multiprocessing as mp
        with mp.get_context("spawn").Pool(4) as pool:
            res = pool.map(F._measure_task, tasks)
        self.assertEqual([n for _, _, n in res], [150] * 4 + [100, 100])

    def test_the_counts_can_fail(self):
        """Mistake 12: a deliverable table of zeros counts every positive request as above it, and a floor
        of 1e9 Nm counts every step below it; the real counts are smaller on the same episode."""
        w = wrapper("honda_l15b7", seed=12)
        w.reset(seed=12)
        base = w.unwrapped
        real = F.episode_counts(base)
        tq, _, _ = F.requests(base)
        zero = property(lambda self: ((0, 0.0), (10000, 0.0)))
        with mock.patch.object(type(base.veh), "DELIVERABLE_TORQUE", zero):
            self.assertEqual(F.episode_counts(base)["above_deliverable"], int(np.count_nonzero(tq > 0.0)))
        stand_in = types.SimpleNamespace(cycle=base.cycle, dt=base.dt, veh=base.veh, plant=types.SimpleNamespace(
            engine=types.SimpleNamespace(loop=types.SimpleNamespace(torque_floor_nm=1e9))))
        self.assertEqual(F.episode_counts(stand_in)["below_floor"], real["steps"])
        self.assertLess(real["above_deliverable"], int(np.count_nonzero(tq > 0.0)))
        self.assertLess(real["below_floor"], real["steps"])
        r, t = zip(*base.veh.DELIVERABLE_TORQUE)
        rpm = np.linspace(900.0, 6000.0, 50)
        self.assertTrue(np.array_equal(F.deliverable_nm(base, rpm), [base.veh.deliverable_nm(x) for x in rpm]))

    def test_the_measurement_SYNTHETIC(self):
        res = F.measure(["b58"], seeds=[9002], episodes=11, scored_share=True, roads_record=STATE["record"],
                        verify_steps=0, jobs=1)
        r = res["engines"]["b58"]
        self.assertEqual((r["all"]["episodes"], r["general"]["episodes"], r["scored"]["episodes"]), (11, 9, 2))
        self.assertEqual(r["all"]["steps"], 11 * 899)
        for part in ("all", "general", "scored"):
            s = r[part]
            with self.subTest(part=part):
                self.assertLessEqual(s["either"]["steps"], s["below_floor"]["steps"] + s["above_deliverable"]["steps"])
                self.assertLessEqual(s["negative"]["steps"], s["below_floor"]["steps"])
        self.assertGreater(r["scored"]["above_coverage_kmh"]["share"], 0.97)
        self.assertTrue(res["same_arrays_on_every_engine"])
        lines = F.report_lines(res, label="SYNTHETIC")
        self.assertIn("SYNTHETIC", lines[0])

    def test_a_SYNTHETIC_measurement_is_not_written_into_the_repository(self):
        with self.assertRaises(SystemExit):
            F.main(["measure", "--engine", "b58", "--seeds", "1", "--episodes", "1", "--synthetic-roads-seed",
                    str(SYNTHETIC_ROADS_SEED), "--out", os.path.join(HERE, "measure.SYNTHETIC.json")])
        self.assertFalse(os.path.exists(os.path.join(HERE, "measure.SYNTHETIC.json")))


# =====================================================================================================
class Recipe(unittest.TestCase):
    def test_the_last_third(self):
        s = TR.LastThird(3e-4)
        for p, want in ((1.0, 3e-4), (0.5, 3e-4), (1 / 3, 3e-4), (0.0, 0.0)):
            with self.subTest(progress_remaining=p):
                self.assertEqual(s(p), want)
        self.assertAlmostEqual(s(1 / 6), 1.5e-4, places=18)
        self.assertLess(s(0.2), s(0.3))
        self.assertIs(TR.learning_rate("constant", 3e-4), 3e-4)
        self.assertIsInstance(TR.learning_rate("last-third", 3e-4), TR.LastThird)
        with self.assertRaises(ValueError):
            TR.learning_rate("cosine", 3e-4)

    def test_the_snapshot_steps(self):
        import train
        self.assertEqual(TR.snapshot_steps(450_000, TR.DECISION_29_WINDOW),
                         [410_000, 420_000, 430_000, 440_000, 450_000])
        self.assertEqual(TR.DECISION_29_WINDOW // train.CHUNK, TR.AVERAGE_SNAPSHOTS)
        self.assertEqual(TR.snapshot_steps(1000, 500), [600, 700, 800, 900, 1000])
        for total, window in ((1000, 2000), (1000, 501), (1000, 0), (1000, -5)):
            with self.subTest(total=total, window=window):
                with self.assertRaises(ValueError):
                    TR.snapshot_steps(total, window)

    def test_the_manifest_refuses_a_changed_or_missing_snapshot(self):
        d = tempfile.mkdtemp(prefix="manifest_", dir=STATE["tmp"])
        os.makedirs(os.path.join(d, TR.SNAPSHOT_DIR))
        for s in TR.snapshot_steps(1000, 500):
            with open(os.path.join(d, TR.SNAPSHOT_DIR, TR.snapshot_name(s)), "wb") as fh:
                fh.write(f"snapshot {s}".encode())
        man = TR.write_manifest(d, total_steps=1000, window=500)
        self.assertEqual(TR.read_manifest(d), man)
        p = os.path.join(d, TR.SNAPSHOT_DIR, TR.snapshot_name(800))
        with open(p, "ab") as fh:
            fh.write(b"!")
        with self.assertRaises(ValueError):
            TR.read_manifest(d)
        os.remove(p)
        with self.assertRaises(FileNotFoundError):
            TR.write_manifest(d, total_steps=1000, window=500)


# =====================================================================================================
def run_train(argv, timeout=900):
    p = subprocess.run([sys.executable, "-B", "train.py", *argv], cwd=HERE, env=ENV, capture_output=True,
                       text=True, timeout=timeout)
    return p.returncode, p.stdout + p.stderr


class TrainRefusals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tmp = STATE["tmp"]
        rec, trec = STATE["record"], STATE["tau_record"]
        base = ["--engine", "b58", "--steps", "600", "--seed", "0", "--device", "cpu"]
        cls.outs = {}
        cases = {
            "share_without_record": base + ["--road", "four_engine", "--scored-share"],
            "record_without_flag": base + ["--road", "four_engine", "--roads-record", rec],
            "share_off_the_road": base + ["--road", "extremes", "--scored-share", "--roads-record", rec],
            "another_step": base + ["--road", "four_engine", "--dt", "0.2"],
            "SYNTHETIC_into_the_repository": base + ["--road", "four_engine", "--scored-share", "--roads-record",
                                                     rec, "--out", os.path.join(HERE, "runs_SYNTHETIC_probe")],
            "H_before_the_plant_commit": base + ["--road", "four_engine", "--horizon-ratio", "1.5",
                                                 "--roads-record", trec],
            "H_on_the_blinded_arm": base + ["--road", "four_engine", "--horizon-ratio", "0.5", "--no-preview",
                                            "--roads-record", trec],
            "a_ratio_the_record_lacks": base + ["--road", "four_engine", "--horizon-ratio", "0.75",
                                                "--roads-record", trec],
            "window_longer_than_the_run": base + ["--road", "four_engine", "--checkpoint-average", "50000"],
            "window_not_five_snapshots": base + ["--road", "four_engine", "--checkpoint-average", "501"],
            "x2_is_closed": base + ["--road", "wideair"],
            "a_frozen_twenty_seed": [x if x != "0" else "1007" for x in base] + ["--road", "four_engine"],
        }
        for name in cases:
            out = os.path.join(tmp, "refused", name, "wideair_dt1" if name == "x2_is_closed" else "out")
            cls.outs[name] = os.path.join(HERE, "runs_SYNTHETIC_probe") if "--out" in cases[name] else out
            if "--out" not in cases[name]:
                cases[name] = cases[name] + ["--out", out]
        with ThreadPoolExecutor(max_workers=4) as pool:
            cls.result = dict(zip(cases, pool.map(run_train, cases.values())))

    def check(self, name, *phrases):
        rc, out = self.result[name]
        self.assertNotEqual(rc, 0, out[-3000:])
        self.assertNotIn("Traceback", out, out[-3000:])
        for ph in phrases:
            self.assertIn(ph, out, out[-3000:])
        self.assertFalse(os.path.exists(self.outs[name]), self.outs[name])

    def test_the_share_needs_a_record(self):
        self.check("share_without_record", "REFUSING", "the scored share needs roads_seed")

    def test_a_record_needs_a_flag(self):
        self.check("record_without_flag", "REFUSING", "nothing would read it")

    def test_the_share_is_the_four_engine_roads(self):
        self.check("share_off_the_road", "REFUSING", "belong to the four-engine roads")

    def test_the_four_engine_roads_run_at_dt_1(self):
        self.check("another_step", "REFUSING", "900 s at dt 1")

    def test_a_SYNTHETIC_share_never_trains_into_the_repository(self):
        self.check("SYNTHETIC_into_the_repository", "REFUSING", "SYNTHETIC roads record", "inside the repository")

    def test_every_H_but_30_s_waits_for_the_plant_commit(self):
        self.check("H_before_the_plant_commit", "REFUSING --horizon-ratio 1.5 on b58", "engine_env.PREVIEW_S",
                   "row 94's plant commit")
        self.assertIsNone(F.preview_h_problem(30.0))
        self.assertIsNone(F.preview_h_problem(None))
        self.assertIsNotNone(F.preview_h_problem(30.000001))

    def test_the_blinded_arm_takes_no_H(self):
        self.check("H_on_the_blinded_arm", "REFUSING", "blinded agent sees no grade ahead")

    def test_the_ratios_are_the_records(self):
        self.check("a_ratio_the_record_lacks", "REFUSING", "is not one of the roads record's ratios")

    def test_the_average_window(self):
        self.check("window_longer_than_the_run", "REFUSING", "--checkpoint-average 50000")
        self.check("window_not_five_snapshots", "REFUSING", "a multiple of 5")

    def test_x2s_directory_is_closed(self):
        self.check("x2_is_closed", "REFUSING", "is X2's, a closed experiment")

    def test_a_training_seed_row_96_reserves_is_refused(self):
        """Row 96 (R0-3, S9): the training seeds avoid the frozen twenty, D2's practice set and the
        practice episodes, read from their definitions; train.py and train_all.py refuse them."""
        import train_all as TA
        self.check("a_frozen_twenty_seed", "REFUSING --seed 1007", "the frozen twenty")
        res = F.reserved_seeds()
        self.assertEqual([tuple(sorted(v)) for v in res.values()],
                         [tuple(range(1000, 1020)), tuple(range(3000, 3010)), tuple(range(4000, 4010))])
        self.assertIsNone(F.reserved_seed_problem([0, 1, 999, 1020, 2999, 3010, 3999, 4010, 9000]))
        for s in (1000, 1019, 3000, 3009, 4000, 4009):
            with self.subTest(seed=s):
                self.assertIsNotNone(F.reserved_seed_problem([0, s]))
                with self.assertRaisesRegex(SystemExit, "REFUSING --seeds on the four-engine roads"):
                    TA.check_four_engine(namespace(road="four_engine", seeds=[0, s]))
        self.assertIsNone(TA.check_four_engine(namespace(road="extremes", seeds=[1000])))


# =====================================================================================================
class TrainSmoke(unittest.TestCase):
    """The two smoke runs ORDER step 7 asks for, into temporary folders, deleted with the module's."""

    @classmethod
    def setUpClass(cls):
        tmp = STATE["tmp"]
        cls.plain, cls.full = os.path.join(tmp, "smoke_plain"), os.path.join(tmp, "smoke_full")
        runs = [["--engine", "b58", "--road", "four_engine", "--steps", "600", "--seed", "0", "--device", "cpu",
                 "--out", cls.plain],
                ["--engine", "b58", "--road", "four_engine", "--steps", "1000", "--seed", "0", "--device", "cpu",
                 "--lr-schedule", "last-third", "--scored-share", "--roads-record", STATE["record"],
                 "--checkpoint-average", "500", "--out", cls.full]]
        with ThreadPoolExecutor(max_workers=2) as pool:
            cls.result = list(pool.map(run_train, runs))

    def _json(self, *parts):
        with open(os.path.join(*parts), encoding="utf-8") as fh:
            return json.load(fh)

    def test_at_x1s_defaults_nothing_of_the_recipe_runs(self):
        rc, out = self.result[0]
        self.assertEqual(rc, 0, out[-3000:])
        run = os.path.join(self.plain, "sighted_seed0")
        meta, cfg = self._json(run, "meta.json"), self._json(run, "config.json")
        self.assertEqual(meta["train_road"], "four_engine")
        self.assertEqual(meta["train_road_sha"], F.code_sha())
        self.assertNotIn("train_recipe", meta)
        self.assertEqual(cfg["recipe"], dict(lr_schedule="constant", scored_share=None, checkpoint_average=None,
                                             horizon_ratio=None, preview_h_s=None, learning_rate_at_end=3e-4))
        self.assertFalse(os.path.exists(os.path.join(run, TR.SNAPSHOT_DIR)))
        self.assertFalse(os.path.exists(os.path.join(run, TR.MANIFEST)))
        rec = np.load(os.path.join(run, "train_record.npz"))
        c, scale = F.general_episode(F.general_rng(0))
        c0 = float(plant_of("b58").engine.thermal.c_turb)
        self.assertTrue(np.allclose(rec["t_amb_c"], c["t_amb"] - 273.15, rtol=0, atol=1e-4))
        self.assertTrue(np.all(rec["c_turb"] == np.float32(c0 * scale)))
        self.assertTrue(np.allclose(rec["v_kmh"], np.asarray(c["v_mps"])[:600] * 3.6, rtol=0, atol=1e-3))

    def test_SYNTHETIC_with_every_recipe_flag_on(self):
        rc, out = self.result[1]
        self.assertEqual(rc, 0, out[-3000:])
        run = os.path.join(self.full, "sighted_seed0")
        meta, cfg = self._json(run, "meta.json"), self._json(run, "config.json")
        rr = F.read_roads_record(STATE["record"])
        self.assertEqual(meta["train_recipe"], dict(lr_schedule="last-third", checkpoint_average=500,
                                                    scored_share=dict(every=10, roads_sha=rr["roads_sha"],
                                                                      seed_kind="SYNTHETIC")))
        self.assertEqual(cfg["recipe"]["learning_rate_at_end"], 0.0)
        # the first episode (steps 1-899) is the share's road, the second the general stream's first
        rec = np.load(os.path.join(run, "train_record.npz"))
        share_c, share_scale, _ = F.share_episode(F.share_rng(SYNTHETIC_ROADS_SEED, 0), seed=0)
        gen_c, gen_scale = F.general_episode(F.general_rng(0))
        c0 = np.float32(float(plant_of("b58").engine.thermal.c_turb) * share_scale)
        first, second = rec["step"] <= 899, rec["step"] > 899
        self.assertTrue(np.allclose(rec["t_amb_c"][first], ER.T_AMB_K - 273.15, atol=1e-4))
        self.assertTrue(np.all(rec["c_turb"][first] == c0))
        self.assertTrue(np.allclose(rec["t_amb_c"][second], gen_c["t_amb"] - 273.15, atol=1e-4))
        self.assertTrue(np.all(rec["c_turb"][second] == np.float32(float(plant_of("b58").engine.thermal.c_turb)
                                                                    * gen_scale)))
        self.assertTrue(np.allclose(rec["grade"][first], np.asarray(share_c["grade"])[:899], atol=1e-6))
        # the learning rate the last update used, as the saved optimizer holds it
        import torch
        import zipfile
        z = zipfile.ZipFile(os.path.join(run, "final.zip"))
        opt = torch.load(__import__("io").BytesIO(z.read("actor.optimizer.pth")), map_location="cpu",
                         weights_only=True)
        self.assertEqual([g["lr"] for g in opt["param_groups"]], [0.0])
        # the five snapshots, the manifest, and the average is their mean
        man = TR.read_manifest(run)
        self.assertEqual([s["step"] for s in man["snapshots"]], [600, 700, 800, 900, 1000])
        avg = TR.AveragedPolicy.load(run)
        from stable_baselines3 import SAC
        singles = [SAC.load(os.path.join(run, *s["path"].split("/")), device="cpu",
                            custom_objects={"learning_rate": 0.0, "lr_schedule": lambda _: 0.0})
                   for s in man["snapshots"]]
        obs = rec["obs"][[0, 300, 950]].astype(np.float32)
        for o in obs:
            want = np.mean([np.asarray(m.predict(o, deterministic=True)[0], np.float64) for m in singles], axis=0)
            got, state = avg.predict(o, deterministic=True)
            self.assertIsNone(state)
            self.assertTrue(np.array_equal(got, want.astype(np.float32)))
        acts = np.stack([m.predict(obs[0], deterministic=True)[0] for m in singles])
        self.assertGreater(np.ptp(acts, axis=0).max(), 0.0)      # the snapshots differ: an average, not a copy
        with self.assertRaises(ValueError):
            avg.predict(obs[0], deterministic=False)
        print("\n[SYNTHETIC smoke, every recipe flag] " + "; ".join(
            ln.strip() for ln in out.splitlines() if ln.startswith(("recipe", "  checkpoint average"))))


# =====================================================================================================
def namespace(**kw):
    d = dict(engine="b58", road="extremes", dt=1.0, steps=50_000, seeds=[0, 1], device="cpu", out="runs/x",
             no_resume=False, keep_buffer=False, third_arm=False, recipe29=False, roads_record=None, ratios=None)
    d.update(kw)
    return argparse.Namespace(**d)


def old_commands(a):
    """train_all.py's commands as it built them before 31 October 2026 (22561da), line for line."""
    out = []
    for s, blind in [(s, blind) for s in a.seeds for blind in (False, True)]:
        tag = f"{'blind' if blind else 'sighted'}_seed{s}"
        cmd = [sys.executable, "train.py", "--engine", a.engine, "--road", a.road, "--dt", f"{a.dt:g}",
               "--steps", str(a.steps), "--seed", str(s), "--device", a.device, "--out", a.out]
        if blind:
            cmd.append("--no-preview")
        if a.no_resume:
            cmd.append("--no-resume")
        if a.keep_buffer:
            cmd.append("--keep-buffer")
        out.append((tag, cmd))
    return out


class TrainAll(unittest.TestCase):
    def test_the_pair_is_built_as_before(self):
        import train_all as TA
        for kw in ({}, dict(no_resume=True), dict(keep_buffer=True), dict(road="wideair", seeds=[0, 1, 2, 3, 4]),
                   dict(road="four_engine")):
            a = namespace(**kw)
            with self.subTest(**kw):
                self.assertEqual(TA.commands(a, None), old_commands(a))

    def test_the_third_arm_SYNTHETIC(self):
        import train_all as TA
        rec = F.read_roads_record(STATE["tau_record"])
        a = namespace(road="four_engine", seeds=[0, 1], third_arm=True, roads_record=rec["path"])
        cmds = TA.commands(a, rec)
        self.assertEqual([t for t, _ in cmds], ["sighted_r0.5_seed0", "sighted_r1.5_seed0", "sighted_r0.5_seed1",
                                                "sighted_r1.5_seed1", "blind_seed0", "blind_seed1"])
        for tag, cmd in cmds:
            with self.subTest(tag=tag):
                if tag.startswith("blind"):
                    self.assertIn("--no-preview", cmd)
                    self.assertNotIn("--horizon-ratio", cmd)
                    self.assertNotIn("--roads-record", cmd)
                else:
                    r = cmd[cmd.index("--horizon-ratio") + 1]
                    self.assertEqual(tag, f"sighted_r{float(r):g}_seed{cmd[cmd.index('--seed') + 1]}")
                    self.assertEqual(cmd[cmd.index("--roads-record") + 1], rec["path"])
        a29 = namespace(road="four_engine", seeds=[0], third_arm=True, recipe29=True, roads_record=rec["path"])
        for tag, cmd in TA.commands(a29, rec):
            with self.subTest(tag=tag, recipe29=True):
                for flag in ("--scored-share", "--roads-record"):
                    self.assertIn(flag, cmd)
                self.assertEqual(cmd[cmd.index("--lr-schedule") + 1], "last-third")
                self.assertEqual(cmd[cmd.index("--checkpoint-average") + 1], "50000")

    def test_the_third_arm_at_some_ratios_SYNTHETIC(self):
        """--ratios 1.5 (decision 29's pilot under A+G, row 112: the blinded arm and r = 1.5) trains the
        sighted arm at that ratio only; a ratio the record lacks, a repeated one, or --ratios without the
        third arm is refused (S10)."""
        import train_all as TA
        rec = F.read_roads_record(STATE["tau_record"])
        a = namespace(road="four_engine", seeds=[0, 1], third_arm=True, roads_record=rec["path"], ratios=[1.5])
        self.assertEqual([t for t, _ in TA.commands(a, rec)],
                         ["sighted_r1.5_seed0", "sighted_r1.5_seed1", "blind_seed0", "blind_seed1"])
        lines, problems = TA.third_arm_problems(a, rec)
        self.assertEqual(len(problems), 1)
        self.assertTrue(any("r = 1.5" in x for x in lines) and not any("r = 0.5" in x for x in lines))
        for bad in ([0.75], [1.5, 1.5]):
            with self.subTest(ratios=bad):
                with self.assertRaisesRegex(SystemExit, "REFUSING --ratios"):
                    TA.check_four_engine(namespace(road="four_engine", third_arm=True, roads_record=rec["path"],
                                                   ratios=bad, out=os.path.join(STATE["tmp"], "ratios")))
        with self.assertRaisesRegex(SystemExit, "--ratios without --third-arm"):
            TA.check_four_engine(namespace(road="four_engine", recipe29=True, roads_record=rec["path"],
                                           ratios=[1.5]))

    def test_every_engines_H_is_row_102s_and_waits_for_the_plant_commit_SYNTHETIC(self):
        """H = r tau from the SYNTHETIC record whose tau is the roads code's, on every engine: the preview
        steps are row 102's (the decision's text, pinned here), and every H is refused today."""
        import train_all as TA
        rec = F.read_roads_record(STATE["tau_record"])
        row_102 = {"b58": ([1, 3, 11, 23], [4, 11, 35, 71]), "mazda_25t": ([1, 3, 10, 21], [4, 10, 32, 64]),
                   "honda_l15b7": ([1, 3, 11, 23], [4, 11, 35, 71]), "ford_27tt": ([2, 5, 16, 33], [6, 16, 50, 100])}
        table = []
        for e in ENGINE_IDS:
            lines, problems = TA.third_arm_problems(namespace(engine=e, road="four_engine"), rec)
            table += lines
            with self.subTest(engine=e):
                self.assertEqual(len(problems), 2)
                self.assertEqual([F.preview_steps(F.horizon_s(rec, e, r), dt=1.0) for r in (0.5, 1.5)],
                                 list(row_102[e]))
                self.assertEqual(F.horizon_s(rec, e, 1.5), 1.5 * STATE["taus"][e])
        print("\n" + "\n".join(table))

    def test_the_third_arm_is_refused_before_any_run_SYNTHETIC(self):
        out = os.path.join(STATE["tmp"], "third_arm")
        p = subprocess.run([sys.executable, "-B", "train_all.py", "--engine", "b58", "--road", "four_engine",
                            "--device", "cpu", "--third-arm", "--roads-record", STATE["tau_record"], "--seeds", "0",
                            "--steps", "600", "--out", out], cwd=HERE, env=ENV, capture_output=True, text=True,
                           timeout=600)
        text = p.stdout + p.stderr
        self.assertNotEqual(p.returncode, 0, text[-3000:])
        self.assertIn("REFUSING the third arm, before any run starts", text)
        self.assertIn("r = 1.5: tau 47.3351 s, H = 71.0026 s", text)
        self.assertNotIn("Traceback", text)
        self.assertFalse(os.path.exists(out))

    def test_train_all_refusals(self):
        import train_all as TA
        with self.assertRaises(SystemExit):
            TA.check_four_engine(namespace(road="four_engine", roads_record=STATE["record"]))
        with self.assertRaises(SystemExit):
            TA.check_four_engine(namespace(road="extremes", third_arm=True, roads_record=STATE["tau_record"]))
        with self.assertRaises(SystemExit):
            TA.check_four_engine(namespace(road="four_engine", recipe29=True, roads_record=STATE["record"],
                                           out=os.path.join(STATE["tmp"], "r29"), steps=600))
        self.assertIsNone(TA.check_four_engine(namespace()))


# =====================================================================================================
class Isolation(unittest.TestCase):
    # this commit's code (ORDER step 7, C1): new modules and the changed ones it may change
    NEW = ("four_engine_roads", "training_recipe", "train", "train_all", "engine_gate", "four_engine_analysis",
           "benchmark_training", "check_training_device", "test_reward", "check_roads")
    TESTS = ("test_four_engine_training", "test_device_gate", "test_four_engine_analysis")
    # The 35 files roads.json hashes (ORDER step 7's task, rows 97 and 121), pinned: a hashed module
    # that came to import anything else would grow epa_roads.hashed_files and fail here
    ROADS_JSON_35 = (
        "check_premise.py derived.py engine_env.py engine_specs/a90_supra.toml engine_specs/accord_2018.toml "
        "engine_specs/b58.toml engine_specs/cars/accord_2018_15t.toml engine_specs/cars/cx9_2016_25t.toml "
        "engine_specs/cars/f150_2015_27tt.toml engine_specs/cx9_2016.toml engine_specs/f150_2015.toml "
        "engine_specs/ford_27tt.toml engine_specs/honda_l15b7.toml engine_specs/mazda_25t.toml engines.py "
        "epa_coefficients.py epa_fit.py epa_freeze.py epa_roads.py epa_rows.py epa_stats.py evaluate.py "
        "fingerprint.py k3_knee.py plant.py preview_ceiling.py random_road.py roads_ceiling.py step_record.py "
        "thermal.py thresholds/__init__.py thresholds/common.py thresholds/contract.py thresholds/ecu_shift.py "
        "thresholds/split.py").split()
    # tracked before this commit, and already ending in a plant file's name (thermal.py): fingerprint's
    # suffix match lists thermal.py dirty whenever either is modified; known, and not this commit's
    SUFFIX_KNOWN = ("calibrate_thermal.py", "car_thermal.py")

    def test_the_hashed_list_is_the_35_and_closed_under_import(self):
        """R0-5: epa_roads.hashed_files is the 35 files; every hashed module's import closure (any depth,
        any nesting: epa_roads.import_closure) lies inside it; none of this commit's files is in it."""
        files = ER.hashed_files(root=HERE, engines=ER.ENGINES)
        self.assertEqual(sorted(files), sorted(self.ROADS_JSON_35))
        closure = set()
        for rel in files:
            if rel.endswith(".py"):
                closure.update(ER.import_closure(rel, root=HERE))
        self.assertLessEqual(closure, set(files), sorted(closure - set(files)))
        for name in self.NEW + self.TESTS:
            self.assertNotIn(f"{name}.py", files)

    def test_no_new_file_ends_in_a_plant_files_name(self):
        """R0-1 (S8): fingerprint.py lists a plant file in git_dirty_plant_files when any dirty path ENDS
        with its name, so a file named like analyse_four_engines.py marked engines.py dirty. No path in
        the tree ends with a plant file's name unless it is that file, or one of the two known before."""
        import fingerprint as FP
        names = set()
        for e in engines.PLANTS:
            names.update(FP.plant_files(e))
        p = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=HERE, capture_output=True,
                           text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        paths = p.stdout.split()
        self.assertGreater(len(paths), 100)
        bad = sorted({q for q in paths for n in names if q.endswith(n) and q != n} - set(self.SUFFIX_KNOWN))
        self.assertEqual(bad, [])
        for name in self.NEW + self.TESTS:
            with self.subTest(file=name):
                self.assertFalse(any(f"{name}.py".endswith(n) for n in names))

    def test_no_hashed_module_imports_the_training_code(self):
        """Row 121: the new code imports the frozen code, never the other way round, and none of it is in
        roads.json's list (epa_roads.hashed_files)."""
        files = ER.hashed_files(root=HERE, engines=ER.ENGINES)
        for new in self.NEW:
            self.assertNotIn(f"{new}.py", files)
        py = [rel for rel in files if rel.endswith(".py")]          # the engine specs (.toml) import nothing
        self.assertGreater(len(py), 20)
        for rel in py:
            with open(os.path.join(HERE, rel), encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names |= {a.name.split(".")[0] for a in node.names}
                elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                    names.add(node.module.split(".")[0])
            with self.subTest(file=rel):
                self.assertEqual(names & set(self.NEW), set())


if __name__ == "__main__":
    unittest.main(verbosity=2)

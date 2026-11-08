"""test_device_gate.py -- the device and gate code of ORDER step 7 (commit C1): benchmark_training.py's
--engine and --road, tools/run_l8.sh, and the per-engine gate of test_reward.py and check_roads.py
(engine_gate.py).

    python -B test_device_gate.py        a few minutes; exit code 0 when all pass

Nothing here trains: every train.py below is run with --help, and the rollouts are the gate's own,
neutral, on decision 34's generator at SYNTHETIC seeds (no roads_seed exists; row 96). Roads' REAL-record
test (Qa) reads the committed results/EPA_ROADS/roads.json and redraws.json, prints nothing of them and
rolls nothing out on them; its control writes roads.json's seed_kind, roads and H_table alone (never its
commit_reveal) to a temporary folder outside the repository, removed when the test ends.

  Sweep        the 0.05 % sweep's grades; notches, band and kickdown on hand-made rows; on the plants,
               the B58's kickdown to 6th where test_reward.py measured it (13.96-13.97 % in 0.01 %
               steps, the comment above D2_ROADS), the Ford's to 3rd inside the C5 failures of the roads step's own
               sweep (results/EPA_ROADS/sweep.txt: 11.20-11.80 %), the Accord's branches by its law
               (CvtVehicle.ratio_for), each box's top gear at 0 %; a scenario that is not decision
               34's refused
  Roads        one source of decision 34's roads; a roads record's roads and horizons; the repository's
               REAL roads.json read as decision 34's scored set through fingerprint.d34_roads, version
               6's redrawn twenty with that record's own H_table, by its absolute path and by Q's
               relative one, the same REAL record anywhere else refused by its text and a SYNTHETIC
               record there read as it stands (Qa, ORDER step 14a, row 146 (1)); the onset twin;
               an H other than 30 s admitted since the plant commit P, each H's preview samples
               engine_env.preview_samples' (row 117), 0 s and -1 s refused; the starver is
               test_reward's; row 116's road built with the options train.py gives it; with a
               SYNTHETIC roads record the share on (C1b, row 130 (5)), the record required of every
               training check, named repository-relative in what is printed and recorded (the tasks
               alone read its absolute path), and check_roads.py's default file named for the share
               and the knock option
  Knock        the plant commit P (row 127 (4)): every environment the gate builds takes the task's
               reward_knock, the band and notch jobs' own SupervisoryTunerEnv among them (a knock-out
               task builds False, the knock-in control True); an AST scan finds every builder call and
               every task base passing it, with its control; the gate's header names it
  BlindArm     check_random_road.py B at H = 30 s on the B58 (SYNTHETIC road): the blinded traces do
               not differ before the grades, the sighted ones differ 30 steps before, and that sighted
               pair is the control that the blind criterion can fail (mistake 12)
  Verdict      the gate's exit code: 0 only when every check ran and passed; NOT COMPLETE when one
               did not run; SYNTHETIC said; the share named on row 116's road, and run_gate returning
               the record it ran with, not its last check's name (P)
  Cli          the refusals of test_reward.py, check_roads.py and benchmark_training.py (no default
               engine, CLAUDE.md mistake 1; the per-engine options only with --engine; a SYNTHETIC
               table only outside the repository); a road train.py does not have refused by the
               benchmark's probe; C1b's options (--roads-record on row 116's road only, the benchmark's
               --reward-knock required there and refused before the plant commit P, neither with
               --merge), and no --table-record (row 136: no table is built); test_reward.py's and
               check_roads.py's --reward-knock, required with --engine as the last check and refused
               without it (P). (benchmark_training.py
               --selftest is its own command: its hung-run case kills its child at a 2 s deadline, which
               a loaded machine can miss.)
  Scans        test_engine_threading's call, default and name scans on the new and changed files
  RunbookB1    the runbook's B0 record, B1 blocks and B5's copy, their own text, on a scratch git work
               tree with a stand-in for row 135's interpreter ($PY a refusing one): two engines in a row
               record a clean tree, their attempts numbered in B0's $B1OUT; B0's record lands there,
               written once; a later session's repeat continues the count there, on cuda the CPU
               series runs with $PY under its own names, and B5 copies both sessions' attempts, the CPU
               series' and the B0 record; the controls, the attempts written inside the tree record it
               dirty, the loop and the CPU series run with that $PY run nothing, and B0's record refuses
               a record that differs, a dirty tree and a tree at no commit (C1b)
  RunL8        tools/run_l8.sh: its refusals, and a dry run into a temporary folder (ref/ is git
               archive cf43fbb, tools/ the tarball's two files byte for byte, eleven --help runs exit 0);
               its comparison's judgement (cmp8) on a stand-in tool: a verdict printed AND its exit
               code, so a comparison that crashed is ERROR, never the controls' expected DIFFERENT;
               every interpreter it runs under -I is given -B too (-I ignores PYTHONDONTWRITEBYTECODE)
"""
import contextlib
import dataclasses
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import engine_env as E  # noqa: E402
import engine_gate as G  # noqa: E402
import engines  # noqa: E402
import epa_roads as ER  # noqa: E402

# no bytecode written into the tree by the children (the project runs Python with -B)
ENV = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONIOENCODING="utf-8",
           PYTHONDONTWRITEBYTECODE="1")
PY_FWD = sys.executable.replace(os.sep, "/")       # the interpreter as bash takes it on Windows too
TARBALL = os.path.join(HERE, "results", "B58_IDENTITY", "certificate_tools.tar.gz")


def run(*argv, timeout=900):
    p = subprocess.run([sys.executable, "-B", *argv], cwd=HERE, capture_output=True, text=True, env=ENV,
                       timeout=timeout, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout + p.stderr


def bash():
    return shutil.which("bash")


_SWEEPS = {}


def sweep_of(engine_id):
    if engine_id not in _SWEEPS:
        _SWEEPS[engine_id] = G.sweep(engines.get(engine_id))
    return _SWEEPS[engine_id]


class Sweep(unittest.TestCase):
    def test_the_grades(self):
        g = G.sweep_grades()
        self.assertEqual((len(g), g[0], g[-1]), (361, 0.0, 0.18))
        self.assertTrue(np.allclose(np.diff(g), 0.0005, rtol=0, atol=1e-9))

    def test_notches_band_and_kickdown_on_hand_made_rows(self):
        rows = [dict(grade=x / 100, held=h, margin=0.1)
                for x, h in ((1, "8"), (2, "8"), (3, "7"), (4, "7"), (5, "6"))]
        cuts = G.notches(rows)
        self.assertEqual([(c["grade"], c["below"], c["from"], c["to"]) for c in cuts],
                         [(0.03, 0.02, "8", "7"), (0.05, 0.04, "7", "6")])
        self.assertEqual(G.band_grade(rows), 0.02)
        self.assertIsNone(G.kickdown_threshold(cuts))
        flat = [dict(grade=x / 100, held="6", margin=0.1) for x in range(4)]
        self.assertEqual((G.notches(flat), G.band_grade(flat)), ([], 0.03))
        cvt = [dict(grade=x / 100, held=h, margin=0.1)
               for x, h in ((1, "economy"), (2, "kickdown"), (3, "kickdown"), (4, "power-limited"))]
        self.assertEqual(G.kickdown_threshold(G.notches(cvt)), 0.02)

    def test_the_b58_kicks_down_to_6th_where_test_reward_measured_it(self):
        """test_reward.py, the comment above D2_ROADS: on the merged plant the 7th-to-6th kickdown at
        130 km/h sits between 13.96 and 13.97 % (Vehicle.demand in 0.01 % steps, 29 September); the
        0.05 % grid's first grade past it is 14.00 %."""
        cut = [c for c in G.notches(sweep_of("b58")) if (c["from"], c["to"]) == ("7", "6")]
        self.assertEqual([(c["below"], c["grade"]) for c in cut], [(0.1395, 0.14)])

    def test_the_ford_kicks_down_to_3rd_inside_the_roads_sweeps_c5_failures(self):
        """results/EPA_ROADS/sweep.txt: on the Ford, C5 at 1.9 % fails 11.20-11.80 %, its smallest gated
        margin at 11.50 %: the box's threshold is there."""
        cut = [c for c in G.notches(sweep_of("ford_27tt")) if (c["from"], c["to"]) == ("4", "3")]
        self.assertEqual(len(cut), 1, cut)
        self.assertTrue(0.112 <= cut[0]["grade"] <= 0.118, cut)

    def test_the_accords_branches_are_its_laws(self):
        p = engines.get("honda_l15b7")
        rows = sweep_of("honda_l15b7")
        veh = E.vehicle_for(p.car)
        sc = p.scenario
        rho = ER.P_BARO_KPA * 1000.0 / (287.0 * float(sc.t_amb))
        v = float(sc.v_kmh) / 3.6

        def branch(grade):
            return veh.ratio_for(v, veh.road_force_n(v, grade, rho=rho))[2]
        kd = G.kickdown_threshold(G.notches(rows))
        band = G.band_grade(rows)
        self.assertIsNotNone(kd)
        self.assertEqual((branch(band), branch(kd)), ("economy", "kickdown"))
        self.assertAlmostEqual(kd - band, G.SWEEP_STEP, places=9)
        self.assertEqual(all(r["held"] == branch(r["grade"]) for r in rows), True)

    def test_each_stepped_box_holds_its_top_gear_on_the_flat(self):
        for e in ("b58", "mazda_25t", "ford_27tt"):
            p = engines.get(e)
            veh = E.vehicle_for(p.car)
            with self.subTest(engine=e):
                self.assertEqual(sweep_of(e)[0]["held"], str(veh.gear_for(float(p.scenario.v_kmh) / 3.6) + 1))
                self.assertTrue(G.band_grade(sweep_of(e)) < G.notches(sweep_of(e))[0]["grade"])

    def test_a_scenario_that_is_not_decision_34s_is_refused(self):
        p = engines.get("b58")
        moved = dataclasses.replace(p, scenario=dataclasses.replace(p.scenario, t_amb=300.0))
        with self.assertRaises(ValueError):
            G.sweep(moved)


class Roads(unittest.TestCase):
    def test_one_source_of_decision_34s_roads(self):
        for kw in (dict(roads_file=None, synthetic_seed=None), dict(roads_file="x.json", synthetic_seed=1),
                   dict(roads_file=None, synthetic_seed=-1), dict(roads_file=None, synthetic_seed=2 ** 32)):
            with self.subTest(**kw), self.assertRaises(ValueError):
                G.d34_roads(**kw)
        roads, h, label = G.d34_roads(roads_file=None, synthetic_seed=101)
        self.assertEqual((len(roads), h), (G.SYNTHETIC_ROADS, None))
        self.assertIn("SYNTHETIC", label)
        self.assertEqual(G.horizons(None, "b58"), [30.0])

    def test_a_roads_record_gives_its_roads_and_horizons(self):
        roads = ER.generate(7, n_roads=2)
        h_table = {"b58": {"1.5": {"H_s": 120.0}, "0.5": {"H_s": 40.0}}, "ford_27tt": {"1.5": {"H_s": 100.0}}}
        d = tempfile.mkdtemp(prefix="gate_record_")
        try:
            path = os.path.join(d, "roads.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"roads": roads, "H_table": h_table}, fh)
            got, h, label = G.d34_roads(roads_file=path, synthetic_seed=None)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        self.assertEqual([r["cycle"]["grade"] for r in got], [r["cycle"]["grade"] for r in roads])
        self.assertEqual((G.horizons(h, "b58"), G.horizons(h, "ford_27tt")), ([40.0, 120.0], [100.0]))
        self.assertNotIn("SYNTHETIC", label)

    def test_the_real_record_gives_the_redrawn_twenty_and_its_H_table(self):
        """Qa (ORDER step 14a; interface sheet 9; row 146 (1)): --roads on the repository's REAL roads.json
        gives decision 34's scored set as fingerprint.d34_roads reads it at epa_roads.REPO, redraws.json's
        version-6 reading (the redrawn twenty: k = 0..19 with evaluate.EPISODES' seeds and weights, and
        equal to roads.json's own, since R4's version 6 failed no slot), with roads.json's own H_table, so
        the blind arm runs at the record's H for each of its ratios; the label names the reading. The set
        is fingerprint.d34_roads' own object (a spy wraps it). It is so for the path as Q's commands give
        it (ORDER step 17; interface sheet 9), results/EPA_ROADS/roads.json relative to the repository as
        the working folder, and for the absolute path given from a working folder outside the repository.
        The record is read, never printed, and nothing is rolled out. The controls (mistake 12): the same
        REAL record, its seed_kind, roads and H_table alone (never its commit_reveal), written outside the
        repository under the same file name, is refused by its text before the set is read; and a
        SYNTHETIC record at that path keeps today's path, its own roads and H_table as they stand, so the
        refusal is the REAL record's alone."""
        import re
        from unittest import mock
        import fingerprint as FP
        path = os.path.join(ER.REPO, *ER.ROADS_REL.split("/"))
        rec = ER.load_record(path)
        self.assertEqual(rec["seed_kind"], "REAL")
        real, seen = FP.d34_roads, []

        def spy(*, root):
            seen.append((root, real(root=root)))
            return seen[-1][1]
        refusal = f"decision 34's roads: a REAL roads record is read only as {ER.ROADS_REL} in this repository"
        d = tempfile.mkdtemp(prefix="gate_real_elsewhere_")
        try:
            with mock.patch.object(FP, "d34_roads", spy):
                with contextlib.chdir(d):            # the absolute path, from a folder outside the repository
                    roads, h, label = G.d34_roads(roads_file=path, synthetic_seed=None)
                with contextlib.chdir(ER.REPO):      # Q's form: the relative path, as its command line gives it
                    roads_q, h_q, label_q = G.d34_roads(roads_file=ER.ROADS_REL, synthetic_seed=None)
                self.assertEqual([root for root, _ in seen], [ER.REPO, ER.REPO])
                other = os.path.join(d, os.path.basename(path))
                with open(other, "w", encoding="utf-8") as fh:       # the REAL record, never its commit_reveal
                    json.dump({key: rec[key] for key in ("seed_kind", "roads", "H_table")}, fh)
                with self.assertRaisesRegex(ValueError, re.escape(refusal)):
                    G.d34_roads(roads_file=other, synthetic_seed=None)
                synthetic = ER.generate(7, n_roads=2)
                h_synthetic = {"b58": {"1.5": {"H_s": 120.0}, "0.5": {"H_s": 40.0}}}
                with open(other, "w", encoding="utf-8") as fh:
                    json.dump({"seed_kind": "SYNTHETIC", "roads": synthetic, "H_table": h_synthetic}, fh)
                got, h2, label2 = G.d34_roads(roads_file=other, synthetic_seed=None)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        self.assertEqual(len(seen), 2)                       # neither control read the scored set
        scenario, want = seen[0][1]
        # assertTrue, not assertIs/assertEqual: a failure would print (and diff) twenty 900-sample roads
        self.assertTrue(roads is want, "d34_roads did not return fingerprint.d34_roads' own roads")
        self.assertTrue(roads_q is seen[1][1][1], "Q's relative path did not give fingerprint.d34_roads' roads")
        self.assertEqual((scenario["seed_kind"], scenario["reading"]), ("REAL", "version 6"))
        episodes = ER.frozen_episodes(root=ER.REPO)
        self.assertEqual([(r["k"], r["episode_seed"], tuple(r["weights"])) for r in roads],
                         [(k, s, w) for k, (s, w) in enumerate(episodes)])
        self.assertTrue(roads == rec["roads"], "row 146 (1): version 6's twenty are not roads.json's")
        self.assertEqual(h, rec["H_table"])
        self.assertEqual(h_q, h)
        self.assertEqual(G.horizons(h, "b58"),
                         sorted(float(rec["H_table"]["b58"][f"{float(r):g}"]["H_s"]) for r in rec["ratios"]))
        self.assertIn(f"{ER.ROADS_REL}, REAL, through fingerprint.d34_roads: {ER.REDRAWS_REL}'s version 6 "
                      f"reading ({len(episodes)} roads)", label)
        self.assertEqual(label_q, label)                    # repository-relative: no machine path in either
        self.assertEqual([r["cycle"]["grade"] for r in got], [r["cycle"]["grade"] for r in synthetic])
        self.assertEqual((h2, G.horizons(h2, "b58")), (h_synthetic, [40.0, 120.0]))
        self.assertNotIn("version 6", label2)

    def test_the_onset_twin(self):
        road = next(r for r in ER.generate(101, n_roads=2) if r["climbs"])
        twin, slot, d = G.onset_twin(road)
        first = min(road["climbs"], key=lambda c: c["onset_s"])
        a, b = np.asarray(road["cycle"]["grade"]), np.asarray(twin["cycle"]["grade"])
        self.assertEqual((slot, d), (first["slot"], int(first["onset_s"]) + 1))
        self.assertTrue(np.array_equal(a[:d], b[:d]) and a[d] != b[d])
        self.assertEqual(ER.ramp_problems(twin["cycle"]["grade"], dt=G.DT), [])
        moved = [c for c in twin["climbs"] if c["slot"] == slot][0]
        self.assertEqual(moved["onset_s"] - first["onset_s"], G.BLIND_SHIFT_S)
        self.assertEqual([c for c in twin["climbs"] if c["slot"] != slot],
                         [c for c in road["climbs"] if c["slot"] != slot])
        self.assertEqual({k: v for k, v in twin["cycle"].items() if k != "grade"},
                         {k: v for k, v in road["cycle"].items() if k != "grade"})
        flat = dict(road, climbs=[])
        with self.assertRaises(ValueError):
            G.onset_twin(flat)

    def test_an_H_other_than_30_s_is_admitted(self):
        """The plant commit P (row 117; interface sheet 6.6): preview_env builds the environment at any H that
        engine_env.preview_samples accepts, with no refusal, its samples H x (1/15, 1/6, 1/2, 1). The control
        (mistake 12): H = 0 and H = -1 are refused, by the environment itself."""
        p = engines.get("b58")
        c = G.notch_cycle(p, 0.10)
        env = G.preview_env(c, plant=p, dt=1.0, use_preview=True, horizon_s=30.0, seed=0, reward_knock=False)
        self.assertEqual((env.use_preview, env.preview_s), (True, E.PREVIEW_S))
        self.assertFalse(hasattr(G, "WaitsForPlantCommit"))
        for h in (29.0, 31.0, 60.0, 130.0):
            with self.subTest(H=h):
                env = G.preview_env(c, plant=p, dt=1.0, use_preview=False, horizon_s=h, seed=0, reward_knock=False)
                self.assertEqual(env.preview_s, E.preview_samples(h))
                self.assertEqual(env.preview_h_s, h)
        for h in (0.0, -1.0):
            with self.subTest(H=h), self.assertRaises(ValueError):
                G.preview_env(c, plant=p, dt=1.0, use_preview=False, horizon_s=h, seed=0, reward_knock=False)

    def test_the_policies_are_the_gates_own(self):
        import test_reward as TR
        rng = np.random.default_rng(0)
        self.assertTrue(np.array_equal(G.policy_action("starver", None, rng), TR.torque_starver()))
        self.assertTrue(np.array_equal(G.policy_action("neutral", None, rng), E.neutral_action()))
        with self.assertRaises(ValueError):
            G.policy_action("reactive", None, rng)

    def test_row_116s_road_is_built_with_the_options_train_py_gives_it(self):
        """engine_gate.FOUR_ENGINE_OPTIONS and benchmark_training.ROAD_OPTIONS are train.py's own for a run
        with neither --scored-share nor --roads-record; both build the road, on an EPA car."""
        import benchmark_training as B
        import train as T
        self.assertEqual(B.ROAD_OPTIONS, {G.FOUR_ENGINE_ROAD: G.FOUR_ENGINE_OPTIONS})
        if G.FOUR_ENGINE_ROAD not in T.DESIGN_DT:
            self.skipTest("train.py has no four_engine road in this tree")
        env = G.training_env(G.FOUR_ENGINE_ROAD, 11, plant=engines.get("mazda_25t"), roads_record=None,
                             reward_knock=False)
        self.assertEqual(len(env.unwrapped.cycle["grade"]), int(T.DURATION_S / T.DESIGN_DT[G.FOUR_ENGINE_ROAD]))
        self.assertIsNotNone(G.wrapper_attr(env, "c_turb_scale"))
        self.assertIs(env.unwrapped.reward_knock, False)
        with self.assertRaises(ValueError):
            G.training_env("no_such_road", 11, plant=engines.get("b58"), roads_record=None, reward_knock=False)

    def test_the_share_on_the_training_road_SYNTHETIC(self):
        """C1b (row 130 (5)): a roads record turns decision 29's share on in the training check, as train.py
        builds the road with --scored-share --roads-record, so each seed's first episode is the share's
        road; None keeps it off. The control (mistake 12): the same seed without the record starts on a
        general road. share_record refuses a record for another road and one train.py would refuse, and
        the record is required of training_env, run_gate, road_table and every training task."""
        import inspect
        import four_engine_roads as F
        d = tempfile.mkdtemp(prefix="gate_share_")
        try:
            rec = F.write_synthetic_record(os.path.join(d, "roads.SYNTHETIC.json"), 4242)
            p = engines.get("b58")
            on = G.training_env(G.FOUR_ENGINE_ROAD, 11, plant=p, roads_record=rec, reward_knock=False)
            off = G.training_env(G.FOUR_ENGINE_ROAD, 11, plant=p, roads_record=None, reward_knock=False)
            self.assertEqual(G.wrapper_attr(on, "road_log")[0].split()[:2], ["scored", "SYNTHETIC"])
            self.assertEqual(G.wrapper_attr(off, "road_log")[0].split()[0], "general")
            self.assertEqual(G.share_record(G.FOUR_ENGINE_ROAD, rec)["seed_kind"], "SYNTHETIC")
            self.assertIsNone(G.share_record(G.FOUR_ENGINE_ROAD, None))
            for road, path in (("extremes", rec), (G.FOUR_ENGINE_ROAD, os.path.join(d, "no_such_roads.json"))):
                with self.subTest(road=road, path=path), self.assertRaises(ValueError):
                    G.share_record(road, path)
            with self.assertRaises(ValueError):
                G.training_env("extremes", 11, plant=p, roads_record=rec, reward_knock=False)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        for fn in (G.training_env, G.run_gate, G.road_table):
            with self.subTest(fn=fn.__name__):
                self.assertIs(inspect.signature(fn).parameters["roads_record"].default, inspect.Parameter.empty)
        bare = G.job(dict(engine="b58", kind="train", train_road=G.FOUR_ENGINE_ROAD, seed=11, policy="neutral",
                          reward_knock=False))
        self.assertIn("KeyError: 'roads_record'", bare["error"])
        # the plant commit P: a task without the knock option is refused the same way (row 127 (4))
        bare = G.job(dict(engine="b58", kind="train", train_road=G.FOUR_ENGINE_ROAD, seed=11, policy="neutral",
                          roads_record=None))
        self.assertIn("KeyError: 'reward_knock'", bare["error"])

    def test_the_record_is_named_relative_to_the_repository(self):
        """C1b (the review of 2 November 2026): the gate and check_roads.py print and record the roads record
        repository-relative, epa_roads.ROADS_REL for a REAL record, and the training tasks alone read it by
        its absolute path; check_roads.py's default file says whether the share is on, so the two runs do
        not overwrite each other. The REAL record is a stand-in here (share_record's dict, no record read).
        The control (mistake 12): the tasks road_table hands its pool do carry the absolute path."""
        from unittest import mock
        import check_roads as CR
        real_abs = os.path.join(HERE, *ER.ROADS_REL.split("/"))
        real = dict(seed_kind="REAL", path=real_abs)
        self.assertIsNone(G.record_name(None))
        self.assertEqual(G.record_name(real), ER.ROADS_REL)
        self.assertEqual(G.record_name(dict(real, path=real_abs.upper() if os.name == "nt" else real_abs)),
                         ER.ROADS_REL)
        inside = os.path.join(HERE, "results", "x.SYNTHETIC.json")
        self.assertEqual(G.record_name(dict(seed_kind="SYNTHETIC", path=inside)), "results/x.SYNTHETIC.json")
        outside = os.path.join(tempfile.gettempdir(), "x.SYNTHETIC.json")
        self.assertEqual(G.record_name(dict(seed_kind="SYNTHETIC", path=outside)), outside)
        handed = []

        def pool(tasks, *, jobs):
            handed.extend(tasks)
            return [dict(t) for t in tasks]
        with mock.patch.object(G, "share_record", return_value=real), mock.patch.object(G, "pool_map", pool), \
                mock.patch.object(G, "d34_roads", return_value=([], None, "stand-in")):
            train, d34, label = G.road_table("b58", train_road=G.FOUR_ENGINE_ROAD, roads_file=None,
                                             synthetic_seed=1, n=3, first_seed=100, jobs=1,
                                             roads_record=ER.ROADS_REL, reward_knock=False)
        self.assertEqual([t["roads_record"] for t in handed], [real_abs] * 3)
        self.assertEqual([t["reward_knock"] for t in handed], [False] * 3)
        self.assertEqual([r["roads_record"] for r in train], [ER.ROADS_REL] * 3)
        self.assertEqual((d34, label), ([], "stand-in"))
        gates = os.path.join(HERE, "results", "ENGINE_GATES", "b58")
        # the plant commit P (interface sheet 12.9): the knock option names the file too, so a run with the
        # knock term never overwrites the gate's own
        self.assertEqual(CR.default_table("b58", G.FOUR_ENGINE_ROAD, True, False),
                         os.path.join(gates, "check_roads_four_engine_share_on_knock_out.json"))
        self.assertEqual(CR.default_table("b58", G.FOUR_ENGINE_ROAD, False, False),
                         os.path.join(gates, "check_roads_four_engine_share_off_knock_out.json"))
        self.assertEqual(CR.default_table("b58", G.FOUR_ENGINE_ROAD, False, True),
                         os.path.join(gates, "check_roads_four_engine_share_off_knock_in.json"))
        self.assertEqual(CR.default_table("b58", "extremes", False, True),
                         os.path.join(gates, "check_roads_extremes_knock_in.json"))
        for bad in ("out", None, 0):
            with self.subTest(reward_knock=bad), self.assertRaises(TypeError):
                CR.default_table("b58", "extremes", False, bad)


class BlindArm(unittest.TestCase):
    def test_the_blind_arm_check_at_30_s(self):
        road = next(r for r in ER.generate(101, n_roads=2) if r["climbs"])
        r = G.blind_check(engines.get("b58"), road, horizon_s=30.0, reward_knock=False)
        d = r["grades_differ_at"]
        self.assertEqual((r["blind_first"], r["sighted_first"], r["sighted_want"]), (d, d - 30, d - 30), r)
        self.assertTrue(r["blind_ok"] and r["sighted_ok"])
        # the control: the sighted pair differs before the grades do, which the blind criterion refuses
        self.assertFalse(r["sighted_first"] >= d)


class Verdict(unittest.TestCase):
    def gate(self, oks, synthetic=True):
        rows = [dict(grade=0.0, held="8", margin=0.1), dict(grade=0.0005, held="8", margin=0.1)]
        return dict(engine="b58", plant_id="p", cvt=False, sweep=rows, notches=[], band=0.0005, kickdown=None,
                    label="SYNTHETIC seed 1", synthetic=synthetic, horizons=[30.0], train_road="extremes",
                    reward_knock=False, results=[],
                    checks=[(f"check {i}", ok, "detail") for i, ok in enumerate(oks)])

    def code(self, g):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = G.print_gate(g)
        return rc, buf.getvalue()

    def test_the_exit_code(self):
        rc, out = self.code(self.gate([True, True]))
        self.assertEqual(rc, 0)
        self.assertIn("SYNTHETIC", out)
        rc, out = self.code(self.gate([True, None]))
        self.assertEqual(rc, 1)
        self.assertIn("NOT COMPLETE", out)
        self.assertIn("NOT RUN", out)
        rc, out = self.code(self.gate([True, None, False], synthetic=False))
        self.assertEqual(rc, 1)
        self.assertIn("STOP.", out)

    def test_the_share_is_named_on_the_four_engine_road(self):
        """C1b: on row 116's road the gate's header says whether decision 29's share was on, and from which
        record; on any other road it says nothing of it, as before."""
        g = dict(self.gate([True]), train_road=G.FOUR_ENGINE_ROAD, roads_record=None, share_kind=None)
        self.assertIn("decision 29's share : off (no --roads-record)", self.code(g)[1])
        _, out = self.code(dict(g, roads_record="R.json", share_kind="REAL"))
        self.assertIn("decision 29's share : on, REAL record R.json (row 130 (5))", out)
        self.assertNotIn("decision 29's share", self.code(self.gate([True]))[1])

    def test_the_gate_returns_the_record_it_ran_with(self):
        """run_gate returns, and print_gate prints, the roads record the training check ran with (C1b's
        record_name), not the name of the last check: the notch and blind-arm loops rebind `name`, and until
        the plant commit P the gate returned that (found by C2's drafter, 5 November 2026). Every unit is a
        stand-in here (pool_map returns each task with an error, the sweep is hand-made with two notches), so
        nothing is rolled out. The control (mistake 12): the gate holds a notch check and a blind-arm check,
        the loops that rebound the name, and reward_knock comes back beside the record."""
        from unittest import mock
        rows = [dict(grade=x / 100, held=h, margin=0.1) for x, h in ((1, "8"), (2, "8"), (3, "7"), (4, "6"))]
        road = next(r for r in ER.generate(101, n_roads=2) if r["climbs"])
        real_abs = os.path.join(HERE, *ER.ROADS_REL.split("/"))

        def pool(tasks, *, jobs):
            return [dict({k: v for k, v in t.items() if k != "road"}, error="stand-in") for t in tasks]
        for share, want, line in ((None, None, "decision 29's share : off (no --roads-record)"),
                                  (dict(seed_kind="REAL", path=real_abs), ER.ROADS_REL,
                                   f"decision 29's share : on, REAL record {ER.ROADS_REL} (row 130 (5))")):
            with self.subTest(share=want), mock.patch.object(G, "pool_map", pool), \
                    mock.patch.object(G, "sweep", return_value=rows), \
                    mock.patch.object(G, "share_record", return_value=share), \
                    mock.patch.object(G, "d34_roads", return_value=([road], None, "stand-in")):
                g = G.run_gate("b58", train_road=G.FOUR_ENGINE_ROAD, roads_file=None, synthetic_seed=1, jobs=1,
                               roads_record=None if share is None else ER.ROADS_REL, reward_knock=False)
                names = [c[0] for c in g["checks"]]
                self.assertTrue(any(n.startswith("the notch at") for n in names), names)
                self.assertTrue(any(n.startswith("the blind arm is blind at H =") for n in names), names)
                self.assertEqual((g["roads_record"], g["reward_knock"]), (want, False))
                self.assertEqual({r["roads_record"] for r in g["results"] if r["kind"] == "train"}, {want})
                self.assertIn(line, self.code(g)[1])

    def test_the_reward_is_named(self):
        """The plant commit P (row 119): the header says which reward every environment of the gate ran."""
        want = "reward              : {} the knock term (--reward-knock {}; row 113 (5))"
        self.assertIn(want.format("without", "out"), self.code(self.gate([True]))[1])
        _, out = self.code(dict(self.gate([True]), reward_knock=True))
        self.assertIn(want.format("with", "in"), out)
        self.assertNotIn("without", out)


class Knock(unittest.TestCase):
    """The plant commit P (rows 119, 127 (4); interface sheet 6.6): the gate's environments take the task's
    reward_knock, every one of them."""

    BUILDERS = ("SupervisoryTunerEnv", "build_env", "preview_env", "d34_env", "training_env", "preview_delta",
                "obs_trace", "blind_check")

    @staticmethod
    def problems(src):
        """Every call in engine_gate's source `src` to an environment builder that does not pass
        reward_knock=, and every task base in run_gate and road_table that does not carry it."""
        import ast
        tree, out = ast.parse(src), []
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                f = n.func
                name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
                if name in Knock.BUILDERS and "reward_knock" not in [k.arg for k in n.keywords]:
                    out.append(f"line {n.lineno}: {name}(...) without reward_knock=")
        for fn in (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("run_gate", "road_table")):
            bases = [a for a in ast.walk(fn) if isinstance(a, ast.Assign) and getattr(a.targets[0], "id", None)
                     == "base"]
            if not any(k.arg == "reward_knock" for a in bases if isinstance(a.value, ast.Call)
                       for k in a.value.keywords):
                out.append(f"{fn.name}: its task base carries no reward_knock")
        return out

    def test_every_environment_the_gate_builds_carries_the_reward_knock(self):
        with open(os.path.join(HERE, "engine_gate.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(self.problems(src), [])
        # the controls (mistake 12): one call without it, and a base without it, are each flagged
        import re
        drop_call = re.sub(r"seed=0,\s*reward_knock=rk\)", "seed=0)", src, count=1)     # the band's own env
        self.assertNotEqual(drop_call, src)
        self.assertEqual(len(self.problems(drop_call)), 1)
        drop_base = src.replace("base = dict(engine=engine_id, reward_knock=reward_knock)", "base = dict(engine=engine_id)")
        self.assertEqual(self.problems(drop_base), ["run_gate: its task base carries no reward_knock"])
        # the builders themselves, directly
        p = engines.get("b58")
        c = G.notch_cycle(p, 0.10)
        for rk in (False, True):
            with self.subTest(reward_knock=rk):
                self.assertIs(G.preview_env(c, plant=p, dt=1.0, use_preview=True, horizon_s=30.0, seed=0,
                                            reward_knock=rk).reward_knock, rk)
                road = next(r for r in ER.generate(101, n_roads=2) if r["climbs"])
                self.assertIs(G.d34_env(road, plant=p, use_preview=True, reward_knock=rk).reward_knock, rk)
                self.assertIs(G.training_env("extremes", 11, plant=p, roads_record=None,
                                             reward_knock=rk).unwrapped.reward_knock, rk)
        import inspect
        for fn in (G.preview_env, G.d34_env, G.training_env, G.preview_delta, G.obs_trace, G.blind_check,
                   G.run_gate, G.road_table):
            with self.subTest(fn=fn.__name__):
                self.assertIs(inspect.signature(fn).parameters["reward_knock"].default, inspect.Parameter.empty)
        for bad in ("out", 0, None):
            with self.subTest(bad=bad), self.assertRaises(TypeError):
                G.run_gate("b58", train_road="extremes", roads_file=None, synthetic_seed=1, jobs=1,
                           roads_record=None, reward_knock=bad)

    def test_the_band_and_notch_jobs_build_with_the_tasks_reward_knock(self):
        """Interface sheet 6.6: a band job and a notch job (and the notch's preview check, decision 34's
        roads and the blind arm) build their SupervisoryTunerEnv with the task's reward_knock, read by
        wrapping the constructor; each job stops right after it, so nothing is rolled out. The control is
        the knock-in task, whose environments read True."""
        from unittest import mock
        seen = []

        class Stop(Exception):
            pass

        class Recording(E.SupervisoryTunerEnv):
            def __init__(self, *a, **kw):
                super().__init__(*a, **kw)
                seen.append(self.reward_knock)
                raise Stop("built")
        road = next(r for r in ER.generate(101, n_roads=2) if r["climbs"])
        kinds = (dict(kind="band", grade=0.05, policy="neutral"), dict(kind="notch", grade=0.10, policy="neutral"),
                 dict(kind="notch-preview", grade=0.10), dict(kind="d34", road=road, policy="neutral"),
                 dict(kind="blind", road=road, H_s=30.0))
        with mock.patch.object(E, "SupervisoryTunerEnv", Recording):
            for rk in (False, True):
                for t in kinds:
                    with self.subTest(kind=t["kind"], reward_knock=rk):
                        seen.clear()
                        res = G.job(dict(t, engine="b58", reward_knock=rk))
                        self.assertIn("Stop: built", res.get("error", ""), res)
                        self.assertEqual(seen, [rk])


class Cli(unittest.TestCase):
    def refused(self, *argv, want):
        rc, out = run(*argv)
        self.assertEqual(rc, 2, out[-2000:])
        self.assertIn(want, out)

    def test_test_reward_refusals(self):
        self.refused("test_reward.py", "--engine", "b58", want="--train-road is required")
        self.refused("test_reward.py", "--engine", "b58", "--train-road", "extremes", want="--synthetic-seed N")
        self.refused("test_reward.py", "--engine", "b58", "--train-road", "extremes", "--synthetic-seed", "1",
                     "--road", "random", want="belong to the B58's committed gate")
        self.refused("test_reward.py", "--engine", "b58", "--train-road", "extremes", "--synthetic-seed", "1",
                     "--duration", "900", want="belong to the B58's committed gate")
        self.refused("test_reward.py", "--train-road", "extremes", want="give --engine")
        self.refused("test_reward.py", "--synthetic-seed", "3", want="give --engine")
        self.refused("test_reward.py", "--engine", "no_such_engine", want="invalid choice")
        self.refused("test_reward.py", "--engine", "b58", "--train-road", "extremes", "--roads", "x.json",
                     "--synthetic-seed", "1", want="not allowed with argument")
        # C1b: the share's record is the per-engine gate's, on row 116's road only, and one train.py reads
        self.refused("test_reward.py", "--roads-record", "x.json", want="give --engine")
        self.refused("test_reward.py", "--engine", "b58", "--train-road", "extremes", "--synthetic-seed", "1",
                     "--roads-record", "x.json", want="four_engine's alone")
        self.refused("test_reward.py", "--engine", "b58", "--train-road", "four_engine", "--synthetic-seed", "1",
                     "--roads-record", os.path.join(HERE, "no_such_roads.json"), want="no roads record there")

    def test_the_reward_knock_is_required_on_every_four_engine_command(self):
        """The plant commit P (rows 119, 127 (4)): engine_gate's two command lines need --reward-knock with
        --engine, as their last check, so every refusal before it keeps its text (test_test_reward_refusals,
        test_check_roads_refusals); without --engine it is refused as the other per-engine options are (the
        control). The benchmark's own requirement is C1b's (test_benchmark_refusals)."""
        self.refused("test_reward.py", "--engine", "b58", "--train-road", "four_engine", "--synthetic-seed", "1",
                     want="--reward-knock in|out is required with --engine")
        tmp = tempfile.mkdtemp(prefix="gate_knock_cli_")
        try:
            self.refused("check_roads.py", "--engine", "b58", "--train-road", "four_engine", "--synthetic-seed", "1",
                         "--out", os.path.join(tmp, "t.json"), want="--reward-knock in|out is required with --engine")
            self.assertEqual(os.listdir(tmp), [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        self.refused("benchmark_training.py", "--engine", "b58", "--road", "four_engine", "--dry-run",
                     want="--reward-knock")
        self.refused("test_reward.py", "--reward-knock", "out", want="give --engine")
        self.refused("check_roads.py", "--reward-knock", "out", want="give --engine")
        self.refused("test_reward.py", "--engine", "b58", "--train-road", "four_engine", "--synthetic-seed", "1",
                     "--reward-knock", "maybe", want="invalid choice")
        # an earlier refusal still wins without the flag
        self.refused("check_roads.py", "--engine", "b58", "--train-road", "extremes", "--synthetic-seed", "1",
                     want="outside the repository")

    def test_check_roads_refusals(self):
        self.refused("check_roads.py", "--engine", "b58", "--train-road", "extremes", "--synthetic-seed", "1",
                     want="outside the repository")
        self.refused("check_roads.py", "--engine", "b58", "--train-road", "extremes", "--synthetic-seed", "1",
                     "--out", os.path.join(HERE, "results", "x.json"), want="outside the repository")
        self.refused("check_roads.py", "--engine", "b58", "--road", "extremes", want="--road is the B58's table")
        self.refused("check_roads.py", "--engine", "b58", want="--train-road is required")
        self.refused("check_roads.py", "--jobs", "4", want="give --engine")
        self.refused("check_roads.py", "--out", "x.json", want="give --engine")
        # C1b: as test_reward.py's, and a SYNTHETIC share record makes the table a test, written outside only
        self.refused("check_roads.py", "--roads-record", "x.json", want="give --engine")
        self.refused("check_roads.py", "--engine", "b58", "--train-road", "extremes", "--roads", "x.json",
                     "--roads-record", "x.json", want="four_engine's alone")
        import four_engine_roads as F
        d = tempfile.mkdtemp(prefix="gate_share_cli_")
        try:
            rec = F.write_synthetic_record(os.path.join(d, "roads.SYNTHETIC.json"), 4242)
            self.refused("check_roads.py", "--engine", "b58", "--train-road", "four_engine", "--roads", "x.json",
                         "--roads-record", rec, want="outside the repository")
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_benchmark_refusals(self):
        self.refused("benchmark_training.py", "--dry-run", want="mistake 1")
        self.refused("benchmark_training.py", "--engine", "b58", "--dry-run", want="--road is required")
        self.refused("benchmark_training.py", "--merge", "a.json", "b.json", "--engine", "b58",
                     want="--merge takes no --engine or --road")
        self.refused("benchmark_training.py", "--engine", "no_such_engine", "--road", "extremes", "--dry-run",
                     want="invalid choice")
        # C1b, row 135's protocol: the knock option required on row 116's road, the share's record that
        # road's alone and repository-relative, and neither option with --merge; row 136 builds no table,
        # so the benchmark has no --table-record
        rr = "results/EPA_ROADS/roads.json"
        self.refused("benchmark_training.py", "--engine", "b58", "--road", "four_engine", "--dry-run",
                     want="--reward-knock is required with --road four_engine")
        self.refused("benchmark_training.py", "--engine", "b58", "--road", "extremes", "--roads-record", rr,
                     "--dry-run", want="--roads-record belongs to --road four_engine")
        for path, why in ((HERE.replace(os.sep, "/") + "/" + rr, "it is absolute"),
                          (rr.replace("/", "\\"), "'/' separators")):
            with self.subTest(path=path):
                self.refused("benchmark_training.py", "--engine", "b58", "--road", "four_engine", "--reward-knock",
                             "out", "--roads-record", path, "--dry-run", want=why)
        for opt in (["--reward-knock", "out"], ["--roads-record", rr]):
            with self.subTest(option=opt[0]):
                self.refused("benchmark_training.py", "--merge", "a.json", "b.json", *opt,
                             want="--merge takes no --roads-record or --reward-knock")
        self.refused("benchmark_training.py", "--engine", "b58", "--road", "four_engine", "--reward-knock", "out",
                     "--table-record", "t.json", "--dry-run", want="unrecognized arguments: --table-record")

    def test_the_benchmarks_four_engine_road_waits_for_the_plant_commit(self):
        """C1b: the record must be the committed roads.json (real_record_problem), refused before the probe
        runs; then --reward-knock is refused while train.build_env takes no reward_knock (before P, row 127
        (4)), so four_engine is not benchmarked before P. From P on the same dry run passes, and every
        command it prints carries the share and the knock option."""
        import inspect
        import train as T
        argv = ["benchmark_training.py", "--engine", "b58", "--road", "four_engine", "--reward-knock", "out",
                "--device", "cpu", "--dry-run"]
        d = tempfile.mkdtemp(prefix="bench_f4_")
        try:
            rc, out = run(*argv, "--roads-record", "results/EPA_ROADS/other_roads.json",
                          "--out", os.path.join(d, "a.json"))
            self.assertEqual(rc, 1, out[-2000:])
            self.assertIn("a REAL roads record is read only from results/EPA_ROADS/roads.json", out)
            rc, out = run(*argv, "--roads-record", "results/EPA_ROADS/roads.json",
                          "--out", os.path.join(d, "b.json"))
            if "reward_knock" not in inspect.signature(T.build_env).parameters:
                self.assertEqual(rc, 1, out[-2000:])
                self.assertIn("REFUSING: --reward-knock needs the plant commit P (row 127 (4))", out)
            else:
                self.assertEqual(rc, 0, out[-2000:])
                self.assertEqual(out.count("--scored-share --roads-record results/EPA_ROADS/roads.json "
                                           "--reward-knock out"), out.count("  section "), out[-3000:])
            self.assertNotIn("Traceback", out)
            self.assertEqual(os.listdir(d), [])
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_the_benchmark_probe_refuses_a_road_train_py_does_not_have(self):
        rc, out = run("benchmark_training.py", "--engine", "b58", "--road", "no_such_road", "--dry-run")
        self.assertEqual(rc, 1, out[-2000:])
        self.assertIn("train.py has no road 'no_such_road'", out)


class Scans(unittest.TestCase):
    FILES = ("engine_gate.py", "test_reward.py", "check_roads.py", "benchmark_training.py", "test_device_gate.py")

    def test_no_default_engine_and_no_unknown_name(self):
        import importlib
        import test_engine_threading as TET
        modules = {m: importlib.import_module(m) for m in TET.PLANT_MODULES}
        for rel in self.FILES:
            with open(os.path.join(HERE, rel), encoding="utf-8") as fh:
                src = fh.read()
            with self.subTest(file=rel):
                self.assertEqual(TET.scan_source(src, rel), [])
                self.assertEqual(TET.scan_names(src, rel, modules), [])
        # the control: a per-engine function with a default engine is flagged
        bad = "import engine_gate as G\ndef gate(engine='b58'):\n    return engine\n"
        self.assertTrue(TET.scan_source(bad, "scratch.py"))


@unittest.skipIf(bash() is None, "no bash here")
class RunbookB1(unittest.TestCase):
    """C1b (the reviews of 2 November 2026): docs/build_step_2/DEVICE_RUNBOOK.md's B0 record, its B1 blocks and B5's
    copy, their own text, run by bash on a scratch git work tree outside the repository (one empty commit), with a
    stand-in for row 135's interpreter (the blocks' <row 135's interpreter>). The stand-in answers the loop's engine
    list with two engines; for each benchmark run it records benchmark_training.code_info of the work tree when it
    starts and writes its --out, which it refuses to overwrite, as the benchmark does; and it runs B0's record lines
    (python reading its script from stdin) with the real interpreter and this tree's benchmark_training. $PY is a
    second stand-in that refuses, since for cuda row 135's interpreter is not the lock's CPU build, and $OUT a
    session folder that must stay empty. B0's record lands in $B1OUT as B0_<git_head>.json, code_info and the host;
    every attempt lands in B0's $B1OUT and records git_dirty False; k counts the attempts in $B1OUT and in
    results/benchmarks/, a .txt alone included; a later session's repeat into the same $B1OUT continues the count,
    on cuda the CPU series runs with $PY as B1_bench_<e>.cpu.attempt<k>, counted on its own, and B5 copies every
    attempt of both sessions, the CPU series' and the B0 record. The controls (mistake 12): the same loop writing
    its attempts into results/benchmarks/, as the sheet first drafted it, records the second engine's run dirty;
    the loop with $PY runs nothing, and the CPU series with that $PY runs nothing either; B0's record lines refuse
    a record that differs, a dirty tree and a tree at no commit. On cuda a later session gets $PYC from 'Before you
    start', which every session runs first; without its PYC line the record lines and the loop run nothing."""
    RUNBOOK = os.path.join(HERE, "docs", "build_step_2", "DEVICE_RUNBOOK.md")
    STAND_IN = ("#!/usr/bin/env bash\n"
                "if [ \"$2\" = \"-c\" ]; then echo \"b58 mazda_25t\"; exit 0; fi\n"
                "if [ \"$2\" = \"-\" ]; then PYTHONPATH=\"$BENCH_HERE\" exec \"$REAL_PY\" \"$@\"; fi\n"
                "out=\"\"; prev=\"\"\n"
                "for x in \"$@\"; do [ \"$prev\" = \"--out\" ] && out=\"$x\"; prev=\"$x\"; done\n"
                "if [ -z \"$out\" ] || [ -e \"$out\" ]; then echo \"refused: --out '$out'\"; exit 1; fi\n"
                "\"$REAL_PY\" -B -c 'import json, os, sys; sys.path.insert(0, os.environ[\"BENCH_HERE\"]); "
                "import benchmark_training as B; "
                "json.dump(dict(argv=sys.argv[2:], code=B.code_info(os.getcwd())), open(sys.argv[1], \"w\"))' "
                "\"$out\" \"$@\"\n"
                "echo \"ran $out\"\n")
    WRONG_PY = ("#!/usr/bin/env bash\n"
                "touch \"$WRONG_PY_MARK\"\n"
                "echo \"the lock's CPU interpreter PY ran, not row 135's\" >&2\n"
                "exit 7\n")
    FIRST = ["B1_bench_b58.attempt1.txt", "B1_bench_b58.attempt2.json", "B1_bench_b58.attempt2.txt",
             "B1_bench_mazda_25t.attempt2.json", "B1_bench_mazda_25t.attempt2.txt"]
    B0_KEYS = {"git_head", "git_dirty", "benchmark_sha", "train_sha", "host"}

    def block(self, step, needle=None):
        """A bash block of the runbook's `step`, as the runbook holds it: the step's first, or the one block of the
        step that holds `needle`."""
        with open(self.RUNBOOK, encoding="utf-8") as fh:
            text = fh.read()
        start = text.index(f"**{step}.")
        end = min(i for i in (text.find("\n**B", start + 1), text.find("\n## ", start + 1), len(text)) if i != -1)
        blocks, at = [], start
        while True:
            first = text.find("```bash\n", at, end)
            if first == -1:
                break
            first += len("```bash\n")
            last = text.index("\n```", first)
            blocks.append(text[first:last])
            at = last + len("\n```")
        self.assertTrue(blocks, step)
        if needle is None:
            return blocks[0]
        held = [b for b in blocks if needle in b]
        self.assertEqual(len(held), 1, (step, needle))
        return held[0]

    def fill(self, body, values):
        for placeholder, value in values:
            self.assertIn(placeholder, body)
            body = body.replace(placeholder, value)
        self.assertNotRegex(body, r"<[a-z][^>]*>")        # every placeholder filled
        return body

    def loop(self, interpreter, device="cpu"):
        """B1's first block, row 135's device's series."""
        return self.fill(self.block("B1"), (("<row 135's interpreter>", interpreter), ("<row 135>", device),
                                            ("<N>", "2"), ("<S>", "1000"), ("<R>", "1")))

    def cpu_loop(self):
        """B1's second block: on cuda, the CPU series, with $PY."""
        body = self.block("B1", needle="--device cpu")
        self.assertTrue(body.startswith("PYB=$PY "), body)
        self.assertIn('--out "$B1OUT/B1_bench_$E.cpu.attempt$k.json"', body)
        return self.fill(body, (("<row 135's CPU N>", "3"), ("<S>", "1000"), ("<R>", "1")))

    def b0_record(self, interpreter):
        """B0's record lines, as the runbook holds them, row 135's interpreter given and its B1OUT line keeping the
        scratch $B1OUT bash is given."""
        body = self.block("B0", needle="B1OUT=~/grad_device/B1 ")
        self.assertTrue(body.startswith("PYB=<row 135's interpreter> "), body)
        self.assertIn('$PYB -B - "$B1OUT" <<', body)
        return self.fill(body, (("<row 135's interpreter>", interpreter),
                                ("B1OUT=~/grad_device/B1 ", 'B1OUT="$B1OUT" '))) + "\n"

    def before_you_start(self, repo, out, pyc):
        """'Before you start''s bash block, as the runbook holds it, what every session runs first: its REPO, OUT
        and PYC lines given the scratch tree, a session folder and a stand-in. Its PYC line must name the python
        of the environment B0's CUDA block makes."""
        with open(self.RUNBOOK, encoding="utf-8") as fh:
            text = fh.read()
        first = text.index("```bash\n", text.index("## Before you start")) + len("```bash\n")
        body = text[first:text.index("\n```", first)] + "\n"
        return self.fill(body, (("REPO=~/GRAD-project ", f'REPO="{repo.replace(os.sep, "/")}" '),
                                ("OUT=~/grad_device/2026-11-01 ", f'OUT="{out.replace(os.sep, "/")}" '),
                                ("PYC=~/grad_venv_cuda_lock/Scripts/python.exe ", f'PYC="{pyc}" ')))

    def scratch(self, root):
        """A scratch git work tree under `root`, at one empty commit, B0's $B1OUT and a session's $OUT beside it,
        as a first session finds them: an attempt already committed (excluded, so the tree is as clean as a
        committed file leaves it) and a crash in $B1OUT that left only its .txt. Returns (tree, $B1OUT, $OUT,
        bash's environment, the stand-in for row 135's interpreter)."""
        tree, b1out, out = os.path.join(root, "tree"), os.path.join(root, "B1OUT"), os.path.join(root, "OUT")
        os.makedirs(os.path.join(tree, "results", "benchmarks"))
        os.makedirs(b1out)
        os.makedirs(out)
        self.git_init(tree, commit=True)
        for path in (os.path.join(tree, "results", "benchmarks", "B1_bench_mazda_25t.attempt1.json"),
                     os.path.join(b1out, "B1_bench_b58.attempt1.txt")):
            open(path, "w").close()
        with open(os.path.join(tree, ".git", "info", "exclude"), "a", encoding="utf-8") as fh:
            fh.write("results/benchmarks/B1_bench_mazda_25t.attempt1.json\n")
        paths = {}
        for name, text in (("py_stand_in.sh", self.STAND_IN), ("wrong_py.sh", self.WRONG_PY)):
            paths[name] = os.path.join(root, name)
            with open(paths[name], "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
        fwd = {k: v.replace(os.sep, "/") for k, v in paths.items()}
        env = dict(ENV, PY=fwd["wrong_py.sh"], B1OUT=b1out.replace(os.sep, "/"), OUT=out.replace(os.sep, "/"),
                   REAL_PY=PY_FWD, BENCH_HERE=HERE,
                   WRONG_PY_MARK=os.path.join(root, "wrong_py_ran").replace(os.sep, "/"))
        return tree, b1out, out, env, fwd["py_stand_in.sh"]

    def git_init(self, tree, commit):
        os.makedirs(tree, exist_ok=True)
        self.assertEqual(subprocess.run(["git", "init", "-q"], cwd=tree, capture_output=True).returncode, 0)
        if commit:
            p = subprocess.run(["git", "-c", "user.name=scratch", "-c", "user.email=scratch@example.invalid",
                                "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", "scratch"],
                               cwd=tree, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def git_head(self, tree):
        p = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=tree, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout.strip()

    def bash_in(self, tree, body, env, ok=True):
        """One session: `body` run by a new bash in `tree`. bash's exit code and output; the code must be 0 when
        `ok`."""
        p = subprocess.run([bash(), "-c", body], cwd=tree, capture_output=True, text=True, env=env, timeout=600)
        if ok:
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            return p.stdout + p.stderr
        return p.returncode, p.stdout + p.stderr

    def record(self, path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    def test_two_engines_in_a_row_record_a_clean_tree(self):
        root = tempfile.mkdtemp(prefix="runbook_b1_")
        try:
            tree, b1out, out, env, interpreter = self.scratch(root)
            body = self.loop(interpreter)
            self.assertIn('--out "$B1OUT/B1_bench_$E.attempt$k.json"', body)
            text = self.bash_in(tree, body, env)
            self.assertEqual(sorted(os.listdir(b1out)), self.FIRST, text)
            for e in ("b58", "mazda_25t"):
                with self.subTest(engine=e):
                    rec = self.record(os.path.join(b1out, f"B1_bench_{e}.attempt2.json"))
                    self.assertIs(rec["code"]["git_dirty"], False, rec)
                    a = rec["argv"]
                    self.assertEqual(a[a.index("--engine") + 1], e)
                    for flag, value in (("--road", "four_engine"), ("--roads-record", ER.ROADS_REL),
                                        ("--reward-knock", "out"), ("--device", "cpu"), ("--runs", "2")):
                        self.assertEqual(a[a.index(flag) + 1], value, a)
                    with open(os.path.join(b1out, f"B1_bench_{e}.attempt2.txt"), encoding="utf-8") as fh:
                        self.assertIn("ran ", fh.read())
            self.assertEqual(os.listdir(os.path.join(tree, "results", "benchmarks")),
                             ["B1_bench_mazda_25t.attempt1.json"])
            self.assertEqual(os.listdir(out), [], "B1 writes into B0's $B1OUT, not the session's $OUT")
            self.assertFalse(os.path.exists(env["WRONG_PY_MARK"]), "the loop ran $PY, not row 135's interpreter")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_a_later_session_continues_the_count_and_B5_copies_every_attempt(self):
        """The reviews of 2 November 2026: B1 may span sessions, each with its own $OUT, and each first runs B0's
        record lines. The first session's write $B1OUT/B0_<git_head>.json, code_info of the tree and the host; a
        later session's, on the same commit and host, leave it as it is. A crash repeated in the later session, for
        its engine alone (the runbook's `for E in <the engine>; do`) and here on cuda, goes into the same $B1OUT as
        attempt 3, and on cuda the CPU series runs at the same visit for every engine, with $PY, as
        B1_bench_<e>.cpu.attempt1. B5's copy, run once at the end, commits every attempt of both sessions, the CPU
        series' and the B0 record, beside the one already committed."""
        import platform
        import benchmark_training as B
        root = tempfile.mkdtemp(prefix="runbook_b1_sessions_")
        try:
            tree, b1out, out, env, interpreter = self.scratch(root)
            head = self.git_head(tree)
            b0 = f"B0_{head}.json"
            text = self.bash_in(tree, self.b0_record(interpreter), env)
            self.assertIn("wrote ", text)
            self.assertEqual(sorted(os.listdir(b1out)), sorted(["B1_bench_b58.attempt1.txt", b0]), text)
            rec = self.record(os.path.join(b1out, b0))
            self.assertEqual(set(rec), self.B0_KEYS, rec)
            mine = B.code_info()
            self.assertEqual((rec["git_head"], rec["git_dirty"], rec["host"], rec["benchmark_sha"], rec["train_sha"]),
                             (head, False, platform.node(), mine["benchmark_sha"], mine["train_sha"]), rec)
            with open(os.path.join(b1out, b0), "rb") as fh:
                written = fh.read()
            self.bash_in(tree, self.loop(interpreter), env)
            later = os.path.join(root, "OUT2")
            os.makedirs(later)
            env2 = dict(env, OUT=later.replace(os.sep, "/"))
            text = self.bash_in(tree, self.b0_record(interpreter), env2)
            self.assertIn("not rewritten", text)
            with open(os.path.join(b1out, b0), "rb") as fh:
                self.assertEqual(fh.read(), written)
            lines = self.loop(interpreter, device="cuda").split("\n")
            (i,) = [n for n, line in enumerate(lines) if line.startswith("for E in ")]
            lines[i] = "for E in b58; do"
            text = self.bash_in(tree, "\n".join(lines), env2)
            # on cuda, the CPU series at the same visit: $PY is the lock's CPU interpreter here, so its stand-in
            # is the one that runs
            text += self.bash_in(tree, self.cpu_loop(), dict(env2, PY=interpreter))
            cpu = [f"B1_bench_{e}.cpu.attempt1.{x}" for e in ("b58", "mazda_25t") for x in ("json", "txt")]
            want = sorted(self.FIRST + [b0, "B1_bench_b58.attempt3.json", "B1_bench_b58.attempt3.txt"] + cpu)
            self.assertEqual(sorted(os.listdir(b1out)), want, text)
            rec = self.record(os.path.join(b1out, "B1_bench_b58.attempt3.json"))
            self.assertIs(rec["code"]["git_dirty"], False, rec)
            self.assertEqual(rec["code"]["git_head"], head)
            self.assertEqual(rec["argv"][rec["argv"].index("--device") + 1], "cuda")
            for e in ("b58", "mazda_25t"):
                with self.subTest(engine=e, series="cpu"):
                    rec = self.record(os.path.join(b1out, f"B1_bench_{e}.cpu.attempt1.json"))
                    self.assertIs(rec["code"]["git_dirty"], False, rec)
                    self.assertEqual(rec["code"]["git_head"], head)
                    a = rec["argv"]
                    for flag, value in (("--engine", e), ("--road", "four_engine"), ("--roads-record", ER.ROADS_REL),
                                        ("--reward-knock", "out"), ("--device", "cpu"), ("--runs", "3")):
                        self.assertEqual(a[a.index(flag) + 1], value, a)
            copy = self.block("B5")
            self.assertIn('"$B1OUT"/B1_bench_', copy)
            self.assertIn('"$B1OUT"/B0_*.json', copy)
            self.bash_in(tree, copy, env)
            bench = os.path.join(tree, "results", "benchmarks")
            self.assertEqual(sorted(os.listdir(bench)), sorted(want + ["B1_bench_mazda_25t.attempt1.json"]))
            for name in want:
                with open(os.path.join(b1out, name), "rb") as a, open(os.path.join(bench, name), "rb") as b:
                    self.assertEqual(a.read(), b.read(), name)
            self.assertEqual((os.listdir(out), os.listdir(later)), ([], []))
            self.assertFalse(os.path.exists(env["WRONG_PY_MARK"]), "a block ran the refusing $PY")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_the_control_attempts_inside_the_tree_record_it_dirty(self):
        root = tempfile.mkdtemp(prefix="runbook_b1_control_")
        try:
            tree, _, _, env, interpreter = self.scratch(root)
            body = self.loop(interpreter).replace('"$B1OUT/B1_bench_$E.attempt$k',
                                                  '"results/benchmarks/B1_bench_$E.attempt$k')
            self.assertNotIn('"$B1OUT/', body)
            text = self.bash_in(tree, body, env)
            second = self.record(os.path.join(tree, "results", "benchmarks", "B1_bench_mazda_25t.attempt2.json"))
            self.assertIs(second["code"]["git_dirty"], True, text)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_the_control_PY_is_refused(self):
        """The stand-in for $PY does refuse (mistake 12): the B1 loop with its interpreter line set to $PY, as
        the draft wrote it, runs no benchmark and leaves the mark; so does the CPU series' block, whose
        interpreter is $PY, so the block that ran in the test above ran $PY."""
        root = tempfile.mkdtemp(prefix="runbook_b1_py_")
        try:
            tree, b1out, _, env, _ = self.scratch(root)
            for body in (self.loop("$PY"), self.cpu_loop()):
                with self.subTest(block=body.split("\n")[0]):
                    if os.path.exists(env["WRONG_PY_MARK"]):
                        os.remove(env["WRONG_PY_MARK"])
                    self.bash_in(tree, body, env, ok=False)
                    self.assertTrue(os.path.exists(env["WRONG_PY_MARK"]))
                    self.assertEqual(sorted(os.listdir(b1out)), ["B1_bench_b58.attempt1.txt"])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_the_control_B0s_record_refuses(self):
        """B0's record lines refuse (mistake 12), and exit non-zero: a record already there that differs (here its
        host) is left as it is; a dirty work tree (an untracked file) and a tree at no commit write no record."""
        root = tempfile.mkdtemp(prefix="runbook_b0_")
        try:
            tree, b1out, _, env, interpreter = self.scratch(root)
            body = self.b0_record(interpreter)
            self.bash_in(tree, body, env)
            path = os.path.join(b1out, f"B0_{self.git_head(tree)}.json")
            rec = dict(self.record(path), host="another host")
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(rec, indent=1, sort_keys=True) + "\n")
            with open(path, "rb") as fh:
                before = fh.read()
            rc, text = self.bash_in(tree, body, env, ok=False)
            self.assertNotEqual(rc, 0, text)
            self.assertIn("exists and differs", text)
            with open(path, "rb") as fh:
                self.assertEqual(fh.read(), before)
            os.remove(path)
            with open(os.path.join(tree, "stray.txt"), "w") as fh:
                fh.write("untracked\n")
            rc, text = self.bash_in(tree, body, env, ok=False)
            self.assertNotEqual(rc, 0, text)
            self.assertIn("needs a clean git work tree at a commit", text)
            bare = os.path.join(root, "no_commit")
            self.git_init(bare, commit=False)
            rc, text = self.bash_in(bare, body, env, ok=False)
            self.assertNotEqual(rc, 0, text)
            self.assertIn("needs a clean git work tree at a commit", text)
            self.assertEqual([x for x in os.listdir(b1out) if x.startswith("B0_")], [])
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_a_later_cuda_session_has_PYC(self):
        """On CUDA, $PYC is row 135's interpreter, of B0's record lines and of B1, and a later session of B1 runs
        only 'Before you start', the record lines and B1 (the review of 2 November 2026): so 'Before you start'
        sets PYC, to the python of the environment B0's CUDA block makes, and no line of B0 or B1 sets it. A first
        session and a later one, each run as the runbook holds it with the interpreter read as $PYC, write B0's
        record once, find it the same, and run both engines on cuda in $B1OUT. The control (mistake 12): the same
        later session without the PYC line, as B0 alone set it before, writes no record and runs no engine, and
        still exits 0."""
        with open(self.RUNBOOK, encoding="utf-8") as fh:
            text = fh.read()
        self.assertNotRegex(text[text.index("**B0."):text.index("**B2.")], r"(?m)^\s*PYC=")
        install = self.block("B0", needle="<CU's CUDA lock>")
        self.assertIn("-m venv ~/grad_venv_cuda_lock ", install)
        self.assertIn("$PYC -m pip install -r <CU's CUDA lock>", install)
        for later in (True, False):
            root = tempfile.mkdtemp(prefix="runbook_pyc_")
            try:
                tree, b1out, out, env, interpreter = self.scratch(root)
                env = {k: v for k, v in env.items() if k != "PYC"}
                before = self.before_you_start(tree, out, interpreter)
                session = self.b0_record("$PYC") + self.loop("$PYC", device="cuda")
                if later:
                    self.assertIn("wrote ", self.bash_in(tree, before + self.b0_record("$PYC"), env))
                    text = self.bash_in(tree, before + session, env)
                    self.assertIn("already written, the same; not rewritten", text)
                    self.assertEqual(len([x for x in os.listdir(b1out) if x.startswith("B0_")]), 1, text)
                    for e in ("b58", "mazda_25t"):
                        a = self.record(os.path.join(b1out, f"B1_bench_{e}.attempt2.json"))["argv"]
                        self.assertEqual((a[a.index("--engine") + 1], a[a.index("--device") + 1]), (e, "cuda"), a)
                else:
                    bare = "".join(x for x in before.splitlines(True) if not x.startswith("PYC="))
                    self.assertNotEqual(bare, before)
                    text = self.bash_in(tree, bare + session, env)
                    self.assertEqual(sorted(os.listdir(b1out)), ["B1_bench_b58.attempt1.txt"], text)
            finally:
                shutil.rmtree(root, ignore_errors=True)


@unittest.skipIf(bash() is None, "no bash here")
class RunL8(unittest.TestCase):
    SCRIPT = os.path.join(HERE, "tools", "run_l8.sh")

    def l8(self, *argv, timeout=1800):
        p = subprocess.run([bash(), self.SCRIPT, *argv], cwd=HERE, capture_output=True, text=True, env=ENV,
                           timeout=timeout, encoding="utf-8", errors="replace")
        return p.returncode, p.stdout + p.stderr

    def test_its_refusals(self):
        root = tempfile.mkdtemp(prefix="l8_refusals_")
        try:
            out = os.path.join(root, "never_made")
            rc, text = self.l8("--cand", HERE, "--out", out)
            self.assertEqual(rc, 2, text)
            self.assertIn("are required", text)
            self.assertFalse(os.path.exists(out))
            busy = os.path.join(root, "busy")
            os.makedirs(busy)
            open(os.path.join(busy, "x"), "w").close()
            rc, text = self.l8("--cand", HERE, "--py", PY_FWD, "--out", busy)
            self.assertEqual(rc, 2, text)
            self.assertIn("not empty", text)
            inside = os.path.join(HERE, "tools", "_l8_refused_here")
            rc, text = self.l8("--cand", HERE, "--py", PY_FWD, "--out", inside)
            self.assertEqual(rc, 2, text)
            self.assertIn("inside the candidate", text)
            self.assertFalse(os.path.exists(inside))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_the_comparisons_judgement(self):
        """The review of 31 October 2026, F2: l8_compare.py exits 1 on NOT IDENTICAL, and so does a Python
        traceback, so cmp8 judges the printed verdict and the exit code together. The script's own cmp8
        and its BAD count are cut from the file and run on a stand-in for the interpreter that prints a
        given text and exits with a given code."""
        with open(self.SCRIPT, encoding="utf-8") as fh:
            src = fh.read()
        start = src.index("cmp8() {")
        func = src[start:src.index("\n}\n", start) + 3]
        bad = next(line for line in src.splitlines() if line.startswith("BAD=$("))
        cases = [  # (exit code, printed, expected, what cmp8 must say, counted as BAD)
            (0, "VERDICT: IDENTICAL TRAINING", "IDENTICAL", "IDENTICAL", 0),
            (1, "VERDICT: NOT IDENTICAL", "DIFFERENT", "DIFFERENT", 0),
            (1, "Traceback (most recent call last):\nFileNotFoundError: final.zip", "DIFFERENT", "ERROR", 1),
            (1, "Traceback (most recent call last):", "INFO", "ERROR", 1),
            (0, "nothing compared", "IDENTICAL", "ERROR", 1),
            (1, "VERDICT: IDENTICAL TRAINING", "IDENTICAL", "ERROR", 1),
            (0, "VERDICT: NOT IDENTICAL", "INFO", "ERROR", 1),
            (1, "VERDICT: NOT IDENTICAL", "INFO", "DIFFERENT", 0),
        ]
        root = tempfile.mkdtemp(prefix="l8_cmp8_")
        try:
            for i, (rc, text, expect, got, n_bad) in enumerate(cases):
                d = os.path.join(root, str(i)).replace(os.sep, "/")
                os.makedirs(os.path.join(d, "L8", "cmp"))
                fake = f"{d}/fakepy.sh"
                with open(fake, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write("#!/usr/bin/env bash\nprintf '%s\\n' " + repr(text).replace("\\n", "' '")
                             + f"\nexit {rc}\n")
                body = (f'L8="{d}/L8"; OUT_PY="{d}"; PY="{fake}"\n' + func + "\n: > \"$L8/_verdicts.txt\"\n"
                        + f"cmp8 case a b {expect}\n" + bad + "\necho \"BAD=$BAD\"\ncat \"$L8/_verdicts.txt\"\n")
                p = subprocess.run([bash(), "-c", body], capture_output=True, text=True, env=ENV, timeout=60)
                with self.subTest(case=(rc, text, expect)):
                    self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
                    self.assertIn(f"case {expect} {got}", p.stdout, p.stdout + p.stderr)
                    self.assertIn(f"BAD={n_bad}", p.stdout.replace(" ", ""), p.stdout)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_a_dry_run(self):
        root = tempfile.mkdtemp(prefix="l8_dry_")
        out = os.path.join(root, "L8out")
        try:
            rc, text = self.l8("--cand", HERE, "--py", PY_FWD, "--out", out, "--dry-run")
            self.assertEqual(rc, 0, text[-3000:])
            self.assertIn("DRY RUN: 11 commands ran with --help appended, 0 did not exit 0", text)
            self.assertEqual(os.path.getsize(os.path.join(out, "L8", "ref_compare.txt")), 0)
            self.assertTrue(os.path.isfile(os.path.join(out, "ref", "train.py")))
            with tarfile.open(TARBALL) as tf:
                for t in ("tools/l8_compare.py", "tools/l8_perturbed.py"):
                    with self.subTest(tool=t), open(os.path.join(out, t), "rb") as fh:
                        self.assertEqual(fh.read(), tf.extractfile(t).read())
            with open(os.path.join(out, "L8", "_status.txt"), encoding="utf-8") as fh:
                status = [line.split() for line in fh if line.strip()]
            self.assertEqual(sorted(s[2] for s in status),
                             sorted(["cand_extremes_sighted", "ref_extremes_sighted", "cand_extremes_blind",
                                     "ref_extremes_blind", "cand_wideair_sighted", "ref_wideair_sighted",
                                     "ctl_none", "ctl_mass", "ctl_cturb", "ctl_mass1e-9", "ctl_mass1e-6"]))
            with open(os.path.join(out, "L8", "ctl_mass1e-9.log"), encoding="utf-8", errors="replace") as fh:
                self.assertIn("PERTURBED car.mass:1e-9", fh.read())
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_every_isolated_interpreter_writes_no_bytecode(self):
        """The last check of 31 October 2026: -I ignores every PYTHON* variable, PYTHONDONTWRITEBYTECODE
        included, so the script's export did not reach the two tools it runs under -I, and l8_perturbed.py,
        which imports engines and train from the candidate, wrote twelve .pyc files into the repository
        (test_a_dry_run alone, before the fix). Every "$PY" -I line carries -B; the control: the scan
        finds a line without it."""
        def unguarded(text):
            return [line for line in text.splitlines()
                    if '"$PY" -I' in line and not line.lstrip().startswith("#") and "-I -B" not in line]
        with open(self.SCRIPT, encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(sum('"$PY" -I' in line for line in src.splitlines()), 2)
        self.assertEqual(unguarded(src), [])
        self.assertEqual(len(unguarded('  "$PY" -I "$OUT_PY/tools/l8_compare.py" a b\n')), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

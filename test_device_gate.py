"""test_device_gate.py -- the device and gate code of ORDER step 7 (commit C1): benchmark_training.py's
--engine and --road, tools/run_l8.sh, and the per-engine gate of test_reward.py and check_roads.py
(engine_gate.py).

    python -B test_device_gate.py        a few minutes; exit code 0 when all pass

Nothing here trains: every train.py below is run with --help, and the rollouts are the gate's own,
neutral, on decision 34's generator at SYNTHETIC seeds (no roads_seed exists; row 96).

  Sweep        the 0.05 % sweep's grades; notches, band and kickdown on hand-made rows; on the plants,
               the B58's kickdown to 6th where test_reward.py measured it (13.96-13.97 % in 0.01 %
               steps, the comment above D2_ROADS), the Ford's to 3rd inside the C5 failures of the roads step's own
               sweep (results/EPA_ROADS/sweep.txt: 11.20-11.80 %), the Accord's branches by its law
               (CvtVehicle.ratio_for), each box's top gear at 0 %; a scenario that is not decision
               34's refused
  Roads        one source of decision 34's roads; a roads record's roads and horizons; the onset twin;
               H other than 30 s refused until the plant commit (row 117); the starver is
               test_reward's; row 116's road built with the options train.py gives it
  BlindArm     check_random_road.py B at H = 30 s on the B58 (SYNTHETIC road): the blinded traces do
               not differ before the grades, the sighted ones differ 30 steps before, and that sighted
               pair is the control that the blind criterion can fail (mistake 12)
  Verdict      the gate's exit code: 0 only when every check ran and passed; NOT COMPLETE when one
               waits; SYNTHETIC said
  Cli          the refusals of test_reward.py, check_roads.py and benchmark_training.py (no default
               engine, CLAUDE.md mistake 1; the per-engine options only with --engine; a SYNTHETIC
               table only outside the repository); a road train.py does not have refused by the
               benchmark's probe. (benchmark_training.py --selftest is its own command: its hung-run case
               kills its child at a 2 s deadline, which a loaded machine can miss.)
  Scans        test_engine_threading's call, default and name scans on the new and changed files
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

    def test_an_H_other_than_30_s_waits_for_the_plant_commit(self):
        p = engines.get("b58")
        c = G.notch_cycle(p, 0.10)
        env = G.preview_env(c, plant=p, dt=1.0, use_preview=True, horizon_s=30.0, seed=0)
        self.assertEqual(env.use_preview, True)
        for h in (29.0, 31.0, 60.0, 130.0):
            with self.subTest(H=h), self.assertRaises(G.WaitsForPlantCommit):
                G.preview_env(c, plant=p, dt=1.0, use_preview=False, horizon_s=h, seed=0)

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
        env = G.training_env(G.FOUR_ENGINE_ROAD, 11, plant=engines.get("mazda_25t"))
        self.assertEqual(len(env.unwrapped.cycle["grade"]), int(T.DURATION_S / T.DESIGN_DT[G.FOUR_ENGINE_ROAD]))
        self.assertIsNotNone(G.wrapper_attr(env, "c_turb_scale"))
        with self.assertRaises(ValueError):
            G.training_env("no_such_road", 11, plant=engines.get("b58"))


class BlindArm(unittest.TestCase):
    def test_the_blind_arm_check_at_30_s(self):
        road = next(r for r in ER.generate(101, n_roads=2) if r["climbs"])
        r = G.blind_check(engines.get("b58"), road, horizon_s=30.0)
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
                    results=[], checks=[(f"check {i}", ok, "detail") for i, ok in enumerate(oks)])

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

    def test_check_roads_refusals(self):
        self.refused("check_roads.py", "--engine", "b58", "--train-road", "extremes", "--synthetic-seed", "1",
                     want="outside the repository")
        self.refused("check_roads.py", "--engine", "b58", "--train-road", "extremes", "--synthetic-seed", "1",
                     "--out", os.path.join(HERE, "results", "x.json"), want="outside the repository")
        self.refused("check_roads.py", "--engine", "b58", "--road", "extremes", want="--road is the B58's table")
        self.refused("check_roads.py", "--engine", "b58", want="--train-road is required")
        self.refused("check_roads.py", "--jobs", "4", want="give --engine")
        self.refused("check_roads.py", "--out", "x.json", want="give --engine")

    def test_benchmark_refusals(self):
        self.refused("benchmark_training.py", "--dry-run", want="mistake 1")
        self.refused("benchmark_training.py", "--engine", "b58", "--dry-run", want="--road is required")
        self.refused("benchmark_training.py", "--merge", "a.json", "b.json", "--engine", "b58",
                     want="--merge takes no --engine or --road")
        self.refused("benchmark_training.py", "--engine", "no_such_engine", "--road", "extremes", "--dry-run",
                     want="invalid choice")

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

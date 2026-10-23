"""test_plant_guards.py -- the guards of 8, 20 and 21 October, each with a test
that fails if the guard is removed.

    python test_plant_guards.py        a few seconds; exit code 0 when all pass

1. THE THERMAL NETWORK IS SUB-STEPPED (agreed step 1 of 30 September,
   thermal.DT_SUB_MAX). One step of 1 s must equal ten steps of 0.1 s, and one
   of 2 s twenty: the integrator splits every step into equal sub-steps of at
   most DT_SUB_MAX. And at the H/tau sweep's 2 s step the coolant must settle on
   a held climb, where before the fix it swung about 10 K every step
   (timestep_study.py, results/timestep_study_before_substep.json). Set
   DT_SUB_MAX back to one step per call and both tests fail.

2. THE FINGERPRINT COVERS THE DERIVED CONSTANTS (agreed step 2,
   fingerprint.derived_sha). Changing one constant in data/derived_params.json
   must move derived_sha, which train.py and evaluate.py treat as fatal; the
   file's bookkeeping (keys starting with "_", such as the timestamp
   derive_params.py writes) must not, or every rebuild of the dataset would
   lock out every trained agent. Runs on a copy of the file; the real one is
   never touched. Since 22 October 2026 (build step 2 P6) for every registered
   plant that has its derived file; an EPA engine before its calibration is
   skipped by name.

3. THE FINGERPRINT NAMES THE ENGINE (schema 3, 20 October 2026, the four-engine
   build). engine, engine_sha and backend are FATAL; a record of an older
   schema, which names no engine, is refused by evaluate.py and by train.py
   with its own message, and passes with --force-plant-mismatch only; a
   schema-3 record of another engine is refused field by field. Added 21
   October 2026 (the review of build step 1): nothing tested any of it, and
   build step 1's own certificate bypassed the refusal on purpose.

4. THE DEVICE ASKED FOR IS THE DEVICE TRAINED ON (21 October 2026, the review
   of benchmark_training.py; train.check_device). An explicit --device that
   torch cannot give is refused (stable-baselines3 falls back to the CPU
   without a word); CUDA is refused unless CUBLAS_WORKSPACE_CONFIG is
   check_training_device.CUBLAS_WORKSPACE, the one value every CUDA run trains
   with, and gets torch's deterministic algorithms; on the CPU the function
   changes nothing.

5. THE FINGERPRINT NAMES EVERY DIRTY PLANT FILE (22 October 2026, build step 2
   P7; found on the way by the reviews of P2-P6). git_dirty_plant_files missed
   whichever plant file `git status --porcelain` listed first, when that line
   began with a space: fingerprint._git stripped the whole output. Strip it
   again and the test fails.

Added 9 October 2026: WBS v3 rows 2.2 and 2.6 named these tests as missing.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import engines  # noqa: E402
import fingerprint as FP  # noqa: E402
import thermal  # noqa: E402

# The plant these guards are checked on, named (20 October 2026): the thermal
# network and the derived file are the B58's, which used to be the defaults.
PLANT = engines.get("b58")
LIVE_DERIVED = os.path.join(HERE, PLANT.engine.derived)

# The locked climb's operating point, held: 12 % at 130 km/h in 42 C air,
# 7th gear at 2706 rpm, the exhaust flow the H/tau axis uses (121.3 g/s) and
# the gas temperature the baseline reaches there (1022 C, CLAUDE.md mistake 23).
CLIMB = dict(mdot_fuel_gps=8.2, mdot_exh_gps=121.3, egt_k=1022.0 + 273.15, t_amb=315.15,
             vehicle_mps=130.0 / 3.6, fan_duty=0.4, coolant_pump_duty=1.0, rpm=2706.0)


def _net():
    n = thermal.ThermalNetwork(PLANT.engine.thermal)
    n.reset(t_amb=CLIMB["t_amb"], warm=True)
    return n


class SubStepping(unittest.TestCase):
    def test_a_step_equals_its_substeps(self):
        """One 1 s step is ten 0.1 s steps; one 2 s step is twenty."""
        self.assertLessEqual(thermal.DT_SUB_MAX, 0.1 + 1e-12)
        for dt, n in ((1.0, 10), (2.0, 20)):
            a, b = _net(), _net()
            for _ in range(30):
                a.step(dt, **CLIMB)
                for _ in range(n):
                    b.step(dt / n, **CLIMB)
            np.testing.assert_allclose(a.state(), b.state(), rtol=0, atol=1e-9,
                                       err_msg=f"a {dt} s step is not {n} steps of {dt / n} s")

    def test_coolant_settles_at_the_sweeps_2s_step(self):
        """Held climb at dt 2 s for 20 minutes: the block node must stop moving.
        Before the sub-stepping it zig-zagged about 10 K on every step."""
        n = _net()
        block = []
        for _ in range(600):
            n.step(2.0, **CLIMB)
            block.append(n.t_block)
        last = np.abs(np.diff(block[-30:]))
        self.assertLess(float(last.max()), 0.05,
                        f"the block node still moves {last.max():.3f} K per 2 s step at the end of a held climb")


# EVERY REGISTERED PLANT THAT HAS ITS DERIVED FILE (22 October 2026, build step 2
# P6; docs/build_step_2/PLAN.md WP1: "DerivedFingerprint per registered plant that
# has a file"). Each check runs on a copy of each such plant's file, the B58's
# data/derived_params.json among them; a registered plant whose file does not
# exist yet -- an EPA engine before its calibration writes it -- is skipped by
# name, and nothing of it is built (engines.get would stop in derived.py). The
# constant moved is one its derived set writes (engines.DERIVED_BY_SET): the B58's
# thermostat span, as before, and an EPA engine's burn base, in a frozen section.
MOVED_BY_SET = {"b58": ("thermal", "t_stat_span"), "epa": ("cycle", "burn_base")}


class DerivedFingerprint(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="derived_sha_")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def each_plant(self):
        """(name, its live derived file, its derived set) for each registered plant
        whose derived file exists; one whose file does not exist yet is a skipped
        subTest, by name. The B58 is always among those checked."""
        out = []
        for name in engines.known():
            meta = engines.read_spec(engines.PLANTS[name][0])["_meta"]
            live = os.path.join(HERE, meta["derived"])
            if os.path.exists(live):
                out.append((name, live, meta["derived_set"]))
                continue
            with self.subTest(plant=name):
                self.skipTest(f"{name} is not calibrated yet: no {meta['derived']}")
        self.assertIn("b58", [n for n, _, _ in out], "no registered plant with a derived file was checked")
        return out

    @staticmethod
    def _load(live):
        with open(live, encoding="utf-8") as fh:
            return json.load(fh)

    def _sha_of(self, name, d):
        path = os.path.join(self.dir, name, "derived_params.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(d, fh)
        return FP.derived_sha(path)

    def test_a_copy_hashes_as_the_live_file(self):
        lives = []
        for name, live, _ in self.each_plant():
            with self.subTest(plant=name):
                self.assertEqual(self._sha_of(name, self._load(live)), FP.derived_sha(live))
            lives.append(os.path.normpath(live))
        self.assertIn(os.path.normpath(LIVE_DERIVED), lives, "the B58's own file was not among them")

    def test_one_changed_constant_moves_it(self):
        for name, live, dset in self.each_plant():
            with self.subTest(plant=name):
                sec, key = MOVED_BY_SET[dset]
                d = self._load(live)
                d[sec][key] = d[sec][key] * 1.001
                self.assertNotEqual(self._sha_of(name, d), FP.derived_sha(live),
                                    f"{name}: derived_sha did not move when a derived constant changed")

    def test_bookkeeping_does_not(self):
        for name, live, _ in self.each_plant():
            with self.subTest(plant=name):
                d = self._load(live)
                d["_generated"] = "2099-01-01 00:00"
                self.assertEqual(self._sha_of(name, d), FP.derived_sha(live),
                                 f"{name}: derived_sha moved on a timestamp: every rebuild would refuse every agent")

    def test_it_is_fatal(self):
        self.assertIn("derived_sha", FP.FATAL)


# The FATAL fields schema 3 must carry: schema 2's and the three that name the
# engine (fingerprint.py's docstring).
SCHEMA_3_FATAL = ("plant_sha", "derived_sha", "engine", "engine_sha", "backend", "gears", "final_drive",
                  "dtheta_deg", "turb_protect_k", "oil_protect_k", "scenario", "episodes_sha")


def missing_fatal(fatal):
    """The schema-3 FATAL fields a FATAL tuple leaves out."""
    return [k for k in SCHEMA_3_FATAL if k not in fatal]


class SchemaThree(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.live = FP.plant_fingerprint(plant=PLANT, backend=FP.BACKEND_CYCLE)
        cls.dir = tempfile.mkdtemp(prefix="schema3_")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir, ignore_errors=True)

    def _model(self, name, meta):
        """A run directory holding only `meta` as its meta.json."""
        d = os.path.join(self.dir, name)
        FP.write(os.path.join(d, "meta.json"), meta)
        return d

    def _schema_2(self):
        """The live block as schema 2 wrote it: no engine, engine_sha or backend."""
        old = {k: v for k, v in self.live.items() if k not in ("engine", "engine_sha", "backend")}
        return dict(old, schema=2)

    def test_the_engine_fields_are_fatal(self):
        self.assertEqual(missing_fatal(FP.FATAL), [])
        self.assertEqual(FP.SCHEMA_VERSION, 3)
        for k in ("engine", "engine_sha", "backend"):
            self.assertIn(k, self.live)

    def test_the_fatal_check_can_fail(self):
        """The control (mistake 12): a FATAL tuple without engine_sha is caught."""
        self.assertEqual(missing_fatal(tuple(k for k in FP.FATAL if k != "engine_sha")), ["engine_sha"])

    def test_schema_problem_names_an_older_record(self):
        self.assertIsNone(FP.schema_problem(self.live))
        msg = FP.schema_problem(self._schema_2())
        self.assertIsNotNone(msg)
        self.assertIn("schema 2", msg)

    def test_evaluate_refuses_a_schema_2_model(self):
        import evaluate
        d = self._model("schema2", self._schema_2())
        with self.assertRaises(SystemExit) as cm:
            evaluate.check_model_fingerprint(d, self.live, False)
        self.assertIn("fingerprint schema 2", str(cm.exception))
        forced = evaluate.check_model_fingerprint(d, self.live, True)
        self.assertTrue(forced and "NOT a result" in forced[0])
        # X1's own meta.json, where this machine has it (runs/ is not in git)
        x1 = os.path.join(HERE, "runs", "extremes_dt1", "sighted_seed0")
        if os.path.exists(os.path.join(x1, "meta.json")):
            with self.assertRaises(SystemExit):
                evaluate.check_model_fingerprint(x1, self.live, False)

    def test_evaluate_passes_a_schema_3_model_of_this_plant(self):
        import evaluate
        d = self._model("schema3", dict(self.live))
        self.assertEqual([ln for ln in evaluate.check_model_fingerprint(d, self.live, False)
                          if ln.startswith("!!")], [])

    def test_another_engine_is_refused_field_by_field(self):
        import evaluate
        other = dict(self.live, engine="another/engine", engine_sha="0" * 16)
        self.assertEqual([k for k, _, _ in FP.compare(other, self.live)], ["engine", "engine_sha"])
        d = self._model("other_engine", other)
        with self.assertRaises(SystemExit):
            evaluate.check_model_fingerprint(d, self.live, False)

    def test_train_refuses_a_schema_2_run_directory(self):
        import train
        with self.assertRaises(SystemExit) as cm:
            train.refuse_old_schema(self._schema_2(), "runs_x/sighted_seed0", False)
        self.assertIn("fingerprint schema 2", str(cm.exception))
        train.refuse_old_schema(None, "runs_x/sighted_seed0", False)          # a fresh directory
        train.refuse_old_schema(dict(self.live), "runs_x/sighted_seed0", False)
        train.refuse_old_schema(self._schema_2(), "runs_x/sighted_seed0", True)   # forced

    def test_the_backend_is_never_assumed(self):
        """backend has no default (the review of 21 October 2026), and is read
        from what computes the engine: a plain environment runs the cycle model,
        one given an engine_model is refused, not called "cycle"."""
        import inspect
        import engine_env as E
        self.assertIs(inspect.signature(FP.plant_fingerprint).parameters["backend"].default,
                      inspect.Parameter.empty)
        with self.assertRaises(TypeError):
            FP.plant_fingerprint(plant=PLANT)
        env = E.SupervisoryTunerEnv(E.locked_climb(PLANT, duration=60.0, dt=1.0), plant=PLANT, dt=1.0)
        self.assertEqual(FP.backend_of(env), FP.BACKEND_CYCLE)
        surrogate = E.SupervisoryTunerEnv(E.locked_climb(PLANT, duration=60.0, dt=1.0), plant=PLANT, dt=1.0,
                                          engine_model=object())
        with self.assertRaises(ValueError):
            FP.backend_of(surrogate)
        with self.assertRaises(TypeError):
            FP.backend_of(object())
        with self.assertRaises(ValueError):
            FP.plant_fingerprint(plant=PLANT, backend="table:0123")


class GitDirtyPlantFiles(unittest.TestCase):
    """The fingerprint's advisory git_dirty_plant_files names EVERY dirty plant
    file (22 October 2026, build step 2 P7; found on the way by the reviews of P2,
    P3, P4 and P6). fingerprint._git stripped the whole of `git status
    --porcelain`, and so the leading space of its first line alone: " M
    engine_env.py" became "M engine_env.py", its path was read as "ngine_env.py",
    and the first dirty file -- engine_env.py, during WP1 -- was never named. git
    is not asked here: subprocess.run, which _git calls, answers with a fixed
    porcelain whose first line is a plant file changed in the work tree only."""

    PORCELAIN = " M engine_env.py\n M engines.py\n?? notes.txt\nM  plant.py\n"

    def _fingerprint(self, porcelain):
        real = subprocess.run

        def run(args, *a, **kw):
            if tuple(args[:2]) == ("git", "status"):
                return subprocess.CompletedProcess(args, 0, stdout=porcelain, stderr="")
            if tuple(args[:2]) == ("git", "rev-parse"):
                return subprocess.CompletedProcess(args, 0, stdout="0123abcd\n", stderr="")
            return real(args, *a, **kw)
        with mock.patch.object(FP.subprocess, "run", side_effect=run):
            return FP.plant_fingerprint(plant=PLANT, backend=FP.BACKEND_CYCLE)

    def test_the_first_dirty_plant_file_is_named(self):
        """Every plant file the porcelain lists, the first among them, whatever its
        status columns; the untracked note is not a plant file. git_head keeps its
        hash without the newline, as strip() gave it."""
        fp = self._fingerprint(self.PORCELAIN)
        self.assertEqual(fp["git_dirty_plant_files"], ["engine_env.py", "engines.py", "plant.py"])
        self.assertIs(fp["git_dirty"], True)
        self.assertEqual(fp["git_head"], "0123abcd")

    def test_a_clean_tree_names_none(self):
        """The control: an empty porcelain is a clean tree, not an unknown one."""
        fp = self._fingerprint("")
        self.assertEqual((fp["git_dirty"], fp["git_dirty_plant_files"]), (False, []))


class DeviceGuard(unittest.TestCase):
    """Guard 4: train.check_device. No GPU is needed: torch.device("cuda") is
    only a name until something runs on it, and check_device decides before."""

    def test_a_silent_cpu_fallback_is_refused(self):
        import torch
        import train
        with self.assertRaises(SystemExit) as cm:
            train.check_device("cuda", torch.device("cpu"))
        self.assertIn("REFUSING", str(cm.exception))
        with self.assertRaises(SystemExit):
            train.check_device("cpu", torch.device("cuda"))

    def test_the_cpu_path_is_left_alone(self):
        import torch
        import train
        before = torch.are_deterministic_algorithms_enabled()
        for asked in ("cpu", "auto"):
            self.assertIsNone(train.check_device(asked, torch.device("cpu")))
        self.assertEqual(torch.are_deterministic_algorithms_enabled(), before)

    def test_cuda_needs_the_cublas_workspace_and_turns_determinism_on(self):
        from unittest import mock
        import torch
        import check_training_device as CTD
        import train
        with mock.patch.dict(os.environ):
            os.environ.pop("CUBLAS_WORKSPACE_CONFIG", None)
            for asked in ("cuda", "cuda:0", "auto"):
                with self.assertRaises(SystemExit) as cm:
                    train.check_device(asked, torch.device("cuda"))
                self.assertIn("CUBLAS_WORKSPACE_CONFIG", str(cm.exception))
        # one value only: ":16:8", which earlier torch versions also accepted, is another
        # workspace (check_training_device.CUBLAS_WORKSPACE)
        for other in (":16:8", " :4096:8", ""):
            with mock.patch.dict(os.environ, {"CUBLAS_WORKSPACE_CONFIG": other}):
                with self.assertRaises(SystemExit):
                    train.check_device("cuda", torch.device("cuda"))
        before = torch.are_deterministic_algorithms_enabled()
        try:
            with mock.patch.dict(os.environ, {"CUBLAS_WORKSPACE_CONFIG": CTD.CUBLAS_WORKSPACE}):
                train.check_device("cuda", torch.device("cuda"))
            self.assertTrue(torch.are_deterministic_algorithms_enabled())
        finally:
            torch.use_deterministic_algorithms(before)


if __name__ == "__main__":
    unittest.main(verbosity=2)

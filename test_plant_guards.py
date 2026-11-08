"""test_plant_guards.py -- the guards of 8, 20 and 21 October, each with a test
that fails if the guard is removed.

    python test_plant_guards.py        about 2 minutes (101.7 s, 5 November 2026, of which
                                       RewardKnock and TitCapInterfaces 93.4 s: they step
                                       environments); exit code 0 when all pass

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
   again and the test fails. Since the plant commit P the match is exact (row
   127 (5)): a dirty car_thermal.py no longer names thermal.py.

6. FINGERPRINT SCHEMA 4 (the plant commit P, ORDER step 14; interface sheet 6.2
   and 6.7, P1). SchemaFour: the FATAL tuple, and schema 3's own refusal.
   CycleBackendOnly: train_backend and score_backend are 'cycle' only (row 136),
   and none of the four new FATAL inputs has a default (mistake 19).
   Transmission, BackendContract (unguarded: it reads the real contract),
   Pairing (row 117's rule) and D34Protocol (decision 34's set, on synthetic
   records, and on the real tree, whose redraws.json R4 committed, 34cca5b).

7. THE REWARD'S KNOCK OPTION AND WHAT tit_cap_ecu.py RELIES ON (the plant
   commit P; interface sheet 6.1 and 6.7, P3). RewardKnock: reward_knock is
   True (X1's) by default everywhere, a bool only, and moves r_life alone, to
   row 113 (5)'s thermal-only reading: the trajectory, every other info value,
   the episode's damage and every score evaluate.py returns are the same in
   both modes, and the defaults are GOLDEN's traces. TitCapInterfaces (row
   127 (2)): BaselineECU.step unwrapped in its own class body with its six
   arguments and its 3-tuple; the environment's ECU on the plant's own
   calibration object; the baseline's ECU calls on map_b_prev before its load
   loop. Each has its control.

THE GOLDEN DIGESTS (golden_digests, GOLDEN; interface sheet 6.7, the one
definition): the B58 and each EPA engine at their defaults, bit for bit, as
MEASURED on step 13's tree (D146's, a3cd3a3; row 146 (3): C2 is not built)
before P's edits. test_preview_horizon asserts them (the H default), and so
does P3's RewardKnock (the knock default).

Added 9 October 2026: WBS v3 rows 2.2 and 2.6 named these tests as missing.
"""
import hashlib
import inspect
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

import engine_env as E  # noqa: E402
import engines  # noqa: E402
import fingerprint as FP  # noqa: E402
import thermal  # noqa: E402
from thresholds import common  # noqa: E402

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


def live_fp(**kw):
    """The live B58 block at the defaults: the cycle model in training and scoring, the default H and
    X1's reward (fingerprint schema 4); `kw` overrides or adds."""
    args = dict(train_backend=FP.BACKEND_CYCLE, score_backend=FP.BACKEND_CYCLE, preview_h_s=E.PREVIEW_H_S,
                reward_knock=E.REWARD_KNOCK_DEFAULT)
    args.update(kw)
    return FP.plant_fingerprint(plant=PLANT, **args)


# ------------------------------------------------------------------ the golden digests (interface sheet 6.7)
# MEASURED on step 13's tree (D146's commit a3cd3a3, pushed; row 146 (3) and interface sheet 17, 6.7: C2
# is not built, so the digests are pinned there), before P's edits, by golden_case and golden_digests at
# the defaults, run twice there with the same result (the control), on 6 November 2026. They equal the
# values the drafts measured on C2's scratch tree (a66fb65), which changed no file the cases run. Each
# digest is golden_sha over the per-step digests.
GOLDEN_PARENT = "a3cd3a3"
GOLDEN = {
    "b58 phase-d EPISODES[0], dt 1, 300 steps":
        "765a3090038bbad5b6a15810e9d96d0fe9b31d0de2c6a6ddf14679e046a652b8",
    "b58 ExtremesTrainingEnv(seed=0), 300 steps":
        "dfe74044c64fae7ca97aaada2f94f994dd03eaa55eb9f51164a161eae9897a47",
    "mazda_25t locked climb 120 s, dt 1":
        "179bf76f8130c8d40bf539c6b7f98b5e7995188270e1f2b0bd282643b32dd916",
    "honda_l15b7 locked climb 120 s, dt 1":
        "cc28c567ce1557c3ca46ded6eba94eb3a4f462fe7b88355b21c6afd7bede02b1",
    "ford_27tt locked climb 120 s, dt 1":
        "8f4b47727cce5a6864cfb11104a0f813a4a971523e02e56b74e2efffff9d2ed8",
}


def golden_actions(steps, *, seed):
    """Neutral actions for the first half, then np.random.default_rng(seed) actions."""
    rng = np.random.default_rng(seed)
    for i in range(steps):
        yield E.neutral_action() if i < steps // 2 else rng.uniform(-1.0, 1.0, 5).astype(np.float32)


def _num_bytes(v):
    """A numeric value's float64 bytes, or None for anything else (a dict, a string)."""
    if isinstance(v, (bool, int, float, np.bool_, np.integer, np.floating)):
        return np.float64(v).tobytes()
    if isinstance(v, np.ndarray) and v.dtype.kind in "biuf":
        return np.asarray(v, dtype=np.float64).tobytes()
    return None


def golden_step(obs, r, info):
    """One step's digest: sha256 over the float64 bytes of the reward, the observation and info's numeric
    values in sorted key order."""
    h = hashlib.sha256()
    h.update(np.float64(r).tobytes())
    h.update(np.asarray(obs, dtype=np.float64).tobytes())
    for k in sorted(info):
        b = _num_bytes(info[k])
        if b is not None:
            h.update(b)
    return h.hexdigest()


def golden_digests(env, steps, *, seed):
    """The per-step digests (golden_step) of `steps` steps of an environment its caller has reset, under
    golden_actions(steps, seed=seed), to its first termination or truncation."""
    out = []
    for a in golden_actions(steps, seed=seed):
        obs, r, term, trunc, info = env.step(a)
        out.append(golden_step(obs, r, info))
        if term or trunc:
            break
    return out


def golden_sha(digests):
    return hashlib.sha256("".join(digests).encode()).hexdigest()


def golden_case(name, **env_kw):
    """(env, steps) for a GOLDEN case, built and reset; `env_kw` reaches the environment's constructor
    (nothing, at the defaults the digests were measured at)."""
    if name.startswith("b58 phase-d"):
        import evaluate as V
        p = engines.get("b58")
        seed, w = V.EPISODES[0]
        env = E.SupervisoryTunerEnv(V.episode_cycle(None, plant=p), plant=p, dt=V.DT, seed=seed, **env_kw)
        env.reset(seed=seed)
        env.w = np.asarray(w, dtype=np.float32)          # evaluate.run_episode's order
        return env, 300
    if name.startswith("b58 ExtremesTrainingEnv"):
        env = E.ExtremesTrainingEnv(seed=0, plant=engines.get("b58"), **env_kw)
        env.reset(seed=0)
        return env, 300
    p = engines.get(name.split()[0])
    env = E.SupervisoryTunerEnv(E.locked_climb(p, duration=120.0, dt=1.0), plant=p, dt=1.0, seed=0, **env_kw)
    env.reset(seed=0)
    return env, 120


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


# The FATAL fields schema 4 carries, in format_block's order (the plant commit P; interface sheet 6.2):
# schema 3's, with backend, gears and final_drive replaced by the backend pair, the contract and the
# transmission, and the agent's H and the reward's knock option.
SCHEMA_4_FATAL = ("plant_sha", "derived_sha", "engine", "engine_sha", "train_backend", "score_backend",
                  "backend_contract", "transmission", "dtheta_deg", "turb_protect_k", "oil_protect_k", "scenario",
                  "episodes_sha", "preview_h_s", "reward_knock")
SCHEMA_4_NEW = ("train_backend", "score_backend", "backend_contract", "transmission", "preview_h_s", "reward_knock")


def missing_fatal(fatal):
    """The schema-4 FATAL fields a FATAL tuple leaves out."""
    return [k for k in SCHEMA_4_FATAL if k not in fatal]


class SchemaFour(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.live = live_fp()
        cls.dir = tempfile.mkdtemp(prefix="schema4_")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir, ignore_errors=True)

    def _model(self, name, meta):
        """A run directory holding only `meta` as its meta.json."""
        d = os.path.join(self.dir, name)
        FP.write(os.path.join(d, "meta.json"), meta)
        return d

    def _schema_3(self):
        """The live block as schema 3 wrote it: backend, gears and final_drive, none of schema 4's."""
        old = {k: v for k, v in self.live.items() if k not in SCHEMA_4_NEW + ("preview_samples_s",)}
        return dict(old, schema=3, backend=FP.BACKEND_CYCLE, gears=list(self.live["transmission"]["gears"]),
                    final_drive=self.live["transmission"]["final_drive"])

    def _schema_2(self):
        """The live block as schema 2 wrote it: no engine, engine_sha or backend."""
        old = {k: v for k, v in self._schema_3().items() if k not in ("engine", "engine_sha", "backend")}
        return dict(old, schema=2)

    def test_the_schema_4_fields_are_fatal(self):
        self.assertEqual(FP.FATAL, SCHEMA_4_FATAL)
        self.assertEqual(missing_fatal(FP.FATAL), [])
        self.assertEqual(FP.SCHEMA_VERSION, 4)
        for k in ("engine", "engine_sha") + SCHEMA_4_NEW:
            self.assertIn(k, self.live)
        for k in ("backend", "gears", "final_drive"):
            self.assertNotIn(k, self.live)
        text = FP.format_block(self.live).splitlines()
        self.assertEqual([ln.split()[0] for ln in text[1:1 + len(SCHEMA_4_FATAL)]], list(SCHEMA_4_FATAL))

    def test_the_fatal_check_can_fail(self):
        """The control (mistake 12): a FATAL tuple without preview_h_s is caught."""
        self.assertEqual(missing_fatal(tuple(k for k in FP.FATAL if k != "preview_h_s")), ["preview_h_s"])

    def test_schema_problem_names_an_older_record(self):
        self.assertIsNone(FP.schema_problem(self.live))
        msg = FP.schema_problem(self._schema_3())
        self.assertIn("schema 3, written before the plant commit", msg)
        for k in ("transmission", "train/score backend", "decision-34 protocol", "preview_h_s", "reward knock"):
            self.assertIn(k, msg)
        msg = FP.schema_problem(self._schema_2())
        self.assertIn("schema 2", msg)
        self.assertIn("names no", msg)

    def test_evaluate_refuses_a_schema_2_or_3_model(self):
        import evaluate
        for n, meta in ((2, self._schema_2()), (3, self._schema_3())):
            d = self._model(f"schema{n}", meta)
            with self.assertRaises(SystemExit) as cm:
                evaluate.check_model_fingerprint(d, self.live, False)
            self.assertIn(f"fingerprint schema {n}", str(cm.exception))
            forced = evaluate.check_model_fingerprint(d, self.live, True)
            self.assertTrue(forced and "NOT a result" in forced[0])
        # X1's own meta.json, where this machine has it (runs/ is not in git)
        x1 = os.path.join(HERE, "runs", "extremes_dt1", "sighted_seed0")
        if os.path.exists(os.path.join(x1, "meta.json")):
            with self.assertRaises(SystemExit):
                evaluate.check_model_fingerprint(x1, self.live, False)

    def test_evaluate_passes_a_schema_4_model_of_this_plant_on_each_arm(self):
        import evaluate
        d = self._model("schema4", dict(self.live))
        self.assertEqual([ln for ln in evaluate.check_model_fingerprint(d, self.live, False)
                          if ln.startswith("!!")], [])
        blind = FP.for_arm(self.live, sighted=False)
        d = self._model("schema4_blind", blind)
        self.assertEqual([ln for ln in evaluate.check_model_fingerprint(d, blind, False)
                          if ln.startswith("!!")], [])
        # the control: the blinded agent against the sighted block is refused on preview_h_s
        self.assertEqual([k for k, _, _ in FP.compare(blind, self.live)], ["preview_h_s"])
        with self.assertRaises(SystemExit):
            evaluate.check_model_fingerprint(d, self.live, False)

    def test_another_engine_is_refused_field_by_field(self):
        import evaluate
        other = dict(self.live, engine="another/engine", engine_sha="0" * 16)
        self.assertEqual([k for k, _, _ in FP.compare(other, self.live)], ["engine", "engine_sha"])
        d = self._model("other_engine", other)
        with self.assertRaises(SystemExit):
            evaluate.check_model_fingerprint(d, self.live, False)

    def test_train_refuses_a_schema_2_or_3_run_directory(self):
        import train
        for n, meta in ((2, self._schema_2()), (3, self._schema_3())):
            with self.assertRaises(SystemExit) as cm:
                train.refuse_old_schema(meta, "runs_x/sighted_seed0", False)
            self.assertIn(f"fingerprint schema {n}", str(cm.exception))
            train.refuse_old_schema(meta, "runs_x/sighted_seed0", True)          # forced
        train.refuse_old_schema(None, "runs_x/sighted_seed0", False)              # a fresh directory
        train.refuse_old_schema(dict(self.live), "runs_x/sighted_seed0", False)


class CycleBackendOnly(unittest.TestCase):
    """Row 136: every engine trains and is scored on the exact cycle, so 'cycle' is the only backend
    string; and none of schema 4's four FATAL inputs has a default (mistake 19; interface sheet 1.7)."""

    def test_the_four_inputs_have_no_default(self):
        params = inspect.signature(FP.plant_fingerprint).parameters
        full = dict(train_backend=FP.BACKEND_CYCLE, score_backend=FP.BACKEND_CYCLE, preview_h_s=30.0,
                    reward_knock=True)
        for k in full:
            self.assertIs(params[k].default, inspect.Parameter.empty, k)
            self.assertIs(params[k].kind, inspect.Parameter.KEYWORD_ONLY, k)
            with self.assertRaises(TypeError, msg=k):
                FP.plant_fingerprint(plant=PLANT, **{n: v for n, v in full.items() if n != k})
        self.assertNotIn("backend", params)
        with self.assertRaises(TypeError):
            FP.plant_fingerprint(plant=None, **full)

    def test_every_backend_but_cycle_is_refused(self):
        for bad in ("table:0123", "table:" + "0123456789abcdef" * 4, "Cycle", "", None):
            for k in ("train_backend", "score_backend"):
                with self.assertRaises(ValueError, msg=(k, bad)):
                    live_fp(**{k: bad})
        fp = live_fp()                                                    # the control
        self.assertEqual((fp["train_backend"], fp["score_backend"]), (FP.BACKEND_CYCLE, FP.BACKEND_CYCLE))

    def test_backend_of_reads_the_environment(self):
        """A plain environment runs the cycle model (the control); one given an engine_model is refused,
        never called "cycle"; a wrapper is a TypeError."""
        env = E.SupervisoryTunerEnv(E.locked_climb(PLANT, duration=60.0, dt=1.0), plant=PLANT, dt=1.0)
        self.assertEqual(FP.backend_of(env), FP.BACKEND_CYCLE)
        surrogate = E.SupervisoryTunerEnv(E.locked_climb(PLANT, duration=60.0, dt=1.0), plant=PLANT, dt=1.0,
                                          engine_model=object())
        with self.assertRaises(ValueError):
            FP.backend_of(surrogate)
        with self.assertRaises(TypeError):
            FP.backend_of(object())

    def test_the_other_inputs_are_refused_when_wrong(self):
        for kw, exc in ((dict(reward_knock=1), TypeError), (dict(reward_knock=None), TypeError),
                        (dict(reward_knock=np.bool_(True)), TypeError), (dict(preview_h_s=True), TypeError),
                        (dict(preview_h_s="30"), TypeError), (dict(preview_h_s=0.0), ValueError),
                        (dict(preview_h_s=float("nan")), ValueError),
                        (dict(preview_h_s=None, use_preview=True), ValueError),
                        (dict(preview_h_s=30.0, use_preview=False), ValueError),
                        (dict(transmission={"kind": "stepped"}), ValueError),
                        (dict(backend_contract={}), ValueError), (dict(protocol="d3"), ValueError)):
            with self.assertRaises(exc, msg=repr(kw)):
                live_fp(**kw)
        # the controls: each arm's own use_preview, and an H of 71 s
        self.assertIsNone(live_fp(preview_h_s=None, use_preview=False)["preview_h_s"])
        fp = live_fp(preview_h_s=71.0, use_preview=True)
        self.assertEqual((fp["preview_h_s"], fp["preview_samples_s"]), (71.0, list(E.preview_samples(71.0))))
        self.assertIs(live_fp(reward_knock=False)["reward_knock"], False)


class Transmission(unittest.TestCase):
    def test_the_supra_is_stepped(self):
        t = FP.transmission_of(PLANT.car)
        self.assertEqual(t, {"kind": "stepped", "gears": [5.25, 3.36, 2.172, 1.72, 1.316, 1.0, 0.822, 0.64],
                             "final_drive": 3.15})
        self.assertEqual(live_fp()["transmission"], t)

    def test_each_calibrated_epa_plant(self):
        """The Accord's CVT records its ratio range, final drive and law, each a float read from the car
        record; the stepped EPA cars their gears. A plant not calibrated yet is skipped by name."""
        for name in ("mazda_25t", "honda_l15b7", "ford_27tt"):
            with self.subTest(plant=name):
                if not engines.calibrated(name):
                    self.skipTest(f"{name} is not calibrated yet")
                car = engines.get(name).car
                t = FP.transmission_of(car)
                if type(car) is engines.CvtCar:
                    self.assertEqual(list(t), ["kind", "ratio_low_gear", "ratio_top_gear", "final_drive",
                                               "kickdown_load", "target_load", "cvt_rpm_min"])
                    self.assertEqual(t["kind"], "cvt")
                    for k in list(t)[1:]:
                        self.assertIs(type(t[k]), float)
                        self.assertEqual(t[k], getattr(car, k))
                else:
                    self.assertIs(type(car), engines.EpaCar)
                    self.assertEqual(t, {"kind": "stepped", "gears": [float(g) for g in car.gears],
                                         "final_drive": float(car.final_drive)})
        self.assertIs(type(engines.get("honda_l15b7").car), engines.CvtCar)

    def test_anything_else_is_a_type_error(self):
        from dataclasses import make_dataclass
        Other = make_dataclass("Other", [("gears", tuple), ("final_drive", float)])
        for bad in (object(), None, Other((1.0,), 3.0)):
            with self.assertRaises(TypeError):
                FP.transmission_of(bad)


class BackendContract(unittest.TestCase):
    """Unguarded on purpose: the one test that reads the real contract (interface sheet 1.8)."""

    def test_it_is_the_two_files_sha_text(self):
        want = {"md_sha_text": common.sha_text(common.CONTRACT_MD),
                "json_sha_text": common.sha_text(common.CONTRACT_JSON)}
        self.assertEqual(FP.backend_contract(), want)
        self.assertIn("backend_contract", FP.FATAL)
        live = live_fp()
        self.assertEqual(live["backend_contract"], want)
        # the control (mistake 12): one character of md_sha_text, and compare names the field alone
        other = dict(live, backend_contract=dict(want, md_sha_text=("0" if want["md_sha_text"][0] != "0" else "1")
                                                 + want["md_sha_text"][1:]))
        self.assertEqual([k for k, _, _ in FP.compare(other, live)], ["backend_contract"])

    def test_it_is_read_at_the_call_through_the_module_global(self):
        stand_in = {"md_sha_text": "stand-in", "json_sha_text": "stand-in"}
        with mock.patch.object(FP, "backend_contract", lambda: stand_in):
            self.assertEqual(live_fp()["backend_contract"], stand_in)
        self.assertNotEqual(live_fp()["backend_contract"], stand_in)


class Pairing(unittest.TestCase):
    """Row 117: a sighted agent pairs with the blinded agent whose every FATAL field but preview_h_s
    agrees, the sighted H a positive finite float and the blinded H None."""

    @classmethod
    def setUpClass(cls):
        cls.sighted = live_fp(preview_h_s=71.0)

    def test_a_sighted_and_a_blinded_block_pair(self):
        blind = FP.for_arm(self.sighted, sighted=False)
        self.assertEqual(FP.pair_problems(self.sighted, blind), [])
        self.assertEqual((blind["preview_h_s"], blind["preview_samples_s"]), (None, None))
        self.assertEqual(self.sighted["preview_h_s"], 71.0)                  # a copy: the original is kept
        same = FP.for_arm(self.sighted, sighted=True)
        self.assertEqual(same, self.sighted)
        self.assertIsNot(same, self.sighted)

    def test_what_does_not_pair(self):
        blind = FP.for_arm(self.sighted, sighted=False)
        self.assertEqual(FP.pair_problems(self.sighted, dict(blind, plant_sha="0" * 16)),
                         [("plant_sha", self.sighted["plant_sha"], "0" * 16)])
        self.assertEqual(FP.pair_problems(self.sighted, dict(blind, reward_knock=False)),
                         [("reward_knock", True, False)])
        for s, b in ((blind, blind), (self.sighted, self.sighted), (live_fp(preview_h_s=30.0), self.sighted),
                     (dict(self.sighted, preview_h_s=float("inf")), blind), (dict(self.sighted, preview_h_s=71), blind)):
            self.assertTrue(any(f == "preview_h_s" for f, _, _ in FP.pair_problems(s, b)), (s["preview_h_s"],
                                                                                           b["preview_h_s"]))
        self.assertIn("schema", [f for f, _, _ in FP.pair_problems(self.sighted, dict(blind, schema=3))])


class D34Protocol(unittest.TestCase):
    """Decision 34's set (d34_roads, d34_set; interface sheet 6.2 and 12.10), on SYNTHETIC records in a
    temporary root: no vehicle and no real record is read, apart from evaluate.py's EPISODES literal
    (copied). The real tree's REAL record is refused until R4 commits redraws.json, and read after it."""

    def setUp(self):
        import epa_roads as ER
        self.ER = ER
        self.root = tempfile.mkdtemp(prefix="d34_")
        shutil.copy(os.path.join(HERE, "evaluate.py"), self.root)
        os.makedirs(os.path.join(self.root, os.path.dirname(ER.ROADS_REL)))
        self.episodes = ER.frozen_episodes(root=self.root)
        self.roads = [{"k": k, "episode_seed": s, "weights": list(w), "label": f"SYNTHETIC road {k}",
                       "cycle": {"t": [0.0, 1.0, 2.0, 3.0, 4.0], "v_mps": [30.0] * 5,
                                 "grade": [0.0, 0.01 * k, 0.02, 0.0, 0.0], "t_amb": 315.15}}
                      for k, (s, w) in enumerate(self.episodes)]
        self.record = {"seed_kind": "SYNTHETIC", "design": {"dt": 1.0, "duration_s": 900.0, "n_roads": 20},
                       "commit_reveal": {"SYNTHETIC": True, "roads_seed": 4242}, "roads": self.roads}

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write(self, rel, d):
        with open(os.path.join(self.root, rel), "w", encoding="utf-8") as fh:
            json.dump(d, fh)
        return os.path.join(self.root, rel)

    def _redraws(self, roads=None, roads_sha=None):
        path = os.path.join(self.root, self.ER.ROADS_REL)
        return self._write(self.ER.REDRAWS_REL, {"roads_sha": roads_sha or self.ER.roads_sha(path),
                                                 "readings": {"version 6": {"roads": roads or self.roads}}})

    def test_a_synthetic_first_draw(self):
        path = self._write(self.ER.ROADS_REL, self.record)
        sc, roads = FP.d34_roads(root=self.root)
        self.assertEqual(sc, {"protocol": "decision-34", "seed_kind": "SYNTHETIC", "roads_sha": common.sha_text(path),
                              "redraws_sha": None, "reading": "first draw",
                              "design_sha": hashlib.sha256(json.dumps(self.record["design"], sort_keys=True)
                                                           .encode()).hexdigest()[:16]})
        self.assertEqual(roads, self.roads)
        _, entries = FP.d34_set(root=self.root)
        self.assertEqual([e[:3] for e in entries], [(k, s, tuple(w)) for k, (s, w) in enumerate(self.episodes)])
        self.assertEqual(entries[3][3], self.ER.arrays_sha256([self.roads[3]]))
        text = json.dumps(sc)
        for never in ("commit_reveal", "roads_seed", "4242"):
            self.assertNotIn(never, text)

    def test_the_version_6_reading(self):
        self._write(self.ER.ROADS_REL, self.record)
        redrawn = json.loads(json.dumps(self.roads))
        redrawn[7]["cycle"]["grade"][2] = 0.05
        rpath = self._redraws(redrawn)
        sc, roads = FP.d34_roads(root=self.root)
        self.assertEqual((sc["reading"], sc["redraws_sha"]), ("version 6", common.sha_text(rpath)))
        self.assertEqual(roads, redrawn)
        self.assertEqual(FP.d34_set(root=self.root)[1][7][3], self.ER.arrays_sha256([redrawn[7]]))

    def test_the_hash_moves_on_a_grade_sample_a_weight_or_the_order(self):
        """The controls (mistake 12): what d34_set's entries hold moves the hash episodes_sha takes."""
        def sha(roads):
            return hashlib.sha256(repr(FP._d34_entries(roads)).encode()).hexdigest()[:16]
        base = sha(self.roads)
        grade = json.loads(json.dumps(self.roads))
        grade[0]["cycle"]["grade"][1] += 1e-12
        weight = json.loads(json.dumps(self.roads))
        weight[0]["weights"][0] += 1e-12
        for moved in (grade, weight, self.roads[1:2] + self.roads[:1] + self.roads[2:]):
            self.assertNotEqual(sha(moved), base)
        self.assertEqual(sha(json.loads(json.dumps(self.roads))), base)

    def test_what_is_refused(self):
        self._write(self.ER.ROADS_REL, dict(self.record, seed_kind="REAL"))
        with self.assertRaisesRegex(ValueError, "without"):
            FP.d34_roads(root=self.root)                                     # REAL, no redraws.json
        self._redraws()
        self.assertEqual(FP.d34_roads(root=self.root)[0]["seed_kind"], "REAL")   # the control
        self._redraws(roads_sha="0" * 64)
        with self.assertRaisesRegex(ValueError, "another roads.json"):
            FP.d34_roads(root=self.root)
        os.remove(os.path.join(self.root, self.ER.REDRAWS_REL))
        for change in ("seed", "weight", "order", "nineteen"):
            roads = json.loads(json.dumps(self.roads))
            if change == "seed":
                roads[4]["episode_seed"] += 1
            elif change == "weight":
                roads[4]["weights"][1] = 0.5
            elif change == "order":
                roads[2], roads[3] = roads[3], roads[2]
            else:
                roads = roads[:19]
            self._write(self.ER.ROADS_REL, dict(self.record, roads=roads))
            with self.assertRaises(ValueError, msg=change):
                FP.d34_roads(root=self.root)

    def test_the_fingerprint_under_d34(self):
        """plant_fingerprint('d34') on the synthetic version-6 reading: the design's dt and duration,
        twenty episodes, and a caller's advisory value that differs is refused."""
        self._write(self.ER.ROADS_REL, self.record)
        self._redraws()
        real = FP._d34
        with mock.patch.object(FP, "_d34", lambda root: real(self.root)):
            fp = live_fp(protocol="d34")
            self.assertEqual(fp["scenario"]["reading"], "version 6")
            self.assertEqual((fp["eval_dt"], fp["eval_duration"], fp["n_episodes"]), (1.0, 900.0, 20))
            self.assertEqual(fp["episodes_sha"],
                             hashlib.sha256(repr(FP.d34_set(root=self.root)[1]).encode()).hexdigest()[:16])
            self.assertNotEqual(fp["episodes_sha"], FP.episodes_sha("phase-d"))
            self.assertEqual(live_fp(protocol="d34", eval_dt=1.0, n_episodes=20)["episodes_sha"], fp["episodes_sha"])
            for kw in (dict(eval_dt=0.2), dict(eval_duration=720.0), dict(n_episodes=19), dict(scenario={}),
                       dict(episodes_sha="0" * 16)):
                with self.assertRaises(ValueError, msg=repr(kw)):
                    live_fp(protocol="d34", **kw)
            for never in ("commit_reveal", "roads_seed"):
                self.assertNotIn(never, json.dumps(fp))

    def test_the_real_tree(self):
        """The tree's roads record, REAL, read under version 6 of the redraws.json R4 committed (ORDER step
        12, 34cca5b): both files are required, never skipped; the scenario names both by their hashes and
        holds nothing of commit_reveal. The control (mistake 12): the same REAL record without its
        redraws.json is refused, in a copy of the two files."""
        import epa_roads as ER
        roads, redraws = (os.path.join(HERE, *rel.split("/")) for rel in (ER.ROADS_REL, ER.REDRAWS_REL))
        self.assertTrue(os.path.exists(roads) and os.path.exists(redraws), "R4 (34cca5b) committed both")
        fp = live_fp(protocol="d34")
        sc = fp["scenario"]
        self.assertEqual((sc["protocol"], sc["seed_kind"], sc["reading"], fp["n_episodes"]),
                         ("decision-34", "REAL", "version 6", 20))
        self.assertEqual((sc["roads_sha"], sc["redraws_sha"]), (ER.roads_sha(roads), common.sha_text(redraws)))
        self.assertEqual(fp["episodes_sha"], FP.episodes_sha("d34"))
        self.assertEqual((fp["eval_dt"], fp["eval_duration"]), (1.0, 900.0))
        for never in ("commit_reveal", "roads_seed"):
            self.assertNotIn(never, json.dumps(fp))
        root = tempfile.mkdtemp(prefix="d34_real_")
        try:
            shutil.copy(os.path.join(HERE, "evaluate.py"), root)
            os.makedirs(os.path.join(root, os.path.dirname(ER.ROADS_REL)))
            shutil.copy(roads, os.path.join(root, ER.ROADS_REL))
            with self.assertRaisesRegex(ValueError, "without"):
                FP.d34_roads(root=root)
        finally:
            shutil.rmtree(root, ignore_errors=True)


class GitDirtyPlantFiles(unittest.TestCase):
    """The fingerprint's advisory git_dirty_plant_files names EVERY dirty plant
    file, and only those (22 October 2026, build step 2 P7; exact since the plant
    commit P, row 127 (5)). fingerprint._git stripped the whole of `git status
    --porcelain`, and so the leading space of its first line alone: " M
    engine_env.py" became "M engine_env.py", its path was read as "ngine_env.py",
    and the first dirty file -- engine_env.py, during WP1 -- was never named; and
    the match was by suffix, so a dirty car_thermal.py named thermal.py. git is
    not asked here: subprocess.run, which _git calls, answers with a fixed
    NUL-separated porcelain and a fixed prefix."""

    PORCELAIN = " M engine_env.py\0 M engines.py\0?? notes.txt\0M  plant.py\0"

    def _fingerprint(self, porcelain, prefix="", calls=None, fail=()):
        real = subprocess.run

        def run(args, *a, **kw):
            args = tuple(args)
            if calls is not None:
                calls.append(args)
            if args[1:2] == ("status",) or args[1:3] == ("rev-parse", "--show-prefix"):
                if args[1] in fail:
                    return subprocess.CompletedProcess(args, 128, stdout="", stderr="fatal")
                out = porcelain if args[1] == "status" else prefix + "\n"
                return subprocess.CompletedProcess(args, 0, stdout=out, stderr="")
            if args[1:3] == ("rev-parse", "HEAD"):
                return subprocess.CompletedProcess(args, 0, stdout="0123abcd\n", stderr="")
            return real(args, *a, **kw)
        with mock.patch.object(FP.subprocess, "run", side_effect=run):
            return live_fp()

    def test_the_first_dirty_plant_file_is_named(self):
        """Every plant file the porcelain lists, the first among them, whatever its
        status columns; the untracked note is not a plant file. git_head keeps its
        hash without the newline, as strip() gave it."""
        calls = []
        fp = self._fingerprint(self.PORCELAIN, calls=calls)
        self.assertEqual(fp["git_dirty_plant_files"], ["engine_env.py", "engines.py", "plant.py"])
        self.assertIs(fp["git_dirty"], True)
        self.assertEqual(fp["git_head"], "0123abcd")
        status = [c for c in calls if c[1:2] == ("status",)]
        self.assertEqual(status, [("git", "status", "--porcelain=v1", "-z", "--no-renames", "--untracked-files=all")])

    def test_the_match_is_exact(self):
        """A file whose name ends with a plant file's is not that file; the control is thermal.py itself."""
        fp = self._fingerprint(" M car_thermal.py\0 M calibrate_thermal.py\0?? analyse_four_engines.py\0")
        self.assertEqual((fp["git_dirty"], fp["git_dirty_plant_files"]), (True, []))
        self.assertEqual(self._fingerprint(" M thermal.py\0")["git_dirty_plant_files"], ["thermal.py"])

    def test_a_rename_names_the_old_path(self):
        self.assertEqual(self._fingerprint("D  engines.py\0?? engines2.py\0")["git_dirty_plant_files"],
                         ["engines.py"])

    def test_the_prefix_is_this_directorys(self):
        self.assertEqual(self._fingerprint(" M sub/engine_env.py\0", prefix="sub/")["git_dirty_plant_files"],
                         ["engine_env.py"])
        self.assertEqual(self._fingerprint(" M engine_env.py\0", prefix="sub/")["git_dirty_plant_files"], [])

    def test_a_clean_tree_names_none(self):
        """The control: an empty porcelain is a clean tree, not an unknown one."""
        fp = self._fingerprint("")
        self.assertEqual((fp["git_dirty"], fp["git_dirty_plant_files"]), (False, []))

    def test_no_git_is_unknown(self):
        for fail in (("status",), ("rev-parse",)):
            fp = self._fingerprint(self.PORCELAIN, fail=fail)
            self.assertEqual((fp["git_dirty"], fp["git_dirty_plant_files"]), (None, None), fail)

# ------------------------------------------------------------------ the knock option (P3; interface sheet 6.1, 6.7)
def retard_then_random(steps, *, seed):
    """A fixed retard for the first half (the spark trim at its -1 end, the rest neutral), then
    np.random.default_rng(seed) uniform actions: the retard keeps the agent off the knock its baseline
    has, and the random half reaches knock of its own."""
    rng = np.random.default_rng(seed)
    for i in range(steps):
        if i < steps // 2:
            a = E.neutral_action().copy()
            a[0] = -1.0
            yield a
        else:
            yield rng.uniform(-1.0, 1.0, 5).astype(np.float32)


def thermal_r_life(env):
    """Row 113 (5)'s primary reading of r_life, from the two networks as the step left them: the damage
    rate without the knock term (engine_env.damage_rate with no knock integral)."""
    cal = env.plant.engine.damage
    l_a = E.damage_rate(env.thermal.t_turb, env.thermal.t_oil, cal=cal)
    l_b = E.damage_rate(env.thermal_base.t_turb, env.thermal_base.t_oil, cal=cal)
    return (l_b - l_a) / (l_b + 0.05)


class RewardKnock(unittest.TestCase):
    """THE REWARD'S KNOCK OPTION (rows 113 (5), 117, 118; the plant commit P). SupervisoryTunerEnv's
    reward_knock, True by default (X1's), moves r_life alone: the trajectory, every other info value and
    the episode's damage, both readings of which stay available, are the same in both modes, and the
    defaults are the pre-P traces bit for bit (GOLDEN)."""

    def test_the_default_is_x1s_knock_in(self):
        import evaluate
        import train
        self.assertIs(E.REWARD_KNOCK_DEFAULT, True)
        for fn in (E.SupervisoryTunerEnv.__init__, evaluate.run_episode, train.build_env):
            with self.subTest(fn=fn.__qualname__):
                p = inspect.signature(fn).parameters["reward_knock"]
                self.assertIs(p.default, True)
                self.assertEqual(p.kind, inspect.Parameter.KEYWORD_ONLY)
        b58, mazda = engines.get("b58"), engines.get("mazda_25t")
        four = dict(scored_share=False, roads_record=None)

        def builds(**kw):
            return (("SupervisoryTunerEnv b58", lambda: E.SupervisoryTunerEnv(
                        E.locked_climb(b58, duration=60.0, dt=1.0), plant=b58, dt=1.0, **kw)),
                    ("EngineEnv b58", lambda: E.EngineEnv(plant=b58, **kw)),
                    ("TerrainTrainingEnv b58", lambda: E.TerrainTrainingEnv(seed=0, plant=b58, **kw)),
                    ("ExtremesTrainingEnv b58", lambda: E.ExtremesTrainingEnv(seed=0, plant=b58, **kw)),
                    ("build_env four_engine mazda_25t", lambda: train.build_env(
                        True, 0, 900.0, "four_engine", 1.0, plant=mazda, **kw, **four)))
        for want, kw in ((True, {}), (False, dict(reward_knock=False))):
            for name, make in builds(**kw):
                with self.subTest(name, reward_knock=kw or "default"):
                    self.assertIs(make().unwrapped.reward_knock, want)
                    self.assertIs(FP.reward_knock_of(make().unwrapped), want)

    def test_only_a_bool(self):
        """'out' is truthy, so a string would train the knock term while saying it did not."""
        for bad in ("out", "in", 0, 1, None, np.bool_(False), np.bool_(True)):
            with self.subTest(value=repr(bad)), self.assertRaisesRegex(TypeError, r"row 113 \(5\)"):
                E.SupervisoryTunerEnv(E.locked_climb(PLANT, duration=60.0, dt=1.0), plant=PLANT, dt=1.0,
                                      reward_knock=bad)
        for good in (True, False):                                            # the control
            self.assertIs(E.SupervisoryTunerEnv(E.locked_climb(PLANT, duration=60.0, dt=1.0), plant=PLANT,
                                                dt=1.0, reward_knock=good).reward_knock, good)

    def test_the_option_moves_the_reward_and_nothing_else(self):
        p = engines.get("mazda_25t")
        envs = [E.SupervisoryTunerEnv(E.locked_climb(p, duration=120.0, dt=1.0), plant=p, dt=1.0, seed=0,
                                      reward_knock=rk) for rk in (True, False)]
        for env in envs:
            env.reset(seed=0)
        moved, r_life_off, steps = 0, [], 0
        for a in retard_then_random(120, seed=7):
            (o1, r1, t1, u1, i1), (o2, r2, t2, u2, i2) = (env.step(a.copy()) for env in envs)
            steps += 1
            self.assertTrue(np.array_equal(o1, o2), f"step {steps}: the observation moved with the option")
            self.assertEqual((t1, u1), (t2, u2))
            self.assertEqual(set(i1), set(i2))
            self.assertEqual({k: v for k, v in i1.items() if k != "r_life"},
                             {k: v for k, v in i2.items() if k != "r_life"}, f"step {steps}")
            self.assertEqual(i2["r_life"], thermal_r_life(envs[1]))
            r_life_off.append(i2["r_life"])
            moved += r1 != r2
            if t1 or u1:
                break
        self.assertIn("episode_summary", i1)
        self.assertEqual(i1["episode_summary"], i2["episode_summary"])
        # the damage both readings come from keeps the knock term in both modes (row 113 (5))
        self.assertEqual(envs[1].ep["damage"], envs[0].ep["damage"])
        self.assertGreater(moved, 0, "the reward never moved with the option: the check could not fail")
        self.assertLess(max(r_life_off), 1.0)                     # TRACK_HINGE's premise, r_life <= 1
        print(f"\n  knock option, mazda_25t locked climb: obs and info equal at {steps} steps; the reward "
              f"moved at {moved}; max r_life without the knock term {max(r_life_off):+.4f}")

    def test_scores_do_not_move_with_the_option(self):
        """evaluate.run_episode on EPISODES[0], cut to 300 s (the climb starts at 180 s; the two 300 s
        episodes ran in 57 s on the team laptop, MEASURED 5 November 2026, so the full 720 s would cost
        2.4 times that): every score is the same in both modes, and only ret moves (the control)."""
        import evaluate as V
        seed, w = V.EPISODES[0]

        def policy(env, obs):
            a = E.neutral_action().copy()
            a[0] = -1.0
            return a
        with mock.patch.object(V, "DURATION", 300.0):
            rows = {rk: V.run_episode(policy, seed, w, plant=PLANT, reward_knock=rk) for rk in (True, False)}
        for k in ("damage", "damage_thermal", "fuel", "torque_viol", "peak_turb", "knock"):
            with self.subTest(score=k):
                self.assertEqual(rows[True][k], rows[False][k])
        self.assertNotEqual(rows[True]["ret"], rows[False]["ret"], "ret did not move: the check could not fail")
        print(f"\n  run_episode, b58 EPISODES[0] to 300 s, fixed retard: ret {rows[True]['ret']:+.4f} with the "
              f"knock term, {rows[False]['ret']:+.4f} without; damage {rows[True]['damage']:.6g} both")

    def test_the_defaults_are_the_pre_P_traces(self):
        """reward_knock=True passed is the pre-P trace bit for bit (GOLDEN, MEASURED on a3cd3a3) on the B58 at its
        defaults and on the Ford, whose trace tit_cap_ecu uses; every GOLDEN case at the default, which
        test_the_default_is_x1s_knock_in reads as True, is asserted on the same pins by test_preview_horizon
        (the H default), so it is not run twice. The control: with False the Mazda's trace moves."""
        for name in ("b58 phase-d EPISODES[0], dt 1, 300 steps", "ford_27tt locked climb 120 s, dt 1"):
            with self.subTest(name):
                env, steps = golden_case(name, reward_knock=True)
                self.assertEqual(golden_sha(golden_digests(env, steps, seed=0)), GOLDEN[name])
        name = "mazda_25t locked climb 120 s, dt 1"
        env, steps = golden_case(name, reward_knock=False)
        self.assertNotEqual(golden_sha(golden_digests(env, steps, seed=0)), GOLDEN[name])


# ------------------------------------------------------------------ what tit_cap_ecu.py relies on (row 127 (2))
def _ast_of(rel):
    import ast
    with open(os.path.join(HERE, rel), encoding="utf-8") as fh:
        return ast.parse(fh.read())


def _class_def(tree, name):
    import ast
    return next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)


def ecu_call_problems(src):
    """What is wrong, in SupervisoryTunerEnv.step's source text `src`, with the baseline ECU's calls that
    tit_cap_ecu.capped relies on: exactly one self.ecu.step(self.rpm, self.map_b_prev, ...) and one
    self.ecu.cam_deg(self.rpm, self.map_b_prev), both before the baseline's load loop (the assignment of
    the tuple (base, map_b) from self._track_torque), and self.map_b_prev = map_b after it."""
    import ast
    tree = ast.parse(src)
    step = next(n for n in _class_def(tree, "SupervisoryTunerEnv").body
                if isinstance(n, ast.FunctionDef) and n.name == "step")

    def is_self(node, attr):
        return (isinstance(node, ast.Attribute) and node.attr == attr and isinstance(node.value, ast.Name)
                and node.value.id == "self")

    def ecu_call(node, meth):
        return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == meth
                and is_self(node.func.value, "ecu"))
    calls = {m: [n for n in ast.walk(step) if ecu_call(n, m)] for m in ("step", "cam_deg")}
    loop = [n for n in ast.walk(step) if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Tuple)
            and [getattr(e, "id", None) for e in n.targets[0].elts] == ["base", "map_b"]
            and isinstance(n.value, ast.Call) and is_self(n.value.func, "_track_torque")]
    keep = [n for n in ast.walk(step) if isinstance(n, ast.Assign) and is_self(n.targets[0], "map_b_prev")
            and isinstance(n.value, ast.Name) and n.value.id == "map_b"]
    problems = []
    if len(loop) != 1:
        return [f"{len(loop)} baseline load loops (base, map_b) in step(), not 1"]
    for m, want_n in (("step", 6), ("cam_deg", 2)):
        if len(calls[m]) != 1:
            problems.append(f"{len(calls[m])} self.ecu.{m}(...) calls in step(), not 1")
            continue
        c = calls[m][0]
        if len(c.args) != want_n or c.keywords:
            problems.append(f"self.ecu.{m} takes {len(c.args)} positional arguments and {len(c.keywords)} "
                            f"keywords, not {want_n} and 0")
        elif not (is_self(c.args[0], "rpm") and is_self(c.args[1], "map_b_prev")):
            problems.append(f"self.ecu.{m}'s first two arguments are not self.rpm and self.map_b_prev")
        if c.lineno >= loop[0].lineno:
            problems.append(f"self.ecu.{m} is called after the baseline's load loop")
    if len(keep) != 1 or keep[0].lineno <= loop[0].lineno:
        problems.append("self.map_b_prev = map_b is not set once, after the baseline's load loop")
    return problems


class TitCapInterfaces(unittest.TestCase):
    """Row 127 (2): what tit_cap_ecu.capped relies on, which the plant commit keeps. MEASURED by the audit
    of row 127: wrapping BaselineECU.step, or building the ECU on an equal copy of the calibration, leaves
    the B58's and the Ford's traces bit-identical and passes every other test, yet capped() refuses
    (tit_cap_ecu.py: ORIGINAL_QUALNAME, and its `self.cal is not cal` identity rule). test_tit_cap.py is the
    check of capped() itself; these pin the interfaces at their source."""

    def test_baseline_ecu_step_is_unwrapped_in_its_own_body(self):
        import ast
        fn = E.BaselineECU.__dict__["step"]
        self.assertEqual((fn.__qualname__, fn.__module__), ("BaselineECU.step", "engine_env"))
        self.assertFalse(hasattr(fn, "__wrapped__"))
        self.assertEqual(list(inspect.signature(fn).parameters),
                         ["self", "rpm", "map_kpa", "iat_k", "ect_k", "knock_observed", "dt"])
        self.assertEqual(list(inspect.signature(E.BaselineECU.__dict__["cam_deg"]).parameters),
                         ["self", "rpm", "map_kpa"])
        body = _class_def(_ast_of("engine_env.py"), "BaselineECU").body
        defs = [n for n in body if isinstance(n, ast.FunctionDef) and n.name == "step"]
        self.assertEqual(len(defs), 1)
        self.assertEqual(defs[0].decorator_list, [])
        for name in ("b58", "ford_27tt"):
            with self.subTest(name):
                out = E.BaselineECU(engines.get(name).engine.ecu).step(2706.0, 175.0, 330.0, 363.0, False, 1.0)
                self.assertIsInstance(out, tuple)
                self.assertEqual([type(x) for x in out], [float, float, float])

    def test_the_env_builds_the_ecu_on_the_plants_own_calibration(self):
        import train
        b58, ford = engines.get("b58"), engines.get("ford_27tt")
        four = dict(scored_share=False, roads_record=None)
        for rk in (True, False):
            for name, plant, make in (
                    ("SupervisoryTunerEnv b58", b58, lambda: E.SupervisoryTunerEnv(
                        E.locked_climb(b58, duration=60.0, dt=1.0), plant=b58, dt=1.0, reward_knock=rk)),
                    ("SupervisoryTunerEnv ford_27tt", ford, lambda: E.SupervisoryTunerEnv(
                        E.locked_climb(ford, duration=60.0, dt=1.0), plant=ford, dt=1.0, reward_knock=rk)),
                    ("TerrainTrainingEnv b58", b58, lambda: E.TerrainTrainingEnv(seed=0, plant=b58, reward_knock=rk)),
                    ("ExtremesTrainingEnv b58", b58, lambda: E.ExtremesTrainingEnv(seed=0, plant=b58,
                                                                                   reward_knock=rk)),
                    ("build_env four_engine ford_27tt", ford, lambda: train.build_env(
                        True, 0, 900.0, "four_engine", 1.0, plant=ford, reward_knock=rk, **four))):
                with self.subTest(name, reward_knock=rk):
                    env = make().unwrapped
                    self.assertIs(type(env.ecu), E.BaselineECU)
                    self.assertIs(env.ecu.cal, plant.engine.ecu)
        # the control: an equal copy is another object, which the identity check tells apart
        import copy
        self.assertIsNot(E.BaselineECU(copy.copy(b58.engine.ecu)).cal, b58.engine.ecu)

    def test_the_baseline_ecu_calls_read_map_b_prev(self):
        with open(os.path.join(HERE, "engine_env.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(ecu_call_problems(src), [])
        # the control (mistake 12): the ECU scheduled on the agent's own MAP is reported
        old = "self.ecu.step(self.rpm, self.map_b_prev,"
        self.assertEqual(src.count(old), 1)
        self.assertTrue(ecu_call_problems(src.replace(old, "self.ecu.step(self.rpm, self.map_kpa,")))
        self.assertTrue(ecu_call_problems(src.replace("cam_b = self.ecu.cam_deg(self.rpm, self.map_b_prev)",
                                                      "cam_b = self.ecu.cam_deg(self.rpm, self.map_kpa)")))


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

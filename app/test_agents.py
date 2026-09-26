"""The agent replay page's own suite. Nothing here writes, trains or evaluates.

    python -m app.test_agents          the default suite
    python -m app.test_agents --full   adds the slow checks

Run from the repository root. app/test_replay.py's test_read_only scans this
file too, so banned tokens are written as raw regexes, never as calls, and
fixtures are made in temporary directories OUTSIDE the repository.
"""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import unittest
from unittest import mock

import numpy as np

import fingerprint as FP
from app import agent_catalog as AC
from app import agent_trace as T
from engine_env import (ACT_HI, ACT_LO, SLEW, SupervisoryTunerEnv, make_grade_climb,
                        neutral_action)
from evaluate import EPISODES, EPISODES_D2, agent_policy, run_episode

ROOT = Path(__file__).resolve().parent.parent
FULL = "--full" in sys.argv

C4_SEEDS = range(8)
HAVE_C4 = all((ROOT / "runs_c4" / f"{arm}_seed{k}" / "final.zip").is_file()
              for arm in ("sighted", "blind") for k in C4_SEEDS)
NO_C4 = "runs_c4/ is not on this machine: the catalog path is UNPROVEN here"


class TraceTests(unittest.TestCase):
    """agent_trace: episodes, cycles, road geometry, JSON safety, the mirror."""

    def test_jsonable_converts_numpy(self):
        got = T.jsonable({"a": np.float32(0.3), "b": np.bool_(True),
                          "c": float("nan"), "d": np.inf,
                          "e": np.array([0.25, 0.5], dtype=np.float32),
                          "f": (np.int64(3), [np.float64(1.5), None, "x"]),
                          7: np.array([True, False])})
        self.assertIs(type(got["a"]), float)
        self.assertEqual(got["a"], float(np.float32(0.3)))
        self.assertIs(got["b"], True)
        self.assertIsNone(got["c"])
        self.assertIsNone(got["d"])
        self.assertEqual(got["e"], [0.25, 0.5])
        self.assertTrue(all(type(v) is float for v in got["e"]))
        self.assertEqual(got["f"], [3, [1.5, None, "x"]])
        self.assertIs(type(got["f"][0]), int)
        self.assertEqual(got["7"], [True, False])
        self.assertTrue(all(type(v) is bool for v in got["7"]))
        json.dumps(got, allow_nan=False)
        with self.assertRaises(TypeError):
            T.jsonable(object())

    def test_episode_indexing(self):
        ep = T.episode("d2", 1)
        self.assertEqual(ep["seed"], 1000)
        self.assertEqual(ep["weights"], EPISODES_D2[0][1])
        self.assertEqual(ep["road"], (141.05, 0.13314))
        self.assertEqual((ep["protocol"], ep["idx"]), ("d2", 1))
        self.assertEqual(T.episode("d2", 20)["seed"], EPISODES_D2[19][0])
        pd = T.episode("phase-d", 1)
        self.assertIsNone(pd["road"])
        self.assertEqual((pd["seed"], pd["weights"]), EPISODES[0])
        for protocol, idx in (("d2", 0), ("d2", 21), ("d2", "1"), ("d2", True),
                              ("x", 1)):
            with self.subTest(protocol=protocol, idx=idx):
                with self.assertRaises(KeyError):
                    T.episode(protocol, idx)

    def test_route_geometry(self):
        cycle = T.build_cycle(T.episode("d2", 1))
        before = {k: np.asarray(v).tobytes() for k, v in cycle.items()}
        r = T.route(cycle)
        for k, v in cycle.items():
            self.assertEqual(np.asarray(v).tobytes(), before[k], f"route() changed cycle[{k!r}]")
        for key in ("s_m", "x_m", "z_m", "grade_pct", "speed_kmh"):
            self.assertEqual(len(r[key]), T.STEPS + 1, key)
        self.assertAlmostEqual(r["length_m"], 25603, delta=1)
        self.assertAlmostEqual(r["rise_m"], 2755, delta=1)
        self.assertEqual(r["climb_start_s"], 141.0)
        v, g = cycle["v_mps"], cycle["grade"]
        for k in range(T.STEPS):
            theta = np.arctan(g[k])
            self.assertAlmostEqual(r["x_m"][k + 1] - r["x_m"][k], v[k] * T.DT * np.cos(theta), delta=1e-9)
            self.assertAlmostEqual(r["z_m"][k + 1] - r["z_m"][k], v[k] * T.DT * np.sin(theta), delta=1e-9)
        json.dumps(r, allow_nan=False)
        self.assertAlmostEqual(T.route(T.build_cycle(T.episode("d2", 5)))["rise_m"], 1917, delta=1)
        self.assertAlmostEqual(T.route(T.build_cycle(T.episode("d2", 6)))["rise_m"], 3247, delta=1)
        self.assertEqual(T.route(T.build_cycle(T.episode("phase-d", 1)))["climb_start_s"], 180.0)

    def test_applied_not_commanded(self):
        frames = []
        with mock.patch.object(T, "build_cycle", _short_cycle):
            T.run_lanes([(_neutral, True)], T.episode("d2", 1),
                        on_frame=lambda frame, seen: frames.append(frame))
        car = frames[0]["cars"][0]
        self.assertEqual(car["cmd"], [float(v) for v in neutral_action()])
        self.assertEqual(car["act"], [0.0, 0.0, 0.0, 0.25, float(np.float32(0.3))])
        self.assertEqual(car["held"], [False, False, False, True, True])

    def test_preview_slice_is_the_observation(self):
        ep = T.episode("d2", 1)
        self.assertEqual(T.STEPS, len(T.build_cycle(ep)["v_mps"]) - 1)
        envs, obs = {}, {}
        for sighted in (True, False):
            env = SupervisoryTunerEnv(T.build_cycle(ep), dt=T.DT, seed=ep["seed"],
                                      use_preview=sighted)
            env.reset(seed=ep["seed"])
            env.w = np.asarray(ep["weights"], dtype=np.float32)
            envs[sighted], obs[sighted] = env, env._obs()
        grade = envs[True].cycle["grade"]
        for k in range(151):
            if k in (0, 125, 150):
                s, b = obs[True], obs[False]
                want = (12 * np.asarray(envs[True]._preview())).astype(np.float32)
                self.assertEqual(s[T.PREVIEW].tolist(), want.tolist(), f"k={k}")
                self.assertEqual(s[13], np.float32(12 * grade[k]), f"k={k}")
                self.assertEqual(b[13], s[13], f"k={k}: the blind car sees the grade it is on")
                self.assertEqual(b[T.PREVIEW].tolist(), [0.0] * len(T.PREVIEW_S), f"k={k}")
            if k == 125:
                # The climb starts at 141 s: 16 s away, so only the 30 s horizon sees it.
                self.assertEqual((s[13], s[16]), (0.0, 0.0))
                self.assertGreater(s[17], 0.0)
            for sighted, env in envs.items():
                obs[sighted] = env.step(neutral_action())[0]

    def test_lane_stops_on_divergence(self):
        frames = []
        with mock.patch.object(T, "build_cycle", _short_cycle):
            got = T.run_lanes([(_neutral, True), (_nan_policy, False)], T.episode("d2", 1),
                              on_frame=lambda frame, seen: frames.append((frame, seen)))
        self.assertEqual([f["k"] for f, _ in frames], list(range(29)))
        self.assertIsNotNone(frames[0][0]["cars"][1])
        self.assertEqual(frames[0][0]["cars"][1]["act"], [None] * 5)
        for frame, seen in frames[1:]:
            self.assertIsNone(frame["cars"][1])
            self.assertIsNone(seen[1])
            self.assertEqual((seen[0].shape, seen[0].dtype), ((23,), np.float32))
        for frame, _ in frames:
            json.dumps(frame, allow_nan=False)
        self.assertEqual(len(got), 2)
        for result in got:
            self.assertEqual(set(result), RESULT_KEYS)


RESULT_KEYS = {"ret", "damage", "fuel", "torque_viol", "peak_turb", "knock"}


def _short_cycle(ep):
    """A 30 s climb: 29 steps, about a second of plant."""
    return make_grade_climb(duration=30.0, dt=1.0)


def _neutral(env, obs):
    return neutral_action()


def _nan_policy(env, obs):
    return np.full(5, np.nan, dtype=np.float32)


class ProofTests(unittest.TestCase):
    """Spec tests 1 and 2: the tracer IS evaluate.run_episode, on a real C4 pair.

    `==` on whole result dicts, no tolerance. If it ever fails, find the cause;
    the fallback is sequential lanes, never an epsilon.
    """

    @classmethod
    def setUpClass(cls):
        paths = [str(ROOT / "runs_c4" / f"{arm}_seed0") + "/final" for arm in ("sighted", "blind")]
        try:
            from stable_baselines3 import SAC
        except ImportError:
            SAC = None
        if SAC is None or not all(Path(p + ".zip").is_file() for p in paths):
            print("\n  agent path UNPROVEN on this machine (no runs_c4/*_seed0/final.zip "
                  "or no stable-baselines3)")
            raise unittest.SkipTest("agent path UNPROVEN on this machine")
        m_s, m_b = SAC.load(paths[0]), SAC.load(paths[1])     # no device: evaluate.py:370
        cls.device = str(m_s.device)
        cls.ep = T.episode("d2", 1)
        seed, weights, start_s, grade = EPISODES_D2[0]
        cls.frames = []
        cls.got = T.run_lanes([(agent_policy(m_s), True), (agent_policy(m_b), False)], cls.ep,
                              on_frame=lambda frame, seen: cls.frames.append(frame))
        cls.want = [run_episode(agent_policy(m_s), seed, weights, True, road=(start_s, grade)),
                    run_episode(agent_policy(m_b), seed, weights, False, road=(start_s, grade))]

    def test_tracer_equals_run_episode(self):
        print(f"\n  == proof on {self.device}: sighted damage {self.got[0]['damage']!r}, "
              f"blind damage {self.got[1]['damage']!r}")
        self.assertEqual(self.got, self.want)

    def test_frames_are_the_episode(self):
        frames, road = self.frames, T.route(T.build_cycle(self.ep))
        self.assertEqual(len(frames), T.STEPS)
        self.assertEqual([f["k"] for f in frames], list(range(T.STEPS)))
        rescale = SupervisoryTunerEnv(T.build_cycle(self.ep), dt=T.DT)._rescale
        any_held = False
        for lane, result in enumerate(self.got):
            cars = [f["cars"][lane] for f in frames]
            self.assertEqual(cars[-1]["damage"], result["damage"])
            self.assertEqual(max(c["turb_c"] for c in cars), result["peak_turb"])
            prev = np.zeros(5, dtype=np.float32)
            for k, car in enumerate(cars):
                for key in ("act", "cmd", "preview_pct"):
                    self.assertNotIn(None, car[key], f"lane {lane} k {k} {key}")
                self.assertIsNotNone(car["map_kpa"])
                raw = rescale(np.asarray(car["cmd"], dtype=np.float32))
                want = np.clip(np.clip(raw, prev - SLEW * T.DT, prev + SLEW * T.DT), ACT_LO, ACT_HI)
                act = np.asarray(car["act"], dtype=np.float32)
                self.assertEqual(act.tolist(), want.tolist(), f"lane {lane} k {k}")
                self.assertEqual(car["held"], (act != raw).tolist(), f"lane {lane} k {k}")
                any_held = any_held or any(car["held"])
                prev = act
                for j, h in enumerate(T.PREVIEW_S):
                    if lane == 0:
                        g = road["grade_pct"][min(k + int(h / T.DT), T.STEPS)] / 100.0
                        self.assertAlmostEqual(car["preview_pct"][j] / 100.0, g, delta=1e-6)
                    else:
                        self.assertEqual(car["preview_pct"][j], 0.0)
        self.assertTrue(any_held, "the rate limit never held a command back: suspicious")
        for f in frames:
            json.dumps(f, allow_nan=False)


def _fake_agent(root, runs, name, src_arm, drop=(), **meta_changes):
    """A copy of runs_c4/<src_arm>_seed0 at root/runs/name, built with
    shutil.copy and json.dump only. `drop` names files to leave out."""
    src = ROOT / "runs_c4" / f"{src_arm}_seed0"
    d = Path(root) / runs / name
    d.mkdir(parents=True)
    if "final.zip" not in drop:
        shutil.copy(src / "final.zip", d / "final.zip")
    if "meta.json" not in drop:
        meta = json.loads((src / "meta.json").read_text(encoding="utf-8"))
        meta.update(meta_changes)
        with open(d / "meta.json", "w", encoding="utf-8") as fh:
            json.dump(meta, fh)
    return d


def _fake_pair(root, runs, **meta_changes):
    for arm in AC.ARMS:
        _fake_agent(root, runs, f"{arm}_seed0", arm, **meta_changes)


def _result_line(path_text, sha):
    return (f"model {path_text}: trained 300000 steps of 300000 requested, "
            f"from step 0, buffer 300000, zip sha {sha}\n")


class CatalogTests(unittest.TestCase):
    """Task 3: which agents may run, and what results/ says about them."""

    def test_protocol_of(self):
        self.assertEqual(AC.protocol_of({}), "phase-d")
        self.assertEqual(AC.protocol_of({"scenario": {"grade": 0.12}}), "phase-d")
        self.assertEqual(AC.protocol_of({"scenario": {"protocol": "random-climb"}}), "d2")
        self.assertIsNone(AC.protocol_of({"scenario": {"protocol": "something-else"}}))

    def test_names_never_become_paths(self):
        for runs, seed in (("..", 0), ("runs_c4/../runs", 0), ("runs_c4\\..\\runs", 0),
                           ("runs_c4\n", 0), ("C:/runs_c4", 0), ("runs_zz", 0),
                           ("runs_C4", 0), ("runs_c4", 99), ("runs_c4", -1),
                           ("runs_c4", "0"), ("runs_c4", True)):
            with self.subTest(runs=runs, seed=seed):
                with self.assertRaises(KeyError):
                    AC.find_pair(runs, seed)
        for name in ("ckpt_1", "_logs", "sighted_seed", "Sighted_seed0",
                     "sighted_seed0/../x", "blind_seed0\n"):
            with self.subTest(name=name):
                with self.assertRaises(KeyError):
                    AC.read_agent("runs_c4", name)

    @unittest.skipUnless(HAVE_C4, NO_C4)
    def test_c4_pairs_are_the_scored_artefacts(self):
        saved = os.environ.pop("GIT_OPTIONAL_LOCKS", None)
        try:
            pairs = [AC.find_pair("runs_c4", k) for k in C4_SEEDS]
            self.assertEqual(os.environ.get("GIT_OPTIONAL_LOCKS"), "0",
                             "live_fingerprint must set it before git status runs")
        finally:
            os.environ["GIT_OPTIONAL_LOCKS"] = saved if saved is not None else "0"
        for k, pair in zip(C4_SEEDS, pairs):
            with self.subTest(seed=k):
                self.assertEqual((pair["prefix"], pair["experiment"], pair["protocol"]),
                                 ("c4", "C4", "d2"))
                self.assertTrue(pair["result_file"])
                self.assertEqual([a["tag"] for a in pair["agents"]],
                                 [f"sighted_seed{k}", f"blind_seed{k}"])
                shas = AC.scored_shas("c4", k)
                for a in pair["agents"]:
                    self.assertEqual(a["status"], "ready", a["reason"])
                    self.assertEqual(a["scored"], "match")
                    self.assertEqual(a["zip_sha"], shas[a["arm"]])
                    self.assertEqual(a["budget"]["num_timesteps"], 300000)
                    self.assertEqual(a["train_dt"], 0.2)
                    self.assertIn("zip sha " + a["zip_sha"], a["budget_line"])

    def test_scored_shas_real_files(self):
        self.assertIsNone(AC.scored_shas("zz", 0))
        if (ROOT / "results" / "d2_seed0.txt").is_file():
            self.assertEqual(AC.scored_shas("d2", 0), {"sighted": None, "blind": None})
        got = AC.scored_shas("c4", 0)
        self.assertEqual(got, {"sighted": "20f0ae6a9c1564a9", "blind": "9ab8d2b29cbb9d06"},
                         "results/c4_seed0.txt:24,26 record these, with backslash paths")

    @unittest.skipUnless(HAVE_C4, NO_C4)
    def test_catalog_synthetic(self):
        threads = threading.active_count()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertNotIn(str(ROOT.resolve()).lower(), str(root.resolve()).lower())
            real = {arm: FP.model_budget(str(ROOT / "runs_c4" / f"{arm}_seed0" / "final.zip"))["sha"]
                    for arm in AC.ARMS}

            # a clean copy: runnable, no result file, no name recorded
            _fake_pair(root, "runs_zz")
            pair = AC.find_pair("runs_zz", 0, root)
            self.assertEqual((pair["prefix"], pair["experiment"], pair["result_file"]),
                             ("zz", "runs_zz (no name recorded)", False))
            self.assertEqual([a["scored"] for a in pair["agents"]], ["not recorded"] * 2)
            self.assertEqual(AC.verdict("zz", root)["state"], "none")
            self.assertEqual(AC.verdict("zz", root)["short"], AC.NONE_TEXT)

            # ckpt_*.zip, checkpoint.zip and _logs/ are ignored: only final.zip counts
            (root / "runs_zz" / "_logs").mkdir()
            shutil.copy(root / "runs_zz" / "sighted_seed0" / "final.zip",
                        root / "runs_zz" / "sighted_seed0" / "ckpt_1000_steps.zip")
            self.assertEqual(AC.find_pair("runs_zz", 0, root)["agents"][0]["status"], "ready")
            with self.assertRaises(KeyError):
                AC.read_agent("runs_zz", "_logs", root)

            # a recorded sha: backslash paths (as evaluate wrote them) and forward slashes
            (root / "results").mkdir()
            res = root / "results" / "zz_seed0.txt"
            with open(res, "w", encoding="utf-8") as fh:
                fh.write(_result_line("runs_zz\\sighted_seed0", real["sighted"]))
                fh.write(_result_line("runs_zz/blind_seed0", real["blind"]))
            pair = AC.find_pair("runs_zz", 0, root)
            self.assertTrue(pair["result_file"])
            self.assertEqual([a["scored"] for a in pair["agents"]], ["match", "match"])
            for sep in ("\\", "/"):
                with self.subTest(separator=sep):
                    with open(res, "w", encoding="utf-8") as fh:
                        fh.write(_result_line(f"runs_zz{sep}sighted_seed0", "0123456789abcdef"))
                    with self.assertRaises(AC.Refused) as cm:
                        AC.find_pair("runs_zz", 0, root)
                    text = " ".join(cm.exception.problems)
                    self.assertIn("not the scored artefact", text)
                    self.assertIn("0123456789abcdef", text)
                    self.assertIn(real["sighted"], text)

            # a plant that moved: incompatible, refused, never SystemExit
            _fake_pair(root, "runs_zzplant")
            meta_path = root / "runs_zzplant" / "sighted_seed0" / "meta.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["plant_sha"] = "0000000000000000"
            with open(meta_path, "w", encoding="utf-8") as fh:
                json.dump(meta, fh)
            a = AC.read_agent("runs_zzplant", "sighted_seed0", root)
            self.assertEqual(a["status"], "incompatible")
            self.assertTrue(any(p.startswith("plant_sha: stored '0000000000000000' live")
                                for p in a["problems"]), a["problems"])
            with self.assertRaises(AC.Refused) as cm:
                AC.find_pair("runs_zzplant", 0, root)
            self.assertIn("plant_sha", " ".join(cm.exception.problems))

            # no meta.json
            _fake_agent(root, "runs_zzmeta", "sighted_seed0", "sighted", drop=("meta.json",))
            a = AC.read_agent("runs_zzmeta", "sighted_seed0", root)
            self.assertEqual((a["status"], a["reason"]),
                             ("incompatible", "no meta.json: plant unknown (AUDIT2 C2-1)"))

            # training now: RUNNING carries this test's own pid
            d = _fake_agent(root, "runs_zztrain", "sighted_seed0", "sighted")
            FP.claim_running(str(d))
            try:
                self.assertEqual(AC.read_agent("runs_zztrain", "sighted_seed0", root)["status"],
                                 "training")
            finally:
                FP.release_running(str(d))
            self.assertEqual(AC.read_agent("runs_zztrain", "sighted_seed0", root)["status"], "ready")

            # no final.zip, even with checkpoints beside it
            d = _fake_agent(root, "runs_zzzip", "blind_seed0", "blind", drop=("final.zip",))
            shutil.copy(ROOT / "runs_c4" / "blind_seed0" / "final.zip", d / "checkpoint.zip")
            shutil.copy(ROOT / "runs_c4" / "blind_seed0" / "final.zip", d / "ckpt_300000_steps.zip")
            self.assertEqual(AC.read_agent("runs_zzzip", "blind_seed0", root)["status"], "incomplete")

            # meta says sighted inside a blind_ directory
            _fake_agent(root, "runs_zzarm", "blind_seed0", "blind", use_preview=True)
            a = AC.read_agent("runs_zzarm", "blind_seed0", root)
            self.assertEqual((a["status"], a["reason"]), (
                "incompatible", "evaluate.py would have scored this agent as the other arm"))

            # evaluate.py:369 decides the arm by "blind" in the PATH it was given
            _fake_pair(root, "runs_zz_blind")
            a = AC.read_agent("runs_zz_blind", "sighted_seed0", root)
            self.assertEqual((a["status"], a["reason"]), (
                "incompatible", "evaluate.py would have scored this agent as the other arm"))
            with self.assertRaises(AC.Refused):
                AC.find_pair("runs_zz_blind", 0, root)
        self.assertEqual(threading.active_count(), threads, "the catalog started a thread")

    def test_c4_verdict(self):
        v = AC.verdict("c4")
        self.assertEqual(v["state"], "found", v["missing"])
        self.assertEqual(v["missing"], [])
        by_key = {ln["key"]: ln for ln in v["lines"]}
        self.assertEqual({k: ln["line"] for k, ln in by_key.items()},
                         {"result": 42, "seeds": 29, "disagree": 33, "convergence": 48,
                          "reading": 50, "explanations": 41, "one_seed": 633})
        for a in AC.VERDICT_LINES["c4"]:
            with self.subTest(anchor=a.key):
                src = (ROOT / "results" / a.file).read_text(encoding="utf-8").splitlines()
                ln = by_key[a.key]
                self.assertEqual(ln["file"], a.file)
                self.assertEqual(ln["text"], "\n".join(src[ln["line"] - 1:ln["line"] - 1 + a.n]))
        self.assertIn("(7 of 8 seeds below 50)", by_key["seeds"]["text"])
        self.assertIn("one\n   seed the other way and the cell would be INCONCLUSIVE",
                      by_key["one_seed"]["text"])
        self.assertEqual(v["short"], {k: AC.SHORT_VERDICT["c4"][k] for k in ("ar", "en")})
        self.assertLessEqual(set(AC.SHORT_VERDICT["c4"]["requires"]),
                             {a.key for a in AC.VERDICT_LINES["c4"]})
        self.assertEqual([c["cell"] for c in v["cells"]], ["SMALLER THAN THE MEI", "NOT-CONVERGED"])
        for c in v["cells"]:
            self.assertEqual(c["gloss"], AC.GLOSS[c["cell"]])
        gloss = AC.GLOSS["SMALLER THAN THE MEI"]
        for lang, one_seed in (("ar", "بذرة واحدة"), ("en", "one seed")):
            for needle in ("50", "300 000", one_seed):
                self.assertIn(needle, gloss[lang])
        self.assertIn("بذرة واحدة", AC.SHORT_VERDICT["c4"]["ar"])
        self.assertIn("one seed", AC.SHORT_VERDICT["c4"]["en"])

        # the same files copied out are found; one anchor removed turns the box to 'missing'
        with tempfile.TemporaryDirectory() as tmp:
            res = Path(tmp) / "results"
            res.mkdir()
            for f in ("C4_RESULT.txt", "PREREGISTRATION_C4.md"):
                shutil.copy(ROOT / "results" / f, res / f)
            self.assertEqual(AC.verdict("c4", tmp)["state"], "found")
            lines = (res / "C4_RESULT.txt").read_text(encoding="utf-8").splitlines()
            self.assertTrue(lines[47].lstrip().startswith("NOT-CONVERGED"))
            del lines[47]
            with open(res / "C4_RESULT.txt", "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + "\n")
            v = AC.verdict("c4", tmp)
        self.assertEqual(v["state"], "missing")
        self.assertEqual(v["missing"], ["C4_RESULT.txt"])
        self.assertEqual(v["short"], {lang: AC.MISSING_TEXT[lang].format(file="C4_RESULT.txt")
                                      for lang in ("ar", "en")})
        self.assertEqual([c["cell"] for c in v["cells"]], ["SMALLER THAN THE MEI"])
        self.assertEqual(AC.verdict("zz")["state"], "none")

    def test_live_fingerprint_is_cached(self):
        a = AC.live_fingerprint("d2")
        self.assertIs(AC.live_fingerprint("d2"), a)
        self.assertRegex(AC.FINGERPRINT_TAKEN["d2"], r"^\d\d:\d\d$")
        self.assertEqual(a["scenario"]["protocol"], "random-climb")


class LoaderTests(unittest.TestCase):
    """Spec test 1b: load_pair is evaluate.py:370's call, and loads the scored zip.

    The == proof injects its own model objects, so without this test a loader
    that picked a different file or a different device would pass unnoticed.
    """

    def test_loader_matches_evaluate(self):
        import os
        import fingerprint as FP
        from app import agent_api as A
        from app import agent_catalog as C
        try:
            import stable_baselines3
            import torch
            from stable_baselines3 import SAC
        except ImportError:
            print("\n  loader UNPROVEN on this machine (no stable-baselines3)")
            self.skipTest("loader UNPROVEN on this machine")
        if not all((ROOT / "runs_c4" / f"{arm}_seed0" / "final.zip").is_file() for arm in C.ARMS):
            print("\n  loader UNPROVEN on this machine (no runs_c4/*_seed0/final.zip)")
            self.skipTest("loader UNPROVEN on this machine")
        recorded = {"sighted": "20f0ae6a9c1564a9", "blind": "9ab8d2b29cbb9d06"}
        prev = os.getcwd()
        os.chdir(ROOT)                      # evaluate.py's paths are relative to the repo
        try:
            got = A.load_pair("runs_c4", 0)
            for arm, model, path in zip(C.ARMS, got, A.pair_paths("runs_c4", 0)):
                with self.subTest(arm=arm):
                    ref = SAC.load(f"runs_c4/{arm}_seed0".rstrip("/\\") + "/final")
                    self.assertEqual(str(model.device), str(ref.device))
                    mine, theirs = model.policy.state_dict(), ref.policy.state_dict()
                    self.assertEqual(list(mine), list(theirs))
                    for name in mine:
                        self.assertTrue(torch.equal(mine[name], theirs[name]), name)
                    sha = FP.model_budget(path + ".zip")["sha"]
                    self.assertEqual(sha, FP.model_budget(f"runs_c4/{arm}_seed0/final.zip")["sha"])
                    self.assertEqual(sha, C.scored_shas("c4", 0)[arm])
                    self.assertEqual(sha, recorded[arm])
        finally:
            os.chdir(prev)
        self.assertEqual(A.versions(), {"torch": torch.__version__,
                                        "sb3": stable_baselines3.__version__})
        print(f"\n  load_pair: device {got[0].device}, torch {torch.__version__}, "
              f"SB3 {stable_baselines3.__version__}")

    def test_as_policy_and_versions(self):
        import os
        import subprocess
        import check_premise
        from app import agent_api as A
        self.assertIs(A.as_policy(check_premise.p_neutral), check_premise.p_neutral)

        class FakeModel:
            def predict(self, obs, deterministic=False):
                self.asked = (obs, deterministic)
                return np.full(5, 0.5, dtype=np.float32), None

        fake, obs = FakeModel(), np.zeros(23, dtype=np.float32)
        self.assertEqual(A.as_policy(fake)(None, obs).tolist(), [0.5] * 5)
        self.assertIs(fake.asked[0], obs)
        self.assertIs(fake.asked[1], True)
        self.assertEqual(A.pair_paths("runs_c4", 5),
                         (str(ROOT / "runs_c4" / "sighted_seed5") + "/final",
                          str(ROOT / "runs_c4" / "blind_seed5") + "/final"))
        for runs, seed in (("..", 0), ("runs_c4/../runs", 0), ("runs_c4\n", 0),
                           ("c4", 0), ("runs_c4", -1), ("runs_c4", "0"), ("runs_c4", True)):
            with self.subTest(runs=runs, seed=seed):
                with self.assertRaises(KeyError):
                    A.pair_paths(runs, seed)
        code = ("import json, sys\n"
                "import app.agent_api as A\n"
                "print(json.dumps({'torch': 'torch' in sys.modules,"
                " 'sb3': 'stable_baselines3' in sys.modules, 'versions': A.versions()}))\n")
        out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True,
                             text=True, timeout=300,
                             env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                                      GIT_OPTIONAL_LOCKS="0"))
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout.strip().splitlines()[-1]),
                         {"torch": False, "sb3": False,
                          "versions": {"torch": None, "sb3": None}})


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]] + [a for a in sys.argv[1:] if a != "--full"], verbosity=2)

"""The agent replay page's own suite. Nothing here writes, trains or evaluates.

    python -m app.test_agents          the default suite
    python -m app.test_agents --full   adds the slow checks

Run from the repository root. app/test_replay.py's test_read_only scans this
file too, so banned tokens are written as raw regexes, never as calls, and
fixtures are made in temporary directories OUTSIDE the repository.
"""
import ast
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

import numpy as np

import fingerprint as FP
from app import agent_api as API
from app import agent_catalog as AC
from app import agent_trace as T
from check_premise import p_grade_now, p_neutral
from engine_env import (ACT_HI, ACT_LO, OBS_DIM, PREVIEW_S, SLEW, TURB_PROTECT_K,
                        SupervisoryTunerEnv, make_grade_climb, neutral_action)
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


_SB3_HERE = importlib.util.find_spec("stable_baselines3") is not None
_C4_PAIR0_HERE = _SB3_HERE and all(
    (ROOT / "runs_c4" / f"{arm}_seed0" / "final.zip").is_file() for arm in ("sighted", "blind"))
_RUNS_PAIR0_HERE = _SB3_HERE and all(
    (ROOT / "runs" / f"{arm}_seed0" / "final.zip").is_file() for arm in ("sighted", "blind"))
UNPROVEN_LINE = "agent path UNPROVEN on this machine"


def _d2_episode_for(runs, seed, idx):
    return T.episode("d2", idx)


def _no_models(runs, seed):
    return (p_neutral, p_grade_now)


def _fake_tracer(n=5, gate=None, fail=None, obs=False):
    """A stand-in for run_lanes: n paired frames, each held at `gate` if one
    is given; `fail` is raised in place of frame 2."""
    def tracer(lanes, ep, on_frame):
        assert [use for _, use in lanes] == [True, False], "lane 0 sighted, lane 1 blind"
        for k in range(n):
            if gate is not None:
                gate.wait(5)
            if fail is not None and k == 2:
                raise fail
            seen = [np.full(OBS_DIM, k, np.float32), None] if obs else [None, None]
            on_frame({"k": k, "cars": [None, None]}, seen)
            time.sleep(0.01)
        return [{"damage": 1.0}, {"damage": 2.0}]
    return tracer


def _wait_for(store, key, want, limit=10.0):
    t0 = time.monotonic()
    while True:
        r = store.poll(key)
        if r["status"] == want:
            return r
        if time.monotonic() - t0 > limit:
            raise AssertionError(f"{key} never reached {want!r}; last {r['status']!r}")
        time.sleep(0.02)


def _builders():
    return [t for t in threading.enumerate() if t.name == "agent-builder"]


class StoreTests(unittest.TestCase):
    """Spec test 9: one worker, streaming, cancellable only by preempt, keep = 2."""

    K1, K2, K3 = ("runs_c4", 5, 1), ("runs_c4", 5, 2), ("runs_c4", 5, 3)

    def store(self, **kw):
        kw.setdefault("loader", _no_models)
        kw.setdefault("tracer", _fake_tracer())
        kw.setdefault("episode_for", _d2_episode_for)
        return API.EpisodeStore(**kw)

    def tearDown(self):
        for t in _builders():
            t.join(5)

    def test_key_and_defaults(self):
        self.assertEqual(API.key_str(self.K1), "runs_c4/5/1")
        self.assertTrue(API.EpisodeStore().needs_sb3)
        self.assertFalse(self.store().needs_sb3)
        self.assertEqual(API.BUILD_FAILED.format(kind="SystemExit"), "build failed: SystemExit")

    def test_loading_then_streaming_then_ready(self):
        s = self.store(tracer=_fake_tracer(obs=True))
        r = s.poll(self.K1, preempt=True)
        self.assertEqual({k: r[k] for k in ("status", "progress", "steps", "since", "frames")},
                         {"status": "loading", "progress": 0.0, "steps": T.STEPS, "since": 0,
                          "frames": []})
        r = _wait_for(s, self.K1, "ready")
        self.assertEqual([f["k"] for f in r["frames"]], [0, 1, 2, 3, 4])
        self.assertEqual(r["progress"], 1.0)
        self.assertEqual(r["device"], "n/a")
        self.assertEqual(set(r["versions"]), {"torch", "sb3"})
        later = s.poll(self.K1, since=3)
        self.assertEqual((later["since"], [f["k"] for f in later["frames"]]), (3, [3, 4]))
        tr = s.trace(self.K1)
        self.assertEqual(tr.key, self.K1)
        self.assertEqual(tr.results, [{"damage": 1.0}, {"damage": 2.0}])
        self.assertEqual(tr.obs[0].shape, (5, OBS_DIM))
        self.assertEqual(tr.obs[0].dtype, np.float32)
        self.assertEqual(tr.obs[1].shape, (0, OBS_DIM))
        self.assertEqual(float(tr.obs[0][3][0]), 3.0)
        for t in _builders():
            t.join(5)
        self.assertEqual(_builders(), [], "the agent-builder thread did not end")

    def test_loading_is_answered_while_the_loader_is_slow(self):
        def slow(runs, seed):
            time.sleep(1.0)
            return _no_models(runs, seed)
        s = self.store(loader=slow)
        s.poll(self.K1, preempt=True)
        worst, seen = 0.0, []
        for _ in range(15):
            t0 = time.perf_counter()
            r = s.poll(self.K1)
            worst = max(worst, time.perf_counter() - t0)
            seen.append(r["status"])
            time.sleep(0.05)
        self.assertLess(worst, 0.1, "poll blocked on the worker's lock")
        self.assertEqual(set(seen), {"loading"})
        r = _wait_for(s, self.K1, "building")
        self.assertEqual(r["frames"][0]["k"], 0, "the first slice must start at frame 0")

    def test_one_worker_and_polls_never_cancel(self):
        gate = threading.Event()
        s = self.store(tracer=_fake_tracer(gate=gate))
        self.assertEqual(s.poll(self.K1)["status"], "loading")
        for _ in range(3):
            r = s.poll(self.K2)
            self.assertEqual(r["status"], "busy")
            self.assertEqual(r["active"], {"runs": "runs_c4", "seed": 5, "ep": 1})
            self.assertEqual(r["frames"], [])
        self.assertEqual(len(_builders()), 1)
        gate.set()
        _wait_for(s, self.K1, "ready")
        self.assertIsNotNone(s.trace(self.K1), "a plain poll cancelled the build")

    def test_preempt_cancels_and_keeps_nothing_partial(self):
        gate = threading.Event()
        s = self.store(tracer=_fake_tracer(gate=gate))
        s.poll(self.K1)
        self.assertEqual(s.poll(self.K1, preempt=True)["status"], "loading",
                         "preempt on the key already building must not cancel it")
        self.assertEqual(s.poll(self.K2, preempt=True)["status"], "busy")
        gate.set()
        r = _wait_for(s, self.K2, "ready")
        self.assertEqual(len(r["frames"]), 5)
        self.assertIsNone(s.trace(self.K1), "a cancelled trace was kept")

    def test_keep_two_least_recently_used(self):
        s = self.store()
        for key in (self.K1, self.K2):
            s.poll(key)
            _wait_for(s, key, "ready")
        s.poll(self.K1)                      # touch K1: K2 is now the oldest
        s.poll(self.K3)
        _wait_for(s, self.K3, "ready")
        self.assertIsNotNone(s.trace(self.K1))
        self.assertIsNone(s.trace(self.K2))
        self.assertIsNotNone(s.trace(self.K3))

    def test_error_is_reported_once_with_a_fixed_message(self):
        calls = []

        def once(lanes, ep, on_frame):
            calls.append(1)
            if len(calls) == 1:
                raise ValueError(r"C:\secret\path must not reach the browser")
            return _fake_tracer()(lanes, ep, on_frame)
        s = self.store(tracer=once)
        s.poll(self.K1)
        r = _wait_for(s, self.K1, "error")
        self.assertEqual(r["message"], "build failed: ValueError")
        self.assertEqual(r["frames"], [])
        self.assertEqual(s.poll(self.K1)["status"], "loading", "the error was not forgotten")
        _wait_for(s, self.K1, "ready")

    def test_system_exit_anywhere_becomes_an_error(self):
        def refuses(runs, seed):
            raise SystemExit("check_model_fingerprint refuses")

        def bad_episode(runs, seed, idx):
            raise AC.Refused(["blind_seed5: incompatible"])
        for kw, kind in (({"tracer": _fake_tracer(fail=SystemExit(2))}, "SystemExit"),
                         ({"loader": refuses}, "SystemExit"),
                         ({"episode_for": bad_episode}, "Refused")):
            with self.subTest(kind=kind, hook=sorted(kw)):
                s = self.store(**kw)
                s.poll(self.K1)
                r = _wait_for(s, self.K1, "error")
                self.assertEqual(r["message"], f"build failed: {kind}")
                self.assertIsNone(s.trace(self.K1))


def _build_through_store(store, key, limit=900.0):
    """Poll the way the page does -- preempt once, then plain polls -- until ready."""
    r = store.poll(key, preempt=True)
    t0 = time.monotonic()
    while r["status"] != "ready":
        if r["status"] == "error":
            raise AssertionError(r["message"])
        if time.monotonic() - t0 > limit:
            raise AssertionError(f"{key} not ready after {limit} s")
        time.sleep(0.2)
        r = store.poll(key)
    return store.trace(key)


class ProofTests(unittest.TestCase):
    """Spec tests 1 and 2: the page's numbers are evaluate.run_episode's, computed
    on the store's own agent-builder thread. Equality, never a tolerance."""

    @classmethod
    def setUpClass(cls):
        seed, weights, start_s, grade = EPISODES_D2[0]
        cls.key = ("runs_c4", 0, 1)
        cls.threads = []

        def tracer(lanes, ep, on_frame=None):
            cls.threads.append(threading.current_thread().name)
            return T.run_lanes(lanes, ep, on_frame)
        if _C4_PAIR0_HERE:
            from stable_baselines3 import SAC
            m_s = SAC.load(str(ROOT / "runs_c4" / "sighted_seed0") + "/final")
            m_b = SAC.load(str(ROOT / "runs_c4" / "blind_seed0") + "/final")
            policies = (agent_policy(m_s), agent_policy(m_b))
            store = API.EpisodeStore(loader=lambda runs, s: (m_s, m_b), tracer=tracer)
        else:
            print(f"\n    {UNPROVEN_LINE}: no runs_c4/ or no stable-baselines3 -- "
                  f"p_neutral / p_grade_now run through the store instead", file=sys.stderr)
            policies = (p_neutral, p_grade_now)
            store = API.EpisodeStore(loader=_no_models, tracer=tracer,
                                     episode_for=_d2_episode_for)
        t0 = time.perf_counter()
        cls.trace = _build_through_store(store, cls.key)
        cls.build_s = time.perf_counter() - t0
        cls.want = [run_episode(policies[0], seed, weights, True, road=(start_s, grade)),
                    run_episode(policies[1], seed, weights, False, road=(start_s, grade))]
        cls.road = T.route(T.build_cycle(T.episode("d2", 1)))

    def test_tracer_equals_run_episode(self):
        self.assertEqual(self.threads, ["agent-builder"])
        self.assertEqual(self.trace.results, self.want)
        label = "PROVEN" if _C4_PAIR0_HERE else UNPROVEN_LINE
        print(f"\n    == proof {label}: device {self.trace.device}, "
              f"torch {self.trace.versions['torch']}, sb3 {self.trace.versions['sb3']}, "
              f"sighted damage {self.want[0]['damage']!r}, blind {self.want[1]['damage']!r}, "
              f"built in {self.build_s:.0f} s", file=sys.stderr)

    def test_frames_are_the_episode(self):
        frames = self.trace.frames
        self.assertEqual(len(frames), T.STEPS)
        self.assertEqual([f["k"] for f in frames], list(range(T.STEPS)))
        grade = self.road["grade_pct"]
        prev = [np.zeros(5, np.float32), np.zeros(5, np.float32)]
        any_held = [False, False]
        for f in frames:
            json.dumps(f, allow_nan=False)
            for lane in (0, 1):
                car = f["cars"][lane]
                for field in ("act", "cmd", "preview_pct"):
                    self.assertNotIn(None, car[field], f"frame {f['k']} lane {lane} {field}")
                self.assertIsNotNone(car["map_kpa"])
                cmd = np.asarray(car["cmd"], np.float32)
                raw = ACT_LO + (np.clip(cmd, -1.0, 1.0) + 1.0) * 0.5 * (ACT_HI - ACT_LO)
                slew = SLEW * T.DT
                want = np.clip(np.clip(raw, prev[lane] - slew, prev[lane] + slew), ACT_LO, ACT_HI)
                act = np.asarray(car["act"], np.float32)
                self.assertTrue(np.array_equal(act, want), f"frame {f['k']} lane {lane}")
                self.assertEqual(car["held"], [bool(h) for h in (act != raw)])
                any_held[lane] = any_held[lane] or any(car["held"])
                prev[lane] = act
            for i, h in enumerate(PREVIEW_S):
                j = min(f["k"] + int(h / T.DT), T.STEPS)
                self.assertAlmostEqual(f["cars"][0]["preview_pct"][i] / 100, grade[j] / 100,
                                       delta=1e-6)
            self.assertEqual(f["cars"][1]["preview_pct"], [0.0, 0.0, 0.0, 0.0])
        self.assertTrue(all(any_held))
        for lane in (0, 1):
            self.assertEqual(frames[-1]["cars"][lane]["damage"], self.trace.results[lane]["damage"])
            self.assertEqual(max(f["cars"][lane]["turb_c"] for f in frames),
                             self.trace.results[lane]["peak_turb"])
            self.assertEqual(self.trace.obs[lane].shape, (T.STEPS, OBS_DIM))

    @unittest.skipUnless(FULL, "--full only: the Phase D pair, about 2.5 min")
    @unittest.skipUnless(_RUNS_PAIR0_HERE, "runs/ or stable-baselines3 missing: Phase D path UNPROVEN")
    def test_phase_d_pair_full(self):
        from stable_baselines3 import SAC
        seed, weights = EPISODES[0]
        store = API.EpisodeStore()               # the production loader and episode_for
        got = _build_through_store(store, ("runs", 0, 1))
        want = [run_episode(agent_policy(SAC.load(str(ROOT / "runs" / f"{arm}_seed0") + "/final")),
                            seed, weights, arm == "sighted", road=None)
                for arm in ("sighted", "blind")]
        self.assertEqual(got.results, want)
        print(f"\n    Phase D == proof PROVEN on {got.device}", file=sys.stderr)


class _StubStore:
    """Answers polls like EpisodeStore and records them; never starts a thread."""
    needs_sb3 = False

    def __init__(self):
        self.calls = []

    def poll(self, key, since=0, preempt=False):
        self.calls.append((key, since, preempt))
        frames = [{"k": k, "cars": [None, None]} for k in range(3)]
        return {"status": "building", "progress": 3 / T.STEPS, "steps": T.STEPS,
                "since": since, "frames": frames[since:], "device": "cuda:0",
                "versions": {"torch": "t", "sb3": "s"}}


META_KEYS = {"experiment", "runs", "prefix", "protocol", "seed", "ep", "episode", "dt",
             "duration_s", "steps", "train_dt", "agents", "result_file", "preview_s", "act",
             "limits", "scenario", "verdict", "fingerprint_taken"}
EPISODE_URL = "/api/agents/episode?runs=runs_c4&seed=5&ep=1"


def _client(store):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    app = FastAPI()
    API.install(app, store=store)
    return app, TestClient(app)


class RouteTests(unittest.TestCase):
    """Spec test 10 and the episode route's contract."""

    def test_routes_only_under_simulation(self):
        code = ("import json, sys, app.server as s\n"
                "print(json.dumps({'mods': sorted(m for m in sys.modules if m.startswith('app.agent')),\n"
                "  'paths': sorted(r.path for r in s.app.routes if hasattr(r, 'path')),\n"
                "  'methods': sorted({m for r in s.app.routes for m in (getattr(r, 'methods', None) or ())})}))\n")
        run = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True,
                             text=True, timeout=180,
                             env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        self.assertEqual(run.returncode, 0, run.stderr[-2000:])
        got = json.loads(run.stdout.strip().splitlines()[-1])
        self.assertEqual(got["mods"], [], "--live/--replay would import agent code")
        self.assertFalse([p for p in got["paths"] if p.startswith(("/agents", "/api/agents"))])
        self.assertLessEqual(set(got["methods"]), {"GET", "HEAD"})

        tree = ast.parse((ROOT / "app" / "server.py").read_text(encoding="utf-8"))
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and getattr(n.func, "id", getattr(n.func, "attr", None)) == "install"]
        self.assertEqual(len(calls), 1, "install( must be called exactly once")
        guarded = [n for n in ast.walk(tree) if isinstance(n, ast.If)
                   and isinstance(n.test, ast.Attribute) and n.test.attr == "simulation"
                   and getattr(n.test.value, "id", None) == "a"]
        self.assertEqual(len(guarded), 1)
        inside = [n for n in ast.walk(guarded[0]) if n in calls]
        self.assertEqual(inside, calls, "install( must sit inside `if a.simulation:`")
        top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertFalse([n for n in top if "agent" in (getattr(n, "module", "") or "")],
                         "server.py must not import agent code at module level")

        app, client = _client(_StubStore())
        paths = {r.path: r for r in app.routes if hasattr(r, "methods")}
        self.assertLessEqual({"/agents", "/api/agents/episode"}, set(paths))
        for p in ("/agents", "/api/agents/episode"):
            self.assertEqual(set(paths[p].methods), {"GET"})
        self.assertEqual(client.post(EPISODE_URL).status_code, 405)

    @unittest.skipUnless(HAVE_C4, NO_C4)
    def test_episode_route_contract(self):
        stub = _StubStore()
        _, client = _client(stub)
        r = client.get(EPISODE_URL + "&since=0&preempt=1")
        self.assertEqual(r.status_code, 200, r.text[:500])
        self.assertEqual(r.headers.get("cache-control"), "no-store")
        body = r.json()
        self.assertLessEqual({"status", "progress", "steps", "since", "frames", "device",
                              "versions", "meta", "road"}, set(body))
        self.assertEqual(stub.calls, [(("runs_c4", 5, 1), 0, True)])
        meta = body["meta"]
        self.assertEqual(set(meta), META_KEYS)
        json.dumps(meta, allow_nan=False)
        self.assertEqual((meta["experiment"], meta["runs"], meta["prefix"], meta["protocol"],
                          meta["seed"], meta["ep"]), ("C4", "runs_c4", "c4", "d2", 5, 1))
        seed, weights, start_s, grade = EPISODES_D2[0]
        self.assertEqual(meta["episode"], {"seed": seed, "weights": list(weights),
                                           "climb_start_s": 141.0, "grade": grade})
        self.assertEqual((meta["dt"], meta["duration_s"], meta["steps"]), (1.0, 720.0, 719))
        self.assertEqual(meta["train_dt"], {"sighted": 0.2, "blind": 0.2})
        self.assertEqual([(a["tag"], a["arm"], a["scored"]) for a in meta["agents"]],
                         [("sighted_seed5", "sighted", "match"), ("blind_seed5", "blind", "match")])
        self.assertTrue(meta["result_file"])
        self.assertEqual(meta["preview_s"], list(PREVIEW_S))
        self.assertEqual(meta["act"]["neutral_phys"], [0.0, 0.0, 0.0, 1.0, 1.0])
        self.assertEqual(meta["act"]["lo"], [float(x) for x in ACT_LO])
        self.assertEqual(meta["limits"]["turb_c"], round(TURB_PROTECT_K - 273.15, 1))
        self.assertEqual(meta["verdict"]["state"], "found")
        self.assertEqual(meta["verdict"]["short"]["ar"], AC.SHORT_VERDICT["c4"]["ar"])
        self.assertRegex(meta["fingerprint_taken"], r"^\d\d:\d\d$")
        self.assertEqual(len(body["road"]["x_m"]), 720)
        self.assertNotIn("device", meta)

        later = client.get(EPISODE_URL + "&since=1").json()
        self.assertNotIn("meta", later)
        self.assertNotIn("road", later)
        self.assertEqual([f["k"] for f in later["frames"]], [1, 2])
        self.assertEqual(stub.calls[-1], (("runs_c4", 5, 1), 1, False))

        n = len(stub.calls)
        for q in ("runs=runs_c4&seed=5&ep=21", "runs=runs_c4&seed=5&ep=0",
                  "runs=runs_c4&seed=abc&ep=1", "runs=runs_c4&seed=5abc&ep=1",
                  "runs=runs_c4&seed=5&ep=1.5", "runs=..&seed=5&ep=1",
                  "runs=runs_c4%2F..&seed=5&ep=1", "runs=runs_zz&seed=5&ep=1",
                  "runs=runs_c4&seed=99&ep=1", "runs=runs_c4&seed=5&ep=1&since=abc",
                  "runs=runs_c4&seed=5", ""):
            with self.subTest(query=q):
                r = client.get("/api/agents/episode?" + q)
                self.assertEqual(r.status_code, 404)
                self.assertEqual(r.headers.get("cache-control"), "no-store")
        self.assertEqual(len(stub.calls), n, "a 404 must not reach the store")

    @unittest.skipUnless((ROOT / "runs_sixspeed_18sep" / "sighted_seed0").is_dir(),
                         "runs_sixspeed_18sep/ is not on this machine")
    def test_refused_pair_is_409_and_never_polled(self):
        stub = _StubStore()
        _, client = _client(stub)
        r = client.get("/api/agents/episode?runs=runs_sixspeed_18sep&seed=0&ep=1&preempt=1")
        self.assertEqual(r.status_code, 409)
        self.assertEqual(r.headers.get("cache-control"), "no-store")
        self.assertEqual(r.json()["status"], "refused")
        self.assertIn("no meta.json", " ".join(r.json()["problems"]))
        self.assertEqual(stub.calls, [])

    @unittest.skipUnless(HAVE_C4, NO_C4)
    def test_missing_sb3_is_503(self):
        stub = _StubStore()
        stub.needs_sb3 = True
        _, client = _client(stub)
        with mock.patch.object(API, "sb3_available", lambda: False):
            r = client.get(EPISODE_URL + "&preempt=1")
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.headers.get("cache-control"), "no-store")
        self.assertEqual(stub.calls, [])
        stub.needs_sb3 = False               # an injected loader needs no SB3
        with mock.patch.object(API, "sb3_available", lambda: False):
            self.assertEqual(client.get(EPISODE_URL).status_code, 200)


# Spec test 11. The snapshot is taken before the first test of this module and
# compared after the last, so it covers the whole suite, the proof included.
_SNAPSHOT = {}


def _snapshot():
    tops = [ROOT / "results", ROOT / "app", ROOT / ".git" / "index"]
    tops += sorted((ROOT / "runs_c4").glob("*_seed0"))
    files = {}
    for top in tops:
        if top.is_file():
            paths = [top]
        elif top.is_dir():
            paths = [p for p in top.rglob("*") if p.is_file()
                     and not {"__pycache__", "node_modules"} & set(p.relative_to(top).parts)]
        else:
            continue
        for p in paths:
            st = p.stat()
            files[p.relative_to(ROOT).as_posix()] = (st.st_size, st.st_mtime_ns)
    status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True,
                            text=True, timeout=60,
                            env=dict(os.environ, GIT_OPTIONAL_LOCKS="0")).stdout
    return files, status


def setUpModule():
    _SNAPSHOT["before"] = _snapshot()


def tearDownModule():
    files, status = _snapshot()
    before, before_status = _SNAPSHOT["before"]
    changed = sorted(p for p in set(before) | set(files) if before.get(p) != files.get(p))
    if changed or status != before_status:
        raise AssertionError("the suite changed files on disk: "
                             + ", ".join(changed[:20])
                             + ("" if status == before_status else " (and git status moved)"))


NEW_MODULES = ("agent_trace.py", "agent_catalog.py", "agent_api.py")
WRITE_PATTERNS = (
    (r"\bopen\s*\([^)]*,\s*(mode\s*=\s*)?['\"][^'\"]*[wax+]", "write-mode open"),
    (r"\.write\w*\s*\(", "write / write_text / write_bytes"),
    (r"\bjson\.dump\s*\(", "json.dump"),
    (r"\.save\w*\s*\(", "save"),
    (r"\bos\.(remove|unlink|rename|replace|rmdir|mkdir|makedirs)\b", "os file operation"),
    (r"\bshutil\b", "shutil"),
    (r"\bmkdir\b", "mkdir"),
    (r"\.(unlink|touch|rmdir)\s*\(", "pathlib file operation"),
)


def _code(path):
    """Source without docstrings and comments, as test_replay's scan reads it."""
    src = path.read_text(encoding="utf-8")
    src = re.sub(r'""".*?"""', "", src, flags=re.S)
    return re.sub(r"#.*", "", src)


class NoWriteTests(unittest.TestCase):
    """Spec test 11, static half: the new modules contain no way to write."""

    def test_new_modules_cannot_write(self):
        bad = []
        for name in NEW_MODULES:
            code = _code(ROOT / "app" / name)
            for pattern, why in WRITE_PATTERNS:
                for m in re.finditer(pattern, code):
                    bad.append(f"{name}:{code[:m.start()].count(chr(10)) + 1} {why}")
        self.assertEqual(bad, [])

    def test_the_scan_can_fail(self):
        probe = ('with open(p, "w") as f:\n    f.write_text(x)\njson.dump(o, f)\n'
                 'model.save(p)\nos.remove(p)\nimport shutil\nPath(p).mkdir()\n')
        hits = {why for pattern, why in WRITE_PATTERNS if re.search(pattern, probe)}
        self.assertEqual(hits, {why for _, why in WRITE_PATTERNS} - {"pathlib file operation"})
        self.assertFalse([w for p, w in WRITE_PATTERNS
                          if re.search(p, 'open(p, encoding="utf-8")\njson.dumps(x)\ns.replace("a", "b")\n')])


NET_ROOTS = {"urllib", "http", "socket", "requests", "httpx", "typesafe_sdk"}
NET_ALLOWED = set()          # M3 allows exactly {"jev.py"}


class NoNetworkTests(unittest.TestCase):
    """Spec test 13: an AST import scan, so 'WebSocket' in server.py is not a hit."""

    def test_no_network_imports_in_app(self):
        found = []
        for path in sorted((ROOT / "app").glob("*.py")):
            if path.name.startswith("test_") or path.name in NET_ALLOWED:
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    roots = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    roots = [(node.module or "").split(".")[0]]
                else:
                    continue
                found += [f"{path.name}:{node.lineno} {r}" for r in roots if r in NET_ROOTS]
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]] + [a for a in sys.argv[1:] if a != "--full"], verbosity=2)

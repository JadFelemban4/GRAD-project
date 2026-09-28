"""The agent replay page's own suite. Nothing here writes, trains or evaluates.

    python -m app.test_agents          the default suite
    python -m app.test_agents --full   adds the slow checks

Run from the repository root. app/test_replay.py's test_read_only scans this
file too, so banned tokens are written as raw regexes, never as calls, and
fixtures are made in temporary directories OUTSIDE the repository.
"""
import ast
import contextlib
import http.client
import importlib.util
import io
import json
import logging
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import unittest
from unittest import mock
from urllib.error import HTTPError, URLError
import urllib.request
import warnings

import numpy as np

import fingerprint as FP
from app import agent_api as API
from app import agent_catalog as AC
from app import agent_trace as T
from app import jev as JEV
from app import laya_bridge as LB
from app import model_questions as MQ
from check_premise import p_grade_now, p_neutral
from engine_env import (ACT_HI, ACT_LO, OBS_DIM, OIL_PROTECT_K, PREVIEW_S, SLEW,
                        TURB_PROTECT_K, SupervisoryTunerEnv, make_grade_climb,
                        neutral_action)
from evaluate import EPISODES, EPISODES_D2, agent_policy, run_episode

ROOT = Path(__file__).resolve().parent.parent
FULL = "--full" in sys.argv

C4_SEEDS = range(8)
HAVE_C4 = all((ROOT / "runs_c4" / f"{arm}_seed{k}" / "final.zip").is_file()
              for arm in ("sighted", "blind") for k in C4_SEEDS)
NO_C4 = "runs_c4/ is not on this machine: the catalog path is UNPROVEN here"
ALL_RUNS = ("runs", "runs_d2", "runs_c4")
HAVE_ALL_RUNS = all((ROOT / d / f"{arm}_seed{k}" / "final.zip").is_file()
                    for d in ALL_RUNS for arm in ("sighted", "blind") for k in range(8))
NO_ALL_RUNS = ("runs/, runs_d2/ and runs_c4/ are not all complete on this machine: "
               "the catalog is UNPROVEN here")


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

    def test_episode_row(self):
        """The picker's row for one frozen episode, read from the road the env steps."""
        want = {("d2", 1): (1000, 141.0, 0.13314),
                # the table says 281.95; random_road.climb starts the grade at int(281.95)
                ("d2", 2): (1001, 281.0, 0.15025),
                ("phase-d", 1): (1000, 180.0, 0.12),
                ("phase-d", 20): (1019, 180.0, 0.12)}
        for (protocol, idx), (seed, climb, grade) in want.items():
            with self.subTest(protocol=protocol, idx=idx):
                ep = T.episode(protocol, idx)
                row = T.episode_row(ep, T.route(T.build_cycle(ep)))
                self.assertEqual(row, {"idx": idx, "seed": seed, "weights": list(ep["weights"]),
                                       "climb_start_s": climb, "grade": grade})
                json.dumps(row, allow_nan=False)
        ep = T.episode("phase-d", 1)
        cycle = T.build_cycle(ep)                      # a fresh cycle: nothing shared is touched
        cycle["grade"] = np.zeros_like(cycle["grade"])
        row = T.episode_row(ep, T.route(cycle))
        self.assertEqual((row["climb_start_s"], row["grade"]), (None, None))

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


def _fake_agent(root, runs, name, src_arm, drop=(), src_runs="runs_c4", **meta_changes):
    """A copy of <src_runs>/<src_arm>_seed0 at root/runs/name, built with
    shutil.copy and json.dump only. `drop` names files to leave out."""
    src = ROOT / src_runs / f"{src_arm}_seed0"
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

    def test_table_rows_are_the_results_tables(self):
        """Quoted from analyse_phase_d2.load, one decimal, exactly as each printed
        table shows its blind-sighted column; never recomputed here."""
        import analyse_phase_d2 as A2
        printed = re.compile(r"^ +(\d+) +[\d.]+ +[\d.]+ +[\d.]+ +[\d.]+ +([+-]\d+\.\d)$", re.M)
        for prefix, table in (("c4", "C4_RESULT.txt"), ("d2", "PHASE_D2_RESULT.txt"),
                              ("phase_d", "PHASE_D_RESULT.txt")):
            with self.subTest(prefix=prefix):
                with warnings.catch_warnings():       # analyse_phase_d.parse leaves files to the GC
                    warnings.simplefilter("ignore", ResourceWarning)
                    rows, incomplete = A2.load(prefix)
                got = AC.table_rows(prefix)
                self.assertEqual(got, {"diffs": {s: round(d, 1) for s, _, d in rows},
                                       "incomplete": [s for s, _ in incomplete]})
                text = (ROOT / "results" / table).read_text(encoding="utf-8")
                first_table = printed.findall(text)[:8]     # PHASE_D2_RESULT.txt prints two
                self.assertEqual(got["diffs"], {int(s): float(d) for s, d in first_table})
        self.assertEqual([AC.table_rows("c4")["diffs"][0], AC.table_rows("c4")["diffs"][5],
                          AC.table_rows("d2")["diffs"][0], AC.table_rows("phase_d")["diffs"][3]],
                         [360.6, -0.3, 221.7, 387.2])
        self.assertEqual(AC.table_rows("zz"), {"diffs": {}, "incomplete": []})

    @unittest.skipUnless(HAVE_C4, NO_C4)
    def test_discover_synthetic(self):
        """Spec test 7, the M2 part: what discover lists, what it ignores, and a
        half pair listed with its missing arm rather than dropped."""
        threads = threading.active_count()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _fake_pair(root, "runs_zz")                                  # seed 0: a clean pair
            _fake_agent(root, "runs_zz", "sighted_seed1", "sighted")     # seed 1: half a pair
            (root / "runs_zz" / "_logs").mkdir()
            (root / "runs_zz" / "sighted_seedX").mkdir()
            meta = root / "runs_zz" / "sighted_seed0" / "meta.json"
            shutil.copy(meta, root / "runs_zz" / "notes.txt")
            (root / "runs_zzempty").mkdir()
            (root / "Runs_zzupper").mkdir()       # Windows' glob ignores case; RUNS_NAME does not
            shutil.copy(meta, root / "runs_zzfile")  # a FILE whose name RUNS_NAME accepts
            cat = AC.discover(root)
        self.assertEqual([e["runs"] for e in cat], ["runs_zz", "runs_zzempty"])
        zz, empty = cat
        self.assertEqual((zz["name"], zz["prefix"], zz["protocol"]),
                         ("runs_zz (no name recorded)", "zz", "d2"))
        self.assertEqual((zz["verdict"]["state"], zz["verdict"]["short"]), ("none", AC.NONE_TEXT))
        self.assertEqual([p["seed"] for p in zz["pairs"]], [0, 1])
        p0, p1 = zz["pairs"]
        self.assertEqual({k: p0[k] for k in ("runnable", "reason", "problems", "protocol",
                                             "result_file", "table_diff")},
                         {"runnable": True, "reason": None, "problems": [], "protocol": "d2",
                          "result_file": False, "table_diff": None})
        self.assertEqual([(a["tag"], a["status"], a["scored"]) for a in p0["agents"]],
                         [("sighted_seed0", "ready", "not recorded"),
                          ("blind_seed0", "ready", "not recorded")])
        for a in p0["agents"] + p1["agents"]:
            self.assertEqual(set(a), set(AC.CATALOG_AGENT_KEYS))
        missing = "blind_seed1: missing -- no such directory"
        self.assertEqual((p1["runnable"], p1["reason"], p1["problems"], p1["protocol"]),
                         (False, missing, [missing], None))
        self.assertEqual([(a["status"], a["scored"]) for a in p1["agents"]],
                         [("ready", None), ("missing", None)])
        self.assertEqual((empty["pairs"], empty["protocol"], empty["verdict"]["state"]),
                         ([], None, "none"))
        json.dumps(T.jsonable(cat), allow_nan=False)
        self.assertEqual(threading.active_count(), threads, "discover started a thread")

    @unittest.skipUnless(HAVE_C4, NO_C4)
    def test_refused_pairs_keep_every_problem(self):
        """check_pair's dict on the sha path, and the catalog keeping EVERY problem
        of a refused pair, both arms (ledger gap 3). An arm whose recorded sha
        differs is 'mismatch': 'not recorded' beside 'records zip sha X' would
        contradict the problem printed next to it."""
        threads = threading.active_count()
        real = {arm: FP.model_budget(str(ROOT / "runs_c4" / f"{arm}_seed0" / "final.zip"))["sha"]
                for arm in AC.ARMS}
        wrong = "0123456789abcdef"

        def line(arm, k):
            return (f"{arm}_seed{k}: not the scored artefact -- results/zz_seed{k}.txt "
                    f"records zip sha {wrong}, final.zip is {real[arm]}")

        # seed: (the sha results/ records for sighted, for blind); None = no line for that arm
        recorded = {0: (wrong, None), 1: (wrong, wrong), 2: (wrong, real["blind"])}
        problems = {0: [line("sighted", 0)], 1: [line("sighted", 1), line("blind", 1)],
                    2: [line("sighted", 2)]}
        scored = {0: ["mismatch", "not recorded"], 1: ["mismatch", "mismatch"],
                  2: ["mismatch", "match"]}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "results").mkdir()
            for k, shas in recorded.items():
                for arm in AC.ARMS:
                    _fake_agent(root, "runs_zz", f"{arm}_seed{k}", arm)
                with open(root / "results" / f"zz_seed{k}.txt", "w", encoding="utf-8") as fh:
                    for arm, sha in zip(AC.ARMS, shas):
                        if sha is not None:
                            fh.write(_result_line(f"runs_zz\\{arm}_seed{k}", sha))
            for k in recorded:
                with self.subTest(seed=k):
                    pair = AC.check_pair("runs_zz", k, root)
                    self.assertEqual({key: v for key, v in pair.items() if key != "agents"},
                                     {"runs": "runs_zz", "seed": k, "prefix": "zz",
                                      "experiment": "runs_zz (no name recorded)",
                                      "protocol": "d2", "result_file": True,
                                      "problems": problems[k]})
                    self.assertEqual([(a["status"], a["scored"]) for a in pair["agents"]],
                                     list(zip(["ready", "ready"], scored[k])))
                    with self.assertRaises(AC.Refused) as cm:
                        AC.find_pair("runs_zz", k, root)
                    self.assertEqual(cm.exception.problems, problems[k])

            # half a pair whose present arm is refused too: both arms' problems
            _fake_agent(root, "runs_zz", "blind_seed3", "blind", drop=("meta.json",))
            # a plant that moved under both arms: each arm's status line and its fields
            _fake_pair(root, "runs_zzplant", plant_sha="0000000000000000")
            plant = AC.check_pair("runs_zzplant", 0, root)["problems"]
            cat = {e["runs"]: e for e in AC.discover(root)}
        zz = cat["runs_zz"]
        self.assertEqual([p["seed"] for p in zz["pairs"]], [0, 1, 2, 3])
        self.assertIsNone(zz["protocol"], "no pair of runs_zz can run")
        for p in zz["pairs"][:3]:
            with self.subTest(catalog_seed=p["seed"]):
                k = p["seed"]
                self.assertEqual((p["runnable"], p["reason"], p["problems"], p["protocol"],
                                  p["result_file"]),
                                 (False, problems[k][0], problems[k], None, True))
                self.assertEqual([a["scored"] for a in p["agents"]], scored[k])
        half = zz["pairs"][3]
        want = ["sighted_seed3: missing -- no such directory",
                "blind_seed3: incompatible -- no meta.json: plant unknown (AUDIT2 C2-1)"]
        self.assertEqual((half["runnable"], half["reason"], half["problems"], half["result_file"]),
                         (False, want[0], want, False))
        self.assertEqual([(a["status"], a["scored"]) for a in half["agents"]],
                         [("missing", None), ("incompatible", None)])
        pp = cat["runs_zzplant"]["pairs"][0]
        self.assertEqual((pp["runnable"], pp["reason"], pp["problems"]), (False, plant[0], plant))
        for arm in AC.ARMS:
            self.assertIn(f"{arm}_seed0: incompatible -- plant mismatch: plant_sha", plant)
            self.assertTrue(any(p.startswith(f"{arm}_seed0: plant_sha: stored '0000000000000000' live")
                                for p in plant), plant)
        json.dumps(T.jsonable(list(cat.values())), allow_nan=False)
        self.assertEqual(threading.active_count(), threads, "the catalog started a thread")

    def test_catalog_real_tree(self):
        """Spec test 6: every experiment on this machine, as the page will list it."""
        if not HAVE_ALL_RUNS:
            print(f"\n    {NO_ALL_RUNS}", file=sys.stderr)
            self.skipTest(NO_ALL_RUNS)
        cat = AC.discover()
        names = [e["runs"] for e in cat]
        self.assertEqual(names, sorted(names))
        self.assertLessEqual(set(ALL_RUNS), set(names))
        by_runs = {e["runs"]: e for e in cat}
        want = {"runs": ("Phase D", "phase_d", "phase-d", "trained 50000 steps", "not recorded"),
                "runs_d2": ("Phase D2", "d2", "d2", "trained 50000 steps", "not recorded"),
                "runs_c4": ("C4", "c4", "d2", "trained 300000 steps", "match")}
        pairs = ready = 0
        for runs, (name, prefix, protocol, budget, scored) in want.items():
            with self.subTest(runs=runs):
                e = by_runs[runs]
                self.assertEqual((e["name"], e["prefix"], e["protocol"]), (name, prefix, protocol))
                self.assertEqual(e["verdict"]["state"], "found", e["verdict"]["missing"])
                self.assertEqual(e["verdict"]["short"],
                                 {k: AC.SHORT_VERDICT[prefix][k] for k in ("ar", "en")})
                self.assertEqual([p["seed"] for p in e["pairs"]], list(range(8)))
                diffs = AC.table_rows(prefix)["diffs"]
                for p in e["pairs"]:
                    self.assertTrue(p["runnable"], p["problems"])
                    self.assertEqual((p["reason"], p["problems"], p["protocol"], p["result_file"]),
                                     (None, [], protocol, True))
                    self.assertEqual(p["table_diff"], diffs[p["seed"]])
                    for a in p["agents"]:
                        self.assertEqual(a["status"], "ready", a["reason"])
                        self.assertTrue(a["budget_line"].startswith(budget + " "), a["budget_line"])
                        self.assertEqual((a["train_dt"], a["scored"]), (0.2, scored))
                        ready += 1
                    pairs += 1
        self.assertEqual((pairs, ready), (24, 48))
        six = by_runs.get("runs_sixspeed_18sep")
        if six is not None:
            self.assertEqual([p["seed"] for p in six["pairs"]], [0])
            p = six["pairs"][0]
            self.assertFalse(p["runnable"])
            self.assertIn("no meta.json: plant unknown (AUDIT2 C2-1)", p["reason"])
            self.assertEqual([a["status"] for a in p["agents"]], ["incompatible"] * 2)
            self.assertEqual((p["protocol"], six["protocol"], six["verdict"]["state"]),
                             (None, None, "none"))
        json.dumps(T.jsonable(cat), allow_nan=False)

    def test_read_agent_refuses_a_directory_that_is_not_there(self):
        """M1 called a missing directory 'incompatible (no meta.json)'; discover
        lists only directories that exist, so a missing one is a KeyError."""
        with tempfile.TemporaryDirectory() as tmp:
            for runs, name, root in (("runs_c4", "sighted_seed99", ROOT),
                                     ("runs_zz", "blind_seed0", tmp)):
                with self.subTest(runs=runs, name=name):
                    with self.assertRaises(KeyError):
                        AC.read_agent(runs, name, root)

    @unittest.skipUnless(HAVE_C4, NO_C4)
    def test_status_and_pair_gaps(self):
        """The M1 test gaps: an unknown protocol, an unreadable final.zip, and
        two arms on different protocols; and check_pair agrees with find_pair."""
        threads = threading.active_count()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertNotIn(str(ROOT.resolve()).lower(), str(root.resolve()).lower())

            # (a) a protocol this code does not know
            _fake_agent(root, "runs_zzproto", "sighted_seed0", "sighted",
                        scenario={"protocol": "something-else"})
            a = AC.read_agent("runs_zzproto", "sighted_seed0", root)
            self.assertEqual((a["status"], a["reason"]), ("incompatible", "unknown protocol"))

            # (b) a final.zip that is not a stable-baselines3 zip: incomplete, not ready
            _fake_agent(root, "runs_zzbadzip", "sighted_seed0", "sighted")
            d = _fake_agent(root, "runs_zzbadzip", "blind_seed0", "blind", drop=("final.zip",))
            shutil.copy(d / "meta.json", d / "final.zip")
            a = AC.read_agent("runs_zzbadzip", "blind_seed0", root)
            self.assertEqual((a["status"], a["reason"], a["zip_sha"], a["budget_line"]),
                             ("incomplete", AC.UNREADABLE_ZIP, None, None))
            self.assertEqual((a["protocol"], a["train_dt"]), ("d2", 0.2))
            want = ["blind_seed0: incomplete -- final.zip is not a readable stable-baselines3 zip"]
            pair = AC.check_pair("runs_zzbadzip", 0, root)
            self.assertEqual((pair["problems"], pair["protocol"]), (want, None))
            self.assertEqual([a["scored"] for a in pair["agents"]], [None, None])
            with self.assertRaises(AC.Refused) as cm:
                AC.find_pair("runs_zzbadzip", 0, root)
            self.assertEqual(cm.exception.problems, want)

            # (c) a clean pair: check_pair finds nothing, and find_pair returns the same dict
            _fake_pair(root, "runs_zzclean")
            pair = AC.check_pair("runs_zzclean", 0, root)
            self.assertEqual((pair["problems"], pair["protocol"], pair["result_file"]),
                             ([], "d2", False))
            self.assertEqual([a["scored"] for a in pair["agents"]], ["not recorded"] * 2)
            self.assertEqual(AC.find_pair("runs_zzclean", 0, root), pair)
            with self.assertRaises(KeyError):
                AC.check_pair("runs_zzclean", 1, root)

            # (d) two ready arms trained on different protocols
            with self.subTest("the two arms on different protocols"):
                if not (ROOT / "runs" / "sighted_seed0" / "final.zip").is_file():
                    self.skipTest("runs/sighted_seed0 is not on this machine")
                _fake_agent(root, "runs_zzmix", "sighted_seed0", "sighted", src_runs="runs")
                _fake_agent(root, "runs_zzmix", "blind_seed0", "blind")
                pair = AC.check_pair("runs_zzmix", 0, root)
                self.assertEqual([(a["status"], a["protocol"]) for a in pair["agents"]],
                                 [("ready", "phase-d"), ("ready", "d2")])
                want = ["the two arms were trained on different protocols: phase-d and d2"]
                self.assertEqual((pair["problems"], pair["protocol"]), (want, None))
                with self.assertRaises(AC.Refused) as cm:
                    AC.find_pair("runs_zzmix", 0, root)
                self.assertEqual(cm.exception.problems, want)
        self.assertEqual(threading.active_count(), threads, "the catalog started a thread")

    def test_c4_verdict(self):
        v = AC.verdict("c4")
        self.assertEqual(v["state"], "found", v["missing"])
        self.assertEqual(v["missing"], [])
        by_key = {ln["key"]: ln for ln in v["lines"]}
        self.assertEqual({k: ln["line"] for k, ln in by_key.items()},
                         {"result": 42, "seeds": 28, "disagree": 33, "convergence": 48,
                          "reading": 50, "explanations": 41, "one_seed": 633})
        for a in AC.VERDICT_LINES["c4"]:
            with self.subTest(anchor=a.key):
                src = (ROOT / "results" / a.file).read_text(encoding="utf-8").splitlines()
                ln = by_key[a.key]
                self.assertEqual(ln["file"], a.file)
                self.assertEqual(ln["text"], "\n".join(src[ln["line"] - 1:ln["line"] - 1 + a.n]))
        # The sign test's p is never quoted without its heading, and never
        # without the permutation test's p beside it (C4_RESULT.txt:28-30).
        seeds = by_key["seeds"]["text"].splitlines()
        self.assertEqual(len(seeds), 3)
        self.assertEqual(seeds[0].strip(), "H1: the effect is smaller than the MEI (50 units)")
        self.assertIn("(7 of 8 seeds below 50)", seeds[1])
        self.assertIn("exact paired permutation test", seeds[2])
        self.assertIn("p = 0.3867", seeds[2])
        # Item 2 of PREREGISTRATION_C4.md section 11 is quoted WHOLE, through
        # its closing caveat, never cut at "The permutation test," (:633-643).
        one_seed = by_key["one_seed"]["text"]
        self.assertIn("one\n   seed the other way and the cell would be INCONCLUSIVE", one_seed)
        self.assertIn("does not reject (p = 0.3867)", one_seed)
        self.assertTrue(one_seed.endswith("is not\n   settled.**"), one_seed[-60:])
        prereg = (ROOT / "results" / "PREREGISTRATION_C4.md").read_text(encoding="utf-8").splitlines()
        after = prereg[by_key["one_seed"]["line"] - 1 + len(one_seed.splitlines())]
        self.assertTrue(after.startswith("3. "), f"the quote must end where item 3 begins: {after!r}")
        self.assertEqual(v["short"], {k: AC.SHORT_VERDICT["c4"][k] for k in ("ar", "en")})
        self.assertLessEqual(set(AC.SHORT_VERDICT["c4"]["requires"]),
                             {a.key for a in AC.VERDICT_LINES["c4"]})
        self.assertEqual([c["cell"] for c in v["cells"]], ["SMALLER THAN THE MEI", "NOT-CONVERGED"])
        for c in v["cells"]:
            self.assertEqual(c["gloss"], AC.GLOSS[c["cell"]])
        gloss = AC.GLOSS["SMALLER THAN THE MEI"]
        for lang, one_seed in (("ar", "بذرة واحدة"), ("en", "one seed")):
            for needle in ("50", "300\u202f000", one_seed):
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
        self.assertEqual(v["short"], {lang: AC.MISSING_TEXT[lang].format(files="results/C4_RESULT.txt")
                                      for lang in ("ar", "en")})
        self.assertEqual([c["cell"] for c in v["cells"]], ["SMALLER THAN THE MEI"])
        self.assertEqual(AC.verdict("zz")["state"], "none")

    def test_d2_and_phase_d_verdicts(self):
        """Spec test 8, the M2 rows: each anchor where results/ has it, each quote
        a WHOLE item -- the file's next line is blank (the M1 final review, F8)."""
        want = {"d2": {"result": 30, "c1": 86},
                "phase_d": {"result": 26, "not_blind": 33, "post_hoc": 65}}
        texts = {}
        for prefix, where in want.items():
            with self.subTest(prefix=prefix):
                v = AC.verdict(prefix)
                self.assertEqual((v["state"], v["missing"]), ("found", []))
                by_key = {ln["key"]: ln for ln in v["lines"]}
                self.assertEqual({k: ln["line"] for k, ln in by_key.items()}, where)
                for a in AC.VERDICT_LINES[prefix]:
                    src = (ROOT / "results" / a.file).read_text(encoding="utf-8").splitlines()
                    ln = by_key[a.key]
                    self.assertEqual(ln["file"], a.file)
                    self.assertEqual(ln["text"], "\n".join(src[ln["line"] - 1:ln["line"] - 1 + a.n]))
                    self.assertEqual(src[ln["line"] - 1 + a.n].strip(), "",
                                     f"{prefix}.{a.key} must quote its whole item")
                    texts[prefix, a.key] = ln["text"]
                self.assertEqual(v["short"], {k: AC.SHORT_VERDICT[prefix][k] for k in ("ar", "en")})
                for c in v["cells"]:
                    self.assertEqual(c["gloss"], AC.GLOSS[c["cell"]])
        self.assertEqual([c["cell"] for c in AC.verdict("d2")["cells"]], ["INCONCLUSIVE"])
        self.assertEqual([c["cell"] for c in AC.verdict("phase_d")["cells"]],
                         ["NOT SIGNIFICANT", "INCONCLUSIVE (post-hoc)"])
        # What each quote must carry, so that none is cut before its caveat.
        self.assertTrue(texts["d2", "result"].endswith("from Phase D's measured spread."))
        self.assertIn("never 'preview does not", texts["d2", "c1"])
        self.assertIn("NOT 'preview does not help'", texts["phase_d", "result"])
        self.assertTrue(texts["phase_d", "not_blind"].endswith("limits 7 and 8."))
        self.assertIn("[MEI set AFTER this result", texts["phase_d", "post_hoc"])
        self.assertIn("POST-HOC reading", texts["phase_d", "post_hoc"])
        self.assertTrue(texts["phase_d", "post_hoc"].endswith("records the ordering."))
        # The short lines keep their qualifiers, in both languages.
        grouped = "50" + chr(0x202F) + "000"
        for lang in ("ar", "en"):
            self.assertIn(grouped, AC.SHORT_VERDICT["d2"][lang])
            self.assertIn("C1", AC.SHORT_VERDICT["d2"][lang])
            self.assertIn("C1", AC.SHORT_VERDICT["phase_d"][lang])
        self.assertIn(chr(0x200F) + "(" + grouped, AC.SHORT_VERDICT["d2"]["ar"])
        self.assertIn("ليست عمياء", AC.SHORT_VERDICT["phase_d"]["ar"])
        self.assertIn("قراءة لاحقة", AC.SHORT_VERDICT["phase_d"]["ar"])
        self.assertIn("post-hoc", AC.SHORT_VERDICT["phase_d"]["en"])
        self.assertIn("not blind", AC.SHORT_VERDICT["phase_d"]["en"])
        post_hoc = AC.GLOSS["INCONCLUSIVE (post-hoc)"]
        self.assertIn("قراءة لاحقة", post_hoc["ar"])
        self.assertIn("post-hoc", post_hoc["en"])

    def test_verdict_when_an_anchor_or_a_file_is_gone(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = Path(tmp) / "results"
            res.mkdir()
            for f in ("PHASE_D_RESULT.txt", "PHASE_D2_RESULT.txt"):
                shutil.copy(ROOT / "results" / f, res / f)
            self.assertEqual([AC.verdict(p, tmp)["state"] for p in ("d2", "phase_d")],
                             ["found", "found"])
            lines = (res / "PHASE_D_RESULT.txt").read_text(encoding="utf-8").splitlines()
            self.assertTrue(lines[32].lstrip().startswith("AND THE BLINDED ARM IS NOT BLIND."))
            del lines[32]
            with open(res / "PHASE_D_RESULT.txt", "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + "\n")
            v, d2 = AC.verdict("phase_d", tmp), AC.verdict("d2", tmp)
        self.assertEqual((v["state"], v["missing"]), ("missing", ["PHASE_D_RESULT.txt"]))
        self.assertEqual(v["short"], {lang: AC.MISSING_TEXT[lang].format(
            files="results/PHASE_D_RESULT.txt") for lang in ("ar", "en")})
        self.assertEqual([ln["key"] for ln in v["lines"]], ["result", "post_hoc"])
        self.assertEqual([c["cell"] for c in v["cells"]],
                         ["NOT SIGNIFICANT", "INCONCLUSIVE (post-hoc)"])
        self.assertEqual(d2["state"], "found")

        # No results/ at all: every file is named, not only the first.
        with tempfile.TemporaryDirectory() as tmp:
            got = {p: AC.verdict(p, tmp) for p in ("phase_d", "d2", "c4")}
        self.assertEqual(got["phase_d"]["missing"], ["PHASE_D2_RESULT.txt", "PHASE_D_RESULT.txt"])
        self.assertEqual(got["phase_d"]["short"], {lang: AC.MISSING_TEXT[lang].format(
            files="results/PHASE_D2_RESULT.txt · results/PHASE_D_RESULT.txt")
            for lang in ("ar", "en")})
        self.assertEqual(got["d2"]["missing"], ["PHASE_D2_RESULT.txt"])
        self.assertEqual(got["c4"]["missing"], ["C4_RESULT.txt", "PREREGISTRATION_C4.md"])
        for prefix, v in got.items():
            with self.subTest(prefix=prefix):
                self.assertEqual((v["state"], v["lines"], v["cells"]), ("missing", [], []))
        none = AC.verdict("sixspeed_18sep")
        self.assertEqual((none["state"], none["short"]), ("none", AC.NONE_TEXT))

    def test_every_prefix_has_its_cells_glosses_and_short_line(self):
        self.assertEqual(set(AC.VERDICT_LINES), {"c4", "d2", "phase_d"})
        self.assertEqual(set(AC.CELLS), set(AC.VERDICT_LINES))
        self.assertEqual(set(AC.SHORT_VERDICT), set(AC.VERDICT_LINES))
        for prefix, anchors in AC.VERDICT_LINES.items():
            with self.subTest(prefix=prefix):
                keys = [a.key for a in anchors]
                self.assertEqual(len(keys), len(set(keys)), "anchor keys must be unique")
                self.assertLessEqual(set(AC.SHORT_VERDICT[prefix]["requires"]), set(keys))
                self.assertLessEqual(set(AC.CELLS[prefix]), set(keys))
                for cell in AC.CELLS[prefix].values():
                    self.assertEqual(set(AC.GLOSS[cell]), {"ar", "en"}, cell)
                    self.assertTrue(all(AC.GLOSS[cell].values()), cell)
                # A pattern that matched two lines could quote the wrong one:
                # 'RESULT: INCONCLUSIVE' alone is on PHASE_D2_RESULT.txt:30 AND :65.
                for a in anchors:
                    src = (ROOT / "results" / a.file).read_text(encoding="utf-8").splitlines()
                    hits = [i + 1 for i, line in enumerate(src) if re.search(a.pattern, line)]
                    self.assertEqual(len(hits), 1, f"{prefix}.{a.key} matches lines {hits}")

    def test_no_plain_space_inside_a_grouped_number(self):
        # (?!\d), not \b: an Arabic letter is a word character, so \b misses a
        # group that runs straight into Arabic text (M1 build record, Task 10b).
        plain = r"\d \d{3}(?!\d)"
        self.assertIsNotNone(re.search(plain, "300 000خطوة"), "the check itself must be able to fail")
        for table_name, table in (("SHORT_VERDICT", AC.SHORT_VERDICT), ("GLOSS", AC.GLOSS)):
            for key, langs in table.items():
                for lang in ("ar", "en"):
                    s = langs[lang]
                    self.assertIsNone(
                        re.search(plain, s),
                        f"{table_name}[{key!r}][{lang!r}] has a plain-space thousands "
                        "separator")
        # The invisible characters are written as escapes in the source, never
        # as themselves (the Write tool once turned escapes into characters).
        src = Path(AC.__file__).read_text(encoding="utf-8")
        for cp in (0x202F, 0x200F):
            self.assertNotIn(chr(cp), src, f"agent_catalog.py carries a literal U+{cp:04X}")

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


def _fake_tracer(n=5, gate=None, fail=None, obs=False, hold=None):
    """A stand-in for run_lanes: n paired frames, each held at `gate` if one
    is given; `fail` is raised in place of frame 2; `hold`, an Event, holds
    the build once frame 1 is out until it is set, so 'building' with frames
    0 and 1 is a stable state rather than a window of a few milliseconds."""
    def tracer(lanes, ep, on_frame):
        assert [use for _, use in lanes] == [True, False], "lane 0 sighted, lane 1 blind"
        for k in range(n):
            if gate is not None:
                gate.wait(5)
            if fail is not None and k == 2:
                raise fail
            seen = [np.full(OBS_DIM, k, np.float32), None] if obs else [None, None]
            on_frame({"k": k, "cars": [None, None]}, seen)
            if hold is not None and k == 1:
                hold.wait(5)
            time.sleep(0.01)
        return [{"damage": 1.0}, {"damage": 2.0}]
    return tracer


def _wait_for(store, key, want, limit=10.0, frames=None):
    """Poll until `want`, and (when `frames` is given) until that many frames are out."""
    t0 = time.monotonic()
    while True:
        r = store.poll(key)
        if r["status"] == want and (frames is None or len(r["frames"]) == frames):
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
        hold = threading.Event()
        s = self.store(loader=slow, tracer=_fake_tracer(hold=hold))
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
        try:
            # The tracer holds after frame 1, so 'building' cannot be missed.
            r = _wait_for(s, self.K1, "building", frames=2)
            self.assertEqual([f["k"] for f in r["frames"]], [0, 1],
                             "the first slice must start at frame 0")
            later = s.poll(self.K1, since=1)
            self.assertEqual((later["status"], later["since"]), ("building", 1))
            self.assertEqual(later["frames"][0]["k"], 1, "since=1 must start the slice at frame 1")
        finally:
            hold.set()
        _wait_for(s, self.K1, "ready")

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
        for t in _builders():                # join, never poll: a poll would rebuild a cancelled K1
            t.join(5)
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

    def test_preempt_answered_from_the_cache_cancels_the_other_build(self):
        """M1 F6: «احسب» for an episode answered from the cache, or with its
        error, still stops the build nobody is watching any more. A plain poll
        answered from the cache stops nothing."""
        gate = threading.Event()
        gated = _fake_tracer(gate=gate)
        k4, k5 = ("runs_c4", 5, 4), ("runs_c4", 5, 5)

        def tracer(lanes, ep, on_frame):
            if ep["idx"] == 4:
                raise ValueError("episode 4 always fails")
            return gated(lanes, ep, on_frame)

        def settle():                        # the worker has returned, not just published
            for t in _builders():
                t.join(5)
        s = self.store(tracer=tracer)
        gate.set()
        s.poll(self.K2)
        _wait_for(s, self.K2, "ready")
        settle()

        # a plain poll answered from the cache cancels nothing. Read the cache
        # after settle(), never through _wait_for: polling K1 to an idle store
        # would rebuild a cancelled K1 and hide the cancel.
        gate.clear()
        self.assertEqual(s.poll(self.K1, preempt=True)["status"], "loading")
        self.assertEqual(s.poll(self.K2)["status"], "ready")
        gate.set()
        settle()
        self.assertIsNotNone(s.trace(self.K1),
                             "a plain poll answered from the cache cancelled the build")

        # «احسب» for a cached episode: answered from the cache, and K3 is cancelled
        gate.clear()
        self.assertEqual(s.poll(self.K3, preempt=True)["status"], "loading")
        r = s.poll(self.K2, preempt=True)
        self.assertEqual((r["status"], len(r["frames"])), ("ready", 5))
        gate.set()
        settle()
        self.assertIsNone(s.trace(self.K3), "the build nobody watches ran on and was kept")
        self.assertIsNotNone(s.trace(self.K2))

        # «احسب» for an episode whose build failed: its error, and k5 is cancelled
        self.assertEqual(s.poll(k4)["status"], "loading")
        settle()
        gate.clear()
        self.assertEqual(s.poll(k5, preempt=True)["status"], "loading")
        r = s.poll(k4, preempt=True)
        self.assertEqual((r["status"], r["message"]), ("error", "build failed: ValueError"))
        gate.set()
        settle()
        self.assertIsNone(s.trace(k5), "the build nobody watches ran on and was kept")

    def test_a_superseded_build_that_fails_reports_nothing(self):
        """A build cancelled by «احسب» for another episode that then raises is
        not a failure anyone is waiting for: the next poll of its key starts
        it again instead of spending «احسب» on a stale error. A build that was
        not superseded still reports its failure, once."""
        gate, entered = threading.Event(), threading.Event()

        def fails_after_the_gate(lanes, ep, on_frame):
            entered.set()
            gate.wait(5)
            raise ValueError(r"C:\secret\path must not reach the browser")
        s = self.store(tracer=fails_after_the_gate)
        self.assertEqual(s.poll(self.K1)["status"], "loading")
        self.assertTrue(entered.wait(5), "the tracer never started")
        self.assertEqual(s.poll(self.K2, preempt=True)["status"], "busy")
        gate.set()
        for t in _builders():
            t.join(5)
        self.assertEqual(s.poll(self.K1)["status"], "loading",
                         "a superseded build's failure was reported")
        r = _wait_for(s, self.K1, "error")
        self.assertEqual(r["message"], "build failed: ValueError")
        self.assertNotEqual(s.poll(self.K1)["status"], "error", "an error is reported once")

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
CATALOG_URL = "/api/agents/catalog"
CATALOG_KEYS = {"experiments", "episodes", "preview_s", "act", "limits", "sb3"}


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
                "print(json.dumps({'mods': sorted(m for m in sys.modules if m.startswith(\n"
                "  ('app.agent', 'app.jev', 'app.laya', 'app.model_questions'))),\n"
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

        from fastapi import FastAPI
        app, client = _client(_StubStore())
        paths = {r.path: r for r in app.routes if hasattr(r, "methods")}
        added = set(paths) - {r.path for r in FastAPI().routes}
        posts = {"/api/agents/jev", "/api/agents/laya"}
        self.assertEqual(added, {"/agents", "/api/agents/episode", "/api/agents/catalog",
                                 "/api/agents/jev/status", "/api/agents/laya/status"} | posts)
        for p in sorted(added):
            self.assertEqual(set(paths[p].methods), {"POST"} if p in posts else {"GET"}, p)
        self.assertEqual(client.post(EPISODE_URL).status_code, 405)
        self.assertEqual(client.post(CATALOG_URL).status_code, 405)
        for p in sorted(posts):
            self.assertEqual(client.get(p).status_code, 405, p)

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

    def test_catalog_route_contract(self):
        """GET /api/agents/catalog: every runs*/ directory, the 20 episodes of
        each protocol read from the road the env steps, and the page's
        constants -- JSON-safe, no-store, and never a poll of the store."""
        stub = _StubStore()
        _, client = _client(stub)
        r = client.get(CATALOG_URL)
        self.assertEqual(r.status_code, 200, r.text[:500])
        self.assertEqual(r.headers.get("cache-control"), "no-store")
        body = r.json()
        self.assertEqual(set(body), CATALOG_KEYS)
        json.dumps(body, allow_nan=False)
        self.assertEqual(stub.calls, [], "the catalog must not reach the store")

        self.assertEqual(set(body["episodes"]), {"d2", "phase-d"})
        for protocol, rows in body["episodes"].items():
            with self.subTest(protocol=protocol):
                self.assertEqual([row["idx"] for row in rows], list(range(1, 21)))
                self.assertEqual([row["seed"] for row in rows],
                                 [T.episode(protocol, i)["seed"] for i in range(1, 21)])
                self.assertEqual({k for row in rows for k in row},
                                 {"idx", "seed", "weights", "climb_start_s", "grade"})
        for row in body["episodes"]["phase-d"]:
            self.assertEqual((row["climb_start_s"], row["grade"]), (180.0, 0.12), row["idx"])
        self.assertEqual(body["episodes"]["d2"][0],
                         {"idx": 1, "seed": 1000, "weights": [0.690154, 0.012829, 0.297017],
                          "climb_start_s": 141.0, "grade": 0.13314})
        # the step at which the env's grade begins, not the table's 281.95
        self.assertEqual(body["episodes"]["d2"][1]["climb_start_s"], 281.0)

        self.assertEqual({k: body[k] for k in ("preview_s", "act", "limits")},
                         API.page_constants())
        self.assertEqual(body["preview_s"], list(PREVIEW_S))
        self.assertEqual(body["act"]["neutral_phys"], [0.0, 0.0, 0.0, 1.0, 1.0])
        self.assertEqual(body["act"]["lo"], [float(x) for x in ACT_LO])
        self.assertEqual(body["limits"]["turb_c"], round(TURB_PROTECT_K - 273.15, 1))
        self.assertEqual([e["runs"] for e in body["experiments"]],
                         [e["runs"] for e in AC.discover()])

        self.assertIs(body["sb3"], True, "a store with an injected loader needs no SB3")
        stub.needs_sb3 = True
        with mock.patch.object(AC, "discover", lambda root=AC.ROOT: []):
            with mock.patch.object(API, "sb3_available", lambda: False):
                self.assertIs(client.get(CATALOG_URL).json()["sb3"], False)
            with mock.patch.object(API, "sb3_available", lambda: True):
                self.assertIs(client.get(CATALOG_URL).json()["sb3"], True)

    def test_catalog_failure_is_500_no_store(self):
        """Anything unexpected is a fixed text naming the exception's class:
        never str(exc), which can carry a path."""
        _, client = _client(_StubStore())
        secret = r"C:\secret\runs_zz\sighted_seed0\meta.json"
        with mock.patch.object(AC, "discover", side_effect=OSError(secret)):
            r = client.get(CATALOG_URL)
        self.assertEqual(r.status_code, 500)
        self.assertEqual(r.headers.get("cache-control"), "no-store")
        self.assertEqual(r.json(), {"detail": "catalog failed: OSError"})
        self.assertNotIn("secret", r.text)

    def test_catalog_failure_inside_discover_is_500_no_store(self):
        """The same fixed text when the error is raised INSIDE the real
        discover: a results file that is not UTF-8 fails in
        analyse_phase_d.parse, reached through discover -> table_rows ->
        analyse_phase_d2.load. discover walks a temporary root holding one
        empty runs_d2/, so this runs on a clone where the gitignored runs*/
        directories are absent; load still reads the repository's own
        tracked results/d2_seed*.txt, which is what reaches parse."""
        import analyse_phase_d2
        self.assertTrue(sorted((ROOT / "results").glob("d2_seed*.txt")),
                        "no results/d2_seed*.txt: parse would never be reached")
        real_discover = AC.discover
        secret = r"C:\secret\runs_zz\sighted_seed0\meta.json"
        bad = UnicodeDecodeError("utf-8", bytes([0xFF]), 0, 1, secret)
        _, client = _client(_StubStore())
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "runs_d2").mkdir()
            with mock.patch.object(AC, "discover", lambda root=AC.ROOT: real_discover(tmp)), \
                    mock.patch.object(analyse_phase_d2, "parse", side_effect=bad) as parse:
                r = client.get(CATALOG_URL)
        self.assertTrue(parse.called, "the error must come through the real discover chain")
        self.assertEqual(r.status_code, 500)
        self.assertEqual(r.headers.get("cache-control"), "no-store")
        self.assertEqual(r.json(), {"detail": "catalog failed: UnicodeDecodeError"})
        self.assertNotIn("secret", r.text)

    @unittest.skipUnless(HAVE_ALL_RUNS, NO_ALL_RUNS)
    def test_episode_route_serves_phase_d_and_d2(self):
        """Phase D and D2 pairs run through the same route as C4. Phase D's
        episode reads its grade off the road the env steps: 0.12 at 180 s,
        so the SIMULATED badge reads 12.0, not a dash."""
        stub = _StubStore()
        _, client = _client(stub)
        seed, weights = EPISODES[0]
        r = client.get("/api/agents/episode?runs=runs&seed=0&ep=1&since=0&preempt=1")
        self.assertEqual(r.status_code, 200, r.text[:500])
        self.assertEqual(r.headers.get("cache-control"), "no-store")
        body = r.json()
        meta = body["meta"]
        self.assertEqual(set(meta), META_KEYS)
        json.dumps(meta, allow_nan=False)
        self.assertEqual((meta["prefix"], meta["experiment"], meta["protocol"]),
                         ("phase_d", "Phase D", "phase-d"))
        self.assertEqual(meta["episode"], {"seed": seed, "weights": list(weights),
                                           "climb_start_s": 180.0, "grade": 0.12})
        self.assertEqual(body["road"]["climb_start_s"], 180.0)
        self.assertEqual(meta["verdict"]["state"], "found", meta["verdict"]["missing"])
        self.assertEqual(meta["verdict"]["short"],
                         {k: AC.SHORT_VERDICT["phase_d"][k] for k in ("ar", "en")})
        self.assertEqual([a["scored"] for a in meta["agents"]], ["not recorded"] * 2)
        self.assertTrue(meta["result_file"])

        seed, weights, start_s, grade = EPISODES_D2[6]
        r = client.get("/api/agents/episode?runs=runs_d2&seed=3&ep=7&since=0&preempt=1")
        self.assertEqual(r.status_code, 200, r.text[:500])
        meta = r.json()["meta"]
        self.assertEqual((meta["prefix"], meta["experiment"], meta["protocol"]),
                         ("d2", "Phase D2", "d2"))
        self.assertEqual(meta["episode"], {"seed": 1006, "weights": list(weights),
                                           "climb_start_s": 247.0, "grade": grade})
        self.assertEqual(grade, 0.15802)
        self.assertEqual(stub.calls, [(("runs", 0, 1), 0, True), (("runs_d2", 3, 7), 0, True)])

    def test_episode_route_unexpected_error_is_500_no_store(self):
        """An exception the route did not expect is a 500 with a fixed text and
        no-store (M1 left it to FastAPI's default 500, with no no-store). The
        road and the meta are built BEFORE the store is polled, so a request
        that fails never starts a build."""
        secret = r"C:\secret\runs_c4\blind_seed5\final.zip"
        pair = {"runs": "runs_c4", "seed": 5, "prefix": "c4", "experiment": "C4",
                "protocol": "d2", "result_file": False, "agents": [], "problems": []}

        def get(stub):
            _, client = _client(stub)
            return client.get(EPISODE_URL + "&since=0&preempt=1")
        answered = []
        stub = _StubStore()
        with mock.patch.object(AC, "find_pair", side_effect=RuntimeError(secret)):
            answered.append(("find_pair", get(stub), stub))
        stub = _StubStore()
        with mock.patch.object(AC, "find_pair", return_value=pair), \
                mock.patch.object(API, "episode_meta", side_effect=RuntimeError(secret)):
            answered.append(("episode_meta", get(stub), stub))
        for name, r, stub in answered:
            with self.subTest(fails=name):
                self.assertEqual(r.status_code, 500)
                self.assertEqual(r.headers.get("cache-control"), "no-store")
                self.assertEqual(r.json(), {"detail": "server error: RuntimeError"})
                self.assertNotIn("secret", r.text)
                self.assertEqual(stub.calls, [], "a request that failed started a build")


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


NEW_MODULES = ("agent_trace.py", "agent_catalog.py", "agent_api.py", "model_questions.py",
               "jev.py", "laya_worker.py", "laya_bridge.py")
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
# M3 (design 7.4, 7.5 and section 9 row 13): jev.py may import any network module;
# laya_worker.py may import socket only, to refuse it. The scan still reads every
# app/*.py, the allowed ones included.
NET_ALLOWED = {"jev.py": NET_ROOTS, "laya_worker.py": {"socket"}}


def _net_hits(name, source):
    """'name:line root' for each network import in `source` that NET_ALLOWED does not give `name`."""
    allowed = NET_ALLOWED.get(name, set())
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            roots = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            roots = [(node.module or "").split(".")[0]]
        else:
            continue
        found += [f"{name}:{node.lineno} {r}" for r in roots
                  if r in NET_ROOTS and r not in allowed]
    return found


class NoNetworkTests(unittest.TestCase):
    """Spec test 13: an AST import scan, so 'WebSocket' in server.py is not a hit."""

    def test_the_scan_sees_urllib_in_the_worker(self):
        """The worker is allowed socket, and nothing else in NET_ROOTS."""
        self.assertEqual(_net_hits("laya_worker.py", "import urllib\n"), ["laya_worker.py:1 urllib"])
        self.assertEqual(_net_hits("laya_worker.py", "import socket\n"), [])

    def test_no_network_imports_in_app(self):
        found = []
        for path in sorted((ROOT / "app").glob("*.py")):
            if not path.name.startswith("test_"):
                found += _net_hits(path.name, path.read_text(encoding="utf-8"))
        self.assertEqual(found, [])

    def test_the_scan_still_reads_allowed_files(self):
        self.assertEqual(_net_hits("jev.py", "import urllib.request\nimport http.client\n"), [])
        self.assertEqual(_net_hits("agent_api.py", "import json\nfrom urllib import request\n"),
                         ["agent_api.py:2 urllib"])
        self.assertEqual(_net_hits("model_questions.py", "import socket\n"),
                         ["model_questions.py:1 socket"])


# ---- M3: the one question both models are asked (app/model_questions.py) ----
#
# Spec tests 14 and 15. _obs_trace() is a real agent_api.Trace built without an
# agent: D2 episode 1 stepped with neutral_action(), sighted and blind, exactly
# as agent_trace.run_lanes builds, resets and pins its envs.

_OBS_TRACES = {}


def _obs_trace(n=8):
    """A Trace for ('runs_c4', 5, 1) holding n real observation rows per lane; cached by n."""
    if n not in _OBS_TRACES:
        ep = T.episode("d2", 1)
        lanes = []
        for use_preview in (True, False):
            env = SupervisoryTunerEnv(T.build_cycle(ep), dt=T.DT, seed=ep["seed"],
                                      use_preview=use_preview)
            env.reset(seed=ep["seed"])
            env.w = np.asarray(ep["weights"], dtype=np.float32)
            obs, rows = env._obs(), []
            for _ in range(n):
                rows.append(np.array(obs, dtype=np.float32, copy=True))
                obs = env.step(neutral_action())[0]
            lanes.append(np.stack(rows))
        _OBS_TRACES[n] = API.Trace(("runs_c4", 5, 1),
                                   [{"k": k, "cars": [None, None]} for k in range(n)],
                                   [], lanes, "cpu", {})
    return _OBS_TRACES[n]


def _model_answer(pick=1):
    """A model-shaped answer: KEYS[qid][pick] chosen with p 0.6, the probabilities
    listed in REVERSED order, and the three fields to_action must drop."""
    out = {}
    for qid in MQ.IDS:
        keys = list(MQ.KEYS[qid])
        probs = {k: (0.6 if j == pick else 0.1) for j, k in enumerate(keys)}
        out[qid] = {"choice": keys[pick], "probabilities": dict(reversed(list(probs.items()))),
                    "confidence": 0.93, "answer_confidence": 0.6, "action": "ignored"}
    return out


def _with(qid, **change):
    """_model_answer() with one question's fields changed (a value of None deletes it)."""
    out = _model_answer()
    for field, value in change.items():
        if value is None:
            del out[qid][field]
        else:
            out[qid][field] = value
    return out


def _with_p(value, qid="spark_trim", key="no change"):
    """_model_answer() with one probability replaced."""
    out = _model_answer()
    out[qid]["probabilities"][key] = value
    return out


class QuestionTests(unittest.TestCase):
    """Spec test 14: the five questions, their levels, and answers become actions."""

    NEUTRAL_COL = (2, 2, 2, 4, 4)
    NAMED = ((-8.0, -4.0, 0.0, 2.0, 4.0),
             (-0.15, -0.075, 0.0, 0.03, 0.06),
             (-40.0, -20.0, 0.0, 7.5, 15.0),
             (0.0, 0.25, 0.5, 0.75, 1.0),
             (0.3, 0.475, 0.65, 0.825, 1.0))

    def test_levels_and_net(self):
        neutral = np.asarray(API.page_constants()["act"]["neutral_phys"], dtype=np.float32)
        env = SupervisoryTunerEnv(make_grade_climb(), dt=1.0)
        for table in (MQ.LEVELS, MQ.NET):
            self.assertEqual((table.dtype, table.shape), (np.float32, (5, 5)))
        np.testing.assert_allclose(MQ.LEVELS, np.asarray(self.NAMED), atol=1e-6,
                                   err_msg="a level is not the one its key names")
        for i, qid in enumerate(MQ.IDS):
            with self.subTest(action=qid):
                row = MQ.LEVELS[i]
                self.assertTrue(np.all(np.diff(row) > 0), row)
                self.assertEqual((row[0], row[-1]), (ACT_LO[i], ACT_HI[i]))
                j = self.NEUTRAL_COL[i]
                self.assertEqual(row[j], neutral[i])
                self.assertEqual(MQ.NET[i, j].tobytes(), neutral_action()[i].tobytes())
        for j in range(5):
            err = np.max(np.abs(env._rescale(MQ.NET[:, j]) - MQ.LEVELS[:, j]))
            self.assertLessEqual(float(err), 1e-6, f"column {j}")
        self.assertTrue(np.all((MQ.NET >= -1.0) & (MQ.NET <= 1.0)))

    def test_questions_and_options(self):
        for questions in (MQ.QUESTIONS, MQ.QUESTIONS_REVERSED):
            self.assertEqual(tuple(questions), MQ.IDS)
            for qid, q in questions.items():
                with self.subTest(qid=qid):
                    self.assertEqual(set(q), {"type", "instructions", "criteria"})
                    self.assertEqual(q["type"], "choice", "a score question is never asked")
                    self.assertIn("`task`", q["instructions"])
                    self.assertEqual(len(q["criteria"]), 5)
                    self.assertTrue(all(key.isascii() for key in q["criteria"]), "C12")
        self.assertTrue(json.dumps(MQ.QUESTIONS, ensure_ascii=False).isascii())
        self.assertIn("ceiling", MQ.QUESTIONS["boost_ceiling"]["instructions"])
        for qid in MQ.IDS:
            with self.subTest(qid=qid):
                fwd, rev = MQ.QUESTIONS[qid], MQ.QUESTIONS_REVERSED[qid]
                self.assertEqual(fwd["instructions"], MQ.INSTRUCTIONS[qid])
                self.assertEqual(list(fwd["criteria"]), list(MQ.KEYS[qid]))
                self.assertEqual(list(fwd["criteria"].values()), list(MQ.DESCRIPTIONS[qid]))
                self.assertEqual(MQ.OPTIONS[qid], {key: j for j, key in enumerate(MQ.KEYS[qid])})
                self.assertEqual(len(set(MQ.OPTIONS[qid].values())), 5)
                self.assertEqual(rev["instructions"], fwd["instructions"])
                self.assertEqual(list(rev["criteria"].items()),
                                 list(reversed(list(fwd["criteria"].items()))))
        self.assertIsNot(MQ.QUESTIONS_REVERSED, MQ.QUESTIONS)

    def test_to_action(self):
        got = MQ.to_action(_model_answer(pick=1))
        self.assertEqual(tuple(got), MQ.IDS)
        for i, qid in enumerate(MQ.IDS):
            with self.subTest(qid=qid):
                a = got[qid]
                self.assertEqual(set(a), {"choice", "level_phys", "level_net", "probabilities",
                                          "chosen_p", "options"})
                self.assertEqual(a["choice"], MQ.KEYS[qid][1])
                self.assertEqual(list(a["probabilities"]), list(MQ.KEYS[qid]), "KEYS order")
                self.assertEqual(a["chosen_p"], a["probabilities"][a["choice"]])
                self.assertEqual(a["chosen_p"], 0.6)
                self.assertEqual(a["level_phys"], float(MQ.LEVELS[i, 1]))
                self.assertEqual(a["level_net"], float(MQ.NET[i, 1]))
                self.assertEqual(a["options"], [{"key": k, "level_phys": float(MQ.LEVELS[i, j])}
                                                for j, k in enumerate(MQ.KEYS[qid])])
        json.dumps(got, allow_nan=False)
        extra = _model_answer(pick=1)
        extra["drive_the_car"] = {"choice": "yes"}
        self.assertEqual(MQ.to_action(extra), got, "an extra id is dropped")
        whole = _model_answer()
        whole["spark_trim"]["probabilities"] = {k: (1 if k == "retard 4 deg" else 0)
                                                for k in MQ.KEYS["spark_trim"]}
        self.assertEqual(MQ.to_action(whole)["spark_trim"]["chosen_p"], 1.0)

        cases = {
            "answers None": None,
            "answers a list": [],
            "an id missing": {k: v for k, v in _model_answer().items() if k != "cooling_fan"},
            "an id not an object": {**_model_answer(), "cooling_fan": "fan 50 %"},
            "a choice outside the options": _with("spark_trim", choice="retard 5 deg"),
            "a choice that is not a string": _with("spark_trim", choice=1),
            "no choice": _with("spark_trim", choice=None),
            "no probabilities": _with("spark_trim", probabilities=None),
            "probabilities a list": _with("spark_trim", probabilities=[0.2] * 5),
            "a probability missing": _with("spark_trim", probabilities={
                k: 0.25 for k in MQ.KEYS["spark_trim"] if k != "no change"}),
            "an extra probability": _with("spark_trim", probabilities={
                **{k: 0.2 for k in MQ.KEYS["spark_trim"]}, "retard 5 deg": 0.0}),
            "NaN": _with_p(float("nan")),
            "infinity": _with_p(float("inf")),
            "above one": _with_p(1.5),
            "below zero": _with_p(-0.1),
            "a bool": _with_p(True),
            "a string": _with_p("0.2"),
            "null": _with_p(None),
        }
        for why, answers in cases.items():
            with self.subTest(why=why):
                with self.assertRaises(MQ.BadAnswer) as caught:
                    MQ.to_action(answers)
                self.assertNotIn("retard 5 deg", str(caught.exception),
                                 "a BadAnswer carries no text from the answer")
        self.assertTrue(issubclass(MQ.BadAnswer, ValueError))


MODEL_MODULES = ("model_questions.py", "jev.py", "laya_worker.py", "laya_bridge.py")
RECORDED_DRIVE = ("app.replay", "app.reader", "app.estimator")


def _imports(source):
    """Every module a source imports, dotted: `from app import x` counts as app.x."""
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                base = "app" + ("." + base if base else "")
            names.add(base)
            names.update(f"{base}.{a.name}" for a in node.names)
    return names


def _recorded_drive(source):
    """The RECORDED_DRIVE modules a source imports, or anything inside them."""
    found = _imports(source)
    return sorted(r for r in RECORDED_DRIVE
                  if any(m == r or m.startswith(r + ".") for m in found))


class StateTests(unittest.TestCase):
    """Spec test 15: the state is the sighted agent's own observation, and nothing else."""

    def test_decode_is_the_observation(self):
        ep = T.episode("d2", 1)
        env = SupervisoryTunerEnv(T.build_cycle(ep), dt=T.DT, seed=ep["seed"])
        env.reset(seed=ep["seed"])
        env.w = np.asarray(ep["weights"], dtype=np.float32)
        checked = []
        for k in range(201):
            if k in (0, 1, 50, 150, 200):
                got = MQ.decode(env._obs())
                t, c = env.thermal.state(), env.cycle
                want = {
                    "engine_speed_rpm": (env.rpm, 1),
                    "manifold_pressure_kPa": (env.map_kpa, 2),
                    "throttle_fraction": (env.tps, 4),
                    "spark_advance_deg_BTDC": (env.spark, 2),
                    "lambda": (env.lam, 4),
                    "engine_block_C": (t[0] - 273.15, 2),
                    "oil_C": (t[1] - 273.15, 2),
                    "turbine_housing_C": (t[2] - 273.15, 1),
                    "charge_air_C": (env.iat_k - 273.15, 2),
                    "ambient_C": (c["t_amb"] - 273.15, 2),
                    "barometric_kPa": (c.get("p_baro", 101.3), 2),
                    "humidity_kg_per_kg": (c.get("humidity", 0.01), 5),
                    "road_speed_kmh": (env.v * 3.6, 2),
                    "grade_now_percent": (c["grade"][env.k] * 100.0, 3),
                    "torque_requested_Nm": (env.torque_req, 1),
                    "driver_aggression_0_to_1": (env.aggression, 4),
                }
                for i, h in enumerate(PREVIEW_S):
                    want[("grade_ahead_percent", f"in_{h:g}_s")] = (env._preview()[i] * 100.0, 3)
                for i, name in enumerate(("deliver_torque", "save_fuel", "protect_components")):
                    want[("priorities", name)] = (env.w[i], 4)
                for name, (value, digits) in want.items():
                    field = got[name[0]][name[1]] if isinstance(name, tuple) else got[name]
                    with self.subTest(k=k, field=name):
                        self.assertLessEqual(abs(field - float(value)), 10.0 ** -digits)
                self.assertEqual(got["note"], MQ.NOTE)
                json.dumps(got, allow_nan=False)
                checked.append(k)
            if k == 200:
                break
            env.step(neutral_action())
        self.assertEqual(checked, [0, 1, 50, 150, 200])
        for bad in (np.zeros(22, dtype=np.float32), np.zeros((1, 23), dtype=np.float32),
                    np.full(23, np.nan, dtype=np.float32)):
            with self.subTest(bad=bad.shape):
                with self.assertRaises(ValueError):
                    MQ.decode(bad)

    def test_state_carries_the_task_and_refuses_browser_state(self):
        trace = _obs_trace()
        state = MQ.build_state(trace, 3)
        self.assertEqual(state, {"engine": MQ.decode(trace.obs[0][3]), "task": MQ.TASK})
        # At second 3 the two lanes still see the same road, so pin the lane directly.
        other = API.Trace(trace.key, trace.frames, [],
                          [trace.obs[0], np.zeros_like(trace.obs[1])], "cpu", {})
        self.assertEqual(MQ.build_state(other, 3), state, "the SIGHTED lane's view, obs[0]")
        self.assertIn(f"{TURB_PROTECT_K - 273.15:.0f} °C", MQ.TASK)
        self.assertIn(f"{OIL_PROTECT_K - 273.15:.0f} °C", MQ.TASK)
        engine = state["engine"]
        self.assertEqual(list(engine["grade_ahead_percent"]), [f"in_{h:g}_s" for h in PREVIEW_S])
        self.assertEqual(list(engine["priorities"]),
                         ["deliver_torque", "save_fuel", "protect_components"])
        for got, weight in zip(engine["priorities"].values(), T.episode("d2", 1)["weights"]):
            self.assertAlmostEqual(got, weight, delta=1e-4)
        json.dumps(state, allow_nan=False)
        for bad in ({"obs": trace.obs}, list(trace.obs), None,
                    type("Lookalike", (), {"obs": trace.obs})()):
            with self.subTest(bad=type(bad).__name__):
                with self.assertRaises(TypeError):
                    MQ.build_state(bad, 3)

    def test_no_recorded_drive_imports(self):
        for name in MODEL_MODULES:
            with self.subTest(module=name):
                source = (ROOT / "app" / name).read_text(encoding="utf-8")
                self.assertEqual(_recorded_drive(source), [])
        probe = "from app import replay\nfrom app.reader import X\nimport app.estimator\n"
        self.assertEqual(_recorded_drive(probe), ["app.estimator", "app.reader", "app.replay"],
                         "the scan must be able to fail")


class UserSettingTests(unittest.TestCase):
    """model_questions.user_setting: the environment first, then a file OUTSIDE the repository."""

    def test_env_wins_and_is_never_a_path(self):
        self.assertEqual(Path.cwd().resolve(), ROOT, "run the suite from the repository root")
        with tempfile.TemporaryDirectory() as appdata:
            (Path(appdata) / "grad-project").mkdir()
            (Path(appdata) / "grad-project" / "typesafe_key").write_text("filekey\n",
                                                                         encoding="utf-8")
            env = {"TYPESAFE_API_KEY": "sentinel-key", "APPDATA": appdata}
            self.assertEqual(MQ.user_setting("TYPESAFE_API_KEY", "typesafe_key", env),
                             ("sentinel-key", "env"))
        # a value is never resolved: one that names a repository file is still just a value
        self.assertEqual(MQ.user_setting("X", "x", {"X": "app/server.py"}), ("app/server.py", "env"))
        self.assertEqual(MQ.user_setting("X", "x", {"X": "  padded \n"}), ("padded", "env"))
        self.assertEqual(MQ.user_setting("X", "x", {"X": "   "}), (None, None))
        with mock.patch.dict(os.environ, {"GRAD_M3_SETTING_PROBE": "from-os-environ"}):
            self.assertEqual(MQ.user_setting("GRAD_M3_SETTING_PROBE", "x"),
                             ("from-os-environ", "env"))

    def test_file_outside_is_read_and_a_file_inside_the_repository_is_refused(self):
        with tempfile.TemporaryDirectory() as appdata:
            self.assertNotIn(ROOT, Path(appdata).resolve().parents)
            folder = Path(appdata) / "grad-project"
            folder.mkdir()
            (folder / "typesafe_key").write_text("filekey\n", encoding="utf-8")
            (folder / "blank").write_text("  \n", encoding="utf-8")
            env = {"APPDATA": appdata}
            self.assertEqual(MQ.user_setting("TYPESAFE_API_KEY", "typesafe_key", env),
                             ("filekey", "file"))
            self.assertEqual(MQ.user_setting("TYPESAFE_API_KEY", "blank", env), (None, None))
            self.assertEqual(MQ.user_setting("TYPESAFE_API_KEY", "missing", env), (None, None))
        # <ROOT>/grad-project/../app/server.py resolves to app/server.py, which exists and
        # reads; only the repository check can refuse it.
        self.assertTrue((ROOT / "app" / "server.py").is_file())
        self.assertEqual(MQ.user_setting("TYPESAFE_API_KEY", "../app/server.py",
                                         {"APPDATA": str(ROOT)}), (None, None))
        self.assertEqual(MQ.user_setting("TYPESAFE_API_KEY", "typesafe_key", {}), (None, None))

    def test_a_file_as_windows_writes_it(self):
        # Windows PowerShell 5.1 writes UTF-16 LE with a byte-order mark for `>` and
        # Out-File, and UTF-8 with a mark under -Encoding utf8 (this machine's profile
        # makes that its default); Notepad can write UTF-16 BE. Measured 28 Sep: a plain
        # UTF-8 read kept the mark in the value and read the UTF-16 file as no file.
        mark, key, home = chr(0xFEFF), "sentinel-key", r"C:\Some Folder\laya"
        read = {
            "utf8_mark": ((key + "\r\n").encode("utf-8-sig"), key),
            "utf16le_mark": ((mark + key + "\r\n").encode("utf-16-le"), key),
            "utf16be_mark": ((mark + key + "\r\n").encode("utf-16-be"), key),
            "home_utf16le_mark": ((mark + home + "\r\n").encode("utf-16-le"), home),
            "home_utf8_mark": ((home + "\r\n").encode("utf-8-sig"), home),
        }
        # UTF-16 with no mark reads as UTF-8 with a NUL after every letter, and UTF-32
        # LE's mark begins with UTF-16 LE's: neither may become a value, and nor may a
        # second line.
        refused = {
            "utf16le_no_mark": key.encode("utf-16-le"),
            "utf32le_mark": (mark + key).encode("utf-32-le"),
            "two_lines": (key + "\r\n" + key + "\r\n").encode("utf-8"),
        }
        with tempfile.TemporaryDirectory() as appdata:
            folder = Path(appdata) / "grad-project"
            folder.mkdir()
            for name, (data, _) in read.items():
                (folder / name).write_bytes(data)
            for name, data in refused.items():
                (folder / name).write_bytes(data)
            env = {"APPDATA": appdata}
            for name, (_, want) in read.items():
                self.assertEqual(MQ.user_setting("M3_UNSET", name, env), (want, "file"), name)
            for name in refused:
                self.assertEqual(MQ.user_setting("M3_UNSET", name, env), (None, None), name)


# ---- M3: jev (app/jev.py), always through a fake send ----------------------
#
# Spec test 17. NO TEST HERE CALLS jev._send OR OPENS A SOCKET: every ask()
# gets a _FakeSend, and there is no key on this machine.

SENTINEL_KEY = "sentinel-key-M3"


@contextlib.contextmanager
def _jev_key(key):
    """os.environ holding this jev key (None: no key at all), with an APPDATA
    that holds no key file, so the machine's own settings never leak in."""
    with tempfile.TemporaryDirectory() as appdata, \
            mock.patch.dict(os.environ, {"APPDATA": appdata}):
        os.environ.pop("TYPESAFE_API_KEY", None)
        if key is not None:
            os.environ["TYPESAFE_API_KEY"] = key
        yield


class _FakeSend:
    """jev._send's stand-in: records (body, key) per call, then returns
    (status, payload) or raises `exc`."""

    def __init__(self, status=200, payload=None, exc=None):
        self.calls = []
        self.status, self.exc = status, exc
        self.payload = payload if payload is not None else json.dumps(
            {"model": "jev-1.13.0", "answers": _model_answer()}).encode("utf-8")

    def __call__(self, body, key, timeout=None):
        self.calls.append((body, key))
        if self.exc is not None:
            raise self.exc
        return self.status, self.payload


class _Records(logging.Handler):
    """Every root-logger record, kept in memory."""

    def __init__(self):
        super().__init__(logging.DEBUG)
        self.records = []

    def emit(self, record):
        self.records.append(record)


class _JevCase(unittest.TestCase):
    """Makes the real network unreachable while a jev test runs: a test that
    reached jev's opener (the one way _send sends) or urllib.request.urlopen by
    mistake fails here, before any byte is sent."""

    def setUp(self):
        for owner, name in ((JEV._OPENER, "open"), (JEV.urllib.request, "urlopen")):
            guard = mock.patch.object(owner, name, side_effect=AssertionError(
                f"a jev test reached {name}(): tests use a fake send only"))
            guard.start()
            self.addCleanup(guard.stop)


class JevTests(_JevCase):
    """Spec test 17: one call per press, every failure a fixed code, nothing substituted."""

    def ask_fails(self, send, **kw):
        """The JevError ask() raises with a key present; asserts exactly one call."""
        with _jev_key(SENTINEL_KEY):
            with self.assertRaises(JEV.JevError) as caught:
                JEV.ask(_obs_trace(), 3, send=send, **kw)
        self.assertEqual(len(send.calls), 1, "one call per press, never a retry")
        return caught.exception

    def test_request_is_the_shared_question(self):
        trace = _obs_trace()
        body = JEV.build_request(trace, 3)
        self.assertEqual(set(body), {"model", "state", "questions"})
        self.assertEqual(body["model"], "jev-latest")
        self.assertIs(body["questions"], MQ.QUESTIONS)
        self.assertEqual(body["state"], MQ.build_state(trace, 3))
        with _jev_key(SENTINEL_KEY):
            self.assertNotIn(SENTINEL_KEY, json.dumps(JEV.build_request(trace, 3)))
        self.assertEqual((JEV.URL, JEV.MODEL, JEV.TIMEOUT_S),
                         ("https://api.typesafe.ai/v1/systemone", "jev-latest", 10.0))

    def test_named_vendor_statuses(self):
        want = {401: "key_rejected", 403: "vendor_refused", 422: "request_rejected",
                429: "rate_limited", 529: "overloaded"}
        self.assertEqual(JEV.STATUS_CODES, want)
        for status, code in want.items():
            with self.subTest(status=status):
                err = self.ask_fails(_FakeSend(status=status, payload=b""))
                self.assertEqual((err.code, err.status), (code, None))

    def test_other_statuses_are_vendor_status_with_only_the_integer(self):
        # 302 is a real reply too: jev's opener refuses every redirect
        # (JevKeyTests.test_a_redirect_is_never_followed), so _send returns it.
        for status in (402, 500, 503, 302):
            with self.subTest(status=status):
                err = self.ask_fails(_FakeSend(status=status, payload=b"sentinel-body no credit"))
                self.assertEqual((err.code, err.status), ("vendor_status", status))
                self.assertIs(type(err.status), int)
                self.assertEqual(err.args, ("vendor_status",))
                seen = repr(err) + str(err) + json.dumps(vars(err))
                self.assertNotIn("sentinel-body", seen)

    def test_network_and_timeout(self):
        for exc, code in ((URLError("down"), "network"), (ConnectionResetError(), "network"),
                          (TimeoutError(), "timeout"), (URLError(TimeoutError()), "timeout")):
            with self.subTest(exc=repr(exc)):
                err = self.ask_fails(_FakeSend(exc=exc))
                self.assertEqual((err.code, err.status), (code, None))

    def test_malformed_answers_are_bad_answer(self):
        def reply(answers):
            return json.dumps({"model": "jev-1.13.0", "answers": answers}).encode("utf-8")

        def one(qid, **change):
            answers = _model_answer()
            answers[qid].update(change)
            return reply(answers)

        payloads = {
            "not JSON": b"not json",
            "not UTF-8": bytes([0xFF, 0xFE]),
            "a JSON list": b"[]",
            "no answers": b"{}",
            "empty answers": reply({}),
            "a choice outside the options": one("spark_trim", choice="retard 5 deg"),
            "a probability missing": one("spark_trim", probabilities={
                k: 0.25 for k in MQ.KEYS["spark_trim"] if k != "no change"}),
            "a NaN probability": one("lambda_trim", probabilities={
                k: float("nan") for k in MQ.KEYS["lambda_trim"]}),
            "a probability of 1.5": one("cooling_fan", probabilities={
                k: 1.5 for k in MQ.KEYS["cooling_fan"]}),
            "a probability of true": one("coolant_pump", probabilities={
                k: True for k in MQ.KEYS["coolant_pump"]}),
            "a score-shaped answer": reply({**_model_answer(), "boost_ceiling": {"score": 0.5}}),
        }
        for why, payload in payloads.items():
            with self.subTest(why=why):
                err = self.ask_fails(_FakeSend(payload=payload))
                self.assertEqual((err.code, err.status), ("bad_answer", None))

    def test_a_reply_the_parser_cannot_hold_is_bad_answer(self):
        # Measured 29 Sep: a 400-digit integer makes to_action's isfinite raise
        # OverflowError, and deep nesting makes json.loads raise RecursionError.
        # Neither is a ValueError; both are the vendor's reply, so both are bad_answer.
        huge = json.dumps({"model": "jev-1.13.0", "answers": _model_answer()}).replace(
            "0.6", "1" + "0" * 400, 1).encode("utf-8")
        payloads = {"a 400-digit probability": huge,
                    "nesting 100 000 deep": b"[" * 100_000 + b"]" * 100_000}
        for why, payload in payloads.items():
            with self.subTest(why=why):
                err = self.ask_fails(_FakeSend(payload=payload))
                self.assertEqual((err.code, err.status), ("bad_answer", None))

    def test_no_key_sends_nothing(self):
        send = _FakeSend()
        with _jev_key(None):
            with self.assertRaises(JEV.JevError) as caught:
                JEV.ask(_obs_trace(), 3, send=send)
        self.assertEqual((caught.exception.code, caught.exception.status), ("no_key", None))
        self.assertEqual(send.calls, [], "no key: nothing is sent")

    def test_an_answer(self):
        ticks = iter([1.0, 1.0873])
        send = _FakeSend(payload=json.dumps({"model": "jev-1.13.0",
                                             "answers": _model_answer(pick=2)}).encode("utf-8"))
        with _jev_key(SENTINEL_KEY):
            got = JEV.ask(_obs_trace(), 3, send=send, clock=lambda: next(ticks))
        self.assertEqual(set(got), {"model_name", "ms", "answers", "sent"})
        self.assertEqual(got["ms"], 87.3)
        self.assertEqual(got["model_name"], "jev-1.13.0")
        self.assertEqual(got["answers"], MQ.to_action(_model_answer(pick=2)))
        self.assertEqual(got["sent"], JEV.build_request(_obs_trace(), 3))
        self.assertEqual(send.calls, [(got["sent"], SENTINEL_KEY)], "the key goes to send only")
        for name in ("x" * 65, 7, None):
            with self.subTest(model=name):
                send = _FakeSend(payload=json.dumps({"model": name,
                                                     "answers": _model_answer()}).encode("utf-8"))
                with _jev_key(SENTINEL_KEY):
                    self.assertIsNone(JEV.ask(_obs_trace(), 3, send=send)["model_name"])


class JevKeyTests(_JevCase):
    """Spec test 17: the key is read on each call and appears only where send puts it."""

    def test_the_key_never_leaks(self):
        cases = {
            "a network error naming the key": _FakeSend(exc=URLError(f"boom {SENTINEL_KEY}")),
            "a reset naming the key": _FakeSend(exc=ConnectionResetError(f"reset {SENTINEL_KEY}")),
            "a timeout naming the key": _FakeSend(exc=TimeoutError(f"slow {SENTINEL_KEY}")),
            "a 401 echoing the key": _FakeSend(status=401, payload=SENTINEL_KEY.encode("utf-8")),
            "an answer": _FakeSend(),
        }
        handler, root = _Records(), logging.getLogger()
        level = root.level
        root.addHandler(handler)
        root.setLevel(logging.DEBUG)
        try:
            for why, send in cases.items():
                with self.subTest(why=why), _jev_key(SENTINEL_KEY), \
                        contextlib.redirect_stderr(io.StringIO()) as stderr:
                    try:
                        seen = json.dumps(JEV.ask(_obs_trace(), 3, send=send))
                    except JEV.JevError as err:
                        seen = (json.dumps(vars(err)) + repr(err)
                                + "".join(traceback.format_exception(err)))
                    self.assertEqual([key for _, key in send.calls], [SENTINEL_KEY])
                    self.assertNotIn(SENTINEL_KEY, seen)
                    self.assertNotIn(SENTINEL_KEY, stderr.getvalue())
        finally:
            root.removeHandler(handler)
            root.setLevel(level)
        logged = " ".join(f"{r.getMessage()} {r.exc_text or ''}" for r in handler.records)
        self.assertNotIn(SENTINEL_KEY, logged)

    def test_a_redirect_is_never_followed(self):
        # Measured 29 Sep, offline: urllib's default opener answers a 301, 302 or
        # 303 to jev's POST with a GET to the Location, http:// included, and
        # carries the Authorization header along: the key to another host, and a
        # second request for one press. jev's opener refuses every redirect, so
        # the reply stays HTTPError(code), which _send makes (code, b'') and ask
        # vendor_status. No socket: http.client's connections are a recorder here.
        sent = []

        class Connection:
            """http.client.HTTP(S)Connection's stand-in: records (host, method,
            Authorization), then fails before any socket exists."""

            def __init__(self, host, timeout=None, **kw):
                self.host = host

            def set_debuglevel(self, level):
                pass

            def request(self, method, url, body=None, headers=None, **kw):
                sent.append((self.host, method, (headers or {}).get("Authorization")))
                raise OSError("a test has no socket")

            def close(self):
                pass

        def outcome(opener, code, location):
            """(what `opener` makes of this reply to jev's POST, the requests it then sent)."""
            sent.clear()
            request = urllib.request.Request(JEV.URL, data=b"{}", method="POST",
                                             headers={"Authorization": f"Bearer {SENTINEL_KEY}"})
            request.timeout = JEV.TIMEOUT_S           # what OpenerDirector.open sets
            fields = http.client.HTTPMessage()
            fields["Location"] = location
            with mock.patch.object(http.client, "HTTPConnection", Connection), \
                    mock.patch.object(http.client, "HTTPSConnection", Connection):
                try:    # the call urllib's HTTPErrorProcessor makes for a non-2xx reply
                    opener.error("http", request, io.BytesIO(b""), code, "moved", fields)
                except HTTPError as err:
                    with err:
                        return err.code, list(sent)
                except URLError:
                    return "followed", list(sent)
            return "returned", list(sent)

        away = "http://elsewhere.example/v1"
        stdlib = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        self.assertEqual(outcome(stdlib, 302, away),
                         ("followed", [("elsewhere.example", "GET", f"Bearer {SENTINEL_KEY}")]),
                         "the recorder sees a followed redirect, as urllib's own opener makes one")
        for code in (301, 302, 303, 307, 308):
            with self.subTest(code=code):
                self.assertEqual(outcome(JEV._OPENER, code, away), (code, []))
        self.assertEqual(outcome(JEV._OPENER, 302, "http://[bad/v1"), (302, []),
                         "a Location urllib cannot parse is still only the status")
        tree = ast.parse(Path(JEV.__file__).read_text(encoding="utf-8"))
        send = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_send")
        calls = {ast.unparse(n.func) for n in ast.walk(send) if isinstance(n, ast.Call)}
        self.assertIn("_OPENER.open", calls, "_send sends only through jev's opener")
        self.assertNotIn("urllib.request.urlopen", calls)

    def test_a_key_no_header_can_carry_is_no_key(self):
        # Measured 29 Sep, offline (http.client putheader with no connection): a
        # character outside latin-1, such as a pasted curly quote, raises a
        # UnicodeEncodeError whose repr holds the whole header, key included; a line
        # break raises a ValueError whose text holds it. Such a key is no key, as an
        # unprintable key FILE already is (user_setting), and nothing is sent.
        curly = SENTINEL_KEY + chr(0x2019)
        for why, key in (("a curly quote", curly), ("a line break", "sentinel\nkey-M3"),
                         ("a no-break space", "sentinel" + chr(0xA0) + "key-M3")):
            with self.subTest(why=why):
                send = _FakeSend()
                with _jev_key(key):
                    self.assertEqual(JEV.load_key(), (None, None))
                    with self.assertRaises(JEV.JevError) as caught:
                        JEV.ask(_obs_trace(), 3, send=send)
                err = caught.exception
                self.assertEqual((err.code, err.status, err.args), ("no_key", None, ("no_key",)))
                self.assertEqual(send.calls, [], "nothing is sent")
                seen = (json.dumps(vars(err)) + repr(err)
                        + "".join(traceback.format_exception(err)))
                self.assertNotIn("sentinel", seen)
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "grad-project").mkdir()
            (Path(tmp) / "grad-project" / "typesafe_key").write_text(curly + "\n",
                                                                     encoding="utf-8")
            with mock.patch.dict(os.environ, {"APPDATA": tmp}):
                os.environ.pop("TYPESAFE_API_KEY", None)
                self.assertEqual(MQ.user_setting("TYPESAFE_API_KEY", "typesafe_key"),
                                 (curly, "file"), "the file rule alone lets it through")
                self.assertEqual(JEV.load_key(), (None, None))
        # The rule is what the header can carry, not ASCII: a latin-1 letter is sent,
        # and the vendor, not this module, judges the key.
        with _jev_key(SENTINEL_KEY + chr(0xE9)):
            self.assertEqual(JEV.load_key(), (SENTINEL_KEY + chr(0xE9), "env"))

    def test_key_files_are_ignored(self):
        env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
        for path, want in ((".env", 0), (".env.local", 0), ("typesafe_key", 0),
                           ("app/typesafe_key.txt", 0), ("app/jev.py", 1)):
            with self.subTest(path=path):
                run = subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT, env=env,
                                     capture_output=True, timeout=60)
                self.assertEqual(run.returncode, want)

    def test_load_key_prefers_the_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            appdata = Path(tmp).resolve()
            (appdata / "grad-project").mkdir()
            (appdata / "grad-project" / "typesafe_key").write_text("file-key\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"APPDATA": str(appdata),
                                              "TYPESAFE_API_KEY": "env-key"}):
                self.assertEqual(JEV.load_key(), ("env-key", "env"))
                os.environ["TYPESAFE_API_KEY"] = "env-key-2"
                self.assertEqual(JEV.load_key(), ("env-key-2", "env"), "read on each call")
                del os.environ["TYPESAFE_API_KEY"]
                self.assertEqual(JEV.load_key(), ("file-key", "file"))
                with mock.patch.object(MQ, "REPO", appdata):
                    self.assertEqual(JEV.load_key(), (None, None),
                                     "a key file inside the repository is refused")
        with mock.patch.dict(os.environ, {"APPDATA": str(ROOT)}):
            os.environ.pop("TYPESAFE_API_KEY", None)
            self.assertEqual(JEV.load_key(), (None, None))


# ---- M3: the Laya worker (spec tests 13 and 19, the worker's half) ---------

WORKER_GUARDED = (("socket", "connect"), ("socket", "connect_ex"), ("socket", "sendto"),
                  ("socket", "sendmsg"), ("module", "create_connection"),
                  ("module", "getaddrinfo"), ("module", "gethostbyname"),
                  ("module", "gethostbyname_ex"))


def _worker_tree():
    return ast.parse((ROOT / "app" / "laya_worker.py").read_text(encoding="utf-8"))


def _import_roots(tree):
    """(line, root) for every import anywhere in `tree`, functions included."""
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out += [(node.lineno, a.name.split(".")[0]) for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            out.append((node.lineno, (node.module or "").split(".")[0]))
    return out


def _guard_loop(tree):
    """(index in tree.body, node) of the module-level `for ... in GUARDED:` loop."""
    for i, node in enumerate(tree.body):
        if isinstance(node, ast.For) and getattr(node.iter, "id", None) == "GUARDED":
            return i, node
    raise AssertionError("laya_worker.py has no module-level loop over GUARDED")


def _guard_source():
    """The worker's module-level code up to and including the guard loop, as source."""
    tree = _worker_tree()
    i, _ = _guard_loop(tree)
    return ast.unparse(ast.Module(body=tree.body[:i + 1], type_ignores=[]))


class WorkerStaticTests(unittest.TestCase):
    """Spec test 19, the worker's half. The guard comes before torch and laya,
    replaces only the entry points this platform has, and a relative model
    folder is refused before either is imported."""

    def test_the_guard_comes_first(self):
        tree = _worker_tree()
        assigned = [n for n in tree.body if isinstance(n, ast.Assign)
                    and [getattr(t, "id", None) for t in n.targets] == ["GUARDED"]]
        self.assertEqual(len(assigned), 1, "GUARDED must be assigned once, at module level")
        self.assertEqual(ast.literal_eval(assigned[0].value), WORKER_GUARDED)
        _, loop = _guard_loop(tree)
        first = next(n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom)))
        self.assertEqual([a.name for a in getattr(first, "names", [])], ["socket"],
                         "`import socket` must be the worker's first import")
        roots = _import_roots(tree)
        heavy = [line for line, root in roots if root in ("torch", "laya")]
        self.assertTrue(heavy, "the worker must import torch and laya")
        self.assertLess(loop.lineno, min(heavy), "the guard must run before torch or laya is imported")
        self.assertEqual([root for _, root in roots if root == "app"], [],
                         "the worker imports nothing from the repository")
        in_loop = {id(n) for n in ast.walk(loop)}
        named = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Name)
                 and n.id == "socket" and id(n) not in in_loop]
        self.assertEqual(named, [], "socket may be named only inside the guard loop")
        rebinds = [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Assign)
                   and any(ast.unparse(t) == "sys.stdout" for t in n.targets)]
        laya_line = min(line for line, root in roots if root == "laya")
        self.assertTrue(rebinds and min(rebinds) < laya_line,
                        "sys.stdout must point at stderr before `import laya`")

    def test_the_guard_leaves_missing_entry_points_missing(self):
        """The guard block alone, run in a fresh interpreter: asyncio still
        imports (a guard that ADDS socket.socket.sendmsg on Windows breaks it,
        and torch with it), and a connection is refused and counted."""
        guard = _guard_source()
        probe = ("\nimport json as _json\nimport asyncio\n"
                 "try:\n    socket.create_connection(('127.0.0.1', 9))\n    _refused = False\n"
                 "except OSError:\n    _refused = True\n"
                 "print(_json.dumps({'sendmsg': hasattr(socket.socket, 'sendmsg'),\n"
                 "                   'refused': _refused, 'attempts': _NET['attempts']}))\n")
        run = subprocess.run([sys.executable, "-I", "-c", guard + probe], capture_output=True,
                             text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr[-2000:])
        import socket
        self.assertEqual(json.loads(run.stdout.strip().splitlines()[-1]),
                         {"sendmsg": hasattr(socket.socket, "sendmsg"), "refused": True,
                          "attempts": 1})

    def test_a_relative_model_dir_is_refused_before_any_import(self):
        tree = _worker_tree()
        heavy = min(line for line, root in _import_roots(tree) if root in ("torch", "laya"))
        refusal = [n.lineno for n in ast.walk(tree)
                   if isinstance(n, ast.Constant) and n.value == "NotADirectoryError"]
        self.assertTrue(refusal and max(refusal) < heavy,
                        "the folder must be checked before torch or laya is imported")
        run = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", "app/laya_worker.py",
                              "models/multilingual"], cwd=ROOT, capture_output=True, text=True,
                             timeout=60)
        self.assertEqual(run.returncode, 1, run.stderr[-2000:])
        self.assertEqual(json.loads(run.stdout.splitlines()[0]),
                         {"ready": False, "error": "NotADirectoryError"})

    def test_a_socket_objects_own_methods_are_refused_and_counted(self):
        """create_connection is not the only way out. The guard block alone, in
        a fresh interpreter, refuses a socket object's own connect, connect_ex
        and sendto, and counts one attempt for each. Unguarded, connect_ex would
        return an error number and a UDP sendto would succeed, so neither would
        raise; an unguarded connect would raise with no count."""
        probe = ("\nimport json as _json\n"
                 "_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
                 "_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)\n"
                 "_got = {}\n"
                 "for _name, _call, _args in (('connect', _tcp.connect, (('127.0.0.1', 9),)),\n"
                 "        ('connect_ex', _tcp.connect_ex, (('127.0.0.1', 9),)),\n"
                 "        ('sendto', _udp.sendto, (b'x', ('127.0.0.1', 9)))):\n"
                 "    _before = _NET['attempts']\n"
                 "    try:\n"
                 "        _call(*_args)\n"
                 "        _got[_name] = 'not refused'\n"
                 "    except OSError:\n"
                 "        _got[_name] = _NET['attempts'] - _before\n"
                 "_tcp.close()\n"
                 "_udp.close()\n"
                 "print(_json.dumps(_got))\n")
        run = subprocess.run([sys.executable, "-I", "-B", "-c", _guard_source() + probe],
                             capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr[-2000:])
        self.assertEqual(json.loads(run.stdout.strip().splitlines()[-1]),
                         {"connect": 1, "connect_ex": 1, "sendto": 1})

    def test_no_app_module_imports_the_worker(self):
        """Importing laya_worker replaces socket entry points for the WHOLE
        process, so no module in app/ may import it: the server only ever
        starts it as another process, under Laya's own python."""
        def names_worker(name):
            parts = name.split(".")
            return parts[0] == "laya_worker" or parts[:2] == ["app", "laya_worker"]

        found = []
        for path in sorted((ROOT / "app").glob("*.py")):
            if path.name != "laya_worker.py":
                found += [f"{path.name} {n}" for n in
                          sorted(_imports(path.read_text(encoding="utf-8"))) if names_worker(n)]
        self.assertEqual(found, [])
        probe = "from app import laya_worker\nfrom .laya_worker import main\nimport laya_worker\n"
        self.assertEqual(sorted(n for n in _imports(probe) if names_worker(n)),
                         ["app.laya_worker", "app.laya_worker.main", "laya_worker"],
                         "the scan must be able to fail")
        self.assertEqual([m for m in ("app.laya_worker", "laya_worker") if m in sys.modules], [],
                         "this process, which imports the server's modules, has the worker loaded")


# ---- M3: the Laya bridge (spec tests 15 fairness, 18, 19 print scan, 20) ----
#
# The fake worker speaks the real worker's protocol. It is a string, run by
# this interpreter with -I -c, so no file is added to app/ and test 11's
# snapshot stays valid. Its mode is argv[1].

FAKE_WORKER = r'''
import json, os, sys, time
mode = sys.argv[1]


def send(obj):
    print(json.dumps(obj), flush=True)


if mode == "hang_start":
    time.sleep(60)
if mode == "exit_start":
    sys.exit(3)
if mode == "bad_ready":
    send({"ready": False, "error": "ImportError"})
    sys.exit(0)
if mode == "slow_start":
    time.sleep(1.5)
send({"ready": True, "device": "fake", "laya": "0.0.0", "load_s": 0.0,
      "env": {k: os.environ.get(k) for k in ("TYPESAFE_API_KEY", "HF_TOKEN",
                                            "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")}})
for line in sys.stdin:
    req = json.loads(line)
    if mode == "hang_answer":
        time.sleep(60)
    if mode == "eof":
        sys.exit(0)
    if mode == "deep":
        print("[" * 100000, flush=True)
        continue
    rid = req["id"] + (100 if mode == "badid" else 0)
    if mode in ("error", "value_error"):
        send({"id": rid, "ok": False, "net_attempts": 0,
              "error": "WeirdError" if mode == "error" else "ValueError"})
        continue
    answers = {}
    for qid, q in req["questions"].items():
        keys = list(q["criteria"])
        pick = (keys[-1] if mode == "order" else "retard 5 deg" if mode == "bad_choice"
                else sorted(keys)[0])
        top = 10 ** 400 if mode == "huge" else 0.6
        answers[qid] = {"choice": pick, "confidence": 0.5, "answer_confidence": 0.6,
                        "probabilities": {k: (top if k == pick else 0.1) for k in keys}}
    send({"id": rid, "ok": True, "device": "fake", "ms": 1.0, "model": "fake-laya",
          "answers": answers, "usage": {"input_tokens": 1, "output_tokens": 0},
          "net_attempts": 1 if mode == "net" else 0})
'''

LAYA_KEYS = {"model_name", "laya", "device", "ms", "started_s", "answers", "answers_reversed",
             "usage", "sent"}


def _fake_bridge(mode, **kw):
    """A LayaBridge whose worker is FAKE_WORKER in `mode`, run by this interpreter."""
    return LB.LayaBridge(command=[sys.executable, "-I", "-c", FAKE_WORKER, mode], **kw)


class _Spawned:
    """Popen, recorded: every process a bridge starts goes through the real Popen."""

    def __init__(self):
        self.procs = []
        self._popen = subprocess.Popen

    def __call__(self, *args, **kwargs):
        proc = self._popen(*args, **kwargs)
        self.procs.append(proc)
        return proc

    def patch(self):
        return mock.patch.object(LB.subprocess, "Popen", side_effect=self)


def _tree_snapshot(root):
    """{relative path: (size, mtime_ns)} for every file under root."""
    out = {}
    for p in root.rglob("*"):
        if p.is_file():
            st = p.stat()
            out[p.relative_to(root).as_posix()] = (st.st_size, st.st_mtime_ns)
    return out


class BridgeTests(unittest.TestCase):
    """Spec test 18: the bridge, against the fake worker. Nothing touches Laya."""

    def ask_fails(self, bridge, code, kind=None):
        with self.assertRaises(LB.LayaError) as caught:
            bridge.ask(_obs_trace(5), 1)
        self.assertEqual((caught.exception.code, caught.exception.kind), (code, kind))

    def test_construction_reads_and_spawns_nothing(self):
        refuse = AssertionError("the constructor must do no I/O")
        with mock.patch.object(LB, "load_home", side_effect=refuse), \
                mock.patch.object(LB, "user_setting", side_effect=refuse), \
                mock.patch.object(LB.subprocess, "Popen", side_effect=refuse):
            bridge = LB.LayaBridge()
            fake = _fake_bridge("ok")
        self.assertEqual((bridge.spawns, fake.spawns), (0, 0))
        self.assertIsNone(bridge.ready)

    def test_status_never_spawns(self):
        spawned = _Spawned()
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            python = home / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            python.parent.mkdir(parents=True)
            python.write_text("", encoding="utf-8")
            (home / "models" / "multilingual").mkdir(parents=True)
            (home / "models" / "multilingual" / "rl_agent_config.json").write_text("{}", encoding="utf-8")
            with spawned.patch(), mock.patch.dict(os.environ, {"LAYA_HOME": tmp}):
                real, fake = LB.LayaBridge(), _fake_bridge("ok")
                seen = [b.status() for b in (real, fake, real, fake, real, fake)]
        self.assertEqual(spawned.procs, [])
        self.assertEqual((real.spawns, fake.spawns), (0, 0))
        self.assertEqual(seen[0], {"configured": True, "source": "env", "problem": None,
                                   "worker": "stopped", "device": None, "laya": None})
        self.assertEqual(seen[1], {"configured": True, "source": "command", "problem": None,
                                   "worker": "stopped", "device": None, "laya": None})

    def test_not_configured_and_inside_the_repository(self):
        spawned = _Spawned()
        with tempfile.TemporaryDirectory() as tmp, spawned.patch(), \
                mock.patch.dict(os.environ, {"APPDATA": tmp}):
            os.environ.pop("LAYA_HOME", None)
            bridge = LB.LayaBridge()
            self.assertEqual(bridge.status(), {"configured": False, "source": None,
                                               "problem": "not_configured", "worker": "stopped",
                                               "device": None, "laya": None})
            self.ask_fails(bridge, "not_configured")
            os.environ["LAYA_HOME"] = str(ROOT)
            inside = LB.LayaBridge()
            got = inside.status()
            self.assertEqual((got["configured"], got["source"], got["problem"]),
                             (True, "env", "not_found"))
            self.ask_fails(inside, "not_found")
        self.assertEqual((bridge.spawns, inside.spawns, spawned.procs), (0, 0, []))

    def test_first_ask_spawns_and_the_second_reuses(self):
        trace = _obs_trace(5)
        bridge = _fake_bridge("ok")
        self.addCleanup(bridge.close)
        first, second = bridge.ask(trace, 3), bridge.ask(trace, 3)
        self.assertEqual(bridge.spawns, 1)
        self.assertEqual(set(first), LAYA_KEYS)
        self.assertIsInstance(first["started_s"], float)
        self.assertIsNone(second["started_s"])
        self.assertEqual((first["model_name"], first["laya"], first["device"]),
                         ("fake-laya", "0.0.0", "fake"))
        self.assertEqual(first["usage"], [{"input_tokens": 1, "output_tokens": 0}] * 2)
        self.assertEqual(first["answers"], first["answers_reversed"], "ok mode: every action held")
        self.assertEqual(bridge.status()["worker"], "ready")

        order = _fake_bridge("order")
        self.addCleanup(order.close)
        got = order.ask(trace, 3)
        for qid in MQ.IDS:
            with self.subTest(qid=qid):
                self.assertEqual(got["answers"][qid]["choice"], MQ.KEYS[qid][-1])
                self.assertEqual(got["answers_reversed"][qid]["choice"], MQ.KEYS[qid][0])

    def test_start_timeout_kills_and_the_next_ask_respawns(self):
        spawned = _Spawned()
        with spawned.patch():
            bridge = _fake_bridge("hang_start", start_timeout=1)
            self.addCleanup(bridge.close)
            self.ask_fails(bridge, "start_timeout")
            self.assertIsNotNone(spawned.procs[0].poll(), "the hung worker was not killed")
            got = bridge.status()
            self.assertEqual((got["worker"], got["problem"]), ("failed", "start_timeout"))
            self.ask_fails(bridge, "start_timeout")
            self.assertEqual(bridge.spawns, 2)
            for mode in ("exit_start", "bad_ready"):
                with self.subTest(mode=mode):
                    other = _fake_bridge(mode)
                    self.addCleanup(other.close)
                    self.ask_fails(other, "start_failed")
                    self.assertIsNotNone(spawned.procs[-1].poll())
                    got = other.status()
                    self.assertEqual((got["worker"], got["problem"]), ("failed", "start_failed"))

    def test_answer_timeout_kills_and_the_next_ask_respawns(self):
        spawned = _Spawned()
        with spawned.patch(), mock.patch.object(LB.atexit, "register") as register:
            bridge = _fake_bridge("hang_answer", answer_timeout=1)
            self.addCleanup(bridge.close)
            self.ask_fails(bridge, "timeout")
            self.assertIsNotNone(spawned.procs[0].poll(), "the hung worker was not killed")
            self.assertEqual(bridge.status()["worker"], "stopped")
            self.ask_fails(bridge, "timeout")
            self.assertEqual(bridge.spawns, 2)
        register.assert_called_once_with(bridge.close)

    def test_worker_errors(self):
        spawned = _Spawned()
        with spawned.patch():
            for mode, code, kind in (("error", "worker_error", "other"),
                                     ("value_error", "worker_error", "ValueError"),
                                     ("bad_choice", "bad_answer", None)):
                with self.subTest(mode=mode):
                    bridge = _fake_bridge(mode)
                    self.addCleanup(bridge.close)
                    self.ask_fails(bridge, code, kind)
                    self.assertIsNone(spawned.procs[-1].poll(), f"{mode} must not kill the worker")
                    self.assertEqual(bridge.status()["worker"], "ready")
            for mode, code in (("eof", "worker_died"), ("badid", "bad_answer"),
                               ("net", "network_attempt")):
                with self.subTest(mode=mode):
                    bridge = _fake_bridge(mode)
                    self.addCleanup(bridge.close)
                    self.ask_fails(bridge, code)
                    self.assertIsNotNone(spawned.procs[-1].poll(), f"{mode} must kill the worker")
                    self.assertEqual(bridge.status()["worker"], "stopped")

    def test_close_ends_the_worker(self):
        spawned = _Spawned()
        with spawned.patch():
            bridge = _fake_bridge("ok")
            bridge.ask(_obs_trace(5), 1)
        t0 = time.perf_counter()
        bridge.close()
        self.assertLess(time.perf_counter() - t0, 5.0)
        self.assertIsNotNone(spawned.procs[0].returncode)
        self.assertEqual(bridge.status()["worker"], "stopped")
        bridge.close()

    def test_a_killed_server_leaves_no_worker(self):
        """A server that dies without close() -- Stop-Process, a crash: its end
        of the worker's stdin closes with it, and the worker reads EOF and
        exits. The worker writes to the server's own stderr, so that pipe
        reaches EOF only when the worker has exited too."""
        server = ("import sys\n"
                  "import numpy as np\n"
                  "from app import agent_api as API, laya_bridge as LB\n"
                  "rows = np.zeros((1, 23), dtype=np.float32)\n"
                  "bridge = LB.LayaBridge(command=[sys.executable, '-I', '-c', sys.argv[1], 'ok'])\n"
                  "bridge.ask(API.Trace(('runs_c4', 5, 1), [], [], [rows, rows], 'cpu', {}), 0)\n"
                  "print(bridge._proc.pid, flush=True)\n"
                  "sys.stdin.read()\n")
        proc = subprocess.Popen([sys.executable, "-c", server, FAKE_WORKER], cwd=ROOT,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True,
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        line = proc.stdout.readline().strip()
        if not line.isdigit():
            proc.kill()
            self.fail("the stand-in server did not ask: " + proc.communicate(timeout=60)[1][-2000:])
        proc.kill()
        proc.wait(10)
        t0 = time.perf_counter()
        try:
            proc.communicate(timeout=10)
            outlived = False
        except subprocess.TimeoutExpired:
            os.kill(int(line), signal.SIGTERM)
            outlived = True
        self.assertFalse(outlived, "the worker outlived its server by 10 s")
        self.assertLess(time.perf_counter() - t0, 5.0)

    def test_the_worker_never_sees_the_key(self):
        with mock.patch.dict(os.environ, {"TYPESAFE_API_KEY": SENTINEL_KEY,
                                          "HF_TOKEN": "hf-sentinel"}):
            bridge = _fake_bridge("ok")
            self.addCleanup(bridge.close)
            bridge.ask(_obs_trace(5), 1)
            env = LB.worker_env("C:/x")
        self.assertEqual(bridge.ready["env"], {"TYPESAFE_API_KEY": None, "HF_TOKEN": None,
                                               "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
        self.assertNotIn("TYPESAFE_API_KEY", env)
        self.assertNotIn("HF_TOKEN", env)
        self.assertEqual(Path(env["HF_HOME"]), Path("C:/x") / ".cache" / "huggingface")
        self.assertEqual({k: env[k] for k in LB.OFFLINE}, LB.OFFLINE)

    def test_status_reads_the_worker_once(self):
        """The status route calls status() on its own thread, beside an ask that
        may kill the worker. _Vanishing's worker is gone at the second read of
        _proc, as it is when a kill runs between two reads."""
        class _Vanishing(LB.LayaBridge):
            @property
            def _proc(self):
                proc, self._slot = self._slot, None
                return proc

            @_proc.setter
            def _proc(self, value):
                self._slot = value

        bridge = _Vanishing(command=["never-started"])
        bridge._proc = mock.Mock(**{"poll.return_value": None})
        self.assertEqual(bridge.status()["worker"], "ready")
        self.assertEqual(bridge.spawns, 0)

    def test_a_worker_dead_between_presses_is_reaped(self):
        """A worker found dead at the next press is killed and forgotten like any
        other: its stdin closed and its ready line cleared, even when the fresh
        start then fails."""
        spawned = _Spawned()
        with spawned.patch():
            bridge = _fake_bridge("ok")
            self.addCleanup(bridge.close)
            bridge.ask(_obs_trace(5), 1)
        dead = spawned.procs[0]
        dead.kill()
        dead.wait(5)
        with mock.patch.object(LB.subprocess, "Popen", side_effect=OSError("no second worker")):
            self.ask_fails(bridge, "start_failed")
        self.assertTrue(dead.stdin.closed, "the dead worker's stdin was left open")
        self.assertIsNone(bridge.ready, "the dead worker's ready line outlived it")
        self.assertEqual(bridge.status()["worker"], "failed")


class FairnessTests(unittest.TestCase):
    """Spec test 15, fairness: both models get the same state and the same questions."""

    def test_both_models_get_the_same_question(self):
        trace = _obs_trace(5)
        bridge = _fake_bridge("ok")
        self.addCleanup(bridge.close)
        sent = bridge.ask(trace, 3)["sent"]
        body = JEV.build_request(trace, 3)
        self.assertEqual(sent[0]["state"], body["state"])
        self.assertEqual(sent[1]["state"], body["state"])
        self.assertIs(body["questions"], MQ.QUESTIONS)
        self.assertIs(sent[0]["questions"], MQ.QUESTIONS)
        self.assertIs(sent[1]["questions"], MQ.QUESTIONS_REVERSED)


class PrintScanTests(unittest.TestCase):
    """Spec test 19 across app/: the lab's read-only scan cannot see
    print(file=...), so this one does. Every such print outside the tests goes
    to sys.stderr, except the worker's protocol stream and the bridge's pipe
    into the worker, neither of which is a path to the vehicle."""

    def test_only_two_prints_leave_stderr(self):
        found = set()
        for path in sorted((ROOT / "app").glob("*.py")):
            if path.name.startswith("test_"):
                continue
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "print":
                    found |= {(path.name, ast.unparse(k.value)) for k in node.keywords
                              if k.arg == "file" and ast.unparse(k.value) != "sys.stderr"}
        self.assertEqual(found, {("laya_worker.py", "proto"), ("laya_bridge.py", "proc.stdin")})

    def test_the_bridge_imports_no_network_module(self):
        source = (ROOT / "app" / "laya_bridge.py").read_text(encoding="utf-8")
        self.assertEqual(_net_hits("laya_bridge.py", source), [])


@unittest.skipUnless(FULL, "the real Laya runs only under --full")
class LayaRealTests(unittest.TestCase):
    """Spec test 20: the real worker on a real trace. LAYA_HOME comes from this
    process's environment only, and nothing may change under it."""

    def test_real_laya(self):
        if not os.environ.get("LAYA_HOME"):
            self.skipTest("LAYA_HOME is not set in this process, so the real Laya is UNPROVEN "
                          "here: run LAYA_HOME=<Laya's folder> python -m app.test_agents --full")
        home = Path(os.environ["LAYA_HOME"]).resolve()
        before = _tree_snapshot(home)
        trace = _obs_trace(200)
        spawned = _Spawned()
        with spawned.patch():
            bridge = LB.LayaBridge()
            try:
                first = bridge.ask(trace, 190)
                ready = dict(bridge.ready)
                again = bridge.ask(trace, 190)
            finally:
                bridge.close()
        self.assertIs(ready["ready"], True)
        self.assertIn(ready["device"].split(":")[0], ("cuda", "cpu"))
        self.assertEqual(bridge.spawns, 1)
        self.assertIsInstance(first["started_s"], float)
        self.assertIsNone(again["started_s"])
        self.assertEqual(set(first["answers"]), set(MQ.IDS))
        self.assertEqual((again["answers"], again["answers_reversed"]),
                         (first["answers"], first["answers_reversed"]), "Laya is deterministic")
        for usage in first["usage"] + again["usage"]:
            self.assertLessEqual(usage["input_tokens"], 5 * 800)
        self.assertEqual([p.poll() is not None for p in spawned.procs], [True])
        self.assertEqual(_tree_snapshot(home), before, "something under LAYA_HOME changed")
        held = {q: "held" if first["answers"][q]["choice"] == first["answers_reversed"][q]["choice"]
                else "changed" for q in MQ.IDS}
        print(f"\n    Laya: {ready['device']}, laya {ready['laya']}, first load "
              f"{first['started_s']} s, both requests {first['ms']} ms then {again['ms']} ms, "
              f"input tokens {first['usage'][0]['input_tokens']}; order check (an observation, "
              f"not asserted): {held}", file=sys.stderr)


# ---- M3: the four model routes (spec test 16) --------------------------------
#
# jev is always the jev tests' _FakeSend, and AskRouteTests is a _JevCase, so a
# request that reached urllib.request.urlopen would fail before any byte left.
# Laya is always the fake worker, or a stub.

ASK_BASE = "http://127.0.0.1:8000"
ORIGIN = {"Origin": ASK_BASE}
ASK_URLS = {"jev": "/api/agents/jev", "laya": "/api/agents/laya"}
STATUS_URLS = {"jev": "/api/agents/jev/status", "laya": "/api/agents/laya/status"}
ASK_BODY = {"trace": "runs_c4/5/1", "step": 2}
JEV_KEYS = {"model", "runs_on", "model_name", "ms", "answers", "sent", "trace", "step"}


class _TraceStore:
    """The store as the model routes see it: one finished trace, every key recorded."""
    needs_sb3 = False

    def __init__(self):
        self.keys = []

    def trace(self, key):
        self.keys.append(key)
        return _obs_trace(5) if key == ("runs_c4", 5, 1) else None


class _Boom:
    """A Laya bridge whose ask raises what no code expects."""
    spawns = 0

    def status(self):
        return {"configured": True, "source": "command", "problem": None, "worker": "stopped",
                "device": None, "laya": None}

    def ask(self, trace, step):
        raise RuntimeError("secret-detail")


class AskRouteTests(_JevCase):
    """Spec test 16: the four model routes, each check run for BOTH models."""

    def client(self, send=None, laya=None):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        self.app = FastAPI()
        self.store = _TraceStore()
        self.send = send if send is not None else _FakeSend()
        self.laya = laya if laya is not None else _fake_bridge("order")
        if isinstance(self.laya, LB.LayaBridge):
            self.addCleanup(self.laya.close)
        API.install(self.app, store=self.store, jev_send=self.send, laya=self.laya)
        return TestClient(self.app, base_url=ASK_BASE)

    def test_bad_bodies_are_422_with_no_store(self):
        c = self.client()
        bodies = {f"json {b!r}": {"json": b} for b in (
            [dict(ASK_BODY, extra=1)]
            + [dict(ASK_BODY, step=s) for s in ("312", True, 1.0, 719)]
            + [dict(ASK_BODY, trace=t) for t in ("xx/runs_c4/5/1", "runs_c4/5/1/zz",
                                                 "runs_c4/5/123", "runs_C4/5/1",
                                                 "../runs_c4/5/1", "runs_c4/5/1\n")])}
        bodies["a form"] = {"data": {"trace": "runs_c4/5/1", "step": "2"}}
        bodies["text/plain"] = {"content": json.dumps(ASK_BODY),
                                "headers": {"Content-Type": "text/plain"}}
        with _jev_key(SENTINEL_KEY):
            for model, url in ASK_URLS.items():
                for why, kw in bodies.items():
                    with self.subTest(model=model, body=why):
                        kw = dict(kw, headers=dict(ORIGIN, **kw.get("headers", {})))
                        r = c.post(url, **kw)
                        self.assertEqual(r.status_code, 422)
                        self.assertEqual(r.headers.get("cache-control"), "no-store")
        self.assertEqual((self.send.calls, self.laya.spawns, self.store.keys), ([], 0, []))

    def test_an_unreadable_body_is_400_with_no_store(self):
        """A JSON body the reader fails on with something other than a JSON
        decode error (bytes that are not UTF-8, nesting 100 000 deep) is
        FastAPI's own 400, raised before the handler: no-store as well."""
        c = self.client()
        with _jev_key(SENTINEL_KEY):
            for model, url in ASK_URLS.items():
                for why, content in (("not UTF-8", bytes([0xFF, 0xFE, 0xFD])),
                                     ("nesting 100 000 deep", b"[" * 100_000 + b"]" * 100_000)):
                    with self.subTest(model=model, body=why):
                        r = c.post(url, content=content,
                                   headers=dict(ORIGIN, **{"Content-Type": "application/json"}))
                        self.assertEqual((r.status_code, r.json()),
                                         (400, {"detail": "There was an error parsing the body"}))
                        self.assertEqual(r.headers.get("cache-control"), "no-store")
        self.assertEqual((self.send.calls, self.laya.spawns, self.store.keys), ([], 0, []))

    def test_the_origin_guard(self):
        c = self.client()
        cases = (({}, "no Origin"), ({"Origin": "http://evil.test"}, "a foreign Origin"),
                 ({"Origin": "http://localhost:8000"}, "an Origin that is not http:// + Host"),
                 ({"Host": "evil.test:8000", "Origin": "http://evil.test:8000"}, "DNS rebinding"))
        with _jev_key(SENTINEL_KEY):
            for model, url in ASK_URLS.items():
                for headers, why in cases:
                    with self.subTest(model=model, why=why):
                        r = c.post(url, json=ASK_BODY, headers=headers)
                        self.assertEqual((r.status_code, r.json()),
                                         (403, {"model": model, "code": "foreign_origin"}))
                        self.assertEqual(r.headers.get("cache-control"), "no-store")
        self.assertEqual((self.send.calls, self.laya.spawns, self.store.keys), ([], 0, []))

    def test_trace_resolution(self):
        c = self.client()
        local = {"Host": "localhost:8000", "Origin": "http://localhost:8000"}
        with _jev_key(SENTINEL_KEY):
            for model, url in ASK_URLS.items():
                with self.subTest(model=model):
                    r = c.post(url, json={"trace": "runs_c4/05/1", "step": 2}, headers=ORIGIN)
                    self.assertEqual(r.status_code, 200, r.text[:300])
                    self.assertEqual(self.store.keys[-1], ("runs_c4", 5, 1))
                    r = c.post(url, json={"trace": "runs_c4/5/2", "step": 2}, headers=ORIGIN)
                    self.assertEqual((r.status_code, r.json()),
                                     (409, {"model": model, "code": "no_trace"}))
                    r = c.post(url, json={"trace": "runs_c4/5/1", "step": 5}, headers=ORIGIN)
                    self.assertEqual((r.status_code, r.json()),
                                     (409, {"model": model, "code": "step_not_computed"}))
                    r = c.post(url, json={"trace": "runs_c4/5/1", "step": 4}, headers=local)
                    self.assertEqual(r.status_code, 200, "localhost is this machine too")

    def test_wrong_methods_are_405_with_no_store(self):
        c = self.client()
        cases = ([(url, "get", "POST") for url in ASK_URLS.values()]
                 + [(url, "post", "GET") for url in STATUS_URLS.values()])
        for url, method, allow in cases:
            with self.subTest(url=url, method=method):
                r = getattr(c, method)(url, headers=ORIGIN)
                self.assertEqual((r.status_code, r.headers.get("allow"),
                                  r.headers.get("cache-control")), (405, allow, "no-store"))
        self.assertEqual((self.send.calls, self.laya.spawns, self.store.keys), ([], 0, []))

    def test_locks_are_per_model(self):
        c = self.client()
        locks = self.app.state.model_locks
        self.assertIsNot(locks["jev"], locks["laya"])
        with _jev_key(SENTINEL_KEY):
            for held, free in (("jev", "laya"), ("laya", "jev")):
                with self.subTest(held=held):
                    self.assertTrue(locks[held].acquire(blocking=False))
                    try:
                        r = c.post(ASK_URLS[held], json=ASK_BODY, headers=ORIGIN)
                        self.assertEqual((r.status_code, r.json()),
                                         (409, {"model": held, "code": "busy"}))
                        r = c.post(ASK_URLS[free], json=ASK_BODY, headers=ORIGIN)
                        self.assertEqual(r.status_code, 200, r.text[:300])
                    finally:
                        locks[held].release()

    def test_jev_failures_never_touch_laya(self):
        with _jev_key(None):
            c = self.client()
            r = c.post(ASK_URLS["jev"], json=ASK_BODY, headers=ORIGIN)
        self.assertEqual((r.status_code, r.json()), (503, {"model": "jev", "code": "no_key"}))
        self.assertEqual((self.send.calls, self.laya.spawns), ([], 0),
                         "no_key must reach neither the send nor the bridge")
        for send, want in ((_FakeSend(exc=URLError("down")), {"model": "jev", "code": "network"}),
                           (_FakeSend(status=402, payload=b"sentinel-body no credit"),
                            {"model": "jev", "code": "vendor_status", "status": 402})):
            with self.subTest(code=want["code"]):
                c = self.client(send=send)
                err = io.StringIO()
                with _jev_key(SENTINEL_KEY), contextlib.redirect_stderr(err):
                    r = c.post(ASK_URLS["jev"], json=ASK_BODY, headers=ORIGIN)
                    laya = c.post(ASK_URLS["laya"], json=ASK_BODY, headers=ORIGIN)
                self.assertEqual((r.status_code, r.json()), (502, want))
                self.assertEqual(r.headers.get("cache-control"), "no-store")
                self.assertEqual(len(send.calls), 1, "one call per press, never a retry")
                self.assertEqual(laya.status_code, 200, laya.text[:300])
                self.assertIn(f"jev: {want['code']} (step 2)", err.getvalue())
                for text in (r.text, laya.text, err.getvalue()):
                    self.assertNotIn("sentinel", text)

    def test_laya_failures_stay_in_laya_s_column(self):
        for mode, want in (("error", {"model": "laya", "code": "worker_error", "kind": "other"}),
                           ("value_error", {"model": "laya", "code": "worker_error",
                                            "kind": "ValueError"}),
                           ("net", {"model": "laya", "code": "network_attempt"})):
            with self.subTest(mode=mode):
                c = self.client(laya=_fake_bridge(mode))
                with _jev_key(SENTINEL_KEY):
                    r = c.post(ASK_URLS["laya"], json=ASK_BODY, headers=ORIGIN)
                    j = c.post(ASK_URLS["jev"], json=ASK_BODY, headers=ORIGIN)
                self.assertEqual((r.status_code, r.json()), (502, want))
                self.assertEqual(r.headers.get("cache-control"), "no-store")
                self.assertEqual(j.status_code, 200, "a Laya failure must not touch jev")
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"APPDATA": tmp}):
            os.environ.pop("LAYA_HOME", None)
            c = self.client(laya=LB.LayaBridge())
            r = c.post(ASK_URLS["laya"], json=ASK_BODY, headers=ORIGIN)
        self.assertEqual((r.status_code, r.json()), (503, {"model": "laya", "code": "not_configured"}))
        self.assertEqual(self.laya.spawns, 0)

    def test_an_unexpected_error_is_500(self):
        c = self.client(laya=_Boom())
        err = io.StringIO()
        with _jev_key(SENTINEL_KEY), contextlib.redirect_stderr(err):
            r = c.post(ASK_URLS["laya"], json=ASK_BODY, headers=ORIGIN)
            jev_r = c.post(ASK_URLS["jev"], json=ASK_BODY, headers=ORIGIN)
        self.assertEqual((r.status_code, r.json()), (500, {"model": "laya", "code": "server_error"}))
        self.assertEqual(r.headers.get("cache-control"), "no-store")
        self.assertIn("laya: server_error RuntimeError (step 2)", err.getvalue())
        self.assertNotIn("secret-detail", r.text + err.getvalue())
        self.assertEqual(jev_r.status_code, 200)
        self.assertTrue(self.app.state.model_locks["laya"].acquire(blocking=False),
                        "the lock was not released after the error")
        self.app.state.model_locks["laya"].release()

    def test_the_status_routes(self):
        c = self.client()
        with _jev_key(None):
            none = c.get(STATUS_URLS["jev"])
        self.assertEqual(none.json(), {"configured": False, "source": None, "vendor": "typesafe.ai",
                                       "model": "jev-latest", "hosted": "USA"})
        with _jev_key(SENTINEL_KEY):
            some = c.get(STATUS_URLS["jev"])
        self.assertEqual((some.json()["configured"], some.json()["source"]), (True, "env"))
        self.assertNotIn(SENTINEL_KEY, some.text)
        laya = [c.get(STATUS_URLS["laya"]) for _ in range(3)]
        self.assertEqual(self.laya.spawns, 0, "the status route started the worker")
        self.assertEqual(laya[0].json(), {"configured": True, "source": "command", "problem": None,
                                          "worker": "stopped", "device": None, "laya": None})
        c.post(ASK_URLS["laya"], json=ASK_BODY, headers=ORIGIN)
        after = c.get(STATUS_URLS["laya"]).json()
        self.assertEqual((after["worker"], after["device"], after["laya"]), ("ready", "fake", "0.0.0"))
        for resp in [none, some] + laya:
            self.assertEqual(resp.headers.get("cache-control"), "no-store")
        self.assertEqual(self.send.calls, [], "a status route sends nothing")

    def test_answers_are_no_store_and_carry_the_contract(self):
        c = self.client()
        with _jev_key(SENTINEL_KEY):
            j = c.post(ASK_URLS["jev"], json=ASK_BODY, headers=ORIGIN)
        self.assertEqual(j.status_code, 200, j.text[:300])
        got = j.json()
        self.assertEqual(set(got), JEV_KEYS)
        self.assertEqual((got["model"], got["runs_on"], got["model_name"], got["trace"], got["step"]),
                         ("jev", "external", "jev-1.13.0", "runs_c4/5/1", 2))
        self.assertEqual(got["answers"], MQ.to_action(_model_answer()))
        self.assertEqual(got["sent"], json.loads(json.dumps(JEV.build_request(_obs_trace(5), 2))))
        self.assertEqual([key for _, key in self.send.calls], [SENTINEL_KEY])
        self.assertNotIn(SENTINEL_KEY, j.text)
        self.assertEqual(j.headers.get("cache-control"), "no-store")
        first = c.post(ASK_URLS["laya"], json=ASK_BODY, headers=ORIGIN)
        again = c.post(ASK_URLS["laya"], json=ASK_BODY, headers=ORIGIN)
        self.assertEqual(first.status_code, 200, first.text[:300])
        got = first.json()
        self.assertEqual(set(got), LAYA_KEYS | {"model", "runs_on", "trace", "step"})
        self.assertEqual((got["model"], got["runs_on"], got["device"], got["laya"]),
                         ("laya", "local", "fake", "0.0.0"))
        self.assertIsInstance(got["started_s"], float)
        self.assertIsNone(again.json()["started_s"])
        for qid in MQ.IDS:
            with self.subTest(qid=qid):
                self.assertEqual(got["answers"][qid]["choice"], MQ.KEYS[qid][-1])
                self.assertEqual(got["answers_reversed"][qid]["choice"], MQ.KEYS[qid][0])
                self.assertEqual(list(got["sent"][1]["questions"][qid]["criteria"]),
                                 list(reversed(MQ.KEYS[qid])))
        self.assertEqual(first.headers.get("cache-control"), "no-store")

    def test_the_server_docstring_names_both_posts(self):
        doc = ast.get_docstring(ast.parse((ROOT / "app" / "server.py").read_text(encoding="utf-8")))
        for text in ("/api/agents/jev", "/api/agents/laya", "Neither", "path to the vehicle"):
            self.assertIn(text, doc)
        self.assertNotIn("Every HTTP route below is a GET.", doc)
        for text in ("/api/agents/jev", "/api/agents/laya"):
            self.assertIn(text, API.install.__doc__)

    def test_an_absurd_answer_is_bad_answer_never_500(self):
        """Carried from Task 2: a reply that to_action or the parser cannot hold
        (a 400-digit probability overflows, nesting 100 000 deep exhausts
        json.loads) is the model's own answer, so it is bad_answer, never 500."""
        huge = json.dumps({"model": "jev-1.13.0", "answers": _model_answer()}).replace(
            "0.6", "1" + "0" * 400, 1).encode("utf-8")
        deep = b"[" * 100_000 + b"]" * 100_000
        for why, payload, mode in (("a 400-digit probability", huge, "huge"),
                                   ("nesting 100 000 deep", deep, "deep")):
            c = self.client(send=_FakeSend(payload=payload), laya=_fake_bridge(mode))
            for model, url in ASK_URLS.items():
                with self.subTest(why=why, model=model):
                    err = io.StringIO()
                    with _jev_key(SENTINEL_KEY), contextlib.redirect_stderr(err):
                        r = c.post(url, json=ASK_BODY, headers=ORIGIN)
                    self.assertEqual((r.status_code, r.json()),
                                     (502, {"model": model, "code": "bad_answer"}))
                    self.assertEqual(r.headers.get("cache-control"), "no-store")
                    self.assertEqual(err.getvalue(), f"{model}: bad_answer (step 2)\n")

    def test_a_status_call_during_a_laya_start_is_never_500(self):
        """The status route runs beside an ask, on another thread, by design. A
        status call while the worker starts, and while a start times out and
        the worker is killed, answers 200 with no-store every time."""
        from fastapi.testclient import TestClient
        for mode, kw, want, end in (("slow_start", {}, 200, "ready"),
                                    ("hang_start", {"start_timeout": 1}, 502, "failed")):
            with self.subTest(mode=mode):
                c = self.client(laya=_fake_bridge(mode, **kw))
                pressed, seen = [], []
                press = threading.Thread(target=lambda: pressed.append(
                    TestClient(self.app, base_url=ASK_BASE).post(
                        ASK_URLS["laya"], json=ASK_BODY, headers=ORIGIN)))
                with contextlib.redirect_stderr(io.StringIO()):
                    press.start()
                    while press.is_alive():
                        seen.append(c.get(STATUS_URLS["laya"]))
                        time.sleep(0.02)
                    press.join()
                self.assertEqual(pressed[0].status_code, want, pressed[0].text[:300])
                self.assertEqual({(r.status_code, r.headers.get("cache-control")) for r in seen},
                                 {(200, "no-store")})
                self.assertIn("starting", [r.json()["worker"] for r in seen])
                self.assertEqual(c.get(STATUS_URLS["laya"]).json()["worker"], end)


def _shape(x):
    """A JSON value's structure: every dict key, a list by its first item, 'value' for the rest."""
    if isinstance(x, dict):
        return {k: _shape(v) for k, v in x.items()}
    if isinstance(x, list) and x:
        return [_shape(x[0])]
    return "value"


class PageTests(unittest.TestCase):
    """The /agents page can load every asset, id and module it names.

    The lab was dead for a day once because main.mjs did not exist: both
    suites passed, the route returned 200 and the browser 404'd one module
    (app/test_simulation.py says so). These are the same checks for this page.
    """

    STATIC = ROOT / "app" / "static"

    def read(self, rel):
        path = self.STATIC / rel
        self.assertTrue(path.is_file(), f"{rel} does not exist")
        return path.read_text(encoding="utf-8")

    def test_page_assets_ids(self):
        import re
        html = self.read("agents.html")
        page = self.read("sim/agents.mjs")
        for src in re.findall(r'<script[^>]+src="/static/([^"]+)"', html):
            self.assertTrue((self.STATIC / src).is_file(), f"{src} is referenced by the page and does not exist")
        for href in re.findall(r'<link[^>]+href="/static/([^"]+)"', html):
            self.assertTrue((self.STATIC / href).is_file(), f"{href} is referenced by the page and does not exist")
        mapped = re.findall(r'"(?:three|three/addons/)":\s*"/static/([^"]+)"', html)
        self.assertEqual(len(mapped), 2, "agents.html must carry the lab's import map")
        for target in mapped:
            path = self.STATIC / target
            self.assertTrue(path.is_file() or path.is_dir(),
                            f"import map points at missing {target}: run app\\start-simulation.ps1 once to vendor Three.js")

        ids = re.findall(r'\sid="([^"]+)"', html)
        self.assertEqual(len(ids), len(set(ids)), "an id is declared twice in agents.html")
        used = set(re.findall(r"\$\('([^']+)'\)", page))
        self.assertTrue(used, "the id scan found nothing; the pattern has drifted")
        self.assertFalse(used - set(ids), f"agents.mjs reads ids the page does not define: {sorted(used - set(ids))}")
        # M3 (design 7.7): the models panel is static in the markup and hidden
        # until the ten taps, so every id agents.mjs reads for it is one the
        # check above can see.
        self.assertTrue('<section id="models-panel" class="models-panel" hidden>' in html,
                        "#models-panel must be written out in agents.html, and hidden")

        for symbol in set(re.findall(r"'#(i-[a-z]+)'", page)):
            self.assertIn(f'id="{symbol}"', html, f"#{symbol} is not in the icon library")

        specs = (re.findall(r"from '(\./[^']+)'", page)
                 + re.findall(r"^import '(\./[^']+)'", page, flags=re.M)
                 + re.findall(r"import\('(\./[^']+)'\)", page))
        self.assertTrue(specs, "the import scan found nothing; the pattern has drifted")
        for spec in specs:
            self.assertTrue((self.STATIC / "sim" / spec[2:]).is_file(), f"agents.mjs imports missing {spec}")
        # M3: the gesture and the panel's pure logic (design 7.2), both static.
        for spec in ("./tap-unlock.mjs", "./model-panel.mjs"):
            self.assertIn(spec, specs, f"agents.mjs does not import {spec}")

        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.agent_api import install
        app = FastAPI()
        install(app)
        with TestClient(app) as client:
            response = client.get("/agents")
        self.assertEqual(response.status_code, 200)
        self.assertIn("/static/sim/agents.mjs", response.text)

    def test_every_string_names_its_language(self):
        """t() with any first argument but currentLang renders one language only.

        app/test_simulation.py pins the same rule on main.mjs, where two bare
        calls once left Arabic on screen in English mode.
        """
        import re
        page = self.read("sim/agents.mjs")
        firsts = re.findall(r"[^.\w]t\(\s*([^,)]*)", page)
        self.assertTrue(firsts, "the t() scan found nothing; the pattern has drifted")
        for first in firsts:
            self.assertEqual(first.strip(), "currentLang", f"t() called with {first.strip()!r} as the language")

    def test_chase_is_optional(self):
        """Three.js is loaded on demand, so its failure cannot blank the page.

        app/static/vendor/ is gitignored and exists only after
        app/start-simulation.ps1 has run. One static import of agent-scene.mjs,
        scene.mjs or 'three' anywhere in agents.mjs's static module graph would
        take the verdict box, the SIMULATED badge, the dt caption, the profile
        and the pause panel down with it when Three.js is missing.
        """
        import re
        page = self.read("sim/agents.mjs")
        self.assertTrue("import('./agent-scene.mjs')" in page, "the chase view must be loaded by dynamic import")
        self.assertTrue("'agents.scene.webgl_error'" in page, "a failed chase view must say so in its place")
        seen, todo = set(), ["agents.mjs"]
        while todo:
            name = todo.pop()
            if name in seen:
                continue
            seen.add(name)
            src = self.read(f"sim/{name}")
            for spec in re.findall(r"^\s*import\b(?!\s*\()[^;]*?['\"]([^'\"]+)['\"]", src, flags=re.M):
                self.assertFalse(spec == "three" or spec.startswith("three/"), f"{name} imports {spec} statically")
                self.assertNotIn(spec, ("./agent-scene.mjs", "./scene.mjs"), f"{name} imports {spec} statically")
                if spec.startswith("./"):
                    todo.append(spec[2:])
        self.assertTrue({"agent-view.mjs", "agents-strings.mjs", "i18n.mjs", "playback.mjs",
                         "tap-unlock.mjs", "model-panel.mjs"} <= seen,
                        f"the static graph scan found only {sorted(seen)}")

    def test_every_car_is_read_through_carOf(self):
        """A lane that diverged is null from that step on (design section 3.2).

        Reading a car straight off frame.cars throws on the first null car and
        the pause panel stops updating, so the page reads cars only through
        carOf(), which returns null for a missing one.
        """
        import re
        page = self.read("sim/agents.mjs")
        hits = [m.start() for m in re.finditer(r"\.cars\b", page)]
        self.assertEqual(len(hits), 1, "read a car only through carOf(frame, lane)")
        head = page.rfind("function carOf(", 0, hits[0])
        self.assertNotEqual(head, -1, "the one read of .cars must be inside carOf")
        self.assertLess(hits[0] - head, 120, "the one read of .cars must be inside carOf")

    def test_the_picker_opens_empty_and_disabled(self):
        """Nothing is selected when the page opens (design section 6, Picker).

        The three selects carry no <option> in the markup, so nothing can read
        as chosen before the catalog arrives, and they stay disabled until
        agents.mjs fills them from it. The list of pairs that cannot run
        starts hidden and empty; agents.mjs fills it from the catalog too. The
        address is only ever REPLACED: a pushState would make every choice a
        step of the back button.
        """
        html = self.read("agents.html")
        for name in ("pick-experiment", "pick-pair", "pick-episode"):
            m = re.search(rf'<select id="{name}"([^>]*)>(.*?)</select>', html, flags=re.S)
            self.assertIsNotNone(m, f"#{name} is missing")
            self.assertIn("disabled", m.group(1), f"#{name} must start disabled")
            self.assertEqual(m.group(2).strip(), "", f"#{name} must carry no option in the markup")
        # The captions under the selects start empty; agents.mjs fills them.
        # pick-experiment-note carries the chosen experiment's WHOLE short
        # line, because a closed select can cut it before its qualifiers.
        for name in ("pick-experiment-note", "pick-pair-note", "pick-episode-note"):
            self.assertTrue(f'<p id="{name}" class="pick-caption"></p>' in html, f"#{name} is missing")
        rows = [html.find(f'id="{name}"') for name in
                ("pick-experiment", "pick-experiment-note", "pick-pair", "pick-pair-note",
                 "pick-episode", "pick-episode-note")]
        self.assertEqual(rows, sorted(rows), "each caption must sit right under its own select")
        self.assertTrue('<details id="pick-refused" class="pick-refused" hidden></details>' in html,
                        "#pick-refused is missing, or not hidden and empty")
        page = self.read("sim/agents.mjs")
        self.assertTrue("fetch('/api/agents/catalog'" in page, "the page does not load the catalog")
        self.assertFalse("parseEpisodeQuery" in page, "M1's read-only address parser is still used")
        self.assertFalse("pushState" in page, "the address is replaced, never pushed")

    def test_the_lab_links_to_agents_where_phones_keep_it(self):
        """The replay lab's one link to /agents (design section 2, edit 4).

        Jad found on 28 Sep that the lab had no way to /agents. The link sits
        right AFTER the lab's first link, never at the end: the lab's phone
        rule hides .topbar nav a:last-child below 760 px (sim/style.css), so a
        link at the end would vanish on phones.
        """
        html = self.read("simulation.html")
        nav = re.search(r"<nav[^>]*>(.*?)</nav>", html, flags=re.S)
        self.assertIsNotNone(nav, "simulation.html has no <nav>")
        links = re.findall(r"<a\b([^>]*)>", nav.group(1))

        def attr(tag, name):
            m = re.search(rf'\b{name}="([^"]*)"', tag)
            return m.group(1) if m else None

        self.assertEqual([attr(a, "href") for a in links], ["/simulation", "/agents", "/", "/review"])
        agents = links[1]
        self.assertEqual(attr(agents, "data-i18n"), "nav.agents")
        self.assertNotIn("active", attr(agents, "class") or "", "the lab's page stays the active one")
        self.assertIn("active", attr(links[0], "class") or "")
        self.assertIsNot(links[-1], agents, "the last link is hidden on phones")
        self.assertTrue(".topbar nav a:last-child{display:none}" in self.read("sim/style.css"),
                        "the phone rule this placement answers has moved; re-check where the link sits")

    def test_the_lab_launcher_names_the_agents_page(self):
        """app/start-simulation.ps1 names /agents and says when its python
        cannot compute an episode (design section 10, M1 Verify note). Only its
        banner changes: its interpreter and its last line stay as they were."""
        text = (self.STATIC.parent / "start-simulation.ps1").read_text(encoding="utf-8")
        self.assertTrue("localhost:$Port/agents" in text, "the banner does not name /agents")
        self.assertTrue("stable_baselines3" in text, "the banner does not check for stable-baselines3")
        self.assertEqual(text.rstrip().splitlines()[-1],
                         "python -m app.server --simulation --http-port $Port")

    @unittest.skipUnless(HAVE_ALL_RUNS, NO_ALL_RUNS)
    def test_catalog_fixture_has_the_server_shape(self):
        """agent-picker.test.mjs drives the picker from a copy of the catalog.

        The copy is sim/agent-catalog.fixture.json, generated from
        agent_api.catalog and never edited by hand. If the served shape moves,
        this fails before a node test can pass against a stale copy.
        """
        text = self.read("sim/agent-catalog.fixture.json")
        self.assertTrue(text.isascii(), "the fixture must be written with ensure_ascii")
        fixture = json.loads(text)
        self.assertIs(fixture["sb3"], True, "the fixture pins sb3 true")
        self.assertEqual(_shape(fixture), _shape(API.catalog()),
                         "agent-catalog.fixture.json no longer has the catalog's shape: regenerate "
                         "it with the command in the header of app/static/sim/agent-picker.test.mjs, "
                         "then re-run node --test \"app/static/sim/*.test.mjs\"")


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]] + [a for a in sys.argv[1:] if a != "--full"], verbosity=2)

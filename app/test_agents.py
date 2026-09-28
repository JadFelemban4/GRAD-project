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
import warnings

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

        from fastapi import FastAPI
        app, client = _client(_StubStore())
        paths = {r.path: r for r in app.routes if hasattr(r, "methods")}
        added = set(paths) - {r.path for r in FastAPI().routes}
        self.assertEqual(added, {"/agents", "/api/agents/episode", "/api/agents/catalog"})
        for p in sorted(added):
            self.assertEqual(set(paths[p].methods), {"GET"}, p)
        self.assertEqual(client.post(EPISODE_URL).status_code, 405)
        self.assertEqual(client.post(CATALOG_URL).status_code, 405)

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

        for symbol in set(re.findall(r"'#(i-[a-z]+)'", page)):
            self.assertIn(f'id="{symbol}"', html, f"#{symbol} is not in the icon library")

        specs = (re.findall(r"from '(\./[^']+)'", page)
                 + re.findall(r"^import '(\./[^']+)'", page, flags=re.M)
                 + re.findall(r"import\('(\./[^']+)'\)", page))
        self.assertTrue(specs, "the import scan found nothing; the pattern has drifted")
        for spec in specs:
            self.assertTrue((self.STATIC / "sim" / spec[2:]).is_file(), f"agents.mjs imports missing {spec}")

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
        self.assertTrue({"agent-view.mjs", "agents-strings.mjs", "i18n.mjs", "playback.mjs"} <= seen,
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
        for name in ("pick-pair-note", "pick-episode-note"):
            self.assertTrue(f'<p id="{name}" class="pick-caption"></p>' in html, f"#{name} is missing")
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

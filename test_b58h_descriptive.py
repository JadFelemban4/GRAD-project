"""test_b58h_descriptive.py -- the readers of the B58 study's descriptive rows (b58h_descriptive.py; row 147 (11)).

    python -B test_b58h_descriptive.py        a few minutes; exit code 0 when all pass

ORDER step 16 (commit V) writes b58h_descriptive.py, the reader of decision 12's three checks for schema-4
agents: the logged-state check, the transfer battery and the locked climb. Each reader has a control that
fails (mistake 12), and every refusal is asserted by its own text. Nothing here trains: the agents are
test_scoring_protocol's SYNTHETIC run folders (untrained SAC networks saved as decision 29's run leaves
one), in a temporary folder outside the repository. No logged drive, EPA table or held-out row is read:
the logged check's and the battery's counts are checked on scripted steps and against their scripts' own
text and cycle, and the battery's cycle against conditions_test._run's, captured before its episode runs.

  Agents      agent_dirs finds the three arms (and sighted_seed<S>, for arm_of to refuse), and leaves a crashed
              run and a folder without final.zip out; the control: conditions_test._agent_tags misses the
              r-arms
  ReadSet     the arm and H read from each meta.json through evaluate.arm_of; the controls: an H one ulp off,
              another environment, no blinded agent, each refused by its text
  Policy      the reader scores evaluate.load_agent's checkpoint average; the control: final.zip acts otherwise
  Horizon     plan gives each agent its own H and the hand-written policies the default; run_job hands it to
              the episode; the locked-climb reader at the default H is evaluate.run_episode, and at the agent's
              H it is not (the control)
  Transfer    check_agents declares each agent's transfer, prints it, and refuses another reward; the scored
              side is each row's own (route_scored): phase-d's for the locked climb, the hills file by path
              and sha_text with the battery's conditions and episodes, the drives' record with the logged
              drives and weightings (the controls: phase-d's names no hills file, another hills file another
              declaration); a scored side naming another field is refused
  Battery     battery_cycle is conditions_test._run's cycle and inlet, and the control's grade is not;
              BatteryCounts counts as _run does; BATTERY_SHORT is _run's literal; one episode of the reader
              equals conditions_test._run's own row, key for key (the control: another episode differs);
              read_grades and its refusals, a hills file of another plant's engine_sha among them
  Logged      LoggedCounts and logged_verdict decide as logged_check.run does, each at its boundary;
              LOGGED_ABOVE_C and LOGGED_DT are run's literals
  Cli         main()'s refusals, and the control that reaches the set
"""
import contextlib
import copy
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

import b58h_descriptive as BD  # noqa: E402
import check_premise as C  # noqa: E402
import conditions_test as CT  # noqa: E402
import engine_env as E  # noqa: E402
import engines  # noqa: E402
import epa_roads as ER  # noqa: E402
import evaluate as V  # noqa: E402
import fingerprint as FP  # noqa: E402
import logged_check as LC  # noqa: E402
import test_scoring_protocol as TSP  # noqa: E402
from thresholds import common  # noqa: E402

STATE = {}


def setUpModule():
    TSP.setUpModule()                      # its temporary folder and SYNTHETIC roads record, which make_run reads


def tearDownModule():
    TSP.tearDownModule()


def b58():
    return engines.get("b58")


def touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb"):
        pass


def the_set():
    """A SYNTHETIC set of one seed's three arms, made once."""
    if "set" not in STATE:
        folder = TSP.fresh("b58h_set")
        STATE["set"] = folder
        STATE["runs"] = {r: TSP.make_run(folder, seed=7, ratio=r, perturb=p) for r, p in ((None, 0.05), (0.5, 0.06),
                                                                                         (1.5, 0.07))}
    return STATE["set"]


def copy_set(name):
    """A copy of the set to spoil."""
    dst = os.path.join(TSP.fresh(name), "set")
    shutil.copytree(the_set(), dst)
    return dst


def read(set_dir):
    return BD.read_set(set_dir, roads_rec=TSP.STATE["record"], engine="b58", train_backend=FP.BACKEND_CYCLE)


class FakeEnv:
    """What the two counters read of an environment after a step: k, prev_act and the baseline's housing."""

    def __init__(self, k, t_turb_base):
        self.k = k
        self.prev_act = np.full(5, float(k), dtype=np.float32)
        self.thermal_base = type("T", (), {"t_turb": t_turb_base})()


# =====================================================================================================
class Agents(unittest.TestCase):
    def test_the_three_arms_and_nothing_else(self):
        root = TSP.fresh("dirs")
        for name in ("blind_seed0", "sighted_r0.5_seed0", "sighted_r1.5_seed0", "sighted_seed1",
                     "blind_seed2.crashed1", "notes"):
            touch(os.path.join(root, name, "final.zip"))
        os.makedirs(os.path.join(root, "sighted_r1.5_seed3"))                   # no final.zip
        got = [os.path.basename(p) for p in BD.agent_dirs(root)]
        self.assertEqual(got, ["blind_seed0", "sighted_seed1", "sighted_r0.5_seed0", "sighted_r1.5_seed0"])
        with mock.patch.object(CT, "SET", root):                                 # the control: X1's reader
            x1 = CT._agent_tags()
        self.assertNotIn("sighted_r0.5_seed0", x1)
        self.assertNotIn("sighted_r1.5_seed0", x1)
        self.assertIn("blind_seed0", x1)


# =====================================================================================================
class ReadSet(unittest.TestCase):
    def test_the_arm_and_H_come_from_each_meta_json(self):
        agents = read(the_set())
        self.assertEqual([(x["arm"], x["seed"], x["H_s"]) for x in agents],
                         [("blind", 7, None), ("sighted_r0.5", 7, TSP.h_of(0.5)), ("sighted_r1.5", 7, TSP.h_of(1.5))])

    def refused(self, set_dir, text):
        with self.assertRaises(SystemExit) as cm:
            read(set_dir)
        self.assertIn(text, str(cm.exception))

    def test_the_controls(self):
        spoiled = copy_set("ulp")
        p = os.path.join(spoiled, "sighted_r1.5_seed7", "meta.json")
        meta = FP.read(p)
        meta["preview_h_s"] = float(np.nextafter(meta["preview_h_s"], 1e9))
        TSP.put_json(os.path.join(spoiled, "sighted_r1.5_seed7"), "meta.json", meta)
        self.refused(spoiled, "is not r x tau")
        spoiled = copy_set("env")
        TSP.put_json(os.path.join(spoiled, "blind_seed7"), "config.json",
                     TSP.synthetic_config(device="cuda"))
        self.refused(spoiled, "one environment (row 143 (5)): config.json device")
        spoiled = copy_set("noblind")
        shutil.rmtree(os.path.join(spoiled, "blind_seed7"))
        self.refused(spoiled, "row 117's pairs: no blinded agent")
        self.refused(TSP.fresh("empty"), "holds no run folder")


# =====================================================================================================
class Policy(unittest.TestCase):
    def test_the_reader_scores_the_checkpoint_average(self):
        from stable_baselines3 import SAC
        the_set()
        run = STATE["runs"][1.5]
        BD._W.update(key=None, policy=None)
        obs = np.linspace(-0.4, 0.6, E.OBS_DIM).astype(np.float32)
        got = BD._policy("agent", run)(None, obs)
        avg, _ = V.load_agent(run, FP.read(os.path.join(run, "meta.json")), device="cpu")
        self.assertTrue(np.array_equal(got, V.agent_policy(avg)(None, obs)))
        final = SAC.load(os.path.join(run, "final"), device="cpu").predict(obs, deterministic=True)[0]
        self.assertFalse(np.array_equal(np.asarray(final, np.float32), got))          # the control
        self.assertIs(BD._policy("hand", "p_grade_now"), C.p_grade_now)


# =====================================================================================================
class Horizon(unittest.TestCase):
    def test_each_agent_gets_its_own_H(self):
        agents = read(the_set())
        jobs, keys, cases = BD.plan("locked", agents, engine="b58", reward_knock=False, grades=None)
        self.assertEqual(len(cases), len(V.EPISODES))
        self.assertEqual(len(jobs), (len(V.HAND_POLICIES) + 3) * len(cases))
        by_ref = {j[3]: (j[4], j[5]) for j in jobs}
        self.assertEqual(by_ref["p_neutral"], (True, E.PREVIEW_H_S))
        self.assertEqual(by_ref[STATE["runs"][None]], (False, None))
        self.assertEqual(by_ref[STATE["runs"][0.5]], (True, TSP.h_of(0.5)))
        self.assertEqual(by_ref[STATE["runs"][1.5]], (True, TSP.h_of(1.5)))
        self.assertEqual(keys[-1], ("agents", ("sighted_r1.5", 7)))
        seen = {}

        def spy(policy, cycle, seed, weights, **kw):
            seen.update(kw, seed=seed)
            return dict({k: 0.0 for k in V.EPISODE_KEYS}, steps=1, fuel_base=0.0, damage_base=0.0)
        BD._W.update(key=None, policy=None)
        with mock.patch.object(V, "run_cycle_episode", spy):
            BD.run_job(("locked", "b58", "agent", STATE["runs"][0.5], True, TSP.h_of(0.5), False, ("locked", 3)))
        self.assertEqual((seen["use_preview"], seen["preview_h_s"], seen["reward_knock"], seen["seed"]),
                         (True, TSP.h_of(0.5), False, V.EPISODES[2][0]))

    def test_the_locked_reader_is_run_episode_at_the_default_H_and_not_at_the_agents(self):
        t, v = ER.time_and_speed()
        cycle = {"t": t[:30], "v_mps": v[:30], "grade": ER.climb_profile(t[:30], 20.0, 30.0, 0.10),
                 "t_amb": ER.T_AMB_K, "p_baro": ER.P_BARO_KPA, "humidity": ER.HUMIDITY}

        def fake_cycle(road, *, plant):
            return copy.deepcopy(cycle)
        with mock.patch.object(V, "episode_cycle", fake_cycle):
            at30 = BD.locked_episode(C.p_predictive, 1, plant=b58(), use_preview=True, preview_h_s=E.PREVIEW_H_S,
                                     reward_knock=True)
            want = V.run_episode(C.p_predictive, V.EPISODES[0][0], V.EPISODES[0][1], True, plant=b58())
            at_h = BD.locked_episode(C.p_predictive, 1, plant=b58(), use_preview=True, preview_h_s=TSP.h_of(0.5),
                                     reward_knock=True)
        self.assertEqual(at30, want)
        self.assertNotEqual(at_h["ret"], want["ret"])                              # the control: H reaches it


# =====================================================================================================
def transfer_set(name):
    """A copy of the set whose agents trained on this plant at their own H (every FATAL field of meta.json
    phase-d's block's but scenario and episodes_sha), on other roads: the declared transfer's case."""
    spoiled = copy_set(name)
    for n in os.listdir(spoiled):
        run = os.path.join(spoiled, n)
        meta = FP.read(os.path.join(run, "meta.json"))
        live = BD.transfer_live(b58(), preview_h_s=meta["preview_h_s"], reward_knock=False,
                                train_backend=FP.BACKEND_CYCLE)
        meta.update({k: live[k] for k in FP.FATAL})               # trained on this plant at this H ...
        meta.update(scenario={"protocol": "decision-34"}, episodes_sha="SYNTHETIC")   # ... on other roads
        TSP.put_json(run, "meta.json", meta)
    return read(spoiled)


def declare(agents, row, scored, *, reward_knock=False):
    """check_agents on one row's route, its printed text captured: (lines, manifests, printed)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        lines, manifests = BD.check_agents(agents, plant=b58(), reward_knock=reward_knock,
                                           train_backend=FP.BACKEND_CYCLE, route=BD.ROUTES[row], scored=scored)
    return lines, manifests, out.getvalue()


def scored_lines(lines, field):
    """The declaration's line of one exempt field, one per agent ('  scenario       trained ... scored ...')."""
    return [line for line in lines if line.lstrip().startswith(field + " ")]


class Transfer(unittest.TestCase):
    def test_each_transfer_is_declared_and_another_reward_refused(self):
        agents = transfer_set("transfer")
        lines, manifests, printed = declare(agents, "locked", BD.route_scored("locked", cases=[], inputs={}))
        declared = [line for line in lines if line.startswith("DECLARED TRANSFER")]
        self.assertEqual(len(declared), 3)
        self.assertTrue(all(BD.ROUTES["locked"] in line for line in declared))
        self.assertEqual(sorted(manifests), sorted(x["path"] for x in agents))
        for line in declared + scored_lines(lines, "scenario") + scored_lines(lines, "episodes_sha"):
            self.assertIn(line, printed)                     # printed, not only returned (row 147 (11))
        self.assertEqual(len(scored_lines(lines, "episodes_sha")), 3)
        # the locked climb's scored side is phase-d's own block: the locked climb and the twenty episodes
        live = BD.transfer_live(b58(), preview_h_s=None, reward_knock=False, train_backend=FP.BACKEND_CYCLE)
        for line in scored_lines(lines, "scenario"):
            self.assertTrue(line.endswith(f"scored {json.dumps(live['scenario'], sort_keys=True)}"), line)
        for line in scored_lines(lines, "episodes_sha"):
            self.assertTrue(line.endswith(f"scored {live['episodes_sha']}"), line)
        with self.assertRaises(SystemExit) as cm:                                   # the control
            declare(agents, "locked", {}, reward_knock=True)
        self.assertIn("reward_knock is False in its meta.json and True live", str(cm.exception))
        with self.assertRaises(ValueError) as cm:
            declare(agents, "locked", {"scenario": {}, "reward_knock": False})
        self.assertIn("replaces only ['scenario', 'episodes_sha'], not ['reward_knock']", str(cm.exception))

    def test_the_battery_route_names_its_hills_file_and_the_logged_route_its_drives(self):
        agents = transfer_set("transfer_routes")
        folder = TSP.fresh("hills_route")
        hills = {name: {"grade": round(0.18 + 0.01 * k, 4)} for k, (name, _, _) in enumerate(CT.CONDITIONS)}
        hills[CT.CONDITIONS[1][0]] = {"grade": None, "curve": {}}
        fixed = {"engine_sha": engines.engine_sha(b58())}
        path = TSP.put_json(folder, "conditions_grades.json", dict(hills, fixed_before_training=fixed))
        named = {"path": path, "sha_text": common.sha_text(path)}
        cases = BD.cases_for("battery", grades=BD.read_grades(path, plant=b58()))
        scored = BD.route_scored("battery", cases=cases, inputs={"grades": named})
        lines, _, printed = declare(agents, "battery", scored)
        scen = scored_lines(lines, "scenario")
        self.assertEqual(len(scen), 3)
        for line in scen:
            self.assertTrue(line.endswith(f"scored {json.dumps(scored['scenario'], sort_keys=True)}"), line)
            self.assertIn(json.dumps(named["sha_text"]), line)            # the hills file, by its sha_text ...
            self.assertIn(json.dumps(path), line)                        # ... and its path
            self.assertIn(line, printed)
        self.assertEqual([c[0] for c in scored["scenario"]["conditions"]],
                         [name for k, (name, _, _) in enumerate(CT.CONDITIONS) if k != 1])
        self.assertEqual([c[3] for c in scored["scenario"]["conditions"]],
                         [hills[name]["grade"] for k, (name, _, _) in enumerate(CT.CONDITIONS) if k != 1])
        want = hashlib.sha256(repr(tuple((i, V.EPISODES[i - 1]) for i in CT.EPISODES)).encode()).hexdigest()[:16]
        self.assertEqual(scored["episodes_sha"], want)
        for line in scored_lines(lines, "episodes_sha"):
            self.assertTrue(line.endswith(f"scored {want}"), line)
        # the controls: phase-d's block names no hills file and not the battery's episodes, and another hills
        # file makes another declaration
        live = BD.transfer_live(b58(), preview_h_s=None, reward_knock=False, train_backend=FP.BACKEND_CYCLE)
        self.assertNotEqual(live["episodes_sha"], want)
        self.assertNotIn(named["sha_text"], json.dumps(live["scenario"]))
        other = TSP.put_json(folder, "other.json", dict(hills, **{CT.CONDITIONS[0][0]: {"grade": 0.25}},
                                                        fixed_before_training=fixed))
        again = BD.route_scored("battery", cases=BD.cases_for("battery", grades=BD.read_grades(other, plant=b58())),
                                inputs={"grades": {"path": other, "sha_text": common.sha_text(other)}})
        self.assertNotEqual(again["scenario"], scored["scenario"])
        # the logged route: the drives' record, its drives in order and the two weightings (SYNTHETIC cases;
        # no logged drive is read here)
        cycles = {"path": "results/logged_cycles.json", "sha_text": "SYNTHETIC"}
        cases = [("logged", "SYNTHETIC_a.csv", 3), ("logged", "SYNTHETIC_a.csv", 14),
                 ("logged", "SYNTHETIC_b.csv", 3), ("logged", "SYNTHETIC_b.csv", 14)]
        got = BD.route_scored("logged", cases=cases, inputs={"cycles": cycles})
        self.assertEqual((got["scenario"]["route"], got["scenario"]["cycles"], got["scenario"]["drives"]),
                         ("logged", cycles, ["SYNTHETIC_a.csv", "SYNTHETIC_b.csv"]))
        self.assertEqual(got["episodes_sha"],
                         hashlib.sha256(repr(((3, V.EPISODES[2]), (14, V.EPISODES[13]))).encode()).hexdigest()[:16])
        lines, _, _ = declare(agents, "logged", got)
        for line in scored_lines(lines, "scenario"):
            self.assertIn('"sha_text": "SYNTHETIC"', line)
        with self.assertRaises(ValueError) as cm:
            BD.route_scored("hills", cases=[], inputs={})
        self.assertIn("row 'hills' is not one of", str(cm.exception))


# =====================================================================================================
class Battery(unittest.TestCase):
    def test_the_cycle_is_conditions_tests(self):
        class Sentinel(Exception):
            pass
        seen = {}

        def capture(cycle, **kw):
            seen.update(cycle=cycle, **kw)
            raise Sentinel
        name, t_amb, p_baro = CT.CONDITIONS[3]
        with mock.patch.object(E, "SupervisoryTunerEnv", capture):
            with self.assertRaises(Sentinel):
                CT._run(("baseline ECU", 1, t_amb, p_baro, 0.20, "varying"))
        cycle, inlet = BD.battery_cycle(b58(), t_amb=t_amb, p_baro=p_baro, grade=0.20)
        for key in ("t", "v_mps", "grade"):
            self.assertTrue(np.array_equal(cycle[key], seen["cycle"][key]), key)
        for key in ("t_amb", "p_baro", "humidity"):
            self.assertEqual(cycle[key], seen["cycle"][key], key)
        self.assertEqual(inlet, seen["inlet_kpa"])
        other, _ = BD.battery_cycle(b58(), t_amb=t_amb, p_baro=p_baro, grade=0.21)       # the control
        self.assertFalse(np.array_equal(other["grade"], seen["cycle"]["grade"]))

    def test_the_counts_are_run_s(self):
        cycle = {"grade": np.array([0.0, 0.0, 0.1, 0.1])}
        counts = BD.BatteryCounts(cycle)
        hot = CT.TRIGGER_C + 273.15
        for k, (req, got, turb) in enumerate(((100.0, 94.9, hot + 1.0), (100.0, 95.0, hot - 0.5),
                                             (100.0, 96.0, hot + 2.0), (100.0, 90.0, hot - 1.0)), start=1):
            counts(FakeEnv(k, 0.0), None, {"torque_req": req, "torque": got, "t_turb": turb})
        row = counts.row(dt=1.0)
        self.assertEqual((row["short_steps"], row["s_above"]), (2, 2.0))
        self.assertEqual(row["act_climb"], [3.5] * 5)                     # the steps of k 3 and 4: grade[2], grade[3]
        with open(os.path.join(HERE, "conditions_test.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(BD.BATTERY_SHORT, 0.95)
        self.assertIn('short += int(info["torque"] < 0.95 * info["torque_req"])', src)
        self.assertIn('above += int(info["t_turb"] - 273.15 > TRIGGER_C)', src)

    def test_the_hills(self):
        folder = TSP.fresh("hills")
        hills = {name: {"grade": 0.2} for name, _, _ in CT.CONDITIONS}
        hills[CT.CONDITIONS[1][0]] = {"grade": None, "curve": {}}
        good = dict(hills, fixed_before_training={"engine_sha": engines.engine_sha(b58())})
        path = os.path.join(folder, "good.json")
        TSP.put_json(folder, "good.json", good)
        self.assertEqual(BD.read_grades(path, plant=b58())[CT.CONDITIONS[1][0]]["grade"], None)    # the control
        cases = BD.cases_for("battery", grades=BD.read_grades(path, plant=b58()))
        self.assertEqual(len(cases), (len(CT.CONDITIONS) - 1) * len(CT.EPISODES))
        TSP.put_json(folder, "x1.json", dict(hills, fixed_before_training={"plant_sha": "SYNTHETIC"}))
        with self.assertRaises(SystemExit) as cm:
            BD.read_grades(os.path.join(folder, "x1.json"), plant=b58())
        self.assertIn("they were fixed on engine_sha None", str(cm.exception))
        short = dict(good)
        del short[CT.CONDITIONS[4][0]]
        TSP.put_json(folder, "short.json", short)
        with self.assertRaises(SystemExit) as cm:
            BD.read_grades(os.path.join(folder, "short.json"), plant=b58())
        self.assertIn(f"no hill for ['{CT.CONDITIONS[4][0]}']", str(cm.exception))

    def test_a_hills_file_of_another_plant_is_refused(self):
        """The hills are fixed in Q on the study's plant (b58h_descriptive's THE HILLS): a file whose
        fixed_before_training.engine_sha is not this plant's is refused by its text, one character off
        included; the control, the plant's own engine_sha, passes."""
        folder = TSP.fresh("hills_plant")
        want = engines.engine_sha(b58())
        hills = {name: {"grade": 0.2} for name, _, _ in CT.CONDITIONS}
        own = TSP.put_json(folder, "own.json", dict(hills, fixed_before_training={"set": "runs/b58h_dt1",
                                                                                  "engine_sha": want}))
        self.assertEqual(BD.read_grades(own, plant=b58())[CT.CONDITIONS[0][0]]["grade"], 0.2)      # the control
        near = want[:-1] + ("0" if want[-1] != "0" else "1")
        for sha in (near, "SYNTHETIC-engine-sha"):
            path = TSP.put_json(folder, "other.json", dict(hills, fixed_before_training={"set": "runs/b58h_dt1",
                                                                                         "engine_sha": sha}))
            with self.assertRaises(SystemExit) as cm:
                BD.read_grades(path, plant=b58())
            self.assertIn(f"they were fixed on engine_sha {sha!r}, and this plant's is {want} (Q fixes them",
                          str(cm.exception))

    def test_one_episode_is_conditions_tests_own(self):
        """The reader and X1's script on one episode: conditions_test._run's row for the baseline ECU on
        condition 3's hill, frozen episode 1, against battery_episode's at the default H with X1's reward,
        key for key: the cycle, the inlet, the loop and the counts at once. The control: episode 5 differs."""
        k, grade = 3, 0.20
        _, t_amb, p_baro = CT.CONDITIONS[k]
        _, want = CT._run(("baseline ECU", 1, t_amb, p_baro, grade, "varying"))
        kw = dict(plant=b58(), use_preview=True, preview_h_s=E.PREVIEW_H_S, reward_knock=E.REWARD_KNOCK_DEFAULT)
        got = BD.battery_episode(C.p_neutral, k, grade, 1, **kw)
        self.assertEqual(sorted(got), sorted(want))
        self.assertEqual(got, want)
        self.assertFalse(np.any(np.isnan(want["act_climb"])))      # the climb's steps were counted (_run's NaN if none)
        other = BD.battery_episode(C.p_neutral, k, grade, 5, **kw)                  # the control
        self.assertNotEqual(other["ret"], want["ret"])


# =====================================================================================================
class Logged(unittest.TestCase):
    def test_the_counts_and_the_verdict_are_run_s(self):
        counts = BD.LoggedCounts()
        hot = BD.LOGGED_ABOVE_C + 273.15
        cold = LC.COLD_C + 273.15
        steps = ((10.0, 5.0, 5.0, hot + 1.0, cold - 1.0),     # no demand step; above for the agent only
                 (100.0, 94.9, 99.0, hot - 0.5, cold + 1.0),  # the agent alone short
                 (100.0, 94.9, 94.0, hot - 1.0, hot + 1.0),   # both short; the reference's turbine above
                 (100.0, 95.0, 99.0, hot - 1.0, cold - 1.0))  # nobody short, at the boundary
        for k, (req, got, base, turb, turb_base) in enumerate(steps, start=1):
            counts(FakeEnv(k, turb_base), None, {"torque_req": req, "torque": got, "torque_base": base, "t_turb": turb})
        out = dict(steps=4, fuel=101.0, fuel_base=100.0, damage=1.0, damage_thermal=0.5, damage_base=2.0,
                   peak_turb=900.0)
        row = counts.row(out)
        self.assertEqual((row["demand_steps"], row["short_agent"], row["short_base"], row["short_agent_only"]),
                         (3, 2, 1, 1))
        self.assertEqual((row["s_above"], row["s_above_base"], row["cold_steps"]), (1, 1, 2))
        self.assertEqual(row["act_cold"], [2.5] * 5)
        self.assertAlmostEqual(row["peak_turb_base"], hot + 1.0 - 273.15)
        t_ok, f_ok = BD.logged_verdict(dict(row, short_agent_only=0, demand_steps=100, fuel=100.5, fuel_base=100.0))
        self.assertEqual((t_ok, f_ok), (True, True))
        self.assertEqual(BD.logged_verdict(dict(row, short_agent_only=1, demand_steps=100))[0], True)
        self.assertEqual(BD.logged_verdict(dict(row, short_agent_only=2, demand_steps=100))[0], False)   # control
        self.assertEqual(BD.logged_verdict(dict(row, fuel=101.5, fuel_base=100.0))[1], False)             # control

    def test_the_literals_are_run_s(self):
        with open(os.path.join(HERE, "logged_check.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual((BD.LOGGED_ABOVE_C, BD.LOGGED_DT), (850.0, 1.0))
        self.assertIn('above_a += info["t_turb"] - 273.15 > 850.0', src)
        self.assertIn('plant=engines.get("b58"), dt=1.0, seed=seed, use_preview=preview)', src)
        self.assertIn("sa = info[\"torque\"] < (1.0 - EE.TRACK_TOL) * req", src)
        self.assertIn('row["T"] = short_only <= T_LIMIT * max(demand, 1)', src)
        self.assertIn('row["F"] = e["fuel"] <= F_LIMIT * e["fuel_base"]', src)


# =====================================================================================================
class Cli(unittest.TestCase):
    def refused(self, argv, text):
        with self.assertRaises(SystemExit) as cm:
            BD.main(argv)
        self.assertIn(text, str(cm.exception))

    def test_its_refusals_and_the_control(self):
        out = TSP.fresh("cli")
        base = ["--engine", "b58", "--set", TSP.fresh("cli_set"), "--reward-knock", "out"]
        self.refused(["locked"] + base + ["--out", out, "--grades", "x.json"], "--grades is the battery's")
        self.refused(["battery"] + base + ["--out", out], "--grades is the battery's")
        self.refused(["locked"] + base + ["--out", os.path.join(HERE, "results")], "lies inside the repository")
        with open(os.path.join(out, "b58h_logged.json"), "w", encoding="utf-8") as fh:
            fh.write("{}")
        self.refused(["logged"] + base + ["--out", out], "b58h_logged.json exists")
        with mock.patch.object(V, "committed_train_backend", lambda engine, *, root: FP.BACKEND_CYCLE):
            self.refused(["locked"] + base + ["--out", out], "holds no run folder")      # the control


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""test_scoring_protocol.py -- evaluate.py's decision-34 protocol (ORDER step 16, commit V; interface sheet 8).

    python -B test_scoring_protocol.py        a few minutes; exit code 0 when all pass

Rows 95, 103 (4), 112, 117, 118, 143 (5), 146 (3) and 147 (5), (10) and (11) of results/VALIDATION_DECISIONS.md,
built by docs/build_step_2/ORDER_TO_TRAINING.md step 16. Every check has its control (mistake 12), and every
refusal is asserted by its own text, so that another refusal cannot stand in for it. Nothing here trains: an
agent is a SYNTHETIC folder of an untrained SAC network saved as decision 29's run leaves one (five snapshots,
final.zip, the manifest training_recipe writes), its actor's output bias moved between saves so that every
saved network acts differently, with meta.json and config.json written by hand, in a temporary folder outside
the repository. The roads are SYNTHETIC (short, or epa_roads.generate's from a SYNTHETIC seed). No EPA table,
held-out row or logs/ file is read; roads.json and redraws.json are read where a test says REAL.

  Names           the constants the study's analysis and logged_check share are theirs; evaluate.py never names
                  the analysis, never prints its pilot factor; PROTOCOLS keeps two entries; d34 is
                  fingerprint's protocol (REAL)
  Episodes        run_episode keeps its seven keys in their order and equals the loop it had before V, step for
                  step (the frozen copy below); _drive counts demand and short steps by DEMAND_NM and TRACK_TOL,
                  at the boundary too; the arm's H reaches the environment, the blinded arm's is None
  Roads           run_road_episode pins the road's seed and weights; a run of the wrong length is refused
  Practice        practice_set: a SYNTHETIC record passes, each refusal by its text; the REAL record's ten
  Decision34Roads decision34_roads in a SYNTHETIC git repository: version 6's roads are scored and version 5's
                  are not, its slots in the provenance; each refusal (a road changed, no version 6, the
                  re-verification record's verdict, plant_sha, head and absence)
  Arms            arm_of: the blinded and the sighted arm, and each refusal
  ReadAgents      read_agents on SYNTHETIC runs, and its refusals
  Environment     environment_problems: one environment, each difference named, a missing value named (meta.json's
                  numpy, which no schema-4 meta.json records, excepted)
  Backend         committed_train_backend in a SYNTHETIC git repository: the backend record's 'cycle'; absent,
                  not committed, no backend, another schema; backend_problems
  Pairing         pairing_problems: row 117's pairs, an unpaired seed, a FATAL field that differs, no blind arm
  Average         load_agent scores the mean of the five snapshots, not final.zip; each refusal of
                  average_lines
  Transfer        check_transfer, the declared transfer route: scenario and episodes_sha printed both ways (the
                  printed text checked) and let through, every other FATAL field refused, no force
  Documents       scores_document passes the study's analysis's own validator, the delivery figures in its
                  provenance (beside D they would be refused, by the validator's text); write_once_json, a NaN
                  refused by json's text before anything is written; merge_scores and its refusals
  Records         rescore_from_records gives an episode's damage back; write_records' files
  ScoreSet        score_set gives the same rows at jobs 1 and 2; its refusals
  Pilot           pilot_spread's s_p with ddof 1; its refusals
  Cli             main()'s refusals of decision 34's flags, each by its text
  EndToEnd        main() on decision 34's protocol and on its practice route, from the command line to the
                  documents, in a SYNTHETIC git repository holding the roads and backend records: the scores
                  pass the analysis's validator and carry train_backend, the environment, the agents, the
                  machine that scored (versions, platform, device: what merge_scores compares, row 143 (4);
                  the control: the document merges as another engine, and on another device is refused) and
                  the rescoring keys; each score is the checkpoint average at its own H (the control: the
                  default H scores otherwise); the practice document, its machine, its s_p printed, its
                  provenance without the test set's episodes_sha; the refusals of an agent of another
                  train_backend (backend_problems' text), of a repository without the backend record, and of
                  the reward the agents did not train with
"""
import contextlib
import copy
import hashlib
import inspect
import io
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

import check_premise as C  # noqa: E402
import engine_env as E  # noqa: E402
import engines  # noqa: E402
import epa_freeze as EF  # noqa: E402
import epa_roads as ER  # noqa: E402
import evaluate as V  # noqa: E402
import fingerprint as FP  # noqa: E402
import four_engine_roads as FER  # noqa: E402
import training_recipe as TR  # noqa: E402

SYNTHETIC_SEED = 271828              # SYNTHETIC: below 2**32, never roads_seed (row 96)
TAU_S = 47.0                         # SYNTHETIC tau for the SYNTHETIC roads record, never the B58's
TOTAL = 9 * TR.DECISION_29_WINDOW    # decision 29's 450 000 steps
STATE = {}


def setUpModule():
    tmp = tempfile.mkdtemp(prefix="scoring_protocol_test_")
    assert not FER.inside_repository(tmp), tmp
    STATE["tmp"] = tmp
    STATE["record"] = FER.read_roads_record(FER.write_synthetic_record(
        os.path.join(tmp, "roads.SYNTHETIC.json"), SYNTHETIC_SEED, taus={"b58": TAU_S}, ratios=[0.5, 1.5]))


def tearDownModule():
    shutil.rmtree(STATE.get("tmp", ""), ignore_errors=True)


def b58():
    return engines.get("b58")


def fresh(name):
    path = tempfile.mkdtemp(prefix=name + "_", dir=STATE["tmp"])
    return path


def git(root, *args):
    r = subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@local", *args], cwd=root,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


def put_json(root, rel, obj):
    path = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh)
    return path


def short_cycle(n, *, onset):
    """A SYNTHETIC cycle, the environment's form: the roads' launch and speed, n one-second samples, a 10 %
    climb from `onset` s (epa_roads.climb_profile), 315 K."""
    t, v = ER.time_and_speed()
    t, v = t[:n], v[:n]
    return {"t": t, "v_mps": v, "grade": ER.climb_profile(t, float(onset), 30.0, 0.10), "t_amb": ER.T_AMB_K,
            "p_baro": ER.P_BARO_KPA, "humidity": ER.HUMIDITY}


def short_road(n, *, k, seed, weights, onset):
    """The same cycle as a road of the roads step (lists, t_amb per sample)."""
    c = short_cycle(n, onset=onset)
    return {"k": k, "episode_seed": seed, "weights": [float(w) for w in weights], "dt": 1.0,
            "cycle": {"t": [float(x) for x in c["t"]], "v_mps": [float(x) for x in c["v_mps"]],
                      "grade": [float(x) for x in c["grade"]], "t_amb": [ER.T_AMB_K] * n, "p_baro": ER.P_BARO_KPA,
                      "humidity": ER.HUMIDITY}}


def h_of(ratio):
    return FER.horizon_s(STATE["record"], "b58", ratio)


def synthetic_meta(*, seed, ratio, seed_kind="REAL", **changes):
    """meta.json as train.py writes its keys for a decision-34 run, SYNTHETIC values; ratio None is the
    blinded arm."""
    recipe = {"lr_schedule": "last-third", "checkpoint_average": TR.DECISION_29_WINDOW,
              "scored_share": {"every": 10, "roads_sha": "0" * 64, "seed_kind": seed_kind}}
    sighted = ratio is not None
    if sighted:
        recipe.update(horizon_ratio=float(ratio), preview_h_s=h_of(ratio))
    meta = {"schema": FP.SCHEMA_VERSION, "seed": seed, "use_preview": sighted,
            "preview_h_s": h_of(ratio) if sighted else None, "train_backend": FP.BACKEND_CYCLE,
            "python": "3.13.2", "train_recipe": recipe}
    meta.update(changes)
    return meta


def synthetic_config(**changes):
    cfg = {"versions": {"python": "3.13.2", "stable_baselines3": "sb3-x", "torch": "torch-x", "gymnasium": "gym-x",
                        "numpy": "np-x"},
           "device": "cpu", "machine": {"system": "Windows", "processor": "SYNTHETIC", "cpus": 20},
           "recipe": {"learning_rate_at_end": 0.0}}
    cfg.update(changes)
    return cfg


def make_run(folder, *, seed, ratio, perturb=0.05, window=TR.DECISION_29_WINDOW, final_steps=TOTAL, meta=None):
    """A SYNTHETIC decision-34 run folder, named as train.py names it (four_engine_roads.run_tag): an untrained
    SAC network saved at the five snapshot steps and as final.zip, its actor's output bias moved by `perturb`
    before each save, num_timesteps TOTAL (final_steps for final.zip), training_recipe's manifest over
    `window`, and meta.json and config.json."""
    import torch
    from stable_baselines3 import SAC
    run = os.path.join(folder, FER.run_tag(seed, use_preview=ratio is not None, ratio=ratio))
    os.makedirs(os.path.join(run, TR.SNAPSHOT_DIR))
    p = b58()
    env = E.SupervisoryTunerEnv(E.locked_climb(p, duration=30.0, dt=1.0), plant=p, dt=1.0, seed=0)
    model = SAC("MlpPolicy", env, seed=seed, buffer_size=64, learning_starts=0, device="cpu", verbose=0)
    for step in TR.snapshot_steps(TOTAL, window):
        with torch.no_grad():
            model.actor.mu.bias.add_(perturb)
        model.num_timesteps = TOTAL
        model.save(os.path.join(run, TR.SNAPSHOT_DIR, TR.snapshot_name(step)))
    with torch.no_grad():
        model.actor.mu.bias.add_(perturb)
    model.num_timesteps = final_steps
    model.save(os.path.join(run, "final"))
    TR.write_manifest(run, total_steps=TOTAL, window=window)
    put_json(run, "meta.json", synthetic_meta(seed=seed, ratio=ratio) if meta is None else meta)
    put_json(run, "config.json", synthetic_config())
    return run


def runs():
    """One SYNTHETIC seed pair, blinded and sighted at r = 1.5, made once; their networks differ (perturb)."""
    if "runs" not in STATE:
        folder = fresh("runs")
        STATE["runs"] = (make_run(folder, seed=7, ratio=None), make_run(folder, seed=7, ratio=1.5, perturb=0.07))
    return STATE["runs"]


def frozen_run_episode(policy, cycle, seed, weights, *, plant, use_preview, reward_knock):
    """evaluate.run_episode's body as it stood before V (P's tree), copied verbatim but for the cycle it is
    handed: the reference _drive must reproduce step for step."""
    env = E.SupervisoryTunerEnv(cycle, plant=plant, dt=V.DT, seed=seed, use_preview=use_preview,
                                reward_knock=reward_knock)
    obs, _ = env.reset(seed=seed)
    env.w = np.asarray(weights, dtype=np.float32)
    obs = env._obs()
    ret, peak, thermal = 0.0, 0.0, 0.0
    while True:
        a = policy(env, obs)
        obs, r, term, trunc, info = env.step(a)
        ret += r
        peak = max(peak, info["t_turb"])
        thermal += E.damage_rate(info["t_turb"], info["t_oil"], cal=plant.engine.damage) * env.dt
        if term or trunc:
            break
    s = info["episode_summary"]
    return dict(ret=ret, damage=s["damage"], damage_thermal=thermal, fuel=s["fuel"],
                torque_viol=s["torque_viol"], peak_turb=peak - 273.15, knock=s["knock_events"])


class StubEnv:
    """An environment of scripted steps for _drive: each info as given, the last carrying the summary."""

    def __init__(self, infos):
        self.infos, self.i, self.dt = infos, 0, 1.0

    def _obs(self):
        return np.zeros(E.OBS_DIM, dtype=np.float32)

    def step(self, action):
        info = dict(self.infos[self.i])
        self.i += 1
        last = self.i == len(self.infos)
        if last:
            info["episode_summary"] = dict(damage=1.0, fuel=2.0, torque_viol=0.0, knock_events=0, fuel_base=3.0,
                                           damage_base=4.0)
        return self._obs(), 0.0, False, last, info


def stub_info(req, got):
    return {"torque_req": req, "torque": got, "t_turb": 900.0, "t_oil": 380.0, "ki": 0.0}


# =====================================================================================================
class Names(unittest.TestCase):
    def test_the_shared_constants_are_their_owners(self):
        import four_engine_analysis as A
        import logged_check as LC
        self.assertEqual(V.SCORES_SCHEMA, A.SCORES_SCHEMA)
        self.assertEqual(V.with_knock_label(), A.WITH_KNOCK_LABEL)
        self.assertEqual(V.DEMAND_NM, LC.DEMAND_NM)
        self.assertEqual(V.READING_KEYS, {"no_knock": "damage_thermal", "with_knock": "damage"})
        self.assertEqual(tuple(V.READING_KEYS), A.READINGS)
        self.assertEqual(V.TRANSFER_EXEMPT, ("scenario", "episodes_sha"))
        self.assertTrue(set(V.TRANSFER_EXEMPT) < set(FP.FATAL))
        self.assertEqual(sorted(V.PROTOCOLS), ["d2", "phase-d"])         # PROTOCOLS stays two entries
        self.assertNotIn(V.DECISION_34, V.PROTOCOLS)
        self.assertEqual(V.N_PRACTICE, ER.N_PRACTICE)
        self.assertEqual(V.N_D34_ROADS, ER.N_ROADS)

    def test_evaluate_never_names_the_analysis_nor_prints_its_factor(self):
        with open(os.path.join(HERE, "evaluate.py"), encoding="utf-8") as fh:
            src = fh.read()
        for text in ("four_engine_analysis", "1.5576", "pilot_factor"):
            self.assertNotIn(text, src)
        self.assertIn("SCORES_SCHEMA", src)                # the control: the scan reads the file it means

    def test_the_report_never_writes_phase_d_s_cut_line(self):
        """plot_agent_pairs.CUT_ROW and analyse_phase_d read "cuts median damage" lines: decision 34's report
        prints none (evaluate.py's DAMAGE TWO WAYS)."""
        rows = fake_rows(V.N_D34_ROADS, [0, 1], ["0.5", "1.5"])
        say = V.d34_report("b58", rows, header=V.D34_HEADER, reading="version 6", ratios=["0.5", "1.5"], lines=[])
        self.assertTrue(say[0].startswith(V.D34_HEADER))
        self.assertFalse([line for line in say if "cuts median damage" in line])
        self.assertEqual(len([line for line in say if line.startswith("    seed ")]), 4)   # d per ratio and seed

    def test_d34_is_fingerprints_protocol_REAL(self):
        if not os.path.isfile(os.path.join(HERE, *ER.REDRAWS_REL.split("/"))):
            self.skipTest("no redraws.json in this tree")
        live = V.live_decision34(b58(), preview_h_s=None, reward_knock=False, train_backend=FP.BACKEND_CYCLE)
        self.assertEqual(live["scenario"]["protocol"], "decision-34")
        self.assertEqual(live["scenario"]["reading"], V.REDRAW_READING)
        self.assertEqual((live["eval_dt"], live["eval_duration"]), (ER.DT, ER.DURATION_S))
        with self.assertRaises(ValueError) as cm:
            FP.plant_fingerprint("d35", plant=b58(), train_backend=FP.BACKEND_CYCLE, score_backend=FP.BACKEND_CYCLE,
                                 preview_h_s=None, reward_knock=False)
        self.assertIn("unknown protocol 'd35'", str(cm.exception))

    def test_the_two_readings_of_redraws_json_are_named_as_written_REAL(self):
        path = os.path.join(HERE, *ER.REDRAWS_REL.split("/"))
        if not os.path.isfile(path):
            self.skipTest("no redraws.json in this tree")
        self.assertEqual(sorted(ER.load_record(path)["readings"]), sorted([V.REDRAW_READING, V.VERSION_5_READING]))


# =====================================================================================================
class Episodes(unittest.TestCase):
    W = (0.6, 0.25, 0.15)

    def test_run_episode_keeps_its_keys_and_its_loop(self):
        cycle = short_cycle(12, onset=4)

        def fake_cycle(road, *, plant):
            return copy.deepcopy(cycle)
        with mock.patch.object(V, "episode_cycle", fake_cycle):
            got = V.run_episode(C.p_grade_now, 1003, self.W, True, plant=b58())
        self.assertEqual(tuple(got), V.EPISODE_KEYS)
        want = frozen_run_episode(C.p_grade_now, copy.deepcopy(cycle), 1003, self.W, plant=b58(), use_preview=True,
                                  reward_knock=E.REWARD_KNOCK_DEFAULT)
        self.assertEqual(got, want)
        other = frozen_run_episode(C.p_grade_now, copy.deepcopy(cycle), 1003, (0.5, 0.3, 0.2), plant=b58(),
                                   use_preview=True, reward_knock=E.REWARD_KNOCK_DEFAULT)
        self.assertNotEqual(other["ret"], got["ret"])                      # the control: the weights reach it

    def test_drive_counts_the_demand_and_the_short_steps(self):
        infos = [stub_info(10.0, 5.0), stub_info(50.0, 49.0), stub_info(100.0, 94.0), stub_info(100.0, 95.0),
                 stub_info(100.0, 96.0)]
        out = V._drive(StubEnv(infos), lambda env, obs: np.zeros(5, np.float32), plant=b58(), record=None,
                       observe=None)
        self.assertEqual((out["steps"], out["demand_steps"], out["short_steps"]), (5, 4, 1))
        self.assertEqual((out["fuel_base"], out["damage_base"]), (3.0, 4.0))
        self.assertEqual(out["trace"]["t_turb"], [900.0] * 5)
        infos[3] = stub_info(100.0, 94.9)                                   # the control: past the tolerance
        out = V._drive(StubEnv(infos), lambda env, obs: np.zeros(5, np.float32), plant=b58(), record=None,
                       observe=None)
        self.assertEqual(out["short_steps"], 2)
        self.assertEqual(V.DEMAND_NM, 40.0)
        self.assertEqual(V.TRACK_TOL, E.TRACK_TOL)

    def test_the_arms_H_reaches_the_environment(self):
        seen = {}

        def observe(env, action, info):
            seen.setdefault("preview_s", env.preview_s)
            seen.setdefault("preview", list(env._preview()))
            seen.setdefault("use_preview", env.use_preview)
        cycle = short_cycle(4, onset=0)
        h = h_of(0.5)

        def run(use_preview, preview_h_s):
            seen.clear()
            V.run_cycle_episode(C.p_neutral, copy.deepcopy(cycle), 1000, self.W, plant=b58(), dt=1.0,
                                use_preview=use_preview, preview_h_s=preview_h_s, reward_knock=False, inlet_kpa=None,
                                record=None, observe=observe)
            return dict(seen)
        self.assertEqual(run(True, h)["preview_s"], E.preview_samples(h))
        self.assertEqual(run(True, E.PREVIEW_H_S)["preview_s"], E.PREVIEW_S)           # the control
        self.assertNotEqual(E.preview_samples(h), E.PREVIEW_S)
        blind = run(False, None)
        self.assertEqual((blind["use_preview"], blind["preview"]), (False, [0.0] * 4))
        for use_preview, h_s, text in ((True, None, "a sighted arm's H is a positive finite float"),
                                       (True, 30, "a sighted arm's H is a positive finite float"),
                                       (False, h, "the blinded arm's H is None")):
            with self.assertRaises(ValueError) as cm:
                run(use_preview, h_s)
            self.assertIn(text, str(cm.exception))


# =====================================================================================================
class Roads(unittest.TestCase):
    def test_the_roads_seed_and_weights_are_pinned(self):
        road = short_road(6, k=3, seed=1004, weights=(0.58, 0.04, 0.38), onset=2)
        seen = []

        def policy(env, obs):
            seen.append(env.w.copy())
            return C.NEUTRAL
        out = V.run_road_episode(policy, road, plant=b58(), use_preview=False, preview_h_s=None, reward_knock=False)
        self.assertEqual(out["steps"], 5)
        self.assertTrue(np.array_equal(seen[0], np.asarray(road["weights"], dtype=np.float32)))
        env = E.SupervisoryTunerEnv(ER.env_cycle(road), plant=b58(), dt=1.0, seed=1004, use_preview=False)
        env.reset(seed=1004)
        self.assertFalse(np.array_equal(env.w, seen[0]))                   # the control: the unpinned draw

    def test_a_run_of_the_wrong_length_is_refused(self):
        road = short_road(6, k=3, seed=1004, weights=(0.58, 0.04, 0.38), onset=2)
        with mock.patch.object(V, "run_cycle_episode", lambda *a, **k: {"steps": 4}):
            with self.assertRaises(ValueError) as cm:
                V.run_road_episode(C.p_neutral, road, plant=b58(), use_preview=False, preview_h_s=None,
                                   reward_knock=False)
        self.assertIn("the episode ran 4 steps, and a road of 6 samples runs 5", str(cm.exception))
        with mock.patch.object(V, "run_cycle_episode", lambda *a, **k: {"steps": 5}):     # the control
            self.assertEqual(V.run_road_episode(C.p_neutral, road, plant=b58(), use_preview=False, preview_h_s=None,
                                                reward_knock=False), {"steps": 5})


# =====================================================================================================
class Practice(unittest.TestCase):
    def setUp(self):
        self.record = {"practice": ER.practice_roads(SYNTHETIC_SEED)}

    def refused(self, record, text):
        with self.assertRaises(SystemExit) as cm:
            V.practice_set(record)
        self.assertIn(text, str(cm.exception))

    def test_the_SYNTHETIC_practice_set_and_each_refusal(self):
        self.assertEqual(V.practice_set(self.record), self.record["practice"])          # the control
        r = copy.deepcopy(self.record)
        r["practice"][3]["k"] = 4
        self.refused(r, "practice road 3 has k 4")
        r = copy.deepcopy(self.record)
        r["practice"][2]["episode_seed"] = 4009
        self.refused(r, "practice road 2 has episode seed 4009, not epa_roads.PRACTICE_SEEDS[2] 4002")
        r = copy.deepcopy(self.record)
        r["practice"][5]["weights"] = r["practice"][5]["weights"][:2]
        self.refused(r, "practice road 5's weights")
        r = copy.deepcopy(self.record)
        r["practice"] = r["practice"][:9]
        self.refused(r, "holds 9 practice roads, not row 96's 10")
        r = copy.deepcopy(self.record)
        r["practice"][0]["episode_seed"] = 1000
        with mock.patch.object(ER, "PRACTICE_SEEDS", (1000,) + tuple(ER.PRACTICE_SEEDS[1:])):
            self.refused(r, "seeds [1000] are the frozen twenty's")

    def test_the_REAL_practice_set(self):
        path = os.path.join(HERE, *ER.ROADS_REL.split("/"))
        if not os.path.isfile(path):
            self.skipTest("no roads.json in this tree")
        roads = V.practice_set(ER.load_record(path))
        self.assertEqual([r["episode_seed"] for r in roads], list(ER.PRACTICE_SEEDS))


# =====================================================================================================
def build_d34_repo(root, *, redraws=True, v6_change=None, reverify=True, verdict="EQUAL", plant_sha=None,
                   head=None, extra=None, backend=None):
    """A SYNTHETIC git repository holding what decision34_roads reads: evaluate.py (its EPISODES, read as text),
    roads.json of epa_roads.generate's twenty roads, redraws.json with version 6 redrawing one climb of road 3
    and version 5 two others (roads 5 and 9), and the re-verification record, each committed. `extra` adds
    keys to roads.json (EndToEnd's: what read_roads_record reads, and the practice roads); `backend`, when
    given, is committed as results/EPA_BACKEND.json. Returns (original roads, version 6's, version 5's)."""
    os.makedirs(root)
    shutil.copyfile(os.path.join(HERE, "evaluate.py"), os.path.join(root, "evaluate.py"))
    roads = ER.generate(SYNTHETIC_SEED)
    rec = dict({"schema": ER.ROADS_SCHEMA, "seed_kind": "SYNTHETIC", "design": ER.design(), "roads": roads},
               **(extra or {}))
    rpath = put_json(root, ER.ROADS_REL, rec)
    if backend is not None:
        put_json(root, engines.BACKEND_REL, backend)
    v6 = copy.deepcopy(roads)
    s3 = roads[3]["climbs"][0]["slot"]
    v6[3] = ER.with_grade(roads[3], s3, 0.111)
    if v6_change is not None:
        v6_change(v6)
    v5 = copy.deepcopy(roads)
    s5, s9 = roads[5]["climbs"][0]["slot"], roads[9]["climbs"][-1]["slot"]
    v5[5], v5[9] = ER.with_grade(roads[5], s5, 0.119), ER.with_grade(roads[9], s9, 0.101)

    def slot(s, k, g):
        return {"slot": s, "road": k, "redraws": 1, "discarded": 0, "stopped_at": None, "kept": "redraw 1",
                "kept_grade": g, "gear_sensitive": [], "thin_on": [], "candidates": [{"SYNTHETIC": "not carried"}]}
    if redraws:
        put_json(root, ER.REDRAWS_REL, {
            "schema": ER.REDRAWS_SCHEMA, "roads_sha": ER.roads_sha(rpath), "seed_kind": "SYNTHETIC",
            "dropped": ["ford_27tt"],
            "readings": {V.REDRAW_READING: {"gating": ["b58"], "failing": [s3], "slots": [slot(s3, 3, 0.111)],
                                            "roads": v6},
                         V.VERSION_5_READING: {"gating": list(ER.ENGINES), "failing": [s5, s9],
                                               "slots": [slot(s5, 5, 0.119), slot(s9, 9, 0.101)], "roads": v5}}})
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "SYNTHETIC roads")
    if reverify:
        dpath = os.path.join(root, *ER.REDRAWS_REL.split("/"))
        put_json(root, FER.REVERIFY_REL, {
            "verdict": verdict, "roads_sha": ER.roads_sha(rpath),
            "redraws_sha": ER.roads_sha(dpath) if os.path.isfile(dpath) else None,
            "head": git(root, "rev-parse", "HEAD") if head is None else head,
            "plants": {"b58": {"plant_sha_now": EF.plant_sha("b58") if plant_sha is None else plant_sha}}})
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "SYNTHETIC re-verification record")
    return roads, v6, v5


class Decision34Roads(unittest.TestCase):
    def refused(self, text, **kw):
        root = os.path.join(fresh("d34"), "repo")
        build_d34_repo(root, **kw)
        with self.assertRaises(SystemExit) as cm:
            V.decision34_roads(root=root)
        self.assertIn(text, str(cm.exception))

    def test_version_6_is_scored_and_version_5_reported(self):
        root = os.path.join(fresh("d34"), "repo")
        roads, v6, v5 = build_d34_repo(root)
        got, prov = V.decision34_roads(root=root)
        self.assertEqual(got, json.loads(json.dumps(v6)))
        self.assertNotEqual(got[3], json.loads(json.dumps(roads[3])))           # version 6's redraw is applied
        for k in (5, 9):                                                         # version 5's are not
            self.assertEqual(got[k], json.loads(json.dumps(roads[k])))
            self.assertNotEqual(got[k], json.loads(json.dumps(v5[k])))
        self.assertEqual((prov["protocol"], prov["reading"], prov["dropped"]), (V.DECISION_34, "version 6", ["ford_27tt"]))
        self.assertEqual([s["kept_grade"] for s in prov["redrawn_version_6"]], [0.111])
        v5p = prov["version_5_reading"]
        self.assertEqual((v5p["name"], v5p["scored"], [s["road"] for s in v5p["slots"]]),
                         (V.VERSION_5_READING, False, [5, 9]))
        self.assertNotIn("candidates", v5p["slots"][0])
        self.assertEqual(prov["reverify"]["path"], FER.REVERIFY_REL)
        self.assertEqual(prov["arrays_sha256"], ER.arrays_sha256(got))
        self.assertEqual(prov["scenario"]["reading"], "version 6")

    def test_a_road_changed_outside_its_slots_is_refused(self):
        def change(v6):
            v6[7]["cycle"]["grade"][400] += 1e-3
        self.refused("road 7 of the version 6 reading is not roads.json's road 7", v6_change=change)

    def test_without_redraws_json_the_first_draw_is_refused(self):
        self.refused("they are the 'first draw' reading, and the scores are computed on the version 6 set only",
                     redraws=False)

    def test_the_re_verification_record(self):
        self.refused("no current re-verification record", reverify=False)
        self.refused("its verdict is 'DIFFERENT', not 'EQUAL'", verdict="DIFFERENT")
        self.refused("b58: its plant_sha_now 'SYNTHETIC' is not this tree's plant_sha", plant_sha="SYNTHETIC")
        self.refused("cannot be placed in HEAD's history", head="f" * 40)


# =====================================================================================================
class Arms(unittest.TestCase):
    def arm(self, name, meta):
        return V.arm_of(os.path.join("runs", "SYNTHETIC", name), meta, STATE["record"], "b58")

    def refused(self, name, meta, text):
        with self.assertRaises(SystemExit) as cm:
            self.arm(name, meta)
        self.assertIn(text, str(cm.exception))

    def test_the_blinded_and_the_sighted_arm(self):
        self.assertEqual(self.arm("blind_seed7", synthetic_meta(seed=7, ratio=None)), ("blind", None))
        self.assertEqual(self.arm("sighted_r1.5_seed7", synthetic_meta(seed=7, ratio=1.5)), ("sighted_r1.5", 1.5 * TAU_S))
        self.assertEqual(self.arm("sighted_r0.5_seed7", synthetic_meta(seed=7, ratio=0.5)), ("sighted_r0.5", 0.5 * TAU_S))

    def test_each_refusal(self):
        h = h_of(1.5)
        self.refused("sighted_r1.5_seed7", synthetic_meta(seed=7, ratio=1.5, preview_h_s=float(np.nextafter(h, 1e9))),
                     "is not r x tau")
        self.refused("sighted_r0.5_seed7", synthetic_meta(seed=7, ratio=1.5), "its folder is 'sighted_r0.5_seed7'")
        self.refused("sighted_r1.5_seed7", synthetic_meta(seed=7, ratio=1.5, seed_kind="SYNTHETIC"), "not 'REAL'")
        meta = synthetic_meta(seed=7, ratio=1.5)
        del meta["train_recipe"]["horizon_ratio"]
        self.refused("sighted_r1.5_seed7", meta, "records no horizon_ratio")
        self.refused("blind_seed7", synthetic_meta(seed=7, ratio=None, preview_h_s=30.0),
                     "a blinded agent's preview_h_s is None")
        meta = synthetic_meta(seed=7, ratio=1.5)
        meta["train_recipe"]["horizon_ratio"] = 2.0
        self.refused("sighted_r2_seed7", meta, "is not one of the roads record's ratios")
        self.refused("blind_seed7", synthetic_meta(seed=7.0, ratio=None), "records seed 7.0, not an int")


class ReadAgents(unittest.TestCase):
    def test_the_runs_and_the_refusals(self):
        blind, sighted = runs()
        got = V.read_agents([blind, sighted + os.sep], roads_rec=STATE["record"], engine="b58")
        self.assertEqual([(x["arm"], x["seed"], x["H_s"], x["r"]) for x in got],
                         [("blind", 7, None, None), ("sighted_r1.5", 7, h_of(1.5), 1.5)])
        self.assertEqual(got[1]["path"], sighted)
        with self.assertRaises(SystemExit) as cm:
            V.read_agents([blind, blind], roads_rec=STATE["record"], engine="b58")
        self.assertIn("is the same arm and seed (blind, seed 7)", str(cm.exception))
        folder = fresh("noconfig")
        run = os.path.join(folder, "blind_seed3")
        put_json(run, "meta.json", synthetic_meta(seed=3, ratio=None))
        with self.assertRaises(SystemExit) as cm:
            V.read_agents([run], roads_rec=STATE["record"], engine="b58")
        self.assertIn("has no config.json", str(cm.exception))
        put_json(run, "meta.json", synthetic_meta(seed=3, ratio=None, schema=3))
        put_json(run, "config.json", synthetic_config())
        with self.assertRaises(SystemExit) as cm:
            V.read_agents([run], roads_rec=STATE["record"], engine="b58")
        self.assertIn("fingerprint schema 3", str(cm.exception))


# =====================================================================================================
class Environment(unittest.TestCase):
    def test_one_environment_and_each_difference(self):
        meta, cfg = synthetic_meta(seed=1, ratio=None), synthetic_config()
        same = [("a", meta, cfg), ("b", copy.deepcopy(meta), copy.deepcopy(cfg))]
        self.assertEqual(V.environment_problems(same), [])                       # the control
        other = copy.deepcopy(cfg)
        other["versions"]["torch"] = "torch-y"
        probs = V.environment_problems([("a", meta, cfg), ("b", meta, other)])
        self.assertEqual(probs, ["config.json versions.torch: b 'torch-y', a 'torch-x'"])
        probs = V.environment_problems([("a", meta, cfg), ("b", dict(meta, python="3.12.0"), cfg)])
        self.assertEqual(probs, ["meta.json python: b '3.12.0', a '3.13.2'"])
        probs = V.environment_problems([("a", meta, cfg), ("b", meta, dict(cfg, device="cuda"))])
        self.assertEqual(probs, ["config.json device: b 'cuda', a 'cpu'"])
        gone = copy.deepcopy(cfg)
        del gone["machine"]["cpus"]
        self.assertEqual(V.environment_problems([("a", meta, gone)]), ["a: its config.json machine.cpus is not recorded"])
        # meta.json's python is required too; its numpy, which no schema-4 meta.json records, is not (the
        # control: synthetic_meta holds no numpy, and `same` above passed)
        self.assertNotIn("numpy", meta)
        self.assertEqual(V.ENV_UNRECORDED, ("meta.json numpy",))
        no_python = {k: v for k, v in meta.items() if k != "python"}
        self.assertEqual(V.environment_problems([("a", no_python, cfg)]), ["a: its meta.json python is not recorded"])
        self.assertEqual(V.environment_problems([("a", meta, None)]), ["a: no config.json, so its training environment "
                                                                       "is unknown"])


# =====================================================================================================
def backend_record(**b58_entry):
    """Tb's record as engines.committed_record reads it, SYNTHETIC: the B58 kept on the cycle model, n null."""
    entry = dict({"drop": False, "backend": FP.BACKEND_CYCLE, "reason": None}, **b58_entry)
    return {"schema": engines.BACKEND_SCHEMA, "n": None, "in_test": ["b58"], "engines": {"b58": entry}}


class Backend(unittest.TestCase):
    def repo(self, record):
        root = os.path.join(fresh("backend"), "repo")
        os.makedirs(root)
        git(root, "init", "-q")
        if record is not None:
            put_json(root, engines.BACKEND_REL, record)
            git(root, "add", "-A")
            git(root, "commit", "-q", "-m", "SYNTHETIC backend record")
        return root

    def record(self, **b58_entry):
        return backend_record(**b58_entry)

    def refused(self, root, text):
        with self.assertRaises(SystemExit) as cm:
            V.committed_train_backend("b58", root=root)
        self.assertIn(text, str(cm.exception))

    def test_the_backend_record_names_the_train_backend(self):
        root = self.repo(self.record())
        self.assertEqual(V.committed_train_backend("b58", root=root), FP.BACKEND_CYCLE)   # the control
        self.refused(self.repo(None), f"no {engines.BACKEND_REL}")
        with open(os.path.join(root, *engines.BACKEND_REL.split("/")), "a", encoding="utf-8") as fh:
            fh.write(" ")
        self.refused(root, "is not committed at HEAD")
        self.refused(self.repo(self.record(backend=None)), "keeps no backend for b58")
        self.refused(self.repo(self.record(drop=True)), "keeps no backend for b58")
        self.refused(self.repo(dict(self.record(), schema="epa-backend/0")), "is schema 'epa-backend/0'")

    def test_every_agent_trained_on_it(self):
        agents = [{"path": "a", "meta": {"train_backend": "cycle"}}, {"path": "b", "meta": {"train_backend": "table"}}]
        self.assertEqual(V.backend_problems(agents[:1], "cycle"), [])
        self.assertEqual(V.backend_problems(agents, "cycle"),
                         ["b: its train_backend 'table' is not the backend record's 'cycle'"])


# =====================================================================================================
class Pairing(unittest.TestCase):
    BASE = dict({k: "SYNTHETIC" for k in FP.FATAL}, schema=FP.SCHEMA_VERSION)

    def agent(self, arm, seed, **changes):
        h = None if arm == "blind" else 23.5
        return {"arm": arm, "seed": seed, "meta": dict(self.BASE, preview_h_s=h, **changes)}

    def test_the_pairs_and_each_problem(self):
        pairs = [self.agent("sighted_r0.5", 0), self.agent("blind", 0), self.agent("sighted_r0.5", 1),
                 self.agent("blind", 1)]
        self.assertEqual(V.pairing_problems(pairs), [])                        # the control
        self.assertEqual(V.pairing_problems(pairs[:3]), ["seed 1 is unpaired: it holds no blind"])
        bad = pairs[:3] + [self.agent("blind", 1, reward_knock="other")]
        self.assertEqual(V.pairing_problems(bad),
                         ["seed 1, sighted_r0.5 with blind: reward_knock 'SYNTHETIC' / 'other' (row 117's pairing rule)"])
        self.assertIn("no blinded agent", V.pairing_problems([pairs[0]])[0])
        self.assertIn("no sighted agent", V.pairing_problems([pairs[1]])[0])


# =====================================================================================================
class Average(unittest.TestCase):
    def test_the_average_of_the_five_snapshots_is_scored_not_final_zip(self):
        from stable_baselines3 import SAC
        _, run = runs()
        meta = FP.read(os.path.join(run, "meta.json"))
        avg, lines = V.load_agent(run, meta, device="cpu")
        self.assertIsInstance(avg, TR.AveragedPolicy)
        self.assertIn("the checkpoint average", lines[0])
        obs = np.linspace(-0.5, 0.5, E.OBS_DIM).astype(np.float32)
        acts = [np.asarray(SAC.load(os.path.join(run, s["path"]), device="cpu").predict(obs, deterministic=True)[0],
                           dtype=np.float64) for s in avg.manifest["snapshots"]]
        want = np.mean(acts, axis=0).astype(np.float32)
        got = V.agent_policy(avg)(None, obs)
        self.assertTrue(np.array_equal(got, want))
        final = SAC.load(os.path.join(run, "final"), device="cpu").predict(obs, deterministic=True)[0]
        self.assertFalse(np.array_equal(np.asarray(final, np.float32), want))        # the control
        self.assertFalse(np.array_equal(acts[0], acts[-1]))

    def test_each_refusal(self):
        def refused(run, meta, text):
            with self.assertRaises(SystemExit) as cm:
                V.average_lines(run, meta)
            self.assertIn(text, str(cm.exception))
        _, run = runs()
        meta = FP.read(os.path.join(run, "meta.json"))
        V.average_lines(run, meta)                                              # the control
        no_avg = copy.deepcopy(meta)
        del no_avg["train_recipe"]["checkpoint_average"]
        refused(run, no_avg, "records checkpoint_average None, not decision 29's 50000")
        folder = fresh("average")
        short = make_run(folder, seed=8, ratio=1.5, final_steps=TOTAL - 1)
        refused(short, FP.read(os.path.join(short, "meta.json")),
                f"its manifest's total_steps {TOTAL} is not final.zip's num_timesteps {TOTAL - 1}")
        half = make_run(folder, seed=9, ratio=1.5, window=TR.DECISION_29_WINDOW // 2)
        refused(half, FP.read(os.path.join(half, "meta.json")), "its manifest's window is 25000, not 50000")
        snap = os.path.join(half, TR.SNAPSHOT_DIR, os.listdir(os.path.join(half, TR.SNAPSHOT_DIR))[0])
        with open(snap, "ab") as fh:
            fh.write(b"0")
        refused(half, FP.read(os.path.join(half, "meta.json")), "its checkpoint average does not read")
        os.remove(os.path.join(short, TR.MANIFEST))
        refused(short, FP.read(os.path.join(short, "meta.json")), "no checkpoint_average.json")


# =====================================================================================================
class Transfer(unittest.TestCase):
    def blocks(self):
        live = FP.plant_fingerprint("phase-d", plant=b58(), train_backend=FP.BACKEND_CYCLE,
                                    score_backend=FP.BACKEND_CYCLE, preview_h_s=23.5, reward_knock=False)
        stored = dict(live, scenario={"protocol": "decision-34", "reading": "version 6"}, episodes_sha="SYNTHETIC")
        return stored, live

    def test_scenario_and_episodes_sha_are_printed_and_let_through(self):
        stored, live = self.blocks()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            lines = V.check_transfer("runs/x/sighted_r0.5_seed0", stored, live, route="the locked climb")
        self.assertTrue(lines[0].startswith("DECLARED TRANSFER the locked climb: runs/x/sighted_r0.5_seed0"))
        self.assertIn('trained {"protocol": "decision-34", "reading": "version 6"}', lines[1])
        self.assertIn(f"scored {json.dumps(live['scenario'], sort_keys=True)}", lines[1])
        self.assertIn(f"trained SYNTHETIC   scored {live['episodes_sha']}", lines[2])
        # printed, both exempt fields trained and scored (row 147 (11)), not only returned
        self.assertEqual(out.getvalue(), "\n".join(lines) + "\n")
        self.assertEqual(len(lines), 1 + len(V.TRANSFER_EXEMPT))

    def test_every_other_fatal_field_is_refused_and_nothing_is_forced(self):
        stored, live = self.blocks()
        for field, value in (("reward_knock", True), ("preview_h_s", 30.0), ("engine_sha", "SYNTHETIC"),
                             ("train_backend", "table")):
            with self.subTest(field=field):
                with self.assertRaises(SystemExit) as cm:
                    V.check_transfer("p", dict(stored, **{field: value}), live, route="r")
                self.assertIn(f"{field} is {value!r} in its meta.json and {live[field]!r} live", str(cm.exception))
        with self.assertRaises(SystemExit) as cm:
            V.check_transfer("p", dict(stored, schema=3), live, route="r")
        self.assertIn("fingerprint schema 3", str(cm.exception))
        with self.assertRaises(SystemExit) as cm:
            V.check_transfer("p", None, live, route="r")
        self.assertIn("it has no meta.json", str(cm.exception))
        self.assertNotIn("force", inspect.signature(V.check_transfer).parameters)


# =====================================================================================================
def fake_rows(n, seeds, ratios):
    """score_set's layout with SYNTHETIC numbers: every policy on n roads."""
    rng = np.random.default_rng(31)

    def row(demand=800):
        d = float(rng.uniform(100.0, 200.0))
        return dict(ret=0.0, damage=d + 5.0, damage_thermal=d, fuel=float(rng.uniform(900.0, 1000.0)), torque_viol=0.0,
                    peak_turb=850.0, knock=0, steps=899, demand_steps=demand, short_steps=8 if demand else 0,
                    fuel_base=950.0, damage_base=d)
    hand = {name: [row() for _ in range(n)] for name, _ in V.HAND_POLICIES}
    hand[V.BASELINE][1] = row(demand=0)
    agents = {(arm, s): [row() for _ in range(n)] for s in seeds
              for arm in ["blind"] + [f"sighted_r{r}" for r in ratios]}
    return {"hand": hand, "agents": agents}


class Documents(unittest.TestCase):
    def doc(self, eid="b58", ratios=("0.5", "1.5"), versions=None):
        """A scores document of the engine `eid` (named so: a parameter called engine takes no default,
        test_engine_threading)."""
        rows = fake_rows(V.N_D34_ROADS, [0, 1], ratios)
        prov = {"protocol": V.DECISION_34, "versions": versions or {"numpy": "np-x"}, "platform": "SYNTHETIC",
                "device": "cpu"}
        return V.scores_document(eid, rows, ratios=list(ratios), provenance=prov), rows

    def test_the_document_is_the_analysis_s_and_carries_the_delivery(self):
        import four_engine_analysis as A
        doc, rows = self.doc()
        sc = A.validate_scores(doc)                                              # the analysis's own validator
        self.assertEqual(sc["ratios"], ("0.5", "1.5"))
        self.assertEqual(sorted(doc["engines"]["b58"]["arms"]), ["blind", "sighted_r0.5", "sighted_r1.5"])
        base = rows["hand"][V.BASELINE]
        entry = doc["engines"]["b58"]["arms"]["sighted_r1.5"]["seeds"]["1"]
        self.assertEqual(entry["no_knock"]["D"], [x["damage_thermal"] for x in rows["agents"][("sighted_r1.5", 1)]])
        self.assertEqual(entry["with_knock"]["D_base"], [b["damage"] for b in base])
        dl = doc["provenance"]["delivery"]
        self.assertEqual(dl["hand"][V.BASELINE]["fuel"], [b["fuel"] for b in base])
        self.assertEqual(dl["hand"][V.BASELINE]["short_share"][:3], [8 / 800, None, 8 / 800])
        self.assertEqual(dl["arms"]["blind"]["0"]["short_steps"], [8] * V.N_D34_ROADS)
        spoiled = copy.deepcopy(doc)                                             # the control: beside D, refused
        spoiled["engines"]["b58"]["arms"]["blind"]["seeds"]["0"]["fuel"] = dl["arms"]["blind"]["0"]["fuel"]
        with self.assertRaises(A.AnalysisError) as cm:
            A.validate_scores(spoiled)
        self.assertIn("scores.engines.b58.arms.blind.seeds.0: keys not in the schema ['fuel']", str(cm.exception))
        short = copy.deepcopy(rows)
        short["agents"][("blind", 0)] = short["agents"][("blind", 0)][:-1]
        with self.assertRaises(ValueError) as cm:
            V.scores_document("b58", short, ratios=["0.5", "1.5"], provenance={})
        self.assertIn("blind seed 0: 19 roads, the baseline ECU 20", str(cm.exception))

    def test_write_once(self):
        path = os.path.join(fresh("once"), "S.json")
        sha = V.write_once_json(path, {"a": 1})
        with open(path, "rb") as fh:
            import hashlib
            self.assertEqual(sha, hashlib.sha256(fh.read()).hexdigest())
        with self.assertRaises(SystemExit) as cm:
            V.write_once_json(path, {"a": 2})
        self.assertIn("exists: a scores document is written once", str(cm.exception))
        nan = os.path.join(fresh("once"), "N.json")
        with self.assertRaises(ValueError) as cm:
            V.write_once_json(nan, {"a": float("nan")})
        self.assertIn("Out of range float values are not JSON compliant", str(cm.exception))
        self.assertFalse(os.path.exists(nan))                     # refused before anything is written

    def test_merge_and_its_refusals(self):
        folder = fresh("merge")

        def put(name, doc):
            path = os.path.join(folder, name)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(doc, fh)
            return path
        a, b = put("a.json", self.doc()[0]), put("b.json", self.doc(eid="ford_27tt")[0])
        merged = V.merge_scores([a, b])
        self.assertEqual(sorted(merged["engines"]), ["b58", "ford_27tt"])
        self.assertEqual([c["path"] for c in merged["provenance"]["copied_from"]], [a, b])

        def refused(paths, text):
            with self.assertRaises(SystemExit) as cm:
                V.merge_scores(paths)
            self.assertIn(text, str(cm.exception))
        refused([a, a], "b58 is in")
        refused([a, put("c.json", self.doc(eid="ford_27tt", ratios=("1.5",))[0])], "different ratios")
        refused([a, put("d.json", self.doc(eid="ford_27tt", versions={"numpy": "np-y"})[0])],
                "versions, platform or device differ")
        nineteen = self.doc(eid="ford_27tt")[0]
        nineteen["n_roads"] = 19
        refused([a, put("e.json", nineteen)], "n_roads 19, not 20")


# =====================================================================================================
class Records(unittest.TestCase):
    def test_a_record_gives_its_episodes_damage_back(self):
        out = V.run_cycle_episode(C.p_grade_now, short_cycle(40, onset=5), 1002, (0.69, 0.06, 0.25), plant=b58(),
                                  dt=1.0, use_preview=True, preview_h_s=E.PREVIEW_H_S, reward_knock=False,
                                  inlet_kpa=None, record=None, observe=None)
        rec = {k: np.asarray([out["trace"][k]], dtype=np.float64) for k in ("t_turb", "t_oil", "ki")}
        rec["dt"] = 1.0
        got = V.rescore_from_records(rec, cal=b58().engine.damage)
        # float64 records of the environment's own values: equal to its sums to within the precision of a
        # node the environment may hold in float32 (UNKNOWN which, under NEP 50; never measured here)
        self.assertTrue(np.isclose(got["no_knock"][0], out["damage_thermal"], rtol=1e-6, atol=0.0))
        self.assertTrue(np.isclose(got["with_knock"][0], out["damage"], rtol=1e-6, atol=0.0))
        rec["t_turb"][0, -1] += 25.0                                             # the control
        moved = V.rescore_from_records(rec, cal=b58().engine.damage)
        self.assertFalse(np.isclose(moved["no_knock"][0], out["damage_thermal"], rtol=1e-6, atol=0.0))


# =====================================================================================================
class ScoreSet(unittest.TestCase):
    def test_the_same_rows_at_any_jobs_and_the_records(self):
        blind, sighted = runs()
        agents = V.read_agents([blind, sighted], roads_rec=STATE["record"], engine="b58")
        roads = [short_road(8, k=0, seed=1000, weights=V.EPISODES[0][1], onset=3),
                 short_road(8, k=1, seed=1001, weights=V.EPISODES[1][1], onset=1)]
        one = V.score_set("b58", agents, roads, plant=b58(), reward_knock=False, train_backend=FP.BACKEND_CYCLE,
                          jobs=1, keep_records=True)
        two = V.score_set("b58", agents, roads, plant=b58(), reward_knock=False, train_backend=FP.BACKEND_CYCLE,
                          jobs=2, keep_records=True)
        self.assertEqual(one, two)
        self.assertEqual(sorted(one["hand"]), sorted(name for name, _ in V.HAND_POLICIES))
        self.assertEqual(sorted(one["agents"]), [("blind", 7), ("sighted_r1.5", 7)])
        self.assertNotEqual(one["agents"][("blind", 7)], one["agents"][("sighted_r1.5", 7)])    # the control
        folder = os.path.join(fresh("records"), "R")
        files = V.write_records(folder, "b58", one, dt=1.0)
        self.assertEqual(sorted(files), ["b58/baseline.npz", "b58/blind_seed7.npz", "b58/sighted_r1.5_seed7.npz"])
        with np.load(os.path.join(folder, "b58", "blind_seed7.npz")) as z:
            self.assertEqual((z["t_turb"].shape, z["t_turb"].dtype, float(z["dt"])), ((2, 7), np.float64, 1.0))
        with self.assertRaises(SystemExit) as cm:
            V.write_records(folder, "b58", one, dt=1.0)
        self.assertIn("exists: a record is written once", str(cm.exception))
        lean = V.score_set("b58", [], roads[:1], plant=b58(), reward_knock=False, train_backend=FP.BACKEND_CYCLE,
                           jobs=1, keep_records=False)
        self.assertNotIn("trace", lean["hand"][V.BASELINE][0])
        self.assertEqual(lean["hand"][V.BASELINE][0]["ret"], one["hand"][V.BASELINE][0]["ret"])

    def test_its_refusals(self):
        with self.assertRaises(ValueError) as cm:
            V.score_set("b58", [], [], plant=b58(), reward_knock=False, train_backend="table", jobs=1,
                        keep_records=False)
        self.assertIn("only 'cycle' exists", str(cm.exception))
        import dataclasses
        variant = dataclasses.replace(b58(), scenario=dataclasses.replace(b58().scenario, grade=0.11))
        with self.assertRaises(ValueError) as cm:
            V.score_set("b58", [], [], plant=variant, reward_knock=False, train_backend=FP.BACKEND_CYCLE, jobs=1,
                        keep_records=False)
        self.assertIn("the plant passed is not b58's", str(cm.exception))


# =====================================================================================================
class Pilot(unittest.TestCase):
    def doc(self, seeds):
        rows = fake_rows(V.N_PRACTICE, seeds, ["1.5"])
        roads = [{"k": i, "episode_seed": ER.PRACTICE_SEEDS[i], "weights": [0.6, 0.2, 0.2]} for i in range(10)]
        return V.practice_document("b58", rows, roads=roads, ratios=["1.5"], provenance={}), rows

    def test_s_p_with_ddof_1(self):
        doc, rows = self.doc([2000, 2001, 2002, 2003, 2004])
        self.assertEqual((doc["schema"], doc["label"], doc["n_roads"]), (V.PRACTICE_SCHEMA, V.PRACTICE_HEADER, 10))
        base = [b["damage_thermal"] for b in rows["hand"][V.BASELINE]]

        def cut(rs):
            return 100.0 * (1.0 - np.median([x["damage_thermal"] for x in rs]) / np.median(base))
        d = [cut(rows["agents"][("sighted_r1.5", s)]) - cut(rows["agents"][("blind", s)]) for s in range(2000, 2005)]
        got = V.pilot_spread(doc, engine="b58", ratio=1.5)
        self.assertEqual((got["seeds"], got["pairs"], got["reading"]), (list(range(2000, 2005)), 5, "no_knock"))
        self.assertTrue(np.allclose(got["d"], d, rtol=0.0, atol=1e-12))
        self.assertAlmostEqual(got["s_p"], float(np.std(d, ddof=1)), places=12)
        self.assertNotAlmostEqual(got["s_p"], float(np.std(d, ddof=0)), places=6)          # the control

    def test_its_refusals(self):
        doc, _ = self.doc([2000, 2001])
        with self.assertRaises(ValueError) as cm:
            V.pilot_spread(doc, engine="ford_27tt", ratio=1.5)
        self.assertIn("not a four-engine-practice/1 document of ford_27tt", str(cm.exception))
        spoiled = copy.deepcopy(doc)
        del spoiled["arms"]["blind"]["seeds"]["2001"]
        with self.assertRaises(ValueError) as cm:
            V.pilot_spread(spoiled, engine="b58", ratio=1.5)
        self.assertIn("unpaired seeds", str(cm.exception))
        one, _ = self.doc([2000])
        with self.assertRaises(ValueError) as cm:
            V.pilot_spread(one, engine="b58", ratio=1.5)
        self.assertIn("1 pair(s): a spread needs at least 2", str(cm.exception))


# =====================================================================================================
class Cli(unittest.TestCase):
    def refused(self, argv, text):
        with mock.patch.object(sys, "argv", ["evaluate.py", "--engine", "b58"] + argv):
            with self.assertRaises(SystemExit) as cm:
                V.main()
        self.assertIn(text, str(cm.exception))

    def test_decision_34s_refusals(self):
        out = os.path.join(fresh("cli"), "S.json")
        d34 = ["--protocol", "d34", "--reward-knock", "out", "--scores-out", out]
        self.refused(d34 + ["--force-plant-mismatch", "runs/x"], "--force-plant-mismatch: every agent is scored")
        self.refused(["--protocol", "d34", "--scores-out", out, "runs/x"], "--reward-knock in|out is required")
        self.refused(["--protocol", "d34", "--reward-knock", "out", "runs/x"], "--scores-out PATH is required")
        self.refused(["--protocol", "d34", "--reward-knock", "out", "--scores-out", os.path.join(HERE, "S.json"),
                      "runs/x"], "lies inside the repository")
        self.refused(d34 + ["--out", os.path.join(fresh("cli"), "phase_d_seed9.txt"), "runs/x"],
                     "is never written as results/*_seed*.txt")
        self.refused(d34 + ["--practice", "--records-out", os.path.join(fresh("cli"), "R"), "runs/x"],
                     "the per-step records are the test set's")
        self.refused(d34 + ["--label", "X", "runs/x"], "--label: the report is headed 'DECISION 34 EVALUATION'")
        self.refused(d34, "no agents given")                    # the control: every check before it passed

    def test_decision_34s_flags_are_refused_on_phase_d_and_d2(self):
        for argv, text in ((["--practice"], "REFUSING --practice on --protocol phase-d"),
                           (["--scores-out", "S.json"], "REFUSING --scores-out on --protocol phase-d"),
                           (["--protocol", "d2", "--jobs", "2"], "REFUSING --jobs on --protocol d2"),
                           (["--protocol", "d2", "--records-out", "R"], "REFUSING --records-out on --protocol d2")):
            with self.subTest(argv=argv):
                self.refused(argv, text)


# =====================================================================================================
N_SHORT = 6                                  # samples kept of each road in EndToEnd: five steps
REAL_D34 = FP._d34                           # fingerprint's decision-34 reader, before any test patches it
REAL_DECISION34_ROADS = V.decision34_roads
ABSENT = "ABSENT"                            # a key a document does not hold reads so, never as copied_from's None


def scoring_machine():
    """What main_decision34 records of the machine that scored, read the way it reads them: epa_freeze's
    versions, platform.platform() and the device 'cpu'. merge_scores compares these three across documents
    (row 143 (4)), so a document without them would merge with any machine's."""
    return {"versions": EF.versions(), "platform": platform.platform(), "device": "cpu"}


def shortened(roads, n):
    """Each road cut to its first n samples, its grade a 10 % climb from 1 s (epa_roads.climb_profile), since
    the roads' own climbs start after 150 s, beyond the cut, and H would then reach no score: decision 34's
    twenty roads of 900 s would take minutes here."""
    out = []
    for r in roads:
        c = dict(r["cycle"])
        for key in ("t", "v_mps", "t_amb"):
            c[key] = list(c[key])[:n]
        c["grade"] = [float(g) for g in ER.climb_profile(np.asarray(c["t"], dtype=float), 1.0, 30.0, 0.10)]
        out.append(dict(r, cycle=c))
    return out


def scoring_extra():
    """What main_decision34 reads of roads.json beside decision34_roads' keys: read_roads_record's (the SYNTHETIC
    seed, the streams, tau and the H table at TAU_S, as four_engine_roads.write_synthetic_record writes them)
    and row 96's practice roads, epa_roads.practice_roads' seeds and weights on short cycles."""
    path = os.path.join(fresh("synthetic_record"), "roads.SYNTHETIC.json")
    syn = ER.load_record(FER.write_synthetic_record(path, SYNTHETIC_SEED, taus={"b58": TAU_S}, ratios=[0.5, 1.5]))
    practice = [short_road(N_SHORT, k=i, seed=r["episode_seed"], weights=r["weights"], onset=1)
                for i, r in enumerate(ER.practice_roads(SYNTHETIC_SEED))]
    return dict({k: syn[k] for k in ("label", "commit_reveal", "streams", "ratios", "tau", "H_table")},
                practice=practice)


def d34_meta(*, seed, ratio):
    """meta.json as train.py writes it for a decision-34 run, built under EndToEnd's patches: live_decision34's
    block at the arm's H with the reward 'out' (the blinded arm's H None), and synthetic_meta's recipe."""
    h = None if ratio is None else h_of(ratio)
    live = V.live_decision34(b58(), preview_h_s=h, reward_knock=False, train_backend=FP.BACKEND_CYCLE)
    return dict(live, seed=seed, use_preview=ratio is not None,
                train_recipe=synthetic_meta(seed=seed, ratio=ratio)["train_recipe"])


class EndToEnd(unittest.TestCase):
    """main_decision34 end to end through main(), on the test set and on the practice route. The roads record
    and the backend record are a SYNTHETIC git repository's (evaluate.HERE points at it), which
    fingerprint's decision-34 reader reads too (fingerprint._d34, patched to that root); the roads are
    decision34_roads' own, run on that repository and then cut short (shortened). Two seed pairs, blinded and
    sighted at r = 1.5, whose meta.json is live_decision34's block (d34_meta). Every check of the route and
    the scoring run as they are; the documents are read back: on the test set every key main_decision34's
    prov.update writes, on the practice route its protocol, train_backend, trained_under, environment, agents
    and the machine (versions, platform, device)."""

    @classmethod
    def setUpClass(cls):
        cls.extra = scoring_extra()
        cls.root = os.path.join(fresh("e2e"), "repo")
        build_d34_repo(cls.root, extra=cls.extra, backend=backend_record())
        folder = fresh("e2e_runs")
        with cls.patched():
            cls.runs = [make_run(folder, seed=s, ratio=r, perturb=p, meta=d34_meta(seed=s, ratio=r))
                        for s, r, p in ((7, None, 0.05), (7, 1.5, 0.07), (8, None, 0.04), (8, 1.5, 0.06))]

    @classmethod
    def patched(cls, root=None):
        where = cls.root if root is None else root

        def roads(*, root):
            got, prov = REAL_DECISION34_ROADS(root=root)
            return shortened(got, N_SHORT), prov
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(FP, "_d34", lambda _root: REAL_D34(where)))
        stack.enter_context(mock.patch.object(V, "HERE", where))
        stack.enter_context(mock.patch.object(V, "decision34_roads", roads))
        return stack

    def main(self, argv, root=None):
        """evaluate.main() on `argv` (after --engine b58), under the patches: (its value, what it printed)."""
        out = io.StringIO()
        with self.patched(root), mock.patch.object(sys, "argv", ["evaluate.py", "--engine", "b58"] + argv), \
                contextlib.redirect_stdout(out):
            got = V.main()
        return got, out.getvalue()

    def refused(self, argv, text, root=None):
        with self.assertRaises(SystemExit) as cm:
            self.main(argv, root)
        self.assertIn(text, str(cm.exception))

    def meta(self, i):
        return FP.read(os.path.join(self.runs[i], "meta.json"))

    def test_the_test_set(self):
        import four_engine_analysis as A
        folder = fresh("e2e_out")
        scores, records, report = (os.path.join(folder, n) for n in ("S.json", "R", "report.txt"))
        got, printed = self.main(["--protocol", "d34", "--reward-knock", "out", "--scores-out", scores,
                                  "--records-out", records, "--out", report] + self.runs)
        self.assertEqual(got, 0)
        with open(scores, "rb") as fh:
            raw = fh.read()
        doc = json.loads(raw)
        sc = A.validate_scores(doc)                                           # the analysis's own validator
        self.assertEqual((sc["ratios"], sc["engines"]["b58"]["seeds"]), (("1.5",), [7, 8]))
        prov, blind = doc["provenance"], self.meta(0)
        self.assertEqual((prov["protocol"], prov["reading"], prov["train_backend"], prov["score_backend"],
                          prov["reward_knock"]),
                         (V.DECISION_34, V.REDRAW_READING, {"b58": FP.BACKEND_CYCLE}, FP.BACKEND_CYCLE, False))
        self.assertEqual(prov["trained_under"], {"scenario": blind["scenario"], "episodes_sha": blind["episodes_sha"]})
        self.assertEqual(prov["episodes_sha"], blind["episodes_sha"])
        self.assertEqual(prov["environment"], V.env_of(blind, synthetic_config()))
        # the machine that scored and the rescoring keys, each present (a dropped one reads ABSENT, so that
        # copied_from's None cannot stand for it)
        keys = ("versions", "platform", "device", "variant_lines", "rescored_engines", "copied_from")
        self.assertEqual({k: prov.get(k, ABSENT) for k in keys},
                         dict(scoring_machine(), variant_lines=[], rescored_engines=["b58"], copied_from=None))
        self.assertEqual({arm: sorted(s) for arm, s in prov["agents"].items()},
                         {"blind": ["7", "8"], "sighted_r1.5": ["7", "8"]})
        self.assertEqual((prov["agents"]["sighted_r1.5"]["7"]["H_s"], prov["agents"]["blind"]["7"]["H_s"]),
                         (h_of(1.5), None))
        with open(os.path.join(self.runs[1], TR.MANIFEST), "rb") as fh:
            self.assertEqual(prov["agents"]["sighted_r1.5"]["7"]["manifest_sha256"], hashlib.sha256(fh.read()).hexdigest())
        self.assertFalse(prov["version_5_reading"]["scored"])
        self.assertEqual(len(prov["delivery"]["hand"][V.BASELINE]["fuel"]), V.N_D34_ROADS)
        self.assertEqual(sorted(prov["recipe_checks"]), sorted(r.replace(os.sep, "/") for r in self.runs))
        self.assertTrue(all(c["learning_rate_reaches_0"] for c in prov["recipe_checks"].values()))
        # the control, what the machine's keys are for (row 143 (4)): the document merges with itself named as
        # another engine, and that copy on another device is refused by merge_scores' text
        merge = fresh("e2e_merge")
        mine = put_json(merge, "b58.json", doc)
        twin = dict(doc, engines={"ford_27tt": doc["engines"]["b58"]})
        self.assertEqual(sorted(V.merge_scores([mine, put_json(merge, "twin.json", twin)])["engines"]),
                         ["b58", "ford_27tt"])
        twin["provenance"] = dict(prov, device="cuda")
        with self.assertRaises(SystemExit) as cm:
            V.merge_scores([mine, put_json(merge, "cuda.json", twin)])
        self.assertIn("REFUSING to merge: the documents' versions, platform or device differ", str(cm.exception))
        # each score is the agent's checkpoint average at its own H, on the roads decision34_roads gives;
        # the control: at the default H the same agent scores otherwise
        with self.patched():
            roads, _ = V.decision34_roads(root=self.root)
        avg, _ = V.load_agent(self.runs[1], self.meta(1), device="cpu")

        def d(h_s):
            return [V.run_road_episode(V.agent_policy(avg), r, plant=b58(), use_preview=True, preview_h_s=h_s,
                                       reward_knock=False)["damage_thermal"] for r in roads]
        want = d(h_of(1.5))
        self.assertEqual(doc["engines"]["b58"]["arms"]["sighted_r1.5"]["seeds"]["7"]["no_knock"]["D"], want)
        self.assertNotEqual(d(E.PREVIEW_H_S), want)
        # the records, their index and the report
        with open(V.records_index_path(scores), encoding="utf-8") as fh:
            index = json.load(fh)
        self.assertEqual(sorted(index["files"]), ["b58/baseline.npz", "b58/blind_seed7.npz", "b58/blind_seed8.npz",
                                                  "b58/sighted_r1.5_seed7.npz", "b58/sighted_r1.5_seed8.npz"])
        self.assertEqual(index["scores_sha256"], hashlib.sha256(raw).hexdigest())
        with open(report, encoding="utf-8") as fh:
            text = fh.read()
        self.assertTrue(text.startswith(V.D34_HEADER))
        self.assertIn("d at r = 1.5, sighted_r1.5 minus blind, per seed", text)
        self.assertIn(f"scores document {scores}: sha256 {hashlib.sha256(raw).hexdigest()}", printed)

    def test_the_practice_route(self):
        folder = fresh("e2e_practice")
        scores, report = os.path.join(folder, "P.json"), os.path.join(folder, "report.txt")
        got, _ = self.main(["--protocol", "d34", "--practice", "--reward-knock", "out", "--scores-out", scores,
                            "--out", report] + self.runs)
        self.assertEqual(got, 0)
        with open(scores, encoding="utf-8") as fh:
            doc = json.load(fh)
        self.assertEqual((doc["schema"], doc["label"], doc["engine"], doc["n_roads"], doc["ratios"]),
                         (V.PRACTICE_SCHEMA, V.PRACTICE_HEADER, "b58", V.N_PRACTICE, ["1.5"]))
        self.assertEqual([r["episode_seed"] for r in doc["roads"]], list(ER.PRACTICE_SEEDS))
        prov, blind = doc["provenance"], self.meta(0)
        self.assertEqual((prov["protocol"], prov["train_backend"], prov["reading"]),
                         (f"{V.DECISION_34} practice", {"b58": FP.BACKEND_CYCLE}, "row 96's practice roads"))
        self.assertEqual(prov["trained_under"]["episodes_sha"], blind["episodes_sha"])
        self.assertNotIn("episodes_sha", prov)            # the practice roads are not the set it names
        self.assertEqual(prov["environment"], V.env_of(blind, synthetic_config()))
        self.assertEqual({k: prov.get(k, ABSENT) for k in ("versions", "platform", "device")}, scoring_machine())
        self.assertEqual(sorted(prov["agents"]), ["blind", "sighted_r1.5"])
        sp = V.pilot_spread(doc, engine="b58", ratio=1.5)
        self.assertEqual((sp["pairs"], sp["seeds"]), (2, [7, 8]))
        with open(report, encoding="utf-8") as fh:
            text = fh.read()
        self.assertTrue(text.startswith(V.PRACTICE_HEADER))
        self.assertIn(f"s_p at r = 1.5 (row 103 (4); no knock, ddof 1, 2 pairs): {sp['s_p']:.4f}", text)

    def test_each_refusal_of_the_route(self):
        out = os.path.join(fresh("e2e_refused"), "S.json")
        d34 = ["--protocol", "d34", "--scores-out", out]
        # an agent of another train_backend, on the practice route: backend_problems' text
        folder = os.path.join(fresh("e2e_table"), "set")
        shutil.copytree(os.path.dirname(self.runs[0]), folder)
        runs = [os.path.join(folder, os.path.basename(r)) for r in self.runs]
        put_json(runs[0], "meta.json", dict(self.meta(0), train_backend="table"))
        self.refused(d34 + ["--practice", "--reward-knock", "out"] + runs,
                     f"REFUSING --protocol d34 --practice: the backend record's train_backend: {runs[0]}: its "
                     "train_backend 'table' is not the backend record's 'cycle'")
        # another environment (row 143 (5)), and an unpaired seed (row 117), each by main's own text
        put_json(runs[0], "meta.json", self.meta(0))
        put_json(runs[2], "config.json", synthetic_config(device="cuda"))
        self.refused(d34 + ["--reward-knock", "out"] + runs,
                     f"REFUSING --protocol d34: one environment (row 143 (5); CLAUDE.md rules 3 and 5): config.json "
                     f"device: {runs[2]} 'cuda', {runs[0]} 'cpu'")
        self.refused(d34 + ["--reward-knock", "out"] + self.runs[:3],
                     "REFUSING --protocol d34: row 117's pairs: seed 8 is unpaired: it holds no sighted_r1.5")
        # no backend record in the repository: committed_train_backend's text, never a typed 'cycle'
        bare = os.path.join(fresh("e2e_nobackend"), "repo")
        build_d34_repo(bare, extra=self.extra)
        self.refused(d34 + ["--reward-knock", "out"] + self.runs,
                     f"no {engines.BACKEND_REL}: the train_backend every agent is checked against", root=bare)
        # the reward they did not train with: each agent's decision-34 fingerprint refuses it
        self.refused(d34 + ["--reward-knock", "in"] + self.runs, "it was trained on a different plant")
        self.assertFalse(os.path.exists(out))


if __name__ == "__main__":
    unittest.main(verbosity=2)

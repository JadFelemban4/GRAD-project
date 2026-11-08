"""test_preview_horizon.py -- row 117: H, the preview horizon, as an environment parameter.

    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -B test_preview_horizon.py     exit code 0 when all pass

The plant commit P (ORDER step 14; interface sheet 6.7, P1). Its first form was the scratch draft of 2
November 2026 (branch s-blind, 40132c5, on fefb7af, never pushed) whose BlindBitForBit result row 135 (5)
quotes; at P a failure of BlindBitForBit is a defect of P, fixed in P. The golden helper and its pins are
test_plant_guards' (golden_digests, GOLDEN; the one definition), imported here.

  PreviewSamples  preview_samples(30) is engine_env.PREVIEW_S exactly; the environment's default H is
                  PREVIEW_H_S and its preview_s PREVIEW_S; the refusals (a bool or a non-real: TypeError;
                  a non-finite H or one <= 0: ValueError), at the function and at construction; every
                  subclass forwards H through **kw; fingerprint.preview_of and reward_knock_of read the
                  environment itself, a wrapper refused
  OtherH          an H other than 30 s is built, not refused; the sample steps int((H / d) / dt) are the
                  roads record's H_table steps (row 102), for every engine and ratio
  Golden          the B58 (phase-d EPISODES[0], ExtremesTrainingEnv seed 0) and each EPA engine (the
                  locked climb, 120 s) at the defaults give, bit for bit, test_plant_guards.GOLDEN, the
                  digests MEASURED on step 13's tree (a3cd3a3) before P's edits; control (mistake 12): the
                  phase-d digest moves with H
  BlindBitForBit  row 117's test: with use_preview off, the observation, reward, flags and info of 899
                  steps (450 neutral, then default_rng(0) actions) are identical at every H on decision-34
                  road 0, ExtremesTrainingEnv seed 0 and the four-engine training road, every preview
                  sample 0.0 (the four-engine road is train.build_env's, H passed as its preview_h_s,
                  and at 30 s equal to its default); a short SAC training (seed 0, 400 steps: 100
                  random, then 300 updates) on
                  the blinded four-engine road at the B58's two H gives identical parameters and replay
                  buffer, and so does the same H twice; control (mistake 12): the sighted arm at the same
                  two H differs, in the observation first at the step its expected samples first differ,
                  and in the training's parameters

Every environment runs in a worker process of its own (spawn), built there by name; the results are
compared here. No EPA table and no held-out row is read; decision 34's road 0 is read from the roads
record this tree holds (results/EPA_ROADS/roads.json), or drawn SYNTHETIC when there is none.
"""
import hashlib
import inspect
import multiprocessing
import os
import re
import sys
import unittest
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

import engine_env as E  # noqa: E402
import engines  # noqa: E402
import epa_roads as ER  # noqa: E402
from test_plant_guards import (GOLDEN, GOLDEN_PARENT, golden_actions, golden_case, golden_digests,  # noqa: E402
                               golden_sha, golden_step)

DT = 1.0
STEPS = 899                 # one 900 s episode at dt 1, to its truncation (k >= n - 1)
TRAIN_STEPS = 400           # SAC's learning_starts is 100, so 300 gradient updates
SYNTHETIC_SEED = 4242       # SYNTHETIC: below 2**32, never roads_seed (row 96); used only without a record
JOBS = 8


# ------------------------------------------------------------------ the digests
def _canon(v, path=()):
    """Everything a value holds, exactly, for the strict comparison; Monitor's wall-clock info['episode']['t']
    is the one thing left out."""
    if isinstance(v, dict):
        return tuple((str(k), _canon(v[k], path + (k,))) for k in sorted(v) if path + (k,) != ("episode", "t"))
    if isinstance(v, np.ndarray):
        return ("nd", v.dtype.str, v.shape, v.tobytes())
    if isinstance(v, (bool, np.bool_)):
        return ("b", bool(v))
    if isinstance(v, (int, np.integer)):
        return ("i", int(v))
    if isinstance(v, (float, np.floating)):
        return ("f", type(v).__name__, np.float64(v).tobytes())
    if isinstance(v, (list, tuple)):
        return ("l", tuple(_canon(x, path) for x in v))
    return ("r", repr(v))


def strict_step(obs, r, term, trunc, info):
    """The strict per-step digest: the observation's own dtype and bytes, the reward, both flags and every
    info value (nested ones included)."""
    o = np.asarray(obs)
    return hashlib.sha256(repr((o.dtype.str, o.shape, o.tobytes(), np.float64(r).tobytes(), bool(term),
                                bool(trunc), _canon(info))).encode()).hexdigest()


def run_trace(env, obs0, steps, *, seed):
    """One open-loop trace: per step (step 0 the reset's observation) the golden and the strict digests,
    the environment's own k and the four preview samples of the observation."""
    u = env.unwrapped
    gold = [golden_step(obs0, 0.0, {})]
    strict = [strict_step(obs0, 0.0, False, False, {})]
    ks, prev = [int(u.k)], [np.asarray(obs0, dtype=np.float32)[14:18].copy()]
    for a in golden_actions(steps, seed=seed):
        obs, r, term, trunc, info = env.step(a)
        gold.append(golden_step(obs, r, info))
        strict.append(strict_step(obs, r, term, trunc, info))
        ks.append(int(u.k))
        prev.append(np.asarray(obs, dtype=np.float32)[14:18].copy())
        if term or trunc:
            break
    return dict(golden=gold, strict=strict, k=np.asarray(ks), prev=np.stack(prev))


trace_sha = golden_sha


# ------------------------------------------------------------------ the environments, built by name
def d34_road():
    """Decision 34's road 0 as this tree holds it: the roads record's, else one SYNTHETIC road."""
    path = os.path.join(HERE, ER.ROADS_REL)
    if os.path.exists(path):
        return ER.load_record(path)["roads"][0], "roads.json road 0"
    return ER.generate(SYNTHETIC_SEED, n_roads=1)[0], f"SYNTHETIC seed {SYNTHETIC_SEED} road 0"


def horizons():
    """30 s and every H of the roads record's H_table (row 102), sorted; the B58's two H (r = 0.5, 1.5)."""
    path = os.path.join(HERE, ER.ROADS_REL)
    rec = ER.load_record(path) if os.path.exists(path) else {}
    table = rec.get("H_table") or {}
    hs = sorted({30.0} | {float(v["H_s"]) for e in table.values() for v in e.values()})
    b58 = sorted(float(v["H_s"]) for v in table["b58"].values()) if "b58" in table else [30.0, 71.0]
    return hs, b58, table


def four_engine_env(plant, *, use_preview, h, seed):
    """train.build_env's four_engine road with H passed (its preview_h_s, the plant commit P), the share
    off; the trace "four_engine_build_env" is build_env at its default H, which must be H = 30 s's."""
    import train as T
    return T.build_env(use_preview, seed, T.DURATION_S, "four_engine", DT, plant=plant, preview_h_s=h,
                       scored_share=False, roads_record=None)


def build(kind, *, use_preview, h):
    """(env, the reset's observation) for one trace, on the B58."""
    plant = engines.get("b58")
    if kind == "d34":
        road = d34_road()[0]
        seed = int(road["episode_seed"])
        env = E.SupervisoryTunerEnv(ER.env_cycle(road), plant=plant, dt=float(road["dt"]), use_preview=use_preview,
                                    seed=seed, preview_h_s=h)
        env.reset(seed=seed)
        env.w = np.asarray(road["weights"], dtype=np.float32)      # engine_gate.d34_env's order
        return env, env._obs()
    if kind == "extremes":
        env = E.ExtremesTrainingEnv(duration=900.0, dt=DT, use_preview=use_preview, seed=0, plant=plant,
                                    preview_h_s=h)
        return env, env.reset(seed=0)[0]
    if kind == "four_engine":
        env = four_engine_env(plant, use_preview=use_preview, h=h, seed=0)
        return env, env.reset(seed=0)[0]
    if kind == "four_engine_build_env":
        import train as T
        assert h == E.PREVIEW_H_S
        env = T.build_env(use_preview, 0, T.DURATION_S, "four_engine", DT, plant=plant, scored_share=False,
                          roads_record=None)
        return env, env.reset(seed=0)[0]
    raise ValueError(kind)


# ------------------------------------------------------------------ the jobs (one process each)
def golden_job(task):
    """test_plant_guards.golden_case at the defaults, or at H = `h` for the control."""
    name, h = task
    env, steps = golden_case(name, **({} if h is None else {"preview_h_s": h}))
    return golden_sha(golden_digests(env, steps, seed=0))


def trace_job(task):
    kind, use_preview, h = task
    env, obs0 = build(kind, use_preview=use_preview, h=h)
    u = env.unwrapped
    t = run_trace(env, obs0, STEPS, seed=0)
    g = np.asarray(u.cycle["grade"], dtype=float)
    n = len(g)
    # what the observation's four samples should be: 12 x grade[min(k + int(h / dt), n - 1)], or 0.0 blind
    want = np.asarray([[np.float32(g[min(int(k) + int(s / u.dt), n - 1)] * 12.0) if u.use_preview else 0.0
                        for s in u.preview_s] for k in t["k"]], dtype=np.float32)
    return dict(t, want=want, preview_s=tuple(u.preview_s), preview_h_s=u.preview_h_s, n=n)


def train_job(task):
    """A short SAC training on the four-engine road, train.py's model at X1's defaults for a 400-step run
    (learning rate 3e-4, buffer 10 000, seed 0, cpu), one torch thread; nothing is saved."""
    use_preview, h, _repeat = task
    import torch
    from stable_baselines3 import SAC
    from stable_baselines3.common.logger import Logger
    torch.set_num_threads(1)
    env = four_engine_env(engines.get("b58"), use_preview=use_preview, h=h, seed=0)
    model = SAC("MlpPolicy", env, seed=0, learning_rate=3e-4, buffer_size=10_000, verbose=0, device="cpu")
    model.set_logger(Logger(folder=None, output_formats=[]))      # no SB3-<time> folder anywhere
    model.learn(total_timesteps=TRAIN_STEPS, progress_bar=False)
    sd = model.policy.state_dict()
    params = np.concatenate([sd[k].detach().cpu().numpy().ravel() for k in sorted(sd)]
                            + [model.log_ent_coef.detach().cpu().numpy().ravel()])
    rb = model.replay_buffer
    n = rb.buffer_size if rb.full else rb.pos
    hb = hashlib.sha256()
    for a in (rb.observations, rb.next_observations, rb.actions, rb.rewards, rb.dones, rb.timeouts):
        hb.update(np.ascontiguousarray(a[:n]).tobytes())
    return dict(params=params, buffer=hb.hexdigest(), n=int(n), updates=int(model._n_updates),
                obs_prev=np.concatenate([rb.observations[:n, 0, 14:18], rb.next_observations[:n, 0, 14:18]]))


STATE = {}


def _run_all():
    """Every environment's trace and every training, in worker processes; once per run of this file."""
    if STATE:
        return STATE
    hs, b58_h, table = horizons()
    h1, h2 = b58_h[0], b58_h[-1]
    kinds = ("d34", "extremes", "four_engine")
    traces = [(k, False, h) for k in kinds for h in hs] + [(k, True, h) for k in kinds for h in (h1, h2)] \
        + [("four_engine_build_env", False, E.PREVIEW_H_S)]
    trains = [(False, h1, 0), (False, h2, 0), (False, h1, 1), (True, h1, 0), (True, h2, 0)]
    goldens = [(name, None) for name in GOLDEN] + [("b58 phase-d EPISODES[0], dt 1, 300 steps", h2)]
    with ProcessPoolExecutor(max_workers=JOBS, mp_context=multiprocessing.get_context("spawn")) as pool:
        ft = {t: pool.submit(trace_job, t) for t in traces}
        fr = {t: pool.submit(train_job, t) for t in trains}
        fg = {t: pool.submit(golden_job, t) for t in goldens}
        STATE.update(hs=hs, h1=h1, h2=h2, kinds=kinds, table=table, road=d34_road()[1],
                     traces={t: f.result() for t, f in ft.items()},
                     trains={t: f.result() for t, f in fr.items()},
                     goldens={t: f.result() for t, f in fg.items()})
    return STATE


def _short(d):
    s = d[:16]
    assert not re.search(r"\d{39}", s)
    return s


def first_difference(a, b):
    """The first index where two lists of digests differ (or the shorter's length), None if equal."""
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return None if len(a) == len(b) else min(len(a), len(b))


# ------------------------------------------------------------------ the tests
class PreviewSamples(unittest.TestCase):
    def test_30_s_gives_PREVIEW_S_exactly(self):
        self.assertEqual(E.PREVIEW_H_S, 30.0)
        self.assertEqual(E.PREVIEW_DIVISORS, (15.0, 6.0, 2.0, 1.0))
        self.assertEqual(E.PREVIEW_S, (2.0, 5.0, 15.0, 30.0))
        for h in (30.0, 30, np.float64(30.0), E.PREVIEW_H_S):
            got = E.preview_samples(h)
            self.assertEqual(got, E.PREVIEW_S)
            self.assertTrue(all(type(x) is float for x in got))
        self.assertEqual(E.preview_samples(71.0), (71.0 / 15.0, 71.0 / 6.0, 35.5, 71.0))

    def test_the_environments_default_is_PREVIEW_H_S(self):
        sig = inspect.signature(E.SupervisoryTunerEnv.__init__)
        self.assertEqual(sig.parameters["preview_h_s"].default, E.PREVIEW_H_S)
        p = engines.get("b58")
        env = E.SupervisoryTunerEnv(E.locked_climb(p, duration=60.0, dt=DT), plant=p, dt=DT)
        self.assertEqual(env.preview_s, E.PREVIEW_S)
        self.assertEqual(env.preview_h_s, 30.0)
        self.assertIs(type(env.preview_h_s), float)
        env = E.SupervisoryTunerEnv(E.locked_climb(p, duration=60.0, dt=DT), plant=p, dt=DT, preview_h_s=30)
        self.assertIs(type(env.preview_h_s), float)

    def test_the_refusals(self):
        for bad in (True, False, np.bool_(True), "30", None, [30.0], 1 + 0j):
            with self.assertRaises(TypeError, msg=repr(bad)):
                E.preview_samples(bad)
        for bad in (0, 0.0, -1.0, float("nan"), float("inf"), float("-inf")):
            with self.assertRaises(ValueError, msg=repr(bad)):
                E.preview_samples(bad)
        p = engines.get("b58")
        c = E.locked_climb(p, duration=60.0, dt=DT)
        with self.assertRaises(TypeError):
            E.SupervisoryTunerEnv(c, plant=p, dt=DT, preview_h_s=True)
        with self.assertRaises(ValueError):
            E.SupervisoryTunerEnv(c, plant=p, dt=DT, preview_h_s=0.0)
        # control: the same construction at a legal H builds
        self.assertEqual(E.SupervisoryTunerEnv(c, plant=p, dt=DT, preview_h_s=0.5).preview_s,
                         E.preview_samples(0.5))

    def test_every_subclass_forwards_H(self):
        from wide_air import WideAirTrainingEnv
        p = engines.get("b58")
        for cls in (E.TerrainTrainingEnv, E.ExtremesTrainingEnv, WideAirTrainingEnv):
            env = cls(duration=60.0, dt=DT, seed=0, plant=p, preview_h_s=71.0)
            self.assertEqual(env.preview_s, E.preview_samples(71.0), cls.__name__)
            self.assertEqual(cls(duration=60.0, dt=DT, seed=0, plant=p).preview_s, E.PREVIEW_S, cls.__name__)

    def test_the_fingerprint_reads_the_environment_itself(self):
        """fingerprint.preview_of: a sighted environment's H, the blinded arm's None; reward_knock_of: the
        environment's knock option (X1's, at the default); both refuse a wrapper (pass env.unwrapped)."""
        import fingerprint as FP
        import train as T
        p = engines.get("b58")
        for use_preview, want in ((True, 30.0), (False, None)):
            env = T.build_env(use_preview, 0, 60.0, "extremes", DT, plant=p)
            self.assertEqual(FP.preview_of(env.unwrapped), want)
            self.assertIs(FP.reward_knock_of(env.unwrapped), E.REWARD_KNOCK_DEFAULT)
            for f in (FP.preview_of, FP.reward_knock_of):
                with self.assertRaises(TypeError):
                    f(env)
        env = E.SupervisoryTunerEnv(E.locked_climb(p, duration=60.0, dt=DT), plant=p, dt=DT, preview_h_s=71.0)
        self.assertEqual(FP.preview_of(env), 71.0)
        env.reward_knock = 1                                       # not a bool
        with self.assertRaises(TypeError):
            FP.reward_knock_of(env)


class OtherH(unittest.TestCase):
    def test_the_sample_steps_are_row_102s(self):
        _, _, table = horizons()
        self.assertTrue(table, "the roads record holds no H_table")
        for e, rows in table.items():
            for r, v in rows.items():
                h = float(v["H_s"])
                self.assertEqual([int(s / DT) for s in E.preview_samples(h)], list(v["sample_steps"]), (e, r))
                self.assertEqual([int((h / d) / DT) for d in E.PREVIEW_DIVISORS], list(v["sample_steps"]), (e, r))

    def test_an_H_other_than_30_s_is_sampled_where_it_says(self):
        s = _run_all()
        for kind in s["kinds"]:
            for h in (s["h1"], s["h2"]):
                t = s["traces"][(kind, True, h)]
                self.assertEqual(t["preview_s"], E.preview_samples(h))
                self.assertTrue(np.array_equal(t["prev"], t["want"]), (kind, h))
                self.assertGreater(np.count_nonzero(t["prev"]), 0, (kind, h))


class Golden(unittest.TestCase):
    def test_the_defaults_are_the_parents_bit_for_bit(self):
        s = _run_all()
        for name, want in GOLDEN.items():
            self.assertIsNotNone(want, f"{name}: no digest pinned from {GOLDEN_PARENT}")
            self.assertEqual(s["goldens"][(name, None)], want, name)

    def test_control_the_digest_moves_with_H(self):
        s = _run_all()
        name = "b58 phase-d EPISODES[0], dt 1, 300 steps"
        self.assertNotEqual(s["goldens"][(name, s["h2"])], s["goldens"][(name, None)])


class BlindBitForBit(unittest.TestCase):
    """Row 117: "A test checks that a blinded environment at H1 and at H2 gives the same trajectory bit for
    bit. If it does not, the blinded arm is trained once per H." Run first on the scratch draft s-blind, for
    row 135 (5); at P it is a gate, and a failure there is a defect of P (sheet 6.7). The four-engine road
    is train.build_env's own, H passed as its preview_h_s."""

    def test_every_blinded_sample_is_zero_at_every_H(self):
        s = _run_all()
        for kind in s["kinds"]:
            for h in s["hs"]:
                t = s["traces"][(kind, False, h)]
                self.assertEqual(t["preview_s"], E.preview_samples(h), (kind, h))
                self.assertTrue(np.all(t["prev"] == 0.0), (kind, h))
                self.assertEqual(len(t["strict"]), STEPS + 1, (kind, h))

    def test_a_blinded_environment_at_every_H_gives_one_trajectory_bit_for_bit(self):
        s = _run_all()
        for kind in s["kinds"]:
            ref = s["traces"][(kind, False, 30.0)]
            for h in s["hs"]:
                t = s["traces"][(kind, False, h)]
                self.assertEqual(t["strict"], ref["strict"], (kind, h))
                self.assertEqual(t["golden"], ref["golden"], (kind, h))

    def test_the_four_engine_road_at_30_s_is_train_build_envs_default(self):
        s = _run_all()
        self.assertEqual(s["traces"][("four_engine", False, 30.0)]["strict"],
                         s["traces"][("four_engine_build_env", False, E.PREVIEW_H_S)]["strict"])

    def test_control_the_sighted_arm_at_two_H_differs_where_its_samples_do(self):
        s = _run_all()
        for kind in s["kinds"]:
            a, b = s["traces"][(kind, True, s["h1"])], s["traces"][(kind, True, s["h2"])]
            got = first_difference(a["strict"], b["strict"])
            want = next((i for i in range(len(a["want"])) if not np.array_equal(a["want"][i], b["want"][i])), None)
            self.assertIsNotNone(got, kind)
            self.assertEqual(got, want, kind)

    def test_a_short_training_blinded_at_two_H_is_bit_for_bit(self):
        s = _run_all()
        a, b, again = (s["trains"][(False, s["h1"], 0)], s["trains"][(False, s["h2"], 0)],
                       s["trains"][(False, s["h1"], 1)])
        self.assertEqual(a["updates"], TRAIN_STEPS - 100)
        self.assertTrue(np.all(a["obs_prev"] == 0.0) and np.all(b["obs_prev"] == 0.0))
        self.assertTrue(np.array_equal(a["params"], again["params"]), "the same H twice differs")
        self.assertEqual(a["buffer"], again["buffer"])
        self.assertTrue(np.array_equal(a["params"], b["params"]))
        self.assertEqual(a["buffer"], b["buffer"])

    def test_control_a_short_training_sighted_at_two_H_differs(self):
        s = _run_all()
        a, b = s["trains"][(True, s["h1"], 0)], s["trains"][(True, s["h2"], 0)]
        self.assertGreater(np.count_nonzero(a["obs_prev"]), 0)
        self.assertFalse(np.array_equal(a["params"], b["params"]))
        self.assertNotEqual(a["buffer"], b["buffer"])


def report():
    """The MEASURED lines row 135 (5) quotes, read off the results."""
    s = _run_all()
    out = [f"[BlindBitForBit, P1's H parameter; goldens pinned on {GOLDEN_PARENT}] use_preview off, {STEPS} steps "
           f"({STEPS // 2} neutral, then default_rng(0) actions), the B58, dt {DT:g}"]
    out.append("  H (s): " + ", ".join(f"{h:.4f}" for h in s["hs"]))
    for kind in s["kinds"]:
        label = {"d34": f"decision-34 road ({s['road']})", "extremes": "ExtremesTrainingEnv seed 0",
                 "four_engine": "four-engine training road seed 0 (build_env's branch, share off)"}[kind]
        ref = s["traces"][(kind, False, 30.0)]
        same = all(s["traces"][(kind, False, h)]["strict"] == ref["strict"] for h in s["hs"])
        zero = all(np.all(s["traces"][(kind, False, h)]["prev"] == 0.0) for h in s["hs"])
        out.append(f"  blinded, {label}: {len(s['hs'])} H give one trajectory bit for bit: {same}; every preview "
                   f"sample 0.0: {zero}; trajectory {_short(trace_sha(ref['strict']))}")
    m = s["traces"][("four_engine", False, 30.0)]["strict"] == \
        s["traces"][("four_engine_build_env", False, E.PREVIEW_H_S)]["strict"]
    out.append(f"  the four-engine road at H = 30 s passed is train.build_env's default H bit for bit: {m}")
    tr = s["trains"]
    a, b, again = tr[(False, s["h1"], 0)], tr[(False, s["h2"], 0)], tr[(False, s["h1"], 1)]
    out.append(f"  short training, blinded (SAC seed 0, {TRAIN_STEPS} steps, {a['updates']} updates, cpu, four-engine "
               f"road): H = {s['h1']:.4f} s and H = {s['h2']:.4f} s give identical parameters: "
               f"{bool(np.array_equal(a['params'], b['params']))} ({a['params'].size} values), identical replay "
               f"buffer: {a['buffer'] == b['buffer']}; H = {s['h1']:.4f} s twice identical: "
               f"{bool(np.array_equal(a['params'], again['params']))}")
    out.append(f"  CONTROL (mistake 12), sighted at H = {s['h1']:.4f} s and H = {s['h2']:.4f} s:")
    for kind in s["kinds"]:
        x, y = s["traces"][(kind, True, s["h1"])], s["traces"][(kind, True, s["h2"])]
        got = first_difference(x["strict"], y["strict"])
        want = next((i for i in range(len(x["want"])) if not np.array_equal(x["want"][i], y["want"][i])), None)
        ok = np.array_equal(x["prev"], x["want"]) and np.array_equal(y["prev"], y["want"])
        out.append(f"    {kind}: trajectories differ: {got is not None}, first at step {got} (expected samples first "
                   f"differ at step {want}); samples = 12 x grade[min(k + int(h/dt), n - 1)] at every step: {ok}")
    x, y = tr[(True, s["h1"], 0)], tr[(True, s["h2"], 0)]
    diff = float(np.max(np.abs(x["params"].astype(np.float64) - y["params"].astype(np.float64))))
    out.append(f"    short training: identical parameters: {bool(np.array_equal(x['params'], y['params']))} "
               f"(max |difference| {diff:.3g}, {int(np.count_nonzero(x['params'] != y['params']))} of "
               f"{x['params'].size} values differ); identical replay buffer: {x['buffer'] == y['buffer']}")
    gl = s["goldens"]
    for name, want in GOLDEN.items():
        got = gl[(name, None)]
        out.append(f"  defaults, {name}: {_short(got)} (pinned on {GOLDEN_PARENT}: "
                   f"{_short(want) if want else None}) equal: {got == want}")
    name = "b58 phase-d EPISODES[0], dt 1, 300 steps"
    out.append(f"  CONTROL: the phase-d digest at H = {s['h2']:.4f} s moves: {gl[(name, s['h2'])] != gl[(name, None)]}")
    return "\n".join(out)


def tearDownModule():
    if STATE:
        print("\n" + report(), flush=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)

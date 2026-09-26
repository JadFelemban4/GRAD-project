# Agent Replay, Milestone 1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Milestone M1 of the approved agent-replay design (docs/superpowers/specs/2026-09-26-agent-replay-design.md, section 10): a new page /agents, served only by `python -m app.server --simulation`, that computes ONE frozen test episode for ONE C4 pair (the sighted and the blind agent of one seed) live on the scoring protocol (dt 1.0, 719 steps). It streams paired frames while they are computed and draws both cars side by side on a road built from the episode's own grade: a whole-route side profile at ×3 vertical exaggeration and a Three.js chase view at true slope. The page has a timeline that waits at the computed edge; a pause panel with the five APPLIED actions in Arabic plus the command when the rate limit held it back, what the sighted car saw ahead, the weights, damage so far, turbine against the limit, torque delivered against requested, and a device line; the C4 verdict quoted word for word with file:line, plus a short line and glosses; a SIMULATED badge; and a dt caption. Every number on the page comes from a tracer that a test proves `==` to evaluate.run_episode through the store's own worker thread. The M1 page reads ?runs=runs_c4&seed=5&ep=1 into a read-only picker and computes only when «احسب» is pressed. M1 leaves out discover(), the catalog route, the three-select picker, the Phase D and D2 verdicts, the simulation.html nav link (all M2) and anything jev (M3), and it is written so that it does not block them: lanes and cars are lists, verdict tables are keyed by prefix, the key format is "runs_c4/5/1", and Trace keeps the observations.

**Architecture:**

Python, three new top-level app/ modules (so app.test_replay's test_read_only scans them unchanged), imported only from the --simulation branch of app/server.py.
(1) app/agent_trace.py: frozen episodes from evaluate.EPISODES/EPISODES_D2 (1-based idx); build_cycle (make_grade_climb or random_road.climb, never RandomClimb); route(cycle), which builds 720-vertex geometry (s, x=Σds·cosθ, z=Σds·sinθ, θ=atan g) without touching the cycle; jsonable, which converts numpy before app.replay.finite; and run_lanes, a step-interleaved copy of evaluate.py:175-202 for N lanes that calls on_frame(frame, seen_obs) once per paired step.
(2) app/agent_catalog.py (M1 subset): live_fingerprint (cached, and it sets GIT_OPTIONAL_LOCKS); read_agent, which follows the section 4 status order with evaluate's own arm-by-path rule; scored_shas, which reads results/<prefix>_seed<k>.txt through analyse_c4.BUDGET with the path separators normalised; find_pair (KeyError or Refused); and verdict(prefix), which quotes anchors from results/ as {file, line, text}, with the authored SHORT_VERDICT and GLOSS only for the 'c4' row.
(3) app/agent_api.py: pair_paths/load_pair (SAC.load(dir + "/final") with no device, the same call as evaluate.py:370); as_policy; versions(), which reads sys.modules and never imports; the Trace dataclass; EpisodeStore, one daemon 'agent-builder' worker modelled on ReplayStore: streaming, cancellable only by preempt, keep=2, errors reported once, and the lock never held during load or trace; episode_meta; and install(app, store=None), which adds GET /agents and GET /api/agents/episode, both with no-store caching.
Browser, ES modules under app/static/sim/. The lab's scene.mjs gains three `export` keywords (stage, ribbonGeometry, supra) and i18n.mjs gains one key (nav.agents). agents-strings.mjs merges every page string into i18n.STRINGS at import and throws on a collision or a key present in only one language. agent-view.mjs holds the pure, node-tested logic: road sampling, episodeAt, profile points, preview marks, gauges, the wait-at-edge play state, appendFrames and parseEpisodeQuery. agent-scene.mjs builds the chase view from stage/ribbonGeometry/supra with a floating origin, a static camera and two cars at ±1.9 units. agents.html, agents.css and agents.mjs make up the RTL page. agents.mjs polls every 400 ms with since=frames.length, appends only contiguous slices, and loads the chase view by dynamic import, so a Three.js failure cannot take down the verdict box, the badge, the profile or the panel.
Data flow: the «احسب» click sends one preempt=1 request. The route runs find_pair (404/409/503) and then store.poll; when since=0 the response also carries meta and road, so the profile draws at once. Later polls bring frames[since:], and the device and versions travel as top-level fields of every response. When status is 'ready', settleDone fixes the end of the timeline. Nothing is written to disk anywhere.

**Tech Stack:** Python 3.12 system interpreter (C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe), numpy, gymnasium env from engine_env (import only), stable-baselines3 SAC + torch imported lazily inside the worker (on this machine: SB3 2.9.0, torch 2.11.0+cu128, CUDA available; read versions from the run), FastAPI + uvicorn (existing server), stdlib unittest (app/test_agents.py, `python -m app.test_agents [--full]`), fastapi.testclient; browser ES modules, Three.js 0.180.0 vendored at app/static/vendor/three (gitignored, produced by app\start-simulation.ps1), node:test on Node 24 (`node --test "app/static/sim/*.test.mjs"`, glob quoted).

**Spec:** `docs/superpowers/specs/2026-09-26-agent-replay-design.md` (APPROVED by Jad, 26 September 2026; its walkthrough log records his answers). Measurements and traps: `docs/superpowers/specs/2026-09-26-agent-replay-recon.md`. Executors read both.

**How this plan was written.** A plan workflow on 26 September 2026: one skeleton with every interface, four authors (Python trace, Python serving, pure frontend, page) who prototyped and ran their code in a scratch copy, one critic who assembled all ten build tasks into a scratch copy of the repository and ran every suite (`app.test_agents` 37 tests OK with the proof PROVEN on cuda; the lab suites unchanged), and one revision of the page group. Milestones M2 (every experiment) and M3 (jev, the paused moment) get their own plans after M1 works.

## Global Constraints

- READ-ONLY for the vehicle and the experiments: never write to the ECU; no training, no evaluation, no writes into runs*/, results/ or anywhere on disk. Traces live in memory only (one in-flight trace plus keep = 2 finished ones). runs/, runs_d2/ and runs_c4/ are CLOSED: read meta.json and final.zip only.
- Never edit plant.py, thermal.py, engine_env.py, random_road.py, fingerprint.py, train.py, evaluate.py or run_phase_d.py; import only. Never add a key to engine_env's `info`: that would move plant_sha and lock out all 48 agents. Read env attributes instead (env.prev_act, env.map_kpa, env.ep['damage']).
- The mirror copies evaluate.py:175-202 step for step. Each lane builds its OWN cycle: make_grade_climb(duration=DURATION, dt=DT) for phase-d, random_road.climb(start_s, grade, duration=DURATION, dt=DT) for d2, never RandomClimb. Then SupervisoryTunerEnv(cycle, dt=DT, seed=seed, use_preview=...), env.reset(seed=seed), env.w = np.asarray(weights, dtype=np.float32), obs = env._obs(), with no second reset. Peak = max(info['t_turb']) starting from 0.0. A lane ends on term or trunc. Result keys are exactly ret, damage, fuel, torque_viol, peak_turb (peak - 273.15), knock.
- DT = 1.0, DURATION = 720.0, STEPS = 719 (engine_env.py:820 truncated = k >= n-1), PREVIEW = slice(14, 14 + len(PREVIEW_S)), GRADE_OBS_SCALE = 12.0. Horizons are always read from engine_env.PREVIEW_S (2, 5, 15, 30 s) and never from a page constant.
- Models: SAC.load(dir + '/final') with NO device argument, exactly evaluate.py:370; policies are evaluate.agent_policy(model); str(model.device), torch.__version__ and stable_baselines3.__version__ are recorded and shown. CPU and CUDA give different episodes (recon section 2).
- The == proof has no tolerance. If it ever fails, find the cause; the fallback is sequential lanes, never an epsilon.
- app.replay.finite() rejects numpy float32. Every frame field, meta.act and road array goes through jsonable first (arrays through .tolist(), np.bool_ to bool, NaN/inf to None). json.dumps(..., allow_nan=False) must succeed.
- Store key (runs, seed, idx) with idx 1..20 (EPISODES_D2[idx-1]), serialised 'runs_c4/5/1'. One daemon worker named 'agent-builder'; any other key gets busy; only preempt=1 cancels, and only the first request after «احسب» sends it. on_frame raises app.replay.BuildCancelled when the cancel event is set. Cancelled or partial traces are never kept. The worker catches Exception AND SystemExit, records one fixed message ('build failed: <ExceptionClassName>', never str(exc)), reports it once, then forgets it. Never call evaluate.check_model_fingerprint; call fingerprint.compare.
- Routes exist only through app.agent_api.install(app), called inside `if a.simulation:` in app/server.py main() (:298). Module-level routes of server.py do not change, so --live/--replay never import agent code. Every M1 route is a GET and carries Cache-Control: no-store. Unknown or malformed runs/seed/ep give 404 and no path is ever resolved from a request; a refused pair gives 409 {status:'refused', problems}; a missing SB3 gives 503. The browser polls every 400 ms.
- live_fingerprint() runs os.environ.setdefault('GIT_OPTIONAL_LOCKS', '0') before its first call (plant_fingerprint runs `git status`, which could otherwise rewrite .git/index) and caches per protocol.
- Verdicts are quoted, never computed, and each is cited as results/<file>:<line>. The short line is authored text, shown only when every anchor it summarises was found; otherwise it becomes the not-found text. The page computes no statistic and no difference between the two cars, and shows no winner.
- Road geometry: theta = atan g; ds_k = v_k*dt over the 719 stepped samples; 720 vertices; drawn FROM the scenario and never fed back into it (the cycle arrays are byte-identical after route()).
- Scene values: the profile uses VE = 3 and says «المقياس الرأسي مضخّم ×3». The chase view uses M = 10 m per world unit on both axes and says «الميل غير مضخّم · السيارة ليست بمقياسها». CAR_OFFSET = ±1.9 units, LANE_W = 3.2, ROAD_W = 7.6 (supra's half-width is 1.486 measured). Both cars share one s. Preview is shown as four markers, not a band, for the sighted car only, on a single-hue ramp from 0 to 16 %.
- Colour tokens --agent-sighted (blue) and --agent-blind (amber) are defined in :root, :root[data-theme="dark"] and @media(prefers-color-scheme:dark){:root:not([data-theme="light"])}, and are never red or green.
- Wording: always «حاسوب المحرك المنمذَج», never «حاسوب المحرك» alone; action 2 is «إزاحة سقف ضغط الشحن» and is shown beside the agent's own map_kpa; no string says 'preview helps', «يساعد الاستباق» or «الاستباق يساعد». The panel shows the APPLIED action (env.prev_act) and shows the command on a second line only where held.
- Layout: at ≥ 1100 px an RTL grid of minmax(0,1.6fr) minmax(320px,1fr); the main column holds chase (16:9) + overlay, timeline, profile, and the side column holds picker, verdict box, pause panel. At < 760 px one column with a 16 px gutter and no horizontal scroll, in the order badge, picker, verdict, chase (4:3), timeline, profile, pause panel. The nav reads simulation, agents (active), monitor, review, and agents.css restores the last nav link that the lab hides on phones. Arabic is the default with the lab's language toggle; the page follows prefers-color-scheme.
- /simulation behaves exactly as today. No lab test file changes. app.test_simulation, app.test_replay --full (49) and the node glob must pass unchanged, with counts read from each run, not from documents.
- New app/*.py files must pass app/test_replay.py test_read_only (:522-553): docstrings use triple double quotes; no `.write(` except on lines containing `fh.write`; banned tokens in tests are written as raw regexes (r"\.write\s*\("). Fixtures are built with shutil.copy, json.dump(obj, fh), FP.claim_running/release_running, in tempfile directories OUTSIDE the repo.
- Environment: PY=C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe (a .venv is blocked by App Control), with PYTHONIOENCODING=utf-8, PYTHONDONTWRITEBYTECODE=1 and GIT_OPTIONAL_LOCKS=0. Run with cwd = the repo root and never with %TEMP% as cwd (a stray inspect.py there shadows the stdlib).
- Commits go to branch JMF-2340550-sep17 only. Every commit touching app/ pastes the output of `$PY -m app.test_replay` (and `--full` at the milestone) into its message. Before committing a new tracked file: `git add` it, run `$PY verify_docs.py` and read its last line (currently 'All 67 checks pass (...)'); a new docstring can trip a figure listed in verify_docs.RETIRED. Every message ends with the line 'Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>'.
- TDD for every task: write the failing test, run it and see it fail, implement, run it and see it pass, commit. Steps are 2-5 minutes each, with complete code in every code step and no placeholders.
- M1 scope: the page reads ?runs=runs_c4&seed=5&ep=1 into a READ-ONLY picker. Nothing is selected by default without a query, and nothing computes until «احسب». M1 carries only the C4 verdict row, short line and glosses. There is no recorded-drive data on this page.

## Review Focus

- **EpisodeStore holds its lock while doing slow work. The prototype's versions() imported torch (~3 s) inside `with self._lock:`, and SAC.load or CUDA initialisation could do the same. Polls then block for seconds; the page never shows «تحميل الشبكتين…», its first response arrives already 'building', and the since-slicing starts mid-list.** Expected: episode_for, loader, device/versions and the tracer all run outside the lock; only the assignment of the results happens under it. versions() reads sys.modules and never imports. StoreTests pins it: with a loader that sleeps 1.0 s, every poll returns in < 0.1 s with status 'loading'. (pinned in T5)
- **Stale or overlapping poll responses get appended: a second «احسب», a slow response landing after a faster one, or a retry after «الخادم غير متاح». Frames end up duplicated or skipped, so frames[k].k != k, and the pause panel and chase view show the decision of a different second than the clock says.** Expected: agent-view.appendFrames(frames, payload) accepts a slice only when payload.since === frames.length and every incoming frame's k equals its index; otherwise it changes nothing and returns false. agents.mjs appends through it alone and drops any response whose loadToken is old. Node tests cover stale since, overlap, gap and empty slices. (pinned in T8)
- **The viewer presses play at the computed edge, which sets the waiting flag. The build then finishes with a 'ready' poll that brings no new frames, or a cached 'ready' delivers all 719 frames in one response. resumeIfStalled never fires, so the play button stays 'waiting' forever and the last seconds cannot be replayed.** Expected: settleDone(state, end, now) is called on 'ready': it fixes clock.duration at frames.length (719 → 11:59), clears waiting, and the next play behaves like the lab (rewinds from the end). A node test covers a wait left pending at done; another pins that resumeIfStalled never resumes after pauseByUser. (pinned in T8)
- **results/c4_seed<k>.txt records model paths with Windows backslashes (`model runs_c4\sighted_seed0: ... zip sha 20f0ae6a9c1564a9`). A basename split on '/' finds no sha, so every C4 pair shows «الملف المقيَّم غير مسجَّل في النتائج» instead of a match, and a swapped final.zip would never be refused as «ليس الملف الذي قُيِّم», right where a committee reads the page.** Expected: scored_shas normalises '\\' to '/' before taking the basename. Tests pin that all eight real runs_c4 pairs come back scored 'match' with budget 300000, and that a synthetic results/zz_seed0.txt with a different sha written with a backslash path is Refused with 'not the scored artefact' and both shas (a forward-slash path parses too). (pinned in T3)
- **agents.mjs statically imports agent-scene.mjs (and so 'three'). app/static/vendor/ is gitignored and exists only after app\start-simulation.ps1 runs. If the server is started directly, or Three.js fails to load, the whole ES module graph fails: the verdict box, SIMULATED badge, dt caption, profile and pause panel (every honesty surface) never render, and the page is blank.** Expected: The chase view is loaded with `await import('./agent-scene.mjs')` inside try/catch; on failure #chase shows agents.scene.webgl_error and everything else renders. PageTests asserts that agents.mjs has no static import of './agent-scene.mjs' or 'three', that it does call import('./agent-scene.mjs'), and that every $('id') it uses exists in agents.html. (pinned in T10)

## Where the plan departs from the design, found while writing it

Each was checked by the critic and is carried by the task named; the design file's log records them.

- Design section 5, View 1 says 'x in km against z'. The plan's profile SVG draws no axis, ticks or km labels, only the path, the climb marker and captions. Either add a light km scale (0, 5, 10, 15, 20, 25 km) or amend the design.
- Design section 5, 'Preview' says each marker is coloured by the grade read there, on a single-hue 0-16 % ramp. The plan applies the ramp to the chase-view posts only; the profile's four ticks are all --agent-sighted blue. Say which one the design means, or colour the profile ticks with gradeRamp() too.
- Design section 5 and misreading row 'the sighted agent saw the road' ('Four markers, not a band — views'): at 130 km/h the chase view (~200 m) cannot contain the 15 s and 30 s markers (~540 m and ~1080 m ahead). The design should state that the chase view shows the in-range posts and the profile carries all four.
- Design section 10 M1 Verify says 'app.test_replay --full at 49'. The plan (T11) records 59 of 59 for --full, and 49 of 49 only for the default run (I re-ran the default run: 49 of 49). The design line and the skeleton's T11 test entry should be corrected so that no commit asserts 49 for --full.
- Design section 10 M1 Verify says to check 'with app\start-simulation.ps1 running'. The plan starts `$PY -m app.server --simulation` directly, because the script's last line calls bare `python` (the plan attributes this to the blocked .venv, which I did not verify). The script's banner also prints only the /simulation URL. Either amend the verify line or add the /agents URL to the ps1 banner in M2, which also touches the lab's entry points.
- Design section 3.4 lists device and versions inside meta. The plan (T6) sends them as top-level fields of every poll, because they are known only after the worker loads the networks. This is a sound, documented deviation, but the design text should be amended to match.
- Design section 5 gives the car half-width as 'about 1.48' and node test 'exceeds 2 × 1.48'. The plan measures 1.486 (hub torus) and uses CAR_HALF_WIDTH = 1.49. Update the design numbers so the spec and the test agree.

---

### Task 1: agent_trace: frozen episodes, per-lane cycles, road geometry and jsonable (+ test file skeleton)

**Files:**
- Create: `app/agent_trace.py`
- Create: `app/test_agents.py`
- Test: `app/test_agents.py` (`TraceTests`)

**Interfaces:**
- Consumes: `evaluate.py:98` `DT = 1.0`; `evaluate.py:99` `DURATION = 720.0`; `evaluate.py:103` `EPISODES` (20 × `(seed, (w_track, w_fuel, w_life))`); `evaluate.py:145` `EPISODES_D2` (20 × `(seed, weights, start_s, grade)`); `engine_env.py:834` `make_grade_climb(duration, dt, ...)`, which returns a dict `t, v_mps, grade, t_amb, p_baro, humidity` with n = int(duration/dt) samples and needs duration ≥ 20 s; `random_road.py:101` `climb(start_s, grade, duration, dt, ...)`, same keys; `engine_env.py:517` `PREVIEW_S = (2.0, 5.0, 15.0, 30.0)`; `app/replay.py:31` `finite(value)` (Python int/float only).
- Produces:
  - `app/agent_trace.py` constants: `STEPS = 719`, `PREVIEW = slice(14, 14 + len(PREVIEW_S))`, `GRADE_OBS_SCALE = 12.0`, `DT` and `DURATION` re-exported from evaluate, and `PROTOCOL_EPISODES = {'phase-d': EPISODES, 'd2': EPISODES_D2}`.
  - `jsonable(x)`: dict → `{str(k): jsonable(v)}`; list, tuple or ndarray → list; bool or `np.bool_` → bool (checked before int); int or `np.integer` → int; float or `np.floating` → `finite(float(x))`, so NaN/inf → None; str and None unchanged. Anything else raises `TypeError`. That last rule is an addition to the skeleton, so an unexpected type fails loudly instead of later inside `json.dumps`.
  - `episode(protocol, idx)` → `{'protocol', 'idx', 'seed', 'weights': (3 floats), 'road': None | (start_s, grade)}`. `idx` is 1-based. It raises `KeyError` for an unknown protocol, a non-int `idx` (including `bool`), or `idx` outside 1..20.
  - `build_cycle(ep)` returns a fresh cycle on every call.
  - `route(cycle)` → `{'s_m', 'x_m', 'z_m', 'grade_pct', 'speed_kmh'}`, each a list of 720, plus `length_m`, `rise_m`, `climb_start_s`, `p_baro_kpa` and `t_amb_c`. Everything is passed through `jsonable`, and the cycle is never changed.
  - `app/test_agents.py`: `ROOT`, `FULL`, `class TraceTests`, and the `__main__` block that strips `--full`.

All commands in this group run in Git Bash from the repository root, with the plan's environment:

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
SCRATCH="<this session's scratchpad directory>"   # outside the repo, never %TEMP% itself
```

- [ ] **Step 1: Write the failing test**

Create `app/test_agents.py` with exactly:

```python
"""The agent replay page's own suite. Nothing here writes, trains or evaluates.

    python -m app.test_agents          the default suite
    python -m app.test_agents --full   adds the slow checks

Run from the repository root. app/test_replay.py's test_read_only scans this
file too, so banned tokens are written as raw regexes, never as calls, and
fixtures are made in temporary directories OUTSIDE the repository.
"""
import json
from pathlib import Path
import sys
import unittest

import numpy as np

from app import agent_trace as T
from evaluate import EPISODES, EPISODES_D2

ROOT = Path(__file__).resolve().parent.parent
FULL = "--full" in sys.argv


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


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]] + [a for a in sys.argv[1:] if a != "--full"], verbosity=2)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `$PY -m app.test_agents`
Expected: the module does not import. `app` is a namespace package (it has no `__init__.py`), so the message is:
```
    from app import agent_trace as T
ImportError: cannot import name 'agent_trace' from 'app' (unknown location)
```

- [ ] **Step 3: Implement**

Create `app/agent_trace.py` with exactly:

```python
"""One frozen test episode, and its road, for the agent replay page (/agents).

episode() and build_cycle() rebuild a scored episode exactly as
evaluate.run_episode builds it (evaluate.py:175-202). route() turns that
episode's cycle into road geometry for the page. jsonable() makes numpy values
safe for JSON.

What this module never does:

- it never writes: no file, no cache, no result;
- route() never calls the plant and never writes into the cycle it reads:
  the road is drawn FROM the scenario and nothing it returns reaches an env.
"""
from __future__ import annotations

import numpy as np

import random_road as RR
from app.replay import finite
from engine_env import PREVIEW_S, make_grade_climb
from evaluate import DT, DURATION, EPISODES, EPISODES_D2

# An episode is 719 steps, not 720: engine_env.py truncates at k >= n - 1.
STEPS = 719
# Observation indices 14..17 are the preview, each grade multiplied by 12
# (engine_env._obs). Horizons always come from engine_env.PREVIEW_S.
PREVIEW = slice(14, 14 + len(PREVIEW_S))
GRADE_OBS_SCALE = 12.0
PROTOCOL_EPISODES = {"phase-d": EPISODES, "d2": EPISODES_D2}


def jsonable(x):
    """A JSON-safe copy of `x`: numpy scalars and arrays become Python values.

    app.replay.finite() accepts only Python int and float, and numpy float32
    is neither, so without this every action and preview value would reach
    the page as null. NaN and infinity become None. bool is tested before int
    because bool is a subclass of int.
    """
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, np.ndarray):
        return [jsonable(v) for v in x.tolist()]
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        return finite(float(x))
    if x is None or isinstance(x, str):
        return x
    raise TypeError(f"not JSON-safe: {type(x).__name__}")


def episode(protocol, idx):
    """Frozen episode `idx` (1-based) of a protocol: 'phase-d' or 'd2'.

    idx 1 is the table's first row. The seed and the weights are the scored
    ones, untouched; `road` is None for Phase D's fixed climb and
    (start_s, grade) for a randomised one. KeyError for anything else.
    """
    table = PROTOCOL_EPISODES[protocol]
    if isinstance(idx, bool) or not isinstance(idx, int) or not 1 <= idx <= len(table):
        raise KeyError(f"no episode {idx!r} in {protocol}")
    row = table[idx - 1]
    road = None if protocol == "phase-d" else (float(row[2]), float(row[3]))
    return {"protocol": protocol, "idx": idx, "seed": int(row[0]),
            "weights": tuple(float(w) for w in row[1]), "road": road}


def build_cycle(ep):
    """A fresh cycle on every call, built exactly as evaluate.run_episode does.

    Never random_road.RandomClimb: that wrapper draws its own road.
    """
    if ep["road"] is None:
        return make_grade_climb(duration=DURATION, dt=DT)
    return RR.climb(ep["road"][0], ep["road"][1], duration=DURATION, dt=DT)


def route(cycle):
    """The road as geometry: 720 vertices along a straight-in-plan route.

    theta = atan(grade), the slope engine_env's vehicle model uses. Over the
    719 stepped samples, ds_k = v_k * DT, and x and z are the cumulative sums
    of ds*cos(theta) and ds*sin(theta). Reads the cycle and returns new lists.
    """
    v = np.asarray(cycle["v_mps"], dtype=float)
    g = np.asarray(cycle["grade"], dtype=float)
    ds = v[:STEPS] * DT
    theta = np.arctan(g[:STEPS])
    s = np.concatenate([[0.0], np.cumsum(ds)])
    x = np.concatenate([[0.0], np.cumsum(ds * np.cos(theta))])
    z = np.concatenate([[0.0], np.cumsum(ds * np.sin(theta))])
    on_climb = np.flatnonzero(g > 0)
    return jsonable({
        "s_m": s, "x_m": x, "z_m": z,
        "grade_pct": g * 100.0,
        "speed_kmh": v * 3.6,
        "length_m": float(s[-1]),
        "rise_m": float(z[-1]),
        "climb_start_s": float(cycle["t"][on_climb[0]]) if on_climb.size else None,
        "p_baro_kpa": float(cycle.get("p_baro", 101.3)),
        "t_amb_c": float(cycle["t_amb"]) - 273.15,
    })
```

- [ ] **Step 4: Run to verify it passes**

Run: `$PY -m app.test_agents`
Expected (measured in the prototype, which imported the real repository modules):
```
test_episode_indexing (__main__.TraceTests.test_episode_indexing) ... ok
test_jsonable_converts_numpy (__main__.TraceTests.test_jsonable_converts_numpy) ... ok
test_route_geometry (__main__.TraceTests.test_route_geometry) ... ok
----------------------------------------------------------------------
Ran 3 tests in 0.007s

OK
```
The prototype measured these figures: length 25602.8 m on episode 1; rise 2754.6 m (ep 1), 1916.8 m (ep 5, seed 1004) and 3246.9 m (ep 6, seed 1005); `climb_start_s` 141.0 (d2 ep 1) and 180.0 (phase-d).

- [ ] **Step 5: Commit**

```bash
git branch --show-current                     # must print JMF-2340550-sep17
git add app/agent_trace.py app/test_agents.py
$PY verify_docs.py 2>&1 | tail -1
```
Expected: `All 67 checks pass (782 figure mentions scanned in the documents).` This was measured on a `git archive` copy of `564927e` with all three new files of this group tracked: they leave the check count and the figure-mention total unchanged. Read the line off the run.

```bash
$PY -m app.test_agents > "$SCRATCH/t1_agents.txt" 2>&1; tail -1 "$SCRATCH/t1_agents.txt"   # OK
$PY -m app.test_replay > "$SCRATCH/t1_replay.txt" 2>&1; tail -1 "$SCRATCH/t1_replay.txt"   # 49 of 49 checks pass (~70 s)
{
cat <<'EOF'
Agent replay T1: agent_trace -- frozen episodes, per-lane cycles, road, jsonable

app/agent_trace.py: episode(protocol, idx), 1-based, KeyError outside 1..20;
build_cycle(ep), built exactly as evaluate.run_episode builds it (never
RandomClimb); route(cycle), 720 vertices with theta = atan g, cycle arrays
byte-identical afterwards; jsonable(), numpy -> JSON with NaN/inf -> None.
app/test_agents.py: the suite's skeleton and TraceTests. Nothing is written.
EOF
echo
echo '$ python -m app.test_agents'
cat "$SCRATCH/t1_agents.txt"
echo
echo '$ python -m app.test_replay'
cat "$SCRATCH/t1_replay.txt"
echo
echo 'Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>'
} > "$SCRATCH/t1_msg.txt"
git commit -F "$SCRATCH/t1_msg.txt"
git log --oneline -1
```

---


---

### Task 2: run_lanes: the step-interleaved mirror of evaluate.run_episode, proven == on a C4 pair

**Files:**
- Modify: `app/agent_trace.py:1-13` (module docstring), `app/agent_trace.py:20` (the engine_env import), and append after `app/agent_trace.py:108` (end of file)
- Modify: `app/test_agents.py:10-18` (imports), and insert after `app/test_agents.py:83` (the last line of `test_route_geometry`)
- Test: `app/test_agents.py` (`TraceTests` + `ProofTests`)

**Interfaces:**
- Consumes:
  - `evaluate.py:175-202` `run_episode(policy, seed, weights, use_preview=True, road=None)` and `evaluate.py:205` `agent_policy(model)`.
  - From engine_env:
    - `:521` `SupervisoryTunerEnv(cycle, dt=..., seed=..., use_preview=...)`
    - `:674` `reset(seed=)`
    - `:646` `_obs()`, float32[23]
    - `:639` `_preview()`
    - `:544` `_rescale(a)`
    - `:713` `step(a)`, where `:724-726` applies the slew and the bounds, `:817` sets `prev_act = act`, `:819` sets terminated when the reward is not finite, and `:820` truncates at `k >= n-1`
    - `:822-829` the `info` keys
    - `:513-515` `ACT_LO` / `ACT_HI` / `SLEW`
    - `:953` `neutral_action()`
  - From Task 1: `episode`, `build_cycle`, `route`, `jsonable`, `STEPS`, `PREVIEW`, `GRADE_OBS_SCALE`, `DT`.
- Produces:
  - `run_lanes(lanes, ep, on_frame=None) -> list[dict]`: one result per lane, with keys exactly `ret, damage, fuel, torque_viol, peak_turb, knock`, `==` to `run_episode`'s.
  - Call order at step k: lane 0 steps, then lane 1, then `on_frame(frame, seen)` is called exactly once.
  - `frame = jsonable({'k', 'cars': [car | None per lane]})`. Each `car` has these keys:

    | key | value |
    |---|---|
    | `cmd` | 5 values, the network output |
    | `act` | 5 values, `env.prev_act` after the step (the applied action) |
    | `held` | 5 bools: `act != env._rescale(float32(cmd))` |
    | `preview_pct` | 4 values: `obs_in[PREVIEW] / 12 * 100` |
    | `map_kpa` | float |
    | `turb_c`, `oil_c` | °C |
    | `torque_nm`, `torque_req_nm` | N·m |
    | `damage` | cumulative |

  - `seen[i]` is a float32 copy, shape (23,), of the observation lane i's policy received, or `None` once lane i has stopped.
  - A lane stops on `term or trunc`, and its later cars are `None`.
  - Convention for everything downstream: `lanes[0]` is the sighted car, `lanes[1]` the blind one.
  - `ProofTests` sets `cls.device`, `cls.ep`, `cls.frames`, `cls.got` and `cls.want` in `setUpClass`. Task 5 replaces only `setUpClass`; both tests read only those five attributes.

- [ ] **Step 1: Write the failing test**

1a. In `app/test_agents.py`, replace the import block:

```python
import json
from pathlib import Path
import sys
import unittest

import numpy as np

from app import agent_trace as T
from evaluate import EPISODES, EPISODES_D2
```
with:
```python
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

import numpy as np

from app import agent_trace as T
from engine_env import (ACT_HI, ACT_LO, SLEW, SupervisoryTunerEnv, make_grade_climb,
                        neutral_action)
from evaluate import EPISODES, EPISODES_D2, agent_policy, run_episode
```

1b. Insert the following directly after the last line of `test_route_geometry`:
```python
        self.assertEqual(T.route(T.build_cycle(T.episode("phase-d", 1)))["climb_start_s"], 180.0)
```
Insert it before the two blank lines and `if __name__ == "__main__":`:

```python

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
```

`test_preview_slice_is_the_observation` checks k in (0, 125, 150), not the skeleton's (0, 150, 400). At k = 125 only the 30 s horizon can see the climb that starts at 141 s, which is the sharper check, and stepping two envs to 150 instead of 400 costs about 16 s instead of about 42 s.

- [ ] **Step 2: Run it to verify it fails**

Run: `$PY -m app.test_agents`
Expected, measured in about 23 s:
```
setUpClass (__main__.ProofTests) ... ERROR
test_applied_not_commanded (__main__.TraceTests.test_applied_not_commanded) ... ERROR
test_episode_indexing (__main__.TraceTests.test_episode_indexing) ... ok
test_jsonable_converts_numpy (__main__.TraceTests.test_jsonable_converts_numpy) ... ok
test_lane_stops_on_divergence (__main__.TraceTests.test_lane_stops_on_divergence) ... ERROR
test_preview_slice_is_the_observation (__main__.TraceTests.test_preview_slice_is_the_observation) ... ok
test_route_geometry (__main__.TraceTests.test_route_geometry) ... ok
ERROR: setUpClass (__main__.ProofTests)
AttributeError: module 'app.agent_trace' has no attribute 'run_lanes'
(the same AttributeError for test_applied_not_commanded and test_lane_stops_on_divergence)
Ran 6 tests in 23.229s
FAILED (errors=3)
```
`test_preview_slice_is_the_observation` already passes. It pins Task 1's `PREVIEW`, `STEPS` and scale against the env's own `_obs()`, so it is green before `run_lanes` exists, and that is expected.

- [ ] **Step 3: Implement**

3a. In `app/agent_trace.py`, replace the module docstring's opening:
```python
"""One frozen test episode, and its road, for the agent replay page (/agents).

episode() and build_cycle() rebuild a scored episode exactly as
evaluate.run_episode builds it (evaluate.py:175-202). route() turns that
episode's cycle into road geometry for the page. jsonable() makes numpy values
safe for JSON.

What this module never does:

- it never writes: no file, no cache, no result;
- route() never calls the plant and never writes into the cycle it reads:
```
with:
```python
"""One frozen test episode, stepped live, for the agent replay page (/agents).

run_lanes() mirrors evaluate.run_episode (evaluate.py:175-202) for several
lanes at once, so that every number the page shows comes from the SAME steps
the scored evaluation took. app/test_agents.py proves the mirror == to
run_episode on whole result dicts; if that proof ever fails, the fix is to
find the cause, never to add a tolerance.

What this module never does:

- it never writes: no file, no cache, no result; traces live in memory only;
- it never edits engine_env: it reads env attributes after each step
  (env.prev_act, env.map_kpa, env.ep) instead of adding a key to `info`,
  because editing engine_env.py would move `plant_sha` and lock out every
  trained agent;
- route() never calls the plant and never writes into the cycle it reads:
```

3b. Replace the import line
```python
from engine_env import PREVIEW_S, make_grade_climb
```
with
```python
from engine_env import PREVIEW_S, SupervisoryTunerEnv, make_grade_climb
```

3c. Append to the end of `app/agent_trace.py`, after `route()`:

```python


def _car(env, cmd, obs_in, info):
    """One lane's step, read from the env AFTER the step; nothing is added to it.

    `act` is env.prev_act: the APPLIED action, after rescaling, the slew limit
    and the bounds (engine_env.py:724-726). `held` marks where that differs
    from the network's command. `preview_pct` is decoded from the observation
    the policy was actually given, so the blind car's zeros are its real ones.
    """
    cmd = np.asarray(cmd, dtype=np.float32)
    act = np.array(env.prev_act, dtype=np.float32)
    return {
        "cmd": cmd,
        "act": act,
        "held": act != env._rescale(cmd),
        "preview_pct": obs_in[PREVIEW] / GRADE_OBS_SCALE * 100.0,
        "map_kpa": float(env.map_kpa),
        "turb_c": info["t_turb"] - 273.15,
        "oil_c": info["t_oil"] - 273.15,
        "torque_nm": info["torque"],
        "torque_req_nm": info["torque_req"],
        "damage": float(env.ep["damage"]),
    }


def run_lanes(lanes, ep, on_frame=None):
    """Step one frozen episode for N (policy, use_preview) lanes, interleaved.

    A copy of evaluate.run_episode, step for step, for each lane: its own
    cycle, its own env, reset once with the episode seed, the weights pinned
    after the reset and the observation rebuilt, then step until terminated
    or truncated. At step k lane 0 steps, then lane 1, and so on; then
    on_frame(frame, seen) is called once, where seen[i] is a float32 copy of
    the observation lane i's policy received (None once lane i has stopped).
    A lane that terminates early stops; its later cars are None.

    Returns one dict per lane with exactly run_episode's keys and values.
    Lane order is the caller's; everywhere in this feature lane 0 is the
    sighted agent and lane 1 the blind one.
    """
    state = []
    for policy, use_preview in lanes:
        cycle = build_cycle(ep)
        env = SupervisoryTunerEnv(cycle, dt=DT, seed=ep["seed"], use_preview=use_preview)
        obs, _ = env.reset(seed=ep["seed"])
        env.w = np.asarray(ep["weights"], dtype=np.float32)   # override the fresh draw
        obs = env._obs()
        state.append({"policy": policy, "env": env, "obs": obs, "ret": 0.0,
                      "peak": 0.0, "info": None, "done": False})
    k = 0
    while not all(s["done"] for s in state):
        cars, seen = [], []
        for s in state:
            if s["done"]:
                cars.append(None)
                seen.append(None)
                continue
            env, obs_in = s["env"], s["obs"]
            a = s["policy"](env, obs_in)
            obs, r, term, trunc, info = env.step(a)
            s["ret"] += r
            s["peak"] = max(s["peak"], info["t_turb"])
            s["obs"], s["info"], s["done"] = obs, info, bool(term or trunc)
            cars.append(_car(env, a, obs_in, info))
            seen.append(np.array(obs_in, dtype=np.float32, copy=True))
        if on_frame is not None:
            on_frame(jsonable({"k": k, "cars": cars}), seen)
        k += 1
    out = []
    for s in state:
        e = s["info"]["episode_summary"]
        out.append(dict(ret=s["ret"], damage=e["damage"], fuel=e["fuel"],
                        torque_viol=e["torque_viol"], peak_turb=s["peak"] - 273.15,
                        knock=e["knock_events"]))
    return out
```

- [ ] **Step 4: Run to verify it passes**

Run: `$PY -m app.test_agents`
Expected, measured on this machine (CUDA) in about 3 min 40 s. The `== proof` line prints after the summary, because stdout is buffered behind unittest's stderr:
```
test_frames_are_the_episode (__main__.ProofTests.test_frames_are_the_episode) ... ok
test_tracer_equals_run_episode (__main__.ProofTests.test_tracer_equals_run_episode) ... ok
test_applied_not_commanded (__main__.TraceTests.test_applied_not_commanded) ... ok
test_episode_indexing (__main__.TraceTests.test_episode_indexing) ... ok
test_jsonable_converts_numpy (__main__.TraceTests.test_jsonable_converts_numpy) ... ok
test_lane_stops_on_divergence (__main__.TraceTests.test_lane_stops_on_divergence) ... ok
test_preview_slice_is_the_observation (__main__.TraceTests.test_preview_slice_is_the_observation) ... ok
test_route_geometry (__main__.TraceTests.test_route_geometry) ... ok
----------------------------------------------------------------------
Ran 8 tests in 220.466s

OK

  == proof on cuda: sighted damage 501.56474787343603, blind damage 1229.059247261675
```
- The prototype run confirmed that the NaN lane terminates at step 0 with `episode_summary` present.
- The sighted `held` counts are [109, 66, 11, 30, 13], as in recon section 5.
- If the proof line says a device other than `cuda`, the equality still holds, because both sides ran on that device. Say so in the commit message.
- If `==` fails, stop and diagnose (superpowers:systematic-debugging). Never add a tolerance; the fallback is sequential lanes.

- [ ] **Step 5: Commit**

```bash
git branch --show-current                     # JMF-2340550-sep17
git add app/agent_trace.py app/test_agents.py
$PY verify_docs.py 2>&1 | tail -1             # All 67 checks pass (...); read it off the run
$PY -m app.test_agents > "$SCRATCH/t2_agents.txt" 2>&1; tail -3 "$SCRATCH/t2_agents.txt"
$PY -m app.test_replay > "$SCRATCH/t2_replay.txt" 2>&1; tail -1 "$SCRATCH/t2_replay.txt"   # 49 of 49 checks pass
{
cat <<'EOF'
Agent replay T2: run_lanes -- the step-interleaved mirror of run_episode, proven ==

run_lanes(lanes, ep, on_frame) copies evaluate.py:175-202 per lane (own cycle,
own env, one reset, weights pinned, obs rebuilt) and steps the lanes
interleaved, calling on_frame once per paired step. Frames carry the APPLIED
action (env.prev_act), the command, held flags, the preview decoded from the
observation the policy saw, map_kpa, turbine/oil, torque and damage; all JSON
safe. ProofTests: == on whole result dicts against run_episode for
runs_c4/*_seed0 on EPISODES_D2[0], no tolerance. Nothing is written.
EOF
echo
echo '$ python -m app.test_agents'
cat "$SCRATCH/t2_agents.txt"
echo
echo '$ python -m app.test_replay'
cat "$SCRATCH/t2_replay.txt"
echo
echo 'Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>'
} > "$SCRATCH/t2_msg.txt"
git commit -F "$SCRATCH/t2_msg.txt"
git log --oneline -1
```

---


---

### Task 3: agent_catalog (M1 subset): agent status, the scored-artefact check, and the quoted C4 verdict

**Files:**
- Create: `app/agent_catalog.py`
- Modify: `app/test_agents.py`. Add imports at the top and constants below `FULL = ...`. Put the helpers and `class CatalogTests` above `if __name__ == "__main__":`.
- Test: `app/test_agents.py` (`$PY -m app.test_agents CatalogTests`)

**Interfaces:**
- Consumes:
  - `fingerprint.py:482 read(path) -> dict | None`
  - `fingerprint.py:289 compare(a, b) -> [(field, stored, live)]` (FATAL fields only; never raises)
  - `fingerprint.py:213 plant_fingerprint(protocol, **advisory)`, which runs `git status` through `_git`
  - `fingerprint.py:342 model_budget(zip) -> {num_timesteps, total_timesteps, num_timesteps_at_start, buffer_size, sha} | None`
  - `fingerprint.py:473 format_budget(b)`
  - `fingerprint.py:434 running_pid(dir)`; `claim_running` / `release_running` (fixtures only)
  - `run_phase_d.py:94 result_prefix(out)`; `run_phase_d.py:113 CLOSED_PREFIX`
  - `analyse_c4.py:83 BUDGET` (group 1 is the model path, group 6 the 16-hex zip sha)
  - `evaluate.py:98-99 DT, DURATION`
  - `evaluate.py:369` (arm = `"blind" in path`)
  - `results/C4_RESULT.txt` lines 29, 33-34, 42, 48 and 50-53
  - `results/PREREGISTRATION_C4.md` lines 41-43 and 633-635
  - `results/c4_seed<k>.txt:24,26` (model paths written with backslashes)
- Produces (exactly the skeleton's):
  - `ROOT`, `RUNS_NAME`, `AGENT_NAME`, `ARMS`, `Refused(.problems)`
  - `live_fingerprint(protocol)` (cached), `FINGERPRINT_TAKEN`
  - `protocol_of(meta)`, `read_agent(runs, name, root=ROOT)`, `scored_shas(prefix, seed, root=ROOT)`, `find_pair(runs, seed, root=ROOT)`
  - `Anchor`, `VERDICT_LINES`, `CELLS`, `SHORT_VERDICT`, `GLOSS`, `MISSING_TEXT`, `NONE_TEXT`
  - `verdict(prefix, root=ROOT) -> {state, lines, missing, short, cells}`
- Code-over-design notes:
  - Names are checked with `RUNS_NAME.fullmatch(...)`. The skeleton's `^...$` regex followed by `.match` accepts a trailing newline (`"runs_c4\n"`).
  - `find_pair` rejects a non-int or bool seed with `KeyError`.
  - `verdict()` returns `short: None` only for a prefix that has anchors but no authored short line. That never happens in M1.

- [ ] **Step 1: Write the failing test**

All commands in Tasks 3, 5 and 6 run in Git Bash from the repo root, using the plan's environment block:

```bash
PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
```

Add these imports at the top of `app/test_agents.py`, beside Task 1's. Skip any line that is already there:

```python
import json
import os
import shutil
import tempfile
import threading

import fingerprint as FP
from app import agent_catalog as AC
```

Add these below `FULL = '--full' in sys.argv`:

```python
C4_SEEDS = range(8)
HAVE_C4 = all((ROOT / "runs_c4" / f"{arm}_seed{k}" / "final.zip").is_file()
              for arm in ("sighted", "blind") for k in C4_SEEDS)
NO_C4 = "runs_c4/ is not on this machine: the catalog path is UNPROVEN here"
```

Add this above `if __name__ == "__main__":`:

```python
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
                           ("runs_c4", 99), ("runs_c4", -1), ("runs_c4", "0"),
                           ("runs_c4", True)):
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
```

Every `.write(` above sits on a line containing `fh.write`, so `app/test_replay.py`'s `test_read_only` exempts it. Every fixture is written inside `tempfile.TemporaryDirectory()`, which is outside the repo.

- [ ] **Step 2: Run it to verify it fails**

Run: `$PY -m app.test_agents CatalogTests`
Expected: FAIL at import, with `ImportError: cannot import name 'agent_catalog' from 'app' (unknown location)`. The whole module stops at the import until Step 3.

- [ ] **Step 3: Implement** `app/agent_catalog.py`

```python
"""Which trained agents the replay page may run, and what results/ says of them.

READ-ONLY. This module opens meta.json, final.zip and files under results/
for reading and nothing else: no training, no evaluation, no file written, no
directory created. Names from a request are matched against two patterns
before any path is built from them, so a request can never choose a path.

The status of an agent is decided in the order of design section 4:
training, then no meta.json, then no final.zip, then evaluate.py's own arm
rule, then the protocol, then the fatal fingerprint fields. A pair runs only
when both arms are ready AND each final.zip is the one results/ recorded as
scored, where results/ records one (only C4 does today).

Verdicts are QUOTED, never computed: each anchor is a pattern searched in a
file under results/, returned with its line number so the page can cite it as
results/<file>:<line>. The short line and the glosses are authored text, and
the short line is shown only when every anchor it summarises was found.
M1 carries the C4 row only; the tables are keyed by result prefix so M2 adds
the d2 and phase_d rows without changing a signature.
"""
from __future__ import annotations

from collections import namedtuple
import os
from pathlib import Path
import re
import threading
import time

import fingerprint as FP
import run_phase_d as RPD
from analyse_c4 import BUDGET
from evaluate import DT, DURATION

ROOT = Path(__file__).resolve().parent.parent
RUNS_NAME = re.compile(r"^runs[A-Za-z0-9_]*$")
AGENT_NAME = re.compile(r"^(sighted|blind)_seed(\d+)$")
ARMS = ("sighted", "blind")


class Refused(Exception):
    """A pair that must not run. `problems` says why, one line per reason."""

    def __init__(self, problems):
        self.problems = [str(p) for p in problems]
        super().__init__("; ".join(self.problems))


_FINGERPRINTS = {}
FINGERPRINT_TAKEN = {}
_FINGERPRINT_LOCK = threading.Lock()


def live_fingerprint(protocol):
    """The live plant fingerprint for 'phase-d' or 'd2', taken once and cached.

    plant_fingerprint runs `git status`, which may rewrite .git/index unless
    GIT_OPTIONAL_LOCKS is 0, so that is set before the first call, here
    rather than in install(), so that tests calling this module directly are
    covered too. Restart the server after changing a hashed file.
    """
    os.environ.setdefault("GIT_OPTIONAL_LOCKS", "0")
    with _FINGERPRINT_LOCK:
        if protocol not in _FINGERPRINTS:
            _FINGERPRINTS[protocol] = FP.plant_fingerprint(
                protocol=protocol, eval_dt=DT, eval_duration=DURATION)
            FINGERPRINT_TAKEN[protocol] = time.strftime("%H:%M")
        return _FINGERPRINTS[protocol]


def protocol_of(meta):
    """'phase-d' when meta.scenario has no protocol, 'd2' for random-climb,
    None for anything else (refused as an unknown protocol)."""
    scenario = meta.get("scenario") or {}
    if "protocol" not in scenario:
        return "phase-d"
    if scenario["protocol"] == "random-climb":
        return "d2"
    return None


def read_agent(runs, name, root=ROOT):
    """One agent directory's status. KeyError if either name is malformed."""
    m = AGENT_NAME.fullmatch(str(name))
    if not RUNS_NAME.fullmatch(str(runs)) or m is None:
        raise KeyError(f"{runs}/{name}")
    arm, seed = m.group(1), int(m.group(2))
    d = Path(root) / runs / name
    out = {"runs": runs, "tag": name, "arm": arm, "seed": seed, "status": None,
           "reason": None, "problems": [], "protocol": None, "budget": None,
           "budget_line": None, "zip_sha": None, "train_dt": None}

    if FP.running_pid(str(d)) is not None:
        return dict(out, status="training", reason="training now")
    meta = FP.read(str(d / "meta.json"))
    if meta is None:
        return dict(out, status="incompatible",
                    reason="no meta.json: plant unknown (AUDIT2 C2-1)")
    if not (d / "final.zip").is_file():
        return dict(out, status="incomplete", reason="no final.zip")
    # evaluate.py:369 decides the arm by "blind" in the path string that
    # run_phase_d.py:330 hands it, f"{runs}/{name}". Apply that exact rule.
    scored_blind = "blind" in f"{runs}/{name}"
    if scored_blind != (arm == "blind") or scored_blind != (not meta.get("use_preview", True)):
        return dict(out, status="incompatible",
                    reason="evaluate.py would have scored this agent as the other arm")
    protocol = protocol_of(meta)
    if protocol is None:
        return dict(out, status="incompatible", reason="unknown protocol")
    bad = FP.compare(meta, live_fingerprint(protocol))
    if bad:
        return dict(out, status="incompatible", protocol=protocol,
                    reason="plant mismatch: " + ", ".join(f for f, _, _ in bad),
                    problems=[f"{f}: stored {a!r} live {b!r}" for f, a, b in bad])
    budget = FP.model_budget(str(d / "final.zip"))
    return dict(out, status="ready", protocol=protocol, budget=budget,
                budget_line=FP.format_budget(budget),
                zip_sha=budget["sha"] if budget else None,
                train_dt=meta.get("train_dt"))


def scored_shas(prefix, seed, root=ROOT):
    """The zip sha results/<prefix>_seed<seed>.txt recorded per arm, or None
    when there is no such file. evaluate.py wrote the model path with the
    platform separator (runs_c4\\sighted_seed0 on this machine), so the path
    is normalised to '/' before its last component is compared."""
    path = Path(root) / "results" / f"{prefix}_seed{seed}.txt"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    out = {arm: None for arm in ARMS}
    for line in lines:
        m = BUDGET.match(line)
        if m is None:
            continue
        base = m.group(1).replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
        for arm in ARMS:
            if base == f"{arm}_seed{seed}":
                out[arm] = m.group(6)
    return out


def find_pair(runs, seed, root=ROOT):
    """The sighted and blind agent of one seed, checked. KeyError for a name
    that is malformed or not on disk; Refused for a pair that must not run."""
    if (not RUNS_NAME.fullmatch(str(runs)) or not isinstance(seed, int)
            or isinstance(seed, bool) or seed < 0):
        raise KeyError(f"{runs}/{seed}")
    root = Path(root)
    if not all((root / runs / f"{arm}_seed{seed}").is_dir() for arm in ARMS):
        raise KeyError(f"{runs}/{seed}")
    agents = [read_agent(runs, f"{arm}_seed{seed}", root) for arm in ARMS]
    problems = []
    for a in agents:
        if a["status"] != "ready":
            problems.append(f"{a['tag']}: {a['status']} -- {a['reason']}")
            problems.extend(f"{a['tag']}: {p}" for p in a["problems"])
    if problems:
        raise Refused(problems)
    if agents[0]["protocol"] != agents[1]["protocol"]:
        raise Refused([f"the two arms were trained on different protocols: "
                       f"{agents[0]['protocol']} and {agents[1]['protocol']}"])
    prefix = RPD.result_prefix(str(root / runs))
    shas = scored_shas(prefix, seed, root)
    for a in agents:
        recorded = None if shas is None else shas[a["arm"]]
        if recorded is not None and recorded != a["zip_sha"]:
            problems.append(f"{a['tag']}: not the scored artefact -- results/{prefix}_seed{seed}.txt "
                            f"records zip sha {recorded}, final.zip is {a['zip_sha']}")
        a["scored"] = "match" if recorded is not None and recorded == a["zip_sha"] else "not recorded"
    if problems:
        raise Refused(problems)
    return {"runs": runs, "seed": seed, "prefix": prefix,
            "experiment": RPD.CLOSED_PREFIX.get(prefix) or f"{runs} (no name recorded)",
            "protocol": agents[0]["protocol"], "result_file": shas is not None,
            "agents": agents}


# ---- verdicts: quoted from results/, cited by line --------------------------
Anchor = namedtuple("Anchor", "key file pattern n")

VERDICT_LINES = {
    "c4": (
        Anchor("result", "C4_RESULT.txt", r"^\s*RESULT: SMALLER THAN THE MEI\s*$", 1),
        Anchor("seeds", "C4_RESULT.txt", r"\(7 of 8 seeds below 50\)", 1),
        Anchor("disagree", "C4_RESULT.txt", r"^\s*THE TWO TESTS DISAGREE", 2),
        Anchor("convergence", "C4_RESULT.txt", r"^\s*NOT-CONVERGED ", 1),
        Anchor("reading", "C4_RESULT.txt", r"^THE READING, as declared", 4),
        Anchor("explanations", "PREREGISTRATION_C4.md", r"^\| \(i\) \|", 3),
        Anchor("one_seed", "PREREGISTRATION_C4.md",
               r"^2\. \*\*It rests on the sign test's threshold", 3),
    ),
}

# The anchor key that carries each quoted cell, in display order.
CELLS = {"c4": {"result": "SMALLER THAN THE MEI", "convergence": "NOT-CONVERGED"}}

SHORT_VERDICT = {
    "c4": {
        "ar": "أصغر من الحد الأدنى المهم (50 وحدة) عند 300 000 خطوة · بفارق بذرة واحدة "
              "· الاختباران مختلفان · لم يستقر التدريب",
        "en": "smaller than the MEI (50) at 300 000 steps · one seed wide "
              "· the two tests disagree · not converged",
        "requires": ("result", "seeds", "disagree", "convergence"),
    },
}

GLOSS = {
    "SMALLER THAN THE MEI": {
        "ar": "أثر الاستباق أقل من 50 وحدة ضرر، وهو حدّ اختاره الفريق مسبقاً، عند 300 000 "
              "خطوة تدريب، على طريق فيه تغيّر واحد في الميل لكل حلقة. التدريب لم يستقر، "
              "والنتيجة معلّقة على بذرة واحدة: لو انقلبت بذرة واحدة لصارت غير حاسمة.",
        "en": "Preview's effect is below 50 damage units, a threshold the team set in advance, "
              "at 300 000 training steps, on a road with one grade change per episode. "
              "Training had not settled, and the result hangs on one seed: if one seed "
              "flipped, it would be inconclusive.",
    },
    "NOT-CONVERGED": {"ar": "لم يستقر التدريب", "en": "Training had not settled"},
}

MISSING_TEXT = {
    "ar": "لم يُعثر على سطر الحكم في results/{file}: لا تقرأ هؤلاء الوكلاء بدونه",
    "en": "verdict line not found in results/{file}: do not read these agents without it",
}
NONE_TEXT = {
    "ar": "لا يوجد حكم مسجَّل مسبقاً لهذه التجربة في results/. ما تعرضه هذه الصفحة ليس نتيجة.",
    "en": "No preregistered verdict for this experiment in results/. "
          "Nothing on this page is a result.",
}


def verdict(prefix, root=ROOT):
    """{state, lines, missing, short, cells} for one result prefix.

    state is 'found' when every anchor matched, 'missing' when a file or an
    anchor is gone, 'none' when the prefix has no row. Each line is
    {key, file, line (1-based), text (the n lines joined by newline)}.
    """
    anchors = VERDICT_LINES.get(prefix)
    if anchors is None:
        return {"state": "none", "lines": [], "missing": [], "short": dict(NONE_TEXT),
                "cells": []}
    texts, lines, missing = {}, [], []
    for a in anchors:
        if a.file not in texts:
            try:
                texts[a.file] = (Path(root) / "results" / a.file).read_text(
                    encoding="utf-8").splitlines()
            except OSError:
                texts[a.file] = None
        src = texts[a.file]
        rx = re.compile(a.pattern)
        hit = None if src is None else next(
            (i for i, line in enumerate(src) if rx.search(line)), None)
        if hit is None:
            missing.append(a.file)
            continue
        lines.append({"key": a.key, "file": a.file, "line": hit + 1,
                      "text": "\n".join(src[hit:hit + a.n])})
    missing = sorted(set(missing))
    found = {line["key"] for line in lines}
    authored = SHORT_VERDICT.get(prefix)
    if missing:
        short = {lang: MISSING_TEXT[lang].format(file=missing[0]) for lang in MISSING_TEXT}
    elif authored is not None and set(authored["requires"]) <= found:
        short = {lang: authored[lang] for lang in ("ar", "en")}
    else:
        short = None
    cells = [{"cell": cell, "gloss": dict(GLOSS[cell])}
             for key, cell in CELLS.get(prefix, {}).items() if key in found]
    return {"state": "missing" if missing else "found", "lines": lines,
            "missing": missing, "short": short, "cells": cells}
```

- [ ] **Step 4: Run to verify it passes**

Run: `$PY -m app.test_agents CatalogTests`

Expected, as observed while planning:
```
test_c4_pairs_are_the_scored_artefacts ... ok
test_c4_verdict ... ok
test_catalog_synthetic ... ok
test_live_fingerprint_is_cached ... ok
test_names_never_become_paths ... ok
test_protocol_of ... ok
test_scored_shas_real_files ... ok
Ran 7 tests in 0.2-0.3s
OK
```

The planning run also checked that the backslash test can fail. With `.replace("\\", "/")` removed from `scored_shas`, 10 checks fail: all 8 seeds, the synthetic test and the real-files test.

Then run the whole suite: `$PY -m app.test_agents 2>&1 | tail -3`. It includes Task 2's proof (about 2.5 min). Expected last line: `OK`. It may read `OK (skipped=N)`, depending on the skips Tasks 1-2 define.

- [ ] **Step 5: Commit**

```bash
git add app/agent_catalog.py app/test_agents.py
$PY verify_docs.py | tail -1
# expect: All 67 checks pass (... figure mentions scanned in the documents).
AGENTS_OUT="$($PY -m app.test_agents 2>&1 | tail -3)"; echo "$AGENTS_OUT"
REPLAY_OUT="$($PY -m app.test_replay 2>&1)"; echo "$REPLAY_OUT" | tail -1
# expect: 49 of 49 checks pass
git commit -F - <<EOF
Agent replay M1 (task 3): agent_catalog -- agent status, scored-artefact check, quoted C4 verdict

app/agent_catalog.py decides whether an agent under runs*/ may run, in the
design section 4 order: training, no meta.json, no final.zip, evaluate.py's own
arm rule on "{runs}/{name}", protocol, then fingerprint.compare on the fatal
fields. It never calls check_model_fingerprint.

A pair is refused when its final.zip is not the zip sha that
results/<prefix>_seed<k>.txt recorded as scored. The recorded model paths
carry Windows backslashes, and they are normalised before the basename is
compared.

The C4 verdict is quoted from results/ with its file:line, beside an authored
short line and glosses. The short line is shown only when every anchor it
summarises was found.

The module is read-only, and live_fingerprint sets GIT_OPTIONAL_LOCKS=0
before its first git call. All 8 runs_c4 pairs come back ready, with scored
'match' and 300000 steps.

\$ python -m app.test_agents
$AGENTS_OUT

\$ python -m app.test_replay
$REPLAY_OUT

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```


---

### Task 4: load_pair: the production loader, pinned to evaluate.py:370 (creates agent_api.py)

**Files:**
- Create: `app/agent_api.py`
- Modify: `app/test_agents.py`. Insert `LoaderTests` immediately above the `if __name__ == "__main__":` block, below every class already there, including Task 3's `CatalogTests`.
- Test: `app/test_agents.py` (`LoaderTests`)

**Interfaces:**
- Consumes:
  - `evaluate.py:370`: `SAC.load(path.rstrip('/\\') + '/final')`, with no device.
  - `evaluate.py:205` `agent_policy(model)`.
  - From Task 3: `agent_catalog.ROOT`, `RUNS_NAME`, `ARMS` (`('sighted', 'blind')`) and `scored_shas(prefix, seed, root=ROOT)`.
  - `fingerprint.py:342` `model_budget(zip_path)['sha']`.
  - `check_premise.py:103` `p_neutral`.
- Produces:
  - `app/agent_api.py`: `ROOT = agent_catalog.ROOT`.
  - `pair_paths(runs, seed)` → `(str(ROOT / runs / f'sighted_seed{seed}') + '/final', str(ROOT / runs / f'blind_seed{seed}') + '/final')`. It raises `KeyError` when `runs` fails `RUNS_NAME` or the seed is not a non-negative int. It uses `RUNS_NAME.fullmatch`, because `.match` with the pattern's `$` would accept `'runs_c4\n'`; the interface is unchanged.
  - `load_pair(runs, seed)` → `(m_s, m_b)`. It validates first, then runs `from stable_baselines3 import SAC` inside the function, then calls `SAC.load(path)` on each path, with no device argument.
  - `as_policy(m)` → `evaluate.agent_policy(m)` if `m` has `predict`, else `m` unchanged.
  - `versions()` → `{'torch': str | None, 'sb3': str | None}`, read from `sys.modules`; it never imports.
  - Task 5 adds the store to this file and Task 6 adds the routes and `install`.

- [ ] **Step 1: Write the failing test**

Insert the following in `app/test_agents.py` immediately above `if __name__ == "__main__":`, leaving two blank lines before that block:

```python
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
```

The imports are local to the methods, so this task does not touch the header import block that Task 3 may have edited.

- [ ] **Step 2: Run it to verify it fails**

Run: `$PY -m app.test_agents LoaderTests`
Expected (measured):
```
test_as_policy_and_versions (__main__.LoaderTests.test_as_policy_and_versions) ... ERROR
test_loader_matches_evaluate (__main__.LoaderTests.test_loader_matches_evaluate) ... ERROR
ERROR: test_as_policy_and_versions (__main__.LoaderTests.test_as_policy_and_versions)
ImportError: cannot import name 'agent_api' from 'app' (unknown location)
ERROR: test_loader_matches_evaluate (__main__.LoaderTests.test_loader_matches_evaluate)
ImportError: cannot import name 'agent_api' from 'app' (unknown location)
Ran 2 tests in 0.002s
FAILED (errors=2)
```

- [ ] **Step 3: Implement**

Create `app/agent_api.py` with exactly:

```python
"""The agent replay page's server side: the model loader, and later the store.

Imported only from the --simulation branch of app/server.py (install() is
added in a later task), so --live and --replay never load agent code, SB3 or
torch.

What this module never does: write to disk, train, evaluate, or call
evaluate.check_model_fingerprint (it raises SystemExit). stable-baselines3 and
torch are imported lazily inside load_pair, so importing this module costs
neither, and versions() only reads what is already loaded.
"""
from __future__ import annotations

import sys

from app import agent_catalog as C
from evaluate import agent_policy

ROOT = C.ROOT


def pair_paths(runs, seed):
    """(sighted, blind) model paths for one seed, spelled as evaluate.py:370 does.

    `runs` must be a runs directory NAME, never a path: anything failing
    agent_catalog.RUNS_NAME is a KeyError, and so is a seed that is not a
    non-negative int.
    """
    if not isinstance(runs, str) or not C.RUNS_NAME.fullmatch(runs):
        raise KeyError(f"unknown runs directory {runs!r}")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise KeyError(f"unknown seed {seed!r}")
    return tuple(str(ROOT / runs / f"{arm}_seed{seed}") + "/final" for arm in C.ARMS)


def load_pair(runs, seed):
    """(sighted, blind) SAC models, loaded exactly as evaluate.py:370 loads them.

    SAC.load(dir + "/final") with NO device argument: SB3's "auto", which is
    cuda on this machine. CPU and CUDA give different episodes (recon
    section 2), so the device is recorded and shown, never chosen here.
    """
    sighted, blind = pair_paths(runs, seed)
    from stable_baselines3 import SAC
    return SAC.load(sighted), SAC.load(blind)


def as_policy(m):
    """A policy(env, obs) callable: an SB3 model is wrapped as evaluate wraps it.

    A plain callable passes through unchanged: that is the proof's no-SB3 path,
    which runs check_premise's hand-written policies through the same store.
    """
    return agent_policy(m) if hasattr(m, "predict") else m


def versions():
    """torch and stable-baselines3 versions AS LOADED; never imports either."""
    return {"torch": getattr(sys.modules.get("torch"), "__version__", None),
            "sb3": getattr(sys.modules.get("stable_baselines3"), "__version__", None)}
```

- [ ] **Step 4: Run to verify it passes**

Run: `$PY -m app.test_agents LoaderTests`
Expected (measured, about 2 s warm):
```
test_as_policy_and_versions (__main__.LoaderTests.test_as_policy_and_versions) ... ok
test_loader_matches_evaluate (__main__.LoaderTests.test_loader_matches_evaluate) ... ok
----------------------------------------------------------------------
Ran 2 tests in 2.157s

OK

  load_pair: device cuda, torch 2.11.0+cu128, SB3 2.9.0
```
A negative check was run in the prototype: with `import torch` added inside `versions()`, `test_as_policy_and_versions` fails with `'versions': {'torch': '2.11.0+cu128', ...} != {'torch': None, ...}`. The subprocess check therefore does see a lazy-import regression.

Then run the whole suite: `$PY -m app.test_agents`
Expected: every class `ok` and `OK`. The output prints both the `load_pair: device cuda, ...` line and `== proof on cuda: sighted damage 501.56474787343603, blind damage 1229.059247261675`. Without Task 3's `CatalogTests` the prototype measured `Ran 10 tests in 230.044s`; with them the count is higher, so read it off the run.

- [ ] **Step 5: Commit**

```bash
git branch --show-current                     # JMF-2340550-sep17
git add app/agent_api.py app/test_agents.py
$PY verify_docs.py 2>&1 | tail -1             # All N checks pass (...); 67 before this milestone, read it off the run
$PY -m app.test_agents > "$SCRATCH/t4_agents.txt" 2>&1; tail -5 "$SCRATCH/t4_agents.txt"
$PY -m app.test_replay > "$SCRATCH/t4_replay.txt" 2>&1; tail -1 "$SCRATCH/t4_replay.txt"   # 49 of 49 checks pass; test_read_only now scans agent_api.py too
{
cat <<'EOF'
Agent replay T4: load_pair -- the production loader, pinned to evaluate.py:370

app/agent_api.py (first part): pair_paths(runs, seed) (a runs NAME, never a
path; KeyError otherwise), load_pair() = SAC.load(dir + "/final") with no
device, exactly evaluate.py:370, with SB3 imported lazily; as_policy() wraps a
model as evaluate.agent_policy does and passes a plain policy through;
versions() reads sys.modules and never imports. LoaderTests (spec 1b): same
device, torch.equal on every state_dict tensor, same model_budget sha, equal
to the sha results/c4_seed0.txt recorded as scored. Nothing is written.
EOF
echo
echo '$ python -m app.test_agents'
cat "$SCRATCH/t4_agents.txt"
echo
echo '$ python -m app.test_replay'
cat "$SCRATCH/t4_replay.txt"
echo
echo 'Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>'
} > "$SCRATCH/t4_msg.txt"
git commit -F "$SCRATCH/t4_msg.txt"
git log --oneline -1
```

Prototype evidence for this group. All of it ran from the scratchpad, with the prototype `app/` directory merged into the repo's `app` namespace package. The repository was untouched, and `git status --porcelain` was empty afterwards.
- Each red run failed with the message quoted above and each green run passed.
- `test_read_only`'s exact scan of the three new files came back clean, and `app.test_replay.test_read_only()` printed `PASS` on a copy of the tree holding them.
- `verify_docs.py` on a `git archive` copy with the files tracked printed `All 67 checks pass (782 figure mentions scanned in the documents).`
- `$PY -m app.test_replay` on the current tree printed `49 of 49 checks pass` in about 70 s.


---

### Task 5: EpisodeStore: one cancellable streaming worker, and the == proof run through it

**Files:**
- Modify: `app/agent_api.py`. Add imports at the top and append the store block below Task 4's `versions()`.
- Modify: `app/test_agents.py`:
  - add imports;
  - add helpers and `class StoreTests`;
  - **replace Task 2's `class ProofTests` block in full** with the store-driven class below. Keep any module-level flags Task 2 or Task 4 defined, because the new block defines its own under different names.
- Test: `app/test_agents.py` (`StoreTests`, `ProofTests`)

**Interfaces:**
- Consumes:
  - Task 2: `agent_trace.run_lanes(lanes, ep, on_frame)`. It calls `on_frame(frame, seen)` once per paired step; `seen[i]` is a float32 (23,) array or `None`. Also `agent_trace.STEPS`, `agent_trace.episode`, `route`, `build_cycle` and `DT`.
  - Task 3: `agent_catalog.find_pair(runs, seed)["protocol"]`, `Refused`.
  - Task 4: `load_pair`, `as_policy`, `versions` in `app/agent_api.py`.
  - `engine_env.OBS_DIM`.
  - `app/replay.py:255 BuildCancelled`.
  - `app/replay.py:259-322` (ReplayStore's busy, preempt and forget-error policy).
  - `evaluate.run_episode`, `agent_policy`, `EPISODES`, `EPISODES_D2`.
  - `check_premise.p_neutral` / `p_grade_now`.
- Produces (the skeleton's, verbatim):
  - `Trace(key, frames, results, obs, device, versions)`
  - `key_str(key) -> "runs_c4/5/1"`
  - `BUILD_FAILED = "build failed: {kind}"`
  - `default_episode_for(runs, seed, idx)`
  - `EpisodeStore(loader=load_pair, tracer=run_lanes, keep=2, episode_for=default_episode_for)` with `.needs_sb3`, `.poll(key, since=0, preempt=False)` and `.trace(key)`
- Code-over-design notes:
  - `Trace.device` is `"n/a"` when the loader returns plain policy callables (the no-SB3 proof path).
  - The two networks' devices are checked equal (design 3.1). A mismatch becomes `build failed: RuntimeError`.
  - The worker also checks the cancel event right after the loader returns, so a superseded build does not wait for its first frame.

- [ ] **Step 1: Write the failing test**

Add these imports at the top of `app/test_agents.py`, skipping any that are already present:

```python
import importlib.util
import time

import numpy as np

from app import agent_api as API
from check_premise import p_grade_now, p_neutral
from engine_env import ACT_HI, ACT_LO, OBS_DIM, PREVIEW_S, SLEW
from evaluate import EPISODES, EPISODES_D2, agent_policy, run_episode
```

Delete Task 2's `class ProofTests` and put the following above `if __name__ == "__main__":`:

```python
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
```

- [ ] **Step 2: Run it to verify it fails**

Run: `$PY -m app.test_agents StoreTests`
Expected: FAIL, with `AttributeError: module 'app.agent_api' has no attribute 'key_str'` / `... has no attribute 'EpisodeStore'` and `FAILED (errors=10)` (8 tests, 3 of them subtests of one). `ProofTests` errors the same way in `setUpClass`.

- [ ] **Step 3: Implement** the store in `app/agent_api.py`

Add these imports at the top, beside Task 4's (keep Task 4's own):

```python
from collections import OrderedDict
from dataclasses import dataclass
import threading

import numpy as np

from app import agent_catalog
from app import agent_trace
from app.replay import BuildCancelled
from engine_env import OBS_DIM
```

Append this below Task 4's `versions()`:

```python


# ---- the episode store: one worker, streaming, cancellable, bounded ---------
#
# Modelled on app.replay.ReplayStore (replay.py:259-322), which cannot stream
# partial frames. THE LOCK IS NEVER HELD DURING SLOW WORK: episode_for (a
# fingerprint and two zip hashes), the loader (torch import, SAC.load, CUDA
# start-up: about 5 s on the first build) and the tracer (about 75 s) all run
# outside it. Only publishing a frame, the device or the result takes it, so a
# poll always answers at once -- and the first answer after «احسب» is 'loading'.

BUILD_FAILED = "build failed: {kind}"


@dataclass
class Trace:
    """One finished pair: what the page plays, and what the policies saw."""
    key: tuple
    frames: list
    results: list
    obs: list
    device: str
    versions: dict


def key_str(key):
    """('runs_c4', 5, 1) -> 'runs_c4/5/1'."""
    runs, seed, idx = key
    return f"{runs}/{seed}/{idx}"


def default_episode_for(runs, seed, idx):
    """The frozen episode for this pair's protocol. find_pair runs again here,
    so the fatal fingerprint and the scored-artefact check are repeated
    immediately before the networks are loaded."""
    return agent_trace.episode(agent_catalog.find_pair(runs, seed)["protocol"], idx)


def _lane_obs(seen_rows, lane):
    rows = [row[lane] for row in seen_rows if row[lane] is not None]
    if not rows:
        return np.zeros((0, OBS_DIM), dtype=np.float32)
    return np.stack(rows).astype(np.float32, copy=False)


class EpisodeStore:
    """One daemon 'agent-builder' worker, one pair at a time, keep = 2 finished.

    Any other key gets 'busy'; only preempt=True cancels, and only the first
    request after «احسب» sends it. A cancelled or partial trace is never kept.
    Errors -- SystemExit included -- are reported once as a fixed message,
    never str(exc), then forgotten so the next poll can retry.
    """

    def __init__(self, loader=load_pair, tracer=agent_trace.run_lanes, keep=2,
                 episode_for=default_episode_for):
        self._loader, self._tracer = loader, tracer
        self._keep, self._episode_for = keep, episode_for
        self.needs_sb3 = loader is load_pair
        self._lock = threading.Lock()
        self._cache = OrderedDict()
        self._errors = {}
        self._active = None
        self._frames = []
        self._device = None
        self._versions = None
        self._cancel = threading.Event()

    def trace(self, key):
        """A finished Trace, or None (never a partial one)."""
        with self._lock:
            return self._cache.get(key)

    def poll(self, key, since=0, preempt=False):
        since = max(0, int(since))
        base = {"steps": agent_trace.STEPS, "since": since}
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                tr = self._cache[key]
                return dict(base, status="ready", progress=1.0, frames=tr.frames[since:],
                            device=tr.device, versions=tr.versions)
            if key in self._errors:
                return dict(base, status="error", progress=0.0, frames=[], device=None,
                            versions=None, message=self._errors.pop(key))
            if self._active == key:
                n = len(self._frames)
                return dict(base, status="building" if n else "loading",
                            progress=n / agent_trace.STEPS, frames=self._frames[since:],
                            device=self._device, versions=self._versions)
            if self._active is not None:
                if preempt:
                    self._cancel.set()
                runs, seed, idx = self._active
                return dict(base, status="busy", progress=0.0, frames=[], device=None,
                            versions=None, active={"runs": runs, "seed": seed, "ep": idx})
            self._cancel = threading.Event()
            self._active, self._frames = key, []
            self._device = self._versions = None
            threading.Thread(target=self._build, args=(key, self._cancel), daemon=True,
                             name="agent-builder").start()
            return dict(base, status="loading", progress=0.0, frames=[], device=None,
                        versions=None)

    def _build(self, key, cancel):
        runs, seed, idx = key
        frames, seen_rows = [], []

        def on_frame(frame, seen):
            if cancel.is_set():
                raise BuildCancelled(key_str(key))
            with self._lock:
                frames.append(frame)
                seen_rows.append(seen)
                self._frames = frames

        try:
            ep = self._episode_for(runs, seed, idx)
            m_s, m_b = self._loader(runs, seed)
            devices = {str(getattr(m, "device", "n/a")) for m in (m_s, m_b)}
            if len(devices) != 1:
                raise RuntimeError("the two networks loaded on different devices")
            device, vers = devices.pop(), versions()
            if cancel.is_set():
                raise BuildCancelled(key_str(key))
            with self._lock:
                self._device, self._versions = device, vers
            results = self._tracer([(as_policy(m_s), True), (as_policy(m_b), False)],
                                   ep, on_frame)
            trace = Trace(key, frames, results, [_lane_obs(seen_rows, 0), _lane_obs(seen_rows, 1)],
                          device, vers)
            with self._lock:
                self._cache[key] = trace
                while len(self._cache) > self._keep:
                    self._cache.popitem(last=False)
        except BuildCancelled:
            pass                     # superseded, not failed: nothing kept, nothing reported
        except (Exception, SystemExit) as exc:
            with self._lock:
                self._errors[key] = BUILD_FAILED.format(kind=type(exc).__name__)
        finally:
            with self._lock:
                self._active = None
```

- [ ] **Step 4: Run the store tests to verify they pass**

Run: `$PY -m app.test_agents StoreTests`
Expected: all 8 `... ok`, then `Ran 8 tests in 1.6s` and `OK`.

The planning run checked two regressions against these tests:
- Wrapping `self._loader(...)` in `with self._lock:` fails `test_loading_is_answered_while_the_loader_is_slow` with `1.00039... not less than 0.1 : poll blocked on the worker's lock`.
- Catching `Exception` alone fails the two `SystemExit` subtests.

- [ ] **Step 5: Run the proof through the store**

Run: `$PY -m app.test_agents ProofTests` (about 2.5 min)

Expected, as observed on this machine (build time 66-111 s depending on load):
```
test_frames_are_the_episode ... ok
test_phase_d_pair_full ... skipped '--full only: the Phase D pair, about 2.5 min'
test_tracer_equals_run_episode ...
    == proof PROVEN: device cuda, torch 2.11.0+cu128, sb3 2.9.0, sighted damage 501.56474787343603, blind 1229.059247261675, built in 66 s
ok
OK (skipped=1)
```

The planning run also exercised the fallback path, with `_C4_PAIR0_HERE` forced False. It printed `agent path UNPROVEN on this machine: ...` and `== proof agent path UNPROVEN on this machine: device n/a, torch None, sb3 None, sighted damage 2113.4858629443584, blind 907.0222264940807`, and passed.

If `==` ever fails, find the cause. Never add a tolerance; the fallback is sequential lanes in Task 2's `run_lanes`.

- [ ] **Step 6: Run the Phase D proof**

Run: `$PY -m app.test_agents ProofTests --full` (about 5 min)

Expected: the same lines, plus `    Phase D == proof PROVEN on cuda` and `Ran 3 tests ... OK`. The planning run took 360 s with other work running beside it. This check loads the models through the production `load_pair` and `default_episode_for` (`find_pair('runs', 0)` gives protocol phase-d).

- [ ] **Step 7: Commit**

```bash
git add app/agent_api.py app/test_agents.py
$PY verify_docs.py | tail -1
# expect: All 67 checks pass (...)
AGENTS_OUT="$($PY -m app.test_agents 2>&1)"; echo "$AGENTS_OUT" | tail -3
PROOF_LINE="$(echo "$AGENTS_OUT" | grep '== proof')"
REPLAY_OUT="$($PY -m app.test_replay 2>&1)"; echo "$REPLAY_OUT" | tail -1
# expect: 49 of 49 checks pass
git commit -F - <<EOF
Agent replay M1 (task 5): EpisodeStore -- one streaming, cancellable worker; the == proof runs through it

EpisodeStore follows ReplayStore's policy with one daemon 'agent-builder'
thread:
- any other key gets 'busy', and only preempt cancels;
- keep = 2, with the least recently used trace evicted first;
- a cancelled or partial trace is never kept;
- Exception and SystemExit are reported once as 'build failed: <Class>'.

The lock is never held during episode_for, the loader or the tracer. A poll
therefore answers in under 0.1 s while SAC loads, and the page sees
'loading' before its first frame.

The Trace keeps each lane's (n, 23) float32 observations for M3.

ProofTests now builds runs_c4/0/1 on the store's own worker thread. It
asserts == to evaluate.run_episode on both full result dicts, and --full
adds the Phase D pair through the production loader.

$PROOF_LINE

\$ python -m app.test_agents
$(echo "$AGENTS_OUT" | tail -3)

\$ python -m app.test_replay
$REPLAY_OUT

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```


---

### Task 6: Routes and install(): GET /agents and GET /api/agents/episode, registered only under --simulation

**Files:**
- Modify: `app/agent_api.py`. Add imports and append the routes block below the store.
- Modify: `app/server.py:298-302`, inside `if a.simulation:` in `main()`.
- Modify: `app/test_agents.py`:
  - add imports;
  - add `_StubStore` and `RouteTests`;
  - add the module-level `setUpModule` / `tearDownModule` snapshot;
  - add `NoWriteTests` and `NoNetworkTests`.
- Test: `app/test_agents.py`; `$PY -m app.test_replay`; `$PY -m app.test_simulation`

**Interfaces:**
- Consumes:
  - Task 5: `EpisodeStore(...).poll` / `.needs_sb3`, key `(runs, int, int)`.
  - Task 3: `find_pair`, `Refused`, `verdict`, `RUNS_NAME`, `FINGERPRINT_TAKEN`.
  - Tasks 1/2: `agent_trace.episode`, `build_cycle`, `route`, `jsonable`, `STEPS`, `DT`, `DURATION`.
  - `engine_env.py:513-515 ACT_LO/ACT_HI/SLEW`; `:953 neutral_action()`; `:490-491 TURB_PROTECT_K / OIL_PROTECT_K`; `:517 PREVIEW_S`.
  - `app/server.py:298`.
  - `app/test_replay.py:293 test_server_imports`.
- Produces (the skeleton's):
  - `sb3_available()`
  - `episode_meta(pair, ep, road, verdict)`, with exactly 19 keys: experiment, runs, prefix, protocol, seed, ep, episode, dt, duration_s, steps, train_dt, agents, result_file, preview_s, act, limits, scenario, verdict, fingerprint_taken
  - `install(app, store=None)`
  - `GET /agents`
  - `GET /api/agents/episode?runs&seed&ep&since&preempt`, returning 200, 404, 409 or 503, every one with `Cache-Control: no-store`. On 200 it carries `meta` and `road` only when `since` is 0.
- Code-over-design notes:
  - FastAPI answers a non-integer `int` or `bool` query parameter with its own 422, which carries no `no-store` header. So all five parameters are declared `str` and validated in the route. A malformed `runs`, `seed`, `ep` or `since` gets this route's 404 with `no-store`.
  - `preempt` is on for `1` or `true`.
  - Digits are matched as `[0-9]`, not `\d`, which would accept Arabic-Indic digits.
  - Device and versions travel as top-level fields of every poll, not inside `meta` (as the skeleton has it, against design 3.4's meta list).
  - `GET /agents` answers 500 until Task 9 creates `app/static/agents.html`, so nothing here requests it.

- [ ] **Step 1: Write the failing test**

Add these imports at the top of `app/test_agents.py`, skipping any that are already present:

```python
import ast
import re
import subprocess
from unittest import mock

from engine_env import TURB_PROTECT_K
```

Add this above `if __name__ == "__main__":`:

```python
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
```

The patterns above are raw regexes, so none of them matches `test_read_only`'s `\.write\s*\(`. The planning run checked the snapshot can fail by shifting `results/README.md`'s mtime between `setUpModule` and `tearDownModule`. It raised `the suite changed files on disk: results/README.md`, and the mtime was then restored.

- [ ] **Step 2: Run it to verify it fails**

Run: `$PY -m app.test_agents RouteTests NoWriteTests NoNetworkTests`

Expected, as observed:
```
ERROR: test_episode_route_contract ... AttributeError: module 'app.agent_api' has no attribute 'install'
ERROR: test_missing_sb3_is_503 ... AttributeError: module 'app.agent_api' has no attribute 'install'
ERROR: test_refused_pair_is_409_and_never_polled ... AttributeError: module 'app.agent_api' has no attribute 'install'
FAIL: test_routes_only_under_simulation ... AssertionError: 0 != 1 : install( must be called exactly once
FAILED (failures=1, errors=3)
```

`NoWriteTests` and `NoNetworkTests` already pass. They guard code that obeys them, and `test_the_scan_can_fail` proves their patterns fire.

- [ ] **Step 3: Implement** the routes in `app/agent_api.py`

Add these imports at the top, and extend Task 5's `from engine_env import OBS_DIM` into the second line below:

```python
import importlib.util
from pathlib import Path
import re

from engine_env import (ACT_HI, ACT_LO, OBS_DIM, OIL_PROTECT_K, PREVIEW_S, SLEW,
                        TURB_PROTECT_K, neutral_action)
```

Append this below `class EpisodeStore`:

```python


# ---- routes: added by install(app), and only under --simulation ------------
#
# app/server.py calls install(app) inside `if a.simulation:` in main(), so the
# --live and --replay processes never import this module. Every route here is
# a GET and answers with Cache-Control: no-store. A request names an episode
# by three strings that must match fixed patterns before anything is looked up;
# no path is ever built from a request.

NO_STORE = {"Cache-Control": "no-store"}
SEED_TEXT = re.compile(r"[0-9]{1,3}")
EP_TEXT = re.compile(r"[0-9]{1,2}")
SINCE_TEXT = re.compile(r"[0-9]{1,4}")
STATIC = Path(__file__).resolve().parent / "static"
_ROADS = {}


def sb3_available():
    """True when stable-baselines3 can be imported. Looked up, not imported."""
    return importlib.util.find_spec("stable_baselines3") is not None


def episode_meta(pair, ep, road, verdict):
    """Everything the page needs once per episode, JSON-safe. The device and
    the torch/SB3 versions are NOT here: they are known only after the worker
    has loaded the networks, so they travel in every poll response instead."""
    neutral_phys = ACT_LO + (neutral_action() + 1.0) * 0.5 * (ACT_HI - ACT_LO)
    agents = pair["agents"]
    return agent_trace.jsonable({
        "experiment": pair["experiment"],
        "runs": pair["runs"],
        "prefix": pair["prefix"],
        "protocol": pair["protocol"],
        "seed": pair["seed"],
        "ep": ep["idx"],
        "episode": {"seed": ep["seed"], "weights": list(ep["weights"]),
                    "climb_start_s": road["climb_start_s"],
                    "grade": None if ep["road"] is None else ep["road"][1]},
        "dt": agent_trace.DT,
        "duration_s": agent_trace.DURATION,
        "steps": agent_trace.STEPS,
        "train_dt": {a["arm"]: a["train_dt"] for a in agents},
        "agents": [{"tag": a["tag"], "arm": a["arm"], "budget_line": a["budget_line"],
                    "zip_sha": a["zip_sha"], "scored": a["scored"]} for a in agents],
        "result_file": pair["result_file"],
        "preview_s": list(PREVIEW_S),
        "act": {"lo": ACT_LO, "hi": ACT_HI, "slew": SLEW, "neutral_phys": neutral_phys},
        "limits": {"turb_c": round(TURB_PROTECT_K - 273.15, 1),
                   "oil_c": round(OIL_PROTECT_K - 273.15, 1)},
        "scenario": {"v_kmh": max(road["speed_kmh"]), "t_amb_c": road["t_amb_c"],
                     "p_baro_kpa": road["p_baro_kpa"]},
        "verdict": verdict,
        "fingerprint_taken": agent_catalog.FINGERPRINT_TAKEN.get(pair["protocol"]),
    })


def _road(ep):
    """The episode's road, from the cycle arrays only (no plant), cached."""
    key = (ep["protocol"], ep["idx"])
    if key not in _ROADS:
        _ROADS[key] = agent_trace.route(agent_trace.build_cycle(ep))
    return _ROADS[key]


def install(app, store=None):
    """Add GET /agents and GET /api/agents/episode to `app`."""
    from fastapi.responses import HTMLResponse, JSONResponse

    store = store if store is not None else EpisodeStore()
    app.state.agent_store = store

    def answer(body, status=200):
        return JSONResponse(body, status_code=status, headers=NO_STORE)

    @app.get("/agents", response_class=HTMLResponse)
    def agents_page():
        """The agent replay page. Read-only; computes nothing until «احسب»."""
        return HTMLResponse((STATIC / "agents.html").read_text(encoding="utf-8"),
                            headers=NO_STORE)

    @app.get("/api/agents/episode")
    def agents_episode(runs: str = "", seed: str = "", ep: str = "",
                       since: str = "0", preempt: str = ""):
        """Start or poll one episode of one pair. since=0 also carries meta and road.

        Every parameter is taken as text and checked here, so a malformed one
        gets this route's own 404 with no-store rather than FastAPI's 422.
        """
        unknown = answer({"detail": "unknown episode"}, 404)
        if (not agent_catalog.RUNS_NAME.fullmatch(runs) or not SEED_TEXT.fullmatch(seed)
                or not EP_TEXT.fullmatch(ep) or not 1 <= int(ep) <= 20
                or not SINCE_TEXT.fullmatch(since)):
            return unknown
        seed_n, idx, since_n = int(seed), int(ep), int(since)
        preempt_on = preempt in ("1", "true")
        try:
            pair = agent_catalog.find_pair(runs, seed_n)
            episode = agent_trace.episode(pair["protocol"], idx)
        except KeyError:
            return unknown
        except agent_catalog.Refused as refused:
            return answer({"status": "refused", "problems": refused.problems}, 409)
        if store.needs_sb3 and not sb3_available():
            return answer({"detail": "stable-baselines3 is not installed"}, 503)
        out = store.poll((runs, seed_n, idx), since=since_n, preempt=preempt_on)
        if since_n == 0:
            road = _road(episode)
            out["road"] = road
            out["meta"] = episode_meta(pair, episode, road, agent_catalog.verdict(pair["prefix"]))
        return answer(out)
```

- [ ] **Step 4: Edit `app/server.py:298-302`**

Use the Edit tool, which keeps the file's line endings. Replace this:

```python
    if a.simulation:
        print(f'  3D replay lab: http://localhost:{a.http_port}/simulation')
        print('  Local recordings only. No vehicle connection. In-memory replay cache.')
        import uvicorn
```

with this:

```python
    if a.simulation:
        print(f'  3D replay lab: http://localhost:{a.http_port}/simulation')
        print(f'  agent replay:  http://localhost:{a.http_port}/agents')
        print('  Local recordings only. No vehicle connection. In-memory replay cache.')
        from app.agent_api import install
        install(app)
        import uvicorn
```

Nothing else in `server.py` changes. The module-level routes stay as they are, and the docstring's "Every HTTP route below is a GET" (line 43) stays true.

- [ ] **Step 5: Run to verify it passes**

Run: `$PY -m app.test_agents RouteTests NoWriteTests NoNetworkTests`
Expected, as observed: seven `... ok` lines and `Ran 7 tests in 0.8s` / `OK`. The `StarletteDeprecationWarning` about httpx from `fastapi.testclient` is harmless.

Then run:
- `$PY -m app.test_agents 2>&1 | tail -3`. Expected: `OK (skipped=N)`. The `tearDownModule` snapshot passes, so nothing under `results/`, `app/`, `runs_c4/*_seed0` or `.git/index` changed, and `git status --porcelain` did not move. If it names only `.git/index`, an editor's background git touched it during the run. Rerun with the editor's git integration idle before suspecting the code.
- `$PY -m app.test_replay | tail -1`. Expected: `49 of 49 checks pass`, including `PASS  M7: app.server imports and serves its three pages   16 routes` and `PASS  READ-ONLY: no write path to the vehicle exists in app/`. `test_read_only` now also scans `agent_trace.py`, `agent_catalog.py`, `agent_api.py` and `test_agents.py`.
- `$PY -m app.test_simulation 2>&1 | tail -3`. Expected: `Ran 15 tests` / `OK`. It imports `app.server`, whose module level did not change.

- [ ] **Step 6: Commit**

```bash
git add app/agent_api.py app/server.py app/test_agents.py
$PY verify_docs.py | tail -1
# expect: All 67 checks pass (...)
AGENTS_OUT="$($PY -m app.test_agents 2>&1)"; echo "$AGENTS_OUT" | tail -3
SIM_OUT="$($PY -m app.test_simulation 2>&1 | tail -3)"; echo "$SIM_OUT"
REPLAY_OUT="$($PY -m app.test_replay 2>&1)"; echo "$REPLAY_OUT" | tail -1
# expect: 49 of 49 checks pass
git commit -F - <<EOF
Agent replay M1 (task 6): GET /agents and GET /api/agents/episode, installed only under --simulation

agent_api.install(app) registers two GET routes. Every response from them,
errors included, carries Cache-Control: no-store.

The episode route answers as follows:
- a runs/seed/ep/since that is unknown or malformed gets 404, and nothing
  reaches the store;
- a refused pair gets 409 with its problems, and no worker starts;
- a missing stable-baselines3 gets 503;
- otherwise it returns store.poll plus, when since is 0 only, meta (19
  JSON-safe keys, with the C4 verdict quoted) and the 720-vertex road.

All parameters are validated as text, because FastAPI's own 422 would carry
no no-store header.

app/server.py calls install() inside 'if a.simulation:' and nowhere else, so
--live and --replay never import agent code; an AST test pins it.

The module snapshot runs around the whole suite. It shows that nothing under
results/, app/ or runs_c4/*_seed0, nor .git/index or git status, changed.

\$ python -m app.test_agents
$(echo "$AGENTS_OUT" | grep '== proof')
$(echo "$AGENTS_OUT" | tail -3)

\$ python -m app.test_simulation
$SIM_OUT

\$ python -m app.test_replay
$REPLAY_OUT

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
```


---

### Task 7: Shared frontend parts: scene.mjs exports, the nav.agents key, and agents-strings.mjs

**Files:**
- Create: `app/static/sim/agents-strings.mjs`
- Create: `app/static/sim/agents-strings.test.mjs`
- Modify: `app/static/sim/scene.mjs:326,453,580` (adds the keyword `export` and nothing else)
- Modify: `app/static/sim/i18n.mjs:56,273` (one line inserted after each)
- Test: `app/static/sim/agents-strings.test.mjs`

**Interfaces:**
- Consumes:
  - `scene.mjs:326 function stage(host, { extent, position, target, shadows = true }) -> { scene, camera, renderer, render, paint, setTheme, theme, dispose }`
  - `scene.mjs:453 function ribbonGeometry(road, start, length, width, offset = 0, lift = 0.04, segments = 300)`
  - `scene.mjs:580 function supra(scene, paint) -> { car, wheels }`
  - `i18n.mjs:35 STRINGS`, `:486 t(lang, key, vars)`, `:500 missingKeys()`, `LANGS`
  - `i18n.mjs:56` / `:273 'nav.review'`
- Produces:
  - `scene.mjs`: `export function stage`, `export function ribbonGeometry` and `export function supra`. Behaviour does not change.
  - `i18n.mjs`: `'nav.agents'` is `'الوكلاء'` (ar) and `'Agents'` (en), placed directly after `'nav.review'` in both blocks.
  - `agents-strings.mjs`:
    - `export const AGENT_STRINGS = { ar, en }` holds exactly the 65 skeleton keys, all prefixed `agents.`: page.title, intro.heading, intro.note, badge, badge.short, pick.experiment, pick.pair, pick.episode, pick.none, pick.pair_option, pick.episode_option, pick.budget, compute, compute_aria, prompt, load.networks, load.building, load.busy, load.error, load.server_down, load.retry, load.refused, load.not_found, load.no_sb3, time.computed, time.waiting, dt.caption, dt.same, dt.not_recorded, pause.heading, pause.grade_now, pause.weights, action.spark, action.lambda, action.boost, action.fan, action.pump, action.tick_trim, action.tick_duty, action.held, action.map, car.sighted, car.blind, seen.item, seen.blind, damage.caption, turbine.label, torque.label, device.line, device.warning, fingerprint_taken, illustration, legend.same_place, scene.slope, scene.webgl_error, profile.ve, profile.rise, profile.climb, lane.stopped, verdict.heading, verdict.source, verdict.scored_match, verdict.not_recorded, verdict.no_result, footer.index.
    - The placeholders are exactly the skeleton's.
    - `export function mergeStrings(target, extra) -> number` (keys merged per language). It throws `Error` for an unknown language, a key missing from a language, or a collision. It validates everything before writing anything.
    - On import it runs `mergeStrings(STRINGS, AGENT_STRINGS)`.

Deviations from the design, one line each:
- The design writes the English prompt as "press احسب". The English string says "press Compute", which is the English label of the same button.
- The design's §8 says «احسب» pre-empts a busy build. The busy line therefore ends by telling the viewer so.
- `pick.none` wraps the example address in an LTR isolate (`\u2066…\u2069`) so it renders correctly inside an Arabic line.
- The `scene.mjs` check reads the file as text, so it needs neither WebGL nor Three.js.

Environment for every command in Tasks 7 and 8: Git Bash, cwd set to the repo root. A shell does not keep variables between steps, so set these again whenever the shell is new:

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
```

- [ ] **Step 1: Write the failing test**

Create `app/static/sim/agents-strings.test.mjs`:

```js
// The /agents strings, and the three things the page borrows from the lab.
// node --test runs every test file in its own process, so the merge this file
// triggers never reaches panel.test.mjs or any other lab test.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { STRINGS, LANGS, missingKeys, t } from './i18n.mjs';

// Taken BEFORE agents-strings.mjs is imported: the lab's strings as the lab ships them.
const before = structuredClone(STRINGS);
let mod = null;
let loadError = null;
try { mod = await import('./agents-strings.mjs'); } catch (err) { loadError = err; }
const api = () => {
  assert.ok(mod, `agents-strings.mjs must load: ${loadError?.message}`);
  return mod;
};

test('scene.mjs lends stage, ribbonGeometry and supra, and only adds the keyword', () => {
  // Design section 2, edit 2 (approved, section 11 Q2). Read as text so this
  // test needs no WebGL and no Three.js install.
  const src = readFileSync(new URL('./scene.mjs', import.meta.url), 'utf8');
  for (const name of ['stage', 'ribbonGeometry', 'supra']) {
    assert.match(src, new RegExp(`^export function ${name}\\(`, 'm'), `${name} is not exported`);
    assert.doesNotMatch(src, new RegExp(`^function ${name}\\(`, 'm'), `${name} is declared twice`);
  }
});

test('i18n.mjs carries nav.agents in both languages, right after nav.review', () => {
  assert.equal(before.ar['nav.agents'], 'الوكلاء');
  assert.equal(before.en['nav.agents'], 'Agents');
  for (const lang of LANGS) {
    const keys = Object.keys(before[lang]);
    assert.equal(keys.indexOf('nav.agents'), keys.indexOf('nav.review') + 1, `${lang}: nav.agents is not after nav.review`);
  }
});

test('the merge adds this page\'s strings and leaves every lab string as it was', () => {
  const { AGENT_STRINGS } = api();
  assert.deepEqual(Object.keys(AGENT_STRINGS).sort(), [...LANGS].sort());
  for (const lang of LANGS) {
    for (const [key, text] of Object.entries(before[lang])) assert.equal(STRINGS[lang][key], text, `${lang} ${key} changed`);
    for (const key of Object.keys(AGENT_STRINGS[lang])) {
      assert.ok(key.startsWith('agents.'), `${key} is not namespaced agents.`);
      assert.ok(!Object.prototype.hasOwnProperty.call(before[lang], key), `${key} already existed in the lab's ${lang}`);
      assert.equal(STRINGS[lang][key], AGENT_STRINGS[lang][key]);
    }
    assert.equal(Object.keys(STRINGS[lang]).length,
      Object.keys(before[lang]).length + Object.keys(AGENT_STRINGS[lang]).length);
  }
  assert.deepEqual(missingKeys(), []);
});

test('mergeStrings refuses a collision, a one-language key and an unknown language, and changes nothing', () => {
  const { mergeStrings } = api();
  const target = { ar: { a: 'أ' }, en: { a: 'A' } };
  const copy = structuredClone(target);
  assert.throws(() => mergeStrings(target, { ar: { a: 'ب', b: 'ب' }, en: { a: 'B', b: 'B' } }), /collides/);
  assert.deepEqual(target, copy);
  assert.throws(() => mergeStrings(target, { ar: { b: 'ب', c: 'ج' }, en: { b: 'B' } }), /missing from en/);
  assert.deepEqual(target, copy);
  assert.throws(() => mergeStrings(target, { ar: { b: 'ب' } }), /missing from en/);
  assert.throws(() => mergeStrings(target, { ar: { b: 'ب' }, en: { b: 'B' }, fr: { b: 'B' } }), /unknown language/);
  assert.deepEqual(target, copy);
  assert.equal(mergeStrings(target, { ar: { b: 'ب' }, en: { b: 'B' } }), 1);
  assert.deepEqual(target, { ar: { a: 'أ', b: 'ب' }, en: { a: 'A', b: 'B' } });
});

test('the honesty captions survive in both languages', () => {
  api();
  const mustSay = {
    'agents.badge': {
      ar: [/محاكاة/, /اصطناعي/, /أقسى من أي تسلّق مسجّل/, /لا يعني ذلك أنه أحرّ من كل لحظة/],
      en: [/simulation/i, /synthetic/, /harsher than any recorded climb/, /does not mean it is hotter than every moment/],
    },
    'agents.illustration': {
      ar: [/مثال توضيحي، لا نتيجة/, /وسيطات عبر 20 حلقة/, /لا يُحسب هنا أي فرق بين السيارتين/],
      en: [/illustration, not a result/, /medians over 20 episodes/, /no difference between the cars is computed/],
    },
    'agents.scene.slope': { ar: [/الميل غير مضخّم/, /ليست بمقياسها/], en: [/not exaggerated/, /not to scale/] },
    'agents.action.boost': { ar: [/سقف/], en: [/ceiling/] },
    'agents.action.map': { ar: [/السقف نفسه/, /لا يُعرض/], en: [/ceiling itself/, /not shown/] },
    'agents.action.tick_duty': { ar: [/المنمذَج/, /0 أو 0\.4 أو 1\.0/], en: [/modelled/, /0, 0\.4 or 1\.0/] },
    'agents.action.held': { ar: [/حد سرعة التغيير/], en: [/rate limit/] },
    'agents.dt.caption': { ar: [/لم تُحلّ/, /H2-2/], en: [/unresolved/, /H2-2/] },
    'agents.damage.caption': { ar: [/في هذه الحلقة فقط/], en: [/in this episode only/] },
    'agents.legend.same_place': { ar: [/في المكان نفسه/], en: [/same place/] },
    'agents.device.line': { ar: [/لا تسجّل الجهاز/], en: [/do not record the device/] },
  };
  for (const [key, langs] of Object.entries(mustSay)) {
    for (const [lang, patterns] of Object.entries(langs)) {
      assert.ok(STRINGS[lang][key], `${key} missing in ${lang}`);
      for (const p of patterns) assert.match(STRINGS[lang][key], p, `${key} lost its caveat in ${lang}`);
    }
  }
  assert.match(t('ar', 'agents.profile.ve', { ve: 3 }), /×3/);
  assert.match(t('en', 'agents.profile.ve', { ve: 3 }), /×3/);
  assert.equal(STRINGS.ar['agents.footer.index'], '02 — AGENTS');
  assert.equal(STRINGS.en['agents.footer.index'], '02 — AGENTS');
});

test('no string says preview helps, and the engine computer is always the modelled one', () => {
  const { AGENT_STRINGS } = api();
  for (const lang of LANGS) {
    for (const [key, text] of Object.entries(AGENT_STRINGS[lang])) {
      assert.doesNotMatch(text, /preview helps/i, `${lang} ${key}`);
      assert.ok(!text.includes('يساعد الاستباق') && !text.includes('الاستباق يساعد'), `${lang} ${key}`);
      if (text.includes('حاسوب المحرك')) assert.ok(text.includes('المنمذَج'), `${key} names the engine computer without «المنمذَج»`);
    }
  }
});

test('every key fills the same {placeholders} in both languages', () => {
  const { AGENT_STRINGS } = api();
  const slots = text => [...text.matchAll(/\{(\w+)\}/g)].map(m => m[1]).sort();
  for (const key of Object.keys(AGENT_STRINGS.ar)) {
    assert.deepEqual(slots(AGENT_STRINGS.ar[key]), slots(AGENT_STRINGS.en[key]), key);
  }
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `node --test app/static/sim/agents-strings.test.mjs 2>&1 | grep -E "^(✔|✖)|^ℹ (tests|pass|fail)|AssertionError" | head -20`

Expected: FAIL. `ℹ tests 7`, `ℹ pass 0`, `ℹ fail 7`, with these errors:
- `AssertionError [ERR_ASSERTION]: stage is not exported`
- `AssertionError [ERR_ASSERTION]: Expected values to be strictly equal:` (nav.agents)
- five times `AssertionError [ERR_ASSERTION]: agents-strings.mjs must load: Cannot find module '...\app\static\sim\agents-strings.mjs' imported from ...\agents-strings.test.mjs`

- [ ] **Step 3: Lend the lab's parts (three keywords, two lines)**

In `app/static/sim/scene.mjs`, make three one-line replacements with Edit. Nothing else in the file changes.

```
:326  function stage(host, { extent, position, target, shadows = true }) {
  ->  export function stage(host, { extent, position, target, shadows = true }) {
:453  function ribbonGeometry(road, start, length, width, offset = 0, lift = 0.04, segments = 300) {
  ->  export function ribbonGeometry(road, start, length, width, offset = 0, lift = 0.04, segments = 300) {
:580  function supra(scene, paint) {
  ->  export function supra(scene, paint) {
```

In `app/static/sim/i18n.mjs`, insert one line after each `nav.review` line:

```js
// after line 56:   'nav.review': 'مراجعة التنبيهات',
    'nav.agents': 'الوكلاء',
// after line 273:  'nav.review': 'Alert review',
    'nav.agents': 'Agents',
```

(The exact old strings for Edit are `    'nav.review': 'مراجعة التنبيهات',` and `    'nav.review': 'Alert review',`. The new strings are those same lines followed by the `nav.agents` line at the same four-space indent.)

Run: `node --test app/static/sim/agents-strings.test.mjs 2>&1 | grep -E "^(✔|✖)|^ℹ (tests|pass|fail)" | head -10`

Expected: the first two tests pass (`✔ scene.mjs lends…` and `✔ i18n.mjs carries nav.agents…`). The other five still fail with `agents-strings.mjs must load`: `ℹ pass 2`, `ℹ fail 5`.

Run: `git diff --numstat -- app/static/sim/scene.mjs app/static/sim/i18n.mjs`

Expected:
```
2	0	app/static/sim/i18n.mjs
3	3	app/static/sim/scene.mjs
```

- [ ] **Step 4: Implement agents-strings.mjs**

Create `app/static/sim/agents-strings.mjs`:

```js
// Every string the /agents page shows, in Arabic and English.
//
// The lab's i18n.mjs owns t(), applyTranslations() and STRINGS; this file only
// ADDS to STRINGS, once, at import, and refuses to overwrite anything. The lab
// page never imports this file, so /simulation's strings are exactly what they
// were. The same three rules as i18n.mjs apply (read its header): both
// languages carry the same keys, numbers go through {placeholders}, and the
// honesty captions are load-bearing text, not copy.
//
// Two rules of this page, pinned by agents-strings.test.mjs:
//  - The engine computer is always «حاسوب المحرك المنمذَج», the MODELLED one.
//  - No string says preview helps. This page shows one episode; the verdict
//    box quotes what the experiment found, word for word from results/.
//
// Arabic lines are from design sections 5 and 6
// (docs/superpowers/specs/2026-09-26-agent-replay-design.md), verbatim where the
// design gives them. \u200f is a right-to-left mark and \u2066...\u2069 isolates a
// left-to-right run (an address) inside an Arabic line.

import { STRINGS } from './i18n.mjs';

export const AGENT_STRINGS = {
  ar: {
    // --- document, intro and badge
    'agents.page.title': 'الوكلاء — GRAD',
    'agents.intro.heading': 'ماذا قرّر كل وكيل، ثانيةً بثانية',
    'agents.intro.note': 'حلقة اختبار واحدة تُحسب الآن من الشبكتين المدرَّبتين، على الطريق المحاكى نفسه للسيارتين.',
    'agents.badge': 'محاكاة: سيناريو إجهاد اصطناعي — تسلّق متواصل {grade}٪ عند {v} كم/س في {t} °م، أقسى من أي تسلّق مسجّل؛ لا يعني ذلك أنه أحرّ من كل لحظة في الرحلات المسجّلة',
    'agents.badge.short': 'محاكاة',

    // --- picker (read-only in M1)
    'agents.pick.experiment': 'التجربة',
    'agents.pick.pair': 'الزوج',
    'agents.pick.episode': 'الحلقة',
    'agents.pick.none': 'لم يُحدَّد زوج ولا حلقة. افتح الصفحة بعنوان مثل \u2066?runs=runs_c4&seed=5&ep=1\u2069',
    'agents.pick.pair_option': 'بذرة {seed} · المُبصر والأعمى',
    'agents.pick.episode_option': 'حلقة {idx} · الصعود عند {start} ث · {grade}٪ · الأوزان: عزم {w0} / وقود {w1} / عمر المكوّنات {w2}',
    'agents.pick.budget': 'دُرِّب {budget} خطوة (من final.zip)',
    'agents.compute': 'احسب',
    'agents.compute_aria': 'احسب هذه الحلقة للوكيلين الآن',
    'agents.prompt': 'اختر تجربة وزوجاً وحلقة ثم اضغط احسب',

    // --- loading and errors
    'agents.load.networks': 'تحميل الشبكتين…',
    'agents.load.building': 'تُحسب الحلقة… {percent}٪',
    'agents.load.busy': 'تُحسب حلقة أخرى الآن ({runs} بذرة {seed} حلقة {ep}) — اضغط احسب لإيقافها وبدء هذه',
    'agents.load.error': 'تعذّر الحساب: {message}',
    'agents.load.server_down': 'الخادم غير متاح',
    'agents.load.retry': 'أعد المحاولة',
    'agents.load.refused': 'رُفض تشغيل هذا الزوج، ولم يُحمَّل أي نموذج:',
    'agents.load.not_found': 'لا توجد تجربة أو زوج أو حلقة بهذا الاسم',
    'agents.load.no_sb3': 'لا يمكن التشغيل: مكتبة stable-baselines3 غير مثبّتة',

    // --- timeline
    'agents.time.computed': 'حُسب حتى {done} · تنتهي الحلقة عند {end}',
    'agents.time.waiting': 'ينتظر الحساب…',
    'agents.dt.caption': 'تُعاد هنا بخطوة 1.0 ث، الخطوة التي قُيِّم بها الوكيلان؛ دُرِّبا بخطوة {train_dt} ث. مشكلة معروفة لم تُحلّ (AUDIT2.md H2-2)؛ لم يُقَس هل تؤثر في الوكيلين بالقدر نفسه',
    'agents.dt.same': 'تُعاد هنا بخطوة 1.0 ث، الخطوة التي قُيِّم بها الوكيلان ودُرِّبا بها',
    'agents.dt.not_recorded': 'تُعاد هنا بخطوة 1.0 ث، الخطوة التي قُيِّم بها الوكيلان؛ خطوة التدريب غير مسجّلة',

    // --- pause panel
    'agents.pause.heading': 'القرار المطبَّق من الثانية {k} إلى {k1}',
    'agents.pause.grade_now': 'ميل الطريق الآن {grade}٪',
    'agents.pause.weights': 'ما طُلب من الوكيلين في هذه الحلقة: عزم {w0} · وقود {w1} · عمر المكوّنات {w2}',
    'agents.action.spark': 'تعديل توقيت الشرارة',
    'agents.action.lambda': 'تعديل خليط الوقود (لامدا)',
    'agents.action.boost': 'إزاحة سقف ضغط الشحن',
    'agents.action.fan': 'مروحة التبريد',
    'agents.action.pump': 'مضخة سائل التبريد',
    'agents.action.tick_trim': 'بلا تعديل',
    'agents.action.tick_duty': 'قيمة صف "حاسوب المحرك الأساسي" في النتائج (1.0 ثابتة)؛ الحاسوب المنمذَج نفسه يجدول المروحة 0 أو 0.4 أو 1.0 حسب حرارة سائل التبريد',
    'agents.action.held': 'أمر به {x}؛ قيّده حد سرعة التغيير',
    'agents.action.map': 'ضغط المشعب الآن {map} كيلوباسكال؛ السقف نفسه يُحسب داخل الحلقة ولا يُعرض',
    'agents.car.sighted': 'يرى الطريق أمامه',
    'agents.car.blind': 'لا يرى الطريق أمامه',
    'agents.seen.item': 'بعد {h} ث: {pct}٪',
    'agents.seen.blind': 'لا يرى الطريق أمامه: مداخل الاستباق عنده {zeros}',
    'agents.damage.caption': 'وحدات ضرر، في هذه الحلقة فقط حتى هذه اللحظة',
    'agents.turbine.label': 'حرارة غلاف التيربو مقابل عتبة الحماية',
    'agents.torque.label': 'العزم المُسلَّم {delivered} من {requested} نيوتن·م مطلوبة',
    'agents.device.line': 'التقييم المسجَّل حمّل الشبكة على الجهاز الافتراضي لـ SB3، وهو cuda على هذا الجهاز؛ ملفات النتائج لا تسجّل الجهاز. هذه الحلقة حُسبت على {device} \u200f(torch {torch}، SB3 {sb3})',
    'agents.device.warning': 'تنبيه: هذه الحلقة لم تُحسب على cuda، وحلقات المعالج تختلف عن حلقات cuda، فقد لا تطابق ما قُيِّم',
    'agents.fingerprint_taken': 'أُخذت بصمة المحاكي عند {time}؛ أعد تشغيل الخادم بعد تغيير أي ملف تدخل فيه البصمة',

    // --- scene and profile
    'agents.illustration': 'حلقة واحدة لزوج واحد مثال توضيحي، لا نتيجة. النتائج وسيطات عبر 20 حلقة، ولا يُحسب هنا أي فرق بين السيارتين',
    'agents.legend.same_place': 'السيارتان في المكان نفسه دائماً: السرعة يفرضها السيناريو، والوكيلان يختاران الحماية فقط',
    'agents.scene.slope': 'الميل غير مضخّم · السيارة ليست بمقياسها',
    'agents.scene.webgl_error': 'تعذّر عرض المشهد ثلاثي الأبعاد في هذا المتصفح. المقطع الجانبي ولوحة القرار يعملان.',
    'agents.profile.ve': 'المقياس الرأسي مضخّم ×{ve}',
    'agents.profile.rise': 'يرتفع الطريق {rise} م بينما يبقى الضغط {p} كيلوباسكال والحرارة {t} °م ثابتين طوال الحلقة',
    'agents.profile.climb': 'يبدأ الصعود عند {start} ث · {grade}٪',
    'agents.lane.stopped': 'توقفت محاكاة هذه السيارة عند الخطوة {k}',

    // --- verdict box
    'agents.verdict.heading': 'الحكم المسجَّل مسبقاً',
    'agents.verdict.source': 'results/{file}:{line}',
    'agents.verdict.scored_match': 'هذا هو الملف الذي قُيِّم: بصمة final.zip تطابق ما سجّلته النتائج',
    'agents.verdict.not_recorded': 'الملف المقيَّم غير مسجَّل في النتائج',
    'agents.verdict.no_result': 'لا ملف نتيجة لهذا الزوج',

    // --- footer (M3 attaches the hidden gesture here; nothing in M1)
    'agents.footer.index': '02 — AGENTS',
  },

  en: {
    // --- document, intro and badge
    'agents.page.title': 'Agents — GRAD',
    'agents.intro.heading': 'What each agent decided, second by second',
    'agents.intro.note': 'One test episode, computed now from the two trained networks, on the same simulated road for both cars.',
    'agents.badge': 'Simulation: a synthetic stress scenario, a sustained {grade} % climb at {v} km/h in {t} °C, harsher than any recorded climb; this does not mean it is hotter than every moment of the recorded drives',
    'agents.badge.short': 'Simulation',

    // --- picker (read-only in M1)
    'agents.pick.experiment': 'Experiment',
    'agents.pick.pair': 'Pair',
    'agents.pick.episode': 'Episode',
    'agents.pick.none': 'No pair or episode is selected. Open the page with an address such as ?runs=runs_c4&seed=5&ep=1',
    'agents.pick.pair_option': 'Seed {seed} · sighted and blind',
    'agents.pick.episode_option': 'Episode {idx} · climb at {start} s · {grade} % · weights: torque {w0} / fuel {w1} / component life {w2}',
    'agents.pick.budget': 'trained {budget} steps (from final.zip)',
    'agents.compute': 'Compute',
    'agents.compute_aria': 'Compute this episode for both agents now',
    'agents.prompt': 'Choose an experiment, a pair and an episode, then press Compute',

    // --- loading and errors
    'agents.load.networks': 'Loading the two networks…',
    'agents.load.building': 'Computing the episode… {percent} %',
    'agents.load.busy': 'Another episode is being computed now ({runs} seed {seed} episode {ep}) — press Compute to stop it and start this one',
    'agents.load.error': 'The computation failed: {message}',
    'agents.load.server_down': 'Server not reachable',
    'agents.load.retry': 'Retry',
    'agents.load.refused': 'This pair was refused and no model was loaded:',
    'agents.load.not_found': 'No experiment, pair or episode by that name',
    'agents.load.no_sb3': 'Cannot run: stable-baselines3 is not installed',

    // --- timeline
    'agents.time.computed': 'Computed up to {done} · the episode ends at {end}',
    'agents.time.waiting': 'Waiting for the computation…',
    'agents.dt.caption': 'Replayed here at a 1.0 s step, the step the agents were scored at; they were trained at {train_dt} s. A known, unresolved problem (AUDIT2.md H2-2); whether it affects both agents equally has not been measured',
    'agents.dt.same': 'Replayed here at a 1.0 s step, the step the agents were scored and trained at',
    'agents.dt.not_recorded': 'Replayed here at a 1.0 s step, the step the agents were scored at; the training step is not recorded',

    // --- pause panel
    'agents.pause.heading': 'The decision applied from second {k} to {k1}',
    'agents.pause.grade_now': 'Grade now {grade} %',
    'agents.pause.weights': 'What the agents were asked to weigh in this episode: torque {w0} · fuel {w1} · component life {w2}',
    'agents.action.spark': 'Spark timing trim',
    'agents.action.lambda': 'Fuel mixture trim (lambda)',
    'agents.action.boost': 'Boost-pressure ceiling offset',
    'agents.action.fan': 'Cooling fan',
    'agents.action.pump': 'Coolant pump',
    'agents.action.tick_trim': 'No change',
    'agents.action.tick_duty': "The value used by the results' 'baseline ECU' row (a constant 1.0); the modelled computer itself schedules the fan at 0, 0.4 or 1.0 by coolant temperature",
    'agents.action.held': 'Commanded {x}; held back by the rate limit',
    'agents.action.map': 'Manifold pressure now {map} kPa; the ceiling itself is computed inside the loop and is not shown',
    'agents.car.sighted': 'Sees the road ahead',
    'agents.car.blind': 'Does not see the road ahead',
    'agents.seen.item': 'In {h} s: {pct} %',
    'agents.seen.blind': 'Does not see the road ahead: its preview inputs were {zeros}',
    'agents.damage.caption': 'Damage units, in this episode only, up to this moment',
    'agents.turbine.label': 'Turbine housing temperature against the protection limit',
    'agents.torque.label': 'Torque delivered {delivered} of {requested} N·m requested',
    'agents.device.line': "The recorded evaluation loaded the network on SB3's default device, which is cuda on this machine; the result files do not record the device. This episode was computed on {device} (torch {torch}, SB3 {sb3})",
    'agents.device.warning': 'Warning: this episode was not computed on cuda, and CPU episodes differ from CUDA ones, so it may not match what was scored',
    'agents.fingerprint_taken': 'Plant fingerprint taken at {time}; restart the server after changing a hashed file',

    // --- scene and profile
    'agents.illustration': 'One episode of one pair is an illustration, not a result. The results are medians over 20 episodes, and no difference between the cars is computed here',
    'agents.legend.same_place': 'Both cars are always at the same place: the scenario sets the speed, and the agents choose only the protection',
    'agents.scene.slope': 'Slope not exaggerated · car not to scale',
    'agents.scene.webgl_error': 'The 3D view could not be shown in this browser. The side profile and the decision panel still work.',
    'agents.profile.ve': 'Vertical scale exaggerated ×{ve}',
    'agents.profile.rise': 'The road rises {rise} m while pressure stays at {p} kPa and temperature at {t} °C throughout the episode',
    'agents.profile.climb': 'Climb starts at {start} s · {grade} %',
    'agents.lane.stopped': "This car's simulation stopped at step {k}",

    // --- verdict box
    'agents.verdict.heading': 'The preregistered verdict',
    'agents.verdict.source': 'results/{file}:{line}',
    'agents.verdict.scored_match': 'This is the scored artefact: the final.zip sha matches the one the results recorded',
    'agents.verdict.not_recorded': 'Scored artefact not recorded in results',
    'agents.verdict.no_result': 'No result file for this pair',

    // --- footer (M3 attaches the hidden gesture here; nothing in M1)
    'agents.footer.index': '02 — AGENTS',
  },
};

/**
 * Add `extra` ({lang: {key: text}}) into `target` (i18n's STRINGS) and return
 * how many keys each language gained. Everything is checked BEFORE anything is
 * written, so a refused merge leaves `target` exactly as it was. It throws on:
 *  - a language `target` does not have;
 *  - a key present in one language of `extra` and missing from another (or a
 *    language of `target` that `extra` leaves out);
 *  - a key `target` already has: this page may add strings, never change the
 *    lab's.
 */
export function mergeStrings(target, extra) {
  const langs = Object.keys(target);
  for (const lang of Object.keys(extra)) {
    if (!langs.includes(lang)) throw new Error(`agents strings: unknown language "${lang}"`);
  }
  const keys = new Set(Object.values(extra).flatMap(table => Object.keys(table)));
  for (const lang of langs) {
    const table = extra[lang] ?? {};
    for (const key of keys) {
      if (!Object.prototype.hasOwnProperty.call(table, key)) {
        const has = Object.keys(extra).filter(l => Object.prototype.hasOwnProperty.call(extra[l], key));
        throw new Error(`agents strings: "${key}" is missing from ${lang} (present in ${has.join(', ')})`);
      }
      if (Object.prototype.hasOwnProperty.call(target[lang], key)) {
        throw new Error(`agents strings: "${key}" collides with an existing ${lang} string`);
      }
    }
  }
  for (const lang of langs) Object.assign(target[lang], extra[lang]);
  return keys.size;
}

mergeStrings(STRINGS, AGENT_STRINGS);
```

- [ ] **Step 5: Run to verify it passes, and that the lab is unchanged**

Run: `node --test app/static/sim/agents-strings.test.mjs 2>&1 | grep -E "^(✔|✖)|^ℹ (tests|pass|fail)"`

Expected: all seven `✔`, then `ℹ tests 7`, `ℹ pass 7`, `ℹ fail 0`.

Run: `node --test "app/static/sim/*.test.mjs" 2>&1 | grep -E "^ℹ (tests|pass|fail|skipped)"`

Expected: `ℹ tests 37`, `ℹ pass 37`, `ℹ fail 0`, `ℹ skipped 0`. That is the lab's 30 plus these 7; read the count from the run. panel.test.mjs's "both languages define exactly the same keys" still passes because `nav.agents` exists in both blocks. The merge itself never reaches it, since each file runs in its own process.

Run: `$PY -m app.test_simulation 2>&1 | tail -n 3`

Expected: `Ran 15 tests in …s`, a blank line, then `OK`. The count must be unchanged; read it from the run.

- [ ] **Step 6: Commit**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
test "$(git branch --show-current)" = JMF-2340550-sep17 && echo "on JMF-2340550-sep17" || echo "WRONG BRANCH -- stop"
git add app/static/sim/scene.mjs app/static/sim/i18n.mjs app/static/sim/agents-strings.mjs app/static/sim/agents-strings.test.mjs
git status --porcelain
OUT=$(mktemp -d)
node --test "app/static/sim/*.test.mjs" > "$OUT/node.txt" 2>&1; echo "node exit $?"
$PY -m app.test_simulation > "$OUT/sim.txt" 2>&1; echo "test_simulation exit $?"
$PY verify_docs.py > "$OUT/docs.txt" 2>&1; echo "verify_docs exit $?"; tail -n 1 "$OUT/docs.txt"
$PY -m app.test_replay > "$OUT/replay.txt" 2>&1; echo "test_replay exit $?"; tail -n 1 "$OUT/replay.txt"
```

Expected:
```
on JMF-2340550-sep17
A  app/static/sim/agents-strings.mjs
A  app/static/sim/agents-strings.test.mjs
M  app/static/sim/i18n.mjs
M  app/static/sim/scene.mjs
node exit 0
test_simulation exit 0
verify_docs exit 0
All 67 checks pass (... figure mentions scanned in the documents).
test_replay exit 0
49 of 49 checks pass
```

`verify_docs.py` scans `.md .py .html .js .txt` only, so the `.mjs` files cannot trip it. The mention count moves with the Python tasks' docstrings; read the line rather than expecting a number. test_replay takes about 90 s and verify_docs about 70 s. If any exit code is not 0, stop and diagnose before committing.

```bash
{
cat <<'EOF'
Agent replay T7: lend the lab's car, add nav.agents and the page's strings

scene.mjs: `export` on stage, ribbonGeometry and supra -- the keyword only
(design section 2 edit 2, approved section 11 Q2); no behaviour changes.
i18n.mjs: one key, nav.agents (الوكلاء / Agents), after nav.review in both
languages (edit 3). agents-strings.mjs: the 65 strings of /agents, Arabic
verbatim from design sections 5-6 where given, merged into i18n.STRINGS at
import by mergeStrings(), which refuses a collision, a one-language key or
an unknown language and writes nothing when it refuses. The lab never
imports it. agents-strings.test.mjs pins the merge, the honesty captions,
no "preview helps", and «المنمذَج» wherever the engine computer is named.

EOF
echo 'node --test "app/static/sim/*.test.mjs":'
grep -E '^ℹ (tests|pass|fail|skipped)' "$OUT/node.txt" | sed 's/^/  /'
echo; echo 'python -m app.test_simulation:'
tail -n 3 "$OUT/sim.txt" | sed 's/^/  /'
echo; echo 'python verify_docs.py (last line):'
tail -n 1 "$OUT/docs.txt" | sed 's/^/  /'
echo; echo 'python -m app.test_replay:'
sed 's/^/  /' "$OUT/replay.txt"
printf '\nCo-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>\n'
} | git commit -F -
git show --stat --format='%h %s' HEAD | tail -n 6
git log -1 --format=%B | tail -n 1
```

Expected: `4 files changed`, covering `app/static/sim/agents-strings.mjs` (222 lines), `agents-strings.test.mjs` (119), `i18n.mjs` (2 +) and `scene.mjs` (3 +, 3 −). The last line of the message is `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.

---


---

### Task 8: agent-view.mjs pure functions and the agent-scene.mjs chase view

**Files:**
- Create: `app/static/sim/agent-view.mjs`
- Create: `app/static/sim/agent-view.test.mjs`
- Create: `app/static/sim/agent-scene.mjs`
- Create: `app/static/sim/agent-scene.test.mjs`. This file is not in the skeleton. It runs the chase view under node through an injected stage and skips loudly without `app/node_modules/three`.
- Test: `app/static/sim/agent-view.test.mjs`, `app/static/sim/agent-scene.test.mjs`

**Interfaces:**
- Consumes:
  - `playback.mjs:2 PlaybackClock { duration, time, playing; tick(now), play(now)` (rewinds to 0 when `time >= duration`), `pause(now), seek(t, now) }`
  - T7: `stage`, `ribbonGeometry`, `supra` exported from `scene.mjs`; `AGENT_STRINGS` keys `agents.action.*` (merged by importing `agents-strings.mjs`)
  - T1 road: `{ s_m, x_m, z_m, grade_pct, speed_kmh }` arrays of 720, plus `length_m`, `rise_m`, `climb_start_s`, `p_baro_kpa`, `t_amb_c`
  - T2 frame: `{ k, cars: [car | null, car | null] }`, with lane 0 sighted, and `car.preview_pct[4]`
  - `engine_env._preview()` index rule `min(k + int(h/dt), len-1)`; `ACT_LO`/`ACT_HI` (the page passes `meta.act.lo/hi`)
- Produces (`agent-view.mjs`, no DOM, no Three.js):
  - Constants: `DT = 1`, `M_PER_UNIT = 10`, `PROFILE_VE = 3`, `GRADE_RAMP_MAX_PCT = 16`, `CAR_HALF_WIDTH = 1.49`, `CAR_OFFSET = 1.9`, `LANE_W = 3.2`, `ROAD_W = 7.6`.
  - `ACTIONS`: 5 frozen `{ key, label, unit, digits }` in engine_env order, with labels `agents.action.{spark,lambda,boost,fan,pump}`.
  - `createEpisodeRoad(road, mPerUnit = M_PER_UNIT) -> { length, mPerUnit, atDistance(d) -> { position: [x, y, 0], tangent: [tx, ty, 0] } }`. It works in world units, is exact at vertices, clamps, skips zero-length segments, and returns tangent `[1,0,0]` when degenerate.
  - `episodeAt(frames, road, t) -> { k, frame, s_m, x_m, z_m, t }`. It clamps t to `[0, frames.length]`; k is `-1` and frame `null` with no frames; s/x/z are `null` without a road.
  - `profilePoints(road, { ve = 3, width = 1000 } = {}) -> { points: [[x, y]] (y up), width, height, ve, sx }`
  - `previewMarks(road, k, previewS, dt = DT) -> [{ h, index, s_m, x_m, z_m, grade_pct }]`
  - `gaugeFraction(v, lo, hi) -> number in [0,1] | null`; `commandPhysical(cmd[5], lo[5], hi[5]) -> (number | null)[5]`; `gradeRamp(pct) -> number in [0,1] | null`
  - `createPlayState(clock) -> { clock, waiting: false, userPaused: true }`
  - `playOrWait(state, computedEnd, done, now) -> boolean` (true means waiting)
  - `pauseByUser(state, now)`
  - `resumeIfStalled(state, newEnd, now) -> boolean` (true means resumed)
  - `settleDone(state, end, now) -> boolean` (true means it was waiting)
  - `appendFrames(frames, payload) -> boolean`; `parseEpisodeQuery(search) -> { runs, seed: number, ep: number } | null`; `laneStoppedAt(frames, lane) -> k | null`
- Produces (`agent-scene.mjs`):
  - `createChaseScene(host, episodeRoad, lanes = { sighted, blind }, options = {}) -> { update({ distance_m, marks }), setTheme(name, lanes), dispose() }`
    - `marks` is `[{ s_m, grade_pct }]`; `[]` or absent hides the posts.
    - `options.makeStage` is for node tests only; the page never passes it.
    - Scene-graph names: `agents-world`, `car-sighted` (z +1.9), `car-blind` (z −1.9), `lane-sighted`, `lane-blind`, `preview-post-<i>`, `grid` and `centre-dashes`.

Deviations from the design and skeleton, one line each:
- `CAR_HALF_WIDTH` is 1.49, not the design's 1.48. supra's hub ring measures 1.4863; agent-scene.test.mjs re-measures it and pins the constant to within 0.01.
- Preview posts stand on the sighted car's road edge (z = 3.65), not inside its lane. At launch speeds a 2 s mark lies inside the car body.
- `stage()` sets `touch-action:none` for the lab's orbit controls. The static chase view resets it to `pan-y`, so a phone can still scroll past the view.
- The camera `[-6, 9, 26] → [8, 0, 0]` was chosen by rendering the real episode-1 road in headless Chrome at k = 130 (flat) and k = 200 (13.3 %). A camera placed more behind the cars made those two frames look identical. T11 re-checks by eye.
- `ribbonGeometry` keeps the design's 719 segments. Measured on episode 1, the chord at the climb-start kink sits at most 0.06 units (0.6 m) off the true road. That is accepted: it is invisible at this scale.

- [ ] **Step 1: Write the failing test (road, timing, gauges, constants)**

Create `app/static/sim/agent-view.test.mjs`:

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { PlaybackClock } from './playback.mjs';
import { STRINGS, LANGS } from './i18n.mjs';
import './agents-strings.mjs';
let V;
let loadError = null;
try { V = await import('./agent-view.mjs'); } catch (err) { loadError = err; }
const api = () => { assert.ok(V, `agent-view.mjs must load: ${loadError?.message}`); return V; };

// A short route built exactly as app/agent_trace.route() builds one (design
// section 5): ds_k = v_k * dt over the stepped samples, x += ds cos(atan g),
// z += ds sin(atan g). A launch from rest, flat running, then a 13.314 % climb.
const SPEED = [0, 10, 20, 30, 36.1, 36.1, 36.1, 36.1, 36.1, 36.1, 36.1, 36.1, 36.1, 36.1];
const GRADE = [0, 0, 0, 0, 0, 0, 0, 0.13314, 0.13314, 0.13314, 0.13314, 0.13314, 0.13314, 0.13314];
function makeRoad(v = SPEED, g = GRADE, dt = 1) {
  const s = [0], x = [0], z = [0];
  for (let k = 0; k < v.length - 1; k++) {
    const th = Math.atan(g[k]);
    const ds = v[k] * dt;
    s.push(s[k] + ds); x.push(x[k] + ds * Math.cos(th)); z.push(z[k] + ds * Math.sin(th));
  }
  return { s_m: s, x_m: x, z_m: z, grade_pct: g.map(u => u * 100), speed_kmh: v.map(u => u * 3.6) };
}
const road = makeRoad();
const LAST = road.s_m.length - 1;   // 13
const close = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol, `${msg}: ${a} vs ${b}`);

test('createEpisodeRoad is exact at every vertex, true to the slope, and clamped', () => {
  const { createEpisodeRoad, M_PER_UNIT } = api();
  const M = M_PER_UNIT;
  const r = createEpisodeRoad(road);
  assert.equal(r.mPerUnit, 10);
  assert.equal(r.length, road.s_m[LAST] / M);
  for (let k = 0; k <= LAST; k++) {
    const { position } = r.atDistance(road.s_m[k] / M);
    close(position[0], road.x_m[k] / M, 1e-12, `x at vertex ${k}`);
    close(position[1], road.z_m[k] / M, 1e-12, `z at vertex ${k}`);
    assert.equal(position[2], 0);
  }
  // On the climb the tangent's rise over run is the grade itself: the slope is not exaggerated.
  const onClimb = r.atDistance((road.s_m[9] + road.s_m[10]) / 2 / M).tangent;
  close(onClimb[1] / onClimb[0], 0.13314, 1e-12, 'rise over run on the climb');
  close(Math.hypot(...onClimb), 1, 1e-12, 'unit tangent');
  // s[0] == s[1] (launch from rest): the zero-length segment never yields a NaN tangent.
  assert.deepEqual(r.atDistance(0).tangent, [1, 0, 0]);
  assert.deepEqual(r.atDistance(-5), r.atDistance(0));
  assert.deepEqual(r.atDistance(NaN), r.atDistance(0));
  assert.deepEqual(r.atDistance(r.length + 50).position, [road.x_m[LAST] / M, road.z_m[LAST] / M, 0]);
  assert.deepEqual(createEpisodeRoad({ s_m: [0, 0], x_m: [0, 0], z_m: [0, 0] }).atDistance(0).tangent, [1, 0, 0]);
});

test('episodeAt is linear inside a step, clamped to the computed frames, and empty before any', () => {
  const { episodeAt } = api();
  const frames = [{ k: 0 }, { k: 1 }, { k: 2 }];
  const mid = episodeAt(frames, road, 1.25);
  assert.equal(mid.k, 1);
  assert.equal(mid.frame, frames[1]);
  close(mid.s_m, road.s_m[1] + 0.25 * (road.s_m[2] - road.s_m[1]), 1e-12, 's inside step 1');
  close(mid.z_m, road.z_m[1] + 0.25 * (road.z_m[2] - road.z_m[1]), 1e-12, 'z inside step 1');
  const past = episodeAt(frames, road, 99);   // three frames computed: the clock ends at t = 3
  assert.equal(past.t, 3);
  assert.equal(past.k, 2);
  assert.equal(past.s_m, road.s_m[3]);
  const before = episodeAt(frames, road, -4);
  assert.equal(before.t, 0);
  assert.equal(before.k, 0);
  assert.equal(before.s_m, road.s_m[0]);
  const none = episodeAt([], road, 5);
  assert.equal(none.k, -1);
  assert.equal(none.frame, null);
  assert.equal(none.s_m, road.s_m[0]);
  assert.equal(episodeAt(frames, null, 1).s_m, null);
});

test('profilePoints exaggerates elevation only; previewMarks stop at the last vertex', () => {
  const { profilePoints, previewMarks, PROFILE_VE } = api();
  assert.equal(PROFILE_VE, 3);
  const flat = profilePoints(road, { ve: 1, width: 500 });
  const tall = profilePoints(road, { width: 500 });
  assert.equal(tall.ve, 3);
  assert.equal(tall.points.length, road.x_m.length);
  close(tall.points[LAST][0], 500, 1e-9, 'x spans the width');
  close(tall.height, 3 * flat.height, 1e-9, 'height scales by ve');
  tall.points.forEach(([x, y], i) => {
    assert.equal(x, flat.points[i][0]);
    close(y, 3 * flat.points[i][1], 1e-9, `y at ${i}`);
  });
  // engine_env._preview(): min(k + int(h / dt), len - 1)
  const marks = previewMarks(road, 3, [2, 5, 15, 30]);
  assert.deepEqual(marks.map(m => m.index), [5, 8, 13, 13]);
  assert.deepEqual(marks.map(m => m.h), [2, 5, 15, 30]);
  assert.equal(marks[1].grade_pct, road.grade_pct[8]);
  assert.equal(marks[1].s_m, road.s_m[8]);
  assert.deepEqual(previewMarks(road, 0, [2], 0.2).map(m => m.index), [10]);
});

test('gauges, commands and the grade ramp', () => {
  const { gaugeFraction, commandPhysical, gradeRamp, GRADE_RAMP_MAX_PCT } = api();
  assert.equal(gaugeFraction(-8, -8, 4), 0);
  assert.equal(gaugeFraction(4, -8, 4), 1);
  assert.equal(gaugeFraction(0, -8, 4), 8 / 12);            // the spark «بلا تعديل» tick
  assert.equal(gaugeFraction(1, 0.3, 1), 1);                // pump at the baseline row's 1.0
  assert.equal(gaugeFraction(9, -8, 4), 1);
  for (const bad of [null, undefined, NaN, Infinity]) assert.equal(gaugeFraction(bad, 0, 1), null);
  assert.equal(gaugeFraction(0.5, 1, 1), null);
  const LO = [-8, -0.15, -40, 0, 0.3];
  const HI = [4, 0.06, 15, 1, 1];
  assert.deepEqual(commandPhysical([-1, -1, -1, -1, -1], LO, HI), LO);
  assert.deepEqual(commandPhysical([1, 1, 1, 1, 1], LO, HI), HI);
  assert.deepEqual(commandPhysical([-7, 7, 2, -2, 1], LO, HI), [-8, 0.06, 15, 0, 1]);
  const mid = commandPhysical([0, 0, 0, 0, 0], LO, HI);
  [-2, -0.045, -12.5, 0.5, 0.65].forEach((v, i) => close(mid[i], v, 1e-12, `midpoint ${i}`));
  assert.equal(commandPhysical([NaN, 0, 0, 0, 0], LO, HI)[0], null);
  assert.equal(GRADE_RAMP_MAX_PCT, 16);
  assert.equal(gradeRamp(0), 0);
  assert.equal(gradeRamp(8), 0.5);
  assert.equal(gradeRamp(16), 1);
  assert.equal(gradeRamp(21), 1);
  assert.equal(gradeRamp(-2), 0);
  assert.equal(gradeRamp(null), null);
});

test('the two cars and their lanes fit the road without touching', () => {
  const { CAR_OFFSET, CAR_HALF_WIDTH, LANE_W, ROAD_W, M_PER_UNIT, DT } = api();
  assert.equal(M_PER_UNIT, 10);
  assert.equal(DT, 1);
  assert.ok(2 * CAR_OFFSET > 2 * CAR_HALF_WIDTH, 'the cars overlap');
  assert.ok(LANE_W > 2 * CAR_HALF_WIDTH, 'a lane tint is narrower than its car');
  assert.ok(CAR_OFFSET + LANE_W / 2 <= ROAD_W / 2, 'a lane tint runs off the road');
  assert.ok(CAR_OFFSET - LANE_W / 2 >= 0, 'the two lane tints overlap');
});

test('ACTIONS lists the five actions in engine_env order, each with a label in both languages', () => {
  const { ACTIONS } = api();
  assert.equal(ACTIONS.length, 5);
  assert.deepEqual(ACTIONS.map(a => a.key), ['spark', 'lambda', 'boost', 'fan', 'pump']);
  for (const a of ACTIONS) {
    for (const lang of LANGS) assert.ok(STRINGS[lang][a.label], `${a.label} missing in ${lang}`);
  }
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `node --test app/static/sim/agent-view.test.mjs 2>&1 | grep -E "^ℹ (tests|pass|fail)|AssertionError" | sort | uniq -c`

Expected: FAIL. `ℹ tests 6`, `ℹ pass 0`, `ℹ fail 6`, with six `AssertionError [ERR_ASSERTION]: agent-view.mjs must load: Cannot find module '...\app\static\sim\agent-view.mjs' imported from ...\agent-view.test.mjs`.

- [ ] **Step 3: Implement the road, timing and gauge half of agent-view.mjs**

Create `app/static/sim/agent-view.mjs`:

```js
// Pure presentation logic for /agents. No DOM, no Three.js, no fetch, and no
// physics: every number this module handles was computed in Python by
// app/agent_trace.py and arrived as JSON. It decides WHERE and WHEN to show a
// value, never what the value is, and it computes nothing that compares the two
// cars. That is why all of it can be tested under node without a browser.

// The scoring protocol's step (evaluate.py DT = 1.0). Frame k covers t = k..k+1.
export const DT = 1;
// Chase-view scale: metres per world unit, the SAME on both axes, so the slope
// on screen is the true slope (design section 5). Changing it alone would not
// exaggerate anything, but the caption «الميل غير مضخّم» depends on it being one
// number for x and z.
export const M_PER_UNIT = 10;
// The whole-route profile's vertical exaggeration; the page prints it (×3).
export const PROFILE_VE = 3;
// Preview marks are coloured on one hue from 0 to this grade, in percent.
export const GRADE_RAMP_MAX_PCT = 16;
// supra()'s bounding half-width in world units, measured on its geometry with
// the light pools left out: the wheel hub ring reaches 1.23 + 0.2 + 0.0563 =
// 1.486 (scene.mjs supra, a TorusGeometry with 6 radial segments). The design's
// "about 1.48" stopped at the spokes (1.4825); agent-scene.test.mjs re-measures.
export const CAR_HALF_WIDTH = 1.49;
// Lateral offset of each car from the road centre: + is the sighted lane, - the
// blind lane. ±1.9 leaves a gap of about 0.83 units between the two cars.
export const CAR_OFFSET = 1.9;
// Width of each lane tint, and of the whole road ribbon.
export const LANE_W = 3.2;
export const ROAD_W = 7.6;

// The five actions in engine_env order (ACT_LO / ACT_HI, engine_env.py:513-514).
// The labels are i18n keys from agents-strings.mjs; digits is display rounding.
export const ACTIONS = Object.freeze([
  Object.freeze({ key: 'spark', label: 'agents.action.spark', unit: '°', digits: 1 }),
  Object.freeze({ key: 'lambda', label: 'agents.action.lambda', unit: 'λ', digits: 3 }),
  Object.freeze({ key: 'boost', label: 'agents.action.boost', unit: 'kPa', digits: 1 }),
  Object.freeze({ key: 'fan', label: 'agents.action.fan', unit: '', digits: 2 }),
  Object.freeze({ key: 'pump', label: 'agents.action.pump', unit: '', digits: 2 }),
]);

const finite = Number.isFinite;
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
// Exact at both ends: a + 1 * (b - a) is not always b in floating point.
const lerp = (a, b, u) => (u === 0 ? a : u === 1 ? b : a + u * (b - a));

// Index of the last vertex at or before `value` in an ascending array
// (-1 when value is below the first vertex).
function lastAtOrBefore(values, value) {
  let lo = 0;
  let hi = values.length;
  while (lo < hi) {
    const mid = (lo + hi) >>> 1;
    if (values[mid] <= value) lo = mid + 1; else hi = mid;
  }
  return lo - 1;
}

/**
 * The episode road in the shape scene.mjs's ribbonGeometry() walks:
 * { length, atDistance(d) -> { position: [x, y, z], tangent: [x, y, z] } }.
 *
 * World X is distance along the (straight) route, world Y is elevation, world Z
 * is across the road; all in world units of `mPerUnit` metres. Positions are
 * linear between the route's own vertices, so they are EXACT at every vertex,
 * and the tangent is the unit vector of the segment the point lies on. The first
 * segment of every episode has zero length (the launch starts at v = 0, so
 * s[0] == s[1]); a zero-length segment never supplies a tangent.
 */
export function createEpisodeRoad(road, mPerUnit = M_PER_UNIT) {
  const s = road.s_m.map(v => v / mPerUnit);
  const x = road.x_m.map(v => v / mPerUnit);
  const z = road.z_m.map(v => v / mPerUnit);
  const last = s.length - 1;
  const length = s[last];
  const atDistance = d => {
    if (last < 1) return { position: [x[0], z[0], 0], tangent: [1, 0, 0] };
    const dd = clamp(finite(d) ? d : 0, 0, length);
    let i = clamp(lastAtOrBefore(s, dd), 0, last - 1);
    while (i < last - 1 && s[i + 1] === s[i]) i += 1;   // onto a segment with length
    let t = i;
    while (t > 0 && s[t + 1] === s[t]) t -= 1;           // a tangent from one with length
    const span = s[i + 1] - s[i];
    const u = span > 0 ? clamp((dd - s[i]) / span, 0, 1) : 0;
    const dx = x[t + 1] - x[t];
    const dz = z[t + 1] - z[t];
    const n = Math.hypot(dx, dz);
    return {
      position: [lerp(x[i], x[i + 1], u), lerp(z[i], z[i + 1], u), 0],
      tangent: n > 0 ? [dx / n, dz / n, 0] : [1, 0, 0],
    };
  };
  return { length, mPerUnit, atDistance };
}

/**
 * Where both cars are at clock time t (seconds). The scenario imposes the speed
 * (engine_env.py:729), so the two cars share one s. Within a step the env holds
 * speed constant, so s, x and z are linear between vertex k and k + 1: exact.
 *
 * t is clamped to [0, frames.length] -- the computed end -- and k to the last
 * computed frame. With no frames, k is -1 and frame is null.
 */
export function episodeAt(frames, road, t) {
  const n = frames.length;
  const tt = clamp(finite(t) ? t : 0, 0, n);
  const k = n ? Math.min(Math.floor(tt), n - 1) : -1;
  const frame = k >= 0 ? frames[k] : null;
  if (!road) return { k, frame, s_m: null, x_m: null, z_m: null, t: tt };
  const i = Math.max(0, k);
  const j = Math.min(i + 1, road.s_m.length - 1);
  const u = k >= 0 ? tt - k : 0;
  const at = a => lerp(a[i], a[j], u);
  return { k, frame, s_m: at(road.s_m), x_m: at(road.x_m), z_m: at(road.z_m), t: tt };
}

/**
 * The whole-route side profile as points in a y-UP box `width` wide. x is
 * scaled to fit; y is the same scale times `ve`, so the exaggeration applies to
 * elevation only. The caller flips y for SVG (svgY = height - y).
 */
export function profilePoints(road, { ve = PROFILE_VE, width = 1000 } = {}) {
  const x0 = road.x_m[0];
  const span = road.x_m[road.x_m.length - 1] - x0;
  const zMin = Math.min(...road.z_m);
  const zMax = Math.max(...road.z_m);
  const sx = span > 0 ? width / span : 0;
  const points = road.x_m.map((x, i) => [(x - x0) * sx, (road.z_m[i] - zMin) * sx * ve]);
  return { points, width, height: (zMax - zMin) * sx * ve, ve, sx };
}

/**
 * The road positions the sighted agent's four preview inputs describe at step
 * k: engine_env._preview() reads the grade at min(k + int(h / dt), len - 1).
 * Math.trunc is Python's int() for these non-negative horizons.
 */
export function previewMarks(road, k, previewS, dt = DT) {
  const last = road.s_m.length - 1;
  return previewS.map(h => {
    const index = Math.min(Math.max(0, k) + Math.trunc(h / dt), last);
    return { h, index, s_m: road.s_m[index], x_m: road.x_m[index], z_m: road.z_m[index], grade_pct: road.grade_pct[index] };
  });
}

/** Position of v on a bar from lo to hi, clamped to [0, 1]; null when unknown. */
export function gaugeFraction(v, lo, hi) {
  if (![v, lo, hi].every(finite) || hi <= lo) return null;
  return clamp((v - lo) / (hi - lo), 0, 1);
}

/**
 * The network's command in physical units, as engine_env._rescale does it
 * (lo + (clip(a, -1, 1) + 1) / 2 * (hi - lo)). For DISPLAY of a held command
 * only: this is float64 where the env is float32, and the applied value always
 * comes from the frame, never from here.
 */
export function commandPhysical(cmd, lo, hi) {
  return cmd.map((a, i) => (finite(a) && finite(lo[i]) && finite(hi[i])
    ? lo[i] + (clamp(a, -1, 1) + 1) / 2 * (hi[i] - lo[i])
    : null));
}

/** 0 at a flat road, 1 at GRADE_RAMP_MAX_PCT and steeper; null when unknown. */
export function gradeRamp(pct) {
  return finite(pct) ? clamp(pct / GRADE_RAMP_MAX_PCT, 0, 1) : null;
}

```

- [ ] **Step 4: Run to verify it passes**

Run: `node --test app/static/sim/agent-view.test.mjs 2>&1 | grep -E "^(✔|✖)|^ℹ (tests|pass|fail)"`

Expected: six `✔`, then `ℹ tests 6`, `ℹ pass 6`, `ℹ fail 0`.

- [ ] **Step 5: Write the failing test (play state at the computed edge, polling, picker)**

Append this block to the end of `app/static/sim/agent-view.test.mjs`:

```js

// ------------------------------------------------ playback at the computed edge
// PlaybackClock.play() rewinds to 0 at its end (playback.mjs:9). While the
// episode is still being computed, the clock's end is the COMPUTED end.

test('play at the computed edge waits instead of rewinding, and rewinds once done', () => {
  const { createPlayState, playOrWait } = api();
  const state = createPlayState(new PlaybackClock(0));
  assert.deepEqual({ waiting: state.waiting, userPaused: state.userPaused }, { waiting: false, userPaused: true });
  state.clock.duration = 5;
  state.clock.seek(5, 0);
  assert.equal(playOrWait(state, 5, false, 100), true);
  assert.equal(state.waiting, true);
  assert.equal(state.clock.time, 5, 'it rewound at the computed edge');
  assert.equal(state.clock.playing, false);
  assert.equal(playOrWait(state, 5, true, 200), false);   // the build is done: behave like the lab
  assert.equal(state.waiting, false);
  assert.equal(state.clock.time, 0);
  assert.equal(state.clock.playing, true);
  const inside = createPlayState(new PlaybackClock(0));
  inside.clock.duration = 5;
  inside.clock.seek(2, 0);
  assert.equal(playOrWait(inside, 5, false, 0), false);
  assert.equal(inside.clock.time, 2);
  assert.equal(inside.clock.playing, true);
});

test('new frames resume a wait or a stop at the edge, never a pause the viewer made', () => {
  const { createPlayState, playOrWait, pauseByUser, resumeIfStalled } = api();
  // (a) waiting after play at the edge
  const waiting = createPlayState(new PlaybackClock(0));
  playOrWait(waiting, 0, false, 0);                          // play pressed before any frame
  assert.equal(waiting.waiting, true);
  assert.equal(resumeIfStalled(waiting, 4, 300), true);
  assert.equal(waiting.clock.duration, 4);
  assert.equal(waiting.clock.playing, true);
  assert.equal(waiting.waiting, false);
  // (b) playback ran into the computed edge by itself
  const edge = createPlayState(new PlaybackClock(0));
  playOrWait(edge, 3, false, 0);
  assert.equal(edge.clock.tick(5000), 3);
  assert.equal(edge.clock.playing, false);
  assert.equal(resumeIfStalled(edge, 6, 5000), true);
  assert.equal(edge.clock.time, 3);
  assert.equal(edge.clock.playing, true);
  // (c) the viewer paused: the duration still grows, playback does not resume
  const paused = createPlayState(new PlaybackClock(0));
  playOrWait(paused, 10, false, 0);
  pauseByUser(paused, 1000);
  assert.equal(resumeIfStalled(paused, 20, 2000), false);
  assert.equal(paused.clock.duration, 20);
  assert.equal(paused.clock.playing, false);
  assert.equal(paused.clock.time, 1);
  paused.clock.seek(20, 2000);                               // paused AT the edge is still a pause
  assert.equal(resumeIfStalled(paused, 30, 2000), false);
  // (d) nothing was ever played: frames arriving start nothing
  const idle = createPlayState(new PlaybackClock(0));
  assert.equal(resumeIfStalled(idle, 7, 0), false);
  assert.equal(idle.clock.duration, 7);
  assert.equal(idle.clock.playing, false);
  // (e) playing well inside the computed part: keep playing, just extend
  const running = createPlayState(new PlaybackClock(0));
  playOrWait(running, 10, false, 0);
  assert.equal(resumeIfStalled(running, 12, 1000), false);
  assert.equal(running.clock.playing, true);
  assert.equal(running.clock.duration, 12);
});

test('settleDone releases a wait that a ready poll with no new frames would leave pending', () => {
  const { createPlayState, playOrWait, resumeIfStalled, settleDone } = api();
  const state = createPlayState(new PlaybackClock(0));
  playOrWait(state, 719, false, 0);
  state.clock.seek(719, 0);
  playOrWait(state, 719, false, 10);                         // pressed at the edge: waiting
  assert.equal(state.waiting, true);
  assert.equal(resumeIfStalled(state, 719, 20), false);      // 'ready' brought no new frame
  assert.equal(settleDone(state, 719, 30), true);
  assert.equal(state.waiting, false);
  assert.equal(state.clock.duration, 719);
  assert.equal(playOrWait(state, 719, true, 40), false);     // next play rewinds, as in the lab
  assert.equal(state.clock.time, 0);
  assert.equal(state.clock.playing, true);
  // a cached 'ready' delivering all 719 frames at once to a page waiting at 0
  const cached = createPlayState(new PlaybackClock(0));
  playOrWait(cached, 0, false, 0);
  assert.equal(resumeIfStalled(cached, 719, 5), true);
  assert.equal(settleDone(cached, 719, 5), false);
  assert.equal(cached.clock.playing, true);
});

// ------------------------------------------------------------------ polling

test('appendFrames takes only the slice that starts where the held frames end', () => {
  const { appendFrames } = api();
  const frames = [];
  assert.equal(appendFrames(frames, { since: 0, frames: [{ k: 0 }, { k: 1 }] }), true);
  const held = structuredClone(frames);
  assert.equal(appendFrames(frames, { since: 0, frames: [{ k: 0 }] }), false, 'stale since');
  assert.equal(appendFrames(frames, { since: 1, frames: [{ k: 1 }, { k: 2 }] }), false, 'overlap');
  assert.equal(appendFrames(frames, { since: 3, frames: [{ k: 3 }] }), false, 'gap');
  assert.equal(appendFrames(frames, { since: 2, frames: [{ k: 3 }] }), false, 'k does not match its index');
  assert.equal(appendFrames(frames, null), false);
  assert.equal(appendFrames(frames, { since: 2 }), false);
  assert.deepEqual(frames, held);
  assert.equal(appendFrames(frames, { since: 2, frames: [] }), true, 'an empty slice at the right since');
  assert.deepEqual(frames, held);
  assert.equal(appendFrames(frames, { since: 2, frames: [{ k: 2 }] }), true);
  assert.deepEqual(frames.map(f => f.k), [0, 1, 2]);
});

test('parseEpisodeQuery reads the M1 address and nothing else', () => {
  const { parseEpisodeQuery } = api();
  assert.deepEqual(parseEpisodeQuery('?runs=runs_c4&seed=5&ep=1'), { runs: 'runs_c4', seed: 5, ep: 1 });
  assert.deepEqual(parseEpisodeQuery('runs=runs&seed=0&ep=20'), { runs: 'runs', seed: 0, ep: 20 });
  for (const bad of ['?runs=runs_c4&seed=5abc&ep=1', '?runs=../x&seed=5&ep=1', '?runs=runs_c4/../runs&seed=5&ep=1',
    '?runs=runs_c4&seed=5&ep=0', '?runs=runs_c4&seed=5&ep=21', '?runs=runs_c4&seed=1234&ep=1',
    '?runs=runs_c4&seed=5', '?seed=5&ep=1', '', undefined]) {
    assert.equal(parseEpisodeQuery(bad), null, String(bad));
  }
});

test('laneStoppedAt names the first step a car went null', () => {
  const { laneStoppedAt } = api();
  const car = { damage: 0 };
  const frames = [{ k: 0, cars: [car, car] }, { k: 1, cars: [car, null] }, { k: 2, cars: [car, null] }];
  assert.equal(laneStoppedAt(frames, 1), 1);
  assert.equal(laneStoppedAt(frames, 0), null);
  assert.equal(laneStoppedAt([], 0), null);
});
```

- [ ] **Step 6: Run it to verify it fails**

Run: `node --test app/static/sim/agent-view.test.mjs 2>&1 | grep -E "^ℹ (tests|pass|fail)|TypeError" | sort | uniq -c`

Expected: FAIL. `ℹ tests 12`, `ℹ pass 6`, `ℹ fail 6`, with:
- `3 TypeError: createPlayState is not a function`
- `1 TypeError: appendFrames is not a function`
- `1 TypeError: parseEpisodeQuery is not a function`
- `1 TypeError: laneStoppedAt is not a function`

- [ ] **Step 7: Implement the play state, polling and picker half**

Append this block to the end of `app/static/sim/agent-view.mjs`. It follows the blank line after `gradeRamp`:

```js
// ---------------------------------------------------------------- playback
// PlaybackClock.play() rewinds to 0 when time >= duration (playback.mjs:9).
// While the episode is still being computed, the clock's duration is the
// COMPUTED end, so a play pressed there must wait for frames instead.

/** userPaused starts true: nothing plays until the viewer presses play. */
export function createPlayState(clock) {
  return { clock, waiting: false, userPaused: true };
}

/**
 * The play button. Returns true when it is now WAITING for frames. It never
 * calls clock.play() at the computed edge of an unfinished build, because that
 * would rewind to 0.
 */
export function playOrWait(state, computedEnd, done, now) {
  const { clock } = state;
  clock.tick(now);
  clock.duration = Math.max(0, computedEnd);
  state.userPaused = false;
  if (!done && clock.time >= clock.duration) {
    clock.pause(now);
    state.waiting = true;
    return true;
  }
  state.waiting = false;
  clock.play(now);
  return false;
}

/** The pause button: the viewer's own stop, which no frame arrival undoes. */
export function pauseByUser(state, now) {
  state.clock.pause(now);
  state.userPaused = true;
  state.waiting = false;
}

/**
 * Frames arrived: the computed end moved to newEnd. Always extends the clock's
 * duration. Resumes playback only if the viewer did not pause and the clock had
 * stopped at the old edge or was waiting. Returns true when it resumed.
 */
export function resumeIfStalled(state, newEnd, now) {
  const { clock } = state;
  clock.tick(now);
  const stalled = state.waiting || (!clock.playing && clock.time >= clock.duration);
  clock.duration = Math.max(clock.duration, newEnd);
  if (state.userPaused || !stalled || clock.time >= clock.duration) return false;
  state.waiting = false;
  clock.play(now);
  return true;
}

/**
 * The build finished ('ready'). Fixes the clock's duration at `end` and clears
 * a wait that no new frame will ever release. Returns whether it was waiting,
 * so the caller can turn the button back to play; the next play then behaves
 * like the lab's (it rewinds from the end).
 */
export function settleDone(state, end, now) {
  const { clock } = state;
  clock.tick(now);
  clock.duration = Math.max(0, end);
  const was = state.waiting;
  state.waiting = false;
  return was;
}

// ---------------------------------------------------------------- polling

/**
 * Append one poll's slice of frames. Accepted only when it starts exactly at
 * the end of what is held (payload.since === frames.length) and every incoming
 * frame's k equals its index, so a stale, overlapping or gapped response can
 * never shift the clock onto another second's decision. Mutates only on
 * accept; an empty slice at the right since is accepted and changes nothing.
 */
export function appendFrames(frames, payload) {
  if (!payload || !Array.isArray(payload.frames) || payload.since !== frames.length) return false;
  const base = frames.length;
  if (!payload.frames.every((f, i) => f && f.k === base + i)) return false;
  frames.push(...payload.frames);
  return true;
}

const RUNS_RE = /^runs[A-Za-z0-9_]*$/;
const SEED_RE = /^\d{1,3}$/;
const EP_RE = /^\d{1,2}$/;

/**
 * The M1 page's read-only picker: ?runs=runs_c4&seed=5&ep=1. All three are
 * required and must match the server's own validation; anything else is null,
 * and the page then selects nothing.
 */
export function parseEpisodeQuery(search) {
  const q = new URLSearchParams(typeof search === 'string' ? search : '');
  const runs = q.get('runs');
  const seed = q.get('seed');
  const ep = q.get('ep');
  if (runs === null || seed === null || ep === null) return null;
  if (!RUNS_RE.test(runs) || !SEED_RE.test(seed) || !EP_RE.test(ep)) return null;
  const epNum = Number(ep);
  if (epNum < 1 || epNum > 20) return null;
  return { runs, seed: Number(seed), ep: epNum };
}

/** Step at which a lane's car first went null (its simulation stopped), or null. */
export function laneStoppedAt(frames, lane) {
  const k = frames.findIndex(f => f && f.cars && f.cars[lane] == null);
  return k < 0 ? null : frames[k].k;
}
```

- [ ] **Step 8: Run to verify it passes**

Run: `node --test app/static/sim/agent-view.test.mjs 2>&1 | grep -E "^(✔|✖)|^ℹ (tests|pass|fail)"`

Expected: twelve `✔`, then `ℹ tests 12`, `ℹ pass 12`, `ℹ fail 0`.

- [ ] **Step 9: Write the failing test for the chase view**

First confirm Three.js is installed for node, because this cycle must be seen to FAIL, not skip. Run: `test -f app/node_modules/three/package.json && echo three-ok`. Expected: `three-ok`. If it is missing, run `cd app && npm install && cd ..`; the directory is gitignored.

Create `app/static/sim/agent-scene.test.mjs`:

```js
// The chase view without a browser: stage() needs WebGL, so these tests hand
// createChaseScene a stand-in stage that owns a real THREE.Scene and nothing
// else, and read the scene graph. What they cannot see (pixels, the camera
// framing, the shadows) is checked by eye in the browser (Task 11).
//
// Three.js lives in app/node_modules (npm install in app/, which
// app\start-simulation.ps1 runs when it has to vendor Three.js); .gitignore
// excludes it. Without it every test here SKIPS and says why. With it, a
// broken agent-scene.mjs FAILS: only the 'three' import is guarded.
import test from 'node:test';
import assert from 'node:assert/strict';
import { createEpisodeRoad, CAR_OFFSET, CAR_HALF_WIDTH, LANE_W, ROAD_W, M_PER_UNIT } from './agent-view.mjs';

let THREE = null;
try { THREE = await import('three'); } catch { /* reported through SKIP */ }
const SKIP = THREE ? false : 'three is not installed in app/node_modules (run: cd app; npm install)';
let S = null;
let lab = null;
let loadError = null;
if (THREE) {
  try { lab = await import('./scene.mjs'); S = await import('./agent-scene.mjs'); } catch (err) { loadError = err; }
}
const api = () => { assert.ok(S, `agent-scene.mjs must load: ${loadError?.message}`); return S; };
const close = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol, `${msg}: ${a} vs ${b}`);

// A route built the way app/agent_trace.route() builds one: launch from rest,
// flat, then 13.314 % from step 20.
function makeRoad() {
  const v = Array.from({ length: 60 }, (_, k) => Math.min(36.1, 2 * k));
  const g = v.map((_, k) => (k >= 20 ? 0.13314 : 0));
  const s = [0], x = [0], z = [0];
  for (let k = 0; k < v.length - 1; k++) {
    const th = Math.atan(g[k]);
    s.push(s[k] + v[k]); x.push(x[k] + v[k] * Math.cos(th)); z.push(z[k] + v[k] * Math.sin(th));
  }
  return { s_m: s, x_m: x, z_m: z, grade_pct: g.map(u => u * 100), speed_kmh: v.map(u => u * 3.6) };
}
const ROUTE = makeRoad();

// Stands in for scene.mjs stage(): same shape, a real Scene, no renderer.
function fakeStage() {
  let theme = 'light';
  const seen = { renders: 0, disposed: false, options: null, view: null };
  const paint = {
    mat: (key, extra = {}) => new THREE.MeshStandardMaterial(extra),
    loose: (key, extra = {}) => new THREE.MeshStandardMaterial(extra),
    glow: (key, extra = {}) => new THREE.MeshBasicMaterial(extra),
    theme: () => theme,
  };
  const make = (host, options) => {
    seen.options = options;
    seen.view = {
      scene: new THREE.Scene(),
      camera: new THREE.OrthographicCamera(),
      renderer: { domElement: { style: {} } },
      render: () => { seen.renders += 1; },
      paint,
      setTheme: name => { theme = name === 'dark' ? 'dark' : 'light'; },
      theme: () => theme,
      dispose: () => { seen.disposed = true; },
    };
    return seen.view;
  };
  return { make, seen, paint };
}
function build(lanes = { sighted: '#0000ff', blind: '#ffaa00' }) {
  const fake = fakeStage();
  const road = createEpisodeRoad(ROUTE);
  const chase = api().createChaseScene({}, road, lanes, { makeStage: fake.make });
  return { chase, road, scene: fake.seen.view.scene, seen: fake.seen };
}

test('the lab car is no wider than CAR_HALF_WIDTH, and the constant is tight', { skip: SKIP }, () => {
  api();
  const { car } = lab.supra(new THREE.Scene(), fakeStage().paint);
  car.updateMatrixWorld(true);
  const body = new THREE.Box3();
  // renderOrder -1 marks scene.mjs glowMesh(): headlight beams and light pools
  // on the road, which are light, not car.
  car.traverse(o => { if (o.isMesh && o.renderOrder !== -1) body.union(new THREE.Box3().setFromObject(o, true)); });
  const half = Math.max(-body.min.z, body.max.z);
  assert.ok(half <= CAR_HALF_WIDTH, `supra is ${half} wide each side, over CAR_HALF_WIDTH`);
  assert.ok(half > CAR_HALF_WIDTH - 0.01, `CAR_HALF_WIDTH is loose: supra measures ${half}`);
});

test('the road slides under two still cars and a still camera', { skip: SKIP }, () => {
  const { chase, road, scene, seen } = build();
  assert.ok(seen.options.extent > 0);
  assert.equal(seen.view.renderer.domElement.style.touchAction, 'pan-y');
  const camera = seen.view.camera.position.clone();
  const world = scene.getObjectByName('agents-world');
  for (const metres of [0, 150, 900, 1e9]) {
    chase.update({ distance_m: metres });
    const p = road.atDistance(Math.min(road.length, metres / M_PER_UNIT)).position;
    assert.deepEqual(world.position.toArray(), [-p[0], -p[1], 0], `world at ${metres} m`);
    assert.deepEqual(scene.getObjectByName('car-sighted').position.toArray(), [0, 0.085, CAR_OFFSET]);
    assert.deepEqual(scene.getObjectByName('car-blind').position.toArray(), [0, 0.085, -CAR_OFFSET]);
    assert.ok(seen.view.camera.position.equals(camera), 'the camera moved');
  }
  const held = world.position.clone();
  chase.update({ distance_m: NaN });
  assert.ok(world.position.equals(held), 'a non-finite distance moved the road');
});

test('both cars pitch to the true slope, the same way', { skip: SKIP }, () => {
  const { chase, scene } = build();
  chase.update({ distance_m: 100 });                        // flat
  let fwd = new THREE.Vector3(1, 0, 0).applyQuaternion(scene.getObjectByName('car-sighted').quaternion);
  close(fwd.y, 0, 1e-12, 'flat pitch');
  const climbM = (ROUTE.s_m[30] + ROUTE.s_m[31]) / 2;        // on the 13.314 % climb
  chase.update({ distance_m: climbM });
  for (const name of ['car-sighted', 'car-blind']) {
    fwd = new THREE.Vector3(1, 0, 0).applyQuaternion(scene.getObjectByName(name).quaternion);
    close(fwd.y / fwd.x, 0.13314, 1e-9, `${name} rise over run`);
    close(fwd.z, 0, 1e-12, `${name} yaw`);
  }
});

test('preview posts stand at the marks on the sighted edge, coloured by grade, and hide without marks', { skip: SKIP }, () => {
  const { chase, road, scene } = build();
  chase.update({ distance_m: 300, marks: [{ s_m: 400, grade_pct: 13.3 }, { s_m: 700, grade_pct: 0 }, { s_m: NaN, grade_pct: null }] });
  const posts = [0, 1, 2].map(i => scene.getObjectByName(`preview-post-${i}`));
  assert.deepEqual(posts.map(p => p.visible), [true, true, false]);
  const q = road.atDistance(400 / M_PER_UNIT).position;
  close(posts[0].position.x, q[0], 1e-9, 'post along the road');
  close(posts[0].position.y, q[1] + 0.04, 1e-9, 'post on the road surface');
  assert.ok(posts[0].position.z - 0.07 > CAR_OFFSET + CAR_HALF_WIDTH, 'a post stands inside the sighted car');
  assert.ok(posts[0].position.z + 0.07 <= ROAD_W / 2, 'a post stands off the road');
  const light = p => p.getObjectByName('flag').material.color.getHSL({}).l;
  assert.ok(light(posts[0]) < light(posts[1]), 'a steeper grade must read stronger on the light theme');
  chase.update({ distance_m: 310 });
  assert.deepEqual(posts.map(p => p.visible), [false, false, false]);
});

test('lane tints sit on their own side in the lane colours, and follow setTheme', { skip: SKIP }, () => {
  const { chase, scene } = build();
  const lanes = { sighted: scene.getObjectByName('lane-sighted'), blind: scene.getObjectByName('lane-blind') };
  for (const [name, sign] of [['sighted', 1], ['blind', -1]]) {
    const g = lanes[name].geometry;
    g.computeBoundingBox();
    close(g.boundingBox.min.z, sign * CAR_OFFSET - LANE_W / 2, 1e-6, `${name} min z`);
    close(g.boundingBox.max.z, sign * CAR_OFFSET + LANE_W / 2, 1e-6, `${name} max z`);
  }
  assert.equal(lanes.sighted.material.color.getHexString(), '0000ff');
  assert.equal(lanes.blind.material.color.getHexString(), 'ffaa00');
  chase.setTheme('dark', { sighted: ' #123456 ' });          // getComputedStyle keeps the space
  assert.equal(lanes.sighted.material.color.getHexString(), '123456');
  assert.equal(lanes.blind.material.color.getHexString(), 'ffaa00');
});

test('dispose is final and idempotent', { skip: SKIP }, () => {
  const { chase, seen } = build();
  chase.dispose();
  chase.dispose();
  assert.equal(seen.disposed, true);
  const renders = seen.renders;
  chase.update({ distance_m: 50 });
  chase.setTheme('dark');
  assert.equal(seen.renders, renders);
});
```

- [ ] **Step 10: Run it to verify it fails**

Run: `node --test app/static/sim/agent-scene.test.mjs 2>&1 | grep -E "^ℹ (tests|pass|fail|skipped)|must load" | sort | uniq -c`

Expected: FAIL, not skip. `ℹ tests 6`, `ℹ pass 0`, `ℹ fail 6`, `ℹ skipped 0`, with `agent-scene.mjs must load: Cannot find module '...\app\static\sim\agent-scene.mjs' imported from ...\agent-scene.test.mjs`. If the output reads `skipped 6`, Three.js is missing; go back to Step 9's check.

- [ ] **Step 11: Implement agent-scene.mjs**

Create `app/static/sim/agent-scene.mjs`:

```js
// The /agents chase view: two cars side by side on the episode's own road.
//
// Built from the lab's own parts (stage, ribbonGeometry and supra, exported by
// scene.mjs for this page; design section 11 Q2), so the car is the lab's car.
// It draws; it never computes. Every position comes from createEpisodeRoad()
// (agent-view.mjs), which reads the Python route, and every colour of a
// preview post comes from the grade the sighted agent was given.
//
// FLOATING ORIGIN. The cars and the camera never move. Each update translates
// the world group by minus the road point under the cars, so the road slides
// under them. The camera is stage()'s orthographic camera, static, and the
// sun's shadow box (±45 units about the origin, scene.mjs stage()) therefore
// always covers the cars. One world unit is M_PER_UNIT metres on BOTH axes, so
// the slope on screen is the true slope (the caption says so); the car is not
// to scale (about 6.5 units, 65 m, long).
import * as THREE from 'three';
import { stage, ribbonGeometry, supra } from './scene.mjs';
import { CAR_OFFSET, LANE_W, ROAD_W, gradeRamp } from './agent-view.mjs';

const UP = new THREE.Vector3(0, 1, 0);
// Camera: a little behind the cars (-x), above them, and well out on the
// sighted car's side (+z), so the preview posts at the sighted road edge are
// never behind a car and the climb shows as the road tilting against the grid.
// Chosen by rendering the real episode-1 road flat (k = 130) and on the climb
// (k = 200): a camera more behind the cars made the two look the same. The
// extent is half the view height in world units: 11 units is about 110 m.
const EXTENT = 11;
const CAMERA_POSITION = [-6, 9, 26];
const CAMERA_TARGET = [8, 0, 0];
const ROAD_SEGMENTS = 719;        // one per episode step (design section 5)
const ROAD_LIFT = 0.04;           // ribbonGeometry's default lift
const CAR_LIFT = 0.085;           // as scene.mjs createScene: the car above the road point
const WHEEL_RADIUS = 0.62;        // supra()'s tyre radius; wheel phase = distance / radius
const DASH_EVERY_M = 20;
const DASH_LEN_M = 6;
const POST_Z = ROAD_W / 2 - 0.15; // the sighted car's road edge, outside its car
const POST_H = 1.4;
const GRID_STEP = 2;              // 20 m
// A horizontal reference under the cars, so a climb reads as a climb.
const GRID = { light: 0xc8cbbd, dark: 0x3b4743 };
// Preview posts: one hue (violet, neither red nor green, and apart from the
// blue and amber lane colours), pale at a flat road and deep at 16 %. On the
// dark theme it runs the other way, dim to bright, so steeper stays stronger.
const RAMP = {
  light: { low: 0xcfc4e8, high: 0x4b2e83, unknown: 0x9aa59e },
  dark: { low: 0x4a3f66, high: 0xd6c6ff, unknown: 0x5d6763 },
};
const LANE_OPACITY = 0.3;

function laneMaterial(colour) {
  const material = new THREE.MeshStandardMaterial({
    color: 0xffffff, transparent: true, opacity: LANE_OPACITY, depthWrite: false, side: THREE.DoubleSide, roughness: 0.9,
  });
  setColour(material, colour);
  return material;
}
function setColour(material, colour) {
  const text = typeof colour === 'string' ? colour.trim() : colour;
  if (text === '' || text === undefined || text === null) return;
  material.color.set(text);
}

/**
 * createChaseScene(host, episodeRoad, lanes) -> { update, setTheme, dispose }
 *
 *   episodeRoad  createEpisodeRoad(road) from agent-view.mjs
 *   lanes        { sighted, blind }: CSS colours (the --agent-* tokens)
 *   update({ distance_m, marks })  distance along the route in metres; marks is
 *                [{ s_m, grade_pct }], one per preview horizon, or [] / absent
 *                to hide the posts. A non-finite distance keeps the last one.
 *   setTheme(name, lanes)  'light' | 'dark', and the lane colours re-read
 *
 * `options.makeStage` exists for agent-scene.test.mjs, which runs under node
 * without WebGL; the page never passes it.
 */
export function createChaseScene(host, episodeRoad, lanes = { sighted: '#2f6db0', blind: '#b7791f' }, options = {}) {
  const makeStage = options.makeStage ?? stage;
  const view = makeStage(host, { extent: EXTENT, position: CAMERA_POSITION, target: CAMERA_TARGET });
  const { scene, render, paint } = view;
  // stage() stops touch scrolling on its canvas (the lab has orbit controls).
  // This camera is fixed, so a phone must still scroll past the view.
  if (view.renderer?.domElement?.style) view.renderer.domElement.style.touchAction = 'pan-y';
  const road = episodeRoad;
  const M = road.mPerUnit;
  let colours = { ...lanes };
  let theme = view.theme();

  // ---- the world: everything that slides under the still cars
  const world = new THREE.Group();
  world.name = 'agents-world';
  scene.add(world);
  const addRibbon = (name, width, offset, lift, material) => {
    const item = new THREE.Mesh(ribbonGeometry(road, 0, road.length, width, offset, lift, ROAD_SEGMENTS), material);
    item.name = name;
    item.receiveShadow = true;
    world.add(item);
    return item;
  };
  addRibbon('verge', ROAD_W + 1.2, 0, 0, paint.mat('verge', { side: THREE.DoubleSide }));
  addRibbon('road', ROAD_W, 0, ROAD_LIFT, paint.mat('road', { side: THREE.DoubleSide }));
  const lineMaterial = paint.mat('roadLine', { side: THREE.DoubleSide });
  for (const side of [-1, 1]) addRibbon(`edge-${side}`, 0.1, side * (ROAD_W / 2 - 0.2), 0.065, lineMaterial);
  const laneSighted = addRibbon('lane-sighted', LANE_W, CAR_OFFSET, 0.05, laneMaterial(colours.sighted));
  const laneBlind = addRibbon('lane-blind', LANE_W, -CAR_OFFSET, 0.05, laneMaterial(colours.blind));

  // Centre dashes every 20 m: one InstancedMesh, one draw call.
  const dashLength = DASH_LEN_M / M;
  const dashGeometry = new THREE.PlaneGeometry(dashLength, 0.14);
  dashGeometry.rotateX(-Math.PI / 2);
  const dashCount = Math.floor(road.length * M / DASH_EVERY_M) + 1;
  const dashes = new THREE.InstancedMesh(dashGeometry, lineMaterial, dashCount);
  dashes.name = 'centre-dashes';
  const place = new THREE.Matrix4();
  const quaternion = new THREE.Quaternion();
  const unit = new THREE.Vector3(1, 1, 1);
  const zAxis = new THREE.Vector3(0, 0, 1);
  for (let i = 0; i < dashCount; i++) {
    const { position: p, tangent: t } = road.atDistance(i * DASH_EVERY_M / M + dashLength / 2);
    quaternion.setFromAxisAngle(zAxis, Math.atan2(t[1], t[0]));
    place.compose(new THREE.Vector3(p[0], p[1] + 0.06, 0), quaternion, unit);
    dashes.setMatrixAt(i, place);
  }
  dashes.instanceMatrix.needsUpdate = true;
  world.add(dashes);

  // Preview posts, grown on demand to however many horizons the page sends
  // (engine_env.PREVIEW_S has four today; this file never assumes that).
  const posts = [];
  const poleMaterial = paint.mat('post');
  const poleGeometry = new THREE.CylinderGeometry(0.07, 0.07, POST_H, 8);
  const flagGeometry = new THREE.BoxGeometry(0.7, 0.4, 0.08);
  const post = i => {
    while (posts.length <= i) {
      const group = new THREE.Group();
      group.name = `preview-post-${posts.length}`;
      const pole = new THREE.Mesh(poleGeometry, poleMaterial);
      pole.position.y = POST_H / 2;
      const flag = new THREE.Mesh(flagGeometry, new THREE.MeshStandardMaterial({ roughness: 0.6 }));
      flag.name = 'flag';
      flag.position.set(0.35, POST_H - 0.2, 0);
      group.add(pole, flag);
      group.visible = false;
      world.add(group);
      posts.push({ group, flag });
    }
    return posts[i];
  };
  let shownMarks = [];
  const placePosts = () => {
    const ramp = RAMP[theme] ?? RAMP.light;
    const count = Math.max(posts.length, shownMarks.length);
    for (let i = 0; i < count; i++) {
      const { group, flag } = post(i);
      const mark = shownMarks[i];
      if (!mark || !Number.isFinite(mark.s_m)) { group.visible = false; continue; }
      const p = road.atDistance(mark.s_m / M).position;
      group.position.set(p[0], p[1] + ROAD_LIFT, POST_Z);
      const f = gradeRamp(mark.grade_pct);
      if (f === null) flag.material.color.set(ramp.unknown);
      else flag.material.color.set(ramp.low).lerp(new THREE.Color(ramp.high), f);
      group.visible = true;
    }
  };

  // ---- the grid: in the scene root, shifted by the fraction of a cell so its
  // lines stay put on the ground as the road slides.
  const gridPoints = [];
  for (let x = -40; x <= 60; x += GRID_STEP) gridPoints.push(x, 0, -20, x, 0, 20);
  for (let z = -20; z <= 20; z += GRID_STEP) gridPoints.push(-40, 0, z, 60, 0, z);
  const gridGeometry = new THREE.BufferGeometry();
  gridGeometry.setAttribute('position', new THREE.Float32BufferAttribute(gridPoints, 3));
  const gridMaterial = new THREE.LineBasicMaterial({ color: GRID[theme] ?? GRID.light, transparent: true, opacity: 0.8 });
  const grid = new THREE.LineSegments(gridGeometry, gridMaterial);
  grid.name = 'grid';
  scene.add(grid);

  // ---- the two cars: same s, same pitch, ±CAR_OFFSET across the road.
  const cars = [['car-sighted', CAR_OFFSET], ['car-blind', -CAR_OFFSET]].map(([name, z]) => {
    const made = supra(scene, paint);
    made.car.name = name;
    made.car.position.set(0, CAR_LIFT, z);
    return made;
  });

  const forward = new THREE.Vector3();
  const side = new THREE.Vector3();
  const normal = new THREE.Vector3();
  const orientation = new THREE.Matrix4();
  let distance = 0;          // world units along the route
  let disposed = false;

  function update({ distance_m, marks } = {}) {
    if (disposed) return;
    if (Number.isFinite(distance_m)) distance = Math.min(road.length, Math.max(0, distance_m / M));
    const { position: p, tangent } = road.atDistance(distance);
    world.position.set(-p[0], -p[1], 0);
    grid.position.set(-(((p[0] % GRID_STEP) + GRID_STEP) % GRID_STEP), -0.02, 0);
    forward.set(...tangent);
    side.crossVectors(forward, UP).normalize();
    normal.crossVectors(side, forward).normalize();
    orientation.makeBasis(forward, normal, side);
    for (const { car, wheels } of cars) {
      car.quaternion.setFromRotationMatrix(orientation);
      wheels.forEach(wheel => { wheel.rotation.z = -distance / WHEEL_RADIUS; });
    }
    shownMarks = Array.isArray(marks) ? marks : [];
    placePosts();
    render();
  }

  function setTheme(name, nextLanes) {
    if (disposed) return;
    view.setTheme(name);
    theme = view.theme();
    if (nextLanes) colours = { ...colours, ...nextLanes };
    setColour(laneSighted.material, colours.sighted);
    setColour(laneBlind.material, colours.blind);
    gridMaterial.color.set(GRID[theme] ?? GRID.light);
    placePosts();
    render();
  }

  update({ distance_m: 0 });
  return {
    update,
    setTheme,
    dispose() {
      if (disposed) return;
      disposed = true;
      view.dispose();
    },
  };
}
```

- [ ] **Step 12: Run to verify it passes, and that the lab is unchanged**

Run: `node --test app/static/sim/agent-scene.test.mjs 2>&1 | grep -E "^(✔|✖)|^ℹ (tests|pass|fail|skipped)"`

Expected: six `✔`, then `ℹ tests 6`, `ℹ pass 6`, `ℹ fail 0`, `ℹ skipped 0`.

Run: `node --test "app/static/sim/*.test.mjs" 2>&1 | grep -E "^ℹ (tests|pass|fail|skipped)"`

Expected: `ℹ tests 55`, `ℹ pass 55`, `ℹ fail 0`, `ℹ skipped 0`. That is the lab's 30, plus 7 from T7, 12 from agent-view and 6 from agent-scene; read the count from the run.

Run: `$PY -m app.test_simulation 2>&1 | tail -n 3`

Expected: `Ran 15 tests in …s`, then `OK`, unchanged.

- [ ] **Step 13: Commit**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
test "$(git branch --show-current)" = JMF-2340550-sep17 && echo "on JMF-2340550-sep17" || echo "WRONG BRANCH -- stop"
git add app/static/sim/agent-view.mjs app/static/sim/agent-view.test.mjs app/static/sim/agent-scene.mjs app/static/sim/agent-scene.test.mjs
git status --porcelain
OUT=$(mktemp -d)
node --test "app/static/sim/*.test.mjs" > "$OUT/node.txt" 2>&1; echo "node exit $?"
$PY -m app.test_simulation > "$OUT/sim.txt" 2>&1; echo "test_simulation exit $?"
$PY verify_docs.py > "$OUT/docs.txt" 2>&1; echo "verify_docs exit $?"; tail -n 1 "$OUT/docs.txt"
$PY -m app.test_replay > "$OUT/replay.txt" 2>&1; echo "test_replay exit $?"; tail -n 1 "$OUT/replay.txt"
```

Expected:
```
on JMF-2340550-sep17
A  app/static/sim/agent-scene.mjs
A  app/static/sim/agent-scene.test.mjs
A  app/static/sim/agent-view.mjs
A  app/static/sim/agent-view.test.mjs
node exit 0
test_simulation exit 0
verify_docs exit 0
All 67 checks pass (... figure mentions scanned in the documents).
test_replay exit 0
49 of 49 checks pass
```

If any exit code is not 0, stop and diagnose before committing.

```bash
{
cat <<'EOF'
Agent replay T8: agent-view (pure logic) and the chase view

agent-view.mjs: the road the lab's ribbonGeometry walks, built from the
Python route and exact at every vertex; episodeAt (one s for both cars);
the x3 profile; the preview marks at engine_env._preview's own indices;
gauges, held commands and the one-hue grade ramp; the play state that
waits at the computed edge instead of rewinding (playOrWait /
resumeIfStalled / settleDone, never resuming a viewer's pause);
appendFrames, which takes only the slice that starts where the held
frames end; parseEpisodeQuery for the M1 read-only picker.
agent-scene.mjs: two supra() cars at +-1.9 on lane tints, the road
sliding under a still orthographic camera (floating origin), preview
posts on the sighted edge coloured by the grade the sighted agent was
given; touch-action pan-y so a phone scrolls past it.
agent-scene.test.mjs runs it under node through an injected stage and
skips loudly without app/node_modules/three. CAR_HALF_WIDTH is 1.49,
measured (supra's hub ring reaches 1.486, not the design's 1.48).

EOF
echo 'node --test "app/static/sim/*.test.mjs":'
grep -E '^ℹ (tests|pass|fail|skipped)' "$OUT/node.txt" | sed 's/^/  /'
echo; echo 'python -m app.test_simulation:'
tail -n 3 "$OUT/sim.txt" | sed 's/^/  /'
echo; echo 'python verify_docs.py (last line):'
tail -n 1 "$OUT/docs.txt" | sed 's/^/  /'
echo; echo 'python -m app.test_replay:'
sed 's/^/  /' "$OUT/replay.txt"
printf '\nCo-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>\n'
} | git commit -F -
git show --stat --format='%h %s' HEAD | tail -n 6
git log -1 --format=%B | tail -n 1
```

Expected: `4 files changed`, all insertions: `agent-scene.mjs` (233 lines), `agent-scene.test.mjs` (160), `agent-view.mjs` (276) and `agent-view.test.mjs` (270). The last line of the message is `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.


---

### Task 9: Page shell: agents.html, agents.css, agents.mjs with URL picker, «احسب», polling, verdict box, badge, timeline and profile

Every command in Tasks 9 to 11 runs from the repository root in Git Bash. A Bash call starts with a fresh shell, so each command block opens with the plan's environment line.

**Files:**
- Create: `app/static/agents.html`
- Create: `app/static/sim/agents.css`
- Create: `app/static/sim/agents.mjs`
- Create: `app/static/sim/agents-page.test.mjs`
- Modify: `app/static/sim/agents-strings.mjs` (Task 7's file): two keys added at the end of each language block, Step 7
- Modify: `app/test_agents.py`: add `class PageTests` directly above the `if __name__ == "__main__":` block that Task 1 wrote
- Test: `app/test_agents.py` (`PageTests`), `app/static/sim/agents-page.test.mjs`

**Interfaces:**
- Consumes:
  - Task 6's route contract. `GET /api/agents/episode?runs&seed&ep&since&preempt` returns `{status, progress, steps, since, frames, device, versions}`. When `since == 0` it adds `meta` and `road`. A `busy` response adds `active`; an `error` response adds `message`. Other statuses are 404, 409 `{status: 'refused', problems}` and 503.
  - `meta` fields: `experiment, runs, prefix, protocol, seed, ep, episode{seed, weights, climb_start_s, grade}, dt, duration_s, steps, train_dt{sighted, blind}, agents[{tag, arm, budget_line, zip_sha, scored}], result_file, preview_s, act{lo, hi, slew, neutral_phys}, limits{turb_c, oil_c}, scenario{v_kmh, t_amb_c, p_baro_kpa}, verdict, fingerprint_taken`.
  - From `app.agent_api`: `install(app)`.
  - Task 1's road: `s_m/x_m/z_m/grade_pct/speed_kmh[720], length_m, rise_m, climb_start_s, p_baro_kpa, t_amb_c`.
  - Task 3's verdict: `{state, lines[{key, file, line, text}], missing, short{ar, en}, cells[{cell, gloss{ar, en}}]}`.
  - From Task 8's `agent-view.mjs`: `DT, PROFILE_VE, parseEpisodeQuery, appendFrames, createPlayState, playOrWait, pauseByUser, resumeIfStalled, settleDone, episodeAt, profilePoints, previewMarks, gradeRamp`.
  - From Task 8's `agent-scene.mjs`: its `RAMP` colours (low and high, light and dark). The profile's tick tokens copy them, and a node test pins that they agree.
  - From Task 7: the `AGENT_STRINGS` keys. From `i18n.mjs`: `t, LANGS, DEFAULT_LANG, resolveLang, applyTranslations`.
  - From `playback.mjs`: `PlaybackClock, formatTime`.
  - From the lab: `style.css` classes and tokens, and the pre-paint block, import map and icon symbols of `simulation.html:9-36`.
- Produces:
  - `agents.html` with every id listed for Task 9 in the skeleton, plus one more, `verdict-cells` (the list of quoted cells and their glosses). The nav reads `/simulation`, `/agents` (active), `/`, `/review`. The footer holds `#footer-index` (`agents.footer.index`, a 32 px target, with no handler in M1). Every reading in the pause panel's `<dl>` has its own `<dt>`.
  - `agents.css`: the lane tokens and the two ramp tokens (`--agent-ramp-lo`, `--agent-ramp-hi`) in all three theme blocks, and the layout at ≥ 1100 / < 1100 / ≤ 760 px.
  - `agents-strings.mjs` gains `agents.torque.heading` (no placeholder) and `agents.profile.km` (`{km}`) in both languages.
  - `agents.mjs`, which exports nothing. It holds `state` (`frames, road, meta, done, loadToken, play, device, versions, query`), `compute()`, `poll(token, preempt)`, `handle(status, body)`, `applyMeta(meta, road)`, `renderPicker/renderBadge/renderVerdict/renderDtCaption/drawProfile/renderProfileCaptions/moveProfile(at, showTicks)/renderTimeline/isWaiting/syncPlayButton/draw(time, force)/renderAll`, and `applyTheme/applyLanguage`. Task 10 extends `draw`, `renderAll`, `applyMeta` and `applyTheme`.
- Where this task differs from the skeleton (it follows the running prototype):
  1. The profile's car marker and preview ticks move here, in `moveProfile`. Task 10 only passes whether the sighted lane is still running.
  2. The scene strip's verdict text is filled by `renderVerdict` here. It is an honesty surface, so it must render even when Three.js never loads.
  3. `isWaiting()` counts two cases as waiting: agent-view's waiting flag, and a clock that stopped by itself at the computed edge while the viewer had not paused. Without the second case, the prototype's play button flickered to «تشغيل» at every edge at 16×.
  4. `#pick-note` repeats the episode line with its weights. The disabled select truncates it at 320 px.
  5. The `<details>` summary lists the cited `results/` files, so it needs no string key.
  6. `handle()` draws once when frame 0 first arrives. Paused at 0:00 the clock never moves, so the animation loop never redraws, and the panel and markers would read «—» for the whole first build (about 70 s).
  7. Design section 5 asks for "x in km", so the profile carries a km scale (0, 5, …, 25 km). It also asks for each preview marker "coloured by the grade read there", so the profile's four ticks use the chase view's ramp through `gradeRamp()`, not the lane colour.
  8. The review asked for the torque label key to be added in Task 7. Task 7 is written elsewhere in this plan, so this task adds that key and the km key to Task 7's file (Step 7). It is the only change this task makes to Task 7's work.

Prototype (26 Sep): these exact files ran in a scratch assembly of Tasks 1 to 10 (a copy of the tree with `runs*/` linked read-only), with the real `SAC.load` and `run_lanes` on CUDA, and were driven in headless Chrome:
- The profile drew 207 to 514 ms after «احسب», and «تحميل الشبكتين…» showed until the first frame at about 2.6 s.
- Before play, the panel already read «القرار المطبَّق من الثانية 0 إلى 1». The episode was ready after 70 to 100 s.
- The verdict box cited `results/C4_RESULT.txt:42, :29, :33-34, :48, :50-53, PREREGISTRATION_C4.md:41-43, :633-635`.
- The km scale read `0 كم … 25 كم`. At 02:10 the ticks showed two ramp colours: flat at +2 s and +5 s, climb at +15 s and +30 s.
- At 390 px `scrollWidth` was 390, and all four nav links fitted.

- [ ] **Step 1: Write the failing Python test**

Add this class to `app/test_agents.py`, directly above `if __name__ == "__main__":`. It uses the module's `ROOT` (Task 1) and imports `re`, FastAPI and `install` locally. It contains no `.write(` (test_read_only).

```python
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
```

- [ ] **Step 2: Write the failing node test**

Create `app/static/sim/agents-page.test.mjs`:

```js
// The /agents page shell, checked without a browser: every string the page
// names exists in BOTH languages, every t() call fills exactly the
// {placeholders} its string has, and the nav reads simulation, agents
// (active), monitor, review. A missing key renders as the key itself and a
// missing placeholder renders as "{percent}" -- both silently, on screen.
import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { STRINGS, LANGS } from './i18n.mjs';
import './agents-strings.mjs';
import { ACTIONS } from './agent-view.mjs';

const HTML = new URL('../agents.html', import.meta.url);
const PAGE = new URL('./agents.mjs', import.meta.url);

function read(url) {
  assert.ok(existsSync(url), `${url.pathname} does not exist`);
  return readFileSync(url, 'utf8');
}

const has = key => LANGS.every(lang => Object.prototype.hasOwnProperty.call(STRINGS[lang], key));
const slots = text => new Set([...text.matchAll(/\{(\w+)\}/g)].map(m => m[1]));

// Top-level property names of the object literal that opens at src[start].
// A scanner rather than a regex, because a value can hold calls, commas,
// brackets and strings of its own.
function objectKeys(src, start) {
  const parts = [];
  let depth = 0;
  let quote = null;
  let part = '';
  for (let i = start; i < src.length; i++) {
    const c = src[i];
    if (quote) {
      part += c;
      if (c === '\\') { part += src[i + 1]; i += 1; } else if (c === quote) quote = null;
      continue;
    }
    if (c === "'" || c === '"' || c === '`') { quote = c; part += c; continue; }
    if ('({['.includes(c)) { depth += 1; if (depth === 1) continue; }
    if (')}]'.includes(c)) { depth -= 1; if (depth === 0) { parts.push(part); break; } }
    if (c === ',' && depth === 1) { parts.push(part); part = ''; continue; }
    part += c;
  }
  return parts.map(p => p.trim()).filter(Boolean)
    .map(p => (p.match(/^([A-Za-z_$][\w$]*)/) || [])[1]);
}

// Every t(currentLang, '<literal key>' ...) call and the names it passes.
function tCalls(src) {
  const out = [];
  const head = /\bt\(\s*currentLang\s*,\s*'([^']+)'\s*/g;
  let m;
  while ((m = head.exec(src))) {
    let i = head.lastIndex;
    let names = [];
    if (src[i] === ',') {
      i += 1;
      while (/\s/.test(src[i])) i += 1;
      if (src[i] === '{') names = objectKeys(src, i);
    }
    out.push({ key: m[1], names });
  }
  return out;
}

test('every key agents.html names exists in both languages and carries no placeholder', () => {
  const html = read(HTML);
  const keys = [...new Set([...html.matchAll(/data-i18n(?:-aria|-title)?="([^"]+)"/g)].map(m => m[1]))];
  assert.ok(keys.length > 20, 'the key scan found almost nothing; the pattern has drifted');
  assert.deepEqual(keys.filter(k => !has(k)), []);
  // Markup has no way to fill a {slot}; a key with one would show it raw.
  assert.deepEqual(keys.filter(k => LANGS.some(lang => slots(STRINGS[lang][k]).size)), []);
});

test('every key agents.mjs names exists in both languages', () => {
  const src = read(PAGE);
  const calls = tCalls(src);
  assert.ok(calls.length > 20, 'the t() scan found almost nothing; the pattern has drifted');
  const literals = [...src.matchAll(/'((?:agents|nav|transport|theme|lang|rate|seed)\.[\w.]+)'/g)]
    .map(m => m[1]).filter(k => !k.endsWith('.mjs'));
  const keys = new Set([...calls.map(c => c.key), ...literals, ...ACTIONS.map(a => a.label)]);
  assert.deepEqual([...keys].filter(k => !has(k)), []);
});

test('each t() call fills exactly the placeholders of its string, in both languages', () => {
  const problems = [];
  for (const { key, names } of tCalls(read(PAGE))) {
    if (!has(key)) continue;   // reported by the test above
    const given = new Set(names);
    for (const lang of LANGS) {
      const want = slots(STRINGS[lang][key]);
      for (const s of want) if (!given.has(s)) problems.push(`${key} [${lang}] is never given {${s}}`);
      for (const g of given) if (!want.has(g)) problems.push(`${key} [${lang}] has no {${g}}`);
    }
  }
  assert.deepEqual(problems, []);
});

test('the nav reads simulation, agents (active), monitor, review', () => {
  const nav = read(HTML).match(/<nav[^>]*>([\s\S]*?)<\/nav>/);
  assert.ok(nav, 'agents.html has no <nav>');
  const links = [...nav[1].matchAll(/<a\b([^>]*)>/g)].map(m => m[1]);
  const attr = (a, name) => (a.match(new RegExp(`${name}="([^"]+)"`)) || [])[1];
  assert.deepEqual(links.map(a => attr(a, 'href')), ['/simulation', '/agents', '/', '/review']);
  assert.deepEqual(links.map(a => attr(a, 'data-i18n')),
    ['nav.simulation', 'nav.agents', 'nav.monitor', 'nav.review']);
  assert.deepEqual(links.map(a => /\bclass="[^"]*\bactive\b/.test(a)), [false, true, false, false]);
});

test('the honesty lines are in the markup itself, not only written by script', () => {
  const html = read(HTML);
  for (const [id, key] of [
    ['illustration-note', 'agents.illustration'],
    ['same-place-legend', 'agents.legend.same_place'],
    ['chase-caption', 'agents.scene.slope'],
    ['model-caveat', 'seed.model_output'],
    ['footer-index', 'agents.footer.index'],
  ]) {
    const tag = html.match(new RegExp(`<[^>]*\\bid="${id}"[^>]*>`));
    assert.ok(tag, `#${id} is missing`);
    assert.ok(tag[0].includes(`data-i18n="${key}"`), `#${id} must carry data-i18n="${key}"`);
  }
  assert.match(html, /\bid="sim-badge"/);
});

test('every reading in the pause panel carries its own label', () => {
  const dl = read(HTML).match(/<dl class="car-readings">([\s\S]*?)<\/dl>/);
  assert.ok(dl, 'agents.html has no <dl class="car-readings">');
  const groups = [...dl[1].matchAll(/<div>([\s\S]*?)<\/div>/g)].map(m => m[1]);
  assert.equal(groups.length, 3, 'damage, turbine and torque');
  for (const group of groups) {
    assert.match(group, /^<dt\b[^>]*data-i18n="[^"]+"[^>]*>[^<]*<\/dt><dd\b/, `a reading without a label: ${group.slice(0, 60)}`);
  }
});

test('the profile ticks and the chase posts share one ramp, in both themes', () => {
  const css = read(new URL('./agents.css', import.meta.url));
  const scene = read(new URL('./agent-scene.mjs', import.meta.url));
  const ramp = scene.match(/const RAMP = \{[\s\S]*?\n\};/);
  assert.ok(ramp, 'agent-scene.mjs has no RAMP table');
  const tokens = [...css.matchAll(/--agent-ramp-(?:lo|hi):#([0-9a-f]{6})/g)].map(m => m[1]);
  assert.equal(tokens.length, 6, 'lo and hi in each of the three theme blocks');
  for (const hex of tokens) assert.ok(ramp[0].includes(`0x${hex}`), `#${hex} is not in agent-scene.mjs's RAMP`);
});
```

- [ ] **Step 3: Run both to verify they fail**

Run:
```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
$PY -m unittest app.test_agents.PageTests -v
node --test app/static/sim/agents-page.test.mjs
```
Expected:
- Python: `FAIL: test_every_string_names_its_language` with `AssertionError: False is not true : sim/agents.mjs does not exist`, and `FAIL: test_page_assets_ids` with `AssertionError: False is not true : agents.html does not exist`. Then `Ran 2 tests` and `FAILED (failures=2)`.
- Node: `ℹ tests 7`, `ℹ fail 7`. Each failure reads `AssertionError [ERR_ASSERTION]: /C:/.../app/static/agents.html does not exist`, or the same for `.../sim/agents.mjs` or `.../sim/agents.css`.

- [ ] **Step 4: Create `app/static/agents.html`**

```html
<!doctype html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="theme-color" content="#f4f3ed">
  <title data-i18n="agents.page.title">الوكلاء على الطريق — GRAD</title>
  <link rel="stylesheet" href="/static/sim/style.css">
  <link rel="stylesheet" href="/static/sim/agents.css">
  <script>
    // The lab's own pre-paint block, unchanged: the same two keys, wrapped
    // because localStorage throws in private mode. Nothing else is stored.
    try {
      var s = localStorage.getItem('grad.sim.theme');
      if (s === 'dark' || s === 'light') document.documentElement.dataset.theme = s;
      var l = localStorage.getItem('grad.sim.lang');
      if (l === 'en' || l === 'ar') {
        document.documentElement.lang = l;
        document.documentElement.dir = l === 'en' ? 'ltr' : 'rtl';
      }
    } catch (e) { /* no stored preference is not an error */ }
  </script>
  <script type="importmap">{"imports":{"three":"/static/vendor/three/three.module.js","three/addons/":"/static/vendor/three/addons/"}}</script>
</head>
<body>
  <svg class="icon-library" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <symbol id="i-play" viewBox="0 0 24 24"><path d="m9 5 11 7-11 7Z"/></symbol>
    <symbol id="i-pause" viewBox="0 0 24 24"><path d="M8 5v14M16 5v14"/></symbol>
    <symbol id="i-reset" viewBox="0 0 24 24"><path d="M4 10a8 8 0 1 1 1 7M4 4v6h6"/></symbol>
    <symbol id="i-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M4.9 4.9l1.5 1.5m11.2 11.2 1.5 1.5M19.1 4.9l-1.5 1.5M6.4 17.6l-1.5 1.5"/></symbol>
    <symbol id="i-moon" viewBox="0 0 24 24"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z"/></symbol>
  </svg>
  <header class="topbar">
    <a href="/simulation" class="brand" data-i18n-aria="brand.aria" aria-label="مختبر GRAD"><span class="brand-mark">G<span>╱</span></span><div><strong dir="ltr">GRAD<span class="brand-point">.</span></strong><small data-i18n="brand.tagline">مختبر الأنظمة الهندسية</small></div></a>
    <nav data-i18n-aria="nav.aria" aria-label="التنقل الرئيسي"><a href="/simulation" data-i18n="nav.simulation">مختبر الرحلة</a><a class="active" href="/agents" aria-current="page" data-i18n="nav.agents">الوكلاء</a><a href="/" data-i18n="nav.monitor">المراقبة</a><a href="/review" data-i18n="nav.review">مراجعة التنبيهات</a></nav>
    <div class="topbar-tools">
      <button id="theme-toggle" type="button" data-i18n-title="theme.to_dark" data-i18n-aria="theme.aria" aria-label="تبديل الوضع الليلي" title="الوضع الليلي"><svg><use href="#i-moon"/></svg></button>
      <button id="lang-toggle" type="button" data-i18n-title="lang.switch_to_english" data-i18n-aria="lang.aria" aria-label="تغيير اللغة" title="English"><span dir="ltr">EN</span></button>
    </div>
  </header>
  <main class="agents-main">
    <section class="page-intro agents-intro">
      <div><p class="eyebrow"><span class="small-rule"></span><span data-i18n="intro.eyebrow">المحرك · الطريق · الزمن</span></p><h1><span data-i18n="agents.intro.heading">ماذا قرّر كل وكيل، ثانية بثانية</span><span>.</span></h1><p class="intro-note" data-i18n="agents.intro.note">حلقة اختبار مجمّدة واحدة لزوج واحد.</p></div>
      <p id="sim-badge" class="sim-badge" role="note" data-i18n="agents.badge.short">محاكاة</p>
    </section>
    <div id="error" class="error" role="alert" hidden></div>
    <section class="agents-layout">
      <div class="agents-col agents-col-main">
        <article class="chase-panel">
          <div class="chase-view">
            <div id="chase" class="chase" role="img" data-i18n-aria="agents.legend.same_place" aria-label="السيارتان في المكان نفسه دائماً"></div>
            <div id="scene-strip" class="scene-strip"><span id="strip-verdict"></span><span class="strip-badge" data-i18n="agents.badge.short">محاكاة</span></div>
            <div class="lane-labels"><span id="lane-sighted-label" class="lane-label sighted"></span><span id="lane-blind-label" class="lane-label blind"></span></div>
            <p id="scene-prompt" class="scene-prompt" data-i18n="agents.prompt">اختر تجربة وزوجاً وحلقة ثم اضغط احسب</p>
            <div id="loading" class="loading-card" role="status" aria-live="polite" hidden><span class="loading-indicator"></span><div><strong id="load-title"></strong><p id="load-detail" dir="ltr"></p><progress id="load-progress" max="1" value="0"></progress></div></div>
          </div>
          <div class="chase-captions"><span id="same-place-legend" data-i18n="agents.legend.same_place">السيارتان في المكان نفسه دائماً</span><span id="chase-caption" data-i18n="agents.scene.slope">الميل غير مضخّم · السيارة ليست بمقياسها</span></div>
        </article>
        <section class="transport agents-transport" data-i18n-aria="transport.aria" aria-label="التحكم في إعادة التشغيل">
          <div class="transport-buttons"><button id="play" class="play-button" type="button" disabled data-i18n-aria="transport.play_aria" aria-label="تشغيل"><svg><use href="#i-play"/></svg><span data-i18n="transport.play">تشغيل</span></button><button id="restart" class="icon-button" type="button" disabled data-i18n-aria="transport.restart_aria" aria-label="إعادة من البداية"><svg><use href="#i-reset"/></svg></button></div>
          <div class="timeline-block">
            <div class="time-labels"><span><b id="current-time" dir="ltr">00:00</b><span class="time-separator"> / </span><span id="duration" dir="ltr">00:00</span></span><span id="computed-note" class="computed-note"></span></div>
            <div class="seek-wrap"><div class="computed-track" aria-hidden="true"><i id="computed-fill"></i><i id="climb-tick" hidden></i></div><input id="seek" type="range" min="0" max="1" value="0" step="0.05" disabled data-i18n-aria="transport.seek_aria" aria-label="موضع إعادة التشغيل"></div>
            <p id="dt-caption" class="dt-caption"></p>
          </div>
          <div class="rate-control"><label for="rate" data-i18n="rate.label">سرعة العرض</label><select id="rate" data-i18n-aria="rate.aria" aria-label="سرعة العرض"><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="2">2×</option><option value="4">4×</option><option value="8">8×</option><option value="16">16×</option></select></div>
        </section>
        <article class="profile-panel">
          <div id="profile" class="profile" role="img"></div>
          <div class="profile-captions"><span id="profile-ve"></span><span id="rise-caption"></span></div>
        </article>
      </div>
      <aside class="agents-col agents-col-side">
        <section class="picker-panel">
          <div class="pick-row"><label for="pick-experiment" data-i18n="agents.pick.experiment">التجربة</label><select id="pick-experiment" disabled></select></div>
          <div class="pick-row"><label for="pick-pair" data-i18n="agents.pick.pair">الزوج</label><select id="pick-pair" disabled></select></div>
          <div class="pick-row"><label for="pick-episode" data-i18n="agents.pick.episode">الحلقة</label><select id="pick-episode" disabled></select></div>
          <div id="pick-note" class="pick-note"></div>
          <button id="compute" class="play-button compute-button" type="button" disabled data-i18n-aria="agents.compute_aria" aria-label="احسب"><span data-i18n="agents.compute">احسب</span></button>
        </section>
        <section id="verdict" class="verdict-panel" data-state="waiting">
          <h2 data-i18n="agents.verdict.heading">الحكم المسجَّل مسبقاً</h2>
          <p id="verdict-short" class="verdict-short">—</p>
          <ul id="verdict-cells" class="verdict-cells"></ul>
          <details id="verdict-more"><summary>—</summary><div id="verdict-lines"></div></details>
          <ul id="verdict-scored" class="verdict-scored"></ul>
          <p id="illustration-note" class="illustration-note" data-i18n="agents.illustration">حلقة واحدة لزوج واحد مثال توضيحي، لا نتيجة.</p>
        </section>
        <section class="pause-panel">
          <div class="panel-heading"><h2 id="pause-heading">—</h2><span id="grade-now" class="sample-tag"></span></div>
          <p id="weights-line" class="weights-line"></p>
          <div id="actions" class="actions"></div>
          <p id="seen-sighted" class="seen sighted"></p>
          <p id="seen-blind" class="seen blind"></p>
          <dl class="car-readings">
            <div><dt id="damage-caption" data-i18n="agents.damage.caption">وحدات ضرر، في هذه الحلقة فقط حتى هذه اللحظة</dt><dd><span class="sighted"><i class="lane-dot"></i><b id="damage-sighted" dir="ltr">—</b></span><span class="blind"><i class="lane-dot"></i><b id="damage-blind" dir="ltr">—</b></span></dd></div>
            <div><dt data-i18n="agents.turbine.label">غلاف التيربو مقابل العتبة</dt><dd><span class="sighted"><i class="lane-dot"></i><b id="turb-sighted" dir="ltr">—</b></span><span class="blind"><i class="lane-dot"></i><b id="turb-blind" dir="ltr">—</b></span></dd></div>
            <div><dt data-i18n="agents.torque.heading">العزم المُسلَّم مقابل المطلوب</dt><dd class="torque-row"><span class="sighted"><i class="lane-dot"></i><span id="torque-sighted">—</span></span><span class="blind"><i class="lane-dot"></i><span id="torque-blind">—</span></span></dd></div>
          </dl>
          <p id="model-caveat" class="seed-note" data-i18n="seed.model_output">حرارة التيربو تقدير من النموذج، وليست قراءة حساس.</p>
          <p id="lane-stopped" class="lane-stopped" hidden></p>
          <p id="device-line" class="device-line"></p>
          <p id="fingerprint-taken" class="device-line"></p>
        </section>
      </aside>
    </section>
    <footer><span dir="ltr" data-i18n="footer.brand">GRAD / ENGINEERING REPLAY LAB</span><span data-i18n="footer.note">مشروع تخرّج · محرك B58 · عرض علمي استكشافي</span><span id="footer-index" class="footer-index" dir="ltr" data-i18n="agents.footer.index">02 — AGENTS</span></footer>
  </main>
  <noscript><p data-i18n="noscript">يحتاج المختبر إلى JavaScript.</p></noscript>
  <script type="module" src="/static/sim/agents.mjs"></script>
</body>
</html>
```

- [ ] **Step 5: Create `app/static/sim/agents.css`**

```css
/* The agent replay page (/agents). Loaded AFTER the lab's style.css: the
   tokens, the topbar, the transport and the loading card are the lab's own,
   and only what this page adds lives here.

   LANE COLOURS. Blue is the agent that sees the road ahead, amber the one that
   does not. NEVER red or green: on this page those would read as a verdict on
   the cars, and the page shows no winner. The three blocks below are the same
   list three times, exactly like style.css's palette -- edit all three.
   The two ramp tokens are agent-scene.mjs's RAMP (low and high), so the
   profile's preview ticks and the chase view's posts share one scale;
   agents-page.test.mjs pins that they agree. */
:root{--agent-sighted:#2f6db0;--agent-blind:#b5761c;--agent-hatch:#d4d9cc;--agent-ramp-lo:#cfc4e8;--agent-ramp-hi:#4b2e83}
:root[data-theme="dark"]{--agent-sighted:#72a9e6;--agent-blind:#e2a54c;--agent-hatch:#3a4345;--agent-ramp-lo:#4a3f66;--agent-ramp-hi:#d6c6ff}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]){--agent-sighted:#72a9e6;--agent-blind:#e2a54c;--agent-hatch:#3a4345;--agent-ramp-lo:#4a3f66;--agent-ramp-hi:#d6c6ff}}

.agents-intro{align-items:flex-end}
.sim-badge{max-width:560px;margin:0;padding:9px 12px;border:1px dashed var(--estimated);border-radius:9px;background:var(--estimated-bg);color:var(--estimated-ink);font-size:11px;line-height:1.75}

/* >= 1100 px: main column (chase, timeline, profile) | side column (picker,
   verdict, pause panel). The grid runs ltr and its children rtl, exactly as the
   lab's .lab-layout does, so the side column sits at the reading start. */
.agents-layout{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(320px,1fr);gap:17px;direction:ltr;align-items:start;margin-bottom:17px}
.agents-layout>*{direction:rtl;min-width:0}
.agents-col{display:flex;flex-direction:column;gap:17px;min-width:0}
html[dir=ltr] .agents-layout>*{direction:ltr}

/* chase view */
.chase-panel{background:var(--world-bg);border:1px solid var(--world-border);border-radius:15px;overflow:hidden}
.chase-view{position:relative;aspect-ratio:16/9}
.chase{position:absolute;inset:0;direction:ltr}
.chase canvas{display:block;width:100%;height:100%}
.chase .webgl-error{padding:16% 24px;margin:0;font-size:12px}
.scene-strip{position:absolute;z-index:2;top:12px;inset-inline:12px;display:flex;flex-wrap:wrap;gap:6px;align-items:center;pointer-events:none}
.scene-strip>span{background:var(--overlay-strong-bg);border:1px solid var(--overlay-border);border-radius:6px;padding:3px 9px;font-size:10px;line-height:1.6}
#strip-verdict:empty{display:none}
.strip-badge{font-weight:650;color:var(--estimated-ink)}
.lane-labels{position:absolute;z-index:2;bottom:12px;inset-inline-start:12px;display:flex;flex-direction:column;align-items:flex-start;gap:5px;pointer-events:none}
.lane-label{display:inline-flex;align-items:center;gap:6px;padding:2px 9px;border-radius:6px;font-size:10px;background:var(--overlay-strong-bg);border:1px solid var(--overlay-border)}
.lane-label:empty{display:none}
.lane-label::before,.lane-dot{content:"";display:inline-block;width:8px;height:8px;border-radius:50%;flex-shrink:0}
.lane-label.sighted::before,.sighted>.lane-dot,.sighted .lane-dot{background:var(--agent-sighted)}
.lane-label.blind::before,.blind>.lane-dot,.blind .lane-dot{background:var(--agent-blind)}
.scene-prompt{position:absolute;z-index:2;inset:0;margin:auto;height:max-content;width:max-content;max-width:80%;text-align:center;padding:12px 16px;background:var(--overlay-strong-bg);border:1px solid var(--overlay-border);border-radius:10px;font-size:12px}
.chase-view .loading-card{bottom:12px;left:12px;right:12px;margin-right:auto}
.chase-captions{display:flex;flex-wrap:wrap;justify-content:space-between;gap:6px 16px;padding:9px 14px;font-size:9px;color:var(--muted);border-top:1px solid var(--world-border)}
#chase-caption{font-weight:600;color:var(--ink-2)}

/* timeline: the computed part is filled, the rest hatched, the climb ticked */
.agents-transport{margin:0}
.computed-note{font-size:9px;color:var(--muted);direction:rtl}
.computed-track{position:absolute;left:6px;right:6px;top:14px;height:3px;border-radius:2px;background:repeating-linear-gradient(135deg,var(--agent-hatch) 0 3px,transparent 3px 6px);pointer-events:none}
#computed-fill{position:absolute;top:0;bottom:0;left:0;width:0;border-radius:2px;background:var(--track-fill)}
#climb-tick{position:absolute;top:-4px;width:2px;height:11px;margin-left:-1px;background:var(--estimated)}
.dt-caption{margin:7px 0 0;font-size:9px;line-height:1.7;color:var(--muted);direction:rtl}
.dt-caption:empty{display:none}
html[dir=ltr] .computed-note,html[dir=ltr] .dt-caption{direction:ltr}

/* whole-route profile. preserveAspectRatio "meet" keeps the stated x3 true on
   screen: the SVG is never stretched along one axis only. */
.profile-panel{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:14px 16px 10px;box-shadow:var(--shadow)}
.profile{position:relative;direction:ltr;min-height:40px}
.profile svg{display:block;width:100%;height:auto;overflow:visible;stroke:none}
.profile-ground{fill:var(--world-bg)}
.profile-road{fill:none;stroke:var(--ink-2);stroke-width:1.6px;vector-effect:non-scaling-stroke}
.profile-climb{stroke:var(--estimated);stroke-width:1px;stroke-dasharray:4 3;vector-effect:non-scaling-stroke}
.profile-tick{stroke:var(--agent-ramp-hi);stroke-width:3px;vector-effect:non-scaling-stroke}
.profile-km-tick{stroke:var(--muted-2);stroke-width:1px;vector-effect:non-scaling-stroke}
.profile-axis{position:relative;height:14px;margin-top:2px}
.profile-km{position:absolute;top:0;transform:translateX(-50%);font-size:8px;line-height:14px;color:var(--muted);white-space:nowrap;direction:rtl}
.profile-km.start{transform:none}
.profile-km.end{transform:translateX(-100%)}
html[dir=ltr] .profile-km{direction:ltr}
.profile-car{fill:var(--ink);stroke:var(--paper);stroke-width:2px;vector-effect:non-scaling-stroke}
.profile-climb-label{position:absolute;top:0;direction:rtl;padding:0 6px 0 0;transform:translateX(-100%);font-size:9px;color:var(--estimated-ink);white-space:nowrap}
.profile-climb-label.flip{padding:0 0 0 6px;transform:none}
html[dir=ltr] .profile-climb-label{direction:ltr}
.profile-captions{display:flex;flex-wrap:wrap;justify-content:space-between;gap:4px 14px;margin-top:6px;font-size:9px;color:var(--muted)}
#profile-ve{font-weight:600;color:var(--ink-2)}

/* side column */
.picker-panel,.verdict-panel,.pause-panel{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:16px 18px;box-shadow:var(--shadow)}
.pick-row{display:grid;grid-template-columns:72px minmax(0,1fr);align-items:center;gap:10px;margin-bottom:8px}
.pick-row label{font-size:10px;color:var(--muted)}
.pick-row select{width:100%;min-width:0;background:var(--field-bg);border:1px solid var(--line);border-radius:8px;padding:8px 10px;font-size:11px}
.pick-row select:disabled{opacity:1;cursor:default;color:var(--ink)}
.pick-note{display:flex;flex-direction:column;gap:4px;margin:4px 0 12px;font-size:10px;line-height:1.7;color:var(--muted)}
.pick-note:empty{display:none}
.pick-note>span{display:flex;align-items:baseline;gap:6px}
.compute-button{width:100%}
#compute:disabled{cursor:not-allowed}

.verdict-panel h2{margin-bottom:8px}
.verdict-short{margin:0 0 8px;font-size:13px;font-weight:650;line-height:1.75}
.verdict-panel[data-state="missing"] .verdict-short,.verdict-panel[data-state="none"] .verdict-short{color:var(--error-ink)}
.verdict-cells{list-style:none;margin:0 0 10px;padding:0;display:flex;flex-direction:column;gap:6px}
.verdict-cells:empty{display:none}
.verdict-cells li{display:flex;flex-direction:column;gap:2px;padding:7px 9px;background:var(--seed-bg);border-radius:6px}
.verdict-cells .cell{font:600 10px/1.5 Consolas,monospace;letter-spacing:.4px;text-align:left}
.verdict-cells .gloss{font-size:11px;line-height:1.8;color:var(--ink-2)}
#verdict-more summary{cursor:pointer;font:10px/1.6 Consolas,monospace;color:var(--green-bright);direction:ltr;text-align:left}
.quote{margin:8px 0 0;padding:8px 10px;border-left:2px solid var(--rule);background:var(--field-bg);border-radius:4px;direction:ltr}
.quote pre{margin:0;white-space:pre-wrap;overflow-wrap:anywhere;font:10px/1.65 Consolas,monospace;color:var(--code-ink);text-align:left}
.quote figcaption{margin-top:4px;font:9px/1.5 Consolas,monospace;color:var(--muted);text-align:left}
.verdict-scored{list-style:none;margin:10px 0 0;padding:0;display:flex;flex-direction:column;gap:3px;font-size:10px;color:var(--muted)}
.verdict-scored:empty{display:none}
.verdict-scored li{display:flex;flex-wrap:wrap;align-items:center;gap:6px}
.verdict-scored code{font:9px Consolas,monospace;color:var(--code-ink)}
.illustration-note{margin:10px 0 0;padding:8px 10px;border-radius:6px;background:var(--warn-bg);color:var(--warn-ink);font-size:11px;line-height:1.8}

.error ul{margin:6px 0;padding-inline-start:18px;font:10px/1.6 Consolas,monospace}
.retry-button{margin-inline-start:12px;border:1px solid currentColor;background:transparent;border-radius:6px;padding:3px 10px;font-size:11px;color:inherit}
.footer-index{display:inline-flex;align-items:center;min-height:32px;min-width:32px;padding:0 8px}

/* < 1100 px: one column, in reading order badge, picker, verdict, chase,
   timeline, profile, pause panel. The two column wrappers dissolve so their
   children can be ordered together. */
@media(max-width:1099px){
.agents-layout{display:flex;flex-direction:column;gap:12px}
.agents-col{display:contents}
.picker-panel{order:1}.verdict-panel{order:2}.chase-panel{order:3}.agents-transport{order:4}.profile-panel{order:5}.pause-panel{order:6}
}
/* < 760 px: phone. The lab hides its last nav link here; this page has four
   and needs all of them, so the nav takes a row of its own instead. */
@media(max-width:760px){
.topbar{height:auto;flex-wrap:wrap;row-gap:0;padding:10px 16px 0}
.topbar nav{order:3;width:100%;height:40px;gap:16px}
.topbar nav a:last-child{display:flex}
main.agents-main{padding:18px 16px 0}
.agents-intro{align-items:stretch}
.chase-view{aspect-ratio:4/3}
.pick-row{grid-template-columns:1fr;gap:4px}
.scene-strip>span{font-size:9px}
}
```

- [ ] **Step 6: Create `app/static/sim/agents.mjs`**

```js
// The agent replay page (/agents): wiring, polling, the clock, the verdict box,
// the badge, the timeline and the whole-route profile.
//
// PRESENTATION ONLY. Every number drawn here arrives in a frame or a road that
// app/agent_trace.py computed on the server, and app/test_agents.py proves
// those frames are evaluate.run_episode's own episode (==, no tolerance). This
// file never does engine physics, never computes a statistic and never
// computes a difference between the two cars: the page shows no winner.
//
// Lane 0 is always the sighted agent and lane 1 the blind one, in run_lanes
// order and in meta.agents order.
//
// M1: the picker is READ-ONLY. It shows ?runs=&seed=&ep= from the address and
// nothing computes until «احسب» is pressed. Nothing is stored in the browser
// except the lab's own theme and language preferences.
import './agents-strings.mjs';
import { t, LANGS, DEFAULT_LANG, resolveLang, applyTranslations } from './i18n.mjs';
import { PlaybackClock, formatTime } from './playback.mjs';
import {
  DT, PROFILE_VE, parseEpisodeQuery, appendFrames, createPlayState, playOrWait,
  pauseByUser, resumeIfStalled, settleDone, episodeAt, profilePoints, previewMarks, gradeRamp,
} from './agent-view.mjs';

const $ = id => document.getElementById(id);
const POLL_MS = 400;
const THEMES = ['light', 'dark'];
const STORE = { theme: 'grad.sim.theme', lang: 'grad.sim.lang' };
const EM_DASH = '—';
const LANES = ['sighted', 'blind'];
const LANE_LABEL = ['agents.car.sighted', 'agents.car.blind'];
const PROFILE_W = 1000;
const PROFILE_PAD = 24;
const KM_STEP = 5;   // the profile's horizontal scale: a label every 5 km

let currentLang = DEFAULT_LANG;

const state = {
  query: parseEpisodeQuery(window.location.search),
  frames: [],
  road: null,
  meta: null,
  metaKey: null,
  done: false,
  loadToken: 0,
  polling: null,
  play: createPlayState(new PlaybackClock(0)),
  device: null,
  versions: null,
  load: null,      // { text: () => string, progress } for the loading card
  error: null,     // { text: () => string, items, retry } for #error
  profile: null,   // { sx, ve, height, car, ticks } once the road is drawn
  lastK: -2,
  drawnTime: -1,
  wasPlaying: false,
};

// ---------------------------------------------------------------- helpers
function remember(key, value) {
  try { localStorage.setItem(key, value); } catch (e) { /* a preference is a convenience */ }
}
function recall(key, allowed, fallback) {
  try {
    const v = localStorage.getItem(key);
    return allowed.includes(v) ? v : fallback;
  } catch (e) { return fallback; }
}
function setText(node, value) {
  if (node && node.textContent !== value) node.textContent = value;
}
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
const num = v => (typeof v === 'number' && Number.isFinite(v) ? v : null);
function fmt(v, digits) {
  const n = num(v);
  return n === null ? EM_DASH : n.toFixed(digits);
}
function fmtInt(v) {
  const n = num(v);
  return n === null ? EM_DASH : String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const keyOf = q => `${q.runs}/${q.seed}/${q.ep}`;

// fingerprint.format_budget writes "trained N steps of M requested, ..."; the
// page shows N and falls back to the whole line rather than guess.
function budgetSteps(line) {
  const m = /^trained (\d+) steps/.exec(line || '');
  return m ? fmtInt(Number(m[1])) : (line || EM_DASH);
}

// ---------------------------------------------------------------- status
// Both hold a function, not a string, so a language switch re-renders them.
function showLoad(text, progress = 0) {
  state.load = text ? { text, progress } : null;
  renderLoad();
}
function renderLoad() {
  const card = $('loading');
  if (!card) return;
  card.hidden = !state.load;
  if (!state.load) return;
  setText($('load-title'), state.load.text());
  setText($('load-detail'), state.query ? keyOf(state.query) : '');
  const bar = $('load-progress');
  if (bar) bar.value = Math.max(0, Math.min(1, state.load.progress || 0));
}
function showError(text, { retry = null, items = [] } = {}) {
  state.error = text ? { text, retry, items } : null;
  renderError();
}
function renderError() {
  const box = $('error');
  if (!box) return;
  box.textContent = '';
  box.hidden = !state.error;
  if (!state.error) return;
  box.appendChild(el('span', '', state.error.text()));
  if (state.error.items.length) {
    const list = el('ul');
    for (const item of state.error.items) {
      const li = el('li', '', String(item));
      li.dir = 'ltr';
      list.appendChild(li);
    }
    box.appendChild(list);
  }
  const retry = state.error.retry;
  if (retry) {
    const again = el('button', 'retry-button', t(currentLang, 'agents.load.retry'));
    again.type = 'button';
    again.addEventListener('click', () => { again.disabled = true; retry(); }, { once: true });
    box.appendChild(again);
  }
}

// ---------------------------------------------------------------- compute
function setControlsEnabled(on) {
  for (const id of ['play', 'restart', 'seek']) {
    const node = $(id);
    if (node) node.disabled = !on;
  }
}

function episodeUrl(since, preempt) {
  const q = state.query;
  const params = new URLSearchParams({
    runs: q.runs, seed: String(q.seed), ep: String(q.ep), since: String(since),
  });
  if (preempt) params.set('preempt', '1');
  return `/api/agents/episode?${params}`;
}

// «احسب». The one request that carries a person's decision sends preempt=1;
// every poll after it waits its turn (app.replay's rule, kept here).
function compute() {
  if (!state.query) return;
  state.loadToken += 1;
  const token = state.loadToken;
  const now = performance.now();
  pauseByUser(state.play, now);
  state.play = createPlayState(new PlaybackClock(0));
  state.play.clock.setRate(Number($('rate')?.value) || 1, now);
  if (state.metaKey !== keyOf(state.query)) { state.meta = null; state.road = null; }
  state.frames = [];
  state.done = false;
  state.device = null;
  state.versions = null;
  state.lastK = -2;
  showError(null);
  const prompt = $('scene-prompt');
  if (prompt) prompt.hidden = true;
  setControlsEnabled(false);
  showLoad(() => t(currentLang, 'agents.load.networks'), 0);
  renderAll();
  poll(token, true);
}

async function poll(token, preempt) {
  if (state.polling === token) return;
  state.polling = token;
  try {
    for (;;) {
      let res;
      let body = null;
      try {
        res = await fetch(episodeUrl(state.frames.length, preempt),
          { headers: { Accept: 'application/json' }, cache: 'no-store' });
        body = await res.json().catch(() => null);
      } catch (err) {
        if (token !== state.loadToken) return;
        // Frames already received stay playable; the retry resumes from them.
        showLoad(null);
        showError(() => t(currentLang, 'agents.load.server_down'), { retry: () => poll(token, false) });
        return;
      }
      if (token !== state.loadToken) return;   // a newer «احسب» owns the page
      preempt = false;
      if (!handle(res.status, body)) return;
      await wait(POLL_MS);
      if (token !== state.loadToken) return;
    }
  } finally {
    if (state.polling === token) state.polling = null;
  }
}

function stop(text, options) {
  showLoad(null);
  showError(text, options);
  renderTimeline();
}

// One response. Returns true to keep polling.
function handle(status, body) {
  if (status === 404) { stop(() => t(currentLang, 'agents.load.not_found')); return false; }
  if (status === 409) {
    stop(() => t(currentLang, 'agents.load.refused'), { items: (body && body.problems) || [] });
    return false;
  }
  if (status === 503) { stop(() => t(currentLang, 'agents.load.no_sb3')); return false; }
  if (status !== 200 || !body) {
    const message = `HTTP ${status}`;
    stop(() => t(currentLang, 'agents.load.error', { message }), { retry: compute });
    return false;
  }
  if (body.meta && body.road) applyMeta(body.meta, body.road);
  if (body.device) state.device = body.device;
  if (body.versions) state.versions = body.versions;
  // Only a slice that starts exactly where the held frames end is kept; a
  // stale or overlapping response changes nothing (agent-view.appendFrames).
  const accepted = appendFrames(state.frames, body);
  const now = performance.now();
  if (accepted && body.frames.length) {
    resumeIfStalled(state.play, state.frames.length * DT, now);
    setControlsEnabled(true);
    // Paused at 0:00 the clock never moves, so the animation loop never redraws:
    // draw once when frame 0 first exists, or the panel reads — until play.
    if (state.lastK < 0) draw(state.play.clock.time, true);
  }
  const steps = num(body.steps) || 1;
  if (body.status === 'loading') showLoad(() => t(currentLang, 'agents.load.networks'), 0);
  else if (body.status === 'busy') {
    const a = body.active || {};
    showLoad(() => t(currentLang, 'agents.load.busy', { runs: a.runs, seed: a.seed, ep: a.ep }), 0);
  } else if (body.status === 'building') {
    const percent = Math.round(state.frames.length / steps * 100);
    showLoad(() => t(currentLang, 'agents.load.building', { percent }), state.frames.length / steps);
  } else if (body.status === 'ready' && accepted) {
    state.done = true;
    settleDone(state.play, state.frames.length * DT, now);
    showLoad(null);
    renderAll();
    return false;
  } else if (body.status === 'error') {
    const message = body.message || '';
    stop(() => t(currentLang, 'agents.load.error', { message }), { retry: compute });
    return false;
  }
  renderTimeline();
  return true;
}

// ---------------------------------------------------------------- meta
function applyMeta(meta, road) {
  const key = keyOf({ runs: meta.runs, seed: meta.seed, ep: meta.ep });
  if (state.metaKey === key && state.road) return;
  state.metaKey = key;
  state.meta = meta;
  state.road = road;
  const more = $('verdict-more');
  if (more) more.open = !window.matchMedia?.('(max-width: 760px)').matches;
  drawProfile(road);
  renderAll();
}

function option(select, text) {
  if (!select) return;
  select.textContent = '';
  const o = el('option', '', text);
  o.selected = true;
  select.appendChild(o);
}

function renderPicker() {
  const q = state.query;
  const m = state.meta;
  const button = $('compute');
  if (button) button.disabled = !q;
  const note = $('pick-note');
  if (note) note.textContent = '';
  if (!q) {
    for (const id of ['pick-experiment', 'pick-pair', 'pick-episode']) option($(id), EM_DASH);
    setText(note, t(currentLang, 'agents.pick.none'));
    return;
  }
  const short = m?.verdict?.short?.[currentLang];
  option($('pick-experiment'), m ? (short ? `${m.experiment} · ${short}` : m.experiment) : q.runs);
  option($('pick-pair'), t(currentLang, 'agents.pick.pair_option', { seed: q.seed }));
  const e = m?.episode;
  const episodeText = e
    ? t(currentLang, 'agents.pick.episode_option', {
      idx: m.ep,
      start: fmt(e.climb_start_s, 0),
      grade: num(e.grade) === null ? EM_DASH : fmt(e.grade * 100, 1),
      w0: fmt(e.weights[0], 2),
      w1: fmt(e.weights[1], 2),
      w2: fmt(e.weights[2], 2),
    })
    : `${t(currentLang, 'agents.pick.episode')} ${q.ep}`;
  option($('pick-episode'), episodeText);
  if (!note || !m) return;
  // The select may truncate on a narrow screen; the weights must stay legible.
  note.appendChild(el('span', '', episodeText));
  (m.agents || []).forEach((agent, i) => {
    const line = el('span', LANES[i]);
    line.appendChild(el('i', 'lane-dot'));
    line.appendChild(el('span', '', `${t(currentLang, LANE_LABEL[i])} · ${t(currentLang, 'agents.pick.budget', { budget: budgetSteps(agent.budget_line) })}`));
    note.appendChild(line);
  });
}

function renderBadge() {
  const m = state.meta;
  if (!m) { setText($('sim-badge'), t(currentLang, 'agents.badge.short')); return; }
  // Figures from meta only: the episode's own grade, the scenario's speed and
  // ambient. Nothing here is read from a document or a recorded drive.
  setText($('sim-badge'), t(currentLang, 'agents.badge', {
    grade: num(m.episode?.grade) === null ? EM_DASH : fmt(m.episode.grade * 100, 1),
    v: fmt(m.scenario?.v_kmh, 0),
    t: fmt(m.scenario?.t_amb_c, 0),
  }));
}

// The verdict is QUOTED, never computed: each line is the file's own text with
// its results/<file>:<line>. The short line and the glosses are authored and
// arrive from the server only when every anchor they summarise was found.
function renderVerdict() {
  const v = state.meta?.verdict || null;
  const box = $('verdict');
  if (box) box.dataset.state = v ? v.state : 'waiting';
  const shortText = v?.short?.[currentLang] || EM_DASH;
  setText($('verdict-short'), shortText);
  setText($('strip-verdict'), v ? shortText : '');
  const cells = $('verdict-cells');
  if (cells) {
    cells.textContent = '';
    for (const c of v?.cells || []) {
      const li = el('li');
      const cell = el('b', 'cell', c.cell);
      cell.dir = 'ltr';
      li.append(cell, el('span', 'gloss', c.gloss?.[currentLang] || ''));
      cells.appendChild(li);
    }
  }
  const lines = $('verdict-lines');
  if (lines) {
    lines.textContent = '';
    for (const line of v?.lines || []) {
      const fig = el('figure', 'quote');
      const pre = el('pre', '', line.text);
      pre.dir = 'ltr';
      const n = line.text.split('\n').length;
      const where = n > 1 ? `${line.line}-${line.line + n - 1}` : String(line.line);
      const cite = el('figcaption', '', t(currentLang, 'agents.verdict.source', { file: line.file, line: where }));
      cite.dir = 'ltr';
      fig.append(pre, cite);
      lines.appendChild(fig);
    }
  }
  const summary = $('verdict-more')?.querySelector('summary');
  const files = [...new Set((v?.lines || []).map(l => `results/${l.file}`))];
  setText(summary, files.length ? files.join(' · ') : EM_DASH);
  const scored = $('verdict-scored');
  if (!scored) return;
  scored.textContent = '';
  const m = state.meta;
  (m?.agents || []).forEach((agent, i) => {
    const status = !m.result_file ? t(currentLang, 'agents.verdict.no_result')
      : agent.scored === 'match' ? t(currentLang, 'agents.verdict.scored_match')
        : t(currentLang, 'agents.verdict.not_recorded');
    const li = el('li', LANES[i]);
    li.appendChild(el('i', 'lane-dot'));
    li.appendChild(el('span', '', `${t(currentLang, LANE_LABEL[i])} · ${status}`));
    const sha = el('code', '', `zip sha ${agent.zip_sha || EM_DASH}`);
    sha.dir = 'ltr';
    li.appendChild(sha);
    scored.appendChild(li);
  });
}

// Replayed at meta.dt, trained at meta.train_dt: said on the page, from meta.
function renderDtCaption() {
  const m = state.meta;
  if (!m) { setText($('dt-caption'), ''); return; }
  const train = [m.train_dt?.sighted, m.train_dt?.blind].map(num);
  if (train.some(v => v === null)) { setText($('dt-caption'), t(currentLang, 'agents.dt.not_recorded')); return; }
  if (train.every(v => v === m.dt)) { setText($('dt-caption'), t(currentLang, 'agents.dt.same')); return; }
  const shown = train[0] === train[1] ? String(train[0]) : `${train[0]} / ${train[1]}`;
  setText($('dt-caption'), t(currentLang, 'agents.dt.caption', { train_dt: shown }));
}

// ---------------------------------------------------------------- profile
function climbIndex(road) {
  const s = num(road?.climb_start_s);
  if (s === null) return null;
  return Math.min(road.grade_pct.length - 1, Math.max(0, Math.round(s / DT)));
}

// Whole route, x against height at VE x3, from the road the server built from
// the episode's own grade. One car marker: both cars are always at one place.
function drawProfile(road) {
  const host = $('profile');
  if (!host || !road) return;
  const p = profilePoints(road, { ve: PROFILE_VE, width: PROFILE_W });
  const height = Math.max(1, p.height);
  const Y = z => (height - z).toFixed(1);
  const line = p.points.map(([x, z], i) => `${i ? 'L' : 'M'}${x.toFixed(1)} ${Y(z)}`).join('');
  const ci = climbIndex(road);
  const climb = ci === null ? ''
    : `<line class="profile-climb" x1="${p.points[ci][0].toFixed(1)}" y1="${(-PROFILE_PAD).toFixed(1)}" x2="${p.points[ci][0].toFixed(1)}" y2="${height.toFixed(1)}"/>`;
  const ticks = (state.meta?.preview_s || []).map(() => '<line class="profile-tick" visibility="hidden"/>').join('');
  // x in km (design section 5, View 1): horizontal distance, every KM_STEP km.
  const kms = [];
  for (let km = 0; km * 1000 * p.sx <= PROFILE_W + 1e-6; km += KM_STEP) kms.push(km);
  const scale = kms.map(km => {
    const X = (km * 1000 * p.sx).toFixed(1);
    return `<line class="profile-km-tick" x1="${X}" y1="${height.toFixed(1)}" x2="${X}" y2="${(height + 8).toFixed(1)}"/>`;
  }).join('');
  host.innerHTML = `<svg viewBox="0 ${-PROFILE_PAD} ${PROFILE_W} ${height + 2 * PROFILE_PAD}" preserveAspectRatio="xMidYMid meet" aria-hidden="true">`
    + `<path class="profile-ground" d="${line}L${PROFILE_W} ${height}L0 ${height}Z"/>`
    + `<path class="profile-road" d="${line}"/>`
    + scale + climb + ticks
    + '<circle class="profile-car" r="7" cx="-40" cy="-40"/>'
    + '</svg>';
  const axis = el('div', 'profile-axis');
  axis.setAttribute('aria-hidden', 'true');
  for (const km of kms) {
    const label = el('span', 'profile-km');
    const frac = km * 1000 * p.sx / PROFILE_W;
    label.dataset.km = String(km);
    label.style.left = `${(frac * 100).toFixed(2)}%`;
    if (frac < 0.04) label.classList.add('start');
    else if (frac > 0.96) label.classList.add('end');
    axis.appendChild(label);
  }
  host.appendChild(axis);
  if (ci !== null) {
    const label = el('span', 'profile-climb-label');
    const frac = p.points[ci][0] / PROFILE_W;
    label.style.left = `${(frac * 100).toFixed(2)}%`;
    label.classList.toggle('flip', frac < 0.5);
    host.appendChild(label);
  }
  state.profile = {
    sx: p.sx, ve: p.ve, height,
    car: host.querySelector('.profile-car'),
    ticks: [...host.querySelectorAll('.profile-tick')],
  };
}

function renderProfileCaptions() {
  const road = state.road;
  const host = $('profile');
  setText($('profile-ve'), road ? t(currentLang, 'agents.profile.ve', { ve: PROFILE_VE }) : '');
  const rise = road ? t(currentLang, 'agents.profile.rise', {
    rise: fmtInt(road.rise_m), p: fmt(road.p_baro_kpa, 1), t: fmt(road.t_amb_c, 0),
  }) : '';
  setText($('rise-caption'), rise);
  if (host) host.setAttribute('aria-label', rise);
  host?.querySelectorAll('.profile-km').forEach(span => {
    setText(span, t(currentLang, 'agents.profile.km', { km: span.dataset.km }));
  });
  const label = host?.querySelector('.profile-climb-label');
  const ci = climbIndex(road);
  if (label && ci !== null) {
    setText(label, t(currentLang, 'agents.profile.climb', {
      start: fmt(road.climb_start_s, 0), grade: fmt(road.grade_pct[ci], 1),
    }));
  }
}

// The car marker and, for the sighted car only, a tick at each horizon it was
// given: x[min(k + int(h/dt), last)]. Four ticks, not a band -- it saw four numbers.
// Each tick is coloured by the grade there on the chase view's single-hue ramp
// (gradeRamp, 0 to 16 %), so the two views read the same way.
function moveProfile(at, showTicks = true) {
  const p = state.profile;
  if (!p) return;
  const X = x => (x * p.sx).toFixed(1);
  const Y = z => (p.height - z * p.sx * p.ve).toFixed(1);
  if (at.k < 0) {
    p.car.setAttribute('visibility', 'hidden');
    p.ticks.forEach(tick => tick.setAttribute('visibility', 'hidden'));
    return;
  }
  p.car.setAttribute('visibility', 'visible');
  p.car.setAttribute('cx', X(at.x_m));
  p.car.setAttribute('cy', Y(at.z_m));
  const marks = showTicks ? previewMarks(state.road, at.k, state.meta.preview_s, DT) : [];
  p.ticks.forEach((tick, i) => {
    const m = marks[i];
    if (!m) { tick.setAttribute('visibility', 'hidden'); return; }
    const y = p.height - m.z_m * p.sx * p.ve;
    tick.setAttribute('x1', X(m.x_m));
    tick.setAttribute('x2', X(m.x_m));
    tick.setAttribute('y1', (y - 18).toFixed(1));
    tick.setAttribute('y2', (y - 4).toFixed(1));
    const f = gradeRamp(m.grade_pct);
    tick.style.stroke = f === null ? 'var(--muted)'
      : `color-mix(in srgb, var(--agent-ramp-hi) ${(f * 100).toFixed(1)}%, var(--agent-ramp-lo))`;
    tick.setAttribute('visibility', 'visible');
  });
}

// ---------------------------------------------------------------- timeline
// Waiting: the viewer asked to play and the clock sits at the computed edge,
// either because play was pressed there (agent-view's waiting flag) or because
// playback caught up with the computation. More frames resume it either way.
function isWaiting() {
  const p = state.play;
  const c = p.clock;
  return p.waiting || (!p.userPaused && !state.done && !c.playing
    && state.frames.length > 0 && c.time >= c.duration - 1e-9);
}

// The track is the whole episode (meta.steps x meta.dt = 11:59); the clock's
// end is the COMPUTED end, and the uncomputed part is hatched.
function renderTimeline() {
  const m = state.meta;
  const end = m ? (num(m.steps) || 0) * (num(m.dt) || DT) : 0;
  const computed = state.frames.length * DT;
  setText($('duration'), formatTime(end));
  const seek = $('seek');
  if (seek) seek.max = String(end || 1);
  const fill = $('computed-fill');
  if (fill) fill.style.width = `${end > 0 ? Math.min(100, computed / end * 100) : 0}%`;
  const tick = $('climb-tick');
  const climb = num(state.road?.climb_start_s);
  if (tick) {
    tick.hidden = climb === null || !(end > 0);
    if (!tick.hidden) tick.style.left = `${(climb / end * 100).toFixed(2)}%`;
  }
  const note = $('computed-note');
  if (isWaiting()) setText(note, t(currentLang, 'agents.time.waiting'));
  else if (m && !state.done && state.frames.length) {
    setText(note, t(currentLang, 'agents.time.computed', { done: formatTime(computed), end: formatTime(end) }));
  } else setText(note, '');
}

function syncPlayButton() {
  const play = $('play');
  if (!play) return;
  const on = state.play.clock.playing || isWaiting();
  play.querySelector('use')?.setAttribute('href', on ? '#i-pause' : '#i-play');
  setText(play.querySelector('span'), t(currentLang, on ? 'transport.pause' : 'transport.play'));
  play.setAttribute('aria-label', t(currentLang, on ? 'transport.pause_aria' : 'transport.play_aria'));
}

// ---------------------------------------------------------------- per frame
function draw(time, force = false) {
  setText($('current-time'), formatTime(time));
  const seek = $('seek');
  if (seek && document.activeElement !== seek) seek.value = String(time);
  if (!state.road) return;
  const at = episodeAt(state.frames, state.road, time);
  moveProfile(at);
  if (force || at.k !== state.lastK) state.lastK = at.k;
}

function renderAll() {
  renderPicker();
  renderBadge();
  renderVerdict();
  renderDtCaption();
  renderProfileCaptions();
  renderTimeline();
  renderLoad();
  renderError();
  syncPlayButton();
  draw(state.play.clock.time, true);
}

// ---------------------------------------------------- theme and language
// Presentation only: switching either never changes a value on this page.
function applyTheme(name) {
  const theme = THEMES.includes(name) ? name : 'light';
  document.documentElement.dataset.theme = theme;
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) {
    meta.setAttribute('content',
      getComputedStyle(document.documentElement).getPropertyValue('--bg').trim() || '#f4f3ed');
  }
  const button = $('theme-toggle');
  if (button) {
    button.title = t(currentLang, theme === 'dark' ? 'theme.to_light' : 'theme.to_dark');
    button.setAttribute('aria-pressed', String(theme === 'dark'));
    button.querySelector('use')?.setAttribute('href', theme === 'dark' ? '#i-sun' : '#i-moon');
  }
  remember(STORE.theme, theme);
}

function applyLanguage(name) {
  currentLang = resolveLang(name);
  applyTranslations(document, currentLang);
  const button = $('lang-toggle');
  if (button) {
    const other = currentLang === 'ar' ? 'en' : 'ar';
    button.title = t(currentLang, other === 'en' ? 'lang.switch_to_english' : 'lang.switch_to_arabic');
    setText(button.querySelector('span'), other === 'en' ? 'EN' : 'AR');
  }
  renderAll();
  remember(STORE.lang, currentLang);
}

// ---------------------------------------------------------------- boot
function loop(now) {
  const clock = state.play.clock;
  const time = clock.tick(now);
  if (time !== state.drawnTime) { draw(time); state.drawnTime = time; }
  const on = clock.playing || isWaiting();
  if (on !== state.wasPlaying) { state.wasPlaying = on; syncPlayButton(); renderTimeline(); }
  requestAnimationFrame(loop);
}

function start() {
  $('play')?.addEventListener('click', () => {
    const now = performance.now();
    if (state.play.clock.playing || isWaiting()) pauseByUser(state.play, now);
    else playOrWait(state.play, state.frames.length * DT, state.done, now);
    syncPlayButton();
    renderTimeline();
  });
  $('restart')?.addEventListener('click', () => {
    const now = performance.now();
    pauseByUser(state.play, now);
    state.play.clock.seek(0, now);
    syncPlayButton();
    renderTimeline();
    draw(0, true);
  });
  $('seek')?.addEventListener('input', () => {
    const seek = $('seek');
    const now = performance.now();
    // Scrubbing clamps to what has been computed; nothing past it exists yet.
    const target = Math.min(Number(seek.value), state.play.clock.duration);
    state.play.clock.seek(target, now);
    if (Number(seek.value) !== target) seek.value = String(target);
    draw(state.play.clock.time, true);
  });
  $('rate')?.addEventListener('change', () => {
    state.play.clock.setRate(Number($('rate').value), performance.now());
  });
  $('compute')?.addEventListener('click', compute);
  $('theme-toggle')?.addEventListener('click', () => {
    applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark');
  });
  $('lang-toggle')?.addEventListener('click', () => {
    applyLanguage(currentLang === 'ar' ? 'en' : 'ar');
  });
  applyTheme(recall(STORE.theme, THEMES,
    window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
  applyLanguage(recall(STORE.lang, LANGS, DEFAULT_LANG));
  requestAnimationFrame(loop);
}

try {
  start();
} catch (err) {
  console.error(err);
  const message = err.message;
  showError(() => t(currentLang, 'agents.load.error', { message }));
}
```

- [ ] **Step 7: Add the two strings the page needs to `app/static/sim/agents-strings.mjs`**

The torque reading's `<dt>` and the profile's km labels use two keys that Task 7 does not define. Add them with the Edit tool. Each old string occurs once: the `ar` block ends just before `en: {`, and the `en` block ends just before `};`.

Replace:

```js
    'agents.footer.index': '02 — AGENTS',
  },

  en: {
```

with:

```js
    'agents.footer.index': '02 — AGENTS',

    // --- added by Task 9: the torque reading's label, the profile's km scale
    'agents.torque.heading': 'العزم المُسلَّم مقابل المطلوب',
    'agents.profile.km': '{km} كم',
  },

  en: {
```

Then replace:

```js
    'agents.footer.index': '02 — AGENTS',
  },
};
```

with:

```js
    'agents.footer.index': '02 — AGENTS',

    // --- added by Task 9: the torque reading's label, the profile's km scale
    'agents.torque.heading': 'Torque delivered against requested',
    'agents.profile.km': '{km} km',
  },
};
```

If Task 7's file lays out the end of its two blocks differently (blank lines, comments), put the same two entries as the last entries of each block. Task 7's tests count the keys from the table itself, so they need no change: they check both languages, collisions and matching `{placeholders}`.

- [ ] **Step 8: Run to verify it passes, and that the lab is unchanged**

Run:
```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
$PY -m unittest app.test_agents.PageTests -v
node --test app/static/sim/agents-page.test.mjs
node --test "app/static/sim/*.test.mjs"
$PY -m app.test_simulation
```
Expected:
- `Ran 2 tests` … `OK`. A starlette DeprecationWarning about `BlockingPortal` may print; it is not a failure.
- agents-page: `ℹ tests 7`, `ℹ pass 7`, `ℹ fail 0`. Before Step 7 the two key tests fail naming `'agents.torque.heading'` and `'agents.profile.km'`; that is the expected failure if Step 7 was skipped.
- The glob: `ℹ fail 0`. The count is the lab's 30, plus Task 7's and Task 8's tests, plus these 7.
- `app.test_simulation`: `Ran 15 tests` … `OK`, the same as before M1.

If `test_page_assets_ids` fails with `import map points at missing vendor/three/...`, Three.js is not vendored on this machine. Run `cd app && npm install && npm run vendor`. That is the first half of `app\start-simulation.ps1`, and it writes only the gitignored `app/static/vendor/`.

If the placeholder test fails, Task 7's strings disagree with the skeleton's placeholder names. For example, `agents.load.building [ar] is never given {percent}` means the call and the string use different names. Fix whichever side departs from the skeleton, then run the test again.

If the ramp test fails with `#… is not in agent-scene.mjs's RAMP`, Task 8 chose different ramp colours. Copy Task 8's `RAMP` low and high values (light and dark) into the three token blocks at the top of `agents.css`.

- [ ] **Step 9: Look at it once in a browser**

Run the server with the system interpreter, in the background:
```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
$PY -m app.server --simulation
```
Do not use `app\start-simulation.ps1` for this. Its last line calls bare `python`, and on this machine that resolves to the repository's `.venv` (checked 26 Sep: `(Get-Command python).Source` is `.venv\Scripts\python.exe`). That interpreter has FastAPI but neither stable-baselines3 nor torch. A server started from it serves `/agents`, but `/api/agents/episode` answers `503 {"detail":"stable-baselines3 is not installed"}` (measured).

Open `http://localhost:8000/agents`. Expected: «احسب» is disabled and `#pick-note` shows the `agents.pick.none` example.

Then open `http://localhost:8000/agents?runs=runs_c4&seed=5&ep=1`. Expected:
- The three disabled selects read `runs_c4`, the pair and `الحلقة 1`. Nothing is requested; `performance.getEntriesByType('resource')` holds no `/api/agents` entry.
- After «احسب», the profile appears within about 0.5 s with a km scale under it (`0 كم` to `25 كم`), «المقياس الرأسي مضخّم ×3» and the rise caption. «تحميل الشبكتين…» shows in the loading card, and the badge fills from meta.
- When the first frame arrives, without pressing play, the car marker appears at the start of the profile.
- The timeline fills as frames arrive and the end label reads `11:59`.
- Seek to about 02:10 and pause. Two of the four ticks above the road are pale (flat road at +2 s and +5 s) and two are dark violet (the climb at +15 s and +30 s).
- The chase view and the pause panel stay empty; Task 10 fills them.

Stop the server.

- [ ] **Step 10: Commit**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
test "$(git branch --show-current)" = JMF-2340550-sep17 || { echo "not on JMF-2340550-sep17"; exit 1; }
git add app/static/agents.html app/static/sim/agents.css app/static/sim/agents.mjs app/static/sim/agents-page.test.mjs app/static/sim/agents-strings.mjs app/test_agents.py
$PY verify_docs.py | tail -1
OUT=$(mktemp -d)
$PY -m app.test_replay > "$OUT/replay.txt" 2>&1; tail -1 "$OUT/replay.txt"
{
  echo "Agent replay M1 task 9: the /agents page shell"
  echo
  echo "agents.html, agents.css and agents.mjs: the read-only URL picker, one"
  echo "preempt=1 request per «احسب», polling every 400 ms through"
  echo "agent-view.appendFrames only, the quoted C4 verdict with results/<file>:<line>,"
  echo "the SIMULATED badge from meta, the dt caption, the timeline that waits at"
  echo "the computed edge, and the whole-route profile at VE x3 with a km scale"
  echo "and preview ticks on the chase view's grade ramp. Frame 0 is drawn as"
  echo "soon as it exists. No physics, no statistic, no difference between the"
  echo "cars. agents-strings.mjs gains agents.torque.heading and agents.profile.km."
  echo "PageTests (assets, ids, imports, t() language) and agents-page.test.mjs"
  echo "(keys, placeholders, nav, labelled readings, one ramp)."
  echo
  echo '$ python -m app.test_replay'
  cat "$OUT/replay.txt"
  echo
  echo "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
} > "$OUT/msg.txt"
git commit -F "$OUT/msg.txt"
git log -1 --stat
```
Expected:
- verify_docs' last line reads `All N checks pass (...)`. On 26 Sep, with Tasks 1 to 10 git-added in the scratch assembly, it read `All 67 checks pass (782 figure mentions scanned in the documents).`; read N from your run.
- test_replay's last line reads `49 of 49 checks pass`.
- The commit lists the six files.

---


---

### Task 10: Pause panel and chase view (dynamic import), scene strip and lane labels

**Files:**
- Modify: `app/static/sim/agents.mjs`: nine exact replacements, below. Each old string occurs exactly once in the Task 9 file; the prototype applied them by script and asserted a count of 1 for each.
- Modify: `app/static/sim/agents.css`: append the pause-panel rules.
- Modify: `app/test_agents.py`: two more methods in `PageTests`.
- Test: `app/test_agents.py` (`PageTests`), `app/static/sim/agents-page.test.mjs` (run again)
- `app/static/agents.html` needs no edit, although the skeleton listed it as possibly modified. Task 9 already declares every id this task writes to, including the torque reading's `<dt>`.

**Interfaces:**
- Consumes:
  - From Task 8: `createChaseScene(host, episodeRoad, {sighted, blind})`, reached only through `await import('./agent-scene.mjs')`. It returns `{update({distance_m, marks[{s_m, grade_pct}]}), setTheme(name, lanes), dispose()}`.
  - From Task 8's `agent-view.mjs`: `ACTIONS, M_PER_UNIT, createEpisodeRoad, gaugeFraction, commandPhysical, laneStoppedAt`.
  - `meta.act{lo, hi, neutral_phys}`, `meta.limits.turb_c`, `meta.preview_s`, `meta.episode.weights`, `meta.protocol`, `meta.fingerprint_taken`, and the top-level `device`/`versions` of each poll.
  - Frame cars: `cmd, act, held, preview_pct, map_kpa, turb_c, torque_nm, torque_req_nm, damage`.
  - The lab key `seed.model_output`, already in `#model-caveat`.
- Produces, in `agents.mjs`:
  - `carOf(frame, lane) -> car | null`, the only reader of `.cars`.
  - `laneColours() -> {sighted, blind}`, read from the CSS tokens.
  - `mountChase(road)`, which uses a dynamic import inside try/catch. On failure `#chase` shows `agents.scene.webgl_error` and everything else keeps rendering.
  - `renderLaneLabels()`, with `BLIND_LABEL` keyed by `meta.protocol`. M2 adds Phase D's label as one more row.
  - `fmtAction(i, v)`.
  - `buildActionRows()` (once per meta and language) and `renderActions(frame)`, which show the APPLIED value and, only where held, the command.
  - `renderSeen`, `renderReadings`, `renderDevice` (with the warning when not on cuda), `renderStopped`, and `renderPanel(k)`, which runs only when k changes. Task 9's frame-0 draw in `handle()` reaches it too.
  - `draw(time, force)` now also feeds `chase.update` and `renderPanel`.
  - Nothing compares the two cars.

Prototype (26 Sep, the same scratch assembly as Task 9). Paused at 312.4 s on `runs_c4/5/1`:
- five rows; row 1 showed both cars held («أمر به −0.135؛ قيّده حد سرعة التغيير»);
- row 2 showed `ضغط المشعب الآن 186.6` and `191.7` beside `+0.9` and `+11.0` kPa;
- the blind car read `0 · 0 · 0 · 0`; the device line read `cuda (torch 2.11.0+cu128، SB3 2.9.0)`;
- with `three.module.js` blocked through DevTools, `#chase` showed the WebGL message while the badge, the verdict, the dt caption, the profile and all five rows rendered.

- [ ] **Step 1: Write the failing tests**

Add these two methods at the end of `class PageTests` in `app/test_agents.py`:

```python
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
```

- [ ] **Step 2: Run to verify they fail**

Run:
```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
$PY -m unittest app.test_agents.PageTests -v
```
Expected: `FAIL: test_chase_is_optional` with `AssertionError: False is not true : the chase view must be loaded by dynamic import`, and `FAIL: test_every_car_is_read_through_carOf` with `AssertionError: 0 != 1 : read a car only through carOf(frame, lane)`. Then `Ran 4 tests` and `FAILED (failures=2)`.

- [ ] **Step 3: Edit `app/static/sim/agents.mjs`**

Apply each replacement with the Edit tool (old string exactly as shown, then new string).

**Edit A: import the panel helpers from agent-view.mjs.** Replace:

```js
  pauseByUser, resumeIfStalled, settleDone, episodeAt, profilePoints, previewMarks, gradeRamp,
} from './agent-view.mjs';
```

with:

```js
  pauseByUser, resumeIfStalled, settleDone, episodeAt, profilePoints, previewMarks, gradeRamp,
  ACTIONS, M_PER_UNIT, createEpisodeRoad, gaugeFraction, commandPhysical, laneStoppedAt,
} from './agent-view.mjs';
```

**Edit B: module state for the chase view and the blind-car label.** Replace:

```js
let currentLang = DEFAULT_LANG;
```

with:

```js
let currentLang = DEFAULT_LANG;

// The chase view is loaded on demand (mountChase) and may never exist: when
// Three.js or WebGL fails, every other surface of the page still renders.
let chase = null;
let chaseToken = 0;
// The blind car's label, by protocol. M2 gives Phase D's blind car its own
// ("may have memorised the road", PHASE_D_RESULT.txt:33-37) as one more row.
const BLIND_LABEL = { d2: 'agents.car.blind', 'phase-d': 'agents.car.blind' };
```

**Edit C: a slot for the action rows in `state`.** Replace:

```js
  wasPlaying: false,
};
```

with:

```js
  wasPlaying: false,
  rows: [],        // the five action rows of the pause panel, built per meta
};
```

**Edit D: refresh the device line on every response (inside `handle`).** Replace:

```js
  if (body.versions) state.versions = body.versions;
```

with:

```js
  if (body.versions) state.versions = body.versions;
  renderDevice();
```

**Edit E: mount the chase view when meta arrives (inside `applyMeta`).** Replace:

```js
  drawProfile(road);
  renderAll();
}
```

with:

```js
  drawProfile(road);
  mountChase(road);
  renderAll();
}
```

**Edit F: the chase-view and pause-panel functions, inserted before the per-frame section.** Replace:

```js
// ---------------------------------------------------------------- per frame
```

with:

```js
// ---------------------------------------------------------------- chase view
// Lane `lane` of a frame, or null. A lane that diverged is null from that
// step on (design 3.2), so every read of a car goes through here.
function carOf(frame, lane) {
  return frame?.cars?.[lane] ?? null;
}

function laneColours() {
  const css = getComputedStyle(document.documentElement);
  // The fallbacks only matter if agents.css failed to load.
  return {
    sighted: css.getPropertyValue('--agent-sighted').trim() || '#2f6db0',
    blind: css.getPropertyValue('--agent-blind').trim() || '#b5761c',
  };
}

// Loaded by DYNAMIC import, never a static one: app/static/vendor/ is
// gitignored and exists only after app\start-simulation.ps1, and a failed
// static import of Three.js would take the whole module graph -- verdict,
// badge, dt caption, profile, panel -- down with it.
async function mountChase(road) {
  const host = $('chase');
  if (!host || !road) return;
  chaseToken += 1;
  const token = chaseToken;
  chase?.dispose();
  chase = null;
  host.textContent = '';
  try {
    const { createChaseScene } = await import('./agent-scene.mjs');
    if (token !== chaseToken) return;
    chase = createChaseScene(host, createEpisodeRoad(road, M_PER_UNIT), laneColours());
    chase.setTheme(document.documentElement.dataset.theme || 'light', laneColours());
    draw(state.play.clock.time, true);
  } catch (err) {
    console.error(err);
    if (token !== chaseToken) return;
    chase = null;
    host.textContent = '';
    host.appendChild(el('p', 'webgl-error', t(currentLang, 'agents.scene.webgl_error')));
  }
}

function renderLaneLabels() {
  const m = state.meta;
  setText($('lane-sighted-label'), m ? t(currentLang, 'agents.car.sighted') : '');
  setText($('lane-blind-label'), m ? t(currentLang, BLIND_LABEL[m.protocol] || 'agents.car.blind') : '');
}

// ---------------------------------------------------------------- pause panel
// The APPLIED action (env.prev_act after rescale, slew limit and bounds) in
// its own unit: trims signed, duties as fractions.
function fmtAction(i, v) {
  const n = num(v);
  if (n === null) return EM_DASH;
  const key = ACTIONS[i].key;
  const text = n.toFixed(ACTIONS[i].digits);
  if (key === 'fan' || key === 'pump') return text;
  return n > 0 ? `+${text}` : text.replace('-', '\u2212');
}

// Five rows, built once per meta and language: a bar from lo to hi, a tick at
// the neutral value, one dot per car. renderActions only moves the dots.
function buildActionRows() {
  const host = $('actions');
  state.rows = [];
  if (!host) return;
  host.textContent = '';
  const act = state.meta?.act;
  if (!act) return;
  ACTIONS.forEach((action, i) => {
    const duty = action.key === 'fan' || action.key === 'pump';
    const row = el('div', 'action-row');
    const head = el('div', 'action-head');
    head.appendChild(el('span', 'action-label', t(currentLang, action.label)));
    if (action.unit) {
      const unit = el('span', 'action-unit', action.unit);
      unit.dir = 'ltr';
      head.appendChild(unit);
    }
    const gauge = el('div', 'gauge');
    const tick = el('i', 'gauge-tick');
    const neutral = gaugeFraction(act.neutral_phys[i], act.lo[i], act.hi[i]);
    tick.style.left = `${((neutral ?? 0) * 100).toFixed(2)}%`;
    gauge.appendChild(tick);
    const dots = LANES.map(lane => {
      const dot = el('i', `gauge-dot ${lane}`);
      dot.hidden = true;
      gauge.appendChild(dot);
      return dot;
    });
    const ends = el('div', 'gauge-ends');
    ends.append(el('span', '', fmtAction(i, act.lo[i])), el('span', '', fmtAction(i, act.hi[i])));
    const note = el('p', 'tick-note', duty
      ? t(currentLang, 'agents.action.tick_duty') : t(currentLang, 'agents.action.tick_trim'));
    const values = el('div', 'action-values');
    const cells = LANES.map(lane => {
      const cell = el('div', `car-value ${lane}`);
      const value = el('b', 'value', EM_DASH);
      value.dir = 'ltr';
      const held = el('small', 'held-line');
      held.hidden = true;
      const map = el('small', 'map-line');
      map.hidden = true;
      cell.append(el('i', 'lane-dot'), value, held, map);
      values.appendChild(cell);
      return { value, held, map };
    });
    row.append(head, gauge, ends, note, values);
    host.appendChild(row);
    state.rows.push({ dots, cells });
  });
}

function renderActions(frame) {
  const act = state.meta?.act;
  if (!act) return;
  state.rows.forEach((row, i) => {
    row.cells.forEach((cell, j) => {
      const car = carOf(frame, j);
      const dot = row.dots[j];
      if (!car) {
        setText(cell.value, EM_DASH);
        cell.held.hidden = true;
        cell.map.hidden = true;
        dot.hidden = true;
        return;
      }
      setText(cell.value, fmtAction(i, car.act[i]));
      const f = gaugeFraction(car.act[i], act.lo[i], act.hi[i]);
      dot.hidden = f === null;
      if (f !== null) dot.style.left = `${(f * 100).toFixed(2)}%`;
      // The command appears only where the rate limit held it back.
      cell.held.hidden = !car.held[i];
      if (car.held[i]) {
        const x = fmtAction(i, commandPhysical(car.cmd, act.lo, act.hi)[i]);
        setText(cell.held, t(currentLang, 'agents.action.held', { x }));
      }
      // Row 2 offsets the CEILING of the agent's own pressure loop; its own
      // manifold pressure is what shows whether that ceiling was reached.
      cell.map.hidden = ACTIONS[i].key !== 'boost';
      if (!cell.map.hidden) setText(cell.map, t(currentLang, 'agents.action.map', { map: fmt(car.map_kpa, 1) }));
    });
  });
}

// What each car was given: the sighted car's four horizons from meta.preview_s
// (engine_env.PREVIEW_S), the blind car's real inputs -- zeros, read from the
// frame rather than written here.
function renderSeen(frame) {
  const horizons = state.meta?.preview_s || [];
  const sighted = carOf(frame, 0);
  const blind = carOf(frame, 1);
  setText($('seen-sighted'), sighted
    ? horizons.map((h, i) => t(currentLang, 'agents.seen.item', { h, pct: fmt(sighted.preview_pct[i], 1) })).join(' · ')
    : '');
  const zeros = blind ? blind.preview_pct.map(v => (v === 0 ? '0' : fmt(v, 1))).join(' · ') : '';
  setText($('seen-blind'), blind ? t(currentLang, 'agents.seen.blind', { zeros }) : '');
}

function renderReadings(frame) {
  const limit = state.meta?.limits?.turb_c;
  const outputs = [
    { damage: $('damage-sighted'), turb: $('turb-sighted'), torque: $('torque-sighted') },
    { damage: $('damage-blind'), turb: $('turb-blind'), torque: $('torque-blind') },
  ];
  outputs.forEach((out, j) => {
    const car = carOf(frame, j);
    setText(out.damage, car ? fmt(car.damage, 1) : EM_DASH);
    setText(out.turb, car ? `${fmt(car.turb_c, 0)} °C / ${fmt(limit, 1)} °C` : EM_DASH);
    setText(out.torque, car ? t(currentLang, 'agents.torque.label', {
      delivered: fmt(car.torque_nm, 0), requested: fmt(car.torque_req_nm, 0),
    }) : EM_DASH);
  });
}

// CPU and CUDA give different episodes (recon section 2), so the device and
// the versions are shown, and a non-CUDA run says so.
function renderDevice() {
  const line = $('device-line');
  if (line) {
    const v = state.versions || {};
    const signature = `${state.device}|${v.torch}|${v.sb3}|${currentLang}`;
    if (line.dataset.signature !== signature) {
      line.dataset.signature = signature;
      line.textContent = '';
      if (state.device) {
        line.appendChild(el('span', '', t(currentLang, 'agents.device.line', {
          device: state.device, torch: v.torch || EM_DASH, sb3: v.sb3 || EM_DASH,
        })));
        if (!String(state.device).startsWith('cuda')) {
          line.appendChild(el('strong', 'device-warning', t(currentLang, 'agents.device.warning')));
        }
      }
    }
  }
  const time = state.meta?.fingerprint_taken;
  setText($('fingerprint-taken'), time ? t(currentLang, 'agents.fingerprint_taken', { time }) : '');
}

function renderStopped() {
  const node = $('lane-stopped');
  if (!node) return;
  const parts = LANE_LABEL.map((label, j) => {
    const k = laneStoppedAt(state.frames, j);
    return k === null ? null : `${t(currentLang, label)}: ${t(currentLang, 'agents.lane.stopped', { k })}`;
  }).filter(Boolean);
  node.hidden = !parts.length;
  setText(node, parts.join(' · '));
}

// The decision applied from second k to k+1. Called only when k changes, so
// it holds still while paused. Nothing here compares the two cars.
function renderPanel(k) {
  const frame = k >= 0 ? state.frames[k] || null : null;
  const road = state.road;
  setText($('pause-heading'), frame ? t(currentLang, 'agents.pause.heading', { k, k1: k + 1 }) : EM_DASH);
  setText($('grade-now'), frame && road
    ? t(currentLang, 'agents.pause.grade_now', { grade: fmt(road.grade_pct[k], 1) }) : '');
  const w = state.meta?.episode?.weights;
  setText($('weights-line'), w
    ? t(currentLang, 'agents.pause.weights', { w0: fmt(w[0], 2), w1: fmt(w[1], 2), w2: fmt(w[2], 2) }) : '');
  renderActions(frame);
  renderSeen(frame);
  renderReadings(frame);
  renderStopped();
}

// ---------------------------------------------------------------- per frame
```

**Edit G: `draw()` feeds the chase view and the pause panel.** Replace:

```js
  const at = episodeAt(state.frames, state.road, time);
  moveProfile(at);
  if (force || at.k !== state.lastK) state.lastK = at.k;
}
```

with:

```js
  const at = episodeAt(state.frames, state.road, time);
  const sighted = carOf(at.frame, 0);
  moveProfile(at, Boolean(sighted));
  if (chase) {
    // Four markers where the sighted car's horizons land, coloured by the
    // grade it was given there. Both cars share one distance: the scenario
    // imposes the speed.
    const marks = sighted
      ? previewMarks(state.road, at.k, state.meta.preview_s, DT)
        .map((m, i) => ({ s_m: m.s_m, grade_pct: sighted.preview_pct[i] }))
      : [];
    chase.update({ distance_m: at.s_m, marks });
  }
  if (force || at.k !== state.lastK) {
    state.lastK = at.k;
    renderPanel(at.k);
  }
}
```

**Edit H: `renderAll()` re-renders lane labels, action rows, the device line and the WebGL notice.** Replace:

```js
  renderError();
  syncPlayButton();
  draw(state.play.clock.time, true);
}
```

with:

```js
  renderError();
  renderLaneLabels();
  buildActionRows();
  renderDevice();
  setText($('chase')?.querySelector('.webgl-error'), t(currentLang, 'agents.scene.webgl_error'));
  syncPlayButton();
  draw(state.play.clock.time, true);
}
```

**Edit I: `applyTheme()` re-tints the chase view.** Replace:

```js
  document.documentElement.dataset.theme = theme;
```

with:

```js
  document.documentElement.dataset.theme = theme;
  chase?.setTheme(theme, laneColours());
```

- [ ] **Step 4: Append the pause-panel rules to `app/static/sim/agents.css`**

Append at the end of the file:

```css
/* pause panel: five rows, each a bar from lo to hi with a tick at the neutral
   value and one dot per car at the APPLIED value */
.weights-line{margin:6px 0 10px;font-size:10px;line-height:1.7;color:var(--ink-2)}
.weights-line:empty{display:none}
.actions{display:flex;flex-direction:column;gap:10px}
.action-row{padding-bottom:9px;border-bottom:1px solid var(--hairline)}
.action-head{display:flex;justify-content:space-between;align-items:baseline;gap:8px;font-size:10px}
.action-label{font-weight:600}
.action-unit{font-size:9px;color:var(--muted)}
.gauge{position:relative;height:17px;margin:6px 5px 0;direction:ltr}
.gauge::before{content:"";position:absolute;left:0;right:0;top:7px;height:3px;border-radius:2px;background:var(--track-bg)}
.gauge-tick{position:absolute;top:1px;width:1px;height:15px;background:var(--muted-2)}
.gauge-dot{position:absolute;width:9px;height:9px;margin-left:-6px;border-radius:50%;border:1.5px solid var(--paper)}
.gauge-dot.sighted{top:-1px;background:var(--agent-sighted)}
.gauge-dot.blind{top:7px;background:var(--agent-blind)}
.gauge-ends{display:flex;justify-content:space-between;margin:0 5px;font-size:8px;color:var(--muted-3);direction:ltr}
.tick-note{margin:2px 0 5px;font-size:8px;line-height:1.6;color:var(--muted-2)}
.action-values{display:grid;grid-template-columns:1fr 1fr;gap:4px 12px}
.car-value{display:flex;flex-wrap:wrap;align-items:center;gap:0 6px;min-width:0}
.car-value .value{font-size:13px;font-weight:600;font-variant-numeric:tabular-nums}
.car-value small{flex-basis:100%;font-size:9px;line-height:1.6;color:var(--muted)}
.car-value small.held-line{color:var(--estimated-ink)}
.seen{display:flex;gap:6px;align-items:baseline;margin:10px 0 0;font-size:10px;line-height:1.7}
.seen:empty{display:none}
.seen::before{content:"";width:8px;height:8px;border-radius:50%;flex-shrink:0}
.seen.sighted::before{background:var(--agent-sighted)}
.seen.blind::before{background:var(--agent-blind)}
.car-readings{margin-top:10px}
.car-readings>div{display:flex;flex-direction:column;gap:4px;padding:8px 0;border-top:1px solid var(--hairline)}
.car-readings dt{font-size:9px}
.car-readings dd{display:grid;grid-template-columns:1fr 1fr;gap:8px;direction:inherit}
.car-readings dd>span{display:flex;align-items:baseline;gap:6px;font-size:10px;line-height:1.6}
.car-readings dd b{font-size:13px;font-weight:600;font-variant-numeric:tabular-nums}
.car-readings .lane-dot{align-self:center}
.lane-stopped{margin:8px 0 0;padding:6px 8px;border-radius:5px;background:var(--error-bg);color:var(--error-ink);font-size:10px}
.device-line{margin:8px 0 0;font-size:9px;line-height:1.7;color:var(--muted)}
.device-line:empty{display:none}
.device-warning{display:block;margin-top:4px;color:var(--warn-ink)}
@media(max-width:760px){
.action-values,.car-readings dd{grid-template-columns:1fr}
}
```

- [ ] **Step 5: Run to verify it passes**

Run:
```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
node --check app/static/sim/agents.mjs && echo syntax-ok
$PY -m unittest app.test_agents.PageTests -v
node --test app/static/sim/agents-page.test.mjs
node --test "app/static/sim/*.test.mjs"
```
Expected:
- `syntax-ok`.
- `Ran 4 tests` … `OK`.
- agents-page: `ℹ tests 7`, `ℹ pass 7`. The new `t()` calls (pause heading, weights, held, map, seen, torque, device, stopped) are now in the key and placeholder scan.
- The glob: `ℹ fail 0`.

- [ ] **Step 6: Look at the paused moment in a browser**

Start `$PY -m app.server --simulation` in the background, as in Task 9 Step 9. Open `http://localhost:8000/agents?runs=runs_c4&seed=5&ep=1` and press «احسب». Do not press play yet. Expected:
- Once the first frame arrives (about 3 s), the pause panel already reads «القرار المطبَّق من الثانية 0 إلى 1», with values in all five rows.

Wait for the end label to stop moving, drag the timeline to about 05:12 and leave it paused. Expected:
- The chase view shows two cars side by side on the road, with lane chips «يرى الطريق أمامه» (blue) and «لا يرى الطريق أمامه» (amber).
- Only the posts that fall inside the view's ~200 m are drawn ahead of the blue lane. At cruise that is the 2 s and 5 s posts; the 15 s and 30 s horizons lie about 540 m and 1080 m ahead. All four posts are visible only during the launch. The profile carries all four ticks at every moment.
- The pause panel reads «القرار المطبَّق من الثانية 312 إلى 313», with the grade and the weights line.
- It has five rows with a blue and an amber dot on each bar. The spark, lambda and boost rows carry the «بلا تعديل» note; the fan and pump rows carry the tick_duty note.
- Where held, a second line reads «أمر به …؛ قيّده حد سرعة التغيير». Row 2 shows «ضغط المشعب الآن … كيلوباسكال» for each car.
- The seen lines read «بعد 2 ث: …٪ · بعد 5 ث …» for the blue car and «… 0 · 0 · 0 · 0» for the amber car.
- Damage, turbine `… °C / 849.9 °C`, torque under its «العزم المُسلَّم مقابل المطلوب» label, the model caveat, the device line and the fingerprint time are shown.
- Pressing play moves the panel; pausing holds it.

Stop the server.

- [ ] **Step 7: Commit**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
test "$(git branch --show-current)" = JMF-2340550-sep17 || { echo "not on JMF-2340550-sep17"; exit 1; }
git add app/static/sim/agents.mjs app/static/sim/agents.css app/test_agents.py
$PY verify_docs.py | tail -1
OUT=$(mktemp -d)
$PY -m app.test_replay > "$OUT/replay.txt" 2>&1; tail -1 "$OUT/replay.txt"
{
  echo "Agent replay M1 task 10: the pause panel and the chase view"
  echo
  echo "The five APPLIED actions per car (the command only where the rate limit"
  echo "held it), row 2 as a ceiling offset beside the agent's own map_kpa, what"
  echo "each car was given (four horizons / its real zeros), damage so far,"
  echo "turbine against the limit, torque delivered against requested, the"
  echo "device line. The chase view is a dynamic import: without Three.js the"
  echo "rest of the page still renders. PageTests pin both (static graph scan,"
  echo "cars read only through carOf)."
  echo
  echo '$ python -m app.test_replay'
  cat "$OUT/replay.txt"
  echo
  echo "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
} > "$OUT/msg.txt"
git commit -F "$OUT/msg.txt"
git log -1 --stat
```
Expected: verify_docs prints `All N checks pass (...)`, and test_replay prints `49 of 49 checks pass`. The commit lists three files.

---


---

### Task 11: M1 verification: every suite, --full, the browser at 1440 and 390 px against the misreading table, milestone commit

**Files:**
- Modify: `docs/superpowers/specs/2026-09-26-agent-replay-design.md`: two amendments in Step 7. One is to section 5 "Preview"; the other is to section 10, the "M1 Verify" list.
- Nothing else in the repository. The browser-check script and every captured output live in the session scratchpad, outside the repository. Each block below starts by exporting `SCRATCH` as that directory, for example `export SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/<project>/<session>/scratchpad` as the system prompt names it. It is never the repository and never `%TEMP%` itself, and the blocks refuse to run without it.

**Interfaces:**
- Consumes: everything from Tasks 1 to 10, and the misreading table and layout of design section 6.
- Produces: a milestone commit on `JMF-2340550-sep17` carrying the design amendments. Its message carries the output of every suite. Any fix found here gets its own commit first, with the same outputs pasted in.

Two corrections to the skeleton and the design, both measured on 26 Sep:
- `python -m app.test_replay` prints `49 of 49 checks pass`, while `python -m app.test_replay --full` prints `59 of 59 checks pass` and takes about 3 minutes. The design's "--full at 49" is the default run's count. No commit may claim 49 for `--full`; read both counts from your runs.
- The design checks M1 "with `app\start-simulation.ps1` running". That script's bare `python` resolves to the repository's `.venv`, which has no stable-baselines3 and no torch, so `/api/agents/episode` answers 503. This task starts the server with `$PY` instead. Step 7 amends both design lines.

The design amendments that belong to Task 6 (device and versions travel outside `meta`) and Task 8 (half-width 1.49) are not made here.

- [ ] **Step 1: The new suite, default**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
export SCRATCH="${SCRATCH:?set SCRATCH to the session scratchpad}"; OUT="$SCRATCH/m1-out"; mkdir -p "$OUT"
$PY -m app.test_agents > "$OUT/agents.txt" 2>&1; echo "exit $?"; tail -5 "$OUT/agents.txt"
grep -n "device\|UNPROVEN" "$OUT/agents.txt"
```
Expected:
- `exit 0`, and `OK` near the end. This takes about 3 minutes; the proof alone takes about 2.5.
- The proof prints its device line with `cuda`.
- `UNPROVEN` does not appear. If `agent path UNPROVEN on this machine` is printed, `runs_c4/` or SB3 was not found and the milestone cannot claim the `==` proof. Stop and find out why.

- [ ] **Step 2: The new suite, --full**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
export SCRATCH="${SCRATCH:?set SCRATCH to the session scratchpad}"; OUT="$SCRATCH/m1-out"
$PY -m app.test_agents --full > "$OUT/agents_full.txt" 2>&1; echo "exit $?"; tail -5 "$OUT/agents_full.txt"
```
Expected: `exit 0` and `OK`. `test_phase_d_pair_full` runs and passes; it does not print as skipped.

- [ ] **Step 3: The unchanged suites**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
export SCRATCH="${SCRATCH:?set SCRATCH to the session scratchpad}"; OUT="$SCRATCH/m1-out"
$PY -m app.test_simulation > "$OUT/simulation.txt" 2>&1; echo "exit $?"; tail -3 "$OUT/simulation.txt"
$PY -m app.test_replay > "$OUT/replay.txt" 2>&1; echo "exit $?"; tail -1 "$OUT/replay.txt"
$PY -m app.test_replay --full > "$OUT/replay_full.txt" 2>&1; echo "exit $?"; tail -1 "$OUT/replay_full.txt"
node --test "app/static/sim/*.test.mjs" > "$OUT/node.txt" 2>&1; echo "exit $?"; grep "ℹ tests\|ℹ pass\|ℹ fail" "$OUT/node.txt"
```
Expected:
- `Ran 15 tests` … `OK`, the recon's count.
- `49 of 49 checks pass`, then `59 of 59 checks pass` for `--full`. Both were measured on 26 Sep in the scratch assembly with every new `app/*.py` file present.
- Node: `ℹ fail 0`. The pass count is the lab's 30, plus Task 7's and Task 8's tests, plus agents-page's 7; the scratch assembly printed `ℹ tests 62`. Record the number your run prints.

- [ ] **Step 4: Save the browser check to the scratchpad (not the repository)**

Save as `$SCRATCH/check-agents-page.mjs`. It drives the installed Chrome through the DevTools protocol, using Node 24's built-in `fetch` and `WebSocket`, so it needs no package. It prints PASS or FAIL per check and saves screenshots.

Every view shares one Chrome profile, and the page remembers the theme and language it last applied. So each view writes its own choice to the page's two `localStorage` keys before loading the episode URL. It then asserts that `data-theme`, `lang` and the computed `--agent-sighted` (`#72a9e6` dark, `#2f6db0` light) are the ones it asked for. Without that step, the first view's stored `light` outranks the emulated dark scheme, and both "dark" screenshots come out light while every line still says PASS.

It was run on 26 Sep against a scratch assembly of Tasks 1 to 10, with a freshly started server, and printed `ALL PASS` (99 PASS lines). On the first, uncached view the first frame came at 2.6 s, and `before play, the panel already shows second 0 to 1` passed.

```js
// M1 browser check for /agents. Scratchpad tool, NOT repository code: drives
// the installed Chrome through the DevTools protocol (Node 24 has fetch and
// WebSocket built in), prints what it reads off the page, saves screenshots.
//   node check-agents-page.mjs [base-url] [out-dir]
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const BASE = process.argv[2] || 'http://127.0.0.1:8000';
const OUT = process.argv[3] || '.';
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const PORT = 9335;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const problems = [];
const expect = (ok, what) => { console.log(`${ok ? 'PASS' : 'FAIL'}  ${what}`); if (!ok) problems.push(what); };

mkdirSync(join(OUT, 'chrome-profile'), { recursive: true });
const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${join(OUT, 'chrome-profile')}`, '--no-first-run', '--use-angle=swiftshader',
  '--enable-unsafe-swiftshader', '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
for (let i = 0; i < 100; i++) { try { await fetch(`http://127.0.0.1:${PORT}/json/version`); break; } catch { await sleep(100); } }

async function open({ width, height, mobile = false, dark = false }) {
  const target = await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: 'PUT' })).json();
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise(r => ws.addEventListener('open', r, { once: true }));
  let id = 0;
  const pending = new Map();
  const errors = [];
  ws.addEventListener('message', ev => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); return; }
    if (msg.method === 'Runtime.exceptionThrown') errors.push(msg.params.exceptionDetails.exception?.description || 'exception');
    if (msg.method === 'Runtime.consoleAPICalled' && msg.params.type === 'error') errors.push(msg.params.args.map(a => a.value ?? a.description).join(' '));
    if (msg.method === 'Log.entryAdded' && msg.params.entry.level === 'error' && !/favicon/.test(msg.params.entry.url || '')) errors.push(`${msg.params.entry.text} ${msg.params.entry.url || ''}`);
  });
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    id += 1;
    pending.set(id, m => (m.error ? reject(new Error(`${method}: ${m.error.message}`)) : resolve(m.result)));
    ws.send(JSON.stringify({ id, method, params }));
  });
  for (const m of ['Runtime.enable', 'Log.enable', 'Page.enable']) await send(m);
  await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile });
  await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: dark ? 'dark' : 'light' }] });
  const page = {
    errors,
    async goto(url, settle = 2000) { await send('Page.navigate', { url }); await sleep(settle); },
    async eval(expression) {
      const r = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
      if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
      return r.result.value;
    },
    async shot(name) {
      const m = await send('Page.getLayoutMetrics');
      const r = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true,
        clip: { x: 0, y: 0, width: m.cssContentSize.width, height: m.cssContentSize.height, scale: 1 } });
      writeFileSync(join(OUT, name), Buffer.from(r.data, 'base64'));
      console.log(`      screenshot ${join(OUT, name)}`);
    },
    raw: send,
    close() { ws.close(); },
  };
  return page;
}

const txt = id => `(document.getElementById('${id}')?.textContent || '')`;
const click = id => `document.getElementById('${id}').click()`;
const seekTo = s => `(() => { const e = document.getElementById('seek'); e.value = '${s}'; e.dispatchEvent(new Event('input')); })()`;
const apiCalls = `performance.getEntriesByType('resource').filter(e => e.name.includes('/api/agents')).length`;
async function until(page, expr, ms) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) { if (await page.eval(expr)) return Date.now() - t0; await sleep(200); }
  return null;
}

try {
  for (const view of [
    { name: '1440-light-ar', width: 1440, height: 900 },
    { name: '390-dark-ar', width: 390, height: 844, mobile: true, dark: true },
    { name: '1440-dark-en', width: 1440, height: 900, dark: true, lang: 'en' },
    { name: '390-light-en', width: 390, height: 844, mobile: true, lang: 'en' },
  ]) {
    console.log(`\n== ${view.name}`);
    const page = await open(view);
    await page.goto(`${BASE}/agents`);
    expect(await page.eval(`document.getElementById('compute').disabled`), 'no query: «احسب» is disabled');
    // Every view shares one Chrome profile, and the page remembers the theme
    // and language it last applied, which would outrank the emulated
    // prefers-color-scheme. So each view writes its own choice first, then
    // proves the page rendered it: a dark view that rendered light must FAIL.
    const theme = view.dark ? 'dark' : 'light';
    const lang = view.lang || 'ar';
    await page.eval(`localStorage.setItem('grad.sim.theme', '${theme}'); localStorage.setItem('grad.sim.lang', '${lang}')`);
    await page.goto(`${BASE}/agents?runs=runs_c4&seed=5&ep=1`);
    const shown = await page.eval(`({ theme: document.documentElement.dataset.theme, lang: document.documentElement.lang,
      sighted: getComputedStyle(document.documentElement).getPropertyValue('--agent-sighted').trim() })`);
    expect(shown.theme === theme && shown.lang === lang, `the view renders the theme and language it asked for (${shown.theme}, ${shown.lang})`);
    expect(shown.sighted === (view.dark ? '#72a9e6' : '#2f6db0'), `--agent-sighted is the ${theme} value (${shown.sighted})`);
    expect(await page.eval(apiCalls) === 0, 'nothing is requested before «احسب»');
    expect(await page.eval(`!document.getElementById('scene-prompt').hidden`), 'the scene asks for a choice first');
    const t0 = Date.now();
    await page.eval(click('compute'));
    const firstTitle = await page.eval(txt('load-title'));
    const profileMs = await until(page, `!!document.querySelector('#profile svg')`, 5000);
    expect(profileMs !== null, `the profile draws right after «احسب» (${profileMs} ms)`);
    expect(/networks|الشبكتين/.test(firstTitle), `the loading card first says «تحميل الشبكتين…» (${firstTitle})`);
    const firstFrameMs = await until(page, `!document.getElementById('play').disabled`, 60000);
    console.log(`      first frame after ${firstFrameMs} ms (about 5 s on the first build after a server start)`);
    const heading0 = await page.eval(txt('pause-heading'));
    expect(/\b0\b.*\b1\b/.test(heading0), `before play, the panel already shows second 0 to 1 (${heading0})`);
    const readyMs = await until(page, `document.getElementById('loading').hidden && !document.getElementById('play').disabled`, 240000);
    expect(readyMs !== null, `the episode is ready (${((Date.now() - t0) / 1000).toFixed(1)} s)`);
    // At 130 s the 2 s and 5 s horizons are still on the flat and the 15 s and
    // 30 s ones already on the climb (it starts at 141 s): two ramp colours.
    await page.eval(seekTo(130));
    await sleep(600);
    const ramp = await page.eval(`[...document.querySelectorAll('#profile .profile-tick')]
      .map(e => e.getAttribute('visibility') === 'visible' ? getComputedStyle(e).stroke : null)`);
    expect(ramp.length === 4 && ramp.every(Boolean), 'four preview ticks on the profile');
    expect(ramp[0] === ramp[1] && ramp[2] === ramp[3] && ramp[1] !== ramp[2],
      `the ticks are coloured by the grade there (${ramp.join(' | ')})`);
    const km = await page.eval(`[...document.querySelectorAll('#profile .profile-km')].map(e => e.textContent)`);
    expect(km.length === 6 && /25/.test(km[5]), `the profile has a km scale (${km.join(', ')})`);
    await page.eval(seekTo(312.4));
    await sleep(800);
    const p = await page.eval(`({
      heading: ${txt('pause-heading')}, weights: ${txt('weights-line')},
      rows: document.querySelectorAll('.action-row').length,
      held: [...document.querySelectorAll('.held-line')].filter(e => !e.hidden).length,
      maps: [...document.querySelectorAll('.map-line')].filter(e => !e.hidden).map(e => e.textContent),
      seenS: ${txt('seen-sighted')}, seenB: ${txt('seen-blind')},
      damage: [${txt('damage-sighted')}, ${txt('damage-blind')}], turb: ${txt('turb-sighted')},
      torque: ${txt('torque-sighted')}, device: ${txt('device-line')}, strip: ${txt('strip-verdict')},
      short: ${txt('verdict-short')}, badge: ${txt('sim-badge')}, dt: ${txt('dt-caption')},
      ve: ${txt('profile-ve')}, rise: ${txt('rise-caption')}, slope: ${txt('chase-caption')},
      cites: [...document.querySelectorAll('#verdict-lines figcaption')].map(f => f.textContent),
      scored: ${txt('verdict-scored')}, illustration: ${txt('illustration-note')},
      canvas: !!document.querySelector('#chase canvas'), chaseError: ${txt('chase')},
      scroll: document.documentElement.scrollWidth,
      nav: [...document.querySelectorAll('.topbar nav a')].map(a => getComputedStyle(a).display !== 'none' && a.getBoundingClientRect().right <= innerWidth + 0.5),
    })`);
    console.log(JSON.stringify(p, null, 1));
    expect(p.rows === 5, 'five action rows');
    expect(p.maps.length === 2, 'row 2 shows each car\'s manifold pressure');
    expect(p.cites.includes('results/PREREGISTRATION_C4.md:41-43') && p.cites.includes('results/PREREGISTRATION_C4.md:633-635'),
      'the verdict cites PREREGISTRATION_C4.md:41-43 and :633-635');
    expect(p.cites.includes('results/C4_RESULT.txt:42'), 'the verdict cites C4_RESULT.txt:42');
    expect(p.strip && p.strip === p.short, 'the scene strip carries the short verdict line');
    expect(/0 · 0 · 0 · 0/.test(p.seenB), 'the blind car\'s preview inputs read 0 · 0 · 0 · 0');
    expect(/cuda/.test(p.device), 'the device line names cuda');
    expect(p.canvas && !p.chaseError, 'the chase view rendered');
    expect(p.scroll === view.width, `no horizontal scroll (${p.scroll} px)`);
    expect(p.nav.length === 4 && p.nav.every(Boolean), 'all four nav links are visible');
    await page.shot(`agents-${view.name}.png`);
    expect(page.errors.length === 0, `no console errors ${page.errors.join(' | ')}`);
    page.close();
  }

  console.log('\n== a second build starts quickly');
  const page = await open({ width: 1440, height: 900 });
  await page.goto(`${BASE}/agents?runs=runs_c4&seed=5&ep=${process.env.SECOND_EP || 2}`);
  await page.eval(click('compute'));
  const laterMs = await until(page, `!document.getElementById('play').disabled`, 30000);
  expect(laterMs !== null && laterMs < 3000, `first frame of a later build after ${laterMs} ms`);
  page.close();

  console.log('\n== Three.js missing: everything but the chase view still renders');
  const bare = await open({ width: 1440, height: 900 });
  await bare.raw('Network.enable');
  await bare.raw('Network.setBlockedURLs', { urls: ['*three.module.js*', '*three.core.js*'] });
  await bare.goto(`${BASE}/agents?runs=runs_c4&seed=5&ep=1`);
  await bare.eval(click('compute'));
  await until(bare, `!document.getElementById('play').disabled`, 240000);
  await bare.eval(seekTo(200));
  await sleep(800);
  const b = await bare.eval(`({ chase: ${txt('chase')}, canvas: !!document.querySelector('#chase canvas'),
    badge: ${txt('sim-badge')}, short: ${txt('verdict-short')}, dt: ${txt('dt-caption')},
    rows: document.querySelectorAll('.action-row').length, profile: !!document.querySelector('#profile svg') })`);
  expect(!b.canvas && b.chase.length > 0, `the chase view says it cannot draw (${b.chase})`);
  expect(b.badge.length > 20 && b.short.length > 20 && b.dt.length > 20 && b.rows === 5 && b.profile,
    'badge, verdict, dt caption, profile and panel all rendered without Three.js');
  expect(bare.errors.every(e => /agent-scene|three/.test(e)), `the only console errors are the blocked module (${bare.errors.join(' | ')})`);
  bare.close();

  console.log('\n== /simulation is unchanged');
  const lab = await open({ width: 1440, height: 900 });
  await lab.goto(`${BASE}/simulation`, 4000);
  expect(await lab.eval(`document.querySelectorAll('.topbar nav a').length`) === 3, 'the lab nav still has its three links (the /agents link is M2)');
  expect(await lab.eval(`!!document.querySelector('#world canvas')`), 'the lab scene rendered');
  expect(lab.errors.length === 0, `no console errors on /simulation ${lab.errors.join(' | ')}`);
  lab.close();
} finally {
  chrome.kill();
  console.log(`\n${problems.length ? `${problems.length} FAILED:\n  ${problems.join('\n  ')}` : 'ALL PASS'}`);
}
```

- [ ] **Step 5: Run the server and the check**

Start a fresh server in the background, so that the first view computes rather than reads a cached trace:
```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
ls app/static/vendor/three/three.module.js
$PY -m app.server --simulation
```

Then, in a second call:
```bash
export SCRATCH="${SCRATCH:?set SCRATCH to the session scratchpad}"
mkdir -p "$SCRATCH/m1-check"
node "$SCRATCH/check-agents-page.mjs" http://127.0.0.1:8000 "$SCRATCH/m1-check" 2>&1 | tee "$SCRATCH/m1-check/check.log" | grep -E "^(==|PASS|FAIL|ALL|[0-9]+ FAILED)|first frame"
```
Expected:
- Every line is `PASS`, and the last line is `ALL PASS`.
- Each view prints `PASS  the view renders the theme and language it asked for (dark, ar)` or the matching pair. The two dark views also print `PASS  --agent-sighted is the dark value (#72a9e6)`.
- On the first view, `first frame after ~2500-6000 ms`: the first build after a server start loads torch, SB3 and CUDA. Then `PASS  before play, the panel already shows second 0 to 1 (…)`.
- `PASS  the ticks are coloured by the grade there (…)` shows two different colours: the first two equal and the last two equal. `PASS  the profile has a km scale (0 كم, 5 كم, … 25 كم)` in Arabic, or `0 km` to `25 km` in English.
- `first frame of a later build after` stays under 3000 ms; the scratch runs measured 322 to 1197 ms.
- `the episode is ready` after about 70 to 100 s on the first view, and after 0.2 s on later views, which read the cached trace.
- Four screenshots `agents-1440-light-ar.png`, `agents-390-dark-ar.png`, `agents-1440-dark-en.png` and `agents-390-light-en.png` in `$SCRATCH/m1-check`.

If a line fails, diagnose it before changing anything; the check is not wrong by default. Never loosen the `==` proof or a test to make the page pass.

- [ ] **Step 6: Read the screenshots against the misreading table (design section 6)**

Open the four screenshots with the Read tool. Also open the page yourself at `http://localhost:8000/agents?runs=runs_c4&seed=5&ep=1`, paused at about 05:12. Tick each row:

- [ ] "a recorded drive": the badge reads «محاكاة: سيناريو إجهاد اصطناعي — تسلّق متواصل 13.3٪ عند 130 كم/س في 42 °م…» from meta; the scene strip reads «محاكاة»; the chase ground is a plain grid, with none of the lab's terrain.
- [ ] "this episode is the result": the verdict box quotes the lines with `results/<file>:<line>` and has no close button; «حلقة واحدة لزوج واحد مثال توضيحي، لا نتيجة…» sits under it.
- [ ] "C4 is a clean negative": the short line with «بفارق بذرة واحدة · الاختباران مختلفان · لم يستقر التدريب» appears in the select, the scene strip and the box; the gloss holds the one-seed clause; `PREREGISTRATION_C4.md:633-635` is quoted.
- [ ] "(i)/(ii) mean something unstated": `PREREGISTRATION_C4.md:41-43` is quoted under the reading.
- [ ] "the page picked a representative pair": without a query nothing is selected and «احسب» is disabled. (Listing every pair is M2.)
- [ ] "high damage means poor protection": the weights appear in `#pick-note`, in the episode select and in the pause panel.
- [ ] "the blind car lost a race": one profile marker, the same-place legend, and no winner or difference anywhere on the page.
- [ ] "the sighted agent saw the road": the profile shows four ticks, not a band, each coloured by the grade there. At about 02:10 two are pale and two dark. The chase view shows the posts that fall inside its ~200 m: the 2 s and 5 s posts at cruise, and all four only during the launch. At 36.1 m/s the 15 s and 30 s horizons lie about 540 m and 1080 m ahead, beyond the view.
- [ ] the first build: before play is pressed, the pause panel already reads «القرار المطبَّق من الثانية 0 إلى 1», and the check's `before play` line passed.
- [ ] "the boost trim lowered the pressure": row 2 reads «إزاحة سقف ضغط الشحن», with «ضغط المشعب الآن …» for each car.
- [ ] "a fan at 0.4 cut cooling below the ECU": the tick note under rows 3 and 4 names the modelled 0 / 0.4 / 1.0 schedule. No «حاسوب المحرك» on the page appears without «المنمذَج»; Task 7's test pins this for the strings.
- [ ] "the slope is real / exaggerated": «المقياس الرأسي مضخّم ×3» under the profile, whose km scale runs 0 to 25 km, and «الميل غير مضخّم · السيارة ليست بمقياسها» under the chase view.
- [ ] "a real 3 km climb": «يرتفع الطريق 2 755 م بينما يبقى الضغط 101.3 كيلوباسكال والحرارة 42 °م ثابتين طوال الحلقة».
- [ ] "trained like this": the dt caption reads «…دُرِّبا بخطوة 0.2 ث. مشكلة معروفة لم تُحلّ (AUDIT2.md H2-2)…».
- [ ] "this is the scored run / artefact": the device line names cuda with the torch and SB3 versions; `#verdict-scored` reads «هذا هو الملف الذي قُيِّم» with each zip sha.
- [ ] "the network's output was applied": the values are applied ones, and the «أمر به …» second line appears only on held actions.
- [ ] "it saved damage by refusing torque": each car shows torque delivered against requested, under the «العزم المُسلَّم مقابل المطلوب» label.
- [ ] "the temperature was measured": «حرارة التيربو تقدير من النموذج، وليست قراءة حساس.» sits under the readings.
- [ ] Layout at 390 px: the order is badge, picker, verdict, chase (4:3), timeline, profile, pause panel; values stack by car; there is no horizontal scroll; all four nav links show.
- [ ] Layout at 1440 px: the main column holds chase (16:9), timeline and profile; the side column holds picker, verdict and pause panel.
- [ ] Theme: tick this only if the check's two dark views printed `(dark, …)` and `--agent-sighted is the dark value (#72a9e6)`. Then confirm by eye that `agents-390-dark-ar.png` and `agents-1440-dark-en.png` show the dark palette. The lane colours are blue and amber in both themes, never red or green.
- [ ] Language: the English screenshots keep every caption above, in English.
- [ ] `/simulation` still loads and plays a drive; its nav still has three links, because the link to `/agents` is M2.
- [ ] Out of M1 (not checked here): Phase D and D2 rows, NOT BLIND, the table-row qualifier, jev.

Stop the server.

- [ ] **Step 7: Amend the design where M1 showed it wrong or silent**

Two edits to `docs/superpowers/specs/2026-09-26-agent-replay-design.md`, with the Edit tool; each old string occurs once. Each amendment says what it replaced, in the project's usual form.

In section 5, replace:

```markdown
**Preview.** One marker at each `PREVIEW_S` horizon, coloured by the grade read there, on a single-hue ramp from 0 to 16 %. There is no continuous band, because the agent saw four numbers, not a stretch of road.
```

with:

```markdown
**Preview.** One marker at each `PREVIEW_S` horizon, coloured by the grade read there, on a single-hue ramp from 0 to 16 %: the profile's ticks and the chase view's posts use the same ramp. There is no continuous band, because the agent saw four numbers, not a stretch of road.

- The profile always carries all four.
- The chase view shows only the posts inside its view of about 200 m. At 130 km/h the 15 s and 30 s horizons lie about 540 m and 1080 m ahead, so after the launch it shows the 2 s and 5 s posts.
- *(Amended while building M1, 26 September: this paragraph did not say which view carries which markers, and the profile's ticks were drawn in the lane colour.)*
```

In section 10, under M1 **Verify:**, replace:

```markdown
  - the lab suites (including `app.test_replay --full` at 49) and the node glob pass unchanged;
  - with `app\start-simulation.ps1` running, the profile draws at once;
```

with:

```markdown
  - the lab suites and the node glob pass unchanged: `app.test_replay` prints 49 of 49 and `app.test_replay --full` 59 of 59, each read from its run;
  - with the server started as `python -m app.server --simulation` on the system interpreter, the profile draws at once. `app\start-simulation.ps1` calls bare `python`, which resolves to the repository's `.venv`; that has FastAPI but neither stable-baselines3 nor torch, so `/api/agents/episode` would answer 503. Its banner also names only `/simulation`. M2, which touches the lab's entry points, can fix both;
  - *(Amended while building M1, 26 September: these two lines read "including `app.test_replay --full` at 49" and "with `app\start-simulation.ps1` running". 49 is the default run's count.)*
```

Then check that the checker still passes with the amended text:
```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
git add docs/superpowers/specs/2026-09-26-agent-replay-design.md
$PY verify_docs.py | tail -1
```
Expected: `All N checks pass (...)`. In the scratch assembly, with these two amendments and every M1 file git-added, it read `All 67 checks pass (782 figure mentions scanned in the documents).`

- [ ] **Step 8: Confirm nothing outside M1 moved**

```bash
export GIT_OPTIONAL_LOCKS=0
git status --porcelain
git log --oneline -12
git diff --stat 564927e..HEAD -- results plant.py thermal.py engine_env.py random_road.py fingerprint.py train.py evaluate.py run_phase_d.py app/static/simulation.html
```
Expected:
- `git status --porcelain` prints exactly one line, `M  docs/superpowers/specs/2026-09-26-agent-replay-design.md`, staged in Step 7. Every other M1 file was committed in its own task.
- The log shows the M1 task commits on `JMF-2340550-sep17`.
- The `git diff --stat` line prints nothing. `564927e` is the design-approval commit, and none of these paths may move in M1. `runs*/` are gitignored; `NoWriteTests` covers them.

- [ ] **Step 9: The milestone commit**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
test "$(git branch --show-current)" = JMF-2340550-sep17 || { echo "not on JMF-2340550-sep17"; exit 1; }
export SCRATCH="${SCRATCH:?set SCRATCH to the session scratchpad}"; OUT="$SCRATCH/m1-out"
git add docs/superpowers/specs/2026-09-26-agent-replay-design.md
$PY verify_docs.py > "$OUT/verify_docs.txt" 2>&1; tail -1 "$OUT/verify_docs.txt"
{
  echo "Agent replay M1: verified -- one C4 pair, one episode, side by side"
  echo
  echo "The == proof ran through the store's worker thread on this machine (device"
  echo "below). Browser check at 1440 and 390 px, light and dark (each view's"
  echo "theme asserted, not assumed), Arabic and English, against the design's"
  echo "misreading table; screenshots kept in the session scratchpad, not in the"
  echo "repository."
  echo
  echo "Design amended in two places, each marked in the text: section 5 now says"
  echo "the profile carries all four preview markers and the chase view only those"
  echo "within its ~200 m, on one ramp; section 10's M1 Verify now reads 49 for"
  echo "app.test_replay and 59 for --full, and starts the server on the system"
  echo "interpreter (start-simulation.ps1's bare python is the .venv, which has no"
  echo "stable-baselines3 or torch, so /agents answered 503)."
  echo
  echo '$ python -m app.test_agents   (tail)'
  tail -15 "$OUT/agents.txt"
  grep "device" "$OUT/agents.txt"
  echo
  echo '$ python -m app.test_agents --full   (tail)'
  tail -5 "$OUT/agents_full.txt"
  echo
  echo '$ python -m app.test_simulation   (tail)'
  tail -3 "$OUT/simulation.txt"
  echo
  echo '$ node --test "app/static/sim/*.test.mjs"   (summary)'
  grep "ℹ tests\|ℹ pass\|ℹ fail" "$OUT/node.txt"
  echo
  echo '$ python verify_docs.py   (last line)'
  tail -1 "$OUT/verify_docs.txt"
  echo
  echo '$ python -m app.test_replay --full'
  cat "$OUT/replay_full.txt"
  echo
  echo "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
} > "$OUT/msg.txt"
git commit -F "$OUT/msg.txt"
git log -1 --stat
git log -1 --format=%B | tail -3
```
Expected:
- `All N checks pass (...)` from verify_docs.
- The commit lists one file, the design document.
- The message carries `59 of 59 checks pass` from `--full` and ends with the Co-Authored-By line.

Do not push. Name the destination branch (`JMF-2340550-sep17`) to Jad and push only when he asks. Leave the server stopped, or running for Jad if he prefers.


---

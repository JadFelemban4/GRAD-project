> **STATUS: APPROVED BY JAD, 26 September 2026** — through the three questions
> of section 11 (he chose to answer only the decisions that are his, and to take
> the rest as drafted and reviewed; see the walkthrough log at the end). Produced
> the same day by a design workflow: three independent designs (minimal-first,
> the committee's view, correctness and hard rules), a judge that chose the
> minimal one as the base and named grafts, one synthesis, three adversarial
> reviewers (31 issues raised: 6 major, 25 minor, 0 blockers) and one revision.
> Inputs: `2026-09-26-agent-replay-recon.md` (Jad's seven decisions are its
> section 12). The implementation plan is the next document; nothing is built
> from this file directly.

## 1. Goal and non-goals

**Goal.** A new page, `/agents`, served only by `python -m app.server --simulation`. It opens with nothing selected. The viewer picks, in order:

1. an experiment;
2. a pair (the sighted and the blind agent of one seed);
3. one of the 20 frozen test **episodes**. Each episode is a road plus three preference weights, and the page shows both.

Then the viewer presses «احسب» (compute). The server computes that episode live under the scoring protocol (dt 1.0, 719 steps) and streams frames while it runs. Both cars are drawn side by side on a road built from the episode's own grade.

At any paused second the page shows, for each agent:

- the five actions it applied (Arabic names, physical units), and what the network commanded;
- what the sighted agent saw of the road ahead;
- each car's damage so far.

Beside the agents sits the experiment's preregistered verdict, quoted word for word from `results/`, together with a short verdict line that keeps its qualifiers. A hidden panel, unlocked by a gesture, lets Jad ask two language models about that same paused moment, jev (an external service) and Laya (on this machine), one button each, and shows each model's choice next to the agents' actions. Every number on the page comes from a tracer that a test proves `==` to `evaluate.run_episode`.

**Non-goals.**

- **No writes and no training.** No training, no evaluation, and no writes into `runs*/`, `results/` or anywhere else. Traces live in memory only.
- **No statistics.** The page computes no statistic and no difference between the cars. The seed's table row is quoted, not computed.
- **Neither model drives an episode.** That is deferred, and nothing here blocks it.
- **`/simulation` behaves exactly as it does today.**
- **No recorded-drive data** appears on this page or goes to jev.
- **Cut from the page:** charts, the gear strip, a baseline-ECU twin (`env.thermal_base` and `map_b_prev` are not the scored "baseline ECU" row, recon §8) and comparator cars.

**What was cut, and why each cut is safe:**

| cut | why safe |
|---|---|
| Charts, gear strip, H/τ card | Not asked for. Gear is not in `info`. The frames can feed charts later without a format change. |
| Orbit and zoom in the 3D view | A fixed follow camera is less code, and nothing competes with the footer gesture. |
| The jev SDK | One POST with stdlib `urllib`. That avoids a week-old dependency and its debug logging of request bodies (recon §9). |
| jev caching and retries | One click is one call. That is the spending rule. |
| Pre-importing SB3 at server start | It would add about 3 s to every `--simulation` start for a page that may never be opened. The first build pays it instead (§3.3). |

---

## 2. Units and files

### New Python modules

All seven modules, and the suite beside them, sit at the top level of `app/`, so `app.test_replay`'s `test_read_only` scan covers them unchanged. None is hashed into `plant_sha` (`fingerprint.py:55` hashes plant, thermal and engine_env only).

| module | its one job | interface | depends on (import only) |
|---|---|---|---|
| `app/agent_trace.py` | Step N envs of one frozen episode in lockstep, mirroring `run_episode`; build the road from the cycle | `STEPS = 719`<br>`PREVIEW = slice(14, 14+len(PREVIEW_S))`<br>`GRADE_OBS_SCALE = 12.0`<br>`episode(protocol, idx) -> {seed, weights, road}`<br>`build_cycle(ep) -> dict`<br>`route(cycle) -> dict`<br>`run_lanes(lanes, ep, on_frame=None) -> list[dict]`<br>`jsonable(x)` | `evaluate`: `DT`, `DURATION`, `EPISODES`, `EPISODES_D2`<br>`engine_env`: `SupervisoryTunerEnv`, `make_grade_climb`, `PREVIEW_S`<br>`random_road.climb`<br>`app.replay.finite` |
| `app/agent_catalog.py` | Find agents; decide status, protocol, arm and budget; check each zip against the scored one; quote verdicts and table rows | `live_fingerprint(protocol)` (cached)<br>`read_agent(runs, name, root) -> dict`<br>`discover(root=ROOT) -> list[dict]`<br>`find_pair(runs, seed, root=ROOT)` (raises `KeyError`/`Refused`)<br>`scored_shas(prefix, seed, root) -> dict or None`<br>`verdict(prefix, root=ROOT) -> {state, lines, short, cells}`<br>`table_rows(prefix)`<br>`VERDICT_LINES`, `SHORT_VERDICT` | `fingerprint`: `read`, `compare`, `plant_fingerprint`, `model_budget`, `format_budget`, `running_pid`<br>`run_phase_d`: `result_prefix`, `CLOSED_PREFIX`<br>`analyse_phase_d2.load`<br>`analyse_c4.BUDGET` (the regex `analyse_c4` itself uses on the `model …: … zip sha` line, `analyse_c4.py:83`) |
| `app/agent_api.py` | Routes, the default model loader, and the single-worker episode store | `install(app, store=None, jev_send=None, laya=None) -> None`<br>`load_pair(runs, seed) -> (m_s, m_b)`<br>`class EpisodeStore(loader=load_pair, tracer=run_lanes, keep=2)` with `.poll(key, since, preempt) -> dict` and `.trace(key) -> Trace or None` | the two modules above; `evaluate.agent_policy`; `app.replay.BuildCancelled`; (M3, imported inside `install`) `app.jev` and `app.laya_bridge` (`LayaBridge`, `LayaError`) |
| `app/model_questions.py` **[new; review change C4]** | The one question both models are asked, and the one way their answers become actions | `LEVELS`, `NET`, `OPTIONS`, `QUESTIONS`<br>`decode(obs) -> dict`<br>`build_state(trace, step) -> dict`<br>`to_action(answers) -> dict` (raises `BadAnswer`)<br>`user_setting(env_var, file_name) -> (value, source)` | `engine_env`: `ACT_LO`, `ACT_HI`, `neutral_action`, `PREVIEW_S`, `TURB_PROTECT_K`, `OIL_PROTECT_K`<br>`app.agent_api.Trace` |
| `app/jev.py` **[changed from §7: slimmed]** | Send one question set to jev and return its answer | `load_key()`<br>`build_request(trace, step) -> dict`<br>`ask(trace, step, send=_send, clock=perf_counter) -> dict` | `model_questions`, `urllib.request` |
| `app/laya_bridge.py` **[new]** | Start, keep and stop Laya's worker; ask it one question set | `load_home() -> (python, model_dir, source)`<br>`class LayaBridge(command=None, start_timeout=90, answer_timeout=20)` with `.status()`, `.ask(trace, step)`, `.close()`<br>`worker_env() -> dict`<br>Building a `LayaBridge` reads no file and starts nothing | `model_questions`, `subprocess`, `threading`, `queue`, `json`, `os`, `sys`, `pathlib`, `atexit` |
| `app/laya_worker.py` **[new]** | Runs **only** under Laya's own `.venv` python and is never imported by the server. Loads Laya once and answers one JSON line per request | `python -I -B -X utf8 laya_worker.py <model_dir>` | stdlib, `laya`, `torch`. It imports `socket` only to refuse it (§7.5) |
| `app/test_agents.py` | The new suite (§9) | `python -m app.test_agents [--full]` | all of the above |

`jsonable` fixes a failure the original draft would have shipped. `app.replay.finite()` (`replay.py:31-32`) accepts only Python `int`/`float`, and numpy `float32` is neither. Measured today, `finite(env.prev_act[3])` returns `None`, so as drafted the page would have shown null for every action and every preview value. `jsonable` therefore converts first:

- numpy arrays go through `.tolist()`, and each element then through `finite`;
- numpy `bool_` becomes Python `bool`;
- scalars become `finite(float(x))`.

It applies to every frame field and to `meta.act` and the `road` arrays.

### New frontend files

| file | its one job |
|---|---|
| `app/static/agents.html` | The RTL shell. Links `sim/style.css` (the lab's tokens) and `sim/agents.css`. |
| `sim/agents.mjs` | DOM wiring, polling, clock and panel rendering. Exports nothing. |
| `sim/agents-strings.mjs` | Every string this page uses, in Arabic and English. On import it merges them into `i18n.STRINGS`, and throws on a key collision or on a key present in only one language. |
| `sim/agent-view.mjs` | Pure, node-testable functions: `createEpisodeRoad(road, mPerUnit)`, `episodeAt(frames, road, t)`, `profilePoints(road, {ve, width})`, `previewMarks(road, k, previewS)`, `gaugeFraction(v, lo, hi)`, `playOrWait(clock, computedEnd, done, now)`, `resumeIfStalled(state, newEnd, now)`, `CAR_OFFSET`, `LANE_W`, `ROAD_W`, `ACTIONS` |
| `sim/agent-scene.mjs` | `createChaseScene(host, episodeRoad) -> {update({distance_m, marks}), setTheme, dispose}` |
| `sim/tap-unlock.mjs` (M3) | `createTapUnlock({taps: 10, windowMs: 4000}) -> {tap(nowMs) -> boolean}` |
| `sim/model-panel.mjs` (M3) | Pure panel logic: `askState(view, k)`, `createAnswers()`, `rowView(answer, i)`, `failureOf(httpStatus, body)`, `errorText(code, status, lang, kind)`, `statusLine(name, status, failure, inFlight, lang)`, `MODELS`, `QUESTION_IDS`, `ERROR_CODES` (M3 design §7.2) |
| `sim/agents.css` | Grid and panel rules. It also overrides the lab's phone rule that hides the last nav link. |
| `sim/agent-view.test.mjs`, `sim/agents-strings.test.mjs`, `sim/tap-unlock.test.mjs`, `sim/model-panel.test.mjs`, `sim/agents-page-models.test.mjs` (M3) | Node tests, picked up by the existing glob |

**Reused by import, never copied:**

- `playback.mjs`: `PlaybackClock` and `formatTime`. **`sampleAt` is not reused.** It searches on `frames[i].t` and reads `s_m`/`speed_kmh` (`playback.mjs:21-23`), which agent frames do not carry. `episodeAt` does the lookup.
- `i18n.mjs`: `t`, `applyTranslations`, `resolveLang`, `STRINGS`, `missingKeys`.
- `scene.mjs`: `stage`, `supra`, `ribbonGeometry` (exported by edit 2 below; approved, §11 Q2).

### Edits to existing files: the complete list

1. **`app/server.py`.** In `main()`'s `if a.simulation:` branch (`:298`): `from app.agent_api import install; install(app)`, plus one printed `/agents` URL. Module-level routes do not change, so `--live` and `--replay` never import agent code. In M3, the docstring sentence at `:43` is amended to name the two POSTs, `/api/agents/jev` (an external service) and `/api/agents/laya` (on this machine) (M3 design §7.6).
2. **`app/static/sim/scene.mjs`** (approved, §11 Q2). Add `export` to `function stage` (`:326`), `function ribbonGeometry` (`:453`) and `function supra` (`:580`). This changes no behaviour, and the lab suites are re-run.
3. **`app/static/sim/i18n.mjs`** (approved, §11 Q2). Add one key, `nav.agents`, in both languages, for the link. Every other key lives in `agents-strings.mjs`.
4. **`app/static/simulation.html:39`** (M2). Add one `<a href="/agents" data-i18n="nav.agents">`, inserted **after the first link, not at the end**. The lab's phone rule hides `.topbar nav a:last-child` below 760 px (`style.css:100`), so a link at the end would vanish on phones. This link is the only edit to the page, and it is needed because decision 7 says "linked from it". Under `--live` or `--replay` the link 404s, which is correct.
5. **`.gitignore`** (M3, its own first commit, before any key exists): `.env`, `.env.*`, `*typesafe_key*`. This is a second line of defence only; the key never lives inside the repository (§7).

No lab test file changes. `app.test_simulation`, `app.test_replay --full` and the node glob must pass unchanged; their counts are read from each run.

---

## 3. The tracer and live computation

### 3.1 The mirror (`run_lanes`), copied step for step from `evaluate.py:175-202`

For each lane `(policy, use_preview)`:

1. Build **its own** cycle, as `run_episode` does:
   - Phase D: `make_grade_climb(duration=DURATION, dt=DT)`;
   - `d2` protocol: `RR.climb(start_s, grade, duration=DURATION, dt=DT)`, never `RandomClimb`.
2. `SupervisoryTunerEnv(cycle, dt=DT, seed=seed, use_preview=use_preview)`.
3. `env.reset(seed=seed)`; `env.w = np.asarray(weights, dtype=np.float32)`; `obs = env._obs()`. There is no second reset.

Then loop:

- `a = policy(env, obs)`;
- `obs, r, term, trunc, info = env.step(a)`;
- `ret += r`;
- `peak = max(peak, info["t_turb"])`, starting at `0.0`.

A lane ends on `term or trunc`, which is 719 steps (`engine_env.py:820`). The results match `evaluate.py:199-202` key for key: `ret, damage, fuel, torque_viol, peak_turb = peak − 273.15, knock`.

**Models.**

- The policies are `evaluate.agent_policy(model)`, imported.
- `load_pair` calls `SAC.load(dir + "/final")` with **no device argument**, exactly the call at `evaluate.py:370`. SB3's `"auto"` gives CUDA on this machine.
- `str(model.device)`, `torch.__version__` and `stable_baselines3.__version__` are recorded in `meta` and shown on the page. The two devices are asserted equal.
- SB3 and torch are imported lazily inside the worker. Models are loaded per build and dropped afterwards. jev needs only the stored observations.

### 3.2 Two agents, step-interleaved

At step k the sighted lane steps, then the blind lane, then `on_frame` receives one paired frame.

The proof (§3.6) runs this interleaved path **on the store's worker thread**, so any cross-talk fails `==`. If it ever does, the fix is to find the cause, never to add a tolerance; the fallback is sequential lanes.

A lane that terminates early (non-finite reward, `engine_env.py:819`) stops. Its later entries are `null`, and the page says «توقفت محاكاة هذه السيارة عند الخطوة k» ("this car's simulation stopped at step k").

`lanes` and `cars[]` are lists, so a deferred jev-driven lane would need no format change.

### 3.3 The store: one worker, streaming, cancellable, bounded

`EpisodeStore` follows `ReplayStore`'s policy (`replay.py:275-302`). It is a new class, because `ReplayStore` cannot stream partial frames.

- **Key.** `(runs, seed, idx)`, serialised as `"runs_c4/5/1"`. `runs` must be a name that `discover` returned, never a path.
- **Worker.** One daemon thread, `agent-builder`, building one pair at a time.
  - Any other key gets `busy`.
  - Only `preempt=1` cancels, and only the first request after «احسب» sends it.
  - `on_frame` raises `BuildCancelled` when the cancel event is set, checked every paired step (about 0.1 s).
  - A cancelled or partial trace is never kept.
- **Hooks.** `loader(runs, seed)` defaults to `load_pair`; the proof injects its own model objects, and test 1b checks `load_pair` itself. `tracer` defaults to `run_lanes`, and the store test injects a fake.
- **Errors.** The worker catches `Exception` **and `SystemExit`**, records one fixed message, reports it once, then forgets it. Nothing in the path calls `check_model_fingerprint`.
- **Memory.** One in-flight trace plus at most `keep = 2` finished traces. Each holds its frames, the two result dicts and each lane's 719 × 23 float32 observations (kept server-side for jev): well under 2 MB in all. Nothing goes to disk.
- **Cost.**
  - Plant: about 52 ms per env step, so a pair takes about 75 s, or about 9.6 episode-seconds per wall second (recon §3).
  - First build after server start, measured today: about 5 s before the first frame (import torch 2.7 s, SB3 0.5 s, first `SAC.load` with CUDA initialisation 1.2 s, first predict 0.4 s).
  - Later builds: under 1 s.
  - The page shows «تحميل الشبكتين…» ("loading the two networks…") until the first frame arrives.
  - Playback at 1× to 8× never catches up with the computation; at 16× it waits.

### 3.4 Routes (added by `install(app, store=None, jev_send=None, laya=None)`, only under `--simulation`)

```
GET  /agents                                   -> agents.html
GET  /api/agents/catalog                       (M2, §4)
GET  /api/agents/episode?runs=runs_c4&seed=5&ep=1&since=0&preempt=1
     200 {status: loading|building|ready|busy|error, progress, steps: 719, device,
          frames: frames[since:], meta + road (only when since == 0),
          active: {runs, seed, ep} (busy), message (error)}
     404 unknown runs/seed/ep     409 {status: "refused", problems: [...]}
     503 stable-baselines3 not installed
GET  /api/agents/jev/status                    (M3)
POST /api/agents/jev    body {"trace": "runs_c4/5/1", "step": 312}      (M3 design §7.6)
GET  /api/agents/laya/status                   (M3)
POST /api/agents/laya   body {"trace": "runs_c4/5/1", "step": 312}      (M3 design §7.6)
```

- `road` is computed synchronously on the first request from `build_cycle(ep)`, using only the cycle arrays and no plant.
- Every response carries `Cache-Control: no-store`. The browser polls every 400 ms (the lab's rate) and appends `frames[since:]`.
- A cross-site GET could at worst start a local computation, exactly as the lab's replay route can. It spends nothing and sends nothing off the machine.

`meta` = `{experiment, runs, prefix, protocol, seed, ep, episode: {seed, weights, climb_start_s, grade}, dt: 1.0, train_dt: {sighted, blind}, duration_s: 720, steps: 719, agents: [{tag, arm, budget_line, zip_sha, scored: "match"|"not recorded"}], device, versions: {torch, sb3}, preview_s, act: {lo, hi, slew, neutral_phys}, limits: {turb_c, oil_c}, scenario: {v_kmh, t_amb_c, p_baro_kpa}, verdict}`. It passes through `jsonable`.

`neutral_phys` is `_rescale(neutral_action())`: 0 for the three trims, and 1.0 for the fan and the pump (`engine_env.py:1001-1003`).

### 3.5 Frame fields

Frame k covers the one-second decision taken at t = k s. Every field passes through `jsonable`.

| field | unit | source |
|---|---|---|
| `k` | step | loop index |
| `cars[i].cmd` | network, [−1, 1] | the policy's output `a` |
| `cars[i].act` | [°, λ, kPa, duty 0–1, duty 0.3–1] | `env.prev_act` after the step (`:817`). This is the **applied** action, after rescaling, the slew limit and the bounds (`:724-726`). |
| `cars[i].held` | 5 Python bools | `act != _rescale(cmd)`: where the slew limit held the command back |
| `cars[i].preview_pct` | % grade at each `PREVIEW_S` horizon | `obs[PREVIEW] / 12 × 100`, from the observation passed to `predict`. The blind car's values are its real zeros. |
| `cars[i].map_kpa` | kPa | `env.map_kpa`, the agent's own manifold pressure. Action 2 needs it to be read (§6). |
| `cars[i].turb_c`, `oil_c` | °C, at the end of the second | `info["t_turb"] − 273.15`, `info["t_oil"] − 273.15` |
| `cars[i].torque_nm`, `torque_req_nm` | N·m | `info["torque"]`, `info["torque_req"]` |
| `cars[i].damage` | damage units, cumulative | `float(env.ep["damage"])`, copied |

Grade, speed and distance per step live in `road`, which is sent once.

### 3.6 The proof

`tracer_equals_run_episode`, one process:

```
m_s, m_b = SAC.load("runs_c4/sighted_seed0/final"), SAC.load("runs_c4/blind_seed0/final")
want = [run_episode(agent_policy(m_s), s, w, True,  road=(st, g)),
        run_episode(agent_policy(m_b), s, w, False, road=(st, g))]     # EPISODES_D2[0]
store = EpisodeStore(loader=lambda runs, seed: (m_s, m_b))
poll(("runs_c4", 0, 1), preempt=1) until ready          # on the agent-builder thread
assert store.trace(key).results == want                 # == on the full dicts
```

Because this proof injects its models, a separate test (1b) pins `load_pair` against `evaluate.py:370`. That test checks four things:

- the same `str(device)`;
- `torch.equal` on every tensor of `policy.state_dict()`;
- the same `FP.model_budget` sha;
- that sha against the one `results/c4_seed0.txt:24,26` recorded as scored.

Without that test, a loader that picked a different file or device would pass the `==` proof unnoticed. Tests 1, 1b and 2 run in about 2.5 min, in the default suite. Without `runs_c4/` or SB3, the proof runs through the store on `check_premise.p_neutral`/`p_grade_now` and prints **"agent path UNPROVEN on this machine"**. `--full` adds the Phase D pair `runs/*_seed0` on `EPISODES[0]`.

---

## 4. Discovery, compatibility and verdicts

**Discovery.** `discover(root)` lists `root/runs*/` in sorted order. Inside each it keeps the children matching `^(sighted|blind)_seed(\d+)$` and ignores everything else. A future `runs_X` appears with no code change.

**Status, decided in this order** (`read_agent(runs, name, root)`). Anything not `ready` is listed with its reason and cannot be run.

| # | check | status |
|---|---|---|
| 1 | `FP.running_pid(dir)` is alive (`fingerprint.py:434`) | `training` |
| 2 | `FP.read(meta.json)` is `None` | `incompatible`: "no meta.json: plant unknown (AUDIT2 C2-1)". Both `runs_sixspeed_18sep/` agents stop here. |
| 3 | no `final.zip` | `incomplete` |
| 4 | **evaluate's own rule on evaluate's own string**: `"blind" in f"{runs}/{name}"` (`evaluate.py:369` applied to the path `run_phase_d.py:330` builds) disagrees with the child name's arm or with `not meta["use_preview"]` | `incompatible`: "evaluate.py would have scored this agent as the other arm". This catches a future runs directory whose name contains `blind`. |
| 5 | protocol from `meta.scenario`: `protocol == "random-climb"` means `d2`; no key means `phase-d`; anything else fails | `incompatible`: "unknown protocol" |
| 6 | `FP.compare(meta, live_fingerprint(protocol))` (`:289`, never raises) is non-empty | `incompatible`, naming each field with its stored and live values |
| 7 | otherwise | `ready`, with `budget_line = FP.format_budget(FP.model_budget(final.zip))` and `train_dt` from meta ("not recorded" if absent) |

**The pair check comes after the status check** (`find_pair`). It asks whether these are the agents that were scored.

- `scored_shas(prefix, seed, root)` reads `results/<prefix>_seed<k>.txt` and matches each line against `analyse_c4.BUDGET`.
- For each arm it takes the `zip sha` whose model path ends in that arm's `<arm>_seed<k>`.
- Only C4 records one today (`c4_seed0.txt:24,26`).

| case | result |
|---|---|
| a recorded sha differs from `model_budget(final.zip)["sha"]` | the pair is refused: «ليس الملف الذي قُيِّم» ("not the scored artefact"), with both shas |
| no sha recorded (D2 and Phase D today) | runnable, with «الملف المقيَّم غير مسجَّل في النتائج» ("scored artefact not recorded in results") beside the verdict |
| no result file | «لا ملف نتيجة لهذا الزوج» ("no result file for this pair") |

*(Amended while building M2, 28 September: each arm of a checked pair carries `scored`: `match`, `not recorded`, or `mismatch` when the zip sha that `results/<prefix>_seed<k>.txt` records differs from its `final.zip`. The pair is then refused, and the page says «ليس هذا هو الملف الذي قُيِّم» beside that arm, never "not recorded" beside a line that names the recorded sha. `scored` is null when an earlier check refused the pair first, and the page then claims nothing either way.)*

**Runnability.**

- A pair runs only when both arms are `ready` and the sha check passes.
- The episode route repeats steps 6 and the sha check before every build, and returns 409 without starting a worker.
- If SB3 is not importable, every pair shows "cannot run: stable-baselines3 not installed".
- *(Amended while building M2, 28 September: the page says it ONCE, under the picker, as soon as the catalog arrives (the catalog's `sb3` is false), rather than on every pair option. The pairs stay selectable, so their verdicts and table rows can still be read; «احسب» stays disabled, and the episode route still answers 503.)*

**Live fingerprint.**

- `live_fingerprint()` itself runs `os.environ.setdefault("GIT_OPTIONAL_LOCKS", "0")` before its first call. `plant_fingerprint` runs `git status` (`:250`) through `_git`, which inherits the environment (`:183`), and without the variable `git status` may rewrite `.git/index`. Putting it in `live_fingerprint` rather than `install()` covers the tests that call `discover()` directly.
- The fingerprint is taken once per protocol and cached. The method line says "fingerprint taken at hh:mm; restart the server after changing a hashed file".

**Experiment identity.** `prefix = run_phase_d.result_prefix(dir)` (`:94`). The name is `CLOSED_PREFIX.get(prefix)` (`:113`), or else "`runs_X` (no name recorded)".

**Verdicts are quoted, never computed.** `VERDICT_LINES[prefix]` is a list of `(file, regex, n_lines)`. Each match returns `{file, line, text}`, cited as `file:line`.

| prefix | quoted (checked today) |
|---|---|
| `c4` | `C4_RESULT.txt:42` RESULT: SMALLER THAN THE MEI<br>`:28-30` H1: the effect is smaller than the MEI (50 units), with both tests under it: the sign test (7 of 8 seeds below 50) and the permutation test<br>`:33-34` THE TWO TESTS DISAGREE…<br>`:48` NOT-CONVERGED…<br>`:50-53` THE READING…<br>`PREREGISTRATION_C4.md:41-43`, what (i), (ii) and (iii) mean, directly under the reading<br>`PREREGISTRATION_C4.md:633-643`, item 2 of section 11 whole: "one seed the other way and the cell would be INCONCLUSIVE" … "whether the average effect is below 50 is not settled" |
| `d2` | `PHASE_D2_RESULT.txt:30-33` RESULT: INCONCLUSIVE and its paragraph<br>`:86-89` "Both are C1 agents … never 'preview does not help'" |
| `phase_d` | `PHASE_D_RESULT.txt:26-31` NOT SIGNIFICANT, with its C1 sentence<br>`PHASE_D2_RESULT.txt:65` INCONCLUSIVE [MEI set AFTER…], labelled post-hoc<br>`PHASE_D_RESULT.txt:33-40` AND THE BLINDED ARM IS NOT BLIND… |

*(Amended after the M1 final review, 27 September: the c4 row quoted `C4_RESULT.txt:29`, the sign test's p on its own, and `PREREGISTRATION_C4.md:633-635`, which stopped at "The permutation test," just before its caveat. Both now quote whole items; see the walkthrough log.)*

*(Amended while building M2, 28 September: the d2 row quotes `PHASE_D2_RESULT.txt:30-35`, not `:30-33`. The item runs on to "power_analysis.py predicted this cell BEFORE this experiment ran, from Phase D's measured spread.", and a quote cut before it is the fault the M1 final review called F8. The phase_d post-hoc quote is the whole item, `PHASE_D2_RESULT.txt:65-76`, because `:72-76` is what makes it post-hoc; NOT BLIND is `PHASE_D_RESULT.txt:33-40`, as drafted. The d2 pattern is anchored at the end of its line, so it can never match the bracketed Phase D line at `:65`. The cell name `INCONCLUSIVE (post-hoc)` is authored: the file's own words, `[MEI set AFTER this result -- see below]`, are quoted in full beside it.)*

**Verdict states.**

- **`found`**: all the lines above are present.
- **`missing`**: a file or an anchor is gone. The box says «لم يُعثر على سطر الحكم في results/<file>: لا تقرأ هؤلاء الوكلاء بدونه» ("verdict line not found in results/<file>: do not read these agents without it"), the short line is replaced by the same text, and test 8 fails.
- *(Amended while building M2, 28 September: the box and the short line name EVERY missing file, not only `results/<file>`: «لم يُعثر على سطر الحكم في {files}: لا تقرأ هؤلاء الوكلاء بدونه», where `{files}` is each missing file as `results/<file>`, sorted and joined by " · ". A reader who restores the first file named must not be told the verdict is whole while a second is still gone.)*
- **`none`**: the prefix has no row, as for a future `runs_X`. The box says «لا يوجد حكم مسجَّل مسبقاً لهذه التجربة في results/. ما تعرضه هذه الصفحة ليس نتيجة.» ("No preregistered verdict for this experiment in results/. Nothing on this page is a result.")

**The short verdict line** (`SHORT_VERDICT[prefix]`) replaces the bare cell on every compact surface: the scene overlay, the experiment select and the phone summary. It is authored text, not a quote, so it is shown only when every anchor it summarises was `found`; test 8 pins that dependency.

| prefix | Arabic (English, same line on toggle) | requires anchors |
|---|---|---|
| `c4` | «أصغر من الحد الأدنى المهم (50 وحدة) عند 300 000 خطوة · بفارق بذرة واحدة · الاختباران لا يتفقان · لم يستقر التدريب» (smaller than the MEI (50) at 300 000 steps · one seed wide · the two tests disagree · not converged) | `:42`, `:28`, `:33`, `:48` |
| `d2` | «غير حاسم · وكلاء C1 ‏(50 000 خطوة)» (inconclusive · C1 agents, 50 000 steps) | `:30`, `:86` |
| `phase_d` | «غير دال إحصائياً · غير حاسم (قراءة لاحقة) · الذراع "العمياء" ليست عمياء · وكلاء C1» (not significant · inconclusive (post-hoc) · the "blind" arm is not blind · C1 agents) | `PHASE_D_RESULT:26`, `:33`, `PHASE_D2_RESULT:65` |

*(Amended after the M1 final review, 27 September: the c4 line read «الاختباران مختلفان» ("the two tests are different"). `app/agent_catalog.py` has said «الاختباران لا يتفقان» ("the two tests disagree", as the English line does) since Task 10b, and this table now says the same; its `seeds` anchor starts at `:28`. See the walkthrough log.)*

*(Amended while building M2, 28 September: the d2 and phase_d lines are carried as drafted, and each is shown only when every anchor it names was found; otherwise the not-found text above replaces it. Grouped digits are joined by U+202F (d2's 50 000), never by a plain space.)*

**Arabic glosses.** They sit under each quoted cell and keep their qualifiers:

| cell | gloss |
|---|---|
| SMALLER THAN THE MEI (c4) | «أثر الاستباق أقل من 50 وحدة ضرر، وهو حدّ اختاره الفريق مسبقاً، عند 300 000 خطوة تدريب، على طريق فيه تغيّر واحد في الميل لكل حلقة. التدريب لم يستقر، والنتيجة معلّقة على بذرة واحدة: لو انقلبت بذرة واحدة لصارت غير حاسمة.» ("Preview's effect is below 50 damage units, a threshold the team set in advance, at 300 000 training steps, on a road with one grade change per episode. Training had not settled, and the result hangs on one seed: if one seed flipped, it would be inconclusive.") |
| INCONCLUSIVE | «غير حاسم: التجربة لا تميّز بين "لا أثر" و"أثر يهمّ الفريق"» ("Inconclusive: the experiment cannot tell 'no effect' from 'an effect the team cares about'"), from `PHASE_D2_RESULT.txt:31-33` |
| NOT SIGNIFICANT | «غير دال إحصائياً، مع وكلاء بميزانية C1» ("Not statistically significant, with agents at the C1 budget") |
| NOT-CONVERGED | «لم يستقر التدريب» ("Training had not settled") |

**Table rows** come from `analyse_phase_d2.load(prefix)`. Missing seeds are named from its `incomplete` list.

**Catalog (M2).** `GET /api/agents/catalog` returns `{experiments: [{runs, name, prefix, protocol, verdict: {state, short, cells}, pairs: [{seed, runnable, reason, table_diff, scored, agents: [{tag, arm, status, budget_line, train_dt, problems}]}]}], episodes: {"d2": [{idx, seed, weights, climb_start_s, grade_pct}], "phase-d": [...]}, preview_s, act, limits, sb3}`.

*(Amended while building M2, 28 September: the catalog as served carries, per experiment, the WHOLE verdict (`state`, `lines`, `missing`, `short`, `cells`), so the verdict box reads before «احسب»; per pair, `problems`, `protocol` (null unless the pair can run) and `result_file`; per agent, `reason`, `problems`, `zip_sha` and `scored` (on each agent, not on the pair). A seed with one arm directory missing is listed, with that arm `missing`. Episodes carry `grade` as a fraction, as `meta.episode.grade` does, not `grade_pct`; `table_diff` is rounded to one decimal, as the results tables print it. An unexpected failure is a fixed-text 500 with no-store, never the exception's own text. Two additions to the status order, which is unchanged: a directory that does not exist is a `KeyError`, and at step 7 a `final.zip` that is not a readable stable-baselines3 zip is `incomplete` (reversing M1 ruling 6). `check_pair` runs `find_pair`'s checks in `find_pair`'s order and returns the problems, so the catalog and the episode route share one rule.)*

---

## 5. The road and the scene

**Geometry** is computed in Python by `agent_trace.route(cycle)`. It reads the cycle, returns new lists, and never writes into the cycle; nothing it returns reaches an env. With θ = atan g (`engine_env.py:426-427`), over the 719 stepped samples:

```
ds_k = v_k·dt;  s = [0, cumsum(ds)];  x = [0, cumsum(ds·cos θ)];  z = [0, cumsum(ds·sin θ)]
```

- That gives 720 vertices, plus `grade_pct` (720 values), `speed_kmh`, `length_m`, `rise_m`, `climb_start_s`, `p_baro_kpa` and `t_amb_c`.
- Recon figures:
  - the path is 25 603 m on every D2 episode;
  - the rise is 2755 m on episode 1;
  - across the 20 episodes the rise runs from 1917 m (seed 1004) to 3247 m (seed 1005).

**Car position** comes from `episodeAt`: k = ⌊t⌋, clamped to the computed frames, and s = s[k] + (t − k)·(s[k+1] − s[k]). This is exact, because the env holds the speed constant within a step.

- **Both cars use one `s`.** The scenario imposes the speed (`engine_env.py:729`), so the two cars are always at the same place.

**View 1: the whole-route side profile (SVG).**

- x in km against z, with **vertical exaggeration VE = 3**, printed as «المقياس الرأسي مضخّم ×3» ("vertical scale exaggerated ×3").
- One car marker, and a climb-start marker with its time and grade.
- For the sighted car only, a tick at each `PREVIEW_S` horizon, placed at `x[min(k + int(h/DT), 719)]`.
- Caption: «يرتفع الطريق {rise} م بينما يبقى الضغط {p} كيلوباسكال والحرارة {t} °م ثابتين طوال الحلقة» ("the road rises {rise} m while pressure stays at {p} kPa and temperature at {t} °C throughout the episode").

**View 2: the 3D chase view (Three.js).**

- `createEpisodeRoad` gives `ribbonGeometry` its `{length, atDistance}` shape.
- The road is straight in plan: world X = x/M, Y = z/M, with **M = 10 m per unit on both axes**, so the slope is true.
- Caption: «الميل غير مضخّم · السيارة ليست بمقياسها» ("slope not exaggerated · car not to scale").
- **Floating origin.** Each update translates the road group by (−x_car/M, −z_car/M). `stage()`'s shadow camera is fixed at ±45 units (`scene.mjs:352`).
- The camera is `stage()`'s orthographic camera, following from behind, the side and above, with no easing.
- The surface is `ribbonGeometry(road, 0, road.length, ROAD_W, …, 719)`.
- Centre dashes every 20 m give the sense of motion. The ground is a plain grid.

**Cars and colours.**

- Two `supra()` calls at lateral offsets **`CAR_OFFSET = ±1.9` units**, in the lab's paint. The car's half-width is about 1.48 units: wheels at z ±1.23, plus tyre and spokes, from `scene.mjs:605-613`. The draft's ±1.45 made the inner wheels overlap by about 0.06; ±1.9 leaves a gap of about 0.84.
- Lane tints are **`LANE_W = 3.2`** wide, on a road ribbon **`ROAD_W = 7.6`** wide. A node test pins that the cars do not overlap and each tint is wider than the car on it.
- Labels:
  - «يرى الطريق أمامه» ("sees the road ahead");
  - «لا يرى الطريق أمامه» ("does not see the road ahead");
  - **Phase D's blind car** instead reads «لا يرى الطريق أمامه، لكنه قد يحفظه: الطريق نفسه في كل حلقة» ("does not see the road ahead, but may have memorised it: the same road in every episode"), citing `PHASE_D_RESULT.txt:33-37`.
- Colour tokens: `--agent-sighted` (blue) and `--agent-blind` (amber), defined in both themes and never red or green. The jev marker (M3) is a dashed warm-grey tick; there is no third car.
- *(Amended while building M2, 28 September: Phase D's blind car is named with its caveat everywhere it is named: the scene label, the picker's budget line, the verdict box's scored line and the stopped-lane line. Its pause-panel line cites `PHASE_D_RESULT.txt:33-40`, the whole NOT BLIND item, read from the verdict's own `not_blind` line rather than typed; this section drafted `:33-37` and section 6 `:33`.)*

**Preview.** One marker at each `PREVIEW_S` horizon, coloured by the grade read there, on a single-hue ramp from 0 to 16 %: the profile's ticks and the chase view's posts use the same ramp. There is no continuous band, because the agent saw four numbers, not a stretch of road.

- The profile always carries all four.
- The chase view shows only the posts inside its view of about 200 m. At 130 km/h the 15 s and 30 s horizons lie about 540 m and 1080 m ahead, so after the launch it shows the 2 s and 5 s posts. In the first second, from rest, it also shows the 15 s post at the edge of the view (about 200 m ahead on episode 1); the 30 s horizon is then about 720 m ahead, so the chase view never holds all four.
- *(Amended while building M1, 27 September: this paragraph did not say which view carries which markers, and the profile's ticks were drawn in the lane colour.)*

**Overlay.** A thin strip inside the scene carries the **short verdict line** and «محاكاة» ("simulation"). A legend reads «السيارتان في المكان نفسه دائماً: السرعة يفرضها السيناريو، والوكيلان يختاران الحماية فقط» ("both cars are always at the same place: the scenario sets the speed, and the agents choose only the protection").

---

## 6. The page and the paused moment

**Picker.** Nothing is selected and nothing is computing when the page opens.

1. **Experiment:** the name plus the **short verdict line**.
2. **Pair:** «بذرة k · الأعمى − المُبصر {+x.x}» ("seed k · blind − sighted {+x.x}"), followed by a qualifier:
   - for D2 and C4: «(فرق وسيطَي 20 حلقة، لكلٍّ منها طريقها وأوزانها؛ ليست هذه الحلقة)» ("difference of the medians of 20 episodes, each with its own road and weights; not this episode");
   - for Phase D: «(فرق وسيطَي 20 حلقة على الطريق نفسه بأوزان مختلفة؛ ليست هذه الحلقة)» ("difference of the medians of 20 episodes on the same road with different weights; not this episode").

   Every pair is listed. Refused pairs are disabled with their reason. Each arm shows «دُرِّب {budget} خطوة (من final.zip)» ("trained {budget} steps (from final.zip)").
3. **Episode 1..20 (حلقة):** for example «حلقة 1 · الصعود عند 141 ث · 13.3٪ · الأوزان: عزم 0.69 / وقود 0.01 / عمر المكوّنات 0.30» ("episode 1 · climb at 141 s · 13.3 % · weights: torque 0.69 / fuel 0.01 / component life 0.30"). *(Amended after the M1 final review, 27 September: the example read fuel 0.29 / component life 0.03. `evaluate.py` `EPISODES_D2[0]` holds the weights (0.690154, 0.012829, 0.297017), in engine_env's order torque, fuel, component life; the page always showed 0.69 / 0.01 / 0.30.)* For Phase D: «الطريق نفسه (180 ث · 12٪)؛ تختلف الحلقات في الأوزان فقط» ("the same road (180 s · 12 %); the episodes differ only in their weights").

«احسب» sends one `preempt=1` request. Until it is pressed, the scene reads «اختر تجربة وزوجاً وحلقة ثم اضغط احسب» ("choose an experiment, a pair and an episode, then press احسب").

*(Amended while building M2, 28 September: an experiment with no runnable pair is listed greyed with its reason and cannot be selected, from the select or from an address. An address selects only what the catalog allows, level by level; one that names more (a refused pair, a malformed level, `ep=21`) is replaced by the address of what it selects. Every change of a select replaces the address, never adding a history entry, and clears the episode on screen. The episode is kept when the pair changes within one protocol, since both pairs are scored on the same twenty episodes. The qualifier sits under the pair select once an experiment is chosen, and Phase D's same-road note under the episode select; it prints the grade with one decimal, «(180 ث · 12.0٪)», like every other grade on the page, where this section wrote «12٪». The table figure is drawn inside a left-to-right isolate: in an Arabic line a bare "+360.6" is drawn "360.6+". A greyed option has room for one reason, so every pair that cannot run is also listed under the picker, collapsed, with every problem the server found: both arms and each stored and live field of a plant mismatch (section 8, "with reason and fields"). When «احسب» meets another build still running, the page says it is stopping that build, because its own request already asked for it; the M1 text asking for «احسب» again appears only when that request may never have arrived, on a retry after a failed request.)*

**Timeline.** The lab's controls: play/pause, restart, scrub, and rates from 0.5 to 16×.

- **Computed region.** It is shown as a fill: «حُسب حتى 03:12 · تنتهي الحلقة عند 11:59» ("computed up to 03:12; the episode ends at 11:59"). The uncomputed part is hatched, the clock's end is the computed end, and scrubbing clamps to it.
- **Play at the computed edge.** `PlaybackClock.play()` rewinds to 0 at its end (`playback.mjs:9`). So while the build is unfinished and time equals the computed end, `playOrWait` sets a *waiting* flag instead of calling `play()`. `resumeIfStalled` extends the duration when frames arrive, then plays, but only if the stop was the edge or the flag, never the viewer's pause.
- **Climb tick.** A tick marks the climb start.
- **dt caption, built from `meta.train_dt` per arm:** «تُعاد هنا بخطوة 1.0 ث، الخطوة التي قُيِّم بها الوكيلان؛ دُرِّبا بخطوة {train_dt} ث. مشكلة معروفة لم تُحلّ (AUDIT2.md H2-2)؛ لم يُقَس هل تؤثر في الوكيلين بالقدر نفسه» ("replayed here at a 1.0 s step, the step the agents were scored at; they were trained at {train_dt} s. A known, unresolved problem; whether it affects both agents equally has not been measured").
  - If `train_dt` equals `DT`, the mismatch clause is dropped.
  - If `train_dt` is absent, it reads «خطوة التدريب غير مسجّلة» ("training step not recorded").

**Pause panel.** It follows playback and holds still when paused.

- **Heading:** «القرار المطبَّق من الثانية k إلى k+1» ("the decision applied from second k to k+1"), plus the grade now.
- **Weights line:** «ما طُلب من الوكيلين في هذه الحلقة: عزم {w0} · وقود {w1} · عمر المكوّنات {w2}» ("what the agents were asked to weigh in this episode: torque {w0} · fuel {w1} · component life {w2}").

The five actions:

| # | Arabic label | unit | what the code does with it | bar |
|---|---|---|---|---|
| 0 | تعديل توقيت الشرارة | ° | added to the modelled engine computer's spark (`engine_env.py:771-772`) | −8 … +4 |
| 1 | تعديل خليط الوقود (لامدا) | λ | added to the modelled engine computer's λ (`:773`) | −0.15 … +0.06 |
| 2 | **إزاحة سقف ضغط الشحن** | kPa | an offset on the **ceiling** of the agent's own pressure loop (`:589-590`, `:633-635`), not added to anything. No effect while the pressure is below that ceiling. | −40 … +15 |
| 3 | مروحة التبريد | duty | absolute value | 0 … 1 |
| 4 | مضخة سائل التبريد | duty | absolute value | 0.3 … 1 |

**Why row 2 is labelled this way.** Measured today on `make_grade_climb`, seed 1000, dt 1.0, neutral otherwise: a constant −20 kPa applied trim left the manifold pressure at 179.0 kPa against 178.6 kPa with trim 0 at k = 200. It did not lower the pressure at all, because the ceiling was not binding.

Row 2 therefore shows each car's `map_kpa` beside it: «ضغط المشعب الآن {map} كيلوباسكال؛ السقف نفسه يُحسب داخل الحلقة ولا يُعرض» ("manifold pressure now {map} kPa; the ceiling itself is computed inside the loop and is not shown").

**Bars and markers.**

- Each row has a bar from lo to hi.
  - **Rows 0 to 2:** the tick at 0 reads «بلا تعديل» ("no change").
  - **Rows 3 and 4:** the tick is at 1.0, and the fan and the pump each have their own note under the bar.
    - Row 3, the fan: «قيمة صف "حاسوب المحرك الأساسي" في النتائج (1.0 ثابتة)؛ الحاسوب المنمذَج نفسه يجدول المروحة 0 أو 0.4 أو 1.0 حسب حرارة سائل التبريد» ("the value used by the results' 'baseline ECU' row (a constant 1.0); the modelled computer itself schedules the fan at 0, 0.4 or 1.0 by coolant temperature").
    - Row 4, the pump: «قيمة صف "حاسوب المحرك الأساسي" في النتائج (1.0 ثابتة)، وهي أيضاً ما يشغّل به الحاسوب المنمذَج المضخة طوال الوقت» ("the value used by the results' 'baseline ECU' row (a constant 1.0), which is also what the modelled computer runs the pump at throughout").
    - Sources: `check_premise.py:25` `NEUTRAL = neutral_action()`, `evaluate.py:347`, `engine_env.py:265` (the modelled computer schedules the fan only), `engine_env.py:764-765` (its thermal step passes no pump duty, so `thermal.py`'s default 1.0 runs the pump).
    - *(Amended after the M1 final review, 27 September: both rows carried the fan's note, which is false for the pump. See the walkthrough log.)*
- Each car has a coloured dot and its **applied** value.
- Where `held` is true, a second line reads «أمر به {x}؛ قيّده حد سرعة التغيير» ("commanded {x}; held back by the rate limit").
- The page always says «حاسوب المحرك المنمذَج» ("the modelled engine computer"), never «حاسوب المحرك» ("the engine computer").

**Under the rows:**

- **What each car saw.**
  - Sighted car: «بعد 2 ث: …٪ · بعد 5 ث … · بعد 30 ث …» ("in 2 s: …% · in 5 s … · in 30 s …"), from `meta.preview_s`.
  - Blind car: «لا يرى الطريق أمامه: مداخل الاستباق عنده 0 · 0 · 0 · 0» ("does not see the road ahead: its preview inputs were 0 · 0 · 0 · 0").
  - Phase D's blind car adds the memorisation caveat of §5, citing `PHASE_D_RESULT.txt:33`.
- **Damage so far, per car:** «وحدات ضرر، في هذه الحلقة فقط حتى هذه اللحظة» ("damage units, in this episode only, up to this moment").
- **Turbine and torque.** Turbine °C against `limits.turb_c`, and torque delivered against torque requested. The lab's model-output caveat (`c_turb` assumed) is reused from its strings.
- **Device line:** «التقييم المسجَّل حمّل الشبكة على الجهاز الافتراضي لـ SB3، وهو cuda على هذا الجهاز؛ ملفات النتائج لا تسجّل الجهاز. هذه الحلقة حُسبت على {device} ‏(torch {v}، SB3 {v})» ("the recorded evaluation loaded the network on SB3's default device, which is cuda on this machine; the result files do not record the device. This episode was computed on {device} (torch {v}, SB3 {v})"). It becomes a warning when the device is not CUDA, because CPU episodes differ from CUDA ones (recon §2).

**Misreading → prevention.** This table is the layout's acceptance checklist.

| a viewer could read | what prevents it | where |
|---|---|---|
| "a recorded drive" | Badge: «محاكاة: سيناريو إجهاد اصطناعي — تسلّق متواصل {grade}٪ عند {v} كم/س في {t} °م، أقسى من أي تسلّق مسجّل؛ لا يعني ذلك أنه أحرّ من كل لحظة في الرحلات المسجّلة» ("simulation: a synthetic stress scenario, a sustained {grade} % climb at {v} km/h in {t} °C, harsher than any recorded climb; this does not mean it is hotter than every moment of the recorded drives"). Figures come from `meta` only. The ground is a plain grid. | header; overlay |
| "this episode is the result" | The verdict box, verbatim with file:line and not dismissable, followed by «حلقة واحدة لزوج واحد مثال توضيحي، لا نتيجة. النتائج وسيطات عبر 20 حلقة، ولا يُحسب هنا أي فرق بين السيارتين» ("one episode of one pair is an illustration, not a result. The results are medians over 20 episodes, and no difference between the cars is computed here") | side column; overlay |
| "C4 is a clean negative" | The short line (one seed wide · the tests disagree · not converged), the gloss, and `PREREGISTRATION_C4.md:633-643` quoted whole | select; overlay; box |
| "(i)/(ii) mean something unstated" | `PREREGISTRATION_C4.md:41-43` quoted under the reading | box |
| "D2's null means no effect" | `PHASE_D2_RESULT.txt:86-89` quoted; "C1" in the short line | box; select |
| "this episode's gap is the table row" | Nothing is computed; the row appears only in the picker, labelled "not this episode" | picker |
| "the page picked a representative pair" | Nothing is selected by default; every pair is listed | picker |
| "high damage means poor protection" | The episode's three weights are shown | picker; pause panel |
| "the blind car lost a race" | One profile marker; the same-place legend; no winner badge | views |
| "the sighted agent saw the road" | Four markers, not a band | views |
| "the Phase D blind agent was blind" | The NOT BLIND quote, the scene label and the panel caveat | box; scene; panel |
| "the boost trim lowered the pressure" | Row 2's ceiling label and `map_kpa` | panel |
| "a fan at 0.4 cut cooling below the ECU" | The fan/pump tick label naming the scheduled 0 / 0.4 / 1.0 | panel |
| "the slope is real" / "exaggerated" | «×3» on the profile; «الميل غير مضخّم» ("slope not exaggerated") in the chase view | corners |
| "a real 3 km climb" | The rise-at-constant-pressure caption | profile |
| "trained like this" | The dt caption, built from meta, "unresolved" | timeline |
| "this is the scored run" / "the scored artefact" | The device line; the zip-sha check or "not recorded" | panel; box |
| "the network's output was applied" | Applied values, with the command on a second line when held | panel |
| "it saved damage by refusing torque" | Delivered against requested torque | panel |
| "the temperature was measured" | The lab's model-output caveat | panel |
| "jev or Laya is part of the thesis" | Hidden by default; the shared honesty lines; no comparison; never applied | models panel |
| "Laya's answer is an engine judgement" | «تجربة تشغيل، لا تقييم»; the README line (`README_AR.md:31`); the order check, held or changed per action (M3 design §7.5b) | models panel |
| "Laya sent data out" | The where-it-runs line; the offline variables, the absolute-path check and the socket guard together (M3 design §7.5); tests 18 to 20 | models panel |
| "the models were told nothing about the agents" | M3 design §7.3: the state is the sighted agent's own observation, which already carries its earlier trims in its spark and lambda | models panel |

*(Amended while building M2, 28 September, after the Task 10 review: the row "C4 is a clean negative" names the select, and a closed select shows only as much of its option as fits. At 390 px the C4 option read «C4 · أصغر من الحد الأدنى المهم (50 وحدة) عند 300 000 خطوة» and nothing more, which is that misreading itself; at 1440 px it stopped inside «بفارق بذرة واحدة». The milestone walk (`fa4e4aa`) passed the row on the strip and the box; the review failed it, and it was right to. The chosen experiment's whole short line now also stands under the select, found, missing or none alike, exactly as the box prints it (`experimentNote`, `#pick-experiment-note`; `f2e3e5f`). The option text is unchanged, so the open list still names each experiment's line. A ruling taken while building, not Jad's word: the line now shows twice in the side column, under the select and in the box.)*

**Layout.**

- **Desktop (≥ 1100 px, RTL):**
  - a grid of `minmax(0,1.6fr) minmax(320px,1fr)`;
  - main column: the chase view (16:9) with its overlay, the timeline, the pause panel, the models panel once unlocked, then the profile (M3 design §7.8, Jad's option 1);
  - side column: picker, verdict box.
- **Phone (< 760 px):**
  - one column with a 16 px gutter and no horizontal scroll;
  - order: badge, picker, verdict, chase view (4:3), timeline, pause panel, profile, models panel once unlocked (below 1100 px);
  - the verdict shows the short line, the C4 one-seed line and the illustration line; the rest sits in `<details>`;
  - in the pause panel, labels sit on their own lines and values stack by car.
- The nav on `agents.html` reads simulation, agents (active), monitor, review, and `agents.css` restores the last link on phones.
- Arabic is the default, with the lab's language toggle. The page follows `prefers-color-scheme`.

---

## 7. jev (M3)

*(Replaced by §7 of `2026-09-28-agent-replay-m3-design.md`, approved 28 September and built 29 Sep, as are rows 14 to 17 of §9 and the M3 part of §10. Kept here as approved.)*

**Gesture.** `tap-unlock.mjs` is a pure counter: 10 taps within 4000 ms returns `true`. Its state is a module variable, and it never touches `localStorage`, `sessionStorage`, IndexedDB or cookies.

- It is attached to this page's own footer label, `02 — AGENTS` (approved, §11 Q1), with padding for a 32 px touch target. The lab's `01 — REPLAY` gets no handler.
- Unlocking removes `hidden` from `#jev-panel` and only then calls `GET /api/agents/jev/status`. That returns `{configured, source, vendor, model, hosted}`, never the key.
- The gesture hides the panel; it protects nothing.

**The panel, fully visible once unlocked.**

- A left-to-right line: `typesafe.ai · {model returned by the API}`.
- Then:

  > «خدمة خارجية تعمل في الولايات المتحدة. ليست جزءاً من الرسالة ولا من أي نتيجة، ولا يقارنها أي رقم بالوكلاء. هذه الصفحة لا تحفظ شيئاً؛ لكن اتفاقية المورّد تسمح له بالاحتفاظ بما يُرسل لاستخراج بيانات القياس بلا حدّ زمني (MCA §4.1). تُرسَل إليه حالة هذه الحلقة المحاكاة فقط، لا بيانات السيارة المسجّلة. كل ضغطة استدعاء واحد مدفوع. اتفاقية المورّد تمنع تدريب أي نموذج على تقليد إجاباته. شروط موقع المورّد موجّهة لزوّار الولايات المتحدة؛ هل الاستخدام من السعودية مسموح؟ غير معروف.»

  In English: "An external service in the USA. It is not part of the thesis or of any result, and no figure compares it with the agents. This page saves nothing, but the vendor's agreement lets it keep what is sent, in perpetuity, to derive telemetry (MCA §4.1). It receives only this simulated episode's state, never the recorded car data. Each press is one paid call. The vendor's agreement forbids training any model to imitate its answers. The vendor's site terms are aimed at US visitors; whether use from Saudi Arabia is permitted is unknown." The telemetry clause is `legal_mca.txt:37`.
- The button «اسأل jev عن هذه الثانية (استدعاء واحد)» ("ask jev about this second (one call)") is enabled only while paused, and disabled while a call is in flight.

**Route: `POST /api/agents/jev`, JSON body only.**

```python
class JevAsk(BaseModel):
    model_config = ConfigDict(extra="forbid")
    trace: str = Field(pattern=r"^runs[A-Za-z0-9_]*/\d{1,3}/\d{1,2}$")
    step: int = Field(ge=0, le=718)
```

- **Body.** The body carries a store key and a step, never browser state. An extra field gets 422, and so does a form-encoded or `text/plain` body.
- **Cross-site guard.** An `Origin` header other than `http://127.0.0.1:<port>` or `http://localhost:<port>` gets **403**. Another tab must not be able to spend a paid call.
- **Resolution.**
  - unknown trace: 404;
  - evicted trace: 409 `trace_gone`;
  - `step ≥ len(frames)`: 409 `step_not_computed`;
  - one call at a time, through a non-blocking lock: a second request gets 409 `busy`.
- **Why POST, against "every route is a GET".** A paid, non-idempotent call to a US service must not fire on prefetch, reload or history, and a GET query string cannot forbid extra parameters.
- **What the GET rule protects still holds.** The rule protects the car. In the M3 commit, `server.py:43` becomes: "Every route this module defines is a GET. The one POST, /api/agents/jev, is added by app.agent_api.install() only under --simulation; it sends simulated state to an external service and has no path to the vehicle." A test pins this.

**The request** (`build_request`, in English, the vendor's primary language): `POST https://api.typesafe.ai/v1/systemone`, `model: "jev-latest"`. The `state` field holds three things:

- **`engine`**: `decode(trace.obs[0][step])`, the sighted agent's actual observation, inverted from `engine_env._obs` (`:646-671`) into named physical units:
  - engine and charge: `engine_speed_rpm`, `manifold_pressure_kPa`, `throttle_fraction`, `spark_advance_deg_BTDC`, `lambda`;
  - temperatures: `engine_block_C`, `oil_C`, `turbine_housing_C`, `charge_air_C`;
  - surroundings: `ambient_C`, `barometric_kPa`, `humidity_kg_per_kg`;
  - road: `road_speed_kmh`, `grade_now_percent`, `grade_ahead_percent: {"in_2_s", "in_5_s", "in_15_s", "in_30_s"}` (keys built from `PREVIEW_S`);
  - driver: `torque_requested_Nm`, `driver_aggression_0_to_1`;
  - `priorities: {deliver_torque, save_fuel, protect_components}` (obs 20–22);
  - `note: "simulated synthetic stress scenario, not a recorded drive"`.
- **`task`**, one fixed paragraph: "Decide the supervisory settings for the next one second. Deliver the requested torque. Keep the turbine housing below {TURB_PROTECT_K − 273.15:.0f} °C and the oil below {OIL_PROTECT_K − 273.15:.0f} °C. Weigh the three by `engine.priorities`. Spark and lambda trims are added to the modelled engine computer's values. The boost setting offsets only the ceiling of the pressure loop and matters only if pressure would otherwise reach it. Fan and pump are absolute duties." The constants are imported (`engine_env.py:490-491`).

Never sent: the agents' actions, the experiment or verdict, or anything from `logs/raw`, `app.replay`, `app.reader` or `app.estimator`. `build_request` accepts only a store `Trace`. The panel shows **the exact body sent, without the key**, under «ما الذي أُرسل» ("what was sent").

**Five questions, one call, each of `type: "choice"`.** The vendor requires `instructions` and `criteria` on every question (`api.md:120-124`). Each instruction refers to `task` by name, as `api.md:58` describes.

| id | instructions | criteria keys → description (physical level) |
|---|---|---|
| `spark_trim` | "Following `task`, how should spark timing be trimmed for the next second?" | "retard 8 deg" (−8), "retard 4 deg" (−4), "no change" (0), "advance 2 deg" (+2), "advance 4 deg" (+4) |
| `lambda_trim` | "Following `task`, how should the air-fuel ratio be trimmed? Richer cools the exhaust and costs fuel." | "richer by 0.15" (−0.15), "richer by 0.075", "no change" (0), "leaner by 0.03", "leaner by 0.06" |
| `boost_ceiling` | "Following `task`, by how much should the ceiling of the boost-pressure loop be offset? It matters only if manifold pressure (`engine.manifold_pressure_kPa`) would otherwise reach the ceiling." | "ceiling −40 kPa" (−40), "ceiling −20 kPa", "no change" (0), "ceiling +7.5 kPa", "ceiling +15 kPa" |
| `cooling_fan` | "Following `task`, what cooling fan duty should run? It cools the coolant loop, not the turbine directly." | "fan 0 %" (0), "fan 25 %", "fan 50 %", "fan 75 %", "fan 100 %" (1.0) |
| `coolant_pump` | "Following `task`, what coolant pump duty should run (minimum 30 %)?" | "pump 30 %" (0.3), "pump 47.5 %", "pump 65 %", "pump 82.5 %", "pump 100 %" (1.0) |

**Mapping.**

- `LEVELS` is a 5 × 5 float32 table built at import from `ACT_LO`, `ACT_HI` and `neutral_phys`:
  - trims: lo, the midpoint of lo and 0, 0, the midpoint of 0 and hi, hi;
  - fan and pump: five evenly spaced values.
- `NET = clip(2.0 * (LEVELS − ACT_LO) / (ACT_HI − ACT_LO) − 1.0, −1, 1)`, computed vectorised on the float32 arrays, **exactly as `neutral_action()` does** (`engine_env.py:1002-1005`).
  - A Python-float expression cast afterwards is off by one ulp for spark and boost (0.33333334 against 0.33333337, measured today).
  - The vectorised form equals `neutral_action()` bitwise at every neutral level, measured today.
- Option keys map back through `OPTIONS`, a dict lookup; strings are never parsed.
- jev's answer is its `choice`, the highest-probability option, which yields `value_phys` and `value_net`. Every answer lies in `Box(-1, 1)`.

**The answer column shows**, per action:

- the chosen level, in physical and network units;
- all five `probabilities` as bars, and `confidence`;
- «هدف لثانية واحدة: لم يُطبَّق ولم يُقيَّد بمعدل التغيّر» ("a one-second target: not applied, not rate-limited");
- the discretisation rule, written under the column;
- «الاحتمالات والثقة ادعاء المورّد، لم تُختبر على هذه المهمة؛ ويقول المورّد إن النموذج ضعيف في الدقة العددية» ("the probabilities and confidence are the vendor's claim and were not tested on this task; the vendor says the model is weak at numeric precision"). Sources: `concepts_system-one.md:21` and `model-jaggedness_jev-1.13.md:13`.

`score` questions are rejected: the vendor warns that jev is not a calculator.

**Latency.** `time.perf_counter()` around the HTTP call, shown as «{ms} ms، مقيسة من هذا الجهاز (ادعاء المورّد 70–500 ms)» ("{ms} ms, measured from this machine (vendor claim 70–500 ms)").

**Key.**

- `load_key()` reads the `TYPESAFE_API_KEY` environment variable, or else `<APPDATA>/grad-project/typesafe_key`, a file **outside the repository**.
- It refuses any candidate path that resolves under the repository root. A git-ignored file inside the working tree would still travel in a zip or a directory copy, and this project has shipped working-copy archives before (CLAUDE.md mistakes 11 and 16).
- It is read on each call. The key appears only in the `Authorization: Bearer` header built inside `_send`. It is never logged, never returned, and never placed in `meta` or an error.

**Errors.** Each error returns a fixed Arabic sentence and a code, and the column shows «لا جواب» ("no answer") with the reason. **Nothing is ever substituted.** The vendor's body and `str(exc)` are never forwarded. There are no automatic retries, and the timeout is 10 s.

| code | when | HTTP |
|---|---|---|
| `no_key` | no key; nothing sent | 503 |
| `network` / `timeout` | `URLError` or 10 s | 502 |
| `key_rejected` | vendor 401 | 502 |
| `vendor_refused` | vendor 403: "access from this location may not be permitted" | 502 |
| `request_rejected` | vendor 422: "a bug on this page" | 502 |
| `rate_limited` / `overloaded` | 429 / 529: "ask again in a moment" | 502 |
| `bad_answer` | a question missing, a choice outside the options, or no probabilities | 502 |
| `foreign_origin`; bad body | our guards | 403; 422 |
| `trace_gone` / `step_not_computed` / `busy` | above | 409 |

**Deferred, not blocked.** Later, `to_action(ask(...))["net"]` wrapped as `policy(env, obs)` would become a third lane in `run_lanes`. A jev error would abort that build, never fall back to neutral. Nothing for it is built.

---

## 8. Error handling across the feature

| situation | behaviour |
|---|---|
| unknown `runs`, seed or episode; malformed or traversal key | 404 with fixed text; no path is ever resolved from a request |
| incompatible, training, incomplete or no-meta agent; zip not the scored one | listed and disabled with reason and fields; 409 `refused`; never loaded |
| SB3 missing | the catalog says "cannot run"; the episode route returns 503; the lab is unaffected |
| model load, plant exception or `SystemExit` | `error` reported once, then retryable; no rebuild loop |
| first build after server start | `loading` state with «تحميل الشبكتين…» ("loading the two networks…"), about 5 s |
| build superseded | cancelled silently; nothing kept; stale frames dropped by a load token |
| busy | «تُحسب حلقة أخرى الآن ({runs} بذرة {k} حلقة {e})» ("another episode is being computed now ({runs} seed {k} episode {e})"); «احسب» pre-empts it |
| a lane diverges | that car stops; the panel names the step |
| device not CUDA | warning line; the run is still shown |
| play pressed at the computed edge | waits for frames, never rewinds |
| poll fails | «الخادم غير متاح» ("server not reachable") with a retry; frames already received stay playable |
| WebGL fails | a message in place of the chase view; the profile and panel still work |
| verdict `missing` or `none` | stated in the box and in the short line; a cell is never guessed |
| lab build and agent build at once | separate single workers; both slow down; nothing breaks |
| jev, Laya | M3 design §7.9 |

---

## 9. Testing

**Ground rules.**

- No test touches the network; the jev tests inject a fake `send`.
- **The new file must not trip `test_read_only`.** That scan (`app/test_replay.py:529-553`) reads `app/test_agents.py` too, strips only triple-quoted strings and `#` comments, and flags `\.write\s*\(` except on lines containing `fh.write`. So:
  - every banned token in this suite is written as a raw regex (`r"\.write\s*\("`, which does not match itself);
  - fixtures are made with `shutil.copy`, `json.dump(obj, fh)` and `FP.claim_running`;
  - `app.test_replay --full` is re-run at every milestone to prove the 49 stay unchanged.

| # | test | what it pins |
|---|---|---|
| 1 | `tracer_equals_run_episode` | §3.6: `==` on both full dicts, through the store worker; "UNPROVEN" fallback; `--full` adds Phase D |
| 1b | `loader_matches_evaluate` | the default `load_pair("runs_c4", 0)` against `SAC.load(path + "/final")` as `evaluate.py:370` does it: same `str(device)`; `torch.equal` on every `policy.state_dict()` tensor; same `model_budget` sha, equal to the sha in `results/c4_seed0.txt` |
| 2 | `frames_are_the_episode` | 719 frames; last `damage` == result `damage`; `max(turb_c)` == `peak_turb`; sighted `preview_pct/100` == `grade[min(k+int(h/DT),719)]` to float32; blind preview all zeros; `act` == `clip(clip(_rescale(cmd), prev ± SLEW·DT), ACT_LO, ACT_HI)` in float32; `held` agrees and `any(held)`; **no `None` in `act`, `cmd`, `preview_pct` or `map_kpa` on a non-diverged lane**; `json.dumps(frame, allow_nan=False)` succeeds for every frame and for `meta` |
| 3 | `applied_not_commanded` | one `neutral_action()` step from rest records `act = [0, 0, 0, 0.25, 0.3]` and `held = [F, F, F, T, T]` |
| 4 | `preview_slice_is_the_observation` | `obs[PREVIEW] == float32(12·env._preview())`; `obs[13] == float32(12·grade)`; blind gives zeros; `STEPS == env.ep["steps"]` |
| 5 | `route_geometry` | 720 vertices; episode 1 is 25 603 m and 2755 m (±1); 3247 m and 1917 m; the cos/sin split; the cycle arrays are byte-identical afterwards |
| 6 | `catalog_real_tree` | 48 ready agents, 24 pairs; sixspeed agents are "no meta.json"; budgets 300 000 / 50 000; protocols; arms agree; C4 zip shas match results; D2 and Phase D pairs say "not recorded". Skipped loudly without `runs*`. |
| 7 | `catalog_synthetic` | a temporary root outside the repo with `runs_zz` and `results/zz_seed0.txt`: altered `plant_sha` is `incompatible [plant_sha]` with no `SystemExit` and no worker thread; no meta is refused; `RUNNING` with the test's own pid is `training`; no zip is `incomplete`; a meta arm mismatch is refused; **`runs_zz_blind/sighted_seed0` is refused by the evaluate-string rule**; **a recorded sha that differs is refused as "not the scored artefact"**; `ckpt_*` and `_logs` are ignored; the verdict is `none` |
| 8 | `verdicts` | each anchor of §4 is found and its `text` equals the file at `line`, including `C4_RESULT.txt:28-30`, `PREREGISTRATION_C4.md:41-43` and `:633-643`, and `PHASE_D2_RESULT.txt:86-89`; each `SHORT_VERDICT` is shown only when all its anchors are found, and a removed anchor turns it into the not-found text; the C4 gloss contains "50", "300 000" and the one-seed clause; `missing` names the file; unknown gives `none`; `table_rows == analyse_phase_d2.load` |
| 9 | `store` (fake tracer) | one worker; busy; preempt cancels and polls do not; `keep = 2`; partial traces never kept; error reported once; `SystemExit` becomes an error; `since` slicing; `loading` state before the first frame |
| 10 | `routes_only_under_simulation` | a subprocess `import app.server` leaves `app.agent_api` out of `sys.modules`; `app.server.app` has no `/agents*` routes and only GET/HEAD; AST: the single `install(` call sits inside `if a.simulation:`; `install(FastAPI())` adds the routes; POST to the episode route gives 405 |
| 11 | `no_writes` | `(path, size, mtime_ns)` snapshots of `runs_c4/*_seed0`, `results/`, `app/` (without `__pycache__`) and **`.git/index`**, plus `git status --porcelain` under `GIT_OPTIONAL_LOCKS=0`, identical before and after the suite; an AST/regex scan of the new modules finds no write-mode `open`, `.write`, `write_text`, `json.dump`, `.save`, `os.remove`, `shutil` or `mkdir` (patterns written as raw regexes) |
| 12 | `page_assets_ids` | every asset and import in `agents.html` resolves; every `$('id')` in `agents.mjs` exists; the `/agents` link in `simulation.html` is not the nav's last child |
| 13 | `no_network_outside_jev` | an **AST import scan** of non-test `app/*.py`: module roots `urllib`, `http`, `socket`, `requests`, `httpx`, `typesafe_sdk` are imported only by `app/jev.py`. A text scan would trip on `WebSocket` in `server.py`. |
| 14 | M3 `jev_levels` / `jev_mapping` | `LEVELS` and `NET` are float32; five sorted levels per action including both limits and the neutral; `NET` at the neutral level equals `neutral_action()[i]` bitwise; `_rescale(NET) ≈ LEVELS`; `OPTIONS` is one-to-one; the boost question's text says "ceiling"; fake answers are mapped with probabilities and confidence kept |
| 15 | M3 `jev_request` | `decode(env._obs())` equals the env attributes (float32) at several steps; horizon keys come from `PREVIEW_S`; every question has `instructions` and five `criteria`; `state.task` carries the imported thresholds; a non-`Trace` input is rejected; AST: `jev.py` imports none of `app.replay`, `app.reader`, `app.estimator` |
| 16 | M3 `jev_route` | extra field 422; form or `text/plain` 422; foreign `Origin` 403; unknown trace 404; step past the frames 409; GET 405; the only non-GET route after `install` is `POST /api/agents/jev`; the `server.py` docstring names it |
| 17 | M3 `jev_errors` / `jev_key` | every status and malformed answer gives its code, with no values; a sentinel key appears in no response body and in no root-logger line at DEBUG, even when the fake's exception text contains it; **`load_key()` with `APPDATA` pointed inside the repo refuses the path**; the env variable wins; `git check-ignore` matches `.env` and `*typesafe_key*` |

**Node tests.**

- **`agent-view.test.mjs`:**
  - `createEpisodeRoad` is exact at vertices;
  - `episodeAt` is linear and clamped;
  - `profilePoints` applies VE to y only;
  - `previewMarks` are clipped at 719;
  - `gaugeFraction` gives the right ends and neutral tick;
  - `playOrWait` at the computed edge sets *waiting* and never rewinds;
  - `resumeIfStalled` resumes after the edge or wait, not after a user pause;
  - `2·CAR_OFFSET` exceeds the car width (2 × 1.48) and `LANE_W` exceeds 2.96.
- **`agents-strings.test.mjs`** (its own process):
  - the lab's `STRINGS` are unchanged after the merge, and `missingKeys()` is `[]`;
  - a collision or a one-language key throws;
  - the honesty strings exist in both languages;
  - no string contains "preview helps", «يساعد الاستباق» or «الاستباق يساعد»;
  - no string says «حاسوب المحرك» without «المنمذَج».
- **`tap-unlock.test.mjs`:** 10 taps in 4000 ms unlock; 9 do not; 10 over 4001 ms do not; the source uses no storage API.

**Unchanged suites, re-run at every milestone:** `python -m app.test_simulation`, `python -m app.test_replay --full`, `node --test "app/static/sim/*.test.mjs"`, and `python verify_docs.py` after `git add`. Counts are read from each run.

---

## 10. Milestones

**M1: one C4 pair, one episode, side by side.**

- **Build order:**
  1. `agent_trace` with tests 1–5;
  2. `load_pair` with test 1b;
  3. `find_pair`, `scored_shas` and `verdict` for the C4 row, short line and gloss;
  4. `EpisodeStore`, the episode route and `install`;
  5. `agents-strings.mjs` and the page: profile, timeline with wait-at-edge, pause panel, verdict box, badge;
  6. the `scene.mjs` exports (approved, §11 Q2) and the chase view.
- The M1 page reads `?runs=runs_c4&seed=5&ep=1` into a read-only picker and still computes only on «احسب».
- **Verify:**
  - the tests pass with the `==` proof shown;
  - the lab suites and the node glob pass unchanged (`app.test_replay` and `app.test_replay --full` count different checks; read both counts from the runs, never from this file);
  - with the server started as `python -m app.server --simulation` on the system interpreter, the profile draws at once. `app\start-simulation.ps1` calls bare `python`, which resolves to the repository's `.venv`; that has FastAPI but neither stable-baselines3 nor torch, so `/api/agents/episode` would answer 503. Its banner also names only `/simulation`. M2, which touches the lab's entry points, can fix both;
  - *(Amended while building M1, 27 September: this line read "with `app\start-simulation.ps1` running". The line above it was corrected when the plan was written (walkthrough log, 26 September); at M1 the two runs printed 49 of 49 for `app.test_replay` and 59 of 59 for `app.test_replay --full`.)*
  - *(Amended while building M2, 28 September: M2 fixed the banner, not the interpreter. `app\start-simulation.ps1` now prints the `/agents` address and, when its own `python` has no stable-baselines3, says that `/agents` lists the experiments but answers 503 for an episode, and how to start the server with an interpreter that has it. Its last line still calls bare `python`, deliberately: the teammates' machines have other Python installations than this one, so no path written here would be right on all of them, and `/simulation` must start exactly as before. A ruling taken while building, not Jad's word; changing the interpreter is one line.)*
  - the first «احسب» shows «تحميل الشبكتين…» for about 5 s, and later builds move within about a second;
  - *(Amended while building M2, 28 September, after the Task 10 review: on the M2 verification the first build on a cold server drew its first frame after 15.8 s, and after 14.3 s on the re-run that followed the Task 10 fix (the 28 Sep prototype: 17.5 s and 17.3 s), each time with another session's work on the same machine; later builds drew theirs within 0.57 to 0.67 s. The 5 s above is M1's one measurement, not a bound.)*
  - a pause shows ten applied actions in Arabic with row 2 as a ceiling offset beside `map_kpa`, the held flags, the preview markers, the blind zeros, the weights, the damage, and the C4 short line with its one-seed clause (also in the scene strip);
  - it is checked at 1440 px and 390 px against the misreading table.

**M2: every experiment.**

- **Adds:**
  - `discover`, the status order (including the evaluate-string arm rule) and `/api/agents/catalog`;
  - the three-select picker with nothing selected, quoted table rows and weights;
  - Phase D episodes;
  - the `phase_d` and `d2` verdicts, short lines and the D2 C1 quote;
  - NOT BLIND on the Phase D blind car;
  - the `none`/`missing` states, and "scored artefact not recorded";
  - the `/simulation` nav link after the first link.
- **Verify:**
  - tests 6–13 pass;
  - there are three experiments of 8 pairs each;
  - sixspeed is greyed out with "no meta.json";
  - a Phase D episode climbs 12 % at 180 s;
  - the lab's nav shows the link on a phone;
  - `--full` passes the Phase D proof.

**M3: the jev paused moment.** *(Replaced by §10 of `2026-09-28-agent-replay-m3-design.md`.)*

- **Commits:** commit 1 is the `.gitignore` patterns alone. Then `jev.py`, the POST and status routes, the `server.py:43` amendment, `tap-unlock.mjs` and the panel.
- **Verify:**
  - tests 14–17 pass with the fake client;
  - Jad makes one real call with the key in his environment variable, and the page shows the model name, the measured latency, five choices with probabilities, the calibration caption, the telemetry sentence and the request body;
  - with no key, the panel shows «لا جواب — no_key» ("no answer: no_key") and nothing is sent;
  - a reload hides the panel.
- That call is not a test and is not recorded.

---

## 11. Questions for Jad — all three answered 26 September (see the log)

1. **Which label carries the gesture?** Decision 6 names `01 — REPLAY` (`i18n.mjs:61`, shown in `/simulation`'s footer). Decision 7 keeps that page untouched, and the jev panel must not share a page with recorded drives.
   - **Recommended:** this page's own footer label, `02 — AGENTS`, in the same place, with the same 10 taps in 4 s. The lab's label stays as it is and does nothing.
2. **May three `export` keywords go into `scene.mjs` and one key (`nav.agents`) into `i18n.mjs`?** Decision 7 asks for a shared car model and a link, but allows only the link as an edit to the page. Those two modules are loaded by `/simulation`, though they are not the page itself.
   - **Recommended:** allow both. They change no behaviour, and the lab suites are re-run to show it.
   - **The alternative:** copy `stage`, `supra` and `ribbonGeometry` into `agent-scene.mjs`, and give the link a static bilingual label. The copy can then drift from the lab's car, and in English mode the link would still read in both languages.
3. **How is jev asked, and how is its answer turned into an action?**
   - **Recommended:**
     - five `choice` levels per action: for the trims, both limits, "no change" and two midpoints; for the fan and pump, five evenly spaced duties;
     - the most probable level is jev's answer, and every probability is shown;
     - `state` carries the observation in named units, the episode's priority weights, and one fixed task paragraph naming the two damage thresholds read from `engine_env`. Without the thresholds, jev would not know what a good answer is; the agents learned them through their reward;
     - a `score` question with a weighted mean is rejected.

---

## Appendix: Review issues not taken

- Pre-import SB3 and torch in `install()` (feasibility, first-build latency). Not taken. It would add about 3 s to every `--simulation` start for a page that may not be opened. The latency is stated and shown as a `loading` state instead; the rest of that issue is taken.
- Add `env.map_b_prev` to each frame (rules-fidelity, boost trim). Not taken. It is the unscored baseline loop's pressure, and showing it invites the baseline-ECU-twin misreading cut in §1 (recon §8). The agent's own `env.map_kpa` is added.
- Put "the hottest recorded drive stayed above 850 °C for only 36 seconds" in the SIMULATED badge (honesty, badge). Not taken as worded. It is a document-sourced figure that would go stale (CLAUDE.md mistake 11), so the badge instead says "harsher than any recorded climb; not necessarily hotter than every recorded moment", with figures from `meta` only.
- Refuse any runs directory whose name contains "blind" (the alternative fix for the arm rule). Not taken. The evaluate-string rule was chosen instead, because it names the exact reason.

## Appendix: Review issues taken

- Boost trim (action 2) relabelled as an offset on the agent's own pressure-loop ceiling, confirmed by measurement today (−20 kPa left MAP at 179.0 against 178.6). Also: `map_kpa` added to frames; jev's task paragraph, question and option keys reworded; only actions 0–1 described as added to the modelled ECU.
- jev key moved out of the working tree (env var or `<APPDATA>/grad-project/typesafe_key`); `load_key` refuses repo paths; test 17 pins it; `.gitignore` kept as the second line.
- `finite()` rejecting numpy float32 (both reviewers): `jsonable` converts first, `held` becomes Python bools, `meta.act` and the road are converted; test 2 asserts no `None` and `json.dumps(allow_nan=False)`.
- Production loader untested: test 1b checks `load_pair` against `evaluate.py:370` (device, state_dict, zip sha, scored sha).
- Scored-artefact check: C4 zip shas are compared with `results/c4_seed<k>.txt` through `analyse_c4.BUDGET`; a mismatch refuses the pair; D2 and Phase D show "not recorded".
- Device line reworded: the result files do not record the device; torch and SB3 versions and the device are recorded in `meta`.
- Arm rule applied to evaluate's own string `f"{runs}/{name}"`; tested with `runs_zz_blind`.
- `GIT_OPTIONAL_LOCKS` set inside `live_fingerprint()`; `.git/index` added to test 11's snapshot.
- `test_read_only` scanning `app/test_agents.py` (both reviewers): raw-regex tokens, fh/`json.dump`/`shutil` fixtures, `app.test_replay --full` re-run at M1.
- `scene.mjs`/`i18n.mjs` edits (both reviewers) made open question 2, with copying as the stated alternative; the former Q2 and Q3 are merged into Q3.
- C4 "one seed wide": `C4_RESULT.txt:29` and `PREREGISTRATION_C4.md:633-635` quoted; the Arabic one-seed line is always visible.
- Compact surfaces (overlay, select, phone) carry a tested short verdict line per prefix instead of the bare cell; Phase D's NOT BLIND is on the blind car's scene label.
- `PREREGISTRATION_C4.md:41-43` quoted under the reading to define (i), (ii) and (iii); the C4 gloss carries 50 units, 300 000 steps, one grade step per episode, not converged, and one seed.
- D2's C1 budget: `PHASE_D2_RESULT.txt:86-89` quoted; "C1" added to D2's short line.
- jev panel: "nothing is saved" replaced by "this page saves nothing; the vendor may keep what is sent, in perpetuity, for telemetry (MCA §4.1)".
- jev probabilities and confidence captioned as a vendor claim, untested here, with the vendor's numeric-precision weakness.
- Fan and pump neutral tick relabelled as the results' "baseline ECU" constant, naming the modelled 0/0.4/1.0 schedule; «حاسوب المحرك المنمذَج» used throughout, and a node test pins it.
- dt caption built from `meta.train_dt` per arm, with the "known, unresolved, symmetry unmeasured" clause.
- "Roads" renamed episodes; the three weights shown in the picker and panel; Phase D's pair label says "same road".
- SIMULATED badge reworded to "a sustained climb harsher than any recorded climb; not necessarily hotter than every recorded moment" (see the not-taken note on the 36 s figure).
- jev level net values computed vectorised in float32 exactly as `neutral_action()`; bitwise equality confirmed by measurement today; test 14 pins it.
- First-build latency (about 5 s cold, under 1 s warm) stated in §3.3 and M1, with a `loading` state.
- Test 13 changed to an AST import scan.
- `sampleAt` dropped from the reuse list.
- `PlaybackClock.play()` rewinding at the edge handled by `playOrWait` and a waiting flag; node-tested.
- The `/simulation` nav link is inserted after the first link so phones still show it; `agents.css` restores the last link; test 12 pins the position.
- Car offsets widened to ±1.9, lane tints to 3.2 and the ribbon to 7.6 units; node-tested.
- Per-question `instructions` and per-option `criteria` written out; the shared paragraph goes in `state.task`; test 15 pins it.
---

## Walkthrough log with Jad

| date | section | outcome |
|---|---|---|
| 26 Sep | — | draft saved; walkthrough not started |
| 26 Sep | §1 | Jad asked how to open the page; the running `/simulation` lab was opened for him to picture it. He asked where the new changes were — none exist yet, by design. **He chose to answer only the three questions that need his decision (§11), then build**, rather than walk all seven sections. |
| 26 Sep | §11 Q1 | **Approved:** the gesture lives on the new page's own footer label `02 — AGENTS`, ten taps within four seconds. The lab's `01 — REPLAY` stays as it is and does nothing. (Refines decision 6, which named the lab's label before the new page existed.) |
| 26 Sep | §11 Q2 | **Approved:** the three `export` keywords in `scene.mjs`, the one `nav.agents` key in `i18n.mjs` and the one link in `simulation.html` — "lend the car" rather than copy it. Jad said he did not follow the explanation and approved anyway; the plain version given afterwards: the new page uses the same car drawing as the old one instead of drawing a new one. The lab suites are re-run to prove the old page unchanged. |
| 26 Sep | §11 Q3 | **Approved: five choices per action**, one call with five `choice` questions, as §7 specifies. Jad's reason: "it is an experiment and something personal" — jev is a trial, not part of the thesis. |
| 26 Sep | whole | **APPROVED** — banner changed. Next: the implementation plan (writing-plans). |
| 26 Sep | plan | The M1 plan (`docs/superpowers/plans/2026-09-26-agent-replay-m1.md`) departs from this design in five small, checked places, and this file defers to it: (1) the device and the torch/SB3 versions travel as top-level fields of every poll, not inside `meta`, because they are known only after the worker loads the networks; (2) the car half-width is 1.486 units (the hub torus), so the plan's constant is 1.49 and the non-overlap test uses it; (3) the chase view (~200 m) cannot contain the 15 s and 30 s preview markers (~540 m and ~1080 m ahead at 130 km/h) — it shows the markers in range, and the profile carries all four; (4) the profile gets a km scale and its preview ticks use the grade ramp; (5) the server is started with the system interpreter directly, because `app\start-simulation.ps1` ends in a bare `python`. §10's line that quoted a `--full` count was wrong and now says to read both counts from the runs. |
| 27 Sep | final review | **M1's whole-branch review: ready to hand to the student, with fixes.** No critical finding: the `==` proof holds, the store and the routes fail closed, nothing is written, and the verdict is quoted, never computed. The eight findings from the M1 walkthrough (Task 11): **F1 FIXED**: the grid drew across the road behind the cars on every climb; it is now a backdrop (opaque, no depth test or depth write, drawn first), pinned in `agent-scene.test.mjs`. **F2 LEFT FOR LATER**: the scored-artefact line's dot can wrap onto a line of its own; cosmetic, and the text beside it names the car. **F3 LEFT FOR LATER**: at 390 px the device line wraps between "SB3" and its version; phone width only, and the bidi is correct. **F4 FIXED**: the dt caption broke inside "H2-2" at 1440 px in Arabic; the hyphen is now U+2011, a non-breaking hyphen. **F5 FIXED**: the pump row carried the fan's note, which is false for the pump; each now has its own (§6). **F6 LEFT FOR LATER**: a cache hit ignores `preempt`, so an unwatched build keeps running; it costs only CPU and GPU time, a later «احسب» of an uncached episode still pre-empts it, and the M1 picker is read-only. **F7 FIXED**: «بلا تعديل» sat under the end of each trim bar, where it labelled +4.0 (Arabic) or −8.0 (English) as "no change"; it now stands on the zero tick. **F8 FIXED**: the quote of `PREREGISTRATION_C4.md` stopped at "The permutation test," just before its caveat; it now quotes item 2 whole (`:633-643`). Fixed in the same wave: the sign test's p is quoted under its heading with the permutation test's p (`C4_RESULT.txt:28-30`); the turbine limit reads 850, not 849.9, and the Arabic readings say «°م»; a pause-panel error is no longer shown as the WebGL message; the store test's 'building' wait is gated. **Rulings, not Jad's word:** the review asked for Jad's approval on F5 (the pump's own sentence) and F8 (quote the whole item, and start the sign-test quote at its heading). The fix wave's controller decided both instead, because each makes the page more faithful to the code and to `results/`; reversing either is one commit. **Task 10b's wording ruling**, also the controller's: «الاختباران مختلفان» ("the two tests are different") became «الاختباران لا يتفقان» ("the two tests disagree"), matching the English line; §4 now says the same. **Correction:** the milestone commit `e7030f0` says `/api/agents/episode answered 503` under the lab's launcher. That was not observed in that task; it is what the `.venv`'s package list implies (no torch, no stable-baselines3). The commit is history and is not rewritten. |
| 28 Sep | M1 in use | **Jad tried M1 and found two gaps, both correct.** (1) The page's own nav link opens `/agents` with nothing selected, and in M1 the three lists are read-only, so the page cannot be used from the link at all; it works only when opened with `?runs=runs_c4&seed=5&ep=1`. The handoff should have said so. (2) The replay lab has no link to `/agents`, so from the lab there is no way back. Both were planned for M2 (§10: the three-select picker; the `/simulation` nav link after the first link). **Offered:** a one-hour C4-only picker plus the link, or the whole of M2. **Jad chose the whole of M2** ("I am not in a hurry"). The M2 plan is the next document. |
| 28 Sep | M2 built | **M2 is built and verified; the milestone commit carries every suite's output.** Both gaps Jad found on 28 Sep are closed, and both were checked in the browser starting FROM THE NAV LINK: the replay lab links to `/agents` right after its first link, so phones keep it, and `/agents` opened from its own link loads the catalog, selects nothing and offers three working selects (experiment, pair, episode) whose choice is kept in the address. All three experiments run; Phase D's blind car is named as possibly memorising its one road wherever it is named; `runs_sixspeed_18sep` is greyed as "no meta.json", and the list of pairs that cannot run names both of its arms. **Rulings taken while building, not Jad's word**, each recorded as a dated amendment above and each one commit to reverse: the d2 quote runs to `:35` and the post-hoc quote to `:76` (whole items); the not-found text names every missing file, not only the first (§4, verdict states); a recorded zip sha that differs is labelled `mismatch` (§4, the pair check); an unreadable `final.zip` is incomplete; the catalog's shape as served; the Phase D citation `:33-40`; the picker's rules, including Phase D's «12.0٪» where §6 wrote «12٪» and the list of pairs that cannot run; a missing stable-baselines3 said once under the picker; the lab launcher's banner fixed (the `/agents` address and a no-stable-baselines3 warning) and its interpreter deliberately left as it was, because the teammates' machines differ. Every ruling, with what it costs if wrong, and what M2 left for later, is in the build record for M2 below, beside M1's. Every other item of the M1 build record's left-for-later list stays deferred as written there; M2 took none of them. That includes, in code M2 edits: the store's untested preempt during the loader and two networks on different devices (Task 5), preempt=true with since omitted untested on the route (Task 6), and the no-write snapshot watching runs_c4/*_seed0 only (Task 6). |
| 28 Sep | M2 final review | **Whole-branch review: ready to hand to the student; no critical or important CODE defect.** Important 1: the lab launcher's bare `python` resolves to the repository `.venv`, which has no stable-baselines3, so `/agents` started from the launcher can never compute; no code change — ruling 8 stands — the handoff instead gives Jad the literal system-Python command, run from the repository root: `C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe -m app.server --simulation`, and says the first episode's first frame takes about 15 s cold. Minor 1, a WORDING PROPOSAL AWAITING JAD, not a code defect: the pair row "blind − sighted +x.x" does not say it is a difference of MEDIAN damage over 20 episodes, nor which sign means the blind car took more damage, and the M1 line "no difference between the cars is computed here" now sits beside a quoted difference. Minor 2, left for later: the "(…; not this episode)" qualifier is chosen by protocol and would vanish for a mixed-protocol experiment — impossible on today's tree. Minor 3, left for later: at 390 px the lab's active nav label wraps onto two lines because of the third link — fixing it needs lab CSS, outside what Jad approved. |
| 28 Sep | M2 in use | **Jad looked at M2 and raised four points.** (1) jev is not there yet -- correct: it is M3. (2) "The pause feature, to see what the agents decided, is not there" -- the pause panel exists since M1 (side column, under the verdict box, after «احسب»); Jad did not find it, which is a discoverability finding about the page, to be walked through with him. (3) **New request: add Laya beside jev in M3.** Laya is a LOCAL model at `C:/Users/admin/Documents/Local AI/laya` (convaiinnovations/laya-multilingual, revision e4e9ddf, Apache 2.0, about 0.65 GB of weights, its own `.venv` with PyTorch; `try_laya.py` calls `laya.load(dir, device=...)` then `agent.predict(state, QUESTIONS)`, where QUESTIONS has the same shape as jev's -- `type: choice`, `instructions`, `criteria` -- and each answer carries `choice` and `probabilities`). It needs no API key and sends nothing off the machine; its own README says an example result does not mean it suits engine control. The M3 design must be revisited to hold two models behind one question set. (4) "What is the difference between the experiments? I am confused" -- answered in chat first, one idea at a time. |
| 28 Sep | M3 revisit, Q1 | Jad found the pause panel once pointed to it ("the decision applied from second k to k+1", side column, under the verdict box); the discoverability finding stands for M3 to consider. **Decided: Laya is hidden WITH jev** behind the same ten taps on `02 — AGENTS`, and appears together with it, so the page in front of the committee is unchanged and both models stay Jad's personal trial. |
| 28 Sep | M3 revisit, Q2 | **Decided: one button per model** ("ask jev", "ask Laya"), each asking about the same paused second with the same questions, each with its own answer column and its own errors. Jad's reason: "I may have no credit on jev, so the other must not fail with it" -- a jev failure (no key, no credit, network) must never block or hide Laya's answer, and the reverse. Recommended was one button for both; Jad's reason outranks it. |
| 28 Sep | M3 revisit, Q3 | Told the Laya spike's result (`2026-09-28-laya-spike.md`: runs locally in 34 ms with no network, but on one probe its answers followed the ORDER of the options, not the engine state), Jad chose: **add Laya with an automatic order check** -- every "ask Laya" asks the same five questions twice, options in the design's order and reversed, and the page shows for each action whether the choice held (the same level both times) or changed. Free and about 70 ms. Not asked for jev (each jev call is paid); whether jev shows the same position effect is unknown until Jad tries it with his key. |
| 28 Sep | M3 revisit, Q4 | **Decided: move the pause panel directly under the play bar**, with the empty-state line «اضغط احسب، ثم أوقف العرض عند أي ثانية لترى ما قرّره كل وكيل» (the M3 design's §7.8 option 1, recommended), so both it and the models panel after it are on screen. The verdict quotes stay open as they are. **The M3 design (`2026-09-28-agent-replay-m3-design.md`) is APPROVED**; the plan is next. |
| 29 Sep | M3 built | **M3 is built and verified; the milestone commit carries every suite's output and the verification record.** jev and Laya sit behind ten taps on `02 — AGENTS`, forgotten on reload, one button and one column each; Laya asks twice, options forward and reversed, and each action says held or changed. Every suite passed; the M3 design's amendments give the counts. The browser check passed all 84 of its checks at 1440 and 390 px, in Arabic and English: locked, the panel is hidden and nothing is asked; the pause panel sits under the play bar and says what to do before «احسب»; an episode played to its natural end enables both buttons at the last second with no seek; Laya answered on this machine (cuda), and test 20 ran it for real; jev with no key, and jev forced to fail through a refused local proxy, each stayed in jev's column while Laya answered. After a Laya press, a hard kill of the server, Ctrl+C in its console window, Ctrl+Break and closing that window each left no Laya worker. The hard kill shows the worker ending when its input closes. The Ctrl+C, Ctrl+Break and close rows do not show that `close()` or `atexit` ran, because the worker shares its console with the server and receives the same event; those rest on the bridge tests and test 20. `LAYA_HOME` was unchanged. No real jev call was made. An observation, not a result: at second 312 of `runs_c4/5/1`, Laya's choice changed with the order for spark, lambda, fan and pump and held for boost. Every departure from the M3 design is a dated amendment there ("Amendments while building M3"); the controller's rulings and what was left for later, the visible-text findings for the final review among them, are in the build record for M3 below. |
| 29 Sep | M3 final review | **Whole-branch review: ready to hand to the student, with fixes; nothing critical.** **Important 1 FIXED:** in the Arabic page a signed number inside a sentence was drawn with its sign on the right of its digits, in the models panel's choice and reversed lines and in M1's held-command line «أمر به»; each such number now sits in a left-to-right isolate, as M2's pair row already did (the isolate is now one shared helper, `isolateLtr` in `agent-picker.mjs`, which `formatDiff` also uses), and the choice line's network value uses the levels' minus sign (U+2212) instead of a hyphen-minus. **Minor 2 FIXED:** the two Arabic latency lines isolate their Latin runs (the measured milliseconds with their unit, the device, and jev's vendor range "70–500 ms"), so a Latin reader no longer sees "cuda على ms 65". **Minor 3 FIXED:** §2's module count, `install`'s four-argument signature and M3 dependencies, the "[new; review change C4]" tag, and two line references in the build record for M3. **Minor 1 LEFT FOR LATER:** the pump's bars and choice read 0.48 and 0.82 for the options "pump 47.5 %" and "pump 82.5 %" (float32 levels rounded to two digits), under a line that calls the five duties evenly spaced. **LEFT FOR LATER, and to be put to Jad before his first real jev call:** a failed press at a second erases a successful answer held at that second, so a paid jev answer can be lost to a later failure there. All the controller's rulings in the build record for M3 stand. |

---

## Build record for M1 (27 September 2026): every ruling the controller made, and what was left for later

M1 was built task by task (11 plan tasks plus one controller-added task, 10b), each by a fresh implementer and checked by a fresh reviewer, then one whole-branch review and one fix wave. The working ledger was scratch and has been deleted; this section is its permanent record, so that no decision taken on Jad's behalf lives only in a deleted file. Commits 3e66189..d22f889 on JMF-2340550-sep17.

### Rulings (each with what it costs if wrong)

1. Ruling: work in place on JMF-2340550-sep17, no git worktree — the == proof needs runs_c4/ and the page needs app/static/vendor/three, both gitignored and present only in this working tree; the branch is Jad's own, not main — cost if wrong: discarding the work means resetting this branch instead of deleting a worktree.
2. Ruling: each task runs as one Workflow (implementer -> task reviewer -> up to 5 fix rounds, fresh fixer each round carrying the report file, rounds 4-5 on opus), not as resumed Agent calls — ultracode is on and workflow agents cannot be resumed; the skill allows a fresh implementer carrying brief + report + findings — cost if wrong: fix rounds 1-3 lose the implementer's live context and may take an extra round.
3. Ruling: implementers on sonnet for transcription-heavy tasks (1, 3, 4, 7), opus for the rest (2, 5, 6, 8, 9, 10, 11); every reviewer on opus — memory: Fable subagents exhaust their quota; the plan carries complete code — cost if wrong: an extra fix round on a sonnet task.
4. Ruling: the pre-flight table below is built from the plan skeleton's per-task files and interfaces plus targeted greps of the briefs, not from reading all 6 873 plan lines into the controller — the plan's critic already assembled all ten build tasks into a scratch copy and ran every suite (37 tests OK, proof PROVEN on cuda) — cost if wrong: a cross-task conflict in the page group (revised AFTER that assembly run) surfaces in review instead of here.
5. Task 3: Ruling: the SMALLER THAN THE MEI gloss stays gated on the result anchor alone (plan-mandated, agent_catalog.py:209/270) — when any anchor is missing the verdict state is 'missing' and the box already says the verdict line was not found and not to read the agents without it — cost if wrong: a gloss claiming "not settled / one seed" could sit beside a results file that no longer says so, under a visible 'missing' warning.
6. Task 3: Ruling: an unreadable final.zip stays 'ready' with 'budget unreadable' (plan-mandated, agent_catalog.py:115) — in M1 only C4 runs, whose recorded scored sha then differs and refuses the pair; a prefix with no result file fails at SAC.load as a store error reported once — revisit for M2 discovery — cost if wrong: a corrupt zip in a future runs_X shows as runnable until the build errors.
7. Task 3: Ruling: find_pair runs on EVERY poll in Task 6's route (plan text, task-6 brief :431), hashing both zips each time — fail-closed on every request; the design asked for "before every build" — cost if wrong: tens of ms of CPU per 400 ms poll competing with the tracer; Task 11's timing will show it.
8. Task 8: Ruling: parseEpisodeQuery accepts lowercase run names only (/^runs[a-z0-9_]*$/), departing from the brief — it must match agent_catalog.RUNS_NAME after Task 3's fix, or the picker would accept runs_C4 that the server 404s — cost if wrong: none found; the plan text still shows the old regex (carried to Task 9).
9. Ruling: add Task 10b (controller-added, brief task-10b-brief.md) BEFORE Task 11 for Task 9's out-of-scope must-fix — the C4 verdict's "300 000" swaps to "000 300" in Arabic; Task 11 must verify the fixed verdict on screen — cost if wrong: one extra small task.
10. Ruling: in the same Task 10b, SHORT_VERDICT c4 Arabic «الاختباران مختلفان» becomes «الاختباران لا يتفقان» (Task 3 minor) — the English says "disagree"; «مختلفان» reads "different" — cost if wrong: departs from the design's verbatim Arabic short line (spec §4), which Jad did not review word by word.
11. Ruling: F5 — the pump row gets its own note (tick_pump: the results' constant 1.0, which is also what the modelled ECU runs the pump at throughout), not the fan's schedule — the shared note was false for the pump (engine_env.py:265 schedules only the fan; :764-765 leaves the pump at thermal.py's default 1.0) — cost if wrong: departs from the design's one text for rows 3 and 4, which Jad did not review word by word.
12. Ruling: F8 — the PREREGISTRATION_C4.md item-2 quote extends to the whole item (633-643), ending on "whether the average effect is below 50 is not settled"; and the C4_RESULT.txt 'seeds' quote starts at its H1 heading (28-30) with the permutation p beside the sign p — a quote cut before its caveat, or a lone p-value, misleads a committee — cost if wrong: a longer verdict box than the design drew.
13. Ruling: the reviewer asked for Jad's approval on F5 and F8; decided here instead under the skill's rulings-not-stalls rule, because both make the page MORE faithful to the code and to results/ and neither is irreversible — cost if wrong: Jad disagrees and the two strings are changed back in one commit.
14. Ruling: the turbine limit is displayed rounded to 850 (the payload keeps 849.85) and Arabic readings use «°م» — the documents and results say 850; 849.9 invites a question with no answer — cost if wrong: none found.

### Left for later (triaged by the final review as not blocking the handoff)

- Task 1: minor (deferred): jsonable() on a 0-d ndarray raises a misleading TypeError (agent_trace.py:42; use jsonable(x.tolist())).
- Task 1: minor (deferred): jsonable str(k) keys can collide silently (agent_trace.py:41).
- Task 1: minor (deferred): route() does not assert len(v) == STEPS+1 (agent_trace.py:92).
- Task 1: minor (deferred): no assertion that build_cycle returns a fresh cycle each call, nor array equality with RR.climb (test_agents.py:64).
- Task 1: minor (deferred): report wrongly says np.asarray copies; the cycle is still not mutated (test pins byte identity).
- Task 2: minor (deferred): on a diverged step held = [True]*5 while cmd/act are null (agent_trace.py:104) — CARRY to Task 10: never show the "held" line when values are null.
- Task 2: minor (deferred): _car docstring says held compares to the network's command; it compares to _rescale(cmd) (agent_trace.py:92-93).
- Task 2: minor (deferred): run_lanes results are raw floats (NaN on divergence) — CARRY to Task 5/6: pass results through jsonable before serving.
- Task 2: minor (deferred): test_frames_are_the_episode does not check turb_c/oil_c/torque against info (test_agents.py:295-325).
- Task 2: minor (deferred): proof skips (UNPROVEN) without runs_c4/SB3; suite still reads OK — reporting must read skips (test_agents.py:269-279).
- Task 3: minor (deferred): commit 542988d pasted only the last line of app.test_replay (count present, transcript absent).
- Task 3: minor (deferred): read_agent on a missing directory returns 'incompatible (no meta.json)' not KeyError (agent_catalog.py:82) — matters for M2 discovery.
- Task 3: minor (deferred): test gaps — unknown protocol, cross-arm protocol mismatch, verdict() with results file absent; GIL_OPTIONAL_LOCKS assertion wording (test_agents.py:291).
- Task 3: minor (deferred): comment at agent_catalog.py:102 says run_phase_d hands f"{runs}/{name}"; it is os.path.join (backslash on Windows).
- Task 3: minor (deferred): Arabic «الاختباران مختلفان» reads "different", not "disagree" — prefer «الاختباران لا يتفقان» (agent_catalog.py:202).
- Task 3: minor (deferred): MISSING_TEXT names only missing[0] (agent_catalog.py:265).
- Task 3: minor (deferred): comment at agent_catalog.py:36-38 says "the eight real C4 agents" — there are sixteen agents, eight pairs (team/jad.md: say "eight pairs").
- Task 4: minor (deferred): device assertion compares two 'auto' loads, so a CPU-only machine cannot catch a hard-coded device (test_agents.py:122; plan-mandated).
- Task 4: minor (deferred): pair_paths duplicates find_pair's name/seed gate; they already differ on Path vs str (agent_api.py:46-49; plan-mandated).
- Task 4: minor (deferred): pair_paths accepts a missing runs dir; relies on find_pair running first (agent_api.py:50).
- Task 4: minor (deferred): docstring "which is cuda on this machine" describes one laptop (agent_api.py:57; plan-mandated).
- Task 4: minor (deferred): local re-imports in the loader test (test_agents.py:101-104; plan-mandated).
- Task 5: minor (deferred): StoreTests _wait_for 'building' has a ~50 ms window — timing-sensitive, may flake under load; a gated fake tracer would make it stable (test_agents.py:466). Its since-slicing assertion cannot fail with since=0.
- Task 5: minor (deferred): untested — preempt during the loader aborts before the tracer; two networks on different devices -> 'build failed: RuntimeError' (agent_api.py:190-193).
- Task 5: minor (deferred): a superseded build that then raises still records _errors[key]; the next preempting request is spent on the stale error (agent_api.py:207; ReplayStore has the same policy).
- Task 5: minor (deferred): agent_catalog imported under two names (agent_api.py:21-22; plan-mandated).
- Task 5: minor (deferred): a preempt after the last frame still caches the complete trace — harmless (agent_api.py:497-498).
- Task 6: minor (deferred): exceptions other than KeyError/Refused (corrupt zip, git failure) reach FastAPI's default 500 without Cache-Control: no-store (agent_api.py:320-333).
- Task 6: minor (deferred): find_pair on every poll re-hashes both zips (agent_api.py:320) — see the Task 3 ruling; Task 11 timing to confirm.
- Task 6: minor (deferred): route comment "no path is ever built from a request" overstates; validated names are joined into a path (agent_api.py:195-199; plan text).
- Task 6: minor (deferred): 1 <= int(ep) <= 20 hard-codes the table length (agent_api.py:313; plan-mandated).
- Task 6: minor (deferred): neutral_phys re-types _rescale's formula without the clip (agent_api.py:250).
- Task 6: minor (deferred): the no-write scan's self-test never shows the pathlib pattern firing (test_agents.py:493-499; plan-mandated).
- Task 6: minor (deferred): the no-write snapshot watches runs_c4/*_seed0 only; route tests also read seed5 and runs_sixspeed_18sep (test_agents.py:426-428; plan-mandated).
- Task 6: minor (deferred): preempt=true and 'since omitted still carries meta/road' untested.
- Task 6: minor (deferred): commit 514798d message lacks the "Ran 33 tests" count line (tail -3 cut it).
- Task 7: minor (deferred): the «المنمذَج» rule checks anywhere in the string, not adjacency (agents-strings.test.mjs:108; plan-mandated).
- Task 7: minor (deferred): no test pins the exact 65-key set (agents-strings.test.mjs).
- Task 7: minor (deferred): mergeStrings throws TypeError not its documented Error on a null table (agents-strings.mjs:224).
- Task 7: minor (deferred): the bidi pin checks presence, not position (agents-strings.test.mjs:121-131).
- Task 8: minor (deferred): camera pose, `grid`/`centre-dashes` names and dark-ramp direction not asserted (agent-scene.test.mjs:344-418).
- Task 8: minor (deferred): a new THREE.Color per visible post per frame (agent-scene.mjs:179; plan-mandated).
- Task 8: minor (deferred): lane colours duplicated as literals beside the --agent-* tokens (agent-scene.mjs:95; plan-mandated).
- Task 8: minor (deferred): createEpisodeRoad does not check non-empty / equal-length arrays (agent-view.mjs:492-516).
- Task 9: minor (deferred): starlette BlockingPortal DeprecationWarning printed by PageTests (test_page_assets_ids).
- Task 9: minor (deferred): theme toggle tooltip reads "switch to dark" in dark mode after a language switch (same as the lab, main.mjs:590/600).
- Task 9: minor (deferred): agents.mjs has little behavioural test coverage; the new agents-page-run.test.mjs fake DOM holds four ids only.
- Task 9: minor (deferred): lane tokens never red/green, phone nav restore, <1100 px ordering untested (checked by inspection).
- Task 9: minor (deferred): #profile role=img unnamed until a road arrives (agents.html:90).
- Task 9: minor (deferred): pre-JS fallback text in agents.html differs from the string table (replaced at boot).
- Task 9: minor (deferred): poll cadence is 400 ms + latency, not fixed; assertion messages in agents-page-run.test.mjs read backwards; retry button removed while focused -> focus falls to <body>.
- Task 10: minor (deferred): renderStopped runs only when k changes; a lane that stops while paused mid-build is announced late (agents.mjs:566-592).
- Task 10: minor (deferred): renderStopped uses LANE_LABEL[1] not BLIND_LABEL[protocol] — matters in M2 for Phase D (agents.mjs:569).
- Task 10: minor (deferred): test_chase_is_optional does not follow `export ... from` (test_agents.py:689).
- Task 10: minor (deferred): boost row shows "— kPa" on a diverged step (agents.mjs:507); fmtAction prints "−0.0" for tiny negatives (agents.mjs:416-423).
- Task 10b: minor (deferred): commit f88d51a pastes only the test_replay summary line.
- Task 10b: minor (deferred): the regex \d \d{3}\b misses a group running straight into Arabic letters (test_agents.py:411; drop \b or use (?!\d)).
- Task 10b: minor (deferred): task-10b-report.md prose has literal U+202F where it meant the escape (report only).
- Task 11: minor (deferred): design spec §4 (line ~286) and plan (line ~1312) still carry «الاختباران مختلفان» after Task 10b — prose drift (mistake 11 shape).
- Task 11: minor (deferred): Starlette/anyio DeprecationWarnings also appear in the lab suite output (pre-existing).
- Task 11: minor (deferred): milestone commit message says "/api/agents/episode answered 503" in past tense; not observed in this task.
- Final re-review: agents-page-run.test.mjs imports registerHooks from node:module (Node >= 22.15); app/package.json pins no engines, so an older Node fails the whole file instead of skipping.
- Final re-review: the test 'a chase scene that cannot be created...' reads the scene the previous test created; run alone it throws a TypeError (test-order coupling).
- Final re-review: createChaseScene's catch calls view.dispose(); if dispose itself throws it masks the original build error.
- Final re-review: at 1440 px the Arabic dt caption breaks between '(AUDIT2.md' and 'H2-2)' at the space; H2-2 itself no longer breaks (a no-break space or an isolate would keep the citation whole).
- Final re-review: the M1 plan file still carries «مختلفان» and agents.action.tick_duty; M2 must copy from this spec, not from the plan.
- Left for later by the final review's triage: F2 the scored-artefact dot wraps alone (agents.css:106); F3 the device line wraps inside '(torch ..., SB3 2.9.0)' at 390 px; F6 a cache hit ignores preempt, so an unwatched build keeps running (agent_api.py:157-161).

## Build record for M2 (28 September 2026): every ruling the controller made, and what was left for later

M2 was built task by task from `docs/superpowers/plans/2026-09-28-agent-replay-m2.md` (10 tasks), each by a fresh implementer and checked by a fresh reviewer, with fix rounds where a review asked for them. The working ledger lives under `.superpowers/sdd/`, which is gitignored scratch; this section is its permanent record, so that no decision taken on Jad's behalf and no deferred item lives only in a scratch file. Commits `8f6789b` (the plan) through `f2e3e5f`, and the commit that adds this record, on JMF-2340550-sep17. Another session committed unrelated files on the same branch while M2 was built (`plot_*.py`, `CLAUDE.md`, `CHECKPOINT.md`, `team/`); every M2 commit's subject starts "Agent replay M2", and the reviews judged only those.

### Rulings (each with what it costs if wrong)

1. Ruling: the same setup as M1 (build record for M1, rulings 1 and 2): in place on JMF-2340550-sep17, one Workflow per task (implementer, reviewer, up to 5 fix rounds, a fresh fixer carrying the report), reviewers on opus — cost if wrong: as in M1.
2. Ruling: implementers on opus for every M2 task, because each task integrates with M1's committed code rather than transcribing new files, and M1's sonnet tasks needed the more fix rounds — cost if wrong: a higher token cost only.
3. Ruling: build without a separate plan review by Jad: he cannot review a 6 000-line English plan, chose "the whole of M2", and was told the build would follow the plan as M1's did — cost if wrong: Jad wanted to see the plan first; nothing is irreversible, every commit is on his own branch.
4. Ruling (plan critic's gap 1): without stable-baselines3 the page says so at the picker as soon as the catalog arrives (`sb3` false), not only after a full selection — cost if wrong: one extra notice line.
5. Ruling (gap 2): the catalog does not carry `analyse_phase_d2.load`'s `incomplete` list in M2, because every table is complete today and the gap cannot be seen — cost if wrong: an incomplete future results file reads "no row for this seed" without naming why.
6. Ruling (gap 3): a refused pair shows ALL of its problems (both arms, every line of `check_pair`'s list), not only the first, because §8 says "with reason and fields" — cost if wrong: a longer list under the picker.
7. Ruling (gap 4): Phase D's episode note prints «12.0٪» (one decimal, like every other grade on the page), and §6 is amended — cost if wrong: none found.
8. Ruling (gap 5): the lab launcher gets the `/agents` banner and the no-stable-baselines3 warning only; its interpreter is NOT changed, because the teammates' machines have other Python paths (§10 amendment) — cost if wrong: the launcher still starts a server whose `/agents` answers 503 on a `.venv` without stable-baselines3, now with a printed warning.
9. Ruling: Task 9's edit to `start-simulation.ps1` (banner and warning) is accepted although Jad's approval of 26 Sep named only three exports, one i18n key and one link: §10 already assigned the launcher to M2, and the edit changes nothing the lab does — cost if wrong: one more lab file touched than Jad approved.
10. Ruling (Task 2, carried to Task 3): an arm whose recorded zip sha DIFFERS from its `final.zip` is labelled `scored` = `mismatch`, a third value beside `match` and `not recorded` (§4 amendment) — cost if wrong: one more value the page renders.
11. Ruling (Task 6): `computeState` checks stable-baselines3 BEFORE the selection: on a machine without it nothing can run, so the warning beats "choose a pair" — cost if wrong: that machine shows only the warning.
12. Ruling (Task 7): the page uses Task 6's `refusedPairs`, `scoredKey` and `agents.verdict.scored_mismatch` instead of the inline logic its brief predates, so `mismatch` reaches the page and nothing is duplicated — cost if wrong: none found.
13. Ruling: two Task 7 minors were folded into Task 8, which edited the same files: the refused-pair and refused-experiment labels put the name inside an isolate, so "runs_sixspeed_18sep (no name recorded)" is not drawn with a mirrored parenthesis in Arabic; and after a failed catalog request the picker note stops saying the list is loading — cost if wrong: two more small edits in Task 8.
14. Ruling (Task 10, fix round 1, taken by the fixer; the review allowed a fix or a ruling): the C4 misreading at the closed experiment select is fixed in code (the whole short line under the select, `f2e3e5f`), not exempted by a ruling, and Steps 1 to 5 of the verification were run again (§6 amendment) — cost if wrong: the short line shows twice in the side column.

### Carried between tasks, and closed

- Task 1 to Task 10: §4 said the not-found box names one `results/<file>`; the code names every missing file, sorted and joined by " · " (§4 amendment).
- Task 3 to Task 4: an exception from `analyse_phase_d.parse` (a non-UTF-8 results file) would have failed the whole catalog; the catalog route's fixed-text 500 covers it.
- Task 3 to Task 7: the page renders `scored` = `mismatch`.
- Task 8 to Task 10: Phase D's long blind lane label fits over the chase view at 390 px, below both cars and over neither; the refused sixspeed pair's name is drawn with its parentheses the right way round at 1440 and 390 px.

### Taken from M1's left-for-later list

F6 (a preempt answered from the cache now cancels the other build); a superseded build that fails reports nothing; `renderStopped` named every blind car alike; `read_agent` on a missing directory; an unreadable `final.zip` showed ready (M1 ruling 6 reversed); the Task 3 test gaps (unknown protocol, cross-arm protocol, results file absent); `MISSING_TEXT` named only the first file; the 10b grouped-number regex; the `agent_catalog` comments at `:36-38` and `:102`; non-KeyError failures reached FastAPI's 500 without no-store; the lab launcher named only `/simulation`. Every other item of M1's list stays deferred as written there, including, in code M2 edits: the store's untested preempt during the loader and two networks on different devices, preempt=true with since omitted untested on the route, and the no-write snapshot watching `runs_c4/*_seed0` only.

### Left for later (M2's own; none blocks the milestone)

- Task 1: minor (deferred): the comment at `agent_catalog.py:260` calls the INCONCLUSIVE gloss `PHASE_D2_RESULT.txt:31-33` "in the team's words", but it paraphrases ("the team cares about" against the file's "would care about") — say "paraphrasing".
- Task 1: minor (deferred): the whole-item test checks the blank line after an item, not before (start lines are pinned).
- Task 1: minor (deferred): `verdict()` is called twice in `test_d2_and_phase_d_verdicts`.
- Task 2: minor (deferred): an existing but unreadable results file skips the sha check with `result_file` true (`agent_catalog.py:180`; M1 behaviour).
- Task 2: minor (deferred): no test of `read_agent` on a path that is a FILE, not a directory.
- Task 2: minor (deferred): the comment at `agent_catalog.py:109-112` paraphrases `run_phase_d.py:330`.
- Task 3: minor (deferred): `warnings.catch_warnings` in `table_rows` is not thread-safe under FastAPI's threadpool (`agent_catalog.py:156`).
- Task 3: minor (deferred): `AGENT_NAME` with `int()` lists `sighted_seed01` as seed 1 with both arms missing (`agent_catalog.py:189-195`; M1's regex).
- Task 3: minor (deferred): `table_rows` reads the repository's `results/` whatever `root` is (`agent_catalog.py:141-160`).
- Task 3: minor (deferred): in a half pair whose present arm is refused, `reason` is that refusal, not the "missing" line (`agent_catalog.py:199-204`); the page lists every line (ruling 6).
- Task 4: minor (deferred): the fixed-text 500s log nothing on the server console (`agent_api.py:157-159`, `:212-213`); a traceback to stderr would help an operator without writing to disk.
- Task 4: minor (deferred): `catalog()` runs `jsonable` over constants that are already JSON (`agent_api.py:129-132`).
- Task 4: minor (deferred): a precondition globs `ROOT/results` where `load` reads `analyse_phase_d2.HERE/results` (the same directory today).
- Task 4: minor (deferred): `PageTests.test_page_assets_ids` fails instead of skipping on a fresh clone without the vendored Three.js (M1).
- Task 4: minor (deferred): an implementer created and deleted an empty `x.py` in `%TEMP%`, the machine trap the environment block warns about; nothing was left behind.
- Task 5: minor (deferred): going back to a key whose build was just cancelled, before its worker exits, answers from the doomed build until the next poll restarts it (`agent_api.py:163`, `:173`); it heals itself, and the progress may step back.
- Task 5: minor (deferred): the join-all-builders loop is written out four times in `test_agents.py`; a shared helper would do.
- Task 6: minor (deferred): `_shape` compares only `experiments[0]` and the first item of each list, and never values; its docstring says more.
- Task 6: minor (deferred): the catalog fixture is served under `/static/sim` in every server mode (tags, zip shas, verdict quotes; no machine path), as M1's test files there are.
- Task 7: minor (deferred): a non-200 catalog shows only "HTTP <status>", dropping the safe fixed-text detail (`agents.mjs` `loadCatalog`).
- Task 7: minor (deferred): the nav test's late-frame assertion cannot tell the fix from its absence; only `requests.length === 0` pins it.
- Task 7: minor (deferred): `clearEpisode` repeats `compute()`'s reset block.
- Task 7: minor (deferred): `loadCatalog().catch(console.error)` hides a render error from the page.
- Task 8: minor (deferred): `state.preempted` belongs to the page, not to the build it stopped, so with two viewers "stopping the previous episode" could describe the other viewer's build (`agents.mjs:403`, `:428`).
- Task 8: minor (deferred): the comment and test cite UAX #9 N1 and N2 for the mirrored parenthesis and ignore N0 (paired brackets); the isolate is harmless.
- Task 8: minor (deferred): `experiment_empty` and the selectable experiment option print the name without an isolate; unreachable on today's tree.
- Task 8: minor (deferred): the extra stopping test never asserts the URL of the requests it answers, and one Task 7 test message now reads slightly wrong.
- Task 9: minor (deferred): a redundant `assertIsNot` on strings, and the conditional stable-baselines3 note is not pinned by a test.
- Task 9: minor (deferred): the launcher's suggested command omits `--http-port $Port`, and any non-zero probe exit reads as "no stable-baselines3".
- Task 4, 9 and 10: minor (deferred): the suite output carries third-party deprecation warnings (Starlette's httpx testclient, anyio's `BlockingPortal`), printed by `test_page_assets_ids`; M1 recorded the same.
- Task 10: minor (deferred): M1 F2 is visible at 390 px: the blind car's scored line wraps so its dot sits on a line of its own (`agents.css`, `.verdict-scored li`).
- Task 10: minor (deferred): at 390 px a quoted results line that wraps continues flush left, while the file's own lines start indented, so a quote reads unevenly (`agents.css`, `.quote pre`); nothing is clipped.
- Task 10: minor (deferred): the cold first frame is about three times §10's "about 5 s" (§10 amendment).
- Task 10: known limit: the no-write snapshot (test 11) raises when another session writes to the shared working tree during the run. It did so three times on 28 Sep: the first run named no file, the second only `.git/index`, and the third — the Task 10 fix round's first `--full` run, from the other session's commit `f96d5b4` — also `.git/index`; the re-runs with HEAD unchanged before and after passed.
- Correction: the milestone commit `fa4e4aa` says the first default run failed because the other session "committed"; that run ended at 11:19:37, before that session's commit at 11:21:18, so the cause was its uncommitted writes. The same commit's walk passed "C4 is a clean negative" against its own evidence (ruling 14). The commit is history and is not rewritten.

## Build record for M3 (29 September 2026): every ruling the controller made, and what was left for later

M3 was built task by task from `docs/superpowers/plans/2026-09-28-agent-replay-m3.md` (11 tasks), subagent-driven as M1 and M2 were. The working ledger lives under `.superpowers/sdd/`, which is gitignored scratch; this section is its permanent record, transcribed by Task 11, so that no decision taken on Jad's behalf and no deferred item lives only in a scratch file. File and line references are as each review gave them, at that task's commit. Commits `5dda9d8` (the plan) through `1a80a6a`, and the commit that adds this record, on JMF-2340550-sep17; every M3 commit's subject starts "Agent replay M3". Task 10, the verification, made no commit by design; its record is in the milestone commit's message. The departures from the M3 design are the dated amendments in that file ("Amendments while building M3") and are not repeated here.

### Rulings (each with what it costs if wrong)

1. Ruling: the same setup as M2 (in place on JMF-2340550-sep17; one Workflow per task; implementers and reviewers on opus; reviews pinned to "Agent replay M3" commits, because another session commits on this branch) -- cost if wrong: as in the build record for M2.
2. Ruling: every implementer is told that its commit subjects must start "Agent replay M3", because the reviewers judge only such commits -- cost if wrong: none.
3. Ruling: build without a separate plan review by Jad, as for M2 -- cost if wrong: Jad wanted to see the plan first; nothing is irreversible.
4. Ruling: (plan critic's gap 1, shutdown) Task 10 must TRY both of the design's shutdown checks, not only a hard kill: start the server in its own console (Start-Process) and close it (CloseMainWindow), and send it Ctrl+C or Ctrl+Break where the platform allows; if either cannot be emulated, report exactly why and leave it for Jad with the command to run -- cost if wrong: one more verification step.
5. Ruling: (gap 2, FastAPI's own 422 and 405 without no-store) follow what the plan's Task 6 does, and the Task 6 reviewer checks it against the design's "every response carries no-store" -- cost if wrong: a 422 or 405 could be cached by the browser; harmless for a POST.
6. Ruling: (gap 3, the commit split 6a/6b not recorded) Task 11 records every departure from the design's seven commits, 4a/4b and 6a/6b included -- cost if wrong: none.
7. Ruling: fold two Task 5 minors into Task 6, which wires the status route to run beside asks: LayaBridge._alive reads self._proc once, so a status call racing a kill or close cannot raise AttributeError (a 500); and a worker found dead between presses is reaped by _kill, so its stdin closes and ready clears, not only forgotten -- cost if wrong: two small edits in Task 6's diff.
8. Ruling: accept NoStoreRoute also catching FastAPI's own 400 (a body that is not UTF-8, or nested too deep) to add no-store, because the design's rule is that every response of the four routes is no-store -- cost if wrong: none found.
9. Ruling: fold one Task 7 minor into Task 8: model-panel.failureOf passed any string kind to errorText; the page now keeps only the four names (ValueError, RuntimeError, OutOfMemoryError, other), with a test, so "never forward str(exc)" does not rest on the server alone -- cost if wrong: one small edit in Task 8's diff.

### Carried between tasks, and closed

- Task 2 to Task 3: a key with a character outside latin-1 (a pasted curly quote) would have failed when the Bearer header was encoded; such a key now reads as no_key, and nothing is sent.
- Task 2 to Task 6: to_action can raise OverflowError on an absurd JSON integer; both models map it to bad_answer, and a reply nested too deep for json.loads as well, never a 500.
- Task 3 to Task 6: JevError is raised "from None" but keeps the original exception as __context__, and ask's frame holds the key; the routes print and return only the code, never an exception object or a traceback.
- Task 3 to Task 11: the plan text still shows urllib.request.urlopen in _send; the M3 design's amendments record that _send posts through _OPENER, which refuses every redirect.
- Task 4 to Task 5: (a) a probe that a socket object's own connect, connect_ex and sendto are refused and counted in the worker; (b) a test that no app module imports laya_worker; (c) the worker docstring's blind spot names asyncio's proactor ConnectEx on Windows.
- Task 5 to Task 6: the two ruled laya_bridge edits (_alive reads _proc once; a worker found dead between presses is reaped by _kill).
- Task 5, by the controller: the Laya folder counted 32572 entries against 32571, a counting difference (with or without the folder itself); nothing under the folder was newer than 28 Sep 00:00, so no write happened.
- Task 7 to Task 8: failureOf keeps only the four kind names, any other string reads other, with a test.
- Task 8 to Task 10: the loop's play-state renderModels hook, which node cannot run, was checked in the browser: at 16x an episode played to its natural end enabled both buttons at the last second with no seek; the two model columns measured 291 px each at 1100 px and 374 px each at 1440 px, side by side, and one 320 px column at 390 px.
- Task 9 to Task 10: the English boot text of #pause-heading is the English empty line; before Compute it wraps on its own over two lines at 390 px, since #grade-now is still empty; while an uncached episode loads it shows for under 3 s.
- Task 10 to Task 11: the Ctrl+C and window-close rows are not cited as proof of LayaBridge.close() or atexit; the card's memory rose by about 2.0 GB with the server and Laya loaded (not the spike's 1.7 for Laya alone; an upper bound on Laya's share, since that server's agents ran on the same card); the Starlette and anyio deprecation warnings are named once as environmental (M3 design, "Amendments while building M3").

### Left for later (M3's own, as the controller deferred them; 3 marked open for the final review)

- Task 1: minor (deferred): *typesafe_key* has no directory anchor, so a future file named, for example, test_typesafe_key.py would be ignored (.gitignore:27).
- Task 1: minor (deferred): the commit message labels the run "python" though $PY ran it, and pastes only the last line (app/ unchanged).
- Task 2: minor (deferred): build_state accepts step -1 through numpy wraparound; the route's ge=0 guards it (model_questions.py:173).
- Task 2: minor (deferred): decode raises TypeError, not ValueError, for non-numeric input (model_questions.py:134).
- Task 2: minor (deferred): three tautological assertions in test_questions_and_options; no test ties the key and description texts to the LEVELS numbers (checked by hand, correct).
- Task 2: minor (deferred): test_no_recorded_drive_imports checks direct imports only (agent_api imports app.replay transitively).
- Task 2: minor (deferred): _NEUTRAL copies page_constants' neutral_phys one-liner (plan-mandated; guarded by a test).
- Task 2: minor (deferred): a test asserts cwd == ROOT (plan-mandated).
- Task 2: minor (deferred): user_setting's printable rule rejects a no-break space in a file's value while environment values are not checked the same way; a cp1252 file with non-ASCII text reads as no file.
- Task 3: minor (deferred): the HTTPError of a non-2xx reply or a refused redirect is not closed (ResourceWarning) (jev.py:100-109).
- Task 3: minor (deferred): the 400-digit payload test is built by string replace, which is fragile (test_agents.py:462-463); the leak-check expression is written out three times.
- Task 3: minor (deferred): NET_ALLOWED gives jev.py every NET_ROOTS entry, where it needs only urllib and http (test_agents.py:229; plan-mandated).
- Task 3: minor (deferred): a non-latin-1 key makes the status route say configured: false although TYPESAFE_API_KEY is set; _header_safe also rejects a tab.
- Task 3: minor (deferred): _OPENER is built at import time and takes the proxy settings of that moment.
- Task 4: minor (deferred): the protocol stream is protected at the Python level only (the sys.stdout rebind), not at fd 1 (laya_worker.py:56-57).
- Task 4: minor (deferred): the guard-probe subprocess runs without -B (test_agents.py:2485).
- Task 4: minor (deferred): a third AST import walker; WORKER_GUARDED copies GUARDED (plan-mandated pin).
- Task 4: minor (deferred): no default-suite test of the real worker's bad-request line, of it staying alive after one, or of its exit 0 at EOF (left to the bridge and test 20).
- Task 5: minor (deferred): the killed-server test's first readline() has no timeout (test_agents.py:2832).
- Task 5: minor (deferred): cwd and HF_HOME are derived from the resolved model folder, not from LAYA_HOME; they differ only under junctions (laya_bridge.py:180).
- Task 5: minor (deferred): status() reads user_setting twice per call (laya_bridge.py:143).
- Task 5: minor (deferred): the real spawn contract (argv, cwd, env, stderr) is pinned only under --full; load_home's "not absolute" and "python under the repository" branches are untested.
- Task 5: minor (deferred): test 20's snapshot records files only, not empty folders (test_agents.py:2662).
- Task 5: minor (deferred): worker_env drops HF_TOKEN* but not HUGGING_FACE_HUB_TOKEN, which HF_HUB_OFFLINE=1 makes moot (laya_bridge.py:91).
- Task 5: minor (deferred): an asyncio loop built inside the worker by a future laya or torch would count as a network attempt (the guard blocks loop creation), and would show as start_failed or network_attempt.
- Task 6: minor (deferred): the route comment names only the 422 and the 405, not the 400 (agent_api.py:252-253; the brief's wording kept).
- Task 6: minor (deferred): commit bc09b4f says 11 AskRouteTests; there are 14.
- Task 6: minor (deferred): _start's ready-line parse catches only ValueError; a RecursionError ready line would give a 500 and wedge the bridge (laya_bridge.py:210; the worker writes that line, low risk).
- Task 6: minor (deferred): Laya's device and usage pass through unvalidated; a NaN would make JSONResponse raise, a 500 in Laya's column only.
- Task 6: minor (deferred): three near-identical server_error blocks and a redundant local import in install() (plan-mandated).
- Task 6: minor (deferred): the refusal lines print uncaptured into the suite output, and the Starlette and anyio deprecation warnings now fire at the first TestClient import.
- Task 6: minor (deferred): NoStoreRoute bypasses any future app-level exception handler for these four routes.
- Task 7: minor (deferred): a FastAPI 422 reads "Server error (HTTP 422)" although it is a bad request from the page (design wording).
- Task 7: minor (deferred): the shared timeout sentence names no duration (jev 10 s, Laya 20 s).
- Task 7: minor (deferred): jev's status line shows the raw source token (env or file) untranslated in Arabic; Task 10 saw «مفتاح مُعَدّ (env)».
- Task 7: minor (deferred): rowView's defensive paths for a missing reversed entry are untested (the server cannot produce them).
- Task 7: minor (deferred): askState's reasons before the first frame and for an out-of-range k read slightly off (the brief's order).
- Task 7: minor (deferred): statusLine checks the Laya problem before the worker state, which hides a running worker if LAYA_HOME stops resolving.
- Task 8: minor (deferred; the final review should triage it): a failed press at a second erases a successful answer already held there, so a paid jev answer can be lost to a later network failure (the design says "a new press replaces").
- Task 8: minor (deferred): loadModelStatus has no sequence guard, so a slow status reply can overwrite a newer one (agents.mjs:1070-1080).
- Task 8: minor (deferred): WORKER_KINDS repeats laya_bridge.KINDS plus 'other', with no test tying them (model-panel.mjs:109).
- Task 9: minor (deferred): a test title says "phones keep that order" although the narrow order differs (plan-mandated).
- Task 10: minor (open for the final review): in the Arabic page a signed number inside a sentence is drawn with its sign on the right of the digits, in the choice line and the reversed line (agents.mjs:1164, :1177); M2's «أمر به» line does the same (agents.mjs:946).
- Task 10: minor (open for the final review): the choice line's network value uses a hyphen-minus while every level uses U+2212, two minus glyphs on one line (agents.mjs:1164).
- Task 10: minor (open for the final review): the latency line «{ms} ms على {device}» is drawn as "cuda على ms 65": right when read right to left, reversed to a Latin reader (agents-strings.mjs:173).
- Task 10: minor (deferred): the Task 10 report miscounts the console windows (three, not four).

*(Corrected 29 September, after the M3 final review: the Task 6 and Task 8 items above cited `agent_api.py:81-84` and `model-panel.mjs:998`; the route comment is at `:252-253` and `WORKER_KINDS` at `:109`, at those tasks' commits and now.)*

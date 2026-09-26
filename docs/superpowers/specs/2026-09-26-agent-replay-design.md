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

Beside the agents sits the experiment's preregistered verdict, quoted word for word from `results/`, together with a short verdict line that keeps its qualifiers. A hidden panel, unlocked by a gesture, sends that same paused moment to jev once and shows jev's choice next to the agents' actions. Every number on the page comes from a tracer that a test proves `==` to `evaluate.run_episode`.

**Non-goals.**

- **No writes and no training.** No training, no evaluation, and no writes into `runs*/`, `results/` or anywhere else. Traces live in memory only.
- **No statistics.** The page computes no statistic and no difference between the cars. The seed's table row is quoted, not computed.
- **jev does not drive an episode.** That is deferred, and nothing here blocks it.
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

All four sit at the top level of `app/`, so `app.test_replay`'s `test_read_only` scan covers them unchanged. None is hashed into `plant_sha` (`fingerprint.py:55` hashes plant, thermal and engine_env only).

| module | its one job | interface | depends on (import only) |
|---|---|---|---|
| `app/agent_trace.py` | Step N envs of one frozen episode in lockstep, mirroring `run_episode`; build the road from the cycle | `STEPS = 719`<br>`PREVIEW = slice(14, 14+len(PREVIEW_S))`<br>`GRADE_OBS_SCALE = 12.0`<br>`episode(protocol, idx) -> {seed, weights, road}`<br>`build_cycle(ep) -> dict`<br>`route(cycle) -> dict`<br>`run_lanes(lanes, ep, on_frame=None) -> list[dict]`<br>`jsonable(x)` | `evaluate`: `DT`, `DURATION`, `EPISODES`, `EPISODES_D2`<br>`engine_env`: `SupervisoryTunerEnv`, `make_grade_climb`, `PREVIEW_S`<br>`random_road.climb`<br>`app.replay.finite` |
| `app/agent_catalog.py` | Find agents; decide status, protocol, arm and budget; check each zip against the scored one; quote verdicts and table rows | `live_fingerprint(protocol)` (cached)<br>`read_agent(runs, name, root) -> dict`<br>`discover(root=ROOT) -> list[dict]`<br>`find_pair(runs, seed, root=ROOT)` (raises `KeyError`/`Refused`)<br>`scored_shas(prefix, seed, root) -> dict or None`<br>`verdict(prefix, root=ROOT) -> {state, lines, short, cells}`<br>`table_rows(prefix)`<br>`VERDICT_LINES`, `SHORT_VERDICT` | `fingerprint`: `read`, `compare`, `plant_fingerprint`, `model_budget`, `format_budget`, `running_pid`<br>`run_phase_d`: `result_prefix`, `CLOSED_PREFIX`<br>`analyse_phase_d2.load`<br>`analyse_c4.BUDGET` (the regex `analyse_c4` itself uses on the `model …: … zip sha` line, `analyse_c4.py:83`) |
| `app/agent_api.py` | Routes, the default model loader, and the single-worker episode store | `install(app) -> None`<br>`load_pair(runs, seed) -> (m_s, m_b)`<br>`class EpisodeStore(loader=load_pair, tracer=run_lanes, keep=2)` with `.poll(key, since, preempt) -> dict` and `.trace(key) -> Trace or None` | the two modules above; `evaluate.agent_policy`; `app.replay.BuildCancelled`; (M3) `app.jev` |
| `app/jev.py` (M3) | Build one jev request from a simulated trace step, send it, map the answers into the action space | `LEVELS`, `NET`, `OPTIONS`<br>`load_key()`<br>`decode(obs) -> dict`<br>`build_request(trace, step) -> dict`<br>`to_action(answers) -> dict`<br>`ask(trace, step, send=_send, clock=perf_counter) -> dict` | `engine_env`: `ACT_LO`, `ACT_HI`, `neutral_action`, `PREVIEW_S`, `TURB_PROTECT_K`, `OIL_PROTECT_K`<br>`urllib.request` |
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
| `sim/agents.css` | Grid and panel rules. It also overrides the lab's phone rule that hides the last nav link. |
| `sim/agent-view.test.mjs`, `sim/agents-strings.test.mjs`, `sim/tap-unlock.test.mjs` | Node tests, picked up by the existing glob |

**Reused by import, never copied:**

- `playback.mjs`: `PlaybackClock` and `formatTime`. **`sampleAt` is not reused.** It searches on `frames[i].t` and reads `s_m`/`speed_kmh` (`playback.mjs:21-23`), which agent frames do not carry. `episodeAt` does the lookup.
- `i18n.mjs`: `t`, `applyTranslations`, `resolveLang`, `STRINGS`, `missingKeys`.
- `scene.mjs`: `stage`, `supra`, `ribbonGeometry` (exported by edit 2 below; approved, §11 Q2).

### Edits to existing files: the complete list

1. **`app/server.py`.** In `main()`'s `if a.simulation:` branch (`:298`): `from app.agent_api import install; install(app)`, plus one printed `/agents` URL. Module-level routes do not change, so `--live` and `--replay` never import agent code. In M3, the docstring sentence at `:43` is amended (§7).
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

### 3.4 Routes (added by `install(app)`, only under `--simulation`)

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
POST /api/agents/jev    body {"trace": "runs_c4/5/1", "step": 312}      (M3, §7)
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

**Runnability.**

- A pair runs only when both arms are `ready` and the sha check passes.
- The episode route repeats steps 6 and the sha check before every build, and returns 409 without starting a worker.
- If SB3 is not importable, every pair shows "cannot run: stable-baselines3 not installed".

**Live fingerprint.**

- `live_fingerprint()` itself runs `os.environ.setdefault("GIT_OPTIONAL_LOCKS", "0")` before its first call. `plant_fingerprint` runs `git status` (`:250`) through `_git`, which inherits the environment (`:183`), and without the variable `git status` may rewrite `.git/index`. Putting it in `live_fingerprint` rather than `install()` covers the tests that call `discover()` directly.
- The fingerprint is taken once per protocol and cached. The method line says "fingerprint taken at hh:mm; restart the server after changing a hashed file".

**Experiment identity.** `prefix = run_phase_d.result_prefix(dir)` (`:94`). The name is `CLOSED_PREFIX.get(prefix)` (`:113`), or else "`runs_X` (no name recorded)".

**Verdicts are quoted, never computed.** `VERDICT_LINES[prefix]` is a list of `(file, regex, n_lines)`. Each match returns `{file, line, text}`, cited as `file:line`.

| prefix | quoted (checked today) |
|---|---|
| `c4` | `C4_RESULT.txt:42` RESULT: SMALLER THAN THE MEI<br>`:29` (7 of 8 seeds below 50)<br>`:33-34` THE TWO TESTS DISAGREE…<br>`:48` NOT-CONVERGED…<br>`:50-53` THE READING…<br>`PREREGISTRATION_C4.md:41-43`, what (i), (ii) and (iii) mean, directly under the reading<br>`PREREGISTRATION_C4.md:633-635`: "one seed the other way and the cell would be INCONCLUSIVE" |
| `d2` | `PHASE_D2_RESULT.txt:30-33` RESULT: INCONCLUSIVE and its paragraph<br>`:86-89` "Both are C1 agents … never 'preview does not help'" |
| `phase_d` | `PHASE_D_RESULT.txt:26-31` NOT SIGNIFICANT, with its C1 sentence<br>`PHASE_D2_RESULT.txt:65` INCONCLUSIVE [MEI set AFTER…], labelled post-hoc<br>`PHASE_D_RESULT.txt:33-40` AND THE BLINDED ARM IS NOT BLIND… |

**Verdict states.**

- **`found`**: all the lines above are present.
- **`missing`**: a file or an anchor is gone. The box says «لم يُعثر على سطر الحكم في results/<file>: لا تقرأ هؤلاء الوكلاء بدونه» ("verdict line not found in results/<file>: do not read these agents without it"), the short line is replaced by the same text, and test 8 fails.
- **`none`**: the prefix has no row, as for a future `runs_X`. The box says «لا يوجد حكم مسجَّل مسبقاً لهذه التجربة في results/. ما تعرضه هذه الصفحة ليس نتيجة.» ("No preregistered verdict for this experiment in results/. Nothing on this page is a result.")

**The short verdict line** (`SHORT_VERDICT[prefix]`) replaces the bare cell on every compact surface: the scene overlay, the experiment select and the phone summary. It is authored text, not a quote, so it is shown only when every anchor it summarises was `found`; test 8 pins that dependency.

| prefix | Arabic (English, same line on toggle) | requires anchors |
|---|---|---|
| `c4` | «أصغر من الحد الأدنى المهم (50 وحدة) عند 300 000 خطوة · بفارق بذرة واحدة · الاختباران مختلفان · لم يستقر التدريب» (smaller than the MEI (50) at 300 000 steps · one seed wide · the two tests disagree · not converged) | `:42`, `:29`, `:33`, `:48` |
| `d2` | «غير حاسم · وكلاء C1 ‏(50 000 خطوة)» (inconclusive · C1 agents, 50 000 steps) | `:30`, `:86` |
| `phase_d` | «غير دال إحصائياً · غير حاسم (قراءة لاحقة) · الذراع "العمياء" ليست عمياء · وكلاء C1» (not significant · inconclusive (post-hoc) · the "blind" arm is not blind · C1 agents) | `PHASE_D_RESULT:26`, `:33`, `PHASE_D2_RESULT:65` |

**Arabic glosses.** They sit under each quoted cell and keep their qualifiers:

| cell | gloss |
|---|---|
| SMALLER THAN THE MEI (c4) | «أثر الاستباق أقل من 50 وحدة ضرر، وهو حدّ اختاره الفريق مسبقاً، عند 300 000 خطوة تدريب، على طريق فيه تغيّر واحد في الميل لكل حلقة. التدريب لم يستقر، والنتيجة معلّقة على بذرة واحدة: لو انقلبت بذرة واحدة لصارت غير حاسمة.» ("Preview's effect is below 50 damage units, a threshold the team set in advance, at 300 000 training steps, on a road with one grade change per episode. Training had not settled, and the result hangs on one seed: if one seed flipped, it would be inconclusive.") |
| INCONCLUSIVE | «غير حاسم: التجربة لا تميّز بين "لا أثر" و"أثر يهمّ الفريق"» ("Inconclusive: the experiment cannot tell 'no effect' from 'an effect the team cares about'"), from `PHASE_D2_RESULT.txt:31-33` |
| NOT SIGNIFICANT | «غير دال إحصائياً، مع وكلاء بميزانية C1» ("Not statistically significant, with agents at the C1 budget") |
| NOT-CONVERGED | «لم يستقر التدريب» ("Training had not settled") |

**Table rows** come from `analyse_phase_d2.load(prefix)`. Missing seeds are named from its `incomplete` list.

**Catalog (M2).** `GET /api/agents/catalog` returns `{experiments: [{runs, name, prefix, protocol, verdict: {state, short, cells}, pairs: [{seed, runnable, reason, table_diff, scored, agents: [{tag, arm, status, budget_line, train_dt, problems}]}]}], episodes: {"d2": [{idx, seed, weights, climb_start_s, grade_pct}], "phase-d": [...]}, preview_s, act, limits, sb3}`.

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

**Preview.** One marker at each `PREVIEW_S` horizon, coloured by the grade read there, on a single-hue ramp from 0 to 16 %. There is no continuous band, because the agent saw four numbers, not a stretch of road.

**Overlay.** A thin strip inside the scene carries the **short verdict line** and «محاكاة» ("simulation"). A legend reads «السيارتان في المكان نفسه دائماً: السرعة يفرضها السيناريو، والوكيلان يختاران الحماية فقط» ("both cars are always at the same place: the scenario sets the speed, and the agents choose only the protection").

---

## 6. The page and the paused moment

**Picker.** Nothing is selected and nothing is computing when the page opens.

1. **Experiment:** the name plus the **short verdict line**.
2. **Pair:** «بذرة k · الأعمى − المُبصر {+x.x}» ("seed k · blind − sighted {+x.x}"), followed by a qualifier:
   - for D2 and C4: «(فرق وسيطَي 20 حلقة، لكلٍّ منها طريقها وأوزانها؛ ليست هذه الحلقة)» ("difference of the medians of 20 episodes, each with its own road and weights; not this episode");
   - for Phase D: «(فرق وسيطَي 20 حلقة على الطريق نفسه بأوزان مختلفة؛ ليست هذه الحلقة)» ("difference of the medians of 20 episodes on the same road with different weights; not this episode").

   Every pair is listed. Refused pairs are disabled with their reason. Each arm shows «دُرِّب {budget} خطوة (من final.zip)» ("trained {budget} steps (from final.zip)").
3. **Episode 1..20 (حلقة):** for example «حلقة 1 · الصعود عند 141 ث · 13.3٪ · الأوزان: عزم 0.69 / وقود 0.29 / عمر المكوّنات 0.03» ("episode 1 · climb at 141 s · 13.3 % · weights: torque 0.69 / fuel 0.29 / component life 0.03"). For Phase D: «الطريق نفسه (180 ث · 12٪)؛ تختلف الحلقات في الأوزان فقط» ("the same road (180 s · 12 %); the episodes differ only in their weights").

«احسب» sends one `preempt=1` request. Until it is pressed, the scene reads «اختر تجربة وزوجاً وحلقة ثم اضغط احسب» ("choose an experiment, a pair and an episode, then press احسب").

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
  - **Rows 3 and 4:** the tick at 1.0 reads «قيمة صف "حاسوب المحرك الأساسي" في النتائج (1.0 ثابتة)؛ الحاسوب المنمذَج نفسه يجدول المروحة 0 أو 0.4 أو 1.0 حسب حرارة سائل التبريد» ("the value used by the results' 'baseline ECU' row (a constant 1.0); the modelled computer itself schedules the fan at 0, 0.4 or 1.0 by coolant temperature"). Sources: `check_premise.py:25` `NEUTRAL = neutral_action()`, `evaluate.py:347`, `engine_env.py:265`.
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
| "C4 is a clean negative" | The short line (one seed wide · the tests disagree · not converged), the gloss, and `PREREGISTRATION_C4.md:633-635` quoted | select; overlay; box |
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
| "jev is part of the thesis" | Hidden by default; the §7 text; no comparison; never applied | jev panel |

**Layout.**

- **Desktop (≥ 1100 px, RTL):**
  - a grid of `minmax(0,1.6fr) minmax(320px,1fr)`;
  - main column: the chase view (16:9) with its overlay, the timeline, then the profile;
  - side column: picker, verdict box, pause panel, then jev once unlocked.
- **Phone (< 760 px):**
  - one column with a 16 px gutter and no horizontal scroll;
  - order: badge, picker, verdict, chase view (4:3), timeline, profile, pause panel;
  - the verdict shows the short line, the C4 one-seed line and the illustration line; the rest sits in `<details>`;
  - in the pause panel, labels sit on their own lines and values stack by car.
- The nav on `agents.html` reads simulation, agents (active), monitor, review, and `agents.css` restores the last link on phones.
- Arabic is the default, with the lab's language toggle. The page follows `prefers-color-scheme`.

---

## 7. jev (M3)

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
| jev | §7 |

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
| 8 | `verdicts` | each anchor of §4 is found and its `text` equals the file at `line`, including `C4_RESULT.txt:29`, `PREREGISTRATION_C4.md:41-43` and `:633-635`, and `PHASE_D2_RESULT.txt:86-89`; each `SHORT_VERDICT` is shown only when all its anchors are found, and a removed anchor turns it into the not-found text; the C4 gloss contains "50", "300 000" and the one-seed clause; `missing` names the file; unknown gives `none`; `table_rows == analyse_phase_d2.load` |
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
  - with `app\start-simulation.ps1` running, the profile draws at once;
  - the first «احسب» shows «تحميل الشبكتين…» for about 5 s, and later builds move within about a second;
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

**M3: the jev paused moment.**

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

# Agent Replay, Milestone 3 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Milestone M3 of the agent-replay page (/agents), exactly as the APPROVED design docs/superpowers/specs/2026-09-28-agent-replay-m3-design.md specifies (sections 7.0-7.11, 9 rows 10-20, 10 steps 1-7, and the consequential amendments), built on the M1+M2 code committed on JMF-2340550-sep17 up to d347ee5 (the code wins over any design line number). Two language models, jev (typesafe.ai, external, paid, key-gated) and Laya (local, free, in its own .venv, run as a persistent worker subprocess speaking JSON lines), sit behind ONE hidden gesture: ten taps within 4000 ms on the footer label #footer-index '02 — AGENTS'. The unlock lives in a module variable, so a reload forgets it. Once unlocked, a static #models-panel shows one column per model, with independent status, button, lock, answers and errors. A jev failure (no key, no credit, network) never blocks or hides Laya, and the reverse holds too. Each button asks about the PAUSED second only, and only when playback is stopped (the play button shows play, which includes the natural end of the episode) on a finished episode. The question is five 'choice' questions with five levels each. The state is the sighted agent's own observation obs[0][k] decoded into named units, plus a fixed task paragraph. Both models get it from ONE module (app/model_questions.py). Every Laya press asks twice, with the options in the design's order and then reversed, and shows per action whether the choice held or changed with the order (Laya's automatic order check, design 7.5b). jev is asked once. Nothing is applied, averaged, compared with the agents or saved. The pause panel moves under the play bar, and its empty state becomes one bilingual line (design 7.8, Jad's option 1). No test or prototype ever makes a real jev call. Laya's real worker runs only in the --full test and in the final verification, with LAYA_HOME taken from the process environment.

**Architecture:**

Four new top-level Python modules in app/ (so app.test_replay's test_read_only scan covers them unchanged; none is hashed into plant_sha), one edit to app/agent_api.py, one docstring sentence in app/server.py, and on the page two new pure ES modules plus wiring.

(1) py-trace. app/model_questions.py is the single source of the question and of the answer-to-action mapping.
- IDS, KEYS, LEVELS, NET and OPTIONS: LEVELS and NET are float32 5x5 arrays, and NET is computed vectorised exactly as neutral_action().
- QUESTIONS and QUESTIONS_REVERSED: the same five questions, with each question's five criteria in reverse order.
- TASK and NOTE.
- decode(obs): inverts engine_env._obs into named physical units.
- build_state(trace, step): accepts only an agent_api.Trace.
- to_action(answers): validates and keeps only choice, level_phys, level_net, the probabilities in design order, chosen_p, and the five options with their levels. confidence is dropped. It raises BadAnswer.
- user_setting(env_var, file_name, environ=None): reads the environment variable first, else the file APPDATA/grad-project/<file_name>. It refuses a FILE that resolves under the repository, and never treats a value as a path.

app/jev.py holds load_key, build_request, _send (one stdlib urllib POST, 10 s timeout, with the key only in the Authorization header) and ask(trace, step, send, clock). Every failure is a JevError(code, status), and a non-2xx status that the design does not name becomes vendor_status carrying only the integer. .gitignore gains .env, .env.* and *typesafe_key* first, in a commit of their own.

(2) py-serve. app/laya_worker.py runs ONLY under Laya's own python, as `python -I -B -X utf8 laya_worker.py <abs model_dir>` with cwd=LAYA_HOME. In order it:
- installs a socket guard over the eight entry points, replacing only those the platform has (Windows has no socket.socket.sendmsg, and adding one breaks `import torch`, as measured);
- rebinds sys.stdout to stderr;
- refuses a model folder that is not an absolute, existing directory;
- loads Laya once and warms it up;
- prints one ready line, then one reply line per request line, where a reply carries its id, ok, device, ms, model, answers, usage and the cumulative net_attempts;
- exits on stdin EOF.

app/laya_bridge.py holds load_home, worker_env and class LayaBridge(command=None, start_timeout=90, answer_timeout=20):
- building a bridge does no I/O, and status() never spawns;
- ask() spawns on the first press, sends QUESTIONS and then QUESTIONS_REVERSED, and reads the replies through a daemon reader thread and a queue.Queue with timeouts;
- it kills the worker on any timeout, id mismatch or network attempt, and the next press respawns it;
- close() closes stdin, waits 5 s, then kills, and is registered with atexit on the first start.

app/agent_api.py gains:
- module-level AskBody: pydantic, strict, extra forbid, trace matching the anchored TRACE_KEY built from agent_catalog.RUNS_NAME, SEED_TEXT and EP_TEXT, step 0..STEPS-1;
- LOCAL_HOST, MODEL_HTTP and same_origin(request);
- install(app, store=None, jev_send=None, laya=None), which adds four routes: GET /api/agents/jev/status, POST /api/agents/jev, GET /api/agents/laya/status and POST /api/agents/laya.

The four routes run their guards in this order: Origin, then trace (store.trace(key) is None, or step >= len(trace.obs[0])), then a per-model non-blocking lock in app.state.model_locks. Every body is sent with Cache-Control: no-store, and each failure also writes one line to stderr. server.py:43 and the docstrings in agent_api.py name the two POSTs. The routes exist only under --simulation, because install() is called only in that branch.

(3) fe-pure.
- app/static/sim/tap-unlock.mjs: createTapUnlock.
- app/static/sim/model-panel.mjs: MODELS, QUESTION_IDS, ERROR_CODES, askState(view, k), createAnswers(), rowView(answer, i), failureOf(httpStatus, body), errorText(code, status, lang, kind) and statusLine(name, status, failure, inFlight, lang). All of it is pure and node-tested.
- Every new string, in both languages, goes into agents-strings.mjs AGENT_STRINGS. No new string needs a backslash-u escape.

(4) fe-page.
- agents.html: a static <section id="models-panel" class="models-panel" hidden> with every id written out, first right after the pause panel. Task 9 then moves the pause panel and the models panel into .agents-col-main, right after the transport, and replaces the '—' empty state with agents.pause.empty.
- agents.css: the panel's own styles; below 1100 px the order is pause 5, profile 6, models 7; .models-panel has align-self:stretch; .footer-index has touch-action:manipulation.
- agents.mjs holds wiring only:
  - a `models` state object;
  - the gesture;
  - both status fetches, each on its own;
  - askModel(name), which POSTs {trace: state.metaKey, step: state.lastK} and drops the answer if state.loadToken moved while it was in flight;
  - renderModels(), called from renderPanel, the play and restart handlers, the loop's play-state branch, each answer's arrival and renderAll.
  - compute() and clearEpisode() empty both answer maps.

Data flow: ten taps -> GET both status routes -> the viewer pauses on a finished episode -> a press -> POST {trace, step} -> the server resolves the frozen in-memory Trace -> build_state(trace, step), the same for both models -> jev: one HTTPS call; Laya: two worker requests -> to_action -> JSON back -> the column stores it under (metaKey, k) and renders from rowView.

**Tech Stack:** Python 3.12.10, the system interpreter only: PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe. A .venv is blocked by App Control, and a bare `python` in the repository resolves to the repo .venv, which has no stable-baselines3 and no torch.
- Libraries measured 28 Sep: numpy 2.5.3, FastAPI 0.141.1, pydantic 2.13.5, starlette 1.6.0 (fastapi.testclient prints a Starlette/anyio DeprecationWarning; this is known and was left for later in M1 and M2).
- Laya: laya 0.3.20 in its OWN .venv (Python 3.12.14, PyTorch, cuda on an RTX 5070) at C:/Users/admin/Documents/Local AI/laya, found only through LAYA_HOME (user_setting). The model is LAYA_HOME/models/multilingual, which holds rl_agent_config.json. The server's python has no laya, transformers or safetensors.
- The repository modules are used by import only: engine_env (ACT_LO/ACT_HI at :513-514, PREVIEW_S at :517, OBS_DIM at :518, TURB_PROTECT_K/OIL_PROTECT_K at :490-491, _rescale at :544, _preview at :639, _obs at :646-671, neutral_action at :953), app.agent_trace, app.agent_catalog and app.agent_api.
- Standard library: urllib.request/urllib.error (jev.py only), subprocess, threading, queue, atexit, json, pathlib.
- Browser: ES modules under app/static/sim, reusing i18n.mjs (t(lang, key, vars) at :488, STRINGS at :35), agent-view.mjs (laneStoppedAt at :252, ACTIONS at :32) and agents-strings.mjs (AGENT_STRINGS at :24, mergeStrings at :264).
- Tests:
  - node:test on Node v24.18.0, run as `node --test "app/static/sim/*.test.mjs"` (glob quoted);
  - Python unittest, run as `$PY -m app.test_agents [--full]`;
  - the lab suites: `$PY -m app.test_replay [--full]` and `$PY -m app.test_simulation`;
  - `$PY verify_docs.py`.
- Browser check: Chrome driven over the DevTools protocol by a scratchpad script, as in M1/M2.
- Baselines measured 28 Sep on d347ee5, to be re-read from runs and never quoted as expected values:
  - node: 102 tests, 102 pass;
  - app.test_agents: 'Ran 59 tests', 'OK (skipped=1)', load_pair on cuda, torch 2.11.0+cu128, SB3 2.9.0;
  - app.test_replay: '49 of 49 checks pass';
  - verify_docs: 'All 67 checks pass (846 figure mentions scanned in the documents).'
- Runnable prototypes of every new unit are in $SCR, which is C:\Users\admin\AppData\Local\Temp\claude\c--Users-admin-Documents-graduation-project-GRAD-project\3ceacbd0-c593-4033-801a-fae5729f96d9\scratchpad\plan_proto_m3\skeleton\. All of them were run on 28 Sep:
  - model_questions.py, jev.py, laya_worker.py, laya_bridge.py and routes_proto.py (the four routes);
  - check_mq.py, check_body.py, check_routes.py (bridge and routes with a fake worker: every error mode) and drive_laya.py (the real Laya);
  - fe/tap-unlock.mjs, fe/model-panel.mjs, fe/strings-proto.mjs (the complete ar/en table of new keys) and fe/proto.test.mjs (5 of 5);
  - simcopy/sim/, a copy of app/static/sim with agents.mjs patched by patch_agents.py, where agents-page-models.test.mjs passes 3 of 3.

**Spec:** `docs/superpowers/specs/2026-09-28-agent-replay-m3-design.md` (APPROVED by Jad, 28 September 2026), with `docs/superpowers/specs/2026-09-28-laya-spike.md` and the main design `docs/superpowers/specs/2026-09-26-agent-replay-design.md` (its section 7 is what M3 replaces; its walkthrough log holds Jad's decisions). **M1 and M2 are built**; where a design line number and the code differ, the code wins.

**How this plan was written.** A plan workflow on 28 September 2026: one skeleton with every interface, read against the committed M1+M2 code; four authors (questions and jev, Laya worker/bridge and routes, pure panel logic, page and verification) who prototyped and ran their code in scratch copies (the Laya worker against the real Laya on this machine); one critic; revisions of the serving and page groups.

## Global Constraints

- READ-ONLY for the vehicle and the experiments. Never write to the ECU. No training, no evaluation, no writes into runs*/, results/, the user's APPDATA or the Laya folder. Never run setx. runs/, runs_d2/ and runs_c4/ are CLOSED. Traces live in memory only. A model's answer is never applied, never rate-limited, never averaged, never saved and never compared with the agents.
- Never edit plant.py, thermal.py, engine_env.py, random_road.py, fingerprint.py, train.py, evaluate.py, run_phase_d.py, analyse_phase_d2.py, analyse_c4.py, or anything in results/. Import only. No lab test file is edited (app/test_replay.py, app/test_simulation.py); M3 adds no exemption to test_read_only.
- Routes exist only through app.agent_api.install(app, store=None, jev_send=None, laya=None), which server.py calls only inside `if a.simulation:`. The four M3 routes are:
- GET /api/agents/jev/status -> {configured, source, vendor: "typesafe.ai", model: "jev-latest", hosted: "USA"}. The key itself is never included.
- POST /api/agents/jev, body {"trace": "runs_c4/5/1", "step": 312}.
- GET /api/agents/laya/status -> {configured, source, problem, worker: stopped|starting|ready|failed, device, laya}. It never spawns and never loads.
- POST /api/agents/laya, with the same body.
Every response of the four carries Cache-Control: no-store. The --simulation banner (server.py:299-301) is not changed.
- Body, for both POST routes: AskBody with model_config = ConfigDict(extra="forbid", strict=True); trace: str = Field(pattern=TRACE_KEY); step: int = Field(ge=0, le=agent_trace.STEPS - 1). TRACE_KEY = rf"^{agent_catalog.RUNS_NAME.pattern.strip('^$')}/(?:{SEED_TEXT.pattern})/(?:{EP_TEXT.pattern})$", which evaluates to ^runs[a-z0-9_]*/(?:[0-9]{1,3})/(?:[0-9]{1,2})$.
Measured, each of these gets 422: an extra field; a form body; text/plain; a step of "312", true, 1.0 or 719; the traces xx/runs_c4/5/1, runs_c4/5/1/zz, runs_c4/5/123, runs_C4/5/1, ../runs_c4/5/1, and a trace with a trailing newline.
These pass: runs_c4/5/1, runs_c4/05/1 (store key ('runs_c4', 5, 1)), and step 718. GET gives 405.
AskBody and fastapi.Request MUST be module-level names in agent_api.py: that module has `from __future__ import annotations`, so handler annotations are strings resolved against the module's globals.
- Guards, in order:
1. Origin must be present and equal 'http://' + Host, and Host must match ^(127\.0\.0\.1|localhost):\d{1,5}$. Otherwise 403 foreign_origin.
2. The body's trace is split on '/' into (runs, int(seed), int(ep)). store.trace(key) is None -> 409 no_trace; step >= len(trace.obs[0]) -> 409 step_not_computed.
3. A non-blocking lock PER MODEL, in app.state.model_locks = {'jev': Lock, 'laya': Lock}. If it is held -> 409 busy. The two locks never meet.
Both POST handlers are sync `def`. TestClient's default Host is 'testserver', so route tests use TestClient(app, base_url='http://127.0.0.1:8000') and the header Origin 'http://127.0.0.1:8000'.
- Error body: {"model": "jev"|"laya", "code": <code>}. It adds 'status' (an int) only for vendor_status and 'kind' only for worker_error. It is sent with no-store, plus one stderr line print(f"{model}: {code} (step {step})", file=sys.stderr) that carries no state and no key.
HTTP statuses:
- 503: no_key (jev), not_configured and not_found (Laya).
- 502: network, timeout, key_rejected (401), vendor_refused (403), request_rejected (422), rate_limited (429), overloaded (529), vendor_status (any other non-2xx; the integer only, the vendor's body dropped), start_failed, start_timeout, worker_error (kind only if in ValueError/RuntimeError/OutOfMemoryError, else 'other'), worker_died, network_attempt, bad_answer.
- 403: foreign_origin.
- 409: no_trace, step_not_computed, busy.
- 422: FastAPI's {detail} for a bad body.
- 500 server_error: anything unexpected.
Nothing is ever substituted, and neither str(exc) nor a vendor body is ever forwarded.
- jev: POST https://api.typesafe.ai/v1/systemone, model 'jev-latest', body {"model", "state": build_state(trace, step), "questions": QUESTIONS}. One call per press, no retries, a 10 s timeout, latency from time.perf_counter around the call. The key comes from user_setting('TYPESAFE_API_KEY', 'typesafe_key'), is read on each call, appears only in the 'Authorization: Bearer' header built inside _send, and is never logged, returned or placed in an error. The page's 'sent' is the exact body, which does not contain the key. NO test, prototype or verification step makes a real jev call: tests pass jev_send=fake. There is no key on this machine.
- Laya:
- Found through user_setting('LAYA_HOME', 'laya_home'). The python is LAYA_HOME/.venv/Scripts/python.exe (bin/python off Windows); the model is LAYA_HOME/models/multilingual, which must hold rl_agent_config.json. Neither may resolve under the repository, and this is the ONE place a setting's value is checked as a path.
- Spawn: subprocess.Popen([python, '-I', '-B', '-X', 'utf8', <app>/laya_worker.py, model_dir], cwd=LAYA_HOME, env=worker_env(home), stdin=PIPE, stdout=PIPE, stderr=None, text=True, encoding='utf-8').
- worker_env drops TYPESAFE_API_KEY and every HF_TOKEN*, adds USE_TF=0, HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1, HF_HUB_DISABLE_TELEMETRY=1 and TOKENIZERS_PARALLELISM=false, and sets HF_HOME=LAYA_HOME/.cache/huggingface.
- Timeouts: 90 s to start and 20 s per answer. The worker is killed on either timeout, on an id mismatch (bad_answer) and on net_attempts != 0 (network_attempt); the next press starts it again.
- It is started only by a press, never by the unlock or the status route. It stays resident until the server stops: close() closes stdin, waits 5 s, then kills, and atexit.register(bridge.close) is installed on the first start.
- Real-Laya tests take LAYA_HOME from the PROCESS environment only, set in the test command.
- Order check (design 7.5b): every Laya press sends two requests back to back, first QUESTIONS (the very object jev receives) and then QUESTIONS_REVERSED (the same ids, instructions and descriptions, with each question's five criteria reversed). Both answers pass to_action, and a BadAnswer in either is bad_answer. Per action the column shows the primary choice, the reversed choice, and «ثبت» ('held') or «تغيّر بتغيير الترتيب» ('changed with the order'). Nothing is counted or averaged across presses. jev is asked once, in the design's order only.
- Questions:
- Five questions in engine_env action order. IDS = spark_trim, lambda_trim, boost_ceiling, cooling_fan, coolant_pump.
- Every question has type 'choice', an instruction that refers to `task`, and five criteria. The ASCII keys (C12) are:
  - spark: 'retard 8 deg', 'retard 4 deg', 'no change', 'advance 2 deg', 'advance 4 deg';
  - lambda: 'richer by 0.15', 'richer by 0.075', 'no change', 'leaner by 0.03', 'leaner by 0.06';
  - boost: 'ceiling -40 kPa', 'ceiling -20 kPa', 'no change', 'ceiling +7.5 kPa', 'ceiling +15 kPa';
  - fan: 'fan 0 %', 'fan 25 %', 'fan 50 %', 'fan 75 %', 'fan 100 %';
  - pump: 'pump 30 %', 'pump 47.5 %', 'pump 65 %', 'pump 82.5 %', 'pump 100 %'.
- Descriptions read '{action} {signed level} {unit}'. The instruction texts are design section 7's table, verbatim.
- LEVELS: for the trims, [lo, (lo+n)/2, n, (n+hi)/2, hi]; for fan and pump, linspace(lo, hi, 5); n = agent_api's neutral_phys (0, 0, 0, 1.0, 1.0).
- NET = np.clip(2.0*(LEVELS-ACT_LO[:,None])/(ACT_HI-ACT_LO)[:,None]-1.0, -1, 1).astype(float32). Measured: bitwise equal to neutral_action() at all five neutral levels, and _rescale(NET) within 3.7e-9 of LEVELS.
- TASK is design section 7's paragraph, with the thresholds formatted from TURB_PROTECT_K and OIL_PROTECT_K ('850 °C', '135 °C').
- The state (design 7.3): {"engine": decode(trace.obs[0][step]), "task": TASK}, which is the sighted agent's actual observation and nothing more.
Not sent: the agents' actions, the experiment or verdict, and anything from logs/raw, app.replay, app.reader or app.estimator.
decode's field names are engine_speed_rpm, manifold_pressure_kPa, throttle_fraction, spark_advance_deg_BTDC, lambda, engine_block_C, oil_C, turbine_housing_C, charge_air_C, ambient_C, barometric_kPa, humidity_kg_per_kg, road_speed_kmh, grade_now_percent, grade_ahead_percent {in_2_s, in_5_s, in_15_s, in_30_s} (keys f'in_{h:g}_s' from PREVIEW_S), torque_requested_Nm, driver_aggression_0_to_1, priorities {deliver_torque, save_fuel, protect_components} (obs 20-22), and note 'simulated synthetic stress scenario, not a recorded drive'.
Measured on the real episode: 2729 Laya input tokens for the five rows (at most 5 x 800 = 4000). The first request took 97 ms, later ones 34.8 ms, and spawn to ready took 6.11 s with -I -B -X utf8.
- Page:
- The gesture is 10 taps within 4000 ms on #footer-index, a 'click' listener. Only #footer-index gets the handler; the lab's '01 — REPLAY' gets none. The state lives in a module variable, and tap-unlock.mjs uses no localStorage, sessionStorage, indexedDB or cookie. A reload forgets the unlock.
- #models-panel is static in agents.html with `hidden`. Unlocking removes hidden, then fetches the two status routes independently; a failed status fills only its own column.
- A button is enabled iff all of these hold: !state.play.clock.playing && !isWaiting() && state.done && frame k exists && the sighted lane did not stop at or before k (laneStoppedAt(frames, 0)) && that model has no request in flight.
- Answers are kept per (state.metaKey, k): one per second, in memory only, and a new press at the same second replaces the old one. An answer is dropped if state.loadToken moved while its request was in flight. compute() and clearEpisode() empty both maps. Nothing is asked on its own.
- The page never shows `confidence`. Model levels are never drawn on the agents' gauges. The error text is «لا جواب — {code}: ...» in that model's column only.
- Strings: every new string lives in agents-strings.mjs AGENT_STRINGS, in both languages, under the key namespace agents.models.* plus agents.pause.empty. The existing rules cover them: «حاسوب المحرك» never without «المنمذَج»; no 'preview helps', «يساعد الاستباق» or «الاستباق يساعد»; the same {placeholders} in both languages. No new key needs a backslash-u escape: the en dash in '70–500 ms' and '§' are literal characters, and a signed level is formatted by agents.mjs fmtAction.
The honesty lines are verbatim from design 7.7:
- «ليس جزءاً من الرسالة ولا من أي نتيجة. لا يقارن أي رقم هنا النموذجين بالوكيلين، ولا يُحسب أي فرق.»
- «الاحتمالات ادعاء النموذج نفسه، ولم تُختبر على هذه المهمة.»
- the discretisation line;
- «تجربة تشغيل، لا تقييم» with (README_AR.md:31), which was checked: Laya's line 31 says an example result does not mean it suits engine control;
- the order-check line «نسأل لايا مرتين، والخيارات بترتيبين متعاكسين. إذا تغيّر اختياره بتغيير الترتيب وحده، فذلك الاختيار لا يأتي من حالة المحرك.»
- Escape trap on this machine: the Write/Edit/Bash tool inputs decode a typed backslash-u-XXXX into the literal, often invisible, character. Any source line that must carry backslash-u-XXXX (U+202F, U+200F, U+2066, U+2068, U+2069, U+2212, U+2011) is written by a short $PY script that builds the escape as chr(92)+'uXXXX', then byte-checked: the count of chr(0xXXXX) in the file must be 0, and the count of chr(92)+'uXXXX' must equal the stated number. In new .mjs code use String.fromCodePoint(0x2212) rather than an escape. The plan keeps escapes as text (<U+XXXX>), never as characters.
- Environment for every command block:
- export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
- cwd = the repository root, never %TEMP%: a stray inspect.py there shadows the stdlib.
- Scratch files go in $SCRATCH (the session scratchpad), never in the repository.
- A real-Laya command sets LAYA_HOME='C:\Users\admin\Documents\Local AI\laya' in that command's own environment only.
- The browser-check server is started from the repository root as `$PY -m app.server --simulation --http-port <port>`, with LAYA_HOME in that process's environment.
- Tests:
- Python unittest in app/test_agents.py (`$PY -m app.test_agents`, and `--full` for the slow ones, including test 20).
- node:test in app/static/sim/*.test.mjs. A helper that is not *.test.mjs is not run by the glob, and each harness test file owns one boot of agents.mjs in its own process.
- test_read_only (test_replay.py:522-555) scans test_agents.py too: no '.write(' anywhere outside triple-double-quoted strings. The fake worker speaks through print(..., flush=True). Temp fixtures are made OUTSIDE the repository, with Path.write_text/mkdir in tempfile dirs.
- No test touches the network. jev is faked with install(..., jev_send=fake). Laya is faked with LayaBridge(command=[sys.executable, '-I', '-c', FAKE_WORKER, mode]), where FAKE_WORKER is a string constant inside test_agents.py (no file on disk, so the no-write snapshot of app/ stays valid).
- A sentinel key appears in no response body, no root-logger record at DEBUG, no captured stderr, and not in the fake worker's reported environment.
- Read every count from a run, never from this plan.
- TDD in every task: write the failing test, run it and see it fail for the stated reason, implement, run it green, commit. Steps are 2-5 minutes, and every code step carries complete code: no placeholders, no 'similar to task N', no 'add error handling'.
- Commits:
- Branch JMF-2340550-sep17 only, by EXPLICIT path: `git add <files>` then `git commit -F $SCRATCH/msg.txt -- <files>`, because another session may be committing in the same tree. Never stage broadly.
- After ANY change under app/, run `$PY -m app.test_replay` and paste its WHOLE output into the commit message (`--full` at the milestone).
- Before committing a new tracked file: `git add` it, run `$PY verify_docs.py`, and read its last line (a new docstring can trip a figure in verify_docs.RETIRED).
- Every message ends with the line 'Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'.
- The subject starts 'Agent replay M3'.
- Known limit, carried from M2: test 11's no-write snapshot raises when another session writes to the shared tree during the run. Re-run with HEAD unchanged before and after, and record it; never weaken the snapshot.

## Review Focus

- **Jad presses «اسأل لايا» on this Windows machine. If the worker's network guard ASSIGNS all eight entry points, it adds socket.socket.sendmsg, which Windows' socket class does not have. asyncio/selector_events.py:37 then takes its Unix branch, os.sysconf('SC_IOV_MAX'), so `import torch` inside the worker raises AttributeError. Measured 28 Sep: the ready line was {"ready": false, "error": "AttributeError"} after 0.71 s. Every press would show start_failed, and Laya would never answer.** Expected: laya_worker.py defines a GUARDED tuple of the eight (owner, name) pairs and replaces an entry point only `if hasattr(owner, name)`. Under Laya's own python with -I -B -X utf8 and cwd=LAYA_HOME, the worker prints {ready: true, device: 'cuda', laya: '0.3.20'} in about 6 s (measured 6.11 s). Test 19 runs the worker's own guard block in a `sys.executable -I` subprocess and checks three things: `import asyncio` succeeds, hasattr(socket.socket, 'sendmsg') is what it was before the guard, and socket.create_connection(('127.0.0.1', 9)) raises OSError and counts 1 attempt. Step 1 of the task (the measurement) and test 20 (--full) run the real worker. (pinned in T4)
- **Jad lets an episode play to its NATURAL END, or opens a finished episode he never played (second 0), and expects to ask about that second. userPaused stays false at the natural end (agent-view.mjs:185, playback.mjs:7), and the only code that sees the play state change is the rAF loop's branch at agents.mjs:1110. An enable test based on userPaused, or a render hook missing from that loop branch, leaves both buttons disabled at the last second with 'pause first'. The same happens when the page only re-renders on a k change.** Expected: askState(view, k) is enabled when playing and waiting are false, done is true, frame k exists, the sighted lane is not stopped at or before k, and nothing is in flight. agents.mjs calls renderModels() in renderPanel, in the play and restart click handlers, in the loop's play-state branch, on every answer's arrival and in renderAll. At the natural end both buttons are enabled at k = 718 with no seek. Pinned by model-panel.test.mjs, which has a natural-end row (playing false, waiting false, done true, k 718 -> enabled) and a never-played row (k 0), and by agents-page-models.test.mjs 'on a finished episode, play then pause at the same second enables both buttons, with no seek'. The browser check in T10 lets an episode play to its end at 16x. (pinned in T8)
- **jev fails because there is no key, the account has no credit (an undocumented non-2xx such as 402), or the network is down. Several designs would let that failure block, hide or blank Laya's column: one shared lock, one shared error slot, Promise.all over both status requests, a 402 turned into a 500, or a vendor body echoed into the page.** Expected: Server:
- a separate non-blocking lock per model in app.state.model_locks: with jev's lock held, Laya answers 200 and jev answers 409 busy, and the reverse;
- a fake send raising URLError gives jev 502 network, and Laya's next answer is 200;
- a fake 402 gives {model: 'jev', code: 'vendor_status', status: 402} with the fake's body text in no response and no log line, and Laya's next answer is 200;
- no_key is 503 and leaves the bridge's spawns at 0 and the fake send uncalled.
Page: each column has its own status fetch, its own in-flight flag and its own error node. Pinned by AskRouteTests.test_locks_are_per_model and test_jev_failures_never_touch_laya (T6), JevTests.test_other_statuses_are_vendor_status_with_only_the_integer (T3), and agents-page-models.test.mjs 'a jev failure stays in jev's column and Laya still answers, with its order check' (T8). (pinned in T6)
- **Laya's first press takes 6-33 s (spawn to ready; 12.2 s on a cold disk) and a jev call can take up to 10 s. Meanwhile Jad presses «احسب» again or changes a select. The late answer could then be stored under the new episode, or shown at whatever second is on screen now; a PAID jev answer would be shown against a second it was not asked about. The in-flight flag could also stay set and leave the button disabled for good.** Expected: askModel captures key = state.metaKey, k = state.lastK and token = state.loadToken at press time. It always resets inFlight when the fetch settles, and stores the entry in that model's createAnswers() map ONLY if state.loadToken === token. compute() and clearEpisode() call answers.clear() on both models. Pausing back at an asked second shows its stored answer with no new request, and a press there replaces it. Pinned by an agents-page-models.test.mjs case: press Laya, click «احسب», reply to the old Laya request, and no .model-row is rendered while the button is enabled again; and by model-panel.test.mjs createAnswers cases (k1 survives k2, get is per (key, k), a second put replaces, clear empties). (pinned in T8)
- **The server stops after a Laya press: Ctrl+C, the console window closed, a crash, or Stop-Process. The worker could keep about 1.7 GB of GPU memory and a python.exe under LAYA_HOME\.venv alive, and the next server start would spawn a second one. The same leak follows if a worker killed for a timeout, an id mismatch or a network attempt is never reaped, or its reader thread is left waiting.** Expected: LayaBridge.close() closes stdin, waits CLOSE_WAIT_S = 5 s, then kills and waits. atexit.register(self.close) is installed once, on the first start. Every kill path calls proc.kill() then proc.wait() and clears _proc and _queue, and the next ask respawns. The worker exits 0 on stdin EOF (measured 0.53 s). Pinned by BridgeTests.test_close_ends_the_worker (returncode set within 5 s), test_start_timeout_kills_and_the_next_ask_respawns and test_answer_timeout_kills_and_the_next_ask_respawns (the Popen wrapper's process has a returncode; spawns goes 1 -> 2), and LayaRealTests (process gone after close). T10 hard-kills a live server after a press and checks with Get-Process that no python.exe whose Path is under LAYA_HOME\.venv survives. (pinned in T5)

## Gaps against the design found by the plan's critic

Ruled on in the build ledger before Task 1.

- Design section 10 Verify requires the shutdown check (no Laya python.exe left) both after Ctrl+C and after closing the server's window. The plan measures only a hard kill (Stop-Process -Force) and hands the other two to Jad without trying either. Both could be emulated: start the server with Start-Process in its own console and close it with CloseMainWindow() (CTRL_CLOSE_EVENT); for Ctrl+C, a GenerateConsoleCtrlEvent helper attached to that console.
- The skeleton's global constraints say every response of the four M3 routes carries Cache-Control: no-store. FastAPI's own 422 (a malformed body, which is validated before the handler runs) and its 405 responses carry no no-store header. The plan records this in a note but adds no handler and no amendment.
- Design section 10 splits the work into seven commits. The plan ships 4a/4b and 6a/6b, and adds test 13's allowances to commits 3 and 4a. Only the 4a/4b split and test 13's timing are recorded as amendments; the 6a/6b split is not (see the Task 11 fix).

---

### Task 1: Agent replay M3 commit 1: the key-file patterns in .gitignore, alone, before any key exists

**Files:**
- Modify: `.gitignore` (append after its last line, line 18; the working-tree file is LF even though `core.autocrlf=true`, so append with a bash heredoc)
- Test: this commit has no unit test (design §10 step 1: the patterns alone). It is checked with `git check-ignore` below, and pinned for good by Task 3's `JevKeyTests.test_key_files_are_ignored`.

**Interfaces:**
- Consumes:
  - `.gitignore` as of d347ee5: 18 lines, `i/lf w/lf`, with no secrets pattern.
  - Today `git check-ignore -v .env .env.local typesafe_key app/typesafe_key.txt` prints nothing and exits 1 (measured 28 Sep).
- Produces:
  - `.gitignore` lines 19-27: a blank line, a five-line comment naming design M3 §7.3 and §10 step 1, then `.env` (line 25), `.env.*` (26) and `*typesafe_key*` (27).
  - No tracked file becomes ignored: `git ls-files -ci --exclude-standard` prints nothing.

No line in this task carries a backslash-u escape.

- [ ] **Step 1: Write the failing check**

These are the four paths the patterns must catch, plus `app/jev.py`, which they must not catch:

```bash
git check-ignore -v .env .env.local typesafe_key app/typesafe_key.txt; echo "exit=$?"
git check-ignore -q app/jev.py; echo "jev exit=$?"
```

- [ ] **Step 2: Run it to verify it fails**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory, never the repository}"
git rev-parse --abbrev-ref HEAD            # must print JMF-2340550-sep17
git check-ignore -v .env .env.local typesafe_key app/typesafe_key.txt; echo "exit=$?"
git check-ignore -q app/jev.py; echo "jev exit=$?"
```

Expected: FAIL. The first command prints no pattern lines, then `exit=1`. The second prints `jev exit=1`.

- [ ] **Step 3: Implement**

```bash
export GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
cat >> .gitignore <<'EOF'

# Agent replay M3 (docs/superpowers/specs/2026-09-28-agent-replay-m3-design.md,
# section 7.3 and section 10 step 1). A jev key lives only in the
# TYPESAFE_API_KEY variable or in <APPDATA>/grad-project/typesafe_key, outside
# the repository. These patterns are a second line of defence, added before
# any key exists, so a copy made by mistake is never committed.
.env
.env.*
*typesafe_key*
EOF
git diff --stat
```

Expected: ` .gitignore | 9 +++++++++` and `1 file changed, 9 insertions(+)`.

- [ ] **Step 4: Run to verify it passes**

```bash
export GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
git check-ignore -v .env .env.local typesafe_key app/typesafe_key.txt; echo "exit=$?"
git check-ignore -q app/jev.py; echo "jev exit=$?"
git check-ignore -q app/model_questions.py; echo "model_questions exit=$?"
git ls-files -ci --exclude-standard        # must print nothing: no tracked file is newly ignored
```

Expected (a TAB separates the pattern from the path; measured on a clone of d347ee5):

```
.gitignore:25:.env	.env
.gitignore:26:.env.*	.env.local
.gitignore:27:*typesafe_key*	typesafe_key
.gitignore:27:*typesafe_key*	app/typesafe_key.txt
exit=0
jev exit=1
model_questions exit=1
```

- [ ] **Step 5: Commit**

Nothing under `app/` changed, so `app.test_replay` is not required. It is run anyway, so that every M3 commit carries its line. No new file is tracked, so `verify_docs.py` is not needed.

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory, never the repository}"
git rev-parse --abbrev-ref HEAD            # JMF-2340550-sep17
git status --short                         # yours: " M .gitignore"; leave any other line alone (another session)
$PY -m app.test_replay > "$SCRATCH/m3t1_replay.txt" 2>&1; tail -1 "$SCRATCH/m3t1_replay.txt"
cat > "$SCRATCH/m3t1_msg.txt" <<'EOF'
Agent replay M3 (1/7): key-file patterns in .gitignore before any key exists

Design M3 section 10 step 1 (and section 7.3; main design section 2 edit 5):
.env, .env.* and *typesafe_key* are ignored in a commit of their own, before
any jev key exists. The key itself lives only in TYPESAFE_API_KEY or in
<APPDATA>/grad-project/typesafe_key, outside the repository; these patterns
are the second line of defence.

$ git check-ignore -v .env .env.local typesafe_key app/typesafe_key.txt
EOF
git check-ignore -v .env .env.local typesafe_key app/typesafe_key.txt >> "$SCRATCH/m3t1_msg.txt"
printf '%s\n' '$ git check-ignore -q app/jev.py; echo $?' "$(git check-ignore -q app/jev.py; echo $?)" '' \
  '$ python -m app.test_replay   (last line; nothing under app/ changed)' >> "$SCRATCH/m3t1_msg.txt"
tail -1 "$SCRATCH/m3t1_replay.txt" >> "$SCRATCH/m3t1_msg.txt"
printf '\n%s\n' 'Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>' >> "$SCRATCH/m3t1_msg.txt"
git add .gitignore
git commit -F "$SCRATCH/m3t1_msg.txt" -- .gitignore
git log -1 --stat --format=%s | cat
```

Expected:
- `app.test_replay`'s last line is `49 of 49 checks pass` (about 75 s). Read it from the run.
- The commit shows `.gitignore | 9 +++++++++`.
- The subject is `Agent replay M3 (1/7): key-file patterns in .gitignore before any key exists`.

**Notes:**
- **Prototype:** this exact sequence ran on 28 Sep in `…\scratchpad\plan_proto_m3\py-trace\clone`, a `git clone --no-hardlinks` of d347ee5 with `core.autocrlf=false`, so its files are LF like the real tree. The output quoted above is from that run.
- `git commit -- .gitignore` commits only that path, even if another session has staged something.

---


---

### Task 2: app/model_questions.py: the one question both models are asked (QUESTIONS and QUESTIONS_REVERSED), LEVELS/NET/OPTIONS, decode, build_state, to_action, user_setting; tests 14 and 15 (its own half)

**Files:**
- Create: `app/model_questions.py`
- Modify: `app/test_agents.py`:
  - `:31-34`: the `from app import agent_trace as T` line and the `engine_env` import;
  - `:1640`: `NEW_MODULES`;
  - one new block inserted directly before `:1704` (`def _shape(x):`).
- Test: `app/test_agents.py`: `QuestionTests`, `StateTests`, `UserSettingTests`, and `NoWriteTests` (test 11, static half)

**Interfaces:**
- Consumes (line numbers read from the code at d347ee5; every one this task uses matches the design, so nothing departs):
  - `engine_env.py`:
    - `:490-491`: `TURB_PROTECT_K = 1123.0`, `OIL_PROTECT_K = 408.0`;
    - `:513-514`: `ACT_LO`, `ACT_HI` (float32[5]);
    - `:517`: `PREVIEW_S = (2.0, 5.0, 15.0, 30.0)`;
    - `:544`: `SupervisoryTunerEnv._rescale(a)`;
    - `:639`: `_preview()`;
    - `:646-671`: `_obs()`, whose index map `decode` inverts;
    - `:953`: `neutral_action()`, whose body is `:1002-1005`.
  - `app/agent_api.py`:
    - `:88-102`: `@dataclass Trace(key, frames, results, obs, device, versions)`, with `obs = [sighted float32 (n, 23), blind float32 (n, 23)]`;
    - `:262`: `neutral_phys = ACT_LO + (neutral_action() + 1.0) * 0.5 * (ACT_HI - ACT_LO)`, inside `page_constants()`.
  - `app/agent_trace.py`:
    - `:29`: `STEPS = 719`;
    - `:62`: `episode(protocol, idx)`;
    - `:78`: `build_cycle(ep)`;
    - `DT` (imported from `evaluate`, 1.0).
  - `app/test_agents.py`:
    - `:31-34`: the imports;
    - `:1640`: `NEW_MODULES`;
    - `:1641-1650`: `WRITE_PATTERNS`;
    - `:1704`: `def _shape(x):`.
- Produces: `app/model_questions.py`. The module-level names:
  - `REPO`, `BadAnswer(ValueError)`;
  - `IDS`, `KEYS`, `LEVELS` and `NET` (float32 5×5), `OPTIONS`, `DESCRIPTIONS`, `INSTRUCTIONS`, `QUESTIONS`, `QUESTIONS_REVERSED`, `TASK`, `NOTE`.

  The functions:
  - `decode(obs) -> dict`: `ValueError` if `obs` is not 23 values or any value is not finite.
  - `build_state(trace, step) -> {'engine', 'task'}`: `TypeError` unless `trace` is an `agent_api.Trace`.
  - `to_action(answers) -> {qid: {choice, level_phys, level_net, probabilities, chosen_p, options}}`: raises `BadAnswer`.
  - `user_setting(env_var, file_name, environ=None) -> (value, 'env' | 'file') | (None, None)`.

  Test-module helpers that Tasks 3, 5 and 6 reuse:
  - `_obs_trace(n=8)`: a real `API.Trace` for `('runs_c4', 5, 1)`, cached by `n`;
  - `_model_answer(pick=1)`, `_with(qid, **change)` and `_with_p(value, qid=..., key=...)`;
  - `MODEL_MODULES = ("model_questions.py",)`, `RECORDED_DRIVE`, `_imports(source)` and `_recorded_drive(source)`.

**Escape trap:** no line in this task carries a backslash-u escape. The only non-ASCII character is `°` (U+00B0), typed as a character: twice in `app/model_questions.py` (TASK) and twice in `app/test_agents.py` (StateTests). `test_agents.py:677` already holds ONE backslash-u escape text (`"300<backslash>u202f000"`). Every edit here must leave it as escape text, and the byte check in Step 4 counts it.

- [ ] **Step 1: Write the failing test**

Edit `app/test_agents.py` in three places, with the Edit tool.

(a) The imports, `:31-34`. Replace:

```python
from app import agent_trace as T
from check_premise import p_grade_now, p_neutral
from engine_env import (ACT_HI, ACT_LO, OBS_DIM, PREVIEW_S, SLEW, TURB_PROTECT_K,
                        SupervisoryTunerEnv, make_grade_climb, neutral_action)
```

with:

```python
from app import agent_trace as T
from app import model_questions as MQ
from check_premise import p_grade_now, p_neutral
from engine_env import (ACT_HI, ACT_LO, OBS_DIM, OIL_PROTECT_K, PREVIEW_S, SLEW,
                        TURB_PROTECT_K, SupervisoryTunerEnv, make_grade_climb,
                        neutral_action)
```

(b) Test 11, `:1640`. Replace:

```python
NEW_MODULES = ("agent_trace.py", "agent_catalog.py", "agent_api.py")
```

with:

```python
NEW_MODULES = ("agent_trace.py", "agent_catalog.py", "agent_api.py", "model_questions.py")
```

(c) Insert this block directly before the line `def _shape(x):` (d347ee5 `:1704`). The block ends with two blank lines, so `def _shape(x):` stays two blank lines below it:

```python
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


MODEL_MODULES = ("model_questions.py",)
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


```

- [ ] **Step 2: Run it to verify it fails**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
$PY -m app.test_agents QuestionTests StateTests UserSettingTests NoWriteTests 2>&1 | tail -3
```

Expected: FAIL at import, with `ImportError: cannot import name 'model_questions' from 'app' (unknown location)`. This is the message measured on the clone.

- [ ] **Step 3: Implement**

Create `app/model_questions.py` with the Write tool. The `°` in TASK is typed as the character U+00B0; no backslash-u escape appears anywhere.

```python
"""The one question both language models are asked, and the one way an answer
becomes an action (agent replay M3, design section 7.3).

jev (app/jev.py) and Laya (app/laya_bridge.py) both import this module, so
both are asked the same thing about the same second: build_state(trace, step)
and QUESTIONS, the same module-level object. Laya is also asked
QUESTIONS_REVERSED, the same five questions with each question's five options
listed in reverse order, so the page can show whether a choice moved with the
order alone (design 7.5b).

The state is the sighted agent's own observation, trace.obs[0][step], decoded
from engine_env._obs back into named physical units, plus one fixed task
paragraph. Nothing else is sent: not the agents' actions, not the experiment
or its verdict, and nothing from the recorded drives. Its spark and lambda are
the values applied in the previous second, with the sighted agent's trims
already in them.

What this module never does: write, open a connection, or parse a model's
text. An option key maps back to a level by dictionary lookup, and every key
is ASCII (design C12).
"""
from __future__ import annotations

import math
import os
from pathlib import Path

import numpy as np

from app.agent_api import Trace
from engine_env import (ACT_HI, ACT_LO, OIL_PROTECT_K, PREVIEW_S, TURB_PROTECT_K,
                        neutral_action)

REPO = Path(__file__).resolve().parent.parent


class BadAnswer(ValueError):
    """An answer that cannot become an action. It carries none of the answer's text."""


# The five actions, in engine_env's order (agent-view.mjs ACTIONS: spark,
# lambda, boost, fan, pump).
IDS = ("spark_trim", "lambda_trim", "boost_ceiling", "cooling_fan", "coolant_pump")

KEYS = {
    "spark_trim": ("retard 8 deg", "retard 4 deg", "no change", "advance 2 deg",
                   "advance 4 deg"),
    "lambda_trim": ("richer by 0.15", "richer by 0.075", "no change", "leaner by 0.03",
                    "leaner by 0.06"),
    "boost_ceiling": ("ceiling -40 kPa", "ceiling -20 kPa", "no change", "ceiling +7.5 kPa",
                      "ceiling +15 kPa"),
    "cooling_fan": ("fan 0 %", "fan 25 %", "fan 50 %", "fan 75 %", "fan 100 %"),
    "coolant_pump": ("pump 30 %", "pump 47.5 %", "pump 65 %", "pump 82.5 %", "pump 100 %"),
}

# Levels in physical units: for the three trims the two limits, the neutral
# and the two midpoints; for the fan and the pump five evenly spaced duties.
# The neutral is agent_api.page_constants()'s neutral_phys formula, which is
# engine_env._rescale(neutral_action()) written out.
_NEUTRAL = ACT_LO + (neutral_action() + 1.0) * 0.5 * (ACT_HI - ACT_LO)
LEVELS = np.array(
    [[ACT_LO[i], (ACT_LO[i] + _NEUTRAL[i]) / 2, _NEUTRAL[i], (_NEUTRAL[i] + ACT_HI[i]) / 2,
      ACT_HI[i]] for i in range(3)]
    + [np.linspace(ACT_LO[i], ACT_HI[i], 5) for i in (3, 4)],
    dtype=np.float32)
# The network's units, computed vectorised in float32 exactly as neutral_action()
# computes them, so the neutral levels are bitwise neutral_action().
NET = np.clip(2.0 * (LEVELS - ACT_LO[:, None]) / (ACT_HI - ACT_LO)[:, None] - 1.0,
              -1.0, 1.0).astype(np.float32)
OPTIONS = {qid: {key: j for j, key in enumerate(keys)} for qid, keys in KEYS.items()}

DESCRIPTIONS = {
    "spark_trim": ("spark trim -8 deg", "spark trim -4 deg", "spark trim 0 deg",
                   "spark trim +2 deg", "spark trim +4 deg"),
    "lambda_trim": ("lambda trim -0.15", "lambda trim -0.075", "lambda trim 0",
                    "lambda trim +0.03", "lambda trim +0.06"),
    "boost_ceiling": ("boost ceiling -40 kPa", "boost ceiling -20 kPa", "boost ceiling 0 kPa",
                      "boost ceiling +7.5 kPa", "boost ceiling +15 kPa"),
    "cooling_fan": ("cooling fan 0 %", "cooling fan 25 %", "cooling fan 50 %",
                    "cooling fan 75 %", "cooling fan 100 %"),
    "coolant_pump": ("coolant pump 30 %", "coolant pump 47.5 %", "coolant pump 65 %",
                     "coolant pump 82.5 %", "coolant pump 100 %"),
}
INSTRUCTIONS = {
    "spark_trim": "Following `task`, how should spark timing be trimmed for the next second?",
    "lambda_trim": ("Following `task`, how should the air-fuel ratio be trimmed? "
                    "Richer cools the exhaust and costs fuel."),
    "boost_ceiling": ("Following `task`, by how much should the ceiling of the "
                      "boost-pressure loop be offset? It matters only if manifold pressure "
                      "(`engine.manifold_pressure_kPa`) would otherwise reach the ceiling."),
    "cooling_fan": ("Following `task`, what cooling fan duty should run? "
                    "It cools the coolant loop, not the turbine directly."),
    "coolant_pump": "Following `task`, what coolant pump duty should run (minimum 30 %)?",
}
QUESTIONS = {qid: {"type": "choice", "instructions": INSTRUCTIONS[qid],
                   "criteria": dict(zip(KEYS[qid], DESCRIPTIONS[qid]))} for qid in IDS}
QUESTIONS_REVERSED = {qid: {"type": "choice", "instructions": q["instructions"],
                            "criteria": dict(reversed(list(q["criteria"].items())))}
                      for qid, q in QUESTIONS.items()}

TASK = ("Decide the supervisory settings for the next one second. Deliver the requested "
        f"torque. Keep the turbine housing below {TURB_PROTECT_K - 273.15:.0f} °C and the "
        f"oil below {OIL_PROTECT_K - 273.15:.0f} °C. Weigh the three by `engine.priorities`. "
        "Spark and lambda trims are added to the modelled engine computer's values. The "
        "boost setting offsets only the ceiling of the pressure loop and matters only if "
        "pressure would otherwise reach it. Fan and pump are absolute duties.")
NOTE = "simulated synthetic stress scenario, not a recorded drive"


def decode(obs):
    """engine_env._obs inverted: 23 observation values -> named physical units.

    Each field is computed in float64 from the float32 value and rounded to
    the digits it can carry. ValueError for any other shape, or for a value
    that is not finite: nothing is substituted.
    """
    o = np.asarray(obs, dtype=np.float32).astype(np.float64)
    if o.shape != (23,) or not np.all(np.isfinite(o)):
        raise ValueError("an observation is 23 finite values")

    def r(v, digits):
        return round(float(v), digits)

    return {
        "engine_speed_rpm": r((o[0] + 1.0) * 3000.0, 1),
        "manifold_pressure_kPa": r((o[1] + 1.0) * 120.0, 2),
        "throttle_fraction": r(o[2], 4),
        "spark_advance_deg_BTDC": r((o[3] + 1.0) * 20.0, 2),
        "lambda": r(o[4] / 8.0 + 1.0, 4),
        "engine_block_C": r(o[5] * 25.0 + 363.0 - 273.15, 2),
        "oil_C": r(o[6] * 30.0 + 373.0 - 273.15, 2),
        "turbine_housing_C": r(o[7] * 200.0 + 873.0 - 273.15, 1),
        "charge_air_C": r(o[8] * 25.0 + 303.0 - 273.15, 2),
        "ambient_C": r(o[9] * 15.0 + 293.0 - 273.15, 2),
        "barometric_kPa": r(o[10] * 8.0 + 101.3, 2),
        "humidity_kg_per_kg": r((o[11] + 0.5) / 40.0, 5),
        "road_speed_kmh": r((o[12] + 1.0) * 25.0 * 3.6, 2),
        "grade_now_percent": r(o[13] / 12.0 * 100.0, 3),
        "grade_ahead_percent": {f"in_{h:g}_s": r(o[14 + i] / 12.0 * 100.0, 3)
                                for i, h in enumerate(PREVIEW_S)},
        "torque_requested_Nm": r((o[18] + 1.0) * 200.0, 1),
        "driver_aggression_0_to_1": r(o[19], 4),
        "priorities": {"deliver_torque": r(o[20], 4), "save_fuel": r(o[21], 4),
                       "protect_components": r(o[22], 4)},
        "note": NOTE,
    }


def build_state(trace, step):
    """{'engine': the sighted agent's observation at `step`, decoded; 'task': TASK}.

    Only a store Trace is accepted, so browser state can never be sent.
    """
    if not isinstance(trace, Trace):
        raise TypeError("build_state takes an agent_api.Trace, never browser state")
    return {"engine": decode(trace.obs[0][step]), "task": TASK}


def _probability(v):
    if (isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
            or not 0.0 <= v <= 1.0):
        raise BadAnswer("a probability that is not a number in [0, 1]")
    return float(v)


def to_action(answers):
    """Per question id: the chosen option as a level, and its probabilities.

    {qid: {choice, level_phys, level_net, probabilities (in KEYS order),
    chosen_p, options: [{key, level_phys}] x5}}. The model's confidence,
    answer_confidence and action are dropped (design C9), and so are ids that
    were not asked. BadAnswer for a missing id, a choice outside its options,
    probabilities that do not name exactly its options, or a probability that
    is not a finite number in [0, 1].
    """
    if not isinstance(answers, dict):
        raise BadAnswer("answers is not an object")
    out = {}
    for i, qid in enumerate(IDS):
        a = answers.get(qid)
        if not isinstance(a, dict):
            raise BadAnswer(f"{qid}: no answer")
        choice = a.get("choice")
        if not isinstance(choice, str) or choice not in OPTIONS[qid]:
            raise BadAnswer(f"{qid}: the choice is not one of its options")
        probs = a.get("probabilities")
        if not isinstance(probs, dict) or set(probs) != set(KEYS[qid]):
            raise BadAnswer(f"{qid}: the probabilities do not name exactly its options")
        ordered = {key: _probability(probs[key]) for key in KEYS[qid]}
        j = OPTIONS[qid][choice]
        out[qid] = {"choice": choice,
                    "level_phys": float(LEVELS[i, j]),
                    "level_net": float(NET[i, j]),
                    "probabilities": ordered,
                    "chosen_p": ordered[choice],
                    "options": [{"key": key, "level_phys": float(LEVELS[i, m])}
                                for m, key in enumerate(KEYS[qid])]}
    return out


def user_setting(env_var, file_name, environ=None):
    """(value, 'env' | 'file'), or (None, None).

    The environment variable wins. Otherwise the file
    <APPDATA>/grad-project/<file_name> is read, and refused if it resolves
    inside the repository: a git-ignored file in the working tree still
    travels in a zip or a copy (CLAUDE.md mistakes 11 and 16). A VALUE is
    never treated as a path: the server runs from the repository root, so a
    key resolved as a path would always land inside it.
    """
    env = os.environ if environ is None else environ
    value = (env.get(env_var) or "").strip()
    if value:
        return value, "env"
    appdata = env.get("APPDATA")
    if not appdata:
        return None, None
    path = (Path(appdata) / "grad-project" / file_name).resolve()
    if path == REPO or REPO in path.parents:
        return None, None
    try:
        text = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return None, None
    return (text, "file") if text else (None, None)
```

- [ ] **Step 4: Run to verify it passes**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory, never the repository}"
$PY - <<'EOF'
from pathlib import Path
for name, deg in (("app/model_questions.py", 2), ("app/test_agents.py", 2)):
    b = Path(name).read_bytes(); s = b.decode("utf-8")
    print(name, "CR", b.count(b"\r"), "U+00B0", s.count(chr(0xB0)), "(want", deg, ")",
          "backslash-u texts", s.count(chr(92) + "u"), "literal U+202F", s.count(chr(0x202F)))
EOF
$PY -m app.test_agents QuestionTests StateTests UserSettingTests NoWriteTests 2>&1 | tail -3
$PY -m app.test_agents > "$SCRATCH/m3t2_agents.txt" 2>&1; grep -E "^Ran |^OK|^FAILED|== proof" "$SCRATCH/m3t2_agents.txt"
```

Expected:
- **Byte check:**
  - `app/model_questions.py CR 0 U+00B0 2 (want 2 ) backslash-u texts 0 literal U+202F 0`;
  - `app/test_agents.py CR 0 U+00B0 2 (want 2 ) backslash-u texts 1 literal U+202F 0`. The one escape text is the existing `:677`, left untouched.
- **The four classes:** `Ran 10 tests in` about 11 s, then `OK`. `test_decode_is_the_observation` steps a real env 200 times, about 9 s.
- **The whole default suite:** `Ran 67 tests` (M2's 59 plus 8), `OK (skipped=1)`, and the `== proof PROVEN: device cuda, ...` line. It takes about 3 min.

Read every count from the run. If `tearDownModule` raises "the suite changed files on disk" and the listed files are not yours, another session wrote to the shared tree (M2's known limit). Re-run with HEAD unchanged before and after, record it, and never weaken the snapshot.

- [ ] **Step 5: Commit**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory, never the repository}"
git rev-parse --abbrev-ref HEAD            # JMF-2340550-sep17
git status --short                         # yours: " M app/test_agents.py", "?? app/model_questions.py"
$PY -m app.test_replay > "$SCRATCH/m3t2_replay.txt" 2>&1; tail -1 "$SCRATCH/m3t2_replay.txt"
git add app/model_questions.py app/test_agents.py
$PY verify_docs.py > "$SCRATCH/m3t2_vd.txt" 2>&1; tail -1 "$SCRATCH/m3t2_vd.txt"
cat > "$SCRATCH/m3t2_msg.txt" <<'EOF'
Agent replay M3 (2/7): model_questions -- one question for both models

app/model_questions.py is the one source of what jev and Laya are asked about
a paused second (design M3 7.3, C4): five 'choice' questions in engine_env's
action order with ASCII option keys (C12), and the same five with each
question's options reversed, for Laya's order check (7.5b). LEVELS and NET are
float32 5x5 tables; NET is computed as neutral_action() computes it and equals
it bitwise at the neutral levels. decode() inverts engine_env._obs into named
units; build_state() takes only a store Trace and sends the SIGHTED agent's
observation (obs[0]) with the task paragraph. to_action() keeps choice, both
levels, the probabilities in key order, chosen_p and the five options, and
drops confidence (C9). user_setting() reads the environment first, then
<APPDATA>/grad-project/<name>, and refuses a file that resolves inside the
repository; a value is never treated as a path.

Plan additions, recorded as design amendments at the milestone: to_action's
`options`, user_setting's `environ` argument, and decode refusing a value that
is not finite.

Tests 14 and 15 (QuestionTests, StateTests, UserSettingTests); test 11's
NEW_MODULES gains model_questions.py. RED before the module:
ImportError: cannot import name 'model_questions' from 'app' (unknown location).

$ python -m app.test_agents   (summary)
EOF
grep -E "^Ran |^OK|== proof" "$SCRATCH/m3t2_agents.txt" >> "$SCRATCH/m3t2_msg.txt"
printf '\n%s\n' '$ python verify_docs.py   (last line)' >> "$SCRATCH/m3t2_msg.txt"
tail -1 "$SCRATCH/m3t2_vd.txt" >> "$SCRATCH/m3t2_msg.txt"
printf '\n%s\n' '$ python -m app.test_replay' >> "$SCRATCH/m3t2_msg.txt"
cat "$SCRATCH/m3t2_replay.txt" >> "$SCRATCH/m3t2_msg.txt"
printf '\n%s\n' 'Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>' >> "$SCRATCH/m3t2_msg.txt"
git commit -F "$SCRATCH/m3t2_msg.txt" -- app/model_questions.py app/test_agents.py
git log -1 --stat --format=%s | cat
```

Expected:
- `app.test_replay`'s last line is `49 of 49 checks pass`. `READ-ONLY: no write path to the vehicle exists in app/` passes: it scans `model_questions.py` and `test_agents.py` too, and neither contains `.write(`.
- `verify_docs.py`'s last line is `All 67 checks pass (846 figure mentions scanned in the documents).` (measured on the clone with this file staged). Read it from the run. If it names a line in these files, reword that line; never change the checker.
- The commit shows `2 files changed`.

**Notes:**
- **Prototype, 28 Sep.** Everything above ran in `…\scratchpad\plan_proto_m3\py-trace\clone` (a clone of d347ee5, LF files). The edits in Step 1, applied to `git show d347ee5:app/test_agents.py`, reproduce the tested file byte for byte (`plan_edits.py` there).
- **The clone's full default run** gave `Ran 67 tests`. In the clone, 13 tests skipped and `test_page_assets_ids` failed, both only because `runs_c4/` and the vendored Three.js are gitignored and absent there. The real tree has both.
- **Measured:**
  - `decode` against the env's own attributes at steps 0, 1, 50, 150 and 200 is off by at most 0.50 of its last printed digit (turbine housing);
  - `LEVELS` = spark (-8, -4, 0, 2, 4), lambda (-0.15, -0.075, 0, 0.03, 0.06), boost (-40, -20, 0, 7.5, 15), fan (0, .25, .5, .75, 1), pump (.3, .475, .65, .825, 1);
  - at step 200 on D2 episode 1 the state reads a turbine housing of 789.4 C and a grade of 13.314 % now and in all four horizons.
- **Every test can fail.** Each of these deliberate breaks, applied to the module one at a time, turned its test red:
  - NET computed in float64 then cast (spark, lambda, boost off by one ulp);
  - QUESTIONS_REVERSED not reversed;
  - no repository check in `user_setting`;
  - a value checked as a path;
  - `confidence` kept;
  - a bool accepted as a probability;
  - a duck-typed trace accepted;
  - oil decoded with the wrong scale;
  - the blind lane `obs[1]` sent: at second 3 the two lanes see the same road, so the test pins the lane with a zeroed `obs[1]`;
  - an `app.replay` import;
  - no finite check;
  - a `write_text` in the module.
- **Plan additions, for Task 11 to record as design amendments:**
  - `to_action`'s `options` field;
  - `user_setting`'s `environ` argument;
  - `decode` refusing a non-finite value, so "NaN" can never reach a paid call. Unreachable today: the page never asks at or after the sighted lane's stop.
- **`from app.agent_api import Trace` at module level is safe:** `agent_api.install()` imports `app.jev` (and so this module) only at call time (Task 6), after `agent_api` has finished loading. The AST test checks direct imports only. `agent_api` itself imports `app.replay` for `BuildCancelled`, but no recorded-drive data reaches the state.

---


---

### Task 3: app/jev.py on model_questions: build_request, a fake-injectable ask with every error code (vendor_status for undocumented statuses), the key never leaking; test 17 and test 13's jev allowance

**Files:**
- Create: `app/jev.py`
- Modify: `app/test_agents.py`, in these places:
  - the stdlib imports (d347ee5 `:10-26`);
  - the `from app import` lines (after Task 2);
  - `NEW_MODULES` (Task 2's line);
  - the whole test-13 block, from `NET_ROOTS = {` to the end of `class NoNetworkTests` (d347ee5 `:1681-1701`, 2 lines lower after Task 2);
  - `MODEL_MODULES` (Task 2's line);
  - one new block inserted directly before `def _shape(x):`.
- Test: `app/test_agents.py`: `JevTests`, `JevKeyTests`, `NoNetworkTests`, `NoWriteTests`, `StateTests`

**Interfaces:**
- Consumes:
  - From Task 1: `.gitignore:25-27` (`.env`, `.env.*`, `*typesafe_key*`).
  - From Task 2:
    - `app/model_questions.py`: `QUESTIONS`, `KEYS`, `REPO`, `build_state(trace, step)`, `to_action(answers)`, `user_setting(env_var, file_name, environ=None)`;
    - the test helpers `_obs_trace(n)`, `_model_answer(pick)` and `MODEL_MODULES`.
  - `app/test_agents.py` at d347ee5:
    - `:1681 NET_ROOTS`;
    - `:1682 NET_ALLOWED = set()`;
    - `:1688-1701 test_no_network_imports_in_app`, which skips allowed files.
- Produces:
  - `app/jev.py`:
    - `URL = 'https://api.typesafe.ai/v1/systemone'`;
    - `MODEL = 'jev-latest'`;
    - `TIMEOUT_S = 10.0`;
    - `STATUS_CODES = {401: 'key_rejected', 403: 'vendor_refused', 422: 'request_rejected', 429: 'rate_limited', 529: 'overloaded'}`;
    - `class JevError(Exception)` with `.code: str` and `.status: int | None`; `args == (code,)`.
  - The functions in `app/jev.py`:
    - `load_key() -> (key | None, 'env' | 'file' | None)`;
    - `build_request(trace, step) -> {'model', 'state', 'questions'}`, where `questions` IS `QUESTIONS`;
    - `_send(body, key, timeout=TIMEOUT_S) -> (status, payload)`, in which `HTTPError` becomes `(err.code, b'')`;
    - `ask(trace, step, send=_send, clock=time.perf_counter) -> {'model_name', 'ms', 'answers', 'sent'}`.
  - The `ask` error codes:
    - `no_key`, raised before anything is sent;
    - `timeout`, for `TimeoutError` or a `URLError` whose reason is one;
    - `network`, for any other `URLError`, any other `OSError` (for example a reset while the reply is being read) and `http.client.HTTPException`;
    - the `STATUS_CODES` names;
    - `('vendor_status', int)`, for any other non-2xx;
    - `bad_answer`, for bad JSON, a missing `answers`, or a `BadAnswer`.
  - Test-module names that Tasks 4-6 reuse:
    - `NET_ALLOWED = {"jev.py": NET_ROOTS}` and `_net_hits(name, source) -> ['name:line root', ...]`;
    - `SENTINEL_KEY = "sentinel-key-M3"`;
    - `_jev_key(key)`, a context manager: the environment with this key or none, and an empty temporary `APPDATA`;
    - `_FakeSend(status=200, payload=None, exc=None)` with `.calls = [(body, key), ...]`;
    - `_Records`, a root-logger capture;
    - `_JevCase`, whose `setUp` makes `urllib.request.urlopen` raise.

**Code wins over the design here.** Design §10 puts test 13's amendments in commit 5. But `jev.py` imports `urllib`, and today's `test_no_network_imports_in_app` (`NET_ALLOWED = set()`, `:1682`) would fail from commit 3 to commit 5. The allowance therefore ships with `jev.py`, in this commit.

**Escape trap:** no line in this task carries a backslash-u escape, and `jev.py` is pure ASCII. The one byte string that must be invalid UTF-8 is written `bytes([0xFF, 0xFE])`, with no backslash escape at all.

- [ ] **Step 1: Write the failing test**

Edit `app/test_agents.py` in six places, with the Edit tool.

(a) Replace:

```python
import ast
import importlib.util
import json
import os
```

with:

```python
import ast
import contextlib
import importlib.util
import io
import json
import logging
import os
```

(b) Replace:

```python
import time
import unittest
from unittest import mock
import warnings
```

with:

```python
import time
import traceback
import unittest
from unittest import mock
from urllib.error import URLError
import warnings
```

(c) Replace:

```python
from app import agent_trace as T
from app import model_questions as MQ
```

with:

```python
from app import agent_trace as T
from app import jev as JEV
from app import model_questions as MQ
```

(d) Replace:

```python
NEW_MODULES = ("agent_trace.py", "agent_catalog.py", "agent_api.py", "model_questions.py")
```

with:

```python
NEW_MODULES = ("agent_trace.py", "agent_catalog.py", "agent_api.py", "model_questions.py",
               "jev.py")
```

(e) Replace the whole test-13 block:

```python
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

with:

```python
NET_ROOTS = {"urllib", "http", "socket", "requests", "httpx", "typesafe_sdk"}
# M3 (design 7.4 and section 9 row 13): jev.py is the one module allowed network
# imports. The scan still reads every app/*.py, the allowed ones included.
NET_ALLOWED = {"jev.py": NET_ROOTS}


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
```

(f) Replace:

```python
MODEL_MODULES = ("model_questions.py",)
```

with:

```python
MODEL_MODULES = ("model_questions.py", "jev.py")
```

Then insert this block directly before the line `def _shape(x):`, which puts it after Task 2's `UserSettingTests`. It ends with two blank lines:

```python
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
    reached urlopen by mistake fails here, before any byte is sent."""

    def setUp(self):
        guard = mock.patch.object(JEV.urllib.request, "urlopen", side_effect=AssertionError(
            "a jev test reached urllib.request.urlopen: tests use a fake send only"))
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


```

- [ ] **Step 2: Run it to verify it fails**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
$PY -m app.test_agents JevTests JevKeyTests NoNetworkTests NoWriteTests StateTests 2>&1 | tail -3
```

Expected: FAIL at import, with `ImportError: cannot import name 'jev' from 'app' (unknown location)`.

- [ ] **Step 3: Implement**

Create `app/jev.py` with the Write tool. It is all ASCII.

```python
"""jev, the external language model (typesafe.ai), asked about one simulated
second (agent replay M3, design section 7.4).

One press is one paid call: a POST to URL with model MODEL, the state and the
five questions from app.model_questions, a TIMEOUT_S timeout and no retry.
The answer is shown, never applied, averaged, compared with the agents or
saved.

The key is read on every call, from TYPESAFE_API_KEY or from
<APPDATA>/grad-project/typesafe_key (model_questions.user_setting), and it
appears in one place only: the Authorization header that _send builds. It is
never logged, returned or put into an error. Every failure is a JevError with
a fixed code; vendor_status also keeps the integer HTTP status. Neither
str(exc) nor the vendor's body is ever kept.

Imported only by app.agent_api.install(), which only the --simulation branch
of app/server.py calls. Nothing here has a path to the vehicle.
"""
from __future__ import annotations

import http.client
import json
import time
import urllib.error
import urllib.request

from app.model_questions import QUESTIONS, build_state, to_action, user_setting

URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"
TIMEOUT_S = 10.0
# The statuses the vendor documents. Any other non-2xx reply is vendor_status
# (design C14): an account with no credit gets a status nobody has documented.
STATUS_CODES = {401: "key_rejected", 403: "vendor_refused", 422: "request_rejected",
                429: "rate_limited", 529: "overloaded"}


class JevError(Exception):
    """A fixed code; `status` is the integer HTTP status for vendor_status only."""

    def __init__(self, code, status=None):
        super().__init__(code)
        self.code = code
        self.status = status


def load_key():
    """(key, 'env' | 'file'), or (None, None). Read on each call, never kept."""
    return user_setting("TYPESAFE_API_KEY", "typesafe_key")


def build_request(trace, step):
    """The exact body sent, which the page shows as 'what was sent': no key in it."""
    return {"model": MODEL, "state": build_state(trace, step), "questions": QUESTIONS}


def _send(body, key, timeout=TIMEOUT_S):
    """One HTTPS POST -> (status, payload). An HTTP error keeps its status only."""
    request = urllib.request.Request(
        URL, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as err:
        return err.code, b""


def ask(trace, step, send=_send, clock=time.perf_counter):
    """Ask jev about one second: {'model_name', 'ms', 'answers', 'sent'}.

    `ms` is `clock` read around the call. JevError codes: no_key (before
    anything is sent), timeout, network, the STATUS_CODES names,
    vendor_status (with the status) and bad_answer.
    """
    key, _source = load_key()
    if not key:
        raise JevError("no_key")
    body = build_request(trace, step)
    start = clock()
    try:
        status, payload = send(body, key)
    except TimeoutError:
        raise JevError("timeout") from None
    except urllib.error.URLError as err:
        raise JevError("timeout" if isinstance(err.reason, TimeoutError) else "network") from None
    except (OSError, http.client.HTTPException):
        raise JevError("network") from None
    ms = (clock() - start) * 1000.0
    if status in STATUS_CODES:
        raise JevError(STATUS_CODES[status])
    if not 200 <= status < 300:
        raise JevError("vendor_status", int(status))
    try:
        data = json.loads(payload)
        answers = to_action(data.get("answers") if isinstance(data, dict) else None)
    except ValueError:                  # BadAnswer is a ValueError, and so is bad JSON
        raise JevError("bad_answer") from None
    name = data.get("model")
    return {"model_name": name if isinstance(name, str) and len(name) <= 64 else None,
            "ms": round(ms, 1), "answers": answers, "sent": body}
```

- [ ] **Step 4: Run to verify it passes**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory, never the repository}"
$PY - <<'EOF'
from pathlib import Path
b = Path("app/jev.py").read_bytes(); s = b.decode("utf-8")
print("jev.py CR", b.count(b"\r"), "non-ASCII", sum(ord(c) > 127 for c in s), "backslash-u texts", s.count(chr(92) + "u"))
t = Path("app/test_agents.py").read_text(encoding="utf-8")
print("test_agents.py backslash-u texts", t.count(chr(92) + "u"), "U+00B0", t.count(chr(0xB0)), "calls of JEV._send", t.count("JEV._send"))
EOF
$PY -m app.test_agents JevTests JevKeyTests NoNetworkTests NoWriteTests StateTests 2>&1 | tail -3
$PY -m app.test_agents > "$SCRATCH/m3t3_agents.txt" 2>&1; grep -E "^Ran |^OK|^FAILED|== proof" "$SCRATCH/m3t3_agents.txt"
```

Expected:
- **Byte check:**
  - `jev.py CR 0 non-ASCII 0 backslash-u texts 0`;
  - `test_agents.py backslash-u texts 1 U+00B0 2 calls of JEV._send 0`.
- **The five classes:** `Ran 17 tests in` about 11 s, then `OK`.
- **The whole default suite:** `Ran 78 tests` (Task 2's 67 plus 11), `OK (skipped=1)`, and the `== proof PROVEN: device cuda, ...` line.

Read the counts from the run.

- [ ] **Step 5: Commit**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory, never the repository}"
git rev-parse --abbrev-ref HEAD            # JMF-2340550-sep17
git status --short                         # yours: " M app/test_agents.py", "?? app/jev.py"
$PY -m app.test_replay > "$SCRATCH/m3t3_replay.txt" 2>&1; tail -1 "$SCRATCH/m3t3_replay.txt"
git add app/jev.py app/test_agents.py
$PY verify_docs.py > "$SCRATCH/m3t3_vd.txt" 2>&1; tail -1 "$SCRATCH/m3t3_vd.txt"
cat > "$SCRATCH/m3t3_msg.txt" <<'EOF'
Agent replay M3 (3/7): jev.py with a fake send; key never leaves the Authorization header

app/jev.py asks jev about one paused second (design M3 7.4): one POST per
press to https://api.typesafe.ai/v1/systemone, model jev-latest, the body
{model, state, questions} built from model_questions (the same state and the
same QUESTIONS object Laya will get), a 10 s timeout and no retry. The key is
read on every call through user_setting and appears only in the Authorization
header _send builds. Every failure is a JevError with a fixed code: no_key
(before anything is sent), timeout, network, key_rejected / vendor_refused /
request_rejected / rate_limited / overloaded for 401/403/422/429/529, and
vendor_status carrying only the integer for any other non-2xx (C14: an account
with no credit gets an undocumented status); bad_answer for anything
to_action refuses. Neither str(exc) nor the vendor's body is kept.

Code wins over design section 10: test 13's allowance ships here, with
jev.py, because jev.py imports urllib and the old scan (NET_ALLOWED = set())
would fail until commit 5. NET_ALLOWED is now {"jev.py": NET_ROOTS}, the loop
no longer skips allowed files, and _net_hits() is the helper Task 4's probe
reuses. Plan additions: an OSError or http.client.HTTPException from send
(for example a reset while reading the reply) is `network`, not a server
error; and every jev test runs with urllib.request.urlopen patched to raise,
so a test that reached the real _send would fail before sending a byte.

Test 17 (JevTests, JevKeyTests), test 13 (NoNetworkTests plus a probe), test
15's AST scan and test 11's NEW_MODULES gain jev.py. No test calls _send;
every ask() gets a fake send. RED before the module:
ImportError: cannot import name 'jev' from 'app' (unknown location).

$ python -m app.test_agents   (summary)
EOF
grep -E "^Ran |^OK|== proof" "$SCRATCH/m3t3_agents.txt" >> "$SCRATCH/m3t3_msg.txt"
printf '\n%s\n' '$ python verify_docs.py   (last line)' >> "$SCRATCH/m3t3_msg.txt"
tail -1 "$SCRATCH/m3t3_vd.txt" >> "$SCRATCH/m3t3_msg.txt"
printf '\n%s\n' '$ python -m app.test_replay' >> "$SCRATCH/m3t3_msg.txt"
cat "$SCRATCH/m3t3_replay.txt" >> "$SCRATCH/m3t3_msg.txt"
printf '\n%s\n' 'Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>' >> "$SCRATCH/m3t3_msg.txt"
git commit -F "$SCRATCH/m3t3_msg.txt" -- app/jev.py app/test_agents.py
git log -1 --stat --format=%s | cat
```

Expected:
- `app.test_replay`'s last line is `49 of 49 checks pass`, and `READ-ONLY: no write path to the vehicle exists in app/` passes: `jev.py` has no `.write(`.
- `verify_docs.py`'s last line is `All 67 checks pass (846 figure mentions scanned in the documents).` (measured on the clone with this file staged). Read it from the run.
- The commit shows `2 files changed`.

**Notes:**
- **Prototype, 28 Sep,** in `…\scratchpad\plan_proto_m3\py-trace\clone`:
  - Steps 1-5 ran there; this exact message-building sequence produced a commit.
  - Step 1's six edits plus the block, applied to Task 2's output, reproduce the tested file byte for byte.
  - The clone's full default run gave `Ran 78 tests`, with the same two gitignored-file effects as Task 2.
- **Every test can fail.** Each of these deliberate breaks, applied one at a time, turned its test red:
  - the vendor body kept as `status`;
  - a retry on 5xx;
  - the key checked after sending;
  - the key put in the body;
  - `str(err)` kept;
  - the exception context shown (`from None` removed);
  - a wrapped timeout reported as `network`;
  - the named statuses dropped;
  - a connection reset not mapped to `network`;
  - a 65-character model name kept;
  - `NET_ALLOWED` reset to `{}`, which fails with `['jev.py:21 http', 'jev.py:24 urllib', 'jev.py:25 urllib']`.

  A probe that routed a fake send into the real `_send` was stopped by `_JevCase`'s patched `urlopen` with `AssertionError: a jev test reached urllib.request.urlopen: tests use a fake send only`. No socket was opened.
- **No real jev call is made anywhere in this task, and there is no key on this machine.** `_jev_key` points `APPDATA` at an empty temporary folder, so a key file on the machine could never be read by a test.
- **Plan additions, for Task 11 to record:**
  - `network` also covers `OSError` and `http.client.HTTPException` raised by `send`;
  - the `_JevCase` guard;
  - test 13's amendment in commit 3 instead of 5.
- `test_key_files_are_ignored` needs Task 1's commit. The test runs `git check-ignore` with `GIT_OPTIONAL_LOCKS=0`, so it writes no index file and the no-write snapshot of test 11 stays valid.


---

### Task 4: app/laya_worker.py: first the -I -B -X utf8 spawn measurement, then the worker (socket guard of existing entry points, stdout kept for protocol, absolute-path refusal, one JSON line per request); test 19's worker half and test 13's worker allowance

The code wins over the design in three places:
- **Design 7.5 step 1** says eight entry points are replaced. On Windows, `socket.socket` has no `sendmsg`, so the guard replaces only the seven that exist. Assigning `sendmsg` makes `import torch` fail with `AttributeError: module 'os' has no attribute 'sysconf'` (measured).
- **Design 10 step 4** is one commit. This plan splits it into 4a (this task, the worker) and 4b (Task 5, the bridge).
- **Test 13's allowance** for the worker lands in this commit, not in commit 5.

The M3 test blocks go directly above `def _shape(x):`, after the block Task 3 put there. Task 3 set that convention, and it keeps every M3 test together.

**Files:**
- Create: `app/laya_worker.py`. Write and measure it first as `$SCRATCH/m3_worker/laya_worker.py`, then copy it unchanged.
- Create (scratch only, never in the repository): `$SCRATCH/m3_worker/measure_worker.py`
- Modify: `app/test_agents.py`:
  - the assignments `NEW_MODULES` and `MODEL_MODULES`, as Task 3 left them;
  - the `NET_ALLOWED` assignment together with the two comment lines above it;
  - one new method in `class NoNetworkTests`;
  - a new block directly above `def _shape(x):`.
- Test: `app/test_agents.py`

**Interfaces:**
- Consumes:
  - From Task 2: `app/model_questions.py` `QUESTIONS`, `QUESTIONS_REVERSED`, `IDS`, `build_state(trace, step)` and `to_action(answers)`. Only the scratch measurement uses them.
  - From Task 2: `MODEL_MODULES = ("model_questions.py", "jev.py")` (Task 3 extended it) and `StateTests.test_no_recorded_drive_imports`.
  - From Task 3:
    - `NET_ROOTS`;
    - the two-line comment and `NET_ALLOWED = {"jev.py": NET_ROOTS}`;
    - `_net_hits(name, source) -> list[str]`, which returns `"<name>:<line> <root>"`;
    - `NoNetworkTests`, with its two tests;
    - `NEW_MODULES` (five names).
  - Laya as installed in its own .venv: `laya.load(model_dir, device) -> Agent`, `.device`, `.predict(state, questions) -> {"model", "answers", "usage"}`, and `importlib.metadata.version("laya")`.
- Produces:
  - `app/laya_worker.py`, run only as `python -I -B -X utf8 laya_worker.py <abs model_dir>`:
    - Module level, in this order: `import socket` as the first import, `_NET = {"attempts": 0}`, `_refuse(*args, **kwargs)`, `GUARDED` (the eight `(owner, name)` pairs), the guard loop (`for _where, _name in GUARDED: ... if hasattr(_owner, _name): setattr(...)`), then `json`, `os`, `sys` and `time`, then `WARM_UP`, then `main() -> int`.
    - The ready line is `{"ready": true, "device", "laya", "load_s"}`, or `{"ready": false, "error": <class name>}` on failure.
    - The reply to `{"id", "state", "questions"}` is `{"id", "ok": true, "device", "ms", "model", "answers", "usage", "net_attempts"}`, or `{"id", "ok": false, "error": <class name>, "net_attempts"}` on failure.
    - It exits 0 at stdin EOF.
  - `$SCRATCH/m3_worker/measure.txt`, the spawn measurement, which the commit quotes.
  - In test_agents.py:
    - the constant `WORKER_GUARDED`;
    - the helpers `_worker_tree()`, `_import_roots(tree)` and `_guard_loop(tree)`;
    - `class WorkerStaticTests` (3 tests);
    - `NoNetworkTests.test_the_scan_sees_urllib_in_the_worker`.

- [ ] **Step 1: Write the worker to scratch first (design 10 step 4: measure before anything is built on it)**

Write `$SCRATCH/m3_worker/laya_worker.py` with the Write tool. The file is pure ASCII, with no backslash anywhere, so the escape trap cannot touch it.

```python
"""Laya behind one JSON line per request. Runs ONLY under Laya's own python:

    <LAYA_HOME>/.venv/Scripts/python.exe -I -B -X utf8 laya_worker.py <absolute model_dir>

app/laya_bridge.py starts it with cwd=LAYA_HOME. The server never imports it:
the server's interpreter has no laya, transformers or safetensors (design M3
section 7.5). -I keeps app/ off sys.path, so nothing from the repository can
be imported here, and -B writes no bytecode anywhere.

The protocol is the REAL stdout, one JSON line at a time: one ready line, then
one reply per request line read from stdin. sys.stdout is pointed at stderr
before laya is imported, because laya prints its warnings to stdout. A failure
is reported by its exception CLASS name, never by its text. The worker stays
alive after a bad request and exits at stdin EOF.

THE NETWORK GUARD COMES FIRST, before torch or laya exist. Every entry point
in GUARDED that this platform has is replaced by _refuse, which counts the
attempt and raises OSError. Each reply carries the running count, and the
bridge kills a worker whose count is not zero. An entry point the platform
does not have is left absent: socket.socket has no sendmsg on Windows, and
adding one sends asyncio down its Unix branch (os.sysconf), so `import torch`
failed (measured 28 September). The count sees Python's socket API only; a
native library that opens its own connection is not seen by it.
"""
import socket

_NET = {"attempts": 0}


def _refuse(*args, **kwargs):
    """Count one network attempt and refuse it."""
    _NET["attempts"] += 1
    raise OSError("the Laya worker makes no network calls")


GUARDED = (("socket", "connect"), ("socket", "connect_ex"), ("socket", "sendto"),
           ("socket", "sendmsg"), ("module", "create_connection"),
           ("module", "getaddrinfo"), ("module", "gethostbyname"),
           ("module", "gethostbyname_ex"))
for _where, _name in GUARDED:
    _owner = socket.socket if _where == "socket" else socket
    if hasattr(_owner, _name):
        setattr(_owner, _name, _refuse)

import json  # noqa: E402  (after the guard, on purpose)
import os  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

WARM_UP = {"warm_up": {"type": "choice", "instructions": "Is this a warm-up call?",
                       "criteria": {"yes": "a warm-up call", "no": "a real question"}}}


def main():
    """Load Laya once, send the ready line, then answer stdin line by line."""
    proto = sys.stdout
    sys.stdout = sys.stderr

    def send(obj):
        print(json.dumps(obj), file=proto, flush=True)

    model_dir = sys.argv[1] if len(sys.argv) > 1 else ""
    if not (os.path.isabs(model_dir) and os.path.isdir(model_dir)):
        send({"ready": False, "error": "NotADirectoryError"})
        return 1
    t0 = time.perf_counter()
    try:
        from importlib.metadata import version
        import torch
        import laya
        agent = laya.load(model_dir, device="cuda" if torch.cuda.is_available() else "cpu")
        agent.predict({"warm_up": True}, WARM_UP)
        ready = {"ready": True, "device": str(agent.device), "laya": version("laya"),
                 "load_s": round(time.perf_counter() - t0, 2)}
    except Exception as exc:
        send({"ready": False, "error": type(exc).__name__})
        return 1
    send(ready)
    for line in sys.stdin:
        if not line.strip():
            continue
        rid = None
        try:
            req = json.loads(line)
            rid = req.get("id")
            t = time.perf_counter()
            out = agent.predict(req["state"], req["questions"])
            reply = {"id": rid, "ok": True, "device": str(agent.device),
                     "ms": round((time.perf_counter() - t) * 1000.0, 1),
                     "model": out.get("model"), "answers": out.get("answers"),
                     "usage": out.get("usage"), "net_attempts": _NET["attempts"]}
            json.dumps(reply)
        except Exception as exc:
            reply = {"id": rid, "ok": False, "error": type(exc).__name__,
                     "net_attempts": _NET["attempts"]}
        send(reply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Measure the spawn with -I -B -X utf8 on this machine, before any test is written**

Write `$SCRATCH/m3_worker/measure_worker.py` with the Write tool. It reads the repository and writes nothing. Its docstring contains no backslash, because a doubled backslash typed into a tool input collapses to a single one on this machine.

```python
"""M3 Task 4 step 2: spawn the scratch worker under Laya's own python with -I -B -X utf8.

Run from the repository root with LAYA_HOME set in this command's environment only:
    LAYA_HOME=<Laya's folder> $PY "$SCRATCH/m3_worker/measure_worker.py" "$SCRATCH/m3_worker/laya_worker.py"
Reads the repository; writes nothing anywhere.
"""
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time

import numpy as np

sys.path.insert(0, os.getcwd())
from app import agent_api as API, agent_trace as T, model_questions as MQ   # noqa: E402
from engine_env import SupervisoryTunerEnv, neutral_action                  # noqa: E402

worker = Path(sys.argv[1]).resolve()
home = Path(os.environ["LAYA_HOME"]).resolve()
python = home / ".venv" / "Scripts" / "python.exe"
model_dir = home / "models" / "multilingual"


def snap(root):
    out = {}
    for p in root.rglob("*"):
        if p.is_file():
            st = p.stat()
            out[p.relative_to(root).as_posix()] = (st.st_size, st.st_mtime_ns)
    return out


before = snap(home)
ep = T.episode("d2", 1)
env = SupervisoryTunerEnv(T.build_cycle(ep), dt=T.DT, seed=ep["seed"])
env.reset(seed=ep["seed"])
env.w = np.asarray(ep["weights"], dtype=np.float32)
rows = []
for _ in range(200):
    rows.append(env._obs().copy())
    env.step(neutral_action())
rows = np.stack(rows).astype(np.float32)
trace = API.Trace(("runs_c4", 5, 1), [], [], [rows, rows], "cpu", {})
state = MQ.build_state(trace, 190)

env_w = {k: v for k, v in os.environ.items()
         if k.upper() != "TYPESAFE_API_KEY" and not k.upper().startswith("HF_TOKEN")}
env_w.update(USE_TF="0", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1",
             TOKENIZERS_PARALLELISM="false", HF_HOME=str(home / ".cache" / "huggingface"))
t0 = time.perf_counter()
proc = subprocess.Popen([str(python), "-I", "-B", "-X", "utf8", str(worker), str(model_dir)],
                        cwd=str(home), env=env_w, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=None, text=True, encoding="utf-8")
lines = queue.Queue()


def pump():
    for line in proc.stdout:
        lines.put(line)
    lines.put(None)


threading.Thread(target=pump, daemon=True).start()
ready = json.loads(lines.get(timeout=120))
print("ready", ready, "spawn->ready", round(time.perf_counter() - t0, 2), "s")
got = []
for rid, questions in ((1, MQ.QUESTIONS), (2, MQ.QUESTIONS_REVERSED)):
    t = time.perf_counter()
    print(json.dumps({"id": rid, "state": state, "questions": questions}), file=proc.stdin, flush=True)
    reply = json.loads(lines.get(timeout=30))
    wall = round((time.perf_counter() - t) * 1000.0, 1)
    a = MQ.to_action(reply["answers"])
    got.append(a)
    print(rid, "ok", reply["ok"], "device", reply["device"], "ms", reply["ms"], "wall_ms", wall,
          "input_tokens", reply["usage"]["input_tokens"], "net_attempts", reply["net_attempts"])
print("held/changed:", {q: ("held" if got[0][q]["choice"] == got[1][q]["choice"] else "changed")
                        for q in MQ.IDS})
t = time.perf_counter()
proc.stdin.close()
print("exit", proc.wait(10), "after stdin close", round(time.perf_counter() - t, 2), "s")
print("LAYA_HOME unchanged:", snap(home) == before, f"({len(before)} files)")
```

Run it. LAYA_HOME is set in this command's environment only; never run setx.

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory}"
LAYA_HOME='C:\Users\admin\Documents\Local AI\laya' $PY "$SCRATCH/m3_worker/measure_worker.py" "$SCRATCH/m3_worker/laya_worker.py" | tee "$SCRATCH/m3_worker/measure.txt"
git status --short        # must print nothing of yours: the measurement writes nothing
```

The prototype printed the following on 28 Sep. It used this worker, run on a clone that has Task 2 and Task 3 as committed, and wrote nothing to stderr. The whole run took 21.6 s, most of it stepping the environment 200 times and taking the two snapshots of LAYA_HOME.

```
ready {'ready': True, 'device': 'cuda', 'laya': '0.3.20', 'load_s': 5.96} spawn->ready 6.01 s
1 ok True device cuda ms 96.2 wall_ms 96.6 input_tokens 2729 net_attempts 0
2 ok True device cuda ms 33.1 wall_ms 33.4 input_tokens 2729 net_attempts 0
held/changed: {'spark_trim': 'changed', 'lambda_trim': 'changed', 'boost_ceiling': 'held', 'cooling_fan': 'changed', 'coolant_pump': 'changed'}
exit 0 after stdin close 0.55 s
LAYA_HOME unchanged: True (29467 files)
```

Decision rule (design 10 step 4): the run fails if the ready line is `{"ready": false, ...}` or the process dies.
- If it fails, remove `"-I"` from the Popen list in `measure_worker.py` and run it again.
- If it then works, keep `-B` and `cwd=LAYA_HOME`, remove `"-I"` from the command in Task 5's `LayaBridge._start`, and say so in both commit messages.

On 28 Sep `-I` worked: spawn to ready took 6.01 s, against the spike's 6.2 s without it.

- [ ] **Step 3: Write the failing tests**

Edit `app/test_agents.py` with the Edit tool. The file is LF, and the Edit tool keeps it that way. No line here contains a backslash-u escape. Each `\n` below is a single backslash; type it once, because a doubled backslash typed into a tool input collapses.

(a) Replace the whole `NEW_MODULES = (...)` assignment, as Task 3 left it with five names, with:

```python
NEW_MODULES = ("agent_trace.py", "agent_catalog.py", "agent_api.py", "model_questions.py",
               "jev.py", "laya_worker.py")
```

(b) Replace the two comment lines and the assignment that Task 3 wrote:

```python
# M3 (design 7.4 and section 9 row 13): jev.py is the one module allowed network
# imports. The scan still reads every app/*.py, the allowed ones included.
NET_ALLOWED = {"jev.py": NET_ROOTS}
```

with:

```python
# M3 (design 7.4, 7.5 and section 9 row 13): jev.py may import any network module;
# laya_worker.py may import socket only, to refuse it. The scan still reads every
# app/*.py, the allowed ones included.
NET_ALLOWED = {"jev.py": NET_ROOTS, "laya_worker.py": {"socket"}}
```

(c) In `class NoNetworkTests`, insert the following directly after its docstring line, `"""Spec test 13: an AST import scan, so 'WebSocket' in server.py is not a hit."""`, and before Task 3's `test_no_network_imports_in_app`:

```python

    def test_the_scan_sees_urllib_in_the_worker(self):
        """The worker is allowed socket, and nothing else in NET_ROOTS."""
        self.assertEqual(_net_hits("laya_worker.py", "import urllib\n"), ["laya_worker.py:1 urllib"])
        self.assertEqual(_net_hits("laya_worker.py", "import socket\n"), [])
```

(d) Replace `MODEL_MODULES = ("model_questions.py", "jev.py")` with:

```python
MODEL_MODULES = ("model_questions.py", "jev.py", "laya_worker.py")
```

(e) Insert the following directly above `def _shape(x):`, which puts it after Task 3's `JevKeyTests`:

```python
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
        tree = _worker_tree()
        i, _ = _guard_loop(tree)
        guard = ast.unparse(ast.Module(body=tree.body[:i + 1], type_ignores=[]))
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
```

- [ ] **Step 4: Run it to verify it fails**

Run:
```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
$PY -m app.test_agents WorkerStaticTests NoNetworkTests NoWriteTests StateTests.test_no_recorded_drive_imports 2>&1 | grep -E "^(ERROR|FAIL):|^[A-Za-z]*Error:|^Ran|^OK|^FAILED"
```

Expected: FAIL. Five tests open `app/laya_worker.py` and each errors with `FileNotFoundError: [Errno 2] No such file or directory: '...\\app\\laya_worker.py'`:
- the three `WorkerStaticTests`;
- `NoWriteTests.test_new_modules_cannot_write`;
- `StateTests.test_no_recorded_drive_imports (module='laya_worker.py')`.

The run ends:
```
Ran 9 tests in 0.1s
FAILED (errors=5)
```

The new probe and Task 3's two `NoNetworkTests` already pass. All of this was observed on the prototype. The prototype also showed that the guard test can fail. With the loop's `if hasattr(_owner, _name):` replaced by `if True:`, `test_the_guard_leaves_missing_entry_points_missing` fails with `AssertionError: 1 != 0 : ... SC_IOV_MAX = os.sysconf('SC_IOV_MAX') ... AttributeError: module 'os' has no attribute 'sysconf'`.

- [ ] **Step 5: Implement: the measured file goes in unchanged**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory}"
cp "$SCRATCH/m3_worker/laya_worker.py" app/laya_worker.py
cmp "$SCRATCH/m3_worker/laya_worker.py" app/laya_worker.py && echo identical
```

Expected: `identical`. If Step 2's decision rule dropped `-I`, this file still does not change, because `-I` is an argument the bridge passes, not part of the worker.

- [ ] **Step 6: Run to verify it passes, then run the default suite**

Run the same command as in Step 4. Expected:
```
Ran 9 tests in 0.2s
OK
```

Then run the default suite. It takes about 4 minutes because the `==` proofs run, so give the Bash tool a timeout of 600000.
```bash
$PY -m app.test_agents > "$SCRATCH/m3_t4_agents.txt" 2>&1; grep -E "== proof|^Ran |^OK|^FAILED|load_pair:" "$SCRATCH/m3_t4_agents.txt"
```

Expected:
- `Ran N tests`, where N is Task 3's recorded count plus 4. The sandbox clone read 78 after Task 3, so 82.
- `OK (skipped=S)`, where S is Task 3's count, unchanged.
- The `== proof PROVEN` line, with the same two damages as before this task, because the tracer is untouched.
- `load_pair: device cuda, ...`.

Read N and S from the run. `tearDownModule` may raise "the suite changed files on disk" and name files another session touched. That is M2's known limit: re-run with HEAD unchanged before and after, and record it. Never weaken the snapshot.

- [ ] **Step 7: Commit**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory}"
git branch --show-current            # must print JMF-2340550-sep17
git add app/laya_worker.py app/test_agents.py
$PY verify_docs.py > "$SCRATCH/m3_t4_verify.txt" 2>&1; tail -1 "$SCRATCH/m3_t4_verify.txt"
$PY -m app.test_replay > "$SCRATCH/m3_t4_replay.txt" 2>&1; tail -1 "$SCRATCH/m3_t4_replay.txt"
cat > "$SCRATCH/m3_t4_msg.txt" <<'EOF'
Agent replay M3 (4a/7): laya_worker -- Laya behind JSON lines, network guarded

app/laya_worker.py runs ONLY under Laya's own python, started as
  <LAYA_HOME>/.venv/Scripts/python.exe -I -B -X utf8 app/laya_worker.py <abs model_dir>
with cwd=LAYA_HOME, and is never imported by the server. In order it:
- replaces every socket entry point in GUARDED that this platform has with a
  function that counts the attempt and raises, before torch or laya exist;
- points sys.stdout at stderr (laya prints warnings to stdout) and keeps the
  real stdout as the protocol stream;
- refuses a model folder that is not an absolute, existing directory;
- loads Laya once, warms it up, sends one ready line, then one JSON reply per
  request line, each carrying the running network count;
- exits at stdin EOF.

MEASURED DEPARTURE from design M3 7.5 step 1 ("eight entry points are
replaced"): socket.socket has no sendmsg on Windows. Assigning one sends
asyncio/selector_events.py down its Unix branch (os.sysconf) and import torch
fails; the prototype's ready line was {"ready": false, "error":
"AttributeError"}. The guard replaces only what exists (seven here).
WorkerStaticTests pins it by importing asyncio after the guard block.

The spawn was measured BEFORE any test was written (design 10 step 4), with
-I -B -X utf8 on this machine; the spike took 6.2 s without -I. Output below.

Tests (app/test_agents.py):
- WorkerStaticTests (spec test 19, the worker's half): the guard comes first
  and socket is named nowhere else; missing entry points stay missing; a
  relative model folder is refused before any import;
- NoNetworkTests: a probe that the scan still sees urllib in the worker;
- NET_ALLOWED gives laya_worker.py socket only (test 13), and the comment
  above it says so;
- NEW_MODULES (test 11) and MODEL_MODULES (test 15) gain laya_worker.py.

EOF
{ echo '$ LAYA_HOME=<Laya folder> python measure_worker.py   (step 2, before any test)'; cat "$SCRATCH/m3_worker/measure.txt"
  echo; echo '$ python -m app.test_agents'; grep -E "== proof|^Ran |^OK|^FAILED|load_pair:" "$SCRATCH/m3_t4_agents.txt"
  echo; echo '$ python -m app.test_replay'; cat "$SCRATCH/m3_t4_replay.txt"
  echo; echo '$ python verify_docs.py'; tail -1 "$SCRATCH/m3_t4_verify.txt"
  echo; echo 'Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'; } >> "$SCRATCH/m3_t4_msg.txt"
git commit -F "$SCRATCH/m3_t4_msg.txt" -- app/laya_worker.py app/test_agents.py
git log -1 --stat | tail -3
```

Expected, each read from the run:
- `verify_docs.py`'s last line reads `All N checks pass (M figure mentions scanned in the documents).`. The clone read `All 67 checks pass (846 figure mentions scanned in the documents).`.
- `app.test_replay` ends with `49 of 49 checks pass` and includes `PASS  READ-ONLY: no write path to the vehicle exists in app/`, as measured on the clone.
- The commit shows `2 files changed`.

**Notes:**
- **Prototype run, 28 Sep.** The prototype was a `git clone` of py-trace's clone, which carries Tasks 1-3 exactly as committed, including Task 3's real `test_agents.py`. Its working-tree line endings were matched to the repository's: LF for `test_agents.py` and `agent_api.py`, CRLF for `server.py`. `app/static/vendor` was copied in, because it is untracked. Tasks 4-6 were applied there and committed. Every failure quoted above was seen before the implementation and every pass after it, and the repository's `git status` stayed clean.
- `print(json.dumps(...), file=proto, flush=True)` does not match the lab's `\.write\s*\(` pattern. That is not the reason the pipe is allowed (design 7.5 gives the reason), and Task 5's print scan pins it explicitly.

---


---

### Task 5: app/laya_bridge.py: load_home, worker_env, LayaBridge (spawn on the first press, the two-request order check, timeouts and kills, status that never spawns, close/atexit); tests 18, 15 (fairness), 19 (print scan over app/), 20 (real Laya, --full)

The code wins, or the plan adds, in five places:
- `ms` covers both requests of one press.
- `model_name`, `laya`, `usage`, `spawns` and `ready` are plan additions to design 7.5 and 7.6.
- The fake worker gains a `bad_choice` mode, which pins that an answer `to_action` refuses leaves the worker alive.
- The reader thread closes the stdout pipe at EOF, so no ResourceWarning is raised.
- `test_a_killed_server_leaves_no_worker` is new. When a server dies without `close()` (Stop-Process or a crash), the worker reads EOF and exits. Every way of stopping the server ends in either `close()` or that EOF, so this test pins the backstop that review focus 5 asks for. T10 still checks Ctrl+C, closing the window and a hard kill live.

**Files:**
- Create: `app/laya_bridge.py`
- Modify: `app/test_agents.py`: two imports, the assignments `NEW_MODULES` and `MODEL_MODULES`, and a new block directly above `def _shape(x):`, after Task 4's block.
- Test: `app/test_agents.py`

**Interfaces:**
- Consumes:
  - From Task 2: `app/model_questions.py` `REPO`, `BadAnswer`, `QUESTIONS`, `QUESTIONS_REVERSED`, `IDS`, `KEYS`, `build_state(trace, step)`, `to_action(answers)` and `user_setting(env_var, file_name, environ=None)`.
  - From Task 2: the test helper `_obs_trace(n)` and the alias `MQ`.
  - From Task 3: the test alias `JEV` (for `JEV.build_request(trace, step)`), `SENTINEL_KEY = "sentinel-key-M3"` and `_net_hits(name, source)`.
  - From Task 4: `app/laya_worker.py`, with its argv contract, its ready line and its reply shapes.
- Produces, in `app/laya_bridge.py`:
  - `WORKER`, `START_TIMEOUT_S = 90.0`, `ANSWER_TIMEOUT_S = 20.0` and `CLOSE_WAIT_S = 5.0`;
  - `KINDS = ("ValueError", "RuntimeError", "OutOfMemoryError")`;
  - `OFFLINE`, which holds 5 variables;
  - `class LayaError(code, kind=None)`, with `.code` and `.kind`;
  - `load_home() -> (python, model_dir, source)`, which raises `LayaError("not_configured" | "not_found")`;
  - `worker_env(home=None) -> dict`;
  - `class LayaBridge(command=None, start_timeout=90.0, answer_timeout=20.0)`:
    - public `spawns` and `ready`;
    - `.status()` returns `{configured, source, problem, worker, device, laya}` and never spawns;
    - `.ask(trace, step)` returns `{model_name, laya, device, ms, started_s, answers, answers_reversed, usage, sent}`;
    - `.close()`;
  - the LayaError codes: `not_configured`, `not_found`, `start_failed`, `start_timeout`, `timeout`, `worker_died`, `bad_answer`, `network_attempt`, and `worker_error` with a kind.
- Produces, in test_agents.py:
  - `FAKE_WORKER` and `LAYA_KEYS`;
  - `_fake_bridge(mode, **kw)`, `class _Spawned` and `_tree_snapshot(root)`;
  - `BridgeTests` (10 tests), `FairnessTests` (1), `PrintScanTests` (2) and `LayaRealTests` (1).
  - Task 6 reuses `_fake_bridge`, `LAYA_KEYS` and `LB`.

- [ ] **Step 1: Write the failing tests**

Edit `app/test_agents.py` with the Edit tool.

(a) Make two import edits. Replace

```python
import shutil
import subprocess
```

with

```python
import shutil
import signal
import subprocess
```

and replace

```python
from app import jev as JEV
```

with

```python
from app import jev as JEV
from app import laya_bridge as LB
```

(b) Replace the `NEW_MODULES = (...)` assignment, which holds Task 4's six names, with:

```python
NEW_MODULES = ("agent_trace.py", "agent_catalog.py", "agent_api.py", "model_questions.py",
               "jev.py", "laya_worker.py", "laya_bridge.py")
```

(c) Replace `MODEL_MODULES = ("model_questions.py", "jev.py", "laya_worker.py")` with:

```python
MODEL_MODULES = ("model_questions.py", "jev.py", "laya_worker.py", "laya_bridge.py")
```

(d) Insert the following directly above `def _shape(x):`, after Task 4's block:
- `FAKE_WORKER` is a raw string and contains no backslash.
- The `server` string in `test_a_killed_server_leaves_no_worker` holds eight `\n`. Each is ONE backslash, typed once: a doubled backslash typed into a tool input collapses, and the string then breaks across lines.
- No line carries a backslash-u escape.

```python
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
send({"ready": True, "device": "fake", "laya": "0.0.0", "load_s": 0.0,
      "env": {k: os.environ.get(k) for k in ("TYPESAFE_API_KEY", "HF_TOKEN",
                                            "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")}})
for line in sys.stdin:
    req = json.loads(line)
    if mode == "hang_answer":
        time.sleep(60)
    if mode == "eof":
        sys.exit(0)
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
        answers[qid] = {"choice": pick, "confidence": 0.5, "answer_confidence": 0.6,
                        "probabilities": {k: (0.6 if k == pick else 0.1) for k in keys}}
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
```

After editing, run `grep -c 'server = ("import sys' app/test_agents.py`. It must print `1`. Then run `$PY -c "import ast; ast.parse(open('app/test_agents.py', encoding='utf-8').read())"`. It must print nothing: a collapsed or doubled `\n` shows up here as a SyntaxError.

- [ ] **Step 2: Run it to verify it fails**

Run:
```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
$PY -m app.test_agents BridgeTests 2>&1 | tail -3
```

Expected: FAIL, because the test module cannot import the bridge. This was observed on the prototype:
```
    from app import laya_bridge as LB
ImportError: cannot import name 'laya_bridge' from 'app' (unknown location)
```

- [ ] **Step 3: Implement app/laya_bridge.py**

Write `app/laya_bridge.py` with the Write tool. It contains no backslash and no backslash-u escape. The docstring carries the Arabic «اسأل لايا» as literal characters, not as escapes.

```python
"""Laya's worker, seen from the server: find it, start it, ask it, stop it.

Laya runs in its OWN interpreter (LAYA_HOME/.venv), because the server's has
no laya, transformers or safetensors, and installing them would change the
interpreter that runs the scored == proof (design M3 section 7.5). So the
bridge starts app/laya_worker.py under Laya's python and speaks JSON lines to
it: one request per line on the worker's stdin, one reply per line back.

WHEN A WORKER EXISTS. Building a LayaBridge reads no file and starts nothing,
and status() never starts one either. Only ask(), which only a press of
«اسأل لايا» reaches, starts the worker, and only when none is alive. It then
stays resident until the server stops: close() is registered with atexit on
the first start, and closes stdin, waits CLOSE_WAIT_S, then kills.

EVERY PRESS ASKS TWICE (design 7.5b): QUESTIONS, the very object jev gets,
then QUESTIONS_REVERSED, the same questions with each one's five options in
reverse order. Laya is deterministic, so a choice that differs between the two
changed with the order alone.

WHAT KILLS THE WORKER: no ready line within start_timeout, no answer within
answer_timeout, a reply whose id is not the request's, and a reply whose
network count is not zero. A late line would put the protocol out of step, so
the next press starts a fresh worker. A reply of ok: false (worker_error) and
an answer to_action refuses (bad_answer) leave it running.

THE WORKER'S ENVIRONMENT is the server's without TYPESAFE_API_KEY or any
HF_TOKEN*, with Hugging Face forced offline. Its stderr goes to the server's
console, never to a file. The only print that does not go to stderr is the
request line into the worker's stdin: a pipe to a process on this machine,
not a path to the vehicle.
"""
from __future__ import annotations

import atexit
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time

from app.model_questions import (BadAnswer, QUESTIONS, QUESTIONS_REVERSED, REPO, build_state,
                                 to_action, user_setting)

WORKER = Path(__file__).resolve().parent / "laya_worker.py"
START_TIMEOUT_S = 90.0
ANSWER_TIMEOUT_S = 20.0
CLOSE_WAIT_S = 5.0
KINDS = ("ValueError", "RuntimeError", "OutOfMemoryError")
OFFLINE = {"USE_TF": "0", "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
           "HF_HUB_DISABLE_TELEMETRY": "1", "TOKENIZERS_PARALLELISM": "false"}


class LayaError(Exception):
    """A fixed code (design 7.9) and, for worker_error only, a fixed kind."""

    def __init__(self, code, kind=None):
        super().__init__(code)
        self.code, self.kind = code, kind


def _under_repo(path):
    p = Path(path).resolve()
    return p == REPO or REPO in p.parents


def load_home():
    """(python, model_dir, source) for LAYA_HOME, or LayaError.

    The one place a setting's VALUE is checked as a path: the folder must be
    absolute, and neither it, its python nor its model may resolve under the
    repository. not_configured: no LAYA_HOME at all; not_found: anything else.
    """
    value, source = user_setting("LAYA_HOME", "laya_home")
    if not value:
        raise LayaError("not_configured")
    home = Path(value)
    python = home / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    model_dir = home / "models" / "multilingual"
    if (not home.is_absolute() or _under_repo(home) or _under_repo(python)
            or _under_repo(model_dir) or not python.is_file()
            or not (model_dir / "rl_agent_config.json").is_file()):
        raise LayaError("not_found")
    return str(python), str(model_dir.resolve()), source


def worker_env(home=None):
    """The server's environment without the jev key or any HF token, offline."""
    env = {k: v for k, v in os.environ.items()
           if k.upper() != "TYPESAFE_API_KEY" and not k.upper().startswith("HF_TOKEN")}
    env.update(OFFLINE)
    if home is not None:
        env["HF_HOME"] = str(Path(home) / ".cache" / "huggingface")
    return env


def _pump(stream, lines):
    """The reader thread: every stdout line onto the queue, then None at EOF.
    A pipe cannot be read with a timeout on Windows; a queue can."""
    try:
        for line in stream:
            lines.put(line)
    except (OSError, ValueError):
        pass
    finally:
        lines.put(None)
        try:
            stream.close()
        except OSError:
            pass


class LayaBridge:
    """One Laya worker, started by the first ask and kept until close().

    `command` replaces the real spawn (tests pass a fake worker run by
    sys.executable); it is then started with no cwd and worker_env(None).
    `spawns` counts Popen calls; `ready` is a live worker's ready line.
    """

    def __init__(self, command=None, start_timeout=START_TIMEOUT_S,
                 answer_timeout=ANSWER_TIMEOUT_S):
        self._command = list(command) if command is not None else None
        self.start_timeout, self.answer_timeout = start_timeout, answer_timeout
        self._proc = None
        self._lines = None
        self._next_id = 0
        self._starting = False
        self._failed = None
        self._atexit = False
        self.ready = None
        self.spawns = 0

    def _alive(self):
        return self._proc is not None and self._proc.poll() is None

    def status(self):
        """What the page's Laya column shows. Reads the setting; never spawns."""
        if self._command is not None:
            configured, source, problem = True, "command", None
        else:
            _value, source = user_setting("LAYA_HOME", "laya_home")
            try:
                load_home()
                configured, problem = True, None
            except LayaError as err:
                configured, problem = err.code != "not_configured", err.code
        alive = self._alive()
        worker = ("starting" if self._starting else "ready" if alive
                  else "failed" if self._failed else "stopped")
        if problem is None and worker == "failed":
            problem = self._failed
        ready = self.ready if alive else None
        return {"configured": configured, "source": source, "problem": problem,
                "worker": worker, "device": ready.get("device") if ready else None,
                "laya": ready.get("laya") if ready else None}

    def _kill(self):
        """Kill and reap the worker, and forget it: the next ask starts another."""
        proc, self._proc, self._lines, self.ready = self._proc, None, None, None
        if proc is None:
            return
        try:
            proc.kill()
            proc.wait(CLOSE_WAIT_S)
        except (OSError, subprocess.TimeoutExpired):
            pass
        try:
            proc.stdin.close()
        except OSError:
            pass

    def _start(self):
        """Spawn, wait for the ready line, and return the seconds it took."""
        if self._command is not None:
            cmd, home = self._command, None
        else:
            python, model_dir, _source = load_home()
            home = str(Path(model_dir).parents[1])
            cmd = [python, "-I", "-B", "-X", "utf8", str(WORKER), model_dir]
        self._starting = True
        try:
            self.spawns += 1
            t0 = time.perf_counter()
            try:
                proc = subprocess.Popen(cmd, cwd=home, env=worker_env(home),
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=None, text=True, encoding="utf-8")
            except OSError:
                self._failed = "start_failed"
                raise LayaError("start_failed") from None
            lines = queue.Queue()
            threading.Thread(target=_pump, args=(proc.stdout, lines), daemon=True,
                             name="laya-reader").start()
            if not self._atexit:
                atexit.register(self.close)
                self._atexit = True
            self._proc = proc
            try:
                line = lines.get(timeout=self.start_timeout)
            except queue.Empty:
                self._kill()
                self._failed = "start_timeout"
                raise LayaError("start_timeout") from None
            try:
                ready = json.loads(line) if line is not None else None
            except ValueError:
                ready = None
            if not isinstance(ready, dict) or ready.get("ready") is not True:
                self._kill()
                self._failed = "start_failed"
                raise LayaError("start_failed")
            self._lines, self.ready, self._failed = lines, ready, None
            return round(time.perf_counter() - t0, 2)
        finally:
            self._starting = False

    def _request(self, state, questions):
        """One request line out, one reply line back, checked; the reply dict."""
        self._next_id += 1
        rid = self._next_id
        proc = self._proc
        try:
            print(json.dumps({"id": rid, "state": state, "questions": questions}),
                  file=proc.stdin, flush=True)
        except (OSError, ValueError):
            self._kill()
            raise LayaError("worker_died") from None
        try:
            raw = self._lines.get(timeout=self.answer_timeout)
        except queue.Empty:
            self._kill()
            raise LayaError("timeout") from None
        if raw is None:
            self._kill()
            raise LayaError("worker_died")
        try:
            reply = json.loads(raw)
        except ValueError:
            reply = None
        if not isinstance(reply, dict) or reply.get("id") != rid:
            self._kill()
            raise LayaError("bad_answer")
        if reply.get("net_attempts") != 0:
            self._kill()
            raise LayaError("network_attempt")
        if reply.get("ok") is not True:
            kind = reply.get("error")
            raise LayaError("worker_error", kind if kind in KINDS else "other")
        return reply

    def ask(self, trace, step):
        """Ask Laya about one second, twice: the design's order, then reversed."""
        state = build_state(trace, step)
        started_s = None
        if not self._alive():
            self._proc = None
            started_s = self._start()
        t0 = time.perf_counter()
        forward = self._request(state, QUESTIONS)
        reverse = self._request(state, QUESTIONS_REVERSED)
        ms = round((time.perf_counter() - t0) * 1000.0, 1)
        try:
            answers = to_action(forward.get("answers"))
            answers_reversed = to_action(reverse.get("answers"))
        except BadAnswer:
            raise LayaError("bad_answer") from None
        name = forward.get("model")
        return {"model_name": name if isinstance(name, str) and len(name) <= 64 else None,
                "laya": (self.ready or {}).get("laya"), "device": forward.get("device"),
                "ms": ms, "started_s": started_s,
                "answers": answers, "answers_reversed": answers_reversed,
                "usage": [forward.get("usage"), reverse.get("usage")],
                "sent": [{"state": state, "questions": QUESTIONS},
                         {"state": state, "questions": QUESTIONS_REVERSED}]}

    def close(self):
        """Close stdin, wait CLOSE_WAIT_S for the worker to exit, then kill. Idempotent."""
        proc, self._proc, self._lines, self.ready = self._proc, None, None, None
        if proc is None:
            return
        try:
            proc.stdin.close()
        except OSError:
            pass
        try:
            proc.wait(CLOSE_WAIT_S)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(CLOSE_WAIT_S)
```

If Task 4's decision rule dropped `-I`, delete `"-I", ` from the `cmd` list in `_start`, and only there.

- [ ] **Step 4: Run to verify it passes**

Run:
```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
$PY -m app.test_agents BridgeTests FairnessTests PrintScanTests LayaRealTests NoWriteTests StateTests.test_no_recorded_drive_imports NoNetworkTests WorkerStaticTests 2>&1 | grep -E "^(ERROR|FAIL):|^Ran|^OK|^FAILED|skipped '"
```

Expected:
```
test_real_laya (__main__.LayaRealTests.test_real_laya) ... skipped 'the real Laya runs only under --full'
Ran 23 tests in 5.3s
OK (skipped=1)
```

The prototype read the same on three runs out of three. Most of the roughly 5 s is the four 1-second timeouts.

The killed-server test can also fail. On the prototype, the fake worker was given a trailing `time.sleep(20)`, so it ignored EOF for 20 s. The test then failed with `AssertionError: True is not false : the worker outlived its server by 10 s`, and its `os.kill` removed the orphan.

- [ ] **Step 5: Run the real Laya once (test 20, `--full`, LAYA_HOME in this command only)**

Run:
```bash
LAYA_HOME='C:\Users\admin\Documents\Local AI\laya' $PY -m app.test_agents --full LayaRealTests 2>&1 | tee "$SCRATCH/m3_t5_laya_real.txt" | tail -8
$PY -m app.test_agents --full LayaRealTests 2>&1 | grep -E "skipped|^OK"
```

Expected from the first command, as observed on the prototype. The run takes about 32 s: the environment is stepped twice 200 times, the model loads in 6.4 s, and each of the two snapshots walks about 29 500 files.
```
test_real_laya (__main__.LayaRealTests.test_real_laya) ...
    Laya: cuda, laya 0.3.20, first load 6.38 s, both requests 152.3 ms then 71.0 ms, input tokens 2729; order check (an observation, not asserted): {'spark_trim': 'changed', 'lambda_trim': 'changed', 'boost_ceiling': 'held', 'cooling_fan': 'changed', 'coolant_pump': 'changed'}
ok
Ran 1 test in 31.7s
OK
```

The second command runs without LAYA_HOME. Expected: `skipped "LAYA_HOME is not set in this process, so the real Laya is UNPROVEN here: ..."` and `OK (skipped=1)`.

Then check that no worker survived:
```bash
powershell -NoProfile -Command "@(Get-Process python -ErrorAction SilentlyContinue | Where-Object { `$_.Path -like 'C:\Users\admin\Documents\Local AI\laya\.venv\*' }).Count"
```

Expected: `0`, as observed on the prototype.

- [ ] **Step 6: Run the default suite**

```bash
$PY -m app.test_agents > "$SCRATCH/m3_t5_agents.txt" 2>&1; grep -E "== proof|^Ran |^OK|^FAILED|load_pair:" "$SCRATCH/m3_t5_agents.txt"
```

Expected:
- `Ran N tests`, where N is Task 4's count plus 14. On the clone that is 96.
- `OK (skipped=S)`, where S is Task 4's count plus 1. The extra skip is `LayaRealTests`, which runs only under `--full`.
- The `== proof PROVEN` line with unchanged damages.

The suite takes about 4 minutes, so give the Bash tool a timeout of 600000. Test 11's known limit applies here as it did in Task 4.

- [ ] **Step 7: Commit**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory}"
git branch --show-current            # must print JMF-2340550-sep17
git add app/laya_bridge.py app/test_agents.py
$PY verify_docs.py > "$SCRATCH/m3_t5_verify.txt" 2>&1; tail -1 "$SCRATCH/m3_t5_verify.txt"
$PY -m app.test_replay > "$SCRATCH/m3_t5_replay.txt" 2>&1; tail -1 "$SCRATCH/m3_t5_replay.txt"
cat > "$SCRATCH/m3_t5_msg.txt" <<'EOF'
Agent replay M3 (4b/7): laya_bridge -- spawn on the first press, order check, timeouts kill

app/laya_bridge.py starts app/laya_worker.py under Laya's own python and speaks
JSON lines to it (design M3 7.5):
- load_home(): LAYA_HOME from user_setting; the folder must be absolute, and
  neither it, its .venv python nor models/multilingual may resolve under the
  repository (not_configured / not_found);
- worker_env(): the server's environment without TYPESAFE_API_KEY or any
  HF_TOKEN*, Hugging Face offline, HF_HOME under LAYA_HOME;
- LayaBridge(): constructing it does no I/O and status() never spawns. ask()
  starts the worker on the first press only (90 s to the ready line), then
  asks TWICE -- QUESTIONS, the object jev gets, then QUESTIONS_REVERSED (design
  7.5b) -- with 20 s per answer. A timeout, an id mismatch or a non-zero
  network count kills the worker and the next press respawns it; worker_error
  and an answer to_action refuses leave it alive. close() closes stdin, waits
  5 s, then kills; atexit.register(close) is installed once, on the first
  start. A server that dies without close() leaves no worker either: its end
  of the worker's stdin closes, and the worker exits at EOF.

Plan additions to design 7.5/7.6: ms covers both requests; model_name, laya,
usage, spawns and ready; the reader thread closes the pipe at EOF.

Tests (app/test_agents.py): BridgeTests (spec 18, a fake worker in a string:
every error mode, kills and respawns, status never spawns, a hard-killed
server leaves no worker, the key never reaches the worker), FairnessTests
(spec 15: both models get == state and the identical QUESTIONS),
PrintScanTests (spec 19 across app/: only the worker's protocol stream and
the bridge's pipe print anywhere but stderr; the bridge imports no network
module), LayaRealTests (spec 20, --full, LAYA_HOME from the process
environment only).

EOF
{ echo '$ LAYA_HOME=<Laya folder> python -m app.test_agents --full LayaRealTests'; grep -E "Laya:|^Ran |^OK|^FAILED" "$SCRATCH/m3_t5_laya_real.txt"
  echo; echo '$ python -m app.test_agents'; grep -E "== proof|^Ran |^OK|^FAILED|load_pair:" "$SCRATCH/m3_t5_agents.txt"
  echo; echo '$ python -m app.test_replay'; cat "$SCRATCH/m3_t5_replay.txt"
  echo; echo '$ python verify_docs.py'; tail -1 "$SCRATCH/m3_t5_verify.txt"
  echo; echo 'Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'; } >> "$SCRATCH/m3_t5_msg.txt"
git commit -F "$SCRATCH/m3_t5_msg.txt" -- app/laya_bridge.py app/test_agents.py
git log -1 --stat | tail -3
```

Expected, each read from the run:
- `verify_docs.py`'s last line reads `All N checks pass (M figure mentions scanned in the documents).`. The clone read 67 and 846.
- `app.test_replay` ends with `49 of 49 checks pass`, as measured on the clone with this file present.
- The commit shows `2 files changed`.

**Notes:**
- The prototype's fake worker pinned every error mode of the bridge:
  - `start_timeout` fires after 1.0 s;
  - the answer timeout fires after 1.0 s, and the next ask respawns;
  - `worker_error` keeps the worker alive;
  - `close()` takes 0.0 s.
- `_Spawned.patch()` patches `subprocess.Popen` for the whole process while it is active. No other code in the suite spawns inside those blocks.
- The killed-server test reads `bridge._proc.pid` only to clean up an orphan if the test fails. The pass condition does not depend on the pid: it is EOF on the stderr pipe that the stand-in server and its worker share.
- T10 still owns the live shutdown checks: Ctrl+C, closing the window, and Stop-Process. All three end in either `close()` or stdin EOF, and this task pins both of those.

---


---

### Task 6: The four routes and install(app, store=None, jev_send=None, laya=None): AskBody (strict, anchored TRACE_KEY), the Origin/Host guard, trace resolution, per-model locks, no-store bodies and stderr lines; server.py:43 and agent_api docstrings; tests 10 (amend) and 16

Where the code wins over design 7.6, or the plan adds to it:
- `model` names the column (`"jev"` or `"laya"`) in every body, success or error. `model_name` is the name the service returned. The design lists only `model`.
- `TRACE_KEY`, `AskBody`, `same_origin` and `NoStoreRoute` sit after `_ROADS` (`agent_api.py:248`), because `SEED_TEXT` and `EP_TEXT` are defined at `:244-245`.
- `fastapi.Request` and pydantic are now imported at module level, because `from __future__ import annotations` resolves handler annotations against the module's globals.
- **Plan addition, which closes a spec gap: `NoStoreRoute`.**
  - Pydantic validates the body before the handler runs. FastAPI's own 422, and its 405 for a wrong method, therefore never pass through `answer()` and carried no `Cache-Control` header. That broke the rule that every response of the four routes is no-store.
  - The four routes are therefore added with `app.router.add_api_route(..., route_class_override=NoStoreRoute)`. The class adds the header to every response and keeps FastAPI's own 422 and 405 bodies unchanged.
  - A malformed body is still refused before the Origin guard runs. No work is done for it.
  - T11 records this.
- Both status routes also turn an exception into a 500 `server_error`.
- Test 13 was already amended in Tasks 3-5.
- The tests reuse Task 3's `_FakeSend`, `_jev_key(key)`, `SENTINEL_KEY` and `_model_answer()`, and `AskRouteTests` is a `_JevCase`. This task defines no second fake send.

**Files:**
- Modify: `app/agent_api.py`, all six places as they are at d347ee5 (Tasks 2 and 3 do not touch this file):
  - `:1-2`, the docstring;
  - `:22-24`, the imports;
  - `:237-241`, the route comment;
  - `:247-248`, where the new block goes after them;
  - `:341-346`, the head of `install`;
  - `:400-404`, after which the four routes are appended, following the episode route.
- Modify: `app/server.py:42-44`, the last sentence of the module docstring. This file is CRLF, and the Edit tool keeps it that way.
- Modify: `app/test_agents.py`, in these places:
  - `RouteTests.test_routes_only_under_simulation`: its subprocess line (`:1342` after Task 3) and its route assertions (`:1372-1376` after Task 3);
  - a new block directly above `def _shape(x):`, after Task 5's block.

  There is no new import: `contextlib`, `io`, `logging` and `URLError` all arrived with Task 3.
- Test: `app/test_agents.py`

**Interfaces:**
- Consumes:
  - From Task 3: `app/jev.py` `JevError(code, status)` (with `.code` and `.status`), `MODEL`, `load_key()`, `_send`, `ask(trace, step, send=...)` and `build_request(trace, step)`.
  - From Task 3, in the tests: `JEV`, `SENTINEL_KEY`, `_FakeSend(status=200, payload=None, exc=None)` (with `.calls`, a list of `(body, key)`), `_jev_key(key)`, `_JevCase`, `_model_answer(pick=1)` and `URLError`.
  - From Task 5: `app/laya_bridge.py` `LayaBridge`, `LayaError` (with `.code` and `.kind`), `.status()` and `.ask()`.
  - From Task 5, in the tests: `_fake_bridge`, `LAYA_KEYS` and `LB`.
  - From Task 2: `_obs_trace(n)` and `MQ`.
  - `app/agent_api.py:151` `EpisodeStore.trace(key)`, and `:243-245` `NO_STORE`, `SEED_TEXT` and `EP_TEXT`.
  - `app/agent_catalog.py:41` `RUNS_NAME` and `app/agent_trace.py:29` `STEPS = 719`.
- Produces, in `app/agent_api.py`:
  - module level: `TRACE_KEY`, `LOCAL_HOST`, `MODEL_HTTP`, `class AskBody`, `same_origin(request) -> bool` and `class NoStoreRoute(APIRoute)`.
  - `install(app, store=None, jev_send=None, laya=None)`, which:
    - sets `app.state.agent_store`, `app.state.laya` and `app.state.model_locks = {"jev": Lock, "laya": Lock}`;
    - keeps the three GET routes;
    - adds `GET /api/agents/jev/status`, `POST /api/agents/jev`, `GET /api/agents/laya/status` and `POST /api/agents/laya`, all four as `NoStoreRoute`.
  - The responses:
    - jev 200: `{model: "jev", runs_on: "external", model_name, ms, answers, sent, trace, step}`;
    - Laya 200: `{model: "laya", runs_on: "local", model_name, laya, device, ms, started_s, answers, answers_reversed, usage, sent, trace, step}`;
    - error: `{model, code}`, plus `status` for `vendor_status` and `kind` for `worker_error`, sent at the HTTP status `MODEL_HTTP.get(code, 502)` with no-store, plus one stderr line `"{model}: {code} (step {step})"`;
    - FastAPI's own 422 and 405 on these four routes, which now carry no-store too.
- Produces, in `app/server.py`: the sentence at `:43`, verbatim from the skeleton.
- Produces, in test_agents.py:
  - `ASK_BASE`, `ORIGIN`, `ASK_URLS`, `STATUS_URLS`, `ASK_BODY` and `JEV_KEYS`;
  - `_TraceStore` and `_Boom`;
  - `AskRouteTests(_JevCase)`, with 11 tests.

- [ ] **Step 1: Write the failing tests**

Edit `app/test_agents.py` with the Edit tool. The file is LF, and no line contains a backslash-u escape. Every `\n` below is a single backslash, typed once, as it already is in that test.

(a) In `RouteTests.test_routes_only_under_simulation`, replace the line

```python
                "print(json.dumps({'mods': sorted(m for m in sys.modules if m.startswith('app.agent')),\n"
```

with the two lines

```python
                "print(json.dumps({'mods': sorted(m for m in sys.modules if m.startswith(\n"
                "  ('app.agent', 'app.jev', 'app.laya', 'app.model_questions'))),\n"
```

(b) In the same test, replace

```python
        self.assertEqual(added, {"/agents", "/api/agents/episode", "/api/agents/catalog"})
        for p in sorted(added):
            self.assertEqual(set(paths[p].methods), {"GET"}, p)
        self.assertEqual(client.post(EPISODE_URL).status_code, 405)
        self.assertEqual(client.post(CATALOG_URL).status_code, 405)
```

with

```python
        posts = {"/api/agents/jev", "/api/agents/laya"}
        self.assertEqual(added, {"/agents", "/api/agents/episode", "/api/agents/catalog",
                                 "/api/agents/jev/status", "/api/agents/laya/status"} | posts)
        for p in sorted(added):
            self.assertEqual(set(paths[p].methods), {"POST"} if p in posts else {"GET"}, p)
        self.assertEqual(client.post(EPISODE_URL).status_code, 405)
        self.assertEqual(client.post(CATALOG_URL).status_code, 405)
        for p in sorted(posts):
            self.assertEqual(client.get(p).status_code, 405, p)
```

(c) Insert the following directly above `def _shape(x):`, after Task 5's block:

```python
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
```

- [ ] **Step 2: Run it to verify it fails**

Run:
```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
$PY -m app.test_agents AskRouteTests RouteTests.test_routes_only_under_simulation 2>&1 | grep -E "^Ran|^OK|^FAILED|^TypeError|^(FAIL):" | sort | uniq -c
```

Expected: FAIL. This was observed on the prototype, built on Task 3's real test file:
```
      1 FAIL: test_routes_only_under_simulation (__main__.RouteTests.test_routes_only_under_simulation)
      1 FAIL: test_the_server_docstring_names_both_posts (__main__.AskRouteTests.test_the_server_docstring_names_both_posts)
      1 FAILED (failures=2, errors=13)
      1 Ran 12 tests in 0.6s
     13 TypeError: install() got an unexpected keyword argument 'jev_send'
```

- The routes-only failure reads `AssertionError: Items in the second set but not the first:` and lists the four new paths.
- The docstring failure reads `'/api/agents/jev' not found in "server.py — the local host. ..."`.

- [ ] **Step 3: Implement agent_api.py (six edits) and server.py (one edit)**

Use the Edit tool. `app/agent_api.py` is LF and `app/server.py` is CRLF (`core.autocrlf` is true); the Edit tool keeps both.

There is no backslash-u escape anywhere in these edits. The only backslashes are the single ones in the raw regex `LOCAL_HOST`, so type each of them once. After editing, `grep -n 'LOCAL_HOST = ' app/agent_api.py` must print `LOCAL_HOST = re.compile(r"^(127\.0\.0\.1|localhost):\d{1,5}$")`. If a backslash ended up doubled, every 200 in Step 4 fails.

Edit 1, `app/agent_api.py:1-2`. Replace

```python
"""The agent replay page's server side: the model loader, the episode store and
the three routes.
```

with

```python
"""The agent replay page's server side: the model loader, the episode store and
the seven routes. Three GETs serve the page and its episodes. Four serve the
hidden models panel (design M3 section 7.6): a status GET and an ask POST for
each of jev and Laya. Each POST asks one model about one second of a finished
episode.
```

Edit 2, `app/agent_api.py:22-24`. Replace

```python
import numpy as np

from app import agent_catalog
```

with

```python
import numpy as np
from fastapi import Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field

from app import agent_catalog
```

Edit 3, `app/agent_api.py:237-241`. Replace

```python
# app/server.py calls install(app) inside `if a.simulation:` in main(), so the
# --live and --replay processes never import this module. Every route here is
# a GET and answers with Cache-Control: no-store. A request names an episode
# by three strings that must match fixed patterns before anything is looked up;
# no path is ever built from a request.
```

with

```python
# app/server.py calls install(app) inside `if a.simulation:` in main(), so the
# --live and --replay processes never import this module. Every route here
# answers with Cache-Control: no-store, and every one is a GET except two
# POSTs, /api/agents/jev and /api/agents/laya, which ask a language model about
# one second of a finished episode. The four model routes use NoStoreRoute, so
# the refusals FastAPI makes itself (a body that fails AskBody, a wrong method)
# are no-store as well. A request names an episode by strings that must match
# fixed patterns before anything is looked up; no path is ever built from a
# request.
```

Keep that wording exactly. A first draft put a status code right before the verb for carrying a header, and `verify_docs.py` failed on it, reading the status code as a drive count. That is its anchored-pattern behaviour, and the checker is right to flag it.

Edit 4, `app/agent_api.py:247-248`. Replace

```python
STATIC = Path(__file__).resolve().parent / "static"
_ROADS = {}
```

with

```python
STATIC = Path(__file__).resolve().parent / "static"
_ROADS = {}

# The two POSTs' body (design M3 section 7.6, C7). Pydantic's `pattern` is an
# unanchored search, so TRACE_KEY carries its own ^...$, and strict=True
# refuses "312", true and 1.0 as a step. AskBody and Request must be
# module-level names: `from __future__ import annotations` makes the handlers'
# annotations strings, which FastAPI resolves against this module's globals.
TRACE_KEY = (rf"^{agent_catalog.RUNS_NAME.pattern.strip('^$')}"
             rf"/(?:{SEED_TEXT.pattern})/(?:{EP_TEXT.pattern})$")
LOCAL_HOST = re.compile(r"^(127\.0\.0\.1|localhost):\d{1,5}$")
MODEL_HTTP = {"no_key": 503, "not_configured": 503, "not_found": 503, "foreign_origin": 403,
              "no_trace": 409, "step_not_computed": 409, "busy": 409, "server_error": 500}


class AskBody(BaseModel):
    """{"trace": "runs_c4/5/1", "step": 312}, and nothing else, nothing coerced."""
    model_config = ConfigDict(extra="forbid", strict=True)
    trace: str = Field(pattern=TRACE_KEY)
    step: int = Field(ge=0, le=agent_trace.STEPS - 1)


def same_origin(request):
    """True when Origin is present and equals http:// + Host, and Host is this
    machine by name and port. Checking Host as well refuses DNS rebinding
    (design M3 C8); browsers send Origin on every POST."""
    host = request.headers.get("host") or ""
    return (LOCAL_HOST.fullmatch(host) is not None
            and request.headers.get("origin") == f"http://{host}")


class NoStoreRoute(APIRoute):
    """The four model routes' class: EVERY response carries no-store, FastAPI's
    own included. A body that fails AskBody is refused before the handler
    runs, with FastAPI's own 422 {"detail": [...]}; a wrong method gets
    FastAPI's own 405 {"detail": "Method Not Allowed"} and its Allow header.
    Only the header is added; neither body changes."""

    def get_route_handler(self):
        handler = super().get_route_handler()

        async def no_store(request):
            try:
                response = await handler(request)
            except RequestValidationError as exc:
                response = await request_validation_exception_handler(request, exc)
            response.headers.update(NO_STORE)
            return response

        return no_store

    async def handle(self, scope, receive, send):
        if self.methods and scope["method"] not in self.methods:
            allow = ", ".join(sorted(self.methods))
            response = JSONResponse({"detail": "Method Not Allowed"}, status_code=405,
                                    headers={"Allow": allow, **NO_STORE})
            await response(scope, receive, send)
            return
        await super().handle(scope, receive, send)
```

Edit 5, `app/agent_api.py:341-346`. Replace

```python
def install(app, store=None):
    """Add GET /agents, GET /api/agents/catalog and GET /api/agents/episode to `app`."""
    from fastapi.responses import HTMLResponse, JSONResponse

    store = store if store is not None else EpisodeStore()
    app.state.agent_store = store
```

with

```python
def install(app, store=None, jev_send=None, laya=None):
    """Add the page's seven routes to `app`.

    GET /agents, GET /api/agents/catalog and GET /api/agents/episode serve the
    page and its episodes. GET /api/agents/jev/status, POST /api/agents/jev,
    GET /api/agents/laya/status and POST /api/agents/laya serve the hidden
    models panel: each POST asks one model about one second of a finished
    episode. /api/agents/jev sends it to an external service in the USA;
    /api/agents/laya sends it to a worker process on this machine, and nothing
    leaves the machine. Neither has a path to the vehicle.

    `jev_send` replaces jev's HTTP call and `laya` the Laya bridge; tests pass
    fakes. The defaults are jev._send and a LayaBridge(), whose construction
    reads no file and starts nothing. Each model has its own lock, so one
    model's slow or failing call never makes the other busy.
    """
    from fastapi.responses import HTMLResponse, JSONResponse

    from app import jev
    from app.laya_bridge import LayaBridge, LayaError

    store = store if store is not None else EpisodeStore()
    jev_send = jev_send if jev_send is not None else jev._send
    laya = laya if laya is not None else LayaBridge()
    app.state.agent_store = store
    app.state.laya = laya
    app.state.model_locks = {"jev": threading.Lock(), "laya": threading.Lock()}
```

Edit 6, `app/agent_api.py:400-404`, the end of the episode route and of the file. Replace

```python
            out = store.poll((runs, seed_n, idx), since=since_n, preempt=preempt_on)
            out.update(first)
            return answer(out)
        except Exception as exc:
            return answer({"detail": f"server error: {type(exc).__name__}"}, 500)
```

with

```python
            out = store.poll((runs, seed_n, idx), since=since_n, preempt=preempt_on)
            out.update(first)
            return answer(out)
        except Exception as exc:
            return answer({"detail": f"server error: {type(exc).__name__}"}, 500)

    # ---- the models panel (design M3 section 7.6) ---------------------------

    def refuse(model, code, step, status=None, kind=None):
        """A fixed code for the asking model's own column, and one stderr line
        that carries no state and no key. Never str(exc), never a vendor body."""
        print(f"{model}: {code} (step {step})", file=sys.stderr)
        body = {"model": model, "code": code}
        if code == "vendor_status":
            body["status"] = status
        if code == "worker_error":
            body["kind"] = kind
        return answer(body, MODEL_HTTP.get(code, 502))

    def ask_model(model, body, request):
        """The guards in order (Origin, trace, this model's own lock), then one ask."""
        if not same_origin(request):
            return refuse(model, "foreign_origin", body.step)
        runs, seed, ep = body.trace.split("/")
        trace = store.trace((runs, int(seed), int(ep)))
        if trace is None:
            return refuse(model, "no_trace", body.step)
        if body.step >= len(trace.obs[0]):
            return refuse(model, "step_not_computed", body.step)
        lock = app.state.model_locks[model]
        if not lock.acquire(blocking=False):
            return refuse(model, "busy", body.step)
        try:
            if model == "jev":
                out = dict(model="jev", runs_on="external",
                           **jev.ask(trace, body.step, send=jev_send))
            else:
                out = dict(model="laya", runs_on="local", **laya.ask(trace, body.step))
        except jev.JevError as err:
            return refuse(model, err.code, body.step, status=err.status)
        except LayaError as err:
            return refuse(model, err.code, body.step, kind=err.kind)
        finally:
            lock.release()
        return answer(dict(out, trace=body.trace, step=body.step))

    def guarded(model, body, request):
        """Anything unexpected is 500 server_error with no-store, never str(exc)."""
        try:
            return ask_model(model, body, request)
        except Exception as exc:
            print(f"{model}: server_error {type(exc).__name__} (step {body.step})",
                  file=sys.stderr)
            return answer({"model": model, "code": "server_error"}, 500)

    def agents_jev_status():
        """Whether a jev key is configured, and where jev runs. Never the key;
        sends nothing."""
        try:
            key, source = jev.load_key()
            return answer({"configured": bool(key), "source": source if key else None,
                           "vendor": "typesafe.ai", "model": jev.MODEL, "hosted": "USA"})
        except Exception as exc:
            print(f"jev: server_error {type(exc).__name__} (status)", file=sys.stderr)
            return answer({"model": "jev", "code": "server_error"}, 500)

    def agents_ask_jev(body: AskBody, request: Request):
        """Ask jev about one second: one paid call to an external service in the USA."""
        return guarded("jev", body, request)

    def agents_laya_status():
        """Laya's column: configured or not, and its worker's state. Never starts it."""
        try:
            return answer(laya.status())
        except Exception as exc:
            print(f"laya: server_error {type(exc).__name__} (status)", file=sys.stderr)
            return answer({"model": "laya", "code": "server_error"}, 500)

    def agents_ask_laya(body: AskBody, request: Request):
        """Ask Laya about one second, twice (options forward, then reversed), in a
        worker on this machine. The first press starts the worker."""
        return guarded("laya", body, request)

    for path, method, endpoint in (("/api/agents/jev/status", "GET", agents_jev_status),
                                   ("/api/agents/jev", "POST", agents_ask_jev),
                                   ("/api/agents/laya/status", "GET", agents_laya_status),
                                   ("/api/agents/laya", "POST", agents_ask_laya)):
        app.router.add_api_route(path, endpoint, methods=[method],
                                 route_class_override=NoStoreRoute)
```

Edit 7, `app/server.py:42-44`. Replace

```python
separation is structural: there is no code path from this process to the bus.
Every HTTP route below is a GET.
"""
```

with

```python
separation is structural: there is no code path from this process to the bus.
Every route this module defines is a GET. Two POST routes, /api/agents/jev and
/api/agents/laya, are added by app.agent_api.install() only under
--simulation. Each asks a language model about one simulated second:
/api/agents/jev sends it to an external service in the USA; /api/agents/laya
sends it to a process on this machine, and nothing leaves the machine. Neither
has a path to the vehicle.
"""
```

Nothing else in `server.py` changes: not the `install(app)` call at `:303`, and not the `--simulation` banner at `:299-301`.

- [ ] **Step 4: Run to verify it passes**

Run:
```bash
$PY -c "from app import agent_api as A; print(A.TRACE_KEY)"
$PY -m app.test_agents AskRouteTests RouteTests.test_routes_only_under_simulation 2>&1 | grep -E "^(ERROR|FAIL):|^Ran|^OK|^FAILED"
```

Expected:
```
^runs[a-z0-9_]*/(?:[0-9]{1,3})/(?:[0-9]{1,2})$
Ran 12 tests in 1.4s
OK
```

The prototype read the same on three runs out of three. The routes' own stderr lines, such as `laya: busy (step 2)`, appear interleaved in the output; they are the design's one line per failure.

The prototype also showed that the two no-store tests can fail. With `route_class_override=APIRoute` in place of `NoStoreRoute`, they failed 30 times:
- 26 times with `AssertionError: None != 'no-store'`, once for each 422 subtest;
- 4 times with `Tuples differ: (405, 'POST', None) != (405, 'POST', 'no-store')` or its GET twin.

Then run the default suite. It takes about 4 minutes, so give the Bash tool a timeout of 600000.
```bash
$PY -m app.test_agents > "$SCRATCH/m3_t6_agents.txt" 2>&1; grep -E "== proof|^Ran |^OK|^FAILED|load_pair:" "$SCRATCH/m3_t6_agents.txt"
```

Expected:
- `Ran N tests`, where N is Task 5's count plus 11.
- `OK (skipped=S)`, where S is Task 5's count, unchanged.
- The `== proof PROVEN` line with unchanged damages.
- `PageTests.test_page_assets_ids` still passes under the `install(app)` defaults: a LayaBridge is built and nothing is spawned.

The sandbox clone carried Tasks 1-3 exactly as py-trace committed them, then Tasks 4-6. There the whole default suite read `Ran 107 tests` and `OK (skipped=14)`:
- 13 of those skips are the tests that need `runs*/`, which the clone does not have;
- one is `LayaRealTests`.

That full run is the check that no name in `test_agents.py` is defined twice. The repository has `runs*/`, so its skip count stays at Task 5's.

- [ ] **Step 5: Commit**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory}"
git branch --show-current            # must print JMF-2340550-sep17
git add app/agent_api.py app/server.py app/test_agents.py
$PY verify_docs.py > "$SCRATCH/m3_t6_verify.txt" 2>&1; tail -1 "$SCRATCH/m3_t6_verify.txt"
$PY -m app.test_replay > "$SCRATCH/m3_t6_replay.txt" 2>&1; tail -1 "$SCRATCH/m3_t6_replay.txt"
cat > "$SCRATCH/m3_t6_msg.txt" <<'EOF'
Agent replay M3 (5/7): the four routes, per-model locks; server.py names both POSTs

install(app, store=None, jev_send=None, laya=None) keeps the three GETs and
adds, only under --simulation (server.py calls it in that branch alone):
  GET  /api/agents/jev/status    {configured, source, vendor, model, hosted}; never the key
  POST /api/agents/jev           one paid call to an external service in the USA
  GET  /api/agents/laya/status   the bridge's status(); never starts the worker
  POST /api/agents/laya          two requests to the worker on this machine

Both POSTs take AskBody (strict, extra forbidden; trace matches the anchored
TRACE_KEY built from RUNS_NAME, SEED_TEXT and EP_TEXT; step 0..STEPS-1) and
run the guards in order:
- Origin must equal http:// + Host, with Host 127.0.0.1:N or localhost:N
  (403 foreign_origin);
- the trace must be finished in the store (409 no_trace), and the step must
  fall inside its sighted observations (409 step_not_computed);
- each model has its OWN non-blocking lock (409 busy), so a hung or failing
  jev call never makes Laya busy, and the reverse.
Failures are {model, code} (+status for vendor_status, +kind for
worker_error), with one stderr line and no state and no key; anything
unexpected is 500 server_error, never str(exc).

Every response of the four is no-store, FastAPI's own included: the routes
are NoStoreRoute, which adds the header to the 422 FastAPI sends for a body
that fails AskBody (before the handler, so before the Origin guard; no work
is done) and to the 405 for a wrong method, leaving both bodies as FastAPI
writes them.

Where the code departs from design 7.6: 'model' names the column in every
body and 'model_name' is the service's own name; NoStoreRoute (plan
addition); both status routes also return server_error on an exception.

server.py:43 now names both POSTs, one external and one local; agent_api's
module docstring, route comment and install() docstring match. The
--simulation banner is unchanged.

Tests (app/test_agents.py): RouteTests.test_routes_only_under_simulation
(spec 10) pins the seven routes, POST only for the two asks; AskRouteTests
(spec 16, 11 tests, a _JevCase so urlopen is unreachable) runs every check
for both models with Task 3's fake send and the fake Laya worker -- nothing
touches the network or the real Laya.

EOF
{ echo '$ python -m app.test_agents'; grep -E "== proof|^Ran |^OK|^FAILED|load_pair:" "$SCRATCH/m3_t6_agents.txt"
  echo; echo '$ python -m app.test_replay'; cat "$SCRATCH/m3_t6_replay.txt"
  echo; echo '$ python verify_docs.py'; tail -1 "$SCRATCH/m3_t6_verify.txt"
  echo; echo 'Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>'; } >> "$SCRATCH/m3_t6_msg.txt"
git commit -F "$SCRATCH/m3_t6_msg.txt" -- app/agent_api.py app/server.py app/test_agents.py
git log -1 --stat | tail -4
```

Expected, each read from the run:
- `verify_docs.py`'s last line reads `All N checks pass (M figure mentions scanned in the documents).`. The clone read `All 67 checks pass (846 figure mentions scanned in the documents).` with the Edit 3 wording above.
- `app.test_replay` ends with `49 of 49 checks pass`, including `PASS  M7: app.server imports and serves its three pages   16 routes` and `PASS  READ-ONLY: no write path to the vehicle exists in app/`, as measured on the clone.
- The commit shows `3 files changed`.

**Notes:**
- **Prototype run, 28 Sep.** The prototype was a clone with Tasks 1-3 as committed, with Tasks 4-6 applied and committed. The repository's `git status` stayed clean throughout. The prototype also served the real server from the clone, started as `-m app.server --simulation --http-port 8791` with no key and no LAYA_HOME, and answered as follows:
  - `GET /api/agents/jev/status`: 200 with no-store, `{"configured":false,"source":null,"vendor":"typesafe.ai","model":"jev-latest","hosted":"USA"}`.
  - `GET /api/agents/laya/status`: `{"configured":false,"source":null,"problem":"not_configured","worker":"stopped","device":null,"laya":null}`.
  - `POST /api/agents/jev` with the same Origin: 409 with no-store, `{"model":"jev","code":"no_trace"}`, logged as `jev: no_trace (step 3)`.
  - A string step: 422 with no-store.
  - `GET /api/agents/laya`: 405 with `allow: POST` and no-store.
  - No request could reach the network: with no trace computed, the trace guard refuses before the key is ever read.
- Recorded measurements:
  - `TRACE_KEY` evaluates to `^runs[a-z0-9_]*/(?:[0-9]{1,3})/(?:[0-9]{1,2})$`.
  - `runs_c4/05/1` resolves to the store key `('runs_c4', 5, 1)`.
  - `text/plain` and form bodies get 422, and so do the steps `"312"`, `true`, `1.0` and `719`.
  - The rebinding case (Host `evil.test:8000` with a matching Origin) gets 403.
- Neither default is used under test. No test calls `jev._send` or makes a real jev call, and there is no key on this machine.
- Two review fixes are applied in this task. The second `_FakeSend` class, which would have rebound Task 3's class and broken every `JevTests` case from this commit on, is gone: the critic offered this as an alternative to a rename, and the plan took it. The old import edit is also gone, because Task 3 already imports `contextlib` and `io`.


---

### Task 7: fe-pure: tap-unlock.mjs, model-panel.mjs (askState, createAnswers, rowView with held/changed, failureOf, errorText, statusLine, ERROR_CODES), every new string in both languages, and their node tests

**Files:**
- Create: `app/static/sim/tap-unlock.mjs`
- Create: `app/static/sim/model-panel.mjs`
- Create: `app/static/sim/tap-unlock.test.mjs`
- Create: `app/static/sim/model-panel.test.mjs`
- Modify: `app/static/sim/agents-strings.mjs`, in three places:
  - after `:20`, the header comment's last line;
  - `:138-140`, the end of the Arabic table (`  },` / blank / `  en: {`);
  - `:251-252`, the end of the English table (`  },` / `};`).
- Modify: `app/static/sim/agents-strings.test.mjs:254`. One test is appended after the last line.
- Test: `app/static/sim/tap-unlock.test.mjs`, `app/static/sim/model-panel.test.mjs`, `app/static/sim/agents-strings.test.mjs`

**Interfaces:**
- Consumes:
  - `app/static/sim/agent-view.mjs:252 laneStoppedAt(frames, lane) -> k | null`. It returns the first frame whose `cars[lane] == null`. Also `:32 ACTIONS`: spark, lambda, boost, fan, pump, in engine_env order.
  - `app/static/sim/i18n.mjs:488 t(lang, key, vars)`. A missing key returns the key itself, and an unfilled `{slot}` stays as written. Also `:35 STRINGS` and `:29 LANGS`.
  - `app/static/sim/agents-strings.mjs:24 AGENT_STRINGS {ar, en}` and `:264 mergeStrings`. The merge refuses a collision and a key in one language only. Also the existing key `agents.load.server_down`.
  - The JSON contracts of Task 6:
    - the 200 bodies, where `answers[qid] = {choice, level_phys, level_net, probabilities, chosen_p, options: [{key, level_phys}] x5}`, plus `answers_reversed` of the same shape for Laya only;
    - the error bodies `{model, code, status?, kind?}`;
    - the status bodies: jev `{configured, source, vendor, model, hosted}`, Laya `{configured, source, problem, worker, device, laya}`.
- Produces:
  - `app/static/sim/tap-unlock.mjs`: `export function createTapUnlock({ taps = 10, windowMs = 4000 } = {}) -> { tap(nowMs) -> boolean }`.
    - The taps live in a closure array, filtered to `nowMs - t <= windowMs`.
    - `tap` returns true on the tap that completes `taps` taps, then the count starts from zero.
    - The module uses no storage, no page access and no clock of its own.
  - `app/static/sim/model-panel.mjs` imports `./agent-view.mjs`, `./i18n.mjs` and `./agents-strings.mjs`. It exports:
    - `MODELS = ['jev', 'laya']` (frozen)
    - `QUESTION_IDS = ['spark_trim', 'lambda_trim', 'boost_ceiling', 'cooling_fan', 'coolant_pump']` (frozen; index i is `ACTIONS[i]`)
    - `ERROR_CODES` (frozen, 21 codes): `no_key, network, timeout, key_rejected, vendor_refused, request_rejected, rate_limited, overloaded, vendor_status, not_configured, not_found, start_failed, start_timeout, worker_error, worker_died, network_attempt, bad_answer, foreign_origin, no_trace, step_not_computed, busy`
    - `askState(view, k) -> { enabled, reason }`, where `view = { playing, waiting, done, frames, inFlight }` for ONE model. The checks run in this order:
      1. inFlight gives `'agents.models.reason.asking'`;
      2. not done with no frames gives `'agents.pause.empty'`;
      3. not done gives `'agents.models.reason.not_done'`;
      4. playing or waiting gives `'agents.models.reason.pause'`;
      5. k not an integer in `[0, frames.length)` gives `'agents.models.reason.not_done'`;
      6. `laneStoppedAt(frames, 0) <= k` gives `'agents.models.reason.stopped'`;
      7. otherwise `{ enabled: true, reason: null }`.
    - `createAnswers() -> { put(key, k, entry), get(key, k) -> entry | null, clear(), size }`. It is a Map keyed `` `${key}#${k}` ``. An entry is `{ body }` or `{ failure }`.
    - `rowView(answer, actionIndex) -> null | { id, choice, level, net, chosenP, bars: [{ key, level, p, chosen }] x5 in options order, reversed: { choice, level } | null, verdict: 'held' | 'changed' | null }`. It returns null for a missing action or an action with no `options` array.
    - `failureOf(httpStatus, body) -> { code, status, kind }`:
      - null or undefined httpStatus gives `{ code: 'server_down', status: null, kind: null }`;
      - `body.code` in ERROR_CODES gives `{ code, status: integer | null, kind: string | null }`;
      - anything else gives `{ code: 'server_error', status: httpStatus, kind: null }`.
    - `errorText(code, status, lang, kind = null) -> string`:
      - `'server_down'` gives `t('agents.models.no_answer_plain', { sentence: t('agents.load.server_down') })`;
      - a code not in ERROR_CODES gives the plain form with `t('agents.models.error.server_error', { status })`;
      - any other code gives `t('agents.models.no_answer', { code, sentence: t('agents.models.error.<code>', { status: status ?? '—', kind: kind ?? 'other' }) })`.
    - `statusLine(name, status, failure, inFlight, lang) -> string`:
      - a failure gives `errorText(...)`, and no status gives `'—'`;
      - jev gives `agents.models.jev.status.configured {source}` or `agents.models.jev.status.no_key`;
      - Laya takes the first that applies: problem `not_configured` or `not_found` gives its own key; worker `ready` gives `status.ready {device}`; worker `starting` or inFlight gives `status.starting`; worker `failed` gives `status.failed {code: problem}`; otherwise `status.stopped`.
  - `agents-strings.mjs AGENT_STRINGS` gains 63 keys in each language, so each table grows from 89 to 152 keys:
    - `agents.pause.empty`;
    - the 41 `agents.models.*` keys listed in the skeleton;
    - `agents.models.error.<code>` for each of the 21 ERROR_CODES, plus `agents.models.error.server_error ({status})`.

**Where this task follows the code rather than the design (one line each):**
- Design 7.2 names `errorText(code, status)`. The module is pure, so it takes the language, and `worker_error`'s sentence names its kind (7.9). The code is therefore `errorText(code, status, lang, kind = null)`.
- `failureOf` and `statusLine` are not in design 7.2's list. They are the skeleton's, so that the page's decisions on a failed request and on a status line are node-tested rather than living in `agents.mjs`.
- Before any episode, askState's reason is `'agents.pause.empty'`. Design 7.7's three reasons would say "wait for the episode to finish" before «احسب» was ever pressed.
- Design §9 describes the natural-end row as "userPaused false". askState's view has no `userPaused` at all, because the design's own predicate is `!playing && !waiting` (`agents.mjs:756`, syncPlayButton). The row is therefore playing false, waiting false, done true, k 718.
- `agents.models.reference` stops at its colon. Design 7.7 writes «… المُبصر {x} · الأعمى {y}», but M2 never names Phase D's blind car «الأعمى» alone (`agents.mjs:343` laneLabel). Task 8 puts the two lanes' values after the colon.
- Design 7.9 gives Arabic only for `vendor_status`, and that sentence is taken verbatim. The other 20 error sentences are this plan's, each saying what 7.9's "when" column says.
- `agents.models.jev.text` is main design §7's paragraph verbatim (`2026-09-26-agent-replay-design.md:499`), plus the numeric-precision sentence that M3 7.7 adds.
- Laya's two `problem` statuses are two literal `t()` calls, not one template key, so that `model-panel.test.mjs`'s key scan sees both keys.

**Environment.** Use Git Bash from the repository root. Tasks 1-6 must already be committed, although none of them touches `app/static`. Re-export in every new shell:

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
export SCRATCH="${SCRATCH:?set SCRATCH to the session scratchpad}"   # outside the repository, never %TEMP% itself
```

**The escape trap.** No line in this task needs a backslash-u escape:
- The en dash in `70–500 ms` (U+2013), the `§`, the `…` and the `·` are typed as ordinary characters.
- The Write and Edit tools decode only backslash-u. The regex escapes `\b`, `\s`, `\.` and `\w` in the new tests survive as typed; this was measured on the prototype, which has 6 and 9 literal `\b` and no control characters.
- `agents-strings.mjs` already carries 12 escapes as text (U+2066 ×1, U+2068 ×2, U+2069 ×3, U+200F ×2, U+2011 ×2, U+2212 ×2).
- `agents-strings.test.mjs` carries escape text too.
- **So never rewrite either file whole with Write.** Change them only through the anchored edits and the `>>` append below: none of their anchors and none of the inserted text contains a backslash-u.
- Step 13's byte check proves the counts.

**Nothing imports the two new modules until Task 8.** `agents.html`, `agents.mjs` and `app/test_agents.py` are therefore untouched, and the page is unchanged. No Python file changes, so `app.test_agents` is not re-run for this commit. `app.test_replay` is, as for every change under `app/`.

**Prototype record (28 Sep).** Steps 0-13 were replayed in order on a fresh copy of `app/static` plus `app/node_modules`, taken at d347ee5, in `C:\Users\admin\AppData\Local\Temp\claude\c--Users-admin-Documents-graduation-project-GRAD-project\3ceacbd0-c593-4033-801a-fae5729f96d9\scratchpad\plan_proto_m3\fe-pure\replay\`. Every output quoted below comes from that replay.
- The node glob went from 102 of 102 to 126 of 126.
- The `agents-strings.mjs` that the three edits produced was byte-identical to the prototype's.
- Ten mutants of `model-panel.mjs` were run: waiting ignored; stopped `<` instead of `<=`; the verdict inverted; no code in the error line; a non-integer status kept; in-flight read before ready; answers keyed by second only; in-flight not checked first; the bars reversed; and a no-op control. Each real mutant turned at least one test red, and the control stayed green.
- Four more changes each failed at least one test: a `Date.now` default in `tap-unlock.mjs`, a `fetch(` or a `.confidence` read added to `model-panel.mjs`, and a misspelt key.

- [ ] **Step 0: Pre-flight**

```bash
git branch --show-current
git log --oneline -1
git status --short -- app/static/sim
node --test "app/static/sim/*.test.mjs" 2>&1 | grep -E '^ℹ (tests|pass|fail)'
```

Expected output:
- the branch line reads `JMF-2340550-sep17`;
- the log line starts `Agent replay M3 (5/7)`;
- `git status` prints nothing for `app/static/sim`. Another session's files elsewhere may show; leave them alone;
- node prints `ℹ tests 102`, `ℹ pass 102` and `ℹ fail 0`. Record the count as BASE. Tasks 1-6 add no node test, so a different count means someone else changed `app/static/sim`: stop and find out who.

- [ ] **Step 1: Write the failing test (the strings)**

Write this block to `$SCRATCH/t7_strings_tail.mjs` with the Write tool. It starts with one empty line. Then append it to the test file:

```bash
cat "$SCRATCH/t7_strings_tail.mjs" >> app/static/sim/agents-strings.test.mjs
```

```js

// M3: the models panel (model-panel.mjs), behind the footer gesture. The
// Arabic honesty lines are design 7.7, 7.5b and 7.8 of
// docs/superpowers/specs/2026-09-28-agent-replay-m3-design.md, word for word,
// so they are pinned whole; the rest keep the clauses that carry a caveat.
const M3_KEYS = [
  'agents.pause.empty',
  'agents.models.heading', 'agents.models.not_thesis', 'agents.models.claim', 'agents.models.levels',
  'agents.models.jev.name', 'agents.models.jev.where', 'agents.models.jev.text',
  'agents.models.jev.status.configured', 'agents.models.jev.status.no_key',
  'agents.models.jev.ask', 'agents.models.jev.latency',
  'agents.models.laya.name', 'agents.models.laya.where', 'agents.models.laya.device_unknown',
  'agents.models.laya.text', 'agents.models.laya.check',
  'agents.models.laya.status.not_configured', 'agents.models.laya.status.not_found',
  'agents.models.laya.status.stopped', 'agents.models.laya.status.starting',
  'agents.models.laya.status.ready', 'agents.models.laya.status.failed',
  'agents.models.laya.ask', 'agents.models.laya.latency', 'agents.models.laya.first_load',
  'agents.models.reason.pause', 'agents.models.reason.not_done', 'agents.models.reason.stopped',
  'agents.models.reason.asking',
  'agents.models.ask_this', 'agents.models.reference', 'agents.models.choice', 'agents.models.chosen_p',
  'agents.models.reversed', 'agents.models.held', 'agents.models.changed',
  'agents.models.footer', 'agents.models.sent', 'agents.models.no_answer', 'agents.models.no_answer_plain',
  'agents.models.error.server_error',
];

test('the M3 strings keep their clauses', () => {
  const { AGENT_STRINGS } = api();
  for (const lang of LANGS) {
    const missing = M3_KEYS.filter(key => !Object.prototype.hasOwnProperty.call(AGENT_STRINGS[lang], key));
    assert.deepEqual(missing, [], `${lang}: M3 keys missing`);
  }
  const verbatim = {
    'agents.models.not_thesis': 'ليس جزءاً من الرسالة ولا من أي نتيجة. لا يقارن أي رقم هنا النموذجين بالوكيلين، ولا يُحسب أي فرق.',
    'agents.models.claim': 'الاحتمالات ادعاء النموذج نفسه، ولم تُختبر على هذه المهمة.',
    'agents.models.levels': 'كل نموذج يختار واحداً من خمسة مستويات لكل إجراء: للتعديلات الثلاثة الحدّان و"بلا تعديل" ونقطتان في المنتصف؛ وللمروحة والمضخة خمس قيم متساوية التباعد. المعروض هو اختيار النموذج نفسه، ولا يُحسب منه متوسط.',
    'agents.models.laya.check': 'نسأل لايا مرتين، والخيارات بترتيبين متعاكسين. إذا تغيّر اختياره بتغيير الترتيب وحده، فذلك الاختيار لا يأتي من حالة المحرك.',
    'agents.models.held': 'ثبت',
    'agents.models.changed': 'تغيّر بتغيير الترتيب',
    'agents.pause.empty': 'اضغط احسب، ثم أوقف العرض عند أي ثانية لترى ما قرّره كل وكيل',
  };
  for (const [key, text] of Object.entries(verbatim)) assert.equal(AGENT_STRINGS.ar[key], text, `ar ${key} is not the design's line`);
  const mustSay = {
    'agents.models.not_thesis': { en: [/not part of the thesis/i, /no difference is computed/] },
    'agents.models.claim': { en: [/model's own claim/, /untested/] },
    'agents.models.levels': { en: [/five levels/, /no average is computed/] },
    'agents.models.laya.check': { en: [/twice/, /opposite orders/, /does not come from the engine state/] },
    'agents.models.laya.text': {
      ar: [/لا يُرسل شيئاً خارجه/, /تجربة تشغيل، لا تقييم/, /README_AR\.md:31/],
      en: [/sends nothing out of it/, /A trial run, not an evaluation/, /README_AR\.md:31/],
    },
    'agents.models.jev.text': {
      ar: [/الولايات المتحدة/, /بلا حدّ زمني \(MCA §4\.1\)/, /تمنع تدريب/, /غير معروف/, /الدقة العددية/],
      en: [/USA/, /in perpetuity/, /\(MCA §4\.1\)/, /forbids training/, /unknown/, /numeric precision/],
    },
    'agents.models.jev.where': { ar: [/الولايات المتحدة/, /مدفوع/], en: [/USA/, /paid/] },
    'agents.models.jev.ask': { ar: [/مدفوع/], en: [/paid/] },
    'agents.models.jev.latency': { ar: [/مقيسة من هذا الجهاز/, /70–500 ms/], en: [/measured from this machine/, /70–500 ms/] },
    'agents.models.laya.where': { ar: [/على هذا الجهاز/], en: [/On this machine/] },
    'agents.models.footer': { ar: [/لم يُطبَّق/, /حد سرعة التغيير/], en: [/not applied/, /not rate-limited/] },
    'agents.models.error.vendor_status': { ar: [/HTTP \{status\}/, /رصيد/], en: [/HTTP \{status\}/, /credit/] },
    'agents.models.error.no_key': { ar: [/لم يُرسل شيء/], en: [/nothing was sent/] },
    'agents.pause.empty': { en: [/Compute/, /pause/] },
  };
  for (const [key, langs] of Object.entries(mustSay)) {
    for (const [lang, patterns] of Object.entries(langs)) {
      assert.ok(AGENT_STRINGS[lang][key], `${key} missing in ${lang}`);
      for (const p of patterns) assert.match(AGENT_STRINGS[lang][key], p, `${key} lost a clause in ${lang}`);
    }
  }
  // Design 7.7: the reference line names no car on its own and subtracts
  // nothing; the page puts the two lane values after its colon.
  for (const lang of LANGS) {
    const ref = AGENT_STRINGS[lang]['agents.models.reference'];
    assert.ok(ref.endsWith(':'), `${lang}: the reference line ends at its colon`);
    assert.doesNotMatch(ref, /[{][a-z0-9_]+[}]/i, `${lang}: the reference line takes no placeholder`);
  }
  // Design C9: the page never shows the model's confidence.
  for (const lang of LANGS) {
    for (const key of Object.keys(AGENT_STRINGS[lang]).filter(k => k.startsWith('agents.models.'))) {
      assert.doesNotMatch(AGENT_STRINGS[lang][key], /confidence|الثقة/i, `${lang} ${key} names the confidence`);
    }
  }
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `node --test app/static/sim/agents-strings.test.mjs 2>&1 | grep -E '^ℹ (tests|pass|fail)|^✖|AssertionError' | head`

Expected: FAIL. The output contains:
- `✖ the M3 strings keep their clauses`
- `AssertionError [ERR_ASSERTION]: ar: M3 keys missing`. The diff lists `'agents.pause.empty'` first.
- `ℹ tests 14`, `ℹ pass 13` and `ℹ fail 1`.

- [ ] **Step 3: Implement (the strings: three Edit-tool edits in `app/static/sim/agents-strings.mjs`)**

**Edit A, the header comment.**

`old_string` (line 20, unique):

```js
// written here as its escape; agents-strings.test.mjs pins every one of them.
```

`new_string`:

```js
// written here as its escape; agents-strings.test.mjs pins every one of them.
//
// M3 adds the models panel's strings (agents.models.*; model-panel.mjs) and
// the pause panel's empty line (agents.pause.empty), from sections 7.5b, 7.7,
// 7.8 and 7.9 of docs/superpowers/specs/2026-09-28-agent-replay-m3-design.md,
// verbatim where it gives them. None of them needs an escape: the en dash in
// '70–500 ms' and the section sign in 'MCA §4.1' are ordinary characters.
```

**Edit B, the end of the Arabic table.**

`old_string` (lines 138-140, unique):

```js
  },

  en: {
```

`new_string`. It STARTS WITH ONE EMPTY LINE, so a blank line separates the M2 block from the M3 block:

```js

    // --- added in M3: the pause panel's empty line (design 7.8), and the models
    // panel behind the footer gesture (model-panel.mjs; design 7.5b, 7.7, 7.9).
    // The honesty lines are design 7.7 word for word; one error sentence per
    // model-panel.mjs ERROR_CODES entry, plus the page's own server_error.
    'agents.pause.empty': 'اضغط احسب، ثم أوقف العرض عند أي ثانية لترى ما قرّره كل وكيل',
    'agents.models.heading': 'اسأل نموذجاً لغوياً عن هذه الثانية',
    'agents.models.not_thesis': 'ليس جزءاً من الرسالة ولا من أي نتيجة. لا يقارن أي رقم هنا النموذجين بالوكيلين، ولا يُحسب أي فرق.',
    'agents.models.claim': 'الاحتمالات ادعاء النموذج نفسه، ولم تُختبر على هذه المهمة.',
    'agents.models.levels': 'كل نموذج يختار واحداً من خمسة مستويات لكل إجراء: للتعديلات الثلاثة الحدّان و"بلا تعديل" ونقطتان في المنتصف؛ وللمروحة والمضخة خمس قيم متساوية التباعد. المعروض هو اختيار النموذج نفسه، ولا يُحسب منه متوسط.',
    'agents.models.jev.name': 'typesafe.ai · {model}',
    'agents.models.jev.where': 'خدمة خارجية في الولايات المتحدة · كل ضغطة استدعاء مدفوع واحد',
    'agents.models.jev.text': 'خدمة خارجية تعمل في الولايات المتحدة. ليست جزءاً من الرسالة ولا من أي نتيجة، ولا يقارنها أي رقم بالوكلاء. هذه الصفحة لا تحفظ شيئاً؛ لكن اتفاقية المورّد تسمح له بالاحتفاظ بما يُرسل لاستخراج بيانات القياس بلا حدّ زمني (MCA §4.1). تُرسَل إليه حالة هذه الحلقة المحاكاة فقط، لا بيانات السيارة المسجّلة. كل ضغطة استدعاء واحد مدفوع. اتفاقية المورّد تمنع تدريب أي نموذج على تقليد إجاباته. شروط موقع المورّد موجّهة لزوّار الولايات المتحدة؛ هل الاستخدام من السعودية مسموح؟ غير معروف. ويقول المورّد إن النموذج ضعيف في الدقة العددية.',
    'agents.models.jev.status.configured': 'مفتاح مُعَدّ ({source})',
    'agents.models.jev.status.no_key': 'لا مفتاح؛ لن يُرسل شيء',
    'agents.models.jev.ask': 'اسأل jev عن هذه الثانية (استدعاء مدفوع واحد)',
    'agents.models.jev.latency': '{ms} ms، مقيسة من هذا الجهاز (ادعاء المورّد 70–500 ms)',
    'agents.models.laya.name': 'Laya · {model} · laya {version}',
    'agents.models.laya.where': 'على هذا الجهاز ({device}) · مجاني، بلا مفتاح',
    'agents.models.laya.device_unknown': 'لم يُحمَّل بعد',
    'agents.models.laya.text': 'يعمل على هذا الجهاز ولا يُرسل شيئاً خارجه. تجربة تشغيل، لا تقييم. يقول ملف لايا نفسه إن نتيجة مثال لا تعني أنه مناسب للتحكم بالمحرك (README_AR.md:31). رخصة Apache 2.0.',
    'agents.models.laya.check': 'نسأل لايا مرتين، والخيارات بترتيبين متعاكسين. إذا تغيّر اختياره بتغيير الترتيب وحده، فذلك الاختيار لا يأتي من حالة المحرك.',
    'agents.models.laya.status.not_configured': 'غير مُعَدّ: LAYA_HOME',
    'agents.models.laya.status.not_found': 'لم يُعثر على لايا في LAYA_HOME، أو يقع داخل المستودع',
    'agents.models.laya.status.stopped': 'يُحمَّل عند أول سؤال',
    'agents.models.laya.status.starting': 'يُحمَّل على هذا الجهاز لأول مرة…',
    'agents.models.laya.status.ready': 'محمَّل على {device} حتى يُغلق الخادم',
    'agents.models.laya.status.failed': 'تعذّر التشغيل: {code}',
    'agents.models.laya.ask': 'اسأل لايا عن هذه الثانية (على هذا الجهاز)',
    'agents.models.laya.latency': '{ms} ms على {device}',
    'agents.models.laya.first_load': 'التحميل الأول {s} ث',
    'agents.models.reason.pause': 'أوقف العرض أولاً',
    'agents.models.reason.not_done': 'انتظر حتى تكتمل الحلقة',
    'agents.models.reason.stopped': 'توقفت محاكاة المُبصر قبل هذه الثانية',
    'agents.models.reason.asking': 'يُسأل الآن…',
    'agents.models.ask_this': 'اسأل عن هذه الثانية',
    'agents.models.reference': 'طبّق الوكيلان في هذه الثانية:',
    'agents.models.choice': 'اختيار النموذج: {level} (الشبكة {net})',
    'agents.models.chosen_p': 'احتمال الخيار المختار {p}',
    'agents.models.reversed': 'بالترتيب المعكوس: {level}',
    'agents.models.held': 'ثبت',
    'agents.models.changed': 'تغيّر بتغيير الترتيب',
    'agents.models.footer': 'هدف لثانية واحدة: لم يُطبَّق ولم يُقيَّد بحد سرعة التغيير',
    'agents.models.sent': 'ما الذي أُرسل',
    'agents.models.no_answer': 'لا جواب — {code}: {sentence}',
    'agents.models.no_answer_plain': 'لا جواب — {sentence}',
    'agents.models.error.no_key': 'لا مفتاح، فلم يُرسل شيء.',
    'agents.models.error.network': 'تعذّر الوصول إلى الخدمة من هذا الجهاز.',
    'agents.models.error.timeout': 'انتهت المهلة دون جواب.',
    'agents.models.error.key_rejected': 'رفضت الخدمة المفتاح.',
    'agents.models.error.vendor_refused': 'رفضت الخدمة الطلب؛ قد لا يُسمح بالوصول من هذا الموقع.',
    'agents.models.error.request_rejected': 'رفضت الخدمة شكل الطلب: خلل في هذه الصفحة.',
    'agents.models.error.rate_limited': 'طلبات كثيرة؛ اسأل مرة أخرى بعد لحظة.',
    'agents.models.error.overloaded': 'الخدمة مشغولة؛ اسأل مرة أخرى بعد لحظة.',
    'agents.models.error.vendor_status': 'رفضت الخدمة الطلب (HTTP {status}). قد يعني ذلك أن الحساب بلا رصيد.',
    'agents.models.error.not_configured': 'لم يُعَدّ LAYA_HOME، فلم يُشغَّل شيء.',
    'agents.models.error.not_found': 'لم يُعثر على بايثون لايا أو مجلد نموذجه، أو يقعان داخل المستودع.',
    'agents.models.error.start_failed': 'خرج عامل لايا قبل أن يجهز.',
    'agents.models.error.start_timeout': 'لم يجهز عامل لايا خلال 90 ث، فأُوقف.',
    'agents.models.error.worker_error': 'أبلغ عامل لايا عن خطأ ({kind}).',
    'agents.models.error.worker_died': 'توقف عامل لايا في منتصف الطلب.',
    'agents.models.error.network_attempt': 'سجّل الحارس محاولة اتصال بالشبكة، فأُسقط الجواب وأُوقف العامل.',
    'agents.models.error.bad_answer': 'جاء جواب لا يمكن تحويله إلى إجراء، فلم يُعرض شيء.',
    'agents.models.error.foreign_origin': 'رُفض الطلب لأنه لم يأتِ من هذه الصفحة.',
    'agents.models.error.no_trace': 'هذه الحلقة لم تعد محفوظة في الخادم؛ اضغط احسب ثم اسأل.',
    'agents.models.error.step_not_computed': 'هذه الثانية لم تُحسب للمُبصر.',
    'agents.models.error.busy': 'سؤال آخر لهذا النموذج جارٍ الآن.',
    'agents.models.error.server_error': 'خطأ في الخادم (HTTP {status})',
  },

  en: {
```

**Edit C, the end of the English table.**

`old_string` (lines 251-252, which become 322-323 after Edits A and B; unique):

```js
  },
};
```

`new_string`. It STARTS WITH ONE EMPTY LINE:

```js

    // --- added in M3: the pause panel's empty line (design 7.8), and the models
    // panel behind the footer gesture (model-panel.mjs; design 7.5b, 7.7, 7.9).
    // The honesty lines are design 7.7 word for word; one error sentence per
    // model-panel.mjs ERROR_CODES entry, plus the page's own server_error.
    'agents.pause.empty': 'Press Compute, then pause at any second to see what each agent decided',
    'agents.models.heading': 'Ask a language model about this second',
    'agents.models.not_thesis': 'Not part of the thesis or of any result. No figure here compares the models with the agents, and no difference is computed.',
    'agents.models.claim': "The probabilities are the model's own claim, untested on this task.",
    'agents.models.levels': 'Each model picks one of five levels per action: for the three trims, both limits, "no change" and two midpoints; for the fan and the pump, five evenly spaced duties. What is shown is the model\'s own choice; no average is computed from it.',
    'agents.models.jev.name': 'typesafe.ai · {model}',
    'agents.models.jev.where': 'External service in the USA · each press is one paid call',
    'agents.models.jev.text': "An external service in the USA. It is not part of the thesis or of any result, and no figure compares it with the agents. This page saves nothing, but the vendor's agreement lets it keep what is sent, in perpetuity, to derive telemetry (MCA §4.1). It receives only this simulated episode's state, never the recorded car data. Each press is one paid call. The vendor's agreement forbids training any model to imitate its answers. The vendor's site terms are aimed at US visitors; whether use from Saudi Arabia is permitted is unknown. The vendor says the model is weak at numeric precision.",
    'agents.models.jev.status.configured': 'Key configured ({source})',
    'agents.models.jev.status.no_key': 'No key; nothing will be sent',
    'agents.models.jev.ask': 'Ask jev about this second (one paid call)',
    'agents.models.jev.latency': '{ms} ms, measured from this machine (vendor claim 70–500 ms)',
    'agents.models.laya.name': 'Laya · {model} · laya {version}',
    'agents.models.laya.where': 'On this machine ({device}) · free, no key',
    'agents.models.laya.device_unknown': 'not loaded yet',
    'agents.models.laya.text': "Runs on this machine and sends nothing out of it. A trial run, not an evaluation. Laya's own file says an example result does not mean it suits engine control (README_AR.md:31). Apache 2.0 licence.",
    'agents.models.laya.check': 'We ask Laya twice, with the options in opposite orders. If its choice changes when only the order changes, that choice does not come from the engine state.',
    'agents.models.laya.status.not_configured': 'Not configured: LAYA_HOME',
    'agents.models.laya.status.not_found': 'Laya was not found at LAYA_HOME, or it lies inside the repository',
    'agents.models.laya.status.stopped': 'Loads on the first question',
    'agents.models.laya.status.starting': 'Loading on this machine for the first time…',
    'agents.models.laya.status.ready': 'Loaded on {device} until the server stops',
    'agents.models.laya.status.failed': 'Could not start: {code}',
    'agents.models.laya.ask': 'Ask Laya about this second (on this machine)',
    'agents.models.laya.latency': '{ms} ms on {device}',
    'agents.models.laya.first_load': 'first load {s} s',
    'agents.models.reason.pause': 'Pause first',
    'agents.models.reason.not_done': 'Wait for the episode to finish',
    'agents.models.reason.stopped': "The sighted car's simulation stopped before this second",
    'agents.models.reason.asking': 'Asking now…',
    'agents.models.ask_this': 'Ask about this second',
    'agents.models.reference': 'The agents applied in this second:',
    'agents.models.choice': "The model's choice: {level} (network {net})",
    'agents.models.chosen_p': 'Probability of the chosen option {p}',
    'agents.models.reversed': 'With the options reversed: {level}',
    'agents.models.held': 'held',
    'agents.models.changed': 'changed with the order',
    'agents.models.footer': 'A one-second target: not applied, not rate-limited',
    'agents.models.sent': 'What was sent',
    'agents.models.no_answer': 'No answer — {code}: {sentence}',
    'agents.models.no_answer_plain': 'No answer — {sentence}',
    'agents.models.error.no_key': 'No key, so nothing was sent.',
    'agents.models.error.network': 'The service could not be reached from this machine.',
    'agents.models.error.timeout': 'The time limit passed with no answer.',
    'agents.models.error.key_rejected': 'The service rejected the key.',
    'agents.models.error.vendor_refused': 'The service refused the request; access from this location may not be permitted.',
    'agents.models.error.request_rejected': "The service rejected the request's shape: a bug on this page.",
    'agents.models.error.rate_limited': 'Too many requests; ask again in a moment.',
    'agents.models.error.overloaded': 'The service is overloaded; ask again in a moment.',
    'agents.models.error.vendor_status': 'The service refused the request (HTTP {status}). This may mean the account has no credit.',
    'agents.models.error.not_configured': 'LAYA_HOME is not set, so nothing was started.',
    'agents.models.error.not_found': "Laya's python or its model folder was not found, or lies inside the repository.",
    'agents.models.error.start_failed': "Laya's worker exited before it was ready.",
    'agents.models.error.start_timeout': "Laya's worker was not ready within 90 s and was stopped.",
    'agents.models.error.worker_error': "Laya's worker reported an error ({kind}).",
    'agents.models.error.worker_died': "Laya's worker stopped in the middle of the request.",
    'agents.models.error.network_attempt': 'The guard counted a network attempt, so the answer was dropped and the worker stopped.',
    'agents.models.error.bad_answer': 'An answer came back that cannot become an action, so nothing is shown.',
    'agents.models.error.foreign_origin': 'The request was refused because it did not come from this page.',
    'agents.models.error.no_trace': 'This episode is no longer held by the server; press Compute, then ask.',
    'agents.models.error.step_not_computed': 'This second was not computed for the sighted car.',
    'agents.models.error.busy': 'Another question to this model is running now.',
    'agents.models.error.server_error': 'Server error (HTTP {status})',
  },
};
```

- [ ] **Step 4: Run to verify it passes (the strings)**

Run: `node --test app/static/sim/agents-strings.test.mjs 2>&1 | grep -E '^ℹ (tests|pass|fail)|^✖'`

Expected: `ℹ tests 14`, `ℹ pass 14` and `ℹ fail 0`, with no `✖` line. The existing tests re-check the new keys on every run:
- 'the merge adds …' checks that the lab strings are unchanged and that `missingKeys()` is `[]`;
- 'no string says preview helps …' checks the «المنمذَج» rule;
- 'every key fills the same {placeholders} …';
- 'the pair row's minus …' checks that there is no literal U+2066/2069/200F/2011/2212/202F.

- [ ] **Step 5: Write the failing test (the gesture)**

Create `app/static/sim/tap-unlock.test.mjs` with the Write tool:

```js
// The hidden gesture of /agents (M3 design 7.7): ten taps within 4000 ms on
// the footer label '02 — AGENTS' show the models panel. The counter is pure
// and lives in a closure, so a reload forgets the unlock; the source must use
// no browser storage at all.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createTapUnlock } from './tap-unlock.mjs';

// n taps spread evenly from 0 to spanMs; returns what each tap() answered.
function taps(gesture, n, spanMs, start = 0) {
  return Array.from({ length: n }, (_, i) => gesture.tap(start + (n > 1 ? i * spanMs / (n - 1) : 0)));
}

test('ten taps spread over 4000 ms unlock, on the tenth only', () => {
  assert.deepEqual(taps(createTapUnlock({ taps: 10, windowMs: 4000 }), 10, 4000), [...Array(9).fill(false), true]);
});

test('nine taps do not unlock', () => {
  assert.deepEqual(taps(createTapUnlock({ taps: 10, windowMs: 4000 }), 9, 900), Array(9).fill(false));
});

test('ten taps over 4001 ms do not unlock: the first has left the window', () => {
  assert.deepEqual(taps(createTapUnlock({ taps: 10, windowMs: 4000 }), 10, 4001), Array(10).fill(false));
});

test('the defaults are ten taps in 4000 ms', () => {
  assert.equal(taps(createTapUnlock(), 10, 4000).at(-1), true);
  assert.equal(taps(createTapUnlock(), 10, 4001).at(-1), false);
  assert.equal(taps(createTapUnlock(), 9, 100).at(-1), false);
});

test('after an unlock the count starts again from zero', () => {
  const gesture = createTapUnlock({ taps: 10, windowMs: 4000 });
  assert.equal(taps(gesture, 10, 900).at(-1), true);
  // The tenth tap reset the count: one more tap is one tap, not eleven.
  assert.equal(gesture.tap(1000), false);
  assert.deepEqual(taps(gesture, 9, 900, 1100), [...Array(8).fill(false), true]);
});

test('the gesture keeps nothing outside its closure', () => {
  const src = readFileSync(new URL('./tap-unlock.mjs', import.meta.url), 'utf8');
  assert.doesNotMatch(src, /localStorage|sessionStorage|indexedDB|cookie/);
  // No page access and no clock of its own: agents.mjs passes each tap's time.
  assert.doesNotMatch(src, /\bfetch\s*\(|\bdocument\.|\bwindow\.|\bglobalThis\b|\bDate\.now\b|\bperformance\.now\b/);
});
```

- [ ] **Step 6: Run it to verify it fails**

Run: `node --test app/static/sim/tap-unlock.test.mjs 2>&1 | grep -E '^ℹ (tests|pass|fail)|^Error|^✖' | head -5`

Expected: FAIL, with:
- `Error [ERR_MODULE_NOT_FOUND]: Cannot find module '…\app\static\sim\tap-unlock.mjs' imported from …\app\static\sim\tap-unlock.test.mjs`
- `✖ app\static\sim\tap-unlock.test.mjs`
- `ℹ tests 1`, `ℹ pass 0` and `ℹ fail 1`.

- [ ] **Step 7: Implement (the gesture)**

Create `app/static/sim/tap-unlock.mjs`. Keep the words of the storage and page patterns out of its comments, because the test reads this source:

```js
// The hidden gesture of /agents (M3 design 7.7): ten taps within four seconds
// on the footer label '02 — AGENTS' show the models panel.
//
// PURE: a counter and nothing else. agents.mjs passes each click's time in
// milliseconds; this module never reads a clock of its own. The taps live in
// this closure only, so a reload forgets them and the unlock, and nothing is
// kept in any browser store (tap-unlock.test.mjs reads this source to check).
// The gesture hides the panel; it protects nothing.
export function createTapUnlock({ taps = 10, windowMs = 4000 } = {}) {
  let times = [];
  return {
    // True on the tap that completes `taps` taps within `windowMs`; the count
    // then starts again from zero.
    tap(nowMs) {
      times.push(nowMs);
      times = times.filter(t => nowMs - t <= windowMs);
      if (times.length < taps) return false;
      times = [];
      return true;
    },
  };
}
```

- [ ] **Step 8: Run to verify it passes (the gesture)**

Run: `node --test app/static/sim/tap-unlock.test.mjs 2>&1 | grep -E '^ℹ (tests|pass|fail)|^✖'`

Expected: `ℹ tests 6`, `ℹ pass 6` and `ℹ fail 0`, with no `✖` line.

- [ ] **Step 9: Write the failing test (the panel logic)**

Create `app/static/sim/model-panel.test.mjs` with the Write tool:

```js
// The models panel's pure logic (M3 design 7.5b, 7.7 and 7.9): when each
// model's button may be pressed, which answer each second keeps, how an
// answer becomes five rows with the order check, and what an error says.
// agents.mjs only wires these to the page, so every decision is pinned here.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { STRINGS, LANGS } from './i18n.mjs';
import { ACTIONS } from './agent-view.mjs';
import {
  MODELS, QUESTION_IDS, ERROR_CODES, askState, createAnswers, rowView, failureOf, errorText, statusLine,
} from './model-panel.mjs';

const SRC = readFileSync(new URL('./model-panel.mjs', import.meta.url), 'utf8');
const has = key => LANGS.every(lang => Object.prototype.hasOwnProperty.call(STRINGS[lang], key));
const UNFILLED = /[{][a-z0-9_]+[}]/i;

// Frames as the episode route serves them: { k, cars: [sighted, blind] }.
const frames = n => Array.from({ length: n }, (_, k) => ({ k, cars: [{ k }, { k }] }));
// A finished 719-step episode, stopped (the play button shows play), nothing in flight.
const FULL = frames(719);
const view = over => ({ playing: false, waiting: false, done: true, frames: FULL, inFlight: false, ...over });
// The sighted lane (cars[0]) goes null from step `at` on, as agents.mjs carOf reads it.
function sightedStopsAt(n, at) {
  const f = frames(n);
  for (let k = at; k < n; k++) f[k].cars[0] = null;
  return f;
}

// The shape app/model_questions.py to_action returns for one question
// (Task 2), with the keys and levels of design section 7: five options in the
// design's order, each with its physical level, and five probabilities.
const KEYS = {
  spark_trim: ['retard 8 deg', 'retard 4 deg', 'no change', 'advance 2 deg', 'advance 4 deg'],
  lambda_trim: ['richer by 0.15', 'richer by 0.075', 'no change', 'leaner by 0.03', 'leaner by 0.06'],
  boost_ceiling: ['ceiling -40 kPa', 'ceiling -20 kPa', 'no change', 'ceiling +7.5 kPa', 'ceiling +15 kPa'],
  cooling_fan: ['fan 0 %', 'fan 25 %', 'fan 50 %', 'fan 75 %', 'fan 100 %'],
  coolant_pump: ['pump 30 %', 'pump 47.5 %', 'pump 65 %', 'pump 82.5 %', 'pump 100 %'],
};
const LEVELS = {
  spark_trim: [-8, -4, 0, 2, 4],
  lambda_trim: [-0.15, -0.075, 0, 0.03, 0.06],
  boost_ceiling: [-40, -20, 0, 7.5, 15],
  cooling_fan: [0, 0.25, 0.5, 0.75, 1],
  coolant_pump: [0.3, 0.475, 0.65, 0.825, 1],
};
const LO = [-8, -0.15, -40, 0, 0.3];
const HI = [4, 0.06, 15, 1, 1];
const P = [0.05, 0.6, 0.2, 0.1, 0.05];
function actionOf(id, j) {
  const i = QUESTION_IDS.indexOf(id);
  const key = KEYS[id][j];
  const level = LEVELS[id][j];
  return {
    choice: key,
    level_phys: level,
    level_net: 2 * (level - LO[i]) / (HI[i] - LO[i]) - 1,
    probabilities: Object.fromEntries(KEYS[id].map((k, m) => [k, P[m]])),
    chosen_p: P[j],
    options: KEYS[id].map((k, m) => ({ key: k, level_phys: LEVELS[id][m] })),
  };
}
// choices: the option index each question picked, in QUESTION_IDS order.
const answersOf = choices => Object.fromEntries(QUESTION_IDS.map((id, i) => [id, actionOf(id, choices[i])]));

test('five questions, one per action, in ACTIONS order; two models', () => {
  assert.deepEqual([...MODELS], ['jev', 'laya']);
  assert.equal(QUESTION_IDS.length, 5);
  assert.equal(ACTIONS.length, 5);
  assert.deepEqual(ACTIONS.map((a, i) => [a.key, QUESTION_IDS[i]]), [
    ['spark', 'spark_trim'], ['lambda', 'lambda_trim'], ['boost', 'boost_ceiling'],
    ['fan', 'cooling_fan'], ['pump', 'coolant_pump'],
  ]);
});

test('askState: a finished, stopped episode can be asked about, and each condition alone disables it', () => {
  assert.deepEqual(askState(view({}), 312), { enabled: true, reason: null });
  assert.deepEqual(askState(view({ playing: true }), 312), { enabled: false, reason: 'agents.models.reason.pause' });
  assert.deepEqual(askState(view({ waiting: true }), 312), { enabled: false, reason: 'agents.models.reason.pause' });
  assert.deepEqual(askState(view({ done: false }), 312), { enabled: false, reason: 'agents.models.reason.not_done' });
  assert.deepEqual(askState(view({ inFlight: true }), 312), { enabled: false, reason: 'agents.models.reason.asking' });
  // The sighted lane stopped AT k, or before it: frame k has no sighted car.
  assert.deepEqual(askState(view({ frames: sightedStopsAt(719, 312) }), 312),
    { enabled: false, reason: 'agents.models.reason.stopped' });
  assert.deepEqual(askState(view({ frames: sightedStopsAt(719, 311) }), 312),
    { enabled: false, reason: 'agents.models.reason.stopped' });
  // Stopped one step AFTER k: frame k still has its sighted car.
  assert.deepEqual(askState(view({ frames: sightedStopsAt(719, 313) }), 312), { enabled: true, reason: null });
});

test('askState: the natural end and a never-played episode are enabled with no seek', () => {
  // Played to its end: the clock stops by itself, userPaused stays false
  // (agent-view.mjs:185), and the play button shows play (design C10).
  assert.deepEqual(askState(view({}), 718), { enabled: true, reason: null });
  // Finished and never played: the clock sits at second 0.
  assert.deepEqual(askState(view({}), 0), { enabled: true, reason: null });
});

test('askState: before any episode the reason says what to do; a second outside the episode is refused', () => {
  // state after load and after compute(): no frames, not done, lastK -2.
  assert.deepEqual(askState({ playing: false, waiting: false, done: false, frames: [], inFlight: false }, -2),
    { enabled: false, reason: 'agents.pause.empty' });
  assert.deepEqual(askState(view({}), -2), { enabled: false, reason: 'agents.models.reason.not_done' });
  assert.deepEqual(askState(view({}), 719), { enabled: false, reason: 'agents.models.reason.not_done' });
  assert.deepEqual(askState(view({}), 1.5), { enabled: false, reason: 'agents.models.reason.not_done' });
});

test('askState: one model in flight leaves the other enabled', () => {
  const jev = view({ inFlight: true });
  const laya = view({ inFlight: false });
  assert.equal(askState(jev, 312).enabled, false);
  assert.equal(askState(laya, 312).enabled, true);
});

test('every reason askState gives is a string in both languages', () => {
  const reasons = ['agents.pause.empty', 'agents.models.reason.asking', 'agents.models.reason.not_done',
    'agents.models.reason.pause', 'agents.models.reason.stopped'];
  assert.deepEqual(reasons.filter(k => !has(k)), []);
});

test('createAnswers keeps one answer per (episode, second), in memory, until cleared', () => {
  const answers = createAnswers();
  assert.equal(answers.size, 0);
  answers.put('runs_c4/5/1', 3, { body: 'a' });
  answers.put('runs_c4/5/1', 4, { body: 'b' });
  assert.deepEqual(answers.get('runs_c4/5/1', 3), { body: 'a' }, 'the answer at k1 survives one at k2');
  assert.deepEqual(answers.get('runs_c4/5/1', 4), { body: 'b' });
  assert.equal(answers.get('runs_c4/5/2', 3), null, 'another episode at the same second has no answer');
  assert.equal(answers.get('runs_c4/5/1', 5), null);
  answers.put('runs_c4/5/1', 3, { failure: { code: 'busy', status: null, kind: null } });
  assert.deepEqual(answers.get('runs_c4/5/1', 3), { failure: { code: 'busy', status: null, kind: null } },
    'a second press at the same second replaces the first');
  assert.equal(answers.size, 2);
  answers.clear();
  assert.equal(answers.size, 0);
  assert.equal(answers.get('runs_c4/5/1', 4), null);
});

test('rowView: the choice, five bars in the options order, and the order check', () => {
  // Laya: spark changed with the order (1 -> 3); lambda held (1 -> 1).
  const body = { answers: answersOf([1, 1, 2, 4, 0]), answers_reversed: answersOf([3, 1, 2, 4, 0]) };
  const spark = rowView(body, 0);
  assert.equal(spark.id, 'spark_trim');
  assert.equal(spark.choice, 'retard 4 deg');
  assert.equal(spark.level, -4);
  assert.equal(spark.net, 2 * (-4 + 8) / 12 - 1);
  assert.equal(spark.chosenP, 0.6);
  assert.deepEqual(spark.bars.map(b => b.key), KEYS.spark_trim);
  assert.deepEqual(spark.bars.map(b => b.level), LEVELS.spark_trim);
  assert.deepEqual(spark.bars.map(b => b.p), P);
  assert.deepEqual(spark.bars.map(b => b.chosen), [false, true, false, false, false]);
  assert.deepEqual(spark.reversed, { choice: 'advance 2 deg', level: 2 });
  assert.equal(spark.verdict, 'changed');
  const lambda = rowView(body, 1);
  assert.equal(lambda.id, 'lambda_trim');
  assert.deepEqual(lambda.reversed, { choice: 'richer by 0.075', level: -0.075 });
  assert.equal(lambda.verdict, 'held');
  assert.deepEqual(QUESTION_IDS.map((_, i) => rowView(body, i).verdict), ['changed', 'held', 'held', 'held', 'held']);
});

test('rowView: jev has no order check; a missing action gives no row', () => {
  const jev = rowView({ answers: answersOf([2, 2, 2, 2, 2]) }, 4);
  assert.equal(jev.id, 'coolant_pump');
  assert.equal(jev.choice, 'pump 65 %');
  assert.equal(jev.reversed, null);
  assert.equal(jev.verdict, null);
  assert.equal(jev.bars.filter(b => b.chosen).length, 1);
  const partial = answersOf([2, 2, 2, 2, 2]);
  delete partial.boost_ceiling;
  assert.equal(rowView({ answers: partial }, 2), null);
  assert.equal(rowView({ answers: { spark_trim: { choice: 'no change' } } }, 0), null, 'no options, no bars');
  assert.equal(rowView(null, 0), null);
  assert.equal(rowView({ answers: answersOf([2, 2, 2, 2, 2]) }, 5), null);
});

test('every error code has its sentence in both languages', () => {
  assert.equal(ERROR_CODES.length, 21);
  assert.equal(new Set(ERROR_CODES).size, 21);
  assert.deepEqual(ERROR_CODES.filter(code => !has(`agents.models.error.${code}`)), []);
  assert.ok(has('agents.models.error.server_error'));
});

test('failureOf: a known code keeps only its code, integer status and kind; anything else is a server error', () => {
  assert.deepEqual(failureOf(502, { model: 'jev', code: 'vendor_status', status: 402 }),
    { code: 'vendor_status', status: 402, kind: null });
  assert.deepEqual(failureOf(502, { model: 'laya', code: 'worker_error', kind: 'ValueError' }),
    { code: 'worker_error', status: null, kind: 'ValueError' });
  assert.deepEqual(failureOf(503, { model: 'jev', code: 'no_key' }), { code: 'no_key', status: null, kind: null });
  assert.deepEqual(failureOf(502, { code: 'vendor_status', status: '402' }), { code: 'vendor_status', status: null, kind: null });
  assert.deepEqual(failureOf(500, { detail: 'Internal Server Error' }), { code: 'server_error', status: 500, kind: null });
  assert.deepEqual(failureOf(422, { detail: [{ loc: ['body', 'step'] }] }), { code: 'server_error', status: 422, kind: null });
  assert.deepEqual(failureOf(502, { code: 'made_up' }), { code: 'server_error', status: 502, kind: null });
  // The server's own 500 (agent_api's server_error) is not a model's code: HTTP 500.
  assert.deepEqual(failureOf(500, { model: 'laya', code: 'server_error' }), { code: 'server_error', status: 500, kind: null });
  assert.deepEqual(failureOf(502, null), { code: 'server_error', status: 502, kind: null });
  assert.deepEqual(failureOf(null, null), { code: 'server_down', status: null, kind: null });
  assert.deepEqual(failureOf(undefined, undefined), { code: 'server_down', status: null, kind: null });
});

test('errorText: «لا جواب — code: sentence», credit named on vendor_status, nothing substituted', () => {
  const credit = failureOf(502, { model: 'jev', code: 'vendor_status', status: 402 });
  assert.equal(errorText(credit.code, credit.status, 'ar', credit.kind),
    'لا جواب — vendor_status: رفضت الخدمة الطلب (HTTP 402). قد يعني ذلك أن الحساب بلا رصيد.');
  assert.equal(errorText(credit.code, credit.status, 'en', credit.kind),
    'No answer — vendor_status: The service refused the request (HTTP 402). This may mean the account has no credit.');
  assert.equal(errorText('no_key', null, 'ar'), 'لا جواب — no_key: لا مفتاح، فلم يُرسل شيء.');
  assert.match(errorText('worker_error', null, 'en', 'OutOfMemoryError'), /^No answer — worker_error: .*\(OutOfMemoryError\)/);
  assert.match(errorText('worker_error', null, 'en', null), /\(other\)/);
});

test('errorText: an unknown code is a server error with its HTTP status; a failed fetch is the server-down sentence', () => {
  const odd = failureOf(500, { detail: 'x' });
  assert.equal(errorText(odd.code, odd.status, 'ar', odd.kind), 'لا جواب — خطأ في الخادم (HTTP 500)');
  assert.equal(errorText(odd.code, odd.status, 'en', odd.kind), 'No answer — Server error (HTTP 500)');
  const down = failureOf(null, null);
  assert.equal(errorText(down.code, down.status, 'ar', down.kind), `لا جواب — ${STRINGS.ar['agents.load.server_down']}`);
  assert.equal(errorText(down.code, down.status, 'en', down.kind), `No answer — ${STRINGS.en['agents.load.server_down']}`);
});

test('no error text leaves a {placeholder} unfilled, whatever the status and kind', () => {
  for (const lang of LANGS) {
    for (const code of [...ERROR_CODES, 'server_error', 'server_down', 'made_up']) {
      for (const [status, kind] of [[402, 'ValueError'], [null, null]]) {
        const text = errorText(code, status, lang, kind);
        assert.doesNotMatch(text, UNFILLED, `${lang} ${code}: ${text}`);
        assert.ok(!text.includes('agents.'), `${lang} ${code}: a key is showing: ${text}`);
      }
    }
  }
});

test('statusLine: jev says whether a key is configured, never the key', () => {
  assert.equal(statusLine('jev', { configured: false, source: null }, null, false, 'ar'), 'لا مفتاح؛ لن يُرسل شيء');
  assert.equal(statusLine('jev', { configured: false, source: null }, null, false, 'en'), 'No key; nothing will be sent');
  assert.equal(statusLine('jev', { configured: true, source: 'env' }, null, false, 'en'), 'Key configured (env)');
  assert.equal(statusLine('jev', null, null, false, 'en'), '—');
});

test('statusLine: Laya reads its worker state, and a failed status request stays in its own column', () => {
  const laya = over => ({ configured: true, source: 'env', problem: null, worker: 'stopped', device: null, laya: null, ...over });
  const line = (status, inFlight = false, lang = 'en') => statusLine('laya', status, null, inFlight, lang);
  assert.equal(line(laya({ configured: false, source: null, problem: 'not_configured' })), 'Not configured: LAYA_HOME');
  assert.equal(line(laya({ problem: 'not_found' })), STRINGS.en['agents.models.laya.status.not_found']);
  assert.equal(line(laya({})), 'Loads on the first question');
  assert.equal(line(laya({}), true), 'Loading on this machine for the first time…');
  assert.equal(line(laya({ worker: 'starting' })), 'Loading on this machine for the first time…');
  assert.equal(line(laya({ worker: 'ready', device: 'cuda' })), 'Loaded on cuda until the server stops');
  assert.equal(line(laya({ worker: 'ready', device: 'cuda' }), true), 'Loaded on cuda until the server stops');
  assert.equal(line(laya({ worker: 'failed', problem: 'start_timeout' })), 'Could not start: start_timeout');
  assert.equal(line(laya({ worker: 'ready', device: 'cuda' }), false, 'ar'), 'محمَّل على cuda حتى يُغلق الخادم');
  // The status request itself failed: the server-down sentence, in this column.
  assert.equal(statusLine('laya', null, failureOf(null, null), false, 'en'), `No answer — ${STRINGS.en['agents.load.server_down']}`);
  for (const lang of LANGS) {
    for (const s of [laya({}), laya({ worker: 'failed', problem: null }), laya({ worker: 'ready', device: null })]) {
      assert.doesNotMatch(statusLine('laya', s, null, false, lang), UNFILLED);
    }
  }
});

test('model-panel.mjs is pure and names only keys that exist', () => {
  assert.doesNotMatch(SRC, /\bfetch\s*\(|\bdocument\.|\bwindow\.|\bglobalThis\b|localStorage|sessionStorage|indexedDB|cookie/);
  // Design C9: the model's own confidence is never read, so it can never be shown.
  assert.doesNotMatch(SRC, /\.confidence\b|\[\s*['"]confidence/);
  const literals = [...new Set([...SRC.matchAll(/'(agents\.[\w.]+)'/g)].map(m => m[1]))];
  assert.ok(literals.length >= 10, 'the key scan found almost nothing; the pattern has drifted');
  assert.deepEqual(literals.filter(k => !has(k)), []);
});
```

- [ ] **Step 10: Run it to verify it fails**

Run: `node --test app/static/sim/model-panel.test.mjs 2>&1 | grep -E '^ℹ (tests|pass|fail)|^Error|^✖' | head -5`

Expected: FAIL, with:
- `Error [ERR_MODULE_NOT_FOUND]: Cannot find module '…\app\static\sim\model-panel.mjs' imported from …\app\static\sim\model-panel.test.mjs`
- `✖ app\static\sim\model-panel.test.mjs`
- `ℹ tests 1`, `ℹ pass 0` and `ℹ fail 1`.

- [ ] **Step 11: Implement (the panel logic)**

Create `app/static/sim/model-panel.mjs`. Its comments must not contain `fetch(`, `document.`, `window.`, `.confidence`, or any storage word, because the test reads this source:

```js
// The models panel of /agents: two language models, jev and Laya, asked about
// the paused second (M3 design, docs/superpowers/specs/2026-09-28-agent-replay-m3-design.md
// sections 7.5b, 7.7 and 7.9).
//
// PURE: no page access, no requests, no clock. agents.mjs does the wiring
// (the gesture, the two status requests, the two buttons) and asks this module
// every question that has an answer worth testing, so model-panel.test.mjs
// pins each decision without a browser.
//
// THREE RULES, and they are the design's, not style:
//  - The two columns never meet. Every function takes one model's view, one
//    model's answer or one model's failure; nothing here reads both, so a jev
//    failure (no key, no credit, no network) can never block or blank Laya.
//  - Nothing is computed from an answer. rowView passes the model's own choice,
//    levels and probabilities through, and the order check compares two
//    choices of the same model. No average, no difference, and no comparison
//    with the agents. The model's own confidence is never read (design C9).
//  - Nothing is substituted. An error is its fixed code and that code's
//    sentence; a code this page does not know is a server error with its HTTP
//    status, never the server's text.
import { laneStoppedAt } from './agent-view.mjs';
import { t } from './i18n.mjs';
import './agents-strings.mjs';

const EM_DASH = '—';

export const MODELS = Object.freeze(['jev', 'laya']);

// The five question ids, in engine_env action order, so index i is ACTIONS[i]
// (agent-view.mjs) and row i of app/model_questions.py LEVELS.
export const QUESTION_IDS = Object.freeze(['spark_trim', 'lambda_trim', 'boost_ceiling', 'cooling_fan', 'coolant_pump']);

// Every code the two POST routes answer with (design 7.9). Each has a sentence
// agents.models.error.<code> in both languages; any other code is shown as
// agents.models.error.server_error with its HTTP status.
export const ERROR_CODES = Object.freeze([
  'no_key', 'network', 'timeout', 'key_rejected', 'vendor_refused', 'request_rejected', 'rate_limited',
  'overloaded', 'vendor_status', 'not_configured', 'not_found', 'start_failed', 'start_timeout',
  'worker_error', 'worker_died', 'network_attempt', 'bad_answer', 'foreign_origin', 'no_trace',
  'step_not_computed', 'busy',
]);

/**
 * May this model be asked about second k now? view = { playing, waiting, done,
 * frames, inFlight } for ONE model. Design C10: playback stopped (the play
 * button shows play: !playing && !waiting), which includes the natural end of
 * the episode and a finished episode never played; the build finished; frame k
 * exists; the sighted lane had not stopped at or before k; nothing in flight
 * for this model. Returns { enabled, reason }, reason an i18n key or null.
 */
export function askState(view, k) {
  const frames = Array.isArray(view?.frames) ? view.frames : [];
  if (view?.inFlight) return { enabled: false, reason: 'agents.models.reason.asking' };
  if (!view?.done && !frames.length) return { enabled: false, reason: 'agents.pause.empty' };
  if (!view.done) return { enabled: false, reason: 'agents.models.reason.not_done' };
  if (view.playing || view.waiting) return { enabled: false, reason: 'agents.models.reason.pause' };
  if (!Number.isInteger(k) || k < 0 || k >= frames.length) return { enabled: false, reason: 'agents.models.reason.not_done' };
  const stopped = laneStoppedAt(frames, 0);
  if (stopped !== null && stopped <= k) return { enabled: false, reason: 'agents.models.reason.stopped' };
  return { enabled: true, reason: null };
}

/**
 * One model's answers, one per second of the episode on screen, in memory
 * only. put() at a second already held replaces it; clear() empties the map
 * (agents.mjs calls it in compute() and clearEpisode()). An entry is whatever
 * agents.mjs stores: { body } for an answer or { failure } for an error.
 */
export function createAnswers() {
  const map = new Map();
  const id = (key, k) => `${key}#${k}`;
  return {
    put(key, k, entry) { map.set(id(key, k), entry); },
    get(key, k) { return map.has(id(key, k)) ? map.get(id(key, k)) : null; },
    clear() { map.clear(); },
    get size() { return map.size; },
  };
}

/**
 * Row `actionIndex` of one answer body (the POST route's 200 JSON), or null
 * when that action is missing. The five bars follow the options' own order
 * (the design's order), each with its physical level and the model's
 * probability, exactly one marked chosen. `reversed` and `verdict` come from
 * Laya's order check (answers_reversed, design 7.5b): 'held' when the choice
 * is the same with the options reversed, 'changed' when it is not; jev is
 * asked once, so both are null for jev.
 */
export function rowView(answer, actionIndex) {
  const id = QUESTION_IDS[actionIndex];
  const a = id ? answer?.answers?.[id] : undefined;
  if (!a || !Array.isArray(a.options)) return null;
  const r = answer.answers_reversed?.[id] ?? null;
  return {
    id,
    choice: a.choice,
    level: a.level_phys,
    net: a.level_net,
    chosenP: a.chosen_p,
    bars: a.options.map(o => ({ key: o.key, level: o.level_phys, p: a.probabilities?.[o.key], chosen: o.key === a.choice })),
    reversed: r ? { choice: r.choice, level: r.level_phys } : null,
    verdict: r ? (r.choice === a.choice ? 'held' : 'changed') : null,
  };
}

/**
 * What went wrong, from the HTTP status and the JSON body (either may be
 * missing). No status at all is a request that never reached the server:
 * 'server_down'. A body whose code is in ERROR_CODES keeps only that code, an
 * integer status and a string kind; anything else (FastAPI's own 500, a 422
 * {detail}, the server's server_error) is 'server_error' with the HTTP status.
 */
export function failureOf(httpStatus, body) {
  if (httpStatus === null || httpStatus === undefined) return { code: 'server_down', status: null, kind: null };
  if (body && typeof body === 'object' && ERROR_CODES.includes(body.code)) {
    return {
      code: body.code,
      status: Number.isInteger(body.status) ? body.status : null,
      kind: typeof body.kind === 'string' ? body.kind : null,
    };
  }
  return { code: 'server_error', status: httpStatus, kind: null };
}

/**
 * The sentence a column shows for a failure: «لا جواب — {code}: {sentence}»
 * for a known code, «لا جواب — {sentence}» for a failed request (the page's
 * own server-down sentence) and for an unknown code (server error, HTTP N).
 */
export function errorText(code, status, lang, kind = null) {
  if (code === 'server_down') {
    return t(lang, 'agents.models.no_answer_plain', { sentence: t(lang, 'agents.load.server_down') });
  }
  if (!ERROR_CODES.includes(code)) {
    return t(lang, 'agents.models.no_answer_plain',
      { sentence: t(lang, 'agents.models.error.server_error', { status: status ?? EM_DASH }) });
  }
  const sentence = t(lang, `agents.models.error.${code}`, { status: status ?? EM_DASH, kind: kind ?? 'other' });
  return t(lang, 'agents.models.no_answer', { code, sentence });
}

/**
 * One model's status line, from its GET status route. A failed status request
 * (failure) shows its error here, in this column only. jev says whether a key
 * is configured and where from, never the key; Laya says what its worker is
 * doing, and reads 'starting' while its first press is in flight.
 */
export function statusLine(name, status, failure, inFlight, lang) {
  if (failure) return errorText(failure.code, failure.status, lang, failure.kind);
  if (!status) return EM_DASH;
  if (name === 'jev') {
    return status.configured
      ? t(lang, 'agents.models.jev.status.configured', { source: status.source ?? EM_DASH })
      : t(lang, 'agents.models.jev.status.no_key');
  }
  if (status.problem === 'not_configured') return t(lang, 'agents.models.laya.status.not_configured');
  if (status.problem === 'not_found') return t(lang, 'agents.models.laya.status.not_found');
  if (status.worker === 'ready') return t(lang, 'agents.models.laya.status.ready', { device: status.device ?? EM_DASH });
  if (status.worker === 'starting' || inFlight) return t(lang, 'agents.models.laya.status.starting');
  if (status.worker === 'failed') return t(lang, 'agents.models.laya.status.failed', { code: status.problem ?? EM_DASH });
  return t(lang, 'agents.models.laya.status.stopped');
}
```

- [ ] **Step 12: Run to verify it passes (the panel logic), then the whole glob**

```bash
node --test app/static/sim/model-panel.test.mjs 2>&1 | grep -E '^ℹ (tests|pass|fail)|^✖'
node --test "app/static/sim/*.test.mjs" 2>&1 | grep -E '^ℹ (tests|pass|fail)|^✖'
```

Expected:
- The first command prints `ℹ tests 17`, `ℹ pass 17` and `ℹ fail 0`.
- The glob prints `ℹ tests <BASE + 24>`, `ℹ pass <BASE + 24>` and `ℹ fail 0`, with no `✖` line. On the prototype that was 126 of 126 from BASE 102. The 24 are 1 strings test, 6 gesture tests and 17 panel tests.

- [ ] **Step 13: Byte-check the six files**

Create `$SCRATCH/t7_bytecheck.py` with the Write tool. It holds no backslash-u; each escape text is built as `chr(92) + 'u' + cp`:

```python
"""Task 7 byte check: no literal escape-trap character in the six files, the
escapes agents-strings.mjs already carried are all still there, and the four
new files carry none. Run from the repository root. Exits 1 on a failure."""
import sys

TRAP = ('2066', '2068', '2069', '200f', '2011', '2212', '202f')
# agents-strings.mjs as M2 left it (d347ee5); this task adds no escape.
KEPT = {'2066': 1, '2068': 2, '2069': 3, '200f': 2, '2011': 2, '2212': 2, '202f': 0}
FILES = {
    'app/static/sim/agents-strings.mjs': KEPT,
    'app/static/sim/agents-strings.test.mjs': None,
    'app/static/sim/tap-unlock.mjs': dict.fromkeys(TRAP, 0),
    'app/static/sim/tap-unlock.test.mjs': dict.fromkeys(TRAP, 0),
    'app/static/sim/model-panel.mjs': dict.fromkeys(TRAP, 0),
    'app/static/sim/model-panel.test.mjs': dict.fromkeys(TRAP, 0),
}
ok = True
for path, escapes in FILES.items():
    with open(path, encoding='utf-8', newline='') as fh:
        src = fh.read()
    literal = {cp: src.count(chr(int(cp, 16))) for cp in TRAP if src.count(chr(int(cp, 16)))}
    wrong = {} if escapes is None else {
        cp: src.count(chr(92) + 'u' + cp) for cp in TRAP if src.count(chr(92) + 'u' + cp) != escapes[cp]}
    good = not literal and not wrong
    ok = ok and good
    print(f"{'ok   ' if good else 'WRONG'} {path}  literal {literal or 0}  escapes off {wrong or 0}")
sys.exit(0 if ok else 1)
```

Run: `$PY "$SCRATCH/t7_bytecheck.py"; echo "exit $?"`

Expected:
```
ok    app/static/sim/agents-strings.mjs  literal 0  escapes off 0
ok    app/static/sim/agents-strings.test.mjs  literal 0  escapes off 0
ok    app/static/sim/tap-unlock.mjs  literal 0  escapes off 0
ok    app/static/sim/tap-unlock.test.mjs  literal 0  escapes off 0
ok    app/static/sim/model-panel.mjs  literal 0  escapes off 0
ok    app/static/sim/model-panel.test.mjs  literal 0  escapes off 0
exit 0
```

A `WRONG` row on `agents-strings.mjs` means an edit rewrote an escape into its character. Restore the file with `git checkout -- app/static/sim/agents-strings.mjs` and redo Step 3 with the Edit tool only.

- [ ] **Step 14: Commit**

```bash
git add app/static/sim/tap-unlock.mjs app/static/sim/tap-unlock.test.mjs app/static/sim/model-panel.mjs app/static/sim/model-panel.test.mjs app/static/sim/agents-strings.mjs app/static/sim/agents-strings.test.mjs
$PY verify_docs.py 2>&1 | tail -1
node --test "app/static/sim/*.test.mjs" 2>&1 | grep -E '^ℹ (tests|pass|fail)' > "$SCRATCH/t7_node.txt"; cat "$SCRATCH/t7_node.txt"
$PY -m app.test_replay > "$SCRATCH/t7_replay.txt" 2>&1; tail -1 "$SCRATCH/t7_replay.txt"
```

Expected output:
- `verify_docs.py`'s last line starts `All` and reads `… checks pass (… figure mentions scanned in the documents).`, with the same two numbers as after Task 6. Its scan (`verify_docs.py:166` `SCAN_EXT`, matched with `endswith`) reads `.md .py .html .js .txt` and never a `.mjs`. Read the line; if it is a failure, stop and read what it names.
- The node lines repeat Step 12's counts.
- `app.test_replay` takes about 77 s. Its last line reads `49 of 49 checks pass` (measured on d347ee5; no task edits `app/test_replay.py`).

Then write the message and commit by explicit path, because another session may be committing in this tree:

```bash
{
cat <<'EOF'
Agent replay M3 (6a/7): tap-unlock and model-panel, pure and node-tested; the M3 strings

M3 design (docs/superpowers/specs/2026-09-28-agent-replay-m3-design.md)
7.5b, 7.7, 7.8, 7.9 and section 9's node tests. Nothing imports the two new
modules yet: agents.mjs wires them in 6b/7, so /agents is unchanged.

- tap-unlock.mjs: createTapUnlock({taps: 10, windowMs: 4000}) -> {tap(nowMs)}.
  A closure counter: no storage, no clock of its own, so a reload forgets it.
- model-panel.mjs: MODELS, QUESTION_IDS, ERROR_CODES (21 codes), askState
  (enabled only when stopped, finished, frame k present, the sighted lane not
  stopped at or before k, and nothing in flight for that model; the natural
  end counts), createAnswers (one entry per episode and second), rowView
  (Laya's order check: held / changed), failureOf, errorText, statusLine.
  Pure: no page access, no requests; the model's confidence is never read.
- agents-strings.mjs: 63 keys per language (agents.models.* and
  agents.pause.empty). The Arabic honesty lines are the design's, pinned
  whole by agents-strings.test.mjs; no new line needs an escape.

Where the code departs from design 7.2: errorText takes (code, status, lang,
kind); failureOf and statusLine are added; askState's reason before any
episode is agents.pause.empty; the reference line stops at its colon.

node --test "app/static/sim/*.test.mjs":
EOF
cat "$SCRATCH/t7_node.txt"
printf '\npython -m app.test_replay:\n'
cat "$SCRATCH/t7_replay.txt"
printf '\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n'
} > "$SCRATCH/t7_msg.txt"
git commit -F "$SCRATCH/t7_msg.txt" -- app/static/sim/tap-unlock.mjs app/static/sim/tap-unlock.test.mjs app/static/sim/model-panel.mjs app/static/sim/model-panel.test.mjs app/static/sim/agents-strings.mjs app/static/sim/agents-strings.test.mjs
git show --stat --oneline HEAD | head -9
```

Expected:
- The first line of `git show` is `<sha> Agent replay M3 (6a/7): tap-unlock and model-panel, pure and node-tested; the M3 strings`.
- The stat lists exactly the six files: four created and two modified.
- The message's last line is `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- The message's body carries `49 of 49 checks pass` and the three node count lines.


---

### Task 8: fe-page: the hidden `#models-panel` in agents.html, its CSS, and the agents.mjs wiring (the gesture, both status calls, both buttons, askModel with the loadToken drop, renderModels at five hooks, answer maps cleared on compute and clearEpisode); the harness records the fetch `init`; agents-page-models.test.mjs; test 12

**Files:**
- Create: `app/static/sim/agents-page-models.test.mjs`
- Modify: `app/static/agents.html:106-108` (insert after the pause panel's closing tag)
- Modify: `app/static/sim/agents.css:81` (card rule), `:127` (`.footer-index`), `:135` (the <1100 list), and the end of the file
- Modify: `app/static/sim/agents.mjs:32` (imports), `:76-77` (end of `state`), `:199` (`compute`), `:458-459` (`clearEpisode`), `:1025-1027` (`renderPanel`), `:1029` (insert the models block before the per-frame header), `:1067-1069` (`renderAll`), `:1110` (loop), `:1115-1129` (play and restart handlers), `:1142` (`start`)
- Modify: `app/static/sim/agents-page-harness.mjs:101-107`
- Modify: `app/static/sim/agents-page.test.mjs:118-119` and the end of the file
- Modify: `app/test_agents.py` (`PageTests.test_page_assets_ids` and `test_chase_is_optional`; anchor by text, because Tasks 2-6 shift the line numbers)
- Test: `app/static/sim/agents-page-models.test.mjs`, `app/static/sim/agents-page.test.mjs`, `app/test_agents.py` (PageTests)

**Interfaces:**
- Consumes:
  - From Task 7: `createTapUnlock` from `./tap-unlock.mjs`; `MODELS`, `askState`, `createAnswers`, `rowView`, `failureOf`, `errorText`, `statusLine` from `./model-panel.mjs`; every `agents.models.*` string and `agents.pause.empty`. `statusLine` returns the Laya "ready" line only when `status.worker === 'ready'`, and "starting" only while `status.worker === 'starting'` or `inFlight`.
  - From Task 6: the JSON of the four routes. The 200 bodies carry `answers[qid] = {choice, level_phys, level_net, probabilities, chosen_p, options: [{key, level_phys}]}`, plus `answers_reversed`, `started_s`, `device` and `laya` for Laya. The error bodies are `{model, code, status?, kind?}`. The status bodies are as in Task 6.
  - Existing code at d347ee5: `agents.mjs` `state`, `isWaiting()` (:722), `carOf()` (:765), `fmtAction()` (:824), `fmt`, `num`, `el`, `setText`, `LANES`, `ACTIONS` and `EM_DASH`; the harness's `installFakePage` and `byClass`.
- Produces:
  - `agents.html`: a static `<section id="models-panel" class="models-panel" hidden>` placed right after the pause panel. Every id in it is written out: `models-not-thesis`, `models-claim`, `models-levels`, `model-{jev,laya}-{name,status,reason,latency,error,rows,sent-body}`, `model-jev-text`, `model-laya-where`, `model-laya-text`, `model-laya-check`, `ask-jev` and `ask-laya`.
  - `agents.css`:
    - `.models-panel` joins the card rule;
    - `.models-panel{align-self:stretch}`;
    - `.models-panel{order:7}` below 1100 px;
    - `.models-columns` collapses to one column below 760 px;
    - `.footer-index` gets `touch-action:manipulation`;
    - the panel's own classes.
  - `agents.mjs`:
    - the `models` state object;
    - the functions `modelNodes`, `askView`, `loadModelStatus`, `askModel`, `renderModelRows` and `renderModels`;
    - `renderModels()` is called in `renderPanel`, in the play and restart handlers, in the loop's play-state branch, when each answer arrives, and in `renderAll`;
    - `compute()` and `clearEpisode()` call `answers.clear()` for both models;
    - a Laya 200 sets that column's status to `worker: 'ready'` (with its `device` and `laya`) before rendering. The status re-fetch still runs and remains the authority.
  - `agents-page-harness.mjs`: each request records `{url, init, resolve, reject}`.

Two traps on this machine, measured 28 Sep:
- **The Bash tool collapses a typed double backslash into one.** `printf '%s' 'a\\b'` printed `a\b`, and a JavaScript `new RegExp(`\\.${name}`)` written through a heredoc lost its escapes. Write every code block below with the **Write or Edit tool**, never with a Bash heredoc.
- **The Write and Edit tools decode a typed backslash-u escape.** None of the code in this task contains one. The existing escapes in `agents.mjs` (`'\u202f'` in `fmtInt`, `'\u2212'` in `fmtAction`) must stay as text, so no Edit below touches those lines. Step 8 byte-checks them.

Code wins over the skeleton in one place: at d347ee5 the <1100 list reads `.profile-panel{order:5}.pause-panel{order:6}` (`agents.css:135`). This task appends `.models-panel{order:7}`, which already places the models panel after the pause panel. Task 9 renumbers the list.

The Bash tool keeps no environment between calls, so every Bash block in Tasks 8 to 11 begins with this line. It is written out in each block. `SCRATCH` is one fixed folder outside the repository (not `%TEMP%` itself), and its Windows form is `C:\Users\admin\AppData\Local\Temp\claude\c--Users-admin-Documents-graduation-project-GRAD-project\m3-build`:

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
```

- [ ] **Step 1: Write the failing tests (the markup and the CSS)**

In `app/static/sim/agents-page.test.mjs`, make one Edit. old_string:

```js
    ['footer-index', 'agents.footer.index'],
  ]) {
```

new_string:

```js
    ['footer-index', 'agents.footer.index'],
    // M3 (design 7.7): the models panel's honesty lines, in the markup like
    // the others, so they are there the moment the panel is shown.
    ['models-not-thesis', 'agents.models.not_thesis'],
    ['models-claim', 'agents.models.claim'],
    ['models-levels', 'agents.models.levels'],
    ['model-jev-text', 'agents.models.jev.text'],
    ['model-laya-text', 'agents.models.laya.text'],
    ['model-laya-check', 'agents.models.laya.check'],
  ]) {
```

Append this test at the end of `app/static/sim/agents-page.test.mjs`, after its last `});`. The `new RegExp` line carries **doubled** backslashes, and they must survive:

```js

// M3 (design 7.2, the agents.css row). Below 1100 px .agents-layout is one
// flex column with align-items:start, so a panel hugs the start edge unless it
// stretches; the models panel comes after the pause panel there; its two
// columns fold into one on a phone; and ten fast taps on the footer label
// must not zoom the page.
test('the models panel stretches, comes after the pause panel below 1100 px, and the footer label never zooms', () => {
  const css = read(new URL('./agents.css', import.meta.url));
  assert.match(css, /\.pause-panel,\.models-panel\{background:var\(--paper\)/, 'the models panel is a card like the pause panel');
  assert.match(css, /(?:^|\})\.models-panel\{align-self:stretch\}/m);
  const narrow = css.match(/@media\(max-width:1099px\)\{([\s\S]*?)\n\}/);
  assert.ok(narrow, 'agents.css has no <1100 px block');
  const order = name => Number((narrow[1].match(new RegExp(`\\.${name}\\{order:(\\d+)\\}`)) || [])[1]);
  assert.equal(order('models-panel'), 7);
  assert.ok(order('models-panel') > order('pause-panel'), 'the models panel follows the pause panel');
  assert.match(css, /@media\(max-width:760px\)\{\s*\.models-columns\{grid-template-columns:1fr\}/);
  assert.match(css, /(?:^|\})\.footer-index\{[^}]*touch-action:manipulation/m);
});
```

In `app/test_agents.py`, `PageTests.test_page_assets_ids`, make one Edit. old_string (one line):

```python
        self.assertFalse(used - set(ids), f"agents.mjs reads ids the page does not define: {sorted(used - set(ids))}")
```

new_string:

```python
        self.assertFalse(used - set(ids), f"agents.mjs reads ids the page does not define: {sorted(used - set(ids))}")
        # M3 (design 7.7): the models panel is static in the markup and hidden
        # until the ten taps, so every id agents.mjs reads for it is one the
        # check above can see.
        self.assertTrue('<section id="models-panel" class="models-panel" hidden>' in html,
                        "#models-panel must be written out in agents.html, and hidden")
```

- [ ] **Step 2: Run them to verify they fail**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
$PY -c "import pathlib; print(pathlib.Path('app/static/sim/agents-page.test.mjs').read_text(encoding='utf-8').count(chr(92)*2))"
node --test app/static/sim/agents-page.test.mjs 2>&1 | grep -E "^✖|^ℹ (tests|pass|fail)|AssertionError"
$PY -m app.test_agents PageTests 2>&1 | grep -E "FAIL:|AssertionError|^Ran|^OK|^FAILED"
```

Expected:
- `10`. The file carried 6 doubled backslashes at d347ee5, and the new test adds 4. A lower number means a doubled backslash was lost: rewrite that line with the Edit tool.
- Node: `ℹ tests 9`, `ℹ pass 7`, `ℹ fail 2`, with:
  - `✖ the honesty lines are in the markup itself, not only written by script` / `AssertionError [ERR_ASSERTION]: #models-not-thesis is missing`
  - `✖ the models panel stretches, comes after the pause panel below 1100 px, and the footer label never zooms` / `AssertionError [ERR_ASSERTION]: the models panel is a card like the pause panel`
- Python: `FAIL: test_page_assets_ids` with `AssertionError: False is not true : #models-panel must be written out in agents.html, and hidden`, then `Ran 8 tests` and `FAILED (failures=1)`. The repository's PageTests have no skip at d347ee5 (measured 28 Sep: `Ran 8 tests`, `OK`); read any skip count from the run.

- [ ] **Step 3: Implement the markup and the CSS**

In `app/static/agents.html`, make one Edit. old_string (the end of the pause panel, `:107-108`):

```html
          <p id="fingerprint-taken" class="device-line"></p>
        </section>
```

new_string:

```html
          <p id="fingerprint-taken" class="device-line"></p>
        </section>
        <section id="models-panel" class="models-panel" hidden>
          <h2 data-i18n="agents.models.heading">اسأل نموذجاً لغوياً عن هذه الثانية</h2>
          <p id="models-not-thesis" class="models-note" data-i18n="agents.models.not_thesis">ليس جزءاً من الرسالة ولا من أي نتيجة. لا يقارن أي رقم هنا النموذجين بالوكيلين، ولا يُحسب أي فرق.</p>
          <p id="models-claim" class="models-note" data-i18n="agents.models.claim">الاحتمالات ادعاء النموذج نفسه، ولم تُختبر على هذه المهمة.</p>
          <p id="models-levels" class="models-note" data-i18n="agents.models.levels">كل نموذج يختار واحداً من خمسة مستويات لكل إجراء: للتعديلات الثلاثة الحدّان و"بلا تعديل" ونقطتان في المنتصف؛ وللمروحة والمضخة خمس قيم متساوية التباعد. المعروض هو اختيار النموذج نفسه، ولا يُحسب منه متوسط.</p>
          <div class="models-columns">
            <article class="model-col jev">
              <h3 id="model-jev-name" class="model-name" dir="ltr"></h3>
              <p class="model-where" data-i18n="agents.models.jev.where">خدمة خارجية في الولايات المتحدة · كل ضغطة استدعاء مدفوع واحد</p>
              <p id="model-jev-text" class="model-text" data-i18n="agents.models.jev.text">خدمة خارجية تعمل في الولايات المتحدة. ليست جزءاً من الرسالة ولا من أي نتيجة، ولا يقارنها أي رقم بالوكلاء. هذه الصفحة لا تحفظ شيئاً؛ لكن اتفاقية المورّد تسمح له بالاحتفاظ بما يُرسل لاستخراج بيانات القياس بلا حدّ زمني (MCA §4.1). تُرسَل إليه حالة هذه الحلقة المحاكاة فقط، لا بيانات السيارة المسجّلة. كل ضغطة استدعاء واحد مدفوع. اتفاقية المورّد تمنع تدريب أي نموذج على تقليد إجاباته. شروط موقع المورّد موجّهة لزوّار الولايات المتحدة؛ هل الاستخدام من السعودية مسموح؟ غير معروف. ويقول المورّد إن النموذج ضعيف في الدقة العددية.</p>
              <p id="model-jev-status" class="model-status"></p>
              <button id="ask-jev" class="play-button model-ask" type="button" disabled data-i18n="agents.models.jev.ask">اسأل jev عن هذه الثانية (استدعاء مدفوع واحد)</button>
              <p id="model-jev-reason" class="model-reason"></p>
              <p id="model-jev-latency" class="model-latency"></p>
              <p id="model-jev-error" class="model-error" role="status" hidden></p>
              <div id="model-jev-rows" class="model-rows"></div>
              <p class="model-footer" data-i18n="agents.models.footer">هدف لثانية واحدة: لم يُطبَّق ولم يُقيَّد بحد سرعة التغيير</p>
              <details class="model-sent"><summary data-i18n="agents.models.sent">ما الذي أُرسل</summary><pre id="model-jev-sent-body" dir="ltr"></pre></details>
            </article>
            <article class="model-col laya">
              <h3 id="model-laya-name" class="model-name" dir="ltr"></h3>
              <p id="model-laya-where" class="model-where"></p>
              <p id="model-laya-text" class="model-text" data-i18n="agents.models.laya.text">يعمل على هذا الجهاز ولا يُرسل شيئاً خارجه. تجربة تشغيل، لا تقييم. يقول ملف لايا نفسه إن نتيجة مثال لا تعني أنه مناسب للتحكم بالمحرك (README_AR.md:31). رخصة Apache 2.0.</p>
              <p id="model-laya-check" class="model-text" data-i18n="agents.models.laya.check">نسأل لايا مرتين، والخيارات بترتيبين متعاكسين. إذا تغيّر اختياره بتغيير الترتيب وحده، فذلك الاختيار لا يأتي من حالة المحرك.</p>
              <p id="model-laya-status" class="model-status"></p>
              <button id="ask-laya" class="play-button model-ask" type="button" disabled data-i18n="agents.models.laya.ask">اسأل لايا عن هذه الثانية (على هذا الجهاز)</button>
              <p id="model-laya-reason" class="model-reason"></p>
              <p id="model-laya-latency" class="model-latency"></p>
              <p id="model-laya-error" class="model-error" role="status" hidden></p>
              <div id="model-laya-rows" class="model-rows"></div>
              <p class="model-footer" data-i18n="agents.models.footer">هدف لثانية واحدة: لم يُطبَّق ولم يُقيَّد بحد سرعة التغيير</p>
              <details class="model-sent"><summary data-i18n="agents.models.sent">ما الذي أُرسل</summary><pre id="model-laya-sent-body" dir="ltr"></pre></details>
            </article>
          </div>
        </section>
```

The Arabic text in the markup is Task 7's strings, verbatim. `applyTranslations` replaces it by key, and the markup test checks only the `data-i18n` keys. `#model-laya-where` has no `data-i18n` because its string carries `{device}`; `renderModels` writes it.

In `app/static/sim/agents.css`, make three Edits:

1. old_string `.picker-panel,.verdict-panel,.pause-panel{background:`, new_string `.picker-panel,.verdict-panel,.pause-panel,.models-panel{background:`.
2. old_string `.profile-panel{order:5}.pause-panel{order:6}`, new_string `.profile-panel{order:5}.pause-panel{order:6}.models-panel{order:7}`.
3. old_string `.footer-index{display:inline-flex;align-items:center;min-height:32px;min-width:32px;padding:0 8px}`, new_string `.footer-index{display:inline-flex;align-items:center;min-height:32px;min-width:32px;padding:0 8px;touch-action:manipulation}`.

Then append this at the end of `agents.css`:

```css

/* M3: the models panel (design 7.7), hidden until ten taps on the footer
   label. One column per model, each with its own status, button, answer and
   error. Nothing here is red or green: a model's choice is not a verdict, and
   "held" or "changed with the order" describes the answer, not a score. It
   stretches because below 1100 px .agents-layout is a flex column with
   align-items:start, where a panel that hugs its content would leave the two
   columns a sliver. */
.models-panel{align-self:stretch}
.models-note{margin:6px 0 0;font-size:10px;line-height:1.75;color:var(--ink-2)}
.models-columns{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:12px}
.model-col{display:flex;flex-direction:column;gap:6px;min-width:0;padding-top:10px;border-top:1px solid var(--hairline)}
.model-name{margin:0;font:600 11px/1.5 Consolas,monospace;overflow-wrap:anywhere}
.model-where{margin:0;font-size:10px;line-height:1.7;color:var(--estimated-ink)}
.model-where:empty{display:none}
.model-text{margin:0;font-size:9px;line-height:1.75;color:var(--muted)}
.model-status{margin:0;font-size:10px;line-height:1.7;color:var(--ink-2)}
.model-ask{width:100%;min-width:0}
.model-reason,.model-latency{margin:0;font-size:9px;line-height:1.7;color:var(--muted)}
.model-reason:empty,.model-latency:empty{display:none}
.model-error{margin:0;padding:6px 8px;border-radius:5px;background:var(--error-bg);color:var(--error-ink);font-size:10px;line-height:1.7}
.model-rows:empty{display:none}
.model-row{padding:8px 0;border-bottom:1px solid var(--hairline)}
.model-reference{display:flex;flex-wrap:wrap;align-items:center;gap:2px 10px;margin:4px 0 0;font-size:9px;color:var(--muted)}
.model-reference>span{display:inline-flex;align-items:center;gap:4px}
.model-reference b{font-weight:600;color:var(--ink-2);font-variant-numeric:tabular-nums}
.model-choice{margin:4px 0 0;font-size:11px;font-weight:600}
.model-bars{display:flex;flex-direction:column;gap:2px;margin-top:4px;direction:ltr}
.model-bar{display:grid;grid-template-columns:56px minmax(0,1fr) 30px;align-items:center;gap:6px;font-size:8px;color:var(--muted);font-variant-numeric:tabular-nums}
.model-bar i{display:block;height:5px;min-width:1px;border-radius:2px;background:var(--muted-3)}
.model-bar.chosen{color:var(--ink);font-weight:650}
.model-bar.chosen i{background:var(--ink-2)}
.model-chosen-p{margin:4px 0 0;font-size:9px;color:var(--ink-2)}
.model-order{display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 8px;margin:4px 0 0;font-size:9px;color:var(--muted)}
.model-order .held,.model-order .changed{font-weight:650;color:var(--ink-2)}
.model-order .changed{text-decoration:underline dotted}
.model-footer{margin:4px 0 0;font-size:9px;line-height:1.7;color:var(--muted-2)}
.model-sent{font-size:9px;color:var(--muted)}
.model-sent summary{cursor:pointer}
.model-sent pre{margin:4px 0 0;max-height:240px;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere;font:9px/1.6 Consolas,monospace;color:var(--code-ink);text-align:left}
@media(max-width:760px){
.models-columns{grid-template-columns:1fr}
}
```

- [ ] **Step 4: Run them to verify they pass**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
node --test app/static/sim/agents-page.test.mjs 2>&1 | grep -E "^✖|^ℹ (tests|pass|fail)"
$PY -m app.test_agents PageTests 2>&1 | grep -E "FAIL:|ERROR:|^Ran|^OK|^FAILED"
```

Expected: `ℹ tests 9`, `ℹ pass 9`, `ℹ fail 0`; then `Ran 8 tests` and `OK`. Nothing in `agents.mjs` reads the new ids yet, so the id scan is unchanged.

- [ ] **Step 5: Write the failing tests (the wiring)**

In `app/static/sim/agents-page-harness.mjs`, make one Edit. old_string (`:101-107`):

```js
  // Each request waits until the test answers it, so the order is the test's.
  const requests = [];
  let arrived = null;
  globalThis.fetch = url => new Promise((resolve, reject) => {
    requests.push({ url: String(url), resolve, reject });
    if (arrived) { arrived(); arrived = null; }
  });
```

new_string:

```js
  // Each request waits until the test answers it, so the order is the test's.
  // `init` is fetch's second argument as the page passed it (method, headers,
  // body), so a test can read what a POST sent.
  const requests = [];
  let arrived = null;
  globalThis.fetch = (url, init = {}) => new Promise((resolve, reject) => {
    requests.push({ url: String(url), init, resolve, reject });
    if (arrived) { arrived(); arrived = null; }
  });
```

Create `app/static/sim/agents-page-models.test.mjs` with the Write tool:

```js
// The /agents page's hidden models panel (M3 design 7.7), RUNNING against the
// fake DOM and the fake server of agents-page-harness.mjs. Its own file, not
// agents-page-run.test.mjs: each harness file boots agents.mjs once in its own
// process, and the unlock adds two status requests to the ordered request
// queue that run.test's existing tests do not answer.
//
// The tests run IN ORDER and each says the state it starts from: the page's
// state carries from one to the next, and the unlock cannot be undone within
// one boot (only a reload forgets it). Every model reply below is a fake,
// shaped as app/agent_api.py's four routes answer; nothing reaches a model.
// The natural end of an episode is pinned in model-panel.test.mjs instead:
// the harness stubs requestAnimationFrame, so the loop never runs here.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { STRINGS } from './i18n.mjs';
import { installFakePage, byClass } from './agents-page-harness.mjs';

const CATALOG = {
  ...JSON.parse(readFileSync(new URL('./agent-catalog.fixture.json', import.meta.url), 'utf8')),
  sb3: true,
};
const MODEL_IDS = ['models-panel', 'ask-jev', 'ask-laya',
  'model-jev-name', 'model-jev-status', 'model-jev-reason', 'model-jev-latency', 'model-jev-error',
  'model-jev-rows', 'model-jev-sent-body',
  'model-laya-name', 'model-laya-where', 'model-laya-status', 'model-laya-reason', 'model-laya-latency',
  'model-laya-error', 'model-laya-rows', 'model-laya-sent-body'];
const h = installFakePage({
  search: '?runs=runs_c4&seed=5&ep=1',
  ids: ['compute', 'error', 'pick-experiment', 'pick-pair', 'pick-episode', 'play', 'restart', 'seek',
    'footer-index', 'pause-heading', ...MODEL_IDS],
});
const { nodes, requests, nextRequest, reply, fail, settle, seekTo } = h;
// What agents.html says before any script runs.
nodes['models-panel'].hidden = true;
nodes['ask-jev'].disabled = true;
nodes['ask-laya'].disabled = true;

const AR = key => STRINGS.ar[key];
const AGENT = { budget_line: 'trained 300000 steps of 300000 requested' };
const META = {
  runs: 'runs_c4', seed: 5, ep: 1, steps: 719, dt: 1, protocol: 'd2', agents: [AGENT, AGENT],
  preview_s: [2, 5, 15, 30],
  act: { lo: [-8, -0.15, -40, 0, 0.3], hi: [4, 0.06, 15, 1, 1], neutral_phys: [0, 0, 0, 1, 1] },
  limits: { turb_c: 849.9 },
};
const ROAD = {
  rise_m: 0, p_baro_kpa: 101.3, t_amb_c: 42, climb_start_s: null,
  grade_pct: [0, 0, 0, 0], s_m: [0, 0, 20, 40], x_m: [0, 0, 20, 40], z_m: [0, 0, 0, 0],
};
const car = {
  cmd: [0, 0, 0, 1, 1], act: [-1.5, 0, 0, 1, 1], held: [false, false, false, false, false],
  preview_pct: [0, 0, 0, 0], map_kpa: 180, turb_c: 700, torque_nm: 300, torque_req_nm: 310, damage: 1.5,
};
const FRAMES = [0, 1, 2].map(k => ({ k, cars: [car, car] }));
const READY = { status: 'ready', since: 0, steps: 3, meta: META, road: ROAD, frames: FRAMES };

// model_questions' five questions: the ASCII keys (design C12) and their levels.
const IDS = ['spark_trim', 'lambda_trim', 'boost_ceiling', 'cooling_fan', 'coolant_pump'];
const KEYS = [
  ['retard 8 deg', 'retard 4 deg', 'no change', 'advance 2 deg', 'advance 4 deg'],
  ['richer by 0.15', 'richer by 0.075', 'no change', 'leaner by 0.03', 'leaner by 0.06'],
  ['ceiling -40 kPa', 'ceiling -20 kPa', 'no change', 'ceiling +7.5 kPa', 'ceiling +15 kPa'],
  ['fan 0 %', 'fan 25 %', 'fan 50 %', 'fan 75 %', 'fan 100 %'],
  ['pump 30 %', 'pump 47.5 %', 'pump 65 %', 'pump 82.5 %', 'pump 100 %'],
];
const LEVELS = [[-8, -4, 0, 2, 4], [-0.15, -0.075, 0, 0.03, 0.06], [-40, -20, 0, 7.5, 15],
  [0, 0.25, 0.5, 0.75, 1], [0.3, 0.475, 0.65, 0.825, 1]];
// One action as to_action returns it: option j of action i chosen.
const pick = (i, j) => ({
  choice: KEYS[i][j],
  level_phys: LEVELS[i][j],
  level_net: 2 * (LEVELS[i][j] - LEVELS[i][0]) / (LEVELS[i][4] - LEVELS[i][0]) - 1,
  probabilities: Object.fromEntries(KEYS[i].map((key, n) => [key, n === j ? 0.6 : 0.1])),
  chosen_p: 0.6,
  options: KEYS[i].map((key, n) => ({ key, level_phys: LEVELS[i][n] })),
});
const ANSWERS = Object.fromEntries(IDS.map((id, i) => [id, pick(i, 2)]));
// With the options reversed, spark moves and the other four hold.
const REVERSED = { ...ANSWERS, spark_trim: pick(0, 4) };
const LAYA_OK = {
  model: 'laya', runs_on: 'local', model_name: 'laya-rl-agent', laya: '0.3.20', device: 'cuda', ms: 70.2,
  started_s: 6.1, answers: ANSWERS, answers_reversed: REVERSED,
  usage: [{ input_tokens: 2729, output_tokens: 0 }, { input_tokens: 2729, output_tokens: 0 }],
  sent: [{ state: {}, questions: {} }, { state: {}, questions: {} }], trace: 'runs_c4/5/1', step: 0,
};
const LAYA_READY = { configured: true, source: 'env', problem: null, worker: 'ready', device: 'cuda', laya: '0.3.20' };
const rowsOf = name => byClass(nodes[`model-${name}-rows`], 'model-row');

await import('./agents.mjs');
reply(await nextRequest(), CATALOG);
await settle();

// Starts from: runs_c4 / 5 / 1 selected, nothing computed, locked.
test('locked, nothing is asked and no model node is touched, even with a finished episode on screen', async () => {
  nodes.compute.click();
  reply(await nextRequest(), READY);
  await settle();
  nodes.play.click();
  nodes.play.click();
  await settle();
  assert.equal(requests.length, 0, 'a model or status request before the gesture');
  assert.equal(nodes['models-panel'].hidden, true);
  for (const id of MODEL_IDS) assert.equal(nodes[id].textContent, '', `#${id} was written while locked`);
  assert.equal(nodes['ask-jev'].disabled, true);
  assert.equal(nodes['ask-laya'].disabled, true);
});

// Starts from: a finished episode at second 0, never played past it; locked.
test('nine taps unlock nothing; the tenth shows the panel and asks for both statuses, each on its own', async () => {
  for (let i = 0; i < 9; i++) nodes['footer-index'].click();
  assert.equal(nodes['models-panel'].hidden, true, 'nine taps unlock nothing');
  assert.equal(requests.length, 0);
  nodes['footer-index'].click();
  assert.equal(nodes['models-panel'].hidden, false, 'the tenth tap shows the panel');
  const jevStatus = await nextRequest();
  const layaStatus = await nextRequest();
  assert.deepEqual([jevStatus.url, layaStatus.url], ['/api/agents/jev/status', '/api/agents/laya/status']);
  fail(jevStatus);
  reply(layaStatus, { configured: true, source: 'env', problem: null, worker: 'stopped', device: null, laya: null });
  await settle();
  assert.match(nodes['model-jev-status'].textContent, new RegExp(AR('agents.load.server_down')), 'jev\'s failed status stays in jev\'s column');
  assert.equal(nodes['model-laya-status'].textContent, AR('agents.models.laya.status.stopped'));
  // A finished episode never played: second 0 can be asked about at once.
  assert.equal(nodes['ask-jev'].disabled, false);
  assert.equal(nodes['ask-laya'].disabled, false);
  assert.equal(nodes['model-laya-reason'].textContent, AR('agents.models.ask_this'));
  for (let i = 0; i < 10; i++) nodes['footer-index'].click();
  await settle();
  assert.equal(requests.length, 0, 'more taps ask nothing more');
});

// Starts from: unlocked, second 0, nothing asked.
test('on a finished episode, play then pause at the same second enables both buttons, with no seek', async () => {
  nodes.play.click();
  assert.equal(nodes['ask-jev'].disabled, true, 'playing');
  assert.equal(nodes['ask-laya'].disabled, true, 'playing');
  assert.equal(nodes['model-jev-reason'].textContent, AR('agents.models.reason.pause'));
  nodes.play.click();
  assert.equal(nodes['ask-jev'].disabled, false, 'paused at the same second');
  assert.equal(nodes['ask-laya'].disabled, false, 'paused at the same second');
  await settle();
  assert.equal(requests.length, 0, 'nothing is asked on its own');
});

// Starts from: unlocked, paused at second 0, nothing asked.
test('a jev failure stays in jev\'s column and Laya still answers, with its order check', async () => {
  nodes['ask-jev'].click();
  const j = await nextRequest();
  assert.equal(j.url, '/api/agents/jev');
  assert.equal(j.init.method, 'POST');
  assert.equal(j.init.headers['Content-Type'], 'application/json');
  assert.deepEqual(JSON.parse(j.init.body), { trace: 'runs_c4/5/1', step: 0 });
  assert.equal(nodes['ask-jev'].disabled, true, 'jev in flight');
  assert.equal(nodes['model-jev-reason'].textContent, AR('agents.models.reason.asking'));
  assert.equal(nodes['ask-laya'].disabled, false, 'jev in flight leaves Laya enabled');
  reply(j, { model: 'jev', code: 'no_key' }, 503);
  await settle();
  assert.equal(nodes['model-jev-error'].hidden, false);
  assert.match(nodes['model-jev-error'].textContent, /no_key/);
  assert.equal(nodes['model-laya-error'].hidden, true, 'nothing reached Laya\'s column');
  assert.equal(nodes['ask-jev'].disabled, false, 'jev can be asked again');

  nodes['ask-laya'].click();
  const l = await nextRequest();
  assert.equal(l.url, '/api/agents/laya');
  assert.deepEqual(JSON.parse(l.init.body), { trace: 'runs_c4/5/1', step: 0 });
  assert.equal(nodes['model-laya-status'].textContent, AR('agents.models.laya.status.starting'), 'the first press loads Laya');
  reply(l, LAYA_OK);
  const s = await nextRequest();
  assert.equal(s.url, '/api/agents/laya/status', 'the Laya status is read again after its answer');
  // Before that re-fetch answers, the answer itself already says Laya is loaded.
  assert.equal(nodes['model-laya-status'].textContent, AR('agents.models.laya.status.ready').replace('{device}', 'cuda'),
    'the status line waits for the re-fetch beside an answer the loaded worker gave');
  reply(s, LAYA_READY);
  await settle();
  assert.equal(nodes['model-laya-error'].hidden, true);
  assert.equal(nodes['model-jev-error'].hidden, false, 'jev keeps its own error');
  const rows = rowsOf('laya');
  assert.equal(rows.length, 5, 'one row per action');
  assert.equal(byClass(rows[0], 'changed').length, 1, 'spark changed with the order');
  for (const row of rows.slice(1)) assert.equal(byClass(row, 'held').length, 1, 'the other four held');
  assert.equal(byClass(rows[0], 'model-bar').length, 5, 'five bars, one per level');
  assert.equal(byClass(rows[0], 'chosen').length, 1, 'exactly one of them chosen');
  assert.equal(rowsOf('jev').length, 0, 'no rows in jev\'s column');
  assert.match(nodes['model-laya-latency'].textContent, /70 ms/);
  assert.match(nodes['model-laya-latency'].textContent, /6\.1/, 'the first-load seconds');
  assert.equal(nodes['model-laya-status'].textContent, AR('agents.models.laya.status.ready').replace('{device}', 'cuda'));
  assert.match(nodes['model-laya-name'].textContent, /laya-rl-agent/);
});

// Starts from: second 0 answered by Laya, jev's no_key at second 0.
test('pausing back at an asked second shows its answer, with no new request', async () => {
  seekTo(2.5);
  assert.equal(rowsOf('laya').length, 0, 'second 2 was never asked');
  assert.equal(nodes['model-laya-reason'].textContent, AR('agents.models.ask_this'));
  assert.equal(nodes['model-jev-error'].hidden, true, 'jev\'s error belongs to second 0');
  seekTo(0.5);
  assert.equal(rowsOf('laya').length, 5, 'second 0\'s answer is shown again');
  assert.equal(nodes['model-jev-error'].hidden, false);
  await settle();
  assert.equal(requests.length, 0, 'no new request');
});

// Starts from: second 0, both columns holding an entry.
test('an answer that arrives after «احسب» belongs to nobody', async () => {
  nodes['ask-laya'].click();
  const late = await nextRequest();
  assert.equal(late.url, '/api/agents/laya');
  nodes.compute.click();
  const episode = await nextRequest();
  assert.match(episode.url, /^\/api\/agents\/episode\?/);
  assert.equal(rowsOf('laya').length, 0, '«احسب» empties both columns');
  assert.equal(nodes['model-jev-error'].hidden, true);
  reply(late, LAYA_OK);
  const status = await nextRequest();
  assert.equal(status.url, '/api/agents/laya/status');
  reply(status, LAYA_READY);
  await settle();
  assert.equal(rowsOf('laya').length, 0, 'the old episode\'s answer was dropped');
  assert.equal(nodes['ask-laya'].disabled, true, 'the new episode is not finished yet');
  reply(episode, READY);
  await settle();
  assert.equal(nodes['ask-laya'].disabled, false, 'free again once the new episode is finished');
  assert.equal(rowsOf('laya').length, 0, 'nothing carried over to the new episode');
});
```

In `app/test_agents.py`, make two Edits.

The first is in `PageTests.test_page_assets_ids`. old_string:

```python
        for spec in specs:
            self.assertTrue((self.STATIC / "sim" / spec[2:]).is_file(), f"agents.mjs imports missing {spec}")
```

new_string:

```python
        for spec in specs:
            self.assertTrue((self.STATIC / "sim" / spec[2:]).is_file(), f"agents.mjs imports missing {spec}")
        # M3: the gesture and the panel's pure logic (design 7.2), both static.
        for spec in ("./tap-unlock.mjs", "./model-panel.mjs"):
            self.assertIn(spec, specs, f"agents.mjs does not import {spec}")
```

The second is in `PageTests.test_chase_is_optional`. old_string:

```python
        self.assertTrue({"agent-view.mjs", "agents-strings.mjs", "i18n.mjs", "playback.mjs"} <= seen,
```

new_string:

```python
        self.assertTrue({"agent-view.mjs", "agents-strings.mjs", "i18n.mjs", "playback.mjs",
                         "tap-unlock.mjs", "model-panel.mjs"} <= seen,
```

- [ ] **Step 6: Run them to verify they fail**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
node --test app/static/sim/agents-page-models.test.mjs 2>&1 | grep -E "^✖|^✔|^ℹ (tests|pass|fail)|AssertionError|Error:" | head -20
$PY -m app.test_agents PageTests 2>&1 | grep -E "FAIL:|AssertionError|^Ran|^OK|^FAILED" | cut -c1-240
```

Expected, measured 28 Sep on a copy of the tree with Task 7 applied:
- Node: `ℹ tests 6`, `ℹ pass 1`, `ℹ fail 5`.
  - The first test, «locked, nothing is asked…», already passes. It pins that the wiring keeps the locked page untouched.
  - `✖ nine taps unlock nothing; the tenth shows the panel…` / `AssertionError [ERR_ASSERTION]: the tenth tap shows the panel`.
  - The two tests that wait for a POST end with `Error: no request arrived within 3000 ms`.
- Python: `FAILED (failures=2)`, with:
  - `FAIL: test_page_assets_ids`: `AssertionError: './tap-unlock.mjs' not found in ['./i18n.mjs', './playback.mjs', './agent-view.mjs', './agent-picker.mjs', './agents-strings.mjs', './agent-scene.mjs'] : agents.mjs does not import ./tap-unlock.mjs`;
  - `FAIL: test_chase_is_optional`: `AssertionError: False is not true : the static graph scan found only [...]`.

- [ ] **Step 7: Implement the wiring in agents.mjs**

Make ten Edits in `app/static/sim/agents.mjs`. At this point every old_string is unique; the 28 Sep prototype asserted each one.

1. The imports. old_string `} from './agent-picker.mjs';` (`:32`), new_string:

```js
} from './agent-picker.mjs';
import { createTapUnlock } from './tap-unlock.mjs';
import {
  MODELS, askState, createAnswers, rowView, failureOf, errorText, statusLine,
} from './model-panel.mjs';
```

2. The end of `state` (`:76-77`). old_string:

```js
  rows: [],        // the five action rows of the pause panel, built per meta
};
```

new_string:

```js
  rows: [],        // the five action rows of the pause panel, built per meta
};

// M3: jev and Laya, behind ten taps on the footer label (design 7.7). The
// unlock lives only in this module variable, so a reload forgets it; the
// gesture hides the panel and protects nothing. Each model has its own
// status, its own request in flight and its own answers, one per second of
// the episode on screen, so a jev failure never touches Laya's column and the
// reverse. Nothing here is saved, averaged, applied or compared with the
// agents.
const models = {
  unlocked: false,
  gesture: createTapUnlock({ taps: 10, windowMs: 4000 }),
  jev: { status: null, statusFailure: null, inFlight: false, answers: createAnswers(), drawn: null },
  laya: { status: null, statusFailure: null, inFlight: false, answers: createAnswers(), drawn: null },
};
```

3. `compute()` (`:199-200`). old_string:

```js
  state.lastK = -2;
  showError(null);
```

new_string:

```js
  state.lastK = -2;
  for (const name of MODELS) models[name].answers.clear();
  showError(null);
```

4. `clearEpisode()` (`:458-459`). old_string:

```js
  state.lastK = -2;
  state.drawnTime = -1;
```

new_string:

```js
  state.lastK = -2;
  state.drawnTime = -1;
  for (const name of MODELS) models[name].answers.clear();
```

5. Hook 1, `renderPanel` (`:1025-1027`). old_string:

```js
  renderReadings(frame);
  renderStopped();
}
```

new_string:

```js
  renderReadings(frame);
  renderStopped();
  renderModels();
}
```

6. The models block. Insert it immediately before the line `// ---------------------------------------------------------------- per frame` (`:1029`). The old_string is that one line and its newline; the new_string is the block below, ending with the same line:

```js
// ---------------------------------------------------------------- models (M3)
// Every id is written out, so app/test_agents.py's id scan can see it; never
// build one with a template literal.
function modelNodes(name) {
  return name === 'jev'
    ? {
      name: $('model-jev-name'), where: null, status: $('model-jev-status'), ask: $('ask-jev'),
      reason: $('model-jev-reason'), latency: $('model-jev-latency'), error: $('model-jev-error'),
      rows: $('model-jev-rows'), sent: $('model-jev-sent-body'),
    }
    : {
      name: $('model-laya-name'), where: $('model-laya-where'), status: $('model-laya-status'), ask: $('ask-laya'),
      reason: $('model-laya-reason'), latency: $('model-laya-latency'), error: $('model-laya-error'),
      rows: $('model-laya-rows'), sent: $('model-laya-sent-body'),
    };
}

// What askState (model-panel.mjs) decides from: playback stopped is the play
// button showing play, the predicate syncPlayButton uses, which also holds at
// the natural end of an episode, where userPaused stays false (design C10).
function askView(name) {
  return {
    playing: state.play.clock.playing, waiting: isWaiting(), done: state.done,
    frames: state.frames, inFlight: models[name].inFlight,
  };
}

async function loadModelStatus(name) {
  const m = models[name];
  try {
    const res = await fetch(`/api/agents/${name}/status`, { headers: { Accept: 'application/json' }, cache: 'no-store' });
    const body = await res.json().catch(() => null);
    if (res.status === 200 && body) { m.status = body; m.statusFailure = null; } else m.statusFailure = failureOf(res.status, body);
  } catch (err) {
    m.statusFailure = failureOf(null, null);
  }
  renderModels();
}

// One press: the paused second of the episode on screen, and nothing else.
// The key, the second and the load token are taken at press time; an answer
// is kept only if no «احسب» or pick moved loadToken while it was in flight,
// so a late answer (a paid one included) is never shown against another
// episode. inFlight is reset however the request ends.
async function askModel(name) {
  const m = models[name];
  const k = state.lastK;
  const key = state.metaKey;
  if (key === null || !askState(askView(name), k).enabled) return;
  const token = state.loadToken;
  m.inFlight = true;
  renderModels();
  let entry;
  try {
    const res = await fetch(`/api/agents/${name}`, {
      method: 'POST', cache: 'no-store',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ trace: key, step: k }),
    });
    const body = await res.json().catch(() => null);
    entry = res.status === 200 && body && body.answers ? { body } : { failure: failureOf(res.status, body) };
  } catch (err) {
    entry = { failure: failureOf(null, null) };
  }
  m.inFlight = false;
  if (token === state.loadToken) m.answers.put(key, k, entry);
  // A Laya answer is itself proof that its worker is loaded, so the status
  // line says so now rather than "loads on the first question" beside the
  // answer. The re-fetch below stays the authority: a press may have started,
  // stopped or failed the worker.
  if (name === 'laya' && entry.body) {
    m.status = {
      ...(m.status || {}), configured: true, worker: 'ready', problem: null,
      device: entry.body.device ?? null, laya: entry.body.laya ?? null,
    };
    m.statusFailure = null;
  }
  if (name === 'laya') loadModelStatus('laya').catch(err => console.error(err));
  renderModels();
}

// One row per action, in ACTIONS order, with the pause panel's own labels and
// units: what the two agents applied in this second (nothing subtracted), the
// model's choice in physical and network units, five bars labelled with the
// physical levels, the chosen option's probability, and, for Laya, the choice
// with the options reversed and whether it held. Model levels are never drawn
// on the agents' gauges.
function renderModelRows(host, body, frame) {
  host.textContent = '';
  if (!body) return;
  ACTIONS.forEach((action, i) => {
    const v = rowView(body, i);
    if (!v) return;
    const row = el('div', 'model-row');
    const head = el('div', 'action-head');
    head.appendChild(el('span', 'action-label', t(currentLang, action.label)));
    if (action.unit) {
      const unit = el('span', 'action-unit', action.unit);
      unit.dir = 'ltr';
      head.appendChild(unit);
    }
    row.appendChild(head);
    const ref = el('p', 'model-reference', t(currentLang, 'agents.models.reference'));
    LANES.forEach((lane, j) => {
      const car = carOf(frame, j);
      const span = el('span', lane);
      const value = el('b', '', fmtAction(i, car ? car.act?.[i] : null));
      value.dir = 'ltr';
      span.append(el('i', 'lane-dot'), value);
      ref.appendChild(span);
    });
    row.appendChild(ref);
    row.appendChild(el('p', 'model-choice',
      t(currentLang, 'agents.models.choice', { level: fmtAction(i, v.level), net: fmt(v.net, 3) })));
    const bars = el('div', 'model-bars');
    for (const b of v.bars) {
      const bar = el('div', b.chosen ? 'model-bar chosen' : 'model-bar');
      const fill = el('i');
      fill.style.width = `${(Math.max(0, Math.min(1, num(b.p) ?? 0)) * 100).toFixed(1)}%`;
      bar.append(el('span', 'bar-label', fmtAction(i, b.level)), fill, el('span', 'bar-p', fmt(b.p, 2)));
      bars.appendChild(bar);
    }
    row.appendChild(bars);
    row.appendChild(el('p', 'model-chosen-p', t(currentLang, 'agents.models.chosen_p', { p: fmt(v.chosenP, 2) })));
    if (v.reversed) {
      const order = el('p', 'model-order');
      order.append(el('span', '', t(currentLang, 'agents.models.reversed', { level: fmtAction(i, v.reversed.level) })),
        el('b', v.verdict, t(currentLang, v.verdict === 'held' ? 'agents.models.held' : 'agents.models.changed')));
      row.appendChild(order);
    }
    host.appendChild(row);
  });
}

// Both columns, each from its own state only. Returns at once while locked,
// so the locked page is M2's page.
function renderModels() {
  if (!models.unlocked) return;
  const k = state.lastK;
  const key = state.metaKey;
  const frame = k >= 0 ? state.frames[k] || null : null;
  for (const name of MODELS) {
    const m = models[name];
    const n = modelNodes(name);
    const entry = key !== null && k >= 0 ? m.answers.get(key, k) : null;
    const body = entry?.body ?? null;
    const s = askState(askView(name), k);
    if (n.ask) n.ask.disabled = !s.enabled;
    setText(n.reason, s.enabled ? (entry ? '' : t(currentLang, 'agents.models.ask_this')) : t(currentLang, s.reason));
    setText(n.status, statusLine(name, m.status, m.statusFailure, m.inFlight, currentLang));
    if (name === 'jev') {
      setText(n.name, t(currentLang, 'agents.models.jev.name', { model: body?.model_name || m.status?.model || EM_DASH }));
      setText(n.latency, body ? t(currentLang, 'agents.models.jev.latency', { ms: fmt(body.ms, 0) }) : '');
    } else {
      const device = body?.device || m.status?.device || t(currentLang, 'agents.models.laya.device_unknown');
      setText(n.name, t(currentLang, 'agents.models.laya.name', {
        model: body?.model_name || EM_DASH, version: body?.laya || m.status?.laya || EM_DASH,
      }));
      setText(n.where, t(currentLang, 'agents.models.laya.where', { device }));
      const first = body && num(body.started_s) !== null
        ? ` · ${t(currentLang, 'agents.models.laya.first_load', { s: fmt(body.started_s, 1) })}` : '';
      setText(n.latency, body
        ? `${t(currentLang, 'agents.models.laya.latency', { ms: fmt(body.ms, 0), device: body.device || EM_DASH })}${first}`
        : '');
    }
    const failure = entry?.failure ?? null;
    if (n.error) n.error.hidden = !failure;
    setText(n.error, failure ? errorText(failure.code, failure.status, currentLang, failure.kind) : '');
    const drawnNow = [currentLang, key, k, entry];
    if (n.rows && !(m.drawn && drawnNow.every((v, i) => v === m.drawn[i]))) {
      m.drawn = drawnNow;
      renderModelRows(n.rows, body, frame);
    }
    setText(n.sent, body ? JSON.stringify(body.sent, null, 2) : '');
  }
}

// ---------------------------------------------------------------- per frame
```

7. Hook 5, `renderAll` (`:1066-1069`). old_string:

```js
  syncPlayButton();
  draw(state.play.clock.time, true);
}
```

new_string:

```js
  syncPlayButton();
  draw(state.play.clock.time, true);
  renderModels();
}
```

8. Hook 3, the loop's play-state branch (`:1110`). old_string `  if (on !== state.wasPlaying) { state.wasPlaying = on; syncPlayButton(); renderTimeline(); }`, new_string `  if (on !== state.wasPlaying) { state.wasPlaying = on; syncPlayButton(); renderTimeline(); renderModels(); }`.

9. Hook 2, the play and restart handlers. The first old_string (`:1118-1121`):

```js
    else playOrWait(state.play, state.frames.length * DT, state.done, now);
    syncPlayButton();
    renderTimeline();
  });
```

new_string:

```js
    else playOrWait(state.play, state.frames.length * DT, state.done, now);
    syncPlayButton();
    renderTimeline();
    renderModels();
  });
```

The second old_string (`:1126-1129`):

```js
    syncPlayButton();
    renderTimeline();
    draw(0, true);
  });
```

new_string:

```js
    syncPlayButton();
    renderTimeline();
    draw(0, true);
    renderModels();
  });
```

10. The gesture and the two buttons, in `start()` (`:1142`). old_string `  $('compute')?.addEventListener('click', compute);`, new_string:

```js
  $('compute')?.addEventListener('click', compute);
  // Ten taps within four seconds on the footer label, and only there (the
  // lab's 01 — REPLAY gets no handler). Each status is fetched on its own, so
  // a failed one fills only its own column.
  $('footer-index')?.addEventListener('click', () => {
    if (models.unlocked || !models.gesture.tap(performance.now())) return;
    models.unlocked = true;
    const panel = $('models-panel');
    if (panel) panel.hidden = false;
    renderModels();
    for (const name of MODELS) loadModelStatus(name).catch(err => console.error(err));
  });
  $('ask-jev')?.addEventListener('click', () => { askModel('jev').catch(err => console.error(err)); });
  $('ask-laya')?.addEventListener('click', () => { askModel('laya').catch(err => console.error(err)); });
```

The status update in `askModel` is what the new assertion in «a jev failure stays in jev's column…» pins. Measured 28 Sep: with this block minus the `if (name === 'laya' && entry.body)` update, that test alone fails with `the status line waits for the re-fetch beside an answer the loaded worker gave`, `actual: 'يُحمَّل عند أول سؤال'`, `expected: 'محمَّل على cuda حتى يُغلق الخادم'`. With the update, it passes.

- [ ] **Step 8: Byte-check, then run to verify it passes**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
$PY -c "import pathlib; b = pathlib.Path('app/static/sim/agents.mjs').read_text(encoding='utf-8'); print('literal', sum(b.count(chr(c)) for c in (0x202F, 0x2212, 0x200F, 0x2066, 0x2068, 0x2069, 0x2011)), 'escapes', b.count(chr(92) + 'u202f'), b.count(chr(92) + 'u2212'))"
node --test app/static/sim/agents-page-models.test.mjs 2>&1 | grep -E "^✖|^✔|^ℹ (tests|pass|fail)"
node --test "app/static/sim/*.test.mjs" 2>&1 | grep -E "^✖|^ℹ (tests|pass|fail|skipped)"
$PY -m app.test_agents PageTests NoWriteTests 2>&1 | grep -E "FAIL:|ERROR:|^Ran|^OK|^FAILED"
```

Expected:
- `literal 0 escapes 1 1`, the same as at d347ee5.
- The models file: six `✔` lines, `ℹ tests 6`, `ℹ pass 6`, `ℹ fail 0`.
- The glob: `ℹ fail 0`, with no `✖` line. The total is Task 7's count plus 7: one test in `agents-page.test.mjs` and six in the new file. On the 28 Sep copy it went from 126 to 133. That copy has no `app/node_modules`, so 8 of its scene tests skipped; the repository reads `ℹ skipped 0`.
- Python: `OK`, with the count read from the run.

- [ ] **Step 9: Commit**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
$PY -m app.test_agents > "$SCRATCH/m3_t8_agents.txt" 2>&1; grep -E "^Ran|^OK|FAILED|PROVEN" "$SCRATCH/m3_t8_agents.txt"
$PY -m app.test_replay > "$SCRATCH/m3_t8_replay.txt" 2>&1; tail -1 "$SCRATCH/m3_t8_replay.txt"
node --test "app/static/sim/*.test.mjs" > "$SCRATCH/m3_t8_node.txt" 2>&1; grep -E "^ℹ (tests|pass|fail|skipped)" "$SCRATCH/m3_t8_node.txt"
git add app/static/agents.html app/static/sim/agents.css app/static/sim/agents.mjs app/static/sim/agents-page-harness.mjs app/static/sim/agents-page.test.mjs app/static/sim/agents-page-models.test.mjs app/test_agents.py
$PY verify_docs.py 2>&1 | tail -1
```

Use a timeout of 600000 ms for this block. Expected:
- `OK` (`(skipped=N)` counts the `--full`-only tests), and the `PROVEN` line.
- `49 of 49 checks pass`, or the count read from the run.
- `ℹ fail 0`.
- verify_docs's last line starts `All ` and ends `figure mentions scanned in the documents).`

If test 11's snapshot raises because another session wrote to the tree, re-run with HEAD unchanged before and after, and record it (M2's known limit).

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
{
  printf '%s\n' "Agent replay M3 (6b/7): the hidden models panel, wired; two buttons, independent" "" \
    "#models-panel is static in agents.html (hidden, every id written out) after" \
    "the pause panel; ten taps within 4 s on #footer-index unhide it and fetch" \
    "both status routes, each on its own. One button, lock, answer map and error" \
    "per model: askModel POSTs {trace: metaKey, step: lastK} and keeps the answer" \
    "only if loadToken did not move; a Laya answer marks its worker ready before" \
    "the status re-fetch returns; renderModels runs from renderPanel, the play and" \
    "restart handlers, the loop's play-state branch, each answer and renderAll;" \
    "compute() and clearEpisode() empty both maps. The harness records fetch init." \
    "Tests: agents-page-models.test.mjs (6), the models CSS and honesty lines in" \
    "agents-page.test.mjs, test 12 (the section, both imports, the static graph)."
  printf '\n$ python -m app.test_agents   (summary)\n'; grep -E "^Ran|^OK|FAILED|PROVEN" "$SCRATCH/m3_t8_agents.txt"
  printf '\n$ node --test "app/static/sim/*.test.mjs"   (summary)\n'; grep -E "^ℹ " "$SCRATCH/m3_t8_node.txt"
  printf '\n$ python verify_docs.py   (last line)\n'; $PY verify_docs.py 2>&1 | tail -1
  printf '\n$ python -m app.test_replay\n'; cat "$SCRATCH/m3_t8_replay.txt"
  printf '\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n'
} > "$SCRATCH/m3_t8_msg.txt"
git commit -F "$SCRATCH/m3_t8_msg.txt" -- app/static/agents.html app/static/sim/agents.css app/static/sim/agents.mjs app/static/sim/agents-page-harness.mjs app/static/sim/agents-page.test.mjs app/static/sim/agents-page-models.test.mjs app/test_agents.py
git log --oneline -1
```

Expected: one new commit on `JMF-2340550-sep17` whose subject starts `Agent replay M3 (6b/7)`.

---


---

### Task 9: fe-page: the pause panel moves under the play bar (the models panel with it), orders 5/6/7 below 1100 px, and the '—' empty state becomes agents.pause.empty (Jad's decision, design 7.8 option 1)

**Files:**
- Modify: `app/static/agents.html`. The pause panel and `#models-panel`, which Task 8 left in the aside, move to right after the transport (`:67`) and before `<article class="profile-panel">`. `#pause-heading`'s text changes.
- Modify: `app/static/sim/agents.css:19-21` (layout comment), `:80` (card comment), `:129-131` (<1100 comment), `:135` (the order list)
- Modify: `app/static/sim/agents.mjs:1017` (`renderPanel`'s heading)
- Modify: `app/static/sim/agents-page-nav.test.mjs:251`, `:255`, `:264`
- Modify: `app/static/sim/agents-page.test.mjs` (append one test)
- Test: `app/static/sim/agents-page.test.mjs`, `app/static/sim/agents-page-nav.test.mjs`

**Interfaces:**
- Consumes:
  - Task 8's `agents.html`, with `#models-panel` right after the pause panel in the side column.
  - Task 8's <1100 list, which ends `.profile-panel{order:5}.pause-panel{order:6}.models-panel{order:7}`.
  - Task 7's string `agents.pause.empty`: in Arabic «اضغط احسب، ثم أوقف العرض عند أي ثانية لترى ما قرّره كل وكيل»; in English "Press Compute, then pause at any second to see what each agent decided".
  - `agents-page-nav.test.mjs`'s `AR = key => STRINGS.ar[key]` (`:58`).
- Produces:
  - In `.agents-col-main`: transport, pause panel, models panel, profile. The aside holds the picker and the verdict only.
  - Below 1100 px: picker 1, verdict 2, chase 3, transport 4, pause 5, profile 6, models 7.
  - `<h2 id="pause-heading" data-i18n="agents.pause.empty">`, followed by the Arabic empty line.
  - `renderPanel` writes `t(currentLang, 'agents.pause.empty')` when there is no frame.

**Code wins over the skeleton in one place.** The skeleton said the static `h2#pause-heading` takes the Arabic line "with no data-i18n". But `draw()` returns before `renderPanel` while there is no road (`agents.mjs:1033`), so at boot `renderPanel` never runs. In the prototype's browser check in English, the Arabic line stayed under an English page, which is a FAIL. The h2 therefore carries `data-i18n="agents.pause.empty"`. `applyTranslations` writes it in the page's language, and `renderPanel` overwrites it once a frame exists: `applyLanguage` runs `applyTranslations`, then `renderAll`, which redraws the panel. The key has no placeholder, so the markup rule of `agents-page.test.mjs` holds. With this change the English view passed.

Write every code block with the Write or Edit tool; the new test carries doubled backslashes.

- [ ] **Step 1: Write the failing tests**

Append at the end of `app/static/sim/agents-page.test.mjs`:

```js

// Jad did not find the pause panel on 28 Sep: at 1440 x 900 it started 957 px
// below the fold, under the verdict box, and before «احسب» it said only "—"
// (M3 design 7.8, his option 1). It now sits right under the play bar in the
// main column, the models panel right after it, and before an episode it says
// what to do. Below 1100 px the one column keeps transport, pause panel,
// profile, models panel.
test('the pause panel sits under the play bar, the models panel right after it, and phones keep that order', () => {
  const html = read(HTML);
  const main = html.slice(html.indexOf('<div class="agents-col agents-col-main">'), html.indexOf('<aside'));
  const side = html.slice(html.indexOf('<aside'), html.indexOf('</aside>'));
  const at = ['<section class="transport', '<section class="pause-panel">', '<section id="models-panel"',
    '<article class="profile-panel">'].map(marker => main.indexOf(marker));
  assert.ok(at.every(i => i >= 0), `the main column is missing the transport, a panel or the profile: ${at}`);
  assert.deepEqual([...at].sort((a, b) => a - b), at, 'transport, pause panel, models panel, profile, in that order');
  assert.equal(side.indexOf('pause-panel'), -1, 'the pause panel is still in the side column');
  assert.equal(side.indexOf('models-panel'), -1, 'the models panel is still in the side column');
  // data-i18n, because draw() returns before renderPanel while there is no
  // road: without it an English page would keep this Arabic line until an
  // episode arrives. renderPanel overwrites it once a frame exists.
  assert.ok(html.includes(`<h2 id="pause-heading" data-i18n="agents.pause.empty">${STRINGS.ar['agents.pause.empty']}</h2>`),
    'before any episode, the pause panel says what to do, in the page\'s language, not "—"');
  const narrow = read(new URL('./agents.css', import.meta.url)).match(/@media\(max-width:1099px\)\{([\s\S]*?)\n\}/);
  assert.ok(narrow, 'agents.css has no <1100 px block');
  for (const [name, n] of [['agents-transport', 4], ['pause-panel', 5], ['profile-panel', 6], ['models-panel', 7]]) {
    assert.match(narrow[1], new RegExp(`\\.${name}\\{order:${n}\\}`), `.${name} must be order ${n} below 1100 px`);
  }
});
```

In `app/static/sim/agents-page-nav.test.mjs`, make three Edits. The test keeps its meaning, "the old episode left the pause panel"; only the text of the empty panel changes, to the new empty line.

1. old_string `  assert.notEqual(nodes['pause-heading'].textContent, '—', 'the episode is on screen');`, new_string `  assert.notEqual(nodes['pause-heading'].textContent, AR('agents.pause.empty'), 'the episode is on screen');`
2. old_string `  assert.equal(nodes['pause-heading'].textContent, '—', 'the old episode left the pause panel');`, new_string `  assert.equal(nodes['pause-heading'].textContent, AR('agents.pause.empty'), 'the old episode left the pause panel');`
3. old_string `  assert.equal(nodes['pause-heading'].textContent, '—', 'a late frame of the old key changed the page');`, new_string `  assert.equal(nodes['pause-heading'].textContent, AR('agents.pause.empty'), 'a late frame of the old key changed the page');`

- [ ] **Step 2: Run them to verify they fail**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
$PY -c "import pathlib; print(pathlib.Path('app/static/sim/agents-page.test.mjs').read_text(encoding='utf-8').count(chr(92)*2))"
node --test app/static/sim/agents-page.test.mjs app/static/sim/agents-page-nav.test.mjs 2>&1 | grep -E "^✖|^ℹ (tests|pass|fail)|AssertionError|actual|expected" | head -20
```

Expected, measured 28 Sep:
- `13`: Task 8 left 10, and this test adds 3.
- `ℹ tests 21`, `ℹ pass 19`, `ℹ fail 2`, with:
  - `✖ changing the pair after a computation clears the old episode and drops its late frames` / `AssertionError [ERR_ASSERTION]: the old episode left the pause panel`, `actual: '—'`, `expected: 'اضغط احسب، ثم أوقف العرض عند أي ثانية لترى ما قرّره كل وكيل'`;
  - `✖ the pause panel sits under the play bar, the models panel right after it, and phones keep that order` / `AssertionError [ERR_ASSERTION]: the main column is missing the transport, a panel or the profile: 1281,-1,-1,2858`.

- [ ] **Step 3: Implement**

The two panels span 51 lines of markup, so a script moves them rather than a 51-line Edit. Write `C:\Users\admin\AppData\Local\Temp\claude\c--Users-admin-Documents-graduation-project-GRAD-project\m3-build\m3_t9_move.py` with the Write tool. It contains no backslash apart from Python's `\n`:

```python
"""Agent replay M3, step 7 (design 7.8, Jad's option 1): move the pause panel
and the models panel from the side column to directly under the play bar, and
give the pause heading its empty-state line. Run once from the repository root.
"""
from pathlib import Path

p = Path("app/static/agents.html")
s = p.read_text(encoding="utf-8")
start = s.index('        <section class="pause-panel">\n')
end = s.index("      </aside>\n")
block = s[start:end]
assert block.count('<section class="pause-panel">') == 1, "the pause panel is not where Task 8 left it"
assert block.count('<section id="models-panel" class="models-panel" hidden>') == 1, "the models panel must follow the pause panel"
assert block.endswith("        </section>\n"), repr(block[-40:])
s = s[:start] + s[end:]
anchor = '        <article class="profile-panel">\n'
assert s.count(anchor) == 1
s = s.replace(anchor, block + anchor)
old = '<h2 id="pause-heading">—</h2>'
assert s.count(old) == 1
s = s.replace(old, '<h2 id="pause-heading" data-i18n="agents.pause.empty">اضغط احسب، ثم أوقف العرض عند أي ثانية لترى ما قرّره كل وكيل</h2>')
p.write_text(s, encoding="utf-8", newline="\n")
print("moved", block.count("\n"), "lines")
```

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
$PY "$(cygpath -w "$SCRATCH/m3_t9_move.py")"
git diff --stat app/static/agents.html
```

Expected: `moved 51 lines` (measured 28 Sep). The diffstat shows the same number of insertions and deletions, give or take the one heading line.

In `app/static/sim/agents.css`, make four Edits.

1. old_string:

```css
/* >= 1100 px: main column (chase, timeline, profile) | side column (picker,
   verdict, pause panel). The grid runs ltr and its children rtl, exactly as the
   lab's .lab-layout does, so the side column sits at the reading start. */
```

new_string:

```css
/* >= 1100 px: main column (chase, timeline, pause panel, models panel,
   profile) | side column (picker, verdict). The pause panel sits right under
   the play bar (M3 design 7.8: at 1440 x 900 it started 957 px below the fold
   in the side column). The grid runs ltr and its children rtl, exactly as the
   lab's .lab-layout does, so the side column sits at the reading start. */
```

2. old_string:

```css
/* side column */
.picker-panel,.verdict-panel,.pause-panel,.models-panel{
```

new_string:

```css
/* the cards: picker and verdict (side column), pause and models panels (main) */
.picker-panel,.verdict-panel,.pause-panel,.models-panel{
```

3. old_string:

```css
/* < 1100 px: one column, in reading order badge, picker, verdict, chase,
   timeline, profile, pause panel. The two column wrappers dissolve so their
   children can be ordered together. */
```

new_string:

```css
/* < 1100 px: one column, in reading order badge, picker, verdict, chase,
   timeline, pause panel, profile, models panel. The two column wrappers
   dissolve so their children can be ordered together. */
```

4. old_string `.agents-transport{order:4}.profile-panel{order:5}.pause-panel{order:6}.models-panel{order:7}`, new_string `.agents-transport{order:4}.pause-panel{order:5}.profile-panel{order:6}.models-panel{order:7}`.

In `app/static/sim/agents.mjs`, `renderPanel` (`:1017`), make one Edit. old_string:

```js
  setText($('pause-heading'), frame ? t(currentLang, 'agents.pause.heading', { k, k1: k + 1 }) : EM_DASH);
```

new_string:

```js
  setText($('pause-heading'), frame ? t(currentLang, 'agents.pause.heading', { k, k1: k + 1 })
    : t(currentLang, 'agents.pause.empty'));
```

`EM_DASH` stays, because the panel's other empty values still use it.

- [ ] **Step 4: Run to verify it passes**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
node --test app/static/sim/agents-page.test.mjs app/static/sim/agents-page-nav.test.mjs 2>&1 | grep -E "^✖|^ℹ (tests|pass|fail)"
node --test "app/static/sim/*.test.mjs" 2>&1 | grep -E "^✖|^ℹ (tests|pass|fail|skipped)"
$PY -m app.test_agents PageTests 2>&1 | grep -E "FAIL:|ERROR:|^Ran|^OK|^FAILED"
grep -n "agents-col-side" -A 21 app/static/agents.html | grep -E "<section|</aside>"
```

Expected:
- The two files: `ℹ tests 21`, `ℹ pass 21`, `ℹ fail 0`.
- The glob: `ℹ fail 0`, `ℹ skipped 0`, and a total one higher than after Task 8 (133 to 134 on the 28 Sep copy).
- PageTests: `OK`. The id scan and the section check do not depend on where the panels sit.
- The grep shows only `<section class="picker-panel">`, `<section id="verdict" …>` and `</aside>`.

- [ ] **Step 5: Commit**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
$PY -m app.test_replay > "$SCRATCH/m3_t9_replay.txt" 2>&1; tail -1 "$SCRATCH/m3_t9_replay.txt"
node --test "app/static/sim/*.test.mjs" > "$SCRATCH/m3_t9_node.txt" 2>&1; grep -E "^ℹ (tests|pass|fail|skipped)" "$SCRATCH/m3_t9_node.txt"
git add app/static/agents.html app/static/sim/agents.css app/static/sim/agents.mjs app/static/sim/agents-page-nav.test.mjs app/static/sim/agents-page.test.mjs
$PY verify_docs.py 2>&1 | tail -1
{
  printf '%s\n' "Agent replay M3 (7/7): the pause panel under the play bar; an empty state that says what to do" "" \
    "Jad's decision (M3 design 7.8, option 1): the pause panel and the models" \
    "panel move from the side column to directly under the play bar; below 1100 px" \
    "the order is transport 4, pause 5, profile 6, models 7. Before an episode the" \
    "pause heading reads agents.pause.empty instead of '-'. The h2 carries" \
    "data-i18n because draw() returns before renderPanel without a road, so an" \
    "English page would otherwise keep the Arabic line. No honesty surface moves." \
    "Tests: the layout and phone order in agents-page.test.mjs; the three" \
    "agents-page-nav.test.mjs heading checks now expect the empty line."
  printf '\n$ node --test "app/static/sim/*.test.mjs"   (summary)\n'; grep -E "^ℹ " "$SCRATCH/m3_t9_node.txt"
  printf '\n$ python verify_docs.py   (last line)\n'; $PY verify_docs.py 2>&1 | tail -1
  printf '\n$ python -m app.test_replay\n'; cat "$SCRATCH/m3_t9_replay.txt"
  printf '\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n'
} > "$SCRATCH/m3_t9_msg.txt"
git commit -F "$SCRATCH/m3_t9_msg.txt" -- app/static/agents.html app/static/sim/agents.css app/static/sim/agents.mjs app/static/sim/agents-page-nav.test.mjs app/static/sim/agents-page.test.mjs
git log --oneline -1
```

Expected:
- `49 of 49 checks pass`, read from the run.
- `ℹ fail 0`.
- verify_docs's last line reads `All … scanned in the documents).`
- One commit whose subject starts `Agent replay M3 (7/7)`.

---


---

### Task 10: M3 verification: every suite (--full with LAYA_HOME so test 20 runs), the browser at 1440 and 390 px locked and unlocked, a real Laya press with its order check, reload hides, the natural end enables both buttons, jev with no key while Laya answers, jev forced to fail with no network call, shutdown by hard kill, by Ctrl+C and by closing the window leaves no Laya python, LAYA_HOME unchanged

**Files:**
- Create (scratch only, never in the repository). Each file is written with the Write tool under `C:\Users\admin\AppData\Local\Temp\claude\c--Users-admin-Documents-graduation-project-GRAD-project\m3-build\`:
  - `m3_laya_snapshot.py`
  - `m3-browser-check.mjs`
  - `m3_console.py`
  - `m3_shutdown.ps1`
  - `m3_kill_running.ps1`
  - `m3_proxy_gate.py`

  The run's outputs go to `m3-out\`, `m3_*.txt` and `m3-verification.txt` in the same folder.
- Modify: none.
- Test: the suites; the browser check; the shutdown checks.

**Interfaces:**
- Consumes:
  - Tasks 1-9, all committed.
  - `app/server.py main()`, run as `$PY -m app.server --simulation --http-port <port>` from the repository root.
  - Chrome at `C:/Program Files/Google/Chrome/Application/chrome.exe`, driven over the DevTools protocol with Node 24's `fetch` and `WebSocket`, as in M1 Task 11 and M2 Task 10.
  - Test 20's observation line, `print(f"\n    Laya: {ready['device']}, laya …", file=sys.stderr)`. Task 5 prints it only after every assertion of `test_real_laya` has passed. Its skip message starts `LAYA_HOME is not set in this process, so the real Laya is UNPROVEN`.
- Produces: `$SCRATCH/m3-verification.txt`. Task 11's amendment script parses it by these section headers (lines starting `$ `), so they are fixed:
  - `$ LAYA_HOME=... python -m app.test_agents --full …`
  - `$ route probes …`
  - `$ browser check, full …`
  - `$ shutdown: kill …`
  - `$ shutdown: Ctrl+C …`
  - `$ shutdown: closing …`
  - `$ jev forced to fail …`
  - `$ LAYA_HOME before/after`

This task verifies rather than builds, so its steps run suites and checks, not a red/green cycle. The browser check was measured on 28 Sep against a prototype that served Tasks 7-9's page with the skeleton's four routes and a **fake** Laya worker (3 s to load). The shutdown checks were measured against the same routes with a fake worker in a file named `laya_worker.py`. Read every count from your own run. This task makes no commit.

**Three facts measured on 28 Sep that shape the checks. Code wins over the design here:**
1. **Laya's `.venv/Scripts/python.exe` is a launcher.** The interpreter runs as its child, from the base Python that `pyvenv.cfg` names (`C:\Users\admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`), so its path is not under `.venv`. Killing the launcher killed the child: 0 left 1 s after `Stop-Process`. The shutdown checks therefore find the worker by its command line (`*laya_worker.py*`), which matches both processes.
2. **"Network off" is a refused local proxy.** An agent cannot switch the network off, and with a dummy key on a working network the call would reach api.typesafe.ai. The jev-fail server gets `HTTPS_PROXY`/`HTTP_PROXY=http://127.0.0.1:9` and an empty `NO_PROXY` in its own environment. A gate runs first: urllib must pick that proxy, and 127.0.0.1:9 must refuse. Windows answers a closed local port after about 2 s (measured 2.04 s), so the gate waits 5 s.
3. **Ctrl+C and closing the window are done from outside, on a console of the server's own.** `m3_shutdown.ps1` starts the server under `conhost.exe`, which gives it a classic console window whatever the default terminal is. `m3_console.py` then attaches to that console and either generates `CTRL_C_EVENT` on it, which is what the key press does, or posts `WM_CLOSE` to its window, which is what the close button sends. `Process.CloseMainWindow()` does not work here: it returned false for the conhost process (measured), so the helper finds the window through `GetConsoleWindow()` instead. The prototype results, one run each, fake worker: Ctrl+C 0 left, close 0 left, hard kill 0 left. Ctrl+C reached the server although it was started from the agent's PowerShell.

**No real jev call is ever made.** Step 1 stops the task if a key exists on this machine.

Every Bash block starts with the environment line from Task 8, written out. The PowerShell steps use the literal Windows path of the same folder.

- [ ] **Step 1: No key, and the LAYA_HOME snapshot before anything runs Laya**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
env -u TYPESAFE_API_KEY $PY -c "from app.jev import load_key; print(load_key())" | tee "$SCRATCH/m3_key.txt"
```

Expected: `(None, None)`. **If anything else prints, stop this task.** A key in `%APPDATA%\grad-project\typesafe_key` would turn the browser check's jev press into a real, paid call. Report it to the controller and go no further.

Write `C:\Users\admin\AppData\Local\Temp\claude\c--Users-admin-Documents-graduation-project-GRAD-project\m3-build\m3_laya_snapshot.py` with the Write tool:

```python
"""Task 10: a (path, size, mtime_ns) snapshot of LAYA_HOME, read-only.

    python m3_laya_snapshot.py take <out.json>      LAYA_HOME from the environment
    python m3_laya_snapshot.py compare <a.json> <b.json>
Writes only the JSON it is given, which must be in the scratch folder.
"""
import json
import os
import sys
from pathlib import Path


def take(home):
    files = {}
    for root, dirs, names in os.walk(home):
        for name in names:
            p = Path(root) / name
            try:
                st = p.stat()
            except OSError:
                continue
            files[str(p.relative_to(home))] = [st.st_size, st.st_mtime_ns]
    return files


if sys.argv[1] == "take":
    home = os.environ["LAYA_HOME"]
    snap = take(home)
    Path(sys.argv[2]).write_text(json.dumps(snap), encoding="utf-8")
    print(f"LAYA_HOME snapshot: {len(snap)} files -> {sys.argv[2]}")
else:
    a = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    b = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
    changed = sorted(p for p in set(a) | set(b) if a.get(p) != b.get(p))
    print(f"LAYA_HOME: {len(a)} files before, {len(b)} after, {len(changed)} new, gone or changed")
    for p in changed[:20]:
        print("  ", p, a.get(p), "->", b.get(p))
    sys.exit(1 if changed else 0)
```

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
LAYA_HOME='C:\Users\admin\Documents\Local AI\laya' $PY "$(cygpath -w "$SCRATCH/m3_laya_snapshot.py")" take "$(cygpath -w "$SCRATCH/m3_laya_before.json")"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader | sed 's/^/before any server: /' | tee "$SCRATCH/m3_gpu.txt"
```

Expected: `LAYA_HOME snapshot: N files -> …` (N was 29467 on 28 Sep, taken in 2.4 s), and one GPU line.

- [ ] **Step 2: Run every suite**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
$PY -m app.test_agents > "$SCRATCH/m3_agents.txt" 2>&1; grep -E "^Ran|^OK|FAILED|PROVEN" "$SCRATCH/m3_agents.txt"
```

Use a timeout of 600000 ms. Expected:
- `OK`, where `(skipped=N)` counts the `--full`-only tests;
- the `== proof PROVEN: device cuda …` line;
- `Ran N tests`, read from the run.

Start the `--full` run with the Bash tool's `run_in_background`, as one self-contained command:

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"; env -u TYPESAFE_API_KEY LAYA_HOME='C:\Users\admin\Documents\Local AI\laya' "$PY" -m app.test_agents --full > "$SCRATCH/m3_agents_full.txt" 2>&1
```

When its completion notification arrives:

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
grep -E "^    Laya: |skipped 'LAYA_HOME|test_real_laya|^Ran|^OK|FAILED|PROVEN" "$SCRATCH/m3_agents_full.txt"
```

Expected:
- `test_real_laya (__main__.LayaRealTests.test_real_laya) ... `. unittest's verbose runner writes that test's `ok` on a line of its own, after test 20's observation line, so this grep does not show it.
- `    Laya: cuda, laya 0.3.20, first load … s, both requests … ms then … ms, input tokens …; order check (an observation, not asserted): {…}`. Test 20 prints this line only after every one of its assertions has passed, so **this line is the proof that test 20 ran**. The order-check pattern in it is an observation and is never asserted.
- **No** line containing `skipped 'LAYA_HOME`. That line would mean test 20 did not run.
- `OK`, and `Phase D == proof PROVEN on cuda`.

This format was reproduced on 28 Sep with a stand-in test that prints the same way: `test_real_laya (…) ... ` on one line, then the `    Laya: ` line, then `ok` alone.

Then:

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
$PY -m app.test_replay > "$SCRATCH/m3_replay.txt" 2>&1; tail -1 "$SCRATCH/m3_replay.txt"
$PY -m app.test_replay --full > "$SCRATCH/m3_replay_full.txt" 2>&1; tail -1 "$SCRATCH/m3_replay_full.txt"
$PY -m app.test_simulation > "$SCRATCH/m3_sim.txt" 2>&1; tail -3 "$SCRATCH/m3_sim.txt"
node --test "app/static/sim/*.test.mjs" > "$SCRATCH/m3_node.txt" 2>&1; grep -E "^✖|^ℹ (tests|pass|fail|skipped)" "$SCRATCH/m3_node.txt"
$PY verify_docs.py > "$SCRATCH/m3_verify_docs.txt" 2>&1; tail -1 "$SCRATCH/m3_verify_docs.txt"
git status --short
```

Expected:
- `49 of 49 checks pass`, and the `--full` count from its run.
- `Ran 15 tests`, `OK`.
- `ℹ fail 0` with no `✖` line, and `ℹ skipped 0`.
- verify_docs's last line reads `All … figure mentions scanned in the documents).`
- `git status --short` lists no M3 file.

If test 11's snapshot raised because another session wrote to the tree, re-run with HEAD unchanged before and after, and record it.

- [ ] **Step 3: Start the server with LAYA_HOME, and probe the four routes**

Start it with `run_in_background`:

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"; env -u TYPESAFE_API_KEY LAYA_HOME='C:\Users\admin\Documents\Local AI\laya' "$PY" -m app.server --simulation --http-port 8765 > "$SCRATCH/m3_server.txt" 2>&1
```

Then, in the foreground:

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
{
  for i in $(seq 1 40); do c=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 http://127.0.0.1:8765/agents); [ "$c" = "200" ] && break; sleep 1; done; echo "agents $c"
  curl -s -D - http://127.0.0.1:8765/api/agents/jev/status | grep -iE "^cache-control|configured"
  curl -s http://127.0.0.1:8765/api/agents/laya/status; echo
  curl -s -o /dev/null -w "POST laya without Origin %{http_code}\n" -X POST -H "Content-Type: application/json" -d '{"trace":"runs_c4/5/1","step":0}' http://127.0.0.1:8765/api/agents/laya
  curl -s -o /dev/null -w "POST laya with a bad body %{http_code} cache-control: [%header{cache-control}]\n" -X POST -H "Content-Type: application/json" -H "Origin: http://127.0.0.1:8765" -d '{"trace":"runs_c4/5/1","step":"0"}' http://127.0.0.1:8765/api/agents/laya
  curl -s -o /dev/null -w "GET /api/agents/laya %{http_code} cache-control: [%header{cache-control}]\n" http://127.0.0.1:8765/api/agents/laya
  curl -s -o /dev/null -w "GET /api/agents/laya/status %{http_code} cache-control: [%header{cache-control}]\n" http://127.0.0.1:8765/api/agents/laya/status
  curl -s http://127.0.0.1:8765/api/agents/laya/status; echo
} | tee "$SCRATCH/m3_probes.txt"
```

Expected:
- `agents 200`.
- `cache-control: no-store` and `{"configured":false,"source":null,"vendor":"typesafe.ai","model":"jev-latest","hosted":"USA"}`.
- `{"configured":true,"source":"env","problem":null,"worker":"stopped","device":null,"laya":null}`, both times: no status call and no refused POST starts the worker.
- `POST laya without Origin 403`.
- `POST laya with a bad body 422 cache-control: […]` and `GET /api/agents/laya 405 cache-control: […]`. These are FastAPI's own responses: the strict body is validated before the handler runs, and GET has no route. On the skeleton's routes both read `cache-control: []` (measured 28 Sep, curl 8.21.0). Record what the brackets hold. Task 11 writes an amendment from it and changes nothing here.
- `GET /api/agents/laya/status 200 cache-control: [no-store]`.

- [ ] **Step 4: Write the browser check**

Write `C:\Users\admin\AppData\Local\Temp\claude\c--Users-admin-Documents-graduation-project-GRAD-project\m3-build\m3-browser-check.mjs` with the Write tool. It contains no backslash-u escape and no doubled backslash. Every expected sentence is read from the repository's own string tables, never typed, so the checks follow Task 7's final wording. The Laya status after the first answer is waited for, not read once.

```js
// M3 browser check (scratchpad, NOT repository code). Drives the installed
// Chrome over the DevTools protocol against a running `-m app.server
// --simulation`, with Node 24's built-in fetch and WebSocket. Every expected
// sentence is read from the page's own string tables (i18n.mjs plus
// agents-strings.mjs, imported from SIM), never typed here.
//   node m3-browser-check.mjs <base-url> <out-dir> <sim-dir> [full|jev-fail]
// full:     1440 light ar, 390 dark ar, 1440 dark en. Locked page, the moved
//           pause panel, the gesture, the natural end at 16x, Laya twice, jev
//           with no key, back to an asked second, a reload.
// jev-fail: 1440 light ar only, against a server started with a dummy key and
//           a refused local proxy: jev shows `network`, Laya still answers.
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const BASE = process.argv[2] || 'http://127.0.0.1:8000';
const OUT = process.argv[3] || '.';
const SIM = process.argv[4];
const MODE = process.argv[5] || 'full';
const { STRINGS } = await import(pathToFileURL(resolve(SIM, 'i18n.mjs')).href);
await import(pathToFileURL(resolve(SIM, 'agents-strings.mjs')).href);
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const PORT = 9341;
const EPISODE = '?runs=runs_c4&seed=5&ep=1';
const sleep = ms => new Promise(r => setTimeout(r, ms));
// The fixed text of a string: everything before its first {placeholder}.
const head = (lang, key) => STRINGS[lang][key].split('{')[0].trim();

mkdirSync(join(OUT, 'chrome-profile-m3'), { recursive: true });
const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${join(OUT, 'chrome-profile-m3')}`, '--no-first-run', '--use-angle=swiftshader',
  '--enable-unsafe-swiftshader', '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
for (let i = 0; i < 400; i++) { try { await fetch(`http://127.0.0.1:${PORT}/json/version`); break; } catch { await sleep(100); } }

const report = { base: BASE, mode: MODE, checks: [], timings: {}, patterns: {} };
function check(view, name, ok, detail = '') {
  report.checks.push({ view, name, ok: Boolean(ok), detail: String(detail).slice(0, 400) });
  console.log(`${ok ? 'PASS' : 'FAIL'}  [${view}] ${name}${ok ? '' : `  -- ${detail}`}`);
}

async function open({ width, height, mobile = false, dark = false }) {
  const target = await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: 'PUT' })).json();
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise(r => ws.addEventListener('open', r, { once: true }));
  let id = 0;
  const pending = new Map();
  const net = [];   // every request the page sends, from the DevTools Network domain
  ws.addEventListener('message', ev => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
    if (msg.method === 'Network.requestWillBeSent') {
      const u = new URL(msg.params.request.url);
      net.push({ method: msg.params.request.method, path: u.pathname, search: u.search });
    }
  });
  const send = (method, params = {}) => new Promise((resolveSend, reject) => {
    id += 1;
    pending.set(id, m => (m.error ? reject(new Error(`${method}: ${m.error.message}`)) : resolveSend(m.result)));
    ws.send(JSON.stringify({ id, method, params }));
  });
  for (const m of ['Runtime.enable', 'Page.enable', 'Network.enable']) await send(m);
  await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 2, mobile });
  await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: dark ? 'dark' : 'light' }] });
  const page = {
    net,
    models: () => net.filter(r => r.path.startsWith('/api/agents/jev') || r.path.startsWith('/api/agents/laya')),
    async goto(url, settle = 2500) { await send('Page.navigate', { url }); await sleep(settle); },
    async reload(settle = 2500) { net.length = 0; await send('Page.reload', { ignoreCache: true }); await sleep(settle); },
    async eval(expression) {
      const r = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
      if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
      return r.result.value;
    },
    async until(expression, ms = 60000, step = 100) {
      const t0 = Date.now();
      while (Date.now() - t0 < ms) { if (await page.eval(expression)) return Date.now() - t0; await sleep(step); }
      return null;
    },
    async shot(name, selector = null) {
      let clip;
      if (selector) {
        const box = await page.eval(`(() => { const e = document.querySelector(${JSON.stringify(selector)}); if (!e) return null;
          const r = e.getBoundingClientRect(); return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: r.height }; })()`);
        if (!box || !box.width || !box.height) { console.log(`      no box for ${selector}`); return; }
        clip = { ...box, scale: 1 };
      }
      const r = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: Boolean(selector), ...(clip ? { clip } : {}) });
      writeFileSync(join(OUT, name), Buffer.from(r.data, 'base64'));
      console.log(`      shot ${join(OUT, name)}`);
    },
    close() { ws.close(); },
  };
  return page;
}

const $t = id => `(document.getElementById(${JSON.stringify(id)})?.textContent ?? '')`;
const shown = id => `(() => { const e = document.getElementById(${JSON.stringify(id)}); return !!e && !e.hidden && getComputedStyle(e).display !== 'none'; })()`;
const enabled = id => `!document.getElementById(${JSON.stringify(id)}).disabled`;
const ready = `document.getElementById('loading').hidden && !document.getElementById('play').disabled`;
const rows = name => `document.querySelectorAll('#model-${name}-rows .model-row').length`;
const playIcon = `document.querySelector('#play use').getAttribute('href')`;
const seekTo = s => `(() => { const e = document.getElementById('seek'); e.value = '${s}'; e.dispatchEvent(new Event('input')); })()`;
const top = sel => `(() => { const e = document.querySelector(${JSON.stringify(sel)}); if (!e || !e.getClientRects().length) return null; return Math.round(e.getBoundingClientRect().top + scrollY); })()`;
const fits = `({ scroll: document.documentElement.scrollWidth, inner: innerWidth })`;
const tapTen = `(() => { const e = document.getElementById('footer-index'); for (let i = 0; i < 10; i++) e.click(); })()`;
const orderPattern = `[...document.querySelectorAll('#model-laya-rows .model-row')].map(r => r.querySelector('.held') ? 'held' : r.querySelector('.changed') ? 'changed' : '?').join(' ')`;
const postsTo = (page, path) => page.net.filter(r => r.method === 'POST' && r.path === path).length;

async function prepare(page, view, lang, dark) {
  await page.goto(`${BASE}/agents`, 1500);
  await page.eval(`localStorage.setItem('grad.sim.theme', '${dark ? 'dark' : 'light'}'); localStorage.setItem('grad.sim.lang', '${lang}')`);
  await page.goto(`${BASE}/agents${EPISODE}`);
  await page.until(`document.getElementById('pick-episode').value === '1'`, 20000);
  const doc = await page.eval(`({ lang: document.documentElement.lang, theme: document.documentElement.dataset.theme })`);
  check(view, `the page is in ${lang} and ${dark ? 'dark' : 'light'}`, doc.lang === lang && doc.theme === (dark ? 'dark' : 'light'), JSON.stringify(doc));
}

async function locked(page, view, lang) {
  check(view, 'locked: the models panel is hidden', !(await page.eval(shown('models-panel'))));
  const heading = await page.eval($t('pause-heading'));
  check(view, 'before «احسب» the pause heading says what to do', heading === STRINGS[lang]['agents.pause.empty'], heading);
  check(view, 'the pause panel is in the main column, right after the transport',
    await page.eval(`(() => { const p = document.querySelector('.agents-col-main > .pause-panel'); return !!p && p.previousElementSibling?.classList.contains('agents-transport'); })()`));
  const y = { transport: await page.eval(top('.agents-transport')), pause: await page.eval(top('.pause-panel')),
    profile: await page.eval(top('.profile-panel')), fold: await page.eval('innerHeight') };
  report.timings[`${view} pause panel top`] = y;
  console.log(`      pause panel top ${y.pause} px (fold ${y.fold}); transport ${y.transport}; profile ${y.profile}`);
  check(view, 'transport, then pause panel, then profile, top to bottom', y.transport < y.pause && y.pause < y.profile, JSON.stringify(y));
  check(view, 'locked: no request to a model route', page.models().length === 0, JSON.stringify(page.models()));
}

async function compute(page, view) {
  const t0 = Date.now();
  await page.eval(`document.getElementById('compute').click()`);
  const ms = await page.until(ready, 180000, 200);
  report.timings[`${view} compute`] = ms;
  check(view, 'runs_c4/5/1 computed to the end', ms !== null, `${Date.now() - t0} ms`);
}

async function unlock(page, view, lang, { jevConfigured = false, fresh = false } = {}) {
  await page.eval(`(() => { const e = document.getElementById('footer-index'); for (let i = 0; i < 9; i++) e.click(); })()`);
  check(view, 'nine taps unlock nothing', !(await page.eval(shown('models-panel'))));
  await sleep(4200);   // the nine taps leave the four-second window
  await page.eval(tapTen);
  check(view, 'ten taps show the panel', await page.eval(shown('models-panel')));
  // Until a status arrives, its line reads '—'.
  await page.until(`![${$t('model-jev-status')}, ${$t('model-laya-status')}].some(s => s === '' || s === '—')`, 10000);
  const jev = await page.eval($t('model-jev-status'));
  const laya = await page.eval($t('model-laya-status'));
  const wantJev = jevConfigured ? head(lang, 'agents.models.jev.status.configured') : STRINGS[lang]['agents.models.jev.status.no_key'];
  check(view, `jev's status: ${wantJev}`, jev.includes(wantJev), jev);
  // Laya stays loaded until the server stops: only a fresh server shows it stopped.
  if (fresh) check(view, 'Laya\'s status: loads on the first question', laya === STRINGS[lang]['agents.models.laya.status.stopped'], laya);
  else check(view, 'Laya\'s status: still loaded from the view before', laya.startsWith(head(lang, 'agents.models.laya.status.ready')), laya);
  check(view, 'the shared honesty lines and the order-check line are on screen',
    await page.eval(['models-not-thesis', 'models-claim', 'models-levels', 'model-jev-text', 'model-laya-text', 'model-laya-check'].map(shown).join(' && ')));
  const statuses = page.models().filter(r => r.method === 'GET').map(r => r.path).sort();
  check(view, 'one status request per model, and nothing else', JSON.stringify(statuses) === JSON.stringify(['/api/agents/jev/status', '/api/agents/laya/status']) && page.models().length === 2, JSON.stringify(page.models()));
}

async function askLaya(page, view, lang, label) {
  const before = postsTo(page, '/api/agents/laya');
  const t0 = Date.now();
  await page.eval(`document.getElementById('ask-laya').click()`);
  let sawStarting = false;
  while (Date.now() - t0 < 120000) {
    const s = await page.eval(`({ status: ${$t('model-laya-status')}, rows: ${rows('laya')}, error: ${shown('model-laya-error')} })`);
    if (s.status === STRINGS[lang]['agents.models.laya.status.starting']) sawStarting = true;
    if (s.rows === 5 || s.error) break;
    await sleep(100);
  }
  report.timings[`${view} Laya ${label}`] = Date.now() - t0;
  const n = await page.eval(rows('laya'));
  check(view, `Laya ${label}: five rows`, n === 5, `${n} rows; error: ${await page.eval($t('model-laya-error'))}`);
  check(view, `Laya ${label}: one POST`, postsTo(page, '/api/agents/laya') === before + 1);
  const pattern = await page.eval(orderPattern);
  report.patterns[`${view} ${label}`] = pattern;
  console.log(`      Laya ${label} order check: ${pattern}; ${Date.now() - t0} ms in the page`);
  check(view, `Laya ${label}: every action says held or changed`, !pattern.includes('?') && pattern.split(' ').length === 5, pattern);
  check(view, `Laya ${label}: no model level is drawn on the agents' gauges`,
    await page.eval(`document.querySelectorAll('#actions .gauge-dot').length === 10 && !document.querySelector('#actions .model-bar, #actions .model-row')`));
  check(view, `Laya ${label}: no confidence is shown`,
    await page.eval(`[...document.querySelectorAll('.model-rows')].every(e => !/confidence|الثقة/i.test(e.textContent))`));
  return { sawStarting, latency: await page.eval($t('model-laya-latency')) };
}

async function fullView(view, { width, height, mobile = false, dark = false, lang, deep, fresh = false }) {
  console.log(`\n== ${view}`);
  const page = await open({ width, height, mobile, dark });
  await prepare(page, view, lang, dark);
  await locked(page, view, lang);
  if (mobile) {
    const w = await page.eval(fits);
    check(view, 'locked: no sideways scroll', w.scroll <= w.inner, JSON.stringify(w));
  }
  await page.shot(`m3-${view}-locked-fold.png`);
  await compute(page, view);
  check(view, 'still locked after «احسب»: nothing asked', page.models().length === 0 && !(await page.eval(shown('models-panel'))));
  await unlock(page, view, lang, { fresh });
  check(view, 'a finished episode never played: both buttons enabled at second 0',
    await page.eval(`${enabled('ask-jev')} && ${enabled('ask-laya')}`));
  if (mobile) {
    const y = { pause: await page.eval(top('.pause-panel')), profile: await page.eval(top('.profile-panel')), models: await page.eval(top('#models-panel')) };
    check(view, 'phone order: pause panel, profile, models panel', y.pause < y.profile && y.profile < y.models, JSON.stringify(y));
    const widths = await page.eval(`[document.querySelector('.agents-transport'), document.getElementById('models-panel')].map(e => Math.round(e.getBoundingClientRect().width))`);
    check(view, 'the models panel stretches to the column', widths[1] >= widths[0] - 1, JSON.stringify(widths));
  }
  if (deep) {
    // The natural end at 16x, with no seek.
    await page.eval(`(() => { const r = document.getElementById('rate'); r.value = '16'; r.dispatchEvent(new Event('change')); })()`);
    await page.eval(`document.getElementById('play').click()`);
    check(view, 'playing: both buttons disabled', await page.until(`${playIcon} === '#i-pause' && document.getElementById('ask-laya').disabled && document.getElementById('ask-jev').disabled`, 5000) !== null);
    const ended = await page.until(`${playIcon} === '#i-play'`, 120000, 250);
    report.timings[`${view} play to the end at 16x`] = ended;
    const end = await page.eval(`({ time: ${$t('current-time')}, duration: ${$t('duration')}, heading: ${$t('pause-heading')} })`);
    check(view, 'played to the natural end (the clock reads the duration)', ended !== null && end.time === end.duration, JSON.stringify(end));
    const lastHeading = STRINGS[lang]['agents.pause.heading'].replace('{k}', '718').replace('{k1}', '719');
    check(view, 'the heading reads second 718 to 719', end.heading === lastHeading, end.heading);
    check(view, 'at the natural end both buttons are enabled, with no seek', await page.eval(`${enabled('ask-jev')} && ${enabled('ask-laya')}`));
    await page.shot(`m3-${view}-natural-end-models.png`, '#models-panel');

    // Laya, first press (starts the worker), at second 718.
    const first = await askLaya(page, view, lang, 'first press at 718');
    check(view, 'the first press showed the loading line', first.sawStarting);
    check(view, 'the first press shows the latency, the device and the first-load time',
      first.latency.includes('ms') && first.latency.includes(head(lang, 'agents.models.laya.first_load')), first.latency);
    // Waited for, not read once: the page re-reads Laya's status after each answer.
    const readyHead = JSON.stringify(head(lang, 'agents.models.laya.status.ready'));
    const loaded = await page.until(`${$t('model-laya-status')}.startsWith(${readyHead})`, 10000);
    check(view, 'Laya is loaded until the server stops', loaded !== null, await page.eval($t('model-laya-status')));

    // jev with no key: its own column only; nothing sent anywhere.
    await page.eval(`document.getElementById('ask-jev').click()`);
    await page.until(shown('model-jev-error'), 15000);
    const jevError = await page.eval($t('model-jev-error'));
    check(view, 'jev: «لا جواب — no_key» in jev\'s column', jevError.includes('no_key'), jevError);
    check(view, 'Laya\'s answer is untouched by jev\'s failure', await page.eval(rows('laya')) === 5 && !(await page.eval(shown('model-laya-error'))));

    // Another second: a warm press.
    await page.eval(seekTo(312.5));
    await sleep(400);
    check(view, 'at second 312 nothing is shown yet', await page.eval(rows('laya')) === 0);
    const second = await askLaya(page, view, lang, 'second press at 312');
    check(view, 'the second press carries no first-load time', !second.latency.includes(head(lang, 'agents.models.laya.first_load')), second.latency);
    await page.shot(`m3-${view}-laya-312.png`, '#models-panel');

    // Back to 718: the stored answer, with no new request.
    const posts = postsTo(page, '/api/agents/laya') + postsTo(page, '/api/agents/jev');
    await page.eval(seekTo(718.5));
    await sleep(600);
    check(view, 'back at second 718 its answer is shown again', await page.eval(rows('laya')) === 5 && await page.eval(shown('model-jev-error')));
    check(view, 'and no new request was sent', postsTo(page, '/api/agents/laya') + postsTo(page, '/api/agents/jev') === posts);
    await page.shot(`m3-${view}-pause-panel.png`, '.pause-panel');

    // A reload forgets the unlock.
    await page.reload();
    await page.until(`document.getElementById('pick-episode').value === '1'`, 20000);
    check(view, 'after a reload the panel is hidden again', !(await page.eval(shown('models-panel'))));
    check(view, 'and nothing is asked', page.models().length === 0, JSON.stringify(page.models()));
  } else {
    await askLaya(page, view, lang, 'press at 0');
    const w = await page.eval(fits);
    if (mobile) check(view, 'with answers shown: no sideways scroll', w.scroll <= w.inner, JSON.stringify(w));
    await page.shot(`m3-${view}-models.png`, '#models-panel');
  }
  page.close();
}

async function jevFail(view) {
  console.log(`\n== ${view} (jev forced to fail)`);
  const page = await open({ width: 1440, height: 900 });
  await prepare(page, view, 'ar', false);
  await compute(page, view);
  await unlock(page, view, 'ar', { jevConfigured: true, fresh: true });
  await page.eval(`document.getElementById('ask-jev').click()`);
  await page.until(shown('model-jev-error'), 30000);
  const text = await page.eval($t('model-jev-error'));
  check(view, 'jev: network (or timeout) in jev\'s column only', /network|timeout/.test(text) && !(await page.eval(shown('model-laya-error'))), text);
  await askLaya(page, view, 'ar', 'after jev failed');
  check(view, 'jev keeps its own error', await page.eval(shown('model-jev-error')));
  await page.shot(`m3-${view}-jev-failed.png`, '#models-panel');
  page.close();
}

try {
  if (MODE === 'jev-fail') await jevFail('1440-light-ar');
  else {
    await fullView('1440-light-ar', { width: 1440, height: 900, lang: 'ar', deep: true, fresh: true });
    await fullView('390-dark-ar', { width: 390, height: 844, mobile: true, dark: true, lang: 'ar' });
    await fullView('1440-dark-en', { width: 1440, height: 900, dark: true, lang: 'en' });
  }
} catch (err) {
  check('script', 'ran to the end', false, err.stack);
} finally {
  writeFileSync(join(OUT, `report-${MODE}.json`), JSON.stringify(report, null, 1));
  const failed = report.checks.filter(c => !c.ok);
  console.log(failed.length ? `\n${failed.length} FAIL of ${report.checks.length}` : `\nALL PASS (${report.checks.length} checks)`);
  chrome.kill();
  process.exit(failed.length ? 1 : 0);
}
```

- [ ] **Step 5: Run the browser check (real Laya), and look at what it cannot judge**

Run it with `run_in_background`. On 28 Sep it took about 5 minutes: a cold build of about 100 s, 45 s of playback at 16x, and the rest.

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"; node "$(cygpath -w "$SCRATCH/m3-browser-check.mjs")" http://127.0.0.1:8765 "$(cygpath -w "$SCRATCH/m3-out")" "$(cygpath -w "$PWD/app/static/sim")" full > "$SCRATCH/m3-browser.txt" 2>&1
```

When it completes:

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
grep -E "^FAIL|ALL PASS|FAIL of" "$SCRATCH/m3-browser.txt"
for v in 1440-light-ar 390-dark-ar 1440-dark-en; do printf '%s ' $v; grep -c "^PASS  \[$v\]" "$SCRATCH/m3-browser.txt"; done
grep -E "pause panel top|order check" "$SCRATCH/m3-browser.txt"
node -e "const r = require(process.argv[1]); console.log(JSON.stringify(r.timings)); console.log(JSON.stringify(r.patterns))" "$(cygpath -w "$SCRATCH/m3-out/report-full.json")"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader | sed 's/^/Laya loaded: /' | tee -a "$SCRATCH/m3_gpu.txt"
```

Expected:
- `ALL PASS (84 checks)`, with no `FAIL` line: 40 at 1440 light Arabic, 24 at 390 dark Arabic, 20 at 1440 English. This was re-measured 28 Sep after Task 8's status fix, against Task 7's final strings.
- The 28 Sep prototype, for comparison only:
  - pause panel top 841 px against a fold of 900 at 1440 × 900, and 1721 px at 390 px;
  - compute about 100 s cold, then about 0.2 s cached;
  - 45 s to the end at 16x;
  - Laya's first press 3.06 s with the fake's 3 s load. With the real Laya, spawn to ready takes about 6-12 s (6.11 s measured by the skeleton), then tens of ms warm (34.8 ms per request, so about 70 ms for a press's two requests).
- Laya's order-check patterns, recorded as observations. The spike saw spark, lambda, fan and pump change and boost hold; nothing is asserted about the pattern.
- The GPU line grows by roughly Laya's footprint (the spike measured about 1.7 GB).

Read these screenshots with the Read tool. Each one checks something the script cannot:

| screenshot | check |
|---|---|
| `m3-1440-light-ar-locked-fold.png` | the pause heading's empty line sits under the play bar and is visible at 900 px; the page is otherwise M2's (verdict box, picker, chase view) |
| `m3-1440-light-ar-natural-end-models.png` | both buttons enabled, the three honesty lines, jev «لا مفتاح؛ لن يُرسل شيء», Laya «يُحمَّل عند أول سؤال» |
| `m3-1440-light-ar-laya-312.png` | five rows in ACTIONS order with units; the reference line's two lane dots; five bars per row, one marked; «احتمال الخيار المختار»; «ثبت» or «تغيّر بتغيير الترتيب» per action, never red or green; Laya's status line reads loaded on the device |
| `m3-1440-light-ar-pause-panel.png` | the pause panel at second 718 is M2's panel, with no model level on any gauge |
| `m3-390-dark-ar-locked-fold.png`, `m3-390-dark-ar-models.png` | one column, no sideways scroll, and the bars and the order line wrap inside the column |
| `m3-1440-dark-en-locked-fold.png`, `m3-1440-dark-en-models.png` | English throughout, including the pause panel's empty line |

- [ ] **Step 6: Shutdown by hard kill, by Ctrl+C and by closing the window: no Laya worker survives any of them**

Write the three helpers with the Write tool, into `C:\Users\admin\AppData\Local\Temp\claude\c--Users-admin-Documents-graduation-project-GRAD-project\m3-build\`.

`m3_console.py`:

```python
"""Task 10: do to the console window of process <pid> what a person would.

    python m3_console.py ctrl-c <pid>   press Ctrl+C in that window
    python m3_console.py close <pid>    click that window's close button

It leaves its own console and attaches to that process's console. ctrl-c sets
itself to ignore the event, then generates CTRL_C_EVENT for every process on
that console (process group 0), which is what the key press does. close reads
that console's window, detaches, and posts WM_CLOSE to it, which is what the
close button sends; the console then sends CTRL_CLOSE_EVENT to every process
on it. It prints nothing once it has left its own console, so the result is
the exit code: 0 done; 10 AttachConsole failed; 11 SetConsoleCtrlHandler
failed; 12 GenerateConsoleCtrlEvent failed; 13 no console window;
14 PostMessage failed.
"""
import ctypes
import sys
import time

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
u32 = ctypes.WinDLL("user32", use_last_error=True)
k32.GetConsoleWindow.restype = ctypes.c_void_p
u32.PostMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p]
WM_CLOSE = 0x0010
CTRL_C_EVENT = 0

action, pid = sys.argv[1], int(sys.argv[2])
k32.FreeConsole()
if not k32.AttachConsole(pid):
    sys.exit(10)
if action == "ctrl-c":
    if not k32.SetConsoleCtrlHandler(None, True):
        sys.exit(11)
    if not k32.GenerateConsoleCtrlEvent(CTRL_C_EVENT, 0):
        sys.exit(12)
    time.sleep(1)
    k32.FreeConsole()
    sys.exit(0)
hwnd = k32.GetConsoleWindow()
k32.FreeConsole()
if not hwnd:
    sys.exit(13)
if not u32.PostMessageW(hwnd, WM_CLOSE, None, None):
    sys.exit(14)
sys.exit(0)
```

`m3_shutdown.ps1`:

```powershell
# Task 10 shutdown check (scratch, NOT repository code). Starts the server in a
# console window of its own (conhost.exe, so the window is a classic console
# that belongs to this run, whatever the default terminal is), computes
# runs_c4/5/1, presses Laya once, stops the server the way -Method says, and
# counts the laya_worker.py processes 5 s later.
#   powershell -NoProfile -ExecutionPolicy Bypass -File m3_shutdown.ps1 -Method ctrl-c -Port 8767 -Out <file>
# ctrl-c: m3_console.py presses Ctrl+C in that window. close: m3_console.py
# posts WM_CLOSE to that window, what its close button sends. kill:
# Stop-Process -Force on the server.
param(
    [Parameter(Mandatory)][ValidateSet('ctrl-c', 'close', 'kill')][string]$Method,
    [Parameter(Mandatory)][int]$Port,
    [Parameter(Mandatory)][string]$Out
)
$ErrorActionPreference = 'Stop'
$repo = 'C:\Users\admin\Documents\graduation project\GRAD-project'
$py = 'C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe'
$scr = 'C:\Users\admin\AppData\Local\Temp\claude\c--Users-admin-Documents-graduation-project-GRAD-project\m3-build'
$base = "http://127.0.0.1:$Port"
$lines = @("== $Method, port $Port, $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$srv = $null
function Get-Workers {
    @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*laya_worker.py*' })
}

try {
    if (@(Get-Workers).Count -ne 0) { throw 'a laya_worker.py process is already running: stop it before this check' }
    # This process's environment only; Start-Process hands it to the server.
    $env:LAYA_HOME = 'C:\Users\admin\Documents\Local AI\laya'
    Remove-Item Env:TYPESAFE_API_KEY -ErrorAction SilentlyContinue
    $env:PYTHONIOENCODING = 'utf-8'
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $con = Start-Process -FilePath "$env:WINDIR\System32\conhost.exe" -WorkingDirectory $repo -PassThru `
        -ArgumentList "$py -m app.server --simulation --http-port $Port"

    $ok = $false
    $deadline = (Get-Date).AddSeconds(60)
    while (-not $ok -and (Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 500
        try { $ok = (Invoke-WebRequest -UseBasicParsing "$base/agents" -TimeoutSec 2).StatusCode -eq 200 } catch { $ok = $false }
    }
    if (-not $ok) { throw "the server did not answer on port $Port within 60 s" }
    $srv = @(Get-NetTCPConnection -LocalPort $Port -State Listen)[0].OwningProcess

    # The episode, as the page asks for it; since=719 polls without the frames.
    $episode = "$base/api/agents/episode?runs=runs_c4&seed=5&ep=1"
    $t0 = Get-Date
    $r = Invoke-RestMethod "$episode&since=0" -TimeoutSec 60
    while ($r.status -ne 'ready') {
        if ($r.status -in @('error', 'refused', 'busy') -or ((Get-Date) - $t0).TotalSeconds -gt 300) { throw "episode: $($r.status)" }
        Start-Sleep -Seconds 2
        $r = Invoke-RestMethod "$episode&since=719" -TimeoutSec 60
    }
    $lines += "episode computed in $([math]::Round(((Get-Date) - $t0).TotalSeconds)) s"

    # One press, same origin, the paused second 0.
    $t0 = Get-Date
    $a = Invoke-RestMethod -Method Post "$base/api/agents/laya" -ContentType 'application/json' `
        -Headers @{ Origin = $base } -Body '{"trace": "runs_c4/5/1", "step": 0}' -TimeoutSec 120
    $lines += "Laya answered in $([math]::Round(((Get-Date) - $t0).TotalSeconds, 1)) s on $($a.device)"

    $before = @(Get-Workers)
    $lines += "server pid $srv (console host pid $($con.Id)); laya_worker processes before: $($before.Count)"
    $lines += $before | ForEach-Object { "  $($_.ProcessId) <- $($_.ParentProcessId)  $($_.ExecutablePath)" }
    if ($Method -eq 'kill') { Stop-Process -Id $srv -Force }
    else {
        & $py (Join-Path $scr 'm3_console.py') $Method $srv
        if ($LASTEXITCODE -ne 0) { throw "m3_console.py $Method exit $LASTEXITCODE" }
    }
    Start-Sleep -Seconds 5
    $after = @(Get-Workers)
    $lines += "5 s after ${Method}: server alive $([bool](Get-Process -Id $srv -ErrorAction SilentlyContinue)); laya_worker processes $($after.Count)"
}
catch {
    $lines += "ERROR: $($_.Exception.Message)"
}
finally {
    # Counted first, then cleaned up, so the next check starts from nothing.
    if ($srv -and (Get-Process -Id $srv -ErrorAction SilentlyContinue)) { Stop-Process -Id $srv -Force }
    foreach ($w in @(Get-Workers)) {
        $lines += "  left running: $($w.ProcessId)  $($w.ExecutablePath) (stopped after counting)"
        Stop-Process -Id $w.ProcessId -Force -ErrorAction SilentlyContinue
    }
    [System.IO.File]::WriteAllLines($Out, [string[]]$lines)
    $lines
}
```

`m3_kill_running.ps1`:

```powershell
# Task 10 (scratch, NOT repository code): hard-kill the server already
# listening on -Port, after a Laya press, and count the laya_worker.py
# processes 5 s later.
#   powershell -NoProfile -ExecutionPolicy Bypass -File m3_kill_running.ps1 -Port 8765 -Out <file>
param(
    [Parameter(Mandatory)][int]$Port,
    [Parameter(Mandatory)][string]$Out
)
$ErrorActionPreference = 'Stop'
$lines = @("== kill (Stop-Process -Force) of the server on port $Port, $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
function Get-Workers {
    @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*laya_worker.py*' })
}
try {
    $srv = @(Get-NetTCPConnection -LocalPort $Port -State Listen)[0].OwningProcess
    $before = @(Get-Workers)
    $lines += "server pid $srv; laya_worker processes before: $($before.Count)"
    $lines += $before | ForEach-Object { "  $($_.ProcessId) <- $($_.ParentProcessId)  $($_.ExecutablePath)" }
    Stop-Process -Id $srv -Force
    Start-Sleep -Seconds 5
    $after = @(Get-Workers)
    $lines += "5 s after kill: server alive $([bool](Get-Process -Id $srv -ErrorAction SilentlyContinue)); laya_worker processes $($after.Count)"
}
catch {
    $lines += "ERROR: $($_.Exception.Message)"
}
finally {
    foreach ($w in @(Get-Workers)) {
        $lines += "  left running: $($w.ProcessId)  $($w.ExecutablePath) (stopped after counting)"
        Stop-Process -Id $w.ProcessId -Force -ErrorAction SilentlyContinue
    }
    [System.IO.File]::WriteAllLines($Out, [string[]]$lines)
    $lines
}
```

Both `.ps1` files write their result with `WriteAllLines`, which writes UTF-8 without a byte-order mark. `Set-Content -Encoding utf8` in Windows PowerShell 5.1 would put a BOM into the middle of the record.

First, hard-kill the browser-check server on 8765. Its Laya worker has been loaded since Step 5. Run this with the PowerShell tool:

```powershell
$scr = 'C:\Users\admin\AppData\Local\Temp\claude\c--Users-admin-Documents-graduation-project-GRAD-project\m3-build'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$scr\m3_kill_running.ps1" -Port 8765 -Out "$scr\m3_shutdown_kill.txt"
"exit $LASTEXITCODE"
```

Expected:
- `server pid …; laya_worker processes before: 2`, followed by two lines: the launcher `…\Local AI\laya\.venv\Scripts\python.exe` whose parent is the server, and its child `…\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.
- `5 s after kill: server alive False; laya_worker processes 0`. The worker exits on stdin EOF (the skeleton measured 0.53 s). On 28 Sep a fake worker was gone within 5 s of every hard kill.
- The background task that ran the server then reports a failed exit. That is the kill.

Then Ctrl+C and closing the window, each on a fresh server in a console window of its own. Run this with the PowerShell tool, with a timeout of 600000 ms. Each run computes the episode cold (about 70-100 s) and loads the real Laya (about 6-12 s). **Two console windows open and close on this machine's desktop while it runs: leave them alone.**

```powershell
$scr = 'C:\Users\admin\AppData\Local\Temp\claude\c--Users-admin-Documents-graduation-project-GRAD-project\m3-build'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$scr\m3_shutdown.ps1" -Method ctrl-c -Port 8767 -Out "$scr\m3_shutdown_ctrlc.txt"
"exit $LASTEXITCODE"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$scr\m3_shutdown.ps1" -Method close -Port 8768 -Out "$scr\m3_shutdown_close.txt"
"exit $LASTEXITCODE"
```

Expected for each:
- `episode computed in … s`;
- `Laya answered in … s on cuda`;
- `server pid … (console host pid …); laya_worker processes before: 2`, with the same two lines as above;
- `5 s after ctrl-c: server alive False; laya_worker processes 0`, and likewise `5 s after close: …`.

On the 28 Sep prototype (fake worker, one process, so `before: 1`), each run took about 75 s and read `server alive False; laya_worker processes 0`, twice for each method. A `left running:` line is a surviving worker, and it stops the milestone. An `ERROR:` line means that method was not measured, and the record says why.

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader | sed 's/^/after shutdown: /' | tee -a "$SCRATCH/m3_gpu.txt"
```

- [ ] **Step 7: jev forced to fail, with a gate first**

Write `C:\Users\admin\AppData\Local\Temp\claude\c--Users-admin-Documents-graduation-project-GRAD-project\m3-build\m3_proxy_gate.py` with the Write tool:

```python
"""Task 10 gate, run in the SAME environment the jev-fail server will get.

It proves, without sending anything, that urllib would reach only a refused
local port: the proxy it would use is 127.0.0.1:9, api.typesafe.ai is not
bypassed, and nothing listens on 127.0.0.1:9. Any other outcome: do not start
that server, and do not press jev.
"""
import socket
import sys
import urllib.request

proxies = urllib.request.getproxies()
print("proxies:", proxies)
if proxies.get("https") != "http://127.0.0.1:9":
    sys.exit("GATE FAILED: urllib would not use the refused local proxy for https")
if urllib.request.proxy_bypass("api.typesafe.ai"):
    sys.exit("GATE FAILED: api.typesafe.ai would bypass the proxy")
probe = socket.socket()
probe.settimeout(5)   # Windows answers a closed local port after about 2 s (measured 2.04 s)
try:
    probe.connect(("127.0.0.1", 9))
except ConnectionRefusedError:
    print("GATE PASSED: 127.0.0.1:9 refuses the connection, so no request can leave through it")
else:
    sys.exit("GATE FAILED: something listens on 127.0.0.1:9")
finally:
    probe.close()
```

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
env HTTPS_PROXY=http://127.0.0.1:9 HTTP_PROXY=http://127.0.0.1:9 NO_PROXY= $PY "$(cygpath -w "$SCRATCH/m3_proxy_gate.py")" 2>&1 | tee "$SCRATCH/m3_gate.txt"
```

`2>&1` matters: `sys.exit("GATE FAILED: …")` writes to stderr, and Task 11 reads the reason from `m3_gate.txt`.

Expected, as on 28 Sep: `proxies: {'https': 'http://127.0.0.1:9', 'http': 'http://127.0.0.1:9'}`, then `GATE PASSED: 127.0.0.1:9 refuses the connection, so no request can leave through it`. **On any `GATE FAILED`, skip the rest of this step.** The `GATE FAILED` line in `m3_gate.txt` is the recorded reason, and the no-key case in Step 5 already covers "jev fails, Laya answers".

Start the second server with `run_in_background`, with the dummy key and the proxy in that server's environment only:

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"; env TYPESAFE_API_KEY=dummy-not-a-key HTTPS_PROXY=http://127.0.0.1:9 HTTP_PROXY=http://127.0.0.1:9 NO_PROXY= LAYA_HOME='C:\Users\admin\Documents\Local AI\laya' "$PY" -m app.server --simulation --http-port 8766 > "$SCRATCH/m3_server_jevfail.txt" 2>&1
```

Then:

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
for i in $(seq 1 40); do c=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 http://127.0.0.1:8766/agents); [ "$c" = "200" ] && break; sleep 1; done; echo "agents $c"
curl -s http://127.0.0.1:8766/api/agents/jev/status; echo
node "$(cygpath -w "$SCRATCH/m3-browser-check.mjs")" http://127.0.0.1:8766 "$(cygpath -w "$SCRATCH/m3-out")" "$(cygpath -w "$PWD/app/static/sim")" jev-fail > "$SCRATCH/m3-browser-jevfail.txt" 2>&1; grep -E "^FAIL|ALL PASS|FAIL of|order check" "$SCRATCH/m3-browser-jevfail.txt"
grep -E "jev: " "$SCRATCH/m3_server_jevfail.txt"
```

Use a timeout of 600000 ms for this block; the cold build takes about 90 s. Expected:
- `agents 200` and `{"configured":true,"source":"env",…}`. The key itself never appears.
- `ALL PASS (15 checks)`. This was re-measured 28 Sep against a prototype whose fake send raises `URLError`: 15 of 15.
- The server's stderr line `jev: network (step 0)`, or `jev: timeout (step 0)`.

Then hard-kill that server with the PowerShell tool:

```powershell
$scr = 'C:\Users\admin\AppData\Local\Temp\claude\c--Users-admin-Documents-graduation-project-GRAD-project\m3-build'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$scr\m3_kill_running.ps1" -Port 8766 -Out "$scr\m3_shutdown_jevfail.txt"
"exit $LASTEXITCODE"
```

Expected: `laya_worker processes before: 2`, then `5 s after kill: server alive False; laya_worker processes 0`.

- [ ] **Step 8: LAYA_HOME after, and the record**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
LAYA_HOME='C:\Users\admin\Documents\Local AI\laya' $PY "$(cygpath -w "$SCRATCH/m3_laya_snapshot.py")" take "$(cygpath -w "$SCRATCH/m3_laya_after.json")"
$PY "$(cygpath -w "$SCRATCH/m3_laya_snapshot.py")" compare "$(cygpath -w "$SCRATCH/m3_laya_before.json")" "$(cygpath -w "$SCRATCH/m3_laya_after.json")" | tee "$SCRATCH/m3_laya_compare.txt"
git status --short
```

Expected: `LAYA_HOME: N files before, N after, 0 new, gone or changed`, and exit 0. This covers the browser check's worker and the three shutdown servers' workers. `git status --short` lists no M3 file, because the scripts and outputs stayed in `$SCRATCH`.

Write the record. Its section headers are what Task 11's script parses, so do not reword them:

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
{
  echo "M3 verification record, $(date '+%Y-%m-%d %H:%M'), HEAD $(git rev-parse --short HEAD)"
  printf '\n$ load_key() before anything ran\n'; cat "$SCRATCH/m3_key.txt"
  printf '\n$ python -m app.test_agents   (summary)\n'; grep -E "^Ran|^OK|FAILED|PROVEN" "$SCRATCH/m3_agents.txt"
  printf '\n$ LAYA_HOME=... python -m app.test_agents --full   (summary; test 20 prints its "    Laya: " line only after every assertion passed)\n'
  grep -E "^    Laya: |skipped 'LAYA_HOME|test_real_laya|^Ran|^OK|FAILED|PROVEN" "$SCRATCH/m3_agents_full.txt"
  printf '\n$ python -m app.test_simulation\n'; tail -3 "$SCRATCH/m3_sim.txt"
  printf '\n$ python -m app.test_replay   (last line)\n'; tail -1 "$SCRATCH/m3_replay.txt"
  printf '\n$ node --test "app/static/sim/*.test.mjs"   (summary)\n'; grep -E "^ℹ " "$SCRATCH/m3_node.txt"
  printf '\n$ python verify_docs.py   (last line)\n'; tail -1 "$SCRATCH/m3_verify_docs.txt"
  printf '\n$ route probes (server with LAYA_HOME, no key)\n'; cat "$SCRATCH/m3_probes.txt"
  printf '\n$ browser check, full (1440 light ar / 390 dark ar / 1440 dark en), real Laya\n'
  grep -E "^FAIL|ALL PASS|FAIL of|pause panel top|order check" "$SCRATCH/m3-browser.txt"
  node -e "const r = require(process.argv[1]); console.log('timings ' + JSON.stringify(r.timings)); console.log('patterns ' + JSON.stringify(r.patterns))" "$(cygpath -w "$SCRATCH/m3-out/report-full.json")"
  printf '\n$ GPU\n'; cat "$SCRATCH/m3_gpu.txt"
  printf '\n$ shutdown: kill (Stop-Process -Force) of the browser-check server after its Laya presses\n'; cat "$SCRATCH/m3_shutdown_kill.txt"
  printf '\n$ shutdown: Ctrl+C in the console window the server was started in\n'; cat "$SCRATCH/m3_shutdown_ctrlc.txt"
  printf '\n$ shutdown: closing the console window the server was started in\n'; cat "$SCRATCH/m3_shutdown_close.txt"
  printf '\n$ jev forced to fail: gate, browser check, server line, shutdown\n'; cat "$SCRATCH/m3_gate.txt"
  grep -E "^FAIL|ALL PASS|FAIL of" "$SCRATCH/m3-browser-jevfail.txt"; grep -E "jev: " "$SCRATCH/m3_server_jevfail.txt"; cat "$SCRATCH/m3_shutdown_jevfail.txt"
  printf '\n$ LAYA_HOME before/after\n'; cat "$SCRATCH/m3_laya_compare.txt"
  printf '\nNo real jev call was made: see load_key() above and the jev forced to fail section.\n'
  printf 'Screenshots: %s\n' "$(ls "$SCRATCH/m3-out"/*.png 2>/dev/null | xargs -n1 basename | tr '\n' ' ')"
} > "$SCRATCH/m3-verification.txt"
cat "$SCRATCH/m3-verification.txt"
```

On a skipped jev-fail check, the three jev-fail files do not exist. Their `cat` and `grep` errors reach the terminal, not the record, and the section then holds only the gate's `GATE FAILED` line. That is what Task 11 reads.

This block was run on 28 Sep over a fake scratch folder built from the prototype's real browser and shutdown outputs. In that run, the record's full-suite section showed the `    Laya: ` line and no `ok`, as expected.

Any of these stops the milestone:
- a `FAIL` line;
- a skipped test 20 (no `    Laya: ` line, or a `skipped 'LAYA_HOME` line);
- a `left running:` line;
- a changed `LAYA_HOME`.

Fix it in its own commit, with its test and the outputs as in Tasks 8 and 9, then run this task again from Step 1.

---


---

### Task 11: Design amendments for every departure the plan made, the M3 design's consequential amendments applied to the main design, and the milestone commit carrying the verification record

**Files:**
- Modify: `docs/superpowers/specs/2026-09-26-agent-replay-design.md`:
  - §1 `:28` and the non-goal `:34`;
  - §2: the `app/jev.py` row `:62`, the tap-unlock row `:82`, the node-tests row `:84`, and edit 1 `:94`;
  - §3.4: the heading `:162` and the routes `:173-174`;
  - §6: the misreading row `:466` and the layout `:474-475`, `:479`;
  - §7 `:486`, §8 `:612`, §10 `:711`;
  - the walkthrough log (after the "M3 revisit, Q4" row);
  - the end of the file (the new build record).
- Modify: `docs/superpowers/specs/2026-09-28-agent-replay-m3-design.md` (a new section before `## Appendix: Review issues not taken`)
- Scratch only, in `C:\Users\admin\AppData\Local\Temp\claude\c--Users-admin-Documents-graduation-project-GRAD-project\m3-build\`: `m3_amend_design.py`, `m3-ledger.txt`, `m3-design-copy\` and `m3_msg.txt`
- Test: `verify_docs.py`

**Interfaces:**
- Consumes:
  - Task 10's `$SCRATCH/m3-verification.txt` (its fixed section headers) and `$SCRATCH/m3_replay_full.txt`.
  - The spawn-to-ready figure in the `Agent replay M3 (4a/7)` commit message.
  - The controller's build ledger. M2 kept its ledger under `.superpowers/sdd/`, which is gitignored.
  - The M3 design's "Consequential amendments elsewhere in this file".
  - The departures named in Tasks 2, 3, 4, 5, 6, 7, 8, 9 and 10.
- Produces:
  - The main design, with the consequential amendments, a `<day> | M3 built` walkthrough row and a "Build record for M3" section. **Every verification claim in the row is read from the record, and every build-record entry is read from the ledger.** A check the record does not show as passed is written as "not run" or "not measured" with the record's own reason, or the script refuses and writes nothing.
  - The M3 design, with a section "Amendments while building M3". It holds 15 dated amendments, or 16 when Task 10's probes show FastAPI's 422 and 405 without `no-store`. Amendments 14 to 16 are built from the record.
  - The milestone commit.

This task writes documents, so its steps are: run the amendment script, run the checker, commit.

- [ ] **Step 1: Nothing in app/ moved since Task 10, and read the spawn figure**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
git log --oneline "$(head -1 "$SCRATCH/m3-verification.txt" | grep -oE '[0-9a-f]{7,}$')"..HEAD -- app/
git log -1 --format=%B --grep="Agent replay M3 (4a/7)" | grep -iE "spawn|ready" | head -5
```

Expected: the first command prints nothing. If it prints a commit, re-run Task 10 from Step 2. From the second command, note the measured spawn-to-ready seconds as `SPAWN_S`, for example `6.11`.

- [ ] **Step 2: Write the amendment script**

Write `C:\Users\admin\AppData\Local\Temp\claude\c--Users-admin-Documents-graduation-project-GRAD-project\m3-build\m3_amend_design.py` with the Write tool. It contains no backslash-u escape and no doubled backslash.

It was run on 28 Sep, with `BASE` moved back three commits so that the design commits stood in for the build's, over fake records of eight kinds and copies of both designs:
- **passed:** printed `wrote 14 amendments, the 28 Sep log row and the M3 build record (…) into …` and `wrote 16 dated amendments into …`. The diffstats were `41 insertions(+), 13 deletions(-)` and `23 insertions(+)`. A second run printed `already in the design: nothing written`. No added line matched any `verify_docs.RETIRED` pattern.
- **gate failed:** the row reads `jev forced to fail was not run (`GATE FAILED: …`)`.
- **close errored:** the row reads `closing that window was not measured (`m3_console.py close exit 13`)`.
- **FastAPI's own 422 and 405 responses also send no-store:** 15 amendments.
- **a surviving worker:** `REFUSED, nothing written: a Laya worker survived kill …`.
- **test 20 skipped:** `REFUSED, nothing written: test 20 did not run the real Laya …`.
- **an unknown ledger line:** `REFUSED, nothing written: m3-ledger.txt:1 is not 'ruling: ...', …`.
- **a ruling with no cost:** `REFUSED, nothing written: m3-ledger.txt:1: a ruling says what it costs if wrong …`.

```python
"""Write M3's amendments into the two design files. Run from the repository root.

    python m3_amend_design.py <spawn_s> <record> <ledger> [main_design] [m3_design]

<spawn_s>  Task 4's measured spawn-to-ready seconds with -I -B -X utf8, read from
           the "Agent replay M3 (4a/7)" commit message.
<record>   Task 10's m3-verification.txt. Every verification claim this script
           writes is read from it: a check the record does not show as passed
           is written as not run, with the record's own reason, or the script
           refuses.
<ledger>   the controller's build ledger as lines "ruling: ...", "closed: ..."
           and "later: ...". The build record's entries come from it and from
           nothing else; an empty file writes "None recorded".
Every anchor must occur exactly once, or nothing is written; a second run
refuses. The two design paths default to the repository's own, so the script
can be tried on copies first.
"""
import re
import subprocess
import sys
import time
from pathlib import Path

if len(sys.argv) < 4:
    sys.exit(__doc__)
SPAWN_S = sys.argv[1]
RECORD = Path(sys.argv[2])
LEDGER = Path(sys.argv[3])
MAIN = Path(sys.argv[4] if len(sys.argv) > 4 else "docs/superpowers/specs/2026-09-26-agent-replay-design.md")
M3 = Path(sys.argv[5] if len(sys.argv) > 5 else "docs/superpowers/specs/2026-09-28-agent-replay-m3-design.md")
DAY = time.strftime("%d %b").lstrip("0")
PLAN = "docs/superpowers/plans/2026-09-28-agent-replay-m3.md"
BASE = "d347ee5"   # the approved M3 design; every M3 build commit comes after it


def refuse(why):
    sys.exit(f"REFUSED, nothing written: {why}")


def join(items):
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


# ------------------------------------------------------------------ the record
sections, name = {}, None
for line in RECORD.read_text(encoding="utf-8").splitlines():
    if line.startswith("$ "):
        name = line[2:]
        sections[name] = []
    elif name is not None:
        sections[name].append(line)


def section(prefix):
    hits = [body for head, body in sections.items() if head.startswith(prefix)]
    if len(hits) != 1:
        refuse(f"the record has {len(hits)} sections starting {prefix!r}")
    return hits[0]


full = section("LAYA_HOME=... python -m app.test_agents --full")
if any("skipped 'LAYA_HOME" in line for line in full) or not any(
        re.match(r"    Laya: (cuda|cpu)", line) for line in full):
    refuse("test 20 did not run the real Laya: no '    Laya: ' line, or a LAYA_HOME skip")

browser = section("browser check, full")
passed = [re.search(r"ALL PASS \((\d+) checks\)", line) for line in browser]
passed = [hit for hit in passed if hit]
if len(passed) != 1 or any(line.startswith("FAIL") for line in browser):
    refuse("the full browser check did not pass")
BROWSER_N = int(passed[0].group(1))

if not any("0 new, gone or changed" in line for line in section("LAYA_HOME before/after")):
    refuse("LAYA_HOME changed, or its comparison is missing")

AFTER = re.compile(r"5 s after (kill|ctrl-c|close): server alive (True|False); laya_worker processes (\d+)")


def shutdown(prefix, method):
    """('stopped' | 'running', None) when measured with no worker left; ('not measured', why)."""
    body = section(prefix)
    hits = [hit for hit in map(AFTER.search, body) if hit and hit.group(1) == method]
    if hits:
        if int(hits[0].group(3)):
            refuse(f"a Laya worker survived {method} ({prefix!r}): the milestone stops (Task 10)")
        return ("stopped" if hits[0].group(2) == "False" else "running", None)
    why = next((line.split("ERROR: ", 1)[1] for line in body if "ERROR: " in line), None)
    if why is None:
        refuse(f"no result for {method} under {prefix!r}")
    return ("not measured", why)


SHUT = {"kill": shutdown("shutdown: kill", "kill"),
        "ctrl-c": shutdown("shutdown: Ctrl+C", "ctrl-c"),
        "close": shutdown("shutdown: closing", "close")}
SAY = {"kill": "a hard kill of the server", "ctrl-c": "Ctrl+C in its console window",
       "close": "closing that window"}

jev = section("jev forced to fail")
GATE_FAILED = next((line for line in jev if line.startswith("GATE FAILED:")), None)
if any(line.startswith("GATE PASSED") for line in jev):
    if not any("ALL PASS (15 checks)" in line for line in jev) or any(line.startswith("FAIL") for line in jev):
        refuse("jev forced to fail ran and did not pass its 15 checks")
    if not any(re.match(r"jev: (network|timeout) \(step \d+\)", line) for line in jev):
        refuse("the jev-fail server printed no 'jev: network' or 'jev: timeout' line")
    if shutdown("jev forced to fail", "kill")[0] == "not measured":
        refuse("the jev-fail server's shutdown was not measured")
elif GATE_FAILED is None:
    refuse("the jev forced to fail section shows neither GATE PASSED nor GATE FAILED")

probes = section("route probes")


def probe(pattern, status):
    hits = [hit for hit in (re.search(pattern, line) for line in probes) if hit]
    if len(hits) != 1 or hits[0].group(1) != status:
        refuse(f"route probe {pattern!r}: missing, repeated or not {status}")
    return hits[0].group(2)


CC_422 = probe(r"POST laya with a bad body (\d+) cache-control: \[(.*)\]", "422")
CC_405 = probe(r"GET /api/agents/laya (\d+) cache-control: \[(.*)\]", "405")

# ------------------------------------------------------------------ the ledger
entries = {"ruling": [], "closed": [], "later": []}
for n, line in enumerate(LEDGER.read_text(encoding="utf-8").splitlines(), 1):
    if not line.strip():
        continue
    kind, sep, text = line.partition(": ")
    if kind not in entries or not sep or not text.strip():
        refuse(f"{LEDGER.name}:{n} is not 'ruling: ...', 'closed: ...' or 'later: ...': {line[:60]!r}")
    if kind == "ruling" and " -- cost if wrong: " not in text:
        refuse(f"{LEDGER.name}:{n}: a ruling says what it costs if wrong (' -- cost if wrong: ')")
    entries[kind].append(text.strip())

log = subprocess.run(["git", "log", "--reverse", "--format=%h %s", f"{BASE}..HEAD"], capture_output=True,
                     text=True, encoding="utf-8", check=True).stdout.splitlines()
COMMITS = [line.split(" ", 1)[0] for line in log if line.split(" ", 1)[1].startswith("Agent replay M3")]
if not COMMITS:
    refuse(f"no commit after {BASE} has a subject starting 'Agent replay M3'")

# ------------------------------------------------------------------ the designs
main = MAIN.read_text(encoding="utf-8")
m3 = M3.read_text(encoding="utf-8")
if "## Build record for M3" in main or "## Amendments while building M3" in m3:
    sys.exit("already in the design: nothing written")


def once(text, old, new, where):
    if text.count(old) != 1:
        refuse(f"{where}: anchor found {text.count(old)} times: {old[:70]!r}")
    return text.replace(old, new)


# The four module rows of the M3 design's section 7.2, copied as they stand there.
rows = [line for line in m3.splitlines()
        if line.startswith(("| `app/model_questions.py`", "| `app/jev.py`", "| `app/laya_bridge.py`",
                            "| `app/laya_worker.py`"))]
if len(rows) != 4:
    refuse(f"M3 design section 7.2: found {len(rows)} of the four module rows")
jev_row = next(line for line in main.splitlines() if line.startswith("| `app/jev.py` (M3) |"))

EDITS = [
    # section 1
    ("A hidden panel, unlocked by a gesture, sends that same paused moment to jev once and shows jev's "
     "choice next to the agents' actions.",
     "A hidden panel, unlocked by a gesture, lets Jad ask two language models about that same paused "
     "moment, jev (an external service) and Laya (on this machine), one button each, and shows each "
     "model's choice next to the agents' actions."),
    ("- **jev does not drive an episode.** That is deferred, and nothing here blocks it.",
     "- **Neither model drives an episode.** That is deferred, and nothing here blocks it."),
    # section 2
    (jev_row, "\n".join(rows)),
    ("| `sim/tap-unlock.mjs` (M3) | `createTapUnlock({taps: 10, windowMs: 4000}) -> {tap(nowMs) -> boolean}` |",
     "| `sim/tap-unlock.mjs` (M3) | `createTapUnlock({taps: 10, windowMs: 4000}) -> {tap(nowMs) -> boolean}` |\n"
     "| `sim/model-panel.mjs` (M3) | Pure panel logic: `askState(view, k)`, `createAnswers()`, `rowView(answer, i)`, "
     "`failureOf(httpStatus, body)`, `errorText(code, status, lang, kind)`, `statusLine(name, status, failure, "
     "inFlight, lang)`, `MODELS`, `QUESTION_IDS`, `ERROR_CODES` (M3 design §7.2) |"),
    ("| `sim/agent-view.test.mjs`, `sim/agents-strings.test.mjs`, `sim/tap-unlock.test.mjs` |",
     "| `sim/agent-view.test.mjs`, `sim/agents-strings.test.mjs`, `sim/tap-unlock.test.mjs`, "
     "`sim/model-panel.test.mjs`, `sim/agents-page-models.test.mjs` (M3) |"),
    ("In M3, the docstring sentence at `:43` is amended (§7).",
     "In M3, the docstring sentence at `:43` is amended to name the two POSTs, `/api/agents/jev` (an external "
     "service) and `/api/agents/laya` (on this machine) (M3 design §7.6)."),
    # section 3.4
    ("### 3.4 Routes (added by `install(app)`, only under `--simulation`)",
     "### 3.4 Routes (added by `install(app, store=None, jev_send=None, laya=None)`, only under `--simulation`)"),
    ('POST /api/agents/jev    body {"trace": "runs_c4/5/1", "step": 312}      (M3, §7)\n',
     'POST /api/agents/jev    body {"trace": "runs_c4/5/1", "step": 312}      (M3 design §7.6)\n'
     "GET  /api/agents/laya/status                   (M3)\n"
     'POST /api/agents/laya   body {"trace": "runs_c4/5/1", "step": 312}      (M3 design §7.6)\n'),
    # section 6, misreading table
    ('| "jev is part of the thesis" | Hidden by default; the §7 text; no comparison; never applied | jev panel |',
     '| "jev or Laya is part of the thesis" | Hidden by default; the shared honesty lines; no comparison; '
     "never applied | models panel |\n"
     "| \"Laya's answer is an engine judgement\" | «تجربة تشغيل، لا تقييم»; the README line (`README_AR.md:31`); "
     "the order check, held or changed per action (M3 design §7.5b) | models panel |\n"
     '| "Laya sent data out" | The where-it-runs line; the offline variables, the absolute-path check and the '
     "socket guard together (M3 design §7.5); tests 18 to 20 | models panel |\n"
     '| "the models were told nothing about the agents" | M3 design §7.3: the state is the sighted agent\'s own '
     "observation, which already carries its earlier trims in its spark and lambda | models panel |"),
    # section 6, layout
    ("  - main column: the chase view (16:9) with its overlay, the timeline, then the profile;\n"
     "  - side column: picker, verdict box, pause panel, then jev once unlocked.",
     "  - main column: the chase view (16:9) with its overlay, the timeline, the pause panel, the models panel "
     "once unlocked, then the profile (M3 design §7.8, Jad's option 1);\n"
     "  - side column: picker, verdict box."),
    ("  - order: badge, picker, verdict, chase view (4:3), timeline, profile, pause panel;",
     "  - order: badge, picker, verdict, chase view (4:3), timeline, pause panel, profile, models panel once "
     "unlocked (below 1100 px);"),
    # sections 7, 9 and 10: pointers to what replaced them
    ("## 7. jev (M3)\n",
     "## 7. jev (M3)\n\n"
     "*(Replaced by §7 of `2026-09-28-agent-replay-m3-design.md`, approved 28 September and built "
     f"{DAY}, as are rows 14 to 17 of §9 and the M3 part of §10. Kept here as approved.)*\n"),
    ("**M3: the jev paused moment.**\n",
     "**M3: the jev paused moment.** *(Replaced by §10 of `2026-09-28-agent-replay-m3-design.md`.)*\n"),
    # section 8
    ("| jev | §7 |", "| jev, Laya | M3 design §7.9 |"),
]
for old, new in EDITS:
    main = once(main, old, new, MAIN.name)

if GATE_FAILED is None:
    jev_clause = ("jev with no key, and jev forced to fail through a refused local proxy, each stayed in jev's "
                  "column while Laya answered")
else:
    jev_clause = (f"jev with no key stayed in jev's column while Laya answered; jev forced to fail was not run "
                  f"(`{GATE_FAILED}`)")
left = [SAY[m] for m, (state, _) in SHUT.items() if state != "not measured"]
shut_sentence = f"After a Laya press, {join(left)} each left no Laya worker" if left else "No shutdown was measured"
running = [SAY[m] for m, (state, _) in SHUT.items() if state == "running"]
if running:
    shut_sentence += f"; the server itself kept running after {join(running)}"
for m, (state, why) in SHUT.items():
    if state == "not measured":
        shut_sentence += f"; {SAY[m]} was not measured (`{why}`)"
shut_sentence += "."

LOG_ANCHOR = next(line for line in main.splitlines() if line.startswith("| 28 Sep | M3 revisit, Q4 |"))
LOG_ROW = (
    f"| {DAY} | M3 built | **M3 is built and verified; the milestone commit carries every suite's output and "
    "the verification record.** jev and Laya sit behind ten taps on `02 — AGENTS`, forgotten on reload, one "
    "button and one column each; Laya asks twice, options forward and reversed, and each action says held "
    f"or changed. The browser check passed all {BROWSER_N} of its checks at 1440 and 390 px, in Arabic and "
    "English: locked, the panel is hidden and nothing is asked; the pause panel sits under the play bar and "
    "says what to do before «احسب»; an episode played to its natural end enables both buttons at the last "
    "second with no seek; Laya answered on this machine, and test 20 ran it for real; "
    f"{jev_clause}. {shut_sentence} `LAYA_HOME` was unchanged. No real jev call was made. Every departure "
    "the plan made is a dated amendment in the M3 design (\"Amendments while building M3\"); the controller's "
    "rulings and what was left for later are in the build record for M3 below. |")
main = once(main, LOG_ANCHOR + "\n", LOG_ANCHOR + "\n" + LOG_ROW + "\n", MAIN.name)


def listed(items, numbered):
    if not items:
        return "None recorded in the controller's ledger.\n"
    if numbered:
        return "".join(f"{i}. Ruling: {text}\n" for i, text in enumerate(items, 1))
    return "".join(f"- {text}\n" for text in items)


RECORD_MD = (
    f"\n## Build record for M3 ({DAY}): every ruling the controller made, and what was left for later\n\n"
    f"M3 was built from `{PLAN}` (11 tasks). This section copies the controller's build ledger, so that no "
    "decision taken on Jad's behalf and no deferred item lives only in a scratch file. Commits "
    f"`{COMMITS[0]}` through `{COMMITS[-1]}`, and the commit that adds this record, on JMF-2340550-sep17; "
    "every M3 commit's subject starts \"Agent replay M3\". The plan's own departures from the M3 design are "
    "the dated amendments in that file (\"Amendments while building M3\") and are not repeated here.\n\n"
    "### Rulings (each with what it costs if wrong)\n\n" + listed(entries["ruling"], True) +
    "\n### Carried between tasks, and closed\n\n" + listed(entries["closed"], False) +
    "\n### Left for later (M3's own, as the controller deferred them)\n\n" + listed(entries["later"], False))
main = main.rstrip("\n") + "\n" + RECORD_MD

AMEND = [
    "**§7.5 step 1, the socket guard.** The guard replaces only the entry points the platform has "
    "(`if hasattr(owner, name)`). On Windows `socket.socket` has no `sendmsg`; assigning one made "
    "`asyncio/selector_events.py:37` call `os.sysconf`, so `import torch` failed and the worker's ready line read "
    '`{"ready": false, "error": "AttributeError"}` after 0.71 s (measured 28 Sep). Test 19 pins it.',
    f"**§10 step 4, the measurement.** Spawn to ready with `-I -B -X utf8` and `cwd=LAYA_HOME` took {SPAWN_S} s "
    "on this machine (commit \"Agent replay M3 (4a/7)\"), against the spike's 6.2 s.",
    "**§7.5, the worker's process.** Laya's `.venv/Scripts/python.exe` is a launcher: the interpreter runs as "
    "its child, from the base Python named in `pyvenv.cfg`, outside `.venv`. Killing the launcher killed the "
    "child (measured 28 Sep), so the bridge's kill holds; the shutdown checks find the worker by its command "
    "line (`laya_worker.py`), not by a path under `.venv`.",
    "**§7.3, `to_action`.** Each action also carries `options`, its five keys with their physical levels in "
    "`KEYS` order, because the page labels each bar with its level (§7.7) and would otherwise re-type `LEVELS`.",
    "**§7.3, `user_setting`.** It takes `environ=None` (default `os.environ`), for the tests.",
    "**§7.6, the responses.** `model` names the column (`jev` or `laya`) in every body, success or error, and "
    "`model_name` is the name the service returned. Laya's 200 also carries `laya` (its version), `usage` (one "
    "per request) and `answers_reversed`, and its `ms` covers both requests of the press.",
    "**§7.2 and §7.9, the page's error text.** `errorText(code, status, lang, kind)` takes the language, "
    "because the module is pure; `failureOf(httpStatus, body)` turns a response into `{code, status, kind}`, "
    "with `server_down` for a failed fetch.",
    "**§7.7, the reasons.** Before any episode, a disabled button gives the pause panel's empty line "
    "(`agents.pause.empty`) as its reason, not \"wait for the episode to finish\".",
    "**§7.7, the reference line.** «طبّق الوكيلان في هذه الثانية:» ends at the colon, and the two lane dots "
    "carry the values, because the page never calls Phase D's blind car «الأعمى» alone (`agents.mjs`, "
    "`laneLabel`).",
    "**§9, the harness case.** It lives in its own `agents-page-models.test.mjs`, not in "
    "`agents-page-run.test.mjs`: each harness file boots `agents.mjs` once in its own process, and the unlock "
    "adds two status requests to the ordered queue that run.test's existing tests do not answer.",
    "**§10, the commits.** Test 13's allowances arrived with the modules that need them (commits 3 and 4a), "
    "because `jev.py` imports `urllib` and the old `NET_ALLOWED = set()` would have failed in between; commit 4 "
    "was split into 4a (the worker) and 4b (the bridge); and commit 6 was split into 6a (`tap-unlock.mjs`, "
    "`model-panel.mjs` and the strings, pure and node-tested) and 6b (the markup, the CSS and the `agents.mjs` "
    "wiring).",
    "**§7.8 against C13, the order below 1100 px.** Pause 5, profile 6, models 7, as §7.8 says: on a phone the "
    "models panel follows the profile, not the pause panel as C13 says. On wide screens it follows the pause "
    "panel.",
    "**§7.8, the empty line.** The pause heading carries `data-i18n=\"agents.pause.empty\"`: `draw()` returns "
    "before `renderPanel` while there is no road, so without it an English page kept the static Arabic line "
    "until an episode arrived (seen at 1440 px in English in the plan's prototype browser check).",
]
NETWORK_OFF = (
    "**§10 Verify, \"network off\".** jev is forced to fail by a refused local proxy: that server alone is "
    "started with `TYPESAFE_API_KEY=dummy-not-a-key`, `HTTPS_PROXY` and `HTTP_PROXY` set to "
    "`http://127.0.0.1:9` and an empty `NO_PROXY`, after a gate shows that urllib would use that proxy and that "
    "127.0.0.1:9 refuses (Windows answers a closed local port after about 2 s; measured 2.04 s). An agent "
    "cannot switch the network off, and with a dummy key on a working network the call would reach "
    "api.typesafe.ai.")
if GATE_FAILED is None:
    NETWORK_OFF += (" It ran: jev showed its failure in its own column and Laya answered (15 of 15 browser "
                    "checks).")
else:
    NETWORK_OFF += (f" On this machine the gate failed (`{GATE_FAILED}`), so that server was never started; jev "
                    "with no key is the check that a jev failure leaves Laya answering.")
AMEND.append(NETWORK_OFF)
RESULT = {"stopped": "no Laya worker left", "running": "no Laya worker left, the server still running"}
AMEND.append(
    "**§10 Verify, the shutdown checks.** Each follows a Laya press and counts the `laya_worker.py` processes "
    "5 s later. The hard kill is `Stop-Process -Force` on the server the browser check used. Ctrl+C and "
    "closing the window run on a server started in a console window of its own (`conhost.exe`, so it is a "
    "classic console whatever the default terminal is), from outside it: a helper attaches to that console "
    "and generates `CTRL_C_EVENT` on it, which is what the key press does, or posts `WM_CLOSE` to its window, "
    "which is what the close button sends. Results: " + "; ".join(
        f"{SAY[m]}: {RESULT[state] if state != 'not measured' else f'not measured (`{why}`)'}"
        for m, (state, why) in SHUT.items()) + ".")
if (CC_422, CC_405) == ("no-store", "no-store"):
    print("FastAPI's own 422 and 405 responses also send no-store: no amendment needed for them")
else:
    AMEND.append(
        "**The rule that every response of the four routes carries `Cache-Control: no-store`.** FastAPI's own "
        "422, for a body that fails `AskBody` (validated before the handler runs), and its 405 are not written "
        f"by the handlers: Task 10's probes read `422 cache-control: [{CC_422}]` and "
        f"`405 cache-control: [{CC_405}]`. Neither holds a model's answer or the key: the 422 lists the fields "
        "that failed, with the values the page sent, and the 405 says only that the method is not allowed. "
        "Every body the four handlers write carries no-store.")

AMEND_MD = (f"## Amendments while building M3 ({DAY})\n\n"
            f"Each is a departure the implementation plan (`{PLAN}`) made from this file, with its evidence. "
            "Where the two differ, the code wins, and this list says so. The verification results in 14 to "
            f"{len(AMEND)} are read from Task 10's record.\n\n"
            + "".join(f"{i}. {text}\n" for i, text in enumerate(AMEND, 1)) + "\n---\n\n")
m3 = once(m3, "## Appendix: Review issues not taken\n", AMEND_MD + "## Appendix: Review issues not taken\n", M3.name)

MAIN.write_text(main, encoding="utf-8", newline="\n")
M3.write_text(m3, encoding="utf-8", newline="\n")
print(f"wrote {len(EDITS)} amendments, the {DAY} log row and the M3 build record "
      f"({len(entries['ruling'])} rulings, {len(entries['closed'])} closed, {len(entries['later'])} left for later) "
      f"into {MAIN}")
print(f"wrote {len(AMEND)} dated amendments into {M3}")
```

If this plan is saved under another name, change `PLAN` to that path before running.

- [ ] **Step 3: Write the ledger, try the script on copies, then on the repository**

This step belongs to the controller, because only the controller holds the build ledger. Write `C:\Users\admin\AppData\Local\Temp\claude\c--Users-admin-Documents-graduation-project-GRAD-project\m3-build\m3-ledger.txt` with the Write tool, one line per entry of the controller's M3 ledger and nothing else:
- `ruling: <what, and why> -- cost if wrong: <cost>` for every ruling taken on Jad's behalf;
- `closed: Task <a> to Task <b>: <what>` for every item carried between tasks and closed;
- `later: Task <n>: <severity> (deferred): <what> (<file>:<line>)` for every review finding left for later.

Nothing is written into the ledger from this plan. If the controller's ledger holds no entries, create the file empty; the three sections then read "None recorded in the controller's ledger." The script refuses any other line shape, and any ruling without its cost.

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
SPAWN_S=6.11   # replace with the figure read in Step 1
rm -rf "$SCRATCH/m3-design-copy"; mkdir -p "$SCRATCH/m3-design-copy"
cp docs/superpowers/specs/2026-09-26-agent-replay-design.md docs/superpowers/specs/2026-09-28-agent-replay-m3-design.md "$SCRATCH/m3-design-copy/"
$PY "$(cygpath -w "$SCRATCH/m3_amend_design.py")" "$SPAWN_S" "$(cygpath -w "$SCRATCH/m3-verification.txt")" "$(cygpath -w "$SCRATCH/m3-ledger.txt")" "$(cygpath -w "$SCRATCH/m3-design-copy/2026-09-26-agent-replay-design.md")" "$(cygpath -w "$SCRATCH/m3-design-copy/2026-09-28-agent-replay-m3-design.md")"
$PY "$(cygpath -w "$SCRATCH/m3_amend_design.py")" "$SPAWN_S" "$(cygpath -w "$SCRATCH/m3-verification.txt")" "$(cygpath -w "$SCRATCH/m3-ledger.txt")" "$(cygpath -w "$SCRATCH/m3-design-copy/2026-09-26-agent-replay-design.md")" "$(cygpath -w "$SCRATCH/m3-design-copy/2026-09-28-agent-replay-m3-design.md")"
git diff --no-index --stat docs/superpowers/specs/2026-09-26-agent-replay-design.md "$SCRATCH/m3-design-copy/2026-09-26-agent-replay-design.md"
git diff --no-index --stat docs/superpowers/specs/2026-09-28-agent-replay-m3-design.md "$SCRATCH/m3-design-copy/2026-09-28-agent-replay-m3-design.md"
grep -F "| M3 built |" "$SCRATCH/m3-design-copy/2026-09-26-agent-replay-design.md"
```

Expected:
- The two `wrote …` lines, with the ledger's counts.
- `already in the design: nothing written`.
- `41 insertions(+), 13 deletions(-)`, plus one insertion for each ledger entry after the first in its section; and `23 insertions(+)`, or `22` when the probes showed `no-store` on both. These are the 28 Sep figures from the copies.
- The generated row. Read it against the record: every claim in it must be one the record shows.

A `REFUSED, nothing written: …` line names what the record or the ledger lacks. Fix that at its source: re-run the Task 10 step it names, or correct the ledger line. Do not edit the script to get past it. An `anchor found 0 times` means another session edited that passage since d347ee5: read the current text, correct that one anchor in the script, and try again on fresh copies.

Then run it on the repository:

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
SPAWN_S=6.11   # the same figure as above
$PY "$(cygpath -w "$SCRATCH/m3_amend_design.py")" "$SPAWN_S" "$(cygpath -w "$SCRATCH/m3-verification.txt")" "$(cygpath -w "$SCRATCH/m3-ledger.txt")"
git diff --stat docs/superpowers/specs/2026-09-26-agent-replay-design.md docs/superpowers/specs/2026-09-28-agent-replay-m3-design.md
```

Expected: the same two `wrote …` lines, and the same diffstat as on the copies.

- [ ] **Step 4: Check the documents**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
git add docs/superpowers/specs/2026-09-26-agent-replay-design.md docs/superpowers/specs/2026-09-28-agent-replay-m3-design.md
$PY verify_docs.py 2>&1 | tail -1
```

Expected: the last line starts `All ` and ends `figure mentions scanned in the documents).`

If it names a line in the amendments, a figure in that sentence has been retired. Then:
1. If the sentence comes from the script, reword it in `m3_amend_design.py`. If it comes from the ledger, reword it in `m3-ledger.txt`.
2. Run `git checkout -- docs/superpowers/specs/2026-09-26-agent-replay-design.md docs/superpowers/specs/2026-09-28-agent-replay-m3-design.md`.
3. Run Step 3's repository command again.

- [ ] **Step 5: The milestone commit**

The message's verification paragraph is the walkthrough-log row that the script generated from the record, so the message states nothing the record does not show.

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH=/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/m3-build; mkdir -p "$SCRATCH"; cd "/c/Users/admin/Documents/graduation project/GRAD-project"
{
  printf '%s\n' "Agent replay M3: jev and Laya at the paused moment, verified" "" \
    "jev (typesafe.ai, external, key-gated) and Laya (local, its own .venv, a" \
    "persistent JSON-lines worker) sit behind ten taps on 02 -- AGENTS, forgotten on" \
    "reload, one button, lock, answer and error each. Both get the same question" \
    "from app/model_questions.py about the paused second only, when playback is" \
    "stopped on a finished episode (the natural end included). Laya is asked" \
    "twice, options forward and reversed, and each action says held or changed." \
    "Nothing is applied, averaged, compared with the agents or saved. The pause" \
    "panel sits under the play bar and says what to do before an episode (Jad," \
    "design 7.8 option 1). Design: the M3 design's consequential amendments" \
    "applied to the main design, a walkthrough-log row and the build record for" \
    "M3 from the controller's ledger; dated amendments in the M3 design for every" \
    "departure the plan made." "" \
    "Verification, as the walkthrough-log row generated from the record below says it:"
  grep -F "| M3 built |" docs/superpowers/specs/2026-09-26-agent-replay-design.md | sed -e 's/^| [^|]* | M3 built | //' -e 's/ |$//'
  printf '\n$ M3 verification record\n'; cat "$SCRATCH/m3-verification.txt"
  printf '\n$ python verify_docs.py   (last line)\n'; $PY verify_docs.py 2>&1 | tail -1
  printf '\n$ python -m app.test_replay --full\n'; cat "$SCRATCH/m3_replay_full.txt"
  printf '\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n'
} > "$SCRATCH/m3_msg.txt"
grep -c "PROVEN" "$SCRATCH/m3_msg.txt"; grep -c "UNPROVEN" "$SCRATCH/m3_msg.txt"
grep -c "^    Laya: cuda\|^    Laya: cpu" "$SCRATCH/m3_msg.txt"; grep -c "skipped 'LAYA_HOME" "$SCRATCH/m3_msg.txt"
git commit -F "$SCRATCH/m3_msg.txt" -- docs/superpowers/specs/2026-09-26-agent-replay-design.md docs/superpowers/specs/2026-09-28-agent-replay-m3-design.md
git log --oneline -1
git status --short
```

Expected:
- The four `grep -c` lines print, in order:
  - `PROVEN`: 2 or more (the default proof and `Phase D == proof PROVEN`);
  - `UNPROVEN`: `0`;
  - `^    Laya: cuda` or `^    Laya: cpu`: `1`. Test 20 prints that observation line only after every assertion passed, so it is the proof that it ran. Its `ok` sits on a line of its own that the record does not carry.
  - `skipped 'LAYA_HOME`: `0`.

  If any count differs, do not commit: test 20 did not run for real. Go back to Task 10 Step 2.
- The commit lands on `JMF-2340550-sep17` with the subject `Agent replay M3: jev and Laya at the paused moment, verified`.
- `git status --short` lists no M3 file.

Earlier commit messages are history and are never amended. Jad's Arabic summary is the session's close routine, not part of this plan.


---

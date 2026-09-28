# Agent replay, M3 — jev and Laya at the paused moment: design

> **STATUS: APPROVED BY JAD, 28 September 2026.** His last answer (§7.8, Q1): **move the pause panel under the
> play bar and give it the one-line empty state** (option 1, recommended). Commit step 7 of §10 is therefore in.
> Everything else here follows Jad's decisions of 28 September (the walkthrough log of
> `2026-09-26-agent-replay-design.md`, rows "M3 revisit, Q1-Q3"): Laya is hidden WITH jev behind the same gesture;
> one button per model, independent answers and errors; **Laya gets an automatic order check (§7.5b)**.
> Inputs: the Laya spike (`2026-09-28-laya-spike.md`), a reading of the M2 code, and a design review whose ten
> issues all held and were taken. When approved, this file replaces §7 ("jev (M3)"), rows 14-17 of §9 and the
> M3 part of §10 of `2026-09-26-agent-replay-design.md`; the consequential amendments are listed at the end.


> **Status: DRAFT for Jad's review, 28 September 2026. Revised the same day after the design review.** All ten review issues were checked against the code and all ten held. Three were fixed in a different way from the one the review proposed; the appendix explains each.
>
> This text replaces §7 ("jev (M3)"), rows 14–17 of §9, and the M3 part of §10. It also lists the small edits it forces in §1, §2, §3.4, §6 and §8. Tags:
>
> - **[changed from §7]** marks every departure from the approved §7.
> - **[new]** marks anything with no counterpart in §7.
> - Untagged text is §7 as approved.
>
> The design rests on three read-only reports from 28 September:
>
> - the **spike**, which ran Laya on this machine;
> - the **reading report**, which mapped every place in the code M3 touches;
> - the **design review**.
>
> Line numbers are at commit `15dc774`. References into the Laya library (`laya/agent.py`, `laya/common.py`) are to laya 0.3.20 inside Laya's own `.venv`.

---

## 7. The two models (M3)

### 7.0 What changed from the approved §7

| # | §7 said | now | why |
|---|---|---|---|
| C1 | one model, jev | two models, jev and Laya, behind the same gesture | Jad, 28 Sep (walkthrough, "M3 revisit, Q1") |
| C2 | one panel, `#jev-panel` | one panel, `#models-panel`, with one column per model | the same |
| C3 | one button | **one button per model**, each with its own answers, lock and errors | Jad, 28 Sep ("Q2"): "I may have no credit on jev, so the other must not fail with it" |
| C4 | the question set, `LEVELS`, `NET`, `OPTIONS`, `decode` and `to_action` live in `app/jev.py` | they live in a new `app/model_questions.py`, which both models import | both models get the same question from one source, so the comparison is fair |
| C5 | a single lock: "one call at a time… 409 busy" | one lock **per model** | with a single lock, a jev call that hangs for its 10 s timeout would make Laya "busy" |
| C6 | 404 unknown / 409 `trace_gone` / 409 `step_not_computed` against `len(frames)` | one 409 `no_trace` for an unknown, evicted or unfinished trace; `step_not_computed` is bounded by `len(trace.obs[0])` | the store returns `None` in all three cases (`agent_api.py:151-154`, `:218-220`), and there can be more frames than sighted-lane observations (`agent_api.py:118-122`) |
| C7 | the trace pattern `^runs[A-Za-z0-9_]*/…`; `step: int` with `le=718` | an **anchored** `TRACE_KEY` built from `agent_catalog.RUNS_NAME` (`agent_catalog.py:41`), `SEED_TEXT` and `EP_TEXT` (`agent_api.py:244-245`); `step` bounded by `le=agent_trace.STEPS - 1`; the model is `strict=True` | the old pattern accepted `runs_C4`, which the server answers with 404. Pydantic's `pattern` is an unanchored search, so a join of unanchored parts accepts `xx/runs_c4/5/1/zz` (measured, pydantic 2.13.5). Lax Pydantic accepted `"312"` and `true` as a step (reading report, measured). The episode route already refuses a bool seed (`agent_api.py:44`). 718 is `STEPS - 1` (`agent_trace.py:29`) |
| C8 | Origin must be `http://127.0.0.1:<port>` or `http://localhost:<port>`; `install` does not know the port; a request with no Origin passes | Origin **must be present** and must equal `http://` + Host, and Host must be `127.0.0.1:N` or `localhost:N` | `install(app)` is not given the port (`server.py:303`). Checking Host as well stops DNS rebinding. Browsers send Origin on every POST |
| C9 | the page shows `confidence` beside the probabilities | the page shows the five probabilities and **the chosen option's probability**, and never `confidence` | for Laya, `confidence` is a normalised entropy that is *not* calibrated (`laya/common.py:289-299`), and `answer_confidence` = max(p) is a different number (`:273-286`). Two fields both called "confidence" that mean different things, side by side, invite comparing unlike numbers |
| C10 | the ask button is enabled while paused, and a partial build is allowed | a button is enabled only while **playback is stopped (the play button shows play)** and the episode has **finished computing** | the store serves only finished traces (C6). `userPaused` cannot be the test: it stays false when an episode plays to its end (`agent-view.mjs:185`, `playback.mjs:7`) |
| C11 | the `server.py:43` sentence names one POST | it names two POSTs, one external and one local | §7.6 |
| C12 | option keys written with U+2212 ("ceiling −40 kPa") | option keys in ASCII ("ceiling -40 kPa"), as the spike sent them | a key is looked up, never displayed; ASCII removes one Unicode trap |
| C13 | the panel sits in the side column, "then jev once unlocked" | the panel comes directly after the pause panel, wherever the pause panel is (§7.8) | layout; see the discoverability question |
| C14 **[new]** | jev errors: vendor 401 / 403 / 422 / 429 / 529 and nothing else | a catch-all `vendor_status` for every other non-2xx reply. It carries only the integer HTTP status, and its sentence says it may mean the account has no credit | Jad's reason for decision 2 is running out of credit (spec `:795`), and the vendor documents no status for that:<br>• `api.md:329-334` lists only 401, 422, 429 and 529;<br>• the SDK adds 400, 403, 404 and 5xx (`sdk_python_api_exceptions.md:156-216`);<br>• `legal_mca.txt:56` says only that TypeSafe "may decline to generate Output" |

Everything else §7 wrote for jev still holds as written:

- the key rules;
- the vendor paragraph;
- the request URL and model;
- the five questions and their texts;
- the float32 mapping;
- the latency caption;
- the error table, apart from C6 and C14;
- the deferral of driving.

They are restated below only where they now live in a different file.

### 7.1 Jad's decisions this section implements (binding)

1. Laya is hidden **with** jev, behind the same ten taps on `02 — AGENTS`.
2. There is **one button per model**. A jev failure never blocks or hides Laya, and the reverse is also true.
3. There are **five choice levels per action**, as §11 Q3 approved.
4. The models see **the sighted agent's view**: `trace.obs[0][step]`.
5. They are asked about **the paused moment only**. A model driving a whole episode stays deferred.
6. **The unlock is forgotten on reload.**

### 7.2 Units and files

**Python.** All four new modules sit at the top level of `app/`, so the scan in `app.test_replay`'s `test_read_only` (`test_replay.py:522-555`) covers them unchanged. None is hashed into `plant_sha`.

| module | its one job | interface | imports |
|---|---|---|---|
| `app/model_questions.py` **[new; C4]** | The one question both models are asked, and the one way their answers become actions | `LEVELS`, `NET`, `OPTIONS`, `QUESTIONS`<br>`decode(obs) -> dict`<br>`build_state(trace, step) -> dict`<br>`to_action(answers) -> dict` (raises `BadAnswer`)<br>`user_setting(env_var, file_name) -> (value, source)` | `engine_env`: `ACT_LO`, `ACT_HI`, `neutral_action`, `PREVIEW_S`, `TURB_PROTECT_K`, `OIL_PROTECT_K`<br>`app.agent_api.Trace` |
| `app/jev.py` **[changed from §7: slimmed]** | Send one question set to jev and return its answer | `load_key()`<br>`build_request(trace, step) -> dict`<br>`ask(trace, step, send=_send, clock=perf_counter) -> dict` | `model_questions`, `urllib.request` |
| `app/laya_bridge.py` **[new]** | Start, keep and stop Laya's worker; ask it one question set | `load_home() -> (python, model_dir, source)`<br>`class LayaBridge(command=None, start_timeout=90, answer_timeout=20)` with `.status()`, `.ask(trace, step)`, `.close()`<br>`worker_env() -> dict`<br>Building a `LayaBridge` reads no file and starts nothing | `model_questions`, `subprocess`, `threading`, `queue`, `json`, `os`, `sys`, `pathlib`, `atexit` |
| `app/laya_worker.py` **[new]** | Runs **only** under Laya's own `.venv` python and is never imported by the server. Loads Laya once and answers one JSON line per request | `python -I -B -X utf8 laya_worker.py <model_dir>` | stdlib, `laya`, `torch`. It imports `socket` only to refuse it (§7.5) |
| `app/agent_api.py` (edit) | Adds four routes inside `install()`, which gains two injection points | `install(app, store=None, jev_send=None, laya=None)`:<br>• `jev_send` defaults to `jev._send`;<br>• `laya` defaults to `LayaBridge()`, built in `install()` with no I/O (§7.6) | `jev` and `laya_bridge`, imported inside `install()` |

**Frontend.**

| file | job |
|---|---|
| `sim/tap-unlock.mjs` (as §7) | `createTapUnlock({taps: 10, windowMs: 4000}) -> {tap(nowMs) -> boolean}`. It uses no storage API. |
| `sim/model-panel.mjs` **[new]** | Pure panel logic that node can test, so no new decision lives in `agents.mjs`, which has little behavioural coverage (M1 left-for-later, Task 9):<br>• `askState(view, k)` returns `{enabled, reason}`;<br>• `createAnswers()` returns `{put(key, k, answer), get(key, k), clear()}`, one entry per second;<br>• `rowView(answer, actionIndex)`;<br>• `errorText(code, status)`;<br>• `ERROR_CODES`. |
| `agents.html` | A static `<section id="models-panel" class="models-panel" hidden>`, placed directly after the pause panel (`agents.html:93-108`). Both columns' ids are written out, so test 12 can see them. |
| `agents.mjs` | Wiring only: the gesture on `#footer-index`, the two status calls, the two buttons, and `renderModels()`, which renders from `model-panel.mjs` (§7.7 lists where it is called). |
| `agents-strings.mjs` | Every new string in both languages. The existing rules apply: «المنمذَج», and no "preview helps". |
| `agents.css` | • `.models-panel` and its two columns;<br>• `order:7` in the `<1100 px` list (`agents.css:135`);<br>• `.models-panel{align-self:stretch}`, because below 1100 px the column otherwise hugs the start edge (`agents.css:22`, measured);<br>• `touch-action:manipulation` on `.footer-index` (`agents.css:127`), so ten fast taps on a phone do not zoom.<br>None of these changes the page while it is locked. |

### 7.3 The shared question set (`app/model_questions.py`) [new file; content from §7]

**One source, so the comparison is fair.** Both routes call `build_state(trace, step)` and send `QUESTIONS`, the same module-level object. Test 15 pins that jev's body and Laya's request carry `==` state and the identical `questions` for the same `(trace, step)`.

**`build_state(trace, step)`** (§7's `state`, unchanged). It accepts only an `agent_api.Trace`, so browser state can never be sent.

- `engine` is `decode(trace.obs[0][step])`: the sighted agent's actual observation, inverted from `engine_env._obs` (`engine_env.py:646-671`, clipped to ±10 at `:671`) into named physical units. The field list is §7's:
  - engine and charge;
  - the four temperatures;
  - surroundings;
  - `grade_now_percent` and `grade_ahead_percent`, keyed from `PREVIEW_S` (`engine_env.py:517`);
  - the driver fields;
  - `priorities`, from obs 20–22, which the tracer pins to the episode's weights (`agent_trace.py:180`);
  - the "simulated synthetic stress scenario" note.
- `task` is §7's fixed paragraph, with `TURB_PROTECT_K` and `OIL_PROTECT_K` imported (`engine_env.py:490-491`).

**What is and is not sent.**

- **Not sent as fields:** the agents' actions, the experiment or its verdict, and anything from `logs/raw`, `app.replay`, `app.reader` or `app.estimator`.
- **Carried inside the state, and stated here so no text on the page claims otherwise:** the state is the one the sighted agent's earlier decisions produced.
  - Its `spark_advance_deg_BTDC` and `lambda` are the values applied in the previous second, with that agent's trims already added. They are observation entries 3 and 4 (`engine_env.py:653-654`), set from `sp_b + act[0]` and `lam_b + act[1]` (`engine_env.py:771-773`).
  - Its manifold pressure and throttle follow from the agent's boost setting.

**`QUESTIONS`** holds five questions of `type: "choice"`. The ids, instructions and five levels are exactly §7's table.

- Each option key is ASCII **[C12]**.
- Each description reads "{action} {signed level} {unit}", as the spike sent it.
- Laya accepts this shape unchanged: criteria as a label → description dict (`laya/agent.py:496-501`), with `instructions` required (`:493-494`).
- Measured in the spike:
  - the state is 430 tokens;
  - each question row is 505–541 of Laya's 1024-token cap;
  - no instruction was cut, although Laya would cut one silently on overflow (`laya/common.py:102-107`).
- **A known risk, not a defect today:** Laya cuts a dict state from the right (`laya/agent.py:565-568`). If `engine` ever grew past about 900 tokens, `task`, which is serialised after it, would be dropped first and without warning. Test 20 guards the size.

**`LEVELS`, `NET` and `OPTIONS`** are §7's, unchanged:

- `LEVELS` is a 5 × 5 float32 table built from `ACT_LO`, `ACT_HI` and `neutral_phys` (`agent_api.py:262`).
- `NET` is computed vectorised in float32, exactly as `neutral_action()` computes it (`engine_env.py:1002-1005`), and is bitwise equal at the neutral levels.
- `OPTIONS` maps a key back to a level by dictionary lookup. Strings are never parsed.

**`to_action(answers)`** gives, per action, `{choice, level_phys, level_net, probabilities, chosen_p}`, where `chosen_p = probabilities[choice]` **[C9]**. It raises `BadAnswer` when:

- any of the five ids is missing;
- `choice` is not one of that question's five keys;
- `probabilities` does not hold exactly those five keys;
- any probability is not finite, or lies outside [0, 1].

The same rules apply to both models. Nothing else from an answer is kept: `confidence`, `answer_confidence` and `action` are dropped **[C9]**.

**`user_setting(env_var, file_name)`** **[new; generalises §7's `load_key`]**:

- It reads the environment variable. Failing that, it reads the file `<APPDATA>/grad-project/<file_name>`. It returns `(value, "env" | "file")`, or `(None, None)`.
- It path-checks only **the file it reads**: it refuses that file if it resolves under the repository root (CLAUDE.md mistakes 11 and 16, as §7 argued).
- It **never** treats a value as a path. The server runs with the repository as its working directory (`app/start-simulation.ps1:14`), so resolving a key string would place it "under the repository" and refuse every key.
- jev uses it for the key (`TYPESAFE_API_KEY`, `typesafe_key`). Laya uses it for its folder (`LAYA_HOME`, `laya_home`); `load_home()` then checks that folder as a path (§7.5).

### 7.4 jev (`app/jev.py`) [unchanged from §7 except C4, C6, C9 and C14]

- `build_request(trace, step)` returns `{"model": "jev-latest", "state": build_state(...), "questions": QUESTIONS}`, sent to `POST https://api.typesafe.ai/v1/systemone`.
- `load_key()` is `user_setting("TYPESAFE_API_KEY", "typesafe_key")`, read on each call.
- The key appears only in the `Authorization: Bearer` header built inside `_send`. It is never logged, never returned, and never placed in an error.
- There is one call per press, no retries, and a 10 s timeout.
- Latency is measured with `perf_counter` around the HTTP call.
- `score` questions are rejected.
- A non-2xx reply that §7.9 does not name becomes `vendor_status` **[C14]**. Only the integer status is kept; the vendor's body is dropped.

### 7.5 Laya: a local worker process [new]

**Why a separate process, not an import.**

- The server's interpreter, the system Python 3.12, has torch but no `laya`, `transformers` or `safetensors` (spike, `find_spec`). Installing them would change the interpreter that runs the scored `==` proof.
- A worker running Laya's own `.venv` python leaves both environments untouched.
- It also keeps Laya's CUDA context, its stdout prints and its out-of-memory fallbacks out of the server process that computes the agents' numbers.

**How it is found.** `load_home()` reads `user_setting("LAYA_HOME", "laya_home")`: Laya's folder, `C:\Users\admin\Documents\Local AI\laya` on Jad's machine. `load_home()` is called by `status()` and before each start; the bridge's constructor never calls it.

- The python is `LAYA_HOME/.venv/Scripts/python.exe` (`bin/python` on other systems).
- The model is `LAYA_HOME/models/multilingual`, as `try_laya.py:30-32` loads it.
- Both must exist, the model folder must hold `rl_agent_config.json`, and **neither may resolve under the repository**. This is the one place a setting's value is checked as a path.
- No path is written into the code, because the teammates' machines differ (M2 ruling 8).
- Jad sets it once with `setx LAYA_HOME "C:\Users\admin\Documents\Local AI\laya"`, then starts the server from a new window.

**When it is started.** Only when all three hold:

1. The server runs `--simulation`. The bridge is constructed in `install()`, which only that branch calls (`server.py:302-303`, test 10).
2. Someone presses **«اسأل لايا»**.
3. No worker is alive.

Unlocking the panel does not start it, and neither does the status route. The press that starts it waits for the worker to become ready; later presses reuse it.

**How it is started.** `subprocess.Popen([python, "-I", "-B", "-X", "utf8", <app>/laya_worker.py, model_dir], cwd=LAYA_HOME, env=worker_env(), stdin=PIPE, stdout=PIPE, stderr=None, text=True, encoding="utf-8")`.

- `-I` leaves the worker's own folder (`app/`) off `sys.path`, so it can import nothing from the repository. It also ignores `PYTHON*` variables, which is why `-X utf8` sets the encoding instead.
- `-B` writes no bytecode, so nothing lands in `app/__pycache__` or in Laya's `.venv`.
- `stderr=None` sends the worker's stderr to the server's console only, never to disk. This also answers M2 Task 4's "the 500s log nothing".
- `worker_env()` is the server's environment with these changes:
  - **`TYPESAFE_API_KEY` and any `HF_TOKEN*` removed**;
  - `USE_TF=0`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `HF_HUB_DISABLE_TELEMETRY=1` and `TOKENIZERS_PARALLELISM=false` added;
  - `HF_HOME=LAYA_HOME/.cache/huggingface`, the folder `try_laya.py:10` already uses. In the spike nothing was created there.
- *The spike ran the worker without `-I`. Milestone step 4 measures `-I` on this machine before anything else is built on it.*

**The worker** (`laya_worker.py`), in this order:

1. **It installs the network guard, before `torch` or `laya` is imported.** Eight entry points are replaced with functions that count the attempt and raise:
   - `socket.socket.connect`, `connect_ex`, `sendto` and `sendmsg`;
   - `socket.create_connection`, `getaddrinfo`, `gethostbyname` and `gethostbyname_ex`.
2. It checks that `argv[1]` is an absolute, existing folder. Laya never downloads when given an absolute path that is missing; it raises instead (`laya/agent.py:252-258`). Its one download call, `snapshot_download`, is reached only for a relative path that is missing (`:259-270`).
3. It keeps the real stdout as the protocol stream and sets `sys.stdout = sys.stderr`, because Laya prints its warnings to stdout (`laya/agent.py:302, 431, 465, 628`).
4. It runs `laya.load(model_dir, device="cuda" if available else "cpu")` and one warm-up predict.
5. It sends one ready line, `{"ready": true, "device", "laya": <importlib.metadata version>, "load_s"}`, or `{"ready": false, "error": <kind>}` on failure.
6. It then answers one request per line:
   - in: `{"id", "state", "questions"}`;
   - out: `{"id", "ok": true, "device", "ms", "model", "answers", "net_attempts"}`, or `{"id", "ok": false, "error": <kind>}`.

   The kind is the exception's class name, never `str(exc)`. After a bad request the worker stays alive (spike).
7. It exits on stdin EOF.

Protocol lines are written with `print(json.dumps(...), file=proto, flush=True)`.

**The pipe, and the lab's read-only scan.** The bridge sends each request with `print(line, file=proc.stdin, flush=True)`.

- `test_read_only` bans `\.write\s*\(` as a "raw port write" (`test_replay.py:531`), and `print(file=)` does not match that pattern.
- **That is not why the pipe is allowed.** The scan looks for a path to the vehicle, and a pipe to a child process on this machine is not one.
- The alternative, an exemption inside `test_replay.py`, would edit a lab test, which §2 forbids.
- Because the lab scan cannot see this form, test 19 scans **every** `app/*.py` outside the test files. Every `print` with a `file=` keyword must target `sys.stderr`, except exactly two: the worker's protocol stream and the bridge's `proc.stdin`.

**Kept warm, and shut down with the server.**

- The worker stays resident for the server's lifetime. It holds 1.2–1.5 GB of GPU memory by `torch.cuda`'s count and adds 1.7 GB by `nvidia-smi`'s (spike).
- The status line says it is loaded until the server stops. There is no idle timeout and no unload button; this keeps M3 small.
- On the first start, `atexit.register(bridge.close)` is installed. `close()` closes stdin, waits 5 s, then kills.
- If the server dies without running `atexit`, the pipe closes and the worker reads EOF. In the spike it then exited in 0.68 s with code 0.
- *A hard kill of the server has not been measured; milestone step 8 checks it with `Get-Process`.*
- A worker that died between presses is detected by `proc.poll()` and restarted by the next press.

**Timeouts and timing.**

- **Start: 90 s** to the ready line. Measured:
  - 6.1–6.2 s warm, from spawn to ready;
  - 12.2 s on the first run after a cold disk;
  - 32.7 s for the whole of `try_laya.py` from a cold disk.
- **Answer: 20 s.** Measured on CUDA: 107–744 ms for the first request, then 33.7–34.8 ms. A CPU answer is **not measured**, and 20 s may prove too short on the CPU. If so it shows as `timeout`, never as a wrong answer.
- On either timeout the worker is killed, because a late line would put the protocol out of step. The next press starts it again.
- A reply whose `id` differs from the request's is `bad_answer`, and the worker is killed.
- A reply with `net_attempts > 0` is `network_attempt`: the answer is dropped and the worker is killed.
- The reader is a daemon thread that puts stdout lines on a `queue.Queue`, and `ask()` calls `get(timeout=…)`. The thread is needed because a pipe cannot be polled with a timeout on Windows.

**The GPU while an episode build holds it.**

- Both buttons need a finished trace (C10), so an ask can never overlap the build of the episode on screen. Another tab can start a build, though.
- The worker is a separate process with its own CUDA context. It can slow a build, and a build can slow it, but neither can change the other's numbers: the trace an ask reads is already finished and frozen in memory.
- If the card lacks memory when Laya loads, Laya moves to the CPU and computes in fp32 (`laya/agent.py:411-425`). A missing CUDA does the same, with a printed warning (`:299-303`). CPU answers can differ from CUDA answers, **so every Laya answer shows the device it was computed on**.
- The agents' device line (§6) is unchanged.

**What it can reach and write.**

- **Network.** The claim that Laya sends nothing out rests on three measures together:
  - the offline variables in `worker_env()`;
  - the absolute-path check, which leaves Laya's one download call unreachable;
  - the guard.

  The guard's count means only this: **no attempt through Python's socket API was recorded.** Native libraries that open their own connections are not seen by it. The spike recorded 0 attempts across every load and predict.
- **Files read:** the model folder only (`laya/agent.py:279-335`).
- **Files written:** none were measured (spike: `find <laya> -newer` was empty, and the repository was clean). Laya's one write path, `_fix_tokenizer_config` (`laya/agent.py:33-85`), is a no-op on this checkpoint (`verification.json:76-78`). Test 20 snapshots `LAYA_HOME` before and after.

**What the spike saw of Laya's answers.** This was one runtime probe, not an evaluation, and the page does not present it as one.

- On the hot climb (turbine 881 °C), Laya chose to advance spark by 4° and to lean the mixture by 0.06: the opposite of protecting the turbine.
- A flat road at 434 °C gave the same five choices.
- Changing the priorities to protect_components 0.9 also gave the same five choices.
- **Reversing the option order changed four of the five choices.** Fan and pump picked whichever option was listed last.

Its answers follow option position more than engine state. Question Q2 in §7.11 asks whether the page should say so.

### 7.5b The order check for Laya [new — Jad, 28 Sep, "M3 revisit, Q3"]

The spike found that Laya's choices moved with the ORDER of the options more than with the engine state
(`2026-09-28-laya-spike.md` §2). Jad chose to keep Laya and let the page test this itself, on every press.

- **Every «اسأل لايا» sends two requests to the worker, back to back:** `QUESTIONS` (the design's order, the
  same object jev receives) and `QUESTIONS_REVERSED` — the same five questions with each question's five
  criteria listed in reverse order. Keys, instructions and descriptions are identical; only the order differs.
  Both are built in `model_questions.py`; a test pins that the reversed set has the same keys, texts and
  descriptions per question and only the order reversed.
- Laya is deterministic (spike: identical answers over 11 calls), so any difference between the two answers
  comes from the order alone. Cost: two warm calls, about 70 ms. Both pass `to_action`; a `BadAnswer` in
  either is `bad_answer` for the press.
- **Per action the column shows:** the choice in the design's order (the primary answer, with its five
  probabilities as in §7.7), the choice with the options reversed, and one verdict word:
  «ثبت» ("held": the same level both times) or «تغيّر بتغيير الترتيب» ("changed with the order").
- **One line under Laya's column heading says what the check means:** «نسأل لايا مرتين، والخيارات بترتيبين
  متعاكسين. إذا تغيّر اختياره بتغيير الترتيب وحده، فذلك الاختيار لا يأتي من حالة المحرك.» ("We ask Laya twice,
  with the options in opposite orders. If its choice changes when only the order changes, that choice does not
  come from the engine state.") Nothing is averaged, scored or counted across presses.
- `sent` shows both request bodies. The response carries `answers` (design order) and `answers_reversed`.
- **jev is asked once, in the design's order only** (each jev call is paid). Whether jev shows the same order
  effect is unknown; the page says nothing about it either way.
- Test additions: row 18 (fake worker) returns order-dependent answers in one mode and order-independent ones
  in another; the route reports "changed" and "held" respectively. Row 20 (real Laya, `--full`) records the
  held/changed pattern for one real trace in the test output, as an observation, never an assertion.

### 7.6 Routes [changed from §7: two models]

```
GET  /api/agents/jev/status     -> {configured, source, vendor: "typesafe.ai", model: "jev-latest", hosted: "USA"}   (as §7)
POST /api/agents/jev            body {"trace": "runs_c4/5/1", "step": 312}
GET  /api/agents/laya/status    -> {configured, source, problem, worker: stopped|starting|ready|failed,
                                    device, laya}                          [new]; never spawns, never loads
POST /api/agents/laya           the same body                              [new]
```

**Injection.** `install(app, store=None, jev_send=None, laya=None)`:

- `jev_send` defaults to `jev._send`.
- `laya` defaults to a `LayaBridge()` built in `install()`. Building it reads no file and starts nothing.

Tests pass a fake send and a bridge with a fake worker. Neither default is used under test.

**Laya's ask is a POST too.** It sends nothing abroad and costs nothing, but it shares the properties that made jev a POST:

- The first press starts a process that holds about 1.7 GB of GPU memory. A GET could fire that on prefetch, on reload or from history.
- A GET query string cannot refuse extra parameters.
- A JSON POST from another site needs a preflight, which this server never grants.

Being a POST also lets both routes share one body model, one guard and one test.

**Body (both routes)** **[C7]**:

```python
TRACE_KEY = (rf"^{agent_catalog.RUNS_NAME.pattern.strip('^$')}"
             rf"/(?:{SEED_TEXT.pattern})/(?:{EP_TEXT.pattern})$")
# = ^runs[a-z0-9_]*/(?:[0-9]{1,3})/(?:[0-9]{1,2})$

class AskBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    trace: str = Field(pattern=TRACE_KEY)
    step: int = Field(ge=0, le=agent_trace.STEPS - 1)
```

Pydantic's `pattern` is an unanchored search, so `TRACE_KEY` carries its own `^…$`. Each of the following gets 422:

- an extra field;
- a form or `text/plain` body;
- a string `"312"`, `true` or `719` as the step;
- a trace with junk before or after it;
- a 3-digit episode;
- `runs_C4/5/1`;
- `../runs_c4/5/1`.

Measured in scratch: `xx/runs_c4/5/1/zz`, `runs_c4/5/123`, `runs_C4/5/1`, `../runs_c4/5/1` and a trailing newline all get 422; `runs_c4/5/1` and `runs_c4/05/1` pass.

**Guards, in order:**

1. **Origin [C8].** Origin must be present and equal `http://` + `Host`, and `Host` must match `^(127\.0\.0\.1|localhost):\d{1,5}$`. Otherwise: 403 `foreign_origin`.
2. **Trace [C6].** The body's trace is split on `/` into `(runs, int(seed), int(ep))`, the store's own key form (`agent_api.py:205`, `key_str` at `:106-109`), so `runs_c4/05/1` names `('runs_c4', 5, 1)`. Then:
   - `store.trace(key)` is `None` → 409 `no_trace`;
   - `step >= len(trace.obs[0])` → 409 `step_not_computed`.
3. **Lock [C5].** Each model has a non-blocking lock; if it is held, 409 `busy`. jev's lock and Laya's lock never meet.

Both routes are sync `def` handlers, so FastAPI runs them in its thread pool. A 10 s jev call or a 90 s Laya start never blocks the episode polls.

**Responses:**

- **200:** `{model, runs_on, device (Laya), ms, started_s (Laya, only on the press that started the worker), trace, step, answers: to_action(...), sent}`.
  - `sent` is jev's exact body without the key, or Laya's request line without its `id`.
- **Error:** `{model, code}`, plus `status` (an integer) for `vendor_status` only, sent with `Cache-Control: no-store`.
  - The server also writes one stderr line with `print(f"{model}: {code} (step {step})", file=sys.stderr)`. It carries no state and no key.

**Docstrings [C11].**

- `server.py:43` ("Every HTTP route below is a GET.") becomes: "Every route this module defines is a GET. Two POST routes, /api/agents/jev and /api/agents/laya, are added by app.agent_api.install() only under --simulation. Each asks a language model about one simulated second: /api/agents/jev sends it to an external service in the USA; /api/agents/laya sends it to a process on this machine, and nothing leaves the machine. Neither has a path to the vehicle."
- These are amended to match:
  - `agent_api.py:1-2` ("the three routes");
  - the route comment at `:236-241` ("Every route here is a GET");
  - `install()`'s docstring (`:342`).
- The `--simulation` banner (`server.py:299-301`) is **not** changed: the panel is hidden, and nothing is sent or started until a press.

### 7.7 The gesture and the panel

**Gesture.** As §7:

- `tap-unlock.mjs`: 10 taps within 4000 ms on `#footer-index` (`agents.html:111`). The lab's `01 — REPLAY` gets no handler.
- The unlock lives in a module variable, **so a reload forgets it**.
- The gesture hides the panel; it protects nothing.
- Unlocking removes `hidden` from `#models-panel` **[C2]**, then calls **both** status routes independently. A failed status fills only its own column.

**Panel structure.**

- A heading: «اسأل نموذجاً لغوياً عن هذه الثانية» ("ask a language model about this second").
- Under it, the shared honesty lines, always visible:
  - «ليس جزءاً من الرسالة ولا من أي نتيجة. لا يقارن أي رقم هنا النموذجين بالوكيلين، ولا يُحسب أي فرق.» ("Not part of the thesis or of any result. No figure here compares the models with the agents, and no difference is computed.")
  - «الاحتمالات ادعاء النموذج نفسه، ولم تُختبر على هذه المهمة.» ("The probabilities are the model's own claim, untested on this task.")
  - The discretisation rule: «كل نموذج يختار واحداً من خمسة مستويات لكل إجراء: للتعديلات الثلاثة الحدّان و"بلا تعديل" ونقطتان في المنتصف؛ وللمروحة والمضخة خمس قيم متساوية التباعد. المعروض هو اختيار النموذج نفسه، ولا يُحسب منه متوسط.» ("Each model picks one of five levels per action: for the three trims, both limits, 'no change' and two midpoints; for the fan and pump, five evenly spaced duties. What is shown is the model's own choice; no average is computed from it.")

**Two columns, one per model, in this order.** They use an `.action-values`-style grid and collapse to one column below 760 px.

| | jev | Laya |
|---|---|---|
| name (ltr) | `typesafe.ai · {model returned}` | `Laya · {model returned} · laya {version}` |
| where it runs | «خدمة خارجية في الولايات المتحدة · كل ضغطة استدعاء مدفوع واحد» ("external service in the USA · each press is one paid call") | «على هذا الجهاز ({device}) · مجاني، بلا مفتاح» ("on this machine ({device}) · free, no key") |
| its own text | §7's vendor paragraph, unchanged: US service; telemetry kept in perpetuity (MCA §4.1, `legal_mca.txt:37`); no imitation training; whether use from Saudi Arabia is permitted is unknown. Plus the vendor's warning on numeric precision (`model-jaggedness_jev-1.13.md:13`) | «يعمل على هذا الجهاز ولا يُرسل شيئاً خارجه. تجربة تشغيل، لا تقييم. يقول ملف لايا نفسه إن نتيجة مثال لا تعني أنه مناسب للتحكم بالمحرك (README_AR.md:31). رخصة Apache 2.0.» ("Runs on this machine and sends nothing out of it. A trial run, not an evaluation. Laya's own file says an example result does not mean it suits engine control. Apache 2.0.") |
| status | from its status route: key configured, or «لا مفتاح؛ لن يُرسل شيء» ("no key; nothing will be sent") | one of:<br>• «غير مُعَدّ: LAYA_HOME» ("not configured")<br>• «يُحمَّل عند أول سؤال» ("loads on the first question")<br>• «يُحمَّل على هذا الجهاز لأول مرة…» ("loading on this machine for the first time…")<br>• «محمَّل على {device} حتى يُغلق الخادم» ("loaded on {device} until the server stops")<br>• the failure code |
| button | «اسأل jev عن هذه الثانية (استدعاء مدفوع واحد)» ("ask jev about this second (one paid call)") | «اسأل لايا عن هذه الثانية (على هذا الجهاز)» ("ask Laya about this second (on this machine)") |
| latency | «{ms} ms، مقيسة من هذا الجهاز (ادعاء المورّد 70–500 ms)» ("measured from this machine (vendor claim 70–500 ms)") | «{ms} ms على {device}»; on the press that started the worker, also «التحميل الأول {s} ث» ("first load {s} s") |
| error | «لا جواب — {code}» ("no answer") with its sentence (§7.9); **nothing is substituted** | the same |
| footer | «هدف لثانية واحدة: لم يُطبَّق ولم يُقيَّد بحد سرعة التغيير» ("a one-second target: not applied, not rate-limited") · «ما الذي أُرسل» ("what was sent": `sent`, collapsed) | the same |

**Rows**, in `ACTIONS` order, with the pause panel's own labels and units:

- A reference line from the same frame: «طبّق الوكيلان في هذه الثانية: المُبصر {x} · الأعمى {y}» ("the agents applied in this second: sighted {x} · blind {y}"). Nothing is subtracted.
- Per model column:
  - the chosen level, in physical and network units;
  - five bars labelled with the physical levels, with the chosen one marked;
  - «احتمال الخيار المختار {p}» ("probability of the chosen option") **[C9]**.

Model levels are **never** drawn as dots on the agents' gauges, because that would read as applied or compared.

**When a button is enabled** (`model-panel.mjs askState`, per model, independently) **[C10]**. All four must hold:

- **Playback is stopped: the play button shows play.** This is `!clock.playing && !isWaiting()`, the predicate `syncPlayButton` uses (`agents.mjs:756`).
  - It counts a stop at the end of the episode, where `userPaused` stays false (`agent-view.mjs:185`, `playback.mjs:7`), so the last second can be asked about.
  - It also counts a finished episode that was never played (second 0).
- The build is finished: `state.done`.
- Frame k exists, and the sighted lane has not stopped at or before k.
- That model has no request in flight.

A disabled button shows its reason:

- «أوقف العرض أولاً» ("pause first");
- «انتظر حتى تكتمل الحلقة» ("wait for the episode to finish");
- «توقفت محاكاة المُبصر قبل هذه الثانية» ("the sighted car's simulation stopped before this second").

**When the panel re-renders.** `renderModels()` is called from five places:

- `renderPanel` (`agents.mjs:1014-1027`), which runs only when k changes (`:1012`, `:1048`);
- the play and restart click handlers (`agents.mjs:1115-1128`);
- the loop's play-state branch (`agents.mjs:1110`). The click handlers never update `state.wasPlaying` (it is written only at `:1110`), so this branch fires on **every** change of the play state, including the natural end of the episode;
- the arrival of an answer;
- `renderAll` (`agents.mjs:1054-1069`), which covers language switches and the end of a build: `handle()` calls it when `state.done` becomes true (`agents.mjs:294-297`).

**Which answer is shown.**

- Each model keeps its answers **per second of the episode on screen**. `createAnswers()` holds a map from `(key, k)` to an answer, with at most one entry per second (so at most 719 per model), in memory only.
- The column shows the answer for the paused `(key, k)` if one exists. Otherwise it shows the button, and «اسأل عن هذه الثانية» ("ask about this second").
- Pausing back at a second already asked shows its answer again, with no new call.
- Pressing the button again at that second asks again, and the new answer replaces the stored one.
- Nothing is ever asked on its own.
- `compute()` and `clearEpisode()` (`agents.mjs:186-208`, `:445-474`) empty both maps.
- A response is dropped if `state.loadToken` moved while it was in flight, the same guard `poll()` uses.
- **The true rule for jev's paid answers:** an answer is kept only while its episode is on screen. It is discarded if the episode changes while the call is in flight or at any time after it arrives, and on reload. Nothing is saved.

### 7.8 Discoverability of the pause panel [new; DECIDED by Jad, 28 Sep: the recommended option 1]

Jad did not find the pause panel (walkthrough, 28 Sep). Measured at 1440 × 900:

- it starts at y = 1857, 957 px below the fold;
- it sits under a verdict box whose quotes open by themselves on desktop (`agents.mjs:315-316`);
- before «احسب», its only content is "—" (`agents.mjs:1017`).

The models panel follows the pause panel, so the same problem would hide both.

**Recommended (small):**

1. Move the `<section class="pause-panel">` from the side column into `.agents-col-main`, directly after the transport (`agents.html:67`).
   - Below 1100 px, give it `order:5`. The profile becomes 6 and the models panel 7 (`agents.css:135`).
   - The panel's top would move from y 1857 to about 873 at 1440 × 900, from 1754 to about 948 at 1920 × 1080, and from about 2027 to about 1798 on a phone. These are estimates from the measured boxes, not measurements taken after a move.
   - It also gives the model columns about 755 px instead of 458.
2. Replace the "—" empty state with one bilingual line: «اضغط احسب، ثم أوقف العرض عند أي ثانية لترى ما قرّره كل وكيل» ("press احسب, then pause at any second to see what each agent decided").

Both change what the committee sees, and neither moves an honesty surface.

**The one-line alternative** is to stop auto-opening the verdict quotes on desktop. The panel would rise about 800 px, but the verbatim quotes would sit behind a click, which touches a verdict surface.

**Decided (Jad, 28 Sep):** recommended option 1 — the move and the empty-state line are built (§10 step 7).

### 7.9 Errors

Each error returns a fixed code, and the page maps the code to a sentence in both languages. **Nothing is ever substituted**, and neither `str(exc)` nor a vendor body is ever forwarded. A code belongs to one model's column and never touches the other.

| code | model | when | HTTP |
|---|---|---|---|
| `no_key` | jev | no key; nothing sent | 503 |
| `network` / `timeout` | jev | `URLError`, or 10 s without a reply | 502 |
| `key_rejected` / `vendor_refused` / `request_rejected` / `rate_limited` / `overloaded` | jev | vendor 401 / 403 / 422 / 429 / 529 (as §7) | 502 |
| `vendor_status` **[new; C14]** | jev | any other non-2xx vendor reply. The body carries `status` (the integer only; the vendor's body is dropped). Sentence: «رفضت الخدمة الطلب (HTTP {status}). قد يعني ذلك أن الحساب بلا رصيد.» ("The service refused the request (HTTP {status}). This may mean the account has no credit.") | 502 |
| `not_configured` **[new]** | Laya | no `LAYA_HOME`; nothing started | 503 |
| `not_found` **[new]** | Laya | the python or the model folder is missing, or resolves under the repository | 503 |
| `start_failed` **[new]** | Laya | the worker exited or sent a bad ready line. One way this happens: the `.venv`'s `pyvenv.cfg` still points at an interpreter that has moved | 502 |
| `start_timeout` / `timeout` **[new]** | Laya | 90 s without the ready line / 20 s without an answer; the worker is killed | 502 |
| `worker_error` **[new]** | Laya | the worker replied `ok: false`. Its kind is shown only if it is in a fixed list (`ValueError`, `RuntimeError`, `OutOfMemoryError`); otherwise it shows as `other` | 502 |
| `worker_died` **[new]** | Laya | EOF in the middle of a request | 502 |
| `network_attempt` **[new]** | Laya | the guard counted an attempt; the answer is dropped | 502 |
| `bad_answer` | both | `to_action` refused the answer; for Laya, also an `id` mismatch | 502 |
| `foreign_origin`; bad body | both | the guards in §7.6 | 403; 422 |
| `no_trace` **[C6]** / `step_not_computed` / `busy` | both | §7.6 | 409 |

**On the page [new]:**

- A response whose `code` is not in `ERROR_CODES` shows «لا جواب — خطأ في الخادم (HTTP {status})» ("no answer: server error"). Examples: FastAPI's default 500, or a 422 body of `{"detail": …}`.
- A fetch that fails shows the page's existing server-down sentence (`agents.load.server_down`).
- Both stay in their own model's column.

### 7.10 Deferred, not blocked (as §7, now for both models)

A model driving a whole episode stays unbuilt. The later shape would be:

- `to_action(ask(...))["net"]`, wrapped as `policy(env, obs)`, as a third lane in `run_lanes`;
- a model error would abort that build and never fall back to neutral.

For Laya this would be cheap: it is deterministic and answers in about 34 ms warm, so about 25 s for 719 steps. For jev it would be 719 paid calls. Nothing is built for either.

### 7.11 Questions for Jad

1. **Discoverability (§7.8).** Three options:
   - move the pause panel under the play button, with the one-line empty state (recommended);
   - stop auto-opening the quotes instead;
   - neither.
2. ~~Should the page say what the spike saw?~~ **Resolved by Jad's Q3 choice (28 Sep):** the page runs the
   order check on every press (§7.5b) instead of printing a static warning.

---

## 9. Testing: M3 rows (replace rows 14–17; amend 10, 11, 12, 13)

**Ground rules (added).**

- No test touches the network.
- jev's tests inject a fake `send` through `install(..., jev_send=fake)`.
- Laya's tests use a **fake worker**, injected through `install(..., laya=LayaBridge(command=[sys.executable, "-I", "-c", FAKE_WORKER, mode]))`.
  - The fake's source is a string inside `test_agents.py`. It speaks the same protocol and needs no file, so test 11's snapshot of `app/` stays valid.
- Only row 20 runs the real Laya. It runs under `--full`, and it is skipped loudly without `LAYA_HOME`.
- A sentinel key never appears in:
  - any response body;
  - any root-logger line at DEBUG;
  - the captured stderr;
  - the fake worker's reported environment.

| # | test | what it pins |
|---|---|---|
| 10 (amend) | `routes_only_under_simulation` | The exact set of added routes grows from three (`test_agents.py:1363`) to seven. `/api/agents/jev` and `/api/agents/laya` are `{"POST"}`; every other added route is `{"GET"}`. The module-level GET/HEAD assertion (`:1344`) is unchanged. |
| 11 (amend) | `no_writes` | `NEW_MODULES` (`:1640`) adds `model_questions.py`, `jev.py`, `laya_bridge.py` and `laya_worker.py`. The dynamic snapshot is unchanged. M2's known limit stands: another session writing to the tree makes it raise. |
| 12 (amend) | `page_assets_ids` | `tap-unlock.mjs` and `model-panel.mjs` resolve; every id `agents.mjs` reads for the panel is static in `agents.html`; `#models-panel` carries `hidden`. |
| 13 (amend) | `no_network_outside_jev` | `NET_ALLOWED` (`:1682`) becomes `{"jev.py": NET_ROOTS, "laya_worker.py": {"socket"}}`.<br>• The loop at `:1690-1691` no longer skips allowed files. It reports every root not in `NET_ALLOWED.get(path.name, set())`.<br>• A probe asserts that an `import urllib` in `laya_worker.py` would be reported.<br>• `laya_bridge.py` imports none of `NET_ROOTS`. |
| 14 | `question_levels` | §7's row 14, on `model_questions`. `chosen_p == probabilities[choice]`; `confidence` is not kept. |
| 15 | `question_state` | §7's row 15, on `model_questions`.<br>• **Fairness:** for one `(trace, step)`, `jev.build_request(...)["state"]` is `==` the Laya request's state, and both `questions` are `QUESTIONS`.<br>• `build_state` rejects a non-`Trace`.<br>• AST: none of `model_questions`, `jev`, `laya_bridge` or `laya_worker` imports `app.replay`, `app.reader` or `app.estimator`.<br>• `user_setting` refuses a *file* inside the repository and prefers the environment variable. |
| 16 | `ask_routes` | Run for **both** routes.<br>• **Body, each case gives 422:** an extra field; a form body; `text/plain`; `"312"`; `true`; `719`; `xx/runs_c4/5/1`; `runs_c4/5/1/zz`; `runs_c4/5/123`; `runs_C4/5/1`; `../runs_c4/5/1`.<br>• `runs_c4/05/1` resolves to the store key `('runs_c4', 5, 1)` or gives `no_trace`, never 500.<br>• **Origin, each case gives 403:** missing; foreign; rebinding (Host `evil.test:8000` with a matching Origin).<br>• **Resolution:** a store with no trace gives `no_trace`; a step at `len(obs[0])` gives `step_not_computed`; GET gives 405.<br>• **Independence:**<br>  – with jev's lock held, Laya answers 200 and jev 409, and the reverse;<br>  – a jev fake raising `URLError` leaves Laya's next answer 200;<br>  – **a jev fake returning 402 gives `vendor_status` with `status: 402`, and Laya's next answer is 200**;<br>  – `no_key` never reaches the Laya bridge.<br>• The `server.py` docstring names both POSTs. |
| 17 | `jev_errors` / `jev_key` | §7's row 17, extended.<br>• Every vendor status and malformed answer gives its code.<br>• **402, 500 and 503 give `vendor_status` carrying only the integer. The fake's body text appears in no response or log line.**<br>• The sentinel key is in no response or log line.<br>• A `typesafe_key` file whose path resolves inside the repository is refused.<br>• **An env key `"sentinel-key"` is accepted with the working directory set to the repository root.**<br>• `git check-ignore` matches `.env` and `*typesafe_key*`. |
| 18 **[new]** | `laya_bridge` (fake worker) | • Constructing `LayaBridge()` reads no file and spawns nothing.<br>• `status()` never spawns (the fake counts spawns).<br>• Not configured gives `not_configured` with zero spawns; a `LAYA_HOME` under the repository gives `not_found`.<br>• The first ask spawns and the second reuses the worker (one spawn).<br>• A start timeout and an answer timeout both kill the process (`returncode` set), and the next ask spawns again.<br>• A worker reply `ok: false` with an unknown kind gives `worker_error`/`other`.<br>• EOF mid-request gives `worker_died`; an id mismatch gives `bad_answer`; `net_attempts: 1` gives `network_attempt`.<br>• `close()` ends the process within 5 s.<br>• The fake reports its environment: no sentinel key, and `HF_HUB_OFFLINE=1`. |
| 19 **[new]** | `laya_worker_static` | AST:<br>• the eight socket replacements (§7.5 step 1) come before any `torch` or `laya` import, and `socket` appears only in those eight assignments;<br>• the worker has no `app.*` import;<br>• `sys.stdout` is rebound before `import laya`.<br>**Across every `app/*.py` except the test files,** every `print` call with a `file=` keyword targets `sys.stderr`, except exactly two: the worker's protocol stream and the bridge's `proc.stdin`.<br>The lab's `test_read_only` passes unchanged. |
| 20 **[new, `--full`]** | `laya_real` | Skipped loudly without `LAYA_HOME`. With the real worker:<br>• the ready line and the device;<br>• one ask on a real finished `Trace` passes `to_action`;<br>• two identical asks give identical answers;<br>• `net_attempts == 0`;<br>• `usage.input_tokens <= 5 × 800` (505–541 per row today, cap 1024; `task` would be cut first);<br>• a `(path, size, mtime_ns)` snapshot of `LAYA_HOME` is identical before and after;<br>• the process is gone after `close()`. |

**Node tests (added).**

- `tap-unlock.test.mjs`, as §9:
  - 10 taps in 4000 ms unlock;
  - 9 taps do not;
  - 10 taps over 4001 ms do not;
  - the source uses no storage API.
- `model-panel.test.mjs`:
  - the `askState` truth table, each condition alone: playing, waiting, not done, lane stopped, in flight;
  - **stopped at the natural end (`playing` false, `waiting` false, `userPaused` false) is enabled**;
  - one model in flight leaves the other enabled;
  - **answers:**
    - an answer at k1 survives an answer at k2;
    - `get` returns only its own `(key, k)`;
    - a second answer at the same k replaces the first;
    - `clear()` empties the map;
  - every `ERROR_CODES` entry has a sentence in both languages;
  - `errorText('vendor_status', 402)` names 402 and credit;
  - an unknown code gives the server-error sentence with its status.
- **The agents-page harness** (`agents-page-run.test.mjs`): on a finished episode, clicking play and then pause at the same k enables the ask button without any seek. The natural end is pinned in `model-panel.test.mjs` instead, because the harness stubs `requestAnimationFrame` (`agents-page-harness.mjs:99`) and so never runs the loop.
- `agents-strings.test.mjs`: the new keys exist in both languages, and the «المنمذَج» and no-"preview helps" rules cover them.

---

## 10. M3: the two models at the paused moment (replaces §10 M3)

**Before building:** nothing waits. Q1 was answered (option 1, so step 7 is built) and Q2 was resolved by the order check (§7.5b).

**Commits, in order:**

1. The `.gitignore` patterns alone (`.env`, `.env.*`, `*typesafe_key*`), before any key exists. As §2 edit 5.
2. `model_questions.py`, with tests 14 and 15.
3. `jev.py` on top of it, with test 17 (fake send).
4. `laya_worker.py` and `laya_bridge.py`, with tests 18 and 19.
   - **First, one measurement:** time from spawn to ready with `-I -B -X utf8` on this machine, in a scratch folder, compared with the spike's 6.2 s.
   - If `-I` breaks Laya's `.venv`, drop `-I`, keep `-B` and `cwd=LAYA_HOME`, and say so in the commit.
5. The four routes, and `install(app, store=None, jev_send=None, laya=None)`. In the same commit: the `server.py:43` sentence and the `agent_api.py` docstrings, with tests 10, 13 and 16 amended.
6. The frontend: `tap-unlock.mjs`, `model-panel.mjs`, the strings, `#models-panel`, the CSS lines and the wiring (including the five `renderModels()` hooks in §7.7). With the node tests, the harness case and test 12.
7. The pause-panel move and the empty-state line (Jad agreed in Q1).

**Verify:**

- **Suites:**
  - `python -m app.test_agents` and `--full`, with `LAYA_HOME` set so test 20 runs;
  - `python -m app.test_replay` and `--full`;
  - `python -m app.test_simulation`;
  - `node --test "app/static/sim/*.test.mjs"`;
  - `python verify_docs.py` after `git add`.

  Counts are read from each run, never from this file.
- **Browser, at 1440 px and 390 px, with the server started by the system interpreter** (M2 final review):
  - **locked**, the page is identical to M2, apart from the Q1 change if Jad chose it;
  - ten taps show both columns and both statuses; a reload hides them;
  - **letting an episode play to its end enables both buttons at the last second, with no seek.**
- **Laya:**
  - the first «اسأل لايا» shows the loading line, then five choices with the device, the latency and the first-load time;
  - a second press at another second answers in tens of milliseconds;
  - pausing back at the first second shows its answer with no new request.
- **Jad's scenario:**
  - with no key, jev's column shows «لا جواب — no_key», nothing is sent, and Laya answers normally;
  - with jev forced to fail (the key variable set to a dummy value, network off), the failure shows in jev's column only;
  - the no-credit reply cannot be produced on demand, because its status is undocumented. Tests 16 and 17 cover it with a fake 402.
- **Shutdown:** stopping the server leaves no `python.exe` from Laya's `.venv`, checked with `Get-Process`, both after Ctrl+C and after closing the window.
- **Laya's folder:** `LAYA_HOME` has no new or changed file.
- **jev, one real call (optional):**
  - Jad makes one real call, only if his jev account has credit, with the key in his environment variable.
  - The page then shows the model name, the measured latency, five choices with probabilities, the telemetry sentence and the request body.
  - If the call returns `vendor_status`, the status number shown is the fact to note. A named code for it is added only in a later commit, with that observation beside it.
  - The call is not a test and is not recorded. M3 is verified whether or not it happens, because Laya's half does not depend on it.

---

## Consequential amendments elsewhere in this file

- **§1, line 28:** "…sends that same paused moment to jev once…" becomes "…lets Jad ask two language models about that same paused moment, jev (an external service) and Laya (on this machine), one button each, and shows each model's choice next to the agents' actions."
- **§1, the non-goal "jev does not drive an episode":** becomes "Neither model drives an episode."
- **§2:**
  - the `app/jev.py` row is replaced by the four rows of §7.2;
  - `sim/model-panel.mjs` and `model-panel.test.mjs` are added to the frontend table;
  - edit 1's M3 clause names the two POSTs (§7.6).
- **§3.4:** the route list gains `GET /api/agents/laya/status` and `POST /api/agents/laya`. `install()`'s signature becomes `install(app, store=None, jev_send=None, laya=None)`.
- **§6, layout:** "side column: … pause panel, then jev once unlocked" becomes "…pause panel, then the models panel once unlocked (§7.8 may move both to the main column)".
- **§6, misreading table:**
  - The row "jev is part of the thesis" becomes "jev or Laya is part of the thesis". Answer: hidden by default; the shared honesty lines; no comparison; never applied.
  - New row, "Laya's answer is an engine judgement". Answer: «تجربة تشغيل، لا تقييم»; the README line; Q2's line, if approved.
  - New row, "Laya sent data out". Answer: the where-it-runs line; the offline variables, the absolute-path check and the guard together (§7.5); tests 18–20.
  - New row, "the models were told nothing about the agents". Answer: §7.3 — the state already carries the sighted agent's earlier trims in its spark and lambda.
- **§8:** the row "jev | §7" becomes "jev, Laya | §7.9".

---

## Appendix: Review issues not taken

None. The evidence for all ten issues held when checked against the code. Five of them were taken with a change, one line each:

- **Issue 1 (render hooks):** the proposed hook in `handle()` was not added, because `handle()` already calls `renderAll` when the build finishes (`agents.mjs:294-297`) and the buttons need a finished build. The harness case covers the pause click only, since the harness stubs `requestAnimationFrame` (`agents-page-harness.mjs:99`); the natural end is pinned in `model-panel.test.mjs`.
- **Issue 3 (answer retention):** fix (a) was taken without the proposed bound of 20. One entry per second already caps each map at 719, and both maps empty on `compute()`/`clearEpisode()`.
- **Issue 6 (network guard):** all four extra entry points were wrapped, and the evidence was reworded as proposed. The page's line «لا يُرسل شيئاً خارجه» ("sends nothing out of it") stays, as the joint claim of the three measures. §7.5 adds that native libraries opening their own connections are not seen by the guard.
- **Issue 7 (actions in the state):** taken, with the review's citation corrected. Observation entries 3 and 4 are `engine_env.py:653-654`, not `:654-655`. Manifest pressure and throttle were added as indirect effects of the boost setting.
- **Issue 10 (print scan):** "exactly twice" was narrowed to prints whose `file=` is not `sys.stderr`. §7.6's own stderr line is a `print(file=sys.stderr)`. Today no non-test `app/*.py` has any `file=` print, so the rule can be enforced from the first commit.
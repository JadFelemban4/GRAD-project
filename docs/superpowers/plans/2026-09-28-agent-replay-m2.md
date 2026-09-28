# Agent Replay, Milestone 2 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Milestone M2 of the approved agent-replay design (docs/superpowers/specs/2026-09-26-agent-replay-design.md, section 10 'M2: every experiment', with sections 4, 5 and 6), built on the M1 code as committed on JMF-2340550-sep17 (3e66189..44582b2; the code wins over the M1 plan). /agents becomes usable from its own nav link and from the replay lab, fixing both gaps Jad found on 28 Sep. The page opens with NOTHING selected, loads GET /api/agents/catalog (every runs*/ directory, every pair with its status, reason and quoted results-table row, and the 20 frozen episodes of each protocol) and offers a working three-select picker (experiment -> pair -> episode) whose selection is mirrored into the address, so a chosen episode can be shared or reloaded; nothing computes until «احسب». Phase D and Phase D2 pairs run as well as C4, each beside its preregistered verdict quoted as WHOLE items, a short line that keeps its qualifiers, glosses, and the found / missing / none states. Phase D's blind car is labelled as possibly memorising its one road, in the scene, the picker, the verdict box and the pause panel. Refused pairs (runs_sixspeed_18sep: no meta.json) are listed greyed with their reason. The replay lab gets exactly one nav link to /agents, after its first link, so phones keep it. Nothing jev (M3).

**Architecture:**

No new Python module; M2 extends M1's three. (1) app/agent_catalog.py (py-trace): VERDICT_LINES / CELLS / SHORT_VERDICT / GLOSS gain the 'd2' and 'phase_d' rows (anchors quoting whole items; MISSING_TEXT names every missing file); read_agent refuses a directory that is not there (KeyError) and calls an unreadable final.zip 'incomplete'; check_pair(runs, seed, root) runs find_pair's checks in find_pair's order but RETURNS the problems (find_pair becomes check_pair plus raise Refused), so the catalog and the episode route share one rule; table_rows(prefix) quotes analyse_phase_d2.load rounded as the tables print; discover(root) lists every root/runs*/ directory matching RUNS_NAME, every seed (a half pair is listed with a 'missing' arm), the verdict, the protocol and each pair's table row. app/agent_trace.py gains episode_row(ep, road), the picker's row for one frozen episode read from the road the env steps (Phase D: 180 s, 0.12). (2) app/agent_api.py (py-serve): page_constants() (preview_s, act, limits, shared by episode_meta and the catalog), catalog_episodes(), catalog(root, sb3) and GET /api/agents/catalog inside install() (so only under --simulation); episode_meta takes the episode from episode_row, so Phase D's badge reads 12.0 instead of a dash; both routes turn any unexpected exception into a fixed-text 500 with Cache-Control: no-store; EpisodeStore.poll lets a preempt cancel another key's build even when it is answered from the cache or with an error (M1 F6), and a superseded build's failure is never reported. (3) Browser (fe-pure): a new pure module app/static/sim/agent-picker.mjs (lenient address parsing, resolveSelection against the catalog, choose(), selectionSearch(), computeState(), option lists and labels for the three selects, formatDiff in a left-to-right isolate, blindLabelKey, notBlindCite) node-tested against app/static/sim/agent-catalog.fixture.json, which is GENERATED from the live catalog and whose shape a Python test pins to the server's; agents-strings.mjs gains the M2 strings in both languages. (4) Page (fe-page): agents.mjs fetches the catalog at boot, fills the selects through agent-picker.mjs, selects only what the address names and the catalog allows (from the nav link: nothing), keeps the address in sync with history.replaceState, clears the displayed episode and drops late frames (loadToken) on every change, renders the verdict box from the selected experiment, names Phase D's blind car and its caveat everywhere, and says 'stopping the previous computation' when its own preempt is answered busy; a shared fake-DOM harness module lets one node test process boot the page from the nav link and another from a full address. simulation.html gets one link after its first nav link; the lab launcher prints the /agents URL and warns when its python has no stable-baselines3. Data flow: page boot -> GET /api/agents/catalog -> three selects (nothing chosen) -> the viewer chooses -> address replaced -> «احسب» -> GET /api/agents/episode?runs&seed&ep&since=0&preempt=1 (M1's route and store, unchanged in shape) -> meta + road + frames, then polls with since=frames.length every 400 ms.

**Tech Stack:** Python 3.12 system interpreter (PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe; a .venv is blocked by App Control and bare python in the repo shell resolves to it), numpy, and by import only: engine_env, evaluate, random_road, fingerprint, run_phase_d, analyse_phase_d2, analyse_c4. stable-baselines3 SAC + torch imported lazily in the worker (measured 28 Sep: SB3 2.9.0, torch 2.11.0+cu128, device cuda). FastAPI + uvicorn (existing app/server.py), fastapi.testclient, stdlib unittest in app/test_agents.py (python -m app.test_agents [--full]; baseline measured 28 Sep: 'Ran 38 tests', 'OK (skipped=1)', '== proof PROVEN: device cuda ... built in 65 s'). Browser ES modules under app/static/sim reusing the lab's i18n.mjs (t, STRINGS, resolveLang, applyTranslations) and playback.mjs (PlaybackClock, formatTime); node:test on Node 24.18 (node --test 'app/static/sim/*.test.mjs', glob quoted; baseline 75 of 75); Three.js 0.180.0 vendored at app/static/vendor/three (gitignored); Chrome driven over the DevTools protocol by a scratchpad script (as in M1 Task 11) for the browser check. verify_docs.py baseline: 'All 67 checks pass (782 figure mentions scanned in the documents).' All counts above are to be re-read from runs, never quoted from here.

**Spec:** `docs/superpowers/specs/2026-09-26-agent-replay-design.md` (APPROVED; its walkthrough log, including Jad's 28 September findings and his choice of the whole of M2, and its 'Build record for M1'). Measurements: `docs/superpowers/specs/2026-09-26-agent-replay-recon.md`. **M1 is built** (3e66189..44582b2); where the M1 plan and the code differ, the code wins. Executors read the spec and this plan.

**How this plan was written.** A plan workflow on 28 September 2026: one skeleton with every interface, read against M1's committed code; four authors (catalog, serving, pure picker logic, page) who prototyped and ran their code in scratch copies; one critic that checked cross-task consistency and spec coverage against the real code; one revision of the page group. Milestone M3 (jev, the paused moment) gets its own plan after M2 works.

## Global Constraints

- READ-ONLY for the vehicle and the experiments: never write to the ECU; no training, no evaluation, no writes into runs*/, results/ or anywhere on disk. runs/, runs_d2/ and runs_c4/ are CLOSED: read meta.json and final.zip only. Traces live in memory only (one in-flight trace plus keep = 2 finished).
- Never edit plant.py, thermal.py, engine_env.py, random_road.py, fingerprint.py, train.py, evaluate.py, run_phase_d.py, analyse_phase_d2.py, analyse_c4.py or anything in results/; import only. app/server.py is not edited in M2 (the catalog route is added inside agent_api.install).
- Routes exist only through app.agent_api.install(app), called inside `if a.simulation:` in app/server.py main(): GET /agents, GET /api/agents/catalog, GET /api/agents/episode. Every one is a GET and every response carries Cache-Control: no-store. Request names are matched before any lookup: runs ^runs[a-z0-9_]*$ (lowercase only, agent_catalog.RUNS_NAME), seed [0-9]{1,3}, ep [0-9]{1,2} with 1 <= ep <= 20, since [0-9]{1,4}; no path is ever resolved from a request. 404 unknown; 409 {status: 'refused', problems}; 503 stable-baselines3 missing; M2 adds 500 {detail: '<fixed text>: <ExceptionClassName>'} for anything unexpected, never str(exc).
- Agent status is decided in design section 4's order, unchanged from M1: 1 FP.running_pid alive -> 'training'; 2 FP.read(meta.json) is None -> 'incompatible', reason 'no meta.json: plant unknown (AUDIT2 C2-1)'; 3 no final.zip -> 'incomplete'; 4 evaluate's own rule `'blind' in f'{runs}/{name}'` disagreeing with the child name's arm or with `not meta['use_preview']` -> 'incompatible', reason 'evaluate.py would have scored this agent as the other arm'; 5 meta.scenario protocol 'random-climb' -> 'd2', no key -> 'phase-d', anything else -> 'incompatible', reason 'unknown protocol'; 6 FP.compare(meta, live_fingerprint(protocol)) non-empty -> 'incompatible' naming each field with stored and live values; 7 'ready' with budget_line = FP.format_budget(FP.model_budget(final.zip)) and train_dt from meta. M2 adds only: a directory that does not exist is a KeyError, and at step 7 an unreadable final.zip (model_budget None) is 'incomplete' with reason 'final.zip is not a readable stable-baselines3 zip'. A pair runs only when both arms are ready on ONE protocol and every zip sha results/<prefix>_seed<k>.txt records matches its final.zip; the episode route repeats the whole check before every build.
- Discovery: discover(root) lists root/runs*/ directories whose name matches RUNS_NAME, sorted by name; inside each it keeps only children matching ^(sighted|blind)_seed([0-9]+)$ and ignores _logs, ckpt_*.zip, checkpoint.zip, LAUNCH.txt and every other file. A future runs_X appears with no code change. Every pair is listed; refused pairs carry their reason. Experiment identity: prefix = run_phase_d.result_prefix(dir) (runs -> phase_d, runs_X -> X); name = run_phase_d.CLOSED_PREFIX.get(prefix) or f'{runs} (no name recorded)'.
- Verdicts are QUOTED, never computed; each line is cited results/<file>:<line>(-<last>). Anchors (M2): d2 = PHASE_D2_RESULT.txt:30-35 (RESULT: INCONCLUSIVE, the whole item) and :86-89 (Both are C1 agents ... never 'preview does not help'); phase_d = PHASE_D_RESULT.txt:26-31 (NOT SIGNIFICANT with its C1 sentence), PHASE_D_RESULT.txt:33-40 (AND THE BLINDED ARM IS NOT BLIND), PHASE_D2_RESULT.txt:65-76 (INCONCLUSIVE [MEI set AFTER this result], through the POST-HOC paragraph, labelled post-hoc); c4 unchanged. Quote WHOLE items, never a fragment cut before its caveat (M1 F8). States: 'found' (every anchor present), 'missing' (a file or an anchor gone: the box and the short line say «لم يُعثر على سطر الحكم في {files}: لا تقرأ هؤلاء الوكلاء بدونه»), 'none' (no row: «لا يوجد حكم مسجَّل مسبقاً لهذه التجربة في results/. ما تعرضه هذه الصفحة ليس نتيجة.»). The short line is authored text and is shown only when every anchor it summarises was found.
- Short lines, verbatim (<U+XXXX> marks where the source carries the escape backslash-u-XXXX; <Q> marks an ASCII double quote): c4 unchanged; d2 ar «غير حاسم · وكلاء C1 <U+200F>(50<U+202F>000 خطوة)» en 'inconclusive · C1 agents, 50<U+202F>000 steps'; phase_d ar «غير دال إحصائياً · غير حاسم (قراءة لاحقة) · الذراع <Q>العمياء<Q> ليست عمياء · وكلاء C1» en 'not significant · inconclusive (post-hoc) · the <Q>blind<Q> arm is not blind · C1 agents'. Glosses: INCONCLUSIVE «غير حاسم: التجربة لا تميّز بين <Q>لا أثر<Q> و<Q>أثر يهمّ الفريق<Q>» / 'Inconclusive: the experiment cannot tell 'no effect' from 'an effect the team cares about''; NOT SIGNIFICANT «غير دال إحصائياً، مع وكلاء بميزانية C1» / 'Not statistically significant, with agents at the C1 budget'; NOT-CONVERGED and SMALLER THAN THE MEI unchanged.
- Table rows are quoted from analyse_phase_d2.load(prefix) (blind minus sighted, per seed), rounded to one decimal as the results tables print them, never recomputed, shown only in the picker and always with its qualifier: D2 and C4 «(فرق وسيطَي 20 حلقة، لكلٍّ منها طريقها وأوزانها؛ ليست هذه الحلقة)», Phase D «(فرق وسيطَي 20 حلقة على الطريق نفسه بأوزان مختلفة؛ ليست هذه الحلقة)». The page computes no statistic, no difference between the two cars, and shows no winner.
- Picker: nothing is selected and nothing computes when the page opens from its nav link (no query). An address selects only what exists in the catalog and can run (never a refused pair, a greyed experiment or an episode outside 1..20). «احسب» sends exactly one preempt=1 request for the selected (runs, seed, ep). Every change of a select replaces the address with '/agents' + selectionSearch(sel) (history.replaceState, never pushState) and clears the displayed episode (frames, meta, road, profile, chase, panel, loading card, error) and bumps loadToken so late responses are dropped. Pair label «بذرة k · الأعمى <U+2212> المُبصر {diff}» with {diff} inside a left-to-right isolate <U+2066>...<U+2069> and U+2212 for negatives; each arm's «دُرِّب {budget} خطوة (من final.zip)». Episode option «حلقة 1 · الصعود عند 141 ث · 13.3٪ · الأوزان: عزم 0.69 / وقود 0.01 / عمر المكوّنات 0.30» (M1's key); Phase D shows «الطريق نفسه (180 ث · 12.0٪)؛ تختلف الحلقات في الأوزان فقط».
- Phase D's blind car reads «لا يرى الطريق أمامه، لكنه قد يحفظه: الطريق نفسه في كل حلقة» / 'Does not see the road ahead, but may have memorised it: the same road in every episode' wherever the blind car is named (scene label, picker budget line, verdict box scored line, stopped-lane line), and its panel line carries the same caveat cited as results/PHASE_D_RESULT.txt:33-40 (from the verdict's 'not_blind' line). D2 and C4 keep «لا يرى الطريق أمامه».
- Numbers: thousands are grouped with U+202F, never a plain space (a plain space swaps the groups in Arabic: 300 000 is drawn as 000 300); every grouped number in Python or JS source is written with the escape, and the M1 test that forbids a plain-space group covers every SHORT_VERDICT and GLOSS entry. Arabic temperatures read «°م». The turbine limit displays as 850.
- The replay lab: app/static/simulation.html gets exactly one <a href='/agents' data-i18n='nav.agents'>الوكلاء</a>, inserted right AFTER its first nav link (the lab's phone rule in style.css:100 hides .topbar nav a:last-child). Nothing else in /simulation changes and no lab test file changes; app.test_simulation, app.test_replay (and --full at the milestone) and the node glob must pass, with counts read from each run. The lab launcher app/start-simulation.ps1 may only gain banner lines (the /agents URL and a stable-baselines3 notice); its interpreter is not changed.
- ESCAPE TRAP on this machine: the Write/Edit/Bash tool inputs decode a typed backslash-u-XXXX into the literal (often invisible) character, and a typed doubled backslash stays doubled, so neither produces the escape text. Any line whose source must carry backslash-u-XXXX (U+202F, U+200F, U+2066, U+2069, U+2212, U+2011) is written by a short Python script run with $PY that builds the escape as chr(92) + 'uXXXX', then byte-checked: count of chr(0xXXXX) in the file == 0 and count of chr(92) + 'uXXXX' == the stated number. The plan keeps escapes as text (<U+XXXX>), never as characters.
- Environment: every command block exports PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe, PYTHONIOENCODING=utf-8, PYTHONDONTWRITEBYTECODE=1, GIT_OPTIONAL_LOCKS=0, runs with cwd = the repository root (never %TEMP%: a stray inspect.py there shadows the stdlib), and puts scratch files under $SCRATCH (the session scratchpad), never in the repository. The server for a browser check is started as `$PY -m app.server --simulation` from the repository root, in the background.
- Tests: Python unittest in app/test_agents.py; node:test files app/static/sim/*.test.mjs (a helper module that is not *.test.mjs is not run by the glob). app/test_replay.py test_read_only scans app/test_agents.py too: no `.write(` except on lines containing `fh.write`; banned tokens in tests are raw regexes; fixtures are made with shutil.copy, json.dump(obj, fh), FP.claim_running/release_running, in tempfile directories OUTSIDE the repository. Read every count from a run.
- TDD for every task: write the failing test, run it and see it fail for the stated reason, implement, run it green, commit. Steps are 2-5 minutes each, with complete code in every code step: no placeholders, no 'similar to task N', no 'add error handling'.
- Commits go to branch JMF-2340550-sep17 only. After ANY change under app/, run `$PY -m app.test_replay` and paste its WHOLE output into the commit message (and `--full` at the milestone). Before committing a new tracked file: `git add` it, run `$PY verify_docs.py` and read its last line (a new docstring can trip a figure in verify_docs.RETIRED). Messages are built in $SCRATCH and committed with `git commit -F`; every message ends with the line 'Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>'.
- Wording: always «حاسوب المحرك المنمذَج», never «حاسوب المحرك» alone; no string says 'preview helps', «يساعد الاستباق» or «الاستباق يساعد»; never 'preview does not help' as the page's own claim (only inside a quote that negates it).
- Not in M2: anything jev (app/jev.py, POST routes, tap-unlock.mjs, the .gitignore key patterns, the server.py:43 docstring amendment).

## Review Focus

- **The viewer computes one episode (say runs_c4 seed 5 episode 1), then changes the experiment, the pair or the episode; or a poll for the old key is in flight when the select changes. With M1's code the old frames, meta, road, profile, chase view, pause panel and badge stay on screen under the new selection, and a late response can append the old key's frames to it.** Expected: Every change of any select that alters the selection bumps loadToken (late responses for the old key are dropped by the existing token checks), clears frames, meta, metaKey, road, the profile host, the chase scene, the pause panel, the loading card and the error, disables play/restart/seek, shows the scene prompt «اختر تجربة وزوجاً وحلقة ثم اضغط احسب», and renders the verdict box from the NEWLY selected experiment. The scene never shows an episode the three selects do not name. Pinned in agents-page-nav.test.mjs 'changing the pair after a computation clears the old episode and drops its late frames'. (pinned in T7)
- **Opening /agents from its own nav link (no query), or reloading/sharing an address that names a refused pair (runs_sixspeed_18sep&seed=0), an unknown runs directory, a seed that is not in the catalog, runs_C4, or ep=21. A lenient picker would choose a default pair, keep the refused pair selected, or start computing on boot.** Expected: resolveSelection(catalog, parsePickerQuery(location.search)) selects only what exists and can run, level by level (an experiment with no runnable pair is not selectable), and nothing otherwise; the page's only request at boot is GET /api/agents/catalog; «احسب» stays disabled with the reason from computeState ('agents.pick.none', 'agents.pick.need_pair', 'agents.pick.need_episode' or 'agents.load.no_sb3'); a full valid address restores its three choices and still computes nothing until «احسب». Pinned in agent-picker.test.mjs (resolution and round trip through selectionSearch), agents-page-nav.test.mjs 'from the nav link the page selects nothing, computes nothing, and says what to choose', and agents-page-run.test.mjs 'a full address restores its selection and computes nothing until «احسب»'. (pinned in T6)
- **A Phase D pair is chosen and computed. M1's code names the blind car with the D2/C4 label in renderStopped (LANE_LABEL[1]), the verdict box's scored lines and the picker's budget lines, its panel line lacks the memorisation caveat, and meta.episode.grade is None for Phase D so the SIMULATED badge reads a dash instead of 12.** Expected: laneLabel(1) is blindLabelKey(protocol) everywhere the blind car is named (scene label, pick-note budget line, verdict-scored line, lane-stopped line); the blind panel line uses 'agents.seen.blind_phase_d' with {cite} = notBlindCite(verdict) = 'results/PHASE_D_RESULT.txt:33-40'; episode_meta's episode comes from episode_row so Phase D's grade is 0.12 and the badge reads 12.0; the episode select says «الطريق نفسه» and the note under it «الطريق نفسه (180 ث · 12.0٪)؛ تختلف الحلقات في الأوزان فقط». Pinned by RouteTests.test_episode_route_serves_phase_d_and_d2 (grade 0.12, climb 180.0) and agents-page-nav.test.mjs 'Phase D: the same-road episodes, and the blind car named as possibly memorising its road wherever it is named'. (pinned in T8)
- **The d2 and phase_d verdict anchors. results/PHASE_D2_RESULT.txt carries TWO 'RESULT: INCONCLUSIVE' lines (:30 for D2, :65 for Phase D's post-hoc reading); a loose pattern quotes the wrong one, and a short n cuts an item before its caveat (d2 at :33 before 'power_analysis.py predicted this cell BEFORE...', the post-hoc item at :70 before 'POST-HOC reading and is labelled so').** Expected: d2 'result' pattern is anchored with the end of line (r'^ *RESULT: INCONCLUSIVE *$' style) and found at :30 with n = 6; 'c1' at :86 with n = 4; phase_d 'result' :26 n = 6, 'not_blind' :33 n = 8, 'post_hoc' :65 n = 12. Tests pin every line number, text == the file's own lines, and that the line after every d2 and phase_d quote is blank (a whole item); each SHORT_VERDICT is shown only when its required anchors are found and becomes MISSING_TEXT naming EVERY missing file otherwise; D2's «50<U+202F>000» never carries a plain space. Pinned by CatalogTests.test_d2_and_phase_d_verdicts and test_verdict_when_an_anchor_or_a_file_is_gone. (pinned in T1)
- **With M2 the viewer switches episodes often: they press «احسب» for a new key while another episode is still computing. The first answer is 'busy' and M1's text tells them to «اضغط احسب لإيقافها وبدء هذه» although this very press already sent preempt=1; and when the new key is already cached, M1's store answers 'ready' from the cache without cancelling the other build (F6), which then runs unwatched for up to 75 s.** Expected: Page: after its own preempt the busy state reads 'agents.load.stopping' «يُوقَف حساب الحلقة السابقة ({runs} بذرة {seed} حلقة {ep})…»; M1's 'agents.load.busy' text appears only when this page did not preempt (a retry after the server was unreachable, where the preempt may never have arrived). Server: a preempt for a key other than the active build sets the cancel event before any branch answers (cache hit, error or busy); a preempt for the key already building never cancels it; a superseded build that then raises records no error. Pinned by StoreTests.test_preempt_answered_from_the_cache_cancels_the_other_build, StoreTests.test_a_superseded_build_that_fails_reports_nothing and agents-page-nav.test.mjs '«احسب» over another running build says it is stopping it'. (pinned in T5)

## Gaps against the design found by the plan's critic

Each is ruled on in the build ledger before Task 1 and recorded in the spec's walkthrough log by Task 10.

- Design §4 'Runnability' and §8 say that when stable-baselines3 cannot be imported, every pair shows 'cannot run: stable-baselines3 not installed' and the catalog says 'cannot run'. The plan carries catalog.sb3, but computeState reports 'agents.load.no_sb3' only after a full experiment/pair/episode selection. No pair or experiment option says it, so a viewer on the launcher's .venv interpreter chooses three levels before learning nothing can run.
- Design §4 'Table rows' says missing seeds are named from analyse_phase_d2.load's `incomplete` list. T3's table_rows returns `incomplete`, but discover keeps only `diffs`, so the catalog never carries it. A pair whose result file is incomplete reads 'no row for this seed in the results table' and the incompleteness is never named. This cannot be seen on today's tree, where all 24 rows are complete.
- Design §8 says refused agents are 'listed and disabled with reason and fields'. The page shows only problems[0], in pair_refused and experiment_refused. For a plant mismatch, the stored/live field lines (problems[1..]) and the second arm's reason never reach the page, though the catalog carries them.
- Design §6 writes Phase D's episode note as «(180 ث · 12٪)». The plan prints «12.0٪» (T6's stated deviation, following the skeleton), but none of T10's design amendments record it. That leaves the spec and the page disagreeing, the prose-drift shape of CLAUDE.md mistake 11.
- Design §10 (M1 Verify) says app/start-simulation.ps1 calls bare python (the .venv, which has no SB3) and names only /simulation, and that 'M2 ... can fix both'. T9 fixes the banner, adds a warning, and deliberately leaves the interpreter unchanged. That ruling is not among T10's amendments or the M2 walkthrough-log row, so the design still reads as if both were to be fixed.

---

### Task 1: agent_catalog: the D2 and Phase D verdicts quoted as whole items, their short lines and glosses, and a not-found text that names every missing file

**Files:**
- Modify: `app/agent_catalog.py:18-19` (module docstring), `:199-205` (end of `VERDICT_LINES`, `CELLS`), `:213-215` (end of `SHORT_VERDICT`), `:227-233` (end of `GLOSS`, `MISSING_TEXT`), `:272-273` (`verdict()`'s missing branch). These are M1's line numbers. Each Edit below also gives the line as the file stands when that edit is made. Every `old_string` is unique in its file, so the Edit tool finds it either way.
- Test: `app/test_agents.py:416-417` (`CatalogTests.test_c4_verdict`), `:421-429` (`test_no_plain_space_inside_a_grouped_number`, replaced by three new tests plus an updated version of itself)

**Interfaces:**
- Consumes:
  - `app/agent_catalog.py:184` `Anchor = namedtuple("Anchor", "key file pattern n")`
  - `:241` `verdict(prefix, root=ROOT)`. It returns `{state, lines, missing, short, cells}` and takes the first line that matches `rx.search`.
  - `results/PHASE_D2_RESULT.txt:30-35` (line 36 is blank), `:65-76` (line 77 blank), `:86-89` (line 90 blank)
  - `results/PHASE_D_RESULT.txt:26-31` (line 32 blank), `:33-40` (line 41 blank)
- Produces:
  - `VERDICT_LINES["d2"]`: `result` at line 30, n 6; `c1` at 86, n 4.
  - `VERDICT_LINES["phase_d"]`: `result` at 26, n 6; `not_blind` at 33, n 8; `post_hoc` at 65, n 12.
  - `CELLS["d2"] = {"result": "INCONCLUSIVE"}` and `CELLS["phase_d"] = {"result": "NOT SIGNIFICANT", "post_hoc": "INCONCLUSIVE (post-hoc)"}`.
  - `SHORT_VERDICT["d2"]` (requires `result`, `c1`) and `SHORT_VERDICT["phase_d"]` (requires `result`, `not_blind`, `post_hoc`).
  - `GLOSS["INCONCLUSIVE"]`, `GLOSS["NOT SIGNIFICANT"]`, `GLOSS["INCONCLUSIVE (post-hoc)"]`.
  - `MISSING_TEXT` with a `{files}` slot, filled by `" · ".join(f"results/{f}" for f in missing)` over the sorted missing list.
  - `verdict()` keeps its return shape, and returns `"found"` for `d2` and `phase_d` on the real tree.
  - After this task, `app/agent_catalog.py` holds the escape text backslash-u-202f 6 times and backslash-u-200f once, and neither character literally.

**Where the design and the results files disagree, the files win:**
- The design's d2 row cites `PHASE_D2_RESULT.txt:30-33`. That item actually runs to `:35` ("power_analysis.py predicted this cell BEFORE this experiment ran, from Phase D's measured spread."), so it is quoted whole with n = 6. This follows the M1 final review's F8 lesson: never cut a quote before its caveat.
- The post-hoc quote is `:65-76` (n = 12, including the blank line 71). Lines `:72-76` are the paragraph that makes the reading post-hoc, so they must be in the quote.

**Other changes in this task:**
- `MISSING_TEXT`'s slot is renamed from `{file}` to `{files}`, and it now carries the `results/` prefix itself. This closes the M1 build-record item "MISSING_TEXT names only missing[0]".
- It also closes two more M1 left-for-later items: the Task 3 test gap "verdict() with the results file absent", and Task 10b's "the regex misses a group running straight into Arabic letters".

**The escape trap applies to every edit in this task.** The Edit tool decodes a typed backslash-u-XXXX. So:
- (a) No `old_string` below contains a file line that carries such an escape. An `old_string` that does is silently not matched; this happened while prototyping this task.
- (b) The two new short lines are typed with the ASCII tokens `<U+200F>` and `<U+202F>`. Step 3b turns those into the escape text with a script and byte-checks the result.

- [ ] **Step 1: Write the failing test**

**Edit 1a** (`app/test_agents.py`, lines 416-417 of `CatalogTests.test_c4_verdict`), replace:

```python
        self.assertEqual(v["short"], {lang: AC.MISSING_TEXT[lang].format(file="C4_RESULT.txt")
                                      for lang in ("ar", "en")})
```

with:

```python
        self.assertEqual(v["short"], {lang: AC.MISSING_TEXT[lang].format(files="results/C4_RESULT.txt")
                                      for lang in ("ar", "en")})
```

**Edit 1b** (`app/test_agents.py`, lines 421-429: the whole of `test_no_plain_space_inside_a_grouped_number`), replace:

```python
    def test_no_plain_space_inside_a_grouped_number(self):
        for table_name, table in (("SHORT_VERDICT", AC.SHORT_VERDICT), ("GLOSS", AC.GLOSS)):
            for key, langs in table.items():
                for lang in ("ar", "en"):
                    s = langs[lang]
                    self.assertIsNone(
                        re.search(r"\d \d{3}\b", s),
                        f"{table_name}[{key!r}][{lang!r}] has a plain-space thousands "
                        "separator")
```

with:

```python
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
```

`"300 000خطوة"` above is typed with a plain ASCII space on purpose. It is the probe that proves the check can fail.

- [ ] **Step 2: Run it to verify it fails**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
$PY -m app.test_agents CatalogTests.test_d2_and_phase_d_verdicts CatalogTests.test_verdict_when_an_anchor_or_a_file_is_gone CatalogTests.test_every_prefix_has_its_cells_glosses_and_short_line CatalogTests.test_c4_verdict CatalogTests.test_no_plain_space_inside_a_grouped_number 2>&1 | grep -E "Error|^Ran|^FAILED|^OK|\.\.\. ok"
```

Expected: FAIL with "FAILED (failures=5, errors=1)", made of:
- `KeyError: 'file'` from `test_c4_verdict` (the placeholder is still `{file}`);
- `AssertionError: Tuples differ: ('none', []) != ('found', [])` twice (d2 and phase_d have no row yet);
- `AssertionError: Lists differ: [] != ['INCONCLUSIVE']`;
- `AssertionError: Lists differ: ['none', 'none'] != ['found', 'found']`;
- `AssertionError: Items in the second set but not the first:` (d2, phase_d).

`test_no_plain_space_inside_a_grouped_number ... ok` passes already. It is a strengthened test, not a new one, and its probe line is what shows it can fail.

- [ ] **Step 3: Implement**

**Edit 1c** (`app/agent_catalog.py`, lines 18-19 of the module docstring), replace:

```python
M1 carries the C4 row only; the tables are keyed by result prefix so M2 adds
the d2 and phase_d rows without changing a signature.
```

with:

```python
The tables carry the c4, d2 and phase_d rows, keyed by result prefix; a
prefix with no row (a future runs_X) has the verdict state 'none'.
```

**Edit 1d** (`app/agent_catalog.py`, lines 199-205: the end of `VERDICT_LINES`, and `CELLS`), replace:

```python
        Anchor("one_seed", "PREREGISTRATION_C4.md",
               r"^2\. \*\*It rests on the sign test's threshold", 11),
    ),
}

# The anchor key that carries each quoted cell, in display order.
CELLS = {"c4": {"result": "SMALLER THAN THE MEI", "convergence": "NOT-CONVERGED"}}
```

with:

```python
        Anchor("one_seed", "PREREGISTRATION_C4.md",
               r"^2\. \*\*It rests on the sign test's threshold", 11),
    ),
    "d2": (
        # :30-35 whole: the item ends on the prediction power_analysis.py made
        # BEFORE the experiment ran. The pattern ends at the line's end, so the
        # bracketed Phase D line (:65) can never be taken for it.
        Anchor("result", "PHASE_D2_RESULT.txt", r"^\s*RESULT: INCONCLUSIVE\s*$", 6),
        Anchor("c1", "PHASE_D2_RESULT.txt", r"^\s*Both are C1 agents", 4),
    ),
    "phase_d": (
        Anchor("result", "PHASE_D_RESULT.txt",
               r"^\s*RESULT: NOT SIGNIFICANT at alpha 0\.05\.\s*$", 6),
        Anchor("not_blind", "PHASE_D_RESULT.txt", r"^\s*AND THE BLINDED ARM IS NOT BLIND\.", 8),
        # Phase D under D2's MEI rule, :65-76 whole: the paragraph after the
        # blank line (:72-76) is what says the reading is post-hoc.
        Anchor("post_hoc", "PHASE_D2_RESULT.txt",
               r"^\s*RESULT: INCONCLUSIVE\s+\[MEI set AFTER this result", 12),
    ),
}

# The anchor key that carries each quoted cell, in display order. The cell
# names are authored: 'INCONCLUSIVE (post-hoc)' is PHASE_D2_RESULT.txt:65,
# whose own text is 'INCONCLUSIVE   [MEI set AFTER this result -- see below]'.
CELLS = {
    "c4": {"result": "SMALLER THAN THE MEI", "convergence": "NOT-CONVERGED"},
    "d2": {"result": "INCONCLUSIVE"},
    "phase_d": {"result": "NOT SIGNIFICANT", "post_hoc": "INCONCLUSIVE (post-hoc)"},
}
```

**Edit 1e** (`app/agent_catalog.py`, lines 235-237 once Edit 1d is in, 213-215 in M1: the end of `SHORT_VERDICT`). Type the `<U+200F>` and `<U+202F>` tokens exactly as shown, as ASCII. Replace:

```python
        "requires": ("result", "seeds", "disagree", "convergence"),
    },
}
```

with:

```python
        "requires": ("result", "seeds", "disagree", "convergence"),
    },
    "d2": {
        "ar": "غير حاسم · وكلاء C1 <U+200F>(50<U+202F>000 خطوة)",
        "en": "inconclusive · C1 agents, 50<U+202F>000 steps",
        "requires": ("result", "c1"),
    },
    "phase_d": {
        "ar": 'غير دال إحصائياً · غير حاسم (قراءة لاحقة) · الذراع "العمياء" ليست عمياء · وكلاء C1',
        "en": 'not significant · inconclusive (post-hoc) · the "blind" arm is not blind · C1 agents',
        "requires": ("result", "not_blind", "post_hoc"),
    },
}
```

**Edit 1f** (`app/agent_catalog.py`, lines 259-265 once Edits 1d-1e are in, 227-233 in M1: the end of `GLOSS`, and `MISSING_TEXT`), replace:

```python
    "NOT-CONVERGED": {"ar": "لم يستقر التدريب", "en": "Training had not settled"},
}

MISSING_TEXT = {
    "ar": "لم يُعثر على سطر الحكم في results/{file}: لا تقرأ هؤلاء الوكلاء بدونه",
    "en": "verdict line not found in results/{file}: do not read these agents without it",
}
```

with:

```python
    "NOT-CONVERGED": {"ar": "لم يستقر التدريب", "en": "Training had not settled"},
    # PHASE_D2_RESULT.txt:31-33, in the team's words.
    "INCONCLUSIVE": {
        "ar": 'غير حاسم: التجربة لا تميّز بين "لا أثر" و"أثر يهمّ الفريق"',
        "en": 'Inconclusive: the experiment cannot tell "no effect" from '
              '"an effect the team cares about"',
    },
    "NOT SIGNIFICANT": {
        "ar": "غير دال إحصائياً، مع وكلاء بميزانية C1",
        "en": "Not statistically significant, with agents at the C1 budget",
    },
    # PHASE_D2_RESULT.txt:72-76: the MEI was set after Phase D's result.
    "INCONCLUSIVE (post-hoc)": {
        "ar": "غير حاسم، وهي قراءة لاحقة: الحد الأدنى المهم (50 وحدة) حُدِّد بعد أن عُرفت "
              "نتيجة Phase D، فهذا التصنيف لم يُسجَّل مسبقاً. "
              'التجربة لا تميّز بين "لا أثر" و"أثر يهمّ الفريق"',
        "en": "Inconclusive, and a post-hoc reading: the MEI (50 units) was set after "
              "Phase D's result was known, so this classification was not preregistered. "
              'The experiment cannot tell "no effect" from "an effect the team cares about"',
    },
}

# {files}: every missing file, as results/<file>, joined by ' · '.
MISSING_TEXT = {
    "ar": "لم يُعثر على سطر الحكم في {files}: لا تقرأ هؤلاء الوكلاء بدونه",
    "en": "verdict line not found in {files}: do not read these agents without it",
}
```

**Edit 1g** (`app/agent_catalog.py`, lines 324-325 once Edits 1d-1f are in, 272-273 in M1: `verdict()`'s missing branch), replace:

```python
    if missing:
        short = {lang: MISSING_TEXT[lang].format(file=missing[0]) for lang in MISSING_TEXT}
```

with:

```python
    if missing:
        files = " · ".join(f"results/{f}" for f in missing)
        short = {lang: MISSING_TEXT[lang].format(files=files) for lang in MISSING_TEXT}
```

- [ ] **Step 3b: Turn the tokens into escape text, and byte-check**

The script builds each escape as `chr(92) + "u" + hex`, so no tool can decode it on the way into the file. It is written once to `$SCRATCH`, and any later task that carries a token can reuse it.

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory, never the repository}"
cat > "$SCRATCH/m2_fix_escapes.py" <<'EOF'
"""Turn every <U+XXXX> token in the named files into the escape TEXT
backslash-u-xxxx (built from chr(92), so no tool can decode it), then print
the byte check: tokens left, and per code point the literal and escape counts."""
import re
import sys
from pathlib import Path

CHECK = ("200F", "202F", "2066", "2069", "2212", "2011")
for name in sys.argv[1:]:
    p = Path(name)
    s = p.read_text(encoding="utf-8")
    s = re.sub(r"<U\+([0-9A-F]{4})>", lambda m: chr(92) + "u" + m.group(1).lower(), s)
    p.write_text(s, encoding="utf-8", newline="")
    b = p.read_text(encoding="utf-8")
    print(name, "| tokens left", b.count("<U+"))
    for cp in CHECK:
        lit, esc = b.count(chr(int(cp, 16))), b.count(chr(92) + "u" + cp.lower())
        if lit or esc:
            print(f"   U+{cp}: literal {lit}, escape {esc}")
EOF
$PY "$SCRATCH/m2_fix_escapes.py" app/agent_catalog.py
git diff --stat
```

Expected output, exactly (the file stays LF-only, as it was):

```
app/agent_catalog.py | tokens left 0
   U+200F: literal 0, escape 1
   U+202F: literal 0, escape 6
```

Any other count means an escape was decoded or a token was mistyped. Fix the line, never the expected count.

- [ ] **Step 4: Run to verify it passes**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory, never the repository}"
$PY -m app.test_agents CatalogTests.test_d2_and_phase_d_verdicts CatalogTests.test_verdict_when_an_anchor_or_a_file_is_gone CatalogTests.test_every_prefix_has_its_cells_glosses_and_short_line CatalogTests.test_c4_verdict CatalogTests.test_no_plain_space_inside_a_grouped_number 2>&1 | tail -3
$PY -m app.test_agents > "$SCRATCH/m2t1_agents.txt" 2>&1; grep -E "^Ran |^OK|^FAILED|== proof" "$SCRATCH/m2t1_agents.txt"
```

Expected:
- The five named tests give "Ran 5 tests" and "OK".
- The default suite takes about 3.5 min, because the == proof builds a C4 pair on the GPU. It gives "Ran 41 tests" and "OK (skipped=1)"; the one skip is `test_phase_d_pair_full`, which runs only with --full.
- The proof prints the line "== proof PROVEN: device cuda, torch 2.11.0+cu128, sb3 2.9.0, sighted damage 501.56474787343603, blind 1229.059247261675, built in N s".

Read the counts from the run.

- [ ] **Step 5: Commit**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory, never the repository}"
git rev-parse --abbrev-ref HEAD            # must print JMF-2340550-sep17
git status --short                         # exactly: M app/agent_catalog.py, M app/test_agents.py
$PY -m app.test_replay > "$SCRATCH/m2t1_replay.txt" 2>&1; tail -1 "$SCRATCH/m2t1_replay.txt"
git add app/agent_catalog.py app/test_agents.py
$PY verify_docs.py | tail -1
{
  printf '%s\n' "Agent replay M2 Task 1: the D2 and Phase D verdicts, quoted as whole items" "" \
    "agent_catalog gains the d2 row (PHASE_D2_RESULT.txt:30-35, the whole INCONCLUSIVE" \
    "item, and :86-89, the C1 quote) and the phase_d row (PHASE_D_RESULT.txt:26-31 and" \
    ":33-40, and PHASE_D2_RESULT.txt:65-76, the post-hoc reading whole), with their" \
    "cells, glosses and short lines. The design's d2 anchor said :30-33; the item runs" \
    "to :35, so it is quoted whole (the M1 final review's F8 lesson). The D2 short line" \
    "writes its grouped 50 000 with the U+202F escape (file: 6 u202f, 1 u200f, 0 literal)." \
    "MISSING_TEXT now names every missing file, not only the first. The grouped-number" \
    "check looks ahead for a digit instead of a word boundary, so a group running into" \
    "Arabic letters is caught (M1 build record, Task 10b), and it now also fails on a" \
    "literal U+202F or U+200F in agent_catalog.py." "" \
    "\$ python -m app.test_agents (summary)"
  grep -E "^Ran |^OK|== proof" "$SCRATCH/m2t1_agents.txt"
  printf '\n%s\n' "\$ python -m app.test_replay"
  cat "$SCRATCH/m2t1_replay.txt"
  printf '\n%s\n' "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
} > "$SCRATCH/m2t1_msg.txt"
git commit -F "$SCRATCH/m2t1_msg.txt"
git log --oneline -1
```

Expected:
- `app.test_replay`'s last line: "49 of 49 checks pass".
- `verify_docs.py`'s last line: "All 67 checks pass (782 figure mentions scanned in the documents)." Read both from the runs. If verify_docs names a line in these two files, reword that line; never change the checker.
- One new commit on JMF-2340550-sep17.

---


---

### Task 2: agent_catalog: check_pair (find_pair's checks without raising), a missing directory is a KeyError, an unreadable final.zip is incomplete, and the M1 status test gaps

**Files:**
- Modify: `app/agent_catalog.py:36-41` (the lowercase comment and the constants), `:85-91` (`read_agent`'s head), `:104-106` (the arm-rule comment), `:118-122` (status step 7), `:147-180` (`find_pair`, split into `check_pair` and `find_pair`). These are M1's numbers, and Task 1 did not move them: its edits lie below line 186, and its docstring edit keeps the line count.
- Test: `app/test_agents.py:177-180` (`_fake_agent` gains `src_runs`), and two new tests inserted after `CatalogTests.test_catalog_synthetic` (after line 355)

**Interfaces:**
- Consumes:
  - `read_agent(runs, name, root=ROOT)` and `find_pair(runs, seed, root=ROOT)` as M1 wrote them (`app/agent_catalog.py:85`, `:147`)
  - `scored_shas(prefix, seed, root)` (`:125`); `Refused(problems)` (`:44`); `RUNS_NAME`, `AGENT_NAME`, `ARMS` (`:39-41`)
  - `fingerprint.model_budget` (`:342`; returns `None` for a file that is not an SB3 zip) and `format_budget` (`:473`)
  - `run_phase_d.result_prefix` (`:94`) and `CLOSED_PREFIX` (`:113`)
  - the test helpers `_fake_agent` (`app/test_agents.py:177`) and `_fake_pair` (`:193`)
- Produces:
  - `agent_catalog.UNREADABLE_ZIP = "final.zip is not a readable stable-baselines3 zip"`.
  - `read_agent` keeps the same keys, with two changes:
    - It raises `KeyError(f"{runs}/{name}")` when `root/runs/name` is not a directory. This is checked right after the name patterns, before status step 1.
    - At step 7, when `FP.model_budget(final.zip)` is `None`, it returns status `"incomplete"` with reason `UNREADABLE_ZIP`, `protocol` and `train_dt` filled, and `budget`/`budget_line`/`zip_sha` set to `None`. This reverses M1 ruling 6.
  - `check_pair(runs, seed, root=ROOT) -> {runs, seed, prefix, experiment, protocol, result_file, agents, problems}`. It runs `find_pair`'s checks in `find_pair`'s order, but does not raise `Refused`:
    - `problems == []` means the pair may run.
    - `protocol` is the arms' shared protocol once both are ready and agree, else `None`.
    - `result_file` is `(root/"results"/f"{prefix}_seed{seed}.txt").is_file()`.
    - Each agent carries `scored`: `"match"` or `"not recorded"` once the sha check has run, or `None` when an earlier check refused the pair.
    - Problem strings are byte for byte M1's, and `KeyError` is raised exactly as `find_pair` raises it.
  - `find_pair(runs, seed, root=ROOT)` is `check_pair` plus `raise Refused(pair["problems"])` when the list is non-empty. It returns M1's keys plus `"problems": []`.
  - Test helper `_fake_agent(root, runs, name, src_arm, drop=(), src_runs="runs_c4", **meta_changes)`, which Task 3 reuses.

**M1 left-for-later items closed here:**
- "read_agent on a missing directory returns incompatible (no meta.json)".
- The Task 3 test gaps "unknown protocol" and "cross-arm protocol mismatch".
- Two wrong comments: `agent_catalog.py:36-38` said "the eight real C4 agents" (there are sixteen, in eight pairs), and `:104-105` said run_phase_d hands evaluate an f-string (it hands it `os.path.join`).
- Ruling 6 ("an unreadable final.zip stays ready ... revisit for M2 discovery") is revisited and reversed.

The status order and every M1 problem string stay byte for byte the same, because `RouteTests.test_refused_pair_is_409_and_never_polled` and the page's error list read them.

- [ ] **Step 1: Write the failing test**

**Edit 2a** (`app/test_agents.py`, lines 177-180: the head of `_fake_agent`), replace:

```python
def _fake_agent(root, runs, name, src_arm, drop=(), **meta_changes):
    """A copy of runs_c4/<src_arm>_seed0 at root/runs/name, built with
    shutil.copy and json.dump only. `drop` names files to leave out."""
    src = ROOT / "runs_c4" / f"{src_arm}_seed0"
```

with:

```python
def _fake_agent(root, runs, name, src_arm, drop=(), src_runs="runs_c4", **meta_changes):
    """A copy of <src_runs>/<src_arm>_seed0 at root/runs/name, built with
    shutil.copy and json.dump only. `drop` names files to leave out."""
    src = ROOT / src_runs / f"{src_arm}_seed0"
```

**Edit 2b** (`app/test_agents.py`, lines 353-357: the end of `test_catalog_synthetic`; the two new tests go between it and `test_c4_verdict`), replace:

```python
            with self.assertRaises(AC.Refused):
                AC.find_pair("runs_zz_blind", 0, root)
        self.assertEqual(threading.active_count(), threads, "the catalog started a thread")

    def test_c4_verdict(self):
```

with:

```python
            with self.assertRaises(AC.Refused):
                AC.find_pair("runs_zz_blind", 0, root)
        self.assertEqual(threading.active_count(), threads, "the catalog started a thread")

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
```

Notes on this test code:
- `scenario={"protocol": "something-else"}` replaces the copied meta's whole `scenario`, through `_fake_agent`'s `json.dump`. Step 5 refuses it before step 6 reads anything else.
- The `.mkdir` and `shutil.copy` calls are in the test file only. `NoWriteTests` scans only the three agent modules, and `app/test_replay.py`'s read-only scan bans only `.write(` outside `fh.write` lines.

- [ ] **Step 2: Run it to verify it fails**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
$PY -m app.test_agents CatalogTests.test_read_agent_refuses_a_directory_that_is_not_there CatalogTests.test_status_and_pair_gaps 2>&1 | grep -E "Error|^Ran|^FAILED|^OK"
```

Expected: FAIL with "FAILED (failures=2, errors=1)", made of:
- `AttributeError: module 'app.agent_catalog' has no attribute 'UNREADABLE_ZIP'`. Part (a) passes on M1's code, and part (b) stops here.
- `AssertionError: KeyError not raised` twice, once per subtest of the missing-directory test.

- [ ] **Step 3: Implement**

**Edit 2c** (`app/agent_catalog.py`, lines 36-41), replace:

```python
# Lowercase only: NTFS is case-insensitive, so "runs_C4" would otherwise
# resolve to the same directory as "runs_c4" while carrying no verdict --
# the eight real C4 agents would come back ready with no C4 caveats attached.
RUNS_NAME = re.compile(r"^runs[a-z0-9_]*$")
AGENT_NAME = re.compile(r"^(sighted|blind)_seed(\d+)$")
ARMS = ("sighted", "blind")
```

with:

```python
# Lowercase only: NTFS is case-insensitive, so "runs_C4" would otherwise
# resolve to the same directory as "runs_c4" while carrying no verdict --
# the sixteen real C4 agents (eight pairs) would come back ready with no C4
# caveats attached.
RUNS_NAME = re.compile(r"^runs[a-z0-9_]*$")
AGENT_NAME = re.compile(r"^(sighted|blind)_seed(\d+)$")
ARMS = ("sighted", "blind")
UNREADABLE_ZIP = "final.zip is not a readable stable-baselines3 zip"
```

**Edit 2d** (`app/agent_catalog.py`, lines 87-93 once Edit 2c is in, 85-91 in M1: the head of `read_agent`), replace:

```python
def read_agent(runs, name, root=ROOT):
    """One agent directory's status. KeyError if either name is malformed."""
    m = AGENT_NAME.fullmatch(str(name))
    if not RUNS_NAME.fullmatch(str(runs)) or m is None:
        raise KeyError(f"{runs}/{name}")
    arm, seed = m.group(1), int(m.group(2))
    d = Path(root) / runs / name
```

with:

```python
def read_agent(runs, name, root=ROOT):
    """One agent directory's status. KeyError if either name is malformed or
    the directory is not there: a missing directory is not an agent at all."""
    m = AGENT_NAME.fullmatch(str(name))
    if not RUNS_NAME.fullmatch(str(runs)) or m is None:
        raise KeyError(f"{runs}/{name}")
    arm, seed = m.group(1), int(m.group(2))
    d = Path(root) / runs / name
    if not d.is_dir():
        raise KeyError(f"{runs}/{name}")
```

**Edit 2e** (`app/agent_catalog.py`, lines 109-111 once Edits 2c-2d are in, 104-106 in M1), replace:

```python
    # evaluate.py:369 decides the arm by "blind" in the path string that
    # run_phase_d.py:330 hands it, f"{runs}/{name}". Apply that exact rule.
    scored_blind = "blind" in f"{runs}/{name}"
```

with:

```python
    # evaluate.py:369 decides the arm by "blind" in the path string that
    # run_phase_d.py:330 hands it, os.path.join(out, tag) -- a backslash on
    # Windows. "blind" in a path gives the same answer for either separator,
    # so f"{runs}/{name}" applies that exact rule here.
    scored_blind = "blind" in f"{runs}/{name}"
```

**Edit 2f** (`app/agent_catalog.py`, lines 125-129 once Edits 2c-2e are in, 118-122 in M1: status step 7), replace:

```python
    budget = FP.model_budget(str(d / "final.zip"))
    return dict(out, status="ready", protocol=protocol, budget=budget,
                budget_line=FP.format_budget(budget),
                zip_sha=budget["sha"] if budget else None,
                train_dt=meta.get("train_dt"))
```

with:

```python
    budget = FP.model_budget(str(d / "final.zip"))
    if budget is None:
        # Not an SB3 zip (FP.model_budget reads its 'data' member). M1 called
        # it ready with 'budget unreadable' and let SAC.load fail at build time.
        return dict(out, status="incomplete", reason=UNREADABLE_ZIP, protocol=protocol,
                    train_dt=meta.get("train_dt"))
    return dict(out, status="ready", protocol=protocol, budget=budget,
                budget_line=FP.format_budget(budget), zip_sha=budget["sha"],
                train_dt=meta.get("train_dt"))
```

**Edit 2g** (`app/agent_catalog.py`, lines 158-191 once Edits 2c-2f are in, 147-180 in M1: the whole of `find_pair`), replace:

```python
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
```

with:

```python
def check_pair(runs, seed, root=ROOT):
    """The sighted and blind agent of one seed, checked, with the problems
    RETURNED rather than raised: the catalog lists a refused pair with its
    reason, and find_pair raises on the same list, so both share one rule.

    KeyError for a name that is malformed or an arm directory not on disk.
    Otherwise 'problems' is [] when the pair may run. 'protocol' is the arms'
    shared protocol once both are ready and agree, else None. Each agent
    gains 'scored' ('match' or 'not recorded') once the sha check has run,
    None when an earlier check refused the pair first.
    """
    if (not RUNS_NAME.fullmatch(str(runs)) or not isinstance(seed, int)
            or isinstance(seed, bool) or seed < 0):
        raise KeyError(f"{runs}/{seed}")
    root = Path(root)
    if not all((root / runs / f"{arm}_seed{seed}").is_dir() for arm in ARMS):
        raise KeyError(f"{runs}/{seed}")
    agents = [dict(read_agent(runs, f"{arm}_seed{seed}", root), scored=None) for arm in ARMS]
    prefix = RPD.result_prefix(str(root / runs))
    pair = {"runs": runs, "seed": seed, "prefix": prefix,
            "experiment": RPD.CLOSED_PREFIX.get(prefix) or f"{runs} (no name recorded)",
            "protocol": None,
            "result_file": (root / "results" / f"{prefix}_seed{seed}.txt").is_file(),
            "agents": agents, "problems": []}
    problems = []
    for a in agents:
        if a["status"] != "ready":
            problems.append(f"{a['tag']}: {a['status']} -- {a['reason']}")
            problems.extend(f"{a['tag']}: {p}" for p in a["problems"])
    if problems:
        return dict(pair, problems=problems)
    if agents[0]["protocol"] != agents[1]["protocol"]:
        return dict(pair, problems=[f"the two arms were trained on different protocols: "
                                    f"{agents[0]['protocol']} and {agents[1]['protocol']}"])
    shas = scored_shas(prefix, seed, root)
    for a in agents:
        recorded = None if shas is None else shas[a["arm"]]
        if recorded is not None and recorded != a["zip_sha"]:
            problems.append(f"{a['tag']}: not the scored artefact -- results/{prefix}_seed{seed}.txt "
                            f"records zip sha {recorded}, final.zip is {a['zip_sha']}")
        a["scored"] = "match" if recorded is not None and recorded == a["zip_sha"] else "not recorded"
    return dict(pair, protocol=agents[0]["protocol"], problems=problems)


def find_pair(runs, seed, root=ROOT):
    """check_pair, raising Refused(problems) for a pair that must not run.
    KeyError for a name that is malformed or not on disk."""
    pair = check_pair(runs, seed, root)
    if pair["problems"]:
        raise Refused(pair["problems"])
    return pair
```

In M1, `result_file` was `shas is not None`. It is now whether the file exists. That gives the same answer whenever the file can be read, and it is known even when an earlier check refuses the pair.

- [ ] **Step 4: Run to verify it passes**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory, never the repository}"
$PY -m app.test_agents CatalogTests.test_read_agent_refuses_a_directory_that_is_not_there CatalogTests.test_status_and_pair_gaps 2>&1 | tail -3
$PY -m app.test_agents CatalogTests RouteTests NoWriteTests 2>&1 | tail -3
$PY -m app.test_agents > "$SCRATCH/m2t2_agents.txt" 2>&1; grep -E "^Ran |^OK|^FAILED|== proof" "$SCRATCH/m2t2_agents.txt"
```

Expected:
- The two named tests give "Ran 2 tests" and "OK". Part (d) runs rather than skipping on this machine: `runs/sighted_seed0` is phase-d and ready, and `runs_c4/blind_seed0` is d2 and ready.
- The three classes give "OK". M1's `test_names_never_become_paths`, `test_c4_pairs_are_the_scored_artefacts`, `test_catalog_synthetic` and the route tests show that `find_pair` keeps its contract.
- The default suite gives "Ran 43 tests", "OK (skipped=1)" and the "== proof PROVEN: device cuda ..." line.

Read the counts from the run.

- [ ] **Step 5: Commit**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory, never the repository}"
git rev-parse --abbrev-ref HEAD            # must print JMF-2340550-sep17
git status --short                         # exactly: M app/agent_catalog.py, M app/test_agents.py
$PY -m app.test_replay > "$SCRATCH/m2t2_replay.txt" 2>&1; tail -1 "$SCRATCH/m2t2_replay.txt"
git add app/agent_catalog.py app/test_agents.py
$PY verify_docs.py | tail -1
{
  printf '%s\n' "Agent replay M2 Task 2: check_pair, and the status gaps M1 left" "" \
    "check_pair runs find_pair's checks in find_pair's order and RETURNS the problems;" \
    "find_pair is check_pair plus raise Refused, so the catalog and the episode route" \
    "share one rule and every M1 problem string is unchanged. read_agent now raises" \
    "KeyError for a directory that is not there (M1 called it 'no meta.json'), and an" \
    "unreadable final.zip is 'incomplete' with UNREADABLE_ZIP instead of 'ready' with" \
    "'budget unreadable' (M1 ruling 6, revisited for discovery as it said). New tests" \
    "close the M1 gaps: an unknown protocol, an unreadable zip, two arms on different" \
    "protocols (runs/ sighted beside runs_c4/ blind). Two M1 comments corrected: sixteen" \
    "C4 agents in eight pairs, and run_phase_d hands evaluate os.path.join, not an f-string." "" \
    "\$ python -m app.test_agents (summary)"
  grep -E "^Ran |^OK|== proof" "$SCRATCH/m2t2_agents.txt"
  printf '\n%s\n' "\$ python -m app.test_replay"
  cat "$SCRATCH/m2t2_replay.txt"
  printf '\n%s\n' "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
} > "$SCRATCH/m2t2_msg.txt"
git commit -F "$SCRATCH/m2t2_msg.txt"
git log --oneline -1
```

Expected: "49 of 49 checks pass"; "All 67 checks pass (782 figure mentions scanned in the documents)."; one new commit.

---


---

### Task 3: The catalog's data: episode_row (agent_trace), table_rows and discover (agent_catalog), with the synthetic and real-tree catalog tests

**Files:**
- Modify:
  - `app/agent_trace.py:115`: insert `episode_row` before `_car`.
  - `app/agent_catalog.py:28`: import `warnings`.
  - `app/agent_catalog.py:361-362` after Tasks 1-2 (280-281 in M1): append the catalog section after `verdict()`.
- Test: `app/test_agents.py`:
  - `:23`: import `warnings`.
  - `:42`: module constants.
  - `:104-106`: insert `TraceTests.test_episode_row`.
  - Three `CatalogTests` inserted after `test_catalog_synthetic` (whose end is lines 353-357 before this task's edits) and before Task 2's `test_read_agent_refuses_a_directory_that_is_not_there`.

**Interfaces:**
- Consumes:
  - `check_pair(runs, seed, root)`, `read_agent(...)` and `UNREADABLE_ZIP` from Task 2.
  - `verdict(prefix, root)` with the d2 and phase_d rows from Task 1.
  - `analyse_phase_d2.load(prefix) -> (rows [(seed, medians, blind - sighted)], incomplete [(seed, keys)])` (`analyse_phase_d2.py:75`). It reads the repository's `results/` and has no root argument.
  - `agent_trace.episode(protocol, idx)` (`:62`); `build_cycle(ep)` (`:78`, a fresh cycle per call); `route(cycle)` (`:88`: `climb_start_s` is the cycle's `t` at the first grade above zero, and `grade_pct` has 720 values); `DT = 1.0`.
  - `run_phase_d.result_prefix` and `CLOSED_PREFIX`.
  - `_fake_agent` and `_fake_pair` from Task 2.
- Produces:
  - `agent_trace.episode_row(ep, road) -> {"idx", "seed", "weights" (3 floats), "climb_start_s" (float or None), "grade" (float or None)}`. Pure and JSON-safe. Values:
    - D2 episode 1: 141.0 and 0.13314.
    - D2 episode 2: 281.0 and 0.15025. The table start is 281.95, but `random_road.climb` starts the grade at `int(start_s / dt)`.
    - Every Phase D episode: 180.0 and 0.12. The grade is the road's own grade at that step, `road["grade_pct"][180] / 100`, which is exactly 0.12 on this machine.
    - Both are `None` on a road with no climb.
  - `agent_catalog.table_rows(prefix) -> {"diffs": {seed: round(blind - sighted, 1)}, "incomplete": [seed]}`, from `analyse_phase_d2.load(prefix)`, imported inside the function. Examples: C4 seed 0 is 360.6, C4 seed 5 is -0.3, D2 seed 0 is 221.7, Phase D seed 3 is 387.2. An unknown prefix gives both empty.
  - `agent_catalog.CATALOG_AGENT_KEYS = ("tag", "arm", "status", "reason", "problems", "budget_line", "train_dt", "zip_sha", "scored")`.
  - `agent_catalog.discover(root=ROOT) -> [experiment]`, sorted by runs name, over the `root/runs*` entries that are directories whose name matches `RUNS_NAME`.
    - `experiment = {"runs", "name", "prefix", "protocol", "verdict", "pairs"}`, where `name = CLOSED_PREFIX.get(prefix) or f"{runs} (no name recorded)"`, `protocol` is the single protocol of its runnable pairs (else `None`), and `verdict = verdict(prefix, root)`, whole.
    - `pair = {"seed", "runnable", "reason", "problems", "protocol", "result_file", "table_diff", "agents"}`, sorted by seed. `reason` is `None` when runnable, else `problems[0]`. `protocol` is `None` unless runnable. `table_diff = table_rows(prefix)["diffs"].get(seed)`. `agents` is `[sighted, blind]`, reduced to `CATALOG_AGENT_KEYS`.
    - A seed with one arm directory missing is still listed. The missing arm is `{"tag", "arm", "status": "missing", "reason": "no such directory", "problems": [], other keys None}`. The present arm is `read_agent`'s dict with `scored` set to `None`. The pair's problems are `[f"{arm}_seed{k}: missing -- no such directory"]`.
    - It never raises for an agent or a pair that cannot run, starts no thread, and writes nothing.
  - Test module constants `ALL_RUNS`, `HAVE_ALL_RUNS`, `NO_ALL_RUNS`. Task 4 and Task 6 reuse `HAVE_ALL_RUNS`.

**Measured while prototyping, on this machine:** `discover()` on the real tree takes 0.22 s in a fresh process (two live fingerprints, 50 agents, 48 zip hashes) and 0.12 s after that. Its catalog serialises to 28 078 bytes of JSON, and `git status` stayed clean.

**Four places where this task follows the code rather than the letter of the brief:**
1. `analyse_phase_d.parse` reads with `for line in open(path)`, so under unittest it prints a `ResourceWarning` for each result file (24 in all). The script is not ours to edit, so `table_rows` silences that one category for the call, and the test's direct `load` call does the same.
2. The table test compares all 24 values with the printed "blind-sighted" columns of `C4_RESULT.txt`, `PHASE_D2_RESULT.txt` (first table) and `PHASE_D_RESULT.txt`, not only four spot values.
3. The synthetic test's stray file is named `runs_zzfile`, with no extension. `RUNS_NAME` accepts that name, so the directory filter is what keeps it out. The brief's `runs_file.txt` would not have tested that filter.
4. The real-tree test prints its UNPROVEN line to stderr and calls `skipTest`, rather than using a decorator, so a machine without the runs says so loudly.

- [ ] **Step 1: Write the failing test**

**Edit 3a** (`app/test_agents.py`, lines 22-23: the imports), replace:

```python
import unittest
from unittest import mock
```

with:

```python
import unittest
from unittest import mock
import warnings
```

**Edit 3b** (`app/test_agents.py`, line 43 once Edit 3a is in, 42 in M1), replace:

```python
NO_C4 = "runs_c4/ is not on this machine: the catalog path is UNPROVEN here"
```

with:

```python
NO_C4 = "runs_c4/ is not on this machine: the catalog path is UNPROVEN here"
ALL_RUNS = ("runs", "runs_d2", "runs_c4")
HAVE_ALL_RUNS = all((ROOT / d / f"{arm}_seed{k}" / "final.zip").is_file()
                    for d in ALL_RUNS for arm in ("sighted", "blind") for k in range(8))
NO_ALL_RUNS = ("runs/, runs_d2/ and runs_c4/ are not all complete on this machine: "
               "the catalog is UNPROVEN here")
```

**Edit 3c** (`app/test_agents.py`, lines 110-112 once Edits 3a-3b are in, 104-106 in M1: the end of `test_route_geometry`), replace:

```python
        self.assertEqual(T.route(T.build_cycle(T.episode("phase-d", 1)))["climb_start_s"], 180.0)

    def test_applied_not_commanded(self):
```

with:

```python
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
```

**Edit 3d** (`app/test_agents.py`, lines 379-383 once Edits 3a-3c are in: the end of `test_catalog_synthetic` and the head of Task 2's first test; the three new tests go between them), replace:

```python
            with self.assertRaises(AC.Refused):
                AC.find_pair("runs_zz_blind", 0, root)
        self.assertEqual(threading.active_count(), threads, "the catalog started a thread")

    def test_read_agent_refuses_a_directory_that_is_not_there(self):
```

with:

```python
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
```

- [ ] **Step 2: Run it to verify it fails**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
$PY -m app.test_agents TraceTests.test_episode_row CatalogTests.test_table_rows_are_the_results_tables CatalogTests.test_discover_synthetic CatalogTests.test_catalog_real_tree 2>&1 | grep -E "Error:|^Ran|^FAILED|^OK" | sort | uniq -c
```

Expected: FAIL with "FAILED (errors=11)" (each subtest counts as one), made of:
- `AttributeError: module 'app.agent_trace' has no attribute 'episode_row'` (5);
- `AttributeError: module 'app.agent_catalog' has no attribute 'table_rows'` (4);
- `AttributeError: module 'app.agent_catalog' has no attribute 'discover'` (2).

- [ ] **Step 3: Implement**

**Edit 3e** (`app/agent_trace.py`, line 115: `episode_row` goes right before `_car`), replace:

```python
def _car(env, cmd, obs_in, info):
```

with:

```python
def episode_row(ep, road):
    """The picker's row for one frozen episode, read from the road the env steps.

    `road` is route(build_cycle(ep)). climb_start_s is route()'s: the first
    step whose grade is above zero, 141.0 for D2 episode 1 although the table
    says 141.05, because random_road.climb starts the grade at int(start_s /
    dt). grade is the table's own value for a randomised climb, and for Phase
    D's fixed road the grade at that step (0.12). Both are None on a road with
    no climb. Pure; JSON-safe.
    """
    start = road["climb_start_s"]
    if start is None:
        grade = None
    elif ep["road"] is not None:
        grade = float(ep["road"][1])
    else:
        grade = road["grade_pct"][int(round(start / DT))] / 100.0
    return {"idx": ep["idx"], "seed": ep["seed"], "weights": list(ep["weights"]),
            "climb_start_s": start, "grade": grade}


def _car(env, cmd, obs_in, info):
```

**Edit 3f** (`app/agent_catalog.py`, lines 27-30: the imports), replace:

```python
import threading
import time

import fingerprint as FP
```

with:

```python
import threading
import time
import warnings

import fingerprint as FP
```

**Edit 3g** (`app/agent_catalog.py`, lines 362-363 once Edit 3f is in: the last two lines of `verdict()` and of the file, 280-281 in M1). The catalog section is appended after them because `discover` calls `verdict`. Replace:

```python
    return {"state": "missing" if missing else "found", "lines": lines,
            "missing": missing, "short": short, "cells": cells}
```

with:

```python
    return {"state": "missing" if missing else "found", "lines": lines,
            "missing": missing, "short": short, "cells": cells}


# ---- the catalog: every runs*/ experiment, every pair, for the picker --------
# What the page may show of each agent. 'budget' (the whole dict) stays here.
CATALOG_AGENT_KEYS = ("tag", "arm", "status", "reason", "problems", "budget_line",
                      "train_dt", "zip_sha", "scored")


def table_rows(prefix):
    """{'diffs': {seed: blind - sighted}, 'incomplete': [seed]} for one prefix.

    QUOTED from analyse_phase_d2.load(prefix), the analysis's own reader of
    the repository's results/<prefix>_seed<k>.txt, and rounded to the one
    decimal the printed tables show; nothing is recomputed here. An unknown
    prefix gives both empty. Imported here, not at the top, so that importing
    this module never loads the analysis scripts.

    analyse_phase_d.parse reads with `for line in open(path)`, leaving each
    file for CPython to close as soon as the loop ends; under unittest that
    prints a ResourceWarning per result file. The script is not ours to edit,
    so that one category is silenced for the call.
    """
    import analyse_phase_d2
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ResourceWarning)
        rows, incomplete = analyse_phase_d2.load(prefix)
    return {"diffs": {int(seed): round(float(diff), 1) for seed, _, diff in rows},
            "incomplete": [int(seed) for seed, _ in incomplete]}


def _missing_agent(arm, seed):
    """The half of a pair whose directory is not there, as the catalog lists it."""
    return {"tag": f"{arm}_seed{seed}", "arm": arm, "status": "missing",
            "reason": "no such directory", "problems": [], "budget_line": None,
            "train_dt": None, "zip_sha": None, "scored": None}


def discover(root=ROOT):
    """Every experiment under `root` and every pair in it, for the picker.

    Lists root/runs*/ directories whose name matches RUNS_NAME, sorted by
    name, so a future runs_X appears with no code change; inside each, only
    children that are directories matching AGENT_NAME (_logs, checkpoints and
    files are ignored). EVERY seed is listed: a pair that cannot run carries
    its problems, and a seed with one arm missing lists that arm as
    'missing'. Never raises for an agent or a pair that cannot run; reads
    only; starts no thread.
    """
    root = Path(root)
    out = []
    for d in sorted((p for p in root.glob("runs*") if p.is_dir() and RUNS_NAME.fullmatch(p.name)),
                    key=lambda p: p.name):
        runs = d.name
        prefix = RPD.result_prefix(str(d))
        diffs = table_rows(prefix)["diffs"]
        seeds = set()
        for child in d.iterdir():
            m = AGENT_NAME.fullmatch(child.name)
            if m is not None and child.is_dir():
                seeds.add(int(m.group(2)))
        pairs = []
        for seed in sorted(seeds):
            here = {arm: (d / f"{arm}_seed{seed}").is_dir() for arm in ARMS}
            if all(here.values()):
                pair = check_pair(runs, seed, root)
            else:
                pair = {"protocol": None,
                        "result_file": (root / "results" / f"{prefix}_seed{seed}.txt").is_file(),
                        "agents": [dict(read_agent(runs, f"{arm}_seed{seed}", root), scored=None)
                                   if here[arm] else _missing_agent(arm, seed) for arm in ARMS],
                        "problems": [f"{arm}_seed{seed}: missing -- no such directory"
                                     for arm in ARMS if not here[arm]]}
            problems = pair["problems"]
            pairs.append({
                "seed": seed,
                "runnable": not problems,
                "reason": problems[0] if problems else None,
                "problems": problems,
                "protocol": None if problems else pair["protocol"],
                "result_file": pair["result_file"],
                "table_diff": diffs.get(seed),
                "agents": [{k: a.get(k) for k in CATALOG_AGENT_KEYS} for a in pair["agents"]],
            })
        protocols = {p["protocol"] for p in pairs if p["runnable"]}
        out.append({
            "runs": runs,
            "name": RPD.CLOSED_PREFIX.get(prefix) or f"{runs} (no name recorded)",
            "prefix": prefix,
            "protocol": protocols.pop() if len(protocols) == 1 else None,
            "verdict": verdict(prefix, root),
            "pairs": pairs,
        })
    return out
```

Nothing added here trips `NoWriteTests`: no write-mode `open`, `.write`, `json.dump`, `.save`, `os.remove`, `shutil` or `mkdir` enters the module. `Path.glob("runs*")` ignores case on Windows, so the lowercase-only `RUNS_NAME` is what keeps `Runs_X` out.

- [ ] **Step 4: Run to verify it passes**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory, never the repository}"
$PY -m app.test_agents TraceTests.test_episode_row CatalogTests.test_table_rows_are_the_results_tables CatalogTests.test_discover_synthetic CatalogTests.test_catalog_real_tree 2>&1 | tail -3
$PY -m app.test_agents > "$SCRATCH/m2t3_agents.txt" 2>&1; grep -E "^Ran |^OK|^FAILED|== proof|UNPROVEN" "$SCRATCH/m2t3_agents.txt"; grep -c ResourceWarning "$SCRATCH/m2t3_agents.txt"
git status --short
```

Expected:
- The four named tests give "Ran 4 tests" and "OK", with no ResourceWarning printed.
- The default suite gives "Ran 47 tests", "OK (skipped=1)" and "== proof PROVEN: device cuda, torch 2.11.0+cu128, sb3 2.9.0, sighted damage 501.56474787343603, blind 1229.059247261675, built in N s" (observed between 65 and 89 s). There is no UNPROVEN line, and the ResourceWarning count is 0.
- `git status --short` lists only the three modified files. The suite's own snapshot test also checks that nothing on disk moved.

Read the counts from the run.

- [ ] **Step 5: Commit**

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory, never the repository}"
git rev-parse --abbrev-ref HEAD            # must print JMF-2340550-sep17
git status --short                         # exactly: M app/agent_catalog.py, M app/agent_trace.py, M app/test_agents.py
$PY -m app.test_replay > "$SCRATCH/m2t3_replay.txt" 2>&1; tail -1 "$SCRATCH/m2t3_replay.txt"
git add app/agent_catalog.py app/agent_trace.py app/test_agents.py
$PY verify_docs.py | tail -1
{
  printf '%s\n' "Agent replay M2 Task 3: discover, table_rows and episode_row" "" \
    "agent_catalog.discover lists every runs*/ directory matching RUNS_NAME and every" \
    "seed in it: a pair that cannot run carries its problems (check_pair's), a half" \
    "pair lists its missing arm, and each experiment carries its whole verdict, its" \
    "protocol and each pair's table row. table_rows quotes analyse_phase_d2.load," \
    "rounded to one decimal; the test checks all 24 values against the printed tables." \
    "analyse_phase_d.parse leaves its files to the garbage collector, so table_rows" \
    "silences ResourceWarning for that call only. agent_trace.episode_row gives the" \
    "picker's row per frozen episode from the road the env steps: Phase D climbs" \
    "0.12 at 180 s, D2 episode 2 at 281 s (its table says 281.95). On the real tree:" \
    "Phase D, C4 and Phase D2 with 8 runnable pairs each, 48 ready agents, and" \
    "runs_sixspeed_18sep listed with its one pair refused for no meta.json." "" \
    "\$ python -m app.test_agents (summary)"
  grep -E "^Ran |^OK|== proof" "$SCRATCH/m2t3_agents.txt"
  printf '\n%s\n' "\$ python -m app.test_replay"
  cat "$SCRATCH/m2t3_replay.txt"
  printf '\n%s\n' "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
} > "$SCRATCH/m2t3_msg.txt"
git commit -F "$SCRATCH/m2t3_msg.txt"
git log --oneline -1
```

Expected: "49 of 49 checks pass"; "All 67 checks pass (782 figure mentions scanned in the documents)."; one new commit.

**Left for later in these three files.** This group does not change them, and T10's milestone commit lists them:
- `jsonable` on a 0-d array, and its silent `str(k)` key collisions (`agent_trace.py:41-42`).
- `route()`'s missing length assertion.
- `find_pair` re-hashing both zips on every poll. It now goes through `check_pair` at the same cost; the catalog adds one hash per agent per catalog request, 0.12 s for the whole tree when warm.
- The Task 3 note "GIT_OPTIONAL_LOCKS assertion wording", at M1's `test_agents.py:231-232`.


---

### Task 4: agent_api: GET /api/agents/catalog, Phase D and D2 served by the episode route with the right grade, shared page constants, and fixed-text 500s with no-store

**Files:**
- Modify: `app/agent_api.py:1-2` (module docstring), `:241-243` (after `sb3_available`), `:246-277` (`episode_meta`), `:280-285` (after `_road`), `:288-289` (`install` docstring), `:298-302` (after the `/agents` route), `:304-333` (episode route). These are M1 line numbers. Tasks 1-3 do not touch this file.
- Modify: `app/test_agents.py`: module constants beside `EPISODE_URL` (M1 `:841`), and `RouteTests` (M1 `:852-967`). Tasks 1-3 add lines above both places, so find them by the text quoted below.
- Test: `app/test_agents.py` (`$PY -m app.test_agents RouteTests`)

**Interfaces:**
- Consumes:
  - From Task 3:
    - `agent_catalog.discover(root=ROOT)`, which returns the list of experiments;
    - `agent_trace.episode_row(ep, road)`, which returns `{idx, seed, weights, climb_start_s, grade}`;
    - the test-module constants `HAVE_ALL_RUNS` and `NO_ALL_RUNS`.
  - From Task 1: `agent_catalog.SHORT_VERDICT['phase_d']` and the `phase_d` verdict anchors.
  - From M1:
    - `app/agent_api.py:288 install(app, store=None)` with `answer(body, status)` and `NO_STORE` (`:233`);
    - `:246 episode_meta`, `:280 _road(ep)` (cached by `(protocol, idx)`), `:241 sb3_available()`, `:138 EpisodeStore.needs_sb3`;
    - `app/agent_trace.py:37 jsonable`, `:62 episode`, `:34 PROTOCOL_EPISODES`;
    - `engine_env`: `ACT_LO`, `ACT_HI`, `SLEW`, `PREVIEW_S`, `TURB_PROTECT_K`, `OIL_PROTECT_K`, `neutral_action`;
    - `app/test_agents.py`: `_StubStore` (`needs_sb3` False, records polls), `_client(store)`, `META_KEYS`, `EPISODE_URL`.
- Produces:
  - `agent_api.page_constants()` returns `{'preview_s': list(PREVIEW_S), 'act': {'lo', 'hi', 'slew', 'neutral_phys'}, 'limits': {'turb_c', 'oil_c'}}`, passed through `jsonable`. `neutral_phys` keeps M1's formula.
  - `agent_api.catalog_episodes()` returns `{'d2': [episode_row(ep, _road(ep)) for idx 1..20], 'phase-d': [...]}`.
  - `agent_api.catalog(root=ROOT, sb3=None)` returns `jsonable({'experiments': agent_catalog.discover(root), 'episodes': catalog_episodes(), 'preview_s', 'act', 'limits', 'sb3'})`, with `sb3 = sb3_available() if sb3 is None else bool(sb3)`. It calls `discover` through the module attribute, so tests can patch it.
  - `GET /api/agents/catalog`, defined inside `install()`, GET only:
    - 200: `catalog(sb3=(not store.needs_sb3) or sb3_available())` with `Cache-Control: no-store`;
    - any exception: 500 `{'detail': 'catalog failed: <ExceptionClassName>'}` with no-store.
  - `episode_meta(pair, ep, road, verdict)`: `'episode'` is now `{k: episode_row(ep, road)[k] for k in ('seed', 'weights', 'climb_start_s', 'grade')}`, so Phase D's grade is 0.12, not None. `preview_s`, `act` and `limits` come from `page_constants()`. `META_KEYS` is unchanged, and a d2 meta is byte-identical to M1's.
  - `GET /api/agents/episode`: the 404 / 409 / 503 / 200 answers are unchanged. Any other exception is 500 `{'detail': 'server error: <ExceptionClassName>'}` with no-store, never `str(exc)`. The road and the meta are now built before `store.poll`, so a request that fails never starts a build.

No line in this task carries a backslash-u escape, so the escape trap does not apply. The Arabic text in these files is typed as characters.

- [ ] **Step 1: Write the failing tests (catalog route)**

In `app/test_agents.py`, make three changes.

(a) Replace

```python
EPISODE_URL = "/api/agents/episode?runs=runs_c4&seed=5&ep=1"
```

with

```python
EPISODE_URL = "/api/agents/episode?runs=runs_c4&seed=5&ep=1"
CATALOG_URL = "/api/agents/catalog"
CATALOG_KEYS = {"experiments", "episodes", "preview_s", "act", "limits", "sb3"}
```

(b) In `RouteTests.test_routes_only_under_simulation`, replace its last six lines:

```python
        app, client = _client(_StubStore())
        paths = {r.path: r for r in app.routes if hasattr(r, "methods")}
        self.assertLessEqual({"/agents", "/api/agents/episode"}, set(paths))
        for p in ("/agents", "/api/agents/episode"):
            self.assertEqual(set(paths[p].methods), {"GET"})
        self.assertEqual(client.post(EPISODE_URL).status_code, 405)
```

with:

```python
        from fastapi import FastAPI
        app, client = _client(_StubStore())
        paths = {r.path: r for r in app.routes if hasattr(r, "methods")}
        added = set(paths) - {r.path for r in FastAPI().routes}
        self.assertEqual(added, {"/agents", "/api/agents/episode", "/api/agents/catalog"})
        for p in sorted(added):
            self.assertEqual(set(paths[p].methods), {"GET"}, p)
        self.assertEqual(client.post(EPISODE_URL).status_code, 405)
        self.assertEqual(client.post(CATALOG_URL).status_code, 405)
```

(c) Replace the last three lines of `RouteTests.test_missing_sb3_is_503`:

```python
        stub.needs_sb3 = False               # an injected loader needs no SB3
        with mock.patch.object(API, "sb3_available", lambda: False):
            self.assertEqual(client.get(EPISODE_URL).status_code, 200)
```

with those same three lines followed by two new methods:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
$PY -m app.test_agents RouteTests.test_routes_only_under_simulation RouteTests.test_catalog_route_contract RouteTests.test_catalog_failure_is_500_no_store 2>&1 | grep -E "^(FAIL|ERROR|AssertionError|Ran|OK|FAILED)"
```

Expected: FAIL. The route does not exist yet. This was observed on the prototype:

```
FAIL: test_routes_only_under_simulation (__main__.RouteTests.test_routes_only_under_simulation)
AssertionError: Items in the second set but not the first:
FAIL: test_catalog_route_contract (__main__.RouteTests.test_catalog_route_contract)
AssertionError: 404 != 200 : {"detail":"Not Found"}
FAIL: test_catalog_failure_is_500_no_store (__main__.RouteTests.test_catalog_failure_is_500_no_store)
AssertionError: 404 != 500
Ran 3 tests in 0.7s
FAILED (failures=3)
```

The first failure's next line names `'/api/agents/catalog'`.

- [ ] **Step 3: Implement the catalog (four edits in `app/agent_api.py`)**

(a) Module docstring, lines 1-2. Replace

```python
"""The agent replay page's server side: the model loader, the episode store and
the two routes.
```

with

```python
"""The agent replay page's server side: the model loader, the episode store and
the three routes.
```

(b) Replace

```python
def sb3_available():
    """True when stable-baselines3 can be imported. Looked up, not imported."""
    return importlib.util.find_spec("stable_baselines3") is not None
```

with

```python
def sb3_available():
    """True when stable-baselines3 can be imported. Looked up, not imported."""
    return importlib.util.find_spec("stable_baselines3") is not None


def page_constants():
    """The preview horizons, the action space and the two protection limits,
    JSON-safe: the same three fields in the catalog and in every episode's
    meta, computed in one place. neutral_phys keeps M1's formula,
    engine_env._rescale(neutral_action()) written out: 0 for the three trims,
    1.0 for the fan and the pump."""
    neutral_phys = ACT_LO + (neutral_action() + 1.0) * 0.5 * (ACT_HI - ACT_LO)
    return agent_trace.jsonable({
        "preview_s": list(PREVIEW_S),
        "act": {"lo": ACT_LO, "hi": ACT_HI, "slew": SLEW, "neutral_phys": neutral_phys},
        "limits": {"turb_c": round(TURB_PROTECT_K - 273.15, 1),
                   "oil_c": round(OIL_PROTECT_K - 273.15, 1)},
    })
```

(c) Replace

```python
def _road(ep):
    """The episode's road, from the cycle arrays only (no plant), cached."""
    key = (ep["protocol"], ep["idx"])
    if key not in _ROADS:
        _ROADS[key] = agent_trace.route(agent_trace.build_cycle(ep))
    return _ROADS[key]
```

with

```python
def _road(ep):
    """The episode's road, from the cycle arrays only (no plant), cached."""
    key = (ep["protocol"], ep["idx"])
    if key not in _ROADS:
        _ROADS[key] = agent_trace.route(agent_trace.build_cycle(ep))
    return _ROADS[key]


def catalog_episodes():
    """The picker's row for every frozen episode of both protocols, each read
    from the road the env steps (agent_trace.episode_row): Phase D's twenty
    all climb 12 % at 180 s and differ only in their weights."""
    out = {}
    for protocol in ("d2", "phase-d"):
        rows = []
        for idx in range(1, len(agent_trace.PROTOCOL_EPISODES[protocol]) + 1):
            ep = agent_trace.episode(protocol, idx)
            rows.append(agent_trace.episode_row(ep, _road(ep)))
        out[protocol] = rows
    return out


def catalog(root=ROOT, sb3=None):
    """Everything the picker needs, JSON-safe: every runs*/ directory with its
    pairs, their status and quoted table rows, and its quoted verdict
    (agent_catalog.discover, read-only, no thread); the frozen episodes of
    both protocols; the page's constants; and whether stable-baselines3 can
    be imported (`sb3`, looked up unless the caller says). Computes nothing."""
    body = {"experiments": agent_catalog.discover(root), "episodes": catalog_episodes()}
    body.update(page_constants())
    body["sb3"] = sb3_available() if sb3 is None else bool(sb3)
    return agent_trace.jsonable(body)
```

(d) In `install`, replace

```python
def install(app, store=None):
    """Add GET /agents and GET /api/agents/episode to `app`."""
```

with

```python
def install(app, store=None):
    """Add GET /agents, GET /api/agents/catalog and GET /api/agents/episode to `app`."""
```

Then replace (the end of `agents_page` and the blank line after it)

```python
        return HTMLResponse((STATIC / "agents.html").read_text(encoding="utf-8"),
                            headers=NO_STORE)

```

with

```python
        return HTMLResponse((STATIC / "agents.html").read_text(encoding="utf-8"),
                            headers=NO_STORE)

    @app.get("/api/agents/catalog")
    def agents_catalog():
        """Every experiment, pair and episode the picker offers. Read-only;
        starts nothing. A failure is a fixed text, never str(exc)."""
        try:
            return answer(catalog(sb3=(not store.needs_sb3) or sb3_available()))
        except Exception as exc:
            return answer({"detail": f"catalog failed: {type(exc).__name__}"}, 500)

```

The route lives inside `install()` beside the other two. That keeps test 10's subprocess check true: `app.server` imported without `--simulation` has no `/api/agents*` route and no agent module.

- [ ] **Step 4: Run the tests to verify they pass**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
$PY -m app.test_agents RouteTests 2>&1 | grep -E "\.\.\. |^(FAIL|ERROR|Ran|OK|FAILED)"
```

Expected: `Ran 6 tests`, `OK`, with each of the six tests `... ok`.

If Task 3's `table_rows` leaves them, lines reading `analyse_phase_d.py:64: ResourceWarning: unclosed file ...results\..._seed<k>.txt` may appear under the catalog test. There is one per result file read. `analyse_phase_d.py` reads with a bare `open()` and is never edited. These lines are warnings, not failures.

- [ ] **Step 5: Write the failing tests (Phase D and D2 through the episode route; fixed-text 500)**

In `app/test_agents.py`, replace the last two lines of `test_catalog_failure_is_500_no_store`:

```python
        self.assertEqual(r.json(), {"detail": "catalog failed: OSError"})
        self.assertNotIn("secret", r.text)
```

with those same two lines followed by two new methods:

```python
        self.assertEqual(r.json(), {"detail": "catalog failed: OSError"})
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
```

- [ ] **Step 6: Run the tests to verify they fail**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
$PY -m app.test_agents RouteTests.test_episode_route_serves_phase_d_and_d2 RouteTests.test_episode_route_unexpected_error_is_500_no_store 2>&1 | grep -E "^(FAIL|ERROR|AssertionError|RuntimeError|Ran|OK|FAILED)|'grade'"
```

Expected: FAIL. This was observed on the prototype:

```
ERROR: test_episode_route_unexpected_error_is_500_no_store (__main__.RouteTests.test_episode_route_unexpected_error_is_500_no_store)
RuntimeError: C:\secret\runs_c4\blind_seed5\final.zip
FAIL: test_episode_route_serves_phase_d_and_d2 (__main__.RouteTests.test_episode_route_serves_phase_d_and_d2)
AssertionError: {'see[28 chars]54, 0.012829, 0.297017], 'climb_start_s': 180.0, 'grade': None} != {'see[28 chars]54, 0.012829, 0.297017], 'climb_start_s': 180.0, 'grade': 0.12}
-  'grade': None,
+  'grade': 0.12,
Ran 2 tests in 0.5s
FAILED (failures=1, errors=1)
```

M1's episode route lets the `RuntimeError` escape to FastAPI's default handler, which `TestClient` re-raises. M1's `episode_meta` sends `None` as Phase D's grade.

- [ ] **Step 7: Implement (three edits in `app/agent_api.py`)**

(a) Replace the head of `episode_meta`, through its `"scenario"` line:

```python
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
```

with the following (the function's last four lines, from `"p_baro_kpa"` to `})`, stay as they are):

```python
def episode_meta(pair, ep, road, verdict):
    """Everything the page needs once per episode, JSON-safe. The device and
    the torch/SB3 versions are NOT here: they are known only after the worker
    has loaded the networks, so they travel in every poll response instead.

    `episode` is the picker's own row (agent_trace.episode_row), read from the
    road the env steps, so Phase D's grade is 0.12 rather than None; preview_s,
    act and limits are page_constants(), the catalog's own."""
    agents = pair["agents"]
    row = agent_trace.episode_row(ep, road)
    consts = page_constants()
    return agent_trace.jsonable({
        "experiment": pair["experiment"],
        "runs": pair["runs"],
        "prefix": pair["prefix"],
        "protocol": pair["protocol"],
        "seed": pair["seed"],
        "ep": ep["idx"],
        "episode": {k: row[k] for k in ("seed", "weights", "climb_start_s", "grade")},
        "dt": agent_trace.DT,
        "duration_s": agent_trace.DURATION,
        "steps": agent_trace.STEPS,
        "train_dt": {a["arm"]: a["train_dt"] for a in agents},
        "agents": [{"tag": a["tag"], "arm": a["arm"], "budget_line": a["budget_line"],
                    "zip_sha": a["zip_sha"], "scored": a["scored"]} for a in agents],
        "result_file": pair["result_file"],
        "preview_s": consts["preview_s"],
        "act": consts["act"],
        "limits": consts["limits"],
        "scenario": {"v_kmh": max(road["speed_kmh"]), "t_amb_c": road["t_amb_c"],
```

(b) In `agents_episode`'s docstring, replace

```python
        Every parameter is taken as text and checked here, so a malformed one
        gets this route's own 404 with no-store rather than FastAPI's 422.
        """
```

with

```python
        Every parameter is taken as text and checked here, so a malformed one
        gets this route's own 404 with no-store rather than FastAPI's 422.
        Anything else unexpected is a 500 with a fixed text and no-store, never
        str(exc). The road and the meta are built before the store is polled,
        so a request that fails never starts a build.
        """
```

(c) Replace the route's body after `preempt_on = ...`:

```python
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

with

```python
        try:
            try:
                pair = agent_catalog.find_pair(runs, seed_n)
                episode = agent_trace.episode(pair["protocol"], idx)
            except KeyError:
                return unknown
            except agent_catalog.Refused as refused:
                return answer({"status": "refused", "problems": refused.problems}, 409)
            if store.needs_sb3 and not sb3_available():
                return answer({"detail": "stable-baselines3 is not installed"}, 503)
            first = {}
            if since_n == 0:
                road = _road(episode)
                first = {"road": road,
                         "meta": episode_meta(pair, episode, road,
                                              agent_catalog.verdict(pair["prefix"]))}
            out = store.poll((runs, seed_n, idx), since=since_n, preempt=preempt_on)
            out.update(first)
            return answer(out)
        except Exception as exc:
            return answer({"detail": f"server error: {type(exc).__name__}"}, 500)
```

The validation order is unchanged: patterns, then `find_pair` (404 or 409), then SB3 (503), then the poll. The only order change is that the road and the meta are now built before `store.poll` instead of after it. The design says nothing on this. The responses are the same, and the second subtest of Step 5 pins the new order: with M1's order the store is polled before `episode_meta` fails, and the subtest reads `[(('runs_c4', 5, 1), 0, True)] != []`. This was checked on the prototype.

`neutral_action`, `ACT_LO`, `ACT_HI`, `SLEW`, `PREVIEW_S`, `TURB_PROTECT_K` and `OIL_PROTECT_K` are still imported, now used by `page_constants()` only.

- [ ] **Step 8: Run to verify it passes, then the whole default suite**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory, as the plan header says}"
$PY -m app.test_agents RouteTests StoreTests 2>&1 | grep -E "^(FAIL|ERROR|Ran|OK|FAILED)"
$PY -m app.test_agents > "$SCRATCH/m2_t4_agents.txt" 2>&1; grep -E "== proof|^Ran |^OK|^FAILED|^FAIL:|^ERROR:|load_pair:" "$SCRATCH/m2_t4_agents.txt"
```

Expected from the first command: `Ran 16 tests` and `OK`.

Expected from the second, observed on the prototype, where it read `Ran 44 tests` on M1's suite plus this group's six tests:

```
    == proof PROVEN: device cuda, torch 2.11.0+cu128, sb3 2.9.0, sighted damage 501.56474787343603, blind 1229.059247261675, built in 66 s
Ran N tests in ...s
OK (skipped=1)
  load_pair: device cuda, torch 2.11.0+cu128, SB3 2.9.0
```

N is the count Task 3's commit recorded plus 4. Read it from the run. The one skip is `test_phase_d_pair_full` (`--full` only). The two damages are the M1 figures and must not move: this task does not touch the tracer or the store.

- [ ] **Step 9: Commit**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory, as the plan header says}"
git branch --show-current            # must print JMF-2340550-sep17
git add app/agent_api.py app/test_agents.py
$PY verify_docs.py > "$SCRATCH/m2_t4_verify.txt" 2>&1; tail -1 "$SCRATCH/m2_t4_verify.txt"
$PY -m app.test_replay > "$SCRATCH/m2_t4_replay.txt" 2>&1; tail -1 "$SCRATCH/m2_t4_replay.txt"
cat > "$SCRATCH/m2_t4_msg.txt" <<'EOF'
Agent replay M2 (task 4): GET /api/agents/catalog; Phase D and D2 through the episode route; fixed-text 500s

agent_api.catalog() serves:
- every runs*/ directory (agent_catalog.discover);
- the 20 frozen episodes of each protocol, read from the road the env steps
  (agent_trace.episode_row): Phase D's twenty all climb 12 % at 180 s;
- the page's constants (page_constants(), now shared with episode_meta);
- whether stable-baselines3 can be imported.

The catalog route is added inside install(), so it exists only under
--simulation. It is a GET, it answers with no-store, and any exception
becomes 500 "catalog failed: <Class>", never str(exc).

episode_meta takes its episode from episode_row, so a Phase D episode's
grade is 0.12. M1 sent None, and the SIMULATED badge read a dash.

The episode route now turns anything unexpected into 500 "server error:
<Class>" with no-store (M1 build record, Task 6). It builds the road and the
meta before polling the store, so a request that fails never starts a build.
The 404 / 409 / 503 answers and the d2 meta are unchanged.

EOF
{ echo '$ python -m app.test_agents'; grep -E "== proof|^Ran |^OK|^FAILED|load_pair:" "$SCRATCH/m2_t4_agents.txt"
  echo; echo '$ python -m app.test_replay'; cat "$SCRATCH/m2_t4_replay.txt"
  echo; echo '$ python verify_docs.py'; tail -1 "$SCRATCH/m2_t4_verify.txt"
  echo; echo 'Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>'; } >> "$SCRATCH/m2_t4_msg.txt"
git commit -F "$SCRATCH/m2_t4_msg.txt"
git log -1 --stat | tail -4
```

Expected results:
- `verify_docs.py`'s last line reads `All N checks pass (M figure mentions scanned in the documents).`. Read N and M from the run; at M1 they were 67 and 782.
- `app.test_replay`'s last line reads `49 of 49 checks pass`, measured on this tree on 28 Sep. Read it from the run.
- The commit shows `2 files changed`.

**Notes:**
- **Prototype run, 28 Sep.** Built in `$SCRATCH/plan_proto_m2/py-serve` as a namespace-package portion placed in front of the repository, with Tasks 1-3 prototyped to their skeleton interfaces. Every failure quoted above was observed before the implementation and every pass after it; `git status` stayed clean.
- **Catalog measured on the real tree:**
  - the first GET took 0.26 s, later ones 0.12 s;
  - the response is 27 328 bytes, with four experiments: Phase D, C4 and Phase D2 with 8 runnable pairs each, and `runs_sixspeed_18sep` with 1 pair refused as `sighted_seed0: incompatible -- no meta.json: plant unknown (AUDIT2 C2-1)`;
  - all 40 routes of `catalog_episodes()` build in 0.04 s and are then cached in `_ROADS`.
- **Deviations from the skeleton:**
  - `test_routes_only_under_simulation` now pins the exact set of routes `install()` adds, not a subset. M3 must add its jev routes to that set.
  - `test_episode_route_unexpected_error_is_500_no_store` has a second subtest, with `episode_meta` failing, to pin that a failing request starts no build.
  - `test_catalog_route_contract` also asserts that the catalog never polls the store.
- **The catalog shape** served here is whatever Task 3's `discover` returns; Task 10 records its amendments to design §4.
- **M1 left-for-later item taken:** "Task 6: exceptions other than KeyError/Refused reach FastAPI's default 500 without Cache-Control: no-store".


---

### Task 5: EpisodeStore: a preempt answered from the cache or with an error still cancels the other build (M1 F6), and a superseded build that fails reports nothing

**Files:**
- Modify: `app/agent_api.py:126-132` (`EpisodeStore` docstring), `:153-182` (`poll`), `:215-219` (`_build`'s except clause). These are M1 line numbers, still exact after Task 4, which edits only lines 1-2 and lines below 225.
- Modify: `app/test_agents.py` (`StoreTests`, after `test_preempt_cancels_and_keeps_nothing_partial`, M1 `:662-672`)
- Test: `app/test_agents.py` (`$PY -m app.test_agents StoreTests`)

**Interfaces:**
- Consumes:
  - `app/agent_api.py:153 EpisodeStore.poll(key, since=0, preempt=False)`. In M1: a cache hit answers `'ready'`; an error answers `'error'` once; the active key answers `'loading'` or `'building'`; another active key answers `'busy'`, calling `cancel.set()` only there and only when preempt is set; when idle it starts the `'agent-builder'` thread.
  - `:184 _build(key, cancel)`, which catches `BuildCancelled` silently and turns `(Exception, SystemExit)` into `_errors[key] = BUILD_FAILED.format(kind=...)`.
  - `app/test_agents.py`: `_fake_tracer(n=5, gate=None, fail=None, obs=False, hold=None)`, `_wait_for(store, key, want, limit=10.0, frames=None)`, `_builders()`, `StoreTests.store(**kw)` (`_no_models` loader, `_d2_episode_for`), and `K1`, `K2`, `K3` = `('runs_c4', 5, 1..3)`.
- Produces:
  - `EpisodeStore.poll(key, since=0, preempt=False)`: the return shapes are unchanged. What is new: when `preempt` is true and a build of a DIFFERENT key is active, the cancel event is set under the lock before any branch answers, whether that answer is a cache hit (`'ready'`), an `'error'` or `'busy'`. A preempt for the key already building never cancels it, and a plain poll never cancels.
  - `EpisodeStore._build`: an `Exception` or `SystemExit` raised after the build's own cancel event was set is not recorded in `_errors`. Every other failure is recorded exactly as in M1.

No line in this task carries a backslash-u escape. «احسب» is typed as Arabic characters, as in M1's comments at `agent_api.py:83` and `:129`.

- [ ] **Step 1: Write the failing tests**

In `app/test_agents.py`, replace the last two lines of `StoreTests.test_preempt_cancels_and_keeps_nothing_partial`:

```python
        self.assertEqual(len(r["frames"]), 5)
        self.assertIsNone(s.trace(self.K1), "a cancelled trace was kept")
```

with those same two lines followed by two new methods:

```python
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

        # a plain poll answered from the cache cancels nothing
        gate.clear()
        self.assertEqual(s.poll(self.K1, preempt=True)["status"], "loading")
        self.assertEqual(s.poll(self.K2)["status"], "ready")
        gate.set()
        _wait_for(s, self.K1, "ready")
        settle()

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
```

Why the tests are shaped this way:
- `settle()` joins the worker after each `_wait_for(..., "ready")`. The cache is filled a moment before `finally` clears `_active`, so without the join the next `poll` could answer `'busy'` instead of `'loading'`.
- The `entered` event makes the second test preempt only once the tracer is running. A preempt that arrives during the loader is caught by `_build`'s own check, before the tracer, and would pass on M1 as well.
- The first test also checks behaviourally that a plain poll answered from the cache cancels nothing: K1 is still built and kept.

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
$PY -m app.test_agents StoreTests.test_preempt_answered_from_the_cache_cancels_the_other_build StoreTests.test_a_superseded_build_that_fails_reports_nothing 2>&1 | grep -E "^(FAIL|ERROR|Ran|OK|FAILED)|: the build|: a superseded|^AssertionError" | cut -c1-120
```

Expected: FAIL. This was observed on the prototype:

```
FAIL: test_preempt_answered_from_the_cache_cancels_the_other_build (__main__.StoreTests.test_preempt_answered_from_the_cache_cancels_the_other_build)
AssertionError: Trace(key=('runs_c4', 5, 3), frames=[{'k': 0, 'cars': [None, None]}, {'k': 1, 'cars': [None, None]
FAIL: test_a_superseded_build_that_fails_reports_nothing (__main__.StoreTests.test_a_superseded_build_that_fails_reports_nothing)
AssertionError: 'error' != 'loading'
 : a superseded build's failure was reported
Ran 2 tests in 0.4s
FAILED (failures=2)
```

The first assertion's message ends `is not None : the build nobody watches ran on and was kept`.

The error-branch phase bites on its own as well. With a variant that cancelled only on cache hits, the first test failed at `self.assertIsNone(s.trace(k5), ...)` with `Trace(key=('runs_c4', 5, 5), ...) is not None`. This was checked on the prototype.

- [ ] **Step 3: Implement (four edits in `app/agent_api.py`)**

(a) In the `EpisodeStore` docstring, replace

```python
    Any other key gets 'busy'; only preempt=True cancels, and only the first
    request after «احسب» sends it. A cancelled or partial trace is never kept.
    Errors -- SystemExit included -- are reported once as a fixed message,
    never str(exc), then forgotten so the next poll can retry.
    """
```

with

```python
    Any other key gets 'busy'; only preempt=True cancels, and only the first
    request after «احسب» sends it. A preempt cancels the build of any OTHER
    key, whether its own key is answered from the cache, with an error or
    'busy'; a preempt for the key already building never cancels it. A
    cancelled or partial trace is never kept. Errors -- SystemExit included --
    are reported once as a fixed message, never str(exc), then forgotten so
    the next poll can retry; a superseded build's error is not reported.
    """
```

(b) At the top of `poll`'s locked block, replace

```python
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
```

with

```python
        with self._lock:
            # «احسب» for this key: whatever else is building is no longer
            # wanted, even when this key is answered from the cache or with its
            # error (M1 F6). The key already building is never cancelled.
            if preempt and self._active is not None and self._active != key:
                self._cancel.set()
            if key in self._cache:
                self._cache.move_to_end(key)
```

(c) The top of `poll` now does the busy branch's cancel. Replace

```python
            if self._active is not None:
                if preempt:
                    self._cancel.set()
                runs, seed, idx = self._active
```

with

```python
            if self._active is not None:
                runs, seed, idx = self._active
```

(d) In `_build`, replace

```python
        except (Exception, SystemExit) as exc:
            with self._lock:
                self._errors[key] = BUILD_FAILED.format(kind=type(exc).__name__)
```

with

```python
        except (Exception, SystemExit) as exc:
            with self._lock:
                # Superseded by «احسب» for another episode, then failed: nobody
                # is waiting for this error, and reporting it would spend this
                # key's next «احسب» on a stale message.
                if not cancel.is_set():
                    self._errors[key] = BUILD_FAILED.format(kind=type(exc).__name__)
```

The lock is still never held during slow work. The new rule is one comparison and one `Event.set` inside the existing `with self._lock:` block, and `cancel` is read under the same lock that sets it.

- [ ] **Step 4: Run to verify it passes, three times, then the whole default suite**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory, as the plan header says}"
for i in 1 2 3; do $PY -m app.test_agents StoreTests 2>&1 | grep -E "^(Ran|OK|FAILED|FAIL:|ERROR:)" | tr '\n' ' '; echo; done
$PY -m app.test_agents > "$SCRATCH/m2_t5_agents.txt" 2>&1; grep -E "== proof|^Ran |^OK|^FAILED|^FAIL:|^ERROR:|load_pair:" "$SCRATCH/m2_t5_agents.txt"
```

Expected from the loop, three times: `Ran 10 tests in 1.9s OK`. The prototype read this 15 runs out of 15, and also on M1's store alone, without Task 4.

Expected from the whole default suite: `== proof PROVEN: device cuda, ... sighted damage 501.56474787343603, blind 1229.059247261675, ...`, then `Ran N tests`, where N is Task 4's count plus 2, then `OK (skipped=1)`. The M1 proof tests `test_preempt_cancels_and_keeps_nothing_partial` and `test_one_worker_and_polls_never_cancel` stay green: a preempt for the key already building, and plain polls, still cancel nothing.

- [ ] **Step 5: Commit**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
: "${SCRATCH:?set SCRATCH to this session's scratchpad directory, as the plan header says}"
git branch --show-current            # must print JMF-2340550-sep17
git add app/agent_api.py app/test_agents.py
$PY verify_docs.py > "$SCRATCH/m2_t5_verify.txt" 2>&1; tail -1 "$SCRATCH/m2_t5_verify.txt"
$PY -m app.test_replay > "$SCRATCH/m2_t5_replay.txt" 2>&1; tail -1 "$SCRATCH/m2_t5_replay.txt"
cat > "$SCRATCH/m2_t5_msg.txt" <<'EOF'
Agent replay M2 (task 5): a preempt answered from the cache or with an error still cancels the other build (M1 F6)

EpisodeStore.poll now sets the running build's cancel event whenever a
preempt names a different key, before any branch answers: from the cache
('ready'), with that key's error, or 'busy'. M1 cancelled only on 'busy'.
Going back to an episode already computed therefore left the other build
running unwatched for up to 75 s, and M2's picker makes that common.

A preempt for the key already building still never cancels it, and a plain
poll never cancels anything.

A superseded build that then raises is no longer recorded as an error:
nobody is waiting for it, and M1 spent that key's next «احسب» on the stale
message (M1 build record, Task 5). Every other failure is still reported
once, as a fixed text.

EOF
{ echo '$ python -m app.test_agents'; grep -E "== proof|^Ran |^OK|^FAILED|load_pair:" "$SCRATCH/m2_t5_agents.txt"
  echo; echo '$ python -m app.test_replay'; cat "$SCRATCH/m2_t5_replay.txt"
  echo; echo '$ python verify_docs.py'; tail -1 "$SCRATCH/m2_t5_verify.txt"
  echo; echo 'Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>'; } >> "$SCRATCH/m2_t5_msg.txt"
git commit -F "$SCRATCH/m2_t5_msg.txt"
git log -1 --stat | tail -4
```

Expected results:
- `verify_docs.py`'s last line reads `All N checks pass (M figure mentions scanned in the documents).`. Read both numbers from the run.
- `app.test_replay`'s last line reads `49 of 49 checks pass`. Read it from the run.
- The commit shows `2 files changed`.

**Notes:**
- **Prototype run, 28 Sep,** in `$SCRATCH/plan_proto_m2/py-serve`:
  - Both tests failed on M1's store exactly as quoted and passed after the four edits.
  - They also apply and pass on M1's `agent_api.py` without Task 4. The anchors are disjoint from Task 4's, so the two tasks can land in either order.
  - The whole default suite, with Tasks 1-3 prototyped, read `Ran 44 tests`, `OK (skipped=1)` and `== proof PROVEN: device cuda ... built in 66 s`.
  - `--full ProofTests.test_phase_d_pair_full` through the changed store printed `Phase D == proof PROVEN on cuda` (`Ran 1 test in 365.948s`, including the C4 proof's setUpClass).
- **Deviation from the skeleton's wording:** the first test checks "a plain poll does not cancel" by its effect (K1 is still built and kept) rather than at one instant. It also adds the error branch (k4/k5), because the rule is "before any branch answers".
- **M1 left-for-later items taken:**
  - F6, "a cache hit ignores preempt": M2's switching makes it common;
  - "Task 5: a superseded build that then raises still records _errors[key]".
- **Not changed:** `app/replay.py`'s `ReplayStore` shares the old error policy. It belongs to `/simulation`, which must behave exactly as it does today.


---

### Task 6: fe-pure: agent-picker.mjs (selection, address, option labels, Phase D wording), the M2 strings in both languages, and a catalog fixture generated from the server

**Files:**
- Create: `app/static/sim/agent-picker.mjs`
- Create: `app/static/sim/agent-picker.test.mjs`
- Create: `app/static/sim/agent-catalog.fixture.json`. It is generated by the command in Step 8 and never edited by hand.
- Modify: `app/static/sim/agents-strings.mjs`:
  - `:15-18` (the header comment);
  - `:31` and `:120` (the "picker (read-only in M1)" block comments);
  - `:35` and `:124` (`agents.pick.none`);
  - new blocks after `:109` and after `:198` (after `'agents.profile.km'` in each language).
- Modify: `app/static/sim/agents-strings.test.mjs:157-167`. The M1 bidi test, which is the last 11 lines of the file, is replaced by three tests.
- Modify: `app/test_agents.py`:
  - one helper `_shape` goes just before `class PageTests` (M1 `:1074`);
  - one test goes right after `test_every_car_is_read_through_carOf` (M1 `:1171-1184`).
  - Tasks 1-5 add lines above both places, so find them by the anchor text given in Step 5.
- Test: `app/static/sim/agent-picker.test.mjs`, `app/static/sim/agents-strings.test.mjs`, `app/test_agents.py` (`PageTests.test_catalog_fixture_has_the_server_shape`)

**Interfaces:**
- Consumes:
  - `app/static/sim/i18n.mjs:488 t(lang, key, vars)`. A missing key returns the key itself, and an unfilled `{slot}` stays as written. Also `:35 STRINGS` and `:29 LANGS`.
  - `app/static/sim/agents-strings.mjs:22 AGENT_STRINGS {ar, en}` and `:212 mergeStrings(target, extra)`, merged at import.
    - M1's `'agents.pick.episode_option'` (`:37` / `:126`) is reused as it is.
    - `'agents.pick.none'` (`:35` / `:124`) changes its text here.
    - `'agents.car.blind'` (`:76` / `:165`).
  - `agent_api.catalog(root=ROOT, sb3=None)` from Task 4, with the catalog JSON shape from Tasks 3 and 4:
    - `experiments[].{runs, name, prefix, protocol, verdict{state, lines, missing, short, cells}, pairs[]}`;
    - `pairs[].{seed, runnable, reason, problems, protocol, result_file, table_diff, agents[CATALOG_AGENT_KEYS]}`;
    - `episodes{d2, phase-d}[].{idx, seed, weights, climb_start_s, grade}`;
    - `preview_s`, `act`, `limits`, `sb3`.
  - `app/test_agents.py`:
    - `HAVE_ALL_RUNS` and `NO_ALL_RUNS` (added by Task 3);
    - `json` and `API` (M1 imports);
    - `PageTests.read(rel)`, which asserts `"<rel> does not exist"`.
- Produces:
  - `app/static/sim/agent-picker.mjs` is pure. It imports only `t` from `./i18n.mjs` and has no DOM and no fetch. It exports:
    - `NOTHING = Object.freeze({runs: null, seed: null, ep: null})`
    - `parsePickerQuery(search) -> {runs, seed, ep}`. The patterns are `/^runs[a-z0-9_]*$/`, `/^[0-9]{1,3}$/` and `/^[0-9]{1,2}$/`, with ep in 1..20. Each level is kept only when every level above it was valid.
    - `experimentOf(catalog, runs) -> experiment|null`
    - `selectable(experiment) -> boolean`: true when some pair is runnable.
    - `pairOf(experiment, seed) -> pair|null`
    - `episodesOf(catalog, pair) -> catalog.episodes[pair.protocol]`, or `[]` unless the pair is runnable with a protocol.
    - `resolveSelection(catalog, query) -> {runs, seed, ep}`. It returns NOTHING unless the experiment exists and is selectable. It keeps the seed only when that pair exists and is runnable, and the ep only when it is one of that pair's episodes.
    - `choose(catalog, sel, level ('runs'|'seed'|'ep'), value (the select's string; '' is the placeholder)) -> {runs, seed, ep}`:
      - a new experiment clears seed and ep, and a non-selectable one clears everything;
      - a new pair keeps ep only when the old and new pairs share a protocol;
      - anything invalid clears that level and everything below it.
    - `selectionSearch(sel) -> '' | '?runs=R' | '?runs=R&seed=K' | '?runs=R&seed=K&ep=E'`
    - `computeState(catalog, sel) -> {ok, reason}`. The reason is `null`, `'agents.pick.catalog_loading'`, `'agents.pick.none'`, `'agents.pick.need_pair'`, `'agents.pick.need_episode'` or `'agents.load.no_sb3'`.
    - `formatDiff(v) -> <U+2066> + sign + abs(v).toFixed(1) + <U+2069>`:
      - the sign is `'+'` for values ≥ 0 and for a value that rounds to 0.0;
      - it is `<U+2212>` for negatives;
      - the result is `'—'` (a literal em dash) for null or non-finite values.
    - `experimentOptions(catalog, lang)`, `pairOptions(experiment, lang)` and `episodeOptions(catalog, pair, lang)`. Each returns `[{value, text, disabled}]`, starting with the placeholder `{value: '', text: t(lang, 'agents.pick.choose'), disabled: false}`.
    - `pairQualifier(experiment, lang)` and `sameRoadNote(catalog, experiment, lang)`.
    - `blindLabelKey(protocol) -> 'agents.car.blind_phase_d' | 'agents.car.blind'`
    - `notBlindCite(verdict) -> 'results/PHASE_D_RESULT.txt:33-40'` on the real tree, from the verdict's own `not_blind` line. It falls back to `'results/PHASE_D_RESULT.txt'`.
  - `agents-strings.mjs` gains 17 new keys in both languages:
    - `agents.pick.choose`, `pick.pair_row`, `pick.pair_no_row`, `pick.pair_refused`, `pick.experiment_refused`, `pick.experiment_empty`, `pick.pair_qualifier`, `pick.pair_qualifier_same_road`, `pick.episode_option_same_road`, `pick.same_road_note`, `pick.need_pair`, `pick.need_episode`, `pick.catalog_loading`, `pick.catalog_error`, `car.blind_phase_d`, `seen.blind_phase_d` and `load.stopping`;
    - the texts are exactly the skeleton's, shown in Step 3.
  - `agents-strings.mjs` also changes:
    - `'agents.pick.none'` now reads «لم يُختر شيء بعد: اختر تجربة، ثم زوجاً، ثم حلقة، ثم اضغط احسب» / 'Nothing is selected yet: choose an experiment, then a pair, then an episode, then press Compute';
    - the header comment is updated;
    - `'agents.pick.pair_option'` stays, because M1's `agents.mjs:323` still uses it and Task 7 removes it.
  - `app/static/sim/agent-catalog.fixture.json` is `agent_api.catalog(sb3=True)` as ASCII JSON, with `indent=1, sort_keys=True` and a final newline, 41 217 bytes.
  - `app/test_agents.py` gains the module helper `_shape(x)` and `PageTests.test_catalog_fixture_has_the_server_shape`.
  - Byte counts after this task:

    | file | U+2212 | U+2066 | U+2069 | U+200F | U+2011 | U+202F |
    |---|---|---|---|---|---|---|
    | `agents-strings.mjs` (escapes) | 2 | 1 | 1 | 2 | 2 | 0 |
    | `agent-picker.mjs` (escapes) | 1 | 1 | 1 | 0 | — | 0 |

    The single U+2066 and U+2069 in `agents-strings.mjs` are the header comment's. Neither file carries any of these characters as a literal.

**Where this task follows the code rather than the design or the skeleton (one line each):**
- **Fixture command.** The skeleton generates the fixture with a scratch script. This task runs the same statements as a `$PY -c` one-liner and writes that one-liner into the header of `agent-picker.test.mjs`, so the regeneration command outlives this session. The Python test's failure message points at that header.
- **computeState is stricter.** It checks that ep is one of the pair's twenty episodes, not only that it is non-null. A hand-made `{ep: 21}` therefore reads `'agents.pick.need_episode'`.
- **Phase D's note.** Design §6 writes it as «(180 ث · 12٪)». The picker prints «12.0٪», one decimal like every grade on the page (M1's episode option and the badge). This follows the skeleton.
- **Grade as a fraction.** Design §4's catalog says `grade_pct`. The served catalog carries `grade` as a fraction (Task 3's ruling), and the picker multiplies it by 100.
- **The M1 bidi test.** M1's `agents-strings.test.mjs` test "the bidi control characters in agents.pick.none and agents.device.line are pinned" is replaced, because `pick.none` no longer holds an address to isolate. Its RLM pin on `device.line` is kept in the replacement, 'the bidi control characters are pinned'.
- **Phase D's episode option.** It is given only `{idx, w0, w1, w2}`, because its string has no `{start}` or `{grade}` slot.

**Environment.** Use Git Bash from the repository root in every step. A new shell does not keep variables, so re-export them. Tasks 1-4 must already be committed, because Step 8 calls `agent_api.catalog`. Task 5 is independent.

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
export SCRATCH="${SCRATCH:?set SCRATCH to the session scratchpad}"   # outside the repo, never %TEMP% itself
```

**The escape trap.** The Write, Edit and Bash tools on this machine decode a typed backslash-u escape into the literal character. This task handles it in four ways:
- Every file that must carry an escape is written with `<U+XXXX>` markers.
- `$SCRATCH/t6_escape.py` then turns each marker into the escape text (`chr(92) + 'u' + hex`).
- `$SCRATCH/t6_bytecheck.py` proves the counts.
- Old lines that already hold escapes (in `agents-strings.mjs` and `agents-strings.test.mjs`) are replaced by Python scripts, because the Edit tool cannot match them.

The tests build every special character with `String.fromCodePoint`. Nothing in this task types a backslash-u.

**Prototype record (28 Sep).** The prototype was a scratch copy of `app/static` plus `app/node_modules`, with Tasks 1-4 installed in memory by a stand-in module.
- Steps 1-9 below were replayed in this order on a fresh copy, and every output quoted is from that replay.
- The node glob went from 75 of 75 to 86 of 86.
- The fixture the one-liner wrote was byte-identical to the one the scratch script wrote.
- Six mutants of `agent-picker.mjs` each turned at least one test red. The mutants were: no isolate, the episode kept across protocols, `runs_sixspeed_18sep` not greyed, a default pair chosen for the viewer, no Phase D label, and a no-op control that stayed green.

- [ ] **Step 0: Pre-flight, and the two scratch helpers**

```bash
git branch --show-current                    # JMF-2340550-sep17
git status --short                           # empty: Tasks 1-5 are committed
$PY -c "from app import agent_api as API; c = API.catalog(sb3=True); print(sorted(c), [(e['runs'], len(e['pairs'])) for e in c['experiments']])"
node --test "app/static/sim/*.test.mjs" 2>&1 | tail -8
```

Expected output:
- The `$PY -c` line prints `['act', 'episodes', 'experiments', 'limits', 'preview_s', 'sb3'] [('runs', 8), ('runs_c4', 8), ('runs_d2', 8), ('runs_sixspeed_18sep', 1)]`.
- The node glob prints `ℹ tests 75`, `ℹ pass 75` and `ℹ fail 0`.
- If the `$PY -c` line raises `AttributeError: module 'app.agent_api' has no attribute 'catalog'`, Task 4 is not in the tree. Stop there.

Create `$SCRATCH/t6_escape.py`:

```python
"""Turn every <U+XXXX> marker in the named files into the escape text backslash-u-xxxx.

Scratch script, never committed. The Write/Edit tools on this machine decode a
typed backslash-u escape into the literal (often invisible) character, so the
source is written with markers and this script puts the escapes in: each one
is built as chr(92) + 'u' + the four hex digits, lower case, as M1's sources
write them. It then prints, per file, how many markers it replaced.
"""
import re
import sys

MARKER = re.compile(r"<U[+]([0-9A-F]{4})>")

for path in sys.argv[1:]:
    with open(path, encoding="utf-8", newline="") as fh:
        src = fh.read()
    out, n = MARKER.subn(lambda m: chr(92) + "u" + m.group(1).lower(), src)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(out)
    print(path, n, "markers replaced")
```

Create `$SCRATCH/t6_bytecheck.py`:

```python
"""Byte-check escapes: python t6_bytecheck.py FILE CP=N [CP=N ...].

For each code point CP (hex, e.g. 2212) it asserts that the literal character
occurs 0 times in FILE and that the escape text chr(92) + 'u' + cp occurs N
times, and that no <U+ marker is left. Prints one line per check; exits 1 on
the first failure.
"""
import sys

path, pairs = sys.argv[1], sys.argv[2:]
with open(path, encoding="utf-8", newline="") as fh:
    src = fh.read()
ok = "<U+" not in src
print(path, "markers left:", src.count("<U+"))
for pair in pairs:
    cp, want = pair.split("=")
    literal = src.count(chr(int(cp, 16)))
    escape = src.count(chr(92) + "u" + cp.lower())
    good = literal == 0 and escape == int(want)
    ok = ok and good
    print(f"  U+{cp.upper()}: literal {literal} (want 0), escape {escape} (want {want})",
          "ok" if good else "WRONG")
sys.exit(0 if ok else 1)
```

- [ ] **Step 1: Write the failing test (the strings)**

Create `$SCRATCH/t6_strings_tail.mjs`. These are the three tests that replace M1's last test in `agents-strings.test.mjs`:

```js
// U+2066 / U+2069 isolate a left-to-right run, U+200F is a right-to-left mark,
// U+2212 is the minus sign and U+202F the narrow no-break space. Each is
// invisible or looks like an ASCII character in an editor, so this file builds
// them from their code points, and the source of agents-strings.mjs must carry
// them as escapes, never as literal characters.
const LRI = String.fromCodePoint(0x2066);
const PDI = String.fromCodePoint(0x2069);
const RLM = String.fromCodePoint(0x200f);
const MINUS = String.fromCodePoint(0x2212);
const escapeText = hex => `${String.fromCharCode(92)}u${hex}`;

test('the bidi control characters are pinned', () => {
  // M2: the picker works from the nav link, so agents.pick.none names no
  // address and carries no isolate any more. device.line keeps its RLM, which
  // keeps the Arabic run after the {device} placeholder reading right-to-left.
  const { AGENT_STRINGS } = api();
  for (const lang of LANGS) {
    const none = AGENT_STRINGS[lang]['agents.pick.none'];
    assert.ok(!none.includes(LRI) && !none.includes(PDI), `${lang}: agents.pick.none still isolates an address`);
    assert.ok(!none.includes('?runs='), `${lang}: agents.pick.none still tells the viewer to type an address`);
  }
  assert.ok(AGENT_STRINGS.ar['agents.device.line'].includes(RLM), 'agents.device.line lost its RLM');
});

test('the pair row\'s minus is U+2212, written as an escape', () => {
  const { AGENT_STRINGS } = api();
  for (const lang of LANGS) {
    const row = AGENT_STRINGS[lang]['agents.pick.pair_row'];
    assert.ok(row, `${lang}: agents.pick.pair_row is missing`);
    assert.ok(row.includes(MINUS), `${lang}: the pair row must subtract with U+2212`);
    assert.ok(!row.includes(' - '), `${lang}: an ASCII hyphen is not a minus sign`);
  }
  const src = readFileSync(new URL('./agents-strings.mjs', import.meta.url), 'utf8');
  assert.equal(src.split(escapeText('2212')).length - 1, 2, 'the U+2212 escape must appear once per language');
  for (const hex of ['2066', '2069', '200f', '2011', '2212', '202f']) {
    assert.equal(src.split(String.fromCodePoint(parseInt(hex, 16))).length - 1, 0,
      `a literal U+${hex} in agents-strings.mjs: write the escape`);
  }
});

test('the M2 picker strings keep their clauses', () => {
  const { AGENT_STRINGS } = api();
  const mustSay = {
    'agents.pick.none': { ar: [/لم يُختر شيء/, /اختر تجربة/, /احسب/], en: [/Nothing is selected/, /choose an experiment/, /Compute/] },
    'agents.pick.pair_qualifier': {
      ar: [/فرق وسيطَي 20 حلقة/, /طريقها وأوزانها/, /ليست هذه الحلقة/],
      en: [/medians of 20 episodes/, /own road and weights/, /not this episode/],
    },
    'agents.pick.pair_qualifier_same_road': {
      ar: [/فرق وسيطَي 20 حلقة/, /الطريق نفسه/, /ليست هذه الحلقة/],
      en: [/medians of 20 episodes/, /same road/, /not this episode/],
    },
    'agents.pick.episode_option_same_road': { ar: [/الطريق نفسه/, /الأوزان/], en: [/same road/, /weights/] },
    'agents.pick.same_road_note': { ar: [/الطريق نفسه/, /في الأوزان فقط/], en: [/same road/, /only in their weights/] },
    'agents.pick.pair_refused': { ar: [/لا يمكن تشغيله/], en: [/cannot run/] },
    'agents.pick.experiment_refused': { ar: [/لا يمكن تشغيل أي زوج/], en: [/no pair can run/] },
    'agents.car.blind_phase_d': {
      ar: [/^لا يرى الطريق أمامه/, /قد يحفظه/, /الطريق نفسه في كل حلقة/],
      en: [/^Does not see the road ahead/, /memorised/, /same road in every episode/],
    },
    'agents.seen.blind_phase_d': { ar: [/^لا يرى الطريق أمامه/, /قد يحفظه/], en: [/^Does not see the road ahead/, /memorised/] },
    'agents.load.stopping': { ar: [/يُوقَف/, /السابقة/], en: [/Stopping/, /previous/] },
  };
  for (const [key, langs] of Object.entries(mustSay)) {
    for (const [lang, patterns] of Object.entries(langs)) {
      assert.ok(AGENT_STRINGS[lang][key], `${key} missing in ${lang}`);
      for (const p of patterns) assert.match(AGENT_STRINGS[lang][key], p, `${key} lost a clause in ${lang}`);
    }
  }
  assert.notEqual(AGENT_STRINGS.ar['agents.pick.pair_qualifier'], AGENT_STRINGS.ar['agents.pick.pair_qualifier_same_road']);
  for (const lang of LANGS) {
    const seen = t(lang, 'agents.seen.blind_phase_d', { zeros: '0 · 0 · 0 · 0', cite: 'results/PHASE_D_RESULT.txt:33-40' });
    assert.ok(seen.includes('0 · 0 · 0 · 0') && seen.includes('results/PHASE_D_RESULT.txt:33-40'), `${lang}: ${seen}`);
    assert.doesNotMatch(seen, /[{][a-z0-9_]+[}]/i, `${lang}: an unfilled placeholder in ${seen}`);
  }
});
```

Create `$SCRATCH/t6_splice_strings_test.py`:

```python
"""Replace the last test of agents-strings.test.mjs (the M1 bidi test) with t6_strings_tail.mjs.

Scratch script, never committed. Run from the repository root:
    $PY "$SCRATCH/t6_splice_strings_test.py" "$SCRATCH/t6_strings_tail.mjs"
The M1 test carries escape text in its comment and its asserts, which the Edit
tool cannot match on this machine, so the splice is done here: everything from
the M1 test's first line to the end of the file (11 lines) is replaced.
"""
import sys

PATH = "app/static/sim/agents-strings.test.mjs"
HEAD = "test('the bidi control characters in agents.pick.none and agents.device.line are pinned'"

with open(sys.argv[1], encoding="utf-8", newline="") as fh:
    tail = fh.read()
with open(PATH, encoding="utf-8", newline="") as fh:
    src = fh.read()
assert src.count(HEAD) == 1, "the M1 bidi test is not in the file exactly once"
start = src.index(HEAD)
old = src[start:]
assert old.count("\n") == 11 and old.endswith("});\n"), "the M1 bidi test is not the last 11 lines"
assert chr(92) + "u" not in tail, "the new tests must build their characters from code points"
assert not [c for c in (0x2066, 0x2069, 0x200F, 0x2212, 0x202F, 0x2011) if chr(c) in tail], \
    "a literal bidi or spacing character in the new tests: rewrite that line"
with open(PATH, "w", encoding="utf-8", newline="") as fh:
    fh.write(src[:start] + tail)
print(PATH, "replaced", old.count("\n"), "lines with", tail.count("\n"))
```

Run the splice and byte-check the result. The U+2011 count is M1's two `'H2\\u20112'` lines, which stay:

```bash
$PY "$SCRATCH/t6_splice_strings_test.py" "$SCRATCH/t6_strings_tail.mjs"
$PY "$SCRATCH/t6_bytecheck.py" app/static/sim/agents-strings.test.mjs 2066=0 2069=0 200f=0 2212=0 202f=0 2011=2
```

Expected output:

```
app/static/sim/agents-strings.test.mjs replaced 11 lines with 76
app/static/sim/agents-strings.test.mjs markers left: 0
  U+2066: literal 0 (want 0), escape 0 (want 0) ok
  U+2069: literal 0 (want 0), escape 0 (want 0) ok
  U+200F: literal 0 (want 0), escape 0 (want 0) ok
  U+2212: literal 0 (want 0), escape 0 (want 0) ok
  U+202F: literal 0 (want 0), escape 0 (want 0) ok
  U+2011: literal 0 (want 0), escape 2 (want 2) ok
```

- [ ] **Step 2: Run it to verify it fails**

Run: `node --test app/static/sim/agents-strings.test.mjs 2>&1 | grep -E "^✖ the|^ℹ (tests|pass|fail)|AssertionError"`

Expected: FAIL. `ℹ tests 12`, `ℹ pass 9`, `ℹ fail 3`, with:

```
✖ the bidi control characters are pinned
  AssertionError [ERR_ASSERTION]: ar: agents.pick.none still isolates an address
✖ the pair row's minus is U+2212, written as an escape
  AssertionError [ERR_ASSERTION]: ar: agents.pick.pair_row is missing
✖ the M2 picker strings keep their clauses
  AssertionError [ERR_ASSERTION]: agents.pick.none lost a clause in ar
```

- [ ] **Step 3: Implement (the strings)**

Create `$SCRATCH/t6_strings.py`. Every edit is an exact replacement with a stated count. If any count is wrong, the script writes nothing. Old and new texts carry `<U+XXXX>` markers, and `esc()` turns them into escapes before matching.

```python
"""M2 Task 6: edit app/static/sim/agents-strings.mjs in place.

Scratch script, never committed. Run from the repository root:
    $PY "$SCRATCH/t6_strings.py"
Every edit is an exact replacement that must match the stated number of times,
or nothing is written. Texts carry <U+XXXX> markers where the source must hold
an escape; esc() turns each into chr(92) + 'u' + the hex digits, so no escape
is ever typed through a tool that would decode it.
"""
import re

PATH = "app/static/sim/agents-strings.mjs"


def esc(text):
    return re.sub(r"<U[+]([0-9A-F]{4})>", lambda m: chr(92) + "u" + m.group(1).lower(), text)


HEADER_OLD = """\
// Arabic lines are from design sections 5 and 6
// (docs/superpowers/specs/2026-09-26-agent-replay-design.md), verbatim where the
// design gives them. <U+200F> is a right-to-left mark and <U+2066>...<U+2069> isolates a
// left-to-right run (an address) inside an Arabic line.
"""
HEADER_NEW = """\
// Arabic lines are from design sections 5 and 6
// (docs/superpowers/specs/2026-09-26-agent-replay-design.md), verbatim where the
// design gives them. <U+200F> is a right-to-left mark; <U+2066>...<U+2069> would isolate
// a left-to-right run inside an Arabic line, which is how agent-picker.mjs
// (formatDiff) writes a pair's table number. The pair row subtracts with U+2212,
// written here as its escape; agents-strings.test.mjs pins every one of them.
"""

AR_NONE_OLD = ("    'agents.pick.none': 'لم يُحدَّد زوج ولا حلقة. افتح الصفحة بعنوان مثل "
               "<U+2066>?runs=runs_c4&seed=5&ep=1<U+2069>',\n")
AR_NONE_NEW = "    'agents.pick.none': 'لم يُختر شيء بعد: اختر تجربة، ثم زوجاً، ثم حلقة، ثم اضغط احسب',\n"
EN_NONE_OLD = ("    'agents.pick.none': 'No pair or episode is selected. Open the page with an address "
               "such as ?runs=runs_c4&seed=5&ep=1',\n")
EN_NONE_NEW = ("    'agents.pick.none': 'Nothing is selected yet: choose an experiment, then a pair, "
               "then an episode, then press Compute',\n")

AR_TAIL_OLD = "    'agents.profile.km': '{km} كم',\n"
AR_TAIL_NEW = AR_TAIL_OLD + """
    // --- added in M2: the working picker (agent-picker.mjs), Phase D's blind
    // car, and the line shown while «احسب» stops another computation
    'agents.pick.choose': 'اختر…',
    'agents.pick.pair_row': 'بذرة {seed} · الأعمى <U+2212> المُبصر {diff}',
    'agents.pick.pair_no_row': 'بذرة {seed} · لا صف لهذه البذرة في جدول النتائج',
    'agents.pick.pair_refused': 'بذرة {seed} · لا يمكن تشغيله: {reason}',
    'agents.pick.experiment_refused': '{name} · لا يمكن تشغيل أي زوج: {reason}',
    'agents.pick.experiment_empty': '{name} · لا يوجد فيه أي زوج',
    'agents.pick.pair_qualifier': '(فرق وسيطَي 20 حلقة، لكلٍّ منها طريقها وأوزانها؛ ليست هذه الحلقة)',
    'agents.pick.pair_qualifier_same_road': '(فرق وسيطَي 20 حلقة على الطريق نفسه بأوزان مختلفة؛ ليست هذه الحلقة)',
    'agents.pick.episode_option_same_road': 'حلقة {idx} · الطريق نفسه · الأوزان: عزم {w0} / وقود {w1} / عمر المكوّنات {w2}',
    'agents.pick.same_road_note': 'الطريق نفسه ({start} ث · {grade}٪)؛ تختلف الحلقات في الأوزان فقط',
    'agents.pick.need_pair': 'اختر زوجاً',
    'agents.pick.need_episode': 'اختر حلقة',
    'agents.pick.catalog_loading': 'تحميل قائمة التجارب…',
    'agents.pick.catalog_error': 'تعذّر تحميل قائمة التجارب: {message}',
    'agents.car.blind_phase_d': 'لا يرى الطريق أمامه، لكنه قد يحفظه: الطريق نفسه في كل حلقة',
    'agents.seen.blind_phase_d': 'لا يرى الطريق أمامه: مداخل الاستباق عنده {zeros}؛ لكنه قد يحفظه: الطريق نفسه في كل حلقة ({cite})',
    'agents.load.stopping': 'يُوقَف حساب الحلقة السابقة ({runs} بذرة {seed} حلقة {ep})…',
"""

EN_TAIL_OLD = "    'agents.profile.km': '{km} km',\n"
EN_TAIL_NEW = EN_TAIL_OLD + """
    // --- added in M2: the working picker (agent-picker.mjs), Phase D's blind
    // car, and the line shown while Compute stops another computation
    'agents.pick.choose': 'Choose…',
    'agents.pick.pair_row': 'Seed {seed} · blind <U+2212> sighted {diff}',
    'agents.pick.pair_no_row': 'Seed {seed} · no row for this seed in the results table',
    'agents.pick.pair_refused': 'Seed {seed} · cannot run: {reason}',
    'agents.pick.experiment_refused': '{name} · no pair can run: {reason}',
    'agents.pick.experiment_empty': '{name} · holds no pair',
    'agents.pick.pair_qualifier': '(difference of the medians of 20 episodes, each with its own road and weights; not this episode)',
    'agents.pick.pair_qualifier_same_road': '(difference of the medians of 20 episodes on the same road with different weights; not this episode)',
    'agents.pick.episode_option_same_road': 'Episode {idx} · the same road · weights: torque {w0} / fuel {w1} / component life {w2}',
    'agents.pick.same_road_note': 'The same road ({start} s · {grade} %); the episodes differ only in their weights',
    'agents.pick.need_pair': 'Choose a pair',
    'agents.pick.need_episode': 'Choose an episode',
    'agents.pick.catalog_loading': 'Loading the list of experiments…',
    'agents.pick.catalog_error': 'The list of experiments could not be loaded: {message}',
    'agents.car.blind_phase_d': 'Does not see the road ahead, but may have memorised it: the same road in every episode',
    'agents.seen.blind_phase_d': 'Does not see the road ahead: its preview inputs were {zeros}; but it may have memorised it: the same road in every episode ({cite})',
    'agents.load.stopping': 'Stopping the previous computation ({runs} seed {seed} episode {ep})…',
"""

EDITS = [
    (HEADER_OLD, HEADER_NEW, 1),
    ("    // --- picker (read-only in M1)\n", "    // --- picker\n", 2),
    (AR_NONE_OLD, AR_NONE_NEW, 1),
    (EN_NONE_OLD, EN_NONE_NEW, 1),
    (AR_TAIL_OLD, AR_TAIL_NEW, 1),
    (EN_TAIL_OLD, EN_TAIL_NEW, 1),
]

with open(PATH, encoding="utf-8", newline="") as fh:
    src = fh.read()
for old, new, count in EDITS:
    old, new = esc(old), esc(new)
    found = src.count(old)
    assert found == count, f"expected {count} x, found {found} x: {old[:70]!r}"
    src = src.replace(old, new)
with open(PATH, "w", encoding="utf-8", newline="") as fh:
    fh.write(src)
print(PATH, "edited:", len(EDITS), "replacements")
```

Run it and byte-check the result:

```bash
$PY "$SCRATCH/t6_strings.py"
$PY "$SCRATCH/t6_bytecheck.py" app/static/sim/agents-strings.mjs 2212=2 2066=1 2069=1 200f=2 2011=2 202f=0
git diff --stat app/static/sim/agents-strings.mjs
```

Expected output:

```
app/static/sim/agents-strings.mjs edited: 6 replacements
app/static/sim/agents-strings.mjs markers left: 0
  U+2212: literal 0 (want 0), escape 2 (want 2) ok
  U+2066: literal 0 (want 0), escape 1 (want 1) ok
  U+2069: literal 0 (want 0), escape 1 (want 1) ok
  U+200F: literal 0 (want 0), escape 2 (want 2) ok
  U+2011: literal 0 (want 0), escape 2 (want 2) ok
  U+202F: literal 0 (want 0), escape 0 (want 0) ok
```

The diff touches:
- header lines 17-18, which become 17-20;
- the two block comments;
- the two `pick.none` lines;
- two new 20-line blocks: a blank line, two comment lines and 17 keys.

- [ ] **Step 4: Run to verify it passes (the strings)**

Run: `node --test app/static/sim/agents-strings.test.mjs app/static/sim/agents-page.test.mjs app/static/sim/agents-page-run.test.mjs 2>&1 | grep -E "^ℹ (tests|pass|fail)"`

Expected: `ℹ tests 27`, `ℹ pass 27`, `ℹ fail 0`. That is agents-strings 12, plus 15 in the two M1 page files, which still pass because `agents.pick.pair_option` is kept.

The M1 rules in `agents-strings.test.mjs` now cover the 17 new keys automatically:
- every key is namespaced `agents.`;
- the two languages carry the same keys and the same `{placeholders}`;
- no string says 'preview helps';
- «حاسوب المحرك» always appears with «المنمذَج».

- [ ] **Step 5: Write the failing test (the picker and the fixture)**

Create `app/static/sim/agent-picker.test.mjs` with exactly the content below. It builds its three special characters with `String.fromCodePoint`, so it needs no escapes.

```js
// The picker's pure logic, driven by the catalog the server really serves.
//
// agent-catalog.fixture.json is GENERATED, never edited by hand: it is
// app/agent_api.py catalog(sb3=True) written as ASCII JSON with sorted keys,
// sb3 pinned true so the file does not depend on the machine. It holds the
// repository's four runs directories: runs, runs_c4, runs_d2 and
// runs_sixspeed_18sep. After any change to the catalog's shape
// (app/test_agents.py PageTests.test_catalog_fixture_has_the_server_shape
// fails first), regenerate it from the repository root, in Git Bash:
//   $PY -c "import json; from app import agent_api as API; cat = API.catalog(sb3=True); fh = open('app/static/sim/agent-catalog.fixture.json', 'w', encoding='utf-8', newline=''); json.dump(cat, fh, indent=1, sort_keys=True, ensure_ascii=True, allow_nan=False); fh.write(chr(10)); fh.close(); print([(e['runs'], len(e['pairs'])) for e in cat['experiments']])"
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { t } from './i18n.mjs';
import './agents-strings.mjs';
import * as P from './agent-picker.mjs';

const CATALOG = JSON.parse(readFileSync(new URL('./agent-catalog.fixture.json', import.meta.url), 'utf8'));
const LRI = String.fromCodePoint(0x2066);
const PDI = String.fromCodePoint(0x2069);
const MINUS = String.fromCodePoint(0x2212);
const FULL = { runs: 'runs_c4', seed: 5, ep: 1 };

// A copy of the fixture with one C4 pair refused and one experiment that holds
// no pair: the two cases the real tree does not have today.
function withRefusals() {
  const cat = structuredClone(CATALOG);
  const pair = P.pairOf(P.experimentOf(cat, 'runs_c4'), 3);
  pair.runnable = false;
  pair.protocol = null;
  pair.reason = 'blind_seed3: incomplete -- final.zip is not a readable stable-baselines3 zip';
  pair.problems = [pair.reason];
  cat.experiments.push({
    runs: 'runs_zzempty', name: 'runs_zzempty (no name recorded)', prefix: 'zzempty', protocol: null,
    verdict: { state: 'none', lines: [], missing: [], short: null, cells: [] }, pairs: [],
  });
  return cat;
}

test('the address is read level by level, only by the server\'s own patterns', () => {
  assert.deepEqual(P.parsePickerQuery('?runs=runs_c4&seed=5&ep=1'), FULL);
  assert.deepEqual(P.parsePickerQuery(''), P.NOTHING);
  assert.deepEqual(P.parsePickerQuery(undefined), P.NOTHING);
  assert.deepEqual(P.parsePickerQuery('?runs=runs_c4'), { runs: 'runs_c4', seed: null, ep: null });
  assert.deepEqual(P.parsePickerQuery('?runs=runs_c4&seed=5'), { runs: 'runs_c4', seed: 5, ep: null });
  assert.deepEqual(P.parsePickerQuery('?runs=runs_c4&seed=5&ep=21'), { runs: 'runs_c4', seed: 5, ep: null });
  assert.deepEqual(P.parsePickerQuery('?runs=runs_c4&seed=5&ep=0'), { runs: 'runs_c4', seed: 5, ep: null });
  assert.deepEqual(P.parsePickerQuery('?runs=runs_C4&seed=5&ep=1'), P.NOTHING);
  assert.deepEqual(P.parsePickerQuery('?runs=../x&seed=5&ep=1'), P.NOTHING);
  assert.deepEqual(P.parsePickerQuery('?seed=5&ep=1'), P.NOTHING);
  assert.deepEqual(P.parsePickerQuery('?runs=runs_c4&seed=5abc&ep=1'), { runs: 'runs_c4', seed: null, ep: null });
  assert.deepEqual(P.parsePickerQuery('?runs=runs_c4&ep=1'), { runs: 'runs_c4', seed: null, ep: null });
  assert.ok(Object.isFrozen(P.NOTHING));
});

test('an address selects only what exists and can run; nothing is ever chosen for the viewer', () => {
  assert.deepEqual(P.resolveSelection(CATALOG, P.NOTHING), P.NOTHING);
  assert.deepEqual(P.resolveSelection(CATALOG, FULL), FULL);
  assert.deepEqual(P.resolveSelection(CATALOG, { runs: 'runs', seed: 0, ep: 20 }), { runs: 'runs', seed: 0, ep: 20 });
  assert.deepEqual(P.resolveSelection(CATALOG, { runs: 'runs_zz', seed: 5, ep: 1 }), P.NOTHING);
  assert.deepEqual(P.resolveSelection(CATALOG, { runs: 'runs_c4', seed: 99, ep: 1 }), { runs: 'runs_c4', seed: null, ep: null });
  assert.deepEqual(P.resolveSelection(CATALOG, { runs: 'runs_c4', seed: 5, ep: null }), { runs: 'runs_c4', seed: 5, ep: null });
  assert.deepEqual(P.resolveSelection(CATALOG, { runs: 'runs_sixspeed_18sep', seed: 0, ep: 1 }), P.NOTHING);
  assert.deepEqual(P.resolveSelection(null, FULL), P.NOTHING);
  assert.deepEqual(P.resolveSelection(CATALOG, { runs: 'runs_c4', seed: null, ep: null }), { runs: 'runs_c4', seed: null, ep: null });
  const refused = withRefusals();
  assert.deepEqual(P.resolveSelection(refused, { runs: 'runs_c4', seed: 3, ep: 1 }), { runs: 'runs_c4', seed: null, ep: null });
  assert.deepEqual(P.resolveSelection(refused, { runs: 'runs_zzempty', seed: 0, ep: 1 }), P.NOTHING);
  // Whole addresses, as a reload or a shared link brings them: only a full,
  // runnable one can make «احسب» possible, and none of them computes by itself.
  for (const [search, want] of [
    ['', P.NOTHING],
    ['?runs=runs_sixspeed_18sep&seed=0&ep=1', P.NOTHING],
    ['?runs=runs_zz&seed=5&ep=1', P.NOTHING],
    ['?runs=runs_C4&seed=5&ep=1', P.NOTHING],
    ['?runs=runs_c4&seed=99&ep=1', { runs: 'runs_c4', seed: null, ep: null }],
    ['?runs=runs_c4&seed=5&ep=21', { runs: 'runs_c4', seed: 5, ep: null }],
    ['?runs=runs_c4&seed=5&ep=1', FULL],
  ]) {
    const sel = P.resolveSelection(CATALOG, P.parsePickerQuery(search));
    assert.deepEqual(sel, want, search);
    assert.equal(P.computeState({ ...CATALOG, sb3: true }, sel).ok, search === '?runs=runs_c4&seed=5&ep=1', search);
  }
});

test('choosing clears what depends on it, and keeps the episode only across pairs of one protocol', () => {
  let sel = P.choose(CATALOG, P.NOTHING, 'runs', 'runs_c4');
  assert.deepEqual(sel, { runs: 'runs_c4', seed: null, ep: null });
  sel = P.choose(CATALOG, sel, 'seed', '5');
  assert.deepEqual(sel, { runs: 'runs_c4', seed: 5, ep: null });
  sel = P.choose(CATALOG, sel, 'ep', '7');
  assert.deepEqual(sel, { runs: 'runs_c4', seed: 5, ep: 7 });
  assert.deepEqual(P.choose(CATALOG, sel, 'seed', '3'), { runs: 'runs_c4', seed: 3, ep: 7 });
  assert.deepEqual(P.choose(CATALOG, sel, 'seed', '5'), sel);
  assert.deepEqual(P.choose(CATALOG, sel, 'runs', 'runs_d2'), { runs: 'runs_d2', seed: null, ep: null });
  assert.deepEqual(P.choose(CATALOG, sel, 'runs', ''), P.NOTHING);
  assert.deepEqual(P.choose(CATALOG, sel, 'seed', ''), { runs: 'runs_c4', seed: null, ep: null });
  assert.deepEqual(P.choose(CATALOG, sel, 'seed', '99'), { runs: 'runs_c4', seed: null, ep: null });
  assert.deepEqual(P.choose(CATALOG, sel, 'ep', ''), { runs: 'runs_c4', seed: 5, ep: null });
  assert.deepEqual(P.choose(CATALOG, sel, 'ep', '21'), { runs: 'runs_c4', seed: 5, ep: null });
  assert.deepEqual(P.choose(CATALOG, sel, 'runs', 'runs_sixspeed_18sep'), P.NOTHING);
  assert.deepEqual(P.choose(CATALOG, { runs: 'runs_c4', seed: null, ep: null }, 'ep', '1'), { runs: 'runs_c4', seed: null, ep: null });
  assert.deepEqual(P.choose(null, sel, 'seed', '3'), P.NOTHING);
  // A refused pair cannot be chosen, even by a script that ignores `disabled`.
  assert.deepEqual(P.choose(withRefusals(), sel, 'seed', '3'), { runs: 'runs_c4', seed: null, ep: null });
  // A pair scored on another protocol does not inherit the episode number.
  const mixed = structuredClone(CATALOG);
  P.pairOf(P.experimentOf(mixed, 'runs_c4'), 3).protocol = 'phase-d';
  assert.deepEqual(P.choose(mixed, sel, 'seed', '3'), { runs: 'runs_c4', seed: 3, ep: null });
});

test('the address follows the selection and never says more than was chosen', () => {
  assert.equal(P.selectionSearch(P.NOTHING), '');
  assert.equal(P.selectionSearch(undefined), '');
  assert.equal(P.selectionSearch({ runs: 'runs_c4', seed: null, ep: 4 }), '?runs=runs_c4');
  assert.equal(P.selectionSearch({ runs: 'runs_c4', seed: 5, ep: null }), '?runs=runs_c4&seed=5');
  assert.equal(P.selectionSearch(FULL), '?runs=runs_c4&seed=5&ep=1');
  assert.equal(P.selectionSearch({ runs: 'runs', seed: 0, ep: 20 }), '?runs=runs&seed=0&ep=20');
  for (const sel of [FULL, { runs: 'runs', seed: 0, ep: null }, { runs: 'runs_d2', seed: null, ep: null }, P.NOTHING]) {
    assert.deepEqual(P.resolveSelection(CATALOG, P.parsePickerQuery(P.selectionSearch(sel))), sel);
  }
});

test('«احسب» needs a runnable pair, an episode and stable-baselines3', () => {
  const on = { ...CATALOG, sb3: true };
  assert.deepEqual(P.computeState(null, FULL), { ok: false, reason: 'agents.pick.catalog_loading' });
  assert.deepEqual(P.computeState(on, P.NOTHING), { ok: false, reason: 'agents.pick.none' });
  assert.deepEqual(P.computeState(on, { runs: 'runs_c4', seed: null, ep: null }), { ok: false, reason: 'agents.pick.need_pair' });
  assert.deepEqual(P.computeState(on, { runs: 'runs_c4', seed: 5, ep: null }), { ok: false, reason: 'agents.pick.need_episode' });
  assert.deepEqual(P.computeState(on, { runs: 'runs_c4', seed: 5, ep: 21 }), { ok: false, reason: 'agents.pick.need_episode' });
  assert.deepEqual(P.computeState(on, FULL), { ok: true, reason: null });
  assert.deepEqual(P.computeState({ ...CATALOG, sb3: false }, FULL), { ok: false, reason: 'agents.load.no_sb3' });
  for (const { reason } of [P.computeState(null, FULL), P.computeState(on, P.NOTHING)]) {
    for (const lang of ['ar', 'en']) assert.notEqual(t(lang, reason), reason, `${reason} has no ${lang} string`);
  }
});

test('a table row is signed, one decimal, in a left-to-right isolate', () => {
  assert.equal(P.formatDiff(360.6), `${LRI}+360.6${PDI}`);
  assert.equal(P.formatDiff(-80.3), `${LRI}${MINUS}80.3${PDI}`);
  assert.equal(P.formatDiff(0), `${LRI}+0.0${PDI}`);
  assert.equal(P.formatDiff(-0.04), `${LRI}+0.0${PDI}`);
  assert.equal(P.formatDiff(null), '—');
  assert.equal(P.formatDiff(Number.NaN), '—');
  assert.equal(P.formatDiff('360.6'), '—');
});

test('the three selects list every experiment, every pair and the twenty episodes, in both languages, with no raw key or unfilled slot', () => {
  const refused = withRefusals();
  for (const lang of ['ar', 'en']) {
    const exps = P.experimentOptions(CATALOG, lang);
    assert.deepEqual(exps[0], { value: '', text: t(lang, 'agents.pick.choose'), disabled: false });
    assert.deepEqual(exps.slice(1).map(o => o.value), ['runs', 'runs_c4', 'runs_d2', 'runs_sixspeed_18sep']);
    assert.deepEqual(exps.slice(1).map(o => o.disabled), [false, false, false, true]);
    assert.match(exps[4].text, /no meta\.json/);
    const c4 = P.experimentOf(CATALOG, 'runs_c4');
    assert.equal(exps[2].text, `C4 · ${c4.verdict.short[lang]}`);
    const empty = P.experimentOptions(refused, lang).find(o => o.value === 'runs_zzempty');
    assert.equal(empty.disabled, true);
    assert.equal(empty.text, t(lang, 'agents.pick.experiment_empty', { name: 'runs_zzempty (no name recorded)' }));

    const pairs = P.pairOptions(c4, lang);
    assert.equal(pairs.length, 9);
    assert.deepEqual(pairs.slice(1).map(o => o.value), ['0', '1', '2', '3', '4', '5', '6', '7']);
    assert.ok(pairs[1].text.includes(`${LRI}+360.6${PDI}`), pairs[1].text);
    assert.ok(pairs[2].text.includes(`${LRI}${MINUS}80.3${PDI}`), pairs[2].text);
    const three = P.pairOptions(P.experimentOf(refused, 'runs_c4'), lang)[4];
    assert.equal(three.disabled, true);
    assert.match(three.text, /final\.zip is not a readable/);

    const eps = P.episodeOptions(CATALOG, P.pairOf(c4, 5), lang);
    assert.equal(eps.length, 21);
    assert.deepEqual(eps.slice(1).map(o => o.value), Array.from({ length: 20 }, (_, i) => String(i + 1)));
    for (const bit of ['141', '13.3', '0.69', '0.01', '0.30']) assert.ok(eps[1].text.includes(bit), `${bit} not in ${eps[1].text}`);

    const pd = P.pairOf(P.experimentOf(CATALOG, 'runs'), 0);
    const pdEps = P.episodeOptions(CATALOG, pd, lang);
    assert.equal(pdEps.length, 21);
    CATALOG.episodes.d2.forEach((e, i) => {
      assert.ok(!pdEps[i + 1].text.includes(e.climb_start_s.toFixed(0)), `Phase D episode ${e.idx} names a D2 climb start`);
      assert.ok(pdEps[i + 1].text.includes(lang === 'ar' ? 'الطريق نفسه' : 'same road'), pdEps[i + 1].text);
    });
    assert.deepEqual(P.episodeOptions(CATALOG, null, lang).length, 1);
    assert.deepEqual(P.episodeOptions(refused, P.pairOf(P.experimentOf(refused, 'runs_c4'), 3), lang).length, 1);

    for (const o of [...exps, ...pairs, ...eps, ...pdEps]) {
      assert.doesNotMatch(o.text, /[{][a-z0-9_]+[}]/i, `${lang}: an unfilled placeholder in ${o.text}`);
      assert.ok(!o.text.startsWith('agents.'), `${lang}: a raw key ${o.text}`);
    }
  }
});

test('Phase D reads as one road, and its blind car keeps its caveat, cited where results/ says it', () => {
  const phaseD = P.experimentOf(CATALOG, 'runs');
  const c4 = P.experimentOf(CATALOG, 'runs_c4');
  const six = P.experimentOf(CATALOG, 'runs_sixspeed_18sep');
  for (const lang of ['ar', 'en']) {
    const note = P.sameRoadNote(CATALOG, phaseD, lang);
    assert.ok(note.includes('180') && note.includes('12.0'), note);
    assert.equal(P.sameRoadNote(CATALOG, c4, lang), '');
    assert.equal(P.sameRoadNote(CATALOG, null, lang), '');
    assert.equal(P.pairQualifier(phaseD, lang), t(lang, 'agents.pick.pair_qualifier_same_road'));
    assert.equal(P.pairQualifier(c4, lang), t(lang, 'agents.pick.pair_qualifier'));
    assert.notEqual(P.pairQualifier(phaseD, lang), P.pairQualifier(c4, lang));
    assert.equal(P.pairQualifier(six, lang), '');
  }
  assert.equal(P.blindLabelKey('phase-d'), 'agents.car.blind_phase_d');
  assert.equal(P.blindLabelKey('d2'), 'agents.car.blind');
  assert.equal(P.blindLabelKey(undefined), 'agents.car.blind');
  assert.equal(P.notBlindCite(phaseD.verdict), 'results/PHASE_D_RESULT.txt:33-40');
  assert.equal(P.notBlindCite(c4.verdict), 'results/PHASE_D_RESULT.txt');
  assert.equal(P.notBlindCite(null), 'results/PHASE_D_RESULT.txt');
  assert.match(t('ar', P.blindLabelKey('phase-d')), /قد يحفظه/);
  assert.match(t('en', P.blindLabelKey('phase-d')), /memorised/);
  assert.doesNotMatch(t('ar', P.blindLabelKey('d2')), /قد يحفظه/);
});

test('the fixture is the server\'s catalog', () => {
  assert.deepEqual(CATALOG.experiments.map(e => [e.runs, e.pairs.length]),
    [['runs', 8], ['runs_c4', 8], ['runs_d2', 8], ['runs_sixspeed_18sep', 1]]);
  assert.deepEqual(CATALOG.experiments.map(e => e.protocol), ['phase-d', 'd2', 'd2', null]);
  assert.equal(P.pairOf(P.experimentOf(CATALOG, 'runs_c4'), 0).table_diff, 360.6);
  assert.equal(CATALOG.sb3, true);
  for (const protocol of ['d2', 'phase-d']) {
    assert.deepEqual(CATALOG.episodes[protocol].map(e => e.idx), Array.from({ length: 20 }, (_, i) => i + 1));
  }
  for (const e of CATALOG.episodes['phase-d']) {
    assert.equal(e.climb_start_s, 180);
    assert.equal(e.grade, 0.12);
  }
  assert.deepEqual(CATALOG.episodes.d2[0], {
    climb_start_s: 141, grade: 0.13314, idx: 1, seed: 1000, weights: [0.690154, 0.012829, 0.297017],
  });
});
```

Byte-check that no literal special character crept in: `$PY "$SCRATCH/t6_bytecheck.py" app/static/sim/agent-picker.test.mjs 2066=0 2069=0 2212=0`. All three lines must say `ok`.

Now edit `app/test_agents.py` with the Edit tool. It needs no escapes.

**Edit 1: the helper.** `old_string`:

```python
class PageTests(unittest.TestCase):
    """The /agents page can load every asset, id and module it names.
```

`new_string`:

```python
def _shape(x):
    """A JSON value's structure: every dict key, a list by its first item, 'value' for the rest."""
    if isinstance(x, dict):
        return {k: _shape(v) for k, v in x.items()}
    if isinstance(x, list) and x:
        return [_shape(x[0])]
    return "value"


class PageTests(unittest.TestCase):
    """The /agents page can load every asset, id and module it names.
```

**Edit 2: the test.** `old_string` (unique, the last line of `test_every_car_is_read_through_carOf`):

```python
        self.assertLess(hits[0] - head, 120, "the one read of .cars must be inside carOf")
```

`new_string`:

```python
        self.assertLess(hits[0] - head, 120, "the one read of .cars must be inside carOf")

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
```

Together, the two edits add 26 lines.
- The new lines contain no `.write(`, so `app.test_replay`'s `test_read_only` scan is unaffected. The file's four existing `fh.write(` lines are its only hits, as before.
- They carry no figure, so `verify_docs.py` is unaffected.

- [ ] **Step 6: Run it to verify it fails**

Run: `node --test app/static/sim/agent-picker.test.mjs 2>&1 | grep -E "ERR_MODULE_NOT_FOUND\]|^ℹ (tests|pass|fail)"`

Expected: FAIL. `Error [ERR_MODULE_NOT_FOUND]: Cannot find module '...\app\static\sim\agent-picker.mjs' imported from ...\app\static\sim\agent-picker.test.mjs`, then `ℹ tests 1`, `ℹ pass 0`, `ℹ fail 1`.

Run: `$PY -m app.test_agents PageTests.test_catalog_fixture_has_the_server_shape 2>&1 | tail -4`

Expected: FAIL with `AssertionError: False is not true : sim/agent-catalog.fixture.json does not exist`, then `FAILED (failures=1)`. If it reports `skipped` instead, `runs/`, `runs_d2/` or `runs_c4/` is missing on this machine. Stop and say so, because the catalog is unproven here.

- [ ] **Step 7: Implement (the picker)**

Create `app/static/sim/agent-picker.mjs` with the Write tool, with exactly the content below. The three `<U+XXXX>` markers on lines 29-31 are typed as shown. The script run after the block turns them into escapes.

```js
// The three-select picker of /agents: experiment -> pair -> episode.
//
// PURE: no DOM, no fetch, no physics. It decides what may be chosen and how
// each choice reads, from the catalog the server sent (GET /api/agents/catalog,
// app/agent_api.py catalog()). It never computes a statistic or a difference
// between the two cars: the number on a pair is the results table's own row
// (analyse_phase_d2.load, rounded as the tables print it), and the page labels
// it "not this episode".
//
// HONESTY RULE: nothing is ever chosen for the viewer. With no address the page
// opens with nothing selected; an address selects only what exists in the
// catalog and can run, level by level, and nothing computes until «احسب».
// Every function here takes the catalog as an argument, so a node test can
// drive it from app/static/sim/agent-catalog.fixture.json.
import { t } from './i18n.mjs';

// The server's own patterns (app/agent_catalog.py RUNS_NAME, app/agent_api.py
// SEED_TEXT and EP_TEXT). Lowercase only: on Windows runs_C4 would open the
// runs_c4 directory under a name no verdict is recorded for.
const RUNS_RE = /^runs[a-z0-9_]*$/;
const SEED_RE = /^[0-9]{1,3}$/;
const EP_RE = /^[0-9]{1,2}$/;
const EP_MIN = 1;
const EP_MAX = 20;
const EM_DASH = '—';
// U+2066 LEFT-TO-RIGHT ISOLATE, U+2069 POP DIRECTIONAL ISOLATE and U+2212
// MINUS SIGN, written as escapes: all three are invisible or look like an ASCII
// character in an editor.
const LRI = '<U+2066>';
const PDI = '<U+2069>';
const MINUS = '<U+2212>';

export const NOTHING = Object.freeze({ runs: null, seed: null, ep: null });

/**
 * ?runs=&seed=&ep= read leniently, level by level: a level is kept only when
 * it matches the server's pattern AND every level above it was kept. Episodes
 * are 1..20. Nothing here says that a name exists; resolveSelection does.
 */
export function parsePickerQuery(search) {
  const q = new URLSearchParams(typeof search === 'string' ? search : '');
  const runs = q.get('runs');
  if (runs === null || !RUNS_RE.test(runs)) return { ...NOTHING };
  const seed = q.get('seed');
  if (seed === null || !SEED_RE.test(seed)) return { runs, seed: null, ep: null };
  const ep = q.get('ep');
  const n = ep !== null && EP_RE.test(ep) ? Number(ep) : null;
  return { runs, seed: Number(seed), ep: n !== null && n >= EP_MIN && n <= EP_MAX ? n : null };
}

/** The catalog's experiment for a runs directory name, or null. */
export function experimentOf(catalog, runs) {
  return (catalog?.experiments || []).find(e => e.runs === runs) || null;
}

/** True when at least one of the experiment's pairs may run; the select greys the others. */
export function selectable(experiment) {
  return Boolean(experiment) && (experiment.pairs || []).some(p => p.runnable);
}

/** The experiment's pair for a seed, or null. */
export function pairOf(experiment, seed) {
  return (experiment?.pairs || []).find(p => p.seed === seed) || null;
}

/** The frozen episodes a runnable pair is scored on, by its protocol; [] otherwise. */
export function episodesOf(catalog, pair) {
  if (!pair || !pair.runnable || !pair.protocol) return [];
  return catalog?.episodes?.[pair.protocol] || [];
}

/**
 * What an address may select in this catalog: an experiment only when it
 * exists and some pair of it can run, a seed only when that pair exists and
 * can run, an episode only when it is one of that pair's twenty. Everything
 * else is dropped, so a shared link can never select a refused pair.
 */
export function resolveSelection(catalog, query) {
  const exp = experimentOf(catalog, query?.runs ?? null);
  if (!selectable(exp)) return { ...NOTHING };
  const pair = pairOf(exp, query.seed);
  if (!pair || !pair.runnable) return { runs: exp.runs, seed: null, ep: null };
  const ep = episodesOf(catalog, pair).find(e => e.idx === query.ep);
  return { runs: exp.runs, seed: pair.seed, ep: ep ? ep.idx : null };
}

/**
 * The selection after the viewer changes one select. `level` is 'runs',
 * 'seed' or 'ep'; `value` is the select's string value, '' for the
 * placeholder. A new experiment clears the pair and the episode (one that
 * cannot run clears everything); a new pair keeps the episode only when both
 * pairs are scored on the same protocol, so the same twenty episodes; anything
 * invalid clears its level and every level below it.
 */
export function choose(catalog, sel, level, value) {
  const current = { ...NOTHING, ...sel };
  if (level === 'runs') {
    const exp = experimentOf(catalog, value);
    return selectable(exp) ? { runs: exp.runs, seed: null, ep: null } : { ...NOTHING };
  }
  const exp = experimentOf(catalog, current.runs);
  if (!selectable(exp)) return { ...NOTHING };
  if (level === 'seed') {
    const pair = SEED_RE.test(String(value)) ? pairOf(exp, Number(value)) : null;
    if (!pair || !pair.runnable) return { runs: exp.runs, seed: null, ep: null };
    const old = pairOf(exp, current.seed);
    const keep = current.ep !== null && Boolean(old) && old.protocol === pair.protocol;
    return { runs: exp.runs, seed: pair.seed, ep: keep ? current.ep : null };
  }
  if (level === 'ep') {
    const pair = pairOf(exp, current.seed);
    if (!pair || !pair.runnable) return { runs: exp.runs, seed: null, ep: null };
    const ep = episodesOf(catalog, pair).find(e => String(e.idx) === String(value));
    return { runs: exp.runs, seed: pair.seed, ep: ep ? ep.idx : null };
  }
  return current;
}

/** The address for a selection: '' when nothing is selected, never more than what is. */
export function selectionSearch(sel) {
  if (!sel || sel.runs === null || sel.runs === undefined) return '';
  const q = new URLSearchParams({ runs: sel.runs });
  if (sel.seed !== null && sel.seed !== undefined) {
    q.set('seed', String(sel.seed));
    if (sel.ep !== null && sel.ep !== undefined) q.set('ep', String(sel.ep));
  }
  return `?${q}`;
}

/**
 * Can «احسب» be pressed? {ok, reason}: reason is null when ok, otherwise the
 * i18n key of what is still missing, checked in the order the viewer chooses.
 */
export function computeState(catalog, sel) {
  if (!catalog) return { ok: false, reason: 'agents.pick.catalog_loading' };
  const exp = experimentOf(catalog, sel?.runs ?? null);
  if (!exp) return { ok: false, reason: 'agents.pick.none' };
  const pair = pairOf(exp, sel.seed);
  if (!pair || !pair.runnable) return { ok: false, reason: 'agents.pick.need_pair' };
  if (!episodesOf(catalog, pair).some(e => e.idx === sel.ep)) {
    return { ok: false, reason: 'agents.pick.need_episode' };
  }
  if (!catalog.sb3) return { ok: false, reason: 'agents.load.no_sb3' };
  return { ok: true, reason: null };
}

/**
 * A results-table difference as the tables print it: signed, one decimal,
 * inside a left-to-right isolate. In an Arabic line a bare "+360.6" is drawn
 * "360.6+": the digits after Arabic letters become Arabic numbers (UAX #9 W2)
 * and the leading sign then resolves right-to-left. U+2212 for a negative, as
 * the pause panel writes it; a value that rounds to 0.0 reads +0.0.
 */
export function formatDiff(v) {
  if (typeof v !== 'number' || !Number.isFinite(v)) return EM_DASH;
  const text = Math.abs(v).toFixed(1);
  const sign = v < 0 && text !== '0.0' ? MINUS : '+';
  return `${LRI}${sign}${text}${PDI}`;
}

const fixed = (v, digits) => (typeof v === 'number' && Number.isFinite(v) ? v.toFixed(digits) : EM_DASH);
const percent = g => (typeof g === 'number' && Number.isFinite(g) ? (g * 100).toFixed(1) : EM_DASH);
const placeholder = lang => ({ value: '', text: t(lang, 'agents.pick.choose'), disabled: false });

/**
 * The experiment select: the placeholder, then each experiment as its name
 * and short verdict line. One with no pair, or with no pair that can run, is
 * greyed with the reason of its first pair (runs_sixspeed_18sep: no meta.json).
 */
export function experimentOptions(catalog, lang) {
  return [placeholder(lang), ...(catalog?.experiments || []).map(e => {
    if (!(e.pairs || []).length) {
      return { value: e.runs, text: t(lang, 'agents.pick.experiment_empty', { name: e.name }), disabled: true };
    }
    if (!selectable(e)) {
      return {
        value: e.runs,
        text: t(lang, 'agents.pick.experiment_refused', { name: e.name, reason: e.pairs[0].reason }),
        disabled: true,
      };
    }
    const short = e.verdict?.short?.[lang];
    return { value: e.runs, text: short ? `${e.name} · ${short}` : e.name, disabled: false };
  })];
}

/** The pair select: every pair, its quoted table row; a refused pair greyed with its reason. */
export function pairOptions(experiment, lang) {
  return [placeholder(lang), ...(experiment?.pairs || []).map(p => {
    const value = String(p.seed);
    if (!p.runnable) {
      return { value, text: t(lang, 'agents.pick.pair_refused', { seed: p.seed, reason: p.reason }), disabled: true };
    }
    if (typeof p.table_diff !== 'number') {
      return { value, text: t(lang, 'agents.pick.pair_no_row', { seed: p.seed }), disabled: false };
    }
    return { value, text: t(lang, 'agents.pick.pair_row', { seed: p.seed, diff: formatDiff(p.table_diff) }), disabled: false };
  })];
}

/** The episode select: climb start, grade and the three weights; Phase D says "the same road". */
export function episodeOptions(catalog, pair, lang) {
  const sameRoad = pair?.protocol === 'phase-d';
  return [placeholder(lang), ...episodesOf(catalog, pair).map(e => {
    const weights = { w0: fixed(e.weights?.[0], 2), w1: fixed(e.weights?.[1], 2), w2: fixed(e.weights?.[2], 2) };
    const text = sameRoad
      ? t(lang, 'agents.pick.episode_option_same_road', { idx: e.idx, ...weights })
      : t(lang, 'agents.pick.episode_option', {
        idx: e.idx, start: fixed(e.climb_start_s, 0), grade: percent(e.grade), ...weights,
      });
    return { value: String(e.idx), text, disabled: false };
  })];
}

/**
 * The qualifier under the pair select, by the experiment's protocol: the table
 * row is a difference of medians over twenty episodes, never this episode.
 * Phase D's says "the same road"; '' when the experiment has no protocol.
 */
export function pairQualifier(experiment, lang) {
  if (experiment?.protocol === 'phase-d') return t(lang, 'agents.pick.pair_qualifier_same_road');
  if (experiment?.protocol === 'd2') return t(lang, 'agents.pick.pair_qualifier');
  return '';
}

/** Phase D's one road, said once under the episode select: its climb start and grade. */
export function sameRoadNote(catalog, experiment, lang) {
  if (experiment?.protocol !== 'phase-d') return '';
  const e = catalog?.episodes?.['phase-d']?.[0];
  if (!e) return '';
  return t(lang, 'agents.pick.same_road_note', { start: fixed(e.climb_start_s, 0), grade: percent(e.grade) });
}

/** The blind car's label key: Phase D's blind agent may have memorised its one road. */
export function blindLabelKey(protocol) {
  return protocol === 'phase-d' ? 'agents.car.blind_phase_d' : 'agents.car.blind';
}

/**
 * Where results/ says the blinded arm is not blind, from the verdict's own
 * 'not_blind' quote, so the citation follows the file: results/<file>:<a>-<b>.
 */
export function notBlindCite(verdict) {
  const line = (verdict?.lines || []).find(l => l.key === 'not_blind');
  if (!line) return 'results/PHASE_D_RESULT.txt';
  const n = String(line.text).split('\n').length;
  return `results/${line.file}:${n > 1 ? `${line.line}-${line.line + n - 1}` : line.line}`;
}
```

Put the escapes in, byte-check, and run the test. The test cannot pass yet, because the fixture does not exist:

```bash
$PY "$SCRATCH/t6_escape.py" app/static/sim/agent-picker.mjs
$PY "$SCRATCH/t6_bytecheck.py" app/static/sim/agent-picker.mjs 2066=1 2069=1 2212=1 200f=0 202f=0
node --test app/static/sim/agent-picker.test.mjs 2>&1 | grep -E "ENOENT: no such file|^ℹ (tests|pass|fail)" | head -4
```

Expected output:
- `app/static/sim/agent-picker.mjs 3 markers replaced`.
- `markers left: 0`, and five `ok` lines, the three escape counts being 1.
- `Error: ENOENT: no such file or directory, open '...\app\static\sim\agent-catalog.fixture.json'`, then `ℹ tests 1` and `ℹ fail 1`. The module now loads, and only the fixture is missing.

- [ ] **Step 8: Generate the fixture**

Run the same command the test header carries, from the repository root:

```bash
$PY -c "import json; from app import agent_api as API; cat = API.catalog(sb3=True); fh = open('app/static/sim/agent-catalog.fixture.json', 'w', encoding='utf-8', newline=''); json.dump(cat, fh, indent=1, sort_keys=True, ensure_ascii=True, allow_nan=False); fh.write(chr(10)); fh.close(); print([(e['runs'], len(e['pairs'])) for e in cat['experiments']])"
$PY -c "b = open('app/static/sim/agent-catalog.fixture.json', 'rb').read(); print(len(b), 'bytes, ascii', max(b) < 128, 'CR', b.count(b'\r'), 'ends', b[-3:])"
git status --short
```

Expected output:
- `[('runs', 8), ('runs_c4', 8), ('runs_d2', 8), ('runs_sixspeed_18sep', 1)]`.
- About `41217 bytes, ascii True CR 0 ends b'\n}\n'`, generated in about 0.4 s. The prototype's stand-in wrote 41 217 bytes. Tasks 1-4's real code may differ by a few bytes, so read the number off the run.
- `git status --short` shows exactly `M app/static/sim/agents-strings.mjs`, `M app/static/sim/agents-strings.test.mjs` and `M app/test_agents.py`, plus three `??` lines for `agent-picker.mjs`, `agent-picker.test.mjs` and `agent-catalog.fixture.json`.

The fixture contains:
- no machine path: 0 matches for `Users` in the prototype;
- no timestamp;
- no `fingerprint_taken`.

So regenerating it on an unchanged tree gives the same bytes. It is served at `/static/sim/...` in every server mode, like the rest of `app/static`, and holds only what the catalog route serves.

- [ ] **Step 9: Run to verify it passes**

```bash
node --test app/static/sim/agent-picker.test.mjs 2>&1 | grep -E "^✔|^✖|^ℹ (tests|pass|fail)"
$PY -m app.test_agents PageTests.test_catalog_fixture_has_the_server_shape 2>&1 | tail -3
node --test "app/static/sim/*.test.mjs" > "$SCRATCH/t6_node.txt" 2>&1; tail -8 "$SCRATCH/t6_node.txt"
$PY -m app.test_agents > "$SCRATCH/t6_agents.txt" 2>&1; grep -E "^Ran |^OK|FAILED|== proof" "$SCRATCH/t6_agents.txt"
```

Expected output:
- **The picker file.** Nine `✔` lines: the address test, the resolution test, the choosing test, the address-sync test, the «احسب» test, the table-row test, the three-selects test, the Phase D test and the fixture test. Then `ℹ tests 9`, `ℹ pass 9`, `ℹ fail 0`.
- **The fixture test.** `Ran 1 test in 0.2xs`, then `OK`.
- **The glob.** `ℹ tests 86`, `ℹ pass 86`, `ℹ fail 0`, `ℹ skipped 0`. That is 75 before this task, plus the 9 picker tests, plus 2 net new string tests.
- **The default suite.** `OK (skipped=1)`, with the `== proof PROVEN: device cuda ...` line, in about 2.5 min.
  - `Ran N tests` should be exactly one more than before this task.
  - If Tasks 1-5 landed as planned, N is 54: M1's 38, plus 3 (Task 1), 2 (Task 2), 4 (Task 3), 4 (Task 4), 2 (Task 5) and 1 here.
  - Record the number read, not this one.
- The module's `tearDownModule` snapshot passes, which means the suite changed no file.

- [ ] **Step 10: Commit**

```bash
git branch --show-current                     # JMF-2340550-sep17
git add app/static/sim/agent-picker.mjs app/static/sim/agent-picker.test.mjs app/static/sim/agent-catalog.fixture.json \
        app/static/sim/agents-strings.mjs app/static/sim/agents-strings.test.mjs app/test_agents.py
git status --short                            # the six paths above, staged (A or M); nothing else
$PY verify_docs.py 2>&1 | tail -1
```

Expected: `All 67 checks pass (N figure mentions scanned in the documents).`, the same line as before this task (782 mentions on M1; Tasks 1-5 may have moved N).
- `verify_docs.py` never reads `.mjs` or `.json` files: `SCAN_EXT` at `verify_docs.py:166` is `.md .py .html .js .txt`.
- The lines added to `app/test_agents.py` carry no figure.
- If the line moved, read which file it names before going on.

```bash
$PY -m app.test_replay > "$SCRATCH/t6_replay.txt" 2>&1; tail -1 "$SCRATCH/t6_replay.txt"   # 49 of 49 checks pass (about 95 s)
{
cat <<'EOF'
Agent replay M2 T6: agent-picker.mjs, the M2 strings, and a catalog fixture from the server

app/static/sim/agent-picker.mjs (new, pure: no DOM, no fetch) holds the rules
of the three-select picker:
- parsePickerQuery reads ?runs=&seed=&ep= level by level, by the server's own
  patterns;
- resolveSelection keeps only what exists and can run, and never chooses a pair
  for the viewer;
- choose: a new experiment clears everything below it, and the episode is kept
  only across pairs of one protocol;
- selectionSearch and computeState, and the option lists of the three selects;
- formatDiff prints the results table's own row, signed, to one decimal, in a
  left-to-right isolate;
- pairQualifier and sameRoadNote (Phase D: the same road);
- blindLabelKey and notBlindCite (Phase D's blind car may have memorised its
  road, citing the verdict's own not_blind quote).

app/static/sim/agents-strings.mjs gains 17 keys in both languages.
agents.pick.none no longer asks for a typed address. The pair row's minus is
the U+2212 escape. agents.pick.pair_option stays until Task 7.

app/static/sim/agent-catalog.fixture.json is generated from
agent_api.catalog(sb3=True); the command is in agent-picker.test.mjs's header.
PageTests.test_catalog_fixture_has_the_server_shape fails when the served shape
moves.

agents-strings.test.mjs: M1's pick.none isolate pin is replaced by three tests
(no isolate left, the RLM kept, U+2212 as an escape, the M2 clauses).
EOF
echo
echo '$ node --test "app/static/sim/*.test.mjs"   (summary)'
tail -8 "$SCRATCH/t6_node.txt"
echo
echo '$ python -m app.test_agents'
cat "$SCRATCH/t6_agents.txt"
echo
echo '$ python -m app.test_replay'
cat "$SCRATCH/t6_replay.txt"
echo
echo 'Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>'
} > "$SCRATCH/t6_msg.txt"
git commit -F "$SCRATCH/t6_msg.txt"
git log --oneline -1
git status --short                            # empty
```

*Seen while prototyping. This is for Task 1, not this task.* The skeleton spells the post-hoc anchor as `r'^ *RESULT: INCONCLUSIVE +[[]MEI set AFTER this result'`. Python's `re` then prints `FutureWarning: Possible nested set at position 26` every time `verdict('phase_d')` compiles it. The match is still correct: line 65 was found. Task 1 should write that bracket as an escaped `[` rather than `[[]`, so no warning lands in the test output this task pastes into its commit.


---

### Task 7: fe-page: the working picker -- catalog at boot, three selects, the address kept in sync, the displayed episode cleared on every change, the verdict box from the catalog

**Files:**
- Create: `app/static/sim/agents-page-harness.mjs`
- Create: `app/static/sim/agents-page-nav.test.mjs`
- Create: `app/static/sim/agents-page-address.test.mjs`
- Modify: `app/static/sim/agents-page-run.test.mjs:1-121` (the fake page moves into the harness, and a new first test is added)
- Modify: `app/test_agents.py` (class `PageTests`: one new test, inserted after `test_every_car_is_read_through_carOf`)
- Modify: `app/static/agents.html:76-80` (two captions, and the list of pairs that cannot run)
- Modify: `app/static/sim/agents.css:85` and `:131`
- Modify: `app/static/sim/agents.mjs:13-23, 46-47, 100, 121, 162-163, 173-174, 181, 301-345, 362-363, 400-403, 959, 968-970`
- Modify: `app/static/sim/agent-view.mjs:251-274` (`parseEpisodeQuery` and its three regexes are deleted)
- Modify: `app/static/sim/agent-view.test.mjs:255-267` (its test is deleted)
- Modify: `app/static/sim/agents-strings.mjs`: `agents.pick.pair_option` is removed from both languages, and `agents.pick.refused_summary` and `agents.pick.refused_pair` are added to both
- Test: `app/static/sim/agents-page-nav.test.mjs`, `app/static/sim/agents-page-address.test.mjs`, `app/static/sim/agents-page-run.test.mjs`, `app/test_agents.py` `PageTests.test_the_picker_opens_empty_and_disabled`

**Interfaces:**
- Consumes (Task 6, verbatim):
  - From `agent-picker.mjs`:
    - `NOTHING`, `parsePickerQuery`, `experimentOf`, `pairOf`, `resolveSelection`, `choose`, `selectionSearch`;
    - `computeState`, with reason keys `agents.pick.catalog_loading` / `agents.pick.none` / `agents.pick.need_pair` / `agents.pick.need_episode` / `agents.load.no_sb3`;
    - `experimentOptions`, `pairOptions`, `episodeOptions`;
    - `pairQualifier(experiment, lang)` and `sameRoadNote(catalog, experiment, lang)`.
  - The strings:
    - from Task 6: `agents.pick.choose`, `agents.pick.pair_qualifier`, `agents.pick.pair_qualifier_same_road`, `agents.pick.catalog_error` (`{message}`), `agents.pick.none` (its M2 text), `agents.pick.need_episode` and `agents.pick.catalog_loading`;
    - from M1: `agents.load.no_sb3` and `agents.load.server_down`.
  - `app/static/sim/agent-catalog.fixture.json`, generated from `agent_api.catalog()`. Each pair carries `problems` (Task 3), and each experiment carries its whole `verdict`.
  - `GET /api/agents/catalog` (Task 4), and `GET /api/agents/episode` unchanged.
  - M1's `agents.mjs`: `compute`, `poll`, `handle`, `applyMeta`, `renderVerdict`, `mountChase` (`chaseToken`), `renderPanel`, `renderAll`, `start`.
- Produces:
  - `agents.html`:
    - the three selects keep `disabled` and carry no `<option>`;
    - new `<p id="pick-pair-note" class="pick-caption">` and `<p id="pick-episode-note" class="pick-caption">`;
    - after `#compute`, a new `<details id="pick-refused" class="pick-refused" hidden></details>`.
  - `agents.css`: disabled selects look disabled (`opacity:.55;cursor:not-allowed`). It adds `.pick-caption`, `.pick-reason`, `.pick-warning`, `.pick-refused` and `.refused-pair`.
  - `agents.mjs` state: `catalog`, `bootQuery` and `sel` replace `query`.
  - `agents.mjs` functions: `sameSel`, `currentExperiment()`, `currentPair()`, `currentVerdict()`, `fillSelect(select, options, value)`, `renderRefused()`, `renderPicker()`, `clearEpisode()`, `onPick(level, select)` and `loadCatalog()`. There are three `change` listeners, and `loadCatalog()` is called once, at the end of `start()`.
  - `renderRefused()` lists every pair of every experiment whose `runnable` is false. The list sits under the picker, collapsed. Each pair shows ALL of its `problems` (both arms, and each stored and live field of a plant mismatch) in a `<ul dir="ltr">`.
  - `renderPicker()`: when `catalog.sb3` is false, `#pick-note` starts with `t(currentLang, 'agents.load.no_sb3')` as soon as the catalog arrives. It says so once, however far the selection has got.
  - `loadCatalog()`: when `window.location.search` differs from `selectionSearch(sel)`, the address is replaced with `'/agents' + selectionSearch(sel)`.
  - New keys in `agents-strings.mjs`, ar / en:
    - `agents.pick.refused_summary`: «أزواج لا يمكن تشغيلها ({n})، ولماذا» / 'Pairs that cannot run ({n}), and why';
    - `agents.pick.refused_pair`: «{name} · بذرة {seed}» / '{name} · seed {seed}'.
  - `agents-page-harness.mjs` exports `FakeNode`, `byClass` and `installFakePage({search, ids}) -> {nodes, history, requests, nextRequest(ms = 3000), reply(req, body, status = 200), fail(req, error), settle, seekTo(time), change(node, value)}`.

**Where this task follows the code rather than the skeleton**, one line each:
- `draw()` returns before the pause panel when there is no road (`agents.mjs:851`). So `clearEpisode()` calls `renderPanel(-1)` itself, which puts the panel back to «—».
- `loadCatalog()` compares the address as TEXT with `selectionSearch(sel)`. It does not compare the parsed query with the selection: `parsePickerQuery` has already dropped a malformed level (`ep=21`, `runs_C4`, `seed=5abc`), so comparing selections would leave such an address untouched. `agents-page-address.test.mjs` pins this. From the nav link, and from a full valid address, the history stays empty.
- Two spec gaps are closed here, beyond the skeleton's Task 7 interface, because both concern what the page shows. Task 10 records both as amendments.
  - Design §8 says refused agents are "listed and disabled with reason and fields". A greyed option has room only for `problems[0]`, so `#pick-refused` lists every problem.
  - Design §4 "Runnability" says a missing stable-baselines3 makes every pair "cannot run". The page says so once, under the picker, from the moment the catalog arrives, instead of only after three choices. The pairs stay selectable, so their verdicts and table rows can still be read.
- The sb3 line never appears twice, whatever order Task 6's `computeState` checks `sb3` in: the reason line is skipped when the reason is `agents.load.no_sb3`.
- A third gap in the same list is left to Tasks 3 and 6: the results table's `incomplete` seeds (design §4 "Table rows"). Task 3's `discover` does not put them in the catalog.
- `nextRequest` in the harness times out after 3000 ms, so a page that never sends a request fails its test instead of hanging the whole file.
- `fillSelect` and `renderRefused` keep their drawn signature in one `WeakMap` (`drawn`), never in a `data-` attribute. That way an open list does not close on a redraw.
- The nav test's fake DOM also holds `verdict-scored`, `lane-blind-label`, `seen-blind`, `lane-stopped` and `sim-badge`, which Task 8 reads.
- The nav test changes a copy of the fixture: `runs_d2`'s verdict becomes `missing`, and a `runs_zz` experiment with a `none` verdict is appended. On the real tree every selectable experiment is `found`, so without this no test would render the box in those states.
- One Python PageTests test is added. The skeleton lists `app/test_agents.py` as modified without naming a test.

Every Bash call starts a fresh shell, so every command block in this task begins with the block below. Fill in `SCRATCH` once, with this session's scratchpad directory written in `/c/...` form; never use `%TEMP%` itself.

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe
export PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0
export SCRATCH='/c/Users/admin/AppData/Local/Temp/claude/<project>/<session>/scratchpad'
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
```

- [ ] **Step 1: Write the failing tests**

**1a.** Create `app/static/sim/agents-page-harness.mjs` with the Write tool. It holds no backslash-u escape.

```js
// A fake page for running agents.mjs under node:test: a DOM holding only the
// ids a test names, a window whose address the test chooses, a history that
// records every replaceState, and a fetch whose every request waits until the
// test answers it, so the order of events is the test's.
//
// NOT a *.test.mjs file, so the glob "app/static/sim/*.test.mjs" never runs it
// on its own. Each test file that imports it owns its own process (node --test
// runs every file in one), and agents.mjs boots once, on import, in it:
//
//   const h = installFakePage({ search: '', ids: ['compute', ...] });
//   await import('./agents.mjs');
//
// Every id not listed is null, which agents.mjs tolerates. Do NOT list
// 'profile' or 'chase' unless the test is about them: FakeNode.querySelector
// returns null, and drawProfile would then fail on the car marker.
import { registerHooks } from 'node:module';

// The page loads its chase view with import('./agent-scene.mjs'), which needs
// Three.js and WebGL. In this process that one import resolves to a stand-in,
// whose behaviour each test sets through globalThis.chaseFake. The chase view
// is mounted only where a test puts a #chase node in the fake DOM.
const FAKE_SCENE = `data:text/javascript,${encodeURIComponent(`
export function createChaseScene() {
  const fake = globalThis.chaseFake;
  if (fake.fail) throw new Error(fake.fail);
  const scene = { disposed: false, update() {}, setTheme() {}, dispose() { scene.disposed = true; } };
  fake.scenes.push(scene);
  if (fake.onCreate) fake.onCreate();
  return scene;
}`)}`;

export class FakeNode {
  constructor(tag) {
    this.tagName = tag;
    this.children = [];
    this.own = '';
    this.hidden = false;
    this.disabled = false;
    this.className = '';
    this.value = '';
    this.dataset = {};
    this.style = {};
    this.attrs = {};
    this.listeners = {};
  }
  get textContent() { return this.own + this.children.map(c => c.textContent).join(''); }
  set textContent(v) { this.own = String(v); this.children = []; }
  appendChild(node) { this.children.push(node); return node; }
  append(...nodes) { this.children.push(...nodes); }
  setAttribute(name, value) { this.attrs[name] = String(value); }
  getAttribute(name) { return name in this.attrs ? this.attrs[name] : null; }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  fire(type) { for (const fn of this.listeners[type] || []) fn(); }
  click() { this.fire('click'); }
  querySelector() { return null; }
  querySelectorAll() { return []; }
}

// Every node under `node` whose class list holds `name`.
export function byClass(node, name, out = []) {
  if (String(node.className).split(' ').includes(name)) out.push(node);
  for (const child of node.children) byClass(child, name, out);
  return out;
}

const SELECTS = new Set(['pick-experiment', 'pick-pair', 'pick-episode', 'rate']);

/**
 * Install the fake page. `search` is window.location.search; `ids` are the
 * elements that exist. Returns the handles a test drives it with.
 */
export function installFakePage({ search = '', ids = [] } = {}) {
  registerHooks({
    resolve(specifier, context, next) {
      if (specifier === './agent-scene.mjs' && String(context.parentURL).endsWith('/agents.mjs')) {
        return { url: FAKE_SCENE, shortCircuit: true };
      }
      return next(specifier, context);
    },
  });
  globalThis.chaseFake = { fail: null, scenes: [], onCreate: null };

  const nodes = Object.fromEntries(ids.map(id => [id, new FakeNode(SELECTS.has(id) ? 'select' : 'div')]));
  const history = [];
  globalThis.document = {
    documentElement: new FakeNode('html'),
    activeElement: null,
    getElementById: id => nodes[id] || null,
    createElement: tag => new FakeNode(tag),
    querySelector: () => null,
    querySelectorAll: () => [],
  };
  globalThis.window = {
    location: { search },
    matchMedia: () => ({ matches: false }),
    history: { replaceState: (data, title, url) => { history.push(String(url)); } },
  };
  globalThis.getComputedStyle = () => ({ getPropertyValue: () => '' });
  globalThis.requestAnimationFrame = () => 0;

  // Each request waits until the test answers it, so the order is the test's.
  const requests = [];
  let arrived = null;
  globalThis.fetch = url => new Promise((resolve, reject) => {
    requests.push({ url: String(url), resolve, reject });
    if (arrived) { arrived(); arrived = null; }
  });
  // A request the page never sends fails the test after `ms` instead of
  // hanging the whole file.
  async function nextRequest(ms = 3000) {
    const deadline = Date.now() + ms;
    while (!requests.length) {
      const left = deadline - Date.now();
      if (left <= 0) throw new Error(`no request arrived within ${ms} ms`);
      await new Promise(resolve => {
        const timer = setTimeout(resolve, left);
        arrived = () => { clearTimeout(timer); resolve(); };
      });
    }
    return requests.shift();
  }
  const reply = (req, body, status = 200) => req.resolve({ status, json: async () => body });
  const fail = (req, error = new TypeError('Failed to fetch')) => req.reject(error);
  const settle = () => new Promise(resolve => setTimeout(resolve, 20));
  function seekTo(time) {
    nodes.seek.value = String(time);
    nodes.seek.fire('input');
  }
  // What a viewer's choice in a <select> does: the value changes, then 'change'.
  function change(node, value) {
    node.value = String(value);
    node.fire('change');
  }
  return { nodes, history, requests, nextRequest, reply, fail, settle, seekTo, change };
}
```

**1b.** Create `app/static/sim/agents-page-nav.test.mjs` with the Write tool. It holds no backslash-u escape.

```js
// The /agents page opened from its own nav link (no address), RUNNING against
// a fake DOM and a fake server (agents-page-harness.mjs). Jad found on 28 Sep
// that M1's page could not be used from the link at all: nothing selected and
// three read-only lists. These tests drive the picker the way a viewer does.
//
// This file owns its own process (node --test runs each file in one), and
// agents.mjs boots once, on import. The tests run IN ORDER and each says the
// selection it starts from: the page's state carries from one to the next.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { STRINGS } from './i18n.mjs';
import { installFakePage, byClass } from './agents-page-harness.mjs';

// Generated from the server's own catalog (agent_api.catalog). This file
// changes two things in a copy, both shaped as agent_catalog returns them, so
// the page meets a verdict that is not found: runs_d2's verdict is 'missing'
// (as if results/PHASE_D2_RESULT.txt were gone), and a runs_zz directory with
// no recorded verdict ('none') holds one runnable pair and one refused by a
// plant mismatch. sb3 is pinned true so nothing depends on the machine.
const FIXTURE = JSON.parse(readFileSync(new URL('./agent-catalog.fixture.json', import.meta.url), 'utf8'));
const MISSING = {
  ar: 'لم يُعثر على سطر الحكم في results/PHASE_D2_RESULT.txt: لا تقرأ هؤلاء الوكلاء بدونه',
  en: 'verdict line not found in results/PHASE_D2_RESULT.txt: do not read these agents without it',
};
const NONE = {
  ar: 'لا يوجد حكم مسجَّل مسبقاً لهذه التجربة في results/. ما تعرضه هذه الصفحة ليس نتيجة.',
  en: 'No preregistered verdict for this experiment in results/. Nothing on this page is a result.',
};
const CATALOG = structuredClone({ ...FIXTURE, sb3: true });
const D2 = CATALOG.experiments.find(e => e.runs === 'runs_d2');
D2.verdict = { state: 'missing', lines: [], missing: ['PHASE_D2_RESULT.txt'], short: MISSING, cells: [] };
const MISMATCH = [
  'blind_seed9: incompatible -- plant mismatch: plant_sha',
  "blind_seed9: plant_sha: stored 'aaaa' live 'bbbb'",
];
CATALOG.experiments.push({
  runs: 'runs_zz', name: 'runs_zz (no name recorded)', prefix: 'zz', protocol: 'd2',
  verdict: { state: 'none', lines: [], missing: [], short: NONE, cells: [] },
  pairs: [
    structuredClone(D2.pairs[0]),
    { ...structuredClone(D2.pairs[1]), seed: 9, runnable: false, reason: MISMATCH[0], problems: MISMATCH,
      protocol: null, table_diff: null },
  ],
});
const C4 = CATALOG.experiments.find(e => e.runs === 'runs_c4');

const h = installFakePage({
  search: '',
  ids: ['compute', 'error', 'pick-experiment', 'pick-pair', 'pick-episode', 'pick-note', 'pick-pair-note',
    'pick-episode-note', 'pick-refused', 'verdict', 'verdict-short', 'verdict-cells', 'strip-verdict',
    'verdict-scored', 'scene-prompt', 'pause-heading', 'loading', 'load-title', 'lane-blind-label', 'seen-blind',
    'lane-stopped', 'lang-toggle', 'seek', 'sim-badge'],
});
const { nodes } = h;
await import('./agents.mjs');

const AR = key => STRINGS.ar[key];
const options = select => select.children.map(o => ({ value: o.value, text: o.textContent, disabled: o.disabled }));
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));

// One meta and one road for runs_c4 seed 5 episode 1, shaped as
// agent_api.episode_meta and agent_trace.route send them.
const c4Pair = seed => C4.pairs.find(p => p.seed === seed);
const META = {
  experiment: 'C4', runs: 'runs_c4', prefix: 'c4', protocol: 'd2', seed: 5, ep: 1,
  episode: { ...CATALOG.episodes.d2[0] }, dt: 1, steps: 719,
  train_dt: { sighted: 0.2, blind: 0.2 }, agents: c4Pair(5).agents, result_file: true,
  preview_s: CATALOG.preview_s, act: CATALOG.act, limits: CATALOG.limits,
  scenario: { v_kmh: 130, t_amb_c: 42, p_baro_kpa: 101.3 }, verdict: C4.verdict,
};
const ROAD = {
  rise_m: 2755, p_baro_kpa: 101.3, t_amb_c: 42, climb_start_s: null,
  grade_pct: [0, 0, 0, 0], s_m: [0, 0, 20, 40], x_m: [0, 0, 20, 40], z_m: [0, 0, 0, 0],
};
const car = (over = {}) => ({
  cmd: [0, 0, 0, 1, 1], act: [0, 0, 0, 1, 1], held: [false, false, false, false, false],
  preview_pct: [0, 0, 12, 12], map_kpa: 180, turb_c: 700, torque_nm: 300, torque_req_nm: 310, damage: 1.5,
  ...over,
});

test('from the nav link the page selects nothing, computes nothing, and says what to choose', async () => {
  const first = await h.nextRequest();
  assert.equal(first.url, '/api/agents/catalog', 'the page\'s only request at boot is the catalog');
  assert.equal(nodes['pick-experiment'].disabled, true, 'nothing can be chosen before the catalog arrives');
  assert.equal(nodes['pick-note'].textContent, AR('agents.pick.catalog_loading'));
  h.reply(first, CATALOG);
  await h.settle();

  const exp = options(nodes['pick-experiment']);
  assert.deepEqual(exp.map(o => o.value), ['', 'runs', 'runs_c4', 'runs_d2', 'runs_sixspeed_18sep', 'runs_zz']);
  assert.equal(exp[0].text, AR('agents.pick.choose'));
  assert.equal(nodes['pick-experiment'].value, '', 'no experiment is chosen for the viewer');
  assert.equal(nodes['pick-experiment'].disabled, false);
  const sixspeed = exp.find(o => o.value === 'runs_sixspeed_18sep');
  assert.equal(sixspeed.disabled, true, 'a directory with no runnable pair is greyed');
  assert.match(sixspeed.text, /no meta\.json/, 'and says why');
  assert.equal(nodes['pick-pair'].disabled, true);
  assert.equal(nodes['pick-episode'].disabled, true);
  assert.equal(nodes.compute.disabled, true);
  assert.equal(nodes['pick-note'].textContent, AR('agents.pick.none'));
  assert.equal(nodes['scene-prompt'].hidden, false);
  assert.equal(nodes['verdict-short'].textContent, '—', 'no verdict before an experiment is chosen');
  await wait(450);
  assert.equal(h.requests.length, 0, 'nothing computes');
  assert.deepEqual(h.history, [], 'the address is left as it was');
});

// Starts from: nothing selected.
test('every pair that cannot run is listed with every problem the server found, both arms and each field', () => {
  const box = nodes['pick-refused'];
  assert.equal(box.hidden, false);
  const summary = box.children.find(c => c.tagName === 'summary');
  assert.equal(summary.textContent, AR('agents.pick.refused_summary').replace('{n}', '2'));
  const items = byClass(box, 'refused-pair').map(item => item.textContent);
  assert.equal(items.length, 2, 'runs_sixspeed_18sep seed 0 and runs_zz seed 9');
  assert.ok(items[0].includes('sighted_seed0: incompatible -- no meta.json'), items[0]);
  assert.ok(items[0].includes('blind_seed0: incompatible -- no meta.json'), 'the second arm too, which no option shows');
  assert.ok(items[1].includes("plant_sha: stored 'aaaa' live 'bbbb'"), 'and each stored and live field');
  const lists = byClass(box, 'refused-pair').flatMap(item => item.children.filter(c => c.tagName === 'ul'));
  assert.ok(lists.every(list => list.dir === 'ltr'), 'the problems read left to right');
  assert.equal(lists.flatMap(list => list.children).length, 4, 'two problems for each refused pair');
});

// Starts from: nothing selected.
test('a refused experiment is greyed with its reason and cannot be chosen', async () => {
  h.change(nodes['pick-experiment'], 'runs_sixspeed_18sep');
  await h.settle();
  assert.equal(nodes['pick-experiment'].value, '', 'the select falls back to its placeholder');
  assert.equal(nodes['pick-pair'].disabled, true);
  assert.equal(nodes.compute.disabled, true);
  assert.deepEqual(h.history, [], 'a choice that selects nothing leaves the address alone');
  assert.equal(h.requests.length, 0);
});

// Starts from: nothing selected.
test('a verdict that is missing, or was never recorded, says so in the box, the strip and the select', () => {
  const experiment = runs => options(nodes['pick-experiment']).find(o => o.value === runs);
  h.change(nodes['pick-experiment'], 'runs_d2');
  assert.equal(nodes.verdict.dataset.state, 'missing');
  assert.equal(nodes['verdict-short'].textContent, MISSING.ar);
  assert.equal(nodes['strip-verdict'].textContent, MISSING.ar);
  assert.ok(experiment('runs_d2').text.endsWith(MISSING.ar), 'the experiment select says it too');
  assert.equal(nodes['verdict-cells'].children.length, 0, 'a cell is never guessed');

  h.change(nodes['pick-experiment'], 'runs_zz');
  assert.equal(nodes.verdict.dataset.state, 'none');
  assert.equal(nodes['verdict-short'].textContent, NONE.ar);
  assert.equal(nodes['strip-verdict'].textContent, NONE.ar);
  assert.ok(experiment('runs_zz').text.endsWith(NONE.ar));
  assert.equal(nodes['verdict-cells'].children.length, 0);
  const pairs = options(nodes['pick-pair']);
  assert.equal(pairs.length, 3, 'the placeholder, the runnable pair and the refused one');
  assert.equal(pairs[2].disabled, true);
  assert.equal(h.history.at(-1), '/agents?runs=runs_zz');
});

// Starts from: runs_zz, no pair.
test('each choice fills the next select, keeps the address in sync and enables «احسب» only at a full selection', async () => {
  h.change(nodes['pick-experiment'], 'runs_c4');
  const pairs = options(nodes['pick-pair']);
  assert.equal(pairs.length, 9, 'the placeholder and eight pairs');
  assert.equal(nodes['pick-pair'].disabled, false);
  assert.equal(nodes['pick-pair'].value, '', 'no pair is chosen for the viewer');
  assert.match(pairs[1].text, /360\.6/, 'seed 0 quotes its row of the results table');
  assert.equal(nodes['pick-pair-note'].textContent, AR('agents.pick.pair_qualifier'));
  assert.equal(nodes['verdict-short'].textContent, C4.verdict.short.ar, 'the box reads the chosen experiment');
  assert.equal(nodes['strip-verdict'].textContent, C4.verdict.short.ar);
  assert.equal(nodes.verdict.dataset.state, 'found');
  assert.equal(nodes['pick-episode'].disabled, true);
  assert.equal(nodes.compute.disabled, true);
  assert.equal(h.history.at(-1), '/agents?runs=runs_c4');

  h.change(nodes['pick-pair'], '5');
  assert.equal(options(nodes['pick-episode']).length, 21, 'the placeholder and twenty episodes');
  assert.equal(nodes['pick-episode'].disabled, false);
  assert.equal(byClass(nodes['pick-note'], 'sighted').length, 1, 'one budget line per arm');
  assert.equal(byClass(nodes['pick-note'], 'blind').length, 1, 'one budget line per arm');
  assert.match(nodes['pick-note'].textContent, /300\D000/, 'each arm says what it was trained for');
  assert.ok(nodes['pick-note'].textContent.endsWith(AR('agents.pick.need_episode')));
  assert.equal(nodes.compute.disabled, true);
  assert.equal(h.history.at(-1), '/agents?runs=runs_c4&seed=5');

  h.change(nodes['pick-episode'], '1');
  assert.equal(nodes.compute.disabled, false);
  assert.equal(h.history.at(-1), '/agents?runs=runs_c4&seed=5&ep=1');
  assert.match(nodes['pick-note'].textContent, /141/, 'the chosen episode is spelled out under the selects');
  await h.settle();
  assert.equal(h.requests.length, 0, 'nothing computes until «احسب»');
});

// Starts from: runs_c4 / 5 / 1.
test('«احسب» asks for exactly the chosen episode, once with preempt=1', async () => {
  nodes.compute.click();
  const req = await h.nextRequest();
  const url = new URL(req.url, 'http://localhost');
  assert.equal(url.pathname, '/api/agents/episode');
  assert.deepEqual(Object.fromEntries(url.searchParams),
    { runs: 'runs_c4', seed: '5', ep: '1', since: '0', preempt: '1' });
  h.reply(req, { status: 'building', since: 0, steps: 719, frames: [{ k: 0, cars: [car(), car()] }], meta: META, road: ROAD });
  const next = await h.nextRequest();
  assert.doesNotMatch(next.url, /preempt/, 'the polls after it wait their turn');
  assert.match(next.url, /since=1/);
  h.reply(next, { status: 'ready', since: 1, steps: 719, frames: [] });
  await h.settle();
});

// Starts from: runs_c4 / 5 / 1, computed.
test('changing the pair after a computation clears the old episode and drops its late frames', async () => {
  nodes.compute.click();
  h.reply(await h.nextRequest(), { status: 'building', since: 0, steps: 719, frames: [{ k: 0, cars: [car(), car()] }], meta: META, road: ROAD });
  const inFlight = await h.nextRequest();
  assert.notEqual(nodes['pause-heading'].textContent, '—', 'the episode is on screen');
  assert.equal(nodes['scene-prompt'].hidden, true);

  h.change(nodes['pick-pair'], '3');
  assert.equal(nodes['pause-heading'].textContent, '—', 'the old episode left the pause panel');
  assert.equal(nodes['scene-prompt'].hidden, false, 'the scene asks for «احسب» again');
  assert.equal(nodes.loading.hidden, true, 'no loading card for an episode nobody asked for');
  assert.equal(h.history.at(-1), '/agents?runs=runs_c4&seed=3&ep=1', 'the episode is kept: the same twenty episodes');
  assert.equal(nodes['pick-episode'].value, '1');
  assert.equal(nodes.compute.disabled, false);

  h.reply(inFlight, { status: 'building', since: 1, steps: 719, frames: [{ k: 1, cars: [car(), car()] }] });
  await wait(450);
  assert.equal(nodes['pause-heading'].textContent, '—', 'a late frame of the old key changed the page');
  assert.equal(h.requests.length, 0, 'the old key is not polled again');
});
```

**1c.** Create `app/static/sim/agents-page-address.test.mjs` with the Write tool. It holds no backslash-u escape.

```js
// The /agents page opened from an address that names MORE than the catalog
// lets it select (episode 21 does not exist), against a fake DOM and a fake
// server (agents-page-harness.mjs). The page selects what it can, cuts the
// address back to exactly that, and computes nothing. This catalog also says
// stable-baselines3 is missing, as it is under the lab launcher's .venv: the
// page must say that nothing can be computed as soon as the catalog arrives,
// not after three choices.
//
// This file owns its own process, and agents.mjs boots once, on import; the
// tests run in order.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { STRINGS } from './i18n.mjs';
import { installFakePage } from './agents-page-harness.mjs';

const FIXTURE = JSON.parse(readFileSync(new URL('./agent-catalog.fixture.json', import.meta.url), 'utf8'));
const h = installFakePage({
  search: '?runs=runs_c4&seed=5&ep=21',
  ids: ['compute', 'error', 'pick-experiment', 'pick-pair', 'pick-episode', 'pick-note', 'lang-toggle'],
});
const { nodes } = h;
await import('./agents.mjs');

const AR = key => STRINGS.ar[key];
const times = (text, part) => text.split(part).length - 1;
const values = () => ['pick-experiment', 'pick-pair', 'pick-episode'].map(id => nodes[id].value);

test('an address naming more than exists is cut back to what it selects, and nothing computes', async () => {
  const boot = await h.nextRequest();
  assert.equal(boot.url, '/api/agents/catalog', 'the page\'s only request at boot is the catalog');
  h.reply(boot, { ...FIXTURE, sb3: false });
  await h.settle();
  assert.deepEqual(values(), ['runs_c4', '5', ''], 'the experiment and the pair exist; episode 21 does not');
  assert.deepEqual(h.history, ['/agents?runs=runs_c4&seed=5'], 'the address says only what is selected');
  assert.equal(nodes.compute.disabled, true);
  await h.settle();
  assert.equal(h.requests.length, 0, 'nothing computes');
});

// Starts from: runs_c4 / 5, no episode; the catalog says sb3 false.
test('without stable-baselines3 the picker says so once, before an episode is chosen and after', () => {
  const note = () => nodes['pick-note'].textContent;
  assert.equal(times(note(), AR('agents.load.no_sb3')), 1, 'said as soon as the catalog arrives');
  h.change(nodes['pick-episode'], '1');
  assert.deepEqual(values(), ['runs_c4', '5', '1']);
  assert.equal(h.history.at(-1), '/agents?runs=runs_c4&seed=5&ep=1');
  assert.equal(nodes.compute.disabled, true, '«احسب» stays disabled');
  assert.equal(times(note(), AR('agents.load.no_sb3')), 1, 'said once at a full selection too, not twice');
  nodes.compute.click();
  assert.equal(h.requests.length, 0, 'a disabled «احسب» sends nothing');
});
```

**1d.** Move the run test onto the harness and add its new first test. Write `$SCRATCH/m2t7_split_run_test.py` with the Write tool. It holds no backslash-u escape, and the head it writes has no backslash at all.

```python
"""Task 7: agents-page-run.test.mjs's fake page moves into the harness.

Everything above the first M1 test is replaced by HEAD; every M1 test below it
is kept byte for byte. Run from the repository root with the system python.
"""
from pathlib import Path

HEAD = r'''// The /agents page RUNNING, against a fake DOM and a fake server
// (agents-page-harness.mjs), opened from a FULL address: what the viewer is
// shown after a failed request is retried, how a grouped number reads in
// Arabic, and the pause panel. agents-page-nav.test.mjs opens the page from
// its nav link instead, agents-page-address.test.mjs from an address that
// names too much; agents-page.test.mjs checks the page's text without running
// it. This file owns the globals of its own test process.
//
// The fake DOM holds only the elements these checks read. Every other id is
// null, which agents.mjs already tolerates, so the profile, the chase view and
// the rest of the pause panel stay out of the way.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { installFakePage, byClass, FakeNode } from './agents-page-harness.mjs';

// The server's own catalog (agent_api.catalog), sb3 pinned true so these tests
// never depend on the machine that generated the fixture.
const CATALOG = {
  ...JSON.parse(readFileSync(new URL('./agent-catalog.fixture.json', import.meta.url), 'utf8')),
  sb3: true,
};
const h = installFakePage({
  search: '?runs=runs_c4&seed=5&ep=1',
  ids: ['compute', 'error', 'pick-experiment', 'pick-pair', 'pick-episode', 'pick-note', 'rise-caption',
    'seek', 'actions', 'lane-stopped', 'lang-toggle', 'turb-sighted', 'turb-blind'],
});
const { nodes, nextRequest, reply, settle, seekTo } = h;

// The page keeps the first meta it is given for a key (applyMeta), so every
// reply here carries this one. act is engine_env's ACT_LO / ACT_HI.
const AGENT = { budget_line: 'trained 300000 steps of 300000 requested' };
const META = {
  runs: 'runs_c4', seed: 5, ep: 1, steps: 719, dt: 1, protocol: 'd2', agents: [AGENT, AGENT],
  preview_s: [2, 5, 15, 30],
  act: { lo: [-8, -0.15, -40, 0, 0.3], hi: [4, 0.06, 15, 1, 1], neutral_phys: [0, 0, 0, 1, 1] },
  // agent_api.episode_meta sends round(TURB_PROTECT_K - 273.15, 1)
  limits: { turb_c: 849.9 },
};
const ROAD = {
  rise_m: 2755, p_baro_kpa: 101.3, t_amb_c: 42, climb_start_s: null,
  grade_pct: [0, 0, 0, 0], s_m: [0, 0, 20, 40], x_m: [0, 0, 20, 40], z_m: [0, 0, 0, 0],
};

await import('./agents.mjs');
// The page's only request at boot is the catalog; it is answered here, before
// any test, so every test below starts from the restored selection.
const boot = await nextRequest();
reply(boot, CATALOG);
await settle();

const retryButton = () => nodes.error.children.find(c => c.tagName === 'button') || null;

test('a full address restores its selection and computes nothing until «احسب»', async () => {
  assert.equal(boot.url, '/api/agents/catalog');
  assert.equal(nodes['pick-experiment'].value, 'runs_c4');
  assert.equal(nodes['pick-pair'].value, '5');
  assert.equal(nodes['pick-episode'].value, '1');
  assert.equal(nodes.compute.disabled, false, '«احسب» is ready');
  assert.deepEqual(h.history, [], 'an address the catalog allows is kept as it is');
  await settle();
  assert.equal(h.requests.length, 0, 'no episode request before «احسب»');
});

'''

path = Path("app/static/sim/agents-page-run.test.mjs")
src = path.read_text(encoding="utf-8")
first = "test('a retry that reaches the server clears the \"server unavailable\" alert'"
assert src.count(first) == 1, "the first M1 test was not found exactly once"
path.write_text(HEAD + src[src.index(first):], encoding="utf-8", newline="")
print("run test now starts with", len(HEAD.splitlines()), "harness lines; every M1 test kept")
```

Run it:

```bash
$PY "$(cygpath -w "$SCRATCH/m2t7_split_run_test.py")"
```

Expected: `run test now starts with 64 harness lines; every M1 test kept`.

**1e.** Add the Python page test. In `app/test_agents.py`, find the line `        self.assertLess(hits[0] - head, 120, "the one read of .cars must be inside carOf")`, the last line of `test_every_car_is_read_through_carOf`. Insert the method below right after it, with one blank line before it. The method stays inside `class PageTests` and uses the module-level `re`.

```python
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
```

- [ ] **Step 2: Run them to verify they fail**

```bash
node --test "app/static/sim/agents-page-nav.test.mjs" 2>&1 | grep -E "^✖|^ℹ (tests|pass|fail)|Error: no request" | head -12
node --test "app/static/sim/agents-page-address.test.mjs" 2>&1 | grep -E "^✖|^ℹ (tests|pass|fail)|Error: no request" | head -8
node --test "app/static/sim/agents-page-run.test.mjs" 2>&1 | grep -E "^✖|^ℹ (tests|pass|fail)|Error" | head -6
$PY -m app.test_agents PageTests.test_the_picker_opens_empty_and_disabled 2>&1 | grep -E "AssertionError|^FAILED|^OK"
```

Expected, as observed on the 28 Sep prototype with Task 6 in place and M1's `agents.mjs`:
- **Nav test:**
  - `✖ from the nav link the page selects nothing, computes nothing, and says what to choose` fails with `Error: no request arrived within 3000 ms`, because M1 never asks for a catalog.
  - Every later test fails behind it.
  - The summary reads `ℹ tests 7`, `ℹ pass 0`, `ℹ fail 7`.
- **Address test:** `✖ an address naming more than exists is cut back to what it selects, and nothing computes` fails with `Error: no request arrived within 3000 ms`. The summary reads `ℹ tests 2`, `ℹ pass 0`, `ℹ fail 2`.
- **Run test:** the whole file fails at its top-level `await nextRequest()`:
  - `Error: no request arrived within 3000 ms`;
  - `✖ app\static\sim\agents-page-run.test.mjs`;
  - `ℹ tests 1` and `ℹ fail 1`.
- **Python:** `AssertionError: False is not true : #pick-pair-note is missing` and `FAILED (failures=1)`.

- [ ] **Step 3: Implement**

**3a.** In `app/static/agents.html`, make two replacements with the Edit tool. Find

```html
          <div class="pick-row"><label for="pick-pair" data-i18n="agents.pick.pair">الزوج</label><select id="pick-pair" disabled></select></div>
          <div class="pick-row"><label for="pick-episode" data-i18n="agents.pick.episode">الحلقة</label><select id="pick-episode" disabled></select></div>
```

and replace it with

```html
          <div class="pick-row"><label for="pick-pair" data-i18n="agents.pick.pair">الزوج</label><select id="pick-pair" disabled></select></div>
          <p id="pick-pair-note" class="pick-caption"></p>
          <div class="pick-row"><label for="pick-episode" data-i18n="agents.pick.episode">الحلقة</label><select id="pick-episode" disabled></select></div>
          <p id="pick-episode-note" class="pick-caption"></p>
```

Then find the end of the `#compute` line and the `</section>` that closes the picker:

```html
<span data-i18n="agents.compute">احسب</span></button>
        </section>
```

and replace it with

```html
<span data-i18n="agents.compute">احسب</span></button>
          <details id="pick-refused" class="pick-refused" hidden></details>
        </section>
```

**3b.** In `app/static/sim/agents.css`, replace `.pick-row select:disabled{opacity:1;cursor:default;color:var(--ink)}` with

```css
.pick-row select:disabled{opacity:.55;cursor:not-allowed}
/* Under the pair row: "difference of the medians of 20 episodes ...; not
   this episode". Under the episode row: Phase D's one road. Aligned with the
   selects (the 72 px label column plus the 10 px gap). */
.pick-caption{margin:-3px 0 9px;padding-inline-start:82px;font-size:9px;line-height:1.7;color:var(--muted)}
.pick-caption:empty{display:none}
.pick-reason{color:var(--ink-2)}
.pick-warning{color:var(--warn-ink)}
/* Every pair that cannot run, with every problem the server found. The
   problems are ltr code-like lines that must wrap, never widen the page. */
.pick-refused{margin-top:12px;font-size:10px;line-height:1.7;color:var(--muted)}
.pick-refused summary{cursor:pointer}
.refused-pair b{font-weight:600;color:var(--ink-2)}
.refused-pair ul{margin:2px 0 8px;padding-inline-start:18px;font:9px/1.6 Consolas,monospace;overflow-wrap:anywhere}
```

Then, in the first `@media(max-width:760px){` block, replace `.pick-row{grid-template-columns:1fr;gap:4px}` with

```css
.pick-row{grid-template-columns:1fr;gap:4px}
.pick-caption{padding-inline-start:0}
```

**3c.** In `app/static/sim/agents.mjs`, make these twelve replacements with the Edit tool. Only two lines in the file carry an escape (`fmtInt` and `fmtAction`), and no replacement touches either of them, so every `old_string` is plain text.

(1) The header comment and the imports. Find

```js
// M1: the picker is READ-ONLY. It shows ?runs=&seed=&ep= from the address and
// nothing computes until «احسب» is pressed. Nothing is stored in the browser
// except the lab's own theme and language preferences.
import './agents-strings.mjs';
import { t, LANGS, DEFAULT_LANG, resolveLang, applyTranslations } from './i18n.mjs';
import { PlaybackClock, formatTime } from './playback.mjs';
import {
  DT, PROFILE_VE, parseEpisodeQuery, appendFrames, createPlayState, playOrWait,
  pauseByUser, resumeIfStalled, settleDone, episodeAt, profilePoints, previewMarks, gradeRamp,
  ACTIONS, M_PER_UNIT, createEpisodeRoad, gaugeFraction, commandPhysical, laneStoppedAt,
} from './agent-view.mjs';
```

and replace it with

```js
// M2: the picker WORKS. At boot the page loads GET /api/agents/catalog, and
// agent-picker.mjs decides what the three selects offer. The page opens with
// NOTHING selected unless the address names a selection the catalog allows,
// never a default pair. Every change of a select replaces the address (never a
// new history entry) and clears the episode on screen. Nothing computes until
// «احسب» is pressed. Nothing is stored in the browser except the lab's own
// theme and language preferences.
import './agents-strings.mjs';
import { t, LANGS, DEFAULT_LANG, resolveLang, applyTranslations } from './i18n.mjs';
import { PlaybackClock, formatTime } from './playback.mjs';
import {
  DT, PROFILE_VE, appendFrames, createPlayState, playOrWait,
  pauseByUser, resumeIfStalled, settleDone, episodeAt, profilePoints, previewMarks, gradeRamp,
  ACTIONS, M_PER_UNIT, createEpisodeRoad, gaugeFraction, commandPhysical, laneStoppedAt,
} from './agent-view.mjs';
import {
  NOTHING, parsePickerQuery, experimentOf, pairOf, resolveSelection, choose, selectionSearch,
  computeState, experimentOptions, pairOptions, episodeOptions, pairQualifier, sameRoadNote,
} from './agent-picker.mjs';
```

(2) The state's `query`. Find

```js
const state = {
  query: parseEpisodeQuery(window.location.search),
  frames: [],
```

and replace it with

```js
const state = {
  catalog: null,   // GET /api/agents/catalog, once it has arrived
  bootQuery: parsePickerQuery(window.location.search),
  sel: { ...NOTHING },   // what the three selects name: { runs, seed, ep }
  frames: [],
```

(3) `keyOf`. Find

```js
const keyOf = q => `${q.runs}/${q.seed}/${q.ep}`;
```

and replace it with

```js
const keyOf = q => `${q.runs}/${q.seed}/${q.ep}`;
const sameSel = (a, b) => a.runs === b.runs && a.seed === b.seed && a.ep === b.ep;
```

(4) The loading card's detail line, in `renderLoad()`. Find

```js
  setText($('load-detail'), state.query ? keyOf(state.query) : '');
```

and replace it with

```js
  setText($('load-detail'), state.sel.runs === null ? '' : keyOf(state.sel));
```

(5) `episodeUrl()`. Find

```js
function episodeUrl(since, preempt) {
  const q = state.query;
```

and replace it with

```js
function episodeUrl(since, preempt) {
  const q = state.sel;
```

(6) `compute()`'s guard. Find

```js
function compute() {
  if (!state.query) return;
```

and replace it with

```js
function compute() {
  if (!computeState(state.catalog, state.sel).ok) return;
```

(7) `compute()`'s meta reset. Find

```js
  if (state.metaKey !== keyOf(state.query)) { state.meta = null; state.road = null; }
```

and replace it with

```js
  if (state.metaKey !== keyOf(state.sel)) { state.meta = null; state.road = null; }
```

(8) M1's `option()` and `renderPicker()`, which are the whole of `agents.mjs:301-345`. Find

```js
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
```

and replace it with

```js
// ---------------------------------------------------------------- picker
// What the three selects name, read from the catalog. The verdict box follows
// the chosen experiment even before «احسب»; after it, the episode's own meta
// is only the fallback (the two always agree: the route reads one catalog).
function currentExperiment() {
  return experimentOf(state.catalog, state.sel.runs);
}
function currentPair() {
  return pairOf(currentExperiment(), state.sel.seed);
}
function currentVerdict() {
  return currentExperiment()?.verdict ?? state.meta?.verdict ?? null;
}

// The <option>s and the refused list are rebuilt only when their text
// changed, so a select is never rebuilt under the viewer's pointer by a poll
// or a redraw, and an open list does not close.
const drawn = new WeakMap();
function fillSelect(select, options, value) {
  if (!select) return;
  const signature = JSON.stringify(options);
  if (drawn.get(select) !== signature) {
    drawn.set(select, signature);
    select.textContent = '';
    for (const o of options) {
      const node = el('option', '', o.text);
      node.value = o.value;
      node.disabled = o.disabled;
      select.appendChild(node);
    }
  }
  select.value = value === null ? '' : String(value);
}

// Every pair that cannot run, in every experiment, with EVERY problem the
// server found (design section 8, "listed and disabled with reason and
// fields"): both arms, and each stored and live field of a plant mismatch. A
// greyed option has room for the first problem only.
function renderRefused() {
  const box = $('pick-refused');
  if (!box) return;
  const refused = (state.catalog?.experiments || []).flatMap(e => (e.pairs || [])
    .filter(p => !p.runnable)
    .map(p => ({ name: e.name, seed: p.seed, problems: p.problems || [] })));
  box.hidden = !refused.length;
  const signature = JSON.stringify([currentLang, refused]);
  if (drawn.get(box) === signature) return;
  drawn.set(box, signature);
  box.textContent = '';
  if (!refused.length) return;
  box.appendChild(el('summary', '', t(currentLang, 'agents.pick.refused_summary', { n: refused.length })));
  for (const r of refused) {
    const item = el('div', 'refused-pair');
    item.appendChild(el('b', '', t(currentLang, 'agents.pick.refused_pair', { name: r.name, seed: r.seed })));
    // The server's own words, read left to right: bullets and indent on the left.
    const list = el('ul');
    list.dir = 'ltr';
    for (const problem of r.problems) list.appendChild(el('li', '', String(problem)));
    item.appendChild(list);
    box.appendChild(item);
  }
}

function renderPicker() {
  const catalog = state.catalog;
  const sel = state.sel;
  const experiment = currentExperiment();
  const pair = currentPair();
  const episodes = episodeOptions(catalog, pair, currentLang);
  fillSelect($('pick-experiment'), experimentOptions(catalog, currentLang), sel.runs);
  fillSelect($('pick-pair'), pairOptions(experiment, currentLang), sel.seed);
  fillSelect($('pick-episode'), episodes, sel.ep);
  const enable = (id, on) => { const node = $(id); if (node) node.disabled = !on; };
  enable('pick-experiment', Boolean(catalog));
  enable('pick-pair', Boolean(experiment));
  enable('pick-episode', Boolean(pair));
  setText($('pick-pair-note'), pairQualifier(experiment, currentLang));
  setText($('pick-episode-note'), sameRoadNote(catalog, experiment, currentLang));
  const can = computeState(catalog, sel);
  enable('compute', can.ok);
  renderRefused();
  const note = $('pick-note');
  if (!note) return;
  note.textContent = '';
  // Without stable-baselines3 nothing can be computed (design section 4,
  // Runnability). Said as soon as the catalog arrives, not after three
  // choices; the pairs stay selectable, so their verdicts and table rows can
  // still be read.
  if (catalog && !catalog.sb3) note.appendChild(el('span', 'pick-reason pick-warning', t(currentLang, 'agents.load.no_sb3')));
  // The select may truncate on a narrow screen; the chosen episode and its
  // weights must stay legible, so they are spelled out here as well.
  const chosen = episodes.find(o => sel.ep !== null && o.value === String(sel.ep));
  if (chosen) note.appendChild(el('span', '', chosen.text));
  (pair?.agents || []).forEach((agent, i) => {
    const line = el('span', LANES[i]);
    line.appendChild(el('i', 'lane-dot'));
    line.appendChild(el('span', '', `${t(currentLang, LANE_LABEL[i])} · ${t(currentLang, 'agents.pick.budget', { budget: budgetSteps(agent.budget_line) })}`));
    note.appendChild(line);
  });
  // What is still to choose; the missing stable-baselines3 is said once, above.
  if (!can.ok && can.reason !== 'agents.load.no_sb3') note.appendChild(el('span', 'pick-reason', t(currentLang, can.reason)));
}

// Everything on screen that belongs to the episode last computed goes, and a
// late response for it is dropped: loadToken is what poll() checks after every
// await, and chaseToken is what mountChase() checks after its import.
function clearEpisode() {
  state.loadToken += 1;
  const now = performance.now();
  pauseByUser(state.play, now);
  state.play = createPlayState(new PlaybackClock(0));
  state.play.clock.setRate(Number($('rate')?.value) || 1, now);
  state.frames = [];
  state.meta = null;
  state.metaKey = null;
  state.road = null;
  state.done = false;
  state.device = null;
  state.versions = null;
  state.lastK = -2;
  state.drawnTime = -1;
  const profile = $('profile');
  if (profile) profile.textContent = '';
  state.profile = null;
  chaseToken += 1;
  chase?.dispose();
  chase = null;
  const scene = $('chase');
  if (scene) scene.textContent = '';
  showLoad(null);
  showError(null);
  const prompt = $('scene-prompt');
  if (prompt) prompt.hidden = false;
  setControlsEnabled(false);
  renderPanel(-1);
}

// A viewer changed one select. choose() says what that selects; a choice that
// changes nothing (the same value, or a greyed option) only redraws the picker.
function onPick(level, select) {
  if (!state.catalog || !select) return;
  const next = choose(state.catalog, state.sel, level, select.value);
  if (sameSel(next, state.sel)) { renderPicker(); return; }
  clearEpisode();
  state.sel = next;
  window.history?.replaceState?.(null, '', `/agents${selectionSearch(next)}`);
  renderAll();
}

// The catalog, once, at boot. It never starts a computation.
async function loadCatalog() {
  showError(null);
  let res;
  let body = null;
  try {
    res = await fetch('/api/agents/catalog', { headers: { Accept: 'application/json' }, cache: 'no-store' });
    body = await res.json().catch(() => null);
  } catch (err) {
    showError(() => t(currentLang, 'agents.pick.catalog_error', { message: t(currentLang, 'agents.load.server_down') }),
      { retry: loadCatalog });
    return;
  }
  if (res.status !== 200 || !body || !Array.isArray(body.experiments)) {
    const message = `HTTP ${res.status}`;
    showError(() => t(currentLang, 'agents.pick.catalog_error', { message }), { retry: loadCatalog });
    return;
  }
  state.catalog = body;
  state.sel = resolveSelection(body, state.bootQuery);
  // The address never names more than is selected. It is compared as TEXT:
  // parsePickerQuery has already dropped a malformed level (runs_C4, seed=5abc,
  // ep=21), so comparing selections would leave such an address as it was.
  const search = selectionSearch(state.sel);
  if (window.location.search !== search) window.history?.replaceState?.(null, '', `/agents${search}`);
  renderAll();
}
```

(9) `renderVerdict()`'s verdict. Find

```js
function renderVerdict() {
  const v = state.meta?.verdict || null;
```

and replace it with

```js
function renderVerdict() {
  const v = currentVerdict();
```

(10) `renderVerdict()`'s scored list. Find

```js
  scored.textContent = '';
  const m = state.meta;
  (m?.agents || []).forEach((agent, i) => {
    const status = !m.result_file ? t(currentLang, 'agents.verdict.no_result')
```

and replace it with

```js
  scored.textContent = '';
  // The chosen pair's agents from the catalog, so the box reads before «احسب».
  const agents = state.meta?.agents ?? currentPair()?.agents ?? [];
  const resultFile = state.meta ? state.meta.result_file : currentPair()?.result_file;
  agents.forEach((agent, i) => {
    const status = !resultFile ? t(currentLang, 'agents.verdict.no_result')
```

(11) The listeners in `start()`. Find

```js
  $('compute')?.addEventListener('click', compute);
```

and replace it with

```js
  $('compute')?.addEventListener('click', compute);
  $('pick-experiment')?.addEventListener('change', () => onPick('runs', $('pick-experiment')));
  $('pick-pair')?.addEventListener('change', () => onPick('seed', $('pick-pair')));
  $('pick-episode')?.addEventListener('change', () => onPick('ep', $('pick-episode')));
```

(12) The end of `start()`. Find

```js
  applyLanguage(recall(STORE.lang, LANGS, DEFAULT_LANG));
  requestAnimationFrame(loop);
}
```

and replace it with

```js
  applyLanguage(recall(STORE.lang, LANGS, DEFAULT_LANG));
  requestAnimationFrame(loop);
  loadCatalog().catch(err => console.error(err));
}
```

**3d.** Make the removals and add the two strings with a checked script. Write `$SCRATCH/m2t7_strings_and_removals.py` with the Write tool. The script holds no backslash-u escape. Python file I/O keeps every escape already in `agents-strings.mjs`, and the script counts them before and after.

```python
"""Task 7: M1's read-only address parser and its test go, the M1 pair label
goes, and the two strings of the refused-pairs list arrive. Each change is
checked before it is made. Python file I/O keeps every backslash-u escape in
agents-strings.mjs exactly as written (counted before and after).

Run from the repository root with the system python.
"""
from pathlib import Path

ESC = chr(92) + "u"


def cut(path, start, end):
    p = Path(path)
    s = p.read_text(encoding="utf-8")
    assert s.count(start) == 1, f"{path}: {start!r} not found once"
    a = s.index(start)
    b = s.index(end, a)
    p.write_text(s[:a] + s[b:], encoding="utf-8", newline="")


cut("app/static/sim/agent-view.mjs",
    "// The server's own patterns (app/agent_catalog.py RUNS_NAME",
    "/** Step at which a lane's car first went null")
cut("app/static/sim/agent-view.test.mjs",
    "test('parseEpisodeQuery reads the M1 address and nothing else'",
    "test('laneStoppedAt names the first step a car went null'")

p = Path("app/static/sim/agents-strings.mjs")
before = p.read_text(encoding="utf-8")
lines = before.split("\n")
kept = [line for line in lines if not line.startswith("    'agents.pick.pair_option': ")]
assert len(lines) - len(kept) == 2, "agents.pick.pair_option must go from exactly two languages"
after = "\n".join(kept)

# The list of pairs that cannot run (agents.mjs renderRefused), one entry per
# language, right after that language's catalog_error line (Task 6).
NEW = {
    "    'agents.pick.catalog_error': 'تعذّر تحميل قائمة التجارب: {message}',\n":
        "    'agents.pick.refused_summary': 'أزواج لا يمكن تشغيلها ({n})، ولماذا',\n"
        "    'agents.pick.refused_pair': '{name} · بذرة {seed}',\n",
    "    'agents.pick.catalog_error': 'The list of experiments could not be loaded: {message}',\n":
        "    'agents.pick.refused_summary': 'Pairs that cannot run ({n}), and why',\n"
        "    'agents.pick.refused_pair': '{name} · seed {seed}',\n",
}
for anchor, extra in NEW.items():
    assert after.count(anchor) == 1, f"{anchor.strip()!r} not found once"
    after = after.replace(anchor, anchor + extra)
assert after.count(ESC) == before.count(ESC), "an escape was lost"
p.write_text(after, encoding="utf-8", newline="")
print("removed parseEpisodeQuery, its test and agents.pick.pair_option; added 2 keys x 2 languages;",
      "escapes kept:", after.count(ESC))
```

Run it, then check that nothing still names the removed items:

```bash
$PY "$(cygpath -w "$SCRATCH/m2t7_strings_and_removals.py")"
grep -rn "parseEpisodeQuery\|pick.pair_option\|read-only in M1" app/static/sim/ || echo "none left"
```

Expected: `removed parseEpisodeQuery, its test and agents.pick.pair_option; added 2 keys x 2 languages; escapes kept: 8`, then `none left`. The 8 is the escape count Task 6 leaves in the file.

- [ ] **Step 4: Run to verify they pass**

```bash
node --test "app/static/sim/agents-page-nav.test.mjs" 2>&1 | grep -E "^✖|^ℹ (tests|pass|fail)"
node --test "app/static/sim/agents-page-address.test.mjs" 2>&1 | grep -E "^✖|^ℹ (tests|pass|fail)"
node --test "app/static/sim/agents-page-run.test.mjs" 2>&1 | grep -E "^✖|^ℹ (tests|pass|fail)"
node --test "app/static/sim/*.test.mjs" 2>&1 | grep -E "^✖|^ℹ (tests|pass|fail|skipped)"
$PY -m app.test_agents PageTests 2>&1 | grep -E "^Ran|^OK|FAILED|Error"
```

Expected (observed on the 28 Sep prototype):
- **Nav test:** `ℹ tests 7`, `ℹ pass 7`, `ℹ fail 0`.
- **Address test:** `ℹ tests 2`, `ℹ pass 2`, `ℹ fail 0`.
- **Run test:** `ℹ tests 8`, `ℹ pass 8`, `ℹ fail 0`: M1's 7 plus the new first test.
- **Node glob:** `ℹ fail 0`, `ℹ skipped 0`. The total is Task 6's total plus 9: 7 nav, 2 address and 1 run, minus 1 for the deleted `parseEpisodeQuery` test. On the prototype it went from 86 to 95. Read it from the run.
- **Python:** `OK`. Expect `Ran 6 tests` if Task 6 put its fixture test in PageTests, as its skeleton says: M1's 4, Task 6's 1 and this one. Read the count.

No `✖` line may appear.

- [ ] **Step 5: Commit**

```bash
git add app/static/sim/agents-page-harness.mjs app/static/sim/agents-page-nav.test.mjs app/static/sim/agents-page-address.test.mjs
$PY verify_docs.py 2>&1 | tail -1
```

Expected last line: `All N checks pass (M figure mentions scanned in the documents).` The M1 baseline was 67 checks and 782 mentions; read the counts from the run. If it fails, the new docstring in `app/test_agents.py` names a retired figure: reword it and run again.

```bash
git add app/static/agents.html app/static/sim/agents.css app/static/sim/agents.mjs app/static/sim/agent-view.mjs \
  app/static/sim/agent-view.test.mjs app/static/sim/agents-strings.mjs app/static/sim/agents-page-run.test.mjs app/test_agents.py
$PY -m app.test_replay > "$SCRATCH/m2t7_replay.txt" 2>&1; tail -1 "$SCRATCH/m2t7_replay.txt"
node --test "app/static/sim/*.test.mjs" > "$SCRATCH/m2t7_node.txt" 2>&1; grep -E "^ℹ (tests|pass|fail)" "$SCRATCH/m2t7_node.txt"
{
  printf '%s\n' "Agent replay M2 task 7: the working picker, usable from its own nav link" "" \
    "Jad found on 28 Sep that /agents opened from its nav link selected nothing and" \
    "offered three read-only lists. The page now loads GET /api/agents/catalog at" \
    "boot, fills three selects through agent-picker.mjs, selects only what the" \
    "address names and the catalog allows (from the nav link: nothing), cuts an" \
    "address that names more back to what it selects, keeps the address in sync" \
    "with replaceState, clears the episode on screen and drops late frames on every" \
    "change, and reads the verdict box from the chosen experiment, missing and none" \
    "states included. Every pair that cannot run is listed under the picker with" \
    "every problem the server found (design section 8), and a missing" \
    "stable-baselines3 is said once as soon as the catalog arrives (section 4)." \
    "M1's read-only parseEpisodeQuery and agents.pick.pair_option are gone. The fake" \
    "page of agents-page-run.test.mjs moved into agents-page-harness.mjs, so two" \
    "more processes boot the page: from the nav link and from an address that" \
    "names too much."
  printf '\n$ node --test "app/static/sim/*.test.mjs"   (summary)\n'
  grep -E "^ℹ " "$SCRATCH/m2t7_node.txt"
  printf '\n$ python -m app.test_replay\n'
  cat "$SCRATCH/m2t7_replay.txt"
  printf '\nCo-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>\n'
} > "$SCRATCH/m2t7_msg.txt"
git commit -F "$SCRATCH/m2t7_msg.txt"
git log --oneline -1
```

Expected: `app.test_replay` ends with `49 of 49 checks pass`, which is the M1 baseline; read the count from the run. The commit lands on `JMF-2340550-sep17`.

---


---

### Task 8: fe-page: per-protocol wording -- Phase D's blind car wherever it is named, its panel caveat, and «احسب» over a running build says it is stopping it

**Files:**
- Modify: `app/static/sim/agents.mjs`. Every edit below is found by its text. After Task 7 the lines are:

  | name | line |
  |---|---|
  | `LANE_LABEL` | `:39` |
  | `BLIND_LABEL` | `:50-52` |
  | `polling` | `:64` |
  | `compute` | `:184` |
  | `poll` | `:207` |
  | `handle` | `:243` |
  | `currentVerdict` | `:322` |
  | `renderPicker` | `:377` |
  | `renderVerdict` | `:506` |
  | `renderLaneLabels` | `:783` |
  | `renderSeen` | `:906` |
  | `renderStopped` | `:964` |

- Modify: `app/static/sim/agents-page-nav.test.mjs` (two tests appended)
- Test: `app/static/sim/agents-page-nav.test.mjs`

**Interfaces:**
- Consumes:
  - From Task 6:
    - `blindLabelKey(protocol)` and `notBlindCite(verdict)` in `agent-picker.mjs`;
    - the strings `agents.car.blind_phase_d`, `agents.seen.blind_phase_d` (`{zeros}`, `{cite}`) and `agents.load.stopping` (`{runs}`, `{seed}`, `{ep}`).
  - From Task 7:
    - `currentExperiment()`, `currentPair()` and `currentVerdict()`;
    - the per-arm budget lines in `renderPicker`;
    - the harness;
    - the nav test's `FIXTURE`, `CATALOG`, `META`, `ROAD`, `car(over)`, `options` and `AR`.
  - `meta.protocol` (`'phase-d'` | `'d2'`).
- Produces:
  - `currentProtocol()` and `laneLabel(j)` in `agents.mjs`. `LANE_LABEL` and `BLIND_LABEL` are gone.
  - Every place that names a car calls `t(currentLang, laneLabel(j))`:
    - the scene labels;
    - the budget lines in pick-note;
    - the verdict box's scored lines;
    - `renderStopped`, which used `LANE_LABEL[1]` in M1 and was on M1's left-for-later list.
  - For Phase D, `renderSeen` uses `agents.seen.blind_phase_d` with `{cite: notBlindCite(currentVerdict())}`.
  - `state.preempted`: `compute()` sets it true, and any answer other than 'busy' or a failed fetch sets it false. While it is true, the busy branch shows `agents.load.stopping`; otherwise it shows M1's `agents.load.busy`.

**Where this task follows the code rather than the skeleton:**
- The sighted scene label also goes through `laneLabel(0)`.
- The Phase D test also checks that the badge reads 12.0. That is the page's half; the grade of 0.12 in `meta.episode` is Task 4's.

- [ ] **Step 1: Write the failing tests**

Begin every command block of this task with Task 7's environment block.

Append this to the end of `app/static/sim/agents-page-nav.test.mjs`, after the last `});`, with one blank line before it. It holds no backslash-u escape.

```js
// Starts from: runs_c4 / 3 / 1, nothing computed.
test('Phase D: the same-road episodes, and the blind car named as possibly memorising its road wherever it is named', async () => {
  const PD = FIXTURE.experiments.find(e => e.runs === 'runs');
  h.change(nodes['pick-experiment'], 'runs');
  assert.equal(nodes['pick-pair-note'].textContent, AR('agents.pick.pair_qualifier_same_road'));
  assert.match(nodes['pick-episode-note'].textContent, /180/, 'the one road\'s climb start');
  assert.match(nodes['pick-episode-note'].textContent, /12\.0/, 'and its grade');
  h.change(nodes['pick-pair'], '0');
  const episodes = options(nodes['pick-episode']).slice(1);
  assert.equal(episodes.length, 20);
  assert.ok(episodes.every(o => o.text.includes('الطريق نفسه')), 'every Phase D episode says it is the same road');
  h.change(nodes['pick-episode'], '1');
  assert.match(byClass(nodes['pick-note'], 'blind')[0].textContent, /قد يحفظه/, 'the blind arm\'s budget line');
  assert.doesNotMatch(byClass(nodes['pick-note'], 'sighted')[0].textContent, /قد يحفظه/);
  assert.equal(nodes['verdict-short'].textContent, PD.verdict.short.ar);
  assert.match(byClass(nodes['verdict-scored'], 'blind')[0].textContent, /قد يحفظه/, 'the verdict box\'s scored line');

  nodes.compute.click();
  const req = await h.nextRequest();
  assert.match(req.url, /runs=runs&seed=0&ep=1&/);
  const meta = {
    ...META, experiment: 'Phase D', runs: 'runs', prefix: 'phase_d', protocol: 'phase-d', seed: 0, ep: 1,
    episode: { ...CATALOG.episodes['phase-d'][0] }, agents: PD.pairs[0].agents, verdict: PD.verdict,
  };
  const blind = car({ preview_pct: [0, 0, 0, 0] });
  h.reply(req, { status: 'ready', since: 0, steps: 2, meta, road: ROAD,
    frames: [{ k: 0, cars: [car(), blind] }, { k: 1, cars: [car(), null] }] });
  await h.settle();
  assert.match(nodes['lane-blind-label'].textContent, /قد يحفظه/, 'the scene label');
  assert.match(nodes['sim-badge'].textContent, /12\.0/, 'the badge reads the one road\'s grade');
  h.seekTo(0.5);
  assert.match(nodes['seen-blind'].textContent, /قد يحفظه/, 'the pause panel line');
  assert.ok(nodes['seen-blind'].textContent.includes('results/PHASE_D_RESULT.txt:33-40'), 'cited where results/ says it');
  assert.match(nodes['seen-blind'].textContent, /0 · 0 · 0 · 0/, 'with the inputs it was actually given');
  h.seekTo(1.5);
  assert.equal(nodes['lane-stopped'].hidden, false);
  assert.ok(nodes['lane-stopped'].textContent.startsWith(AR('agents.car.blind_phase_d')), 'the stopped lane');

  h.change(nodes['pick-experiment'], 'runs_c4');
  h.change(nodes['pick-pair'], '5');
  h.change(nodes['pick-episode'], '1');
  const c4Blind = byClass(nodes['pick-note'], 'blind')[0].textContent;
  assert.ok(c4Blind.startsWith(AR('agents.car.blind')), 'C4\'s blind car keeps its own label');
  assert.doesNotMatch(c4Blind, /قد يحفظه/, 'without the Phase D caveat');
});

// Starts from: runs_c4 / 5 / 1, nothing computed.
test('«احسب» over another running build says it is stopping it, not to press «احسب» again', async () => {
  const title = () => nodes['load-title'].textContent;
  const busy = { status: 'busy', since: 0, steps: 719, frames: [], active: { runs: 'runs_c4', seed: 3, ep: 1 } };
  nodes.compute.click();
  const req = await h.nextRequest();
  assert.match(req.url, /preempt=1/);
  h.reply(req, { ...busy, meta: META, road: ROAD });
  await h.settle();
  assert.match(title(), /يُوقَف/);
  for (const part of ['runs_c4', ' 3 ', ' 1)']) assert.ok(title().includes(part), `names the build it stops: ${part}`);
  assert.doesNotMatch(title(), /اضغط احسب/, 'this press already asked for it');

  const second = await h.nextRequest();
  assert.doesNotMatch(second.url, /preempt/);
  h.reply(second, busy);
  await h.settle();
  assert.match(title(), /يُوقَف/, 'still stopping it on the next poll');

  h.reply(await h.nextRequest(), { status: 'loading', since: 0, steps: 719, frames: [] });
  await h.settle();
  assert.equal(title(), AR('agents.load.networks'));

  h.fail(await h.nextRequest());
  await h.settle();
  const retry = nodes.error.children.find(c => c.tagName === 'button');
  assert.ok(retry, 'a failed poll offers a retry');
  retry.click();
  h.reply(await h.nextRequest(), busy);
  await h.settle();
  assert.match(title(), /اضغط احسب/, 'after a failed request the preempt may never have arrived');
});
```

- [ ] **Step 2: Run it to verify it fails**

```bash
node --test "app/static/sim/agents-page-nav.test.mjs" 2>&1 | grep -E "^✖|^✔|^ℹ (tests|pass|fail)|AssertionError" | head -16
```

Expected (observed on the 28 Sep prototype):
- The seven tests from Task 7 show `✔`.
- `✖ Phase D: the same-road episodes, ...` fails with `AssertionError [ERR_ASSERTION]: the blind arm's budget line`. M1's `LANE_LABEL[1]` names every blind car the same way.
- `✖ «احسب» over another running build ...` fails with `The input did not match the regular expression /يُوقَف/. Input: 'تُحسب حلقة أخرى الآن (runs_c4 بذرة 3 حلقة 1) — اضغط احسب لإيقافها وبدء هذه'`.
- The summary reads `ℹ tests 9`, `ℹ pass 7`, `ℹ fail 2`.

- [ ] **Step 3: Implement**

In `app/static/sim/agents.mjs`, make these fourteen replacements with the Edit tool. None of them touches a line that carries an escape.

(1) The picker import. Find

```js
  computeState, experimentOptions, pairOptions, episodeOptions, pairQualifier, sameRoadNote,
} from './agent-picker.mjs';
```

and replace it with

```js
  computeState, experimentOptions, pairOptions, episodeOptions, pairQualifier, sameRoadNote,
  blindLabelKey, notBlindCite,
} from './agent-picker.mjs';
```

(2) `LANE_LABEL`. Find

```js
const LANES = ['sighted', 'blind'];
const LANE_LABEL = ['agents.car.sighted', 'agents.car.blind'];
```

and replace it with

```js
const LANES = ['sighted', 'blind'];
```

(3) `BLIND_LABEL` and its comment. Find

```js
let chaseToken = 0;
// The blind car's label, by protocol. M2 gives Phase D's blind car its own
// ("may have memorised the road", PHASE_D_RESULT.txt:33-37) as one more row.
const BLIND_LABEL = { d2: 'agents.car.blind', 'phase-d': 'agents.car.blind' };
```

and replace it with

```js
let chaseToken = 0;
```

(4) The state gains `preempted`. Find

```js
  loadToken: 0,
  polling: null,
```

and replace it with

```js
  loadToken: 0,
  polling: null,
  // True from «احسب» until an answer other than 'busy' (or a failed request):
  // while it holds, a 'busy' answer means this page's preempt is stopping the
  // other build, and the page says so instead of asking for «احسب» again.
  preempted: false,
```

(5) The end of `compute()`. Find

```js
  showLoad(() => t(currentLang, 'agents.load.networks'), 0);
  renderAll();
  poll(token, true);
}
```

and replace it with

```js
  showLoad(() => t(currentLang, 'agents.load.networks'), 0);
  renderAll();
  state.preempted = true;
  poll(token, true);
}
```

(6) `poll()`'s network-failure catch. Find

```js
        if (token !== state.loadToken) return;
        // Frames already received stay playable; the retry resumes from them.
        showLoad(null);
```

and replace it with

```js
        if (token !== state.loadToken) return;
        // The preempt may never have reached the server: a retry that finds
        // another build running must ask for «احسب» again (M1's busy text).
        state.preempted = false;
        // Frames already received stay playable; the retry resumes from them.
        showLoad(null);
```

(7) The top of `handle()`. Find

```js
function handle(status, body) {
  if (status === 404) {
```

and replace it with

```js
function handle(status, body) {
  if (!(status === 200 && body?.status === 'busy')) state.preempted = false;
  if (status === 404) {
```

(8) The busy branch of `handle()`. Find

```js
  else if (body.status === 'busy') {
    const a = body.active || {};
    showLoad(() => t(currentLang, 'agents.load.busy', { runs: a.runs, seed: a.seed, ep: a.ep }), 0);
  } else if
```

and replace it with

```js
  else if (body.status === 'busy') {
    const a = body.active || {};
    // After this page's own preempt the other build is being stopped (the
    // store cancels it on that request); only without one is «احسب» needed.
    const stopping = state.preempted;
    showLoad(() => (stopping
      ? t(currentLang, 'agents.load.stopping', { runs: a.runs, seed: a.seed, ep: a.ep })
      : t(currentLang, 'agents.load.busy', { runs: a.runs, seed: a.seed, ep: a.ep })), 0);
  } else if
```

(9) After `currentVerdict()`. Find

```js
function currentVerdict() {
  return currentExperiment()?.verdict ?? state.meta?.verdict ?? null;
}
```

and replace it with

```js
function currentVerdict() {
  return currentExperiment()?.verdict ?? state.meta?.verdict ?? null;
}
function currentProtocol() {
  return state.meta?.protocol ?? currentPair()?.protocol ?? currentExperiment()?.protocol ?? null;
}
// The i18n key naming lane j's car. Phase D's blind car may have memorised its
// one road (results/PHASE_D_RESULT.txt:33-40), so it is never called blind
// alone: every place that names a car calls this, never a fixed key.
function laneLabel(j) {
  return j === 0 ? 'agents.car.sighted' : blindLabelKey(currentProtocol());
}
```

(10) The budget line in `renderPicker()`. Find

```js
    line.appendChild(el('span', '', `${t(currentLang, LANE_LABEL[i])} · ${t(currentLang, 'agents.pick.budget', { budget: budgetSteps(agent.budget_line) })}`));
```

and replace it with

```js
    line.appendChild(el('span', '', `${t(currentLang, laneLabel(i))} · ${t(currentLang, 'agents.pick.budget', { budget: budgetSteps(agent.budget_line) })}`));
```

(11) The scored line in `renderVerdict()`. Find

```js
    li.appendChild(el('span', '', `${t(currentLang, LANE_LABEL[i])} · ${status}`));
```

and replace it with

```js
    li.appendChild(el('span', '', `${t(currentLang, laneLabel(i))} · ${status}`));
```

(12) The scene labels in `renderLaneLabels()`. Find

```js
  setText($('lane-sighted-label'), m ? t(currentLang, 'agents.car.sighted') : '');
  setText($('lane-blind-label'), m ? t(currentLang, BLIND_LABEL[m.protocol] || 'agents.car.blind') : '');
```

and replace it with

```js
  setText($('lane-sighted-label'), m ? t(currentLang, laneLabel(0)) : '');
  setText($('lane-blind-label'), m ? t(currentLang, laneLabel(1)) : '');
```

(13) The blind line in `renderSeen()`. Find

```js
  setText($('seen-blind'), blind ? t(currentLang, 'agents.seen.blind', { zeros }) : '');
```

and replace it with

```js
  // Phase D's blind car saw zeros too, on the one road it was trained and
  // scored on; the caveat is cited from the verdict's own not_blind line.
  const text = currentProtocol() === 'phase-d'
    ? t(currentLang, 'agents.seen.blind_phase_d', { zeros, cite: notBlindCite(currentVerdict()) })
    : t(currentLang, 'agents.seen.blind', { zeros });
  setText($('seen-blind'), blind ? text : '');
```

(14) The stopped lanes in `renderStopped()`. Find

```js
  const parts = LANE_LABEL.map((label, j) => {
    const k = laneStoppedAt(state.frames, j);
    return k === null ? null : `${t(currentLang, label)}: ${t(currentLang, 'agents.lane.stopped', { k })}`;
  }).filter(Boolean);
```

and replace it with

```js
  const parts = LANES.map((_, j) => {
    const k = laneStoppedAt(state.frames, j);
    return k === null ? null : `${t(currentLang, laneLabel(j))}: ${t(currentLang, 'agents.lane.stopped', { k })}`;
  }).filter(Boolean);
```

Then check that nothing still names the old constants:

```bash
grep -n "LANE_LABEL\|BLIND_LABEL" app/static/sim/agents.mjs || echo "none left"
```

Expected: `none left`.

- [ ] **Step 4: Run to verify it passes**

```bash
node --test "app/static/sim/agents-page-nav.test.mjs" 2>&1 | grep -E "^✖|^ℹ (tests|pass|fail)"
node --test "app/static/sim/*.test.mjs" 2>&1 | grep -E "^✖|^ℹ (tests|pass|fail|skipped)"
$PY -m app.test_agents PageTests 2>&1 | grep -E "^Ran|^OK|FAILED|Error"
```

Expected (observed on the 28 Sep prototype):
- **Nav test:** `ℹ tests 9`, `ℹ pass 9`, `ℹ fail 0`.
- **Node glob:** `ℹ fail 0`, with a total two more than after Task 7 (97 on the prototype).
- **PageTests:** `OK`, with the same count as in Task 7.
  - `test_every_car_is_read_through_carOf` still finds exactly one `.cars`.
  - `agents-page.test.mjs` shows that every literal key exists and every `t()` fills exactly its placeholders. That includes `stopping`'s `{runs, seed, ep}` and `seen.blind_phase_d`'s `{zeros, cite}`.

- [ ] **Step 5: Commit**

```bash
git add app/static/sim/agents.mjs app/static/sim/agents-page-nav.test.mjs
$PY -m app.test_replay > "$SCRATCH/m2t8_replay.txt" 2>&1; tail -1 "$SCRATCH/m2t8_replay.txt"
node --test "app/static/sim/*.test.mjs" > "$SCRATCH/m2t8_node.txt" 2>&1; grep -E "^ℹ (tests|pass|fail)" "$SCRATCH/m2t8_node.txt"
{
  printf '%s\n' "Agent replay M2 task 8: Phase D's blind car named with its caveat, and a stopping build said so" "" \
    "Every place that names a car goes through laneLabel(j): the scene label, the" \
    "picker's budget line, the verdict box's scored line and the stopped-lane line" \
    "(M1 left renderStopped on LANE_LABEL[1]). Phase D's blind car reads 'does not" \
    "see the road ahead, but may have memorised it: the same road in every" \
    "episode', and its panel line cites results/PHASE_D_RESULT.txt:33-40 from the" \
    "verdict's own not_blind line. After this page's own preempt a 'busy' answer" \
    "says the previous computation is being stopped; M1's 'press Compute to stop" \
    "it' appears only when the preempt may never have arrived."
  printf '\n$ node --test "app/static/sim/*.test.mjs"   (summary)\n'
  grep -E "^ℹ " "$SCRATCH/m2t8_node.txt"
  printf '\n$ python -m app.test_replay\n'
  cat "$SCRATCH/m2t8_replay.txt"
  printf '\nCo-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>\n'
} > "$SCRATCH/m2t8_msg.txt"
git commit -F "$SCRATCH/m2t8_msg.txt"
git log --oneline -1
```

Expected: `app.test_replay` still ends with `49 of 49 checks pass`; read the count from the run. This task adds no tracked file, so `verify_docs.py` is not needed here; it runs in Task 10.

---


---

### Task 9: fe-page: the replay lab links to /agents right after its first nav link, and the lab launcher names /agents

**Files:**
- Modify: `app/static/simulation.html:39` (one `<a>` after the first nav link)
- Modify: `app/start-simulation.ps1:49-50` (banner lines only; the interpreter line `:52` is unchanged)
- Modify: `app/test_agents.py` (two PageTests tests, inserted after Task 7's test)
- Test: `app/test_agents.py` `PageTests.test_the_lab_links_to_agents_where_phones_keep_it`, `PageTests.test_the_lab_launcher_names_the_agents_page`

**Interfaces:**
- Consumes:
  - The lab's nav at `simulation.html:39`: `/simulation` (active), `/`, `/review`.
  - The phone rule in `sim/style.css`. In its `@media(max-width:760px)` block it reads `.brand small,.readonly,.topbar nav a:last-child{display:none}`.
  - `nav.agents` in `i18n.mjs:57` and `:275` («الوكلاء» / 'Agents'). The lab's `main.mjs` already translates it through `applyTranslations`.
  - The launcher banner.
- Produces:
  - The `simulation.html` nav reads `/simulation` (active), `/agents` (`data-i18n="nav.agents"`, not active), `/`, `/review`.
  - `start-simulation.ps1` prints `agent replay   ->  http://localhost:$Port/agents`. When its own `python` has no stable-baselines3, it also prints a note: `/agents` lists the experiments but answers 503 for an episode. That is the repository `.venv`'s case (measured 28 Sep: exit 1).

**Notes:**
- The launcher's new lines are ASCII only, because Windows PowerShell 5.1 reads a `.ps1` without a BOM as ANSI.
- The launcher's `python` stays as it is, because `/simulation` must start exactly as it does today. The page itself says «لا يمكن التشغيل: مكتبة stable-baselines3 غير مثبّتة» under the picker as soon as the catalog reports `sb3: false` (Task 7).
- Task 10 records this ruling in the design: the banner was fixed, the interpreter was not.

- [ ] **Step 1: Write the failing tests**

Begin every Bash block of this task with Task 7's environment block.

In `app/test_agents.py`, find the line `        self.assertFalse("pushState" in page, "the address is replaced, never pushed")`, the last line of Task 7's test. Insert these two methods right after it, with one blank line before them:

```python
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
```

- [ ] **Step 2: Run them to verify they fail**

```bash
$PY -m app.test_agents PageTests.test_the_lab_links_to_agents_where_phones_keep_it PageTests.test_the_lab_launcher_names_the_agents_page 2>&1 | grep -E "AssertionError|^Ran|^FAILED"
```

Expected (observed on the 28 Sep prototype):
- `AssertionError: Lists differ: ['/simulation', '/', '/review'] != ['/simulation', '/agents', '/', '/review']`
- `AssertionError: False is not true : the banner does not name /agents`
- `Ran 2 tests` and `FAILED (failures=2)`

- [ ] **Step 3: Implement**

**3a.** In `app/static/simulation.html`, find `<a class="active" href="/simulation" data-i18n="nav.simulation">مختبر الرحلة</a><a href="/" data-i18n="nav.monitor">` and replace it with

```html
<a class="active" href="/simulation" data-i18n="nav.simulation">مختبر الرحلة</a><a href="/agents" data-i18n="nav.agents">الوكلاء</a><a href="/" data-i18n="nav.monitor">
```

Nothing else in the file changes.

**3b.** In `app/start-simulation.ps1`, find

```powershell
Write-Host '  Picking a different drive cancels the one being computed.'
Write-Host ''
```

and replace it with

```powershell
Write-Host '  Picking a different drive cancels the one being computed.'
Write-Host ''
Write-Host '  agent replay   ->  ' -NoNewline
Write-Host "http://localhost:$Port/agents"
# /agents computes an episode with stable-baselines3 and torch. Say so here
# when THIS python cannot: the page still lists every experiment, and its
# episode route answers 503. A native command's exit code never throws under
# $ErrorActionPreference 'Stop' in Windows PowerShell 5.1, so it is read here.
python -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('stable_baselines3') else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host '  Note: this python has no stable-baselines3, so /agents lists the'
    Write-Host '  experiments but cannot compute an episode (it answers 503). To'
    Write-Host '  compute one, start the server with an interpreter that has it:'
    Write-Host '      <that python> -m app.server --simulation'
}
Write-Host ''
```

The last line of the file, `python -m app.server --simulation --http-port $Port`, is unchanged.

- [ ] **Step 4: Run to verify they pass**

```bash
$PY -m app.test_agents PageTests 2>&1 | grep -E "^Ran|^OK|FAILED|Error"
$PY -m app.test_simulation 2>&1 | tail -3
node --test "app/static/sim/*.test.mjs" 2>&1 | grep -E "^✖|^ℹ (tests|pass|fail)"
```

Expected (observed on the 28 Sep prototype):
- **PageTests:** `OK`, with two more tests than after Task 8 (`Ran 8 tests` if Task 6 added one).
- **`app.test_simulation`:** `Ran 15 tests` and `OK`. That is the M1 baseline, and its page test passes against the edited `simulation.html`. Read the count from the run.
- **Node glob:** unchanged from Task 8, `ℹ fail 0`.

Then look at the banner itself. The launcher starts the lab server with its own `python`, so this check runs it for a few seconds and then stops it. PowerShell tool calls do not keep `$env:` variables from one call to the next, so the whole check is ONE command. Fill in `SCRATCH_W` with the same scratchpad directory, written in `C:\...` form.

```powershell
$env:SCRATCH_W = 'C:\Users\admin\AppData\Local\Temp\claude\<project>\<session>\scratchpad'; $p = Start-Process powershell -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','app\start-simulation.ps1','-SkipVendor','-Port','8791' -WorkingDirectory (Get-Location).Path -RedirectStandardOutput "$env:SCRATCH_W\m2t9_banner.txt" -PassThru -WindowStyle Hidden; Start-Sleep -Seconds 8; try { Stop-Process -Id $p.Id -Confirm:$false -ErrorAction Stop } catch {}; try { Get-NetTCPConnection -LocalPort 8791 -State Listen -ErrorAction Stop | ForEach-Object { Stop-Process -Id $_.OwningProcess -Confirm:$false } } catch {}; Get-Content "$env:SCRATCH_W\m2t9_banner.txt"
```

The second `try` stops the launcher's python server, which outlives the PowerShell that started it. Both are wrapped because a cmdlet that finds nothing to stop would otherwise report exit 1.

Expected output, as observed on the 28 Sep prototype, where bare `python` was the repository `.venv`: the lab's own banner, then

```
  agent replay   ->  http://localhost:8791/agents
  Note: this python has no stable-baselines3, so /agents lists the
  experiments but cannot compute an episode (it answers 503). To
  compute one, start the server with an interpreter that has it:
      <that python> -m app.server --simulation
```

- [ ] **Step 5: Commit**

```bash
git add app/static/simulation.html app/start-simulation.ps1 app/test_agents.py
$PY verify_docs.py 2>&1 | tail -1
$PY -m app.test_replay > "$SCRATCH/m2t9_replay.txt" 2>&1; tail -1 "$SCRATCH/m2t9_replay.txt"
$PY -m app.test_simulation > "$SCRATCH/m2t9_sim.txt" 2>&1; tail -3 "$SCRATCH/m2t9_sim.txt"
{
  printf '%s\n' "Agent replay M2 task 9: the replay lab links to /agents, where phones keep it" "" \
    "Jad found on 28 Sep that the lab had no way to /agents. simulation.html's nav" \
    "gains one link, /agents (nav.agents), right AFTER its first link: the lab's" \
    "phone rule hides .topbar nav a:last-child below 760 px. Nothing else in the" \
    "lab page changes and no lab test file changes. app/start-simulation.ps1 now" \
    "prints the /agents URL and, when its own python has no stable-baselines3 (the" \
    "repository .venv), says /agents will list the experiments but answer 503 for" \
    "an episode. Its interpreter line is unchanged."
  printf '\n$ python -m app.test_simulation\n'
  cat "$SCRATCH/m2t9_sim.txt"
  printf '\n$ python -m app.test_replay\n'
  cat "$SCRATCH/m2t9_replay.txt"
  printf '\nCo-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>\n'
} > "$SCRATCH/m2t9_msg.txt"
git commit -F "$SCRATCH/m2t9_msg.txt"
git log --oneline -1
```

Expected:
- `verify_docs.py`'s last line starts `All ` and ends `figure mentions scanned in the documents).` Read the counts. If it fails, a new docstring names a retired figure: reword it and run again.
- `app.test_replay` ends with `49 of 49 checks pass`.
- `app.test_simulation` shows `OK`.

---


---

### Task 10: M2 verification: every suite, --full with the Phase D proof, the browser at 1440 and 390 px starting from the nav link with nothing selected, one pair from each experiment, the misreading table, the lab link on a phone, design amendments, milestone commit

**Files:**
- Modify: `docs/superpowers/specs/2026-09-26-agent-replay-design.md`. The amendments go after these anchors:
  - `:259` (§4 Runnability);
  - `:276` (§4 verdicts);
  - `:292` (§4 short lines);
  - `:305` (§4 catalog);
  - `:352` (§5 colours);
  - `:376` (§6 picker);
  - `:671` (§10, the M1 Verify note on the launcher).

  A walkthrough-log row goes after `:773` (28 Sep).
- Scratch only, never in the repository: `$SCRATCH/m2-browser-check.mjs`, `$SCRATCH/m2_amend_design.py`, `$SCRATCH/m2-out/`, `$SCRATCH/m2-misreading.txt`, and every other `$SCRATCH/m2_*.txt` output.

**Interfaces:**
- Consumes:
  - Everything from Tasks 1 to 9.
  - `ProofTests.test_phase_d_pair_full` (`--full`: prints `Phase D == proof PROVEN on <device>`).
  - M1's approach to the browser check. A Node 24 script drives the installed Chrome over the DevTools protocol with the built-in `fetch` and `WebSocket`. Before loading, it writes the theme and language to the page's two localStorage keys.
  - Design §6's "Misreading → prevention" table and "Layout".
- Produces:
  - A milestone commit on `JMF-2340550-sep17` whose message carries every suite's output. The message also lists the M1 left-for-later items that M2 took. One sentence says every other item stays deferred, and names the ones in code M2 edits, so none of them lives only in a scratch file.
  - The design amendments and one walkthrough-log row, in the same commit.
  - Any fix found here gets its own commit first, with the same outputs.

This task verifies rather than builds, so its steps run suites and checks instead of a red/green cycle. Every expected output below was observed on the 28 Sep prototype, which had Tasks 1 to 9 patched in. Read every count from your own run. Begin every Bash block with Task 7's environment block.

- [ ] **Step 1: Run every suite**

```bash
$PY -m app.test_agents > "$SCRATCH/m2_agents.txt" 2>&1; grep -E "^Ran|^OK|FAILED|PROVEN|UNPROVEN" "$SCRATCH/m2_agents.txt"
```

Use a timeout of 600000 ms.

Expected:
- `OK`; the `(skipped=1)` is the Phase D proof, which runs only under `--full`.
- The line `== proof PROVEN: device cuda, torch 2.11.0+cu128, sb3 2.9.0, ...`.
- `Ran N tests`, where N is M1's 38 plus the tests Tasks 1 to 9 added.

Also confirm that spec tests 6 to 13 ran and passed:

```bash
grep -E "test_catalog_real_tree|test_discover_synthetic|test_catalog_synthetic|test_d2_and_phase_d_verdicts|test_verdict_when_an_anchor_or_a_file_is_gone|test_preempt_answered_from_the_cache|test_routes_only_under_simulation|test_new_modules_cannot_write|test_page_assets_ids|test_the_lab_links_to_agents|test_no_network_imports_in_app" "$SCRATCH/m2_agents.txt"
```

Expected: every one of those names ends in `... ok`. Test 11 takes its snapshot in setUpModule and tearDownModule, and raises if anything was written.

The `--full` run adds the Phase D pair to the proof and takes longer than one foreground Bash call allows. Start it with the Bash tool's `run_in_background`, as one self-contained command:

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH='/c/Users/admin/AppData/Local/Temp/claude/<project>/<session>/scratchpad'; cd "/c/Users/admin/Documents/graduation project/GRAD-project" && "$PY" -m app.test_agents --full > "$SCRATCH/m2_agents_full.txt" 2>&1
```

When its completion notification arrives:

```bash
grep -E "^Ran|^OK|FAILED|PROVEN" "$SCRATCH/m2_agents_full.txt"
```

Expected: `OK` and `Phase D == proof PROVEN on cuda`. M1 measured this pair at about 2.5 minutes.

```bash
$PY -m app.test_simulation > "$SCRATCH/m2_sim.txt" 2>&1; tail -3 "$SCRATCH/m2_sim.txt"
$PY -m app.test_replay > "$SCRATCH/m2_replay.txt" 2>&1; tail -1 "$SCRATCH/m2_replay.txt"
$PY -m app.test_replay --full > "$SCRATCH/m2_replay_full.txt" 2>&1; tail -1 "$SCRATCH/m2_replay_full.txt"
node --test "app/static/sim/*.test.mjs" > "$SCRATCH/m2_node.txt" 2>&1; grep -E "^✖|^ℹ (tests|pass|fail|skipped)" "$SCRATCH/m2_node.txt"
```

Expected:

| suite | expected |
|---|---|
| `app.test_simulation` | `Ran 15 tests`, `OK` |
| `app.test_replay` | `49 of 49 checks pass` |
| `app.test_replay --full` | its own count; M1 recorded 59 of 59 |
| node glob | `ℹ fail 0` with no `✖` line, and `ℹ skipped 0` on this machine because `app/node_modules/three` is present (97 tests on the prototype) |

- [ ] **Step 2: Start the server and time the catalog**

Start the server with the Bash tool's `run_in_background`. A background call is a fresh shell too, so the command defines everything it uses:

```bash
export PY=/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 SCRATCH='/c/Users/admin/AppData/Local/Temp/claude/<project>/<session>/scratchpad'; cd "/c/Users/admin/Documents/graduation project/GRAD-project" && "$PY" -m app.server --simulation --http-port 8765 > "$SCRATCH/m2_server.txt" 2>&1
```

Then, in the foreground:

```bash
for i in $(seq 1 40); do c=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 http://127.0.0.1:8765/agents); [ "$c" = "200" ] && break; sleep 1; done; echo "agents $c"
curl -s -o /dev/null -w "catalog %{http_code} %{time_total}s %{size_download}B\n" --max-time 30 http://127.0.0.1:8765/api/agents/catalog | tee "$SCRATCH/m2_catalog_timing.txt"
curl -s -D - -o /dev/null http://127.0.0.1:8765/api/agents/catalog | grep -i "cache-control"
curl -s -o /dev/null -w "POST catalog %{http_code}\n" -X POST http://127.0.0.1:8765/api/agents/catalog
git status --short
```

Expected:
- `agents 200`.
- `catalog 200` in about a quarter of a second. On a fresh server the prototype measured 0.25 s and 0.26 s, 28406 bytes; Task 3 measured 0.2 to 0.3 s. Record the time.
- `cache-control: no-store`.
- `POST catalog 405`.
- `git status --short` prints nothing.

- [ ] **Step 3: Write the browser check**

Write `$SCRATCH/m2-browser-check.mjs` with the Write tool. It holds no backslash-u escape; the invisible code points are built with `String.fromCodePoint`. What the script does:
- every view computes a C4 episode and a Phase D episode;
- the phone view also checks that nothing scrolls sideways;
- the first view also computes D2, reloads the page, cuts back an address and switches the pair mid-build.

```js
// M2 browser check (scratchpad, NOT repository code). Drives the installed
// Chrome over the DevTools protocol against a running `-m app.server
// --simulation`, starting where Jad started on 28 Sep: the replay lab, then
// its nav link to /agents with nothing selected. Every view computes a C4 and
// a Phase D episode; the first view also D2, a reload and a mid-build switch;
// the phone view also checks that nothing scrolls sideways. Prints one
// PASS/FAIL line per check, writes report.json, texts-<view>-*.json and
// clipped screenshots to OUT.
//   node m2-browser-check.mjs [base-url] [out-dir]
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const BASE = process.argv[2] || 'http://127.0.0.1:8000';
const OUT = process.argv[3] || '.';
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const PORT = 9337;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const LRI = String.fromCodePoint(0x2066);
const PDI = String.fromCodePoint(0x2069);
const NNBSP = String.fromCodePoint(0x202f);
// What the page says, by language, where a check reads words.
const WORDS = {
  ar: { same: 'الطريق نفسه', caveat: 'قد يحفظه', notThis: 'ليست هذه الحلقة' },
  en: { same: 'the same road', caveat: 'memorised', notThis: 'not this episode' },
};

mkdirSync(OUT, { recursive: true });
mkdirSync(join(OUT, 'chrome-profile-m2'), { recursive: true });
const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${join(OUT, 'chrome-profile-m2')}`, '--no-first-run', '--use-angle=swiftshader',
  '--enable-unsafe-swiftshader', '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
for (let i = 0; i < 400; i++) { try { await fetch(`http://127.0.0.1:${PORT}/json/version`); break; } catch { await sleep(100); } }

const report = { base: BASE, checks: [], timings: {} };
function check(view, name, ok, detail = '') {
  report.checks.push({ view, name, ok: Boolean(ok), detail: String(detail).slice(0, 300) });
  console.log(`${ok ? 'PASS' : 'FAIL'}  [${view}] ${name}${ok ? '' : `  -- ${detail}`}`);
}

async function open({ width, height, mobile = false, dark = false }) {
  const target = await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: 'PUT' })).json();
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise(r => ws.addEventListener('open', r, { once: true }));
  let id = 0;
  const pending = new Map();
  ws.addEventListener('message', ev => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
  });
  const send = (method, params = {}) => new Promise((resolve, reject) => {
    id += 1;
    pending.set(id, m => (m.error ? reject(new Error(`${method}: ${m.error.message}`)) : resolve(m.result)));
    ws.send(JSON.stringify({ id, method, params }));
  });
  for (const m of ['Runtime.enable', 'Page.enable']) await send(m);
  await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 2, mobile });
  await send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-color-scheme', value: dark ? 'dark' : 'light' }] });
  const page = {
    async goto(url, settle = 2000) { await send('Page.navigate', { url }); await sleep(settle); },
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
    async clip(selector, name) {
      const box = await page.eval(`(() => { const e = document.querySelector(${JSON.stringify(selector)}); if (!e) return null;
        const r = e.getBoundingClientRect(); return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: r.height }; })()`);
      if (!box || !box.width || !box.height) { console.log(`      no box for ${selector}`); return; }
      const r = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true, clip: { ...box, scale: 1 } });
      writeFileSync(join(OUT, name), Buffer.from(r.data, 'base64'));
      console.log(`      clip ${join(OUT, name)}`);
    },
    close() { ws.close(); },
  };
  return page;
}

// What the page shows, read from the DOM only.
const $t = id => `(document.getElementById(${JSON.stringify(id)})?.textContent ?? '')`;
const choose = (id, value) => `(() => { const s = document.getElementById(${JSON.stringify(id)});
  s.value = ${JSON.stringify(String(value))}; s.dispatchEvent(new Event('change')); return s.value; })()`;
const options = id => `[...document.querySelectorAll('#${id} option')].map(o => ({ value: o.value, text: o.textContent, disabled: o.disabled }))`;
const requests = `performance.getEntriesByType('resource').map(e => { const u = new URL(e.name); return u.pathname + u.search; })`;
const ready = `document.getElementById('loading').hidden && !document.getElementById('play').disabled`;
const seekTo = s => `(() => { const e = document.getElementById('seek'); e.value = '${s}'; e.dispatchEvent(new Event('input')); })()`;
const fits = `({ scroll: document.documentElement.scrollWidth, inner: innerWidth })`;
const texts = `(() => {
  const t = s => [...document.querySelectorAll(s)].map(e => e.textContent.trim());
  return {
    search: location.search, badge: t('#sim-badge'), strip: t('#strip-verdict'),
    experiment: t('#pick-experiment option'), pair: t('#pick-pair option'), episode: t('#pick-episode option').slice(0, 3),
    pairNote: t('#pick-pair-note'), episodeNote: t('#pick-episode-note'), pickNote: t('#pick-note'),
    refused: t('#pick-refused'),
    verdictShort: t('#verdict-short'), cells: t('#verdict-cells li'), cites: t('#verdict-lines figcaption'),
    scored: t('#verdict-scored li'), lanes: t('.lane-label'), seen: t('.seen'), stopped: t('#lane-stopped'),
    heading: t('#pause-heading'), climb: t('.profile-climb-label'), rise: t('#rise-caption'),
    ve: t('#profile-ve'), dt: t('#dt-caption'), weights: t('#weights-line'), legend: t('#same-place-legend'),
    slope: t('#chase-caption'), illustration: t('#illustration-note'), caveat: t('#model-caveat'),
    device: t('#device-line'), torque: t('.torque-row'), markers: document.querySelectorAll('#profile .profile-car').length,
    held: [...document.querySelectorAll('.held-line')].filter(e => !e.hidden).map(e => e.textContent),
    maps: [...document.querySelectorAll('.map-line')].filter(e => !e.hidden).map(e => e.textContent),
    tickNotes: t('.tick-note'),
    winner: /winner|فائز|فاز|الأفضل|better|أفضل/.test(document.body.innerText),
  };
})()`;

async function fromTheLab(page, view, phone) {
  await page.goto(`${BASE}/simulation`, 3000);
  const nav = await page.eval(`[...document.querySelectorAll('.topbar nav a')].map(a => ({ href: a.getAttribute('href'),
    shown: getComputedStyle(a).display !== 'none' && a.getBoundingClientRect().width > 0, text: a.textContent.trim() }))`);
  check(view, 'the lab nav reads /simulation, /agents, /, /review', nav.map(a => a.href).join(' ') === '/simulation /agents / /review', JSON.stringify(nav));
  check(view, 'the lab\'s /agents link is visible', nav.find(a => a.href === '/agents')?.shown, JSON.stringify(nav));
  if (phone) check(view, 'on a phone the lab hides its LAST link, not /agents', !nav.at(-1).shown && nav.at(-1).href === '/review', JSON.stringify(nav));
  await page.clip('.topbar', `m2-${view}-lab-nav.png`);
  await page.eval(`document.querySelector('.topbar nav a[href="/agents"]').click()`);
  await sleep(2500);
  await page.until(`document.querySelectorAll('#pick-experiment option').length > 1`, 15000);
  const state = await page.eval(`({ path: location.pathname, search: location.search,
    values: ['pick-experiment', 'pick-pair', 'pick-episode'].map(id => document.getElementById(id).value),
    disabled: ['pick-experiment', 'pick-pair', 'pick-episode', 'compute'].map(id => document.getElementById(id).disabled),
    prompt: !document.getElementById('scene-prompt').hidden, requests: ${requests} })`);
  check(view, 'the nav link opens /agents with an empty address', state.path === '/agents' && state.search === '', JSON.stringify(state));
  check(view, 'nothing is selected', state.values.every(v => v === ''), JSON.stringify(state.values));
  check(view, 'only the experiment select is enabled; «احسب» is disabled', JSON.stringify(state.disabled) === '[false,true,true,true]', JSON.stringify(state.disabled));
  check(view, 'the catalog is requested and no episode is', state.requests.some(r => r === '/api/agents/catalog') && !state.requests.some(r => r.startsWith('/api/agents/episode')), JSON.stringify(state.requests));
  check(view, 'the scene asks for a choice', state.prompt);
  const exp = await page.eval(options('pick-experiment'));
  check(view, 'four experiments listed after the placeholder', exp.map(o => o.value).join(',') === ',runs,runs_c4,runs_d2,runs_sixspeed_18sep', JSON.stringify(exp.map(o => o.value)));
  const six = exp.find(o => o.value === 'runs_sixspeed_18sep');
  check(view, 'sixspeed is greyed, naming no meta.json', six?.disabled && /no meta\.json/.test(six.text), JSON.stringify(six));
  await page.eval(`document.getElementById('pick-refused').open = true`);
  const refused = await page.eval($t('pick-refused'));
  check(view, 'the refused list names BOTH sixspeed arms and why', refused.includes('sighted_seed0: incompatible -- no meta.json')
    && refused.includes('blind_seed0: incompatible -- no meta.json'), refused);
  await page.clip('.picker-panel', `m2-${view}-picker-empty.png`);
}

async function computeEpisode(page, view, runs, seed, ep) {
  await page.eval(choose('pick-experiment', runs));
  await page.eval(choose('pick-pair', seed));
  await page.eval(choose('pick-episode', ep));
  const search = await page.eval('location.search');
  check(view, `the address follows the choice (${runs}/${seed}/${ep})`, search === `?runs=${runs}&seed=${seed}&ep=${ep}`, search);
  const t0 = Date.now();
  await page.eval(`document.getElementById('compute').click()`);
  const titles = new Set();
  let firstFrame = null;
  while (Date.now() - t0 < 150000) {
    const s = await page.eval(`({ title: ${$t('load-title')}, heading: ${$t('pause-heading')}, ready: ${ready} })`);
    if (s.title) titles.add(s.title);
    if (firstFrame === null && s.heading !== '—') firstFrame = Date.now() - t0;
    if (s.ready) break;
    await sleep(100);
  }
  report.timings[`${view} ${runs}/${seed}/${ep}`] = { first_frame_ms: firstFrame, ready_ms: Date.now() - t0 };
  check(view, `${runs}/${seed}/${ep} computed to the end`, await page.eval(ready));
  return [...titles];
}

// Phase D, in every view: one road, and the blind car's caveat wherever it is named.
async function phaseD(page, view, lang) {
  const words = WORDS[lang];
  await page.eval(choose('pick-experiment', 'runs'));
  await page.eval(choose('pick-pair', 0));
  const pdEpisodes = await page.eval(options('pick-episode'));
  check(view, `every Phase D episode says "${words.same}"`, pdEpisodes.slice(1).every(o => o.text.includes(words.same)), pdEpisodes[1]?.text);
  const note = await page.eval($t('pick-episode-note'));
  check(view, 'the same-road note names 180 s and 12.0 %', note.includes('180') && note.includes('12.0'), note);
  await computeEpisode(page, view, 'runs', 0, 1);
  await page.eval(seekTo(200.5));
  await sleep(900);
  const pd = await page.eval(texts);
  writeFileSync(join(OUT, `texts-${view}-phase-d.json`), JSON.stringify(pd, null, 1));
  check(view, 'the badge reads 12.0', pd.badge.join(' ').includes('12.0'), pd.badge);
  check(view, 'the profile climb label says 180', pd.climb.join(' ').includes('180'), pd.climb);
  check(view, 'the blind car\'s scene label names the caveat', pd.lanes.some(s => s.includes(words.caveat)), pd.lanes);
  check(view, 'the blind panel line cites PHASE_D_RESULT.txt:33-40', pd.seen.some(s => s.includes(words.caveat) && s.includes('results/PHASE_D_RESULT.txt:33-40')), pd.seen);
  check(view, 'the scored line names the caveat', pd.scored.some(s => s.includes(words.caveat)), pd.scored);
  check(view, 'the blind arm\'s budget line names the caveat', pd.pickNote.join(' ').includes(words.caveat), pd.pickNote);
  check(view, 'Phase D cells: NOT SIGNIFICANT and INCONCLUSIVE (post-hoc)', pd.cells.join('|').includes('NOT SIGNIFICANT') && pd.cells.join('|').includes('INCONCLUSIVE (post-hoc)'), pd.cells);
  for (const cite of ['results/PHASE_D_RESULT.txt:26-31', 'results/PHASE_D_RESULT.txt:33-40', 'results/PHASE_D2_RESULT.txt:65-76']) {
    check(view, `Phase D quotes ${cite}`, pd.cites.includes(cite), pd.cites);
  }
  check(view, 'no winner is named', !pd.winner);
  const inside = await page.eval(`(() => {
    const v = document.querySelector('.chase-view').getBoundingClientRect();
    const l = document.getElementById('lane-blind-label').getBoundingClientRect();
    return { ok: l.width > 0 && l.left >= v.left - 0.5 && l.right <= v.right + 0.5 && l.top >= v.top - 0.5 && l.bottom <= v.bottom + 0.5,
      view: [v.left, v.top, v.right, v.bottom].map(Math.round), label: [l.left, l.top, l.right, l.bottom].map(Math.round) };
  })()`);
  check(view, 'the blind car\'s long label stays inside the chase view', inside.ok, JSON.stringify(inside));
  await page.eval(`document.getElementById('verdict-more').open = true`);
  await sleep(300);
  await page.clip('.agents-col-main > :first-child', `m2-${view}-phase-d-chase.png`);
  await page.clip('.picker-panel', `m2-${view}-phase-d-picker.png`);
  await page.clip('#verdict', `m2-${view}-phase-d-verdict.png`);
  await page.clip('.pause-panel', `m2-${view}-phase-d-pause.png`);
}

// The phone view: nothing may scroll sideways, with an episode on screen and
// with each experiment's verdict box, its quotes and the refused list open.
async function phoneFits(page, view) {
  await page.eval(`document.getElementById('verdict-more').open = true; document.getElementById('pick-refused').open = true`);
  await sleep(300);
  let w = await page.eval(fits);
  check(view, 'no sideways scroll with the Phase D episode on screen', w.scroll <= w.inner, JSON.stringify(w));
  for (const runs of ['runs', 'runs_c4', 'runs_d2']) {
    await page.eval(choose('pick-experiment', runs));
    await sleep(500);
    w = await page.eval(fits);
    check(view, `no sideways scroll with ${runs} chosen, its quotes and the refused list open`, w.scroll <= w.inner, JSON.stringify(w));
  }
  await page.clip('.picker-panel', `m2-${view}-picker-refused-open.png`);
  await page.clip('#verdict', `m2-${view}-d2-verdict.png`);
}

try {
  const views = [
    { name: '1440-light-ar', width: 1440, height: 900, lang: 'ar', full: true },
    { name: '390-dark-ar', width: 390, height: 844, mobile: true, dark: true, lang: 'ar' },
    { name: '1440-dark-en', width: 1440, height: 900, dark: true, lang: 'en' },
  ];
  for (const view of views) {
    console.log(`\n== ${view.name}`);
    const page = await open(view);
    await page.goto(`${BASE}/simulation`, 1500);
    await page.eval(`localStorage.setItem('grad.sim.theme', '${view.dark ? 'dark' : 'light'}'); localStorage.setItem('grad.sim.lang', '${view.lang}')`);
    await fromTheLab(page, view.name, Boolean(view.mobile));

    // C4: eight pairs, the table row isolated left-to-right, the qualifier.
    await page.eval(choose('pick-experiment', 'runs_c4'));
    const pairs = await page.eval(options('pick-pair'));
    check(view.name, 'C4 lists eight pairs', pairs.length === 9, pairs.length);
    check(view.name, 'seed 0 quotes +360.6 inside a left-to-right isolate', pairs[1].text.includes(`${LRI}+360.6${PDI}`), JSON.stringify(pairs[1].text));
    const qualifier = await page.eval($t('pick-pair-note'));
    check(view.name, 'the pair qualifier says "not this episode"', qualifier.includes(WORDS[view.lang].notThis), qualifier);
    await page.clip('.picker-panel', `m2-${view.name}-picker-c4.png`);
    const c4titles = await computeEpisode(page, view.name, 'runs_c4', 5, 1);
    if (view.full) check(view.name, 'the first build said «تحميل الشبكتين…»', c4titles.some(s => s.includes('تحميل الشبكتين')), JSON.stringify(c4titles));
    await page.eval(seekTo(312.4));
    await sleep(900);
    writeFileSync(join(OUT, `texts-${view.name}-c4.json`), JSON.stringify(await page.eval(texts), null, 1));
    await page.clip('.agents-col-main > :first-child', `m2-${view.name}-c4-chase.png`);
    await page.clip('.pause-panel', `m2-${view.name}-c4-pause.png`);

    await phaseD(page, view.name, view.lang);
    if (view.mobile) await phoneFits(page, view.name);
    if (!view.full) { page.close(); continue; }

    // D2: INCONCLUSIVE with the C1 quote, 50 000 grouped with U+202F.
    await computeEpisode(page, view.name, 'runs_d2', 0, 2);
    const d2 = await page.eval(texts);
    writeFileSync(join(OUT, `texts-${view.name}-d2.json`), JSON.stringify(d2, null, 1));
    check(view.name, 'D2 cell: INCONCLUSIVE', d2.cells.some(s => s.startsWith('INCONCLUSIVE')), d2.cells);
    for (const cite of ['results/PHASE_D2_RESULT.txt:30-35', 'results/PHASE_D2_RESULT.txt:86-89']) {
      check(view.name, `D2 quotes ${cite}`, d2.cites.includes(cite), d2.cites);
    }
    check(view.name, 'D2 short line groups 50 000 with U+202F', d2.verdictShort.join('').includes(`50${NNBSP}000`), JSON.stringify(d2.verdictShort));
    check(view.name, 'D2 episode 2 climbs at 281 s', d2.climb.join(' ').includes('281'), d2.climb);
    await page.clip('#verdict-short', `m2-${view.name}-d2-short.png`);
    await page.clip('#scene-strip', `m2-${view.name}-d2-strip.png`);

    // Reload the D2 address: restored, nothing computing.
    await page.goto(`${BASE}/agents?runs=runs_d2&seed=0&ep=2`, 3000);
    const back = await page.eval(`({ values: ['pick-experiment', 'pick-pair', 'pick-episode'].map(id => document.getElementById(id).value),
      compute: !document.getElementById('compute').disabled, prompt: !document.getElementById('scene-prompt').hidden,
      requests: ${requests} })`);
    check(view.name, 'a reloaded address restores its three choices', JSON.stringify(back.values) === '["runs_d2","0","2"]', JSON.stringify(back.values));
    check(view.name, 'and computes nothing', back.compute && back.prompt && !back.requests.some(r => r.startsWith('/api/agents/episode')), JSON.stringify(back));

    // An address naming an episode that does not exist is cut back.
    await page.goto(`${BASE}/agents?runs=runs_d2&seed=0&ep=21`, 3000);
    const cut = await page.eval(`({ search: location.search, values: ['pick-experiment', 'pick-pair', 'pick-episode'].map(id => document.getElementById(id).value) })`);
    check(view.name, 'an address with ep=21 is cut back to ?runs=runs_d2&seed=0', cut.search === '?runs=runs_d2&seed=0' && JSON.stringify(cut.values) === '["runs_d2","0",""]', JSON.stringify(cut));

    // Switch the pair mid-build, then «احسب» over the build still running.
    await page.eval(choose('pick-experiment', 'runs_c4'));
    await page.eval(choose('pick-pair', 7));
    await page.eval(choose('pick-episode', 11));
    await page.eval(`document.getElementById('compute').click()`);
    await page.until(`${$t('pause-heading')} !== '—'`, 60000, 50);
    await page.eval(choose('pick-pair', 6));
    const cleared = await page.eval(`({ heading: ${$t('pause-heading')}, prompt: !document.getElementById('scene-prompt').hidden,
      loading: document.getElementById('loading').hidden, play: document.getElementById('play').disabled, search: location.search })`);
    check(view.name, 'switching the pair mid-build clears the scene and the panel', cleared.heading === '—' && cleared.prompt && cleared.loading && cleared.play, JSON.stringify(cleared));
    check(view.name, 'the address follows the switch', cleared.search === '?runs=runs_c4&seed=6&ep=11', cleared.search);
    await page.eval(`document.getElementById('compute').click()`);
    const seen = new Set();
    const t0 = Date.now();
    while (Date.now() - t0 < 5000) { const s = await page.eval($t('load-title')); if (s) seen.add(s); await sleep(40); }
    check(view.name, '«احسب» over the running build says it is stopping it', [...seen].some(s => s.includes('يُوقَف')), JSON.stringify([...seen]));
    await page.until(ready, 150000);
    page.close();
  }
} finally {
  writeFileSync(join(OUT, 'report.json'), JSON.stringify(report, null, 1));
  const failed = report.checks.filter(c => !c.ok).length;
  console.log(`\n${report.checks.length - failed} of ${report.checks.length} checks PASS; timings ${JSON.stringify(report.timings)}`);
  chrome.kill();
}
```

- [ ] **Step 4: Run the browser check and look at what it cannot judge**

The check computes seven episodes and takes about ten minutes. Run it with the Bash tool's `run_in_background`, as one self-contained command, and wait for its completion notification:

```bash
export SCRATCH='/c/Users/admin/AppData/Local/Temp/claude/<project>/<session>/scratchpad'; cd "$SCRATCH" && node m2-browser-check.mjs http://127.0.0.1:8765 "$(cygpath -w "$SCRATCH/m2-out")" > "$SCRATCH/m2-browser.txt" 2>&1
```

Then:

```bash
grep -E "^FAIL|checks PASS" "$SCRATCH/m2-browser.txt"
for v in 1440-light-ar 390-dark-ar 1440-dark-en; do printf '%s ' $v; grep -c "^PASS  \[$v\]" "$SCRATCH/m2-browser.txt"; done
```

Expected: no `FAIL` line, and `112 of 112 checks PASS; timings {...}`. That is 45 checks at 1440 light Arabic, 36 at 390 dark Arabic and 31 at 1440 English. The 28 Sep prototype passed 112 of 112 twice, with these timings:

| episode | timing on the 28 Sep prototype |
|---|---|
| first build, C4 5/1, cold server | first frame after 17.5 s and 17.3 s in the two runs, with other GPU work on the machine; M1 measured about 5 s |
| later builds | first frame after 0.57 to 0.70 s |
| a whole episode | 67 to 87 s |
| a cached one (the English view's two) | 0.15 to 0.17 s |

Record your own run's timings.

Read these screenshots with the Read tool. Each one checks something the script cannot:

| screenshot | check |
|---|---|
| `m2-1440-light-ar-d2-short.png` | the Arabic short line reads «(50 000 خطوة)» with the digit groups in order, never «000 50» |
| `m2-390-dark-ar-lab-nav.png` | the lab's phone nav shows «الوكلاء» |
| `m2-390-dark-ar-picker-c4.png` | the 390 px picker: the labels sit on their own lines, and the qualifier sits under the pair select |
| `m2-390-dark-ar-picker-refused-open.png` | the refused list's two problem lines wrap inside the panel, read left to right, with bullets on the left |
| `m2-1440-light-ar-phase-d-chase.png` | the blind car's label carries «قد يحفظه», and the strip shows Phase D's short line |
| `m2-390-dark-ar-phase-d-chase.png` | the same at phone width: the long label wraps inside the view, over neither car |
| `m2-1440-light-ar-phase-d-picker.png` | «الطريق نفسه (180 ث · 12.0٪)» under the episode select, the pair's +9.8 drawn left to right, and the blind arm's budget line with «قد يحفظه» |
| `m2-1440-light-ar-phase-d-verdict.png`, `m2-390-dark-ar-phase-d-verdict.png` | two cells with their glosses, and three quotes cited `:26-31`, `:33-40` and `PHASE_D2_RESULT.txt:65-76`, wrapped and never clipped at 390 px |
| `m2-1440-light-ar-phase-d-pause.png` | the blind car's line ends «(results/PHASE_D_RESULT.txt:33-40)» |
| `m2-1440-dark-en-phase-d-chase.png` | the English blind label ("... may have memorised it ...") stays inside the view |

Stop the server when this step and Step 5 are done:

```powershell
try { Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction Stop | ForEach-Object { Stop-Process -Id $_.OwningProcess -Confirm:$false } } catch {}
```

- [ ] **Step 5: Walk the misreading table (design §6), row by row**

Write `$SCRATCH/m2-misreading.txt` with the Write tool. Give one line per row: `PASS` or `FAIL`, then the evidence. The evidence is a check name from `m2-browser.txt`, a key of `m2-out/texts-*.json`, or a screenshot. The rows, and where their evidence is:

| row | evidence |
|---|---|
| "a recorded drive" | `badge` and «محاكاة» in `m2-*-c4-chase.png`; the plain grid |
| "this episode is the result" | the verdict box and `illustration` |
| "C4 is a clean negative" | the C4 short line in `m2-*-picker-c4.png` and in `strip`; the C4 gloss; `cites` include `PREREGISTRATION_C4.md:633-643` |
| "(i)/(ii) mean something unstated" | `cites` include `PREREGISTRATION_C4.md:41-43` |
| "D2's null means no effect" | the checks `D2 quotes ...:86-89` and the D2 cell; "C1" in the D2 short line |
| "this episode's gap is the table row" | the row exists only in the pair select, with the qualifier check "not this episode" in all three views; the page shows no difference anywhere else |
| "the page picked a representative pair" | the checks `nothing is selected` and `the nav link opens /agents with an empty address` in all three views |
| "high damage means poor protection" | the weights in the episode option (`episode`) and in `weights` |
| "the blind car lost a race" | `markers` is 1; the `legend`; `no winner is named` |
| "the sighted agent saw the road" | four profile ticks and chase posts, in the chase and profile screenshots |
| "the Phase D blind agent was blind" | the Phase D caveat checks (scene label, panel line, scored line, budget line, cells, quotes) in all three views |
| "the boost trim lowered the pressure" | `maps` in `texts-1440-light-ar-phase-d.json` |
| "a fan at 0.4 cut cooling below the ECU" | `tickNotes` name 0 / 0.4 / 1.0 |
| "the slope is real" / "exaggerated" | `ve` ×3 and `slope` |
| "a real 3 km climb" | `rise` |
| "trained like this" | `dt` |
| "this is the scored run" / "the scored artefact" | `device`, and `scored` naming match or not recorded |
| "the network's output was applied" | `held` |
| "it saved damage by refusing torque" | `torque` |
| "the temperature was measured" | `caveat` |
| "jev is part of the thesis" | not applicable in M2 (M3); write `N/A (M3)` |

Add two lines for design §8 rows that the table does not carry:
- "verdict `missing` or `none`": no browser evidence is possible on this tree, where every selectable experiment is `found`. The evidence is the test in `agents-page-nav.test.mjs` named "a verdict that is missing, or was never recorded, says so in the box, the strip and the select", which passes in `m2_node.txt`.
- "refused agents listed with reason and fields": the check `the refused list names BOTH sixspeed arms and why` in all three views, and the refused-list test in `agents-page-nav.test.mjs`, which covers a plant mismatch's stored and live field.

Any `FAIL` stops the milestone. Fix it in its own commit, with its test and outputs as in Tasks 7 to 9, then run Steps 1 to 5 again.

- [ ] **Step 6: Amend the design**

Write `$SCRATCH/m2_amend_design.py` with the Write tool. Its only backslashes are Python string escapes: `\"` inside double-quoted strings, and one doubled `\\` in `app\\start-simulation.ps1`. None of them is a backslash-u escape. The script was tried on a copy of the design on 28 Sep:
- it wrote 7 amendments and the log row;
- `verify_docs.py` still read `All 67 checks pass (782 figure mentions scanned in the documents).`;
- a second run refused with "already in the design".

```python
"""Write M2's amendments into the approved design, each after a fixed anchor.

Run from the repository root with the system interpreter. Every anchor must
occur exactly once, or nothing is written. Takes the design's path as argv[1]
(default: the repository's own), so it can be tried on a copy first.
"""
import sys
import time
from pathlib import Path

PATH = Path(sys.argv[1] if len(sys.argv) > 1
            else "docs/superpowers/specs/2026-09-26-agent-replay-design.md")
DAY = time.strftime("%d %b").lstrip("0")

# The same sentence closes the milestone commit message and the log row, so
# that no deferred item lives only in a scratch file.
DEFERRED = (
    "Every other item of the M1 build record's left-for-later list stays deferred as written "
    "there; M2 took none of them. That includes, in code M2 edits: the store's untested preempt "
    "during the loader and two networks on different devices (Task 5), preempt=true with since "
    "omitted untested on the route (Task 6), and the no-write snapshot watching runs_c4/*_seed0 "
    "only (Task 6).")

AFTER = [
    # section 4, the verdict table
    ("*(Amended after the M1 final review, 27 September: the c4 row quoted `C4_RESULT.txt:29`",
     "*(Amended while building M2: the d2 row quotes `PHASE_D2_RESULT.txt:30-35`, not `:30-33`. "
     "The item runs on to \"power_analysis.py predicted this cell BEFORE this experiment ran, from "
     "Phase D's measured spread.\", and a quote cut before it is the fault the M1 final review "
     "called F8. The phase_d post-hoc quote is the whole item, `PHASE_D2_RESULT.txt:65-76`, "
     "because `:72-76` is what makes it post-hoc; NOT BLIND is `PHASE_D_RESULT.txt:33-40`, as "
     "drafted. The d2 pattern is anchored at the end of its line, so it can never match the "
     "bracketed Phase D line at `:65`. The cell name `INCONCLUSIVE (post-hoc)` is authored: the "
     "file's own words, `[MEI set AFTER this result -- see below]`, are quoted in full beside it.)*"),
    # section 4, the short verdict lines
    ("*(Amended after the M1 final review, 27 September: the c4 line read",
     "*(Amended while building M2: the d2 and phase_d lines are carried as drafted, and each is "
     "shown only when every anchor it names was found. When a file or an anchor is gone, the "
     "not-found text names every missing file, joined by \" · \", not only the first. Grouped "
     "digits are joined by U+202F (d2's 50 000), never by a plain space.)*"),
    # section 4, runnability without stable-baselines3
    ("- If SB3 is not importable, every pair shows",
     "- *(Amended while building M2: the page says it ONCE, under the picker, as soon as the "
     "catalog arrives (the catalog's `sb3` is false), rather than on every pair option. The pairs "
     "stay selectable, so their verdicts and table rows can still be read; «احسب» stays disabled, "
     "and the episode route still answers 503.)*"),
    # section 4, the catalog
    ("**Catalog (M2).** `GET /api/agents/catalog` returns",
     "*(Amended while building M2: the catalog as served carries, per experiment, the WHOLE "
     "verdict (`state`, `lines`, `missing`, `short`, `cells`), so the verdict box reads before "
     "«احسب»; per pair, `problems`, `protocol` (null unless the pair can run) and `result_file`; "
     "per agent, `reason`, `problems`, `zip_sha` and `scored` (on each agent, not on the pair). A "
     "seed with one arm directory missing is listed, with that arm `missing`. Episodes carry "
     "`grade` as a fraction, as `meta.episode.grade` does, not `grade_pct`; `table_diff` is "
     "rounded to one decimal, as the results tables print it. An unexpected failure is a "
     "fixed-text 500 with no-store, never the exception's own text. Two additions to the status "
     "order, which is unchanged: a directory that does not exist is a `KeyError`, and at step 7 "
     "a `final.zip` that is not a readable stable-baselines3 zip is `incomplete` (reversing M1 "
     "ruling 6). `check_pair` runs `find_pair`'s checks in `find_pair`'s order and returns the "
     "problems, so the catalog and the episode route share one rule.)*"),
    # section 5, cars and colours
    ("- Colour tokens: `--agent-sighted` (blue) and `--agent-blind` (amber)",
     "- *(Amended while building M2: Phase D's blind car is named with its caveat everywhere it "
     "is named: the scene label, the picker's budget line, the verdict box's scored line and the "
     "stopped-lane line. Its pause-panel line cites `PHASE_D_RESULT.txt:33-40`, the whole NOT "
     "BLIND item, read from the verdict's own `not_blind` line rather than typed; this section "
     "drafted `:33-37` and section 6 `:33`.)*"),
    # section 6, the picker
    ("«احسب» sends one `preempt=1` request. Until it is pressed,",
     "*(Amended while building M2: an experiment with no runnable pair is listed greyed with its "
     "reason and cannot be selected, from the select or from an address. An address selects only "
     "what the catalog allows, level by level; one that names more (a refused pair, a malformed "
     "level, `ep=21`) is replaced by the address of what it selects. Every change of a select "
     "replaces the address, never adding a history entry, and clears the episode on screen. The "
     "episode is kept when the pair changes within one protocol, since both pairs are scored on "
     "the same twenty episodes. The qualifier sits under the pair select once an experiment is "
     "chosen, and Phase D's same-road note under the episode select; it prints the grade with one "
     "decimal, «(180 ث · 12.0٪)», like every other grade on the page, where this section wrote "
     "«12٪». The table figure is drawn inside a left-to-right isolate: in an Arabic line a bare "
     "\"+360.6\" is drawn \"360.6+\". A greyed option has room for one reason, so every pair that "
     "cannot run is also listed under the picker, collapsed, with every problem the server found: "
     "both arms and each stored and live field of a plant mismatch (section 8, \"with reason and "
     "fields\"). When «احسب» meets another build still running, the page says it is stopping that "
     "build, because its own request already asked for it; the M1 text asking for «احسب» again "
     "appears only when that request may never have arrived, on a retry after a failed "
     "request.)*"),
    # section 10, the M1 Verify note on the lab launcher
    ("  - *(Amended while building M1, 27 September: this line read",
     "  - *(Amended while building M2: M2 fixed the banner, not the interpreter. "
     "`app\\start-simulation.ps1` now prints the `/agents` address and, when its own `python` "
     "has no stable-baselines3, says that `/agents` lists the experiments but answers 503 for an "
     "episode, and how to start the server with an interpreter that has it. Its last line still "
     "calls bare `python`: the launcher is the lab's entry point, and `/simulation` must start "
     "exactly as before. A ruling taken while building, not Jad's word; changing the interpreter "
     "is one line.)*"),
]
LOG_ANCHOR = "| 28 Sep | M1 in use |"
LOG_ROW = (
    f"| {DAY} | M2 built | **M2 is built and verified; the milestone commit carries every suite's "
    "output.** Both gaps Jad found on 28 Sep are closed, and both were checked in the browser "
    "starting FROM THE NAV LINK: the replay lab links to `/agents` right after its first link, so "
    "phones keep it, and `/agents` opened from its own link loads the catalog, selects nothing "
    "and offers three working selects (experiment, pair, episode) whose choice is kept in the "
    "address. All three experiments run; Phase D's blind car is named as possibly memorising its "
    "one road wherever it is named; `runs_sixspeed_18sep` is greyed as \"no meta.json\", and the "
    "list of pairs that cannot run names both of its arms. "
    "**Rulings taken while building, not Jad's word**, each recorded as an amendment above and "
    "each one commit to reverse: the d2 quote runs to `:35` and the post-hoc quote to `:76` "
    "(whole items); an unreadable `final.zip` is incomplete; the catalog's shape as served; the "
    "Phase D citation `:33-40`; the picker's rules, including Phase D's «12.0٪» and the list of "
    "pairs that cannot run; a missing stable-baselines3 said once under the picker; the lab "
    "launcher's banner fixed and its interpreter left as it was. " + DEFERRED + " |")


def main():
    lines = PATH.read_text(encoding="utf-8").split("\n")
    plan = []
    for anchor, text in AFTER + [(LOG_ANCHOR, None)]:
        hits = [i for i, line in enumerate(lines) if line.startswith(anchor)]
        if len(hits) != 1:
            sys.exit(f"anchor found {len(hits)} times, not once: {anchor[:60]!r}")
        plan.append((hits[0], text))
    if any("Amended while building M2" in line for line in lines):
        sys.exit("the M2 amendments are already in the design; nothing written")
    for i, text in sorted(plan, reverse=True):
        if text is None:
            lines.insert(i + 1, LOG_ROW)
        elif lines[i].lstrip().startswith("- "):
            lines.insert(i + 1, text)
        else:
            lines[i + 1:i + 1] = ["", text]
    PATH.write_text("\n".join(lines), encoding="utf-8", newline="")
    print(f"wrote {len(AFTER)} amendments and the {DAY} log row into {PATH}")


if __name__ == "__main__":
    main()
```

Run it, then check it and the documents:

```bash
$PY "$(cygpath -w "$SCRATCH/m2_amend_design.py")"
git diff --stat docs/superpowers/specs/2026-09-26-agent-replay-design.md
git add docs/superpowers/specs/2026-09-26-agent-replay-design.md
$PY verify_docs.py 2>&1 | tail -1
```

Expected:
- `wrote 7 amendments and the <day> log row into docs\superpowers\specs\2026-09-26-agent-replay-design.md`
- The diffstat shows only insertions: 12 on the prototype (7 amendments, 4 blank lines and 1 log row).
- `verify_docs.py`'s last line starts `All ` and ends `figure mentions scanned in the documents).`

If `verify_docs.py` names a line in the amendments, a figure in that sentence has been retired. Then:
1. Reword that sentence in `$SCRATCH/m2_amend_design.py`.
2. Run `git checkout -- docs/superpowers/specs/2026-09-26-agent-replay-design.md`.
3. Run the script again.

- [ ] **Step 7: The milestone commit**

```bash
{
  printf '%s\n' "Agent replay M2: every experiment -- verified from the nav link, with nothing selected" "" \
    "Both gaps Jad found on 28 Sep are closed and were checked in the browser from" \
    "the lab's nav link: /simulation links to /agents after its first link (phones" \
    "keep it), and /agents opened from its own link loads GET /api/agents/catalog," \
    "selects nothing and offers experiment -> pair -> episode, kept in the address." \
    "Phase D, D2 and C4 pairs all run beside their quoted verdicts; Phase D's blind" \
    "car is named as possibly memorising its one road, at 1440 px and at 390 px;" \
    "runs_sixspeed_18sep is greyed as 'no meta.json', and the list of pairs that" \
    "cannot run names both of its arms. Design amended in place (sections 4, 5, 6" \
    "and 10) with an M2 row in the walkthrough log." "" \
    "Taken from the M1 build record's left-for-later list: F6 (a preempt answered" \
    "from the cache now cancels the other build); a superseded build that fails" \
    "reports nothing; renderStopped named every blind car alike; read_agent on a" \
    "missing directory; an unreadable final.zip showed ready (ruling 6 reversed);" \
    "the Task 3 test gaps (unknown protocol, cross-arm protocol, results file" \
    "absent); MISSING_TEXT named only the first file; the 10b grouped-number regex;" \
    "the agent_catalog comments at :36-38 and :102; non-KeyError failures reached" \
    "FastAPI's 500 without no-store; the lab launcher named only /simulation." "" \
    "Still deferred, named: M1 F2 and F3 (cosmetic wraps); the dt caption's" \
    "citation breaking at its space; jsonable of a 0-d array and its key" \
    "collisions; route's length assertion; pair_paths duplicating find_pair's gate;" \
    "find_pair re-hashing both zips on every poll; the 1..20 hard-code; the" \
    "StoreTests 50 ms window; no engines pin for registerHooks (Node >= 22.15); the" \
    "chase tests' order coupling; createChaseScene's dispose masking an error; the" \
    "boost row's dash on a diverged step." \
    "Every other item of the M1 build record's left-for-later list stays deferred" \
    "as written there; M2 took none of them. That includes, in code M2 edits: the" \
    "store's untested preempt during the loader and two networks on different" \
    "devices (Task 5), preempt=true with since omitted untested on the route" \
    "(Task 6), and the no-write snapshot watching runs_c4/*_seed0 only (Task 6)."
  printf '\n$ browser check (scratch m2-browser-check.mjs, 1440 light ar / 390 dark ar / 1440 en)\n'
  grep -E "checks PASS" "$SCRATCH/m2-browser.txt"
  printf '\n$ catalog timing\n'
  cat "$SCRATCH/m2_catalog_timing.txt"
  printf '\n$ python -m app.test_agents   (summary)\n'
  grep -E "^Ran|^OK|FAILED|PROVEN" "$SCRATCH/m2_agents.txt"
  printf '\n$ python -m app.test_agents --full   (summary)\n'
  grep -E "^Ran|^OK|FAILED|PROVEN" "$SCRATCH/m2_agents_full.txt"
  printf '\n$ python -m app.test_simulation\n'
  tail -3 "$SCRATCH/m2_sim.txt"
  printf '\n$ node --test "app/static/sim/*.test.mjs"   (summary)\n'
  grep -E "^ℹ " "$SCRATCH/m2_node.txt"
  printf '\n$ python verify_docs.py   (last line)\n'
  $PY verify_docs.py 2>&1 | tail -1
  printf '\n$ python -m app.test_replay\n'
  cat "$SCRATCH/m2_replay.txt"
  printf '\n$ python -m app.test_replay --full\n'
  cat "$SCRATCH/m2_replay_full.txt"
  printf '\nCo-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>\n'
} > "$SCRATCH/m2_msg.txt"
grep -c "PROVEN" "$SCRATCH/m2_msg.txt"; grep -c "UNPROVEN" "$SCRATCH/m2_msg.txt"
git commit -F "$SCRATCH/m2_msg.txt"
git log --oneline -1
git status --short
```

Expected:
- The first `grep -c` prints 2 or more: the default proof line and the `Phase D == proof PROVEN` line. The second prints `0`.
- The commit lands on `JMF-2340550-sep17`.
- `git status --short` prints nothing, because the browser script, its outputs and its screenshots stayed in `$SCRATCH`.


---

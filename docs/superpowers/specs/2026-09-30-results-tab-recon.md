# The results tab — what was found before designing

30 September 2026. Jad asked for a new tab in the local app with interactive
charts (hover or tap a point, its numbers appear), built from the project's
result files so that it follows every change, and pointed at Ghassan's
published results page as "the charts we need".

Decided by Jad in the brainstorming questions, in this order:

1. **A new tab inside our app**, beside the replay lab and the agents page. It
   reads the latest results every time it is opened.
2. **All experiments**: Ghassan's twenty agents, Jad's Phase D, D2 and C4, and any
   future experiment appears by itself. Each in its own section, labelled with the
   plant it was made on, never pooled.
3. **Both languages**, on the app's own language button. Preregistered verdicts
   stay verbatim in English with an Arabic gloss beside them, as on `/agents`.
4. **Built in our app's style**, from a copy of the chart-drawing code of
   Ghassan's page. His page and `make_page.py` are not edited.

Also this session: the speed idea for the replay lab was cancelled (Jad: the
speeds already differ; the car's distance is integrated from the recorded speed,
`app/replay.py:189-209`), and the "car stumbles when its agent errs" idea for
`/agents` waits for the retrain, because on `main` the page runs no pair: 25
pairs listed, 0 runnable, every one refused for `plant_sha` (checked with
`app.agent_catalog.discover()`).

Method: six read-only readers in parallel and one critic who re-checked every
disagreement between them. Commit `a7ce729`. Nothing in the repository was
written; `git status` was clean afterwards. **This file is the evidence, not the
design**, which goes to its own file after Jad answers the remaining questions.

---

## 1. Ghassan's page is already in the repository, and it is already interactive

`results/page/template.html` (1608 lines), filled by `make_page.py`.

- **27 SVG charts and 8 tables in 22 figures**: Part 1 (the simulation) holds 10
  charts, Part 2 (the simulator against the car) 17.
- **Every chart shows numbers on hover, and a tap opens them on all 27.** By kind:
  crosshair 9, nearest-point 5, per-mark 9, custom listeners 4. Only the 9 per-mark
  charts can be reached with the keyboard, and 21 of 27 have no "show the
  numbers" table.
- **The drawing library is small and has no dependency**: about 270 generic lines
  (`template.html:747-978`, `:988-996`, `:1348-1361`, `:1463-1474`, `:1491-1496`)
  plus about 50 lines of chart CSS and 22 CSS variables. The other ~590 lines are
  chart-specific and keyed to English names. The page reads one inline JSON blob
  (`:742`) and never fetches.
- **Its data build is cheap**: `make_page.py` imports with no side effect, and its
  reader functions take about 0.12 s warm and 0.8 s cold, for about 221 KB of
  JSON. Only `main()` writes (to `results/page/index.html`), so a live tab must
  never call it.

## 2. The link Jad sent is newer than anything in the repository

The published page says it was built from commit `a3656ac`. That commit is in no
local ref and on no remote branch (checked after `git fetch` on 30 September,
`origin/GRA-2340394` included).

- It is `main`'s template plus **three charts** (`c-km` how much rests on the
  knock model, `c-act` what the agents do on the climb, `c-ep1` one frozen episode
  step by step), one table, two caveats and a few reworded sentences. The 27
  shared charts carry the same numbers as a fresh build of `main`.
- **`c-km` and `c-act` can be built live from committed files**:
  `results/agents/terrain_dt1/knock_margin.json` (per agent: preview, cut,
  cut_orig, ki_p95_climb, fuel_pct) and each policy's `eval_summary.json`
  (`actions.<lever>.climb.{p5,p50,p95}` and `.neutral`).
- **`c-ep1` cannot be built from the repository today.** It reads
  `results/agents/terrain_dt1/episode_trace.json`, which exists nowhere here;
  `eval_record.npz` is gitignored and absent, and so are the agents' `final.zip`.
  The critic rebuilt one policy offline from its committed `policy.npz` (a numpy
  forward pass through `evaluate.run_episode`): 37.2 s, damage within a relative
  1.3e-6 of the committed value, close but not bit-identical. All 22 policies
  would take about 14 minutes, and only while the plant still equals the scoring
  plant, that is before the agreed thermal sub-stepping. The take-away figure
  "5–6 times" cannot be rebuilt at all: its definition is only in `a3656ac`.
- `c-act` types the action ranges (spark −8 to +4 and so on). They match
  `engine_env.py:644-645` today and will not follow the agreed spark cap at 0.
- Its new caveat "Not on this page" leaves out Phase D, D2 and C4, which is the
  opposite of decision 2.

## 3. Defects found in Ghassan's page (reported here; the tab does not edit his files)

- **A typed sentence is false against its own chart.** The take for `f-thfit`
  (`template.html:537`) says the derived thermal constants beat the old ones on
  every drive, fitted and held out. `results/calibration_comparison.json`
  (`thermal.per_drive`) shows 4 of 14 drive-and-quantity cells worse: coolant on
  670063b2 (4.47 K old, 5.31 fitted, 5.39 held out) and on 7475b5d7 (4.84, then
  6.66 and 6.82), and both oil (6.55 to 14.26) and coolant (6.99 to 14.18) on
  683640a0 held out.
- The Phase D lede (`template.html:294`) calls the scored climb a 900 s episode;
  `evaluate.py:130` scores 720 s.
- In dark mode the heat-map legends' "darker = more" states the opposite of what
  is drawn.
- `c-boost` clips 4 raw-sensor points above 345 kPa, and `c-boostB` drops 3 of
  drive B's 89 readings outside 1400–4200 rpm while its caption counts all 89.
- `c-gear` binds no `pointerdown`, and `c-abl` draws a bar of negative width for
  an agent worse than the baseline, so both the bar and its tap target vanish.
- About 25 results are typed into the template beside its tokens, and several
  tokens pick rows by position (`series.2`, `cells.7`, `lit.8`, `h2.2`), so a
  reordered result file would name the wrong row without an error.
- `make_page.py:134-150` still computes the verdict wording the merge review
  retired ("Indistinguishable from zero."); the published page already says
  "Inconclusive".
- The page's provenance line is from 29 September (`JMF-2340550 @ cbb8d09`),
  while its data equal a fresh build of `main`.
- It loads Google Fonts from a CDN; the lab is offline by rule
  (`app/README.md:40-42`), and the fallback mono font draws Arabic as
  disconnected letters.

## 4. Reading the data live

- **Four of make_page's readers describe the plant, not an experiment**, and can
  be reused as they are: `model_vs_car`, `training_roads`, `calibration`,
  `generality`. The last is the H/τ sweep, which CLAUDE.md marks not quotable
  until the thermal network is sub-stepped.
- **`phase_d()` mixes two things**: the hand-written traces and sweep, and agent
  results read from `results/phase_d_130kmh_raw.json`, a single file holding
  whichever set `run_results.py` scored last. Setting `make_page.AGENT_SET` to
  another set therefore mixes two sets without any error; the reader measured it
  in memory (the 19 September curves beside the 29 September evaluations).
- **A set's own folder is enough.** For `terrain_dt1`, every
  `results/agents/terrain_dt1/*/eval_summary.json["episodes"]` equals
  `phase_d_130kmh_raw.json` on all seven fields, 480 of 480 episodes, and it also
  carries `damage_thermal` (damage without the knock term).
- **Failure modes**: a missing input raises `SystemExit` in four places
  (`make_page.py:275`, `:428`, `:514`, `:581`), `FileNotFoundError` elsewhere,
  and `TypeError` with fewer than two pairs (`:134`). `SystemExit` is not an
  `Exception`; in a synchronous FastAPI route it becomes a bare 500 while the
  server survives (read from the installed anyio, starlette and uvicorn sources,
  not run). Starlette's `JSONResponse` refuses NaN (`allow_nan=False`).
- **Half-written and mixed files**: every result writer except `train.py` writes
  straight to the final path. `knock_margin.json` comes from a separate script
  and can lag the evaluations after a retrain. Two cheap live checks catch a mix:
  `cut_orig` equals `eval_summary.summary.cut_pct` (20 of 20 today) and the
  per-set episodes equal `phase_d_130kmh_raw.json` (480 of 480).
- **Caches that do not follow the disk**: `derived.py` keeps
  `data/derived_params.json` for the life of the process, and
  `agent_catalog.live_fingerprint` keeps the plant hash.
- **A folder name is not an identity.** The documented retrain routine rewrites
  `results/agents/terrain_dt1` in place (`record_agents.py:384`, `:402-406`), so a
  section title must come from what the files record (training commit, dates,
  plant hash when present), not from the folder name.
- `record_agents.py` scores only the locked climb, so the agreed next test set
  may appear as `evaluate.py` result files (`results/<prefix>_seed<N>.txt`)
  rather than under `results/agents/`. Discovery has to accept both shapes and
  never show one experiment twice.

## 5. Jad's three experiments

- **24 per-seed files** (`results/phase_d_seed0-7.txt`, `d2_seed0-7.txt`,
  `c4_seed0-7.txt`). For each of five policies (baseline ECU, reactive,
  current-grade, the sighted agent, the blind agent) they give the median
  damage, the interquartile range **as a width only**, the worst episode, the
  median fuel and the hottest turbine peak over the 20 frozen episodes.
- **No per-episode numbers exist for them**, in the tree or in git history, and
  no thermal-only damage. A chart can draw one median mark per agent per seed,
  with the worst as a second mark; it cannot draw boxes, quartile bars or
  episode dots.
- The per-seed "points" line is in points of damage cut, not in the damage
  units the MEI uses: Phase D seed 0 reads +1.0 points but +9.8 units.
- Every file carries a fingerprint block: `plant_sha b5a3069f32a83754` under
  Python 3.12.10, with its `git_head`. Rebuilt from git on this machine, every
  recorded head gives both the recorded code hash and the recorded byte hash, so
  "made on another plant" can be shown, not only claimed.
- D2 and C4 share one episode set (`1c5d49852290d27c`), and C4's agents continue
  D2's: never pooled, and C4 is not a replication.
- Readers: `analyse_phase_d.parse`, `analyse_phase_d2.load(prefix)` (no root
  parameter) and `analyse_c4` import with no side effect but return medians
  only. The IQR width, worst, fuel and peak need a parser of their own,
  cross-checked against `load()` as `plot_study_page.policy_tables` does.
- Verdicts are quoted, never computed: `app.agent_catalog.verdict(prefix)`
  returns the preregistered lines with file:line references, and the Arabic
  `SHORT_VERDICT` and `GLOSS` live in `app/agent_catalog.py:271-321`.
- `agent_catalog.discover()` scans the gitignored `runs*/` folders, so on a
  teammate's clone Jad's experiments do not appear. The tab should discover from
  `results/<prefix>_seed<N>.txt` with a strict name pattern.
- `results/PHASE_D_RESULT.txt:42-44` still says the MEI is unset; a fresh
  `analyse_phase_d.py` run says otherwise. Quote it only with that noted.
- **Rules Jad's pages already follow**, to keep: nothing computed beyond reading
  and counting; verdicts quoted with file:line; no new statistic, average or
  winner; the 50-unit MEI drawn as a length; sighted blue, blind amber, joined per
  seed; current-grade as the reference line; supervision kept apart from the
  preview test.
- **Required beside every figure of these experiments**: the training budget
  (50 000 steps; C4 300 000 and not converged); Phase D's blind arm is not blind;
  trained at a 0.2 s step and scored at 1.0 s; the plant label; supervision rests
  on the untested knock model; the one-step knock spike at the grade step sits
  inside every D2 and C4 episode and its effect on these results was never
  measured.
- **Forbidden**: "preview does not help" in any form; reading "beats
  current-grade" as evidence for preview; pooling experiments or calling C4 a
  replication of D2; rescuing a null with H/τ; binning D2 or C4 by grade.

## 6. The other sets

- **`results/agents/terrain_dt1`, Ghassan's twenty.** Trained from commit
  `cbb8d09` with uncommitted changes (which files is not recorded), Python
  3.13.2, data fingerprint `c4fdd4babfb3752a`, which equals the data on disk. No
  `plant_sha` anywhere. The plant code at `cbb8d09`, `74de99a`,
  `ghassan-before-merge` and `a7ce729` hashes to the same live
  `c236a8db3e201090` under this machine's Python. Honest label: *same plant code
  and derived data as this tree by its recorded commit; trained from a tree with
  uncommitted changes*. Not "another plant".
- **Its reading under Jad's MEI rule reproduces but is printed by no script.**
  Run in memory with `analyse_phase_d2.classify` on the committed
  `eval_summary.json` files: 6 of 10 positive, sign p 0.377, permutation 0.3154;
  below the MEI sign p 0.1719, permutation 0.0547; INCONCLUSIVE. That equals
  `SESSION_REPORT_2026-09-30_merge.md:197-200`, but CLAUDE.md forbids quoting a
  number no script prints, and the set has no preregistration.
- `index.json` records `regression_checked 0`. That is the report rebuild
  carrying no count (`record_agents.py:505-536`), not a failed check; compared
  independently, 480 of 480 episodes are identical.
- **`results/agents/sep19_110kmh`**: "a record, not a result"; no
  `knock_margin.json`.
- **`runs_sixspeed_18sep/` and `results/void/`**: void.
- **`results/curve_sighted_seed0.csv` and `results/curve_blind_seed0.csv` are
  void data outside `results/void/`.** They are byte-identical to
  `runs_sixspeed_18sep/{sighted,blind}_seed0/curve.csv` (checked with `cmp`),
  were committed in `a68715f` with the void six-speed run, and `results/README.md`
  lists them only as learning curves. Nothing in the code reads them.

## 7. Provenance: what can be said about where each number came from

- `plant_sha` is the first 16 hex characters of a SHA-256 over `ast.dump` of
  `plant.py`, `thermal.py` and `engine_env.py`, docstrings removed
  (`fingerprint.py:142`, `:171-173`). It does not cover `derived.py`,
  `data/derived_params.json`, the hand-written policies or `evaluate.run_episode`.
- **It depends on the Python minor version**, as Ghassan's draft report says:
  `ast.dump` prints each interpreter's own AST fields, and on 3.12 the three
  plant files dump `type_params=[]` 67 times, a field that exists only from 3.12.
  Confirmed from the code; his 3.11 and 3.13 values could not be reproduced here
  (this machine has only 3.12). Ghassan's laptop runs 3.13, so a naive comparison
  there would call every result "another plant".
- **Only the 24 per-seed files record a plant.** No JSON under `results/` does;
  `premise.json`'s data fingerprint and timestamp are copied from the
  derivation, not from the premise run.
- **Git answers cheaply and without writing** (with `GIT_OPTIONAL_LOCKS=0`): one
  `git log --name-only --diff-merges=dense-combined` pass over all 225 result
  files takes about 20 ms and agrees with per-file queries; one `git status`
  about 17 ms; re-hashing a recorded commit's plant 62–78 ms. File modification
  times are useless: almost every file reads the merge checkout time.
- `verify_docs.check_derived`'s "fresh" means only that the data fingerprints
  agree; it says nothing about plant code.
- Proposed states for a label, one per file: *same plant as this tree* / *made
  on another plant* / *plant not recorded in this file* / *cannot compare* (for
  example a different Python and no git route) / *void*. Words never to use:
  current, stale, outdated, fresh, up to date.

## 8. The app: what a new tab must respect

- **Route pins** (`app/test_agents.py:1344-1386`): importing `app.server` may load
  no module named `app.agent*`, `app.jev*`, `app.laya*` or
  `app.model_questions`; module-level routes are GET or HEAD only; `server.py`
  has exactly one call named `install(`, inside `if a.simulation:`.
- **Nav pins**: `app/test_agents.py:3795-3802` and
  `app/static/sim/agents-page.test.mjs:100-109` list the nav links exactly; on
  phones `style.css` hides the last nav link of `simulation.html`; a new nav key
  may not sit between `nav.review` and `nav.agents`
  (`agents-strings.test.mjs:32-39`).
- **Strings**: flat keys, the same in both languages; a page's strings live in
  their own module; `agents-strings.mjs` pins its escape counts. The Write tool
  turns `\u` escapes into literal invisible characters (project memory), so
  string files are written through Python and byte-checked.
- **Test scans** cover every `app/*.py` for `.write(`, network imports and
  `print(file=...)`, and the suite fails if anything under `results/`, `app/` or
  `.git/index` changes; fixtures live outside the repository.
- **`verify_docs.py`** reads every tracked `.md`, `.py`, `.html`, `.js` and
  `.txt`, not `.mjs`, `.css` or `.json`. Numbers belong in the data, not in
  tracked HTML.
- **CSS collisions**: the app's global `svg{width:20px;height:20px;...}` and
  `.chart{height:136px}` (`app/static/sim/style.css:97`) would break the copied
  charts, and five variable names mean different things in the two sheets. The
  app colours sighted blue and blind amber, never red or green.
- **Right to left, measured in headless Chrome**: with `dir=rtl`, 323 of 613 chart
  labels land on the wrong side of their anchor, two square charts put their
  tooltip about 400 px from the point, and numbers reorder ("1600–2000" reads
  "2000–1600"). The fix the app already uses: `direction:ltr` on the chart host
  and left-to-right isolates around numbers and Latin runs (`isolateLtr`,
  `app/static/sim/agent-picker.mjs:159-173`). The thousands separator must be
  U+202F (bidi class CS), not make_page's U+2009 (WS), which splits a number in
  Arabic.
- **A language switch needs a forced redraw** (the copied `render()` redraws only
  on a width change); a theme switch needs none, every colour being a variable.
- **The guard**: `agent_api.same_origin` requires an `Origin` header, which a
  browser's same-origin GET does not send (Fetch standard; not measured). The
  reusable part is the Host check against `LOCAL_HOST`, which no GET route has
  today.
- **Reach**: the server listens on 127.0.0.1 only, so a phone cannot open the tab.
- **Browser caching**: `.mjs` files go out with no `Cache-Control` and no version
  query, so a browser can keep running an old script (Ghassan measured this).
- **Speed is not the constraint**: Ghassan's whole page builds in 122–141 ms in
  headless Chrome on this laptop.

## 9. Ghassan's draft branch `origin/GRA-2340394` (pushed 30 September, "DRAFT for Jad")

- `8f7275b` pins `.mjs` to `text/javascript` in `app/server.py`: on his laptop
  the registry served the page scripts as plain text and both lab pages rendered
  empty. A new tab would render empty there too until this is merged.
- `0779585` writes `meta_reconstructed.json` certificates so that `/agents` lists
  his twenty agents, changes `agent_catalog.py`, `agent_api.py`, `agents.mjs`,
  `agent-picker.mjs` and `agents-strings.mjs`, and asks Jad five decisions
  (`SESSION_REPORT_2026-09-30_agents_page.md` section 5).
- Overlap with a new tab: `app/server.py` and `app/test_simulation.py` (the MIME
  fix). It touches no `.html`, `i18n.mjs`, `style.css` or `agents.css`. Keeping
  the tab's strings, styles and tests in new files avoids conflicts.

## 10. Decisions still open, for Jad

*(Later on 30 September: 1 was decided, a committed post-hoc script, printed with and without the knock term; 2,
`c-ep1` waits for Ghassan's commit; 3, the pause does not cover this tab. 4 and 5 are open. See
`2026-09-30-results-tab-design.md` §1 and §11.)*

1. Ghassan's set has no preregistered verdict. Show his numbers only; or add a
   small committed script that prints the MEI-rule reading so the tab can quote
   it, labelled post hoc; or show make_page's t-interval wording (retired).
2. `c-ep1`: wait for Ghassan's `a3656ac` and its `episode_trace.json`, or rebuild
   it offline from `policy.npz` before the thermal sub-stepping, or leave it out.
3. Whether the agreed pause of "the agents page" (`conflict.md:470`) covers a
   read-only results tab. Its stated reason is that `/agents` refuses every
   agent it replays; this tab replays nothing.
4. Whether `results/curve_{sighted,blind}_seed0.csv` should move into
   `results/void/`.
5. Ghassan's defects in section 3: tell him, since the tab does not edit his page.

# Results tab R1a: what the reviews ruled and left for later

Written on 6 October 2026, when milestone R1a was finished by subagent-driven
execution of `docs/superpowers/plans/2026-10-05-results-tab-r1a.md`. Each of the
ten tasks was reviewed before the next began, and the whole branch was reviewed
at the end. The working ledger lived in a git-ignored folder and is gone; this
file keeps what it held that the code and the build record do not: every
decision the controller took on Jad's behalf, and every minor finding that was
deferred rather than fixed. The build record at the end of
`docs/superpowers/specs/2026-09-30-results-tab-design.md` says what the fixes
changed; the commits carry them.

Read the deferred findings before planning R1b: most are cheap, several touch
the files R1b will extend, and none was judged worth blocking R1a.

## The rulings, in the order they were made

Each ruling says what was decided, why, and what it costs if it was wrong.

1. work in place in the main checkout on JMF-2340550-results-tab, with no worktree — the plan's commands, expected outputs and the git-ignored test assets (runs*/, app/static/vendor, app/node_modules) exist only in this checkout, and Jad approved the plan as written — cost if wrong: another session's uncommitted edit could enter a test run (verify_docs reads tracked documents); each implementer checks git status first and commits by explicit path.
2. proceed although app.test_agents fails before R1a — the failures are the merged plant refusing Jad's agents (CLAUDE.md; the plan's "Before Task 1"), and the plan measures each task by "no new failing entry" against $SP/agents_baseline.txt — cost if wrong: a regression hidden among the pre-existing entries; the per-task comparison names any entry the baseline does not have.
3. the four copies the spec mandates stand (charts-lib.mjs from Ghassan's page template; results_provenance's copies of train.derived_sha and derive_params.fingerprint; results_api's LOCAL_HOST from agent_api; results-strings' mergeInto from agents-strings' mergeStrings) — the spec mandates each: Q4 and §7.1 (Ghassan's page stays untouched, and the app cannot import from an HTML template), §5.2 (the tab never imports derive_params or train), §6.1 (importing agent_api would load agent code), §7.1 (importing agents-strings.mjs would merge every /agents string into the tab); the two formulas and LOCAL_HOST are pinned by tests that compare them with their originals, while charts-lib.mjs and mergeInto are adapted on purpose and tested on their own behaviour — cost if wrong: the copies drift from their originals; for the formulas and LOCAL_HOST the equality tests fail when they do, for the other two nothing does.
4. implementers on sonnet, not the cheapest tier — every task is long, multi-step and full of this machine's traps (the Write tool decoding escapes, Bash collapsing doubled backslashes, CRLF files, captured outputs), where a cheap model's extra turns and slips cost more than the price difference — cost if wrong: higher spend than needed.
5. commits that transcribe the plan keep the plan's trailer, Co-Authored-By: Claude Opus 5.5 (1M context) — their content is the plan's code, drafted by this Opus session and transcribed byte for byte (the implementer checked the blobs); a commit whose content an implementer writes itself (a fix round) ends with that implementer's own model line — cost if wrong: R1a commits under-credit the Sonnet implementers, which a later note can correct; 169deed is not amended.
6. accept the plan-mandated Important finding of Task 2 (a git status that exits non-zero returns {} = "nothing changed" while the helper stays available) — the spec shows a file's last commit as a fact only when git status says it is unchanged (§5.2), and fingerprint.py's own rule is "Unknown is not clean"; fix round 1: status and last_commits call self._lose("error") when git exits non-zero on a non-empty path list, with a corrupt-index test — cost if wrong: one failed git call hides every commit fact for that one build, and the next open rebuilds.
7. Ruling (carried into Task 4's dispatch): results_data.build asks git.status before git.last_commits, so a status that fails (and loses git) leaves no commit date on the page beside the "git is not available" line — cost if wrong: none beyond call order; healthy git gives the same answer either way.
8. accept Task 3's Important finding — spec §5.2 says derived.py's cached constants against data/derived_params.json on disk follow the plant-files restart rule (the page shows no "same" state), and the plan left that sentence out; fix round 1: classify_eval returns ("cannot_compare", "derived_restart") when live["derived_loaded_differs"], right after the restart check (so a differing field still reads "another", and a plant restart still reads "restart"), with tests; Task 6's dispatch adds the string results.plant.reason.derived_restart (en "the derived constants changed after the server started; restart the server", ar «تغيّرت الثوابت المشتقة بعد أن بدأ الخادم؛ أعد تشغيل الخادم») and its CONTRACT row; Task 9's reasonText maps reasons generically and needs nothing — cost if wrong: one more state the page can show, reachable only after the server outlives a change to data/derived_params.json.
9. the four spec gaps are real and enter one fix round for Task 4 — the spec is binding: (1) §4.1 "never dropped silently": two files naming one (prefix, seed) are both listed in not_read with reason "duplicate_seed" and neither is read, a prefix left with no seed is dropped from the groups; (2) §6.3 "the git facts are omitted": built.head is None whenever git is unavailable at the end of the build; (3) §5.4 "C4 300 000 steps, from its files, not converged": KNOWN["c4"] gains the note "c4_not_converged" (cited to results/PREREGISTRATION_C4.md 5b and results/C4_RESULT.txt); (4) §5.5/§9.10: the Python wording test bans the Arabic «حالي», «الميل الحالي» exempt — Task 6's ruling file gains the two strings (results.not_read.reason.duplicate_seed, results.note.c4_not_converged) — cost if wrong: two more strings and one more note on the page; the duplicate rule hides a seed only when two files claim it.
10. from Task 5 on, implementers run on opus, and each task review is a Workflow (four lenses: spec against brief + ruling + spec; correctness and edge cases; tests; project constraints: Arabic, bidi, wording, no-write) whose Critical and Important findings each face adversarial refuters before they reach the fix loop; the final whole-branch review is a Workflow of the same shape over 9afff5a..HEAD, which also covers Tasks 1-4 (reviewed by a single reviewer each) — cost if wrong: more tokens and time per task, which Jad chose.
11. Review Focus 1 is met from the next update on and stated honestly for this one — no import map or version query on the shared pages (they would touch simulation.html, agents.html and their pinned tests for a cosmetic, self-healing, half-day window); fix round 1 rewrites the RevalidatedStatic docstring to say what it covers and what it does not (and drops the word "freshness"); Task 10's ruling adds one sentence to app/README.md's results-tab section and corrects the build record's claim; Jad is told in the hand-off to press Ctrl+F5 once on the lab pages after updating — cost if wrong: a teammate who reads none of it sees "nav.results" in the nav for up to half a day.
12. fix round 1 rewrites five notes so each names its file and, where it types a judgement or a number, its date (budget_c1 both preregistrations with 21 and 22 September; blind_not_blind found on 22 September; spike_unmeasured conflict.md 3b, 30 September; knock_model drive C and conflict.md 3a, 30 September; turbine_modelled CLAUDE.md "Limits the live app adds"), text in task-6-fix1.md — cost if wrong: longer note lines; the dates are the files' first commits and CLAUDE.md's record.
13. fmtNum stays ungrouped (its docstring: "a file's numbers keep the shape the file printed"; Task 8's tests pin '1118.0' and '2363.8'), deferred as Minor — cost if wrong: medians over 1000 show as 2527.3 while fuel shows 4 818.
14. fix the failure note now, as Important for this project — it breaks the plan's own contract that results.css styles every class Task 9 builds (Task 9 writes no CSS), the Arabic is the page's first language, and the fix is two rules plus a test pin; fix round 1: `.rc-chart-error{margin:12px 0;font-size:11px;line-height:1.75;color:var(--rc-muted);text-align:center}` and `html[dir=rtl] .rc-chart-error{direction:rtl}`, pinned in charts-lib.test.mjs (both rule strings, and rc-chart-error in the class list) — cost if wrong: one small fix round.
15. the lab's own chrome on the tab (the nav underline, the dark-mode focus ring) is outside spec 7.3's "no red and no green", which says "as on /agents", where the same chrome stands — cost if wrong: a green focus ring on the tab's links in dark mode.
16. (1) and (5) enter fix round 1 although rated Minor — spec 4.1 ("never dropped silently", as Task 4's duplicate-seed ruling) and spec 5.1 with §2's success criterion 3 ("nothing on the tab is computed that a committed script does not compute") are binding; for 'total' every seed stays on the axis and in the table with dashes, and the difference is shown for 'total' only; code and tests in task-8-fix1.md — cost if wrong: one more fix round; the thermal panel loses a column no script backs.
17. Task 9's one changed test literal stands — the brief pinned the English knock_model note as "(drive C).", which Task 6's fix 0497c1e changed by ruling; the view code is the brief's — cost if wrong: none (the test follows the string).
18. (A) and (B) enter fix round 1 — (A) spec 5.2 says secondary facts appear under their own labels in every state, a changed file reads "changed since its last commit" and forced lines are quoted, and the first re-run seed makes a section mixed; (B) Jad switches language often and the spec's "a language switch redraws every chart" does not license losing the reader's place — cost if wrong: one fix round on DOM code checked in headless Chrome.
19. (C) the plant line gets a separator between its label and its state (": "), although rated Minor — it shows on every section and reads «المحاكي أُجريت على محاكٍ آخر» in Arabic, the page's first language — cost if wrong: none.
20. Task 10's task review is one opus reviewer, not the four-lens workflow — its diff is documents and three tests, and the final whole-branch review that follows has a documents lens and a browser lens — cost if wrong: a documents defect waits for the final review.
21. fix round 1 corrects both, and two inaccuracies in the controller's own ruling text: the Ctrl+F5 paragraph's "in the hours before" (a cached copy can last days when the file had not changed for weeks) and "this update" (named instead), and the record's ambiguous "That covers every later update"; the record gains a Task 10 line — cost if wrong: none (documents only).
22. one fix wave (final-fix.md): F1 heading scoped + a line naming the absent agent sets (R1b); F2 the intro, README and CLAUDE.md layout (guarded) say the one figure computed; F3 the failed build logged via uvicorn.error and named on the page by status and type; F4 the not-read list separates path and reason, monospace for the path only; F5 "Repository at commit", "run from commits" (spec 5.2: commits say what kind they are), and an unambiguous unpaired line; F6 reload, Back and #exp links keep their place — F5 and F6 although rated Minor/split, because each is a false or misleading sentence on the page or the place-keeping Task 9 already ruled on — cost if wrong: one fix wave over strings, CSS, results.mjs and results_api.py.
23. the other 46 triaged items stay deferred as the triage lens recommends, and the final review's other minors (a new protocol reads "not known here"; an unreadable seed file is not named in its section; the import-failure line promises more than sections say; facts lose layout in some states; tables thinner than tooltips; marks without accessible names; the thermal panel reuses the dashed-line sentence; draw coordinates untested; real-tree pins turn red on a fourth experiment; README Tests section stale; no test pins the no-network rule) go to the hand-off as known limits — cost if wrong: they surface in R1b's work instead.

## Deferred minor findings, by task

### Task 1

- test_results.py:161 checks the 24 frozen files against the live fingerprint.FATAL, so a field added to FATAL later fails all 24 for a non-parser reason (plan-mandated test; pin the eight names literally?)
- no test pins thermal == {} for a heading with no parsable line, nor "a field that appears twice keeps its first value" (both probed correct by the reviewer)
- a policy row accepts nan / inf as numbers, as analyse_phase_d.parse does, while the knock-term regex rejects them (no change: the contract says "as analyse_phase_d.parse reads them")
- results_eval.py:4 names app/results_data.py before Task 4 creates it (intended forward reference)
- d2_seed07.txt and d2_seed7.txt both parse to seed 7; discover_evaluations keeps the later in sort order and lists neither as not read

### Task 2

- _REF and _OBJECT_ID end in $, which also accepts one trailing newline (git still rejects it); fullmatch would make the docstring exact
- test_results.py:526-527 cannot show that an unusual ref is refused WITHOUT running git (only HEAD~1 discriminates); a spy on subprocess.run would
- no test for the "timeout" and "error" reasons, the rename branch of status, or derived_loaded_differs against the real derived module (a rename of _CACHE would make it return False forever)
- test_live_side `continue`s on import_errors, so a regression that makes every protocol raise would still pass
- the temp-repo test inherits GIT_DIR / GIT_WORK_TREE / GIT_INDEX_FILE (only matters if the suite ever runs from a git hook)
- test_results.py's docstring says fixtures use only write_text / write_bytes, but the new tests also mkdir and run git init / commit in temporary directories

### Task 3

- ghassan-before-merge's code-only plant hash equals this tree's, so a file on this tree's code that differs only in derived constants (or episodes_sha) reads "another" with tag ghassan-before-merge (spec-literal tag rule; tag only when plant_sha differs?)
- tag_for annotates plant_sha: str although it accepts None (the Interfaces say str | None)
- no test pins one-sided-before-restart, nor the no_git_route reasons for "cleanliness not recorded" and "random_road.py unreadable"
- the rule that the literal text "None" counts as not clean (format_block's rendering of None) is implicit; a one-line comment would say it
- section_provenance collapses reason and tag to None when files share a state but differ in them; Task 4 and the page must read files, not treat None as "none"
- on the git route a random_road.py modified at run time is invisible (git_dirty_plant_files covers the three plant files only)
- app/test_results.py is 1,121 lines and grows with each task (plan-mandated layout)

### Task 4

- a later git loss (a timeout inside tag_for or the git route, after status and log were read) leaves earlier files' commit facts beside "git unavailable" (head is fixed in the fix round; the per-file case is not)
- the parse check reads NaN medians as a disagreement (nan != nan), and an exception inside analysis.parse costs the whole section where spec §4.4 says a failed check never hides one
- jsonable and the shared context (evaluate.PROTOCOLS, CLOSED_PREFIX) run outside the per-section try, so one non-JSON value or a shape change costs the tab, not a section
- a verdict reader that raises (e.g. a UTF-16 C4_RESULT.txt) loses the section's numbers and the error names no file
- the environment test cannot see import-time changes (runs after setUpClass built once); the fresh-process test checks DERIVING_PARAMS only, not OMP_NUM_THREADS
- no test for a seed past 9 (text order vs numeric order), nor that the real tree's not_read is empty
- setUpClass enters catch_warnings and makes the temp dir without addClassCleanup; the index-mtime and HEAD-after-build tests can flake while the other session runs git; test_temporary_tree_has_no_git assumes no repository above %TEMP%
- the build-timing line prints on every suite run
- results_data.py:295-297 docstring and :330-331 comment claim "no git fact survives a git lost part-way through the build", but a loss inside classify_eval (a timeout in tag_for or the git route) leaves earlier files' commits (the deferred per-file case); reword to "built.head is None whenever built.git reads unavailable"
- a KNOWN prefix whose every seed is named twice reads unavailable/missing with the re-run command although its files exist (spec 5.6 says no re-run advice for a present file); near-impossible
- the Python wording guard's English half is whole-word (current\b, fresh\b), so "currently" and "freshly" pass, while Task 6's Node guard bans them (\bcurrent, \bfresh)

### Task 5

- test_one_build_at_a_time does not show that a second request waits (a refuse-when-busy lock or a never-released lock both pass)
- app/test_results.py imports TestClient at module level, so the whole suite needs httpx, which no requirements file lists; lazy import or skipUnless would keep Tasks 1-4's tests runnable on a lab-only install
- /results answers Starlette's bare 500 without no-store when results.html is missing or not UTF-8, and POST 405s carry no no-store; no test of the page-read failure path
- test_the_page_is_read_on_every_request makes one request, so it cannot tell "every request" from "first request"
- app.test_results' output gains a StarletteDeprecationWarning line (from importing fastapi.testclient; app.test_agents had it before R1a)
- results_api's docstring says mounting loads no other module of the tab, but results_provenance imports results_eval
- server.py's route paragraph says the routes read results/, but the build also reads data/, the plant files and runs git; no blank lines between LIMITS and the new class
- a failed build leaves no trace on the server side; the tab's modules load at two different times (mount and first request), so a pull while the server runs can mix code with no hint
- nothing pins that the route's catch stays (Exception, SystemExit)

### Task 6

- English budget_c1's "50 000" uses an ASCII space (breakable) while the formatter writes U+202F
- the tests pin neither the key set nor its order (the contract check runs one way), and the invisible-character lists miss NBSP, ZWNJ, ZWJ, WJ and SHY
- inline() isolates only for the literal 'ar', while t() resolves unknown language codes to Arabic
- nothing pins the server's emitted reasons and note keys to the string keys
- "The preregistered verdict" heads Phase D's post-hoc cell too; the Arabic «الحكم المسجَّل مسبقاً»
- the intro says "Nothing here is recomputed", but the tab subtracts blind minus sighted per seed
- the Arabic subtraction order and the sighted/blind labels are not pinned
- the wording guard bans "preview does not help" in Arabic but not "preview helps", and misses common forms of "latest" and "current"
- «تُكمل وكلاء {other}» reads as "completes {other}'s agents"
- results.chart.mei_after types "22 September" without naming its file

### Task 7

- in Arabic the y-axis title (HTML) aligns right while the ltr chart draws its y axis on the left
- crosshair() and nearest() are copied without arrow-key stepping (spec 7.3) — R1a draws no crosshair chart; the contract defers it to R2 and the build record says so
- createMounter's error hook covers draw() only (a throwing hOf or onError escapes render() and stops the other charts), and a failure note stays after a later successful draw
- redrawing inside the ResizeObserver callback sometimes raises "ResizeObserver loop completed with undelivered notifications" in Chrome's console (7 of 8 probe runs with focusable marks); spec 9's browser check wants no console error
- on a touch screen, tapping a second chart leaves the first chart's tooltip open (copied from the template)
- baseline and reactive differ only in lightness and are both squares side by side on the hand figure
- #not-read-list is set in Consolas, Arabic reasons included (a recon §3 defect reintroduced)
- the stylesheet test pins selectors not declarations; the no-red/no-green guard sees only 6-digit hex; the plot/hline options R1a passes, the tooltip placement and the observer's height-only path are not pinned; copied helpers R1a does not call are mostly unpinned
- charts-lib.mjs's header list of adaptations omits two behaviour changes from the template

### Task 8

- tests use seeds 0..7, so none can tell a seed from its index; draw tests check no coordinate (every mark could sit at zero); the MEI bracket's height and placement are untested; no test has one seed without current-grade among seeds that have it, or a role missing from every seed; the colour guards miss named colours; the ROLE_VAR test never reads results.css
- tipTitle passes the seed already isolated into results.tip.seed, whose Arabic isolates {seed} again (nested isolates; the strings contract says pass it bare), pinned by the brief's test
- spec 3.2 says the MEI bracket is labelled "MEI, set 22 September, after this result" on Phase D and UNLABELLED on D2 and C4, but the chart writes an SVG "MEI" on every section (the HTML lines under the chart carry the Phase D sentence)
- the invisible-character guard is narrower than the tab's own list

### Task 9

- the noscript line on /results talks about drive data and a 3D scene (copied from /simulation), and leaves «JavaScript» unisolated
- Arabic list slots ({list}, {seeds}) put one isolate around the whole list with a Latin comma, not one per item; "<path>: changed since its last commit" is built outside the string table
- the per-section guard cannot catch what it targets (summaryRows runs the same helpers unguarded first, and the failure reads as a fetch failure); a failed build shows only the status code, not the type the server sends
- files not read: path and reason run together; «آخر commit a3a048e (…)» does not say whose commit; the Arabic scenario quote sits flush left; the pairs "what" line claims a dashed current-grade line even when the layout has none
- tests: the view's own isolation is unguarded where it is the only isolate; the 'never the catalog's' verdict guard cannot fail; role="group" on chart hosts pinned nowhere; the placeholder check sees only literal-key t() calls; server-reachable view branches untested; results.mjs failure rendering runs in no test; four aria-label/title attributes differ from STRINGS.ar; PageTests repeats imports and lists
- "With five links" in a modified test_agents.py docstring (a count in a .py docstring)

### Task 10

- README's maintenance sentence omits the restart a new drive needs (the page says it); README's example command is a path only Jad's machine has; the Ctrl+F5 paragraph is not pinned by DocsTests
- CLAUDE.md's layout list: static/sim/results*.mjs misses results.css, charts-lib.mjs lacks its folder, charts-fake-dom.mjs unlisted, one line 87 columns
- the launcher test passes even if the results line moves inside the `if ($LASTEXITCODE -ne 0)` block
- the record's commit list stops before its own commit without saying so; "first request" means the first /api/results request; Task 9's changed test literal is not in "What the reviews changed"
- "Nothing is recomputed" in app/README.md and CLAUDE.md's layout (the tab subtracts blind minus sighted per seed, which the analysis scripts print), as Task 6's intro string
- the record's Task 5 line still says "before this one"

## The whole-branch review

Six lenses reviewed the branch (spec, correctness, security, the page in a
browser, tests and documents, and a triage of every deferred minor above).
Security found nothing to fix. Five items were fixed before merge (the build
record lists them); the triage kept the rest deferred, and the review's own
minor findings are these known limits:

- a protocol other than phase-d and d2 reads "not known here" (the live side compares only those two);
- an unreadable seed file is listed under files not read but not named in its own section;
- the import-failure line promises that every section names the module, and sections do not;
- some plant facts and their raw lines lose their layout in some states;
- the folded number tables hold fewer numbers than the tooltips, and the IQR appears nowhere;
- focusable chart marks have no accessible name, and the tooltip is not announced;
- the panel without the knock term reuses the sentence about the dashed current-grade line;
- the draw steps' coordinates are not tested;
- six real-tree tests turn red the first time a fourth experiment appears, with no note that they are pins;
- app/README.md's Tests section and file list were not updated for the tab;
- no test pins the no-network rule or that subprocess is used for git only.

## After the final fix wave

The fix wave's own re-review found nothing to fix before merge and left four
small points, parked rather than fixed (the process allows one fix wave):

- a doc comment in `app/static/sim/results-view.mjs` (about line 257) still quotes the old unpaired line;
- when the URL carries a fragment, Reload or Back lands on the fragment's section rather than on the reader's last place (still better than the top of the page, as before the fix);
- the unpaired line reads "its file holds only —" for a file with no agent arm, and names only the agent arms of a one-arm file;
- the build record's "checks, as printed" table carries Task 10's counts; after the fix wave the Python suite runs one test more and the node suite one more.

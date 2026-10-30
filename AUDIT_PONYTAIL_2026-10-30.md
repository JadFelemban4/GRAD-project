# Code audit (ponytail-audit), 30 October 2026 — report only

Branch `JMF-2340550-anatomy-housing` at `dff4cd3`. Nothing in the code, the data or
the results was changed by this audit. Scope: the whole code, as Jad chose it:
the core (`plant.py`, `thermal.py`, `engine_env.py`, `derived.py`, `train.py`,
`fingerprint.py`, `evaluate.py`), `app/` (Python and browser code), the learning lab
(`Explanatory Simulation/`, with `presentation/` skimmed), and the 67 other root scripts.

**How it was done.** The lead session read the core in full. Five helper agents
(Opus) read the other parts, one each, and ran small throwaway probe scripts outside
the repository to confirm what they found. The lead re-checked the four strongest
claims in the code itself (findings 1, 2, 6 and 13) and re-ran the probe behind
finding 1. Every finding says how sure it is and whether it was already known.
`git status` was clean before and after every helper.

**Known before this audit, and not reported as new:** the learning lab's suites
(Python 4 of 35 failing, Node 1 of 147: pins from before the 8 October plant change),
`app.test_agents` 22 failing, `app.test_simulation` 1, `app.test_results` 1 (needs
`pwsh`). The full list of known items is the last section.

---

**What this repo does:** A physics simulator of the GR Supra's B58 engine, its turbo
housing and its cooling, fitted to read-only phone logs of the car; reinforcement-learning
agents trained on it to protect the turbo, compared in sighted/blind pairs to test when
looking ahead (preview) is worth having (H/τ). Around it: a local web app that replays
and reads OBD-II drives, a teaching lab, and scripts that fit, validate, score and
publish the results.

**Load assumed:** one student at a time, on a laptop, running scripts by hand; training
runs launched in parallel on one PC and limited by RAM; the app and the lab served on
`127.0.0.1` to one browser. That browser also opens other websites, which matters for
finding 4.

---

## Must fix

1. **The "+1.9 %" boost check compares two different sets of samples, and drive C's input uncertainty is built on it** (`model_vs_data.py:L116-150`)
   - **What this is:** The one independent check of `plant.charge_temperature`: the model's inverted manifold pressure above 200 kPa, against the car's own boost channel above 15 psi, median to median.
   - **Problem:** The model side drops the rows where the air-flow sensor was pinned at its maximum (`model_vs_data.py:L123`); the car side keeps them (`L138-140`), and those are the highest-boost rows. With the same rule on both sides (air flow below 1019.9 kg/h, the rule `build_dataset.py:L272` uses), the gap is +3.96 % over 740 logged rows, not +1.91 % over 1097. Paired row by row it is +6.7 %. `drive_c_rule_numbers.py:L163-186` turns the 1.9 % into 6.3 K of charge temperature, which gives `U_CHARGE_DEG` 0.86° and `U_INPUT_KI` 0.032 (`drive_c_analysis.py:L397, L404`); at 4.0 % the same code gives 1.79° and 0.070. That moves item 8's retune bar from about 1.7° to about 3.6°, and item 7's from 0.10 to at least 0.14. A third copy of the check, `plot_sim_vs_car.py:L396-397`, already disagrees (+3.8 %, no drive-B exclusion) under a comment that says it is the same computation.
   - **Fix:** On the car side, keep only rows whose own air flow is below 1019.9 kg/h. Make it one function in `model_vs_data.py` that `verify_docs.py:L2045-2083` and `plot_sim_vs_car.py` import. Then sweep the 1.9 % (mistake 11). **Drive C's rule is frozen: do not edit its constants.** State the corrected input uncertainty beside the stage C result and let Jad and Ghassan decide what it changes.
   - **If we skip it:** The charge-temperature model looks twice as good as it is, and drive C's spark and knee decisions run on about half the real input uncertainty.
   - **Sure:** Confirmed by running. The lead re-ran the probe: "as shipped +1.91 %, n 1097"; "MAF not pinned, n 740, +3.96 %". The paired figure and the 1.79°/0.070 come from the helper's probes, which reproduce the committed 0.85°/0.032 at 1.9 %.
   - **Known:** New. `docs/MISTAKES.md:553-556`, `verify_docs.py:2052` and `plot_sim_vs_car.py:372` say the gate matches the two sets "by construction"; that holds for pressure, not for the pinned rows.

2. **`python run_results.py` overwrites X1's published scores on any machine without the agents** (`run_results.py:L183-206`; default set at `L149`)
   - **What this is:** `phase_d()` finds the agents under `runs/extremes_dt1/`, scores them with the four hand-written policies, and writes `results/phase_d_extremes_dt1_raw.json` and `.txt`.
   - **Problem:** `runs/` is not in git. On a clone, or on this disk today, the search finds nothing, the plant check loops over nothing, and the committed file (1000 rows, 50 policies) is rewritten with the hand-written policies only (80 rows, 4 policies). `README.md:911` gives `python run_results.py` as the regenerate command, and `.claude/rules/data.md:40` says to run `run_results.py phase_d` after every new drive.
   - **Fix:** In `phase_d()`, `if not agents: raise SystemExit(...)` before the write. Better: also refuse when the file on disk names agents this run would drop.
   - **If we skip it:** The next "regenerate everything" deletes X1's per-episode record without a word, and `git commit -a` makes it permanent.
   - **Sure:** Confirmed by running (the helper sent the writes to a scratch folder): published 1000 rows / 50 policies, would write 80 rows / 4 policies; `runs/extremes_dt1` absent. The lead read the code: nothing stops an empty list (`L185-205`).
   - **Known:** New.

3. **`analyse_x1.py` and `analyse_x2.py` rewrite their published result with a fallback sentence, and `full_run.py` runs `analyse_x1.py` every time** (`analyse_x1.py:L152-164, L174-180`; `analyse_x2.py:L59-65`; `full_run.py:L141-143`)
   - **What this is:** Run with no arguments, both scripts always rewrite `results/X1_RESULT.txt/.json` (or X2's). Their "yardstick" line is read from `current-grade/eval_record.npz`, which is not in git.
   - **Problem:** Without that file, the measured line "1 of 719 demand steps" becomes the fallback "no per-step record of current-grade here; measured before training…", and the `yardstick` key disappears from `X1_RESULT.json`. `full_run.py` does this even with `--quick`. This is mistake 19's shape: a fallback that reads like a result, written into a committed file.
   - **Fix:** Write only behind an explicit `--write` flag (or only when the new text equals the file on disk); `full_run.py` calls them without it.
   - **If we skip it:** A full run followed by `git commit -a` replaces a preregistered, measured output with a fallback.
   - **Sure:** Confirmed by running `analyse_x1.report` in memory and diffing it against the published file: every statistic matches; only line 71, the yardstick, changes.
   - **Known:** New.

4. **The app's car-data routes and its live websocket answer any website open in the same browser** (`app/server.py:L209-250, L295-317`)
   - **What this is:** The results, records and artifacts routes refuse a request whose `Host` is not local. The server's own routes and `/api/agents/*` have no such check: `/api/replay/trips`, `/api/replay/trips/{id}`, `/api/state`, `/api/review`, `/api/status`, and the live feed `/ws`.
   - **Problem:** With `Host: evil.example:8000` the four server routes answered 200 (the trip list showed all 11 drives), while `/results` answered 403. `/ws` accepted `Origin: http://evil.example` and sent its first frame; browsers let any page open a websocket to localhost, so this needs no trick at all. With DNS rebinding a page can also read a whole recorded drive, and start or cancel an agent build through the GET `/api/agents/episode?...&preempt=1`.
   - **Fix:** One `@app.middleware("http")` in `server.py` that refuses any Host other than `127.0.0.1`/`localhost`; in `ws()`, close before `accept()` unless the Origin is `http://localhost:<port>` or `http://127.0.0.1:<port>`. Then delete the four per-module copies of the check (`agent_api.py:306`, `artifact_api.py:12`, `record_api.py:14`, `results_api.py:41`); keep `same_origin` for the POSTs. One test: a foreign Host gets 403 on `/api/replay/trips` and `/api/state`.
   - **If we skip it:** While the app runs, any website in the browser can read the live or recorded drive, which the server's docstring says never leaves memory.
   - **Sure:** Confirmed by running (FastAPI `TestClient` on `app.server.app`).
   - **Known:** New.

5. **The live dashboard shows a cooling rate of about −1200 K/s after any blank sample** (`app/static/index.html:L216-220`)
   - **What this is:** The turbine trend on `/`, computed in the browser from two websocket messages in a row.
   - **Problem:** When a sample is blank (no rpm, no air flow, or MAP under 15 kPa) the estimator sends `t_turb_c: null`, and JavaScript turns `null − 601` into −601. After (10.0 s, 600 °C), (10.5 s, 601 °C) and a blank at 11.0 s, the page shows "−1202.0 K/s" while every other field correctly shows "—". No test opens `index.html` or `driver.html`.
   - **Fix:** Compute the trend only when both values are numbers; otherwise show "—".
   - **If we skip it:** Every key-off or drop-out on a live drive shows an absurd cooling rate beside the turbine estimate.
   - **Sure:** Confirmed by running the page's own script on a fake page: "after one blank sample, trend = −1202.0 K/s | turbine = —".
   - **Known:** New. `AUDIT.md` L4 fixed the stale fields, not this computed one.

6. **The results tab's "Files not read" box hides the files whose names are wrong** (`app/static/sim/results.mjs:L258-275`, the same pattern at `L658`)
   - **What this is:** The box that lists result files the tab could not read, with the reason.
   - **Problem:** It keeps an entry only if its name parses as `<prefix>_seed<N>.txt` with a prefix of a section selected now. A file listed for a bad name (`results/C4_seed9.txt`, `results/c4_seedA.txt`) can never match, so no selection ever shows it. With five entries sent and C4 selected, the page listed one. This breaks the contract in `app/results_data.py` ("never dropped silently") and the tab's design (`docs/superpowers/specs/2026-09-30-results-tab-design.md:138`).
   - **Fix:** Also keep entries whose prefix belongs to no section, or drop the filter. Add one page test with a non-empty list; every test today sends an empty one.
   - **If we skip it:** A mistyped result file disappears from the tab built to show that nothing disappears.
   - **Sure:** Confirmed by running ("server sent 5 not_read items", one row shown).
   - **Known:** New.

7. **In the learning lab, setting a grade jumps it in one step, which brings back the knock spike the 8 October ramp removed** (`Explanatory Simulation/backend/simulation.py:L273-275`)
   - **What this is:** The lab's road control writes the new grade into every remaining sample at once. Lesson 1 asks for exactly this: "set grade from 0% to 12%, then advance 30 s" (`content.json:1880`).
   - **Problem:** Since 8 October the plant ramps every grade change over 8 s (`engine_env.GRADE_RAMP_S`), because a one-step change drives the knock integral to about 2. A flat 60 s, then 12 %: the first step shows knock integral 2.019 (above the 1.0 line) and one extra knock event; the same climb as an 8 s ramp peaks at 0.93. The scenario text still says "level for 180 s then 12% grade" (`content.json:2168`, `content.ar.json:2229`).
   - **Fix:** Ramp toward the new grade over `GRADE_RAMP_S` (imported from `engine_env`), restarting the ramp only when the target changes (the page re-sends the grade every step). Reword the text. Add a test that the first step after a change is still below the target.
   - **If we skip it:** Every student who does lesson 1 sees a knock event the model no longer produces.
   - **Sure:** Confirmed by running: knock integral per step [2.019, 0.685, 0.551, …] with the jump, [0.791, 0.904, 0.928, …] with the ramp.
   - **Known:** New. The three known `test_simulation` ramp failures are a different path.

## Should fix

8. **The document guard cannot see a single experiment result, and its own test cannot tell** (`verify_docs.py:L1809-2108`, exemption comment `L874-888`; `drift_test.py:L114-147`, verdict at `L136`)
   - **What this is:** CLAUDE.md says to run `verify_docs.py` before quoting a number in the thesis. `drift_test.py` proves the guard works by planting a wrong figure in a copy of the tree.
   - **Problem:** None of the 74 checks reads `X1_RESULT.json`, `X2_RESULT.json` or the D2/C4/Phase D results, so "10 of 23", "−10.35 / 24.78", "sign p 0.0173", "1 of 5" and "3 of 8" can drift in `results/README.md`, `CHECKPOINT.md` and the thesis drafts while the check stays green. Changing "10 of 23" to "11 of 23" in a copy of `results/README.md`: drift_test printed "MISSED … green run, exit 0". And `drift_test.py` counts ANY non-zero exit as caught, without first running an unmodified copy: if `verify_docs.py` is red for another reason, all 16 rows still say CAUGHT.
   - **Fix:** Add `figure()` checks that read the committed X1/X2 JSON and `analyse_phase_d2.load()` (pairs positive, mean, sd, sign p), with patterns over every document, as the premise figures already have; add one such row to `drift_test.DRIFTS`. In `drift_test.py`, run a clean copy first and stop unless it exits 0; count a row as caught only when a WRONG line names that row's file.
   - **If we skip it:** The numbers an examiner checks first are the only ones the guard cannot see.
   - **Sure:** Confirmed by running (`drift_test.run_one` on a scratch copy). The drift_test control gap is from reading, high.
   - **Known:** New. `AUDIT.md` H2 found the same blindness for the simulation figures; results were never added.

9. **P-values no preregistration names are printed beside the preregistered test** (`record_agents.py:L191-199, L286-287, L733`; `run_results.py:L131-142, L241-244`; `make_page.py:L146-147`; `make_figures.py:L358-364`)
   - **What this is:** Paired t-tests, Wilcoxon tests and t-based intervals on the same sighted-minus-blind differences, written into committed tables, figure titles and the page.
   - **Problem:** `results/agents/extremes_dt1/README.md` says "paired t-test p = 0.058, exact Wilcoxon p = 0.234" for X1, unlabelled, beside the preregistered reading (smaller than the MEI). `make_figures.py:363-364` labels a panel "preview HELPS / HURTS" from a t interval. And the home-made Wilcoxon gives tied values different ranks, so the answer depends on order: `[1,-1,2,3]` gives 0.375, `[-1,1,2,3]` gives 0.25 (scipy: 0.375 for both).
   - **Fix:** Delete them. If any stay, label each "not the preregistered test" and use `scipy.stats.wilcoxon`.
   - **If we skip it:** Someone quotes "p = 0.058" to a supervisor, and no preregistration supports it.
   - **Sure:** Confirmed by running (the tie case); the sentences were read from the committed files.
   - **Known:** New.

10. **Two scripts score trained agents without the plant check `evaluate.py` enforces** (`knock_margin.py:L65-86, L127-137`; `logged_check.py:L186-196, L264-266`)
    - **What this is:** Both load `final.zip` and run the live environment; neither reads `meta.json`.
    - **Problem:** `runs/blind_seed0/meta.json` records plant `b5a3069f32a83754`; the live plant is `3c48890dd15bc116`. `evaluate.py` refuses that agent (checked). `python knock_margin.py runs` would score it and write `results/agents/runs/knock_margin.json` without a word. `logged_check.py` also resumes from an existing JSON that records no plant, so one file can mix two plants.
    - **Fix:** Call `evaluate.check_model_fingerprint(...)` for each agent before scoring, as `evaluate.py:441-457` does; in `logged_check.py` store `plant_sha`/`derived_sha` in the JSON and refuse to resume on a mismatch.
    - **If we skip it:** A number from one plant is reported as a result on another: `AUDIT2.md` C2-1 through a side door.
    - **Sure:** The refusal in `evaluate.py` confirmed by running; the two missing checks from reading, high (not run: they write results).
    - **Known:** New.

11. **`evaluate.py` decides which agent is blind from the folder name, not from `meta.json`** (`evaluate.py:L467`, `L522-524`)
    - **What this is:** Before scoring an agent, evaluate.py decides whether to zero its preview input.
    - **Problem:** It tests `"blind" in path` on the whole path and never reads `use_preview` from the `meta.json` it has just loaded. `python evaluate.py runs_blindtest/sighted_seed0` scores a sighted agent with its preview zeroed; a blind agent in a folder without "blind" in its name gets a preview it never trained with. The "SIGHTED over BLINDED" line then compares the wrong arms, and the result file does not show it.
    - **Fix:** Take the arm from `meta.json`'s `use_preview` and refuse when the path disagrees: the rule `app/agent_catalog.py:345-348` already applies.
    - **If we skip it:** One misnamed folder gives an ablation number with the arms swapped.
    - **Sure:** From reading, high.
    - **Known:** Partly. The app knows and guards it (`app/agent_catalog.py:341-348`); `evaluate.py` itself was never changed.

12. **The plant fingerprint counts two kinds of text as physics** (`fingerprint.py:L98-176` with `plant.py:L353-355`; `fingerprint.py:L247-263` with `data/derived_params.json`)
    - **What this is:** `plant_sha` and `derived_sha` decide whether a trained agent may be scored. Both promise that docstrings and "_" bookkeeping keys do not count.
    - **Problem:** (1) `_code_only` drops only the FIRST string of a module, class or function. The explanation under `EXH_BACKPRESSURE_RATIO = 1.15` (`plant.py:353-355`) is a bare string, so it stays in the hash: rewording it moves `plant_sha`, while the same edit in a real docstring does not. (2) `derived_sha` skips "_" keys only at the top level; inside the sections they are hashed (`thermal._method`, `._drives`, `._excluded`, `._fit_*_rmse_k`, `boost_ceiling._method`, `enrichment._method`, `spark._method`, …). Rewording `spark._method` in a copy of the file moves `derived_sha`; changing the top-level `_generated` does not.
    - **Fix:** (1) Make `plant.py:353-355` a `#` comment, or have `_code_only` drop every bare string. (2) Skip "_" keys at every depth. Both fixes move the hashes once, so ship them with the next planned plant change, not alone.
    - **If we skip it:** A wording edit (a documentation sweep, or rewording a `_method` line in `derive_params.py`) makes `train.py` and `evaluate.py` refuse every current agent, and the easy way out is `--force-plant-mismatch`, the habit `_code_only`'s own docstring warns about.
    - **Sure:** Confirmed by running on temporary copies.
    - **Known:** New. `test_plant_guards.py:107` tests only the top-level `_generated`.

13. **The replay reader serves a channel that is zero on every row as a real 0 °C reading** (`app/reader.py:L316-325`)
    - **What this is:** `AUDIT.md` M8's guard masks the logger's placeholder zeros at the start of a column.
    - **Problem:** It starts at `idx = 0` and moves only when it finds a non-zero row, so a column that never leaves zero is never masked. Drive `f51686d7` has coolant and oil at 0 on all 211 rows; the reader serves `ect_c = 0.0` and `oil_c = 0.0` on every sample, and `/simulation` shows them as recorded. On a running engine that would seed the block at 273 K, the M8 symptom.
    - **Fix:** Start with `idx = len(self.rows)` (one line). Add `f51686d7` to `test_placeholder_zeros`: every `ect_c` is None.
    - **If we skip it:** Any log whose coolant or oil never answered shows 0 °C as a measurement.
    - **Sure:** Confirmed by running; the lead read the loop. (The engine is off in that log, so the estimator never ran on it.)
    - **Known:** Partly: `AUDIT.md` M8 fixed only the leading run of zeros.

14. **In live mode, a missed reading's old value is served as fresh** (`app/reader.py:L528-540`)
    - **What this is:** When the car answers NO DATA, the live reader copies the last good value into the sample for every channel, the fast ones (rpm, air flow) included.
    - **Problem:** Its own docstring (`reader.py:65-66`) says a missed channel stays empty and the estimator marks what depended on it as modelled. With a fake adapter, air flow answered 300 kg/h once and then NO DATA four times: all five samples carried 299.9988 kg/h, `ok` stayed true, and nothing was marked modelled. At 7 channels that is about 6 s of a lift-off computed as full load, feeding EGT, the turbine trend and the mismatch check.
    - **Fix:** Hold only the slow channels: line 538, `if c.min_period_s > 0 and c.field in held:`. Add a one-miss air-flow case to `test_live_reader_degrades`.
    - **If we skip it:** Stale load is shown as measured data on the live path (mistake 19).
    - **Sure:** Confirmed by running with a fake `obd` module. Not tried on the car.
    - **Known:** New. `AUDIT.md` M9 covers a different part.

15. **The "+0.75° spark" sensitivity row now measures nothing** (`validation_numbers.py:L42, L113-115`)
    - **What this is:** The R1 sensitivity table adds +0.75° to the neutral spark trim and runs the locked climb.
    - **Problem:** Since 8 October the environment clips the trim at 0 (`engine_env.py:876`, `SPARK_TRIM_MAX`). On today's plant "+0.75" gives damage 848.1, the same as "none"; only −0.75 moves (964.1). The committed JSON is from before the cap, so the pending recompute will print a silent zero, and `car_spark_boost.TURB_K_PER_DEG` and the validation plan's "1.3° of spark" come from this row.
    - **Fix:** Shift `BaselineECU.base_spark` by ±0.75°, as `drive_c_rule_numbers.climb` already does, or assert that the applied trim equals the requested one.
    - **If we skip it:** The spark sensitivity is halved on the next run, with no warning.
    - **Sure:** Confirmed by running on the live plant (none 848.1, +0.75 848.1, −0.75 964.1).
    - **Known:** Half: the stale JSON is in `SESSION_REPORT_2026-10-08_records.md:478`; the clip is new.

16. **The thermal fit's constants are set by the random seed, and the fit uses the census log the project calls unusable** (`calibrate_thermal.py:L96-111, L251-256`; `derive_params.py:L68-86`)
    - **What this is:** `derive_params.py` ships one seed-0 search for the block and oil constants, over every log that carries coolant, oil and ambient.
    - **Problem:** The thermal fit's own 7 logs, searched with seed 1 instead of 0, fit equally well (oil RMSE 1.764 against 1.760 K) but move `ua_block_amb` +118 %, `k_oil_rpm` +20 %, `frac_fuel_to_oil` −14 %, `frac_fuel_to_coolant` +13 %, `c_block` +12 %. The locked climb barely notices (baseline 848.05 → 847.51). And one of the seven is `fb988991`, the 654-channel census log, which `build_dataset.py` rejects and `logged_check.py:66` excludes by name; dropping it moves the constants about as much as the seed does. `derived.py:13` says the method means "nothing is frozen at the value one person got on one day"; it is frozen at what seed 0 got.
    - **Fix:** Skip the census log in `usable_drives()`; run the search from several seeds and keep the best; write each constant's spread into `derived_params.json` and `thesis/LIMITATIONS.md`, and quote no single constant without it. This changes `derived_sha`: ship it with training gate item 1.
    - **If we skip it:** Constants the thesis may quote one by one (the radiator scale, the oil time constant, `c_block`) are an accident of the seed.
    - **Sure:** Confirmed by running (the seed-0 refit reproduces the shipped constants to every digit).
    - **Known:** Partly: mistake 25 says the coolant constants are weakly identified. The seed dependence, the oil constants and the census log are new.

17. **Two guards that let the write through when they should stop it** (`record_agents.py:L466-487`; `conditions_test.py:L756-775`)
    - **What this is:** `record_agents.py` stops if recording changed a score; `conditions_test.py --merge` says a re-run must reproduce the saved rows exactly.
    - **Problem:** If `record_agents.py`'s reference file is missing (a new set, or a typo), it compares 0 episodes, prints "all identical", and writes every table under `results/agents/<set>/`; `x1_score.py` and `x2_score.py` treat this as their regression check. `conditions_test.py --merge` prints "N differ" and then overwrites the published table anyway, with no plant check, so a re-run after a plant change silently replaces X1's transfer counts (for example "26 of 46" at 50 °C).
    - **Fix:** `if checked == 0 and a.set_dir: raise SystemExit(...)`; and `if differ: raise SystemExit(...)` unless `--accept-changes` is given.
    - **If we skip it:** Two published files can change with one console line as the only trace.
    - **Sure:** From reading, high.
    - **Known:** New.

18. **The exact permutation test cannot run at the seed counts the project plans** (`analyse_phase_d.py:L89-97`; `run_results.py:L131-142`)
    - **What this is:** `perm_test` tries all 2^n sign patterns in plain Python; every analysis imports it.
    - **Problem:** At 23 pairs one call takes 71.7 s, and `analyse_x1.report` (four calls) 302 s. `power_analysis.py` plans about 42 seeds a side; at 42 one call would take about a year (extrapolated), and the home-made Wilcoxon runs out of memory first.
    - **Fix:** Above about 20 pairs, a seeded Monte Carlo of about a million sign flips in numpy. The preregistrations say "exact", so the next one must name the method before training.
    - **If we skip it:** The next properly powered experiment's analysis never finishes.
    - **Sure:** Timings confirmed by running; the 42-pair figure is an extrapolation.
    - **Known:** New.

19. **Three pages warn "near the limit" by three different rules** (`app/static/index.html:L153, L177, L207`; `app/static/driver.html:L151`; `app/static/sim/panel.mjs:L134, L149`)
    - **What this is:** `/` and `/driver` turn orange from 70 K under the limit; `/simulation` from 50 K under it (`NEAR_K`) or when the steady state reaches it; `app/alerts.py` warns only on its projection.
    - **Problem:** At 790 °C with a steady state of 800 °C, `/` and `/driver` show orange, `/simulation` shows normal, and no alert fires. At 760 °C rising towards 900, the driver hears a warning chirp on a green screen. The 70 has no measurement behind it, against CLAUDE.md's rule that a threshold in `app/` changes only for a measurement written beside it.
    - **Fix:** Serve one band from `server.LIMITS` (for example `near_k: 50`, with `NEAR_K`'s docstring as its measurement) and read it in all three pages.
    - **If we skip it:** The same estimate gets a different warning colour depending on which page is open.
    - **Sure:** Confirmed by running the pages' scripts on a fake page.
    - **Known:** New.

20. **The lab's spark slider goes to +4°, but the plant has capped spark at 0 since 8 October, and the lab gives the wrong reason** (`Explanatory Simulation/backend/catalog.py:L177-201`; `src/ActuatorEditor.tsx:L29-30`; `src/model/supervisor.mjs:L21`)
    - **What this is:** The manual editor takes its slider ranges from `ACT_LO`/`ACT_HI`.
    - **Problem:** `engine_env.SPARK_TRIM_MAX = 0` clips the trim after the rate limit. Asking for +4° for 4 s: requested 4.0, applied 0.0 on every step. The lab labels the applied value "after the rate limit", which would allow 1.5° after one second; the student is taught the wrong cause.
    - **Fix:** Read `SPARK_TRIM_MAX` like the other constants and cap the slider at it; name the cap in the label; move the pin at `tests/test_catalog.py:20`.
    - **If we skip it:** Half the slider does nothing, and the lab explains it wrongly.
    - **Sure:** Confirmed by running.
    - **Known:** New.

---

**Verdict:** Not healthy yet. Fix 2 and 3 first (two commands can overwrite committed, preregistered evidence), then take 1 to Ghassan (drive C's input uncertainty), then 4 (the app leaks drives to other websites).

**Lean: about −900 lines, −0 dependencies possible** (all parts together; the largest pieces: `extract_steady.py` 171 lines, the thermal equation copies about 150 once gate item 1 lands, unused chart helpers about 65, repeated page code about 90, the second scorer about 100).

**Not checked:**
- Nothing that trains, and nothing that needs agents under `runs*/` beyond `runs/blind_seed0/meta.json`: the X1 and X2 agents are not on this disk.
- Not run: `app.test_agents`, `app.test_simulation`, `app.test_results`, `drift_test.py` in full, `test_reward.py`, `check_roads.py`, `npm run build` and `npm run figures` (they write into the tree), `build_dataset.py`, `derive_params.py` and `validate.py` against `data/` (their functions were called from probes instead).
- Run and passing: `verify_docs.py` 74 of 74; `app.test_replay` 49 of 49; `node --test` for the app 306 of 306; `python -m unittest test_drive_c_analysis` 105 of 105; the lab's suites with only the known failures; `tsc --noEmit` clean; `analyse_phase_d`, `analyse_phase_d2`, `analyse_c4`, `power_analysis` exit 0 and `analyse_c4` matches `C4_RESULT.txt`.
- Read partly: `app/results_provenance.py` (lines 1-200 of 605), `app/results_sets.py` (1-260 of 614), `app/results_comparisons.py` (1-120 of 463), `app/agent_catalog.py` 600-848; the 3D geometry in `app/static/sim/scene.mjs`, `engine-assembly.mjs`, `engine-casting.mjs`; `make_page.py`, `make_figures.py`, `plot_study_page.py`, `plot_agent_pairs.py` (statistics and labels only); `conditions_test.py`, `x2_agents.py`, `record_extracts.py`, `step_record.py`, `show_record.py`, `wide_air.py`, `random_road.py`, `training_roads.py` skimmed; `presentation/` skimmed.
- Nothing was opened in a real browser (layout, right-to-left, WebGL); live mode was not tried on the car.

---

## The rest of the findings

Kept, not dropped. Ranked lower than the twenty above; each was checked by the helper
that found it (how is in brackets). S = should fix, N = nice to have.

**Core**
- N. Preview horizons are cut, not rounded: `int(h / dt)` (`engine_env.py:791`). At dt 2.0, which `generality_test.py:110, 132` uses, the 15 s horizon becomes 14 s, and `generality_test.py:80` reads it. Fix `int(round(h / dt))` with the next plant change. (arithmetic)
- N. Pass-through code: `train.derived_sha()` only calls `FP.derived_sha()`, and its result is passed to `plant_fingerprint`, which computes the same field (`train.py:189-193, 526`); `evaluate.agent_policy`'s `use_preview` argument is unused (`evaluate.py:286`). About −8 lines. (reading)
- N. `plant.py:519` says "a 3.0 % gap" in a paragraph that otherwise quotes +1.9 % (and see finding 1). (reading)

**app/ (Python)**
- S. `--replay --loop` restarts time at 0 on each pass, so the alert windows stop trimming (`_hist` grew 84 → 2270 → 4456) and every cooldown stays active: pass 1 raised 4 alerts, passes 2 and 3 none (`app/reader.py:331-370`; `app/alerts.py:293, 335, 429`). Fix: keep time increasing across passes, about 3 lines. (running)
- S. An agent build re-checks every source file on every one of its 719 frames, 66 ms a check, about 48 s added to a build the README times at about 75 s (`app/agent_api.py:227-240`). Fix: check every 64 frames; line 256 still guards what is published. (running; full build not timed, SB3 is not installed here)
- N. A turbine warning silences the oil warning: both use the cooldown key ("thermal", "warn") (`app/alerts.py:290-298, 371-393`). Partly known (`AUDIT.md` L2, which also says the oil limit cannot be reached with today's parameters). (running)
- N. `VALID_MAP_HI` is 74 kPa (`app/alerts.py:234`) while the 26 steady points span 30.42-74.94 kPa (`data/master_points.csv`), so 74.5 kPa is flagged as between the evidence bands. The 74 comes from the old 22-point set (`AUDIT.md:217`). (running)
- N. A review file that cannot be written fails silently: `_persist` swallows `OSError` (`app/alerts.py:280-288`). Count failures into `/api/status`. (reading)
- N. Dead code: `app/record_reader.py:288` (two identical branches), `410-413` (a loop of only `continue`), `416-420` (an unused list); `app/artifact_catalog.py:90-96` `revisions()` and `170-172` `_source()` have no caller. About −20 lines. (reading, grep)
- N. The policy-folder naming rule from `record_agents.py:381` is copied three times (`app/record_api.py:51-52`, `app/artifact_catalog.py:489`, `app/results_sets.py:72-75`); import one. (reading)

**app/static (browser)**
- S. A summary link on `/results` throws away the comparison: in compare mode, clicking an experiment's name turns `#compare:exp-a:exp-b` into `#exp-b` (`app/static/sim/results.mjs:249`, hash handling `L98-107, L940-941`). Fix: the link only scrolls. (running)
- S. On the replay charts every line has its own hidden scale and only its maximum is labelled: turbine 300-850 °C and oil 85-95 °C both fill the full height under one "°C" footer (`app/static/sim/main.mjs:74-78`, `panel.mjs:78-95`). Fix: label the range. (reading)
- N. The "no recorded values" message piles up on each redraw: 1 after mount, 4 after three zooms, 5 after a resize (`app/static/sim/results-graphics.mjs:205-206`); swap two lines. (running)
- N. Unused chart helpers `crosshair`, `nearest`, `sideLabel` and the log scale (`app/static/sim/charts-lib.mjs:58-63, 81-82, 177-222, 234-246`) and `graphicsKeys` (`graphics-strings.mjs:247`); only tests use them. About −65 lines. (grep)
- N. Three copies of one string-merge function (`agents-strings.mjs:451-473`, `results-strings.mjs:397-419`, `artifact-strings.mjs:79-101`); one in `i18n.mjs`. About −45 lines. (reading)
- N. The `?v=` cache-busting suffixes are no longer needed (the server sends `no-cache`), and they make `/agents` load `scene.mjs` twice (`agent-scene.mjs:17` against `record-view.mjs:170`). Partly known: they are also the cause of the known `test_simulation` failure (`app/REVIEW_2026-10-09_full-app.md` F14). (reading)
- N. The same page code in three pages: preferences, theme and language buttons, the artifact strip, a repeated status phrase, a repeated citation format (`main.mjs:22-34, 577-633`; `agents.mjs:120-136, 639-671, 1493-1530`; `results.mjs:111-141, 643-690, 812-840`). About −90 lines with one shared module. (reading)
- N. "15 km/h" is typed into the gear note in both languages (`app/static/sim/i18n.mjs:154, 373`) while the server already sends `inference_min_kmh`. (reading)

**Root scripts**
- S. `build_dataset.py`'s "rejected N windows for wall-clock span", the line check 5 of the new-drive routine reads for logger gaps, counts only the end of the file: all 208 rejections over the 11 drives are the last window retried; drive10, with no gaps, prints 46 (`build_dataset.py:388-409, 431-434, 450-453`). Fix: stop at the end of the data. (running)
- S. `train_all.py`, the launcher used since 8 October, defaults `--jobs` to the CPU count with no memory check; only `run_phase_d.py` sizes it to free RAM, and its docstring records 13 of 16 runs dying at the first launch. X1 and X2 passed `--jobs` by hand. Also `x1_score.py` and `x2_score.py` are near-copies (about 115 lines each). (reading)
- N. `build_dataset.py` keeps an old CSV when a table comes out empty, so one wrong argument leaves `data/` in a state no command made (`build_dataset.py:676-687`). (running, into a scratch folder)
- N. `generality_test.py` keeps its own copy of the four hand-written policies (`L34-84` against `check_premise.py:89-144`); identical today, drifted once before (`AUDIT.md` C1). About −45 lines. (reading)
- N. `check_x2_convergence.py` reads each checkpoint's step count and discards it (`L96-104, L130`), so a short or extended `final.zip` would be judged without comment. (reading)
- N. `analyse_c4.py` section 5c labels seeds by position (`L391-399`); correct today because D2 is complete. (reading)
- N. The thermal node equations exist in three copies (`calibrate_thermal.py:162-177`, `substep_fit_check.py:40-55`, `thermal.py:223-253`); they agree today. Known: mistake 25, training gate item 1. (reading)
- N. `extract_steady.py` (171 lines) is a superseded near-copy of `build_dataset.steady_points` with every bug since fixed there; it crashes on drive B. Known: `AUDIT.md:498`. (running, into scratch)
- N. `plot_sim_vs_car.py` does not import (`L92`: `fit_envelope` was rewritten). Known: `SESSION_REPORT_2026-10-19_driveC-rule.md:53`. (running)
- N. Housekeeping, not code: two 68 MB copies of the tree left by earlier drift-test runs sit inside the repository, ignored by git: `.superpowers/sdd/2026-10-07-training-linked-app/tmp/drift5_h6a_8xcj` (7 October) and `app/.superpowers/training-linked-app/tmp/drift7_4bnl7r39` (8 October).

**Learning lab**
- S. Three "open it in the code" links land on the wrong line, and the fallback is silent (`backend/catalog.py:143-163`; `content.json:321, 619-621, 649` and the Arabic twins): `exhaust_flow` opens a comment at `engine_env.py:925`, `egt` opens `plant.py:311` instead of `315`, `turbocharger` opens a comment at `engine_env.py:770`. Eight more line numbers typed into the frontend have drifted (`src/PressureDiagram.tsx:24`, `src/model/pressure.mjs:5`, `src/Results.tsx:69`, `src/ProvenanceDrawer.tsx:18-19`). Fix: a `match` text on every reference and a test that the text is on the line (97 references; one fails today). Partly known: the `97.0 °C` text and the line-106 pin are the known `provenance.test.mjs` failure. (running)
- S. English and Arabic list different causes and effects for three concepts: in Arabic `fuel` affects `t_block` and `t_oil`, `rpm` and `ambient_temp` affect `t_oil`; English leaves these out (`content.json:449, 1213, 1325`). The map takes both, so in English the map card and the Inspector disagree. `tests/test_locale.py:13-16` does not compare links. (running)
- S. Four tour lessons point the Inspector at ids that are not concepts ("cylinder", "thermal", "reward", "results"), so it opens empty in 4 of 10 lessons (`content.json:1926, 1971, 2000, 2016` and the Arabic twins). (reading, script)
- N. Dead code and content: `initial_frame` and its branch (`backend/simulation.py:394-397, 315-320`), a no-effect `env._obs()` (`L225`), the never-shown `limitations` lists (`catalog.py:333`, `content.json:2187`), 57 unread `evidence_label_ar` fields; and near-copies (`reset_frame` against `_frame`, `_gear` against `Vehicle.demand`, two copies of the preview horizons). About −95 lines. (grep)
- N. The τ marker flashes at 0 °C for about 70 ms when it first appears (`figures/housing-lag/build.mjs:552-558, 603`). (running a copy of the page's logic)
- N. `/api/meta` takes about 2 s because it re-reads `content.json` about 97 times per call (`backend/catalog.py:76-77, 102-118, 143-149`). (timed)

**Smaller notes the helpers listed and did not count** (one line each, mostly from reading, not checked by the lead): `thresholdSpans` is one sample interval short per span; `/simulation` prints the limit as 849.9 °C where other pages print 850; the `/simulation` turbo rotor never turns (frames carry `t`, the scene reads `time`); `/results` renders twice on a hash change; two minus-sign styles; a dead `gearState` fallback; a reconnect can list an alert twice; a literal 8 gears in `buildGearStrip`; the preview ribbon rebuilt every frame; a stale "clamp" comment at `app/estimator.py:479-480`; a 1 s sleep cap after log gaps in replay; `results_data.jsonable` copies `agent_trace.jsonable`; `record_api._resolve` re-runs discovery per request; `scan_allowed` ignores the "RETIRED-OK: file" skip; the generated agents README prints the smallest Wilcoxon p as "0.0000"; `x1_score.py`/`x2_score.py` refuse forever if `LAUNCH.txt` is appended to after a failure; `power_analysis.py` types the MEI as 50.0 and keeps a hand-typed `PHASE_D_DIFFS`; `run_results.py` maps `runs` and `terrain_dt1` to the same files; `new_drive.py:105` calls rows warm above 70 °C, `build_dataset.py:590` above 75 °C; ambient fallbacks of 25, 30 and 42 °C typed in six scripts; `derive_params.py` imports a physics column from `verify_docs.py`; drive B's manifest row says "pts 7" while 0 are written; `derive_params.write` can leave out `deliverable_torque` if its subprocess fails (loudly); two Arabic message keys in the lab do not match the backend's text; `presentation/dump_traces.py` says it writes nothing but writes `traces.json`; `launch.py --check` calls `healthy()` twice; nothing checks the built lab figure against `params.json` (they agree today).

---

## Known before this audit (confirmed, not new)

- The learning lab's suites fail on a clean `main` the same way: Python 4 (`tests/test_catalog.py:83`, stale plant pins, which also hides line 86; three `test_simulation.py` tests expecting the grade step at 180 s), Node 1 (`provenance.test.mjs`) (`SESSION_REPORT_2026-10-30_learning-lab-figures.md` section 2; `team/jad.md`, "the learning lab's pins").
- Six lab texts still say the coolant update "oscillates at dt=1 s" (`Explanatory Simulation/docs/HOUSING_LAG_VALIDATION.md`, "Found, not fixed"). This audit found two more places with the same claim in other words: `content.json:1053` (and its Arabic twin), "Numerical stiffness in the block node currently prevents quoting the H/tau sweep", shown for `thermal_time_constant`; and `src/model/ui-copy.mjs:794`. Grep "stiffness" as well as "oscillat".
- The map's loose link `thermal_time_constant` → `preview` (`CONCEPT_MAP_VALIDATION.md`).
- `app.test_agents` 22 failing, `app.test_simulation` 1, `app.test_results` 1 (`CHECKPOINT.md`).
- The agent's own knock does not trigger the knock retard the baseline gets (`engine_env.py:915, 928`; `_merge_review/reports/physics-protocol-knock.md:186, 294`). Spark advance is now capped at 0; boost and lambda trims can still raise the agent's knock.
- The load loop is per step, not per second, and agents train and are scored at different steps (`engine_env.py:737-767`; `AUDIT2.md` H2-2).
- The thermal fit steps at 1 s while the network sub-steps at 0.1 s (`thermal.py:209-214`; training gate item 1, mistake 25).
- `train.py`'s `CLOSED` list lacks `wideair_dt1` (`CHECKPOINT.md`, next action 7).
- The app caches the plant fingerprint and `derived.py` caches its file per process; "Restart the server after changing a hashed file" is a stated decision (`app/agent_catalog.py:214`).
- `presentation/`'s stale figures and missing `data.js` packer (`AUDIT2.md` C2-3, M2-8; `AUDIT.md` L11).
- `drive_c_analysis.py` was checked against `results/DRIVE_C_RULE.md` item by item (D1-D6, V1-V8, items 1-8, the shams, blocks, cuts and verdict order): no bug found. `dry-run-spark` prints REPRODUCED. Its weakness is upstream (finding 1).
- The two hard rules hold in the app's code, not only in its test: the live reader only sends fixed mode-01 queries, and the only file the app writes is the review log of marked events. No path traversal was found in the app or the lab backend.

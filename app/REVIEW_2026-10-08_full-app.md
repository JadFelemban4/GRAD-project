# Astra review — whole app and agreed graphics scope

Date: 2026-10-08. Baseline: branch `JMF-2340550-results-tab`, HEAD `3b6953a`, including the current uncommitted implementation.

This is a review handoff, not a completion report. Sol's latest graphics work was interrupted before its acceptance pass. The findings below distinguish regressions in implemented code from unfinished milestones. No implementation files were edited during this review.

## Scope and boundaries

- Reviewed discovery, stable reads, source revisions, results selection and graphics, agent replay invalidation, and B1/B2/B3/C1 coverage against the training-linked-app plan and visual addendum.
- All subsequent edits must remain under `app/`. Keep scientific source data, producers, training, evaluation, and the existing outside-app changes untouched. Put the coverage report under `app/verification/`, even though the older plan proposed a path under `docs/`.
- Keep each experiment, agent set, protocol, and recorded generation independent. Missing scientific outputs remain explicitly unavailable; do not invent verdicts, traces, thresholds, or model results.
- Prior A1–A3 and selector repairs are already present. Preserve them and their tests.

## Confirmed implementation findings

### F01 — P1: existing evaluation charts become unreachable

Locations: `static/sim/results.mjs:784–786`, `static/sim/graphics-browser.mjs:25–37`, `results_graphics.py:20–24`.

The new graphics browser counts only new panels. Legacy experiments receive a G13 training panel but no new evaluation panel. Selecting training hides the old `#sections`; the evaluation button has count zero and is disabled, so the viewer cannot return to the existing evaluation results. This affects the legacy experiment path, including D2 and the C4 comparison.

Confirmed in the real browser at `/results#exp-d2`: selected experiment `exp-d2`, `#sections.hidden === true`, one existing legacy section, visible graphics `[G13]`, training active, evaluation disabled. Evidence: `verification/astra-full-review-d2-hidden.jpg`.

Fix: make group availability account for the existing evaluation sections, or migrate those sections into the group model. Do not hide accessible existing results behind a disabled group.

Acceptance: D, D2 and C4 retain their evaluation/comparison charts after direct navigation and switching groups/experiments. Exercise the actual renderer, including A → B → A and pending deep links, rather than only selector helper functions.

### F02 — P1: G22 reference ratios are plotted against counts

Locations: `results_comparisons.py:379–393`, `static/sim/results-graphics.mjs:209–225`.

G22 points are `(ratio midpoint, count)` and reference values correctly declare semantic `axis: x` for ratio. The generic bar renderer swaps the plotted axes to horizontal bars, but references are still rendered as vertical lines at `P.x(ref.value)`. Thus ratios are positioned on the count scale. The caption claims a shared ratio axis, which the rendered chart does not provide. The separate gear-reference channel also inherits parent reference markers that do not describe that channel's axes.

Fix: consistently transform points, axes, reference lines, intervals and cursors, or use a histogram-specific renderer. Give channels explicit reference ownership.

Acceptance: a small known histogram proves that a reference intersects the corresponding ratio bin, independent of count magnitude; switching to the gear-reference channel removes unrelated histogram references. Check both orientations if both remain supported. Source histogram counts are correct and sum to 89,510; this is a display error.

### F03 — P2: G08 pointer selection cannot distinguish seeds

Locations: `results_sets.py:307–350`, `static/sim/results-graphics.mjs:281–287`.

All pairs have x=0 for sighted and x=1 for blind. A transparent line-chart hit layer intercepts pointer events and selects using x-distance only. Every seed shares those x values, so ties resolve to the first seed, currently seed 0. Clicking a different pair cannot select it through this handler. Keyboard navigation can advance pairs, which hides the defect from keyboard-only tests.

Fix: use two-dimensional screen-distance selection or pair-specific hit targets for paired charts. Preserve same-seed links and the source-scoped selection store.

Acceptance: clicking/tapping a nonzero seed on either arm selects that exact seed, highlights both endpoints, and updates the linked values. Verify keyboard and table selection still agree.

### F04 — P2: G01 climb shading is silently discarded

Locations: `results_comparisons.py:163–170`, `static/sim/results-graphics.mjs:216–217`.

The adapter emits intervals with `start`/`end`; the renderer reads `from`/`to`. No rectangle is drawn. Backend assertions for a valid interval do not verify the frontend contract.

Fix: define one interval schema and use it consistently.

Acceptance: feed the actual adapter payload through the renderer and assert shading at the recorded grade-positive interval. Keep unavailable threshold/component caveats; do not add an invented thermal threshold.

### F05 — P2: evaluation arrival can retain an old replay generation

Locations: `agent_catalog.py:145–150,406`, `static/sim/agent-picker.mjs:88–94`, `static/sim/agents.mjs:603–608`.

Backend `replay_generation` includes scored evaluation source files. The catalog's pair `source_revision` includes only its training source revision. Frontend reconciliation checks that revision and the plant revision. Publishing or replacing valid evaluation provenance for an otherwise unchanged selected pair changes the backend generation without clearing the displayed frames. A later generation-bound request can reject that retained trace.

Fix: expose a pair replay identity covering the same dependencies as the replay cache, and invalidate only the affected selection. Keep summary arrival for unrelated pairs from interrupting playback.

Acceptance: with fixture models/provenance, obtain a generation, publish a matching evaluation without changing model/config/meta, refresh, and assert the selected trace is cleared with a source-change message. Repeat for a matching evaluation replacement and for an unrelated pair that must retain playback. No actual inference is needed for this regression test.

### F06 — P2: timestamp-preserving replacement bypasses discovery caches

Locations: `artifact_readiness.py:19–25`, `artifact_catalog.py:132–154`; compare `agent_catalog.py:83–85`.

Artifact cache signatures use only size and mtime. An atomic replacement with different bytes but the same size and preserved mtime reuses the old digest/model identity. A reviewer fixture reproduced this using a replacement ZIP; its file identity changed while the catalog revision and model identity stayed unchanged. The replay hash cache already includes inode, so the two paths can disagree.

Fix: use replacement-sensitive filesystem identity consistently, with an appropriate fallback on supported platforms. This finding concerns replacement with preserved timestamps, not every ordinary file write.

Acceptance: atomically replace a valid same-size model fixture, restore mtime, and require a new digest/revision after stability checks. Preserve the no-change polling guarantee: do not hash every large model on every poll.

### F07 — P2: G21 density omits samples without reporting coverage

Location: `results_comparisons.py:350–375`.

The published density grid spans KI 0–1.6 and retard −2–20 degrees. The adapter discards points outside these bounds. In the current source, 1,424 of 14,318 paired samples fall outside the grid (165 outside KI, 1,350 outside retard, 91 in both). Raw scatter retains the population, but the density channel neither reports the omitted count nor explains its coverage. Retard reaches 45 degrees.

Fix: keep the published bins and report included/excluded counts and ranges next to the density view, or clearly identified overflow bins. Do not silently redefine the scientific binning or present a new validation conclusion.

Acceptance: known boundary/outlier fixtures plus the real source verify conservation of included + excluded samples and a visible localized caveat.

### F08 — P2: populated tables show an empty-chart message; scientific caveats remain untranslated

Locations: `static/sim/results-graphics.mjs:130–148`, `static/sim/graphics-strings.mjs` and table rendering.

In the real Arabic G25 view, the table contains 11 rows but the panel says “لا توجد قيم مسجلة في هذه القناة.” and displays previous/next sample controls. Column headers and consequential row caveats fall back to English or raw identifiers such as `ROW4_SOURCE_UNSPECIFIED_KNOCK_MODEL_NOT_VALIDATED` and `TAU_RECOMPUTES_C_OVER_UA_NOT_AN_INDEPENDENT_MEASUREMENT_CAPACITY_ASSUMED`. G19 channel labels also remain English on the phone view.

Fix: make table-only panels a supported state with relevant controls and counts. Translate user-facing labels and scientific limitations into readable Arabic/English while preserving numbers, source identifiers and evidence meaning. Distinguish “unavailable”, “withheld”, “empty channel” and “populated table”.

Acceptance: Arabic/English G25 shows its data and readable limitations without a contradictory empty message; controls remain usable at 390×844. Cover chart, table-only, partially available and withheld states.

## Unfinished agreed deliverables

### U01 — B2: complete the saved-decision reader and synchronized viewer

Plan: B2, lines 242–271. Current implementation: `results_records.py:1–79` and the generic G11 panel.

The current reader accepts only an `episode_trace.json` extract. There is no bounded NPZ reader, `/api/records/{record_id}/meta` or frame-window endpoint, saved train/evaluation record selection, or the planned decision viewer. Presence checks for provenance strings and policy membership are not validation of the claimed recorded generation. Historical records should remain inspectable as historical records; that does not justify presenting arbitrary provenance strings as verified compatibility.

Required implementation:

- Registry-bound records and validated schema/provenance; numeric NPZ loading with `allow_pickle=False`, bounded archive members/decompression and frame windows of at most 500.
- The five command/applied actuator lanes, observation/preview, recorded reward components, torque/thermal and event information where recorded. Missing channels remain explicit.
- A single correctly aligned selected sample shared by timelines, exact values and the model view. Keep time/pair axes separate and reset selection on source revision changes.
- Small numeric fixtures cover absent records, object arrays, malformed archives, shape/unit/provenance errors, non-finite values, bounds and source replacement. Real records being absent does not prevent implementing and testing the reader.

Do not start training, evaluation or inference to manufacture a trace. Retain the missing-real-record limitation separately from implementation status.

### U02 — B3: the mechanical view milestone is still pending

Plan: B3, lines 273–285. The current changes do not implement the agreed mechanical model update and saved-sample link. Existing agent discovery/replay work does not itself complete B3.

Complete the specified readable engine/turbo/airflow/cooling presentation and camera controls, synchronized selected sample, mobile single-lane switching, reduced motion and useful non-WebGL fallback. Preserve scientific geometry and avoid presenting decorative animation as measured physics. Verify that language/theme/camera changes preserve the numeric sample.

### U03 — finish acceptance and report coverage honestly

Maintain one G01–G25 coverage row under `app/verification/` with actual source, reader, renderer, runtime availability, interactions and evidence. Verify Arabic/English × dark/light × desktop/mobile (1440×900 and 390×844) after the fixes. Include pointer/touch/keyboard/table access and real navigation between experiments/groups; older selector screenshots do not verify the new graphics.

Retain the separately unavailable published post-hoc verdict/analysis deliverable when applicable. Neither a card for every G-number nor a successful unit suite establishes full R1b/B2/B3/C1 completion. Keep `app/.superpowers/training-linked-app/graphics-progress.md` aligned with actual status.

## Verification performed in this review

- Node suite: **281 passed**, zero failures.
- Python command below: **212 run, OK, 2 skipped** (210 non-skipped successful tests).
- Browser: reproduced inaccessible D2 evaluation results; inspected G25 populated-table/empty-state contradiction and untranslated caveats; checked a 390×844 graphics view without horizontal overflow. This was targeted review, not the completed eight-case acceptance matrix.
- Data checks included historical trace alignment/endpoints, set summaries and matched seeds, and histogram totals. Several reader values are correct; the renderer contract findings above remain independently actionable.
- Actual Torch/SB3 inference was not exercised: those dependencies are absent from the selected environment. No training/evaluation jobs or external AI calls were run. The procedural replay suite was not rerun in this review; do not reuse an older result as fresh evidence.

Python suite:

```text
.venv\Scripts\python.exe -B -m unittest app.test_results_comparisons app.test_results_sets app.test_results_records app.test_results_graphics app.test_graphics_revisions app.test_results app.test_artifacts app.test_artifact_api app.test_agent_generations app.test_agent_sources app.test_launcher app.test_simulation
```

## Suggested execution order for Sol

1. Restore evaluation access (F01) and correct scientific rendering (F02/F04/F07).
2. Fix paired pointer selection and panel states/localization (F03/F08).
3. Close source-generation invalidation and replacement detection (F05/F06).
4. Finish B2 and B3 within the app-only boundary; preserve truthful missing-source states.
5. Run relevant regression checks and the complete browser matrix, update the G01–G25 coverage ledger, and report the remaining unavailable scientific deliverables explicitly.

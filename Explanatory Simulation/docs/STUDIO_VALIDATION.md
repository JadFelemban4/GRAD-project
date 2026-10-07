# Interactive dark studio — 2026-10-04

Default Arabic mode is now the mechanical studio. The guided tour, source tracing, sandbox, viva and research results remain accessible. New presentation code is confined to `ex`; the original research checkout has no tracked changes.

## Visual mechanism and controls

The source Supra remains the project's procedural model. The standalone six-cylinder assembly is a teaching model, not OEM CAD. Beveled castings retain exact requested visual bounds. Section mode opens the block, sleeves, head and sump so the crank, articulated rods and ringed pistons remain visible. Cams rotate at half crank speed. Spark/fuel cues are explicitly illustrative; no cylinder pressure measurement or validated firing sequence is claimed.

Picking a mesh selects its actual source concept; piston mesh and shortcut both select `four_stroke`. Crank picking selects `engine_torque` and displays actual returned torque. Missing thermal states render neutral metal and “غير متاح”. Explode separates the castings/head/sump while preserving piston-to-rod-to-crank joints; restore returns separation to zero. Attached head/plug/valve parts use one shared offset.

Presentation controls provide solid, ghost and section displays; part isolation and focus; four camera presets, zoom/reset, automatic orbit; expanded view with Escape and focus containment; play/pause, visual speed and manual 0–720° cycle inspection. Automatic motion honors reduced-motion preferences. These controls do not alter the simulation timestep or physics outputs.

## Actual API and browser verification

Tests used the built frontend and the local Python server via real browser controls, without injected application state.

- Desktop 1440×1080 and mobile 390×844 render without page-level horizontal overflow. Phone canvas is 500 px high; the part card, operating inputs and presentation controls flow below it.
- Default plant point 2500 rpm / 100 kPa / 15° BTDC / lambda 1 returns 221.0 Nm, 840.8°C EGT, 4.2 g/s fuel and 61.2 g/s air. Changing only RPM to 3000 yields 219.6 Nm, 875.7°C, 5.1 g/s and 74.8 g/s.
- Changing all four numeric inputs to 3000 / 150 / 20 / 0.95 yields 369.7 Nm, 872.3°C, 8.2 g/s fuel and 114.9 g/s air. Frame HUD and returned outputs agree. Debounced requests reject stale responses. Last valid outputs stay labeled during recalculation, keeping the layout steady.
- Part shortcuts and canvas picking, isolate/restore, full explode/restore, all camera presets, solid/ghost/section, zoom, auto-orbit toggle, expanded mode/Escape, pause/resume, visual speed and keyboard cycle scrub were exercised. Explode resets the cycle slider and its readout together to 0°.
- Tour still exposes the Python simulation step controls, viva still reveals its explanation, and source dialog opens the actual numbered `plant.py:37` Geometry definition. Research remains inconclusive: +1.17 pp with CI −4.44..+6.78 and ten pairs; the hand-policy preview margin remains −0.32 pp.
- Console returned zero errors and warnings in final interactions. Production build passes; Vite retains its advisory about the lazy Three.js chunk size. Launcher reports “Local app healthy”.

## Automated checks

25 backend tests and 18 Node tests pass (43 total). Node coverage includes exact casting envelopes/open section faces, Supra bounds, under-bonnet path containment, full-cycle rod attachment/sleeve fit, frozen pause, RPM-derived pedagogical motion, 720° manual wrapping and capped resumed-tab delta. New checks cover immutable operating references, unavailable/zero/signed readings, conserved exhaust mass, bounded flow visualization, path envelopes, reversible housing separation and retained turbo phase across paused input changes.

Screenshots: `qa/studio-engine.png` (expanded inspection), `qa/studio-desktop.png`, `qa/studio-mobile.png`. This verifies the interactive explainer, not the physical validity of the research model.

## Reference-driven turbo and comparison revision

See `REFERENCE_REVIEW_2026-10-04.md` for all 17 unique posts, review evidence and inclusion decisions. The two-wheel, single-shaft turbo is now a standalone studio assembly; the normal vehicle/learning layers keep their source Supra context. Section/ghost/solid, direct part picking, focus/isolate, housing separation and restore use the same presentation controls as the engine. Solid covers sit ahead of the impeller blades; section mode opens them for inspection. Compressor housing picks MAP; turbine housing picks its independent `t_turb` concept.

The five-step Arabic flow guide opens the source concepts for inlet, compressor, shaft, turbine and exhaust outlet. An overview restores both separate gas paths. The shaft step shows energy coupling with no gas flow through the shaft. Actual exhaust g/s is air plus fuel, including the source Inspector reading. Missing values are unavailable. Surface temperature uses only a supplied `t_turb`; direct plant operating points provide no turbine thermal node.

Both wheels share one accumulated illustrative angle. Pause freezes that angle even when MAP changes and the returned flows update; it resumes from the retained phase. Neither motion rate nor particle paths claim measured turbo RPM or CFD. The illustrative flow mapping caps at 250 g/s rather than saturating below the default plant point.

At 2500 rpm / 15° / lambda 1, freezing MAP=100 and changing only MAP to 150 produces:

| Output | Reference | Current | Difference |
|---|---:|---:|---:|
| Torque (Nm) | 221.0 | 359.9 | +138.9 |
| EGT (°C) | 840.8 | 902.0 | +61.1 |
| Fuel (g/s) | 4.2 | 6.4 | +2.2 |
| Air (g/s) | 61.2 | 94.0 | +32.8 |

Differences are calculated before rounding, so rounded displayed operands may not subtract to the last shown decimal. Returning to the reference restores all four inputs and yields four zero deltas after recalculation. Clear removes the comparison. Results remain associated with their successful input point during pending/error responses; no Celsius percentage or implicit better/worse judgment is used.

Real-browser verification exercised all five flow selections, overview, compressor-housing mesh picking and correct MAP Inspector, isolate/restore, full explode/restore, solid/section, pause and comparison freeze/change/restore/clear. Desktop 1440×1080 and phone 390×844 fit without page-level horizontal overflow (phone scroll width 375 px). Phone comparison grid is 303 px wide; its four numeric columns and all five guide buttons remain readable and reachable. The mobile camera uses the available canvas area without reserving space for controls that already flow below it.

The frontend releases its own active road-session IDs on unload using keepalive DELETE requests, preventing the repeated-reload leak seen during QA. The local development server was restarted to clear prior transient QA sessions. This does not modify research files or results. Known Arabic error translations survive a second formatting pass.

New proof images: `qa/studio-turbo.png`, `qa/studio-comparison.png`, `qa/studio-turbo-mobile.png`, `qa/studio-comparison-mobile.png`. Build and launcher pass; the Three.js chunk-size advisory remains. Backend tests emit the existing Starlette/httpx deprecation warning, with no failures.

## Integrated vehicle and road-story follow-up

The studio now starts with the source car and the same enlarged turbo assembly mounted in its engine bay. Front-entry and rear-exit gas guides, clickable part labels and a full text path legend make both routes visible in the vehicle. A prominent mission strip leads to the turbo or an actual road preview → current load/heat → applied ECU-command story, including a locked-road example and preview visibility intervention. See `VEHICLE_PROJECT_VALIDATION.md` for the 51-test total, current browser evidence and the distinction between source preview data, illustrative geometry, current temperatures and SAC reenactments.

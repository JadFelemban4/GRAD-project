# Validation and browser evidence

Verification date: 2026-10-04. This document tests the **explainer's fidelity and usability**, not physical validation of the core research model. Core validation caveats remain visible in the UI and LIMITATIONS.md.

## Backend and source checks

See VALIDATION_BACKEND.md for fresh full-suite output and complete episode verification. Tests cover direct source-step parity, reset nulls, finite computed values, all 23 observation slots, physical bounds and slew, preview-only blinding, deterministic actor export inference, frozen-road settings, timing across the climb edge, session validation, plant/thermal calls, source allowlist/traversal safety, result identity and static hosting.

Core Git status was checked against initial state: only the pre-existing untracked `PROMPT_AUDIT_2026-09-30.md` and `PROMPT_AUDIT_2026-09-30/` remain. No tracked core file changes or training were introduced.

## Actual browser interactions

Used the in-app browser with real UI actions against the live Python API, not DOM-injected state.

- Guided tour renders nine progressive lessons. 3D cutaway loads, including car, six pistons, air/exhaust/cooling/oil paths and road.
- Initial Step 1s advances time 0→1 s. Flat-road torque demand 66.2 Nm and delivered 66.8 Nm.
- Enabled road override at 130 km/h, moved grade to 12%, advanced 30 s. Time 31 s, RPM 2706, requested torque 335.4 Nm, delivered torque 336.2 Nm.
- Manual spark trim can move to its source lower bound; one step updates actual physics. Other controllers disable manual levers.
- Engine lab computes 221.0 Nm, 840.8°C EGT, 61.2 g/s air, 4.2 g/s fuel and 57.9 kW at its default point. Changing RPM and clicking Intake/Compression/Power/Exhaust updates the scene; automatic recalculation follows slider changes.
- Thermal lab heats 30 s then cools 90 s. Final turbine 623.8 K / 350.6°C, oil 349.0 K / 75.9°C, block 351.3 K / 78.2°C. Housing remains hot after removing exhaust heat input. Timeline and selectable signals respond.
- Trace search `t_turb` finds housing temperature; Show me in the project opens actual `thermal.py:226` with `q_in_turb = ua_gt * (egt_k - self.t_turb)` and neighboring state equations.
- Viva initially hides the answer. Reveal shows a 30-second answer; Next question hides it again. Fourteen questions are available.
- Research result reads current files: mean +1.17 pp, CI −4.44 to +6.78, ten pairs; current hand preview margin −0.32 pp; diagnostic median spark-cap figures 41.6/41.7%. Retired figures are excluded from the headline.
- Loaded paired seed-0 actors and advanced six batches to 180 s. At input sample 179 s both have current grade 0%; sighted future slots all 12%, blinded all 0%. Values differ in actual model outputs: turbine 438.7 vs 436.8°C; fuel 2.5 vs 2.0 g/s. No claim that this is the original scored trace.
- Scrubbing paired timeline to Home returns selected time to 0; End returns to the latest synchronized frame.
- Loaded real recording `3f64372e-20260907_070041`. Original timestamp 0, measured RPM/speed 0; missing thermal and torque values remain Unavailable. Missing coolant/oil badges are UNAVAILABLE.

## Final production checks

- `npm run build`: TypeScript and Vite production build passed. Main script 275.67 kB (87.08 kB gzip); lazy Three.js scene 936.15 kB (254.35 kB gzip). The scene chunk triggers Vite's advisory size warning; it is lazy-loaded and rendered successfully in the actual browser.
- `launch.py --check`: Local app healthy. Both built UI and metadata served on 127.0.0.1:8765. No Vite dependency is needed to use the built app.
- Fresh production tab: initial missing combustion/air/gas results display Unavailable. Canvas loads. Play advances 0→1 s; Pause stops the loop. Engine cycle has an independent pause control.
- Repeated production Engine/thermal/trace/viva/result interactions passed. Engine slider at 6000 rpm returned 158.9 Nm, 1007.8°C EGT and 99.9 kW, with direct-point calibration warning. Engine-lab turbine/oil/block are unavailable and have muted geometry, rather than invented thermal values.
- Thermal timeline at heating endpoint: actual plant EGT 940.6°C and housing approximately 449°C. At cooling endpoint: gas temperature Unavailable; housing approximately 351°C. Inspector and scene follow the selected lab frame.
- Source excerpt still opens correctly after switching between labs and modes. Result still reports the current paired CI. All test-supported sources resolve, including 57 concepts, 23 observations and five action mappings.
- Browser console captured **zero errors and zero warnings** throughout these final production interactions. Development hot reload had exposed Drei HTML portal unmount errors; replacing road labels with disposable Three.js sprites removed the failure in production.
- Portrait test at 390×844: viewport content width 375 px after scrollbar, page scrollWidth 375 px; canvas 345×340 px. No page-level horizontal overflow. Navigation/lessons use deliberate internal scrolling; inspector stacks below the main content. Portrait camera pulls back to fit the cutaway. Temporary viewport override was reset.
- Final screenshot saved in `qa/desktop.png`; browser tab left open as the user-facing deliverable.

## Review disposition

Independent code review and backend review both flagged engine-lab missing thermal values; corrected them by retaining ECT as a named input and leaving ThermalNetwork nodes absent/muted. Corrected 3D lookahead to `input_time_s`, and missing recorded-channel badges to UNAVAILABLE. No unresolved important explainer defects were found. Underlying physical/scoring uncertainty is documented in LIMITATIONS.md and preserved on screen.

# Replay lab implementation plan

> **For agentic workers:** Use subagent-driven-development for the isolated scene task; root implements integration and conducts verification. Steps use checkbox syntax.

**Goal:** Run an honest interactive 3D replay of the existing Supra recordings.

**Architecture:** A read-only Python replay adapter generates immutable timestamped frames with provenance. One browser playback clock selects all telemetry; independent Three.js renderers consume selected frames and interpolated presentation distance.

**Tech Stack:** Existing FastAPI, Python 3.11+, ES modules, pinned Three.js, Node built-in test runner.

**Spec:** `docs/superpowers/specs/2026-09-21-replay-lab-design.md`

## Global constraints

- No ECU writes, no raw/cache persistence, no changes to physics or measurements.
- Eight ratios from Vehicle; missing fields null; recorded gear must pass channel validation.
- Original sample timing for Estimator; playback speed never changes integration.
- Road is illustrative; no Phase D result or comparison claim.
- User has approved implementation; execute in this existing clean feature checkout. Do not push or commit unrelated work.

## Task 1: Python replay data and HTTP contract

Files: `app/replay.py`, `app/test_simulation.py`, `app/estimator.py`, `app/server.py`.

Produces `GET /api/replay/trips` -> `{trips, vehicle, preview_s, limits}`. Each trip has `id,name,rows,duration_s,has_speed,has_gear`. `GET /api/replay/trips/{id}` starts or polls a single bounded memory build; response `{status,progress,...}`. Ready response includes `frames,events,meta`. Frames carry `t,s_m,speed_kmh,rpm,gear,gear_source,gear_raw,gear_note,grade_pct,coolant_c,oil_c,oil_source,turbine_c,turbine_lo_c,turbine_hi_c,block_c,fuel_gps,torque_nm,map_kpa,ambient_c,modelled,ok,gap`. No numeric field uses NaN/Infinity in JSON.

- [ ] Write unittest fixtures with recorded speed/RPM at 8th but raw gear 6, genuine lower recorded gear, low-speed/slip uncertainty, unavailable speed, and input traversal rejection. Check fuel field exposes the same predict result used by Estimator.
- [ ] Run `python -m unittest app.test_simulation` and observe missing-feature failures.
- [ ] Implement `infer_gear`, `build_replay`, catalog and bounded worker. Use `ReplayReader(speed=0)` and `Estimator.update` once per sample. `State.fuel_gps = out['mdot_fuel_gps']` only exposes existing computation.
- [ ] Run tests and original replay regression suite. Verify ready frames against a separate direct Estimator pass at matching timestamps; no interpolation of physics outputs.

## Task 2: Three.js scene (isolated worker)

Files: `app/static/sim/scene.mjs`, optional `app/static/sim/geometry.mjs` and `scene.test.mjs`. Own no other files.

Produces `createScene(host)` -> `{update(frame, presentation),setFollow(on),resetCamera(),zoom(factor),dispose()}` and `createEngineScene(host)` -> `{update(frame),dispose()}`. Presentation = `{distance_m,preview_m,playing}`. Missing distance freezes motion; frame may be null before ready. Parent calls updates each animation frame. Use imports `three` and `three/addons/controls/OrbitControls.js`. Draw a genuine low-poly Supra silhouette, terrain/road loop with level, rise, descent, sparse trees and roadside objects. Terrain is always illustrative, looping distance at scale must be documented. Single travel-distance coordinate drives wheel rotation and road position. Highlight the upcoming available distance; do not feed road elevation into physics. Engine schematic only colors measured/estimated nodes it receives; absent values gray. No UI text drawn as invented telemetry.

- [ ] Verify geometric distance/continuity behavior with Node tests where useful; visual-only styling requires browser inspection, not tautological tests.
- [ ] Build renderer with orthographic camera and OrbitControls; cap pixel ratio and shadow maps; ResizeObserver, disposal and reduced-motion support.
- [ ] Root integrates the exported interface and reviews screenshot + interactions.

## Task 3: Playback and Arabic UI

Files: `app/static/simulation.html`, `app/static/sim/playback.mjs`, `playback.test.mjs`, `main.mjs`, `style.css`, `app/package.json`, `app/vendor.mjs`.

Consumes the HTTP/frame contract and scene interface. Exports `PlaybackClock` with `play,pause,seek,setRate,reset,tick` and `sampleAt(frames,t)` selecting the last recorded sample at or before t, never blending discrete gear/RPM. Distance-only interpolation uses adjacent valid samples. `previewAt(frames,t,H)` returns distance plus covered seconds and completeness, breaking at gaps. Single selected sample drives counters, thermal inset, chart cursor and gear strip. All eight gears remain visible; shift events only from accepted observations with sample-interval caveat.

- [ ] Write tests: paused clock holds after 20 wall seconds, 4x advances 8 seconds over 2 wall seconds, seeking backward restores earlier gear/temperature, 1x and 8x reach identical state at same trip time, unknown gaps prevent distance/preview guesses.
- [ ] Run `node --test app/static/sim/playback.test.mjs` red, implement clock and lookup, rerun green.
- [ ] Add polished responsive Arabic layout, charts and controls with accessible names, loading/error/empty states and explicit source legends. Serve pinned Three.js locally via a vendor-copy script; no remote CDN at runtime.
- [ ] Connect selecting trips, loading progress and cancellation of stale UI requests. No automatic playback before data ready.

## Task 4: Integration verification and delivery

Files: `app/README.md`, `app/requirements-replay.txt`, `app/start-simulation.ps1`, `docs/superpowers/plans/2026-09-21-replay-lab-progress.md`.

- [ ] Run new Python suite, all Node tests, full app replay regression and verify_docs.py. Record exact outputs; do not update scientific baselines to hide a failure.
- [ ] Use real browser to select a drive, play, pause, seek, change rate, restart, inspect eight gears, inspect thermal nodes and errors. Check desktop and narrow viewport and 3D resource behavior.
- [ ] Inspect git diff to verify physics/data untouched. Write run/setup instructions and remaining limits. Keep server running locally for user inspection.

## Interface review

| Tasks | Shared interface | Resolution |
|---|---|---|
| 1 and 3 | frames, events, progress API | Single contract above; raw and estimated sources stay separate |
| 2 and 3 | scene factories + update payload | Only root owns UI; scene module consumes null-safe primitives |
| 1 and 4 | State.fuel_gps | Expose existing output only; original full regressions required |
| Each task | Tests versus requirements | Numerical and playback behavior tested; aesthetics inspected in browser |

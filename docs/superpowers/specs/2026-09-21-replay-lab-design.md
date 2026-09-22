# GRAD replay lab — approved design

Approved in conversation on 21 September 2026. Baseline: 9c4b5fa, branch JMF-2340550-sep17.

Add `/simulation` to the existing FastAPI application. Keep physics in Python; use Three.js only for rendering. The first release replays existing CSV drives using ReplayReader and Estimator at original timestamps. No ECU command path, no manual transmission control, no replay ambient/grade controls, no Phase D comparisons.

The Arabic interface has a large low-poly isometric Supra scene with zoom/orbit/follow, a schematic B58/turbo/cooling inset, telemetry, an eight-gear strip, charts, a shift-event timeline, a trip selector and play/pause/restart/seek/rate controls. Road topology is explicitly illustrative, not geographic or a claim about recorded grade. Geometry cannot feed the model. All channels carry recorded/estimated/unavailable provenance, and unknown data remain null.

Use Vehicle.gears, final_drive, wheel_r and shift metadata from live objects. Prefer valid recorded gear; Actual gear in shipped logs saturates at 6 and is not accepted blindly. Infer gear from RPM/road speed when ratio agreement supports it, label it estimated, retain the raw reading, and suppress ambiguous/low-speed/slip cases. Shifts remain discrete; timestamps bracket sampled changes, not exact mechanical shift times. Never synthesize all eight gears.

Reuse plant fuel output (g/s) by adding a State field; do not recompute combustion in JavaScript. Show measured coolant/oil where present, thermal estimates with seed bounds otherwise. The thermal network has block/oil/turbine nodes, not separate radiator/compressor metal temperatures. Keep schematic proxies explicit.

PREVIEW_S comes from engine_env; default H is its maximum. Replay preview distance is the timestamp-aligned integral of available road speed over H, clipped at the end with coverage displayed. This visual horizon does not mean a preview controller is active.

Precompute frames in memory without wall-clock sleeps and serve build progress. Persist no raw telemetry or computed trip cache. Playback never calls the integrator. A bounded cache and a single build worker prevent unbounded work. Missing speed freezes car motion and marks distance unavailable; logger gaps break interpolation and inferred shift continuity.

A metadata fingerprint includes code hashes, source hash, vehicle constants, preview times and estimator integration policy. Future comparison is hidden until compatible outputs exist. Current scope does not train or re-evaluate old agents.

Verify Python data and API contracts, JS clock/seek/sample/preview behavior, original app regression suite (full), browser controls and responsive visual layout. Deliver reproducible setup/run instructions and known limitations. No change to plant.py, thermal.py, engine_env.py or raw/data files.

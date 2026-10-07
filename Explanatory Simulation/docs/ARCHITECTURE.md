# Explainer architecture

## Choice

React + TypeScript + Vite, a meaningful Three.js scene, and a loopback-only Python bridge. Alternatives rejected: a JavaScript physics reimplementation would drift; static recordings alone would prevent freely changing variables. Existing models are imported read-only. The learning environment lives in `GRAD-project/Explanatory Simulation`; its parent supplies the scientific modules and results.

## Contracts

- `GET /api/meta`: source-derived action bounds/slew, preview horizons, ordered observation metadata, vehicle metadata, concepts, guided lessons and viva questions.
- `GET /api/results`: current terrain_dt1 index and premise, provenance/fingerprint and caveats, never automatic fallback to retired files.
- `GET /api/source?file=…&line=…`: allowlisted project file excerpt with actual numbered lines. No arbitrary path or code execution.
- `POST /api/session`: `{scenario, preview, policy, seed}` creates an isolated in-memory environment. Returns `{id, frame, road}`.
- `POST /api/session/{id}/step`: `{steps, controls?}` steps real project code; returns `{frames, done}`. Simulation mutation is only in memory, not vehicle or project mutation.
- `POST /api/plant`: constrained operating point, calls `plant.predict`; engine lab explicitly separates RPM/MAP from vehicle-coupled demand.
- `POST /api/thermal`: operating point plus heating/cooling duration, real ThermalNetwork with <=0.1 s substeps, clearly a teaching experiment not a scored evaluation.
- `GET /api/logs`, `POST /api/replay`: available raw logs through existing replay code; unavailable channels remain null.

Frame contract: `time_s, input_time_s, dt, rpm, map_kpa, speed_kmh, grade_pct, gear, torque_req, torque, egt_c, t_turb, t_oil, t_block` (thermal K), `spark, lam, mdot_fuel, mdot_air, ki, damage_rate, reward, r_resp, r_fuel, r_life, cost_torque, cost_knock, cost_egt, action[5], requested[5], command[5], obs[23], obs_in[23], preview_pct[4], baseline{…}, totals{…}`. Frames correspond to the step just executed. `input_time_s` is the observation/road sample at interval start; `time_s` is interval-end thermal state. `obs_in` is what the actor read; returned `obs` is the next observation. Road arrays: `time_s, grade_pct, speed_kmh`. Missing reset calculations and unavailable recorded channels are null. Thermal cooling has no calculated gas temperature, so `egt_c` is null while `exhaust_boundary_c` identifies ambient boundary conditions.

## UI

One persistent interactive stage with four learning modes. Guided tour starts with few controls and reveals engine, turbo, thermal and agent layers. Sandbox offers vehicle-coupled simulation and isolated engine/thermal labs. Trace mode supplies a searchable concept dictionary and upstream/downstream graph. Viva hides answers until requested. Preview comparison steps two isolated environments on the same road and pins weights/seed; trained-agent inference uses exported actors only after identity checks, and remains labelled an educational rerun.

Plots use actual returned frames and synchronized scrubbing. 3D flows, piston motion and heat colors are explanatory exaggerations, not additional physics. A keyboard-accessible component selector duplicates scene picking. Loading/errors and disconnected state are visible; no synthetic numeric fallback.

## Isolation, performance and verification

Bind API to 127.0.0.1. Vite proxies `/api`. Batch small step requests to reduce overhead; cap sessions, step counts and allowed input ranges. Pause prevents additional stepping; slow playback affects wall time only. Avoid dt changes in scored roads. Verify bridge parity against direct env steps, bounds/order/blinding, finite outputs, source allowlist, current result identity, build, desktop/mobile interactions and WebGL scene. No training, OBD, result rewriting or remote deployment.

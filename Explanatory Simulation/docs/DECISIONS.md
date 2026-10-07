# Decisions and continuation notes

- Investigated local executable code, derived data, validation/audit documents and current artifacts before scaffolding. Local work is authoritative; no checkout/reset or core changes.
- Used Sol integration and three focused Luna workers, the available four-agent concurrency limit. Separate ownership prevented shared-file conflicts. No unresolved scientific contradiction required Astra.
- Initially kept all implementation under `ex`, with imports from sibling `GRAD-project`. On 7 October 2026, moved the renamed `Explanatory Simulation` folder inside `GRAD-project`; imports now reference the parent tree. Bytecode writes remain disabled before core imports. No training, OBD link or result rewriting.
- React/TypeScript/Vite + R3F conceptual scene, local Python FastAPI bridge. Avoided a JavaScript physics copy. Canvas animation explains sampled state and deliberately exaggerates/slows flows.
- Ordered observations, action vectors, gears and thresholds come from source. Excerpts are allowlisted and dynamically numbered. Missing calculations display Unavailable rather than fabricated zero.
- Use current `terrain_dt1/index.json`, `premise.json` and `KNOCK_MARGIN.md` only for headlines. No automatic retired-result fallback. Code-derived status and identity guard interpretation.
- Exported NumPy actor inference mirrors deterministic SAC layers but cannot prove scored-trace identity. Label every actor reenactment unverified.
- Match frozen evaluation Episode 1 (720 samples, dt=1, 719 transitions) for the locked teaching road. Retain the source's dt=1 thermal behavior rather than repairing core physics silently.
- Thermal memory lab calls actual ThermalNetwork at 0.1 s; clearly distinct cold-start teaching experiment. Oil cooling phase retains the source's rpm=800 heat term.
- Manual spark/lambda/MAP are trims; fan/pump absolute duties. Baseline neutral supervisor differs from ECU fan schedule, disclosed explicitly. Road speed override replaces remaining speed samples, not an artificial acceleration impulse.
- Two timestamps matter: `input_time_s` is the interval-start observation/control sample; `time_s` is interval-end state. Preview aligns to input time, thermal plotting to end time.
- Built static UI is served with API on loopback port 8765; Vite development runs 5173. Self-hosted fonts avoid a network dependency during the viva.
- Preserve all existing core untracked audit files. Final verification should compare core git status to the initial status, not delete unrelated files.

Future improvements: corrected upstream thermal scoring integration and retraining are research tasks requiring separate authorization. An exact saved scored trace/code fingerprint would allow stronger replay provenance. Large scene bundle is lazy-loaded; source dialog and learning UI remain usable without WebGL.

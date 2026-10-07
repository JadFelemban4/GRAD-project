# Interactive learning environment implementation plan

**Goal:** teach the real graduation project by manipulating its actual simulation.

**Architecture:** see ARCHITECTURE.md; scientific scope: PROJECT_MAP.md. All learning implementation stays under `Explanatory Simulation` (formerly `ex`), now inside `GRAD-project`. Core modules and local changes are preserved.

## Task 1: verified sources and vertical simulation slice

- [x] Investigate physics, environment and results independently with Luna workers.
- [x] Read local source, derived data, audits and existing app before scaffolding.
- [x] Write project map and architecture.
- [x] Build metadata/source registry and result reader from current files.
- [x] Add isolated session API, real plant/thermal endpoints and read-only replay.
- [x] Test direct-step parity, finite values, action bounds, observation order and blinding.

## Task 2: complete visual stage

- [x] React/TypeScript app and responsive engineering workbench.
- [x] Three.js conceptual car, six cylinders, intake/turbo/exhaust/cooling/oil/gearbox/road.
- [x] Grade → demand → exhaust → heating → supervisor vertical slice.
- [x] Browser-check slice before expanding modes.

## Task 3: teaching and experiments

- [x] Guided progressive lessons and Engine/Turbo 101 animations.
- [x] Sandbox vehicle controls, operating-point lab and heat/cool memory experiment.
- [x] Agent observations/actions/reward explorer and preview/blind comparison.
- [x] Trace-to-code variable search, causal highlighting and source excerpts.
- [x] Viva questions, hidden answers and technical detail.
- [x] Dynamic current result charts, CI, hand-vs-trained distinctions and caveats.

## Task 4: integration and QA

- [x] Launch scripts and required continuation documentation.
- [x] Build, API startup, real browser interactions and mobile layout.
- [x] Review scientific fidelity, evidence labels, limitations and all source links.
- [x] Record validation evidence and any genuinely unresolved gaps.

Ownership: orchestrator owns UI shell/integration/docs; physics worker owns Scene.tsx only; controls worker owns backend simulation/server/tests; results worker owns backend catalog/content/current-result tests. No concurrent edits of shared files. Workers consume the contracts in ARCHITECTURE.md.


Verification: 23 tests pass; complete 719-step locked episode finite; production build/launcher and real browser desktop/mobile interactions verified. See VALIDATION.md and VALIDATION_BACKEND.md. Physical research limits remain explicit in LIMITATIONS.md. No core changes or training.

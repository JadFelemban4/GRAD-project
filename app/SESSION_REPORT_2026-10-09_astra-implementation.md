# Astra implementation and acceptance — 9 October 2026

Implemented the review in `REVIEW_2026-10-08_full-app.md` inside `app/`. Independent source, record-reader and UI reviews found no remaining in-scope blocker after fixes and scoped re-review. The reviewer retracted a suspected playback-boundary defect after reproducing that the controller correctly awaits the next window.

| Review item | Result |
| --- | --- |
| F01 | Legacy D/D2/C4 evaluation groups remain reachable alongside training. Real D2 training → evaluation verified. |
| F02 | Horizontal G22 references use the ratio coordinate. Channels own their references; known count/ratio fixture verifies it. |
| F03 | G08 pointer distance uses both coordinates. Real pointer selected seed 4; table seed 3 and keyboard seed 1. G12 follows when mounted. |
| F04 | G01 consumes start/end climb intervals; rendering regression verifies recorded coordinates. |
| F05 | Selected replay identity covers evaluation provenance changes, with unrelated arrivals preserved. |
| F06 | Replacement-sensitive file signatures invalidate cached source identities while unchanged polls reuse hashes. |
| F07 | Density reports included/excluded ranges and counts. All raw paired samples are accessible through a separate scatter channel. |
| F08 | Table-only G25 opens its 11 rows immediately, without an empty-chart message or sample controls. Scientific limitations and labels are readable in both languages. |
| U01 / B2 | Registry-bound numeric NPZ metadata/frame APIs, bounded decompression/header checks, pickle disabled, one decoded cache, 200-sample viewer windows, sample-linked plots/values and physical versus normalized action units. |
| U02 / B3 | Inline-six cutaway adapted from Explanatory Simulation, distinct intake/exhaust/cooling paths and shaft/turbo parts, camera framing/highlighting, recorded temperature overlays, reduced motion, fallback, mobile switching and compact action values. |
| U03 | G01–G25 inventory and eight exact-size language/theme cases recorded in `verification/`. |

The saved viewer handles one policy/episode at a time: no pair alignment or current-plant compatibility is inferred. Commands/observations are before-step values; applied actions/rewards/outcomes are after-step values. Missing channels stay null/unavailable. Initial NPZ decompression is bounded and cached, not free random disk access. Revision identity covers NPZ and relevant sidecars. Review also fixed simulation startup's string-to-Path conversion and added an actual main-route-registration test with uvicorn mocked; compressed members are drained to EOF for length and CRC checks before NumPy loading.

Verification:

- JavaScript: 300 tests, 0 failures, 0 skips (`node --test app/static/sim/*.test.mjs`).
- Relevant Python: 234 tests, OK with 2 skips, covering result readers/API, source identity, records, launcher and simulation. Record-reader targeted round: 18 tests pass.
- Browser: Arabic/English × dark/light × 1440×900/390×844, no document overflow. G25 retains 11 rows; saved fixture retains sample 200/time 50 s and all five compact actuator rows. Camera/theme/language preserve the sample. Phone switches 5 command/0 applied plots to 0 command/5 applied. Fallback retains sample/temperature/control evidence when a fixture renderer refuses WebGL.
- G21: 14,318 pairs total, 12,894 inside published density bounds and 1,424 outside. The raw scatter rendered 14,318 marks. Boundary/outlier tests verify conservation.
- Whitespace check: `git diff --check` passes (line-ending notices only).

The earlier broader app discovery run completed 360 tests and was **not green**: 17 failures, 1 error, 6 skips. Its failing historical `test_agents` checks assume scored legacy policies match the current plant (stored `b5a3069f32a83754`, loaded `c236a8db3e201090`), the old catalog/protocol/fixture shape, or temporary fixture roots outside this checkout. The app correctly refuses incompatible models. Tests were not weakened to make historical policy execution appear available. Missing SB3/Torch and these full-suite exceptions remain limits of this machine/legacy tests, separate from the passing relevant regression suite.

Resume additions requested by Jad:

- `start.cmd` delegates to the existing PowerShell launcher, forwards quoted interpreter/port/vendor options, prevents bytecode writes and preserves the server exit status. Errors remain visible before the window closes. Actual startup used the repository virtual environment and served `/results` and `/agents` on port 8000. Behavioral CMD checks cover another working directory, paths with spaces, nonzero exit propagation and dependency refusal; the launcher suite has 8 passing tests.
- The engine geometry is adapted inside `app/` from Explanatory Simulation's casting, inline-six and turbo designs. It has six stationary cutaway pistons/bores, rods/crankshaft, head/camshafts, plugs, rail, cast shells and curved turbo blades. No React dependency or external source file is required or modified. Camera focus fits actual parts on resize; temperatures still use the existing recorded channels. Piston combustion/RPM are not inferred.
- Browser testing found that timeline input read its value after `pause()` had redrawn the slider at the previous sample. It now captures the selected index first. A real viewer event regression failed before the fix and passes afterward; browser selection reaches sample 200/time 50 s and survives camera/theme/language changes. Versioned module entry points prevent reusing the earlier cached viewer.
- `verification/astra-engine-matrix.json` records eight additional language/theme/viewport cases for the new geometry, all retaining sample 200, five actuator rows and no document overflow. The actual production viewer retains missing recording notices and four unavailable temperature values; `astra-new-engine-real.jpg` shows its new geometry without fabricated readings.

All 86 expected real recordings are absent; real recorded-policy playback remains unverified. The acceptance NPZ is clearly labelled, generated only under ignored `app/.superpowers/`, and served by a separate temporary fixture server. No scientific source file was generated or modified. Missing verdict/posthoc analysis, exact historical curves, thermal split and certain source channels cannot be invented. Full scientific R1b completion remains dependent on those inputs.

No commit, push, worktree, dependency install, training, evaluation or external model request was performed. Implementation, tests, reports and screenshots stay under `app/`; preexisting outside-app work is preserved. The production localhost server remains available at `/results` and `/agents`; the fixture server is stopped after acceptance.

See `verification/astra-graphics-coverage.md`, its JSON manifest, and `verification/astra-browser-matrix.json` for per-source availability and evidence. Independent review records are retained under ignored `.superpowers/training-linked-app/`.

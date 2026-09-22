# Three.js scene implementation report

## Owned files

- `app/static/sim/scene.mjs`: main miniature road scene and thermal engine inset.
- `app/static/sim/geometry.mjs`: dependency-free arc-length lookup and preview scaling.
- `app/static/sim/scene.test.mjs`: four meaningful geometry tests.
- This report.

No other implementation files edited. No commits or dependency installs performed.

## Interface

`createScene(host)` returns `update(frame, presentation)`, `setFollow(boolean)`, `resetCamera()`, `zoom(factor)`, and idempotent `dispose()`.

`createEngineScene(host)` returns `update(frame)` and idempotent `dispose()`.

Imports use `three` and `three/addons/controls/OrbitControls.js`. Both scenes render immediately, on resize, and on update. Main scene also renders when OrbitControls change. No internal requestAnimationFrame loop or optional ambient animation exists. Renderer construction errors propagate for the root UI to handle.

The initial main camera is an orthographic overview. Drag orbits, wheel zooms, and panning is supported. Follow translates the target and camera together with smoothing, preserving the user's orbit orientation; it suspends target tracking during direct control interaction. Reset restores the overview and disables follow. Numeric `zoom(factor)` multiplies current zoom within the controls' limits.

Main car position uses only finite `presentation.distance_m`. Missing values freeze the most recent position. A null initial frame and presentation park the car at the front of the loop. `frame.s_m`, wall time, speed, and rpm never advance the vehicle. Wheels use the same replay-distance position. The car's pitch follows the illustrative road tangent.

Only finite positive `presentation.preview_m` displays a preview. The highlight starts at the car, wraps continuously across the seam, and is clipped to one lap. Null/non-finite/negative/zero preview hides it.

## Visual implementation

Pastel sage terrain island with a charcoal elliptical road, ivory markings, hill section, stylized trees, rocks, and compact engineering station. Procedural cream sports coupe includes a long hood, low dark canopy, broad rear shoulders, four tires/alloy wheels, headlights, taillights, mirrors, side skirts, splitter, and raised rear spoiler. No external assets, textures, or downloaded fonts are used.

The inset contains an inline-six block/head, six cylinder caps and manifold branches, single turbo with turbine/compressor housings and connecting shaft, intake/exhaust pipes, radiator proxy, coolant loop, oil sump/filter. Block uses `block_c`; turbine uses `turbine_c`; radiator and coolant hoses use `coolant_c`; sump/filter use `oil_c`. Missing/non-finite values are gray. Neutral manifold/compressor/head parts are schematic and do not claim measured temperatures. There is no invented engine rotation or crank phase.

Pixel ratio is capped at 2; the main shadow map is 2048 square. Both scenes use ResizeObserver and dispose it, geometries, materials, shadow maps, renderer, canvas, and main controls/listeners.

## Distance scale

Exported `METERS_PER_WORLD_UNIT = 90` from both geometry and scene modules. One replay kilometer is 11.111 world units. Measured world loop length is 131.151732856464 units, corresponding to 11,803.6559570818 replay meters. A normal 1 km preview highlights approximately 8.47% of the loop. All geometry is illustrative: road elevation is never sent back to the replay, physics, grade, or temperature model.

## Verification

- Wrote geometry tests before implementing the geometry functions and observed expected failing assertions.
- `node --test app/static/sim/scene.test.mjs`: 4 passed, 0 failed.
- `node --check app/static/sim/scene.mjs`: exit 0.
- Native Node import of `scene.mjs` against the installed Three.js dependency succeeds, exporting `METERS_PER_WORLD_UNIT`, `createEngineScene`, and `createScene`.
- Verified actual loop length and parked position using the real arc mapping.

Tests cover seam position/heading continuity, equal spatial distance through bends and slopes, flat/climb/descent presence, and null-safe/clipped preview scaling. Root owns browser/visual and integration verification.

## Remaining limitations

- Vehicle and engine are deliberately stylized procedural schematics, not manufacturer CAD or an exact engine assembly.
- Scene terrain and pitch illustrate travel; they do not reproduce the logged road grade.
- Color ranges are illustrative visual ramps, not additional alarm thresholds or independent readings. Temperature numbers and legend belong to the root UI.
- Follow smoothing is frame-based visual easing; it never changes vehicle distance.
- Full browser rendering and responsive composition still require the root's integration check.

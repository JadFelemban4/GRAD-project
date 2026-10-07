# Arabic version and ready Supra model — 2026-10-04

This revision supersedes the original English scene and layout described in VALIDATION.md. It verifies the explainer, not the physical validity of the research model.

## Model provenance and fit

`src/model/source-scene.mjs` and `geometry.mjs` are unchanged copies of the project's existing procedural simulator model. No GLB asset was present. `supra.mjs` adapts that genuine model: daylight beam meshes are removed, materials support solid/cutaway views, and the original horizontal hood accents are fitted to the sloping bonnet. Core files remain untouched.

The original vehicle is +X-forward with Z wheel axes. Engine, six pistons, turbo, radiator, charge cooler, gearbox, driveshaft and rear differential use that coordinate frame. Exhaust terminates behind the vehicle; other paths remain under the bonnet. Engine teaching mode hides the car and enlarges the engine through camera framing. Slider-crank geometry keeps each connecting rod attached to its piston and rotating crank pin.

Three Node tests passed: source coupe bounds/material roles/four wheels; 201 samples per pipe path including radius inside the original vehicle bounds and under the local bonnet surface; full-cycle fixed rod length and pistons contained in sleeves. These establish visual packaging, not OEM dimensional accuracy or validated fluid simulation.

## Arabic and scientific fidelity

Default page: `lang=ar`, `dir=rtl`; metadata request `locale=ar`. Authored content includes 57 concepts, 23 observations, five actions, nine lessons and fourteen viva questions. English IDs, units, source objects and numeric contracts are preserved. Equations, source excerpts and units retain LTR direction. Two locale-contract tests and the existing 23 backend tests passed (25 total).

Applied the user-invoked i-have-adhd skill to content presentation: one visible experiment before the model, current and nearby lessons, optional roadmap, at most five component shortcuts, expandable observations and technical details. Arabic controls and paragraphs are larger than the prior interface.

## Actual browser verification

Used actual in-app-browser controls against the built UI and Python server, without injected application state.

- Source Supra exterior, transparent system views and separate enlarged engine render. Six cylinders remain legible. Zoom-in, zoom-out and camera reset operate; OrbitControls supplies drag rotation. No drag automation claim is made.
- Road step advances 0→1 s. Road override at 130 km/h and 12% grade followed by 30 s advances to 31 s: 2706 rpm, 335.4 Nm demand and 336.2 Nm delivered. Vehicle and road share the same grade rotation. All four lookahead horizons show the overridden 12% grade.
- Engine lab changed by keyboard from 2500→2600 rpm and recalculated automatically: EGT 848.6°C. Selecting the power stroke freezes the explanatory cycle with Arabic text. Engine thermal nodes stay absent rather than invented.
- Thermal layer displays actual housing/oil/block values with Kelvin-to-Celsius conversion. Source dialog opens exact numbered `engine_env.py:803` with the original English code and Arabic surrounding explanation.
- Research page remains inconclusive: +1.17 pp, CI −4.44..+6.78, ten pairs; hand preview margin −0.32 pp. Viva reveals an Arabic short explanation; fourteen questions remain available.
- Mobile at 390×844: content/page width 375 px after scrollbar; canvas 349×430 px. No page-level horizontal overflow; entire exterior fits. Model layers/nav scroll internally where needed. Desktop 1440×1080: canvas 861×520 px.
- Browser console returned zero errors and zero warnings during these interactions.

Independent review identified a fan concept-ID mismatch and fast-mode cadence mismatch. Corrected picking/value mapping to `fan_duty`/`pump_duty`; playback now uses one model step per `1000/speed` ms at each selected rate. Final production build and launcher check pass. Three.js remains a lazy scene chunk with a Vite size advisory.

Screenshots in `qa/arabic-*.png` document exterior, cutaway, enlarged engine and phone views. Existing core uncertainty and actor UNVERIFIED labels remain visible.

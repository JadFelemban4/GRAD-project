# Arabic learning flow and Supra model revision

Goal: Arabic-first, low-distraction teaching with the actual existing Supra model as the visual foundation. Work stays inside ex; original app and physics remain untouched.

## Design

Reuse `GRAD-project/app/static/sim/scene.mjs::supra`, the existing procedural coupe, with its actual lofted body, glazing, lamps, spoiler and wheels. The ready model is code geometry, not a GLB asset. Keep a solid exterior overview. Reveal internals only for the selected lesson or explicit cutaway control. Place engine, turbo, manifold, cooling and driveline inside a shared vehicle coordinate envelope. Exhaust runs under the vehicle to rear outlets. Never draw arbitrary tubes beyond the body.

Use a separate focused engine view when teaching four strokes. Its scale is explicitly enlarged, rather than placing oversized cylinders through the hood. Camera framing follows the selected system, with fitted orthographic views, portrait adaptation, reset and zoom. Drag controls never compete with animated recentering.

Arabic is the default UI language with RTL layout. English variable IDs, units, mathematical expressions and source excerpts keep LTR direction. Read-only metadata selects the Arabic authored dictionary using `locale=ar`, retaining identical numeric/scientific/source contracts. The English content remains preserved in `content.json`.

Apply i-have-adhd to the teaching experience: visible current step, one action prompt, short paragraphs, three nearby lessons, optional full roadmap, five or fewer component shortcuts per layer, detailed evidence and all observations available on demand. Increase Arabic text and controls; prioritize the model in the layout.

## Execution

- [x] Arabic content and source-contract test: create `content.ar.json`; compare IDs, sources, action bounds, observation order, verdict and numerical results against English.
- [x] Reusable actual model factory: adapt existing `supra` export inside `src/model`, retain provenance and test four wheels/body bounds/material roles.
- [x] Replace scene: source car, bounded internal assembly, focused stroke view, progressive layer highlighting, physical road slope, time-aligned preview, picking and camera controls.
- [x] Arabic app/components: RTL-safe labels, short guided instructions, visible progress, preserve real API interaction and uncertainty.
- [x] Browser verification: exterior and each layer at desktop/mobile, four-stroke/RPM controls, source inspection, unchanged research result, console and launcher; save screenshots and update validation.

Ownership: root owns Scene/App/style/backend locale/integration; results worker owns Arabic content; controls worker owns the five secondary UI component files/types; physics worker owns `src/model` factory and geometry tests. No concurrent file ownership.

Regression commands: `python -m unittest discover -s tests -v`, `node --test src/model/*.test.mjs`, `npm run build`; actual browser actions verify rendered geometry and Arabic layout.

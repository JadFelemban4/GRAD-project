# Interactive mechanical studio

Status: implemented and verified. See `STUDIO_VALIDATION.md` for the original studio checks, and `VEHICLE_PROJECT_VALIDATION.md` for the integrated car airflow and project story revision with 51 passing automated checks. The reference review adds standalone turbo inspection, guided split flows and frozen operating-point comparison; see `REFERENCE_REVIEW_2026-10-04.md`.

User direction: dark immersive lab inspired by the supplied X engine/lens references, confirmed 2026-10-04. Existing Arabic and ADHD learning flow stays available. Native Three.js geometry and the genuine local Supra body remain the base; no core edits.

1. Add a default studio mode with a large dark stage, direct operating-point controls and one focused part explanation. Keep learning/research/source modes accessible.
2. Upgrade standalone inline-six visual assembly: recognizable block, head, crank, articulated rods, piston rings, cam gear and hardware. Part picking selects the related real source concept. Exploded mode is explicitly pedagogical; restore returns to assembly coordinates.
3. Add solid/ghost/section displays, gradual exploded assembly, isolated/focused parts, camera presets, fullscreen, visual play/pause/rate and manual 720-degree cycle scrubbing. No animation control claims to change the plant's real RPM or its simulation dt.
4. Direct RPM/MAP/spark/lambda inputs call the existing read-only plant API and update actual outputs with debounce and stale-response protection. Explain absent thermal nodes and independent operating points.
5. Verify source/static contracts, geometry bounds at assembly zero, explosion reversibility, camera fit, API inputs, all presentation controls, mobile/desktop, console, launcher and screenshots.

Design read: audience is one graduate learning their own model. Main action is inspect a mechanism and see input→motion→computed result. Reference engine supplies dark inspection views and exploded display; lens lab supplies direct manipulation. Use charcoal stage, warm metal/copper, restrained amber selection, readable Arabic, no decorative glow or dense dashboard tiles. Motion serves the mechanism and honors reduced motion.

Ownership: root Scene/App/integration; physics new EngineAssembly component; controls new StudioControls component. Core source untouched.

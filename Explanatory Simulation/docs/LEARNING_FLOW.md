# Learning flow

The default tour introduces one experiment at a time. Exact lesson and viva prose lives in `content.json`; source-derived metadata lives in `backend/catalog.py`.

1. **Road creates load:** speed, grade and resistance → requested engine torque. Override the remaining road in memory and step; no independent torque slider bypasses vehicle coupling.
2. **Engine 101:** six cylinders, four strokes, RPM and torque. Inspect a frozen stroke or animate the deliberately slowed cycle; change actual plant inputs.
3. **Air and fuel:** absolute MAP, air mass, boost above ambient and lambda. Charge density and fuel cues accompany calculated airflow/fuel.
4. **Spark and finite burn:** shift spark timing and inspect torque, exhaust, knock and burn-angle consequences. Knock remains unvalidated.
5. **Turbo exhaust:** separate compressor and turbine, connect exhaust → shaft → compression and housing heat.
6. **Thermal memory:** apply heat then remove fuel/exhaust heat. Scrub turbine, oil, block and gas traces. Three nodes retain different memories.
7. **Agent and preview:** expose exactly 23 normalized observations and five applied supervisory commands; contrast current and future grade.
8. **Reward:** reveal torque response, baseline-relative fuel/life savings, weights, smoothness and diagnostic constraints.
9. **Research result:** interpret the paired interval, current hand-policy comparison, knock-margin diagnostic and uncertainty.

Sandbox exposes all controls and observations. Selector changes require Load/reset; road overrides and manual trims take effect at the next step. Trims are source-bounded and slew-limited. Single-step, slow/normal/fast playback, pause, reset, batching and timeline inspection share actual frames.

Trace mode searches names, IDs and source variables. Picking 3D components or keyboard-accessible buttons updates the inspector, causal graph and source excerpt. Physical dependencies are not promises of monotonic effects across all operating points.

Viva mode hides answers, provides a concise answer and expandable technical explanation, and focuses the relevant scene layer. Fourteen questions cover the requested defense topics, result interpretation and why H/τ is not currently quantitative evidence.

Recorded drives retain original timestamps and measured/modelled channel badges. Unavailable grade is explicitly absent. Paired actors use the same frozen evaluation road/start/preferences with different preview slots; the live reenactment is not asserted to recreate the scored traces.

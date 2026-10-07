# Integrated vehicle airflow and project story

The user's screenshot showed the source cutaway vehicle without an obvious turbo, inlet/outlet flow or project narrative. The studio now starts in **السيارة ومسار الهواء**. A three-action mission strip opens the vehicle, enlarged turbo, or **رؤية الطريق والقرار** directly.

## Car integration

`VehicleAirflow.tsx` mounts the same reusable `TurboAssembly` used in the enlarged view at position [2.06, 0.753, 0.62], scale 0.22. Its compressor/turbine connection ports match the vehicle's pipe endpoints exactly. Internal tube surfaces, including actual rendered radii and sampled spline interpolation, fit inside the supplied coupe bounds. The external front inlet and rear outlet use dashed flow guides rather than solid pipes projecting beyond the body.

Cyan arrows travel from outside the front bumper through the filter, compressor, charge cooler and intake. Orange arrows travel from the six exhaust runners to the turbine, underbody tailpipe and rear exterior. Four clickable labels open source concepts or the enlarged turbo. The path legend provides the same sequence as text. The source shell remains available in full/transparent/section views.

Mass flow is read from the actual engine point: air = `mdot_air`, exhaust = air + fuel in g/s. Six parallel runners use equal illustrative shares of the aggregate exhaust; there is no individual-cylinder mass-flow model. Arrow travel, geometry, particle density and turbo rotation are educational, not CFD or measured turbo speed. Elapsed presentation time preserves paused phase across input changes. Vehicle operating-point controls remain independent of the road session; this distinction is stated in the legend.

Labels have a stable Canvas DOM portal and explicit left anchoring. This avoids a first-label mount failure and the RTL static-position offset. Mobile inlet placement separates its label from the turbo label. Road-view gas labels are suppressed so future road inputs remain the focus.

## Road and decision

`ProjectStory.tsx` displays three linked steps: future road grade, current load/thermal state, and applied supervisory commands over ECU. It uses the selected real road-session frame. Preview values are aligned to the observation that generated the action (`input_time_s`, four `preview_pct` values). The fallback samples the source road at that input time plus 2/5/15/30 seconds. Missing/non-finite data remain unavailable; reset-frame command placeholders are not presented as applied commands.

Future boards ahead of the car are schematic inputs with time horizons, not surveyed positions or camera measurements. Phone boards show compact horizon labels; their actual numeric grades are in the story immediately below. Current temperatures are labelled as current model state, not numeric future-temperature forecasts.

**شاهد مثالًا قبل الصعود** explicitly recreates the locked road with the handwritten predictive policy, no custom road overrides, and advances the genuine source environment to 170 seconds. This demonstrates nonzero future grade before the current grade changes. It does not claim a trained SAC actor. The controller selector separately allows SAC reruns with their existing unverified-provenance warning.

Preview toggling recreates the same selected policy/seed and replays to the same elapsed time. Manual trims and custom road overrides are retained for this intervention. Seeking is bounded by the new source road duration rather than an arbitrary 180 seconds. Session replacement and page unload release owned transient API sessions. The example is deliberately a fresh locked-road setup.

## Evidence

Production build and TypeScript pass. All **26 Node geometry/presentation/data tests** and **25 Python API/source tests** pass (51 total). `launch.py --check` reports `Local app healthy`. Existing Vite chunk-size and Starlette/httpx deprecation advisories remain.

Real browser verification at desktop 1440×1080 and phone 390×844:

- Default vehicle shows four labels, internal colored paths and front/rear external arrows. Clicking the turbo label opens the enlarged assembly. Clicking exhaust opens the `exhaust_flow` Inspector with 65.3 g/s at the default independent point (air 61.2, fuel 4.2 before rounding).
- Example at end time 170 s / input time 169 s: current grade 0%; future grades [0, 0, 12, 12]%; requested torque 115.0 Nm; EGT 719.7 °C; turbine housing 437.2 °C. Applied commands [0.0 °BTDC, -0.05 lambda, -9.9 kPa, 1.00 fan, 1.00 pump].
- With preview hidden at the same input time, current grade stays 0% and all four preview fields become 0%; EGT 744.6 °C, turbine housing 438.9 °C and applied lambda/boost trims return to 0.00 / 0.0 for this handwritten policy.
- The next-step button advances the actual observation time. Further stepping reaches current grade 12% after the climb begins. Keyboard navigation reaches the preview fields. A CSS connector overlay that intercepted the preview toggle was corrected.
- At end time 182 s / input time 181 s, hiding preview retains current grade 12.0% and input time 181 s while all future slots become zero. Re-enabling preview replays the same elapsed time. Selecting sighted SAC seed 0 creates the actor session and visibly retains its unverified-rerun warning.
- Mobile labels remain inside the viewport and the inlet/turbo labels do not overlap. Story controls flow below the canvas; page scroll width is 375 px at the 390 px test viewport (390 px in expanded mode).

Proof files: `qa/vehicle-airflow.png`, `qa/vehicle-airflow-mobile.png`, `qa/project-vision.png`, `qa/project-vision-mobile.png`.

The sibling GRAD-project tracked files remain unchanged. Recorded research evidence still has the existing inconclusive paired preview effect; this visualization does not change the experiment, model, actor verification status or recorded conclusions.

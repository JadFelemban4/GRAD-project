# Backend and UI integration validation

Reviewed against `GRAD-project/engine_env.py`, `plant.py`, `thermal.py`, `evaluate.py`, and `app/replay.py`, plus the current `ex/src/App.tsx`, `Labs.tsx`, `Plots.tsx`, and `Scene.tsx` integration. The bridge imports the project simulator and keeps each session in memory; it does not write simulation or replay results into the source project.

## Data contract checked

- `engine_env.py:786–810` defines the ordered 23-value observation. Slots 0–13 are RPM, MAP, TPS proxy, spark, lambda, block/oil/turbine temperatures, charge temperature, ambient, barometric pressure, humidity, speed and current grade. Slots 14–17 are grade at 2/5/15/30 seconds. Slots 18–22 are torque request, aggression and the three weights. Values are clipped to `[-10, 10]`. Current grade and future grades are stored as fractions scaled by 12.
- `simulation.py` preserves these normalized values in `obs_in` and `obs`. It reports physical `preview_pct` by undoing the factor of 12 and converting the fraction to percent. `action` is the normalized request; `requested` is its source-rescaled physical vector; `command` is the slew-limited vector actually applied by the environment. Thermal-node values (`t_block`, `t_oil`, `t_turb`) are kelvin.
- Each step frame represents an integrated state at `time_s` (interval end) and now also carries `input_time_s` (sample used to create the action) and `dt`. At the Episode 1 grade transition, the action frame uses the 179-second flat-road input, ends at 180 seconds, and its next observation sees the 12% grade. `Plots.PreviewRoad` uses `input_time_s` and its `preview_pct` conversion matches the source scaling.
- The locked source cycle has 720 samples at dt=1 s, with a 20-second speed ramp and grade changing from 0% to 12% at 180 seconds. Reset uses the first frozen Phase D episode seed and pins `evaluate.EPISODES[0]` weights for every controller. The source environment truncates after 719 integrations; the bridge follows that behavior.
- `api_plant` returns the named scalar outputs from `plant.predict` with Celsius/Kelvin conversion made explicit. Charge temperature uses `plant.charge_temperature(ambient_k)`. It adds the airflow-specific log-derived operating ceiling and warnings; it does not silently clamp the independent engine-lab MAP input.
- `api_thermal` calls `plant.predict` and `ThermalNetwork`, integrates at 0.1 seconds, and starts all three nodes cold at ambient. EGT is present only during the heating phase when the plant supplies an exhaust-temperature value. At start and during cooling `egt_c` is null, because there is no exhaust flow; `exhaust_boundary_c` separately exposes the ambient boundary used for cooling.
- Replay field names match `app/replay.py:210–220`: original `t`, RPM, road speed, coolant, oil, turbine estimate and torque estimate. Grade is unavailable. Oil source maps to `recorded`/`estimated`/`unavailable`.

## UI mismatches found during review (resolved by integration)

1. `Scene.tsx:213,268` sends interval-end `time_s` to `RoadLookahead`, but road grade, current grade and preview values on the frame refer to interval-start `input_time_s`. This shifts the 2/5/15/30-second road markers by one simulation step. `Plots.tsx:47` already uses `input_time_s`; the 3D road lookahead should do the same while keeping animation time at `time_s`.
2. `Labs.tsx:15` builds an Engine Lab frame with `t_block = ect_c + 273.15` and no turbine/oil temperatures. `App.tsx:30` uses it as the active Scene frame, where `Scene.tsx:249` and its thermal visuals fall back to 298 K for missing nodes. ECT is the plant input here, not a simulated ThermalNetwork node; the Scene can make the synthetic temperature overlay look like a live thermal result. Hide those live thermal overlays in Engine Lab or label/use a distinct frame mode.
3. `App.tsx` Replay rendering (`replay-values` block around line 96) marks coolant as `MEASURED` unconditionally. `app/replay.py:210` returns `coolant_c=None` when that recording has no coolant channel. In that case the value correctly displays unavailable while its evidence badge incorrectly says measured. Choose the badge from the selected frame value or the trip’s `has_coolant` metadata.

No other backend/UI field-mapping mismatches were found in the reviewed paths. Baseline values are the parallel production-representative ECU model state, not factory firmware; the bridge labels this reference and notes its fan schedule difference. Replay oil evidence is selected from `oil_source`; turbine and torque are modelled; unavailable source channels remain null.

Final disposition: (1) Scene lookahead now uses `input_time_s`; (2) Engine Lab keeps `ect_input_k` as input, leaves thermal nodes absent, and Scene displays unavailable/gray; (3) missing replay values receive an UNAVAILABLE badge. Production browser checks confirm these fixes; see VALIDATION.md.

## Verification

Ran the complete test suite with the project virtual environment:

```text
python -m unittest discover -s ex/tests -p "test_*.py" -v
Ran 23 tests — OK
```

The suite covers catalog/source contracts, direct-environment parity, preview blinding, Episode 1 cycle/weights, the 180-second input/end timestamp boundary, controls validation, actor labeling, engine and thermal endpoints, replay allowlisting, and static UI serving when `ex/dist` exists. The installed Starlette TestClient emits a deprecation warning about `httpx`; it does not fail the suite.

Separately ran a complete manual Episode 1 locked session in a fresh Python process, issuing batches of at most 120 steps. It produced 719 frames, `done=True`, 719 environment steps, final frame time 719.0 s, and zero non-finite numeric fields. The only nulls were intentional unavailable initial diagnostics.

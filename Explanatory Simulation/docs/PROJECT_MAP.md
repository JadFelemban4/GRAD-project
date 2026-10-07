# Verified project map

Verified against the local `GRAD-project` tree on 4 October 2026. Since relocation on 7 October, that tree is the parent (`../`) of `Explanatory Simulation`. Its working tree is authoritative. No source physics or result file is modified by this explainer.

## What is being tested?

Whether seeing future road grade helps a supervisory engine controller protect components while delivering torque and managing fuel. The broader H/τ hypothesis is a research goal, not an established universal rule. A second plant and a corrected sweep are outstanding.

## Physical system

The conceptual vehicle represents a 2023 Toyota GR Supra with a BMW B58B30O1, turbocharged 2997.5 cc inline six, and ZF 8HP51. `plant.b58()` supplies geometry. `Vehicle` supplies road force, eight ratios, final drive, shift and kickdown logic. Geometry on screen is a teaching diagram, not OEM CAD.

Road speed, acceleration, grade and ambient air density determine wheel force. The gearbox converts this demand to engine torque and RPM. The inner MAP loop tracks torque. The single-zone, zero-dimensional spark-ignition cycle calculates air, fuel, torque, knock integral and exhaust gas temperature. Exhaust mass flow is air plus fuel. `ThermalNetwork` integrates block/coolant, oil and turbine housing states.

## Control hierarchy

The baseline ECU is production-representative, not extracted factory firmware. It schedules spark, enrichment, knock response and fan. A separate reference plant and thermal state run beside the supervised plant. The SAC agent adds spark, lambda and MAP trims; fan and pump are absolute duties. Its five policy outputs are normalized [-1,1], then rescaled, slew-limited per second and clipped using source constants. It does not command gears, road speed or the real vehicle.

The 23 observations are RPM, MAP, TPS proxy, spark, lambda, block, oil, turbine, charge temperature, ambient, barometric pressure, humidity, speed, current grade, four future grades, torque request, aggression and three preference weights. Future grade is sampled at 2, 5, 15 and 30 seconds. Blinding zeroes only slots 14–17; current grade remains visible. Temperature slots 5–7 are block, **oil**, turbine.

## What is known, calculated or assumed?

- Measured: logged RPM, airflow, pressure, spark/lambda and coolant/oil channels where the log provides them. A measurement channel is not interchangeable with a model input: the intake channel is upstream of the charge cooler.
- Derived: fitted block/oil thermal parameters, boost operating envelope, calibrated spark offset, enrichment dwell and kickdown table in `data/derived_params.json`.
- Modelled: torque, EGT, knock, charge temperature, housing temperature, thermal damage proxy and all simulation frames.
- Published: engine geometry and transmission ratios with citations in `REFERENCES.md`.
- Assumed: turbine heat capacity and heat-transfer coefficients, exhaust backpressure closure, unidentifiable radiator parameter split and damage-law scaling. No logged turbine sensor validates the turbine node.
- Validation: `validate.py` reports 8 of 11 band checks in the current state. Those checks are not comprehensive engine validation, and several literature bands lack verified sources. The load identity does not independently validate torque or thermal predictions.
- Uncertain: hot-region extrapolation, knock realism, turbine dynamics, some factory configuration details, and numerical thermal stiffness. At dt=1 s coolant oscillates; dt above approximately 1.1 s is unsuitable. The explainer preserves dt=1 s for scenario fidelity, and uses substeps only in a separately labelled thermal teaching lab.

## Current result

Use `results/agents/terrain_dt1/index.json` and its generated README, not older Phase D/D2/C4 figures. Twenty retrained agents: ten sighted and ten blind. Mean sighted-minus-blind damage-cut difference +1.1693 percentage points, 95% CI [-4.4391, 6.7777], n=10: **INCONCLUSIVE**. Median agent gains over hand policies depend heavily on the untested knock margin. A median win does not guarantee protection on every episode. Disabling spark advance reduces the typical cut below current-grade protection. Historical files are explicitly excluded from headline cards.

## Causal loop

Road → wheel force → gear/RPM/torque request → baseline ECU + supervisor trims → intake charge/combustion → torque/fuel/exhaust → thermal memory → damage proxy → agent observations → next action. Future road grade enters the observation before the vehicle reaches that section. Reward uses baseline-relative fuel/life gains and a strongly penalized tracking error, plus uncertainty and smoothness; returned constraint costs are diagnostics, not automatically extra reward penalties.

# Housing-lag figure: validation, 29 October 2026

Branch `JMF-2340550-anatomy-housing`. A new lesson, `housing_lag` (sixth of ten),
puts an interactive figure on the stage, where the 3D scene usually is, so the
tour no longer shows the car in every lesson. The figure is drawn with the
Anatomy kit: a hot-gas test stand.
A burner, standing in for the engine, drives gas into a turbine housing, and a
two-pen strip recorder draws the gas and the housing metal. The reader lights
and stops the burner and watches the metal lag the gas; a dot marks where τ ends.

Nothing in the physics changed: no file outside `Explanatory Simulation/` was
edited.

## What it draws, and where each number comes from

All from `figures/housing-lag/params.json`, written by `export_params.py` from
the parent repo (plant_sha `3c48890dd15bc116` on Python 3.12):

| quantity | value | source |
|---|---|---|
| engine point | 3000 rpm, 180 kPa, 42 °C ambient, spark 8, λ 0.92 | the lab's own thermal experiment, `ThermalLab.tsx` `initial` |
| gas temperature | 940.62 °C | `plant.predict` at that point |
| exhaust flow | 141.502 g/s | `plant.predict`, air plus fuel |
| `c_turb`, `ua_turb_amb`, `ua_gas_turb` | 6000 J/K, 18 W/K, 0.9 W/K per g/s | `thermal.ThermalParams`, all three **ASSUMED** |
| τ, burner lit | 41.28 s | `c_turb / (ua_gas_turb · flow + ua_turb_amb)` |
| τ, burner off | 325.2 s | the same, with the flow at thermal.py's 0.5 g/s floor |
| where the housing settles, lit | 829.3 °C | the node's steady state |

"Off" is what `/api/thermal`'s cooling phase feeds the network: no fuel, no
flow, gas at ambient, 800 rpm. The figure says the burner stands in for the
engine, that τ rests on an assumed heat capacity, that no sensor on the car
measures the housing, that time runs 10 times faster than real, and that the
turbine wheel's spin only shows that gas flows.

## What was checked, and what it printed

| check | result |
|---|---|
| `node --test src/model/housing-lag.test.mjs` | 4 of 4 pass: the page's model equals `ThermalNetwork` within 1e-9 K, every second of 120 s lit then 180 s off; one 1 s step equals ten 0.1 s steps; τ covers 1 − 1/e of the way (63.2 %) within 0.002, lit and off |
| `python -m unittest tests.test_housing_figure` | 4 of 4 pass: params.json equals a fresh export; the point equals ThermalLab's; at 30 s the figure's housing temperature equals `/api/thermal`'s within 1e-8 K |
| the tests can fail | each was run against a changed value (c_turb +1, one sample +1e-6 K, MAP +1 kPa, the 30 s sample +0.01 K) and each failed |
| reference run | 211.57 °C at 10 s, 449.02 °C at 30 s, 786.47 °C at 120 s: the values the lab's thermal experiment shows |
| `npm run build` | type check and bundle pass; `dist/figures/housing-lag.html` written |
| anatomy line check, mid-run, dark Arabic and light English | `line ends: 0 of 230` in both; the first build had one (a turbine blade ending 1.2 px short of the outlet ring), fixed |
| `python launch.py --check` | "Local app healthy"; `/figures/housing-lag.html` served (200); `/api/meta` lists the lesson after `exhaust_to_turbine` |
| in the lab, tour mode | lesson 5 shows the 3D scene; lesson 6 shows the figure on the stage (745 px tall at 1440 px), with no scrolling; the engine tab brings the 3D scene back and the heat tab brings the figure back; it follows the language and theme, starts after 1.4 s, console clean |
| screenshots | dark and light, Arabic and English, 1100 px and 390 px, close-ups of the outlet (6×) and the recorder (5×), heating and cooling; kept in `qa/figures/` (not committed) |

## Failures that were already there

The lab's suites do not all pass, and they did not before this change either.
Each failure below was reproduced on a clean copy of `main` (`git archive main`),
with the same result:

- `tests/test_catalog.py:83` pins the premise figure at -0.32; the data now gives
  -0.01. Line 86 pins plant_sha `c236a8db3e201090`; the live plant is
  `3c48890dd15bc116`. Both are from before the plant fixes of 8 October
  (`team/jad.md`, "the learning lab's pins").
- `tests/test_simulation.py`, three tests, expect the locked road's grade to be
  0.12 at exactly 180 s; since 8 October the grade ramps in over 8 s
  (`engine_env.GRADE_RAMP_S`), so it reads 0.0 there.
- `src/model/provenance.test.mjs`, one test, matches an older wording of the
  parent's `validation_table.md`.

Totals on this branch: Python 35 tests, the same 4 failures (31 and 4 on main);
Node 142 tests, the same 1 failure.

## Found, not fixed

Six texts still say the block/coolant update "oscillates at dt=1 s", although
`thermal.py` has sub-stepped at 0.1 s (`DT_SUB_MAX`) since 8 October:
`content.json` lines 693, 725 and 2111 (and their Arabic twins),
`backend/catalog.py:310`, `src/types.ts:39`, `docs/LIMITATIONS.md:27`.
They are left for a change of their own.

## Limits

- The housing node is one lump (housing and manifold) with assumed constants.
  The figure shows the project's model, not a measured housing.
- The burner is a stand-in for one engine point. On the locked climb the flow,
  and so τ, differ.
- The red tint on the housing grows with the modelled temperature; it is a cue,
  not a colour model of hot iron.
- The idle tour stops for good at the first click or key, so it never overrides
  the reader's own experiment (the kit's default resumes it).

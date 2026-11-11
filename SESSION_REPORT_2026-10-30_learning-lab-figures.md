# Session report — 21 to 30 October 2026: the learning lab's first figure, its stage, the project map

Jad's session, on the branch `JMF-2340550-anatomy-housing` (from `cf43fbb`, not
pushed). Nothing in the physics, the data or the training changed: every edit
is under `Explanatory Simulation/`, plus this report, `CHECKPOINT.md`,
`STATE_HISTORY.md` and `NEXT_SESSION_2026-10-30.md`.

## 1. What was done

- **Ghassan's literature-review message (21 October), explained to Jad.** It
  asks Jad for library access (UJ login, the Saudi Digital Library; SAE and ASME
  papers through interlibrary loan or a budget), the format from Dr. Hammam, a
  yes or no on buying ASME V&V 20, a team decision on a housing thermocouple, and
  drive C then A. It also argues that the claim in `CLAUDE.md` ("nobody has
  mapped") must be reworded: Tomizuka and Whitney 1975, Seiler et al. 2012 and
  Yu et al. 2020 already tie preview's value to the horizon over the system's
  time scale; what stays new is whether different plants fall on one H/τ curve
  for a protection problem with learned agents. Jad has not answered him yet; the
  papers were not opened in this session.
- **The Anatomy skill** (github.com/wheresryan22/anatomy, commit `1482e84`, MIT)
  was read before installing: Jad's part by this session, the rest by a helper
  agent (verdict: safe with caveats; network only to a local Chrome, publishing
  only on an explicit request). Installed for Jad only at
  `~/.claude/skills/anatomy` from that reviewed copy, never with `npx`.
- **Lesson `housing_lag`, the first figure** (`de7d083`): a hot-gas test stand,
  a burner standing in for the engine, a turbine housing and a two-pen strip
  recorder. The housing lags the gas; a dot marks where τ ends (41.28 s lit at
  141.5 g/s, 325.2 s off; c_turb ASSUMED and said so on the figure). Every
  number comes from `plant.py` and `thermal.py` through
  `figures/housing-lag/params.json`; the page's model equals `ThermalNetwork`
  within 1e-9 K. Detail: `Explanatory Simulation/docs/HOUSING_LAG_VALIDATION.md`.
- **Jad's review: the figure goes on the stage** (`cc5dc24`). A lesson names its
  figure in `content.json`; in the tour the figure replaces the 3D scene while
  its layer is selected. **Then the turbo** (`dc08498`): the tour draws the
  studio's turbo model in lessons 3 and 5. The stage by lesson is now car,
  engine, turbo, engine, turbo, figure, car, road for the last three.
- **Jad's idea: a project map** (`fe35cc6`), in the manner of Obsidian's graph:
  58 concepts, 155 arrows cause to effect from the content files' own links,
  six coloured parts, search in both languages, a button to each concept's line
  in the code. Detail: `Explanatory Simulation/docs/CONCEPT_MAP_VALIDATION.md`.
  Jad wants it for looking things up later (thesis, viva).

## 2. What was found and left alone

- The lab's suites already fail on a clean `main` (`git archive main`, same
  failures): Python 4 of 31 (`test_catalog.py` lines 83 and 86 pin the plant of
  before 8 October; three `test_simulation.py` tests expect a grade step at
  180 s, which ramps over 8 s since 8 October), Node 1 (`provenance.test.mjs`).
- Six texts in the lab still say the coolant update "oscillates at dt=1 s",
  though `thermal.py` has sub-stepped at 0.1 s since 8 October
  (`HOUSING_LAG_VALIDATION.md`, "Found, not fixed").
- The map shows a loose link: `thermal_time_constant` listed as a cause of
  `preview` (`CONCEPT_MAP_VALIDATION.md`).

## 3. Checks at the close

`python verify_docs.py`: run at the close, read by its exit code (see the
commit). Lab: `npm run build` passes; Python 35 run, the same 4 failures as
`main`; Node 147 run, the same 1 failure; `python launch.py --check` "Local app
healthy".

## 4. Next

Jad's choice for the next session: a quality check of the whole code with the
`ponytail` skills (`NEXT_SESSION_2026-10-30.md`). Still waiting on Jad: whether
to push this branch, and his answers to Ghassan's message.

# SDD ledger — plan: docs/superpowers/plans/2026-09-21-replay-lab.md

Baseline 9c4b5fa. User approved the design. No code changes before approval.

Ruling: implement directly on the requested clean feature branch — user explicitly identified it; no isolated checkout is needed for this local deliverable.
Ruling: no further design approval gate — the written spec records the already-approved chat design.
Ruling: one isolated scene implementer can run alongside root's Python and UI integration; file ownership prevents collisions.

Preflight interface review is recorded in the plan. Task 1 started; Python venv created. Dependency installation needs network access.

---

## Session 2 — 21 September 2026, HEAD e429715

Picked the plan up at Task 3's last box. Tasks 1 and 2 were already complete
and green; Task 3 was one file short and Task 4 had not started.

**The page was dead and nothing said so.** `simulation.html:78` loaded
`/static/sim/main.mjs`, which did not exist. `GET /simulation` returned 200,
`python -m app.test_simulation` passed 8 of 8, `node --test` passed 10 of 10,
and the browser silently 404'd the one module that drives everything. This is
mistake 11's shape in the app: every check was green and the product did not
run.

### Done this session

- **Task 3 closed.** `app/static/sim/main.mjs` written: catalog, polled build
  with progress, playback transport, per-frame DOM, the eight-gear strip,
  shift marks, two SVG charts with a shared cursor, camera controls, the
  fingerprint block, WebGL-failure fallback.
- **`app/static/sim/panel.mjs` split out** of it. Pure presentation logic —
  gear labelling, H/τ, chart paths, cursor geometry — with no DOM and no
  physics, so it is unit tested without a browser. `main.mjs` keeps only DOM
  glue.
- **Task 4 delivered**: `app/README.md`, `app/requirements-replay.txt`,
  `app/start-simulation.ps1`.

### Approved extension: H/τ shown live

User approved on 21 September, in conversation, after the design. `τ` is the
project's own denominator and `Estimator` already computes it per sample, but
`replay.py` was dropping it. Now passed through (one field) and displayed
beside H, with a caption saying it is a reading from this recording and not an
experimental result. `tau_turb_s` is the Estimator's value, never recomputed;
a test asserts it falls as exhaust flow rises, so a stubbed constant fails.

### A CHANNEL WAS MISREAD AGAIN — the fifth time on this car

Found by adversarial review, then reproduced. `infer_gear` accepted `Internal
gear (including neutral and reverse)` as corroboration and promoted a
ratio-INFERRED gear to `gear_source='recorded'`. Measured on the data:

| log | values that channel takes |
|---|---|
| `fb988991` | **8.0 on all 3259 populated rows**, 0.0 on the other 193 |
| `f51686d7` | 0.0 on all 211 rows |

It is a constant, not a gear — 233 of the 8.0 rows are at standstill and 429
are while `Actual gear` reads 1. The effect: **2158 frames of `fb988991`, 62 %
of the drive, displayed an eighth gear as MEASURED** on a car whose gear
channel saturates at 6, so an eighth gear can never be a recorded value here.
The green «مسجّل» label is exactly the measured-vs-estimated distinction the
rest of the lab exists to protect.

Mistakes 2, 7, 13 and 18 are the same failure: a channel name taken at face
value. This is the fifth. The branch is deleted, the `internal` argument is
kept with the measurement written beside it so nobody re-adds it, and a test
asserts `infer_gear(1944.59, 120.0, 6, 8)` returns `estimated`. Re-measured
after the fix: `fb988991` now reports `(8, 'estimated') 2158`, and no gear
above 6 is labelled recorded on any drive.

### Three defects found by an adversarial read, and fixed

1. **No build cancellation.** `Estimator` runs at 74–79 rows/s (measured), so
   the longest recording is a multi-minute build. `ReplayStore` had no way to
   stop one, so picking it returned `busy` for every other trip until it
   finished. The builder now takes a cancel event checked in the progress
   callback; a request for a different trip abandons the one in flight.
   Verified live: the long build was cancelled and a short trip became ready
   in 2 s.
2. **A failure poisoned a recording for the life of the process.**
   `self._errors` was never cleared, so one error made that trip permanently
   unopenable. The error is now reported once and then forgotten, so the user
   can retry.
3. **`has_speed` was a header check, not a data check.** `3f64372e` carries a
   `Vehicle speed` column reading 0.0 on all 276 rows, so the catalog promised
   a moving car and delivered a parked one. `has_motion` now reports the data
   fact beside the header fact, and the UI says so.

### One risk accepted deliberately, with a mitigation

The decorative road is a short loop, so a long drive laps it many times — a
viewer could read "car climbs hill, metal glows red" as causation. User chose
to keep the loop illustrative and clearly labelled rather than flatten it
(flattening also breaks a `scene.test.mjs` assertion). Mitigation: the caption
now names the lap number and the loop length, so the repetition is visible
rather than only asserted.

### A 36-agent adversarial review, and what it changed

Four reviewers (correctness, honesty, Python, integration) over the new and
changed files, each finding refuted by independent verifiers before it counted.
**26 findings survived refutation.** Four of them were defects introduced by
this session's own work, and all four are fixed:

1. **Switching trips left the previous drive's telemetry on screen** for the
   whole build — speed, RPM, the lit gear cell, temperatures and the sample
   index, under the new drive's name. `loadTrip` set `lastFrame = null` while
   `sampleAt` on an empty set also returns `null`, so `frame !== lastFrame` was
   false and `draw()` returned before every panel write. Reproduced headlessly
   by a verifier against a stub DOM. Fixed with an `undefined` sentinel and a
   forced clear; the panel now blanks to `—` the instant a new trip is chosen.
2. **Cancellation could livelock.** Every poll for a different trip cancelled
   the build in flight, so two browser tabs on two recordings would cancel each
   other forever and neither would finish. Cancelling is now a user action:
   only the first request after someone picks a drive carries `preempt=1`.
   Verified live — a poll leaves the build running, a pick stops it.
3. **`requirements-replay.txt` could not import the server.** It omitted
   `gymnasium`, which `engine_env` imports at module level and `app/estimator`
   depends on. It would have worked on this machine and failed on a teammate's.
4. **Opening the page auto-built the longest recording.** The list is sorted
   longest-first, and the default was `trips[0]` — the two-hour drive, minutes
   before anything rendered. It now opens the quickest recording that moves.

Also fixed from the same review: the horizon card lost its `s` and `m` units
because `setText` overwrote the nested `<small>`; a failed load disabled the
transport with no way back, so there is now a retry button; τ carried no
estimated marker and no statement that `c_turb` is assumed; the coolant dot
was hardcoded `recorded` on drives with no coolant channel; `distance_partial`
was computed and ignored, so a gapped drive showed a short odometer as if
complete, and it now reads `≥`; `trip_catalog` was `lru_cache`d for the
process lifetime, so a newly copied drive never appeared without a restart;
`start-simulation.ps1` ignored an npm failure and then served a dead page; and
two claims in `app/README.md` were wrong — it said the browser computes
nothing, when it does integrate speed into distance, and it stated a low-speed
gear rule the code does not implement.

**Not fixed, recorded instead:** `frame.modelled` — the estimator's own list of
substituted inputs — is sent to the browser and never displayed, so an estimate
built on a default input looks like one built on a measurement. It needs a UI
decision about where it belongs. And `verify_docs.py` cannot scan `.mjs` or
`.html`, so the lab's captions sit outside both its scans; that belongs to
AUDIT2 fix 2, not here.

### Verification, run this session

| check | result |
|---|---|
| `python -m app.test_simulation` | **14 of 14** (was 8; +6 this session) |
| `node --test "static/sim/*.test.mjs"` | **22 of 22** (was 10; +12 this session) |
| `python -m app.test_replay` | **49 of 49**, unchanged |
| `python verify_docs.py` | **1 of 67 failed — the same pre-existing `FULL_RUN.txt:553` and `:632` as before these changes.** No new violation. |
| live server, real HTTP | all assets 200; a trip built to `ready`; τ, gears and provenance present |

**The `verify_docs` failure is not ours and predates this work.** Both `WRONG`
lines are against `FULL_RUN.txt`, a committed log of an earlier `verify_docs`
plus `drift_test` run: the checker now scans `.txt`, so it reads the drift
test's deliberate synthetic mutations as real document errors. Recorded here
because the next person will otherwise think the lab broke it. It belongs to
AUDIT2 fix 2, not to this plan.

### Mutation-tested, because a test that cannot fail cannot confirm

The new asset/id guard was checked against both bugs it claims to catch:
deleting `main.mjs` fails it with `sim/main.mjs is referenced by the page and
does not exist`, and adding a `$('no-such-id')` fails it naming the id. Both
restored and green afterwards.

### Not done, and why

- **No browser screenshot pass.** Playwright is not installed and adding it
  pulls ~300 MB of browsers into a repo whose `requirements.txt` is
  deliberately minimal. Covered instead by the asset/id guard, which catches
  the class of failure that killed the page, plus a live HTTP check. **Visual
  layout on a real screen is still unverified** — that is the open item.
- Physics untouched: no change to `plant.py`, `thermal.py`, `engine_env.py`,
  `logs/raw/` or `data/`.


---

## Session 2, later the same day — dark mode, English, and the threshold

Three features the user asked for after seeing the lab run, plus two defects
their screenshots exposed.

### Dark mode
77 semantic CSS variables replacing 97 literal colours, a dark palette under
both `[data-theme="dark"]` and `prefers-color-scheme`, and a matching palette
in the 3D scene with a `setTheme()` that re-tints materials without rebuilding
geometry. The provenance colours were re-tuned for the dark ground and checked
against a dichromat simulation, because they carry meaning rather than style.

**The night needed two passes.** The first lit the lamps, the windows and the
headlights and dropped the ambient to make them read — and the ground, the
trees and the road between the lamps disappeared with it. An isometric view
whose landscape has no shape is not a darker version of the scene, it is a
worse one. Ambient went 1.15 -> 1.95, key 1.5 -> 2.3, and the base surfaces up
about 36 % on average. Still well below daylight, so a lamp is still the
brightest thing on the verge. Every night effect is `opacity: 0` in the light
palette, verified key by key, so daylight is untouched.

### English
173 keys in both languages in `static/sim/i18n.mjs`, with `dir` and the RTL
layout pins flipping together. Tests assert the two languages define identical
keys, that the gear reading is the same in both, and that each honesty caveat
survives translation — a caveat lost in translation is this project's worst
failure mode, so it is checked rather than trusted.

**Arabic leaked into English mode on first run**, in two panels. `gearState`
and `previewCaption` take a language and default to Arabic, and two call sites
passed none. Nothing failed: the page rendered and one panel was simply in the
wrong language. That is mistake 1's shape — a default that silently selects
different behaviour. Fixed, and a test now reads `main.mjs` itself and fails
if any language-taking function is called without one; mutation-tested by
re-introducing the bug.

### The turbine threshold highlight
Two signals, because the obvious one is not enough on a first-order node.

A 50 K value band, and — the useful one — the steady state the CURRENT
operating point implies, taken from the estimator's own fixed point rather
than extrapolated (AUDIT.md M10 records that extrapolating the trend is wrong
here). Measured on `670063b2`: the housing peaks about 70 K below the
threshold so the value band says nothing all drive, while the steady state the
driving implies reaches far above it and 133 frames correctly read as
approaching.

**The band was nearly self-justifying nonsense.** The first docstring argued
50 K was the margin hard real driving reaches — and the hardest recorded drive
peaks 52 K short, so it would never have lit. The docstring was corrected to
say what the data shows rather than widening the band until something lit up,
which would have been choosing a threshold to produce an indication.

### World scale: speed was unreadable
The user reported 60 km/h looking the same as 164. Measured: at 90 m per world
unit they crossed the view in 292 s and 107 s. The 2.7x ratio was there and
both read as stationary. The scale is now 35 m/unit (41 s and 113 s). It
enters no calculation — distance is integrated from recorded speed in metres
and divided by this only to place the car — and the loop is now 4.6 km rather
than 11.8, which is why the lap caption exists. A test pins the two speeds
apart so the old value cannot come back quietly.

### Also fixed from the same screenshots
The gearbox name was hardcoded in the HTML while every ratio was read live
from `Vehicle`; it now comes from the same place. The gear strip was built
from a literal 8 and now follows the ratio count, so a gearbox correction
cannot leave the strip showing eight cells for a seven-speed.

### Verification

| check | result |
|---|---|
| `node --test "static/sim/*.test.mjs"` | **30 of 30** |
| `python -m app.test_simulation` | **15 of 15** |
| `python -m app.test_replay` | **49 of 49** |
| `python verify_docs.py` | 1 of 67 failed — the same pre-existing `FULL_RUN.txt` pair, unchanged |

Still not done: no automated browser check. The layout and the night were
judged from the user's screenshots, not from a test.

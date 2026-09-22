# `app/` — the live supervisor and the 3D replay lab

Two things live here and they share the same physics.

| page | what it is | vehicle connection |
|---|---|---|
| `/` and `/driver` | the live supervisor: the project's plant running beside the car | live OBD-II, **read-only** |
| `/review` | what the supervisor marked during a drive | none |
| `/simulation` | **the 3D replay lab** — recorded drives, rendered | **none, ever** |

Everything below is about `/simulation`. For the supervisor read
`CLAUDE.md` and `AUDIT.md` first.

**The project never writes to the vehicle's ECU.** `app/test_replay.py`
asserts that no write path exists and that no raw car data reaches the disk.
Breaking either fails a check rather than going unnoticed.

---

## Run it

From the **repository root**, not from `app/`.

```powershell
powershell -ExecutionPolicy Bypass -File app\start-simulation.ps1
```

Then open <http://localhost:8000/simulation>.

The script vendors Three.js on the first run and then starts the server.
If you would rather do it by hand:

```bash
python -m pip install -r app/requirements-replay.txt   # no obd, no serial port
cd app && npm install && npm run vendor && cd ..       # copies Three.js locally
python -m app.server --simulation --http-port 8000
```

`npm` is needed **once**, only to copy Three.js out of `node_modules` into
`app/static/vendor/`. After that the lab is offline: it never loads a CDN.
If `app/static/vendor/three/three.module.js` already exists, skip npm entirely.

### The first drive takes a while, and that is the physics

Picking a drive does not just read a file. It runs `plant.predict` and
`thermal.ThermalNetwork` over **every sample, at the recording's own
timestamps**, exactly as the live supervisor does. Measured on 21 September:
**74 to 79 rows per second**, so a one-minute recording is ready in seconds
and the two-hour Taif drive takes several minutes. The progress bar is real.

Picking a different drive **cancels** the one being computed, so a mis-click
costs a second, not the whole build.

---

## What it shows, and where each number comes from

No engine physics runs in JavaScript. The browser selects an already-computed
sample and displays it. The one thing it does compute is **position**: it
integrates the recorded road speed between two samples so the car slides
smoothly instead of jumping, and that integral is what the odometer and the
preview distance show. Nothing thermal, chemical or mechanical is computed in
the browser, and the displayed telemetry is never blended between samples.

```
logs/raw/*.csv  ->  app/reader.py  ->  app/estimator.py  ->  app/replay.py  ->  JSON
                     (the same path the live supervisor uses)                     |
                                                                                  v
                             app/static/sim/main.mjs  ->  scene.mjs / panel.mjs
```

Every channel is labelled at the point it is displayed:

| dot | meaning |
|---|---|
| **مسجّلة** | read from the car's own log |
| **مقدّرة** | produced by this project's model |
| **غير متاحة** | the recording does not carry it — shown as `—`, never guessed |

### The gearbox

Eight forward gears, read live from `engine_env.Vehicle` — the ratios are
never written into the page:

```
final_drive = 3.150
gears = (5.250, 3.360, 2.172, 1.720, 1.316, 1.000, 0.822, 0.640)
```

`Actual gear` in the logs **saturates at 6** (CLAUDE.md mistake 18), so the
lab does not trust it blindly:

1. If the recorded gear is 1–6 **and** agrees with the ratio measured from
   engine speed and road speed, it is shown as **مسجّل**.
2. Otherwise the gear is inferred from that ratio against the eight published
   ones and shown as **مقدّر**, with the method named underneath.
3. When no ratio matches within 4 %, it shows **غير محسوم** and lights no
   cell. Converter slip is not a gear.
4. Below 15 km/h the ratio is meaningless, so nothing is inferred there. A
   recorded gear of 1–5 is still shown, marked **مسجّل** and captioned as
   unverified; anything else shows **غير محسوم**.

There is no manual gear control, because the replay has nothing to control.
Shift marks on the timeline sit between two samples; they are not exact
mechanical shift instants.

### H and τ

`H` is the preview horizon, chosen from `engine_env.PREVIEW_S`. `τ` is the
turbine housing's thermal time constant **at the current operating point**,
taken from the estimator rather than assumed — it moves with exhaust flow, so
it is short under load and long at idle.

`H/τ` is displayed as a live reading of this recording. It is **not** an
experimental result and not evidence that preview is worth anything. The
project's criterion is tested in Phase D, not here.

### Dark mode and English

Two quiet buttons in the top bar. Both are presentation only: switching theme
or language never changes a value, a limit or a computed frame, and a test
asserts the gear reading is identical in both languages.

The choice is kept in `localStorage` and applied before first paint, so a dark
reader never sees a light flash. With nothing stored the page follows the
operating system's `prefers-color-scheme`. Every string lives in
`static/sim/i18n.mjs`, Arabic and English, with the same keys in both — a test
fails if a key exists in one language and not the other, and another test
asserts that each honesty caveat survives translation, because a caveat lost
in translation is the failure this project punishes hardest.

### The turbine threshold highlight

The lab marks when the **estimated** housing temperature reaches the alert
threshold the app carries, or is heading for it. There are two signals and the
second is the useful one:

1. **Value band.** Within 50 K of the threshold, or at/above it. Measured
   across the shipped drives, only one crosses it, and the next hottest — the
   two-hour Taif run — peaks about 52 K short and so falls just *outside* the
   band. That is reported rather than tuned away: widening the band until a
   drive lights up would be choosing a threshold to produce an indication.
2. **Where it is heading.** The housing is a first-order node, so it can read
   far below the limit while climbing towards a steady state above it. When
   the steady state implied by the *current* operating point sits at or above
   the threshold, the state reads "approaching" whatever the present value is.
   That number is the estimator's own fixed point — not a trend extrapolation,
   which `AUDIT.md` M10 records as wrong on this node.

The difference is not academic. On `670063b2` the housing peaks about 70 K
below the threshold, so the value band alone says nothing for the whole drive,
while the steady state the driving implies goes far above it — and the second
signal fires. The timeline shows any spans that actually sat at or above the
threshold, with the total time and its share of the drive.

**Both caveats travel with the highlight, on screen:** the threshold is one
*this project chose*, not a manufacturer rating, and the temperature compared
against it is a model output whose heat capacity is assumed.

### The road

The road is a **decorative loop of about 4.6 km**. No recording in
`logs/raw/` carries road grade, GPS or altitude, so `grade_pct` is `null` on
every frame and the page says it is unavailable. The slope you see is not the
slope the car drove, it feeds nothing, and the caption names the lap number
and the loop length so a long drive visibly goes round the same hill instead
of appearing to climb a real route.

The loop is short because the viewing scale is set for **legible speed**, not
for map accuracy: one world unit stands for 35 replay metres. At the 90 that
shipped first, a 60 km/h cruise and a 164 km/h pull both crawled across the
view (292 s against 107 s) and looked identical. The scale enters no
calculation — distance is integrated from recorded speed in metres, and only
the final step divides by it to place the car — and a test pins the speeds
apart so nobody quietly restores the old value.

---

## Limits to state, not to hide

- **The turbine temperature is a model output, not a reading.** Its heat
  capacity `c_turb` is marked ASSUMED in `thermal.py` and in `REFERENCES.md`
  section 4, and it is the constant that sets τ. A number on a screen looks
  like a measurement to everyone who did not write it.
- **Early in a drive the estimate is mostly assumption.** The lab starts from
  a bracketed seed and shows the band while it is wide (mistake 15). On a
  short recording that covers much of the drive. The warning is per sample —
  believe the band, not the headline.
- **No controller comparison exists.** `comparison_available` is `false` in
  the payload and the UI has no panel for it. Phase D has not produced a
  result on the current plant, so there is nothing honest to draw.
- **The preview ribbon is not a controller.** It is the distance the car
  actually covered in the next H seconds of the recording. It says nothing
  about anticipation.
- **One recording never moves.** `3f64372e` carries a `Vehicle speed` column
  that reads zero on every row; the catalog marks it `has_motion: false` and
  the car correctly stays put.
- **Shift marks come from sampled changes**, and the logger polls one channel
  per row, so two channels in one frame were not measured at the same instant.
- **No geographic route is drawn**, because none was recorded.

---

## Tests

Run all three after touching anything under `app/`.

```bash
python -m app.test_simulation          # replay adapter, gear inference, page assets
cd app && node --test "static/sim/*.test.mjs" && cd ..   # clock, sampling, panels
python -m app.test_replay              # the original supervisor regression suite
```

`test_simulation` includes a check that every module, stylesheet, icon and DOM
id the page references actually exists. That check was written because the
page shipped for a day pointing at a `main.mjs` that was never created: both
suites passed, the route returned 200, and the browser silently 404'd one file.

---

## Files

```
replay.py            builds immutable frames from one CSV. Cancellable, in
                     memory only, nothing cached to disk.
static/simulation.html   the Arabic RTL shell. Carries no figures of its own.
static/sim/main.mjs      the only file that touches the DOM.
static/sim/panel.mjs     pure presentation logic — gear labels, H/tau, chart
                         paths. No DOM, no physics, so it is unit tested.
static/sim/playback.mjs  the presentation clock. Display rate never changes
                         which sample a given trip time selects.
static/sim/scene.mjs     the two Three.js scenes: the world and the engine.
static/sim/geometry.mjs  the decorative road loop, arc-length parameterised.
vendor.mjs               copies Three.js into static/vendor for offline use.
```

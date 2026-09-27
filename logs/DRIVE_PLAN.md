# Drives we need — what to log, and how to drive it

Written 27 September 2026, from what the simulator-versus-car comparison
(`model_vs_data.py`) could not settle. Three drives, in order of value. Each
answers one question the existing logs cannot. None of them is needed to run
Phase D, which is simulation; they make the simulator it runs on more
trustworthy.

**Read-only, always.** BimmerLink logs; nothing is ever written to the car.
Passenger runs the phone, driver drives. Every instruction below is to be
done only where it is legal and the road is clear — if a step cannot be done
safely, skip it; a missing pull costs less than anything else.

---

## Before every drive

1. **Select ONLY the channels listed for that drive.** Fewer channels means each
   one is read more often: 7 channels refresh every 1.45 s, 26 every 7.5 s
   (CLAUDE.md mistake 13b). The speed is the whole point.
2. **Always include `Coolant temperature`.** `build_dataset.py` keeps only warm
   samples, and a drive without the coolant channel contributes nothing —
   that is what happened to `pull01`.
3. **Warm the engine first** (coolant at 88 °C or above), then start the log.
4. **Wait 30 seconds after starting the log before driving.** The first rows
   are placeholder zeros until the car answers (AUDIT.md M8).
5. After the drive: export the CSV, copy it into `logs/raw/` with a name that
   says what it is (`climb_thermal-20261004.csv`), then run

   ```
   python new_drive.py logs/raw/<file>.csv        # what did this drive buy?
   python build_dataset.py "logs/raw/*.csv"       # then CLAUDE.md's routine
   python model_vs_data.py                        # re-score the simulator
   ```

---

## Drive 1 — a long mountain climb, for heat (most valuable)

**Why.** The car has never been logged under sustained load. Only 1.8 % of the
logged moving samples reach the manifold pressure of the locked climb — the
logs are fast flat-road cruising. So the thermal model has never been checked
in the region the whole experiment runs in. This drive gives:

- the **oil node's** real response to sustained load. On hard pulls the model's
  oil spikes to 140 °C where the sump reads 107 °C; its fuel-to-oil heat share
  (5 %) and oil heat capacity are ASSUMED numbers that this drive can measure,
  using the logged coolant as the boundary so the unidentifiable radiator
  stays out of the fit;
- the first **sustained-load coolant** data, and — if the climb is long and hot
  enough to push coolant past 100 °C — the **radiator**, which CLAUDE.md says
  can only be identified by a drive that overwhelms the cooling system;
- a **hot idle**, which tests the model's stand-in thermostat against the
  B58's heat-management valve (on drive10 the model cooled 13 K at a four-minute
  idle while the car held 93 °C).

**Channels (8):**

| channel | why |
|---|---|
| `Engine speed` | operating point |
| `Vehicle speed` | road load, gear inference |
| `Air mass flow` | load, and fuel flow with lambda |
| `Lambda actual value` | fuel flow = air / (14.7 λ) |
| `Coolant temperature` | the block node's boundary — and the warm filter |
| `Oil temperature` | the node being identified |
| `Engine radiator outlet temperature (coolant)` | radiator cold side |
| `Ambient temperature` | every heat flow's boundary |

**How to drive.**

1. Pick the longest continuous climb within reach — an escarpment road up
   from the coast is ideal. 15–25 minutes of climbing without stopping.
2. Afternoon, when it is hottest. Hotter air is closer to the 42 °C the
   scenario assumes.
3. Warm up on the way. Start the log at the foot of the climb.
4. Climb at a steady, legal speed in **D**. Don't lift off unless you must;
   sustained load is the point, not speed.
5. **At the top, pull over somewhere safe and leave the engine running at idle
   for 5 minutes** with the log still going. Do not switch off — the hot idle is
   half the value of the drive.
6. Stop the log.

---

## Drive 2 — full-throttle roll-ons in a high gear, for low-rpm boost

**Why.** The simulator's boost ceiling is "what the car was seen to do", and on
flat roads the car was never asked for boost at low engine speed. So the model
can only make 333 Nm at 2100 rpm, while a B58 is rated for far more there. To
keep the training roads drivable, the simulated gearbox now kicks down when the
engine falls short — a workaround, stated as one in `engine_env.py`. This drive
measures what boost the car actually makes at low rpm, which would let the
ceiling be refitted and the workaround retired.

**Channels (7):**

| channel | why |
|---|---|
| `Engine speed` | the speed the boost is reached at |
| `Vehicle speed` | gear, and acceleration as a torque check |
| `Air mass flow` | corrected flow — the ceiling's x-axis |
| `Boost pressure` | at full throttle this IS manifold pressure (mistake 14) |
| `Ambient pressure` | pressure ratio |
| `Throttle valve angle related to the lower stop` | proves the pull was full throttle |
| `Coolant temperature` | warm filter |

**How to drive.** A straight, empty multi-lane road with a 120 km/h limit or
higher, engine warm.

1. Put the gearbox in **manual mode (M)** and use the paddles to hold the gear.
2. For each row: settle at the start speed, then **floor it for 3–4 seconds and
   lift**, always before the speed limit.

   | gear | start at | engine speed there |
   |---|---|---|
   | 6th | 70 km/h | about 1770 rpm |
   | 7th | 90 km/h | about 1870 rpm |
   | 8th | 100 km/h | about 1620 rpm |

3. Do each row **three times**, with **a minute of steady cruising** between
   pulls. The logger reads one channel at a time, so the pause is what turns
   rows into independent readings (AUDIT.md H4).
4. If the gearbox kicks down anyway in M mode, keep going — that is the car
   telling us the same thing the model's workaround assumes.

---

## Drive 3 — loaded, steady-gear driving in the heat, for knock

**Why.** The model's knock integral has **no detectable relationship** with the
retard the car applies (correlation −0.12 over 14 318 samples on 7475b5d7).
CLAUDE.md: *settling it needs a deliberate drive.* The retard is target minus
actual ignition angle, and it can only be read cleanly when both are sampled
fast and the gear is not changing (a gearshift torque cut looks like 45° of
retard).

**Channels (8):**

| channel | why |
|---|---|
| `Engine speed` | operating point |
| `Vehicle speed` | gear inference (the `Actual gear` channel clamps at 6 — mistake 18) |
| `Air mass flow` | load |
| `Actual ignition angle` | what the car fired |
| `Target ignition angle from torque intervention` | target minus actual = retard |
| `Lambda actual value` | the model needs it at each sample |
| `Coolant temperature` | warm filter |
| `Ambient temperature` | knock depends on it |

**How to drive.** The same climb as drive 1 works — a second ascent with this
channel set — in the afternoon heat.

1. **Manual mode (M).** Choose a gear that keeps the engine at **2000–3500 rpm**
   on the climb — low speed and high load is where an engine knocks.
2. Hold **steady throttle for 20–30 seconds at a time**, firm but not
   necessarily full. No gear changes inside a segment.
3. Ten or more segments. Ease off between them.

---

## What no drive on this car can settle

- **The turbine temperature and the 850 °C trigger.** Every pre-catalyst exhaust
  temperature channel reads zero on every sample; the only live one is modelled
  and post-catalyst. It needs a published source, not a drive.
- **Enrichment at 4500–7000 rpm with long dwell**, the weakest enrichment cell.
  It needs 4–12 seconds of full load at high engine speed, which is not legal
  road driving in any gear. A track day could do it; a public road cannot.
- **A real boost leak** for the app's mismatch detector. Inducing one on a
  borrowed car is not something to do.

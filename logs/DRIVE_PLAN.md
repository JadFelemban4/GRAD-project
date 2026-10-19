# Drives we need — what to log, and how to drive it

Written 27 September 2026 and revised 28 September, from what the
simulator-versus-car comparison (`model_vs_data.py`) could not settle;
**revised 13 October, after X1 and X2** (the first box below). Four drives:
**C, A, D, and B (done)**, in the order they are now needed. Each answers one
question the existing logs cannot. None of them is needed to run an experiment,
which is simulation; they make the simulator it runs on more trustworthy, and C
decides what the next training charges for knock.

*(Lettered, not numbered, on purpose: `DRIVE_1_card_v1.md` and `v2` are the
**completed** first drive of 6 September, kept as a record. These are new.)*

**What each drive would change, and when.** A and D change the plant: A the oil
and coolant constants `derive_params.py` derives from the logs, D the boost
ceiling (and the thin-air inlet, if training keeps thin air). The team retrains
after every drive. C changes no fitted parameter; it decides whether the knock
term, and the one-step knock spike behind most of it, stay in the next
training's plant and reward, so **C comes before the next training**.

> **13 October 2026: WHAT X1 AND X2 CHANGED, AND THE ORDER NOW.**
>
> 1. **Drive C first, with a new part.** Since X1 the agents may not advance
>    spark, but the knock term still decides what they do. It is the baseline
>    car's largest damage term in ordinary driving: on the cool stretches of the
>    car's own drives, 0.060 a second of knock against 0.010 of oil and 0.0001
>    of turbine. X1's and X2's agents burn 4–7 % more fuel than the baseline ECU
>    on those drives (median, life weighted most), mostly to avoid it. That knock
>    comes from a **one-step spike at every sudden rise in torque demand**,
>    because the model's baseline ECU sets spark from the previous second's
>    load: on the car's drives 84 % of it (all but each replay's first step)
>    falls on such rises, and in X2's training about 85 % falls where a speed-up
>    starts or a slow-down ends (`results/X2_AGENTS.md`, section 5). **Whether
>    the real car pulls timing on a sudden load step decides whether that is
>    protection or a model artefact.** Drive C adds those steps (part C2) to its
>    steady loaded segments (part C1), and carries a draft decision rule to be
>    fixed before it is driven.
> 2. **Drive A second**, for the reasons below, plus one: the coolant constants
>    are weakly identified (stepping the fit's integrator finer moved the
>    radiator scale by +61 %, CLAUDE.md mistake 25), and sustained load is the
>    data that pins them. It now logs `Ambient pressure` too.
> 3. **Drive D, new:** drive B's roll-ons again, held longer, repeated on the
>    plateau at the top of drive A's climb, and logging the car's own torque
>    request. It measures (a) the boost the car makes at 1600–2000 rpm when held
>    long enough to count (the model's ceiling is 9–20 % low there, mistake 22);
>    (b) the boost in thin air, which nothing has measured: X2 trained down to
>    80 kPa and its transfer test goes to 76 kPa on a compressor inlet scaled
>    from sea level, and drive10, the only drive at altitude, logged no ambient
>    pressure (every other drive with that channel was logged on the coast,
>    14.1–14.5 psi in the raw logs); (c) how fast the car's own torque request
>    rises when the pedal goes down: the model's demand jumps in one step, which
>    is what makes the spike, and a ramped demand would need the car's rate.
> 4. **Not reachable now:** air colder than 19.0 °C, the coldest in the dataset
>    (`data/master_samples.csv`, drive10 at altitude), while X2 trained down to
>    0 °C. Only a winter night at altitude comes close.
>
> | drive | question | channels | changes the plant? | when |
> |---|---|---|---|---|
> | **C** knock | does the car retard on sudden load steps, and under sustained load? | 6 | the knock term and the ECU's spark lag, by the decision rule | **before the next training** |
> | **A** heat | oil, coolant and radiator under sustained load; the valve's control law | 9 | yes: the derived thermal constants | next |
> | **D** boost and torque request | boost at low rpm and in thin air; how fast the torque request rises | 8 | yes: the boost ceiling, and thin air if kept | the same trip as A |
> | B | boost at low rpm | 7 | done 28 September | — |

> **28 September 2026, evening: DRIVE B IS DONE** —
> `logs/raw/driveB_rollons-20260928_140513.csv`, 41 full-throttle roll-ons in a
> held 6th/7th/8th. What it bought and what it could not: the evening session
> report, section 1. **One lesson for every drive below: log `Ambient
> temperature`.** Drive B's list left it out, so its corrected flow and charge
> temperature rest on an ambient borrowed from other drives
> (`build_dataset.AMB_FALLBACK_C`), and the charge-temperature check has to
> exclude it. It is now on every list below. **Drive A is the most valuable
> drive left**: `validate.py` rows 8 and 9 (the oil) and the coolant regulation
> law all need sustained load logged with oil and ambient.

> **29 September 2026: DRIVE C MOVES UP.** The retrained agents advance spark
> to just under the knock model's knee, and with that advance forbidden their
> median damage cut falls from ~68 % to ~42 %, below the hand-written
> current-grade policy (`knock_margin.py`, `results/agents/terrain_dt1/
> KNOCK_MARGIN.md`). Whether the car tolerates that spark is exactly what drive
> C measures, so **for Phase D's claim drive C is now the most valuable drive**;
> drive A stays the most valuable for the thermal model. The team retrains the
> agents after every drive.

**Read-only, always.** BimmerLink logs; nothing is ever written to the car.
Passenger runs the phone, driver drives. Every instruction below is to be
done only where it is legal and the road is clear — if a step cannot be done
safely, skip it; a missing pull costs less than anything else.

---

## Before every drive

1. **Select ONLY the channels listed for that drive or part.** Fewer channels
   means each one is read more often: each channel is read about every
   0.15–0.21 s times the number selected (7 channels: every 1.05 s on drive B,
   every 1.45 s on `pull01`; 26 channels: every 7.5 s; CLAUDE.md mistake 13b).
   The speed is the whole point.
2. **Always include `Coolant temperature`.** `build_dataset.py` keeps only warm
   samples, and a drive without the coolant channel contributes nothing —
   that is what happened to `pull01`.
3. **Warm the engine first** (coolant at 88 °C or above), then start the log.
4. **Wait 30 seconds after starting the log before driving.** The first rows
   are placeholder zeros until the car answers (AUDIT.md M8).
5. **One log per part.** When the channel set changes, stop the log and start a
   new one, and name each file for its part (`driveC2_steps-20261020.csv`).
6. After the drive: export the CSV, copy it into `logs/raw/` with a name that
   says what it is (`climb_thermal-20261004.csv`), then run

   ```
   python new_drive.py logs/raw/<file>.csv        # what did this drive buy?
   python build_dataset.py "logs/raw/*.csv"       # then CLAUDE.md's routine
   python model_vs_data.py                        # re-score the simulator
   ```

   **Except drive C** (19 October): its CSVs stay out of `logs/raw/`, and
   `build_dataset.py`, `full_run.py` and `car_spark_boost.py` are not run on
   them, until its decision rule's analysis has run (`results/DRIVE_C_RULE.md`,
   section 1). `new_drive.py` is safe on them: it withholds the retard unless
   given `--unblind`.

---

## Drive C — knock: sustained load and sudden load steps (do this first)

> **19 October 2026: DRIVEN ONCE, TO BE REPEATED.** Ghassan drove it on 18–19
> October. The logging was right (drive C's six channels, each read about every
> 0.9 s), but the driving covered neither part: one load step matched C2, no
> segment reached the climb's cell, and it ran after midnight at 17.5–31.5 °C
> (Jad's side's check, `drive_c_check.py`). **The decision rule is agreed**
> (19 October, Jad and Ghassan: decisions 14–23 in `results/VALIDATION_DECISIONS.md`;
> the rule is `results/DRIVE_C_RULE.md`), from research that read no drive C log.
> **Drive again once the rule's analysis script is committed.** The instructions
> below match the rule; nobody computes the retard on the 18–19 October files
> before that script's stage C.

**Why.** The model's knock integral shows **no detectable relationship** with
the retard the car applies (correlation −0.12 over 14 318 rows of 7475b5d7).
**But that drive could not have seen it** (28 September): logged with 26
channels, it holds only about 400 genuine readings of each ignition angle in
55 minutes — one every ~8 s — and a third of the target/actual pairs in a row
were read more than a second apart. A knock retard lasts a second or two. *(Corrected
19 October: Bosch's documented setting is a 3° step per knock event recovered
0.75° at a time at about 4 s per degree, so a single event lasts about 12 s;
faster, 1–2 s per degree, only after a load-range change. The conclusion stands:
8 s sampling still cannot resolve its onset.)* The
test so far is not a refutation; it is a test this sampling cannot perform —
mistake 13b's trap again, where a real relationship read +0.35 until faster
logging showed +0.95.

**What it now decides** (13 October):

- **The one-step knock spike (part C2).** Does the car pull timing when the
  load rises suddenly? The model's baseline ECU does, for one step, at every
  rise in torque demand, and that spike is what X1's and X2's agents spend fuel
  avoiding on the car's own drives (the box above).
- **The knock knee (part C1).** The 0.85 in the damage formula waits for the
  knock integral at which the car's own ECU starts to retard
  (`results/DAMAGE_CONSTANTS.md`).
- **Spark under boost (part C1).** The car runs a median 3.8° below the model's
  spark at 2000–4000 rpm and 140–240 kPa, but on 31 genuine readings, and on 4
  in the climb's own cell (2400–3000 rpm, 165–185 kPa); read linearly that is
  about +29 K of turbine the model would be missing, and by the validation
  plan's rule it is untested (`results/VALIDATION_PLAN.md`, the spark row).
  Part C1 is meant to put hundreds of readings in that cell.

So this drive logs **as few channels as possible**, to read both angles about
every 0.9–1.25 s:

**Channels (6):**

| channel | why |
|---|---|
| `Engine speed` | operating point |
| `Air mass flow` | load; and the marker of each load step in C2 |
| `Actual ignition angle` | what the car fired |
| `Target ignition angle from torque intervention` | target minus actual = retard |
| `Coolant temperature` | warm filter |
| `Ambient temperature` | knock depends on it |

`Vehicle speed` and `Lambda actual value` are left out on purpose: in a held
gear the gear does not need inferring, and below 3300 rpm this engine does not
enrich, so lambda is 1.0.

**Select the channels in exactly the order of the table** (19 October): the
target angle is then polled right after the actual, which the rule's pairing
needs (`results/DRIVE_C_RULE.md`, V8).

**How to drive.** Gearbox in **manual mode (M)** throughout. No gear changes
inside a segment or a step. Do C2 before C1, or write down the order. Write down
the fuel grade and fill, and the drive mode.

*Part C1 — steady loaded segments, on a climb, in the warmest hours you can get.*

1. The same climb as drive A works — a second ascent with this channel set.
2. Choose a gear that keeps the engine at **2000–3500 rpm** — low speed and high
   load is where an engine knocks. The locked climb's own point is 2706 rpm at
   175 kPa, where the baseline ECU breathes about 400 kg/h of air (its record on
   the locked climb, median 113 g/s): on the passenger's screen, `Engine speed`
   near 2700 and `Air mass flow` near 400. Let most segments pass through it.
3. Hold **firm throttle, near full, for 20–30 seconds at a time**. On most roads
   the car will gain speed at that load: lift before the limit, and ease off
   between segments.
4. **25–30 segments** (revised 19 October from twenty), at least 20 of them held
   in the cell near 2700 rpm (at 25 °C, 165–185 kPa is about 350–400 kg/h at
   2400 rpm and 450–510 kg/h at 3000 rpm), the rest near full throttle at
   2000–3300 rpm for the knee. The spark verdict needs at least 15 segments with
   5 readings in the cell each.

*Part C2 — sudden load steps, on a straight, empty road, in the warmest hours,
on the coast.* *(New, 13 October; revised 19 October to match the rule.)*

1. **35 steps in 5 blocks of 7.** Each block is one gear on its own stretch, and
   the blocks are at least 5 minutes apart (steps driven with no break count as
   one block and need far stricter cuts). About 20 full-pedal and 15 half-pedal
   steps.
2. Before each step, **a full steady minute of light cruise** in a held gear:
   **press every 75–90 s**, start to start. A press every 60 s still works, but
   then the sham window after each step falls in the next step's baseline and is
   lost; at 75 s or more every step also yields one sham (the analysis script on
   synthetic logs: 60–61 valid shams at 60–67 s, 91–94 at 75–95 s; 24 needed).
   Then press the pedal firmly and quickly from the cruise position, without
   lifting first, and **hold it 7 s where legal (5 s at least)**, then back to the
   same cruise. Always before the limit.
   - **Full pedal** only from 1500–2000 rpm in 6th, 1500–1800 in 7th, 1500–1600
     in 8th: on drive B's rates these end at or below about 116 km/h after 5 s.
   - **Half pedal** in 6th or 7th at 2000–2500 rpm (in the model, half steps
     lower or in 8th barely spike, so they would not count).
   - Full pedal below 2000 rpm is the low-speed pre-ignition region of a
     downsized turbo engine; worth knowing.
3. **8–10 minutes of step-free steady cruise** as well, anywhere in the C2 file:
   the sham windows that measure the channel's jitter on the day.
4. A cool-morning session is optional now: the rule's verdict covers only the
   ambient range driven, either way.

**Decision rule — AGREED 19 October by Jad and Ghassan**
(`results/DRIVE_C_RULE.md`, decisions 14–23 in `results/VALIDATION_DECISIONS.md`;
every number printed by `python drive_c_rule_numbers.py`). It replaces the draft
of 13 October, whose placeholders were: a step = air mass +50 % between two
readings; the 3 s after against the 20 s before; a pull = more than 2°;
"does not" under 1 step in 5, "does" over half.

- **C2:** a step is air above 1.2× its 20-s median reaching 1.5× and holding,
  from a steady light cruise, counted only where the model's own spike exceeds
  KI 1.0. **Only the late window decides** (1–5 s after, ending 0.6 s before the
  release); a step pulls if it rises **≥ 2.25°** (3 counts). At 24 valid steps:
  **pulls if ≥ 6** (and more often than sham windows), **does not if ≤ 3**,
  4–5 inconclusive; at least 16 valid steps. Half against full pedal is a
  non-binding secondary; the verdict covers only the ambient driven.
- **What it triggers:** "does not", or "pulls" no more often than steady C1
  running at the same load → schedule the baseline's spark on the current load.
  "Pulls" and step-specific → keep a load-step knock cost sized with C1's knee.
- **C1:** retune the damage knee only if the measured onset is more than
  max(0.10 KI, 2·u_val) from 0.85 (at least 8 confirmed onsets); retune the
  boosted spark schedule only if it is off by more than max(0.85°, 2·u_val)
  (at least 15 segments). 0.85° departs from the validation plan's 1.3°: it is
  the schedule error that moves every car by 10 K, R1's own basis.

---

## Drive A — a long mountain climb, for heat

**Why.** The car has never been logged under sustained load. Only 2.77 % of the
logged moving samples reach the manifold pressure of the locked climb, and
those in short pulls (`model_vs_data.py`, the duty cycle; corrected 13 October,
it quoted a smaller share from before the dataset grew) — the logs are fast
flat-road cruising. So the thermal model has never been checked
in the region the whole experiment runs in. This drive gives:

- the **oil node's** real response to sustained load. On hard pulls the model's
  oil spikes to 140 °C where the sump reads 107 °C; its fuel-to-oil heat share
  (5 %) and oil heat capacity are ASSUMED numbers. **The logs we have cannot
  fix them** (28 September, `model_vs_data.py`): fitted on the three light-load
  calibration drives they fix the pulls but take drive10 — the only drive in
  the published band — from 116 to 102 °C against the car's 117. The drives
  disagree, and only sustained load can say which way. **One constraint the
  logs do already give:** the car's oil takes 70–100 s to follow a change and
  the model's takes 14 s (`validate.py` row 9), so whatever this drive fits
  must reproduce that too;
- the first **sustained-load coolant** data, and — if the climb is long and hot
  enough to push coolant past 100 °C — the **radiator**, which CLAUDE.md says
  can only be identified by a drive that overwhelms the cooling system. Since
  9 October there is a second reason: re-fitted with the plant's own
  sub-steps, the radiator scale moves +61 % and block-to-ambient −42 %
  (`substep_fit_check.py`, CLAUDE.md mistake 25), so the logs we have barely
  pin the coolant constants;
- a **hot idle**, which tests the model's stand-in thermostat against the
  B58's heat-management valve (on drive10 the model cooled 13 K at a four-minute
  idle while the car held 93 °C).

It will not hold the locked climb's load: a mountain road at legal speed asks
40–50 kW (drive10) against the climb's 88.7 kW. It is the longest sustained load
a road can give.

**Channels (9):**

| channel | why |
|---|---|
| `Engine speed` | operating point |
| `Vehicle speed` | road load, gear inference |
| `Air mass flow` | load, and fuel flow with lambda |
| `Lambda actual value` | fuel flow = air / (14.7 λ) |
| `Coolant temperature` | the block node's boundary — and the warm filter |
| `Oil temperature` | the node being identified |
| `Engine radiator outlet temperature (coolant)` | radiator cold side |
| `Ambient temperature` | every heat flow's boundary -- and without it the thermal fit cannot use the drive at all (`calibrate_thermal.usable_drives`) |
| `Ambient pressure` | ADDED 13 October: the air the engine breathes as the road climbs, which no log has recorded above the coast. It changes slowly, so it costs the thermal channels nothing they need (each is read about every 1.35–1.9 s; the oil follows a change over 70–100 s) |

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
6. Stop the log. Then, on the plateau, drive D's part D2 before coming down.

---

## Drive D — boost and the car's own torque request, at sea level and in thin air (new, 13 October)

**Why.** Three questions, one channel set:

- **Boost at 1600–2000 rpm, held long enough to count.** The model's boost
  ceiling is the measured envelope, and it sits 9–20 % below the highest boost
  drive B reached at 1600–2000 rpm (CLAUDE.md mistake 22). Drive B's 3–4 s pulls
  are transients, which the envelope (built from quasi-steady rows) excludes by
  construction. Longer pulls, best uphill, give readings it can use.
- **Boost in thin air.** X2 trained at 80–101.3 kPa and its transfer test runs
  at 90, 82 and 76 kPa, all on a compressor inlet scaled from sea level
  (`wide_air.py`, the conditions test's model). No log has recorded the car above
  the coast: drive10 climbed to Taif without an ambient-pressure channel. The
  plateau at the top of drive A's climb is about the transfer test's 82 kPa
  "about Taif" condition. This part matters if the next design keeps thin air in
  training, or keeps the transfer test's pressure conditions.
- **How fast the car's torque request rises.** The model's torque demand jumps
  in a single 1 s step when a speed-up starts, and that jump is what makes the
  one-step knock spike. If drive C says the spike must go, one way out is to ramp
  the demand; the car's own request gives the rate. `Coordinated target torque
  on the wheel` is live (7475b5d7 holds 273 distinct values of it, −37 to
  2 921 Nm at the wheel), but that drive logged 26 channels, so each was read
  only about every 8 s, far too slowly to see a tip-in.

**Channels (8):**

| channel | why |
|---|---|
| `Engine speed` | the speed the boost is reached at |
| `Air mass flow` | corrected flow — the ceiling's x-axis |
| `Boost pressure` | at full throttle this IS manifold pressure (mistake 14) |
| `Ambient pressure` | the pressure ratio, and the thin air itself |
| `Throttle valve angle related to the lower stop` | proves the pull was full throttle, and marks when each step began |
| `Coordinated target torque on the wheel` | the car's own torque request |
| `Coolant temperature` | warm filter |
| `Ambient temperature` | corrected flow and charge temperature |

Each is read about every 1.2–1.7 s. `Vehicle speed` is left out: the gear is
held in M, and a kickdown shows as a jump in engine speed. The pedal channels
(`Target wheel torque from accelerator pedal request`, `Normalized accelerator
pedal angle`) were read only 2–8 times in the census log, too few to say whether
they are useful, so they are not on the list.

**How to drive.** Gearbox in **manual mode (M)**; hold the gear with the paddles.

*Part D1 — at sea level, on a straight, empty road (or a long gentle climb) where
it is legal.*

1. Drive B's rows: **6th from 70 km/h** (about 1770 rpm), **7th from 90 km/h**
   (about 1870 rpm), **8th from 100 km/h** (about 1620 rpm). Floor it and **hold
   for as long as the limit allows — 6–8 seconds if you can — then lift**.
   Uphill is best: the grade takes the load, so the car gains less speed in the
   same time.
2. Each row **three times**, with **a minute of steady cruising** between pulls.
3. Then **five moderate tip-ins**: from steady cruise, about half pedal for
   3 seconds, a minute apart. They show how the car shapes an ordinary
   acceleration, which is what the model's speed-ups are.

*Part D2 — on the plateau at the top of drive A's climb.*

1. The same three full-throttle rows, three times each, a minute apart, on a
   straight road where it is legal and empty.
2. If no such road is safe, skip D2: D1 still answers two of the three
   questions.

---

## Drive B — full-throttle roll-ons in a high gear, for low-rpm boost — DONE 28 September

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
| `Ambient temperature` | ADDED 28 Sep: corrected flow and charge temperature need it; the drive as logged did not have it |

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

## What no drive on this car can settle

- **The turbine temperature and the 850 °C trigger.** Every pre-catalyst exhaust
  temperature channel reads zero on every sample; the only live one is modelled
  and post-catalyst. It needs a published source, not a drive.
- **Enrichment at 4500–7000 rpm with long dwell**, the weakest enrichment cell.
  It needs 4–12 seconds of full load at high engine speed, which is not legal
  road driving in any gear. A track day could do it; a public road cannot.
- **A real boost leak** for the app's mismatch detector. Inducing one on a
  borrowed car is not something to do.
- **The locked climb itself** (added 13 October). It holds 88.7 kW for twelve
  minutes in sea-level air; no legal road does (drive10's Taif climb asks
  40–50 kW and never reached the trigger). Every result on it is an
  extrapolation in duration (`results/VALIDATION_PLAN.md`, operating region).
- **Air colder than about 19 °C** (added 13 October), which X2 trained in down
  to 0 °C. Not a drive this season; only a winter night at altitude comes near.

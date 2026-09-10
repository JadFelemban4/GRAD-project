> **COMPLETED — all four questions answered. Kept as the record; do not re-drive.**
>
> Drive 1 and six more have been logged: **113 minutes across seven drives**.
> The four checks at the bottom of this card came back as follows.
>
> **1. The pressure channel — settled, and it was not what the label says.**
> `Intake manifold absolute pressure` reads **13.49 psi at warm idle against an
> ambient of 14.23**, where a throttled engine must sit near a third of ambient.
> The air-mass channel on the same samples implies **31.2 kPa**, the textbook
> value. It is a **pre-throttle sensor**, useful for boost and useless as load.
> Units are psi, so the conversion on this card is right; the *use* was wrong.
> Load is now inverted from air mass (`plant.map_from_airflow`), which took the
> model's error from 75 % to 1.3 %.
>
> **2. The radiator outlet came alive.** Median 50 °C, peak 84 °C, against a
> regulated 92-97 °C block. Present on every drive since, except `fb988991`,
> which predates the change.
>
> **3. The brake switch toggled** — 294 actuations on the 8 September drive.
>
> **4. Sample rate.** The prediction was right: 19-21 channels give **4.6-6.6 Hz**
> against the 655-channel log's 3.52 Hz. The 21-channel set records at 4.56 Hz.
>
> One thing this card could not have anticipated: **`Air mass flow` saturates at
> exactly 1020 kg/h**, on four separate drives. See `CHANNEL_SET_FINAL.md`.
>
> The channel set has since grown to 21. **Use `logs/CHANNEL_SET_FINAL.md`** for
> what to record next, not the list of eighteen below.
>
> **v1 is archived as `DRIVE_1_card_v1.md`.** Two things in it are worth
> knowing. First, it confirms the audit finding that prompted v2: v1 asks the
> driver to "press the brake pedal 4 times (tests the brake channel)" and then
> asks "did the brake switch toggle?", while none of its fourteen selected
> channels is a brake channel. Second, its physics reasoning turned out to be
> right — it justified three-minute holds on the grounds that "the turbine
> housing settles in about 4 minutes", and the turbine time constant has since
> been measured at 48 s, giving 5*tau = 4.0 min exactly.

# DRIVE 1 — v2. Do only this. ~40 minutes. One recording.

> **v2 supersedes v1.** Four channels added, and a two-minute parked test added
> at the start. The reason is in the audit: v1 asked you to press the brake to
> "test the brake channel" but never selected a brake channel, and the pressure
> channels in your last log do not reconcile with physics. Both are fixed here.

## Before you leave (5 min, parked)

1. BimmerLink → data logging → select **these 18**:

```
Engine speed
Intake manifold absolute pressure
Boost pressure
Air mass flow
Mass flow through throttle valve bank 1
Relative air filling
Intake air temperature before throttle valve, measured
Coolant temperature
Engine radiator outlet temperature (coolant)
Oil temperature
Ambient pressure
Ambient temperature
Vehicle speed
Throttle valve angle related to the lower stop
Actual gear
Lambda actual value
Actual ignition angle
Condition brake test switch actuated
```

All eighteen were confirmed present in your own logs. Fourteen were confirmed
live. Two — the radiator outlet and the brake switch — appeared only in the
short engine-off recording, so they are selectable but unproven; Drive 1 is
what proves them.

2. Phone: **Auto-Lock → Never**, Low Power Mode **off**, plugged in, **vent mount**.
3. Engine warm before recording. Drive 10 min first if cold.

---

## Start recording, then:

### Part 0 — the parked test. Two minutes. Do not skip this.

**0:00 — parked, in P, engine idling, foot off everything.**
Sit still for **60 seconds**. Do nothing.

**1:00** — Press the **brake pedal 4 times**, slowly.

**1:30** — **3 hard throttle blips** in neutral.

**2:00** — Wait 30 seconds, then drive.

> **Why 60 seconds of doing nothing matters more than the rest of the drive.**
> At warm idle the true manifold pressure of any throttled engine is about
> 30–35 kPa, roughly 4.5–5 psi. In your last log the channel called "intake
> manifold absolute pressure" never dropped below 13.4 — about 92 kPa — which
> cannot be an idle manifold reading. Sixty seconds of clean idle tells us which
> of the pressure channels is the real one and what its units are. Without it,
> every number the simulator is compared against could be wrong by a factor of
> two, and nobody would notice until month three.

### Part 1 — the operating points

**Hold each of these for 3 minutes.** Cruise control where you can.

> **What "manual 4th" means.** Pull the **left paddle** (the minus one) to shift
> *down* a gear. Pull, look at the gear number on the dash, pull again if needed,
> until it reads 4. Your foot does nothing during this — you are only telling the
> gearbox which gear to sit in.
>
> **What "higher revs" means.** The engine spins faster *because a lower gear is
> selected*, not because you accelerated. 100 km/h in D is around 1600 rpm; 100
> km/h in 3rd is around 3000 rpm. **Same speed, same steady throttle, different
> engine speed.** That is the entire point — a second data point at a road speed
> you already have.
>
> **Nothing in this drive goes near full throttle or redline.** If at any moment
> you are accelerating hard, you have misread the card. The engine will sound
> busier in a low gear; that is expected and it is not stress.

| # | Speed | Gear | Notes |
|---|---|---|---|
| 1 | 60 km/h | D (auto) | |
| 2 | 80 km/h | D | |
| 3 | 100 km/h | D | |
| 4 | 120 km/h | D | |
| 5 | 100 km/h | **manual 4th** | paddle down until it holds 4th |
| 6 | 80 km/h | **manual 4th** | |
| 7 | 100 km/h | **manual 3rd** | higher revs, same speed |
| 8 | 60 km/h | **manual 3rd** | |
| 9 | 120 km/h | **manual 5th** | |
| 10 | any | D | 3 min of normal driving |

**Steady means steady.** Foot still, speed within ±2 km/h. If traffic forces you
off a point, redo it — no harm.

**Stop recording. Export CSV. Send it.**

---

## What Drive 1 can and cannot validate

Worth knowing before you drive, so the result is not a disappointment.

**It will validate** the low-load, naturally-aspirated corner of the model:
volumetric efficiency, intake temperature behaviour, coolant and oil
temperatures, and the relationship between gear, engine speed and load.

**It cannot validate** the boosted, knock-limited, enriched region — the exact
place the project's damage physics lives. Your previous log never exceeded 46.5%
relative filling and lambda never left 1.00, and this drive is deliberately
gentle, so it will look similar.

That is not a flaw in the drive. Steady points require steady driving, and steady
driving is light-load driving. The boosted region gets validated against
published figures instead, and **Chapter 3 says so plainly.** An examiner
respects a stated scope limit far more than a silent one.

---

## After this drive

Send me the CSV. I check four things:

1. What the pressure channels read at true idle — the unit question, settled.
2. Whether the radiator outlet channel came alive.
3. Whether the brake switch toggled.
4. What sample rate eighteen channels actually gave you. Your 655-channel log
   ran at 3.52 Hz; eighteen should be far faster, but that is a prediction, not
   a measurement, until you send it.

Then Drive 2 gets designed from what Drive 1 actually shows.
**Do not plan drives 2–8 yet.**

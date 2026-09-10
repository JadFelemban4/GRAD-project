> **ARCHIVED — v1, superseded by `DRIVE_1_card_v2.md` and completed.**
>
> Kept as the record of what was originally asked for, and because two of its
> details still matter.
>
> **Its known flaw.** It tells you to press the brake pedal four times "to test
> the brake channel" and asks afterwards whether the brake switch toggled — but
> no brake channel appears in its fourteen. Nothing was recorded. v2 fixed it,
> and `Condition brake test switch actuated` has logged cleanly ever since
> (294 actuations on the 8 September drive).
>
> **Its reasoning was sound.** It justified three-minute holds by saying the
> turbine housing "settles in about 4 minutes". That was an assumption at the
> time; the turbine time constant has since been measured at **48 s**, so five
> time constants is 4.0 minutes. The card was right.
>
> How the protocol actually went on the road: across seven drives there are
> **22 steady holds of 60 s or more but only 6 of 180 s**. Three uninterrupted
> minutes is more than a public road usually grants, which is why
> `build_dataset.py` extracts 60 s windows. See its comment on `WINDOW_S` for
> what a 60 s window does and does not settle.

# DRIVE 1 — do only this. ~35 minutes. One recording.

## Before you leave (5 min, parked)

1. BimmerLink → data logging → select **only these 14**:

```
Engine speed
Intake manifold absolute pressure
Air mass flow
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
```

2. Phone: **Auto-Lock → Never**, Low Power Mode **off**, plugged in, **vent mount** (not windscreen).
3. Engine warm before you start recording. Drive 10 min first if cold.

---

## Start recording, then:

**0:00 — parked, engine running**
Press the **brake pedal 4 times**, slowly. (Tests the brake channel.)
Then **3 hard throttle blips** in neutral. (Time-sync marker.)
Wait 30 seconds.

**Then hold each of these for 3 minutes.** Cruise control where you can.

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

**Steady means steady.** Foot still, speed within ±2 km/h. If traffic
forces you off a point, just redo it — no harm.

**Stop recording. Export CSV. Send it.**

---

## Why each thing is there

- **10 speed/gear combinations** = 10 different (RPM, load) points. Same speed in
  a different gear gives a different RPM — that is the second axis of the map.
- **3 minutes each** because the slowest thing being measured (turbine housing)
  settles in about 4 minutes. 3 min gets you most of the way, and 10 points at
  3 min fits in one drive.
- **Brake presses at the start** tell us whether that channel works.
- **Throttle blips** make a signature we can use to align GPS later if needed.

---

## After this drive

Send me the CSV. I check three things and tell you:
1. Did the radiator outlet channel come alive?
2. Did the brake switch toggle?
3. What sample rate did 14 channels actually give you?

Then Drive 2 gets designed from what Drive 1 actually shows.
**Do not plan drives 2–8 yet.**

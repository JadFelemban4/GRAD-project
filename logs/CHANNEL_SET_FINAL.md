# Channel set — what is actually being recorded, and what to add next

Regenerated 8 September 2026 from `logs/raw/cb67b01f-20260908_084142.csv`.

This supersedes `bimmerlink_channel_selection.md`, which was written from the
first log on 6 September and contains **two errors that would corrupt any
analysis built on it**. Both are corrected below. Keep the old file for the
record; do not plan a drive from it.

---

## The two corrections

**1. `Air mass flow` is kg/h, not g/s.** The old file says g/s in two places and
the code has always treated it as kg/h. The code is right, and idle settles it:
at warm idle this channel reads **16–20**, and a 3.0 L six needs about 4–6 g/s
of air to idle. As kg/h that is 4.5–5.6 g/s — correct. As g/s it would be four
times what the engine can breathe. Peak reads 1020, which is 283 g/s, or about
850 kW of fuel at λ=1 — right for a 387 PS engine.

**2. `Intake manifold absolute pressure` is a PRE-THROTTLE sensor.** The old
file lists it as "load axis — CONVERT: kPa = psi × 6.895". Converting it is
fine; **using it as the model's load input is not.** At warm idle it reads 13.49
psi against an ambient of 14.23, where a throttled engine must sit near a third
of ambient. The air-mass channel on the same samples implies 31.2 kPa, the
textbook value. Feeding the logged channel to the model gives **75 % air-mass
error**; inverting air mass gives **1.3 %**. Record the channel — it is the only
direct boost measurement — but derive load with `plant.map_from_airflow()`.

---

## The 21 channels currently recorded

All confirmed live on 8 September. Units are as the export writes them.

| # | Channel | Unit | What it is for |
|---|---|---|---|
| 1 | `Engine speed` | rpm | primary map axis |
| 2 | `Intake manifold absolute pressure` | psi | **pre-throttle** — boost only, never load |
| 3 | `Boost pressure` | psi gauge | compressor pressure ratio, with #12 |
| 4 | `Air mass flow` | **kg/h** | the load input, via `map_from_airflow()`. Saturates at 1020 |
| 5 | `Mass flow through throttle valve bank 1` | kg/h | cross-check on #4 |
| 6 | `Relative air filling` | % | BMW's own load figure — what `compare_log.py` scores against |
| 7 | `Intake air temperature before throttle valve, measured` | °C | charge temperature. Post-intercooler, runs 57–163 °C |
| 8 | `Air mass flow participating in combustion` | kg/h | ECU's modelled trapped charge. Does **not** saturate at 1020 |
| 9 | `Coolant temperature` | °C | block node, engine-out |
| 10 | `Engine radiator outlet temperature (coolant)` | °C | radiator cold side |
| 11 | `Oil temperature` | °C | oil node |
| 12 | `Ambient pressure` | psi | compressor inlet, altitude correction |
| 13 | `Ambient temperature` | °C | boundary condition for every heat flow |
| 14 | `Vehicle speed` | km/h | road load, gear inference, ram-air term |
| 15 | `Throttle valve angle related to the lower stop` | % | driver demand |
| 16 | `Actual gear` | – | gear ratio for the vehicle model |
| 17 | `Lambda actual value` | – | mixture. Reads ~16 during overrun fuel cut |
| 18 | `Actual ignition angle` | deg | the action variable. Goes negative on fuel cut |
| 19 | `Condition brake test switch actuated` | 0/1 | isolates coast-down and overrun |
| 20 | `Intake air temperature` | °C | ambient-side intake temp — the compressor inlet |
| 21 | `Is position electrical wastegate` | % | boost actuator position |

Recorded rate on this set: **4.56 Hz**. Earlier 19-channel drives reached
6.6 Hz. Fewer channels buys rate; the trade is real.

---

## Add these, and what each one unlocks

> **CORRECTION, 8 September.** An earlier version of this file recommended
> adding `Actual speed electr. water pump` and `Duty cycle electric fan` so the
> radiator could be measured directly. **Both are all-zero on this car** — see
> `CHANNEL_CENSUS.md`, built from the 655-channel exploratory logs. Recording
> them would have cost a drive and returned columns of zeros. The radiator
> cannot be measured directly on this vehicle, and that is now a confirmed
> property of the car rather than a gap in the channel list.

### 1. `Target ignition angle from torque intervention` — deg

**The best single addition.** Live, −17.2 to 31.5°. Target minus actual is the
knock retard the ECU is applying. `BaselineECU` models that retard and nothing
currently measures it.

### 2. `Oil temperature after filter` — °C

Live, and it runs a consistent **+12.5 K hotter** than the `Oil temperature`
channel we record — 108 °C against 96 °C on the census drive. That offset may
explain why the model's sustained-climb oil temperature misses its published
band: the two numbers are probably measured at different points in the circuit.
Record both and find out.

### 3. `Boost pressure setpoint` and `Control difference boost pressure bank 1`

Both live. Together they show the wastegate controller's target against actual —
the loop the agent's boost trim sits on top of.

### 4. `Coordinated target torque on the wheel` — Nm

Live, 0–357.7 Nm. The car's own torque request, which would let the vehicle
model in `engine_env.py` be checked against the real thing instead of assumed.

---

## Do not bother re-adding

- **`Temperature after the intercooler`** — read 0.00 across all 3452 samples of
  the 6 September log. Not supported on this car.
- **`Voltage knock values cylinder N`** — the old file recommends these. They
  are raw sensor voltages sampled far faster than the logger runs; at 4–6 Hz
  they alias into noise. The knock retard channel above is the useful signal.
- **`Oil temperature in the sump`** — the sump is the coolest point in the
  circuit and oil is already known to track coolant there within a few kelvin.
  (`Oil temperature after filter` is a different matter — see addition 2 above.
  An earlier version of this file lumped the two together and dismissed both;
  that was wrong, because the after-filter channel runs 12.5 K hotter and may
  explain a validation miss.)

---

## The drive still missing

Everything in the dataset is either cruising or a short pull. **No drive has yet
overwhelmed the cooling system**, which is why the radiator is unidentifiable
and why the model's oil behaviour above 103 °C is extrapolation.

Note what the census adds to this: it is not only that the coolant stays in
band. The **fan setpoint sits between 28 and 31 % for an entire drive** and
`Target temperature coolant` reads a flat 95 °C. The actuators never move, so
there is nothing to fit against. Even with the right channels, a comfortable
drive cannot identify a cooling system.

The drive to plan: a sustained climb in traffic, high ambient, low road speed so
ram air is weak, held long enough for the fan to reach full duty and the coolant
to rise past the thermostat's fully-open point.

**Be realistic about what it can deliver.** With no coolant-flow signal on this
car, even that drive gives a constrained fit rather than a direct measurement —
`Q = ṁ·cp·ΔT` needs a ṁ that does not exist here. What it can do is force the
system out of regulation so the radiator term stops being masked by the
thermostat, and let `ua_rad_ram` and `ua_rad_fan` be fitted up to an unknown
flow constant. That is a real improvement on three reasoned numbers, and it is
not the same as measuring them. Say which it is.

**Safety comes first: this is a normal road drive with a passenger logging, not
a deliberate attempt to overheat the engine.** If the coolant gauge moves off
its normal position, or any warning appears, end the drive. The point is to
reach the top of the regulated band, not to exceed it.

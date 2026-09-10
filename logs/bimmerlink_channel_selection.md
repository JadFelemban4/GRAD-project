> **SUPERSEDED — 8 September 2026. Do not plan a drive from this file.**
>
> Read `logs/CHANNEL_SET_FINAL.md` instead. This one was written from the first
> log on 6 September and contains two errors that would corrupt any analysis
> built on it:
>
> 1. It lists **`Air mass flow` as g/s. It is kg/h.** Idle settles it: this
>    channel reads 16-20 at warm idle, and a 3.0 L six needs 4-6 g/s to idle.
> 2. It presents **`Intake manifold absolute pressure` as the load axis. It is a
>    pre-throttle sensor** and using it as load gives 75 % air-mass error.
>
> Kept unedited below as the record of what was planned and why.

# BimmerLink channel selection — exact names from your 2026-09-06 log

Source log: 655 channels, 3452 rows, 16.3 min, 4.2 Hz, ambient 38.5-40.5 C.
317 channels carried live data; 337 were all-zero (not supported on this car).

Names below are copied verbatim from your CSV header — tick these exact strings.

## SET A — STEADY-STATE MAP  (target 8-12 Hz)

- [x] `Engine speed`  — *rpm* — primary map axis
- [x] `Intake manifold absolute pressure`  — *PSI* — load axis - CONVERT: kPa = psi x 6.895
- [x] `Air mass flow`  — *g/s* — volumetric efficiency - the curve you cannot get otherwise
- [x] `Air mass flow participating in combustion`  — *g/s* — cleaner than raw MAF for combustion work
- [x] `Intake air temperature before throttle valve, measured`  — *C* — *** CHARGE TEMP - use THIS one, not 'Intake air temperature' ***
- [x] `Coolant temperature`  — *C* — thermal state
- [x] `Oil temperature`  — *C* — thermal state
- [x] `Ambient pressure`  — *PSI* — altitude correction - critical on the Taif escarpment
- [x] `Ambient temperature`  — *C* — boundary condition
- [x] `Vehicle speed`  — *km/h* — road load and gear inference
- [x] `Throttle valve angle related to the lower stop`  — *%* — driver demand
- [x] `Actual gear`  — *-* — gear ratio for the vehicle model
- [x] `Lambda actual value`  — *-* — mixture
- [x] `Actual ignition angle`  — *deg* — action variable

## SET B — TRANSIENT & KNOCK  (keep small, maximise rate)

- [x] `Engine speed`  — *rpm* — axis
- [x] `Intake manifold absolute pressure`  — *PSI* — axis
- [x] `Actual ignition angle`  — *deg* — *** the action variable ***
- [x] `Target ignition angle from torque intervention`  — *deg* — target minus actual = the retard
- [x] `Intake air temperature before throttle valve, measured`  — *C* — feeds knock correlation exponentially
- [x] `Voltage knock values cylinder 1`  — *V* — *** raw per-cylinder knock sensor ***
- [x] `Voltage knock values cylinder 4`  — *V* — one from each bank half is enough at first
- [x] `Normalized reference level knock control cylinder 1`  — *-* — the adaptive reference the ECU compares against
- [x] `Lambda actual value`  — *-* — other action variable
- [x] `Boost pressure`  — *PSI* — load

## SET C — THERMAL & ROUTE  (1-2 Hz is plenty)

- [x] `Coolant temperature`  — *C* — block/coolant node
- [x] `Oil temperature`  — *C* — oil node
- [x] `Oil temperature in the sump`  — *C* — second oil measurement - useful cross-check
- [x] `Oil temperature after filter`  — *C* — runs hottest - good for the damage model
- [x] `Exhaust gas temperature after catalytic converter from model`  — *C* — MODELLED and POST-CAT - see limitation note
- [x] `Intake air temperature before throttle valve, measured`  — *C* — heat soak, esp. with your open intake
- [x] `Ambient temperature`  — *C* — boundary condition
- [x] `Ambient pressure`  — *PSI* — altitude
- [x] `Engine speed`  — *rpm* — operating point
- [x] `Intake manifold absolute pressure`  — *PSI* — operating point
- [x] `Air mass flow`  — *g/s* — heat input to the thermal network
- [x] `Vehicle speed`  — *km/h* — ram-air cooling term
- [!] `Actual value of electric fan`  — *%* — cooling actuator - the agent controls this
- [!] `Actual speed electr. water pump`  — *%* — cooling actuator
- [x] `Is position electrical wastegate (0: WG closed, 100 WG open)`  — *%* — boost actuator


## ADD THESE TWO — missed in the first log

- [ ] `Engine radiator outlet temperature (coolant)`  — *°C* — **Set C. High value.**
  Paired with `Coolant temperature` (engine-out, hot side) this gives the temperature
  DROP across the radiator. With `Actual speed electr. water pump` for flow and
  `Vehicle speed` / `Duty cycle electric fan` as the conditions, you can MEASURE the
  radiator UA instead of fitting it:

      Q_rejected = m_dot_coolant * cp * (T_engine_out - T_radiator_out)
      UA_rad(v, fan) = Q_rejected / (T_mean_coolant - T_ambient)

  In `thermal.py` this replaces three currently-guessed parameters —
  `ua_rad_min`, `ua_rad_ram`, `ua_rad_fan` — with measured ones.
  It also makes the thermostat directly observable: while it is shut there is little
  flow through the radiator so the drop is small; when it opens the drop jumps. That
  gives you `t_stat_open` and `t_stat_span` from data rather than assumption.

- [ ] `Condition brake light switch actuated`  — *0/1* — **Sets A and C. Cheap, useful.**
  One bit, negligible bandwidth. Three uses:
  1. Isolates clean coast-down segments (throttle closed AND brake off) — that is how
     you fit the vehicle model's drag area and rolling resistance.
  2. Separates engine braking from friction braking in the road-load fit.
  3. Flags overrun / fuel-cut samples so they can be excluded from fuelling analysis.

## Units found in your log

- Pressures are **PSI**, not kPa. Ambient reads 14.44 psi = 99.5 kPa (sea level, checks out).
  Convert with `kPa = psi * 6.895` before anything touches the plant.
- Temperatures °C, air mass g/s, speed km/h, ignition angle degrees.

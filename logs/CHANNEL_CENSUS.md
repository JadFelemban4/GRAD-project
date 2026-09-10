# What this car actually exposes — the channel census

Derived 8 September 2026 from `fb988991-20260906_143515.csv` and
`f51686d7-20260906_154426.csv` — the two reconnaissance recordings.

---

## These two recordings are not failed drives

They were made on 6 September with **every channel BimmerLink offers selected**,
before anyone knew which parameters this car publishes. That was the right thing
to do and it is the only reason the rest of the project could pick a sensible
21-channel set. They are **reconnaissance**, and they succeeded.

They are not usable as *driving* data, and that is a consequence of their
purpose rather than a mistake: at 655 channels the logger cannot keep up. It
dropped **222 of `fb988991`'s 980 seconds — 23 % of the recording** — in 196
separate gaps. `build_dataset.py` therefore extracts no operating points from
either. Both are kept in `logs/raw/` because they are the census, and the census
is still answering questions.

**Do not delete them, and do not treat their exclusion as a quality failure.**

---

## The census

| | count |
|---|---|
| channels the car offers | **656** |
| carrying any non-zero data | **318** |
| genuinely varying (not constants or flags) | **177** |
| all-zero — not fitted or not published on this vehicle | **338** |

---

## What the census settles

### The radiator cannot be identified on this car. Confirmed, not assumed.

`thermal.py` leaves `ua_rad_min`, `ua_rad_ram` and `ua_rad_fan` at reasoned
values because the drives cannot identify them. The census shows this is not a
matter of selecting the right channels — **the signals do not exist**:

| channel | state |
|---|---|
| `Actual speed electr. water pump` | **all zero** |
| `Confirmed target speed electr. water pump` | **all zero** |
| `Set speed of electric water pump` | **all zero** |
| `Current consumption electr. water pump` | **all zero** |
| `Actual value of electric fan` | **all zero** |
| `Duty cycle electric fan` | **all zero** |
| `Setpoint electric fan` | live, but **28.1–30.9 %** for the whole drive |

**This corrects a recommendation made earlier in `CHANNEL_SET_FINAL.md`**, which
told you to add the water pump speed and fan duty channels so the radiator could
be measured directly. Both are dead. Recording them would have cost a drive and
returned columns of zeros.

Two independent reasons the radiator stays unidentifiable:

1. **No coolant flow signal.** `Q = ṁ·cp·ΔT` needs ṁ, and no pump channel
   publishes anything. The temperature drop across the radiator is measurable
   (in the 21-channel set), the flow is not.
2. **The actuators never move.** The fan setpoint sits between 28 and 31 % for
   the entire drive, and `Target temperature coolant` reads a flat 95 °C. The
   cooling system is regulated and comfortable, so there is no excitation to fit
   against — the same reason the thermostat masks the radiator in every log.

**ATTEMPTED 8 September (afternoon) and it does not work either.** Drive
`7475b5d7` gave 55 minutes at 40–45 °C ambient with far more excitation than
anything before it: radiator outlet spanning 49.5–92.2 °C, the coolant-to-
radiator drop ranging 1.0–46.2 K, road speed 0–64 m/s.

The constrained fit — assume coolant flow constant at high pump duty, then fit
`ua_rad ∝ stat·(a + b·v)` against the observed drop — returns **R² = 0.157 and a
NEGATIVE ram coefficient**. Binned, the drop ratio *falls* with road speed:
0.58 below 10 m/s, 0.47 at 30–40, 0.21 above 40.

That is not a bad fit, it is the wrong model, and the reason is instructive. The
only observable is ΔT across the radiator, and **ΔT = Q / ṁ**. Both the heat
rejected and the coolant flow rise with road speed, so ΔT carries almost no
information about UA — it is dominated by the flow term that cannot be measured.
Assuming flow constant is not a mild approximation here; flow co-varies with the
very variable being fitted.

**So the radiator cannot be identified on this vehicle at all — not directly,
and not by a constrained fit.** An earlier version of this file promised the
constrained fit as a fallback. It does not work. `ua_rad_min`, `ua_rad_ram` and
`ua_rad_fan` stay as reasoned values, and the thesis should say so plainly
rather than implying a measurement that is not available.

Nothing downstream depends on it: the thermostat regulates coolant to 88–97 °C
in every drive, so the block node behaves correctly whatever the radiator
constants are. It is a stated limitation, not a blocker.

### `Oil temperature after filter` is a real, hotter channel — and it may reconcile a validation miss

| channel | max in the census drive |
|---|---|
| `Oil temperature` (what we record and calibrate on) | 96.0 °C |
| `Oil temperature after filter` | **108.0 °C** |

The offset is consistent, not noise: median **+12.5 K**, p95 +13.0 K, max +15.5 K.

This matters for `validate.py`. The oil row currently reports 110.2 °C against a
published sustained-climb band of 115–140 °C and is recorded as a miss. If the
published band refers to a hotter measurement point in the circuit — which
"sustained-load oil temperature" figures usually do — then the model's 110.2 °C
plus the measured +12.5 K offset is about **123 °C, inside the band**.

**TESTED 8 September (afternoon), drive `7475b5d7`. The offset holds, but it
shrinks with temperature — and the shrinking is what matters.**

| | census drive | 55-min drive, 45 °C ambient |
|---|---|---|
| median offset, whole drive | +12.5 K | **+11.0 K** |
| p95 | +13.0 K | +13.0 K |
| **median at oil above 100 °C** | — | **+6.8 K** |
| peak oil / oil-after-filter | 96 / 108 °C | **107 / 111 °C** |

The offset is real and repeatable, but quoting +12.5 K at climb temperatures
would have been wrong: it is a whole-drive median dominated by cool cruise, and
at the temperatures the published band describes it is about **+6.8 K**.

That still reconciles the miss — the model's 110.2 °C plus 6.8 K is **117 °C,
inside the 115–140 band** — but the correct number is half what this file first
suggested. Note the shape of the error: a figure computed over the wrong subset,
which is the same mistake `verify_docs.py` was written to catch.

Still not applied anywhere. The miss is still reported as a miss.

### Confirmed dead — do not select these

- `Temperature after the intercooler` — all zero, as previously found.
- Every bank-2 channel (`... bank 2`) — this is an inline six with one bank.
- Every SCR / oxidation-cat / diesel aftertreatment channel.
- Every 48 V, electric-machine and hybrid cooling channel.

### Confirmed live and worth adding

- **`Target ignition angle from torque intervention`** — live, −17.2 to 31.5°.
  Target minus actual is the knock retard the ECU is applying, which
  `BaselineECU` models and nothing currently measures. Still the best addition.
- `Boost pressure setpoint` and `Control difference boost pressure bank 1` —
  live. Together they show the wastegate controller's target against actual,
  which is the loop the agent's boost trim sits on top of.
- `Coordinated target torque on the wheel` — live, 0–357.7 Nm. The car's own
  torque request. Would let the vehicle model in `engine_env` be checked against
  the real thing rather than assumed.
- `Exhaust gas temperature after catalytic converter from model` — live to
  645 °C, but **modelled and post-catalyst**, so it is not turbine inlet
  temperature and cannot validate the turbine node. Say so if it is used.

### Live but not worth the bandwidth

- `Voltage knock values cylinder 1–6` — live, but the whole range is 0.0–0.1 V.
  At 4–6 Hz these are aliased noise; knock detection happens orders of magnitude
  faster than this logger samples. The retard channel above is the useful signal.
- `Normalized reference level knock control cylinder 1–6` — same range problem.

---

## How to redo this census

If the car is ever updated, or a different vehicle is used:

1. Select every channel BimmerLink offers. Accept that the log will be full of
   dropouts — that is fine, this recording is not for driving data.
2. Ten minutes of ordinary driving is enough to see which channels move.
3. A channel that is all-zero across the whole recording is not fitted or not
   published. A channel that never varies is published but not useful.
4. Then choose the small set, and record *that* for the real drives.

The two recordings that produced this census cost one short drive and answered
questions that are still being answered two days later.

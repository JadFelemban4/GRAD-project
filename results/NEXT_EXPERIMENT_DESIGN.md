# Design of the next experiment — randomising the climb

**Written 22 September 2026. NOT a preregistration.** This is the design record
the next preregistration will be written from. It holds the measurement that
constrains the design, the options that were considered, and why. Nothing here
has been trained, and nothing is fixed until `PREREGISTRATION_2.md` (or
whatever the next one is called) is committed before its first run.

## Why this experiment exists

`PREREGISTRATION.md` limit 7: **the blinded arm of Phase D is not blind.** The
road is the same hill at the same second (t = 180 s) in every training and
evaluation episode, and the blind agent's thermal state takes a distinct value
at every step, so it has a clock on a road it can memorise. Phase D compared an
explicit preview channel with an implicit one, not foresight with none.

The fix is to randomise the climb per episode so that no amount of memorisation
tells the blind agent when — or how hard — the hill arrives. Then the preview
channel is the only route to anticipating it.

## THE MEASUREMENT THAT CONSTRAINS THE DESIGN

A randomised climb is only useful if **every** episode reaches the protection
limit. An episode that never binds carries no protection signal — protection
costs something and buys nothing — so preview cannot help in it, and it dilutes
every episode that does bind.

Measured 22 September, neutral policy, 130 km/h, 720 s, dt 1.0, trigger 850 °C:

| grade | start | peak | vs trigger | seconds above | binds? |
|---|---|---|---|---|---|
| 8 % | 180 s | 848.9 °C | **−1.0 K** | 0 | **no** |
| 10 % | 180 s | 826.6 °C | **−23.3 K** | 0 | **no** |
| 12 % | 180 s | 884.0 °C | +34.2 K | 417 | yes |
| 14 % | 180 s | 862.6 °C | +12.7 K | 380 | yes |
| 16 % | 180 s | 902.9 °C | +53.0 K | 451 | yes |
| 12 % | 120 s | 884.0 °C | +34.2 K | 475 | yes |
| 12 % | 300 s | 884.0 °C | +34.1 K | 300 | yes |

**Two things follow, and both are findings in their own right.**

**1. The start time is free; the grade is not.** Moving the climb between 120 s
and 300 s leaves the peak at 884.0 °C — only the time spent above the limit
changes. Every start in that range binds. But grades of 8 % and 10 % never reach
the trigger at all.

**2. Peak temperature is NOT monotonic in grade.** 10 % runs cooler than 8 %,
and 14 % cooler than 12 %. That is the gearbox: `Vehicle.gear_for` hands back a
gear when the torque demand passes `SHIFT_LOAD`, a lower gear means higher rpm
and lower load per cycle, and a lower load per cycle means a cooler exhaust
(`CLAUDE.md` mistake 17 records the same mechanism). **Grade is not a "hotter"
knob.** A randomisation over grade inherits that shape, and a reader who assumes
steeper-is-hotter will misread the results.

**The range first proposed and accepted on 22 September — 120–300 s and
8–16 % — is therefore flawed in its grade half.** Roughly a third of its
episodes would not bind. It was measured before anything was built, which is
why it can still be changed.

## The options, with what each buys and costs

### A. Randomise the START TIME only; grade fixed at 12 % — RECOMMENDED

| | |
|---|---|
| **buys** | the cleanest test of what preview actually does, which is **timing**; every episode binds (+34 K, measured at 120, 180 and 300 s); ONE variable changes, which is this project's house rule |
| **costs** | the blind agent still knows every hill is 12 %, so it knows *how hard* — only *when* is hidden. That is acceptable: preview's value is in the when |
| **risk** | none measured |

### B. Randomise start time AND grade, over binding grades only (12–16 %)

| | |
|---|---|
| **buys** | the blind agent can know neither when nor how hard; every measured grade in the range binds |
| **costs** | two variables at once; the gearbox makes peak non-monotonic in grade, so a result is harder to read; **14 % binds by only +12.7 K**, so some episodes barely exercise protection; 13 % and 15 % are unmeasured |
| **risk** | a thin-margin episode behaves like a non-binding one and dilutes the signal |

### C. The originally accepted range: 120–300 s and 8–16 %

| | |
|---|---|
| **buys** | the widest variation |
| **costs** | **8 % and 10 % do not bind** — measured above. Those episodes carry no signal |
| **verdict** | **do not use.** Kept here so it is recognised if proposed again |

### D. Several climbs per episode (a rolling road)

| | |
|---|---|
| **buys** | several events per episode, so more signal per training episode — which matters because Phase D's agents saw only 11 episodes (`PREREGISTRATION.md` limit 6) |
| **costs** | a new road shape to design and validate; `CLAUDE.md` records that on a rolling road hand-written preview got WORSE, because the max-over-horizon policy protects almost continuously — a flaw of that policy, not of the road, but it shows the shape changes what preview is for |
| **risk** | confounds "is preview worth it" with "how should preview be used on a busy road" |

### E. Randomise the initial thermal state as well

| | |
|---|---|
| **buys** | breaks the thermal clock at its source |
| **costs** | on its own it does not stop the road being memorised by counting from reset. Useful only in combination with A or B |

## Recommendation

**A first, at the C1 budget.** It is the minimum change that removes the flaw,
it moves one variable, and every episode is measured to bind. About an hour of
training and two and a half of evaluation on this machine.

- If the arms **separate** under A, the fixed road was hiding the effect, and
  that is the result.
- If they **still do not**, the design flaw is ruled out as the explanation, and
  the next suspects are the training budget (C4) and the preview horizon — in
  that order.

B is the natural second step if A separates and the question becomes "does
preview also help with how hard, not only when".

## Decision

**Open.** The team accepted C on 22 September before the measurement above
existed; A is recommended in its place. The chosen option, and its ranges, go
into the next preregistration **before** training — not into this file.

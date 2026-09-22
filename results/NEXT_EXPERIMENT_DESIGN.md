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

## Decision — OPTION B, taken 22 September 2026

**Randomise the climb's start time over 120–300 s and its grade over 12–16 %,
per episode.** Decided by the team (Jad), overriding the recommendation of A
above, and the reasoning is better than the recommendation was.

### The principle the decision rests on

> **"Our goal is not the highest result. Our goal is to be realistic."**
> — Jad, 22 September 2026

Recorded because it is a design principle, not a preference, and it will decide
future choices the same way: when a cleaner experiment and a more faithful one
disagree, this project takes the faithful one.

### Why B is right, and where A's case was weaker than it looked

1. **B tests a richer preview, which is the real one.** Under A the preview
   tells the sighted agent only *when* the hill comes. Under B it says *when* and
   *how steep* — which is what a map or GPS actually tells a driver. "Is preview
   worth acquiring" is a question about the real thing, so B is the more
   faithful test of the project's claim.
2. **Under B the blind agent is blind to both** — neither timing nor severity
   can be memorised. That is exactly limit 7's fix, fully applied.
3. **A's main advantage was ease of interpretation, and it was overstated.** The
   objection was that the gearbox makes peak non-monotonic in grade. But the
   comparison is PAIRED: sighted and blind face the identical episodes, so the
   sawtooth hits both arms equally and does not bias the difference between
   them.
4. **"Change one variable" is a debugging rule**, for finding which change
   caused an effect. It is not a rule for designing an experiment, where testing
   the right condition matters more than testing a minimal one.
5. **B's one real risk is now measured away** — see below.

### The measurement that makes B safe: every grade in 12–16 % binds

Neutral policy, 130 km/h, 720 s, dt 1.0, trigger 850 °C:

| grade | peak | margin | seconds above |
|---|---|---|---|
| 12.0 % | 884.0 °C | +34.2 K | 417 |
| 12.5 % | 896.9 °C | +47.1 K | 435 |
| 13.0 % | 909.2 °C | +59.4 K | 447 |
| 13.5 % | 920.8 °C | +70.9 K | 457 |
| **14.0 %** | **862.6 °C** | **+12.7 K** | 380 |
| 14.5 % | 873.1 °C | +23.2 K | 410 |
| 15.0 % | 883.3 °C | +33.4 K | 428 |
| 15.5 % | 893.2 °C | +43.4 K | 441 |
| 16.0 % | 902.9 °C | +53.0 K | 451 |

**Nine of nine bind.** The weakest is 14.0 % at +12.7 K. The sawtooth is the
gearbox: the peak climbs from 12 % to 13.5 %, drops 58 K between 13.5 % and
14 % where the box hands back a gear, then climbs again. **Grade is not a
"hotter" knob, and any figure in the write-up that bins results by grade has to
say so.**

The start time does not move the peak (12 % at 120 s and at 300 s both reach
884.0 °C), because the climb lasts at least 420 s — about nine climb time
constants — and reaches steady state whenever it starts.

### THE ONE THING "REALISTIC" CANNOT MEAN HERE, and it must be said

B is realistic in its **variability**: real roads change, and a driver does not
know what is coming. It is **not** realistic in its **severity**, and nothing
that tests protection can be.

- Grades of 12–16 % at 130 km/h are steeper than any road this project has
  driven. The Taif run — two hours of real mountain road — peaks at 797.6 °C,
  **52 K short of the trigger**, and never binds.
- Across 292.0 replayed minutes of the car's own driving, the turbine is above
  the limit for 36 seconds: **0.206 % of the time.**
- Grades of 8 % and 10 %, the realistic end, do not bind at all (measured above).

**So realistic severity and a binding constraint are mutually exclusive on this
car.** A climb gentle enough to be typical is too gentle to need protection, and
an experiment about protection has to use one that isn't. That is a stated
design choice, as `CLAUDE.md` already records for the locked scenario — and it is
also a finding: on this vehicle, in real driving, preview has very little to
protect against.

The thesis sentence: *the climb varies like a real road, in when it comes and
how steep it is, but it is steeper than any road we measured — because no road
we measured stresses the turbine enough to need protecting.*

### What goes into the preregistration

- start time: uniform on [120, 300] s, drawn per episode
- grade: uniform on [12, 16] %, drawn per episode
- speed 130 km/h, ambient 42 °C, everything else as Phase D
- the draw is seeded per episode, so the twenty evaluation episodes are frozen
  exactly as Phase D's were — randomised across episodes, fixed across policies
- eight seeds per arm, C1 budget first; the statistic, test and alpha as
  Phase D, **plus the minimum effect of interest, which must be set this time**

## ADDENDUM, 22 September 2026 — the fine sweep found a deeper notch, and it still binds

The table above sampled grade every 0.5 % and named **14.0 % at +12.7 K** the
weakest. Training draws grade from a CONTINUOUS range, and the peak is a
sawtooth, so a notch between two grid points could be deeper than either.
`check_random_road.py` swept 12–16 % at 0.05 % and the notch region
(13.60–14.10 %) at 0.01 %, at the worst-case start (300 s, the shortest climb in
a 720 s episode), neutral policy, dt 1.0:

| | grade | peak | margin | seconds above |
|---|---|---|---|---|
| the 0.5 % grid's weakest | 14.00 % | 862.6 °C | +12.7 K | 263 |
| **the real minimum** | **13.73 %** | **856.8 °C** | **+6.9 K** | **233** |

**121 of 121 grades bind**, so option B stands. But the true margin at the
notch is half what the design record said, and it sits between the grid points
the decision was made on. The lesson is the one this record already states for
the grade range as a whole: measure a continuous draw continuously before
training on it.

The same run checked the rest of what Phase D2 needs, and all of it passes: the
road changes between resets; the blind arm's observations are identical on
every road until its climb arrives (first difference at 150 s for a 150 s climb,
against 120 s for the sighted arm); all twenty frozen episodes bind (weakest
13.99 %, +12.5 K); and the peak at 13.73 % is identical at dt 0.2 and dt 1.0
(856.8 °C). Output in `results/PREREGISTRATION_D2.md` section 10.

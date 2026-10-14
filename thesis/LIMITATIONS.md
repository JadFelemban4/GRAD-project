# LIMITATIONS — what the thesis must state, not fix quietly

Material for the thesis, moved verbatim from CLAUDE.md on 14 October 2026 (the
documentation restructure, plan v3 phase 4). Each block says what was measured,
on which plant, and what it does and does not show; the dates are the ones it
was written on.

## From CLAUDE.md's "The numbers that matter": real driving against the scenario, the rolling road, the towing standard

**And the scenario is the thing to fix, not the threshold — measured
17 September over EVERY drive.** *(17 Sep conclusion, since done: the scenario
was rebuilt at 12 % / 130 km/h on the ZF 8HP51 and now binds by ~34 K, peak
884 C against the 850 C trigger. The do-not-lower-the-limit half still stands.)*
Replaying every drive through `app/` (nine on 17 September, drive10 added on
the 19th) and reading the peak estimated turbine housing against the 1123 K
trigger, with the app's physics of those days (exhaust = fuel × 15). The merge's
exhaust-flow fix has since lowered `7475b5d7`'s pinned peak (the Numbers
section); the other rows, the 36 seconds and the fraction under the table were
not re-measured. Replay them before quoting any:

| drive | minutes | peak C | vs trigger | seconds above |
|---|---|---|---|---|
| `7475b5d7` | 55.1 | **890.6** | **+40.8** | **36** |
| `670063b2` | 7.3 | 780.3 | −69.5 | 0 |
| `cb67b01f` | 21.6 | 728.0 | −121.9 | 0 |
| `3aca2ec1` | 41.7 | 676.1 | −173.7 | 0 |
| `683640a0` | 24.0 | 664.1 | −185.7 | 0 |
| `pull01` | 7.4 | 608.0 | −241.8 | 0 |
| `fb988991` | 14.7 | 607.9 | −242.0 | 0 |
| `3f64372e` | 0.7 | 340.1 | −509.8 | 0 |
| `f51686d7` | — | no estimate | — | — |
| **`drive10` — TAIF** | **119.4** | **797.6** | **−52.4** | **0** |
| **total** | **292.0** | | | **36 s = 0.206 %** |

**ONE drive of ten reaches the limit, for 36 seconds in 292.0 minutes.**

**THE TAIF ROW IS THE IMPORTANT ONE AND IT WAS ADDED 19 SEPTEMBER.** `drive10`
is a real mountain drive — Jeddah to Taif and back, two hours — and it is the
drive this project had been saying it did not have. The ambient channel proves
the altitude without a barometer: **31.5 °C at the start, 20.5 °C at minute 50,
34.5 °C at the end.** Sea level, up, and back down.

**It does not bind. It does not come close. 797.6 °C, 52 K short, zero seconds
above the trigger in 119.4 minutes.**

And the driver was not gentle. Measured off the same replay:

| | |
|---|---|
| above 140 km/h | 15 s |
| above 160 km/h | **5 s** |
| peak speed | 167 km/h |
| turbine median at 160+ km/h | **667.8 °C** |
| **where the peak actually happened** | **137 km/h at 5792 rpm, minute 13.5** |

**The hottest moment of the Taif drive was an acceleration, not the climb and
not the top speed** — a low gear at high rpm, held briefly. Every one of those
bursts is short, and the housing has a ~50 s time constant, so none of them
lands. The 160 km/h stretch lasted five seconds and ran *cooler* than the
peak.

**This is load-per-cycle and road power for the fourth time**, after
`12 % @ 90` beating `4 % @ 150`, SAE J2807's slow heavy climb, and the real
gearbox running hotter than the invented one. A mountain road taken at 59 to
90 km/h asks 40–50 kW; the locked scenario asks **88.7 kW for twelve
uninterrupted minutes**. Altitude does not heat a turbine. Sustained power
does.

**What this settles, and it is worth more than the row.** The obvious objection
to the locked scenario — that 12 % at 130 km/h is contrived — now has a
measured answer: **the hardest real climb we have recorded is 86 K cooler than
it.** The scenario is deliberately above real driving, and that is a stated
design choice rather than an accident.

*(The synthetic climb figure quoted in the next paragraph, 812 C, is the
pre-gearbox one. On the real ZF 8HP51 the same scenario reaches 884 C. See the
19 September checkpoint.)* <!-- RETIRED-OK: 812 -->

<!-- RETIRED-OK: 812, 38, 78 -->
The synthetic climb reaches 812 C and misses by 38 K, so **the car's own driving
gets 78 K hotter than the scenario written to stress it.**

Two conclusions, and they pull in opposite directions — state both:

- *(17 Sep, pre-gearbox. Since done: the scenario was rebuilt at 12 % /
  130 km/h and binds by ~34 K, peak 884 C against 850 C. The Do-NOT-lower-the-
  limit half still stands.)* **The scenario is too mild, not the trigger too
  high.** Rebuild it from measured driving. Do NOT lower the limit: 1123 K is already 80 K more
  conservative than the 930 C pre-turbine enrichment limit REFERENCES.md cites
  (Conway et al., SAE 2018-01-1423, p. 10), and moving it is turning the one
  knob the audit named. *(Corrected 8 October: the "80 K more conservative"
  half is mistake 23 -- a housing temperature set against a gas temperature.
  Like for like the knee is 984 C of gas, 54 K HOTTER than Conway's limit. The
  "do not turn the knob after seeing results" half stands; whether the knee
  moves is decision 9 of results/VALIDATION_DECISIONS.md, before training.)*
- **0.206 % is itself a result about H/tau, and it belongs in the thesis.** On
  this vehicle, in this driving, the protected component is near its limit a
  fifth of one percent of the time. That is a statement about how much preview
  could be worth HERE, and it is exactly the kind of answer the criterion exists
  to give.

  **The caveat that used to close this bullet is now RETRACTED, and the
  retraction is a stronger result than the caveat.** It read: *"it is not a
  measurement of the sustained-climb duty cycle the project targets, because
  no logged drive is one."* Since 19 September one is — `drive10`, the Taif
  run, two hours of real mountain driving. **It reaches 797.6 °C and spends
  zero seconds above the trigger.** So the sentence to write in the thesis is
  no longer "we have no sustained climb"; it is **"we have one, and it does
  not bind"** — which is a measurement rather than a gap.

  <!-- RETIRED-OK: 0.351, 172.6 -- naming the superseded pair IS the sentence -->
  Adding it moved the figure from 0.351 % over 172.6 minutes to **0.206 % over
  292.0 minutes**, because the numerator did not move at all: Taif contributed
  119.4 minutes and **not one second** above the limit.

#### A ROLLING ROAD MAKES PREVIEW WORSE, NOT BETTER. 18 September

Once the scenario binds, the obvious next question is whether preview was losing
because the road has only ONE change in it -- flat for three minutes, then a
constant grade, so 30 s of lookahead buys a single head start in 720 s. Tested by
alternating the grade about the same 12 % mean at the same 130 km/h, sweeping only
how fast it alternates. Neither bound is chosen for effect: 2 % is the policies'
own deadband (`grade_now > 0.02`) and 16 % is engine headroom, 471 Nm of 500.

| road period | baseline | grade-now | predictive | preview edge |
|---|---|---|---|---|
| constant | 1402.0 | 697.3 | 705.7 | −0.6 pts |
| 60 s | 1395.4 | 992.9 | 1025.4 | **−2.3 pts** |
| 120 s | 937.6 | 655.1 | 674.0 | −2.0 pts |
| 240 s | 754.5 | 502.3 | 514.0 | −1.5 pts |
| 480 s | 791.9 | 473.5 | 478.2 | −0.6 pts |

**The faster the road varies, the WORSE preview does.** The hypothesis was the
opposite and it is refuted.

**THE MECHANISM IS ONE LINE, AND IT IS THE POLICY, NOT THE INFORMATION.**
`check_premise.p_predictive` takes `max(preview[+15 s], preview[+30 s])`, so on a
road that keeps climbing again there is always a steep section in view and the
policy protects almost continuously -- including through the easy sections, where
protection costs and buys nothing. It is a driver who brakes for a red light
half a kilometre early. **Preview is not what loses here; using preview as a
worst-case-ahead maximum is.**

**FIRST ATTEMPT AT THIS SWEEP WAS BLIND, and the failure is worth more than the
row it produced.** It alternated 8 % ↔ 16 %, and both policies normalise grade as
`clip(grade/0.08, 0, 1)` -- 8 % gives 1.0 and 16 % gives 1.0 after the clip. The
road varied and NEITHER POLICY COULD SEE IT. Every row printed −0.1 points, which
looked like a finding and was zero information. AUDIT.md C3's lesson one level
down: a test that cannot see cannot measure, exactly as a test that cannot fail
cannot confirm.

**What this settles, and it is the useful part.** Five scenarios, three
hand-written policies, and preview loses in all of them -- by a margin that moves
with a formatting choice inside one policy. **The question "is preview worth
acquiring" cannot be answered by hand-written policies at all.** That is
AUDIT.md C3's own sentence, now measured rather than argued, and it means Phase D
is not one route to the result. It is the only one.

#### The published towing standard was tried, and it does NOT bind. 18 September

This file and README both name "a published towing cycle" as a legitimate source
for the new scenario. **It was looked up, implemented and measured, and it is the
wrong standard for this vehicle.** Recorded so nobody spends the afternoon again.

`SAE J2807` FEB2016 section 4.3.5, read off the standard's own PDF rather than a
summary: Arizona SR 68, **18.3 km (11.4 miles)**, grade **0–7 %** (Figure 2, GPS
data 11/2004), minimum speed **64.4 km/h (40 mph)**, minimum ambient **37.8 °C
(100 °F)**, air conditioning at maximum. Run with `Vehicle.mass` swept, neutral
policy:

| trailer kg | peak turbine C | vs trigger | peak torque Nm |
|---|---|---|---|
| 0 | 432.4 | −417.5 | 140 |
| 1000 | 587.0 | −262.9 | 224 |
| **2000** | **756.3** | **−93.5** | **308** |

**Two tonnes of trailer is still 94 K short**, and extrapolating puts the
crossing near four tonnes behind a 1520 kg sports car. Do not pursue it.

**WHY IT FAILS IS WORTH MORE THAN THE FAILURE, and it redirects the search.**
Compare the last row with the standard climb: 308 Nm → 756 °C against 297 Nm →
812 °C. **Nearly the same torque, 56 K apart.** The turbine node is heated by
`ua_gas_turb · mdot_exh · (egt − t_turb)`, so **the housing is heated by EXHAUST
FLOW, not by torque.** J2807 is a truck standard run at truck speeds: 40 mph puts
the engine at low speed and low airflow, so a heavily loaded engine grinding
slowly uphill produces a *cool* turbine.

**WHAT MOVES IT IS ROAD POWER — and a first reading of this measurement said
"speed, not grade", which the next sweep refuted within the hour.** Both axes
work. Neutral policy, 42 °C, 12 min:

| grade | km/h | peak turbine C | vs trigger |
|---|---|---|---|
| 12 % | 90 | 756.0 | −93.8 |
| 12 % | 110 | 812.3 | −37.6 |
| **12 %** | **130** | **899.4** | **+49.5** |
| **12 %** | **150** | **942.6** | **+92.7** |
| 7 % | 130 | 758.8 | −91.0 |
| 7 % | 150 | 820.4 | −29.5 |
| **16 %** | **110** | **906.2** | **+56.3** |
| 4 % | 150 | 708.5 | −141.4 |

**Three combinations bind, and the boundary is near 12 % at ~120 km/h.** The two
cleanest rows are the argument: 12 % at 130 km/h and 16 % at 110 km/h demand
**88.7 and 88.5 kW** of road power and reach **899 and 906 °C** — different
grade, different speed, same power, same temperature. **Do not promote that to a
law:** 12 % at 90 km/h (54.7 kW → 756 °C) is HOTTER than 4 % at 150 km/h
(60.4 kW → 709 °C), because the slower row sits at 2018 rpm against 2790 and so
runs a higher load per cycle and a hotter EGT. Flow and EGT both enter
`ua_gas_turb·ṁ_exh·(EGT − T_turb)`, and only the measurement settles a case.

That is why J2807 fails: 40 mph at 0–7 %, even behind two tonnes, is a modest
road power however much torque the trailer asks for.

**Two cautions from doing this.** The web summaries of J2807 report "11.4" as a
PERCENT GRADE; it is the LENGTH IN MILES, and only opening the standard settled
it. And the first sweep's "peak torque" column was measuring the launch
transient from rest, not the climb, which is why two different rows showed the
same number — it was deleted rather than explained.

<!-- RETIRED-OK -->
*(One caveat, stated rather than buried: the J2807 runs above used the standard's
37.8 °C, while the project scenario uses 42 °C. The gap is not the ambient — the
turbine is gas-heated and barely sees it — but the comparison is not
temperature-matched and should not be quoted as though it were.)*

---


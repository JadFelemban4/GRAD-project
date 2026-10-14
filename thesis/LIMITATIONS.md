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


---

## Known limitations to state in the thesis, not fix quietly

- **Altitude is not modelled.** The scored climb rises 2 340 m in 720 s, but
  `p_baro` is a fixed 101.3 kPa that the plant never reads: compressor inlet,
  boost ceiling and exhaust backpressure all see sea-level air throughout. A
  standard atmosphere would give about 76 kPa at the top, and colder air. The
  scenario is sustained heavy load at sea level — say that, and do not describe
  it as a mountain.
- **The boosted inversion is now within 2 % of the car, and the old 28 % gap
  was the charge temperature, not the breathing model.** See mistake 13. What
  remains uncertain under boost is the MAF ceiling at 1020 kg/h and the logger's
  round-robin sampling, which pairs air mass with pressure taken seconds apart.
- **There is NO part-load test of `volumetric_efficiency()` against this car.**
  Both logged pressure channels sit before the throttle, so there is nothing to
  compare a modelled manifold pressure against at part load. The load residual
  cannot serve — it cancels `eta_v` entirely (mistake 12). State this plainly
  rather than letting the 1.4 % imply coverage it does not have.

- **Peak power is not a prediction.** Manifold pressure is an input.
  `plant.boost_ceiling_kpa` now bounds it to what the car was observed to do,
  but an operating line is not a compressor map — no efficiency islands, no
  speed lines, because the car has no turbo speed sensor and no pre-intercooler
  temperature.
- **Two residuals, both true, and the fitted one fits better.** Over the 26
  pooled points that survive the window checks, 30–75 kPa: **1.4 % with the
  derived k = 0.831 and zero free parameters**, **1.1 % with the fitted
  k = 0.839 and one**. Dropping the parameter makes the residual RISE, which is
  the honest direction — one free parameter should fit better than none. Quote
  the derived 1.4 % and say that it costs nothing; quote the fitted 1.1 % only
  next to the parameter it spends. And read mistake 12 first: neither number
  tests the breathing model.
- **Vehicle validation covers 30–75 kPa only.** Steady points need steady
  driving, and steady driving is light-load driving. The boosted region is
  validated against published correlations.
- **The compressor envelope is unmeasured above 0.314 kg/s corrected**, because
  that is where the MAF channel saturates. The 0.18–0.27 kg/s hole is filled;
  0.33–0.36 is still empty and no drive can fill it with this sensor.
  *(0.303 and 0.314 appear in different sections of `validation_table.md` for
  the same quantity under two different filters — AUDIT.md M5. `fit_envelope.py`
  prints the figure with the filter that produced it.)*
- **THE TOP OF THE ENVELOPE RESTS ON FOUR TO FIVE INDEPENDENT READINGS.** This
  is the sharpest consequence of AUDIT.md H4 and it was invisible while the
  table quoted row counts. `python fit_envelope.py` prints both:

  | flow kg/s | PR p95 | rows | **independent readings** |
  |---|---|---|---|
  | 0.225 | 2.415 | 36 | **5** |
  | 0.255 | 2.342 | 40 | **5** |
  | 0.285 | 2.515 | 53 | **4** |
  | 0.315 | 2.473 | 47 | **5** |

  **"PR 2.52", the number `plant.boost_ceiling_kpa` is built on and every boost
  claim inherits, is four measurements.** The low-flow bins are genuinely dense
  (1120 readings in the first), so the envelope is well determined where it does
  not matter and barely determined where it does. Say so in Chapter 3, and do
  not quote the top bins to three significant figures.
- **Turbine τ is 48.0 s on the climb, and it is ONE measurement, not two.**
  `validate.py` prints 48.0 s, inside the published 40–120 s band.

  This line used to say "`C/UA` gives 50.3 s; the step response gives 48.0 s",
  presenting two methods that nearly agree. **They are the same method.** The
  turbine node is decoupled from the block and oil (`thermal.py`), and
  `validate.py` holds fuel flow, exhaust flow and EGT CONSTANT for the whole
  step, so the response is an exact first-order exponential whose time constant
  IS `C/UA`. Perturbed in mistake 12's style — `c_turb` and `ua_gas_turb` each
  swept over three values — the step-response τ tracks analytic `C/UA` to within
  0.13 s in all nine cells. **The step response cannot corroborate C/UA; it
  recomputes it.** And the 50.3 s was `C/UA` at an exhaust flow of 112.5 g/s,
  the assumed constant `AUDIT.md` M12 condemned.

  **τ is also not one number.** Over the locked episode it runs from 40 to 239 s,
  a factor of six, because UA rises with exhaust flow: 48 s on the climb, 129 s
  on the flat approach. `app/estimator.py`'s table (50 s loaded, 151 s cruise,
  239 s idle) says the same. Quote τ with its operating point, always — that is
  mistake 15. And `c_turb = 6000 J/K` is ASSUMED, so every τ is an assumed
  number to within that constant.

  Corrected 22 September; see `results/PREREGISTRATION.md` limit 8.
  <!-- RETIRED-OK: 50.3, 39.5 -- the superseded figures, named so they are recognised -->
  The old 39.5 s figure came from the four-cylinder and is void.
- **The knock retard is measured, the baseline's cap is the right order, and
  THE PUBLISHED p99 IS UNDER RE-DERIVATION — do not quote it.**
  `Target ignition angle from torque intervention` minus `Actual ignition angle`
  gives the retard the ECU is applying. The figure this section used to state
  as settled was: steady gear (shifts and torque cuts removed, 10 896 samples),
  median 0°, **p99 9.8°**, more than 1° for 22 % of the time and more than 3°
  for 11 %. <!-- RETIRED-OK -->

  **Mistake 18 ordered it re-derived and 19 September did the work.** That
  filter used `Actual gear`, which clamps at 6, so it cannot see a 6→7 or 7→8
  shift and left those transients in. Re-derived from the gear INFERRED from
  rpm and road speed, over `data/master_samples.csv`, retard in [−5°, 45°],
  moving samples only:

  | gear filter | n | p95 | p99 | >1° | >3° |
  |---|---|---|---|---|---|
  | none | 15 780 | 13.50 | 21.75 | 27.4 % | 17.2 % |
  | steady CHANNEL gear | 15 654 | 12.75 | 21.75 | 27.3 % | 17.1 % |
  | **steady INFERRED gear** | **13 329** | **9.75** | **18.00** | **25.5 %** | **15.3 %** |

  The correction removes 2 325 further samples — the 6→7 and 7→8 shifts the
  clamped channel is blind to — and it is **not cosmetic**: p95 falls 12.75 →
  9.75 and p99 falls 21.75 → 18.00.

  **But this does not replace 9.8, because the shipped figure cannot be
  reproduced.** Neither its p99 nor its n = 10 896 comes out of the shipped
  data under a gear-steadiness filter alone, so the torque-cut half of the
  original filter is doing work that is not written down anywhere. Until
  whoever wrote it re-runs it with that filter stated, **the row has no
  quotable p99.**

  *(One hypothesis worth a single check and no more: the re-derived **p95** is
  **9.75**, which rounds to the 9.8 published as a **p99**. That would make the
  original a mislabelled percentile rather than a wrong filter. It is a
  coincidence, not a finding — do not write it down as one.)*

  What survives unchanged: `BaselineECU` caps its knock retard at 12°, which is
  the right order and slightly conservative rather than a strawman, on every
  filter above. **Do not use the raw channel difference** — unfiltered it
  reaches 45°, which is a gearshift torque cut, not knock.
- **The radiator is not identifiable ON THIS CAR, and the census proves it.**
  Every water-pump channel the vehicle offers is all-zero, so there is no
  coolant-flow signal and `Q = ṁ·cp·ΔT` cannot be formed. `Actual value of
  electric fan` and `Duty cycle electric fan` are also all-zero; `Setpoint
  electric fan` is live but sits at 28–31 % for a whole drive. The thermostat
  regulating 88–99 % of the time is the second reason, not the only one.
  `ua_block_oil` **is** identified (800 W/K, from the measured oil-minus-coolant
  gap) and has been changed; the radiator parameters were deliberately left
  alone. See `logs/CHANNEL_CENSUS.md`.

  A constrained fit was attempted on 8 September with 55 minutes at 45 °C
  ambient and far more excitation, and **it fails too**: R² = 0.157 with a
  negative ram coefficient. The only observable is ΔT across the radiator, and
  ΔT = Q/ṁ — both terms rise with road speed, so ΔT carries almost no
  information about UA. Assuming constant flow is not a mild approximation here.
  Stop trying; state it as a limitation.

  **28 September, evening: its SIZE is now derived, its SPLIT is not.** With the
  block's capacity pinned by 683640a0's warm-up, the stretches where the coolant
  climbs above its regulated point carry the radiator's overall size, and
  `derive_params.py` scales the reasoned 300 / 60 / 700 split by one factor
  (x1.42). The three terms still cannot be told apart, and the heat-management
  valve's control law (82-84 C after load on hot afternoons, 97-99 C on
  drive10's high-rpm stretch) is not modelled.
- **THE OIL BAND IS SUPPORTED BY OUR OWN CAR, AND THE MODEL MISSES IT LOW.**
  This is the most valuable thing `drive10` delivered (18 September).
  <!-- RETIRED-OK: 107 -->
  The hottest oil in the first nine drives was 107 °C, *below* the published
  115–140 °C band; `drive10` reaches **117 °C**, with **1320 rows above 110 °C
  and 60 above 115 °C**, so the band's lower end is inside our own measurement.
  Above 117 °C is still extrapolation.

  `validate.py` row 8 replays drive10 and compares model and car over the car's
  hottest ten minutes: **97.0 °C against 103–111 °C**. Row 9 finds the car's oil
  time constant at 70–100 s against the model's 60 s. Both are outside after the
  oil node was re-structured and derived (mistake 20), and the miss is measured,
  not tuned in: of row 8's 12.0 K, 4.6 K is the coolant (the car's
  heat-management valve holds it higher than the model's regulation) and 7.3 K
  is the oil node itself (`model_vs_data.row8_split`). Say it that way in the
  thesis. Drive A, logged with oil AND ambient, is the data that can move it.
- **Eleven drives in the manifest, eight with usable samples.** `3f64372e` and `f51686d7` are under
  a minute each and contain no warm running window; `fb988991` is a census log
  whose windows are all rejected for span or logger gaps (mistake 8), so it
  carries samples but contributes **zero** operating points, and drive B logged
  no spark or lambda, so it adds none either. Quote it as "eleven drives, 321.7
  minutes, eight carrying samples, 26 distinct operating points".

  <!-- RETIRED-OK: 113, 5, 7 -->
  This line read "seven drives, 113 minutes, five carrying samples" until
  9 September. It was written before `7475b5d7` arrived and simply never
  updated, while the current-state table at the top of this file, `verify_docs.py`
  and `build_dataset.py` all moved on. **A limitations section goes stale the
  same way a results section does, and nobody re-reads it.** `verify_docs.py`
  checks the figures in the DOCUMENTS; it does not check the prose in this file.
- **Steady points are steady for fast quantities only.** The 60 s window is
  fully settled for air, lambda, spark and manifold pressure, and reaches just
  **71 %** of a turbine thermal step (τ = 48 s). Never validate a thermal
  quantity at a steady point; drive `thermal.py` over the whole log instead.
- **Enrichment uses dwell above the 180 kPa gate as a proxy** for turbine inlet
  temperature, which this vehicle does not expose. (`ENR_LOAD` = 180 kPa on the
  corrected charge-temperature scale of mistake 13.) **Since 28 September the
  dwell thresholds are derived from the car on the timestamp axis**
  (`derive_params.py`: 1.5 → 3.0 s, were 2 → 9 s on the retired row-count
  axis), and eight of the nine cells are within 0.02 of the car. **The weakest
  cell is 3500–4500 rpm at long dwell, 0.033 lean** — the speed band and depth
  are held at the 8 September fit because ~100 genuine readings cannot identify
  them (REFERENCES.md 4b).
  <!-- RETIRED-OK -->
  *(Until the evening of 28 September the weakest cell was 4500–7000 rpm at
  4–8 s dwell: car 0.83, model 0.906 — 0.076 lean.)*
  <!-- RETIRED-OK -->
  *(Until 27 September this line said the weakest cell was 3500–4500 rpm at
  long dwell and that every cell was within 0.027. The 4500–7000 rpm, 4–8 s cell
  had been tabulated at 0.87 on the row-count dwell axis AUDIT.md H3 retired,
  and was never regenerated. `ENR_DWELL_LO/HI` were fitted on that axis too and
  are NOT refitted: the cell holds a few dozen independent readings at most.
  It does not touch Phase D — the locked climb runs 178 kPa at 2706 rpm and
  enrichment needs 180 kPa and 3300 rpm.)*
  <!-- RETIRED-OK -->
  *(This line read "short dwell, n=29, observed 0.94, model 1.00" until
  9 September — the seven-drive
  version, in which that cell held only 29 samples and read 0.94 by chance.
  `base_lambda()`'s docstring had the corrected cell all along.)*
- **AND ON THE LOCKED SCENARIO THE BASELINE NEVER ENRICHES AT ALL.** Measured
  19 September 2026, neutral policy, 12 % at 130 km/h, 42 °C, 720 s:
  **λ = 1.000 on every single step of the episode.** This is not a defect and
  it is not the gate: the climb sits at **2706 rpm** (7th gear), and
  `base_lambda` returns 1.000 there at **any** load and **any** dwell —
  178 kPa or 220 kPa, 0 s or 30 s, all 1.000. The first enrichment appears at
  3600 rpm. That is the map being faithful to the car, which mistake 4 records
  as not enriching below about 3300 rpm however long boost is held.

  **Say this in Chapter 4, because it changes what the ablation measures.**
  Enrichment is one of the four protection levers and one of the five actions
  the agent controls (action 1, λ trim, down to −0.15 → λ 0.85). On this
  scenario **the production-representative baseline does not use it and the
  agent can**, so part of any margin the agent shows is a lever the ECU would
  not have pulled here — not anticipation. The ablation is sighted-against-
  blinded and both agents hold that same lever, so it does not corrupt the
  preview comparison; it does inflate every "cuts damage N %" figure quoted
  against the baseline.

  The other protection paths ARE live on this scenario and were checked the
  same run: thermostat open 0.20 → 0.70 and never shut (~100 kW rejected),
  cooling fan on its 0.4 rung for 97.4 % of the climb, coolant pump at 1.0,
  charge cooler taking 42 °C ambient to 56.9 °C, knock retard peaking at 3.2°
  and active 3.8 % of the time.
- **The eleven validation bands are engineering-judgement bands, not sourced
  ones.** `validate.py` scores the model against eleven "published" ranges,
  and until 12 September the only citation behind any of them was the word
  "Heywood" in a code comment. `REFERENCES.md` now records, row by row, which
  bands have been checked against an opened source and which have not, and
  sorts them into general engine physics (a textbook settles them), facts
  specific to the B58 (only BMW or Toyota documentation can), and one band
  with no support at all: the knock-limited spark, row 4. Until a row is
  marked CONFIRMED there, describe its band in the thesis as engineering
  judgement. Never promote a row from memory; open the source and write down
  the page.
- **`c_turb` = 6000 J/K is ASSUMED, not measured, and it sets τ.** The
  turbine-housing heat capacity (how much heat it takes to warm the housing
  by one degree) divided by its heat-transfer coefficient (how fast heat gets
  in and out) is the housing's time constant τ, and τ is the denominator of
  H/τ, the project's whole claim. `generality_test.py` sweeps `c_turb` from
  800 to 60 000 J/K, a factor of 75, on purpose: the claim is about the RATIO
  H/τ, not about one engine's heat capacity, so if preview value collapses
  onto one curve across that sweep the exact value of `c_turb` does not
  matter. State this explicitly in Chapter 3. Unstated, it reads as an
  unexamined assumption; stated, it is the reason the experiment is designed
  the way it is. See `REFERENCES.md` section 4.
- **The B58 has no thermostat, so the 88 °C in `thermal.py` is a modelling
  equivalent.** BMW's own B58 training document (ST1505, 2015, section 4.2)
  says the conventional thermostat "is replaced by a so-called heat management
  module": a motor-driven rotary valve positioned by the engine computer from
  the coolant and cylinder-head temperatures, with no wax element and no
  published opening temperature. `t_stat_open` = 88 °C is identified from the
  car's own coolant channel (regulated 88–97 °C in every log) and cannot be
  cited to BMW. It is also a third reason the radiator cannot be identified
  from the logs: the radiator branch opening is a commanded valve angle, not a
  function of coolant temperature. See `REFERENCES.md` section 2.
- **The compression ratio question is SETTLED: this is the 285 kW car, so
  10.2:1 is right.** Confirmed by the team on 19 September 2026 — the car is the
  285 kW / ~386 hp B58B30O1, which is the engine every manufacturer sheet prints
  10.2:1 beside, and which is what `plant.py` runs. The 11.0:1 that Toyota UK's
  sheets print belongs to the **250 kW / 340 PS** European variant and does not
  apply here.

  <!-- RETIRED-OK -->
  This entry read "Nobody has yet recorded which version this car is" until
  19 September, and warned that if it were the 250 kW car the knock model would
  be running the wrong compression ratio. It is not, and the knock model's
  compression ratio is correct. **That does not rescue the knock model** — see
  the section below: its integral still has no detectable relationship with the
  car's own retard, and now that the compression ratio is excluded as the
  explanation, the remaining candidates are the Douaud-Eyzat tuning, the charge
  temperature or pressure under boost, or the assumption that `Actual ignition
  angle` is the final commanded angle. **Excluding a suspect is progress; it is
  not a fix.**


### THE KNOCK MODEL IS NOT VALIDATED AGAINST THIS CAR, AND THE DATA SAYS SO

Added 16 September 2026, from AUDIT.md H5. This is a negative result and it is
worth more than most of the positive ones.

The car publishes its own knock response: `Target ignition angle from torque
intervention` minus `Actual ignition angle` is the retard the ECU is applying.
Replaying `7475b5d7` through the app -- which feeds the car's MEASURED spark and
lambda into `predict()` -- gives a model knock integral to compare against it,
sample for sample. Over 13 592 paired samples:

| | model knock integral | car's own retard |
|---|---|---|
| median | 0.464 | 0.00 deg |
| p95 | 0.732 | 6.75 deg |
| max | 3.446 | 44.25 deg |
| active | KI > 0.85 on **1.6 %** | retard > 1 deg on **25.5 %** |

**Correlation between them: −0.149.** Where the model says the engine is
knocking, the car's median retard is 0 deg. Where the model says it is not, the
car's median retard is also 0 deg. **The two have no detectable relationship.**

**What that costs, stated rather than hidden:**

- `validate.py`'s knock-limited-spark row (11 deg at 3000 rpm / 200 kPa) is
  inside a band that REFERENCES.md already marks unsourced, and it is now also
  unsupported by the car's own behaviour. It still counts toward the literature rows' 6 of 7.
- `BaselineECU.knock_limited_spark` and the `40·max(0, KI − 0.85)²` term in the
  damage function rest on the same model.
- `check_map.py`'s entire knock-limited surface is model-internal.

**Do not quote a knock-limited spark or a knock damage term as calibrated.** One
of three things is wrong and the data here cannot say which: the Douaud-Eyzat
integral is mis-tuned for this engine, the modelled charge temperature or
inverted pressure are off under boost, or `Actual ignition angle` is not the
final commanded angle. Settling it needs a deliberate drive, not another
re-analysis of these logs.

**Why this did not show up before:** the premise numbers never exercised the
knock term, because the baseline was over-retarded by the scheduling error of
AUDIT.md C2 and sat at KI 0.3-0.4. Fixing C2 is what made the term live.

**28 September: this test could not have seen knock, so it is UNTESTED, not
refuted.** Counting genuine readings (AUDIT.md H4) instead of rows: the drive
holds **404 target and 410 actual ignition readings in 55 minutes**, one every
~8 s, and a third of the pairs in a row were read more than a second apart. A
knock retard lasts a second or two, so most were never sampled, and the ones
that were are paired with the wrong moment. Filtering to steady inferred gear
does not rescue it — above 120 kPa only 106 rows even have an inferable gear,
because engine speed and road speed were themselves read seconds apart. This is
mistake 13b exactly: the compressor-outlet hypothesis read +0.35 on slow data
and +0.95 once `pull01` logged 7 channels. The table above stands as a
measurement of THIS drive; it is not evidence against Douaud-Eyzat.

**What it costs Phase D, measured.** On the hand-written policies the knock
term is **6.4 % of the baseline's damage and 11–12 % of the protecting
policies'**, and it is all of preview's −0.4 against current-grade: on turbine
and oil damage alone the two tie. Report both until drive C settles it.

### Limits the LIVE APP adds, and they are the simulator's limits plus three

The app reuses `plant.predict`, `plant.map_from_airflow`,
`plant.charge_temperature` and `thermal.ThermalNetwork` **unchanged**, so every
limitation above applies to it word for word. It adds these:

- **The turbine temperature it displays is a model output, not a reading, and
  its heat capacity is an ASSUMED number.** `c_turb = 6000 J/K` is marked
  ASSUMED in `thermal.py` and in REFERENCES.md section 4, and it is the constant
  that sets τ, which is the denominator of this project's central ratio. The UI
  says so on every screen and the thesis must too. **A number on a dashboard
  looks like a measurement to everyone who did not write it.**
- **The warm-start bound holds under steady operation only.** Connect within a
  few tens of seconds of lifting off a hard pull and the housing can be hotter
  than the gas now flowing through it, so the upper bound is too low. There is
  no channel on this car that would catch it. See mistake 15.
- **The mismatch detector only has an opinion at wide-open throttle.** Below a
  pressure ratio of 1.8 the two quantities it compares sit on opposite sides of
  the throttle plate (mistake 14), so it is silent there — which means **a boost
  leak on a car that is never driven hard will not be found by it.** That is a
  coverage limit, not a bug, and it is the honest consequence of the only
  pressure channels this vehicle publishes being pre-throttle.
- **The alert counts are not evidence.** 14 thermal / 0 mismatch / 19 novel on
  `7475b5d7` is a property of thresholds this project chose, pinned so that a
  regression is visible. It is not a measurement of the car.

### THE 14 SEPTEMBER AUDIT FOUND SIX BUGS IN `app/` THAT ITS OWN TESTS PASSED — ALL SIX NOW FIXED

`AUDIT.md` is a full technical review of this branch. **Read it before quoting
anything the app prints.** It was the most important document of its week, and
it disagreed with the confident tone of the section above.

Six of its findings were against `app/`, and the app's own suite reported 46 of
46 while every one of them was live. That is the point worth internalising: **a test
suite pins the behaviour it was written to pin, and cannot see a defect nobody
thought to look for.** The same lesson as mistake 11, one more level down.

| id | what | why it matters |
|---|---|---|
| **H8** | the modelled-lambda fallback can never enrich — `base_lambda` is called without `dwell_s`, so λ = 1.00 always | the modelled EGT runs **80–110 K hot** under a sustained pull, and that feeds the DRIVER-FACING thermal alerts. This is the worst of the six |
| **M11** | the block node free-runs although coolant is measured every sample | drifts **14 K** from the sensor on `7475b5d7`, and the oil node inherits it |
| **M10** | the thermal warning projects the trend LINEARLY 30 s ahead | the housing is a first-order node with τ 27–51 s, so it reaches 61–75 % of that. Five of ten warns on `7475b5d7` project to the limit but fall **20–110 K short** of it in the model's own dynamics. "Threshold in about N s" is a quantitative claim the model contradicts |
| **M9** | one missed barometric reading retires the mismatch detector for the session | `_last_poll` is advanced before the query rather than after, so a single NO DATA silences the detector 7–15 s later |
| **M8** | BimmerLink's placeholder zeros are parsed as measurements | the first rows of every log read coolant 0, so the seed can start the block at 273 K |
| **M7** | nothing in the test suite imports `app/server.py` | "36 of 36 pass" therefore says nothing about whether the product starts |

**ALL SIX ARE NOW FIXED**, and `AUDIT_FIXES.md` carries a row per finding
saying what moved.

Verified by running the suite, not by reading the response document: it reports
**49 of 49** (three new regressions over the old 46), and five of the six carry a
test named after the finding — `H8: the modelled lambda reaches 0.81 after a
sustained pull`, `M11: the modelled block equals the measured coolant`,
`M10: no time-to-threshold when the limit is unreachable`, `M8: leading coolant
zeros are not read as 0 C`, `M7: app.server imports and serves its three pages`.
**M9 is the exception**: it is fixed in `app/reader.py` (the comments at `:530`
and `:581` name it) but carries no test of its own, so it is the one of the six
that could silently regress.

<!-- RETIRED-OK: 890.6, 608.0 -- the app pins of 17 September; 873.1 and 604.8 on the merged physics -->
**What moved on 17 September, and it was small:** `7475b5d7`'s peak estimated
turbine went to **890.6 °C** from the 884.9 °C of mistake 15, and `pull01`'s to
**608.0 °C** from 593.7. Both rises were the H1 crank-angle correction, not the
app fixes — see `AUDIT_FIXES.md`. Since the merge the pins have moved again,
with the exhaust-flow fix: the Numbers section has the current ones.

**The lesson the section title still carries is the one worth keeping:** the
suite reported 46 of 46 while all six defects were live. **A test suite pins the
behaviour it was written to pin.** Every fix above ships with a regression test
that would have failed before it, which is the only reason the count went up.

**Three of the audit's CRITICAL findings are about the simulator, not the app,
and they matter more than anything in this section** — in particular C3, which
argues the 13.4-point preview advantage is protection depth and that the
ablation identity is guaranteed by construction. That goes to the project's
central claim.

**C3 IS NOW ADDRESSED, and the answer is a null.** C3's demand was precisely a
trained blinded agent raced against a trained sighted one, and that ran on
21–22 September: eight paired seeds, preregistered before any agent started.
**Preview is not significant** — 5 of 8 positive, mean +4.8 damage units, sign
test p = 0.3633, permutation p = 0.4922. The blinded agents were trained blind
rather than zeroed at evaluation, so the comparison could have failed, and
across eight pairs it did not separate from seed noise.

C1 and C2 remain where they were.
---


---

## Open, and honest about it

### PHASE D, D2 AND C4 WERE SCORED IN A DISCRETISATION THEY DID NOT LEARN IN. Measured 19 Sep

`dt` was not consistent across this project until 27 September. Ghassan logged
it as an open question on 19 September; this measures it.

```
train.py         dt = 0.2   duration 900 s   ->  4500 steps per episode
evaluate.py      dt = 1.0   duration 720 s   ->   720 steps per episode
check_premise    dt = 1.0
generality_test  dt = 2.0
```

**The preview horizon is NOT the problem** — `_preview()` computes
`int(h / self.dt)`, so the 2/5/15/30 s horizons are the same wall-clock
horizons at every `dt`. That was checked first, because H is the numerator of
this project's central ratio.

**The damage integral IS.** Hand-written policies, locked scenario, 720 s,
identical seed and weights, the only difference being the step:

<!-- RETIRED-OK: 900.9 -->
| policy | dt = 1.0 | dt = 0.2 | cuts vs baseline |
|---|---|---|---|
| baseline ECU | 959.8 | 900.9 | — |
| current-grade | 633.2 | 567.8 | **34.0 % → 37.0 %** |
| reactive | 679.0 | 622.5 | **29.3 % → 30.9 %** |

Peak turbine is **dt-invariant** — 884.0 °C at both steps, 860.5 for
current-grade at both — and fuel moves 0.2 %. The physics is not in question.
The accumulated damage is, and so is everything computed from it.

**The sharpest form: the GAP between two fixed policies moves from 4.8 to 6.1
points, 1.3 points, on the step size alone.** Every preview effect this project
has measured with hand-written policies is between 0.4 and 2.3 points.
**`dt` sits inside the signal, not underneath it.**

The cause is one loop. `_track_torque`'s PI accumulates per STEP with no `dt` in
it, so it advances five times per second at 0.2 and once at 1.0. This is the
same defect AUDIT.md M16 fixed for `SLEW`, in the loop M16 did not touch.

**What this does and does not do to the ablation.** In Phase D, D2 and C4 the
sighted and the blinded agent both trained at 0.2 and were scored at 1.0, so the
handicap is shared and
is not a bias by construction. Whether it is SYMMETRIC is unmeasured, and there
is a reason to doubt it: a policy whose entire value is timing may lose more to
a coarser step than one with no preview at all. **Quote no ablation figure
without this paragraph beside it**, and note that the hand-written comparators
are unaffected — they have no `dt`, they are functions of the current state.

Three ways out were listed: train at 1.0 to match the protocol; score at 0.2 to
match the training; or leave it and state it as a limitation. **The team chose
the first on 27 September:** `train.py` passes dt = 1.0 for the terrain design
(`runs/terrain_dt1/`), so the 29 September agents and every run after them learn
in the step they are scored in. For Phase D, D2 and C4 this section stays a
stated limitation — written down rather than discovered by an examiner.

**Phase F's H2b threshold rule does not survive the correct engine.** It sets
the constraint at the 80th percentile of the unprotected trace, which assumes
the temperature spends a minority of the episode near its peak. The standard
scenario is a sustained climb: nine of its twelve minutes sit at the top, so p80
lands on the peak and the top three rows of the sweep saturate at 100 % for both
policies.

`check_premise.py` hit the same wall and solved it by anchoring the trigger to
the **damage model** instead — 1123 K, the knee of `exp((t_turb − 1123)/45)`,
above which damage stops being negligible. That is a statement about the
component rather than about one episode, and it transfers between scenarios.
**`generality_test.py` now imports the same constant** —
`engine_env.TURB_PROTECT_K` — so the two experiments cannot report different
protection limits. Until H2b's percentile rule is replaced, use the fixed-limit
H2 table — but **those figures are void too** (AUDIT.md C1: the whole sweep was
scored against the same cooling-disabled baseline, and M12: the τ axis assumed
112.5 g/s of exhaust where the climb makes about 103, so every τ was ~7 % low).
Re-run `generality_test.py` and read what it prints.

Those numbers were 0.0 / 0.1 / 0.2 at the old 930 K trigger. **Nothing about the
plant changed — only the threshold.** Report the threshold with every preview
figure; a preview advantage quoted without the limit it was measured against is
not a result.

---


# Validation table

Regenerate with `python validate.py` (plant, ~4 min) and

```
python build_dataset.py "logs/raw/*.csv"
python compare_log.py data/master_points.csv
```

**Do not edit `plant.py` or `thermal.py` without re-running both and updating this file.**

Last regenerated: **28 September 2026 — rows 8–11 (oil and coolant) now scored
against our own logs.** `validate.py` returns **7 of 11**: 6 of 7 against
literature, 1 of 4 against the car. Section A says how each car band is built.
Before that: 11 September, after the charge-temperature correction (and, before
it, the engine-geometry correction).

<!-- RETIRED-OK: dated record of the 16 September re-check -->
**Re-checked 16 September 2026 and UNCHANGED.** `validate.py` still returns
**8 of 11** inside band with identical values, so nothing in this table has been
rewritten. Two things happened around it that a reader will otherwise wonder
about:

- **The dataset grew to ten drives, 295.0 minutes**, because `pull01` arrived.
  It contributes **zero samples and zero operating points** — no coolant
  channel, so the warm-sample filter excludes it — so not one figure here moves.
  Note the three drive counts are different and all correct: **nine** logged,
  **six** carrying samples, **eight** behind the fitted calibrations. This table
  is built on the sample set, not the manifest.
- **A live app now exists** (`app/`) that runs this same plant and thermal
  network against a real-time stream. It **inherits this table, misses and all**,
  and adds no evidence to it. Its estimated turbine temperature is a model
  output resting on an ASSUMED heat capacity (REFERENCES.md section 4) and the
  vehicle publishes nothing to check it against, so it does not and cannot
  appear as a validated quantity here.


**Regenerated 16 September 2026 at `plant.DTHETA_DEG = 0.25`.** The crank-angle
step was 0.5 deg with no convergence study behind it, and the model is not
converged there: every EGT it reported was **14-21 K low** (AUDIT.md H1). The
rows above are at the finer step, so the cruise-band EGT maximum moved
777.3 -> 787.7 C - **further outside its band, not closer**, which is the honest
direction and is why the step was not left alone. The residual discretisation
error at 0.25 deg is about **7 K of EGT and 0.25 % of torque**; do not quote
these rows to finer precision than that. `validate.test_convergence()` fails if
halving the step moves a headline by more than that.

---

## Read this before quoting any earlier version of this table

Until 8 September the simulation ran a **2.0 L inline-four**, not the 3.0 L
inline-six in the car. `plant.Geometry` defaulted to a generic 1998 cc I4 and
`b58()` was an opt-in override that **no call site ever used** — every
`run_cycle()` call in the repository omitted the geometry argument. Only
`predict()` and `map_from_airflow()` used the real engine.

Consequences, all now corrected:

- The Gymnasium environment, the premise check, the reward tests and the H/τ
  sweep all ran on a four-cylinder. Torque was 33 % low, air mass 33 % low.
- Ten of the eleven rows below were computed on that engine. Only the
  displacement row used `b58()`, so the table asserted 2997.5 cc in row 1 and
  then reported a 1998 cc engine in rows 2–11.
- Phase B was **not** affected. The vehicle comparison goes through
  `map_from_airflow()` and `predict()`, both of which used the B58 throughout.
  The load residual stands unchanged.

`Geometry()` and `b58()` now return the same object, and every call site passes
a geometry explicitly. Any figure from a document dated before 8 September that
did not come out of `compare_log.py` should be regenerated.

---

## A. The eleven rows — `validate.py`

Rows 1–7 are quantities no channel on this car can see — cylinder pressure,
brake efficiency, exhaust temperature, the turbine — so a published range is the
only yardstick. **Rows 8–11 are oil and coolant, which the car does log, and
since 28 September they are scored against bands computed from our own drives**
(`validate.check_against_car`, replays in `car_thermal.py`).

| # | Quantity | Model | Band | Status | Basis |
|---|---|---|---|---|---|
| 1 | Displacement | 2997.5 cc | 2990–3000 | inside | literature — REFERENCES.md §3 row 1 |
| 2 | MFB50 at MBT (2500 rpm, 60 kPa) | 8.5° aTDC | 8–10 | inside | literature — row 2 |
| 3 | Best BSFC, knock-feasible, λ=1 | 239.9 g/kWh | 235–260 | inside | literature — row 3 |
| 4 | Knock-limited spark (3000 rpm, 200 kPa) | 11.0° BTDC | 8–14 | inside | literature — row 4 |
| 5 | EGT, cruise band, minimum | 724.1 °C | 600–750 | inside | literature — row 5 |
| 6 | EGT, cruise band, maximum | 787.7 °C | 600–750 | **outside** | literature — row 6 |
| 7 | Turbine housing time constant | 48.0 s | 40–120 | inside | literature — row 7 |
| 8 | Oil, sustained load (drive10, hottest 10 min) | 96.4 °C | 103–111 | **outside** | **our car** — the car's interquartile range over that window |
| 9 | Oil apparent time constant (identified) | 14.0 s | 70–100 | **outside** | **our car** — identified on 4 of 5 drives |
| 10 | Coolant, regulated (synthetic climb) | 94.5 °C | 83.5–95.6 | inside | **our car** — warm coolant, 5th–95th percentile, all drives |
| 11 | Coolant, whole drive (drive10, free-running) | 88.4 °C | 91.8–94 | **outside** | **our car** — the car's interquartile range over the drive |

**7 of 11 inside: 6 of 7 against literature, 1 of 4 against our own car.** The
literature rows' sources and grades live in `REFERENCES.md` section 3 and only
there; an UNVERIFIED band is an engineering-judgement band in Chapter 3.

### How rows 8–11 are scored

Each rule was fixed before the model was scored against it.

- **The replay.** `thermal.py` is driven over a logged drive on a 1 s grid,
  **free-running** from a seed taken at the first real reading, with the fuel the
  car burned formed from two measured channels, air mass over (14.7 × λ). No
  combustion model is involved, so the replay captures the car's fuel cut on
  overrun, and it runs in seconds.
- **Row 8** uses drive10 — chosen because it is the only drive whose oil reaches
  the published 115–140 °C band, the longest, and logged with ten channels so
  oil is read every couple of seconds. The window is the 10 minutes where the
  CAR's rolling-median oil is highest; the band is the car's interquartile range
  there.
- **Row 9** identifies an apparent first-order time constant by one method
  (`car_thermal.identify_tau`) from the car's oil and from the model's, with the
  block pinned to the measured coolant. The method was checked first: on the
  model it recovers the analytic 14 s on every drive. A drive whose best fit
  sits at the edge of the candidate grid did not excite the oil enough to say —
  `3aca2ec1`, the steady cruise, is excluded that way. The band is the car's
  range over the other four.
- **Row 10** keeps the synthetic sustained climb and scores its settled coolant
  against the car's own warm range, instead of a band whose upper half was
  judgement.
- **Row 11** replaces a "regulation response" row whose 1–600 s band almost
  nothing could fail (AUDIT.md L10) with the whole of drive10 replayed.

### The misses

**EGT maximum, 787.7 °C against a 600–750 band** (literature). The band
describes moderate cruise. The test's own worst point is 2500 rpm at 100 kPa, and
the measured cruise range on this car is **30–75 kPa** — so that point is above
cruise for this engine, and ~790 °C port-exit at near-full naturally-aspirated
load is normal. The test point is mislabelled rather than the model being wrong,
but the band was not moved to make it pass.

**Oil, rows 8 and 9 — measured, and they agree with each other.** The car's
oil takes **70–100 s** to follow a change; the model's takes 14 s. And over
drive10's hottest ten minutes the car's oil sat at 103–111 °C while the model's
median was 96 °C. The node is too light and, on sustained load, too cool: its
oil follows the block within seconds, where the car's sump carries far more
heat. It is also what makes the model's oil spike on hard pulls (140 °C against
the car's 107 on 7475b5d7). Fitting it is drive A in `logs/DRIVE_PLAN.md`: the
logs we have pull the two assumed oil parameters opposite ways
(`model_vs_data.py`).

**Coolant over a whole drive, row 11.** Free-running, the model's coolant
settles about 4 K below the car's. The car holds 92–94 °C through cruise and
idle with its heat-management valve; the model's 88 °C thermostat stand-in lets
the block drift down at light load. Row 10 passes because under sustained load
the model's coolant (94.5 °C) sits inside the car's warm range. Both say the same
thing: the regulation point is right under load and too low at light load.

*(The literature bands these rows used to be scored against — 115–140 °C,
20–400 s, 88–108 °C, 1–600 s — are kept in REFERENCES.md section 3. The car's
own oil time constant, 70–100 s, sits inside the old 20–400 s band: the band was
right, and the model was not.)*

**A note on the two oil channels.** `Oil temperature after filter`, recorded
since 8 September, runs hotter than the `Oil temperature` channel the model is
compared with: +11.0 K median over a whole drive, and **+6.8 K at oil above
100 °C**. Until 28 September this was offered as a possible reconciliation of the
old literature miss — the synthetic climb's 110.2 °C plus 6.8 K is 117 °C, inside
115–140. Row 8 now compares the model against the `Oil temperature` channel on
the same drive, so the offset no longer bears on the table. It is not applied
anywhere. **Matching the car and missing a band is the better failure**; do not
raise the coupling to close a gap the data does not support.

Note the turbine constant now sits inside its band at 48.0 s, near the `C/UA`
analytic value of 50.3 s. <!-- RETIRED-OK -->
The old 39.5 s figure came from the four-cylinder.

---

## B. Against the vehicle — `compare_log.py`

Source: **ten drives, 295.0 minutes**, 3.52–6.63 Hz, 2023 GR Supra B58B30O1.
`build_dataset.py` finds **26 distinct operating points**, 30–75 kPa manifold
pressure, with the charge temperature modelled rather than read from the
pre-throttle sensor — see section E, limit 2, for why that sensor cannot be used.

| Comparison | Points | Result | Target | Status |
|---|---|---|---|---|
| Load residual, **k derived**, zero free parameters | 22 | **1.4 %** | < 15 % | **PASS** |
| Load residual, k fitted, one free parameter | 22 | 1.1 % | < 15 % | PASS |
| Normalisation constant k, fitted | — | 0.837 | — | one fitted scale factor |
| Normalisation constant k, derived | — | 0.831 | — | 269.6 / T_charge, nothing fitted |

**k is not a tuning parameter — it is a unit conversion, and we can derive it.**
Our load is normalised to 100 kPa at the modelled charge temperature; BMW's
"relative air filling" is normalised to the DIN reference state, 1013 mbar and
0 °C. Since ρ = P/(R·T), the ratio between the two is

    k = (100 / T_ch) ÷ (101.3 / 273.15) = (100 × 273.15 / 101.3) / T_ch
      = 269.6 / T_ch

The 269.6 is three **defined** constants — no measurement, no fit. Over the 22
points the modelled charge temperature runs 48–57 °C, 52 °C mean, so the constant
this expression produces averages 0.831 against a fitted 0.837.

**Report the direction honestly: dropping the free parameter makes the residual
RISE.** The fitted k scores **1.1 %** over the 23 points and the derived form
scores **1.4 %**, both at 30–75 kPa. That is what one free parameter is for.
Any earlier version of this table that described the derived form as the more
*accurate* one had the argument backwards, and an examiner will spot it in one
line of arithmetic.

**The argument for the derived form is falsifiability, not accuracy.** Nothing in
it was tuned, and unlike the fitted form it is blind-sensitive to the engine.
Force the geometry back to the old 2.0 L inline-four and the derived residual goes
to **48.1 %**, while the fitted residual still reports **1.1 %** — the fit absorbs
the wrong engine into its constant and returns a clean number either way. Had the
derived form been in place in August it would have caught the geometry error on
day one. That is the case for reporting it as the headline.

**Why the reference state is evidence rather than numerology.** The reference
temperature was the one thing we assumed. Had BMW normalised to 20 °C, the same
arithmetic gives **0.890** over these points, which the fitted 0.837 excludes
outright — a 6.3 % separation, several times the residual either constant leaves
behind. The data selects the reference state on its own; an arbitrary fudge factor
would have accommodated either. Bosch defines the DIN state, so cite them rather
than claiming a discovery, and write it as *consistent with a 0 °C reference to
within 1.4 %, and excludes 20 °C* — not as "0.1 % agreement".

Per-drive, with the derived constant: `3aca2ec1` 1.6 % (10 points),
`683640a0` 0.9 % (5), `7475b5d7` 1.3 % (5), `cb67b01f` 1.8 % (2). Unaffected by
the geometry correction — this path always used the B58.

**Limit, and it is the one that matters.** This residual is computed through an
inversion of the same relation `run_cycle()` uses, so **it cannot test the
breathing model.** `map_from_airflow()` inverts `load ≈ eta_v·(1−f_res)·map`, so

    load_model = eta_v(1−f_res)·map   and   map = ṁ·R·T / (eta_v(1−f_res)·V·rpm/120)
        ==>  load_model = ṁ·R·T / (V·rpm/120)        eta_v and f_res CANCEL
        ==>  k·load_model = 269.6·ṁ·R / (V·rpm/120)  T cancels too

Measured, not argued: force the charge temperature to a flat 300 K and the derived
residual is **1.3738 %** against 1.3738 % as shipped — identical to four decimal
places. What the number *does* earn is the meaning of BMW's `Relative air filling`
channel (the DIN reference state, which was a guess before), zero fitted
parameters, and the displacement sensitivity above. **Before quoting any residual
as validation, perturb the parameter it supposedly validates and check that the
number moves.** It takes one run.

#### What the 10 September charge-temperature correction changed here

<!-- RETIRED-OK -->
Until 10 September this section reported the points as 31–82 kPa, k fitted 0.784,
k derived 0.783, and a residual of 2.8 % fitted against 1.4 % derived. Those
figures were computed with the pre-throttle temperature sensor standing in for
the charge temperature, and that sensor is a compressor outlet (section E,
limit 2). The operating points are the same 22 windows; the pressure scale
changed underneath them. The derived residual came out at 1.4 % before and after,
because T cancels — **the residual could not see the very error being fixed**,
which is the second half of the lesson above.

### Why points were excluded, and why none of it was tuning

Points were removed by two rules, each written from a measurable defect rather
than from a residual. **Say so in Chapter 3** — an exclusion rule justified after
seeing the answer is worthless, and an examiner will ask. The current figure is
**1.4 % derived over 26 points, 30–75 kPa**; the residuals quoted below are the
ones each rule was scored against when it was introduced.

<!-- RETIRED-OK: section -->
Everything from here to the end of this subsection is that record: figures from
before the eighth drive and before the 10 September charge-temperature
correction, kept because they show what each rule actually did.

**Rule two, the window checks (20 points → 17, 4.4 % → 2.3 %).** `steady_points`
sizes its window in samples from each drive's average rate, so on a drive whose
rate is not constant a "60 second window" is not 60 seconds. Windows were
spanning **42.8 to 73.7 s**, and one contained an internal hole of **3.18 s**.

The cause is `fb988991`, and it is not a driving error. That recording and
`f51686d7` are **reconnaissance runs with all 655 channels selected on purpose**,
made on 6 September to establish which parameters this car publishes. At that
channel count the logger dropped **222 of its 980 seconds — 23 % of the drive
was never recorded**. Its "3.52 Hz" is a normal rate with a quarter of the
samples missing, which also explains the fuel-cut outlier below and the drive's
disagreement between its own load and airflow channels.

Describe them in Chapter 3 as what they are: a channel census that succeeded,
excluded from the operating-point set because a census log cannot also be
steady-state data. `logs/CHANNEL_CENSUS.md` records what they established —
including that the radiator can never be identified on this vehicle, because
every water-pump channel it offers reads zero.

A window is now rejected unless its wall-clock span is within 20 % of 60 s and
it contains no gap longer than four median sample intervals. Every surviving
point records `t_span` (58.7–68.7 s) and `max_gap` (≤ 0.48 s), so the check is
auditable. `fb988991` contributes nothing.

**Be honest about the improvement**: part of it is the removal of the worst
drive. The rule is legitimate because it was written from the logger dropouts,
not from the residual.

**Rule one, the fuel-cut filter (21 windows → 20 points, 9.8 % → 4.4 %).**

`fb988991`, the 3.52 Hz export, contributed a window at 2774 rpm with a
commanded spark of **−14.8° BTDC** and lambda 0.90 — overrun fuel cut, where the
cylinder is not firing and a combustion model does not apply. That single point
carried a 124 % residual. `build_dataset.py` now drops windows with negative
spark or lambda outside 0.70–1.10 from `master_points.csv`; they stay in
`master_samples.csv` because they are real vehicle behaviour.

Per-drive residuals after the exclusion: `3aca2ec1` 4.8 % (11 pts), `683640a0`
5.6 % (5), `cb67b01f` 4.9 % (2), `670063b2` 4.3 % (1).

State the rule in Chapter 3: *"windows in fuel cut were excluded because the
combustion model does not apply to them."*

### How the load input is obtained, and why

Manifold pressure is **inverted from measured air mass flow**
(`plant.map_from_airflow`), not read from the logged pressure channel.

That channel is not manifold pressure. At warm idle — 684 rpm, coolant 81 °C,
stationary — it reads 13.49 against an ambient of 14.23, while the air mass
channel implies **31.2 kPa**, the textbook value. It is a pre-throttle sensor.
Using it gives **75.3 % air-mass error** and a 17.2 % load residual.

---

## C. The thermal network — calibrated 8 September

`thermal.py` was the largest unvalidated part of the model. It has now been run
as a time series over three drives (80 minutes) against logged coolant and oil.

| | before | after |
|---|---|---|
| coolant RMSE | 4.2 K | 4.2 K |
| oil RMSE | 4.7 K | 4.1 K |

**What the data identifies: the oil-to-coolant coupling.** The old
`ua_block_oil = 450 W/K` let the oil float 80 K above the block under load. The
car does not do that:

| measured oil − coolant | median | p95 | max |
|---|---|---|---|
| three drives used for the fit | −1.2 K | +5.4 K | +12.0 K |
| all six drives carrying both channels | −0.6 K | +6.1 K | +15.4 K |

Sweeping the coupling: 450 W/K gives a p95 gap of 8.6 K, 800 gives 5.6 K, 6000
gives 1.0 K. Oil RMSE keeps falling all the way to 6000, but that criterion is
dominated by long cruise stretches where oil and coolant are equal whatever the
coupling. **The p95 gap carries the information, and it picks 800 W/K.**

**What the data does not identify: the radiator.** The thermostat is regulating
for 88–99 % of every drive — coolant sits at 88–97 °C throughout — so it absorbs
any radiator sizing error. A least-squares fit does drive `ua_rad_min` and
`ua_rad_ram` to their bounds, but only by trading against
`frac_fuel_to_coolant`; that is unidentifiability, not a result. **The radiator
parameters were left at their reasoned values and the reason is recorded in the
file.** Identifying them needs a drive that overwhelms the cooling system:
sustained climb in traffic, high ambient, fan at full duty, coolant pushed past
the thermostat's fully-open point. That is a drive to plan, not one to hope for.

### The validation test condition changed too

`validate.py`'s thermal step response used to be 4000 rpm at 190 kPa, lambda
0.85 — wide-open throttle. On the four-cylinder that was 121 kW and looked
plausible. On the real six it is **186 kW held for 83 minutes**, which no road
car does and which no published "sustained climb" figure describes; oil came out
at 182 °C. The model was right and the test was absurd.

It is now a hard sustained climb: 3000 rpm, 140 kPa, stoichiometric, at 25 m/s
with the fan at full duty — 108 kW, and 7.6 g/s of fuel. It is the load
`thermal.py`'s own worked example uses.

**One of its two anchors has gone, and Chapter 3 must not keep claiming it.** The
condition was also chosen because it sat above the hardest load the car had ever
been recorded holding. That ceiling is now **8.7 g/s** — the highest 60-second
mean fuel flow anywhere in the dataset's own samples, on `7475b5d7`, with the
window sized from each drive's own sample rate — so the test's 7.6 g/s now sits
*below* it. The condition was deliberately **not** raised to chase the log: it is
anchored to `thermal.py`'s worked example, and moving it to clear a measured
number would be fitting the test to the data. Describe it as a hard sustained
cruise, not as an upper bound on anything the car has done.

---

## D. The compressor operating envelope — refitted 8 September

Fitted to **74 013 quasi-steady samples**. An operating line, not a compressor map.

Measured 95th-percentile pressure ratio per corrected-flow bin:

| kg/s | 0.021 | 0.039 | 0.070 | 0.105 | 0.134 | 0.164 | 0.194 | 0.230 | 0.260 | 0.280 | 0.301 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PR | 1.175 | 1.314 | 1.537 | 1.933 | 2.283 | 2.353 | 2.219 | 2.415 | 2.287 | 2.515 | 2.333 |

Shipped form, RMS residual **0.135** in pressure ratio:

```
PR = 1 + 14.5023 m / (1 + 6.4019 m)
```

The 7 September quadratic was fitted across an empty middle and under-predicted
badly once the 8 September mid-load drive filled it — 1.53 against 2.28 observed
at 0.134 kg/s. A parabola refitted to the filled data falls above 0.25 kg/s,
which no boost ceiling does, so the form was changed to one that is monotone and
saturating: pressure ratio rises with flow until the wastegate opens to hold the
boost target, then flattens.

The highest pressure ratio observed anywhere is **2.52**, or 250 kPa absolute, at
a highest corrected flow of 0.314 kg/s.
`engine_env.SupervisoryTunerEnv.MAP_CEIL_KPA` is that measured number rather
than the round 240 that used to sit there.

---

## E. Stated limits — put these in Chapter 3 verbatim

1. **The MAF channel saturates at 1020 kg/h.** Exactly 1020.0 kg/h on six
   separate drives — 547 samples pinned at that ceiling — while the
   combustion-air channel reaches 1233 kg/h on the same samples, a median ratio
   of 1.095. Pinned samples are flagged (`maf_pinned`) and excluded from
   everything fitted on air mass. They are **not** repaired by substituting the
   combustion-air channel: that is the ECU's modelled trapped charge, a different
   quantity, and splicing two definitions puts a step in the middle of the curve.
   **The envelope above 0.303 kg/s corrected flow is therefore unmeasured, not
   merely sparse.**

2. **There is no logged manifold pressure on this car to compare against, and
   the boosted gap was the charge temperature — not the breathing model.**

   Both pressure channels the vehicle publishes sit **before the throttle**. Over
   the 22 steady points `Intake manifold absolute pressure` reads 93–97 kPa and
   `Boost pressure`, converted to absolute, reads 100–126 kPa, against an
   inversion of 30–75 kPa. That is not a disagreement about manifold pressure; it
   is two different places in the intake, and at part load the throttle is the
   whole difference. **No script prints an agreement between them below 80 kPa.**
   An earlier version of this table claimed one, inside "the 4.4 % residual".
   There was never any such comparison to run.

   Under boost the throttle is open, so the car's own `Boost pressure` channel
   *is* comparable. **The gate is > 200 kPa and it is not arbitrary:** the logged
   side is filtered at `Boost pressure` > 15 psi gauge, and
   (15 + 14.23) × 6.894757 = 201.5 kPa absolute, so a 200 kPa gate on the model
   side selects the same population by construction. 587 boosted, MAF-unpinned
   model samples against 887 logged readings, logged median 226 kPa:

   | charge temperature used | inverted MAP | gap |
   |---|---|---|
   | the raw pre-throttle sensor (117 °C median) | 279.5 kPa | **+23.7 %** |
   | `plant.charge_temperature()` (52 °C median) | 232.7 kPa | **+1.9 %** |
   | ambient + 8 K (45 °C median) | 227.5 kPa | **+0.7 %** |

   The sensor reads 149 °C under boost and 163 °C at its peak, which is a
   compressor outlet, not charge air: the B58 carries its cooler *inside* the
   intake manifold, downstream of the throttle body, so "before throttle valve"
   is before the cooler. **`volumetric_efficiency()` is cleared, not convicted.**
   The 0.7 % row is **rejected** — "ambient + 8 K" is a knob tuned to hit the
   target, which is the same mistake as validating a model through its own
   inversion. The shipped formula carries no parameter fitted to the boost
   channel, and 1.9 % from an independent model beats 0.7 % from a fitted one.

   What remains uncertain under boost is the MAF ceiling at 1020 kg/h and the
   logger's round-robin sampling, which pairs air mass with pressure taken
   seconds apart.

   **And cleared is not the same as tested.** There is NO part-load test of
   `volumetric_efficiency()` against this car at all, for the same reason: both
   logged pressure channels sit before the throttle, so there is nothing to
   compare a modelled manifold pressure against. The load residual cannot serve —
   it cancels `eta_v` entirely (section B). State that plainly rather than letting
   the 1.4 % imply coverage it does not have.

3. **Peak power is not a prediction.** Manifold pressure is an input.
   `boost_ceiling_kpa` bounds it to what the car was observed to do, but an
   operating line is not a compressor map — no efficiency islands, no speed
   lines, because the vehicle has no turbo speed sensor and no pre-intercooler
   temperature.

4. **Vehicle validation covers 30–75 kPa manifold pressure only.** Steady points
   require steady driving, and steady driving is light-load driving. Limit 2 is
   why this matters more than it looks.

5. **Exhaust backpressure is not measured.** `predict()` estimates it as
   1.15 × manifold pressure. An assumption, not a measurement.

6. **Oil above 117 °C is extrapolation.** That is the hottest oil anywhere in
   the logs (`7475b5d7`, at 45 °C ambient; 111 °C after the filter). The thermal model
   reproduces the logged oil trace, but everything it says about oil on a
   sustained climb rests on the network's structure, not on measurement.

7. **Two drives contribute no samples, and a third contributes no operating
   points.** The manifest lists **ten drives and 295.0 minutes**. `3f64372e`
   (0.7 min) and `f51686d7` (0.8 min) are too short to contain a warm running
   window, so `master_samples.csv` covers six drives. `fb988991` is one of those
   six, but every one of its windows is rejected for span or a logger gap
   (section B), so it carries samples and contributes **zero** operating points.
   Quote it as "ten drives, 295.0 minutes, seven carrying samples,
   26 distinct operating points" rather than implying all eight were analysed.

8. **The radiator-outlet channel is missing on `fb988991`.** It was added to the
   recording set after that drive. Thermal work uses the other four.

9. **A "steady point" is steady for fast quantities only.** The extraction
   window is 60 s, chosen because the drives contain 22 steady holds of 60 s
   but only 6 of 180 s — public roads do not grant three uninterrupted minutes
   on demand. Air mass, lambda, spark and manifold pressure settle in
   milliseconds and are fully converged. The **turbine housing is not**: at a
   measured τ of 48 s, a 60 s window reaches only **71 %** of a thermal step.
   Nothing in the current validation depends on this, because `compare_log.py`
   scores air and load. It would matter immediately if anyone validated a
   thermal quantity "at the steady points" — use a time-series comparison over
   the whole drive instead.

# Validation table

Regenerate with `python validate.py` (plant, ~4 min) and

```
python build_dataset.py "logs/raw/*.csv"
python compare_log.py data/master_points.csv
```

**Do not edit `plant.py` or `thermal.py` without re-running both and updating this file.**

Last regenerated: 8 September 2026, **after the engine-geometry correction.**

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

## A. Against published figures — `validate.py`

| Quantity | Model | Published band | Status |
|---|---|---|---|
| Displacement | 2997.5 cc | 2990–3000 | inside |
| MFB50 at MBT (2500 rpm, 60 kPa) | 8.5° aTDC | 8–10 | inside |
| Best BSFC, knock-feasible, λ=1 | 241.2 g/kWh | 235–260 | inside |
| Knock-limited spark (3000 rpm, 200 kPa) | 11.0° BTDC | 8–14 | inside |
| EGT, cruise band, minimum | 714.5 °C | 600–750 | inside |
| EGT, cruise band, maximum | 777.3 °C | 600–750 | **outside** |
| Turbine housing time constant | 48.0 s | 40–120 | inside |
| Oil temperature, sustained climb | 110.2 °C | 115–140 | **outside** |
| Oil time constant | 16.0 s | 20–400 | **outside** |
| Coolant, thermostat-regulated | 94.5 °C | 88–108 | inside |
| Coolant apparent time constant | 9.5 s | 1–600 | inside |

**8 of 11 inside**, down from a claimed 10 of 11 on the wrong engine. Report the
three misses with their reasons; each is informative.

### The three misses

**EGT maximum, 777 °C against a 600–750 band.** The band describes moderate
cruise. The test's own worst point is 2500 rpm at 100 kPa, and the measured
cruise range on this car is **31–79 kPa** — so that point is above cruise for
this engine, and 777 °C port-exit at near-full naturally-aspirated load is
normal. The test point is mislabelled rather than the model being wrong, but the
band was not moved to make it pass. State it as it is.

**Oil temperature, 110.2 °C against a 115–140 band, and oil τ 16.0 s against
20–400.** Both come from the same parameter, `ua_block_oil`, and both are
consequences of calibrating it against the car instead of the literature — see
section C. The model reproduces the measured oil trace to about 4 K RMSE, and the
measured oil never exceeded **107 °C** anywhere in 168 minutes of logging.

**There may be a resolution, and it is not a tuning knob.** `Oil temperature
after filter` — recorded for the first time on 8 September — runs consistently
hotter than the `Oil temperature` channel the model is calibrated against:
+11.0 K median over a whole drive, and **+6.8 K at oil above 100 °C**, which is
the regime the published band describes. Model 110.2 °C plus 6.8 K is 117 °C,
inside 115–140. If the published figure refers to a hotter point in the oil
circuit, the two numbers were never measuring the same place.

This is **not applied anywhere** and the row is still reported as a miss.
Confirm it with a sustained high-load drive recording both channels first.
**Matching the car and missing the band is the better failure**; do not raise the
coupling to close a gap the data does not support.

Note the turbine constant now sits inside its band at 48.0 s, near the `C/UA`
analytic value of 50.3 s. <!-- RETIRED-OK -->
The old 39.5 s figure came from the four-cylinder.

---

## B. Against the vehicle — `compare_log.py`

Source: **eight drives, 168.1 minutes**, 3.52–6.63 Hz, 2023 GR Supra B58B30O1.
`build_dataset.py` finds **22 distinct operating points**, 31–82 kPa manifold
pressure.

| Comparison | Points | Result | Target | Status |
|---|---|---|---|---|
| Load residual, **k derived**, no free parameters | 22 | **1.4 %** | < 15 % | **PASS** |
| Load residual, k fitted (1 free parameter) | 22 | 2.8 % | < 15 % | PASS |
| Normalisation constant k, fitted | — | 0.784 | — | one fitted scale factor |
| Normalisation constant k, derived | — | 0.783 | — | 269.6 / T_intake, nothing fitted |

**k is not a tuning parameter — it is a unit conversion, and we can derive it.**
Our load is normalised to 100 kPa at the measured intake temperature; BMW's
"relative air filling" is normalised to the DIN reference state, 1013 mbar and
0 °C. Since ρ = P/(R·T), the ratio between the two is

    k = (100 / T_in) ÷ (101.3 / 273.15) = (100 × 273.15 / 101.3) / T_in
      = 269.6 / T_in

The 269.6 is three **defined** constants — no measurement, no fit. Replacing the
fitted 0.784 with this expression leaves the comparison with **zero free
parameters**, and the residual *falls* from 2.8 % to **1.4 %**.

**Why this is evidence rather than numerology.** The reference temperature was
the one thing we assumed. Had BMW normalised to 20 °C, the same arithmetic gives
**0.840**, which the fitted 0.784 excludes outright. The data selects the
reference state on its own; an arbitrary fudge factor would have accommodated
either. Report the agreement, not just the residual.

**Limit.** The derived k varies point to point with the intake temperature
sensor — the pre-throttle one, which lags under boost. All 22 points sit at
31–82 kPa where it tracks. Do not carry this form into the boosted region
without re-checking.

Per-drive: `3aca2ec1` 3.5 % (10 pts), `683640a0` 3.9 % (5), `7475b5d7` 1.8 % (5),
`cb67b01f` 0.6 % (2), all at fitted k. The residual rose from 2.3 % to 2.8 % when the eighth
drive added five points and widened the load range — more coverage, slightly
more scatter. That is the honest direction for a number to move.
Unaffected by the geometry correction — this path always used the B58.

### Why the residual moved from 9.8 % to 4.4 % to 2.3 % to 2.8 %

Not by tuning. Points were removed by two rules, each written from a measurable
defect rather than from a residual. **Say so in Chapter 3** — an exclusion rule
justified after seeing the answer is worthless, and an examiner will ask.

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
point records `t_span` (58.7–68.7 s) and `max_gap` (≤ 0.45 s), so the check is
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
| all five drives carrying both channels | −1.0 K | +5.5 K | +12.0 K |

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

It is now a hard sustained climb: 3000 rpm, 140 kPa, stoichiometric, 108 kW,
7.6 g/s of fuel, at 25 m/s with the fan at full duty. Two anchors put it there —
it is the load `thermal.py`'s own worked example uses, and it was chosen to sit
above the hardest sustained load then recorded on the car.

> **That second anchor no longer holds, and the thesis should say so.** The
> ceiling was read as 6.5 g/s across seven drives (on `670063b2`). Over the
> current eight drives `verify_docs.py` recomputes it as **8.7 g/s**, so the
> 7.6 g/s condition now sits *below* the hardest recorded sustained load rather
> than above it. The first anchor stands and the printed rows are unaffected;
> the argument for the condition is what changed.

---

## D. The compressor operating envelope — refitted 8 September

Fitted to **43 853 quasi-steady samples**. An operating line, not a compressor map.

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

Highest pressure ratio observed anywhere: **2.516**, or 250 kPa absolute.
`engine_env.SupervisoryTunerEnv.MAP_CEIL_KPA` is that measured number rather
than the round 240 that used to sit there.

---

## E. Stated limits — put these in Chapter 3 verbatim

1. **The MAF channel saturates at 1020 kg/h.** Exactly 1020.0 on five separate
   drives, 517 samples, while the combustion-air channel reads higher on the
   same samples (median ratio 1.095).  <!-- RETIRED-OK -->
   *(This item said "four separate drives, 192 samples" and a 1.163 ratio until
   10 September; both were the counts before the eighth drive.)* Pinned samples are flagged (`maf_pinned`) and excluded from
   everything fitted on air mass. **The envelope above 0.303 kg/s corrected flow
   is unmeasured, not merely sparse.** 517 samples across five drives.

2. **The two manifold-pressure estimates diverge under boost, and the cause is
   now identified.** Above 200 g/s: inverted 295 kPa against a logged 231 kPa.
   Re-run the inversion with a plausible post-cooler charge temperature and it
   lands on the logged figure — 241 kPa at 50 °C, 233 kPa at 40 °C. The
   `Intake air temperature before throttle valve` channel reads compressor-outlet
   air, because the B58's charge cooler sits inside the intake manifold
   downstream of the throttle. **The gap is the temperature, not the breathing
   model.** A stock B58 runs about 1.3 bar gauge, which is the logged figure.
   <!-- RETIRED-OK -->
   *(This item claimed until 10 September that below 80 kPa the inversion and the
   logged boost channel "agree inside the 4.4 % residual". They do not: both
   pressure channels are pre-throttle and read 93–125 kPa at the 22 steady points
   against an inverted 31–82, off by 44–52 %. No script prints a 4.4 % agreement.)*

   **The inversion is right
   at part load and wrong under boost.**

3. **Peak power is not a prediction.** Manifold pressure is an input.
   `boost_ceiling_kpa` bounds it to what the car was observed to do, but an
   operating line is not a compressor map — no efficiency islands, no speed
   lines, because the vehicle has no turbo speed sensor and no pre-intercooler
   temperature.

4. **Vehicle validation covers 31–79 kPa manifold pressure only.** Steady points
   require steady driving, and steady driving is light-load driving. Limit 2 is
   why this matters more than it looks.

5. **Exhaust backpressure is not measured.** `predict()` estimates it as
   1.15 × manifold pressure. An assumption, not a measurement.

6. **Oil above 107 °C is extrapolation.** That is the hottest oil anywhere in
   the logs (`7475b5d7`, at 45 °C ambient; 111 °C after the filter). The thermal model
   reproduces the logged oil trace, but everything it says about oil on a
   sustained climb rests on the network's structure, not on measurement.

7. **Two drives contribute no samples, and a third contributes no points.** The
   manifest lists **eight drives and 168.1 minutes**, but `3f64372e` (0.7 min)
   and `f51686d7` (0.8 min) are too short to contain a warm running window, so
   `master_samples.csv` covers **six** drives. `fb988991` carries samples but
   loses every window to the span and gap checks, so it contributes zero
   operating points. Say **"eight drives, 168.1 minutes, six carrying samples,
   22 operating points"** rather than implying all eight were analysed.

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

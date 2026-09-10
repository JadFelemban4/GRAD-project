# Context.md — the domain, the vocabulary, and the constraints

What the words mean in this project, and which physical facts about *this*
vehicle shape every design decision. Read it before arguing about a number.

---

## The vehicle

A **2023 Toyota GR Supra**, engine **BMW B58B30O1** — 3.0 L turbocharged
inline-six, **2997.5 cc**. Data comes off OBD-II through BimmerLink, exported as
CSV.

**Read-only. Always.** The project logs the car; it never commands it. This is
not a soft preference — it is the constraint that keeps a student project on a
road car defensible.

---

## The claim, in vocabulary

| Term | Meaning here |
|---|---|
| **H** | preview horizon — how far ahead the controller can see, in seconds |
| **τ** | time constant of the protected component (turbine, oil, battery) |
| **H/τ** | the dimensionless ratio the whole thesis is about |
| **preview value / preview edge** | how much better a policy does *because* it can see ahead, measured against a policy with identical levers and no preview |
| **the ablation** | running the predictive policy with preview switched off. It must land on the reactive policy |
| **protection trigger** | the temperature above which a policy intervenes. Currently **1123 K** |

## Why 1123 K and not something rounder

The turbine damage term is `exp((t_turb − 1123) / 45)`. 1123 K is the **knee** —
below it damage is negligible, above it damage compounds.

Anchoring the trigger there makes it a statement **about the component**, not
about one episode, so it transfers between scenarios without being re-derived.

It used to be a hard-coded 930 K, chosen when the simulation was accidentally a
four-cylinder. On the real six the turbine reaches 1152 K, so a 930 K trigger
fires from the first second, both policies saturate, and the measured gap
collapses for reasons that have nothing to do with preview.

**One constant, `engine_env.TURB_PROTECT_K`, imported by every policy in the
repo** — so `check_premise.py` and `generality_test.py` cannot silently report
different experiments.

> If you change the damage model, change this constant with it. They are the
> same number.

---

## The three levers, and why they are thermal

The agent is a **supervisor**: it trims a baseline ECU rather than replacing it.
Zero action reproduces the baseline exactly.

| Lever | What it trades |
|---|---|
| **spark retard** | torque and efficiency ↓, exhaust temperature ↑, knock margin ↑ |
| **enrichment (λ < 1)** | fuel ↑, exhaust temperature ↓ — this is component protection |
| **boost trim** | torque ↑, everything thermal ↑ |
| **fan duty** | coolant heat rejection ↑ |
| **coolant pump duty** | radiator effectiveness ↑ |

**Enrichment on this engine is component protection, not a load table.** That is
a measured finding, not an assumption — see below.

---

## Facts about this car that constrain the whole design

### 1. The pressure channel lies

`Intake manifold absolute pressure` is a **pre-throttle sensor**. At warm idle it
reads 13.49 against an ambient of 14.23; real manifold pressure at idle must be
about a third of ambient.

- Using it as the model's load input → **75 % air-mass error**
- Inverting the air-mass channel → **2.8 %**

**Always use `plant.map_from_airflow()`.** `compare_log.py --map-from-log` exists
only to reproduce the failure for the thesis.

### 2. Enrichment follows engine speed and dwell, not load

At 118 seconds above 230 kPa, the correlation between λ and manifold pressure is
**−0.05 — none**. What correlates:

| variable | correlation with λ |
|---|---|
| engine speed | −0.56 |
| air mass flow | −0.49 |
| dwell above 200 kPa | −0.47 |
| manifold pressure | **−0.05** |

Below ~3300 rpm the car does not enrich however long boost is held. Above
4500 rpm it runs stoichiometric for the first seconds of a pull and enriches to
0.81 only after roughly eight seconds.

**Dwell above 200 kPa stands in for turbine inlet temperature**, which this
vehicle does not expose. State that as a limitation.

### 3. The MAF channel saturates silently

`Air mass flow` tops out at exactly **1020.0 kg/h** — the same number on five
drives, 517 samples. On the same samples `Air mass flow participating in
combustion` reads up to 1233 kg/h.

`build_dataset.py` flags them `maf_pinned` and excludes them from `stable`. They
are **not repaired** by substituting the combustion-air channel: that is the
ECU's modelled trapped charge, a different quantity, and splicing two
definitions puts a step in the middle of the curve.

### 4. The radiator is not identifiable on this car

Every water-pump channel the vehicle offers is **all-zero**, so there is no
coolant-flow signal and `Q = ṁ·cp·ΔT` cannot be formed. The fan actual-value and
duty channels are all-zero too.

A constrained fit was attempted with 55 minutes at 45 °C ambient: **R² = 0.157
with a negative ram coefficient.** The only observable is ΔT across the
radiator, and ΔT = Q/ṁ — both terms rise with road speed, so ΔT carries almost
no information about UA.

**Stop trying. State it as a limitation.** `ua_block_oil` *is* identified
(800 W/K); the radiator parameters were deliberately left alone.

### 5. A census log is not a driving log

`fb988991` was logged with **655 channels selected**. The logger could not keep
up: 196 gaps larger than three times the median interval, **222 of its 980
seconds never recorded — 23 % of the drive missing**.

That single fact explained three symptoms previously filed as unrelated. It
contributes **zero** operating points and always will.

But it was not logged *wrong*. It and `f51686d7` were deliberate reconnaissance
runs, made before anyone knew which parameters this car publishes. They are the
reason the 21-channel set exists.

> **The rule: census once with everything, then record the small set for real
> drives.** Twenty channels log cleanly at 4.6 Hz with no dropouts.

---

## What "validated" means here, precisely

Three different claims, routinely conflated. Keep them apart.

| Claim | Evidence | Coverage |
|---|---|---|
| the cycle model matches published engine physics | `validate.py`, 8 of 11 inside band | generic, not this car |
| the cycle model matches **this car** | `compare_log.py`, 2.8 % over 22 points | **31–82 kPa only** |
| the thermal network matches this car | `thermal.py` driven over whole logs | oil ≤ 107 °C only |

**Vehicle validation covers 31–82 kPa.** Steady points need steady driving, and
steady driving is light-load driving. The boosted region is validated against
published correlations, not against the car.

---

## The three drive counts, which are not the same number

Conflating these is easy and produces a wrong sentence in the thesis.

| count | value | who is excluded |
|---|---|---|
| drives in the manifest | **8** | — |
| drives carrying samples | **6** | `3f64372e`, `f51686d7` (under a minute, no warm window) |
| drives carrying steady points | **5** | + `fb988991` (every window fails the span/gap checks) |

Quote it as **"eight drives, 168.1 minutes, six carrying samples, 22 operating
points"** — and say which of the three you mean.

---

## Reporting discipline

1. **Never quote a number a script does not print.**
2. **Report the condition with the number.** "2.8 % load residual over 22
   points, 31–82 kPa" — not "the model is accurate."
3. **Report the threshold with every preview figure.**
4. **Run `verify_docs.py` before quoting anything into the thesis.** It exists
   because five published figures had already drifted, four for the same reason:
   a figure computed on ONE drive and quoted as if it were pooled.
5. **Change one thing, re-run, write down what happened.** Two changes at once
   and you no longer know which one did it.

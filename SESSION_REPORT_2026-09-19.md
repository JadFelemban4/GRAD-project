# Session report — 19 September 2026

**Audience:** the team. It assumes you know the project. Everything is in the
order it happened, including the two things that were wrong on the first attempt
and the one question the internet could not answer.

**Branch:** everything is on **`JMF-2340550`**. `JMF-2340550-sep17` was NOT
merged — see Part 0, it matters. `git log 926b6f5..HEAD` is this session.

---

## Headline

| | |
|---|---|
| **The gearbox is the real one.** | ZF 8HP51, eight speeds, Toyota's published ratios — and **the car's own logs confirm them to 0.9 %**. |
| **A fourth channel is not what its name says.** | `Actual gear` **clamps at 6** on an eight-speed. Three quarters of what it calls top gear is 7th or 8th. |
| **The compression-ratio question is settled.** | The car is the 285 kW / ~386 hp B58B30O1, so `plant.py`'s 10.2:1 is right. |
| **Phase C is running.** | Ten SAC runs in flight — 5 sighted, 5 blinded, 50 k steps each. |
| **"I can't reach that temperature" — investigated.** | The 850 °C trigger sits inside the 825–925 °C band production ECUs use. But **nothing on this car can check it**, and that is now written down. |

> **Correction, made while writing this.** The scenario figures below are at
> **110 km/h**, which is this branch's default. `sep17` locked the scenario at
> **130 km/h** and this branch does not have that commit. Any comparison with
> the 18 September report is a comparison across two different scenarios until
> the branches merge.

---

# Part 0 · The branch, and why this report is not on `sep17`

`origin/JMF-2340550-sep17` carries twelve commits this branch does not,
including `1df41a2` — **mistake 17**, the load-aware gearbox fix, the locked
12 % / 130 km/h scenario, `evaluate.py` and Phase D's first result. This branch
carries two that `sep17` does not: the tenth drive (+119.5 min) and the runtime
3 L verification.

**The team chose to make this change here anyway.** The consequence is handled
rather than ignored: the load-aware downshift from mistake 17 is **carried
deliberately** into the new eight-speed (Part 2.4), so merging the branches
later resolves to the same rule rather than to a conflict.

**What this branch still lacks and needs from `sep17`:** `evaluate.py` and its
twenty locked episodes. Phase D cannot be scored here without them.

---

# Part 1 · The question that came first: can the car reach 850 °C?

Asked directly, and it is the right question, because the whole protection
experiment is built on that trigger.

## 1.1 · What the trigger is

`TURB_PROTECT_K = 1123 K` = **850 °C**, the knee of the damage term
`exp((T − 1123) / 45)`. It is a *damage* knee, not a destruction limit.

## 1.2 · What the literature says

| source | figure | what it refers to |
|---|---|---|
| turbocharger material reviews | conventional turbine wheels limited to **900–980 °C**; nickel-base MAR-M246 above **1030 °C** | METAL |
| production ECU component-protection practice | thresholds for catalyst/turbine protection **typically 825–925 °C**, with examples at 875 and 900 °C, at which point torque is limited | GAS |

**850 °C sits inside the band production ECUs actually use**, and below every
material limit found. As a threshold it is defensible.

**But the second row is UNVERIFIED.** It comes from a search summary of patent
text; the primary documents would not open (USPTO returns scanned images,
ScienceDirect returns 403). **It is not a citation until someone opens it and
writes down the page.** REFERENCES.md records it as such.

## 1.3 · Why the car cannot settle it — and this is the real answer

| channel | what it gives | why it cannot help |
|---|---|---|
| `Exhaust gas temperature after catalytic converter from model` | median 601 °C, **max 645.3 °C** | **modelled, post-catalyst, and CLAMPED** — p95 = max = 645.3, a saturated channel |
| `Exhaust gas temperature behind main catalyst from model` | max 645.1 °C | same |
| every pre-catalyst / SCR temperature sensor | all-zero | not fitted |
| turbine temperature | — | **the car has no such sensor.** That is why the app exists |

So: the model says the tenth drive peaked at **890.6 °C** estimated turbine. The
car's only exhaust channel is modelled, post-cat, and pinned at 645. **There is
no measurement on this vehicle that can confirm or refute 890 °C**, and the
honest position is that the estimate is unfalsifiable from our own data.

## 1.4 · What would settle it

1. **A thermocouple in the exhaust manifold, pre-turbine.** The only direct
   answer. It is the single highest-value instrumentation this project could add.
2. **A drive that sustains WOT far longer than any log we have.** The estimate
   is highest where the data is thinnest.
3. **The knock-retard channel, properly filtered** — the ECU's own enrichment and
   retard behaviour is an indirect witness to how hot it thinks it is getting.

## 1.5 · Public datasets: searched, and they do not fill the gap

| dataset | what it has | why it does not help |
|---|---|---|
| Vehicle Energy Dataset (Michigan/Argonne/Idaho) | a year of OBD-II from personal vehicles | no turbine or pre-cat exhaust temperature |
| Automotive OBD-II Dataset (RADAR-KIT) | ten signals: coolant, MAP, rpm, speed, IAT, MAF | the standard ten; no exhaust temperature |
| Kaggle obd2data / obdii-ds3 | 27 parameters, Toyota Etios 1.5 | naturally aspirated, wrong engine class |
| Cummins ISB6.7 transit-bus OBD set | 90 attributes at 1 Hz **including exhaust temperature** | **diesel**, and a bus |

**No public dataset found carries turbine or pre-turbine exhaust temperature on
a turbocharged petrol engine.** The gap in this project is the gap in the field's
public data, and that is worth one sentence in the thesis rather than an apology.

---

# Part 2 · The gearbox — ZF 8HP51

## 2.1 · What was there

A **generic six-speed with invented ratios**: 3.6 / 2.1 / 1.4 / 1.0 / 0.82 /
0.68 on a 3.4 final drive. No source, and not the transmission in the car.

## 2.2 · What Toyota publishes

Toyota's own technical specification sheet names the unit **"8-speed Sports
Automatic 8HP 51"** and prints the set:

| gear | ratio | gear | ratio |
|---|---|---|---|
| 1st | 5.250 | 5th | 1.316 |
| 2nd | 3.360 | 6th | 1.000 |
| 3rd | 2.172 | 7th | 0.822 |
| 4th | 1.720 | 8th | 0.640 |
| reverse | 3.712 | **final drive** | **3.150** |

**The final drive is confirmed twice on two different power outputs.** That sheet
is the 250 kW European car; Toyota USA's pressroom gives 3.15 for the automatic
on the **382 hp** car, which is this one. The driveline is not variant-sensitive.

## 2.3 · What the CAR says, which is better evidence

Engine speed and road speed give the overall ratio the car is actually running:

> **86.7 % of 79 105 moving samples land within 4 % of one of the eight
> published ratios.**

And it excludes the alternative. Toyota offered the 3.0 with a six-speed manual
whose top gear is 0.846 × 3.46 = **2.927** overall. The car measures **1.998**,
which matches the 8HP51's 8th (2.016) to 0.9 % and matches nothing on the manual.

## 2.4 · The shift schedule, which is the only part with no source

Neither Toyota nor ZF publishes when the box changes gear. Two parameters carry
it, both declared ASSUMED:

- **`UPSHIFT_MIN_RPM` = 2000** — **calibrated against the car**, not guessed.
  Swept against the gear inferred from the car's own ratios:

  | rpm | exact gear | within one | mean (model − car) |
  |---|---|---|---|
  | 1400 | 47.0 % | 60.9 % | +1.18 |
  | 2000 | 28.2 % | **79.7 %** | **+0.28** |
  | 2100 | 24.1 % | 74.3 % | −0.06 |

  **Exact agreement peaks at ~47 % for ANY threshold.** A speed-only schedule
  cannot reproduce a real automatic, which shifts on throttle and load too.
  Quote "within one gear, 79.7 %" and say what it is.

  **It was not tuned to move a result, and that is checkable:** at 130 km/h on a
  12 % grade, 1400 and 2000 rpm both select 7th, 2706 rpm, 340 Nm.

- **`SHIFT_LOAD` = 0.75** — mistake 17's 25 % torque reserve, carried
  deliberately. Shipping an eight-speed with a bare speed ladder would have
  reintroduced the mid-climb upshift with a **taller** top gear (2.016 overall
  against 2.312).

## 2.5 · The converter is modelled LOCKED, and that is a decision

It is a torque-**converter** automatic. ZF and Toyota publish no stall ratio, no
K-factor and no lock-up schedule, so any converter curve would be an invented
parameter of exactly the kind mistake 12 warns about. The scenarios here are
steady high-speed climbs where a real 8HP is locked.

**Say "converter assumed locked" wherever the gearbox is described.**

## 2.6 · What ZF does NOT publish, and two figures to stop repeating

| figure in circulation | what ZF actually publishes |
|---|---|
| torque capacity ~560 Nm | the 8HP **family**, 220–1000 Nm. No per-variant figure. **UNVERIFIED** |
| weight ~77 kg | **87 kg**, and for the **8HP70**. **UNVERIFIED** |
| ratio spread 7.0 | 7.0 for the family. This set spreads 5.250/0.640 = **8.20**. **Do not cite 7.0 for these ratios** |

The 560 Nm is worth chasing: the engine makes 500 Nm, so a stock car sits at
~89 % of the rated limit and any tune passes it. **Good sentence for the thesis,
bad one to write without a source.**

---

# Part 3 · Mistake 18 — `Actual gear` clamps at 6

The check that confirmed the gearbox broke a channel.

**`Actual gear` never exceeds 6 on any drive**, across 45 606 moving samples.
Taken at face value that says the car is the manual. It is not — within the
samples the channel labels "gear 6" there are **three sharp clusters**:

| overall ratio | samples | what it really is |
|---|---|---|
| ~2.016 | 19 290 (59.3 %) | **8th** |
| ~2.589 | 5 406 (16.6 %) | **7th** |
| ~3.15 | 4 833 (14.9 %) | 6th |

The channel reports truly to 6th and then **saturates**.

**Fourth channel on this car that is not what its name says** — after the
pre-throttle pressure, the MAF ceiling and the compressor outlet — and the first
that fails by RANGE rather than by meaning.

**Act on this:** the knock-retard p99 in the limitations section is filtered "to
steady gear" using this channel. It cannot see a 6→7 or 7→8 shift, so the figure
includes transients it was meant to remove. **Re-derive before quoting it.**

---

# Part 4 · Phase C — ten runs in flight

```bash
python train.py --steps 50000 --seed 0..4            # sighted
python train.py --steps 50000 --seed 0..4 --no-preview  # blinded
```

Launched 05:58, ten concurrent, 2 torch threads each across 20 logical cores.
Measured: **17.2 effective cores in use**, no 10 000-step checkpoint after 50
minutes, so **under 3.3 steps/s per run** and roughly **4 hours** for all ten.
Aggregate throughput is ~33 steps/s against 9.4 solo, so running them together
is the right call on this machine.

**Results are not in this report.** They land in `runs/` and go in the next one.

## 4.1 · The budget is too small, and here is the arithmetic

The episode is 900 s at `dt = 0.2` → **4500 steps**. So 50 000 steps is
**11 episodes**.

The observation includes the three preference weights (`w[0..2]`, the last 3 of
23 dimensions), drawn fresh at every reset. **The policy is weight-conditioned:
it must generalise across the weight simplex from eleven samples of it.**

That is the single biggest lever on result quality, and it is arithmetic rather
than opinion.

---

# Part 5 · Exactly what changed

## Code

| file | what |
|---|---|
| **`engine_env.py`** | `Vehicle` rebuilt: eight published ratios, `final_drive` 3.4 → **3.150**, new `UPSHIFT_MIN_RPM`, `_upshift_speeds()`, load-aware `gear_for(v_mps, force_n=None)`, `PEAK_TORQUE_NM`, `SHIFT_LOAD`, `SHIFT_RPM_MAX`. `demand()` passes tractive force. |
| **`new_drive.py`** | **NEW.** Scores a candidate CSV against the four things the project is short of, before it is added. |
| **`fit_envelope.py`** | **NEW** (previous session, first reported here). Regenerates the compressor envelope with independent-reading counts. |

**Nothing in `plant.py` or `thermal.py` moved**, so `validate.py` is untouched at
8 of 11.

## Documents

`CLAUDE.md` — mistake 18, the settled compression ratio, the mistake count to
eighteen with a note that 17 lives on `sep17`. `REFERENCES.md` — new section 2b,
the gearbox, every figure sorted into CONFIRMED / UNVERIFIED / ASSUMED.
`AUDIT_FIXES.md` — the tenth drive and the window-sizing bug it exposed.

## Verified on this tree

```
verify_docs.py         All 38 checks pass, 311 figure mentions, 24 tracked files
validate.py            8 of 11 inside band, unchanged
test_reward.py         4 of 4, neutral inside the ±0.05 band
app.test_replay        49 of 49
check_premise.py       baseline 414.4 at 840 °C — still does not bind, by 10 K
build_dataset.py       295.0 min, 10 drives, 26 operating points
```

**If you read one diff:** `git show 5c859f0 -- engine_env.py` — the gearbox, and
the only change to what the simulator does.

---

# Part 6 · What moved, and what it means

| | before | after |
|---|---|---|
| premise baseline damage | 294.2 | **414.4** |
| peak turbine, baseline | 812 °C | **840 °C** |
| margin to the trigger | 38 K short | **10.2 K short**, at 110 km/h |
| preview over current-grade | −1.8 pts | **−1.2 pts** |

The real gearbox holds **7th at 2706 rpm** on the climb where the invented
six-speed sat in 6th at 2416. Higher rpm, more exhaust flow, hotter turbine. The
scenario is now **10 K from binding** — closer than any change this project has
made, and it got there by being more correct rather than by being tuned.

Measured directly: over the 4500-step episode the baseline peaks at
**839.7 °C** and spends **0.0 %** of the episode above the trigger, with the
grade at its 12 % maximum for 80 % of the run. The margin is 10.2 K.

**Preview is still negative against a policy that merely knows the current
grade.** That has survived the audit fixes, the tenth drive and now the real
gearbox. It is beginning to look like a result rather than a defect.

---

# Part 7 · Open questions

1. **The 850 °C trigger cannot be validated on this car.** Is a pre-turbine
   thermocouple feasible on a borrowed vehicle? If not, say so in the thesis —
   the estimate is unfalsifiable from our data and that is a limitation, not a
   failure.
2. **The 825–925 °C production band is UNVERIFIED.** Someone with library access
   should open one primary source and write down the page. It is the difference
   between "our trigger is defensible" and "our trigger is cited".
3. **The step budget.** 11 episodes for a weight-conditioned policy. Raise it, or
   fix `w` during training and condition afterwards — but decide before the five
   seeds are treated as Phase D's input.
4. **`dt` is not consistent.** Premise runs at 1.0, generality at 2.0, training at
   0.2. The agent learns in a different discretisation than the hand-written
   policies were scored in.
5. **Merge `sep17`.** This branch cannot score Phase D without `evaluate.py` and
   its twenty locked episodes.

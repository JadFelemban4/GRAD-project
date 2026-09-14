# REFERENCES.md — where every number that we did not measure comes from

**Written to be read by someone who is not an engine specialist.** Every
technical term below has a plain-English explanation beside it. If a row is
unclear, that is a defect in this file, not in the reader.

Created 12 September 2026, because `validate.py` compares eleven of our model's
outputs against "published bands" and the repository cited exactly **one**
source for all eleven: the word "Heywood" in a code comment, with no edition
and no page number. If an examiner asks *"where does 115–140 °C come from?"*,
that is not an answer.

---

## First, the four kinds of number in this project

This is the most important section. A reader who understands this table can
follow everything else.

| kind | what it means | can it be checked? |
|---|---|---|
| **1. We measured it** | It came out of 168 minutes of OBD-II logs from our own car | Yes — re-run the script |
| **2. General engine physics** | True of any petrol engine, from textbooks and papers | Yes — open the book |
| **3. Specific to the B58** | Only BMW or Toyota can tell you; it is a fact about this engine, not about engines in general | Only with factory service documentation |
| **4. We assumed it** | A reasonable engineering estimate nobody has verified | **No.** Must be declared as an assumption |

**The project's strength is kind 1.** The risk is presenting kind 4 as if it
were kind 2 or 3. This file exists to stop that.

## Second, what CONFIRMED and UNVERIFIED mean here

| status | meaning |
|---|---|
| **CONFIRMED** | Checked against the publisher or an indexing service on 12 Sep 2026. Author, year, title and paper number are correct. |
| **UNVERIFIED** | The number is standard and probably right, but **nobody has opened the source and found it.** The source named is *where to look*, not a citation that has been checked. |

**Never move a row from UNVERIFIED to CONFIRMED without opening the source and
writing down the page.** Never fill one in from memory — anyone's, including an
AI's. A fabricated citation is worse than a missing one, because no script can
catch it.

---

## 1. The methods our simulator uses — general engine physics (kind 2)

These are named, standard methods. They apply to **any** petrol engine, not just
the B58, so a general source is the correct source here.

| what it is | plain English | citation | status |
|---|---|---|---|
| **Wiebe function** | A formula describing how fast the fuel burns once the spark fires — burning is not instant, it takes a few thousandths of a second, and this curve is its shape | Vibe (Wiebe), I. I., *Brennverlauf und Kreisprozess von Verbrennungsmotoren*, VEB Verlag Technik, Berlin, 1970 — [Open Library](https://openlibrary.org/books/OL5771526M/Brennverlauf_und_Kreisprozess_von_Verbrennungsmotoren) | **CONFIRMED** |
| Wiebe — easier modern citation | A 2010 review article; cite this if the 1970 German book is hard to obtain | Ghojel, J. I., "Review of the development and applications of the Wiebe function", *International Journal of Engine Research*, 2010 — [SAGE](https://journals.sagepub.com/doi/abs/10.1243/14680874jer06510) | **CONFIRMED** |
| **Woschni correlation** | A formula for how fast heat leaks from the burning gas into the metal walls of the cylinder. Without it the model would predict the engine runs far hotter than it does | Woschni, G., SAE Technical Paper **670931**, 1967 — [SAE](https://www.sae.org/papers/a-universally-applicable-equation-instantaneous-heat-transfer-coefficient-internal-combustion-engine-670931) | **CONFIRMED** |
| **Chen–Flynn FMEP model** | FMEP = the engine's internal friction, expressed as pressure. Some of the power made inside the cylinder is eaten by the engine rubbing against itself before it reaches the wheels; this estimates how much | Chen, S. K. and Flynn, P. F., SAE Technical Paper **650733**, 1965 — [SAE](https://saemobilus.sae.org/content/650733), doi:10.4271/650733 | **CONFIRMED** |
| **Douaud & Eyzat knock integral** | "Knock" is uncontrolled detonation — the fuel exploding instead of burning smoothly. It destroys engines. This formula predicts when it will happen | Douaud, A. M. and Eyzat, P., SAE Technical Paper **780080**, 1978 — [SAE](https://saemobilus.sae.org/papers/four-octane-number-method-predicting-anti-knock-behavior-fuels-engines-780080) | **CONFIRMED** |
| **General reference** | The standard graduate textbook on petrol and diesel engines | Heywood, J. B., *Internal Combustion Engine Fundamentals*, **2nd ed., McGraw-Hill Education, 2018**. Print ISBN 978-1-26-011610-6 (MHID 1-26-011610-7); e-book ISBN 978-1-26-011611-3 (MHID 1-26-011611-5). 1st ed. 1988. | **CONFIRMED** — verified from the book's own copyright page, 13 Sep 2026 |
| **Bosch relative air charge** | Defines what BMW's "relative air filling" channel actually means — the reference air density it is measured against (1013 mbar, 0 °C). This is what our constant k converts between | Robert Bosch GmbH, *Gasoline-Engine Management*; and patent [EP1015746B1](https://patents.google.com/patent/EP1015746B1/en) | **CONFIRMED** — page not yet located |

---

## 2. Facts about the B58 specifically (kind 3)

**These cannot come from a textbook.** They are facts about one engine, and only
the manufacturer can supply them. Our own logs partly confirm some.

| what | our value | what an external source must confirm | status |
|---|---|---|---|
| **Displacement** — total swept volume of all six cylinders | 2997.5 cc | 2998 cc is the published B58 figure. Our 2997.5 is computed from bore and stroke, so a 0.5 cc difference is rounding, not error | **UNVERIFIED — need factory documentation** |
| **Bore** — cylinder diameter | 82.0 mm | Matches the published B58 figure | **UNVERIFIED — need factory documentation** |
| **Stroke** — how far the piston travels | 94.6 mm | Matches the published B58 figure | **UNVERIFIED — need factory documentation** |
| **Compression ratio** — how much the piston squeezes the air before ignition | 10.2:1 | Published range across B58 variants is 10.2–11.0:1. **Confirm which applies to the B58B30O1 in a 2023 GR Supra**, because it affects knock prediction | **UNVERIFIED — and variant-sensitive** |
| **Thermostat opening temperature** — the valve that lets coolant reach the radiator | 88 °C | A manufacturer figure, in the service data | **UNVERIFIED** |
| **Coolant operating band** | 88–108 °C | Manufacturer figure. Our logs sit at 88–97 °C throughout, which supports it | **UNVERIFIED — but our data agrees** |
| **Oil operating band, sustained load** | 115–140 °C | Manufacturer figure. **Our model gives 110.2 °C and we report this as a MISS**, so getting the real band matters | **UNVERIFIED** |

> **Note on sources for this section.** Wikipedia's B58 article carries the bore,
> stroke and displacement figures and they match our model exactly, but
> Wikipedia is not an acceptable thesis citation. Use it to find the underlying
> source, then cite that. BMW/Toyota workshop documentation, or a recognised
> technical reference on the engine, is what is needed.
>
> **Forum posts are not sources.** Searching for B58 oil temperatures returns
> mostly owner forums. Those cannot go in a thesis at any price.

---

## 3. The eleven validation bands — ALL UNVERIFIED

Every band `validate.py` scores against. **None has been checked against a
source.** The "kind" column says whether a general textbook will do, or whether
this needs BMW-specific data.

| # | quantity | plain English | band | kind | **exact place to look** |
|---|---|---|---|---|---|
| 1 | Displacement | engine size | 2990–3000 cc | **B58** | factory documentation — section 2 |
| 2 | MFB50 at MBT | The crank angle by which half the fuel has burned, at the spark timing giving most torque | 8–10° ATDC | general | **Heywood §9.2.3 "Combustion Process Characterization", p. 415**; and **§15.3.1 "Spark Timing", p. 899** |
| 3 | Best BSFC | Fuel burned per unit of work — best-case efficiency | 235–260 g/kWh | general | **Heywood §2.8 "Specific Fuel Consumption and Efficiency", p. 66**; and **§15.2.4 "Engine Performance Maps", p. 894** |
| 4 | Knock-limited spark | How far spark can advance at high load before detonation | 8–14° | **B58-ish** | **Heywood §9.6 "Abnormal Combustion: Spontaneous Ignition and Knock", p. 475**, esp. **§9.6.5 "Knock Suppression", p. 502**. Expect to find the mechanism, NOT this band. **Weakest of the eleven** |
| 5 | EGT cruise, min | Exhaust gas temperature at steady cruise | 600–750 °C | general | **Heywood §6.5 "Exhaust Gas Flow Rate and Temperature Variation", p. 246** |
| 6 | EGT cruise, max | as above | 600–750 °C | general | as above |
| 7 | **Turbine housing time constant** | How long the turbo takes to heat up — to reach 63 % of the way to its final temperature after a load step | 40–120 s | **B58** | Heywood **§6.8.4 "Turbines", p. 278** gives turbine behaviour but probably NOT a thermal time constant. Expect to need turbocharger thermal-modelling literature. **HIGHEST PRIORITY** |
| 8 | Oil temperature, sustained climb | how hot oil gets on a long hard climb | 115–140 °C | **B58** | **Heywood §12.7 "Thermal Loading and Component Temperatures", p. 744** and **§13.11 "Lubricants", p. 813**, then factory data |
| 9 | Oil time constant | how long oil takes to heat up | 20–400 s | **B58** | **Heywood §12.7.3 "Engine Warm-Up", p. 757** |
| 10 | Coolant, thermostat-regulated | steady coolant temperature once warm | 88–108 °C | **B58** | factory data; **Heywood §12.7.2 "Component Temperature Distributions", p. 754** for context |
| 11 | Coolant apparent time constant | how fast coolant responds | 1–600 s | **B58** | **§12.7.3, p. 757**. Band is so wide it asserts nothing — consider narrowing or dropping |

**These page numbers come from the book's own table of contents, verified
13 Sep 2026.** They tell you exactly which section to open. They do NOT mean the
band has been checked — you still have to read the page and confirm the number.
Status stays UNVERIFIED until someone does.

### Why row 7 comes first

**The entire thesis claim is H/τ** — preview horizon divided by the time
constant of the part being protected. **τ for the turbine is row 7.**

If that band is wrong, every point on the H/τ curve sits in the wrong place.
No other row can move the headline result. Source it before any of the others.

### Why row 4 is the weakest

Douaud & Eyzat is correctly cited for the knock *calculation*. But "a production
turbocharged engine runs 8–14° of spark at 3000 rpm and 200 kPa" is a **separate
claim about real engines**, and nothing in the repository supports it. Either
find a source or drop the row.

---

## 3a. HEYWOOD PAGE MAP — BOTH EDITIONS

**READ THIS BEFORE QUOTING A PAGE NUMBER.** There are two editions in
circulation and **their page numbers are completely different.** The 1st edition
ends at p. 917; the 2nd ends at p. 1006. "Heywood p. 66" means *Specific Fuel
Consumption* in the 2nd edition and *Thermochemistry of Fuel-Air Mixtures* in
the 1st. Always write the edition next to the page.

Section numbers are mostly stable between editions; **page numbers are not.**
When in doubt, cite the SECTION and give the page for the edition you used.

| what we need it for | section | **1st ed (1988)** | **2nd ed (2018)** |
|---|---|---|---|
| **Row 3 — BSFC 235–260 g/kWh** | §2.8 Specific Fuel Consumption and Efficiency | **p. 51** | p. 66 |
| — real engine data tables (check BSFC against these) | §2.15 Engine Design and Performance Data | **p. 57** | p. 73 |
| **Row 2 — MFB50 at MBT, 8–10°** | §9.2.3 Combustion Process Characterization | **p. 389** | p. 415 |
| — and spark timing effects | §15.3.1 Spark Timing | **p. 827** | p. 899 |
| **Rows 5, 6 — EGT 600–750 °C** | §6.5 Exhaust Gas Flow Rate and Temperature Variation | **p. 231** | p. 246 |
| **Row 4 — knock-limited spark** | §9.6 Abnormal Combustion: Knock and Surface Ignition | **p. 450** | p. 475 |
| — knock mechanism | §9.6.2 Knock Fundamentals | **p. 457** | p. 482 |
| **Row 7 — turbine** | §6.8.4 Turbines | **p. 263** | p. 278 |
| — turbocharged SI performance | §15.6.1 Four-Stroke Cycle SI Engines | **p. 869** | — |
| **`frac_fuel_to_coolant = 0.26`** | §12.3 Heat Transfer and Engine Energy Balance | **p. 673** | p. 721 |
| **`f_res` residual gas fraction** | §6.4 Residual Gas Fraction | **p. 230** | p. 245 |
| **Woschni, as we use it** | §12.4.4 Correlations for Instantaneous Local Coefficients | **p. 681** | p. 728 |
| **`volumetric_efficiency()`** | §2.10 Volumetric Efficiency / §6.2 in depth | **p. 53 / 209** | p. 68 / 216 |
| **Chen–Flynn friction context** | §13.5.1 SI Engines (friction data) | **p. 722** | p. 776 |
| **Compression ratio, 10.2 vs 11.0** | §15.3.4 Compression Ratio | **p. 841** | p. 916 |
| **Oil / component temperatures** | §12.7 Thermal Loading and Component Temperatures | **p. 698** | p. 744 |
| — lubricant requirements | §13.8.2 Lubricant Requirements | **p. 741** | p. 813 |
| **Our whole 0-D modelling approach** | §14.4.2 Spark-Ignition Engine Models | **p. 766** | p. 836 |

**Two differences between the editions that matter to us:**

1. **The 2nd edition adds §12.7.3 "Engine Warm-Up" (p. 757). The 1st edition has
   no equivalent.** That section is the natural home for row 9, the oil time
   constant. If you only have the 1st edition, row 9 is harder to source there.
2. The 2nd edition adds §6.2.3 "Intake and In-Cylinder Heat Transfer" and
   §6.2.8 "Effects of Turbocharging", both relevant to our charge-temperature
   correction (mistake 13).

**Page numbers verified 13 Sep 2026** — 1st edition from its own contents pages,
2nd edition from the publisher's front matter. They tell you where to LOOK.
Every band stays UNVERIFIED until someone opens the page and reads the number.

### A lead for row 7, found in Heywood's own reference list

Heywood 1st ed., p. 898, reference 48 cites:

> **Watson, N. and Janota, M. S., *Turbocharging the Internal Combustion
> Engine*, Wiley-Interscience, John Wiley, New York, 1982.**

That is the standard monograph on turbocharging, and it is the best lead we have
for the turbine time constant. Heywood's §6.8.4 covers turbine *performance*
(efficiency, flow), which is probably NOT a thermal time constant — so expect to
need Watson & Janota, or turbocharger thermal-modelling papers, for row 7.

Also on that page: **Hiereth, H. and Withalm, G., "Some Special Features of the
Turbocharged Gasoline Engine", SAE 790207, 1979** — turbocharged *petrol*
specifically, closer to our case than most of the diesel literature.

## 3b. Other Heywood sections this project needs

Not validation bands — these are where the *methods* and *assumed parameters*
are justified. All page numbers from the 2nd-edition contents, verified 13 Sep.

| what it supports in our code | Heywood section | page |
|---|---|---|
| **`frac_fuel_to_coolant = 0.26`** — the biggest unsourced thermal assumption | **§12.3 "Heat Transfer and Engine Energy Balance"** | **721** |
| Woschni correlation, as we use it | §12.4.4 "Correlations for Instantaneous Local Coefficients" | 728 |
| `volumetric_efficiency()` — the breathing model | §2.10 "Volumetric Efficiency" p. 68, and §6.2 in depth | 68 / 216 |
| `f_res` — residual gas fraction | **§6.4 "Residual Gas Fraction"** | **245** |
| Chen–Flynn friction, as we use it | §13.9 "Engine Friction Modeling" | 804 |
| The whole 0-D modelling approach | §14.4.2 "Spark-Ignition Engine Models" | 836 |
| Compression ratio effects (the 10.2 vs 11.0 question) | §15.3.4 "Compression Ratio" | 916 |
| Turbocharging generally | §6.8 "Supercharging and Turbocharging" | 265 |

**Open p. 721 first.** `frac_fuel_to_coolant = 0.26` is currently an assumption
with no source at all, and the engine energy balance section is exactly where
the real figure lives. One page fixes it.

## 4. Thermal model parameters (`thermal.py`)

**These are not literature values and must never be presented as such.**

The thermal model treats the engine as three lumps of metal that heat and cool:
the **block** (slow, minutes), the **oil** (medium), and the **turbine housing**
(fast, under a minute). Two kinds of number describe each lump:

- **C** = heat capacity — how much heat it takes to warm that lump by one degree
- **UA** = heat transfer — how fast heat moves in or out of it

| parameter | value | what it is | status |
|---|---|---|---|
| `ua_block_oil` | 800 W/K | how fast heat moves between oil and coolant | **WE MEASURED IT** — fitted to the oil-minus-coolant gap across three drives (median −1.2 K, p95 +5.4 K). Swept table in `thermal.py`. Cite our own logs |
| `c_block` | 105 000 J/K | heat capacity of the block + coolant | **ASSUMED** — metal mass × specific heat |
| `c_oil` | 12 000 J/K | heat capacity of the oil | **ASSUMED** — sump volume × oil properties |
| **`c_turb`** | **6 000 J/K** | **heat capacity of the turbine housing** | **ASSUMED — AND IT IS LOAD-BEARING. See below.** |
| `ua_gas_turb` | 0.90 W/K per g/s | how fast exhaust heats the turbine | **ASSUMED** |
| `ua_block_amb` / `ua_oil_amb` / `ua_turb_amb` | 45 / 60 / 18 W/K | heat lost to the surrounding air | **ASSUMED** |
| `ua_rad_*` | 300 / 60 / 700 | radiator performance | **CANNOT BE DETERMINED ON THIS CAR.** Two fitting attempts failed (R² 0.157, physically impossible negative coefficient). Every water-pump channel reads zero, so coolant flow is unknown and the heat equation cannot be formed. Deliberately left alone — **report as a limitation, do not fix quietly** |
| `frac_fuel_to_coolant` | 0.26 | fraction of fuel energy that ends up in the coolant | **ASSUMED** — close to the textbook energy split, not sourced to a page |
| `frac_fuel_to_oil` | 0.050 | same, for the oil | **ASSUMED** |
| `t_stat_open` | 88 °C | thermostat opening temperature | **UNVERIFIED — B58 service data** |

### `c_turb` needs a sentence in the thesis, and it is not a weakness

τ = C ÷ UA. C here is **assumed**, not measured. A reader could object that the
whole H/τ result rests on a guessed number.

**The design already answers this.** `generality_test.py` deliberately sweeps
`c_turb` from 800 to 60 000 J/K — a factor of 75 — precisely because the claim
is about the **ratio H/τ**, not about one engine's heat capacity. If the curve
holds across that sweep, the exact value of `c_turb` does not matter.

**Say this out loud in Chapter 3.** Unstated, it looks like an unexamined
assumption. Stated, it is the reason the experiment is designed the way it is.

---

## 5. Numbers that need no external source — they are ours (kind 1)

All from 168.1 minutes of our own logs, all regenerated by a script anyone can
run. **This is the strongest tier in the project.**

- 22 operating points, 30–74 kPa manifold pressure
- the spark map fit — 11 points, residual RMS 1.66°
- enrichment v4 — 1055 samples above 180 kPa, correlations −0.56 / −0.49 / −0.47
- the compressor envelope, and its 1020 kg/h air-flow sensor ceiling
- knock retard, 99th percentile 9.8°, from 10 896 filtered samples
- the oil–coolant heat transfer (800 W/K, section 4)
- charge temperature — within 3.0 % of the car's own boost sensor
- the round-robin logging discovery — the logger records one channel per row,
  confirmed to the decimal by `pull01`: 7 channels at 4.90 Hz gives 1.45 s per
  channel against 1.43 s predicted, 5.2x faster than the 26-channel drive
- **the pre-throttle temperature sensor's own time constant, ~10 s**, fitted on
  `pull01`: treating it as a lagged compressor outlet raises the correlation
  from +0.35 to **+0.95**, with compressor efficiency ~0.55-0.65 and a +11.7 K
  heat-soak offset. This is OUR measurement of a sensor, not a literature value

---

## 6. What to do with this file

1. **Row 7 first** (turbine time constant). Then the rest of section 3.
2. **Section 2 next** — one visit to BMW/Toyota service documentation settles
   most of it at once.
3. Add a `source` column to `validation_table.md` pointing at these row numbers.
4. Anything still UNVERIFIED at submission gets said plainly in Chapter 3:
   *"engineering-judgement band, not a sourced one."* That costs far less than
   being caught with an invented citation.

**The honest position, which is a strong one:**

> Everything we claim about *this car* comes from our own logs and is
> reproducible by script. Everything we claim about *engines in general* comes
> from published correlations, and we report which of our numbers fall outside
> them rather than adjusting the model to fit.

That second sentence is what makes 8-of-11 better than 11-of-11.

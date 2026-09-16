# REFERENCES.md — where every number that we did not measure comes from

**Written to be read by someone who is not an engine specialist.** Every
technical term below has a plain-English explanation beside it. If a row is
unclear, that is a defect in this file, not in the reader.

Created 12 September 2026, because `validate.py` compares eleven of our model's
outputs against "published bands" and the repository cited exactly **one**
source for all eleven: the word "Heywood" in a code comment, with no edition
and no page number. If an examiner asks *"where does 115–140 °C come from?"*,
that is not an answer.

**Updated 14 September 2026** after a research pass that opened manufacturer
specification sheets, patents, journal papers and a scanned textbook. Section 7
lists exactly which documents were opened and which were not. Nothing in this
file was promoted from memory; every locator below was read off the page, and
where the page was only seen through a tool's rendering the row says so.

---

## First, the four kinds of number in this project

This is the most important section. A reader who understands this table can
follow everything else.

| kind | what it means | can it be checked? |
|---|---|---|
| **1. We measured it** | It came out of 175.5 minutes of OBD-II logs from our own car | Yes — re-run the script |
| **2. General engine physics** | True of any petrol engine, from textbooks and papers | Yes — open the book |
| **3. Specific to the B58** | Only BMW or Toyota can tell you; it is a fact about this engine, not about engines in general | Only with factory documentation |
| **4. We assumed it** | A reasonable engineering estimate nobody has verified | **No.** Must be declared as an assumption |

**The project's strength is kind 1.** The risk is presenting kind 4 as if it
were kind 2 or 3. This file exists to stop that.

## Second, what the status words mean here

| status | meaning |
|---|---|
| **CONFIRMED** | Someone opened the source and found the claim on a page, table, column or paragraph that is written in the row. For a bibliographic record it means the record was checked against the publisher or an index. |
| **PARTIAL** | A source was opened and supports part of the claim — one measured value inside a band, a qualitative statement, or the record but not the page. What it does *not* support is written in the row. |
| **UNVERIFIED** | The number is standard and probably right, but **nobody has opened a source that states it.** The source named is *where to look*, not a citation that has been checked. |
| **MEASURED (ours)** | No external source is needed or exists: the figure comes from our own logs and a script regenerates it. |
| **MODELLING EQUIVALENT** | The model has a knob for something the real engine does differently. The knob is identified from our own data and must never be cited to the manufacturer. |

**Never move a row to CONFIRMED without opening the source and writing down
the page.** Never fill one in from memory — anyone's, including an AI's. A
fabricated citation is worse than a missing one, because no script can catch
it. When a page was only seen through an automated fetch tool's rendering
rather than the raw document, the row says "as rendered".

---

## 1. The methods our simulator uses — general engine physics (kind 2)

These are named, standard methods. They apply to **any** petrol engine, not just
the B58, so a general source is the correct source here. All six records were
re-checked against publisher or catalogue records on 14 September; the changes
that produced are noted in each row.

| what it is | plain English | citation | status |
|---|---|---|---|
| **Wiebe function** | A formula describing how fast the fuel burns once the spark fires — burning is not instant, it takes a few thousandths of a second, and this curve is its shape | Vibe (Wiebe), I. I., *Brennverlauf und Kreisprozess von Verbrennungsmotoren*, Verlag Technik, Berlin, 1970, 286 pp. German translation from the Russian (translator Joachim Heinrich; German editing Franz Meissner). [Open Library OL5771526M](https://openlibrary.org/books/OL5771526M); LCCN 71509128; OCLC 17395956 | **CONFIRMED** (record). The catalogue prints the publisher as "Verlag Technik", without the "VEB" prefix this file used to carry; no catalogue that could be opened shows "VEB", so it was dropped |
| Wiebe — easier modern citation | A 2010 review article; cite this if the 1970 German book is hard to obtain | Ghojel, J. I., "Review of the development and applications of the Wiebe function: A tribute to the contribution of Ivan Wiebe to engine research", *International Journal of Engine Research* **11**(4), 2010, pp. 297–312, SAGE — [DOI 10.1243/14680874JER06510](https://doi.org/10.1243/14680874JER06510) | **CONFIRMED** (record, via Crossref; the SAGE page blocks automated readers but the DOI resolves). Full title and volume/issue/pages added 14 Sep |
| **Woschni correlation** | A formula for how fast heat leaks from the burning gas into the metal walls of the cylinder. Without it the model would predict the engine runs far hotter than it does | Woschni, G., "A Universally Applicable Equation for the Instantaneous Heat Transfer Coefficient in the Internal Combustion Engine", SAE Technical Paper **670931**, 1967 (presented 30 Oct 1967, Pittsburgh) — [SAE Mobilus](https://saemobilus.sae.org/content/670931), doi:10.4271/670931 | **CONFIRMED** (record, SAE Mobilus and Crossref) |
| **Chen–Flynn FMEP model** | FMEP = the engine's internal friction, expressed as pressure. Some of the power made inside the cylinder is eaten by the engine rubbing against itself before it reaches the wheels; this estimates how much | Chen, S. K. and Flynn, P. F., "Development of a Single Cylinder Compression Ignition Research Engine", SAE Technical Paper **650733**, 1965 (presented 18 Oct 1965, Cleveland) — [SAE Mobilus](https://saemobilus.sae.org/content/650733), doi:10.4271/650733 | **CONFIRMED (record only).** The paper exists with these authors, number and year, but its title and abstract are about building a research engine and say nothing about friction. That the FMEP correlation in `plant.py` comes from a page of this paper has **not** been checked; friction-model papers do cite it. Before the thesis is frozen, cite the page that carries the correlation, or a secondary source that quotes it |
| **Douaud & Eyzat knock integral** | "Knock" is uncontrolled detonation — the fuel exploding instead of burning smoothly. It destroys engines. This formula predicts when it will happen | Douaud, A. M. and Eyzat, P., "Four-Octane-Number Method for Predicting the Anti-Knock Behavior of Fuels and Engines", SAE Technical Paper **780080**, 1978 (Institut Français du Pétrole; presented 27 Feb 1978, Detroit) — [SAE Mobilus](https://saemobilus.sae.org/papers/four-octane-number-method-predicting-anti-knock-behavior-fuels-engines-780080), doi:10.4271/780080 | **CONFIRMED** (record; the abstract confirms it is the autoignition-delay paper) |
| **General reference** | The standard graduate textbook on petrol and diesel engines | Heywood, J. B., *Internal Combustion Engine Fundamentals*, 2nd ed., McGraw-Hill Education, May 2018, 1056 pp., ISBN 9781260116106 (1st ed., McGraw-Hill, 1988) | **CONFIRMED** (record, Open Library and Google Books). The 2018 publisher is "McGraw-Hill Education"; plain "McGraw-Hill" is the 1988 edition's string. The page references used in section 3 come from a scanned copy whose edition is not stated on the scan — see section 7 |
| **Bosch relative air charge** | Defines what BMW's "relative air filling" channel actually means — the reference air density it is measured against. This is what our constant k converts between | Robert Bosch GmbH, US Patent **6,588,261 B1** (Wild, Reuschenbach, Benninger, Hess, Zhang, Mallebrein, von Hofmann; granted 8 Jul 2003; priority DE 197 13 379, 1 Apr 1997), **column 3 line 55 to column 4 line 2**: *"Definition of rl as the relative air filling in the combustion chamber: rl = ma/m_norm = (ps − pirg)·Tn/(Pn·Ts) under the standard conditions: Tn=273 K, Pn=1013 hPa"*; also column 3 lines 8–10: *"This standardization also applies to an air temperature of 273° K. and a pressure of 1013 hPa upstream from the throttle valve."* Same family as [EP 1 015 746 B1](https://patents.google.com/patent/EP1015746B1/de) (German original, grant published 10 Sep 2003), description paragraph reported as [0021] by the EPO server's rendering — verify the paragraph number on the EPO PDF. Corroborated by US 6,754,577 B2 (Bosch, 2004): "a standard pressure p₀ of 1013.25 hPa, a standard temperature T₀ of 273 Kelvin" | **CONFIRMED** — page located 14 Sep, read off the patent's page image. Two caveats. (a) Bosch writes 273 K and 1013 hPa; "0 °C" is our gloss, not their wording. (b) That BMW's OBD channel uses this definition is **not** in any source; it rests on our own inversion (CLAUDE.md mistake 12: implied reference 276.9 K, consistent with 273 K, excludes 20 °C). The Bosch handbook page (*Gasoline-Engine Management*) is still not located; Google Books shows the passage exists but no page number |

---

## 2. Facts about the B58 specifically (kind 3)

**These cannot come from a textbook.** They are facts about one engine, and only
the manufacturer can supply them. Manufacturer documents were opened on
14 September; the geometry is settled, the thermal rows are not, and the
compression ratio turned out to depend on something the project has not yet
recorded about its own car.

| what | our value | what the manufacturer documents say | status |
|---|---|---|---|
| **Displacement** — total swept volume of all six cylinders | 2997.5 cc | Toyota Australia, *GR Supra Mechanical Specifications*, document GTP-009045, version July 2025, p. 1, block ENGINE: "Displacement (cm³) 2998". BMW, *The new BMW 3 Series Sedan / Touring, Specifications*, 05/2015, p. 7 (340i): "Effective capacity cc 2998". Toyota Motor Corporation global newsroom, 28 Nov 2024, release 41894560, specification table: "Displacement [liters] 2.997". Our 2997.5 is π/4 × 82.0² × 94.6 × 6 and sits between the two published roundings; say so rather than treating either as a discrepancy | **CONFIRMED** |
| **Bore** — cylinder diameter | 82.0 mm | Identical in every manufacturer document opened: Toyota Australia GTP-009045 p. 1 "Bore (mm) 82"; BMW Canada, *BMW Z4 2020MY Product Guide*, p. 2, "Motor data", Z4 M40i column: "Bore, mm 82"; BMW 3 Series 05/2015 p. 7 "Stroke/bore mm 94.6/82.0"; Toyota global newsroom 28 Nov 2024 "Bore x stroke [mm] 82.0 x 94.6"; Toyota UK technical specifications (Feb 2021 ref. 210223M, June 2022 ref. 220605M, Feb 2024) p. 1 "Bore x stroke (mm) 82 x 94.6" | **CONFIRMED** |
| **Stroke** — how far the piston travels | 94.6 mm | Same documents and pages as the bore | **CONFIRMED** |
| **Compression ratio** — how much the piston squeezes the air before ignition | 10.2:1 | **The engine code B58B30O1 goes with 10.2:1 in four manufacturer documents:** BMW Canada Z4 2020MY Product Guide p. 2 ("Engine type B58B30O1 … Compression rate, :1 10.2 … 285 kW / 382 bHP at 5800–6500 rpm"); Toyota Australia GTP-009045 p. 1 ("Engine model code B58B30O1 … Compression ratio 10.2:1 … 285 kW @ 5800–6500"); BMW, *M340i xDrive Specifications*, 10/2019, p. 1 ("2998 … 94.6/82.0 … Compression ratio :1 10.2 … 275/374 kW/hp"); Toyota Canada press release, Toronto, 14 Feb 2020, *Toyota GR Supra Races Into 2021 with More Power…*: "A new piston design reduces the engine's compression ratio from 11:1 to 10.2:1" as output rose from 335 hp to 382 hp. Toyota Canada, 28 Apr 2022, *…Enhanced Drive Dynamics for 2023*: the 2023 GR Supra 3.0 is the 382 hp car. **But the ratio follows the engine version, not the model year:** the 340 PS / 250 kW GR Supra 3.0 sold in the UK and Europe is printed at **11.0:1** on Toyota UK's own specification sheets of Feb 2021, June 2022 and Feb 2024 (p. 1: "Compression ratio 10.2:1 11.0:1", the first figure being the 2.0-litre), and every 2015–2021 BMW sheet for the original B58 (code B58B30M0 on the 2018 US 5 Series sheet) prints 11.0:1 | **CONFIRMED that B58B30O1 = 10.2:1. OPEN: which version our car is.** Settle it from the car's rated output on its registration, compliance plate or dealer paperwork: 285 kW (382 hp / 387 PS) means 10.2:1; 250 kW (340 PS / 335 bhp) means 11.0:1. Our logs cannot tell the two apart on their own. If it is the 250 kW car, the project's value is wrong and the knock prediction must be re-run |
| **Thermostat opening temperature** — the valve that lets coolant reach the radiator | 88 °C | **The B58 has no thermostat.** BMW Group University Technical Training, *Technical training. Product information. B58 Engine*, course ST1505, information status April 2015, section 4.2 p. 38: *"The conventional thermostat in the B58 engine is replaced by a so-called heat management module."* Section 4.2 p. 39: *"In contrast to a map controlled thermostat with expansion element, there is no direct, physical connection to the coolant temperature"* — the module is a motor-driven rotary valve positioned by the engine computer from the coolant temperature and a cylinder-head metal temperature. No opening temperature is printed anywhere in its cooling chapter. (Unofficial copy on archive.org; page numbers taken from the OCR text and to be checked against the PDF) | **MODELLING EQUIVALENT.** Our 88 °C is the point at which `thermal.py`'s stand-in thermostat cracks, identified from the car's own coolant channel. It must not be cited to BMW |
| **Coolant operating band** | 88–108 °C | BMW publishes no setpoint. ST1505 section 4.2.2 pp. 43–45 lists five control phases (cold start, warm-up, operating temperature, transfer, maximum cooling) with no temperature for any of them. Our logs sit at 88–97 °C throughout | **MEASURED (ours)** for the lower part; the 108 °C upper edge is engineering judgement and is not observed in any log |
| **Oil operating band, sustained load** | 115–140 °C | Searched SAE, MTZ, patents and handbooks; nothing admissible states a sustained-load oil band for this or any modern engine. ST1505 section 4.1 p. 37 confirms only the structure: *"the engine oil as well as the transmission fluid are cooled using coolant"* through an oil/coolant heat exchanger in the filter module, which is what our `ua_block_oil` term models. **Our model gives 110.2 °C and we report this as a MISS** | **UNVERIFIED.** The only numbers found were on owner forums, which cannot be cited |

> **Note on sources for this section.** Wikipedia's B58 article carries the bore,
> stroke and displacement figures and they match our model exactly, but
> Wikipedia is not an acceptable thesis citation; the manufacturer sheets above
> replace it. **Forum posts are not sources.** Searching for B58 oil temperatures
> returns mostly owner forums. Those cannot go in a thesis at any price.
>
> **A trap for anyone re-searching the compression ratio.** Third-party
> specification aggregators splice the North American "382 hp" with the
> European "11.0:1"; a listing that pairs those two is two markets stitched
> together and is not a manufacturer figure.
>
> **Grey source.** ST1505 is a BMW training document obtained as an unofficial
> archive.org copy. It is the only BMW document opened that describes the
> cooling system. Quote it as what it is and let the supervisor decide whether
> it may be cited; the official alternative is the BMW-authored MTZ article in
> section 7, which nobody has opened past its abstract.

---

## 3. The eleven validation bands — status after the 14 September pass

Every band `validate.py` scores against. Before 14 September none had been
checked against a source. Now: rows 1 and 2 are CONFIRMED, row 7 is PARTIAL,
row 10 is ours, and **seven rows (3, 4, 5, 6, 8, 9, 11) remain UNVERIFIED** and
must be called engineering-judgement bands in Chapter 3. Two of those seven
(rows 3 and 5–6) were searched hard and the opened sources point *away* from
the band as written; that is recorded below rather than hidden.

The "kind" column says whether a general textbook will do, or whether this
needs BMW-specific data.

| # | quantity | plain English | band | kind | status | what was found (14 Sep) |
|---|---|---|---|---|---|---|
| 1 | Displacement | engine size | 2990–3000 cc | **B58** | **CONFIRMED** | section 2 |
| 2 | MFB50 at MBT | The crank angle by which half the fuel has burned, at the spark timing that makes the most torque. If burning finishes too early or too late you lose power | 8–10° after top-dead-centre | general | **CONFIRMED** (as the common rule; it is engine-dependent) | Zhu, Haskara & Winkelman 2007, p. 417: "between 8 and 10 [°] after TDC when MBT timing is achieved"; Heywood scan: "half the charge is burned at about 10° after TC" (a single value, not a band); Machado et al. 2015, abstract as rendered: the industry adopts 8°–10° for CA50. Caveat: Klimstra 1985 (abstract) puts the optimum at 7–8°, so the thesis should say "commonly 8–10°, engine-dependent" |
| 3 | Best BSFC | Fuel used per unit of work done — the engine's best-case efficiency | 235–260 g/kWh | general | **UNVERIFIED** — opened sources bracket the band but none states it | Heywood scan, eq. 2.22 context: "For SI engines typical best values of brake specific fuel consumption are about 75 μg/J = 270 g/kW·h" — *above* the band. Conway et al. 2018, p. 5: "The best BSFC of 233 g/kWh (35.8% brake thermal efficiency or BTE) was achieved at 2500 rpm 12 bar BMEP" on a production-like 1.6 L turbo GDI calibration — *below* the band. Our 241.2 g/kWh sits between them. Do not change the band; state it as judgement bracketed by 233 and 270, or cite both. The B58's own fuel-consumption map is in the MTZ article of section 7, unopened |
| 4 | Knock-limited spark | How far the spark can be advanced at high load before detonation starts | 8–14° | **B58-ish** | **UNVERIFIED — expected, and confirmed by searching** | SAE knock-limit papers, MIT and MTU theses and knock-model papers were searched; not one admissible page states a knock-limited spark value near 3000 rpm and 200 kPa. Douaud & Eyzat gives the knock *model*, not this band. **Weakest of the eleven.** Drop the row from the thesis, or keep it labelled as an internal consistency check |
| 5 | EGT cruise, min | Exhaust gas temperature at steady cruise | 600–750 °C | general | **UNVERIFIED** | No opened source states a part-load cruise range. Heywood presents port-exit temperature against load and speed in Fig. 6-22 (Sec. 6.5), but the numbers are in the figure, which nobody has opened; his chapter 11 remarks that a conventional engine's manifold temperature "is not sufficient" for thermal-reactor oxidation at about 600–700 °C, which leans against the band. The only measured figures found are full-load protection limits on a modern turbo GDI: 900 °C at the exhaust port, 930 °C pre-turbine (Conway et al. 2018, p. 10). State which temperature the band means: thermocouple readings sit roughly 100 K below mass-averaged port temperature (Heywood, Sec. 6.5) or about 20 K below the time-averaged value (Caton 1982, abstract) |
| 6 | EGT cruise, max | as above | 600–750 °C | general | **UNVERIFIED** | as above |
| 7 | **Turbine housing time constant** | How long the turbocharger takes to heat up — technically, to reach 63 % of the way to its final temperature after a step change in load | 40–120 s | **B58** | **PARTIAL** | Burke, Vagg, Chalet & Chesse 2015, section 5.3: after a load step on a 2.2-litre diesel with a variable-geometry turbocharger, the gas-to-housing heat flow "peaks at the beginning of the transient (in this case at around 7kW) before slowly falling to a value of around 3.6kW three minutes later. This spike in heat flow is accounted for by the accumulation of heat in the turbine housing as it warms up"; their protocol holds each step three minutes because "this allows for the system to stabilise". Settling within about three minutes bounds the housing time constant from above at roughly 45–60 s, consistent with our 48.0 s and inside the band. **What it does not do:** it reports no time constant, supports neither the 40 s floor nor the 120 s ceiling, and is a diesel turbocharger, not a B58. **No opened source publishes a turbine-housing heat capacity in J/K**, so `c_turb` cannot be cross-checked; see section 4 |
| 8 | Oil temperature, sustained climb | how hot the oil gets on a long hard climb | 115–140 °C | **B58** | **UNVERIFIED** | section 2, oil row |
| 9 | Oil time constant | how long the oil takes to heat up | 20–400 s | **B58** | **UNVERIFIED** | Jarrier et al. 2000 (abstract): oil temperature "lags behind the water one" — supports the ordering in `thermal.py`, gives no number |
| 10 | Coolant, thermostat-regulated | steady coolant temperature once warm | 88–108 °C | **B58** | **MEASURED (ours)** | 88–97 °C in every log; BMW publishes no band (section 2). Our model's 94.5 °C is a comparison against our own data, not against a published figure |
| 11 | Coolant apparent time constant | how long the coolant takes to respond | 1–600 s | **B58** | **UNVERIFIED** | The band is so wide it asserts almost nothing. A documented way to *measure* it instead was seen only in a search snippet (US 6,732,025 B2: time the decay to 36.8 % of the initial difference after shutdown) and was not confirmed on the page. Better: drive `thermal.py` over a whole log, as CLAUDE.md already says |

### Why row 7 comes first

**The entire thesis claim is H/τ** — preview horizon divided by the time
constant of the part being protected. **τ for the turbine is row 7.**

If that band is wrong, every point on the H/τ curve sits in the wrong place.
No other row can move the headline result. It is now PARTIAL: the one measured
load-step transient that could be opened settles within three minutes, which is
consistent with our 48 s, but nobody has published the housing time constant
itself. The two documents most likely to contain it are listed first in
section 7.

### Why row 4 is the weakest

Douaud & Eyzat is correctly cited for the knock *calculation*. But "a production
turbocharged engine runs 8–14° of spark at 3000 rpm and 200 kPa" is a **separate
claim about real engines**, and after a deliberate search nothing supports it.
Drop the row, or keep it as an internal check with no "published" label.

---

## 4. Thermal model parameters (`thermal.py`)

**These are not literature values and must never be presented as such.**

The thermal model treats the engine as three lumps of metal that heat and cool:
the **block** (slow, minutes), the **oil** (medium), and the **turbine housing**
(fast, under a minute). Two kinds of number describe each lump:

- **C** = heat capacity — how much heat it takes to warm that lump by one degree
- **UA** = heat transfer — how fast heat moves in or out of it

| parameter | value | what it is | status |
|---|---|---|---|
| `ua_block_oil` | 800 W/K | how fast heat moves between oil and coolant | **WE MEASURED IT** — fitted to the oil-minus-coolant gap across three drives (median −1.2 K, p95 +5.4 K). Swept table in `thermal.py`. Cite our own logs. BMW's ST1505 confirms the structure (oil cooled by coolant through an exchanger in the filter module) but no number |
| `c_block` | 105 000 J/K | heat capacity of the block + coolant | **ASSUMED** — metal mass × specific heat |
| `c_oil` | 12 000 J/K | heat capacity of the oil | **ASSUMED** — sump volume × oil properties |
| **`c_turb`** | **6 000 J/K** | **heat capacity of the turbine housing** | **ASSUMED — AND IT IS LOAD-BEARING. See below.** No opened source publishes a housing heat capacity. Burke, Olmeda, Arnau & Reyes-Belmonte 2014 (abstract) report that the heat-transfer model's parameters move "housing temperatures by up to 80 °C" and that "errors in the thermal capacitance also lead to errors" in transient simulation — a citable statement that this is the sensitive, uncertain parameter |
| `ua_gas_turb` | 0.90 W/K per g/s | how fast exhaust heats the turbine | **ASSUMED** |
| `ua_block_amb` / `ua_oil_amb` / `ua_turb_amb` | 45 / 60 / 18 W/K | heat lost to the surrounding air | **ASSUMED** |
| `ua_rad_*` | 300 / 60 / 700 | radiator performance | **CANNOT BE DETERMINED ON THIS CAR.** Two fitting attempts failed (R² 0.157, physically impossible negative coefficient). Every water-pump channel reads zero, so coolant flow is unknown and the heat equation cannot be formed. A third reason appeared on 14 September: the real radiator branch is opened by a commanded valve angle (the heat management module), not by coolant temperature, so even a flow signal would not close the equation without the valve position. Deliberately left alone — **report as a limitation, do not fix quietly** |
| `frac_fuel_to_coolant` | 0.26 | fraction of fuel energy that ends up in the coolant | **ASSUMED** — close to the textbook energy split, not sourced to a page |
| `frac_fuel_to_oil` | 0.050 | same, for the oil | **ASSUMED** |
| `t_stat_open` | 88 °C | the point at which the model's stand-in thermostat starts to open | **MODELLING EQUIVALENT** — the real engine has a heat management module, not a thermostat (section 2). Identified from the logged coolant channel; never cite it to BMW |

### `c_turb` needs a sentence in the thesis, and it is not a weakness

τ = C ÷ UA. C here is **assumed**, not measured. A reader could object that the
whole H/τ result rests on a guessed number.

**The design already answers this.** `generality_test.py` deliberately sweeps
`c_turb` from 800 to 60 000 J/K — a factor of 75 — precisely because the claim
is about the **ratio H/τ**, not about one engine's heat capacity. If the curve
holds across that sweep, the exact value of `c_turb` does not matter. The
Burke et al. 2014 abstract quoted above is the published reason the capacitance
deserves to be swept rather than trusted.

**Say this out loud in Chapter 3.** Unstated, it looks like an unexamined
assumption. Stated, it is the reason the experiment is designed the way it is.

---

## 5. Numbers that need no external source — they are ours (kind 1)

All from 175.5 minutes over nine drives of our own logs (six carrying usable
samples), all regenerated by a script anyone can run. **This is the strongest
tier in the project.** `verify_docs.py` opens this file and checks the figures
in this section against the shipped data, so they cannot drift.

- 22 distinct operating points; vehicle validation covers 30–74 kPa manifold
  pressure only
- the spark map fit — 11 points, residual RMS 1.66°
- enrichment v4 — 1055 samples above 180 kPa, correlations −0.56 / −0.49 / −0.47
- the compressor envelope, and the 1020 kg/h air-flow sensor ceiling, pinned on
  517 samples across five separate drives
- knock retard, 99th percentile 9.8°, from 10 896 filtered samples
- the oil–coolant heat transfer (800 W/K, section 4)
- charge temperature — within 3.0 % of the car's own boost sensor
- the round-robin logging discovery — the logger records one channel per row
- the coolant regulation band, 88–97 °C in every log (section 2)


---

## 5b. The live app's own numbers — added 16 September 2026

`app/` runs the same plant and the same thermal network beside the car in real
time, so **every number in sections 1–5 applies to it unchanged, including every
UNVERIFIED and ASSUMED one.** It introduces no new physics. It does introduce
five numbers of its own, and they divide into two kinds that must not be
confused.

### Measured on our own logs (kind 1)

| number | what it is | where it came from |
|---|---|---|
| **1020.0 kg/h** | the air-mass sensor ceiling the app refuses to trust | 573 pinned samples across 6 of the 9 raw logs; 517 across 5 after the warm filter. Already in section 5 |
| **6.0 s** | the channel refresh interval on a 26-channel log, which sets how long a detection window must span | measured directly on `7475b5d7`: air mass 6.00 s, boost 6.00 s, engine speed 6.00 s, ambient pressure 18.0 s |
| **7.5 s / 1.45 s** | per-channel rate at 26 and 7 channels — the whole justification for keeping the live set to six | `7475b5d7` against `pull01`, CLAUDE.md mistake 13b |
| **13.6 %** | the worst windowed disagreement between inverted and measured pressure on a car with nothing wrong with it — the evidence behind the 25 % fault threshold | 45 gated windows across all nine drives, CLAUDE.md mistake 14 |

### Chosen by us, and defensible but not measured (kind 4)

| number | what it is | why this value, and what would change it |
|---|---|---|
| **PR ≥ 1.8** | the pressure ratio above which the app believes the throttle is not restricting, so the comparison is valid | the median disagreement stops moving there (+6.5 %) and the tail is mostly gone. 1.7 and 2.0 give 17.5 % and 9.6 % of samples over threshold against 14.1 %. **A judgement call on a continuum, not a measured boundary** |
| **25 %** | the disagreement the app calls a fault | 11 points above the worst healthy window measured (13.6 %). The margin is chosen; the 13.6 % is not |
| **25 K** | the seed-uncertainty width below which the app stops calling the estimate unknown | the thermal alert projects 30 s ahead at 1–4 K/s, i.e. 30–120 K of lead, so 25 K is small against the lead the alert is built on. **Reasoned from the alert's own design, not measured** |

### The one that matters most, and it is ASSUMED

The app's headline output is an estimated turbine housing temperature. Its time
constant, and therefore everything the app says about how fast the housing is
heating, rests on **`c_turb = 6000 J/K`** — which section 4 marks **ASSUMED**,
and which is the same constant that sets the τ in this project's central H/τ
ratio.

**Say this in the thesis in one sentence, beside the screenshot.** *The app
displays a modelled temperature, not a measurement; the model's heat capacity is
an engineering estimate, and the vehicle publishes no turbine temperature
against which it could be checked.* A number on a dashboard reads as a
measurement to everyone who did not write it, and that is precisely the
impression this file exists to prevent.

### What the app is NOT evidence for

- **It has never been shown a fault.** Nothing in nine drives is broken, so
  every figure behind the mismatch detector is a FALSE-POSITIVE rate. None of
  them is a detection rate, and the difference is the whole of the claim.
- **It has never run against the car.** Every number above is from replay.
- **Its alert counts are not measurements of the vehicle.** 13 thermal / 0
  mismatch / 19 novel on `7475b5d7` is a property of thresholds we chose. They
  are pinned so a regression is visible, which is a different job.
---

## 6. What to do with this file

1. **Settle which engine version the car is** (section 2, compression ratio).
   One line on the registration or compliance plate does it.
2. **Row 7 next**: open Burke 2014 (section 7, first item) for the housing heat
   capacity, and Burke et al. 2015 for the temperature traces behind the
   three-minute settling.
3. **Get the MTZ article** (section 7) through the library. It is the only
   BMW-authored document on this engine and may carry the fuel-consumption map
   for row 3 and the cooling description that would replace the grey ST1505.
4. `validation_table.md` carries a `source` column pointing at the row numbers
   here; keep the two files' row numbers aligned.
5. Anything still UNVERIFIED at submission gets said plainly in Chapter 3:
   *"engineering-judgement band, not a sourced one."* That costs far less than
   being caught with an invented citation.

**The honest position, which is a strong one:**

> Everything we claim about *this car* comes from our own logs and is
> reproducible by script. Everything we claim about *engines in general* comes
> from published correlations, and we report which of our numbers fall outside
> them rather than adjusting the model to fit.

That second sentence is what makes 8-of-11 better than 11-of-11.

---

## 7. What the 14 September pass opened, and what it did not

Everything in this section was read from the document itself, except where a
row says "abstract" (only the abstract page was opened) or "as rendered" (the
page was seen through an automated fetch tool's summary rather than raw text).
Saved copies of the manufacturer PDFs and the extracted texts are in the
session's scratch directory, not in the repository.

### Manufacturer documents (kind 3)

- **Toyota Australia**, *GR Supra — Mechanical Specifications*, spec table
  GTP-009045, "Version: July 2025", 2 pp. Page 1: engine model code B58B30O1,
  bore 82, stroke 94.6, 2998 cm³, compression ratio 10.2:1, 285 kW at
  5800–6500 rpm, 500 Nm at 1800–5000 rpm.
  `toyota.com.au/-/media/toyota/main-site/vehicle-hubs/supra/files/20250725_gr_supra_spec_table_gtp009045.pdf`
- **Toyota Motor Corporation global newsroom**, 28 Nov 2024, release 41894560,
  *TGR Announces Partially Upgraded Supra (3.0-liter) and Special-edition Supra
  "A90 Final Edition"*: engine type B58B30O1, displacement 2.997 L, bore × stroke
  82.0 × 94.6, 285 kW (387 PS) at 5,800 rpm. No compression-ratio row.
- **Toyota Canada**, Toronto, 14 Feb 2020, *Toyota GR Supra Races Into 2021 with
  More Power and First-Ever Four-Cylinder Turbo Model*: "A new piston design
  reduces the engine's compression ratio from 11:1 to 10.2:1"; 335 hp (2020) to
  382 hp (2021). The Toyota USA original refuses automated readers; cite the
  Canadian mirror or open the US page in a browser.
- **Toyota Canada**, Toronto, 28 Apr 2022, *Toyota GR Supra Adds Manual
  Transmission and Enhanced Drive Dynamics for 2023*: the 2023 GR Supra 3.0 is
  the 382 hp engine.
- **Toyota (GB)**, *Toyota GR Supra Technical Specifications*, Feb 2021
  (ref. 210223M), June 2022 (ref. 220605M) and Feb 2024 sheets, p. 1 of 3, and
  p. 16 of the June 2022 and Feb 2024 press packs: 2,998 cc, 82 × 94.6,
  **compression ratio 11.0:1** for the 335 bhp / 340 DIN hp / 250 kW 3.0-litre
  (the 10.2:1 in the same row is the 2.0-litre).
- **BMW Group Canada**, *BMW Z4 2020MY Product Guide*, PressClub attachment
  T0304258EN/444868, p. 2, "Motor data", Z4 M40i column: engine type B58B30O1,
  stroke 94.6, bore 82, 2998 cm³, compression rate 10.2:1, 285 kW / 382 bHP at
  5800–6500 rpm. **The strongest single document for the project's pairing.**
- **BMW Group**, *M340i xDrive Specifications*, 10/2019, PressClub attachment
  T0302031EN/440594, p. 1: 2998 cc, 94.6/82.0, compression ratio 10.2, 275 kW.
- **BMW of North America**, *The All-New 2020 BMW M340i and M340i xDrive
  Sedans*, PressClub T0286917EN_US, 13 Nov 2018, engine table as rendered:
  B58, 2,998 cm³, 82 × 94.6, compression rate 10.2, 382 hp at 5,800–6,500 rpm.
- **BMW Group**, *The new BMW 3 Series Sedan / Touring, Specifications*,
  05/2015, PressClub attachment T0234765EN/349813, p. 7 (340i): 2998 cc,
  94.6/82.0, **compression ratio 11.0**, 240 kW. The launch engine. The same
  11.0 appears on the 540i xDrive Touring 02/2017 sheet (p. 3), the 2018 US
  5 Series technical data (p. 1, which prints the code **B58B30M0**), the X5
  xDrive40i 09/2018 and 03/2021 sheets and the X4 M40i 6/2018 sheet.
- **BMW of North America**, *The new BMW Z4*, PressClub T0285141EN_US,
  14 Jan 2019, as rendered: prints 11.0:1 next to 382 hp with the *older*
  engine's rpm bands. Contradicted by the three later documents above for the
  same engine; treat as a stale preliminary table and do not cite it.
- **BMW Group University Technical Training**, *Technical training. Product
  information. B58 Engine*, ST1505, information status April 2015, © 2015 BMW
  AG. Unofficial copy: archive.org item BMWTechnicalTrainingDocuments,
  "ST1505 B58 Engine/B58 Engine.pdf". Sections 3.4, 4.1, 4.2, 4.2.2 as quoted in
  section 2; page numbers from the OCR text, to be checked on the PDF.

### Journal papers, patents and the textbook (kind 2)

- **Burke, R. D., Vagg, C. R. M., Chalet, D., Chesse, P.**, "Heat transfer in
  turbocharger turbines under steady, pulsating and transient conditions",
  *International Journal of Heat and Fluid Flow* **52** (2015) 185–197,
  DOI 10.1016/j.ijheatfluidflow.2015.01.004. Accepted manuscript, University of
  Bath research portal (file 119302957/Accepted_version.pdf): section 5.3,
  manuscript lines 418–420 (quoted in row 7); section 4.3, lines 244–246
  (three-minute hold). Figure 17(a) holds the actual trace and has not been
  read.
- **Burke, R. D., Olmeda, P., Arnau, F., Reyes-Belmonte, M.**, "Modelling of
  Turbocharger heat transfer under stationary and transient conditions", 11th
  International Conference on Turbochargers and Turbocharging, London, 13–14
  May 2014. **Abstract only** (Bath portal), quoted in section 4.
- **Burke, R. D.**, "Analysis and modeling of the transient thermal behavior of
  automotive turbochargers", *Journal of Engineering for Gas Turbines and
  Power* **136**(10), 101511 (2014), DOI 10.1115/1.4027290. **Abstract only.**
  Its lumped model has a turbine node, so its parameter table should give the
  housing C and UA from which τ = C/UA follows. **First document to open for
  row 7.**
- **Romagnoli, A., Manivannan, A., Rajoo, S., Chiong, M. S., Feneley, A.,
  Pesiridis, A., Martinez-Botas, R. F.**, "A review of heat transfer in
  turbochargers", accepted manuscript in the Brunel University repository
  (handle 2438/15655; journal version ScienceDirect S1364032117306172, year and
  venue not printed on the manuscript). Section 6.8 paraphrases Burke et al.
  2015 as "6.6 kW to 0.6 kW in 100 s" and "half the initial value within three
  minutes"; **neither figure appears in the Burke text**, so cite the primary.
- **Zhu, G. G., Haskara, I., Winkelman, J.**, "Closed-Loop Ignition Timing
  Control for SI Engines Using Ionization Current Feedback", *IEEE Transactions
  on Control Systems Technology* **15**(3), May 2007, pp. 416–427. Author-hosted
  copy (egr.msu.edu), p. 417 and p. 424, quoted in row 2. Cite the IEEE record.
- **Machado, G. B., Cordeiro de Melo, T. C., Soares, L. A. M.**, "Flex Fuel
  Engine — Influence of Fuel Composition on the CA50 at Maximum Brake Torque
  Condition", SAE 2015-36-0215, DOI 10.4271/2015-36-0215. **Abstract, as
  rendered.**
- **Klimstra, J.**, "The Optimum Combustion Phasing Angle — A Convenient Engine
  Tuning Criterion", SAE 852090, DOI 10.4271/852090. **Abstract**: optimum
  phasing "close between 7 to 8 deg after Top Dead Centre".
- **Conway, G., Robertson, D., Chadwell, C., McDonald, J., Kargul, J., Barba,
  D., Stuhldreher, M.**, "Evaluation of Emerging Technologies on a 1.6 L
  Turbocharged GDI Engine", SAE 2018-01-1423, DOI 10.4271/2018-01-1423,
  EPA-hosted PDF: p. 5 (233 g/kWh best point) and p. 10 (900 °C port / 930 °C
  pre-turbine enrichment limit). The second figure is also a published
  comparison for the project's 1123 K protection trigger, which is about 80 K
  more conservative than that engine's enrichment limit.
- **Caton, J. A.**, "Comparisons of Thermocouple, Time-Averaged and
  Mass-Averaged Exhaust Gas Temperatures for a Spark-Ignited Engine",
  SAE 820050, DOI 10.4271/820050. **Abstract**: thermocouple reads about 20 K
  below the time-averaged gas temperature.
- **Jarrier, L., Champoussin, J., Yu, R., Gentile, D.**, "Warm-Up of a D.I.
  Diesel Engine: Experiment and Modeling", SAE 2000-01-0299,
  DOI 10.4271/2000-01-0299. **Abstract.**
- **Chen, Y., Lee, J., Holmer, J., Ha, J.**, "Model Predictive Control for
  Engine Thermal Management System", SAE 2021-01-0225, DOI 10.4271/2021-01-0225.
  **Abstract, as rendered.** Not a validation source — **prior art on the
  premise**: it schedules the coolant target from road-grade preview. It
  belongs in the literature review, and the H/τ criterion should be positioned
  as the thing that paper does not state.
- **Heywood, J. B.**, *Internal Combustion Engine Fundamentals*, scanned copy on
  archive.org (item InternalCombustionEngineJohnHeywood). The scan carries no
  edition, publisher or year; its figure and section numbering matches the
  1988 single-volume edition. The full-text search returned the passages quoted
  in rows 2, 3, 5 and 6 at **scan leaves** 403, 80, 261–262 and 688. A scan
  leaf is not a printed page number: read the folio off the page image before
  citing, and confirm the edition from the title-page scan. Google Books
  confirms the row-2 sentence survives into the 2018 edition but shows no page.
- **Robert Bosch GmbH**, US 6,588,261 B1 and EP 1 015 746 B1, US 6,754,577 B2 —
  see section 1. The US grant was read from page images of the USPTO PDF.
- **Landerl, C., Mattes, W., Rülicke, M., Durst, B.**, "The New BMW Inline
  Six-cylinder Gasoline Engine", *MTZ worldwide* **76**(10), Oct 2015,
  pp. 22–29, DOI 10.1007/s38313-015-0041-7. **Record confirmed via Crossref;
  full text not opened.** The BMW-authored design paper for this engine.
- **Steinparzer, F., Nefischer, P., Hiemesch, D., Rechberger, E.**, "The New
  BMW Six-cylinder Top Engine with Innovative Turbocharging Concept", *MTZ
  worldwide* **77**(10), 2016, pp. 38–45, DOI 10.1007/s38313-016-0104-4.
  **Record only**; which engine it describes is not shown.

### Still open, in order of value

1. **Which engine version the car is** — one look at the registration or
   compliance plate. Decides whether 10.2:1 is right (section 2).
2. **Burke 2014**, *J. Eng. Gas Turbines Power* 136(10) 101511: the turbine-node
   capacitance and conductances, hence a published C/UA to set against our
   48.0 s and 6000 J/K (row 7, section 4).
3. **Landerl et al. 2015**, MTZ worldwide 76(10): the BMW description of the
   engine, its cooling system and, probably, its fuel-consumption map (rows 3
   and 10, section 2). Library access.
4. **Toyota USA 2023 GR Supra** pressroom specification page and MY23 brochure:
   the one document that would print "2023" and the compression ratio together.
   Both refuse automated readers; open them in a browser.
5. **Heywood printed page numbers** for scan leaves 403, 80, 261–262, 688, and
   the values in Fig. 6-22 (rows 2, 3, 5, 6).
6. **Basir, Alaviyoun & Rosen 2022**, "Thermal Investigation of a Turbocharger
   Using IR Thermography", *Clean Technologies* 4(2) 19 (open access): measured
   casing warm-up and cool-down curves, which would give a directly measured
   settling time for row 7. The site refuses automated readers.
7. **Chen & Flynn 650733**: the page that carries the FMEP correlation, or a
   secondary source that quotes it (section 1).
8. **The Bosch handbook page** for the relative-air-charge definition; the
   Springer/Reif edition of *Gasoline Engine Management* shows a search hit near
   page 12 but no text (section 1).

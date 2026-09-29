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
| **1. We measured it** | It came out of 321.7 minutes of OBD-II logs from our own car, or is computed from them by `derive_params.py` | Yes — re-run the script |
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
| **Compression ratio** — how much the piston squeezes the air before ignition | 10.2:1 | **The engine code B58B30O1 goes with 10.2:1 in four manufacturer documents:** BMW Canada Z4 2020MY Product Guide p. 2 ("Engine type B58B30O1 … Compression rate, :1 10.2 … 285 kW / 382 bHP at 5800–6500 rpm"); Toyota Australia GTP-009045 p. 1 ("Engine model code B58B30O1 … Compression ratio 10.2:1 … 285 kW @ 5800–6500"); BMW, *M340i xDrive Specifications*, 10/2019, p. 1 ("2998 … 94.6/82.0 … Compression ratio :1 10.2 … 275/374 kW/hp"); Toyota Canada press release, Toronto, 14 Feb 2020, *Toyota GR Supra Races Into 2021 with More Power…*: "A new piston design reduces the engine's compression ratio from 11:1 to 10.2:1" as output rose from 335 hp to 382 hp. Toyota Canada, 28 Apr 2022, *…Enhanced Drive Dynamics for 2023*: the 2023 GR Supra 3.0 is the 382 hp car. **But the ratio follows the engine version, not the model year:** the 340 PS / 250 kW GR Supra 3.0 sold in the UK and Europe is printed at **11.0:1** on Toyota UK's own specification sheets of Feb 2021, June 2022 and Feb 2024 (p. 1: "Compression ratio 10.2:1 11.0:1", the first figure being the 2.0-litre), and every 2015–2021 BMW sheet for the original B58 (code B58B30M0 on the 2018 US 5 Series sheet) prints 11.0:1 | **CONFIRMED, and SETTLED for our car.** B58B30O1 = 10.2:1 in four manufacturer documents, and the team confirmed on 19 September 2026 that our car is the 285 kW / 382 hp version (CLAUDE.md); section 2c's Toyota Saudi Arabia page confirms the GCC car is the 382 hp engine. *(This cell said "OPEN: which version our car is" until 28 September -- a week after it was settled.)* |
| **Thermostat opening temperature** — the valve that lets coolant reach the radiator | 88 °C | **The B58 has no thermostat.** BMW Group University Technical Training, *Technical training. Product information. B58 Engine*, course ST1505, information status April 2015, section 4.2 p. 38: *"The conventional thermostat in the B58 engine is replaced by a so-called heat management module."* Section 4.2 p. 39: *"In contrast to a map controlled thermostat with expansion element, there is no direct, physical connection to the coolant temperature"* — the module is a motor-driven rotary valve positioned by the engine computer from the coolant temperature and a cylinder-head metal temperature. No opening temperature is printed anywhere in its cooling chapter. (Unofficial copy on archive.org; page numbers taken from the OCR text and to be checked against the PDF) | **MODELLING EQUIVALENT.** Our 88 °C is the point at which `thermal.py`'s stand-in thermostat cracks, identified from the car's own coolant channel. It must not be cited to BMW |
| **Coolant operating band** | 88–108 °C | BMW publishes no setpoint. ST1505 section 4.2.2 pp. 43–45 lists five control phases (cold start, warm-up, operating temperature, transfer, maximum cooling) with no temperature for any of them. Our logs sit at 88–97 °C throughout | **MEASURED (ours)** for the lower part; the 108 °C upper edge is engineering judgement and is not observed in any log |
| **Oil operating band, sustained load** | 115–140 °C | Searched SAE, MTZ, patents and handbooks; nothing admissible states a sustained-load oil band for this or any modern engine. ST1505 section 4.1 p. 37 confirms only the structure: *"the engine oil as well as the transmission fluid are cooled using coolant"* through an oil/coolant heat exchanger in the filter module, which is what our `ua_block_oil` term models. **Since 28 September `validate.py` no longer scores against this band**: row 8 uses the car's own oil over drive10's hottest ten minutes, 103–111 °C (section 3). drive10's oil reached 117 °C, inside this band's low end; the model's synthetic climb settles at 110.2 °C | **UNVERIFIED** as a published band, and no longer needed. The only numbers found were on owner forums, which cannot be cited |

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

## 2b. The gearbox — ZF 8HP51 (added 19 September 2026)

The vehicle model ran a **generic six-speed with invented ratios** until today
(3.6 / 2.1 / 1.4 / 1.0 / 0.82 / 0.68 on a 3.4 final drive). No source, and not
the transmission in the car. It is now the real one.

### CONFIRMED — Toyota publishes the whole ratio set

| gear | ratio | | gear | ratio |
|---|---|---|---|---|
| 1st | 5.250 | | 5th | 1.316 |
| 2nd | 3.360 | | 6th | 1.000 |
| 3rd | 2.172 | | 7th | 0.822 |
| 4th | 1.720 | | 8th | 0.640 |
| reverse | 3.712 | | **final drive** | **3.150** |

Toyota's own technical specification sheet names the unit **"8-speed Sports
Automatic 8HP 51"** and prints all of the above:
[media.toyota.co.uk](https://media.toyota.co.uk/wp-content/uploads/sites/5/pdf/220605M-GR-Supra-Tech-Spec.pdf)
— **CONFIRMED**, opened 19 September 2026.

**The final drive is confirmed twice, on two different power outputs.** That
sheet is the 250 kW / 11.0:1 European car; Toyota USA's pressroom gives 3.15 for
the automatic on the **382 hp** car, which is this one:
[pressroom.toyota.com](https://pressroom.toyota.com/vehicle/2025-toyota-gr-supra/)
— **CONFIRMED**. So the final drive is not variant-sensitive and the open
question in section 2 about which car this is does not reach the driveline.

### CONFIRMED BY OUR OWN CAR — and this is the stronger evidence

The ratios are not merely cited, they are **measured**. Engine speed and road
speed give the overall ratio the car is actually running, sample by sample:

> **86.7 % of 79 105 moving samples land within 4 % of one of the eight
> published ratios**, and the inferred gears cluster at every one of them
> (8th: 32 376 samples, 7th: 7 309, 6th: 8 189, 5th: 9 182, 4th: 7 551,
> 3rd: 3 598).

A spec sheet says what the car should have. This says what it has.

**It also excludes the alternative.** Toyota offered the 3.0 with a six-speed
manual, whose top gear is 0.846 x 3.46 = **2.927** overall. The car's measured
top-gear ratio is **1.998**, which matches the 8HP51's 8th (2.016) to 0.9 % and
matches nothing on the manual. The car is the automatic.

### UNVERIFIED — two figures in circulation that ZF does not publish

| figure | status |
|---|---|
| torque capacity **~560 Nm** | **UNVERIFIED.** ZF's product page gives the 8HP FAMILY a range of 220–1000 Nm and no per-variant figure. 560 is widely repeated with no primary source found. |
| weight **~77 kg** | **UNVERIFIED.** ZF publishes **87 kg**, and for the **8HP70**, not the 8HP51. |
| ratio spread **7.0** | **DO NOT CITE FOR THIS SET.** ZF publishes 7.0 for the family; 5.250 / 0.640 = **8.20**. The spread quoted by ZF is not the spread of the ratios Toyota prints. |

The 560 Nm figure is worth chasing because it is interesting if true: the engine
makes 500 Nm, so a stock car sits at ~89 % of the gearbox's rated limit and any
tune passes it. **That is a good sentence for the thesis and a bad one to write
without a source.** ZF product literature for the 8HP51 specifically, or a BMW
or Toyota service document, would settle it.
[zf.com](https://www.zf.com/products/en/cars/products_64238.html)

### ASSUMED — the shift schedule, and only the schedule

Neither Toyota nor ZF publishes when the box changes gear. Two parameters carry
that, both declared in `engine_env.Vehicle`:

- **`UPSHIFT_MIN_RPM` = 2000** — calibrated against the car's own inferred gear,
  not guessed. A speed-only schedule tops out at **~47 % exact-gear agreement**
  for any threshold, because a real automatic shifts on throttle and load too;
  2000 rpm is where the model stops sitting a gear high (bias +0.28, **79.7 %
  within one gear**). Quote "within one gear", and say it is a coarse model of
  the shift logic on a gearbox whose ratios are exact.
- **`SHIFT_LOAD` = 0.75** — a 25 % torque reserve before handing back a gear.
  Ordinary automatic calibration; no source opened for this vehicle's.

### ASSUMED — the torque converter is modelled as LOCKED

It is a torque-**converter** automatic, so below lock-up it multiplies torque and
slips. ZF and Toyota publish no stall ratio, no K-factor and no lock-up
schedule, so any converter curve would be an invented parameter. The scenarios
this environment runs are steady high-speed climbs where a real 8HP is locked,
so a 1:1 locked converter is both the right approximation and the honest one.
**Say "converter assumed locked" wherever the gearbox is described.**

---

## 2c. The GCC market specification, and the fuel (added 28 September 2026)

**Our car is a GCC-specification GR Supra.** GCC cars are often said to carry
hotter-climate cooling, so the question was whether the cooling, the oil
parameters or the exhaust temperatures should differ from the model's.

### CONFIRMED — the GCC car is the 382 hp engine

Toyota Saudi Arabia (Abdul Latif Jameel), *Toyota Supra 2026 — full specs*,
`toyota.com.sa/en/vehicles/passenger/supra/full-specs`, opened 28 Sep 2026:
"Engine: 3.0L, In-line 6-Cylinders Turbo (Twin Scroll), 382 HP", Track Edition
MT and AT. That is the 285 kW B58B30O1 whose compression ratio section 2 settles
at 10.2:1 — the pairing `plant.py` runs. **Caveat:** the page is the 2026 model
year; our car is a 2023. It supports the pairing; it does not document our car.

### NOT FOUND — any market-specific cooling hardware

**Searched 28 September and found nothing admissible.** The Toyota Saudi page
lists no cooling, oil-cooler, radiator, fan or oil-capacity row at all. US
dealer catalogues list the Supra radiator as 16400-WAA01 with other WAA
variants in circulation, but every catalogue page refused an automated reader,
so which market each variant belongs to was not established. BMW's "hot climate
version" option (S823A: a larger radiator and a stronger fan) appears only on
owner forums, which are not sources, and nothing ties it to a GCC Supra.
**Do not write that the GCC car has uprated cooling.** If someone can open a
Toyota parts catalogue by region (EPC: Europe / General / Middle East), compare
the radiator, fan and oil-cooler part numbers — that would settle it.

### Why it matters less than it sounds — MEASURED on the model

- **The parameters that were fitted to the car already describe THIS car.**
  `ua_block_oil` (the oil cooler), the 88 °C regulation point, the spark map and
  the enrichment schedule all came from our own GCC car's logs. Whatever
  cooling it has is in them.
- **Stronger cooling barely moves the protected component.** Running the
  locked climb with the radiator and fan 50 % stronger (the unidentifiable
  `ua_rad_*` terms): turbine peak 884.0 → 883.5 °C, oil 109.9 → 108.3 °C,
  coolant 93.4 → 91.8 °C, baseline damage −1.4 %. Doubling `c_oil` changes
  nothing on a steady climb. The turbine housing trades heat with the exhaust
  gas and the air, not the cooling system.
- **EGT is not a cooling output.** It comes from combustion — spark, lambda,
  load — and the spark and lambda calibrations are fitted to this car. No
  channel on the car measures EGT before the catalyst.

### The fuel — 95 RON, CONFIRMED by the team (29 September 2026)

**Settled 29 September 2026: the team confirms the car was logged on 95 RON** —
the fuel `plant.Operating.octane` already assumes, so nothing is refitted and the
knock-limited spark, `validate.py` and `check_map.py` stand as they are. What
follows is kept because it says what a fuel change WOULD cost.

`plant.Operating.octane` is **95 RON**. The team reports (28 Sep) that the
owner's manual gives **95 RON as the minimum and 98 RON as recommended for
optimal performance**. *(Record the manual's page here when it is next to hand;
until then this is the team's report of it, not an opened citation.)*

Measured on the locked climb, hand-written policies, only the octane changed:

<!-- RETIRED-OK: the table below was measured on the plant before its constants were derived -->
| fuel | baseline damage | knock term | turbine peak | preview over current-grade: total | thermal-only |
|---|---|---|---|---|---|
| 95 RON | 951.9 | 61.3 | 884 °C | −0.41 pts | +0.00 pts |
| 98 RON | 931.5 | 41.2 | 884 °C | −0.31 pts | +0.00 pts |

<!-- RETIRED-OK -->
*Measured on 28 September on the plant as it stood BEFORE its thermal, boost,
exhaust-flow and air-density constants were derived from the logs (section 4;
the premise now reads differently -- `results/premise.json`). The conclusion
does not depend on those constants -- at the climb the knock integral stays
below the ECU's knock flag at 91, 95 and 98 RON, so only the knock damage term
moves -- but re-run it before quoting the numbers in the table.*

**The thermal result is fuel-independent.** At the climb the baseline is
already knock-limited at 0.7° BTDC and its knock integral stays below the ECU's
knock flag at 91, 95 and 98 RON alike, so EGT does not move (1027 °C). The knock
damage term is what changes — and that term rests on the knock model this
project has not yet been able to test (CLAUDE.md, 28 September).

**Before changing the default:** the octane should be the fuel the car was
actually filled with while it was logged, because the logged spark map already
reflects it. Changing it also means refitting `BaselineECU.knock_limited_spark`
(fitted at 95), re-running `validate.py` (the knock-limited-spark row) and
`check_map.py`, and it is a plant change — so it goes in before the Phase D
retrain, not after.

---

## 3. The eleven validation bands — status after the 28 September pass

Every band `validate.py` scores against. Before 14 September none had been
checked against a source. **On 28 September rows 8–11 — oil and coolant — stopped
being literature bands at all.** The car logs both, so their bands are now
computed from our own drives (`validate.check_against_car`, replays in
`car_thermal.py`; how each band is built is in `validation_table.md` section A).
That leaves the literature half as: rows 1 and 2 CONFIRMED, row 7 PARTIAL, and
**four rows (3, 4, 5, 6) UNVERIFIED**, to be called engineering-judgement bands
in Chapter 3. Two of those (rows 3 and 5–6) were searched hard and the opened
sources point *away* from the band as written; that is recorded below rather
than hidden.

`validate.py` now prints **8 of 11**: 6 of 7 against literature, 2 of 4 against
our own car. It read seven of the eleven from the morning of 28 September until that
evening, when thermal.py's block and oil nodes were derived from the logs
(section 4): rows 10 and 11 are inside, rows 8 and 9 still outside.

The "kind" column says whether a general textbook will do, or whether this
needs BMW-specific data.

| # | quantity | plain English | band | kind | status | what was found (14 Sep) |
|---|---|---|---|---|---|---|
| 1 | Displacement | engine size | 2990–3000 cc | **B58** | **CONFIRMED** | section 2 |
| 2 | MFB50 at MBT | The crank angle by which half the fuel has burned, at the spark timing that makes the most torque. If burning finishes too early or too late you lose power | 8–10° after top-dead-centre | general | **CONFIRMED** (as the common rule; it is engine-dependent) | Zhu, Haskara & Winkelman 2007, p. 417: "between 8 and 10 [°] after TDC when MBT timing is achieved"; Heywood scan: "half the charge is burned at about 10° after TC" (a single value, not a band); Machado et al. 2015, abstract as rendered: the industry adopts 8°–10° for CA50. Caveat: Klimstra 1985 (abstract) puts the optimum at 7–8°, so the thesis should say "commonly 8–10°, engine-dependent" |
| 3 | Best BSFC | Fuel used per unit of work done — the engine's best-case efficiency | 235–260 g/kWh | general | **UNVERIFIED** — opened sources bracket the band but none states it | Heywood scan, eq. 2.22 context: "For SI engines typical best values of brake specific fuel consumption are about 75 μg/J = 270 g/kW·h" — *above* the band. Conway et al. 2018, p. 5: "The best BSFC of 233 g/kWh (35.8% brake thermal efficiency or BTE) was achieved at 2500 rpm 12 bar BMEP" on a production-like 1.6 L turbo GDI calibration — *below* the band. Our 239.9 g/kWh sits between them. Do not change the band; state it as judgement bracketed by 233 and 270, or cite both. The B58's own fuel-consumption map is in the MTZ article of section 7, unopened |
| 4 | Knock-limited spark | How far the spark can be advanced at high load before detonation starts | 8–14° | **B58-ish** | **UNVERIFIED — expected, and confirmed by searching** | SAE knock-limit papers, MIT and MTU theses and knock-model papers were searched; not one admissible page states a knock-limited spark value near 3000 rpm and 200 kPa. Douaud & Eyzat gives the knock *model*, not this band. **Weakest of the eleven.** Drop the row from the thesis, or keep it labelled as an internal consistency check |
| 5 | EGT cruise, min | Exhaust gas temperature at steady cruise | 600–750 °C | general | **UNVERIFIED** | No opened source states a part-load cruise range. Heywood presents port-exit temperature against load and speed in Fig. 6-22 (Sec. 6.5), but the numbers are in the figure, which nobody has opened; his chapter 11 remarks that a conventional engine's manifold temperature "is not sufficient" for thermal-reactor oxidation at about 600–700 °C, which leans against the band. The only measured figures found are full-load protection limits on a modern turbo GDI: 900 °C at the exhaust port, 930 °C pre-turbine (Conway et al. 2018, p. 10). State which temperature the band means: thermocouple readings sit roughly 100 K below mass-averaged port temperature (Heywood, Sec. 6.5) or about 20 K below the time-averaged value (Caton 1982, abstract) |
| 6 | EGT cruise, max | as above | 600–750 °C | general | **UNVERIFIED** | as above |
| 7 | **Turbine housing time constant** | How long the turbocharger takes to heat up — technically, to reach 63 % of the way to its final temperature after a step change in load | 40–120 s | **B58** | **PARTIAL** | Burke, Vagg, Chalet & Chesse 2015, section 5.3: after a load step on a 2.2-litre diesel with a variable-geometry turbocharger, the gas-to-housing heat flow "peaks at the beginning of the transient (in this case at around 7kW) before slowly falling to a value of around 3.6kW three minutes later. This spike in heat flow is accounted for by the accumulation of heat in the turbine housing as it warms up"; their protocol holds each step three minutes because "this allows for the system to stabilise". Settling within about three minutes bounds the housing time constant from above at roughly 45–60 s, consistent with our 48.0 s and inside the band. **What it does not do:** it reports no time constant, supports neither the 40 s floor nor the 120 s ceiling, and is a diesel turbocharger, not a B58. **No opened source publishes a turbine-housing heat capacity in J/K**, so `c_turb` cannot be cross-checked; see section 4 |
| 8 | Oil, sustained load (drive10, hottest 10 min) | how hot the oil runs when the car is worked hard for ten minutes | 103–111 °C | **our car** | **MEASURED (ours)** | The car's interquartile range over the 10 minutes of drive10 where its rolling-median oil is highest. The model, with the derived oil node, sits at 97.0 °C (it was 96.4 before): **still outside**, and now IN-SAMPLE, because drive10 is in the fit. Of the 12.0 K miss, 4.6 K is the coolant (over that stretch the car's heat-management valve let it rise to 97–99 °C where the model regulates near 93; pinning the block to the measured coolant recovers 4.6 K) and 7.3 K is the oil node itself, which runs 4.4 K over its coolant where the car's oil runs 11.7 K (`model_vs_data.row8_split`; corrected 29 September from an unmeasured "about 6 K"). Replaces the 115–140 °C band, which no source supported (section 2, oil row) |
| 9 | Oil apparent time constant (identified) | how long the oil takes to follow a change in load | 70–100 s | **our car** | **MEASURED (ours)** | One first-order fit (`car_thermal.identify_tau`) applied to the car's oil and to the model's; the car's range over the four drives that excite the oil enough to say. The model's was 14.0 s; with the derived oil node it is 60.0 s: **closer, still outside**. The old 20–400 s band contained the car's value — the band was right, and the model was not. Jarrier et al. 2000 (abstract) still supports the ordering, oil lagging coolant |
| 10 | Coolant, regulated (synthetic climb) | steady coolant temperature once warm, under load | 83.6–95.5 °C | **our car** | **MEASURED (ours)** | Warm coolant on every drive, 5th–95th percentile (83.5–95.6 until drive B's coolant joined the pool, by the same rule). The model's settled 93.0 °C on the synthetic climb is inside (was 94.5). Was 88–108 °C, whose upper half was judgement |
| 11 | Coolant, whole drive (drive10, free-running) | coolant temperature over two hours of real driving | 91.8–94 °C | **our car** | **MEASURED (ours)** | The car's interquartile range over drive10; the model, replayed free-running on the car's measured fuel, had a median of 88.4 °C (**outside**); with the derived block node it is 92.2 °C: **inside** -- and 92.0 °C with drive10 held out of the fit, so the pass is a prediction, not a fit to its own band. Replaces a "regulation response" row with a 1–600 s band that almost nothing could fail (AUDIT.md L10) |

<!-- RETIRED-OK: the literature bands rows 8-11 used until 28 September -->
*Until 28 September rows 8–11 were: oil on a sustained climb 115–140 °C
(UNVERIFIED), oil time constant 20–400 s (UNVERIFIED), coolant
thermostat-regulated 88–108 °C (our logs, loosely), and coolant apparent time
constant 1–600 s (UNVERIFIED). Scored that way `validate.py` read eight of
eleven. The count went down because the new bands are narrower and they are
the car's; that is the direction a stricter test should move it.*

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

| parameter | value (28 Sep derivation) | what it is | status |
|---|---|---|---|
| `c_block` | 36 350 J/K | heat capacity the regulated coolant sees | **DERIVED from our logs** (`derive_params.py`), as a RATIO with `frac_fuel_to_coolant`: identified by the one warm-up in the logs (683640a0, radiator shut). Left out of the fit, that drive is predicted ~14 K wrong, so do not quote the capacity alone. Was an ASSUMED 105 000 |
| `frac_fuel_to_coolant` | 0.178 | share of fuel energy that reaches the coolant | **DERIVED**, as a ratio with `c_block` (above). Was an ASSUMED 0.26 |
| `ua_block_amb` | 2.4 W/K | block to ambient, radiator shut | **DERIVED.** At a four-minute idle on drive10 the car held 93.5 °C on ~1.7 kW of fuel heat, so standing losses are near zero. Was an ASSUMED 45, which cooled the model 13 K there |
| `t_stat_open` / `t_stat_span` | 92.1 °C / 2.8 K | where the stand-in thermostat opens, and how fast | **DERIVED; MODELLING EQUIVALENT.** The real engine has a heat management module, not a thermostat (section 2); never cite these to BMW. Were 88 °C / 9 K, which let the model's coolant drift 4–13 K low at light load and spike on every pull |
| `ua_rad_*` | 427 / 85 / 996 | radiator: fan off, per m/s of road speed, fan on | **SIZE DERIVED, SPLIT UNIDENTIFIABLE.** One scale factor on the reasoned 300 / 60 / 700 split (×1.42) is derived: wherever coolant climbs above its regulated point the radiator is open and its size sets the temperature. The split between the three terms cannot be: every water-pump and fan-actual channel reads zero (`logs/CHANNEL_CENSUS.md`), and the valve angle is not logged |
| `ua_block_oil` | 474 W/K | oil to coolant, through the oil cooler | **DERIVED** jointly with the oil's heat input (stage 1 of `calibrate_thermal.py`, block pinned to measured coolant). Was 800 W/K, measured on 8 September from the p95 oil-minus-coolant gap with the oil's heat share ASSUMED at 5 %; with the heat input estimated too, the coupling comes out looser. BMW's ST1505 confirms the structure, not the number |
| `c_oil` | 27 200 J/K | heat capacity of the oil node | **DERIVED, weakly** -- its time constant is the robust figure: 57 s at rest, 55 s at 130 km/h (was 14 s; the car's apparent 70–100 s, `validate.py` row 9). Was an ASSUMED 12 000 |
| `k_oil_rpm`, `n_oil_rpm` | 610 W at 3000 rpm, exponent 3.86 | the oil's heat input from engine speed (friction, windage, churning) | **DERIVED. NEW STRUCTURE, 28 September.** The car runs its oil 11–15 K above coolant at 3700–4800 rpm and 70–100 km/h, and 2–3 K below it cruising at 2600 rpm and 130–140 km/h: oil heat follows engine speed, not fuel. Four candidate forms were scored on drive10 held out; this one won (`results/figures/fig24`) |
| `frac_fuel_to_oil` | 0.0042 | share of fuel energy reaching the oil | **DERIVED.** Was an ASSUMED 0.050 -- the cause of the model's 140 °C oil spikes on hard pulls |
| `ua_oil_amb`, `ua_oil_ram` | 0.38 W/K + 0.68 W/K per m/s | sump to ambient, at rest and with road speed | **DERIVED. The road-speed term is NEW**: the sump sits in the airstream. Was a constant ASSUMED 60 W/K |
| **`c_turb`** | **6 000 J/K** | **heat capacity of the turbine housing** | **ASSUMED — AND IT IS LOAD-BEARING. See below.** No channel on this car measures the turbine (every pre-catalyst exhaust channel reads zero). No opened source publishes a housing heat capacity. Burke, Olmeda, Arnau & Reyes-Belmonte 2014 (abstract) report that the heat-transfer model's parameters move "housing temperatures by up to 80 °C" and that "errors in the thermal capacitance also lead to errors" in transient simulation — a citable statement that this is the sensitive, uncertain parameter |
| `ua_gas_turb` / `ua_turb_amb` | 0.90 W/K per g/s / 18 W/K | exhaust to turbine; turbine to air | **ASSUMED**, and underivable for the same reason as `c_turb` |

**WHAT THE DERIVED ROWS MEAN.** They are not typed anywhere: `thermal.py` reads
them from `data/derived_params.json`, which `derive_params.py` recomputes from
every drive that logs coolant, oil and ambient whenever the data changes (it
runs at the end of `build_dataset.py`). The values above are the 28 September
derivation, on 7 drives; the file holds the current ones. The fit, its
per-drive and held-out scores, and the structures it rejected are in
`calibrate_thermal.py` and `results/thermal_calibration.json`.

<!-- RETIRED-OK: the section 4 table as it stood before 28 September -->
*Until 28 September this table read: `ua_block_oil` 800 W/K MEASURED; `c_block`
105 000, `c_oil` 12 000, `ua_block_amb` / `ua_oil_amb` 45 / 60, `frac_fuel_to_coolant`
0.26 and `frac_fuel_to_oil` 0.050 all ASSUMED; `ua_rad_*` 300 / 60 / 700
UNIDENTIFIABLE; `t_stat_open` 88 °C identified from the coolant channel.*

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

## 4b. Every other constant: does the data set it, and if not, why not

Reviewed 28 September 2026, constant by constant, because the team asked that
nothing the data can set be left as a typed number. Four outcomes: **DERIVED**
(computed from the data every time it changes -- `derive_params.py`), **DERIVED
ONCE** (from our data, but not re-derived automatically, for the reason given),
**CANNOT** (no channel on this car carries the information), and **DESIGN**
(a choice the experiment makes, not a property of the car to be measured).

| constant | where | outcome | why |
|---|---|---|---|
| boost ceiling | `plant.boost_ceiling_kpa` | **DERIVED** | It IS the measured envelope now: p95 pressure ratio per corrected-flow bin, made monotone, capped at the highest stable ratio in the logs (2.515). The 8 Sep formula (A 14.5023, B 6.4019, cap 2.6 "observed peak plus margin") could not follow the envelope's jump at 0.075–0.105 kg/s and left RMS 0.128 against it; the envelope leaves 0.013. Against the highest boost drive B reached in each 200 rpm band, the ceiling sits −7 to +7 % from 2000 rpm up but 9–20 % LOW at 1600–2000 rpm (`fig22`, the results page); the envelope is built from quasi-steady rows, and roll-ons are transients. Corrected 29 September: this said drive B "now matches" at 1400–2400 rpm |
| `MAP_CEIL_KPA` | `engine_env` | **DERIVED** | the envelope's cap × 99.3 kPa (was a typed 250.0) |
| `SPARK_A` | `BaselineECU` | **DERIVED** | the offset at which commanded part-load spark has zero mean bias against the car; solved, not searched |
| `ENR_DWELL_LO` / `HI` | `BaselineECU` | **DERIVED** | 1.5 / 3.0 s on the timestamp axis (were 2.0 / 9.0 s on the row-count axis AUDIT.md H3 retired); 100 genuine lambda readings, RMSE 0.057 against 0.070 |
| `DELIVERABLE_TORQUE` | `Vehicle` | **DERIVED** | measured through the plant after the above; the gearbox's kickdown table |
| `AMB_FALLBACK_C` | `build_dataset` | **DERIVED ONCE** | 42 °C, the median ambient of the two other early-afternoon drives, for drive B, which logged no ambient. Its effect on the ceiling is recorded at 19 and 45 °C |
| air density | `Vehicle.demand` | **DERIVED** (physics) | ρ = p / (R·T) from the scenario's own ambient: 1.12 kg/m³ at 42 °C. Was a typed 1.2 (air at ~21 °C), drag 7 % too high |
| exhaust mass flow | `engine_env`, `app/estimator.py` | **DERIVED** (physics) | air + fuel from the plant. Was fuel × 15 -- 5 % low at λ 1, 16 % high at λ 0.81 (AUDIT.md M2) |
| load constant k | `compare_log.py` | **DERIVED** (definition) | 269.6 / T_charge at each point, since 10 September |
| `SPARK_B`, `SPARK_C` | `BaselineECU` | **DERIVED ONCE** (7 Sep) | Re-deriving the slopes from the current points gives a load slope that, extended into boost, falls below the knock limit -- a part-load fit setting spark in boost (mistake 6). Every steady point is 30–75 kPa; no road drive can extend that |
| `ENR_RPM_LO` / `HI`, `ENR_DEPTH` | `BaselineECU` | **DERIVED ONCE** (8 Sep) | A free fit of all five enrichment constants on the ~100 genuine readings puts `ENR_RPM_LO` on the edge of its grid and a depth that cannot reach the car's 0.79 floor: not identified. The attempt is kept in `data/derived_params.json` as `free_fit_all_five` |
| `UPSHIFT_MIN_RPM` | `Vehicle` | **DERIVED ONCE** (19 Sep) | Swept against the car's inferred gear. Not re-derived automatically: drive B was driven in manual mode (held gears), and no channel marks manual mode, so an automatic re-derivation would learn the shift schedule from a drive where the driver chose the gears |
| `ENR_LOAD`, charge-temperature gate 200 kPa, MAF ceiling 1019.9 kg/h | several | **definitions / measured limits** | the 200 kPa gate restated on the corrected scale (mistake 13); 15 psi gauge in absolute terms; the sensor's own range limit (mistake 7) |
| vehicle mass, `cd_a`, `crr` | `Vehicle` | **CANNOT (yet)** | Tried on 28 September from 7475b5d7's `Coordinated target torque on the wheel`: drag area 0.66 m² (90 % bootstrap 0.36–1.02) and mass 2 846 kg (2 181–3 432) -- not identified. 537 torque readings in 55 min, paired with speed readings a median 3.4 s away, and a TARGET torque that leads the actual. Needs Toyota's specification sheet for the kerb weight (not opened; do not quote one from memory) or a coast-down drive logging wheel torque with few channels |
| `wheel_r` | `Vehicle` | **CANNOT separately** | The data fixes only the product of the speed channel's scale and the radius: measured overall ratios run 1.2–1.5 % below the published ones (drive B: 8th 1.992 against 2.016), i.e. r = 0.335 m OR a speed channel reading ~1.5 % high. The tyre size has not been opened from a source |
| driveline efficiency 0.92, `SHIFT_LOAD` 0.75 | `Vehicle` | **CANNOT** | no engine- or wheel-torque channel at a usable refresh; the efficiency is inseparable from road load |
| `charge_temperature` (+12 K, 0.06) | `plant` | **CANNOT** | no post-intercooler sensor (`Temperature after the intercooler` reads zero). The boost comparison fixes only the RATIO of charge temperature to volumetric efficiency |
| `volumetric_efficiency`, residual fraction | `plant` | **CANNOT** | the same ratio; and both pressure channels sit before the throttle, so there is no part-load test at all (mistake 12) |
| `UA_PORT`, `CP_EXH`, `EXH_BACKPRESSURE_RATIO` | `plant` | **CANNOT** | no exhaust temperature before the catalyst and no exhaust pressure channel |
| combustion: Wiebe, burn duration, ignition delay, Woschni, Chen-Flynn FMEP, γ(T), combustion efficiency, fuel properties | `plant` | **CANNOT** | need cylinder pressure; the car publishes none. Published correlations, cited in section 1 |
| knock: Douaud-Eyzat constants, octane 95, the knock-limited surface, the ECU's 3° pull / 12° cap / 0.35 °/s restore | `plant`, `BaselineECU` | **CANNOT (yet)** | the only log with both ignition angles reads each every ~8 s -- too slow to see a knock event (drive C would). The fuel is 95 RON, confirmed by the team on 29 September (section 2c) |
| `iat_compensation`, cold-start retard | `BaselineECU` | **CANNOT** | spark against CHARGE temperature, which is modelled, not measured, so the slope is confounded with the model it would test |
| fan schedule (367 / 372 K) | `BaselineECU` | **CANNOT** | every fan-actual and fan-duty channel reads zero |
| `p_baro` 101.3 kPa | scenario | **DESIGN** | altitude is not modelled (CLAUDE.md, limitations) |
| damage model (1123 K knee, 45 K, 0.4, 408 K, 12 K, knock 40, 0.85), reward (`TRACK_*`), action ranges, slew, preview horizons, the locked scenario, the training roads, the load loop's gains | `engine_env` | **DESIGN** | choices that define the experiment, not properties of the car. The 1123 K knee has a published comparison (Conway et al. 2018: 930 °C pre-turbine) but no channel on this car could measure it |
| `DTHETA_DEG` | `plant` | **studied** | numerical step, set by a convergence study (AUDIT.md H1) |

---

## 5. Numbers that need no external source — they are ours (kind 1)

All from 321.7 minutes over eleven drives of our own logs (eight carrying usable
samples), all regenerated by a script anyone can run. **This is the strongest
tier in the project.** `verify_docs.py` opens this file and checks the figures
in this section against the shipped data, so they cannot drift.

- 26 distinct operating points; vehicle validation covers 30–75 kPa manifold
  pressure only
- the spark map: its offset DERIVED for zero mean bias over the 26 points (RMS
  2.5°); its slopes the 7 September fit on 11 points (section 4b)
- enrichment v4 — 1055 samples above 180 kPa, correlations −0.47 / −0.41 / −0.44
- the compressor envelope, which IS the boost ceiling now (section 4b), and the
  1020 kg/h air-flow sensor ceiling, pinned on 568 samples across seven
  separate drives
- knock retard, 99th percentile 9.8°, from 10 896 filtered samples -- **filtered
  with `Actual gear`, which clamps at 6 (CLAUDE.md mistake 18); re-derive from
  the inferred gear before quoting**
- the whole block and oil nodes of the thermal network (section 4)
- charge temperature — within 1.9 % of the car's own boost sensor (762 model
  samples against 1097 logged readings above 200 kPa; the figure read 3.0 % here
  until 28 September, after drive10 had moved it)
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
| **1020.0 kg/h** | the air-mass sensor ceiling the app refuses to trust | 573 pinned samples across 7 of the 10 raw logs; 517 across 5 after the warm filter. Already in section 5 |
| **6.0 s** | the channel refresh interval on a 26-channel log, which sets how long a detection window must span | measured directly on `7475b5d7`: air mass 6.00 s, boost 6.00 s, engine speed 6.00 s, ambient pressure 18.0 s |
| **7.5 s / 1.45 s** | per-channel rate at 26 and 7 channels — the whole justification for keeping the live set to six | `7475b5d7` against `pull01`, CLAUDE.md mistake 13b |
| **13.6 %** | the worst windowed disagreement between inverted and measured pressure on a car with nothing wrong with it — the evidence behind the 25 % fault threshold | 45 gated windows across all ten drives, CLAUDE.md mistake 14 |

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

- **It has never been shown a fault.** Nothing in ten drives is broken, so
  every figure behind the mismatch detector is a FALSE-POSITIVE rate. None of
  them is a detection rate, and the difference is the whole of the claim.
- **It has never run against the car.** Every number above is from replay.
- **Its alert counts are not measurements of the vehicle.** 13 thermal / 0
  mismatch / 19 novel on `7475b5d7` is a property of thresholds we chose. They
  are pinned so a regression is visible, which is a different job.
---

## 6. What to do with this file

1. ~~Settle which engine version the car is~~ -- **settled 19 September 2026**:
   the 285 kW / 382 hp car, so 10.2:1 is right (section 2).
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

1. ~~Which engine version the car is~~ -- **settled 19 September 2026**, the 285 kW
   car (section 2). Listed as open here until 28 September.
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

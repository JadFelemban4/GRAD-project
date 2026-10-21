# `logs/epa/` — EPA's engine benchmarking files for decision 24's three new engines

Decision 24 (`results/VALIDATION_DECISIONS.md`, section F) makes the H/τ test four
engines. The B58 has our own drives in `logs/raw/`. The other three have only what
the US EPA's National Center for Advanced Technology (NCAT) published: test-cell
workbooks of averaged operating points, and an ALPHA engine file built from them.
This folder holds those files, **byte for byte as EPA published them**.

**These files are measurements. Never edit them**, like `logs/raw/` (CLAUDE.md,
conventions). `.gitattributes` here switches off git's line-ending conversion
(this machine's git runs `core.autocrlf=true`), so a checkout keeps EPA's bytes and
every sha256 below holds. The tables the project reads are generated from them:

```bash
python epa_map.py           # logs/epa/ -> data/engines/<engine>/ (never edit those either)
python test_epa_map.py      # hashes, row counts, units, ranges, byte-for-byte rebuild
```

## Where they came from

Downloaded from epa.gov on 20 October 2026 into the team's data folder
(`C:\Users\badcl\Desktop\GRAD-engine-data`, outside the repository: its
`MANIFEST.csv` hashes every download and every file extracted from a zip, and its
`CATALOGUE.md` says what each holds). `python epa_map.py --stage <data folder>`
copied the files below out of it, refusing any whose sha256 differed from that
manifest, and wrote `MANIFEST.csv` here:

| column | meaning |
|---|---|
| `url` | the EPA package zip the file is a member of |
| `zip_member` | the member's name inside that zip (EPA's own file name, kept) |
| `repo_path` | where it sits in this repository |
| `bytes`, `sha256` | equal to the data folder's `MANIFEST.csv` row for the same file (`test_epa_map.py` checks it) |
| `data_folder_path` | the file's path inside the data folder |

`python fetch_engine_data.py --verify-only` re-checks the chain end to end: the
data folder's zips hash as listed, and each file here equals the member of the zip
it came from. `D3_AND_EPA_SOURCES.csv` is what `fetch_engine_data.py` downloads
into a data folder (never into the repository): every EPA package, the Test Car
Lists and Argonne's D3 data for the CX-9 and the Accord, each with its sha256.

## The files

Tier 2 fuel (EPA's certification gasoline) only. Per engine: the test-data
workbook, the test report that says how the points were taken, the fuel analysis
that says what the engine burned, and the ALPHA engine file with the document of
how EPA built it. 18 files, 15,541,486 bytes.

| engine | file | from the package | what it is |
|---|---|---|---|
| `mazda_25t` | `4- … Test Data.xlsx` | 2016 Mazda 2.5L Turbo Skyactiv-G, Tier 2 test data | Steady State, Steady State with Transmission, High Load Initial and Final; Test Parameter List |
| | `3a- … Test Report.docx` | same | method, instruments, Test Cell 9, the test article (a 2016 CX-9, VIN JM3TCABYXG0104977) |
| | `6- NVFEL Fuel Analysis Report 26864.pdf` | same | the fuel |
| | `7- engine_2016_Mazda_Skyactiv_Turbo_2L5_Tier2.m` | Tier 2 ALPHA map | displacement, cylinders, compression ratio, full-throttle and closed-throttle curves, fuel map |
| | `3- … ALPHA Generation Process.html` | same | how EPA built the `.m`, and which of its points are not measured |
| `honda_l15b7` | `4- … Test Data.xlsx` | 2016 Honda 1.5L L15B7, Tier 2 test data | the same four sheets |
| | `3a- … Test Report.docx` | same | Test Cell 7; the test article (a 2016 Civic 4D Touring, VIN 19XFC1F9XGE000831) |
| | `6- NVFEL Fuel Analysis Report 25842.pdf` | same | the fuel |
| | `7- engine_2016_Honda_L15B7_1L5_Tier2.m` | Tier 2 ALPHA map | as above |
| | `3- … ALPHA Generation Process.html` | same | as above |
| `ford_27tt` | `4- … Cell 9 - Test Data.xlsx` | 2015 Ford 2.7L EcoBoost V6, Tier 2, Cell 9 | Steady State to 4,500 rpm |
| | `3- … Cell 9 - Test Report.docx` | same | Test Cell 9 |
| | `6- NVFEL Fuel Analysis Report 25278.pdf` | same | the Cell 9 fuel |
| | `4- … HD1 - Test Data.xlsx` | 2015 Ford 2.7L EcoBoost V6, Tier 2, HD1 | Steady State to 5,481 rpm, High Load Initial and Final |
| | `3- … HD1 - Test Report.docx` | same | Test Cell Heavy Duty 1; the test article (a 2015 F150 2WD, VIN 1FTEX1CP5FFA23506) |
| | `6- NVFEL Fuel Analysis Report 26864.pdf` | same | the HD1 fuel |
| | `7- engine_2015_Ford_EcoBoost_2L7_Tier2.m` | Tier 2 ALPHA map | as above |
| | `3- … ALPHA Generation Process.html` | same | as above |

Left in the data folder, because nothing here reads them: the Tier 3 and LEV III
packages, the contour plots, the SAE papers, the package-content and related-package
notes, the test cells' start-up procedures, the ALPHA map's BSFC and efficiency
plots and its fuel-map workbook (the `.m` carries the same map). The sheet
`Steady State with Transmission` is in the workbooks but not tabulated: those
points were taken through a transmission and torque converter (the Mazda's through
a GM 6L80, the Honda's through its CVT), so the torque is not the engine's alone.

## Citations — EPA's own, verbatim

- 2016 Mazda 2.5L Turbo Skyactiv-G Engine Tier 2 Fuel - Test Data Package. Version 2019-02. Ann Arbor, MI: US EPA, National Vehicle and Fuel Emissions Laboratory, National Center for Advanced Technology, 2019.
- 2016 Mazda 2.5L Turbo Skyactiv-G Engine Tier 2 Fuel - ALPHA Map Package. Version 2019-02. Ann Arbor MI: US EPA National Vehicle and Fuel Emissions Laboratory, National Center for Advanced Technology, 2019.
- 2016 Honda 1.5L L15B7 Engine Tier 2 Fuel - Test Data Package. Version 2018-05. Ann Arbor, MI: US EPA, National Vehicle and Fuel Emissions Laboratory, National Center for Advanced Technology, 2018.
- 2016 Honda 1.5L L15B7 Engine Tier 2 Fuel - ALPHA Map Package. Version 2018-05. Ann Arbor MI: US EPA National Vehicle and Fuel Emissions Laboratory, National Center for Advanced Technology, 2018.
- 2015 Ford 2.7L EcoBoost V6 Engine Tier 2 Fuel Cell 9 - Test Data Package. Version 2019-11. Ann Arbor, MI: US EPA, National Vehicle and Fuel Emissions Laboratory, National Center for Advanced Technology, 2019.
- 2015 Ford 2.7L EcoBoost V6 Engine Tier 2 Fuel HD1 - Test Data Package. Version 2019-11. Ann Arbor, MI: US EPA, National Vehicle and Fuel Emissions Laboratory, National Center for Advanced Technology, 2019.
- 2015 Ford 2.7L EcoBoost V6 Engine Tier 2 Fuel - ALPHA Map Package. Version 2019-11. Ann Arbor MI: US EPA National Vehicle and Fuel Emissions Laboratory, National Center for Advanced Technology, 2019.

`epa_map.py` copies each table's citation into `data/engines/<engine>/epa_engine.json`
from the workbook itself. Argonne's D3 data, which `D3_AND_EPA_SOURCES.csv` lists
but this repository does not hold, may only be used with Argonne's attribution:
*"This data is from the Downloadable Dynamometer Database and was generated at the
Advanced Mobility Technology Laboratory (AMTL) at Argonne National Laboratory under
the funding and guidance of the U.S. Department of Energy (DOE)"*
(https://www.anl.gov/taps/downloadable-dynamometer-database).

## Read these before using the data

Each from the files here; `data/engines/<engine>/epa_channels.csv` carries EPA's
status for every channel, and its minimum and maximum.

1. **Every point is an average.** Steady State points are held, then logged and
   averaged; High Load Initial and Final are two windows of one 30-second hold, the
   Initial the maximum torque within 2 s of reaching the target, the Final once
   torque and fuel are stable. The 100 Hz traces that would show the protection
   transient were never published. Initial row r and Final row r are the same hold.
2. **`Turbine Inlet Temp` is a gas reading** ("Sensor Verified to a Standard",
   measured at the turbocharger turbine inlet), not the housing metal the plant
   protects (mistake 23). On the Ford's twin-turbo V6 there is one such channel, and
   which bank it reads is not stated: Figure 2 of each Ford report draws pressure,
   temperature and oxygen points after each bank's turbocharger and no turbine-inlet
   point. UNVERIFIED.
3. **Spark, lambda and fuel-rail pressure are "Reference Only"**: uncalibrated sensors
   or readings of the engine's own signals. Kept and flagged, not dropped
   (`reference_only` in `epa_channels.csv`). The Mazda's spark reads −120 on its
   fuel-cut points, a sentinel, not an angle.
4. **High Load Initial has no fuel-meter value**, only EPA's injector estimate; High
   Load Final lacks the meter on 5 of the Mazda's 61 rows, 2 of the Honda's 65 and 2
   of the Ford's 19. BSFC near zero torque is a division by almost nothing (the
   Ford's HD1 steady state reaches 149 503 g/kWh): filter it where it is used.
5. **The two Ford cells are two experiments.** Cell 9 ran fuel 25278, HD1 fuel 26864;
   HD1's own report says its steady state "was included as comparison" with Cell 9's
   and its job was high speed and high load. EPA's ALPHA map combines Cell 9's steady
   state with HD1's High Load Initial. The tables keep them apart (`_cell9`, `_hd1`).
6. **The edges of the ALPHA curves are not measurements** (mistake 6).
   `epa_engine.json` marks every node: `node_is_measured` is true where the node is a
   point of the sheets EPA built the curve from (the `readtable2` calls of its
   generation script), false where EPA added it. Full throttle: the Mazda's nodes are
   measured from 1501 to 2252 rpm only; those at 981, 1250 and 4000–5500 rpm come
   from a 2016 Mazda symposium paper (Okita), and at 4000 rpm that paper's 391 Nm
   stands where EPA measured 388 Nm. The Honda's are measured to 5001 rpm; its
   6000–6600 rpm nodes are EPA's estimate from the rated 130 kW. The Ford's are
   measured to 1751 rpm only; the rest is built from Ford's specification sheet
   (375 lb-ft, 508 Nm, at 3000 rpm, where EPA measured 496 Nm at 3016 rpm).
7. **Bore and stroke.** Only the Ford's `.m` states both (83 × 83 mm). The Honda's
   stroke (89.4 mm) is in its `.m`; its bore (73 mm) and the Mazda's (89 mm) are in
   EPA's generation scripts under a misspelt variable (`enigne.bore_mm`), which is why
   the `.m` files lack them. The Mazda's stroke is stated nowhere: its script's only
   stroke line, `% engine.stroke_mm = 100;`, is commented out. `epa_engine.json`
   gives null for it, with the reason. A handbook value is not typed in.
8. **The Honda engine is not the Accord's.** EPA's L15B7 came from a 2016 Civic
   (130 kW, 220 Nm, compression 10.6); the 2018 Accord whose D3 data exist is rated
   143 kW and 260 Nm at 10.3 (`engine_specs/cars/accord_2018_15t.toml`).
9. **EPA's BMEP column** is 4π × torque over a displacement, and not always the
   `.m`'s: it implies 2.488 L for the Mazda (the `.m`'s), 1.495 L for the Honda
   (the `.m` says 1.496) and 2.700 L for the Ford (the `.m` says 2.694, 0.22 % less)
   on every sheet (`test_epa_map.py`, Ranges). BMEP is EPA's calculation; torque is
   the measurement.

Added 20 October 2026, build step 1 of decision 24 (the data, before any calibration).

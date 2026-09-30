# Session report — 28 September 2026, evening: drive B, and the constants the data sets

**Audience:** the team. It assumes you know the project and have read the
earlier 28 September report. In the order it happened.

**Branch:** `JMF-2340550`. **Nothing here is committed yet** — the working tree
holds every change, ready to review. `JMF-2340550-sep17` is still not merged,
and the merge is **not** documents-only (section 8).

**What was asked, in order:** (1) add the drive the team logged; (2) the
model's oil and coolant spike and drop far faster than the car's — match them to
the data; (3) `validate.py` rows 8, 9 and 11 sit outside the car's bands — fix
them; (4) review every variable, and calculate from the data any that lack a
source; and along the way, fix and document whatever is found, graph every
comparison, and **stay away from fitted numbers for constants — compute them
from the data as it arrives, the way k is derived.**

---

## Headline

| | |
|---|---|
| **Drive B is in.** | 26.7 min of full-throttle roll-ons in a held 6th/7th/8th from 1440–2000 rpm, 7 channels, each read every 1.05 s. Dataset 295.0 → **321.7 min, eleven drives**. It logged **no ambient temperature and no oil**, so it informs boost and coolant, not oil. |
| **The data now sets the constants, not the code.** | `derive_params.py` recomputes every constant the logs can set and writes `data/derived_params.json`; `thermal.py`, `plant.py` and `engine_env.py` read it (`derived.py`). `build_dataset.py` runs it at the end, so a new drive re-derives the plant. No fitted number is typed into a module where the data can set it. |
| **The oil node had the wrong structure.** | The car's oil heats with ENGINE SPEED and is cooled by ROAD SPEED; the model heated it with 5 % of fuel and cooled it through a constant. Re-structured and fitted: oil time constant **14 s → 57 s**; drive10 oil RMSE **7.55 → 3.57 K** (3.90 K held out). |
| **validate.py: 7 of 11 → 8 of 11.** | Row 11 (drive10 coolant) and row 10 now inside. **Rows 8 and 9 (oil) still outside** — 97.0 °C against 103–111, and 60 s against 70–100 — and the reason is stated, not tuned away (section 3). |
| **The boost ceiling IS the measured envelope now.** | No formula, no fitted constants: the binned p95, made monotone. ~~It follows drive B's low-rpm full-throttle boost at 1400–2400 rpm.~~ **Corrected 29 Sep:** against the highest boost drive B reached per 200 rpm it is −7 to +7 % from 2000 rpm up, but 9–20 % LOW at 1600–2000 rpm (section 5). |
| **Four defects fixed on the way**, each measured. | Exhaust flow was fuel × 15 (now air + fuel); the ceiling was evaluated at the charge temperature (now ambient); air density was a typed 1.2 (now 1.12 at 42 °C); the H/τ axis fix of AUDIT.md M12 had never worked. |
| **Preview did not move.** | Against current-grade, hand-written: −0.4 → **−0.3 points** through every step. The premise now reads baseline **920.1** at **883 °C**. |
| **The H/τ sweep shows no preview value against the honest comparator.** | 0.0 points over current-grade at every τ and cost curvature; the reported edges were all against a reactive policy (section 7b). No sweep can be cited for the criterion yet. |

---

## 1 · Drive B — what it is and what it bought

`logs/raw/driveB_rollons-20260928_140513.csv` (uploaded as
`6e7b70a0-2026-09-28_14-05-13.csv`; copied byte-identical). Seven channels:
engine speed, vehicle speed, air mass, boost, ambient pressure, **target**
throttle angle, coolant. 97 % of moving samples sit within 4 % of a published
ZF 8HP51 ratio; 41 full-throttle onsets in held 6th, 7th and 8th.

**Three things were in the way of adding it, all fixed:**
- **The export changed its capitalisation** (`"Engine Speed"`, not
  `Engine speed`). `build_dataset.py` and `new_drive.py` matched names exactly,
  so the drive read as all-NaN. Both now match case-insensitively; rebuilding
  the ten earlier drives with the change is byte-identical.
- **It logged no ambient temperature** (`logs/DRIVE_PLAN.md` left it off drive
  B's list). `build_dataset.py` silently fell back to 25 °C. It now uses
  `AMB_FALLBACK_C` = 42 °C, the median ambient of the two other early-afternoon
  drives, flags every such row `t_amb_assumed = 1`, and keeps `t_amb` NaN. The
  **charge-temperature check excludes those rows** — admitted, they doubled the
  population and moved the headline gap from +1.9 % to +1.0 % on an assumption.
  With them excluded it stays +1.9 % on 762 / 1097. The ceiling's sensitivity to
  the assumption is recorded at 19 °C and 45 °C.
- **Missing channels were reported as fuel cut.** A window with no spark channel
  read NaN and failed "spark > 0". Now counted and reported separately.

Also found in the rebuild: **placeholder zeros** (AUDIT.md M8, fixed in the app
on 16 September) were still reaching `master_samples.csv` — drive10's first two
ambient rows read 0 °C. `build_dataset.py` now masks each channel's leading
run of zeros.

**What it did NOT buy:** operating points (no spark or lambda channel), the oil
node (no oil channel), the knock question (no ignition channels).

## 2 · The thermal network, matched to the car

**What was wrong, measured** (`fig20`, before): on hard pulls the model's oil
spiked to 140 °C where the sump read 107 °C; its coolant spiked 10 K where the
car's barely moved; at a four-minute idle on drive10 the block cooled 13 K while
the car held 93.5 °C (1.7 kW of fuel heat in, ~7 kW assumed out).

**The data rejected the oil node's structure.** drive10, minutes 1–14:
3700–4800 rpm at 70–100 km/h on 3–5 g/s of fuel, oil **11–15 K above** coolant.
3aca2ec1 cruising: 2600 rpm at 127–142 km/h on 2–3 g/s, oil **2–3 K below**
coolant. Oil heat follows engine speed (friction, windage, churning) and the
sump is cooled by road speed. Seven structures were fitted with the block pinned
to measured coolant and scored on drive10 **held out** (`fig24`):

| oil node structure | drive10 oil RMSE, held out |
|---|---|
| as shipped: 5 % of fuel, constant 60 W/K (free-running) | 7.55 K |
| fuel share, road-speed cooling | 3.30 K |
| **engine-speed heating, road-speed cooling (chosen)** | **2.78 K** |
| engine speed + fuel, road-speed cooling | 2.68 K (one more parameter; not kept) |
| + a separate oil-sensor lag | 2.79 K (the data picked a 6 s lag; not supported) |

**The fit** (`calibrate_thermal.py`): stage 1 the oil with the block pinned to
measured coolant; stage 2 the block with the oil pinned; stage 3 both free, as
the environment runs them. Seven drives qualify (coolant + oil + ambient ≥ 5 min).
Leave-one-drive-out cross-validation throughout (`fig21`):

| drive | coolant RMSE before → derived (held out) | oil RMSE before → derived (held out) |
|---|---|---|
| drive10 | 5.51 → 2.28 (2.35) K | 7.55 → 3.57 (3.90) K |
| 3aca2ec1 | 3.81 → 1.56 (1.65) | 3.31 → 1.22 (1.28) |
| cb67b01f | 3.88 → 2.60 (2.84) | 4.37 → 1.31 (1.41) |
| fb988991 | 4.02 → 0.98 (1.17) | 4.88 → 1.95 (2.34) |
| 683640a0 | 6.99 → 2.93 (**14.2**) | 6.55 → 3.30 (**14.3**) |
| 7475b5d7 | 4.84 → **6.66** (6.82) | 7.12 → 5.95 (6.22) |
| 670063b2 | 4.47 → **5.31** (5.39) | 7.93 → 5.17 (5.65) |

**Read the three bold cells.** 683640a0 holds the only warm-up in the logs — the
one stretch where the radiator is shut and the block's heat capacity shows —
so left out, the capacity is unidentified: c_block and the coolant heat share
are known as a RATIO, not separately. 7475b5d7 and 670063b2, the two drives at
41–45 °C ambient, get WORSE on coolant: after load the car's heat-management
valve runs the coolant ~9 K lower (82–84 °C), which a fixed stand-in setpoint
cannot do, and two drives with ambient and load confounded are not enough to fit
the valve's control law.

## 3 · validate.py rows 8–11

| row | before | derived | car's band | |
|---|---|---|---|---|
| 8 oil, drive10's hottest 10 min | 96.4 °C | **97.0** | 103–111 | **still outside** |
| 9 oil apparent time constant | 14.0 s | **60.0** | 70–100 | **still outside** |
| 10 coolant, synthetic climb | 94.5 °C | 93.0 | 83.6–95.5 | inside |
| 11 coolant, drive10 free-running | 88.4 °C | **92.2** | 91.8–94 | **now inside** |

**8 of 11**: 6 of 7 literature, 2 of 4 car. The bands were not touched (row
10's moved 83.5–95.6 → 83.6–95.5 because drive B added warm coolant, by the rule
fixed on 28 September). **drive10 is in the fit** — it is the only drive with
sustained high engine speed at low road speed — so rows 8 and 11 were also
scored with drive10 HELD OUT (the leave-one-out parameters): row 8 **96.1 °C**,
still outside; row 11 **92.0 °C, still inside** — the coolant fix is a genuine
prediction, not a fit to its own band.

**Why rows 8 and 9 still miss, and why they were not forced in.** Row 8: even
fitted ON drive10, the structure cannot hold drive10's oil at 103–111 °C while
also fitting the other six drives. ~~About 6 K of it is the block~~ **Corrected
29 September, measured by `model_vs_data.row8_split`:** of the 12.0 K miss,
4.6 K is the block (during that stretch the car's valve let the coolant rise to
97–99 °C where the model regulates near 93) and 7.3 K is the oil running 4.4 K
over coolant at sustained 4300 rpm where the car's runs 11.7 K. The "about 6 K"
was never measured. Row 9: the node's time constant rose from
14 s to 57 s; the car's apparent 70–100 s is still ~30 % slower. Changing the
fit's objective until these rows pass would be tuning to the target (mistake 12's
shape). **Drive A** (a sustained climb logged with oil, `logs/DRIVE_PLAN.md`) is
the data that would settle both.

## 4 · Constants computed from the data, not typed

`derive_params.py` → `data/derived_params.json` → `derived.py` → the modules.
`build_dataset.py` runs it after writing `data/`. Each value carries its method
and the data fingerprint; `verify_docs.py` fails if the data moved and the
derivation did not.

| constant | before | derived (28 Sep) | how |
|---|---|---|---|
| thermal block + oil (12 values) | ASSUMED, except ua_block_oil | fitted on seven drives | `calibrate_thermal.fit`, seeded |
| radiator size | 300 / 60 / 700 | ×1.42 | its SPLIT stays unidentifiable |
| boost ceiling | PR = 1 + 14.5023 m / (1 + 6.4019 m), cap 2.6 | the measured envelope, monotone, cap 2.515 | no fitted constant at all |
| MAP_CEIL_KPA | 250.0 typed | cap × 99.3 | |
| SPARK_A | 13.33 | 13.42 | solved for zero mean bias |
| ENR_DWELL_LO / HI | 2.0 / 9.0 s (retired axis) | 1.5 / 3.0 s | timestamp axis, 100 genuine readings |
| DELIVERABLE_TORQUE | typed table | measured through the derived plant | |

**What could not be derived, and why** — every other constant, in
`REFERENCES.md` section 4b. In short: the turbine node, the exhaust side, the
charge temperature and the combustion correlations have no channel on this car;
the road load was tried from the wheel-torque channel and is not identified
(mass 2 846 kg, 90 % range 2 181–3 432); the enrichment's speed band and depth
were tried and are not identified (grid edge); the spark slopes and the shift
point are derived once and deliberately not re-derived (mistake 6; drive B was
driven in manual mode).

## 5 · Drive B and the boost ceiling (`fig22`)

At full throttle, genuine boost readings, drive B reached 127–143 kPa at
1400–1650 rpm, 146–175 at 1650–1900, 175–225 at 1900–2150 and 218–229 at
2150–2400. The derived envelope gives the modelled engine 133–138, 147, 198 and
221 kPa there — inside the car's range at every point up to 2400 rpm.
**Corrected 29 September: inside the range is the wrong test for a CEILING.**
Against the HIGHEST reading in each 200 rpm band (engine speed interpolated to
each boost reading), the derived ceiling is 9–20 % LOW at 1600–2000 rpm (the car
reached 193 kPa at 1800–2000 rpm where the model allows 155) and −7 to +7 % from
2000 rpm up. "Follows drive B at 1400–2400 rpm", written above and in CLAUDE.md,
was wrong at 1600–2000. The
8 September formula gave the model MORE low-rpm boost than the car made in a
roll-on; above 2600 rpm the envelope runs 10–15 kPa above the car.

**Stated, not hidden:** roll-ons are transients, so this is spool-limited boost,
not necessarily steady capability (Toyota rates 500 Nm from 1800 rpm). There is
no torque channel, so the gearbox kickdown cannot be retired on this evidence:
at 2107 rpm (8th, 130 km/h) the model delivers ~335 Nm against the 375 Nm a
9 % grade asks, and still kicks down. The envelope's top bin now rests on 8
independent readings, not 4.

## 6 · The premise, one change at a time (`fig23`)

| step | baseline | current-grade | predictive | peak turbine | preview vs current-grade |
|---|---|---|---|---|---|
| as committed | 951.9 | 624.5 | 628.4 | 884 °C | −0.4 |
| 1 thermal derived | 926.9 | 597.5 | 601.3 | 884 | −0.4 |
| 2 + boost, spark, table derived | 928.2 | 599.3 | 603.3 | 884 | −0.4 |
| 3 + envelope ceiling at ambient | 927.3 | 596.6 | 599.8 | 884 | −0.3 |
| 4 + exhaust = air + fuel | 1052.1 | 587.5 | 590.3 | 889 | −0.3 |
| 5 + enrichment dwell | 1052.1 | 587.5 | 590.3 | 889 | −0.3 |
| 6 + air density 1.12 | **920.1** | **520.5** | **523.5** | **883** | **−0.3** |

Step 3 combined two changes (the envelope and the ambient inlet); neither binds
on the climb's steady state, so they were not separated. Step 5 moves nothing:
the climb runs below the 180 kPa enrichment gate. The climb's oil peak fell from
110 to 94 °C at step 1, which is what removes most of the oil damage term.

## 7 · Found and fixed on the way

| what | where | effect |
|---|---|---|
| exhaust flow = fuel × 15 | `engine_env`, `app/estimator.py`, `car_thermal` | now air + fuel; turbine +5 K on the climb |
| ceiling at the CHARGE temperature | `engine_env._track_torque` | now ambient; 2000 rpm 345 → 316 Nm deliverable |
| air density typed 1.2 | `Vehicle.demand` | now p / (R T) = 1.12 at 42 °C |
| M12 "fix" never worked | `generality_test.py` read `info["mdot"]`, never emitted | the τ axis now uses the climb's measured 123.6 g/s (was silently 112.5) |
| premise figures unguarded | `verify_docs.py` | `check_premise.py` writes `results/premise.json`; the checker verifies it is fresh and that the documents agree |
| `check_map.py` backpressure 1.12 | `check_map.py` | now `EXH_BACKPRESSURE_RATIO` (1.15); map unchanged, spot EGTs +6–7 K |
| `fit_envelope.py` fitted a different formula from the plant's | `fit_envelope.py` | now prints the plant's own envelope, from the same code |
| fitted k quoted as 0.837 | docs | `compare_log.py` prints 0.839 on the 26 points; retired |
| results files no script produced | `traces_130kmh.json`, `sweep_speed_grade.json`, `phase_d_130kmh_raw.json` | `run_results.py` regenerates them |
| evaluate.py reported damage one way | `evaluate.py` | adds a thermal-only column (a reporting change; episodes untouched) |
| H/τ sweep compared preview with REACTIVE only | `generality_test.py` | now also reports preview over CURRENT-GRADE, AUDIT.md C3's comparator (section 7b) |
| placeholder zeros in the dataset | `build_dataset.py` | each channel's leading run of zeros masked (AUDIT.md M8 had reached only the app) |
| missing channels reported as "fuel cut" | `build_dataset.py` | counted separately |
| export capitalisation | `build_dataset.py`, `new_drive.py`, `car_thermal.py` | channel names matched case-insensitively |
| stale documents | `DOCUMENT_STATUS.md`, `REFERENCES.md`, `README.md`, `validation_table.md`, `CHECKPOINT.md`, `CLAUDE.md`, `handoff.md`, `NEXT_CHAT_PROMPT.md`, `new_drive.py`, code docstrings | swept against `verify_docs.py`; `Roadmap_Two_Plants.pdf` was listed clean and carries the void 7.6 → 49.9 sweep; REFERENCES still called the engine version open a week after it was settled; README's history section still closed on the withdrawn ablation argument, now flagged |
| `presentation/index.html` out of date | the page | a visible bilingual banner on the page; its first line declares it a dated record, and `verify_docs.py` prints that it skipped it on every run |
| the checker | `verify_docs.py` | new checks: the derived constants and the premise are FRESH against the data; the premise figures in the documents; retired: the old premise, fitted k 0.837, 295.0 min. Dated session reports are exempt from the retired-figure scan, like AUDIT.md |

## 7b · The H/τ sweep, with the honest comparator (`generality_test.py`)

`generality_test.py` measured "preview" as predictive minus REACTIVE — the
comparison AUDIT.md C3 showed is mostly protection depth and timing, which a
policy that knows only the current grade gets for free. It now reports both. On
the derived plant, with the τ axis on the climb's measured 121.3 g/s of exhaust:

| turbine τ (H/τ) | predictive over reactive | **predictive over current-grade** |
|---|---|---|
| 6.3 s (4.77) | 13.3 pts | **−0.0 pts** |
| 19.7 s (1.53) | 14.9 pts | **−0.0 pts** |
| 47.2 s (0.64) | 21.3 pts | **−0.0 pts** |
| 141.6 s, 471.8 s | never exceeds the limit (fixed-limit table); +0.1 / +0.3 pts in the percentile table | |

and 0.0 points at every cost curvature of H1 (linear to exponential). **On the
hand-written policies and the locked single-step climb, preview has no value at
any H/τ once the honest comparator is used.** That is not a refutation — C3
says hand-written policies cannot settle this, and one step in grade is the
road where knowing the grade NOW is as good as knowing it 30 s ahead — but it
means **no sweep result can be cited for the criterion today.** The trained
ablation on varied roads (Phase D) is the test, and then Phase F on varied
roads.

**The ten old agents, re-scored on the derived plant** (`run_results.py`;
still a record — 110 km/h, dt 0.2, one road, an older plant): training beats
current-grade by **+25.7** points; sighted minus blinded, paired by seed, mean
**−1.3** points (sd 5.5, t −0.53, Wilcoxon p 1.00) — indistinguishable from
zero, as before. Thermal-only damage: predictive and current-grade tie (47.3 %
against 47.2 %), so the hand-written deficit is still the knock term. The
speed-by-grade sweep still binds at 3 of 12 combinations; 12 % at 130 km/h
peaks at 883.0 °C.

## 7c · The app's pins, and which change moved each

The app's replay pins moved, and each was traced by reverting one change at a
time on the full replay; with all four reverted, both pins return exactly.

| pin | before → now | what moved it |
|---|---|---|
| `pull01` peak estimated turbine | 609.2 → **604.8 °C** | the derived enrichment dwell: `pull01` logs no lambda, so the fallback runs through `BaselineECU`, which now enriches much sooner into a pull (reverting it alone: 618.0 °C) |
| `pull01` thermal warnings | 1 → **0** | either the dwell or the exhaust-flow change, each alone restores it |
| `7475b5d7` peak estimated turbine | 890.6 → **873.1 °C** | exhaust = air + fuel (reverting it alone: 890.7 °C). That drive reports its own spark and lambda; on its rich pulls air + fuel is ~12.5 × fuel, not 15 |
| `7475b5d7` thermal warnings | 15 → **14** | the same |

`python -m app.test_replay --full`: **59 of 59** with the new pins, the reason
written beside them in the file. Neither figure is a measurement of the car.

## 7d · Three new entries in the mistake log (CLAUDE.md)

19. **A fix that read a key nobody wrote** — AUDIT.md M12's "fix" averaged an
    always-empty list and fell back to the value it replaced, for twelve days.
20. **The oil node had the wrong structure, and no parameter could fix it** —
    the drives "pulled opposite ways" because the equation lacked the mechanism.
21. **A drive planned without the channel every heat flow needs** — drive B
    omitted ambient temperature, and the dataset filled it silently.

## 8 · The sep17 merge is not documents-only

A dry-run merge (`git merge-tree`) shows **seven conflicts, four of them code**:
`engine_env.py`, `train.py`, `evaluate.py`, `verify_docs.py`. `sep17`'s
`engine_env.py` still carries the six-speed gearbox. Resolve code toward this
branch, then re-run `verify_docs.py`: its documents will carry figures this
branch has retired (mistake 16).

## 9 · Next

1. **Review and commit** this working tree (nothing is committed). Run
   `verify_docs.py`, `test_reward.py`, `check_roads.py` and
   `python -m app.test_replay --full` first; all pass on this tree.
2. **Drive A** is now the most valuable drive: it is the data rows 8 and 9 need,
   and the coolant regulation law. Add `Ambient temperature` to every drive's
   channel list.
3. **Retrain on the derived plant** — or after drive A. The plant moved; the ten
   agents in `runs/` are a record twice over.
4. **Merge sep17** with code resolved toward this branch.

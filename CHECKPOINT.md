# CHECKPOINT.md — state as of 16 September 2026

**What this file is for:** a dated snapshot of where the work stands and what was
verified when. `CLAUDE.md` is the permanent handoff and the mistake log — the
rules and the traps, written to outlive any one week. This file is the diary of a
particular day, and it is meant to go out of date. Where the two disagree,
`CLAUDE.md` and the scripts win. Regenerate the numbers rather than trusting this
file if it is more than a week old.

> **10 September, v16 and its audit.** The load constant `k` is now derived
> rather than fitted, and the residual reads 1.4 % with zero free parameters.
> An audit of that change found it measures no part of the plant, and that the
> intake temperature channel reads compressor-outlet air. See the section at the
> bottom of this file and mistakes 12 and 13 in `CLAUDE.md`. `AUDIT_2026-09-10.md`
> was one of the five duplicates deleted on 11 September; what it found is in
> those two mistakes. The repository is now on GitHub at `JadFelemban4/GRAD-project`,
> private.

> **11 September, v17 and a document sweep.** The charge-temperature correction
> shipped, the operating points moved down to **30–75 kPa**, and every tracked
> document was swept against the data. See the 11 September section at the
> bottom of this file.

> **14 September, the citation pass, the live app and a ninth drive.**
> `REFERENCES.md` now records, row by row, which of `validate.py`'s eleven
> bands have a source and which do not — **seven do not**. `app/` runs the
> same physics alongside the car. `pull01` takes the manifest to **nine
> drives, 295.0 minutes** and adds zero samples by design. Two findings
> change what the model may claim: the B58 has **no thermostat**, and the
> compression ratio depends on an engine version nobody has recorded. See the
> last section of this file.

> **13–16 September, v19, the ninth drive and the live app.** `pull01` joined
> `logs/raw/`, taking the manifest to **ten drives, 295.0 minutes** — it
> contributes zero samples and zero operating points by design, so no
> calibration figure moved. `app/`, the live supervisor, was imported and then
> hardened; two defects in it are now **mistakes 14 and 15** in `CLAUDE.md`, and
> a third, **mistake 16**, is about the release archive that carried it. See the
> section at the bottom of this file.

---

## Phase status

| Phase | Status |
|---|---|
| A · setup | done |
| B · match the simulator to the car | **passed** — 1.4 % load residual with k derived (0.831, zero free parameters), 1.1 % with k fitted (0.837, one). 26 pooled points, 30–75 kPa, 295.0 min logged. Read mistake 12 before quoting either |
| C · get an agent to learn | **next.** `train.py` exists and runs; nothing trained yet |
| D · baselines and the ablation | not started. **This is the floor of the project** |
| E · battery plant | not started. `battery.py` does not exist |
| F · the H/τ sweep | preliminary only, from hand-written policies |
| G · writing | not started |
| **APP · live supervisor** | **working and tested, 46 of 46 replay checks.** `app/` runs this same physics beside the car and estimates turbine temperature. A SECOND deliverable — it does not advance D, and D is the passing bar |

**Phase D is the passing bar.** Validated simulator + agent beating two baselines
+ an ablation isolating preview. Do not start E or F until D produces a table.

---

## Full verification run — 9 September 2026

<!-- RETIRED-OK: section -->

Every script in the repo was executed end to end. **All eight passed.**

| # | Script | Result |
|---|---|---|
| 1 | `plant.py` | ✅ four sweeps; torque 431–514 Nm across the boosted sweep |
| 2 | `validate.py` | ✅ **8 of 11** inside band; τ_turb 48.0 s; 2997.5 cc |
| 3 | `check_premise.py` | ✅ **829.2 · 548.6 · 437.6 · 548.6** |
| 4 | `verify_docs.py` | ✅ every published figure matched. Run it and read the total it prints |
| 5 | `test_reward.py` | ✅ **4 of 4** |
| 6 | `build_dataset.py` | ✅ 295.0 min, 10 drives, 23 points |
| 7 | `compare_log.py` | ✅ **PASS** — 1.4 % load residual with k derived, 1.1 % with k fitted |
| 8 | `generality_test.py` | ✅ H2 table reproduced: 16.5 / 18.0 / 26.0 pts |

Nothing in the repository is stale. Every published figure regenerates.

### The premise check, in full

<!-- RETIRED-OK: section -->

Protection trigger **1123 K (850 °C)** — the knee of the turbine damage term.

| policy | fuel g | damage | peak turb °C | peak oil °C |
|---|---|---|---|---|
| baseline ECU (neutral trims) | 4091 | **829.2** | 879 | 128 |
| reactive protection | 4175 | **548.6** | 859 | 123 |
| predictive protection | 4314 | **437.6** | 852 | 109 |
| predictive, **preview disabled** | 4175 | **548.6** | 859 | 123 |

**The ablation held again.** Preview-disabled lands on reactive across *all four*
reported quantities, not just damage. Reactive cuts damage 33.8 %, predictive
47.2 % — **13.4 points**.

The cost is legible and worth quoting: predictive burns **139 g more fuel than
reactive** (+3.3 %) and **223 g more than baseline** (+5.5 %) to buy that damage
reduction, and it drops peak oil by **19 °C** where reactive manages 5 °C.

### The validation table

| Quantity | Model | Published | Status |
|---|---|---|---|
| Displacement | 2997.5 cc | 2990–3000 | inside |
| MFB50 at MBT | 8.5° | 8–10 | inside |
| Best BSFC (λ1, knock-feasible) | 241.2 | 235–260 | inside |
| Knock-limited spark (3000 / 200 kPa) | 11.0° | 8–14 | inside |
| EGT cruise band, min | 714.5 °C | 600–750 | inside |
| EGT cruise band, max | 777.3 °C | 600–750 | **outside** |
| Turbine housing τ | 48.0 s | 40–120 | inside |
| Oil temp, sustained climb | 110.2 °C | 115–140 | **outside** |
| Oil τ | 16.0 s | 20–400 | **outside** |
| Coolant, thermostat-regulated | 94.5 °C | 88–108 | inside |
| Coolant apparent τ | 9.5 s | 1–600 | inside |

The three misses are documented in `validation_table.md` and are **not** to be
closed by tuning toward the band.

### The reward gate

| check | result | detail |
|---|---|---|
| neutral scores ≈ zero | PASS | −0.00438 (want \|r\| < 0.05) |
| refusing torque is punished | PASS | starver **−0.28044** vs neutral −0.00438 |
| disabling preview changes the observation | PASS | max \|Δobs\| = 1.44 |
| rewards are finite | PASS | 1499 / 1499 / 1499 steps |

For information, not pass/fail: a random policy scores −0.08197.

---

## Changes made on 9 September

Two fixes and one documentation correction. **No calculation changed; every
number above is identical before and after.**

### 1. `gymnasium` was not installed

Installed **1.3.0**. It is an active line in `requirements.txt` (only the SB3 and
torch lines are commented out), so this was a missing environment, not a missing
dependency declaration.

### 2. Console encoding — six scripts crashed or mangled their own output

`build_dataset.py` wrote all three CSVs successfully and **then died** printing
its summary table, because a Windows console defaults to cp1252 and cannot encode
`λ`. The data was fine; the run looked failed. `validate.py` printed `—` as `?`
in its title.

Fixed by forcing UTF-8 on stdout in the six scripts that print non-ASCII:
`build_dataset.py`, `validate.py`, `compare_log.py`, `extract_steady.py`,
`generality_test.py`, `train.py`.

All six re-run clean at exit code 0. **`train.py`'s patch is the one exception —
it is unverified at runtime**, because the script exits immediately with a clean
"stable-baselines3 is not installed" message and never reaches its print
statements. It compiles; it will be confirmed the first time SB3 is present.

An audit of all 13 scripts confirms **no script prints non-ASCII without the
guard**. The remaining seven confine theirs to comments and docstrings.

### 3. `CLAUDE.md` carried a stale drive count

<!-- RETIRED-OK: section 113, 7 -->
The old sentence is quoted below deliberately, as the record of what was
corrected. `verify_docs.py` needs the marker above to know that.

It said "seven drives, 113 minutes, five carrying samples." The data says **eight
drives, 168.1 minutes, seven carrying samples**.

The old sentence was also wrong in a subtler way, and the correction records the
distinction: **`fb988991` does carry samples** — 16.3 minutes of them — but not
one of its windows survives the span and gap checks, so it contributes zero
*operating points*. Six carry samples; five carry points. Three different counts.

---

## Open problems, honestly stated

### 1. Phase F's H2b threshold rule does not survive the correct engine

<!-- RETIRED-OK: section -->

H2b sets the constraint at the 80th percentile of the unprotected trace, which
assumes the temperature spends a *minority* of the episode near its peak. The
standard scenario is a sustained climb — nine of its twelve minutes at the top —
so p80 lands on the peak and the top three rows saturate at 100 % for both
policies.

Today's run confirms it, unchanged:

| C_turb J/K | τ s | H/τ | t_ref K | reactive | predictive | edge |
|---|---|---|---|---|---|---|
| 800 | 6.7 | 4.47 | 1152 | 100.0 % | 100.0 % | 0.0 |
| 2500 | 21.0 | 1.43 | 1152 | 100.0 % | 100.0 % | 0.0 |
| 6000 | 50.3 | 0.60 | 1146 | 100.0 % | 100.0 % | 0.0 |
| 18000 | 150.9 | 0.20 | 1022 | 0.0 % | 57.0 % | **57.0** |
| 60000 | 503.1 | 0.06 | 752 | 0.0 % | 9.7 % | 9.7 |

**Until the percentile rule is replaced, use the fixed-limit H2 table:**

| C_turb J/K | τ s | H/τ | reactive | predictive | preview edge |
|---|---|---|---|---|---|
| 800 | 6.7 | 4.47 | 79.6 % | 96.1 % | 16.5 pts |
| 2500 | 21.0 | 1.43 | 78.7 % | 96.7 % | 18.0 pts |
| 6000 | 50.3 | 0.60 | 73.2 % | 99.1 % | **26.0 pts** |
| 18000 | 150.9 | 0.20 | — | — | never exceeds the limit |
| 60000 | 503.1 | 0.06 | — | — | never exceeds the limit |

Preview edge rises as τ grows — **16.5 → 18.0 → 26.0** as H/τ falls from 4.47 to
0.60 — then the component becomes massive enough that the constraint stops
binding. That is the direction the physical argument predicts.

**These numbers moved from 0.0 / 0.1 / 0.2 at the old 930 K trigger. Nothing
about the plant changed — only the threshold.** Report the threshold with every
preview figure.

### 2. Known limitations to state in the thesis, not fix quietly

- **Vehicle validation covers 30–75 kPa only.** Steady points require steady
  driving, which is light-load driving.
- **The boosted inversion is within 2 % of the car, once the charge temperature
  is right.** 587 modelled samples against 887 logged `Boost pressure` readings
  above 200 kPa, logged median 226 kPa: the raw sensor gives 279.5 kPa,
  **+23.7 %**; `plant.charge_temperature()` gives 232.7 kPa, **+1.9 %**. An
  ambient + 8 K rule scores 227.5 kPa, +0.7 %, and was rejected as a knob tuned
  to hit the target. What is still uncertain under boost is the MAF ceiling at
  1020 kg/h and the logger's round-robin sampling.
- **Peak power is not a prediction.** Manifold pressure is an input. An operating
  line is not a compressor map.
- **The compressor envelope is unmeasured above 0.303 kg/s corrected**, because
  that is where the MAF saturates. Only the 0.33–0.36 kg/s bin remains empty and
  no drive can fill it with this sensor.
- **The radiator is not identifiable on this car**, and the channel census proves
  it: every water-pump and fan-actual channel is all-zero. A constrained fit
  gives R² = 0.157 with a negative ram coefficient. Stop trying.
<!-- RETIRED-OK -->
- **Oil above 117 °C is extrapolation.** That is the hottest oil anywhere in the
  logs, on `7475b5d7`; 111 °C after the filter. This line said 103 °C until
  10 September, which was the figure before the eighth drive arrived — quoted
  here on purpose, as the record of the correction.
- **Steady points are steady for fast quantities only.** The 60 s window is fully
  settled for air, lambda, spark and manifold pressure, and reaches just **71 %**
  of a turbine thermal step (τ = 48 s). Never validate a thermal quantity at a
  steady point.
- **Enrichment uses dwell above `ENR_LOAD` = 180 kPa as a proxy** for turbine
  inlet temperature, which this vehicle does not expose. The gate moved from
  200 kPa with the manifold-pressure *definition*, not with the physics, and
  selects the same 1055 samples. The weakest cell of the fit is 3500–4500 rpm at
  **long** dwell: n = 47, observed 0.90 against a modelled 0.93.

---

## What to do next, in order

1. `pip install "stable-baselines3[extra]"` — **2 minutes**. Also confirms the
   last unverified encoding patch.
2. `python train.py --steps 50000 --seed 0` — **about 4.6 hours on one CPU core**,
   measured not guessed: the environment runs at 19.5 steps/s alone and 3.0
   steps/s once SAC's gradient updates are included. **Plan an overnight, not an
   evening.** Checkpoints land every 10 000 steps. Expect a poor result; it
   running is the point.
3. `python test_reward.py` before trusting any training curve.
4. **Five seeds, one per team member, overnight** — `--seed 0` through `--seed 4`.
   Then the same five with `--no-preview`. That is Phase D's input.
5. **Phase D**: three baselines, one fixed evaluation protocol of 20 episodes,
   median and interquartile range over five seeds.

> **Once the 20 evaluation episodes are fixed they never change.** Changing the
> test set after seeing results is the one mistake this project cannot recover
> from.

Full detail: [handoff.md](handoff.md).

---

## Session of 9–10 September 2026 — v16, and an audit of it

### What was run

<!-- RETIRED-OK: section -->

`engine-supervisor-v16.zip` was unpacked over the working copy. All 38 archive
files are byte-identical to the archive. All six checks were run in order.

| script | result |
|---|---|
| `check_premise.py` | 829.2 · 548.6 · 437.6 · 548.6 at 1123 K; rows 2 and 4 equal to the last float bit |
| `verify_docs.py` | failed on three documents the unzip left behind, then passed once they were corrected. Run it and read the total it prints |
| `test_reward.py` | 4 of 4, neutral −0.00438, starver −0.28044 |
| `check_map.py` | 85 of 85 adjacent pairs monotonic, 6 unreachable, 0 `knk` |
| `validate.py` | 8 of 11 inside band, τ_turb 48.0 s, 2997.5 cc |
| `compare_log.py` | derived 1.4 %, fitted 1.1 % |

**The preview identity was checked below the printed decimals.** A probe compared
the reactive and preview-disabled rollouts at full float precision. All seven
returned fields are bit-identical: fuel `4175.220663624409`, damage
`548.6498477371352`, peak turbine `858.6302607939912`, knock `0`.

### Why `verify_docs.py` had failed

Not v16's fault. The archive holds 38 files and does not contain the six
documents written on 9 September, so unzipping left them behind unchanged while
everything else moved to v16. Three of them still carried retired figures. The
checker passed on a clean extraction of the archive alone, all along.

Fixed on 10 September: `Context.md` and `DATA-MODEL.md` — both deleted on
11 September as duplicates — had a live seven-drive dwell figure corrected, and the historical quotation in this file was marked
`RETIRED-OK`, which is what the checker requires for a deliberate mention. That
dwell figure has since been recomputed again on the corrected manifold-pressure
scale, and now reads **178 s above 207 kPa**.

The checker itself was reworked after this run — see the 11 September section —
so its totals from that day do not compare with today's.

### What the audit found

Two entries were added to the mistake log in `CLAUDE.md`.

- **Mistake 12 — the load residual tests no part of the plant.** Because
  `map_from_airflow()` inverts the exact relation `run_cycle()` uses, volumetric
  efficiency, residual fraction and intake temperature all cancel out of the
  comparison. The 1.4 % is the ECU's filling channel against its own air-mass
  channel. Forcing volumetric efficiency to 0.5 leaves the residual at 1.3740 %.
  There is no part-load test of the breathing model anywhere in the repository.
- **Mistake 13 — the intake temperature channel reads compressor-outlet air.**
  The B58's charge cooler sits inside the intake manifold, downstream of the
  throttle, so the "before throttle valve" sensor is before the cooler. A
  modelled post-cooler temperature in the inversion lands on the logged boost
  pressure. Recomputed from the shipped data on 11 September, over 587 modelled
  samples against 887 logged readings above 200 kPa whose median is 226 kPa:
  **232.7 kPa, +1.9 %**, where the raw sensor gives 279.5 kPa, **+23.7 %**. The
  boost gap was the temperature, not the breathing model.

### Stale figures corrected the same day

<!-- RETIRED-OK -->
This paragraph is the record of what changed on 10 September, so every arrow
reads old → new *as of that day*. Two of those new values have since moved
again; the note underneath carries the current ones.

<!-- RETIRED-OK: 192, 31, 82 -->
Oil extrapolation 103 → **117 °C**. Enrichment v4 fitted on seven → **eight**
drives. MAF ceiling 192 samples on four → **517 on five** drives. Compressor fit
30 534 → **74 013** quasi-steady samples. Vehicle validation 31–79 → **31–82 kPa**.
Load residual 2.3 % over 17 points → **1.4 % and 2.8 % over 22**. Reactive damage
reduction 33.9 → **33.8 %**. The claim that the inversion and the logged boost
channel agree inside 4.4 % below 80 kPa was removed; both pressure channels are
pre-throttle and disagree by 44–52 % at the steady points.

**Current values, 11 September.** The charge-temperature correction moved the
point span again: it is **30–75 kPa** now, not 31–82. And the fitted residual is
**1.1 %** against the derived **1.4 %**, over the same 23 points — dropping the
fitted parameter makes the residual rise, not fall.

### Also corrected, in the second pass

<!-- RETIRED-OK -->
A record of edits made on 10 September; the superseded values are named on
purpose, because they are the thing that was corrected.

<!-- RETIRED-OK -->
`validation_table.md` section E now says eight drives and 168.1 minutes, and its
MAF and manifold-pressure items carry the current counts. Its thermal test
condition keeps the 7.6 g/s figure but now states plainly that the condition
sits **below** the hardest sustained 60 s fuel flow in the logs — **8.7 g/s** —
rather than above it. `README.md` moved off the 2.3 % residual in both places.
The module docstring of `engine_env.py` and two comments in `build_dataset.py`
moved off the seven-drive correlations and the 1.163 combustion-air ratio, which
is **1.095** on the current dataset; both are comments, and `test_reward.py` and
`build_dataset.py` were re-run to prove it. The regenerated `data/` files are
byte-identical to what was there before.

### Still open — these need a decision, not a correction

- **`compare_log.py --map-from-log` scores zero rows** on
  `data/master_points.csv`: the alias table has no entry for the manifold
  pressure channel under the short schema, so every row is dropped, the table
  prints empty, and the script still exits 0. `CLAUDE.md` says this mode exists
  to reproduce the pre-throttle failure for the thesis; it cannot, on the
  canonical dataset. Fail-open, the same shape as mistake 9.
- **`compare_log.py` tells the reader to look at volumetric efficiency** when
  the load residual is large. That quantity cancels, so the residual cannot grow
  for that reason. The advice is unreachable.
- **`validate.py` still prints that there is no compressor flow ceiling**,
  although `plant.boost_ceiling_kpa` exists and bounds the model.
- **`check_map.py` schedules lambda by load**, which mistake 4 identifies as the
  wrong variable. The effect is at most one degree per cell and no cell becomes
  `knk`, so no published figure changes.
- **The B58 cooler layout rests on vendor documentation**, not a BMW service
  source. Get the primary source before the thesis leans on it. The measured
  numbers behind mistake 13 stand either way.
- **Nothing asserts the 1.4 % itself.** `verify_docs.py` checks the constant,
  the derived value and the excluded alternative, but not the residual, so that
  figure can drift without the checker noticing.

---

## Session of 11 September 2026 — v17, and a sweep of every document

### What shipped: the charge-temperature correction

<!-- RETIRED-OK: section -->

`build_dataset.py` and `compare_log.py` no longer feed the pre-throttle intake
temperature channel into `map_from_airflow()`. That channel is a compressor
outlet — mistake 13 in `CLAUDE.md` — and the inversion now uses
`plant.charge_temperature()`. What moved, recomputed from the shipped data:

| quantity | value after v17 |
|---|---|
| operating-point span | **30–75 kPa**, 23 points, 295.0 min over 10 drives |
| load residual, k **derived** 0.831 | **1.4 %**, zero free parameters |
| load residual, k **fitted** 0.837 | **1.1 %**, one free parameter |
| a 20 °C reference state would need | k = 0.890 — the fit excludes it |
| enrichment gate `ENR_LOAD` | 180 kPa, 1055 samples above it |
| boosted inversion against the car | 232.7 kPa modelled against a logged median of 226, **+1.9 %** |

**Dropping the fitted parameter makes the residual rise, 1.1 → 1.4 %.** Say it
that way round. The derived form is not the more accurate one; it is the more
falsifiable one, because it has no constant to absorb an error with — which is
why it would have caught the wrong-engine bug on day one and the fitted form did
not.

The premise result did not move: **829.2 · 548.6 · 437.6 · 548.6**, reactive
cutting damage 33.8 % against predictive 47.2 %, a **13.4-point** gap. The
simulator never read that sensor; `engine_env` models its own charge temperature.

### The document sweep

**55 stale figures were found across the tracked documents.** Almost none of them
were in the code — the code had moved and the prose had not, which is mistake 11
happening at scale instead of in six places.

`verify_docs.py` was reworked in answer to that. It used to compare figures
recomputed from the data against constants written inside itself, which proves
the data has not drifted and says nothing about what any document claims. It now
recomputes the published figures from the shipped data, then **opens every
tracked document and compares what is written there against those numbers**,
reporting by file and line, and it still greps every document for retired values.
A passage that quotes a superseded figure on purpose must carry
`<!-- RETIRED-OK -->` in its section, which is an assertion that the passage is
history.

Run it and read the total it prints. **Do not write a check count into any
document** — it moves every time a figure is added, and a count in prose is one
more number to go stale.

### Five documents deleted, two kept

Seven overlapping status documents had accumulated. Five were duplicates of
`CLAUDE.md` carrying older numbers and were deleted. This file and
[handoff.md](handoff.md) were restored at the owner's request, because they are
wanted for the write-up, and both were brought current the same day.

They are now part of the tracked set that `verify_docs.py` scans, and that is the
condition of keeping them: **a second document is only safe while something
checks it.** The division of labour is stated at the top of this file —
`CLAUDE.md` is the permanent handoff and mistake log, this file is a dated
snapshot. What belongs in the first should not be restated in the second, which
is how five duplicates came to exist in the first place.

---

## Session of 14 September 2026 — the citation pass, and a merge

Two pieces of work met in one merge commit. They were done independently and
they are reported separately here, because only one of them was verified by the
person writing this section.

### What the citation pass was for

`validate.py` scores the model against eleven "published bands". Until this day
the repository cited **one** source for all eleven: the word "Heywood" in a code
comment, with no edition and no page. An examiner asking *"where does 115–140 °C
come from?"* had no answer.

`REFERENCES.md` replaces that. It is written for a reader who is not an
internal-combustion specialist — every term carries a plain-English gloss — and
it sorts every number in the project into four kinds: measured by us, general
engine physics, specific to the B58, or assumed. It is tracked by
`verify_docs.py`, so the figures it quotes from our own logs cannot drift.

### What was promoted, and on what evidence

Sources were opened, not remembered. Each row carries the page, column or
paragraph the claim was read from.

| what | status now | where it was read |
|---|---|---|
| Bosch relative air charge | **CONFIRMED** | US 6,588,261 B1, col. 3 l. 55 – col. 4 l. 2: *"rl = ma/m_norm … under the standard conditions: Tn=273 K, Pn=1013 hPa"* |
| Bore 82.0, stroke 94.6, displacement | **CONFIRMED** | Toyota Australia spec table GTP-009045 p. 1; BMW Canada Z4 2020MY guide p. 2; BMW 3 Series 05/2015 p. 7 |
| Row 2, MFB50 at MBT 8–10° | **CONFIRMED** as the common rule | Zhu, Haskara & Winkelman, IEEE TCST 15(3) 2007, p. 417 |
| Row 7, turbine τ 40–120 s | **PARTIAL** | Burke et al., IJHFF 52 (2015) §5.3 — housing heat flow settles from ~7 kW to ~3.6 kW within three minutes, bounding τ above at roughly 45–60 s |

Two corrections fell out of re-checking the six records the file already called
CONFIRMED: the Wiebe book's publisher is **Verlag Technik** (no catalogue that
could be opened shows the "VEB" prefix the file carried), and Chen & Flynn's SAE
650733 is titled *"Development of a Single Cylinder Compression Ignition Research
Engine"* — a paper about building a research engine, whose abstract never
mentions friction. **That the FMEP correlation in `plant.py` comes from a page of
it has not been checked.**

### What was searched for and not found — this is the useful half

- **Row 3, best BSFC 235–260 g/kWh.** No source states it. Heywood gives
  **270 g/kWh**, above the band; a 2018 SwRI/EPA turbocharged GDI engine measures
  **233**, below it. Our 241.2 sits between them. The band was **not** widened to
  swallow the evidence; it is labelled engineering judgement and bracketed.
- **Row 4, knock-limited spark 8–14°.** Nothing admissible, which is what the
  task expected. Douaud & Eyzat supply the knock *model*, not this band. Drop the
  row or relabel it an internal consistency check.
- **Rows 5, 6, 8, 9 and 11.** No source states a part-load exhaust-temperature
  range, a sustained-load oil band, or either time constant.

Seven of eleven bands therefore remain unsourced. **Say so in Chapter 3.**

### Two findings that change what the model may claim

**The B58 has no thermostat.** BMW's own training document (ST1505, information
status April 2015, §4.2) states that the conventional thermostat *"is replaced by
a so-called heat management module"* — a motor-driven rotary valve positioned by
the engine computer from the coolant and cylinder-head temperatures, with no wax
element and no published opening temperature. `thermal.py`'s `t_stat_open` = 88 °C
is therefore a **modelling equivalent** identified from the car's own coolant
channel (regulated 88–97 °C in every log), and must never be cited to BMW. It is
also a **third** reason the radiator is unidentifiable from the logs: the
radiator branch opening is a commanded valve angle, not a function of coolant
temperature, so even a coolant-flow signal would not close the heat equation
without the valve position.

**The compression ratio follows the engine version, not the model year.**
Manufacturer sheets on both sides print 10.2:1 beside the engine code
**B58B30O1** — the 285 kW / 382 hp engine, which is what `plant.py` models. But
Toyota UK's own technical specifications of Feb 2021, June 2022 and Feb 2024
print **11.0:1** for the 250 kW / 340 PS GR Supra 3.0 sold in Europe. **Nobody
has recorded which version this car is.** The rated output on its registration or
compliance plate settles it in one look; if it is the 250 kW car, the knock model
is running the wrong compression ratio. Third-party specification aggregators
splice the North American "382 hp" with the European "11.0:1" — such a listing is
two markets stitched together, not a manufacturer figure.

### Mistake 11 recurred a third time, and named two holes in the checker

<!-- RETIRED-OK: section 168.1, 8 -->
This subsection names the superseded figure throughout, because the figure is
what was corrected. The current dataset is ten drives and 295.0 minutes.

`pull01` took the manifest from eight drives and 168.1 minutes to nine and
175.5. Seventeen lines were swept. **Five were not**, by two different routes:

- **Three escaped the regex.** The dataset-size pattern requires *pooled*,
  *dataset*, *manifest* or a drive count within thirty characters of the figure,
  so `REFERENCES.md`'s "168.1 minutes of OBD-II logs from our own car" matched
  nothing. The anchoring is the right trade — a looser pattern misreported the
  thermal fit's "three drives (80 minutes)" as a wrong total — but it means a
  figure in an unusual sentence is invisible.
- **Two escaped inside a `RETIRED-OK` paragraph.** The marker exempts its whole
  paragraph, and a live claim about the current dataset shared a paragraph with
  the retired figure the marker was there for.

**And nothing in `RETIRED` was guarding 168.1 at all** — the seven-drive entry
still named "eight drives, 168.1 minutes" as the value to use instead, so the
list pointed at a figure that had itself been superseded.

All five are corrected, the seven-drive entry points at ten drives, and `168.1`
is now a retired pattern in its own right. It deliberately does not match "eight
drives" alone: the enrichment map and the compressor fit genuinely rest on eight
drives of samples, because `pull01` contributes **zero** samples.

### Verification on the merged tree — every script re-run

<!-- RETIRED-OK: section -->

| script | result |
|---|---|
| `check_premise.py` | **829.2 · 548.6 · 437.6 · 548.6**, trigger 1123 K; rows 2 and 4 identical |
| `validate.py` | **8 of 11** inside band; every model value unchanged |
| `test_reward.py` | **4 of 4** pass; neutral −0.00438, starver −0.28044 |
| `compare_log.py` | **PASS** — 1.4 % residual, derived k 0.831 |
| `check_map.py` | 6 cells above the compressor ceiling, **0** reachable fail-open cells |
| `verify_docs.py` | **all 33 checks pass**; 29 retired figures guarded, 51 historical mentions marked |
| `app/test_replay.py` | **36 of 36** pass, including the read-only and no-raw-data-on-disk assertions |

The citation pass changed no code logic and no numeric value: the compiled
bytecode and every numeric constant of `thermal.py` and `validate.py` are
identical to the commit before it. Only `test_reward.py`'s unseeded
random-policy line moves run to run, and it is printed under the heading
"FOR INFORMATION, NOT A PASS/FAIL".

### Not verified by the author of this section

`app/` and the ninth drive came from the other half of the merge. `app/test_replay.py`
was run here and passes 36 of 36, but the app's design, its estimator and its
alert thresholds were not reviewed. `CLAUDE.md` describes it; read that before
changing it.

### Still open after this session

1. **Which engine version the car is.** Two minutes with the registration.
   Decides whether the compression ratio is right.
2. **Row 7's actual time constant.** Burke 2014, *J. Eng. Gas Turbines Power*
   136(10) 101511, should carry the turbine-node capacitance and conductances,
   giving a published C/UA to set against our 48.0 s and 6000 J/K.
3. **The MTZ article** (Landerl et al., *MTZ worldwide* 76(10) 2015, pp. 22–29),
   the only BMW-authored document on this engine. Library access. It may settle
   row 3 and replace the grey training document used for the thermostat finding.
4. **Phase C.** Still the next real step, and nothing has been trained yet.

## Session of 14–16 September 2026 — hardening the live app, and a document sweep

*(Overlaps the section above by a day. The two were done independently: that one
is the citation pass, this one is the app. Neither supersedes the other.)*

### What arrived

| thing | what it is |
|---|---|
| `logs/raw/pull01-20260913_093527.csv` | the **ninth** drive. Purpose-built, 7 channels, to settle mistake 13. Contributes **zero samples, zero operating points** — no coolant channel, so the warm filter excludes it |
| `app/` | the live supervisor: reader, estimator, alert engine, server, three pages |
| `DOC/`, `presentation/`, `REFERENCES.md` | from the branch, in parallel — the document reorganisation and the provenance file |

### The dataset now reads three different drive counts, and all three are right

| population | count | used for |
|---|---|---|
| manifest | **9** drives, 295.0 min | "how much have we logged" |
| carrying usable samples | **6** | anything computed from `master_samples` |
| behind the fitted calibrations | **8** | enrichment, spark — `pull01` is not in them |

`verify_docs.py` asserts the first two separately. Quoting the wrong one is now
the easiest available mistake.

### What was verified, on the merged tree

| # | Script | Result |
|---|---|---|
| 1 | `verify_docs.py` | ✅ **All 33 checks pass**, 228 figure mentions scanned across 22 tracked files |
| 2 | `validate.py` | ✅ **8 of 11** inside band — unchanged |
| 3 | `test_reward.py` | ✅ **4 of 4**; neutral −0.00438, unchanged |
| 4 | `python -m app.test_replay --full` | ✅ **46 of 46** |

`check_premise.py`, `build_dataset.py`, `compare_log.py` and `generality_test.py`
were not re-run this session: nothing under them changed, and `verify_docs.py`
recomputes their published figures from the shipped data and agrees. Re-run them
before a release rather than trusting this line.

### The app's own numbers, pinned so a regression is visible

Replaying `7475b5d7` end to end:

| quantity | value |
|---|---|
| samples estimated | **14278 of 14340** (99.7 % of samples with the engine running) |
| peak estimated turbine | **884.9 °C** — a MODEL OUTPUT, not a reading |
| alerts | **13 thermal · 0 mismatch · 19 novel** |
| seed forgotten after | **461 s** — not the 145 s the code used to assume |

And on `pull01`, the fast regression: 2186 of 2193 estimated, peak **593.7 °C**,
4 novel, seed forgotten at 172 s.

**None of these is evidence about the car.** The turbine figure is a model
output with an assumed heat capacity and the alert counts are a property of
thresholds we chose. They are pinned so that a change to the pipeline shows up,
which is a different job from being a result.

### Three defects found and fixed — the detail is in CLAUDE.md mistakes 14–16

1. **The mismatch detector was measuring the throttle.** 55 alerts on
   `7475b5d7` looked like an over-sensitive threshold; the firing condition was
   actually true for **95.7 % of the drive** at a median of −52 %, because
   `Boost pressure` is a pre-throttle channel. Fixed with three validity gates,
   not a threshold change: **55 → 0**. The threshold did move, 15 % → 25 %, for
   a separate and measured reason.
2. **The app reported a turbine temperature its own physics called impossible.**
   The 500 °C seed sat outside the ambient-to-EGT bracket — on `pull01`, 300 K
   outside it. The fixed 145 s warm-up timer also used τ = 48 s, which is the
   *loaded* time constant; at cruise it is 151 s and at idle 239 s.
3. **The v19 archive was an older snapshot of everything except `app/`.**
   Unzipping it over the branch would have reverted a fortnight of document
   work, including three figures that had already been corrected once. They are
   now guarded by `verify_docs.RETIRED`.

### Two defects in `verify_docs.py` itself, both fixed here

- **It crashed while reporting.** The new document scanner echoes the offending
  line back; line 54 of this file contains a tick emoji; on a cp1252 console
  that raised `UnicodeEncodeError` and killed the run **after every check had
  already computed correctly**. Third occurrence of the character-encoding bug
  in this repository, and the worst place for it.
- **Its MAF-ceiling drive count and its MAF-ceiling sample count were counting
  different populations** — raw files against the warm-filtered dataset. Adding
  `pull01`, which pins 56 times in its raw log, pushed them apart: 6 drives
  against 547 samples over 5. Both halves now count the same set.

### What this session did NOT do

- **No training run.** Phase C is still where it was, and Phase D is still the
  floor of the project. The app is a second deliverable and it is not on that
  path — see the backlog at the end of `CLAUDE.md`'s plan section.
- **No live-car test.** Everything about the app is replay. The first item in
  its backlog is one drive with `--live`, and it is the only item that can find
  something replay cannot.
- **No fault has ever been shown to the mismatch detector.** Nothing in nine
  drives is broken, so every number behind it is a false-positive rate, not a
  detection rate. Say that in the thesis rather than implying validation.

---

## Session of 17 September 2026 — the merge, and a sweep behind the audit fixes

**No code behaviour changed.** One constant moved (`train.py`'s printed
estimate) and one guard was added. Everything else is documents.

### What arrived

`main` was **behind both branches** and carried no commit they lacked.
`JMF-2340550` held everything but one commit; `JMF-new-plan` added `aca526d`,
which only creates `ABSTRACT.md`, `CONTROL_SCOPE.md`, three `DOC/Abstract_*.docx`
and `presentation/plan.html`. Fast-forward, then merge: **zero conflicts**.

### What was verified, on the merged tree

Every script run, output read, nothing taken from a document:

| script | result |
|---|---|
| `verify_docs.py` | **38 of 38**, 311 figure mentions, 25 files |
| `test_reward.py` | **4 of 4**; neutral −0.00870, starver −0.49080 |
| `python -m app.test_replay` | **49 of 49** |
| `compare_log.py` | PASS, 1.3 % derived / 1.1 % fitted over 23 points |
| `check_premise.py` | baseline **294.2 at 812 °C**, constraint does not bind |
| `train.py --steps 3000` | ran; SAC trains |

### Six stale figures found and swept

All the same failure: the 16 September audit fixes moved the code and no
document followed. **Mistake 11 for the fifth time.**

| where | said | prints |
|---|---|---|
| CLAUDE.md, README.md, handoff.md | 256.5 · 801 °C · 2.2 pts | **294.2 · 812 °C · 1.8 pts** |
| CLAUDE.md, handoff.md | 36 of 36 / 46 of 46, peak 884.9 °C | **49 of 49**, peak **890.6 °C** |
| CLAUDE.md phase table + app section | "six known bugs", "none fixed" | **all six fixed** |
| presentation/README.md | 801 °C, "thirteen mistakes" | 812 °C, sixteen |

### Two measurements taken this session

<!-- RETIRED-OK: this is a dated record of what was measured that day; the
     tenth drive (Taif) took the total to 292.0 min and 0.206 % on 19 Sep -->
**Every drive replayed against the protection trigger.** One of nine binds:
`7475b5d7` peaks at 890.6 °C, **41 K above**, for **36 s of 172.6 replayed
minutes — 0.351 %**. The synthetic climb reaches 812 °C and misses by 38 K, so
**the car's own driving is 78 K hotter than the scenario written to stress it.**
The scenario is what is wrong, not the trigger.

**The training rate, re-timed.** `STEPS_PER_S` was 3.0, quoted as "4.6 hours on
one CPU core". Measured over 2000 SAC steps with updates running: **19.19
steps/s at one thread, 18.14 at six.** Both halves of the old claim were wrong
and neither is a hardware difference — one thread is marginally FASTER than six,
and the gradient updates cost ~2 %, not 6.5×. **Phase D is ~7.5 hours, one
evening, not "five overnights twice".** `plant.DTHETA_DEG` is what sets the
cost; it was halved on 16 September.

### Two holes left open on purpose

<!-- RETIRED-OK: naming the void figures IS the finding -->
- **`presentation/index.html`** still hard-codes 829.2 ×24, 548.6 ×70,
  437.6 ×16. Fixing it means regenerating the page, not editing a document.
- **`check_retired()` never opens it.** It builds its own list from
  `glob("**/*.md")` plus the root `*.py`, while `TRACKED_DOCS` — used by the
  FIGURE scan — does include the page. **Two scans, two file lists, and only one
  was fixed** when AUDIT.md L11 was closed. Measured: the retired scan opens
  25 files; 77 lines of that page would fire six retired patterns.

### One guard added, and it is not a figure

<!-- RETIRED-OK: the retired string is the subject of this paragraph -->
`King Abdulaziz` joins `RETIRED`. CLAUDE.md line 13 carried the wrong university
until `d57f3da` — inside a commit about `REFERENCES.md`, so the change is
invisible from the log. Confirmed with the team: **University of Jeddah**.
Verified by planting the string and watching the run fail. `DOC/*.docx`,
`DOC/*.pdf` and `presentation/index.html` were checked by hand; **none carries a
university name at all**, which is open if the submission template needs one.

### What this session did NOT do

- **No Phase D.** Nothing trained beyond a 3000-step smoke run.
- **No scenario chosen.** That is the one blocker, and it is a team decision:
  pick it from something physical, never by turning a knob until the gap looks
  good.
<!-- RETIRED-OK: the figures named here are the ones the run rejected -->
- **`verify_docs.py` caught the author mid-edit**, correctly, when explaining
  the void headline re-quoted 829.2 and 548.6. The errata came out with the
  figure. **When a number goes void, its corrections go with it.**

---

## Session of 18-19 September 2026 — the scenario, a gearbox defect, and the first ablation

**The project has a measured preview advantage for the first time.** It is one
seed against one seed and it is not quotable yet. Everything below was run, not
argued; the output of each command is in `results/`.

### The scenario is chosen and LOCKED

`make_grade_climb` defaults move **v_kmh 110 -> 130**. Decided before any
training run existed, from an envelope measured beforehand (eight grade/speed
pairs, in CLAUDE.md), and it does not move again. Four conditions hold together
for the first time in this project:

| | |
|---|---|
| constraint binds | 857 C against an 850 C trigger |
| torque trackable | 316 Nm demanded, **0.0 %** shortfall |
| reward gate | 4 of 4, neutral **+0.00048** |
| protection works | current-grade cuts damage **29.7 %** |

**The published towing standard was tried first and rejected by measurement.**
`SAE J2807` Davis Dam does not bind even behind a two-tonne trailer — 756.3 C,
94 K short. A truck standard at truck speeds asks a modest road power however
much torque the trailer adds.

### The gate caught a gearbox defect — mistake 17

`test_reward.py` FAILED on the new scenario: neutral scored **-0.124** against a
+/-0.05 band. The baseline demanded **381 Nm and delivered 359**, short 5.7 % on
**519 of 519** climb samples. `Vehicle.gear_for` selected on road speed alone, so
at the 115 km/h rung **the model upshifted into top gear halfway up a 12 %
grade**. A 4 % step in road speed moved the torque demand 23 %.

Fixed with a load term and a 25 % torque reserve. **Every operating point the
environment had already been used at keeps its gear**, so the old scenario is
bit-identical. Cost: peak turbine 899.4 -> 857.0 C, so the scenario binds by 7 K
instead of 49.

**Third defect in this project that was invisible until the load became real**,
after the wrong engine and the reward hack. Same shape every time.

### Phase C ran. Phase D has its protocol and its first point.

`train.py` executed past its import guard **for the first time**: 50 000 steps,
seed 0, sighted and blinded, **63 minutes each** — not the 45 min a 2000-step
probe predicted, so quote 63.

`evaluate.py` is new: **twenty frozen episodes**, weights pinned as literals, the
same for every policy. It exists because training-curve returns are NOT
comparable — the preference vector is redrawn every episode, and seed 0 ranged
from -506.4 to +643.6 over eleven episodes with its best in the FIRST five.

| policy | damage med | IQR | worst | fuel med |
|---|---|---|---|---|
| baseline ECU | 572.8 | 0.0 | 572.8 | 4528 |
| reactive | 540.9 | 0.0 | 540.9 | 4552 |
| current-grade | 402.6 | 0.0 | 402.6 | 4796 |
| **agent, sighted** | **194.7** | 35.6 | 378.8 | 5337 |
| **agent, blinded** | **261.4** | 19.9 | 336.9 | 5008 |

**SIGHTED over BLINDED: +11.7 points.** Sighted cuts 66.0 %, blinded 54.4 %.

### This reverses the hand-written result, and that is the finding

Earlier the same day, preview was measured with HAND-WRITTEN policies across
five scenarios — constant grade and four rolling periods — and **lost in every
one**, between -0.1 and -2.3 points. The cause is one line: `p_predictive` takes
`max(preview[+15 s], preview[+30 s])`, so on a road that keeps climbing it
protects continuously, including through easy sections.

**AUDIT.md C3 said hand-written policies cannot answer this. They now
demonstrably cannot: the two verdicts differ by 12 points.**

### Four limits on the +11.7, all of them stated

1. **n = 1 against n = 1.** The protocol wants five seeds each.
2. **The worst episode reverses it** — blinded 336.9 against sighted 378.8.
3. **The sighted agent burns 6.6 % more fuel**, 5337 against 5008 g.
4. **The twenty episodes vary the preference weights only**, not the road or the
   ambient — which is why every hand-written policy shows IQR 0.0. The protocol
   compares policies; it does not test robustness.

### What this session did NOT do

- **No five-seed result.** Eight runs remain, 63 min each, about 8.4 hours.
- **No second plant.** `battery.py` still does not exist, and with one plant the
  H/tau claim cannot be tested at all — only a curve, never an overlap.
- **The 115-125 km/h band still over-asks**, because the gear rule uses a flat
  torque ceiling on an rpm-dependent quantity. Not tuned away: lowering it would
  have moved 16 % at 110 km/h, the team's third scenario.

---

## Session of 19 September 2026 — the branches merged, and the gearbox is the car's

**The two working branches are one again.** `JMF-2340550` (Ghassan: the real
gearbox, the tenth drive, mistake 18) merged into the `sep17` line (mistake 17,
the locked scenario, `evaluate.py`, Phase D's first ablation). Two conflicts,
both in the gearbox, both resolved toward the measured side.

### What the merge took from each

| from `sep17` | from `JMF-2340550` |
|---|---|
| mistake 17 — the load-aware downshift | **the real ZF 8HP51**, eight published ratios on 3.150 |
| the locked 12 % / 130 km/h scenario | mistake 18 — `Actual gear` clamps at 6 |
| `evaluate.py` and its twenty frozen episodes | the tenth drive, +119.5 min |
| Phase D's first ablation, +11.7 points | the runtime 3 L verification |

**Ghassan carried mistake 17's `SHIFT_LOAD` into the eight-speed deliberately**,
so the merge resolved to ONE rule rather than a conflict. Without it the taller
top gear (2.016 overall against 2.312) would have reintroduced the mid-climb
upshift that 17 was written to stop.

### The gearbox is validated against the car, not just cited

Toyota publishes the 8HP51 set. **The car confirms it.** Reproduced independently
from `data/master_samples.csv` during the merge: **80 898 moving samples, 85.1 %
within 4 %** of one of the eight published overall ratios (Ghassan reports 86.7 %
on 79 105 — a sample-filter difference, same result).

It also **excludes the alternative**: the 6MT top gear is 2.927 overall, the
8AT 8th is 2.016, and the car measures **1.993** in top-gear cruise. That is
1.1 % from the automatic and 32 % from the manual — the car's own data says it is
the eight-speed.

### The locked scenario survived, and it survived BY LUCK

| | peak turbine | vs trigger |
|---|---|---|
| 110 km/h, real gearbox | 840 °C | **−10 K** |
| 130 km/h, invented gearbox | 857 °C | +7 K |
| **130 km/h, real gearbox** | **884 °C** | **+34 K** |

130 was chosen because it was the only speed that bound **on a gearbox that did
not exist**. On the real one it binds by 34 K instead of 7 — a better scenario
than the one that was picked. **Recorded in `make_grade_climb`'s docstring as an
accident, not as foresight.**

### And the mechanism is load per cycle, for the third time

The first explanation offered was "the real box holds a lower gear, more rpm,
more exhaust flow". **Measured, it is backwards:**

```
invented 6-speed   5th, overall 2.788   2913 rpm   316 Nm
real ZF 8HP51      7th, overall 2.589   2706 rpm   340 Nm
```

The real box is **taller** here, so the engine turns **slower** and each cycle
carries **more** load. Road power is identical — 96.4 kW at the wheels either
way. All the gearbox changes is how that power splits between torque and rpm,
and the higher load per cycle is worth **27 K of turbine housing**.

**Same mechanism as `12 % @ 90` running hotter than `4 % @ 150`, and the same one
that makes SAE J2807's slow heavy climb produce a cool turbine.** Three times now
the answer has been load per cycle rather than flow.

### Verified on the merged tree

```
verify_docs.py    All 38 checks pass, 311 figure mentions
test_reward.py    4 of 4; neutral -0.00038, starver -0.90349
check_premise.py  baseline 959.8 at 884 C; current-grade cuts 34.0 %;
                  preview over current grade -0.4 points
```

**`test_reward`'s starver margin recovered from −0.10 to −0.90.** The real
gearbox gives the engine room, so refusing to make torque is a clear crime
again — the number flagged on 18 September as the first to watch.

### What this session did NOT do, and it is the blocker

**No training run exists on this tree.** Two runs were on the invented gearbox
at 130 km/h; Ghassan's ten were on the real gearbox at 110 km/h without
`evaluate.py`. **All twelve are on trees that no longer exist**, and the 110 km/h
scenario does not bind at all — an agent trained there had nothing to learn about
protection.

Phase D restarts from zero on this tree: ten runs, seeds 0–4 sighted and blinded.

---

## Session of 19 September 2026, later — Phase D was NOT started, and four checks were run instead

**Phase D was requested, then stood down before any run was launched.** Nothing
was trained. `runs/` is untouched. What follows is verification work on the
merged tree, done in its place.

### Verified on this tree, independently

```
verify_docs.py    All 38 checks pass, 311 figure mentions, 15 tracked files
test_reward.py    4 of 4; neutral -0.00038, starver -0.90349
```

Both match what the merge reported, so the tree is the tree.

### 1 · The gearbox is the real one, reproduced rather than read

`Vehicle.gears` carries eight ratios on a 3.150 final drive, and **all eight are
reachable**: 8th on the flat at 130 km/h, 7th on the 12 % grade at the same
speed, 2706 rpm and 340 Nm.

Ghassan's channel finding was re-derived from `data/master_samples.csv` without
reference to his figures — overall ratio straight from rpm and road speed:

| | |
|---|---|
| moving samples | 80 898 |
| within 4 % of a published ratio | **85.1 %** |
| maximum value of `Actual gear` | **6.0**, on every drive |

Inside the samples the channel calls "gear 6": **60.2 % are really 8th, 17.4 %
really 7th, 15.5 % really 6th.** Top-gear cruise measures **1.997** overall
against the 8HP51's 2.016 (0.9 %) and the 6MT's 2.927 (32 %).

Mistake 18 stands in every particular. *(85.1 % on 80 898 here against
Ghassan's 86.7 % on 79 105 — the sample-filter difference this file already
records.)*

### 2 · Every cooling path is live on the locked scenario EXCEPT enrichment

Instrumented over a full neutral-policy episode:

| path | state | measured |
|---|---|---|
| thermostat / radiator | live | open 0.20 → 0.70, never shut, ~100 kW rejected |
| cooling fan | live | 0.4 rung for 97.4 % of the climb, never 1.0 |
| coolant pump | live | baseline at 1.0 |
| charge cooler | live | 42 °C ambient → 56.9 °C charge |
| knock retard | live | peak 3.2°, active 3.8 % |
| **enrichment** | **never fires** | **λ = 1.000 on every step** |

**And the enrichment is off structurally, not by accident.** The climb sits at
2706 rpm, and `base_lambda` returns 1.000 there at any load and any dwell —
178 or 220 kPa, 0 or 30 s. First enrichment appears at 3600 rpm. That is the
map being faithful to the car (mistake 4: no enrichment below ~3300 rpm however
long boost is held).

Consequence for Phase D, now in CLAUDE.md's limitations: the baseline does not
use one of the four protection levers here and the agent can, so every "cuts
damage N %" figure against the baseline is inflated by a lever, not by
anticipation. The sighted-vs-blinded ablation is unaffected — both agents hold
the same lever.

### 3 · `dt` is inside the signal, not underneath it

Ghassan's open question 4, measured. Hand-written policies, locked scenario,
720 s, same seed and weights, only the step changed:

| policy | dt = 1.0 | dt = 0.2 | cuts vs baseline |
|---|---|---|---|
| baseline ECU | 959.8 | 900.9 | — |
| current-grade | 633.2 | 567.8 | 34.0 % → **37.0 %** |
| reactive | 679.0 | 622.5 | 29.3 % → **30.9 %** |

Peak turbine is **dt-invariant** (884.0 °C at both) and fuel moves 0.2 %, so the
physics is sound. The damage integral is not. **The gap between two fixed
policies moves 4.8 → 6.1 points on the step alone**, against preview effects of
0.4–2.3 points from hand-written policies.

`train.py` runs 0.2, `evaluate.py` runs 1.0, so **a trained agent is scored in a
discretisation it did not learn in**. The cause is `_track_torque`'s PI, which
accumulates per step with no `dt` — the defect AUDIT.md M16 fixed for `SLEW`, in
the loop M16 left alone. The preview horizon is clean: `_preview()` uses
`int(h / dt)`, so H is wall-clock at every step size.

Shared by both agents, so not a bias by construction; **symmetry unmeasured**.

### 4 · Mistake 18's outstanding order, carried out

Mistake 18 ends "re-derive it from the inferred gear before quoting the p99
again". Done:

| gear filter | n | p95 | p99 |
|---|---|---|---|
| steady CHANNEL gear | 15 654 | 12.75 | 21.75 |
| **steady INFERRED gear** | **13 329** | **9.75** | **18.00** |

Not cosmetic. **But it does not replace the published 9.8**, because neither
that figure nor its n = 10 896 reproduces from the shipped data under a
gear filter alone — the torque-cut half of the original filter is undocumented.
The row now carries no quotable p99 until its author re-runs it.

### One documentation defect found and fixed

`neutral_action()`'s fan caveat was inverted in both halves — see the
19 September addition to mistake 10. The constant was deliberately NOT changed;
the sentence was.

### What this session did NOT do

- **No training, no Phase D, no five-seed result.** Ten runs still outstanding.
- **`runs/sighted_seed0` and `runs/blind_seed0` are still there**, from the
  invented gearbox, both at 50 000 steps. `train.py` resumes from the newest
  `ckpt_*_steps.zip`, so `--seed 0` on this tree would print "already at 50000
  of 50000 steps", train nothing, and write a `final.zip` holding an agent from
  a gearbox that no longer exists. **Move them aside before Phase D starts.**
- **The step budget is still undecided** — 50 000 steps is eleven episodes for a
  weight-conditioned policy, and Ghassan asked for a decision before the five
  seeds are treated as Phase D's input.

---

## Session of 20-21 September 2026 — the SECOND audit, and the Phase D result does not reproduce

**Nothing in the repository was changed by the audit itself.** It ran read-only:
every historical tree was exported with `git archive`, every rebuild went to a
scratch directory outside the repo, and `train.py` was exercised only on a copy
of `runs/`. The only file this session adds is `AUDIT2.md`, plus this entry.

**`AUDIT2.md` is the report: 1041 lines, 50 new findings** (3 CRITICAL, 12 HIGH,
16 MEDIUM, 13 LOW, 4 NITPICK), IDs `C2-n` / `H2-n` / `M2-n` / `L2-n` / `N2-n` so
they never collide with `AUDIT.md`. 34 are CONFIRMED by execution here, 16 are
PLAUSIBLE on one agent's output and are labelled as such.

### The headline: neither Phase D file is a result, and this branch's does not reproduce

`python evaluate.py runs/sighted_seed0 runs/blind_seed0` on HEAD, 76 min,
same two trained agents as `results/phase_d_seed0.txt`:

| row | the shipped file | re-run on HEAD |
|---|---|---|
| baseline damage / peak | 572.8 / 857 C | **959.8 / 884 C** |
| sighted median (IQR, worst) | 194.7 (35.6, 378.8) | 279.3 (9.6, 360.6) |
| blinded median (IQR, worst) | 261.4 (19.9, 336.9) | 351.1 (31.8, 435.0) |
| **sighted over blinded** | **+11.7** | **+7.5** |

**Why:** the SB3 archives decode to 130 km/h at **2913 rpm**, which is the
invented six-speed in 5th after mistake 17's load-aware downshift. The ZF landed
at `27e720c`, seven hours after `a68715f` committed the result. The +7.5 is not
a Phase D point either -- it scores agents on a plant they never saw.

**Isolated on three exported trees, one neutral episode each, 720 s at dt 1.0:**

```
six-speed (a68715f)   110 km/h  damage 294.2  peak 812.3 C
six-speed (a68715f)   130 km/h  damage 572.8  peak 857.0 C
ZF 8HP51  (f6b46e9)   110 km/h  damage 462.7  peak 839.7 C
ZF 8HP51  (HEAD)      130 km/h  damage 959.8  peak 884.0 C
```

Every published baseline row is on that grid. Speed is worth -44.3 K and the
gearbox +27.4 K; they add to the observed gap within 0.4 K, so nothing else in
the 209-line `engine_env.py` divergence moves the baseline.

### Three things the tree says that the scripts contradict

| document | says | prints today |
|---|---|---|
| `CLAUDE.md`, `README.md`, `handoff.md` | baseline 294.2 at 812 C, "the constraint does not bind" | 959.8 at 884 C, binds by **34 K** |
| the four abstracts, `CONTROL_SCOPE.md` | 175.5 min, nine drives, 22 points, 30-74 kPa | 295.0, ten, 26, 30-75 |
| `CLAUDE.md:1664`, `CHECKPOINT.md:657` | 13 thermal alerts on `7475b5d7` | **15** |

### The guard is blind to the figures that decide the project

16 deliberate drifts injected into a `git archive` copy; 4 CAUGHT, 12 MISSED.
Caught: `8 of 11`, `ten drives`, `DTHETA_DEG`, `derived k`. **Missed:** the load
residual, the app's peak turbine, every Phase D figure, the premise table, the
scenario docstring, **`make_grade_climb`'s default `v_kmh` 130 -> 120**, and
**`TURB_PROTECT_K` 1123 -> 1100**. `check_retired` globs `**/*.md` plus root
`*.py` only, so `presentation/index.html`, `plan.html` and `data.js` -- which
<!-- RETIRED-OK: naming the void set the deck still ships IS the finding -->
carry 829.2 / 548.6 / 437.6 / 13.4 on more than a hundred lines -- are outside it.

### M16 is not fixed, and the mechanism is not the one recorded

Same policy, seed and weights; only the step changed:

| policy | dt 0.2 | dt 1.0 | dt 2.0 |
|---|---|---|---|
| baseline | 900.9 | 959.8 | 1034.9 |
| current-grade | 567.8 | 633.2 | 723.2 |
| **cuts vs baseline** | **37.0 %** | **34.0 %** | **30.1 %** |

Splitting the baseline integral by term: turbine 862.26 -> 858.87 (-0.4 %), oil
unchanged, **knock 69.33 -> 13.85**. So **94 % of the dt shift is one step**: a
knock spike of 66.3 damage/s at t = 181 s, where the grade steps 0 -> 12 %,
charged for one step whatever the step is. `_track_torque`'s PI is per-step, but
its effect lives inside the remaining 0.4 %. The dt paragraph in `CLAUDE.md`
names the wrong loop.

### Verified as still holding, by execution

C1, C2 (ECU on the lagged baseline MAP; retard peak 3.2 deg, 3.3 % of steps),
C3, H1, H3, H4, H7 (`master_points.csv` byte-identical in two input orders), H8,
M5, M7, M8, M10, M11. **Incomplete here:** M16, H6 (resume blanks `curve.csv`
and re-saves `final.zip` on a no-op), M2/M12 (`generality_test` still scores with
its own `damage(scale=25.0)` against the retired reactive comparator), M3, H2,
L11, M15.

### The scenario: locked in its parameters, not in its experiment

Git supports the envelope-before-choice account (`9f41082`, 18 Sep 17:26, three
hours before the first run). It cannot settle "decided by the team", and the
sighted run's SB3 `start_time` is **26 s before** the lock commit `1df41a2` --
the run demonstrably used the new code, but no artefact records an uncommitted
tree. The plant under the locked scenario was then replaced and the result kept.

**What protects the project, and it is measured:** preview LOSES on this row
under every hand-written policy (-0.6, -2.3, -0.4), so the row cannot have been
chosen to favour the claim. Say that in the defence.

### What this session did NOT do

- **No fix was applied.** Every finding in `AUDIT2.md` is described, none is
  implemented. The repository is exactly as it was apart from the report.
- **No training.** `runs/` still holds the two six-speed agents, untouched.
- **Four of nine audit parts ran on the orchestrator rather than on agents**,
  because the account's usage limit killed two full workflow runs; the coverage
  and what could not be verified are listed in the report's confidence ledger.

## Session of 21 September 2026 — results get a fingerprint, and the guard gets the figures that decide the project

The second audit's fixes 1 and 2. Fix 3, the document sweep, is NOT done and is
still the next session's work — see the ledger below, which is how much of it is
outstanding, counted.

### Fix 1 — every trained result now records the plant that produced it

<!-- RETIRED-OK: 11.7 -- naming the void figure IS the finding -->
`AUDIT2.md` C2-1: `results/phase_d_seed0.txt` says +11.7 points and was produced
on an invented six-speed gearbox that commit `27e720c` replaced seven hours
later. Nothing in `runs/` recorded which gearbox. The header that was supposed to
say was a hardcoded string, **byte-identical on both plants**.

New `fingerprint.py` builds a block from the LIVE objects:

| field | what it is | fatal? |
|---|---|---|
| `plant_sha` | SHA-256 over the bytes of `plant.py` + `thermal.py` + `engine_env.py` | yes |
| `gears`, `final_drive` | the transmission | yes |
| `dtheta_deg` | the crank-angle integration step | yes |
| `turb_protect_k`, `oil_protect_k` | the protection triggers | yes |
| `scenario` | grade / v_kmh / t_amb, from `inspect.signature` | yes |
| `episodes_sha` | a hash of the twenty frozen evaluation episodes | yes |
| `git_head`, `git_dirty`, `python`, `train_dt`, `eval_dt` … | context | no |

**The plant SHA outranks the git commit deliberately.** The audit measured that
the 18 September sighted run started **26 seconds before** the commit that locked
the scenario, from an uncommitted working tree — so `git rev-parse HEAD`
describes a tree that run did not use. It is recorded, and it is advisory.

**`dt` is advisory too, and that is not an oversight.** Training builds its
environment at dt 0.2 over 900 s; `evaluate.py` scores at 1.0 over 720 s. The
asymmetry is real, deliberate on both sides, and an open problem (H2-2). Making
it fatal would refuse every legitimate evaluation this project performs, so it is
printed side by side with the finding named instead.

What changed where:

- `train.py` writes `runs/<tag>/meta.json` before the first step, and on resume
  **refuses** a missing or mismatched fingerprint (`--force-plant-mismatch`
  overrides and says so in the output).
- `train.py` **appends** to `curve.csv` instead of overwriting it (H2-3: a re-run
  of a finished agent blanked a twelve-episode curve to its header), and a re-run
  with nothing left to do now returns **before** `model.learn` and `model.save`
  instead of silently rewriting the only copy of a trained agent.
- `evaluate.py` builds its scenario line from `inspect.signature(make_grade_climb)`,
  prints the fingerprint block, writes the whole report to `--out`, and refuses a
  model whose `meta.json` disagrees.

Six paths were exercised rather than argued: a fresh run, a no-op re-run, a
resume that appends, a refused plant mismatch, a refused missing `meta.json`, and
a clean match.

### Fix 2 — the guard now sees the figures that decide the experiment

`AUDIT2.md` C2-2 measured that fourteen realistic drifts were injected into a
copy of the tree and **twelve went through green**, including
`make_grade_climb(v_kmh=)` 130 → 120 and `TURB_PROTECT_K` 1123 → 1100. Either one
re-bases every damage figure in the repository while every document goes on
saying 130 km/h and 850 °C.

`check_scenario()` asserts, from the live objects: the four `make_grade_climb`
defaults, both protection triggers, the eight ZF ratios and the final drive,
`evaluate.DT` / `DURATION`, a hash of `EPISODES`, `check_premise`'s baseline
damage and peak (a real 34-second rollout, identical to the script's own first
row), both of `compare_log`'s residuals and its fitted k (by running it and
reading what it prints), and `app/test_replay`'s pinned peak and alert counts.

Three structural changes came with it:

- **ONE file list for both scans**, from `git ls-files`, so a file that is in the
  repository cannot be outside the checker by accident. It reaches every tracked
  `.py`, `.html`, `.js` and `.txt` now, with HTML tags stripped per line. The
  retired scan went from 35 files to 52.
- **`RETIRED-OK` is figure-specific** (H2-6). A marker names the figures it
<!-- RETIRED-OK: 168.1, 113 -- the marker syntax being quoted, not a claim -->
  excuses: `<!-- RETIRED-OK: 168.1, 113 -->`. A marker that names none can excuse
  the RETIRED scan only — it can no longer switch off the comparison against live
  data. The per-file exempted count is printed every run.
- **A mention is not a marker.** Five passages in this repository *discuss* the
  mechanism in backticks, and every one of them was switching the checker off for
  its own paragraph — including one whose next sentence states a live and wrong
  dwell figure. An occurrence inside an inline code span is now ignored.

### The known-stale ledger, and why the run is green with rot outstanding

Turning the guard on over the whole repository surfaced roughly two hundred and
fifty stale figures in one run. **Every one is already a written finding** in
`AUDIT2.md` with fix 3 scheduled against it.

Leaving the checker red was rejected: a checker that is red for a week is a
checker nobody reads, and this project's house rule is to run it before quoting
any number. Exempting the files was rejected too — that is the blunt instrument
H2-6 is about, one level up.

So they are **counted**. `KNOWN_STALE` carries one row per (file, figure) with
the audit finding, the exact count, and **the exact stale values**. A row that
grows is new rot and fails. A row that shrinks fails too, so the ledger has to be
swept in the same commit as the documents. A row whose *values* move fails — a
count alone cannot see a stale line being edited into a differently stale one,
<!-- RETIRED-OK: 294.2, 812 -- naming the stale pair IS the example -->
which is how `CLAUDE.md`'s "294.2 at 812 °C" could have had its 812 changed
unnoticed.

**Read the ledger total as the size of fix 3.** It is printed every run.

### The acceptance test is in the repository

`drift_test.py` re-runs AUDIT2 Part 4a's injected drifts against the current
tree, each in its own copy of the tracked file set, and reports CAUGHT or MISSED
per row. It is the file that makes fix 2's claim checkable instead of asserted,
and it is the reason `verify_docs.py` may not simply be trusted when it prints
green.

### What this session did NOT do

- **Fix 3 is not started.** The document sweep is the next session's work and the
  ledger is its inventory.
- **No training, and no Phase D.** `runs_sixspeed_18sep/` is untouched.
- **`presentation/` is untouched.** Its void premise figures are ledgered under
  C2-3, not fixed; the deck still must not be shown.

# Drive C's decision rule — PROPOSED, 19 October 2026

**Status: proposed, not yet binding.** It replaces the placeholders of the
13 October draft (`logs/DRIVE_PLAN.md`, drive C). It becomes binding when Jad
and Ghassan have answered decisions 14–23 in `results/VALIDATION_DECISIONS.md`
and the analysis script that implements it is committed, **before the repeat
drive and before anyone computes the ignition retard on any drive C log**. That
is the training gate's item 6 (`CLAUDE.md`): the rule is written before the drive.

Every number below is printed by `python drive_c_rule_numbers.py`
(`results/DRIVE_C_RULE_NUMBERS.txt`) or named with its source file. The research
behind it (19 October) read no drive C log and computed no retard on any log:
five strands (Bosch knock-control documentation and papers, the retard channel's
noise in the old logs, the statistics, the project's own sensitivity, the
simulator's half and full steps), a synthesis, and three independent reviews
(blindness, statistics, engine realism).

## 0. What was seen before this rule (disclosure)

- Drive C was driven on 18–19 October, **before** this rule existed; the draft
  of 13 October (`c16b857`) was committed before the drive but its numbers were
  placeholders. The rule was therefore not fixed before the drive, as the plan
  asked. The repeat drive is what it is fixed before.
- Known about the 18–19 October files, from Jad's side's check
  (`drive_c_check.py`, branch `JMF-2340550-driveC-check`, not on GitHub when
  this was written), and used here only as context: each channel was read about
  every 0.90–0.93 s (p99 gap 1.47 s); ambient 17.5–31.5 °C; neither C1 nor C2
  was covered (one step matched the plan; no segment in the climb's cell).
  None of this is an ignition value.
- **No ignition value from those files has been computed, printed or plotted**
  by this session. To be completed by Ghassan before the rule is committed:
  who watched the live display of the two angles during the drive, and any
  impression they formed.

## 1. Guards that keep the rule blind

1. Drive C CSVs stay **out of `logs/raw/`**, and `build_dataset.py`,
   `full_run.py` and `car_spark_boost.py` are not run on them, until C2's
   stage C and the C1 analysis below have run. (`build_dataset.py` would write
   both angles into `data/master_samples.csv` and re-derive the plant;
   `car_spark_boost.py` would print C1's spark outcome.)
2. `new_drive.py` no longer prints the retard (target minus actual); it reports
   only how many ignition readings a file holds. `--unblind` prints the values,
   and is used only after the analysis.
3. The analysis script asserts `plant_sha` `3c48890dd15bc116` and the committed
   `derived_sha`, and refuses to run on any other plant.
4. **Stage A** reads only engine speed, air mass, coolant and ambient. **Stage
   B** reads the ignition channels inside the pre-windows only, and counts the
   pairs in the other windows by poll position. The list they produce (steps,
   shams, segments, blocks, cuts, the cell choice, every flag and reason) is
   committed with its SHA-256 before **stage C** reads one response-window
   retard. Stage C refuses to run if the hash differs.
5. Stage C runs **once**, after the repeat drive, on every drive C file
   (18–19 October, the repeat, any cool session driven before it). No criterion
   in this document changes once stage A has run on any drive C file; a
   shortfall is made up by more driving. A later drive after a verdict is a new
   test with its own freeze; the first verdict is reported beside it and never
   recomputed.

## 2. Definitions

- **D1 genuine readings.** The logger polls one channel per row in column order.
  A channel's genuine readings are its poll rows (the round-robin phase,
  estimated per run between logger breaks); forward-filled rows are never used,
  nor leading placeholder zeros (AUDIT.md M8), blanks, or values outside rpm
  500–7000, air 4–1020 kg/h, coolant 40–130 °C, ambient 2–55 °C. If fewer than
  99 % of single-change rows share the phase, the run is flagged and only value
  changes count.
- **D2 pairing and retard.** A file is analysable only if its target column is
  polled 1–2 rows after its actual column (V8). For each genuine actual reading:
  retard = min(target polled just before, target polled just after) − actual,
  the before-target no more than 1.25 s earlier. This can miss a pull, never
  create one, whichever way the target moves between reads. A pair belongs to a
  window only if both its target readings and its actual reading lie inside it.
- **D3 grid.** Both angles move in 0.75° counts; thresholds are stated in counts
  (2.25° = 3 counts). Baselines are lower medians, so they are observed values.
- **D4 load.** Inverted MAP = `plant.map_from_airflow(air/3.6, rpm,
  plant.charge_temperature(T_amb, T_coolant))` (mistake 2), as in
  `car_spark_boost.py`. Engine speed and air mass are interpolated linearly
  between genuine readings to the times needed.
- **D5 the model's own spike at a step, KI1.** spark_pre = `BaselineECU.base_spark(rpm₁, MAP_pre)`
  + `iat_compensation(T_ch)` (−5° below 340 K coolant); KI1 =
  `plant.predict(rpm₁, MAP₁, T_ch, T_cool, spark_pre, 1.0)["knock_integral"]`,
  with MAP_pre from the pre-window medians and rpm₁, MAP₁ at the first genuine
  air reading after t1: the environment's own sequence (`engine_env.py`, spark
  on the previous step's MAP). Computed in stage A on the frozen plant; never
  recomputed.
- **D6 held gear.** No vehicle-speed channel: a gear change is flagged when two
  consecutive genuine engine-speed readings give |ln(n₂/n₁)|/Δt > 0.17 s⁻¹.
  Drive B's twelve held-gear roll-ons stayed at or below 0.106 s⁻¹; a downshift
  shows at least 0.187 s⁻¹ across the slowest reading gap.

## 3. C2 — does the car pull timing on a sudden load step?

### Item 1: what counts as a step

Air-mass readings aᵢ at τᵢ; Mᵢ = the median of the readings in (τᵢ − 20 s, τᵢ].

1. **Departure:** the first reading k with a_k > 1.2·M_{k−1}; t0 = τ_{k−1}, M = M_{k−1}.
2. **Trigger:** t1 = the first of readings k, k+1 with a ≥ 1.5·M; neither: no step.
3. **Confirmation:** the two readings after t1 are ≥ 1.5·M, the first also ≥ M + 25 kg/h.
4. **Fall:** τ_f = the first reading after t1 with a < 0.85 × the previous reading or a < 1.3·M.
   Scanning resumes at min(τ_f, the first reading after t1 + 10 s).

The draft's bare "+50 % between two readings" fires 1.6–1.8 times a minute in
light cruise; on drive B this detector finds each of the twelve roll-ons once.

**A step is valid (stage A, no ignition channel) only if all hold:**

| | criterion |
|---|---|
| V1 | steady cruise: ≥ 10 air readings in (t0 − 20 s, t0], all within 0.7–1.3·M; engine speed max/min ≤ 1.05 there, median 1400–2600 rpm |
| V2 | light load: M ≤ 100 kg/h (below it the steady retard is exactly 0 on about 80 % of old-log readings) |
| V3 | spacing: no air reading above 1.3·M in (t0 − 40 s, t0] (a Bosch knock retard recovers in about 12 s) |
| V4 | held gear (D6) from t0 − 20 s to t_W |
| V5 | held step: every air reading in [t1, t_W] ≥ 1.3·M, and t_W ≥ t1 + 2.5 s |
| V6 | coolant median over the pre-window ≥ 80 °C, and ambient was logged |
| V7 | **primary set: KI1 > 1.0**, the level at which the model's own ECU pulls 3°. 0.85 < KI1 ≤ 1.0 is a side set, reported, never in the verdict. A pinned air reading counts as high; its KI1 is flagged as a lower bound |
| V8 | the file's target column is polled 1–2 rows after its actual column |

Every step that passes counts, planned or not; the passenger's notes never
include or exclude one. Stage B then requires ≥ 10 pairs in the pre-window, ≥ 3
in the late window, and a baseline B with −0.75° ≤ B ≤ 0.75°. Steps failing on
B are counted (n_B) and reported.

### Item 2: the windows

- **Pre-window P = (t0 − 20 s, t0].** B = the lower median of its retards.
- **Late window L = (t1 + 1.0 s, t_W]**, with t_W = min(t1 + 5.0 s, τ_{f−1} − 0.6 s).
  **Only L decides.**
- **Early window E = (t0, t1 + 1.0 s]** is reported, and feeds remedy (d) only.

Why: the first second after a step is where pairing can manufacture a pull
(Bosch removes its pre-emptive load-step retard at up to 3° per working cycle)
and where a pre-emptive or torque-deficit retard sits; a knock-control retard
(3°, recovering about 0.75° per 1–4 s) and the model's own pull both reach L.
The 0.6 s guard keeps pairs that straddle the pedal release out of L. Holding the
pedal 7 s where legal lets L run its full 4 s.

### Item 3: what counts as pulling timing

A step **pulls** if max over L of (retard − B) **≥ 2.25°** (3 counts). One Bosch
knock event is 3.0°, its first recovery level 2.25°, Bosch's example pre-emptive
retard 2.25°; in steady light cruise single readings reach ≥ 2.25° on 1.3 % and
never 3°. Use the maximum, not a mean: the actual angle is most likely the
cylinder being computed, so a one-cylinder retard shows on about one reading in
six. A step with any (retard − B) above 12° (the Bosch and model retard limit)
is **unreadable**: excluded and counted; if more than one valid step in four is
unreadable, C2 is inconclusive.

### Item 4: the verdict

The cuts are computed **at freeze from the realised blocks** by
`drive_c_rule_numbers.cuts()`: "pulls" at the smallest count a never-pulling car
reaches at most 5 % of the time, "does not" at the largest count a car pulling
on 60 % of steps reaches at most 5 % of the time, with q 0.075 (jitter), m 0.45
(miss rate, one retarded cylinder of six) and ICC 0.1. A new block starts at a
valid step in a new file, or one starting at least 5 min after the previous
valid step's fall. Planning table, blocks of 7:

| valid steps N | 16 | 20 | 24 | 30 | 35 |
|---|---|---|---|---|---|
| **pulls** if K ≥ | 5 | 5 | 6 | 7 | 7 |
| **does not** if K ≤ | 1 | 2 | 3 | 5 | 6 |

- **"Pulls"** needs K ≥ k_yes **and** the steps pulling more often than the sham
  windows (one-sided Fisher exact test, p ≤ 0.05).
- **"Does not"** needs K ≤ k_no **and** the channel check **and** that it still
  holds with every step excluded for B counted as a pull (K + n_B against the
  cut for N + n_B); otherwise *inconclusive (baseline)*.
- In between: **inconclusive**. Always report K/N with its exact 90 % interval,
  and K per block.

At N = 24 (cuts 6 / 3): a never-pulling car is called "pulls" 2.9 % of the
time; a car pulling on 60 % of steps is called "does not" 2.2 % of the time;
one pulling on 20 % gets "pulls" 27 %, inconclusive 31 %, "does not" 41 %.
**"Does not" means fewer than about 60 % of steps pull, not never.** If the miss
rate is really 0.58 (three late readings), wrong "does not" rises to 7.6 %; if
the jitter is 0.10 instead of 0.075, wrong "pulls" rises to 6.3 % before the
sham test. Steps driven with no break (one block of 24) need cuts 8 / 1: drive
the blocks apart.

The draft's 1 in 5 and one half read the *observed* share, which noise lifts by
about 0.08 with no pulls at all and misses lower by about half: at N = 24 it
would leave a car pulling on 60 % of steps inconclusive about half the time.

**Sham windows** measure the jitter on the day. Anchors, from C2 files only:
(a) the first air reading ≥ 40 s after each detected step's fall, valid or not;
(b) the grid t = 30, 60, 90 … s from each file's first row, more than 50 s after
any fall and at least 25 s before any step's t0. Each is scored like a step:
B* the lower median of the 20 s before; its window as long as the median late
window of the valid steps; validity V1–V4, V6 and the B rule, and no air reading
above 1.3·M* across. At least 24 valid shams are needed (plan 40).

**Channel check** (a blind channel can only say "does not"): at least 3
confirmed C1 onsets (item 7), of which at least 2 persist (2 of the next 3 pairs
≥ B_seg + 1.5°). Otherwise a "does not" becomes *inconclusive (channel)*.

### Item 5: the fewest valid steps

**16 valid primary steps.** Below 16: untested, and stage C is not run. Plan
**35 steps** in 5 blocks of 7 (about 20 full, 15 half), at least 5 min of
step-free driving between blocks, plus 8–10 min of step-free steady cruise for
the shams. Drive B passed the steady-cruise test on none of its roll-ons, so
expect a yield of about two thirds.

### Item 6a: ambient

The verdict covers only the ambient range of the valid steps (minimum to
maximum of their pre-window medians). **Neither verdict extends to hotter air**:
the ECU's intake-temperature compensation sits inside the target channel, so the
uncompensated "1° per 7 K" does not carry. 42 °C, the scenario's ambient, stays
untested.

### Item 6b: half and full pedal

Drive the split, but keep **one pooled verdict**. Declared secondary, never
changing the verdict or the remedy: a one-sided Fisher test on primary steps,
"large" (inverted MAP ≥ 120 kPa at the second air reading after t1, frozen in
stage A) against "moderate". Its power at realistic counts (about 13 large
against 8 moderate) is 43–51 % for 0.10 against 0.52, so it is descriptive. With the ambient secondary as well, Holm applies (the smaller
p ≤ 0.025). **Step size cannot separate knock from a tip-in retard**: knock, a
torque-deficit term and pairing artefacts all grow with step size, and
drivability and anti-jerk retards sit inside the target channel and cancel in
target minus actual. What separates them is timing (only L decides) and the C1
comparison below.

### What each verdict triggers (fixed now)

A late pull may be the car's steady knock limit at the new load rather than the
step. So the late-window pull rate is compared with C1: for each C1 segment, one
window ≥ 10 s in with as many pairs as the median late window, readings at
2000–3300 rpm and ≥ 160 kPa only; C2 late readings in the same band. The pulls
are **step-specific** only if C2 steps pull more often than C1 windows (one-sided
Fisher, 5 %), with both sessions' median ambients within 5 K and at least 10 on
each side; otherwise they are not step-specific.

| verdict | remedy |
|---|---|
| (a) does not | schedule the baseline ECU's spark on the current step's load (real ECUs compute spark every combustion; the model's spike then falls to KI 0.62–0.84 on its 72 test steps) |
| (b) pulls, not step-specific | the same remedy; C2's late readings are reported beside C1's knee |
| (c) pulls, step-specific | keep a load-step knock cost, sized with C1's knee |
| (d) L says no, but E alone reaches the "pulls" cut | current-load spark plus at most a brief protective retard (the median early pull, for at most 1 s); never knock damage |

## 4. C1 — the knee and the spark in the climb's cell

**Segment:** a maximal run of genuine air readings, each with inverted MAP
≥ 140 kPa at the interpolated rpm, 2000–3500 rpm, air < 1019 kg/h, coolant
≥ 80 °C and no gear flag. s0 = its first reading + 3 s (spool-up); it ends at
τ_{f−1} − 0.6 s of its own fall (a < 0.85 × the previous reading or MAP
< 140 kPa); it counts if it runs ≥ 7 s after s0. Only C1 files are used
(`car_spark_boost.readings()` pools every drive).

### Item 7: the knee

- **Onset:** the first pair at τ ≥ s0 + 5 s and ≤ 3300 rpm with retard ≥ B_seg
  + 2.25°, B_seg the lower median of the pairs in [max(s0, τ − 10 s), τ) (at
  least 3, all ≤ 0.75°). **Confirmed** if one of the next 2 pairs is ≥ B_seg +
  1.5° (a lone jitter reading survives this in about 1.4 % of segments).
- **K\*** = `plant.predict(rpm, inverted MAP, T_ch, T_cool, spark = that pair's
  TARGET angle, 1.0)["knock_integral"]`: at the target, because each degree of
  retard lowers KI by about 0.05 and would bias the onset low.
- **Estimate:** the median onset KI by an interval-censored (Turnbull) estimator
  over **all** segments: an onset gives (KI of the last quiet pair, K\*]; a
  segment with no onset gives (its highest quiet KI, ∞); one retarded from its
  first pairs gives (−∞, KI of its first in-cell pair]. Bosch reloads learned
  retard when a load range is entered, so segments that start retarded are
  expected; the estimator uses them instead of dropping them.
- **Uncertainty:** h = half the width of the 95 % interval from ≥ 2000
  resamples of whole segments; u_D = h/2; u_input = 0.032 KI (the charge-
  temperature path, part 4 of the script); u_num = 0;
  2·u_val = √(h² + (2·0.032)²).
- **Requirement R_K = 0.10 KI.** Retune iff |median − 0.85| > max(0.10,
  2·u_val); the new damage knee is the median, to 0.01. On the locked climb a
  knee of 0.75 makes the baseline's knock damage ×3.93 and 0.95 makes it ×0.15
  (part 3); the cost the agents meet on ordinary drives scales the same steep
  way. X1's preregistered reading would change only for a knee at or below
  about 0.62 (the research's re-score, 19 October).
- **Untested** if fewer than 8 confirmed onsets, or the median is not identified
  inside the observed range (then report "onset above x"). **Limited, no
  retune,** if 2000–2650 and 2650–3300 rpm give medians more than 0.10 apart.
  A logistic fit of P(retard ≥ 2.25°) against KI over all pairs is reported as a
  secondary estimate.
- **Which constants move:** only the damage knee (`engine_env.damage_rate`). The
  measured median is also compared with the model ECU's own threshold, KI 1.0;
  if that is off by more than max(0.10, 2·u_val), moving it (and the
  knock-limited surface fitted at 1.0) is recorded as a separate, later plant
  step, one change at a time.

### Item 8: the spark in the climb's cell

- **In-cell readings:** genuine polls of the actual angle at 2400–3000 rpm and
  165–185 kPa (`car_spark_boost.py`'s cell, ends included), coolant ≥ 80 °C,
  ambient logged. Fallback cell 2000–3500 rpm × 160–200 kPa, chosen in stage A
  from blind counts only if the primary cell has fewer than 15 counting segments.
- **E:** per segment, the median of (car actual − model schedule:
  `base_spark` + `iat_compensation`, −5° cold, no knock retard) over its in-cell
  readings; a segment counts with ≥ 5 in-cell readings. E = the mean of the
  segment values; u_D = their SD / √n_seg (segments are the unit; readings in
  one segment share its state). With more than one session, E per session and a
  random-effects u_D across sessions.
- **u_input** = √(u_al² + 0.86²): u_al the alignment term (half the change in
  model spark between neighbouring genuine rpm and air readings, RMS), and 0.86°
  the charge-temperature error through both the inverted MAP and the IAT
  compensation (part 4). u_num = 0 (closed form).
- **Requirement R_spark = 0.85°.** Shifting the boosted schedule by −0.85° for
  every car moves the locked climb's peak turbine by +9.95 K and its damage
  ×1.248 (part 2): R1's own basis, 10 K and ×1.25. The plan's 1.3° is the
  one-car trim conversion; this tests the schedule, which moves every car.
  **This departs from `results/VALIDATION_PLAN.md`'s proposed 1.3° and needs
  both signatures (decision 22).** The 1.3° reading is reported and decides nothing.
- **Action:** retune iff |E| > max(0.85°, 2·u_val): add E to `base_spark` at
  ≥ 140 kPa for every car. With u_input ≈ 0.86°, a retune in practice needs
  |E| ≳ 1.7°. This is an **action rule, separate from the label**: the plan's
  label (k = 2) will read *untested* unless |E| ≳ 2.6°.
- **Needs ≥ 15 counting segments**, or the row is untested. Plan 25–30 segments
  with ≥ 10 in-cell readings each.
- **Dry run:** in legacy mode on the committed readings the script must first
  reproduce −3.81° / 2.07 and −1.78° (`car_spark_boost.py`).

### Order, held-out data, ambient

If more than one change triggers: C2's remedy first, then the spark offset, then
the knee, each measured on its own (`premise_split.py` style) with
`test_reward.py`, `check_roads.py` and the three app suites. A spark retune moves
the climb's knock integral, so the order matters. A retuned row is labelled
*fitted, held-out check pending* until a later drive logs both angles in the
cell. Damage keeps being reported with and without the knock term until the
knee's held-out label is validated or limited. C1's labels carry "extrapolated
in ambient from [min, max] to 42 °C" and "in duration" (20–30 s segments against
the twelve-minute climb).

Under "nothing is wrong", the three binding decisions (C2, knee, spark)
together act wrongly about 8–10 % of the time. Stated, not hidden.

## 5. What the repeat drive must deliver

- **Channel order**, selected in this order: Engine speed, Air mass flow, Actual
  ignition angle, Target ignition angle from torque intervention, Coolant
  temperature, Ambient temperature (the target is then polled right after the
  actual; V8).
- **C2:** 35 steps in 5 blocks of 7, each block one gear on its own stretch, at
  least 5 min apart; a full steady minute before each step, pressing from the
  cruise pedal position. **Full pedal** only from 1500–2000 rpm in 6th,
  1500–1800 in 7th, 1500–1600 in 8th (these end at or below about 116 km/h after
  5 s on drive B's rates); **half pedal** in 6th or 7th at 2000–2500 rpm. Hold
  7 s where legal. 8–10 min of step-free steady cruise for the shams. C2 before
  C1, or record the order. Full pedal below 2000 rpm is the low-speed
  pre-ignition region of a downsized turbo engine; worth knowing.
- **C1:** 25–30 segments of 20–30 s, at least 20 held in the cell near 2700 rpm
  (at 25 °C, 165–185 kPa is about 350–400 kg/h at 2400 rpm and 450–510 kg/h at
  3000 rpm), the rest near full throttle at 2000–3300 rpm for knee onsets.
- **Record** the fuel grade and fill, the drive mode, and the order of the parts.
- **One log per part**, named for it.
- After the rule is committed, **stage A runs blind on the 18–19 October files**
  and says how many valid steps and segments they already give; the repeat
  drive makes up the rest.

## 6. Open, and honest about it

1. **What target minus actual measures** (Bosch documentation, three readings):
   (A) the target is knock-free and the difference is the sampled cylinder's
   knock plus pre-emptive retard; (B) the target follows the cylinder-mean,
   knock-controlled angle, so retards applied to every cylinder cancel; (C) the
   target is computed from the driver's request, adding a torque-deficit term on
   full steps. The old logs cannot tell them apart. A "does not" covers only
   retards the difference can show; the channel check guards the worst case.
2. **The miss rate m is assumed, not measured** (0.45 for one retarded cylinder
   of six); the shams measure q on the day, nothing measures m. C1's persistent
   onsets report a visibility v̂, and m ≈ (1 − v̂)^n.
3. Whether the B58's pre-emptive retard follows the pedal or the boost gradient
   (if boost, it can reach L).
4. The real half-pedal load: the pedal map is unknown.
5. 42 °C is untested; the intake-temperature compensation is tested only across
   the logged range.
6. The crank-angle step check of the knock integral is still outstanding
   (`results/VALIDATION_PLAN.md` section 5c); u_num = 0 for this decision
   whatever it later finds.
7. If the knee ends untested or limited: whether the next training draws the
   knee per episode, as decision 12's first safeguard asks.

## Sources

Bosch, *ME 7.3.1H Function and Data Sheet* (2000) and *Funktionsrahmen MED17.5,
EA888* (2007), unofficial copies (files.s4wiki.com), knock-control modules
KRKE, KRRA, KRREG, KRDY, ZWOUT, MDZW; Saab WIS, Motronic 2.8.1 knock control;
Bosch patents US6513495, US6729300, US6581570; SAE 960497, 2017-01-2234,
2018-01-0213, 2015-01-0758; BMW ST1505 (B58). The old logs: `data/master_samples.csv`
and `logs/raw/` (drive B for air-mass steps and held-gear rpm rates; the steady
retard noise from the drives logging both angles). Project files:
`results/VALIDATION_PLAN.md` (R1, the label rules), `results/DAMAGE_CONSTANTS.md`
(the knee), `car_spark_boost.py`, `engine_env.py`, `plant.py`.

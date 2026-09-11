# CLAUDE.md — read this first

Project context for Claude Code. If you are an AI assistant opening this repo,
this file is the handoff: it tells you what the project claims, what is already
proven, and which mistakes have already been made so you do not repeat them.

If you are a human, read it too. It is shorter than the handbook.

---

## What this project is

A BSc graduation project, five students, King Abdulaziz University, Jeddah.

**The claim.** Not "a predictive controller for engines" — that is commercially
solved and academically crowded. The claim is a **criterion for when preview
information is worth acquiring at all**, governed by one dimensionless ratio:

> **H / τ** — the preview horizon divided by the time constant of the component
> being protected.

When τ ≫ H you are seeing thirty seconds into a problem that takes ten minutes
to develop, and preview buys nothing. When τ ≪ H the system reacts faster than
you can anticipate and preview is redundant. The useful region is where they are
comparable, and nobody has mapped it.

**The falsifiable version.** Preview value should collapse onto a single curve
when plotted against H/τ, regardless of which plant produced the point. If the
two plants do not overlap, the criterion is wrong or incomplete — and reporting
that is still a result.

---

## Hard constraint, no exceptions

**The project never writes to the vehicle's ECU.** Read-only OBD-II logging
only. No flashing, no CAN transmission, no tuning. If a task seems to require
writing to the car, it is the wrong task. Say so rather than finding a way.

---

## Current state — 11 September 2026 (after the charge-temperature correction and a document pass)

| Phase | Status |
|---|---|
| A · setup | done |
| B · match the simulator to the car | **passed** — load residual **1.4 % with zero fitted parameters** (derived k = 0.829), **1.1 % with the one fitted k** (0.837), over 22 pooled points from eight drives, 168.1 minutes, 30–74 kPa. **Read mistake 12 before quoting it:** that residual is a consistency check between two ECU channels, not a test of the cycle model. Thermal network calibrated; knock retard measured |
| C · get an agent to learn | **next.** `train.py` exists, nothing has been trained yet |
| D · baselines and the ablation | not started. This is the floor of the project |
| E · battery plant | not started. `battery.py` does not exist |
| F · the H/τ sweep | preliminary result only, from hand-written policies |
| G · writing | not started |

**What changed since 8 September.** Two more mistakes are logged and the
documents have been swept behind them.

- **Mistake 12** — the load residual cannot see the model it was said to
  validate. `eta_v`, `f_res` and the intake temperature all cancel out of it.
  It still earns three things, listed there, but "the simulator matches the car"
  is not one of them.
- **Mistake 13** — `Intake air temperature before throttle valve` is a
  compressor outlet, not a charge temperature. Correcting it moved the
  operating-point span, both values of k, and the enrichment gate. It did not
  move the premise result or the load residual, and the second of those is the
  point of mistake 12.
- **`verify_docs.py` now opens the documents.** Until 11 September it compared
  the data against constants written inside itself and never read a document at
  all, so it printed green while 55 stale figures were still shipping. See the
  closing note of mistake 11.

**What "passing project" means here:** validated simulator + agent beating two
baselines + an ablation isolating preview. That is Phase D. Everything after it
raises the ceiling, nothing after it protects the floor.

---

## The numbers that matter

Anyone can regenerate these. Do not quote a number that a script does not print.

```
python check_premise.py    baseline 829.2 · reactive 548.6 · predictive 437.6 · blinded 548.6
python validate.py         8 of 11 published quantities inside band
python test_reward.py      4 of 4 checks pass
python build_dataset.py "logs/raw/*.csv"    168.1 min, 8 drives, 22 operating points
python compare_log.py data/master_points.csv   PASS, 1.4 % load residual,
                           k derived 0.829 and zero free parameters. Read what
                           it prints, not what you hope: it compares two ECU
                           channels through the displacement and three defined
                           constants, and it does NOT measure the breathing
                           model — mistake 12
python verify_docs.py      recomputes the published figures from the shipped
                           data, then greps every tracked document and .py file
                           both for those figures and for retired ones. It
                           prints its own total; read that, do not quote a
                           count from here, because the count moves whenever a
                           figure is added
python check_map.py        spark falls with load in every row, rises with speed
                           in every column; 6 cells above the compressor ceiling
```

`build_dataset.py` used to crash on a Windows console **after** writing all three
CSVs — its summary header printed a Greek lambda, which cp1252 cannot encode, so
the run failed loudly on data that was already correct. Header is ASCII now. If
any script ever does this again, the character is the bug, not the data.

Preview advantage: reactive cuts damage 33.8 %, predictive 47.2 % — **13.4
points**.

<!-- RETIRED-OK -->
*(That first figure read 33.9 % until 11 September. (829.2 − 548.6) / 829.2 =
33.84, which rounds to 33.8 at any sensible precision; 33.9 was a typo that no
printed column supported. The predictive figure and the 13.4-point gap are
unchanged.)*

**The strongest single fact in the project:** disabling preview collapses the
predictive policy onto the reactive one *to the decimal* — 548.6 against 548.6.
The size of the effect has now changed four times, across two different engines,
two scenarios and two protection triggers. **The identity has held every single
time.** That is what makes it the load-bearing claim: whatever gap exists is
attributable to preview information and to nothing else.

---

## Thirteen mistakes already made. Do not remake them.

### 1. THE SIMULATION WAS THE WRONG ENGINE FOR THREE WEEKS

`plant.Geometry` defaulted to a generic **2.0 L inline-four**. `b58()` — the
real 3.0 L inline-six — was an opt-in override that **not one call site in the
repository ever passed**. Every `run_cycle()` call omitted the geometry
argument, so the Gymnasium environment, the premise check, the reward tests, the
H/τ sweep and ten of the eleven validation rows all simulated a 1998 cc
four-cylinder while every document said 2998 cc six.

Torque was 33 % low, air mass 33 % low, EGT 46 °C low.

Phase B escaped, because `predict()` and `map_from_airflow()` did use `b58()` —
which is exactly why the error survived: the number everyone watched, the load
residual, was computed on the right engine.

What it cost once corrected: the thermal network turned out to be uncalibrated,
the standard scenario turned out not to load the real engine, and the reward
hack from mistake 5 turned out to still be live. None of those were visible
while the plant was two thirds of its true size.

`Geometry()` and `b58()` now return the same object and every call site passes
one explicitly. **A default that silently picks a different physical system is
not a convenience, it is a trap.** If a second engine is ever added, pass it.

### 2. The pressure channel is not what it says

`Intake manifold absolute pressure` on this vehicle is a **pre-throttle sensor**.
At warm idle it reads 13.49 against an ambient of 14.23, where real manifold
pressure must be about a third of ambient. Using it as the model's load input
gives **75 % air-mass error**; inverting the air-mass channel gives **1.3 %**.

**Always use `plant.map_from_airflow()`.** `compare_log.py --map-from-log` exists
only to reproduce the failure for the thesis.

### 3. The baseline ECU was flattering us

The original guessed baseline ran a knock integral of 1.4–2.1 — detonating
continuously, which no production ECU does. About 90 % of its apparent "damage"
was a knock penalty. Recalibrating against real data dropped baseline damage
from 527 to 52.7 and cut the headline preview advantage from 30 points to 4.

Both of those sets are now void anyway — they were measured on the wrong engine
(mistake 1). What survives is the lesson: **a baseline you guessed will flatter
you, and the flattery shows up as a large headline number.**

### 4. The enrichment map has been wrong three times, most recently in its variable

| version | behaviour | verdict |
|---|---|---|
| v1, guessed | enriches from 120 kPa | far too early |
| v2, from one 42-min drive | never enriches | only 4 s of high-load data |
| v3, from two drives | stoichiometric to 207 kPa, then 0.85 | right effect, **wrong variable** |
| v4, from eight drives | function of engine speed and sustained dwell | current |

v3 was fitted to 17 seconds at high load. The two 8 September drives took that
to **178 seconds above 207 kPa**, and at that sample size the correlation
between lambda and manifold pressure is **+0.23** — weak, and pointing the
WRONG WAY for a load table: higher manifold pressure goes with *leaner*
mixture, not richer. What correlates is engine speed (−0.56), air mass flow
(−0.49), and how long the engine has been held above the 180 kPa enrichment
gate (−0.47), over the 1055 samples above 180 kPa.

<!-- RETIRED-OK -->
Both pressures in that paragraph are on the **corrected** scale of mistake 13.
The gate `ENR_LOAD` is 180 kPa and the high-load cut is 207 kPa; on the old
compressor-outlet scale those were 200 and 230 kPa, and they select the same
samples.

<!-- RETIRED-OK -->
*(This paragraph read 118 s / +0.02 / −0.60 / −0.52 / −0.38 until 9 September:
the seven-drive figures, written before `7475b5d7` arrived and never updated.
`base_lambda()`'s docstring had the current numbers all along, and
`verify_docs.py` asserts them and passes — the checker was right and the prose
was stale. Note the dwell term STRENGTHENED, −0.38 to −0.47: the correction
makes the v4 story stronger, not weaker. See mistake 11.)*

Below about 3300 rpm the car does not enrich however long the
boost is held; above 4500 rpm it runs stoichiometric for the first seconds of a
pull and enriches to 0.81 only after roughly eight seconds.

**Enrichment on this engine is component protection, not a load table.** That
matters beyond calibration accuracy: enrichment is one of the actions the agent
controls, and it is a thermal action.

**The lesson, twice over: one drive is not evidence, and a fit that reproduces
the effect can still be built on the wrong variable.** Check how many samples
support a fit, and check that the variable you fitted against actually
correlates.

### 5. The reward had a live hack — twice

**First time.** An unconstrained Dirichlet over three preference weights let the
tracking weight land near zero, and on those episodes refusing to make torque
was free — a policy that pinned boost trim to minimum scored **+0.285** against
neutral's **+0.003**. Fixed with `TRACK_W_MIN = 0.45`.

**Second time.** That fix was verified on the four-cylinder, in a scenario so
light the torque constraint never bound. On the real engine at a grade that
actually loads it, the starver scored **+0.011** against neutral's **−0.027**:
the hack was back, and a weight floor alone could not close it, because a linear
tracking penalty is always tradeable against damage at some exchange rate.

The fix is a tolerance band plus a steep hinge, `TRACK_TOL = 0.05` and
`TRACK_HINGE = 25`, sized so that **no achievable damage saving pays for a
sustained torque shortfall beyond 10 %**. Starver now scores −0.280 against
neutral's −0.004.

**Delivering the requested torque is the job, not a preference.** Run
`test_reward.py` after any reward change *and after any change to the plant or
the scenario* — a reward is only safe relative to the dynamics it scores.

### 6. Extrapolating a part-load fit into boost

A straight-line spark fit on 11 part-load points, extrapolated to 240 kPa, put
the baseline at +21° BTDC, which no turbo engine survives. The shipped map is
two pieces: the fit below ~90 kPa, and the plant's own knock limit above it.

**Do not extend a fit beyond the data that produced it.** Say where it stops.

### 7. A channel can hit its range limit and keep reporting

`Air mass flow` tops out at exactly **1020.0 kg/h** — the same number on five
separate drives, **517 samples**. That is a sensor ceiling, and on the same
samples `Air mass flow participating in combustion` reads up to 1233 kg/h.

A pinned sample under-reports air, so the manifold pressure inverted from it
comes out low and the compressor pressure ratio at that flow comes out high —
exactly at the top of the envelope, where the fit is most exposed.
`build_dataset.py` flags them (`maf_pinned`) and excludes them from `stable`.

They are **not repaired** by substituting the combustion-air channel: that is
the ECU's modelled trapped charge, a different quantity (median ratio 1.095),
and splicing two definitions puts a step in the middle of the curve.

**Before fitting anything, check whether the channel saturated.** A flat maximum
repeated across drives is the tell.

### 8. A "60 second window" was neither 60 seconds nor a window

`steady_points()` sizes its window in SAMPLES, from each drive's average rate.
On a drive whose rate is not constant, that is not a 60-second window at all.
Measured before the check existed: windows spanned **42.8 to 73.7 seconds**, and
one contained an internal hole of **3.18 s** during which nothing was recorded.

The cause is upstream. `fb988991` was logged with **655 channels selected** and
the logger could not keep up: 196 gaps larger than three times the median
interval, **222 of its 980 seconds missing entirely — 23 % of the drive never
recorded.** Its nominal 3.52 Hz is not a slow steady rate, it is a normal rate
with a quarter of the samples dropped.

That single fact explains three separate symptoms previously filed as unrelated:
the fuel-cut point with a 124 % residual, the load channel that disagreed with
its own airflow, and the drive's outlier status in every per-drive table.

A window is now rejected unless its real wall-clock span is within 20 % of
WINDOW_S and it contains no gap larger than four median intervals. Every
surviving point records `t_span` and `max_gap` so the check is auditable.

Effect on the day: 20 operating points became 17, `fb988991` contributed none,
and the pooled load residual roughly halved. **Do not quote that day's residual
as the project's number.** The dataset has since gained a drive and the charge
temperature has since been corrected (mistake 13), and the current figure is
**1.4 % derived / 1.1 % fitted over 22 points, 30–74 kPa**. Be honest about the
improvement either way — part of it was the removal of the worst drive, and the
exclusion rule was written from a measurable defect rather than from the
residual, which is the only reason it is legitimate.

**But do not read this as "fb988991 was logged wrong."** It and `f51686d7` were
deliberate reconnaissance runs made before anyone knew which parameters this car
publishes, with every channel selected on purpose. They are the reason the
21-channel set exists, and they are still answering questions — see
`logs/CHANNEL_CENSUS.md`. A census log is supposed to be unusable as driving
data; that is the trade it makes.

The rule is therefore: **census once with everything, then record the small set
for real drives.** Twenty channels log cleanly at 4.6 Hz with no dropouts.

### 9. A knock limiter that failed OPEN, and published MBT as the calibration

`check_map.py` searched spark from 0 to 45° and recorded the knock-limited
advance as `klsa`, starting at `None`. The caller then did:

```python
final = min(mbt, klsa) if klsa is not None else mbt      # WRONG
```

In a cell that knocks at **every** advance in the range, `klsa` stayed `None`
and the table printed **MBT** — the most knock-prone advance in the row — as if
it were the calibration. The 1200 rpm row read `11, 3, 21, 22`: spark falling
with load as it should, then jumping back up by 18° at 180 kPa. That jump is
the fallback firing, not physics.

A limiter that publishes the unlimited value when it cannot find a safe one is
worse than no limiter, because the output still looks like a number.

Second, smaller defect in the same function: `klsa = sp` inside the loop with no
`break` records the **last** advance seen below the threshold, not the largest
one with every advance below it also safe. The knock integral is not monotonic
in spark — it turns over near 42° as combustion finishes too early to dwell at
peak temperature — so a cell whose integral dipped back under 1.0 at extreme
advance would have published that extreme advance as safe. No cell currently
does. The search now stops at the first knocking advance, which is what "knock
limit" means.

**Third, the cells were not operating points at all.** 1200 rpm at 180 kPa is
off the compressor map: the highest MAP that closes on itself against
`boost_ceiling_kpa` is 148 kPa at that speed, 168 at 1600, 184 at 2000, 204 at
2500. Six of the 56 cells in the grid are unreachable and are now marked `--`
rather than filled with numbers from a state this engine cannot occupy.

With all three fixed the map is monotonic in both directions — spark falls with
load in every row, rises with speed in every column — and **zero reachable
cells** hit the fail-open path, so no published figure changes. Every spot check
is unchanged. The bug was never affecting a result; it was affecting whether the
table could be shown to an examiner.

**Found from a screenshot of the terminal, not from a test.** Nothing in the
repo asserted that the spark surface was monotonic. If a table is meant to have
a shape, check the shape.

### 10. `neutral_action()` was not neutral, and was outside the action space

The five actions are not the same kind of thing. Actions 0–2 are **trims** added
to what the baseline commands, so their neutral is 0. Actions 3 and 4 are
**absolute duties** — cooling fan and coolant pump — and their neutral is what
the baseline runs, not zero.

`neutral_action()` mapped all five to "zero", which put the fan **off** and the
pump at its 0.3 floor. That is not a neutral policy, it is a policy with the
cooling disabled. It also returned **−1.857** for the pump: outside the
`Box(-1, 1)` action space the env declares. `step()` clips, so it never crashed.

`test_reward.py` already knew — it carried a local `true_neutral()` and a
docstring explaining the trap — but the fix lived in the test file while the
exported function stayed wrong, and `engine_env.py`'s own `__main__` block
imported the broken one and printed its score under the label `(target: ~0)`.

That block made the second mistake its own docstring warns about too: it rolls
200 steps of a 60 s episode, and `make_grade_climb()` puts the grade at
**t = 180 s**. It never reaches the climb. `python engine_env.py` was therefore
reporting `-0.06046` next to the words "target: ~0" for a 40-second cold cruise
that contains no constraint and no reward check.

Fixed in `neutral_action()` itself, with an assert that the result is inside the
action space. `true_neutral()` is now a pass-through. The `__main__` block is
labelled a smoke test and says to run `test_reward.py` for the real figure.
`test_reward.py` still reports neutral **−0.00438**, unchanged, because it was
already using the correct vector.

**The lesson: a fix that lives in the test file is not a fix.** If a helper is
wrong, correct the helper. Everything downstream of it inherits the bug, and
the next person to call it will not have read the test's docstring.

### 11. The seven-drive figures survived in the prose after the data moved on

<!-- RETIRED-OK: this whole section is the record of what changed. -->

`7475b5d7` arrived on 8 September and took the dataset from 113 minutes over
seven drives to **168.1 minutes over eight**. The code was updated. The
documents were not, in six places:

| where | said | should say |
|---|---|---|
| CLAUDE.md mistake 4, README | 118 s above 230 kPa | **198 s** |
| CLAUDE.md mistake 4, README | corr(λ, MAP) **+0.02** | **−0.05** |
| CLAUDE.md mistake 4, README | −0.60 / −0.52 / −0.38 | **−0.56 / −0.49 / −0.47** |
| README enrichment table | n = 353 / 80 / 176 | **422 / 168 / 465** |
| CLAUDE.md limitations | seven drives, 113 min, five carrying | **eight, 168.1, six** |
| CLAUDE.md limitations | weakest cell: short dwell, n=29, 0.94 vs 1.00 | **long dwell, n=47, 0.90 vs 0.93** |

`base_lambda()`'s docstring had every one of the corrected figures already, and
`verify_docs.py` asserts them and passes. **The checker was right, the code was
right, and the prose was wrong** — which is exactly the failure verify_docs.py
was written for, recurring one level up.

Two details worth keeping:

- **The correction strengthens the result.** The dwell correlation moved from
  −0.38 to −0.47 and the 3500–4500 rpm cell went from n=29 to n=47. The stale
  numbers were understating the evidence for the model's own central variable.
  A stale number is not automatically a flattering one, which is why "it still
  supports our conclusion" is not a reason to leave it.
- **The old weakest cell was noise.** At n=29 that cell read 0.94; at n=47 it
  reads 0.99, and the genuinely weakest cell is a different one. Quoting a cell
  as "the weakest" when it holds 29 samples was reading structure into scatter.

`verify_docs.py` now greps the documents for these retired values and fails if
any reappears (`RETIRED` at the bottom of the file). **Checking that a number is
correct is not the same as checking that no document still carries the old one.**

**11 September: the same failure, one level further up.** The checker compared
each figure computed from the shipped data against a constant written inside
`verify_docs.py` itself — and then never opened a document. It printed green on
every run while **55 stale figures** were still shipping across CLAUDE.md,
README.md, `validation_table.md`, `logs/CHANNEL_SET_FINAL.md` and four `.py`
docstrings, including the dataset size, the MAF ceiling, the enrichment
correlations and the load residual. Every one of them had a matching green line
in the checker's own output.

It now scans every tracked `.md` and `.py` file, compares each figure **as the
document states it** against the value computed from the data rather than
against a constant of its own, and fails naming the file and the line. A passage
that quotes a superseded figure on purpose says so with a `RETIRED-OK` marker in
its own section, and the checker counts those separately.

**A checker that only checks itself is not a checker.** That is the lesson of
this whole pass, and it is mistake 11 recurring one level up for the second
time: the data were right, the code was right, and nothing was looking at the
prose.

**And record HOW 55 of them arrived at once, because that part will recur.** The
v17 release did not drift figure by figure. Its documents were written from an
earlier base and the corrections made in the last v16 commit were simply not in
it — `validation_table.md` came back saying 30 534 quasi-steady samples, 192
pinned MAF samples and seven drives, all of which v16 had already fixed. The
code moved forward and the prose moved backward, in the same zip.

Two rules follow, and neither is optional:

- **A release is a diff against the repository, not a fresh export of someone's
  working copy.** Before shipping an archive, diff it against the tree it will
  land on and account for every file that moves BACKWARD. A document that gets
  shorter is the tell.
- **Unzipping over a repository is not an update.** It cannot delete, so any
  tracked file the archive omits survives at its old content while everything
  around it moves on. Seven such files were carried for two releases this way
  and were deleted on 11 September — they had become a second source of truth
  that contradicted the first, and nothing referenced them.

Run `verify_docs.py` immediately after unpacking any release. It is now the
thing that would have caught this on the day it shipped.

### 12. A residual that could not see the thing it was said to validate

<!-- RETIRED-OK: this section is the record of what changed. -->

`compare_log.py` reported a load residual and the documents called it "the
simulator matches the car". **It never tested the simulator.**

`map_from_airflow()` inverts the same relation `run_cycle()` uses, so:

```
load_model = eta_v*(1-f_res)*map   and   map = m_dot*R*T / (eta_v*(1-f_res)*V*rpm/120)
    ==>  load_model = m_dot*R*T / (V*rpm/120)      eta_v and f_res CANCEL
    ==>  k*load_model = 269.6*m_dot*R / (V*rpm/120)   T cancels too
```

Measured, not argued:

| test | residual |
|---|---|
| as shipped | 1.3737 % |
| intake temperature forced to 300 K | 1.3738 % |
| `eta_v` forced to 0.50 | 1.3740 % |
| `eta_v` forced to 1.20 | 1.3739 % |
| model-free, `plant.py` never imported | **1.3740 %** |

Delete the entire breathing model and the number does not move. It is a
consistency check between two ECU channels — relative air filling against air
mass flow — through the displacement and three defined constants.

**Both the fitted 1.1 % and the derived 1.4 % have this property.** The derived
residual is the larger of the two, and that is the honest direction: one free
parameter should fit better than none. Dropping the parameter was not a
regression — it made an existing overstatement visible.

What the number DOES earn, and it is not nothing:

- It pins the meaning of BMW's `Relative air filling` channel: the DIN
  reference state, 1013 mbar and 0 °C. That was a guess before.
- **It is blind-sensitive to displacement.** Derived k on the true I6 gives
  1.4 %; forced onto the old 2.0 L inline-four it gives **48.1 %**. The fitted
  form absorbs the wrong engine into the constant and reports **1.1 % either
  way**. Had the derived form been in place in August, it would have caught
  mistake 1 on day one.
- Zero fitted parameters. That part was always true.

**The lesson: a residual computed through an inversion of the same model cannot
test that model.** Before quoting any residual as validation, perturb the
parameter it supposedly validates and check the number moves. It takes one run.

Also retract the "0.1 % agreement" language. The implied reference temperature
is **276.9 K**, not 273.15 — a real +1.4 % bias — and the fitted-vs-derived
agreement was partly luck. Say: *consistent with a 0 °C reference to within
1.4 %, and excludes 20 °C.* Bosch defines it; cite them rather than claiming a
discovery.

### 13. The charge temperature was a compressor outlet

<!-- RETIRED-OK: this section is the record of what changed. -->

`logs/CHANNEL_SET_FINAL.md` labelled `Intake air temperature before throttle
valve` as "charge temperature. Post-intercooler", and `build_dataset.py` and
`compare_log.py` fed it straight into `map_from_airflow()`.

**It reads 149 °C under boost, 163 °C peak.** No water-to-air charge cooler
with its circuit near ambient delivers 149 °C air to the ports. What it matches
is a compressor outlet: PR 2.3 at 70 % efficiency from 40 °C gives 160 °C. The
B58 carries its cooler INSIDE the intake manifold, downstream of the throttle
body, so "before throttle valve" is before the cooler.

The car settles it. **587** boosted MAF-unpinned model samples against **887**
boosted readings of the vehicle's own `Boost pressure` channel (median
226 kPa):

| charge temperature used | inverted MAP | gap |
|---|---|---|
| the raw sensor (107 °C median) | 279.5 kPa | **+23.7 %** |
| `plant.charge_temperature()` (52 °C median) | 232.7 kPa | **+3.0 %** |
| ambient + 8 K (45 °C median) | 227.5 kPa | +0.7 % |

**The >200 kPa gate on the model side is not arbitrary, and say so wherever
this table appears.** The logged side filters on `Boost pressure` > 15 psi
gauge, and (15 + 14.23) × 6.894757 = **201.5 kPa absolute**, so a 200 kPa model
gate selects the same population by construction rather than by choice.

**This file used to blame that 23.7 % on `volumetric_efficiency()` understating
breathing under boost. It was the temperature. The breathing model is cleared,
not convicted** — and there is no part-load test of it at all, because both
pressure channels on this car sit before the throttle.

`ambient + 8 K` scores +0.7 % and was **rejected**: it is a knob tuned to hit
the target, which is mistake 12 all over again. The shipped formula was written
independently for the Gymnasium environment months earlier and carries no
parameter fitted to the boost channel. 3.0 % from an independent model beats
0.7 % from a fitted one.

**What it changed.** Operating points 31–82 kPa → **30–74 kPa**. Fitted k 0.784
→ 0.837, derived 0.783 → 0.829. `ENR_LOAD` 200 → 180 kPa, because the gate is
written in manifold pressure and manifold pressure changed definition — 180 on
the new scale selects exactly the 1055 samples that 200 selected on the old one,
and every enrichment figure reproduces to the decimal without a refit.

**What it did NOT change.** The premise result — 829.2 / 548.6 / 437.6 / 548.6 —
is identical, because the simulator never used the sensor; `engine_env` always
modelled its own charge temperature. The load residual is also identical at
1.4 %, because T cancels (mistake 12). **The residual could not see the very
error being fixed.**

**Third channel on this car that is not what its name says**, after the
pre-throttle pressure sold as manifold pressure and the MAF that saturates while
still reporting. **Treat every channel name as a hypothesis.**

---

## Known limitations to state in the thesis, not fix quietly

- **The boosted inversion is now within 3 % of the car, and the old 28 % gap
  was the charge temperature, not the breathing model.** See mistake 13. What
  remains uncertain under boost is the MAF ceiling at 1020 kg/h and the logger's
  round-robin sampling, which pairs air mass with pressure taken seconds apart.
- **There is NO part-load test of `volumetric_efficiency()` against this car.**
  Both logged pressure channels sit before the throttle, so there is nothing to
  compare a modelled manifold pressure against at part load. The load residual
  cannot serve — it cancels `eta_v` entirely (mistake 12). State this plainly
  rather than letting the 1.4 % imply coverage it does not have.

- **Peak power is not a prediction.** Manifold pressure is an input.
  `plant.boost_ceiling_kpa` now bounds it to what the car was observed to do,
  but an operating line is not a compressor map — no efficiency islands, no
  speed lines, because the car has no turbo speed sensor and no pre-intercooler
  temperature.
- **Two residuals, both true, and the fitted one fits better.** Over the 22
  pooled points that survive the window checks, 30–74 kPa: **1.4 % with the
  derived k = 0.829 and zero free parameters**, **1.1 % with the fitted
  k = 0.837 and one**. Dropping the parameter makes the residual RISE, which is
  the honest direction — one free parameter should fit better than none. Quote
  the derived 1.4 % and say that it costs nothing; quote the fitted 1.1 % only
  next to the parameter it spends. And read mistake 12 first: neither number
  tests the breathing model.
- **Vehicle validation covers 30–74 kPa only.** Steady points need steady
  driving, and steady driving is light-load driving. The boosted region is
  validated against published correlations.
- **The compressor envelope is unmeasured above 0.303 kg/s corrected**, because
  that is where the MAF channel saturates. The 0.18–0.27 kg/s hole is filled;
  0.33–0.36 is still empty and no drive can fill it with this sensor.
- **Turbine τ.** `C/UA` gives 50.3 s; the step response on the correct engine
  gives 48.0 s, inside the published band. <!-- RETIRED-OK -->
  The old 39.5 s figure came from the four-cylinder and is void.
- **The knock retard is now measured, and the baseline's cap is right.**
  `Target ignition angle from torque intervention` minus `Actual ignition angle`
  gives the retard the ECU is applying. Filtered to steady gear (shifts and
  torque cuts removed, 10 896 samples): median 0°, **p99 9.8°**, retarding more
  than 1° for 22 % of the time and more than 3° for 11 %. `BaselineECU` caps its
  knock retard at 12°, which is now confirmed as the right order and slightly
  conservative rather than a strawman. **Do not use the raw channel difference**
  — unfiltered it reaches 45°, which is a gearshift torque cut, not knock.
- **The radiator is not identifiable ON THIS CAR, and the census proves it.**
  Every water-pump channel the vehicle offers is all-zero, so there is no
  coolant-flow signal and `Q = ṁ·cp·ΔT` cannot be formed. `Actual value of
  electric fan` and `Duty cycle electric fan` are also all-zero; `Setpoint
  electric fan` is live but sits at 28–31 % for a whole drive. The thermostat
  regulating 88–99 % of the time is the second reason, not the only one.
  `ua_block_oil` **is** identified (800 W/K, from the measured oil-minus-coolant
  gap) and has been changed; the radiator parameters were deliberately left
  alone. See `logs/CHANNEL_CENSUS.md`.

  A constrained fit was attempted on 8 September with 55 minutes at 45 °C
  ambient and far more excitation, and **it fails too**: R² = 0.157 with a
  negative ram coefficient. The only observable is ΔT across the radiator, and
  ΔT = Q/ṁ — both terms rise with road speed, so ΔT carries almost no
  information about UA. Assuming constant flow is not a mild approximation here.
  Stop trying; state it as a limitation.
- **Oil above 107 °C is extrapolation.** That is the hottest oil anywhere in the
  logs (`7475b5d7`); the after-filter channel `oil_filt_c` reaches 111 °C on the
  same drive. Everything the model says about oil on a sustained climb rests on
  the network's structure, not on measurement.
- **Eight drives, six with usable samples.** `3f64372e` and `f51686d7` are under
  a minute each and contain no warm running window; `fb988991` is a census log
  whose windows are all rejected for span or logger gaps (mistake 8), so it
  carries samples but contributes **zero** operating points. Quote it as "eight
  drives, 168.1 minutes, six carrying samples, 22 distinct operating points".

  <!-- RETIRED-OK -->
  This line read "seven drives, 113 minutes, five carrying samples" until
  9 September. It was written before `7475b5d7` arrived and simply never
  updated, while the current-state table at the top of this file, `verify_docs.py`
  and `build_dataset.py` all moved on. **A limitations section goes stale the
  same way a results section does, and nobody re-reads it.** `verify_docs.py`
  checks the figures in the DOCUMENTS; it does not check the prose in this file.
- **Steady points are steady for fast quantities only.** The 60 s window is
  fully settled for air, lambda, spark and manifold pressure, and reaches just
  **71 %** of a turbine thermal step (τ = 48 s). Never validate a thermal
  quantity at a steady point; drive `thermal.py` over the whole log instead.
- **Enrichment uses dwell above the 180 kPa gate as a proxy** for turbine inlet
  temperature, which this vehicle does not expose. (`ENR_LOAD` = 180 kPa on the
  corrected charge-temperature scale of mistake 13.) The weakest cell of the fit
  is 3500–4500 rpm at **long** dwell — observed 0.90 against a modelled 0.93,
  and that speed band is the thinnest of the three at n = 168 samples above the
  gate, against 422 and 465. Every one of the nine cells is within 0.027 of
  measurement.
  <!-- RETIRED-OK -->
  *(This line read "short dwell, n=29, observed 0.94, model 1.00" until
  9 September — the seven-drive
  version, in which that cell held only 29 samples and read 0.94 by chance.
  `base_lambda()`'s docstring had the corrected cell all along.)*

---

## Repository layout

```
plant.py              0-D cycle model. predict() is the shared interface.
thermal.py            3-node lumped-capacitance thermal network.
engine_env.py         Gymnasium env. BaselineECU lives here.
validate.py           Regenerates the published-figure validation table.
build_dataset.py      All drives -> data/manifest, master_points, master_samples.
extract_steady.py     Steady points from one CSV (build_dataset supersedes it).
compare_log.py        Model vs measurement at steady points.
check_map.py          MBT and knock-limited spark surfaces.
check_premise.py      Reactive vs predictive, hand-written. The premise check.
test_reward.py        Phase C sanity checks. Run after ANY reward change.
verify_docs.py        Recomputes the published figures from the shipped data,
                      then OPENS every tracked .md and .py and compares what it
                      finds written there against those figures, and against a
                      list of retired ones. Fails naming file and line. Run it
                      before quoting anything. Never edit its expected values.
train.py              SAC training. One seed per person, overnight.
generality_test.py    The H/τ experiment. H1, H2, H2b.
README.md             The public-facing summary. Tracked by verify_docs.py.
CLAUDE.md             This file. The handoff and the mistake log.
DOCUMENT_STATUS.md    Which team PDFs still carry void numbers, and why.
logs/CHANNEL_SET_FINAL.md   What is recorded, what to add, and why.
logs/CHANNEL_CENSUS.md      All 656 channels the car offers, live vs dead.
logs/raw/*.csv        Raw BimmerLink exports. Never edit these.
data/*.csv            Generated. Never edit by hand — re-run build_dataset.py.
validation_table.md   Chapter 3's evidence. Regenerate after touching the plant.
```

---

## Conventions

- **Never edit `data/` or `validation_table.md` by hand.** Regenerate them.
- **Run `verify_docs.py` before quoting a number in the thesis.** It recomputes
  the published figures from the shipped data, then opens every tracked `.md`
  and `.py` and compares what is written there against them, and against the
  list of figures this project has retired. It prints its own totals — read
  them off the run rather than quoting a count from here, because the count
  moves whenever a figure is added. It exists because figures had already
  drifted, mostly for the same reason: one computed on ONE drive and then quoted
  as if it were pooled. On 11 September it found 55 of them in one pass.
- **Never edit `logs/raw/`.** Those are measurements.
- After changing `plant.py` or `thermal.py`, re-run `validate.py` and update
  `validation_table.md` **in the same commit**.
- After changing the reward or the env, re-run `test_reward.py` and paste the
  output into the commit message.
- Change one thing, re-run, write down what happened. Two changes at once and
  you no longer know which one did it.
- Report numbers with the condition attached. "1.4 % load residual over 22
  points, 30–74 kPa" — not "the model is accurate".

---

## When a new drive CSV arrives

This is the routine, and it is the most likely reason someone opens this repo.

```bash
cp <new>.csv logs/raw/
python build_dataset.py "logs/raw/*.csv"     # rebuilds all three data files
python compare_log.py data/master_points.csv # re-scores the model
```

Then check, in this order:

1. **Did the sanity floor or the fuel-cut filter drop anything?** Both print.
2. **Did the operating-point count go up?** If the new drive added zero distinct
   points, it was not steady enough — that is a driving problem, not a code one.
3. **Which compressor flow bins are still empty?** It prints them. Only
   0.33–0.36 kg/s remains, and the MAF sensor cannot reach it.
4. **Does the load residual stay near 1.4 %?** If it jumps, the new drive covers
   a region the model has not seen, which is information, not failure.
6. **Did any window get rejected for span or a logger gap?** It prints both. A
   drive that loses every window that way was logged with too many channels
   selected — see mistake 8.
5. **Did the new drive push any channel to a flat maximum?** See mistake 6.

If the drive changes a calibration — lambda, spark, the boost ceiling — **check
how many samples support the change, and check that the variable you are fitting
against actually correlates.** See mistakes 3 and 6.

---

## Open, and honest about it

**Phase F's H2b threshold rule does not survive the correct engine.** It sets
the constraint at the 80th percentile of the unprotected trace, which assumes
the temperature spends a minority of the episode near its peak. The standard
scenario is a sustained climb: nine of its twelve minutes sit at the top, so p80
lands on the peak and the top three rows of the sweep saturate at 100 % for both
policies.

`check_premise.py` hit the same wall and solved it by anchoring the trigger to
the **damage model** instead — 1123 K, the knee of `exp((t_turb − 1123)/45)`,
above which damage stops being negligible. That is a statement about the
component rather than about one episode, and it transfers between scenarios.
**`generality_test.py` now imports the same constant** —
`engine_env.TURB_PROTECT_K` — so the two experiments cannot report different
protection limits. Until H2b's percentile rule is replaced, use the fixed-limit
H2 table: preview edge **16.5 → 18.0 → 26.0 points** as H/τ falls from 4.47 to
0.60, then the constraint stops binding entirely.

Those numbers were 0.0 / 0.1 / 0.2 at the old 930 K trigger. **Nothing about the
plant changed — only the threshold.** Report the threshold with every preview
figure; a preview advantage quoted without the limit it was measured against is
not a result.

---

## What to do next, in order

1. `python check_premise.py` — confirm the environment works at all.
2. `pip install "stable-baselines3[extra]"`, then
   `python train.py --steps 50000 --seed 0`. Expect a poor result; it running is
   the point. **About 4.6 hours on one CPU core** — measured, not guessed: the
   environment runs at 19.5 steps/s alone and 3.0 steps/s once SAC's gradient
   updates are included. The old "1.5 hours" came from a formula optimistic by
   3.6x. Plan an overnight, not an evening. Checkpoints land every 10 000 steps.
3. `python test_reward.py` before trusting any training curve.
4. Five seeds, one per team member, overnight — `--seed 0` through `--seed 4`.
   Then the same five with `--no-preview`. That is Phase D's input.
5. Phase D: three baselines, one fixed evaluation protocol of 20 episodes,
   median and interquartile range over five seeds. **Once the 20 episodes are
   fixed they never change.** Changing the test set after seeing results is the
   one mistake this project cannot recover from.

Do not start Phase E or F until D produces a table.

---

## Tone note for whoever writes the thesis

This project's advantage is that almost every number came out of running
something. Two calibrations have been corrected against measurement, one
hypothesis has been refuted and reported, and the validation table states what
it does *not* cover. Keep that. An examiner trusts a student who reports against
themselves, and punishes a validation table that implies coverage it lacks.

# MISTAKES — every mistake this project has made, in full

Moved verbatim from CLAUDE.md on 14 October 2026 (the documentation
restructure, plan v3 phase 4). CLAUDE.md keeps one rule line for each, under the
same number; this file keeps the story and the evidence. Mistake 17 stood in
CLAUDE.md's "The numbers that matter" until then; it sits between 16 and 18
here. A new mistake goes at the end with the next number, and its rule line goes
into CLAUDE.md in the same commit.

## Twenty-five mistakes already made. Do not remake them.

*(**17 and 18 are the same gearbox, found from two directions and now merged.**
17 is the mid-climb upshift, found on `sep17` when the reward gate refused to
pass. 18 is the ratio set itself — invented six-speed against the car's real
ZF 8HP51 — found on `JMF-2340550` from the specification and confirmed against
the car's own logs. **18's fix carries 17's load-aware guard deliberately**, so
the merge resolved to one rule rather than to a conflict. Both entries are kept:
they are different failures in the same component, and the second would not have
been looked for without the first.)*

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
to **208 seconds above 207 kPa**. Over the 1055 rows above 180 kPa the
correlations are: engine speed **−0.47**, air mass flow **−0.41**, dwell above
the 180 kPa gate **−0.44**, and manifold pressure **+0.11**.

**READ THOSE WITH THEIR ERROR BARS, WHICH THIS FILE USED NOT TO GIVE.**
AUDIT.md H4: 1055 is a count of FORWARD-FILLED ROWS. The exporter polls one
channel per row, so those 1055 rows contain about **39 independent air-mass
readings and 74 lambda readings** — a 15–30× inflation. The standard error on a
correlation at that sample size is about **±0.17**.

Two things follow, and the second is a correction to this entry's own argument:

- **The v4 conclusion still stands.** −0.56 and −0.49 are three standard errors
  from zero. Engine speed and air mass really do carry the signal.
- **The "+0.23 points the WRONG WAY" argument does NOT stand**, and it used to
  be stated here as though it did. +0.23 is 1.4 σ — indistinguishable from zero,
  and the reviewer's decimation across poll phases put it anywhere between
  −0.01 and +0.34. The honest statement is that **manifold pressure carries no
  detectable signal**, which is still enough to reject a load table. It is not
  evidence that load points the other way.

<!-- RETIRED-OK -->
*(The dwell figure was **−0.47** until 16 September, computed on a dwell axis
built from row counts over an assumed 4.6 Hz when the drives log at 4.34–6.63 Hz.
Summed from the timestamps it is −0.41. AUDIT.md H3.)*

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

`Air mass flow` tops out at exactly **1020.0 kg/h** — the same number on seven
separate drives, **568 samples** (six and 547 until drive B's last roll-on). That is a sensor ceiling, and on the same
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
**1.4 % derived / 1.1 % fitted over 26 points, 30–75 kPa**. Be honest about the
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
`test_reward.py` still reports neutral inside the ±0.05 band, because it was
already using the correct vector.

**The lesson: a fix that lives in the test file is not a fix.** If a helper is
wrong, correct the helper. Everything downstream of it inherits the bug, and
the next person to call it will not have read the test's docstring.

**19 September: the fix was right and the SENTENCE EXPLAINING IT was backwards.**
The corrected `neutral_action()` carried a caveat saying the baseline's fan
"holds 1.0 once the engine is hot, which is the part of the episode the
constraint binds in — exactly neutral during the climb, slightly over-cooled
during the first three minutes of flat running." Measured on the locked
scenario over the 720 s episode:

| fan duty | whole episode | during the climb |
|---|---|---|
| 0.0 | 26.8 % | 2.6 % |
| 0.4 | 73.2 % | **97.4 %** |
| 1.0 | **0.0 %** | **0.0 %** |

**The baseline fan never reaches 1.0 at all**, because coolant peaks at 94.2 °C
here and the 1.0 rung needs 98.9 °C. So the action is over-cooled *during the
climb* — the exact window the caveat claimed it was neutral in — and neutral
during the flat running it claimed was over-cooled. **Both halves inverted.**

**The constant was NOT changed, and that is deliberate.** The fan acts on the
coolant loop (700 W/K of a 1925 W/K peak UA) while the turbine housing is
gas-heated, so the protected component barely sees it; `test_reward.py`
measures the whole effect and neutral still scores −0.00038 against a ±0.05
band. Moving a constant inside a locked scenario to make a docstring true would
be tuning for prose. **The sentence was what was wrong, so the sentence is what
changed.**

Mistake 11's shape, inside mistake 10's own function: the code was right, the
number was right, and nothing was checking the prose beside them.

### 11. The seven-drive figures survived in the prose after the data moved on

<!-- RETIRED-OK: section 113, 168.1, 5, 7, 8, 30534 -- this whole entry is the record of what changed. -->

`7475b5d7` arrived on 8 September and took the dataset from 113 minutes over
seven drives to **168.1 minutes over eight**. The code was updated. The
documents were not, in six places:

| where | said | should say |
|---|---|---|
| CLAUDE.md mistake 4, README | 118 s above 230 kPa | **198 s** |
| CLAUDE.md mistake 4, README | corr(λ, MAP) **+0.02** | **−0.05** |
| CLAUDE.md mistake 4, README | −0.60 / −0.52 / −0.38 | **−0.47 / −0.41 / −0.44** |
| README enrichment table | n = 353 / 80 / 176 | **441 / 235 / 665** |
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

**14 September: a third recurrence, and it names the two holes the checker
still has.** `pull01` took the manifest from eight drives and 168.1 minutes to
**nine and 175.5**. Seventeen lines were swept to the new figure. **Five were
not**, and they escaped by two different routes, both worth knowing:

- **Three escaped the regex**, because the patterns are anchored. The
  dataset-size pattern needs the words *pooled*, *dataset*, *manifest* or a
  drive count within thirty characters of the figure, so
  `REFERENCES.md`'s "168.1 minutes of OBD-II logs from our own car" and
  `CHECKPOINT.md`'s "30–75 kPa, 168.1 min." matched nothing. An anchored
  pattern is the right trade — a loose one reported the thermal fit's "three
  drives (80 minutes)" as a wrong total — but it means **a figure written in
  an unusual sentence is invisible to the checker.**
- **Two escaped inside a `RETIRED-OK` paragraph.** The marker exempts its
  whole paragraph, and in `validate.py` and `build_dataset.py` a **live**
  claim about the current dataset sat in the same paragraph as the retired
  figure the marker was there for. The exemption is a blunt instrument: it
  cannot tell the historical sentence from the current one beside it.

**And nothing in `RETIRED` was guarding 168.1 at all** — the seven-drive entry
still named "eight drives, 168.1 minutes" as the value to use instead, so the
list was pointing at a figure that had itself been superseded. A retired-value
list has to be swept when the value that replaced it moves on.

Fixed: the five lines carry the current figure, the seven-drive entry points
at ten drives, and `168.1` is now a retired pattern in its own right. The
pattern deliberately does **not** match "eight drives" on its own, because
the enrichment map and the compressor fit genuinely rest on eight drives of
samples: `pull01` adds 7.5 minutes and **zero** samples, so every figure fitted
to samples is unchanged and those sentences are still true.

**The rule that comes out of three recurrences:** when a figure changes,
grep the whole tree for the OLD value yourself and read every hit, then add
it to `RETIRED`. Do not trust a green run to prove the sweep was complete —
a green run proves only that the patterns that exist found nothing.

<!-- RETIRED-OK: 11.7 -->
**22 September: the fourth recurrence, and it was in the GUARD, found by the
guard's own acceptance test.** `AUDIT2.md` fix 3 swept the KNOWN STALE ledger
from 187 mentions to zero (commit `3f4627d`), and emptying it was right. But
`drift_test.py` then fell from **16 of 16 to 14 of 16**, and one of the two was
a real hole: the ledger had been counting the void `+11.7` margin in the files
that quote it, and that COUNT was the only thing catching an edit of `+11.7`
into `+13.7`. Nobody had written that down. **A protection that exists only as
a side effect of another mechanism disappears when that mechanism is retired.**
It is now an explicit check, `PINNED_HISTORY`, and the test is back at 16 of 16.

The same sweep found two more holes in the guard that had been there since
fix 2, both worth knowing when you write a marker:

- **HTML-comment markers were invisible.** The tag stripper deleted
  `<!-- RETIRED-OK ... -->` with every other tag, so every marker in
  `presentation/*.html` was decorative. They survive stripping now.
- **A marker's explanation was read as figures.** `RETIRED-OK: 900.9 -- the
  baseline at dt 0.2, not the protocol step of dt 1.0` also excused 0.2 and
  1.0 in its scope. Figures now come from the list before the first ` -- `.

And one forward-update of exactly this entry's shape: commit `6e40cd8` changed
"all nine drives" to "all ten drives" in mistake 14 and `app/alerts.py` when
drive10 arrived, **without re-running the measurement** the sentence described.
Restored. **After retiring or reworking anything in the guard, run
`drift_test.py` before committing** — it is the only thing that checks the
checker.

### 12. A residual that could not see the thing it was said to validate

<!-- RETIRED-OK: section -- this entry is the record of what changed. -->

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

<!-- RETIRED-OK: section -- this entry is the record of what changed. -->

`logs/CHANNEL_SET_FINAL.md` labelled `Intake air temperature before throttle
valve` as "charge temperature. Post-intercooler", and `build_dataset.py` and
`compare_log.py` fed it straight into `map_from_airflow()`.

**It reads 149 °C under boost, 163 °C peak.** No water-to-air charge cooler
with its circuit near ambient delivers 149 °C air to the ports. What it matches
is a compressor outlet: PR 2.3 at 70 % efficiency from 40 °C gives 160 °C. The
B58 carries its cooler INSIDE the intake manifold, downstream of the throttle
body, so "before throttle valve" is before the cooler.

<!-- RETIRED-OK: 587, 887 -->
The car settles it. **587** boosted MAF-unpinned model samples against **887**
boosted readings of the vehicle's own `Boost pressure` channel (median
226 kPa) — the 10 September counts. *(With the drives since added, the same
comparison rests on 762 model samples against 1097 logged readings, and the
shipped formula's gap is still +1.9 % — `verify_docs.py`, CHARGE TEMPERATURE.)*

| charge temperature used | inverted MAP | gap |
|---|---|---|
| the raw sensor (117 °C median) | 279.5 kPa | **+23.7 %** |
| `plant.charge_temperature()` (52 °C median) | 232.7 kPa | **+1.9 %** |
| ambient + 8 K (45 °C median) | 227.5 kPa | +0.7 % |

*(28 September: the 117 °C in the first row does not reproduce. The 587
samples whose inversion gives the 279.5 kPa read 106.8 °C at the median, while
the 279.5 kPa itself reproduces exactly (`plot_sim_vs_car.py`, chart 2). Which
population the 117 °C describes is not recorded, so treat it as unverified.
`plant.charge_temperature()`'s docstring carries the same row.)*

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
parameter fitted to the boost channel. 1.9 % from an independent model beats
0.7 % from a fitted one.

<!-- RETIRED-OK: 0.784, 0.837, 0.783 -->
**What it changed.** Operating points 31–82 kPa → **30–75 kPa**. Fitted k 0.784
→ 0.837, derived 0.783 → 0.831. `ENR_LOAD` 200 → 180 kPa, because the gate is
written in manifold pressure and manifold pressure changed definition — 180 on
the new scale selects exactly the 1055 samples that 200 selected on the old one,
and every enrichment figure reproduces to the decimal without a refit. *(The
fitted k has since moved on to 0.839; `compare_log.py data/master_points.csv`
prints the current value.)*

**What it did NOT change.** The premise result — 829.2 / 548.6 / 437.6 / 548.6 —
*(all four since VOID, AUDIT.md C1/C3; the point here is only that the sensor
change did not move them)* is identical, because the simulator never used the sensor; `engine_env` always
modelled its own charge temperature. The load residual is also identical at
1.4 %, because T cancels (mistake 12). **The residual could not see the very
error being fixed.**

**Third channel on this car that is not what its name says**, after the
pre-throttle pressure sold as manifold pressure and the MAF that saturates while
still reporting. **Treat every channel name as a hypothesis.**

---

### 13b. CONFIRMED 13 September — the sensor is a LAGGED compressor outlet

> **Restored 16 September.** This entry shipped in the v19 release archive but
> never existed on the branch, because the branch did not have `pull01` — and
> the merge that brought `pull01` in took the branch's `CLAUDE.md`, which
> dropped it. It is load-bearing: `app/reader.py`'s entire channel budget is
> built on the 7.5 s / 1.45 s measurement below, and the app cites this entry
> by number. **Mistake 16, in miniature: the archive held something real and
> the merge nearly threw it away.**


`pull01`, a purpose-built **7-channel** drive, settled mistake 13 and explained
why the first attempt at settling it failed.

**The logging rule was confirmed to the decimal.** The logger polls one channel
per row, round-robin, so per-channel rate is (row rate ÷ channels):

| drive | channels | predicted | measured |
|---|---|---|---|
| `7475b5d7` | 26 | — | 7.5 s |
| **`pull01`** | **7** | **1.43 s** | **1.45 s** |

**5.2x faster per channel**, from logging fewer of them. Halving the channel
count really does roughly halve the interval.

**And that resolution is what made the physics visible.** Testing whether
`Intake air temperature before throttle valve` is a compressor outlet:

    T_out = T_inlet * (1 + (PR^0.2857 - 1) / eta)

| test | correlation |
|---|---|
| raw, on the old 26-channel data | +0.47 |
| raw, on `pull01` | +0.35 |
| **`pull01`, with a first-order thermal lag applied** | **+0.95** |

Best fit: **eta ~= 0.55-0.65, sensor time constant ~= 10 s**, RMSE 13.8 K, with
a residual **+11.7 K** offset consistent with heat soak in the charge pipe.

**The hypothesis was right and the earlier test was simply too slow to see it.**
A sensor with a 10 s time constant cannot be characterised by samples taken
7.5 s apart — there are barely two points per pull. At 1.45 s there are four or
five, and the lag becomes fittable. The weak +0.35/+0.47 correlations were an
artefact of the sampling, not evidence against the hypothesis.

This also explains the raw readings: the sensor peaks at 150 C on `pull01` while
the un-lagged compressor-outlet prediction at peak boost is around 200 C. It is
not reading a lower temperature — it is failing to keep up with a rising one.

**`pull01` contributes ZERO samples and ZERO operating points, by design.** It
carries no coolant channel, so the warm-sample filter excludes it outright. A
purpose-built drive answers one question and cannot contaminate a calibration it
was not designed for. That is the argument for small sets, not just the rate.

**What this does NOT change.** `charge_temperature()` is unaffected — the charge
temperature is still post-intercooler and still unmeasured on this car. This
confirms what `iat_pre` is NOT, which is what mistake 13 was about.

---

### 14. THE APP'S FAULT DETECTOR WAS MEASURING THE THROTTLE — mistake 2, a third time

Found 14 September, while tuning what looked like an over-sensitive threshold.

`app/alerts.py` compared the manifold pressure **inverted from measured air
mass** against the pressure read from the vehicle's own `Boost pressure`
channel, and called a disagreement above 15 % a fault. On `7475b5d7` it raised
55 events, which reads like a threshold that needs raising.

It was not a threshold problem. The firing condition was true for **13669 of
14278 samples — 95.7 % of the drive, median −52 %.** It produced only 55 events
because a 60 s cooldown was collapsing a continuous, systematic disagreement
into a handful of discrete-looking ones. **A detector that fires on 96 % of
normal driving is not sensitive, it is measuring something else.**

What it was measuring: `Boost pressure` on this car sits **BEFORE THE THROTTLE**,
exactly like `Intake manifold absolute pressure` in mistake 2. At part throttle
the pressure before the plate and the pressure after it are different physical
quantities, and the throttle is the thing making them different. Binned by the
logged throttle angle:

| throttle | n | median disagreement |
|---|---|---|
| 0–25 % | 13431 | **−52.5 %** |
| 25–50 % | 222 | −61.1 % |
| 90–100 % | 236 | −33.1 % |

and binned by the pre-throttle pressure itself, the disagreement collapses
exactly where the throttle stops restricting:

| logged pre-throttle | n | median |
|---|---|---|
| 90–110 kPa | 8538 | −56.7 % |
| 110–130 kPa | 4782 | −44.0 % |
| **200–250 kPa** | **157** | **+7.7 %** |

That −52 % is the same 44–52 % this file's limitations section already records
for the 22 steady points. **It was never a fault and it was never news.**

**The fix is three validity gates, and the threshold was not where it went.**

1. **Wide-open throttle only**, expressed as a pressure ratio so it needs no
   extra channel and no extra budget: `logged / ambient >= 1.8`. Pooled over all
   nine drives of 14 September, MAF-unpinned *(this read "ten" from 19 Sep:
   commit `6e40cd8` forward-updated the count when drive10 arrived without
   re-running the measurement — mistake 11's shape; drive10 is not in these
   figures)*, the disagreement at that gate has a median of
   **+6.5 %**, and per drive **+7.7 / +6.8 / +3.6 / +1.2 %** — consistent with
   the **+1.9 %** that `plant.charge_temperature()` already records for this
   same comparison under boost.
2. **MAF not pinned** at its 1020 kg/h ceiling (mistake 7).
3. **Persistence counted in DISTINCT READINGS**, over a window spanning at least
   one measured 6.0 s channel refresh.

**Two things found on the way that are worth more than the fix.**

- **The suspected cause was the wrong one, and backwards.** The obvious
  hypothesis was MAF saturation (mistake 7). Pinned samples turn out to be the
  ones that **AGREE** — median −5.4 % against −52.5 % for the rest — because
  pinning only happens at wide-open throttle, which is the only place the
  comparison was ever valid. Excluding them is still right, for the separate
  reason that they are biased low by a known sensor limit. They were never the
  cause of the 55 events.
- **A forward-filled stream is not a stream of measurements.** The exporter
  writes every channel on every 0.15 s row and each one only changes when it is
  actually polled. The worst window found on a healthy drive, `cb67b01f` at
  t = 825 s, was **21 consecutive samples all reading +40.9 %, spanning 4.8 s,
  containing exactly ONE air-mass reading and ONE boost reading.** A median over
  those 21 samples is that one measurement, counted 21 times. Requiring the
  window to span a refresh interval is what makes persistence mean persistence:

  | span required | windows | worst healthy median |
  |---|---|---|
  | ≥ 0 s | 89 | 34.5 % |
  | ≥ 4 s | 74 | 16.6 % |
  | **≥ 6 s** | **45** | **13.6 %** |
  | ≥ 12 s | 16 | 6.9 % |

**A steadiness gate was tried and is actively wrong.** Requiring a *settled*
operating point selects cruise at a closed throttle with the compressor still
making pressure behind it — a genuine and blameless −60 % — and rejects the
wide-open pulls, which are the only valid samples and are transient by nature.
**On a road car the only place this comparison means anything is inherently
unsteady.**

**The threshold moved 15 % → 25 %, and the reason is a measurement.** The old
15 % was justified in the docstring by "the model's validated load residual is
1.4 %". Both halves of that were wrong: per **mistake 12** the 1.4 % residual
cannot bound this or any other comparison involving the breathing model, and
measured directly under the gates above, the worst windowed median on nine
healthy drives is **13.6 %** — so 15 % carried 1.4 points of margin. 25 % carries
11. **The gates removed the 55 events, not the threshold**; with the gates in
place and the threshold left at 15 %, `7475b5d7` still raises zero.

**The lesson: before tuning a detector, check that it is comparing two
measurements of the same physical quantity.** Three of this car's channels have
now been misread the same way.

### 15. THE APP REPORTED A TEMPERATURE ITS OWN PHYSICS SAID WAS IMPOSSIBLE

Same session, the neighbouring file. Two defects, one cause.

**First, the warm-up was a timer, and the timer used the wrong τ.**
`app/estimator.py` seeded the thermal state on connection and declared the seed
forgotten after a fixed `WARMUP_S = 145`, quoted as three turbine time constants
at τ = 48 s. But τ for the turbine node is `c_turb / (ua_gas_turb·ṁ_exh +
ua_turb_amb)`, so it depends on exhaust flow:

| condition | exhaust flow, g/s | UA, W/K | τ |
|---|---|---|---|
| hard climb | ~112 | 119 | **50 s** |
| cruise | ~24 | 40 | **151 s** |
| idle | ~8 | 25 | **239 s** |

*(Units live in the header on purpose. With the unit written next to each
number instead, the first row tripped `verify_docs.py`'s pattern for the hardest
sustained FUEL flow — a different quantity, an order of magnitude smaller, and
exactly the collision that file's docstring warns about.)*

**48 s is the LOADED time constant.** Sit in traffic and the seed is still
largely intact at 145 s, and the app would have been calling the estimate
trustworthy while it was mostly assumption. Measured on the replay of
`7475b5d7`, the seed actually takes **461 s** to be forgotten, not 145; on a
synthetic light-load stream **576 s** against **110 s** loaded.

**Second, and worse, the seed was outside its own physics.** The nominal seed
was a flat 500 °C, chosen "because we have nothing at all to go on". That was
not true — engine speed, air mass and coolant are all visible, so the operating
point is visible, and an operating point has a settled turbine temperature. And
the flat 500 °C was not merely imprecise: on `pull01` the housing at the seed
instant is bounded by ambient and the model's own exhaust temperature, which is
**35–193 °C**. The app was displaying a number **300 K above what its own model
said was possible**, and displaying it as the headline figure.

**The fix replaces the timer with a measured bound.** Three copies of the
thermal network are integrated with identical inputs, differing only in where
the turbine started — one at ambient, one at the model's own EGT. The width
between them is what the seed is still worth, it narrows at whatever rate the
driving allows, and thermal alerts stay suppressed until it is inside 25 K. The
nominal is now the steady state the current operating point implies — the fixed
point of the very equation `ThermalNetwork.step` integrates, so no new
parameter — clamped into the bracket so **the reported value can never sit
outside its own error bar**.

<!-- RETIRED-OK: 593.7, 673.5, 885.2, 884.9 -->
**What it cost, and be honest about it in the thesis.** `pull01`'s peak
estimated turbine reads **593.7 °C** where the old code said 673.5 °C, because
that drive is short and its peak falls inside the warm-up. `7475b5d7` moved
**885.2 → 884.9 °C**, essentially nothing, because a 40-minute drive forgets its
seed long before its peak. **The long drive was never wrong; the short one was,
and only the bound could tell them apart.**

**The limit the bound does NOT cover, and it is real.** The bracket holds under
steady operation. Connect within a few tens of seconds of lifting off a hard
pull and the housing can be hotter than the gas now flowing through it, because
the gas cooled first — so the upper bound will be too low. No channel on this
car would catch that. A cold start has the opposite and happier property:
coolant, ambient and exhaust are all low together, the bracket is narrow from
the first sample, and the estimate is trustworthy almost immediately.

**The lesson: a convergence claim needs a convergence measurement.** "Three time
constants" is a statement about a τ you have to name, and naming the wrong one
is invisible until something checks.

### 16. A RELEASE ARCHIVE TRIED TO DRAG THE TREE BACKWARDS

<!-- RETIRED-OK: section 113, 7 -->
*(This entry quotes the retired figures on purpose — naming them IS the
entry. The marker above is what tells `verify_docs.py` so, and it is the
same mechanism mistake 13 uses for the same reason.)*

Found 14 September, merging the v19 archive into a branch that had moved on.

This file already warns that documents *missing* from a release archive get left
behind while everything around them moves on. **The opposite is the worse
failure and it happened here.** The v19 archive was an OLDER snapshot of almost
everything, carrying one genuinely new thing — `app/` — so unzipping it over the
tree would have silently reverted a fortnight of document work:

- its `validation_table.md` was **335 lines against the branch's 429**, and
  contained "seven drives, 113 minutes", retired long ago;
- its `CLAUDE.md` re-introduced **33.9 %**, **"192 samples"** and **1.163**, all
  three of which the branch already had right;
- its `validate.py` dropped explanatory docstrings the branch still carried.

**All three of those figures had already been corrected once, and came back**,
because nothing was asserting them. That is mistake 11 recurring one level up:
a correction that is not guarded by a check has a short half-life. They are now
in `verify_docs.RETIRED`, and adding the guard immediately found a **fourth**
occurrence of 1.163 in `build_dataset.py` that a careful manual pass had missed.

**The rule: a release archive is a snapshot, not an authority.** Diff it against
the tree before applying it, take only what is genuinely new, and re-run
`verify_docs.py` afterwards. Never unzip one over a live branch.

**The same session also caught `verify_docs.py` crashing while reporting.** Its
new document scanner echoes the offending line back, `CHECKPOINT.md` line 54
contains a tick emoji, and on a cp1252 console that raised `UnicodeEncodeError`
and took the whole run down — **after every check had already been computed
correctly**. That is the `build_dataset.py` lambda bug for the third time, in
the one script whose entire job is to be trusted. **A checker that dies while
reporting is worse than one that stays quiet, because the traceback looks like a
data problem and hides the real finding underneath it.** Output is now encoded
defensively.

<!-- RETIRED-OK: 547, 6 -- the warm-filtered count of 16 September -->
<!-- RETIRED-OK: 517 -->
**And a third defect in the same scanner, from the same merge.** Its check
"drives showing that exact ceiling" counted raw files in `logs/raw/`, while the
"547 samples" check sitting beside it counted the warm-filtered dataset. `pull01`
hits the 1020 kg/h ceiling 56 times in its raw log, so the drive count became 6
while the sample count stayed 517 across 5. **Both numbers were true and the
sentence built from them was not.** Both halves now count the same population.
For the record, as written on 16 September (commit `4905498`): **573 pinned samples across 7 of the 10 raw
logs; 517 across 5 once the warm filter has run.** *(Since superseded for the
warm-filtered population: `verify_docs.py` now computes 547 samples across 6
drives.)*


#### 17. THE GEARBOX UPSHIFTED MID-CLIMB, AND ONLY A HARDER SCENARIO COULD SHOW IT

Found 18 September, by the reward gate refusing to pass. **This is the third
defect in this project that was invisible until the load became real**, after the
wrong engine (mistake 1) and the reward hack (mistake 5), and it has the same
shape: a simplification that is harmless at part load and wrong exactly where the
project does its work.

**What happened.** The scenario moved to 12 % at 130 km/h and `test_reward.py`
failed its first check: the neutral action -- which by construction reproduces
the baseline ECU -- scored **-0.124** against a +/-0.05 band. The script's own
advice is to raise the tracking weight. **That advice was written for a different
failure and following it would have made this one worse.**

**The real cause, measured on the shipped trace.** Over the whole climb the
baseline demanded **381 Nm and delivered 359** -- short by **5.7 %, on 519 of
519 samples**, just past `TRACK_TOL` = 5 %, so the hinge fired every single step.
The baseline could not hold the demand. No reward weight fixes a scenario asking
for torque the vehicle cannot make.

**Why it could not.** `Vehicle.gear_for` selected on ROAD SPEED ALONE:

| km/h | gear | demand Nm | shortfall |
|---|---|---|---|
| 110 | 5th (0.82) | 297 | 0.0 % |
| **115** | **6th (0.68)** | **364** | **7.8 %** |

**A 4 % step in road speed moved the torque demand 23 %.** That is the ratio
dropping at the 115 km/h rung of a fixed speed ladder: **the model upshifted into
top gear halfway up a 12 % grade**, which no automatic transmission does, and
then asked the engine for the whole hill at 2137 rpm.

**The fix is a load term, and it is guarded against being a convenience.**
`gear_for` now takes the tractive force and hands back a gear while the required
torque exceeds `SHIFT_LOAD` x `PEAK_TORQUE_NM` -- a 25 % torque reserve, declared
ASSUMED -- subject to the lower gear not hitting the limiter. **Every operating
point the environment had already been used at keeps the gear it had**: 110 km/h
flat, 110 at 12 %, 110 at 16 %, 90 flat and 50 km/h town are all unchanged, so
the old scenario is bit-identical. Only 130 and 150 km/h on the 12 % grade
downshift, 381 Nm -> 316 Nm at 2913 rpm.

**What it cost, stated rather than buried.** The peak turbine at 130 km/h falls
**899.4 -> 857.0 C** -- the downshift raises rpm and lowers load per cycle, so
the EGT drops. The scenario still binds, by **7 K instead of 49**, and protection
still does real work: current-grade cuts damage **29.7 %**. The gate passes at
**+0.00048**. But the starver's margin narrowed from -2.16 to -0.10, because an
engine that meets its demand easily makes refusing to work a smaller crime --
**that is the number to watch first if a trained agent turns lazy.**

**A KNOWN LIMIT OF THE FIX, because it is a flat ceiling on an rpm-dependent
quantity.** 500 Nm is peak torque, not torque at every speed, so 115-125 km/h
still over-ask: they sit at 364-375 Nm, under the ceiling, while the engine
cannot deliver that at 2137 rpm. Those speeds are not scenarios and the ceiling
was NOT lowered to smooth the table -- doing so would have moved 16 % at 110 km/h,
which is the team's third scenario. Fixing it properly needs an rpm-dependent
torque limit, which is a larger change.

**The lesson, and it is mistake 5's written down one level out:** a reward is
only safe relative to the dynamics it scores, and **a plant simplification is
only safe relative to the operating points it has been used at.** Both go stale
the moment the scenario gets harder. Run `test_reward.py` after a scenario
change, read WHICH check failed, and diagnose it before taking the advice the
failure prints.

### 18. `Actual gear` CLAMPS AT 6 ON AN EIGHT-SPEED — a fourth misread channel

Found 19 September 2026, while fitting the real gearbox. It is mistakes 2, 7 and
13 in one channel: a name that is not what it says, **and** a range limit that
keeps reporting past it.

The vehicle model ran a generic six-speed with invented ratios until today. The
car has a **ZF 8HP51**, an eight-speed torque-converter automatic, and Toyota
publishes every ratio (REFERENCES.md section 2b). Fitting it raised an obvious
check: the logs carry `Actual gear`, so compare.

**`Actual gear` never exceeds 6, on any drive.** Across 45 606 moving samples
from eight drives it reports 1 to 6 and nothing above. Taken at face value that
says the car is the six-speed manual.

**It is not.** Engine speed and road speed give the overall ratio the car is
actually running, and within the samples the channel labels "gear 6" there are
**three sharp clusters**:

| overall ratio | samples | what it is |
|---|---|---|
| ~2.016 | 19 290 (59.3 %) | **8th** (0.640 x 3.150) |
| ~2.589 | 5 406 (16.6 %) | **7th** (0.822 x 3.150) |
| ~3.15 | 4 833 (14.9 %) | 6th (1.000 x 3.150) |

The channel reports the true gear for 1st to 6th and then **saturates**, calling
7th and 8th "6" as well. Three quarters of the samples it labels top gear are
not in top gear.

**What it would have cost.** Anything scheduled on that channel — a gear-aware
filter, a shift-transient exclusion, a per-gear table — silently pools three
ratios spanning 2.016 to 3.15, a **56 % spread**, under one label. The knock
retard figure in the limitations section is filtered "to steady gear" using it.
That filter still works, because it only asks whether the gear CHANGED, and a
clamped channel still changes at every shift below 6th; but it cannot see a 6-7
or 7-8 shift at all, so the figure includes shift transients it was meant to
remove. **Re-derive it from the inferred gear before quoting the p99 again.**

**The fix is not to repair the channel but to stop needing it.** Overall ratio
from rpm and road speed recovers the true gear directly, and it validates the
ratio set at the same time: **86.7 % of 79 105 moving samples land within 4 % of
one of the eight published ratios.** That is a better measurement than the
channel would have been even if it worked.

**Fourth channel on this car that is not what its name says**, after the
pre-throttle pressure sold as manifold pressure, the MAF that saturates while
still reporting, and the compressor outlet sold as charge temperature. The rule
from mistake 13 now has four instances behind it: **treat every channel name as
a hypothesis, and check the range as well as the meaning.**

*(The tell was available without any of this analysis: the car is an
eight-speed and the channel's maximum is 6. A channel whose maximum equals a
round number that is ALSO a plausible count is the easiest kind of saturation to
miss -- mistake 7's 1020.0 kg/h at least looked like a sensor limit.)*
---

### 19. A FIX THAT READ A KEY NOBODY WROTE — AUDIT.md M12, never working

Found 28 September 2026. M12 asked `generality_test.py` to take the H/τ axis from
the climb's own exhaust flow instead of an assumed 112.5 g/s. The "fix" read
`info.get("mdot")` — a key the environment has never emitted — so the list it
averaged was always empty, and the script fell back to exactly the 112.5 g/s it
was meant to replace, printing "was an assumed 112.5" beside the assumed value.
`AUDIT_FIXES.md` recorded M12 as FIXED for twelve days.

**It is mistake 9's shape — a check that fails OPEN still prints a number.**
`.get(key, default)` on data you produced yourself is a place a bug hides: the
environment now reports `mdot_exh`, and the script indexes it, so a missing key
is an error. **After fixing something, look at what the fix PRINTS and ask
whether the number could have come from the fallback.**

### 20. THE OIL NODE HAD THE WRONG STRUCTURE, AND NO PARAMETER COULD FIX IT

Found 28 September 2026. For three weeks the thermal network heated the oil with
a fixed 5 % of fuel energy and cooled it through a constant 60 W/K, and every
attempt to match the car — halving the share, doubling the capacity, fitting
both on the light-load drives — traded one drive against another ("the drives
pull opposite ways"). They pulled opposite ways because the STRUCTURE was
wrong: tabulated minute by minute, the car runs its oil 11–15 K over coolant at
3700–4800 rpm and 70–100 km/h on moderate fuel, and 2–3 K under coolant at
2600 rpm and 130–140 km/h. Oil heat follows engine speed; the sump is cooled by
road speed. With that structure one parameter set fits 7 drives and
predicts the held-out one (drive10 oil 7.55 → 3.9 K).

**When fits of the same model to different data disagree, suspect the model's
form before its numbers. Tabulate the raw channels against the conditions
first; a parameter search cannot find a mechanism the equation does not have.**

### 21. A DRIVE PLANNED WITHOUT THE CHANNEL EVERY HEAT FLOW NEEDS

Drive B (28 September) was logged exactly to plan — seven channels, 1.05 s per
channel, 41 roll-ons — and the plan had left out `Ambient temperature`. Every
corrected flow, every charge temperature and every heat flow in the thermal
network is referenced to it. `build_dataset.py` then filled the gap SILENTLY
with 25 °C, and the charge-temperature check swallowed drive B's rows and moved
from +1.9 % to +1.0 % on an assumption.

Fixed three ways: the fallback is now a value taken from our own afternoon logs
and every such row is flagged `t_amb_assumed`; the charge-temperature check
excludes flagged rows; and **every channel list in `logs/DRIVE_PLAN.md` now
carries `Ambient temperature`.** A purpose-built drive answers its question only
if it also logs what the question is measured against.

### 22. TWO CLAIMS WRITTEN FROM A LOOK AT A FIGURE, NOT FROM A MEASUREMENT

Found 29 September 2026, while putting the 28 September results on the phone
page, where every figure has to come from a token. Two sentences had shipped in
five documents without a number behind them:

- **"The derived boost ceiling matches drive B at 1400–2400 rpm."** It was read
  off `fig22` as "the model's line sits inside the car's scatter". Inside the
  range is the wrong test for a CEILING: a ceiling is judged against the top of
  what the car did. Against the highest reading per 200 rpm band it is 9–20 %
  LOW at 1600–2000 rpm (193 kPa reached at 1800–2000 rpm where the model allows
  155). Re-pairing engine speed to each boost reading's own moment moved the
  points ~55 rpm and did not change that.
- **"About 6 K of row 8's miss is the coolant."** Never computed. Replaying
  drive10 with the block pinned to the measured coolant (`model_vs_data.
  row8_split`) gives 4.6 K of a 12.0 K miss; the larger share, 7.3 K, is the
  oil node itself.

**The lesson is the page's own rule: a sentence that carries a number needs the
run that printed it.** A figure is evidence for what it plots, not for the
sentence written under it. When a claim is a comparison, say what it is compared
against — "inside the range" and "at the top of the range" are different tests,
and for a limit only the second one means anything.

### 23. A HOUSING TEMPERATURE SET AGAINST A GAS TEMPERATURE

Found 8 October 2026, while asking which published limit could set the damage
knee (`damage_constants.py`). REFERENCES.md and this file said the 1123 K
trigger "is already 80 K more conservative than the 930 C pre-turbine
enrichment limit" of Conway et al. 2018, and used that to say *do not lower the
limit*. **The 1123 K knee is on `thermal.py`'s turbine HOUSING node; 930 C is a
GAS temperature at the turbine inlet.** At steady state the node sits a fixed
fraction of the way from the gas to the ambient: 0.142 on the baseline's own
climb (1022 C gas, 883 C housing). Like for like, the knee is **984 C of gas,
54 K hotter than Conway's limit**, and 930 C of gas is 804 C on the node, 46 K
under the knee. The direction of the comparison was backwards. (The 0.142 rests
on the ASSUMED `ua_gas_turb` and `ua_turb_amb`; BorgWarner's own housing at a
950 C inlet has its inner wall at the gas temperature and about 100 C of
gradient inside it.)

Mistake 14's shape, in a document instead of a detector: **before comparing two
temperatures, check they are the same temperature.** A housing, the gas through
it, a thermocouple in that gas and the gas averaged over the cycle are four
different numbers (REFERENCES.md row 5 already warns about the last two).

### 24. AN AGENT'S BEHAVIOUR EXPLAINED FROM ITS INPUTS, NOT ITS OUTPUTS

Found 8 October 2026, the first day every step was recorded. Since 29 September
this file, the agents' README and the results page said blinded seed 6 does more
damage than the baseline on the five frozen episodes that weight life least
because "the preference-weighted reward lets it trade life for fuel". It was
read off the weights: low life weight, high damage, so it must be buying fuel.
**Nobody looked at the fuel.** On those five episodes it burns 6.3–9.9 % MORE
fuel than the baseline, its return is negative (at most −45, against at least
+32 on its other fifteen), and its per-step record shows why: on the climb its
median spark trim is −3.2 to −6.4° on those five episodes, against +2.6 to +3.9°
on the other fifteen. It loses on fuel and life together, so it is not a trade
the reward pays for. Nor is it inexperience: it met life weights that low in 13 of
its 56 training episodes, and all ten road sequences together in 124 of 560
(`record_extracts.py` -> `training_env.json`). The retard is something it learned
under those weights, and why is open. *(Corrected the same day: this said "a
policy failing on the inputs it saw least", written before the training weights
were counted -- this mistake's own shape, one paragraph later.)*

The same records showed the same retard behind its failure at 25 °C in the
conditions test, and `VALIDATION_PLAN.md` §11 had said "every agent keeps its
spark between +3 and +4°" from the group medians. **An explanation names
quantities; measure every one it names before writing it.** "Trades life for
fuel" names the fuel.

### 25. A FIX DECLARED SHARED WITHOUT FOLLOWING EVERY CALLER

Found 9 October 2026, in an audit of everything the simulation touches. Agreed
step 1 asked for ONE integrator for `thermal.py`, `calibrate_thermal.py` and the
app. On 8 October `thermal.ThermalNetwork.step` was sub-stepped and its
docstring said "every caller gets the same integrator, so the replays that
derive the constants (car_thermal.py) and the environment agree"; the WBS and
the validation plan then repeated it. **The constants are not derived by those
replays.** `calibrate_thermal.simulate` has its own copy of the node equations
and takes one explicit-Euler step per 1 s sample, so the re-derivation of
8 October ran the fit unchanged and returned the same constants to the last
digit, and that identical result was read as "re-fitted, nothing moved".
Re-fitted with the sub-steps (`substep_fit_check.py`, a diagnostic that writes
nothing the plant reads) the oil constants move under 2 %
and the coolant constants a lot: the radiator scale +61 %, block-to-ambient
−42 %. The locked climb barely notices (baseline −2.4 units, current-grade's
cut +0.01 points), which says the coolant constants are weakly identified,
not that the gap does not matter. Shipping the fix changes `derived_sha`, so
it waits for the next plant change.

The same audit found the agreed ramp (step 4) had broken six tests of
`app.test_agents`, which nobody had run since: the app read the climb as
starting on the ramp's first step, "181 s at 1.5 %", where it is 180 s at 12 %.
`agent_trace.route` now starts the climb on the last level step.

**An output that does not move after its input changed is a reason to check
that the input reached it. And after a plant change, run every suite that
reads the plant, not the one the convention names.**

---

### 26. AN ALLOWLIST THAT NEVER SAW THE SPELLING ITS OWN RECORDER WRITES

Found 31 October 2026, from one failure in the gate of R2b (`2f8e4a5`, whose
message records it). `test_calibrate_epa.Audit.test_dry_load_opens_only_its_allowlist`
reported that the Ford's dry-load had opened "1 path(s) outside the allowlist".
The `run.json` that named the path was deleted with the test's temporary folder,
the test passed when run alone, and looped reproductions on a quiet laptop did
not repeat it. Two agents then found it, one by reading the code and one by
reproducing it under load. When a WMI query times out, Python's `platform`
module stops using WMI for the rest of the process and runs `ver` with stdin on
DEVNULL, which opens `nul`. `calibrate_epa.Audit.norm` records the device as
`//./nul`, and the null clause of `Audit.allowed` tests its basename, which is
empty for a device path. So the one path the clause was written to admit was
refused under the only spelling the recorder produces. `validate_epa`'s audit
had admitted that spelling all along (`validate_epa.py:1434`). Under load the
fault was common in scratch runs; none of Run 1's real invocations hit it. Arm
runs the same audit in its `check` child, so one timeout during Run 2 would have
sent an engine back through its whole calibration (row 125). Commit N fixes the
one line, with a test that fails on the old code.

**A rule written for a value must be tested on the value as the recorder writes
it. A failure seen once is evidence: make the test print what it saw before its
fixture is deleted, and reproduce it under the conditions it failed in.**

---

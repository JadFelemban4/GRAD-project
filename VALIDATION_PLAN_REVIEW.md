# Review of the validation plan (Ghassan's draft of 7 October 2026)

Written for Jad and Ghassan. Reviewed by Claude in Jad's session, 7 October
2026, from the text Jad pasted; the plan (`results/VALIDATION_PLAN.md`) is not
yet on any branch, and neither are the three scripts it cites. Jad's decisions
are recorded in the last section as he makes them, one at a time.

**Status, 7 October, evening.** The plan has been explained to Jad in five
parts: the contexts of use, the required accuracies, the three sources of
u_val, the label rules, and the plan's findings. The eight points below and
the seven decisions are next. No decision has been taken yet.

**8 October.** Ghassan took all eight points, each checked, in section 12 of
the plan as pushed on `origin/GRA-2340394` (`2864592`). One correction to point
5, and it is right: the exact two-sided Wilcoxon p is 0.0137 (14 of 1024), so
nine looks give about **0.12**, not 0.09. On that commit the seven decisions
still read "pending".

**8 October, later. Jad agreed to all seven**, as recommended and as they now
read in section 10 of `2864592` (R3 withdrawn; the label order; the MEI as
5.43 % of the baseline's damage; the extrapolation named in duration). It is
Ghassan's to mark section 10 on his branch.

**Verdict.** The plan answers the supervisor's request: each label is computed
from numbers, not assigned by reading. Its method is sound (V&V 20's E and
u_val, and a required accuracy set per use from what an error would change),
and it states its own limits: the turbine is never measured, absolute damage
cannot be validated, and the climb is an extrapolation. Three points should
change before it is agreed; five more are smaller.

---

## Change before agreeing

### 1. "The supervision claim survives every ruler" needs its other half

The nine rulers change the damage function. None of them changes the knock
model that the agents exploit. With spark advance forbidden, the median margin
over current-grade goes from +24.4 points to −1.8, and 9 of 20 agents still
beat it (`results/agents/terrain_dt1/KNOCK_MARGIN.md`). As written, the
sentence reads as "the supervision claim is robust", and it is the sentence
most likely to be repeated to the supervisor.

Suggested wording: *"The supervision claim survives every damage ruler. It does
not survive forbidding spark advance (`knock_margin.py`); that is drive C's
question."*

### 2. The label rules overlap, and section 10 does not list them

If 2·u_val > R and also |E| − 2·u_val > R, a row is both *untested* and *off*.
A model far outside its requirement is *off* however noisy the data, so the
rules need an order. Proposed order: excluded, not covered, off, untested,
validated, limited.

Section 9 step 1 asks to agree sections 3, 4 and 7, but section 10 has no item
for section 7. Proposed: decision 4 becomes *"agree section 7: the rules, their
order, and k = 2"*.

### 3. Relative-only damage (decision 5) collides with the MEI, which is absolute

The minimum effect of interest is **50 damage units**
(`results/PREREGISTRATION_D2.md`). A uniform turbine error of 10 K (R1's limit)
multiplies every damage by about ×1.25 (section 4 of the plan), and with it
every sighted-minus-blinded difference counted in damage units. A true 50-unit
effect could then read 40 or 62.5. Points of cut, Ghassan's unit, are close to
invariant to that error; damage units are not.

<!-- RETIRED-OK: 920.1 -- the check_premise baseline when this review was written, 7 October; the plant fixes merged on 14 October moved it -->
If decision 5 is agreed, the next preregistration should state the MEI as a
fraction of the baseline's damage (50 of 920.1 is 5.4 %), not in units. R2's
basis ("+23 K of oil error moves damage by 50 units") reads the same way once
restated.

---

## Smaller

### 4. Push all three scripts with the plan

The plan's numbers come from `validation_numbers.py`, `damage_robustness.py`
and `car_spark_boost.py`. Ghassan's message names only the first. A number
needs the script that printed it in the tree (CLAUDE.md, mistake 22).
`damage_robustness.py` reads the per-step records, which are gitignored, so
the plan should say on which machine it can run.

### 5. The robustness table is nine looks, and its one significant row is post-hoc

knock ×4 gives Wilcoxon p 0.01 among nine rulers. Corrected for nine looks
(Bonferroni), that is about 0.09. The plan's reading is already careful
(preview's only measurable value is the one-second knock spike at the grade
step). Label the row post-hoc, and never quote it as a preview effect.

### 6. Operating region: the point is in the data, the hold is not

2.77 % of moving samples reach 2706 rpm and 175 kPa, so the operating point
itself is in the logs, in short pulls. What no drive contains is that load held
for twelve minutes; drive10, the Taif climb, never reached the trigger. Decision
6 should name the sustained hold as the extrapolation. Otherwise the obvious
reply is "but 2.77 % of your data is there".

### 7. R3 has nothing to be checked against

τ's only comparison is a literature band (40–120 s), and the step test
recomputes C/UA rather than measuring it (CLAUDE.md, limitations, the turbine τ
entry). There are two clean options. Drop R3 and state that COU-2's credibility
rests on the `c_turb` sweep, which the plan already says. Or name the comparison
R3 would judge.

### 8. The 1.2 s is the thermostat loop, not the block's mass

`thermal.py`'s docstring puts the explicit-Euler factor of a block perturbation
on the climb at −0.78 at dt 1.0, an effective time constant of about
1/1.78 = 0.56 s. That is consistent with the derived constants in
`data/derived_params.json`:

- c_block 36 350 J/K;
- an opening span of 2.85 K;
- up to about 3 560 W/K of radiator at 25 m/s and full fan;
- a coolant about 50 K above ambient.

Together these change the radiator's heat by roughly 60 kW per kelvin inside
the span. *(This is arithmetic from the derived constants, not a run.)* A
regulator that fast is a property of the fit, not of the block.

Sub-stepping will make it converge; it will not make it physical. The
time-step study should refit `calibrate_thermal.py` with the shared integrator,
as the plan says, and then report whether the fitted span stays this narrow.

---

## The seven decisions

| # | decision | recommendation | why | Jad |
|---|---|---|---|---|
| 1 | which standards | V&V 20 for the comparisons. **NASA-STD-7009B** for the risk side | 7009B is free, general-purpose and current (March 2024), so it can be opened and cited now, as `REFERENCES.md` requires. V&V 40 is written for medical devices and sold by ASME. V&V 20 is sold too: until the library provides it, cite its method through the free OSTI overview and Oberkampf & Roy | **agreed**, 8 Oct |
| 2 | the four contexts of use | agree | they separate the thesis claim (COU-1 to 3) from the app (COU-4), and give each its own accuracy | **agreed**, 8 Oct |
| 3 | R1 to R3 | agree R1 and R2 with their bases; R3 per point 7 | E is already known for most rows, so the guard against tuning is that each R comes from a consequence and is written beside it. Say so in the plan | **agreed**, 8 Oct |
| 4 | k = 2 | agree, together with section 7 and its order (point 2) | the usual coverage factor, about 95 % | **agreed**, 8 Oct |
| 5 | relative damage only | agree, and restate the MEI as a fraction (point 3) | no comparison can confirm the turbine to ±3 K | **agreed**, 8 Oct |
| 6 | every climb result is an extrapolation | agree, naming the sustained hold (point 6) | the data holds the operating point but never holds it for minutes | **agreed**, 8 Oct |
| 7 | fold into the next preregistration | agree | it fixes the required accuracies before the next training, which is the plan's own rule | **agreed**, 8 Oct |

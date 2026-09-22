# presentation/ — the team briefing site

An interactive, bilingual explainer of this project, written for the five of us rather
than for an examiner. It starts at "what is a piston" and ends at the sentence we have
to defend in the viva.

**Open `index.html` in a browser.** No server, no build step, no internet required
except for the web fonts — it degrades to system fonts offline and still works.

Published copy (private, share from the page's own share menu):
<https://claude.ai/code/artifact/92ebb852-f5b4-4bf5-938c-843d72130799>

---

## What is in it

| Section | What it covers |
|---|---|
| 01 · the problem | the sustained climb, what a reactive ECU does, what protection costs |
| 02 · the engine in ten minutes | four-stroke, spark advance, MBT, knock, lambda, turbo, EGT, τ |
| 03 · prior art | the five nearest works, why each does not close the gap |
| 04 · our contribution | H/τ, why dimensionless, why a second plant, the three claims |
| 05 · what sets us apart | the head-to-head, the premise table, the ablation, the objections |
| 06 · where we are | phases A–G, the evidence banked, the limitations, the next five steps |
| 07 · the mistake log | `CLAUDE.md`'s mistakes, one line of lesson each. **The page says eighteen and tabulates the first thirteen** (`CLAUDE.md`'s heading, plus the 13b addendum); its kicker names 13b and 14 to 18 and points to `CLAUDE.md` for them |
| 08 · glossary | 70 terms, searchable, the ★ ones marked as viva material |
| A · run it yourself | the five commands and the numbers they must print |
| B · teach-backs | who teaches what, and the four questions we will actually be asked |

**Two controls in the rail:** `English` / `العربية` swaps the whole page, and
**Presentation mode** turns it into a deck — arrow keys to move, `F` for fullscreen,
`Esc` to leave. Both choices are remembered in the browser.

**Seven interactive widgets.** Four-stroke animation, spark-versus-knock, the cost of
enrichment, the time constant τ, the race between the three policies, the H/τ sweep,
and the glossary filter.

---

## Where the numbers come from — none of them are typed by hand

`data.js` is **generated**. Two scripts in this folder produce it, and both import the
repository's own modules rather than re-implementing anything:

```bash
python presentation/dump_traces.py    # check_premise.py's four policies, per-second traces
python presentation/dump_sweeps.py    # plant.predict() spark and lambda sweeps
```

`dump_traces.py` writes `traces.json`, `dump_sweeps.py` writes `sweeps.json`, and the two
are packed into `data.js`. Both write only to their own output; neither touches `data/`
or `logs/raw/`.

> ## ⚠️ THE PAGE WAS OUT OF DATE UNTIL 22 SEPTEMBER — CHECK IT BEFORE SHOWING IT
>
> <!-- RETIRED-OK: 829.2, 548.6, 437.6, 13.4 -->
> Until the 22 September sweep, `index.html` hard-coded the premise figures
> **24 times** (829.2), **70 times** (548.6) and **16 times** (437.6), plus the
> 13.4-point preview edge and the H2 table. **Every one of them is void** as of
> 16 September 2026 — see the box at the top of [README.md](../README.md) and
> `AUDIT.md` findings C1, C2 and C3. Grepped after that sweep, `index.html`
> carries 829.2, 548.6 and 437.6 **zero times** and no longer states the
> 13.4-point edge as a claim; the H2 table and the H1 curvature table survive
> only as a record, captioned void, under markers that name their figures.
>
> In short: the baseline those figures were measured against had its cooling
> switched off, the baseline ECU was scheduled on a load the engine was not at,
> and the "blinded run is byte-identical to the reactive one" claim this file
> used to make as evidence is an identity that could not have failed.
>
> **The constraint now binds.** On the locked scenario — 12 % at 130 km/h,
> 42 °C — `check_premise.py` prints a baseline of **959.8** damage units peaking
> at **884 °C** against the 850 °C trigger. Against the honest comparator, the
> policy that acts on the grade the car is on now, hand-written preview
> **loses by 0.4 points**. And the project's result is not from this script at
> all: it is Phase D (`python analyse_phase_d.py`), a **null** — with agents
> trained to the C1 budget, preview does not separate from seed noise
> (p = 0.3633 sign, p = 0.4922 permutation) — and its blinded arm was not
> blind (one fixed road plus a thermal clock, `results/PREREGISTRATION.md`
> limit 7), which Phase D2 exists to remove.
> <!-- RETIRED-OK: 801, 812, 110 -->
> *(Until 22 September this box said the constraint did not bind at all: the
> baseline peaked at 801 °C, then 812 °C after the H1 crank-angle correction,
> on the old 110 km/h scenario. That stopped being true when the scenario moved
> to 130 km/h on 18 September; the box was not corrected until the 22 September
> sweep. See `CLAUDE.md`.)*
>
> In `data.js`, the traces were regenerated with `dump_traces.py` on
> 22 September; the sweeps were re-embedded from `sweeps.json`, which
> `dump_sweeps.py` wrote on 18 September and whose plant code has not changed
> since (docstrings only). So the widgets draw the current plant. The figures
> hard-coded in `index.html` itself were swept separately on 22 September. Run
> `verify_docs.py` and read its result for that file before this page is shown
> to anyone outside the team, and note that its mistake log still stops at 13.
>
> **THE CHECKER HOLE IS CLOSED.** Until 17 September `check_retired()` built its
> own file list from `glob("**/*.md")` plus the root `*.py`, so the RETIRED scan
> never opened `index.html` — measured that day, it opened 25 files and this page
> was not one of them, while 77 of its lines would have fired six retired
> patterns. Since AUDIT2 M2-7d it reads `tracked_files()`, the same list as the
> figure scan, so `index.html`, `plan.html` and `data.js` are all checked.

<!-- RETIRED-OK: 2.8, 31, 82, 62, 32, 527.2, 39.5 -->
The page was also scanned for every figure this project has **retired** — 2.8 %,
31–82 kPa, 62 %/32 %, 527.2, τ = 39.5 s and the rest — and carries none of them as a
live claim. The figures named in that sentence are listed as retired, not asserted:
the current values are a 1.4 % load residual over 26 points spanning 30–75 kPa, and a
turbine time constant of 48.0 s. The only mentions of the 2.0 L inline-four are inside the account of
mistake 1, where it belongs.

---

## Rebuilding it after the numbers move

The page is assembled from partials that are **not** in this folder — they live in the
session scratchpad that produced it. If a figure changes and the page needs regenerating,
the honest options are:

1. **Small correction** — edit `index.html` directly. It is one self-contained file.
2. **A figure that appears in several places** — re-run `verify_docs.py` first to learn
   every place the old value survives, then fix each. This is mistake 11, and it is the
   one this page is most exposed to.
3. **The traces or sweeps changed** — re-run the two dump scripts above and rebuild
   `data.js`; the widgets pick the new data up with no code change.

**If this page disagrees with a script, the script is right.**

---

## Added 16 September 2026 — the live app is not in this page

`app/` now exists: the live supervisor that runs the plant and the thermal
network beside the car and estimates turbine temperature. **Nothing on this
briefing page covers it**, and nothing on this page is wrong because of it — the
figures here are Phase B and the premise check, and as of 16 September neither
had moved. *(Both moved afterwards: the premise check was voided by `AUDIT.md` that
same day and later re-run on the rebuilt scenario, and the dataset grew with
`drive10` — see the box above and the next paragraph.)*

If the app is added to the briefing later, two things have to come with it:

1. **The turbine temperature it shows is a MODEL OUTPUT, not a reading.** Its
   heat capacity is an ASSUMED number (REFERENCES.md section 4) and the vehicle
   publishes no channel to check it against. A screenshot without that caption
   is the most misleading artefact this project could produce.
2. **Its alert counts are not measurements.** 15 thermal / 0 mismatch / 19 novel
   on `7475b5d7` is a property of thresholds we chose, pinned so a regression is
   visible. A slide that presents them as findings about the car is wrong.

<!-- RETIRED-OK: 168.1 -->
The dataset behind this page also moved: **ten drives, 295.0 minutes**, up from
eight and 168.1 before `pull01` and the Taif drive `drive10` arrived. (The
superseded pair is named on purpose, so anyone holding an older caption can
recognise it.) `pull01` contributes zero samples and zero operating points by
design; `drive10` took the operating points to 26 over 30–75 kPa. Any caption
quoting the dataset has to follow.

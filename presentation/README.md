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
| 07 · the mistake log | `CLAUDE.md`'s mistakes, one line of lesson each. **The page shows thirteen; the log now holds sixteen** — 14, 15 and 16 are not on the page |
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

> ## ⚠️ THE PAGE IS OUT OF DATE AND MUST NOT BE SHOWN AS IT STANDS
>
> <!-- RETIRED-OK: section -->
> `index.html` hard-codes the premise figures **24 times** (829.2), **70 times**
> (548.6) and **16 times** (437.6), plus the 13.4-point preview edge and the
> H2 table. **Every one of them is void** as of 16 September 2026 — see the box
> at the top of [README.md](../README.md) and `AUDIT.md` findings C1, C2 and C3.
>
> In short: the baseline those figures were measured against had its cooling
> switched off, the baseline ECU was scheduled on a load the engine was not at,
> and the "blinded run is byte-identical to the reactive one" claim this file
> used to make as evidence is an identity that could not have failed.
>
> **The corrected script reports that the constraint does not bind at all** on
> this scenario: the baseline peaks at **812 °C** against an 850 °C trigger.
> *(801 °C until 17 September — that was the figure before the H1 crank-angle
> correction moved `plant.DTHETA_DEG` to 0.25°. `AUDIT_FIXES.md` records the
> move 801 → 812; this file did not follow it.)*
>
> Regenerate `data.js` from the two dump scripts and rewrite every figure before
> this page is shown to anyone outside the team. Until then it is a record of
> what we believed in September, not a briefing.
>
> **THE CHECKER HOLE IS NARROWER THAN THIS FILE USED TO SAY, AND STILL OPEN.**
> `index.html` was added to `verify_docs.TRACKED_DOCS` (AUDIT.md L11), so the
> FIGURE scan does read it. But `check_retired()` builds its own file list from
> `glob("**/*.md")` plus the root `*.py`, and `index.html` is neither — so the
> RETIRED scan never opens it. Measured 17 September: the retired scan opens
> **25 files and `presentation/index.html` is not one of them**, while 77 of its
> lines would fire six retired patterns and it carries no `RETIRED-OK` marker.
> **Two scans, two file lists, and only one of them was fixed.** Until the lists
> are shared, a green run says nothing about this page.

<!-- RETIRED-OK -->
The page was also scanned for every figure this project has **retired** — 2.8 %,
31–82 kPa, 62 %/32 %, 527.2, τ = 39.5 s and the rest — and carries none of them as a
live claim. The figures named in that sentence are listed as retired, not asserted:
the current values are a 1.4 % load residual over 22 points spanning 30–75 kPa, and a
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
figures here are Phase B and the premise check, and neither moved.

If the app is added to the briefing later, two things have to come with it:

1. **The turbine temperature it shows is a MODEL OUTPUT, not a reading.** Its
   heat capacity is an ASSUMED number (REFERENCES.md section 4) and the vehicle
   publishes no channel to check it against. A screenshot without that caption
   is the most misleading artefact this project could produce.
2. **Its alert counts are not measurements.** 13 thermal / 0 mismatch / 19 novel
   on `7475b5d7` is a property of thresholds we chose, pinned so a regression is
   visible. A slide that presents them as findings about the car is wrong.

<!-- RETIRED-OK -->
The dataset behind this page also moved: **ten drives, 295.0 minutes**, up from
eight and 168.1, because `pull01` arrived. (The superseded pair is named on
purpose, so anyone holding an older caption can recognise it.) It contributes zero samples and zero
operating points by design, so no figure on this page changed — but the drive
count in any caption did.

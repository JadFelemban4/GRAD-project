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
| 07 · thirteen mistakes | the mistake log from `CLAUDE.md`, one line of lesson each |
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

The traces behind the race widget are the real thing: four full 720 s rollouts whose
summary reproduces the published premise numbers exactly —
**829.2 · 548.6 · 437.6 · 548.6**, with the blinded run byte-identical to the reactive one.

Everything else on the page was checked against the repository before it shipped:

```
python verify_docs.py         # all checks pass, 230 figure mentions agree
python generality_test.py     # H2 confirms 16.5 -> 18.0 -> 26.0
python check_premise.py       # 829.2 / 548.6 / 437.6 / 548.6
```

<!-- RETIRED-OK -->
The page was also scanned for every figure this project has **retired** — 2.8 %,
31–82 kPa, 62 %/32 %, 527.2, τ = 39.5 s and the rest — and carries none of them as a
live claim. The figures named in that sentence are listed as retired, not asserted:
the current values are a 1.4 % load residual over 22 points spanning 30–74 kPa, and a
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

The dataset behind this page also moved: **nine drives, 175.5 minutes**, up from
eight and 168.1, because `pull01` arrived. It contributes zero samples and zero
operating points by design, so no figure on this page changed — but the drive
count in any caption did.

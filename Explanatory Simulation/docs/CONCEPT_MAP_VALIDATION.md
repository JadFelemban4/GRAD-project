# Project map: validation, 30 October 2026

Branch `JMF-2340550-anatomy-housing`. A "Project map" button in the top bar
opens a map of every concept in the lab, in the manner of Obsidian's graph:
58 nodes, 155 arrows from cause to effect, coloured by part of the project.
Click a node and its causes and effects light up; the card beside the map
gives its meaning, its links and a button that opens its line in the code
(the lab's own source dialog). Search finds a concept by its Arabic or English
name or its id. A colour in the list shows one part of the project alone.

## Where the map comes from

- **The links are the content files' own** (`upstream` and `downstream` of each
  concept in `content.json` and `content.ar.json`). A link written on either
  end counts once: 155 links, the same in both languages. 103 of them are
  written on one end only, which is why the map takes the union.
- **The grouping is the one thing written for the map**:
  `src/model/concept-map.mjs`, `GROUP_OF`, six parts (road and scenario 9,
  engine and combustion 12, air exhaust and turbo 5, heat and damage 7,
  supervisor and reward 16, preview and the research question 9).
- **The layout** is a deterministic force layout (same picture every time).
  Pushing between nodes stops past two spacings, so a lightly linked node is
  not flung to the edge: the median gap between neighbours went from 36 to 51
  units, the smallest from 27 to 43.

## What was checked

| check | result |
|---|---|
| `node --test src/model/concept-map.test.mjs` | 5 of 5: every concept has a group; both languages give the same links; the links are exactly the content files'; the layout repeats, stays in the frame and no two circles touch; search works in Arabic, English and by id |
| `npm run build` | type check and bundle pass |
| all Node tests | 147 run, 1 fails: the provenance test that already failed on main |
| all Python tests | 35 run, the same 4 failures as on main |
| in the browser | dark Arabic and light English; selecting the turbine housing lights its 4 causes and 2 effects, and the code button opens `thermal.py` at the `q_in_turb` line; labels never overlap (a name with no room shows on hover); Arabic names read right to left |

A first version put the button inside the mode bar; `thermal-viva.test.mjs`
renders that bar with a fixed set of handlers and failed. The button moved to
the top bar instead, and the test was left as it is.

## Worth a look, not changed

The map shows the content's links as written, so it also shows the ones that
read loosely: `thermal_time_constant` is listed as a cause of `preview` (the
road preview itself), where the project's argument is that τ decides what the
preview is worth. The links are for whoever owns `content.json` to review.

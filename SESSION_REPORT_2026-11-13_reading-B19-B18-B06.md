# Session report — 12 to 13 November 2026: Jad reads B19, B18 and B06 of his ten

Jad's learning session on `JMF-2340550-Literature-review`, the third and fourth day of
his ten papers (B37 and B40 were the first two, `SESSION_REPORT_2026-11-12_reading-B37-B40.md`).
Nothing in the physics, the data or the training changed; the work lives in the team's
Notion tracker. New: this report and `NEXT_SESSION_2026-11-13_reading.md`; edited:
`CHECKPOINT.md` (item 11), `STATE_HISTORY.md` (part AU), `HISTORY.md`, `team/jad.md`.

## 1. What was done

- **B19** (Bosch, US 12,553,397 B2), **B18** (Hyundai-Kia, SAE 2021-01-0225) and **B06**
  (Prakash et al., ASME DSCC 2016) were read with Jad in Dr. Hammam's order
  (`docs/literature/READING_METHOD.md`): the abstract and the conclusion first (claim 1
  for the patent), Jad set "Related?", then the methodology, then the evidence. The
  explanations were in Arabic, one idea per message, each passage quoted with its page.
- **The tracker as Jad left it.** B19 and B18 were read back from the table after each
  write. B06's last write could not be read back: see the note under the table.

| ID | Related? | Bears on our claim | Status | Theme | fields filled |
|---|---|---|---|---|---|
| B19 | Unsure | Prior art (does part of it) | Annotated, 12 November | L6 Reactive protection | Critical synopsis, Why (claim) |
| B18 | Yes | Prior art (does part of it) | Annotated, 13 November | L5 Predictive powertrain | Critical synopsis, Why (claim) |
| B06 | Yes | Background only | **not set** (see below) | L5 Predictive powertrain | Why (claim); Critical synopsis **not confirmed** |

- **B06 at the close.** Jad approved the B06 synopsis; the write to Notion returned
  "Internal server error", and every read after it failed (timeouts, "overloaded",
  "Authentication is temporarily unavailable") until the close. Whether the text is in
  the cell is not known. The approved text was kept outside the repository, in the
  session's scratchpad. B06's Status was asked and not answered before Jad closed, so it
  was left at "Not started". Both wait for the next session (its prompt says so).
- **Jad's choices against Claude's suggestion:** B06's "Background only" is Jad's
  ("ما شفت انها لامست افكار مشروعنا"); Claude had suggested "Prior art", since B06 sweeps the
  horizon and finds a ceiling, the H half of the ratio. Claude noted that an examiner may
  ask why a horizon sweep is background only; Jad kept his reason. B19's "Unsure" is
  Jad's, after Claude suggested Yes.
- **Left empty on all three, by Jad's pace:** Specific finding (page), Evidence,
  Strengths and weaknesses, Answer to Read it for (page), Contrary evidence, Original
  source, Leads to, Method, System studied, Current?.

## 2. What in those fields is not Jad's own wording

Each completion was written at Jad's request, in his style, shown to him (for B18 and
B06 before it was written), and each addition listed to him.

- **B19, Critical synopsis:** Jad's summary, corrected and completed: the test bench is a
  real engine on a stand (not a simulation) and fills the numbers, it does not test the
  idea; the first map takes the air requested and gives the temperature (the computed
  quantity is the temperature); the inverted map takes that temperature with the
  component's limit and gives the air allowed; the cap is not "the table's largest value"
  but moves with the turbo's computed temperature; the order of the three measures is
  chosen per engine; and a closing line: the method does not look at the road, it
  anticipates only from the driver's request, and Bosch calls map-based protection
  "inherently known".
- **B19, Why (claim):** Jad's sentence, corrected (two of Bosch's three measures are ours,
  water injection is not; our fan and pump cool the coolant, not the turbo directly) and
  completed with the H/τ line (Bosch protects without seeing the road and does not ask
  when preview is worth it).
- **B18, Critical synopsis:** Jad's summary, corrected (Hyundai-Kia *say* GT-SUITE was
  validated on a car and show no data; the small model was calibrated on GT-SUITE's
  output; "early is harmful" is stated without a run; the project did not drop spark, it
  capped the trim at 0 and reports with and without the knock term until drive C; fuel
  "implies the potential", it was not measured) and completed (what they protect, their
  actuators against ours, the abstract-conclusion contradiction on knock, results under 5 %).
- **B18, Why (claim):** Jad's own text, verbatim, in the order he gave last.
- **B06, Critical synopsis (if it is in the cell):** Jad's summary, corrected (the lead
  car comes from EPA's official test cycles; the Ford Escape is in EPA's fuel calculator,
  ALPHA, not on the road; the pedal as well as the brake; the human driver is the third
  term of the comparison) and completed (no engine or heat in the planner, so no τ; the
  results; perfect prediction in every run; short preview with the wrong cost function
  made fuel worse; the horizon sweep shown for one cycle).
- **B06, Why (claim):** Jad's text, verbatim.

## 3. Where things are in the three texts

Page pointers for the fields Jad left empty. They are **not a reading**: a field filled
from this list instead of the text does not count (`READING_LIST.md` rule 4). Pages are
those of the tracker's PDF file.

B19, 7 pages, a scan:

- p. 1: the abstract; the only document cited is FR 2893979 A1 (2007).
- p. 3, column 1: the first map "is inherently known"; the measures (charge limitation,
  enrichment, water injection in future systems); the maximum temperature from test-bench
  parameters; late ignition listed among the temperature-raising effects. Column 2: a
  real-time model can "determine and optionally precalculate" the exhaust temperature;
  the order of the three measures "can be freely selected".
- p. 4, column 4: the air volume correcting element 26, e.g. a throttle valve.
- p. 5, column 5: the temperature models "are assumed to be inherently known". Column 6:
  the pipe model depends on the valve temperature, vehicle speed, ambient temperature and
  exhaust mass flow; the target relative charge addresses map 36; map 40 holds the
  maximum temperatures; the PI regulator 44 corrects the *modeled* component temperature.
- p. 6, column 7: the inverted map 50; the smaller of two charges is applied; the limit is
  "at least ideally not exceeded". Column 8: one measure at a time "to avoid mutual
  interference"; the order "can be established by test bench measurements"; Examples 1-4.
- p. 6-7: the claims; claim 2 names the turbocharger. No measured data anywhere.
- Against "Read it for": no route, navigation, map or forecast on any of the seven pages
  (p. 2 is the drawing); the only anticipation is from the driver's request.

B18, 8 pages, with a text layer:

- p. 1: the abstract claims savings from delayed knock spark retard and from the fan.
- p. 3: the cycle: one acceleration-deceleration section and one uphill at 40 mph, 15 %,
  20 minutes, 45 °C, A/C on.
- p. 6: the 3-state model calibrated on GT-SUITE data; GT-SUITE "validated using
  real-world vehicle test data", not shown; Method #1: GPS sees the hill 240 s ahead, and
  lowering the target 240 s or 120 s ahead "will" over-cool (stated, no run shown);
  Fig. 8: hill detected at 560 s, target lowered at 710 s, hill at 800 s.
- p. 7: Table 2 (fan start delayed, fan energy -4.8 %, alternator -2.3 %, coolant before
  the hill 82.7 against 91.1 °C), and "This implies the potential of fuel consumption
  improvement".
- p. 8: knock and spark retard "will be modeled" in future; on-road tests "are needed".
- Against "Read it for": a 240 s horizon, with against without preview in one run; the
  horizon is not varied.
- Leads to: its references 4 (Lehner et al., SAE 2001-01-0336) and 5 (Khodabakhshian,
  Feng and Wikander 2014); B34, its follow-up.

B06, 8 pages, with a text layer:

- p. 2-3: the hypothetical lead; a point-mass model; the gap bounds; "The model does not
  consider the engine, vehicle or powertrain dynamics"; fuel from EPA's ALPHA model of a
  2013 Ford Escape 1.6 L EcoBoost, values "specific" to that car.
- p. 4: Fig. 3, fuel economy against the prediction horizon, for the UDDS cycle only.
- p. 5: "perfect prediction of constraints along the prediction horizon is assumed for
  all cases"; a 1.5 s velocity prediction is accurate, longer "is not very probable"
  (their ref. 22); MPCa below the standard cycle under 5 s, equal to DP at 20 s, with the
  speed traces converging (RMS 2.24, 1.26, 0.58 m/s at 4, 8, 20 s).
- p. 6: MPCv chosen at 1.5 s; "not all accelerations are equally fuel consuming"; the
  claim that 20 s matches DP "for all the given cycles" (only UDDS is plotted).
- p. 7: Table 1 (DP 13.1-16.7 %, MPCv at 1.5 s 5.3-11.8 % over four cycles); the
  conclusion and the regulators.
- Against "Read it for": the gain is not a straight line in H; it rises, can fall below
  zero under 5 s for one formulation, and is flat from 20 s; all under perfect prediction.
- Leads to: its references 1 (the hypothetical lead, ACC 2016), 7 (Shengbo et al. 2008,
  5 s look-ahead) and 22 (Nüesch et al. 2015, the 1.5 s predictability).

## 4. Found and left alone (tools)

- **Downloading a tracker PDF:** `curl` inside the sandbox got "Empty reply from server"
  from Notion's file host; with the sandbox off it returned 200. B19 is a scan (rendered
  with PyMuPDF, `C:\Users\admin\Python3132\python.exe -P`); B18 and B06 have a text layer
  (`pdftotext` from Git's `mingw64`).
- **The Notion connector failed twice.** Once with ECONNRESET on B19's "Why (claim)": the
  read-back showed the write had not happened, and the retry was read back right. At the
  close, an internal server error on B06's synopsis and no reads after it (section 1).
  Every write this session was read back before Jad was told it was saved.
- Notion's SQL by ID returns the right row (`userDefined:ID`), as the last report found.

## 5. How the reading went

- Jad writes back what he understood; Claude confirms or corrects; no check questions.
  Jad asked twice for his notes to be completed in his style; for B18 and B06 he asked to
  see the text before it went in.
- What landed and what did not, with the examples: `team/jad.md`, 12 to 13 November.
- **One wrong statement by Claude, corrected in the session:** it called the logged car
  "Ghassan's". The repository says only that the Supra is a teammate's car
  (`team/jad.md`); the owner is not named here.
- A check of the code during the reading, for Jad's question: the scored locked climb runs
  at a constant 130 km/h, the plain training roads at a constant speed, and the extremes
  roads change the speed target every 60-180 s between 60 and 150 km/h
  (`engine_env.py`, `locked_climb` and `extreme_speed_profile`). So B18's "one climb at a
  constant speed" applies to the climb the project scores on as well.

## 6. Checks at the close

- `python verify_docs.py`: read by its exit code, see the close commit.

## 7. Next

B31, then A25, B49, C20 and C18 (`NEXT_SESSION_2026-11-13_reading.md`); first, B06's
synopsis checked in Notion (re-written from Jad's approved text if missing) and its Status
set by Jad. Waiting on Jad, as before: readers for the other 40; C48 and C61 from a
browser; the housing-lag exporter's port (`CHECKPOINT.md` item 4); the paid D01, A03 and C36.

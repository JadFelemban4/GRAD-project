# Session report — 16 to 18 November 2026: Jad reads B31 and A25, and writes his part of the literature review

Jad's learning session on `JMF-2340550-Literature-review`: B31's abstract and conclusion on the PC on
16 November (`NEXT_SESSION_2026-11-16_reading.md`), then his laptop from 16 to 18 November, while the PC
trained. Nothing in the physics, the data or the training changed; the work lives in the team's Notion
tracker and in two Claude Docs. New: this report, `NEXT_SESSION_2026-11-18_reading.md` and
`docs/literature/review/computer-simulations.md`. `docs/literature/review/preview-in-vehicles.md`, written by
another session on 17 November, is committed with them at Jad's request ("ارفع كل شي"). Edited:
`CHECKPOINT.md` (item 11), `STATE_HISTORY.md` (part AV), `HISTORY.md`, `team/jad.md`.

## 1. What was done

- **B31** (Liu et al., IEEE TCST 2023) was read again from its abstract at Jad's request ("نبدا من البداية
  عشان نراجع"), then its methodology and its evidence, in the handoff's order. **A25** (Wei et al.,
  AgriEngineering 2026) went the same way: the abstract and the conclusion on 16 November, the methodology
  and the results on 17 November.
- **C20 and C18 left Jad's list:** the teammates asked to read them and Jad agreed. The tracker shows both
  under Mohammed, read in full. Jad's last paper is B49.
- **The tracker as Jad left it**, each write read back after it was made:

| ID | Related? | Bears on our claim | Status | Theme | fields filled |
|---|---|---|---|---|---|
| B31 | Unsure | Background only | Annotated, 16 November | L5 Predictive powertrain | Critical synopsis, Why (claim); Date read 16 November |
| A25 | Unsure | Background only | Annotated, 17 November | L4 Horizon rules | Critical synopsis, Why (claim), Answer to Read it for (page); Date read 17 November |

- **The Status column changed after those writes.** On 18 November no row in the tracker reads "Annotated":
  the seven Jad set so (B37, B40, B19, B18, B06, B31, A25) read "Read in full", like 27 rows of the
  teammates; 2 rows read "Abstract and conclusion read" (A23, C62; a query of 18 November). This session
  wrote "Annotated" and read it back; it did not make the change. Whether someone edited the rows or renamed
  the option is not known.
- **Summaries in chat:** Jad's eight papers in his style, each with its field, how it was tested and how it
  bears on the project. Not saved anywhere.
- **Jad's own review**, in English for the thesis: the Claude Doc "Literature Review: Preview, Time
  Constants and Thermal Protection" (https://claude.ai/artifact/DEXHXuT7sZxqVQsiZvBs8k), on the seven
  sources he had read, by theme (protection without preview, preview at one fixed horizon, where preview stops
  paying), then how each source produced its evidence, and the gap. Two of its sentences said A25 had been read
  only to its abstract and conclusion; they were corrected at the close (the doc's revision 15).
- **Jad's section of the team's review**, "Computer simulations of engines, vehicles and buildings" (B18,
  B31, B06, A25), one of the six kinds of study on the team's map, approved by Jad on 17 November:
  `docs/literature/review/computer-simulations.md`, with the pages behind each sentence.
- **The team's draft:** the Claude Doc "Literature Review: Team Draft"
  (https://claude.ai/artifact/SdVgmBW53zLCquoTdHJ3uh) puts the four sections Jad pasted from his teammates
  beside his own, under one IEEE numbering from `docs/literature/references.bib` (33 references), with the
  comparison table from Jad's file; its rows [15]-[18] were corrected against the PDFs. The teammates' text
  was not rewritten: what it still needs is listed under "Open items" (among them the Landerl reference, the
  EPA document, and the Standards section, not written).
- **For his presentation to the supervisor**, in chat: talking points for his section, what each of his
  four papers protects, and the gap. The gap as given: of the reviewed works, only A25 ties the preview
  horizon to a time constant, for one house; none tests such a rule on more than one system, or uses it to
  protect an engine component from heat. Two cautions went with it: the team's mathematics section (Seiler
  et al. and others) already relates preview to a system's dynamics for simple linear systems, so "nobody
  linked preview to τ" would be false; and the battery is a plan, not a result.

## 2. What in those fields is not Jad's own wording

- **B31, Critical synopsis:** Jad's draft, corrected and completed at his request ("اذا في تعديل او اضافة قول
  لي"), shown to him before it went in ("حطها في Critical synopsis"). The corrections: the draft had the two
  EGR loops swapped (the short one bypasses the turbo, the long one passes through it; he had them right
  earlier); the long loop is used more at steady high load because it costs the engine less and saves a
  little fuel (p. 5), not to relieve the short one; returning exhaust is what they control, not their idea,
  which is the two-level controller; the aim is to balance NOx, soot, fuel and torque (p. 1), not to calm
  the burn; the twin differs in structure, solver and tuning in every run, not in hardware in the last one;
  the heat was not ignored (the engine model has heat transfer, p. 3), what they left out is the slow thermal
  part, DPF regeneration (p. 9). The additions: the engine in the second stage is a model on a second
  machine; the results, the HiL bench and the noise test; the weaknesses (one horizon, the future known
  exactly, a model and not an engine). Jad declined one more, on how the weights were chosen ("لا تحطها").
- **B31, Why (claim):** Jad's text, verbatim.
- **A25, Critical synopsis:** Jad's text from before the methodology, verbatim, at his request ("بنفس كلامي
  الي قلته اول"). Its last line says that control uses the τ of a part of the house. In the methodology
  Claude showed that the plan's "pieces" are pieces of time (p. 7, p. 17) and that control's scale is the same
  house's fast scale, τf ≈ 5.5 h (p. 13, p. 22). Jad kept his first words; read that line with this note.
- **A25, Why (claim):** "مجالين مختلفين", Jad's, verbatim.
- **A25, Answer to Read it for (page):** Jad's sentence, verbatim, without the lines of his message that were
  instructions; the cell has no page. In the text: the two best of the five horizons, 4 h and 8 h, divided by
  τf (p. 17-18).
- **In the explanations of 17 November** ("القسم يقول / انت كتبت"), some lines labelled "you wrote" quoted
  completions Claude wrote in Jad's style and he approved before they went into Notion: B18's "they protect
  the engine, not the turbo" and "they say it was checked on a car but show no data", B31's "the engine a
  model on a second machine", B06's "no engine and no heat". They are in his notes, not his first wording.
  Jad was told at the close.

## 3. Where things are in the two texts

Page pointers, for fields left empty. They are **not a reading**: a field filled from this list instead of
the text does not count (`READING_LIST.md` rule 4). Pages are those of the tracker's PDF.

B31, 12 pages, with a text layer:

- p. 3: the engine model, FEV's, "experimentally validated" in its references 34 and 35, with physics-based
  flow, combustion and heat transfer; the baselines, the eMPC of its reference 19 (one controller for the slow
  and the fast dynamics, no look-ahead) and a production-line controller; the horizon "should ideally be as
  long as possible"; the contributions list's NOx and soot figures (5.3 % and 11.5 %).
- p. 4: Fig. 3, torque autocorrelation useful to about 3.5 s, turbo-lag 1.4 s, boost affecting torque up to
  8 s; "a horizon between 1.4 and 8.0 s fully considers the airpath dynamics"; "to reduce the computational
  complexity, this study uses a 2-s look-ahead horizon".
- p. 5: the look-ahead is used by the upper level only; one 0.1 s horizon for both EGR loops; a larger LP
  share lowers the pumping loss.
- p. 6: the constraints: the VNT kept off its choking and surging boundaries by box constraints from FEV's
  look-up tables; the oxygen-fuel ratio held above a minimum, as a soft constraint.
- p. 7: Table III (on the HiL bench, torque tracking against the production controller 1.2 % worse, where
  the desktop run was better); the bench, the controller on an A80Q7 board's Cortex-A15 and the engine model
  on a dSPACE SCALEXIO (Fig. 4); the future read from a stored array.
- p. 9: the noise test (a random delay of 0 to 2 s, multiplicative Gaussian noise); soot accumulation and DPF
  regeneration "not considered in this study for their longer horizon related to the temperature dynamics";
  tail-pipe NOx 4.6 % and 8.7 % below the eMPC and the production controller.
- p. 10: the conclusion: NOx and soot 5.5 % and 11.7 % (p. 3's figures measured another way, Table III);
  torque tracking 30.9 % better than the production controller (the desktop figure); the benefit fades with
  the noise and vanishes at about 13 %; with an automatic gearbox the benefits "remain consistent"; worst-case
  execution time 8.92 ms (also p. 1).
- Against "Read it for": 2 s chosen for computation inside a 1.4-8 s range set by the turbo's dynamics
  (p. 4); 0.1 s for both EGR loops; no other horizon was run.
- Leads to (p. 11): its references 18 and 40 (Liao-McPherson et al., cited for the 2 s), 19 (the baseline
  eMPC), 32 (Umezawa et al., hierarchical MPC), 35 (Vagnoni et al.) and 38 (Shin and Sunwoo, speed
  prediction).

A25, 26 pages, with a text layer:

- p. 1: the abstract: 78,000 birds, 35 days at 15 min, τ = 25.7 h; 4-8 h of preview held σ = 0.17 K with no
  violations (0.74 K at 1 h); the rule, 0.7-1.5 τf, "re-estimated per house and season"; the introduction:
  indoor temperature drives the birds' growth.
- p. 6: the heat-balance model, calibrated by grid search on the training segment.
- p. 7-8: the control simulation: five horizons, 1, 4, 8, 24 and 48 h, each plan piecewise-constant in time;
  the setpoint 27.5 °C (p. 8).
- p. 13: τf from about three days of record (Table 4).
- p. 17-18: replaying the farm's actions through the model misses by about 2.5 K; 4 h and 8 h regulate best,
  24 h and 48 h worse; the refined 24 h plan does no better (p. 17); the robustness tables report the best of
  three noise seeds (p. 18).
- p. 20: Table 12's note: replay RMSE 2.53 K; only replay left the 24-33 °C band (326 events above, 765
  below); MPC-24h used 47 % more energy than MPC-1h.
- p. 22: the 4-8 h optimum is set by the fast scale, "the time scale on which the controller's own actions
  actually move the indoor temperature".
- p. 23: one house, one winter, one controller; the numbers are house- and season-specific.
- Against "Read it for": the τ is the house's (25.7 h for forecasting, τf ≈ 5.5 h for control); one house and
  one controller, MPC on a calibrated model; the rule is the two best of five horizons divided by τf, tested
  in simulation only.

## 4. Found and left alone (tools)

- The laptop has no `pdftoppm` either, so the Read tool could not render a PDF. PyMuPDF was installed into
  the session's scratchpad (`pip install --target`) and run with `python -I`, to render B31's Fig. 1 and
  Table III and to find pages; it went with the scratchpad.
- `curl` to Notion's file host worked inside the sandbox on the laptop (on the PC it had failed).
- The Notion connector dropped several calls (ECONNRESET); every write was read back before Jad was told it
  was saved. Creating the team's Claude Doc failed once the same way; the artifact list showed no copy before
  it was created again.
- **`python verify_docs.py` could not run on the laptop.** Its Python 3.13.2 (`C:\Users\endof\Python3132`)
  has no numpy, pandas or stable-baselines3; the other Pythons are 3.13.14 (the default, numpy 2.4.2, and
  `venvs\ml`), neither with stable-baselines3. So this close is unchecked; the next session runs it on the PC,
  in the lock's environment, first.

## 5. How the reading went

- Jad writes back what he understood; Claude confirms or corrects; no check questions. He asks to see a text
  before it goes into Notion, keeps his own words when he prefers them (A25's synopsis), and declines
  additions he does not want (B31's weights).
- What landed and what did not, with the examples: `team/jad.md`, 16 to 18 November.
- **Claude's own errors, corrected in the session:** A25 was said to run four horizons (five: 1, 4, 8, 24 and
  48 h; corrected in Doc 1 and told to Jad); the refined 24 h plan was said to improve a little (it did not,
  p. 17); and the "you wrote" labels of section 2.

## 6. Checks at the close

- `python verify_docs.py`: not run (section 4).
- Every Notion write of the session was read back; the rows of section 1 were queried again on 18 November.
- Doc 1's correction read back (revision 15).

## 7. Next

B49 (Laguna et al. 2022), Jad's last paper, on the PC (`NEXT_SESSION_2026-11-18_reading.md`), after
`verify_docs.py`. The team's draft waits on the teammates (its "Open items"). Paid: D01, A03 (A06 in the zip)
and C36 were missing on 13 November; on 18 November the tracker shows C36 read in full (Ghassan).

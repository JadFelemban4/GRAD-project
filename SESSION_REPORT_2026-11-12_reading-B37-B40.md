# Session report — 11 to 12 November 2026: Jad reads B37 and B40 of his ten

Jad's learning session, begun on `JMF-2340550-merge-2026-11-11` and closed onto a new
branch, `JMF-2340550-Literature-review`, at his request. Nothing in the physics, the
data or the training changed; the work lives in the team's Notion tracker. New: this
report and `NEXT_SESSION_2026-11-12_reading.md`; edited: `CHECKPOINT.md` (item 11 and
Jad's line under "In progress"), `STATE_HISTORY.md` (part AT), `HISTORY.md`,
`team/jad.md`.

## 1. What was done

- **B37** (Scania, US 9,822,691 B2) and **B40** (GM, US 12,233,738 B2) were read with
  Jad in Dr. Hammam's order (`docs/literature/READING_METHOD.md`): the abstract and
  claim 1 first (a patent has no conclusion; claim 1 stands in for it), Jad set
  "Related?", then the description, then the evidence. Jad went through each passage
  in the PDF himself; the explanations were in Arabic, one idea per message.
- **The tracker as Jad left it** (read back from the table at the close):

| ID | Related? | Bears on our claim | Status | fields Jad filled |
|---|---|---|---|---|
| B37 | Yes | Prior art (does part of it) | Annotated, 11 November | Critical synopsis, Why (claim), Strengths and weaknesses |
| B40 | Unsure | Background only | Annotated, 11 November | Critical synopsis, Why (claim) |

- B40's "Unsure" is Jad's: it is related only if the battery plant (phase E, not
  started, `README.md` phase table) is built. Its "Background only" is Jad's choice;
  Claude had suggested "Prior art", since the list put B40 in as the industrial rule
  nearest to H/τ, so the review still has to name it.
- **What in those fields is not Jad's own wording.** B37's Critical synopsis carries
  a completion Claude wrote at Jad's request («كمل الملخص لا تحطه ناقص»), in his style,
  each addition listed to him before the close: that the tests the patent cites are
  about what damages the radiator, that the radiator cools the coolant with air, that
  the main aim is the radiator's own life, that the thermostat opens early and slowly,
  and "for every part" at the end. The second line of B37's Strengths and weaknesses
  is Jad's sentence, placed there on Claude's reading of his message; he kept it.
  Everything else in both rows is Jad's text, verbatim.
- **Left empty on both, by Jad's pace:** Specific finding (page), Evidence, Answer to
  Read it for (page), Contrary evidence, Original source, Leads to, Method, System
  studied, Current?.
- **B19's file** was fetched and rendered at the close; Jad chose to start B19 from the
  beginning in a new session.

## 2. Where things are in the two texts

Page pointers for the fields Jad left empty, so he can find the passage again. They
are **not a reading**: a field filled from this list instead of the text does not
count (`READING_LIST.md` rule 4). Pages are those of the tracker's PDF file.

B37, 20 pages, with a text layer:

- p. 12, step 201: the look-ahead stretch "can be, for example, 0.5 km, 1 km or 2 km
  long", one stretch for every component, predicted at 1 Hz (or 0.1 or 10 Hz). The
  text gives no rule for choosing it.
- p. 12, step 202: the components whose temperature is predicted, "a turbocharger
  device" among them.
- p. 11: "Tests have shown" that the number of strain changes is what harms the
  radiator; no test is described. FIG. 3 to 5 are "non-limitative" examples. The
  patent holds no measured data.
- p. 11: the object is the radiator's life (fewer large thermostat swings), not only
  component limits.
- p. 13: a limit of 4 °C/s on the coolant's rate of rise, in one embodiment.
- p. 16: pre-cooling builds a buffer; a turbocharger limit of about 125 °C needs
  coolant at about 90 °C and 400 l/min. That is a coolant-side temperature, and the
  text does not say which part of the turbocharger; it is not the temperature the
  project protects (the turbine side: the exhaust-gas limit is 1223 K on the B58,
  `engine_env.py`). Mistake 23.
- p. 18: the claims.

B40, 15 pages, a scan:

- p. 1: the abstract. p. 13 and 14: claim 1. p. 14: claim 7, delay preconditioning
  when the estimated travel time is greater than the predicted preconditioning time.
- p. 13, column 15: the worked example, about one hour to precondition with the
  charger about 2.25 hours away, so the start waits one hour to an hour and a quarter;
  30 minutes away, it starts at once and is amplified.
- p. 3 to 5: the three drawing sheets are a block diagram, a cell sketch and the
  method's flow chart. The example's words are "approximately" and "may". No
  measured data.
- Against H/τ: it compares the time to arrival with the battery's thermal time to
  decide when to start, for one component and one aim (charging speed). It does not
  ask whether knowing the route is worth having.

## 3. Found and left alone (tools)

- The Read tool cannot render a PDF on this PC (no `pdftoppm`). `pdftotext`, from
  Git's `mingw64`, reads a PDF with a text layer (B37).
- B40 and B19 are scans with no text layer: `pdftotext` returns nothing. Their pages
  were rendered to PNG with PyMuPDF (`fitz`, in the user site of
  `C:\Users\admin\Python3132`, so run with `-P`) and read as images. The script and the
  files stayed in the session's scratchpad.
- Notion's SQL query returned an empty Reader for all ten, although every page shows
  Reader = Jad (set in the app). Query by ID; a fetch of the page is right. The last
  report found the same for files.

## 4. How the reading went

- After the first check question Jad asked for none: he writes back what he
  understood, and Claude confirms or corrects it. Setting a field is his decision, not
  a quiz.
- When Jad asks Claude to complete his notes, the words added are in his style and
  listed for him.
- What landed and what did not, with the examples: `team/jad.md`, 11 to 12 November.

## 5. Checks at the close

- `python verify_docs.py`: read by its exit code, see the close commit.

## 6. Next

B19 from the beginning, then B18, B06, B31, A25, B49, C20 and C18:
`NEXT_SESSION_2026-11-12_reading.md`. Waiting on Jad, as in the last report: readers
for the other 40; C48 and C61 from a browser; the housing-lag exporter's port
(`CHECKPOINT.md` item 4); the paid D01, A03 and C36.

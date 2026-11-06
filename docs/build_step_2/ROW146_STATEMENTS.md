# Row 146's two statements, for the B58 study across H only (signed 6 November 2026)

Rows 146 and 147 of `results/VALIDATION_DECISIONS.md` (section R, the B58 study of row 107 (2)) need two
written statements signed by Ghassan before the study trains: row 147 (13). Each statement holds for the
B58 study across H only. Each is cited and disclosed in its preregistration,
`results/PREREGISTRATION_B58H.md` (ORDER step 20, PR-B). Neither changes `CLAUDE.md` for any other
experiment, and neither changes row 111's two statements, which hold for the four-engine test of decision
24 only (`docs/build_step_2/ROW111_STATEMENTS.md:5-7`). The two statements below are the two of the
question Ghassan answered on 6 November 2026, set out to be signed: the bold text of each is his
question's words, under a sentence that names its scope. The lines marked "Disclosed" are the agents'
disclosures, written under each statement as row 111's (ii) carries row 127's sentence; they add no
condition to what he signed. Drafted by the AI agents on 6 November 2026.
From 31 October Ghassan works alone (row 133), so each statement counts once Ghassan's column is filled.

## (i) Rule 2, amended for this study

> For the B58 study across H only (row 107 (2); rows 146 and 147), rule 2 of `CLAUDE.md`'s rules for an
> experiment that will be reported ("Train from a clean, pushed commit whose `train.py` and
> `fingerprint.py` are `main`'s") reads instead: **training runs from the commit the study's
> preregistration names.**
>
> Disclosed:
> - Rule 2's own "clean, pushed" is kept: the commit is clean and pushed, as rule 2 already requires.
>   The statement replaces only "whose `train.py` and `fingerprint.py` are `main`'s"; Q2 (i) did not
>   mention the rest of rule 2, which this file therefore leaves as it is.
> - Today `main` is `cf43fbb`, X1's plant, and `main` stays X1's plant until drive C's stage C. On
>   `GRA-test`, `train.py` and `fingerprint.py` differ from `main`'s by 416 and 279 changed lines
>   (MEASURED on 6 November 2026: `git diff --stat main GRA-test -- train.py fingerprint.py`).
> - The preregistration is `results/PREREGISTRATION_B58H.md`. The commit it names, `T*`, is its own
>   commit, the one that adds it, as X1 trained from its preregistration's own commit
>   (`results/PREREGISTRATION_X1.md:355`). It is found by
>   `git log --diff-filter=A --format=%H -- results/PREREGISTRATION_B58H.md`.
>   `T*` is checked out on the training device, with `git status --porcelain` printing nothing, before
>   the pilot and before the training (row 146 (6)), and the training waits for the pilot's commit
>   (row 147 (3)).

## (ii) Gate item 6, waived for this study

> For the B58 study across H only, the training gate's item 6 ("Drive C (knock), before drive A", which
> puts drive C before any training) is waived. **The study trains before drive C, and every result is
> reported with and without the knock term** (gate item 3).
>
> Disclosed:
> - The untested knock model enters the primary, no-knock reading too: through the B58's E8 band, κ
>   3.4226 (section Q.2; row 107 (4)), the baseline ECU's spark under boost, which drive C would test.
>   Reporting both readings therefore does not cover everything drive C would have tested.
> - Every with-knock number carries the label "not converged in dt on these roads" (row 101): on decision
>   34's roads the dt 0.5 s repeat moves the B58's hand-written (a) at r = 1.5 by +1.1735 points with
>   knock, against −0.0035 without (`results/EPA_ROADS/roads.json`, `report.dt_repeat`).
> - The training reward is without the knock term (Ghassan's answer Q4 of 6 November; row 147 (3)).
> - The B58 that is trained and scored is X1's plant `cf43fbb`, frozen for this study (decision 31):
>   plant_sha 865f8e7b7e5c2dbe until the plant commit P (ORDER step 14), whose code edits move the
>   plant_sha while the B58 stays identical at its defaults (its engine_sha 023f5589215ee68e unchanged
>   and the B58 identity certificate L1-L7 re-run; rows 94, 117 and 127 (6)).
> - A stage-C retune enters only after scoring, as decision 31 says of new drives.
> - The training gate was agreed by Jad and Ghassan (`CLAUDE.md`, the Training gate); this waiver is signed
>   by Ghassan alone (row 133).

## Signatures

| statement | Ghassan | Jad |
|---|---|---|
| (i) rule 2 amended for this study | signed 6 Nov 2026: his own answer "Sign both (Recommended)" to the question below, recorded by the agents | not filled (row 133 (1)) |
| (ii) gate item 6 waived for this study | signed 6 Nov 2026: the same answer | not filled (row 133 (1)) |

The question as it was asked on 6 November 2026, and Ghassan's answer, which the agents record as his
signature of both:
"The training gate was agreed by you and Jad, so the B58 study needs two statements signed by you: (i)
training runs from the commit the study's preregistration names; (ii) the study trains before drive C
(gate item 6 waived for this study only), and every result is reported with and without the knock term.
Do you sign both?" -> "Sign both (Recommended)".

His answer of the same day to the question before it ("Run 2 dropped all three EPA engines, so the
four-engine test is off. Row 107 (2) already says a B58-only study across H runs instead, as exploration,
never a test of H/τ; a null result is the expected outcome. Your standing instruction was written for the
four-engine test. Does it also cover this B58 study, so I keep deciding its route for you?" -> "Yes, it
covers it (Recommended)") makes row 133 (2)'s standing instruction cover the study's other choices
(section R's note): every choice of rows 146-147 that is not one of his answers Q2-Q4 is the agents'
recommendation adopted under it, among them the readings of gate items 1 and 5 for this study (row 147
(13)), which are not part of the two statements above. This file is committed with rows 146 and 147
(D146), before any agent of the study trains. `CLAUDE.md`'s brackets on gate items 5 and 6 should say
that item 6 is waived for this study too, citing this file, and that `results/PREREGISTRATION_B58H.md`
is item 5 for it; that edit is Ghassan's (row 133 (4)).

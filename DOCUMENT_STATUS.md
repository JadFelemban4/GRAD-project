# Which documents still carry void numbers

Checked 8 September 2026, after the engine-geometry correction, by extracting
the text of every PDF in the project folder and searching for figures that are
no longer true.

**Nothing here is a code problem.** The repository is correct and everything in
it regenerates. These are the team-facing PDFs and decks produced before
8 September. They are listed so nobody quotes them into the thesis or hands one
to the supervisor without knowing what is stale.

---

## The four figures that went void on 8 September

| void figure | what replaced it |
|---|---|
| premise 527.2 / 356.8 / 198.7 | **829.2 / 548.6 / 437.6 / 548.6** |
| premise 52.7 / 29.9 / 27.8 / 29.9 | same — that set was the four-cylinder |
| "10 of 11 quantities inside band" | **8 of 11** |
| load residual 9.8 %, then 4.4 % | **2.3 % over 17 points** |
| turbine τ 39.5 s | **48.0 s** |
| "2.0 L turbo I4" / "inline-four" | **3.0 L B58B30O1 inline-six, 2997.5 cc** |

---

## Documents affected

| document | what is stale in it |
|---|---|
| `Consistency_Audit.pdf` | old premise numbers, "10 of 11", τ = 39.5 s |
| `Supervisory_Engine_Tuner.pdf` | old premise numbers **and describes the plant as a 2.0 L turbo I4 throughout** |
| `What_To_Do_In_Order.pdf` | old premise numbers |
| `Slide_By_Slide_Team_Brief.pdf` | old premise numbers |
| `Project_Vocabulary.pdf` | one worked example uses a 2.0 L engine |

Checked and **clean**: `Roles_And_Lessons.pdf`, `Team_Working_Model.pdf`,
`Roadmap_Two_Plants.pdf`, `Novelty_Statement.pdf`, `Logging_Channel_Reference.pdf`,
`Preview_Worth_Proposal.pdf` and its team variant, `Project_Proposal_5.pptx`,
`موجز_المشروع_للفريق.pdf`.

---

## What to do about it

**Do not patch the numbers by hand.** Regenerate from the scripts when the
document is next needed — that is the whole point of `validate.py`,
`check_premise.py` and `verify_docs.py` existing.

`Supervisory_Engine_Tuner.pdf` is the one to prioritise if any of these goes to
the supervisor. It is the technical description of the plant, and it describes
the wrong engine from beginning to end.

`Project_Vocabulary.pdf` is the least urgent: its 2.0 L reference is a generic
worked example of BMEP, not a claim about this vehicle. Worth a footnote saying
so rather than a rebuild.

---

## The trap that was next door

Until 8 September there was a **second, stale copy of the entire codebase** in
the folder where these PDFs are built — `plant.py`, `thermal.py`,
`engine_env.py`, `check_map.py`, `check_premise.py`, `validate.py` and
`generality_test.py`, all still carrying `n_cyl = 4`.

Any document regenerated from that folder would have silently reintroduced the
four-cylinder. The copies have been synchronised with this repository.

**The repository under `build/engine-supervisor/` is canonical.** If you find a
`.py` file outside it, check it against the one in here before running it.

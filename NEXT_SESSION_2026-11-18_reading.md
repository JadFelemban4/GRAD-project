# Next session — on the PC, B49, Jad's last paper (written 18 November 2026)

Jad moves the reading back to the PC: the laptop's work of 16 to 18 November is committed and pushed. This
file replaces `NEXT_SESSION_2026-11-16_reading.md`. Jad opens the session with a line like «أنا جاد، اسحب
الفرع واقرأ NEXT_SESSION_2026-11-18_reading.md»: that line answers CLAUDE.md's first rule (who you are
talking to).

## 0. Before the first reply

1. `git fetch origin`, switch to `JMF-2340550-Literature-review`, `git pull`: the commit that adds this file
   must be there.
2. Read `CLAUDE.md`, `team/jad.md` (follow it all session), `docs/literature/READING_METHOD.md` (Dr.
   Hammam's method; its last section describes the tracker) and
   `SESSION_REPORT_2026-11-16_reading-B31-A25.md` (how B31 and A25 went, and what Jad wrote).
3. Check that the Notion tools are loaded. If they are missing, say so before anything else (on 16 November
   Jad had to reconnect the connector: `/mcp`, or claude.ai, Settings, Connectors).
4. `python verify_docs.py`, in the lock's environment (`grad-venv-lock-3.13.2` in Jad's user folder,
   `CHECKPOINT.md`, "Files outside git"). The laptop could not run it, so the close of 18 November is
   unchecked. Ask Jad first whether the PC is still training: the check takes CPU. Tell him the result in one
   line. If it flags the new review files, change their wording, never the guard.

## 1. Where the reading stands

The tracker: the Notion database "Literature Tracker · متتبع الأوراق" (under the GRAD Project Dashboard),
data source `collection://3b224093-a84e-459e-8801-ed312f744055`. Query a row by `"userDefined:ID"`.

- Done: B37, B40, B19, B18, B06, B31 and A25.
- C20 and C18 went to Mohammed (the teammates asked; Jad agreed).
- **B49: next, and Jad's last** (section 2).
- **The Status column:** on 18 November no row reads "Annotated"; the seven Jad set so read "Read in full"
  (the report, section 1). Before setting B49's Status, ask Jad which option the team now uses.

## 2. B49: Laguna et al. 2022, Energy Reports 8, 10193-10202

"Dynamic horizon selection methodology for model predictive control in buildings". Notion page
`4159ef597fcf81c89696cd535a98d390`; Theme L4 Horizon rules; free full text. Its "Read it for", as the row has
it on 18 November (re-read it from the row): "How the thermal-inertia period is read off the ARX lag order and
whether it is a time constant in the C/UA sense, so the review does not equate it with the housing's τ."

Fetch the page with `include_file_urls` and download the PDF at once (the links expire in 5 minutes), into
its own new scratchpad folder. Nothing of it has been read, and there are no notes from Claude: start from the
abstract and the conclusion, as for every paper.

Why it matters: it sits beside A25, a horizon chosen from a building's thermal behaviour, and on the team's
map it is in Jad's kind of study, computer simulations. If Jad relates it, his section
(`docs/literature/review/computer-simulations.md`) and the team's draft may gain a sentence, in his words
and with his approval only.

## 3. What Jad wrote, and where it is

- `docs/literature/review/computer-simulations.md`: his section of the team's review (B18, B31, B06, A25),
  approved 17 November.
- `docs/literature/review/preview-in-vehicles.md`: his section by theme, of 17 November (another session's;
  all three paragraphs approved).
- His own review, in English, a Claude Doc: https://claude.ai/artifact/DEXHXuT7sZxqVQsiZvBs8k (revision 15).
- The team's draft, a Claude Doc, IEEE [1]-[33]: https://claude.ai/artifact/SdVgmBW53zLCquoTdHJ3uh
  (revision 11). Its "Open items" are for the teammates.
- Before editing either doc, read it from its last revision (`sinceRev`): Jad or a teammate may have edited it.
- A25's synopsis in the tracker ends with Jad's reading from before the methodology (control on "a part of
  the house"); he kept his first words. Do not change it; if A25 comes up, say it once.

## 4. The method (unchanged)

For each paper, one step at a time: the abstract and the conclusion first (a patent has none: claim 1 stands
in for it), and Jad sets "Related?"; then the methodology; then the evidence and the rest. Explain in Arabic,
a familiar example first, one idea per message, the passage quoted with its page. Do not end with a check
question: Jad writes back what he understood, and you confirm or correct it. If he does not understand,
change the example and cut the numbers; do not repeat. He goes through the text himself; the fields hold his
words (type what he says, never your own summary). If he asks you to complete his notes, write in his style
(الي، انو، ف، ح), show him the text before it goes in, and list exactly what you added. After each paper, help
him set "Bears on our claim" with the reason (against H/τ) and the theme, and ask him before moving "Status"
on.

Two additions from 16 to 18 November (`team/jad.md`): when he asks about a whole text, explain all of it
briefly in one message; and when you explain his own writing back to him, give each point with what is in his
notes beside it ("القسم يقول" / "في ملاحظاتك"). A line Claude wrote and he approved is "in your notes", never
"you wrote". `team/jad.md` asks for the `/i-have-adhd` skill; the laptop did not have it: check whether the PC
does, and follow `team/jad.md`'s rules either way.

## 5. Tools

- On the PC, PyMuPDF is in `C:\Users\admin\Python3132\python.exe` (run it with `-P`); `pdftotext` comes with
  Git for Windows (`/mingw64/bin/pdftotext` in Git Bash). The Read tool cannot render a PDF without
  `pdftoppm`.
- Put each download in its own new scratchpad folder and any script outside it; run Python that reads them
  with `-I`.
- On the PC, curl to Notion's file host failed inside the sandbox ("Empty reply from server") and worked with
  the sandbox off; on the laptop it worked inside.
- The Notion connector can fail mid-write (ECONNRESET, "Internal server error"): read every write back before
  telling Jad it is saved.
- Write Arabic as characters, never as `\u` escapes.

## 6. Rules (Jad's, verbatim)

Write only in the columns, never in a page body (the workspace is at Notion's free block limit). Never put the
brain's content in Notion or in this public repo. Never write to the car's ECU; never run train.py without my
yes. Commit by explicit path; push only where I name it, naming the destination back first. Reply in Arabic.

## 7. At the close («قفلنا»)

1. A session report, `SESSION_REPORT_<date>_reading-B49.md`, on the pattern of 18 November's.
2. `CHECKPOINT.md` item 11: rewrite it, and move the old text verbatim to the end of `STATE_HISTORY.md` as a
   new part (AV was 18 November's). Never append.
3. `HISTORY.md`: index the report and the next prompt.
4. `team/jad.md`: the entry for the session.
5. The next prompt under a new name: never overwrite a file Jad has been handed.
6. `python verify_docs.py`, in the lock's environment.
7. Commit by explicit path, never `git add -A` (another session may share a tree). Push only where Jad names,
   naming it back first; his branches are `JMF-2340550-*`, never `main`.
8. A short summary to Jad, in Arabic.

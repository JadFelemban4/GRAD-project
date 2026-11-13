# Next session — reading prompt, from B31 (written 13 November 2026)

Paste the block below into a new Claude Code session opened in the repository.

```
Repository: C:\Users\admin\Documents\graduation project\GRAD-project (BSc project, UJ;
public repo JadFelemban4/GRAD-project). Read CLAUDE.md first and follow its first rule:
ask who you are talking to ("مين معي؟ / Who am I talking to?"), then read their file in
team/ (Jad -> team/jad.md) and follow it. Branch: JMF-2340550-Literature-review.

This is a learning session. Task: carry on reading my 10 papers (Reader = Jad) in the
team's Notion database "Literature Tracker · متتبع الأوراق" (under the GRAD Project
Dashboard). B37, B40, B19 and B18 are done (Annotated). B06 is read, with two loose
ends: (1) its Critical synopsis was approved but the Notion write failed at the close
and could not be read back: check the cell, and if it is empty, tell me and I will paste
the text; (2) its Status is still "Not started": ask me. Then start B31, then A25, B49,
C20, C18. Read first: docs/literature/READING_METHOD.md (Dr. Hammam's method; its last
section describes the tracker) and SESSION_REPORT_2026-11-13_reading-B19-B18-B06.md (how
the last three went, and the page pointers).

For each paper: take its PDF from the tracker's "PDF file" column (fetch the page with
include_file_urls; the links expire in 5 minutes), then one step at a time: abstract
and conclusion first (a patent has none: claim 1 stands in for it), and I set
"Related?"; then the methodology; then the evidence and the rest. Explain in Arabic, a
familiar example first, one idea per message, the passage quoted with its page. Do not
end with a check question: I write back what I understood, and you confirm or correct
it. If I do not understand, change the example and cut the numbers; do not repeat.
I go through the text myself; the fields hold my words (type what I say, never your
own summary). If I ask you to complete my notes, write in my style (الي، انو، ف، ح),
show me the text before it goes in, and list exactly what you added. After each paper,
help me set "Bears on our claim" with the reason (against H/tau), the theme, and ask me
before moving "Status" on.

Tools on this PC: the Read tool cannot render PDFs (no pdftoppm). A PDF with a text
layer: pdftotext (Git's mingw64). A scan: render the pages to PNG with PyMuPDF,
C:\Users\admin\Python3132\python.exe -P (fitz is in its user site), and read the images.
Put each download in its own new scratchpad folder and the script outside it. curl to
Notion's file host fails inside the sandbox ("Empty reply from server"); it works with
the sandbox off. The Notion connector can fail mid-write: read every write back before
telling me it is saved. Notion's SQL may show Reader empty: query by ID.

Rules: write only in the columns, never in a page body (the workspace is at Notion's
free block limit). Never put the brain's content in Notion or in this public repo.
Never write to the car's ECU; never run train.py without my yes. Commit by explicit
path; push only where I name it, naming the destination back first. Reply in Arabic.
```

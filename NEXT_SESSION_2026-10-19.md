# Prompt for the next session — written 19 October 2026, after drive C's first attempt and the proposal's evaluation

Paste the block below into a fresh Claude Code session opened at the repository root.

```
Repository: C:\Users\admin\Documents\graduation project\GRAD-project
(GitHub JadFelemban4/GRAD-project, public). Branch: JMF-2340550-driveC-check,
unless Jad pushed today's work to main.

First, before anything else, ask who you are talking to (CLAUDE.md, "Before
anything else"): «مين معي؟ / Who am I talking to?». Then open their file in
team/ and follow it for the whole session. For Jad (team/jad.md): Arabic first,
one small idea per message, a familiar example before the project, never a
void figure. The /i-have-adhd skill is not installed here: follow its rules
by hand.

Read first, in this order: CLAUDE.md, CHECKPOINT.md,
SESSION_REPORT_2026-10-19_driveC-and-evaluation.md, then the files the task
names.

State on 19 October 2026:
- Drive C's first attempt (Ghassan, night of 18-19 October) covers neither C1
  nor C2: logs/DRIVE_C_CHECK_2026-10-19.md, printed by drive_c_check.py. It was
  checked blind: nobody has computed the retard. The six CSVs are on Jad's
  machine (C:\Users\admin\Downloads\2026-10-19), outside logs/raw/ on purpose.
- Ghassan will drive C2 and C1 again, in the warmest hours available (the summer
  heat is over; section 8), once the rule's numbers are fixed.
- The proposal's evaluation: both evaluators accept; Evaluator 2 asks for four
  corrections. docs/supervisor/2026-10-19_proposal-evaluation.md (the workbook
  stays outside the repository). The team has moved to the research track, and
  plans in Notion (GRAD Project Dashboard, gates G0-G9, 12 October to 23
  November).
- verify_docs.py: 74 of 74.

The next task, CHECKPOINT.md "Next actions" item 1: drive C's ten rule numbers
(logs/DRIVE_C_CHECK_2026-10-19.md, section 9). Propose a value for each, with
its reason, one number per message for Jad; Jad and Ghassan fix them. Do not
change logs/DRIVE_PLAN.md's numbers yourself, and compute no retard on the
19 October logs before the numbers are fixed.

If Jad picks the evaluation instead: CHECKPOINT.md item 2, one correction at a
time (section 4 of the evaluation file); Jad's first answers and the verdicts
are its section 8.

Rules that matter here:
- Never write to the car's ECU; read-only OBD-II logging only.
- Never run train.py without Jad's permission; train.py is Ghassan's file.
- Use C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe with
  PYTHONIOENCODING=utf-8 (the project .venv is blocked on this machine).
- Adding a drive to logs/raw/ and running build_dataset.py re-derives the plant:
  only with Jad's and Ghassan's yes.
- Run verify_docs.py before quoting a number; read it by its exit code.
- Commit by explicit path (another session may share this folder); push only
  where Jad names it, and name the destination back to him first. The
  repository is public: the evaluation file carries the scores.
- Never copy content from Jad's second brain into this repository.
- Every finding goes into a tracked file before the session ends.
```

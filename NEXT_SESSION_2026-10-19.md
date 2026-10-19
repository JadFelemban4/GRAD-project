# Prompt for the next session — written 19 October 2026, after drive C's first attempt and the proposal's evaluation

Paste the block below into a fresh Claude Code session opened at the repository root.

```
Repository: C:\Users\admin\Documents\graduation project\GRAD-project
(GitHub JadFelemban4/GRAD-project, public). Branch: main.

First, before anything else, ask who you are talking to (CLAUDE.md, "Before
anything else"): «مين معي؟ / Who am I talking to?». Then open their file in
team/ and follow it for the whole session. For Jad (team/jad.md): Arabic first,
one small idea per message, a familiar example before the project, never a
void figure. The /i-have-adhd skill is not installed here: follow its rules
by hand.

Read first, in this order: CLAUDE.md, CHECKPOINT.md,
SESSION_REPORT_2026-10-19_driveC-and-evaluation.md,
SESSION_REPORT_2026-10-19_driveC-rule.md, then the files the task names.

State on 19 October 2026:
- Drive C's first attempt (Ghassan, night of 18-19 October) covers neither C1
  nor C2: logs/DRIVE_C_CHECK_2026-10-19.md, printed by drive_c_check.py. It was
  checked blind: nobody has computed the retard. The six CSVs are on Jad's
  machine (C:\Users\admin\Downloads\2026-10-19), outside logs/raw/ on purpose.
- Drive C's rule is AGREED (decisions 14-23, 7ad649c; results/DRIVE_C_RULE.md)
  and coded (drive_c_analysis.py, stages A/B/C; Ghassan's session report
  SESSION_REPORT_2026-10-19_driveC-rule.md). Ghassan repeats C2 and C1 in the
  warmest hours available (logs/DRIVE_PLAN.md).
- The proposal's evaluation: both evaluators accept; Evaluator 2 asks for four
  corrections. docs/supervisor/2026-10-19_proposal-evaluation.md (the workbook
  stays outside the repository). The team has moved to the research track, and
  plans in Notion (GRAD Project Dashboard, gates G0-G9, 12 October to 23
  November).
- verify_docs.py: 74 of 74.

The next task, CHECKPOINT.md "Next actions" item 1: stage A, blind, on the
18-19 October files, which are on THIS machine (Ghassan's is not). Follow the
item exactly (logs/drive_c/, never logs/raw/; python drive_c_analysis.py
stage-a ...); ask Jad, or Ghassan through him, which files go as --c2 and
which as --c1. Never run stage B or C, and never compute target minus actual,
outside the rule's own order.

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

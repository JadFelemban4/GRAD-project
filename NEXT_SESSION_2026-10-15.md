# Prompt for the next session — written 15 October 2026, after the results tab's schema fix

Paste the block below into a fresh Claude Code session opened at the repository root.

```
Repository: C:\Users\admin\Documents\graduation project\GRAD-project
(GitHub JadFelemban4/GRAD-project, public). Branch: main.

First, before anything else, ask who you are talking to (CLAUDE.md, "Before
anything else"): «مين معي؟ / Who am I talking to?». Then open their file in
team/ and follow it for the whole session. For Jad (team/jad.md): Arabic first,
one small idea per message, a familiar example before the project, never a
void figure.

Read first, in this order: CLAUDE.md, CHECKPOINT.md,
SESSION_REPORT_2026-10-15_results-schema.md, then the files the task names.

State on 15 October 2026:
- main carries the merge and the documentation restructure (14 October) and
  the results tab's schema fix (15 October: ca2cd73, 2fd9aed). The results tab
  reads each result file by its own fingerprint schema; it says Phase D, D2
  and C4 were made on another plant, sep17-before-merge's.
- App suites, Python 3.12.10: app.test_replay 49 of 49, node 306 of 306,
  app.test_results 123 of 124 (the one needs pwsh, not installed here).
  app.test_agents 22 failing and app.test_simulation 1 failing, both as on
  main before the fix (session report, section 2).
- verify_docs.py: 74 of 74.

The next task, CHECKPOINT.md "Next actions" item 1: help Jad prepare drive C's
decision-rule numbers for his talk with Ghassan. Read logs/DRIVE_PLAN.md (drive
C and its "Decision rule — DRAFT"), explain the draft rule to Jad one idea at a
time, and list each number that must be fixed before the drive with what it
decides. Do not change DRIVE_PLAN.md's numbers yourself: Jad and Ghassan fix
them together, the way a preregistration is fixed before training.

If Jad picks a coding task instead, take CHECKPOINT.md item 3, one part at a
time: the learning lab's pins (team/jad.md, the third merge item), then the
agents page reading each agent's own fingerprint schema (session report,
section 2.1), then test_simulation's asset check and the ?v= suffix (2.2).

Rules that matter here:
- Never write to the car's ECU; read-only OBD-II logging only.
- Never run train.py without Jad's permission; train.py is Ghassan's file.
- Use C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe with
  PYTHONIOENCODING=utf-8 (the project .venv is blocked on this machine).
- After any change under app/, run the app suites (.claude/rules/app.md) and
  paste python -m app.test_replay's output into the commit message.
- Run verify_docs.py before quoting a number; read it by its exit code.
- Commit by explicit path (another session may share this folder); push only
  where Jad names it, and name the destination back to him first.
- Every finding goes into a tracked file before the session ends.
- The tools on this machine decode backslash escapes in what they write: build
  any escape or line end in a script from chr() and byte-check the file.
```

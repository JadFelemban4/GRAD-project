# Next session — prompt (written 30 October 2026)

Paste the block below into a new Claude Code session opened in the repository.

```
Repository: C:\Users\admin\Documents\graduation project\GRAD-project (BSc project, UJ;
public repo JadFelemban4/GRAD-project). Read CLAUDE.md first and follow its first rule:
ask who you are talking to ("مين معي؟ / Who am I talking to?"), then read their file
in team/ (Jad -> team/jad.md) and follow it.

State: branch JMF-2340550-anatomy-housing, four commits on cf43fbb (de7d083, cc5dc24,
dc08498, fe35cc6) plus the close-of-session commit: the learning lab's first Anatomy
figure (lesson housing_lag), figures and the turbo model on the tour's stage, and a
project map of all 58 concepts. Ask Jad whether it was pushed before assuming either.
Read CHECKPOINT.md and SESSION_REPORT_2026-10-30_learning-lab-figures.md.

Task (Jad's choice): a quality check of the whole code with the ponytail skills.
Use /ponytail-audit (a one-shot report that changes nothing). REPORT ONLY: fix
nothing in this session unless Jad asks for a specific item afterwards.
- Scope it before reading: a full read of every tracked file costs about a quarter of
  Jad's usage (team/jad.md). Propose the order to Jad and let him cut it: the physics
  and training core (plant.py, thermal.py, engine_env.py, derived.py, train.py,
  fingerprint.py, evaluate.py), then app/, then Explanatory Simulation/, then the
  scripts. Subagents, if any, run on Opus (memory: workflow agents need Opus).
- Findings go in a tracked file, not the chat: AUDIT_PONYTAIL_2026-10-<day>.md, each
  finding with file:line, the failure in plain words, and how sure you are. Mark
  which findings are already known: docs/MISTAKES.md, AUDIT.md, AUDIT2.md,
  CHECKPOINT.md, Explanatory Simulation/docs/HOUSING_LAG_VALIDATION.md ("Found,
  not fixed") and CONCEPT_MAP_VALIDATION.md.
- Known before you start: the lab's tests already fail on main (Python 4, Node 1;
  stale pins from before the 8 October plant change), and app.test_agents has 22
  failing (CHECKPOINT.md). Report them as known, not as new.

Rules that matter: never write to the car's ECU; never edit data/, logs/raw/ or
validation_table.md by hand; never run train.py without Jad's yes; "a wrong number
means the code or the document is wrong, not the checker"; Python 3.12 (the system
interpreter if .venv is blocked: memory, machine traps). Commit by explicit path;
push only where Jad names, naming the destination back first. Reply to Jad in
Arabic, one idea at a time (team/jad.md).
```

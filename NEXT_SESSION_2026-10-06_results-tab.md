# Prompt for the next session — after the results tab, milestone R1a (6 October 2026)

Paste the block below into a new session. It assumes nothing from earlier chats.

```
Repository: C:\Users\admin\Documents\graduation project\GRAD-project (Windows; use Git Bash).
Branch: JMF-2340550-results-tab. It holds the results tab, milestone R1a, complete and
reviewed; it was NOT pushed unless Jad said so at the end of the last session (check
`git status -sb` and `git log --oneline -5`). Base branch: main.

First, as CLAUDE.md says: ask who you are talking to ("مين معي؟ / Who am I talking to?")
and follow their file in team/. For Jad: Arabic first, one idea per message, the next
action first, English terms on their own line.

State: /results in the lab (python -m app.server --simulation, or app\start-simulation.ps1)
shows Jad's three evaluation experiments (Phase D, D2, C4), rebuilt from results/ on every
open, with plant state, quoted verdicts, notes and two interactive charts, Arabic and
English. Final checks on f5a93cc: app.test_results 120 OK, app.test_simulation 15 OK,
app.test_replay 49 of 49, node 236 pass, app.test_agents at its pre-R1a baseline (no new
failing entry), verify_docs all 73 pass, drift_test 16 of 16.

Read first:
1. docs/superpowers/plans/2026-10-05-results-tab-r1a-review-notes.md: the 23 rulings made
   on Jad's behalf (with their costs) and 73 deferred minor findings. It is R1b's
   starting list.
2. docs/superpowers/specs/2026-09-30-results-tab-design.md: the approved design; its
   section 10 defines R1b and R2, and its last section is R1a's build record.
3. CLAUDE.md (the first box) and team/jad.md.

Next task: R1b, Ghassan's set (results/agents/terrain_dt1) on the tab: analyse_agent_set.py
and its committed capture, the posthoc: anchors in app/agent_catalog.py, the agent-set
reader, the pairs chart both ways, the figures the spec lists, the incomplete box, the two
provenance lines, the record fold. Start with superpowers:writing-plans from the spec's
R1b section, folding in the review notes; ask Jad before anything that changes scope.

Also owed to Jad, one per message, when he has a moment: (1) Ghassan's draft branch
origin/GRA-2340394 (its .mjs MIME fix and reconstructed certificates; five decisions for
Jad); (2) the installed i-have-adhd skill is the old version ("Five items ranked beats ten
unranked"); his profile asks for the updated one.

Rules that matter:
- Never write to the vehicle's ECU; read-only OBD-II only.
- Push only to Jad's own branch (JMF-2340550-*), naming the destination, and only when he
  approves that push. Never main.
- Another Claude session works in this same folder (CLAUDE.md, handoff.md, team/,
  NEXT_SESSION_*.md, PROMPT_AUDIT*): commit by explicit path only; never stash, reset,
  checkout or add -A.
- Never edit plant.py, thermal.py, engine_env.py, random_road.py, fingerprint.py, train.py,
  evaluate.py, run_phase_d.py; never run train.py without Jad's permission; never write
  under results/ or runs*/.
- Machine traps: the Write tool decodes a typed backslash-u escape into the literal
  character (write such files through Python, byte-check them); the Bash tool collapses a
  doubled backslash; Python's write_text writes CR LF here (use write_bytes); .venv is
  blocked, use C:/Users/admin/AppData/Local/Programs/Python/Python312/python.exe with
  PYTHONIOENCODING=utf-8.
- Usage limits: Fable subagents exhaust their quota in minutes; give subagents an explicit
  model (opus for judgement, sonnet for checks). Parallel opus review workflows hit the
  session limit twice in the last session.
- After updating, press Ctrl+F5 once on the lab pages (a browser may keep the old
  i18n.mjs and show nav.results).
```

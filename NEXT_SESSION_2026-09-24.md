# Next session — 24 September 2026, after C4

Paste the block below as the first message of the next session. It was checked
before commit by three read-only reviewers (facts, traps, completeness), each
finding challenged by a second. **If a number here disagrees with a script, the
script is right** — re-run it and fix this file.

```
You are picking up a BSc graduation project the day C4 produced its result.
Three preregistered ablations of the preview channel now exist -- Phase D,
Phase D2 and C4 -- and the next experiment is a TEAM DECISION not yet made.

Branch: JMF-2340550-sep17. Confirm with `git rev-parse --abbrev-ref HEAD`,
and `git status --short` should print nothing.

READ FIRST, IN THIS ORDER
  team/          run `git config user.email` and read the matching profile
                 BEFORE explaining anything. For endo.felemban@gmail.com (Jad):
                 Arabic first, one small idea per message, a familiar example
                 before the project, English terms on their own line, invoke
                 /i-have-adhd and keep it on. Statistics are NOT covered for
                 him: explain before asking.
  CLAUDE.md      the "Current state -- 24 September 2026 (after C4)" box at
                 the top.
  CHECKPOINT.md  the LAST entries (23-24 September, and the SESSION CLOSE
                 index). They index everything below.
  results/PREREGISTRATION_C4.md   sections 2 and 2a (the explanations and
                 the six readings, fixed before training), 5b (convergence),
                 5c (the budget-change test), 6a (the run log), 11 (outcome).

THE STATE IN ONE PARAGRAPH
C4 is Phase D2's design at 300 000 steps per run instead of 50 000 -- ONE
variable changed, by Jad's rule ("one at a time, otherwise we cannot tell which
one was the cause"). Every C4 agent retraced its D2 twin bit for bit through
50 000 steps (80 of 80), so C4 is D2's agents trained longer -- and for that
reason NOT an independent replication of D2 (C4 limit 11). Result: SMALLER THAN
THE MEI by the primary sign test (7 of 8 seeds below 50 damage units,
p = 0.0352) -- but the permutation test DISAGREES (p = 0.3867), because seed 0
carries +360.6: already D2's outlier (+221.7), it widened because its blinded
agent got WORSE with longer training. By the preregistered rule the agents were
NOT CONVERGED (2 of 8 sighted, 1 of 8 blinded, 1 of 8 pairs settled). The
budget-change test (5c) did not reject (p = 0.6367). The spread did not shrink
(sd 139.9, D2 98.8). No agent refuses torque.

    python analyse_c4.py       C4 beside D2 and Phase D (results/C4_RESULT.txt)
    python power_analysis.py   the C4 section: the planning figures below

THE SENTENCE THAT MAY BE SAID, fixed before C4 trained (section 2a):
  "Preview's effect is below the MEI at 300 000 steps: (i) is supported AT
  THIS BUDGET. The agents were still changing, so (ii) is not ruled out."
  (i) = preview genuinely buys little at this configuration -- which reads
  "with one grade step per episode" (section 2, row iii). (ii) = the agents are
  undertrained. Always with: it hangs on one seed; the sensitivity test
  disagrees; the agents did not converge; it is the third unadjusted look.
  NEVER "preview does not help".

========================================================================
THE ONE OPEN DECISION -- JAD'S (AND THE TEAM'S), NOT THE SESSION'S
========================================================================
What next? By Jad's rule it changes ONE variable relative to C4 and gets its own
preregistration BEFORE anything trains. On record (PREREGISTRATION_C4.md
section 2, Jad, 23 Sep): more seeds only after C4, and only if C4 leaves the
question open. C4's cell is not INCONCLUSIVE, but it is one seed wide and not
converged -- whether that counts as "open" is part of the question to put to
him. Present the options, with these figures, and recommend nothing he has not
asked for.

  A. A LONGER BUDGET, seeds 0-7, as FRESH runs from step 0 in a NEW --out.
     C4's agents cannot be continued: runs_c4 is closed, and every C4 run has
     resume_allowed False. Up to 300 000 steps the new agents would BE C4's
     (training is deterministic), so A tests the same agents older.
     For: the agents were still changing. Recorded in 6a: several agents took
     MORE practice damage at 300 000 steps than at 200 000 (blinded seed 0:
     538.8, 589.5, 694.5). One untested reading, in no preregistration: SAC at
     a constant learning rate (3e-4) may not settle by the 5b rule at any
     budget -- set beside the measured one-step noise floor (max 7.9 per agent).
     Cost, if linear in steps: C4 took 882 min for sixteen 300 000-step runs at
     up to ten concurrent -- about 4.9 h per 100 000 steps of the WHOLE budget.
     So 600 000 steps ~ 29 h, 1 000 000 ~ 49 h, plus ~3 h to score. Keep the
     budget <= 1 000 000 or set --buffer, or the replay buffer starts to evict
     and becomes a second variable. Longer runs cross more Windows Update
     windows.
  B. MORE SEEDS at 300 000 steps -- NEW seeds only (e.g. --seeds 8 9 ... on
     BOTH the training and the --evaluate launch; the default is 0-7).
     Retraining seeds 0-7 would reproduce C4 bit for bit. A new seeds
     experiment is reported BESIDE C4, never pooled with C4's eight, unless its
     preregistration declares a sequential design with its alpha adjustment
     BEFORE training (pooling after seeing C4 is adding seeds to C4, which its
     section 7 forbids). For: the result hangs on one seed.
     Planning figures -- `python power_analysis.py`, C4 section, normal
     approximation, ORDER OF MAGNITUDE ONLY: at C4's spread, 80 % power
     against 50 units needs about 80 seeds per arm (power is not monotonic
     just above it); without seed 0 the spread is 45.1 and the need about 11.
     So the true need lies somewhere between, depending on whether seed 0 is
     typical -- which is what B would find out. Never a reason to drop seed 0.
     Cost: runs go in waves of ten, ~7.5 h per wave; 42 seeds per arm ~ 3 days,
     80 per arm ~ 5-6 days of continuous training, plus scoring (80 min per
     eight seeds) and checks. One extra pair alone is ~4.3 h, not the batch
     average of ~1.8 h.
  C. NO FOURTH ABLATION NOW: finish Chapter 4 on the three results and turn
     the machine to the next phase (E, the battery plant; or F, the H/tau
     sweep). Costs no compute; leaves (ii) and the one-seed question open, and
     says so in the thesis.

The profile's order for this conversation: one idea per message -- what C4
found; why one seed matters (a familiar example first); what "not converged"
means; then A, B, C -- each with one check question. Give him the sentence he
may repeat to a supervisor, and the one he may not. Then ask which.

========================================================================
THE TOOLS ARE SAFE -- AND HOW TO LAUNCH ANY NEW EXPERIMENT
========================================================================
Closed on 23-24 September (f987049, hardened by two reviews BEFORE it was
committed, and the close commit of 24 September):
  - train.py refuses to resume at a different --steps; reads the step count
    from the ZIP, not the file name; refuses new seeds or --extend inside the
    CLOSED experiments; holds a RUNNING mark; saves atomically; --no-resume
    forbids any resume.
  - run_phase_d.py never relaunches over final.zip; appends logs; derives the
    result prefix from --out; refuses a dirty tree and HOLDS its queue while
    the tree is dirty; refuses work in closed experiments; restarts a crash
    only with --seeds <k> --restart-crashed, never a live run.
  - CLOSED experiments: runs/, runs_d2/, runs_c4/ (train.CLOSED,
    run_phase_d.CLOSED_OUT) and the result prefixes phase_d, d2, c4
    (run_phase_d.CLOSED_PREFIX), compared case-insensitively. Every future
    experiment is added to all three tables once its result exists.
  - evaluate.py never overwrites a result file without --overwrite. It does NOT
    know which prefixes are closed: score ONLY through run_phase_d.py
    --evaluate.
  - The agents exist only on this machine (gitignored). Backups, sha-checked:
    graduation project/GRAD-agent-backups/2026-09-23/{runs, runs_d2, c4_probe}
    and 2026-09-24/runs_c4 (587 files). Never delete or move anything under
    runs/, runs_d2/ or runs_c4/.

For the next experiment, in order:
  1. its own --out in lowercase (e.g. runs_c5), ADDED TO .gitignore in the
     preregistration commit, checked with `git check-ignore -v runs_c5/x` --
     otherwise its LAUNCH.txt dirties the tree and the launcher holds forever;
  2. its own analysis script that IMPORTS the statistic (as analyse_c4.py
     imports analyse_phase_d2.classify), and its own convergence and identity
     checks: check_c4_convergence.py and check_c4_start.py are C4-ONLY
     (checkpoints 200k/250k/300k, C4_STEPS, seeds 0-7, twin runs_d2) -- copy
     and adapt them, never edit them; C4's record depends on them;
  3. its preregistration, committed before any agent trains;
  4. a dry-run on the committed, clean tree, recorded in its run log;
  5. the launch as a DETACHED process, so closing the session cannot stop it.
     C4's, from PowerShell (PREREGISTRATION_C4.md 6a):
       Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments
         @{CommandLine='cmd.exe /c "set PYTHONIOENCODING=utf-8&& set
         PYTHONUNBUFFERED=1&& C:\Users\admin\AppData\Local\Programs\Python\
         Python312\python.exe run_phase_d.py --road random --steps <N>
         --out <dir> > <dir>\launcher_train.log 2>&1"';
         CurrentDirectory='<repo>'}
     The log goes INSIDE the gitignored --out.
  6. While ANY run is still queued, create or edit NO file in the repository --
     untracked files count too. The last wave may start hours after launch.

========================================================================
SMALLER, RECORDED
========================================================================
  - thesis/CHAPTER4_ABLATION_DRAFT.md: the title and opening summary still say
    "Phase D and Phase D2 ... INCONCLUSIVE in both"; the 4.8 explanations table
    and 4.9 limits table have no C4 column; section 4.10's C4 paragraphs were
    added AFTER the reviewed draft -- review them, and give C4 its own section
    beside 4.3 and 4.5.
  - capture `python check_d2_tracking.py --out results/d2_tracking.txt`
    (~40 min, D2's agents) so Chapter 4 cites a file -- before any launch, or
    after the last wave has started.
  - app/alerts.py VALID_MAP_HI is 74 in code against the 30-75 kPa span (an
    app threshold moves only for a measurement); the deck tabulates 13 of the
    18 mistakes; a later reviewed commit could make evaluate.py refuse
    closed prefixes itself.

DO NOT
  - Do not add seeds to Phase D, D2 or C4 (each preregistration's section 7).
  - Do not change two variables at once (Jad's rule).
  - Do not say "preview does not help"; do not rescue a result with H/tau
    (PREREGISTRATION.md limit 8); do not read "the agent beats current-grade"
    as "preview helps" (AUDIT.md C3) -- and on the worst episode about half do
    not beat it (C4: 4 of 8 sighted, 5 of 8 blinded worse than its 907.0).
  - Do not drop seed 0, or treat the permutation test as primary because it
    disagrees; section 5 fixed that both are reported and the sign test leads.
  - Do not change the CODE of plant.py, thermal.py or engine_env.py (all three
    are plant_sha), random_road.py (road_sha), or evaluate.EPISODES /
    EPISODES_D2 (episodes_sha): any of them locks out every trained agent in
    runs/, runs_d2/ and runs_c4/, and makes a next experiment differ from C4 in
    more than one variable. Comments and docstrings are safe.
  - Do not write to the vehicle's ECU. Read-only OBD-II only.

MACHINE TRAPS ON JAD'S PC
  `python` resolves to the project .venv, which Windows Application Control
  blocks -- use /c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe
  with PYTHONIOENCODING=utf-8. Never put a scratch script directly in %TEMP%.
  Workflow subagents need model 'opus' and a scratchpad scriptPath. Shell
  heredocs can turn "\n" escapes into real newlines -- patch Python through a
  script file, then parse-check it. verify_docs.py reads `git ls-files`: STAGE
  new files before running it or it will not scan them. Windows Update was
  never confirmed paused (active hours end 03:00).

HOUSE RULES
  - Read every exit code in its own variable: `python x.py; echo $?`.
  - Run verify_docs.py before every commit that carries a figure; after
    reworking verify_docs.py itself, run drift_test.py (16 of 16).
  - After changing the reward, env, plant or scenario, run test_reward.py (and
    `--road random`); after changing anything under app/, run app.test_replay
    and app.test_simulation.
  - Every finding goes into a tracked file before the turn ends.
  - Push to JMF-2340550-sep17, not main.

WHAT THE SCRIPTS PRINTED, AND WHEN (exit 0 each)
  24 Sep  analyse_c4.py           C4: 3 of 8; below-MEI sign p 0.0352, perm
                                  0.3867 (disagree); SMALLER THAN THE MEI;
                                  NOT-CONVERGED; 5c p 0.6367
  24 Sep  power_analysis.py       C4 section: power 0.15 at 8 seeds; 176 units
                                  for 80 %; ~80 seeds per arm; ~11 without seed 0
  24 Sep  check_c4_convergence.py NOT-CONVERGED sighted 2/8 blind 1/8 pairs 1/8
  24 Sep  check_c4_start.py       IDENTITY compared 80 identical 80
  24 Sep  check_d2_tracking.py runs_c4   0 of 16 agents track torque >1 pt worse
  24 Sep  verify_docs.py          All 67 checks pass
  23 Sep  check_c4_convergence.py --calibrate   one gradient step: max 7.9 per
                                  agent, 8.5 per pair; D2 30k-50k median 118.2
  23 Sep  drift_test.py           16 of 16 drifts CAUGHT
```

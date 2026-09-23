# Prompt for the next session — written 23 September 2026, after Phase D2

Paste the block below into a fresh Claude Code session. Accurate as of the
commit that adds this file on `JMF-2340550-sep17`, the close of the 22–23
September session. If a number here disagrees with a script, **the script is
right** — run it. Before it was committed, this prompt was checked by three
read-only reviewers (facts, traps, completeness); every valid finding is in it.

---

```
You are picking up a BSc graduation project the day after Phase D2 produced
its result. Both ablations -- Phase D and Phase D2 -- are INCONCLUSIVE at the
C1 training budget. Jad has DECIDED the next experiment: C4.

Branch: JMF-2340550-sep17. Confirm with `git rev-parse --abbrev-ref HEAD`.

READ FIRST, IN THIS ORDER
  CHECKPOINT.md      the LAST entry, "Session of 22-23 September 2026", is the
                     index: the result, what was found, who decided what, and
                     what is open. Start there.
  CLAUDE.md          the current-state box at the top (Phase D2) and the live
                     list under "What to do next". Read `team/` first and match
                     `git config user.email` to a profile before explaining
                     anything. For endo.felemban@gmail.com: Arabic first, one
                     small idea per message, invoke /i-have-adhd and keep it on.
  results/PREREGISTRATION_D2.md   the design C4 inherits, its ten limits, the
                     run log (section 6a) and the outcome (section 11).

THE STATE IN ONE PARAGRAPH
Phase D2 re-ran the preview ablation on a randomised climb (start 120-300 s,
grade 12-16 % per episode) so the blinded arm could not memorise the road --
check_random_road.py verified it is blind. Result, preregistered with a
minimum effect of interest of 50 damage units: 4 of 8 seeds, sign p = 0.6367,
INCONCLUSIVE. The seed spread halved (sd 214.4 -> 98.8), against the
preregistered prediction. Supervision beats current-grade on 8 of 8 seeds,
blind agents included. No agent refuses torque (check_d2_tracking.py).

    python analyse_phase_d2.py     both experiments, side by side, in seconds

THE DECISION, AND ITS RULE -- Jad, 23 September
  The next experiment is C4: D2's design at 300 000 steps per run instead of
  50 000 -- about 66 training climbs per agent against 11.
  ONE VARIABLE AT A TIME, in Jad's words: "ولا كذا ما نعرف مين السبب، فنسويهم
  واحد واحد عشان نقدر نحدد" -- otherwise we cannot tell which one was the
  cause, so we do them one at a time. C4 first. More seeds is a SEPARATE,
  later experiment with its own preregistration, and only if C4 leaves the
  question open. Never both at once.

========================================================================
FIRST, BEFORE ANYTHING TRAINS: DISARM THE TRAPS. Verified at close.
Both agent directories are BACKED UP (23 Sep, 184 + 189 files, checked):
    graduation project/GRAD-agent-backups/2026-09-23/{runs, runs_d2}
Do not rely on the backup instead of the fix.
========================================================================
  TRAP 1 -- IRREVERSIBLE. train.py RESUMES any run directory that holds a
  ckpt_*_steps.zip whose FATAL fingerprint matches, and `steps` is only an
  ADVISORY field. So `train.py --steps 300000 --road random` (default --out
  runs_d2/) resumes a D2 agent from 50 000 steps and overwrites its
  final.zip; and `train.py --steps 300000` with the fixed road (default --out
  runs/) does the same to a PHASE D agent. Worse than the overwrite:
    - run_phase_d.py opens <logs>/<tag>.log in 'w' mode at launch, so the old
      training logs are TRUNCATED the moment a run starts -- even if it is
      killed seconds later;
    - a resumed run never rewrites meta.json, so the agent would carry a
      50 000-step certificate for a 300 000-step model;
    - a resumed run is not a fresh C4 run: no replay buffer contents (the
      checkpoints save none), a 50 000-slot buffer that WOULD evict (SAC.load
      restores the old size), and the same road sequence replayed from the start.
  runs/ and runs_d2/ are gitignored: the agents exist only on this machine.

  TRAP 2 -- recoverable if caught before a commit. `run_phase_d.py --road
  random --evaluate` writes results/d2_seed<N>.txt (the prefix is hard-coded)
  and would overwrite D2's committed results. Run `git status results/` after
  any evaluation, before any commit.

  TRAP 3 -- a false clearance. check_d2_tracking.py hard-codes runs_d2/ and
  takes no arguments; run "for C4" it would re-inspect the D2 agents and print
  their clean limit-10 result.

  THE FIX, in the order to do it:
    a. train.py: REFUSE to resume when the stored steps_requested differs from
       the live one, unless an explicit --extend flag is given (add
       'steps_requested' to the refusal beside train_duration / train_dt,
       around train.py:273). This disarms runs/, runs_d2/ and every direct call.
    b. run_phase_d.py: never relaunch into a directory that holds final.zip
       (report and skip), and never open an existing log in 'w' mode. --out
       and --logs ALREADY exist (training can go to runs_c4/ today); what is
       missing is the evaluation result prefix (hard-coded 'd2') and the
       "next:" hint. Make the dry-run print the logs directory too.
    c. check_d2_tracking.py: take the runs directory as an argument.
    d. A NEW analysis script for C4 that IMPORTS analyse_phase_d2 -- do not
       edit analyse_phase_d2.py, which D2's preregistration pins at 8e91276.
    e. The fingerprint cannot tell a C4 agent from a D2 agent: same plant,
       scenario and episodes; only the advisory steps_requested differs, and
       evaluate.py prints "PHASE D2 EVALUATION" for both. So the C4 analysis
       must assert that each model's final.zip has num_timesteps == 300000,
       read from the zip itself, not from meta.json.
    f. Gitignore runs_c4/. Dry-run and confirm nothing points at runs/,
       runs_d2/ or results/d2_*. Test trap 1's guard on a COPY of one D2 run
       directory, never on the real one. Commit.

THE PLAN FOR THIS SESSION

  1. Disarm the traps above (a-f). Commit. About an hour.

  2. WRITE AND COMMIT results/PREREGISTRATION_C4.md BEFORE ANY TRAINING.
     Inherit from D2 unchanged: the randomised climb, seeds 0-7 per arm, the
     frozen set evaluate.EPISODES_D2 (hash 1c5d49852290d27c), the statistic
     (exact one-sided sign test, permutation sensitivity, alpha 0.05), the MEI
     (50 damage units), the three-cell rule, limits 3-10.
     Pin: the code commit, plant_sha b5a3069f32a83754, road_sha
     1a29dc46db24f233 -- and launch from a CLEAN tree.
     State what moves: --steps 300000, and the replay buffer with it (sized to
     the run, 300 000 slots, never evicting -- non-behavioural per
     prove_buffer.py).
     Rewrite limit 1 from D2's spread (power 0.24 against 50 at eight seeds,
     `python power_analysis.py`, D2 section) and say whether C4 shrinks the
     spread is a prediction to CHECK, not assume -- the last one was wrong.
     Replace limit 2 (the C1 budget) with C4's own budget limit.
     DECIDE IN ADVANCE, and write down:
       - how convergence is judged from curve.csv (e.g. the last N episode
         returns flat within a stated band), so a C4 null cannot be waved
         away as "maybe still undertrained";
       - what a C4 separation, and a C4 non-separation, would each mean for
         explanations (i) preview buys little and (ii) the budget;
       - the crash policy: a crashed run restarts FROM SCRATCH in a fresh
         directory with the same seed (a resume is not the same agent --
         trap 1), recorded in section 6a;
       - its own section 7: sixteen runs, then stop; no seed added after any
         C4 result is seen.
     C4 is reported BESIDE D2 and Phase D, never pooled with them.
     Check with `git log` that the commit exists before step 3.

  3. LAUNCH. Close other programs and turn off Windows sleep and updates for
     the run. The launcher computes its concurrency cap ONCE from free memory
     (min(cores, (free - 5.0) / 1.5)): read the "-> N at a time" line of the
     dry-run and pass --jobs if N is below 8. Arithmetic, from D2's records:
     71-81 min per 50 000-step run x 6 = about 7-8 h per C4 run; at 8-10
     concurrent that is two waves, about 16 h; at a cap of 5 it is 24-32 h.
     Re-measure one run's peak memory early -- PEAK_GB = 1.5 was measured with
     a 50 000-slot buffer. Then ~1.5 h of evaluation.

  4. WHILE IT RUNS -- the ablation chapter draft (Phase D and D2), both
     findings kept separate, each with the limits its preregistration
     declared, the failed spread prediction stated plainly.

  5. AFTER: the preregistered C4 test, beside D2 and Phase D; then the
     limit-10 torque check on the C4 agents (check_d2_tracking.py pointed at
     runs_c4/). Write it into CLAUDE.md, CHECKPOINT.md and results/ before
     ending.

  Recorded, not urgent: app/alerts.py VALID_MAP_HI is 74 in code against the
  30-75 kPa span (an app threshold moves only for a measurement); the deck
  tabulates 13 of the 18 mistakes.

DO NOT
  - Do not add seeds to D2 (its section 7) or, later, to C4 (its own).
  - Do not run C4 and more seeds together (Jad's rule above).
  - Do not say "preview does not help". Say "with agents trained to the C1
    budget, preview does not separate from seed noise (INCONCLUSIVE)".
  - Do not rescue a null with H/tau (PREREGISTRATION.md limit 8).
  - Do not read "the agent beats current-grade" as "preview helps" (AUDIT.md C3).
  - Do not edit the CODE of engine_env.py (moves plant_sha) or of
    random_road.py (moves road_sha, part of the FATAL scenario field) -- either
    locks out every trained agent of its experiment.
  - Do not write to the vehicle's ECU. Read-only OBD-II only.

MACHINE TRAPS ON JAD'S PC
  `python` resolves to the project .venv, which Windows Application Control
  blocks (pandas DLL) -- use
      /c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe
  with PYTHONIOENCODING=utf-8. Never put a scratch script directly in %TEMP%:
  a stray inspect.py there shadows the stdlib. Workflow subagents need
  model 'opus' and a scratchpad scriptPath.

HOUSE RULES
  - Read every exit code in its own variable: `python x.py; echo $?`.
  - After reworking anything in verify_docs.py, run drift_test.py (16 of 16)
    before committing -- mistake 11's fourth recurrence was in the guard.
  - After changing the reward, env, plant or scenario, run test_reward.py
    (and `--road random`) and paste the output into the commit.
  - After changing anything under app/, run app.test_replay and
    app.test_simulation.
  - Every finding goes into a tracked file before the turn ends.
  - Push to JMF-2340550-sep17, not main.

WHAT THE SCRIPTS PRINTED, AND WHEN (exit 0 each)
  23 Sep  analyse_phase_d2.py   D2: 4 of 8, sign p 0.6367, INCONCLUSIVE;
                                Phase D beside it, also INCONCLUSIVE (post-hoc)
  23 Sep  power_analysis.py     Phase D spread: power 0.10 vs 50;
                                D2 spread: 0.24, 80 % needs ~42 seeds per arm
  23 Sep  check_d2_tracking.py  0 of 16 agents track torque >1 point worse
  23 Sep  verify_docs.py        All 67 checks pass
  23 Sep  drift_test.py         16 of 16 drifts CAUGHT
  22 Sep  check_random_road.py  PASS -- 0 of 121 grades fail to bind; blind arm
                                blind (D2's pre-training gate)
  22 Sep  test_reward.py        4 of 4; --road random all five roads PASS
                                (D2's pre-training gate)
  22 Sep  app.test_replay 49 of 49; app.test_simulation 15 of 15 -- on the
          swept tree, recorded in commit 3f4627d
```

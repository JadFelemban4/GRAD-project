# Prompt for the next session — written 22 September 2026, after Phase D produced a null

Paste the block below into a fresh Claude Code session. Accurate as of commit
`4510f33` on `JMF-2340550-sep17`, the close of the 21-22 September session. If a number here disagrees with a script,
**the script is right** — run it.

---

```
You are picking up a BSc graduation project the day after Phase D produced a
result. The result is a NULL and that is not a failure.

Branch: JMF-2340550-sep17. Confirm with `git rev-parse --abbrev-ref HEAD`.
Last commit should be 4510f33 or later.

READ FIRST, IN THIS ORDER
  CHECKPOINT.md      the LAST entry, "SESSION CLOSE, 21-22 September", is the
                     index: what was done, what was found, who decided what,
                     and what is open. Start there.
  results/PREREGISTRATION.md   the experiment's rules, committed before any
                     agent was trained. Section 5 has an UNSET line.
  CLAUDE.md          the mistake log. Read `team/` first and match
                     `git config user.email` to a profile before explaining
                     anything. For endo.felemban@gmail.com: Arabic first, one
                     small idea per message, invoke /i-have-adhd and keep it on.
  AUDIT2.md          the second audit. Fixes 1 and 2 are DONE; fix 3 is not.

THE STATE IN ONE PARAGRAPH
Phase D ran. Sixteen agents, eight seeds per arm, on the corrected ZF plant,
under a preregistration committed before any of them started. Preview cannot be
shown to help: 5 of 8 seeds positive, mean +4.8 damage units, sign test
p = 0.3633, permutation p = 0.4922. The seed spread swamps the effect -- seed 3
says +387, seed 5 says -288. SEPARATELY and positively, the trained agent beats
the current-grade comparator by +29 to +34 points on five of eight seeds. Those
are two different claims; only the first was the hypothesis.

    python analyse_phase_d.py     reproduces all of it in seconds

AND THE BUDGET BELONGS WITH THE NULL. Every agent is a C1 agent -- 50 000
steps, which train.py itself calls "the first bad run", 11 training episodes.
A null from an undertrained agent and a null from a converged one are different
claims and 11 episodes cannot separate them. Write "with agents trained to the
C1 budget, preview does not separate from seed noise", NOT "preview does not
help". results/PREREGISTRATION.md limit 6.

WHAT TO DO -- ALL OF IT IN ONE SESSION. That is the team's decision, 22 Sep.

IT FITS BECAUSE THE SLOW PART RUNS IN THE BACKGROUND. Training and evaluation
are ~6 hours of CPU but need no attention once launched; the document sweep is
the foreground work and happens WHILE they run. Wall-clock is set by the
compute, not by the sum of the list. About 6-7 hours, one sitting.

  PHASE 1 -- DECIDE AND LOCK   (foreground, ~40 min, BLOCKS everything after)

  1. SET THE MINIMUM EFFECT OF INTEREST. TEAM DECISION. It goes into the new
     preregistration and also closes PREREGISTRATION.md section 5 for Phase D.
     Without it neither experiment can be written up: a null cannot be told
     apart from an underpowered study.

  2. WRITE AND COMMIT THE NEW PREREGISTRATION, BEFORE ANY TRAINING.
     The design is DECIDED -- results/NEXT_EXPERIMENT_DESIGN.md, "Decision":
         OPTION B. Start time uniform on [120, 300] s, grade uniform on
         [12, 16] %, drawn per episode, seeded so the twenty evaluation
         episodes are frozen. 130 km/h, 42 C. Eight seeds per arm, C1 budget.
     Nine of nine grades in 12-16 % are MEASURED to bind (weakest: 14 % at
     +12.7 K). The team's principle, recorded there: "our goal is not the
     highest result, our goal is to be realistic."
     Copy the statistic, test and alpha from PREREGISTRATION.md. Commit it.
     Check with `git log` that the commit exists before step 4.

  3. IMPLEMENT THE RANDOMISED ROAD. make_grade_climb() takes a per-episode
     draw of start and grade; reset() rebuilds the cycle from it. Then:
       - test_reward.py MUST still pass -- a changed scenario is a changed
         reward surface (CLAUDE.md mistakes 5 and 17). Paste its output into
         the commit.
       - verify the road now differs between resets: the check that found
         limit 7 printed "road identical across 3 resets: True". It must
         print False.
       - verify every drawn episode binds: peak > 850 C.
       - evaluate.EPISODES is FROZEN for Phase D. The new experiment needs its
         OWN frozen set that also freezes the road draw. Do not edit the old one.
       - fingerprint.py hashes the make_grade_climb defaults; the new scenario
         is a new plant fingerprint by design. That is correct -- it stops a
         Phase D agent being scored on the new road.

  PHASE 2 -- LAUNCH, THEN SWEEP WHILE IT RUNS   (~6 h wall-clock)

  4. LAUNCH TRAINING, then evaluation, in the background.
         python run_phase_d.py              (adapt the tag so runs do not
         python run_phase_d.py --evaluate    overwrite Phase D's in runs/)
     Memory-capped by measurement; ~5-6 concurrent on this machine. Expect
     ~3.5 h training and ~2.5 h evaluation. KEEP PHASE D's runs/ INTACT --
     they are the first experiment's evidence.

     <!-- RETIRED-OK: 829.2, 548.6, 437.6, 13.4 -- naming the void set IS the task -->
  5. WHILE IT RUNS -- SWEEP presentation/. 116 stale mentions, and it is what an
     examiner is shown: the void premise set (829.2 / 548.6 / 437.6 / 13.4) on
     more than a hundred lines. `verify_docs.py`'s KNOWN STALE ledger lists every
     one with its file and count. Rewrite from FULL_RUN.txt, not memory. Lower
     each ledger row in the same commit that sweeps its file.

  6. WHILE IT RUNS -- SWEEP THE REST. CLAUDE.md / README.md / handoff.md first
     (they still say the constraint does not bind; it binds by 34 K), then
     ABSTRACT.md and CONTROL_SCOPE.md, then the internal files.

  7. FIX generality_test.py line 81 -- info.get("mdot") is a key the env never
     emits, so the H/tau axis silently uses the assumed 112.5 g/s. Small, and
     it is the axis of the project's central experiment.

  PHASE 3 -- READ THE RESULT   (foreground, ~30 min, after 4 finishes)

  8. Run the preregistered test on the new experiment, exactly as
     analyse_phase_d.py does for Phase D -- and report BOTH experiments, whatever
     they say. If the arms separate, the fixed road was hiding the effect. If
     they still do not, the design flaw is ruled out and the next suspect is the
     training budget (C4).

  9. Write it into CLAUDE.md, CHECKPOINT.md and results/ BEFORE ending the
     session. Not in chat. Point at the file.

  NOT THIS SESSION: C4 (300 000 steps), and the Phase D chapter. Both depend on
  the result of step 8.

DO NOT RESCUE THE NULL WITH H/tau. "H/tau is below 1, so the null fits the
theory" was drafted on 22 Sep, checked, and refuted: "near 1" is nowhere in the
repo, and the project's only H/tau curve puts the LARGEST preview value near
0.6, which is where Phase D sits. PREREGISTRATION limit 8.

DO NOT
  - Do not add seeds. PREREGISTRATION section 7: sixteen runs, then stop.
    Adding seeds now, having seen the result, destroys the preregistration.
    More seeds is a SECOND experiment with its own preregistration, and both
    get reported.
  - Do not switch to a two-sided test because the one-sided one failed.
    <!-- RETIRED-OK: 11.7 -- naming the void figure IS the warning -->
  - Do not quote +11.7 or +7.5. Both are void; `results/void/README.md` says
    why, and verify_docs.py fails on "11.7 points" anywhere. (It no longer fails
    on ANY sighted-over-blinded margin: that shape guard was removed on 22 Sep
    because Phase D's legitimate results now print one. Commit a32f6e4.)
  - Do not read "the agent beats current-grade" as "preview helps". That
    conflation is AUDIT.md C3.
  - Do not write to the vehicle's ECU. Read-only OBD-II only.

A MACHINE TRAP ON JAD'S PC, found 22 Sep. If `python` resolves to the project's
.venv (`which python` -> .venv/Scripts/python), Windows Application Control
blocks a pandas DLL inside it and verify_docs.py dies with "ImportError: DLL
load failed ... An Application Control policy has blocked this file". THAT IS
NOT A DOCUMENT FAILURE, and its exit code 1 must not be read as one. Every run
this session used the system interpreter:
    /c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe
Check `which python` before trusting an exit code.

HOUSE RULES
  - Run `python verify_docs.py ; echo $?` and READ THE EXIT CODE in its own
    variable. A `python x.py | grep ... && git commit` chain tests the grep,
    not the script -- that happened in this session and produced one commit
    whose message claimed a green run that had failed.
  - Never edit data/ or validation_table.md by hand; regenerate them.
  - After changing the reward, the env, the plant or the scenario, re-run
    test_reward.py and paste the output into the commit message.
  - After changing anything under app/, re-run `python -m app.test_replay`
    AND `python -m app.test_simulation`.
  - Change one thing, re-run, write down what happened.
  - Push to JMF-2340550-sep17, not main.

WHAT EACH SCRIPT PRINTS TODAY (from FULL_RUN.txt, 21 Sep, all exit 0)
  build_dataset.py   295.0 min, 10 drives, 26 operating points, 30-75 kPa
  compare_log.py     fitted k 0.839 / 1.1 %, derived 1.4 %, PASS
  validate.py        8 of 11 inside the published bands
  check_premise.py   baseline 959.8 at 884 C, THE CONSTRAINT BINDS,
                     preview over current-grade -0.4 points
  test_reward.py     4 of 4
  app.test_replay    49 of 49, --full 59 of 59, peak 890.6 C
  app.test_simulation 15 of 15
  verify_docs.py     All 67 checks pass, exit 0
  drift_test.py      16 of 16 drifts CAUGHT
  analyse_phase_d.py the table above

TOOLS BUILT THIS SESSION, so you do not rebuild them
  fingerprint.py      plant provenance; evaluate.py refuses a mismatched model
  drift_test.py       the guard's own acceptance test, 16 injected drifts
  full_run.py         every script in one pass, with exit codes
  run_phase_d.py      training and evaluation, memory-capped by MEASUREMENT
  prove_buffer.py     proves the replay-buffer size changes nothing learned
  analyse_phase_d.py  the preregistered statistic, and nothing else
```

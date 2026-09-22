# Prompt for the next session — written 22 September 2026, after Phase D produced a null

Paste the block below into a fresh Claude Code session. Accurate as of commit
`a3a048e` on `JMF-2340550-sep17`. If a number here disagrees with a script,
**the script is right** — run it.

---

```
You are picking up a BSc graduation project the day after Phase D produced a
result. The result is a NULL and that is not a failure.

Branch: JMF-2340550-sep17. Confirm with `git rev-parse --abbrev-ref HEAD`.
Last commit should be a3a048e or later.

READ FIRST, IN THIS ORDER
  CHECKPOINT.md      last entry, 21-22 Sep, is the whole of what happened.
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

WHAT TO DO, IN ORDER

1. SET THE MINIMUM EFFECT OF INTEREST. TEAM DECISION, and it blocks the
   write-up, not the experiment. `results/PREREGISTRATION.md` section 5 says
   "TEAM DECISION — NOT YET SET". Until it is set, "preview does not help"
   cannot be told apart from "the experiment was too small to see it", and an
   examiner will ask which one you are claiming. Pick it from the measured
   seed-to-seed standard deviation, write the reasoning beside it, commit.
   `analyse_phase_d.py` prints a warning while it is unset.

2. FIX 3 — SWEEP THE DOCUMENTS. About a day. It is the last of AUDIT2's top
   three and everything is prepared for it:
     - `python verify_docs.py` prints a KNOWN STALE ledger, ~195 mentions over
       ~85 rows, each with the file, the figure, the exact count, the exact
       stale values and the AUDIT2 finding. THAT LEDGER IS THE WORK LIST.
     - `FULL_RUN.txt` is a transcript of every script run in one pass on
       21 September, each block opening with its exit code. Rewrite from it,
       not from memory. Regenerate with `python full_run.py`.
     - When a file is swept, LOWER ITS LEDGER ROW IN THE SAME COMMIT. The
       checker fails if a row shrinks, on purpose.
   Priority order, by who reads the file:
     <!-- RETIRED-OK: 829.2, 548.6, 437.6, 13.4, 294.2, 812 -- naming the void
          figures IS the work list -->
     a. presentation/  — 116 mentions, and it is what an examiner is shown. It
        ships the void premise set (829.2 / 548.6 / 437.6 / 13.4) on more than
        a hundred lines with no warning.
     b. CLAUDE.md, README.md, handoff.md — 26 mentions. They say the constraint
        "no longer binds" and quote 294.2 at 812 C. The script prints 959.8 at
        884 C and the constraint BINDS by 34 K. This is the sharpest one: it is
        not a stale number, it is the opposite of the truth on the question the
        whole experiment turns on.
     c. ABSTRACT.md, CONTROL_SCOPE.md — 7 mentions. The abstract handed to the
        supervisor understates the dataset by 40 %.

3. WRITE THE PHASE D CHAPTER. The null is the result. Say both findings, keep
   them separate, and quote the limits from PREREGISTRATION section 8 -- they
   were declared before the numbers, which is what makes them limits rather
   than excuses.

DO NOT
  - Do not add seeds. PREREGISTRATION section 7: sixteen runs, then stop.
    Adding seeds now, having seen the result, destroys the preregistration.
    More seeds is a SECOND experiment with its own preregistration, and both
    get reported.
  - Do not switch to a two-sided test because the one-sided one failed.
  - Do not quote +11.7 or +7.5. Both are void; `results/void/README.md` says
    why, and verify_docs.py fails on any sighted-over-blinded margin.
  - Do not read "the agent beats current-grade" as "preview helps". That
    conflation is AUDIT.md C3.
  - Do not write to the vehicle's ECU. Read-only OBD-II only.

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

# Prompt for the next chat -- Ghassan's branch, 29 September 2026 (SUPERSEDED)

> **SUPERSEDED BY THE MERGE, 30 September 2026. Do not paste this into a new
> session.** It was `NEXT_CHAT_PROMPT.md` on `JMF-2340550`; the merge renamed it
> to this dated file (Jad's branch uses dated `NEXT_SESSION_*` files and had
> deleted `NEXT_CHAT_PROMPT.md` on purpose). Four of its sentences were wrong
> and are corrected below, as Ghassan accepted in his reply to the merge
> review. What is current: `CLAUDE.md`'s first box, and `conflict.md`.

Copy everything inside the fence into a new Claude Code session opened in
`C:\Users\badcl\Desktop\GRAD-project`. Written 29 September 2026.

---

```
Continue the BMW B58 graduation project. Read CLAUDE.md first — it is the
handoff and the mistake log, and its FIRST current-state box (29 September) is
current. Then handoff.md (the short entry point) and SESSION_REPORT_2026-09-29.md
(the last session in full).

WHERE THINGS STAND (branch JMF-2340550, committed 29 September)

1. PHASE D HAS ITS FIRST RESULT. Twenty agents (train_all.py): seeds 0-9,
   sighted and blinded, 50 000 steps each, a new road every episode, 130 km/h,
   dt 1.0, on the plant derived from the logs. Scored on evaluate.py's twenty
   frozen episodes (results/phase_d_130kmh.txt):
     - all twenty beat every hand-written policy; sighted median cut 67.9 %,
       blinded 65.4 %, current-grade 43.4 %;
     - THE ABLATION: sighted minus blinded +1.2 points, 95 % CI -4.4 to +6.8,
       exact Wilcoxon p = 0.43, n = 10 -- INCONCLUSIVE under the MEI rule
       (sign-test power 0.26 against 50 units; corrected 30 Sep, was "no
       measurable preview value");
     - blinded seed 6 does more damage than the baseline on the five episodes
       with the lowest weight on component life.

2. MOST OF THE AGENTS' MARGIN RESTS ON THE UNTESTED KNOCK MODEL. Every agent
   advances spark 3.5-4 deg past the baseline, and stops at the +4 deg ACTION
   BOUND, which happens to sit below the knock knee (corrected 30 Sep).
   knock_margin.py re-scores them with that advance forbidden: median cut
   ~41.6 %, below current-grade; 9 of 20 still beat it (a lower bound -- an
   agent trained without the lever could do better). Drive C (knock,
   logs/DRIVE_PLAN.md) is now the most valuable drive.

3. EVERY AGENT IS DOCUMENTED in results/agents/<set>/<agent>/: config, curve,
   policy weights, eval_summary.json; set READMEs with every table, figures.
   The per-step records (train_record.npz, eval_record.npz) are GITIGNORED by
   the team's decision and live only on the training machine beside runs/.

4. SETTLED: the fuel is 95 RON (what the model runs). The GPU does not help
   (the plant is 84 % of a training step; measured, train.py's docstring).

5. THE TEAM RETRAINS AFTER EVERY NEW DRIVE, because a drive re-derives the
   plant (derive_params.py). The routine is in CLAUDE.md, "When a new drive CSV
   arrives". Move runs/terrain_dt1/ aside first. (On this branch train.py
   resumed any checkpoint it found there; the merged train.py refuses a resume
   whose plant, dt, device or budget differ -- corrected 30 Sep.)

DO THESE, IN THIS ORDER
1. git status; run verify_docs.py and read its total.
2. ASK THE USER which drive comes next: C (knock -- now the most valuable), A
   (sustained climb: the oil rows and the coolant law) or another. Every drive
   must log Ambient temperature (logs/DRIVE_PLAN.md).
3. (DONE 30 September.) The merge with JMF-2340550-sep17 had 15 conflicted
   files, 7 of them code, and was resolved hunk by hunk as agreed in
   conflict.md -- not "toward" either branch. sep17's engine_env.py had the
   ZF 8HP51 since 27e720c (19 Sep); the six-speed sentence was wrong.
4. The boost ceiling is 9-20 % low at 1600-2000 rpm against drive B (mistake
   22). Admitting drive B's transient full-throttle readings into the envelope
   would raise it: a plant change, so it goes with the next retrain. Ask.

WHEN A DRIVE ARRIVES
   python new_drive.py <file>; build_dataset.py (re-derives the plant);
   compare_log.py, model_vs_data.py, validate.py, check_premise.py,
   test_reward.py, check_roads.py; then the retrain: train_all.py (~4 h, all
   CPU cores), record_agents.py runs/terrain_dt1, run_results.py phase_d,
   knock_margin.py, make_figures.py, make_page.py; verify_docs.py.

HOUSE RULES THAT ARE NOT NEGOTIABLE
- The car is read-only. Nothing is ever written to its ECU.
- Run verify_docs.py before quoting any number. Never edit its expected values
  to make a check pass -- only for a measured change, with the reason beside it.
- A sentence that carries a number needs the run that printed it (mistake 22).
  On the results page every figure is a token (make_page.py).
- Never edit logs/raw/, data/ or data/derived_params.json by hand.
- No fitted number typed into a module where the data can set it: derive it
  (derive_params.py) or say why it cannot be derived (REFERENCES.md 4b).
- The twenty evaluation episodes never change. Diagnostics (knock_margin.py)
  run BESIDE them, never instead of them.
- After changing the env, the plant, the gearbox, the reward or the roads:
  test_reward.py AND check_roads.py, output in the commit message.
- After changing plant.py or thermal.py: validate.py and validation_table.md
  in the same commit.
- After any change under app/: python -m app.test_replay.
- Count READINGS, not rows. Cite nothing from memory. One change at a time.
- Every comparison gets a figure.
```

---

## Files the next session should read, in order

| file | why |
|---|---|
| `CLAUDE.md` | the handoff, the mistake log, the improvement plan. Current-state boxes at the top |
| `handoff.md` | what to run first and what each command prints today |
| `SESSION_REPORT_2026-09-29.md` | the retrain, the knock margin, the corrections of mistake 22 |
| `results/agents/terrain_dt1/README.md` + `KNOCK_MARGIN.md` | every agent, every table |
| `results/phase_d_130kmh.txt` | the frozen-episode scores, with their caveats |
| `SESSION_REPORT_2026-09-28_evening.md` | drive B, the derived constants, the oil node |
| `logs/DRIVE_PLAN.md` | the drives still worth making, and how |
| `REFERENCES.md` | where every number comes from; section 4b, constant by constant |
| `AUDIT.md` + `AUDIT_FIXES.md` | the 15 September review and what was done about it |

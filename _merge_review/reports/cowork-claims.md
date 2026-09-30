# cowork-claims -- the co-work plan of 29 Sep 2026, checked claim by claim

Agent label: cowork-claims. Written 29-30 Sep 2026 (+03:00). Nothing in MERGE
("To main") or in GRAD-project was modified; only read-only git was used there.
All runs were made in copies under scratchpad/work/cowork-claims/.

Paths used below:
- JAD = scratchpad/trees/jad (tip 086c519), GHASSAN = scratchpad/trees/ghassan (tip 74de99a), BASE = f6b46e9
- MERGE = "C:/Users/admin/Documents/graduation project/To main"
- REPO = "C:/Users/admin/Documents/graduation project/GRAD-project" (read-only: reflog, runs*/meta.json, final.zip copied out)

## One line

The co-work plan's facts are mostly right (C3, C5, C6, C8-C12 hold; C1/C2 hold as push counts),
but three things are wrong or too strong. (1) "The main result is firm" is not: under Jad's
preregistered MEI rule Ghassan's ablation is INCONCLUSIVE, and C4 hangs on one seed. (2) "Jad's
agents probably do the same" is now measured: all 48 of Jad's agents push spark to the +4 deg
bound on the climb. Taking that lever away drops C4's margin over current-grade from +15.7 to
-1.2 points on one frozen episode. (3) "Half a day" for P1 is far too short: 91 hunks, 5 827
conflicted lines, 96 stale dataset figures in 21 files, plus a fingerprint that cannot see
Ghassan's data-derived constants.

## What I read, and what I did not

- Read in full: ghassan_commits.txt (all 15 messages); GHASSAN NEXT_CHAT_PROMPT.md; GHASSAN logs/DRIVE_PLAN.md;
  GHASSAN results/agents/terrain_dt1/KNOCK_MARGIN.md and README.md; GHASSAN knock_margin.py docstring;
  JAD AUDIT2.md Part 6 and Part 4a (lines 249-386); JAD results/C4_RESULT.txt; JAD PREREGISTRATION_C4.md
  sections 1-5a (lines 1-240); JAD CHAPTER4 sections 4.7 and 4.9 (lines 289-410); the conflict hunks of
  MERGE engine_env.py, thermal.py, .gitignore.
- Read in part (targeted greps and sections): both CLAUDE.md, both engine_env.py, train.py, evaluate.py,
  thermal.py, JAD fingerprint.py, app/agent_*.py, team/*.md, JAD CHANNEL_CENSUS.md, GHASSAN
  results/thermal_calibration.json, eval_summary.json and config.json of all 20 of Ghassan's agents,
  jad_commits.txt (subjects of the 28-29 Sep commits).
- Not read: the other ~380 added files, the binaries, jad_commits.txt in full (421 KB). This is a
  claims check, not a cover-to-cover read of both trees.

## Measurements I made (new, not in the orchestrator's logs)

1. **spark_probe** (scratchpad/work/cowork-claims/jad/spark_probe.py, output spark_probe_all.json).
   This is Jad's unmodified tree. Its live plant_sha is b5a3069f32a83754, the same as the meta.json of
   every agent in runs/, runs_d2/ and runs_c4/. Each of Jad's 48 agents ran one frozen episode:
   EPISODES[0] for Phase D, EPISODES_D2[0] for D2 and C4. The probe recorded the applied spark trim
   (env.prev_act[0], after slew and clip) and the knock integral on the climb (grade > 2 %). Sanity
   check: the neutral action on the Phase D episode scores 959.8, which is check_premise's baseline.

   | set | agents | climb spark-trim p50 (deg; bound +4.0) | KI p95 on climb | baseline (neutral) KI p95 |
   |---|---|---|---|---|
   | Phase D (runs/) | 16 | 2.82 .. 3.95, median 3.84 | 0.680 .. 0.788 | 0.610 |
   | D2 (runs_d2/) | 16 | 3.14 .. 3.95, median 3.81 | 0.703 .. 0.772 | 0.599 (ep 0) |
   | C4 (runs_c4/) | 16 | 3.22 .. 4.00, median 3.98 | 0.705 .. 0.785 | 0.599 (ep 0), 0.639 (ep 3) |

   C4 agents spend 43-96 % of climb steps at a trim of 3.9 deg or more (blind_seed0: 5.7 %).
   Ghassan's agents do the same (GHASSAN results/agents/terrain_dt1/*/eval_summary.json: climb trim
   p50 3.47-3.98). The damage knee is 0.85 (engine_env.py:510 JAD, :641 GHASSAN). Both branches bound the
   spark trim at +4.0 (ACT_HI, engine_env.py:514 JAD, :645 GHASSAN). The agents sit against that
   **action bound**, and the bound happens to fall just under the knee.

2. **Knock cap on C4** (probe_cap/, tab_cap.py). This follows Ghassan's knock_margin.py rule: spark trim
   capped at the neutral (0 deg), retard still allowed. It was run on the one frozen episode EPISODES_D2[0]
   (baseline 2122.2, current-grade 907.0 = 57.3 % cut):
   - median margin over current-grade: **+15.7 points as trained, -1.2 with advance forbidden**
   - 8 of 16 still beat current-grade
   - capped KI p95 is 0.605-0.627, the baseline's level

   This is one episode, not the 20-episode protocol, and the agents never trained with the cap
   (out of distribution). It points the same way as Ghassan's 20-episode diagnostic (+24.4 -> -1.8;
   9 of 20).
3. **Jad's guard on Ghassan's data** (jad_on_gdata/, verify_docs_jad_on_gdata.log). I ran JAD's
   verify_docs.py on JAD's tree with GHASSAN's data/manifest.csv, master_points.csv,
   master_samples.csv and driveB log copied in. Result: **"10 of 67 checks failed"**, and **96**
   document mentions in 21 files are WRONG:
   - by figure: 39 total-minutes, 25 drive counts, 10 pinned-sample counts, 9 ceiling-drive counts,
     5 quasi-steady counts, 5 sample-drive counts, 3 charge-temperature gap (3.8 % against 1.9 %,
     because JAD's guard does not exclude driveB's assumed-ambient rows)
   - by file: CLAUDE.md 13, validation_table.md 13, presentation/index.html 10, REFERENCES.md 7,
     README.md 7, CHECKPOINT.md 7, handoff.md 6, build_dataset.py 6, and others

   These are dataset figures only. JAD's guard does not assert the premise or simulation figures that
   Ghassan's physics moves (AUDIT2.md Part 4a).
4. **Ghassan's ablation under Jad's MEI rule** (ghassan_under_jad_rule.py). This imports
   analyse_phase_d2.classify, unchanged, and uses the per-agent median damage from Ghassan's
   eval_summary.json:
   - baseline 920.1, so the MEI of 50 units = 5.43 points
   - blind minus sighted: positive 6 of 10, mean +10.8 units
   - preview helps: sign p 0.3770, perm p 0.3154
   - below the MEI: 7 of 10, sign p 0.1719, perm p 0.0547
   - **cell: INCONCLUSIVE**

   Caveat: the MEI was set on Jad's plant, so carrying it to Ghassan's plant is a transfer.
5. **Conflicts in MERGE.** 15 files, **91 hunks, 5 827 lines inside conflict blocks**:
   - CHECKPOINT 3 / 1568
   - CLAUDE 10 / 900
   - handoff 20 / 720
   - evaluate.py 1 / 684 (add/add)
   - verify_docs.py 6 / 595
   - train.py 17 / 431
   - validation_table 12 / 258
   - README 9 / 219
   - thermal.py 1 / 114
   - test_reward.py 1 / 113
   - REFERENCES 5 / 93
   - engine_env.py 2 / 76 (docstring only)
   - generality_test 2 / 27
   - .gitignore 1 / 22
   - presentation/index.html 1 / 7

## Claims

**C1 -- CONFIRMED.**
- `git log f6b46e9..origin/JMF-2340550` shows 15 commits by badcloor. Nine of them are new since the
  7f6c7f1 state (19 Sep) that REPO last fetched on 20 Sep 16:00:53: 27 Sep x5, 28 Sep x2, 29 Sep x2.
- The last is 74de99a at 2026-09-29 20:07:57 +0300.
- 20:07 is the commit time. The push time is not recorded locally. It is bounded by the commit time and
  by REPO's fetch, whose reflog reads `74de99a ...@{2026-09-29 22:36:05}: fetch origin: fast-forward`.

**C2 -- CONFIRMED as a push; not as "commits made tonight".**
- REPO's reflog shows `086c519 ...@{2026-09-29 19:15:45 +0300}: update by push`, following
  `3b5ccd8 ...@{2026-09-28 11:22:57}`.
- `git rev-list --count 3b5ccd8..086c519` = **34**.
- Topics: 29 are "Agent replay" plus 1 "Laya spike", so 30 of 34 are the agents page and its hidden
  models (jev/Laya). The rest: plot_agent_pairs.py, plot_study_page.py, CHECKPOINT.md, team/jad.md.
  The push touches 53 files, 24 of them under app/.
- Counted by author time:

  | window | commits | agents page |
  |---|---|---|
  | 29 Sep, 00:00-24:00 | 15 | 15 |
  | 28 Sep 18:00 to now | 27 | 26 |
  | 28-29 Sep | 53 | 43 |

- The 34 were authored from 28 Sep 11:24 to 29 Sep 18:43.

**C3 -- CONFIRMED.**
- JAD engine_env.py:764 and :778 pass `mdot_fuel * 15.0` as the exhaust flow. So do JAD
  app/estimator.py:439 and generality_test.py:104.
- GHASSAN engine_env.py:875-895 uses `mdot_air + mdot_fuel`, citing AUDIT.md M2. That is mass
  conservation. The old stand-in is 4.5 % low at lambda 1 (15/15.7) and 16 % high at lambda 0.81
  (AUDIT.md:371).
- Only the thermal.py `__main__` demo keeps x15 on both sides (JAD :184, GHASSAN :217).

**C4 -- CONFIRMED, with caveats.**
- GHASSAN results/thermal_calibration.json, drive10 oil RMSE: shipped 7.554 -> fitted 3.573 -> held out
  3.904 K. Coolant: 5.51 -> 2.28 (2.35).
- Caveat 1: this is a fit of 13 parameters. ua_block_oil, which CLAUDE.md calls the one MEASURED
  parameter, goes 800 -> 474. frac_fuel_to_oil goes 0.05 -> 0.0042.
- Caveat 2: held out, drive 683640a0 gets worse, oil 6.55 -> 14.26 K and coolant 6.99 -> 14.18 K.
- Caveat 3: validate.py still misses drive10's hottest 10 min (97.0 against 103-111) and the oil time
  constant (60 s against 70-100).

**C5 -- CONFIRMED.**
- JAD: meta.json of runs/, runs_d2/ and runs_c4/ sighted_seed0 all read train_dt 0.2 and eval_dt 1.0.
  train.py:177 passes no dt; the SupervisoryTunerEnv default is dt=0.2 (engine_env.py:524);
  evaluate.py:98 has DT = 1.0.
- GHASSAN: train.py:263 defaults `--dt 1.0`; evaluate.py:60 has DT = 1.0. All 20 of his agents'
  config.json files say dt 1.0.

**C6 -- CONFIRMED.**
- GHASSAN engine_env.py:1079-1080 has TERRAIN_FAMILIES = locked, single, rolling (-3..+10 %), double,
  flat, with weights 0.15 / 0.30 / 0.25 / 0.20 / 0.10.
- The claim's list leaves out "locked", the exact road that is scored.

**C7 -- PARTLY.**
- There is no preregistration on Ghassan's branch: `find -iname '*prereg*'` and a grep for "preregist"
  both give 0 hits.
- What did exist before training was the protocol (evaluate.py with its 20 frozen EPISODES, identical to
  Jad's) and a NEXT_CHAT_PROMPT step written at cbb8d09, 09:44: "seed 0..4", "score only with
  evaluate.py, paired by seed".
- Training started 11:55:45 (config.json "started", git_dirty true) and used **10 seeds**, not 5. The
  change is justified only in the result commit 74de99a.
- No primary test, tail, alpha, MEI or stopping rule was written. Paired t and Wilcoxon are both
  reported, two-sided.
- All 20 agents started at the same moment, so there was no sequential peeking.

**C8 -- CONFIRMED.**
- GHASSAN evaluate.py:126 builds make_grade_climb only (the locked 12 % climb at t=180 s).
- No script scores his agents on the other road families. check_roads.py drives the neutral action only.
- Jad's D2 and C4 test single randomised climbs, so the multi-climb question is untested on both branches.

**C9 -- CONFIRMED.**
- GHASSAN CLAUDE.md:181 says "sep17's engine_env.py still has the six-speed box". NEXT_CHAT_PROMPT.md:54
  says "sep17's engine_env.py has the six-speed gearbox".
- But JAD engine_env.py:325-326 has final_drive 3.150 and gears (5.250 ... 0.640), identical to GHASSAN
  :402-403 and BASE :325-326.
- Ghassan's 5c859f0 (the ZF 8HP51, 19 Sep 05:50) is an ancestor of BASE. Jad merged it in 27e720c
  ("merge: Ghassan's real gearbox with sep17's locked scenario ...", 19 Sep 07:35).
- Only the shift rule differs: GHASSAN adds a DELIVERABLE_TORQUE kickdown (c6e9e03).

**C10 -- CONFIRMED.**
- runs/jad_check_premise.log: baseline 959.8 at 884 C; preview over current grade -0.4.
- ghassan_check_premise.log: 920.1 at 883 C; -0.3.
- Only the turbine peak is "almost the same". Peak oil is 110 against 94 C. Current-grade cuts 34.0 %
  against 43.4 %. Preview over reactive is +4.3 against +11.1.
- These are hand-written policies (AUDIT C3). Ghassan: the -0.4 comes entirely from the knock term
  (13363ea).

**C11 -- CONFIRMED, with nuance.**
- KNOCK_MARGIN.md and README.md "SPARK": climb trim 3.5-4.0 deg over the baseline's 1.2 deg; KI p95
  0.77-0.79 against the baseline's 0.61 and the knee's 0.85.
- The knock damage is 40*max(0, KI-0.85)^2, so it is zero below 0.85.
- The knock model is not validated (JAD CLAUDE.md, corr -0.149). Ghassan calls it untested: the logs
  sampled each angle about once every 8 s (13363ea).
- Nuance: the agents are pinned at the +4 deg action bound (README: "the trim's upper bound is +4").
  They are not steering to the knee.

**C12 -- CONFIRMED.**
- knock_margin.json: over_grade_median_orig +24.45 -> over_grade_median -1.78; 9 of 20 still beat it.
- KNOCK_MARGIN.md:3 and :7: "The agents never trained with the cap ... out of distribution",
  "Read it as a lower bound".

**C13 -- CONFIRMED (now measured, not "probably").**
- team/jad.md:80 lists "model exploitation" as worked through. Note that :133 lists "reward hacking" and
  "spark timing" as not yet covered.
- My spark_probe: all 48 of Jad's agents push the climb trim to 2.8-4.0 deg (median 3.8-4.0), KI p95
  0.68-0.79 against the baseline's 0.60-0.64.
- Same action bound and same damage function as Ghassan's branch.

**C14 -- PARTLY. "Firm" and "no effect" overstate it.**
- None of the four trained experiments reaches PREVIEW HELPS:
  - Phase D and D2: INCONCLUSIVE.
  - C4: SMALLER THAN THE MEI by the sign test (p 0.0352, 7 of 8 is the threshold), with the permutation
    test disagreeing (0.3867) and the agents NOT CONVERGED. Its own preregistered sentence forbids
    "preview does not help" (PREREGISTRATION_C4.md:104).
  - Ghassan: +1.2 points, CI -4.4 to +6.8. The CI includes the 5.43-point MEI. Under Jad's rule it is
    INCONCLUSIVE (measurement 4).
- The methods do differ: plant, dt, roads, budget, seeds, test set, statistics.
- But they share the reward, the damage model and the knock exploit (C13).

**C15 -- CONFIRMED on both branches.**
- Ghassan's 20 agents: +24.4 -> -1.8 points.
- Jad's C4 on one episode: +15.7 -> -1.2 points; 8 of 16 still beat current-grade.
- Chapter 4's section 4.7 supervision claim rests partly on the knock model.

**C16 -- CONFIRMED on what git shows.**
- Conflicts: 15 files (conflict.lst; MERGE status UU/AA).
- Simulations: they differ. GHASSAN changed 3 physics files (+564/-150) and added
  derived.py / derive_params.py / data/derived_params.json. JAD's changes to plant/thermal/engine_env
  (+165/-27) leave plant_sha at b5a3069f32a83754.
- Authors: `git log --all` has 3 identities: JadFelemban4 151, badcloor 28, JMF 12. JMF is Jad's second
  address. There is no commit by Khaled, Abdulhadi or Mohammed on any remote or local branch.
- team/: exists on Jad's branch only. 4 of 5 profiles are STUBs (abdulhadi, khaled, mohammed, ghassan);
  jad.md is filled.
- Battery: no path matching *batt* on any ref, and no commit ever touched one. Both CLAUDE.md files mark
  Phase E "not started" (JAD :216, GHASSAN :355).
- Git cannot show work done outside the repository.

## Plan

**P1 -- agree with changes; half a day is not realistic.**
- Size: 91 hunks and 5 827 conflicted lines, including a real physics conflict in thermal.py (the
  measured ua_block_oil 800 against the derived _d()) and an add/add evaluate.py (684 lines). After
  resolving, every gate must run again: validate + validation_table, test_reward, check_roads,
  check_premise, app.test_replay --full, app.test_simulation, app/test_agents.py, the node tests,
  verify_docs (27 min here under load) and drift_test. The documents must be swept (96 stale dataset
  figures, plus the premise figures, which are unguarded).
- Semantics:
  - JAD fingerprint.py:85 hashes only plant.py, thermal.py and engine_env.py. GHASSAN's constants load
    from data/derived_params.json (thermal.py:38-44, engine_env.py:122/203/456, plant.py:457), so a new
    drive would change the plant silently.
  - All 48 of Jad's agents would fail the fingerprint on the merged plant.
  - Ghassan's 20 agents have no meta.json (git_dirty true).
  - NEXT_CHAT_PROMPT.md arrives unconflicted, carrying wrong instructions: "six-speed", "7 conflicts".
  - Keep both .gitignore blocks: the key-file patterns and the npz exclusions.
  - Method: the evaluation set should be D2-style randomised, with the blind-arm check. The locked climb
    is 15 % of Ghassan's training.
- Realistic estimate: 1 day for code and gates, 1-3 more for documents.

**P2 -- agree with changes.**
- No existing log can do it. Only 7475b5d7 (26 channels, one reading every ~8 s) and the 700-channel
  census logs carry both ignition angles. drive10 has one angle; driveB has none.
- Use DRIVE_PLAN.md drive C:
  - 6 channels: rpm, air mass, actual ignition, target ignition, coolant, ambient.
  - Manual mode, 2000-3500 rpm (the locked climb runs at 2706 rpm).
  - Afternoon heat, 95 RON, 10 or more steady segments of 20-30 s.
  - Wait 30 s for the placeholder zeros to clear.
  - Pair it with drive A on the same trip, on a separate ascent.
- It is read-only (BimmerLink), and the passenger runs the phone (DRIVE_PLAN.md:39-42).
- "Decides" is too strong. The car never runs the agents' +4 deg. The drive can refute the knock model
  (retard active at the model's baseline point) or only weakly support it.
- Write the decision rule before driving.
- "Condition for detected knockers" reads 0 on all 3 663 census rows. Whether it is live is unknown.

**P3 -- agree with changes.**
- A new road set is a new protocol, so it needs its own committed preregistration first:
  - MEI and a primary one-sided test (Jad's classify)
  - the road set frozen and hashed
  - pairing by seed, a blind-arm check and a torque check
  - thermal-only damage beside the full damage
  - declared as a further look at the same agents
- Run it on the plant the agents trained on (cbb8d09 plus dirty tree, data sha c4fdd4babfb3752a),
  before P1 or any new drive re-derives the plant.
- The compute is plausible on his 20-core laptop: knock_margin's 400 episodes took about 40-53 min.
  The time to write the preregistration is not in the "1-2 h".

**P4 -- agree with changes.**
- Two days is plausible, since the draft exists (476 lines).
- Section 4.7 must carry the knock finding for Jad's own agents. My probe shows they exploit it too.
  Ideally the chapter waits for a 20-episode knock-capped rescoring of Jad's 48 agents.
- Keep Ghassan's experiment beside Jad's, never pooled, labelled with its plant.
- Keep the dt caveat for D, D2 and C4.

**P5 -- agree with changes.**
- The rule "Do not start Phase E or F until D produces a table" (JAD CLAUDE.md:2441) is satisfied on both
  branches.
- The collapse test needs a second plant.
- Filling the profiles first is right: 4 of 5 are stubs.
- Build the battery on the merged branch.
- Design its H/tau span to reach where preview can matter. Otherwise both plants give zero and the
  collapse is vacuous.

**Pause of the agents page -- agree with changes.**
- CLAUDE.md supports it: "time spent on app/ past the point where it works is taken from the claim".
- After P1 the page's live fingerprint check (agent_catalog.py:121) refuses every agent it has.
- The Laya spike (bd061ad) found that its answers follow the order of the options, not the engine state.
- Tie the resumption to P1 and to agents on the merged plant. P2 is not a technical dependency.

## Missing from the plan

1. A 20-episode knock-capped rescoring of Jad's 48 agents. C13 said "must check" and no step does it.
   My one-episode probe shows the same exploit.
2. A decision on the knock lever before any new training: cap the trim, validate the knock model first,
   or report damage with and without the knock term. Otherwise the next training repeats the exploit.
3. Fingerprint coverage for data/derived_params.json, and provenance for Ghassan's agents (no plant hash,
   git_dirty true).
4. The canonical test set for the merged method: D2-style randomised plus multi-climb, with the blind-arm
   check, instead of the memorisable locked climb.
5. Restating the headline. Under the MEI rule Ghassan's result is INCONCLUSIVE; "no measurable preview
   value" in NEXT_CHAT_PROMPT.md:22-23 and "firm" in the plan both overstate it.
6. Dropping or rewriting Ghassan's NEXT_CHAT_PROMPT.md and CLAUDE.md:181 (the six-speed and 7-conflict
   claims). AUDIT2 recommended keeping NEXT_CHAT_PROMPT deleted.
7. Backing up Ghassan's runs/terrain_dt1 and train_record.npz, which "cannot be regenerated at all" and
   which train.py resumes into.
8. Re-examining reward safety on the merged plant: the random policy scores +0.00436, above neutral, and
   the 300 s starver margin is -0.133 against Jad's -0.903.
9. The charge-temperature check must exclude driveB's assumed-ambient rows (3.8 % against 1.9 %).
10. Reporting all looks at the preview question together, with unadjusted p flagged.
11. Keeping the dt caveat for Jad's closed experiments.
12. The oil fit's held-out regression on 683640a0, which must be stated before calling Ghassan's physics
    better.

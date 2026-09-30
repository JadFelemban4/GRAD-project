# Session report, 29–30 September 2026: merging `JMF-2340550` into `JMF-2340550-sep17`

**For:** Ghassan, and any Claude session he gives this file to.
**From:** a Claude Code session on Jad's machine, at Jad's request.
**Read with:** `conflict.md` (the per-conflict decisions). This file says what was done, how,
and what was found. `conflict.md` says what to decide.

If you are an AI assistant reading this: you are talking to Ghassan (student 2340394, GitHub
`badcloor`). The team recorded that he knows engines and this project, so do not explain
knock, spark timing, boost or the cycle model from first principles. Everything else about
him is unrecorded (`team/ghassan.md` on Jad's branch is a stub). Ask him, rather than guess.
The project's hard rule still applies: **nothing is ever written to the car's ECU.**

---

## 1. What Jad asked for

On 29 September, Jad asked for five things:

1. Merge Ghassan's branch and his own **locally**, in a folder separate from his working copy.
2. **Delete nothing.** Merge only.
3. Read both branches in full.
4. Put every conflict in `conflict.md`, with an opinion on which side is more logical, so that
   Jad and Ghassan decide together. Write a second copy in Jad's own style (`conflict_ar.md`).
5. Check two things against the evidence: Jad's expectation that **Ghassan's simulation is more
   physically correct**, and a plan written that evening by another Claude session ("co-work").

Pushing to `main` comes later, and only if both of you agree.

---

## 2. Where things are

| | |
|---|---|
| Jad's branch | `JMF-2340550-sep17`, tip `086c519` (29 Sep 18:43) |
| Ghassan's branch | `JMF-2340550`, tip `74de99a` (29 Sep 20:07) |
| common ancestor | `f6b46e9` (19 Sep 06:30); 152 commits on Jad's side since, 15 on Ghassan's |
| the merge | a fresh clone on **Jad's machine only**: `C:\Users\admin\Documents\graduation project\To main`, branch `JMF-2340550-merge` |
| state | `git merge --no-ff --no-commit origin/JMF-2340550`, **in progress, not committed, not pushed**. Jad's working copy (`GRAD-project`) was not touched |
| conflicts | 15 files, 91 hunks, 5 827 lines inside conflict blocks; zdiff3 markers (HEAD = Jad, the middle block = the ancestor, `origin/JMF-2340550` = Ghassan) |
| dropped files | none: 454 of 454 files of the two branches are in the merge |
| `main` | `origin/main` is an ancestor of both branches, so pushing the finished merge to `main` is a fast-forward |

**To reproduce the same merge on your machine** (identical only if both tips are still
`086c519` and `74de99a`):

```
git fetch origin
git checkout -b JMF-2340550-merge origin/JMF-2340550-sep17
git -c merge.conflictStyle=zdiff3 merge --no-ff --no-commit origin/JMF-2340550
git diff --name-only --diff-filter=U        # the 15 files
```

Files this session wrote, all **untracked** in `To main` (none is in git):

- `conflict.md` — the decisions, hunk by hunk, in English
- `conflict_ar.md` — the same, in Arabic, in Jad's style
- `SESSION_REPORT_2026-09-30_merge.md` — this file
- `_merge_review/proposed/` — proposed merged versions of `evaluate.py`, `train.py`,
  `test_reward.py` and `verify_docs.py`, plus two patches (`agent_trace.patch`,
  `test_agents.patch`) and `verify_docs.union.patch`
- `_merge_review/reports/` — eight reports, each with every command it ran and what it
  printed: `physics-thermal`, `physics-vehicle-env`, `physics-protocol-knock`,
  `cowork-claims`, `conflict-evaluate`, `conflict-train`, `conflict-test_reward`,
  `trial-merge`

**If `conflict.md` points at `_merge_review/`, you need that folder too.** Jad has it, in
the zip beside this file.

---

## 3. What was done, in order

1. **Scoping.** `git fetch` brought Ghassan's branch from `7f6c7f1` to `74de99a`. Then:
   the merge base, commit counts, and a dry run (`git merge-tree --write-tree`) that listed
   the 15 conflicts before anything was touched. The six files both sides edited but git
   merged cleanly were listed too: `validate.py`, `check_map.py`, `app/estimator.py`,
   `app/test_replay.py`, `SESSION_REPORT_2026-09-19.md`, `presentation/README.md`.
2. **The merge folder.** A clone from GitHub into the empty `To main`, then the merge with
   `--no-commit`. It was checked afterwards that no file of either branch was lost, and before
   and after every agent run that nothing tracked in `To main` had changed.
3. **Both simulators, unmodified.** `check_premise.py`, `test_reward.py` and `validate.py`
   were run on plain copies of each branch (section 4a).
4. **A 32-agent analysis workflow.** One agent per conflicted file, plus physics agents,
   one-sided-file sweeps, and a claims check. It hit the account's usage limit: 4 agents
   finished, and 3 more wrote their reports before stopping. After the limit reset, the
   remaining conflicts were adjudicated directly by this session instead, to stay under the
   limit: all 91 hunks were extracted with both sides and the ancestor.
5. **A trial build.** One agent built the recommended resolution in a throw-away copy and ran
   every suite (section 4e).
6. **Writing.** `conflict.md`, `conflict_ar.md` and this file.

The physics work, in brief:

- A thermal replay of all seven usable drives through both `thermal.py` modules, with
  identical inputs. It reproduces `results/thermal_calibration.json` to the second decimal.
- Seven environment × thermal × exhaust variants of the premise.
- Per-step traces at dt 0.2, 1.0 and 2.0.
- An explicit-Euler stability check of the block node.
- Deliverable-torque probes and a notch sweep.
- A spark-trim sweep.
- `knock_margin.py` spot-checks from the committed `policy.npz` files.
- A probe of all 48 of Jad's trained agents (Phase D, D2, C4) from his `runs*/` zips, read-only.
- Ghassan's `eval_summary.json` files re-analysed with Jad's preregistered statistics.

---

## 4. What was found

Every figure here was printed by a run made on 29–30 September. The reports in
`_merge_review/reports/` carry the command behind each one.

### 4a. The two branches, unmodified

| | Jad (`086c519`) | Ghassan (`74de99a`) |
|---|---|---|
| `check_premise.py` baseline damage / peak turbine / peak oil | 959.8 / 884 °C / 110 °C | 920.1 / 883 °C / 94 °C |
| current-grade cut | 34.0 % | 43.4 % |
| preview over reactive / over current-grade | +4.3 / −0.4 points | +11.1 / −0.3 points |
| `test_reward.py` | 4 of 4; starver −0.90349; random −0.04744 | 8 of 8; starver −0.13265; random **+0.00436** |
| `validate.py` | 8 of 11 (literature bands) | 8 of 11 (6 of 7 literature, 2 of 4 against our car) |

### 4b. Whose physics is more correct

**Ghassan's, on every component where the code differs — with one defect of his own, and an
oil node that is better on average but not at sustained load.** Details and evidence:
`conflict.md` section 2.

- **Right on Ghassan's side:**
  - exhaust into the turbine node = air + fuel. Jad's `fuel × 15` is −4.5 % at λ 1 and
    +11 % at λ 0.85; it hides ~22 % of enrichment's real housing cooling. On Jad's plant this
    fix alone takes the baseline from 959.8 to 1085.3 and raises every cut by 7–9 points
  - drag air density from the ambient (1.12 kg/m³ at 42 °C, against a typed 1.2)
  - the boost ceiling evaluated at ambient, as `plant.py`'s own docstring says, and built
    from the measured envelope. Readings above the model's ceiling in drive B: 17 of 89
    against 41 of 89 on Jad's
  - the BaselineECU spark offset: 13.42, now used at 25 of 26 points, bias +0.00°. On Jad's
    branch the fitted line was never used
  - the deliverable-torque kickdown. On Jad's plant, 8–9.7 % at 130 km/h cannot be driven
    by any policy; this never touched D2/C4
- **Equal:** the ZF 8HP51 ratios and upshift rule, identical on both since `27e720c`
  (19 Sep); the turbine node (`c_turb`, `ua_gas_turb`, `ua_turb_amb`), identical and ASSUMED
  on both.
- **Against Ghassan — the thermal constants are numerically stiff.** The explicit-Euler
  factor of the block/coolant node at the climb is −0.78 at dt 1.0, −1.67 at 1.5 and −2.56
  at 2.0 (Jad's: +0.84 to +0.67). At dt 1.0 the coolant rings and settles. At dt 2.0, the
  step `generality_test.py` runs at on both branches, it never settles: 86.8–95.4 °C,
  8.3 K per step, the thermostat flipping 0 ↔ 1. **Sub-step the thermal network (or
  integrate it implicitly) before trusting any H/τ output.**
- **The oil node: mixed.**
  - Better: lower RMSE on 6 of 7 drives free-running and 7 of 7 pinned, and it removes Jad's
    +22 to +32 K overshoot on pulls.
  - Worse: sustained load. Drive10 spent 201 s above 110 °C; Jad's model 6 s, Ghassan's
    0 s. At drive10's 117 °C peak the error is −16.9 K (Jad's −4.1 K). Row 8: 97.0 °C
    against Jad's 96.4, car 103–111.
  - The docstring's "oil heat follows ENGINE SPEED ... not fuel" is refuted in its second
    half: in every rpm bin the car's oil-minus-coolant gap rises with fuel (+1.5 to +2.8 K
    per g/s).
  - The fuel share is not identified. The objective is flat from 0.05 % to 5 %
    (1.741–1.800 K); the shipped 0.0042 is not its own optimum (0.01 gives 1.741); Jad's 5 %
    fits as well once the other oil constants refit.
  - Holding 683640a0 out, its oil error is 14.3 K against 6.6 K before the fit.
- **Coolant:** Ghassan's regulates near the car's ~93 °C median, where Jad's sits at
  88–90 °C. But the block ratio is identified by one warm-up drive: held out, 683640a0's
  coolant error is 14.2 K, and the held-out mean is not better (4.91 against 4.79 K).
- **Why both give ~884 °C:** a cancellation. The exhaust fix adds +5.5 K and the air density
  removes −6.2 K. The two plants' damage differs by 12–13 %.

### 4c. Findings that apply to both branches

1. **All 68 trained agents exploit spark advance.**
   - Ghassan's 20: climb trim +3.5 to +4.0°, KI p95 0.77–0.79 against the baseline's 0.61.
     `knock_margin.py`'s +24.4 → −1.8 points was reproduced (8 episodes, within 0.05 %).
   - Jad's 48 (Phase D, D2, C4): trim 2.8–4.0°, median 3.8–4.0°. C4 on one frozen
     episode: +15.7 → −1.2 points with advance capped at 0. Two C4 agents on two D2
     episodes: capped damage 33–68 % higher.
   - The +4° action bound stops them, not the knee: the model's KI 0.85 sits at 6.9° and
     KI 1.0 at 10.0°, at held torque.
   - The direction is real: +4° cuts EGT 28 K and fuel 5 %. A constant +4° alone takes the
     locked climb from 920.1 to 572.3, about what `current-grade` buys.
   - But the car's own boosted logs run 3–8° *below* the model baseline's spark at matched
     rpm, MAP and ambient (31 genuine readings). That points against the margin being real.
2. **The grade-step knock spike.** At an instantaneous grade step the baseline ECU schedules
   spark on the previous step's MAP (cruise, ~66 kPa) while the load loop jumps to ~145 kPa.
   The knock integral reaches 2.1 for one step.
   - Size at dt 1.0: 66 damage units on Jad's plant, 59 on Ghassan's — 96 % of the episode's
     knock term. It scales with dt: 13 at 0.2, 133 at 2.0.
   - It is 34–102 units on D2 roads, the size of the 50-unit MEI.
   - It is all of the hand-written preview-over-current-grade gap. Turbine-only, that gap
     is +0.01 / +0.04 points.
   - It is the only significant preview effect in Ghassan's retrain: knock term alone,
     10 of 10 seeds, sign p 0.0010. Sighted seed 2 pre-retards from t = 175 s at the slew
     limit.
   - An 8 s ramp removes it: 69 → 3.5 (Jad), 61 → 2.4 (Ghassan).
   - Whether it moved Phase D, D2 or C4's preregistered results was **not measured**.
3. **Ghassan's retrain, under Jad's preregistered rules:** 6 of 10 positive, mean +10.8
   units, sd 72.1. Sign p 0.377, permutation p 0.315. Below-MEI: sign p 0.172, permutation
   p 0.055. **INCONCLUSIVE**, with sign-test power 0.26 against 50 units (23 seeds for 80 %).
   Ghassan's own figures reproduce (+1.17 points, t p 0.65, Wilcoxon p 0.43). Supervision:
   10 of 10 in each arm beat `current-grade` on the median. Worst episode above
   `current-grade`'s 520.5: 3 of 10 sighted, 5 of 10 blinded.
4. **Ghassan's protocol, measured against Jad's method:**
   - The design was committed before training (`cbb8d09` 09:44; training started 11:55).
   - Not written: hypothesis direction, alpha, MEI, decision rule, stopping rule.
   - The seed count was written as 5 and run as 10. The change was made before training
     (all 20 started together), but committed only with the results.
   - The test set is only the locked climb, which is 15 % of the training roads.
   - The agents carry `config.json` with `git_dirty true` and no fingerprint `meta.json`.

### 4d. Claims in Ghassan's documents that are wrong

- `CLAUDE.md:181`, `NEXT_CHAT_PROMPT.md:54` and `SESSION_REPORT_2026-09-28_evening.md:290`
  say `sep17`'s `engine_env.py` still has the six-speed box. **It does not**: Jad's branch
  has carried the ZF 8HP51 ratios since `27e720c` (19 Sep).
- The same files say "7 conflicts, 4 in code". Today it is 15, 7 of them code.
- "PREVIEW ADDS NOTHING MEASURABLE" / "no measurable preview value": INCONCLUSIVE is the
  defensible word (4c.3).
- "Every agent advances spark to just under the knock knee": they sit at the +4° action
  bound.
- `engine_env.py`'s neutral-fan caveat ("exactly neutral during the climb") is wrong on your
  plant too: your baseline fan is 0.0 for the whole episode.
- `NEXT_CHAT_PROMPT.md` returns with the merge (Jad's branch deleted it on purpose) and tells
  the next session to "Resolve code toward THIS branch". `conflict.md` section 5 proposes
  renaming it, not deleting it.

### 4e. The trial build of the recommended resolution

Built in a throw-away copy. Everything functional passes:

- the preregistered Phase D (5 of 8, p 0.3633), D2 (4 of 8, p 0.6367) and C4 figures
- `validate.py` 8 of 11; `test_reward.py` 8 of 8; `check_premise.py` 920.1 at 883 °C;
  `check_roads.py` 40 roads, 14 bind
- `app.test_replay` 49/49 and `--full` 59/59; `app.test_agents` 129 OK
- node tests: 140 pass

The fixes the trial showed are needed:

- move `results/phase_d_seed0_110kmh.txt` to `results/void/` (without it Phase D reads n = 9)
- `app/agent_trace.py` and `RESULT_KEYS` in `app/test_agents.py` gain `damage_thermal`
- `verify_docs.py` must be a union. Jad's side alone crashes with `NameError: check_derived`,
  and the two sides both define `RETIRED_EXEMPT_DIRS`, with Jad's silently replacing yours
- `drift_test.py:114` needs `encoding="utf-8"`

`verify_docs.py` (union) then fails 7 of 73 checks, all from the merge. Five are Jad's pins
(959.8 / 884 / 890.6 / 608.0 / 15 against 920.1 / 883 / 873.1 / 604.8 / 14); two are stale
document figures (11 drives and 321.7 minutes, not 10 and 295.0). `plant_sha` on the merged
tree is `c236a8db3e201090`, yours, so all 48 of Jad's agents are refused there — correctly.

### 4f. The co-work plan

Most of its facts hold. It overstates one thing: "the main result is firm". Every preview
result is INCONCLUSIVE or one-seed-thin, and all of them share the knock model and the
step spike. It underestimates another: "half a day" for the merge, where the realistic
figure is about a day for code and checks, then one to three for the documents. And its
"Jad's agents probably do the same" is now measured, as 4c.1. `conflict.md` section 6
covers each claim and each step.

---

## 5. Decisions waiting for both of you

From `conflict.md` section 0:

1. **Physics:** Ghassan's, plus thermal sub-stepping.
2. **Method:** Jad's (preregistration, MEI rule, fingerprints, train.py guards), with the
   fingerprint extended to `data/derived_params.json`. Today a new drive changes the plant
   without moving `plant_sha`.
3. **The spark lever** before any new training: cap the trim at 0, or report every result
   with and without the knock term.
4. **Ramp every grade change** before the next ablation (a new preregistration).
5. **Tag both tips** before committing the merge (`sep17-before-merge` on `086c519`,
   `ghassan-before-merge` on `74de99a`), so the finished experiments stay reproducible.

---

## 6. What this session did not do

- It did not commit, push, or resolve any conflict in `To main`. It did not touch Jad's
  `GRAD-project`.
- It did not read line by line: the agent-replay design documents under `docs/superpowers/`
  (~23 000 lines), the agents-page JavaScript, the generated HTML under `figures/`, and
  binaries. None of them conflicts or sets physics.
- It did not score Jad's 48 agents with the spark cap on the full 20-episode protocol: only one
  or two episodes each.
- It did not measure whether the step spike, or `fuel × 15`, changed what Jad's agents learned
  or moved D2/C4's preregistered verdicts.
- It did not re-run Ghassan's agents on multi-climb roads (the plan's step P3). That can be
  done from the committed `policy.npz` files, on the plant they trained on (`cbb8d09` plus
  data sha `c4fdd4babfb3752a`), after the test is written down.

---

## 7. For a Claude session helping Ghassan

- **Start with `conflict.md` section 0**, then section 2 (physics) and section 3 (the two
  cross-branch findings). Those are the parts he can check best.
- **Findings he may want to contest** are in 4b and 4c: the stiffness at dt > 1.1 s, the
  unidentified oil fuel share, the refuted "not fuel", the step spike. Each can be reproduced
  from his own branch; the method is described in `_merge_review/reports/physics-thermal.md`
  and `physics-vehicle-env.md`. Report a disagreement with a measurement, as this project does.
- **Do not resolve conflicts "toward" either branch as a rule.** `conflict.md` gives a
  decision per hunk, and several go to each side.
- **Do not push the merge or anything to `main`** until both have agreed; Jad pushes to
  branches named `JMF-2340550-*` first. Jad sometimes runs several Claude sessions in the same
  working copy, so commit by explicit path, never `git add -A`.
- **Run `verify_docs.py` before quoting a figure**, and `test_reward.py` after any change to
  the plant, reward, gearbox or roads.

---

## 8. After Ghassan's reply: the merge was finished (30 September)

Ghassan accepted all five decisions, with two points of his own: his retrain's result
reads **INCONCLUSIVE**, and **drive C comes before drive A**. His re-checks agreed with
this report on all four findings about his branch. One sharpened a finding: at dt 1.0 the
coolant does not settle on the climb, it zig-zags about 2 K on every step. One corrected
it: the knock-term sign test is p 0.002 two-sided (0.001 one-sided). Jad then asked for
the merge to be finished and pushed to `main`.

What the merge commit applies:

- every conflict, resolved hunk by hunk as `conflict.md` recommends;
- the section 5 fixes and fixes a–f of `conflict.md` section 7;
- Ghassan's accepted corrections to his own documents: the six-speed sentences,
  "7 conflicts", "adds nothing measurable", "just under the knock knee", and the oil
  docstring's "not fuel";
- the document sweep: `verify_docs.py` passes all 73 checks on the merged tree.

Two files were moved, not deleted: `results/phase_d_seed0_110kmh.txt` went to
`results/void/`, and `NEXT_CHAT_PROMPT.md` became `NEXT_SESSION_2026-09-29_ghassan.md`.
The checks and their results are in `CHECKPOINT.md`, in the entry for 29–30 September.

What the merge does **not** apply, by agreement, because each belongs before the next
training and needs its own measurement:

- the thermal sub-stepping
- the fingerprint on `data/derived_params.json`
- the spark cap
- the grade ramps
- the new preregistration

Renamed on GitHub after the push (the commits are kept under the new names and under
the two tags):

- `JMF-2340550` became `GRA-2340394-leftin-2026-09-30`
- `JMF-2340550-sep17` became `JMF-2340550-leftin-2026-09-30`

**For Ghassan:** your two unpushed commits (`f35a5df`, `194d75f`, the results page) sit on a
branch whose remote name has changed. Rebase them onto the new `main` when you rebuild
the page, as your reply planned.

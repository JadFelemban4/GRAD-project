# Prompt audit — 30 September 2026

An audit of every file in this repository that an AI assistant reads as
instructions, looking for text that no longer fits: the model that reads it,
the project as it stands after the merge, or the other files. Run at Jad's
request with `/claude-api prompt-audit`.

Every fix is its own patch in `PROMPT_AUDIT_2026-09-30/` (28 patches, plus
`all.patch` with all of them). Line numbers below are those of commit
`a0ab79b`.

**Status, 5 October 2026:** Jad approved patches 01–27, and they are applied;
`verify_docs.py` passes every check after them. **Patch 28 (the move to
`STATE_HISTORY.md`) is NOT applied.** It waits for Ghassan, because the merge
agreement kept the boxes in `CLAUDE.md`. Apply it with
`git apply PROMPT_AUDIT_2026-09-30/28-state-history-move.patch`.

---

## Assumptions

- **Scope: the whole working tree**, because the request named no file. That
  is `CLAUDE.md`, `handoff.md`, `team/*.md`, the dated `NEXT_SESSION_*.md`
  prompts, and the prompt the app sends to its models
  (`app/model_questions.py`). The project has no `.claude/` directory, skill,
  rule file, command or subagent definition. Skipped: `.venv/` (a dependency
  directory; it holds FastAPI's own `SKILL.md`) and everything under
  `~/.claude/`, the user-level memory and skills, which the request did not
  name.
- **Target model: Claude Opus 5.5**, the model that ran the audit. The request
  named none and no instruction file pins one.
- **Two models here are not Claude.** `app/jev.py` calls typesafe.ai's
  `jev-latest` and `app/laya_bridge.py` runs Laya, a local model. These are the
  only model calls in the code. Their prompt (`app/model_questions.py`) is
  listed and not audited: the audit's patterns describe Claude's documented
  behaviour, and nothing comparable is documented for those two models. No
  change to them is proposed.

---

## Summary

Three findings matter most.

1. **The new-drive routine would start training too early.** `CLAUDE.md`'s
   "When a new drive CSV arrives" says to run `train_all.py` after every drive.
   On 30 September Jad and Ghassan agreed five steps and a new preregistration
   before ANY training. An assistant that follows the routine as written would
   train without the preregistration. Current models follow written
   instructions closely, so this line gets followed. Patch 02.
2. **Two overclaims that could reach a supervisor.** "What passing project
   means" still says the floor is down, on +29 to +34 points over
   `current-grade`. It doesn't mention the merge finding that this margin
   disappears once spark advance is forbidden (patch 01). `handoff.md`'s
   29 September box still says "no measurable preview value" and that the
   agents stop "just under" the knock knee. Ghassan accepted corrections to
   both phrases on 30 September, but only `CLAUDE.md` got them (patch 16).
3. **Old orders still written as current.** `CLAUDE.md`, which every session
   reads, still carries eight dated state boxes and three old to-do lists. Some
   of their lines still read as orders: "THE NEXT ACTION IS TO RETRAIN AT
   130 km/h", and "The live list is now: set the minimum effect of interest …
   NOT YET SET". Patches 03, 04 and 06 fix the lines that sit outside the
   boxes. Patch 28 moves the boxes word for word to `STATE_HISTORY.md`.

| group | findings |
|---|---|
| 1 · dated prompt text | 2 — patches 18, 26 |
| 2 · brittle instruction files: stale facts, broken pointers, files that disagree | 26 |
| 3 · tool descriptions | not applicable: no tools are defined for Claude here |
| 4 · request code and architecture | not applicable: no code here calls Claude |
| flags, no patch | 5 |

`verify_docs.py` passes every check on an untouched copy, and again with all 28
patches and this report added. The results are in "Verification" at the end.

---

## High confidence — each one is contradicted by the repository itself

### 01 · `CLAUDE.md:677-687` — "passing project" leaves out the knock caveat
- **Says:** "That is Phase D, **and Phase D is in.** The floor is down … the agent **does** beat the comparators — **+29 to +34 points** over `current-grade`".
- **Why it no longer fits:** the phase table (line 606) and the first box (finding 1, lines 126-130) say that margin disappears with spark advance forbidden. They also show three more ablations have run. The paragraph dates from 22 September (`d66417a`), before both.
- **Pattern:** Group 2, a claim the repository contradicts. **Action:** rewrite — `01-claude-passing-project.patch`.

### 02 · `CLAUDE.md:2793-2797` — the new-drive routine trains before the agreed steps
- **Says:** "**The team's plan (29 September): retrain after every drive** — `python check_roads.py`, then `python train_all.py` (~4 h) …"
- **Why it no longer fits:** the first box (lines 138-150) and the live list (line 2905): "Before ANY training, in this order", ending in a new preregistration. The routine (29 September, `74de99a`) predates that agreement and gives no condition.
- **Pattern:** Group 2, two passages that disagree; the newer one is the 30 September agreement. **Action:** rewrite, keeping the plan and adding the condition — `02-claude-new-drive-before-training.patch`.

### 03 · `CLAUDE.md:3055-3061` — two finished steps still read as orders
- **Says:** "0. **Review and commit the working tree**, then decide the order of drive A and the retrain" and "1. **Merge `origin/JMF-2340550-sep17`.** … Nothing below is reportable until the branches are one."
- **Why it no longer fits:** the work was committed in `cbb8d09` (29 September) and the merge is `a7ce729` (30 September; the first box says so). Steps 2, 3, 7 and 9 of the same list already carry "DONE". The list sits inside a `RETIRED-OK: section` marker (line 3024). That marker switches off `verify_docs.py`'s retired-figure scan for it, and no live-data check reads a sentence like this one.
- **Pattern:** Group 2. **Action:** mark both DONE — `03-claude-steps-0-1-done.patch`.

### 04 · `CLAUDE.md:2996-2998` and `2955-2956` — "The live list is now:" is three lists old
- **Says:** "**The live list is now:** 1. **Set the minimum effect of interest.** … NOT YET SET" and "2. **Sweep the documents** … ~187 mentions". Also C4's "**Next is the team's decision** — longer budget … or more seeds".
- **Why it no longer fits:** the MEI was set at 50 damage units on 22 September (line 606). The ledger was swept to zero in `3f4627d` (line 2967 and mistake 11). The C4 decision was overtaken by the merge's live list.
- **Pattern:** Group 2. **Action:** add a dated SUPERSEDED note to each. The 23 September list already has one (line 2962), so the note copies the file's own convention — `04-claude-superseded-lists.patch`.

### 05 · `CLAUDE.md:2823-2875` — "THE AGENT IS SCORED IN A DISCRETISATION IT DID NOT LEARN IN"
- **Says:** the heading, "`dt` is not consistent across this project and never has been", and "Three ways out, and the choice is the team's, not the next session's".
- **Why it no longer fits:** the team chose on 27 September. `train.py` passes dt 1.0 for the terrain design (line 2610; step 4 at line 3074: "the agent finally trains in the discretisation `evaluate.py` scores it in"). The section is still true for Phase D, D2 and C4 only. It dates from 19 September (`c59346f`).
- **Pattern:** Group 2. **Action:** rewrite, scoped to Phase D, D2 and C4, with the decision stated — `05-claude-dt-section.patch`.

### 06 · `CLAUDE.md:3118-3120` — "Decide the order before step 3"
- **Says:** "Decide the order before step 3: either drives A and B first, or retrain now and again after them."
- **Why it no longer fits:** step 3 is DONE (29 September), drive B is in, and the live list fixes the order: drive C before drive A, nothing trained before the five steps.
- **Pattern:** Group 2. **Action:** rewrite — `06-claude-drive-order-decided.patch`.

### 07 · `CLAUDE.md:3133-3138` — "spend it on step 2"
- **Says:** "**Where the app fits in that order: nowhere.** … If you have an hour, spend it on step 2, not on `app/`." and "### The app's backlog — AFTER Phase D, not before".
- **Why it no longer fits:** step 2 is "DONE 19 September" (line 3062), so the pointer sends the reader to finished work. Phase D has its table (line 3114). The live list now schedules the agents page ("waits for step 1 and the retrain", line 2927). Written 16 September (`4905498`).
- **Pattern:** Group 2. **Action:** rewrite, pointing at the live list — `07-claude-app-fits.patch`.

### 08 · `CLAUDE.md:858-863` — the honest comparator's "currently" figure is sep17's
<!-- RETIRED-OK: 0.4, 633.2, 637.4 -- quoted as audit evidence, the sep17 plant's figures -->
- **Says:** "which currently BEATS the predictive one by **0.4 points** (633.2 against 637.4 damage; …)".
- **Why it no longer fits:** on the merged plant `check_premise.py` prints −0.3 points (line 107, line 729, and line 819 in the same section). The 0.4 is sep17's plant (23 September, `3f4627d`).
- **Pattern:** Group 2. **Action:** rewrite to the merged figure, and drop the rounding history beside it — `08-claude-honest-comparator.patch`.

### 09 · `CLAUDE.md:869-870` — the replay table has no date on its physics
- **Says:** "Replaying all nine through `app/` and reading the peak estimated turbine housing against the 1123 K trigger:", followed by a table of ten drives and "**0.206 % is itself a result about H/tau, and it belongs in the thesis.**"
- **Why it no longer fits:** the table was measured on 17–19 September with that day's app physics. The merged physics moved `7475b5d7`'s pinned peak (line 776; the marker at line 2541 says so). `handoff.md` (lines 142-145) already says which rows were not re-measured, and `CLAUDE.md` does not. The table lists ten drives, not nine.
- **Pattern:** Group 2, two files that disagree; `handoff.md`'s wording is newer (the merge). **Action:** add the condition before the table. The 36 s and 0.206 % stay, as `drift_test.py` and `verify_docs.py` pin them — `09-claude-replay-table-condition.patch`.

### 10 · `CLAUDE.md:2542-2546` — "What moved" quotes app pins two moves old
<!-- RETIRED-OK: 890.6, 884.9, 608.0, 593.7 -- quoted as audit evidence -->
- **Says:** "`7475b5d7`'s peak estimated turbine is **890.6 °C** … and `pull01` reads **608.0 °C**".
- **Why it no longer fits:** the current pins are in the Numbers section (line 776), and the marker right above this paragraph (line 2541) names the newer ones.
- **Pattern:** Group 2. **Action:** rewrite in the past tense, pointing at the Numbers section — `10-claude-what-moved-17-sep.patch`.

### 11 · `CLAUDE.md:2505-2512` — the heading says the bugs are live; the body says fixed
- **Says:** "### THE 14 SEPTEMBER AUDIT FOUND SIX BUGS IN `app/`, AND THE APP'S OWN TESTS PASS ANYWAY" and "the app's own suite reports 46 of 46 while every one of them is live".
- **Why it no longer fits:** line 2525 of the same section: "**ALL SIX ARE NOW FIXED**".
- **Pattern:** Group 2. **Action:** past tense — `11-claude-app-audit-tense.patch`.

### 12 · `CLAUDE.md:2700-2701`, `handoff.md:480-481` — pointers to a file that is gone and a report that is not the latest
- **Says:** "NEXT_CHAT_PROMPT.md   The prompt to paste into a new session." and "SESSION_REPORT_*.md … 2026-09-28 is the latest."; `handoff.md` links both.
- **Why it no longer fits:** `NEXT_CHAT_PROMPT.md` does not exist. Jad's branch deleted it on purpose, and the merge renamed Ghassan's copy to `NEXT_SESSION_2026-09-29_ghassan.md`, marked SUPERSEDED (`SESSION_REPORT_2026-09-30_merge.md`, line 331). The latest report is `SESSION_REPORT_2026-09-30_merge.md`. These lines arrived with the merge from `13363ea` (28 September).
- **Pattern:** Group 2, a named path that no longer exists. **Action:** rewrite, with no date to go stale — `12-pointers-next-prompt-last-report.patch`.

### 13 · `CLAUDE.md:2810-2817` — two wrong mistake numbers, and steps 6 and 5 swapped
- **Says:** "5. **Did the new drive push any channel to a flat maximum?** See mistake 6." and "check that the variable you are fitting against actually correlates.** See mistakes 3 and 6."
- **Why it no longer fits:** a channel that hits its limit is mistake 7, and "check that the variable … correlates" is mistake 4's lesson. These references have been wrong since the first commit (`dcf2f93`, 10 September), and the mistake numbering has not changed since.
- **Pattern:** Group 2. **Action:** fix both references and the order — `13-claude-new-drive-mistake-refs.patch`.

### 14 · `CLAUDE.md:2757-2758` — the example in Conventions uses the old point count
<!-- RETIRED-OK: 22 -- quoted as audit evidence -->
- **Says:** "Report numbers with the condition attached. "1.4 % load residual over 22 points, 30–75 kPa""
- **Why it no longer fits:** it is 26 points (lines 604 and 758). `handoff.md`'s habit 4 already says 26. An example is the text a model copies most closely.
- **Pattern:** Group 2, two files that disagree. **Action:** 22 → 26 — `14-claude-convention-26-points.patch`.

### 15 · `CLAUDE.md:2273-2300` — the oil limitation corrects itself twice and keeps the wrong version first
<!-- RETIRED-OK: 110.2, 7, 96.4 -- quoted as audit evidence -->
- **Says:** "the model's **110.2 °C is confirmed about 7 K too cool** … Say it that way in the thesis: … it points at … `ua_block_oil`". Two paragraphs later: "**the pointer above was wrong.**" (96.4 °C). Then 28 September evening: 97.0 °C.
- **Why it no longer fits:** the instruction "Say it that way in the thesis" is attached to the version the same bullet retracts. The current reading is the evening box's: 97.0 °C against 103–111. Of the 12.0 K miss, 4.6 K is the coolant and 7.3 K is the oil node itself.
- **Pattern:** Group 2 (and Group 1 patch accretion). **Action:** rewrite to the current state in two paragraphs — `15-claude-oil-band.patch`.

### 16 · `handoff.md:62-65`, `186-188` — the two corrections Ghassan accepted did not reach `handoff.md`
- **Says:** "sighted minus blinded is +1.2 points … — no measurable preview value." and "Every agent advances spark to just under the untested knock model's knee". Also "that is Phase D — which has now run, and returned a null".
- **Why it no longer fits:** on 30 September Ghassan accepted both corrections, and `CLAUDE.md` carries them (lines 161-163 and 197-198). The heading "PREVIEW ADDS NOTHING MEASURABLE" became INCONCLUSIVE under the MEI rule, and "just under the knock knee" became "the +4° action bound, which happens to sit just under the knock knee". `conflict.md` §4.10 hunk 1 lists both. `handoff.md`'s own first box says "never *preview does not help*".
- **Pattern:** Group 2, two instruction files that disagree; the newer one is the 30 September correction. **Action:** carry the corrections over — `16-handoff-29sep-box-corrections.patch`.

### 17 · `handoff.md:129-131` — contradicts the table seven lines above it
<!-- RETIRED-OK: 0.4 -- quoted as audit evidence -->
- **Says:** "hand-written preview **loses to it by 0.4 points**."
- **Why it no longer fits:** the table just above prints "preview over current grade -0.3 points".
- **Pattern:** Group 2. **Action:** 0.4 → 0.3 — `17-handoff-preview-0.3.patch`.

### 18 · `handoff.md:366-375`, `390-393` — the same rows and the same paragraph twice
- **Says:** the last four rows of "What you must not do" appear twice. The second copy (16 September) comes after a blank line, so it renders as loose text rather than as table rows. The charge-temperature paragraph also appears twice, once with "+23.7 %" and once with "about 25 %".
- **Why it no longer fits:** both sides of the merge were kept (blame: `13363ea` and `4905498`). A model reading two wordings of one rule has to reconcile them.
- **Pattern:** Group 1, duplicated passages that drift apart. **Action:** keep one copy of each. For the rows, keep the fuller 16 September copy, moved into the table: it carries the reasons, and the one row the shorter copy lacks ("Add a seventh live channel"). For the paragraph, keep the one with the measured +23.7 % — `18-handoff-duplicate-rows.patch`.

### 19 · `handoff.md:227-345` — "The path to a passing project" is two versions interleaved
- **Says:** "### Step 1 — install the trainer" followed straight away by "### Step 1 — decide the order". After that come two Step 2s and two Step 3s. Their bodies are swapped: "check the gate" holds the training commands, and "score" holds the timing.
- **Why it no longer fits:** blame shows 10 September lines (Jad) and 28 September lines (Ghassan) alternating. "Decide the order … say which you chose" was decided on 30 September.
- **Pattern:** Group 2. **Action:** rewrite as one record plus the four rules that still bind the next run: gates, ask the owner, move the old runs aside, score and report two ways. It keeps "the twenty never change" and "do not add seeds" — `19-handoff-path-to-passing-project.patch`.

### 20 · `handoff.md:532-542` — the viva section still waits for the retrain
- **Says:** "*we built an ablation that could fail, ran it eight times*"; "On the existing (not yet valid) agents …"; "**If the retrain shows no preview advantage on this scenario, that is the result**".
- **Why it no longer fits:** the same section opens with "ran it four times" (the merge). The retrain ran on 29 September.
- **Pattern:** Group 2. **Action:** rewrite in the past tense with the MEI wording, keeping "never *preview does not help*" — `20-handoff-viva.patch`.

### 21 · `team/jad.md:152-153` — the corrected dataset figure is itself three drives old
<!-- RETIRED-OK: 175.5, 168.1, 8 -- quoted as audit evidence -->
- **Says:** "It also quotes 168.1 minutes over eight drives; the figure is **175.5 over nine**."
- **Why it no longer fits:** 321.7 minutes over eleven drives (`CLAUDE.md` line 111, `python build_dataset.py`).
- **Pattern:** Group 2. **Action:** update it, and say where the figure comes from — `21-jad-profile-dataset-figure.patch`.

---

## Medium confidence — a documented pattern, and the fix is a judgement

### 22 · `CLAUDE.md:3-5` — "what is already proven"
- **Says:** "it tells you what the project claims, what is already proven, and which mistakes …"
- **Why:** the file's own rule (line 621): "Note the verb: **tested**, not proved." The first box: every preview result is INCONCLUSIVE or one seed thin. `team/jad.md` records "proven" as a word that has overclaimed to Jad before. Written 10 September, before the rule.
- **Pattern:** Group 2. **Action:** "what has been measured so far" — `22-claude-measured-not-proven.patch`.

### 23 · `CLAUDE.md:615-617`, `699`; `handoff.md:478` — "the project's result" means Phase D alone
- **Says:** "That is still the project's result"; `analyse_phase_d.py  THE PROJECT'S RESULT.`; `handoff.md`: "**the project's result** … `python analyse_phase_d.py`".
- **Why:** four ablations have run (the first box). Pointing at one of them as "the result" steers a reader to the oldest and least-trained.
- **Pattern:** Group 2. **Action:** name all four — `23-the-projects-result.patch`.

### 24 · `CLAUDE.md:3154-3157` — backlog item 3 is half built
- **Says:** "3. **Wire the trained agent in.** Once Phase D has a policy, the app can display what the agent WOULD command …"
- **Why:** the agent replay exists (`app/agent_api.py`, `python -m app.server --simulation`). It shows trained agents on finished simulated episodes, with no vehicle connection. The live half does not exist yet.
- **Pattern:** Group 2. **Action:** say which half exists — `24-claude-app-backlog-item-3.patch`.

### 25 · `CLAUDE.md:2720-2728` — the layout's `app/` block omits the module that holds a paid key
- **Says:** seven entries: estimator, reader, alerts, server, static, test_replay, review_log.
- **Why:** since 27–29 September `app/` also holds the agent replay (`agent_api.py`), the external-model call (`jev.py`, api.typesafe.ai, one paid call per press, key never written) and the local model (`laya_bridge.py`). An assistant reading the map would not know the app has an outbound call or a key to protect.
- **Pattern:** Group 2 plus keep-list 11. Re-fitting sometimes means adding text. **Action:** add four entries — `25-claude-layout-app-modules.patch`.

### 26 · Errata about the file's own edits, in the sections read as current
<!-- RETIRED-OK: 46 -- quoted as audit evidence -->
- **Where:** `CLAUDE.md:610, 619-622, 653-654, 783-788, 853-856, 2526-2529, 2567-2568, 3035-3043`; `handoff.md:132-139`.
- **Says, for example:** "*(This row said "has six known bugs … passes 46 of 46" until 17 September; the fixes and the count both moved on 16 September and this row did not.)*"
- **Why:** each is a diff against an earlier version of the prose, which the reader never saw. The file's own rule (line 826): "**When a figure goes void, its errata go with it.**" Git history keeps the record. Where an erratum carries a rule (line 621's "tested, not proved"; line 3041's "what sets it is `plant.DTHETA_DEG`"), the patch keeps the rule and drops the history. The mistake log's errata are left alone: correction history is that section's subject.
- **Pattern:** Group 1, relative phrasing ("this paragraph read …"). **Action:** remove — `26-errata-parentheticals.patch`.

### 27 · Six old `NEXT_SESSION_*.md` prompts do not say they are superseded
- **Where:** `NEXT_SESSION_2026-09-21`, `-22`, `-23`, `-24`, `-27` and `NEXT_SESSION_VIZ_2026-09-26`, line 1.
- **Why:** each is a ready-to-paste prompt, and each says the "top box" or "next step" of its own day. Only the 29 September one carries SUPERSEDED. A pasted old prompt would start a session on a plan from before the merge.
- **Pattern:** Group 2, time-sensitive content. **Action:** one SUPERSEDED line under each title — `27-next-session-superseded-headers.patch`.

### 28 · `CLAUDE.md:157-598` and `2929-3022` — eight dated boxes and three old lists in the file every session reads
<!-- RETIRED-OK: 130 -- quoted as audit evidence, the 19 September box -->
- **Says, for example:** "**THE NEXT ACTION IS TO RETRAIN AT 130 km/h.**" (line 472), "**Nothing below is committed yet**" (236), "**Ask which fuel the car was logged on**" (354), "**Next is a TEAM DECISION**" (499).
- **Why:** a rule's authority is what it tells the reader to do now. Every one of these was overtaken by the first box, but each is written in the present tense, and about 440 lines of it load into every session. `conflict.md` §4.10 hunk 1 asked for the boxes "newest first". Instead, the 19 September box sits between 28 and 24 September.
- **Pattern:** Group 2, history narratives and time-sensitive content. **Action:** move them word for word, newest first, to a new `STATE_HISTORY.md`. `CLAUDE.md` keeps a pointer, plus the two rules from the old lists that still hold ("do not add seeds to Phase D or D2", "do not switch to a two-sided test") — `28-state-history-move.patch`. **This one needs Ghassan as well:** the merge decision (`conflict.md` §4.10) chose to keep the boxes in `CLAUDE.md`, and this patch changes where they live but not what they say.

---

## Flags — no patch

- **The installed `i-have-adhd` skill is the old copy.** Its rule 9 reads "Five items ranked beats ten unranked". `team/jad.md` (lines 45-54) says that wording marks the v0.2.0 copy, which drops list items. The skill lives in `~/.claude/skills/`, outside the project, so there is no patch: update it from https://github.com/ayghri/i-have-adhd.
- **`CLAUDE.md:803` — the VOID section's `RETIRED-OK: section` marker covers nothing.** It sits one line above its heading. `verify_docs.py` ends a section marker's scope at the next line that starts with `#`, and that is the very next line. Nothing fails today. Moving it below the heading would switch the RETIRED scan off for the whole section, including live claims such as the one patch 08 fixes, so decide that on purpose. This is outside the audit: it is the checker's rule.
- **`CLAUDE.md:963-1139` — mistake 17 and two scenario findings sit under "### VOID".** Mistake 17 is a `####` heading inside VOID, not in the mistake list. "A ROLLING ROAD…" and "The published towing standard…" are not void either. No pattern in the audit covers misplaced structure, so there is no patch. The fix is to move mistake 17 between 16 and 18 and give the scenario evidence its own heading.
- **`CLAUDE.md:630-675` — "What changed since 11 September" and "since 8 September"** are dated lists like the boxes patch 28 moves. They are not moved because `drift_test.py` row 5 injects its drift into this list's dataset-size line. Retarget that row first.
- **Emphasis.** Most paragraphs in `CLAUDE.md` carry bold or capitals. Current models over-apply forceful wording. Here, though, nearly every emphasis marks a fact with its reason beside it, which the audit leaves alone. No single line is worth a patch. Low confidence.

## Left alone on purpose

- The "ask who you are talking to" rule and the read-only hard constraint: real constraints, each with its reason.
- The twenty-two mistakes. They are long, but they are the reasons behind the rules, and reasons are context, never cruft.
- `handoff.md`'s "What you must not do" table (once de-duplicated): prohibitions with reasons.
- `team/README.md`, `team/_TEMPLATE.md` and the three stubs: current, and in agreement with `CLAUDE.md`.
- `app/model_questions.py`: written for non-Claude models (see Assumptions).

---

## Verification

- **Stale facts were checked against the repository by reading, not by running
  anything:**
  - `git blame` on every quoted line;
  - the argument parsers: `--device`, `--no-preview`, `--no-resume`,
    `--full`, `--simulation` and `--map-from-log` all exist;
  - the helpers `CLAUDE.md` names (`row8_split`, `usable_drives`,
    `AMB_FALLBACK_C`, `DELIVERABLE_TORQUE`, `EPISODES`, `model_budget`) all
    exist;
  - every file path the instruction files name. Only `NEXT_CHAT_PROMPT.md` is
    missing. `battery.py` is stated as not existing, and the rest are generated
    or gitignored.
- **`verify_docs.py` on a scratch worktree** (system Python, per the
  machine-traps note): every check passes at `a0ab79b`, and every check passes
  with all 28 patches applied and this report tracked. The patches keep every
  string that `drift_test.py` injects into `CLAUDE.md`. They also keep the
  three pinned "+11.7" mentions.
- **The series is consistent:** on a fresh worktree at `a0ab79b`, applying
  patches 01–28 in order gives exactly `all.patch`. `git apply --check
  PROMPT_AUDIT_2026-09-30/all.patch` passes against the working tree as it
  stood when the audit ended.
- **`drift_test.py`** on the patched worktree, with this report tracked: 16 of
  16 drifts CAUGHT (858 s). The rows that inject into `CLAUDE.md` (6, 12, 13
  and 14) still find their text after the move.
- **No behaviour probes.** Every finding is a stale fact or a structural one,
  so it was checked against the repository. None is a claim about how a model
  behaves.

## How to apply

- All of them: `git apply PROMPT_AUDIT_2026-09-30/all.patch`, then
  `python verify_docs.py`.
- Some of them: the numbered patches are a series, each made on top of the
  ones before it. A later patch can need an earlier one where they touch the
  same lines. Patch 28 needs 04 and 15.

# The results tab: design

> **STATUS: DRAFT for Jad's review, 30 September 2026, revised after the design review.** Every section follows
> an answer Jad gave in the brainstorming questions of 30 September (§1). The evidence is
> `2026-09-30-results-tab-recon.md` in this directory, cited as "recon §n". Line numbers are at commit `a7ce729`.
>
> **The review.** Five reviewers read the first draft, each from one side (honesty, fit with the code, data and
> adaptation, the page, robustness and scope), and a verifier re-checked every claim in the repository. 80 issues
> were raised, all 80 held, 30 of them major; after merging duplicates they are 45 distinct points. A second pass
> (a coverage checker and a fresh reader) found 39 more problems in the revision, 9 of them major: statistics the
> kept fields still carried, the derived-constants states, the git route's comparison, the post-hoc cells, the
> caveats of Ghassan's "What this page is not", and the identity of a set whose path the retrain reuses. This draft
> answers both rounds; the appendix says where. The review changed four things Jad was told in chat, and §12 lists
> them for him.

---

## 1. What Jad asked, and what he decided

He asked, 30 September: a page with interactive charts ("when I point at something, the numbers at that point
appear"), with the charts of Ghassan's published page, "and the same thing: make it adaptive, so that if a change
happens it adapts to the change".

| # | question | Jad's answer |
|---|---|---|
| Q1 | where the page lives | **a new tab in our app**, beside the replay lab and the agents page; it reads the latest results every time it is opened. Laptop only, like the rest of the app |
| Q2 | what it shows | **all experiments**: Ghassan's twenty agents, Jad's Phase D, D2 and C4, and every future experiment by itself; each in its own section, labelled with its plant, never pooled |
| Q3 | language | **both**, on the app's language button; preregistered verdicts verbatim in English with an Arabic gloss, as on `/agents` |
| Q4 | how it is built | **in our app's style, from a copy of Ghassan's chart-drawing code**; his page and `make_page.py` untouched |
| Q5 | Ghassan's missing files | **show his section now**, and say on the page, while it is shown, that it is incomplete and what is missing |
| Q6 | a verdict for Ghassan's set, which had no test rule written before training | **judge it by Jad's MEI rule, after the fact, and say so**: a small committed script prints the reading, and the tab quotes it |
| D1 | design part 1, what the tab shows | approved, with the assumption that this tab is not the paused agents page |
| D2 | design part 2, the honesty rules | approved |
| D3 | design part 3, how it is built | approved |

Also this session: the speed idea for the replay lab was cancelled, and the "car stumbles" idea for `/agents`
waits for the retrain (recon, preamble).

**The pause of "the agents page"** (`conflict.md:470`) does not cover this tab: its stated reason is that `/agents`
refuses every agent it replays after the merge, and this tab replays nothing. Jad confirmed the assumption (D1).

## 2. What success looks like

1. Opening `/results` in the lab shows every experiment found in `results/`, each labelled with where its numbers
   came from, in Arabic or English, and every chart shows the numbers under the pointer or a tap, and in a folded
   table under it.
2. After a new drive, a retrain or a new experiment, re-running the scripts that write `results/` and reloading
   the tab is enough, **with three stated exceptions** that need an edit, each dated on the page:
   - the team's judgements typed into the tab (the status pills of §3.4 and the notes of §5.4), which drive C and
     the thermal sub-stepping will move;
   - a new post-hoc reading (§5.3), which is a new capture and new anchors, as every verdict has been;
   - the one-episode chart, which needs Ghassan's code (§5.6).
3. Nothing on the tab is computed that a committed script does not compute, and nothing on it breaks the
   project's wording rules (recon §5).
4. A missing or broken file costs its own section, never the tab.

## 3. What the tab shows

URL `/results` in the lab (`--simulation`), nav label «النتائج» / "Results". From top to bottom:

### 3.1 The summary

One row per experiment section: its name, its plant state (§5.2), and its **short verdict only** (§5.3), or "no
verdict recorded for this experiment". Each row links to its section. The rows obey the same guards as their
sections: a missing anchor or a changed input quotes nothing. Ghassan's row is marked "post hoc"; C4's row says
"continues D2's agents, on the same episodes". One fixed line above the rows: "Each row is a separate experiment,
on its own plant and road; the rows are not to be counted together."

### 3.2 Experiment sections

Order: the experiments the team has run, in the order they ran (Phase D, D2, C4, Ghassan's set), then any new
experiment by name. The order does not depend on git.

**An evaluation experiment** (Jad's Phase D, D2, C4, and any future `results/<prefix>_seed<N>.txt` set):

- *The pairs chart.* For each seed, the sighted agent's and the blind agent's median damage as two marks joined
  by a line, sighted blue and blind amber; the current-grade median as a reference line; the 50-unit MEI drawn as
  a length, labelled "MEI, set 22 September, after this result" on Phase D and unlabelled on D2 and C4. When the
  file carries a thermal-only block (§4.1), a second panel shows the same without the knock term; when it does
  not, the section says "damage without the knock term: not recorded in these files".
- *Against the hand-written policies.* Each agent's median damage beside the baseline ECU, reactive and
  current-grade medians from the same file.
- The verdict block (§5.3), the required notes (§5.4), the plant label (§5.2), and the numbers table of the
  per-seed rows.

**An agent set** (Ghassan's `results/agents/terrain_dt1`, and any future `results/agents/<set>/`):

- The **incomplete box** at the top when something is missing (§5.6).
- The pairs chart as above, from each agent's `eval_summary.json`, with **both** damage and damage without the
  knock term (every `eval_summary.json` carries both). The MEI is labelled "MEI applied post hoc".
- Ghassan's four agent figures, ported (§6.4): every policy over the episodes (`f-eval`), the ablation paired by
  seed in points of damage cut (`f-abl`, the per-seed values only), damage against fuel (`f-trade`), every
  training run (`f-curves`).
- **Two new figures** built from committed files, **in milestone R1b**, because their code is only in Ghassan's
  unpushed commit `a3656ac` and cannot be ported (recon §2): how much rests on the knock model, from
  `knock_margin.json`; what the agents do on the climb, from each policy's `eval_summary.json` `actions`.
- The verdict block (the post-hoc reading of Q6, both ways), the notes (§5.4), the two provenance lines (§5.2).

**A record**: an agent set in which **any** agent's `config.json` has a `status` field containing "NOT A RESULT"
(case-insensitive; today `results/agents/sep19_110kmh`). Folded; the status quoted as its title line, and the
fold names which agents carry it.

**A recorder test run**: a set whose name ends in `_TEST` (`record_agents.py --limit`). Folded, "a test run of the
recorder, not an experiment". None exists today.

### 3.3 The simulator (milestone R2)

The figures of Ghassan's Part 1 that depend on no agent set: the hand-written policies on the locked climb
(`f-trace`, `f-damage`), the premise one change at a time (`f-steps`, a table), the H/τ sweep (`f-htau`), speed
against grade (`f-sweep`), the training roads (`f-roads`). Their notes are in §5.4.

### 3.4 The simulator against the car (milestone R2)

All of Ghassan's Part 2 figures: `f-load`, `f-boost`, `f-enrich`, `f-spark`, `f-th10`, `f-thfit`, `f-th74`,
`f-knock`, `f-gear`, `f-env`, `f-duty`, `f-lit`. Each figure that has a status pill in `template.html` carries it
(`f-thfit` has none), copied as an authored string and labelled "a judgement, not a measurement, as typed in
`results/page/template.html` at `74de99a`, 29 September 2026", which is how `make_page.py:20-22` describes them.
The three kinds (agrees; limited; untested or not covered) get three distinct tones, none red and none green.

### 3.5 Not on the tab

Ghassan's Summary prose, his findings list, "Drives we need" and "What this page is not" (its two caveats that
still hold, the modelled turbine temperature and the unmodelled altitude, travel as notes, §5.4); each figure's take
and caption (the figure carries its title, one line saying what it shows, its pill and its notes instead); the
one-episode chart `c-ep1` (§5.6); the "5–6 times" figure (its definition is only in `a3656ac`); C4's side files
(convergence, tracking, identity); `results/phase_d_130kmh.{txt,json}` as a section (§4.3); anything under
`results/void/`; `results/curve_{sighted,blind}_seed0.csv` (void data, recon §6).

## 4. Finding the experiments

Discovery reads `results/` only, never `runs*/` (gitignored, absent on a teammate's clone). The one exception is
the existence check of the incomplete box (§5.6), which never feeds a section.

### 4.1 Evaluation experiments

- **Candidates**: every file directly in `results/` matching the glob `*_seed*.txt`.
- **Name**: `^(?P<prefix>[a-z][a-z0-9]*(?:_[a-z0-9]+)*)_seed(?P<seed>[0-9]+)\.txt$`. A candidate whose name fails it
  is listed under "files not read: name not recognised" (`run_phase_d.result_prefix` keeps case and hyphens, and
  `--prefix` is free text).
- **Header**: the first line must match
  `^(?P<title>.+?) -- (?:scored on the '(?P<protocol>[^']+)' protocol, )?(?P<n>[0-9]+) FIXED EPISODES, frozen (?P<frozen>.+)$`
  and the file must carry the `--- PLANT FINGERPRINT (this run) ---` block. The three headers of today are
  `PHASE D EVALUATION -- 20 FIXED EPISODES, frozen 18 Sep 2026`,
  `PHASE D2 EVALUATION (randomised climb) -- ...` and `C4 EVALUATION (agents from runs_c4/) -- scored on the 'd2'
  protocol, ...`. A file that fails is listed under "files not read", with the reason.
- **Protocol**: the named group; else the `protocol=` token of the rendered scenario line in the fingerprint block
  (`random-climb` is the d2 protocol; no token is phase-d); else from the title through `evaluate.PROTOCOLS`. An
  unknown protocol makes the plant state "cannot compare".
- **What is parsed**: the fingerprint block, kept as the text lines `fingerprint.format_block` rendered; any `!!`
  lines (§5.2); the policy table (median, IQR width, worst, median fuel, peak per policy); the optional `WITHOUT THE
  KNOCK TERM` block, which `evaluate.py` writes today and Jad's 24 files do not have; the model lines and note lines.
  The episode count comes from the header.
- **Pairs**: a seed with both arms is a pair; an unpaired or unreadable seed is listed, never dropped silently.
- **Name of the section**: `run_phase_d.CLOSED_PREFIX` for a known prefix, otherwise the prefix with "no name
  recorded".

### 4.2 Agent sets

- **Qualifies**: `results/agents/<set>/index.json` exists and names at least one agent.
- **Members**: the keys of `index.json["policies"]`, never a folder listing. `record_agents.py` never deletes a
  folder, so a smaller re-recording into the same set leaves old seed folders; any `*_seed*` folder that
  `index.json` does not name is listed as "left over from an earlier recording, not read".
- **Folders**: each key maps to its folder by `record_agents.py:451`'s rule (spaces become `_`, brackets are
  dropped: `baseline ECU` is `baseline_ECU`, `predictive (hand)` is `predictive_hand`), copied into the reader with a
  test that each folder's `eval_summary.json["policy"]` equals its key. The order is `index.json["policies"]`'s.
- **Not qualifying**, and listed with the reason under "folders not read": a set with no `index.json` yet, and a
  hand-written-only set (`record_agents.py --hand` writes `results/agents/hand_written/` with no agent).
- **Identity comes from the files, not the folder name**: the title shows the training commit
  (`git_head`, or `git_commit` in configs written before the merge), the training dates, and the plant hash when
  one is recorded.

### 4.3 Never twice

- **Rule**: an evaluation experiment and an agent set are candidates for the same agents when the directory an
  evaluation file names for an agent (its model line, or, where there is none, as in Phase D and D2, the path in
  its policy label, such as `agent runs\sighted_seed0`) equals the set's `config.json["output"]`, both normalised
  to relative POSIX paths (and case-folded on Windows). A path is not an identity, because the documented routine
  reuses `runs/terrain_dt1`: candidates become one section only when the training dates or `git_head` also agree;
  otherwise both sections show, each saying "may share agents with <other>; not established".
- `results/phase_d_130kmh.{txt,json}` hold the same agents as `results/agents/terrain_dt1` and match no pattern
  of §4.1; the raw JSON is read only by the cross-check of §4.4.

### 4.4 Cross-checks, run on every open

- **Agent set against the raw file**: an agent row of `phase_d_130kmh_raw.json` is a candidate when its label
  equals the agent's `config.json["output"]` and its `episode` equals the position in
  `eval_summary.json["episodes"]`. The check passes only when every candidate row's seven values equal the set's;
  when the rows exist but disagree, it reads "not compared: the raw file may hold another set recorded under the
  same path", not "failed"; when no row matches, "not compared". Never "passed" over zero rows.
- **Knock margin**: `knock_margin.json["agents"][tag]["cut_orig"]` equals the agent's `summary.cut_pct`. On a
  failure, the knock-model figure is withheld and the section says why.
- **Evaluation experiment**: the medians the tab parsed equal `analyse_phase_d.parse`'s for the same file. The
  comparison with `analyse_phase_d2.load(prefix)`, which reads the real tree only, is a test (§9), not a runtime
  check.
- A failed check never hides a section; it says which check failed and what is withheld.

## 5. The honesty rules

### 5.1 Every number comes from a file or a committed script

- The tab reads values. It computes no new statistic, no average across experiments and no winner.
- **Descriptive exceptions**, each computed by a committed script and tested equal to it:
  - blind minus sighted per seed, printed by the analysis scripts;
  - for agent sets, the fields of Ghassan's `make_page.phase_d()` and `agent_records()` listed as **kept** in §6.4;
  - the counts `analyse_agent_set.py` prints (§5.3): the knock-term count, the worst-episode counts, the fuel
    counts. The tab imports that script's counting functions rather than repeating them.
- **Never computed or shown**: the standard deviation, the t-interval, the paired-t and Wilcoxon p, the mean
  difference, the "within ±0.75 points" count and any classification that uses 0.75 (make_page's "both ways"
  seeds), the verdict ("Indistinguishable from zero."), and the `ablation` blocks of `index.json` and of
  `knock_margin.json["summary"]`, which hold the same statistics. Nothing is taken from `index.json["findings"]`;
  "what a file records" means the fields named in §4 and §6.4, never free text in a file.
- **His English sentences are not copied**: the "reading" sentence ("…comes from learning to protect, not from
  seeing ahead"), the winner sentence ("All N trained agents beat every hand-written policy"), the trade take and
  caption, and the bad-episode sentence. Where the tab needs such a sentence, it builds its own, in both languages,
  from kept fields only.
- **Sentences are built in the browser.** The server sends values, and quoted text marked as quoted; every sentence
  is a template in `results-strings.mjs` filled with values. No typed result is copied from Ghassan's template; one
  of its typed sentences is false today (recon §3).

### 5.2 Where the numbers came from

**Computed per file.** A section shows one state when all its files agree, listing the distinct commits (Phase D's
files record two); otherwise a per-seed breakdown.

**The states**, applied in this order:

1. **Agents scored with a plant mismatch forced**: any `!!` line in an evaluation file. The lines are quoted;
   this state never reads "same plant".
2. **Plant not recorded in this file**: no `plant_sha`.
3. **Made on another plant**: a valid comparison (below) shows a shared fatal field that differs, or a recorded
   `derived_sha` that differs from the live one ("made on another plant: the derived constants differ"). Shows both
   hashes and the recorded plant's tag, under the tag rule below.
4. **Cannot compare**: a `plant_sha` is recorded but no valid comparison exists; or, for an evaluation file only,
   all shared fields agree and a fatal field exists on one side only (after the fingerprint gains a field, agreed
   step 2).
5. **Same plant code as this tree; derived constants not recorded**: a valid comparison with every compared field
   equal, and no `derived_sha` recorded. The fatal fields do not cover `data/derived_params.json`, and a new drive
   changes it.
6. **Same plant as this tree**: as 5, and a recorded `derived_sha` equals the live one.

**What is compared.** For an evaluation file, the fatal lines as text: the live fingerprint is rendered by
`fingerprint.format_block` for the file's protocol and compared line by line with the file's block. For a training
config, which records only `plant_sha` and, from the merged `train.py` on, `derived_sha`: those two fields only;
the one-sided rule of state 4 does not apply to configs. `data_sha1` (kept in a config at
`plant_inputs.data_sha1`) is a secondary fact, never a state: it hashes the logs, not the constants derived from
them.

**A valid comparison** is either the same Python minor version (the plant hash depends on it, recon §7), or a git
route. Under the git route the recorded commit's plant files are read from git and hashed under the server's Python,
and that hash replaces the recorded `plant_sha` in the comparison; a `road_sha` inside a d2 scenario line is
recomputed the same way from the commit's `random_road.py`. The route needs the recorded commit to be here, and:
for an evaluation file, the commit's plant files' byte hash equals the recorded `plant_text_sha` and the recorded
`git_dirty_plant_files` is empty; for a training config, `git_dirty` is false. A training config with `git_dirty`
true records no list of dirty files, so it gets no git route: its state stays "cannot compare" (or "not
recorded"), with the git facts beside it.

**Secondary facts** appear under their own labels in every state and never promote a state: the training commit
and its "uncommitted changes" flag; whether the plant code at that commit, hashed under the server's Python, equals
this tree's; whether a recorded data fingerprint equals the logs on disk ("made from the same logs as on disk"); the
file's last commit.

**Agent sets carry two lines.** "Trained on": from `config.json`, by the rules above. "Scored on: not recorded by
`record_agents.py`; report generated <date, local time>". No state reads "same plant" for a set's scores until the
recorder writes a fingerprint.

**The tag rule.** A recorded plant is named by a tag only for `sep17-before-merge` and `ghassan-before-merge`, and
only when that tag's plant hash equals the recorded `plant_sha`.

**The live side.** `plant_sha` and `plant_text_sha` come from the files on disk. The live `derived_sha` is the tab's
own copy of `train.derived_sha`'s formula over `data/derived_params.json` on disk, and the data fingerprint the tab's
own copy of `derive_params.fingerprint`'s six lines over `data/master_samples.csv` and `data/master_points.csv`;
each copy is tested equal to the original, run in a subprocess. **The results modules never import
`derive_params`** (it sets `DERIVING_PARAMS=1` for the whole process, which turns `derived.py`'s missing-constant
errors into NaN for every page), **`record_agents`, `knock_margin` or `train`** (import-time environment changes, and
`train` imports the plant). The other fatal fields come from modules imported when the server started. The plant hash
is taken once at import too; if the files on disk differ from it, the page says "the plant files changed after the
server started; restart the server" and shows no "same" state. The same holds for `derived.py`'s cached constants
against `data/derived_params.json` on disk.

**Dates** always say what kind they are: committed; generated, local time, timezone not recorded; run from commit;
episodes frozen, as printed by `evaluate.py`. A file that `git status` shows modified or untracked reads "changed
since its last commit (<date>)", and its last commit is not shown as a fact about it. File modification times are
never used.

**Words never used**: current, stale, outdated, fresh, up to date.

**Today's labels**, from the recon: Jad's three experiments, "made on another plant" (`b5a3069f32a83754`, the plant
of `sep17-before-merge`; this tree `c236a8db3e201090`); they record Python 3.12.10, as this machine runs, so the
comparison is direct. Ghassan's set: trained on "plant not recorded in this file", with the facts "trained from
commit `cbb8d09` with uncommitted changes (which files not recorded)", "the plant code at that commit equals this
tree's", "made from the same logs as on disk"; scored on "not recorded". The simulator sections: "plant not recorded
in this file", with each file's last commit.

### 5.3 Verdicts are quoted

- Through `app.agent_catalog.verdict(key)`: the anchored lines with file and line, the authored short verdict and
  the Arabic gloss, as `/agents` shows them. When the state is `none`, the tab shows its own line, "no verdict
  recorded for this experiment", never the returned `short`, which says "Nothing on this page is a result".
- **Ghassan's set (Q6), with both damage measures.** A new script, `analyse_agent_set.py <set>`, reads the set's
  members from `index.json`, pairs the arms by seed, and prints blind minus sighted median damage per seed, then
  the MEI-rule reading from `analyse_phase_d2.classify` (imported, never copied; `report()` is never called, because
  it prints two sentences that are false for this set). **It prints the reading twice: on damage, and on damage
  without the knock term**, as the team agreed to report every result until drive C. In memory, the recon (§6) gives
  6 of 10 positive and INCONCLUSIVE on damage, and the design review gives 4 of 10 positive and INCONCLUSIVE on
  thermal-only damage, where the sign and permutation tests disagree on "smaller than the MEI" (the merge review's
  figures, `conflict.md:195-198`); the committed capture, not this sentence, is what the tab quotes.
- **Where the two tests disagree**, the script prints a "THE TWO TESTS DISAGREE" block, as `report()` does for C4;
  it gets an anchor, and the post-hoc short verdict requires that anchor, as C4's requires its own.
- **It also prints**, for the notes of §5.4: per seed, the knock term alone (damage minus damage without it) for
  each arm, the count of seeds in which the sighted agent's is smaller, with its sign test; per arm, the count of
  agents whose worst episode is above current-grade's worst; the count of agents that burn less fuel than the
  baseline ECU, and the range of the others. The tab imports these counting functions and a test checks the capture
  against them.
- **Its heading**: "POST HOC: the design was committed before training, but no test, MEI or decision rule was; the
  team's MEI rule (set 22 September) is applied after this result."
- **Its inputs line**: one function in `analyse_agent_set.py`, which the tab imports, hashes for each seed in
  ascending order the pair (sighted, blind) of `float(summary.damage.median)` and of
  `float(summary.damage_thermal.median)` as stored, and `analyse_phase_d2.MEI`, in a fixed text format, with
  SHA-256, first 16 hex. The capture also prints the set's training commit and the report's generated date.
- It refuses more than 20 pairs (the permutation test enumerates every sign pattern).
- **The capture**: written once, UTF-8 without BOM, by Python or bash (PowerShell's `>` writes UTF-16), ASCII only,
  committed as `results/agents/terrain_dt1/POSTHOC_MEI.txt`, inside the folder `verify_docs.py` already exempts as
  generated agent reports, so a coincidental match with a retired figure cannot block the guard on a file that may
  never be edited. **It is never overwritten**; a later reading of another set is a new file. Comparisons with it
  normalise line endings (the repository checks out with `core.autocrlf=true`).
- **Keys**: the anchors live in their own namespace, `posthoc:terrain_dt1`, which no result prefix can produce
  (`run_phase_d.result_prefix("runs/terrain_dt1")` is `terrain_dt1`, the key Ghassan's draft `/agents` would look
  up). Two new cells with distinct names, "INCONCLUSIVE (post hoc, total damage)" and "INCONCLUSIVE (post hoc,
  without the knock term)", each with its own authored gloss in Arabic and English saying the reading came after the
  result; the existing post-hoc gloss names Phase D and cannot be reused.
- **The guard, inside `verdict()` for post-hoc keys, so every caller gets it**: the inputs hash is recomputed from
  the files. On a mismatch the block says "this post-hoc reading belongs to other numbers than these; no reading is
  recorded for these" and quotes nothing. It gives no advice to re-run: after the next retrain the new set in that
  folder gets its own preregistration (agreed step 5).

### 5.4 Required notes

Notes are authored strings, dated, cited to the file that states them, in both languages. A number in a note comes
from the data wherever a file records it. Where no file does (the Phase D and D2 budgets, the +4° action bound), the
number is typed, with its date and its source named beside it.

- **Every agent result, until drive C is recorded**: the supervision margin over current-grade rests on the
  knock model, which is untested on the car.
- **Every section that shows a turbine temperature** (the policy tables' peak column, the charts, the 850 °C
  trigger): "modelled, not measured: no sensor on this car reads it, and its heat capacity, `c_turb`, is assumed; it
  sets τ" (CLAUDE.md, "Limits the live app adds").
- **The one-step knock spike**: it sits inside every Phase D, D2 and C4 episode (the locked climb and the D2 roads
  are both instantaneous grade steps), and whether it moved their preregistered results was never measured
  (`conflict.md:199-203`). Ghassan's set was scored on the same locked climb, and there it was measured: on the knock
  term alone the sighted agent beats its blind twin in 10 of 10 seeds, the only significant preview effect in his
  retrain (`conflict.md:194-197`). The tab takes that count from `analyse_agent_set.py`'s output, never typed.
- **Phase D, D2, C4**: the training budget (C1, 50 000 steps, from the preregistrations; C4 300 000 steps, from its
  files, not converged); Phase D's blind arm is not blind; trained at a 0.2 s step and scored at 1.0 s; "every agent
  pushes spark to the +4° bound (trim measured); the margin with advance forbidden was measured for C4 on one episode
  and not for Phase D or D2" (the merge report); "no thermal-only damage was recorded in these files".
- **Ghassan's set**: the budget and step from `config.json`; the test set is the locked climb only, which is one of
  the training road families; the knock-margin figure is "a diagnostic, not the protocol" (quoting
  `knock_margin.json["what"]`) and "a lower bound: an agent trained without the lever could do better than one that
  has it taken away" (cited to `results/agents/terrain_dt1/KNOCK_MARGIN.md`); the worst-episode and fuel counts
  from `analyse_agent_set.py`; "scored: the scoring run's commit and plant were not recorded".
- **The hand-written figures**:
  - `f-trace`, `f-damage`, `f-steps`, `f-htau`: "hand-written policies cannot settle the preview question"
    (`AUDIT.md` C3);
  - `f-damage`: the preview-over-current-grade figure with and without the knock term, from the port of
    `make_page.py`'s split block (§6.4), which computes both from `traces_130kmh.json`;
  - `f-steps`: "damage without the knock term: not recorded per step"; the split block's thermal-only figure is
    quoted for the plant of today only;
  - `f-htau`: "not quotable until the thermal network is sub-stepped";
  - `f-trace`, `f-sweep`, `f-roads`: "altitude is not modelled: the engine breathes sea-level air the whole way".
- **An unknown future experiment**: only what its files record in the fields of §4 and §6.4, the knock-model and
  turbine notes above, and "no other notes recorded for this experiment".

### 5.5 Forbidden wording

- "Preview does not help" in any form, including «المعاينة لا تفيد» and «الاستباق لا يفيد»; "adds nothing
  measurable"; "comes from learning to protect, not from seeing ahead"; reading "beats current-grade" as evidence
  for preview; pooling two experiments; calling C4 a replication of D2; rescuing a null with H/τ.
- The words of §5.2 (current, stale, outdated, fresh, up to date, and their Arabic forms), with "current-grade"
  and its Arabic name exempt.
- Checked in both languages by two tests: a Node test over every string and sentence template of
  `results-strings.mjs`, and a Python test over every `SHORT_VERDICT` and `GLOSS` entry of `agent_catalog.py` (the
  existing ones too, since the tab shows them) and over the text values of the real tree's `/api/results` answer.
  Quoted anchor text is exempt, being verbatim (it contains the phrase inside a negation), and is pinned by the
  anchor test.

### 5.6 Incomplete, missing, broken

- **The incomplete box (Q5)**, per agent set, computed on every open. For each item it says what it would give and
  which of three states holds:
  - *never recorded* (for example `config.json` has no `recorded_steps`);
  - *recorded, but not in this copy of the project* (gitignored, or on the training machine);
  - *a file of that name exists; whether it belongs to this set is not recorded*.

  The items: the step-by-step records (`train_record.npz` and `eval_record.npz` in each policy's folder under
  `results/agents/<set>/`); the trained models (`final.zip` under the directory `config.json["output"]` names); and
  the one-episode chart (`results/agents/<set>/episode_trace.json`).
- **The one-episode chart needs more than the file**: its layout and drawing code are only in `a3656ac`. Until that
  commit arrives, the box keeps the line "the one-episode chart: waiting for Ghassan's `episode_trace.json` and the
  code that draws it", even if a file of that name appears.
- **A section that cannot be built** says why, and nothing else of the tab is affected:
  - a missing input names the file and the command that makes it (§6.3);
  - any other failure reads "could not read <file>: <error type>", with no command, because advice to re-run a
    script for a file that is present would send the reader the wrong way.
- **A module that cannot be imported** (for example `evaluate`, whose import runs `random_road`'s check of the
  locked climb, which agreed step 4 will edit) is caught once per build and shown as one line at the top of the tab,
  naming the module and the error type, and every section that needs it says "needs <module>, which could not be
  loaded". It is never reported as a fault in a file.

## 6. The server side

### 6.1 Routes

Registered only under `--simulation`, like `/agents`, through a function `mount_results(app)` in
`app/results_api.py`, called beside `install(app)` in `main()`. The function is not named `install`, so the pin "one
call named `install(`" holds, and `--live` and `--replay` never load the readers, which import agent code
(`app.agent_catalog`, `evaluate`, `random_road`). The lab's nav link to `/results` therefore 404s outside the lab,
as its `/agents` link already does.

- `GET /results`: the page, read from `app/static/results.html` on every request.
- `GET /api/results`: every section, rebuilt from the files on every request. No parameter: nothing from the
  request reaches the filesystem. Its cost is not measured yet: make_page's readers take about 0.12 s warm and
  0.8 s cold (recon §1), and git about 0.04 s (recon §7); R1a measures the whole build and writes the figure into the
  build record.
- Both are synchronous `def` handlers, like every route in `server.py`, so the build runs in the thread pool and
  never blocks the event loop. One build runs at a time (a lock); a second request waits for it.
- Both answer `Cache-Control: no-store`, the 403 included.
- **The guard**: a request whose raw `Host` header is not `127.0.0.1` or `localhost`, with any port or none, gets a
  fixed-text 403. That stops DNS rebinding. No `Origin` is required; a browser does not send one on a same-origin
  GET. The pattern is copied into `app/results_api.py` (importing it from `app.agent_api` would load agent code),
  with a test that it accepts what `agent_api.LOCAL_HOST` accepts plus a port-less host.
- The whole build is wrapped: a failure outside every section returns a no-store 500 with a fixed text, never
  `str(exc)`.

### 6.2 Modules

| file | what it does |
|---|---|
| `app/results_api.py` (new) | `mount_results(app)`: the two routes, the guard, the lock |
| `app/results_data.py` (new) | discovery (§4), the readers (§6.4), the cross-checks, and `build(results_root, git_root)`, which returns `{built, sections, not_read}`. Each section is built inside `try: … except (Exception, SystemExit)`, since `make_page.py`'s readers raise `SystemExit`; nothing broader is caught |
| `app/results_provenance.py` (new) | the live side and the states of §5.2; one git helper for every git call |
| `analyse_agent_set.py` (new, repository root) | §5.3. Prints only; writes no file |
| `app/agent_catalog.py` | the `posthoc:` namespace: anchors, cells, short verdicts and glosses for `results/agents/terrain_dt1/POSTHOC_MEI.txt`, and the inputs-hash guard in `verdict()`. The dictionaries at `:228-321` are not touched by Ghassan's draft branch |

Every reader takes `results_root` and `git_root`, so tests run on temporary trees. `make_page`'s readers use the
module global `RES`; the tests patch it in the test process only, and `results_data.py` patches no module global.

### 6.3 Git, and the command behind each file

- **The git helper**: `GIT_OPTIONAL_LOCKS=0` is set in `os.environ` when `app/results_provenance.py` is imported,
  before any fingerprint call, because `fingerprint._git` runs `git status` with the inherited environment and
  could otherwise rewrite `.git/index`. Every call has a timeout. Git missing, no `.git`, a timeout or "dubious
  ownership" give one state, "git unavailable", in which the git facts are omitted and nothing else changes. A
  recorded short commit is resolved with `git rev-parse --verify <sha>^{commit}`; an ambiguous or unknown one
  reads "commit not found here".
- **One pass per build**: `git log --format=%x00%h%x09%cI --name-only --diff-merges=dense-combined` over
  `results/` and `data/derived_params.json`, and one `git status --porcelain` over the same; the plant hash of a
  recorded commit is cached per commit, since a commit never changes.
- **The command that makes each file**, named when the file is missing: `run_results.py` (traces, sweep, raw
  file), `check_roads.py`, `model_vs_data.py`, `compare_calibration.py`, `generality_test.py`,
  `calibrate_thermal.py`, `check_premise.py`, `record_agents.py runs/<set>`, `knock_margin.py`, `evaluate.py`
  through `run_phase_d.py`, `analyse_agent_set.py <set>`. The tab never runs any of them.
- **The working order after a plant change**, written into the page's help line: `run_results.py phase_d`, then
  `record_agents.py`, then `knock_margin.py`. The recorder compares its hand-written rows with the raw file and stops
  when they differ, so the raw file comes first. Between the first two runs the raw-file check of §4.4 reads "not
  compared"; between the last two, the knock-margin check fails and the knock-model figure is withheld.

### 6.4 Readers

- **The simulator and the car** (R2): `make_page.model_vs_car`, `training_roads`, `calibration` and `generality`,
  called as they are, imported inside the build. `make_page.main()` is never called; it writes Ghassan's page.
- **The locked-climb traces, the speed-grade sweep and the damage split** (R2): a port of the first part of
  `make_page.phase_d()` (`make_page.py:57-79`) and of its split block (`make_page.py:210-230`), which computes each
  hand-written policy's damage with and without the knock term from `traces_130kmh.json`; `phase_d()` itself needs an
  agent set.
- **`cal.boost.at_climb`** (R2) joins `model_vs_car`'s `duty.scen_rpm` and `calibration`'s `boost.bands`; it belongs
  to the car-comparison reader, names both files, and is `null` ("not available") when the climb's band has no car
  reading, where `make_page.main()` raises `StopIteration`.
- **Agent sets** (R1b): a port of the per-set part of `make_page.phase_d()` and of `agent_records()`, parameterised
  by set, reading the set's own folder, never `make_page.AGENT_SET` (which silently mixes sets) and never scipy.
  - **Kept from `phase_d()`**: per policy the median, quartiles, worst, fuel, fuel against the baseline, peak and
    cut; per seed the sighted and blind cuts, their difference and their fuels; the training curves.
  - **Kept from `agent_records()`**: the baseline's knock integral and spark on the climb; each agent's spark trim
    and knock integral on the climb; from the knock-margin summary, the cuts with and without spark advance per arm,
    current-grade's cut, how many agents still beat it, the median margin over it both ways, and the knock-integral
    range; per agent, the episodes on which it does more damage than the baseline ECU, their worst damage and peak.
    **Dropped**: the knock-margin `ablation` fields (`abl`, `abl_lo`, `abl_hi`, `abl_pw`) and the `bad_sentence`.
  - **The life weights** (`w_life_max`, `lowest`: whether an agent's bad episodes are the ones with the lowest weight
    on component life) come from `evaluate.EPISODES`, since no file of the set records weights; they are used only
    when the set's recorded `protocol` names `evaluate.EPISODES` and its episode count equals that table's length.
    Otherwise they are withheld, and the section says why.
  - The kept fields are tested `==` against `make_page` on the real tree when all 480 raw-file episodes agree with
    the set (§4.4) and scipy can be imported (`make_page.phase_d()` imports it); otherwise that test is skipped with
    its reason. The port itself never imports scipy.
  - **No new keys** beyond the kept ones: the counts the bilingual sentences need come from `analyse_agent_set.py`'s
    functions (§5.3). make_page's "both ways" seeds, which rest on the 0.75-point rule, are not ported.
- **The two new agent-set figures** (R1b): designed from `knock_margin.json` and the `actions` blocks, with their
  own data shape and tests. The actions axis is sized from the data and the neutral value, never from the live
  `engine_env` bounds, which the agreed spark cap will move. Every hand-written policy whose file has `actions`, the
  baseline ECU first, then every agent.
- **Evaluation experiments** (R1a): the parser of §4.1.
- **NaN and infinity** become `null` before the answer; a test serialises the real tree's answer with
  `allow_nan=False`.

## 7. The page

### 7.1 Files

| file | what it holds |
|---|---|
| `app/static/results.html` (new) | the frame: the lab's topbar, nav, language and theme buttons, the lab's pre-paint script (`grad.sim.theme`, `grad.sim.lang`), a host per section. **No figures in it**: `verify_docs.py` reads `.html` |
| `app/static/sim/charts-lib.mjs` (new) | the copy of Ghassan's generic drawing code (about 270 lines, recon §1), adapted as in §7.3 |
| `app/static/sim/results-charts.mjs` (new) | per figure, a **pure layout function** (domains, marks, tooltip rows, table rows) tested under Node, and a thin drawing step |
| `app/static/sim/results.mjs` (new) | boots the page, fetches `/api/results`, renders the sections, handles language, theme and errors |
| `app/static/sim/results-strings.mjs` (new) | every string and every sentence template, Arabic and English, merged into `i18n.mjs`'s table by a small merge of its own; it never imports `agents-strings.mjs`, which merges every `/agents` string on import. The five lever names are copied from `agents.action.*`, with a test that they equal them. Written through Python and byte-checked (the Write tool decodes `\u` escapes) |
| `app/static/sim/results.css` (new) | the tab's styles, its resets and its `--rc-*` colours for both themes |

`results.html` loads `style.css`, then `agents.css` (the nav on its own row on phones, the sighted and blind
colours, the verdict quote styles), then `results.css`. `isolateLtr` is imported from `agent-picker.mjs`. Every
import of the tab's own modules carries a version query (`?v=R1a` and so on, the same in every import, checked by a
test), because `/static` sends no `Cache-Control` and a browser could run an old module against a new answer.

### 7.2 Text

**Per figure**, both languages: the title, one line saying what it shows, the axis titles, legend and tooltip
keys, the pill where there is one, and the notes of §5.4. No take or caption travels. **Axis titles are HTML**,
placed beside the chart (the x title under it, the y title above it), not SVG text, so they follow the rule of §7.3.

**English that arrives from the data:**

| kind | treatment |
|---|---|
| policy roles, arm and seed, road families, enrichment dwell labels, `validate.py` row names, lever names | translated through a keyed map; a value the map does not know is shown in English inside an FSI isolate, never dropped |
| verdict lines, a record's status, evaluation notes, the scenario line, error texts | quoted as they are, in a `dir="ltr"` block |
| every number, range, date, hash, unit and drive name (`drive10`, `pull01`, `7475b5d7`) inside Arabic text | wrapped in an LRI … PDI isolate at substitution; minus U+2212; thousands U+202F |

Table cells align to `start`, so they follow the page's direction. "baseline ECU" follows the wording rule `/agents`
already has for the engine computer.

### 7.3 Changes to the copied drawing code

- **Resets, not only a prefix.** The app's `svg{width:20px;height:20px;fill:none;stroke:currentColor;
  stroke-width:1.6}` is an element rule and matches every chart whatever its class, so `results.css` resets it on
  `.rc-chart > svg` (size from the attributes, `fill` black, `stroke: none`, width 1, butt caps, miter joins) and on
  the chart text. Other element rules that reach the tab (`a`, `dl`, `dt`, `dd`, `h2`, `footer`, `button`, `body`
  font size) get explicit rules for the tab's elements. The browser check verifies a chart's rendered size equals its
  attributes and a chart label's computed stroke is none.
- **Colours**, one table in `results.css` for both themes, each role distinct from every other shown on the same
  figure: sighted blue and blind amber from `agents.css`; the four hand-written policies (predictive (hand) not
  amber); the car and the simulator in the R2 figures (Ghassan's car blue and simulator orange sit too close to the
  sighted and blind pair, so both change); before and after; the heat ramps; the 850 °C trigger; the three pill
  kinds. **No red and no green anywhere on the tab**, as on `/agents`.
- **Bidi in SVG.** Chart hosts are `direction:ltr` (with `dir=rtl`, 323 of 613 labels moved, recon §8). SVG labels
  carry only numbers, units, symbols and Latin; every Arabic word of a chart goes into HTML (the title, the legend,
  the tooltip), where the isolates of §7.2 apply. A Node test fails if an Arabic letter reaches an SVG label.
- **Tooltips in Arabic**: `html[dir=rtl] .rc-tip{direction:rtl}`, values isolated, and no ellipsis on labels.
- **Label widths are measured** (`getComputedTextLength`), not estimated at 6.8 px per character, and the label
  column is sized from the measured labels.
- **The heat legends** say "stronger colour = more", which is true in both themes, so a theme switch still redraws
  nothing.
- **A language switch redraws every chart**; a theme switch redraws none (every colour is a variable).
- **Every chart** gets a translated `aria-label` and a folded "the numbers" table built from its layout function's
  rows. The focusable marks are not placed inside `role=img`. A crosshair or nearest-point chart also steps with the
  arrow keys.
- A chart that fails to draw writes a translated "not available" note in its host, not only to the console.
- A teardown, so reopening the tab does not stack listeners.
- The defects of recon §3, fixed in the copy: axis domains from the data where his were fixed and clip today
  (`c-boost`, `c-boostB`); `pointerdown` on `c-gear`; no bar of negative width (`c-abl`, and the new knock-model
  figure); rows chosen by name, never by position.

### 7.4 Nav

The link «النتائج» / "Results" is the third link in `simulation.html` and `agents.html`, never the last (the lab's
phone rule hides the last link). `nav.results` goes into `i18n.mjs` right after `nav.agents`. The two pinned nav
tests (`app/test_agents.py:3795-3802`, `agents-page.test.mjs:100-109`) change in the same commit. The browser check
opens `/simulation` and `/agents` at 390 px in both languages; if the lab's nav overflows its row, `simulation.html`
gets the own-row rule `agents.css` already has.

## 8. What else the change touches

`app/server.py` (the `mount_results(app)` call, the `--simulation` banner line, the docstring's route list),
`app/start-simulation.ps1` (the banner), `app/README.md` (the page table), `CLAUDE.md` (the repository layout and the
numbers-that-matter line for `analyse_agent_set.py`), `results/README.md` (the capture), `full_run.py` (a block for
`analyse_agent_set.py terrain_dt1`, whose output must equal the committed capture), `app/test_agents.py` (the nav
pin, `CatalogTests`' key sets, `NEW_MODULES`) and `app/static/sim/agents-page.test.mjs` (the nav pin).

## 9. Tests

**Python, `app/test_results.py` (new):**

1. The ports: the traces, sweep and damage split equal `make_page.phase_d()`'s; the kept fields of §6.4 equal its
   per-set output and `agent_records()`'s for `terrain_dt1`, run only when all 480 raw-file episodes agree with the
   set; each skipped, with its reason, when scipy cannot be imported (a lab-only install has none).
2. The evaluation parser against `analyse_phase_d2.load(prefix)` on the real tree, for all three prefixes; the
   thermal-only block, the `!!` lines and a backslash model line on temporary-tree files.
3. Discovery on temporary trees: a new prefix and a new set appear; `phase_d_130kmh.*`, `c4_convergence.txt`,
   `results/void/*` and `results/curve_*.csv` never do; a badly named `*_seed*.txt`, a `hand_written` set and a set
   without `index.json` are listed as not read; a stale seed folder is listed as left over; each key's folder holds
   an `eval_summary.json` whose policy equals the key; a `_TEST` set and a record fold; the same agents scored both
   ways are one section, and two sets recorded under the same path are not joined.
4. The plant states: each of the six, including "same code, derived not recorded", "the derived constants differ"
   and the forced state; the order of precedence with an extra live field; the fatal lines compared as rendered
   text; Jad's files with commit and tag; Ghassan's set with its facts; a config under another Python, and one with
   `git_dirty` true; a modified result file; "git unavailable" (git removed from `PATH` in the test process).
5. Failure: a missing, empty or half-written file makes only its section unavailable, with the right message kind;
   a reader raising `SystemExit` is caught; a `KeyboardInterrupt` is not; a module that fails to import gives the one
   tab-level line; NaN becomes `null`; the real tree's answer serialises with `allow_nan=False`.
6. Routes: present under `--simulation` only; both `no-store`; a foreign `Host` gets a no-store 403; a port-less
   `localhost` is accepted; only GET; importing `app.server` loads none of the pinned modules; the page's assets, ids
   and imports resolve (as the two lab pages' tests already check).
7. The post-hoc reading: `analyse_agent_set.py terrain_dt1` prints the committed capture, line endings normalised;
   its numbers equal `classify`'s, both ways; its counts equal the functions the tab imports; the anchors each match
   one line, the disagreement anchor included; a changed input gives "belongs to other numbers"; the `posthoc:` key
   cannot equal any result prefix; more than 20 pairs is refused.
8. Side effects: `.git/index` is unchanged after `build()`; `DERIVING_PARAMS` and `OMP_NUM_THREADS` are as they were
   after `build()`; the tab's data fingerprint equals `derive_params.fingerprint()` and its `derived_sha` equals
   `train.derived_sha()`, each computed in a subprocess, and each skipped with its reason when pandas or torch is
   missing.
9. The write scan: `app/results_api.py`, `app/results_data.py` and `app/results_provenance.py` join the agents
   suite's `NEW_MODULES` (its scan reads names under `app/`); `test_results.py` runs the same `WRITE_PATTERNS` over the
   root-level `analyse_agent_set.py`.
10. Wording: the §5.5 and §5.2 checks over every `SHORT_VERDICT` and `GLOSS` entry of `agent_catalog.py` and over the
    text values of the real tree's `/api/results` answer, in both languages, quoted anchors exempt.

**Tests that change:** the two nav pins (§7.4) and `CatalogTests`' exact key sets (`app/test_agents.py:801-803`),
which the `posthoc:` entries move.

**Node, `app/static/sim/results-*.test.mjs` (new):** the Arabic and English tables have the same keys; the wording
of §5.5 and §5.2 over every string and sentence template, both languages; number formatting (isolates, U+2212,
U+202F); no Arabic letter in an SVG label; each layout function's domain contains all its data; a negative value
still gives a visible bar and tap target; tooltip and table rows per figure; the lever names equal
`agents.action.*`'s; the version query is the same in every import.

**In the browser**, before each milestone is called done: headless Chrome at 1440 px and in a 390 px frame (the
browser here will not lay out below 500 px), both languages, both themes; the new tab, and `/simulation` and
`/agents` for the nav; a tooltip opened on one point of each chart kind, by pointer and by keyboard; a chart's
rendered size equals its attributes; no console error. Screenshots stay in the session scratchpad.

**The project's checks** pass before each milestone is committed: `python -m app.test_results`,
`python -m app.test_agents`, `python -m app.test_simulation`, `python -m app.test_replay`,
`node --test "app/static/sim/*.test.mjs"`, `python verify_docs.py`, `python drift_test.py`.

## 10. Milestones

| milestone | contents | done when |
|---|---|---|
| **R1a: the frame and Jad's experiments** | routes, guard, lock; `results_data`, `results_provenance`; the page, nav, drawing-code copy, summary; the three evaluation experiments with the pairs chart, the hand-written comparison, verdicts, notes, plant labels and tables; strings; tests | Jad opens `/results` and sees Phase D, D2 and C4, each labelled and quoted, in both languages |
| **R1b: Ghassan's set** | `analyse_agent_set.py`, its capture and the `posthoc:` anchors; the agent-set reader and port; the pairs chart both ways; `f-eval`, `f-abl`, `f-trade`, `f-curves`; the two new figures; the incomplete box; the two provenance lines; the record fold | his section shows with its post-hoc reading both ways and the incomplete box |
| **R2: the simulator and the car** | §3.3 and §3.4, their readers, strings and tests, and the defect fixes that belong to them | every figure of Ghassan's Part 1 and Part 2 is on the tab, with pointer, tap and table numbers |

**Estimates, as agent work, with the Arabic writing and its byte check:** R1a three to four hours, R1b three to four
hours, R2 three to four hours; nine to twelve hours in all. Each milestone ends with the checks of §9, a commit, and
a short note to Jad saying what now works.

## 11. Not in this work, and notes for the team

- Opening the tab from a phone (the server listens on 127.0.0.1 only).
- The one-episode chart and the "5–6 times" figure (§5.6).
- Ghassan's draft branch `origin/GRA-2340394`, including its `.mjs` MIME fix: on a machine whose registry serves
  `.mjs` as text, this tab renders empty like the other lab pages until that fix is merged (recon §9).
- Moving `results/curve_{sighted,blind}_seed0.csv` into `results/void/` (a repository decision for Jad).
- The defects in Ghassan's own page (recon §3): his to fix; the tab only avoids copying them.
- The "car stumbles" idea for `/agents`.
- **For the team, before the next retrain.** The documented routine re-records into `results/agents/terrain_dt1`,
  which would replace Ghassan's twenty on the tab (and would leave old seed folders behind, which §4.2 now handles).
  Recording the next set under a new name (`record_agents.py ... --name <set>`) keeps both. And the routine's order
  must be `run_results.py phase_d` before `record_agents.py` after any plant change (§6.3); CLAUDE.md lists the
  reverse.

## 12. What the review changed from what Jad approved in chat

1. **The size**: nine to twelve hours of agent work in three milestones, not four to eight in two, because of the
   Arabic writing, the extra checks, and two figures that have to be designed rather than copied.
2. **Ghassan's verdict is shown twice**, with and without the knock term, as the team agreed to report every result
   until drive C. The two readings differ in detail (§5.3).
3. **The tab lives in the lab mode only** (`--simulation`), like the agents page, so the program that reads the car
   never loads agent code.
4. **Two of Ghassan's newest figures are new work**, not copies: their code exists only in his unpushed commit.

## Appendix: where each review point is answered

The 45 distinct points (80 claims, duplicates merged by the verifier), by the section that answers them.

| section | points |
|---|---|
| §2 | the typed judgements and the post-hoc capture as named exceptions to "no edit" |
| §3.1 | summary rows: short verdict only, the guards, the post-hoc and "continues D2" marks, the "not to be counted together" line |
| §3.2 | both damage measures; the MEI labels; c-km and c-act as new R1b work; the record rule on any agent; the `_TEST` fold |
| §3.5 | takes and captions not carried |
| §4.1 | the outer glob; the header pattern and the three headers; the protocol; the thermal-only block; `!!` lines; section names |
| §4.2 | members from `index.json`; left-over folders; names and order; non-qualifying folders listed; `git_head` or `git_commit` |
| §4.3 | never twice, by the model directory |
| §4.4 | the raw-file match rule and "not compared"; parse rather than load at runtime |
| §5.1 | the kept and never-shown fields of the port; the index.json ablation block |
| §5.2 | per-file states; precedence; "same code, derived not recorded"; the forced state; the config git route; two lines for sets; the tag rule; modified files; memory against disk and the restart rule; the data fingerprint without `derive_params` |
| §5.3 | the `posthoc:` namespace; `classify` only; the heading; the hash definition; both measures; the capture's encoding and permanence; the guard inside `verdict()`; the `none` text; n above 20 |
| §5.4 | the spike note for every experiment; the knock-term 10 of 10 figure from a script; per-prefix knock-margin wording; Ghassan's set caveats; the hand-written figures' notes |
| §5.5 | the Arabic forms; "adds nothing measurable" and "learning to protect"; the banned words and the current-grade exemption; the quoted-anchor exemption; the sources the test covers |
| §5.6 | the box's three states and the right paths; the two kinds of failure message |
| §6.1 | lab mode only; sync handlers; the lock; the Host pattern with any or no port; the no-store 403; the outer wrapper |
| §6.2 | `except (Exception, SystemExit)`; roots for every reader; no module global patched |
| §6.3 | the git helper, process-wide `GIT_OPTIONAL_LOCKS`, timeouts, "git unavailable", short-SHA resolution; the working order after a plant change |
| §6.4 | `at_climb` moved and made safe; the kept, new and dropped keys; no scipy; weights from the set's files; the actions axis |
| §7 | the CSS resets; the colour table; SVG labels without Arabic; rtl tooltips; measured labels; the legend wording; strings merged without `agents-strings.mjs`; `isolateLtr`'s source; `agents.css`; the storage keys and pre-paint; the data-string table; aria, keyboard and tables; the version query; the nav check at 390 px |
| §8 | the banner, README, CLAUDE.md, results/README.md and `full_run.py` |
| §9 | the tests of every point above, the `CatalogTests` pin, the write scan, the assets test, the real-tree strict JSON |
| §10 | R1 split into R1a and R1b; the estimates restated |
| §11 | the retrain overwrite and the routine's order, for the team |

**The second pass**, by the section that answers it: §5.1 (the knock-margin `ablation` fields, the 0.75-point "both
ways" seeds, `index.json["findings"]`, where sentences are built); §5.2 (`derived_sha` against `data_sha1`, the live
`derived_sha`, "the derived constants differ", configs compared on `plant_sha` and `derived_sha` only, the git route
rehashing under the server's Python and recomputing `road_sha`, dirty configs, fatal lines compared as rendered text,
the imports never made); §5.3 (the two cell names, the disagreement anchor, the counts the script prints, the
capture's folder and line endings, the citations); §5.4 (the spike note measured for Ghassan's set only, the turbine
and altitude notes, `f-steps` without a thermal-only figure, typed numbers with their sources, the "lower bound"
citation); §5.6 (the import-failure line); §4.1 (the protocol from the rendered scenario); §4.2 (the key-to-folder
rule); §4.3 and §4.4 (a path is not an identity; separators; the raw-file check that does not "fail" on another set);
§3.4 (the pills' source, date, `f-thfit`, three tones); §6.1 (the build time left unmeasured); §6.3 (the three-step
order); §6.4 (the kept fields named, the life weights' condition, the split block, scipy); §7.1 and §7.2 (the lever
strings, axis titles in HTML, drive names isolated, cell alignment); §7.3 (the colour roles of R2); §8 and §9 (the
new suite in the checks, the skips, `NEW_MODULES` for `app/` files only, the Python wording test, the added cases).

---

## Build record, R1a

Built on 2026-10-06, branch `JMF-2340550-results-tab`, by the R1a plan, task by task. Every figure in this record is copied from the run it names; the outputs themselves stay in the session scratchpad.

### What was built

- **The server side, under `--simulation` only.** `app/results_eval.py` parses an `evaluate.py` result file; `app/results_provenance.py` gives each file its plant state (§5.2), with git and the fingerprint of this tree; `app/results_data.py` finds the experiments in `results/` (§4.1), builds one section each with its notes, its quoted verdict and the cross-check against `analyse_phase_d.parse` (§4.4); `app/results_api.py` serves `GET /results` and `GET /api/results` behind the Host guard, one build at a time, `no-store`. `app/server.py` mounts them right after `install(app)`.
- **Two changes the spec did not name, from the plan's review.** Mounting imports `app.results_provenance`, so the plant hash the tab compares against is taken when the server starts, which is when the server loaded the plant (§5.2). And `/static` now answers `Cache-Control: no-cache` in every mode: §7.1 records that it sent none, and R1a changes `i18n.mjs` and `style.css`, which the pages load without a version query, so a browser could keep running its cached copies after an update. That covers every later update. For this one, a browser that cached the lab's files before it needs one reload with the cache bypassed (Ctrl+F5), or its nav shows the key `nav.results`; `app/README.md` says so (Task 5's review).
- **The page.** `app/static/results.html`, and in `app/static/sim/`: `results.mjs` (the DOM), `results-view.mjs` (every sentence), `results-charts.mjs` (the pairs chart and the hand-written comparison), `charts-lib.mjs` (the copy of Ghassan's drawing code), `results-format.mjs`, `results-strings.mjs` (Arabic and English) and `results.css`.
- **The nav.** «النتائج» / "Results" is the third link of `simulation.html` and `agents.html`. With five links the lab's top bar ran wider than a phone, so `style.css` now gives its nav a row of its own there, as `agents.css` does (§7.4); the browser check measures it.
- **Tests.** `app/test_results.py`; `results-format`, `results-strings`, `charts-lib`, `results-charts`, `results-view` and `results-page` under `app/static/sim/`; the two nav pins (`app/test_agents.py`, `agents-page.test.mjs`).
- **Documents.** `app/README.md` (the page table, "Opening the results tab"), `app/start-simulation.ps1` (the banner); CLAUDE.md's repository layout: edited (its app/ block lists the results modules and the page).

### Commits

- `169deed` Results tab R1a (task 1): the evaluation-file parser
- `1fe6e76` Results tab R1a (task 2): results_provenance part 1, the git helper and the live side
- `13794a4` Results tab R1a (task 2): a git status or log that fails loses git, never reads as clean
- `96c3beb` Results tab R1a (task 3): results_provenance part 2, the plant state of each file
- `0dd7c52` Results tab R1a (task 3): derived constants changed after the server started leave no same state
- `ac9f43f` Results tab R1a (task 4): results_data, the evaluation sections and build()
- `38ac3de` Results tab R1a (task 4): duplicate seeds listed, no head without git, C4's convergence note, the Arabic word for current
- `6d4a1c1` Results tab R1a (task 5): GET /results and /api/results under --simulation
- `eaf16fa` Results tab R1a (task 5): say what no-cache on /static covers and what it does not
- `04f1096` Results tab R1a (task 6): number formatting, the tab's strings, nav.results
- `0497c1e` Results tab R1a (task 6): the notes name their files and dates (spec 5.4)
- `84e1d83` Results tab R1a (task 7): the drawing library and the tab's stylesheet
- `236b3ff` Results tab R1a (task 7): the chart-failure note follows the page's direction
- `32b83eb` Results tab R1a (task 8): the pairs chart and the hand-written comparison
- `ccc4acc` Results tab R1a (task 8): every seed stays on the pairs chart; no difference no script prints
- `5416fd6` Results tab R1a (task 9): the page, its view helpers, and the nav link
- `628367d` Results tab R1a (task 9): a mixed plant names each file's facts; a language switch keeps the reader's place
- `1c16043` Results tab R1a (task 10): the tab in the README, the launcher and the layout

### What the reviews changed

Each task was reviewed before the next began; from Task 5 on, by four reviewers, one per lens, with three refuters on every serious finding. Where a finding held against the spec, the task got a fix commit, listed above with the others. The plan document keeps its code as planned; these are the places where the shipped code differs from it:

- **Task 2** (`13794a4`): a `git status` or `git log` that exits with an error now loses git for the build, so a file is never shown unchanged when git could not say (`fingerprint.py`'s rule: unknown is not clean).
- **Task 3** (`0dd7c52`): derived constants changed after the server started leave no "same" plant state, as changed plant files already did (§5.2).
- **Task 4** (in its first commit, and `38ac3de`): the build asks git's status before its log, so a failed status leaves no commit date on the page; two files naming one seed are both listed as not read (§4.1); the head commit is left out when git is unavailable (§6.3); C4 carries its "not converged" note (§5.4); the Python wording test bans the Arabic word for current (§5.5).
- **Task 5** (`eaf16fa`): the docstring of the `/static` revalidation says what it covers: every later update, but not a browser that cached the lab before this one, which needs one Ctrl+F5 (`app/README.md`).
- **Task 6** (in its first commit, and `0497c1e`): three strings for the reason and note keys above, and five notes that now name their files and dates (§5.4).
- **Task 7** (`236b3ff`): the "could not be drawn" note follows the page's direction in Arabic.
- **Task 8** (`ccc4acc`): every seed stays on the pairs chart and in its table, with a dash where a median is missing (§4.1); blind minus sighted is shown for the total damage only, since no script prints it without the knock term (§5.1).
- **Task 9** (`628367d`): when a section's files disagree on the plant, each seed carries its own facts (a changed file, its forced lines, its hashes and tag, its last commit) (§5.2); a language switch keeps the reader's place on the page and every open table; the plant line has a colon between its label and its state.

### The checks, as printed

| check | as printed |
|---|---|
| `python -m app.test_results` | Ran 119 tests in 8.960s · OK |
| `python -m app.test_agents` | Ran 126 tests in 42.906s · FAILED (failures=16, errors=3, skipped=1) |
| `python -m app.test_simulation` | Ran 15 tests in 1.101s · OK |
| `python -m app.test_replay` | 49 of 49 checks pass |
| `node --test "static/sim/*.test.mjs"` | ℹ tests 235 · ℹ pass 235 · ℹ fail 0 |
| `python verify_docs.py` | All 73 checks pass (849 figure mentions scanned in the documents). |
| `python drift_test.py` | 16 of 16 drifts CAUGHT |
| the browser check (scratchpad script) | 18 of 18 browser checks pass |

**The agents suite against its baseline.** Before R1a the suite already failed, because the merged plant refuses Jad's agents; the coordinator captured that list before any R1a change. Entries this run has and the baseline does not: none.

**The browser check.** Every check passed. Screenshots at 1440 px and in a 390 px frame, both languages and both themes, of `/results`, `/simulation` and `/agents`, are in the scratchpad, not in the repository.

### The build time of `/api/results`

`INFO  /api/results build: cold 325 ms (wall 332 ms), warm 244 ms (wall 253 ms)` (the build's own `elapsed_ms`, and the wall clock seen by the client, on the first request after the server started and on the next).

### Left for R1b and R2

- **R1b, Ghassan's set:** `analyse_agent_set.py`, its committed capture and the `posthoc:` anchors; the agent-set reader and port; the pairs chart both ways; `f-eval`, `f-abl`, `f-trade`, `f-curves`; the two new figures; the incomplete box; the two provenance lines; the record fold.
- **R2, the simulator and the car:** every figure of §3.3 and §3.4, their readers, strings and tests, and the defect fixes that belong to them.
- **Not in R1a, by its contract:** stepping a crosshair or nearest-point chart with the arrow keys (§7.3); R1a's figures are per-mark charts, whose marks take keyboard focus.

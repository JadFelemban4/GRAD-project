# Session report — 29 September 2026

Three requests: update the results page (the artifact), then commit; then
document the trained agents with every action they took, and retrain — ten
seeds, 50 000 steps, scored on the twenty frozen episodes, on the GPU if that is
faster; then, with the team's decisions (records out of git, the fuel is 95 RON,
retrain after every drive), measure the knock margin and commit everything.

Every figure below is printed by a script named beside it.

---

## 1 · The results page, and two claims of 28 September that were wrong

The page (`make_page.py` → `results/page/index.html`, published as the "B58
Preview Study" artifact) was the morning's build. Rebuilt on the evening's tree,
with the H/τ sweep (`generality_test.py` now writes `results/generality.json`),
the premise step by step, per-drive thermal error, the oil structures and drive B
against the ceiling. Every figure in its prose is a token; the sentences that
state a result without a number are computed or asserted in `make_page.py`.

Putting every sentence behind a token found two claims with no run behind them
(**mistake 22**, CLAUDE.md):

- **"The derived boost ceiling matches drive B at 1400–2400 rpm."** Against the
  highest genuine full-throttle reading in each 200 rpm band, it is **9–20 % LOW
  at 1600–2000 rpm** (193 kPa reached where the model allows 155) and −7 to +7 %
  from 2000 rpm up. Re-pairing engine speed to each boost reading's own moment
  (`compare_calibration.py`) moved the points ~55 rpm and changed nothing.
- **"About 6 K of row 8's miss is the coolant."** Measured
  (`model_vs_data.row8_split`): **4.6 K of a 12.0 K miss**; 7.3 K is the oil node.

Corrected in CLAUDE.md, REFERENCES.md, `validation_table.md` and the 28 September
report. Also fixed on the page: three typed sentences about the agents that had
gone false, a clipped chart point, phone-width label overflows. Committed as
`cbb8d09`, with the reward and full app-replay outputs in the message.

## 2 · The GPU — measured, not assumed

One training step, one thread (`train.py`'s docstring):

| part of a step | time |
|---|---|
| the plant (numpy, CPU) | 61.6 ms |
| SAC's gradient update | 11.5 ms |
| choosing the action | 0.2 ms |

The network is 16 % of the step. A GPU that made it free would make a run at most
1.19× faster, twenty runs at once would need twenty CUDA contexts on a 4 GB laptop
card, and the installed torch is a CPU build. **Training runs on the CPU.**
`train.py --device` exists for when that changes. A GPU was not benchmarked
directly: installing a CUDA build to confirm a bound of 1.19× was not worth it.

## 3 · The retrain

`python train_all.py`: seeds 0–9, sighted and blinded — **twenty runs, ten
seeds a side.** With five pairs an exact Wilcoxon signed-rank test cannot return
less than p = 0.0625, so five seeds could never show a preview effect at 5 %.
50 000 steps each (55 episodes of 900 s), a new road every episode, 130 km/h,
dt 1.0, on the derived plant. All twenty ran at once on the 20-thread laptop:
**234 min, 3.6 steps/s each**, every run finished. The "twenty episodes" are
`evaluate.py`'s frozen set, unchanged.

**What is recorded now** (`train.py`, new): `config.json` (every SAC setting,
versions, commit, the plant's data fingerprint, wall time) and
`train_record.npz` — **every training step**: the action, the observation it
was chosen from, the reward and its terms, the engine's state.

## 4 · Scored and documented

`record_agents.py` (new) runs each agent through the twenty frozen episodes,
recording every step, and writes `results/agents/<set>/<agent>/`: config, curve,
policy weights, the training record, the evaluation record (commanded AND applied
actuators, observation, engine state), a scored summary; per set a generated
README with every table, an index and five figures. **Its scores are checked
against `results/phase_d_130kmh_raw.json` episode by episode and the run stops on
any difference: 280 episodes (the 19 September set) and 480 (the new set), all
identical.**

| | median cut | over current-grade | thermal-only cut |
|---|---|---|---|
| sighted, median of 10 | 67.9 % | +24.5 | 67.0 % |
| blinded, median of 10 | 65.4 % | +22.0 | 68.5 % |
| current-grade, hand-written | 43.4 % | — | 47.2 % |

**All twenty beat every hand-written policy** (weakest: blinded seed 1, 49.0 %).

**The ablation, ten pairs: sighted minus blinded +1.2 points, 95 % CI −4.4 to
+6.8, paired t p = 0.65, exact Wilcoxon p = 0.43.** Thermal-only: −1.5 points,
p = 0.56. The pairs run from −14.3 (seed 5) to +14.6 (seed 2). At this scenario's
H/τ (0.64), what a learned policy gains comes from learning to protect, not from
seeing ahead. It is one point on the H/τ curve.

**Two things the records show that the scores alone do not:**

- **Every agent advances spark to just under the knock knee.** Median trim on
  the climb +3.5 to +4.0° over the baseline's 1.2° (the trim's bound is +4),
  knock integral p95 0.77–0.79 against the baseline's 0.61 and the damage knee's
  0.85. Section 8 measures how much of the gain this is: most of it. Both halves
  do it, so the ablation is unaffected.
- **Blinded seed 6 does more damage than the baseline ECU on 5 of 20 episodes**
  (worst 2 527 against 920, turbine 932 °C) — exactly the five with the lowest
  weight on component life (at most 0.089). The reward lets it trade life for
  fuel. No other agent does.

The ten agents of 19 September are documented the same way in
`results/agents/sep19_110kmh/`, except that their **training actions were never
recorded and cannot be recovered**; their config is read back out of the saved
model and says so.

## 5 · Also changed

- `evaluate.run_episode` takes an optional `record`; it only reads, and the
  scores are unchanged (the regression check above).
- `run_results.py` scores `runs/terrain_dt1` (`--agents=` for another set) and
  pairs any number of seeds; `make_page.py` and `make_figures.py` (figures 5–7)
  read the agents from `results/agents/`, which is committed, not `runs/`, which
  is not, and follow the data instead of hard-coding five seeds or a t of 2.776.

## 6 · The team's decisions, and the commit

- **The records stay out of git.** `results/agents/` is 98 MB on disk: 52 MB of
  `train_record.npz` (20 files), 33 MB of `eval_record.npz` (38: twenty agents
  and ten old ones, each set with its four hand-written policies), 8 MB of
  `policy.npz` (30). By the team's decision the two `*_record.npz` kinds are
  gitignored and stay on the training machine; configs, curves, summaries,
  policy weights, READMEs and figures (about 11 MB) are committed.
  `eval_summary.json` now carries the statistics the page and the READMEs read
  from the records, so both build from git alone.
- **Everything else is committed on `JMF-2340550`.**
- **Still open**: the boost ceiling at 1600–2000 rpm and drive A — each
  changes the plant, and the team retrains after every drive (~4 h) — and the
  sep17 merge.

## 7 · The fuel — settled

The team confirms the car was logged on **95 RON**, which `plant.Operating.octane`
already assumes: nothing is refitted (REFERENCES.md 2c). Removed from every
"still open" list; the page's GCC/fuel item says so.

## 8 · The knock margin, measured

`knock_margin.py` re-scores the twenty on the frozen episodes with **spark
advance forbidden**: each agent's own action, its spark trim capped at zero (the
baseline's knock-limited spark; retard still allowed). A diagnostic beside the
protocol; the twenty episodes and `evaluate.run_episode` are untouched.

| | as trained | advance forbidden |
|---|---|---|
| sighted, median cut | 67.9 % | **41.6 %** |
| blinded, median cut | 65.4 % | **41.7 %** |
| margin over current-grade (43.4 %), median of all twenty | +24.4 | **−1.8** |
| agents still beating current-grade | 20 of 20 | **9 of 20** |
| sighted minus blinded | +1.2 | −0.95 (95 % CI −13.7 to +11.8) |

**Most of what the agents gain over the hand-written policies is spark advance
the untested knock model allows.** It is a lower bound — an agent trained without
the lever could do better than one that has it taken away — but it moves drive C
(knock, `logs/DRIVE_PLAN.md`) to the top of the drive list: it decides whether
that margin is real. Full table: `results/agents/terrain_dt1/KNOCK_MARGIN.md`.

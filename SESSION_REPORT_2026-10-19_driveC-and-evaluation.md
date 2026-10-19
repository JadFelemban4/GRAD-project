# Session report — 19 October 2026: drive C's first attempt, and the proposal's evaluation

Jad, with Claude Code. Branch `JMF-2340550-driveC-check`, from `main` at
`c41c9ee`, with `JMF-2340550-proposal-eval` merged into it (`72a258b`). Not
pushed when this was written: the push waits for Jad's answer.

## 1. Drive C, first attempt: checked blind, it covers neither part

Ghassan logged six CSVs with drive C's six channels on the night of 18–19
October and asked whether they are enough. `drive_c_check.py` (new) answers
that without reading an ignition angle's value, so the draft decision rule can
still be fixed before anyone sees the retard. Its output and the verdict are
`logs/DRIVE_C_CHECK_2026-10-19.md`:

- **The logging worked:** the logger reads one channel per row in a fixed
  rotation, and each angle was read every 0.90–0.93 s (median), as the plan
  intended.
- **The driving was not drive C's:** C1 has no loaded segment of 20 s at
  2000–3500 rpm (the longest 2.7 s) and 0 readings in the climb's cell; C2 has
  one step as the plan drives it, of twenty. The boosted driving ran at a
  median 4824 rpm, in bursts of 5.5 s at most.
- **It closes no planned drive.** A and D need other channels. Drive C has to be
  driven again; recommended, the logs stay outside `logs/raw/` until the repeat,
  so that the plant is re-derived once (section 6 of the check).

## 2. Ghassan's reply: the summer heat is over

By voice message, transcribed on this machine (`faster_whisper`, large-v3, on
the CPU; nothing left the machine): the heat of the earlier logs will not come
back this season; he will drive C1 and C2. Recommended in section 8 of the
check: drive now, in the warmest hours available, with the verdict limited to
the ambient range driven and the scenario's 42 °C reported as untested; the
hot-against-cool comparison is lost, and Ghassan is asked whether the step size
can separate a knock retard from a tip-in retard instead.

## 3. The rule's numbers

Ghassan asked what "fix the rule's numbers" means. Section 9 of the check lists
the ten numbers, with the draft's value and what each decides. Seven come from
the draft of 13 October (five with a value); three are new: the fewest valid
steps that allow a verdict, the ambient range, and a half-pedal against
full-pedal split. None is fixed yet; Ghassan has been asked not to drive before
they are.

## 4. The proposal's evaluation

Dr. Hammam sent the SP1 abstract round's evaluation (two evaluators, identities
withheld, on the Innovation & Entrepreneurship track's form). Both accept; the
corrections are Evaluator 2's four points, and Evaluator 1 asks that the tests
fit the project's time. `docs/supervisor/2026-10-19_proposal-evaluation.md`
holds the scores, the comments verbatim, and for each point what the project
already has, what is missing and what to do; section 8 holds Jad's first
answers, the verdict on each, and the sentence for the evaluator on what
separates the project from Mercedes-Benz's system. The workbook stays outside
the repository.

The team has moved the project to the research track (Jad, 19 October), and
plans in Notion (the GRAD Project Dashboard: components C0–C9, gates G0–G9
from 12 October to 23 November). Notion was read, not changed.

## 5. Found on the way, not fixed

1. **Two plants in `CLAUDE.md`, one in Notion.** `CLAUDE.md`'s claim and the
   submitted abstract still test H/τ across two plants; Notion removed the
   battery (gate G0, 12 October, "C5 removal approved"). The team's call.
2. **The gap needs restating for one engine.** `DOC/Novelty_Statement.pdf` rests
   its gap on "tested across physically distinct plants". Within one engine the
   claim that the ratio governs needs points with the same H/τ from different H
   and τ; `generality_test.py` sweeps τ at one horizon (30 s).
3. **The literature review is scheduled last.** Notion's C9-03 runs 16–18
   November, after the analysis freezes (G5, 11 November); two of the
   evaluator's four points depend on it.
4. **The draft rule had no minimum number of steps** for a verdict (now C2-6 in
   section 9).
5. **`/i-have-adhd` is not installed in this environment**, though
   `team/jad.md` asks for it; its rules were followed by hand.

## 6. Not done

- The rule's ten values: not proposed, not fixed.
- The proposal: nothing changed yet; the two questions for Dr. Hammam (the
  deadline, and which track's form) not asked.
- No Notion task was created.
- `python verify_docs.py`: All 74 checks pass, after every commit of this
  session. No app suite was run: nothing under `app/` changed.

## 7. At the push: the rule had been fixed on `main` the same day

When Jad named `main`, it had moved: Ghassan's session
(`SESSION_REPORT_2026-10-19_driveC-rule.md`) proposed the rule blind, recorded
decisions 14–23 as agreed by Jad and Ghassan (`7ad649c`), and committed
`drive_c_analysis.py`. So section 3 above, and section 9 of the check, are
superseded: the numbers are fixed in `results/DRIVE_C_RULE.md`. The two
branches were merged; `CHECKPOINT.md`, `HISTORY.md` and `STATE_HISTORY.md`
conflicted, and `main`'s text was kept in each, with this session's additions
on top (the line `CHECKPOINT.md` replaced is `STATE_HISTORY.md` part N). Stage A
has not run on the 18–19 October files; they are on Jad's machine.

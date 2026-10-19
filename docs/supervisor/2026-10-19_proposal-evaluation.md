# The proposal's evaluation (SP1 abstract round): what it asks, and how we answer it

Received 19 October 2026: the workbook `18279_د.همام_محمد_الغامدي.xlsx`, sent by
Dr. Hammam (last saved by him on 17 October 2026). Two evaluators, identities
withheld, each on the form *Senior Project (SP1) — Abstract Evaluation Form —
Innovation & Entrepreneurship Track*. The workbook is not in the repository
(SHA-256 `9ff9ec55a2651f76a02befdead6baad6f22ff2848504c9aebdabf228cabb1a85`).
The abstract they scored is `ABSTRACT.md` section 1 (`DOC/Abstract_EN.docx`).

**Since then the team has moved to the research track** (Jad, 19 October). The
form above is the Innovation & Entrepreneurship track's; whether the corrections
are answered on the research track's form is the second question in section 5.

## 1. The decision

| | Evaluator 1 | Evaluator 2 |
|---|---|---|
| total, out of 20 | 15.36 | 12 |
| decision | Accepted, with no correction required | Accepted, with minor corrections |

Both accept. The corrections asked for are Evaluator 2's four points (section
3); Evaluator 1 adds one comment, on feasibility.

## 2. The scores

Each criterion is scored out of 5; the total is the weighted mean scaled to 20.
The level text is the rubric's fixed wording for the level given, not a written
comment, but it says what kept the score from the level above.

| criterion | weight | E1 | E2 | what the level text says is missing |
|---|---|---|---|---|
| A. Problem clarity | 17 % | 4 | 3 | E1: "relies mostly on assumption rather than concrete evidence". E2: "lacks depth in explaining who experiences it or why it matters" |
| B. Target user definition | 17 % | 4 | 3 | E1: "without a concrete supporting example". E2: "superficial or generic" |
| C. Problem–solution fit | 17 % | 4 | 3 | E1: "minor gaps or unstated assumptions". E2: "the connection is not fully convincing" |
| D. Feasibility & scope | 17 % | 4 | 3 | E1: limitations in skills, tools or data access "acknowledged but not deeply mitigated". E2: "scope, required skills, or data/API access are not fully addressed" |
| E. Innovation & originality | 16 % | 4 | 3 | E1: "even if not fully unique". E2: "largely builds on existing/common approaches without clearly naming what distinguishes it" |
| F. Expected impact | 16 % | 3 | 3 | both: "An impact is claimed, but described in general terms without depth." |

**Impact is the weakest criterion: the only one both evaluators scored 3.**

## 3. The comments, verbatim

**Evaluator 1:**

> التأكد من إمكانية إنجاز الاختبارات المقترحة ضمن المدة المحددة لمشروع التخرج.

(Make sure the proposed tests can be completed within the graduation
project's set period.)

**Evaluator 2:**

> The proposed idea is promising and has clear value, but it needs further
> development before it can be approved. Specifically:
>
> 1- Expand the literature survey: Conduct a broader review of previous studies
> and related projects to establish the problem and its scope, and to identify
> the gap the idea addresses.
> 2-Compare with existing solutions: Present a clear comparison between current
> solutions and the proposed one, highlighting what makes it distinctive and the
> real value it adds (in terms of efficiency, cost, usability, etc.).
> 3-Clarify the implementation phases: Provide a phased implementation plan
> outlining the work steps, expected deliverables for each phase, and a proposed
> timeline.
> 4-Link the idea to the group’s specialization: Explain how the project relates
> to the team members’ field of study and how their specialized knowledge and
> skills will be applied in carrying it out.
>
> We recommend addressing these points to strengthen the idea’s clarity and
> feasibility

## 4. How we answer each: what we have, what is missing, what to do

### 4.1 The tests within the project's time (Evaluator 1; criterion D for both)

- **We have** Notion's milestone gates G0 to G9, 12 October to 23 November,
  each with a lead, a definition of done and a fallback ("If not accepted").
  The battery plant is already out of scope (Notion component C5), and drive A
  is conditional.
- **Missing:** the proposal does not show any of it. And one test is at risk
  now: drive C's first attempt, 19 October, did not cover the plan and has to
  be driven again before G3 on 2 November (`logs/DRIVE_C_CHECK_2026-10-19.md`).
- **Do:** a table in the proposal, one row per test (drive C, the final
  training, the H/τ test, the analysis): how long it takes, its gate's date,
  and what happens if it slips, from the gates' "If not accepted" column. Name
  the smallest result the project still reports if a test slips: an
  inconclusive verdict under the preregistration (G5), or the engine-only
  claim (G6).

### 4.2 The literature survey and the gap (Evaluator 2, point 1; criterion A)

- **We have** two starting points. `DOC/Novelty_Statement.pdf` section 2 ranks
  the prior work by how close it comes: H∞ preview-control regret bounds, MPC
  horizon selection, Mercedes-Benz Predictive Powertrain Control, RL for engine
  control (ORNL, NREL, a 2026 survey), and predictive energy management.
  `docs/supervisor/2026-10-06_why-rl-not-supervised.md` summarises seven
  references, the closest to us being Hu et al. (2019), DDPG on a
  variable-geometry turbocharger, in simulation.
- **Missing:** the survey itself. Notion schedules "Write related work and
  literature review" (C9-03) for 16–18 November, after the analysis is frozen
  (G5, 11 November). And the seven references were read by AI agents, not yet
  by the team, as that file says (6 October).
- **Do:** bring C9-03 forward to now. Four strands: preview and look-ahead
  control; predictive powertrain and thermal management; the reactive
  protection a car does today (knock control, enrichment to protect
  components); RL for engine and turbocharger control. Each paper read by a
  team member before it is cited. End with the gap, as 4.3 restates it.

### 4.3 The comparison with existing solutions (Evaluator 2, point 2; criterion E)

- **We have** the novelty statement's table, which gives for each prior
  approach why it does not answer our question; and experiments that compare
  against named baselines: the production-style ECU, a reactive policy, the
  current-grade rule, and an agent trained blind.
- **Missing:** a comparison a reader can scan in the proposal itself. And the
  novelty statement cannot be used as it stands: its figures are void
  (`DOCUMENT_STATUS.md`), and its gap rests on the clause "tested across
  physically distinct plants", which the team removed with the battery (Notion
  C5; gate G6, "engine-only claim").
- **Do:** one table. Rows: reactive ECU protection, map-based predictive control
  (Predictive Powertrain Control), MPC with a horizon rule of thumb, preview
  control theory, RL engine control, this project. Columns: the question it
  answers; whether it needs preview; whether it says, before anything is built,
  if preview pays; whether it was checked against a real car. Then restate the
  gap for one engine: that the ratio H/τ governs the value of preview, not τ
  alone, which needs points with the same H/τ reached through different H and
  τ. `generality_test.py` sweeps τ (the turbine's heat capacity) at one horizon,
  30 s, so it cannot separate the two; a second horizon is what that test lacks.
  Give the value in the evaluator's terms (cost, efficiency, usability) as what
  the project will measure, not as a result.

### 4.4 The phased plan (Evaluator 2, point 3)

- **We have** it: Notion's gates G0–G9 with dates, leads, deliverables,
  definitions of done and fallbacks, and a phase (PH1–PH3) on every task.
- **Missing:** it is not in the proposal.
- **Do:** one table or Gantt chart from the gates (phase, gate, deliverable,
  date, lead), marking what is done.

### 4.5 The link to the team's specialization (Evaluator 2, point 4)

- **We have** a project in the department's AI senior projects ("AI SP" on the
  form) whose work is AI and computing: a reinforcement-learning agent (Soft
  Actor-Critic) designed and trained, a simulator calibrated on logged car data,
  an experiment design with a preregistration and paired seeds, and a real-time
  read-only application.
- **Missing:** who applies what.
- **Do:** a table, one row per member: the role (Notion's leads) and the AI or
  computing knowledge it applies. Say plainly that the engine is the testbed,
  and that the question, when information about the future is worth acquiring
  for a learning controller, is an AI question.

### 4.6 The rubric's other points (no correction asked, but they set the scores)

- **Impact (F):** name it concretely and say how it will be measured. For an
  engineer, a go or no-go on buying preview, read from two numbers, H and τ,
  before building it. For research, a measurement protocol (preregistered,
  paired), an open calibrated simulator and its data, and the H/τ curve for one
  engine with its uncertainty.
- **Problem and user (A, B):** one concrete user and one concrete case, for
  example a powertrain engineer deciding whether turbine protection should use
  map-based road preview. Commercial preview products show that preview is
  bought; what is missing is a way to know beforehand whether it pays.
- **Fit (C):** state the assumptions the abstract leaves unstated: that a road
  preview of horizon H is available, that the protected part's time constant τ
  can be estimated, and that the damage model and the simulator are a reference
  validated over a stated region (`validation_table.md`).

## 5. Open questions for Dr. Hammam

1. The deadline for the corrections, and their form: a revised abstract or a
   separate response.
2. Since the team has moved to the research track: should the corrected
   proposal answer the research track's form, and is there one?

## 6. Found on the way, not fixed

- `CLAUDE.md`'s claim ("regardless of which plant produced the point. If the two
  plants do not overlap...") and the submitted abstract ("A battery plant tests
  transfer") still describe two plants, while Notion removed the battery (gate
  G0, 12 October: "C5 removal approved"). A change to `CLAUDE.md` is the team's
  call; the corrected proposal should not repeat the two-plant claim.

## 7. Not done

- Nothing in the proposal has been changed yet.
- No reference was read for this file: the strands in 4.2 are a plan, not a
  survey.

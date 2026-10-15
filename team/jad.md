---
name: Jad Felemban
student_number: 2340550
email: endo.felemban@gmail.com
updated: 2026-10-15
---

# Jad

**Graduation supervisor:** د. همام محمد الغامدي (Dr. Hammam Mohammed Al-Ghamdi).
Recorded 1 October 2026 at Jad's request, in every file in `team/`.

## What I am responsible for

The repository and the GitHub account it lives on (`JadFelemban4`).

**The Supra is a teammate's car, not mine.** I drive a GAC Emzoom 2024, the trim
below Sport. Corrected here on 18 September — this file said the logged car was
mine, which I never said; it was assumed. Ask rather than assume who owns what,
because it decides who can schedule a drive.

## What to assume I know — and what not to

| area | where I am |
|---|---|
| engines, combustion, turbocharging | **beginner.** Started near zero in September and worked up through a long teaching session |
| control theory | the ideas, not the mathematics |
| reinforcement learning | the shape of it — agent, reward, baseline. Not the algorithm |
| Python, git, the command line | I can run what I am given and read output |
| statistics, uncertainty, error bars | not covered as mathematics. **One idea landed on 26 September:** a paired test that counts votes (C4's sign test) rather than averaging |
| academic writing | not covered |

**Specifically do NOT assume I know:** the parts of an engine, just because I
followed a control argument. Those are separate, and I said so directly. A
correct answer from me to a yes/no question is **not** proof I have it — I often
need a fresh example to connect the pieces.

## How to explain things to me

**Use the `/i-have-adhd` skill. This is a standing preference, not a one-off.**
Added 19 September 2026. If you are an AI assistant with that skill available,
invoke it at the start and keep it on — it stays active until "stop adhd mode".
Everything in this section is what that skill enforces anyway; the skill just
makes it automatic instead of depending on you remembering.

    https://github.com/ayghri/i-have-adhd

**Version matters, and here is why.** Rule 9 changed on 10 September 2026
(v0.2.0 → v0.3.0). The old wording let the assistant DROP list items past five.
The new one is explicit that the cap is **presentation only** — keep everything,
show five at a time, never omit a relevant item when completeness matters.

**On this project the old wording was a hazard.** The whole culture here is
"state every limitation, report against yourself" (see the tone note at the
bottom of CLAUDE.md). A rule that silently discards the sixth item is how a
caveat goes missing, which is mistake 11's shape. **If the installed copy still
says "Five items ranked beats ten unranked", it is the old one — update it.**

- **One small idea per message**, then one question to check I followed. Not a
  lecture with a quiz at the end.
- **Even when I send several points at once, answer ONE.** On 26 September
  2026 I listed five points about a session I had missed and got back five
  sections, each with its own example and a quiz at the end. I understood none
  of it and said so. Take the point that matters most, give one example, ask
  one question — and say that the other points come next, one at a time.
- **Familiar example first, then the project.** If I do not get it, **change the
  example — do not repeat the definition.** Repeating has never worked.
- **Arabic first.** Mixing Arabic, English and arrows in one line breaks the
  formatting for me; I have said so twice. Put the English term on its own line
  when I need it.
- **Say where we are.** Do not open five terms at once.
- Let me explain it back **in my own words**. Several of my answers have been
  right in substance and needed only a small correction. Do not ask me to recite
  a definition.
- If a car term is load-bearing for a decision, define it in one clause the
  first time — "manifold pressure, how hard air is being pushed into the
  engine". Do not append a glossary to every message.

## What I have already worked through

As of 18 September 2026: knock (self-ignition of part of the mixture before the
flame reaches it — **not** two mixtures colliding, which is where I started);
model exploitation; preview control, H, τ and the H/τ ratio; the three tiers;
why the second plant is a battery; reactive vs predictive; the four protection
levers and that each one costs something; objective vs constraint; reward and
baseline; the neutral action; the turbo layout — **the shaft carries rotation
only**, no gas crosses it; the piston, roughly.

26 September 2026: **what C4 found, and why it is not yet a verdict on
preview** — explained back in my own words. Seven of eight seed pairs showed no
worthwhile benefit from preview, but the agents had not finished learning, so
undertraining is still a live explanation; if they finish learning and preview
still makes no difference, the preview itself becomes the likely cause — on
this road, one climb per ride (that last part was the correction I needed). It
landed through one example — eight pairs of pots of kabsa, one pot in each pair
with a new spice, tasted before the meat is cooked — after a five-part
explanation of the same session had not.

Same day, the preregistration, through the same kabsa frame: the rule of the
judgement is written before the tasting. Asked what to say to a teammate who
wants to change the rule after seeing the result, I answered that it is "a
crime and a violation of our constitution" — **the preregistration is our
constitution.** The one legitimate change: a new plan for a new experiment,
written before it starts, with both results reported.

Same day, the supervision claim: the agent beats the hand-written rule on the
typical ride, not on the worst one. Two cooks, one of whom burns the dish at a
wedding, did NOT land; two students did — one usually scores 90 but once scored
40, the other usually 80 and never below 70. Asked which is better, I chose the
steady one "because our project is very sensitive" — the right instinct for
protection. The correction I needed: the damage the project measures is heat
damage to the turbo, not fire, and the agent runs only in the simulation.

Same day, the pairing, after I asked "16 agents and 8 seeds?": sixteen agents
are eight pairs, one sighted and one blind in each and identical otherwise; the
seed is the pair's number, like one batch of meat per pair of pots. I knew why
a PAIR is needed. Why EIGHT pairs needed a correction, and seed 0 in C4's own
table was the example that did it: run alone, it would have said preview saves
361 damage units, while the other seven said no. **Say "eight pairs" rather
than "sixteen agents" or "eight seeds" when talking to me.**

28 September, after seeing all three experiments listed on the agent page and
saying I was confused: **the difference between Phase D, D2 and C4**, through a
speed bump on the road to the university and two drivers, one with eyes open and
one with eyes closed. Phase D: the bump is in the same place every day, so the
closed-eyes driver can memorise it (the "blind" arm was not really blind), short
training. D2: the bump moves and changes height every day, so it cannot be
memorised, same short training. C4: D2 with six times the training. Asked why
the team re-ran Phase D with a moving bump, I answered "so the agent does not
memorise" — right; the small addition I needed: it is the BLIND agent that must
not memorise, so that seeing the road is the only difference left between the
two.

7 October, after Ghassan sent his draft validation plan (`results/VALIDATION_PLAN.md`,
not yet pushed): **how the simulator is judged against the car**, through a
kitchen scale and a bag of rice marked 1 kg — a frame I brought myself. The
scale is the simulator, the bag is the car's reading. In my own words: write
how much difference you accept BEFORE weighing, chosen by what the scale is
for (kabsa or gold); compute the difference and how wrong the bag itself may
be; the verdict then comes from the numbers, not from opinion — which is what
the supervisor asked Ghassan for. The addition I needed: there is a third
verdict, "cannot tell", and what decides it is the bag's own error, not how
much the use matters. I gave the right verdict on a fresh case (gold, bag
±10 g, scale 1.03: not good) with the use as my reason, and needed that
correction; then answered a second one right with no help (kabsa, 100 g
accepted, bag ±50 g, scale 1.08: cannot tell). **The rule in three lines:**
the worst case inside the limit is good; the best case outside it is not good;
the limit between the best and the worst case is cannot tell.

Same day, the rest of Ghassan's plan in five parts, one per message, each
through a new everyday example. What landed:

- **The margin rule:** arriving at the airport 33 minutes early with a watch
  that may be 10 minutes wrong. I answered the follow-up right: with only a
  10-degree margin, accepting 10 degrees of error is not enough.
- **The computer's own step error:** a car wheel that looks to spin backwards
  on a phone video. The test is more frames until the video stops changing; I
  understood it but could not invent that test myself.
- **Errors in what we feed the model:** Google Maps given a wrong starting
  point.
- **"Not covered":** a car's AC tried for five minutes, then a ten-hour summer
  drive to Riyadh; then water that is fine at 95 °C and boils at 100. I first
  said five degrees outside the tested range is acceptable. That is an
  opinion, which is what the rule removes.
- **"Untested" against "cannot tell":** corrected twice. Untested is not worse
  than "not good", and we did test, with a bag too coarse to see.
- **Relative damage:** a bathroom scale that adds 10 % to everyone. Answered
  right.
- **Spark timing, first idea only:** charcoal lit late is thrown into the bin
  while at its hottest, so late spark heats the turbo. Understood, not checked
  back.

What did NOT land:

- Three error sources in one message ("ما فهمت").
- Asking whether an error "lives in the car or in our computer". The logger is
  a phone app, so it IS a computer of ours, and both of my wrong answers came
  from the question. The bag-and-scale frame fixed it.

**Ten check questions in one sitting was too many.** By the end I understood
but had nothing left to answer with. Ask fewer, keep the ones that matter, and
when I say I am at my limit, stop asking.

**Not covered yet:** the thermal detail of the turbo (exhaust-gas temperature
against housing-metal temperature); how thermal damage is computed; reward
hacking; the learning algorithm; uncertainty models; spark timing beyond the
first idea (late spark heats the turbo, 7 October), BTDC/ATDC;
the battery specifics.

## Corrections I have needed more than once

- Explanations aimed at me have overclaimed, in phrases like *"the simulation is
  the truth"*, *"the idea is proven by week 18"*, *"the ratio guarantees the
  benefit"*. The accurate forms: a simulation **reference**; a **date for an
  experimental result**; a **hypothesis being tested**. Do not sell me a result
  that does not exist yet — I will repeat it to a supervisor.
- I have twice been handed the project's own **void** figures as if current. See
  below.

## Anything else

**Reading every file of the project takes about 25 % of the usage** on the
Claude Max plan ($100) with Opus 5.5. Measured by Jad on 1 October 2026: one
session read all 465 tracked files once, with three helper agents reading the
app, the results and the older documents. A full read is a real cost, so it is
worth doing on purpose, not by default.

<!-- RETIRED-OK: 548.6, 168.1, 8 -- naming the void figure IS the warning -->
**My interview prep sheet is out of date and I nearly presented from it.** It
calls `548.6 = 548.6` the project's strongest fairness evidence. The
15 September audit proved that identity is guaranteed by construction and is
not evidence at all (`AUDIT.md` C3). It also quotes 168.1 minutes over eight
drives; the figure is **321.7 minutes over eleven drives** on 30 September, and
it grows with every drive, so take it from `python build_dataset.py`, not from
here. That sheet reviews a presentation in
`Documents\engine-supervisor\presentation`, a **different directory** from this
repository.

My own learning notes are in `LEARNING-CHAT-HANDOFF.md`, outside this repo.

## Open item: the results tab after the merge of 14 October 2026

Recorded at my request, 14 October: I decided to fix it later.

**The problem.** After Ghassan's `GRA-2340394` was merged (merge commit
`cc5468f`, the conflicts in `conflict_2026-10-14.md`), the results tab can no
longer tell which plant made the Phase D, D2 and C4 result files. Ghassan's
branch moved the plant fingerprint to schema 2 on 8 October (`conflict.md`
decision 2, which Ghassan and I agreed): `derived_sha` became fatal and
`derived.py` became a plant file. The results tab was written for schema 1 on
5 and 6 October:

- `app/results_provenance.py`, `plant_at`, hashes today's `FP.PLANT_FILES` at an
  old commit. `derived.py` does not exist at `sep17-before-merge`, so it
  returns None and the tab cannot name the plant.
- `app/test_results.py` checks that every result file carries every fatal
  field. The old files were written under schema 1, without `derived_sha`.
- `app/test_agents.py` expects a plant mismatch on `plant_sha` alone. Under
  schema 2 the same agents mismatch on `plant_sha, derived_sha, scenario`.

Measured on `cc5468f`: `test_results` 55 failing (1 before the merge),
`test_agents` 22 failing (21 before). Every other app suite is as it was before
the merge, and node passes 305 of 305. The conflict resolutions did not cause
this: any merge of the two branches gives the same result.

**The fix, later (about 1 to 2 hours).** Make the results tab read each result
file's schema and use THAT schema's plant files and hashing rule when it names
the plant: schema 1 is `plant.py`, `thermal.py` and `engine_env.py`; schema 2
adds `derived.py` and makes `derived_sha` fatal. Then update the tests, so that
a schema-1 file is recognised as schema 1 instead of rejected for lacking
`derived_sha`. Ghassan's schema 2 stays as it is.

**Fixed 15 October 2026**, on the branch `JMF-2340550-results-schema2`
(`ca2cd73`, `2fd9aed`, not pushed yet). The tab reads each result file by its
own schema. Schema 1's rule, copied from `fingerprint.py` at `a7ce729`, gives
back the hash all 24 files record, `b5a3069f32a83754`, which is the plant of
`sep17-before-merge`. For Phase D, D2 and C4 the tab now says: made on another
plant, the plant of `sep17-before-merge`; and a line beside the two hashes
names the schema whose rule made them. `python -m app.test_results`: 123 of 124
(the one left needs `pwsh`, as before the merge). `app.test_agents` still has 22
failing, and that is a separate problem, the agents page's (session report of
15 October): only the "plant_sha alone" line came with the merge.

**A second, smaller item from the same merge.** `verify_docs.py` fails 1 of its
73 checks: two dated documents still quote the premise figures from before
Ghassan's plant fixes moved them. `PROMPT_AUDIT_2026-09-30.md` line 167 says
-0.3 for preview over current-grade (the data now gives -0.0), and
`VALIDATION_PLAN_REVIEW.md` line 69 says 920.1 for the baseline damage (now
848.1). Both were right on the day they were written. The fix: mark each as a
dated figure with a `RETIRED-OK` note, or update the sentence. Do not change
the data. **Fixed the same day**, before the documentation restructure: each
line now sits under a `RETIRED-OK` marker naming its dated figure, and
`verify_docs.py` passes 73 of 73 (933 figure mentions).

**A third item from the same merge: the learning lab's pins.**
`Explanatory Simulation/tests/test_catalog.py` still pins the merged plant of
30 September: its premise figures and its `plant_sha` (`c236a8db3e201090`).
The plant fixes of 8 October moved both (`plant_sha` is now `3c48890dd15bc116`
on Python 3.12). Measured on 14 October: `python -m unittest tests.test_catalog`,
run inside the lab's folder, fails one of its ten tests, on the preview figure.
The fix, later: move the pins to the live plant, with a comment naming the
plant they belong to (plan v3, section 12.3, step 4).

---
name: Jad Felemban
email: endo.felemban@gmail.com
updated: 2026-09-26
---

# Jad

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

**Not covered yet:** the thermal detail of the turbo (exhaust-gas temperature
against housing-metal temperature); how thermal damage is computed; reward
hacking; the learning algorithm; uncertainty models; spark timing, BTDC/ATDC;
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

<!-- RETIRED-OK: 548.6, 168.1, 8 -- naming the void figure IS the warning -->
**My interview prep sheet is out of date and I nearly presented from it.** It
calls `548.6 = 548.6` the project's strongest fairness evidence. The
15 September audit proved that identity is guaranteed by construction and is
not evidence at all (`AUDIT.md` C3). It also quotes 168.1 minutes over eight
drives; the figure is **175.5 over nine**. That sheet reviews a presentation in
`Documents\engine-supervisor\presentation`, a **different directory** from this
repository.

My own learning notes are in `LEARNING-CHAT-HANDOFF.md`, outside this repo.

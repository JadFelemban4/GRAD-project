---
name: Ghassan Alrefaei
email: <set this to your `git config user.email`>
updated: 2026-09-19
---

# Ghassan

> **STUB — written by someone else, so most of it is missing.** Only the lines
> below are things the team actually stated; every empty section is yours to
> fill. Nobody should guess your background for you, and a profile that guesses
> is worse than none, because it steers every explanation you get.
>
> To finish it: set `email:` above to whatever `git config user.email` prints on
> your machine, then work through `team/_TEMPLATE.md` and replace this file.

Student number **2340394**. GitHub **`badcloor`**.

## What to assume I know

**Engines: yes.** Stated by the team on 19 September 2026 — Ghassan is the one to
take an engine question to. Do not explain knock, spark timing, boost or
air–fuel ratio from first principles.

**This project: yes.** Do not open with an H/τ primer, a tour of the phases, or
an explanation of the cycle model.

Everything else — control theory, reinforcement learning, Python and git,
statistics, academic writing — **unrecorded**. Ask rather than assume.

## How to explain things to me

*Unrecorded.* `DOC/SESSION_REPORT_2026-09-18.md` was written on the
assumption that a dense technical brief with tables suits you, because that is
what an engine-literate reader who knows the project can use. If that is wrong,
say so there and it changes.

## What I am responsible for

*Unrecorded.*

## Open questions addressed to me

From the 18–19 September session, all four in
`DOC/SESSION_REPORT_2026-09-18.md` §17:

1. The gear rule uses a flat torque ceiling on an rpm-dependent quantity. What
   is the right shape, and is a 25 % torque reserve sensible for this box?
2. ~~`12 % @ 90 km/h` runs hotter than `4 % @ 150 km/h` on less road power.~~
   **ANSWERED BY GHASSAN, 19 September.** He read it as *less load, more air*,
   which was right and sharper than the rpm explanation in the draft. Measuring
   it settled it: the two cases carry the SAME exhaust flow to within a few
   percent (MAP x rpm = 304 769 against 303 892), so flow is not the
   differentiator at all -- the whole 44.6 K gap is EGT, 956 C against 892,
   because 151 kPa of manifold pressure burns more fuel per cycle than 109.
   And it is the same mechanism that killed SAE J2807: high load per cycle at
   low engine speed. Written up in the report's section 6.2.
3. The 115–125 km/h band is still over-asked, deliberately not tuned away.
4. Should the twenty evaluation episodes vary ambient and grade, or weights only?

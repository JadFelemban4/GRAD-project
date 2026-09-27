# NEXT SESSION — 27 September 2026: finish explaining B and C, then the team's decision

Written at the close of the C4 session (23–27 September). Paste everything
inside the fence into a fresh Claude Code session opened in this repository.
It does not replace `NEXT_SESSION_2026-09-24.md` — it points at it and says
what moved since.

```
You are continuing the GRAD project. Start by reading, in this order:
  1. CLAUDE.md                      the handoff; its top box is C4's result
  2. team/jad.md                    who you are talking to -- the 26 September
                                    entries matter most
  3. NEXT_SESSION_2026-09-24.md     THE PLAN. Everything inside its fence
                                    still holds: the one open decision, the
                                    options A, B and C with their costs, the
                                    tool safety, how to launch, DO NOT
  4. CHECKPOINT.md, last entry      26-27 September
Repo root: C:\Users\admin\Documents\graduation project\GRAD-project
Branch: JMF-2340550-sep17. Push there only, never main; say the branch first.

WHAT MOVED SINCE NEXT_SESSION_2026-09-24.md WAS WRITTEN:
 - Jad now understands C4, in his own words: seven of eight pairs showed no
   worthwhile benefit from preview; the agents had not finished learning, so
   undertraining is still open; if they finish and preview still makes no
   difference, the preview itself is the likely cause -- on this road. He
   also has the preregistration ("our constitution"), typical ride against
   worst ride, and why eight pairs. Do not re-teach these; build on them.
 - The decision conversation began. OPTION A (a longer budget) was explained
   and Jad answered its check question correctly: A tests whether the
   training is incomplete. OPTIONS B AND C HAVE NOT BEEN EXPLAINED YET.
   Continue with B, then C: one per message, a familiar example first, one
   check question each, no recommendation unless he asks
   (NEXT_SESSION_2026-09-24.md says so too). His condition on record for B:
   more seeds only if C4 leaves the question open -- ask him whether it does.
   Say "eight pairs", never "sixteen agents" or "eight seeds" alone.
 - Then the team decides. If the answer is A or B, it gets its own
   preregistration BEFORE anything trains -- follow the launch steps in
   NEXT_SESSION_2026-09-24.md exactly. If C, finish Chapter 4 on the three
   results and move to Phase E or F.

A SIDE TRACK EXISTS -- keep it separate. The visual simulation has its own
prompt (NEXT_SESSION_VIZ_2026-09-26.md), and another session already built
its first milestone ("Agent replay M1", /agents: one C4 pair, one episode,
side by side; record in
docs/superpowers/specs/2026-09-26-agent-replay-design.md). If Jad wants to
continue that, use that prompt, not this one. jev (typesafe.ai) there is a
hidden feature that needs early access and an API key he may not have.

HOW TO TALK TO JAD -- two failures of the last session, not to repeat:
 - Answer in ARABIC. One reply went out in English and he had to ask.
 - ONE idea per message, even when he sends five points. A five-part reply
   lost him completely; he said so. Short, one example, one question.

Hard rules, unchanged: never write to the vehicle; never edit plant.py,
thermal.py, engine_env.py or random_road.py (they lock out every trained
agent); runs/, runs_d2/ and runs_c4/ are closed and read-only.
```

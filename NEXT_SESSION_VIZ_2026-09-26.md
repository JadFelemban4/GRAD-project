# NEXT SESSION — the visual simulation: agents, grade, and jev as a hidden feature

Written on 26 September 2026, at Jad's request, by the session that ran C4.
Paste everything inside the fence into a fresh Claude Code session opened in
this repository.

This is a side project while the team decides the next experiment (options A,
B and C in `NEXT_SESSION_2026-09-24.md`). It is not on the thesis's critical
path; CLAUDE.md's rule about `app/` applies — time spent past "it works" is
time taken from the claim.

```
You are continuing work on the REPLAY LAB -- the Three.js visual simulation at
/simulation in app/. It was built on 21 September:
  design  docs/superpowers/specs/2026-09-21-replay-lab-design.md
  plan    docs/superpowers/plans/2026-09-21-replay-lab.md
  scene   docs/superpowers/plans/scene-task-report.md
  run     app/README.md and app/start-simulation.ps1
It replays the recorded Supra drives (logs/raw/*.csv) through ReplayReader and
Estimator, on an ILLUSTRATIVE looping road. Read those four before anything.
Repo root: C:\Users\admin\Documents\graduation project\GRAD-project
Branch: JMF-2340550-sep17.

It is a side project while the team decides the next experiment
(NEXT_SESSION_2026-09-24.md). Keep it small.

WHO YOU ARE TALKING TO. Jad (git config user.email -> team/jad.md). Read that
profile before your first message and follow it: Arabic, one small idea per
message, one question, a familiar example first, no English or arrows mixed
into Arabic lines, the /i-have-adhd skill on. Even when he sends several points
at once, answer one. He is new to RL internals and statistics; team/jad.md
(26 September) records what he now understands about C4.

WHAT JAD ASKED FOR (his words, 26 September, translated):
 1. Add the agents' experiments to the simulation -- the current ones and the
    future ones.
 2. Add the road grade.
 3. Make the map adapt to the grade that actually exists in the experiments.
 4. Add jev as an external add-on -- "honestly, I just want to try the
    model" -- and make it a HIDDEN feature, switched on by a secret gesture
    ("press ten times on some spot, or whatever the gesture is").
 5. On the timeline: "stop here, and see what the agents decided here and
    what jev decided".
 6. "I press this option, and the agents play the plays they were trained on,
    and jev does the same thing."

THE TIMELINE (items 5 and 6). For an agent episode, pausing at any moment shows
what each agent decided there: its five actions, named from engine_env.py and
labelled in Arabic, taken from the trace (the action actually applied at that
step), plus -- for the sighted agent -- the road ahead it saw in its
observation. Once jev is unlocked, a third column shows jev's decision for the
same observation, and a mode lets jev drive the same episode as a third car.
Ask Jad which of the two he wants first; they cost very different amounts
(below).

JEV -- what it is, from the vendor's own page, fetched 26 September 2026:
https://typesafe.ai/blog/introducing-system-one-models-and-jev
 - A hosted model from typesafe.ai: structured state in, TYPED decisions out,
   with calibrated probabilities. Early access, from a waitlist. Console
   https://console.typesafe.ai/ and docs https://docs.typesafe.ai/. The page
   claims 70-500 ms per call, at most 255 choices, text and structured input
   only (no images), input at $0.042 per million tokens and output free. It
   does NOT state whether numeric outputs exist, nor the SDK or endpoints.
   Read docs.typesafe.ai before designing, and treat every figure here as the
   vendor's claim, not a measurement.
 - FIRST QUESTION TO JAD: does he have early access and an API key? Without
   one, the unlocked panel says so plainly and nothing else changes.
 - The key lives in an environment variable or an untracked local file, is
   read by the Python server only, never reaches the browser and is never
   committed. Put the file in .gitignore BEFORE creating it.
 - Send jev only SIMULATED episode state -- never logs/raw or anything derived
   from the recordings, which are data from a teammate's car (team/jad.md:
   the Supra is not Jad's). The page says the service runs in the USA. A call
   happens only on an explicit user action.
 - jev's decision must be expressed in the environment's own action space
   (five actions, Box(-1, 1)). Two traps: actions 3 and 4 are ABSOLUTE duties
   whose "do nothing" is engine_env.neutral_action(), not zero (CLAUDE.md,
   mistake 10); and if jev returns choices rather than numbers, the
   discretisation is a design decision -- state it on screen.
 - When jev drives, it runs in the SAME simulation as the agents: the same
   frozen episode, seed and weights, stepped through the same tracing runner.
   Agree with Jad what jev sees; the sighted agent's observation, preview
   included, is the natural choice. At 70-500 ms per call, a 720-step episode
   is minutes of calls: measure it, show progress, cache in memory. One paused
   moment is one call.
 - jev is NOT part of the thesis experiment. Nothing it does goes into
   results/, no statistic compares it with the agents, and the unlocked panel
   says so -- with the vendor's name, where it runs, and that it is external.
   Like everything else here, it never writes to the vehicle.
 - The gesture hides the panel. Once open, the panel hides nothing about what
   it is.

START WITH DESIGN, NOT CODE. Brainstorm with Jad one question at a time, write
the approved design to docs/superpowers/specs/, then a plan, then build. Make
the first milestone small and visible -- for example ONE pair from C4 (the
sighted and the blind agent of one seed) driving ONE frozen test episode side
by side, on a road built from that episode's own grade. Discovery of every
experiment comes after that works, and jev after the agents work.

HARD RULES -- each exists because breaking it destroys something:
 - Never write to the vehicle. Read-only, as the whole project.
 - Do NOT edit plant.py, thermal.py, engine_env.py or random_road.py: their
   code is hashed into plant_sha and road_sha, and a change locks out EVERY
   trained agent of Phase D, D2 and C4. Do not edit fingerprint.py, train.py,
   evaluate.py or run_phase_d.py either: they certified closed experiments.
   Import from them; never change them.
 - runs/, runs_d2/ and runs_c4/ are CLOSED experiments and the only local
   copies of those agents (the backups are outside the repo). Read final.zip
   and meta.json only. Never write, move, resume, train or evaluate into them.
   Nothing in this work trains an agent.
 - Refuse any agent whose fingerprint does not match the live plant, as
   evaluate.py does (check_model_fingerprint). Show it as incompatible in the
   UI rather than running it.
 - The app never writes raw CAR data to disk (app/test_replay.py asserts it).
   Simulated agent traces are not car data, but keep the replay lab's policy
   unless Jad agrees otherwise: build in memory, bounded cache, one worker,
   progress shown.
 - Honesty in the picture:
   * An agent episode is a SIMULATION of a synthetic stress scenario -- a
     12-16 % climb at 130 km/h in 42 C, deliberately harsher than any recorded
     drive (CLAUDE.md, the Taif paragraph). Label it simulated, never recorded.
   * One episode of one pair is an illustration, not a result. Showing each
     car's own damage along the episode is fine -- that is what the picture is
     for. Do not aggregate episodes into any new statistic and do not label a
     pair "preview helps". Wherever agents are shown, show the experiment's
     PREREGISTERED verdict beside them, read from results/ (C4: SMALLER THAN
     THE MEI, one seed wide, the two tests disagreeing, NOT-CONVERGED; Phase D
     and D2: INCONCLUSIVE). C4's seed 0 is exactly the pair that would mislead
     a viewer on its own.
   * The agents trained at dt 0.2 and were scored at dt 1.0 (CLAUDE.md, "THE
     AGENT IS SCORED IN A DISCRETISATION IT DID NOT LEARN IN"). Replay at the
     scoring protocol, so the picture matches the scores, and say so.
   * Recorded drives have no grade channel: keep their road illustrative, as
     the original design says. Only agent episodes get a road built from a
     real grade, because there the grade is the scenario's own input.
   * Road geometry is drawn FROM the scenario and never fed back into it.

HOW AN AGENT EPISODE IS DEFINED -- reuse it, do not reinvent it:
 - evaluate.py: DT = 1.0 and DURATION = 720.0; EPISODES (Phase D's fixed
   climb, engine_env.make_grade_climb) and EPISODES_D2 (seed, weights, climb
   start in s, grade) are both FROZEN; PROTOCOLS maps them. run_episode()
   builds the cycle (random_road.climb for D2 and C4), builds the env, pins the
   weights after reset and steps a policy; agent_policy() wraps a
   stable-baselines3 model with deterministic=True. C4 was scored on the "d2"
   protocol.
 - run_episode() returns totals only. For per-step frames, write a tracing
   runner in app/ that mirrors run_episode step for step, and PROVE it with a
   test: on the same agent and episode, its total damage, fuel and peak
   turbine temperature equal run_episode's exactly. Without that test the
   picture is not the experiment.
 - Which episode set an agent uses comes from its meta.json "scenario" block
   ("protocol": "random-climb" for D2 and C4), not from the directory name;
   "use_preview" says which arm it is. Which result files belong to a runs directory:
   run_phase_d.result_prefix() (runs -> phase_d, runs_X -> X).
 - "Future experiments" means discovery: any runs*/<arm>_seed<k>/ holding
   meta.json and final.zip appears without a code change.
 - Simulating an episode takes real time (the combustion model is the whole
   cost). Measure it before designing the waiting screen.

THE MAP. For agent episodes, build the road's elevation from the episode's own
grade: distance is the integral of speed, rise the integral of speed x grade.
Scale check before you design: a 12-16 % climb that starts 120-300 s into a
720 s episode at 130 km/h runs roughly 15-22 km and rises roughly 1.8-3.5 km.
The current looping island cannot hold that. Design for it (for example, a
stretch of road that follows the car) and state any vertical exaggeration on
screen.

VERIFY BEFORE SAYING ANYTHING WORKS:
  python -m app.test_simulation     the replay lab's suite
  python -m app.test_replay         the app's regression suite (--full before
                                    a release)
  node --test "app/static/sim/*.test.mjs"
                                    the scene, playback and panel tests --
                                    quote the glob; a bare directory FAILS
                                    on this machine's Node 24
  python verify_docs.py             stage new files first: it scans
                                    git ls-files
Read the counts they print; never quote a count from a document. After any
change under app/, paste the test_replay output into the commit message
(CLAUDE.md, Conventions). Check the real browser at desktop and narrow widths.

MACHINE. Python is
  C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe
(a .venv is blocked by App Control). Never run Python with %TEMP% as the
working directory: a stray inspect.py there shadows the standard library. Set
PYTHONIOENCODING=utf-8 on Windows consoles.

GIT. Commit to JMF-2340550-sep17, never main, and say the branch before every
push. Findings go in files, not only in chat.
```

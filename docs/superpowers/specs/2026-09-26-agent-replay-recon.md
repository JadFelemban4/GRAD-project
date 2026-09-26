# Agent episodes in the replay lab — what was found before designing

26 September 2026. Read-only reconnaissance for `NEXT_SESSION_VIZ_2026-09-26.md`
(agents, grade, a road built from the grade, and jev as a hidden add-on). Six
parallel readers and one critic; nothing in the repository was written, and
`git status --porcelain` was empty after every run. This file is the input to
the design. **It is not the design**, which comes after Jad answers the
brainstorming questions and goes to its own file in this directory.

Every file:line below was read on commit `b6b8149`. Scratch scripts that
produced the measurements lived in the session scratchpad and are not kept.

---

## 1. The mirror is possible, and it has been checked once

A per-step loop in `app/` can reproduce `evaluate.run_episode` exactly.

- **Checked:** a hand-written loop, on `runs_c4/*_seed0` and `EPISODES_D2[0]`,
  returned a result dict `==` to `run_episode`'s, in the same process, for both
  arms. Run over all 20 frozen D2 episodes on CUDA, it reproduced
  `results/c4_seed0.txt` at printed precision (sighted 359.9 / IQR 156.9 /
  worst 674.3; blind 720.5 / 492.6 / 1453.7).
- **The tracer still needs its own test**, as the next-session prompt requires:
  mirror against `run_episode`, same process, same model object, `==` on the
  whole dict. This recon check is not that test.

What the mirror must copy, in order (`evaluate.py:175-202`):

1. Cycle: Phase D `make_grade_climb(duration=720, dt=1.0)`; D2 and C4
   `random_road.climb(start_s, grade, duration=720, dt=1.0)`. **Never** the
   `RandomClimb` wrapper — it draws its own road.
2. `SupervisoryTunerEnv(cycle, dt=1.0, seed=seed, use_preview=...)`.
3. `env.reset(seed=seed)`, then pin `env.w = float32(weights)` and rebuild the
   observation with `env._obs()`. Do not reset again after pinning.
4. Step until `term or trunc`. **An episode is 719 steps, not 720**
   (`engine_env.py:820`, `truncated = k >= n-1`).
5. Peak: max of `info["t_turb"]` after each step, from 0.0, in kelvin. The
   initial 500 K state is excluded.

## 2. A trap found by the critic: CPU and CUDA give different episodes

`evaluate.py:370` loads with no device, which on this machine means CUDA.

| device | damage | fuel | peak °C |
|---|---|---|---|
| CUDA (two runs, bit-identical) | 823.2909890944601 | 5344.675611450641 | 868.1891563294192 |
| CPU (1 and 6 threads, identical) | 823.6139349788583 | 5344.930883009203 | 868.1866302074901 |

`runs_c4/sighted_seed1`, `EPISODES_D2[0]`. The actions differ from step 0, by
up to 0.117 in one action. **The tracer must load on the same device as
`evaluate.py` and record the device in each trace.** A machine without CUDA
will draw a slightly different run from the one that was scored, and the page
should say so rather than hide it.

## 3. Cost

- **One agent episode: 34–37 s of wall time** on this machine (measured four
  times, CPU or CUDA; 37.4 s for 719 steps, 19.2 steps/s). The network is
  0.42 ms per step; the plant is 51.7 ms per step (six `run_cycle` calls).
- One pair is about 70 s run one after the other. The work is CPU-bound Python,
  so a second worker thread does not help.
- All 20 episodes of one agent: about 12 minutes.

## 4. What the trace can read — without touching hashed files

`info` carries 14 keys (`engine_env.py:822-827`): `cost_torque, cost_knock,
cost_egt, torque, torque_req, egt_c` (°C), `ki, spark, lam, t_turb` (K),
`t_oil` (K), `r_fuel, r_life, r_resp`; `episode_summary` on the last step only.

It does **not** carry grade, speed, rpm, MAP, the applied action, or the damage
increment. Read them from the env after each step:

- `env.v`, `env.rpm`, `env.map_kpa`, `env.torque_req`, `env.thermal.*`
- the applied action: `env.prev_act` (after clip, rescale, slew limit, bounds)
- the grade used in the step: `cycle["grade"][env.k - 1]`
- increments: differences of `env.ep["damage"]`, `env.ep["fuel"]` — `ep` is
  mutated in place, so copy each step
- gear: not stored; recover it from rpm and speed with `app.replay.infer_gear`
  (fails below ~15 km/h, during the 0–19 s launch ramp)

Adding one key to `info` in `engine_env.py` would move `plant_sha` and lock out
all 48 agents. Read attributes instead.

## 5. The five actions

`Box(-1, 1, (5,))`, `engine_env.py:540`; ranges `ACT_LO/ACT_HI` (`:513-514`).
The code has no list of action names; these come from where each is used.

| # | what | physical range | kind |
|---|---|---|---|
| 0 | spark trim, degrees | −8 to +4 | trim |
| 1 | lambda trim | −0.15 to +0.06 | trim |
| 2 | boost trim, kPa | −40 to +15 | trim |
| 3 | cooling fan duty | 0 to 1 | **absolute** |
| 4 | coolant pump duty | 0.3 to 1.0 | **absolute** |

`neutral_action()` is `[0.333, 0.429, 0.455, 1, 1]` in network units (fan and
pump at 1.0). Slew limits per second `[1.5, 0.03, 10, 0.25, 0.2]` mean the
applied action differs from the commanded one on many steps (sighted episode 0:
109 / 66 / 11 / 30 / 13 steps of 719). **Show the applied action.**

Observation: 23 values. Index 13 is the current grade (×12); **14–17 are the
preview at 2, 5, 15, 30 s**, and 0.0 for the blind arm.

## 6. The road — the numbers, for all 20 frozen D2 episodes

- Speed is imposed by the scenario (`engine_env.py:729`): a ramp from rest over
  19 s, then 130 km/h. **Every agent in one episode is at the same place at
  every step**, so two cars on one road must be offset sideways.
- **Path: 25.6 km in every episode.** Flat run-in 4.3–10.3 km, then the climb
  15.3–21.3 km along the road.
- **Rise: 1917–3247 m** (seeds 1004 and 1005).
- Grade is tan θ; rise per step is `v·dt·sin(atan g)`. The next-session
  prompt's `∫ v·g` overstates it by ~1.3 % at 16 %.
- Build distance and elevation from one Python array and send them on every
  frame; the browser's trapezoid and a rectangle sum differ by a constant 18 m.
- **Visibility:** at 1:1 the whole-route profile already shows the climb;
  12 % and 16 % differ by only 2.2° on screen. Vertical exaggeration 3–4 gives
  20–33° and keeps the worst episode inside 16:9; above ~4.4 it overflows.
  State the exaggeration on screen.
- **Two scales are needed:** a whole-route profile (a car there is under one
  pixel) and a local chase view of ~200 m.
- **Honest oddity the picture will expose:** the car gains up to 3.2 km of
  altitude while the scenario holds 101.3 kPa and 42 °C (`engine_env.py:934`).
  That is the synthetic stress scenario being deliberately harsher than any
  road, and the page should say so.
- The current lab road is a fixed 4.59 km ellipse with no parameters
  (`app/static/sim/geometry.mjs:33-36`); it cannot hold this.

## 7. Which agents exist, and how to recognise them

| directory | agents | meta.json | protocol |
|---|---|---|---|
| `runs/` | 16 | yes | Phase D: no `scenario.protocol`, fixed 12 % climb at 180 s |
| `runs_d2/` | 16 | yes | `scenario.protocol == "random-climb"` |
| `runs_c4/` | 16 | yes | same as D2; budget 300 000 from the ZIP |
| `runs_sixspeed_18sep/` | 2 | **no** | must be refused |

- Arm: `evaluate.py:369` decides by path (`"blind" in path`); `meta.use_preview`
  agrees for all 48 today. The tracer should follow evaluate and assert the two
  agree.
- C4 and D2 share every fatal fingerprint field; only
  `fingerprint.model_budget` (the ZIP) tells them apart.
- Skip `_logs/`, `checkpoint.zip` and `ckpt_*`; only `final.zip` counts.

## 8. Verdicts

No verdict is machine-readable, and a future `runs_X` will have none. The lines
exist as text: `results/PHASE_D_RESULT.txt:26`, `results/PHASE_D2_RESULT.txt:30`,
`results/C4_RESULT.txt:42` (with `:33` the tests disagree, `:48`
NOT-CONVERGED). Parsers already exist (`analyse_phase_d2.load`). **Per-episode
values are never saved** — result files hold 20-episode medians — so one
episode's gap will not equal the seed's table row (C4 seed 0's +360.6 is a
difference of medians). The page must not imply it does.

"Baseline" means two things: the results' baseline row is `p_neutral` run as
the agent (`evaluate.py:347`); `env.thermal_base` / `ep["damage_base"]` is the
env's internal ECU twin. Do not label the second "baseline" beside the first.

## 9. Risks to hard rules, and the fix for each

| risk | fix |
|---|---|
| `check_model_fingerprint` raises `SystemExit`; the replay worker catches only `Exception`, so a refused agent would rebuild forever | call `fingerprint.compare` directly |
| `plant_fingerprint` runs `git status` on every call and hashes files on disk | compute once at start-up with `GIT_OPTIONAL_LOCKS=0` |
| new routes would also exist in the `--live` process connected to the car, and a 35 s CPU build holds the GIL against the live pump | register agent and jev routes only under `--simulation` |
| recorded-car data reaching jev | the jev route takes only a server-side key (episode id, step) into a simulated trace; never state sent from the browser |
| API key leaks | `.gitignore` has **no** secrets pattern today — add one before any key file exists; sanitise SDK exceptions (replay errors reach the browser verbatim, `replay.py:320`); never put jev config in the meta JSON the page prints; never enable the SDK's debug logging (it writes request bodies) |
| `app/test_replay.py`'s read-only test scans only top-level `app/*.py` and bans `.write(`; nothing bans outbound HTTP | extend the test when a jev client is added |
| a jev network failure silently replaced by a neutral action | abort the episode and say so |

## 10. jev — vendor claims, read 26 September 2026

Every figure here is **typesafe.ai's claim**; nothing was sent to the service.

- `POST https://api.typesafe.ai/v1/systemone`, bearer key; Python SDK
  `typesafe-sdk` (`typesafe_sdk.TypeSafeClient`), key from `TYPESAFE_API_KEY`,
  model `jev-latest` = `jev-1.13.0`.
- Input: a state (text or JSON) plus a map of typed questions. Text only.
- **Output has no numeric type.** Three question types: yes/no probability,
  choice (≤255 options, with probabilities), score (2–10 levels, with a
  probability-weighted mean). The vendor warns against reading a score as a
  precise number and says "Jev is not a calculator". **Five questions — one
  per action — fit in one call**, answered independently. Mapping each answer
  onto [−1, 1] is therefore a discretisation this project must choose and show.
- Latency 70–500 ms, "about 100 ms" typical, measured from the US West Coast;
  nothing from Jeddah. A jev-driven episode is 719 calls: roughly 1–6 minutes
  of calls plus the 35 s of plant.
- $0.042 per million input tokens, output free; 1 200 requests per minute.
- Early access from a waitlist; keys at `console.typesafe.ai/keys`.
- **Hosted in the United States.** The site terms say it is "intended for
  visitors located within the United States", and the customer agreement has
  an export clause — **whether access from Saudi Arabia is allowed is unknown.**
- The agreement **forbids training a model to imitate jev's output**. jev must
  never feed any training in this project.
- Not trained on customer inputs, but inputs may be kept for telemetry "in
  perpetuity". Another reason to send only simulated state.

## 11. The hidden gesture — where it can live

The cleanest target is the footer label `01 — REPLAY`
(`app/static/simulation.html:95`): not a link, no handler, visible at narrow
widths (small, 7 px, on a phone). The canvas belongs to OrbitControls, and the
heading and cards have `pointer-events:none`. A pure tap-counter module can be
unit-tested like `playback.test.mjs`.

## 12. Jad's answers so far (brainstorming, 26 September)

1. **Audience: both** — Jad himself, to see what each agent decided at each
   moment, **and** the supervisor or examining committee, as a demonstration.
   So every honesty label must survive being shown to someone who did not
   write it.
2. **Jad has a jev API key.** It must never be pasted into the chat or
   committed; it goes in an environment variable or an untracked file, after
   the `.gitignore` pattern exists (section 9).
3. **jev mode: the paused moment first.** Pause an agent episode, ask jev once
   what it would decide there, show it beside the two agents' applied actions.
   jev driving a whole episode as a third car is **deferred**, not dropped.
   Jad's own reading of the limit, correct: jev is a classification and
   decision system, so its answer is a choice among levels, not a number.
4. **Compute every episode live; save no traces to disk.** Jad's reason: a
   saved trace "feels like cheating — it would be like reading the results",
   and he wants to see the decisions being made. (The small correction given:
   a saved trace would hold the same decisions bit for bit, made earlier —
   not results. The choice stands, and it is also the stronger one in front of
   a committee.) Cost accepted: ~35 s of plant per agent episode on every
   run. This keeps the replay lab's memory-only policy unchanged.
5. **jev sees the sighted agent's view:** the engine state now plus the road
   ahead (the preview). Jad adds that the 30 s horizon may change in a future
   experiment if the team decides it, for example after a longer training
   budget. **Design consequence:** the page and the jev prompt read the
   horizons from the code (`engine_env.PREVIEW_S`, and the observation the
   agent was actually given), never from a constant of their own. Note for the
   team, not for this page: changing `PREVIEW_S` inside `engine_env.py` moves
   `plant_sha` and locks out all 48 existing agents everywhere; D2 avoided the
   same trap by putting its road in a wrapper (`random_road.py`).
6. **The hidden gesture:** ten taps within four seconds on the small footer
   label `01 — REPLAY` opens the jev panel. **The unlock is forgotten on page
   reload** — nothing is stored in the browser — so a page opened in front of
   the committee shows no jev panel unless Jad opens it there.

## 13. Current tests, as run during this recon

`node --test "app/static/sim/*.test.mjs"`: 30 of 30. `python -m
app.test_simulation`: 15 of 15. `app.test_replay` was not run. Re-run all three
before quoting them; these are counts from 26 September, not constants.

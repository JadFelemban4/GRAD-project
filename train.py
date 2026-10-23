"""train.py -- Phase C: every training design this project has run, in one file.

Trains a SAC agent on the engine environment and saves everything Phase D needs.

    pip install "stable-baselines3[extra]"      # once; also uncomment it in requirements.txt

A ROAD NAMES A DESIGN, AND A DESIGN INCLUDES ITS STEP. Five designs exist:

    --road wideair   dt 1.0   X2 (11 Oct, results/PREREGISTRATION_X2.md): the extremes
                              roads in wider air, ambient 0-45 C and pressure 80-101.3 kPa
                              drawn per episode, the compressor inlet following the
                              pressure (wide_air.WideAirTrainingEnv) -> runs/wideair_dt1/

    --road extremes  dt 1.0   decision 12 of results/VALIDATION_DECISIONS.md (8 Oct):
                              the terrain roads with ambient 25-45 C, a speed target
                              that changes mid-run (60-150 km/h), hills to 18 % and
                              the housing's heat capacity drawn per episode
                              (engine_env.ExtremesTrainingEnv) -> runs/extremes_dt1/

    --road terrain   dt 1.0   a new road every episode (engine_env.TerrainTrainingEnv),
                              scored by evaluate.py on the locked climb. The design
                              of the 29 September retrain. DEFAULT -> runs/terrain_dt1/,
                              CLOSED since 8 October (its result is published)
    --road fixed     dt 0.2   Phase D's one locked climb, 12 % from 180 s.
                              CLOSED: runs/ takes no new work -- give it --out
    --road random    dt 0.2   Phase D2 and C4: a new climb every episode, start
                              120-300 s, grade 12-16 %. CLOSED: runs_d2/, runs_c4/

    python train.py --engine b58 --steps 50000 --seed 0                  # terrain, dt 1.0
    python train.py --engine b58 --steps 50000 --seed 0 --no-preview     # its blinded arm
    python train.py --engine b58 --steps 50000 --seed 0 --fixed-road     # locked climb at dt 1.0
    python train.py --engine b58 --steps 50000  --seed 0 --road fixed  --out runs_x
                                              # C1: the first bad run (11 episodes at dt 0.2)
    python train.py --engine b58 --steps 300000 --seed 0 --road random --out runs_c5
                                              # C4's design, in a NEW directory
    python train.py ... --no-preview          # the blinded arm of any of them

--engine IS REQUIRED (20 October 2026, decision 24: the H/tau test runs four
engines). It names the plant every environment is built on (engines.get), and
meta.json's fingerprint -- schema 3 -- records it in three FATAL fields: engine,
engine_sha and backend. A run directory holding a schema-2 meta.json (every
agent trained before the four-engine build) is not resumed: its record names no
engine. NOTHING TRAINS ON GRA-test until decision 25 says so.

--keep-buffer (11 October 2026) saves the replay buffer beside every checkpoint
(OUT/<tag>/replay_buffer.pkl, overwritten each time) and loads it when the run
resumes. Without it a resumed run starts from an empty buffer, so for a while it
learns from a handful of fresh transitions, which an unbroken run never does.
The road and weight streams still restart at a resume, and the policy's
sampling noise is not saved, so a resumed run is CLOSE to an unbroken one, not
equal to it; config.json records every resume and the buffer it restored. For
runs long enough that restarting from step 0 is not an option (X2: 1 080 000
steps, about 50 hours).

A NEW BUDGET NEEDS ITS OWN --out. `--steps 300000` into runs/ or runs_d2/ is
refused: those hold the Phase D and D2 agents, and continuing one of them is not
a C4 run. See "A RESUME IS NOT A LONGER RUN" below.

(train_all.py and run_phase_d.py are the two launchers. Neither should lean on
the defaults above: a default that selects an experiment is the trap AUDIT2.md
Part 3 is about. Both pass --engine, --road and --device explicitly, and
train_all.py --dt; run_phase_d.py's fixed and random roads train at their
design step, DESIGN_DT.)

THE DEVICE ASKED FOR IS THE DEVICE TRAINED ON (21 October 2026, the review of
benchmark_training.py). An explicit --device that torch cannot give is refused:
stable-baselines3 would fall back to the CPU without a word. On CUDA a run
needs CUBLAS_WORKSPACE_CONFIG to be check_training_device.CUBLAS_WORKSPACE
(the launchers set it) and trains with torch's deterministic algorithms, and
config.json records the CUDA build, the driver and both settings. The CPU
path is unchanged (check_device).
"""
import argparse
import csv
import glob
import json
import platform
import re
import os
import subprocess
import time
from datetime import datetime

import numpy as np

import engines
import fingerprint as FP
import random_road as RR
import step_record
from engine_env import (ExtremesTrainingEnv, SupervisoryTunerEnv, TerrainTrainingEnv,
                        damage_rate, locked_climb)

try:
    import gymnasium as gym
    from stable_baselines3 import SAC
    from stable_baselines3.common.monitor import Monitor
    from stable_baselines3.common.callbacks import BaseCallback, CallbackList, CheckpointCallback
    from stable_baselines3.common.utils import get_device
except ImportError:
    raise SystemExit(
        "stable-baselines3 is not installed.\n\n"
        '    pip install "stable-baselines3[extra]"\n\n'
        "Then uncomment the two lines under 'Phase C onward' in requirements.txt\n"
        "so the rest of the team installs the same thing."
    )

HERE = os.path.dirname(os.path.abspath(__file__))

# Experiments whose preregistrations say "sixteen runs, then stop". Nothing new
# is trained into their directories -- see "CLOSED EXPERIMENTS" in main().
CLOSED = {"runs": "Phase D", "runs_d2": "Phase D2",
          "runs_c4": "C4",           # closed 24 Sep 2026, after its result
          "terrain_dt1": "the 29 September retrain",   # closed 8 Oct 2026
          "extremes_dt1": "X1"}      # closed 9 Oct 2026, after its result (PREREGISTRATION_X1.md §12)

# Each road's own step. fixed and random are the designs Phase D, D2 and C4 ran
# at 0.2 s; terrain is the 27 September design at evaluate.py's 1.0 s.
DESIGN_DT = {"fixed": 0.2, "random": 0.2, "terrain": 1.0, "extremes": 1.0, "wideair": 1.0}
# The training episode, s: --duration's default, "the standard scenario". A
# module constant since 21 October 2026, so verify_docs.py can check the 900 s
# the documents quote against the live value: it read make_grade_climb's
# duration= default until that default went (the review of build step 1).
DURATION_S = 900.0


def refuse_old_schema(stored, outdir, force):
    """Refuse to train into `outdir` when its meta.json (`stored`, or None when
    there is none) is an older fingerprint schema: a record of schema 2 or less
    names no engine (20 October 2026), and is refused with its own message
    before any field is compared. --force-plant-mismatch (`force`) lets it
    through, as it does every other plant refusal. A function since 21 October
    2026, so test_plant_guards.py can show it refuses (the review of build step 1)."""
    if stored is not None and FP.schema_problem(stored) and not force:
        raise SystemExit(f"\nREFUSING: {outdir}: {FP.schema_problem(stored)}\n"
                         "Train into a fresh --out directory.")


def check_device(asked, device):
    """Refuse to train on a device other than the one asked for, and make CUDA
    deterministic before anything runs on it (21 October 2026, the review of
    benchmark_training.py).

    `asked` is --device as given, `device` what stable-baselines3's get_device
    made of it -- the CPU, without a word, when --device cuda meets a torch with
    no usable CUDA, and a CUDA experiment would then hold CPU agents (rule 3,
    decision 32). "auto" is never refused. On CUDA a run is refused unless
    CUBLAS_WORKSPACE_CONFIG is check_training_device.CUBLAS_WORKSPACE, the one
    cuBLAS workspace every CUDA run trains with (that constant says why), and
    torch's deterministic algorithms are switched on. On the CPU it compares
    two strings and refuses or returns, with no import and no torch setting, so
    a CPU run trains the agent it trained before by construction. That is not
    re-certified: level L8 of results/B58_IDENTITY.md ran before this function
    existed. A function so test_plant_guards.py can show it refuses."""
    if asked != "auto" and device.type != asked.split(":")[0]:
        raise SystemExit(f"\nREFUSING: --device {asked} was asked for and torch offers {device}.\n"
                         "stable-baselines3 would train there without a word, and one experiment "
                         "trains on one device type (rule 3, decision 32).")
    if device.type == "cuda":
        from check_training_device import CUBLAS_WORKSPACE
        have = os.environ.get("CUBLAS_WORKSPACE_CONFIG")
        if have != CUBLAS_WORKSPACE:
            raise SystemExit(f"\nREFUSING to train on CUDA with CUBLAS_WORKSPACE_CONFIG {have!r}: every "
                             f"CUDA run trains with {CUBLAS_WORKSPACE}\n(check_training_device."
                             "CUBLAS_WORKSPACE says why). train_all.py, run_phase_d.py and "
                             "benchmark_training.py set it for --device cuda.")
        import torch
        torch.use_deterministic_algorithms(True)


def cuda_machine(device):
    """What fixes a CUDA run's bits besides the versions, for config.json's
    machine block: the CUDA torch was built with, the driver (from nvidia-smi;
    torch does not report it), the GPU, the cuBLAS workspace and the
    deterministic switch. Written for CUDA runs only: a CPU run's config.json
    is what it was. Called before the timed window opens (t0): nvidia-smi is a
    process of its own, and its seconds are not training's (the review of 21
    October 2026)."""
    import torch
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                           capture_output=True, text=True, timeout=30)
        driver = r.stdout.strip().splitlines()[0].strip() if r.returncode == 0 and r.stdout.strip() else None
    except (OSError, subprocess.SubprocessError):
        driver = None
    return dict(torch_cuda=torch.version.cuda, driver=driver, gpu=torch.cuda.get_device_name(device),
                cublas_workspace_config=os.environ.get("CUBLAS_WORKSPACE_CONFIG"),
                deterministic_algorithms=torch.are_deterministic_algorithms_enabled())


def buffer_size(a):
    """How many transitions the replay buffer holds.

    `--buffer` if given, otherwise the run's own length, floored at 10 000 so a
    very short smoke run still has somewhere to sample from, and capped at
    SB3's default so this can only ever ask for LESS memory than before.
    """
    if a.buffer is not None:
        return int(a.buffer)
    return int(min(1_000_000, max(10_000, a.steps)))


class _RoadLog(gym.Wrapper):
    """Keeps the D2 road each episode drew, for curve.csv. It only reads."""

    def __init__(self, env):
        super().__init__(env)
        self.road_log = []

    def reset(self, **kw):
        obs, info = self.env.reset(**kw)
        r = info.get("road") or {}
        self.road_log.append(f"climb {r.get('start_s', float('nan')):.0f}s "
                             f"{100 * r.get('grade', float('nan')):.2f}%")
        return obs, info


class _StepState(gym.Wrapper):
    """Puts into every step's info what the environment holds and its info dict
    does not -- the road (grade, speed, gear), the parallel baseline car, the
    episode's running totals (step_record.env_state) -- and what the actuators
    applied, the damage rate and the episode's preference weights, so that
    ActionRecorder keeps the road and the car beside every training action
    (7 October 2026; until then a terrain run kept no road at all). Read after
    the step returns, before the vector env resets. It only reads."""

    def step(self, action):
        obs, r, term, trunc, info = self.env.step(action)
        u = self.env.unwrapped
        info = dict(info, **step_record.env_state(u))
        info["applied"] = np.asarray(u.prev_act, np.float32)
        info["weights"] = np.asarray(u.w, np.float32)
        info["damage_rate"] = damage_rate(info["t_turb"], info["t_oil"], info["ki"],
                                          cal=u.plant.engine.damage)
        return obs, r, term, trunc, info


def build_env(use_preview, seed, duration, road="terrain", dt=1.0, *, plant):
    """The training environment. dt is passed EXPLICITLY, to the cycle and the env,
    and so is the plant (required, 20 October 2026).

    terrain  TerrainTrainingEnv: a new road every episode.
    extremes ExtremesTrainingEnv: the same roads, plus ambient, speed, steeper
             hills and the housing's heat capacity drawn per episode.
    fixed    make_grade_climb, Phase D's road.
    random   the same, rebuilt at every reset by random_road.RandomClimb (D2).

    The wrappers sit INSIDE Monitor, so Monitor's episode returns are the
    returns of the drawn roads, and `env.unwrapped` still reaches the
    SupervisoryTunerEnv for `dt` and the fingerprint. At dt 0.2 the fixed and
    random builds are the objects Phase D and D2 trained on.
    """
    if road == "terrain":
        env = TerrainTrainingEnv(duration=duration, dt=dt, use_preview=use_preview, seed=seed,
                                 plant=plant)
    elif road == "wideair":
        # Imported here, not at the top, as before. It used to matter more:
        # importing wide_air swapped engine_env's boost ceiling for the whole
        # process until 20 October 2026; the inlet is each environment's own now.
        from wide_air import WideAirTrainingEnv
        env = WideAirTrainingEnv(duration=duration, dt=dt, use_preview=use_preview, seed=seed,
                                 plant=plant)
    elif road == "extremes":
        env = ExtremesTrainingEnv(duration=duration, dt=dt, use_preview=use_preview, seed=seed,
                                  plant=plant)
    else:
        env = SupervisoryTunerEnv(locked_climb(plant, duration=duration, dt=dt), plant=plant, dt=dt,
                                  use_preview=use_preview, seed=seed)
        if road == "random":
            env = _RoadLog(RR.RandomClimb(env, seed=seed, duration=duration))
    return Monitor(_StepState(env))


def _road_log(env):
    try:
        return list(env.get_wrapper_attr("road_log"))
    except AttributeError:
        return []


def derived_sha(plant):
    """A hash of the plant's derived file's values (data/derived_params.json for
    the B58): since 28 September the plant's thermal, boost, spark, enrichment
    and gearbox constants live there. Since 8 October it is fingerprint.py's
    own, and FATAL there: one definition. The plant is required (20 October)."""
    return FP.derived_sha(os.path.join(HERE, plant.engine.derived))


# What the engine did on each training step, read off the step's info dict:
# since 7 October 2026 every field step_record.py defines (the road, the gear,
# the baseline car, the running totals, which _StepState adds to the info
# dict), plus the applied actuators and the episode's preference weights.
REC_INFO = step_record.INFO + step_record.ENV
REC_VEC = ("applied", "weights")
CHUNK = 10_000          # the checkpoint interval; a chunk is written with each one


class ActionRecorder(BaseCallback):
    """Every action the agent takes while it learns, and what it cost.

    Per step: the timestep, the episode, the ACTION (the network's output in
    [-1, 1], exactly what went to env.step), the OBSERVATION it was chosen from,
    the reward, and the engine quantities in REC_INFO. It only reads: an agent
    trained with it is the agent trained without it (30 Sep 2026, 600 steps, on
    CUDA and on CPU: largest weight difference 0.0). Re-checked 7 October with
    _StepState and the 44 fields: seed 0, 600 steps, CPU, against the train.py
    of 2864592 -- largest weight difference 0.0; the 18 fields both keep agree
    exactly, or to the float16 rounding the old record stored them at.
    """

    def __init__(self, outdir):
        super().__init__()
        self.dir = os.path.join(outdir, "record")
        os.makedirs(self.dir, exist_ok=True)
        self._clear()

    def _clear(self):
        self.buf = {k: [] for k in ("step", "episode", "action", "obs", "reward") + REC_INFO + REC_VEC}

    def _on_training_start(self):
        prev = [np.load(f)["episode"] for f in glob.glob(os.path.join(self.dir, "rec_*.npz"))]
        prev = [p for p in prev if len(p)]
        self.episode = int(max(p.max() for p in prev)) + 1 if prev else 0

    def _on_step(self):
        b = self.buf
        b["step"].append(self.num_timesteps)
        b["episode"].append(self.episode)
        b["action"].append(np.asarray(self.locals["actions"][0], np.float32))
        b["obs"].append(np.asarray(self.model._last_obs[0], np.float32))
        b["reward"].append(float(self.locals["rewards"][0]))
        info = self.locals["infos"][0]
        for k in REC_INFO:
            b[k].append(info.get(k, np.nan))
        for k in REC_VEC:
            b[k].append(np.asarray(info.get(k, np.full(5 if k == "applied" else 3, np.nan)), np.float32))
        if self.locals["dones"][0]:
            self.episode += 1
        if self.num_timesteps % CHUNK == 0:
            self._flush()
        return True

    def _on_training_end(self):
        self._flush()

    def _flush(self):
        b = self.buf
        if not b["step"]:
            return
        path = os.path.join(self.dir, f"rec_{b['step'][0]:07d}_{b['step'][-1]:07d}.npz")
        np.savez_compressed(path, **_record_arrays(b))
        self._clear()


def _record_arrays(b):
    """step_record.cast's rule: float16 for the observation, integers as they
    are, float32 for everything else (the engine fields were float16 until
    7 October: 1 K steps at a turbine temperature)."""
    out = dict(step=np.asarray(b["step"], np.int32), episode=np.asarray(b["episode"], np.int32))
    for k in ("action", "obs", "reward") + REC_INFO + REC_VEC:
        out[k] = step_record.cast(k, np.asarray(b[k]))
    return out


BUFFER_FILE, BUFFER_STAMP = "replay_buffer.pkl", "replay_buffer.json"


class BufferKeeper(BaseCallback):
    """--keep-buffer: the replay buffer, written beside every checkpoint.

    Same cadence as the CheckpointCallback before it in the list (every CHUNK
    calls of this session), so the buffer on disk belongs to the latest
    ckpt_*_steps.zip unless the process died between the two writes; the stamp
    says which step it was saved at. One file, overwritten through a temporary
    name, so a kill mid-write leaves the previous buffer whole. It only reads
    the model. The buffer saved at step N holds N - 1 transitions:
    stable-baselines3 stores a step's transition just after the callbacks run
    (checked 11 October: killed after step 1000, resumed with 999)."""

    def __init__(self, outdir):
        super().__init__()
        self.path = os.path.join(outdir, BUFFER_FILE)
        self.stamp = os.path.join(outdir, BUFFER_STAMP)

    def _on_step(self):
        if self.n_calls % CHUNK == 0:
            tmp = self.path[:-len(".pkl")] + ".saving.pkl"
            self.model.save_replay_buffer(tmp)
            os.replace(tmp, self.path)
            with open(self.stamp, "w", encoding="utf-8") as fh:
                json.dump(dict(num_timesteps=int(self.num_timesteps),
                               transitions=int(self.model.replay_buffer.size())), fh)
        return True


def load_buffer(model, outdir, done_steps):
    """Put the saved replay buffer back into a resumed model; say what it was."""
    path = os.path.join(outdir, BUFFER_FILE)
    if not os.path.exists(path):
        print("  no saved replay buffer: this resume starts from an EMPTY one")
        return dict(restored=False)
    model.load_replay_buffer(path)
    try:
        with open(os.path.join(outdir, BUFFER_STAMP), encoding="utf-8") as fh:
            saved_at = json.load(fh).get("num_timesteps")
    except (OSError, ValueError):
        saved_at = None
    n = int(model.replay_buffer.size())
    print(f"  replay buffer restored: {n:,} transitions, saved at step {saved_at}"
          + ("" if saved_at == done_steps else
             f" -- NOT the checkpoint's step {done_steps}; the transitions between are missing"))
    return dict(restored=True, transitions=n, saved_at=saved_at, checkpoint_step=int(done_steps))


def merge_records(outdir):
    """The chunks, in step order, as one train_record.npz. A step recorded twice
    keeps its LAST recording, the one the saved model continued from."""
    files = glob.glob(os.path.join(glob.escape(outdir), "record", "rec_*.npz"))
    if not files:
        return None
    parts = [dict(np.load(f)) for f in sorted(files, key=os.path.getmtime)]
    # A run resumed across 7 October holds chunks with fewer fields: keep the
    # fields every chunk has.
    keys = [k for k in parts[0] if all(k in p for p in parts)]
    cat = {k: np.concatenate([p[k] for p in parts]) for k in keys}
    rev = cat["step"][::-1]
    _, first_in_rev = np.unique(rev, return_index=True)
    keep = np.sort(len(rev) - 1 - first_in_rev)
    cat = {k: v[keep] for k, v in cat.items()}
    path = os.path.join(outdir, "train_record.npz")
    np.savez_compressed(path, **cat)
    return path, int(len(keep))


def _git(*args):
    try:
        return subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL,
                                       cwd=HERE).strip()
    except Exception:
        return None


ROADS_TEXT = {"terrain": "a new road every episode (TerrainTrainingEnv)",
              "extremes": "a new road every episode, ambient 25-45 C, speed target 60-150 km/h "
                          "changing mid-run, hills to 18 %, housing capacity x0.75-1.33 "
                          "(ExtremesTrainingEnv, decision 12)",
              "wideair": "the extremes roads (decision 12) in wider air: ambient 0-45 C and "
                         "pressure 80-101.3 kPa drawn per episode, the compressor inlet "
                         "following the pressure (wide_air.WideAirTrainingEnv, X2)",
              "fixed": "the locked climb only",
              "random": "a new climb every episode (random_road.RandomClimb, Phase D2)"}


def run_config(a, tag, model, outdir, live, plant_obj):
    """Everything needed to say what this agent is, written beside it.
    The git fields are meta.json's, so the two files cannot disagree."""
    import stable_baselines3
    import torch
    try:
        with open(os.path.join(HERE, plant_obj.engine.derived), encoding="utf-8") as fh:
            plant = json.load(fh).get("_inputs")
    except (OSError, ValueError):
        plant = None
    return dict(
        tag=tag, seed=a.seed, preview=not a.no_preview, steps=a.steps, dt=a.dt,
        duration_s=a.duration, steps_per_episode=int(round(a.duration / a.dt)),
        road=a.road, roads=ROADS_TEXT[a.road],
        device=str(model.device), algorithm="SAC",
        sac=dict(learning_rate=a.lr, buffer_size=model.buffer_size, batch_size=model.batch_size,
                 learning_starts=model.learning_starts, gamma=model.gamma, tau=model.tau,
                 train_freq=str(model.train_freq), gradient_steps=model.gradient_steps,
                 ent_coef=str(model.ent_coef), target_entropy=float(model.target_entropy),
                 policy="MlpPolicy", net_arch=str(model.policy.net_arch)),
        versions=dict(python=platform.python_version(), stable_baselines3=stable_baselines3.__version__,
                      torch=torch.__version__, gymnasium=gym.__version__, numpy=np.__version__),
        git_head=live.get("git_head"), git_dirty=live.get("git_dirty"),
        plant_sha=live.get("plant_sha"), derived_sha=live.get("derived_sha"),
        engine=live.get("engine"), engine_sha=live.get("engine_sha"), backend=live.get("backend"),
        plant_inputs=plant, output=outdir.replace(os.sep, "/"),
        machine=dict(system=platform.system(), processor=platform.processor(), cpus=os.cpu_count(),
                     omp_threads=os.environ.get("OMP_NUM_THREADS")))


def main():
    ap = argparse.ArgumentParser()
    # engines.trainable(), not known() (22 October 2026, decision 47): an EPA engine is
    # registered and refused here until fingerprint schema 4 and its validation exist
    ap.add_argument("--engine", required=True, choices=engines.trainable(),
                    help="the plant to train on (engines.get), one that may train "
                         "(engines.trainable(), decision 47). REQUIRED: there is no "
                         "default engine (CLAUDE.md mistake 1)")
    ap.add_argument("--steps", type=int, default=50_000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-preview", action="store_true",
                    help="the blinded baseline for Phase D step D3")
    ap.add_argument("--duration", type=float, default=DURATION_S,
                    help="episode length in seconds; 900 is the standard scenario")
    ap.add_argument("--lr", type=float, default=3e-4,
                    help="divide by 3 if the reward curve climbs then collapses")
    ap.add_argument("--road", choices=("terrain", "extremes", "wideair", "fixed", "random"), default="terrain",
                    help="terrain: a new road every episode (27 Sep). extremes: the same, "
                         "with ambient, speed, steeper hills and the housing capacity drawn "
                         "per episode (decision 12, 8 Oct). fixed: Phase D's "
                         "climb, 12 %% from 180 s. random: Phase D2 / C4, start 120-300 s, "
                         "grade 12-16 %%.")
    ap.add_argument("--fixed-road", action="store_true",
                    help="the same as --road fixed --dt 1.0 (the 27 Sep spelling)")
    ap.add_argument("--dt", type=float, default=None,
                    help="step length, s. Default: the design's own -- 1.0 for terrain "
                         "(evaluate.py's step), 0.2 for fixed and random (Phase D, D2, C4)")
    ap.add_argument("--device", default="auto",
                    help="auto (SB3's default: cuda where torch has it, else cpu), cpu or cuda. "
                         "CPU and CUDA train different agents from one seed; the device is "
                         "written into meta.json. A device torch cannot give is refused, and "
                         "CUDA needs CUBLAS_WORKSPACE_CONFIG (check_device)")
    ap.add_argument("--out", default=None,
                    help="default runs/terrain_dt1 for terrain; runs/ and runs_d2/ -- both "
                         "CLOSED -- for fixed and random at their own dt; otherwise "
                         "runs/<road>_dt<dt>")
    ap.add_argument("--buffer", type=int, default=None,
                    help="SAC replay buffer size. Default: sized to the run, "
                         "because a buffer bigger than --steps can never fill "
                         "and costs memory for nothing. See the docstring.")
    ap.add_argument("--force-plant-mismatch", action="store_true",
                    help="resume into a run whose meta.json describes a "
                         "DIFFERENT plant. Almost never what you want: the "
                         "resulting agent has seen two physical systems and "
                         "belongs to neither. See AUDIT2.md C2-1.")
    ap.add_argument("--extend", action="store_true",
                    help="resume a run that was started with a DIFFERENT "
                         "--steps, on purpose, to train it further. Without "
                         "this, such a resume is refused: it is not a fresh "
                         "run at the new budget. See 'A RESUME IS NOT A "
                         "LONGER RUN' in the docstring.")
    ap.add_argument("--no-resume", action="store_true",
                    help="record in meta.json that this run must never be "
                         "resumed: a crash is re-run from scratch instead. "
                         "C4's crash rule; run_phase_d.py passes it for every "
                         "new experiment.")
    ap.add_argument("--keep-buffer", action="store_true",
                    help="save the replay buffer with every checkpoint and load "
                         "it on resume (OUT/<tag>/replay_buffer.pkl). See the "
                         "docstring: a resumed run is then close to an unbroken "
                         "one, not equal to it.")
    a = ap.parse_args()
    if a.keep_buffer and a.no_resume:
        raise SystemExit("--keep-buffer exists for resuming; --no-resume forbids it. Pick one.")
    if a.fixed_road:
        if a.road == "random":
            raise SystemExit("--fixed-road and --road random contradict each other.")
        a.road = "fixed"
        if a.dt is None:
            a.dt = 1.0
    if a.dt is None:
        a.dt = DESIGN_DT[a.road]
    if a.out is None:
        if a.road in ("fixed", "random") and a.dt == DESIGN_DT[a.road]:
            a.out = "runs" if a.road == "fixed" else "runs_d2"      # CLOSED: refuses new work
        else:
            a.out = os.path.join("runs", {"fixed": "locked", "random": "random",
                                          "terrain": "terrain", "extremes": "extremes",
                                          "wideair": "wideair"}[a.road]
                                 + f"_dt{a.dt:g}".replace(".", "p"))
    protocol = "d2" if a.road == "random" else "phase-d"
    device = get_device(a.device)
    check_device(a.device, device)      # before any directory, and before anything runs on CUDA
    plant = engines.get(a.engine)

    tag = f"{'blind' if a.no_preview else 'sighted'}_seed{a.seed}"
    outdir = os.path.join(a.out, tag)
    # No directory is created until every refusal below has had its say: a
    # refused call must leave nothing behind, not even an empty folder.
    closed = CLOSED.get(os.path.basename(os.path.normpath(a.out)).lower())

    busy = FP.running_pid(outdir)
    if busy:
        raise SystemExit(f"\nREFUSING: {outdir} is being trained right now by "
                         f"process {busy}. Wait for it, or stop it first.")

    print(f"plant         : {plant.id}   (--engine {a.engine})")
    print(f"configuration : {'BLINDED (no preview)' if a.no_preview else 'sighted'}")
    print(f"road          : {a.road}   ({ROADS_TEXT[a.road]})")
    print(f"step          : dt = {a.dt:g} s, {a.duration / a.dt:.0f} steps per episode, "
          f"{a.steps / (a.duration / a.dt):.0f} episodes")
    print(f"seed          : {a.seed}")
    print(f"steps         : {a.steps:,}")
    print(f"device        : {device}")
    # MEASURED, and the two figures are two machines and two devices:
    #   19.2 steps/s  17 Sep, Jad's 12-core machine, SAC on CUDA, dt 0.2, locked climb
    #   13.7 steps/s  27 Sep, the 20-thread team laptop, SAC on CPU, dt 1.0, varied roads
    # and side by side on that laptop, 11 Oct (a scratch benchmark, X1's roads,
    # the plant of 8 Oct): 7.5 steps/s each with six at once, 6.0 with ten.
    # A step costs six engine evaluations whatever dt is. Re-measure after
    # changing plant.DTHETA_DEG, the plant, the machine or the device.
    STEPS_PER_S = 19.2 if device.type == "cuda" else 13.7
    mins_est = a.steps / STEPS_PER_S / 60
    print(f"estimate      : about {mins_est:.0f} minutes "
          f"({mins_est / 60:.1f} h) at a measured {STEPS_PER_S:.1f} steps/s on {device.type}")
    print(f"output        : {outdir}/\n")

    env = build_env(not a.no_preview, a.seed, a.duration, a.road, a.dt, plant=plant)

    ckpt_path = os.path.join(outdir, "checkpoint.zip")
    periodic = sorted(glob.glob(os.path.join(glob.escape(outdir), "ckpt_*_steps.zip")),
                      key=lambda f: int(re.search(r"ckpt_(\d+)_steps",
                                                  os.path.basename(f)).group(1)))
    resume_from = periodic[-1] if periodic else (ckpt_path if os.path.exists(ckpt_path) else None)
    done_steps = 0
    extending, was_steps = False, None
    buffer_restored = None

    if closed and not resume_from:
        raise SystemExit(
            f"\nREFUSING: {a.out}/ is {closed}'s, a closed experiment, and "
            f"{tag} is not one of its runs.\nA new seed or a new budget is a "
            "new experiment: give it its own --out, e.g. --out runs_c5.")
    if closed and a.extend:
        raise SystemExit(
            f"\nREFUSING: --extend inside {a.out}/ would change one of "
            f"{closed}'s agents after its result was\npublished. Train a new "
            "experiment into its own --out instead.")

    meta_path = os.path.join(outdir, "meta.json")
    # backend: read from the environment this run trains in (an engine_model
    # there would be refused, not recorded as the cycle model)
    live = FP.plant_fingerprint(protocol=protocol, plant=plant,
                                backend=FP.backend_of(env.unwrapped),
                                train_dt=float(env.unwrapped.dt),
                                train_duration=a.duration,
                                steps_requested=a.steps, seed=a.seed,
                                use_preview=not a.no_preview, tag=tag,
                                train_road=a.road, train_device=str(device))
    stored = FP.read(meta_path)
    refuse_old_schema(stored, outdir, a.force_plant_mismatch)

    if resume_from:
        b = FP.model_budget(resume_from)
        if b is None or b["num_timesteps"] is None:
            raise SystemExit(f"\n{resume_from} is not a readable "
                             "stable-baselines3 zip -- refusing to guess how far "
                             "it got.")
        done_steps = b["num_timesteps"]
        if stored is None:
            raise SystemExit(
                f"\n{resume_from} exists but {meta_path} does not.\n"
                "This run predates the plant fingerprint (AUDIT2.md C2-1), so\n"
                "there is no way to tell which plant it was trained on. Train\n"
                "into a fresh --out directory, or delete the old one on purpose."
            )
        bad = FP.compare(stored, live)
        if bad:
            print(FP.format_block(stored, "STORED (meta.json)"))
            print(FP.format_block(live, "LIVE (this tree)"))
            print("\nfields that disagree:")
            for k, was, now in bad:
                print(f"  {k:<20} stored {was!r}  live {now!r}")
            if not a.force_plant_mismatch:
                raise SystemExit(
                    "\nREFUSING to resume: the checkpoint was trained on a "
                    "different plant.\n"
                    "Train into a fresh --out directory, or pass "
                    "--force-plant-mismatch if you\nreally mean it and will say "
                    "so beside every number the run produces."
                )
            print("\n  --force-plant-mismatch given; continuing anyway.")
        # The advisory fields are not refused over, except the ones that change
        # WHAT IS LEARNED: the episode length, the step, the road design, the
        # device, and the derived plant constants.
        adv = FP.advisory_diff(stored, live)
        learned = [t for t in adv if t[0] in ("train_duration", "train_dt", "train_road",
                                              "train_device", "derived_sha")]
        if adv:
            print("\nadvisory fields that moved since this run started:")
            for k, was, now in adv:
                print(f"  {k:<22} stored {was!r}  live {now!r}")
        if learned and not a.force_plant_mismatch:
            raise SystemExit(
                "\nREFUSING to resume: " + ", ".join(t[0] for t in learned) + " changed.\n"
                "The agent would be trained on two different tasks and meta.json would\n"
                "record only the first. Pass the original values, use a fresh --out\n"
                "directory, or pass --force-plant-mismatch and say so beside the result.")
        was_steps = stored.get("steps_requested")
        extending = was_steps != a.steps
        if extending and not a.extend:
            raise SystemExit(
                f"\nREFUSING to resume: {outdir} was started with --steps "
                f"{was_steps}, and this call asks for {a.steps}.\n"
                "That would continue an existing agent, not train a new one at "
                "the new budget.\n\n"
                "  A NEW budget:      use a fresh --out directory, e.g. "
                "--out runs_c5"
                + ("" if closed else
                   "\n  continue THIS run: pass --extend, and say so beside "
                   "every number it produces"))
        if extending and a.steps <= done_steps:
            raise SystemExit(
                f"\n--extend asks for {a.steps} steps but {outdir} already "
                f"holds {done_steps}. Nothing to extend.")
        if stored.get("resume_allowed") is False and done_steps < a.steps:
            raise SystemExit(
                f"\nREFUSING to resume {outdir}: this run was started with "
                f"--no-resume. It holds {done_steps}\nsteps and this call asks "
                f"for {a.steps}. Its experiment re-runs a crash FROM SCRATCH:\n"
                "  python run_phase_d.py ... --seeds <this seed> --restart-crashed\n"
                "moves this directory aside and trains the seed again from step 0.")
        print(f"resuming from {resume_from} at {done_steps} steps")
        model = SAC.load(resume_from, env=env, device=a.device)
        if a.keep_buffer:
            buffer_restored = load_buffer(model, outdir, done_steps)
    else:
        if os.path.exists(os.path.join(outdir, "final.zip")):
            raise SystemExit(
                f"\n{outdir}/final.zip exists but no checkpoint does, so this "
                "would be a\nFRESH run in a directory that already holds a "
                "trained agent.\n\nTrain into a fresh --out directory. If you "
                "meant to retrain over this one,\ndelete it yourself.")
        if stored is not None and FP.compare(stored, live):
            print(FP.format_block(stored, "STORED (meta.json)"))
            print(FP.format_block(live, "LIVE (this tree)"))
            if not a.force_plant_mismatch:
                raise SystemExit(
                    f"\n{meta_path} describes a different plant and there is no "
                    "checkpoint to\nresume. Use a fresh --out "
                    "directory, or pass --force-plant-mismatch.")
        if a.no_resume:
            live["resume_allowed"] = False
        FP.write(meta_path, live)
        print(FP.format_block(live, "PLANT FINGERPRINT (written to meta.json)"))
        print()
        model = SAC("MlpPolicy", env, seed=a.seed, learning_rate=a.lr,
                    buffer_size=buffer_size(a), verbose=1, tensorboard_log=None,
                    device=a.device)

    # On CUDA only, and before t0, so its nvidia-smi call is outside
    # steps_per_s_this_session's window; on the CPU this is one comparison
    cuda_block = cuda_machine(model.device) if model.device.type == "cuda" else None
    t0 = time.time()
    remaining = max(0, a.steps - done_steps)

    # A no-op must be a genuine no-op: nothing below this line may run on it --
    # not the recorder's folder, not config.json (AUDIT2.md H2-3).
    if remaining == 0:
        print(f"already at {done_steps} of {a.steps} steps; nothing to do.")
        print(f"  {outdir}/final.zip, curve.csv and config.json left untouched.")
        print("  A new budget is a new run: use a fresh --out directory. To "
              "continue THIS\n  agent on purpose, pass a larger --steps WITH "
              "--extend. Do not delete this\n  directory in place.")
        return

    cb = CallbackList([CheckpointCallback(save_freq=CHUNK, save_path=outdir,
                                          name_prefix="ckpt", verbose=0)]
                      + ([BufferKeeper(outdir)] if a.keep_buffer else [])
                      + [ActionRecorder(outdir)])

    cfg_path = os.path.join(outdir, "config.json")
    prev = None
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, encoding="utf-8") as fh:
                prev = json.load(fh)
        except (OSError, ValueError):
            prev = None
    cfg = run_config(a, tag, model, outdir, live, plant)
    if cuda_block is not None:
        cfg["machine"]["cuda"] = cuda_block
    cfg.update(keep_buffer=bool(a.keep_buffer), resumed_buffer=buffer_restored)
    cfg.update(started=datetime.now().isoformat(timespec="seconds"), resumed_from=resume_from,
               status="running")
    if isinstance(prev, dict):
        cfg["previous_sessions"] = prev.pop("previous_sessions", []) + [prev]
    with open(cfg_path, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=1)

    FP.claim_running(outdir)
    try:
        _train_and_save(a, model, env, cb, outdir, ckpt_path, remaining,
                        resume_from, extending, was_steps, done_steps,
                        stored, live, meta_path, t0, tag, cfg, cfg_path)
    finally:
        FP.release_running(outdir)


def _save_atomic(model, dest_zip):
    """model.save, but a kill mid-write cannot leave a truncated dest_zip."""
    tmp = dest_zip[:-len(".zip")] + ".saving.zip"
    model.save(tmp)
    os.replace(tmp, dest_zip)


def _write_curve(curve_path, rewards, lengths, roads):
    """APPEND, with each episode's road (AUDIT2.md H2-3). Monitor only knows the
    episodes THIS process ran. Reads a curve.csv of three columns (before the
    road column existed) as well as four. Returns every return, oldest first."""
    prior = []
    if os.path.exists(curve_path):
        with open(curve_path, newline="", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
        if rows and [c.strip() for c in rows[0][:3]] == ["episode", "return", "length"]:
            for r in rows[1:]:
                try:
                    prior.append((float(r[1]), float(r[2]), r[3] if len(r) > 3 else ""))
                except (ValueError, IndexError):
                    pass
    fresh = [(float(r), float(n), road) for r, n, road in zip(rewards, lengths, roads)]
    with open(curve_path, "w", newline="", encoding="utf-8") as fh:
        fh.write("episode,return,length,road\n")
        for i, (r, n, road) in enumerate(prior + fresh):
            fh.write(f"{i},{r:.6f},{n:.0f},{road}\n")
    return np.array([p[0] for p in prior + fresh], dtype=float), len(prior)


def _train_and_save(a, model, env, cb, outdir, ckpt_path, remaining,
                    resume_from, extending, was_steps, done_steps,
                    stored, live, meta_path, t0, tag, cfg, cfg_path):
    model.learn(total_timesteps=remaining, callback=cb, progress_bar=False,
                reset_num_timesteps=(resume_from is None))
    mins = (time.time() - t0) / 60

    _save_atomic(model, os.path.join(outdir, "final.zip"))
    _save_atomic(model, ckpt_path)
    merged = merge_records(outdir)

    if resume_from and extending:
        stored.setdefault("steps_requested_original", was_steps)
        stored["steps_requested"] = a.steps
        stored.setdefault("extensions", []).append({
            "from_steps_requested": was_steps,
            "to_steps_requested": a.steps,
            "resumed_at_step": done_steps,
            "git_head": live.get("git_head"),
            "git_dirty": live.get("git_dirty"),
        })
        FP.write(meta_path, stored)
        print(f"  --extend: meta.json now records {was_steps} -> {a.steps} "
              "steps, under 'extensions'.")

    rewards = np.array(env.get_episode_rewards(), dtype=float)
    lengths = np.array(env.get_episode_lengths(), dtype=float)
    log = _road_log(env)
    roads = [log[i] if i < len(log) else ("locked" if a.road == "fixed" else "?")
             for i in range(len(rewards))]
    curve, n_prior = _write_curve(os.path.join(outdir, "curve.csv"), rewards, lengths, roads)
    if n_prior:
        print(f"  curve.csv: {n_prior} earlier episodes kept, {len(rewards)} appended")

    cfg.update(status="finished", finished=datetime.now().isoformat(timespec="seconds"),
               wall_min_this_session=round(mins, 1),
               steps_per_s_this_session=round(remaining / max(mins * 60, 1e-9), 2),
               episodes_this_session=int(len(rewards)), episodes=int(len(curve)),
               total_timesteps=int(model.num_timesteps),
               recorded_steps=merged[1] if merged else 0)
    with open(cfg_path, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=1)

    print(f"\ntrained in {mins:.0f} min | {len(curve)} episodes ({len(rewards)} this session)"
          + (f" | {merged[1]:,} steps recorded in {merged[0]}" if merged else ""))
    # No first-five-versus-last-five verdict: every episode draws new preference
    # weights (and, on terrain and random, a new road), so consecutive returns
    # are scored with different rulers. evaluate.py's docstring measured it:
    # eleven episodes, -506.4 to +643.6, the largest in the FIRST five.
    print("\n  Episode returns vary with the road and the preference weights, so this")
    print("  curve cannot show learning. Score the run on the frozen episodes:")
    print(f"      python evaluate.py --engine {a.engine}{' --protocol d2' if a.road == 'random' else ''} {outdir}")
    print("  If the agent does not beat the baseline there, re-run test_reward.py")
    print("  before changing anything else -- a broken reward trains normally.")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        if len(curve) >= 5:
            k = max(1, len(curve) // 40)
            smooth = np.convolve(curve, np.ones(k) / k, mode="valid")
            plt.figure(figsize=(7, 4))
            plt.plot(curve, lw=0.8, alpha=0.35, color="#9AA7AE", label="episode return")
            plt.plot(np.arange(len(smooth)) + k - 1, smooth, lw=2, color="#E8871E",
                     label=f"moving average ({k})")
            plt.axhline(0, color="#5E6C75", lw=0.8, ls="--")
            plt.xlabel("episode"); plt.ylabel("return")
            plt.title(f"{tag} -- {a.steps:,} steps")
            plt.legend(); plt.tight_layout()
            png = os.path.join(outdir, "curve.png")
            plt.savefig(png, dpi=130)
            print(f"  curve written to {png}")
    except ImportError:
        print("  (matplotlib not importable -- curve.csv written, no plot)")

    if a.road == "terrain":
        print("\nnext: every seed of both arms through train_all.py (the same --steps and "
              f"--out), then\n      python record_agents.py {a.out}")
    else:
        print("\nnext: an experiment's other seeds and arms go through "
              "run_phase_d.py, with the\nsame --steps, --road, --dt and --out -- "
              "never a second directory per seed.")


if __name__ == "__main__":
    main()

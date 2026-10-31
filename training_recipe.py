"""training_recipe.py -- decision 29's recipe, behind train.py flags whose defaults are X1's (row 118).

Decision 29 (results/VALIDATION_DECISIONS.md): 450 000 steps (500 episodes); the scored kind of road as a
fixed 10 % share of training episodes; a learning rate falling linearly to 0 over the last third; the
reported policy is the action average of the checkpoints in the last 50 000 steps. Row 118 puts it in
train.py behind flags whose defaults are X1's, so that L8 (600 SAC steps through train.py) and
check_training_device.py --identity stay valid for the B58 by construction:

    the learning rate   train.py --lr-schedule last-third: LastThird(--lr) (default `constant`: the float
                        --lr, exactly as X1 trained)
    the share           train.py --scored-share --roads-record PATH: four_engine_roads.py (default none)
    the average         train.py --checkpoint-average N, N = DECISION_29_WINDOW = 50 000: the model is saved
                        at snapshot_steps(steps, N) into OUT/<tag>/average/, the manifest written at the end
                        (write_manifest), and AveragedPolicy averages their actions (default none: no
                        snapshot, no manifest)

THE AVERAGE LIVES HERE so that evaluate.py's decision-34 protocol (ORDER step 16, after the last redraw is
recorded; evaluate.py is hashed by roads.json until then, row 121) can import it without importing train.py.
AveragedPolicy has stable-baselines3's predict(obs, deterministic=True) -> (action, None), so evaluate.
agent_policy wraps it as it wraps one model (evaluate.py, agent_policy). Its action is the mean of the
snapshots' deterministic actions, in the network's [-1, 1] (what goes to env.step), computed in float64
and returned as float32. A sampled average is refused: decision 29 reports one deterministic policy.

WHICH CHECKPOINTS (DESIGN). "The checkpoints in the last 50 000 steps": train.py checkpoints every CHUNK =
10 000 steps, so the window (T - 50 000, T] holds five, at T - 40 000, ..., T (410 000 ... 450 000 at the
recipe's 450 000 steps). The window's start, T - 50 000, is the agent before those steps and is left out.
AVERAGE_SNAPSHOTS = 5 spaces them window / 5 apart, which is CHUNK at decision 29's window and lets a
smoke run of a few hundred steps take the same path. The snapshots are saved by their own callback
(train.AverageSnapshots) on num_timesteps, so a resumed run still saves every one it passes, and each is
hashed into the manifest (sha256), which AveragedPolicy checks before it loads anything.

THE SCHEDULE (DESIGN, the reading of "falling linearly to 0 over the last third"). stable-baselines3 calls
a learning-rate schedule with progress_remaining p = 1 - num_timesteps / total_timesteps, 1 at the start
and 0 at the last step (common/base_class.py, _update_current_progress_remaining; a resumed run without
reset_num_timesteps adds the steps already done to the total, so p is the whole run's). LastThird gives
lr0 while p >= 1/3 and lr0 x 3p below it: exactly lr0 for the first two thirds and 0 at the last step,
which the pilot checks ("the learning rate reaches 0", ORDER step 21; train.py writes it into
config.json). It is a module-level class, so the model's zip pickles it by reference to this module.
"""
import hashlib
import json
import os

import numpy as np

DECISION_29_WINDOW = 50_000      # decision 29: the checkpoints in the last 50 000 steps
AVERAGE_SNAPSHOTS = 5            # = DECISION_29_WINDOW / train.CHUNK (DESIGN; see the docstring)
LR_SCHEDULES = ("constant", "last-third")
SNAPSHOT_DIR = "average"
MANIFEST = "checkpoint_average.json"
MANIFEST_SCHEMA = "checkpoint-average/1"


class LastThird:
    """Decision 29's learning rate: lr0 until two thirds of the run, then linearly to 0 at its end."""

    def __init__(self, lr):
        self.lr = float(lr)

    def __call__(self, progress_remaining):
        return self.lr * min(1.0, 3.0 * float(progress_remaining))

    def __repr__(self):
        return f"LastThird(lr={self.lr!r})"


def learning_rate(schedule, lr):
    """What train.py hands SAC as learning_rate: the float itself for `constant` (X1's, unchanged), a
    LastThird for `last-third`."""
    if schedule == "constant":
        return lr
    if schedule == "last-third":
        return LastThird(lr)
    raise ValueError(f"unknown learning-rate schedule {schedule!r}; expected one of {LR_SCHEDULES}")


def snapshot_steps(total_steps, window):
    """The steps the average's snapshots are saved at: AVERAGE_SNAPSHOTS of them, evenly spaced, the last
    at total_steps, all inside (total_steps - window, total_steps]. Refused (ValueError) unless the window
    is positive, no longer than the run and a multiple of AVERAGE_SNAPSHOTS."""
    total_steps, window = int(total_steps), int(window)
    if window <= 0 or window > total_steps or window % AVERAGE_SNAPSHOTS:
        raise ValueError(f"--checkpoint-average {window}: the window must be positive, at most --steps "
                         f"({total_steps}) and a multiple of {AVERAGE_SNAPSHOTS} (decision 29: "
                         f"{DECISION_29_WINDOW})")
    step = window // AVERAGE_SNAPSHOTS
    return [total_steps - window + j * step for j in range(1, AVERAGE_SNAPSHOTS + 1)]


def snapshot_name(step):
    return f"snap_{int(step):07d}_steps.zip"


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_manifest(run_dir, *, total_steps, window):
    """OUT/<tag>/checkpoint_average.json: the rule, and every snapshot with its sha256. Refused
    (FileNotFoundError) if a snapshot the rule names was not saved."""
    steps = snapshot_steps(total_steps, window)
    snaps = []
    for s in steps:
        rel = f"{SNAPSHOT_DIR}/{snapshot_name(s)}"
        path = os.path.join(run_dir, *rel.split("/"))
        if not os.path.isfile(path):
            raise FileNotFoundError(f"{path}: the snapshot at step {s} was not saved; the average needs every one")
        snaps.append(dict(step=int(s), path=rel, sha256=_sha256(path)))
    man = dict(schema=MANIFEST_SCHEMA, total_steps=int(total_steps), window=int(window),
               rule=(f"the action average of the {AVERAGE_SNAPSHOTS} snapshots in ({int(total_steps) - int(window)}, "
                     f"{int(total_steps)}] steps (decision 29), each the deterministic action of one saved model"),
               snapshots=snaps)
    with open(os.path.join(run_dir, MANIFEST), "w", encoding="utf-8") as fh:
        json.dump(man, fh, indent=1)
    return man


def read_manifest(run_dir):
    """The manifest, every snapshot's sha256 checked against its file. Refused (ValueError) on a mismatch."""
    with open(os.path.join(run_dir, MANIFEST), encoding="utf-8") as fh:
        man = json.load(fh)
    if man.get("schema") != MANIFEST_SCHEMA:
        raise ValueError(f"{run_dir}: manifest schema {man.get('schema')!r}, not {MANIFEST_SCHEMA!r}")
    if [s["step"] for s in man["snapshots"]] != snapshot_steps(man["total_steps"], man["window"]):
        raise ValueError(f"{run_dir}: the manifest's snapshots are not the rule's")
    for s in man["snapshots"]:
        path = os.path.join(run_dir, *s["path"].split("/"))
        if _sha256(path) != s["sha256"]:
            raise ValueError(f"{path}: its sha256 is not the manifest's; the snapshot changed after training")
    return man


class AveragedPolicy:
    """Decision 29's reported policy: the action average of a run's snapshots.

    predict(obs, deterministic=True) -> (action, None), stable-baselines3's interface, so evaluate.
    agent_policy can wrap it. Loaded on the CPU, the training-only fields (the learning rate and its
    schedule) replaced on load, as stable-baselines3's custom_objects allows: the average never trains."""

    def __init__(self, models, manifest):
        self.models = list(models)
        self.manifest = manifest

    @classmethod
    def load(cls, run_dir, *, device="cpu"):
        from stable_baselines3 import SAC
        man = read_manifest(run_dir)
        models = [SAC.load(os.path.join(run_dir, *s["path"].split("/")), device=device,
                           custom_objects={"learning_rate": 0.0, "lr_schedule": lambda _: 0.0})
                  for s in man["snapshots"]]
        return cls(models, man)

    def predict(self, observation, state=None, episode_start=None, deterministic=True):
        if not deterministic:
            raise ValueError("the checkpoint average is a deterministic policy (decision 29): "
                             "predict(..., deterministic=True)")
        acts = [np.asarray(m.predict(observation, deterministic=True)[0], dtype=np.float64) for m in self.models]
        return np.mean(acts, axis=0).astype(np.float32), None
